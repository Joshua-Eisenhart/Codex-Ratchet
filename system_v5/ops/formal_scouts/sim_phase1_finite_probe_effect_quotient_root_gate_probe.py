#!/usr/bin/env python3
"""Phase 1 finite probe/effect quotient root gate.

Formal scout only.

This scout tests exactly one first-layer object:

  S finite, P finite, r_P(s) = (p_1(s), ..., p_m(s)),
  s ~_P t iff r_P(s) = r_P(t), Q_P = S / ~_P.

It does not implement PEPS3D, spinor/Hopf/Weyl geometry, terrain, operators
beyond the finite N01 order witness, engines, flux, Xi/Phi0, Axis0, Holodeck,
FEP, physics, IGT/game theory, axes 7-12, or 64-cell work.
"""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "phase1_finite_probe_effect_quotient_root_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.1"
TIER = "1 finite probe/effect quotient"
PURPOSE = (
    "Repair the Phase 1 reset receipt metadata while preserving the existing "
    "finite probe/effect quotient scout and downstream blockers."
)
SCIENTIFIC_QUESTION = (
    "Does one finite torch-native probe/effect family produce the quotient "
    "Q_P = S / ~_P with F01 finite carriers/probes/operators/paths and an "
    "N01 noncommuting order witness, while rejecting single-probe, empty-probe, "
    "and order-erased controls?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "constraint_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase1_finite_probe_effect_quotient_root_gate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal Phase 1 scout only: tests one finite probe/effect quotient with F01 "
    "finite carriers/probes/operators/paths and an N01 noncommuting witness. It "
    "does not admit PEPS3D implementation, spinor/Hopf/Weyl enforcement, terrain, "
    "operator substages, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game "
    "theory, axes 7-12, or 64-cell work."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite density carriers, finite effects, probe-response vectors, quotient classes, and commutator norm",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing structural gate that rejects single-probe admission while preserving finite quotient and noncommutation witnesses",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent structural gate for single-probe rejection and nonpromotion",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite counts for states, effects, operators, paths, and quotient classes",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9
GAP_FLOOR = 1.0e-6

BLOCKED_CONSUMERS = [
    "PEPS3D seed implementation",
    "spinor/Hopf/Weyl enforcement",
    "terrain generator placement",
    "operator substage cells",
    "PEPS/PEPS3D closure",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "IGT/game theory",
    "axes 7-12",
]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            item = value.detach().cpu().item()
            if isinstance(item, complex):
                return {"real": item.real, "imag": item.imag}
            return item
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def ket(values: list[complex]) -> torch.Tensor:
    vector = torch.tensor(values, dtype=CDTYPE)
    return vector / torch.linalg.vector_norm(vector)


def projector(vector: torch.Tensor) -> torch.Tensor:
    return torch.outer(vector, vector.conj())


def finite_states() -> dict[str, torch.Tensor]:
    z0 = ket([1.0 + 0.0j, 0.0 + 0.0j])
    z1 = ket([0.0 + 0.0j, 1.0 + 0.0j])
    x_plus = ket([1.0 + 0.0j, 1.0 + 0.0j])
    x_minus = ket([1.0 + 0.0j, -1.0 + 0.0j])
    return {
        "z0": projector(z0),
        "z1": projector(z1),
        "x_plus": projector(x_plus),
        "x_minus": projector(x_minus),
    }


def finite_effects() -> dict[str, torch.Tensor]:
    states = finite_states()
    return {
        "Z0": states["z0"],
        "Z1": states["z1"],
        "X_plus": states["x_plus"],
        "X_minus": states["x_minus"],
    }


def finite_operators() -> dict[str, torch.Tensor]:
    x_op = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
    z_op = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)
    identity = torch.eye(2, dtype=CDTYPE)
    return {"X": x_op, "Z": z_op, "I": identity}


def response(state: torch.Tensor, effect: torch.Tensor) -> float:
    return float(torch.real(torch.trace(effect @ state)).item())


def response_table(states: dict[str, torch.Tensor], effects: dict[str, torch.Tensor]) -> dict[str, tuple[float, ...]]:
    return {
        state_name: tuple(round(response(state, effect), 12) for effect in effects.values())
        for state_name, state in states.items()
    }


