#!/usr/bin/env python3
"""Bottom-up JAX audit for nested Hopf-torus placement dynamics.

JAX lane only. Julia files are reference doctrine for the finite object; this
script does not run Julia and does not import PyTorch.

Object under audit:

    16 placements = {L,R} x {fiber,base} x {Se,Ne,Ni,Si}
    nested leaves = finite Clifford-torus latitudes theta_k in (0, pi/2)

The script builds the object bottom-up:

1. Local 16 Lindblad density-matrix ODEs solved in one batched diffrax solve.
2. A finite nested-leaf branch/hop ensemble driven by the leaf-area ratchet
   A(theta)=2*pi^2*sin(2*theta).
3. Survivor basin readouts under F01 finitude and N01 noncommutation controls.

This is a diagnostic cross-audit receipt, not a Julia-native Grassmann proof,
not an official G-structure selection, and not manifold admission.
"""

from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import diffrax
import jax
from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp

try:
    from jaxga.jaxga import reduce_bases
    from jaxga.signatures import positive_signature

    JAXGA_AVAILABLE = True
except Exception:  # pragma: no cover - recorded in the receipt.
    reduce_bases = None
    positive_signature = None
    JAXGA_AVAILABLE = False


OUT = Path("jax_nested_hopf_bottom_up_branch_prune_audit_results.json")
N_BRANCH = 4096
N_LEAVES = 9
NEST_STEPS = 700
DT_NEST = 0.01
F01_TOL = 1.0e-3
EPS = 0.2
GAM = 1.0

TOPOLOGIES = ("Se", "Ne", "Ni", "Si")
LEFT_TERRAINS = {"Se": "Funnel", "Ne": "Vortex", "Ni": "Pit", "Si": "Hill"}
RIGHT_TERRAINS = {"Se": "Cannon", "Ne": "Spiral", "Ni": "Source", "Si": "Citadel"}

PAULI_X = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
PAULI_Y = jnp.asarray([[0, -1j], [1j, 0]], dtype=jnp.complex128)
PAULI_Z = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
ID2 = jnp.eye(2, dtype=jnp.complex128)
SM = jnp.asarray([[0, 0], [1, 0]], dtype=jnp.complex128)
SP = jnp.asarray([[0, 1], [0, 0]], dtype=jnp.complex128)
PXP = 0.5 * (ID2 + PAULI_X)
PXM = 0.5 * (ID2 - PAULI_X)

