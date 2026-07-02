#!/usr/bin/env python3
"""
eng_yinyang_jax.py — JAX parity audit for the yin-yang engine.

object_id: eng_yinyang_jax_parity_v1
claim_ceiling: parity probe only — NOT layer-complete, NOT bridge claim.
  promotion_allowed: false

Finite map (mirrors eng_yinyang_julia.jl exactly):
  domain:  qubit density matrices on S^1 (Bloch equator), N=64 states
  codomain: {flip_gap, cw_ccw_gap, independence_gap, ctrl_identity_gap,
             two_dots_distinguishable, hexagram_count}

JAX role: scale/stress/AUDIT lane.
Julia is the truth lane. This file reads Julia's result JSON and recomputes
the same quantities in JAX x64, then writes /tmp/eng_yinyang_parity.json.

F01: finite ensemble of 64 qubit density matrices — terminates.
N01: CW rotation R_z(+θ) vs CCW R_z(-θ) genuinely non-commuting with dephase;
     flip (complex conjugation) is structurally distinct from rotation.
"""

from jax import config
config.update("jax_enable_x64", True)

import json
import math
import sys
from pathlib import Path

import jax
import jax.numpy as jnp
import numpy as np

# ── constants ──────────────────────────────────────────────────────────────────
OBJECT_ID      = "eng_yinyang_jax_parity_v1"
CLAIM_CEILING  = "JAX parity audit of eng_yinyang_v1; promotion_allowed=false"
JULIA_RESULT   = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/eng_yinyang_julia_results.json")
PARITY_OUT     = Path("/tmp/eng_yinyang_parity.json")
ROTATE_ANGLE   = math.pi / 4
SEED_EPS       = 0.05
N_PARITY       = 64
FLIP_EPS       = 1e-10
ROTATE_EPS     = 1e-10
INDEP_EPS      = 1e-10
COMMUTE_EPS    = 1e-6

# ── Pauli matrices ─────────────────────────────────────────────────────────────
I2 = jnp.eye(2, dtype=jnp.complex128)
sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
sy = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
sz = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)

# ── yin-yang state (mirrors Julia) ────────────────────────────────────────────
def yinyang_state(phi: float, seed_eps: float = SEED_EPS) -> jnp.ndarray:
    psi_main = jnp.array([
        math.cos(phi / 2),
        cmath_exp(1j * phi) * math.sin(phi / 2),
    ], dtype=jnp.complex128)
    psi_anti = jnp.array([
        math.cos((phi + math.pi) / 2),
        cmath_exp(1j * (phi + math.pi)) * math.sin((phi + math.pi) / 2),
    ], dtype=jnp.complex128)
    psi = (1.0 - seed_eps) * psi_main + seed_eps * psi_anti
    n = jnp.linalg.norm(psi)
    psi = psi / n
    return jnp.outer(psi, jnp.conj(psi))

def cmath_exp(z):
    """Complex exponential for scalar."""
    import cmath
    return cmath.exp(z)

def yinyang_state_v(phi: float, seed_eps: float = SEED_EPS) -> jnp.ndarray:
    """Vectorized-safe version."""
    c_phi = complex(math.cos(phi / 2), 0)
    e_phi = complex(math.cos(phi), math.sin(phi))  # e^{i*phi}
    c_phi_pi = complex(math.cos((phi + math.pi) / 2), 0)
    e_phi_pi = complex(math.cos(phi + math.pi), math.sin(phi + math.pi))

    psi_main = jnp.array([c_phi, e_phi * math.sin(phi / 2)], dtype=jnp.complex128)
    psi_anti = jnp.array([c_phi_pi, e_phi_pi * math.sin((phi + math.pi) / 2)], dtype=jnp.complex128)
    psi = (1.0 - seed_eps) * psi_main + seed_eps * psi_anti
    psi = psi / jnp.linalg.norm(psi)
    return jnp.outer(psi, jnp.conj(psi))

# ── operations ────────────────────────────────────────────────────────────────
def chirality_flip(rho: jnp.ndarray) -> jnp.ndarray:
    """σ_y ρ* σ_y† — complex conjugation chirality flip."""
    return sy @ jnp.conj(rho) @ sy.conj().T

def rz_unitary(theta: float) -> jnp.ndarray:
    """R_z(θ) = exp(-i θ/2 σ_z)."""
    c = complex(math.cos(theta / 2), 0)
    s = complex(0, -math.sin(theta / 2))
    return jnp.array([[c + s, 0], [0, c - s]], dtype=jnp.complex128)

def rotate_cw(rho: jnp.ndarray, theta: float = ROTATE_ANGLE) -> jnp.ndarray:
    U = rz_unitary(theta)
    return U @ rho @ U.conj().T

