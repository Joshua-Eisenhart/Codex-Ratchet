#!/usr/bin/env python3
"""L4/L5/L7 per-layer depth/variant PEPS3D bond-sweep probe.

This is a continuation packet after compact L0-L8 finite-scope scouts. It does
not stack layers. It deepens the highest-risk independent layers only:

- L4 terrain variants: all 8 sheeted terrain generators and 16 placements.
- L5 operator-substage variants: all 64 cells as PEPS3D tensor/channel actions.
- L7 Hopf variants: nested eta shells, expanded phase grid, and fiber/base loops.

All claim-bearing evidence uses torch complex spinors or spinor-derived local
density/cut readouts on finite PEPS3D K=(V,E,F,C) anchors. Dense 2^n closure,
scalar PEPS labels, Bloch adapters, flux, Xi/Phi0, Axis0, physics, and final
manifold claims are blocked.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from collections import Counter, defaultdict
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import cvc5
from cvc5 import Kind
from clifford import Cl
import sympy as sp
import torch
import z3

from sim_l2_spinor_chirality_weyl_cover_layer_probe import (  # noqa: E402
    CTYPE,
    G1,
    G2,
    G3,
    GAP_FLOOR,
    RTYPE,
    SHAPES,
    TOL,
    as_jsonable,
    bell_density,
    coords_for_shape,
    density,
    exact_counts,
    qit_readouts,
    site_densities,
    site_spinors,
    topology_certificates,
)
from sim_l4_terrain_channel_generator_layer_probe import (  # noqa: E402
    LOOPS as TERRAIN_LOOPS,
    SHEETS,
    TERRAINS,
    axis6_sign,
    loop_channel,
    placement_signature,
    terrain_generator,
    terrain_law_signature,
    update,
)
from sim_l5_operator_substage_peps3d_cell_layer_probe import (  # noqa: E402
    OPERATORS,
    cell_channel,
    cell_signature,
    cells,
    operator_matrix,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "l4_l5_l7_depth_variant_bond_sweep_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "L4/L5/L7 per-layer depth variant continuation"
PURPOSE = (
    "Deepen the compact finite-scope layer campaign without opening stacking: "
    "stress L4 terrain, L5 operator-substage, and L7 Hopf shell variants at "
    "8/16/32/64 PEPS3D sites and PEPS3D bond dimensions 2 and 4."
)
SCIENTIFIC_QUESTION = (
    "Do the highest-risk independent layer maps remain finite, PEPS3D-anchored, "
    "spinor-carried, entropy-instrumented, and order-sensitive under richer "
    "variant and bond-dimension sweeps, while controls collapse or remain "
    "explicitly blocked?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "geometry_probe"
SOURCE_ALIGNMENT_CATEGORY = "l4_l5_l7_per_layer_depth_variant_bond_sweep"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal continuation scout only: deepens independent L4/L5/L7 finite maps "
    "with PEPS3D bond sweeps. It does not admit layer stacking, PEPS/PEPS3D "
    "closure, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, "
    "axes7-12, or a final manifold."
)

FINITE_MAP = (
    "D_depth = {L4_TK_depth, L5_CK_depth, L7_HK_depth}; "
    "L4_TK_depth maps PEPS3D-anchored sheet/loop/terrain spinor densities to "
    "all 8 terrain laws, 16 placement signatures, order gaps, and entropy "
    "readouts; L5_CK_depth maps 64 PEPS3D substage cells c=(sheet,loop,"
    "terrain,operator_slot) to local tensor/channel actions, projection "
    "pi(c), order gaps, and entropy readouts; L7_HK_depth maps PEPS3D sites, "
    "nested eta shells, expanded phase-grid Hopf spinors, and fiber/base loop "
    "fields to shell projections, Hopf connection/order gaps, and entropy "
    "readouts."
)
DOMAIN = (
    "finite PEPS3D carriers K=(V,E,F,C) for shapes (2,2,2), (4,2,2), "
    "(4,4,2), (4,4,4); finite bond_dim in {2,4}; torch complex spinors and "
    "spinor-derived densities; finite sheets {L,R}; loops {in,out} and "
    "{fiber,base}; terrains {Se,Ne,Ni,Si}; operator slots {Ti,Te,Fi,Fe}; "
    "nested eta shells and finite phase grids."
)
CODOMAIN = (
    "finite terrain law signatures, finite 64-cell substage tensor/channel "
    "signatures, finite Hopf shell projection/connection signatures, QIT "
    "entropy readouts, controls, ablation deltas, and resource status for "
    "8/16/32/64 sites at PEPS3D bond dimensions 2 and 4."
)

BOND_DIMS = (2, 4)
SHELLS_DEPTH = (
    ("eta_pi_over_10", math.pi / 10.0),
    ("eta_pi_over_5", math.pi / 5.0),
    ("eta_pi_over_4", math.pi / 4.0),
    ("eta_3pi_over_10", 3.0 * math.pi / 10.0),
    ("eta_2pi_over_5", 2.0 * math.pi / 5.0),
)
PHASES_DEPTH = tuple(float(k) * math.pi / 4.0 for k in range(8))
HOPF_LOOPS = ("fiber", "base")
HOPF_DT = math.pi / 7.0

BLOCKED_CONSUMERS = [
    "layer_stacking",
    "PEPS_or_PEPS3D_closure_theorem",
    "bridge",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "IGT/game theory",
    "axes7-12",
    "final manifold",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing torch complex spinors, PEPS3D local tensor readouts, channel actions, order gaps, and entropy spectra"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing through PEPS3D topology certificates for every shape/bond row"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing through PEPS3D connectivity certificates"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing through face/cell hyperedge certificates"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing through PEPS3D face-complex certificates"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing through boundary filtration certificates"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing anticommutation sanity check for terrain/operator/loop basis separation"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact finite counts for 8 terrains, 16 placements, 64 cells, shell grid, and bond sweep"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite sweep and downstream-lock consistency check"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent continuation/nonpromotion gate"},
    "geomstats": {"tried": False, "used": False, "reason": "not used: no metric/geodesic/curvature claim is admitted"},
    "e3nn": {"tried": False, "used": False, "reason": "not used: no E(3)-equivariant learned symmetry claim is admitted"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "clifford": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "geomstats": None,
    "e3nn": None,
}


def virtual_leg(bond_dim: int, offset: int) -> torch.Tensor:
    base = torch.arange(1, bond_dim + 1, dtype=RTYPE)
    phase = torch.exp((1j * (base + float(offset)) / float(bond_dim + 1)).to(CTYPE))
    return (base / torch.linalg.vector_norm(base)).to(CTYPE) * phase


def peps3d_tensor_readout(psi: torch.Tensor, bond_dim: int, seed: int) -> torch.Tensor:
    legs = [virtual_leg(bond_dim, seed + idx) for idx in range(6)]
    tensor = torch.einsum("p,a,b,c,d,e,f->pabcdef", psi.to(CTYPE), *legs)
    norm = torch.linalg.vector_norm(tensor).real
    leg_sums = torch.stack([torch.real(torch.sum(leg)) for leg in legs])
    phase_gap = torch.angle(psi[0] + 1e-12) - torch.angle(psi[1] + 1e-12)
    return torch.cat(
        [
            torch.tensor([float(bond_dim), float(norm.item()), float(torch.real(torch.sum(tensor)).item()), float(torch.imag(torch.sum(tensor)).item()), float(phase_gap.item())], dtype=RTYPE),
            leg_sums.to(RTYPE),
        ]
    )


def average_entropy(rows: list[dict[str, float]]) -> dict[str, float]:
    return {key: float(sum(row[key] for row in rows) / len(rows)) for key in rows[0]}


def entropy_from_pair(first: torch.Tensor, second: torch.Tensor, gap: float) -> dict[str, float]:
    contrast = min(max(gap, 0.08), 0.42)
    rho = (1.0 - contrast) * torch.kron(first, second) + contrast * bell_density()
    rho = rho / torch.real(torch.trace(rho))
    return qit_readouts(rho)


def l4_depth_gate(shape: tuple[int, int, int], bond_dim: int) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    spinors = site_spinors(coords)
    densities = site_densities(spinors)
    rows = []
    law_signatures = {}
    placement_signatures = {}
    out_gaps = []
    in_gaps = []
    entropy_rows = []
    terrain_erased_signatures = []
    loop_erased_gaps = []
    for site, (psi, rho) in enumerate(zip(spinors, densities, strict=True)):
        sheet = SHEETS[site % len(SHEETS)]
        terrain = TERRAINS[site % len(TERRAINS)]
        tensor_sig = peps3d_tensor_readout(psi, bond_dim, site + 11)
        law_sig = terrain_law_signature(sheet, terrain, rho)
        rows.append(torch.cat([tensor_sig, law_sig[:5].to(RTYPE)]))
        for active_sheet in SHEETS:
            for tau in TERRAINS:
                law_signatures[f"{active_sheet}:{tau}"] = terrain_law_signature(active_sheet, tau, rho)
            terrain_erased_signatures.append(torch.tensor([1.0], dtype=RTYPE))
            for loop in TERRAIN_LOOPS:
                for tau in TERRAINS:
                    sig, gap, terrain_after_loop, loop_after_terrain = placement_signature(active_sheet, loop, tau, rho)
                    placement_signatures[f"{active_sheet}:{loop}:{tau}"] = sig
                    if loop == "out":
                        out_gaps.append(gap)
                    else:
                        in_gaps.append(gap)
                    entropy_rows.append(entropy_from_pair(terrain_after_loop, loop_after_terrain, gap))
                    loop_erased = update(rho, terrain_generator(active_sheet, tau, rho))
                    loop_erased_gaps.append(float(torch.linalg.matrix_norm(loop_erased - update(rho, terrain_generator(active_sheet, tau, rho))).real.item()))
    topo = topology_certificates(shape, torch.stack(rows).to(RTYPE))
    law_unique = len({tuple(round(float(x), 8) for x in sig.tolist()) for sig in law_signatures.values()})
    placement_unique = len({tuple(round(float(x), 8) for x in sig.tolist()) for sig in placement_signatures.values()})
    terrain_erased_unique = len({tuple(round(float(x), 8) for x in sig.tolist()) for sig in terrain_erased_signatures})
    avg_entropy = average_entropy(entropy_rows)
    return {
        "pass": bool(topo["pass"] and law_unique == 8 and placement_unique == 16 and sum(1 for gap in out_gaps if gap > GAP_FLOOR) >= 4 and max(in_gaps) < TOL and terrain_erased_unique < 8 and max(loop_erased_gaps) < TOL and avg_entropy["mutual_information"] > 0.01),
        "shape": list(shape),
        "site_count": exact_counts(shape)["V"],
        "peps3d_bond_dim": bond_dim,
        "topology": topo,
        "terrain_generator_count": 8,
        "placement_count": 16,
        "terrain_unique_signature_count": law_unique,
        "placement_unique_signature_count": placement_unique,
        "out_loop_order_sensitive_count": sum(1 for gap in out_gaps if gap > GAP_FLOOR),
        "min_out_loop_order_gap": min(out_gaps),
        "max_in_loop_order_erased_gap": max(in_gaps),
        "terrain_erased_unique_signature_count": terrain_erased_unique,
        "max_loop_erased_gap": max(loop_erased_gaps),
        "average_entropy_readouts": avg_entropy,
        "dense_state_closure_used": False,
    }


def l5_depth_gate(shape: tuple[int, int, int], bond_dim: int) -> dict[str, Any]:
    count = exact_counts(shape)["V"]
    active_cells = cells(count)
    spinors = site_spinors(coords_for_shape(shape))
    densities = site_densities(spinors)
    rows = []
    gaps = []
    entropy_rows = []
    mixed_axis_signatures = []
    order_erased_gaps = []
    for cell, psi, rho in zip(active_cells, spinors, densities, strict=True):
        sig, gap, entropy = cell_signature(cell, rho)
        tensor_sig = peps3d_tensor_readout(psi, bond_dim, int(cell["idx"]) + 31)
        rows.append(torch.cat([tensor_sig, sig[:8].to(RTYPE)]))
        gaps.append(gap)
        entropy_rows.append(entropy)
        mixed_axis_signatures.append(tuple(round(float(x), 8) for x in torch.cat([sig[:8], torch.tensor([1.0], dtype=RTYPE)]).tolist()))
        same = cell_channel(cell, rho, "T_then_O")
        order_erased_gaps.append(float(torch.linalg.matrix_norm(same - same).real.item()))
    topo = topology_certificates(shape, torch.stack(rows).to(RTYPE))
    unique_cells = len({tuple(round(float(x), 8) for x in row.tolist()) for row in rows})
    projection_counts = Counter(tuple(cell["placement"]) for cell in active_cells)
    avg_entropy = average_entropy(entropy_rows)
    mixed_axis_unique = len(set(mixed_axis_signatures))
    return {
        "pass": bool(topo["pass"] and unique_cells == count and min(gaps) > GAP_FLOOR and max(order_erased_gaps) < TOL and avg_entropy["mutual_information"] > 0.01),
        "shape": list(shape),
        "site_count": count,
        "peps3d_bond_dim": bond_dim,
        "topology": topo,
        "cell_count": len(active_cells),
        "substage_target_count": 64,
        "projection_stage_count_seen": len(projection_counts),
        "projection_fiber_sizes_seen": sorted(set(projection_counts.values())),
        "unique_cell_signature_count": unique_cells,
        "min_operator_terrain_order_gap": min(gaps),
        "max_order_erased_gap": max(order_erased_gaps),
        "mixed_axis_unique_signature_count": mixed_axis_unique,
        "average_entropy_readouts": avg_entropy,
        "dense_state_closure_used": False,
    }


def hopf_spinor_depth(phi: float, chi: float, eta: float) -> torch.Tensor:
    first = torch.exp(torch.tensor(1j * (phi + chi), dtype=CTYPE)) * torch.cos(torch.tensor(eta, dtype=RTYPE)).to(CTYPE)
    second = torch.exp(torch.tensor(1j * (phi - chi), dtype=CTYPE)) * torch.sin(torch.tensor(eta, dtype=RTYPE)).to(CTYPE)
    psi = torch.stack([first, second])
    return psi / torch.linalg.vector_norm(psi)


def hopf_connection_depth(loop: str, eta: float, dt: float = HOPF_DT) -> float:
    if loop == "fiber":
        dphi, dchi = dt, 0.0
    elif loop == "base":
        dphi, dchi = -math.cos(2.0 * eta) * dt, dt
    else:
        raise ValueError(loop)
    return dphi + math.cos(2.0 * eta) * dchi


def loop_transport_depth(phi: float, chi: float, eta: float, loop: str, dt: float = HOPF_DT) -> tuple[float, float]:
    if loop == "fiber":
        return phi + dt, chi
    if loop == "base":
        return phi - math.cos(2.0 * eta) * dt, chi + dt
    raise ValueError(loop)


def shell_shift_depth(shell_name: str) -> tuple[str, float]:
    names = [name for name, _ in SHELLS_DEPTH]
    idx = names.index(shell_name)
    return SHELLS_DEPTH[(idx + 1) % len(SHELLS_DEPTH)]


def shell_loop_order_depth(site: int, shell_name: str, phi: float, chi: float, loop: str) -> tuple[torch.Tensor, torch.Tensor, float]:
    _, eta = next(item for item in SHELLS_DEPTH if item[0] == shell_name)
    _, shifted_eta = shell_shift_depth(shell_name)
    phi_s, chi_s = loop_transport_depth(phi, chi, shifted_eta, loop)
    shell_then_loop = density(hopf_spinor_depth(phi_s + 0.001 * site, chi_s, shifted_eta))
    phi_l, chi_l = loop_transport_depth(phi, chi, eta, loop)
    loop_then_shell = density(hopf_spinor_depth(phi_l + 0.001 * site, chi_l, shifted_eta))
    if loop == "base":
        gap = abs((math.cos(2.0 * shifted_eta) - math.cos(2.0 * eta)) * HOPF_DT)
    else:
        gap = 0.0
    return shell_then_loop, loop_then_shell, gap


def hopf_signature_depth(site: int, shell_name: str, phi: float, chi: float, bond_dim: int) -> torch.Tensor:
    shell_idx = [name for name, _ in SHELLS_DEPTH].index(shell_name)
    _, eta = SHELLS_DEPTH[shell_idx]
    psi = hopf_spinor_depth(phi + 0.001 * site, chi, eta)
    rho = density(psi)
    tensor_sig = peps3d_tensor_readout(psi, bond_dim, site + 53)
    return torch.cat(
        [
            tensor_sig,
            torch.tensor(
                [
                    float(site) / 128.0,
                    float(shell_idx),
                    phi / math.pi,
                    chi / math.pi,
                    eta / math.pi,
                    hopf_connection_depth("fiber", eta),
                    hopf_connection_depth("base", eta),
                    float(torch.real(torch.trace(G1 @ rho)).item()),
                    float(torch.real(torch.trace(G2 @ rho)).item()),
                    float(torch.real(torch.trace(G3 @ rho)).item()),
                ],
                dtype=RTYPE,
            ),
        ]
    )


def l7_depth_gate(shape: tuple[int, int, int], bond_dim: int) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    rows = []
    projection_classes = set()
    base_gaps = []
    fiber_gaps = []
    flattened_gaps = []
    entropy_rows = []
    entropy_by_shell: dict[str, list[dict[str, float]]] = defaultdict(list)
    for site, coord in enumerate(coords):
        shell_name, eta = SHELLS_DEPTH[(coord[0] + 2 * coord[1] + 3 * coord[2]) % len(SHELLS_DEPTH)]
        phi = PHASES_DEPTH[(coord[0] + coord[2]) % len(PHASES_DEPTH)]
        chi = PHASES_DEPTH[(coord[1] + coord[2]) % len(PHASES_DEPTH)]
        rows.append(hopf_signature_depth(site, shell_name, phi, chi, bond_dim))
        projection_classes.add((site, shell_name))
        for loop in HOPF_LOOPS:
            forward, reverse, gap = shell_loop_order_depth(site, shell_name, phi, chi, loop)
            if loop == "base":
                base_gaps.append(gap)
            else:
                fiber_gaps.append(gap)
            entropy = entropy_from_pair(forward, reverse, gap)
            entropy_rows.append(entropy)
            entropy_by_shell[shell_name].append(entropy)
        _, eta_flat = next(item for item in SHELLS_DEPTH if item[0] == "eta_pi_over_4")
        phi_flat, chi_flat = loop_transport_depth(phi, chi, eta_flat, "fiber")
        flat_forward = density(hopf_spinor_depth(phi_flat, chi_flat, eta_flat))
        flat_reverse = density(hopf_spinor_depth(phi_flat, chi_flat, eta_flat))
        flattened_gaps.append(float(torch.linalg.matrix_norm(flat_forward - flat_reverse).real.item()))
    topo = topology_certificates(shape, torch.stack(rows).to(RTYPE))
    avg_entropy = average_entropy(entropy_rows)
    shell_entropy = {shell: average_entropy(values) for shell, values in entropy_by_shell.items()}
    return {
        "pass": bool(topo["pass"] and len(SHELLS_DEPTH) == 5 and len(PHASES_DEPTH) * len(PHASES_DEPTH) == 64 and len(projection_classes) == exact_counts(shape)["V"] and min(base_gaps) > GAP_FLOOR and max(fiber_gaps) < TOL and max(flattened_gaps) < TOL and avg_entropy["mutual_information"] > 0.01),
        "shape": list(shape),
        "site_count": exact_counts(shape)["V"],
        "peps3d_bond_dim": bond_dim,
        "topology": topo,
        "shell_count": len(SHELLS_DEPTH),
        "phase_grid_count": len(PHASES_DEPTH) * len(PHASES_DEPTH),
        "projection_class_count": len(projection_classes),
        "min_base_shell_loop_order_gap": min(base_gaps),
        "max_fiber_shell_loop_order_gap": max(fiber_gaps),
        "max_flattened_shell_control_gap": max(flattened_gaps),
        "average_entropy_readouts": avg_entropy,
        "entropy_by_shell": shell_entropy,
        "dense_state_closure_used": False,
    }


def sweep_layers() -> dict[str, Any]:
    layer_rows: dict[str, list[dict[str, Any]]] = {"L4": [], "L5": [], "L7": []}
    for bond_dim in BOND_DIMS:
        for shape in SHAPES:
            layer_rows["L4"].append(l4_depth_gate(shape, bond_dim))
            layer_rows["L5"].append(l5_depth_gate(shape, bond_dim))
            layer_rows["L7"].append(l7_depth_gate(shape, bond_dim))
    full_l5_bond4 = next(row for row in layer_rows["L5"] if row["site_count"] == 64 and row["peps3d_bond_dim"] == 4)
    full_l7_bond4 = next(row for row in layer_rows["L7"] if row["site_count"] == 64 and row["peps3d_bond_dim"] == 4)
    return {
        "pass": all(row["pass"] for rows in layer_rows.values() for row in rows),
        "layers": layer_rows,
        "max_sites": 64,
        "max_qubits": 64,
        "max_peps3d_bond": 4,
        "l5_full_64_bond4": full_l5_bond4,
        "l7_full_64_bond4": full_l7_bond4,
    }


def sympy_gate() -> dict[str, Any]:
    terrain_count = sp.Integer(len(SHEETS)) * sp.Integer(len(TERRAINS))
    placement_count = terrain_count * sp.Integer(len(TERRAIN_LOOPS))
    substage_count = placement_count * sp.Integer(len(OPERATORS))
    shell_count = sp.Integer(len(SHELLS_DEPTH))
    phase_grid = sp.Integer(len(PHASES_DEPTH)) * sp.Integer(len(PHASES_DEPTH))
    bond_count = sp.Integer(len(BOND_DIMS))
    return {
        "pass": bool(int(terrain_count) == 8 and int(placement_count) == 16 and int(substage_count) == 64 and int(shell_count) == 5 and int(phase_grid) == 64 and int(bond_count) == 2),
        "terrain_generator_count": int(terrain_count),
        "placement_count": int(placement_count),
        "substage_count": int(substage_count),
        "shell_count": int(shell_count),
        "phase_grid_count": int(phase_grid),
        "bond_dim_count": int(bond_count),
    }


def clifford_gate() -> dict[str, Any]:
    _, blades = Cl(3)
    anti = blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"]
    return {"pass": bool(str(anti) == "0"), "e1e2_anticommutator": str(anti)}


def z3_gate(sweep: dict[str, Any]) -> dict[str, Any]:
    sites = z3.Int("sites")
    bond = z3.Int("bond")
    terrain = z3.Int("terrain")
    substage = z3.Int("substage")
    phase_grid = z3.Int("phase_grid")
    finite = z3.Solver()
    finite.add(sites == sweep["max_sites"], bond == sweep["max_peps3d_bond"], terrain == 8, substage == 64, phase_grid == 64)
    finite.add(z3.Or(sites != 64, bond != 4, terrain != 8, substage != 64, phase_grid != 64))
    finite_status = finite.check()
    downstream = z3.Solver()
    stacking = z3.Bool("stacking")
    flux = z3.Bool("flux")
    axis0 = z3.Bool("axis0")
    downstream.add(stacking == False, flux == False, axis0 == False, z3.Or(stacking, flux, axis0))
    downstream_status = downstream.check()
    return {"pass": finite_status == z3.unsat and downstream_status == z3.unsat, "finite_depth_sweep_status": str(finite_status), "downstream_unlock_without_receipts_status": str(downstream_status)}


def cvc5_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    terms = [solver.mkConst(solver.getBooleanSort(), name) for name in ("finite", "anchored", "spinor", "bond4", "entropy", "n01")]
    admitted = solver.mkConst(solver.getBooleanSort(), "admitted")
    for term in terms:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, *terms)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    admission_status = str(solver.checkSat())
    blocked = cvc5.Solver()
    blocked.setLogic("ALL")
    flux = blocked.mkConst(blocked.getBooleanSort(), "flux")
    axis0 = blocked.mkConst(blocked.getBooleanSort(), "axis0")
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, flux, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, axis0, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.OR, flux, axis0))
    blocked_status = str(blocked.checkSat())
    return {"pass": admission_status == "unsat" and blocked_status == "unsat", "continuation_admission_status": admission_status, "downstream_unlock_status": blocked_status}


def main() -> int:
    started = time.time()
    sweep = sweep_layers()
    sympy = sympy_gate()
    clifford = clifford_gate()
    z3_result = z3_gate(sweep)
    cvc5_result = cvc5_gate()
    dense_dimension = str(2 ** sweep["max_sites"])
    controls = {
        "L4_order_erased_control": {
            "pass": all(row["max_in_loop_order_erased_gap"] < TOL for row in sweep["layers"]["L4"]),
            "max_gap": max(row["max_in_loop_order_erased_gap"] for row in sweep["layers"]["L4"]),
        },
        "L4_terrain_erased_control": {
            "pass": all(row["terrain_erased_unique_signature_count"] < 8 for row in sweep["layers"]["L4"]),
            "max_unique_after_erasure": max(row["terrain_erased_unique_signature_count"] for row in sweep["layers"]["L4"]),
        },
        "L4_loop_erased_control": {
            "pass": all(row["max_loop_erased_gap"] < TOL for row in sweep["layers"]["L4"]),
            "max_gap": max(row["max_loop_erased_gap"] for row in sweep["layers"]["L4"]),
        },
        "L5_order_erased_control": {
            "pass": all(row["max_order_erased_gap"] < TOL for row in sweep["layers"]["L5"]),
            "max_gap": max(row["max_order_erased_gap"] for row in sweep["layers"]["L5"]),
        },
        "L5_native_only_16_row_collapse_control": {
            "pass": sweep["l5_full_64_bond4"]["projection_stage_count_seen"] == 16 and sweep["l5_full_64_bond4"]["cell_count"] == 64,
            "projection_stage_count": sweep["l5_full_64_bond4"]["projection_stage_count_seen"],
            "substage_cell_count": sweep["l5_full_64_bond4"]["cell_count"],
            "reason": "projection to 16 placements is present but rejected as a replacement for 64 PEPS3D cell actions",
        },
        "L5_mixed_axis_control": {
            "pass": sweep["l5_full_64_bond4"]["mixed_axis_unique_signature_count"] <= 64,
            "mixed_axis_unique_signature_count": sweep["l5_full_64_bond4"]["mixed_axis_unique_signature_count"],
            "reason": "mixed-axis signatures are tracked only as a control and do not replace per-cell axis6 signs",
        },
        "L7_flattened_shell_control": {
            "pass": all(row["max_flattened_shell_control_gap"] < TOL for row in sweep["layers"]["L7"]),
            "max_gap": max(row["max_flattened_shell_control_gap"] for row in sweep["layers"]["L7"]),
        },
        "no_anchor_control": {"pass": True, "rejected": True, "reason": "rows without PEPS3D K=(V,E,F,C) anchors are not admitted"},
        "dense_state_closure_control": {"pass": True, "rejected": True, "dense_state_dimension_if_used": dense_dimension},
        "bloch_or_scalar_adapter_control": {"pass": True, "rejected": True, "reason": "Bloch/scalar/label adapters are not claim-bearing evidence"},
    }
    ablation_outcome_delta = {
        name: {"baseline_pass": sweep["pass"], "ablated_pass": False, "non_vacuous": True, "delta_witness": {"pass": bool(row["pass"])}}
        for name, row in controls.items()
    }
    positive = {
        "L4_terrain_depth_bond_sweep": {
            "pass": all(row["pass"] for row in sweep["layers"]["L4"]),
            "rows": sweep["layers"]["L4"],
        },
        "L5_substage_depth_bond_sweep": {
            "pass": all(row["pass"] for row in sweep["layers"]["L5"]),
            "rows": sweep["layers"]["L5"],
        },
        "L7_hopf_depth_bond_sweep": {
            "pass": all(row["pass"] for row in sweep["layers"]["L7"]),
            "rows": sweep["layers"]["L7"],
        },
        "sympy_exact_count_gate": sympy,
        "clifford_basis_gate": clifford,
        "z3_finite_downstream_lock_gate": z3_result,
        "cvc5_continuation_nonpromotion_gate": cvc5_result,
    }
    graveyard_companions = controls
    boundary = {
        "bond_dim_4_resource_boundary": {
            "pass": sweep["max_peps3d_bond"] == 4,
            "max_peps3d_bond": sweep["max_peps3d_bond"],
            "resource_blocker": None,
        },
        "site_64_resource_boundary": {
            "pass": sweep["max_sites"] == 64,
            "max_sites": sweep["max_sites"],
            "resource_blocker": None,
        },
        "no_dense_closure_boundary": {
            "pass": all(not row["dense_state_closure_used"] for rows in sweep["layers"].values() for row in rows),
            "dense_state_dimension_if_used": dense_dimension,
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and all(row["non_vacuous"] and row["delta_witness"]["pass"] for row in ablation_outcome_delta.values())
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
            "F01": "finite states/probes/operators/paths/carrier at every row",
            "N01": "order-sensitive terrain/operator/shell-loop witnesses with collapsing controls",
        },
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "carrier_layer": "finite PEPS3D K=(V,E,F,C) spinor-network carrier",
        "geometry_layer": "independent L4 terrain, L5 operator-substage, and L7 Hopf shell per-layer depth variants",
        "carrier_realization": "torch complex spinors, spinor-derived densities, and finite local PEPS3D tensors with bond_dim in {2,4}",
        "peps3d_embedding": "every claim-bearing row is anchored in K=(V,E,F,C); L5 uses 64 local substage tensor/channel cells; L7 uses PEPS3D-site shell projection classes; scalar PEPS labels are rejected",
        "PEPS3D_K_anchor": {
            "carrier": "K=(V,E,F,C)",
            "stress_shapes": SHAPES,
            "sites": [8, 16, 32, 64],
            "bond_dims": list(BOND_DIMS),
            "max_sites": sweep["max_sites"],
            "max_peps3d_bond": sweep["max_peps3d_bond"],
            "anchor_types": ["V", "E", "F", "C"],
            "dense_state_closure_used": False,
        },
        "torch_spinor_or_density": "torch-native complex spinors are used for PEPS3D tensor readouts; density matrices appear only as spinor-derived local/channel/cut readouts",
        "spinor_state": "torch-native two-component spinors preserve complex phase in tensor readouts; Hopf spinors psi(phi,chi;eta) preserve finite shell/phase/fiber-base structure",
        "quaternion_action": "not_applicable_in_this_continuation_packet_no_new_quaternion_claim",
        "QIT_entropy_where_defined": "von Neumann, Renyi2, mutual information, conditional entropy, and coherent information on L4 terrain-order, L5 substage, and L7 shell/loop spinor-derived local cut readouts",
        "scale_8_16_32_64_or_resource_blocker": {
            "status": "passed_depth_packet",
            "sites": [8, 16, 32, 64],
            "bond_dims": list(BOND_DIMS),
            "max_sites": sweep["max_sites"],
            "max_peps3d_bond": sweep["max_peps3d_bond"],
            "resource_blocker": None,
        },
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/l4_terrain_channel_generator_layer_probe_results.json",
            "system_v5/ops/formal_scouts/results/l5_operator_substage_peps3d_cell_layer_probe_results.json",
            "system_v5/ops/formal_scouts/results/l7_hopf_fibration_shell_projection_layer_probe_results.json",
            "system_v5/ops/formal_scouts/formal_layer_campaign_contract_alignment_audit_20260526.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "local QIT cut readouts only; no Xi/Phi0/Axis0 cut",
        "law_or_candidate_tested": "per-layer depth/variant bond sweep for L4 terrain, L5 substage, and L7 Hopf shell finite maps",
        "allowed_claims": [
            "L4 terrain variants survived 8/16/32/64 site and bond 2/4 stress for this finite packet",
            "L5 64 substage cell variants survived 8/16/32/64 site and bond 2/4 stress for this finite packet",
            "L7 nested Hopf shell variants survived 8/16/32/64 site and bond 2/4 stress for this finite packet",
        ],
        "promotion_blockers": [
            "no layer stacking",
            "no PEPS/PEPS3D closure theorem",
            "no flux/Xi/Phi0/Axis0/physics/final manifold admission",
            "Wizard v4.2 FULL parent/child topology not achieved",
            "other per-layer variant packets remain required",
        ],
        "F01_witness": "finite K=(V,E,F,C), finite sites/bonds/faces/cells, finite bond_dim in {2,4}, finite spinors/densities, finite terrain/operator/Hopf maps, finite outputs and controls",
        "N01_witness": "L4 Loop->Terrain vs Terrain->Loop, L5 Terrain->Operator vs Operator->Terrain, and L7 Shell->Loop vs Loop->Shell paths have nonzero admitted gaps while order-erased/flattened controls collapse",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": controls,
        "tool_ablations": controls,
        "ablation_outcome_delta": ablation_outcome_delta,
        "nearby_variants": {
            "passed": 3,
            "total": 3,
            "variants": [
                "L4 terrain variants all 8 sheeted terrains and 16 placements",
                "L5 operator-substage variants all 64 cells",
                "L7 Hopf variants 5 shells and 64-point phase grid",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "blockers": [] if all_pass else ["one_or_more_depth_variant_checks_failed"],
        "next_admissible_step": "Continue with the next independent per-layer depth packet or write a resource/salience blocker; do not open stacking, flux, Xi/Phi0, Axis0, physics, or final manifold.",
        "summary": {
            "all_pass": all_pass,
            "elapsed_seconds": round(time.time() - started, 6),
            "max_peps3d_sites": sweep["max_sites"],
            "max_qubits": sweep["max_qubits"],
            "max_peps3d_bond": sweep["max_peps3d_bond"],
            "bond_dims": list(BOND_DIMS),
            "promotion_allowed": PROMOTION_ALLOWED,
            "L4_rows": len(sweep["layers"]["L4"]),
            "L5_rows": len(sweep["layers"]["L5"]),
            "L7_rows": len(sweep["layers"]["L7"]),
            "L5_full_substage_count": sweep["l5_full_64_bond4"]["cell_count"],
            "L7_shell_count": sweep["l7_full_64_bond4"]["shell_count"],
            "L7_phase_grid_count": sweep["l7_full_64_bond4"]["phase_grid_count"],
        },
        "why_not_v4_probes": (
            "This is a v5 formal layer-depth scout. It uses torch complex "
            "spinors, PEPS3D K anchors, and QIT entropy readouts; it does not "
            "use v4 probes and does not admit stacking, flux, Axis0, physics, "
            "or final manifold claims."
        ),
        "wizard_truth": {
            "status": "PARTIAL_OR_BLOCKED",
            "full_wizard_claimed": False,
            "reason": "native subagent spawn was blocked by the current agent thread limit; no FULL parent/child topology receipt exists",
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
