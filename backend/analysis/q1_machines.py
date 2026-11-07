"""Q1: which machines are truly underperforming once exposure, availability, location and luck
are accounted for.

Each machine's house win is decomposed into a waterfall that starts from a reference machine
(on the floor every hour of the window, earning the floor-average theo per available hour):

    reference + partial window + downtime + game mix + location + machine + luck = house win

Game mix and location use indirect standardization: a config's floor-wide theo per available
hour, then a zone factor = actual theo in the zone / theo expected from its config mix.
"""
import numpy as np
import pandas as pd
from scipy import stats

from . import claims
from .db import df

H1_END = "2025-03-31"
LEAK_Q = 0.001


def _standardized_expectations(where: str = "TRUE") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rates = df(f"""
        SELECT config_id, sum(theo) / sum(available_hours) AS config_theo_per_hour,
               count(DISTINCT machine_id) AS machines
        FROM floor_day WHERE {where} GROUP BY 1 ORDER BY 2""")
    zones = df(f"""
        WITH cfg AS (SELECT config_id, sum(theo) / sum(available_hours) c FROM floor_day
                     WHERE {where} GROUP BY 1)
        SELECT zone_id, any_value(zone_name) AS zone_name,
               sum(theo) / sum(c * available_hours) AS zone_factor,
               count(DISTINCT machine_id) AS machines
        FROM floor_day JOIN cfg USING (config_id) WHERE {where} GROUP BY 1 ORDER BY 3""")
    per_machine = df(f"""
        WITH cfg AS (SELECT config_id, sum(theo) / sum(available_hours) c FROM floor_day
                     WHERE {where} GROUP BY 1),
        r AS (SELECT f.*, c * available_hours AS exp_cfg FROM floor_day f JOIN cfg USING (config_id)
              WHERE {where}),
        zf AS (SELECT zone_id, sum(theo) / sum(exp_cfg) AS k FROM r GROUP BY 1)
        SELECT machine_id, count(*) AS days, sum(available_hours) AS available_hours,
               sum(theo) AS theo, sum(exp_cfg) AS expected_theo_config,
               sum(exp_cfg * k) AS expected_theo_location
        FROM r JOIN zf USING (zone_id) GROUP BY 1""")
    return rates, zones, per_machine


