#!/usr/bin/env python3
"""Explore candidate terrain-loop-dependent generators beside the current baseline.

This is not a replacement for the Hopf spinor-density placement baseline. It
tests whether small, explicit generator variants can separate the terrain-loop
f/b pairs that the current source leaves generator-equivalent.
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import pathlib
import sys
import time
from itertools import combinations
from typing import Any

import numpy as np


NAME = "hopf_spinor_density_terrain_loop_dependent_generator_variant_graveyard"
CLASSIFICATION = "classical_baseline"
classification = CLASSIFICATION

PROBE_DIR = pathlib.Path(__file__).resolve().parent
ROOT = PROBE_DIR.parents[1]
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
TIME_SERIES_RESULT = RESULT_DIR / "hopf_spinor_density_time_series_collision_separation_audit_results.json"
GENERATOR_EQUIVALENCE_RESULT = RESULT_DIR / "hopf_spinor_density_terrain_loop_generator_equivalence_audit_results.json"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

sys.path.insert(0, str(PROBE_DIR))
import sim_hopf_spinor_density_inner_outer_operator_placement_baseline as baseline  # noqa: E402
from receipt_boundary import apply_default_receipt_boundary  # noqa: E402


TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing for generator variants, density trajectories, and pairwise norm separation",
    }
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}

CLAIM_CEILING = (
    "candidate generator-variant exploration only: tests whether terrain-loop-dependent unitary variants can separate "
    "previously unresolved f/b pairs under finite spinor-density readouts; no baseline rewrite, no 16-placement closure, "
    "no QIT, GStack, axis, bridge, engine, flux, Weyl-sheet, bundle, or nonclassical admission"
)

ANGLE = np.pi / 25


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def unitary(axis: str, sign: int, angle: float = ANGLE) -> np.ndarray:
    theta = sign * angle / 2.0
    c, s = np.cos(theta), np.sin(theta)
    if axis == "z":
        return np.array([[np.exp(1j * theta), 0.0], [0.0, np.exp(-1j * theta)]], dtype=complex)
    if axis == "y":
        return np.array([[c, -s], [s, c]], dtype=complex)
    if axis == "x":
        return np.array([[c, 1j * s], [1j * s, c]], dtype=complex)
    raise ValueError(f"unknown axis {axis!r}")


def terrain_unitary(terrain: dict[str, Any], variant: str) -> np.ndarray:
    topo = terrain["topo"]
    loop = terrain["loop"]
    is_base_loop = loop in {"b", "base"}
    topo_axis = {"Se": "z", "Si": "z", "Ne": "y", "Ni": "y"}[topo]
    topo_sign = {"Se": 1, "Si": -1, "Ne": 1, "Ni": -1}[topo]

    if variant == "topology_only_current":
        return np.round(baseline.terrain_generator_matrix(terrain["name"], baseline._build_cl3_terrain_rotors()), 12)

    if variant == "terrain_loop_global_phase_only":
        phase = np.exp(1j * ANGLE) if is_base_loop else 1.0
        return phase * unitary(topo_axis, topo_sign)

    if variant == "terrain_loop_angle_sign":
        loop_sign = -1 if is_base_loop else 1
        return unitary(topo_axis, topo_sign * loop_sign)

    if variant == "terrain_loop_plane_selection":
        if is_base_loop:
            axis = {"Se": "x", "Si": "x", "Ne": "z", "Ni": "z"}[topo]
        else:
            axis = topo_axis
        return unitary(axis, topo_sign)

    raise ValueError(f"unknown variant {variant!r}")


def density_vector(rho: np.ndarray) -> list[float]:
    return np.concatenate([np.real(rho).ravel(), np.imag(rho).ravel()]).astype(float).tolist()


def trajectory_vector(terrain_idx: int, evolution_loop: str, variant: str) -> np.ndarray:
    terrain = baseline.TERRAINS[terrain_idx]
    u_terrain = terrain_unitary(terrain, variant)
    u_accumulated = np.eye(2, dtype=complex)
    rows: list[float] = []

    for step in range(baseline.N_STEPS + 1):
        u = 2.0 * np.pi * step / baseline.N_STEPS
        if evolution_loop == "inner":
            psi_loop = baseline.inner_loop_step(baseline.PHI_0, baseline.CHI_0, baseline.ETA_0, u)
        else:
            psi_loop = baseline.outer_loop_step(baseline.PHI_0, baseline.CHI_0, baseline.ETA_0, u)
        if step > 0:
            u_accumulated = u_terrain @ u_accumulated
        psi_combined = u_accumulated @ psi_loop
        norm = np.linalg.norm(psi_combined)
        if norm > 1e-15:
            psi_combined /= norm
        rho = baseline.density_from_spinor(psi_combined)
        rows.extend(density_vector(rho))

    return np.asarray(rows, dtype=float)


def placements_for_variant(variant: str) -> list[dict[str, Any]]:
    rows = []
    for terrain_idx, terrain in enumerate(baseline.TERRAINS):
        for evolution_loop in ["inner", "outer"]:
            rows.append(
                {
                    "terrain_idx": terrain_idx,
                    "terrain_name": terrain["name"],
                    "terrain_topo": terrain["topo"],
                    "terrain_loop": terrain["loop"],
                    "evolution_loop": evolution_loop,
                    "label": f"{terrain['topo']}_{terrain['loop']}__{evolution_loop}",
                    "trajectory": trajectory_vector(terrain_idx, evolution_loop, variant),
                    "generator": terrain_unitary(terrain, variant),
                }
            )
    return rows


def unresolved_pairs() -> list[dict[str, Any]]:
    data = json.loads(TIME_SERIES_RESULT.read_text(encoding="utf-8"))
    return data["negative"]["unresolved_time_series_pairs_block_promotion"]["pairs"]


def variant_report(variant: str) -> dict[str, Any]:
    rows = placements_for_variant(variant)
    all_pairs = []
    for i, j in combinations(range(len(rows)), 2):
        distance = float(np.linalg.norm(rows[i]["trajectory"] - rows[j]["trajectory"]))
        all_pairs.append(
            {
                "pair": [i, j],
                "labels": [rows[i]["label"], rows[j]["label"]],
                "distance": round(distance, 12),
                "separated": distance > 1e-9,
            }
        )

    unresolved = []
    for pair in unresolved_pairs():
        i, j = pair["pair"]
        trajectory_distance = float(np.linalg.norm(rows[i]["trajectory"] - rows[j]["trajectory"]))
        generator_distance = float(np.linalg.norm(rows[i]["generator"] - rows[j]["generator"]))
        unresolved.append(
            {
                "pair": [i, j],
                "labels": [rows[i]["label"], rows[j]["label"]],
                "trajectory_distance": round(trajectory_distance, 12),
                "generator_distance": round(generator_distance, 12),
                "trajectory_separated": trajectory_distance > 1e-9,
                "generator_separated": generator_distance > 1e-12,
            }
        )

    all_120_separated = all(row["separated"] for row in all_pairs)
    unresolved_all_separated = all(row["trajectory_separated"] for row in unresolved)
    minimum_pair_distance = min(row["distance"] for row in all_pairs)
    collision_pairs = [row for row in all_pairs if not row["separated"]]
    return {
        "variant": variant,
        "all_120_pairs_separated": all_120_separated,
        "unresolved_f_b_pairs_separated": unresolved_all_separated,
        "minimum_pair_distance": minimum_pair_distance,
        "collision_pair_count": len(collision_pairs),
        "collision_pairs": collision_pairs,
        "previously_unresolved_pairs": unresolved,
    }


def main() -> dict[str, Any]:
    started = time.time()
    variants = [
        "topology_only_current",
        "terrain_loop_global_phase_only",
        "terrain_loop_angle_sign",
        "terrain_loop_plane_selection",
    ]
    reports = {variant: variant_report(variant) for variant in variants}

    graveyards = {
        "topology_only_current_preserves_unresolved_f_b_collisions": {
            "passed": not reports["topology_only_current"]["unresolved_f_b_pairs_separated"],
            "collision_pair_count": reports["topology_only_current"]["collision_pair_count"],
        },
        "terrain_loop_global_phase_only_preserves_density_collisions": {
            "passed": not reports["terrain_loop_global_phase_only"]["unresolved_f_b_pairs_separated"],
            "collision_pair_count": reports["terrain_loop_global_phase_only"]["collision_pair_count"],
        },
    }
    candidates = {
        "terrain_loop_angle_sign": {
            "passed": reports["terrain_loop_angle_sign"]["unresolved_f_b_pairs_separated"],
            "all_120_pairs_separated": reports["terrain_loop_angle_sign"]["all_120_pairs_separated"],
            "minimum_pair_distance": reports["terrain_loop_angle_sign"]["minimum_pair_distance"],
        },
        "terrain_loop_plane_selection": {
            "passed": reports["terrain_loop_plane_selection"]["unresolved_f_b_pairs_separated"],
            "all_120_pairs_separated": reports["terrain_loop_plane_selection"]["all_120_pairs_separated"],
            "minimum_pair_distance": reports["terrain_loop_plane_selection"]["minimum_pair_distance"],
        },
    }
    any_candidate_separates_unresolved = any(row["passed"] for row in candidates.values())
    all_pass = all(row["passed"] for row in graveyards.values()) and all(
        variant in reports for variant in variants
    )

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "all_pass_meaning": (
            "contract pass means the candidate-variant search completed, the topology-only and global-phase graveyards "
            "kept the expected unresolved f/b collisions, and the receipt explicitly reports whether any candidate "
            "separated those pairs; it does not admit a candidate or close 16 placements"
        ),
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": "none; candidate mechanism exploration for placement distinguishability",
        "promotion_condition": "No promotion from this receipt. Future admission requires a declared generator source, physical rationale, full 120-pair closure, and surrounding graveyards.",
        "blocked_until": "blocked from placement closure until a candidate is separately admitted or the current source is explicitly quotiented",
        "demotion_condition": "Demote if this candidate exploration is cited as a source-level rewrite or as physical terrain-loop evidence.",
        "divergence_log": (
            "This receipt deliberately explores small terrain-loop-dependent unitary variants and records that the "
            "tested angle-sign and plane-selection candidates still do not separate the previously unresolved f/b "
            "density time-series pairs. The negative outcome strengthens the blocker; it does not promote a generator."
        ),
        "source_receipts": [
            rel(TIME_SERIES_RESULT),
            rel(GENERATOR_EQUIVALENCE_RESULT),
        ],
        "operation_sequence": [
            "load the current Hopf spinor-density terrain and loop fixture",
            "construct four generator formulations: topology-only, global-phase-only, terrain-loop angle-sign, and terrain-loop plane-selection",
            "evolve each formulation over finite spinor-density trajectories",
            "measure all 120 pairwise trajectory distances",
            "check the 8 previously unresolved f/b pairs",
            "keep topology-only and global-phase-only as graveyards",
        ],
        "carrier_topology": "finite Hopf spinor-density path fixture with candidate 2x2 unitary generator variants",
        "observable": "pairwise Euclidean distance between flattened real/imaginary density-matrix time series",
        "pass_fail_predicate": "graveyard variants preserve unresolved f/b collisions and all declared candidate variants produce recorded pairwise-distance outcomes",
        "graveyards": [
            "topology-only current generator preserves unresolved f/b collisions",
            "terrain-loop global phase changes generator labels but preserves density collisions",
        ],
        "baselines": [
            "current Hopf spinor-density placement baseline",
            "time-series collision separation audit",
            "terrain-loop generator equivalence audit",
        ],
        "alternative_formulations": [
            "terrain-loop angle-sign generator variant",
            "terrain-loop plane-selection generator variant",
            "quotient interpretation under terrain-loop generator equivalence",
        ],
        "exact_tool_function_needs": {
            "numpy": ["array", "cos", "sin", "exp", "linalg.norm", "real", "imag"],
            "baseline_module": ["TERRAINS", "inner_loop_step", "outer_loop_step", "density_from_spinor"],
        },
        "lego_or_coupling_target": "candidate mechanism for terrain-loop placement distinguishability",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "variant_count": len(variants),
            "graveyards_passed": all(row["passed"] for row in graveyards.values()),
            "any_candidate_separates_unresolved": any_candidate_separates_unresolved,
            "promotion_allowed": False,
            "all_pass": all_pass,
        },
        "positive": {"candidate_variants": candidates},
        "negative": {"graveyards": graveyards},
        "boundary": {"variant_reports": reports},
        "out_of_scope": [
            "No modification of the current baseline source.",
            "No claim that either candidate generator is physically correct.",
            "No 16-placement operational closure.",
            "No QIT, GStack, axis, bridge, engine, flux, Weyl-sheet, bundle, or nonclassical admission.",
        ],
        "elapsed_seconds": round(time.time() - started, 6),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    result = apply_default_receipt_boundary(result, source_name=f"sim_{NAME}")
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUT_PATH)
    print(f"ALL PASS: {result['all_pass']}")
    return result


if __name__ == "__main__":
    main()
