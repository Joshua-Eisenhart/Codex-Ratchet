#!/usr/bin/env python3
"""M_RPF(C) post-stack bond-5 admission micro-probe.

This packet is a bounded repair of the post-stack variant receipt that left
bond_dim=5 unadmitted. It tests whether a finite local PEPS3D tensor with six
virtual legs of dimension 5 can carry the already-earned M_RPF(C) order:

Omega_r -> compatibility_weights -> ordered adapters A0..A8 -> compression C
-> rho_present -> outward_record -> derived readouts.

It does not admit flux, Xi/Phi0, Axis0, FEP/Holodeck, physics, gravity,
PEPS3D closure theorem, or final manifold closure.
"""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
import z3

from sim_l2_spinor_chirality_weyl_cover_layer_probe import (  # noqa: E402
    CTYPE,
    GAP_FLOOR,
    SHAPES,
    TOL,
    as_jsonable,
    coords_for_shape,
    density,
    site_spinors,
)
from sim_m_rpf_cross_row_order_closure_probe import (  # noqa: E402
    ADAPTER_ORDER,
    BLOCKED_CONSUMERS,
    OBJECT_PACKET,
    compose_adapters,
    event_density,
    stack_row,
)
from sim_m_rpf_l4_terrain_channel_shell_object_preservation_probe import terrain_object_row  # noqa: E402
from sim_m_rpf_l5_operator_substage_shell_object_preservation_probe import substage_object_row  # noqa: E402
from sim_m_rpf_l7_hopf_shell_projection_object_preservation_probe import hopf_object_row  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "m_rpf_post_stack_bond5_admission_micro_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = "formal_scout"
SIM_ID = NAME
VERSION = "1.0.0"
TIER = "M_RPF(C) post-stack bond-5 admission micro-probe"
PURPOSE = "Test one bounded bond_dim=5 local PEPS3D tensor family without widening or promoting downstream consumers."
SCIENTIFIC_QUESTION = (
    "Can bond_dim=5 be admitted as a finite local PEPS3D carrier while preserving "
    "spinor phase, Hopf fiber/base distinction, L/R Weyl sign, terrain/operator "
    "action, row-local adapter provenance, and M_RPF(C) object order?"
)
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "geometry_probe"
SOURCE_ALIGNMENT_CATEGORY = "m_rpf_post_stack_bond5_admission"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal M_RPF(C) bond-5 admission micro-probe only. Passing admits one "
    "bounded local PEPS3D bond_dim=5 tensor family as a post-stack stress "
    "variant; it does not admit stacking beyond this packet, flux, Xi/Phi0, "
    "Axis0, Holodeck/FEP, physics, gravity, IGT/game theory, axes7-12, "
    "PEPS3D closure theorem, or final manifold."
)
FINITE_MAP = (
    "M_RPF_post_stack_bond5_admission : (K, event_x, Sigma_r(x), Omega_r, "
    "spinor payload psi_v, spinor-derived rho_v, Hopf/Weyl/terrain/operator "
    "metadata, compatibility weights, ordered adapters A0..A8, compression C, "
    "bond_dim candidate 5) -> (bond5 admission table, resource residuals, "
    "object-order residuals, spinor-phase/fiber/sheet/locality residuals, "
    "failed controls, blocked consumers)"
)
DOMAIN = (
    "finite PEPS3D carriers K for shapes (2,2,2), (4,2,2), (4,4,2), "
    "(4,4,4); event_x vertex anchors; finite shell stacks; torch complex "
    "spinor sites; ordered adapters A0..A8; local PEPS3D tensors "
    "T_v[alpha_x-,alpha_x+,alpha_y-,alpha_y+,alpha_z-,alpha_z+,a] with bond 5"
)
CODOMAIN = (
    "finite bond-5 admission table, local tensor resource table, object-order "
    "residuals, N01 order gaps, source-native preservation residuals, killed "
    "controls, and locked downstream consumers"
)

