#!/usr/bin/env python3
"""
sim_root_constraint_carrier_rank.py
===================================

Small carrier-family sweep under the existing bridge/readout surface.

Goal:
  Hold the Xi candidate family fixed and let a small carrier family compete:
    1. live Hopf/Weyl chiral carrier
    2. de-chiralized history control
    3. Cartesian no-history control

This is a lower-ladder theorem-side probe, not a bridge-admission probe.
Raw I_AB is preserved for visibility, but the live read should also expose
a counterfeit-resistant honesty signal.
"""

from __future__ import annotations

import copy
import json
import os
import sys
from datetime import UTC, datetime
from typing import Callable, Dict, List

import numpy as np
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, EngineState
from geometric_operators import _ensure_valid_density
from sim_axis0_bridge_search import ALL_CANDIDATES, TORUS_CONFIGS, full_metrics


def product_state(rho_l: np.ndarray, rho_r: np.ndarray) -> np.ndarray:
    return _ensure_valid_density(np.kron(rho_l, rho_r))


def averaged_pair(rho_l: np.ndarray, rho_r: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    rho_avg = _ensure_valid_density(0.5 * (rho_l + rho_r))
    return rho_avg, rho_avg.copy()


def maximally_mixed_pair() -> tuple[np.ndarray, np.ndarray]:
    rho_mix = 0.5 * np.eye(2, dtype=complex)
    return rho_mix.copy(), rho_mix.copy()


def carrier_live_hopf_weyl(state: EngineState) -> EngineState:
    return copy.deepcopy(state)


def carrier_dechiralized_history(state: EngineState) -> EngineState:
    new_state = copy.deepcopy(state)
    rho_l, rho_r = averaged_pair(state.rho_L, state.rho_R)
    new_state.rho_AB = product_state(rho_l, rho_r)

    new_history = []
    for h in state.history:
        hist_l, hist_r = averaged_pair(h["rho_L"], h["rho_R"])
        new_entry = dict(h)
        new_entry["rho_L"] = hist_l
        new_entry["rho_R"] = hist_r
        new_history.append(new_entry)
    new_state.history = new_history
    return new_state


def carrier_cartesian_nohistory(state: EngineState) -> EngineState:
    new_state = copy.deepcopy(state)
    rho_l, rho_r = averaged_pair(state.rho_L, state.rho_R)
    new_state.rho_AB = product_state(rho_l, rho_r)
    new_state.history = []
    return new_state


def carrier_dechiralized_nohistory(state: EngineState) -> EngineState:
    new_state = copy.deepcopy(state)
    rho_l, rho_r = averaged_pair(state.rho_L, state.rho_R)
    new_state.rho_AB = product_state(rho_l, rho_r)
    new_state.history = []
    return new_state


def carrier_maxmix_history(state: EngineState) -> EngineState:
    new_state = copy.deepcopy(state)
    rho_l, rho_r = maximally_mixed_pair()
    new_state.rho_AB = product_state(rho_l, rho_r)
    new_history = []
    for h in state.history:
        hist_l, hist_r = maximally_mixed_pair()
        new_entry = dict(h)
        new_entry["rho_L"] = hist_l
        new_entry["rho_R"] = hist_r
        new_history.append(new_entry)
    new_state.history = new_history
    return new_state


CARRIERS: Dict[str, Callable[[EngineState], EngineState]] = {
    "carrier_live_hopf_weyl": carrier_live_hopf_weyl,
    "carrier_dechiralized_history": carrier_dechiralized_history,
    "carrier_cartesian_nohistory": carrier_cartesian_nohistory,
    "carrier_dechiralized_nohistory": carrier_dechiralized_nohistory,
    "carrier_maxmix_history": carrier_maxmix_history,
}


def run_probe() -> dict:
    rows: List[dict] = []
    carrier_candidate_metrics: Dict[str, Dict[str, Dict[str, List[float]]]] = {
        carrier: {candidate: {"I_AB": [], "I_c": []} for candidate in ALL_CANDIDATES}
        for carrier in CARRIERS
    }

    for engine_type in (1, 2):
        engine = GeometricEngine(engine_type=engine_type)
        for torus_label, eta in TORUS_CONFIGS:
            init_state = engine.init_state(eta=eta, theta1=0.0, theta2=0.0)
            final_state = engine.run_cycle(init_state)

            row = {
                "engine_type": engine_type,
                "torus": torus_label,
                "eta": float(eta),
                "carriers": {},
            }

            for carrier_name, carrier_fn in CARRIERS.items():
                carrier_state = carrier_fn(final_state)
                row["carriers"][carrier_name] = {}
                for candidate_name, candidate_fn in ALL_CANDIDATES.items():
                    rho_ab, _meta = candidate_fn(carrier_state)
                    metrics = full_metrics(rho_ab)
                    row["carriers"][carrier_name][candidate_name] = {
                        "I_AB": metrics["I_AB"],
                        "I_c": metrics["I_c"],
                    }
                    carrier_candidate_metrics[carrier_name][candidate_name]["I_AB"].append(metrics["I_AB"])
                    carrier_candidate_metrics[carrier_name][candidate_name]["I_c"].append(metrics["I_c"])

            rows.append(row)

    mean_mi_by_carrier_candidate = {
        carrier: {
            candidate: float(np.mean(values["I_AB"]))
            for candidate, values in candidate_map.items()
        }
        for carrier, candidate_map in carrier_candidate_metrics.items()
    }

    mean_ic_by_carrier_candidate = {
        carrier: {
            candidate: float(np.mean(values["I_c"]))
            for candidate, values in candidate_map.items()
        }
        for carrier, candidate_map in carrier_candidate_metrics.items()
    }

    carrier_best = {}
    carrier_honesty_best = {}
    for carrier, candidate_map in mean_mi_by_carrier_candidate.items():
        best_candidate = max(candidate_map, key=candidate_map.get)
        carrier_best[carrier] = {
            "best_candidate": best_candidate,
            "best_mean_mi": candidate_map[best_candidate],
            "ranking": sorted(candidate_map, key=candidate_map.get, reverse=True),
        }
        ic_map = mean_ic_by_carrier_candidate[carrier]
        honesty_scores = {candidate: max(value, 0.0) for candidate, value in ic_map.items()}
        best_honesty_candidate = max(honesty_scores, key=honesty_scores.get)
        carrier_honesty_best[carrier] = {
            "best_candidate": best_honesty_candidate,
            "best_mean_i_c": ic_map[best_honesty_candidate],
            "best_mean_mi": mean_mi_by_carrier_candidate[carrier][best_honesty_candidate],
            "honesty_score": honesty_scores[best_honesty_candidate],
            "ranking": sorted(
                honesty_scores,
                key=lambda candidate: (honesty_scores[candidate], mean_mi_by_carrier_candidate[carrier][candidate]),
                reverse=True,
            ),
        }

    live_best = carrier_best["carrier_live_hopf_weyl"]["best_mean_mi"]
    control_best = max(
        carrier_best["carrier_dechiralized_history"]["best_mean_mi"],
        carrier_best["carrier_cartesian_nohistory"]["best_mean_mi"],
        carrier_best["carrier_dechiralized_nohistory"]["best_mean_mi"],
        carrier_best["carrier_maxmix_history"]["best_mean_mi"],
    )
    live_honesty = carrier_honesty_best["carrier_live_hopf_weyl"]["honesty_score"]
    control_honesty = max(
        carrier_honesty_best["carrier_dechiralized_history"]["honesty_score"],
        carrier_honesty_best["carrier_cartesian_nohistory"]["honesty_score"],
        carrier_honesty_best["carrier_dechiralized_nohistory"]["honesty_score"],
        carrier_honesty_best["carrier_maxmix_history"]["honesty_score"],
    )

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "probe": "sim_root_constraint_carrier_rank",
        "rows": rows,
        "mean_mi_by_carrier_candidate": mean_mi_by_carrier_candidate,
        "mean_ic_by_carrier_candidate": mean_ic_by_carrier_candidate,
        "carrier_best": carrier_best,
        "carrier_honesty_best": carrier_honesty_best,
        "best_root_rank_margin": float(live_best - control_best),
        "best_control_mean_mi": float(control_best),
        "best_honesty_margin": float(live_honesty - control_honesty),
        "best_control_honesty_score": float(control_honesty),
    }


def main() -> int:
    payload = run_probe()
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "root_constraint_carrier_rank_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    print("=" * 72)
    print("ROOT CONSTRAINT CARRIER RANK")
    print("=" * 72)
    for carrier, summary in payload["carrier_best"].items():
        honesty = payload["carrier_honesty_best"][carrier]
        print(
            f"{carrier:<30} best={summary['best_candidate']:<26} "
            f"mean_I_AB={summary['best_mean_mi']:.6f} "
            f"honest={honesty['best_candidate']}({honesty['best_mean_i_c']:.6f})"
        )
    print(f"\nbest_root_rank_margin: {payload['best_root_rank_margin']:.6f}")
    print(f"best_control_mean_mi: {payload['best_control_mean_mi']:.6f}")
    print(f"best_honesty_margin: {payload['best_honesty_margin']:.6f}")
    print(f"best_control_honesty_score: {payload['best_control_honesty_score']:.6f}")
    print(f"results: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