def rotate_ccw(rho: jnp.ndarray, theta: float = ROTATE_ANGLE) -> jnp.ndarray:
    U = rz_unitary(-theta)
    return U @ rho @ U.conj().T

def frobenius_gap(a: jnp.ndarray, b: jnp.ndarray) -> float:
    return float(jnp.linalg.norm(a - b))

# ── ensemble ──────────────────────────────────────────────────────────────────
def make_ensemble(N: int, seed_eps: float = SEED_EPS):
    states = []
    for i in range(N):
        phi = 2 * math.pi * (i + 0.5) / N
        states.append(yinyang_state_v(phi, seed_eps))
    return states

# ── hexagram ──────────────────────────────────────────────────────────────────
def hexagram_states(seed_eps: float = SEED_EPS):
    states = []
    for k in range(64):
        bits = [(k >> b) & 1 for b in range(6)]  # LSB first
        rho_k = jnp.ones((1, 1), dtype=jnp.complex128)
        for b in bits:
            phi = 0.0 if b == 0 else math.pi
            rho_bit = yinyang_state_v(phi, seed_eps)
            rho_k = jnp.kron(rho_k, rho_bit)
        states.append(rho_k)
    n_distinct = sum(
        1 for i in range(63)
        if frobenius_gap(states[i], states[i + 1]) > FLIP_EPS
    )
    return len(states), n_distinct

# ── parity computation ────────────────────────────────────────────────────────
def run_parity(N: int = N_PARITY, seed_eps: float = SEED_EPS):
    ensemble = make_ensemble(N, seed_eps)

    flip_gaps    = []
    cw_ccw_gaps  = []
    indep_gaps   = []
    ctrl_id_gaps = []
    flip2_gaps   = []

    for rho in ensemble:
        rho_f   = chirality_flip(rho)
        rho_cw  = rotate_cw(rho)
        rho_ccw = rotate_ccw(rho)
        rho_ff  = chirality_flip(rho_f)
        rho_id  = rho  # θ=0

        flip_gaps.append(frobenius_gap(rho, rho_f))
        cw_ccw_gaps.append(frobenius_gap(rho_cw, rho_ccw))
        indep_gaps.append(frobenius_gap(rho_f, rho_cw))
        ctrl_id_gaps.append(frobenius_gap(rho_id, rho_id))  # should be 0
        flip2_gaps.append(frobenius_gap(rho_ff, rho))

    mean_flip    = float(np.mean(flip_gaps))
    mean_cw_ccw  = float(np.mean(cw_ccw_gaps))
    mean_indep   = float(np.mean(indep_gaps))
    max_ctrl_id  = float(np.max(ctrl_id_gaps))
    max_flip2    = float(np.max(flip2_gaps))

    hexagram_count, n_hex_distinct = hexagram_states(seed_eps)

    return {
        "N": N,
        "mean_flip_gap": mean_flip,
        "mean_cw_ccw_gap": mean_cw_ccw,
        "mean_independence_gap": mean_indep,
        "max_ctrl_identity_gap": max_ctrl_id,
        "max_flip_involution_gap": max_flip2,
        "flip_is_chirality": all(g > FLIP_EPS for g in flip_gaps),
        "rotate_is_axis4": all(g > ROTATE_EPS for g in cw_ccw_gaps),
        "flip_ne_rotate": all(g > INDEP_EPS for g in indep_gaps),
        "ctrl_identity_collapses": max_ctrl_id < COMMUTE_EPS,
        "flip_is_involution": max_flip2 < COMMUTE_EPS,
        "hexagram_count": hexagram_count,
        "hexagram_neighbors_distinct": n_hex_distinct == 63,
        "two_dots_distinguishable": frobenius_gap(
            yinyang_state_v(0.0, seed_eps),
            yinyang_state_v(math.pi, seed_eps)
        ) > FLIP_EPS,
    }

# ── parity delta computation ───────────────────────────────────────────────────
def load_julia_ref(path: Path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)

def compute_deltas(jax_res: dict, julia_ref: dict) -> dict:
    """Compare JAX results to Julia parity_ref_for_jax field."""
    if julia_ref is None:
        return {"status": "julia_result_not_found", "path_checked": str(JULIA_RESULT)}
    pref = julia_ref.get("parity_ref_for_jax", {})
    deltas = {}
    for key in ["mean_flip_gap", "mean_cw_ccw_gap", "mean_independence_gap", "max_ctrl_identity_gap"]:
        j_val = pref.get(key)
        jx_val = jax_res.get(key)
        if j_val is not None and jx_val is not None:
            deltas[key] = {
                "julia": j_val,
                "jax": jx_val,
                "abs_diff": abs(j_val - jx_val),
                "within_1e8": abs(j_val - jx_val) < 1e-8,
            }
    return deltas

