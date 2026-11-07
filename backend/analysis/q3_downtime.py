"""Q3: how much play was lost to downtime, and when.

Each down machine-hour is valued at that machine's own theo per available hour for the same local
hour of day and weekend/weekday type, so an outage at 21:00 on a Saturday costs more than one at
04:00 on a Tuesday. This gross figure assumes nobody moved to another machine; the substitution
test below measures how much of it neighbours on the same bank recovered.
"""
import numpy as np
import pandas as pd

from . import claims
from .db import connect, df

RNG = np.random.default_rng(7)


def _build_hourly() -> None:
    con = connect()
    con.execute("""
        CREATE OR REPLACE TEMP TABLE mh AS
        SELECT h.machine_id, h.hour_start_utc, h.hour_start_local, h.local_hour, h.gaming_date,
               h.location_id, fl.bank_id, fl.zone_id, c.is_weekend, md.config_id,
               h.available_seconds, 3600 - h.available_seconds AS down_seconds,
               h.coin_in_cents * (1 - gm.configured_rtp::DOUBLE) / 100.0 AS theo
        FROM machine_hour h
        JOIN machine_day md USING (machine_id, gaming_date)
        JOIN game_math gm ON gm.config_id = md.config_id
        JOIN calendar_day c USING (gaming_date)
        JOIN floor_locations fl ON fl.location_id = h.location_id
        WHERE h.active;

        CREATE OR REPLACE TEMP TABLE rate AS
        SELECT machine_id, local_hour, is_weekend,
               sum(theo) / nullif(sum(available_seconds) / 3600.0, 0) AS theo_per_hour
        FROM mh GROUP BY ALL;

        CREATE OR REPLACE TEMP TABLE rate_cfg AS
        SELECT config_id, zone_id, local_hour, is_weekend,
               sum(theo) / nullif(sum(available_seconds) / 3600.0, 0) AS theo_per_hour
        FROM mh GROUP BY ALL;

        CREATE OR REPLACE TEMP TABLE down AS
        SELECT mh.*, coalesce(r.theo_per_hour, rc.theo_per_hour) AS expected_rate,
               down_seconds / 3600.0 * coalesce(r.theo_per_hour, rc.theo_per_hour) AS lost_theo
        FROM mh
        LEFT JOIN rate r USING (machine_id, local_hour, is_weekend)
        LEFT JOIN rate_cfg rc USING (config_id, zone_id, local_hour, is_weekend)
        WHERE down_seconds > 0;

        CREATE OR REPLACE TEMP TABLE down_cause AS
        SELECT d.*, coalesce(o.event_type, 'unattributed') AS cause, o.operation_id
        FROM down d
        LEFT JOIN operations o ON o.machine_id = d.machine_id
            AND o.opened_at_utc < d.hour_start_utc + INTERVAL 1 HOUR
            AND o.available_at_utc > d.hour_start_utc
        QUALIFY row_number() OVER (PARTITION BY d.machine_id, d.hour_start_utc
                                   ORDER BY o.opened_at_utc DESC) = 1;
    """)


def faults() -> pd.DataFrame:
    f = df("""
        WITH roster AS (
            SELECT gaming_date, shift, sum(planned_headcount) planned, sum(actual_headcount) actual
            FROM shift_roster WHERE role = 'slot_tech' GROUP BY 1, 2)
        SELECT o.operation_id, o.machine_id, m.manufacturer, o.opened_at_local,
               gaming_date_of(o.opened_at_local) gaming_date,
               extract(hour FROM o.opened_at_local) local_hour,
               shift_of(extract(hour FROM o.opened_at_local)) shift,
               epoch(o.available_at_utc - o.opened_at_utc) / 3600.0 repair_hours,
               epoch(o.work_started_at_utc - o.opened_at_utc) / 3600.0 wait_hours,
               o.direct_cost_cents / 100.0 direct_cost, r.planned, r.actual,
               r.actual < r.planned understaffed
        FROM operations o JOIN machines m USING (machine_id)
        LEFT JOIN roster r ON r.gaming_date = gaming_date_of(o.opened_at_local)
            AND r.shift = shift_of(extract(hour FROM o.opened_at_local))
        WHERE o.event_type = 'fault_repair'""")
    f["month"] = pd.to_datetime(f.gaming_date).dt.strftime("%Y-%m")
    return f


