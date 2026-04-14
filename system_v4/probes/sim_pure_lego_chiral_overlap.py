#!/usr/bin/env python3
"""
PURE LEGO: Chiral Overlap <L|R> for Weyl Spinors
=================================================
Foundational building block.  Pure math -- numpy + clifford Cl(3).
No engine imports.  Every operation verified against theory.

Sections
--------
1. Bloch-sphere parameterized left/right Weyl spinors
2. Chiral overlap |<L|R>|^2 as function of (theta, phi)
3. Poles: overlap = 0 at theta=0 and theta=pi
4. Equator: maximal overlap at theta=pi/2
5. L<->R symmetry verification
6. Completeness: overlap + complement = 1
7. Cl(3) cross-validation of chiral projectors
8. Negative: non-normalized spinors give wrong results
9. Boundary: poles, equator, full theta sweep
"""

import json, os, time, traceback
import numpy as np
from clifford import Cl
classification = "classical_baseline"  # auto-backfill

np.random.seed(42)
EPS = 1e-12

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": "classical baseline -- numpy + clifford only"},
    "pyg":        {"tried": False, "used": False, "reason": "classical baseline -- numpy + clifford only"},
    "z3":         {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "cvc5":       {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "sympy":      {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "clifford":   {"tried": True, "used": True, "reason": "Cl(3) chiral projector cross-validation"},
    "geomstats":  {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "e3nn":       {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "rustworkx":  {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "xgi":        {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "toponetx":   {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "gudhi":      {"tried": False, "used": False, "reason": "not needed for this baseline"},
}

TOOL_INTEGRATION_DEPTH = {
    **{k: None for k in TOOL_MANIFEST},
    "clifford": "load_bearing",
}

CLASSIFICATION = "classical_baseline"
CLASSIFICATION_NOTE = (
    "Classical baseline for fixed-reference chiral overlap on Weyl spinors, including "
    "orthogonality, completeness, and Cl(3) projector cross-checks."
)
LEGO_IDS = ["chiral_overlap"]
PRIMARY_LEGO_IDS = ["chiral_overlap"]

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def ket(v):
    """Column vector from list."""
    return np.array(v, dtype=complex).reshape(-1, 1)

def inner(a, b):
    """<a|b> inner product of column vectors."""
    return (a.conj().T @ b)[0, 0]

def norm2(v):
    """Squared norm of column vector."""
    return float(np.real(inner(v, v)))

# ──────────────────────────────────────────────────────────────────────
# Core: Bloch-sphere Weyl spinors
# ──────────────────────────────────────────────────────────────────────

def left_weyl(theta, phi):
    """
    Left Weyl spinor from Bloch sphere angles.
    |L> = cos(theta/2)|0> + e^{i*phi}*sin(theta/2)|1>
    """
    return ket([np.cos(theta / 2), np.exp(1j * phi) * np.sin(theta / 2)])

def right_weyl(theta, phi):
    """
    Right Weyl spinor (orthogonal chirality partner).
    |R> = sin(theta/2)|0> - e^{i*phi}*cos(theta/2)|1>
    """
    return ket([np.sin(theta / 2), -np.exp(1j * phi) * np.cos(theta / 2)])

def chiral_overlap(theta, phi):
    """
    |<L|R>|^2 -- the chiral overlap.
    Analytic: |cos(theta/2)*sin(theta/2) - sin(theta/2)*cos(theta/2)|^2
    simplifies to |sin(theta/2)*cos(theta/2)(1 - 1)|^2... but let's be careful.
    Actually: <L|R> = cos(t/2)*sin(t/2) + e^{-i*phi}*sin(t/2)*(-e^{i*phi}*cos(t/2))
                    = cos(t/2)*sin(t/2) - sin(t/2)*cos(t/2) = 0
    Wait -- that would mean L and R are always orthogonal. Let me recheck.

    <L|R> = conj(cos(t/2))*sin(t/2) + conj(e^{i*phi}*sin(t/2))*(-e^{i*phi}*cos(t/2))
           = cos(t/2)*sin(t/2) + e^{-i*phi}*sin(t/2)*(-e^{i*phi}*cos(t/2))
           = cos(t/2)*sin(t/2) - sin(t/2)*cos(t/2)
           = 0

    So L and R as defined are ALWAYS orthogonal -- they form a complete basis.
    This is itself the key physical result: chiral partners don't overlap.
    The "overlap" quantity of interest is then the PROJECTION overlap when
    we consider a FIXED reference chirality basis versus a rotated one.

    We compute it numerically and verify the orthogonality.
    """
    L = left_weyl(theta, phi)
    R = right_weyl(theta, phi)
    return float(np.abs(inner(L, R))**2)

def chiral_overlap_fixed_ref(theta, phi):
    """
    Overlap of a Bloch-sphere state with the FIXED chiral reference.
    |psi(theta,phi)> = cos(theta/2)|0> + e^{i*phi}*sin(theta/2)|1>

    Left projector onto |0>: P_L = |0><0|
    Right projector onto |1>: P_R = |1><1|

    "Chiral overlap" = probability of BOTH projections being nonzero
    = p_L * p_R = cos^2(theta/2) * sin^2(theta/2) = sin^2(theta)/4

    This is 0 at poles, maximal at equator -- the physically meaningful quantity.
    """
    p_L = np.cos(theta / 2)**2
    p_R = np.sin(theta / 2)**2
    return float(p_L * p_R)

# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    t0 = time.time()

    # --- Test 1: L and R are orthogonal for all (theta, phi) ---
    test_angles = [
        (0, 0), (np.pi/4, 0), (np.pi/2, 0), (np.pi/2, np.pi/4),
        (np.pi, 0), (np.pi/3, np.pi/6), (2.1, 0.7), (0.1, 3.0),
    ]
    ortho_pass = True
    ortho_detail = {}
    for theta, phi in test_angles:
        L = left_weyl(theta, phi)
        R = right_weyl(theta, phi)
        overlap_val = float(np.abs(inner(L, R))**2)
        ok = np.isclose(overlap_val, 0.0, atol=1e-14)
        ortho_detail[f"t={theta:.3f}_p={phi:.3f}"] = {
            "overlap": overlap_val,
            "pass": bool(ok),
        }
        if not ok:
            ortho_pass = False
    results["LR_always_orthogonal"] = {
        "detail": ortho_detail,
        "pass": ortho_pass,
    }

    # --- Test 2: L and R form a complete basis (|L><L| + |R><R| = I) ---
    completeness_pass = True
    completeness_detail = {}
    for theta, phi in test_angles:
        L = left_weyl(theta, phi)
        R = right_weyl(theta, phi)
        proj_sum = L @ L.conj().T + R @ R.conj().T
        ok = np.allclose(proj_sum, np.eye(2), atol=1e-12)
        completeness_detail[f"t={theta:.3f}_p={phi:.3f}"] = {"pass": bool(ok)}
        if not ok:
            completeness_pass = False
    results["LR_completeness"] = {
        "detail": completeness_detail,
        "pass": completeness_pass,
    }

    # --- Test 3: L<->R symmetry of the overlap function ---
    # chiral_overlap_fixed_ref uses cos^2 * sin^2, which is symmetric in (L,R)
    sym_pass = True
    sym_detail = {}
    for theta, phi in test_angles:
        ov = chiral_overlap_fixed_ref(theta, phi)
        # "Swapped" overlap: use (pi - theta) which swaps p_L and p_R
        ov_swap = chiral_overlap_fixed_ref(np.pi - theta, phi)
        ok = np.isclose(ov, ov_swap)
        sym_detail[f"t={theta:.3f}"] = {
            "overlap": ov, "overlap_swapped": ov_swap, "pass": bool(ok),
        }
        if not ok:
            sym_pass = False
    results["LR_symmetry"] = {
        "detail": sym_detail,
        "pass": sym_pass,
    }

    # --- Test 4: Fixed-ref overlap = sin^2(theta)/4 (analytic check) ---
    analytic_pass = True
    analytic_detail = {}
    for theta, phi in test_angles:
        computed = chiral_overlap_fixed_ref(theta, phi)
        analytic = np.sin(theta)**2 / 4.0
        ok = np.isclose(computed, analytic, atol=1e-14)
        analytic_detail[f"t={theta:.3f}"] = {
            "computed": computed, "analytic": float(analytic), "pass": bool(ok),
        }
        if not ok:
            analytic_pass = False
    results["analytic_sin2_over_4"] = {
        "detail": analytic_detail,
        "pass": analytic_pass,
    }

    # --- Test 5: Completeness: p_L + p_R = 1 for any state ---
    comp2_pass = True
    for theta, phi in test_angles:
        p_L = np.cos(theta / 2)**2
        p_R = np.sin(theta / 2)**2
        if not np.isclose(p_L + p_R, 1.0):
            comp2_pass = False
    results["pL_plus_pR_equals_1"] = {"pass": comp2_pass}

    # --- Test 6: Cl(3) chirality cross-validation ---
    # In Cl(3), pseudoscalar I3 = e1*e2*e3 satisfies I3^2 = -1 (odd dim).
    # So (1+I3)/2 are NOT idempotent projectors (that requires gamma^2 = +1).
    # Instead we verify:
    #   a) I3^2 = -1 (correct Cl(3) signature)
    #   b) I3 commutes with all even-grade elements (relevant for chirality)
    #   c) Reflection-based chirality: e3 as the "chirality axis" projector
    #      P_+ = (1 + e3)/2, P_- = (1 - e3)/2 ARE idempotent since e3^2 = +1
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    I3 = e1 * e2 * e3
    one = 1.0 + 0*e1

    # (a) I3^2 = -1
    I3_sq = I3 * I3
    cl3_ps_sq_minus1 = np.allclose(I3_sq.value, (-one).value, atol=1e-12)

    # (b) I3 commutes with bivectors (even subalgebra)
    e12 = e1 * e2
    e23 = e2 * e3
    e13 = e1 * e3
    commutes_12 = np.allclose((I3 * e12).value, (e12 * I3).value, atol=1e-12)
    commutes_23 = np.allclose((I3 * e23).value, (e23 * I3).value, atol=1e-12)
    commutes_13 = np.allclose((I3 * e13).value, (e13 * I3).value, atol=1e-12)
    cl3_commutes_even = commutes_12 and commutes_23 and commutes_13

    # (c) e3-axis projectors (grade-1 reflector, e3^2 = +1)
    P_plus = (one + e3) * 0.5
    P_minus = (one - e3) * 0.5
    Pp_sq = P_plus * P_plus
    Pm_sq = P_minus * P_minus
    Pp_Pm = P_plus * P_minus

    cl3_refl_idem_p = np.allclose(Pp_sq.value, P_plus.value, atol=1e-12)
    cl3_refl_idem_m = np.allclose(Pm_sq.value, P_minus.value, atol=1e-12)
    cl3_refl_ortho = np.allclose(Pp_Pm.value, 0.0, atol=1e-12)
    cl3_refl_complete = np.allclose((P_plus + P_minus).value, one.value, atol=1e-12)

    results["cl3_chirality"] = {
        "I3_sq_is_minus1": bool(cl3_ps_sq_minus1),
        "I3_commutes_with_even": bool(cl3_commutes_even),
        "e3_projector_idempotent_plus": bool(cl3_refl_idem_p),
        "e3_projector_idempotent_minus": bool(cl3_refl_idem_m),
        "e3_projectors_orthogonal": bool(cl3_refl_ortho),
        "e3_projectors_complete": bool(cl3_refl_complete),
        "pass": bool(
            cl3_ps_sq_minus1 and cl3_commutes_even
            and cl3_refl_idem_p and cl3_refl_idem_m
            and cl3_refl_ortho and cl3_refl_complete
        ),
    }

    # --- Test 7: Normalization of L and R ---
    norm_pass = True
    for theta, phi in test_angles:
        L = left_weyl(theta, phi)
        R = right_weyl(theta, phi)
        if not (np.isclose(norm2(L), 1.0) and np.isclose(norm2(R), 1.0)):
            norm_pass = False
    results["LR_normalized"] = {"pass": norm_pass}

    results["elapsed_s"] = time.time() - t0
    return results

# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    t0 = time.time()

    # --- Neg 1: Non-normalized spinors give wrong overlap ---
    theta, phi = np.pi / 3, 0.5
    L = left_weyl(theta, phi) * 2.0   # scale by 2
    R = right_weyl(theta, phi) * 3.0  # scale by 3
    bad_norm_L = norm2(L)
    bad_norm_R = norm2(R)
    # "Overlap" computed naively is no longer a proper probability
    bad_overlap = float(np.abs(inner(L, R))**2)
    # For normalized spinors it's always 0; for non-normalized it's still 0 here
    # because L and R are orthogonal. But the NORMS are wrong.
    results["non_normalized_spinors"] = {
        "norm_L": float(bad_norm_L),
        "norm_R": float(bad_norm_R),
        "L_is_unit": bool(np.isclose(bad_norm_L, 1.0)),
        "R_is_unit": bool(np.isclose(bad_norm_R, 1.0)),
        "pass": bool(not np.isclose(bad_norm_L, 1.0) and not np.isclose(bad_norm_R, 1.0)),
    }

    # --- Neg 2: Non-normalized state in fixed-ref overlap ---
    # If we don't normalize, p_L + p_R != 1
    bad_state = ket([2, 1])  # not normalized
    p_L = float(np.abs(bad_state[0, 0])**2)
    p_R = float(np.abs(bad_state[1, 0])**2)
    total = p_L + p_R
    results["non_normalized_fixed_ref"] = {
        "p_L": p_L,
        "p_R": p_R,
        "sum": total,
        "sums_to_1": bool(np.isclose(total, 1.0)),
        "pass": bool(not np.isclose(total, 1.0)),  # should FAIL normalization
    }

    # --- Neg 3: Non-orthogonal "chiral pair" ---
    # Construct two spinors that are NOT orthogonal and verify they fail completeness
    fake_L = ket([1, 0])
    fake_R = ket([1/np.sqrt(2), 1/np.sqrt(2)])  # |+>, not orthogonal to |0>
    fake_overlap = float(np.abs(inner(fake_L, fake_R))**2)
    fake_proj_sum = fake_L @ fake_L.conj().T + fake_R @ fake_R.conj().T
    fake_complete = np.allclose(fake_proj_sum, np.eye(2))
    results["non_orthogonal_chiral_pair"] = {
        "overlap": fake_overlap,
        "is_orthogonal": bool(np.isclose(fake_overlap, 0.0)),
        "completeness": bool(fake_complete),
        "pass": bool(not np.isclose(fake_overlap, 0.0) and not fake_complete),
    }

    # --- Neg 4: Cl(3) non-projector (wrong normalization) ---
    # Using e3 (which squares to +1), (1+e3)*0.7 is NOT idempotent
    layout, blades = Cl(3)
    e3 = blades["e3"]
    one = 1.0 + 0*e3
    bad_P = (one + e3) * 0.7  # not 0.5 -> not idempotent
    bad_sq = bad_P * bad_P
    is_idempotent = np.allclose(bad_sq.value, bad_P.value, atol=1e-10)
    results["cl3_non_projector"] = {
        "is_idempotent": bool(is_idempotent),
        "pass": bool(not is_idempotent),
    }

    results["elapsed_s"] = time.time() - t0
    return results

# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    t0 = time.time()

    # --- Boundary 1: North pole (theta=0) -> overlap = 0 ---
    ov_north = chiral_overlap_fixed_ref(0, 0)
    results["north_pole"] = {
        "theta": 0,
        "overlap": ov_north,
        "pass": bool(np.isclose(ov_north, 0.0)),
    }

    # --- Boundary 2: South pole (theta=pi) -> overlap = 0 ---
    ov_south = chiral_overlap_fixed_ref(np.pi, 0)
    results["south_pole"] = {
        "theta": float(np.pi),
        "overlap": ov_south,
        "pass": bool(np.isclose(ov_south, 0.0)),
    }

    # --- Boundary 3: Equator (theta=pi/2) -> maximal overlap = 0.25 ---
    phis = [0, np.pi/4, np.pi/2, np.pi, 3*np.pi/2]
    equator_pass = True
    equator_detail = {}
    for phi in phis:
        ov = chiral_overlap_fixed_ref(np.pi / 2, phi)
        ok = np.isclose(ov, 0.25)
        equator_detail[f"phi={phi:.3f}"] = {"overlap": ov, "pass": bool(ok)}
        if not ok:
            equator_pass = False
    results["equator_maximal"] = {
        "expected": 0.25,
        "detail": equator_detail,
        "pass": equator_pass,
    }

    # --- Boundary 4: Full theta sweep (0 to pi) ---
    thetas = np.linspace(0, np.pi, 37)
    sweep_data = []
    sweep_pass = True
    for theta in thetas:
        ov = chiral_overlap_fixed_ref(float(theta), 0.0)
        analytic = float(np.sin(theta)**2 / 4.0)
        ok = np.isclose(ov, analytic, atol=1e-14)
        sweep_data.append({
            "theta": float(theta),
            "overlap": ov,
            "analytic": analytic,
        })
        if not ok:
            sweep_pass = False

    # Verify: max at equator, zero at poles
    overlaps = [d["overlap"] for d in sweep_data]
    max_idx = np.argmax(overlaps)
    max_at_equator = np.isclose(thetas[max_idx], np.pi / 2, atol=np.pi / 36)
    results["theta_sweep"] = {
        "n_points": len(thetas),
        "max_overlap": float(max(overlaps)),
        "max_theta": float(thetas[max_idx]),
        "max_at_equator": bool(max_at_equator),
        "analytic_match": sweep_pass,
        "pass": bool(sweep_pass and max_at_equator),
    }

    # --- Boundary 5: Phi independence of overlap ---
    phi_sweep = np.linspace(0, 2*np.pi, 25)
    theta_test = np.pi / 3
    expected = float(np.sin(theta_test)**2 / 4.0)
    phi_pass = True
    for phi in phi_sweep:
        ov = chiral_overlap_fixed_ref(theta_test, float(phi))
        if not np.isclose(ov, expected, atol=1e-14):
            phi_pass = False
    results["phi_independence"] = {
        "theta": float(theta_test),
        "expected_overlap": expected,
        "all_phi_match": phi_pass,
        "pass": phi_pass,
    }

    results["elapsed_s"] = time.time() - t0
    return results

# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = True
    for section in [positive, negative, boundary]:
        for v in section.values():
            if isinstance(v, dict) and "pass" in v and not v["pass"]:
                all_pass = False

    results = {
        "name": "pure_lego_chiral_overlap",
        "description": "Chiral overlap <L|R> for Weyl spinors: orthogonality, completeness, Cl(3) projectors",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Direct local chiral-overlap baseline on one Weyl-spinor family with Cl(3) cross-validation.",
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_paths = [
        os.path.join(out_dir, "chiral_overlap_results.json"),
        os.path.join(out_dir, "pure_lego_chiral_overlap_results.json"),
    ]
    for out_path in out_paths:
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_paths[0]}")

    # Summary
    for section in ["positive", "negative", "boundary"]:
        for k, v in results[section].items():
            if isinstance(v, dict) and "pass" in v:
                status = "PASS" if v["pass"] else "FAIL"
                if not v["pass"]:
                    all_pass = False
                print(f"  [{section}] {k}: {status}")
    print(f"\nOverall: {'ALL PASS' if all_pass else 'FAILURES DETECTED'}")
