"""Q6: price the $100,000 / 30-day portfolio.

Cost = quantity x (unit cost + recurring per day x max(0, 30 - lead days)). Benefits are expected
house win (theo) or avoided supplied costs over the days left after the lead time, in low / mid /
high scenarios built from the evidence in Q1-Q5 and the July forecast. July-scaled low cases assume
June's demand level persists. An action is funded when its mid-scenario net benefit is positive, at
most three action types, within budget.
"""
import numpy as np
import pandas as pd

from . import claims
from .db import df

BUDGET = 100_000
HORIZON = 30
MAX_TYPES = 3


def catalog() -> pd.DataFrame:
    return df("SELECT * FROM action_catalog").set_index("action_type_id")


def cost(cat: pd.DataFrame, action: str, qty: int) -> float:
    a = cat.loc[action]
    return qty * (a.unit_cost_cents + a.recurring_cost_cents_per_day * max(0, HORIZON - a.lead_days)) / 100


def effective_days(cat: pd.DataFrame, action: str) -> int:
    return max(0, HORIZON - int(cat.loc[action, "lead_days"]))


def _row(cat, action, qty, targets, low, mid, high, assumption, breakeven, measurement, uncertainty, note=""):
    c = cost(cat, action, qty)
    return {"action_type_id": action, "name": cat.loc[action, "name"], "quantity": qty, "targets": targets,
            "lead_days": int(cat.loc[action, "lead_days"]), "effective_days": effective_days(cat, action),
            "cost": c, "benefit_low": low, "benefit_mid": mid, "benefit_high": high,
            "net_low": low - c, "net_mid": mid - c, "net_high": high - c,
            "key_assumption": assumption, "breakeven": breakeven, "measurement": measurement,
            "uncertainty": uncertainty, "note": note,
            "incompatibility_group": cat.loc[action, "incompatibility_group"]}


