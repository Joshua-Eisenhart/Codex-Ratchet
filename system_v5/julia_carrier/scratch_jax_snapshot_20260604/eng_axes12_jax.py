#!/usr/bin/env python3
"""
JAX parity audit for Axis 1 (expand/compress) + Axis 2 (open/closed).

object_id: eng_axes12_jax_parity_v1
claim_ceiling: candidate — parity probe only. NOT layer-complete. NOT bridge claim.
  promotion_allowed: false

Finite map (mirrors eng_axes12_julia.jl exactly):
  domain: L/R Weyl spinor density matrices, N=32 (parity reference size)
  codomain: (axis1 compress/expand delta_r, axis1 N01 gap,
             axis2 open delta_S, axis2 closed delta_S, axis2 N01 gap,
             divergence_from_5_6 Frobenius gaps)

JAX role: scale/stress/AUDIT lane.
Julia is the truth lane. This file recomputes the same channels in JAX x64,
reads Julia's result JSON for parity comparison, and writes /tmp/eng_axes12_parity.json.

F01: finite ensemble of 32 L/R Weyl spinor density matrices.
N01: compress∘expand ≠ expand∘compress; open∘closed ≠ closed∘open.
"""

from jax import config
config.update("jax_enable_x64", True)

import json
import math
import sys
from pathlib import Path

import jax.numpy as jnp
import numpy as np

# ── Parameters (must match Julia exactly) ─────────────────────────────────────
RNG_SEED   = 20260604
PARITY_N   = 32
SIZE_LADDER = [8, 16, 32, 64]
GAMMA_AX1  = 0.30
GAMMA_BATH = 0.40
OMEGA_AX2  = 1.0
DT_AX2     = 0.5
NSTEPS_AX2 = 4
THETA_AX2  = math.pi / 3.0
P_SZILARD  = 0.5

AX1_EPS    = 1.0e-6
AX2_EPS    = 1.0e-6
AX2_CLOSE  = 1.0e-10
N01_EPS    = 1.0e-9
COMMUTE_EPS = 1.0e-9

PARITY_TOL = 1.0e-8   # max allowed difference between JAX and Julia scalars

# ── Pauli matrices ─────────────────────────────────────────────────────────────
I2 = jnp.eye(2, dtype=jnp.complex128)
SX = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
SZ = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)

# ── State construction (deterministic arithmetic — matches Julia) ──────────────
def seeded_fraction(seed: int, n: int, idx: int, stride: int, modulus: int, offset: int) -> float:
    """Deterministic fraction from arithmetic hash — must match Julia exactly."""
    raw = (seed % modulus + stride * n + offset * idx) % modulus
    return (raw + 0.5) / modulus

def seeded_angles(seed: int, n: int, idx: int):
    theta_frac = seeded_fraction(seed, n, idx, 37, 997, 53)
    phi_frac   = seeded_fraction(seed, n, idx, 101, 991, 67)
    chi_frac   = seeded_fraction(seed, n, idx, 131, 983, 71)
    theta = math.pi * (0.11 + 0.78 * theta_frac)
    phi   = 2.0 * math.pi * phi_frac
    chi   = 2.0 * math.pi * chi_frac
    return theta, phi, chi

def weyl_density(seed: int, n: int, idx: int, sheet_sign: float) -> jnp.ndarray:
    theta, phi, chi = seeded_angles(seed, n, idx)
    psi = jnp.array([
        math.cos(theta / 2.0) * (math.cos(phi + sheet_sign * chi) + 1j * math.sin(phi + sheet_sign * chi)),
        math.sin(theta / 2.0) * (math.cos(phi - sheet_sign * chi) + 1j * math.sin(phi - sheet_sign * chi)),
    ], dtype=jnp.complex128)
    psi = psi / jnp.linalg.norm(psi)
    return jnp.outer(psi, psi.conj())

def ensemble(seed: int, n: int):
    return [weyl_density(seed, n, idx + 1, +1.0 if (idx % 2 == 0) else -1.0) for idx in range(n)]

# ── Quantum operations ─────────────────────────────────────────────────────────
def von_neumann_entropy(rho: jnp.ndarray) -> float:
    clean = (rho + rho.conj().T) / 2.0
    evals = np.linalg.eigvalsh(np.array(clean))
    s = 0.0
    for lam in evals:
        if lam > 1.0e-14:
            s -= lam * math.log(lam)
    return float(s)