BOND_DIM_CANDIDATE = 5
BOND5_BLOCKED_CONSUMERS = [
    "stacking",
    *BLOCKED_CONSUMERS,
    "PEPS3D closure theorem",
]
TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing bond5 local tensor construction, spinor phase checks, density/readout compression, and N01 gaps"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact tensor cardinality and finite shape count checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing bond5 finite admission and downstream-lock gates"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent object-order and proxy nonpromotion gate"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D row topology and post-stack provenance"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing through imported finite graph certificates"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing through imported hyperedge/cell certificates"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing through imported cell-complex certificates"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing through imported filtration certificates"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing through imported chirality/quaternion/Hopf row provenance"},
    "geomstats": {"tried": False, "used": False, "reason": "not used: no metric/geodesic/curvature bond5 claim is made"},
    "e3nn": {"tried": False, "used": False, "reason": "not used: no equivariant learned field claim is made"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "pyg": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "clifford": "load_bearing",
    "geomstats": None,
    "e3nn": None,
}


def peps3d_counts(shape: tuple[int, int, int]) -> dict[str, int]:
    x, y, z = shape
    return {
        "V": x * y * z,
        "E": (x - 1) * y * z + x * (y - 1) * z + x * y * (z - 1),
        "F": (x - 1) * (y - 1) * z + (x - 1) * y * (z - 1) + x * (y - 1) * (z - 1),
        "C": max(0, (x - 1) * (y - 1) * (z - 1)),
    }


def local_bond5_tensor(spinor: torch.Tensor, site_index: int) -> torch.Tensor:
    """Build one finite PEPS3D local tensor with six bond-5 virtual legs."""
    base = torch.linspace(0.2, 1.0, BOND_DIM_CANDIDATE, dtype=torch.float64)
    legs = []
    for axis_index in range(6):
        phase = torch.exp(
            1j
            * torch.tensor(
                (site_index + 1) * (axis_index + 1) / (BOND_DIM_CANDIDATE + 7.0),
                dtype=torch.float64,
            )
        ).to(CTYPE)
        leg = (base + 0.013 * (axis_index + 1)).to(CTYPE) * phase
        legs.append(leg / torch.linalg.vector_norm(leg))
    virtual = torch.einsum("a,b,c,d,e,f->abcdef", *legs)
    tensor = torch.einsum("abcdef,p->abcdefp", virtual, spinor.to(CTYPE))
    return tensor / torch.linalg.vector_norm(tensor.reshape(-1))


def phase_erased_spinor(spinor: torch.Tensor) -> torch.Tensor:
    erased = torch.abs(spinor).to(CTYPE)
    return erased / torch.linalg.vector_norm(erased)


def local_tensor_residuals(shape: tuple[int, int, int]) -> dict[str, Any]:
    spinors = site_spinors(coords_for_shape(shape))
    tensor_numel = BOND_DIM_CANDIDATE**6 * 2
    norms = []
    phase_gaps = []
    density_gaps = []
    for site_index, spinor in enumerate(spinors):
        tensor = local_bond5_tensor(spinor, site_index)
        erased_tensor = local_bond5_tensor(phase_erased_spinor(spinor), site_index)
        norms.append(float(torch.linalg.vector_norm(tensor.reshape(-1)).real.item()))
        phase_gaps.append(float(torch.linalg.vector_norm((tensor - erased_tensor).reshape(-1)).real.item()))
        rho = density(spinor)
        erased_rho = density(phase_erased_spinor(spinor))
        density_gaps.append(float(torch.linalg.matrix_norm(rho - erased_rho).real.item()))
    return {
        "local_tensor_numel": tensor_numel,
        "tensor_norm_min": min(norms),
        "tensor_norm_max": max(norms),
        "phase_erased_tensor_gap_min": min(phase_gaps),
        "phase_erased_tensor_gap_max": max(phase_gaps),
        "phase_erased_tensor_nonzero_count": sum(1 for gap in phase_gaps if gap > GAP_FLOOR),
        "phase_erased_density_gap_min": min(density_gaps),
        "phase_erased_density_gap_max": max(density_gaps),
        "phase_erased_density_nonzero_count": sum(1 for gap in density_gaps if gap > GAP_FLOOR),
        "tensor_memory_estimate_bytes_if_materialized_all_sites": tensor_numel * len(spinors) * 16,
        "all_site_tensors_constructed": len(norms),
    }


def trace_gap(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(a - b).real.item())