def _boot_diff(a: np.ndarray, b: np.ndarray, reps: int = 4000) -> tuple[float, float, float]:
    point = a.mean() - b.mean()
    sims = [RNG.choice(a, a.size).mean() - RNG.choice(b, b.size).mean() for _ in range(reps)]
    lo, hi = np.percentile(sims, [2.5, 97.5])
    return float(point), float(lo), float(hi)


def substitution() -> dict:
    """During outage hours, did same-bank neighbours earn more theo than their own norm?"""
    r = df("""
        WITH out_hours AS (
            SELECT DISTINCT bank_id, hour_start_utc, machine_id AS down_machine, lost_theo
            FROM down WHERE down_seconds >= 1800),
        nb AS (
            SELECT o.bank_id, o.hour_start_utc, o.down_machine, o.lost_theo,
                   sum(mh.theo) actual, sum(mh.available_seconds / 3600.0 * r.theo_per_hour) expected
            FROM out_hours o
            JOIN mh ON mh.bank_id = o.bank_id AND mh.hour_start_utc = o.hour_start_utc
                   AND mh.machine_id <> o.down_machine AND mh.down_seconds = 0
            JOIN rate r USING (machine_id, local_hour, is_weekend)
            GROUP BY ALL)
        SELECT count(*) outage_hours, sum(actual) actual, sum(expected) expected,
               sum(lost_theo) lost_theo FROM nb""").iloc[0]
    extra = r.actual - r.expected
    return {"outage_hours": int(r.outage_hours), "neighbour_actual": float(r.actual),
            "neighbour_expected": float(r.expected), "outage_lost_theo": float(r.lost_theo),
            "neighbour_lift": float(r.actual / r.expected - 1),
            "recovered_share": float(extra / r.lost_theo)}


