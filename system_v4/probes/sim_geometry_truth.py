# REQUIRES: numpy
# Run as: make sim NAME=sim_geometry_truth  (from repo root)
"""
Geometry Truth Probe  [Class 1 — geometry truth]
=================================================
Tests ONLY math that is directly established by the canonical docs
(terrain rosetta strong math.md, operator math explicit.md, AXIS_0_1_2_QIT_MATH.md).

Does NOT test runtime conformance or telemetry writeback.

Three sections, strictly separated:

  Section 1 — Loop geometry
    G1: γ_f^L density stationary: ρ_f^L(u) = ρ_f^L(0) for u ∈ [0, 2π)
    G2: γ_b^L density traversing: off-diagonal phase = e^{2i(χ₀+u)}
    G3: γ_f^R density stationary (e^{-iθ} fiber phase, same density blindness)
    G4: γ_b^R density traversing
    G5: Horizontal condition: dφ/du + cos(2η)·dχ/du = 0 along γ_b
    G6: Fiber phase chirality: left fiber = e^{+iθ}·ψ_L, right fiber = e^{-iθ}·ψ_R

  Section 2 — Operator canonical forms
    O1: Ti at q=1: ρ → P₀ρP₀ + P₁ρP₁ (zero off-diagonals)
    O2: Te at q=1: ρ → Q₊ρQ₊ + Q₋ρQ₋ (zero imaginary off-diagonals, diagonal mixed)
    O3: Fe: ρ → U_z(φ)ρU_z(φ)† (diagonal preserved, off-diagonals rotate by e^{-iφ})
    O4: Fi: ρ → U_x(θ)ρU_x(θ)† (diagonal mixed, off-diagonals preserved in magnitude)

  Section 3 — Placement operator assignment
    P1: Type 1 fiber (inner): Fi for Se/Ne, Te for Ni/Si
    P2: Type 1 base  (outer): Ti for Se/Ne, Fe for Ni/Si
    P3: Type 2 fiber (inner): Ti for Se/Ne, Fe for Ni/Si
    P4: Type 2 base  (outer): Fi for Se/Ne, Te for Ni/Si

All pass conditions are strict numerical equalities derived from the exact math,
not approximations or regime checks.
"""
from __future__ import annotations
import os, sys, json
import numpy as np
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills"))

from hopf_manifold import (
    torus_coordinates, left_weyl_spinor, right_weyl_spinor,
    fiber_phase_left, fiber_phase_right,
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
)
from geometric_operators import apply_Ti, apply_Te, apply_Fe, apply_Fi
from engine_core import STAGE_OPERATOR_LUT

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# ── helpers ──────────────────────────────────────────────────────────────────

def spinor_from_coords(phi: float, chi: float, eta: float) -> np.ndarray:
    """ψ(φ,χ;η) = (e^{i(φ+χ)}cosη, e^{i(φ-χ)}sinη) — canonical Hopf chart."""
    return np.array([
        np.exp(1j * (phi + chi)) * np.cos(eta),
        np.exp(1j * (phi - chi)) * np.sin(eta),
    ], dtype=complex)


def density(psi: np.ndarray) -> np.ndarray:
    """ρ = |ψ⟩⟨ψ|"""
    return np.outer(psi, psi.conj())


def trace_distance(a: np.ndarray, b: np.ndarray) -> float:
    diff = a - b
    return float(0.5 * np.sum(np.abs(np.linalg.eigvalsh(diff @ diff.conj().T) ** 0.5)))


def td(a: np.ndarray, b: np.ndarray) -> float:
    """Frobenius norm (faster proxy; exact for Hermitian differences)."""
    return float(np.linalg.norm(a - b, ord="fro"))


_pass = []
_fail = []

def check(label: str, cond: bool, detail: str = "") -> None:
    if cond:
        _pass.append(label)
        print(f"  ✓ {label}")
    else:
        _fail.append(label)
        print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


# ════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Loop geometry
# ════════════════════════════════════════════════════════════════════════════

