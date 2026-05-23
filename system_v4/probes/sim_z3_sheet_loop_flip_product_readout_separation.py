#!/usr/bin/env python3
"""Finite product readout for two independent Z2 flips.

This probe is intentionally small. It models two abstract binary coordinates,
``sheet`` and ``loop``, and four transformations on their product:
identity, sheet flip, loop flip, and the composed double flip. It proves only
that the full two-coordinate readout separates those four transformations and
that coordinate-dropped readouts collapse the expected neighbors.

It does not model Weyl spinors, Hopf fibers, flux, bundles, engines, QIT, or
nonclassical structure.
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import os
import time

import z3
from receipt_boundary import apply_default_receipt_boundary


CLASSIFICATION = "classical_baseline"
NAME = "z3_sheet_loop_flip_product_readout_separation"

CLAIM_CEILING = (
    "local z3 finite-product readout separation only: two abstract Z2 coordinates separate four declared "
    "flip transformations under the full readout; no physical sheet/loop independence, Weyl spinor, Hopf "
    "fibration, flux, bundle, engine, QIT, GStack, bridge, axis, or nonclassical admission"
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not used: no tensors, gradients, simulation state, or differentiable objective occur in this finite SMT receipt"},
    "pyg": {"tried": False, "used": False, "reason": "not used: no graph neural network, message passing, edge_index, or PyG data object is constructed"},
    "z3": {"tried": True, "used": True, "reason": "z3 is load-bearing: Solver.check proves full-readout collisions UNSAT and coordinate-projection graveyard collisions SAT"},
    "cvc5": {"tried": False, "used": False, "reason": "not used: this bounded receipt uses one SMT backend and has no second-backend agreement claim"},
    "sympy": {"tried": False, "used": False, "reason": "not used: the construction is finite Boolean algebra, not symbolic matrix or polynomial algebra"},
    "clifford": {"tried": False, "used": False, "reason": "not used: no geometric algebra layout, blade, rotor, chirality operator, or Clifford product is represented"},
    "geomstats": {"tried": False, "used": False, "reason": "not used: there is no manifold, metric, geodesic, tangent vector, or Riemannian operation"},
    "e3nn": {"tried": False, "used": False, "reason": "not used: there is no equivariant tensor, irreducible representation, Wigner-D matrix, or spherical harmonic"},
    "rustworkx": {"tried": False, "used": False, "reason": "not used: the finite product proof is not a graph traversal, DAG, path, or transitive-reduction problem"},
    "xgi": {"tried": False, "used": False, "reason": "not used: the two-coordinate product is not encoded as a hypergraph or higher-order incidence structure"},
    "toponetx": {"tried": False, "used": False, "reason": "not used: no simplicial complex, cell complex, incidence matrix, or Hodge Laplacian is built"},
    "gudhi": {"tried": False, "used": False, "reason": "not used: no filtration, persistence interval, simplex tree, or Betti summary is computed"},
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


TRANSFORMS = {
    "identity": (0, 0),
    "sheet_flip": (1, 0),
    "loop_flip": (0, 1),
    "sheet_loop_double_flip": (1, 1),
}


def xor_bit(a: z3.ArithRef, bit: int) -> z3.ArithRef:
    return z3.If(a == bit, z3.IntVal(0), z3.IntVal(1))


def apply_transform(sheet: z3.ArithRef, loop: z3.ArithRef, transform: tuple[int, int]) -> tuple[z3.ArithRef, z3.ArithRef]:
    sheet_bit, loop_bit = transform
    return xor_bit(sheet, sheet_bit), xor_bit(loop, loop_bit)


def check(formula: z3.BoolRef) -> str:
    solver = z3.Solver()
    solver.add(formula)
    outcome = solver.check()
    if outcome == z3.sat:
        return "sat"
    if outcome == z3.unsat:
        return "unsat"
    return "unknown"


def base_constraints(sheet: z3.ArithRef, loop: z3.ArithRef) -> z3.BoolRef:
    return z3.And(z3.Or(sheet == 0, sheet == 1), z3.Or(loop == 0, loop == 1))


def pairwise_full_readout() -> dict:
    sheet, loop = z3.Ints("sheet loop")
    rows = []
    names = list(TRANSFORMS)
    for i, left_name in enumerate(names):
        for right_name in names[i + 1:]:
            left = apply_transform(sheet, loop, TRANSFORMS[left_name])
            right = apply_transform(sheet, loop, TRANSFORMS[right_name])
            collision = z3.And(base_constraints(sheet, loop), left[0] == right[0], left[1] == right[1])
            outcome = check(collision)
            rows.append({
                "pair": [left_name, right_name],
                "z3_result": outcome,
                "expected": "unsat",
                "passed": outcome == "unsat",
            })
    return {
        "pair_count": len(rows),
        "all_full_readout_pairs_separated": all(row["passed"] for row in rows),
        "rows": rows,
    }


def coordinate_projection_graveyards() -> dict:
    sheet, loop = z3.Ints("sheet_g loop_g")
    checks = {}
    cases = {
        "drop_loop_collapses_identity_vs_loop_flip": ("identity", "loop_flip", ["sheet"]),
        "drop_loop_collapses_sheet_flip_vs_double_flip": ("sheet_flip", "sheet_loop_double_flip", ["sheet"]),
        "drop_sheet_collapses_identity_vs_sheet_flip": ("identity", "sheet_flip", ["loop"]),
        "drop_sheet_collapses_loop_flip_vs_double_flip": ("loop_flip", "sheet_loop_double_flip", ["loop"]),
    }
    for name, (left_name, right_name, keys) in cases.items():
        left = apply_transform(sheet, loop, TRANSFORMS[left_name])
        right = apply_transform(sheet, loop, TRANSFORMS[right_name])
        atoms = [base_constraints(sheet, loop)]
        if "sheet" in keys:
            atoms.append(left[0] == right[0])
        if "loop" in keys:
            atoms.append(left[1] == right[1])
        outcome = check(z3.And(*atoms))
        checks[name] = {
            "pair": [left_name, right_name],
            "retained_readout": keys,
            "z3_result": outcome,
            "expected": "sat",
            "passed": outcome == "sat",
        }
    return checks


def commutation_boundary() -> dict:
    sheet, loop = z3.Ints("sheet_c loop_c")
    sheet_then_loop = apply_transform(*apply_transform(sheet, loop, TRANSFORMS["sheet_flip"]), TRANSFORMS["loop_flip"])
    loop_then_sheet = apply_transform(*apply_transform(sheet, loop, TRANSFORMS["loop_flip"]), TRANSFORMS["sheet_flip"])
    double_direct = apply_transform(sheet, loop, TRANSFORMS["sheet_loop_double_flip"])
    commute_failure = z3.And(
        base_constraints(sheet, loop),
        z3.Or(sheet_then_loop[0] != loop_then_sheet[0], sheet_then_loop[1] != loop_then_sheet[1]),
    )
    double_mismatch = z3.And(
        base_constraints(sheet, loop),
        z3.Or(sheet_then_loop[0] != double_direct[0], sheet_then_loop[1] != double_direct[1]),
    )
    identity_collision = z3.And(
        base_constraints(sheet, loop),
        sheet_then_loop[0] == sheet,
        sheet_then_loop[1] == loop,
    )
    return {
        "sheet_loop_flips_commute": {
            "z3_result": check(commute_failure),
            "expected": "unsat",
            "passed": check(commute_failure) == "unsat",
        },
        "sequential_flips_equal_double_flip": {
            "z3_result": check(double_mismatch),
            "expected": "unsat",
            "passed": check(double_mismatch) == "unsat",
        },
        "double_flip_not_identity_under_full_readout": {
            "z3_result": check(identity_collision),
            "expected": "unsat",
            "passed": check(identity_collision) == "unsat",
        },
    }


def main() -> dict:
    started = time.time()
    positive = {"full_readout_pairwise_separation": pairwise_full_readout()}
    negative = {"coordinate_projection_graveyards": coordinate_projection_graveyards()}
    boundary = commutation_boundary()
    all_pass = (
        positive["full_readout_pairwise_separation"]["all_full_readout_pairs_separated"]
        and all(row["passed"] for row in negative["coordinate_projection_graveyards"].values())
        and all(row["passed"] for row in boundary.values())
    )
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": "sheet_loop_product_readout_separation_baseline",
        "promotion_condition": "No promotion from this receipt; downstream candidates need exact carrier/topology, observable, and graveyard receipts.",
        "demotion_condition": "Demote or block if full readout no longer separates the four transformations, if projection graveyards stop colliding, or if used as physical geometry evidence.",
        "blocked_until": "blocked from Weyl, Hopf, flux, bundle, engine, QIT, GStack, bridge, axis, or nonclassical claims until separate exact receipts close those gates",
        "out_of_scope": [
            "No Weyl spinor, Hopf fibration, flux, bundle, engine, QIT, GStack, bridge, axis, or nonclassical claim.",
            "No assertion that physical sheet/loop operations exist or are represented.",
            "No placement-lego admission beyond this finite readout fixture.",
        ],
        "divergence_log": (
            "This is a finite Boolean-product SMT baseline. It separates declared labels in Z2 x Z2, but it does "
            "not simulate Hopf/Weyl geometry, physical inner/outer loops, flux, bundle structure, or any target "
            "geometric-constraint manifold."
        ),
        "operation_sequence": [
            "define two abstract Z2 coordinates",
            "define identity, sheet flip, loop flip, and double flip transformations",
            "prove full readout separates all transform pairs",
            "drop one coordinate at a time and record expected collisions",
        ],
        "carrier_topology": "finite product set Z2 x Z2 only",
        "observable": "z3 SAT/UNSAT verdicts for transform-output equality under retained readout coordinates",
        "pass_fail_predicate": "full-readout collisions are UNSAT, coordinate-projection graveyards are SAT, and flip composition checks pass",
        "graveyards": [
            "drop loop coordinate",
            "drop sheet coordinate",
            "test double flip against identity under full readout",
        ],
        "baselines": [
            "abstract Z2 x Z2 product fixture",
            "coordinate-projection collision controls",
        ],
        "alternative_formulations": [
            "density-matrix sheet-loop probe",
            "Clifford chirality and loop carrier probe",
            "Hopf-fiber/base-lift observable probe",
        ],
        "exact_tool_function_needs": {"z3": ["Solver", "And", "Or", "If", "IntVal"]},
        "lego_or_coupling_target": "sheet_loop_product_readout_separation_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "transforms": TRANSFORMS,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "elapsed_seconds": round(time.time() - started, 6),
        "promotion_allowed": False,
    }
    result = apply_default_receipt_boundary(result, source_name=f"sim_{NAME}")
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Results written to {out_path}")
    print(f"all_pass={all_pass}")
    return result


if __name__ == "__main__":
    main()