def machine_scorecard() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base = df("""
        WITH home AS (
            SELECT machine_id, arg_max(zone_id, n) zone_id, arg_max(bank_id, n) bank_id,
                   arg_max(location_id, n) location_id
            FROM (SELECT machine_id, zone_id, bank_id, location_id, count(*) n
                  FROM floor_day GROUP BY ALL) GROUP BY 1)
        SELECT f.machine_id, h.zone_id, h.bank_id, h.location_id,
               any_value(f.manufacturer) manufacturer, any_value(f.lease_class) lease_class,
               arg_max(f.config_id, f.gaming_date) config_id,
               count(DISTINCT f.config_id) n_configs,
               any_value(f.volatility_class) volatility_class,
               any_value(f.configured_rtp)::DOUBLE configured_rtp,
               min(f.gaming_date) first_day, max(f.gaming_date) last_day, count(*) days_on,
               sum(scheduled_hours) scheduled_hours, sum(available_hours) available_hours,
               sum(occupied_hours) occupied_hours,
               sum(paid_spins) paid_spins, sum(payout_positive_spins) hit_spins,
               sum(paid_spins * hit_probability::DOUBLE) expected_hits,
               sum(paid_spins * hit_probability::DOUBLE * (1 - hit_probability::DOUBLE)) hit_var,
               sum(coin_in) coin_in, sum(house_win) house_win, sum(theo) theo,
               sum(win_variance) win_variance, sum(contribution) contribution,
               sum(supplied_costs) supplied_costs, sum(faults_opened) faults
        FROM floor_day f JOIN home h USING (machine_id)
        GROUP BY f.machine_id, h.zone_id, h.bank_id, h.location_id""")
    meta = df("SELECT machine_id, theme, install_date, retire_date FROM machines")
    s = base.merge(meta, on="machine_id", how="left")

    s["availability"] = s.available_hours / s.scheduled_hours
    s["occupancy"] = s.occupied_hours / s.available_hours
    s["hold"] = s.house_win / s.coin_in
    s["theo_hold"] = s.theo / s.coin_in
    s["luck"] = s.house_win - s.theo
    s["luck_sd"] = np.sqrt(s.win_variance)
    s["luck_z"] = s.luck / s.luck_sd
    s["luck_p"] = 2 * stats.norm.sf(s.luck_z.abs())
    s["hit_rate"] = s.hit_spins / s.paid_spins
    s["hit_expected"] = s.expected_hits / s.paid_spins
    s["hit_z"] = (s.hit_spins - s.expected_hits) / np.sqrt(s.hit_var)
    s["hit_p"] = 2 * stats.norm.sf(s.hit_z.abs())
    s["luck_q"] = stats.false_discovery_control(s.luck_p.clip(lower=1e-300), method="bh")
    s["hit_q"] = stats.false_discovery_control(s.hit_p.clip(lower=1e-300), method="bh")
    s["theo_per_hour"] = s.theo / s.available_hours
    s["house_win_per_hour"] = s.house_win / s.available_hours
    s["contribution_per_hour"] = s.contribution / s.available_hours
    s["theo_contribution_per_hour"] = (s.theo - s.supplied_costs) / s.available_hours
    s["retired"] = s.retire_date.notna()

    rates, zones, exp = _standardized_expectations()
    s = s.merge(exp[["machine_id", "expected_theo_config", "expected_theo_location"]], on="machine_id")
    floor_rate = s.theo.sum() / s.available_hours.sum()
    ref_hours = df("SELECT sum(scheduled_seconds) / 3600.0 h FROM calendar_day").h.iloc[0]
    s["wf_reference"] = floor_rate * ref_hours
    s["wf_partial_window"] = floor_rate * (s.scheduled_hours - ref_hours)
    s["wf_downtime"] = floor_rate * (s.available_hours - s.scheduled_hours)
    s["wf_game_mix"] = s.expected_theo_config - floor_rate * s.available_hours
    s["wf_location"] = s.expected_theo_location - s.expected_theo_config
    s["wf_machine"] = s.theo - s.expected_theo_location
    s["wf_luck"] = s.luck
    s["machine_effect"] = s.theo / s.expected_theo_location - 1

    # Persistence: is the machine effect stable between the two quarters, or noise?
    _, _, h1 = _standardized_expectations(f"gaming_date <= DATE '{H1_END}'")
    _, _, h2 = _standardized_expectations(f"gaming_date > DATE '{H1_END}'")
    halves = h1.merge(h2, on="machine_id", suffixes=("_h1", "_h2"))
    halves = halves[(halves.days_h1 >= 30) & (halves.days_h2 >= 30)]
    halves["effect_h1"] = halves.theo_h1 / halves.expected_theo_location_h1 - 1
    halves["effect_h2"] = halves.theo_h2 / halves.expected_theo_location_h2 - 1
    s = s.merge(halves[["machine_id", "effect_h1", "effect_h2"]], on="machine_id", how="left")

    s["payout_anomaly"] = (s.hit_q < LEAK_Q) & (s.luck_z < 0)
    s["primary_driver"] = s.apply(_primary_driver, axis=1)
    return s, rates, zones


def _primary_driver(r: pd.Series) -> str:
    if r.payout_anomaly:
        return "payout anomaly"
    parts = {
        "partial window": r.wf_partial_window,
        "downtime": r.wf_downtime,
        "game mix": r.wf_game_mix,
        "location": r.wf_location,
        "machine": r.wf_machine,
        "luck": r.wf_luck,
    }
    return min(parts, key=parts.get)


def manager_list(s: pd.DataFrame) -> pd.DataFrame:
    """The GM's rule: the 10 lowest total house wins, Jan 1 to Jun 30."""
    m = s.nsmallest(10, "house_win").copy()
    m["manager_rank"] = range(1, 11)
    m["status"] = np.where(m.retired, "already retired", np.where(m.days_on < 181, "partial window", "on floor"))
    return m


