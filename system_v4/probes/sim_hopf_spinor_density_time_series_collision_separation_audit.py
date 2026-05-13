#!/usr/bin/env python3
"""Time-series separation audit for Hopf spinor-density placement collisions.

The aggregate readout collision audit found 28 label-free collisions. This
receipt replays the finite trajectory from the Hopf spinor-density placement
baseline and asks whether the colliding aggregate rows separate when compared
as time-series density/Bloch readouts.
"""

from __future__ import annotations

import json
import pathlib
import sys
import time
from typing import Any

import numpy as np


NAME = "hopf_spinor_density_time_series_collision_separation_audit"
CLASSIFICATION = "classical_baseline"
classification = CLASSIFICATION

PROBE_DIR = pathlib.Path(__file__).resolve().parent
ROOT = PROBE_DIR.parents[1]
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
BASELINE_RESULT = RESULT_DIR / "hopf_spinor_density_inner_outer_operator_placement_baseline_results.json"
COLLISION_RESULT = RESULT_DIR / "hopf_spinor_density_operator_placement_readout_collision_audit_results.json"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

sys.path.insert(0, str(PROBE_DIR))
import sim_hopf_spinor_density_inner_outer_operator_placement_baseline as baseline  # noqa: E402


OBSERVABLE_KEYS = [
    "loop_max_density_drift",
    "combined_density_drift",
    "combined_max_density_drift",
    "trace_distance_first_last",
    "bloch_drift",
    "bloch_max_drift",
    "entropy_range",
    "berry_phase_pure_loop",
    "berry_phase_combined",
    "chiral_drift",
    "chiral_mean",
]

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing for finite trajectory vectors and pairwise trajectory distances",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "supportive through the imported Hopf placement baseline module and its spinor-density path utilities",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "supportive through the imported baseline terrain rotor construction",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not used: this audit is finite numeric trajectory replay, not satisfiability checking",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": "supportive",
    "clifford": "supportive",
    "z3": None,
}

CLAIM_CEILING = (
    "classical finite time-series collision audit only: time-resolved Hopf spinor-density readouts "
    "separate some aggregate collisions but leave unresolved pairs; no 16-placement closure, QIT, "
    "GStack, axis, bridge, engine, flux, Weyl-sheet, bundle, or nonclassical admission"
)


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_rows() -> list[dict[str, Any]]:
    payload = json.loads(BASELINE_RESULT.read_text(encoding="utf-8"))
    rows = [row for key, row in payload["positive"].items() if key != "__summary"]
    return sorted(rows, key=lambda row: (row["terrain_idx"], row["evolution_loop"]))


def aggregate_collision_pairs(rows: list[dict[str, Any]]) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            if tuple(rows[i][key] for key in OBSERVABLE_KEYS) == tuple(rows[j][key] for key in OBSERVABLE_KEYS):
                pairs.append((i, j))
    return pairs


def time_series_vector(row: dict[str, Any], rotors: dict[str, Any]) -> np.ndarray:
    terrain = baseline.TERRAINS[row["terrain_idx"]]
    unitary = baseline.terrain_generator_matrix(terrain["name"], rotors)
    accumulated = np.eye(2, dtype=complex)
    values: list[float] = []
    for step in range(baseline.N_STEPS + 1):
        u = 2.0 * np.pi * step / baseline.N_STEPS
        if row["evolution_loop"] == "inner":
            psi_loop = baseline.inner_loop_step(baseline.PHI_0, baseline.CHI_0, baseline.ETA_0, u)
        else:
            psi_loop = baseline.outer_loop_step(baseline.PHI_0, baseline.CHI_0, baseline.ETA_0, u)
        if step > 0:
            accumulated = unitary @ accumulated
        psi = accumulated @ psi_loop
        psi = psi / np.linalg.norm(psi)
        rho = baseline.density_from_spinor(psi)
        bloch = baseline.bloch_from_density(rho)
        values.extend(float(x) for x in bloch)
        values.append(float(baseline.chiral_current(rho)))
    return np.round(np.array(values, dtype=float), 10)


def pair_record(rows: list[dict[str, Any]], i: int, j: int, distance: float) -> dict[str, Any]:
    return {
        "pair": [i, j],
        "placement_i": rows[i]["placement_label"],
        "placement_j": rows[j]["placement_label"],
        "distance": round(distance, 12),
        "same_evolution_loop": rows[i]["evolution_loop"] == rows[j]["evolution_loop"],
        "same_terrain_topo": rows[i]["terrain_topo"] == rows[j]["terrain_topo"],
        "same_terrain_loop": rows[i]["terrain_loop"] == rows[j]["terrain_loop"],
    }


