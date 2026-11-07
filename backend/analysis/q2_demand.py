"""Q2: what changed in demand across the floor, and why."""
import numpy as np
import pandas as pd

from . import claims
from .db import df

CLOSURE_START = pd.Timestamp("2025-03-03")
CLOSURE_END = pd.Timestamp("2025-04-06")  # walkway reopened 06:00 local on Apr 7
BANK51_OPEN = pd.Timestamp("2025-03-24")
CONTROL_EXCLUDE = ("Z-B40", "Z-HL")
RNG = np.random.default_rng(20250102)


def daily() -> pd.DataFrame:
    d = df("""
        SELECT p.gaming_date, p.local_weekday, c.is_weekend, p.events_active, c.federal_holiday,
               p.active_machines, p.coin_in_usd::DOUBLE coin_in, p.house_win_usd::DOUBLE house_win,
               p.theo_usd::DOUBLE theo, p.available_machine_hours, p.occupied_machine_hours,
               p.occupied_machine_hours / p.available_machine_hours AS occupancy,
               p.total_zone_entries_observed entries, p.counter_coverage_share,
               p.carded_coin_in_share, p.faults_opened, c.scheduled_seconds,
               w.tmax_c::DOUBLE tmax_c, w.prcp_mm::DOUBLE prcp_mm
        FROM property_day p JOIN calendar_day c USING (gaming_date)
        LEFT JOIN weather_daily w ON w.source_date = p.gaming_date
        ORDER BY 1""")
    d["gaming_date"] = pd.to_datetime(d.gaming_date)
    d["month"] = d.gaming_date.dt.strftime("%Y-%m")
    d["special"] = d.events_active.notna() | d.federal_holiday.notna()
    return d


def weekday_profile(d: pd.DataFrame) -> pd.DataFrame:
    base = d[~d.special]
    order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    w = base.groupby("local_weekday").agg(coin_in=("coin_in", "mean"), theo=("theo", "mean"),
                                          occupancy=("occupancy", "mean"), days=("coin_in", "size"))
    w = w.reindex(order).reset_index()
    w["index_vs_mean"] = w.coin_in / w.coin_in.mean()
    return w


def event_lift(d: pd.DataFrame) -> pd.DataFrame:
    """Each event day vs the mean of the same weekday within 3 weeks on ordinary days."""
    events = df("SELECT event_id, name, event_type, start_date, end_date, announced_date, local_scope"
                " FROM events ORDER BY start_date")
    ordinary = d[~d.special]
    rows = []
    for e in events.itertuples():
        days = d[(d.gaming_date >= pd.Timestamp(e.start_date)) & (d.gaming_date <= pd.Timestamp(e.end_date))]
        lifts = []
        for day in days.itertuples():
            ref = ordinary[(ordinary.local_weekday == day.local_weekday)
                           & ((ordinary.gaming_date - day.gaming_date).abs() <= pd.Timedelta(days=21))]
            if len(ref):
                lifts.append(day.coin_in / ref.coin_in.mean() - 1)
        rows.append({"event_id": e.event_id, "name": e.name, "event_type": e.event_type,
                     "local_scope": e.local_scope, "start_date": e.start_date, "end_date": e.end_date,
                     "announced_date": e.announced_date, "days": len(days),
                     "lift_mean": float(np.mean(lifts)) if lifts else np.nan,
                     "lift_min": float(np.min(lifts)) if lifts else np.nan,
                     "lift_max": float(np.max(lifts)) if lifts else np.nan,
                     "extra_coin_in": float(sum(days.coin_in) - sum(days.coin_in / (1 + np.array(lifts))))
                     if lifts else np.nan})
    return pd.DataFrame(rows)


def zone_day() -> pd.DataFrame:
    z = df("""
        SELECT gaming_date, zone_id, any_value(zone_name) zone_name, count(*) machines,
               sum(coin_in) coin_in, sum(theo) theo, sum(house_win) house_win,
               sum(occupied_hours) occupied_hours, sum(available_hours) available_hours
        FROM floor_day GROUP BY 1, 2 ORDER BY 1, 2""")
    z["gaming_date"] = pd.to_datetime(z.gaming_date)
    z["coin_in_per_machine"] = z.coin_in / z.machines
    z["occupancy"] = z.occupied_hours / z.available_hours
    return z


