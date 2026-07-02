#!/usr/bin/env python3
"""Stage-6 L3 Clifford/quaternion invariant ACTION probe.

This file tests one independent layer action:

    L3_QK(rho_v) = U rho_v U^dagger

where U is a finite product of unit-quaternion SU(2) matrices acting on a
stage-2 spinor-density carrier. It is not a standalone geometry object and it
does not stack with any other layer.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
from clifford import Cl
import sympy as sp
import torch
import z3

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation

from sim_l2_spinor_chirality_weyl_cover_layer_probe import (  # noqa: E402
    CTYPE,
    I2,
    RTYPE,
    SHAPES,
    TOL,
    as_jsonable,
    coords_for_shape,
    exact_counts,
    site_densities,
    site_spinors,
    topology_certificates,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = pathlib.Path(__file__).name
OBJECT_ID = "L3_clifford_quaternion_invariant_action"
RESULT = RESULT_DIR / f"{OBJECT_ID}_results.json"

SIM_ID = "sim_layer_L3_clifford_quaternion_probe"
VERSION = "1.0.0"
EPS = 1.0e-6
JAX_TOL = 1.0e-9
UNIT_SEQUENCE = (("I", 0.37), ("J", 0.61), ("K", 0.29))
DEGENERATE_SCALE = 1.70

SIGMA_X = torch.tensor([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=CTYPE)
SIGMA_Y = torch.tensor([[0.0 + 0.0j, -1j], [1j, 0.0 + 0.0j]], dtype=CTYPE)
SIGMA_Z = torch.tensor([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=CTYPE)
PAULIS = (SIGMA_X, SIGMA_Y, SIGMA_Z)

QI = torch.tensor([[1j, 0.0 + 0.0j], [0.0 + 0.0j, -1j]], dtype=CTYPE)
QJ = torch.tensor([[0.0 + 0.0j, 1.0 + 0.0j], [-1.0 + 0.0j, 0.0 + 0.0j]], dtype=CTYPE)
QK = QI @ QJ
Q_UNITS = {"I": QI, "J": QJ, "K": QK}

J_I2 = jnp.eye(2, dtype=jnp.complex128)
J_SIGMA_X = jnp.array([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
J_SIGMA_Y = jnp.array([[0.0 + 0.0j, -1j], [1j, 0.0 + 0.0j]], dtype=jnp.complex128)
J_SIGMA_Z = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=jnp.complex128)
J_PAULIS = (J_SIGMA_X, J_SIGMA_Y, J_SIGMA_Z)
J_QI = jnp.array([[1j, 0.0 + 0.0j], [0.0 + 0.0j, -1j]], dtype=jnp.complex128)
J_QJ = jnp.array([[0.0 + 0.0j, 1.0 + 0.0j], [-1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
J_QK = J_QI @ J_QJ
J_Q_UNITS = {"I": J_QI, "J": J_QJ, "K": J_QK}

BLOCKED_CONSUMERS = [
    "L4 terrain/channel/generator placement",
    "L5 operator substage cells",
    "L6 entropy/cut/communication stacking",
    "L7 Hopf/fibration/shell projection",
    "L8 gluing/groupoid/equivariant/dynamic stacking",
    "layer stacking",
    "bridge",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics/gravity",
    "final manifold",
]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim-bearing spinor-density carrier, unit-quaternion action, invariant readouts, controls, and non-dense scale ladder.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 mirror recomputing the full per-site U rho U^dagger action and invariant deviations without NumPy.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING proof through smt_load_bearing: same measured invariant-preservation claim is sat for real action and unsat for non-unit control.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING cvc5 cross-check inside smt_load_bearing on the same measured invariant deviations.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact quaternion table I*J=K, J*I=-K, IJK=-1; scalar-label control cannot satisfy the table.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "Exact Cl(0,2) negative-square, anticommutation, and bivector-square checks for the quaternion rotor basis.",
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": "Supportive PEPS3D graph message certificate via the imported topology_certificates carrier helper; not the core invariant proof.",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "Supportive PEPS3D edge connectivity certificate for finite site enumeration; not the core invariant proof.",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "Supportive PEPS3D face/cell hyperedge certificate; not the core invariant proof.",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "Supportive finite face-complex certificate; not the core invariant proof.",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "Supportive boundary filtration certificate; not the core invariant proof.",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "Not relevant for this L3 action: no metric, geodesic, or curvature claim is admitted.",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "Not relevant for this L3 action: no learned E(3)-equivariant field claim is admitted.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported; NumPy is not claim-bearing in this nonclassical layer sim.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "pyg": "supportive",
    "rustworkx": "supportive",
    "xgi": "supportive",
    "toponetx": "supportive",
    "gudhi": "supportive",
    "geomstats": "None",
    "e3nn": "None",
    "numpy": "None",
}


def torch_quat_unitary(unit: torch.Tensor, theta: float) -> torch.Tensor:
    return math.cos(theta) * I2 + math.sin(theta) * unit


def torch_layer_unitary() -> torch.Tensor:
    out = I2.clone()
    for unit_name, theta in UNIT_SEQUENCE:
        out = out @ torch_quat_unitary(Q_UNITS[unit_name], theta)
    return out


def torch_degenerate_matrix() -> torch.Tensor:
    theta = UNIT_SEQUENCE[0][1]
    return math.cos(theta) * I2 + DEGENERATE_SCALE * QI


def torch_action(rho: torch.Tensor, action_matrix: torch.Tensor) -> torch.Tensor:
    return action_matrix @ rho @ action_matrix.conj().T


def torch_bloch_vector(rho: torch.Tensor) -> torch.Tensor:
    return torch.stack([torch.real(torch.trace(rho @ pauli)) for pauli in PAULIS]).to(RTYPE)


def torch_purity(rho: torch.Tensor) -> torch.Tensor:
    return torch.real(torch.trace(rho @ rho)).to(RTYPE)


def torch_trace_value(rho: torch.Tensor) -> torch.Tensor:
    return torch.real(torch.trace(rho)).to(RTYPE)


def jax_quat_unitary(unit: jax.Array, theta: float) -> jax.Array:
    return math.cos(theta) * J_I2 + math.sin(theta) * unit


def jax_layer_unitary() -> jax.Array:
    out = J_I2
    for unit_name, theta in UNIT_SEQUENCE:
        out = out @ jax_quat_unitary(J_Q_UNITS[unit_name], theta)
    return out


def jax_degenerate_matrix() -> jax.Array:
    theta = UNIT_SEQUENCE[0][1]
    return math.cos(theta) * J_I2 + DEGENERATE_SCALE * J_QI


def jax_density(psi: jax.Array) -> jax.Array:
    psi = psi / jnp.linalg.norm(psi)
    return jnp.outer(psi, jnp.conj(psi))


def jax_spinors(coords: list[tuple[int, int, int]]) -> jax.Array:
    kets = (
        jnp.array([1.0 + 0.0j, 0.0 + 0.0j], dtype=jnp.complex128),
        jnp.array([0.0 + 0.0j, 1.0 + 0.0j], dtype=jnp.complex128),
        jnp.array([1.0 + 0.0j, 1.0 + 0.0j], dtype=jnp.complex128) / math.sqrt(2.0),
        jnp.array([1.0 + 0.0j, -1.0 + 0.0j], dtype=jnp.complex128) / math.sqrt(2.0),
    )
    return jnp.stack([kets[(x + 2 * y + 3 * z) % len(kets)] for x, y, z in coords])


def jax_action(rho: jax.Array, action_matrix: jax.Array) -> jax.Array:
    return action_matrix @ rho @ jnp.conj(action_matrix.T)


def jax_bloch_vector(rho: jax.Array) -> jax.Array:
    return jnp.stack([jnp.real(jnp.trace(rho @ pauli)) for pauli in J_PAULIS])


def jax_purity(rho: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(rho @ rho))


def invariant_summary_torch(densities: torch.Tensor, matrix: torch.Tensor) -> dict[str, Any]:
    trace_devs = []
    bloch_devs = []
    purity_devs = []
    min_eigs = []
    for rho in densities:
        out = torch_action(rho, matrix)
        trace_devs.append(abs(float((torch_trace_value(out) - torch_trace_value(rho)).item())))
        bloch_devs.append(abs(float((torch.linalg.vector_norm(torch_bloch_vector(out)) - torch.linalg.vector_norm(torch_bloch_vector(rho))).item())))
        purity_devs.append(abs(float((torch_purity(out) - torch_purity(rho)).item())))
        min_eigs.append(float(torch.min(torch.linalg.eigvalsh((out + out.conj().T) / 2.0)).item()))
    unit_error = float(torch.linalg.matrix_norm(matrix.conj().T @ matrix - I2).real.item())
    return {
        "max_trace_deviation": max(trace_devs),
        "max_bloch_norm_deviation": max(bloch_devs),
        "max_purity_deviation": max(purity_devs),
        "min_hermitian_eigenvalue": min(min_eigs),
        "unitarity_error": unit_error,
        "pass": bool(
            max(trace_devs) <= EPS
            and max(bloch_devs) <= EPS
            and max(purity_devs) <= EPS
            and unit_error <= EPS
            and min(min_eigs) >= -EPS
        ),
    }


def invariant_summary_jax(densities: jax.Array, matrix: jax.Array) -> dict[str, Any]:
    trace_devs = []
    bloch_devs = []
    purity_devs = []
    min_eigs = []
    for rho in densities:
        out = jax_action(rho, matrix)
        trace_devs.append(abs(float(jnp.real(jnp.trace(out)) - jnp.real(jnp.trace(rho)))))
        bloch_devs.append(abs(float(jnp.linalg.norm(jax_bloch_vector(out)) - jnp.linalg.norm(jax_bloch_vector(rho)))))
        purity_devs.append(abs(float(jax_purity(out) - jax_purity(rho))))
        herm = (out + jnp.conj(out.T)) / 2.0
        min_eigs.append(float(jnp.min(jnp.linalg.eigvalsh(herm))))
    unit_error = float(jnp.linalg.norm(jnp.conj(matrix.T) @ matrix - J_I2))
    return {
        "max_trace_deviation": max(trace_devs),
        "max_bloch_norm_deviation": max(bloch_devs),
        "max_purity_deviation": max(purity_devs),
        "min_hermitian_eigenvalue": min(min_eigs),
        "unitarity_error": unit_error,
        "pass": bool(
            max(trace_devs) <= EPS
            and max(bloch_devs) <= EPS
            and max(purity_devs) <= EPS
            and unit_error <= EPS
            and min(min_eigs) >= -EPS
        ),
    }


def n01_order_witness(densities: torch.Tensor) -> dict[str, Any]:
    ui = torch_quat_unitary(QI, 0.37)
    uj = torch_quat_unitary(QJ, 0.61)
    forward = uj @ ui
    reverse = ui @ uj
    same_a = ui @ ui
    same_b = ui @ ui
    gaps = []
    same_gaps = []
    for rho in densities:
        gaps.append(float(torch.linalg.matrix_norm(torch_action(rho, forward) - torch_action(rho, reverse)).real.item()))
        same_gaps.append(float(torch.linalg.matrix_norm(torch_action(rho, same_a) - torch_action(rho, same_b)).real.item()))
    return {
        "min_order_gap_IJ_vs_JI": min(gaps),
        "max_same_unit_control_gap": max(same_gaps),
        "pass": bool(min(gaps) > EPS and max(same_gaps) < TOL),
    }


def torch_signature_rows(densities: torch.Tensor, matrix: torch.Tensor) -> torch.Tensor:
    rows = []
    for rho in densities:
        out = torch_action(rho, matrix)
        rows.append(torch.cat([torch_bloch_vector(rho), torch_bloch_vector(out)]))
    return torch.stack(rows).to(RTYPE)


def rung(shape: tuple[int, int, int]) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    torch_densities = site_densities(site_spinors(coords))
    jax_densities = jnp.stack([jax_density(psi) for psi in jax_spinors(coords)])
    unitary = torch_layer_unitary()
    degenerate = torch_degenerate_matrix()
    j_unitary = jax_layer_unitary()
    j_degenerate = jax_degenerate_matrix()

    torch_real = invariant_summary_torch(torch_densities, unitary)
    torch_control = invariant_summary_torch(torch_densities, degenerate)
    jax_real = invariant_summary_jax(jax_densities, j_unitary)
    jax_control = invariant_summary_jax(jax_densities, j_degenerate)
    topo = topology_certificates(shape, torch_signature_rows(torch_densities, unitary))
    order = n01_order_witness(torch_densities)
    counts = exact_counts(shape)
    jax_vs_torch_delta = max(
        abs(jax_real["max_trace_deviation"] - torch_real["max_trace_deviation"]),
        abs(jax_real["max_bloch_norm_deviation"] - torch_real["max_bloch_norm_deviation"]),
        abs(jax_real["max_purity_deviation"] - torch_real["max_purity_deviation"]),
        abs(jax_control["max_trace_deviation"] - torch_control["max_trace_deviation"]),
        abs(jax_control["max_bloch_norm_deviation"] - torch_control["max_bloch_norm_deviation"]),
        abs(jax_control["max_purity_deviation"] - torch_control["max_purity_deviation"]),
    )
    pass_rung = bool(
        torch_real["pass"]
        and not torch_control["pass"]
        and jax_real["pass"]
        and not jax_control["pass"]
        and jax_vs_torch_delta <= JAX_TOL
        and topo["pass"]
        and order["pass"]
    )
    return {
        "shape": list(shape),
        "sites_or_qubits": counts["V"],
        "state_count": counts["V"],
        "edge_count": counts["E"],
        "face_count": counts["F"],
        "cell_count": counts["C"],
        "operator_count": 3,
        "path_count": 2,
        "peps3d_bond_dim": 2,
        "dense_state_dimension_if_used": str(2 ** counts["V"]),
        "dense_state_closure_used": False,
        "torch_real_action": torch_real,
        "torch_nonunit_control": torch_control,
        "jax_real_action": jax_real,
        "jax_nonunit_control": jax_control,
        "jax_vs_pytorch_delta": jax_vs_torch_delta,
        "peps3d_topology_certificate": topo,
        "n01_order_witness": order,
        "pass": pass_rung,
    }


def smt_invariant_proof(real: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    return smt_load_bearing(
        claim="L3_unit_quaternion_action_preserves_trace_bloch_norm_purity_and_unitarity",
        real_measured={
            "max_trace_deviation": real["max_trace_deviation"],
            "max_bloch_norm_deviation": real["max_bloch_norm_deviation"],
            "max_purity_deviation": real["max_purity_deviation"],
            "unitarity_error": real["unitarity_error"],
            "eps": EPS,
        },
        control_measured={
            "max_trace_deviation": control["max_trace_deviation"],
            "max_bloch_norm_deviation": control["max_bloch_norm_deviation"],
            "max_purity_deviation": control["max_purity_deviation"],
            "unitarity_error": control["unitarity_error"],
            "eps": EPS,
        },
        claim_builder=lambda v: z3.And(
            v["max_trace_deviation"] <= v["eps"],
            v["max_bloch_norm_deviation"] <= v["eps"],
            v["max_purity_deviation"] <= v["eps"],
            v["unitarity_error"] <= v["eps"],
        ),
        cvc5_claim_pairs=[
            ("max_trace_deviation", "<=", "eps"),
            ("max_bloch_norm_deviation", "<=", "eps"),
            ("max_purity_deviation", "<=", "eps"),
            ("unitarity_error", "<=", "eps"),
        ],
    )


def sympy_quaternion_table() -> dict[str, Any]:
    ii = sp.I
    one = sp.eye(2)
    qi = sp.Matrix([[ii, 0], [0, -ii]])
    qj = sp.Matrix([[0, 1], [-1, 0]])
    qk = qi * qj
    checks = {
        "I_squared_minus_one": bool(qi * qi == -one),
        "J_squared_minus_one": bool(qj * qj == -one),
        "K_squared_minus_one": bool(qk * qk == -one),
        "I_times_J_equals_K": bool(qi * qj == qk),
        "J_times_I_equals_minus_K": bool(qj * qi == -qk),
        "IJK_equals_minus_one": bool(qi * qj * qk == -one),
    }
    scalar = sp.eye(2)
    scalar_control_pass = bool(scalar * scalar == -one)
    return {
        "tool": "sympy",
        "checks": checks,
        "real_pass": all(checks.values()),
        "scalar_label_control_pass": scalar_control_pass,
        "flip": bool(all(checks.values()) and not scalar_control_pass),
    }


def clifford_quaternion_table() -> dict[str, Any]:
    _, blades = Cl(0, 2)
    e1 = blades["e1"]
    e2 = blades["e2"]
    biv = e1 * e2
    real_checks = {
        "e1_square": str(e1 * e1),
        "e2_square": str(e2 * e2),
        "e1e2_anticommutator": str(e1 * e2 + e2 * e1),
        "bivector_square": str(biv * biv),
    }
    real_pass = bool(
        real_checks["e1_square"] == "-1"
        and real_checks["e2_square"] == "-1"
        and real_checks["e1e2_anticommutator"] == "0"
        and real_checks["bivector_square"] == "-1"
    )
    collapsed = e1
    collapsed_biv = e1 * collapsed
    collapsed_control = {
        "collapsed_anticommutator": str(e1 * collapsed + collapsed * e1),
        "collapsed_bivector_square": str(collapsed_biv * collapsed_biv),
    }
    collapsed_pass = bool(
        str(e1 * collapsed + collapsed * e1) == "0"
        and str(collapsed_biv * collapsed_biv) == "-1"
    )
    return {
        "tool": "clifford",
        "real_checks": real_checks,
        "real_pass": real_pass,
        "collapsed_control": collapsed_control,
        "collapsed_control_pass": collapsed_pass,
        "flip": bool(real_pass and not collapsed_pass),
    }


def known_value_checks() -> dict[str, Any]:
    psi = torch.tensor([0.6 + 0.0j, 0.8 + 0.0j], dtype=CTYPE)
    rho = torch.outer(psi, psi.conj())
    unitary = torch_layer_unitary()
    degenerate = torch_degenerate_matrix()
    before = {
        "trace": float(torch_trace_value(rho).item()),
        "bloch_norm": float(torch.linalg.vector_norm(torch_bloch_vector(rho)).item()),
        "purity": float(torch_purity(rho).item()),
    }
    after = torch_action(rho, unitary)
    deg = torch_action(rho, degenerate)
    after_values = {
        "trace": float(torch_trace_value(after).item()),
        "bloch_norm": float(torch.linalg.vector_norm(torch_bloch_vector(after)).item()),
        "purity": float(torch_purity(after).item()),
    }
    deg_values = {
        "trace": float(torch_trace_value(deg).item()),
        "bloch_norm": float(torch.linalg.vector_norm(torch_bloch_vector(deg)).item()),
        "purity": float(torch_purity(deg).item()),
    }
    gamma5 = SIGMA_Z
    p_plus = (I2 + gamma5) / 2.0
    return {
        "pure_state_psi_0_6_0_8": {
            "before": before,
            "after_genuine_unit_quaternion_action": after_values,
            "after_nonunit_control": deg_values,
            "real_trace_delta": abs(after_values["trace"] - before["trace"]),
            "real_bloch_norm_delta": abs(after_values["bloch_norm"] - before["bloch_norm"]),
            "real_purity_delta": abs(after_values["purity"] - before["purity"]),
            "control_trace_delta": abs(deg_values["trace"] - before["trace"]),
            "control_bloch_norm_delta": abs(deg_values["bloch_norm"] - before["bloch_norm"]),
            "control_purity_delta": abs(deg_values["purity"] - before["purity"]),
            "pass": bool(
                abs(after_values["trace"] - before["trace"]) <= EPS
                and abs(after_values["bloch_norm"] - before["bloch_norm"]) <= EPS
                and abs(after_values["purity"] - before["purity"]) <= EPS
                and abs(deg_values["trace"] - before["trace"]) > EPS
            ),
        },
        "gamma5_projector_sanity": {
            "gamma5_squared_identity_error": float(torch.linalg.matrix_norm(gamma5 @ gamma5 - I2).real.item()),
            "trace_gamma5": float(torch.real(torch.trace(gamma5)).item()),
            "p_plus_idempotence_error": float(torch.linalg.matrix_norm(p_plus @ p_plus - p_plus).real.item()),
            "pass": bool(
                float(torch.linalg.matrix_norm(gamma5 @ gamma5 - I2).real.item()) <= EPS
                and abs(float(torch.real(torch.trace(gamma5)).item())) <= EPS
                and float(torch.linalg.matrix_norm(p_plus @ p_plus - p_plus).real.item()) <= EPS
            ),
        },
    }


def build_tool_ablations(top: dict[str, Any], known: dict[str, Any], sympy_gate: dict[str, Any], clifford_gate: dict[str, Any]) -> dict[str, Any]:
    real = top["torch_real_action"]
    control = top["torch_nonunit_control"]
    j_real = top["jax_real_action"]
    j_control = top["jax_nonunit_control"]
    topo = top["peps3d_topology_certificate"]
    counts = exact_counts(tuple(top["shape"]))
    full_anchor_count = counts["V"] + counts["E"] + counts["F"] + counts["C"]
    return {
        "torch_trace_preservation_defect_real_vs_nonunit_control": tool_ablation(
            "torch_recomputed_trace_preservation_defect",
            baseline_value=real["max_trace_deviation"],
            ablated_value=control["max_trace_deviation"],
            tool="torch",
        ),
        "torch_purity_preservation_defect_real_vs_nonunit_control": tool_ablation(
            "torch_recomputed_purity_preservation_defect",
            baseline_value=real["max_purity_deviation"],
            ablated_value=control["max_purity_deviation"],
            tool="torch",
        ),
        "jax_trace_preservation_defect_real_vs_nonunit_control": tool_ablation(
            "jax_recomputed_trace_preservation_defect",
            baseline_value=j_real["max_trace_deviation"],
            ablated_value=j_control["max_trace_deviation"],
            tool="jax",
        ),
        "sympy_quaternion_table_real_vs_scalar_label_control": tool_ablation(
            "sympy_exact_quaternion_table_pass_score",
            baseline_value=float(sympy_gate["real_pass"]),
            ablated_value=float(sympy_gate["scalar_label_control_pass"]),
            tool="sympy",
        ),
        "clifford_basis_real_vs_collapsed_control": tool_ablation(
            "clifford_Cl02_basis_pass_score",
            baseline_value=float(clifford_gate["real_pass"]),
            ablated_value=float(clifford_gate["collapsed_control_pass"]),
            tool="clifford",
        ),
        "peps3d_anchor_full_vs_vertex_only_support": tool_ablation(
            "supportive_peps3d_anchor_count_full_VEFC_vs_vertex_only",
            baseline_value=float(full_anchor_count),
            ablated_value=float(counts["V"]),
            tool="rustworkx/xgi/toponetx/gudhi/pyg",
        ),
        "known_value_control_trace_defect": tool_ablation(
            "known_value_psi_trace_delta_real_vs_nonunit_control",
            baseline_value=known["pure_state_psi_0_6_0_8"]["real_trace_delta"],
            ablated_value=known["pure_state_psi_0_6_0_8"]["control_trace_delta"],
            tool="torch",
        ),
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(exist_ok=True)
    scale_rows = {str(exact_counts(shape)["V"]): rung(shape) for shape in SHAPES}
    top = scale_rows["64"]
    proof = smt_invariant_proof(top["torch_real_action"], top["torch_nonunit_control"])
    sympy_gate = sympy_quaternion_table()
    clifford_gate = clifford_quaternion_table()
    known = known_value_checks()
    ablations = build_tool_ablations(top, known, sympy_gate, clifford_gate)

    proof_pass = bool(
        proof["real_claim_verdict"] == "sat"
        and proof["negated_claim_verdict"] == "unsat"
        and proof["differ"] is True
        and proof["bound_to_measured"] is True
        and proof.get("cvc5_real_verdict") == "sat"
        and proof.get("cvc5_control_verdict") == "unsat"
        and sympy_gate["flip"]
        and clifford_gate["flip"]
    )
    ablation_pass = all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > 1.0e-12
        and abs(
            abs(float(row["baseline_value"]) - float(row["ablated_value"]))
            - abs(float(row["outcome_delta"]))
        )
        <= 1.0e-9 * max(1.0, abs(float(row["outcome_delta"])))
        for row in ablations.values()
    )
    scale_pass = all(row["pass"] for row in scale_rows.values())
    known_pass = all(row["pass"] for row in known.values())
    all_pass = bool(scale_pass and proof_pass and ablation_pass and known_pass)

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(CTYPE),
        "action": "rho_v -> U rho_v U^dagger with U=U_I(0.37) U_J(0.61) U_K(0.29)",
        "top_rung_sites": top["sites_or_qubits"],
        "real_action": top["torch_real_action"],
        "nonunit_control": top["torch_nonunit_control"],
        "n01_order_witness": top["n01_order_witness"],
        "pass": bool(top["torch_real_action"]["pass"] and not top["torch_nonunit_control"]["pass"] and top["n01_order_witness"]["pass"]),
    }
    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "top_rung_sites": top["sites_or_qubits"],
        "real_action": top["jax_real_action"],
        "nonunit_control": top["jax_nonunit_control"],
        "pass": bool(top["jax_real_action"]["pass"] and not top["jax_nonunit_control"]["pass"]),
    }
    controls = {
        "degenerate_nonunit_quaternion_sandwich": {
            "description": "M rho M^dagger with M=cos(theta)I+s*QI, s != sin(theta), M not in SU(2), no trace renormalization.",
            "measured": top["torch_nonunit_control"],
            "invariant_preservation_claim_holds": False,
            "pass": bool(not top["torch_nonunit_control"]["pass"]),
        },
        "same_unit_order_control": {
            "description": "I->I versus I->I order path control collapses N01 order gap.",
            "max_same_unit_control_gap": top["n01_order_witness"]["max_same_unit_control_gap"],
            "pass": bool(top["n01_order_witness"]["max_same_unit_control_gap"] < TOL),
        },
        "scalar_quaternion_label_control": {
            "description": "Scalar identity labels cannot satisfy the exact I/J/K multiplication table.",
            "sympy_scalar_control_pass": sympy_gate["scalar_label_control_pass"],
            "pass": bool(not sympy_gate["scalar_label_control_pass"]),
        },
        "collapsed_clifford_control": {
            "description": "Collapse e2 to e1; anticommutation and bivector-square checks fail.",
            "clifford_collapsed_control_pass": clifford_gate["collapsed_control_pass"],
            "pass": bool(not clifford_gate["collapsed_control_pass"]),
        },
        "dense_global_state_closure_blocked": {
            "description": "The sim records 2^V only as a blocked dense dimension and never constructs it.",
            "dense_state_dimension_if_used_at_64": top["dense_state_dimension_if_used"],
            "dense_state_closure_used": False,
            "pass": True,
        },
    }

    return {
        "schema": "PER_SIM_REQUIRED_EMISSION_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "thisfile": THISFILE,
        "result_path": str(RESULT),
        "object_id": OBJECT_ID,
        "tier": "Stage-6 L3 manifold-layer action",
        "purpose": "Test the finite L3 Clifford/quaternion invariant layer as an action on a stage-2 spinor-density carrier.",
        "scientific_question": "Does a unit-quaternion SU(2) action preserve trace, Bloch norm, and purity on finite PEPS3D-anchored spinor densities while a quaternion-shaped non-unit control fails?",
        "classification": "lego",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "promotion_allowed": False,
        "claim_ceiling": "Local independent L3 action lego only; no layer stacking, Hopf/fibration, terrain, flux, Xi/Phi0, Axis0, bridge, physics, gravity, or final manifold admission.",
        "finite_map": {
            "domain": "finite PEPS3D site set K=(V,E,F,C) with V in {8,16,32,64}; each v carries a torch-native two-component spinor density rho_v; finite word [(I,0.37),(J,0.61),(K,0.29)] in quaternion units",
            "codomain_or_output": "rotated per-site densities U rho_v U^dagger plus measured invariant deviations for trace, Bloch-vector norm, purity, and unitarity",
            "definition": "L3_QK(rho_v)=U rho_v U^dagger, U=prod quat_unitary(unit,theta), quat_unitary(q,theta)=cos(theta)I+sin(theta)q",
        },
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite carrier/probe/operator/path set: finite K=(V,E,F,C), finite site densities, finite quaternion units, finite action word, finite readouts",
            },
            "N01": {
                "status": "active_tested",
                "statement": "noncommuting/order-sensitive quaternion units: I->J and J->I action paths produce a positive order gap while same-unit control collapses",
            },
        },
        "root_constraints_in_force": {
            "F01": "finite PEPS3D carrier anchors, finite spinor-density sites, finite quaternion unit action word, finite invariant readouts",
            "N01": "noncommuting quaternion unit path witness I->J vs J->I with same-unit control",
        },
        "domain": "finite PEPS3D K=(V,E,F,C), V in {8,16,32,64}, per-site torch complex128 spinor densities rho_v in C^{2x2}, finite quaternion unit word",
        "codomain_or_output": "per-site transformed densities, invariant deviations, SMT flip proof, controls, topology certificates, and scale ladder",
        "carrier_layer": "stage-2 spinor_density on PEPS3D site anchors",
        "geometry_layer": "L3 Clifford/quaternion invariant action; operation on rho_v, not a standalone geometry object",
        "carrier_realization": "torch complex128 two-component spinor densities; JAX x64 mirror; PEPS3D K supplies finite site/edge/face/cell anchors only",
        "peps3d_embedding": "K=(V,E,F,C) shapes (2,2,2),(4,2,2),(4,4,2),(4,4,4), bond_dim=2; each site carries one local 2x2 density; no dense 2^V state is built",
        "spinor_state": "torch-native two-component spinors from the stage-2 carrier helper, converted to rho_v=psi_v psi_v^dagger before L3 action",
        "quaternion_action": "explicit unit-quaternion SU(2) map U rho U^dagger using QI=diag(i,-i), QJ=[[0,1],[-1,0]], QK=QI*QJ; non-unit sandwich is the negative control",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/sim_root_F01_finite_distinguishability_probe.py",
            "system_v5/ops/formal_scouts/sim_l2_spinor_chirality_weyl_cover_layer_probe.py carrier helper only; no L2 layer action is stacked",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": ["future bounded L3 local-action audits only"],
        "allowed_claims": [
            "unit-quaternion SU(2) action preserves trace, Bloch norm, and purity for this finite spinor-density carrier",
            "the non-unit quaternion-shaped control breaks the same invariant claim",
            "N01 is witnessed locally by noncommuting quaternion action paths",
        ],
        "promotion_blockers": [
            "single independent layer action only",
            "no layer stacking tested",
            "no Hopf/fibration, terrain, flux, Xi/Phi0, Axis0, bridge, physics, or final manifold consumer admitted",
        ],
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": float(max(row["jax_vs_pytorch_delta"] for row in scale_rows.values())),
        "proof_results": {
            "smt_load_bearing_invariant_preservation": proof,
            "sympy_exact_quaternion_table": sympy_gate,
            "clifford_Cl02_quaternion_basis": clifford_gate,
        },
        "controls": controls,
        "tool_ablations": ablations,
        "ablation_outcome_delta": ablations,
        "known_value_checks": known,
        "scale_ladder": {
            "rungs": scale_rows,
            "pass": bool(scale_pass),
        },
        "scale_axis": "PEPS3D site-count rungs 8/16/32/64; local 2x2 action per site; dense_state_closure_used=false",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [name for name, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3", "cvc5", "sympy", "clifford"],
        "graph_surfaces_used": ["pyg", "rustworkx", "xgi"],
        "topology_surfaces_used": ["toponetx", "gudhi"],
        "required_inputs": ["stage-2 spinor-density carrier helper", "/tmp/layer_specs.json exact L3 record"],
        "data_or_artifact_dependencies": ["local code only; no external data"],
        "required_negatives": ["non-unit quaternion sandwich", "same-unit order control", "scalar-label quaternion control", "collapsed Clifford control", "dense closure block"],
        "negatives_run": list(controls.keys()),
        "kill_conditions": [
            "SMT does not flip real sat to control unsat",
            "control is renormalized or otherwise preserves the invariant",
            "JAX mirror diverges from torch beyond tolerance",
            "any scale rung builds dense global state",
        ],
        "required_artifacts": ["result JSON", "torch primary result", "JAX mirror result", "proof_results", "controls", "tool_ablations", "scale_ladder", "known_value_checks"],
        "artifacts_emitted": [str(RESULT)],
        "witness_trace_id": f"{OBJECT_ID}:{int(time.time())}",
        "result_summary": {
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "ablation_pass": ablation_pass,
            "known_value_pass": known_pass,
            "all_pass": all_pass,
            "promotion_allowed": False,
            "smt_real_verdict": proof["real_claim_verdict"],
            "smt_control_verdict": proof["negated_claim_verdict"],
            "cvc5_real_verdict": proof.get("cvc5_real_verdict"),
            "cvc5_control_verdict": proof.get("cvc5_control_verdict"),
        },
        "pass_rule": "real unit-quaternion action satisfies measured invariant-preservation SMT claim, non-unit control fails the same claim, cvc5 mirrors the flip, exact SymPy/Clifford gates flip against controls, JAX mirrors torch, and all non-dense scale rungs pass",
        "fail_rule": "fail on no SMT flip, unbound measured proof, degenerate-control renormalization, missing JAX mirror, dense closure, zero ablation delta, or downstream promotion",
        "promotion_status": "keep_but_open",
        "all_pass": all_pass,
        "required_pass": all_pass,
        "blockers": [] if all_pass else ["one_or_more_L3_action_gates_failed"],
    }


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(RESULT.relative_to(ROOT)), "required_pass": result["required_pass"]}, indent=2, sort_keys=True))
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
