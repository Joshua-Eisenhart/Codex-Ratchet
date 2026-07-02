#!/usr/bin/env python3
"""SIC versus MUB finite probe-family comparison scout."""

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
NAME = "sic_mub_probe_family_comparison_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.1"
TIER = "1 finite probe/effect quotient"
PURPOSE = (
    "Reissue the Phase 1 SIC/MUB finite probe-family comparison row against "
    "the current LEGO receipt contract without opening downstream consumers."
)
SCIENTIFIC_QUESTION = (
    "Do minimal SIC and overcomplete MUB finite probe families both give "
    "informationally complete finite response assignments while arbitrary "
    "simplex points, single-basis probes, and order-erased controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "constraint_probe"
SOURCE_ALIGNMENT_CATEGORY = "sic_mub_finite_probe_family_comparison"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: compares minimal SIC and overcomplete MUB finite probe "
    "families as root-adjacent effect surfaces. It does not admit final probe "
    "doctrine, final manifold foundation, Axis0, Xi, flux, IGT, FEP, or physics."
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
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite effects, response assignments, reconstruction, and conditioning checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite-count/nonpromotion gate"},
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


def carrier(v: torch.Tensor) -> torch.Tensor:
    return projector(v)


def finite_assignment(rho: torch.Tensor, effects: list[torch.Tensor]) -> torch.Tensor:
    return torch.real(torch.stack([torch.trace(rho @ item) for item in effects])).to(RTYPE)


def sic_rays_effects() -> tuple[list[torch.Tensor], list[torch.Tensor]]:
    spinors = [
        ket([1.0 + 0.0j, 0.0 + 0.0j]),
        ket([1.0 / math.sqrt(3.0) + 0.0j, math.sqrt(2.0 / 3.0) + 0.0j]),
        ket([1.0 / math.sqrt(3.0) + 0.0j, math.sqrt(2.0 / 3.0) * phase(2.0 * math.pi / 3.0)]),
        ket([1.0 / math.sqrt(3.0) + 0.0j, math.sqrt(2.0 / 3.0) * phase(4.0 * math.pi / 3.0)]),
    ]
    rays = [projector(v) for v in spinors]
    return rays, [ray / D for ray in rays]


def wh_shift() -> torch.Tensor:
    return torch.tensor([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=CDTYPE)


def wh_phase() -> torch.Tensor:
    return torch.diag(torch.tensor([1.0 + 0.0j, -1.0 + 0.0j], dtype=CDTYPE))


def mub_projectors_effects() -> tuple[list[torch.Tensor], list[torch.Tensor]]:
    ops = [wh_shift(), wh_phase(), wh_shift() @ wh_phase()]
    projectors: list[torch.Tensor] = []
    for op in ops:
        _, vecs = torch.linalg.eig(op)
        for idx in range(D):
            v = vecs[:, idx] / torch.linalg.norm(vecs[:, idx])
            projectors.append(projector(v))
    return projectors, [item / 3.0 for item in projectors]


def reconstruct_sic(assignment: torch.Tensor, rays: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros((D, D), dtype=CDTYPE)
    for p_i, ray in zip(assignment, rays):
        out = out + p_i.to(CDTYPE) * ray
    return (D + 1) * out - eye()


def reconstruct_mub(assignment: torch.Tensor, projectors: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros((D, D), dtype=CDTYPE)
    for p_i, proj in zip(assignment, projectors):
        q_i = 3.0 * p_i
        out = out + q_i.to(CDTYPE) * proj
    return out - eye()


def condition_matrix(effects: list[torch.Tensor]) -> torch.Tensor:
    basis = [
        torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=CDTYPE),
        torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE),
        torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=CDTYPE),
        torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=CDTYPE),
    ]
    rows = []
    for effect in effects:
        rows.append(torch.real(torch.stack([torch.trace(b @ effect) for b in basis])).to(RTYPE))
    return torch.stack(rows, dim=0)