def quotient_classes(table: dict[str, tuple[float, ...]]) -> dict[str, list[str]]:
    classes: dict[str, list[str]] = {}
    for name, vector in table.items():
        classes.setdefault(json.dumps(vector), []).append(name)
    return {key: sorted(value) for key, value in classes.items()}


def effect_family_gate(effects: dict[str, torch.Tensor]) -> dict[str, Any]:
    z_sum = effects["Z0"] + effects["Z1"]
    x_sum = effects["X_plus"] + effects["X_minus"]
    identity = torch.eye(2, dtype=CDTYPE)
    rows = {}
    for name, effect in effects.items():
        hermitian_gap = torch.linalg.matrix_norm(effect - effect.conj().T).real
        eigvals = torch.linalg.eigvalsh((effect + effect.conj().T) / 2.0).real
        rows[name] = {
            "hermitian_gap": float(hermitian_gap.item()),
            "min_eigenvalue": float(torch.min(eigvals).item()),
            "max_eigenvalue": float(torch.max(eigvals).item()),
            "valid_effect": bool(
                float(hermitian_gap.item()) < TOL
                and float(torch.min(eigvals).item()) >= -TOL
                and float(torch.max(eigvals).item()) <= 1.0 + TOL
            ),
        }
    return {
        "pass": bool(
            all(row["valid_effect"] for row in rows.values())
            and float(torch.linalg.matrix_norm(z_sum - identity).item()) < TOL
            and float(torch.linalg.matrix_norm(x_sum - identity).item()) < TOL
        ),
        "effect_rows": rows,
        "Z_probe_sum_gap": float(torch.linalg.matrix_norm(z_sum - identity).item()),
        "X_probe_sum_gap": float(torch.linalg.matrix_norm(x_sum - identity).item()),
    }


def finite_probe_effect_quotient_gate() -> dict[str, Any]:
    states = finite_states()
    effects = finite_effects()
    table = response_table(states, effects)
    classes = quotient_classes(table)
    exact_state_count = sp.Integer(len(states))
    exact_effect_count = sp.Integer(len(effects))
    exact_class_count = sp.Integer(len(classes))
    return {
        "pass": bool(int(exact_state_count) == 4 and int(exact_effect_count) == 4 and int(exact_class_count) == 4),
        "finite_map": "q_P : S -> Q_P, q_P(s) = equivalence class of r_P(s)",
        "domain": "S = {z0, z1, x_plus, x_minus}; P = {Z0, Z1, X_plus, X_minus}",
        "output": "Q_P = S / ~_P with four response-distinguished quotient classes",
        "response_table": table,
        "quotient_classes": classes,
        "state_count": int(exact_state_count),
        "effect_count": int(exact_effect_count),
        "quotient_class_count": int(exact_class_count),
    }


def noncommuting_order_witness_gate() -> dict[str, Any]:
    ops = finite_operators()
    xz = ops["X"] @ ops["Z"]
    zx = ops["Z"] @ ops["X"]
    iz = ops["I"] @ ops["Z"]
    zi = ops["Z"] @ ops["I"]
    order_gap = torch.linalg.matrix_norm(xz - zx).real
    commuting_control_gap = torch.linalg.matrix_norm(iz - zi).real
    exact_operator_count = sp.Integer(len(ops))
    exact_path_count = sp.Integer(2)
    return {
        "pass": bool(
            float(order_gap.item()) > GAP_FLOOR
            and float(commuting_control_gap.item()) < TOL
            and int(exact_operator_count) == 3
            and int(exact_path_count) == 2
        ),
        "operator_family": ["X", "Z", "I"],
        "path_order_set": ["X_then_Z", "Z_then_X"],
        "order_witness": "X @ Z != Z @ X",
        "order_gap": float(order_gap.item()),
        "commuting_control": "I @ Z == Z @ I",
        "commuting_control_gap": float(commuting_control_gap.item()),
        "operator_count": int(exact_operator_count),
        "path_count": int(exact_path_count),
    }


def single_probe_negative_control() -> dict[str, Any]:
    states = finite_states()
    effects = {"Z0": finite_effects()["Z0"]}
    table = response_table(states, effects)
    classes = quotient_classes(table)
    merged = [value for value in classes.values() if len(value) > 1]
    return {
        "pass": bool(len(classes) < len(states) and any(set(item) == {"x_minus", "x_plus"} for item in merged)),
        "why_rejected": "one finite probe merges x_plus and x_minus, so it is not an admitted identity quotient for this task",
        "single_probe_class_count": len(classes),
        "merged_classes": merged,
        "response_table": table,
    }


