#!/usr/bin/env python3

import hashlib
import json
import math
from datetime import datetime, timezone

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp

N_ETA = 200
N_CHI = 400
H = 1.0e-5
ROW_SOURCE = "/tmp/16_token_axis_projection_matrix.json"
OUT_PATH = "/tmp/wol_geometry_2_jax_results.json"


def read_row_source():
    with open(ROW_SOURCE, "rb") as f:
        raw = f.read()
    data = json.loads(raw.decode("utf-8"))
    tokens = data.get("tokens", [])
    return {
        "path": ROW_SOURCE,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "token_count": len(tokens),
        "signed_operator_count": len(data.get("signed_operators", [])),
        "lock_check_counts": data.get("lock_check_counts", {}),
        "first_token": tokens[0].get("token") if tokens else None,
    }


def psi_s(phi, chi, eta):
    phase_plus_arg = phi + chi
    phase_minus_arg = phi - chi
    phase_plus = jnp.cos(phase_plus_arg) + 1j * jnp.sin(phase_plus_arg)
    phase_minus = jnp.cos(phase_minus_arg) + 1j * jnp.sin(phase_minus_arg)
    a = phase_plus * jnp.cos(eta)
    b = phase_minus * jnp.sin(eta)
    psi = jnp.stack([a, b], axis=-1)
    norm = jnp.sqrt(jnp.real(jnp.sum(jnp.conj(psi) * psi, axis=-1)))
    return psi / norm[..., None]


def projector_from_psi(psi):
    return psi[..., :, None] * jnp.conj(psi[..., None, :])


def projector_L(eta, chi):
    return projector_from_psi(psi_s(0.0, chi, eta))


def projector_R(eta, chi):
    return projector_from_psi(psi_s(0.0, chi, eta))


def projector_trivial(eta, chi):
    shape = jnp.broadcast_shapes(jnp.shape(eta), jnp.shape(chi))
    base = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
    return jnp.broadcast_to(base, shape + (2, 2))


FROZEN_PROJECTOR = projector_from_psi(psi_s(0.217, 0.923, 0.371))


def projector_frozen(eta, chi):
    shape = jnp.broadcast_shapes(jnp.shape(eta), jnp.shape(chi))
    return jnp.broadcast_to(FROZEN_PROJECTOR, shape + (2, 2))


def curvature_grid(projector_fn, eta_grid, chi_grid):
    p = projector_fn(eta_grid, chi_grid)
    dp_eta = (projector_fn(eta_grid + H, chi_grid) - projector_fn(eta_grid - H, chi_grid)) / (2.0 * H)
    dp_chi = (projector_fn(eta_grid, chi_grid + H) - projector_fn(eta_grid, chi_grid - H)) / (2.0 * H)
    comm = jnp.matmul(dp_eta, dp_chi) - jnp.matmul(dp_chi, dp_eta)
    trace_terms = jnp.einsum("...ij,...ji->...", p, comm)
    return jnp.real(1j * trace_terms)


def integrate_chern(projector_fn):
    d_eta = (math.pi / 2.0) / N_ETA
    d_chi = (2.0 * math.pi) / N_CHI
    eta = (jnp.arange(N_ETA, dtype=jnp.float64) + 0.5) * d_eta
    chi = (jnp.arange(N_CHI, dtype=jnp.float64) + 0.5) * d_chi
    eta_grid = eta[:, None]
    chi_grid = chi[None, :]
    f = curvature_grid(projector_fn, eta_grid, chi_grid)
    integral = jnp.sum(f) * d_eta * d_chi
    c1 = integral / (2.0 * math.pi)
    return float(c1), float(integral), float(jnp.min(f)), float(jnp.max(f))


def curvature_sample(projector_fn, eta, chi):
    eta_v = jnp.array(eta, dtype=jnp.float64)
    chi_v = jnp.array(chi, dtype=jnp.float64)
    f_eta_chi = curvature_grid(projector_fn, eta_v, chi_v)
    p = projector_fn(eta_v, chi_v)
    dp_eta = (projector_fn(eta_v + H, chi_v) - projector_fn(eta_v - H, chi_v)) / (2.0 * H)
    dp_chi = (projector_fn(eta_v, chi_v + H) - projector_fn(eta_v, chi_v - H)) / (2.0 * H)
    rev_comm = jnp.matmul(dp_chi, dp_eta) - jnp.matmul(dp_eta, dp_chi)
    f_chi_eta = jnp.real(1j * jnp.einsum("ij,ji->", p, rev_comm))
    return {
        "eta": eta,
        "chi": chi,
        "F_eta_chi": float(f_eta_chi),
        "F_chi_eta": float(f_chi_eta),
        "Delta": float(f_eta_chi - f_chi_eta),
    }


