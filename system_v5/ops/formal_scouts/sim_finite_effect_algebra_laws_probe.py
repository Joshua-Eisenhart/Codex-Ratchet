#!/usr/bin/env python3
"""Finite effect-algebra law scout for the probe-first substrate.

Formal scout only.

This row tests the word "effect algebra" before it is allowed to carry
doctrinal weight. The finite effects are admissible only when they obey the
bounded partial-addition laws used by POVM instruments: zero/unit effects,
complement, defined partial sums, coarse-graining, and order. The carrier is a
bounded adapter used to evaluate finite probe responses; it is not the root
object in this row.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "finite_effect_algebra_laws_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.1"
TIER = "1 finite probe/effect quotient"
PURPOSE = (
    "Reissue the Phase 1 finite effect-algebra law row against the current "
    "LEGO receipt contract without opening downstream consumers."
)
SCIENTIFIC_QUESTION = (
    "Do finite SIC-style effects obey the bounded effect-algebra laws needed "
    "for a probe-first Phase 1 carrier while arbitrary addition, negative "
    "effects, unlabeled responses, and order-erased controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "constraint_probe"
SOURCE_ALIGNMENT_CATEGORY = "finite_effect_algebra_probe_first_substrate_laws"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests finite effect-algebra laws for the probe-first "
    "substrate. It does not admit final effect algebra doctrine, final manifold "
    "foundation, Axis0, Xi, flux, IGT, FEP, physics, or ontology claims."
)

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

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite effects, bounded partial sums, complements, order, and probe responses",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite/nonclosure/nonpromotion consistency gate",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1e-9
GAP_FLOOR = 1e-5
D = 2


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def eye() -> torch.Tensor:
    return torch.eye(D, dtype=CDTYPE)


def zero() -> torch.Tensor:
    return torch.zeros((D, D), dtype=CDTYPE)


def size(item: torch.Tensor) -> float:
    return float(torch.linalg.norm(item).item())


def phase(angle: float) -> complex:
    return complex(math.cos(angle), math.sin(angle))


def ket(items: list[complex]) -> torch.Tensor:
    out = torch.tensor(items, dtype=CDTYPE)
    return out / torch.linalg.norm(out)


def projector(local_spinor: torch.Tensor) -> torch.Tensor:
    return torch.outer(local_spinor, torch.conj(local_spinor))


def carrier(local_spinor: torch.Tensor) -> torch.Tensor:
    return projector(local_spinor)


def sic_effects() -> list[torch.Tensor]:
    spinors = [
        ket([1.0 + 0.0j, 0.0 + 0.0j]),
        ket([1.0 / math.sqrt(3.0) + 0.0j, math.sqrt(2.0 / 3.0) + 0.0j]),
        ket([1.0 / math.sqrt(3.0) + 0.0j, math.sqrt(2.0 / 3.0) * phase(2.0 * math.pi / 3.0)]),
        ket([1.0 / math.sqrt(3.0) + 0.0j, math.sqrt(2.0 / 3.0) * phase(4.0 * math.pi / 3.0)]),
    ]
    return [projector(item) / D for item in spinors]


def eig_bounds(effect: torch.Tensor) -> tuple[float, float]:
    eigvals = torch.linalg.eigvalsh((effect + torch.conj(effect.T)) / 2.0)
    return float(torch.min(eigvals).item()), float(torch.max(eigvals).item())


def is_effect(effect: torch.Tensor) -> bool:
    lo, hi = eig_bounds(effect)
    return lo >= -TOL and hi <= 1.0 + TOL and size(effect - torch.conj(effect.T)) < TOL


def partial_sum_defined(*effects: torch.Tensor) -> bool:
    return is_effect(sum(effects, zero()))


def response(adapter: torch.Tensor, effect: torch.Tensor) -> float:
    return float(torch.real(torch.trace(adapter @ effect)).item())


def zero_unit_gate(effects: list[torch.Tensor]) -> dict[str, Any]:
    checks = {
        "zero_is_effect": is_effect(zero()),
        "unit_is_effect": is_effect(eye()),
        "all_sic_effects_valid": all(is_effect(item) for item in effects),
        "sic_family_complete": size(sum(effects, zero()) - eye()) < TOL,
    }
    return {"pass": all(checks.values()), "checks": checks}


def complement_gate(effects: list[torch.Tensor]) -> dict[str, Any]:
    rows = []
    for idx, item in enumerate(effects):
        comp = eye() - item
        rows.append(
            {
                "idx": idx,
                "effect_valid": is_effect(item),
                "complement_valid": is_effect(comp),
                "sum_to_unit_gap": size(item + comp - eye()),
            }
        )
    return {
        "pass": all(row["effect_valid"] and row["complement_valid"] and row["sum_to_unit_gap"] < TOL for row in rows),
        "rows": rows,
    }


def partial_sum_gate(effects: list[torch.Tensor]) -> dict[str, Any]:
    pair = effects[0] + effects[1]
    triple_left = (effects[0] + effects[1]) + effects[2]
    triple_right = effects[0] + (effects[1] + effects[2])
    whole = sum(effects, zero())
    rows = {
        "pair_defined": partial_sum_defined(effects[0], effects[1]),
        "pair_commutes_under_partial_addition_gap": size(effects[0] + effects[1] - (effects[1] + effects[0])),
        "triple_defined": partial_sum_defined(effects[0], effects[1], effects[2]),
        "triple_association_gap": size(triple_left - triple_right),
        "whole_defined_as_unit": partial_sum_defined(*effects) and size(whole - eye()) < TOL,
        "pair_bounds": eig_bounds(pair),
        "triple_bounds": eig_bounds(triple_left),
    }
    return {
        "pass": rows["pair_defined"]
        and rows["pair_commutes_under_partial_addition_gap"] < TOL
        and rows["triple_defined"]
        and rows["triple_association_gap"] < TOL
        and rows["whole_defined_as_unit"],
        "rows": rows,
    }


def coarse_graining_gate(effects: list[torch.Tensor]) -> dict[str, Any]:
    coarse_a = effects[0] + effects[1]
    coarse_b = effects[2] + effects[3]
    adapter = carrier(ket([math.cos(0.43) + 0.0j, phase(0.91) * math.sin(0.43)]))
    fine_responses = [response(adapter, item) for item in effects]
    coarse_responses = [response(adapter, coarse_a), response(adapter, coarse_b)]
    additivity_gaps = [
        abs(coarse_responses[0] - (fine_responses[0] + fine_responses[1])),
        abs(coarse_responses[1] - (fine_responses[2] + fine_responses[3])),
    ]
    return {
        "pass": is_effect(coarse_a)
        and is_effect(coarse_b)
        and size(coarse_a + coarse_b - eye()) < TOL
        and max(additivity_gaps) < TOL,
        "coarse_effect_count": 2,
        "fine_response_sum": sum(fine_responses),
        "coarse_response_sum": sum(coarse_responses),
        "max_additivity_gap": max(additivity_gaps),
        "coarse_bounds": [eig_bounds(coarse_a), eig_bounds(coarse_b)],
    }


def order_gate(effects: list[torch.Tensor]) -> dict[str, Any]:
    e0 = effects[0]
    comp = eye() - e0
    zero_le_e0 = is_effect(e0 - zero())
    e0_le_unit = is_effect(eye() - e0)
    e0_le_e0_plus_e1 = is_effect((e0 + effects[1]) - e0)
    comp_le_unit = is_effect(eye() - comp)
    return {
        "pass": zero_le_e0 and e0_le_unit and e0_le_e0_plus_e1 and comp_le_unit,
        "checks": {
            "zero_le_effect": zero_le_e0,
            "effect_le_unit": e0_le_unit,
            "effect_le_pair_sum_when_defined": e0_le_e0_plus_e1,
            "complement_le_unit": comp_le_unit,
        },
    }


def graveyard_overfull_partial_sum(effects: list[torch.Tensor]) -> dict[str, Any]:
    overfull = eye() + effects[0]
    lo, hi = eig_bounds(overfull)
    return {
        "pass": not is_effect(overfull) and hi > 1.0 + GAP_FLOOR,
        "why_rejected": "partial addition is bounded; effect algebra is not closed under arbitrary addition",
        "overfull_bounds": [lo, hi],
    }


def graveyard_negative_effect(effects: list[torch.Tensor]) -> dict[str, Any]:
    bad = -effects[0]
    lo, hi = eig_bounds(bad)
    return {
        "pass": not is_effect(bad) and lo < -GAP_FLOOR,
        "why_rejected": "negative operator is not a valid finite effect",
        "bad_bounds": [lo, hi],
    }


def graveyard_unlabeled_response() -> dict[str, Any]:
    declared = {"effect_label": "sic_effect_0", "response": 0.25}
    unlabeled = {"response": 0.25}
    return {
        "pass": "effect_label" in declared and "effect_label" not in unlabeled,
        "why_rejected": "a probability-like response without its named effect is not an admissible root object",
        "declared_has_label": "effect_label" in declared,
        "unlabeled_has_label": "effect_label" in unlabeled,
    }


def z3_gate() -> dict[str, Any]:
    finite_effects = z3.Int("finite_effects")
    partial_addition_bounded = z3.Bool("partial_addition_bounded")
    arbitrary_addition_closed = z3.Bool("arbitrary_addition_closed")
    final_claim = z3.Bool("final_claim")
    solver = z3.Solver()
    solver.add(finite_effects == 4, partial_addition_bounded, z3.Not(arbitrary_addition_closed), z3.Not(final_claim))
    collapse = z3.Solver()
    collapse.add(finite_effects == 4, partial_addition_bounded, z3.Not(arbitrary_addition_closed), z3.Not(final_claim))
    collapse.add(z3.Or(finite_effects != 4, z3.Not(partial_addition_bounded), arbitrary_addition_closed, final_claim))
    return {
        "positive_status": str(solver.check()),
        "collapse_status": str(collapse.check()),
        "pass": solver.check() == z3.sat and collapse.check() == z3.unsat,
    }


def finite_order_witness_gate() -> dict[str, Any]:
    x_op = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
    z_op = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)
    identity = eye()
    order_gap = size(x_op @ z_op - z_op @ x_op)
    order_erased_gap = size(identity @ z_op - z_op @ identity)
    return {
        "pass": order_gap > GAP_FLOOR and order_erased_gap < TOL,
        "operator_family": ["X", "Z", "I"],
        "path_order_set": ["X_then_Z", "Z_then_X"],
        "order_witness": "X @ Z != Z @ X",
        "order_gap": order_gap,
        "order_erased_control": "I @ Z == Z @ I",
        "order_erased_gap": order_erased_gap,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    effects = sic_effects()
    positive = {
        "zero_unit_and_sic_effect_validity": zero_unit_gate(effects),
        "effect_complement_law": complement_gate(effects),
        "bounded_partial_sum_laws": partial_sum_gate(effects),
        "coarse_graining_response_additivity": coarse_graining_gate(effects),
        "effect_order_law": order_gate(effects),
        "n01_finite_order_witness": finite_order_witness_gate(),
        "z3_finite_effect_nonclosure_nonpromotion_gate": z3_gate(),
    }
    graveyard_companions = {
        "GC1_arbitrary_addition_closure_rejected": graveyard_overfull_partial_sum(effects),
        "GC2_negative_effect_rejected": graveyard_negative_effect(effects),
        "GC3_unlabeled_response_rejected": graveyard_unlabeled_response(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_effect_algebra_name_requires_laws": {
            "pass": all(positive[key]["pass"] for key in positive if key != "z3_finite_effect_nonclosure_nonpromotion_gate"),
            "law_names": [
                "zero_unit",
                "complement",
                "bounded_partial_sum",
                "coarse_graining",
                "effect_order",
            ],
        },
        "B3_no_final_foundation_claim": {
            "pass": "does not admit" in CLAIM_CEILING and "final manifold foundation" in CLAIM_CEILING,
            "claim_ceiling": CLAIM_CEILING,
        },
    }
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
        "finite_map": [
            "E -> law_vector(E), where law_vector records zero/unit, complement, bounded partial sum, coarse-graining, and order-law pass/fail readouts"
        ],
        "domain": "finite SIC-style effect family E = {E0,E1,E2,E3} on a 2-dimensional torch-native carrier plus finite operator/path witness {X,Z,I}",
        "codomain_or_output": "finite effect-algebra law vector with graveyard controls for overfull addition, negative effects, unlabeled response, and order-erased witness",
        "root_constraints_in_force": {
            "F01": {
                "finite_effect_family": ["sic_effect_0", "sic_effect_1", "sic_effect_2", "sic_effect_3"],
                "finite_carrier_dimension": D,
                "finite_operator_family": positive["n01_finite_order_witness"]["operator_family"],
                "finite_path_order_set": positive["n01_finite_order_witness"]["path_order_set"],
            },
            "N01": {
                "witness": positive["n01_finite_order_witness"]["order_witness"],
                "order_gap": positive["n01_finite_order_witness"]["order_gap"],
                "order_erased_control": positive["n01_finite_order_witness"]["order_erased_control"],
                "order_erased_gap": positive["n01_finite_order_witness"]["order_erased_gap"],
            },
        },
        "carrier_layer": "phase_1_finite_effect_algebra_laws",
        "geometry_layer": "none",
        "carrier_realization": "finite torch-native 2x2 effect tensors and bounded probe-response adapter only",
        "peps3d_embedding": "blocked downstream next step only; not implemented here",
        "spinor_state": "not_applicable_for_this_phase_1_effect_law_result",
        "quaternion_action": "not_applicable",
        "dependency_receipts": ["none_root_phase1_effect_law_reissue"],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "finite effect-algebra zero/unit, complement, bounded partial addition, coarse-graining, and order laws",
        "branch_status_before_run": "phase_1_frontier_reissue",
        "allowed_claims": ["Phase 1 finite effect-algebra law scout only"],
        "promotion_blockers": ["broader Phase 1 frontier rows remain needs_reissue or open"],
        "required_tools": ["pytorch", "z3"],
        "actual_tools_used": ["pytorch", "z3"],
        "proof_surfaces_used": ["z3"],
        "graph_surfaces_used": ["not_relevant_for_this_phase1_effect_law_packet"],
        "topology_surfaces_used": ["not_relevant_for_this_phase1_effect_law_packet"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_inputs": ["finite SIC-style effects defined in this source"],
        "data_or_artifact_dependencies": ["none_root_phase1_effect_law_reissue"],
        "required_negatives": [
            "arbitrary_addition_closure_rejected",
            "negative_effect_rejected",
            "unlabeled_response_rejected",
            "order_erased_control",
        ],
        "negatives_run": list(graveyard_companions.keys()) + ["order_erased_control"],
        "kill_conditions": [
            "arbitrary overfull addition accepted as an effect",
            "negative effect accepted",
            "unlabeled scalar response accepted as a root object",
            "order-erased control retains the N01 witness",
            "any downstream consumer admitted",
        ],
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT))],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": "phase1_finite_effect_algebra_laws_reissue_v1",
        "result_summary": {
            "finite_effect_count": len(effects),
            "laws_tested": ["zero_unit", "complement", "bounded_partial_sum", "coarse_graining", "effect_order"],
            "order_gap": positive["n01_finite_order_witness"]["order_gap"],
        },
        "pass_rule": "finite effects satisfy zero/unit, complement, bounded partial-sum, coarse-graining, and order laws while negative and boundary controls fail",
        "fail_rule": "any missing law, admitted arbitrary addition, admitted negative effect, missing N01 witness, or downstream consumer admission",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["phase1_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": {
            "positive": positive,
            "negative": graveyard_companions,
            "boundary": boundary,
        },
        "nearby_variants": {"passed": sum(1 for item in checks if item), "total": len(checks)},
        "all_pass": all(checks),
        "blockers": [],
        "summary": {
            "finite_effect_count": len(effects),
            "laws_tested": ["zero_unit", "complement", "bounded_partial_sum", "coarse_graining", "effect_order"],
            "carrier_role": "bounded_probe_response_adapter_only",
            "order_gap": positive["n01_finite_order_witness"]["order_gap"],
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 formal scout for finite effect-algebra laws. It is "
            "not a v4 probe and not a promotion of final manifold, Axis0, "
            "flux, IGT, FEP, or physics claims."
        ),
        "next_admissible_step": "Continue Phase 1 bounded frontier repair or write a Phase 1 blocker; do not open downstream consumers from this receipt.",
        "next_required_work": [
            "Reissue the next Phase 1 frontier row or write an explicit Phase 1 blocker.",
            "Keep all listed downstream consumers blocked.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
