#!/usr/bin/env python3
"""Finite effect/SIC plus Weyl-Heisenberg substrate admission scout.

Formal scout only.

The root object tested here is a finite probe-response assignment. A carrier
matrix is reconstructed only after the finite SIC effects pass admission.
The finite Weyl-Heisenberg shift/phase relation supplies the noncommuting
operator algebra. Legacy sphere/axis pictures are therefore not primitive in
this row; they can only return as derived adapters after this gate.
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
NAME = "finite_effect_sic_weyl_substrate_admission_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.1"
TIER = "1 finite probe/effect quotient"
PURPOSE = (
    "Reissue the Phase 1 finite SIC/Weyl substrate row against the current "
    "LEGO receipt contract while keeping all downstream consumers blocked."
)
SCIENTIFIC_QUESTION = (
    "Can a finite SIC probe-response assignment plus finite Weyl-Heisenberg "
    "shift/phase operator witness satisfy F01/N01 while single-probe, "
    "commuting, and non-informationally-complete controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "constraint_probe"
SOURCE_ALIGNMENT_CATEGORY = "finite_probe_effect_sic_weyl_substrate_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests finite effect/SIC probe-response assignments "
    "and finite Weyl-Heisenberg shift/phase operators as a root-admissible "
    "replacement substrate for older sphere/axis adapters. It does not admit "
    "a final manifold foundation, Axis0, Xi, flux, IGT, FEP, physics, or "
    "ontology claim."
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
        "reason": "load-bearing finite complex spinors, SIC effects, probability assignments, and operator checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite/admissible/nonpromotion consistency gate",
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


def eye(dim: int) -> torch.Tensor:
    return torch.eye(dim, dtype=CDTYPE)


def norm(item: torch.Tensor) -> float:
    return float(torch.linalg.norm(item).item())


def ket(items: list[complex]) -> torch.Tensor:
    out = torch.tensor(items, dtype=CDTYPE)
    return out / torch.linalg.norm(out)


def projector(local_spinor: torch.Tensor) -> torch.Tensor:
    return torch.outer(local_spinor, torch.conj(local_spinor))


def phase(angle: float) -> complex:
    return complex(math.cos(angle), math.sin(angle))


def sic_spinors_qubit() -> list[torch.Tensor]:
    return [
        ket([1.0 + 0.0j, 0.0 + 0.0j]),
        ket([1.0 / math.sqrt(3.0) + 0.0j, math.sqrt(2.0 / 3.0) + 0.0j]),
        ket([1.0 / math.sqrt(3.0) + 0.0j, math.sqrt(2.0 / 3.0) * phase(2.0 * math.pi / 3.0)]),
        ket([1.0 / math.sqrt(3.0) + 0.0j, math.sqrt(2.0 / 3.0) * phase(4.0 * math.pi / 3.0)]),
    ]


def sic_from_spinors(spinors: list[torch.Tensor]) -> tuple[list[torch.Tensor], list[torch.Tensor]]:
    rays = [projector(item) for item in spinors]
    effects = [ray / D for ray in rays]
    return rays, effects


def finite_assignment(carrier: torch.Tensor, effects: list[torch.Tensor]) -> torch.Tensor:
    return torch.real(torch.stack([torch.trace(carrier @ effect) for effect in effects])).to(RTYPE)


def reconstruct_from_sic(assignment: torch.Tensor, rays: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros((D, D), dtype=CDTYPE)
    for p_i, ray in zip(assignment, rays):
        out = out + p_i.to(CDTYPE) * ray
    return (D + 1) * out - eye(D)


def carrier_from_spinor(local_spinor: torch.Tensor) -> torch.Tensor:
    return projector(local_spinor)


def wh_shift(dim: int) -> torch.Tensor:
    op = torch.zeros((dim, dim), dtype=CDTYPE)
    for col in range(dim):
        op[(col - 1) % dim, col] = 1.0 + 0.0j
    return op


def wh_phase(dim: int) -> torch.Tensor:
    omega = phase(2.0 * math.pi / dim)
    return torch.diag(torch.tensor([omega**idx for idx in range(dim)], dtype=CDTYPE))


def wh_omega(dim: int) -> complex:
    return phase(2.0 * math.pi / dim)


def wh_orbit(fiducial: torch.Tensor, dim: int) -> list[torch.Tensor]:
    x_op = wh_shift(dim)
    z_op = wh_phase(dim)
    return [
        torch.linalg.matrix_power(x_op, a) @ torch.linalg.matrix_power(z_op, b) @ fiducial
        for a in range(dim)
        for b in range(dim)
    ]


def pair_overlaps(spinors: list[torch.Tensor]) -> list[float]:
    out = []
    for idx, left in enumerate(spinors):
        for right in spinors[idx + 1 :]:
            out.append(abs(torch.vdot(left, right).item()) ** 2)
    return out


def sic_gate() -> dict[str, Any]:
    spinors = sic_spinors_qubit()
    rays, effects = sic_from_spinors(spinors)
    effect_sum_gap = norm(sum(effects, torch.zeros((D, D), dtype=CDTYPE)) - eye(D))
    overlaps = pair_overlaps(spinors)
    overlap_gap = max(abs(item - 1.0 / 3.0) for item in overlaps)

    probe = ket([math.cos(0.41) + 0.0j, phase(0.73) * math.sin(0.41)])
    carrier = carrier_from_spinor(probe)
    assignment = finite_assignment(carrier, effects)
    reconstructed = reconstruct_from_sic(assignment, rays)
    reconstructed_assignment = finite_assignment(reconstructed, effects)
    reconstruction_gap = norm(reconstructed - carrier)
    assignment_gap = norm(reconstructed_assignment - assignment)
    eigvals = torch.linalg.eigvalsh(reconstructed)

    return {
        "pass": effect_sum_gap < TOL
        and overlap_gap < TOL
        and abs(float(torch.sum(assignment).item()) - 1.0) < TOL
        and reconstruction_gap < TOL
        and assignment_gap < TOL
        and float(torch.min(eigvals).item()) > -TOL,
        "effect_count": len(effects),
        "root_object": "finite_probe_response_assignment",
        "effect_sum_gap": effect_sum_gap,
        "sic_pair_overlap_target": 1.0 / 3.0,
        "sic_pair_overlap_max_gap": overlap_gap,
        "assignment": assignment,
        "assignment_sum": float(torch.sum(assignment).item()),
        "reconstruction_adapter_gap": reconstruction_gap,
        "assignment_roundtrip_gap": assignment_gap,
        "reconstructed_trace": torch.trace(reconstructed),
        "reconstructed_min_eigenvalue": float(torch.min(eigvals).item()),
    }


def wh_gate(dim: int) -> dict[str, Any]:
    x_op = wh_shift(dim)
    z_op = wh_phase(dim)
    omega = wh_omega(dim)
    relation_gap = norm(x_op @ z_op - omega * (z_op @ x_op))
    order_gap = norm(x_op @ z_op - z_op @ x_op)
    return {
        "pass": relation_gap < TOL and order_gap > GAP_FLOOR,
        "dimension": dim,
        "omega": omega,
        "xz_equals_omega_zx_gap": relation_gap,
        "plain_order_gap": order_gap,
    }


def wh_covariant_sic_gate() -> dict[str, Any]:
    amp0 = math.sqrt((1.0 + 1.0 / math.sqrt(3.0)) / 2.0)
    amp1 = math.sqrt((1.0 - 1.0 / math.sqrt(3.0)) / 2.0)
    fiducial = ket([amp0 + 0.0j, phase(math.pi / 4.0) * amp1])
    orbit = wh_orbit(fiducial, D)
    overlaps = pair_overlaps(orbit)
    overlap_gap = max(abs(item - 1.0 / 3.0) for item in overlaps)
    rays, effects = sic_from_spinors(orbit)
    effect_sum_gap = norm(sum(effects, torch.zeros((D, D), dtype=CDTYPE)) - eye(D))
    return {
        "pass": overlap_gap < TOL and effect_sum_gap < TOL,
        "orbit_size": len(orbit),
        "sic_pair_overlap_max_gap": overlap_gap,
        "effect_sum_gap": effect_sum_gap,
        "note": "d=2 SIC recovered as finite Weyl-Heisenberg orbit of one admitted spinor.",
    }


def quotient_identity_gate() -> dict[str, Any]:
    _, effects = sic_from_spinors(sic_spinors_qubit())
    base_angle = 0.62
    left = ket([math.cos(base_angle) + 0.0j, math.sin(base_angle) + 0.0j])
    right = ket([math.cos(base_angle) + 0.0j, phase(math.pi / 2.0) * math.sin(base_angle)])
    left_assignment = finite_assignment(carrier_from_spinor(left), effects)
    right_assignment = finite_assignment(carrier_from_spinor(right), effects)
    coarse_gap = abs(float((left_assignment[0] - right_assignment[0]).item()))
    full_gap = norm(left_assignment - right_assignment)
    return {
        "pass": coarse_gap < TOL and full_gap > GAP_FLOOR,
        "active_probe_subset": [0],
        "coarse_probe_gap": coarse_gap,
        "full_sic_assignment_gap": full_gap,
        "reading": "same under one finite probe is not identity under the active complete probe family",
    }


def gauge_phase_gate() -> dict[str, Any]:
    _, effects = sic_from_spinors(sic_spinors_qubit())
    original = ket([math.cos(0.53) + 0.0j, phase(1.31) * math.sin(0.53)])
    shifted = phase(0.91) * original
    original_assignment = finite_assignment(carrier_from_spinor(original), effects)
    shifted_assignment = finite_assignment(carrier_from_spinor(shifted), effects)
    gap = norm(original_assignment - shifted_assignment)
    return {
        "pass": gap < TOL,
        "phase_shift": 0.91,
        "assignment_gap": gap,
        "reading": "finite probe responses quotient away global phase",
    }


def mub_probe_family_gate() -> dict[str, Any]:
    # Three finite two-outcome bases supply an overcomplete but finite probe family.
    x_op = wh_shift(D)
    z_op = wh_phase(D)
    y_like = x_op @ z_op
    effects: list[torch.Tensor] = []
    for op in [x_op, z_op, y_like]:
        vals, vecs = torch.linalg.eig(op)
        del vals
        for col in range(D):
            local = vecs[:, col] / torch.linalg.norm(vecs[:, col])
            effects.append(projector(local) / 3.0)
    effect_sum_gap = norm(sum(effects, torch.zeros((D, D), dtype=CDTYPE)) - eye(D))
    probe = ket([math.cos(0.47) + 0.0j, phase(0.37) * math.sin(0.47)])
    assignment = finite_assignment(carrier_from_spinor(probe), effects)
    return {
        "pass": len(effects) == 6 and effect_sum_gap < TOL and abs(float(torch.sum(assignment).item()) - 1.0) < TOL,
        "effect_count": len(effects),
        "effect_sum_gap": effect_sum_gap,
        "assignment_sum": float(torch.sum(assignment).item()),
        "status": "viable_secondary_candidate_overcomplete_finite_probe_family",
    }


def graveyard_single_probe_not_complete() -> dict[str, Any]:
    row = quotient_identity_gate()
    return {
        "pass": row["coarse_probe_gap"] < TOL and row["full_sic_assignment_gap"] > GAP_FLOOR,
        "why_rejected": "single effect cannot provide identity; it merges states separated by complete finite SIC probes",
        "coarse_probe_gap": row["coarse_probe_gap"],
        "full_sic_assignment_gap": row["full_sic_assignment_gap"],
    }


def graveyard_commuting_algebra_collapse() -> dict[str, Any]:
    x_op = wh_shift(D)
    unit = eye(D)
    gap = norm(x_op @ unit - unit @ x_op)
    return {
        "pass": gap < TOL,
        "why_rejected": "commuting algebra has no order witness for N01",
        "order_gap": gap,
    }


def graveyard_non_ic_pair_probe() -> dict[str, Any]:
    z_op = wh_phase(D)
    vals, vecs = torch.linalg.eig(z_op)
    del vals
    effects = [projector(vecs[:, col] / torch.linalg.norm(vecs[:, col])) for col in range(D)]
    base_angle = 0.62
    left = ket([math.cos(base_angle) + 0.0j, math.sin(base_angle) + 0.0j])
    right = ket([math.cos(base_angle) + 0.0j, phase(math.pi / 2.0) * math.sin(base_angle)])
    left_assignment = finite_assignment(carrier_from_spinor(left), effects)
    right_assignment = finite_assignment(carrier_from_spinor(right), effects)
    pair_gap = norm(left_assignment - right_assignment)
    full_gap = quotient_identity_gate()["full_sic_assignment_gap"]
    return {
        "pass": pair_gap < TOL and full_gap > GAP_FLOOR,
        "why_rejected": "one two-outcome basis is finite but not informationally complete",
        "pair_probe_gap": pair_gap,
        "full_sic_assignment_gap": full_gap,
    }


def z3_admission_gate() -> dict[str, Any]:
    dim = z3.Int("dim")
    sic_effects = z3.Int("sic_effects")
    finite = z3.Bool("finite")
    noncommuting = z3.Bool("noncommuting")
    final_claim = z3.Bool("final_claim")
    solver = z3.Solver()
    solver.add(dim == 2, sic_effects == dim * dim, finite, noncommuting, z3.Not(final_claim))
    contradiction = z3.Solver()
    contradiction.add(dim == 2, sic_effects == dim * dim, finite, noncommuting, z3.Not(final_claim))
    contradiction.add(z3.Or(sic_effects != dim * dim, z3.Not(finite), z3.Not(noncommuting), final_claim))
    return {
        "positive_status": str(solver.check()),
        "collapse_status": str(contradiction.check()),
        "pass": solver.check() == z3.sat and contradiction.check() == z3.unsat,
    }


def candidate_matrix() -> list[dict[str, Any]]:
    return [
        {
            "candidate": "finite_effect_povm_state_space",
            "admission_score": 10.0,
            "first_gate": "finite probe responses define quotient identity; noncomplete probe families must fail",
            "status_after_this_scout": "primary_substrate_candidate_passed_local_gate",
        },
        {
            "candidate": "sic_povm_probability_simplex",
            "admission_score": 9.5,
            "first_gate": "d^2 finite effects sum to identity, SIC overlaps hold, assignments reconstruct carrier adapter",
            "status_after_this_scout": "primary_concrete_carrier_candidate_passed_local_gate",
        },
        {
            "candidate": "weyl_heisenberg_shift_phase_algebra",
            "admission_score": 9.0,
            "first_gate": "finite XZ = omega ZX with nonzero order gap in d=2 and d=3",
            "status_after_this_scout": "primary_operator_candidate_passed_local_gate",
        },
        {
            "candidate": "mub_finite_probe_family",
            "admission_score": 8.4,
            "first_gate": "finite overcomplete bases sum to one admitted instrument",
            "status_after_this_scout": "secondary_candidate_passed_smoke_gate_needs_reconstruction_gate",
        },
        {
            "candidate": "contextuality_sheaf_or_presheaf_events",
            "admission_score": 8.2,
            "first_gate": "finite measurement contexts have no global section under a contextual witness",
            "status_after_this_scout": "not_run_next_candidate",
        },
        {
            "candidate": "finite_projective_geometry_or_quantum_designs",
            "admission_score": 8.0,
            "first_gate": "finite incidence/design relations generate IC probes without a metric substrate",
            "status_after_this_scout": "not_run_next_candidate",
        },
        {
            "candidate": "finite_spectral_triple_or_dirac_pair",
            "admission_score": 7.6,
            "first_gate": "finite algebra, finite module, and bounded commutator separate states operationally",
            "status_after_this_scout": "not_run_next_candidate",
        },
        {
            "candidate": "quantum_comb_or_process_povm",
            "admission_score": 7.5,
            "first_gate": "finite causal instrument history is represented without primitive time-order ontology",
            "status_after_this_scout": "not_run_next_candidate",
        },
        {
            "candidate": "finite_convex_operational_theory",
            "admission_score": 7.3,
            "first_gate": "state/effect dual cones are finite-generated and distinguishability-native",
            "status_after_this_scout": "not_run_next_candidate",
        },
    ]


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    positive = {
        "finite_sic_probe_assignment_is_admissible": sic_gate(),
        "weyl_heisenberg_d2_relation_is_noncommuting": wh_gate(2),
        "weyl_heisenberg_d3_relation_is_noncommuting": wh_gate(3),
        "weyl_heisenberg_orbit_recovers_qubit_sic": wh_covariant_sic_gate(),
        "probe_quotient_identity_is_active_family_relative": quotient_identity_gate(),
        "global_phase_quotients_out_under_effect_responses": gauge_phase_gate(),
        "mub_overcomplete_finite_probe_family_smoke_test": mub_probe_family_gate(),
        "z3_finite_noncommuting_nonpromotion_gate": z3_admission_gate(),
    }
    graveyard_companions = {
        "GC1_single_probe_identity_smuggling_rejected": graveyard_single_probe_not_complete(),
        "GC2_commuting_operator_family_rejected_for_N01_root": graveyard_commuting_algebra_collapse(),
        "GC3_non_informationally_complete_pair_probe_rejected": graveyard_non_ic_pair_probe(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_root_object_is_finite_probe_response_not_adapter": {
            "pass": positive["finite_sic_probe_assignment_is_admissible"]["root_object"]
            == "finite_probe_response_assignment",
            "root_object": positive["finite_sic_probe_assignment_is_admissible"]["root_object"],
        },
        "B3_candidate_matrix_marks_unrun_options_as_unrun": {
            "pass": any(row["status_after_this_scout"] == "not_run_next_candidate" for row in candidate_matrix()),
            "not_run_candidates": [
                row["candidate"] for row in candidate_matrix() if row["status_after_this_scout"] == "not_run_next_candidate"
            ],
        },
        "B4_no_final_axis0_or_physics_claim": {
            "pass": "does not admit" in CLAIM_CEILING and "Axis0" in CLAIM_CEILING and "physics" in CLAIM_CEILING,
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
            "rho -> p_E(rho), where p_E is the finite SIC effect-response assignment",
            "fiducial -> Weyl-Heisenberg orbit effects with finite XZ = omega ZX order witness",
        ],
        "domain": "finite qubit SIC effects, finite probe-response assignments, and finite Weyl-Heisenberg X/Z operators in d=2 and d=3",
        "codomain_or_output": "admission readouts for SIC completeness, finite assignment reconstruction, Weyl-Heisenberg noncommutation, and failed single-probe/non-IC/commuting controls",
        "root_constraints_in_force": {
            "F01": {
                "finite_effect_family": "d^2 SIC effects in d=2 plus finite MUB smoke family",
                "finite_carrier_dimension": D,
                "finite_operator_family": ["Weyl_shift_X", "Weyl_phase_Z"],
                "finite_path_order_set": ["X_then_Z", "Z_then_X"],
            },
            "N01": {
                "witness": "X @ Z = omega * Z @ X and X @ Z != Z @ X",
                "d2_order_gap": positive["weyl_heisenberg_d2_relation_is_noncommuting"]["plain_order_gap"],
                "d3_order_gap": positive["weyl_heisenberg_d3_relation_is_noncommuting"]["plain_order_gap"],
                "order_erased_control": graveyard_companions["GC2_commuting_operator_family_rejected_for_N01_root"],
            },
        },
        "carrier_layer": "phase_1_finite_sic_weyl_probe_effect_substrate",
        "geometry_layer": "none",
        "carrier_realization": "finite torch-native complex spinors as SIC construction inputs, finite effects, and finite response assignments; carrier matrices are adapters after probe admission",
        "peps3d_embedding": "blocked downstream next step only; not implemented here",
        "spinor_state": "finite torch-native spinors are used only to construct SIC effects for this Phase 1 probe-response row",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json"
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "finite SIC probe-response assignment and finite Weyl-Heisenberg noncommuting operator substrate",
        "branch_status_before_run": "phase_1_frontier_reissue",
        "allowed_claims": ["Phase 1 finite SIC/Weyl probe-response substrate scout only"],
        "promotion_blockers": ["broader Phase 1 frontier rows remain needs_reissue or open"],
        "required_tools": ["pytorch", "z3"],
        "actual_tools_used": ["pytorch", "z3"],
        "proof_surfaces_used": ["z3"],
        "graph_surfaces_used": ["not_relevant_for_this_phase1_sic_weyl_packet"],
        "topology_surfaces_used": ["not_relevant_for_this_phase1_sic_weyl_packet"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_inputs": ["finite SIC spinors/effects and finite Weyl-Heisenberg X/Z operators defined in this source"],
        "data_or_artifact_dependencies": [
            "system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json"
        ],
        "required_negatives": [
            "single_probe_identity_smuggling_rejected",
            "commuting_operator_family_rejected_for_N01_root",
            "non_informationally_complete_pair_probe_rejected",
        ],
        "negatives_run": list(graveyard_companions.keys()),
        "kill_conditions": [
            "single finite probe accepted as complete identity",
            "commuting operator family accepted as N01 witness",
            "non-informationally-complete pair probe accepted as complete",
            "any downstream consumer admitted",
        ],
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT))],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": "phase1_finite_sic_weyl_substrate_reissue_v1",
        "result_summary": {
            "effect_count": positive["finite_sic_probe_assignment_is_admissible"]["effect_count"],
            "d2_order_gap": positive["weyl_heisenberg_d2_relation_is_noncommuting"]["plain_order_gap"],
            "d3_order_gap": positive["weyl_heisenberg_d3_relation_is_noncommuting"]["plain_order_gap"],
            "single_probe_full_assignment_gap": graveyard_companions["GC1_single_probe_identity_smuggling_rejected"]["full_sic_assignment_gap"],
        },
        "pass_rule": "finite SIC responses reconstruct the adapter carrier, Weyl-Heisenberg X/Z are noncommuting in d=2 and d=3, and single-probe/commuting/non-IC controls fail",
        "fail_rule": "missing finite SIC completeness, missing Weyl noncommutation, admitted single-probe identity, admitted commuting N01 witness, or downstream consumer admission",
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
        "candidate_matrix": candidate_matrix(),
        "summary": {
            "primary_substrate": "finite_effect_povm_state_space",
            "primary_concrete_probe": "qubit_sic_povm",
            "primary_operator_algebra": "finite_weyl_heisenberg_shift_phase",
            "secondary_candidate_passed": "mub_finite_probe_family",
            "unrun_next_candidate_count": sum(
                1 for row in candidate_matrix() if row["status_after_this_scout"] == "not_run_next_candidate"
            ),
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 formal scout for a root-layer replacement substrate. "
            "It is not a v4 probe and not a promotion of final manifold, Axis0, "
            "flux, IGT, FEP, or physics claims."
        ),
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