def main() -> dict[str, Any]:
    started = time.time()
    rows = load_rows()
    aggregate_pairs = aggregate_collision_pairs(rows)
    rotors = baseline._build_cl3_terrain_rotors()
    vectors = [time_series_vector(row, rotors) for row in rows]

    separated = []
    unresolved = []
    for i, j in aggregate_pairs:
        distance = float(np.linalg.norm(vectors[i] - vectors[j]))
        record = pair_record(rows, i, j, distance)
        if distance > 1e-8:
            separated.append(record)
        else:
            unresolved.append(record)

    all_pass = (
        len(rows) == 16
        and len(aggregate_pairs) == 28
        and len(separated) == 20
        and len(unresolved) == 8
        and all(row["same_terrain_topo"] and row["same_evolution_loop"] for row in unresolved)
    )

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "all_pass_meaning": (
            "contract pass means the time-series audit found partial separation plus unresolved pairs; "
            "it does not mean 16 placements are operationally distinguished"
        ),
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": "none; use as a blocking diagnostic before stronger placement distinguishability authorship",
        "promotion_condition": (
            "No promotion from this receipt. Closure requires all 120 pairs separated by a declared physical "
            "probe family with adjacent graveyards, or an explicit quotient interpretation with admission gates."
        ),
        "blocked_until": (
            "blocked from 16-placement closure until the 8 unresolved time-series pairs are separated, killed, "
            "or intentionally routed as a lower-dimensional quotient with graveyards"
        ),
        "demotion_condition": "Demote if cited as full placement distinguishability or higher-stage admission evidence.",
        "source_receipts": [rel(BASELINE_RESULT), rel(COLLISION_RESULT)],
        "operation_sequence": [
            "load 16 placement rows from the Hopf spinor-density placement baseline",
            "recompute the 28 aggregate label-free collision pairs",
            "replay the finite terrain-plus-loop trajectory for each placement",
            "flatten Bloch vector and chiral-current time series for every step",
            "compare trajectory distances for the 28 aggregate collision pairs",
        ],
        "carrier_topology": "finite Hopf spinor-density inner/fiber and outer/base-lift trajectory replay",
        "observable": "time series of Bloch x/y/z components and chiral current over 51 trajectory samples",
        "pass_fail_predicate": (
            "pass iff the audit reproduces 28 aggregate collisions, separates exactly 20 by time series, "
            "and leaves exactly 8 unresolved same-topology same-evolution-loop pairs"
        ),
        "graveyards": [
            "aggregate readout collision set remains the source pool",
            "time-series readout separates some aggregate collisions",
            "unresolved pairs remain and block promotion",
            "same-topology same-loop unresolved pattern is recorded rather than promoted",
        ],
        "baselines": [
            "Hopf spinor-density inner/outer operator placement baseline",
            "aggregate readout collision audit",
            "label-free aggregate readout vector",
        ],
        "divergence_log": (
            "Classical baseline divergence: time-resolved trajectory readouts separate 20 of the 28 aggregate "
            "collisions but leave 8 unresolved same-topology same-loop pairs, so aggregate collisions are partly "
            "readout-thin but not fully closed."
        ),
        "alternative_formulations": [
            "density-matrix time series instead of Bloch/chiral time series",
            "fiber phase sweep on unresolved pairs",
            "base-lift perturbation sweep on unresolved pairs",
            "quotient classification over unresolved terrain-loop pairs",
        ],
        "exact_tool_function_needs": {
            "numpy": ["numpy.eye", "numpy.linalg.norm", "numpy.array"],
            "baseline_module": [
                "terrain_generator_matrix",
                "inner_loop_step",
                "outer_loop_step",
                "density_from_spinor",
                "bloch_from_density",
            ],
        },
        "lego_or_coupling_target": "16-placement distinguishability diagnostic before placement-lego admission",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "placement_count": len(rows),
            "aggregate_collision_count": len(aggregate_pairs),
            "time_series_separated_count": len(separated),
            "time_series_unresolved_count": len(unresolved),
            "promotion_allowed": False,
            "all_pass": all_pass,
        },
        "positive": {
            "aggregate_collision_pairs_partly_separate_under_time_series": {
                "separated_count": len(separated),
                "sample": separated[:12],
                "passed": len(separated) == 20,
            }
        },
        "negative": {
            "unresolved_time_series_pairs_block_promotion": {
                "unresolved_count": len(unresolved),
                "pairs": unresolved,
                "passed": len(unresolved) == 8,
            }
        },
        "boundary": {
            "unresolved_pattern": {
                "same_terrain_topo_and_same_evolution_loop": all(
                    row["same_terrain_topo"] and row["same_evolution_loop"] for row in unresolved
                ),
                "passed": bool(unresolved),
            }
        },
        "out_of_scope": [
            "No 16-placement operational closure.",
            "No claim that unresolved pairs are physically identical.",
            "No QIT, GStack, axis, bridge, engine, flux, bundle, Weyl-sheet, or nonclassical admission.",
        ],
        "elapsed_seconds": round(time.time() - started, 6),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(OUT_PATH)
    print(f"ALL PASS: {all_pass}")
    return result


if __name__ == "__main__":
    main()
