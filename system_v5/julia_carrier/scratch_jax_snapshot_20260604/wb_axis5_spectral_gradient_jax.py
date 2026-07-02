#!/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3
"""
wb_axis5_spectral_gradient_jax.py

JAX audit lane for axis5_spectral_gradient_v1. Reads the Julia carrier JSON,
independently recomputes the N=32 entropy readouts from the same deterministic
seed table, and writes the strict parity JSON requested for the lane.

Claim ceiling:
  Does NOT assert layer-completion, manifold admission, coupling, bridge,
  flux, or physics. promotion_allowed=false. A state that passes is a candidate,
  not a proven object.

Re-run:
  /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 /tmp/wb_axis5_spectral_gradient_jax.py
"""

from __future__ import annotations

import json
import math
import os
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("JAX_ENABLE_X64", "1")

import jax
import jax.numpy as jnp

jax.config.update("jax_enable_x64", True)

OBJECT_ID = "axis5_spectral_gradient_v1"
JULIA_RESULT_PATH = Path(
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/"
    "wb_axis5_spectral_gradient_julia_results.json"
)
PARITY_OUTPUT_PATH = Path("/tmp/wb_axis5_spectral_gradient_parity.json")

RNG_SEED = 20260604
PARITY_N = 32
SPEC_EPS = 1.0e-6
GRAD_EPS = 1.0e-6
COMMUTE_EPS = 1.0e-6
N01_EPS = 1.0e-9
DELTA_THRESHOLD = 1.0e-6

CLAIM_CEILING = (
    "Does NOT assert layer-completion, manifold admission, coupling, bridge, "
    "flux, or physics. promotion_allowed=false. A state that passes is a "
    "candidate, not a proven object."
)

