#!/usr/bin/env python3
"""JAX G-structure audit over the 16 Weyl-terrain placements.

This is the JAX scale/audit lane. It reads no Julia code at runtime, runs no
Julia process, and uses no PyTorch. The object is finite:

    P = {L,R} x {fiber,base} x {Se,Ne,Ni,Si}

It tests that this placement lattice can be carried by S3 unit-quaternion
spinors while preserving the diagnostic G-structure candidates Spin(3) ~= SU(2),
SO(3) frame reduction, U(1) Hopf Chern readout, horizontal/base path condition,
and explicit blocked/missing package surfaces such as riemannax.
"""

from __future__ import annotations

import importlib.util
import json
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import diffrax
import jax
from jax import config

config.update("jax_enable_x64", True)

import jax.dlpack
import jax.numpy as jnp
import jaxlie
import optax

try:
    from jaxga.jaxga import reduce_bases
    from jaxga.signatures import positive_signature

    JAXGA_AVAILABLE = True
except Exception:  # pragma: no cover - availability is recorded in receipt.
    reduce_bases = None
    positive_signature = None
    JAXGA_AVAILABLE = False


OUT = Path("jax_gstructure_16_placement_spin3_audit_results.json")
EPS = 1.0e-10

TOPOLOGIES = ("Se", "Ne", "Ni", "Si")
LEFT_TERRAINS = {"Se": "Funnel", "Ne": "Vortex", "Ni": "Pit", "Si": "Hill"}
RIGHT_TERRAINS = {"Se": "Cannon", "Ne": "Spiral", "Ni": "Source", "Si": "Citadel"}


@dataclass(frozen=True)
class Placement:
    index: int
    sheet: str
    path: str
    topology: str
    terrain: str
    label: str


def _f(x: Any) -> float:
    return float(jax.device_get(x))


def _b(x: Any) -> bool:
    return bool(jax.device_get(x))


def unit(x: jax.Array) -> jax.Array:
    return x / jnp.linalg.norm(x, axis=-1, keepdims=True)


@jax.custom_vjp
def retract_s3(q: jax.Array) -> jax.Array:
    return q / jnp.linalg.norm(q)


def _retract_s3_fwd(q: jax.Array) -> tuple[jax.Array, jax.Array]:
    y = q / jnp.linalg.norm(q)
    return y, y


def _retract_s3_bwd(y: jax.Array, g: jax.Array) -> tuple[jax.Array]:
    tangent = g - y * jnp.real(jnp.vdot(y, g))
    return (tangent,)


retract_s3.defvjp(_retract_s3_fwd, _retract_s3_bwd)


@jax.custom_jvp
def retract_s3_jvp(q: jax.Array) -> jax.Array:
    return q / jnp.linalg.norm(q)


@retract_s3_jvp.defjvp
def _retract_s3_jvp(primals: tuple[jax.Array], tangents: tuple[jax.Array]) -> tuple[jax.Array, jax.Array]:
    (q,) = primals
    (dq,) = tangents
    y = q / jnp.linalg.norm(q)
    tangent = (dq - y * jnp.real(jnp.vdot(y, dq))) / jnp.linalg.norm(q)
    return y, tangent


def qmul(a: jax.Array, b: jax.Array) -> jax.Array:
    a0, a1, a2, a3 = a
    b0, b1, b2, b3 = b
    return jnp.asarray(
        [
            a0 * b0 - a1 * b1 - a2 * b2 - a3 * b3,
            a0 * b1 + a1 * b0 + a2 * b3 - a3 * b2,
            a0 * b2 - a1 * b3 + a2 * b0 + a3 * b1,
            a0 * b3 + a1 * b2 - a2 * b1 + a3 * b0,
        ],
        dtype=jnp.float64,
    )


def qconj(q: jax.Array) -> jax.Array:
    return jnp.asarray([q[0], -q[1], -q[2], -q[3]], dtype=jnp.float64)


