"""Shared DuckDB connection: one view per dataset plus the filters every module needs."""
from functools import lru_cache
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

TABLES = {
    "prepared_daily_view": "1_prepared_views/prepared_daily_view",
    "property_day": "1_prepared_views/property_day",
    "player_period": "1_prepared_views/player_period",
    "action_catalog": "2_machine_decision/action_catalog",
    "calendar_day": "2_machine_decision/calendar_day",
    "cost_rules": "2_machine_decision/cost_rules",
    "floor_locations": "2_machine_decision/floor_locations",
    "floor_walkways": "2_machine_decision/floor_walkways",
    "game_math": "2_machine_decision/game_math",
    "machine_day": "2_machine_decision/machine_day",
    "machines": "2_machine_decision/machines",
    "operations": "2_machine_decision/operations",
    "placements": "2_machine_decision/placements",
    "players": "3_guests/players",
    "sessions": "3_guests/sessions",
    "trips": "3_guests/trips",
    "loyalty_ledger": "3_guests/loyalty_ledger",
    "fnb_transactions": "3_guests/fnb_transactions",
    "events": "4_context/events",
    "zone_traffic_hourly": "4_context/zone_traffic_hourly",
    "weather_daily": "4_context/real_sources/weather_daily",
    "city_visitation_monthly": "4_context/real_sources/city_visitation_monthly",
    "benchmark_state_monthly": "4_context/real_sources/benchmark_state_monthly",
    "benchmark_property_monthly": "4_context/real_sources/benchmark_property_monthly",
    "machine_hour": "5_optional/machine_hour",
    "shift_roster": "5_optional/shift_roster",
    "security_incidents": "5_optional/security_incidents",
    "visitor_profile_monthly": "5_optional/visitor_profile_monthly",
}

WINDOW_START = pd.Timestamp("2025-01-01")
WINDOW_END = pd.Timestamp("2025-06-30")

# Gaming days run 06:00 to 06:00 local, so a local timestamp minus six hours lands on its gaming date.
MACROS = """
CREATE OR REPLACE MACRO gaming_date_of(ts_local) AS CAST(ts_local - INTERVAL 6 HOUR AS DATE);
CREATE OR REPLACE MACRO shift_of(local_hour) AS CASE
    WHEN local_hour >= 6 AND local_hour < 14 THEN 'day'
    WHEN local_hour >= 14 AND local_hour < 22 THEN 'swing'
    ELSE 'grave' END;
"""

# Machine-days on the floor, in dollars, with game math and placement attached.
FLOOR_DAY = """
CREATE OR REPLACE VIEW floor_day AS
SELECT
    md.machine_id, md.gaming_date, p.month, p.local_weekday, p.is_weekend, p.events_active,
    p.zone_id, p.zone_name, p.bank_id, md.location_id, md.config_id,
    m.manufacturer, m.lease_class, gm.configured_rtp, gm.volatility_class,
    gm.hit_probability, gm.payout_multiplier_variance,
    md.scheduled_seconds / 3600.0 AS scheduled_hours,
    md.available_seconds / 3600.0 AS available_hours,
    md.occupied_seconds / 3600.0 AS occupied_hours,
    md.paid_spins, md.payout_positive_spins,
    md.coin_in_cents / 100.0 AS coin_in,
    md.payout_cents / 100.0 AS payout,
    md.house_win_cents / 100.0 AS house_win,
    CAST(md.theo_cents AS DOUBLE) / 100.0 AS theo,
    md.sum_bet_squared * CAST(gm.payout_multiplier_variance AS DOUBLE) / 1e4 AS win_variance,
    md.carded_coin_in_cents / 100.0 AS carded_coin_in,
    CAST(p.contribution_after_supplied_costs_usd AS DOUBLE) AS contribution,
    CAST(p.lease_cost_usd + p.service_cost_usd + p.power_cost_usd + p.repair_cost_usd AS DOUBLE)
        AS supplied_costs,
    p.faults_opened
FROM machine_day md
JOIN prepared_daily_view p USING (machine_id, gaming_date)
JOIN game_math gm ON gm.config_id = md.config_id
JOIN machines m USING (machine_id)
WHERE md.active AND md.location_id IS NOT NULL
"""


@lru_cache(maxsize=1)
def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    for name, path in TABLES.items():
        con.read_parquet(str(DATA / f"{path}.parquet")).create_view(name)
    con.execute(MACROS)
    con.execute(FLOOR_DAY)
    return con


def df(sql: str, params: list | None = None) -> pd.DataFrame:
    return connect().execute(sql, params or []).df()
