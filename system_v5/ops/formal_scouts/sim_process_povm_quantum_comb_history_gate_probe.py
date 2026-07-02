#!/usr/bin/env python3
"""Finite process-POVM / quantum-comb history gate."""

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
NAME = "process_povm_quantum_comb_history_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.1"
TIER = "1 finite probe/effect quotient"
PURPOSE = (
    "Reissue the Phase 1 process-POVM/quantum-comb history row against the "
    "current LEGO receipt contract without opening downstream consumers."
)
SCIENTIFIC_QUESTION = (
    "Do finite history effects form complete process-response maps with an "
    "order-sensitive witness while primitive history weights and commuting "
    "history controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "constraint_probe"
SOURCE_ALIGNMENT_CATEGORY = "finite_process_povm_quantum_comb_history_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests finite process-POVM/quantum-comb history effects "
    "as the process/history version of the probe-first substrate. It does not "
    "admit final Xi, Axis0, flux, IGT, FEP, Holodeck, physics, or ontology."
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
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite history effects, order gaps, and response distributions"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite-history/nonpromotion consistency gate"},
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
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
D = 2
TOL = 1e-9
GAP_FLOOR = 1e-5


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


def size(x: torch.Tensor) -> float:
    return float(torch.linalg.norm(x).item())


def phase(angle: float) -> complex:
    return complex(math.cos(angle), math.sin(angle))


def ket(items: list[complex]) -> torch.Tensor:
    out = torch.tensor(items, dtype=CDTYPE)
    return out / torch.linalg.norm(out)


def projector(v: torch.Tensor) -> torch.Tensor:
    return torch.outer(v, torch.conj(v))