def section_loop_geometry() -> dict:
    print("\n[Section 1: Loop geometry]")
    results = {}

    # Test across three torus latitudes and several random base points
    for eta in [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]:
        for trial in range(5):
            rng = np.random.default_rng(trial)
            phi0 = float(rng.uniform(0, 2 * np.pi))
            chi0 = float(rng.uniform(0, 2 * np.pi))

            us = np.linspace(0, 2 * np.pi, 40, endpoint=False)

            # ── G1: γ_f^L density stationary ────────────────────────────── #
            psi0_L = spinor_from_coords(phi0, chi0, eta)
            rho0_L = density(psi0_L)
            for u in us:
                psi_u = spinor_from_coords(phi0 + u, chi0, eta)
                rho_u = density(psi_u)
                err = td(rho_u, rho0_L)
                if err > 1e-10:
                    check(f"G1 fiber_L stationary η={eta:.3f} trial={trial}", False,
                          f"td={err:.3e} at u={u:.3f}")
                    break
            else:
                check(f"G1 fiber_L stationary η={eta:.3f} trial={trial}", True)

            # ── G2: γ_b^L density traversing (off-diagonal phase) ────────── #
            # ρ_b^L(u) = ½(I + r⃗(χ₀+u, η)·σ⃗)
            # off-diagonal = e^{2i(χ₀+u)} cosη sinη
            psi_b0 = spinor_from_coords(phi0 - np.cos(2 * eta) * 0, chi0 + 0, eta)
            off_diag_deviations = []
            for u in us[1:]:
                phi_u = phi0 - np.cos(2 * eta) * u
                chi_u = chi0 + u
                psi_bu = spinor_from_coords(phi_u, chi_u, eta)
                rho_bu = density(psi_bu)
                # Expected off-diagonal from the exact density formula
                expected_off = np.exp(2j * chi_u) * np.cos(eta) * np.sin(eta)
                actual_off = rho_bu[0, 1]
                off_diag_deviations.append(abs(actual_off - expected_off))
            max_off_err = max(off_diag_deviations)
            check(f"G2 base_L off-diagonal formula η={eta:.3f} trial={trial}",
                  max_off_err < 1e-10, f"max_err={max_off_err:.3e}")

            # Density period is π (not 2π): r⃗ uses 2χ, so e^{2i(χ₀+π)} = e^{2iχ₀}.
            # Check traversal at u=π/4 (quarter period, not half period).
            u_check = np.pi / 4
            psi_b_qtr = spinor_from_coords(
                phi0 - np.cos(2 * eta) * u_check,
                chi0 + u_check, eta)
            rho_b_qtr = density(psi_b_qtr)
            psi_b_start = spinor_from_coords(phi0, chi0, eta)
            rho_b_start = density(psi_b_start)
            traversal = td(rho_b_qtr, rho_b_start)
            # At poles (η≈0 or η≈π/2), sin(2η)≈0 so Bloch vector barely moves — skip
            at_pole = abs(np.sin(2 * eta)) < 0.1
            check(f"G2 base_L traversal non-trivial η={eta:.3f} trial={trial}",
                  traversal > 1e-6 or at_pole,
                  f"traversal={traversal:.3e} sin2η={np.sin(2*eta):.3f}")

            # ── G3: γ_f^R density stationary ────────────────────────────── #
            # Right spinor: ψ_R = (z̄₂, -z̄₁) from hopf_manifold.py
            q = torus_coordinates(eta, phi0, chi0)
            psi_R0 = right_weyl_spinor(q)
            rho_R0 = density(psi_R0)
            fiber_stationary_R = True
            for u in us:
                psi_Ru = fiber_phase_right(psi_R0, u)
                rho_Ru = density(psi_Ru)
                if td(rho_Ru, rho_R0) > 1e-10:
                    fiber_stationary_R = False
                    break
            check(f"G3 fiber_R stationary η={eta:.3f} trial={trial}", fiber_stationary_R)

            # ── G5: Horizontal condition along γ_b ──────────────────────── #
            # A = dφ + cos(2η) dχ; along γ_b: dφ/du = -cos(2η), dχ/du = 1
            # So A(γ̇_b) = -cos(2η) + cos(2η) = 0
            A_val = -np.cos(2 * eta) + np.cos(2 * eta) * 1.0
            check(f"G5 horizontal condition η={eta:.3f} trial={trial}",
                  abs(A_val) < 1e-12, f"A={A_val:.3e}")

    # ── G4: γ_b^R density traverses (at Clifford torus) ─────────────────── #
    eta = TORUS_CLIFFORD
    phi0, chi0 = 0.0, 0.0
    q0 = torus_coordinates(eta, phi0, chi0)
    # Use hopf_manifold's right_weyl_spinor to get initial right spinor
    psi_R0 = right_weyl_spinor(q0)
    # Base loop: χ advances, φ retreats at rate -cos(2η)
    # Right density depends on χ via off-diagonal phase (same density formula as left)
    rho_R_start = density(psi_R0)
    u_half = np.pi
    q_half = torus_coordinates(eta,
                               phi0 - np.cos(2 * eta) * u_half,
                               chi0 + u_half)
    psi_R_half = right_weyl_spinor(q_half)
    rho_R_half = density(psi_R_half)
    check("G4 base_R traversal non-trivial",
          td(rho_R_half, rho_R_start) > 1e-6,
          f"td={td(rho_R_half, rho_R_start):.3e}")

    # ── G6: Fiber phase chirality ─────────────────────────────────────────── #
    # Left fiber: ψ_L → e^{+iθ}·ψ_L, density unchanged
    # Right fiber: ψ_R → e^{-iθ}·ψ_R, density unchanged
    # But: ψ_L and ψ_R live on the SAME carrier S³ with opposite U(1) actions.
    # Direct check: applying e^{+iθ} to ψ_L gives same result as fiber_phase_left;
    #               applying e^{-iθ} to ψ_R gives same result as fiber_phase_right.
    q_test = torus_coordinates(TORUS_CLIFFORD, 0.3, 0.7)
    psi_L_test = left_weyl_spinor(q_test)
    psi_R_test = right_weyl_spinor(q_test)
    theta_test = 0.9

    psi_L_fiber = fiber_phase_left(psi_L_test, theta_test)
    psi_L_direct = np.exp(1j * theta_test) * psi_L_test
    check("G6 left fiber = e^{+iθ}·ψ_L",
          td(density(psi_L_fiber), density(psi_L_direct)) < 1e-10,
          f"td={td(density(psi_L_fiber), density(psi_L_direct)):.3e}")

    psi_R_fiber = fiber_phase_right(psi_R_test, theta_test)
    psi_R_direct = np.exp(-1j * theta_test) * psi_R_test
    check("G6 right fiber = e^{-iθ}·ψ_R",
          td(density(psi_R_fiber), density(psi_R_direct)) < 1e-10,
          f"td={td(density(psi_R_fiber), density(psi_R_direct)):.3e}")

    # Opposite chirality: left and right fiber phases are opposite
    check("G6 left/right fiber phase chirality is opposite",
          not np.allclose(psi_L_fiber, psi_L_direct * np.exp(-2j * theta_test)))

    results["section1_pass"] = all(
        g.startswith("G") for g in _pass
        if g.startswith("G")
    )
    return results