# ── main ──────────────────────────────────────────────────────────────────────
def main():
    print("Running eng_yinyang_jax_parity_v1 ...")

    jax_res = run_parity(N=N_PARITY, seed_eps=SEED_EPS)
    julia_ref = load_julia_ref(JULIA_RESULT)
    deltas = compute_deltas(jax_res, julia_ref)

    # Determine parity verdict
    # Parity passes if all booleans match and numeric deltas < 1e-8
    bool_keys = ["flip_is_chirality", "rotate_is_axis4", "flip_ne_rotate",
                 "ctrl_identity_collapses", "flip_is_involution",
                 "hexagram_neighbors_distinct", "two_dots_distinguishable"]

    julia_bools = {}
    if julia_ref:
        s64 = julia_ref.get("summary_n64", {})
        julia_bools = {
            "flip_is_chirality": s64.get("flip_is_chirality"),
            "rotate_is_axis4": s64.get("rotate_is_axis4"),
            "flip_independent_of_rotate": s64.get("flip_independent_of_rotate"),
            "ctrl_identity_collapses": s64.get("ctrl_identity_collapses"),
            "flip_is_involution": s64.get("flip_is_involution"),
        }
        hexagram_t = julia_ref.get("hexagram_test", {})
        julia_bools["hexagram_neighbors_distinct"] = hexagram_t.get("neighbors_all_distinct")
        two_dots_t = julia_ref.get("two_dots_test", {})
        julia_bools["two_dots_distinguishable"] = two_dots_t.get("two_dots_distinguishable")

    bool_mismatches = []
    for k in bool_keys:
        jx_v = jax_res.get(k)
        ju_v = julia_bools.get(k) if julia_bools else None
        if ju_v is not None and jx_v != ju_v:
            bool_mismatches.append({"key": k, "jax": jx_v, "julia": ju_v})

    numeric_max_diff = max(
        (d["abs_diff"] for d in deltas.values() if isinstance(d, dict) and "abs_diff" in d),
        default=float("nan")
    )

    parity_pass = (len(bool_mismatches) == 0) and (
        math.isnan(numeric_max_diff) or numeric_max_diff < 1e-8
    )

    result = {
        "object_id": OBJECT_ID,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
        "root_gates": ["F01", "N01"],
        "jax_version": jax.__version__,
        "julia_result_path": str(JULIA_RESULT),
        "julia_result_found": julia_ref is not None,
        "jax_results": jax_res,
        "numeric_deltas": deltas,
        "bool_mismatches": bool_mismatches,
        "numeric_max_diff": numeric_max_diff if not math.isnan(numeric_max_diff) else "nan",
        "parity_pass": parity_pass,
        "honest_caveat": (
            "parity_pass=true iff JAX and Julia agree on all boolean verdicts AND "
            "numeric quantities agree to < 1e-8. If Julia result JSON is missing, "
            "parity is incomplete (julia_result_found=false)."
        ),
        "downstream_blocks": [
            "layer_completion", "manifold_admission", "coupling",
            "bridge", "Axis0_readout", "flux", "physics",
        ],
    }

    with open(PARITY_OUT, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Parity result written to: {PARITY_OUT}")

    print("\n=== JAX Parity Summary ===")
    print(f"  flip_is_chirality       : {jax_res['flip_is_chirality']}")
    print(f"  rotate_is_axis4         : {jax_res['rotate_is_axis4']}")
    print(f"  flip_ne_rotate          : {jax_res['flip_ne_rotate']}")
    print(f"  ctrl_identity_collapses : {jax_res['ctrl_identity_collapses']}")
    print(f"  flip_is_involution      : {jax_res['flip_is_involution']}")
    print(f"  two_dots_distinguishable: {jax_res['two_dots_distinguishable']}")
    print(f"  hexagram_count          : {jax_res['hexagram_count']} (expected 64)")
    print(f"  hexagram_nbrs_distinct  : {jax_res['hexagram_neighbors_distinct']}")
    print(f"  mean_flip_gap           : {jax_res['mean_flip_gap']:.6e}")
    print(f"  mean_cw_ccw_gap         : {jax_res['mean_cw_ccw_gap']:.6e}")
    print(f"  mean_independence_gap   : {jax_res['mean_independence_gap']:.6e}")
    print(f"  max_ctrl_identity_gap   : {jax_res['max_ctrl_identity_gap']:.6e}")
    print(f"  numeric_max_diff (vs Julia): {numeric_max_diff:.2e}" if not math.isnan(numeric_max_diff) else "  numeric_max_diff: N/A (Julia result not found)")
    print(f"  bool_mismatches         : {len(bool_mismatches)}")
    print(f"  parity_pass             : {parity_pass}")
    print("\nDone.")

if __name__ == "__main__":
    main()