def result_block(c1, integral, f_min, f_max):
    rounded = int(round(c1))
    return {
        "c1": c1,
        "integral_F": integral,
        "rounded": rounded,
        "integer_error": abs(c1 - rounded),
        "abs_c1_minus_1": abs(abs(c1) - 1.0),
        "F_min": f_min,
        "F_max": f_max,
    }


def complex_pairs(values):
    host = jax.device_get(values)
    return [{"re": float(jnp.real(z)), "im": float(jnp.imag(z))} for z in host]


def main():
    rows = read_row_source()

    c1_l, integral_l, fmin_l, fmax_l = integrate_chern(projector_L)
    c1_r, integral_r, fmin_r, fmax_r = integrate_chern(projector_R)
    c1_trivial, integral_trivial, fmin_trivial, fmax_trivial = integrate_chern(projector_trivial)
    c1_frozen, integral_frozen, fmin_frozen, fmax_frozen = integrate_chern(projector_frozen)

    delta_l = curvature_sample(projector_L, math.pi / 4.0, math.pi / 3.0)
    delta_trivial = curvature_sample(projector_trivial, math.pi / 4.0, math.pi / 3.0)

    positive_pass = abs(abs(c1_l) - 1.0) < 0.01 and abs(abs(c1_r) - 1.0) < 0.01
    negative_pass = abs(c1_trivial) < 0.01
    kill_pass = abs(c1_frozen) < 0.01
    boundary_pass = abs(c1_l - round(c1_l)) < 0.01 and abs(c1_r - round(c1_r)) < 0.01
    n01_pass = abs(delta_l["Delta"]) > 1.0e-6 and abs(delta_trivial["Delta"]) < 1.0e-10
    all_pass = positive_pass and negative_pass and kill_pass and boundary_pass and n01_pass

    sample_psi = psi_s(0.217, 0.923, 0.371)

    result = {
        "object_id": "wol_geometry_2_u1_chern_locked_full_s2_base",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "stage": "geometry",
        "item": "3/7",
        "engine": "jax",
        "claim_ceiling": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ground_truth_source": rows,
        "psi_source": "built directly in JAX from locked formula psi_s(phi,chi;eta)=[exp(i*(phi+chi))*cos(eta), exp(i*(phi-chi))*sin(eta)]",
        "psi_not_from_row_matrix": True,
        "fiber_phi_for_base_section": 0.0,
        "grid": {
            "N_eta": N_ETA,
            "N_chi": N_CHI,
            "eta_range": [0.0, math.pi / 2.0],
            "chi_range": [0.0, 2.0 * math.pi],
            "finite_difference": "central projector differences",
            "h": H,
        },
        "F01": {
            "finite_carrier": "midpoint grid over S2 base rectangle",
            "domain": "{(eta_i, chi_j): i=1..200, j=1..400}",
            "domain_size": N_ETA * N_CHI,
            "codomain": "{F_eta_chi(i,j) real scalar curvature values}",
        },
        "N01": {
            "operation": "commutator [dP/d_eta, dP/d_chi]",
            "delta_L_sample": delta_l,
            "delta_trivial_sample": delta_trivial,
            "order_sensitive_pass": n01_pass,
        },
        "c1_L": c1_l,
        "c1_R": c1_r,
        "c1_trivial": c1_trivial,
        "c1_frozen_kill": c1_frozen,
        "L_details": result_block(c1_l, integral_l, fmin_l, fmax_l),
        "R_details": result_block(c1_r, integral_r, fmin_r, fmax_r),
        "trivial_details": result_block(c1_trivial, integral_trivial, fmin_trivial, fmax_trivial),
        "frozen_kill_details": result_block(c1_frozen, integral_frozen, fmin_frozen, fmax_frozen),
        "controls": {
            "positive_expected_abs_c1": 1.0,
            "positive_pass": positive_pass,
            "negative_trivial_expected_c1": 0.0,
            "negative_pass": negative_pass,
            "kill_frozen_expected_c1": 0.0,
            "kill_pass": kill_pass,
            "boundary_integer_pass": boundary_pass,
        },
        "all_pass": all_pass,
        "diagnostic_note": "The locked formula over chi in [0,2pi] gives a raw pullback Chern number near +/-2 in this sign convention, so the requested |c1|=1 positive control is not forced here.",
        "sample_psi_L_phi_0_217_chi_0_923_eta_0_371": complex_pairs(sample_psi),
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")

    print(
        f"c1_L={c1_l:.12f} c1_R={c1_r:.12f} "
        f"c1_trivial={c1_trivial:.12f} c1_frozen_kill={c1_frozen:.12f} all_pass={all_pass}"
    )
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
