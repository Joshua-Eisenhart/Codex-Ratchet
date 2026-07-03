"""QUARANTINE_EXPLORATORY: deterministic shared 3q world fixture.

classification='scratch_diagnostic'; promotion_allowed=false.

Mechanics mirror qit_live_loop_3q_v1/world_fixture_3q.py with seed 20260704
for this eps-sheet direct/conjugated dual-engine run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from common_dual_engine import CLASSIFICATION, PROMOTION_ALLOWED, RESULTS_DIR, clean_float, deterministic_iso


def segment_for_tick(tick: int) -> tuple[str, float]:
    if tick < 100:
        return "A_stationary", 0.82
    if tick < 200:
        return "B_stationary", 0.22
    drift = (tick - 200) / 99.0 if tick <= 299 else 1.0
    return "C_drift", 0.35 + 0.40 * drift


def build_fixture(ticks: int = 300, seed: int = 20260704) -> dict:
    rng = np.random.default_rng(seed)
    records = []
    for tick in range(ticks):
        segment, p0 = segment_for_tick(tick)
        p0 = clean_float(p0)
        outcome = int(rng.random() >= p0)
        records.append(
            {
                "tick": tick,
                "t_iso": deterministic_iso(tick),
                "world_segment": segment,
                "signal_povm": {"p0": p0, "p1": clean_float(1.0 - p0)},
                "outcome": outcome,
                "shift_marker": tick in (100, 200),
            }
        )
    return {
        "schema": "cr.qit_dual_engine_live_v0.world_fixture.v1",
        "ticks_requested": ticks,
        "ticks": records,
        "seed": seed,
        "deterministic": True,
        "segments": {
            "A_stationary": {"tick_start": 0, "tick_end": 99, "p0": 0.82},
            "B_stationary": {"tick_start": 100, "tick_end": 199, "p0": 0.22},
            "C_drift": {"tick_start": 200, "tick_end": ticks - 1, "p0_start": 0.35, "p0_end": 0.75},
        },
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "quarantine": "QUARANTINE_EXPLORATORY",
    }


def write_fixture(out: Path, ticks: int = 300, seed: int = 20260704) -> dict:
    fixture = build_fixture(ticks=ticks, seed=seed)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n")
    return fixture


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate qit_dual_engine_live_v0 deterministic fixture")
    parser.add_argument("--ticks", type=int, default=300)
    parser.add_argument("--seed", type=int, default=20260704)
    parser.add_argument("--out", type=Path, default=RESULTS_DIR / "world_fixture.json")
    args = parser.parse_args()
    fixture = write_fixture(args.out, ticks=args.ticks, seed=args.seed)
    print(json.dumps({"fixture": str(args.out), "ticks": len(fixture["ticks"]), "seed": fixture["seed"]}, sort_keys=True))


if __name__ == "__main__":
    main()
