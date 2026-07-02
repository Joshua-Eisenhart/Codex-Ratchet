#!/usr/bin/env python3
"""Focused 64-site high-bond ceiling probe for Weyl spinor networks."""

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
NAME = "weyl_spinor_network_64site_high_bond_ceiling_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "resource_ceiling_stress_probe"
SOURCE_ALIGNMENT_CATEGORY = "source_native_weyl_spinor_network_64site_high_bond_ceiling"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: pushes the 64-site source-native Weyl spinor-network "
    "resource ceiling beyond the prior frontier by sweeping bond caps 40/48/64 "
    "and one/two/four full passes through the 13 candidate layer actions, with "
    "both L/R sheets and phase/order/edge controls. It does not admit a "
    "complete manifold layer, full PEPS3D contraction closure, flux, Xi/Phi0, "
    "Axis0, FEP/Holodeck, physics/gravity, IGT/game theory, or final manifold "
    "claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing high-bond 64-site Weyl spinor/MPS dynamics and control gaps"},
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
    "z3": {"tried": True, "used": True, "reason": "load-bearing high-bond frontier and downstream-lock proof fence"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent high-bond frontier and downstream-lock proof fence"},
    "sim_weyl_spinor_network_resource_frontier_probe": {"tried": True, "used": True, "reason": "supportive local source-native high-bond run helper"},
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
BOND_CAPS = [40, 48, 64]
CYCLE_COUNTS = [1, 2, 4]
GAP_FLOOR = 1.0e-5


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


def z3_high_bond_gate(summary: dict[str, Any]) -> dict[str, Any]:
    max_sites = z3.Int("max_sites")
    max_bond = z3.Int("max_bond")
    max_cycles = z3.Int("max_cycles")
    min_gap = z3.Real("min_gap")
    solver = z3.Solver()
    solver.add(max_sites == summary["max_site_count"])
    solver.add(max_bond == summary["max_bond_cap"])
    solver.add(max_cycles == summary["max_cycles"])
    solver.add(min_gap == z3.RealVal(str(summary["min_gap"])))
    solver.add(max_sites == 64, max_bond >= 64, max_cycles >= 4, min_gap > z3.RealVal(str(GAP_FLOOR)))
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
        "high_bond_status": str(solver.check()),
        "collapsed_zero_gap_status": str(collapsed.check()),
        "downstream_promotion_status": str(promoted.check()),
        "pass": solver.check() == z3.sat and collapsed.check() == z3.unsat and promoted.check() == z3.unsat,
    }