def bloch_radius(rho: jnp.ndarray) -> float:
    rx = 2.0 * float(jnp.real(rho[0, 1]))
    ry = 2.0 * float(jnp.imag(rho[1, 0]))
    rz = float(jnp.real(rho[0, 0] - rho[1, 1]))
    return math.sqrt(rx**2 + ry**2 + rz**2)

def kraus_apply(Ks, rho: jnp.ndarray) -> jnp.ndarray:
    out = jnp.zeros((2, 2), dtype=jnp.complex128)
    for K in Ks:
        out = out + K @ rho @ K.conj().T
    return out

# ── Axis 1: CP channels ────────────────────────────────────────────────────────
def compress_channel(gamma: float):
    K0 = jnp.array([[1, 0], [0, math.sqrt(1.0 - gamma)]], dtype=jnp.complex128)
    K1 = jnp.array([[0, math.sqrt(gamma)], [0, 0]], dtype=jnp.complex128)
    return [K0, K1]

def expand_channel(gamma: float):
    K0 = jnp.array([[math.sqrt(1.0 - gamma), 0], [0, 1]], dtype=jnp.complex128)
    K1 = jnp.array([[0, 0], [math.sqrt(gamma), 0]], dtype=jnp.complex128)
    return [K0, K1]

def identity_channel():
    return [jnp.eye(2, dtype=jnp.complex128)]

# ── Axis 2: open/closed ────────────────────────────────────────────────────────
def lindblad_step(rho: jnp.ndarray, H: jnp.ndarray, L: jnp.ndarray, gamma: float, dt: float) -> jnp.ndarray:
    LdL = L.conj().T @ L
    comm = H @ rho - rho @ H
    diss = gamma * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))
    drho = -1j * comm + diss
    rho_new = rho + dt * drho
    t = jnp.trace(rho_new)
    return rho_new / t

def open_channel(rho: jnp.ndarray) -> jnp.ndarray:
    H = OMEGA_AX2 * SZ / 2.0
    # sigma_minus decay: L = sqrt(gamma_bath) * [[0,1],[0,0]]
    L = jnp.array([[0, 1], [0, 0]], dtype=jnp.complex128) * math.sqrt(GAMMA_BATH)
    rho_c = rho
    for _ in range(NSTEPS_AX2):
        rho_c = lindblad_step(rho_c, H, L, 1.0, DT_AX2)
    return rho_c

def closed_channel(rho: jnp.ndarray) -> jnp.ndarray:
    c = math.cos(THETA_AX2 / 2.0)
    s = math.sin(THETA_AX2 / 2.0)
    U = c * I2 - 1j * s * SX
    return U @ rho @ U.conj().T

def commuting_ax2_control(rho: jnp.ndarray) -> jnp.ndarray:
    c = math.cos(THETA_AX2 / 2.0)
    s = math.sin(THETA_AX2 / 2.0)
    U = c * I2 - 1j * s * SX
    return U @ (U @ rho @ U.conj().T) @ U.conj().T

# ── Axis 5 channels (for divergence check) ────────────────────────────────────
def z_dephase(rho: jnp.ndarray) -> jnp.ndarray:
    return jnp.array([[rho[0, 0], 0], [0, rho[1, 1]]], dtype=jnp.complex128)

def x_rotation_Fi(rho: jnp.ndarray) -> jnp.ndarray:
    c = math.cos(math.pi / 4.0)
    s = math.sin(math.pi / 4.0)
    U = c * I2 - 1j * s * SX
    return U @ rho @ U.conj().T

# ── Szilard variant ────────────────────────────────────────────────────────────
def szilard_bit_expand(rho: jnp.ndarray, p: float) -> jnp.ndarray:
    return (1.0 - p) * rho + p * (I2 / 2.0)

def szilard_bit_compress(rho: jnp.ndarray) -> jnp.ndarray:
    K0 = jnp.array([[1, 0], [0, 0]], dtype=jnp.complex128)
    K1 = jnp.array([[0, 1], [0, 0]], dtype=jnp.complex128)
    out = K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T
    t = jnp.trace(out)
    if float(jnp.abs(t)) > 1e-14:
        out = out / t
    return out

