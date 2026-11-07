"""Q4: what tracked (carded) players wagered, got back and netted, and how concentrated it is.

Player tables cover loyalty-card play only. Net is from the player's side: payout - coin-in.
"""
import numpy as np
import pandas as pd

from . import claims
from .db import df


def players() -> pd.DataFrame:
    p = df("""
        SELECT player_id, any_value(home_region) home_region,
               coalesce(any_value(age_band), 'Unknown') age_band, any_value(opening_tier) opening_tier,
               arg_max(tier_end, period_month) tier_end, count(*) active_months,
               sum(observed_visits) visits, sum(sessions) sessions, sum(carded_play_hours) play_hours,
               sum(tracked_coin_in_usd)::DOUBLE coin_in, sum(tracked_payout_usd)::DOUBLE payout,
               sum(tracked_net_usd)::DOUBLE net, sum(theo_usd)::DOUBLE theo,
               sum(luck_residual_usd)::DOUBLE luck, sum(comp_cost_usd)::DOUBLE comp_cost,
               sum(tracked_contribution_usd)::DOUBLE contribution
        FROM player_period GROUP BY 1""")
    p["ahead"] = p.net > 0
    return p


def lorenz(values: np.ndarray, points: int = 101) -> tuple[pd.DataFrame, float]:
    v = np.sort(np.clip(values, 0, None))
    cum = np.concatenate([[0], np.cumsum(v)]) / v.sum()
    x = np.linspace(0, 1, points)
    y = np.interp(x, np.linspace(0, 1, len(cum)), cum)
    gini = 1 - 2 * np.trapezoid(cum, np.linspace(0, 1, len(cum)))
    return pd.DataFrame({"population_share": x, "value_share": y}), float(gini)


def top_share(values: np.ndarray, frac: float) -> float:
    v = np.sort(np.clip(values, 0, None))[::-1]
    k = max(1, int(round(frac * len(v))))
    return float(v[:k].sum() / v.sum())


def segment_table(p: pd.DataFrame, col: str) -> pd.DataFrame:
    total_theo, total_loss = p.theo.sum(), (-p.net).clip(lower=0).sum()
    g = p.groupby(col).agg(players=("player_id", "size"), coin_in=("coin_in", "sum"),
                           payout=("payout", "sum"), net=("net", "sum"), theo=("theo", "sum"),
                           luck=("luck", "sum"), visits=("visits", "sum"), ahead=("ahead", "mean"),
                           comp_cost=("comp_cost", "sum"))
    g["loss"] = p.assign(loss=(-p.net).clip(lower=0)).groupby(col).loss.sum()
    g["coin_in_per_player"] = g.coin_in / g.players
    g["net_per_player"] = g.net / g.players
    g["theo_per_player"] = g.theo / g.players
    g["visits_per_player"] = g.visits / g.players
    g["hold"] = -g.net / g.coin_in
    g["share_of_theo"] = g.theo / total_theo
    g["share_of_losses"] = g.loss / total_loss
    g["share_of_players"] = g.players / len(p)
    return g.reset_index().rename(columns={col: "segment"}).assign(dimension=col)


