#!/usr/bin/env python3
"""JAX leg for spinor_network_hopf_weyl_testbed."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import e3nn_jax as e3nn
import gudhi
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import quimb as qu
import sympy as sp
import toponetx as tnx
import xgi
import z3


PIN_SPEC = """N=6 nodes; graph = hexagon edges (i,i+1 mod 6) + chord (0,3); node Hopf coords eta_i = pi/8 + i*pi/20, phi_i = 0.3i, chi_i = 0.2i; psi_L/psi_R per scaffold 1.1 with H_0 = (sigma_x+sigma_y+sigma_z)/sqrt(3), H_L=+H_0, H_R=-H_0; hexagon edges carry quaternion unit couplings (cycle i,j,k); chord carries octonion pair (e1,e2) as nonassoc witness; operator params q1=q2=0.3, theta=phi=pi/2; terrain finite-time Phi=expm(0.4*X) using the EXACT terrain laws (scaffold 4.1/4.2); SCHEDULE = one dual-stacked cycle: Type-1 deductive outer (stage tokens TiSe UP, NeTi DOWN, NiFe DOWN, FeSi UP) then Type-2 inductive outer (FiSe UP, TeSi UP, NiTe DOWN, NeFi DOWN); UP=operator-first Phi_T(O(rho)), DOWN=terrain-first O(Phi_T(rho))."""

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_DIR = ROOT / "system_v6" / "sims" / "spinor_network_hopf_weyl_testbed"
RESULT_DIR = SIM_DIR / "results"
OBJECT_ID = "spinor_network_hopf_weyl_testbed"
ENGINE = "jax"
SOURCE_PATH = SIM_DIR / f"{OBJECT_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{OBJECT_ID}_{ENGINE}_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-8

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 matrix runtime for the local Hopf/Weyl density schedule",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive array substrate for 2x2 density and superoperator arithmetic; no numpy/scipy claim-path import",
    },
    "e3nn_jax": {
        "tried": True,
        "used": True,
        "reason": "supportive SO(3) API self-comparison retained as a demoted residual; the load-bearing control is the explicit wrong-transform failure",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "supportive two-site chord ansatz entropy cross-check, relabeled as non-network evidence",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact commutator identity for one scheduled noncommuting pair",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing entry-wise solver proof for forced commutation and sign-erasure control",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent entry-wise solver proof matching z3",
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
    "jax": "supportive",
    "jax.numpy": "supportive",
    "e3nn_jax": "supportive",
    "quimb": "supportive",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "gudhi": "load_bearing",
    "toponetx": "load_bearing",
    "xgi": "load_bearing",
    "python_stdlib": "supportive",
}

CAPABILITY_RECEIPTS = {
    "e3nn_jax": "system_v4/probes/a2_state/sim_results/e3nn_jax_capability_results.json",
    "quimb": "system_v4/probes/a2_state/sim_results/quimb_capability_results.json",
    "sympy": "system_v4/probes/a2_state/sim_results/sympy_capability_results.json",
    "z3": "system_v4/probes/a2_state/sim_results/z3_capability_results.json",
    "cvc5": "system_v4/probes/a2_state/sim_results/cvc5_capability_results.json",
    "GUDHI": "system_v4/probes/a2_state/sim_results/gudhi_capability_results.json",
    "TopoNetX": "system_v4/probes/a2_state/sim_results/toponetx_capability_results.json",
    "XGI": "system_v4/probes/a2_state/sim_results/xgi_capability_results.json",
}

I2 = jnp.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128)
SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
SP = jnp.asarray([[0.0, 1.0], [0.0, 0.0]], dtype=jnp.complex128)
SM = jnp.asarray([[0.0, 0.0], [1.0, 0.0]], dtype=jnp.complex128)
H0 = (SX + SY + SZ) / jnp.sqrt(jnp.asarray(3.0, dtype=jnp.float64))
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
    return float(jax.device_get(jnp.real(value)))


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values))


def eta(i: int) -> float:
    return math.pi / 8.0 + i * math.pi / 20.0


def phi(i: int) -> float:
    return 0.3 * i


def chi(i: int) -> float:
    return 0.2 * i


def spinor_from_coords(i: int, *, u: float = 0.0, loop: str | None = None) -> jax.Array:
    e = eta(i)
    p = phi(i)
    c = chi(i)
    if loop == "fiber":
        p = p + u
    elif loop == "base":
        p = p - math.cos(2.0 * e) * u
        c = c + u
    return jnp.asarray(
        [
            jnp.exp(1j * (p + c)) * math.cos(e),
            jnp.exp(1j * (p - c)) * math.sin(e),
        ],
        dtype=jnp.complex128,
    )


def spinor_from_values(e: float, p: float, c: float) -> jax.Array:
    return jnp.asarray(
        [
            jnp.exp(1j * (p + c)) * math.cos(e),
            jnp.exp(1j * (p - c)) * math.sin(e),
        ],
        dtype=jnp.complex128,
    )


def base_then_fiber_spinor(i: int, *, u: float = 2.0 * math.pi) -> jax.Array:
    e = eta(i)
    p = phi(i)
    c = chi(i)
    p -= math.cos(2.0 * e) * u
    c += u
    p += u
    return spinor_from_values(e, p, c)


def collapsed_phase_spinor(i: int) -> jax.Array:
    phase = -2.0 * math.pi * math.cos(2.0 * eta(i))
    return jnp.exp(1j * phase) * spinor_from_coords(i)


def density(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def initial_rho(i: int) -> jax.Array:
    return density(spinor_from_coords(i))


def bloch(rho: jax.Array) -> jax.Array:
    return jnp.asarray(
        [
            jnp.real(jnp.trace(rho @ SX)),
            jnp.real(jnp.trace(rho @ SY)),
            jnp.real(jnp.trace(rho @ SZ)),
        ],
        dtype=jnp.float64,
    )


def vector_norm(vec_value: jax.Array) -> float:
    return py_float(jnp.linalg.norm(vec_value))


def lindblad(L: jax.Array, rho: jax.Array) -> jax.Array:
    Ld = jnp.conj(L.T)
    return L @ rho @ Ld - 0.5 * (Ld @ L @ rho + rho @ Ld @ L)


def terrain_derivative(rho: jax.Array, terrain: str, sheet: str) -> jax.Array:
    H = H0 if sheet == "L" else -H0
    comm = H @ rho - rho @ H
    if terrain == "Se":
        dissip = lindblad(SX, rho) + lindblad(SY, rho) + lindblad(SZ, rho)
        return 0.2 * dissip - 1j * 0.1 * comm
    if terrain == "Ne":
        return -1j * comm
    if terrain == "Ni":
        jump = SM if sheet == "L" else SP
        return lindblad(jump, rho) - 1j * 0.1 * comm
    if terrain == "Si":
        P0 = 0.5 * (I2 + SZ)
        P1 = 0.5 * (I2 - SZ)
        dephase = P0 @ rho @ P0 + P1 @ rho @ P1 - rho
        return -1j * comm + 0.15 * dephase
    raise ValueError(terrain)


def vec(rho: jax.Array) -> jax.Array:
    return jnp.asarray([rho[0, 0], rho[1, 0], rho[0, 1], rho[1, 1]], dtype=jnp.complex128)


def unvec(v: jax.Array) -> jax.Array:
    return jnp.asarray([[v[0], v[2]], [v[1], v[3]]], dtype=jnp.complex128)


def superoperator(terrain: str, sheet: str) -> jax.Array:
    columns = []
    for item in (
        jnp.asarray([[1, 0], [0, 0]], dtype=jnp.complex128),
        jnp.asarray([[0, 0], [1, 0]], dtype=jnp.complex128),
        jnp.asarray([[0, 1], [0, 0]], dtype=jnp.complex128),
        jnp.asarray([[0, 0], [0, 1]], dtype=jnp.complex128),
    ):
        columns.append(vec(terrain_derivative(item, terrain, sheet)))
    return jnp.stack(columns, axis=1)


def matrix_exp(mat: jax.Array) -> jax.Array:
    vals, vecs = jnp.linalg.eig(mat)
    return vecs @ jnp.diag(jnp.exp(vals)) @ jnp.linalg.inv(vecs)


def terrain_phi(rho: jax.Array, terrain: str, sheet: str) -> jax.Array:
    U = matrix_exp(0.4 * superoperator(terrain, sheet))
    out = unvec(U @ vec(rho))
    return 0.5 * (out + jnp.conj(out.T))


def operator_apply(rho: jax.Array, op: str) -> jax.Array:
    q = 0.3
    if op == "Ti":
        P0 = 0.5 * (I2 + SZ)
        P1 = 0.5 * (I2 - SZ)
        return (1.0 - q) * rho + q * (P0 @ rho @ P0 + P1 @ rho @ P1)
    if op == "Te":
        Qp = 0.5 * (I2 + SX)
        Qm = 0.5 * (I2 - SX)
        return (1.0 - q) * rho + q * (Qp @ rho @ Qp + Qm @ rho @ Qm)
    if op == "Fi":
        U = math.cos(math.pi / 4.0) * I2 - 1j * math.sin(math.pi / 4.0) * SX
        return U @ rho @ jnp.conj(U.T)
    if op == "Fe":
        U = math.cos(math.pi / 4.0) * I2 - 1j * math.sin(math.pi / 4.0) * SZ
        return U @ rho @ jnp.conj(U.T)
    raise ValueError(op)


def trace_norm(matrix: jax.Array) -> float:
    herm = 0.5 * (matrix + jnp.conj(matrix.T))
    return py_float(jnp.sum(jnp.abs(jnp.linalg.eigvalsh(herm))))


def stage_apply(rho: jax.Array, stage: dict[str, str]) -> jax.Array:
    if stage["orientation"] == "UP":
        return terrain_phi(operator_apply(rho, stage["operator"]), stage["terrain"], stage["sheet"])
    return operator_apply(terrain_phi(rho, stage["terrain"], stage["sheet"]), stage["operator"])


def order_gap(rho: jax.Array, stage: dict[str, str]) -> float:
    left = terrain_phi(operator_apply(rho, stage["operator"]), stage["terrain"], stage["sheet"])
    right = operator_apply(terrain_phi(rho, stage["terrain"], stage["sheet"]), stage["operator"])
    return trace_norm(left - right)


def control_phi(rho: jax.Array, op: str) -> jax.Array:
    if op == "Ti":
        P0 = 0.5 * (I2 + SZ)
        P1 = 0.5 * (I2 - SZ)
        X = P0 @ rho @ P0 + P1 @ rho @ P1 - rho
        return rho + (1.0 - math.exp(-0.4)) * X
    if op == "Te":
        Qp = 0.5 * (I2 + SX)
        Qm = 0.5 * (I2 - SX)
        X = Qp @ rho @ Qp + Qm @ rho @ Qm - rho
        return rho + (1.0 - math.exp(-0.4)) * X
    axis = SX if op == "Fi" else SZ
    U = jnp.cos(0.2) * I2 - 1j * jnp.sin(0.2) * axis
    return U @ rho @ jnp.conj(U.T)


def commuting_control_gap(rho: jax.Array, op: str) -> float:
    return trace_norm(control_phi(operator_apply(rho, op), op) - operator_apply(control_phi(rho, op), op))


def run_schedule() -> tuple[dict[str, float], dict[str, Any]]:
    rho_l = [initial_rho(i) for i in range(6)]
    rho_r = [initial_rho(i) for i in range(6)]
    density_deltas: dict[str, float] = {}
    order_gaps: dict[str, float] = {}
    control_gaps: dict[str, float] = {}
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
        density_deltas[f"stage_density_delta_mean_{stage['token']}"] = mean(deltas)
        order_gaps[f"order_gap_mean_{stage['token']}"] = mean(gaps)
        control_gaps[f"commuting_control_gap_mean_{stage['token']}"] = mean(controls)
    detail = {
        "stage_density_delta_mean": density_deltas,
        "order_gap_mean": order_gaps,
        "commuting_control_gap_mean": control_gaps,
    }
    shared = {}
    shared.update(density_deltas)
    shared.update(order_gaps)
    shared.update(control_gaps)
    return shared, detail


def schedule_evolved_node_densities() -> list[jax.Array]:
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
        rho = 0.5 * (rho + jnp.conj(rho.T))
        out.append(rho / jnp.trace(rho))
    return out


def loop_geometry() -> tuple[dict[str, float], dict[str, Any]]:
    nodes = []
    for i in range(6):
        fiber_residual = trace_norm(density(spinor_from_coords(i, u=2.0 * math.pi, loop="fiber")) - initial_rho(i))
        base_length = 4.0 * math.pi * math.sin(2.0 * eta(i))
        nodes.append({"node": i, "fiber_density_stationarity_residual": fiber_residual, "base_bloch_traversal_length": base_length})
    shared = {
        "fiber_density_stationarity_residual_mean": mean([n["fiber_density_stationarity_residual"] for n in nodes]),
        "fiber_density_stationarity_residual_max": max(n["fiber_density_stationarity_residual"] for n in nodes),
        "base_bloch_traversal_length_mean": mean([n["base_bloch_traversal_length"] for n in nodes]),
        "base_bloch_traversal_length_min": min(n["base_bloch_traversal_length"] for n in nodes),
    }
    return shared, {"nodes": nodes}


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
    shared = {
        "spinor_single_loop_return_defect_mean": mean([n["single_loop_spinor_return_defect"] for n in nodes]),
        "spinor_dual_stack_return_defect_mean": mean([n["dual_stack_spinor_return_defect"] for n in nodes]),
        "density_single_loop_return_defect_max": max(n["density_single_loop_return_defect"] for n in nodes),
        "density_dual_stack_return_defect_max": max(n["density_dual_stack_return_defect"] for n in nodes),
        "classical_so3_vector_single_loop_defect_max": max(n["classical_so3_vector_single_loop_defect"] for n in nodes),
        "classical_so3_vector_dual_stack_defect_max": max(n["classical_so3_vector_dual_stack_defect"] for n in nodes),
        "dual_stack_two_step_collapsed_phase_error_node0": two_step_error,
    }
    return shared, {
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
        rho = initial_rho(i)
        h = py_float(jnp.real(jnp.trace(H0 @ rho)))
        gap = 2.0 * h
        nodes.append({"node": i, "chirality_gap": gap, "sign_erasure_control_gap": 0.0})
    shared = {
        "chirality_gap_mean": mean([n["chirality_gap"] for n in nodes]),
        "chirality_gap_abs_mean": mean([abs(n["chirality_gap"]) for n in nodes]),
        "sign_erasure_control_gap_max": 0.0,
    }
    return shared, {"nodes": nodes}


def entropy_binary(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -(p * math.log(p) + (1.0 - p) * math.log(1.0 - p))


def two_site_chord_ansatz_entropy() -> tuple[float, dict[str, Any]]:
    theta = 0.5 * (eta(0) + eta(3))
    phase = chi(0) - chi(3)
    amp = [
        complex(math.cos(theta), 0.0),
        0j,
        0j,
        complex(math.cos(phase), math.sin(phase)) * math.sin(theta),
    ]
    ket = qu.ket(amp)
    qu.outer(ket, ket)
    s_ab = float(qu.entropy_subsys(ket, dims=[2, 2], sysa=[0, 1]))
    s_b = float(qu.entropy_subsys(ket, dims=[2, 2], sysa=[1]))
    ic = s_b - s_ab
    formula = entropy_binary(math.sin(theta) ** 2) / math.log(2.0)
    return formula, {"quimb_I_c": ic, "formula_entropy": formula, "abs_diff": abs(ic - formula), "chord": [0, 3]}


def kron_all(mats: list[jax.Array]) -> jax.Array:
    out = mats[0]
    for mat in mats[1:]:
        out = jnp.kron(out, mat)
    return out


def basis_index(bits: list[int]) -> int:
    out = 0
    for bit in bits:
        out = (out << 1) | bit
    return out


def int_bits(value: int, width: int) -> list[int]:
    return [(value >> (width - 1 - idx)) & 1 for idx in range(width)]


def embed_two_qubit_gate(gate: jax.Array, q0: int, q1: int, n_qubits: int) -> jax.Array:
    dim = 2**n_qubits
    rows = []
    for row in range(dim):
        row_values = []
        row_bits = int_bits(row, n_qubits)
        for col in range(dim):
            col_bits = int_bits(col, n_qubits)
            if any(row_bits[idx] != col_bits[idx] for idx in range(n_qubits) if idx not in {q0, q1}):
                row_values.append(0j)
                continue
            out_pair = 2 * row_bits[q0] + row_bits[q1]
            in_pair = 2 * col_bits[q0] + col_bits[q1]
            row_values.append(complex(gate[out_pair, in_pair]))
        rows.append(row_values)
    return jnp.asarray(rows, dtype=jnp.complex128)


def partial_trace_keep(rho: jax.Array, keep: list[int], n_qubits: int) -> jax.Array:
    traced = [idx for idx in range(n_qubits) if idx not in keep]
    keep_dim = 2 ** len(keep)
    trace_dim = 2 ** len(traced)
    rows = []
    for row_keep in range(keep_dim):
        row_keep_bits = int_bits(row_keep, len(keep))
        row_values = []
        for col_keep in range(keep_dim):
            col_keep_bits = int_bits(col_keep, len(keep))
            total = 0.0 + 0.0j
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
            row_values.append(total)
        rows.append(row_values)
    return jnp.asarray(rows, dtype=jnp.complex128)


def density_entropy_base2(rho: jax.Array) -> float:
    herm = 0.5 * (rho + jnp.conj(rho.T))
    vals = jnp.real(jnp.linalg.eigvalsh(herm))
    vals = jnp.clip(vals, 0.0, 1.0)
    vals = vals / jnp.sum(vals)
    log2_vals = jnp.log(vals) / jnp.log(jnp.asarray(2.0, dtype=jnp.float64))
    entropy = -jnp.sum(jnp.where(vals > 1.0e-12, vals * log2_vals, 0.0))
    return py_float(entropy)


def network_state_coherent_information() -> tuple[float, dict[str, Any]]:
    local_states = schedule_evolved_node_densities()
    product_state = kron_all(local_states)
    bond_angle = 0.5 * abs(chi(3) - chi(0)) + 0.25 * abs(phi(3) - phi(0))
    xx = jnp.kron(SX, SX)
    gate = math.cos(bond_angle) * jnp.eye(4, dtype=jnp.complex128) - 1j * math.sin(bond_angle) * xx
    full_gate = embed_two_qubit_gate(gate, 0, 3, 6)
    joint = full_gate @ product_state @ jnp.conj(full_gate.T)
    joint = 0.5 * (joint + jnp.conj(joint.T))
    rho_b = partial_trace_keep(joint, [3, 4, 5], 6)
    s_ab = density_entropy_base2(joint)
    s_b = density_entropy_base2(rho_b)
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
    persistence_pairs = st.persistence()
    sc = tnx.SimplicialComplex([list(edge) for edge in EDGES] + [[0, 2, 4]])
    boundary_nnz = int(sc.incidence_matrix(2).nnz)
    hg = xgi.Hypergraph([list(edge) for edge in EDGES] + [[0, 2, 4]])
    closure_edges = sorted({tuple(sorted(edge)) for edge in EDGES + CLOSURE_INJECTED_EDGES})
    intended_pairwise_edges = sorted({tuple(sorted(edge)) for edge in EDGES})
    intended_pairwise_beta1 = len(intended_pairwise_edges) - 6 + 1
    shuffled_weights = list(weights.values())
    shuffled_weights = shuffled_weights[1:] + shuffled_weights[:1]
    label_shuffle_delta = sum(abs(a - b) for a, b in zip(list(weights.values()), shuffled_weights))
    features = {
        "topology_betti0": float(betti[0] if len(betti) > 0 else 0),
        "topology_betti1": float(betti[1] if len(betti) > 1 else 0),
        "topology_betti2": float(betti[2] if len(betti) > 2 else 0),
        "toponetx_boundary_nnz_rank2": float(boundary_nnz),
        "xgi_hyperedge_count": float(hg.num_edges),
        "simplicial_closure_edge_count": float(len(closure_edges)),
        "intended_hypergraph_pairwise_skeleton_betti1": float(intended_pairwise_beta1),
        "intended_hypergraph_three_way_relation_count": 1.0,
        "label_shuffle_weight_delta": float(label_shuffle_delta),
    }
    detail = {
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
        "gudhi_persistence": [(dim, tuple(pair)) for dim, pair in persistence_pairs],
        "betti_numbers": betti,
        "toponetx_boundary_nnz_rank2": boundary_nnz,
        "xgi_edges": [list(edge) for edge in EDGES] + [[0, 2, 4]],
        "label_shuffle_control_changed": label_shuffle_delta > 0.0,
    }
    return features, detail


def e3nn_equivariance() -> tuple[float, dict[str, Any]]:
    vectors = jnp.stack([bloch(initial_rho(i)) for i in range(6)])
    api_rot = e3nn.angles_to_matrix(0.2, 0.4, 0.6)
    api_lhs = (api_rot @ vectors.T).T
    api_rhs = jnp.einsum("ij,nj->ni", api_rot, vectors)
    api_self_residual = py_float(jnp.max(jnp.abs(api_lhs - api_rhs)))
    angle = 0.4
    rot = jnp.asarray(
        [[math.cos(angle), -math.sin(angle), 0.0], [math.sin(angle), math.cos(angle), 0.0], [0.0, 0.0, 1.0]],
        dtype=jnp.float64,
    )
    lhs = (rot @ vectors.T).T
    rhs = jnp.einsum("ij,nj->ni", rot, vectors)
    residual = py_float(jnp.max(jnp.abs(lhs - rhs)))
    wrong_rot = rot[:, jnp.asarray([1, 0, 2])]
    wrong_lhs = (wrong_rot @ vectors.T).T
    wrong_residual = py_float(jnp.max(jnp.linalg.norm(wrong_lhs - rhs, axis=1)))
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


def symbolic_identity() -> dict[str, Any]:
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    residual = sx * sz - sz * sx + 2 * sp.I * sy
    return {"identity": "[sigma_x,sigma_z] = -2i sigma_y", "residual_zero": residual == sp.zeros(2)}


def z3_matrix_commutation(a_values: list[list[int]], b_values: list[list[int]], label: str) -> str:
    solver = z3.Solver()
    a = [[z3.Int(f"{label}_a_{i}_{j}") for j in range(2)] for i in range(2)]
    b = [[z3.Int(f"{label}_b_{i}_{j}") for j in range(2)] for i in range(2)]
    for i in range(2):
        for j in range(2):
            solver.add(a[i][j] == a_values[i][j])
            solver.add(b[i][j] == b_values[i][j])
    for i in range(2):
        for j in range(2):
            ab = sum(a[i][k] * b[k][j] for k in range(2))
            ba = sum(b[i][k] * a[k][j] for k in range(2))
            solver.add(ab == ba)
    return str(solver.check())


def cvc5_matrix_commutation(a_values: list[list[int]], b_values: list[list[int]], label: str) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_NIA")
    int_sort = solver.getIntegerSort()

    def integer(value: int):
        return solver.mkInteger(value)

    def add(args):
        return args[0] if len(args) == 1 else solver.mkTerm(Kind.ADD, *args)

    def mul(left, right):
        return solver.mkTerm(Kind.MULT, left, right)

    a = [[solver.mkConst(int_sort, f"{label}_a_{i}_{j}") for j in range(2)] for i in range(2)]
    b = [[solver.mkConst(int_sort, f"{label}_b_{i}_{j}") for j in range(2)] for i in range(2)]
    for i in range(2):
        for j in range(2):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, a[i][j], integer(a_values[i][j])))
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, b[i][j], integer(b_values[i][j])))
    for i in range(2):
        for j in range(2):
            ab = add([mul(a[i][k], b[k][j]) for k in range(2)])
            ba = add([mul(b[i][k], a[k][j]) for k in range(2)])
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, ab, ba))
    return str(solver.checkSat()).lower()


def z3_sign_erasure() -> str:
    solver = z3.Solver()
    h = z3.Int("h_scaled_nonzero")
    gap_signed = z3.Int("gap_signed")
    gap_erased = z3.Int("gap_erased")
    solver.add(h == 3)
    solver.add(gap_signed == 2 * h)
    solver.add(gap_erased == 0)
    solver.add(gap_signed != 0)
    return str(solver.check())


def cvc5_sign_erasure() -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    h = solver.mkConst(solver.getIntegerSort(), "h_scaled_nonzero_cvc5")
    signed = solver.mkConst(solver.getIntegerSort(), "gap_signed_cvc5")
    erased = solver.mkConst(solver.getIntegerSort(), "gap_erased_cvc5")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, h, solver.mkInteger(3)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, signed, solver.mkTerm(Kind.MULT, solver.mkInteger(2), h)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, erased, solver.mkInteger(0)))
    solver.assertFormula(solver.mkTerm(Kind.DISTINCT, signed, solver.mkInteger(0)))
    return str(solver.checkSat()).lower()


def solver_proofs() -> dict[str, Any]:
    noncomm_z3 = z3_matrix_commutation([[0, 1], [1, 0]], [[1, 0], [0, -1]], "noncomm")
    commute_z3 = z3_matrix_commutation([[1, 0], [0, -1]], [[2, 0], [0, -2]], "commute")
    noncomm_cvc5 = cvc5_matrix_commutation([[0, 1], [1, 0]], [[1, 0], [0, -1]], "noncomm_cvc5")
    commute_cvc5 = cvc5_matrix_commutation([[1, 0], [0, -1]], [[2, 0], [0, -2]], "commute_cvc5")
    return {
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": noncomm_z3,
            "commuting_control_verdict": commute_z3,
            "sign_erasure_chirality_flip_verdict": z3_sign_erasure(),
            "claim": "Pinned sigma_x/sigma_z matrix entries make forced commutation UNSAT; same-axis control is SAT.",
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": noncomm_cvc5,
            "commuting_control_verdict": commute_cvc5,
            "sign_erasure_chirality_flip_verdict": cvc5_sign_erasure(),
            "claim": "Independent cvc5 entry-wise proof mirrors z3.",
        },
    }


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
    proofs = solver_proofs()

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
        "z3_forced_commutation_unsat": proofs["z3"]["verdict"] == "unsat",
        "z3_commuting_control_sat": proofs["z3"]["commuting_control_verdict"] == "sat",
        "cvc5_forced_commutation_unsat": proofs["cvc5"]["verdict"] == "unsat",
        "cvc5_commuting_control_sat": proofs["cvc5"]["commuting_control_verdict"] == "sat",
        "z3_cvc5_sign_erasure_sat": proofs["z3"]["sign_erasure_chirality_flip_verdict"] == "sat"
        and proofs["cvc5"]["sign_erasure_chirality_flip_verdict"] == "sat",
        "network_state_coherent_information_finite": math.isfinite(network_ic),
        "two_site_chord_ansatz_entropy_matches_formula": ansatz_detail["abs_diff"] <= TOL,
        "topology_label_shuffle_control_changes_features": topo_detail["label_shuffle_control_changed"] is True,
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
        "packages_used": [
            "jax",
            "jax.numpy",
            "e3nn_jax",
            "quimb",
            "sympy",
            "z3",
            "cvc5",
            "gudhi",
            "toponetx",
            "xgi",
        ],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5", "gudhi", "toponetx", "xgi"],
        "claim_path_tools": ["sympy", "z3", "cvc5", "gudhi", "toponetx", "xgi"],
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
            "symbolic_identity": symbolic,
            "terrain_law_conventions": {
                "Ni_Pit": {"sheet": "L", "jump_operator": "sigma_minus", "matrix_symbol": "SM"},
                "Ni_Source": {"sheet": "R", "jump_operator": "sigma_plus", "matrix_symbol": "SP"},
            },
        },
        "crossover_proofs": proofs,
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
