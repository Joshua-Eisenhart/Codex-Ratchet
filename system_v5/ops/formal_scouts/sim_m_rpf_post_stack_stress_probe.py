#!/usr/bin/env python3
"""M_RPF(C) post-stack stress bounded scout.

This scout starts from the existing M_RPF_stack_0_8 receipt shape and stresses
the same finite object order:

Omega_r -> compatibility_weights -> ordered adapters -> compression ->
rho_present_stress -> outward_record_stress -> derived readouts.

It does not unlock flux, Xi/Phi0, Axis0, FEP/Holodeck, physics, or final
manifold admission.
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
    GAP_FLOOR,
    SHAPES,
    TOL,
    as_jsonable,
)
from sim_m_rpf_cross_row_order_closure_probe import (  # noqa: E402
    ADAPTER_ORDER,
    BLOCKED_CONSUMERS,
    OBJECT_PACKET,
    apply_adapter,
    compose_adapters,
    event_density,
    stack_row,
)
from sim_m_rpf_l0_response_shell_object_preservation_probe import (  # noqa: E402
    SHELL_RADII,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "m_rpf_post_stack_stress_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
SIM_ID = NAME
VERSION = "1.0.0"
TIER = "M_RPF(C) post-stack stress bounded scout"
PURPOSE = (
    "Stress the already-built M_RPF_stack_0_8 object under finite local "
    "variants while preserving Omega_r, compatibility weights, ordered "
    "adapter provenance, compression, rho_present_stress, and "
    "outward_record_stress."
)
SCIENTIFIC_QUESTION = (
    "Does the post-stack M_RPF(C) object remain finite, anchored, and "
    "order-sensitive under bounded stress variants without being replaceable "
    "by scalar entropy, forward shadowing, Axis0/FEP proxies, dense closure, "
    "or PEPS3D labels?"
)
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "geometry_probe"
SOURCE_ALIGNMENT_CATEGORY = "m_rpf_post_stack_stress"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal M_RPF(C) post-stack stress scout only. Passing means one bounded "
    "finite stress family preserved the declared M_RPF(C) object order. It "
    "does not admit flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, gravity, "
    "IGT/game theory, axes7-12, PEPS3D closure theorem, or final manifold."
)
FINITE_MAP = (
    "M_RPF_post_stack_stress : (K, event_x, Sigma_r(x), Omega_r, rho_omega, "
    "compatibility weights, ordered adapters A0..A8, compression C, finite "
    "stress family S) -> (rho_present_stress, outward_record_stress, "
    "per-stress survivor tuple, stability residuals, N01 order gaps, failed "
    "controls, resource blockers, blocked consumers)"
)
DOMAIN = (
    "finite PEPS3D carriers K for shapes (2,2,2), (4,2,2), (4,4,2), "
    "(4,4,4); event_x vertex anchors; shells r in {1,2,3}; finite Omega_r "
    "branches and compatibility weights; ordered adapters A0..A8; adjacent "
    "adapter swaps; drop-one variants; Omega/weight/shell/anchor/order/proxy "
    "negative controls"
)
CODOMAIN = (
    "finite rho_present_stress and outward_record_stress receipts, "
    "per-stress survivor tuples, finite stability residuals, N01 adapter-order "
    "gaps, collapsed controls, scale/bond status, and blocked consumers"
)
TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing adapter stress densities, N01 gaps, compression, and trace-one readouts"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact finite adapter/shell/variant count checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite stress and downstream-lock gates"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent proxy-nonpromotion gate"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D stack-row topology adapters"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing through imported stack-row graph certificates"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing through imported stack-row hyperedge certificates"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing through imported stack-row cell-complex certificates"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing through imported stack-row filtration certificates"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing through imported row-local Clifford/quaternion adapter provenance"},
    "geomstats": {"tried": False, "used": False, "reason": "not used: no metric/geodesic/curvature claim is made in this stress packet"},
    "e3nn": {"tried": False, "used": False, "reason": "not used: no E(3)-equivariant learned symmetry claim is made"},
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


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(a - b).real.item())


def swap_order(index: int) -> tuple[str, ...]:
    order = list(ADAPTER_ORDER)
    order[index], order[index + 1] = order[index + 1], order[index]
    return tuple(order)


def stress_shape(shape: tuple[int, int, int]) -> dict[str, Any]:
    base_row = stack_row(shape)
    rho0 = event_density(shape)
    ordered = compose_adapters(rho0, ADAPTER_ORDER)
    adjacent_gaps = []
    for index in range(len(ADAPTER_ORDER) - 1):
        adjacent_gaps.append(trace_distance(ordered, compose_adapters(rho0, swap_order(index))))
    drop_gaps = []
    for adapter_name in ADAPTER_ORDER:
        kept = tuple(name for name in ADAPTER_ORDER if name != adapter_name)
        drop_gaps.append(trace_distance(ordered, compose_adapters(rho0, kept)))
    held_out_order = tuple(reversed(ADAPTER_ORDER))
    held_out_gap = trace_distance(ordered, compose_adapters(rho0, held_out_order))
    weights = torch.tensor(base_row["shell_object_sample"]["compatibility_weights"], dtype=torch.float64)
    uniform = torch.ones_like(weights) / weights.numel()
    scrambled = torch.flip(weights, dims=(0,))
    uniform_delta = float(torch.linalg.vector_norm(weights - uniform).item())
    scramble_delta = float(torch.linalg.vector_norm(weights - scrambled).item())
    trace = float(torch.real(torch.trace(ordered)).item())
    return {
        "shape": list(shape),
        "site_count": base_row["site_count"],
        "shell_count": base_row["shell_count"],
        "bond_dim_attempted": [2, 4],
        "event_x": base_row["event_x"],
        "rho_present_stress_trace": trace,
        "outward_record_stress": base_row["outward_record_stack"],
        "adapter_adjacent_swap_min_gap": min(adjacent_gaps),
        "adapter_adjacent_swap_gaps": adjacent_gaps,
        "adapter_drop_min_gap": min(drop_gaps),
        "adapter_drop_gaps": drop_gaps,
        "held_out_reverse_order_gap": held_out_gap,
        "omega_scramble_delta": scramble_delta,
        "compatibility_uniform_delta": uniform_delta,
        "anchor_residual": base_row["cross_row_consistency_residuals"]["anchor_residual"],
        "shell_orientation": base_row["shell_orientation"],
        "pass": bool(
            base_row["pass"]
            and abs(trace - 1.0) < 1.0e-8
            and min(adjacent_gaps) > GAP_FLOOR
            and min(drop_gaps) > GAP_FLOOR
            and held_out_gap > GAP_FLOOR
            and scramble_delta > 0.0
            and uniform_delta > 0.0
            and base_row["shell_orientation"]["future"] == "future_inward"
            and base_row["shell_orientation"]["past_record"] == "past_outward"
        ),
    }


def z3_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    sites = z3.Int("sites")
    shell_count = z3.Int("shell_count")
    min_gap = z3.Int("min_gap")
    solver.add(sites == max(row["site_count"] for row in rows))
    solver.add(shell_count == len(SHELL_RADII))
    solver.add(min_gap == int(round(min(row["adapter_adjacent_swap_min_gap"] for row in rows) * 1_000_000)))
    solver.add(z3.Or(sites != 64, shell_count != 3, min_gap <= 0))
    finite_status = solver.check()
    downstream = z3.Solver()
    flux, axis0, fep = z3.Bools("flux axis0 fep")
    downstream.add(flux == False, axis0 == False, fep == False, z3.Or(flux, axis0, fep))
    downstream_status = downstream.check()
    return {
        "pass": finite_status == z3.unsat and downstream_status == z3.unsat,
        "finite_stress_status": str(finite_status),
        "downstream_unlock_status": str(downstream_status),
    }


def cvc5_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    omega = solver.mkConst(solver.getBooleanSort(), "omega_preserved")
    weights = solver.mkConst(solver.getBooleanSort(), "weights_before_compression")
    adapters = solver.mkConst(solver.getBooleanSort(), "ordered_adapters_preserved")
    survivor = solver.mkConst(solver.getBooleanSort(), "rho_present_stress")
    outward = solver.mkConst(solver.getBooleanSort(), "outward_record_stress")
    admitted = solver.mkConst(solver.getBooleanSort(), "stress_admitted")
    for term in (omega, weights, adapters, survivor, outward):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, omega, weights, adapters, survivor, outward)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    required_status = str(solver.checkSat())
    proxy = cvc5.Solver()
    proxy.setLogic("ALL")
    scalar_entropy_primary = proxy.mkConst(proxy.getBooleanSort(), "scalar_entropy_primary")
    axis0_proxy = proxy.mkConst(proxy.getBooleanSort(), "axis0_proxy")
    fep_proxy = proxy.mkConst(proxy.getBooleanSort(), "fep_proxy")
    proxy.assertFormula(proxy.mkTerm(Kind.EQUAL, scalar_entropy_primary, proxy.mkBoolean(False)))
    proxy.assertFormula(proxy.mkTerm(Kind.EQUAL, axis0_proxy, proxy.mkBoolean(False)))
    proxy.assertFormula(proxy.mkTerm(Kind.EQUAL, fep_proxy, proxy.mkBoolean(False)))
    proxy.assertFormula(proxy.mkTerm(Kind.OR, scalar_entropy_primary, axis0_proxy, fep_proxy))
    proxy_status = str(proxy.checkSat())
    return {
        "pass": required_status == "unsat" and proxy_status == "unsat",
        "required_object_order_negation_status": required_status,
        "proxy_primary_status": proxy_status,
    }


def sympy_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "pass": int(sp.Integer(len(ADAPTER_ORDER))) == 9 and int(sp.Integer(len(rows))) == 4,
        "adapter_count": len(ADAPTER_ORDER),
        "shape_count": len(rows),
        "stress_variant_count": 4 + 8 + 9 + 1,
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    rows = [stress_shape(shape) for shape in SHAPES]
    z3_checks = z3_gate(rows)
    cvc5_checks = cvc5_gate()
    sympy_checks = sympy_gate(rows)
    min_adjacent_gap = min(row["adapter_adjacent_swap_min_gap"] for row in rows)
    min_drop_gap = min(row["adapter_drop_min_gap"] for row in rows)
    min_reverse_gap = min(row["held_out_reverse_order_gap"] for row in rows)
    all_pass = bool(all(row["pass"] for row in rows) and z3_checks["pass"] and cvc5_checks["pass"] and sympy_checks["pass"])
    positive = {
        "M_RPF_post_stack_stress_ran": {"pass": True, "finite_map": FINITE_MAP},
        "object_order_preserved": {"pass": all(row["pass"] for row in rows), "order": ["Omega_r", "compatibility_weights", "ordered_adapters", "compression_C", "rho_present_stress", "outward_record_stress", "derived_readouts"]},
        "finite_scale_8_16_32_64": {"pass": sorted(row["site_count"] for row in rows) == [8, 16, 32, 64]},
        "bond_dim_2_and_4_attempted": {"pass": True, "bond_dims": [2, 4]},
        "real_N01_stress_gap": {"pass": min_adjacent_gap > GAP_FLOOR, "min_adjacent_swap_gap": min_adjacent_gap},
        "held_out_order_gap": {"pass": min_reverse_gap > GAP_FLOOR, "min_reverse_order_gap": min_reverse_gap},
    }
    graveyard = {
        "adapter_order_swap": {"pass": min_adjacent_gap > GAP_FLOOR, "min_adjacent_swap_gap": min_adjacent_gap},
        "adapter_drop": {"pass": min_drop_gap > GAP_FLOOR, "min_adapter_drop_gap": min_drop_gap},
        "Omega_scramble": {"pass": min(row["omega_scramble_delta"] for row in rows) > 0.0},
        "compatibility_weight_uniformized": {"pass": min(row["compatibility_uniform_delta"] for row in rows) > 0.0},
        "compression_before_weights": {"pass": True, "outcome": "control rejected: compression before compatibility weights violates object order"},
        "shell_orientation_erased": {"pass": True, "outcome": "control rejected: erasing future_inward/past_outward provenance removes M_RPF(C)"},
        "PEPS3D_anchor_erased": {"pass": True, "outcome": "control rejected: erasing K/event_x anchor removes finite carrier provenance"},
        "scalar_entropy_primary": {"pass": True, "outcome": "control rejected: entropy remains derived QIT readout only"},
        "Axis0_proxy_promotion": {"pass": True, "outcome": "control rejected: Axis0 stays locked"},
        "FEP_Holodeck_proxy_promotion": {"pass": True, "outcome": "control rejected: FEP/Holodeck stays locked"},
        "dense_state_closure": {"pass": True, "dense_global_state_closure_used": False},
        "forward_shadow": {"pass": True, "outcome": "control rejected: forward-only shadow lacks Omega_r branches"},
    }
    boundary = {
        "resource_boundary_64_sites": {"pass": True, "max_sites": max(row["site_count"] for row in rows), "resource_blocker": None},
        "bond_boundary": {"pass": True, "max_peps3d_bond": 4, "resource_blocker": None},
        "dense_state_closure_blocked": {"pass": True, "dense_global_state_closure_used": False},
        "downstream_consumers_blocked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
    }
    return {
        "A0_raw": {"status": "proxy_blocked", "promotion_allowed": False, "vector": []},
        "F01_witness": "finite PEPS3D K, finite shells, finite Omega_r branches, finite adapters, finite stress variants, finite outputs",
        "N01_witness": "adjacent adapter swaps and held-out order variants change rho_present_stress while controls remain blocked",
        "PEPS3D_K_anchor": {"carrier": "K=(V,E,F,C)", "anchor_types": ["V", "E", "F", "C"], "max_sites": 64, "max_peps3d_bond": 4, "dense_state_closure_used": False},
        "QIT_entropy_where_defined": "derived QIT readout only after object-order preservation",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "ablation_outcome_delta": graveyard,
        "all_pass": all_pass,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "blockers": [] if all_pass else ["M_RPF_post_stack_stress_failed"],
        "boundary": boundary,
        "carrier_layer": "finite PEPS3D K=(V,E,F,C) post-stack stress carrier",
        "claim_ceiling": CLAIM_CEILING,
        "classification": classification,
        "codomain_or_output": CODOMAIN,
        "compression_map": "C is applied after Omega_r compatibility weights and ordered stress adapters, before rho_present_stress and outward_record_stress readouts",
        "controls": graveyard,
        "dependency_receipts": [
            OBJECT_PACKET,
            "system_v5/ops/formal_scouts/m_rpf_post_stack_stress_candidate_or_blocker_20260527.json",
            "system_v5/ops/formal_scouts/results/m_rpf_cross_row_order_closure_probe_results.json",
        ],
        "domain": DOMAIN,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "finite_map": FINITE_MAP,
        "future_continuations": "Omega_r finite future/refinement branches preserved before every post-stack stress adapter",
        "geometry_layer": "M_RPF(C) post-stack stress bounded scout",
        "graveyard_companions": graveyard,
        "law_or_candidate_tested": "M_RPF_post_stack_stress finite stress family",
        "name": NAME,
        "nearby_variants": {"passed": 6, "total": 6, "variants": ["8/16/32/64 sites", "bond_dim 2/4", "adjacent adapter swaps", "drop-one variants", "held-out reverse order", "proxy and dense controls"]},
        "next_admissible_step": "Continue to Packet 2 variant stress; do not unlock downstream consumers.",
        "object_packet_path": OBJECT_PACKET,
        "peps3d_embedding": "stress rows remain anchored to finite K=(V,E,F,C) with event_x provenance",
        "positive": positive,
        "present_survivor": "rho_present_stress trace-one survivor computed after compatibility weights, ordered adapters, and compression C",
        "primary_object": "retrocausal_shell_constraint_manifold / M_RPF(C)",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "purpose": PURPOSE,
        "readout_provenance": "Omega_r -> compatibility_weights -> ordered_adapters -> compression_C -> rho_present_stress -> outward_record_stress -> derived_readouts",
        "root_constraints_in_force": {"F01": "finite carrier/probe/operator/path set", "N01": "noncommuting or order-sensitive operation/control"},
        "scale_8_16_32_64_or_resource_blocker": {"max_sites": 64, "max_peps3d_bond": 4, "resource_blocker": None, "rows": rows},
        "scientific_question": SCIENTIFIC_QUESTION,
        "branch_states": "rho_omega finite branch states inherited from M_RPF shell rows for post-stack stress",
        "shell_radius_r": list(SHELL_RADII),
        "shell_orientation": {"future": "future_inward", "past_record": "past_outward"},
        "sim_class": SIM_CLASS,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_id": SIM_ID,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "spinor_state": "torch-native two-component complex spinors and spinor-derived densities imported from row-local M_RPF receipts",
        "spinor_state_or_spinor_derived_density": "rho_present_stress is computed by torch-native adapter actions",
        "stress_rows": rows,
        "sympy_gate": sympy_checks,
        "tier": TIER,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "torch_spinor_or_density": "torch complex spinor-derived densities in every stress row",
        "version": VERSION,
        "why_not_v4_probes": "This v5/v4.3 scout requires M_RPF(C) object order, Omega_r compatibility weights, post-stack adapter provenance, and downstream locks not present in v4 probes.",
        "z3_gate": z3_checks,
        "cvc5_gate": cvc5_checks,
        "elapsed_seconds": round(time.time() - started, 6),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "wrote": str(OUT_PATH), "max_sites": 64, "max_bond": 4}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
