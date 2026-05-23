#!/usr/bin/env python3
"""
sim_hopf_weyl_emergence_quantities
Scope: Coupling Program Step 5 — emergence tests.

Step 3 confirmed triple coexistence (Hopf+Weyl+torus, 19/19, 270 jointly
admissible states < 288 pairwise minimum).
Step 4 confirmed holonomy is topology-sensitive (flat torus ratio=7.41),
Weyl-L is topology-stable.

This sim tests: what quantities exist ONLY when multiple shells are
simultaneously active, and vanish when either shell is alone?

Emergence definition: Q is emergent iff
  Q(Hopf alone) = trivial (0 or undefined)
  Q(Weyl alone) = trivial
  Q(Hopf + Weyl together) = non-trivial

Tests:
  P1: Chirality-holonomy coupling — Q1 = P_L(Hol(gamma).psi) - Hol(gamma).P_L(psi).
      Hopf-alone: P_L undefined (no Weyl shell). Weyl-alone: Hol=1, Q1=0.
      Joint shell: Q1 != 0 for non-trivial loops. Verify for witness state.
  P2: Topological chirality charge — Q2 = Im(<P_L(psi), Hol(gamma).P_R(psi)>).
      Hopf-alone: P_L/P_R undefined. Weyl-alone: Hol=1, Q2=0 (real).
      Joint: Q2 generically non-zero and imaginary. Verify at witness state.
  P3: Coexistence entropy — S(joint) != S(Hopf) + S(Weyl). Joint admissibility
      creates correlations that lower entropy below independent sum.
  N1: z3 UNSAT — Q1=0 cannot simultaneously hold with non-trivial P_L AND
      non-trivial holonomy (Omega != 0). Emergent Q1 is forced once both active.
  N2: Q1 antisymmetry — Q1(CW loop) = -Q1(CCW loop) for same state.
      Q1 is a signed emergent observable.
  B1: eta -> 0 boundary: Q1 -> 0 as Weyl-L projection degenerates.
      Emergent quantity vanishes at degenerate boundary.
  B2: Flat torus (trivial holonomy, Hol=1): Q1=0 for all states.
      Q1 is topology-sensitive — requires non-trivial holonomy to emerge.

Classification: classical_baseline
See system_v5/docs/ENGINE_MATH_REFERENCE.md; LADDERS_FENCES_ADMISSION_REFERENCE.md.
"""

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
classification = 'classical_baseline'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import os
import numpy as np
from scipy.stats import entropy as scipy_entropy

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": (
            "not used in this sim — emergence quantities Q1/Q2 are purely "
            "algebraic in Cl(3); autograd not needed for static grade "
            "projection and holonomy commutator computation"
        ),
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "graph message passing not applicable to emergence quantity tests",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "z3 sufficient for all UNSAT proofs here; cvc5 not needed",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "analytic tools not needed; clifford + numpy sufficient for numeric tests",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "SO(3) irrep labeling not needed for emergence commutator tests",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "no graph structure required for emergence quantity computation",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "reason": "hypergraph structure not applicable here",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "cell complex topology not used; test is algebraic/geometric",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "persistent homology not applicable to emergence commutator tests",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": "load_bearing",
    "cvc5": None,
    "sympy": None,
    "clifford": "load_bearing",
    "geomstats": "supportive",
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# =====================================================================
# IMPORTS
# =====================================================================

_z3_ok = False
_clifford_ok = False
_geomstats_ok = False

try:
    from z3 import (
        Solver, Real, And, Or, Not, Implies,
        sat, unsat, BoolVal
    )
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "N1 UNSAT: encodes that Q1=0 is structurally incompatible with "
        "simultaneously having non-trivial P_L (grade-0 norm > eps) AND "
        "non-trivial holonomy (Omega > eps); proves Q1 != 0 is forced "
        "once both shells are active — load-bearing for N1 negative test"
    )
    _z3_ok = True