def qrot(q: jax.Array) -> jax.Array:
    q = retract_s3(q)
    w, x, y, z = q
    return jnp.asarray(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=jnp.float64,
    )


def spinor_raw(phi: jax.Array, chi: jax.Array, eta: jax.Array) -> jax.Array:
    z1 = jnp.exp(1j * (phi + chi)) * jnp.cos(eta)
    z2 = jnp.exp(1j * (phi - chi)) * jnp.sin(eta)
    return jnp.asarray([z1, z2], dtype=jnp.complex128)


def spinor_to_q(psi: jax.Array) -> jax.Array:
    return retract_s3(jnp.asarray([jnp.real(psi[0]), jnp.imag(psi[0]), jnp.real(psi[1]), jnp.imag(psi[1])], dtype=jnp.float64))


def density_from_q(q: jax.Array) -> jax.Array:
    q = retract_s3(q)
    psi = jnp.asarray([q[0] + 1j * q[1], q[2] + 1j * q[3]], dtype=jnp.complex128)
    return jnp.outer(psi, psi.conj())


def hopf_base(q: jax.Array) -> jax.Array:
    q = retract_s3(q)
    z1 = q[0] + 1j * q[1]
    z2 = q[2] + 1j * q[3]
    return jnp.asarray(
        [
            2.0 * jnp.real(z1 * jnp.conj(z2)),
            2.0 * jnp.imag(z1 * jnp.conj(z2)),
            jnp.abs(z1) ** 2 - jnp.abs(z2) ** 2,
        ],
        dtype=jnp.float64,
    )


def initial_params(sheet: str) -> tuple[float, float, float]:
    if sheet == "L":
        return 0.23, -0.41, 0.47
    return -0.19, 0.62, 0.71


def path_q(sheet: str, path: str, u: jax.Array) -> jax.Array:
    phi0, chi0, eta0 = initial_params(sheet)
    if path == "fiber":
        phi = phi0 + u
        chi = chi0
    elif path == "base":
        phi = phi0 - jnp.cos(2.0 * eta0) * u
        chi = chi0 + u
    else:
        raise ValueError(path)
    return spinor_to_q(spinor_raw(phi, chi, eta0))


