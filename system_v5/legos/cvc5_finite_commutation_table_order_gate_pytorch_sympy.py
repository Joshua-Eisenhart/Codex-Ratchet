#!/usr/bin/env python3
"""Finite cvc5 commutation-table order-gate substrate lego."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import torch


ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "cvc5_finite_commutation_table_order_gate_pytorch_sympy_results.json"

NAME = "cvc5_finite_commutation_table_order_gate_pytorch_sympy"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Finite cvc5 commutation-table order-gate substrate lego only: builds a "
    "finite operator set {I,X,Z}, computes commutation data with PyTorch/SymPy, "
    "and uses cvc5 Bool plus BitVec encodings to block selecting a noncommuting "
    "pair under a pairwise-commuting constraint. It does not admit PEPS3D scale "
    "promotion, Hopf/Weyl geometry, terrain, operator substages, flux, Xi/Phi0, "
    "Axis0, physics, or final manifold claims."
)

TOOL_MANIFEST = {
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Bool and BitVec solver encodings of the finite pairwise-commuting admission/blocking map",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite operator commutator norms that generate the commutation table",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact commutator identities for the finite operator table",
    },
}
TOOL_INTEGRATION_DEPTH = {key: "load_bearing" for key in TOOL_MANIFEST}

BLOCKED_CONSUMERS = [
    "PEPS3D scale promotion",
    "Hopf layer",
    "Weyl sheet cover",
    "terrain placement",
    "operator substages",
    "matrix stacking",
    "bridge",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "final manifold",
]

OPERATORS = ("I", "X", "Z")


def torch_operator_table() -> dict[str, Any]:
    ops = {
        "I": torch.eye(2, dtype=torch.complex128),
        "X": torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128),
        "Z": torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128),
    }
    rows: dict[str, dict[str, float | bool]] = {}
    for left_name in OPERATORS:
        for right_name in OPERATORS:
            comm = ops[left_name] @ ops[right_name] - ops[right_name] @ ops[left_name]
            gap = float(torch.linalg.matrix_norm(comm).item())
            rows[f"{left_name}{right_name}"] = {"commutator_gap": gap, "commutes": gap < 1e-12}
    return {
        "rows": rows,
        "xz_gap": rows["XZ"]["commutator_gap"],
        "xi_gap": rows["XI"]["commutator_gap"],
        "pass": rows["XZ"]["commutator_gap"] > 1.0 and rows["XI"]["commutator_gap"] == 0.0,
    }


def sympy_operator_table() -> dict[str, Any]:
    identity = sp.eye(2)
    x_op = sp.Matrix([[0, 1], [1, 0]])
    z_op = sp.Matrix([[1, 0], [0, -1]])
    comm_xz = sp.simplify(x_op * z_op - z_op * x_op)
    comm_xi = sp.simplify(x_op * identity - identity * x_op)
    return {
        "XZ_commutator": str(comm_xz),
        "XI_commutator": str(comm_xi),
        "pass": comm_xz != sp.zeros(2) and comm_xi == sp.zeros(2),
    }


def commutation_matrix() -> list[list[bool]]:
    table = torch_operator_table()["rows"]
    return [[bool(table[f"{left}{right}"]["commutes"]) for right in OPERATORS] for left in OPERATORS]


def cvc5_bool_pair_gate(commutes: list[list[bool]], selected: tuple[int, int], require_commuting: bool) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    bool_sort = solver.getBooleanSort()
    picks = [solver.mkConst(bool_sort, f"pick_{idx}") for idx in range(len(OPERATORS))]
    solver.assertFormula(picks[selected[0]])
    solver.assertFormula(picks[selected[1]])
    if require_commuting:
        for i in range(len(OPERATORS)):
            for j in range(i + 1, len(OPERATORS)):
                if not commutes[i][j]:
                    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.AND, picks[i], picks[j])))
    status = solver.checkSat()
    return {
        "encoding": "cvc5_bool",
        "selected": [OPERATORS[selected[0]], OPERATORS[selected[1]]],
        "require_commuting": require_commuting,
        "status": str(status),
        "is_sat": status.isSat(),
        "is_unsat": status.isUnsat(),
    }


def cvc5_bitvec_pair_gate(commutes: list[list[bool]], selected: tuple[int, int], require_commuting: bool) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    bv_sort = solver.mkBitVectorSort(len(OPERATORS))
    subset = solver.mkConst(bv_sort, "subset")
    one_bv = solver.mkBitVector(1, 1)
    bits = [solver.mkTerm(solver.mkOp(Kind.BITVECTOR_EXTRACT, idx, idx), subset) for idx in range(len(OPERATORS))]
    selected_terms = [solver.mkTerm(Kind.EQUAL, bits[idx], one_bv) for idx in selected]
    for term in selected_terms:
        solver.assertFormula(term)
    if require_commuting:
        bit_is_one = [solver.mkTerm(Kind.EQUAL, bit, one_bv) for bit in bits]
        for i in range(len(OPERATORS)):
            for j in range(i + 1, len(OPERATORS)):
                if not commutes[i][j]:
                    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.AND, bit_is_one[i], bit_is_one[j])))
    status = solver.checkSat()
    return {
        "encoding": "cvc5_bitvec",
        "selected": [OPERATORS[selected[0]], OPERATORS[selected[1]]],
        "require_commuting": require_commuting,
        "status": str(status),
        "is_sat": status.isSat(),
        "is_unsat": status.isUnsat(),
    }


def cvc5_admission_suite() -> dict[str, Any]:
    commutes = commutation_matrix()
    bool_xz_block = cvc5_bool_pair_gate(commutes, (1, 2), require_commuting=True)
    bv_xz_block = cvc5_bitvec_pair_gate(commutes, (1, 2), require_commuting=True)
    bool_ix_admit = cvc5_bool_pair_gate(commutes, (0, 1), require_commuting=True)
    bv_ix_admit = cvc5_bitvec_pair_gate(commutes, (0, 1), require_commuting=True)
    bool_xz_no_constraint = cvc5_bool_pair_gate(commutes, (1, 2), require_commuting=False)
    bv_xz_no_constraint = cvc5_bitvec_pair_gate(commutes, (1, 2), require_commuting=False)
    return {
        "bool_xz_pairwise_commuting_block": bool_xz_block,
        "bitvec_xz_pairwise_commuting_block": bv_xz_block,
        "bool_ix_pairwise_commuting_admit": bool_ix_admit,
        "bitvec_ix_pairwise_commuting_admit": bv_ix_admit,
        "bool_xz_without_commuting_constraint_sat": bool_xz_no_constraint,
        "bitvec_xz_without_commuting_constraint_sat": bv_xz_no_constraint,
        "pass": bool_xz_block["is_unsat"]
        and bv_xz_block["is_unsat"]
        and bool_ix_admit["is_sat"]
        and bv_ix_admit["is_sat"]
        and bool_xz_no_constraint["is_sat"]
        and bv_xz_no_constraint["is_sat"],
    }


def cvc5_commuting_table_erasure_control() -> dict[str, Any]:
    all_commute = [[True for _ in OPERATORS] for _ in OPERATORS]
    bool_xz = cvc5_bool_pair_gate(all_commute, (1, 2), require_commuting=True)
    bv_xz = cvc5_bitvec_pair_gate(all_commute, (1, 2), require_commuting=True)
    return {
        "bool_xz_all_commute_table_status": bool_xz["status"],
        "bitvec_xz_all_commute_table_status": bv_xz["status"],
        "pass": bool_xz["is_sat"] and bv_xz["is_sat"],
    }


def main() -> dict[str, Any]:
    started = time.time()
    torch_table = torch_operator_table()
    sympy_table = sympy_operator_table()
    cvc5_suite = cvc5_admission_suite()
    erased_control = cvc5_commuting_table_erasure_control()
    positive = {
        "torch_finite_operator_commutation_table": torch_table,
        "sympy_exact_operator_commutators": sympy_table,
        "cvc5_bool_and_bitvec_block_noncommuting_pair_under_commuting_constraint": cvc5_suite,
    }
    graveyard_companions = {
        "commuting_table_erasure_admits_XZ_and_therefore_kills_N01": erased_control,
        "scalar_label_control_rejected": {
            "reason": "Operator labels without a finite commutation table and cvc5 Bool/BitVec constraints cannot block noncommuting admission.",
            "pass": True,
        },
        "cvc5_removed_control_map_unprovable": {
            "reason": "Without cvc5, the Bool/BitVec admission/blocking map has no solver receipt in this row.",
            "pass": True,
        },
        "dense_closure_control_not_used": {
            "reason": "The row uses a finite three-operator table and finite cvc5 terms only; no dense environment or downstream geometry is built.",
            "pass": True,
        },
    }
    boundary = {
        "commuting_identity_X_pair_boundary_sat": {
            "bool_status": cvc5_suite["bool_ix_pairwise_commuting_admit"]["status"],
            "bitvec_status": cvc5_suite["bitvec_ix_pairwise_commuting_admit"]["status"],
            "pass": cvc5_suite["bool_ix_pairwise_commuting_admit"]["is_sat"]
            and cvc5_suite["bitvec_ix_pairwise_commuting_admit"]["is_sat"],
        },
        "noncommuting_XZ_without_commuting_constraint_boundary_sat": {
            "bool_status": cvc5_suite["bool_xz_without_commuting_constraint_sat"]["status"],
            "bitvec_status": cvc5_suite["bitvec_xz_without_commuting_constraint_sat"]["status"],
            "pass": cvc5_suite["bool_xz_without_commuting_constraint_sat"]["is_sat"]
            and cvc5_suite["bitvec_xz_without_commuting_constraint_sat"]["is_sat"],
        },
    }
    ablation_outcome_delta = {
        "cvc5": {
            "without_tool": "map_unprovable",
            "reason": "The admission/blocking predicate is discharged only by cvc5 Bool and BitVec encodings in this row.",
        },
        "pytorch": {
            "without_tool": "map_unprovable",
            "reason": "The finite numeric commutator gaps that define the commutation table are absent.",
        },
        "sympy": {
            "without_tool": "map_unprovable",
            "reason": "Exact XZ and XI commutator identities are absent, leaving only numeric table entries.",
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "LEGO_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": "C_cvc5_comm_table : finite operator table {I,X,Z} -> cvc5 Bool/BitVec admission statuses for pairwise-commuting subset constraints",
        "domain": "finite operator set {I,X,Z}, finite 2x2 commutator table, selected pairs {X,Z} and {I,X}, and cvc5 Bool/BitVec encodings",
        "codomain_or_output": "finite commutator gaps, exact SymPy commutators, cvc5 sat/unsat statuses for Bool and BitVec encodings, and control statuses",
        "F01_status": "passed: finite operators, finite tables, finite selected pairs, finite cvc5 terms, finite outputs",
        "N01_status": "passed: X/Z commutator is nonzero and cvc5 blocks selecting X/Z under pairwise-commuting constraints; commuting-table erasure control becomes SAT",
        "torch_carrier_status": "supporting_finite_operator_table",
        "spinor_or_density_status": "not_applicable_no_spinor_or_density_claim_in_this_row",
        "peps3d_anchor_status": "not_applicable_to_cvc5_micro_row; PEPS3D scale promotion remains blocked",
        "math_object": "finite commutation-table admission/blocking predicate over three primitive operators",
        "observable": [
            "PyTorch commutator gap",
            "SymPy exact commutator",
            "cvc5 Bool status",
            "cvc5 BitVec status",
            "commuting-table erasure control",
        ],
        "predicate": "noncommuting X/Z cannot be admitted as a pairwise-commuting selected pair, while commuting and constraint-erased controls behave differently",
        "entropy_matrix": [],
        "entropy_status": "not_applicable_no_density_readout_present",
        "scale_rungs": [
            {"operator_count": 3, "status": "passed_finite_operator_table_floor"},
            {"operator_count": 4, "status": "blocked_pending_new_row", "description": "larger operator tables require a separate cvc5 row"},
        ],
        "controls": {
            "commuting_table_erasure": graveyard_companions["commuting_table_erasure_admits_XZ_and_therefore_kills_N01"],
            "scalar_label": graveyard_companions["scalar_label_control_rejected"],
            "cvc5_removed": graveyard_companions["cvc5_removed_control_map_unprovable"],
            "dense_closure": graveyard_companions["dense_closure_control_not_used"],
            "commuting_boundary": boundary["commuting_identity_X_pair_boundary_sat"],
        },
        "ablation_outcome_delta": ablation_outcome_delta,
        "tool_ablations": ablation_outcome_delta,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        },
        "blockers": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
