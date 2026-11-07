"""Write the dashboard data contract: compact JSON in frontend/public/data/.

Small tables are arrays of records. Large tables (machine_day_slim, zone_day, faults, player_groups)
are columnar ({column: [values]}) with dictionary-coded ids so the browser can re-aggregate any
date range without a server.
"""
import json
from datetime import date, datetime

import numpy as np
import pandas as pd

from . import claims
from .db import ROOT, df

OUT = ROOT.parent / "frontend" / "public" / "data"

SCORECARD_COLS = [
    "machine_id", "zone_id", "bank_id", "location_id", "manufacturer", "lease_class", "config_id",
    "volatility_class", "configured_rtp", "theme", "first_day", "last_day", "days_on", "retired",
    "available_hours", "occupied_hours", "coin_in", "house_win", "theo", "contribution", "faults",
    "availability", "occupancy", "hold", "theo_hold", "luck", "luck_z", "luck_q", "hit_rate", "hit_expected",
    "hit_z", "hit_q", "theo_per_hour", "house_win_per_hour", "expected_theo_config", "expected_theo_location",
    "wf_reference", "wf_partial_window", "wf_downtime", "wf_game_mix", "wf_location", "wf_machine", "wf_luck",
    "machine_effect", "effect_h1", "effect_h2", "payout_anomaly", "primary_driver",
]


def _value(v):
    if v is None:
        return None
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        if not np.isfinite(v):
            return None
        return float(round(v, 4))
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d") if v == v.normalize() else v.strftime("%Y-%m-%dT%H:%M")
    if isinstance(v, datetime):
        return v.isoformat(timespec="minutes")
    if isinstance(v, date):
        return v.isoformat()
    if v is pd.NaT or (isinstance(v, float) and np.isnan(v)):
        return None
    return v if isinstance(v, (str, int, list, dict)) else str(v)


def records(d: pd.DataFrame) -> list[dict]:
    cols = list(d.columns)
    return [{c: _value(v) for c, v in zip(cols, row)} for row in d.itertuples(index=False, name=None)]


def columnar(d: pd.DataFrame) -> dict[str, list]:
    return {c: [_value(v) for v in d[c].tolist()] for c in d.columns}


def _write(name: str, payload) -> int:
    path = OUT / f"{name}.json"
    text = json.dumps(payload, separators=(",", ":"), allow_nan=False)
    path.write_text(text, encoding="utf-8")
    return len(text)


def machine_day_slim() -> dict:
    d = df("""
        SELECT gaming_date, machine_id, scheduled_hours, available_hours, occupied_hours,
               coin_in, house_win, theo, faults_opened
        FROM floor_day ORDER BY gaming_date, machine_id""")
    dates = sorted(d.gaming_date.unique())
    machines = sorted(d.machine_id.unique())
    return {
        "dates": [_value(pd.Timestamp(x)) for x in dates],
        "machines": machines,
        "d": d.gaming_date.map({x: i for i, x in enumerate(dates)}).tolist(),
        "m": d.machine_id.map({x: i for i, x in enumerate(machines)}).tolist(),
        "sched": d.scheduled_hours.round(2).tolist(),
        "avail": d.available_hours.round(2).tolist(),
        "occ": d.occupied_hours.round(2).tolist(),
        "coin_in": d.coin_in.round(0).astype(int).tolist(),
        "house_win": d.house_win.round(0).astype(int).tolist(),
        "theo": d.theo.round(1).tolist(),
        "faults": d.faults_opened.astype(int).tolist(),
    }


def player_groups() -> dict:
    g = df("""
        SELECT period_month AS month, tier_end AS tier, coalesce(age_band, 'Unknown') AS age_band,
               home_region, count(*) players, sum(observed_visits) visits,
               sum(tracked_coin_in_usd)::DOUBLE coin_in, sum(tracked_payout_usd)::DOUBLE payout,
               sum(tracked_net_usd)::DOUBLE net, sum(theo_usd)::DOUBLE theo,
               sum(comp_cost_usd)::DOUBLE comp_cost, sum((tracked_net_usd > 0)::INT) ahead
        FROM player_period GROUP BY ALL ORDER BY ALL""")
    return columnar(g)


def floor_map() -> list[dict]:
    return records(df("""
        SELECT location_id, parent_location_id, node_type, zone_id, bank_id, name, x_m, y_m, capacity
        FROM floor_locations"""))


def write(r: dict) -> dict[str, int]:
    OUT.mkdir(parents=True, exist_ok=True)
    q1, q2, q3, q4, q5, m, b = (r[k] for k in ("q1", "q2", "q3", "q4", "q5", "model", "budget"))
    sizes = {}
    sizes["machine_day_slim"] = _write("machine_day_slim", machine_day_slim())
    sizes["machines"] = _write("machines", {
        "scorecard": records(q1["scorecard"][SCORECARD_COLS]),
        "manager_list": records(q1["manager_list"][["machine_id", "manager_rank", "status", "primary_driver"]]),
        "truly_weak": records(q1["truly_weak"][["machine_id", "persistent_weak", "reason"]]),
        "config_rates": records(q1["config_rates"]),
        "zone_factors": records(q1["zone_factors"]),
        "anomaly_monthly": records(q1["anomaly_monthly"]),
        "summary": records(q1["summary"])[0],
    })
    sizes["demand"] = _write("demand", {
        "daily": records(q2["daily"]),
        "weekday": records(q2["weekday"]),
        "events": records(q2["events"]),
        "renovation_daily": records(q2["renovation_daily"]),
        "renovation_monthly": records(q2["renovation_monthly"]),
        "monthly": records(q2["monthly"]),
        "summary": records(q2["summary"])[0],
    })
    sizes["zone_day"] = _write("zone_day", columnar(q2["zone_day"].merge(
        q2["traffic_day"], on=["gaming_date", "zone_id"], how="left")))
    sizes["downtime"] = _write("downtime", {
        k: records(q3[k]) for k in ("by_cause", "by_month", "by_hour", "by_shift", "by_zone", "by_manufacturer",
                                    "by_machine", "daily", "staffing", "faults_month", "repair_by_staff")
    } | {"summary": records(q3["summary"])[0]})
    sizes["faults"] = _write("faults", columnar(q3["faults"].drop(columns=["planned", "actual"])))
    sizes["players"] = _write("players", {
        k: records(q4[k]) for k in ("segments", "lorenz", "theo_deciles", "monthly", "reconciliation",
                                    "net_histogram", "tail_profile")
    } | {"summary": records(q4["summary"])[0]})
    sizes["player_groups"] = _write("player_groups", player_groups())
    sizes["comps"] = _write("comps", {
        k: records(q5[k]) for k in ("daily", "monthly", "by_tier", "its", "redemption_rates")
    } | {"summary": records(q5["summary"])[0]})
    sizes["forecast"] = _write("forecast", {
        k: records(m[k]) for k in ("selection", "holdout", "metrics", "by_weekday", "july", "factors")
    } | {"summary": records(m["summary"])[0]})
    sizes["budget"] = _write("budget", {"actions": records(b["actions"]), "summary": records(b["summary"])[0]})
    sizes["floor_map"] = _write("floor_map", floor_map())
    sizes["claims"] = _write("claims", claims.as_records())
    sizes["meta"] = _write("meta", {
        "window_start": "2025-01-01", "window_end": "2025-06-30", "budget_window": "2025-07-01 to 2025-07-30",
        "holdout": "2025-05-01 to 2025-06-30", "files": sorted(sizes),
        "note": "The Gilded Ace is fictional and the data synthetic. Money in US dollars.",
    })
    return sizes
