"""Daily floor coin-in forecast: weekday factors times a level index, validated on frozen time holdouts.

- Series: coin-in per scheduled hour, so the 23-hour DST gaming day is not a dip.
- Weekday factors: log rate on ordinary days (no event, no federal holiday) regressed on weekday and
  month, so a drifting level does not leak into the weekly shape.
- Level index: rate divided by its weekday factor, ordinary days only. Four ways to carry it forward:
  the training mean, the last 28 days, a local level, and a local level with damped drift.
- Selection: fit to Mar 31, score April. Holdout: refit to Apr 30, forecast May 1-Jun 30 in one shot,
  write it to disk, then score. July uses the method with the lowest error across both windows.
- No event term: one occurrence per event cannot be estimated. Federal holidays get no uplift; their
  interval widens by the largest holiday miss known at the forecast origin.
- Baselines (frozen the same way): weekday mean of all days, weekday mean of ordinary days, constant
  mean, and the previous Holt-Winters model.
"""
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.tsa.exponential_smoothing.ets import ETSModel

from . import claims
from .db import ROOT, df

OUT = ROOT / "output"
SELECT_ORIGIN = pd.Timestamp("2025-03-31")
HOLDOUT_ORIGIN = pd.Timestamp("2025-04-30")
HOLDOUT_END = pd.Timestamp("2025-06-30")
JULY = pd.date_range("2025-07-01", "2025-07-30", freq="D")
JULY_HOLIDAYS = {pd.Timestamp("2025-07-04"): "Independence Day"}
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
TRAILING_DAYS = 28
Z = {80: 1.2816, 95: 1.9600}
METHODS = {"flat": "Training-mean level", "trailing28": "Last-28-day level", "local_level": "Local level",
           "damped_drift": "Local level with damped drift"}
BASELINES = {"weekday_mean": "Weekday mean, all days (guide baseline)",
             "weekday_mean_ordinary": "Weekday mean, ordinary days", "constant_mean": "Constant mean",
             "holt_winters": "Holt-Winters (previous model)"}


def series() -> pd.DataFrame:
    d = df("""
        SELECT p.gaming_date, p.local_weekday, c.month, p.coin_in_usd::DOUBLE AS coin_in,
               p.theo_usd::DOUBLE AS theo, c.scheduled_seconds / 3600.0 AS hours,
               p.events_active, c.federal_holiday
        FROM property_day p JOIN calendar_day c USING (gaming_date)
        ORDER BY 1""")
    d["gaming_date"] = pd.to_datetime(d.gaming_date)
    d = d.set_index("gaming_date").asfreq("D")
    d["log_rate"] = np.log(d.coin_in / d.hours)
    d["special"] = d.events_active.notna() | d.federal_holiday.notna()
    return d


def weekday_factors(d: pd.DataFrame, origin: pd.Timestamp) -> pd.Series:
    """Log weekday factors, centred so the seven average zero."""
    train = d.loc[:origin]
    fit = smf.ols("log_rate ~ C(local_weekday) + C(month)", train[~train.special]).fit()
    f = pd.Series({w: fit.params.get(f"C(local_weekday)[T.{w}]", 0.0) for w in WEEKDAYS})
    return f - f.mean()


def level_index(d: pd.DataFrame, origin: pd.Timestamp, factors: pd.Series) -> pd.Series:
    """Log of rate over weekday factor; event and holiday days are missing."""
    train = d.loc[:origin]
    return (train.log_rate - train.local_weekday.map(factors)).where(~train.special)


