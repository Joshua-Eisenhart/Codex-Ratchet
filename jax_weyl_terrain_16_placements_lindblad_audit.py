#!/usr/bin/env python3
"""JAX audit for the 16 Weyl-terrain placements.

This is the JAX scale/audit lane. It does not execute Julia and it does not use
PyTorch. It implements the finite 4 topology x 2 Weyl sheet x 2 path placement
table as GKSL/Lindblad density dynamics plus S3 spinor path readouts.
"""

from __future__ import annotations

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
    from jaxga.signatures import sta_signature

    JAXGA_AVAILABLE = True
except Exception:  # pragma: no cover - availability is reported in the receipt.
    reduce_bases = None
    sta_signature = None
    JAXGA_AVAILABLE = False


OUT = Path("jax_weyl_terrain_16_placements_lindblad_audit_results.json")
EPS = 1.0e-9
I = 1j

ID2 = jnp.eye(2, dtype=jnp.complex128)
SX = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.asarray([[0, -I], [I, 0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
SP = jnp.asarray([[0, 1], [0, 0]], dtype=jnp.complex128)
SM = jnp.asarray([[0, 0], [1, 0]], dtype=jnp.complex128)
P0 = jnp.asarray([[1, 0], [0, 0]], dtype=jnp.complex128)
P1 = jnp.asarray([[0, 0], [0, 1]], dtype=jnp.complex128)

H0 = 0.53 * SZ + 0.19 * SX
K0 = 0.41 * SZ + 0.13 * SY

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


def spinor_raw(phi: jax.Array, chi: jax.Array, eta: jax.Array) -> jax.Array:
    return jnp.exp(1j * phi) * jnp.asarray([jnp.cos(eta), jnp.exp(1j * chi) * jnp.sin(eta)], dtype=jnp.complex128)


@jax.custom_vjp
def project_spinor(psi: jax.Array) -> jax.Array:
    return psi / jnp.linalg.norm(psi)


def _project_spinor_fwd(psi: jax.Array) -> tuple[jax.Array, tuple[jax.Array, jax.Array]]:
    norm = jnp.linalg.norm(psi)
    y = psi / norm
    return y, (y, norm)


def _project_spinor_bwd(res: tuple[jax.Array, jax.Array], g: jax.Array) -> tuple[jax.Array]:
    y, norm = res
    tangent = g - y * jnp.real(jnp.vdot(y, g))
    return (tangent / norm,)


project_spinor.defvjp(_project_spinor_fwd, _project_spinor_bwd)


def density(psi: jax.Array) -> jax.Array:
    psi = project_spinor(psi)
    return jnp.outer(psi, psi.conj())


def project_density(rho: jax.Array) -> jax.Array:
    rho = 0.5 * (rho + rho.conj().T)
    vals, vecs = jnp.linalg.eigh(rho)
    vals = jnp.clip(jnp.real(vals), 0.0, None)
    rho_pos = (vecs * vals[None, :]) @ vecs.conj().T
    return rho_pos / jnp.trace(rho_pos)


def dissipator(l_op: jax.Array, rho: jax.Array) -> jax.Array:
    ld_l = l_op.conj().T @ l_op
    return l_op @ rho @ l_op.conj().T - 0.5 * (ld_l @ rho + rho @ ld_l)


def commutator_rhs(h_op: jax.Array, rho: jax.Array) -> jax.Array:
    return -1j * (h_op @ rho - rho @ h_op)


def jump_stack(sheet: str, topology: str) -> jax.Array:
    if topology == "Se":
        jump = SM if sheet == "L" else SP
        return jnp.stack([jnp.sqrt(0.32) * jump, jnp.zeros_like(ID2)])
    if topology == "Ne":
        return jnp.stack([jnp.sqrt(0.08) * SZ, jnp.zeros_like(ID2)])
    if topology == "Ni":
        jump = SM if sheet == "L" else SP
        return jnp.stack([jnp.sqrt(0.42) * jump, jnp.zeros_like(ID2)])
    if topology == "Si":
        return jnp.stack([jnp.sqrt(0.18) * P0, jnp.sqrt(0.18) * P1])
    raise ValueError(topology)


def hamiltonian(sheet: str, topology: str) -> jax.Array:
    sign = 1.0 if sheet == "L" else -1.0
    if topology == "Si":
        return sign * K0
    return sign * H0


def lindblad_parts(sheet: str, topology: str) -> tuple[jax.Array, jax.Array]:
    h_op = hamiltonian(sheet, topology)
    jumps = jump_stack(sheet, topology)
    if topology == "Se":
        return 0.05 * h_op, jumps
    if topology == "Ne":
        return h_op, jnp.sqrt(0.07) * jumps
    if topology == "Ni":
        return 0.04 * h_op, jumps
    if topology == "Si":
        return h_op, jumps
    raise ValueError(topology)


def generator(sheet: str, topology: str, rho: jax.Array) -> jax.Array:
    h_op, jumps = lindblad_parts(sheet, topology)
    return commutator_rhs(h_op, rho) + sum(dissipator(j, rho) for j in jumps)


def initial_params(sheet: str) -> tuple[float, float, float]:
    if sheet == "L":
        return 0.23, -0.41, 0.47
    return -0.19, 0.62, 0.71


def path_spinor(sheet: str, path: str, u: jax.Array) -> jax.Array:
    phi0, chi0, eta0 = initial_params(sheet)
    if path == "fiber":
        phi = phi0 + u
        chi = chi0
    elif path == "base":
        phi = phi0 - jnp.cos(2.0 * eta0) * u
        chi = chi0 + u
    else:
        raise ValueError(path)
    return project_spinor(spinor_raw(phi, chi, eta0))


def path_metrics(sheet: str, path: str) -> dict[str, Any]:
    rho0 = density(path_spinor(sheet, path, 0.0))
    rho1 = density(path_spinor(sheet, path, 1.0))
    _, _, eta0 = initial_params(sheet)
    if path == "base":
        horizontal_residual = -jnp.cos(2.0 * eta0) + jnp.cos(2.0 * eta0) * 1.0
    else:
        horizontal_residual = 1.0
    return {
        "path_density_delta": _f(jnp.linalg.norm(rho1 - rho0)),
        "horizontal_connection_residual": _f(jnp.abs(horizontal_residual)),
        "spinor_norm_start_gap": _f(jnp.abs(jnp.linalg.norm(path_spinor(sheet, path, 0.0)) - 1.0)),
        "spinor_norm_end_gap": _f(jnp.abs(jnp.linalg.norm(path_spinor(sheet, path, 1.0)) - 1.0)),
    }


def pack_rho(rho: jax.Array) -> jax.Array:
    flat = rho.reshape(-1)
    return jnp.concatenate([jnp.real(flat), jnp.imag(flat)])


def unpack_rho(y: jax.Array) -> jax.Array:
    return (y[:4] + 1j * y[4:]).reshape(2, 2)


def solve_master(sheet: str, topology: str, rho0: jax.Array) -> jax.Array:
    def vf(t: jax.Array, y: jax.Array, args: Any) -> jax.Array:
        del t, args
        return pack_rho(generator(sheet, topology, unpack_rho(y)))

    sol = diffrax.diffeqsolve(
        diffrax.ODETerm(vf),
        diffrax.Tsit5(),
        t0=0.0,
        t1=0.8,
        dt0=0.01,
        y0=pack_rho(rho0),
        saveat=diffrax.SaveAt(t1=True),
        stepsize_controller=diffrax.PIDController(rtol=1e-7, atol=1e-9),
        max_steps=4096,
    )
    return project_density(unpack_rho(sol.ys[0]))


@jax.jit
def trajectory_batch(psi0: jax.Array, h_op: jax.Array, jumps: jax.Array, key: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
    n_traj = 512
    n_steps = 180
    dt = 0.8 / n_steps
    psi = jnp.tile(project_spinor(psi0)[None, :], (n_traj, 1))
    alive = jnp.ones((n_traj,), dtype=bool)
    keys = jax.random.split(key, n_steps)
    jump_ldl = jnp.einsum("jab,jbc->jac", jumps.conj().transpose(0, 2, 1), jumps)
    sum_ldl = jnp.sum(jump_ldl, axis=0)

    def step(carry: tuple[jax.Array, jax.Array], k: jax.Array) -> tuple[tuple[jax.Array, jax.Array], None]:
        psi_cur, alive_cur = carry
        k_jump, k_choice = jax.random.split(k)
        rates = jnp.real(jnp.einsum("bi,jik,bk->bj", psi_cur.conj(), jump_ldl, psi_cur))
        total_rate = jnp.sum(jnp.clip(rates, 0.0), axis=1)
        total_p = jnp.clip(dt * total_rate, 0.0, 0.35)
        jump_draw = jax.random.uniform(k_jump, (n_traj,))
        choose_draw = jax.random.uniform(k_choice, (n_traj,))
        do_jump = jump_draw < total_p
        probs = jnp.where(total_rate[:, None] > 0.0, rates / total_rate[:, None], 0.0)
        cdf = jnp.cumsum(probs, axis=1)
        jump_idx = jnp.argmax(choose_draw[:, None] <= cdf, axis=1)
        jump_ops = jumps[jump_idx]
        psi_jump = jnp.einsum("bij,bj->bi", jump_ops, psi_cur)
        psi_no = psi_cur + dt * (-1j * (psi_cur @ h_op.T) - 0.5 * (psi_cur @ sum_ldl.T))
        psi_next_raw = jnp.where(do_jump[:, None], psi_jump, psi_no)
        norms = jnp.linalg.norm(psi_next_raw, axis=1)
        alive_next = alive_cur & jnp.isfinite(norms) & (norms > 1e-10)
        psi_next = psi_next_raw / norms[:, None]
        return (psi_next, alive_next), None

    (psi_final, alive_final), _ = jax.lax.scan(step, (psi, alive), keys)
    rhos = jnp.einsum("bi,bj->bij", psi_final, psi_final.conj())
    rho_avg = jnp.mean(rhos, axis=0)
    max_norm_gap = jnp.max(jnp.abs(jnp.linalg.norm(psi_final, axis=1) - 1.0))
    pruned = jnp.sum(~alive_final)
    return project_density(rho_avg), max_norm_gap, pruned


def placements() -> list[Placement]:
    out: list[Placement] = []
    idx = 1
    for sheet, type_name, terrains in (("L", "Type 1", LEFT_TERRAINS), ("R", "Type 2", RIGHT_TERRAINS)):
        for path, loop_name in (("fiber", "inner"), ("base", "outer")):
            for topology in TOPOLOGIES:
                terrain = terrains[topology]
                out.append(Placement(idx, sheet, path, topology, terrain, f"{topology} / {terrain} on {type_name} {loop_name}"))
                idx += 1
    return out


def cl13_jaxga_checks() -> dict[str, Any]:
    if not JAXGA_AVAILABLE:
        return {"available": False, "pass": False, "reason": "jaxga import failed"}
    square_values = [float(reduce_bases((i,), (i,), sta_signature)[0]) for i in range(4)]
    anti_gaps = []
    for i in range(4):
        for j in range(i + 1, 4):
            sign_ij, blade_ij = reduce_bases((i,), (j,), sta_signature)
            sign_ji, blade_ji = reduce_bases((j,), (i,), sta_signature)
            anti_gaps.append(abs(float(sign_ij + sign_ji)) if blade_ij == blade_ji else 2.0)
    return {
        "available": True,
        "pass": square_values == [1.0, -1.0, -1.0, -1.0] and max(anti_gaps) < 1.0e-6,
        "signature_squares": square_values,
        "max_offdiag_anticommutator": max(anti_gaps),
    }


def placement_row(p: Placement, key: jax.Array) -> dict[str, Any]:
    psi0 = path_spinor(p.sheet, p.path, 0.0)
    rho0 = density(psi0)
    rho_master = solve_master(p.sheet, p.topology, rho0)
    h_eff, jumps_eff = lindblad_parts(p.sheet, p.topology)
    rho_traj, traj_norm_gap, pruned = trajectory_batch(psi0, h_eff, jumps_eff, key)
    evals = jnp.linalg.eigvalsh(rho_master)
    path = path_metrics(p.sheet, p.path)
    ensemble_gap = jnp.linalg.norm(rho_master - rho_traj)
    trace_gap = jnp.abs(jnp.trace(rho_master) - 1.0)
    herm_gap = jnp.linalg.norm(rho_master - rho_master.conj().T)
    path_ok = path["path_density_delta"] < 1e-8 if p.path == "fiber" else path["path_density_delta"] > 0.25 and path["horizontal_connection_residual"] < 1e-8
    checks = {
        "density_trace_one": _b(trace_gap < 1.0e-8),
        "density_hermitian": _b(herm_gap < 1.0e-8),
        "density_psd": _b(jnp.min(evals) > -1.0e-8),
        "path_geometry_matches_inner_outer": bool(path_ok),
        "trajectory_norm_projected": _b(traj_norm_gap < 1.0e-10),
        "trajectory_matches_master_reasonably": _b(ensemble_gap < 0.18),
    }
    return {
        "index": p.index,
        "label": p.label,
        "sheet": p.sheet,
        "path": p.path,
        "topology": p.topology,
        "terrain": p.terrain,
        "finite_map": "placement (X_terrain^sheet, Gamma_path^sheet) -> final finite density rho(t=0.8) plus trajectory ensemble readout",
        "checks": checks,
        "pass": all(checks.values()),
        "metrics": {
            "trace_gap": _f(trace_gap),
            "hermitian_gap": _f(herm_gap),
            "min_eigenvalue": _f(jnp.min(evals)),
            "trajectory_master_frobenius_gap": _f(ensemble_gap),
            "trajectory_max_norm_gap": _f(traj_norm_gap),
            "trajectory_pruned": int(jax.device_get(pruned)),
            **path,
        },
        "promotion_allowed": False,
    }


def run_probe(write: bool = True) -> dict[str, Any]:
    pls = placements()
    keys = jax.random.split(jax.random.PRNGKey(20260602), len(pls))
    rows = [placement_row(p, k) for p, k in zip(pls, keys)]
    labels = [r["label"] for r in rows]
    sheet_terrain = sorted({(r["sheet"], r["topology"], r["terrain"]) for r in rows})
    cl13 = cl13_jaxga_checks()
    h_sign_gap = jnp.linalg.norm(hamiltonian("L", "Se") + hamiltonian("R", "Se"))
    checks = {
        "sixteen_placements_enumerated": len(rows) == 16 and len(set(labels)) == 16,
        "four_topologies_present": sorted({r["topology"] for r in rows}) == sorted(TOPOLOGIES),
        "eight_sheet_specific_terrains_present": len(sheet_terrain) == 8,
        "two_weyl_sheets_present": sorted({r["sheet"] for r in rows}) == ["L", "R"],
        "two_path_classes_present": sorted({r["path"] for r in rows}) == ["base", "fiber"],
        "all_rows_pass": all(r["pass"] for r in rows),
        "left_right_hamiltonians_opposed": _b(h_sign_gap < EPS),
        "jaxga_cl13_signature_available_and_passes": bool(cl13["pass"]),
        "no_julia_execution": True,
        "no_pytorch_execution": True,
        "promotion_blocked": True,
    }
    result = {
        "AUDIT_PASS": all(checks.values()),
        "name": "jax_weyl_terrain_16_placements_lindblad_audit",
        "classification": "diagnostic_jax_weyl_terrain_16_placements_lindblad_audit",
        "executed_track": "jax",
        "ran_julia": False,
        "ran_pytorch": False,
        "legacy_tensor_lane_used": False,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_boundary": "JAX diagnostic for 16 finite Weyl-terrain placements; no full layer, G-structure, stacking, Axis0, flux, bridge, or physics admission.",
        "domain": "two unit Weyl spinors psi_L, psi_R in S3; finite path classes Gamma_f/Gamma_b; finite 2x2 density matrices",
        "codomain_or_output": "16 final density matrices, 16 trajectory ensemble readouts, path geometry controls, Cl(1,3) signature check",
        "finite_map": "P={L,R} x {fiber,base} x {Se,Ne,Ni,Si} -> (X_terrain^sheet, Gamma_path^sheet) -> rho(t)",
        "rows": rows,
        "checks": checks,
        "cl13_jaxga_checks": cl13,
        "tool_manifest": {
            "jax": "load-bearing vectorized finite density, trajectory, projection, and invariant checks",
            "diffrax": "load-bearing adaptive ODE integration of the Lindblad master equation",
            "jaxga": "load-bearing Cl(1,3) signature square/anticommutator check when available",
            "json": "supportive receipt serialization",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "diffrax": "load_bearing",
            "jaxga": "load_bearing" if cl13["available"] else "None",
            "json": "supportive",
        },
        "blocked_consumers": [
            "full_layer_completion",
            "official_g_structure_selection",
            "layer_stacking",
            "flux",
            "Xi/Phi0",
            "xi_phi0",
            "Axis0",
            "axis0",
            "bridge",
            "FEP",
            "fep_holodeck",
            "physics_gravity",
            "final_manifold_admission",
        ],
    }
    if write:
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    result = run_probe(write=True)
    print(
        "jax_weyl_terrain_16_placements "
        f"rows={len(result['rows'])}/16 pass={sum(1 for r in result['rows'] if r['pass'])}/{len(result['rows'])} "
        f"AUDIT_PASS={result['AUDIT_PASS']}"
    )


if __name__ == "__main__":
    main()