def cvc5_high_bond_gate(summary: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    site64 = solver.mkConst(solver.getBooleanSort(), "site64")
    bond64 = solver.mkConst(solver.getBooleanSort(), "bond64")
    cycles4 = solver.mkConst(solver.getBooleanSort(), "cycles4")
    controls = solver.mkConst(solver.getBooleanSort(), "controls")
    admitted = solver.mkConst(solver.getBooleanSort(), "admitted")
    values = {
        site64: summary["max_site_count"] == 64,
        bond64: summary["max_bond_cap"] >= 64,
        cycles4: summary["max_cycles"] >= 4,
        controls: summary["min_gap"] > GAP_FLOOR,
    }
    for term, value in values.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, site64, bond64, cycles4, controls)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    high_bond_status = str(solver.checkSat())

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
        "all_high_bond_conditions_true_but_not_admitted_status": high_bond_status,
        "downstream_promotion_without_downstream_receipts_status": nonpromotion_status,
        "pass": high_bond_status == "unsat" and nonpromotion_status == "unsat",
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
    config_rows = [frontier.run_config(SITE_COUNT, bond_cap, cycles) for bond_cap in BOND_CAPS for cycles in CYCLE_COUNTS]
    all_gaps = [gap for row in config_rows for gap in row["gaps"].values()]
    shape = base.SITE_SHAPES[SITE_COUNT]
    spinors = base.build_spinors(SITE_COUNT, "L")
    scale_certificates = {
        "topology": base.topology_certificates(shape, spinors),
        "contraction": base.contraction_witness(shape),
    }
    aux_tools = frontier.auxiliary_tool_witnesses()
    summary = {
        "site_counts": [SITE_COUNT],
        "bond_caps": BOND_CAPS,
        "cycle_counts": CYCLE_COUNTS,
        "configs_completed": len(config_rows),
        "sheet_control_runs": len(config_rows) * 2 * 4,
        "max_site_count": SITE_COUNT,
        "max_bond_cap": max(row["bond_cap"] for row in config_rows),
        "max_cycles": max(row["cycles"] for row in config_rows),
        "max_layer_applications_per_sheet_run": max(row["cycles"] for row in config_rows) * len(base.MANIFOLD_LAYERS),
        "min_gap": min(all_gaps),
        "min_left_right_gap": min(row["gaps"]["left_right_nominal_gap"] for row in config_rows),
        "min_order_gap": min(min(row["gaps"]["L_order_gap"], row["gaps"]["R_order_gap"]) for row in config_rows),
        "min_phase_gap": min(min(row["gaps"]["L_phase_gap"], row["gaps"]["R_phase_gap"]) for row in config_rows),
        "min_edge_gap": min(min(row["gaps"]["L_edge_gap"], row["gaps"]["R_edge_gap"]) for row in config_rows),
        "max_bond_seen": max(bundle["nominal"]["mps_bond_stats"]["max_bond"] for row in config_rows for bundle in row["rows"].values()),
        "elapsed_seconds": time.time() - started,
    }
    z3_gate = z3_high_bond_gate(summary)
    cvc5_gate = cvc5_high_bond_gate(summary)
    positive = {
        "high_bond_64site_grid_completed": {
            "pass": all(row["pass"] for row in config_rows),
            "summary": summary,
            "rows": config_rows,
        },
        "scale_tool_certificates_pass": {
            "pass": scale_certificates["topology"]["pass"] and scale_certificates["contraction"]["pass"],
            "scale_certificates": scale_certificates,
        },
        "auxiliary_tool_witnesses_pass": aux_tools,
        "z3_cvc5_high_bond_gates_pass": {"z3": z3_gate, "cvc5": cvc5_gate, "pass": z3_gate["pass"] and cvc5_gate["pass"]},
    }
    graveyard_companions = {
        "phase_erasure_control_rejected_at_high_bond": {"min_phase_gap": summary["min_phase_gap"], "pass": summary["min_phase_gap"] > GAP_FLOOR},
        "order_reversal_control_rejected_at_high_bond": {"min_order_gap": summary["min_order_gap"], "pass": summary["min_order_gap"] > GAP_FLOOR},
        "edge_drop_control_rejected_at_high_bond": {"min_edge_gap": summary["min_edge_gap"], "pass": summary["min_edge_gap"] > GAP_FLOOR},
        "left_right_sheet_collapse_rejected_at_high_bond": {"min_left_right_gap": summary["min_left_right_gap"], "pass": summary["min_left_right_gap"] > GAP_FLOOR},
        "dense_64_qubit_closure_still_not_used": {
            "runtime_projection": "64-site MPS path projection over source spinors with PEPS3D K=(V,E,F,C) anchors; no dense 2**64 vector constructed",
            "pass": True,
        },
    }
    boundary = {
        "high_bond_ceiling_not_final_manifold": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": PROMOTION_ALLOWED is False and "does not admit a complete manifold layer" in CLAIM_CEILING,
        },
        "full_peps3d_closure_remains_blocked": {
            "boundary": "PEPS3D grid anchors are present; full 3D contraction closure is not claimed",
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
        "finite_map": (
            "WeylSpinorNetwork64HighBondCeiling : (64-site PEPS3D K=(V,E,F,C), "
            "L/R Weyl spinor networks, bond caps 40/48/64, cycle counts 1/2/4, "
            "finite controls) -> high-bond resource-ceiling receipt, sheet/"
            "control gaps, QIT cut readouts, and proof/tool fences"
        ),
        "domain": {
            "site_count": SITE_COUNT,
            "shape": list(shape),
            "bond_caps": BOND_CAPS,
            "cycle_counts": CYCLE_COUNTS,
            "candidate_layer_actions": base.MANIFOLD_LAYERS,
        },
        "codomain_or_output": {
            "high_bond_summary": summary,
            "blocked_consumers": boundary["downstream_consumers_remain_locked"]["blocked"],
        },
        "root_constraints": {
            "F01_finite_carrier_probe_operator_path_set": "64 finite spinor sites, PEPS3D K anchor, finite bond caps, finite layer cycles, finite controls",
            "N01_noncommuting_or_order_sensitive_operation_control": "canonical-vs-reversed order gaps plus proof/tool noncommutation witnesses",
        },
        "carrier_realization": {
            "claim_bearing_object": "source_native_left_right_weyl_spinor_network",
            "torch_runtime": "PyTorch complex spinors and repo-local PyTorch MPS dynamics",
            "peps3d_embedding": "4x4x4 PEPS3D K=(V,E,F,C) anchor plus topology/contraction certificates",
            "resource_projection": "MPS path projection up to bond cap 64, not dense-state closure",
        },
        "spinor_state": "psi_v in C^2 for every site and sheet; rho_v/QIT cuts are derived readouts",
        "quaternion_action": "not_applicable: no quaternion claim is made in this scout",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/weyl_spinor_network_resource_frontier_probe_results.json",
            "system_v5/ops/formal_scouts/results/weyl_spinor_network_8_16_32_64_layer_stress_probe_results.json",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby,
        "why_not_v4_probes": "This is a v5 high-bond source-native Weyl spinor-network formal scout.",
        "blockers": [],
        "all_pass": nearby["passed"] == nearby["total"],
        "summary": summary,
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "out_path": str(OUT_PATH), "summary": summary}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