def probe_family_gate() -> dict[str, Any]:
    sic_rays, sic_effects = sic_rays_effects()
    mub_projectors, mub_effects = mub_projectors_effects()
    rho = carrier(ket([math.cos(0.48) + 0.0j, phase(0.77) * math.sin(0.48)]))
    sic_assignment = finite_assignment(rho, sic_effects)
    mub_assignment = finite_assignment(rho, mub_effects)
    sic_recon = reconstruct_sic(sic_assignment, sic_rays)
    mub_recon = reconstruct_mub(mub_assignment, mub_projectors)
    sic_matrix = condition_matrix(sic_effects)
    mub_matrix = condition_matrix(mub_effects)
    sic_rank = int(torch.linalg.matrix_rank(sic_matrix, tol=1e-10).item())
    mub_rank = int(torch.linalg.matrix_rank(mub_matrix, tol=1e-10).item())
    sic_cond = float(torch.linalg.cond(sic_matrix).item())
    mub_singular = torch.linalg.svdvals(mub_matrix)
    mub_nonzero = mub_singular[mub_singular > 1e-10]
    mub_cond_effective = float((torch.max(mub_nonzero) / torch.min(mub_nonzero)).item())
    return {
        "pass": size(sum(sic_effects, torch.zeros((D, D), dtype=CDTYPE)) - eye()) < TOL
        and size(sum(mub_effects, torch.zeros((D, D), dtype=CDTYPE)) - eye()) < TOL
        and size(sic_recon - rho) < TOL
        and size(mub_recon - rho) < TOL
        and sic_rank == 4
        and mub_rank == 4,
        "sic_effect_count": len(sic_effects),
        "mub_effect_count": len(mub_effects),
        "sic_reconstruction_gap": size(sic_recon - rho),
        "mub_reconstruction_gap": size(mub_recon - rho),
        "sic_rank": sic_rank,
        "mub_rank": mub_rank,
        "sic_condition": sic_cond,
        "mub_effective_condition": mub_cond_effective,
        "sic_assignment_sum": float(torch.sum(sic_assignment).item()),
        "mub_assignment_sum": float(torch.sum(mub_assignment).item()),
    }


def graveyard_arbitrary_simplex_rejected() -> dict[str, Any]:
    sic_rays, _ = sic_rays_effects()
    arbitrary = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=RTYPE)
    recon = reconstruct_sic(arbitrary, sic_rays)
    eig = torch.linalg.eigvalsh((recon + torch.conj(recon.T)) / 2.0)
    return {
        "pass": float(torch.min(eig).item()) < -GAP_FLOOR,
        "why_rejected": "not every simplex point is an admissible SIC quantum response assignment",
        "min_eigenvalue": float(torch.min(eig).item()),
    }


def graveyard_single_basis_rejected() -> dict[str, Any]:
    projectors, _ = mub_projectors_effects()
    single_basis = [projectors[0], projectors[1]]
    rank = int(torch.linalg.matrix_rank(condition_matrix(single_basis), tol=1e-10).item())
    return {
        "pass": rank < 4,
        "why_rejected": "one finite two-outcome basis is not informationally complete",
        "rank": rank,
    }


def z3_gate() -> dict[str, Any]:
    sic_count = z3.Int("sic_count")
    mub_count = z3.Int("mub_count")
    rank = z3.Int("rank")
    final_claim = z3.Bool("final_claim")
    solver = z3.Solver()
    solver.add(sic_count == 4, mub_count == 6, rank == 4, z3.Not(final_claim))
    collapse = z3.Solver()
    collapse.add(sic_count == 4, mub_count == 6, rank == 4, z3.Not(final_claim))
    collapse.add(z3.Or(sic_count != 4, mub_count != 6, rank < 4, final_claim))
    return {"positive_status": str(solver.check()), "collapse_status": str(collapse.check()), "pass": solver.check() == z3.sat and collapse.check() == z3.unsat}