THETAS = jnp.linspace(jnp.pi / (2.0 * (N_LEAVES + 1)), jnp.pi / 2.0 - jnp.pi / (2.0 * (N_LEAVES + 1)), N_LEAVES)
AREAS = 2.0 * jnp.pi**2 * jnp.sin(2.0 * THETAS)
MAX_LEAF = int(N_LEAVES // 2)


@dataclass(frozen=True)
class Placement:
    label: int
    sheet: str
    path: str
    topology: str
    terrain: str
    target: tuple[float, float, float, float]


def _f(x: Any) -> float:
    return float(jax.device_get(x))


def _i(x: Any) -> int:
    return int(jax.device_get(x))


def _b(x: Any) -> bool:
    return bool(jax.device_get(x))


def unit(x: jax.Array) -> jax.Array:
    return x / jnp.linalg.norm(x, axis=-1, keepdims=True)


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


def qrot(q: jax.Array) -> jax.Array:
    q = q / jnp.linalg.norm(q)
    w, x, y, z = q
    return jnp.asarray(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=jnp.float64,
    )


def placements() -> list[Placement]:
    rows: list[Placement] = []
    label = 1
    for sheet, terrains in (("L", LEFT_TERRAINS), ("R", RIGHT_TERRAINS)):
        q0 = 0.5 if sheet == "L" else -0.5
        for path_bit, path in enumerate(("fiber", "base")):
            for topo_i, topology in enumerate(TOPOLOGIES):
                s1 = 0.5 if path_bit == 0 else -0.5
                s2 = 0.5 if (topo_i & 1) == 0 else -0.5
                s3 = 0.5 if (topo_i & 2) == 0 else -0.5
                rows.append(Placement(label, sheet, path, topology, terrains[topology], (q0, s1, s2, s3)))
                label += 1
    return rows


PLACEMENTS = placements()
TARGETS = jnp.asarray([p.target for p in PLACEMENTS], dtype=jnp.float64)
SHEET_SIGN = jnp.asarray([1.0 if p.sheet == "L" else -1.0 for p in PLACEMENTS], dtype=jnp.float64)
TOPO_IDX = jnp.asarray([TOPOLOGIES.index(p.topology) for p in PLACEMENTS], dtype=jnp.int32)
PATH_IDX = jnp.asarray([0 if p.path == "fiber" else 1 for p in PLACEMENTS], dtype=jnp.int32)


def rho_of_r(r: jax.Array) -> jax.Array:
    return 0.5 * (ID2 + r[0] * PAULI_X + r[1] * PAULI_Y + r[2] * PAULI_Z)


def bloch(rho: jax.Array) -> jax.Array:
    return jnp.real(jnp.asarray([jnp.trace(rho @ PAULI_X), jnp.trace(rho @ PAULI_Y), jnp.trace(rho @ PAULI_Z)]))


def dissipator(jump: jax.Array, rho: jax.Array) -> jax.Array:
    jj = jump.conj().T @ jump
    return jump @ rho @ jump.conj().T - 0.5 * (jj @ rho + rho @ jj)


def build_local_generators() -> tuple[jax.Array, jax.Array]:
    hs = []
    jumps = []
    zero = jnp.zeros((2, 2), dtype=jnp.complex128)
    for p in PLACEMENTS:
        sign = 1.0 if p.sheet == "L" else -1.0
        if p.topology == "Se":
            hs.append(EPS * sign * PAULI_Z)
            jumps.append(jnp.stack([SM, jnp.sqrt(0.3) * SP], axis=0))
        elif p.topology == "Ne":
            hs.append(sign * PAULI_Z)
            jumps.append(jnp.stack([jnp.sqrt(EPS) * PAULI_Z, zero], axis=0))
        elif p.topology == "Ni":
            hs.append(EPS * sign * PAULI_Z)
            jump = SM if p.sheet == "L" else SP
            jumps.append(jnp.stack([jnp.sqrt(GAM) * jump, zero], axis=0))
        elif p.topology == "Si":
            hs.append(PAULI_X)
            jumps.append(jnp.stack([PXP, PXM], axis=0))
        else:
            raise AssertionError(p)
    return jnp.stack(hs, axis=0), jnp.stack(jumps, axis=0)


H_ROWS, J_ROWS = build_local_generators()


def one_lindblad_rhs(rho: jax.Array, h: jax.Array, jumps: jax.Array) -> jax.Array:
    drho = -1j * (h @ rho - rho @ h)
    drho = drho + dissipator(jumps[0], rho) + dissipator(jumps[1], rho)
    return drho


def batched_lindblad_rhs(_t: jax.Array, y: jax.Array, args: tuple[jax.Array, jax.Array]) -> jax.Array:
    hs, jumps = args
    return jax.vmap(one_lindblad_rhs)(y, hs, jumps)


def pack_mat(mat: jax.Array) -> jax.Array:
    flat = mat.reshape(mat.shape[:-2] + (4,))
    return jnp.concatenate([jnp.real(flat), jnp.imag(flat)], axis=-1)


def unpack_mat(y: jax.Array) -> jax.Array:
    flat = y[..., :4] + 1j * y[..., 4:]
    return flat.reshape(y.shape[:-1] + (2, 2))


def batched_lindblad_rhs_real(t: jax.Array, y: jax.Array, args: tuple[jax.Array, jax.Array]) -> jax.Array:
    hs_real, jumps_real = args
    return pack_mat(batched_lindblad_rhs(t, unpack_mat(y), (unpack_mat(hs_real), unpack_mat(jumps_real))))


def solve_local_16() -> dict[str, Any]:
    r0 = jnp.asarray([0.42, -0.31, 0.17], dtype=jnp.float64)
    rho0 = jnp.stack([rho_of_r(r0) for _ in PLACEMENTS], axis=0)
    y0 = pack_mat(rho0)
    term = diffrax.ODETerm(batched_lindblad_rhs_real)
    sol = diffrax.diffeqsolve(
        term,
        diffrax.Dopri5(),
        t0=0.0,
        t1=12.0,
        dt0=0.02,
        y0=y0,
        args=(pack_mat(H_ROWS), pack_mat(J_ROWS)),
        saveat=diffrax.SaveAt(t1=True),
        stepsize_controller=diffrax.PIDController(rtol=1.0e-7, atol=1.0e-9),
        max_steps=4096,
    )
    rho = unpack_mat(sol.ys[0])
    tr = jnp.trace(rho, axis1=1, axis2=2)
    herm = jnp.linalg.norm(rho - jnp.swapaxes(rho.conj(), 1, 2), axis=(1, 2))
    ev = jnp.linalg.eigvalsh(0.5 * (rho + jnp.swapaxes(rho.conj(), 1, 2)))
    rs = jax.vmap(bloch)(rho)
    norms = jnp.linalg.norm(rs, axis=1)

    pit_l = rs[2]       # label 3: L fiber Ni/Pit
    source_r = rs[10]   # label 11: R fiber Ni/Source
    hill_l = rs[3]      # label 4: L fiber Si/Hill
    vortex_l = local_angular_velocity(1.0, jnp.asarray([0.4, 0.2, 0.1], dtype=jnp.float64), 1)
    spiral_r = local_angular_velocity(-1.0, jnp.asarray([0.4, 0.2, 0.1], dtype=jnp.float64), 1)
    terrain_readout_idx = jnp.asarray([0, 1, 2, 3, 8, 9, 10, 11], dtype=jnp.int32)
    rounded = jnp.round(rs[terrain_readout_idx] * 10.0) / 10.0
    unique_terrain_readouts = jnp.unique(rounded, axis=0, size=8, fill_value=jnp.nan)
    unique_count = jnp.sum(~jnp.isnan(unique_terrain_readouts[:, 0]))

    checks = {
        "sixteen_density_rows": rho.shape[0] == 16,
        "trace_preserved": _f(jnp.max(jnp.abs(tr - 1.0))) < 1.0e-6,
        "hermitian": _f(jnp.max(herm)) < 1.0e-6,
        "positive_semidefinite": _f(jnp.min(ev)) > -1.0e-7,
        "bloch_ball_finite": _f(jnp.max(norms)) <= 1.0 + 1.0e-6,
        "pit_sink_south": _f(pit_l[2]) < -0.95,
        "source_sink_north": _f(source_r[2]) > 0.95,
        "si_dephases_yz": _f(jnp.linalg.norm(hill_l[1:])) < 5.0e-3,
        "ne_lr_opposite_chirality": _f(vortex_l * spiral_r) < 0.0,
        "terrain_readouts_not_collapsed": _i(unique_count) >= 4,
    }
    return {
        "solver": "diffrax.Dopri5 + PIDController over 16 batched density matrices",
        "checks": checks,
        "pass": all(checks.values()),
        "metrics": {
            "max_trace_error": _f(jnp.max(jnp.abs(tr - 1.0))),
            "max_hermiticity_error": _f(jnp.max(herm)),
            "min_eigenvalue": _f(jnp.min(ev)),
            "max_bloch_norm": _f(jnp.max(norms)),
            "pit_final_bloch": [float(x) for x in jax.device_get(pit_l)],
            "source_final_bloch": [float(x) for x in jax.device_get(source_r)],
            "unique_terrain_readout_count": _i(unique_count),
        },
    }


def local_angular_velocity(sheet_sign: float, r: jax.Array, topo_idx: int) -> jax.Array:
    del topo_idx
    # d angle at r in the xy plane under +/- sigma_z Hamiltonian.
    drx = -2.0 * sheet_sign * r[1] - 2.0 * EPS * r[0]
    dry = 2.0 * sheet_sign * r[0] - 2.0 * EPS * r[1]
    return r[0] * dry - r[1] * drx


def spinor_raw(phi: jax.Array, chi: jax.Array, eta: jax.Array) -> jax.Array:
    return jnp.asarray(
        [jnp.exp(1j * (phi + chi)) * jnp.cos(eta), jnp.exp(1j * (phi - chi)) * jnp.sin(eta)],
        dtype=jnp.complex128,
    )


def spinor_to_q(psi: jax.Array) -> jax.Array:
    return unit(jnp.asarray([jnp.real(psi[0]), jnp.imag(psi[0]), jnp.real(psi[1]), jnp.imag(psi[1])], dtype=jnp.float64))


def density_from_q(q: jax.Array) -> jax.Array:
    q = unit(q)
    psi = jnp.asarray([q[0] + 1j * q[1], q[2] + 1j * q[3]], dtype=jnp.complex128)
    return jnp.outer(psi, psi.conj())


def path_q(sheet: str, path: str, u: jax.Array, eta: jax.Array) -> jax.Array:
    phi0 = 0.23 if sheet == "L" else -0.19
    chi0 = -0.41 if sheet == "L" else 0.62
    if path == "fiber":
        phi = phi0 + u
        chi = chi0
    else:
        phi = phi0 - jnp.cos(2.0 * eta) * u
        chi = chi0 + u
    return spinor_to_q(spinor_raw(phi, chi, eta))


def path_phase_coords(sheet: str, path: str, u: jax.Array, eta: jax.Array) -> tuple[jax.Array, jax.Array]:
    phi0 = 0.23 if sheet == "L" else -0.19
    chi0 = -0.41 if sheet == "L" else 0.62
    if path == "fiber":
        return phi0 + u, jnp.asarray(chi0)
    if path == "base":
        return phi0 - jnp.cos(2.0 * eta) * u, chi0 + u
    raise ValueError(path)


def path_geometry_checks() -> dict[str, Any]:
    eta = jnp.pi / 5.0
    rows = {}
    checks = []
    for sheet in ("L", "R"):
        qf0 = path_q(sheet, "fiber", 0.0, eta)
        qf1 = path_q(sheet, "fiber", 1.0, eta)
        qb0 = path_q(sheet, "base", 0.0, eta)
        qb1 = path_q(sheet, "base", 1.0, eta)
        fiber_density_delta = jnp.linalg.norm(density_from_q(qf1) - density_from_q(qf0))
        base_density_delta = jnp.linalg.norm(density_from_q(qb1) - density_from_q(qb0))
        f_phi0, f_chi0 = path_phase_coords(sheet, "fiber", 0.0, eta)
        f_phi1, f_chi1 = path_phase_coords(sheet, "fiber", 1.0, eta)
        b_phi0, b_chi0 = path_phase_coords(sheet, "base", 0.0, eta)
        b_phi1, b_chi1 = path_phase_coords(sheet, "base", 1.0, eta)
        fiber_connection = jnp.abs((f_phi1 - f_phi0) + jnp.cos(2.0 * eta) * (f_chi1 - f_chi0))
        base_connection = jnp.abs((b_phi1 - b_phi0) + jnp.cos(2.0 * eta) * (b_chi1 - b_chi0))
        row = {
            "fiber_density_delta": _f(fiber_density_delta),
            "base_density_delta": _f(base_density_delta),
            "fiber_vertical_connection_abs": _f(fiber_connection),
            "base_horizontal_residual": _f(base_connection),
        }
        rows[sheet] = row
        checks.append(row["fiber_density_delta"] < 1.0e-10)
        checks.append(row["fiber_vertical_connection_abs"] > 0.9)
        checks.append(row["base_density_delta"] > 1.0e-2)
        checks.append(row["base_horizontal_residual"] < 1.0e-12)
    return {"pass": all(checks), "rows": rows}


def project_bloch_ball(r: jax.Array) -> jax.Array:
    n = jnp.linalg.norm(r, axis=-1, keepdims=True)
    return jnp.where(n > 1.0, r / n, r)


def bloch_field(r: jax.Array, placement: jax.Array, mode_code: jax.Array) -> jax.Array:
    rx, ry, rz = r[:, 0], r[:, 1], r[:, 2]
    sign = SHEET_SIGN[placement]
    topo = TOPO_IDX[placement]

    se = jnp.stack([-0.55 * rx - 0.35 * sign * ry, 0.35 * sign * rx - 0.55 * ry, -0.8 * (rz + 0.538)], axis=1)
    ne = jnp.stack([-2.0 * sign * ry - 2.0 * EPS * rx, 2.0 * sign * rx - 2.0 * EPS * ry, -0.08 * rz], axis=1)
    pit_or_source_target = jnp.where(sign > 0.0, -1.0, 1.0)
    ni = jnp.stack([-0.5 * rx, -0.5 * ry, -1.0 * (rz - pit_or_source_target)], axis=1)
    si = jnp.stack([jnp.zeros_like(rx), -1.0 * ry, -1.0 * rz], axis=1)

    field = jnp.where((topo == 0)[:, None], se, jnp.where((topo == 1)[:, None], ne, jnp.where((topo == 2)[:, None], ni, si)))

    commuting = jnp.stack([-0.5 * rx, -0.5 * ry, -(rz + 1.0)], axis=1)
    expansive = jnp.stack([rx, ry, rz], axis=1)
    field = jnp.where(mode_code == 1, commuting, field)
    field = jnp.where(mode_code == 3, expansive, field)
    return field


def initial_nested_state() -> tuple[jax.Array, jax.Array, jax.Array, jax.Array, jax.Array]:
    key = jax.random.PRNGKey(20260603)
    q = unit(jax.random.normal(key, (N_BRANCH, 4), dtype=jnp.float64))
    placement = jnp.arange(N_BRANCH, dtype=jnp.int32) % 16
    leaf = (jnp.arange(N_BRANCH, dtype=jnp.int32) * 5 + placement) % N_LEAVES
    angles = 2.0 * jnp.pi * (jnp.arange(N_BRANCH, dtype=jnp.float64) / N_BRANCH)
    rad = 0.48 + 0.08 * (placement.astype(jnp.float64) % 3.0)
    r = jnp.stack([rad * jnp.cos(angles), rad * jnp.sin(angles), 0.22 * jnp.sin(2.0 * angles)], axis=1)
    alive = jnp.ones((N_BRANCH,), dtype=bool)
    return q, r, leaf, placement, alive


@jax.jit
def run_nested(mode_code: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array, jax.Array, jax.Array, jax.Array]:
    q0, r0, leaf0, placement0, alive0 = initial_nested_state()
    key0 = jax.random.PRNGKey(9001)

    def step(carry: tuple[jax.Array, jax.Array, jax.Array, jax.Array, jax.Array, jax.Array], _: Any):
        q, r, leaf, placement, alive, key = carry
        key, sub = jax.random.split(key)
        u = jax.random.uniform(sub, (N_BRANCH,), dtype=jnp.float64)

        target_idx = jnp.where(mode_code == 1, jnp.zeros_like(placement), placement)
        target = TARGETS[target_idx]
        tangent = target - jnp.sum(target * q, axis=1, keepdims=True) * q
        rotor_axis = jnp.stack([jnp.zeros(N_BRANCH), 0.05 * SHEET_SIGN[placement], 0.03 * (TOPO_IDX[placement] - 1.5), 0.02 * (PATH_IDX[placement] * 2 - 1)], axis=1)
        rotor_term = jax.vmap(qmul)(rotor_axis, q)
        q_raw = q + DT_NEST * (1.8 * tangent + rotor_term)
        q_next = unit(q_raw)

        dr = bloch_field(r, placement, mode_code)
        r_raw = r + DT_NEST * dr
        killed = jnp.linalg.norm(r_raw, axis=1) > (1.0 + F01_TOL)
        r_next = project_bloch_ball(r_raw)

        left = jnp.maximum(leaf - 1, 0)
        right = jnp.minimum(leaf + 1, N_LEAVES - 1)
        areas = jnp.where(mode_code == 4, jnp.ones_like(AREAS), AREAS)
        prefer_right = areas[right] > areas[left]
        step_dir = jnp.where(prefer_right, 1, -1)
        candidate = jnp.clip(leaf + step_dir, 0, N_LEAVES - 1)
        area_gain = jnp.maximum(areas[candidate] - areas[leaf], 0.0)
        hop_p = jnp.where((mode_code == 2) | (area_gain <= 0.0), 0.0, 0.06 + 0.30 * area_gain / jnp.max(areas))
        leaf_next = jnp.where(u < hop_p, candidate, leaf)

        alive_next = alive & ~killed
        max_q_drift = jnp.max(jnp.abs(jnp.linalg.norm(q_next, axis=1) - 1.0))
        max_r_norm = jnp.max(jnp.linalg.norm(r_next, axis=1))
        return (q_next, r_next, leaf_next, placement, alive_next, key), jnp.asarray([max_q_drift, max_r_norm], dtype=jnp.float64)

    (qf, rf, leaff, placement, alive, _key), metrics = jax.lax.scan(step, (q0, r0, leaf0, placement0, alive0, key0), None, length=NEST_STEPS)
    del placement
    return qf, rf, leaff, alive, jnp.max(metrics[:, 0]), jnp.max(metrics[:, 1])


def populated(values: jax.Array, alive: jax.Array, size: int) -> list[int]:
    uniq = jnp.unique(values[alive], size=size, fill_value=-1)
    return [int(x) for x in jax.device_get(uniq) if int(x) >= 0]


def run_nested_summary(name: str, mode: int) -> dict[str, Any]:
    qf, rf, leaff, alive, max_q_drift, max_r_norm = run_nested(jnp.asarray(mode, dtype=jnp.int32))
    labels0 = jnp.argmax(qf @ TARGETS.T, axis=1)
    labels = labels0 + 1
    alive_count = _i(jnp.sum(alive))
    central_alive = _i(jnp.sum(alive & (leaff == MAX_LEAF)))
    leaf_hist = jnp.bincount(jnp.where(alive, leaff, 0), length=N_LEAVES)
    # Remove dead rows accidentally counted in bin 0.
    leaf_hist = leaf_hist.at[0].add(-_i(jnp.sum(~alive)))
    if alive_count:
        q_alive = qf[alive]
        double_cover = jax.vmap(lambda q: jnp.linalg.norm(qrot(q) - qrot(-q)))(q_alive)
        max_double_cover_gap = _f(jnp.max(double_cover))
    else:
        max_double_cover_gap = None
    return {
        "name": name,
        "populated_placements": populated(labels, alive, 16),
        "populated_leaves_zero_based": populated(leaff, alive, N_LEAVES),
        "survivors": alive_count,
        "pruned": int(N_BRANCH - alive_count),
        "central_leaf_fraction": float(central_alive / max(alive_count, 1)),
        "leaf_histogram": [int(x) for x in jax.device_get(leaf_hist)],
        "max_q_norm_drift": _f(max_q_drift),
        "max_bloch_norm_after_projection": _f(max_r_norm),
        "max_double_cover_gap": max_double_cover_gap,
        "mean_final_bloch_norm": _f(jnp.mean(jnp.linalg.norm(rf[alive], axis=1))) if alive_count else None,
    }


def order_sensitivity() -> dict[str, Any]:
    rho0 = rho_of_r(jnp.asarray([0.37, -0.29, 0.11], dtype=jnp.float64))
    pit_h = H_ROWS[2]
    pit_j = J_ROWS[2]
    hill_h = H_ROWS[3]
    hill_j = J_ROWS[3]
    dt = 0.05

    def euler(rho, h, jumps):
        return rho + dt * one_lindblad_rhs(rho, h, jumps)

    ab = euler(euler(rho0, pit_h, pit_j), hill_h, hill_j)
    ba = euler(euler(rho0, hill_h, hill_j), pit_h, pit_j)
    gap = jnp.linalg.norm(ab - ba)

    def euler_dt(rho, h, jumps, local_dt):
        return rho + local_dt * one_lindblad_rhs(rho, h, jumps)

    ca = euler_dt(euler_dt(rho0, pit_h, pit_j, 0.03), pit_h, pit_j, 0.07)
    cb = euler_dt(euler_dt(rho0, pit_h, pit_j, 0.07), pit_h, pit_j, 0.03)
    control_gap = jnp.linalg.norm(ca - cb)
    return {
        "pass": _f(gap) > 1.0e-4 and _f(control_gap) < 1.0e-12,
        "metrics": {
            "pit_then_hill_vs_hill_then_pit_gap": _f(gap),
            "same_generator_order_control_gap": _f(control_gap),
        },
    }


def leaf_area_checks() -> dict[str, Any]:
    measured = AREAS
    analytic = 2.0 * jnp.pi**2 * jnp.sin(2.0 * THETAS)
    descending = measured[MAX_LEAF::-1]
    monotone_to_pole = jnp.all(descending[:-1] > descending[1:])
    flat = jnp.ones_like(measured) * measured[MAX_LEAF]
    checks = {
        "finite_leaf_count": N_LEAVES == 9,
        "area_matches_formula": _f(jnp.max(jnp.abs(measured - analytic))) < 1.0e-10,
        "clifford_leaf_maximum": int(jnp.argmax(measured)) == MAX_LEAF,
        "area_decreases_from_clifford_to_pole": _b(monotone_to_pole),
        "flat_control_has_no_ratchet_gradient": _f(jnp.max(jnp.abs(flat - flat[0]))) < 1.0e-12,
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "theta_grid": [float(x) for x in jax.device_get(THETAS)],
        "areas": [float(x) for x in jax.device_get(AREAS)],
        "max_leaf_zero_based": MAX_LEAF,
    }


def cl3_jaxga_check() -> dict[str, Any]:
    if not JAXGA_AVAILABLE:
        return {"pass": False, "status": "blocked_missing_package", "metrics": {}}
    squares = [float(reduce_bases((i,), (i,), positive_signature)[0]) for i in range(3)]
    anticommute = []
    for i in range(3):
        for j in range(i + 1, 3):
            sij, bij = reduce_bases((i,), (j,), positive_signature)
            sji, bji = reduce_bases((j,), (i,), positive_signature)
            anticommute.append(bij == bji and float(sij + sji) == 0.0)
    ok = all(abs(x - 1.0) < 1.0e-12 for x in squares) and all(anticommute)
    return {"pass": ok, "status": "ok", "metrics": {"basis_squares": squares, "anticommutators_zero": anticommute}}


def dlpack_snapshot_check() -> dict[str, Any]:
    if hasattr(jax.dlpack, "to_dlpack"):
        capsule = jax.dlpack.to_dlpack(AREAS)
        restored = jax.dlpack.from_dlpack(capsule)
        api = "jax.dlpack.to_dlpack"
    elif hasattr(AREAS, "__dlpack__"):
        restored = jax.dlpack.from_dlpack(AREAS)
        api = "array.__dlpack__"
    else:
        return {"pass": False, "status": "blocked_missing_dlpack_export", "metrics": {}}
    gap = jnp.max(jnp.abs(restored - AREAS))
    return {"pass": _f(gap) == 0.0, "status": "ok", "api": api, "metrics": {"max_roundtrip_gap": _f(gap)}}


def riemannax_status() -> dict[str, Any]:
    available = importlib.util.find_spec("riemannax") is not None
    return {"pass": bool(available), "status": "available" if available else "blocked_missing_package"}


def main() -> int:
    local = solve_local_16()
    path_geometry = path_geometry_checks()
    area = leaf_area_checks()
    order = order_sensitivity()
    cl3 = cl3_jaxga_check()
    dlpack = dlpack_snapshot_check()
    riem = riemannax_status()

    genuine = run_nested_summary("genuine_ratchet_noncommuting", 0)
    commuting = run_nested_summary("n01_off_single_commuting_sink", 1)
    no_ratchet = run_nested_summary("ratchet_off_theta_frozen", 2)
    expansive = run_nested_summary("f01_expansive_prune_control", 3)
    flat_area = run_nested_summary("flat_area_no_ratchet_control", 4)

    genuine_set = set(genuine["populated_placements"])
    no_ratchet_hist_differs = no_ratchet["leaf_histogram"] != genuine["leaf_histogram"]
    flat_hist_differs = flat_area["leaf_histogram"] != genuine["leaf_histogram"]
    nested_checks = {
        "genuine_populates_all_16_placement_basins": genuine_set == set(range(1, 17)),
        "genuine_survivors_not_pruned": genuine["pruned"] == 0,
        "genuine_ratchet_concentrates_clifford_leaf": genuine["central_leaf_fraction"] > 0.70,
        "n01_off_collapses_to_one_placement_basin": commuting["populated_placements"] == [1],
        "ratchet_off_leaf_histogram_differs": no_ratchet_hist_differs and no_ratchet["central_leaf_fraction"] < genuine["central_leaf_fraction"] - 0.20,
        "flat_area_control_leaf_histogram_differs": flat_hist_differs and flat_area["central_leaf_fraction"] < genuine["central_leaf_fraction"] - 0.20,
        "f01_expansive_prune_fires": expansive["pruned"] > 0,
        "bookkeeping_consistent": all(row["survivors"] == N_BRANCH - row["pruned"] for row in (genuine, commuting, no_ratchet, expansive, flat_area)),
        "s3_retraction_works": max(row["max_q_norm_drift"] for row in (genuine, commuting, no_ratchet, expansive, flat_area)) < 1.0e-12,
        "double_cover_preserved": max(row["max_double_cover_gap"] or 0.0 for row in (genuine, commuting, no_ratchet, flat_area)) < 1.0e-12,
    }

    checks = {
        "local_16_lindblad": local["pass"],
        "path_geometry": path_geometry["pass"],
        "leaf_area_ratchet": area["pass"],
        "noncommuting_order_sensitivity": order["pass"],
        "nested_branch_prune": all(nested_checks.values()),
        "cl3_jaxga": cl3["pass"],
        "dlpack_snapshot": dlpack["pass"],
        "riemannax_status_recorded": riem["status"] in {"available", "blocked_missing_package"},
    }
    audit_pass = all(checks.values())

    receipt = {
        "sim_id": "jax_nested_hopf_bottom_up_branch_prune_audit",
        "name": "JAX bottom-up nested Hopf-tori branch/prune audit",
        "version": "1.0",
        "classification": "tool_lego_fit_probe",
        "sim_execution_kind": "nonclassical_diagnostic_jax_audit",
        "promotion_allowed": False,
        "promotion_status": "blocked_diagnostic_only",
        "claim_ceiling": (
            "JAX diagnostic cross-audit of the finite bottom-up object only: 16 Lindblad placements, "
            "finite nested Hopf-torus leaves, leaf-area ratchet/hop ensemble, and F01/N01 controls. "
            "Not Julia-native Grassmann/QuantumOptics evidence, not official G-structure selection, "
            "not layer completion, not Axis0/FEP/flux/physics admission."
        ),
        "ran_julia": False,
        "ran_pytorch": False,
        "root_constraints_in_force": {
            "F01": "finite placement set, finite leaf grid, finite branch ensemble, S3 retraction, Bloch-ball prune",
            "N01": "noncommuting/order-sensitive Lindblad generator control; N01-off single commuting sink collapses basin labels",
        },
        "finite_map": "{16 placement rows} x {9 theta leaves} x {4096 branch states} -> survivor placement/leaf basins plus control readouts",
        "domain": {
            "placements": "{L,R} x {fiber,base} x {Se,Ne,Ni,Si}",
            "leaves": "theta_k in (0,pi/2), k=0..8",
            "state": "unit quaternion q in S3 plus spinor-derived density rho and Bloch vector r",
        },
        "codomain_or_output": "JSON receipt with local Lindblad readouts, nested survivor basins, F01/N01 controls, and blocked downstream consumers",
        "carrier_layer": "S3 unit-quaternion spinor carrier with finite nested Hopf-torus leaf grid",
        "geometry_layer": "nested Hopf tori T^2_theta with leaf-area ratchet A(theta)=2*pi^2*sin(2theta)",
        "carrier_realization": "jax arrays: q in R^4 normalized to S3, rho in D(C^2), r in Bloch ball",
        "spinor_state": "q=(Re z1, Im z1, Re z2, Im z2), ||q||=1; rho=|psi><psi| for path geometry and density native ODEs",
        "quaternion_action": "Spin(3)/SU(2) q target flow plus q/-q SO(3) double-cover invariant",
        "peps3d_embedding": "diagnostic finite cell anchor only: placement x leaf x branch index; not admitted PEPS3D evidence",
        "dependency_receipts": [
            "jax_gstructure_16_placement_spin3_audit_results.json",
            "jax_gstructure_16_branch_prune_selector_audit_results.json",
            "system_v5/julia_carrier/layers/sixteen_terrain_placement_lattice_results.json (read-only reference)",
            "system_v5/julia_carrier/layers/nested_leaf_area_ratchet_results.json (read-only reference)",
            "system_v5/julia_carrier/layers/emergent_basin_nested_terrains_results.json (read-only reference)",
        ],
        "blocked_consumers": ["official_g_structure_selection", "layer_stacking_readiness", "Axis0", "FEP", "flux", "Xi", "Phi0", "physics/gravity", "final_manifold_admission"],
        "tool_manifest": {
            "jax": "load-bearing batched S3 branch/prune and density readout computation",
            "diffrax": "load-bearing local 16 Lindblad density-matrix ODE solve",
            "jaxga": "load-bearing Cl(3,0) basis square/anticommutator check when available",
            "DLPack": "supportive snapshot interchange check only",
            "riemannax": "recorded as available or blocked; not faked if missing",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "diffrax": "load_bearing",
            "jaxga": "load_bearing" if JAXGA_AVAILABLE else "None",
            "DLPack": "supportive",
            "riemannax": "None" if riem["status"] == "blocked_missing_package" else "supportive",
        },
        "local_16_lindblad": local,
        "path_geometry": path_geometry,
        "leaf_area_ratchet": area,
        "order_sensitivity": order,
        "nested_runs": {
            "genuine": genuine,
            "commuting_control": commuting,
            "ratchet_off_control": no_ratchet,
            "expansive_prune_control": expansive,
            "flat_area_control": flat_area,
        },
        "nested_checks": nested_checks,
        "cl3_jaxga": cl3,
        "dlpack_snapshot": dlpack,
        "riemannax": riem,
        "checks": checks,
        "AUDIT_PASS": audit_pass,
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        "jax_nested_hopf_bottom_up "
        f"local16={local['pass']} nested={checks['nested_branch_prune']} "
        f"genuine={genuine['populated_placements']} commuting={commuting['populated_placements']} "
        f"exp_pruned={expansive['pruned']} AUDIT_PASS={audit_pass}"
    )
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
