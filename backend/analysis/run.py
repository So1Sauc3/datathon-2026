"""Run the whole analysis end to end: python -m analysis.run (from backend/)."""
import time

from . import budget, claims, export, model_forecast, q1_machines, q2_demand, q3_downtime, q4_players, q5_comps
from .db import ROOT


def main() -> dict:
    claims.REGISTRY.clear()
    steps = [("q1", q1_machines.run), ("q2", q2_demand.run), ("q3", q3_downtime.run), ("q4", q4_players.run),
             ("q5", q5_comps.run), ("model", model_forecast.run)]
    r = {}
    for name, fn in steps:
        t = time.perf_counter()
        r[name] = fn()
        print(f"{name:<7} {time.perf_counter() - t:6.1f}s")
    r["budget"] = budget.run(r["q1"], r["q2"], r["q3"], r["q5"], r["model"])

    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    (out / "CLAIMS_AND_EVIDENCE.md").write_text(claims.to_markdown(), encoding="utf-8")
    sizes = export.write(r)
    print(f"{len(claims.REGISTRY)} claims -> {out / 'CLAIMS_AND_EVIDENCE.md'}")
    for name, n in sizes.items():
        print(f"  {name + '.json':<24} {n / 1024:8.0f} KB")
    return r


if __name__ == "__main__":
    main()