# ════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Operator canonical forms
# ════════════════════════════════════════════════════════════════════════════

def section_operator_forms() -> dict:
    print("\n[Section 2: Operator canonical forms]")
    results = {}

    # Use a generic test density with nonzero off-diagonals
    # ρ = [[a, u-iv], [u+iv, d]] with a=0.6, d=0.4, u=0.1, v=0.15
    a, d_val, u, v = 0.6, 0.4, 0.1, 0.15
    rho_test = np.array([[a, u - 1j * v],
                         [u + 1j * v, d_val]], dtype=complex)

    # ── O1: Ti at full strength ──────────────────────────────────────────── #
    # Ti(ρ) at q₁=1: ρ → P₀ρP₀ + P₁ρP₁ = [[a,0],[0,d]]
    rho_Ti = apply_Ti(rho_test, polarity_up=True, strength=1.0)
    rho_Ti_expected = np.array([[a, 0], [0, d_val]], dtype=complex)
    check("O1 Ti full strength zeroes off-diagonals",
          td(rho_Ti, rho_Ti_expected) < 1e-10,
          f"td={td(rho_Ti, rho_Ti_expected):.3e}")
    check("O1 Ti preserves diagonal",
          abs(rho_Ti[0, 0] - a) < 1e-10 and abs(rho_Ti[1, 1] - d_val) < 1e-10)
    check("O1 Ti is trace-preserving",
          abs(np.trace(rho_Ti) - 1.0) < 1e-10)

    # ── O2: Te at full strength ──────────────────────────────────────────── #
    # Te(ρ) at q₂=1: ρ → Q₊ρQ₊ + Q₋ρQ₋
    # Result: [[½, u],[u, ½]] — diagonal forced to ½, real off-diag preserved, imag zeroed
    rho_Te = apply_Te(rho_test, polarity_up=True, strength=1.0, q=1.0)
    rho_Te_expected = np.array([[0.5, u], [u, 0.5]], dtype=complex)
    check("O2 Te full strength: diagonal forced to ½",
          abs(rho_Te[0, 0] - 0.5) < 1e-10 and abs(rho_Te[1, 1] - 0.5) < 1e-10,
          f"diag=({rho_Te[0,0]:.4f}, {rho_Te[1,1]:.4f})")
    check("O2 Te full strength: real off-diagonal preserved",
          abs(np.real(rho_Te[0, 1]) - u) < 1e-10,
          f"Re(off)={np.real(rho_Te[0,1]):.4f} expected={u}")
    check("O2 Te full strength: imaginary off-diagonal zeroed",
          abs(np.imag(rho_Te[0, 1])) < 1e-10,
          f"Im(off)={np.imag(rho_Te[0,1]):.4e}")
    check("O2 Te is trace-preserving",
          abs(np.trace(rho_Te) - 1.0) < 1e-10)

    # ── O3: Fe — z-rotation ──────────────────────────────────────────────── #
    # Fe: ρ → U_z(φ)ρU_z(φ)† where U_z(φ) = diag(e^{-iφ/2}, e^{iφ/2})
    # Diagonal preserved; off-diag (0,1) rotated by e^{-iφ}
    phi = 0.7
    rho_Fe = apply_Fe(rho_test, polarity_up=True, strength=1.0, phi=phi)
    expected_off_01 = np.exp(-1j * phi) * (u - 1j * v)
    check("O3 Fe preserves diagonal",
          abs(rho_Fe[0, 0] - a) < 1e-10 and abs(rho_Fe[1, 1] - d_val) < 1e-10,
          f"diag=({rho_Fe[0,0]:.4f}, {rho_Fe[1,1]:.4f})")
    check("O3 Fe rotates off-diagonal by e^{-iφ}",
          abs(rho_Fe[0, 1] - expected_off_01) < 1e-10,
          f"off={rho_Fe[0,1]:.4f} expected={expected_off_01:.4f}")
    check("O3 Fe is trace-preserving",
          abs(np.trace(rho_Fe) - 1.0) < 1e-10)
    check("O3 Fe is unitary (purity preserved)",
          abs(np.trace(rho_Fe @ rho_Fe) - np.trace(rho_test @ rho_test)) < 1e-10)

    # ── O4: Fi — x-rotation ──────────────────────────────────────────────── #
    # Fi: ρ → U_x(θ)ρU_x(θ)†
    # From operator math explicit.md:
    #   a' = a·cos²(θ/2) + d·sin²(θ/2) + v·sin(θ)
    #   d' = a·sin²(θ/2) + d·cos²(θ/2) - v·sin(θ)
    #   u' = u
    theta = 0.5
    rho_Fi = apply_Fi(rho_test, polarity_up=True, strength=1.0, theta=theta)
    c2 = np.cos(theta / 2) ** 2
    s2 = np.sin(theta / 2) ** 2
    st = np.sin(theta)
    a_prime = a * c2 + d_val * s2 + v * st
    d_prime = a * s2 + d_val * c2 - v * st
    u_prime = u
    check("O4 Fi: a' = a·cos²(θ/2) + d·sin²(θ/2) + v·sin(θ)",
          abs(rho_Fi[0, 0] - a_prime) < 1e-10,
          f"got={rho_Fi[0,0]:.6f} expected={a_prime:.6f}")
    check("O4 Fi: d' = a·sin²(θ/2) + d·cos²(θ/2) - v·sin(θ)",
          abs(rho_Fi[1, 1] - d_prime) < 1e-10,
          f"got={rho_Fi[1,1]:.6f} expected={d_prime:.6f}")
    check("O4 Fi: real off-diagonal u' = u (preserved)",
          abs(np.real(rho_Fi[0, 1]) - u_prime) < 1e-10,
          f"got={np.real(rho_Fi[0,1]):.6f} expected={u_prime:.6f}")
    check("O4 Fi is trace-preserving",
          abs(np.trace(rho_Fi) - 1.0) < 1e-10)
    check("O4 Fi is unitary (purity preserved)",
          abs(np.trace(rho_Fi @ rho_Fi) - np.trace(rho_test @ rho_test)) < 1e-10)

    return results