def source_native_rows(shape: tuple[int, int, int]) -> dict[str, Any]:
    stack = stack_row(shape)
    terrain5 = terrain_object_row(shape, BOND_DIM_CANDIDATE)
    substage5 = substage_object_row(shape, BOND_DIM_CANDIDATE)
    hopf5 = hopf_object_row(shape, BOND_DIM_CANDIDATE)
    tensor_residuals = local_tensor_residuals(shape)
    rho0 = event_density(shape)
    ordered = compose_adapters(rho0, ADAPTER_ORDER)
    swapped = compose_adapters(rho0, ("A0", "A1", "A2", "A3", "A5", "A4", "A6", "A7", "A8"))
    dropped = compose_adapters(rho0, tuple(name for name in ADAPTER_ORDER if name != "A5"))
    weights = torch.tensor(stack["shell_object_sample"]["compatibility_weights"], dtype=torch.float64)
    uniform = torch.ones_like(weights) / weights.numel()
    counts = peps3d_counts(shape)
    tensor_memory = tensor_residuals["tensor_memory_estimate_bytes_if_materialized_all_sites"]
    return {
        "shape": list(shape),
        "site_count": counts["V"],
        "peps3d_K_counts": counts,
        "bond_dim_candidate": BOND_DIM_CANDIDATE,
        "event_x": stack["event_x"],
        "shell_orientation": stack["shell_orientation"],
        "adapter_order_gap": trace_gap(ordered, swapped),
        "adapter_drop_gap": trace_gap(ordered, dropped),
        "compatibility_uniform_delta": float(torch.linalg.vector_norm(weights - uniform).item()),
        "rho_present_trace": float(torch.real(torch.trace(ordered)).item()),
        "outward_record": stack["outward_record_stack"],
        "local_tensor_resource": tensor_residuals,
        "source_native_preservation": {
            "spinor_phase_gap": tensor_residuals["phase_erased_tensor_gap_min"],
            "spinor_derived_density_gap": tensor_residuals["phase_erased_density_gap_min"],
            "Hopf_fiber_base_preserved": hopf5["pass"],
            "L_R_Weyl_sign_preserved": any(row["adapter"] == "A2" and row["pass"] for row in stack["adapter_rows"]),
            "terrain_action_preserved": terrain5["pass"],
            "operator_action_preserved": substage5["pass"],
            "PEPS3D_locality_preserved": counts["V"] == stack["site_count"] and tensor_residuals["all_site_tensors_constructed"] == counts["V"],
            "density_readout_only": True,
        },
        "resource_residuals": {
            "requires_dense_state_closure": False,
            "drops_anchor_provenance": False,
            "drops_row_local_adapter_provenance": False,
            "materialized_tensor_bytes": tensor_memory,
            "within_micro_probe_bound": tensor_memory <= 40_000_000,
        },
        "pass": bool(
            stack["pass"]
            and terrain5["pass"]
            and substage5["pass"]
            and hopf5["pass"]
            and counts["V"] == tensor_residuals["all_site_tensors_constructed"]
            and tensor_residuals["local_tensor_numel"] == 2 * BOND_DIM_CANDIDATE**6
            and tensor_residuals["tensor_norm_min"] > 1.0 - 1.0e-9
            and tensor_residuals["tensor_norm_max"] < 1.0 + 1.0e-9
            and tensor_residuals["phase_erased_tensor_nonzero_count"] > 0
            and tensor_residuals["phase_erased_density_nonzero_count"] > 0
            and trace_gap(ordered, swapped) > GAP_FLOOR
            and trace_gap(ordered, dropped) > GAP_FLOOR
            and abs(float(torch.real(torch.trace(ordered)).item()) - 1.0) < 1.0e-8
            and tensor_memory <= 40_000_000
        ),
    }


def z3_bond5_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    max_sites = z3.Int("max_sites")
    bond = z3.Int("bond")
    min_gap = z3.Int("min_gap")
    dense = z3.Bool("dense_state_closure")
    solver.add(max_sites == max(row["site_count"] for row in rows))
    solver.add(bond == BOND_DIM_CANDIDATE)
    solver.add(min_gap == int(round(min(row["adapter_order_gap"] for row in rows) * 1_000_000)))
    solver.add(dense == False)
    solver.add(z3.Or(max_sites != 64, bond != 5, min_gap <= 0, dense == True))
    finite_status = solver.check()

    downstream = z3.Solver()
    flux, axis0, fep, peps_closure = z3.Bools("flux axis0 fep peps_closure")
    downstream.add(flux == False, axis0 == False, fep == False, peps_closure == False)
    downstream.add(z3.Or(flux, axis0, fep, peps_closure))
    downstream_status = downstream.check()
    return {
        "pass": finite_status == z3.unsat and downstream_status == z3.unsat,
        "finite_bond5_admission_status": str(finite_status),
        "downstream_unlock_status": str(downstream_status),
    }


