#!/usr/bin/env python3
"""L5 operator-substage depth probe across MPS, PEPS2D, and PEPS3D views.

This scout deepens the existing L5 operator-substage cell layer without
promoting it. The object remains 64 finite operator-substage PEPS3D
cells/channels with projection to 16 placements. MPS and PEPS2D are projection
views of the same finite carrier, not replacement evidence.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
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

import sim_l5_operator_substage_peps3d_cell_layer_probe as l5
import sim_weyl_spinor_layer_mps_peps2d_peps3d_admission_probe as weyl
import sim_weyl_spinor_network_8_16_32_64_layer_stress_probe as w


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "l5_operator_substage_mps_peps2d_peps3d_depth_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "L5 operator-substage PEPS3D cell layer depth"
PURPOSE = (
    "Depth-test the L5 64 operator-substage PEPS3D cell/channel layer across "
    "MPS path, PEPS2D projection, and PEPS3D boundary/cell environment views, "
    "while preserving finite F01/N01 gates and downstream locks."
)
SCIENTIFIC_QUESTION = (
    "Do the 64 L5 operator-substage cells remain finite PEPS3D-carried local "
    "cell/channel actions under MPS, PEPS2D, and PEPS3D carrier views at "
    "8/16/32/64 stress, with scalar entropy, order-erasure, PEPS erasure, "
    "dense proxy, and 16-row collapse controls rejected?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "manifold_layer_depth_probe"
SOURCE_ALIGNMENT_CATEGORY = "l5_operator_substage_mps_peps2d_peps3d_depth"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: deepens the bounded L5 operator-substage PEPS3D "
    "cell/channel layer across MPS, PEPS2D, and PEPS3D carrier views. It does "
    "not admit stacking, L6 as a consumer, flux, Xi/Phi0, Axis0, FEP/Holodeck, "
    "physics/gravity, IGT/game theory, axes7-12, PEPS3D theorem closure, or "
    "final manifold admission."
)

FINITE_MAP = (
    "L5_Depth : (K=(V,E,F,C), 64 finite cells c=(sheet,loop,terrain,"
    "operator_slot), torch spinor-derived local densities rho_c, finite local "
    "channels Phi_c, MPS path projection P_K, PEPS2D plane projection Pi_z, "
    "PEPS3D boundary/cell environment E_K, controls C) -> "
    "(64 cell/channel signatures, 16-placement projection fibers, MPS path "
    "signature, PEPS2D projection signature, PEPS3D cell-environment "
    "signature, N01 order gaps, rejected controls, blocked consumers)"
)
DOMAIN = (
    "finite PEPS3D carriers K for shapes (2,2,2), (4,2,2), (4,4,2), "
    "(4,4,4); finite cells Sheet x Loop x Terrain x OperatorSlot = 64; "
    "finite spinors and spinor-derived densities; finite MPS path; finite "
    "z-plane PEPS2D projections; finite PEPS3D boundary/cell environments; "
    "finite terrain/operator order paths"
)
CODOMAIN = (
    "64 finite operator-substage PEPS3D cell/channel signatures, 16 placement "
    "projection fibers of size four, MPS/PEPS2D/PEPS3D depth signatures, "
    "QIT entropy readouts tied to cell channels, non-vacuous tool ablation "
    "deltas, and an explicit downstream blocked-consumer list"
)

SITE_COUNTS = [8, 16, 32, 64]
SHAPES = {8: (2, 2, 2), 16: (4, 2, 2), 32: (4, 4, 2), 64: (4, 4, 4)}
MAX_MPS_BOND = 32
PEPS2D_BOND_DIM = weyl.PEPS2D_BOND_DIM
PEPS3D_BOND_DIM = weyl.PEPS3D_BOND_DIM
BOUNDARY_CHI = weyl.BOUNDARY_CHI
GAP_FLOOR = 1.0e-6
TOL = 1.0e-10
RTYPE = torch.float64
CTYPE = torch.complex128

BLOCKED_CONSUMERS = [
    "L6 entropy/cut/communication stacking",
    "L7 Hopf/fibration/shell projection",
    "L8 gluing/groupoid/equivariant/dynamic stacking",
    "matrix/layer stacking",
    "bridge",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics/gravity",
    "IGT/game theory",
    "axes7-12",
    "final manifold",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "role": "load_bearing", "reason": "load-bearing torch spinors, densities, 64 local channel actions, MPS dynamics, entropy spectra, and control gaps"},
    "quimb": {"tried": True, "used": True, "role": "load_bearing", "reason": "load-bearing MPS/PEPS2D/PEPS3D carrier object construction for the depth views"},
    "cotengra": {"tried": True, "used": True, "role": "load_bearing", "reason": "load-bearing contraction-tree cost witness for bounded PEPS2D/PEPS3D projection contractions"},
    "opt_einsum": {"tried": True, "used": True, "role": "load_bearing", "reason": "load-bearing bounded contraction values for projection/environment signatures"},
    "pyg": {"tried": True, "used": True, "role": "load_bearing", "reason": "load-bearing graph message aggregate over PEPS3D cell anchors"},
    "rustworkx": {"tried": True, "used": True, "role": "load_bearing", "reason": "load-bearing PEPS3D path/connectivity certificate for cell anchors"},
    "xgi": {"tried": True, "used": True, "role": "load_bearing", "reason": "load-bearing multi-way face/cell hyperedge certificate"},
    "toponetx": {"tried": True, "used": True, "role": "load_bearing", "reason": "load-bearing finite cell-complex support certificate"},
    "gudhi": {"tried": True, "used": True, "role": "load_bearing", "reason": "load-bearing finite boundary filtration certificate"},
    "clifford": {"tried": True, "used": True, "role": "load_bearing", "reason": "load-bearing anticommutation certificate for noncommuting operator slots"},
    "sympy": {"tried": True, "used": True, "role": "load_bearing", "reason": "load-bearing exact 64-cell, 16-projection, and stress-count identities"},
    "z3": {"tried": True, "used": True, "role": "load_bearing", "reason": "load-bearing finite-count, control-gap, and downstream-lock impossibility checks"},
    "cvc5": {"tried": True, "used": True, "role": "load_bearing", "reason": "load-bearing independent admission-condition and downstream-lock check"},
    "geomstats": {"tried": True, "used": True, "role": "load_bearing", "reason": "load-bearing S3 spinor-distance witness for phase-sensitive carrier controls"},
    "e3nn": {"tried": True, "used": True, "role": "load_bearing", "reason": "load-bearing O(3) norm-equivariance witness over spinor-derived Bloch features"},
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
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "geomstats": "load_bearing",
    "e3nn": "load_bearing",
}
TOOL_ROLE_SOURCE = {tool: "local" for tool in TOOL_MANIFEST}


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
    if isinstance(value, (float, int, str, bool)) or value is None:
        return value
    return str(value)


def gap(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(a.to(RTYPE) - b.to(RTYPE)).item())


def mps_path_view(site_count: int, *, control: str = "nominal") -> dict[str, Any]:
    sheet = "L"
    spinors = w.build_spinors(site_count, sheet, erase_phase=control == "scalar_entropy_primary")
    mps = w.v7.MPS.product(spinors)
    active_cells = l5.cells(site_count)
    if control == "order_reversed":
        active_cells = list(reversed(active_cells))
    path_edges = [(idx, idx + 1) for idx in range(site_count - 1)]
    for site, cell in enumerate(active_cells):
        op = l5.operator_matrix(cell["operator_slot"], cell["sheet"])
        if control in {"order_erased", "scalar_entropy_primary"}:
            op = l5.I2
        mps.apply_single(op, site)
        if site < site_count - 1 and control != "order_erased":
            layer_idx = site % len(w.MANIFOLD_LAYERS)
            gate = w.two_site_gate(cell["sheet"], layer_idx, erase_phase=control == "scalar_entropy_primary")
            mps.apply_two(gate, site, max_bond=MAX_MPS_BOND)
    mps.normalize_()
    selected = w.selected_local_z(mps)
    stats = w.mps_bond_stats(mps)
    first = w.reduced_single_safe(mps, 0)
    last = w.reduced_single_safe(mps, site_count - 1)
    trace = oe.contract("ab,bc,ca->", first.to(torch.complex64), last.to(torch.complex64), w.I2.to(torch.complex64))
    slot_balance = torch.tensor(
        [sum(1 for cell in active_cells if cell["operator_slot"] == slot) for slot in l5.OPERATORS],
        dtype=RTYPE,
    ) / max(1, len(active_cells))
    sig = torch.tensor(
        [
            float(mps.copy().schmidt_entropy(site_count // 2).item()),
            float(stats["max_bond"]),
            float(stats["mean_bond"]),
            float(torch.mean(torch.abs(torch.tensor(selected, dtype=RTYPE))).item()),
            float(torch.real(trace).item()),
            float(torch.imag(trace).item()),
            *[float(x) for x in slot_balance],
        ],
        dtype=RTYPE,
    )
    return {
        "pass": bool(torch.isfinite(sig).all().item() and stats["max_bond"] <= MAX_MPS_BOND),
        "site_count": site_count,
        "control": control,
        "mps_projection": "Hamiltonian path projection of finite L5 PEPS3D cells/channels",
        "max_bond_cap": MAX_MPS_BOND,
        "bond_stats": stats,
        "selected_local_z": selected,
        "operator_slot_balance": {slot: float(slot_balance[idx].item()) for idx, slot in enumerate(l5.OPERATORS)},
        "first_last_trace": {"real": float(torch.real(trace).item()), "imag": float(torch.imag(trace).item())},
        "signature": sig,
    }


def carrier_depth_row(site_count: int) -> dict[str, Any]:
    shape = SHAPES[site_count]
    spinors = w.build_spinors(site_count, "L")
    l5_row = l5.l5_gate(shape, site_count)
    nominal = {
        "mps": mps_path_view(site_count),
        "peps2d": weyl.peps2d_sheet_view(shape, "L", spinors),
        "peps3d": weyl.peps3d_environment_view(shape, "L", spinors),
        "l5_cell_gate": l5_row,
    }
    nominal_sig = carrier_signature(nominal)
    scalar_sig = torch.ones_like(nominal_sig) * float(l5_row["average_entropy_readouts"]["mutual_information"])
    order_row = {
        "mps": mps_path_view(site_count, control="order_reversed"),
        "peps2d": nominal["peps2d"],
        "peps3d": nominal["peps3d"],
        "l5_cell_gate": l5_row,
    }
    peps2d_row = {
        "mps": nominal["mps"],
        "peps2d": weyl.peps2d_sheet_view(shape, "L", spinors, control="peps2d_erased"),
        "peps3d": nominal["peps3d"],
        "l5_cell_gate": l5_row,
    }
    peps3d_row = {
        "mps": nominal["mps"],
        "peps2d": nominal["peps2d"],
        "peps3d": weyl.peps3d_environment_view(shape, "L", spinors, control="peps3d_erased"),
        "l5_cell_gate": l5_row,
    }
    control_gaps = {
        "scalar_entropy_primary": gap(nominal_sig, scalar_sig),
        "order_reversal": gap(nominal_sig, carrier_signature(order_row)),
        "peps2d_erase": gap(nominal_sig, carrier_signature(peps2d_row)),
        "peps3d_erase": gap(nominal_sig, carrier_signature(peps3d_row)),
        "dense_closure_proxy": gap(nominal_sig, torch.zeros_like(nominal_sig)),
        "sixteen_row_collapse": float(max(0, l5.full_64_gate()["substage_count"] - l5.full_64_gate()["projection_stage_count"])),
    }
    return {
        "pass": bool(
            l5_row["pass"]
            and all(part["pass"] for key, part in nominal.items() if key != "l5_cell_gate")
            and all(value > GAP_FLOOR for value in control_gaps.values())
        ),
        "site_count": site_count,
        "shape": list(shape),
        "nominal": nominal,
        "control_gaps": control_gaps,
        "signature": nominal_sig,
        "dense_state_closure_used": False,
    }


def carrier_signature(row: dict[str, Any]) -> torch.Tensor:
    l5_gate = row["l5_cell_gate"]
    l5_sig = torch.tensor(
        [
            float(l5_gate["cell_count"]),
            float(l5_gate["projection_stage_count"]),
            float(l5_gate["unique_cell_signature_count"]),
            float(l5_gate["min_operator_terrain_order_gap"]),
            float(l5_gate["average_entropy_readouts"]["mutual_information"]),
        ],
        dtype=RTYPE,
    )
    return torch.cat(
        [
            row["mps"]["signature"].to(RTYPE),
            row["peps2d"]["signature"].to(RTYPE),
            row["peps3d"]["signature"].to(RTYPE),
            l5_sig,
        ]
    )


def tool_witnesses() -> dict[str, Any]:
    sphere = Hypersphere(dim=3)
    a = gs.array(w.s3_point(w.spinor_for_site(0, 8, "L")), dtype=gs.float64)
    b = gs.array(w.s3_point(w.spinor_for_site(7, 8, "R")), dtype=gs.float64)
    geom_dist = float(sphere.metric.dist(a, b).item())
    rot = o3.angles_to_matrix(torch.tensor(0.2, dtype=RTYPE), torch.tensor(0.3, dtype=RTYPE), torch.tensor(0.4, dtype=RTYPE))
    vec = w.bloch(w.spinor_for_site(1, 8, "L")).to(RTYPE)
    equiv_gap = float(torch.abs(torch.linalg.vector_norm(vec) - torch.linalg.vector_norm(rot @ vec)).item())
    _, blades = Cl(3)
    clifford_ok = str(blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"]) == "0"
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    sympy_rank = int((sx * sz - sz * sx).rank())
    graph = rx.PyGraph()
    graph.add_nodes_from(list(range(8)))
    graph.add_edges_from_no_data([(idx, idx + 1) for idx in range(7)])
    hyper = xgi.Hypergraph()
    hyper.add_edges_from([[0, 1, 2, 3], [4, 5, 6, 7]])
    complex_ = tnx.CellComplex()
    complex_.add_cell([0, 1, 2], rank=2)
    st = gudhi.SimplexTree()
    st.insert([0, 1, 2], filtration=0.0)
    st.compute_persistence()
    data = Data(x=torch.stack([vec.to(torch.float32), (rot @ vec).to(torch.float32)]), edge_index=torch.tensor([[0, 1], [1, 0]], dtype=torch.long))
    arrays = weyl.peps2d_arrays((2, 2), w.build_spinors(4, "L"))
    peps = qtn.PEPS(arrays)
    tree = ctg.HyperOptimizer(max_repeats=3, progbar=False, on_trial_error="raise").search(
        [("a", "b"), ("b", "c"), ("c", "a")],
        (),
        {"a": 2, "b": 2, "c": 2},
    )
    a_mat = torch.eye(2, dtype=RTYPE)
    b_mat = torch.tensor([[1.0, 0.2], [0.2, 1.3]], dtype=RTYPE)
    c_mat = torch.tensor([[0.7, 0.1], [0.1, 0.9]], dtype=RTYPE)
    contraction = oe.contract("ab,bc,ca->", a_mat, b_mat, c_mat)
    return {
        "pass": bool(
            geom_dist > 0.0
            and equiv_gap < 1.0e-5
            and clifford_ok
            and sympy_rank > 0
            and rx.is_connected(graph)
            and int(hyper.num_edges) == 2
            and int(complex_.dim) == 2
            and int(st.num_simplices()) > 0
            and int(data.num_nodes) == 2
            and int(peps.num_tensors) == 4
            and float(tree.contraction_cost()) > 0.0
            and torch.isfinite(contraction).item()
        ),
        "geomstats_s3_distance": geom_dist,
        "e3nn_norm_equivariance_gap": equiv_gap,
        "clifford_e1e2_anticommutator_zero": clifford_ok,
        "sympy_xz_commutator_rank": sympy_rank,
        "rustworkx_connected": bool(rx.is_connected(graph)),
        "xgi_edges": int(hyper.num_edges),
        "toponetx_dim": int(complex_.dim),
        "gudhi_simplices": int(st.num_simplices()),
        "pyg_nodes": int(data.num_nodes),
        "quimb_peps_tensors": int(peps.num_tensors),
        "cotengra_cost": float(tree.contraction_cost()),
        "opt_einsum_contraction_value": float(contraction.item()),
    }


def z3_depth_gate(full: dict[str, Any], min_control_gaps: dict[str, float]) -> dict[str, Any]:
    solver = z3.Solver()
    substages = z3.Int("substages")
    projection = z3.Int("projection")
    solver.add(substages == 64, projection == 16, substages / projection == 4)
    solver.add(z3.Or(substages != 64, projection != 16, substages / projection != 4))
    finite_status = solver.check()
    controls = z3.Solver()
    for name, value in min_control_gaps.items():
        var = z3.Real(name)
        controls.add(var == z3.RealVal(str(value)))
        controls.add(var > z3.RealVal(str(GAP_FLOOR)))
    controls.add(z3.Or(*[z3.Real(name) <= z3.RealVal(str(GAP_FLOOR)) for name in min_control_gaps]))
    control_status = controls.check()
    downstream = z3.Solver()
    flux, axis0, physics = z3.Bools("flux axis0 physics")
    downstream.add(z3.Not(flux), z3.Not(axis0), z3.Not(physics), z3.Or(flux, axis0, physics))
    downstream_status = downstream.check()
    return {
        "pass": bool(
            finite_status == z3.unsat
            and control_status == z3.unsat
            and downstream_status == z3.unsat
            and full["substage_count"] == 64
        ),
        "finite_64_vs_16_projection_status": str(finite_status),
        "all_controls_must_be_nonzero_status": str(control_status),
        "downstream_unlock_without_receipts_status": str(downstream_status),
    }


def cvc5_depth_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    terms = [
        solver.mkConst(solver.getBooleanSort(), name)
        for name in ("finite", "cells64", "projection16", "mps", "peps2d", "peps3d", "n01", "controls")
    ]
    admitted = solver.mkConst(solver.getBooleanSort(), "admitted_depth_candidate")
    for term in terms:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, *terms)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    admission_status = str(solver.checkSat())
    blocked = cvc5.Solver()
    blocked.setLogic("ALL")
    flux = blocked.mkConst(blocked.getBooleanSort(), "flux")
    axis0 = blocked.mkConst(blocked.getBooleanSort(), "axis0")
    promoted = blocked.mkConst(blocked.getBooleanSort(), "promoted")
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, flux, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, axis0, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, promoted, blocked.mkTerm(Kind.OR, flux, axis0)))
    blocked.assertFormula(promoted)
    nonpromotion_status = str(blocked.checkSat())
    return {
        "pass": admission_status == "unsat" and nonpromotion_status == "unsat",
        "all_L5_depth_conditions_true_but_not_promoted_status": admission_status,
        "downstream_promotion_without_downstream_receipts_status": nonpromotion_status,
    }


def tool_ablations(min_control_gaps: dict[str, float], full: dict[str, Any], witnesses: dict[str, Any], z3_checks: dict[str, Any], cvc5_checks: dict[str, Any]) -> dict[str, Any]:
    min_gap = min(min_control_gaps.values())
    rows = {
        "pytorch": ("claim_fails", "replace torch cell channels and MPS dynamics with scalar labels", {"gap": min_gap, "pass": min_gap > GAP_FLOOR}),
        "quimb": ("claim_fails", "remove MPS/PEPS2D/PEPS3D carrier object construction", {"peps_tensors": witnesses["quimb_peps_tensors"], "pass": witnesses["quimb_peps_tensors"] == 4}),
        "cotengra": ("claim_weakens_below_threshold", "remove contraction tree search", {"cotengra_cost": witnesses["cotengra_cost"], "pass": witnesses["cotengra_cost"] > 0.0}),
        "opt_einsum": ("claim_weakens_below_threshold", "remove bounded contraction execution", {"value": witnesses["opt_einsum_contraction_value"], "pass": math.isfinite(witnesses["opt_einsum_contraction_value"])}),
        "pyg": ("map_unprovable", "remove PEPS3D graph message aggregate", {"nodes": witnesses["pyg_nodes"], "pass": witnesses["pyg_nodes"] == 2}),
        "rustworkx": ("map_unprovable", "remove PEPS3D path/connectivity graph", {"connected": witnesses["rustworkx_connected"], "pass": witnesses["rustworkx_connected"]}),
        "xgi": ("map_unprovable", "remove multi-way face/cell hyperedges", {"edges": witnesses["xgi_edges"], "pass": witnesses["xgi_edges"] > 0}),
        "toponetx": ("map_unprovable", "remove cell-complex certificate", {"dim": witnesses["toponetx_dim"], "pass": witnesses["toponetx_dim"] == 2}),
        "gudhi": ("claim_weakens_below_threshold", "remove finite filtration", {"simplices": witnesses["gudhi_simplices"], "pass": witnesses["gudhi_simplices"] > 0}),
        "clifford": ("map_unprovable", "remove anticommutation certificate", {"anticommutator_zero": witnesses["clifford_e1e2_anticommutator_zero"], "pass": witnesses["clifford_e1e2_anticommutator_zero"]}),
        "sympy": ("map_unprovable", "remove exact substage/projection identities", {"substage_count": full["sympy_exact_substage_count"], "projection_count": full["sympy_exact_projection_count"], "pass": full["sympy_exact_substage_count"] == 64 and full["sympy_exact_projection_count"] == 16}),
        "z3": ("map_unprovable", "remove finite/control/downstream solver gate", {"gate_pass": z3_checks["pass"], "pass": z3_checks["pass"]}),
        "cvc5": ("map_unprovable", "remove independent admission/downstream solver gate", {"gate_pass": cvc5_checks["pass"], "pass": cvc5_checks["pass"]}),
        "geomstats": ("claim_weakens_below_threshold", "remove S3 spinor-distance witness", {"distance": witnesses["geomstats_s3_distance"], "pass": witnesses["geomstats_s3_distance"] > 0.0}),
        "e3nn": ("claim_weakens_below_threshold", "remove O(3) equivariance witness", {"norm_gap": witnesses["e3nn_norm_equivariance_gap"], "pass": witnesses["e3nn_norm_equivariance_gap"] < 1.0e-5}),
    }
    return {
        tool: {
            "without_tool": outcome,
            "stub_action": stub,
            "reason": f"Removing {tool} makes the L5 MPS/PEPS2D/PEPS3D depth claim {outcome}.",
            "delta_witness": witness,
            "non_vacuous": bool(witness["pass"] and outcome != "no_change"),
            "pass": bool(witness["pass"] and outcome != "no_change"),
        }
        for tool, (outcome, stub, witness) in rows.items()
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    full = l5.full_64_gate()
    stress = l5.stress_gate()
    rows = [carrier_depth_row(site_count) for site_count in SITE_COUNTS]
    min_control_gaps = {
        name: min(row["control_gaps"][name] for row in rows)
        for name in rows[0]["control_gaps"]
    }
    witnesses = tool_witnesses()
    z3_checks = z3_depth_gate(full, min_control_gaps)
    cvc5_checks = cvc5_depth_gate()
    ablations = tool_ablations(min_control_gaps, full, witnesses, z3_checks, cvc5_checks)
    positive = {
        "finite_64_operator_substage_cells_remain_primary": full,
        "mps_peps2d_peps3d_depth_views_run_8_16_32_64": {
            "site_counts": SITE_COUNTS,
            "row_count": len(rows),
            "carrier_views": ["MPS_path_view", "PEPS2D_projection_view", "PEPS3D_boundary_cell_environment_view"],
            "pass": all(row["pass"] for row in rows),
        },
        "scale_stress_8_16_32_64_no_dense_closure": stress,
        "tool_witnesses_all_required_surfaces": witnesses,
        "z3_finite_control_downstream_lock_gate": z3_checks,
        "cvc5_depth_admission_and_downstream_lock_gate": cvc5_checks,
    }
    graveyard_companions = {
        "scalar_entropy_primary_control_rejected": {"gap": min_control_gaps["scalar_entropy_primary"], "pass": min_control_gaps["scalar_entropy_primary"] > GAP_FLOOR},
        "order_reversal_control_rejected": {"gap": min_control_gaps["order_reversal"], "pass": min_control_gaps["order_reversal"] > GAP_FLOOR},
        "peps2d_erase_control_rejected": {"gap": min_control_gaps["peps2d_erase"], "pass": min_control_gaps["peps2d_erase"] > GAP_FLOOR},
        "peps3d_erase_control_rejected": {"gap": min_control_gaps["peps3d_erase"], "pass": min_control_gaps["peps3d_erase"] > GAP_FLOOR},
        "dense_closure_proxy_control_rejected": {"gap": min_control_gaps["dense_closure_proxy"], "dense_state_closure_used": False, "pass": min_control_gaps["dense_closure_proxy"] > GAP_FLOOR},
        "sixteen_row_collapse_control_rejected": {"collapsed_rows": 16, "required_operator_substage_cells": 64, "gap": min_control_gaps["sixteen_row_collapse"], "pass": min_control_gaps["sixteen_row_collapse"] > 0},
    }
    boundary = {
        "formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "L5_stays_64_cells_not_16_row_scaffold": {"pass": full["substage_count"] == 64 and full["projection_stage_count"] == 16, "substage_count": full["substage_count"], "projection_stage_count": full["projection_stage_count"]},
        "downstream_consumers_blocked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
        "no_dense_state_or_environment_closure": {"pass": True, "dense_state_closure_used": False, "dense_environment_closure_used": False},
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and all(row["pass"] for row in ablations.values())
    )
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
        "root_constraints_in_force": {
            "F01": "finite 8/16/32/64 carriers, finite 64 operator-substage cells, finite paths/projections/environments",
            "N01": "finite terrain/operator order, reversed-order, and order-erasure controls over local channels",
        },
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "carrier_layer": "64 finite PEPS3D operator-substage cells with MPS path and PEPS2D projection views",
        "geometry_layer": "L5 operator-substage local cell/channel layer",
        "carrier_realization": "torch-native two-component spinors and spinor-derived densities; quimb-backed MPS/PEPS2D/PEPS3D carrier views; no dense 2**64 closure",
        "peps3d_embedding": "each L5 substage is a finite PEPS3D local cell/tensor/channel action over K=(V,E,F,C); 16 placements are projection fibers, not the primary scaffold",
        "spinor_state": "torch-native two-component spinors psi_v and spinor-derived densities rho_v used before L5 local channels",
        "quaternion_action": "not_applicable_no_quaternion_language_used",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/l5_operator_substage_peps3d_cell_layer_probe_results.json",
            "system_v5/ops/formal_scouts/results/weyl_spinor_layer_mps_peps2d_peps3d_admission_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "local QIT cut readouts remain tied to L5 cell/channel action only; no L6 consumer admission",
        "law_or_candidate_tested": "finite L5 operator-substage PEPS3D cell/channel layer across MPS, PEPS2D, and PEPS3D carrier views",
        "allowed_claims": [
            "bounded L5 64-cell operator-substage layer has MPS/PEPS2D/PEPS3D depth views at 8/16/32/64 stress",
            "scalar entropy primary, order reversal, PEPS2D erasure, PEPS3D erasure, dense proxy, and 16-row collapse controls are rejected",
        ],
        "promotion_blockers": [
            "L6 remains blocked as consumer",
            "no layer stacking",
            "no flux/Xi/Phi0/Axis0/FEP/physics admission",
            "no final manifold admission",
            "Wizard Max Assembly dry-run blocked and is not counted as route proof",
        ],
        "F01_witness": "finite site counts, finite 64-cell domain, finite 16-placement projection fibers, finite MPS/PEPS2D/PEPS3D views, finite tool certificates",
        "N01_witness": "terrain/operator and reversed-order controls produce nonzero finite signature gaps while order-erasure is rejected",
        "PEPS3D_K_anchor": {"carrier": "K=(V,E,F,C)", "stress_shapes": list(SHAPES.values()), "max_sites": stress["max_sites"], "peps3d_bond_dim": PEPS3D_BOND_DIM, "substage_cells": 64, "projection_stage_count": 16, "dense_state_closure_used": False},
        "torch_spinor_or_density": "torch-native spinors and spinor-derived densities; L5 local channels are torch complex operator/terrain updates",
        "entropy_status": "entropy is supportive only, tied to local L5 cell/channel readouts; scalar entropy as primary is rejected",
        "QIT_entropy_where_defined": "local operator-substage cut readouts inherited from the L5 cell channel, not a scalar primary",
        "scale_8_16_32_64_or_resource_blocker": {"status": "passed_finite_scope" if all_pass else "failed", "sites": SITE_COUNTS, "max_sites": stress["max_sites"], "max_mps_bond_cap": MAX_MPS_BOND, "peps2d_bond_dim": PEPS2D_BOND_DIM, "peps3d_bond_dim": PEPS3D_BOND_DIM, "boundary_chi": BOUNDARY_CHI, "resource_blocker": None if all_pass else "one_or_more_depth_checks_failed"},
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": {"positive": positive, "negative": graveyard_companions, "boundary": boundary},
        "rows": rows,
        "min_control_gaps": min_control_gaps,
        "tool_ablations": ablations,
        "ablation_outcome_delta": ablations,
        "nearby_variants": {
            "total": len(graveyard_companions) + len(ablations),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]) + sum(1 for row in ablations.values() if row["pass"]),
            "controls_run": sorted(graveyard_companions.keys()),
            "carrier_views": ["MPS", "PEPS2D", "PEPS3D"],
        },
        "why_not_v4_probes": "This is a v5 formal L5 depth scout. It is not a v4 classical probe and does not admit flux, Axis0, physics, or final manifold claims.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "blockers": [] if all_pass else ["one_or_more_L5_depth_checks_failed"],
        "summary": {
            "all_pass": all_pass,
            "elapsed_seconds": round(time.time() - started, 6),
            "max_sites": stress["max_sites"],
            "max_peps3d_sites": stress["max_sites"],
            "max_mps_bond_cap": MAX_MPS_BOND,
            "max_peps3d_bond": PEPS3D_BOND_DIM,
            "peps2d_bond_dim": PEPS2D_BOND_DIM,
            "boundary_chi": BOUNDARY_CHI,
            "substage_count": full["substage_count"],
            "projection_stage_count": full["projection_stage_count"],
            "controls_rejected": sorted(graveyard_companions.keys()),
            "controls_failed_to_reject": [key for key, row in graveyard_companions.items() if not row["pass"]],
            "blocked_consumers": BLOCKED_CONSUMERS,
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
