#!/usr/bin/env python3
"""
sim_hopf_pointwise_pullback.py
==============================

Bounded Hopf pointwise pullback probe.

Purpose
-------
Test the pointwise bridge on sampled S³ / Hopf geometry:

    x ↦ ρ(x) = ρ_L(x) ⊗ ρ_R(x) ↦ Φ₀(ρ(x))

where Φ₀ is the coherent-information kernel I_c(A⟩B) and the companion
mutual information I(A:B).

The key structural prediction from the Hopf fibration:
- Fiber loops: density is constant (ρ_f(u) = ρ_f(0)), so the pullback
  Φ₀(ρ(γ_fiber(u))) must be constant along the fiber.
- Base loops: density varies (ρ_b(u) traces a path on the Bloch sphere),
  so the pullback Φ₀(ρ(γ_base(u))) should vary along the base.

This probe does NOT broaden into the full bridge family. It tests only the
pointwise product-state pullback on sampled S³ points across the three
nested Hopf tori.

Token: E_SIM_HOPF_POINTWISE_PULLBACK_OK
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from datetime import UTC, datetime

import numpy as np
classification = "canonical"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    berry_phase,
    fiber_action,
    hopf_map,
    left_density,
    right_density,
    sample_fiber,
    torus_coordinates,
)
from proto_ratchet_sim_runner import EvidenceToken


RESULTS_PATH = os.path.join(
    os.path.dirname(__file__),
    "a2_state",
    "sim_results",
    "hopf_pointwise_pullback_results.json",
)

TORUS_CONFIGS = [
    ("inner", TORUS_INNER),
    ("clifford", TORUS_CLIFFORD),
    ("outer", TORUS_OUTER),
]

N_SAMPLES = 64


# ── helpers ───────────────────────────────────────────────────────

def von_neumann_entropy(rho: np.ndarray) -> float:
    vals = np.real(np.linalg.eigvalsh((rho + rho.conj().T) / 2))
    vals = vals[vals > 1e-15]
    return float(-np.sum(vals * np.log2(vals))) if len(vals) else 0.0


def pair_state(q: np.ndarray) -> np.ndarray:
    """Product pair state ρ_L ⊗ ρ_R from a single S³ point."""
    return np.kron(left_density(q), right_density(q))


def pointwise_pullback(q: np.ndarray) -> dict:
    """Compute Φ₀(ρ(x)) at a single S³ point.

    Returns I(A:B), I_c(A⟩B), S(A|B), S_A, S_B, S_AB, and the Bloch vector.
    """
    rho_ab = pair_state(q)
    # partial traces for 2⊗2 system
    rho_a = np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)
    rho_b = np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)
    s_a = von_neumann_entropy(rho_a)
    s_b = von_neumann_entropy(rho_b)
    s_ab = von_neumann_entropy(rho_ab)
    i_ab = max(0.0, s_a + s_b - s_ab)
    s_a_given_b = s_ab - s_b
    i_c = -s_a_given_b  # coherent information I_c(A⟩B) = S(B) - S(AB)
    bloch = hopf_map(q).tolist()
    return {
        "I_AB": float(i_ab),
        "I_c_A_to_B": float(i_c),
        "S_A_given_B": float(s_a_given_b),
        "S_A": float(s_a),
        "S_B": float(s_b),
        "S_AB": float(s_ab),
        "bloch": bloch,
    }


def exact_fiber_q(eta: float, u: float) -> np.ndarray:
    """Fiber loop: phase rotation at fixed base point."""
    q0 = torus_coordinates(eta, 0.0, 0.0)
    return fiber_action(q0, u)


def exact_base_q(eta: float, u: float) -> np.ndarray:
    """Horizontal base loop: density-traversing loop on the torus."""
    theta1 = 2.0 * (np.sin(eta) ** 2) * u
    theta2 = -2.0 * (np.cos(eta) ** 2) * u
    return torus_coordinates(eta, theta1, theta2)


# ── per-torus sweep ──────────────────────────────────────────────

def sweep_loop(name: str, eta: float, loop_label: str, q_fn) -> dict:
    """Sweep a fiber or base loop and collect pointwise pullback values."""
    u_grid = np.linspace(0.0, 2.0 * np.pi, N_SAMPLES, endpoint=False)
    rows = []
    for u in u_grid:
        q = q_fn(eta, float(u))
        pb = pointwise_pullback(q)
        pb["u"] = float(u)
        rows.append(pb)

    i_vals = np.array([r["I_AB"] for r in rows])
    ic_vals = np.array([r["I_c_A_to_B"] for r in rows])

    # Berry phase on the S³ loop
    loop_points = np.array([q_fn(eta, float(u)) for u in u_grid])
    bp = float(berry_phase(loop_points))

    return {
        "torus": name,
        "eta": float(eta),
        "loop": loop_label,
        "n_samples": N_SAMPLES,
        "berry_phase": bp,
        "I_AB_stats": {
            "mean": float(np.mean(i_vals)),
            "std": float(np.std(i_vals)),
            "min": float(np.min(i_vals)),
            "max": float(np.max(i_vals)),
            "range": float(np.max(i_vals) - np.min(i_vals)),
        },
        "I_c_stats": {
            "mean": float(np.mean(ic_vals)),
            "std": float(np.std(ic_vals)),
            "min": float(np.min(ic_vals)),
            "max": float(np.max(ic_vals)),
            "range": float(np.max(ic_vals) - np.min(ic_vals)),
        },
        "rows": rows,
    }


# ── main ─────────────────────────────────────────────────────────

def main() -> int:
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    print("=" * 72)
    print("HOPF POINTWISE PULLBACK PROBE")
    print("=" * 72)

    suites = []
    for torus_name, eta in TORUS_CONFIGS:
        print(f"\n  Torus: {torus_name} (η = {eta:.4f})")
        for loop_label, q_fn in [("fiber", exact_fiber_q), ("base", exact_base_q)]:
            suite = sweep_loop(torus_name, eta, loop_label, q_fn)
            suites.append(suite)
            stats = suite["I_AB_stats"]
            print(
                f"    {loop_label:<5}  "
                f"I(A:B) mean={stats['mean']:.6f}  "
                f"std={stats['std']:.6f}  "
                f"range={stats['range']:.6f}  "
                f"Berry={suite['berry_phase']:.4f}"
            )

    # ── verdicts ──────────────────────────────────────────────────

    fiber_suites = [s for s in suites if s["loop"] == "fiber"]
    base_suites = [s for s in suites if s["loop"] == "base"]

    # Fiber constancy: all fiber loops must have near-zero range
    fiber_ranges = [s["I_AB_stats"]["range"] for s in fiber_suites]
    fiber_ic_ranges = [s["I_c_stats"]["range"] for s in fiber_suites]
    fiber_constant = all(r < 1e-10 for r in fiber_ranges)
    fiber_ic_constant = all(r < 1e-10 for r in fiber_ic_ranges)

    # Base variation: at least one base loop should have nontrivial range
    # For product states on a base loop, I(A:B) = 0 always (product state),
    # but Bloch vectors vary. The key test is whether the Bloch path varies.
    base_bloch_ranges = []
    for s in base_suites:
        blochs = np.array([r["bloch"] for r in s["rows"]])
        bloch_spread = float(np.max(np.std(blochs, axis=0)))
        base_bloch_ranges.append(bloch_spread)

    base_bloch_varies = all(r > 0.01 for r in base_bloch_ranges)

    # Product state reality check: for ρ_L⊗ρ_R, I(A:B) = 0 and I_c = 0
    # This is a guardrail: the pointwise product pullback is trivially zero.
    all_i_ab = [r["I_AB"] for s in suites for r in s["rows"]]
    product_guardrail = all(abs(v) < 1e-10 for v in all_i_ab)

    overall_pass = fiber_constant and fiber_ic_constant and base_bloch_varies and product_guardrail

    verdict = {
        "fiber_I_AB_constant": bool(fiber_constant),
        "fiber_I_c_constant": bool(fiber_ic_constant),
        "fiber_I_AB_ranges": [float(r) for r in fiber_ranges],
        "fiber_I_c_ranges": [float(r) for r in fiber_ic_ranges],
        "base_bloch_varies": bool(base_bloch_varies),
        "base_bloch_spreads": [float(r) for r in base_bloch_ranges],
        "product_guardrail_pass": bool(product_guardrail),
        "result": "PASS" if overall_pass else "KILL",
        "read": (
            "Hopf pointwise pullback confirms structural prediction: "
            "fiber loops yield constant pullback (density-stationary), "
            "base loops yield varying Bloch trajectory (density-traversing). "
            "Product-state I(A:B) and I_c are identically zero as expected — "
            "the pointwise product pullback is honest but trivial, confirming "
            "that a nontrivial bridge construction (not just the product state) "
            "is required for Axis 0."
            if overall_pass
            else "Hopf pointwise pullback probe failed one or more structural checks."
        ),
    }

    token = EvidenceToken(
        token_id="E_SIM_HOPF_POINTWISE_PULLBACK_OK" if overall_pass else "",
        sim_spec_id="S_SIM_HOPF_POINTWISE_PULLBACK",
        status="PASS" if overall_pass else "KILL",
        measured_value=float(
            int(fiber_constant) + int(fiber_ic_constant)
            + int(base_bloch_varies) + int(product_guardrail)
        ),
        kill_reason=None if overall_pass else "STRUCTURAL_CHECK_FAILED",
    )

    results = {
        "metadata": {
            "name": "hopf_pointwise_pullback",
            "timestamp": datetime.now(UTC).isoformat(),
            "results_path": RESULTS_PATH,
            "n_samples_per_loop": N_SAMPLES,
        },
        "suites": [{k: v for k, v in s.items() if k != "rows"} for s in suites],
        "suites_with_rows": suites,
        "verdict": verdict,
        "evidence_token": asdict(token),
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'=' * 72}")
    print("VERDICTS")
    print(f"{'=' * 72}")
    print(f"  Fiber I(A:B) constant:   {fiber_constant}  ranges={[f'{r:.2e}' for r in fiber_ranges]}")
    print(f"  Fiber I_c constant:      {fiber_ic_constant}  ranges={[f'{r:.2e}' for r in fiber_ic_ranges]}")
    print(f"  Base Bloch varies:       {base_bloch_varies}  spreads={[f'{r:.4f}' for r in base_bloch_ranges]}")
    print(f"  Product guardrail:       {product_guardrail}")
    print(f"\n  {verdict['result']}: {verdict['read']}")
    print(f"\nResults saved: {RESULTS_PATH}")

    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
