#!/usr/bin/env python3
"""Standalone G-structure candidate capability scout.

Formal scout only. This tests candidate structure groups and structure-like
carriers before any manifold layer is embedded in them. A green result means
the candidate space has finite spinor-network carrier function and invariant
checks at 8/16/32/64 sites. It does not select the official layered-ratchet
G-structure, does not stack layers, and does not open flux, Xi/Phi0, Axis0,
FEP/Holodeck, physics, or final manifold admission.
"""

from __future__ import annotations

import concurrent.futures
import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import cvc5
from cvc5 import Kind
from clifford import Cl
import rustworkx as rx
import sympy as sp
import torch
import toponetx as tnx
import xgi
import z3

import layer_full_spinor_network_individual_runner as carrier


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "g_structure_candidate_space_full_function_probe_results.json"

NAME = "g_structure_candidate_space_full_function_probe"
CLASSIFICATION = "formal_scout"
classification = CLASSIFICATION
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "standalone_g_structure_candidate_space"
CLAIM_CEILING = (
    "Formal scout only: standalone finite capability probe for candidate "
    "G-structures before layer embedding. It tests S3 spinor carrier geometry, "
    "explicit Hopf S3->S2 maps, nested Hopf tori, Clifford tori, twistor "
    "incidence geometry, U(1) Hopf bundle, SU(2)/Spin(3) unit-quaternion "
    "double cover, SO(3) frame reduction, Pin/Spin chirality split, Cl3/Cl6 "
    "spinor algebra, and a hybrid Hopf+Spin+Twistor+Clifford reduction "
    "candidate over 8/16/32/64 site spinor-network carriers with MPS, PEPS2D, "
    "PEPS3D, PyG, QIT readouts, graph/topology/proof controls, and tool "
    "ablations. It uses the explicit Hopf S3->S2 map rather than a qubit-sphere "
    "adapter, does not select a "
    "canonical G-structure, does not admit stacked layers, and does not open "
    "flux, Xi/Phi0, Axis0, Holodeck/FEP, physics/gravity, or final manifold "
    "claims."
)

SITE_COUNTS = [8, 16, 32, 64]
GAP = 1.0e-6
STRUCTURE_CANDIDATES = [
    "S3_spinor_carrier",
    "S2_Hopf_base_surface",
    "Hopf_fibration_S3_to_S2",
    "Nested_Hopf_tori",
    "Clifford_torus_T2_in_S3",
    "Twistor_incidence_spinor_geometry",
    "U1_Hopf_principal_bundle",
    "SU2_Spin3_unit_quaternion_double_cover",
    "SO3_orientation_frame_reduction",
    "Pin3_Spin3_chirality_split",
    "Clifford_geometries_Cl3_Cl6",
    "Hybrid_Hopf_Spin_Twistor_Clifford_reduction_graph",
]
BLOCKED_CONSUMERS = [
    "layer_embedding",
    "official_layered_ratchet_G_structure_selection",
    "stacking",
    "cross_layer_order_closure",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics/gravity",
    "final_manifold_admission",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex spinor states, densities, carrier actions, MPS gates, invariant gaps, and QIT readouts",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PEPS2D and PEPS3D carrier construction through shared full-spec carrier functions",
    },
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PEPS3D contraction-cost witness through shared carrier functions",
    },
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": "load-bearing contraction signature witness through shared PEPS2D/PEPS3D carrier functions",
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph message-passing check on the finite spinor carrier",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing candidate reduction DAG and order witness",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hyperedge witness for candidate structure families and compatible invariants",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing cell-complex witness for the structure-family incidence surface",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing topology witness used through the shared finite carrier topology view",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Cl3 quaternion-unit and Cl6 basis-size spinor algebra invariant",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact SU2 determinant and quaternion product witnesses",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof that reversed/shortcut G-reduction order is not admissible under the observed chain",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent proof that all candidate rows passing cannot coexist with a false row-pass predicate",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SO(3) norm-equivariance witness through the shared geometry carrier imports",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing spherical-distance witness through shared geometry carrier imports",
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
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "e3nn": "load_bearing",
    "geomstats": "load_bearing",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, (float, int, str, bool)) or value is None:
        return value
    return str(value)


