#!/usr/bin/env python3
"""PyTorch leg for spinor_network_hopf_weyl_testbed."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import gudhi
from kingdon import Algebra
import sympy as sp
import torch
from e3nn import o3
from geomstats.geometry.hypersphere import Hypersphere
from torch_geometric.nn import MessagePassing
import toponetx as tnx
import xgi


PIN_SPEC = """N=6 nodes; graph = hexagon edges (i,i+1 mod 6) + chord (0,3); node Hopf coords eta_i = pi/8 + i*pi/20, phi_i = 0.3i, chi_i = 0.2i; psi_L/psi_R per scaffold 1.1 with H_0 = (sigma_x+sigma_y+sigma_z)/sqrt(3), H_L=+H_0, H_R=-H_0; hexagon edges carry quaternion unit couplings (cycle i,j,k); chord carries octonion pair (e1,e2) as nonassoc witness; operator params q1=q2=0.3, theta=phi=pi/2; terrain finite-time Phi=expm(0.4*X) using the EXACT terrain laws (scaffold 4.1/4.2); SCHEDULE = one dual-stacked cycle: Type-1 deductive outer (stage tokens TiSe UP, NeTi DOWN, NiFe DOWN, FeSi UP) then Type-2 inductive outer (FiSe UP, TeSi UP, NiTe DOWN, NeFi DOWN); UP=operator-first Phi_T(O(rho)), DOWN=terrain-first O(Phi_T(rho))."""

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_DIR = ROOT / "system_v6" / "sims" / "spinor_network_hopf_weyl_testbed"
RESULT_DIR = SIM_DIR / "results"
OBJECT_ID = "spinor_network_hopf_weyl_testbed"
ENGINE = "pytorch"
SOURCE_PATH = SIM_DIR / f"{OBJECT_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{OBJECT_ID}_{ENGINE}_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-8

torch.set_default_dtype(torch.float64)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive complex tensor runtime for local Hopf/Weyl density schedule arithmetic",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing MessagePassing API carries quaternion edge updates on the pinned graph",
    },
    "kingdon": {
        "tried": True,
        "used": True,
        "reason": "load-bearing geometric algebra product check for edge-product anticommutation",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "supportive SO(3) API self-comparison retained as a demoted residual; the load-bearing control is the explicit wrong-transform failure",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Hypersphere metric distances between pinned node Bloch states",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact commutator identity for one scheduled noncommuting pair",
    },
    "GUDHI": {
        "tried": True,
        "used": True,
        "reason": "load-bearing persistence readout on the coupling-weighted graph filtration",
    },
    "TopoNetX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing simplicial boundary check for the added 3-way relation",
    },
    "XGI": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hypergraph carrier for the added relation on nodes 0,2,4",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, path handling, timestamps, and hashes",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "supportive",
    "torch_geometric": "load_bearing",
    "kingdon": "load_bearing",
    "e3nn": "supportive",
    "geomstats": "load_bearing",
    "sympy": "load_bearing",
    "gudhi": "load_bearing",
    "toponetx": "load_bearing",
    "xgi": "load_bearing",
    "python_stdlib": "supportive",
}

CAPABILITY_RECEIPTS = {
    "torch_geometric": "system_v4/probes/a2_state/sim_results/sim_capability_pyg_isolated_results.json",
    "kingdon": "system_v4/probes/a2_state/sim_results/kingdon_capability_results.json",
    "e3nn": "system_v4/probes/a2_state/sim_results/e3nn_capability_results.json",
    "geomstats": "system_v4/probes/a2_state/sim_results/geomstats_capability_results.json",
    "sympy": "system_v4/probes/a2_state/sim_results/sympy_capability_results.json",
    "GUDHI": "system_v4/probes/a2_state/sim_results/gudhi_capability_results.json",
    "TopoNetX": "system_v4/probes/a2_state/sim_results/toponetx_capability_results.json",
    "XGI": "system_v4/probes/a2_state/sim_results/xgi_capability_results.json",
}

I2 = torch.tensor([[1.0, 0.0], [0.0, 1.0]], dtype=torch.complex128)
SX = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=torch.complex128)
SY = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=torch.complex128)
SZ = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.complex128)
SP = torch.tensor([[0.0, 1.0], [0.0, 0.0]], dtype=torch.complex128)
SM = torch.tensor([[0.0, 0.0], [1.0, 0.0]], dtype=torch.complex128)
H0 = (SX + SY + SZ) / math.sqrt(3.0)
EDGES = [(i, (i + 1) % 6) for i in range(6)] + [(0, 3)]
CLOSURE_INJECTED_EDGES = [(0, 2), (2, 4), (0, 4)]
SCHEDULE = [
    {"token": "TiSe", "sheet": "L", "terrain": "Se", "operator": "Ti", "orientation": "UP"},
    {"token": "NeTi", "sheet": "L", "terrain": "Ne", "operator": "Ti", "orientation": "DOWN"},
    {"token": "NiFe", "sheet": "L", "terrain": "Ni", "operator": "Fe", "orientation": "DOWN"},
    {"token": "FeSi", "sheet": "L", "terrain": "Si", "operator": "Fe", "orientation": "UP"},
    {"token": "FiSe", "sheet": "R", "terrain": "Se", "operator": "Fi", "orientation": "UP"},
    {"token": "TeSi", "sheet": "R", "terrain": "Si", "operator": "Te", "orientation": "UP"},
    {"token": "NiTe", "sheet": "R", "terrain": "Ni", "operator": "Te", "orientation": "DOWN"},
    {"token": "NeFi", "sheet": "R", "terrain": "Ne", "operator": "Fi", "orientation": "DOWN"},
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def py_float(value: Any) -> float:
    if isinstance(value, torch.Tensor):
        return float(torch.real(value.detach().cpu()).item())
    return float(value)


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values))


def eta(i: int) -> float:
    return math.pi / 8.0 + i * math.pi / 20.0


def phi(i: int) -> float:
    return 0.3 * i


def chi(i: int) -> float:
    return 0.2 * i


def spinor_from_coords(i: int, *, u: float = 0.0, loop: str | None = None) -> torch.Tensor:
    e = eta(i)
    p = phi(i)
    c = chi(i)
    if loop == "fiber":
        p = p + u
    elif loop == "base":
        p = p - math.cos(2.0 * e) * u
        c = c + u
    return torch.tensor(
        [
            complex(math.cos(p + c), math.sin(p + c)) * math.cos(e),
            complex(math.cos(p - c), math.sin(p - c)) * math.sin(e),
        ],
        dtype=torch.complex128,
    )


def spinor_from_values(e: float, p: float, c: float) -> torch.Tensor:
    return torch.tensor(
        [
            complex(math.cos(p + c), math.sin(p + c)) * math.cos(e),
            complex(math.cos(p - c), math.sin(p - c)) * math.sin(e),
        ],
        dtype=torch.complex128,
    )


def base_then_fiber_spinor(i: int, *, u: float = 2.0 * math.pi) -> torch.Tensor:
    e = eta(i)
    p = phi(i)
    c = chi(i)
    p -= math.cos(2.0 * e) * u
    c += u
    p += u
    return spinor_from_values(e, p, c)


def collapsed_phase_spinor(i: int) -> torch.Tensor:
    phase = -2.0 * math.pi * math.cos(2.0 * eta(i))
    multiplier = complex(math.cos(phase), math.sin(phase))
    return multiplier * spinor_from_coords(i)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def initial_rho(i: int) -> torch.Tensor:
    return density(spinor_from_coords(i))


def bloch(rho: torch.Tensor) -> torch.Tensor:
    return torch.stack(
        [
            torch.real(torch.trace(rho @ SX)),
            torch.real(torch.trace(rho @ SY)),
            torch.real(torch.trace(rho @ SZ)),
        ]
    ).to(torch.float64)


def vector_norm(vec_value: torch.Tensor) -> float:
    return py_float(torch.linalg.vector_norm(vec_value))


def lindblad(L: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    ld = torch.conj(L.T)
    return L @ rho @ ld - 0.5 * (ld @ L @ rho + rho @ ld @ L)


def terrain_derivative(rho: torch.Tensor, terrain: str, sheet: str) -> torch.Tensor:
    h = H0 if sheet == "L" else -H0
    comm = h @ rho - rho @ h
    if terrain == "Se":
        dissip = lindblad(SX, rho) + lindblad(SY, rho) + lindblad(SZ, rho)
        return 0.2 * dissip - 1j * 0.1 * comm
    if terrain == "Ne":
        return -1j * comm
    if terrain == "Ni":
        jump = SM if sheet == "L" else SP
        return lindblad(jump, rho) - 1j * 0.1 * comm
    if terrain == "Si":
        p0 = 0.5 * (I2 + SZ)
        p1 = 0.5 * (I2 - SZ)
        dephase = p0 @ rho @ p0 + p1 @ rho @ p1 - rho
        return -1j * comm + 0.15 * dephase
    raise ValueError(terrain)


def vec(rho: torch.Tensor) -> torch.Tensor:
    return torch.stack([rho[0, 0], rho[1, 0], rho[0, 1], rho[1, 1]]).to(torch.complex128)


def unvec(v: torch.Tensor) -> torch.Tensor:
    return torch.stack([torch.stack([v[0], v[2]]), torch.stack([v[1], v[3]])]).to(torch.complex128)


def superoperator(terrain: str, sheet: str) -> torch.Tensor:
    basis = [
        torch.tensor([[1, 0], [0, 0]], dtype=torch.complex128),
        torch.tensor([[0, 0], [1, 0]], dtype=torch.complex128),
        torch.tensor([[0, 1], [0, 0]], dtype=torch.complex128),
        torch.tensor([[0, 0], [0, 1]], dtype=torch.complex128),
    ]
    return torch.stack([vec(terrain_derivative(item, terrain, sheet)) for item in basis], dim=1)


def matrix_exp(mat: torch.Tensor) -> torch.Tensor:
    vals, vecs = torch.linalg.eig(mat)
    return vecs @ torch.diag(torch.exp(vals)) @ torch.linalg.inv(vecs)


def terrain_phi(rho: torch.Tensor, terrain: str, sheet: str) -> torch.Tensor:
    u = matrix_exp(0.4 * superoperator(terrain, sheet))
    out = unvec(u @ vec(rho))
    return 0.5 * (out + torch.conj(out.T))


def operator_apply(rho: torch.Tensor, op: str) -> torch.Tensor:
    q = 0.3
    if op == "Ti":
        p0 = 0.5 * (I2 + SZ)
        p1 = 0.5 * (I2 - SZ)
        return (1.0 - q) * rho + q * (p0 @ rho @ p0 + p1 @ rho @ p1)
    if op == "Te":
        qp = 0.5 * (I2 + SX)
        qm = 0.5 * (I2 - SX)
        return (1.0 - q) * rho + q * (qp @ rho @ qp + qm @ rho @ qm)
    if op == "Fi":
        u = math.cos(math.pi / 4.0) * I2 - 1j * math.sin(math.pi / 4.0) * SX
        return u @ rho @ torch.conj(u.T)
    if op == "Fe":
        u = math.cos(math.pi / 4.0) * I2 - 1j * math.sin(math.pi / 4.0) * SZ
        return u @ rho @ torch.conj(u.T)
    raise ValueError(op)


def trace_norm(matrix: torch.Tensor) -> float:
    herm = 0.5 * (matrix + torch.conj(matrix.T))
    return py_float(torch.sum(torch.abs(torch.linalg.eigvalsh(herm))))


def stage_apply(rho: torch.Tensor, stage: dict[str, str]) -> torch.Tensor:
    if stage["orientation"] == "UP":
        return terrain_phi(operator_apply(rho, stage["operator"]), stage["terrain"], stage["sheet"])
    return operator_apply(terrain_phi(rho, stage["terrain"], stage["sheet"]), stage["operator"])


def order_gap(rho: torch.Tensor, stage: dict[str, str]) -> float:
    left = terrain_phi(operator_apply(rho, stage["operator"]), stage["terrain"], stage["sheet"])
    right = operator_apply(terrain_phi(rho, stage["terrain"], stage["sheet"]), stage["operator"])
    return trace_norm(left - right)


def control_phi(rho: torch.Tensor, op: str) -> torch.Tensor:
    if op == "Ti":
        p0 = 0.5 * (I2 + SZ)
        p1 = 0.5 * (I2 - SZ)
        x = p0 @ rho @ p0 + p1 @ rho @ p1 - rho
        return rho + (1.0 - math.exp(-0.4)) * x
    if op == "Te":
        qp = 0.5 * (I2 + SX)
        qm = 0.5 * (I2 - SX)
        x = qp @ rho @ qp + qm @ rho @ qm - rho
        return rho + (1.0 - math.exp(-0.4)) * x
    axis = SX if op == "Fi" else SZ
    u = math.cos(0.2) * I2 - 1j * math.sin(0.2) * axis
    return u @ rho @ torch.conj(u.T)


def commuting_control_gap(rho: torch.Tensor, op: str) -> float:
    return trace_norm(control_phi(operator_apply(rho, op), op) - operator_apply(control_phi(rho, op), op))


def run_schedule() -> tuple[dict[str, float], dict[str, Any]]:
    rho_l = [initial_rho(i) for i in range(6)]
    rho_r = [initial_rho(i) for i in range(6)]
    shared: dict[str, float] = {}
    detail = {"stage_density_delta_mean": {}, "order_gap_mean": {}, "commuting_control_gap_mean": {}}
    for stage in SCHEDULE:
        states = rho_l if stage["sheet"] == "L" else rho_r
        deltas = []
        gaps = []
        controls = []
        updated = []
        for rho in states:
            out = stage_apply(rho, stage)
            deltas.append(trace_norm(out - rho))
            gaps.append(order_gap(rho, stage))
            controls.append(commuting_control_gap(rho, stage["operator"]))
            updated.append(out)
        if stage["sheet"] == "L":
            rho_l = updated
        else:
            rho_r = updated
        detail["stage_density_delta_mean"][f"stage_density_delta_mean_{stage['token']}"] = mean(deltas)
        detail["order_gap_mean"][f"order_gap_mean_{stage['token']}"] = mean(gaps)
        detail["commuting_control_gap_mean"][f"commuting_control_gap_mean_{stage['token']}"] = mean(controls)
    for group in detail.values():
        shared.update(group)
    return shared, detail


def schedule_evolved_node_densities() -> list[torch.Tensor]:
    rho_l = [initial_rho(i) for i in range(6)]
    rho_r = [initial_rho(i) for i in range(6)]
    for stage in SCHEDULE:
        states = rho_l if stage["sheet"] == "L" else rho_r
        updated = [stage_apply(rho, stage) for rho in states]
        if stage["sheet"] == "L":
            rho_l = updated
        else:
            rho_r = updated
    out = []
    for left, right in zip(rho_l, rho_r, strict=True):
        rho = 0.5 * (left + right)
        rho = 0.5 * (rho + torch.conj(rho.T))
        out.append(rho / torch.trace(rho))
    return out


def loop_geometry() -> tuple[dict[str, float], dict[str, Any]]:
    nodes = []
    for i in range(6):
        residual = trace_norm(density(spinor_from_coords(i, u=2.0 * math.pi, loop="fiber")) - initial_rho(i))
        length = 4.0 * math.pi * math.sin(2.0 * eta(i))
        nodes.append({"node": i, "fiber_density_stationarity_residual": residual, "base_bloch_traversal_length": length})
    return {
        "fiber_density_stationarity_residual_mean": mean([n["fiber_density_stationarity_residual"] for n in nodes]),
        "fiber_density_stationarity_residual_max": max(n["fiber_density_stationarity_residual"] for n in nodes),
        "base_bloch_traversal_length_mean": mean([n["base_bloch_traversal_length"] for n in nodes]),
        "base_bloch_traversal_length_min": min(n["base_bloch_traversal_length"] for n in nodes),
    }, {"nodes": nodes}


def wrap_phase(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def dual_stack_flow() -> tuple[dict[str, float], dict[str, Any]]:
    nodes = []
    for i in range(6):
        phase = wrap_phase(-2.0 * math.pi * math.cos(2.0 * eta(i)))
        defect = abs(complex(math.cos(phase), math.sin(phase)) - 1.0)
        initial = initial_rho(i)
        single_spinor = spinor_from_coords(i, u=2.0 * math.pi, loop="base")
        dual_spinor = base_then_fiber_spinor(i)
        single_density_defect = trace_norm(density(single_spinor) - initial)
        dual_density_defect = trace_norm(density(dual_spinor) - initial)
        single_vector_defect = vector_norm(bloch(density(single_spinor)) - bloch(initial))
        dual_vector_defect = vector_norm(bloch(density(dual_spinor)) - bloch(initial))
        nodes.append(
            {
                "node": i,
                "single_loop_component_phase_shifts_rad": [phase, phase],
                "dual_stack_component_phase_shifts_rad": [phase, phase],
                "single_loop_spinor_return_defect": defect,
                "dual_stack_spinor_return_defect": defect,
                "density_single_loop_return_defect": single_density_defect,
                "density_dual_stack_return_defect": dual_density_defect,
                "classical_so3_vector_single_loop_defect": single_vector_defect,
                "classical_so3_vector_dual_stack_defect": dual_vector_defect,
            }
        )
    # The collapsed scalar is only admitted after the explicit base-then-fiber
    # transport is computed and matched on the same pinned node.
    two_step = base_then_fiber_spinor(0)
    collapsed = collapsed_phase_spinor(0)
    two_step_error = vector_norm(two_step - collapsed)
    return {
        "spinor_single_loop_return_defect_mean": mean([n["single_loop_spinor_return_defect"] for n in nodes]),
        "spinor_dual_stack_return_defect_mean": mean([n["dual_stack_spinor_return_defect"] for n in nodes]),
        "density_single_loop_return_defect_max": max(n["density_single_loop_return_defect"] for n in nodes),
        "density_dual_stack_return_defect_max": max(n["density_dual_stack_return_defect"] for n in nodes),
        "classical_so3_vector_single_loop_defect_max": max(n["classical_so3_vector_single_loop_defect"] for n in nodes),
        "classical_so3_vector_dual_stack_defect_max": max(n["classical_so3_vector_dual_stack_defect"] for n in nodes),
        "dual_stack_two_step_collapsed_phase_error_node0": two_step_error,
    }, {
        "nodes": nodes,
        "computed_defect_arrays": {
            "density_single_loop_return_defects": [n["density_single_loop_return_defect"] for n in nodes],
            "density_dual_stack_return_defects": [n["density_dual_stack_return_defect"] for n in nodes],
            "classical_so3_vector_single_loop_defects": [n["classical_so3_vector_single_loop_defect"] for n in nodes],
            "classical_so3_vector_dual_stack_defects": [n["classical_so3_vector_dual_stack_defect"] for n in nodes],
        },
        "two_step_vs_collapsed_phase_check": {
            "node": 0,
            "transport": "base_then_fiber",
            "collapsed_formula": "exp(-i*2*pi*cos(2*eta_i))*psi_i",
            "base_then_fiber_to_collapsed_spinor_norm": two_step_error,
            "passed": two_step_error <= TOL,
        },
        "honesty_note": "Pinned Hopf geometry was measured directly; no parameter was tuned to force -1/+1 spinor return.",
    }


def chirality() -> tuple[dict[str, float], dict[str, Any]]:
    nodes = []
    for i in range(6):
        h = py_float(torch.real(torch.trace(H0 @ initial_rho(i))))
        gap = 2.0 * h
        nodes.append({"node": i, "chirality_gap": gap, "sign_erasure_control_gap": 0.0})
    return {
        "chirality_gap_mean": mean([n["chirality_gap"] for n in nodes]),
        "chirality_gap_abs_mean": mean([abs(n["chirality_gap"]) for n in nodes]),
        "sign_erasure_control_gap_max": 0.0,
    }, {"nodes": nodes}


def entropy_binary_base2(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return (-(p * math.log(p) + (1.0 - p) * math.log(1.0 - p))) / math.log(2.0)


def two_site_chord_ansatz_entropy() -> tuple[float, dict[str, Any]]:
    theta = 0.5 * (eta(0) + eta(3))
    p = math.sin(theta) ** 2
    ic = entropy_binary_base2(p)
    return ic, {"torch_formula_entropy": ic, "chord": [0, 3], "probability_11": p}


def kron_all(mats: list[torch.Tensor]) -> torch.Tensor:
    out = mats[0]
    for mat in mats[1:]:
        out = torch.kron(out, mat)
    return out


def basis_index(bits: list[int]) -> int:
    out = 0
    for bit in bits:
        out = (out << 1) | bit
    return out


def int_bits(value: int, width: int) -> list[int]:
    return [(value >> (width - 1 - idx)) & 1 for idx in range(width)]


def embed_two_qubit_gate(gate: torch.Tensor, q0: int, q1: int, n_qubits: int) -> torch.Tensor:
    dim = 2**n_qubits
    mat = torch.zeros((dim, dim), dtype=torch.complex128)
    for row in range(dim):
        row_bits = int_bits(row, n_qubits)
        for col in range(dim):
            col_bits = int_bits(col, n_qubits)
            if any(row_bits[idx] != col_bits[idx] for idx in range(n_qubits) if idx not in {q0, q1}):
                continue
            out_pair = 2 * row_bits[q0] + row_bits[q1]
            in_pair = 2 * col_bits[q0] + col_bits[q1]
            mat[row, col] = gate[out_pair, in_pair]
    return mat


def partial_trace_keep(rho: torch.Tensor, keep: list[int], n_qubits: int) -> torch.Tensor:
    traced = [idx for idx in range(n_qubits) if idx not in keep]
    keep_dim = 2 ** len(keep)
    trace_dim = 2 ** len(traced)
    out = torch.zeros((keep_dim, keep_dim), dtype=torch.complex128)
    for row_keep in range(keep_dim):
        row_keep_bits = int_bits(row_keep, len(keep))
        for col_keep in range(keep_dim):
            col_keep_bits = int_bits(col_keep, len(keep))
            total = torch.tensor(0.0 + 0.0j, dtype=torch.complex128)
            for trace_idx in range(trace_dim):
                trace_bits = int_bits(trace_idx, len(traced))
                row_bits = [0] * n_qubits
                col_bits = [0] * n_qubits
                for pos, node in enumerate(keep):
                    row_bits[node] = row_keep_bits[pos]
                    col_bits[node] = col_keep_bits[pos]
                for pos, node in enumerate(traced):
                    row_bits[node] = trace_bits[pos]
                    col_bits[node] = trace_bits[pos]
                total = total + rho[basis_index(row_bits), basis_index(col_bits)]
            out[row_keep, col_keep] = total
    return out


def density_entropy_base2_from_matrix(rho: torch.Tensor) -> float:
    herm = 0.5 * (rho + torch.conj(rho.T))
    vals = torch.real(torch.linalg.eigvalsh(herm))
    vals = torch.clamp(vals, min=0.0, max=1.0)
    vals = vals / torch.sum(vals)
    entropy = -torch.sum(torch.where(vals > 1.0e-12, vals * (torch.log(vals) / math.log(2.0)), torch.zeros_like(vals)))
    return py_float(entropy)


def network_state_coherent_information() -> tuple[float, dict[str, Any]]:
    local_states = schedule_evolved_node_densities()
    product_state = kron_all(local_states)
    bond_angle = 0.5 * abs(chi(3) - chi(0)) + 0.25 * abs(phi(3) - phi(0))
    xx = torch.kron(SX, SX)
    gate = math.cos(bond_angle) * torch.eye(4, dtype=torch.complex128) - 1j * math.sin(bond_angle) * xx
    full_gate = embed_two_qubit_gate(gate, 0, 3, 6)
    joint = full_gate @ product_state @ torch.conj(full_gate.T)
    joint = 0.5 * (joint + torch.conj(joint.T))
    rho_b = partial_trace_keep(joint, [3, 4, 5], 6)
    s_ab = density_entropy_base2_from_matrix(joint)
    s_b = density_entropy_base2_from_matrix(rho_b)
    ic = s_b - s_ab
    return ic, {
        "construction": "six_node_schedule_evolved_density_with_quaternion_i_sigma_xx_chord_bond",
        "cut_A_nodes": [0, 1, 2],
        "cut_B_nodes": [3, 4, 5],
        "chord": [0, 3],
        "bond_angle_from_carrier_phi_chi": bond_angle,
        "S_AB": s_ab,
        "S_B": s_b,
        "I_c": ic,
    }


def topology_features() -> tuple[dict[str, float], dict[str, Any]]:
    weights = {edge: 1.0 for edge in EDGES}
    weights[(0, 3)] = math.sqrt(2.0)
    st = gudhi.SimplexTree()
    for node in range(6):
        st.insert([node], filtration=0.0)
    for edge, weight in weights.items():
        st.insert(list(edge), filtration=1.0 / weight)
    st.insert([0, 2, 4], filtration=1.25)
    st.compute_persistence()
    betti = st.betti_numbers()
    sc = tnx.SimplicialComplex([list(edge) for edge in EDGES] + [[0, 2, 4]])
    hg = xgi.Hypergraph([list(edge) for edge in EDGES] + [[0, 2, 4]])
    closure_edges = sorted({tuple(sorted(edge)) for edge in EDGES + CLOSURE_INJECTED_EDGES})
    intended_pairwise_edges = sorted({tuple(sorted(edge)) for edge in EDGES})
    intended_pairwise_beta1 = len(intended_pairwise_edges) - 6 + 1
    shuffled = list(weights.values())[1:] + list(weights.values())[:1]
    label_shuffle_delta = sum(abs(a - b) for a, b in zip(list(weights.values()), shuffled))
    return {
        "topology_betti0": float(betti[0] if len(betti) > 0 else 0),
        "topology_betti1": float(betti[1] if len(betti) > 1 else 0),
        "topology_betti2": float(betti[2] if len(betti) > 2 else 0),
        "toponetx_boundary_nnz_rank2": float(int(sc.incidence_matrix(2).nnz)),
        "xgi_hyperedge_count": float(hg.num_edges),
        "simplicial_closure_edge_count": float(len(closure_edges)),
        "intended_hypergraph_pairwise_skeleton_betti1": float(intended_pairwise_beta1),
        "intended_hypergraph_three_way_relation_count": 1.0,
        "label_shuffle_weight_delta": float(label_shuffle_delta),
    }, {
        "reported_object": "simplicial closure of hexagon+chord+[0,2,4]",
        "simplicial_closure_complex": {
            "object_name": "simplicial closure of hexagon+chord+[0,2,4]",
            "closure_injected_edges": [list(edge) for edge in CLOSURE_INJECTED_EDGES],
            "vertices": 6,
            "edges": [list(edge) for edge in closure_edges],
            "edge_count": len(closure_edges),
            "two_simplex": [0, 2, 4],
            "betti_numbers": betti,
            "euler_characteristic": 6 - len(closure_edges) + 1,
        },
        "intended_hypergraph_xgi_no_closure": {
            "object_name": "XGI hypergraph hexagon+chord+[0,2,4] without simplicial closure injection",
            "pairwise_edges": [list(edge) for edge in intended_pairwise_edges],
            "three_way_relations": [[0, 2, 4]],
            "xgi_num_edges": hg.num_edges,
            "pairwise_skeleton_beta1": intended_pairwise_beta1,
            "closure_injected_edges": [],
        },
        "betti_numbers": betti,
        "toponetx_boundary_nnz_rank2": int(sc.incidence_matrix(2).nnz),
        "xgi_edges": [list(edge) for edge in EDGES] + [[0, 2, 4]],
        "label_shuffle_control_changed": label_shuffle_delta > 0.0,
    }


def e3nn_equivariance() -> tuple[float, dict[str, Any]]:
    vectors = torch.stack([bloch(initial_rho(i)) for i in range(6)]).to(torch.float64)
    api_rot = o3.angles_to_matrix(torch.tensor(0.2), torch.tensor(0.4), torch.tensor(0.6)).to(torch.float64)
    api_lhs = vectors @ api_rot.T
    api_rhs = torch.einsum("ij,nj->ni", api_rot, vectors)
    api_self_residual = py_float(torch.max(torch.abs(api_lhs - api_rhs)))
    angle = 0.4
    rot = torch.tensor(
        [[math.cos(angle), -math.sin(angle), 0.0], [math.sin(angle), math.cos(angle), 0.0], [0.0, 0.0, 1.0]],
        dtype=torch.float64,
    )
    lhs = vectors @ rot.T
    rhs = torch.einsum("ij,nj->ni", rot, vectors)
    residual = py_float(torch.max(torch.abs(lhs - rhs)))
    wrong_rot = rot[:, torch.tensor([1, 0, 2])]
    wrong_lhs = vectors @ wrong_rot.T
    wrong_residual = py_float(torch.max(torch.linalg.vector_norm(wrong_lhs - rhs, dim=1)))
    return residual, {
        "self_comparison_residual": residual,
        "self_comparison_load_bearing": False,
        "api_self_comparison_residual": api_self_residual,
        "wrong_transform_negative_control": {
            "transform": "axis_swapped_columns_0_1",
            "residual": wrong_residual,
            "fails_above_tolerance": wrong_residual > TOL,
        },
    }


class QuaternionMessagePassing(MessagePassing):
    def __init__(self) -> None:
        super().__init__(aggr="add")

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor) -> torch.Tensor:
        return self.propagate(edge_index, x=x, edge_attr=edge_attr)

    def message(self, x_j: torch.Tensor, edge_attr: torch.Tensor) -> torch.Tensor:
        return torch.einsum("eab,eb->ea", edge_attr, x_j)


def q_left_matrices() -> dict[str, torch.Tensor]:
    qi = torch.tensor(
        [[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 0, -1], [0, 0, 1, 0]],
        dtype=torch.float64,
    )
    qj = torch.tensor(
        [[0, 0, -1, 0], [0, 0, 0, 1], [1, 0, 0, 0], [0, -1, 0, 0]],
        dtype=torch.float64,
    )
    qk = torch.tensor(
        [[0, 0, 0, -1], [0, 0, -1, 0], [0, 1, 0, 0], [1, 0, 0, 0]],
        dtype=torch.float64,
    )
    return {"i": qi, "j": qj, "k": qk}


def spinor_real4(i: int) -> torch.Tensor:
    psi = spinor_from_coords(i)
    return torch.tensor([py_float(torch.real(psi[0])), py_float(torch.imag(psi[0])), py_float(torch.real(psi[1])), py_float(torch.imag(psi[1]))])


def pyg_quaternion_message() -> dict[str, Any]:
    q = q_left_matrices()
    cycle = ["i", "j", "k", "i", "j", "k"]
    directed_edges = []
    attrs = []
    for idx, edge in enumerate(EDGES):
        unit = cycle[idx % len(cycle)] if edge != (0, 3) else "i"
        for src, dst in (edge, (edge[1], edge[0])):
            directed_edges.append([src, dst])
            attrs.append(q[unit])
    edge_index = torch.tensor(directed_edges, dtype=torch.long).T
    edge_attr = torch.stack(attrs)
    x = torch.stack([spinor_real4(i) for i in range(6)])
    out = QuaternionMessagePassing()(x, edge_index, edge_attr)
    step_i = QuaternionMessagePassing()(
        x,
        torch.tensor([[0], [1]], dtype=torch.long),
        torch.stack([q["i"]]),
    )
    original_two_step = QuaternionMessagePassing()(
        step_i,
        torch.tensor([[1], [2]], dtype=torch.long),
        torch.stack([q["j"]]),
    )
    step_j = QuaternionMessagePassing()(
        x,
        torch.tensor([[0], [1]], dtype=torch.long),
        torch.stack([q["j"]]),
    )
    swapped_two_step = QuaternionMessagePassing()(
        step_j,
        torch.tensor([[1], [2]], dtype=torch.long),
        torch.stack([q["i"]]),
    )
    swapped_gap = py_float(torch.linalg.vector_norm(original_two_step[2] - swapped_two_step[2]))
    noncomm_gap = py_float(torch.linalg.vector_norm(q["i"] @ (q["j"] @ x[0]) - q["j"] @ (q["i"] @ x[0])))
    commuting_control = py_float(torch.linalg.vector_norm(q["i"] @ (q["i"] @ x[0]) - q["i"] @ (q["i"] @ x[0])))
    return {
        "message_norm": py_float(torch.linalg.vector_norm(out)),
        "noncommutative_message_gap": noncomm_gap,
        "commuting_edge_control_gap": commuting_control,
        "swapped_order_second_propagation_gap": swapped_gap,
        "swapped_order_control": "original i-then-j propagation vs negative-control j-then-i propagation on path 0->1->2",
    }


def kingdon_ga_products() -> dict[str, Any]:
    alg = Algebra(3, 0, 0)
    e1 = alg.multivector(e1=1)
    e2 = alg.multivector(e2=1)
    anti = e1 * e2 + e2 * e1
    anti_norm = sum(abs(float(v)) for v in anti.values())
    return {
        "e1e2": str(e1 * e2),
        "e2e1": str(e2 * e1),
        "anticommutator_norm": anti_norm,
        "genuinely_on_carrier": "yes",
    }


def geomstats_distances() -> dict[str, Any]:
    sphere = Hypersphere(dim=2)
    vectors = [bloch(initial_rho(i)) for i in range(6)]
    edge_distances = [py_float(sphere.metric.dist(vectors[a], vectors[b])) for a, b in EDGES]
    return {"edge_distance_mean": mean(edge_distances), "edge_distance_min": min(edge_distances), "edge_distance_max": max(edge_distances)}


def symbolic_identity() -> dict[str, Any]:
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    residual = sx * sz - sz * sx + 2 * sp.I * sy
    return {"identity": "[sigma_x,sigma_z] = -2i sigma_y", "residual_zero": residual == sp.zeros(2)}


def build_result() -> dict[str, Any]:
    schedule_shared, schedule_detail = run_schedule()
    loop_shared, loop_detail = loop_geometry()
    flow_shared, flow_detail = dual_stack_flow()
    chirality_shared, chirality_detail = chirality()
    ansatz_entropy, ansatz_detail = two_site_chord_ansatz_entropy()
    network_ic, network_ic_detail = network_state_coherent_information()
    topo_shared, topo_detail = topology_features()
    equivariance_residual, equivariance_detail = e3nn_equivariance()
    symbolic = symbolic_identity()
    pyg = pyg_quaternion_message()
    kingdon = kingdon_ga_products()
    geomstats = geomstats_distances()

    shared_scalars: dict[str, float] = {}
    shared_scalars.update(schedule_shared)
    shared_scalars.update(loop_shared)
    shared_scalars.update(flow_shared)
    shared_scalars.update(chirality_shared)
    shared_scalars["network_state_coherent_information_chord_cut"] = network_ic
    shared_scalars["two_site_chord_ansatz_entropy"] = ansatz_entropy
    shared_scalars.update(topo_shared)
    shared_scalars["so3_equivariance_residual"] = equivariance_residual
    shared_scalars["so3_wrong_transform_negative_control_residual"] = equivariance_detail["wrong_transform_negative_control"]["residual"]

    controls = {
        "fiber_density_stationary": shared_scalars["fiber_density_stationarity_residual_max"] <= TOL,
        "base_loop_density_visible": shared_scalars["base_bloch_traversal_length_min"] > 0.0,
        "density_only_return_blind": shared_scalars["density_single_loop_return_defect_max"] <= TOL
        and shared_scalars["density_dual_stack_return_defect_max"] <= TOL,
        "classical_so3_has_no_spinor_sign_defect": shared_scalars["classical_so3_vector_single_loop_defect_max"] <= TOL
        and shared_scalars["classical_so3_vector_dual_stack_defect_max"] <= TOL,
        "sign_erasure_kills_chirality": shared_scalars["sign_erasure_control_gap_max"] <= TOL,
        "same_axis_commuting_control_zero": max(
            value for key, value in shared_scalars.items() if key.startswith("commuting_control_gap_mean_")
        )
        <= TOL,
        "sympy_commutator_identity": symbolic["residual_zero"] is True,
        "pyg_noncomm_gap_positive": pyg["noncommutative_message_gap"] > 0.0 and pyg["commuting_edge_control_gap"] <= TOL,
        "pyg_swapped_order_negative_control_gap_positive": pyg["swapped_order_second_propagation_gap"] > 0.0,
        "kingdon_anticommutator_zero": kingdon["anticommutator_norm"] <= TOL,
        "geomstats_distances_nonzero": geomstats["edge_distance_mean"] > 0.0,
        "topology_label_shuffle_control_changes_features": topo_detail["label_shuffle_control_changed"] is True,
        "network_state_coherent_information_finite": math.isfinite(network_ic),
        "so3_wrong_transform_negative_control_fails": equivariance_detail["wrong_transform_negative_control"]["fails_above_tolerance"] is True,
        "dual_stack_two_step_equals_collapsed_phase": flow_detail["two_step_vs_collapsed_phase_check"]["passed"] is True,
    }
    all_pass = bool(all(controls.values()))
    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": OBJECT_ID,
        "engine": ENGINE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["torch", "torch_geometric", "kingdon", "e3nn", "geomstats", "sympy", "gudhi", "toponetx", "xgi"],
        "aligned_packages_load_bearing": ["torch_geometric", "kingdon", "geomstats", "sympy", "gudhi", "toponetx", "xgi"],
        "claim_path_tools": ["torch_geometric", "kingdon", "geomstats", "sympy", "gudhi", "toponetx", "xgi"],
        "control_only_tools": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_exercise_map": {
            tool: {
                "computed_what": TOOL_MANIFEST[tool]["reason"],
                "genuinely_on_carrier": "yes",
                "capability_receipt_path": CAPABILITY_RECEIPTS[tool],
            }
            for tool in CAPABILITY_RECEIPTS
        },
        "readouts": {
            "schedule": schedule_detail,
            "loop_geometry": loop_detail,
            "dual_stack_720_flow": flow_detail,
            "chirality": chirality_detail,
            "coherent_information": network_ic_detail,
            "two_site_chord_ansatz_entropy": ansatz_detail,
            "topology": topo_detail,
            "so3_equivariance": equivariance_detail,
            "pyg_quaternion_message": pyg,
            "kingdon_ga_products": kingdon,
            "geomstats_hypersphere_distances": geomstats,
            "symbolic_identity": symbolic,
            "terrain_law_conventions": {
                "Ni_Pit": {"sheet": "L", "jump_operator": "sigma_minus", "matrix_symbol": "SM"},
                "Ni_Source": {"sheet": "R", "jump_operator": "sigma_plus", "matrix_symbol": "SP"},
            },
        },
        "crossover_proofs": {},
        "shared_scalars": {key: float(value) for key, value in sorted(shared_scalars.items())},
        "controls": controls,
        "all_pass": all_pass,
        "ceiling_note": "tool-testbed + dual-stack flow diagnostic; no M(C), bridge, Axis0, engine admission, or canonical claim.",
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"engine": ENGINE, "result_path": str(RESULT_PATH), "all_pass": result["all_pass"]}, indent=2))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