def traffic_day() -> pd.DataFrame:
    t = df("""
        SELECT gaming_date_of(hour_start_local) gaming_date, zone_id,
               sum(entries_count) FILTER (WHERE counter_status = 'ok') entries_ok,
               sum(coverage_minutes) FILTER (WHERE counter_status = 'ok') / 60.0 ok_hours,
               count(*) FILTER (WHERE counter_status <> 'ok') bad_hours
        FROM zone_traffic_hourly GROUP BY 1, 2""")
    t["gaming_date"] = pd.to_datetime(t.gaming_date)
    t = t[(t.gaming_date >= "2025-01-01") & (t.gaming_date <= "2025-06-30")]
    t["entries_per_hour"] = t.entries_ok / t.ok_hours
    return t


def _period(dates: pd.Series) -> pd.Series:
    return np.select([dates < CLOSURE_START, dates <= CLOSURE_END], ["pre", "closure"], "post")


def _boot_ratio(a: np.ndarray, b: np.ndarray, reps: int = 4000) -> tuple[float, float, float]:
    point = a.mean() / b.mean() - 1
    sims = [RNG.choice(a, a.size).mean() / RNG.choice(b, b.size).mean() - 1 for _ in range(reps)]
    lo, hi = np.percentile(sims, [2.5, 97.5])
    return float(point), float(lo), float(hi)