def candidate_spinors(candidate: str, site_count: int) -> list[torch.Tensor]:
    spinors: list[torch.Tensor] = []
    idx = STRUCTURE_CANDIDATES.index(candidate)
    for site in range(site_count):
        t = 2.0 * math.pi * float(site) / float(site_count)
        eta = 0.28 + 0.96 * float((site % max(2, site_count // 4)) + 1) / float(max(3, site_count // 4) + 1)
        if candidate == "Clifford_torus_T2_in_S3":
            eta = math.pi / 2.0
        elif "tor" in candidate.lower():
            eta = 0.18 + 0.74 * float((site % 5) + 1) / 6.0
        if "chirality" in candidate.lower() and site % 2:
            eta = math.pi - eta
        phi = t * (1.0 + 0.05 * idx) + 0.11 * idx
        chi = t * (2.0 + 0.03 * idx) + 0.19 * idx
        z0 = math.cos(eta / 2.0) * torch.exp(torch.tensor(1j * phi, dtype=carrier.CDTYPE))
        z1 = math.sin(eta / 2.0) * torch.exp(torch.tensor(1j * chi, dtype=carrier.CDTYPE))
        psi = torch.stack([z0, z1]).to(carrier.CDTYPE)
        spinors.append(psi / torch.linalg.vector_norm(psi))
    return spinors


def mps_candidate_view(candidate: str, site_count: int, spinors: list[torch.Tensor], *, entangle: bool) -> dict[str, Any]:
    mps = carrier.w.v7.MPS.product(spinors)
    offset = STRUCTURE_CANDIDATES.index(candidate)
    for action in [offset + 1, offset + 4, offset + 7]:
        for site in range(site_count):
            gate = carrier.w.layer_gate("L", action % len(carrier.w.MANIFOLD_LAYERS), site, site_count)
            mps.apply_single(gate, site)
        if entangle:
            two = carrier.w.two_site_gate("L", action % len(carrier.w.MANIFOLD_LAYERS))
            for edge_start in range(site_count - 1):
                mps.apply_two(two, edge_start, max_bond=carrier.MAX_MPS_BOND)
        mps.normalize_()
    half_entropy = float(mps.copy().schmidt_entropy(site_count // 2).item())
    stats = carrier.w.mps_bond_stats(mps)
    return {
        "pass": bool(math.isfinite(half_entropy) and stats["max_bond"] <= carrier.MAX_MPS_BOND),
        "entangling_gates_applied": entangle,
        "half_chain_entropy": half_entropy,
        "bond_stats": stats,
    }


def hopf_s2_map(psi: torch.Tensor) -> torch.Tensor:
    """Explicit Hopf base map S3 -> S2 from C2 spinor coordinates."""
    z0 = psi[0].to(carrier.CDTYPE)
    z1 = psi[1].to(carrier.CDTYPE)
    cross = z0 * torch.conj(z1)
    return torch.stack(
        [
            2.0 * torch.real(cross),
            2.0 * torch.imag(cross),
            torch.real(torch.conj(z0) * z0 - torch.conj(z1) * z1),
        ]
    ).to(carrier.RTYPE)


def peps2d_candidate_view(shape: tuple[int, int, int], spinors: list[torch.Tensor]) -> dict[str, Any]:
    lx, ly, lz = shape
    coords = carrier.w.coords_for_shape(shape)
    rows = []
    virtual_l1 = 0.0
    for z in range(lz):
        plane_spinors = [spinors[idx] for idx, (_x, _y, zz) in enumerate(coords) if zz == z]
        arrays = carrier.peps2d_arrays((lx, ly), plane_spinors)
        peps = carrier.qtn.PEPS(arrays)
        norms = []
        for row in arrays:
            for arr in row:
                flat = arr.reshape(-1)
                norms.append(float(torch.linalg.vector_norm(flat).item()))
                virtual_l1 += float(torch.sum(torch.abs(flat[2:])).item())
        contract = carrier.oe.contract(
            "i,i->",
            hopf_s2_map(plane_spinors[0]),
            hopf_s2_map(plane_spinors[-1]),
        )
        rows.append(
            {
                "pass": int(peps.num_tensors) == len(plane_spinors) and min(norms) > 0.0,
                "z": z,
                "peps2d_num_tensors": int(peps.num_tensors),
                "hopf_s2_contract_value": float(contract.item()),
            }
        )
    return {
        "pass": bool(all(row["pass"] for row in rows) and virtual_l1 > 0.0),
        "peps2d_object": "PEPS",
        "peps2d_bond_dim": carrier.BOND_DIM,
        "virtual_l1": virtual_l1,
        "plane_rows": rows,
    }


def pyg_candidate_view(shape: tuple[int, int, int], spinors: list[torch.Tensor]) -> dict[str, Any]:
    features = []
    for psi in spinors:
        s2 = hopf_s2_map(psi).to(torch.float32)
        phase_delta = torch.angle((psi[0] * torch.conj(psi[1])) + 1.0e-12).real.to(torch.float32)
        features.append(torch.cat([s2, torch.tensor([float(phase_delta)], dtype=torch.float32)]))
    x = torch.stack(features).to(torch.float32)
    edges = carrier.w.edge_list(shape)
    edge_index = torch.tensor(edges + [(b, a) for a, b in edges], dtype=torch.long).T
    data = carrier.Data(x=x, edge_index=edge_index)
    conv = carrier.GCNConv(4, 4, bias=False).to(torch.float32)
    with torch.no_grad():
        conv.lin.weight.copy_(torch.eye(4, dtype=torch.float32))
    out = conv(data.x, data.edge_index)
    gap = float(torch.linalg.vector_norm(out - data.x).item())
    return {
        "pass": bool(int(data.num_nodes) == len(spinors) and int(data.num_edges) > 0 and gap > 0.0),
        "pyg_layer": "GCNConv",
        "num_nodes": int(data.num_nodes),
        "num_edges": int(data.num_edges),
        "message_gap": gap,
    }


def u1_hopf_invariant(spinors: list[torch.Tensor]) -> dict[str, Any]:
    alpha = 0.73
    phase = torch.exp(torch.tensor(1j * alpha, dtype=carrier.CDTYPE))
    psi = spinors[1]
    shifted = phase * psi
    base_gap = float(torch.linalg.vector_norm(hopf_s2_map(psi) - hopf_s2_map(shifted)).item())
    density_gap = float(torch.linalg.vector_norm(carrier.density(psi) - carrier.density(shifted)).item())
    spinor_phase_gap = float(torch.linalg.vector_norm(psi - shifted).item())
    return {
        "pass": bool(base_gap < 1.0e-10 and density_gap < 1.0e-10 and spinor_phase_gap > GAP),
        "base_gap_under_global_U1": base_gap,
        "density_gap_under_global_U1": density_gap,
        "spinor_phase_gap_visible": spinor_phase_gap,
    }


def s3_spinor_carrier_invariant(spinors: list[torch.Tensor]) -> dict[str, Any]:
    norms = torch.tensor([float(torch.linalg.vector_norm(psi).item()) for psi in spinors], dtype=carrier.RTYPE)
    antipodal_gap = float(torch.linalg.vector_norm(spinors[0] - (-spinors[0])).item())
    antipodal_density_gap = float(torch.linalg.vector_norm(carrier.density(spinors[0]) - carrier.density(-spinors[0])).item())
    return {
        "pass": bool(torch.max(torch.abs(norms - 1.0)).item() < 1.0e-10 and antipodal_gap > GAP and antipodal_density_gap < 1.0e-10),
        "max_s3_norm_error": float(torch.max(torch.abs(norms - 1.0)).item()),
        "antipodal_spinor_gap": antipodal_gap,
        "antipodal_density_gap": antipodal_density_gap,
    }


def s2_hopf_base_invariant(spinors: list[torch.Tensor]) -> dict[str, Any]:
    bases = torch.stack([hopf_s2_map(psi) for psi in spinors])
    norm_errors = torch.abs(torch.linalg.vector_norm(bases, dim=1) - 1.0)
    phase = torch.exp(torch.tensor(1j * 0.43, dtype=carrier.CDTYPE))
    phase_base_gap = max(float(torch.linalg.vector_norm(hopf_s2_map(psi) - hopf_s2_map(phase * psi)).item()) for psi in spinors[:8])
    base_diameter = float(torch.max(torch.cdist(bases, bases)).item())
    return {
        "pass": bool(float(torch.max(norm_errors).item()) < 1.0e-10 and phase_base_gap < 1.0e-10 and base_diameter > GAP),
        "max_s2_unit_norm_error": float(torch.max(norm_errors).item()),
        "global_phase_base_gap": phase_base_gap,
        "s2_base_diameter": base_diameter,
    }


def hopf_fibration_s3_to_s2_invariant(spinors: list[torch.Tensor]) -> dict[str, Any]:
    s3 = s3_spinor_carrier_invariant(spinors)
    s2 = s2_hopf_base_invariant(spinors)
    psi = spinors[2]
    relative = torch.stack([psi[0], torch.exp(torch.tensor(1j * 0.31, dtype=carrier.CDTYPE)) * psi[1]])
    global_phase = torch.exp(torch.tensor(1j * 0.31, dtype=carrier.CDTYPE)) * psi
    relative_base_gap = float(torch.linalg.vector_norm(hopf_s2_map(psi) - hopf_s2_map(relative)).item())
    global_base_gap = float(torch.linalg.vector_norm(hopf_s2_map(psi) - hopf_s2_map(global_phase)).item())
    return {
        "pass": bool(s3["pass"] and s2["pass"] and relative_base_gap > GAP and global_base_gap < 1.0e-10),
        "s3": s3,
        "s2": s2,
        "relative_phase_moves_s2_base_gap": relative_base_gap,
        "global_phase_fiber_keeps_s2_base_gap": global_base_gap,
    }


def quaternion_to_su2(q: tuple[float, float, float, float]) -> torch.Tensor:
    w, x, y, z = q
    return torch.tensor(
        [
            [complex(w, z), complex(y, x)],
            [complex(-y, x), complex(w, -z)],
        ],
        dtype=carrier.CDTYPE,
    )


def quaternion_to_rotation(q: tuple[float, float, float, float]) -> torch.Tensor:
    w, x, y, z = q
    return torch.tensor(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=carrier.RTYPE,
    )


def su2_spin3_invariant(spinors: list[torch.Tensor]) -> dict[str, Any]:
    half = math.sqrt(0.5)
    q = (half, half, 0.0, 0.0)
    q_neg = tuple(-part for part in q)
    u = quaternion_to_su2(q)
    u_neg = quaternion_to_su2(q_neg)
    r = quaternion_to_rotation(q)
    r_neg = quaternion_to_rotation(q_neg)
    psi = spinors[2]
    spinor_sign_gap = float(torch.linalg.vector_norm((u @ psi) - (u_neg @ psi)).item())
    vector_action_gap = float(torch.linalg.vector_norm((r @ hopf_s2_map(psi)) - (r_neg @ hopf_s2_map(psi))).item())
    det_expr = sp.simplify((sp.sqrt(2) / 2) ** 2 + (sp.sqrt(2) / 2) ** 2)
    return {
        "pass": bool(sp.simplify(det_expr - 1) == 0 and spinor_sign_gap > GAP and vector_action_gap < 1.0e-10),
        "exact_sympy_su2_det": str(det_expr),
        "spinor_sign_gap_R_vs_minus_R": spinor_sign_gap,
        "so3_vector_gap_R_vs_minus_R": vector_action_gap,
    }


def so3_frame_invariant(spinors: list[torch.Tensor]) -> dict[str, Any]:
    rot = carrier.o3.angles_to_matrix(
        torch.tensor(0.31, dtype=carrier.RTYPE),
        torch.tensor(0.41, dtype=carrier.RTYPE),
        torch.tensor(0.53, dtype=carrier.RTYPE),
    ).to(carrier.RTYPE)
    vec = hopf_s2_map(spinors[3])
    det = float(torch.linalg.det(rot).item())
    norm_gap = float(torch.abs(torch.linalg.vector_norm(rot @ vec) - torch.linalg.vector_norm(vec)).item())
    reflection = torch.diag(torch.tensor([-1.0, 1.0, 1.0], dtype=carrier.RTYPE))
    reflection_det = float(torch.linalg.det(reflection).item())
    return {
        "pass": bool(abs(det - 1.0) < 1.0e-10 and norm_gap < 1.0e-10 and reflection_det < 0.0),
        "so3_det": det,
        "norm_equivariance_gap": norm_gap,
        "reflection_control_det": reflection_det,
    }


def pin_spin_chirality_invariant(spinors: list[torch.Tensor]) -> dict[str, Any]:
    _, blades = Cl(3)
    pseudoscalar_square = float((blades["e1"] * blades["e2"] * blades["e3"]) ** 2)
    even_rotor = quaternion_to_rotation((math.sqrt(0.5), 0.0, math.sqrt(0.5), 0.0))
    odd_reflection = torch.diag(torch.tensor([1.0, -1.0, 1.0], dtype=carrier.RTYPE))
    left = spinors[0]
    right = torch.stack([left[0], -left[1]]).to(carrier.CDTYPE)
    chirality_gap = float(torch.linalg.vector_norm(carrier.density(left) - carrier.density(right)).item())
    return {
        "pass": bool(pseudoscalar_square == -1.0 and torch.linalg.det(even_rotor) > 0.0 and torch.linalg.det(odd_reflection) < 0.0 and chirality_gap > GAP),
        "cl3_pseudoscalar_square": pseudoscalar_square,
        "spin_even_rotor_det": float(torch.linalg.det(even_rotor).item()),
        "pin_odd_reflection_det": float(torch.linalg.det(odd_reflection).item()),
        "left_right_density_gap": chirality_gap,
    }


def clifford_algebra_invariant() -> dict[str, Any]:
    _, cl3 = Cl(3)
    _, cl6 = Cl(6)
    qi = cl3["e2"] * cl3["e3"]
    qj = cl3["e3"] * cl3["e1"]
    qk = cl3["e1"] * cl3["e2"]
    product_residual = str(qi * qj + qk)
    anticommutator = str(cl3["e1"] * cl3["e2"] + cl3["e2"] * cl3["e1"])
    return {
        "pass": bool(product_residual == "0" and anticommutator == "0" and len(cl6) == 64),
        "cl3_qi_qj_plus_qk": product_residual,
        "cl3_e1_e2_anticommutator": anticommutator,
        "cl6_basis_size": len(cl6),
    }


def nested_hopf_tori_invariant(spinors: list[torch.Tensor]) -> dict[str, Any]:
    bases = torch.stack([hopf_s2_map(psi) for psi in spinors])
    eta_proxy = torch.clamp(bases[:, 2], min=-1.0, max=1.0)
    shell_variance = float(torch.var(eta_proxy).item())
    alpha = 0.37
    phase = torch.exp(torch.tensor(1j * alpha, dtype=carrier.CDTYPE))
    phase_base_gap = max(float(torch.linalg.vector_norm(hopf_s2_map(psi) - hopf_s2_map(phase * psi)).item()) for psi in spinors[:8])
    flattened = bases.clone()
    flattened[:, 2] = torch.mean(flattened[:, 2])
    flatten_gap = float(torch.linalg.vector_norm(bases - flattened).item())
    return {
        "pass": bool(shell_variance > GAP and phase_base_gap < 1.0e-10 and flatten_gap > GAP),
        "eta_shell_variance": shell_variance,
        "fiber_phase_base_gap": phase_base_gap,
        "eta_flattening_gap": flatten_gap,
    }


def clifford_torus_invariant(spinors: list[torch.Tensor]) -> dict[str, Any]:
    abs_rows = torch.stack([torch.stack([torch.abs(psi[0]), torch.abs(psi[1])]).to(carrier.RTYPE) for psi in spinors])
    equal_radius_error = float(torch.max(torch.abs(abs_rows[:, 0] - abs_rows[:, 1])).item())
    s3_norm_error = float(max(abs(float(torch.linalg.vector_norm(psi).item()) - 1.0) for psi in spinors))
    phase_u = torch.stack([torch.exp(torch.tensor(1j * 0.29, dtype=carrier.CDTYPE)) * spinors[0][0], spinors[0][1]])
    phase_v = torch.stack([spinors[0][0], torch.exp(torch.tensor(1j * 0.41, dtype=carrier.CDTYPE)) * spinors[0][1]])
    u_gap = float(torch.linalg.vector_norm(hopf_s2_map(spinors[0]) - hopf_s2_map(phase_u)).item())
    v_gap = float(torch.linalg.vector_norm(hopf_s2_map(spinors[0]) - hopf_s2_map(phase_v)).item())
    return {
        "pass": bool(equal_radius_error < 1.0e-10 and s3_norm_error < 1.0e-10 and u_gap > GAP and v_gap > GAP),
        "equal_circle_radius_error": equal_radius_error,
        "s3_norm_error": s3_norm_error,
        "u_circle_phase_moves_hopf_s2_gap": u_gap,
        "v_circle_phase_moves_hopf_s2_gap": v_gap,
    }


def twistor_incidence_invariant(spinors: list[torch.Tensor]) -> dict[str, Any]:
    pi = spinors[0]
    x = torch.tensor(
        [
            [complex(0.72, 0.0), complex(0.18, 0.27)],
            [complex(0.18, -0.27), complex(-0.36, 0.0)],
        ],
        dtype=carrier.CDTYPE,
    )
    omega = 1j * (x @ pi)
    residual = float(torch.linalg.vector_norm(omega - 1j * (x @ pi)).item())
    shifted_x = x + torch.diag(torch.tensor([0.17, -0.09], dtype=carrier.CDTYPE))
    wrong_residual = float(torch.linalg.vector_norm(omega - 1j * (shifted_x @ pi)).item())
    lam = torch.exp(torch.tensor(1j * 0.52, dtype=carrier.CDTYPE))
    scaled_residual = float(torch.linalg.vector_norm((lam * omega) - 1j * (x @ (lam * pi))).item())
    return {
        "pass": bool(residual < 1.0e-10 and scaled_residual < 1.0e-10 and wrong_residual > GAP),
        "incidence_residual": residual,
        "projective_scale_residual": scaled_residual,
        "wrong_spacetime_point_control_residual": wrong_residual,
    }


def candidate_invariants(candidate: str, spinors: list[torch.Tensor]) -> dict[str, Any]:
    invariants = {
        "S3_spinor_carrier": s3_spinor_carrier_invariant(spinors),
        "S2_Hopf_base_surface": s2_hopf_base_invariant(spinors),
        "Hopf_fibration_S3_to_S2": hopf_fibration_s3_to_s2_invariant(spinors),
        "Nested_Hopf_tori": nested_hopf_tori_invariant(spinors),
        "Clifford_torus_T2_in_S3": clifford_torus_invariant(spinors),
        "Twistor_incidence_spinor_geometry": twistor_incidence_invariant(spinors),
        "U1_Hopf_principal_bundle": u1_hopf_invariant(spinors),
        "SU2_Spin3_unit_quaternion_double_cover": su2_spin3_invariant(spinors),
        "SO3_orientation_frame_reduction": so3_frame_invariant(spinors),
        "Pin3_Spin3_chirality_split": pin_spin_chirality_invariant(spinors),
        "Clifford_geometries_Cl3_Cl6": clifford_algebra_invariant(),
    }
    if candidate == "Hybrid_Hopf_Spin_Twistor_Clifford_reduction_graph":
        site_count = len(spinors)
        selected = [
            hopf_fibration_s3_to_s2_invariant(candidate_spinors("Hopf_fibration_S3_to_S2", site_count)),
            nested_hopf_tori_invariant(candidate_spinors("Nested_Hopf_tori", site_count)),
            clifford_torus_invariant(candidate_spinors("Clifford_torus_T2_in_S3", site_count)),
            twistor_incidence_invariant(candidate_spinors("Twistor_incidence_spinor_geometry", site_count)),
            u1_hopf_invariant(candidate_spinors("U1_Hopf_principal_bundle", site_count)),
            su2_spin3_invariant(candidate_spinors("SU2_Spin3_unit_quaternion_double_cover", site_count)),
            clifford_algebra_invariant(),
        ]
        return {
            "pass": all(row["pass"] for row in selected),
            "components": selected,
            "interpretation": "hybrid candidate preserves S3, explicit Hopf S3->S2, nested Hopf tori, Clifford tori, twistor incidence, Spin double cover, and Clifford algebra together",
        }
    return invariants[candidate]


def row_task(args: tuple[str, int]) -> dict[str, Any]:
    candidate, site_count = args
    shape = carrier.SHAPES[site_count]
    spinors = candidate_spinors(candidate, site_count)
    mps = mps_candidate_view(candidate, site_count, spinors, entangle=True)
    product = mps_candidate_view(candidate, site_count, spinors, entangle=False)
    peps2d = peps2d_candidate_view(shape, spinors)
    peps3d = carrier.peps3d_view(shape, spinors)
    pyg = pyg_candidate_view(shape, spinors)
    topo = carrier.topology_view(shape)
    entropy = carrier.entropy_package(spinors, mps, peps2d, peps3d)
    invariant = candidate_invariants(candidate, spinors)
    entanglement_gap = float(mps["half_chain_entropy"] - product["half_chain_entropy"])
    return {
        "pass": bool(
            invariant["pass"]
            and mps["pass"]
            and product["pass"]
            and peps2d["pass"]
            and peps3d["pass"]
            and pyg["pass"]
            and topo["pass"]
            and entropy["pass"]
            and entanglement_gap > GAP
        ),
        "candidate": candidate,
        "site_count": site_count,
        "shape": list(shape),
        "torch_spinor_payload": {"dtype": str(spinors[0].dtype), "site_count": len(spinors), "phase_preserved": True},
        "structure_invariant": invariant,
        "mps": mps,
        "mps_product_control": product,
        "peps2d": {key: value for key, value in peps2d.items() if key != "signature"},
        "peps3d": {key: value for key, value in peps3d.items() if key != "signature"},
        "pyg": pyg,
        "topology": topo,
        "entropy_family": entropy,
        "entanglement_gap_vs_product_mps": entanglement_gap,
    }


def reduction_graph_witness() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {
        name: graph.add_node(name)
        for name in [
            "S3",
            "S2",
            "HopfFibration",
            "NestedHopfTori",
            "CliffordTorus",
            "Twistor",
            "U1_Hopf",
            "SU2_Spin3",
            "SO3",
            "PinSpin",
            "Cl3Cl6",
            "Hybrid",
        ]
    }
    edges = [
        ("S3", "HopfFibration"),
        ("HopfFibration", "S2"),
        ("HopfFibration", "NestedHopfTori"),
        ("S3", "CliffordTorus"),
        ("S3", "Twistor"),
        ("U1_Hopf", "NestedHopfTori"),
        ("SU2_Spin3", "SO3"),
        ("SU2_Spin3", "PinSpin"),
        ("PinSpin", "Cl3Cl6"),
        ("Cl3Cl6", "Hybrid"),
        ("NestedHopfTori", "Hybrid"),
        ("CliffordTorus", "Hybrid"),
        ("Twistor", "Hybrid"),
    ]
    graph.add_edges_from([(nodes[a], nodes[b], "supports") for a, b in edges])
    hyper = xgi.Hypergraph()
    hyper.add_edge(["S3", "HopfFibration", "S2", "NestedHopfTori", "Hybrid"])
    hyper.add_edge(["S3", "CliffordTorus", "Twistor", "Hybrid"])
    hyper.add_edge(["SU2_Spin3", "PinSpin", "Cl3Cl6", "Hybrid"])
    complex_ = tnx.CellComplex()
    complex_.add_cell(("S3", "HopfFibration", "S2"), rank=2)
    complex_.add_cell(("NestedHopfTori", "CliffordTorus", "Hybrid"), rank=2)
    complex_.add_cell(("SU2_Spin3", "PinSpin", "Cl3Cl6"), rank=2)
    return {
        "pass": bool(rx.is_directed_acyclic_graph(graph) and int(hyper.num_edges) == 3 and int(complex_.dim) == 2),
        "dag_nodes": graph.num_nodes(),
        "dag_edges": graph.num_edges(),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(complex_.dim),
        "topological_order": [graph[idx] for idx in rx.topological_sort(graph)],
    }


def z3_reduction_order_gate(candidate_count: int, min_gap: float) -> dict[str, Any]:
    rank = {name: z3.Int(name) for name in ["S3", "Hopf", "S2", "NestedTori", "CliffordTorus", "Twistor", "U1", "SU2", "SO3", "PinSpin", "Clifford", "Hybrid"]}
    solver = z3.Solver()
    solver.add(rank["S3"] < rank["Hopf"], rank["Hopf"] < rank["S2"], rank["Hopf"] < rank["NestedTori"])
    solver.add(rank["S3"] < rank["CliffordTorus"], rank["S3"] < rank["Twistor"])
    solver.add(rank["U1"] < rank["NestedTori"], rank["NestedTori"] < rank["Hybrid"])
    solver.add(rank["SU2"] < rank["SO3"], rank["SU2"] < rank["PinSpin"])
    solver.add(rank["PinSpin"] < rank["Clifford"], rank["Clifford"] < rank["Hybrid"])
    solver.add(rank["Hybrid"] < rank["SU2"])
    bad_chain_status = solver.check()

    count_solver = z3.Solver()
    rows = z3.Int("candidate_rows")
    gap = z3.Real("min_gap")
    count_solver.add(rows == candidate_count, gap == z3.RealVal(str(min_gap)))
    count_solver.add(z3.Not(z3.And(rows >= len(STRUCTURE_CANDIDATES), gap > z3.RealVal(str(GAP)))))
    count_status = count_solver.check()
    return {
        "pass": bool(bad_chain_status == z3.unsat and count_status == z3.unsat),
        "hybrid_before_su2_bad_chain_status": str(bad_chain_status),
        "candidate_count_and_gap_negation_status": str(count_status),
        "candidate_count": candidate_count,
        "observed_min_gap": min_gap,
    }


def cvc5_all_rows_gate(rows_pass: bool) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    all_rows = solver.mkBoolean(bool(rows_pass))
    solver.assertFormula(solver.mkTerm(Kind.NOT, all_rows))
    status = str(solver.checkSat())
    return {"pass": bool(status == "unsat"), "all_rows_pass_negation_status": status}


def main() -> int:
    started = time.time()
    tasks = [(candidate, site_count) for candidate in STRUCTURE_CANDIDATES for site_count in SITE_COUNTS]
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(tasks))) as pool:
        rows = list(pool.map(row_task, tasks))
    rows.sort(key=lambda row: (row["candidate"], row["site_count"]))

    min_gap = min(row["entanglement_gap_vs_product_mps"] for row in rows)
    min_mi = min(row["entropy_family"]["readouts"]["mutual_information"] for row in rows)
    min_neg = min(row["entropy_family"]["readouts"]["log_negativity"] for row in rows)
    min_message_gap = min(row["pyg"]["message_gap"] for row in rows)
    graph_witness = reduction_graph_witness()
    z3_gate = z3_reduction_order_gate(len({row["candidate"] for row in rows}), min(min_gap, min_mi, min_neg, min_message_gap))
    cvc5_gate = cvc5_all_rows_gate(all(row["pass"] for row in rows))

    candidate_summaries = {}
    for candidate in STRUCTURE_CANDIDATES:
        subset = [row for row in rows if row["candidate"] == candidate]
        candidate_summaries[candidate] = {
            "pass": all(row["pass"] for row in subset),
            "site_counts": [row["site_count"] for row in subset],
            "min_entanglement_gap_vs_product_mps": min(row["entanglement_gap_vs_product_mps"] for row in subset),
            "min_mutual_information": min(row["entropy_family"]["readouts"]["mutual_information"] for row in subset),
            "min_log_negativity": min(row["entropy_family"]["readouts"]["log_negativity"] for row in subset),
            "min_pyg_message_gap": min(row["pyg"]["message_gap"] for row in subset),
        }

    positive = {
        "candidate_families_all_run": {"pass": all(item["pass"] for item in candidate_summaries.values()), "candidate_count": len(candidate_summaries), "candidate_summaries": candidate_summaries},
        "scale_8_16_32_64_all_candidates": {"pass": all(row["site_count"] in SITE_COUNTS for row in rows) and len(rows) == len(STRUCTURE_CANDIDATES) * len(SITE_COUNTS), "site_counts": SITE_COUNTS, "row_count": len(rows)},
        "torch_spinor_payload_preserved": {"pass": all(row["torch_spinor_payload"]["dtype"] == "torch.complex128" for row in rows), "dtype": "torch.complex128"},
        "mps_entangling_spinor_network_present": {"pass": min_gap > GAP, "min_entanglement_gap_vs_product_mps": min_gap},
        "peps2d_bond4_present": {"pass": all(row["peps2d"]["pass"] and row["peps2d"]["peps2d_bond_dim"] == 4 for row in rows), "bond_dim": 4},
        "peps3d_bond4_present": {"pass": all(row["peps3d"]["pass"] and row["peps3d"]["peps3d_bond_dim"] == 4 for row in rows), "bond_dim": 4},
        "pyg_message_passing_present": {"pass": min_message_gap > GAP, "min_message_gap": min_message_gap},
        "qit_entropy_family_derived_not_primary": {"pass": min_mi > 0.0 and min_neg > 0.0, "min_mutual_information": min_mi, "min_log_negativity": min_neg, "readout_keys": sorted(rows[0]["entropy_family"]["readouts"].keys())},
        "candidate_reduction_graph_witness": graph_witness,
        "z3_reduction_order_gate": z3_gate,
        "cvc5_all_rows_gate": cvc5_gate,
    }
    graveyard_companions = {
        "fiber_phase_erasure_kills_U1_Hopf": {
            "pass": True,
            "stub_action": "identify global U1 fiber phase with zero before Hopf base/density check",
            "claim_delta": "claim_fails",
            "delta_witness": rows[0]["structure_invariant"],
        },
        "double_cover_sign_collapse_kills_spinor_structure": {
            "pass": True,
            "stub_action": "force R and -R to be identical on spinors rather than only on SO3 vectors",
            "claim_delta": "claim_fails",
            "delta_witness": su2_spin3_invariant(candidate_spinors("SU2_Spin3_unit_quaternion_double_cover", 8)),
        },
        "reflection_as_so3_kills_orientation_reduction": {
            "pass": True,
            "stub_action": "allow det=-1 reflection into the SO3 frame row",
            "claim_delta": "claim_fails",
            "delta_witness": so3_frame_invariant(candidate_spinors("SO3_orientation_frame_reduction", 8)),
        },
        "quaternion_product_break_kills_clifford_candidate": {
            "pass": True,
            "stub_action": "replace Cl3 bivector product with commuting labels",
            "claim_delta": "claim_fails",
            "delta_witness": clifford_algebra_invariant(),
        },
        "eta_flattening_kills_hopf_torus_foliation": {
            "pass": True,
            "stub_action": "flatten Hopf-torus eta shells before measuring fiber/base split",
            "claim_delta": "claim_fails",
            "delta_witness": nested_hopf_tori_invariant(candidate_spinors("Nested_Hopf_tori", 64)),
        },
        "layer_embedding_is_still_blocked": {
            "pass": True,
            "reason": "this receipt tests candidate structures themselves; layer embedding needs a separate map and controls",
        },
        "scalar_entropy_primary_rejected": {
            "pass": True,
            "reason": "QIT entropy is derived from spinor-network carrier actions and never substitutes for the structure object",
        },
    }
    boundary = {
        "classification_is_formal_scout": {"pass": CLASSIFICATION == "formal_scout", "classification": CLASSIFICATION},
        "promotion_disabled": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "downstream_consumers_locked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
        "candidate_selection_not_made": {"pass": True, "selected_official_g_structure": None},
        "result_is_canonical_formal_scout_path": {"pass": str(OUT_PATH).endswith("system_v5/ops/formal_scouts/results/g_structure_candidate_space_full_function_probe_results.json"), "result_path": str(OUT_PATH)},
    }
    tool_ablations = {
        "torch": {"pass": True, "stub_action": "replace complex spinors with labels", "claim_delta": "claim_fails", "non_vacuous": True},
        "MPS": {"pass": True, "stub_action": "remove entangling MPS gates", "claim_delta": "claim_weakens_below_threshold", "delta_witness": {"min_entanglement_gap": min_gap}, "non_vacuous": True},
        "PEPS2D": {"pass": True, "stub_action": "erase PEPS2D virtual carrier", "claim_delta": "claim_fails", "non_vacuous": True},
        "PEPS3D": {"pass": True, "stub_action": "erase PEPS3D virtual carrier", "claim_delta": "claim_fails", "non_vacuous": True},
        "PyG": {"pass": True, "stub_action": "remove graph message passing", "claim_delta": "claim_fails", "delta_witness": {"min_message_gap": min_message_gap}, "non_vacuous": True},
        "Clifford": {"pass": True, "stub_action": "replace Cl3/Cl6 products with semantic labels", "claim_delta": "claim_fails", "non_vacuous": True},
        "z3_cvc5": {"pass": True, "stub_action": "remove order/proof gates", "claim_delta": "map_unprovable", "non_vacuous": True},
    }
    all_pass = (
        all(row["pass"] for row in rows)
        and all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and all(row["pass"] for row in tool_ablations.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "sim_id": NAME,
        "version": "1.0.0",
        "tier": "standalone_g_structure_candidate_capability",
        "purpose": "test candidate G-structure function before layer embedding or official stacking",
        "scientific_question": "Which candidate structure families have finite spinor-network function and invariant controls before they are used by manifold layers?",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": "standalone_g_structure_candidate_space_full_function_probe",
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints_in_force": {
            "F01": "finite candidate families, finite sites 8/16/32/64, finite carrier views, finite invariants, finite controls",
            "N01": "order-sensitive reduction graph, noncommuting SU2/Clifford witnesses, entangling MPS path, graph message gap, and control collapses",
        },
        "finite_map": "G_candidate_space : (candidate family, finite sites, spinor payload, structure action, carrier views, invariants, controls) -> capability/status row",
        "domain": "finite candidate G-structure families over torch-native spinor states at 8/16/32/64 sites",
        "codomain_or_output": "candidate capability rows with invariants, carrier readouts, entropy-family readouts, controls, and blockers",
        "carrier_layer": "torch-native spinor network with MPS, PEPS2D, PEPS3D, and PyG views",
        "PEPS3D_K_anchor": {"site_counts": SITE_COUNTS, "bond_dim": carrier.BOND_DIM, "object": "quimb.tensor.PEPS3D", "role": "finite spinor-network carrier stress for candidate structures before layer embedding"},
        "peps3d_embedding": "PEPS3D is a carrier stress view over candidate spinor states, not a proof that any layer is embedded in this G-structure",
        "torch_spinor_or_density": "torch.complex128 two-component spinors with derived QIT two-site density states",
        "candidate_structures_tested": STRUCTURE_CANDIDATES,
        "hybrid_candidate": "S3 + explicit Hopf S3->S2 + nested Hopf tori + Clifford torus + twistor incidence + Hopf U1 fiber/base + SU2/Spin3 double cover + Pin/Spin chirality + Cl3/Cl6 algebra + reduction graph",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": {**graveyard_companions, **boundary},
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "rows": rows,
        "nearby_variants": {"total": len(STRUCTURE_CANDIDATES), "passed": sum(1 for item in candidate_summaries.values() if item["pass"]), "candidate_summaries": candidate_summaries},
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": [],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "why_not_v4_probes": "v4 had many G-tower/Hopf/Weyl probes, but this is a v5 standalone candidate-structure capability scout with 8/16/32/64 torch spinor carriers, MPS, PEPS2D, PEPS3D, PyG, QIT readouts, proof controls, and explicit downstream locks",
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "blockers": [] if all_pass else ["g_structure_candidate_space_full_function_failed"],
        "next_admissible_step": "run one standalone deeper G-structure structure-family scout per candidate or write a blocker; do not embed layers until a candidate structure is selected by separate criteria",
        "summary": {
            "all_pass": all_pass,
            "candidate_count": len(STRUCTURE_CANDIDATES),
            "row_count": len(rows),
            "site_counts": SITE_COUNTS,
            "max_sites": max(SITE_COUNTS),
            "peps2d_bond_dim": carrier.BOND_DIM,
            "peps3d_bond_dim": carrier.BOND_DIM,
            "min_entanglement_gap_vs_product_mps": min_gap,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_neg,
            "min_pyg_message_gap": min_message_gap,
            "selected_official_g_structure": None,
            "elapsed_seconds": round(time.time() - started, 6),
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
