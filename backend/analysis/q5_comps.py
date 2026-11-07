"""Q5: what the comp program cost, and whether anything about it changed.

Comp cost is the economic cost of redeemed items. It already sits inside POS cost of goods, so it
is never subtracted a second time.
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from . import claims
from .db import df

PRE_START = "2025-01-01"
CHANGE_DATE = pd.Timestamp("2025-05-01")
CHANGE_UTC = "TIMESTAMP '2025-05-01 13:00'"  # 06:00 PDT, the start of gaming day May 1


def change_point() -> dict:
    r = df("""
        WITH r AS (SELECT event_at_utc, -points_delta * 100.0 / face_value_cents AS pts_per_usd
                   FROM loyalty_ledger WHERE event_type = 'redeem' AND face_value_cents > 0)
        SELECT (SELECT max(event_at_utc) FROM r WHERE pts_per_usd > 9 AND event_at_utc > '2025-04-15') last_old,
               (SELECT min(event_at_utc) FROM r WHERE pts_per_usd < 8 AND event_at_utc > '2025-04-15') first_new""").iloc[0]
    return {"last_old_rate_utc": str(r.last_old), "first_new_rate_utc": str(r.first_new)}


def redemption_rates() -> pd.DataFrame:
    return df(f"""
        WITH r AS (SELECT tier_before, -points_delta pts, face_value_cents / 100.0 face,
                          event_at_utc >= {CHANGE_UTC} AS after
                   FROM loyalty_ledger WHERE event_type = 'redeem')
        SELECT tier_before AS tier,
               sum(pts) FILTER (WHERE NOT after) / sum(face) FILTER (WHERE NOT after) pts_per_usd_before,
               sum(pts) FILTER (WHERE after) / sum(face) FILTER (WHERE after) pts_per_usd_after
        FROM r GROUP BY 1 ORDER BY 2 DESC""")


def daily() -> pd.DataFrame:
    # Ledger timestamps are UTC only; the gaming day starts 13:00 or 14:00 UTC, so shift by the
    # calendar's own boundaries rather than a fixed offset.
    d = df("""
        WITH led AS (
            SELECT c.gaming_date, l.event_type, l.points_delta, l.face_value_cents, l.economic_cost_cents
            FROM loyalty_ledger l JOIN calendar_day c
              ON l.event_at_utc >= c.gaming_day_start_utc AND l.event_at_utc < c.gaming_day_end_utc),
        lg AS (
            SELECT gaming_date,
                   count(*) FILTER (WHERE event_type = 'redeem') redemptions,
                   sum(-points_delta) FILTER (WHERE event_type = 'redeem') points_redeemed,
                   sum(points_delta) FILTER (WHERE event_type = 'award') points_awarded,
                   sum(face_value_cents) FILTER (WHERE event_type = 'redeem') / 100.0 comp_face,
                   sum(economic_cost_cents) FILTER (WHERE event_type = 'redeem') / 100.0 comp_cost
            FROM led GROUP BY 1),
        md AS (
            SELECT gaming_date, sum(carded_coin_in_cents) / 100.0 carded_coin_in,
                   sum(carded_theo_cents)::DOUBLE / 100.0 carded_theo
            FROM machine_day GROUP BY 1),
        tr AS (SELECT gaming_date_of(first_observed_local) gaming_date, count(*) visits,
                      count(DISTINCT player_id) visitors FROM trips GROUP BY 1)
        SELECT c.gaming_date, c.local_weekday, p.events_active IS NOT NULL AS event_day,
               lg.*, md.carded_coin_in, md.carded_theo, tr.visits, tr.visitors,
               p.comp_cost_usd::DOUBLE property_comp_cost, p.pos_cash_usd::DOUBLE pos_cash,
               p.pos_cogs_usd::DOUBLE pos_cogs
        FROM calendar_day c
        JOIN property_day p USING (gaming_date)
        LEFT JOIN lg USING (gaming_date)
        LEFT JOIN md USING (gaming_date)
        LEFT JOIN tr USING (gaming_date)
        ORDER BY 1""")
    d["gaming_date"] = pd.to_datetime(d.gaming_date)
    d["reinvestment"] = d.comp_cost / d.carded_theo
    d["pts_per_usd"] = d.points_redeemed / d.comp_face
    d["redemptions_per_1000_visits"] = d.redemptions / d.visits * 1000
    d["t"] = (d.gaming_date - d.gaming_date.min()).dt.days
    d["post"] = (d.gaming_date >= CHANGE_DATE).astype(int)
    d["t_post"] = (d.gaming_date - CHANGE_DATE).dt.days.clip(lower=0) * d.post
    return d


def its(d: pd.DataFrame, y: str) -> dict:
    """Segmented regression with weekday and event controls; Newey-West standard errors."""
    m = smf.ols(f"{y} ~ t + post + t_post + C(local_weekday) + event_day", data=d).fit(
        cov_type="HAC", cov_kwds={"maxlags": 7})
    pre = d[d.post == 0]
    base = pre[y].mean()
    post_days = d[d.post == 1]
    cf = m.predict(post_days.assign(post=0, t_post=0))
    excess = float((post_days[y] - cf).sum())
    ci = m.conf_int().loc["post"]
    return {"outcome": y, "level_change": float(m.params["post"]), "level_lo": float(ci[0]),
            "level_hi": float(ci[1]), "level_p": float(m.pvalues["post"]),
            "slope_change": float(m.params["t_post"]), "slope_p": float(m.pvalues["t_post"]),
            "pre_mean": float(base), "level_change_pct": float(m.params["post"] / base),
            "pre_trend_per_30d": float(m.params["t"] * 30), "excess_total_post": excess}


def monthly() -> pd.DataFrame:
    m = df("""
        WITH pp AS (
            SELECT period_month AS month, count(*) FILTER (WHERE tracked_coin_in_usd > 0) gamers,
                   sum(tracked_coin_in_usd)::DOUBLE coin_in, sum(theo_usd)::DOUBLE theo,
                   sum(comp_cost_usd)::DOUBLE comp_cost, sum(comp_face_value_usd)::DOUBLE comp_face,
                   sum(comps_redeemed) comps_redeemed, sum(points_earned) points_earned,
                   sum(points_redeemed) points_redeemed, sum(observed_visits) visits,
                   sum(tracked_contribution_usd)::DOUBLE contribution,
                   sum(linked_pos_cash_usd)::DOUBLE pos_cash, sum(linked_pos_cogs_usd)::DOUBLE pos_cogs
            FROM player_period GROUP BY 1)
        SELECT *, comp_cost / theo reinvestment, points_redeemed / comp_face pts_per_comp_usd,
               comp_cost / gamers comp_cost_per_gamer, comps_redeemed / visits * 1000 comps_per_1000_visits,
               coin_in / gamers coin_in_per_gamer, visits / gamers visits_per_gamer
        FROM pp ORDER BY 1""")
    return m


def by_tier() -> pd.DataFrame:
    t = df("""
        SELECT opening_tier AS tier,
               CASE WHEN period_month IN ('2025-03', '2025-04') THEN 'before' ELSE 'after' END AS period,
               count(DISTINCT player_id) FILTER (WHERE tracked_coin_in_usd > 0) gamers,
               sum(comp_cost_usd)::DOUBLE comp_cost, sum(theo_usd)::DOUBLE theo,
               sum(comps_redeemed) comps, sum(observed_visits) visits,
               sum(tracked_coin_in_usd)::DOUBLE coin_in, sum(points_redeemed) points_redeemed,
               sum(comp_face_value_usd)::DOUBLE comp_face
        FROM player_period WHERE period_month IN ('2025-03', '2025-04', '2025-05', '2025-06')
        GROUP BY ALL ORDER BY 1, 2 DESC""")
    t["reinvestment"] = t.comp_cost / t.theo
    t["comps_per_visit"] = t.comps / t.visits
    t["coin_in_per_visit"] = t.coin_in / t.visits
    t["pts_per_comp_usd"] = t.points_redeemed / t.comp_face
    return t


def liability(rates: pd.DataFrame) -> dict:
    """Unredeemed points this year, valued at the old and new redemption rates."""
    b = df("""
        SELECT sum(points_delta) FILTER (WHERE event_at_utc < TIMESTAMP '2025-07-01 13:00') balance,
               sum(economic_cost_cents) FILTER (WHERE event_type = 'redeem') /
                   sum(face_value_cents) FILTER (WHERE event_type = 'redeem') cost_ratio
        FROM loyalty_ledger""").iloc[0]
    led = df(f"""SELECT sum(-points_delta) pts, sum(face_value_cents) / 100.0 face,
                       event_at_utc >= {CHANGE_UTC} AS after
                FROM loyalty_ledger WHERE event_type = 'redeem' GROUP BY 3""").set_index("after")
    old_rate = led.loc[False, "pts"] / led.loc[False, "face"]
    new_rate = led.loc[True, "pts"] / led.loc[True, "face"]
    bal = float(b.balance)
    return {"balance_points": bal, "cost_ratio": float(b.cost_ratio), "old_rate": float(old_rate),
            "new_rate": float(new_rate),
            "face_at_old": bal / old_rate, "face_at_new": bal / new_rate,
            "cost_at_old": bal / old_rate * float(b.cost_ratio),
            "cost_at_new": bal / new_rate * float(b.cost_ratio)}


def run() -> dict[str, pd.DataFrame]:
    cp = change_point()
    rates = redemption_rates()
    d = daily()
    m = monthly()
    t = by_tier()
    lia = liability(rates)
    results = pd.DataFrame([its(d, y) for y in
                            ("pts_per_usd", "comp_cost", "reinvestment", "redemptions",
                             "redemptions_per_1000_visits", "carded_coin_in", "visits")])
    r = results.set_index("outcome")

    claims.add(
        "Q5-change", "Q5 Comp program",
        "At the start of gaming day May 1, 2025, the points needed per comp dollar fell by about half in"
        " every tier.",
        "loyalty_ledger redemptions: points / face value, by tier, before and after",
        f"Last old-rate redemption {cp['last_old_rate_utc']} UTC; first new-rate redemption"
        f" {cp['first_new_rate_utc']} UTC. " + "; ".join(
            f"{x.tier}: {x.pts_per_usd_before:.1f} to {x.pts_per_usd_after:.1f} points per $"
            for x in rates.itertuples())
        + f". Segmented regression level change {r.loc['pts_per_usd', 'level_change']:+.2f} points per $.",
        "Item mix: the change appears in every tier and every benefit at once, not as a drift.",
        "The data show the change, not the policy reason for it.",
        ["q5", "change"])

    cc, rv, rd, ci = (r.loc[k] for k in ("comp_cost", "reinvestment", "redemptions", "carded_coin_in"))
    claims.add(
        "Q5-cost", "Q5 Comp program",
        f"The comp program cost ${m.comp_cost.sum():,.0f} over six months ({m.comp_cost.sum() / m.theo.sum():.2%}"
        " of tracked theo). Cheaper redemptions did not produce a measurable jump in comp cost or play"
        " beyond the existing upward trend.",
        "Daily interrupted time series (statsmodels OLS: trend + post + post-trend + weekday + event,"
        " Newey-West errors) on ledger comp cost, comp cost / carded theo, redemptions, carded coin-in",
        f"Comp cost level change {cc.level_change:+,.0f}/day ({cc.level_change_pct:+.1%}, 95% CI"
        f" {cc.level_lo:+,.0f} to {cc.level_hi:+,.0f}, p={cc.level_p:.2f}); reinvestment"
        f" {rv.level_change * 100:+.2f} pp (p={rv.level_p:.2f}); redemptions {rd.level_change:+.1f}/day"
        f" (p={rd.level_p:.2f}); carded coin-in {ci.level_change_pct:+.1%} (p={ci.level_p:.2f}). Monthly"
        f" reinvestment: " + ", ".join(f"{x.month} {x.reinvestment:.2%}" for x in m.itertuples()) + ".",
        "Pre-existing trend: reinvestment was already rising"
        f" ({rv.pre_trend_per_30d * 100:+.2f} pp per 30 days before May); the model projects that trend"
        " forward. Seasonality: weekday and event controls; June's Locals Week is an event day.",
        "Two months after the change; a small effect could be missed. One floor-wide change with no"
        " control group, which is why a pilot with a control group is the better test.",
        ["q5", "cost"])

    claims.add(
        "Q5-liability", "Q5 Comp program",
        "The change roughly doubled what this year's unredeemed points are worth to guests.",
        "loyalty_ledger: points awarded minus redeemed through Jun 30, valued at the old and new"
        " points-per-dollar rates and the observed economic-cost-to-face ratio",
        f"{lia['balance_points']:,.0f} unredeemed points = ${lia['face_at_old']:,.0f} face"
        f" (${lia['cost_at_old']:,.0f} cost) at the old rate vs ${lia['face_at_new']:,.0f} face"
        f" (${lia['cost_at_new']:,.0f} cost) at the new rate.",
        "Redemption behaviour: redemptions per visit did not jump, so guests are not yet cashing in"
        " the cheaper points; the exposure is latent.",
        "Balances reset each year, so unredeemed points may expire; this is exposure, not a booked cost.",
        ["q5", "liability"])

    return {"daily": d, "monthly": m, "by_tier": t, "its": results, "redemption_rates": rates,
            "summary": pd.DataFrame([{**cp, **lia}])}


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    out = run()
    print(out["monthly"].round(4))
    print(out["by_tier"].round(4))
    print(out["its"].round(4))
    print(out["summary"].T)
    for c in claims.REGISTRY.values():
        print("-", c.id, ":", c.result)