# ── Per-state analysis ─────────────────────────────────────────────────────────
def analyze_state(seed: int, n: int, idx_0based: int, rho: jnp.ndarray) -> dict:
    Ks_c = compress_channel(GAMMA_AX1)
    Ks_e = expand_channel(GAMMA_AX1)
    Ks_i = identity_channel()

    rho_c = kraus_apply(Ks_c, rho)
    rho_e = kraus_apply(Ks_e, rho)
    rho_i = kraus_apply(Ks_i, rho)

    r0  = bloch_radius(rho)
    r_c = bloch_radius(rho_c)
    r_e = bloch_radius(rho_e)
    r_i = bloch_radius(rho_i)

    rho_ce = kraus_apply(Ks_e, rho_c)
    rho_ec = kraus_apply(Ks_c, rho_e)
    n01_ax1_gap = float(jnp.linalg.norm(rho_ce - rho_ec))

    rho_ii = kraus_apply(Ks_i, rho_i)
    n01_identity_gap = float(jnp.linalg.norm(rho_ii - rho_i))

    S0 = von_neumann_entropy(rho)
    rho_open   = open_channel(rho)
    rho_closed = closed_channel(rho)

    S_open   = von_neumann_entropy(rho_open)
    S_closed = von_neumann_entropy(rho_closed)

    rho_oc = open_channel(closed_channel(rho))
    rho_co = closed_channel(open_channel(rho))
    n01_ax2_gap = float(jnp.linalg.norm(rho_oc - rho_co))

    rho_zdeph = z_dephase(rho)
    rho_xrot  = x_rotation_Fi(rho)
    ax1_vs_ax5 = float(jnp.linalg.norm(rho_c - rho_zdeph))
    ax2_vs_ax5 = float(jnp.linalg.norm(rho_open - rho_zdeph))
    ax2_vs_ax5_xrot = float(jnp.linalg.norm(rho_open - rho_xrot))

    return {
        "state_index_0based": idx_0based,
        "bloch_r0": r0,
        "ax1_compress_delta_r": r_c - r0,
        "ax1_expand_delta_r":   r_e - r0,
        "ax1_identity_delta_r": r_i - r0,
        "ax1_n01_gap": n01_ax1_gap,
        "ax1_identity_gap": n01_identity_gap,
        "ax2_open_delta_S":   S_open - S0,
        "ax2_closed_delta_S": S_closed - S0,
        "ax2_n01_gap": n01_ax2_gap,
        "ax1_vs_ax5_zdeph_frobenius": ax1_vs_ax5,
        "ax2_vs_ax5_zdeph_frobenius": ax2_vs_ax5,
        "ax2_vs_ax5_xrot_frobenius":  ax2_vs_ax5_xrot,
    }