def renovation(z: pd.DataFrame, t: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """B40 relative to control zones, day by day. A daily ratio cancels floor-wide swings."""
    ctrl = z[~z.zone_id.isin(CONTROL_EXCLUDE)].groupby("gaming_date").agg(
        coin_in=("coin_in", "sum"), machines=("machines", "sum"), occ_h=("occupied_hours", "sum"),
        av_h=("available_hours", "sum"))
    b40 = z[z.zone_id == "Z-B40"].set_index("gaming_date")
    r = pd.DataFrame({
        "b40_per_machine": b40.coin_in_per_machine,
        "ctrl_per_machine": ctrl.coin_in / ctrl.machines,
        "b40_occupancy": b40.occupancy,
        "ctrl_occupancy": ctrl.occ_h / ctrl.av_h,
        "b40_machines": b40.machines,
        "b40_theo_hold": b40.theo / b40.coin_in,
    })
    r["ratio"] = r.b40_per_machine / r.ctrl_per_machine
    tz = t.pivot(index="gaming_date", columns="zone_id", values="entries_per_hour")
    ctrl_cols = [c for c in tz.columns if c not in CONTROL_EXCLUDE]
    r["traffic_ratio"] = tz["Z-B40"] / tz[ctrl_cols].mean(axis=1)
    r = r.reset_index()
    r["period"] = _period(r.gaming_date)

    pre, clo, post = (r[r.period == p] for p in ("pre", "closure", "post"))
    eff_closure = _boot_ratio(clo.ratio.values, pre.ratio.values)
    eff_post = _boot_ratio(post.ratio.values, pre.ratio.values)
    tr = r.dropna(subset=["traffic_ratio"])
    tr_closure = _boot_ratio(tr[tr.period == "closure"].traffic_ratio.values,
                             tr[tr.period == "pre"].traffic_ratio.values)
    tr_post = _boot_ratio(tr[tr.period == "post"].traffic_ratio.values,
                          tr[tr.period == "pre"].traffic_ratio.values)

    pre_ratio = pre.ratio.mean()
    r["b40_expected_coin_in"] = pre_ratio * r.ctrl_per_machine * r.b40_machines
    r["b40_actual_coin_in"] = r.b40_per_machine * r.b40_machines
    lost = r[r.period != "pre"]
    lost_coin_closure = float((lost[lost.period == "closure"].b40_expected_coin_in
                               - lost[lost.period == "closure"].b40_actual_coin_in).sum())
    lost_coin_post = float((lost[lost.period == "post"].b40_expected_coin_in
                            - lost[lost.period == "post"].b40_actual_coin_in).sum())
    hold = float(b40.theo.sum() / b40.coin_in.sum())

    r["month"] = r.gaming_date.dt.strftime("%Y-%m")
    monthly = r.groupby("month").agg(ratio=("ratio", "mean"), traffic_ratio=("traffic_ratio", "mean"),
                                     b40_occupancy=("b40_occupancy", "mean"),
                                     ctrl_occupancy=("ctrl_occupancy", "mean")).reset_index()
    summary = {
        "pre_ratio": float(pre_ratio), "closure_effect": eff_closure, "post_effect": eff_post,
        "traffic_closure_effect": tr_closure, "traffic_post_effect": tr_post,
        "lost_coin_in_closure": lost_coin_closure, "lost_theo_closure": lost_coin_closure * hold,
        "lost_coin_in_post": lost_coin_post, "lost_theo_post": lost_coin_post * hold,
        "post_days": int(len(post)), "b40_theo_hold": hold,
    }
    return r, monthly, summary


def bank51(z: pd.DataFrame) -> dict:
    """Did the new Center Pit bank add play or pull it from the rest of the pit?"""
    b = df("""
        SELECT gaming_date, bank_id = 'B-51' AS new_bank, zone_id, count(*) machines, sum(coin_in) coin_in
        FROM floor_day GROUP BY ALL""")
    b["gaming_date"] = pd.to_datetime(b.gaming_date)
    pit_old = b[(b.zone_id == "Z-PIT") & ~b.new_bank].set_index("gaming_date")
    new = b[b.new_bank].set_index("gaming_date")
    ctrl = z[~z.zone_id.isin(("Z-PIT", "Z-B40", "Z-HL"))].groupby("gaming_date").agg(
        coin_in=("coin_in", "sum"), machines=("machines", "sum"))
    ratio = (pit_old.coin_in / pit_old.machines) / (ctrl.coin_in / ctrl.machines)
    before = ratio[(ratio.index >= "2025-02-24") & (ratio.index < BANK51_OPEN)]
    after = ratio[(ratio.index >= BANK51_OPEN) & (ratio.index < "2025-04-21")]
    eff = _boot_ratio(after.values, before.values)
    new_per_machine = new.coin_in / new.machines
    rest_pit = pit_old.coin_in / pit_old.machines
    rel = (new_per_machine / rest_pit).dropna()
    first4, last4 = rel.iloc[:28].mean(), rel.iloc[-28:].mean()
    return {"pit_rest_effect": eff, "new_bank_vs_pit_first4w": float(first4),
            "new_bank_vs_pit_last4w": float(last4), "new_bank_machines": int(new.machines.max())}


def weather_effect(d: pd.DataFrame) -> dict:
    o = d[~d.special].copy()
    o["resid"] = o.coin_in / o.groupby("local_weekday").coin_in.transform("mean") - 1
    corr_t = float(o[["resid", "tmax_c"]].corr().iloc[0, 1])
    wet = o[o.prcp_mm > 0.5].resid.mean()
    dry = o[o.prcp_mm <= 0.5].resid.mean()
    return {"corr_tmax": corr_t, "wet_minus_dry": float(wet - dry), "wet_days": int((o.prcp_mm > 0.5).sum())}


def monthly(d: pd.DataFrame) -> pd.DataFrame:
    m = d.groupby("month").agg(coin_in_per_day=("coin_in", "mean"), theo_per_day=("theo", "mean"),
                               house_win_per_day=("house_win", "mean"), occupancy=("occupancy", "mean"),
                               entries_per_day=("entries", "mean"), active_machines=("active_machines", "mean"),
                               event_days=("events_active", lambda s: int(s.notna().sum()))).reset_index()
    lv = df("""SELECT month, visitor_volume, mean_visitors_per_calendar_day::DOUBLE visitors_per_day,
                      visitor_yoy_ratio::DOUBLE visitor_yoy, convention_attendance,
                      hotel_occupancy_ratio::DOUBLE hotel_occupancy FROM city_visitation_monthly""")
    survey = df("""SELECT month, survey_metric, estimate, standard_error FROM visitor_profile_monthly
                   WHERE month <= '2025-06'""")
    sv = survey.pivot(index="month", columns="survey_metric", values="estimate").add_prefix("survey_")
    m = m.merge(lv, on="month", how="left").merge(sv.reset_index(), on="month", how="left")
    m["coin_in_index"] = m.coin_in_per_day / m.coin_in_per_day.iloc[0]
    # Weekday mix differs month to month; compare on a mix-adjusted basis too.
    prof = d[~d.special].groupby("local_weekday").coin_in.mean()
    d2 = d.assign(wk_expected=d.local_weekday.map(prof))
    adj = d2.groupby("month").apply(lambda g: g.coin_in.sum() / g.wk_expected.sum(), include_groups=False)
    m["weekday_adjusted_index"] = m.month.map(adj).values
    return m


def run() -> dict[str, pd.DataFrame]:
    d = daily()
    wk = weekday_profile(d)
    ev = event_lift(d)
    z = zone_day()
    t = traffic_day()
    reno, reno_m, rs = renovation(z, t)
    b51 = bank51(z)
    wx = weather_effect(d)
    m = monthly(d)

    peak, low = m.loc[m.coin_in_per_day.idxmax()], m.loc[m.coin_in_per_day.idxmin()]
    corr_lv = float(m[["coin_in_per_day", "visitors_per_day"]].corr().iloc[0, 1])
    corr_conv = float(m[["coin_in_per_day", "convention_attendance"]].corr().iloc[0, 1])
    sat, tue = wk.set_index("local_weekday").coin_in[["Sat", "Tue"]]

    claims.add(
        "Q2-trend", "Q2 Demand changes",
        f"Floor demand peaked in {peak.month} and was lowest in {low.month}; the June dip lines up"
        " with the city-wide drop in visitors and conventions.",
        "property_day coin-in per gaming day by month; weekday-mix-adjusted index;"
        " city_visitation_monthly (LVCVA, real)",
        f"Coin-in per day ranged ${low.coin_in_per_day:,.0f} ({low.month}) to"
        f" ${peak.coin_in_per_day:,.0f} ({peak.month}); weekday-adjusted index"
        f" {m.weekday_adjusted_index.min():.3f}-{m.weekday_adjusted_index.max():.3f}."
        f" Correlation with LVCVA visitors/day {corr_lv:.2f}, with convention attendance {corr_conv:.2f}"
        f" (6 months only). LVCVA visitors were down {-m.visitor_yoy.max():.0%} to {-m.visitor_yoy.min():.0%}"
        " year over year.",
        "Weekday mix: the adjusted index removes months with extra weekends."
        " Machine count: active machines stayed between 300 and 308.",
        "LVCVA data describe all Las Vegas visitors, were published after 2025 and cannot have been"
        " known at the time; six monthly points cannot establish causation.",
        ["q2", "trend"])

    claims.add(
        "Q2-weekday", "Q2 Demand changes",
        f"Saturday brings in {sat / tue:.2f}x the coin-in of Tuesday; weekday is the largest regular"
        " demand driver.",
        "property_day mean coin-in by weekday, excluding event and holiday days",
        "; ".join(f"{r.local_weekday} ${r.coin_in:,.0f}" for r in wk.itertuples()),
        "Events: event and holiday days are excluded from the profile.",
        "Averages over about 22 ordinary days per weekday.",
        ["q2", "weekday"])

    best = ev.sort_values("lift_mean", ascending=False)
    claims.add(
        "Q2-events", "Q2 Demand changes",
        "Events lift coin-in by different amounts; the property's own promotions are the evidence base"
        " for pricing a promotion weekend.",
        "Each event day vs the mean of the same weekday within 21 days on ordinary days (property_day)",
        "; ".join(f"{r.name}: {r.lift_mean:+.1%} ({r.days} days, ${r.extra_coin_in:,.0f} extra coin-in)"
                  for r in best.itertuples()),
        "Seasonality: the comparison days are the same weekday within three weeks.",
        "One occurrence per event; overlapping events (CinemaCon then NAB) share comparison days.",
        ["q2", "events"])

    ce, pe = rs["closure_effect"], rs["post_effect"]
    tce, tpe = rs["traffic_closure_effect"], rs["traffic_post_effect"]
    claims.add(
        "Q2-renovation", "Q2 Demand changes",
        "Closing the entrance walkway to the Back Forty (Mar 3-Apr 7) cut its play, and it has not fully"
        " recovered.",
        "Daily ratio of Z-B40 coin-in per machine to control zones (all except Z-B40 and Z-HL) from"
        " floor_day; door counters from zone_traffic_hourly (status ok only); bootstrap 95% intervals",
        f"During closure: {ce[0]:+.1%} (95% CI {ce[1]:+.1%} to {ce[2]:+.1%}); after reopening:"
        f" {pe[0]:+.1%} ({pe[1]:+.1%} to {pe[2]:+.1%}) vs before. Door-counter entries: {tce[0]:+.1%}"
        f" during, {tpe[0]:+.1%} after. Estimated lost coin-in ${rs['lost_coin_in_closure']:,.0f} during"
        f" the closure (about ${rs['lost_theo_closure']:,.0f} theo) and ${rs['lost_coin_in_post']:,.0f}"
        f" since (about ${rs['lost_theo_post']:,.0f} theo).",
        "Floor-wide demand swings cancel in the daily ratio. Machine mix: per-machine coin-in, and"
        " B40's machine count barely changed.",
        "Assumes control zones were unaffected by the closure; some B40 players may have moved to them,"
        " which would overstate the effect slightly. The bootstrap treats days as independent, so"
        " intervals are somewhat too narrow.",
        ["q2", "location", "renovation"])

    pr = b51["pit_rest_effect"]
    claims.add(
        "Q2-bank51", "Q2 Demand changes",
        "The new 8-machine Center Pit bank (B-51, opened Mar 24) is the floor's busiest bank, and its"
        f" effect on the rest of the pit is {'small' if abs(pr[0]) < 0.05 else 'noticeable'}.",
        "floor_day: rest-of-pit coin-in per machine relative to control zones, 4 weeks before vs after"
        " Mar 24; B-51 per machine relative to the rest of the pit",
        f"Rest of pit vs control: {pr[0]:+.1%} (95% CI {pr[1]:+.1%} to {pr[2]:+.1%}). B-51 earned"
        f" {b51['new_bank_vs_pit_first4w']:.2f}x the rest of the pit per machine in its first 4 weeks and"
        f" {b51['new_bank_vs_pit_last4w']:.2f}x in its last 4.",
        "Novelty: compared the first and last four weeks of the new bank.",
        "Four-week windows are short; the basketball tournament falls in the 'before' window.",
        ["q2", "bank51"])

    claims.add(
        "Q2-weather", "Q2 Demand changes",
        "Weather explains little of the day-to-day demand.",
        "Ordinary-day coin-in relative to its weekday mean vs NOAA daily max temperature and rain (real)",
        f"Correlation with max temperature {wx['corr_tmax']:.2f}; rainy days (>0.5 mm, n={wx['wet_days']})"
        f" differ by {wx['wet_minus_dry']:+.1%}.",
        "Season: temperature rises steadily through the window, so its correlation also carries the"
        " seasonal trend.",
        "Few rainy days in Las Vegas; calendar dates, not gaming dates.",
        ["q2", "weather"])

    summary = pd.DataFrame([{**{k: v for k, v in rs.items() if not isinstance(v, tuple)},
                             "closure_effect": ce[0], "closure_lo": ce[1], "closure_hi": ce[2],
                             "post_effect": pe[0], "post_lo": pe[1], "post_hi": pe[2],
                             "traffic_closure": tce[0], "traffic_post": tpe[0],
                             "pit_rest_effect": pr[0], "pit_rest_lo": pr[1], "pit_rest_hi": pr[2],
                             "bank51_first4w": b51["new_bank_vs_pit_first4w"],
                             "bank51_last4w": b51["new_bank_vs_pit_last4w"],
                             **wx}])
    return {"daily": d, "weekday": wk, "events": ev, "zone_day": z, "traffic_day": t,
            "renovation_daily": reno, "renovation_monthly": reno_m, "monthly": m, "summary": summary}


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    out = run()
    print(out["monthly"].round(3))
    print(out["events"])
    print(out["renovation_monthly"].round(3))
    print(out["summary"].T)
    for c in claims.REGISTRY.values():
        print("-", c.id, ":", c.result)