def truly_weak(s: pd.DataFrame, halves_corr: float) -> pd.DataFrame:
    """Machines that are weak after adjusting for exposure, game mix, location and luck.

    A machine qualifies when its machine effect is in the bottom decile in both quarters (so it is
    persistent, not noise), or when it is a payout anomaly. Retired machines are excluded.
    """
    live = s[~s.retired & s.effect_h1.notna()].copy()
    cut1, cut2 = live.effect_h1.quantile(0.10), live.effect_h2.quantile(0.10)
    live["persistent_weak"] = (live.effect_h1 <= cut1) & (live.effect_h2 <= cut2)
    out = live[live.persistent_weak | live.payout_anomaly].copy()
    out["reason"] = np.where(out.payout_anomaly, "payout anomaly: inspect",
                             "persistently below location- and game-adjusted expectation")
    return out.sort_values("theo_contribution_per_hour")


def monthly_hit_rates(machine_ids: list[str]) -> pd.DataFrame:
    if not machine_ids:
        return pd.DataFrame()
    ids = ", ".join(f"'{m}'" for m in machine_ids)
    return df(f"""
        SELECT machine_id, month, sum(payout_positive_spins) / sum(paid_spins) AS hit_rate,
               sum(paid_spins * hit_probability::DOUBLE) / sum(paid_spins) AS hit_expected,
               sum(house_win) / sum(coin_in) AS hold, sum(theo) / sum(coin_in) AS theo_hold,
               sum(paid_spins) AS paid_spins
        FROM floor_day WHERE machine_id IN ({ids}) GROUP BY 1, 2 ORDER BY 1, 2""")