# ── Size-ladder ────────────────────────────────────────────────────────────────
def run_at_size(seed: int, n: int) -> dict:
    states = ensemble(seed, n)
    rows = [analyze_state(seed, n, idx, rho) for idx, rho in enumerate(states)]
    # (states variable used later for channel_dist)

    compress_dr = [r["ax1_compress_delta_r"] for r in rows]
    expand_dr   = [r["ax1_expand_delta_r"]   for r in rows]
    n01_ax1_gaps = [r["ax1_n01_gap"]          for r in rows]
    identity_gaps = [r["ax1_identity_gap"]    for r in rows]
    open_dS     = [r["ax2_open_delta_S"]      for r in rows]
    closed_dS   = [r["ax2_closed_delta_S"]    for r in rows]
    n01_ax2_gaps = [r["ax2_n01_gap"]          for r in rows]
    ax1_vs5     = [r["ax1_vs_ax5_zdeph_frobenius"] for r in rows]
    ax2_vs5     = [r["ax2_vs_ax5_zdeph_frobenius"] for r in rows]

    ax1_compress_ok  = all(d < -AX1_EPS for d in compress_dr)
    # Channel distinctness: compress(rho) != expand(rho) by Frobenius gap
    Ks_c = compress_channel(GAMMA_AX1)
    Ks_e = expand_channel(GAMMA_AX1)
    channel_dist = [
        float(jnp.linalg.norm(kraus_apply(Ks_c, rho) - kraus_apply(Ks_e, rho)))
        for rho in states
    ]
    ax1_distinct_channels_ok = all(d > AX1_EPS for d in channel_dist)
    n01_ax1_ok       = all(g > N01_EPS for g in n01_ax1_gaps)
    identity_ctrl_ok = all(g < COMMUTE_EPS for g in identity_gaps)

    ax2_open_ok   = all(abs(d) > AX2_EPS for d in open_dS)
    ax2_closed_ok = all(abs(d) < AX2_CLOSE for d in closed_dS)
    n01_ax2_ok    = all(g > N01_EPS for g in n01_ax2_gaps)

    ax1_distinct_ax5 = all(g > N01_EPS for g in ax1_vs5)
    ax2_distinct_ax5 = all(g > N01_EPS for g in ax2_vs5)

    all_pass = (ax1_compress_ok and ax1_distinct_channels_ok and n01_ax1_ok and identity_ctrl_ok and
                ax2_open_ok and ax2_closed_ok and n01_ax2_ok and
                ax1_distinct_ax5 and ax2_distinct_ax5)

    return {
        "N": n,
        "ax1_mean_compress_delta_r": sum(compress_dr) / n,
        "ax1_mean_expand_delta_r":   sum(expand_dr) / n,
        "ax1_min_channel_dist":      min(channel_dist),
        "ax1_mean_channel_dist":     sum(channel_dist) / n,
        "ax1_min_n01_gap":  min(n01_ax1_gaps),
        "ax1_max_identity_gap": max(identity_gaps),
        "ax2_mean_open_delta_S":    sum(open_dS) / n,
        "ax2_max_closed_delta_S_abs": max(abs(d) for d in closed_dS),
        "ax2_min_n01_gap": min(n01_ax2_gaps),
        "mean_ax1_vs_ax5_frobenius": sum(ax1_vs5) / n,
        "mean_ax2_vs_ax5_frobenius": sum(ax2_vs5) / n,
        "ax1_compress_ok": ax1_compress_ok,
        "ax1_distinct_channels_ok": ax1_distinct_channels_ok,
        "ax1_n01_ok": n01_ax1_ok,
        "identity_ctrl_ok": identity_ctrl_ok,
        "ax2_open_ok": ax2_open_ok,
        "ax2_closed_ok": ax2_closed_ok,
        "ax2_n01_ok": n01_ax2_ok,
        "ax1_distinct_from_ax5": ax1_distinct_ax5,
        "ax2_distinct_from_ax5": ax2_distinct_ax5,
        "all_pass": all_pass,
        "state_results": rows,
    }

