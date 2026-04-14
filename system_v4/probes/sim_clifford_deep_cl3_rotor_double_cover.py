#!/usr/bin/env python3
"""
sim_clifford_deep_cl3_rotor_double_cover.py

Deep clifford-package sim. Exercises Cl(3) = Cl(3,0) using the `clifford`
library's real geometric algebra multivectors (NOT numpy matrix mimicry) to
verify three load-bearing spin-group identities relevant to the Weyl/Hopf
carrier in this project:

  (P1) SU(2) -> SO(3) double cover: R and -R act identically on vectors,
       i.e. for any unit rotor R and vector v in Cl(3),
           R v R^~  ==  (-R) v (-R)^~ .
       Yet R and -R are distinct elements of Spin(3), proving 2-to-1.

  (P2) Rotor exponential identity: exp(-B * theta/2) with B a unit bivector
       yields a rotor whose sandwich action on a vector rotates it by theta
       in the plane dual to B. Composing two such rotors about the SAME axis
       (same B) produces a rotor equal (up to global sign in Spin(3)) to the
       single rotor for (theta1+theta2). The SO(3)-action is literally equal.

  (P3) Pseudoscalar chirality flip: the unit pseudoscalar I = e1 e2 e3 in
       Cl(3) commutes with all vectors but anticommutes with bivectors'
       duals in a controlled way; multiplying a "Weyl-like" odd multivector
       (vector + trivector component) by I swaps vector <-> trivector
       grade, flipping chirality. We verify grade involution under I on a
       constructed odd element.

Classification: canonical. clifford is load_bearing. Positive/negative/boundary.
Interpreter: Makefile PYTHON (codex-ratchet env).

If `clifford` not importable -> report blocker, do NOT fall back to numpy.
"""