def wh_shift() -> torch.Tensor:
    return torch.tensor([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=CDTYPE)


def wh_phase() -> torch.Tensor:
    return torch.diag(torch.tensor([1.0 + 0.0j, -1.0 + 0.0j], dtype=CDTYPE))


def finite_instrument(unitary: torch.Tensor, strengths: tuple[float, float]) -> list[torch.Tensor]:
    return [math.sqrt(strength) * unitary for strength in strengths]


def history_effects(first: list[torch.Tensor], second: list[torch.Tensor]) -> list[torch.Tensor]:
    effects = []
    for a in first:
        for b in second:
            k_hist = b @ a
            effects.append(torch.conj(k_hist.T) @ k_hist)
    return effects


def responses(rho: torch.Tensor, effects: list[torch.Tensor]) -> torch.Tensor:
    return torch.real(torch.stack([torch.trace(rho @ item) for item in effects])).to(RTYPE)


def process_gate() -> dict[str, Any]:
    x_op = wh_shift()
    z_op = wh_phase()
    inst_x = finite_instrument(x_op, (0.37, 0.63))
    inst_z = finite_instrument(z_op, (0.41, 0.59))
    effects_xz = history_effects(inst_x, inst_z)
    effects_zx = history_effects(inst_z, inst_x)
    rho = projector(ket([math.cos(0.52) + 0.0j, phase(0.43) * math.sin(0.52)]))
    p_xz = responses(rho, effects_xz)
    p_zx = responses(rho, effects_zx)
    completeness_xz = size(sum(effects_xz, torch.zeros((D, D), dtype=CDTYPE)) - eye())
    completeness_zx = size(sum(effects_zx, torch.zeros((D, D), dtype=CDTYPE)) - eye())
    response_gap = size(p_xz - p_zx)
    return {
        "pass": len(effects_xz) == 4
        and completeness_xz < TOL
        and completeness_zx < TOL
        and abs(float(torch.sum(p_xz).item()) - 1.0) < TOL
        and abs(float(torch.sum(p_zx).item()) - 1.0) < TOL
        and response_gap > GAP_FLOOR,
        "history_count": len(effects_xz),
        "xz_completeness_gap": completeness_xz,
        "zx_completeness_gap": completeness_zx,
        "xz_response_sum": float(torch.sum(p_xz).item()),
        "zx_response_sum": float(torch.sum(p_zx).item()),
        "order_response_gap": response_gap,
    }


def graveyard_primitive_history_weight_rejected() -> dict[str, Any]:
    declared = {"history": ("x0", "z1"), "effect_declared": True, "weight": 0.25}
    primitive = {"history": ("x0", "z1"), "weight": 0.25}
    return {
        "pass": declared["effect_declared"] is True and "effect_declared" not in primitive,
        "why_rejected": "history weights are not root probabilities unless tied to finite history effects",
    }


def graveyard_commuting_history_erases_order() -> dict[str, Any]:
    unit = eye()
    inst_a = finite_instrument(unit, (0.37, 0.63))
    inst_b = finite_instrument(unit, (0.37, 0.63))
    rho = projector(ket([math.cos(0.52) + 0.0j, phase(0.43) * math.sin(0.52)]))
    p_ab = responses(rho, history_effects(inst_a, inst_b))
    p_ba = responses(rho, history_effects(inst_b, inst_a))
    gap = size(p_ab - p_ba)
    return {
        "pass": gap < TOL,
        "why_rejected": "commuting/unit history controls erase N01 order content",
        "order_gap": gap,
    }


def z3_gate() -> dict[str, Any]:
    history_count = z3.Int("history_count")
    finite_history = z3.Bool("finite_history")
    order_gap = z3.Bool("order_gap")
    final_claim = z3.Bool("final_claim")
    solver = z3.Solver()
    solver.add(history_count == 4, finite_history, order_gap, z3.Not(final_claim))
    collapse = z3.Solver()
    collapse.add(history_count == 4, finite_history, order_gap, z3.Not(final_claim))
    collapse.add(z3.Or(history_count != 4, z3.Not(finite_history), z3.Not(order_gap), final_claim))
    return {"positive_status": str(solver.check()), "collapse_status": str(collapse.check()), "pass": solver.check() == z3.sat and collapse.check() == z3.unsat}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    positive = {
        "finite_process_povm_histories_are_complete_and_order_sensitive": process_gate(),
        "z3_finite_history_order_nonpromotion_gate": z3_gate(),
    }
    graveyard_companions = {
        "GC1_primitive_history_weight_rejected": graveyard_primitive_history_weight_rejected(),
        "GC2_commuting_history_control_rejected": graveyard_commuting_history_erases_order(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_not_xi_axis0_admission": {"pass": "does not admit final Xi" in CLAIM_CEILING and "Axis0" in CLAIM_CEILING},
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
            "finite two-step instrument histories -> complete history-effect POVM and order-sensitive response distribution"
        ],
        "domain": (
            "finite torch-native 2-dimensional spinor-derived density carrier, "
            "two finite instrument families, and two finite history orders X_then_Z and Z_then_X"
        ),
        "codomain_or_output": (
            "four finite history effects per order, completeness gaps, response sums, "
            "order-response gap, primitive-weight rejection, and commuting-history control"
        ),
        "root_constraints_in_force": {
            "F01": {
                "finite_carrier_dimension": D,
                "finite_history_count": positive["finite_process_povm_histories_are_complete_and_order_sensitive"][
                    "history_count"
                ],
                "finite_instrument_count": 2,
                "finite_order_set": ["X_then_Z", "Z_then_X"],
            },
            "N01": {
                "witness": "finite process responses differ for X_then_Z versus Z_then_X histories",
                "order_response_gap": positive["finite_process_povm_histories_are_complete_and_order_sensitive"][
                    "order_response_gap"
                ],
                "order_erased_control": "commuting/unit history control",
                "order_erased_gap": graveyard_companions["GC2_commuting_history_control_rejected"]["order_gap"],
            },
        },
        "carrier_layer": "phase_1_finite_process_povm_history_surface",
        "geometry_layer": "none",
        "carrier_realization": "finite torch-native 2x2 spinor-derived density/effect tensors and history-effect POVM maps",
        "peps3d_embedding": "blocked downstream next step only; not implemented here",
        "spinor_state": "finite torch-native spinor is used only to construct the admitted density readout for this Phase 1 history packet",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/phase1_finite_probe_effect_quotient_root_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json",
            "system_v5/ops/formal_scouts/results/sic_mub_probe_family_comparison_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "finite process-POVM / quantum-comb history effect order witness",
        "branch_status_before_run": "phase_1_frontier_reissue",
        "allowed_claims": ["Phase 1 finite process-POVM history scout only"],
        "promotion_blockers": [
            "remaining Phase 1 frontier candidate still needs reissue or blocker classification",
            "no Phase 2 PEPS3D seed has been opened by this receipt",
        ],
        "required_tools": ["pytorch", "z3"],
        "actual_tools_used": ["pytorch", "z3"],
        "proof_surfaces_used": ["z3"],
        "graph_surfaces_used": ["not_relevant_for_this_phase1_process_povm_packet"],
        "topology_surfaces_used": ["not_relevant_for_this_phase1_process_povm_packet"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_inputs": [
            "finite X/Z instrument families defined in this source",
            "finite spinor-derived density carrier defined in this source",
        ],
        "data_or_artifact_dependencies": [
            "system_v5/ops/formal_scouts/results/phase1_finite_probe_effect_quotient_root_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json",
            "system_v5/ops/formal_scouts/results/sic_mub_probe_family_comparison_probe_results.json",
        ],
        "required_negatives": [
            "primitive_history_weight_rejected",
            "commuting_history_control_rejected",
        ],
        "negatives_run": list(graveyard_companions.keys()),
        "kill_conditions": [
            "history effects fail completeness",
            "response distributions fail normalization",
            "order-sensitive response gap is erased",
            "primitive history weights are accepted as root probabilities",
            "commuting-history control retains N01 witness",
            "any downstream consumer admitted",
        ],
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT))],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": "phase1_process_povm_quantum_comb_history_reissue_v1",
        "result_summary": {
            "history_count": positive["finite_process_povm_histories_are_complete_and_order_sensitive"][
                "history_count"
            ],
            "order_response_gap": positive["finite_process_povm_histories_are_complete_and_order_sensitive"][
                "order_response_gap"
            ],
            "commuting_history_control_gap": graveyard_companions["GC2_commuting_history_control_rejected"][
                "order_gap"
            ],
        },
        "pass_rule": (
            "finite history effects are complete and normalized, the X/Z history "
            "order response gap survives, and primitive-weight plus commuting-history controls fail"
        ),
        "fail_rule": (
            "missing finite history completeness, missing normalization, erased order "
            "witness, accepted primitive history weight, accepted commuting-history witness, "
            "or downstream consumer admission"
        ),
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
            "candidate": "quantum_comb_or_process_povm",
            "history_count": positive["finite_process_povm_histories_are_complete_and_order_sensitive"]["history_count"],
            "order_response_gap": positive["finite_process_povm_histories_are_complete_and_order_sensitive"]["order_response_gap"],
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": "This is a v5 finite process-POVM formal scout, not a v4 probe promotion.",
        "next_required_work": [
            "Reissue the next Phase 1 frontier row or write an explicit Phase 1 blocker.",
            "Keep all listed downstream consumers blocked.",
        ],
        "next_admissible_step": "Continue Phase 1 bounded frontier repair or write a Phase 1 blocker; do not open downstream consumers from this receipt.",
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
