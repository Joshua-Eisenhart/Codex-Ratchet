#!/usr/bin/env python3
"""Pairwise separation of 16 abstract component tuples under declared readouts.

This is a pure finite tuple/readout probe. It does not simulate engine dynamics,
Hopf geometry, Weyl spinors, flux, bundles, or QIT structure. The only claim is
local: for 16 tuples in a 4 x 2 x 2 product, the full component readout separates
all 120 unordered pairs, while coordinate-dropped readouts have collisions.
"""

from __future__ import annotations

import json
import os
import time

import z3


classification = "canonical"

CLAIM_CEILING = (
    "local z3 finite-tuple readout separation only: 16 abstract 4x2x2 tuples are "
    "pairwise separated by the declared full component readout; no engine, QIT, "
    "GStack, bridge, axis, Weyl-sheet, flux, bundle, or nonclassical admission"
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not used: this is a finite SMT tuple/readout proof with no tensor, gradient, or simulation state",
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "not used: no graph neural network, message-passing graph, or PyG data object is constructed",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "z3 is load-bearing: Solver.check proves full-readout pair collisions UNSAT and coordinate-dropped graveyard collisions SAT",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not used: no alternate SMT backend is needed for this bounded z3-only tuple separation receipt",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "not used: the proof uses finite integer tuples and SMT equality, not symbolic algebra expressions",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "not used: no geometric algebra layout, blade, rotor, grade, or Clifford product appears in this receipt",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not used: there is no manifold, metric, geodesic, tangent vector, or Frechet mean operation",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not used: there is no equivariant tensor, irreducible representation, Wigner-D matrix, or spherical harmonic",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "not used: pair separation is not a graph traversal, DAG, path, or transitive-reduction problem",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "reason": "not used: the tuple product is not represented as a hypergraph or higher-order incidence structure",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "not used: no simplicial complex, cell complex, incidence matrix, or Hodge Laplacian is built",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "not used: no filtration, simplex tree, persistence interval, or Betti summary is computed",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "clifford": None,
    "cvc5": None,
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "pyg": None,
    "pytorch": None,
    "rustworkx": None,
    "sympy": None,
    "toponetx": None,
    "xgi": None,
    "z3": "load_bearing",
}


def all_tuples() -> list[dict[str, int]]:
    tuples = []
    for operator_id in range(4):
        for path_id in range(2):
            for sheet_id in range(2):
                tuples.append({
                    "operator_id": operator_id,
                    "path_id": path_id,
                    "sheet_id": sheet_id,
                })
    return tuples


def pair_indices(n: int) -> list[tuple[int, int]]:
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def readout_equal(a: dict[str, int], b: dict[str, int], keys: list[str]) -> z3.BoolRef:
    return z3.And(*[z3.IntVal(a[k]) == z3.IntVal(b[k]) for k in keys])


def is_distinct_tuple(a: dict[str, int], b: dict[str, int]) -> z3.BoolRef:
    return z3.Or(
        z3.IntVal(a["operator_id"]) != z3.IntVal(b["operator_id"]),
        z3.IntVal(a["path_id"]) != z3.IntVal(b["path_id"]),
        z3.IntVal(a["sheet_id"]) != z3.IntVal(b["sheet_id"]),
    )


def check_formula(formula: z3.BoolRef) -> str:
    solver = z3.Solver()
    solver.add(formula)
    outcome = solver.check()
    if outcome == z3.sat:
        return "sat"
    if outcome == z3.unsat:
        return "unsat"
    return "unknown"


def full_readout_pair_sweep(tuples: list[dict[str, int]]) -> dict:
    keys = ["operator_id", "path_id", "sheet_id"]
    rows = []
    for i, j in pair_indices(len(tuples)):
        formula = z3.And(is_distinct_tuple(tuples[i], tuples[j]), readout_equal(tuples[i], tuples[j], keys))
        outcome = check_formula(formula)
        rows.append({"pair": [i, j], "z3_result": outcome, "passed": outcome == "unsat"})
    return {
        "pair_count": len(rows),
        "unsat_pair_count": sum(1 for row in rows if row["z3_result"] == "unsat"),
        "all_pairs_separated": all(row["passed"] for row in rows),
        "rows": rows,
    }