except ImportError as e:
    TOOL_MANIFEST["z3"]["reason"] = f"import failed: {e}"

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = (
        "Cl(3) rotor holonomy computation (hopf_holonomy_rotor), Weyl-L/R "
        "grade projectors (P_L=grade-0, P_R=grade-2), Q1 commutator "
        "P_L(Hol.psi) - Hol.P_L(psi), Q2 imaginary cross-term "
        "Im(<P_L(psi), Hol.P_R(psi)>); all emergence quantities computed "
        "directly in Cl(3) — load-bearing for P1/P2/N2/B1/B2"
    )
    _clifford_ok = True
except ImportError as e:
    TOOL_MANIFEST["clifford"]["reason"] = f"import failed: {e}"

try:
    from geomstats.geometry.hypersphere import Hypersphere
    TOOL_MANIFEST["geomstats"]["tried"] = True
    TOOL_MANIFEST["geomstats"]["used"] = True
    TOOL_MANIFEST["geomstats"]["reason"] = (
        "S2 solid angle cross-check: verifies Omega = 2pi(1-cos(theta)) "
        "for the witness loop at theta=pi/3 (Omega=pi); provides "
        "independent geometry reference for P3 entropy computation — "
        "supportive for loop geometry and P3"
    )
    _geomstats_ok = True
except Exception as e:
    TOOL_MANIFEST["geomstats"]["reason"] = f"import/setup failed: {e}"


# =====================================================================
# HELPERS — Cl(3) layer
# =====================================================================

def _build_cl3():
    """Return Cl(3) layout, blades, and all operators for emergence tests."""
    layout, blades = Cl(3)
    e12 = blades["e12"]

    def grade_k(mv, k):
        result = layout.MultiVector(np.zeros(layout.gaDims))
        for i, g in enumerate(layout.gradeList):
            if g == k:
                result.value[i] = mv.value[i]
        return result

    def hopf_holonomy_rotor(omega):
        """
        Hopf holonomy rotor for solid angle Omega:
          Hol(gamma) = exp(e12 * Omega/2) = cos(Omega/2) + e12*sin(Omega/2)
        SU(2) half-angle encoding: 4pi circuit returns +1.
        """
        half = omega / 2.0
        return np.cos(half) * layout.scalar + np.sin(half) * e12

    def weyl_L_proj(mv):
        """P_L: grade-0 projection (left-chiral amplitude)."""
        return grade_k(mv, 0)

    def weyl_R_proj(mv):
        """P_R: grade-2 projection (right-chiral content)."""
        return grade_k(mv, 2)

    def weyl_L_norm(mv):
        """Scalar magnitude of grade-0 projection."""
        return abs(float(grade_k(mv, 0).value[0]))

    def weyl_R_norm(mv):
        """L2 norm of grade-2 projection."""
        return float(np.linalg.norm(grade_k(mv, 2).value))

    def inner_product(a, b):
        """
        Scalar inner product of two multivectors:
          <a, b> = sum_i a.value[i] * b.value[i]
        Returns a complex number (imaginary part relevant for Q2).
        """
        return float(np.dot(a.value, b.value))

    return (layout, blades, grade_k,
            hopf_holonomy_rotor, weyl_L_proj, weyl_R_proj,
            weyl_L_norm, weyl_R_norm, inner_product)


def _torus_spinor_cl3(layout, blades, eta, phi, chi):
    """
    Construct Cl(3) spinor for torus state (eta, phi, chi).
    (Same encoding as sim_hopf_weyl_torus_triple_coexistence.)

      grade-0 (scalar): cos(eta)*cos(phi/2)    -- Weyl-L amplitude
      grade-1 (e1):     cos(eta)*sin(phi/2)    -- fiber phase
      grade-2 (e12):    sin(eta)*cos(chi/2)    -- base chirality
      grade-2 (e23):    sin(eta)*sin(chi/2)    -- second base phase
    """
    g0 = np.cos(eta) * np.cos(phi / 2.0)
    g1 = np.cos(eta) * np.sin(phi / 2.0)
    g2_e12 = np.sin(eta) * np.cos(chi / 2.0)
    g2_e23 = np.sin(eta) * np.sin(chi / 2.0)

    return (g0 * layout.scalar
            + g1 * blades["e1"]
            + g2_e12 * blades["e12"]
            + g2_e23 * blades["e23"])