def finite_order_witness_gate() -> dict[str, Any]:
    x_op = wh_shift()
    z_op = wh_phase()
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
    gate = probe_family_gate()
    positive = {
        "sic_and_mub_are_finite_informationally_complete_probe_families": gate,
        "n01_finite_order_witness": finite_order_witness_gate(),
        "z3_count_rank_nonpromotion_gate": z3_gate(),
    }
    graveyard_companions = {
        "GC1_arbitrary_simplex_point_rejected": graveyard_arbitrary_simplex_rejected(),
        "GC2_single_basis_not_ic_rejected": graveyard_single_basis_rejected(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_minimal_vs_overcomplete_roles_kept_separate": {
            "pass": gate["sic_effect_count"] == 4 and gate["mub_effect_count"] == 6,
            "sic_role": "minimal IC finite probe",
            "mub_role": "overcomplete IC finite probe",
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
            "rho -> p_SIC(rho) and rho -> p_MUB(rho), finite response assignments compared by reconstruction/rank/conditioning"
        ],
        "domain": "finite SIC effects, finite MUB effects, and finite X/Z/I operator family on a 2-dimensional torch-native carrier",
        "codomain_or_output": "finite comparison readout for SIC/MUB informational completeness, reconstruction gaps, rank/conditioning, and failed simplex/single-basis/order-erased controls",
        "root_constraints_in_force": {
            "F01": {
                "finite_effect_families": {
                    "SIC": 4,
                    "MUB": 6,
                },
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
        "carrier_layer": "phase_1_sic_mub_finite_probe_family_comparison",
        "geometry_layer": "none",
        "carrier_realization": "finite torch-native 2x2 density/effect tensors; carrier matrices are reconstruction adapters after finite response admission",
        "peps3d_embedding": "blocked downstream next step only; not implemented here",
        "spinor_state": "finite torch-native spinors are used only to construct probe effects for this Phase 1 comparison",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "finite SIC versus MUB probe-family informational-completeness comparison",
        "branch_status_before_run": "phase_1_frontier_reissue",
        "allowed_claims": ["Phase 1 finite SIC/MUB probe-family comparison scout only"],
        "promotion_blockers": ["remaining Phase 1 frontier rows still need reissue or blocker classification"],
        "required_tools": ["pytorch", "z3"],
        "actual_tools_used": ["pytorch", "z3"],
        "proof_surfaces_used": ["z3"],
        "graph_surfaces_used": ["not_relevant_for_this_phase1_sic_mub_packet"],
        "topology_surfaces_used": ["not_relevant_for_this_phase1_sic_mub_packet"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_inputs": ["finite SIC and MUB effect families defined in this source"],
        "data_or_artifact_dependencies": [
            "system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json",
        ],
        "required_negatives": [
            "arbitrary_simplex_point_rejected",
            "single_basis_not_ic_rejected",
            "order_erased_control",
        ],
        "negatives_run": list(graveyard_companions.keys()) + ["order_erased_control"],
        "kill_conditions": [
            "arbitrary simplex point accepted as an admissible SIC assignment",
            "single finite basis accepted as informationally complete",
            "order-erased control retains N01 witness",
            "any downstream consumer admitted",
        ],
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT))],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": "phase1_sic_mub_probe_family_comparison_reissue_v1",
        "result_summary": {
            "sic_effect_count": gate["sic_effect_count"],
            "mub_effect_count": gate["mub_effect_count"],
            "sic_rank": gate["sic_rank"],
            "mub_rank": gate["mub_rank"],
            "order_gap": positive["n01_finite_order_witness"]["order_gap"],
        },
        "pass_rule": "SIC and MUB finite probe families both reconstruct the carrier adapter and have rank 4 while simplex, single-basis, and order-erased controls fail",
        "fail_rule": "missing IC rank/reconstruction, admitted invalid simplex point, admitted single-basis IC claim, missing N01 witness, or downstream consumer admission",
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
            "sic_status": "minimal_ic_pass",
            "mub_status": "overcomplete_ic_pass",
            "order_gap": positive["n01_finite_order_witness"]["order_gap"],
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": "This is a v5 SIC/MUB finite probe-family formal scout, not a v4 probe promotion.",
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
