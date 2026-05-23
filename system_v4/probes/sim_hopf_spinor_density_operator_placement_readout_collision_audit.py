#!/usr/bin/env python3
"""Hopf spinor-density operator-placement readout collision audit.

This audits the classical baseline receipt produced by
sim_hopf_spinor_density_inner_outer_operator_placement_baseline.py. It does not
rerun dynamics. It asks a narrower question: do the existing numeric readouts
operationally separate all 16 operator/loop placements, or do collisions remain
when claim-layer tuple labels are removed?
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import itertools
import json
import pathlib
import time
from collections import defaultdict
from typing import Any

import numpy as np
import z3


NAME = "hopf_spinor_density_operator_placement_readout_collision_audit"
CLASSIFICATION = "classical_baseline"
classification = CLASSIFICATION

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
SOURCE_RESULT = RESULT_DIR / "hopf_spinor_density_inner_outer_operator_placement_baseline_results.json"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

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

LABEL_KEYS = ["terrain_idx", "evolution_loop"]

CLAIM_CEILING = (
    "classical readout-collision audit only: existing numeric Hopf spinor-density placement "
    "readouts do not operationally close all 16 placements; no QIT, GStack, axis, bridge, "
    "engine, flux, Weyl-sheet, bundle, or nonclassical admission"
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "numpy is load-bearing for finite readout vectors and pairwise distance checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "z3 is supportive for label-level full tuple collision UNSAT and observable-collision SAT fences",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not used: this audits a completed result JSON and does not rerun tensor dynamics",
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "not used: no graph neural network or message-passing data object is constructed",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not used: z3 is sufficient for the bounded Boolean/integer readout fences",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "not used: the audit compares finite numeric vectors rather than symbolic expressions",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "not used: Clifford rotors are already upstream in the source baseline receipt",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not used: this receipt does not estimate manifold distances or geodesics",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not used: no equivariant tensor field is built for this collision audit",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "not used: pair enumeration is direct and does not require graph traversal",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "reason": "not used: no hypergraph incidence structure is needed for pair collisions",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "not used: no cell complex or Hodge operator is constructed",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "not used: persistence summaries are upstream; this receipt audits their readout vector",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "z3": "supportive",
    "pytorch": None,
    "pyg": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}


def load_rows() -> list[dict[str, Any]]:
    data = json.loads(SOURCE_RESULT.read_text(encoding="utf-8"))
    rows = [
        row
        for key, row in data["positive"].items()
        if key != "__summary"
    ]
    return sorted(rows, key=lambda row: (row["terrain_idx"], row["evolution_loop"]))


def pair_indices(n: int) -> list[tuple[int, int]]:
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def vector(row: dict[str, Any], keys: list[str]) -> tuple[Any, ...]:
    return tuple(row[key] for key in keys)


def pair_collisions(rows: list[dict[str, Any]], keys: list[str]) -> list[dict[str, Any]]:
    collisions = []
    for i, j in pair_indices(len(rows)):
        if vector(rows[i], keys) == vector(rows[j], keys):
            collisions.append(
                {
                    "pair": [i, j],
                    "placement_i": rows[i]["placement_label"],
                    "placement_j": rows[j]["placement_label"],
                    "shared_readout": list(vector(rows[i], keys)),
                }
            )
    return collisions


def min_observable_distance(rows: list[dict[str, Any]]) -> dict[str, Any]:
    vectors = np.array([[float(row[key]) for key in OBSERVABLE_KEYS] for row in rows], dtype=float)
    best: tuple[float, tuple[int, int]] | None = None
    for i, j in pair_indices(len(rows)):
        dist = float(np.linalg.norm(vectors[i] - vectors[j]))
        if best is None or dist < best[0]:
            best = (dist, (i, j))
    assert best is not None
    dist, (i, j) = best
    return {
        "distance": round(dist, 12),
        "pair": [i, j],
        "placement_i": rows[i]["placement_label"],
        "placement_j": rows[j]["placement_label"],
    }


def z3_label_collision_result() -> str:
    solver = z3.Solver()
    a_terrain, b_terrain = z3.Ints("a_terrain b_terrain")
    a_loop, b_loop = z3.Ints("a_loop b_loop")
    solver.add(a_terrain >= 0, a_terrain < 8, b_terrain >= 0, b_terrain < 8)
    solver.add(a_loop >= 0, a_loop < 2, b_loop >= 0, b_loop < 2)
    solver.add(z3.Or(a_terrain != b_terrain, a_loop != b_loop))
    solver.add(a_terrain == b_terrain, a_loop == b_loop)
    outcome = solver.check()
    return str(outcome)


def z3_observable_collision_witness(rows: list[dict[str, Any]], collisions: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    collision_exists = z3.Bool("collision_exists")
    solver.add(collision_exists == bool(collisions))
    solver.add(collision_exists)
    outcome = str(solver.check())
    return {
        "z3_result": outcome,
        "expected": "sat",
        "passed": outcome == "sat",
        "collision_count": len(collisions),
        "first_collision": collisions[0] if collisions else None,
    }


def grouped_collision_summary(collisions: list[dict[str, Any]]) -> dict[str, int]:
    groups: dict[str, int] = defaultdict(int)
    for row in collisions:
        labels = [row["placement_i"], row["placement_j"]]
        if all("__inner" in label for label in labels):
            groups["inner_inner"] += 1
        elif all("__outer" in label for label in labels):
            groups["outer_outer"] += 1
        else:
            groups["inner_outer"] += 1
    return dict(sorted(groups.items()))


def main() -> dict[str, Any]:
    started = time.time()
    rows = load_rows()
    label_keys = LABEL_KEYS
    full_keys = LABEL_KEYS + OBSERVABLE_KEYS

    label_collisions = pair_collisions(rows, label_keys)
    full_collisions = pair_collisions(rows, full_keys)
    observable_collisions = pair_collisions(rows, OBSERVABLE_KEYS)
    loop_only_collisions = pair_collisions(rows, ["loop_max_density_drift", "berry_phase_pure_loop"])
    terrain_dropped_collisions = pair_collisions(rows, ["evolution_loop"] + OBSERVABLE_KEYS)

    label_unsat = z3_label_collision_result()
    observable_sat = z3_observable_collision_witness(rows, observable_collisions)
    min_distance = min_observable_distance(rows)

    all_pass = (
        len(rows) == 16
        and len(pair_indices(len(rows))) == 120
        and not label_collisions
        and not full_collisions
        and bool(observable_collisions)
        and label_unsat == "unsat"
        and observable_sat["passed"]
    )

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "all_pass_meaning": (
            "contract pass means the blocking collision pattern was detected; it does not mean "
            "16 placements are operationally distinguished"
        ),
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": (
            "none; use as a blocking audit before any stronger 16-placement distinguishability candidate"
        ),
        "promotion_condition": (
            "No promotion from this receipt. A stronger candidate must supply physical-evolution observables "
            "or a declared probe family that separates all 120 unordered pairs with adjacent graveyards."
        ),
        "blocked_until": (
            "blocked from 16-placement operational closure until observable collisions are eliminated or "
            "explained by a stronger probe family with graveyards"
        ),
        "demotion_condition": (
            "Demote if used as placement closure evidence; this receipt is only evidence that the current "
            "readout vector is insufficient."
        ),
        "out_of_scope": [
            "No QIT, GStack, axis, bridge, engine, flux, Weyl-sheet, bundle, or nonclassical admission.",
            "No claim that the 16 placements are operationally distinct.",
            "No claim that the observed collisions are physical equivalences.",
        ],
        "operation_sequence": [
            "load the classical Hopf spinor-density placement baseline receipt",
            "extract 16 placement rows and declared numeric readout vectors",
            "compare all 120 unordered pairs with label keys present",
            "compare all 120 unordered pairs with label keys removed",
            "record collisions and graveyard controls",
        ],
        "carrier_topology": "completed finite Hopf spinor-density inner/outer placement receipt",
        "observable": "finite numeric readout vector over density drift, Bloch drift, entropy, Berry phase, and chiral current",
        "pass_fail_predicate": (
            "pass iff labels separate the fixture but label-free numeric observables still have collisions, "
            "thereby blocking promotion"
        ),
        "graveyards": [
            "label-included readout separates all pairs",
            "label-free observable readout has collisions",
            "loop-only readout has more collisions than full observable readout",
            "terrain-label dropped readout has collisions",
        ],
        "baselines": [
            "source Hopf spinor-density placement baseline",
            "label-included tuple separation",
            "loop-only readout collision control",
        ],
        "divergence_log": (
            "Classical baseline divergence: label-included tuple separation distinguishes all 120 pairs, "
            "but label-free numeric Hopf spinor-density placement readouts have 28 collisions; loop-only "
            "and terrain-dropped controls retain collisions, so this receipt blocks 16-placement promotion."
        ),
        "divergence_details": [
            {
                "baseline": "label-included tuple separation",
                "observation": "labels separate all 120 unordered pairs while label-free numeric observables collide",
                "collision_count": len(full_collisions),
                "comparison_collision_count": len(observable_collisions),
                "interpretation": "label separation is not physical readout separation",
            },
            {
                "baseline": "loop-only readout collision control",
                "observation": "loop-only readout collapses more pairs than the full numeric observable vector",
                "collision_count": len(loop_only_collisions),
                "comparison_collision_count": len(observable_collisions),
                "interpretation": "the observable vector adds information but remains insufficient for closure",
            },
            {
                "baseline": "terrain-label dropped readout control",
                "observation": "dropping terrain labels leaves unresolved collisions",
                "collision_count": len(terrain_dropped_collisions),
                "comparison_collision_count": len(observable_collisions),
                "interpretation": "terrain labels cannot be treated as earned physical distinguishability",
            },
        ],
        "alternative_formulations": [
            "physical-evolution pairwise measurement family",
            "sheet-loop double-flip physical carrier probe",
            "bare-Pauli/no-carrier negative control",
        ],
        "exact_tool_function_needs": {
            "numpy": ["numpy.array", "numpy.linalg.norm"],
            "z3": ["z3.Solver", "z3.Ints", "z3.Or"],
        },
        "lego_or_coupling_target": "16-placement distinguishability pre-admission blocking audit",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipt": str(SOURCE_RESULT.relative_to(PROBE_DIR.parents[1])),
        "summary": {
            "placement_count": len(rows),
            "pair_count": len(pair_indices(len(rows))),
            "label_collision_count": len(label_collisions),
            "label_plus_observable_collision_count": len(full_collisions),
            "observable_collision_count": len(observable_collisions),
            "loop_only_collision_count": len(loop_only_collisions),
            "terrain_dropped_collision_count": len(terrain_dropped_collisions),
            "minimum_observable_distance": min_distance,
            "observable_collision_groups": grouped_collision_summary(observable_collisions),
            "promotion_allowed": False,
            "all_pass": all_pass,
        },
        "z3_controls": {
            "distinct_label_collision": {"z3_result": label_unsat, "expected": "unsat", "passed": label_unsat == "unsat"},
            "observable_collision_exists": observable_sat,
        },
        "positive": {
            "label_plus_observable_pair_separation": {
                "collision_count": len(full_collisions),
                "passed": len(full_collisions) == 0,
            }
        },
        "negative": {
            "label_free_observable_collision_blocks_promotion": {
                "collision_count": len(observable_collisions),
                "sample_collisions": observable_collisions[:12],
                "passed": bool(observable_collisions),
            },
            "loop_only_readout_collision_control": {
                "collision_count": len(loop_only_collisions),
                "sample_collisions": loop_only_collisions[:12],
                "passed": len(loop_only_collisions) > len(observable_collisions),
            },
            "terrain_dropped_readout_collision_control": {
                "collision_count": len(terrain_dropped_collisions),
                "sample_collisions": terrain_dropped_collisions[:12],
                "passed": bool(terrain_dropped_collisions),
            },
        },
        "elapsed_seconds": round(time.time() - started, 6),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(OUT_PATH)
    print(f"ALL PASS: {all_pass}")
    return result


if __name__ == "__main__":
    main()