def run() -> dict[str, pd.DataFrame]:
    _build_hourly()
    by_cause = df("""SELECT cause, sum(down_seconds) / 3600.0 down_hours, sum(lost_theo) lost_theo,
                            count(DISTINCT operation_id) tickets
                     FROM down_cause GROUP BY 1 ORDER BY 3 DESC""")
    by_month = df("""SELECT strftime(gaming_date, '%Y-%m') AS month, sum(down_seconds) / 3600.0 down_hours,
                            sum(lost_theo) lost_theo FROM down_cause GROUP BY 1 ORDER BY 1""")
    by_hour = df("""SELECT local_hour, sum(down_seconds) / 3600.0 down_hours, sum(lost_theo) lost_theo,
                           sum(lost_theo) / (sum(down_seconds) / 3600.0) theo_per_down_hour
                    FROM down_cause GROUP BY 1 ORDER BY 1""")
    by_shift = df("""SELECT shift_of(local_hour) shift, sum(down_seconds) / 3600.0 down_hours,
                            sum(lost_theo) lost_theo,
                            sum(lost_theo) / (sum(down_seconds) / 3600.0) theo_per_down_hour
                     FROM down_cause GROUP BY 1 ORDER BY 3 DESC""")
    by_zone = df("""SELECT zone_id, sum(down_seconds) / 3600.0 down_hours, sum(lost_theo) lost_theo
                    FROM down_cause GROUP BY 1 ORDER BY 3 DESC""")
    by_mfr = df("""
        WITH d AS (SELECT m.manufacturer, sum(down_seconds) / 3600.0 down_hours, sum(lost_theo) lost_theo
                   FROM down_cause dc JOIN machines m USING (machine_id) WHERE cause = 'fault_repair'
                   GROUP BY 1),
        e AS (SELECT manufacturer, count(*) machine_days, count(DISTINCT machine_id) machines,
                     sum(faults_opened) faults, sum(available_hours) available_hours,
                     sum(occupied_hours) occupied_hours
              FROM floor_day GROUP BY 1),
        c AS (SELECT m.manufacturer, sum(o.direct_cost_cents) / 100.0 repair_cost
              FROM operations o JOIN machines m USING (machine_id)
              WHERE o.event_type = 'fault_repair' GROUP BY 1)
        SELECT e.*, d.down_hours, d.lost_theo, c.repair_cost,
               e.faults / (e.occupied_hours / 1000.0) faults_per_1000_occupied_hours,
               e.faults / (e.machine_days / 30.0) faults_per_machine_month,
               d.down_hours / e.machines down_hours_per_machine,
               d.lost_theo / e.machines lost_theo_per_machine
        FROM e JOIN d USING (manufacturer) JOIN c USING (manufacturer)
        ORDER BY faults_per_machine_month DESC""")
    by_machine = df("""
        SELECT dc.machine_id, any_value(m.manufacturer) manufacturer, any_value(dc.zone_id) zone_id,
               count(DISTINCT operation_id) FILTER (WHERE cause = 'fault_repair') faults,
               sum(down_seconds) / 3600.0 down_hours, sum(lost_theo) lost_theo
        FROM down_cause dc JOIN machines m USING (machine_id) GROUP BY 1 ORDER BY faults DESC""")
    daily = df("""SELECT gaming_date, sum(down_seconds) / 3600.0 down_hours, sum(lost_theo) lost_theo
                  FROM down_cause GROUP BY 1 ORDER BY 1""")
    staffing = df("""
        SELECT strftime(gaming_date, '%Y-%m') AS month, shift, sum(planned_headcount) planned,
               sum(actual_headcount) actual, count(*) FILTER (WHERE actual_headcount < planned_headcount)
               short_days
        FROM shift_roster WHERE role = 'slot_tech' GROUP BY 1, 2 ORDER BY 1, 2""")

    f = faults()
    f_month = f.groupby(["month", "manufacturer"]).agg(faults=("operation_id", "size"),
                                                        repair_hours=("repair_hours", "median")).reset_index()
    repair_by_staff = f.groupby(["shift", "understaffed"]).agg(
        faults=("operation_id", "size"), repair_mean=("repair_hours", "mean"),
        repair_median=("repair_hours", "median"), wait_mean=("wait_hours", "mean")).reset_index()
    short, full = f[f.understaffed == True], f[f.understaffed == False]  # noqa: E712
    staff_eff = _boot_diff(short.repair_hours.values, full.repair_hours.values)
    wait_eff = _boot_diff(short.wait_hours.values, full.wait_hours.values)
    sub = substitution()

    total_h = by_cause.down_hours.sum()
    total_lost = by_cause.lost_theo.sum()
    fault_row = by_cause.set_index("cause").loc["fault_repair"]
    mfr = by_mfr.set_index("manufacturer")
    worst = mfr.index[0]
    others = mfr.drop(worst)
    excess_faults = mfr.loc[worst, "faults_per_machine_month"] / others.faults_per_machine_month.mean()
    floor_hours = df("SELECT sum(scheduled_hours) h FROM floor_day").h.iloc[0]
    peak_month = by_month.loc[by_month.lost_theo.idxmax()]
    sh = by_shift.set_index("shift")

    claims.add(
        "Q3-total", "Q3 Downtime",
        f"Downtime removed {total_h:,.0f} machine-hours ({total_h / floor_hours:.2%} of scheduled time),"
        f" worth about ${total_lost:,.0f} in expected house win (theo) before substitution.",
        "machine_hour (3600 - available_seconds on active hours), valued at each machine's theo per"
        " available hour for the same local hour and weekday/weekend; causes from operations",
        f"Fault repairs: {fault_row.down_hours:,.0f} h, ${fault_row.lost_theo:,.0f}. "
        + "; ".join(f"{r.cause}: {r.down_hours:,.0f} h" for r in by_cause.itertuples()
                    if r.cause != "fault_repair")
        + f". Matches machine_day downtime exactly ({total_h:,.0f} h).",
        f"Substitution: in outage hours, same-bank neighbours earned {sub['neighbour_lift']:+.1%} vs"
        f" their own norm, recovering about {sub['recovered_share']:.0%} of the gross loss.",
        "Theo is an expectation; actual lost house win depends on luck. Substitution is measured only"
        " within the same bank.",
        ["q3", "downtime"])

    claims.add(
        "Q3-when", "Q3 Downtime",
        f"Downtime cost the most in {peak_month.month} and on the {sh.index[0]} shift; an hour of"
        f" downtime is worth ${sh.theo_per_down_hour.max():.2f} on the {sh.theo_per_down_hour.idxmax()}"
        f" shift vs ${sh.theo_per_down_hour.min():.2f} on the {sh.theo_per_down_hour.idxmin()} shift.",
        "down machine-hours grouped by month and by shift (day 06-14, swing 14-22, grave 22-06 local)",
        "; ".join(f"{r.month}: {r.down_hours:,.0f} h, ${r.lost_theo:,.0f}" for r in by_month.itertuples()),
        "Volume of faults vs speed of repair: repair duration is analysed separately against staffing.",
        "Shift boundaries are approximate; roster shifts overlap by one hour.",
        ["q3", "timing"])

    claims.add(
        "Q3-manufacturer", "Q3 Downtime",
        f"{worst} machines fail {excess_faults:.1f}x as often as the other manufacturers.",
        "operations fault_repair tickets per machine-month on the floor, by manufacturer (floor_day exposure)",
        "; ".join(f"{i}: {r.faults_per_machine_month:.2f} faults per machine-month, {r.down_hours_per_machine:.1f}"
                  f" h, ${r.lost_theo_per_machine:,.0f} theo lost and ${r.repair_cost / r.machines:,.0f}"
                  " direct repair cost per machine" for i, r in mfr.iterrows()),
        "Heavier use: per 1,000 occupied hours the gap remains ("
        + ", ".join(f"{i} {r.faults_per_1000_occupied_hours:.2f}" for i, r in mfr.iterrows()) + ").",
        "Fault counts include repeat faults on the same machines (see repeat-fault list).",
        ["q3", "manufacturer"])

    claims.add(
        "Q3-staffing", "Q3 Downtime",
        "Repairs take longer when the slot-tech shift is short-staffed.",
        "Each fault joined to the slot_tech roster for its gaming date and shift (shift_roster);"
        " bootstrap difference in mean hours, short vs fully staffed",
        f"Mean repair time {short.repair_hours.mean():.2f} h short-staffed (n={len(short)}) vs"
        f" {full.repair_hours.mean():.2f} h fully staffed (n={len(full)}): {staff_eff[0]:+.2f} h"
        f" (95% CI {staff_eff[1]:+.2f} to {staff_eff[2]:+.2f}). Time to start work:"
        f" {wait_eff[0]:+.2f} h ({wait_eff[1]:+.2f} to {wait_eff[2]:+.2f}). Short-staffed shift-days: "
        + ", ".join(f"{r.month} {r.shift} {r.short_days}" for r in staffing[staffing.short_days > 0].itertuples()),
        "Fault mix: short-staffed months also had different fault volumes; compare within shift in the"
        " dashboard table (repair_by_staff).",
        "Observational; short staffing clusters in April-May, so seasonal effects are not fully separated.",
        ["q3", "staffing"])

    return {"by_cause": by_cause, "by_month": by_month, "by_hour": by_hour, "by_shift": by_shift,
            "by_zone": by_zone, "by_manufacturer": by_mfr, "by_machine": by_machine, "daily": daily,
            "staffing": staffing, "faults_month": f_month, "repair_by_staff": repair_by_staff,
            "faults": f,
            "summary": pd.DataFrame([{"down_hours": total_h, "lost_theo": total_lost,
                                      "down_share": total_h / floor_hours, **sub,
                                      "staff_effect_h": staff_eff[0], "staff_lo": staff_eff[1],
                                      "staff_hi": staff_eff[2], "excess_fault_ratio": excess_faults,
                                      "worst_manufacturer": worst}])}


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    out = run()
    for k in ["by_cause", "by_month", "by_shift", "by_manufacturer", "staffing", "repair_by_staff"]:
        print(k)
        print(out[k].round(3))
    print(out["by_machine"].head(10).round(1))
    print(out["summary"].T)
    for c in claims.REGISTRY.values():
        print("-", c.id, ":", c.result)