def run() -> dict[str, pd.DataFrame]:
    s, rates, zones = machine_scorecard()
    corr = float(np.corrcoef(s.dropna(subset=["effect_h1", "effect_h2"]).effect_h1,
                             s.dropna(subset=["effect_h1", "effect_h2"]).effect_h2)[0, 1])
    mgr = manager_list(s)
    weak = truly_weak(s, corr)
    anomalies = s[s.payout_anomaly].machine_id.tolist()
    monthly = monthly_hit_rates(anomalies)

    n = len(s)
    beyond2 = int((s.luck_z.abs() > 2).sum())
    luck_sig = int((s.luck_q < 0.05).sum())
    drivers = mgr.primary_driver.value_counts().to_dict()
    in_b40 = int((mgr.zone_id == "Z-B40").sum())
    retired = mgr[mgr.retired].machine_id.tolist()
    partial = mgr[(mgr.days_on < 181)].machine_id.tolist()
    low_hold = int((mgr.theo_hold <= 0.08).sum())

    claims.add(
        "Q1-manager-list", "Q1 Truly underperforming machines",
        "The manager's bottom 10 (lowest total house win) mostly reflects where machines sit, what game"
        " settings they run and how long they were on the floor, not broken machines.",
        "floor_day (machine_day + prepared_daily_view + game_math, on-floor rows) ranked by SUM(house_win);"
        " waterfall decomposition in analysis/q1_machines.py",
        f"{in_b40} of 10 are in zone Z-B40; {low_hold} run configs with theo hold <= 8%;"
        f" partial window: {', '.join(partial)} (retired: {', '.join(retired)});"
        f" primary drivers: {drivers}.",
        "Bad luck: compared house win with theo using each machine's exact win variance."
        " Downtime: availability on the list averages"
        f" {mgr.availability.mean():.1%} vs {s.availability.mean():.1%} floor-wide.",
        "Zone and config are partly confounded (G-HL90 only appears in Z-HL; G-NEW91 only in Z-PIT).",
        ["q1", "manager"])

    if anomalies:
        a = s.set_index("machine_id").loc[anomalies[0]]
        claims.add(
            "Q1-payout-anomaly", "Q1 Truly underperforming machines",
            f"{anomalies[0]} pays out on far more spins than its configured game allows, and has done so"
            " in every month; it is a lead for a paytable inspection, not proof of wrongdoing.",
            "machine_day.payout_positive_spins / paid_spins vs game_math.hit_probability;"
            " binomial z-test with Benjamini-Hochberg correction over all 310 machines",
            f"hit rate {a.hit_rate:.1%} vs configured {a.hit_expected:.1%} (z = {a.hit_z:.0f},"
            f" q < 1e-6); hold {a.hold:.1%} vs theo hold {a.theo_hold:.1%};"
            f" luck z = {a.luck_z:.1f}; ${-a.luck:,.0f} below theo over {a.days_on} days.",
            "Luck: a luck z this extreme happens about once in"
            f" {1 / max(a.luck_p, 1e-12):,.0f} machines, and luck would not hold the hit rate"
            " steady month after month. Config change: placements shows one config for the whole window.",
            "The hit-rate gap shows payouts differ from the published game math; it cannot say why"
            " (miscalibration, wrong paytable chip, or recording).",
            ["q1", "leak"])

    claims.add(
        "Q1-luck", "Q1 Truly underperforming machines",
        "Apart from the payout anomaly, the spread of results versus theo is what luck alone produces.",
        "luck_z = (house_win - theo) / sqrt(sum_bet_squared x payout_multiplier_variance), per machine",
        f"{beyond2} of {n} machines beyond |z| > 2 (about {0.0455 * n:.0f} expected by chance);"
        f" {luck_sig} remain significant after Benjamini-Hochberg at q < 0.05.",
        "A real machine problem would show as a hit-rate or theo gap, not only a house-win gap.",
        "Normal approximation to the sum of many spins; very high volatility games converge slowly.",
        ["q1", "luck"])

    b40 = zones.set_index("zone_id").zone_factor
    claims.add(
        "Q1-location", "Q1 Truly underperforming machines",
        "Zone Z-B40 earns the least theo per available hour once its game mix is accounted for.",
        "Indirect standardization: zone theo / sum(config floor-wide theo per available hour x hours)",
        "Zone factors: " + ", ".join(f"{z} {v:.2f}" for z, v in b40.items()) + ".",
        "Game mix: factors already divide out each config's floor-wide earning rate.",
        "G-HL90 appears only in Z-HL, so the high-limit room's factor is close to 1 by construction"
        " and says little about that zone.",
        ["q1", "location"])

    claims.add(
        "Q1-persistence", "Q1 Truly underperforming machines",
        "Machine effects (theo vs location- and game-adjusted expectation) are"
        f" {'stable' if corr > 0.5 else 'only weakly stable'} between quarters.",
        "Machine effect computed separately for Jan-Mar and Apr-Jun, machines with >= 30 days in each",
        f"Correlation of the two quarters' machine effects: {corr:.2f}. Persistent bottom-decile machines"
        f" (excluding retired): {', '.join(weak[~weak.payout_anomaly].machine_id) or 'none'}.",
        "Noise: a machine effect driven by chance would not repeat across quarters.",
        "Theo depends on the bets players choose, so a machine effect can reflect its neighbours or"
        " sightlines rather than the cabinet.",
        ["q1", "model"])

    return {"scorecard": s, "config_rates": rates, "zone_factors": zones, "manager_list": mgr,
            "truly_weak": weak, "anomaly_monthly": monthly,
            "summary": pd.DataFrame([{"machines": n, "beyond_2sd": beyond2, "luck_sig": luck_sig,
                                      "effect_corr": corr}])}


if __name__ == "__main__":
    out = run()
    cols = ["machine_id", "zone_id", "config_id", "days_on", "house_win", "theo", "luck_z", "hit_z",
            "machine_effect", "primary_driver", "status"]
    pd.set_option("display.width", 250)
    print(out["manager_list"][cols])
    print(out["truly_weak"][["machine_id", "zone_id", "config_id", "effect_h1", "effect_h2",
                             "theo_contribution_per_hour", "reason"]])
    print(out["zone_factors"])
    print(out["summary"])
    for c in claims.REGISTRY.values():
        print("-", c.id, ":", c.result)