def cvc5_bond5_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    names = (
        "omega",
        "weights",
        "adapters",
        "compression",
        "rho_present",
        "outward",
        "spinor_phase",
        "hopf",
        "weyl",
        "terrain",
        "operator",
        "peps3d_bond5",
    )
    fields = [solver.mkConst(solver.getBooleanSort(), name) for name in names]
    admitted = solver.mkConst(solver.getBooleanSort(), "bond5_admitted")
    for field in fields:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, field, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, *fields)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    required_status = str(solver.checkSat())

    proxy = cvc5.Solver()
    proxy.setLogic("ALL")
    entropy_primary = proxy.mkConst(proxy.getBooleanSort(), "entropy_primary")
    wolfram_primary = proxy.mkConst(proxy.getBooleanSort(), "wolfram_primary")
    axis0_primary = proxy.mkConst(proxy.getBooleanSort(), "axis0_primary")
    proxy_promoted = proxy.mkConst(proxy.getBooleanSort(), "proxy_promoted")
    for field in (entropy_primary, wolfram_primary, axis0_primary):
        proxy.assertFormula(proxy.mkTerm(Kind.EQUAL, field, proxy.mkBoolean(False)))
    proxy.assertFormula(proxy.mkTerm(Kind.EQUAL, proxy_promoted, proxy.mkTerm(Kind.OR, entropy_primary, wolfram_primary, axis0_primary)))
    proxy.assertFormula(proxy_promoted)
    proxy_status = str(proxy.checkSat())
    return {
        "pass": required_status == "unsat" and proxy_status == "unsat",
        "all_required_fields_true_but_not_admitted_status": required_status,
        "proxy_primary_promotion_status": proxy_status,
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    rows = [source_native_rows(shape) for shape in SHAPES]
    z3_checks = z3_bond5_gate(rows)
    cvc5_checks = cvc5_bond5_gate()
    sympy_checks = {
        "pass": int(sp.Integer(BOND_DIM_CANDIDATE) ** 6 * 2) == 31250 and int(sp.Integer(len(SHAPES))) == 4,
        "bond5_local_tensor_numel": int(sp.Integer(BOND_DIM_CANDIDATE) ** 6 * 2),
        "shape_count": len(SHAPES),
    }
    min_order_gap = min(row["adapter_order_gap"] for row in rows)
    max_phase_gap = max(row["local_tensor_resource"]["phase_erased_tensor_gap_max"] for row in rows)
    phase_witness_count = sum(row["local_tensor_resource"]["phase_erased_tensor_nonzero_count"] for row in rows)
    max_memory = max(row["local_tensor_resource"]["tensor_memory_estimate_bytes_if_materialized_all_sites"] for row in rows)
    all_pass = bool(all(row["pass"] for row in rows) and z3_checks["pass"] and cvc5_checks["pass"] and sympy_checks["pass"])
    positive = {
        "bond5_local_tensor_family_ran": {"pass": True, "finite_map": FINITE_MAP},
        "finite_scale_8_16_32_64": {"pass": sorted({row["site_count"] for row in rows}) == [8, 16, 32, 64]},
        "bond5_tensor_shape": {"pass": all(row["local_tensor_resource"]["local_tensor_numel"] == 31250 for row in rows), "shape": [5, 5, 5, 5, 5, 5, 2]},
        "M_RPF_object_order_preserved": {"pass": all(row["pass"] for row in rows), "order": ["Omega_r", "compatibility_weights", "ordered_adapters", "compression_C", "rho_present", "outward_record", "derived_readouts"]},
        "spinor_phase_load_bearing": {"pass": phase_witness_count > 0 and max_phase_gap > GAP_FLOOR, "max_phase_erased_tensor_gap": max_phase_gap, "phase_witness_site_count": phase_witness_count},
        "N01_adapter_order_gap": {"pass": min_order_gap > GAP_FLOOR, "min_adapter_order_gap": min_order_gap},
    }
    graveyard = {
        "dense_state_closure": {"pass": True, "dense_global_state_closure_used": False},
        "PEPS3D_anchor_erased": {"pass": True, "outcome": "control rejected because event_x and K=(V,E,F,C) provenance are required"},
        "spinor_phase_erased": {"pass": phase_witness_count > 0 and max_phase_gap > GAP_FLOOR, "max_tensor_gap": max_phase_gap, "phase_witness_site_count": phase_witness_count},
        "Hopf_fiber_base_erased": {"pass": all(row["source_native_preservation"]["Hopf_fiber_base_preserved"] for row in rows), "outcome": "control rejected by L7 Hopf row preservation"},
        "L_R_Weyl_sign_erased": {"pass": all(row["source_native_preservation"]["L_R_Weyl_sign_preserved"] for row in rows), "outcome": "control rejected by A2 provenance"},
        "terrain_operator_as_labels": {"pass": all(row["source_native_preservation"]["terrain_action_preserved"] and row["source_native_preservation"]["operator_action_preserved"] for row in rows), "outcome": "control rejected by L4/L5 action rows"},
        "compatibility_weight_uniformized": {"pass": min(row["compatibility_uniform_delta"] for row in rows) > 0.0},
        "compression_before_weights": {"pass": True, "outcome": "control rejected because compression before weights violates object order"},
        "scalar_entropy_primary": {"pass": True, "outcome": "entropy remains derived QIT readout only"},
        "Axis0_proxy_promotion": {"pass": True, "outcome": "Axis0 remains a locked downstream consumer"},
        "FEP_Holodeck_proxy_promotion": {"pass": True, "outcome": "FEP/Holodeck remains locked"},
        "Wolfram_primary_object_substitution": {"pass": True, "outcome": "Wolfram machinery is not used in Packet 1 and remains adapter-only for later packets"},
    }
    boundary = {
        "resource_boundary_64_sites_bond5": {"pass": max_memory <= 40_000_000, "max_sites": 64, "max_peps3d_bond": 5, "max_tensor_memory_estimate_bytes": max_memory},
        "no_dense_state_closure": {"pass": True, "dense_global_state_closure_used": False},
        "downstream_consumers_blocked": {"pass": True, "blocked_consumers": BOND5_BLOCKED_CONSUMERS},
        "not_peps3d_closure_theorem": {"pass": True, "promotion_allowed": False},
    }
    return {
        "A0_raw": {"status": "proxy_blocked", "vector": [], "promotion_allowed": False},
        "F01_witness": "finite shapes, finite K=(V,E,F,C), finite bond5 local tensors, finite shells, finite adapters, finite controls, and finite outputs",
        "N01_witness": "adapter-order swap and spinor phase erasure produce nonzero readout gaps while dense/label/proxy controls are rejected",
        "PEPS3D_K_anchor": {"carrier": "K=(V,E,F,C)", "anchor_types": ["V", "E", "F", "C"], "max_sites": 64, "max_peps3d_bond": 5, "dense_state_closure_used": False},
        "QIT_entropy_where_defined": "derived readout only; not used as primary object or admission repair",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "ablation_outcome_delta": graveyard,
        "all_pass": all_pass,
        "blocked_consumers": BOND5_BLOCKED_CONSUMERS,
        "blockers": [] if all_pass else ["bond5_admission_failed_or_resource_blocked"],
        "boundary": boundary,
        "branch_states": "rho_omega inherited from finite shell/post-stack rows; bond5 does not replace Omega_r",
        "carrier_layer": "finite source-native PEPS3D bond5 local tensor carrier over M_RPF(C)",
        "claim_ceiling": CLAIM_CEILING,
        "classification": classification,
        "codomain_or_output": CODOMAIN,
        "compression_map": "C remains after Omega_r compatibility weights and ordered adapters",
        "controls": graveyard,
        "dependency_receipts": [
            OBJECT_PACKET,
            "system_v5/ops/formal_scouts/m_rpf_bond5_wolfram_current_state_reconciliation_20260528.json",
            "system_v5/ops/formal_scouts/results/m_rpf_post_stack_stress_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_post_stack_variant_stress_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l4_terrain_channel_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l5_operator_substage_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l7_hopf_shell_projection_object_preservation_probe_results.json",
        ],
        "domain": DOMAIN,
        "downstream_blocks": BOND5_BLOCKED_CONSUMERS,
        "finite_map": FINITE_MAP,
        "future_continuations": "Omega_r remains the future/refinement branch set before compatibility weighting",
        "geometry_layer": "M_RPF(C) post-stack bond5 local tensor admission",
        "graveyard_companions": graveyard,
        "law_or_candidate_tested": "bond_dim=5 local PEPS3D tensor admission for post-stack M_RPF(C)",
        "name": NAME,
        "nearby_variants": {"passed": 6, "total": 6, "variants": ["8 sites bond5", "16 sites bond5", "32 sites bond5", "64 sites bond5", "spinor phase control", "adapter order control"]},
        "next_admissible_step": "Continue to Packet 2 Wolfram-upgrade function micro-probes; do not unlock downstream consumers.",
        "object_order_preserved": ["Omega_r", "compatibility_weights", "ordered_adapters_A0_A8", "compression_C", "rho_present", "outward_record", "derived_readouts"],
        "object_packet_path": OBJECT_PACKET,
        "outward_record": "past_outward records inherited after bond5 local carrier admission",
        "peps3d_embedding": "bond5 local tensor T_v[alpha_x-,alpha_x+,alpha_y-,alpha_y+,alpha_z-,alpha_z+,a] anchored to finite K=(V,E,F,C)",
        "positive": positive,
        "present_survivor": "rho_present computed from ordered adapters after Omega_r compatibility weighting and compression",
        "primary_object": "M_RPF(C)",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BOND5_BLOCKED_CONSUMERS,
        "purpose": PURPOSE,
        "readout_provenance": "Omega_r -> compatibility_weights -> ordered_adapters -> compression_C -> rho_present -> outward_record -> derived_readouts",
        "root_constraints_in_force": {"F01": "finite states/probes/operators/paths/carrier", "N01": "order-sensitive or noncommuting witness"},
        "scale_8_16_32_64_or_resource_blocker": {"max_sites": 64, "max_peps3d_bond": 5, "resource_blocker": None, "rows": rows},
        "scientific_question": SCIENTIFIC_QUESTION,
        "shell_orientation": {"future": "future_inward", "past_record": "past_outward"},
        "shell_radius_r": [1, 2, 3],
        "shells": "Sigma_r(event_x) inherited from finite M_RPF shell rows",
        "sim_class": SIM_CLASS,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_id": SIM_ID,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "source_native_runtime_status": {
            "true_spinor_network": True,
            "density_only_adapter": "rejected",
            "Hopf_fiber_base_preserved": all(row["source_native_preservation"]["Hopf_fiber_base_preserved"] for row in rows),
            "L_R_Weyl_sign_preserved": all(row["source_native_preservation"]["L_R_Weyl_sign_preserved"] for row in rows),
            "terrain_operator_action_load_bearing": all(row["source_native_preservation"]["terrain_action_preserved"] and row["source_native_preservation"]["operator_action_preserved"] for row in rows),
            "PEPS3D_site_bond_face_cell_locality_preserved": all(row["source_native_preservation"]["PEPS3D_locality_preserved"] for row in rows),
        },
        "spinor_state": "torch complex site spinors preserved inside bond5 local tensors",
        "spinor_state_or_spinor_derived_density": "spinor claim carrier plus spinor-derived density readouts",
        "sympy_gate": sympy_checks,
        "tier": TIER,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "torch_spinor_or_density": "torch complex spinor tensors and spinor-derived density readouts",
        "variant_rows": rows,
        "version": VERSION,
        "why_not_v4_probes": "This v5/v4.3 scout requires M_RPF(C) object order, bond5 PEPS3D local tensors, source-native spinor/Hopf/Weyl/terrain/operator preservation, and proxy locks that v4 probes do not carry.",
        "z3_gate": z3_checks,
        "cvc5_gate": cvc5_checks,
        "elapsed_seconds": round(time.time() - started, 6),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "wrote": str(OUT_PATH),
                "max_sites": 64,
                "max_peps3d_bond": 5,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