def run(q1: dict, q2: dict, q3: dict, q5: dict, model: dict) -> dict[str, pd.DataFrame]:
    cat = catalog()
    sc = q1["scorecard"].set_index("machine_id")
    zf = q1["zone_factors"].set_index("zone_id").zone_factor
    jul = model["july"].copy()
    jul["gaming_date"] = pd.to_datetime(jul.gaming_date)
    floor_theo_hold = float(q2["daily"].theo.sum() / q2["daily"].coin_in.sum())
    jan_jun_theo_day = float(q2["daily"].theo.mean())
    july_scale = float(jul.theo.mean() / jan_jun_theo_day)
    july_scale_low = float(jul.theo_low.mean() / jan_jun_theo_day)
    recovered = float(q3["summary"].recovered_share.iloc[0])
    rows = []

    # Inspect: the payout anomaly. Benefit = restoring its daily theo shortfall.
    anomalies = sc[sc.payout_anomaly].index.tolist()
    if anomalies:
        a = sc.loc[anomalies]
        gap_day = float((a.theo - a.house_win).sum() / a.days_on.mean())
        days = effective_days(cat, "A-INSPECT")
        down = float((a.theo_per_hour * cat.loc["A-INSPECT", "downtime_minutes"] / 60).sum())
        val = gap_day * days
        rows.append(_row(
            cat, "A-INSPECT", len(anomalies), ", ".join(anomalies),
            0.3 * val - down, 0.7 * val - down, 0.95 * val - down,
            f"Chance the inspection finds and fixes a paytable fault (30% / 70% / 95%); a fix restores the"
            f" ${gap_day:,.0f}/day gap between theo and actual house win.",
            f"Pays back if the fix probability exceeds {cost(cat, 'A-INSPECT', len(anomalies)) / val:.0%}.",
            "Before/after hit rate and hold vs game_math on the machine meters; expect hit rate back near"
            f" {a.hit_expected.iloc[0]:.1%} and hold near {a.theo_hold.iloc[0]:.1%}. Also track its occupancy,"
            " since frequent small hits may be why players like it.",
            "The anomaly is certain (z > 100); the cause and whether a fix holds are not.",
            "Continuing the anomaly costs about $73,000 a year."))

    # Move machines out of the Back Forty into empty Center Pit slots.
    empty = df("""
        WITH occ AS (SELECT DISTINCT location_id FROM machine_day WHERE gaming_date = DATE '2025-06-30' AND active)
        SELECT location_id, zone_id FROM floor_locations
        WHERE node_type = 'slot' AND location_id NOT IN (SELECT location_id FROM occ)""")
    best_zone = zf.drop("Z-HL").idxmax() if "Z-HL" in zf.index else zf.idxmax()
    pit_slots = empty[empty.zone_id == "Z-PIT"].location_id.tolist()
    target_zone = "Z-PIT" if pit_slots else best_zone
    b40_now = df("""
        SELECT machine_id, sum(theo) / count(*) theo_day, sum(theo) / sum(available_hours) theo_per_hour
        FROM floor_day WHERE zone_id = 'Z-B40' AND gaming_date >= DATE '2025-04-07' GROUP BY 1""")
    b40_now = b40_now[~b40_now.machine_id.isin(anomalies)]
    b40_now = b40_now[b40_now.machine_id.map(lambda m: not sc.loc[m, "retired"])]
    movers = b40_now.nlargest(len(pit_slots), "theo_day")
    if len(movers):
        ratio = float(zf[target_zone] / zf["Z-B40"])
        days = effective_days(cat, "A-MOVE-MACHINE")
        down = float((movers.theo_per_hour * cat.loc["A-MOVE-MACHINE", "downtime_minutes"] / 60).sum())
        base = float(movers.theo_day.sum()) * july_scale
        base_low = float(movers.theo_day.sum()) * july_scale_low

        def gain(uplift, absorbed, b=base):
            return (b * uplift - b * (1 - absorbed)) * days - down

        low, mid, high = gain(1 + 0.25 * (ratio - 1), 0.0, base_low), gain(ratio, 0.25), gain(ratio, 0.5)
        be = (cost(cat, "A-MOVE-MACHINE", len(movers)) + down) / (base * days) + 1
        rows.append(_row(
            cat, "A-MOVE-MACHINE", len(movers),
            ", ".join(f"{m} (Z-B40) to {s}" for m, s in zip(movers.machine_id, pit_slots)),
            low, mid, high,
            f"Moved machines earn the Center Pit's location factor ({zf[target_zone]:.2f} vs Back Forty"
            f" {zf['Z-B40']:.2f}, so x{ratio:.2f}) and B40 neighbours absorb 0% / 25% / 50% of the play"
            " they leave behind; low case assumes only a quarter of the location gap transfers.",
            f"Pays back if a moved machine earns more than {be:.2f}x its Back Forty theo with no absorption.",
            "Moved machines' theo per available hour vs their own April-June Back Forty rate; rest of the"
            " pit vs control zones (the same test that showed bank B-51 did not cannibalize the pit); B40"
            " remaining machines vs control.",
            "Location factors are averages; the new bank B-51 added play without cannibalizing the pit"
            f" ({q2['summary'].pit_rest_effect.iloc[0]:+.1%}), which supports the mid case.",
            "Uses the two empty Center Pit slots; more moves would need swaps."))

    # Promotion weekend: the forecast gives every ordinary weekend the same baseline, so take the earliest
    # Friday-Sunday after the lead time with no holiday, whose baseline is the best measured.
    jul["dow"] = jul.gaming_date.dt.dayofweek
    earliest = pd.Timestamp("2025-07-01") + pd.Timedelta(days=int(cat.loc["A-PROMO", "lead_days"]))
    weekends = []
    for f in jul[(jul.dow == 4) & (jul.gaming_date >= earliest)
                 & (jul.gaming_date + pd.Timedelta(days=2) <= jul.gaming_date.max())].gaming_date:
        wk = jul[(jul.gaming_date >= f) & (jul.gaming_date <= f + pd.Timedelta(days=2))]
        if wk.holiday.isna().all():
            weekends.append((f, float(wk.forecast.sum()), float(wk.scenario_low.sum())))
    if weekends:
        fri, base_coin, base_low = weekends[0]
        ev = q2["events"].set_index("event_id")
        lifts = ev[ev.event_type == "property_promotion"].lift_mean
        lo_l, hi_l = float(lifts.min()), float(lifts.max())
        mid_l = float(lifts.mean())
        reinvest = float(q5["monthly"].reinvestment.iloc[-1])

        def promo(lift, base=base_coin):
            return lift * base * floor_theo_hold * (1 - reinvest)

        rows.append(_row(
            cat, "A-PROMO", 1, f"Weekend {fri:%b %d}-{fri + pd.Timedelta(days=2):%d} (earliest holiday-free"
                               f" weekend after the lead time; forecast coin-in ${base_coin:,.0f}, June-level"
                               f" ${base_low:,.0f})",
            promo(lo_l, base_low), promo(mid_l), promo(hi_l),
            f"Lift equals the property's own past promotions: Locals Week {lo_l:+.1%}, average {mid_l:+.1%},"
            f" Winter Tournament {hi_l:+.1%}, applied to the July forecast (June's level in the low case) at the"
            f" floor theo hold ({floor_theo_hold:.2%}), less comp reinvestment.",
            f"Pays back above a {cost(cat, 'A-PROMO', 1) / (base_coin * floor_theo_hold):.1%} lift.",
            "Actual weekend coin-in vs the frozen July forecast and its 80% daily band; the following week vs"
            " forecast to catch pulled-forward play. Exclude the heaviest-loss guests from direct invitations.",
            "Two past promotions only, both in cooler months; July demand is softer, so a smaller lift is"
            " plausible.",
            "Responsible-gaming guardrail: broad marketing, no targeting of heavy-loss players."))

    # Evaluated but expected to lose money within 30 days.
    sh = q3["by_shift"].set_index("shift")
    f = q3["faults"]
    swing_faults_day = float((f["shift"] == "swing").sum() / 181)
    val_swing = float(sh.loc["swing", "theo_per_down_hour"]) * july_scale * (1 - recovered)
    val_swing_low = val_swing * july_scale_low / july_scale
    days = effective_days(cat, "A-TECH-SHIFT")
    staff_h = float(q3["summary"].staff_effect_h.iloc[0])
    rows.append(_row(
        cat, "A-TECH-SHIFT", 1, "Swing shift (highest-value downtime hour)",
        *(swing_faults_day * h * v * days for h, v in ((0.25, val_swing_low), (0.5, val_swing),
                                                       (staff_h, val_swing))),
        f"An extra technician saves 0.25 / 0.5 / {staff_h:.2f} hours per swing-shift fault (the high case"
        f" equals the whole short-staffing penalty); {swing_faults_day:.1f} faults per day at"
        f" ${val_swing:.2f} per down hour after substitution.",
        f"Would need {cost(cat, 'A-TECH-SHIFT', 1) / (swing_faults_day * val_swing * days):.1f} hours saved per fault.",
        "Repair time on the swing shift vs the April-June fully staffed baseline.",
        "Staffing returned to plan in June; the short-staffing penalty may not recur."))

    mfr = q3["by_manufacturer"].set_index("manufacturer")
    worst = q3["summary"].worst_manufacturer.iloc[0]
    w = mfr.loc[worst]
    per_day = (w.lost_theo * (1 - recovered) * july_scale + w.repair_cost) / 181
    per_day_low = (w.lost_theo * (1 - recovered) * july_scale_low + w.repair_cost) / 181
    days = effective_days(cat, "A-PREVENTIVE")
    pm_down = w.machines * cat.loc["A-PREVENTIVE", "downtime_minutes"] / 60 * float(
        sh.loc["grave", "theo_per_down_hour"]) * (1 - recovered)
    rows.append(_row(
        cat, "A-PREVENTIVE", 1, f"{worst} ({int(w.machines)} machines)",
        *(p * days * r - pm_down for p, r in ((per_day_low, 0.10), (per_day, 0.25), (per_day, 0.50))),
        f"Preventive maintenance cuts {worst} faults by 10% / 25% / 50%, saving lost theo and direct repair"
        f" cost (${per_day:,.0f}/day combined), less 90 minutes of quiet-hour downtime per machine.",
        f"Would need a {cost(cat, 'A-PREVENTIVE', 1) / (per_day * days):.0%} fault reduction within 30 days.",
        f"{worst} faults per machine-month vs the other manufacturers, before and after.",
        "No preventive-maintenance history in the data to calibrate the effect.",
        "Benefits continue after July; a stronger case over a longer horizon."))

    rs = q2["summary"].iloc[0]
    gap_day = rs.lost_theo_post / rs.post_days * july_scale
    days = effective_days(cat, "A-WAYFINDING")
    rows.append(_row(
        cat, "A-WAYFINDING", 1, "Z-B40 (Back Forty)",
        *(gap_day * days * r for r in (0.0, 0.35, 1.0)),
        f"Signage recovers 0% / 35% / 100% of the Back Forty's remaining post-renovation gap"
        f" ({rs.post_effect:+.1%}, about ${gap_day:,.0f} theo per day).",
        f"Would need to recover {cost(cat, 'A-WAYFINDING', 1) / (gap_day * days):.0%} of the gap.",
        "Back Forty coin-in per machine and door-counter entries vs control zones.",
        "The remaining gap is small; the zone was already the weakest before the closure."))

    lia = q5["summary"].iloc[0]
    rows.append(_row(
        cat, "A-COMP-PILOT", 1, "Random half of card holders at the pre-May rate vs current rate",
        0.0, 0.0, 0.0,
        "No in-horizon cash benefit: the May change had no measurable effect on play or comp cost, so the"
        " pilot buys information about the"
        f" ${lia.cost_at_new - lia.cost_at_old:,.0f} rise in latent points exposure.",
        "Information only.",
        "Visits, coin-in and redemptions per player, treatment vs control, by tier.",
        "A 25-day pilot may be too short to detect a small effect.",
        "Recommended as the next step once a slot frees up; incompatible with A-COMP-CHANGE."))

    rows.append(_row(
        cat, "A-COMP-CHANGE", 1, "Floor-wide redemption rate",
        0.0, 0.0, 0.0,
        "Reverting toward the pre-May rate would shrink latent points exposure, but May's change moved no"
        " measured outcome, so a blind floor-wide change has no evidence-based benefit within 30 days.",
        "Information only.", "Comp cost, redemptions and carded coin-in vs the ITS trend.",
        "A floor-wide change has no control group.",
        "Incompatible with A-COMP-PILOT; the pilot is the better-evidenced way to settle the rate."))
    rows.append(_row(
        cat, "A-MOVE-BANK", 1, "A Back Forty bank", 0.0, 0.0, 0.0,
        "Needs a whole empty bank position in a stronger zone; the floor has only scattered empty slots.",
        "Not feasible on the June 30 floor.", "n/a", "n/a"))
    rows.append(_row(
        cat, "A-SURVEY", 1, "July intercept survey", 0.0, 0.0, 0.0,
        "Improves next month's decisions (why the Back Forty lags, comp awareness); no direct July return.",
        "Information only.", "n/a", "The current survey is already monthly, with documented sampling limits."))

    mgr = q1["manager_list"]
    live = mgr[~mgr.retired]
    rows.append(_row(
        cat, "A-REPLACE-BUY", len(mgr), "Manager's bottom 10", 0.0, 0.0, 0.0,
        "Buying ten new machines costs more than the whole budget.",
        "Not affordable.", "n/a",
        f"{int(mgr.retired.sum())} of the ten are already retired.",
        "The manager's original plan."))
    lease_days = effective_days(cat, "A-REPLACE-LEASE")
    live_theo_day = float(live.theo.sum() / live.days_on.sum()) * july_scale
    rows.append(_row(
        cat, "A-REPLACE-LEASE", len(live), "Manager's bottom 10, excluding retired machines",
        *(len(live) * live_theo_day * u * lease_days for u in (0.0, 0.3, 1.0)),
        "A new leased title in the same Back Forty slot earns 0% / 30% / 100% more theo than the machine"
        " it replaces; the location stays the same.",
        f"Would need a {cost(cat, 'A-REPLACE-LEASE', len(live)) / (len(live) * live_theo_day * lease_days):.0%}"
        " uplift per machine.",
        "Replaced machines' theo per available hour vs their predecessors.",
        "The waterfall shows these machines lose to game mix and location, which a new cabinet in the same"
        " slot does not change."))

    t = pd.DataFrame(rows)
    t["roi_mid"] = t.net_mid / t.cost.replace(0, np.nan)
    candidates = t[(t.net_mid > 0)].sort_values("roi_mid", ascending=False)
    funded, spent = [], 0.0
    for r in candidates.itertuples():
        if len(funded) < MAX_TYPES and spent + r.cost <= BUDGET:
            funded.append(r.action_type_id)
            spent += r.cost
    t["funded"] = t.action_type_id.isin(funded)
    hold = {"action_type_id": "A-HOLD", "name": cat.loc["A-HOLD", "name"], "quantity": 1,
            "targets": "Unspent budget", "lead_days": 0, "effective_days": HORIZON, "cost": 0.0,
            "benefit_low": 0.0, "benefit_mid": 0.0, "benefit_high": 0.0, "net_low": 0.0, "net_mid": 0.0,
            "net_high": 0.0, "key_assumption": "Keep what the evidence does not justify spending.",
            "breakeven": "n/a", "measurement": "n/a", "uncertainty": "n/a", "funded": True,
            "note": f"${BUDGET - spent:,.0f} kept", "incompatibility_group": None, "roi_mid": np.nan}
    t = pd.concat([t, pd.DataFrame([hold])], ignore_index=True)

    f_rows = t[t.funded & (t.action_type_id != "A-HOLD")]
    claims.add(
        "Q6-portfolio", "Q6 Budget",
        f"Fund {len(f_rows)} action types for ${spent:,.0f} and keep ${BUDGET - spent:,.0f}: "
        + "; ".join(f"{r.name} x{r.quantity} (${r.cost:,.0f})" for r in f_rows.itertuples()) + ".",
        "analysis/budget.py: catalogue cost formula, benefits from Q1-Q5 evidence and the July forecast"
        " (weekday factors x level), low/mid/high scenarios; funded when the mid-case net benefit is positive",
        f"Expected net benefit (mid) ${f_rows.net_mid.sum():,.0f}, range ${f_rows.net_low.sum():,.0f} to"
        f" ${f_rows.net_high.sum():,.0f}. Not funded (mid-case net): "
        + "; ".join(f"{r.action_type_id} {r.net_mid:+,.0f}" for r in t[~t.funded].itertuples()) + ".",
        "Spending on causes the data do not support: replacements (game mix and location, not cabinets),"
        " technicians (staffing is back to plan) and maintenance (pays back after July).",
        "Benefits are expectations, mostly theo; action costs are fictional catalogue inputs and no uplift"
        f" is guaranteed. July-scaled low cases assume June's level persists ({july_scale_low / july_scale - 1:+.1%}"
        " vs the forecast).",
        ["q6", "budget"])
    claims.add(
        "Q6-no-replacement", "Q6 Budget",
        "Do not replace the manager's bottom 10.",
        "Q1 waterfall and Q6 pricing of A-REPLACE-BUY and A-REPLACE-LEASE",
        f"Buying all ten costs ${cost(cat, 'A-REPLACE-BUY', 10):,.0f}, more than double the budget;"
        f" {int(mgr.retired.sum())} are already retired; leasing replacements for the other"
        f" {len(live)} costs ${cost(cat, 'A-REPLACE-LEASE', len(live)):,.0f} and loses money in the mid case.",
        "That the machines are genuinely broken: their hit rates match game math (except M-1158, which is"
        " for inspection) and availability is normal.",
        "A new title could still out-earn an old one; the evidence says location and game settings"
        " dominate.",
        ["q6", "manager"])
    return {"actions": t, "summary": pd.DataFrame([{"budget": BUDGET, "spent": spent, "kept": BUDGET - spent,
                                                    "types": len(f_rows), "net_mid": f_rows.net_mid.sum(),
                                                    "net_low": f_rows.net_low.sum(),
                                                    "net_high": f_rows.net_high.sum()}])}