def level_forecast(li: pd.Series, method: str, h: int) -> pd.DataFrame:
    """Log level for the next h days with 80% and 95% bands."""
    ordinary = li.dropna()
    if method in ("flat", "trailing28"):
        recent = ordinary if method == "flat" else \
            ordinary[ordinary.index > li.index[-1] - pd.Timedelta(days=TRAILING_DAYS)]
        out = pd.DataFrame({"mean": np.repeat(recent.mean(), h)})
        for lvl, z in Z.items():
            out[f"lo{lvl}"] = out["mean"] - z * ordinary.std()
            out[f"hi{lvl}"] = out["mean"] + z * ordinary.std()
        return out
    cfg = dict(trend=None) if method == "local_level" else dict(trend="add", damped_trend=True)
    start = li.index[-1] + pd.Timedelta(days=1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = ETSModel(li.interpolate(limit_direction="both"), error="add", initialization_method="estimated",
                       **cfg).fit(disp=False, maxiter=2000)
        pred = res.get_prediction(start=start, end=start + pd.Timedelta(days=h - 1))
        out = pd.DataFrame({"mean": pred.predicted_mean.values})
        for lvl in Z:
            fr = pred.summary_frame(alpha=1 - lvl / 100)
            out[f"lo{lvl}"], out[f"hi{lvl}"] = fr["pi_lower"].values, fr["pi_upper"].values
    return out


def holiday_misses(d: pd.DataFrame, origin: pd.Timestamp, factors: pd.Series) -> pd.Series:
    """Each federal holiday's log gap to the ordinary-day level within two weeks."""
    train = d.loc[:origin]
    li = train.log_rate - train.local_weekday.map(factors)
    ordinary = li[~train.special]
    return pd.Series({day: li[day] - ordinary[np.abs((ordinary.index - day).days) <= 14].mean()
                      for day in train.index[train.federal_holiday.notna()]}, dtype=float)


def path(d: pd.DataFrame, origin: pd.Timestamp, method: str, idx: pd.DatetimeIndex, hours: np.ndarray,
         holidays) -> pd.DataFrame:
    """Dollar forecast over idx: exp(level + weekday factor) x scheduled hours."""
    factors = weekday_factors(d, origin)
    lvl = level_forecast(level_index(d, origin, factors), method, len(idx))
    widen = float(holiday_misses(d, origin, factors).abs().max())
    fac = idx.strftime("%a").map(factors).values
    on_holiday = idx.isin(holidays)
    out = pd.DataFrame(index=idx)
    for col in lvl.columns:
        pad = 0.0 if col == "mean" else (-widen if col.startswith("lo") else widen)
        out[col] = np.exp(lvl[col].values + fac + np.where(on_holiday, pad, 0.0)) * hours
    return out


def holidays_in(d: pd.DataFrame, idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    return idx[d.federal_holiday.reindex(idx).notna().values]


def select(d: pd.DataFrame) -> pd.DataFrame:
    idx = pd.date_range(SELECT_ORIGIN + pd.Timedelta(days=1), HOLDOUT_ORIGIN, freq="D")
    actual = d.coin_in.reindex(idx).values
    rows = []
    for m, name in METHODS.items():
        f = path(d, SELECT_ORIGIN, m, idx, d.hours.reindex(idx).values, holidays_in(d, idx))["mean"].values
        rows.append({"method": m, "name": name, "april_mae": float(np.mean(np.abs(f - actual))),
                     "april_bias": float(np.mean(f - actual))})
    return pd.DataFrame(rows).sort_values("april_mae").reset_index(drop=True)


def holt_winters_reference(d: pd.DataFrame, idx: pd.DatetimeIndex) -> np.ndarray:
    """The previous model: ETS(M,N,A) with a 7-day season on event-cleaned rate, no event adjustment."""
    train = d.loc[:HOLDOUT_ORIGIN]
    rate = np.exp(train.log_rate)
    ordinary = train[train.events_active.isna()]
    for day in train.index[train.events_active.notna()]:
        ref = ordinary[(ordinary.local_weekday == train.local_weekday[day])
                       & (np.abs((ordinary.index - day).days) <= 21)]
        rate.loc[day] = np.exp(ref.log_rate).mean()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = ETSModel(rate, error="mul", trend=None, seasonal="add", seasonal_periods=7,
                       initialization_method="estimated").fit(disp=False, maxiter=2000)
    return res.forecast(len(idx)).values * d.hours.reindex(idx).values


def holdout(d: pd.DataFrame) -> pd.DataFrame:
    idx = pd.date_range(HOLDOUT_ORIGIN + pd.Timedelta(days=1), HOLDOUT_END, freq="D")
    hours = d.hours.reindex(idx).values
    train = d.loc[:HOLDOUT_ORIGIN]
    ordinary = train[~train.special]
    frozen = pd.DataFrame(index=idx)
    frozen.index.name = "gaming_date"
    frozen["local_weekday"] = d.local_weekday.reindex(idx)
    frozen["federal_holiday"] = d.federal_holiday.reindex(idx)
    for m in METHODS:
        p = path(d, HOLDOUT_ORIGIN, m, idx, hours, holidays_in(d, idx))
        frozen[m] = p["mean"]
        for col in ("lo80", "hi80", "lo95", "hi95"):
            frozen[f"{m}_{col}"] = p[col]
    frozen["weekday_mean"] = frozen.local_weekday.map(train.groupby("local_weekday").coin_in.mean())
    frozen["weekday_mean_ordinary"] = frozen.local_weekday.map(ordinary.groupby("local_weekday").coin_in.mean())
    frozen["constant_mean"] = train.coin_in.mean()
    frozen["holt_winters"] = holt_winters_reference(d, idx)
    OUT.mkdir(exist_ok=True)
    frozen.to_csv(OUT / "forecast_frozen_holdout.csv")
    return frozen


def score(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frozen = pd.read_csv(OUT / "forecast_frozen_holdout.csv", parse_dates=["gaming_date"]).set_index("gaming_date")
    scored = frozen.assign(actual=d.coin_in.reindex(frozen.index), event=d.events_active.reindex(frozen.index),
                           special=d.special.reindex(frozen.index))
    rows = []
    for col, name in {**METHODS, **BASELINES}.items():
        err = scored[col] - scored.actual
        row = {"model": name, "column": col, "mae": float(err.abs().mean()), "bias": float(err.mean()),
               "mape": float((err.abs() / scored.actual).mean()),
               "mae_may": float(err[err.index.month == 5].abs().mean()),
               "mae_june": float(err[err.index.month == 6].abs().mean()),
               "mae_ordinary": float(err[~scored.special].abs().mean()),
               "mae_special": float(err[scored.special].abs().mean())}
        for lvl in (80, 95):
            inside = (scored.actual >= scored.get(f"{col}_lo{lvl}", np.nan)) \
                & (scored.actual <= scored.get(f"{col}_hi{lvl}", np.nan))
            row[f"coverage{lvl}"] = float(inside.mean()) if col in METHODS else np.nan
            row[f"coverage{lvl}_ordinary"] = float(inside[~scored.special].mean()) if col in METHODS else np.nan
        rows.append(row)
    cols = list(METHODS) + list(BASELINES)
    by_wd = scored[cols].sub(scored.actual, axis=0).abs().assign(local_weekday=scored.local_weekday) \
        .groupby("local_weekday").mean().reindex(WEEKDAYS).reset_index()
    return scored.reset_index(), pd.DataFrame(rows), by_wd


def deployed(selection: pd.DataFrame, metrics: pd.DataFrame) -> tuple[str, pd.Series]:
    """Method with the lowest day-weighted error across both out-of-sample windows."""
    april = selection.set_index("method").april_mae
    hold = metrics.set_index("column").mae.reindex(list(METHODS))
    n_a, n_h = (HOLDOUT_ORIGIN - SELECT_ORIGIN).days, (HOLDOUT_END - HOLDOUT_ORIGIN).days
    pooled = (april * n_a + hold * n_h) / (n_a + n_h)
    return str(pooled.idxmin()), pooled


def shift_profile() -> pd.DataFrame:
    """Share of daily coin-in by slot-tech shift, weekdays vs weekends."""
    return df("""
        SELECT c.is_weekend, shift_of(h.local_hour) AS shift,
               sum(h.coin_in_cents) / sum(sum(h.coin_in_cents)) OVER (PARTITION BY c.is_weekend) coin_in_share
        FROM machine_hour h JOIN calendar_day c USING (gaming_date)
        WHERE h.active GROUP BY 1, 2 ORDER BY 1, 2""")


def july(d: pd.DataFrame, method: str) -> pd.DataFrame:
    """Forecast the decision horizon, with June's level as the low scenario."""
    holidays = [x for x in JULY_HOLIDAYS if x in JULY]
    hours = np.full(len(JULY), 24.0)
    out = path(d, HOLDOUT_END, method, JULY, hours, holidays).rename(columns={"mean": "forecast"})
    out.index.name = "gaming_date"
    out["june_level"] = path(d, HOLDOUT_END, "trailing28", JULY, hours, holidays)["mean"]
    out["scenario_low"] = np.minimum(out.forecast, out.june_level)
    out["local_weekday"] = JULY.strftime("%a")
    out["is_weekend"] = out.local_weekday.isin(["Sat", "Sun"])
    out["holiday"] = [JULY_HOLIDAYS.get(x) for x in JULY]
    out["method"] = METHODS[method]
    theo_hold = float(d.theo.sum() / d.coin_in.sum())
    out["theo"] = out.forecast * theo_hold
    out["theo_low"] = out.scenario_low * theo_hold
    prof = shift_profile()
    for shift in ("day", "swing", "grave"):
        share = prof[prof["shift"] == shift].set_index("is_weekend").coin_in_share
        out[f"theo_{shift}"] = out.theo * out.is_weekend.map(share).astype(float)
    return out.reset_index()


def run() -> dict[str, pd.DataFrame]:
    d = series()
    selection = select(d)
    april_choice = str(selection.method.iloc[0])
    holdout(d)
    scored, metrics, by_wd = score(d)
    method, pooled = deployed(selection, metrics)
    selection["pooled_mae"] = selection.method.map(pooled)
    jul = july(d, method)

    fac = pd.DataFrame({str(o.date()): np.exp(weekday_factors(d, o))
                        for o in (SELECT_ORIGIN, HOLDOUT_ORIGIN, HOLDOUT_END)})
    fac_drift = float((fac.max(axis=1) - fac.min(axis=1)).max())
    final_fac = weekday_factors(d, HOLDOUT_END)
    misses = holiday_misses(d, HOLDOUT_END, final_fac)
    widen = float(misses.abs().max())
    li = level_index(d, HOLDOUT_END, final_fac)
    lvl_m = np.exp(li.groupby(li.index.month).mean())
    april_rise = lvl_m[4] / lvl_m[[1, 2, 3]].mean() - 1
    june_fall = lvl_m[6] / lvl_m[[1, 2, 3, 4]].mean() - 1

    m = metrics.set_index("column")
    ac, wk, wko, hw, cm = (m.loc[c] for c in (april_choice, "weekday_mean", "weekday_mean_ordinary",
                                              "holt_winters", "constant_mean"))
    best = m.loc[list(METHODS)].mae.idxmin()
    bh = m.loc[best]
    lead = (f"weekday factors times a {METHODS[best].lower()} cut daily error to ${bh.mae:,.0f} MAE,"
            f" {1 - bh.mae / wk.mae:.0%} below the weekday-mean baseline (${wk.mae:,.0f}) and"
            f" {1 - bh.mae / hw.mae:.0%} below the previous Holt-Winters model (${hw.mae:,.0f})")
    if best == april_choice:
        claim = f"On a frozen May-June holdout, {lead}; April's validation picked the same method."
    else:
        claim = (f"On a frozen May-June holdout, {lead}. The method April's validation picked"
                 f" ({METHODS[april_choice].lower()}) also beat both, at ${ac.mae:,.0f}, but followed April's"
                 " rise too closely.")
    claims.add(
        "M-validation", "Model: weekday factors x level index",
        claim,
        "property_day coin-in per scheduled hour; log-rate OLS on weekday + month over ordinary days for the"
        " weekly shape; level index carried forward four ways (training mean, last 28 days, ETS local level,"
        " ETS damped drift); chosen on Jan-Mar vs April MAE; refit on Jan-Apr and a 61-day forecast frozen to"
        " backend/output/forecast_frozen_holdout.csv before scoring",
        "MAE (bias): " + "; ".join(f"{r.model} ${r.mae:,.0f} ({r.bias:+,.0f})" for r in metrics.itertuples())
        + f". April MAE: " + "; ".join(f"{r.name} ${r.april_mae:,.0f}" for r in selection.itertuples())
        + f". {METHODS[best]} 80% interval covered {bh.coverage80:.0%} of days ({bh.coverage80_ordinary:.0%} of"
        f" ordinary days), 95% covered {bh.coverage95:.0%} ({bh.coverage95_ordinary:.0%}); event and holiday days"
        f" MAE ${bh.mae_special:,.0f} vs ordinary days ${bh.mae_ordinary:,.0f}."
        f" Weekday factors (Jun 30 fit): " + ", ".join(f"{w} {np.exp(final_fac[w]):.2f}" for w in WEEKDAYS) + ".",
        f"June softening vs a contaminated baseline: the weekday mean of ordinary days alone scores"
        f" ${wko.mae:,.0f} (bias {wko.bias:+,.0f}) against the guide baseline's ${wk.mae:,.0f}"
        f" ({wk.bias:+,.0f}), so most of the old over-forecast came from averaging event days into the"
        f" baseline. Recent-level methods: the level index rose {april_rise:+.1%} in April over Jan-Mar, then"
        f" June ran {june_fall:+.1%} below Jan-Apr, so methods that track the latest level over-forecast June."
        f" Shape stability: weekday factors moved at most {fac_drift:.3f} between the Mar 31, Apr 30 and Jun 30"
        " fits. Leakage: no event term; Gilded Ace Locals Appreciation Week was announced May 26, after the"
        " Apr 30 origin, so the previous event-adjusted forecast used information it could not have had.",
        f"Two out-of-sample windows (30 and 61 days). The weekly shape does most of the work: the"
        f" {METHODS[best].lower()} is within ${abs(bh.mae - wko.mae):,.0f} of a plain ordinary-day weekday mean."
        " The bands come from ordinary-day spread and are too narrow once the level moves. One winter-to-summer"
        " pass cannot identify a yearly season; events are not forecast.",
        ["model"])

    total, low_total = jul.forecast.sum(), jul.scenario_low.sum()
    holiday_list = "; ".join(f"{d.federal_holiday[k]} ({d.local_weekday[k]}) {np.exp(v) - 1:+.1%}"
                             for k, v in misses.items())
    claims.add(
        "M-decision", "Model: weekday factors x level index",
        f"The July forecast ({METHODS[method].lower()}, lowest error across April and May-June) puts July"
        f" coin-in at ${total:,.0f}; if June's level persists it is ${low_total:,.0f}"
        f" ({low_total / total - 1:+.1%}), which sets the low case for every July-scaled benefit in the budget.",
        "July 1-30: Jun 30 weekday factors x level forecast x 24 hours; June-level scenario from the last 28"
        " days; x floor theo hold x each shift's share of coin-in (machine_hour)",
        f"${jul.forecast.mean():,.0f}/day; weekend days average ${jul[jul.is_weekend].forecast.mean():,.0f} vs"
        f" weekdays ${jul[~jul.is_weekend].forecast.mean():,.0f}. Pooled out-of-sample MAE: "
        + "; ".join(f"{METHODS[k]} ${v:,.0f}" for k, v in pooled.sort_values().items())
        + f". July 4 band widened by +/-{np.exp(widen) - 1:.1%}.",
        f"Holiday uplift: no federal holiday in the data lifted coin-in ({holiday_list}), so July 4 gets no"
        f" uplift, only a wider band. Method choice: April alone picked the {METHODS[april_choice].lower()};"
        " pooling both windows decides the July method.",
        "July is outside the observed window, and summer seasonality cannot be estimated from one season; the"
        " July 4 band is a judgement from five holidays, none on a Friday.",
        ["model", "decision"])

    summary = pd.DataFrame([{"method": METHODS[method], "april_choice": METHODS[april_choice],
                             "best_holdout": METHODS[best], "holiday_widen": widen, "april_rise": april_rise,
                             "june_fall": june_fall, "factor_drift": fac_drift,
                             "july_total": total, "july_low_total": low_total}])
    factors = fac.rename_axis("local_weekday").reset_index()
    return {"selection": selection, "holdout": scored, "metrics": metrics, "by_weekday": by_wd,
            "july": jul, "factors": factors, "summary": summary}


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    out = run()
    print(out["selection"])
    print(out["metrics"].round(3))
    print(out["factors"].round(3))
    print(out["july"].head(10))
    print(out["summary"].T)
    for c in claims.REGISTRY.values():
        print("-", c.id, ":", c.result)