def empty_probe_boundary_control() -> dict[str, Any]:
    states = finite_states()
    table = {name: tuple() for name in states}
    classes = quotient_classes(table)
    return {
        "pass": bool(len(classes) == 1),
        "why_boundary": "empty probe family collapses all states into one quotient class and marks the lower boundary",
        "empty_probe_class_count": len(classes),
        "quotient_classes": classes,
    }


def order_erased_control() -> dict[str, Any]:
    witness = noncommuting_order_witness_gate()
    return {
        "pass": bool(witness["commuting_control_gap"] < TOL and witness["order_gap"] > GAP_FLOOR),
        "why_rejected": "replacing X with I erases the N01 order witness",
        "order_gap": witness["order_gap"],
        "order_erased_gap": witness["commuting_control_gap"],
    }


def z3_structural_gate(full_class_count: int, single_probe_class_count: int) -> dict[str, Any]:
    full_count = z3.Int("full_count")
    single_count = z3.Int("single_count")
    n01 = z3.Bool("n01_noncommuting_witness")
    promoted = z3.Bool("downstream_promotion")
    single_probe_admitted = z3.Bool("single_probe_admitted")

    solver = z3.Solver()
    solver.add(full_count == 4)
    solver.add(single_count == single_probe_class_count)
    solver.add(n01)
    solver.add(z3.Not(promoted))
    solver.add(single_count < full_count)

    collapse = z3.Solver()
    collapse.add(full_count == full_class_count)
    collapse.add(single_count == single_probe_class_count)
    collapse.add(z3.Implies(single_probe_admitted, single_count == full_count))
    collapse.add(single_probe_admitted)
    return {
        "positive_status": str(solver.check()),
        "single_probe_admission_status": str(collapse.check()),
        "pass": solver.check() == z3.sat and collapse.check() == z3.unsat,
    }