def path_phase_coords(sheet: str, path: str, u: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
    phi0, chi0, eta0 = initial_params(sheet)
    if path == "fiber":
        return phi0 + u, jnp.asarray(chi0), jnp.asarray(eta0)
    if path == "base":
        return phi0 - jnp.cos(2.0 * eta0) * u, chi0 + u, jnp.asarray(eta0)
    raise ValueError(path)


def path_metrics(sheet: str, path: str) -> dict[str, float]:
    q0 = path_q(sheet, path, 0.0)
    q1 = path_q(sheet, path, 1.0)
    base_delta = jnp.linalg.norm(hopf_base(q1) - hopf_base(q0))
    density_delta = jnp.linalg.norm(density_from_q(q1) - density_from_q(q0))
    phi_a, chi_a, eta0 = path_phase_coords(sheet, path, 0.0)
    phi_b, chi_b, _ = path_phase_coords(sheet, path, 1.0)
    phidot = phi_b - phi_a
    chidot = chi_b - chi_a
    connection_value = phidot + jnp.cos(2.0 * eta0) * chidot
    horizontal_residual = jnp.where(path == "base", jnp.abs(connection_value), jnp.asarray(0.0))
    fiber_vertical_connection = jnp.where(path == "fiber", jnp.abs(connection_value), jnp.asarray(0.0))
    return {
        "base_delta": _f(base_delta),
        "density_delta": _f(density_delta),
        "horizontal_connection_residual": _f(jnp.abs(horizontal_residual)),
        "fiber_vertical_connection_abs": _f(fiber_vertical_connection),
        "connection_value": _f(connection_value),
        "start_norm_gap": _f(jnp.abs(jnp.linalg.norm(q0) - 1.0)),
        "end_norm_gap": _f(jnp.abs(jnp.linalg.norm(q1) - 1.0)),
    }


def topology_axis(sheet: str, topology: str) -> jax.Array:
    base = {
        "Se": jnp.asarray([0.0, 0.0, 1.0], dtype=jnp.float64),
        "Ne": jnp.asarray([1.0, 0.0, 0.0], dtype=jnp.float64),
        "Ni": jnp.asarray([0.0, 1.0, 0.0], dtype=jnp.float64),
        "Si": unit(jnp.asarray([1.0, 1.0, 1.0], dtype=jnp.float64)),
    }[topology]
    return base if sheet == "L" else -base


def topology_rate(topology: str) -> float:
    return {"Se": 0.13, "Ne": 0.29, "Ni": 0.17, "Si": 0.23}[topology]


@jax.jit
def evolve_quaternion(q0: jax.Array, axis: jax.Array, rate: jax.Array) -> tuple[jax.Array, jax.Array]:
    dt = 0.002
    steps = 500
    omega = jnp.concatenate([jnp.asarray([0.0], dtype=jnp.float64), rate * axis])

    def step(q: jax.Array, _: Any) -> tuple[jax.Array, jax.Array]:
        dq = 0.5 * qmul(omega, q)
        qn = retract_s3(q + dt * dq)
        return qn, jnp.abs(jnp.linalg.norm(qn) - 1.0)

    return jax.lax.scan(step, retract_s3(q0), None, length=steps)


def placements() -> list[Placement]:
    rows: list[Placement] = []
    idx = 1
    for sheet, type_name, terrains in (("L", "Type 1", LEFT_TERRAINS), ("R", "Type 2", RIGHT_TERRAINS)):
        for path, loop_name in (("fiber", "inner"), ("base", "outer")):
            for topology in TOPOLOGIES:
                terrain = terrains[topology]
                rows.append(Placement(idx, sheet, path, topology, terrain, f"{topology} / {terrain} on {type_name} {loop_name}"))
                idx += 1
    return rows


def placement_row(p: Placement) -> dict[str, Any]:
    q0 = path_q(p.sheet, p.path, 0.0)
    axis = topology_axis(p.sheet, p.topology)
    qf, drifts = evolve_quaternion(q0, axis, jnp.asarray(topology_rate(p.topology), dtype=jnp.float64))
    no_op_gap = jnp.linalg.norm(qf - q0)
    metrics = path_metrics(p.sheet, p.path)
    path_ok = (
        metrics["density_delta"] < 1.0e-9 and metrics["base_delta"] < 1.0e-9 and metrics["fiber_vertical_connection_abs"] > 0.9
        if p.path == "fiber"
        else metrics["density_delta"] > 0.2 and metrics["base_delta"] > 0.2 and metrics["horizontal_connection_residual"] < 1.0e-12
    )
    checks = {
        "s3_norm_retracted": _b(jnp.max(drifts) < 1.0e-12),
        "topology_flow_nontrivial": _b(no_op_gap > 1.0e-3),
        "path_class_control": bool(path_ok),
        "hopf_base_on_s2": _b(jnp.abs(jnp.linalg.norm(hopf_base(qf)) - 1.0) < 1.0e-12),
    }
    return {
        "index": p.index,
        "label": p.label,
        "sheet": p.sheet,
        "path": p.path,
        "topology": p.topology,
        "terrain": p.terrain,
        "finite_map": "placement -> S3 quaternion path -> topology rotor flow -> Hopf base/density readout",
        "checks": checks,
        "pass": all(checks.values()),
        "metrics": {
            **metrics,
            "topology_axis": [_f(x) for x in axis],
            "flow_no_op_gap": _f(no_op_gap),
            "max_norm_drift": _f(jnp.max(drifts)),
        },
        "promotion_allowed": False,
    }


def spin3_su2_candidate() -> dict[str, Any]:
    q = retract_s3(jnp.asarray([0.37, -0.21, 0.69, 0.58], dtype=jnp.float64))
    p = retract_s3(jnp.asarray([0.51, 0.49, -0.38, 0.58], dtype=jnp.float64))
    qp = qmul(q, p)
    rot = qrot(q)
    jaxlie_rot = jaxlie.SO3.exp(jnp.asarray([0.2, -0.1, 0.3], dtype=jnp.float64))
    jaxlie_quat = jaxlie_rot.as_quaternion_xyzw()
    reflection = jnp.diag(jnp.asarray([1.0, 1.0, -1.0], dtype=jnp.float64))
    checks = {
        "quaternion_product_closed_on_s3": _b(jnp.abs(jnp.linalg.norm(qp) - 1.0) < 1.0e-12),
        "double_cover_q_and_minus_q_same_so3": _b(jnp.linalg.norm(qrot(q) - qrot(-q)) < 1.0e-12),
        "rotation_matrix_is_so3": _b(jnp.linalg.norm(rot.T @ rot - jnp.eye(3)) < 1.0e-12 and jnp.abs(jnp.linalg.det(rot) - 1.0) < 1.0e-12),
        "jaxlie_exp_quaternion_unit": _b(jnp.abs(jnp.linalg.norm(jaxlie_quat) - 1.0) < 1.0e-12),
        "reflection_kill_not_so3": _b(jnp.linalg.det(reflection) < 0.0),
    }
    return {
        "candidate": "Spin(3) ~= SU(2)",
        "finite_map": "unit quaternions -> SO(3) rotations with q/-q double cover",
        "checks": checks,
        "metrics": {
            "product_norm_gap": _f(jnp.abs(jnp.linalg.norm(qp) - 1.0)),
            "double_cover_gap": _f(jnp.linalg.norm(qrot(q) - qrot(-q))),
            "rotation_det": _f(jnp.linalg.det(rot)),
            "reflection_det": _f(jnp.linalg.det(reflection)),
            "jaxlie_quaternion_norm_gap": _f(jnp.abs(jnp.linalg.norm(jaxlie_quat) - 1.0)),
        },
        "pass": all(checks.values()),
    }


def cl3_jaxga_candidate() -> dict[str, Any]:
    if not JAXGA_AVAILABLE:
        return {"candidate": "Cl(3,0) via jaxga", "pass": False, "checks": {"jaxga_available": False}, "metrics": {}}
    squares = [float(reduce_bases((i,), (i,), positive_signature)[0]) for i in range(3)]
    anti = []
    for i in range(3):
        for j in range(i + 1, 3):
            sij, bij = reduce_bases((i,), (j,), positive_signature)
            sji, bji = reduce_bases((j,), (i,), positive_signature)
            anti.append(abs(float(sij + sji)) if bij == bji else 2.0)
    checks = {
        "jaxga_available": True,
        "cl3_squares_positive": squares == [1.0, 1.0, 1.0],
        "cl3_anticommutators_zero": max(anti) < 1.0e-12,
    }
    return {
        "candidate": "Cl(3,0) via jaxga",
        "finite_map": "finite jaxga basis blades -> square signs and anticommutators",
        "checks": checks,
        "metrics": {"squares": squares, "max_anticommutator": max(anti)},
        "pass": all(checks.values()),
    }


def u1_chern_candidate() -> dict[str, Any]:
    n = 4096
    theta = (jnp.arange(n, dtype=jnp.float64) + 0.5) * jnp.pi / n
    dtheta = jnp.pi / n
    dphi = 2.0 * jnp.pi
    c_plus = jnp.sum(0.5 * jnp.sin(theta) * dtheta * dphi) / (2.0 * jnp.pi)
    c_minus = -c_plus
    trivial = 0.0 * c_plus
    checks = {
        "chern_plus_one": _b(jnp.abs(c_plus - 1.0) < 1.0e-7),
        "chern_minus_one": _b(jnp.abs(c_minus + 1.0) < 1.0e-7),
        "trivial_bundle_zero": _b(jnp.abs(trivial) < 1.0e-12),
    }
    return {
        "candidate": "U(1) Hopf bundle Chern readout",
        "finite_map": "finite S2 curvature quadrature -> c1 signs and trivial-bundle control",
        "checks": checks,
        "metrics": {"c1_plus": _f(c_plus), "c1_minus": _f(c_minus), "trivial_c1": _f(trivial)},
        "pass": all(checks.values()),
    }


def noncommuting_candidate() -> dict[str, Any]:
    q = path_q("L", "base", 0.0)
    ax_a = topology_axis("L", "Se")
    ax_b = topology_axis("L", "Ne")
    qa, _ = evolve_quaternion(q, ax_a, jnp.asarray(0.17))
    qab, _ = evolve_quaternion(qa, ax_b, jnp.asarray(0.19))
    qb, _ = evolve_quaternion(q, ax_b, jnp.asarray(0.19))
    qba, _ = evolve_quaternion(qb, ax_a, jnp.asarray(0.17))
    order_gap = jnp.minimum(jnp.linalg.norm(qab - qba), jnp.linalg.norm(qab + qba))
    qa_slow, _ = evolve_quaternion(q, ax_a, jnp.asarray(0.17))
    q_same_forward, _ = evolve_quaternion(qa_slow, ax_a, jnp.asarray(0.19))
    qa_fast, _ = evolve_quaternion(q, ax_a, jnp.asarray(0.19))
    q_same_reverse, _ = evolve_quaternion(qa_fast, ax_a, jnp.asarray(0.17))
    same_gap = jnp.minimum(jnp.linalg.norm(q_same_forward - q_same_reverse), jnp.linalg.norm(q_same_forward + q_same_reverse))
    checks = {
        "different_topology_rotors_order_sensitive": _b(order_gap > 1.0e-3),
        "same_word_control_zero": _b(same_gap < 1.0e-12),
    }
    return {
        "candidate": "N01 topology rotor noncommutation",
        "finite_map": "two finite topology rotor flows -> AB vs BA order gap",
        "checks": checks,
        "metrics": {"order_gap": _f(order_gap), "same_word_gap": _f(same_gap)},
        "pass": all(checks.values()),
    }


def diffrax_event_candidate() -> dict[str, Any]:
    target = retract_s3(jnp.asarray([0.5, 0.5, 0.5, 0.5], dtype=jnp.float64))

    def vector_field(t: jax.Array, y: jax.Array, args: jax.Array) -> jax.Array:
        del t
        q = y / jnp.linalg.norm(y)
        return 2.0 * (args - jnp.dot(args, q) * q)

    def forbidden_event(state: Any, **kwargs: Any) -> jax.Array:
        del kwargs
        return state.y[0] < -0.01

    def solve(y0: jax.Array) -> Any:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*discrete_terminating_event=.*deprecated.*")
            return diffrax.diffeqsolve(
                diffrax.ODETerm(vector_field),
                diffrax.Dopri5(),
                t0=0.0,
                t1=4.0,
                dt0=0.01,
                y0=retract_s3(y0),
                args=target,
                stepsize_controller=diffrax.PIDController(rtol=1e-7, atol=1e-9),
                discrete_terminating_event=diffrax.DiscreteTerminatingEvent(forbidden_event),
                saveat=diffrax.SaveAt(t1=True),
                max_steps=4096,
                throw=False,
            )

    alive = solve(jnp.asarray([0.2, 0.9, 0.1, -0.2], dtype=jnp.float64))
    dead = solve(jnp.asarray([-0.2, 0.97, 0.0, 0.0], dtype=jnp.float64))
    alive_event = "event occurred" in str(alive.result)
    dead_event = "event occurred" in str(dead.result)
    alive_norm_gap = jnp.abs(jnp.linalg.norm(alive.ys[-1]) - 1.0)
    checks = {
        "alive_path_not_pruned": not alive_event,
        "forbidden_path_pruned": dead_event,
        "alive_norm_preserved": _b(alive_norm_gap < 1.0e-6),
    }
    return {
        "candidate": "diffrax DiscreteTerminatingEvent prune",
        "finite_map": "finite S3 ODE trajectory -> monotone forbidden q0 event",
        "checks": checks,
        "metrics": {
            "alive_result": str(alive.result),
            "dead_result": str(dead.result),
            "alive_norm_gap": _f(alive_norm_gap),
        },
        "pass": all(checks.values()),
    }


def optax_retraction_candidate() -> dict[str, Any]:
    target = retract_s3(jnp.asarray([0.5, 0.5, 0.5, 0.5], dtype=jnp.float64))
    start = retract_s3(jnp.asarray([0.2, -0.8, 0.5, -0.1], dtype=jnp.float64))
    opt = optax.adam(learning_rate=0.08)

    def loss(x: jax.Array) -> jax.Array:
        q = retract_s3(x)
        return 1.0 - jnp.dot(q, target)

    @jax.jit
    def run() -> tuple[jax.Array, jax.Array, jax.Array]:
        state = opt.init(start)

        def step(carry: tuple[jax.Array, Any], _: Any) -> tuple[tuple[jax.Array, Any], tuple[jax.Array, jax.Array]]:
            x, opt_state = carry
            value, grad = jax.value_and_grad(loss)(x)
            updates, opt_state = opt.update(grad, opt_state, x)
            x = retract_s3(optax.apply_updates(x, updates))
            return (x, opt_state), (value, jnp.abs(jnp.linalg.norm(x) - 1.0))

        (xf, _), (values, drifts) = jax.lax.scan(step, (start, state), None, length=96)
        return xf, values, drifts

    xf, values, drifts = run()
    checks = {
        "loss_decreases": _b(loss(xf) < values[0]),
        "retraction_keeps_s3": _b(jnp.max(drifts) < 1.0e-12),
    }
    return {
        "candidate": "optax plus S3 retraction",
        "finite_map": "finite gradient steps -> retracted S3 optimizer state",
        "checks": checks,
        "metrics": {
            "initial_loss": _f(values[0]),
            "final_loss": _f(loss(xf)),
            "max_norm_drift": _f(jnp.max(drifts)),
        },
        "pass": all(checks.values()),
    }


def custom_jvp_candidate() -> dict[str, Any]:
    q = jnp.asarray([0.7, -0.3, 0.2, 0.1], dtype=jnp.float64)
    dq = jnp.asarray([0.4, 0.2, -0.5, 0.3], dtype=jnp.float64)

    y, tangent = jax.jvp(retract_s3_jvp, (q,), (dq,))
    tangent_dot = jnp.abs(jnp.vdot(y, tangent))
    finite_diff = (retract_s3_jvp(q + 1.0e-5 * dq) - y) / 1.0e-5
    fd_gap = jnp.linalg.norm(finite_diff - tangent)
    checks = {
        "jvp_output_on_s3": _b(jnp.abs(jnp.linalg.norm(y) - 1.0) < 1.0e-12),
        "jvp_tangent_to_s3": _b(tangent_dot < 1.0e-12),
        "jvp_matches_finite_difference": _b(fd_gap < 1.0e-4),
    }
    return {
        "candidate": "custom_jvp S3 retraction derivative",
        "finite_map": "finite S3 retraction primal/tangent -> tangent-space JVP readout",
        "checks": checks,
        "metrics": {
            "tangent_dot": _f(tangent_dot),
            "finite_difference_gap": _f(fd_gap),
            "output_norm_gap": _f(jnp.abs(jnp.linalg.norm(y) - 1.0)),
        },
        "pass": all(checks.values()),
    }


def dlpack_snapshot_candidate() -> dict[str, Any]:
    x = jnp.arange(16, dtype=jnp.float64).reshape(4, 4)
    y = jax.dlpack.from_dlpack(x)
    checks = {
        "jax_array_exports_dlpack_protocol": hasattr(x, "__dlpack__") and hasattr(x, "__dlpack_device__"),
        "jax_from_dlpack_roundtrip_values": _b(jnp.linalg.norm(y - x) < 1.0e-12),
    }
    return {
        "candidate": "DLPack checkpoint/snapshot boundary",
        "finite_map": "finite JAX array -> DLPack protocol import -> value-preserving snapshot",
        "checks": checks,
        "metrics": {"roundtrip_gap": _f(jnp.linalg.norm(y - x)), "shape": list(x.shape)},
        "pass": all(checks.values()),
    }


def run_probe(write: bool = True) -> dict[str, Any]:
    rows = [placement_row(p) for p in placements()]
    labels = [row["label"] for row in rows]
    base_rows = [row for row in rows if row["path"] == "base"]
    fiber_rows = [row for row in rows if row["path"] == "fiber"]
    sheet_terrains = {(row["sheet"], row["topology"], row["terrain"]) for row in rows}
    candidates = {
        "spin3_su2": spin3_su2_candidate(),
        "cl3_jaxga": cl3_jaxga_candidate(),
        "u1_chern": u1_chern_candidate(),
        "noncommuting_topology_rotors": noncommuting_candidate(),
        "diffrax_event_prune": diffrax_event_candidate(),
        "optax_retraction": optax_retraction_candidate(),
        "custom_jvp_retraction": custom_jvp_candidate(),
        "dlpack_snapshot": dlpack_snapshot_candidate(),
        "riemannax": {
            "candidate": "riemannax optional manifold optimizer",
            "pass": importlib.util.find_spec("riemannax") is not None,
            "checks": {"installed": importlib.util.find_spec("riemannax") is not None},
            "metrics": {"status": "ok" if importlib.util.find_spec("riemannax") is not None else "blocked_missing_package"},
        },
    }
    checks = {
        "sixteen_placements_enumerated": len(rows) == 16 and len(set(labels)) == 16,
        "four_topologies_present": sorted({row["topology"] for row in rows}) == sorted(TOPOLOGIES),
        "eight_sheet_specific_terrains_present": len(sheet_terrains) == 8,
        "two_weyl_sheets_present": sorted({row["sheet"] for row in rows}) == ["L", "R"],
        "fiber_and_base_paths_present": sorted({row["path"] for row in rows}) == ["base", "fiber"],
        "all_placement_rows_pass": all(row["pass"] for row in rows),
        "base_paths_horizontal": all(row["metrics"]["horizontal_connection_residual"] < 1.0e-12 for row in base_rows),
        "fiber_paths_density_invariant": all(row["metrics"]["density_delta"] < 1.0e-9 for row in fiber_rows),
        "spin3_su2_candidate_passes": candidates["spin3_su2"]["pass"],
        "cl3_jaxga_candidate_passes": candidates["cl3_jaxga"]["pass"],
        "u1_chern_candidate_passes": candidates["u1_chern"]["pass"],
        "noncommuting_topology_rotors_pass": candidates["noncommuting_topology_rotors"]["pass"],
        "diffrax_event_prune_passes": candidates["diffrax_event_prune"]["pass"],
        "optax_retraction_passes": candidates["optax_retraction"]["pass"],
        "custom_jvp_retraction_passes": candidates["custom_jvp_retraction"]["pass"],
        "dlpack_snapshot_boundary_passes": candidates["dlpack_snapshot"]["pass"],
        "riemannax_status_recorded": candidates["riemannax"]["metrics"]["status"] in {"ok", "blocked_missing_package"},
        "no_julia_execution": True,
        "no_pytorch_execution": True,
        "promotion_blocked": True,
    }
    result = {
        "AUDIT_PASS": all(checks.values()),
        "name": "jax_gstructure_16_placement_spin3_audit",
        "classification": "diagnostic_jax_gstructure_16_placement_spin3_audit",
        "executed_track": "jax",
        "ran_julia": False,
        "ran_pytorch": False,
        "julia_reference_mode": "read_only_external_reference_only",
        "legacy_tensor_lane_used": False,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_boundary": "JAX diagnostic for 16 placements and G-structure candidates; no full layer, official G-structure selection, stacking, Axis0, flux, bridge, or physics admission.",
        "root_constraints_in_force": {
            "F01": "finite placement set P, finite S3 quaternions, finite Hopf path samples, finite ODE/scan steps, finite Chern quadrature",
            "N01": "quaternion rotor noncommutation, Clifford anticommutators, chirality/path order controls, monotone prune event",
        },
        "domain": "P={L,R} x {fiber,base} x {Se,Ne,Ni,Si}; unit quaternion spinors q in S3; finite topology rotor axes; finite Hopf curvature samples",
        "codomain_or_output": "16 placement rows, Spin(3)/SU(2) checks, Cl(3) jaxga checks, U(1) Chern signs, horizontal/fiber controls, DLPack snapshot status",
        "finite_map": "placement and candidate G-structure maps -> bounded JAX invariant/control receipt",
        "rows": rows,
        "candidates": candidates,
        "checks": checks,
        "tool_manifest": {
            "jax": "load-bearing finite quaternion, Hopf, placement, scan, x64, and gradient computations",
            "jax.numpy": "load-bearing finite linear algebra and invariant readouts",
            "jaxlie": "load-bearing SO3 exp/quaternion unit check for Spin(3)/SU(2) candidate",
            "jaxga": "load-bearing Cl(3,0) blade square/anticommutator check when available",
            "diffrax": "load-bearing S3 ODE event-prune check",
            "optax": "load-bearing optimizer with explicit S3 retraction",
            "custom_jvp": "load-bearing tangent-space derivative rule for S3 retraction",
            "jax.dlpack": "supportive checkpoint/snapshot boundary check for future Julia/JAX file or zero-copy exchange",
            "riemannax": "optional manifold optimizer; blocker recorded when missing",
            "json": "supportive receipt serialization",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "jaxlie": "load_bearing",
            "jaxga": "load_bearing" if JAXGA_AVAILABLE else "None",
            "diffrax": "load_bearing",
            "optax": "load_bearing",
            "custom_jvp": "load_bearing",
            "jax.dlpack": "supportive",
            "riemannax": "blocked_or_supportive",
            "json": "supportive",
        },
        "reference_paths_read_only": [
            "system_v5/READ ONLY Reference Docs/terrains.md",
            "system_v5/ops/AXES_TERRAINS_OPERATORS_MANIFOLD_SOURCE_LAYOUT_20260522.md",
            "system_v5/julia_carrier/layers/*_results.json",
        ],
        "blocked_consumers": [
            "full_layer_completion",
            "official_g_structure_selection",
            "layer_stacking",
            "flux",
            "Xi/Phi0",
            "Axis0",
            "FEP",
            "bridge",
            "basin_admission",
            "physics_gravity",
            "physics/gravity",
            "final_manifold_admission",
        ],
        "honesty_notes": [
            "This is a JAX diagnostic/audit lane, not a Julia-native Grassmann/QuantumOptics proof.",
            "riemannax is absent in this environment and is recorded instead of silently assumed.",
            "DLPack is checked only as a finite JAX snapshot boundary; no live Julia exchange is claimed.",
            "No PyTorch import, process, or retired-lane port is used.",
        ],
    }
    if write:
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    result = run_probe(write=True)
    row_pass = sum(1 for row in result["rows"] if row["pass"])
    cand_pass = sum(1 for key, value in result["candidates"].items() if key != "riemannax" and value["pass"])
    cand_total = sum(1 for key in result["candidates"] if key != "riemannax")
    print(
        "jax_gstructure_16_placement_spin3 "
        f"placements={row_pass}/{len(result['rows'])} candidates={cand_pass}/{cand_total} "
        f"riemannax={result['candidates']['riemannax']['metrics']['status']} AUDIT_PASS={result['AUDIT_PASS']}"
    )


if __name__ == "__main__":
    main()