import json
import os
import math
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not needed; pure GA identities, no autograd"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed; no graph structure in rotor identities"},
    "z3":        {"tried": False, "used": False, "reason": "GA identities are over reals with transcendental angles; SMT not suitable here"},
    "cvc5":      {"tried": False, "used": False, "reason": "same as z3 -- transcendental rotor angles out of scope"},
    "sympy":     {"tried": False, "used": False, "reason": "symbolic GA would duplicate clifford's numeric proof; kept as supportive option only"},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": "geomstats SO(3) would be numpy-matrix mimicry; deliberately not used"},
    "e3nn":      {"tried": False, "used": False, "reason": "e3nn Wigner-D is matrix form; we test rotor form directly"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi":       {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx":  {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi":     {"tried": False, "used": False, "reason": "no persistence"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

# --- clifford (load-bearing) ---
CLIFFORD_AVAILABLE = True
CLIFFORD_ERR = None
try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
except Exception as e:
    CLIFFORD_AVAILABLE = False
    CLIFFORD_ERR = repr(e)
    TOOL_MANIFEST["clifford"]["reason"] = f"import failed: {CLIFFORD_ERR}"


# =====================================================================
# HELPERS (all operate on clifford MultiVector objects)
# =====================================================================

def _setup_cl3():
    """Build Cl(3,0). Returns (layout, blades, e1, e2, e3, I)."""
    layout, blades = Cl(3)
    e1 = blades['e1']
    e2 = blades['e2']
    e3 = blades['e3']
    I  = e1 * e2 * e3   # unit pseudoscalar
    return layout, blades, e1, e2, e3, I


def _mv_close(a, b, tol=1e-10):
    """Compare two multivectors coefficient-wise in the clifford basis."""
    diff = a - b
    # clifford exposes .value as the coefficient vector in the canonical basis
    return max(abs(float(x)) for x in diff.value) < tol


def _rotor_exp(B, theta):
    """Rotor = exp(-B * theta/2) with B a unit bivector. Uses clifford's
    built-in MultiVector exponential (not numpy)."""
    from clifford import MultiVector  # noqa: F401 (for clarity)
    half = -B * (theta / 2.0)
    # clifford MultiVector has .exp() -- closed-form for bivector arguments
    return half.exp()


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    if not CLIFFORD_AVAILABLE:
        results["blocker"] = f"clifford not importable: {CLIFFORD_ERR}"
        return results

    layout, blades, e1, e2, e3, I = _setup_cl3()
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = "Cl(3) layout, bivector exp, rotor sandwich, pseudoscalar duality all computed as MultiVector ops"
    TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"

    # --- P1: double cover ---
    B12 = e1 * e2                       # unit bivector (B12^2 = -1)
    theta = math.pi / 3.0               # 60 deg
    R = _rotor_exp(B12, theta)
    negR = -R
    v = 2.0 * e1 + 1.0 * e2 + 0.5 * e3  # arbitrary vector
    vR   = R   * v * (~R)
    vNeg = negR * v * (~negR)
    p1_equal_action = _mv_close(vR, vNeg, tol=1e-10)
    p1_rotors_distinct = not _mv_close(R, negR, tol=1e-10)
    # A rotor rotates in the plane of its bivector by theta:
    # check ||v_rot|| == ||v||
    def _vnorm2(x):
        return float((x * x).value[0])  # scalar part of v*v for a vector = |v|^2
    p1_norm_preserved = abs(_vnorm2(vR) - _vnorm2(v)) < 1e-10
    results["P1_double_cover"] = {
        "equal_action_on_vector": p1_equal_action,
        "R_neg_R_distinct":       p1_rotors_distinct,
        "norm_preserved":         p1_norm_preserved,
        "pass": p1_equal_action and p1_rotors_distinct and p1_norm_preserved,
    }

    # --- P2: rotor exponential + composition about same axis ---
    t1, t2 = 0.37, 1.21
    R1 = _rotor_exp(B12, t1)
    R2 = _rotor_exp(B12, t2)
    R12_composed = R2 * R1                         # apply R1 then R2
    R_sum        = _rotor_exp(B12, t1 + t2)
    p2_rotor_match = _mv_close(R12_composed, R_sum, tol=1e-10)

    # Sandwich-action equality (guaranteed even if rotors differ by global sign,
    # but here they should match exactly for commuting bivector exponentials)
    v_c = v
    vA = R12_composed * v_c * (~R12_composed)
    vB = R_sum        * v_c * (~R_sum)
    p2_action_match = _mv_close(vA, vB, tol=1e-10)

    # Cross-check: rotation of e1 by theta in e1^e2 plane gives
    # cos(theta) e1 + sin(theta) e2 (standard right-hand rule for B12 = e1 e2
    # with rotor exp(-B12*theta/2))
    th = t1 + t2
    expected_e1_rot = math.cos(th) * e1 + math.sin(th) * e2
    got_e1_rot = R_sum * e1 * (~R_sum)
    p2_closed_form = _mv_close(got_e1_rot, expected_e1_rot, tol=1e-10)
    results["P2_rotor_exp_composition"] = {
        "R2_R1_equals_R_sum":         p2_rotor_match,
        "sandwich_action_equal":      p2_action_match,
        "matches_closed_form_on_e1":  p2_closed_form,
        "pass": p2_rotor_match and p2_action_match and p2_closed_form,
    }

    # --- P3: pseudoscalar chirality / grade duality ---
    # In Cl(3,0), I = e1 e2 e3, I^2 = -1, I commutes with everything (center).
    # For a vector v, I*v is a bivector (grade 2). For a bivector B, I*B is a
    # vector. So I swaps grade 1 <-> grade 2. We build a "Weyl-like" odd
    # multivector psi = a*v + b*T where T is trivector, verify that I*psi
    # is an even multivector (grade 0 + grade 2), i.e. grade-parity flipped.
    I_sq = I * I
    p3_I_squared = abs(float(I_sq.value[0]) + 1.0) < 1e-12 and \
                   max(abs(float(x)) for x in (I_sq + 1).value) < 1e-12
    # I commutes with vectors in Cl(3) (odd dim): I*e1 == e1*I
    p3_I_central = _mv_close(I * e1, e1 * I, 1e-12) and \
                   _mv_close(I * e2, e2 * I, 1e-12) and \
                   _mv_close(I * e3, e3 * I, 1e-12)
    # Grade swap: I * e1 is grade-2
    Iv = I * e1
    # clifford MultiVector has .grades() giving the set of present grades
    grades_Iv = set(Iv.grades())
    p3_vector_to_bivector = (grades_Iv == {2})
    IB = I * (e1 * e2)
    grades_IB = set(IB.grades())
    p3_bivector_to_vector = (grades_IB == {1})
    # Chirality flip on Weyl-like odd element
    psi = 0.7 * e1 + 0.3 * (e1 * e2 * e3)   # grade {1, 3} = odd
    I_psi = I * psi
    grades_Ipsi = set(I_psi.grades())
    p3_parity_flip = grades_Ipsi.issubset({0, 2}) and len(grades_Ipsi) > 0
    results["P3_pseudoscalar_chirality"] = {
        "I_squared_is_minus_one":   p3_I_squared,
        "I_is_central":             p3_I_central,
        "I_maps_grade1_to_grade2":  p3_vector_to_bivector,
        "I_maps_grade2_to_grade1":  p3_bivector_to_vector,
        "odd_psi_maps_to_even":     p3_parity_flip,
        "pass": all([p3_I_squared, p3_I_central, p3_vector_to_bivector,
                     p3_bivector_to_vector, p3_parity_flip]),
    }

    results["all_positive_pass"] = all(
        v.get("pass", False) for k, v in results.items() if k.startswith("P")
    )
    return results


# =====================================================================
# NEGATIVE TESTS  (must FAIL the identity deliberately -> confirms test is real)
# =====================================================================

def run_negative_tests():
    results = {}
    if not CLIFFORD_AVAILABLE:
        results["blocker"] = f"clifford not importable: {CLIFFORD_ERR}"
        return results
    _, _, e1, e2, e3, I = _setup_cl3()

    # N1: wrong bivector normalization -> rotor is NOT norm-preserving,
    #     sandwich action differs from the closed-form rotation.
    B_bad = 2.0 * e1 * e2            # not unit
    theta = math.pi / 4
    R_bad = _rotor_exp(B_bad, theta)
    v = e1 + 0.5 * e2
    v_rot_bad = R_bad * v * (~R_bad)
    expected = math.cos(theta) * e1 + math.sin(theta) * e2 + 0 * e3
    # Should NOT match the unit-bivector closed form
    n1_differs = not _mv_close(v_rot_bad, math.cos(theta) * e1 + math.sin(theta) * e2, tol=1e-6)
    results["N1_non_unit_bivector_breaks_closed_form"] = {"differs_as_expected": n1_differs, "pass": n1_differs}

    # N2: non-commuting axes -> R(B23)*R(B12) != R about some single axis with summed angles.
    B12 = e1 * e2
    B23 = e2 * e3
    Ra = _rotor_exp(B12, 0.5)
    Rb = _rotor_exp(B23, 0.7)
    Rprod = Rb * Ra
    Rsum_fake = _rotor_exp(B12, 1.2)  # pretend composition is about B12
    n2_not_equal = not _mv_close(Rprod, Rsum_fake, tol=1e-6)
    results["N2_noncommuting_axes_compose_differently"] = {"not_equal_as_expected": n2_not_equal, "pass": n2_not_equal}

    # N3: I on an EVEN multivector stays EVEN (not a parity flip).
    #     A true chirality flip only occurs for odd input. Check the "flip"
    #     claim fails when fed an even input -> confirms the flip is grade-parity, not magic.
    even_phi = 1.0 + 0.4 * (e1 * e2)   # grades {0, 2}
    I_even = I * even_phi
    grades_Ieven = set(I_even.grades())
    # Expect grades to remain even {1 maybe? no: I*1=I which is grade 3 (odd); I*e12 = -e3 (grade 1, odd)}
    # So I on an EVEN element in Cl(3) produces an ODD element. Parity flips either way --
    # the negative claim we test: "I preserves parity" is FALSE.
    claim_parity_preserved = grades_Ieven.issubset({0, 2})
    n3_claim_is_false = not claim_parity_preserved
    results["N3_I_does_not_preserve_parity"] = {
        "grades_of_I_times_even": sorted(grades_Ieven),
        "parity_preserved_claim_is_false": n3_claim_is_false,
        "pass": n3_claim_is_false,
    }

    results["all_negative_pass"] = all(
        v.get("pass", False) for k, v in results.items() if k.startswith("N")
    )
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    if not CLIFFORD_AVAILABLE:
        results["blocker"] = f"clifford not importable: {CLIFFORD_ERR}"
        return results
    _, _, e1, e2, e3, I = _setup_cl3()

    B12 = e1 * e2

    # B1: theta = 0 -> rotor = 1 (scalar identity)
    R0 = _rotor_exp(B12, 0.0)
    b1 = _mv_close(R0, 1.0 + 0 * e1, tol=1e-12)
    results["B1_zero_angle_is_identity"] = {"pass": b1}

    # B2: theta = 2*pi -> rotor = -1 (the hallmark of Spin(3): a full 2pi
    #     rotation returns -1, not +1; 4pi returns +1). This IS the double cover.
    R_2pi = _rotor_exp(B12, 2 * math.pi)
    b2_minus_one = _mv_close(R_2pi, -1.0 + 0 * e1, tol=1e-10)
    R_4pi = _rotor_exp(B12, 4 * math.pi)
    b2_plus_one = _mv_close(R_4pi, 1.0 + 0 * e1, tol=1e-10)
    results["B2_2pi_is_minus_one_4pi_is_plus_one"] = {
        "R(2pi)==-1": b2_minus_one,
        "R(4pi)==+1": b2_plus_one,
        "pass": b2_minus_one and b2_plus_one,
    }

    # B3: tiny angle linearization: R ~ 1 - B*theta/2 for small theta
    eps = 1e-6
    R_eps = _rotor_exp(B12, eps)
    lin = 1.0 - B12 * (eps / 2.0)
    diff = R_eps - lin
    # second-order term is B12^2 * eps^2/8 = -eps^2/8; allow O(eps^2) error
    max_coef = max(abs(float(x)) for x in diff.value)
    b3 = max_coef < 1e-10
    results["B3_small_angle_linearization"] = {"max_residual": max_coef, "pass": b3}

    # B4: inverse rotor: R * ~R == 1
    theta = 0.913
    R = _rotor_exp(B12, theta)
    prod = R * (~R)
    b4 = _mv_close(prod, 1.0 + 0 * e1, tol=1e-12)
    results["B4_rotor_inverse_is_reverse"] = {"pass": b4}

    results["all_boundary_pass"] = all(
        v.get("pass", False) for k, v in results.items() if k.startswith("B")
    )
    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    overall_pass = (
        CLIFFORD_AVAILABLE
        and positive.get("all_positive_pass", False)
        and negative.get("all_negative_pass", False)
        and boundary.get("all_boundary_pass", False)
    )

    results = {
        "name": "sim_clifford_deep_cl3_rotor_double_cover",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "clifford_available": CLIFFORD_AVAILABLE,
        "clifford_import_error": CLIFFORD_ERR,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall_pass,
        "identities_proved": [
            "SU(2)->SO(3) double cover: R and -R induce identical vector rotation",
            "Rotor exponential: exp(-B*theta/2) composition about same axis is additive in angle",
            "Pseudoscalar I=e1e2e3 flips grade parity (chirality) on odd multivectors",
            "Spin(3) 4pi-periodicity: R(2pi)=-1, R(4pi)=+1",
        ],
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_clifford_deep_cl3_rotor_double_cover_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"overall_pass={overall_pass}")
    print(f"Results written to {out_path}")

    if not overall_pass:
        raise SystemExit(1)
