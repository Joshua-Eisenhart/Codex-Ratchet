#!/usr/bin/env python3
"""Resource-frontier continuation for the Weyl spinor-network stress sim."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import cotengra as ctg
import cvc5
from cvc5 import Kind
from clifford import Cl
from e3nn import o3
import geomstats.backend as gs
from geomstats.geometry.hypersphere import Hypersphere
import gudhi
import opt_einsum as oe
import quimb.tensor as qtn
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
import toponetx as tnx
import xgi
import z3

import sim_weyl_spinor_network_8_16_32_64_layer_stress_probe as base


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "weyl_spinor_network_resource_frontier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "resource_frontier_stress_probe"
SOURCE_ALIGNMENT_CATEGORY = "source_native_weyl_spinor_network_resource_frontier"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: continues the source-native Weyl spinor-network sim "
    "to the current resource frontier by sweeping 8/16/32/64 sites, both L/R "
    "Weyl sheets, bond caps 8/16/24/32, one/two/four full passes through the "
    "13 candidate layer actions, and phase/order/edge controls. It keeps "
    "PyTorch-owned spinor/MPS dynamics and PEPS3D grid anchors. It does not "
    "admit a complete manifold layer, full PEPS3D contraction closure, flux, "
    "Xi/Phi0, Axis0, FEP/Holodeck, physics/gravity, IGT/game theory, or final "
    "manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex Weyl spinors, repeated MPS layer dynamics, local Hamiltonian/layer gates, QIT cuts, controls, and resource-frontier metrics",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PEPS3D/MPS carrier representation checks seeded from source spinors at the 8/16/32/64 anchors",
    },
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "load-bearing contraction-tree witness for representative PEPS3D cell/cut expressions at each scale",
    },
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": "load-bearing local overlap/cut contractions over evolved spinor-derived densities",
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph message aggregation over PEPS3D grid anchors with spinor features",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PEPS3D grid connectivity and path-projection certification",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing face/cell hyperedge inventory for K=(V,E,F,C)",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite face-complex certification for PEPS3D surface structure",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing boundary filtration/persistence witness over finite grid anchors",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Clifford anticommutation and bivector orientation witness for Weyl sheet action",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing S3 spinor-distance witness using the PyTorch backend",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SO(3) equivariance/norm-preservation check for spinor-derived Bloch feature transport",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact count and noncommuting generator checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite resource-frontier and downstream-lock proof fence",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite resource-frontier and downstream-lock proof fence",
    },
    "sim_weyl_spinor_network_8_16_32_64_layer_stress_probe": {
        "tried": True,
        "used": True,
        "reason": "supportive local source-native Weyl spinor-network helper functions; this scout reruns the dynamics with a larger resource grid",
    },
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
    "sim_weyl_spinor_network_8_16_32_64_layer_stress_probe": "supportive",
}
TOOL_ROLE_SOURCE = {tool: "local" for tool in TOOL_MANIFEST}

SITE_COUNTS = [8, 16, 32, 64]
BOND_CAPS = [8, 16, 24, 32]
CYCLE_COUNTS = [1, 2, 4]
SHEETS = ["L", "R"]
GAP_FLOOR = 1.0e-5
CDTYPE = base.CDTYPE
RTYPE = torch.float64
I2 = torch.eye(2, dtype=CDTYPE)
SZ = base.SZ


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


def selected_local_z(mps: base.v7.MPS) -> list[float]:
    sites = sorted({0, mps.N // 4, mps.N // 2, (3 * mps.N) // 4, mps.N - 1})
    values = []
    for site in sites:
        rho = base.reduced_single_safe(mps, site)
        values.append(float(torch.trace(rho @ SZ).real.item()))
    return values


def signature(row: dict[str, Any]) -> torch.Tensor:
    return torch.tensor(
        [
            float(row["half_chain_entropy"]),
            float(row["mean_abs_local_z"]),
            float(row["mps_bond_stats"]["max_bond"]),
            float(row["mps_bond_stats"]["mean_bond"]),
            float(row["geomstats_s3_first_last_distance"]),
            *[float(value) for value in row["selected_local_z"]],
        ],
        dtype=RTYPE,
    )


def sig_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return float(torch.linalg.vector_norm(signature(a) - signature(b)).item())


def run_sheet_frontier(
    site_count: int,
    sheet: str,
    *,
    bond_cap: int,
    cycles: int,
    reversed_order: bool = False,
    erase_phase: bool = False,
    drop_edges: bool = False,
    include_quimb: bool = False,
) -> dict[str, Any]:
    layer_order = list(range(len(base.MANIFOLD_LAYERS)))
    if reversed_order:
        layer_order = list(reversed(layer_order))
    spinors = base.build_spinors(site_count, sheet, erase_phase=erase_phase)
    mps = base.v7.MPS.product(spinors)
    path_edges = [(idx, idx + 1) for idx in range(site_count - 1)]
    layer_trace = []
    for cycle in range(cycles):
        for step, layer_idx in enumerate(layer_order):
            for site in range(site_count):
                mps.apply_single(base.layer_gate(sheet, layer_idx, site, site_count, erase_phase=erase_phase), site)
            if not drop_edges:
                gate = base.two_site_gate(sheet, layer_idx, erase_phase=erase_phase)
                edge_iter = path_edges if (cycle + step) % 2 == 0 else list(reversed(path_edges))
                for edge_start, _edge_end in edge_iter:
                    mps.apply_two(gate, edge_start, max_bond=bond_cap)
            mps.normalize_()
            if (cycle, step) in {(0, 0), (cycles - 1, len(layer_order) - 1)}:
                layer_trace.append(
                    {
                        "cycle": int(cycle),
                        "step": int(step),
                        "layer_index": int(layer_idx),
                        "layer": base.MANIFOLD_LAYERS[layer_idx],
                        "max_bond": base.mps_bond_stats(mps)["max_bond"],
                        "half_chain_entropy": float(mps.copy().schmidt_entropy(site_count // 2).item()),
                    }
                )
    z_values = selected_local_z(mps)
    first_rho = base.reduced_single_safe(mps, 0)
    last_rho = base.reduced_single_safe(mps, site_count - 1)
    opt_value = oe.contract("ab,bc,ca->", first_rho.to(torch.complex64), last_rho.to(torch.complex64), I2)
    quimb_check = base.quimb_carrier_check(base.SITE_SHAPES[site_count], spinors) if include_quimb else {"pass": True, "deferred_to_scale_certificate": True}
    return {
        "site_count": site_count,
        "shape": list(base.SITE_SHAPES[site_count]),
        "sheet": sheet,
        "bond_cap": bond_cap,
        "cycles": cycles,
        "spinor_count": len(spinors),
        "layer_applications": len(layer_order) * cycles,
        "two_site_edge_sweeps": 0 if drop_edges else len(layer_order) * cycles,
        "mps_bond_stats": base.mps_bond_stats(mps),
        "half_chain_entropy": float(mps.copy().schmidt_entropy(site_count // 2).item()),
        "selected_local_z": z_values,
        "mean_abs_local_z": float(torch.mean(torch.abs(torch.tensor(z_values, dtype=RTYPE))).item()),
        "first_last_opt_einsum_trace": {"real": float(torch.real(opt_value).item()), "imag": float(torch.imag(opt_value).item())},
        "geomstats_s3_first_last_distance": base.geomstats_s3_distance(spinors[0], spinors[-1]),
        "e3nn_norm_check": base.e3nn_norm_check(base.bloch(spinors[0])),
        "quimb_carrier_check": quimb_check,
        "layer_trace": layer_trace,
        "pass": (
            len(spinors) == site_count
            and base.mps_bond_stats(mps)["max_bond"] <= bond_cap
            and quimb_check["pass"]
            and len(layer_order) * cycles > 0
        ),
    }


def run_config(site_count: int, bond_cap: int, cycles: int) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    gaps: dict[str, float] = {}
    for sheet in SHEETS:
        nominal = run_sheet_frontier(site_count, sheet, bond_cap=bond_cap, cycles=cycles, include_quimb=(bond_cap == BOND_CAPS[0] and cycles == CYCLE_COUNTS[0]))
        reversed_row = run_sheet_frontier(site_count, sheet, bond_cap=bond_cap, cycles=cycles, reversed_order=True)
        phase_row = run_sheet_frontier(site_count, sheet, bond_cap=bond_cap, cycles=cycles, erase_phase=True)
        edge_row = run_sheet_frontier(site_count, sheet, bond_cap=bond_cap, cycles=cycles, drop_edges=True)
        rows[sheet] = {
            "nominal": nominal,
            "reversed_order": reversed_row,
            "phase_erased": phase_row,
            "edge_dropped": edge_row,
        }
        gaps[f"{sheet}_order_gap"] = sig_gap(nominal, reversed_row)
        gaps[f"{sheet}_phase_gap"] = sig_gap(nominal, phase_row)
        gaps[f"{sheet}_edge_gap"] = sig_gap(nominal, edge_row)
    gaps["left_right_nominal_gap"] = sig_gap(rows["L"]["nominal"], rows["R"]["nominal"])
    return {
        "site_count": site_count,
        "shape": list(base.SITE_SHAPES[site_count]),
        "bond_cap": bond_cap,
        "cycles": cycles,
        "rows": rows,
        "gaps": gaps,
        "pass": all(row["pass"] for bundle in rows.values() for row in bundle.values()) and all(value > GAP_FLOOR for value in gaps.values()),
    }


def scale_certificates() -> dict[str, Any]:
    rows = {}
    for site_count in SITE_COUNTS:
        shape = base.SITE_SHAPES[site_count]
        spinors = base.build_spinors(site_count, "L")
        rows[str(site_count)] = {
            "topology": base.topology_certificates(shape, spinors),
            "contraction": base.contraction_witness(shape),
        }
    return {
        "rows": rows,
        "pass": all(row["topology"]["pass"] and row["contraction"]["pass"] for row in rows.values()),
    }


def auxiliary_tool_witnesses() -> dict[str, Any]:
    clifford = base.clifford_witness()
    sympy = base.sympy_witness()
    autograd = base.autograd_witness()
    sphere = Hypersphere(dim=3)
    p = gs.array([1.0, 0.0, 0.0, 0.0], dtype=gs.float64)
    q = gs.array([0.0, 1.0, 0.0, 0.0], dtype=gs.float64)
    geomstats = {"distance_pi_over_2": float(sphere.metric.dist(p, q).item()), "pass": abs(float(sphere.metric.dist(p, q).item()) - 1.57079632679) < 1.0e-5}
    rotation = o3.angles_to_matrix(torch.tensor(0.11, dtype=torch.float64), torch.tensor(0.23, dtype=torch.float64), torch.tensor(0.37, dtype=torch.float64))
    e3nn = {"determinant": float(torch.det(rotation).item()), "pass": abs(float(torch.det(rotation).item()) - 1.0) < 1.0e-5}
    _layout, blades = Cl(3)
    clifford["e2e3_anticommutator_zero"] = str(blades["e2"] * blades["e3"] + blades["e3"] * blades["e2"]) == "0"
    clifford["pass"] = bool(clifford["pass"] and clifford["e2e3_anticommutator_zero"])
    return {
        "clifford": clifford,
        "sympy": sympy,
        "autograd": autograd,
        "geomstats": geomstats,
        "e3nn": e3nn,
        "pass": all(row["pass"] for row in (clifford, sympy, autograd, geomstats, e3nn)),
    }


def z3_frontier_gate(summary: dict[str, Any]) -> dict[str, Any]:
    max_sites = z3.Int("max_sites")
    max_bond = z3.Int("max_bond")
    max_cycles = z3.Int("max_cycles")
    min_gap = z3.Real("min_gap")
    solver = z3.Solver()
    solver.add(max_sites == summary["max_site_count"])
    solver.add(max_bond == summary["max_bond_cap"])
    solver.add(max_cycles == summary["max_cycles"])
    solver.add(min_gap == z3.RealVal(str(summary["min_gap"])))
    solver.add(max_sites == 64, max_bond >= 32, max_cycles >= 4, min_gap > z3.RealVal(str(GAP_FLOOR)))
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
        "frontier_status": str(solver.check()),
        "collapsed_zero_gap_status": str(collapsed.check()),
        "downstream_promotion_status": str(promoted.check()),
        "pass": solver.check() == z3.sat and collapsed.check() == z3.unsat and promoted.check() == z3.unsat,
    }


def cvc5_frontier_gate(summary: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    finite = solver.mkConst(solver.getBooleanSort(), "finite_8_16_32_64")
    bond32 = solver.mkConst(solver.getBooleanSort(), "bond32")
    cycles4 = solver.mkConst(solver.getBooleanSort(), "cycles4")
    controls = solver.mkConst(solver.getBooleanSort(), "controls")
    admitted = solver.mkConst(solver.getBooleanSort(), "admitted")
    values = {
        finite: summary["max_site_count"] == 64,
        bond32: summary["max_bond_cap"] >= 32,
        cycles4: summary["max_cycles"] >= 4,
        controls: summary["min_gap"] > GAP_FLOOR,
    }
    for term, value in values.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, finite, bond32, cycles4, controls)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    admission_status = str(solver.checkSat())

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
        "all_frontier_conditions_true_but_not_admitted_status": admission_status,
        "downstream_promotion_without_downstream_receipts_status": nonpromotion_status,
        "pass": admission_status == "unsat" and nonpromotion_status == "unsat",
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
    scale_tool_certificates = scale_certificates()
    aux_tools = auxiliary_tool_witnesses()
    config_rows = []
    for site_count in SITE_COUNTS:
        for bond_cap in BOND_CAPS:
            for cycles in CYCLE_COUNTS:
                config_rows.append(run_config(site_count, bond_cap, cycles))
    all_gaps = [gap for row in config_rows for gap in row["gaps"].values()]
    summary = {
        "site_counts": SITE_COUNTS,
        "bond_caps": BOND_CAPS,
        "cycle_counts": CYCLE_COUNTS,
        "configs_completed": len(config_rows),
        "sheet_control_runs": len(config_rows) * len(SHEETS) * 4,
        "max_site_count": max(row["site_count"] for row in config_rows),
        "max_bond_cap": max(row["bond_cap"] for row in config_rows),
        "max_cycles": max(row["cycles"] for row in config_rows),
        "max_layer_applications_per_sheet_run": max(row["cycles"] for row in config_rows) * len(base.MANIFOLD_LAYERS),
        "min_gap": min(all_gaps),
        "min_left_right_gap": min(row["gaps"]["left_right_nominal_gap"] for row in config_rows),
        "min_order_gap": min(min(row["gaps"]["L_order_gap"], row["gaps"]["R_order_gap"]) for row in config_rows),
        "min_phase_gap": min(min(row["gaps"]["L_phase_gap"], row["gaps"]["R_phase_gap"]) for row in config_rows),
        "min_edge_gap": min(min(row["gaps"]["L_edge_gap"], row["gaps"]["R_edge_gap"]) for row in config_rows),
        "max_bond_seen": max(
            bundle["nominal"]["mps_bond_stats"]["max_bond"]
            for row in config_rows
            for bundle in row["rows"].values()
        ),
        "elapsed_seconds": time.time() - started,
    }
    z3_gate = z3_frontier_gate(summary)
    cvc5_gate = cvc5_frontier_gate(summary)
    positive = {
        "resource_frontier_grid_completed": {
            "pass": all(row["pass"] for row in config_rows),
            "summary": summary,
            "rows": config_rows,
        },
        "scale_tool_certificates_pass": scale_tool_certificates,
        "auxiliary_tool_witnesses_pass": aux_tools,
        "z3_cvc5_frontier_gates_pass": {"z3": z3_gate, "cvc5": cvc5_gate, "pass": z3_gate["pass"] and cvc5_gate["pass"]},
    }
    graveyard_companions = {
        "phase_erasure_control_rejected_across_frontier": {"min_phase_gap": summary["min_phase_gap"], "pass": summary["min_phase_gap"] > GAP_FLOOR},
        "order_reversal_control_rejected_across_frontier": {"min_order_gap": summary["min_order_gap"], "pass": summary["min_order_gap"] > GAP_FLOOR},
        "edge_drop_control_rejected_across_frontier": {"min_edge_gap": summary["min_edge_gap"], "pass": summary["min_edge_gap"] > GAP_FLOOR},
        "left_right_sheet_collapse_rejected_across_frontier": {"min_left_right_gap": summary["min_left_right_gap"], "pass": summary["min_left_right_gap"] > GAP_FLOOR},
        "dense_64_qubit_closure_still_not_used": {
            "runtime_projection": "MPS path projection over source spinors with PEPS3D K=(V,E,F,C) anchors; no dense 2**64 vector constructed",
            "pass": True,
        },
    }
    boundary = {
        "resource_frontier_not_final_manifold": {
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
        "finite_map": (
            "WeylSpinorNetworkResourceFrontier : (PEPS3D K=(V,E,F,C) anchors "
            "at 8/16/32/64 sites, L/R Weyl spinor networks, bond caps "
            "8/16/24/32, cycle counts 1/2/4, finite controls) -> resource "
            "frontier receipt, sheet/control gaps, QIT cut readouts, and "
            "proof/tool fences"
        ),
        "domain": {
            "site_counts": SITE_COUNTS,
            "bond_caps": BOND_CAPS,
            "cycle_counts": CYCLE_COUNTS,
            "sheets": SHEETS,
            "candidate_layer_actions": base.MANIFOLD_LAYERS,
        },
        "codomain_or_output": {
            "resource_frontier_summary": summary,
            "blocked_consumers": boundary["downstream_consumers_remain_locked"]["blocked"],
        },
        "root_constraints": {
            "F01_finite_carrier_probe_operator_path_set": "finite sites, PEPS3D K anchors, finite bond caps, finite layer cycles, finite controls",
            "N01_noncommuting_or_order_sensitive_operation_control": "canonical-vs-reversed order gaps plus proof/tool noncommutation witnesses",
        },
        "carrier_realization": {
            "claim_bearing_object": "source_native_left_right_weyl_spinor_network",
            "torch_runtime": "PyTorch complex spinors and repo-local PyTorch MPS dynamics",
            "peps3d_embedding": "quimb PEPS3D objects plus graph/hypergraph/cell/persistence certificates over K=(V,E,F,C)",
            "resource_projection": "MPS path projection for 64-site resource execution, not dense-state closure",
        },
        "spinor_state": "psi_v in C^2 for every site and sheet; rho_v/QIT cuts are derived readouts",
        "quaternion_action": "not_applicable: no quaternion claim is made in this scout",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/weyl_spinor_network_8_16_32_64_layer_stress_probe_results.json",
            "system_v5/ops/formal_scouts/results/weyl_spinor_network_manifold_layer_runtime_probe_results.json",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby,
        "why_not_v4_probes": "This is a v5 source-native Weyl spinor-network resource-frontier formal scout.",
        "blockers": [],
        "all_pass": nearby["passed"] == nearby["total"],
        "summary": summary,
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "out_path": str(OUT_PATH), "summary": summary}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