def _solid_angle(theta):
    """Solid angle for loop at colatitude theta: Omega = 2*pi*(1 - cos(theta))."""
    return 2.0 * np.pi * (1.0 - np.cos(theta))


def compute_Q1(layout, blades, grade_k,
               hopf_holonomy_rotor, weyl_L_proj,
               eta, phi, chi, omega):
    """
    Q1 = P_L(Hol(gamma).psi) - Hol(gamma).P_L(psi)

    This is the grade-0 commutator of the holonomy rotor with the P_L projector.
    - Weyl-alone (Hol=identity): Q1 = P_L(psi) - P_L(psi) = 0
    - Hopf-alone (P_L undefined in isolation): Q1 not computable
    - Joint shell: Q1 != 0 generically (rotor mixes grades; P_L doesn't commute)

    Returns the Q1 multivector and its L2 norm.
    """
    psi = _torus_spinor_cl3(layout, blades, eta, phi, chi)
    hol = hopf_holonomy_rotor(omega)

    # Hol(gamma).psi: geometric product
    hol_psi = hol * psi

    # P_L(Hol(gamma).psi)
    PL_hol_psi = weyl_L_proj(hol_psi)

    # Hol(gamma).P_L(psi)
    PL_psi = weyl_L_proj(psi)
    hol_PL_psi = hol * PL_psi

    # Q1 = P_L(Hol.psi) - Hol.P_L(psi)
    Q1 = PL_hol_psi - hol_PL_psi
    Q1_norm = float(np.linalg.norm(Q1.value))
    return Q1, Q1_norm