# ── Parity comparison ──────────────────────────────────────────────────────────
def compare_parity(julia_ref: dict, jax_ref: dict) -> dict:
    """
    Compare Julia parity_reference values against JAX recomputed values.
    Returns max_diff and per-key diffs.
    """
    keys_to_compare = [
        "ax1_mean_compress_delta_r",
        "ax1_mean_expand_delta_r",
        "ax1_mean_channel_dist",
        "ax2_mean_open_delta_S",
        "ax2_max_closed_delta_S_abs",
        "ax1_min_n01_gap",
        "ax2_min_n01_gap",
        "mean_ax1_vs_ax5_frobenius",
        "mean_ax2_vs_ax5_frobenius",
    ]
    diffs = {}
    max_diff = 0.0
    for k in keys_to_compare:
        if k in julia_ref and k in jax_ref:
            d = abs(float(julia_ref[k]) - float(jax_ref[k]))
            diffs[k] = d
            if d > max_diff:
                max_diff = d
        else:
            diffs[k] = None

    return {
        "max_diff": max_diff,
        "per_key_diffs": diffs,
        "parity_pass": max_diff < PARITY_TOL,
        "parity_tol": PARITY_TOL,
    }

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    # Run JAX size ladder
    size_rows = {n: run_at_size(RNG_SEED, n) for n in SIZE_LADDER}
    jax_parity_ref = size_rows[PARITY_N]

    # Try to read Julia result JSON for parity comparison
    julia_result_path = Path(
        "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/eng_axes12_julia_results.json"
    )
    julia_available = julia_result_path.exists()
    julia_parity_ref = None
    parity_result = None

    if julia_available:
        with open(julia_result_path) as f:
            julia_data = json.load(f)
        julia_parity_ref = julia_data.get("parity_reference", {})
        parity_result = compare_parity(julia_parity_ref, jax_parity_ref)
    else:
        parity_result = {
            "max_diff": None,
            "per_key_diffs": {},
            "parity_pass": None,
            "note": "Julia result JSON not found — run Julia carrier first",
        }

    all_pass_jax = all(size_rows[n]["all_pass"] for n in SIZE_LADDER)

    # Aggregate divergence
    ax1_distinct_all = all(size_rows[n]["ax1_distinct_from_ax5"] for n in SIZE_LADDER)
    ax2_distinct_all = all(size_rows[n]["ax2_distinct_from_ax5"] for n in SIZE_LADDER)

    output = {
        "object_id": "eng_axes12_jax_parity_v1",
        "classification": "tool_lego_fit_probe",
        "classification_note": "parity audit only; promotion_allowed=false",
        "promotion_allowed": False,
        "claim_ceiling": "JAX recomputation of axis1+axis2 channels for parity against Julia. No layer/manifold/bridge/physics claims.",
        "rng_seed": RNG_SEED,
        "parity_n": PARITY_N,
        "size_ladder": SIZE_LADDER,
        "jax_size_ladder_results": {str(n): size_rows[n] for n in SIZE_LADDER},
        "julia_result_path": str(julia_result_path),
        "julia_available": julia_available,
        "parity_comparison": parity_result,
        "all_pass_jax": all_pass_jax,
        "ax1_distinct_from_ax5_all_sizes": ax1_distinct_all,
        "ax2_distinct_from_ax5_all_sizes": ax2_distinct_all,
        "independent_from_5_6_jax": (
            "INDEPENDENT: axis1 compress != axis5 zdephase by Frobenius gap; "
            "axis2 open Lindblad != axis5 zdephase by Frobenius gap."
        ) if (ax1_distinct_all and ax2_distinct_all) else "NOT_CONFIRMED",
        "root_constraints_in_force": {
            "F01": "finite 8/16/32/64 Weyl spinor density matrices",
            "N01": "compress-expand order gap > N01_EPS; open-closed order gap > N01_EPS",
        },
        "thresholds": {
            "AX1_EPS": AX1_EPS,
            "AX2_EPS": AX2_EPS,
            "AX2_CLOSE": AX2_CLOSE,
            "N01_EPS": N01_EPS,
            "COMMUTE_EPS": COMMUTE_EPS,
            "PARITY_TOL": PARITY_TOL,
            "GAMMA_AX1": GAMMA_AX1,
            "GAMMA_BATH": GAMMA_BATH,
            "THETA_AX2": THETA_AX2,
            "P_SZILARD": P_SZILARD,
        },
        "blocked_consumers": ["layer-completion", "manifold admission", "coupling", "bridge", "Phi0", "Xi", "Axis0", "flux", "physics"],
    }

    out_path = Path("/tmp/eng_axes12_parity.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
        f.write("\n")

    print("=== AXIS 1+2 JAX PARITY ===")
    print(f"object_id: {output['object_id']}")
    print(f"julia_available: {julia_available}")
    print(f"all_pass_jax: {all_pass_jax}")
    for n in SIZE_LADDER:
        r = size_rows[n]
        print(f"  N={n}: ax1_compress_Δr={r['ax1_mean_compress_delta_r']:.6f}"
              f"  ax1_expand_Δr={r['ax1_mean_expand_delta_r']:.6f}"
              f"  ax2_open_ΔS={r['ax2_mean_open_delta_S']:.6f}"
              f"  ax2_closed_ΔS_max={r['ax2_max_closed_delta_S_abs']:.2e}"
              f"  all_pass={r['all_pass']}")
    if parity_result and parity_result.get("max_diff") is not None:
        md = parity_result["max_diff"]
        pp = parity_result["parity_pass"]
        print(f"parity_max_diff={md:.3e}  parity_pass={pp}")
    else:
        print("parity_comparison: Julia JSON not found; run Julia first")
    print(f"independent_from_5_6: {output['independent_from_5_6_jax']}")
    print(f"result_path: {out_path}")

    return 0 if all_pass_jax else 1

if __name__ == "__main__":
    sys.exit(main())