def dropped_coordinate_graveyard(tuples: list[dict[str, int]], dropped_key: str) -> dict:
    keys = [key for key in ["operator_id", "path_id", "sheet_id"] if key != dropped_key]
    collisions = []
    for i, j in pair_indices(len(tuples)):
        formula = z3.And(is_distinct_tuple(tuples[i], tuples[j]), readout_equal(tuples[i], tuples[j], keys))
        outcome = check_formula(formula)
        if outcome == "sat":
            collisions.append({"pair": [i, j], "tuple_i": tuples[i], "tuple_j": tuples[j]})
    return {
        "dropped_key": dropped_key,
        "remaining_readout": keys,
        "collision_count": len(collisions),
        "has_collision": bool(collisions),
        "sample_collisions": collisions[:8],
        "passed": bool(collisions),
    }


def main() -> dict:
    started = time.time()
    tuples = all_tuples()
    full = full_readout_pair_sweep(tuples)
    graveyards = {
        key: dropped_coordinate_graveyard(tuples, key)
        for key in ["operator_id", "path_id", "sheet_id"]
    }
    boundary = {
        "tuple_count_is_16": {"observed": len(tuples), "expected": 16, "passed": len(tuples) == 16},
        "unordered_pair_count_is_120": {"observed": len(pair_indices(len(tuples))), "expected": 120, "passed": len(pair_indices(len(tuples))) == 120},
        "same_tuple_full_readout_collision_is_sat": {
            "z3_result": check_formula(readout_equal(tuples[0], tuples[0], ["operator_id", "path_id", "sheet_id"])),
            "expected": "sat",
        },
    }
    boundary["same_tuple_full_readout_collision_is_sat"]["passed"] = (
        boundary["same_tuple_full_readout_collision_is_sat"]["z3_result"] == "sat"
    )
    all_pass = (
        full["all_pairs_separated"]
        and all(row["passed"] for row in graveyards.values())
        and all(row["passed"] for row in boundary.values())
    )

    result = {
        "name": "sim_z3_tuple_component_readout_pair_separation",
        "classification": classification,
        "all_pass": all_pass,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": (
            "none; use as bounded tuple-readout separation evidence before any separate placement "
            "distinguishability or sheet-loop candidate authorship"
        ),
        "promotion_condition": (
            "No promotion from this receipt; downstream candidates must supply exact carrier/topology, "
            "observable, and graveyard receipts beyond abstract tuple labels."
        ),
        "demotion_condition": (
            "Demote or block if any full-readout pair collision is SAT, if coordinate-dropped graveyards "
            "stop colliding, or if the result is used as evidence for dynamics or geometry."
        ),
        "blocked_until": (
            "blocked from engine, QIT, GStack, bridge, axis, Weyl-sheet, flux, bundle, or nonclassical claims "
            "until separate exact receipts close those gates"
        ),
        "out_of_scope": [
            "No dynamics, density evolution, Hopf geometry, Weyl spinor, flux, bundle, or engine claim.",
            "No proof that physical placements are operationally distinct under any real measurement family.",
            "No promotion of the 16-count beyond this declared tuple/readout fixture.",
        ],
        "operation_sequence": [
            "enumerate 16 tuples in a 4x2x2 product",
            "prove every unordered pair is separated by full component readout",
            "drop one coordinate at a time and prove adjacent collisions exist",
        ],
        "carrier_topology": "finite product set {0..3} x {0,1} x {0,1}",
        "observable": "z3 SAT/UNSAT verdicts for readout equality under distinct tuple constraints",
        "pass_fail_predicate": "120 full-readout pair collisions are UNSAT and all coordinate-dropped graveyards have SAT collisions",
        "graveyards": [
            "drop operator_id from the readout",
            "drop path_id from the readout",
            "drop sheet_id from the readout",
        ],
        "baselines": [
            "abstract tuple-label readout only",
            "coordinate-dropped readout controls",
        ],
        "alternative_formulations": [
            "density-matrix observable distinguishability sweep",
            "sheet-loop double-flip probe",
            "bare-Pauli/no-bundle baseline",
        ],
        "exact_tool_function_needs": {
            "z3": ["Solver", "And", "Or", "IntVal"],
        },
        "lego_or_coupling_target": "none; pre-lego tuple-readout boundary evidence",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tuple_count": len(tuples),
        "pair_count": 120,
        "tuples": tuples,
        "positive": {"full_readout_pair_sweep": full},
        "negative": {"coordinate_dropped_collision_graveyards": graveyards},
        "boundary": boundary,
        "graveyard": graveyards,
        "elapsed_seconds": round(time.time() - started, 6),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_z3_tuple_component_readout_pair_separation_results.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Results written to {out_path}")
    print(f"all_pass={all_pass} pair_count=120")
    return result


if __name__ == "__main__":
    main()