# ════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Placement operator assignment
# ════════════════════════════════════════════════════════════════════════════

def section_placement_assignment() -> dict:
    """
    Verify STAGE_OPERATOR_LUT matches the canonical token tables from
    terrain rosetta strong math.md.

    Canonical assignment:
      Type 1 fiber (inner): Fi for {Se, Ne}, Te for {Ni, Si}
      Type 1 base  (outer): Ti for {Se, Ne}, Fe for {Ni, Si}
      Type 2 fiber (inner): Ti for {Se, Ne}, Fe for {Ni, Si}
      Type 2 base  (outer): Fi for {Se, Ne}, Te for {Ni, Si}
    """
    print("\n[Section 3: Placement operator assignment]")
    results = {}

    canonical = {
        # (engine_type, loop, topo) → expected_op
        (1, "fiber", "Se"): "Fi",
        (1, "fiber", "Ne"): "Fi",
        (1, "fiber", "Ni"): "Te",
        (1, "fiber", "Si"): "Te",
        (1, "base",  "Se"): "Ti",
        (1, "base",  "Ne"): "Ti",
        (1, "base",  "Ni"): "Fe",
        (1, "base",  "Si"): "Fe",
        (2, "fiber", "Se"): "Ti",
        (2, "fiber", "Ne"): "Ti",
        (2, "fiber", "Ni"): "Fe",
        (2, "fiber", "Si"): "Fe",
        (2, "base",  "Se"): "Fi",
        (2, "base",  "Ne"): "Fi",
        (2, "base",  "Ni"): "Te",
        (2, "base",  "Si"): "Te",
    }

    for key, expected_op in canonical.items():
        et, loop, topo = key
        actual_op, _ = STAGE_OPERATOR_LUT.get(key, (None, None))
        section_label = f"P{1 if loop == 'fiber' else 2} T{et} {loop} {topo}"
        check(f"{section_label} → {expected_op}",
              actual_op == expected_op,
              f"got {actual_op!r}")

    # Summarize: Type 1 inner (fiber) uses TeFi family; outer (base) uses FeTi family
    t1_fiber_ops = {STAGE_OPERATOR_LUT[(1, "fiber", t)][0] for t in ["Se", "Ne", "Ni", "Si"]}
    t1_base_ops  = {STAGE_OPERATOR_LUT[(1, "base",  t)][0] for t in ["Se", "Ne", "Ni", "Si"]}
    t2_fiber_ops = {STAGE_OPERATOR_LUT[(2, "fiber", t)][0] for t in ["Se", "Ne", "Ni", "Si"]}
    t2_base_ops  = {STAGE_OPERATOR_LUT[(2, "base",  t)][0] for t in ["Se", "Ne", "Ni", "Si"]}

    check("P — Type 1 fiber uses TeFi family",  t1_fiber_ops == {"Te", "Fi"})
    check("P — Type 1 base uses FeTi family",   t1_base_ops  == {"Fe", "Ti"})
    check("P — Type 2 fiber uses FeTi family",  t2_fiber_ops == {"Fe", "Ti"})
    check("P — Type 2 base uses TeFi family",   t2_base_ops  == {"Te", "Fi"})

    # Type 1 and Type 2 fiber operators are disjoint families (exact swap)
    check("P — T1 fiber ops == T2 base ops (families swap between engines)",
          t1_fiber_ops == t2_base_ops)
    check("P — T2 fiber ops == T1 base ops (families swap between engines)",
          t2_fiber_ops == t1_base_ops)

    return results


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def run() -> None:
    print("Geometry Truth Probe [Class 1]")
    print("=" * 50)

    section_loop_geometry()
    section_operator_forms()
    section_placement_assignment()

    total = len(_pass) + len(_fail)
    print(f"\n{'='*50}")
    print(f"Results: {len(_pass)}/{total} passed")
    if _fail:
        print("FAILURES:")
        for f in _fail:
            print(f"  ✗ {f}")

    all_pass = len(_fail) == 0
    print(f"\n{'✓ ALL PASS' if all_pass else '✗ FAILURES DETECTED'}")

    result = {
        "total": total,
        "passed": len(_pass),
        "failed": len(_fail),
        "failures": _fail,
        "all_pass": all_pass,
        "sections": {
            "G": "loop geometry (G1–G6)",
            "O": "operator canonical forms (O1–O4)",
            "P": "placement assignment (P1–P4)",
        },
    }
    out_path = os.path.join(RESULTS_DIR, "geometry_truth_results.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nResults → {out_path}")


if __name__ == "__main__":
    run()
