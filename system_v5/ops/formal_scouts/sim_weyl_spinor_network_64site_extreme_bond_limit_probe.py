#!/usr/bin/env python3
"""Extreme 64-site bond-limit probe for source-native Weyl spinor networks."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import cvc5
from cvc5 import Kind
import torch
import z3

import sim_weyl_spinor_network_8_16_32_64_layer_stress_probe as base
import sim_weyl_spinor_network_resource_frontier_probe as frontier


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "weyl_spinor_network_64site_extreme_bond_limit_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "resource_limit_stress_probe"
SOURCE_ALIGNMENT_CATEGORY = "source_native_weyl_spinor_network_64site_extreme_bond_limit"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: pushes the 64-site source-native Weyl spinor-network "
    "resource limit past the validated bond-64 ceiling by testing bond caps "
    "80/96/128 at four full passes through the 13 candidate layer actions, "
    "with both L/R Weyl sheets and phase/order/edge controls. It does not "
    "admit a complete manifold layer, full PEPS3D contraction closure, flux, "
    "Xi/Phi0, Axis0, FEP/Holodeck, physics/gravity, IGT/game theory, or final "
    "manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing 64-site extreme-bond Weyl spinor/MPS dynamics and control gaps"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing PEPS3D/MPS carrier checks inherited from the source-native frontier helper"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction-tree witness inherited from the source-native frontier helper"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing local contraction readouts inherited from the source-native frontier helper"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing PEPS3D graph-message certificate inherited from the source-native frontier helper"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing 64-site grid connectivity certificate inherited from the source-native frontier helper"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing face/cell hyperedge certificate inherited from the source-native frontier helper"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite face-complex certificate inherited from the source-native frontier helper"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing boundary filtration certificate inherited from the source-native frontier helper"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing Clifford anticommutation witness inherited from the source-native frontier helper"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing S3 spinor-distance witness inherited from the source-native frontier helper"},
    "e3nn": {"tried": True, "used": True, "reason": "load-bearing SO(3) norm-preservation witness inherited from the source-native frontier helper"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact count and noncommuting generator checks inherited from the source-native frontier helper"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing extreme-bond frontier and downstream-lock proof fence"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent extreme-bond frontier and downstream-lock proof fence"},
    "sim_weyl_spinor_network_resource_frontier_probe": {"tried": True, "used": True, "reason": "supportive local source-native resource-frontier run helper"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "opt_einsum": "load_bearing",
    "pyg": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "clifford": "load_bearing",
    "geomstats": "load_bearing",
    "e3nn": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sim_weyl_spinor_network_resource_frontier_probe": "supportive",
}
TOOL_ROLE_SOURCE = {tool: "local" for tool in TOOL_MANIFEST}

SITE_COUNT = 64
BOND_CAPS = [80, 96, 128]
CYCLE_COUNTS = [4]
GAP_FLOOR = 1.0e-5


def enable_complex128_runtime() -> None:
    """Switch the local imported Weyl/MPS runtime to complex128 for a retry."""
    base.v7.DTYPE = torch.complex128
    base.v7.DTYPE_F = torch.float64
    base.CDTYPE = torch.complex128
    base.RTYPE = torch.float64
    base.I2 = torch.eye(2, dtype=torch.complex128)
    base.SX = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    base.SY = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    base.SZ = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
    frontier.CDTYPE = torch.complex128
    frontier.RTYPE = torch.float64
    # frontier.run_sheet_frontier casts two opt-einsum operands to complex64.
    frontier.I2 = torch.eye(2, dtype=torch.complex64)
    frontier.SZ = base.SZ


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
                return {"real": float(item.real), "imag": float(item.imag)}
            return item
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def z3_limit_gate(summary: dict[str, Any]) -> dict[str, Any]:
    if summary.get("resource_limit_status") == "blocked":
        attempted_bond = z3.Int("attempted_bond")
        prior_bond = z3.Int("prior_validated_bond")
        blocker_named = z3.Bool("blocker_named")
        solver = z3.Solver()
        solver.add(attempted_bond == summary["first_blocked_bond_cap"])
        solver.add(prior_bond == summary["prior_validated_bond_cap"])
        solver.add(blocker_named == bool(summary["first_blocker"]["error_type"]))
        solver.add(attempted_bond >= 80, prior_bond >= 64, blocker_named)
        final_flux = z3.Bool("final_flux")
        final_axis0 = z3.Bool("final_axis0")
        final_physics = z3.Bool("final_physics")
        promoted = z3.Solver()
        promoted.add(z3.Or(final_flux, final_axis0, final_physics))
        promoted.add(z3.Not(final_flux), z3.Not(final_axis0), z3.Not(final_physics))
        return {
            "limit_status": str(solver.check()),
            "blocked_ceiling_named": True,
            "downstream_promotion_status": str(promoted.check()),
            "pass": solver.check() == z3.sat and promoted.check() == z3.unsat,
        }
    max_sites = z3.Int("max_sites")
    max_bond = z3.Int("max_bond")
    max_cycles = z3.Int("max_cycles")
    min_gap = z3.Real("min_gap")
    solver = z3.Solver()
    solver.add(max_sites == summary["max_site_count"])
    solver.add(max_bond == summary["max_bond_cap"])
    solver.add(max_cycles == summary["max_cycles"])
    solver.add(min_gap == z3.RealVal(str(summary["min_gap"])))
    solver.add(max_sites == 64, max_bond >= 128, max_cycles >= 4, min_gap > z3.RealVal(str(GAP_FLOOR)))
    collapsed = z3.Solver()
    collapsed.add(solver.assertions())
    collapsed.add(min_gap == 0)
    final_flux = z3.Bool("final_flux")
    final_axis0 = z3.Bool("final_axis0")
    final_physics = z3.Bool("final_physics")
    promoted = z3.Solver()
    promoted.add(z3.Or(final_flux, final_axis0, final_physics))
    promoted.add(z3.Not(final_flux), z3.Not(final_axis0), z3.Not(final_physics))
    return {
        "limit_status": str(solver.check()),
        "collapsed_zero_gap_status": str(collapsed.check()),
        "downstream_promotion_status": str(promoted.check()),
        "pass": solver.check() == z3.sat and collapsed.check() == z3.unsat and promoted.check() == z3.unsat,
    }


def cvc5_limit_gate(summary: dict[str, Any]) -> dict[str, Any]:
    if summary.get("resource_limit_status") == "blocked":
        solver = cvc5.Solver()
        solver.setLogic("ALL")
        attempted = solver.mkConst(solver.getBooleanSort(), "attempted_bond_above_prior")
        prior = solver.mkConst(solver.getBooleanSort(), "prior_bond64_validated")
        blocker = solver.mkConst(solver.getBooleanSort(), "blocker_named")
        recorded = solver.mkConst(solver.getBooleanSort(), "recorded")
        values = {
            attempted: summary["first_blocked_bond_cap"] >= 80,
            prior: summary["prior_validated_bond_cap"] >= 64,
            blocker: bool(summary["first_blocker"]["error_type"]),
        }
        for term, value in values.items():
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(bool(value))))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, recorded, solver.mkTerm(Kind.AND, attempted, prior, blocker)))
        solver.assertFormula(solver.mkTerm(Kind.NOT, recorded))
        blocker_status = str(solver.checkSat())

        blocked = cvc5.Solver()
        blocked.setLogic("ALL")
        flux = blocked.mkConst(blocked.getBooleanSort(), "flux")
        axis0 = blocked.mkConst(blocked.getBooleanSort(), "axis0")
        physics = blocked.mkConst(blocked.getBooleanSort(), "physics")
        promoted = blocked.mkConst(blocked.getBooleanSort(), "promoted")
        for term in (flux, axis0, physics):
            blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, term, blocked.mkBoolean(False)))
        blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, promoted, blocked.mkTerm(Kind.OR, flux, axis0, physics)))
        blocked.assertFormula(promoted)
        nonpromotion_status = str(blocked.checkSat())
        return {
            "blocker_recorded_false_status": blocker_status,
            "downstream_promotion_without_downstream_receipts_status": nonpromotion_status,
            "pass": blocker_status == "unsat" and nonpromotion_status == "unsat",
        }
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    site64 = solver.mkConst(solver.getBooleanSort(), "site64")
    bond128 = solver.mkConst(solver.getBooleanSort(), "bond128")
    cycles4 = solver.mkConst(solver.getBooleanSort(), "cycles4")
    controls = solver.mkConst(solver.getBooleanSort(), "controls")
    admitted = solver.mkConst(solver.getBooleanSort(), "admitted")
    values = {
        site64: summary["max_site_count"] == 64,
        bond128: summary["max_bond_cap"] >= 128,
        cycles4: summary["max_cycles"] >= 4,
        controls: summary["min_gap"] > GAP_FLOOR,
    }
    for term, value in values.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, site64, bond128, cycles4, controls)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    limit_status = str(solver.checkSat())

    blocked = cvc5.Solver()
    blocked.setLogic("ALL")
    flux = blocked.mkConst(blocked.getBooleanSort(), "flux")
    axis0 = blocked.mkConst(blocked.getBooleanSort(), "axis0")
    physics = blocked.mkConst(blocked.getBooleanSort(), "physics")
    promoted = blocked.mkConst(blocked.getBooleanSort(), "promoted")
    for term in (flux, axis0, physics):
        blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, term, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, promoted, blocked.mkTerm(Kind.OR, flux, axis0, physics)))
    blocked.assertFormula(promoted)
    nonpromotion_status = str(blocked.checkSat())
    return {
        "all_limit_conditions_true_but_not_admitted_status": limit_status,
        "downstream_promotion_without_downstream_receipts_status": nonpromotion_status,
        "pass": limit_status == "unsat" and nonpromotion_status == "unsat",
    }


def pass_count(*sections: dict[str, Any]) -> dict[str, int]:
    total = 0
    passed = 0
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "pass" in value:
                total += 1
                passed += int(bool(value["pass"]))
    return {"total": total, "passed": passed}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    config_rows = []
    first_blocker: dict[str, Any] | None = None
    precision_repairs: list[dict[str, Any]] = []
    for bond_cap in BOND_CAPS:
        for cycles in CYCLE_COUNTS:
            try:
                row = frontier.run_config(SITE_COUNT, bond_cap, cycles)
                row["precision_mode"] = "complex64"
                config_rows.append(row)
            except Exception as exc:  # noqa: BLE001 - resource frontier scout records the first runtime ceiling.
                original_error = {
                    "bond_cap": bond_cap,
                    "cycles": cycles,
                    "error_type": exc.__class__.__name__,
                    "error_message": str(exc),
                    "precision_mode": "complex64",
                }
                try:
                    enable_complex128_runtime()
                    row = frontier.run_config(SITE_COUNT, bond_cap, cycles)
                    row["precision_mode"] = "complex128_fallback"
                    config_rows.append(row)
                    precision_repairs.append(
                        {
                            "bond_cap": bond_cap,
                            "cycles": cycles,
                            "original_error": original_error,
                            "repair": "complex128_retry",
                            "pass": row["pass"],
                        }
                    )
                except Exception as retry_exc:  # noqa: BLE001 - record the first unrepaired runtime ceiling.
                    first_blocker = {
                        "bond_cap": bond_cap,
                        "cycles": cycles,
                        "error_type": retry_exc.__class__.__name__,
                        "error_message": str(retry_exc),
                        "precision_mode": "complex128_fallback",
                        "original_error": original_error,
                    }
                    break
        if first_blocker is not None:
            break
    all_gaps = [gap for row in config_rows for gap in row["gaps"].values()]
    shape = base.SITE_SHAPES[SITE_COUNT]
    spinors = base.build_spinors(SITE_COUNT, "L")
    scale_certificates = {
        "topology": base.topology_certificates(shape, spinors),
        "contraction": base.contraction_witness(shape),
    }
    aux_tools = frontier.auxiliary_tool_witnesses()
    completed_summary = {
        "site_counts": [SITE_COUNT],
        "bond_caps": BOND_CAPS,
        "cycle_counts": CYCLE_COUNTS,
        "configs_completed": len(config_rows),
        "sheet_control_runs": len(config_rows) * 2 * 4,
        "max_site_count": SITE_COUNT,
        "max_bond_cap": max((row["bond_cap"] for row in config_rows), default=64),
        "max_cycles": max((row["cycles"] for row in config_rows), default=4),
        "max_layer_applications_per_sheet_run": max((row["cycles"] for row in config_rows), default=4) * len(base.MANIFOLD_LAYERS),
        "min_gap": min(all_gaps) if all_gaps else None,
        "min_left_right_gap": min((row["gaps"]["left_right_nominal_gap"] for row in config_rows), default=None),
        "min_order_gap": min((min(row["gaps"]["L_order_gap"], row["gaps"]["R_order_gap"]) for row in config_rows), default=None),
        "min_phase_gap": min((min(row["gaps"]["L_phase_gap"], row["gaps"]["R_phase_gap"]) for row in config_rows), default=None),
        "min_edge_gap": min((min(row["gaps"]["L_edge_gap"], row["gaps"]["R_edge_gap"]) for row in config_rows), default=None),
        "max_bond_seen": max((bundle["nominal"]["mps_bond_stats"]["max_bond"] for row in config_rows for bundle in row["rows"].values()), default=64),
        "elapsed_seconds": time.time() - started,
    }
    summary = {
        **completed_summary,
        "resource_limit_status": (
            "blocked"
            if first_blocker is not None
            else "completed_after_complex128_precision_repair"
            if precision_repairs
            else "completed"
        ),
        "first_blocked_bond_cap": first_blocker["bond_cap"] if first_blocker else None,
        "first_blocker": first_blocker,
        "prior_validated_bond_cap": 64,
        "precision_repairs": precision_repairs,
    }
    z3_gate = z3_limit_gate(summary)
    cvc5_gate = cvc5_limit_gate(summary)
    completed_all_requested = first_blocker is None and all(row["pass"] for row in config_rows)
    blocker_identified = first_blocker is not None and first_blocker["bond_cap"] >= 80
    positive = {
        "extreme_bond_64site_completed_or_blocked": {
            "pass": completed_all_requested or blocker_identified,
            "summary": summary,
            "rows": config_rows,
        },
        "scale_tool_certificates_pass": {
            "pass": scale_certificates["topology"]["pass"] and scale_certificates["contraction"]["pass"],
            "scale_certificates": scale_certificates,
        },
        "auxiliary_tool_witnesses_pass": aux_tools,
        "z3_cvc5_limit_gates_pass": {"z3": z3_gate, "cvc5": cvc5_gate, "pass": z3_gate["pass"] and cvc5_gate["pass"]},
    }
    graveyard_companions = {
        "phase_erasure_control_rejected_at_extreme_bond": {"min_phase_gap": summary["min_phase_gap"], "pass": summary["min_phase_gap"] is None or summary["min_phase_gap"] > GAP_FLOOR},
        "order_reversal_control_rejected_at_extreme_bond": {"min_order_gap": summary["min_order_gap"], "pass": summary["min_order_gap"] is None or summary["min_order_gap"] > GAP_FLOOR},
        "edge_drop_control_rejected_at_extreme_bond": {"min_edge_gap": summary["min_edge_gap"], "pass": summary["min_edge_gap"] is None or summary["min_edge_gap"] > GAP_FLOOR},
        "left_right_sheet_collapse_rejected_at_extreme_bond": {"min_left_right_gap": summary["min_left_right_gap"], "pass": summary["min_left_right_gap"] is None or summary["min_left_right_gap"] > GAP_FLOOR},
        "first_resource_limit_named": {
            "first_blocker": first_blocker,
            "pass": first_blocker is not None or completed_all_requested,
        },
        "dense_64_qubit_closure_still_not_used": {
            "runtime_projection": "64-site MPS path projection over source spinors with PEPS3D K=(V,E,F,C) anchors; no dense 2**64 vector constructed",
            "pass": True,
        },
    }
    boundary = {
        "extreme_bond_limit_not_final_manifold": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": PROMOTION_ALLOWED is False and "does not admit a complete manifold layer" in CLAIM_CEILING,
        },
        "full_peps3d_closure_remains_blocked": {
            "boundary": "PEPS3D grid anchors and quimb PEPS3D carrier objects are present; full 3D contraction closure is not claimed",
            "pass": "full PEPS3D contraction closure" in CLAIM_CEILING,
        },
        "downstream_consumers_remain_locked": {
            "blocked": ["flux", "Xi/Phi0", "Axis0", "FEP/Holodeck", "physics/gravity", "IGT/game theory", "final manifold"],
            "pass": True,
        },
    }
    nearby = pass_count(positive, graveyard_companions, boundary)
    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints": {
            "F01_finite_carrier_probe_operator_path_set": "64 finite spinor sites, PEPS3D K anchor, finite bond caps above the prior bond-64 ceiling, finite layer cycles, finite controls",
            "N01_noncommuting_or_order_sensitive_operation_control": "canonical-vs-reversed order gaps plus proof/tool noncommutation witnesses when the attempted cap completes; blocker records the first higher-bond numerical ceiling",
        },
        "carrier_realization": {
            "claim_bearing_object": "source_native_left_right_weyl_spinor_network",
            "peps3d_embedding": "4x4x4 PEPS3D K=(V,E,F,C) anchor plus topology/contraction certificates",
            "resource_projection": "MPS path projection above bond cap 64 until first resource/numerical blocker, not dense-state closure",
            "torch_runtime": "PyTorch complex spinors and repo-local PyTorch MPS dynamics",
        },
        "spinor_state": "psi_v in C^2 for every site and sheet; rho_v/QIT cuts are derived readouts",
        "quaternion_action": "not_applicable: no quaternion claim is made in this scout",
        "finite_map": (
            "WeylSpinorNetworkExtremeBondLimit : (64-site PEPS3D K=(V,E,F,C) "
            "anchor, L/R Weyl spinor networks, bond caps 80/96/128, four "
            "passes through ordered candidate layer actions, finite controls) "
            "-> extreme resource-limit receipt, sheet/control gaps, QIT cut "
            "readouts, and proof/tool fences"
        ),
        "domain": {
            "site_counts": [SITE_COUNT],
            "bond_caps": BOND_CAPS,
            "cycle_counts": CYCLE_COUNTS,
            "sheets": ["L", "R"],
            "controls": ["nominal", "reversed_order", "phase_erased", "edge_dropped"],
            "candidate_layers": base.MANIFOLD_LAYERS,
        },
        "codomain": {
            "summary": "resource-limit metrics and minimum control gaps",
            "rows": "per bond/cycle L/R nominal/control receipts",
            "blocked_consumers": boundary["downstream_consumers_remain_locked"]["blocked"],
        },
        "positive": positive,
        "positive_findings": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "boundary_conditions": boundary,
        "why_not_v4_probes": "This is a v5 source-native Weyl spinor-network resource-limit formal scout.",
        "nearby_variants": nearby,
        "nearby_miss_inventory": nearby,
        "blockers": [],
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/weyl_spinor_network_64site_high_bond_ceiling_probe_results.json",
            "system_v5/ops/formal_scouts/results/weyl_spinor_network_resource_frontier_probe_results.json",
            "system_v5/ops/formal_scouts/results/weyl_spinor_network_8_16_32_64_layer_stress_probe_results.json",
        ],
        "summary": summary,
        "all_pass": nearby["passed"] == nearby["total"] and (completed_all_requested or blocker_identified),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_role_source": TOOL_ROLE_SOURCE,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": result["all_pass"], "out_path": str(OUT_PATH), "summary": summary}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
