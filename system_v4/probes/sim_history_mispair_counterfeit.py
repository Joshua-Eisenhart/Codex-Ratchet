#!/usr/bin/env python3
"""
sim_history_mispair_counterfeit.py
==================================

Negative probe for a history-counterfeit carrier:
preserve one-body history marginals while mispairing L and R across steps.

This tests whether the lower theorem lane is rewarding genuine live pairing
or merely any history-rich cross-pairing under the current bridge metric.
"""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from engine_core import GeometricEngine, EngineState
from geometric_operators import _ensure_valid_density
from sim_axis0_bridge_search import TORUS_CONFIGS, ALL_CANDIDATES, full_metrics
classification = "classical_baseline"  # auto-backfill


ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "a2_state" / "sim_results" / "history_mispair_counterfeit_results.json"


def product_state(rho_l: np.ndarray, rho_r: np.ndarray) -> np.ndarray:
    return _ensure_valid_density(np.kron(rho_l, rho_r))


def shifted_mispair(state: EngineState) -> EngineState:
    new_state = copy.deepcopy(state)
    history = state.history
    if not history:
        new_state.history = []
        new_state.rho_AB = product_state(state.rho_L, state.rho_R)
        return new_state

    shifted = []
    n = len(history)
    for idx, entry in enumerate(history):
        partner = history[(idx + 1) % n]
        new_entry = dict(entry)
        new_entry["rho_L"] = entry["rho_L"]
        new_entry["rho_R"] = partner["rho_R"]
        shifted.append(new_entry)

    new_state.history = shifted
    new_state.rho_AB = product_state(state.rho_L, history[0]["rho_R"])
    return new_state


def run_probe() -> dict:
    rows = []
    live_i_vals = []
    fake_i_vals = []
    live_ic_vals = []
    fake_ic_vals = []

    candidate_fn = ALL_CANDIDATES["Xi_chiral_entangle"]

    for engine_type in (1, 2):
        engine = GeometricEngine(engine_type=engine_type)
        for torus_label, eta in TORUS_CONFIGS:
            init_state = engine.init_state(eta=eta, theta1=0.0, theta2=0.0)
            live_state = engine.run_cycle(init_state)
            fake_state = shifted_mispair(live_state)

            live_rho, _ = candidate_fn(live_state)
            fake_rho, _ = candidate_fn(fake_state)
            live_metrics = full_metrics(live_rho)
            fake_metrics = full_metrics(fake_rho)

            live_i_vals.append(live_metrics["I_AB"])
            fake_i_vals.append(fake_metrics["I_AB"])
            live_ic_vals.append(live_metrics["I_c"])
            fake_ic_vals.append(fake_metrics["I_c"])

            rows.append(
                {
                    "engine_type": engine_type,
                    "torus": torus_label,
                    "eta": float(eta),
                    "live": live_metrics,
                    "counterfeit": fake_metrics,
                    "delta_I_AB": float(live_metrics["I_AB"] - fake_metrics["I_AB"]),
                    "delta_I_c": float(live_metrics["I_c"] - fake_metrics["I_c"]),
                }
            )

    summary = {
        "mean_live_I_AB": float(np.mean(live_i_vals)),
        "mean_counterfeit_I_AB": float(np.mean(fake_i_vals)),
        "mean_live_I_c": float(np.mean(live_ic_vals)),
        "mean_counterfeit_I_c": float(np.mean(fake_ic_vals)),
        "mean_I_AB_gap": float(np.mean(live_i_vals) - np.mean(fake_i_vals)),
        "mean_I_c_gap": float(np.mean(live_ic_vals) - np.mean(fake_ic_vals)),
        "counterfeit_beats_live_on_I_AB_count": int(sum(f > l for l, f in zip(live_i_vals, fake_i_vals))),
        "live_beats_counterfeit_on_I_c_count": int(sum(l > f for l, f in zip(live_ic_vals, fake_ic_vals))),
    }

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "probe": "sim_history_mispair_counterfeit",
        "bridge_candidate": "Xi_chiral_entangle",
        "rows": rows,
        "summary": summary,
    }


def main() -> int:
    payload = run_probe()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    summary = payload["summary"]
    print("=" * 72)
    print("HISTORY MISPAIR COUNTERFEIT")
    print("=" * 72)
    print(f"mean_live_I_AB: {summary['mean_live_I_AB']:.6f}")
    print(f"mean_counterfeit_I_AB: {summary['mean_counterfeit_I_AB']:.6f}")
    print(f"mean_live_I_c: {summary['mean_live_I_c']:.6f}")
    print(f"mean_counterfeit_I_c: {summary['mean_counterfeit_I_c']:.6f}")
    print(f"counterfeit_beats_live_on_I_AB_count: {summary['counterfeit_beats_live_on_I_AB_count']}")
    print(f"live_beats_counterfeit_on_I_c_count: {summary['live_beats_counterfeit_on_I_c_count']}")
    print(f"results: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