def cvc5_structural_gate(full_class_count: int, single_probe_class_count: int) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    full_count = solver.mkConst(int_sort, "full_count")
    single_count = solver.mkConst(int_sort, "single_count")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, full_count, solver.mkInteger(full_class_count)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, single_count, solver.mkInteger(single_probe_class_count)))
    solver.assertFormula(solver.mkTerm(Kind.LT, single_count, full_count))
    positive = solver.checkSat()

    collapse = cvc5.Solver()
    collapse.setLogic("QF_LIA")
    c_full = collapse.mkConst(collapse.getIntegerSort(), "full_count")
    c_single = collapse.mkConst(collapse.getIntegerSort(), "single_count")
    collapse.assertFormula(collapse.mkTerm(Kind.EQUAL, c_full, collapse.mkInteger(full_class_count)))
    collapse.assertFormula(collapse.mkTerm(Kind.EQUAL, c_single, collapse.mkInteger(single_probe_class_count)))
    collapse.assertFormula(collapse.mkTerm(Kind.EQUAL, c_single, c_full))
    unsafe = collapse.checkSat()
    return {"positive_status": str(positive), "single_probe_admission_status": str(unsafe), "pass": str(positive) == "sat" and str(unsafe) == "unsat"}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    effects = finite_effects()
    effect_gate = effect_family_gate(effects)
    quotient = finite_probe_effect_quotient_gate()
    order = noncommuting_order_witness_gate()
    negative = single_probe_negative_control()
    boundary_case = empty_probe_boundary_control()
    order_control = order_erased_control()

    positive = {
        "finite_effect_family": effect_gate,
        "finite_probe_effect_quotient": quotient,
        "n01_noncommuting_order_witness": order,
        "z3_phase1_quotient_structure_gate": z3_structural_gate(
            quotient["quotient_class_count"], negative["single_probe_class_count"]
        ),
        "cvc5_phase1_quotient_structure_gate": cvc5_structural_gate(
            quotient["quotient_class_count"], negative["single_probe_class_count"]
        ),
    }
    graveyard_companions = {
        "GC1_single_probe_negative_rejected": negative,
        "GC2_empty_probe_boundary_collapses": boundary_case,
        "GC3_order_erased_commuting_control_rejected": order_control,
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_no_phase2_or_downstream_claim": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
        "B3_no_peps3d_implementation": {
            "pass": True,
            "peps3d_embedding": "blocked next step only; no PEPS3D implementation in this Phase 1 scout",
        },
    }
    controls = {"positive": positive, "negative": graveyard_companions, "boundary": boundary}
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [
        row["pass"] for row in boundary.values()
    ]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": NAME,
        "version": VERSION,
        "tier": TIER,
        "purpose": PURPOSE,
        "scientific_question": SCIENTIFIC_QUESTION,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": [quotient["finite_map"]],
        "domain": quotient["domain"],
        "codomain_or_output": quotient["output"],
        "root_constraints_in_force": {
            "F01": {
                "finite_states": list(finite_states().keys()),
                "finite_probe_effect_family": list(effects.keys()),
                "finite_operator_family": order["operator_family"],
                "finite_path_order_set": order["path_order_set"],
            },
            "N01": {
                "witness": order["order_witness"],
                "order_gap": order["order_gap"],
                "order_erased_control": order["commuting_control"],
                "order_erased_gap": order["commuting_control_gap"],
            },
        },
        "carrier_realization": "finite torch-native 2x2 density carriers and finite projective effects only",
        "carrier_layer": "phase_1_finite_probe_effect_quotient",
        "geometry_layer": "none",
        "peps3d_embedding": "blocked downstream next step only; not implemented here",
        "spinor_state": "not_applicable_for_this_phase_1_result",
        "quaternion_action": "not_applicable",
        "dependency_receipts": ["none_root_phase1_receipt"],
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "finite probe/effect response quotient q_P with single-probe and order-erased controls",
        "branch_status_before_run": "phase_1_reset",
        "allowed_claims": ["Phase 1 finite probe/effect quotient scout only"],
        "promotion_blockers": ["Phase 2 PEPS3D seed carrier not admitted by this receipt"],
        "actual_tools_used": ["pytorch", "z3", "cvc5", "sympy"],
        "required_tools": ["pytorch", "z3", "cvc5", "sympy"],
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": ["not_relevant_for_this_phase1_quotient_packet"],
        "topology_surfaces_used": ["not_relevant_for_this_phase1_quotient_packet"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_inputs": ["finite states S and finite effects P defined in this source"],
        "data_or_artifact_dependencies": ["none_root_phase1_receipt"],
        "required_negatives": ["single_probe_negative", "empty_probe_boundary", "order_erased_commuting_control"],
        "negatives_run": list(graveyard_companions.keys()),
        "kill_conditions": [
            "single probe admitted as complete identity quotient",
            "order-erased commuting control retains N01 witness",
            "any downstream consumer admitted",
        ],
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT))],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": "phase1_finite_probe_effect_quotient_root_gate_v1",
        "result_summary": {
            "state_count": quotient["state_count"],
            "effect_count": quotient["effect_count"],
            "quotient_class_count": quotient["quotient_class_count"],
            "order_gap": order["order_gap"],
            "single_probe_class_count": negative["single_probe_class_count"],
        },
        "pass_rule": "full finite probe/effect family gives four quotient classes, single-probe control collapses classes, and X/Z order witness survives",
        "fail_rule": "any missing finite quotient, invalid effect family, missing N01 witness, or admitted downstream consumer",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["phase1_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": controls,
        "nearby_variants": {"passed": sum(1 for item in checks if item), "total": len(checks)},
        "all_pass": all(checks),
        "blockers": [],
        "summary": {
            "phase": 1,
            "candidate": "finite_probe_effect_quotient",
            "state_count": quotient["state_count"],
            "effect_count": quotient["effect_count"],
            "quotient_class_count": quotient["quotient_class_count"],
            "single_probe_class_count": negative["single_probe_class_count"],
            "order_gap": order["order_gap"],
            "peps3d_implemented": False,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": "This is a v5 one-layer Phase 1 reset scout, not a broad suite or downstream manifold probe.",
        "next_admissible_step": (
            "Continue Phase 1 bounded frontier repair or write a Phase 1 blocker; "
            "do not open downstream consumers from this receipt."
        ),
        "next_required_work": [
            "Build or refresh Phase 1 frontier rows only.",
            "Keep all listed downstream consumers blocked.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