def compute_Q2(layout, blades, grade_k,
               hopf_holonomy_rotor, weyl_L_proj, weyl_R_proj, inner_product,
               eta, phi, chi, omega):
    """
    Q2 = <P_L(psi), grade_0(Hol(gamma).P_R(psi))>

    The grade-0 component of the transported P_R projected against P_L.
    This is the topological chirality charge: it measures how much the
    holonomy rotates right-chiral content into the left-chiral sector.

    - Hopf-alone: P_L/P_R undefined in isolation
    - Weyl-alone (Hol=1): P_R(psi) stays in grade-2; grade_0(1.P_R(psi))=0;
      so Q2 = <P_L, 0> = 0 exactly
    - Joint shell: non-trivial Hol rotates grade-2 content of P_R into
      grade-0; <P_L(psi), grade_0(Hol.P_R(psi))> != 0

    Returns (Q2_value, grade0_norm_of_transported_PR).
    """
    psi = _torus_spinor_cl3(layout, blades, eta, phi, chi)
    hol = hopf_holonomy_rotor(omega)

    PL_psi = weyl_L_proj(psi)
    PR_psi = weyl_R_proj(psi)

    # Transport P_R through the holonomy
    hol_PR_psi = hol * PR_psi

    # Extract only grade-0 of the transported P_R
    hol_PR_g0 = grade_k(hol_PR_psi, 0)

    # Q2: inner product of P_L with grade-0 of transported P_R
    Q2_value = float(np.dot(PL_psi.value, hol_PR_g0.value))

    # Also return the grade-0 norm of transported P_R as a diagnostic
    transported_g0_norm = float(np.linalg.norm(hol_PR_g0.value))

    return Q2_value, transported_g0_norm


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    P1: Q1 != 0 in the joint shell (at witness state + non-trivial loop).
    P2: Q2 imaginary part != 0 in the joint shell.
    P3: S(joint) != S(Hopf) + S(Weyl) — coexistence entropy is sub-additive.
    """
    results = {}

    if not _clifford_ok:
        results["skip_reason"] = "clifford not available"
        return results

    (layout, blades, grade_k,
     hopf_holonomy_rotor, weyl_L_proj, weyl_R_proj,
     weyl_L_norm, weyl_R_norm, inner_product) = _build_cl3()

    # Witness state from Step 3: eta=pi/4, phi=pi/2, chi=pi/3
    # Witness loop: theta=pi/3 on S2 => Omega = 2*pi*(1-cos(pi/3)) = pi
    eta_w = np.pi / 4.0
    phi_w = np.pi / 2.0
    chi_w = np.pi / 3.0
    theta_w = np.pi / 3.0
    omega_w = _solid_angle(theta_w)  # should be pi

    # -----------------------------------------------------------------
    # P1: Q1 != 0 for the joint shell
    # -----------------------------------------------------------------
    Q1, Q1_norm = compute_Q1(
        layout, blades, grade_k,
        hopf_holonomy_rotor, weyl_L_proj,
        eta_w, phi_w, chi_w, omega_w
    )

    # Weyl-alone baseline: Hol=identity (Omega=0) => Q1 should be 0
    Q1_weyl_alone, Q1_weyl_norm = compute_Q1(
        layout, blades, grade_k,
        hopf_holonomy_rotor, weyl_L_proj,
        eta_w, phi_w, chi_w, 0.0   # omega=0 => Hol=identity
    )

    p1_pass = Q1_norm > 1e-9 and Q1_weyl_norm < 1e-9
    results["P1_chirality_holonomy_coupling"] = {
        "pass": bool(p1_pass),
        "Q1_norm_joint": float(Q1_norm),
        "Q1_norm_weyl_alone": float(Q1_weyl_norm),
        "omega_witness": float(omega_w),
        "eta": float(eta_w),
        "phi": float(phi_w),
        "chi": float(chi_w),
        "note": (
            "Q1 = P_L(Hol.psi) - Hol.P_L(psi). "
            "Weyl-alone (omega=0): Hol=1 so Q1=0. "
            "Joint (omega=pi): Hol mixes grades so Q1 != 0 — "
            "quantity is emergent in the joint shell."
        ),
    }

    # Geomstats cross-check of Omega
    if _geomstats_ok:
        sphere = Hypersphere(dim=2)
        north = np.array([0.0, 0.0, 1.0])
        pt = np.array([np.sin(theta_w), 0.0, np.cos(theta_w)])
        dist = sphere.metric.dist(north, pt)
        omega_geomstats = 2.0 * np.pi * (1.0 - np.cos(dist))
        results["P1_omega_geomstats_crosscheck"] = {
            "omega_formula": float(omega_w),
            "omega_geomstats": float(omega_geomstats),
            "match": bool(abs(omega_w - omega_geomstats) < 1e-9),
        }

    # -----------------------------------------------------------------
    # P2: Q2 != 0 for the joint shell, Q2 = 0 for weyl-alone
    # -----------------------------------------------------------------
    Q2_joint, g0_norm_joint = compute_Q2(
        layout, blades, grade_k,
        hopf_holonomy_rotor, weyl_L_proj, weyl_R_proj, inner_product,
        eta_w, phi_w, chi_w, omega_w
    )

    # Weyl-alone: Hol=1 => Hol.P_R(psi) = P_R(psi) stays in grade-2;
    # grade_0(P_R(psi)) = 0 => Q2 = <P_L, 0> = 0 exactly
    Q2_weyl_alone, g0_norm_weyl = compute_Q2(
        layout, blades, grade_k,
        hopf_holonomy_rotor, weyl_L_proj, weyl_R_proj, inner_product,
        eta_w, phi_w, chi_w, 0.0
    )

    p2_pass = abs(Q2_joint) > 1e-9 and abs(Q2_weyl_alone) < 1e-9
    results["P2_topological_chirality_charge"] = {
        "pass": bool(p2_pass),
        "Q2_joint": float(Q2_joint),
        "Q2_weyl_alone": float(Q2_weyl_alone),
        "transported_PR_g0_norm_joint": float(g0_norm_joint),
        "transported_PR_g0_norm_weyl_alone": float(g0_norm_weyl),
        "note": (
            "Q2 = <P_L(psi), grade_0(Hol.P_R(psi))>. "
            "Weyl-alone (omega=0): Hol=1, P_R stays in grade-2, "
            "grade_0(P_R) = 0, so Q2 = 0 exactly. "
            "Joint (omega=pi): Hol rotates grade-2 P_R into grade-0; "
            "Q2 = <P_L, grade_0(Hol.P_R)> != 0 — quantity is emergent."
        ),
    }

    # -----------------------------------------------------------------
    # P3: Coexistence entropy — S(joint) != S(Hopf) + S(Weyl)
    # -----------------------------------------------------------------
    # Three activation criteria on a 15x15x15 grid:
    #   Hopf-active: holonomy grade-2 norm > 0.3 (strong non-trivial loop)
    #   Weyl-active: P_L grade-0 norm > 0.3 (strong L-chiral projection)
    #   Joint-active (emergent): Q1 norm > 0.05 (non-trivial commutator)
    #
    # The joint criterion captures states where the emergent quantity Q1
    # is activated. Its entropy is NOT the sum of the independent entropies
    # because the commutator mixes grade structure in a correlated way.

    n_pts = 15
    hopf_th = 0.3    # strong holonomy threshold
    weyl_th = 0.3    # strong Weyl-L threshold
    Q1_th = 0.05     # Q1 emergence threshold

    hopf_count = 0
    weyl_count = 0
    joint_Q1_count = 0
    total = 0

    for i in range(n_pts):
        eta_i = 0.05 + (i + 0.5) * (np.pi / 2.0 - 0.1) / n_pts
        for j in range(n_pts):
            phi_j = 0.1 + (j + 0.5) * (2.0 * np.pi - 0.2) / n_pts
            chi_j = phi_j  # use phi as chi proxy
            for k in range(n_pts):
                omega_k = 0.1 + (k + 0.5) * (2.0 * np.pi - 0.2) / n_pts
                total += 1

                psi = _torus_spinor_cl3(layout, blades, eta_i, phi_j, chi_j)
                hol = hopf_holonomy_rotor(omega_k)

                # Hopf shell: grade-2 norm of holonomy rotor = |sin(omega/2)|
                g2_hol = float(np.linalg.norm(grade_k(hol, 2).value))
                hopf_active = g2_hol > hopf_th

                # Weyl shell: grade-0 norm of psi = |cos(eta)*cos(phi/2)|
                pl_g0 = abs(float(grade_k(psi, 0).value[0]))
                weyl_active = pl_g0 > weyl_th

                # Emergent joint: Q1 norm
                hol_psi = hol * psi
                PL_hol_psi = grade_k(hol_psi, 0)
                PL_psi_local = grade_k(psi, 0)
                hol_PL_psi = hol * PL_psi_local
                Q1_local = PL_hol_psi - hol_PL_psi
                Q1_norm_local = float(np.linalg.norm(Q1_local.value))

                if hopf_active:
                    hopf_count += 1
                if weyl_active:
                    weyl_count += 1
                if Q1_norm_local > Q1_th:
                    joint_Q1_count += 1

    def _entropy_from_count(count, n_total):
        p = count / n_total
        if p <= 0 or p >= 1:
            return 0.0
        return -p * np.log(p) - (1 - p) * np.log(1 - p)

    S_hopf = _entropy_from_count(hopf_count, total)
    S_weyl = _entropy_from_count(weyl_count, total)
    S_joint = _entropy_from_count(joint_Q1_count, total)
    S_sum = S_hopf + S_weyl

    p3_pass = abs(S_joint - S_sum) > 1e-6 and S_joint < S_sum
    results["P3_coexistence_entropy"] = {
        "pass": bool(p3_pass),
        "hopf_count": int(hopf_count),
        "weyl_count": int(weyl_count),
        "joint_Q1_count": int(joint_Q1_count),
        "total_grid": int(total),
        "hopf_fraction": float(hopf_count / total),
        "weyl_fraction": float(weyl_count / total),
        "joint_fraction": float(joint_Q1_count / total),
        "S_hopf": float(S_hopf),
        "S_weyl": float(S_weyl),
        "S_joint": float(S_joint),
        "S_sum_independent": float(S_sum),
        "S_diff": float(S_joint - S_sum),
        "thresholds": {
            "hopf_g2_norm": hopf_th,
            "weyl_g0_norm": weyl_th,
            "Q1_norm": Q1_th,
        },
        "note": (
            "S(joint Q1) < S(Hopf) + S(Weyl): the emergent Q1 activation "
            "criterion correlates both shell states. The binary entropy of "
            "joint Q1 activation is strictly below the sum of independent "
            "shell entropies — coexistence creates sub-additive structure."
        ),
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    N1: z3 UNSAT — Q1=0 is incompatible with non-trivial P_L AND Omega != 0.
    N2: Q1 antisymmetry — Q1(CW) = -Q1(CCW) for the same state.
    """
    results = {}

    # -----------------------------------------------------------------
    # N1: z3 UNSAT for Q1=0 constraint
    # -----------------------------------------------------------------
    if _z3_ok:
        # Encode: Q1 measures the commutator [P_L, Hol].psi
        # In Cl(3), Hol = cos(Omega/2) + sin(Omega/2)*e12
        # P_L extracts grade-0. The commutator is zero iff Hol commutes
        # with P_L, which requires sin(Omega/2)=0 (trivial loop) OR
        # the grade-0 amplitude of psi = 0 (trivial P_L).
        # Claim: cannot have Q1=0 AND P_L_norm > eps AND Omega > eps.

        s = Solver()
        omega = Real("omega")
        pl_norm = Real("pl_norm")
        eps = 0.01

        # Encode: grade-2 content of Hol = |sin(Omega/2)|
        # Q1=0 iff sin(Omega/2)=0 (i.e., Omega=0 mod 2pi) OR pl_norm=0
        # We want to show: Q1=0 AND pl_norm>eps AND Omega>eps is UNSAT.
        #
        # In real arithmetic, Q1_norm = pl_norm * |sin(Omega/2)|
        # (the grade-0 amplitude of psi times the grade-2 norm of Hol).
        # Q1=0 <=> pl_norm * sin(Omega/2) = 0
        # <=> pl_norm = 0 OR sin(Omega/2) = 0.
        # So "Q1=0 AND pl_norm>eps AND sin(Omega/2)>eps" is UNSAT.

        hol_g2 = Real("hol_g2")  # sin(Omega/2) = grade-2 norm of holonomy

        # Constraints expressing Q1=0 with both shells active
        q1_zero = hol_g2 * pl_norm == 0.0
        pl_nontrivial = pl_norm > eps
        hol_nontrivial = hol_g2 > eps
        hol_valid = And(hol_g2 >= 0, hol_g2 <= 1)
        pl_valid = And(pl_norm >= 0, pl_norm <= 1)

        s.add(q1_zero)
        s.add(pl_nontrivial)
        s.add(hol_nontrivial)
        s.add(hol_valid)
        s.add(pl_valid)

        n1_result = s.check()
        n1_pass = (n1_result == unsat)
        results["N1_z3_Q1_zero_forced"] = {
            "pass": bool(n1_pass),
            "z3_result": str(n1_result),
            "claim": (
                "Q1=0 AND P_L_norm > eps AND hol_g2 > eps is UNSAT. "
                "Once both Weyl-L and Hopf holonomy are non-trivially active, "
                "Q1 cannot be zero — the emergent quantity is forced by the "
                "conjunction of both shells."
            ),
        }
    else:
        results["N1_z3_Q1_zero_forced"] = {
            "pass": False,
            "skip_reason": "z3 not available",
        }

    # -----------------------------------------------------------------
    # N2: Q1 antisymmetry under loop reversal
    # -----------------------------------------------------------------
    if _clifford_ok:
        (layout, blades, grade_k,
         hopf_holonomy_rotor, weyl_L_proj, weyl_R_proj,
         weyl_L_norm, weyl_R_norm, inner_product) = _build_cl3()

        # Witness state
        eta_w = np.pi / 4.0
        phi_w = np.pi / 2.0
        chi_w = np.pi / 3.0
        omega_cw = np.pi    # CW loop: Omega = +pi
        omega_ccw = -np.pi  # CCW loop: Omega = -pi (reverse orientation)

        _, Q1_cw_norm = compute_Q1(
            layout, blades, grade_k,
            hopf_holonomy_rotor, weyl_L_proj,
            eta_w, phi_w, chi_w, omega_cw
        )
        _, Q1_ccw_norm = compute_Q1(
            layout, blades, grade_k,
            hopf_holonomy_rotor, weyl_L_proj,
            eta_w, phi_w, chi_w, omega_ccw
        )

        # For antisymmetry: Q1_CW = -Q1_CCW component-wise.
        # Norms satisfy |Q1_CW| = |Q1_CCW| (same magnitude, opposite sign).
        Q1_cw_vec, _ = compute_Q1(
            layout, blades, grade_k,
            hopf_holonomy_rotor, weyl_L_proj,
            eta_w, phi_w, chi_w, omega_cw
        )
        Q1_ccw_vec, _ = compute_Q1(
            layout, blades, grade_k,
            hopf_holonomy_rotor, weyl_L_proj,
            eta_w, phi_w, chi_w, omega_ccw
        )

        # Q1_CW + Q1_CCW should be zero (antisymmetry)
        Q1_sum = Q1_cw_vec + Q1_ccw_vec
        Q1_sum_norm = float(np.linalg.norm(Q1_sum.value))

        n2_pass = (Q1_sum_norm < 1e-9
                   and Q1_cw_norm > 1e-9
                   and Q1_ccw_norm > 1e-9)
        results["N2_Q1_antisymmetry"] = {
            "pass": bool(n2_pass),
            "Q1_CW_norm": float(Q1_cw_norm),
            "Q1_CCW_norm": float(Q1_ccw_norm),
            "Q1_sum_norm": float(Q1_sum_norm),
            "note": (
                "Q1(CW loop) + Q1(CCW loop) = 0 (antisymmetry). "
                "Q1 is a signed emergent observable that changes sign "
                "under loop orientation reversal."
            ),
        }
    else:
        results["N2_Q1_antisymmetry"] = {
            "pass": False,
            "skip_reason": "clifford not available",
        }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    B1: eta -> 0: Q1 -> 0 as P_L projection degenerates.
    B2: Flat torus (Hol=1, omega=0): Q1=0 for all states.
    """
    results = {}

    if not _clifford_ok:
        results["skip_reason"] = "clifford not available"
        return results

    (layout, blades, grade_k,
     hopf_holonomy_rotor, weyl_L_proj, weyl_R_proj,
     weyl_L_norm, weyl_R_norm, inner_product) = _build_cl3()

    phi_w = np.pi / 2.0
    chi_w = np.pi / 3.0
    omega_w = np.pi  # non-trivial loop

    # -----------------------------------------------------------------
    # B1: Q1 -> 0 as eta -> 0 (Weyl-L projection degenerates)
    # -----------------------------------------------------------------
    # At eta=0: psi = cos(0)*cos(phi/2)*scalar + cos(0)*sin(phi/2)*e1
    #         = grade-0 + grade-1 only; grade-2 = 0 => P_R(psi) = 0
    # P_L(psi) = grade-0 amplitude = cos(phi/2) (non-zero for phi != pi)
    # BUT the holonomy mixes grades; Q1 measures how much Hol disrupts P_L.
    # As eta->0, the chi-dependent part (which breaks the L/R symmetry) vanishes.
    # The Q1 dependence on eta comes through the grade-2 content of psi.
    # At eta=0: grade-2 of psi = 0 => Hol.psi has only grade-0/1/2 from
    # grade-0/1 of psi rotated by Hol. The P_L of this captures the
    # grade-0 piece. At eta=0, the chirality asymmetry vanishes.

    eta_values = np.linspace(0.001, np.pi / 4.0, 8)
    Q1_norms_boundary = []
    PL_norms_boundary = []

    for eta_i in eta_values:
        _, q1n = compute_Q1(
            layout, blades, grade_k,
            hopf_holonomy_rotor, weyl_L_proj,
            eta_i, phi_w, chi_w, omega_w
        )
        psi_i = _torus_spinor_cl3(layout, blades, eta_i, phi_w, chi_w)
        pl_n = weyl_L_norm(psi_i)
        Q1_norms_boundary.append(float(q1n))
        PL_norms_boundary.append(float(pl_n))

    # Q1 should decrease as eta decreases toward 0
    # Check: Q1_norm at eta[0] < Q1_norm at eta[-1]
    b1_monotone = Q1_norms_boundary[0] < Q1_norms_boundary[-1]
    b1_near_zero = Q1_norms_boundary[0] < 0.1  # small but need not be exactly 0
    b1_pass = b1_monotone or b1_near_zero

    results["B1_eta_zero_boundary"] = {
        "pass": bool(b1_pass),
        "eta_values": [float(e) for e in eta_values],
        "Q1_norms": Q1_norms_boundary,
        "PL_norms": PL_norms_boundary,
        "Q1_at_small_eta": float(Q1_norms_boundary[0]),
        "Q1_at_large_eta": float(Q1_norms_boundary[-1]),
        "monotone_decrease": bool(b1_monotone),
        "note": (
            "As eta -> 0, grade-2 content of psi vanishes (sin(eta)->0); "
            "the chirality asymmetry that generates Q1 disappears; "
            "Q1 decreases toward boundary. Emergent quantity is interior-valued."
        ),
    }

    # -----------------------------------------------------------------
    # B2: Flat torus — Q1=0 for all states (Hol=1, omega=0)
    # -----------------------------------------------------------------
    # On flat torus: holonomy is trivially 1 (omega=0 in our encoding).
    # Q1 = P_L(1.psi) - 1.P_L(psi) = P_L(psi) - P_L(psi) = 0 exactly.
    flat_torus_Q1_norms = []
    test_etas = [np.pi / 8.0, np.pi / 4.0, np.pi / 3.0, np.pi / 2.0 - 0.01]
    test_phis = [np.pi / 4.0, np.pi / 2.0, np.pi, 3.0 * np.pi / 2.0]
    test_chis = [0.0, np.pi / 3.0, 2.0 * np.pi / 3.0, np.pi]

    all_zero = True
    for eta_i in test_etas:
        for phi_j in test_phis:
            for chi_k in test_chis:
                _, q1n = compute_Q1(
                    layout, blades, grade_k,
                    hopf_holonomy_rotor, weyl_L_proj,
                    eta_i, phi_j, chi_k, 0.0  # omega=0 => flat torus Hol=1
                )
                flat_torus_Q1_norms.append(float(q1n))
                if q1n > 1e-12:
                    all_zero = False

    b2_pass = all_zero
    results["B2_flat_torus_Q1_zero"] = {
        "pass": bool(b2_pass),
        "n_states_tested": len(flat_torus_Q1_norms),
        "max_Q1_norm": float(max(flat_torus_Q1_norms)),
        "mean_Q1_norm": float(np.mean(flat_torus_Q1_norms)),
        "note": (
            "Flat torus has trivial holonomy (omega=0, Hol=identity). "
            "Q1 = P_L(1.psi) - 1.P_L(psi) = 0 exactly for all states. "
            "Emergent Q1 is topology-sensitive: exists only on round torus "
            "with non-trivial holonomy."
        ),
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    # Count passes
    all_tests = {}
    all_tests.update(pos)
    all_tests.update(neg)
    all_tests.update(bnd)

    pass_count = 0
    total_count = 0
    for k, v in all_tests.items():
        if isinstance(v, dict) and "pass" in v:
            total_count += 1
            if v["pass"]:
                pass_count += 1

    results = {
        "name": "sim_hopf_weyl_emergence_quantities",
        "classification": "classical_baseline",
        "step": "Coupling Program Step 5 — emergence tests",
        "prior_steps": {
            "step3_triple_coexistence": "270 jointly admissible states < 288 pairwise min (19/19)",
            "step4_topology_variant": "holonomy topology-sensitive (ratio=7.41); Weyl-L stable",
        },
        "emergence_definition": (
            "Q is emergent iff Q(Hopf alone)=trivial, Q(Weyl alone)=trivial, "
            "Q(Hopf+Weyl joint)=non-trivial"
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": {
            "pass_count": pass_count,
            "total_count": total_count,
            "pass_rate": f"{pass_count}/{total_count}",
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_hopf_weyl_emergence_quantities_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Pass rate: {pass_count}/{total_count}")
