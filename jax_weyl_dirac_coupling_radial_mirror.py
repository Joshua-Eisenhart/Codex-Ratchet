#!/usr/bin/env python3
"""JAX-only Weyl-to-Dirac radial coupling diagnostic.

Julia reference, read-only:
    system_v5/julia_carrier/layers/emergence_3d_dirac_from_weyl_coupling.jl

This is the JAX audit lane, not the native Julia/Grassmann lane and not a
PyTorch port. It builds a finite L/R Weyl block with

    H_L = +H0,  H_R = -H0,  C_LR = m I2

and checks that the off-diagonal radial coupling gives the Dirac spectrum,
gamma5/chirality readouts, density readouts, unitary evolution, and kill
controls. The receipt is diagnostic only and blocks promotion.
"""

from __future__ import annotations

import json
from functools import partial
from pathlib import Path
from typing import Any

import jax
from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp


OUT = Path("jax_weyl_dirac_coupling_radial_mirror_results.json")
JULIA_REFERENCE = "system_v5/julia_carrier/layers/emergence_3d_dirac_from_weyl_coupling.jl"
JULIA_REFERENCE_RESULT = "system_v5/julia_carrier/layers/emergence_3d_dirac_from_weyl_coupling_results.json"

I = 1j
EPS = 1.0e-10
I2 = jnp.eye(2, dtype=jnp.complex128)
Z2 = jnp.zeros((2, 2), dtype=jnp.complex128)
I4 = jnp.eye(4, dtype=jnp.complex128)
SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.asarray([[0.0, -I], [I, 0.0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)


def block2(a: jax.Array, b: jax.Array, c: jax.Array, d: jax.Array) -> jax.Array:
    return jnp.concatenate(
        [jnp.concatenate([a, b], axis=1), jnp.concatenate([c, d], axis=1)],
        axis=0,
    )


G0 = block2(Z2, I2, I2, Z2)
G1 = block2(Z2, SX, -SX, Z2)
G2 = block2(Z2, SY, -SY, Z2)
G3 = block2(Z2, SZ, -SZ, Z2)
GAMMAS = jnp.stack([G0, G1, G2, G3])
METRIC = jnp.asarray([1.0, -1.0, -1.0, -1.0], dtype=jnp.float64)
G5 = I * G0 @ G1 @ G2 @ G3
GAMMA_THETA = G0


def _f(x: Any) -> float:
    return float(jax.device_get(jnp.real(x)))


def _b(x: Any) -> bool:
    return bool(jax.device_get(x))


def jsonable(x: Any) -> Any:
    x = jax.device_get(x)
    if hasattr(x, "tolist"):
        return x.tolist()
    if isinstance(x, (complex,)):
        return {"real": float(x.real), "imag": float(x.imag)}
    return x


def h0(kvec: jax.Array) -> jax.Array:
    return kvec[0] * SX + kvec[1] * SY + kvec[2] * SZ


def two_leaf_h(kvec: jax.Array, mass: float, *, coupled: bool = True, wrong_sign: bool = False) -> jax.Array:
    base = h0(kvec)
    h_l = +base
    h_r = +base if wrong_sign else -base
    c = mass * I2 if coupled else Z2
    return block2(h_l, c, c.conj().T, h_r)


def wrong_channel_h(kvec: jax.Array, mass: float) -> jax.Array:
    base = h0(kvec)
    # Chirality-preserving perturbation: it changes on-leaf Weyl blocks but
    # never opens the L/R off-diagonal Dirac mass channel.
    return block2(+base + mass * SZ, Z2, Z2, -base - mass * SZ)


def radial_chain_h(kvec: jax.Array, mass: float, n_leaf: int = 8, *, coupled: bool = True) -> jax.Array:
    dim = 2 * n_leaf
    h = jnp.zeros((dim, dim), dtype=jnp.complex128)
    base = h0(kvec)
    for leaf in range(n_leaf):
        sl = slice(2 * leaf, 2 * leaf + 2)
        sign = 1.0 if leaf % 2 == 0 else -1.0
        h = h.at[sl, sl].set(sign * base)
    if coupled:
        for leaf in range(n_leaf - 1):
            a = slice(2 * leaf, 2 * leaf + 2)
            b = slice(2 * (leaf + 1), 2 * (leaf + 1) + 2)
            h = h.at[a, b].set(mass * I2)
            h = h.at[b, a].set(mass * I2)
    return h


def central_gap(h: jax.Array) -> jax.Array:
    ev = jnp.linalg.eigvalsh(0.5 * (h + h.conj().T))
    n = ev.shape[0] // 2
    return ev[n] - ev[n - 1]


def normalize(psi: jax.Array) -> jax.Array:
    return psi / jnp.linalg.norm(psi, axis=-1, keepdims=True)


def chiral_charge(psi: jax.Array) -> jax.Array:
    return jnp.real(jnp.einsum("...i,ij,...j->...", jnp.conj(psi), G5, psi))


def mass_bilinear_state(psi: jax.Array) -> jax.Array:
    return jnp.real(jnp.einsum("...i,ij,...j->...", jnp.conj(psi), G0, psi))


def density_from_state(psi: jax.Array) -> jax.Array:
    psi = normalize(psi)
    return psi[..., :, None] * jnp.conj(psi[..., None, :])


def occupied_density(h: jax.Array, rank: int = 2) -> jax.Array:
    _vals, vecs = jnp.linalg.eigh(0.5 * (h + h.conj().T))
    occ = vecs[:, :rank]
    projector = occ @ occ.conj().T
    return projector / rank


def density_metrics(rho: jax.Array, projector_rank: int | None = None) -> dict[str, Any]:
    rho_h = 0.5 * (rho + rho.conj().T)
    ev = jnp.linalg.eigvalsh(rho_h)
    trace = jnp.trace(rho)
    metrics: dict[str, Any] = {
        "trace_real": _f(jnp.real(trace)),
        "trace_imag_abs": _f(jnp.abs(jnp.imag(trace))),
        "trace_error": _f(jnp.abs(trace - 1.0)),
        "hermitian_error": _f(jnp.max(jnp.abs(rho - rho.conj().T))),
        "min_eigenvalue": _f(jnp.min(ev)),
        "purity": _f(jnp.real(jnp.trace(rho @ rho))),
        "mbar_trace_gamma0": _f(jnp.real(jnp.trace(rho @ G0))),
        "gamma5_trace": _f(jnp.real(jnp.trace(rho @ G5))),
        "lr_coherence_norm": _f(jnp.linalg.norm(rho[:2, 2:4])),
        "left_weight": _f(jnp.real(jnp.trace(rho[:2, :2]))),
        "right_weight": _f(jnp.real(jnp.trace(rho[2:4, 2:4]))),
    }
    if projector_rank is not None:
        metrics["rank_normalized_projector_error"] = _f(jnp.max(jnp.abs(rho @ rho - rho / projector_rank)))
    return metrics


def unitary_from_h(h: jax.Array, dt: float) -> jax.Array:
    vals, vecs = jnp.linalg.eigh(0.5 * (h + h.conj().T))
    phases = jnp.exp(-1j * vals * dt)
    return (vecs * phases[None, :]) @ vecs.conj().T


@partial(jax.jit, static_argnames=("steps",))
def evolve_norm_drift(h: jax.Array, states: jax.Array, dt: jax.Array, steps: int) -> tuple[jax.Array, jax.Array]:
    u = unitary_from_h(h, dt)

    def step(psi: jax.Array, _unused: None) -> tuple[jax.Array, jax.Array]:
        nxt = psi @ u.T
        return nxt, jnp.max(jnp.abs(jnp.linalg.norm(nxt, axis=-1) - 1.0))

    final, drifts = jax.lax.scan(step, states, None, length=steps)
    return final, jnp.max(drifts)


def carrier_checks() -> dict[str, Any]:
    clifford_errors = []
    for mu in range(4):
        for nu in range(4):
            anti = GAMMAS[mu] @ GAMMAS[nu] + GAMMAS[nu] @ GAMMAS[mu]
            expected = 2.0 * METRIC[mu] * I4 if mu == nu else jnp.zeros((4, 4), dtype=jnp.complex128)
            clifford_errors.append(jnp.max(jnp.abs(anti - expected)))
    max_cliff = jnp.max(jnp.asarray(clifford_errors))
    g5_diag = jnp.real(jnp.diag(G5))
    gamma_theta_ll = jnp.max(jnp.abs(GAMMA_THETA[:2, :2]))
    gamma_theta_rr = jnp.max(jnp.abs(GAMMA_THETA[2:4, 2:4]))
    gamma_theta_lr = jnp.max(jnp.abs(GAMMA_THETA[:2, 2:4]))
    return {
        "clifford_algebra_ok": _b(max_cliff < EPS),
        "max_clifford_residual": _f(max_cliff),
        "gamma5_square_ok": _b(jnp.max(jnp.abs(G5 @ G5 - I4)) < EPS),
        "gamma5_diag": jsonable(g5_diag),
        "weyl_split_ok": _b(jnp.max(jnp.abs(g5_diag - jnp.asarray([-1.0, -1.0, 1.0, 1.0]))) < EPS),
        "gamma_theta_offdiagonal_LR": _b((gamma_theta_ll < EPS) & (gamma_theta_rr < EPS) & (gamma_theta_lr > 0.5)),
        "gamma_theta_LL_block_norm": _f(gamma_theta_ll),
        "gamma_theta_RR_block_norm": _f(gamma_theta_rr),
        "gamma_theta_LR_block_norm": _f(gamma_theta_lr),
    }


def chirality_checks() -> dict[str, Any]:
    key = jax.random.PRNGKey(20260601)
    raw = jax.random.normal(key, (512, 2, 2), dtype=jnp.float64)
    w = normalize(raw[..., 0] + 1j * raw[..., 1])
    zeros = jnp.zeros_like(w)
    left = jnp.concatenate([w, zeros], axis=1)
    right = jnp.concatenate([zeros, w], axis=1)
    q_l = chiral_charge(left)
    q_r = chiral_charge(right)
    m_l = mass_bilinear_state(left)
    m_r = mass_bilinear_state(right)
    return {
        "left_gamma5_minus_one": _b(jnp.max(jnp.abs(q_l + 1.0)) < 1.0e-12),
        "right_gamma5_plus_one": _b(jnp.max(jnp.abs(q_r - 1.0)) < 1.0e-12),
        "pure_chirality_mbar_zero": _b(jnp.max(jnp.maximum(jnp.abs(m_l), jnp.abs(m_r))) < 1.0e-12),
        "max_left_chirality_error": _f(jnp.max(jnp.abs(q_l + 1.0))),
        "max_right_chirality_error": _f(jnp.max(jnp.abs(q_r - 1.0))),
        "max_pure_chirality_mbar": _f(jnp.max(jnp.maximum(jnp.abs(m_l), jnp.abs(m_r)))),
    }


def spectral_and_control_checks(kvec: jax.Array, mass: float) -> dict[str, Any]:
    kabs = jnp.linalg.norm(kvec)
    h_correct = two_leaf_h(kvec, mass, coupled=True, wrong_sign=False)
    h_off = two_leaf_h(kvec, mass, coupled=False, wrong_sign=False)
    h_node_on = two_leaf_h(jnp.zeros(3, dtype=jnp.float64), mass, coupled=True, wrong_sign=False)
    h_node_off = two_leaf_h(jnp.zeros(3, dtype=jnp.float64), mass, coupled=False, wrong_sign=False)
    h_wrong_sign = two_leaf_h(kvec, mass, coupled=True, wrong_sign=True)
    h_wrong_channel = wrong_channel_h(kvec, mass)

    ev_correct = jnp.linalg.eigvalsh(h_correct)
    ev_off = jnp.linalg.eigvalsh(h_off)
    ev_wrong_sign = jnp.linalg.eigvalsh(h_wrong_sign)
    e_dirac = jnp.sqrt(kabs * kabs + mass * mass)
    expected = jnp.sort(jnp.asarray([-e_dirac, -e_dirac, e_dirac, e_dirac], dtype=jnp.float64))
    correct_spectrum_error = jnp.max(jnp.abs(ev_correct - expected))
    off_expected = jnp.sort(jnp.asarray([-kabs, -kabs, kabs, kabs], dtype=jnp.float64))
    off_spectrum_error = jnp.max(jnp.abs(ev_off - off_expected))

    kinetic_correct = two_leaf_h(kvec, 0.0, coupled=False, wrong_sign=False)
    kinetic_wrong = two_leaf_h(kvec, 0.0, coupled=False, wrong_sign=True)
    mass_only = two_leaf_h(jnp.zeros(3, dtype=jnp.float64), mass, coupled=True, wrong_sign=False)
    anti_correct = jnp.max(jnp.abs(kinetic_correct @ mass_only + mass_only @ kinetic_correct))
    anti_wrong = jnp.max(jnp.abs(kinetic_wrong @ mass_only + mass_only @ kinetic_wrong))
    h2_correct_error = jnp.max(jnp.abs(h_correct @ h_correct - (kabs * kabs + mass * mass) * I4))
    h2_wrong_error = jnp.max(jnp.abs(h_wrong_sign @ h_wrong_sign - (kabs * kabs + mass * mass) * I4))

    rho_off = occupied_density(h_off, rank=2)
    rho_on = occupied_density(h_correct, rank=2)
    rho_wrong_sign = occupied_density(h_wrong_sign, rank=2)
    rho_wrong_channel = occupied_density(h_wrong_channel, rank=2)
    dm_off = density_metrics(rho_off, projector_rank=2)
    dm_on = density_metrics(rho_on, projector_rank=2)
    dm_wrong_sign = density_metrics(rho_wrong_sign, projector_rank=2)
    dm_wrong_channel = density_metrics(rho_wrong_channel, projector_rank=2)

    node_gap_off = central_gap(h_node_off)
    node_gap_on = central_gap(h_node_on)
    wrong_channel_mbar_abs = jnp.abs(jnp.real(jnp.trace(rho_wrong_channel @ G0)))

    checks = {
        "correct_hermitian": _b(jnp.max(jnp.abs(h_correct - h_correct.conj().T)) < EPS),
        "coupling_off_hermitian": _b(jnp.max(jnp.abs(h_off - h_off.conj().T)) < EPS),
        "correct_spectrum_dirac": _b(correct_spectrum_error < 1.0e-9),
        "coupling_off_spectrum_weyl": _b(off_spectrum_error < 1.0e-9),
        "node_gap_off_zero": _b(node_gap_off < 1.0e-12),
        "node_gap_on_equals_2m": _b(jnp.abs(node_gap_on - 2.0 * abs(mass)) < 1.0e-9),
        "correct_kinetic_mass_anticommute": _b(anti_correct < 1.0e-10),
        "correct_h2_scalar": _b(h2_correct_error < 1.0e-9),
        "coupling_off_density_no_dirac_mass": abs(dm_off["mbar_trace_gamma0"]) < 1.0e-10,
        "coupled_density_has_dirac_mass": abs(dm_on["mbar_trace_gamma0"]) > 1.0e-3,
        "wrong_sign_rejected_by_anticommutator": _b(anti_wrong > 1.0e-3),
        "wrong_sign_rejected_by_h2": _b(h2_wrong_error > 1.0e-3),
        "wrong_channel_no_dirac_mass": _b(wrong_channel_mbar_abs < 1.0e-10),
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "kvec": jsonable(kvec),
        "kabs": _f(kabs),
        "mass": mass,
        "eigenvalues_correct": jsonable(ev_correct),
        "eigenvalues_coupling_off": jsonable(ev_off),
        "eigenvalues_wrong_sign": jsonable(ev_wrong_sign),
        "dirac_energy_sqrt_k2_m2": _f(e_dirac),
        "correct_spectrum_max_error": _f(correct_spectrum_error),
        "coupling_off_spectrum_max_error": _f(off_spectrum_error),
        "node_gap_off": _f(node_gap_off),
        "node_gap_on": _f(node_gap_on),
        "anti_correct_residual": _f(anti_correct),
        "anti_wrong_sign_residual": _f(anti_wrong),
        "h2_correct_residual": _f(h2_correct_error),
        "h2_wrong_sign_residual": _f(h2_wrong_error),
        "density_coupling_off": dm_off,
        "density_coupled": dm_on,
        "density_wrong_sign": dm_wrong_sign,
        "density_wrong_channel": dm_wrong_channel,
    }


def radial_chain_checks(kvec: jax.Array, mass: float) -> dict[str, Any]:
    h_off_node = radial_chain_h(jnp.zeros(3, dtype=jnp.float64), mass, coupled=False)
    h_on_node = radial_chain_h(jnp.zeros(3, dtype=jnp.float64), mass, coupled=True)
    h_on_fixed = radial_chain_h(kvec, mass, coupled=True)
    h_off_fixed = radial_chain_h(kvec, mass, coupled=False)
    n_leaf = 8

    adjacent_weight = 0.0
    nonadjacent_weight = 0.0
    for a in range(n_leaf):
        for b in range(n_leaf):
            if a == b:
                continue
            block = h_on_fixed[2 * a : 2 * a + 2, 2 * b : 2 * b + 2]
            w = _f(jnp.linalg.norm(block))
            if abs(a - b) == 1:
                adjacent_weight += w
            else:
                nonadjacent_weight += w

    node_gap_off = central_gap(h_off_node)
    node_gap_on = central_gap(h_on_node)
    fixed_gap_off = central_gap(h_off_fixed)
    fixed_gap_on = central_gap(h_on_fixed)
    checks = {
        "chain_hermitian": _b(jnp.max(jnp.abs(h_on_fixed - h_on_fixed.conj().T)) < EPS),
        "adjacent_radial_coupling_nonzero": adjacent_weight > 1.0,
        "nonadjacent_radial_coupling_zero": nonadjacent_weight < 1.0e-12,
        "node_gap_off_zero": _b(node_gap_off < 1.0e-12),
        "node_gap_opens_with_radial_coupling": _b(node_gap_on > 1.0e-3),
        "fixed_gap_not_smaller_when_coupled": _b(fixed_gap_on >= fixed_gap_off - 1.0e-9),
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "n_leaf": n_leaf,
        "node_gap_off": _f(node_gap_off),
        "node_gap_on": _f(node_gap_on),
        "fixed_gap_off": _f(fixed_gap_off),
        "fixed_gap_on": _f(fixed_gap_on),
        "adjacent_weight": adjacent_weight,
        "nonadjacent_weight": nonadjacent_weight,
    }


def unitary_checks(h: jax.Array) -> dict[str, Any]:
    dt = 0.03
    steps = 64
    key = jax.random.PRNGKey(404)
    raw = jax.random.normal(key, (128, 4, 2), dtype=jnp.float64)
    states = normalize(raw[..., 0] + 1j * raw[..., 1])
    u = unitary_from_h(h, dt)
    final, max_scan_drift = evolve_norm_drift(h, states, jnp.asarray(dt, dtype=jnp.float64), steps)
    rho0 = density_from_state(states[0])
    rhof = density_from_state(final[0])
    checks = {
        "unitary_matrix": _b(jnp.max(jnp.abs(u.conj().T @ u - I4)) < 1.0e-10),
        "evolution_norm_preserved": _b(max_scan_drift < 1.0e-10),
        "density_trace_preserved": _f(jnp.abs(jnp.trace(rhof) - jnp.trace(rho0))) < 1.0e-10,
        "density_hermitian_after_evolution": _f(jnp.max(jnp.abs(rhof - rhof.conj().T))) < 1.0e-10,
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "unitarity_error": _f(jnp.max(jnp.abs(u.conj().T @ u - I4))),
        "max_norm_drift": _f(max_scan_drift),
        "rho0": density_metrics(rho0),
        "rhof": density_metrics(rhof),
        "dt": dt,
        "steps": steps,
        "ensemble_size": int(states.shape[0]),
    }


def main() -> None:
    kvec = jnp.asarray([0.6, 0.2, -0.5], dtype=jnp.float64)
    mass = 0.9

    carrier = carrier_checks()
    chirality = chirality_checks()
    spectral = spectral_and_control_checks(kvec, mass)
    chain = radial_chain_checks(kvec, mass)
    unitary = unitary_checks(two_leaf_h(kvec, mass, coupled=True, wrong_sign=False))

    checks = {
        "carrier": bool(
            carrier["clifford_algebra_ok"]
            and carrier["gamma5_square_ok"]
            and carrier["weyl_split_ok"]
            and carrier["gamma_theta_offdiagonal_LR"]
        ),
        "chirality": bool(
            chirality["left_gamma5_minus_one"]
            and chirality["right_gamma5_plus_one"]
            and chirality["pure_chirality_mbar_zero"]
        ),
        "two_leaf_spectral_controls": bool(spectral["pass"]),
        "radial_chain": bool(chain["pass"]),
        "unitarity_density": bool(unitary["pass"]),
    }
    audit_pass = all(checks.values())

    receipt = {
        "object": "jax_weyl_dirac_coupling_radial_mirror",
        "classification": "diagnostic_only",
        "promotion_status": "diagnostic_only",
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "julia_reference_read_only": JULIA_REFERENCE,
        "julia_reference_result_read_only": JULIA_REFERENCE_RESULT,
        "sim_execution_kind": "nonclassical_diagnostic_jax_audit",
        "finite_map": "finite L/R Weyl pair plus 8-leaf radial chain -> Dirac spectral, chirality, density, and unitary readouts",
        "domain": {
            "weyl_blocks": "L,R two-component complex spinors",
            "hamiltonians": "H_L=+H0, H_R=-H0, off-diagonal C_LR=m I2",
            "radial_chain_leaves": 8,
        },
        "codomain_or_output": "finite JSON receipt of spectra, gamma5 charges, density readouts, controls, and pass/fail booleans",
        "root_constraints_in_force": ["F01 finite carrier/probe/operator/path set", "N01 L/R order-sensitive off-diagonal coupling controls"],
        "tool_manifest": {
            "jax": "load_bearing finite complex linear algebra, eigensystems, unitary evolution, batched norm checks",
            "jax.numpy": "load_bearing matrix construction and density readouts",
            "json": "receipt writer only",
        },
        "tool_integration_depth": {"jax": "load_bearing", "json": "supportive"},
        "blocked_consumers": [
            "layer_completion",
            "G_structure_selection",
            "Axis0",
            "FEP",
            "flux",
            "physics_gravity",
            "final_manifold_admission",
        ],
        "carrier": carrier,
        "chirality": chirality,
        "two_leaf": spectral,
        "radial_chain": chain,
        "unitarity_density": unitary,
        "checks": checks,
        "AUDIT_PASS": audit_pass,
        "all_pass": audit_pass,
    }

    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        "jax_weyl_dirac_coupling_radial_mirror "
        f"two_leaf={spectral['pass']} chain={chain['pass']} "
        f"density={unitary['pass']} controls={checks['two_leaf_spectral_controls']} "
        f"AUDIT_PASS={audit_pass}"
    )
    print(f"wrote={OUT}")


if __name__ == "__main__":
    main()