I2 = jnp.eye(2, dtype=jnp.complex128)
SX = jnp.array([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SZ = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=jnp.complex128)
H = (SX + SZ) / jnp.sqrt(jnp.array(2.0, dtype=jnp.float64))


def rotation(pauli: jnp.ndarray, angle: float) -> jnp.ndarray:
    return (
        math.cos(angle / 2.0) * I2
        - 1j * math.sin(angle / 2.0) * pauli
    )


FI = rotation(SX, math.pi / 2.0)
FE = rotation(SZ, math.pi / 2.0)


def unitary_apply(unitary: jnp.ndarray, rho: jnp.ndarray) -> jnp.ndarray:
    return unitary @ rho @ jnp.conjugate(unitary.T)


def z_dephase(rho: jnp.ndarray) -> jnp.ndarray:
    return jnp.diag(jnp.diag(rho)).astype(jnp.complex128)


def x_dephase(rho: jnp.ndarray) -> jnp.ndarray:
    rho_x = H @ rho @ jnp.conjugate(H.T)
    return jnp.conjugate(H.T) @ z_dephase(rho_x) @ H


def von_neumann_entropy(rho: jnp.ndarray) -> float:
    clean = (rho + jnp.conjugate(rho.T)) / 2.0
    eigvals = jnp.linalg.eigvalsh(clean)
    total = 0.0
    for value in [float(x) for x in eigvals]:
        if value > 1.0e-14:
            total -= value * math.log(value)
    return float(total)


def seeded_fraction(seed: int, n: int, idx: int, stride: int, modulus: int, offset: int) -> float:
    raw = ((seed % modulus) + stride * n + offset * idx) % modulus
    return (float(raw) + 0.5) / float(modulus)


def seeded_angles(seed: int, n: int, idx: int) -> tuple[float, float, float]:
    theta_frac = seeded_fraction(seed, n, idx, 37, 997, 53)
    phi_frac = seeded_fraction(seed, n, idx, 101, 991, 67)
    chi_frac = seeded_fraction(seed, n, idx, 131, 983, 71)
    theta = math.pi * (0.11 + 0.78 * theta_frac)
    phi = 2.0 * math.pi * phi_frac
    chi = 2.0 * math.pi * chi_frac
    return theta, phi, chi


def sheet_sign_for_index(idx: int) -> float:
    return 1.0 if idx % 2 == 1 else -1.0


def chirality_for_index(idx: int) -> str:
    return "L" if idx % 2 == 1 else "R"


def weyl_density(seed: int, n: int, idx: int) -> jnp.ndarray:
    theta, phi, chi = seeded_angles(seed, n, idx)
    sheet_sign = sheet_sign_for_index(idx)
    psi0 = complex(
        math.cos(phi + sheet_sign * chi),
        math.sin(phi + sheet_sign * chi),
    ) * math.cos(theta / 2.0)
    psi1 = complex(
        math.cos(phi - sheet_sign * chi),
        math.sin(phi - sheet_sign * chi),
    ) * math.sin(theta / 2.0)
    psi = jnp.array([psi0, psi1], dtype=jnp.complex128)
    psi = psi / jnp.linalg.norm(psi)
    return jnp.outer(psi, jnp.conjugate(psi))


def density_valid(rho: jnp.ndarray) -> bool:
    trace_ok = abs(complex(jnp.trace(rho)) - 1.0) < 1.0e-10
    hermitian_ok = float(jnp.linalg.norm(rho - jnp.conjugate(rho.T))) < 1.0e-10
    eig_ok = all(float(value) >= -1.0e-10 for value in jnp.linalg.eigvalsh((rho + jnp.conjugate(rho.T)) / 2.0))
    return bool(trace_ok and hermitian_ok and eig_ok)


def analyze_state(seed: int, n: int, idx: int) -> dict:
    rho = weyl_density(seed, n, idx)
    s0 = von_neumann_entropy(rho)

    rho_ti = z_dephase(rho)
    rho_te = x_dephase(rho)
    rho_fi = unitary_apply(FI, rho)
    rho_fe = unitary_apply(FE, rho)

    gain_ti = von_neumann_entropy(rho_ti) - s0
    gain_te = von_neumann_entropy(rho_te) - s0
    gain_fi = von_neumann_entropy(rho_fi) - s0
    gain_fe = von_neumann_entropy(rho_fe) - s0

    spectral_then_gradient = unitary_apply(FI, z_dephase(rho))
    gradient_then_spectral = z_dephase(unitary_apply(FI, rho))
    n01_gap = float(jnp.linalg.norm(spectral_then_gradient - gradient_then_spectral))

    control_spectral_then_gradient = unitary_apply(FE, z_dephase(rho))
    control_gradient_then_spectral = z_dephase(unitary_apply(FE, rho))
    control_order_gap = float(jnp.linalg.norm(control_spectral_then_gradient - control_gradient_then_spectral))
    control_gain_a = von_neumann_entropy(control_spectral_then_gradient) - s0
    control_gain_b = von_neumann_entropy(control_gradient_then_spectral) - s0
    control_entropy_gain_gap = abs(control_gain_a - control_gain_b)

    return {
        "state_index": idx,
        "chirality": chirality_for_index(idx),
        "gain_spectral_Ti": gain_ti,
        "gain_spectral_Te": gain_te,
        "gain_gradient_Fi": gain_fi,
        "gain_gradient_Fe": gain_fe,
        "n01_gap": n01_gap,
        "n01_pass": n01_gap > N01_EPS,
        "commuting_control_order_gap": control_order_gap,
        "commuting_control_entropy_gain_gap": control_entropy_gain_gap,
        "commuting_control_pass": (
            control_order_gap < COMMUTE_EPS
            and control_entropy_gain_gap < COMMUTE_EPS
        ),
        "rho_valid": density_valid(rho),
        "post_rho_valid": all(
            density_valid(candidate)
            for candidate in (rho_ti, rho_te, rho_fi, rho_fe)
        ),
    }


def compute_reference(seed: int, n: int) -> dict:
    rows = [analyze_state(seed, n, idx) for idx in range(1, n + 1)]
    gains_ti = [row["gain_spectral_Ti"] for row in rows]
    gains_te = [row["gain_spectral_Te"] for row in rows]
    gains_fi = [row["gain_gradient_Fi"] for row in rows]
    gains_fe = [row["gain_gradient_Fe"] for row in rows]
    mean_gain_ti = sum(row["gain_spectral_Ti"] for row in rows) / n
    mean_gain_te = sum(row["gain_spectral_Te"] for row in rows) / n
    mean_gain_fi = sum(row["gain_gradient_Fi"] for row in rows) / n
    mean_gain_fe = sum(row["gain_gradient_Fe"] for row in rows) / n
    return {
        "N": n,
        "rng_seed": seed,
        "jax_spectral_entropy_gain": mean_gain_ti,
        "jax_gradient_entropy_gain": mean_gain_fi,
        "mean_gain_spectral_Te": mean_gain_te,
        "mean_gain_gradient_Fe": mean_gain_fe,
        "min_gain_spectral_Ti": min(gains_ti),
        "min_gain_spectral_Te": min(gains_te),
        "max_abs_gain_gradient_Fi": max(abs(gain) for gain in gains_fi),
        "max_abs_gain_gradient_Fe": max(abs(gain) for gain in gains_fe),
        "spectral_entropy_gain_positive": all(gain > SPEC_EPS for gain in gains_ti)
        and all(gain > SPEC_EPS for gain in gains_te),
        "gradient_entropy_gain_near_zero": all(abs(gain) < GRAD_EPS for gain in gains_fi)
        and all(abs(gain) < GRAD_EPS for gain in gains_fe),
        "n01_noncommuting_control_survived": all(row["n01_pass"] for row in rows),
        "wrong_structure_control_indistinguishable": all(row["commuting_control_pass"] for row in rows),
        "rho_valid": all(row["rho_valid"] and row["post_rho_valid"] for row in rows),
        "max_n01_gap": max(row["n01_gap"] for row in rows),
        "max_commuting_control_order_gap": max(row["commuting_control_order_gap"] for row in rows),
        "max_commuting_control_entropy_gain_gap": max(row["commuting_control_entropy_gain_gap"] for row in rows),
    }


def main() -> bool:
    if not JULIA_RESULT_PATH.exists():
        raise FileNotFoundError(f"Julia result JSON missing: {JULIA_RESULT_PATH}")

    with JULIA_RESULT_PATH.open() as handle:
        julia_data = json.load(handle)

    parity_ref = julia_data.get("parity_reference", {})
    julia_spectral = parity_ref.get("julia_spectral_entropy_gain")
    julia_gradient = parity_ref.get("julia_gradient_entropy_gain")
    if julia_spectral is None:
        julia_spectral = parity_ref["mean_gain_spectral_Ti"]
    if julia_gradient is None:
        julia_gradient = parity_ref["mean_gain_gradient_Fi"]

    seed = int(parity_ref.get("rng_seed", RNG_SEED))
    n = int(parity_ref.get("N", PARITY_N))
    jax_ref = compute_reference(seed, n)

    delta_spectral = abs(float(julia_spectral) - jax_ref["jax_spectral_entropy_gain"])
    delta_gradient = abs(float(julia_gradient) - jax_ref["jax_gradient_entropy_gain"])
    max_abs_delta = max(delta_spectral, delta_gradient)
    parity_pass = max_abs_delta < DELTA_THRESHOLD

    jax_gate_pass = (
        jax_ref["spectral_entropy_gain_positive"]
        and jax_ref["gradient_entropy_gain_near_zero"]
        and jax_ref["n01_noncommuting_control_survived"]
        and jax_ref["wrong_structure_control_indistinguishable"]
        and jax_ref["rho_valid"]
    )

    payload = {
        "object_id": OBJECT_ID,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
        "classification": "tool_lego_fit_probe",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_path": str(Path(__file__)),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "execution_command": (
            "/tmp/wb_axis5_spectral_gradient_jax.py"
        ),
        "julia_result_path": str(JULIA_RESULT_PATH),
        "julia_result_exists": True,
        "parity_N": n,
        "rng_seed": seed,
        "seed_protocol": "deterministic arithmetic state table shared by Julia and JAX",
        "julia_spectral_entropy_gain": float(julia_spectral),
        "jax_spectral_entropy_gain": jax_ref["jax_spectral_entropy_gain"],
        "julia_gradient_entropy_gain": float(julia_gradient),
        "jax_gradient_entropy_gain": jax_ref["jax_gradient_entropy_gain"],
        "delta_spectral": delta_spectral,
        "delta_gradient": delta_gradient,
        "max_abs_delta": max_abs_delta,
        "delta_threshold": DELTA_THRESHOLD,
        "parity_pass": parity_pass,
        "julia_all_pass": bool(julia_data.get("all_pass", False)),
        "jax_gate_pass": bool(jax_gate_pass),
        "jax_reference": jax_ref,
        "finite_map": {
            "domain": "(rho_L or rho_R, op_class in {spectral, gradient, commuting_control})",
            "codomain_or_output": "(von_Neumann_entropy_after, entropy_gain, frobenius_order_gap, axis5_class)",
        },
        "TOOL_MANIFEST": {
            "JAX": {
                "used": True,
                "reason": "load_bearing: independent parity recomputation of entropy monotone values",
            },
            "entropy_monotone_check": {
                "used": True,
                "reason": "load_bearing: parity_pass depends on spectral and gradient entropy gain deltas",
            },
            "json": {
                "used": True,
                "reason": "supportive: reads Julia receipt and writes parity receipt",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "JAX": "load_bearing",
            "entropy_monotone_check": "load_bearing",
            "json": "supportive",
        },
        "tool_manifest": {
            "JAX": "load_bearing",
            "entropy_monotone_check": "load_bearing",
            "json": "supportive",
        },
        "tool_integration_depth": {
            "JAX": "load_bearing",
            "entropy_monotone_check": "load_bearing",
            "json": "supportive",
        },
        "blocked_consumers": [
            "layer-completion",
            "manifold admission",
            "coupling",
            "bridge",
            "Phi0",
            "Xi",
            "Axis0",
            "flux",
            "physics",
        ],
    }

    with PARITY_OUTPUT_PATH.open("w") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")

    print("=== AXIS-5 JAX PARITY LANE ===")
    print(f"julia_result_path: {JULIA_RESULT_PATH}")
    print(f"julia_spectral_entropy_gain: {payload['julia_spectral_entropy_gain']:.16g}")
    print(f"jax_spectral_entropy_gain: {payload['jax_spectral_entropy_gain']:.16g}")
    print(f"max_abs_delta: {max_abs_delta:.16g}")
    print(f"parity_pass: {parity_pass}")
    print(f"jax_gate_pass: {jax_gate_pass}")
    print(f"parity_path: {PARITY_OUTPUT_PATH}")
    return bool(parity_pass and jax_gate_pass and bool(julia_data.get("all_pass", False)))


if __name__ == "__main__":
    try:
        ok = main()
    except Exception as exc:
        print(f"Axis-5 JAX parity failed: {exc}", file=sys.stderr)
        raise
    sys.exit(0 if ok else 1)