def run() -> dict[str, pd.DataFrame]:
    p = players()
    n = len(p)
    tot = p[["coin_in", "payout", "net", "theo", "luck"]].sum()

    lz_theo, gini_theo = lorenz(p.theo.values)
    lz_loss, gini_loss = lorenz((-p.net).values)
    lz_coin, gini_coin = lorenz(p.coin_in.values)
    lor = pd.concat([lz_theo.assign(metric="theo"), lz_loss.assign(metric="losses"),
                     lz_coin.assign(metric="coin_in")])
    shares = {
        "top1_theo": top_share(p.theo.values, 0.01), "top10_theo": top_share(p.theo.values, 0.10),
        "top1_loss": top_share((-p.net).values, 0.01), "top10_loss": top_share((-p.net).values, 0.10),
        "gini_theo": gini_theo, "gini_loss": gini_loss, "gini_coin_in": gini_coin,
    }

    segs = pd.concat([segment_table(p, c) for c in ("opening_tier", "age_band", "home_region", "tier_end")])

    gamers = p[p.coin_in > 0].copy()
    gamers["theo_decile"] = pd.qcut(gamers.theo.rank(method="first"), 10, labels=range(1, 11)).astype(int)
    by_decile = gamers.groupby("theo_decile").agg(players=("player_id", "size"), theo_mean=("theo", "mean"),
                                             net_mean=("net", "mean"), ahead=("ahead", "mean"),
                                             coin_in=("coin_in", "sum")).reset_index()

    monthly = df("""
        SELECT period_month AS month, count(*) players, sum(tracked_coin_in_usd)::DOUBLE coin_in,
               sum(tracked_payout_usd)::DOUBLE payout, sum(tracked_net_usd)::DOUBLE net,
               sum(theo_usd)::DOUBLE theo, sum(luck_residual_usd)::DOUBLE luck,
               avg((tracked_net_usd > 0)::INT) ahead_share
        FROM player_period GROUP BY 1 ORDER BY 1""")
    recon = df("""
        SELECT strftime(gaming_date, '%Y-%m') AS month, sum(coin_in_cents) / 100.0 total_coin_in,
               sum(carded_coin_in_cents) / 100.0 carded_coin_in,
               sum(carded_coin_in_cents - carded_payout_cents) / 100.0 carded_house_win,
               sum(house_win_cents) / 100.0 total_house_win
        FROM machine_day GROUP BY 1 ORDER BY 1""").merge(
        monthly[["month", "coin_in", "net"]].rename(columns={"coin_in": "player_coin_in", "net": "player_net"}),
        on="month")
    recon["carded_share"] = recon.carded_coin_in / recon.total_coin_in
    recon["gap"] = recon.carded_coin_in - recon.player_coin_in

    edges = [-np.inf, -10000, -2500, -1000, -500, -250, -100, -50, -10, 0, 10, 50, 100, 250, 500, 1000, np.inf]
    labels = ["<-10k", "-10k..-2.5k", "-2.5k..-1k", "-1k..-500", "-500..-250", "-250..-100", "-100..-50",
              "-50..-10", "-10..0", "0..10", "10..50", "50..100", "100..250", "250..500", "500..1k", ">1k"]
    p["net_bin"] = pd.cut(p.net, edges, labels=labels, right=False)
    hist = p.groupby("net_bin", observed=False).agg(players=("player_id", "size"),
                                                     net=("net", "sum")).reset_index()

    cut = p.net.quantile(0.01)
    tail = p[p.net <= cut]
    rest = p[p.net > cut]
    tail_profile = pd.DataFrame([{
        "group": name, "players": len(g), "net_mean": g.net.mean(), "theo_mean": g.theo.mean(),
        "luck_mean": g.luck.mean(), "visits_mean": g.visits.mean(), "play_hours_mean": g.play_hours.mean(),
        "share_65_plus": (g.age_band == "65+").mean(), "share_local": (g.home_region == "Local").mean(),
        "share_gold_plus": g.opening_tier.isin(["Gold", "Platinum"]).mean(),
    } for name, g in (("heaviest-loss 1%", tail), ("other 99%", rest))])

    ahead = gamers.ahead.mean()
    d = by_decile.set_index("theo_decile")
    claims.add(
        "Q4-outcomes", "Q4 Tracked player outcomes",
        f"Tracked players wagered ${tot.coin_in:,.0f}, got back ${tot.payout:,.0f} and netted"
        f" ${tot.net:,.0f}; {ahead:.1%} of those who gambled finished the six months ahead.",
        "player_period summed per player (loyalty-card play only)",
        f"{n:,} card holders, {len(gamers):,} with carded gaming ({n - len(gamers):,} used the card only"
        f" for food and drink); hold {(-tot.net) / tot.coin_in:.2%} vs theo {tot.theo / tot.coin_in:.2%};"
        f" combined luck residual ${tot.luck:,.0f}. Ahead share falls from {d.ahead.iloc[0]:.0%} in the"
        f" lightest theo decile to {d.ahead.iloc[-1]:.0%} in the heaviest.",
        "Luck vs skill: net = -theo + luck; ahead players are those whose luck exceeded their theo,"
        " which becomes rarer the more they play.",
        "Uncarded play (about a third of coin-in) is invisible at the person level.",
        ["q4"])

    claims.add(
        "Q4-concentration", "Q4 Tracked player outcomes",
        f"Results are highly concentrated: the top 1% of players produce {shares['top1_theo']:.0%} of"
        f" tracked theo and the top 10% produce {shares['top10_theo']:.0%}.",
        "Lorenz curves and Gini coefficients on per-player theo and losses (player_period)",
        f"Gini theo {gini_theo:.2f}, losses {gini_loss:.2f}, coin-in {gini_coin:.2f}. Top 1% of losses:"
        f" {shares['top1_loss']:.0%}; top 10%: {shares['top10_loss']:.0%}.",
        "Short observation: many players visit once; concentration over a longer window could differ.",
        "Tracked guests only; a guest playing partly uncarded looks lighter than they are.",
        ["q4", "concentration"])

    region = segs[segs.dimension == "home_region"].set_index("segment")
    claims.add(
        "Q4-locals", "Q4 Tracked player outcomes",
        f"Local players are {region.loc['Local', 'share_of_players']:.0%} of card holders but produce"
        f" {region.loc['Local', 'share_of_theo']:.0%} of tracked theo.",
        "player_period grouped by home_region",
        "; ".join(f"{i}: {r.share_of_players:.0%} of players, {r.share_of_theo:.0%} of theo,"
                  f" {r.visits_per_player:.1f} visits, ${r.net_per_player:,.0f} net per player"
                  for i, r in region.iterrows()),
        "Tier: locals are also over-represented in Gold and Platinum, so tier and residence overlap.",
        "Home region is coarse and self-reported at enrolment.",
        ["q4", "segments"])

    tp = tail_profile.set_index("group")
    claims.add(
        "Q4-heavy-loss", "Q4 Tracked player outcomes",
        "The heaviest-loss 1% of players lose far more per visit and are a group for protective outreach,"
        " not for more marketing.",
        "Players at or below the 1st percentile of net vs everyone else (player_period)",
        f"Heaviest-loss 1% (n={int(tp.loc['heaviest-loss 1%', 'players'])}): mean net"
        f" ${tp.loc['heaviest-loss 1%', 'net_mean']:,.0f}, mean theo ${tp.loc['heaviest-loss 1%', 'theo_mean']:,.0f},"
        f" {tp.loc['heaviest-loss 1%', 'visits_mean']:.1f} visits; others: mean net"
        f" ${tp.loc['other 99%', 'net_mean']:,.0f}, {tp.loc['other 99%', 'visits_mean']:.1f} visits.",
        "Bad luck vs volume: the tail's mean luck residual is"
        f" ${tp.loc['heaviest-loss 1%', 'luck_mean']:,.0f} against mean theo"
        f" ${tp.loc['heaviest-loss 1%', 'theo_mean']:,.0f}, so volume of play, not only luck, drives it.",
        "Synthetic guests; no information on affordability. Any outreach should be opt-in.",
        ["q4", "responsible"])

    claims.add(
        "Q4-reconciliation", "Q4 Tracked player outcomes",
        "Player tables reconcile exactly with the carded meters; they cover about two-thirds of all play.",
        "machine_day carded_coin_in_cents vs player_period tracked_coin_in_usd by month",
        f"Maximum monthly gap ${recon.gap.abs().max():,.2f}; carded share"
        f" {recon.carded_share.min():.1%}-{recon.carded_share.max():.1%}.",
        "Data error: the exact match rules out missing carded sessions.",
        "Uncarded guests can win as a group, so carded and total house win move differently.",
        ["q4", "reconciliation"])

    return {"players": p, "segments": segs, "lorenz": lor, "theo_deciles": by_decile, "monthly": monthly,
            "reconciliation": recon, "net_histogram": hist, "tail_profile": tail_profile,
            "summary": pd.DataFrame([{"players": n, "gamers": len(gamers), **tot.to_dict(),
                                      "ahead_share": ahead, **shares}])}


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    out = run()
    print(out["segments"][["dimension", "segment", "players", "coin_in_per_player", "net_per_player", "ahead",
                           "share_of_theo", "share_of_losses"]].round(3))
    print(out["theo_deciles"].round(2))
    print(out["tail_profile"].round(2))
    print(out["summary"].T)
    for c in claims.REGISTRY.values():
        print("-", c.id, ":", c.result)
