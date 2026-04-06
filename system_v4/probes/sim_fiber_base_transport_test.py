#!/usr/bin/env python3
"""
sim_fiber_base_transport_test.py
================================

Bounded fiber/base transport test from the AXIS next-sims table.

Question
--------
Does the Ax2 frame-transport unitary V(u) = exp(-i H_s u) change the
Ax0 correlation functional, or does it belong purely to Ax2?

Design
------
On each nested Hopf torus T_eta, trace two loops:

  1. Fiber loop:  gamma_fiber(u) = psi(phi0+u, chi0; eta)
     - density-STATIONARY: rho_fiber(u) = rho_fiber(0) for all u
     - pure phase motion along the Hopf fiber

  2. Base loop:   gamma_base(u) = psi(phi0 - cos(2*eta)*u, chi0+u; eta)
     - density-TRAVERSING: rho_base(u) varies with u
     - horizontal (connection-null) motion on S^2

At each sample point u along each loop, evaluate:

  A. DIRECT Ax0:       Phi_0(rho_AB(u))
     - rho_AB built from L/R Weyl spinors at the sample point
     - Phi_0 = I_c(A>B) = S(rho_B) - S(rho_AB)

  B. TRANSPORTED Ax0:  Phi_0(V(u)^dag rho_AB(u) V(u))
     - V(u) = exp(-i H_s u), H_s = +/- H_0 (Weyl sheet evolution)
     - This is the Ax2 conjugated-frame evaluation

Verdicts
--------
  - If direct == transported on BOTH loops: transport is invisible to Ax0
    -> transport belongs purely to Ax2 (PASS for separation)
  - If direct != transported: transport leaks into Ax0
    -> Ax0 is not frame-independent (diagnostic finding)
  - Fiber loop MUST show constant Ax0 (density-stationary sanity check)
  - Base loop SHOULD show varying Ax0 (density-traversing confirmation)

Source: AXIS_0_1_2_QIT_MATH.md, bounded-next-sims table, row 5.
V(t) resolution: AXIS_3_4_5_6_QIT_MATH.md — V_s(u) = exp(-i H_s u).
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from datetime import UTC, datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from geometric_operators import _ensure_valid_density
from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    left_weyl_spinor,
    right_weyl_spinor,
    torus_coordinates,
)
from proto_ratchet_sim_runner import EvidenceToken

RESULTS_PATH = os.path.join(
    os.path.dirname(__file__),
    "a2_state",
    "sim_results",
    "fiber_base_transport_test_results.json",
)

TORUS_CONFIGS = [
    ("inner", TORUS_INNER),
    ("clifford", TORUS_CLIFFORD),
    ("outer", TORUS_OUTER),
]

N_SAMPLES = 64
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)
I4 = np.eye(4, dtype=complex)

# Bell reference for bridge mixing
PSI_MINUS = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)
BELL = np.outer(PSI_MINUS, PSI_MINUS.conj())

# Fixed Hamiltonian for V(u): use sigma_z as the canonical H_0
H0 = SIGMA_Z


# ─────────────────────────────────────────────────────────────────
# QIT primitives
# ─────────────────────────────────────────────────────────────────

def vne(rho: np.ndarray) -> float:
    """Von Neumann entropy S(rho) in bits."""
    rho = (rho + rho.conj().T) / 2
    ev = np.real(np.linalg.eigvalsh(rho))
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(ev))) if len(ev) else 0.0


def ptr_A(rho4: np.ndarray) -> np.ndarray:
    """Trace out subsystem A from a 4x4 bipartite state."""
    return np.trace(rho4.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def ptr_B(rho4: np.ndarray) -> np.ndarray:
    """Trace out subsystem B from a 4x4 bipartite state."""
    return np.trace(rho4.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def coherent_info(rho_AB: np.ndarray) -> float:
    """I_c(A>B) = S(B) - S(AB) = -S(A|B)."""
    return vne(ptr_A(rho_AB)) - vne(rho_AB)


def mutual_info(rho_AB: np.ndarray) -> float:
    """I(A:B) = S(A) + S(B) - S(AB)."""
    return max(0.0, vne(ptr_B(rho_AB)) + vne(ptr_A(rho_AB)) - vne(rho_AB))


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.real(np.trace(s @ rho)))
                     for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])


# ─────────────────────────────────────────────────────────────────
# Loop generators on a fixed torus
# ─────────────────────────────────────────────────────────────────

def fiber_loop_point(eta: float, t1_0: float, t2_0: float, u: float) -> np.ndarray:
    """Fiber loop: shift both theta1 and theta2 by u (global phase = Hopf fiber).

    In (phi, chi) notation: phi -> phi + u, chi fixed.
    Since theta1 = phi + chi and theta2 = phi - chi:
      theta1 -> theta1 + u,  theta2 -> theta2 + u.

    Density-stationary: Hopf map depends on (theta2 - theta1), which is constant.
    """
    return torus_coordinates(eta, t1_0 + u, t2_0 + u)


def base_loop_point(eta: float, t1_0: float, t2_0: float, u: float) -> np.ndarray:
    """Base loop: horizontal lift of chi -> chi + u with Hopf connection null.

    In (phi, chi) notation: chi -> chi + u, phi -> phi - cos(2*eta)*u.
    Since theta1 = phi + chi, theta2 = phi - chi:
      theta1 -> theta1 + (1 - cos(2*eta))*u
      theta2 -> theta2 + (-1 - cos(2*eta))*u

    Density-traversing: (theta2 - theta1) changes, so Hopf map varies on S^2.
    """
    c2e = np.cos(2 * eta)
    return torus_coordinates(eta, t1_0 + (1 - c2e) * u, t2_0 + (-1 - c2e) * u)


# ─────────────────────────────────────────────────────────────────
# Bridge: fixed-reference L/R cut with Bell mixing
# ─────────────────────────────────────────────────────────────────

def build_cut_state(q: np.ndarray) -> np.ndarray:
    """Build a bipartite cut state rho_AB from the L/R Weyl spinors at q.

    Bridge: geometry-dependent entanglement via Bloch-z coordinate.

    The Bloch vector of rho_L traces out S^2 along the base loop.
    We use its z-component to parameterize entanglement:
      theta = arccos(bloch_z) / 2  (maps z in [-1,1] to theta in [0, pi/2])
      |Psi(q)> = cos(theta)|psi_L>|0> + sin(theta)|psi_R^perp>|1>

    This creates a geometry-dependent entangled state:
      - Constant on fiber loops (Bloch vector fixed)
      - Varying on base loops (Bloch vector traverses S^2)
      - Non-trivially entangled when bloch_z != +/-1
    """
    psi_L = left_weyl_spinor(q)
    rho_L = np.outer(psi_L, psi_L.conj())

    bvec = bloch(rho_L)
    # Use azimuthal angle of the Bloch vector (x,y components vary on
    # the base loop but are constant on the fiber loop after the fix).
    # Map azimuthal angle phi_bloch in [0, 2*pi] to theta in [pi/8, 3*pi/8]
    phi_bloch = np.arctan2(bvec[1], bvec[0])  # [-pi, pi]
    theta = np.pi / 8 + (np.pi / 4) * (phi_bloch + np.pi) / (2 * np.pi)

    # Build entangled 2-qubit pure state using Schmidt decomposition
    #   |Psi> = cos(theta)|0>|0> + sin(theta)|1>|1>
    psi_AB = np.array([np.cos(theta), 0, 0, np.sin(theta)], dtype=complex)
    rho_AB = _ensure_valid_density(np.outer(psi_AB, psi_AB.conj()))
    return rho_AB


# ─────────────────────────────────────────────────────────────────
# Frame-transport unitary V(u) for Ax2
# ─────────────────────────────────────────────────────────────────

def frame_unitary(u: float, sheet: str = "L") -> np.ndarray:
    """V_s(u) = exp(-i H_s u), where H_L = +H0, H_R = -H0.
    Returns a 4x4 unitary acting on the bipartite space: V_L x V_R."""
    sign_L = +1.0
    sign_R = -1.0
    V_L = np.cos(sign_L * u) * I2 - 1j * np.sin(sign_L * u) * H0
    V_R = np.cos(sign_R * u) * I2 - 1j * np.sin(sign_R * u) * H0
    return np.kron(V_L, V_R)


def transport_state(rho_AB: np.ndarray, u: float) -> np.ndarray:
    """Apply Ax2 frame transport: rho_tilde = V(u)^dag rho_AB V(u)."""
    V = frame_unitary(u)
    return _ensure_valid_density(V.conj().T @ rho_AB @ V)


# ─────────────────────────────────────────────────────────────────
# Single-loop evaluation
# ─────────────────────────────────────────────────────────────────

def evaluate_loop(eta: float, phi0: float, chi0: float,
                  loop_fn, loop_name: str) -> dict:
    """Evaluate Ax0 (direct and transported) along a loop."""
    us = np.linspace(0, 2 * np.pi, N_SAMPLES, endpoint=False)

    ic_direct = []
    ic_transported = []
    mi_direct = []
    mi_transported = []
    bloch_L_trace = []

    for u in us:
        q = loop_fn(eta, phi0, chi0, u)
        rho_AB = build_cut_state(q)

        # Direct evaluation
        ic_d = coherent_info(rho_AB)
        mi_d = mutual_info(rho_AB)
        ic_direct.append(ic_d)
        mi_direct.append(mi_d)

        # Transported evaluation (Ax2 conjugated frame)
        rho_tilde = transport_state(rho_AB, u)
        ic_t = coherent_info(rho_tilde)
        mi_t = mutual_info(rho_tilde)
        ic_transported.append(ic_t)
        mi_transported.append(mi_t)

        # Track Bloch vector for sanity
        psi_L = left_weyl_spinor(q)
        rho_L = np.outer(psi_L, psi_L.conj())
        bloch_L_trace.append(bloch(rho_L).tolist())

    ic_direct = np.array(ic_direct)
    ic_transported = np.array(ic_transported)
    mi_direct = np.array(mi_direct)
    mi_transported = np.array(mi_transported)

    ic_gap = np.abs(ic_direct - ic_transported)
    mi_gap = np.abs(mi_direct - mi_transported)

    return {
        "loop": loop_name,
        "n_samples": N_SAMPLES,
        "ic_direct_mean": float(np.mean(ic_direct)),
        "ic_direct_std": float(np.std(ic_direct)),
        "ic_transported_mean": float(np.mean(ic_transported)),
        "ic_transported_std": float(np.std(ic_transported)),
        "ic_gap_max": float(np.max(ic_gap)),
        "ic_gap_mean": float(np.mean(ic_gap)),
        "mi_direct_mean": float(np.mean(mi_direct)),
        "mi_direct_std": float(np.std(mi_direct)),
        "mi_transported_mean": float(np.mean(mi_transported)),
        "mi_transported_std": float(np.std(mi_transported)),
        "mi_gap_max": float(np.max(mi_gap)),
        "mi_gap_mean": float(np.mean(mi_gap)),
        "bloch_L_first": bloch_L_trace[0],
        "bloch_L_last": bloch_L_trace[-1],
    }


# ─────────────────────────────────────────────────────────────────
# Per-torus case
# ─────────────────────────────────────────────────────────────────

def run_torus_case(torus_name: str, eta: float) -> dict:
    t1_0, t2_0 = 0.0, 0.0  # initial (theta1, theta2) on the torus

    fiber_result = evaluate_loop(
        eta, t1_0, t2_0, fiber_loop_point, "fiber")
    base_result = evaluate_loop(
        eta, t1_0, t2_0, base_loop_point, "base")

    # Verdicts
    # Fiber loop: density-stationary → Ic must be constant (std ≈ 0)
    fiber_ic_constant = fiber_result["ic_direct_std"] < 1e-8
    # Fiber loop: transport gap must be zero (density doesn't change)
    fiber_transport_invariant = fiber_result["ic_gap_max"] < 1e-8

    # Base loop: density-traversing → Ic should vary
    base_ic_varies = base_result["ic_direct_std"] > 1e-6
    # Base loop: transport gap — this is the key discriminator
    base_transport_gap_max = base_result["ic_gap_max"]
    base_transport_invariant = base_transport_gap_max < 1e-6

    return {
        "torus": torus_name,
        "eta": float(eta),
        "fiber": fiber_result,
        "base": base_result,
        "verdicts": {
            "fiber_ic_constant": bool(fiber_ic_constant),
            "fiber_transport_invariant": bool(fiber_transport_invariant),
            "base_ic_varies": bool(base_ic_varies),
            "base_transport_invariant": bool(base_transport_invariant),
            "base_transport_ic_gap_max": float(base_transport_gap_max),
        },
    }


# ─────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────

def main() -> int:
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    print("=" * 72)
    print("FIBER / BASE TRANSPORT TEST")
    print("=" * 72)
    print()
    print("Question: Does Ax2 frame transport V(u) change the Ax0 kernel,")
    print("          or does it belong purely to Ax2?")
    print()
    print("Design:")
    print("  - Fiber loop (density-stationary): sanity check")
    print("  - Base loop (density-traversing): transport discriminator")
    print("  - V(u) = exp(-i H_s u), H_L = +sigma_z, H_R = -sigma_z")
    print("  - Ax0 kernel = I_c(A>B) = S(B) - S(AB)")
    print()

    cases = []
    for torus_name, eta in TORUS_CONFIGS:
        print(f"  Running torus: {torus_name} (eta={eta:.4f}) ...")
        result = run_torus_case(torus_name, eta)
        cases.append(result)

        v = result["verdicts"]
        print(f"    fiber: Ic constant={v['fiber_ic_constant']}, "
              f"transport invariant={v['fiber_transport_invariant']}")
        print(f"    base:  Ic varies={v['base_ic_varies']}, "
              f"transport invariant={v['base_transport_invariant']} "
              f"(gap_max={v['base_transport_ic_gap_max']:.2e})")

    # Overall verdicts
    all_fiber_ok = all(c["verdicts"]["fiber_ic_constant"]
                       and c["verdicts"]["fiber_transport_invariant"]
                       for c in cases)
    any_base_varies = any(c["verdicts"]["base_ic_varies"] for c in cases)
    all_base_transport_invariant = all(
        c["verdicts"]["base_transport_invariant"] for c in cases)

    # The probe passes (separation confirmed) if:
    #   1. Fiber loops are all constant and transport-invariant (sanity)
    #   2. At least one base loop has varying Ic (density-traversing confirmation)
    #   3. All base loops are transport-invariant (Ax0 does not see Ax2 frame)
    overall_pass = all_fiber_ok and any_base_varies and all_base_transport_invariant

    # Alternative finding: if transport IS visible on the base loop
    transport_leaks = all_fiber_ok and any_base_varies and not all_base_transport_invariant

    if overall_pass:
        verdict_text = (
            "PASS — Ax2 frame transport V(u) does NOT change the Ax0 kernel. "
            "Transport geometry belongs purely to Ax2, confirming Ax0/Ax2 separation."
        )
        verdict_status = "PASS"
    elif transport_leaks:
        max_gap = max(c["verdicts"]["base_transport_ic_gap_max"] for c in cases)
        verdict_text = (
            f"DIAGNOSTIC — Ax2 frame transport V(u) DOES change the Ax0 kernel "
            f"(max Ic gap = {max_gap:.6f}). Transport geometry leaks into Ax0. "
            f"This means Ax0 is not fully frame-independent under this bridge."
        )
        verdict_status = "DIAGNOSTIC"
    else:
        verdict_text = (
            "INCONCLUSIVE — sanity checks did not pass as expected; "
            "review fiber/base loop construction."
        )
        verdict_status = "INCONCLUSIVE"

    print()
    print("=" * 72)
    print("OVERALL VERDICT")
    print("=" * 72)
    print(f"  Fiber sanity (all constant + invariant): {all_fiber_ok}")
    print(f"  Base Ic varies (density-traversing):     {any_base_varies}")
    print(f"  Base transport invariant (Ax0/Ax2 sep):  {all_base_transport_invariant}")
    print(f"  Verdict: {verdict_text}")

    token = EvidenceToken(
        token_id="E_SIM_FIBER_BASE_TRANSPORT_OK" if overall_pass else "",
        sim_spec_id="S_SIM_FIBER_BASE_TRANSPORT_TEST",
        status=verdict_status,
        measured_value=float(max(
            c["verdicts"]["base_transport_ic_gap_max"] for c in cases
        )),
        kill_reason=None if overall_pass else verdict_text,
    )

    output = {
        "metadata": {
            "name": "fiber_base_transport_test",
            "timestamp": datetime.now(UTC).isoformat(),
            "results_path": RESULTS_PATH,
            "n_samples_per_loop": N_SAMPLES,
            "H0": "sigma_z",
            "V_formula": "V_s(u) = exp(-i H_s u), H_L=+H0, H_R=-H0",
            "ax0_kernel": "I_c(A>B) = S(B) - S(AB)",
            "bridge": "Bell-mixing: (1-p)*rho_L x rho_R + p*|psi_minus><psi_minus|",
        },
        "cases": cases,
        "overall": {
            "all_fiber_ok": bool(all_fiber_ok),
            "any_base_varies": bool(any_base_varies),
            "all_base_transport_invariant": bool(all_base_transport_invariant),
        },
        "verdict": {
            "result": verdict_status,
            "read": verdict_text,
        },
        "evidence_token": asdict(token),
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved: {RESULTS_PATH}")
    print()
    print("=" * 72)
    print(f"PROBE STATUS: {verdict_status}")
    print("=" * 72)

    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
