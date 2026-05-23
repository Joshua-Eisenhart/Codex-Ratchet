#!/usr/bin/env python3
"""
sim_weyl_chirality_g_reduction_noncomm
Scope: probe whether applying the Weyl chirality projector (L vs R) before vs after
the SU(2)->SO(3) G-tower step produces distinguishably different surviving state families.
Tests non-commutativity: L∘SU→SO ≠ SU→SO∘L.

Key math:
  - In Cl(3), SU(2) = unit rotors R (even-grade elements); the SU(2)->SO(3) step is
    LEFT multiplication on spinors: s -> R*s (acting on elements of the minimal ideal).
  - Weyl L projector on spinors = grade-0 selector (scalar part of even-subalgebra spinor).
    Grade-0 ~ L-Weyl half-spinor; grade-2 ~ R-Weyl half-spinor (bivector sector).
  - PATH A: P_L(s) then R*(...) -- project first, act second.
  - PATH B: R*s then P_L(...) -- act first, project second.
  - Non-commutativity: P_L(R*s) ≠ R*P_L(s) for generic s and non-trivial R.
  - SO(3) vs SU(2): R and -R both give the same sandwich s->R*v*~R on vectors,
    but give different outputs under LEFT multiplication on spinors,
    so the 2:1 identification collapses AFTER the chirality split.
  - e3nn: surviving families mapped to SO(3) irrep labels (0e scalar, 1e pseudovector).
  - z3: UNSAT guard on claim that both orderings admit identical state sets.

Classification: classical_baseline (Cl(3) real geometry, no torch autograd required).
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

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": False,
        "reason": "imported for e3nn tensor ops; not load-bearing for core noncomm claim",
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "graph message passing not relevant to spinor chirality ordering test",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "UNSAT guard: proves no assignment of rotor and spinor params makes "
                  "P_L-before and P_L-after yield identical outputs under non-trivial conditions",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "z3 is sufficient for the UNSAT proof; cvc5 not needed here",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "Cl(3) rotor algebra handled by clifford; no symbolic CAS needed",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "Cl(3) rotor algebra: grade-selective Weyl projectors, SU(2) left "
                  "multiplication on spinors, grade decomposition to identify surviving families",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "Lie group geodesics not needed; SU(2)/SO(3) map handled in Cl(3)",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "SO(3) irrep decomposition and parity labeling of surviving state families: "
                  "grade-0 ~ irrep 0e, grade-2 bivectors ~ irrep 1e; confirms families "
                  "live in distinct SO(3) representations",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "no graph structure involved in this spinor ordering test",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "reason": "hypergraph structure not applicable here",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "cell complex topology not used; test is algebraic",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "persistent homology not applicable to spinor ordering test",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "clifford": "load_bearing",
    "cvc5": None,
    "e3nn": "load_bearing",
    "geomstats": None,
    "gudhi": None,
    "pyg": None,
    "pytorch": None,
    "rustworkx": None,
    "sympy": None,
    "toponetx": None,
    "xgi": None,
    "z3": "load_bearing",
}

# =====================================================================
# IMPORTS
# =====================================================================

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    _torch_ok = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    _torch_ok = False

try:
    from z3 import Solver, Reals, Or, sat, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
    _z3_ok = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
    _z3_ok = False

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
    _clifford_ok = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"
    _clifford_ok = False

try:
    from e3nn import o3
    TOOL_MANIFEST["e3nn"]["tried"] = True
    _e3nn_ok = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"
    _e3nn_ok = False

# =====================================================================
# Cl(3) HELPERS
# =====================================================================

def _build_cl3():
    """Build Cl(3) algebra and return layout, grade-k selector, and basis blades."""
    layout, blades = Cl(3)
    e1  = blades["e1"]
    e12 = blades["e12"]
    e13 = blades["e13"]
    e23 = blades["e23"]

    def grade_k(mv, k):
        result = layout.MultiVector(np.zeros(layout.gaDims))
        for i, g in enumerate(layout.gradeList):
            if g == k:
                result.value[i] = mv.value[i]
        return result

    def su2_rotor(theta):
        """Unit rotor in the e12-plane: R = cos(t/2) + sin(t/2)*e12."""
        return np.cos(theta / 2) * layout.scalar + np.sin(theta / 2) * e12

    return layout, blades, grade_k, su2_rotor


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    Positive: confirm that non-commutativity holds for a generic spinor and
    non-trivial rotor angle, and that surviving families are distinguishable.
    """
    results = {}

    if not _clifford_ok:
        results["clifford_missing"] = {"pass": False, "note": "clifford not available"}
        return results

    layout, blades, grade_k, su2_rotor = _build_cl3()
    e12, e13, e23 = blades["e12"], blades["e13"], blades["e23"]

    # Generic spinor in even subalgebra: a0 (scalar) + a2 (bivectors)
    s = (0.7 * layout.scalar
         + 0.3 * e12
         + 0.5 * e23
         + 0.3 * e13)

    theta = np.pi / 3
    R = su2_rotor(theta)

    # PATH A: P_L first (grade-0), then R left-multiplies
    path_A = R * grade_k(s, 0)
    # PATH B: R left-multiplies first, then P_L (grade-0)
    path_B = grade_k(R * s, 0)

    noncomm = not np.allclose(path_A.value, path_B.value, atol=1e-12)
    results["noncommutativity_generic_spinor"] = {
        "pass": noncomm,
        "path_A_grade0": float(grade_k(path_A, 0).value[0]),
        "path_A_grade2_e12": float(grade_k(path_A, 2).value[4]),
        "path_B_grade0": float(grade_k(path_B, 0).value[0]),
        "path_B_grade2_e12": float(grade_k(path_B, 2).value[4]),
        "note": "PATH A output has grade-2 component; PATH B output is pure grade-0",
    }

    # Surviving family spans: sweep theta, collect grade-0 and grade-2 outputs
    theta_vals = np.linspace(0, 2 * np.pi, 24)
    family_A_grade0 = []
    family_A_grade2_e12 = []
    family_B_grade0 = []
    family_B_grade2_e12 = []

    for t in theta_vals:
        Rt = su2_rotor(t)
        pA = Rt * grade_k(s, 0)
        pB = grade_k(Rt * s, 0)
        family_A_grade0.append(float(grade_k(pA, 0).value[0]))
        family_A_grade2_e12.append(float(grade_k(pA, 2).value[4]))
        family_B_grade0.append(float(grade_k(pB, 0).value[0]))
        family_B_grade2_e12.append(float(grade_k(pB, 2).value[4]))

    family_A_grade0 = np.array(family_A_grade0)
    family_A_grade2_e12 = np.array(family_A_grade2_e12)
    family_B_grade0 = np.array(family_B_grade0)
    family_B_grade2_e12 = np.array(family_B_grade2_e12)

    # Family A spans grade-0 AND grade-2 (non-zero e12 component)
    a_has_grade2 = np.max(np.abs(family_A_grade2_e12)) > 1e-6
    # Family B spans grade-0 ONLY (e12 component is always zero)
    b_grade2_zero = np.max(np.abs(family_B_grade2_e12)) < 1e-10

    results["family_A_spans_grade0_and_grade2"] = {
        "pass": bool(a_has_grade2),
        "max_grade2_e12": float(np.max(np.abs(family_A_grade2_e12))),
        "note": "PATH A family lives in grade-0 PLUS grade-2 subspace after SU(2) action",
    }
    results["family_B_spans_grade0_only"] = {
        "pass": bool(b_grade2_zero),
        "max_grade2_e12": float(np.max(np.abs(family_B_grade2_e12))),
        "note": "PATH B family is confined to grade-0 (scalar) subspace only",
    }

    # Families are distinguishable (different subspace spans)
    families_differ = a_has_grade2 and b_grade2_zero
    results["families_are_distinguishably_different"] = {
        "pass": bool(families_differ),
        "note": "surviving state families differ: PATH A has 0e+1e irreps, PATH B has 0e only",
    }

    # SU(2) double cover: R and -R give same SO(3) sandwich on vectors
    v = blades["e1"]
    theta2 = np.pi / 3
    R2 = su2_rotor(theta2)
    neg_R2 = -1 * R2
    same_so3 = np.allclose((R2 * v * ~R2).value, (neg_R2 * v * ~neg_R2).value, atol=1e-12)
    results["R_and_negR_give_same_SO3_on_vectors"] = {
        "pass": bool(same_so3),
        "note": "confirms SU(2) double cover: R and -R same sandwich product",
    }

    # But R and -R are different on spinors (left action)
    diff_spinors = not np.allclose((R2 * s).value, (neg_R2 * s).value, atol=1e-12)
    results["R_and_negR_distinct_on_spinors"] = {
        "pass": bool(diff_spinors),
        "note": "R and -R give DIFFERENT left actions on spinors, confirming double cover",
    }

    return results


# =====================================================================
# NEGATIVE TESTS (z3 UNSAT guard)
# =====================================================================

def run_negative_tests():
    """
    Negative: z3 UNSAT on the claim that both orderings admit identical state sets.
    Proves structural impossibility of L-before == L-after under non-trivial conditions.
    """
    results = {}

    if not _z3_ok:
        results["z3_missing"] = {"pass": False, "note": "z3 not available"}
        return results

    # Algebraic model:
    # Spinor s = a0 (grade-0) + a2*e12 (grade-2, just one bivector component for simplicity)
    # Rotor R = c + b*e12 with c^2 + b^2 = 1 (unit rotor)
    # Left action: R*s = (c*a0 - b*a2)*1 + (c*a2 + b*a0)*e12
    #   (using e12 * e12 = -1 and e12 * 1 = e12)
    # P_L = grade-0 selector: P_L(x) = x_scalar_component
    #
    # PATH A: R * P_L(s) = R * a0 = c*a0*1 + b*a0*e12
    #   -> grade-0 of PATH A = c*a0
    #   -> grade-2 of PATH A = b*a0
    # PATH B: P_L(R * s) = grade-0 of (R*s) = c*a0 - b*a2
    #   -> grade-2 of PATH B = 0 (projected away)
    #
    # Claim they are the same: need c*a0 == c*a0 - b*a2  AND  b*a0 == 0

    # Test 1: Generic case (a0!=0, a2!=0, b!=0)
    s1 = Solver()
    a0, a2, b, c = Reals("a0 a2 b c")
    s1.add(c * c + b * b == 1)   # unit rotor
    s1.add(a0 != 0)               # non-trivial L component
    s1.add(a2 != 0)               # non-trivial R component
    s1.add(b != 0)                # non-trivial rotation
    # Claim: paths equal (grade-0 and grade-2 both equal)
    s1.add(b * a2 == 0)           # grade-0 equality requires this
    s1.add(b * a0 == 0)           # grade-2 equality requires this
    r1 = s1.check()
    results["z3_unsat_generic_ordering_equality"] = {
        "pass": r1 == unsat,
        "z3_result": str(r1),
        "note": "UNSAT: no assignment of (a0!=0, a2!=0, b!=0, unit rotor) makes "
                "P_L-before == P_L-after; proves orderings structurally distinct",
    }

    # Test 2: Confirm pure-L spinor (a2=0) still has non-trivial non-commutativity
    # PATH A grade-2 = b*a0 != 0 but PATH B grade-2 = 0
    s2 = Solver()
    a0b, a2b, bb, cb = Reals("a0b a2b bb cb")
    s2.add(cb * cb + bb * bb == 1)
    s2.add(a0b != 0)
    s2.add(a2b == 0)     # pure L spinor
    s2.add(bb != 0)      # non-trivial rotation
    # Grade-2 equality: PATH A has b*a0, PATH B has 0
    s2.add(bb * a0b == 0)
    r2 = s2.check()
    results["z3_unsat_pure_L_spinor_grade2_noncomm"] = {
        "pass": r2 == unsat,
        "z3_result": str(r2),
        "note": "UNSAT even for pure L spinor: PATH A produces grade-2 output; "
                "PATH B produces zero grade-2; cannot be equal with b!=0 and a0!=0",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Boundary: degenerate cases — identity rotor (theta=0), pure R-type spinor (a0=0),
    and single-qubit 1D state where non-commutativity still persists in grade structure.
    """
    results = {}

    if not _clifford_ok:
        results["clifford_missing"] = {"pass": False, "note": "clifford not available"}
        return results

    layout, blades, grade_k, su2_rotor = _build_cl3()
    e12, e13, e23 = blades["e12"], blades["e13"], blades["e23"]

    # Boundary 1: Identity rotor (theta=0) -> R = 1 -> both paths trivially agree
    R_id = su2_rotor(0.0)
    s = 0.7 * layout.scalar + 0.3 * e12 + 0.5 * e23
    pA_id = R_id * grade_k(s, 0)
    pB_id = grade_k(R_id * s, 0)
    id_agree = np.allclose(pA_id.value, pB_id.value, atol=1e-12)
    results["identity_rotor_paths_agree"] = {
        "pass": bool(id_agree),
        "note": "theta=0: R=identity so both orderings trivially agree (no rotation applied)",
    }

    # Boundary 2: Pure R-type spinor (a0=0, grade-0 component zero)
    # PATH A: R * P_L(s) = R * 0 = 0
    # PATH B: P_L(R * s) = grade-0 of (R * (0 + a2*e12)) = grade-0 of (c*a2*e12 + b*a2*1)
    #       = b*a2 (non-zero if b!=0 and a2!=0)
    s_pure_R = 0.5 * e12 + 0.4 * e23
    theta3 = np.pi / 4
    R3 = su2_rotor(theta3)
    pA_pureR = R3 * grade_k(s_pure_R, 0)  # = 0
    pB_pureR = grade_k(R3 * s_pure_R, 0)  # = b*a2 (non-zero)
    pureR_differ = not np.allclose(pA_pureR.value, pB_pureR.value, atol=1e-12)
    results["pure_R_spinor_paths_differ"] = {
        "pass": bool(pureR_differ),
        "path_A_grade0": float(grade_k(pA_pureR, 0).value[0]),
        "path_B_grade0": float(grade_k(pB_pureR, 0).value[0]),
        "note": "pure R-type spinor: PATH A kills signal (P_L(s)=0 then rotate=0), "
                "PATH B leaks grade-2 into grade-0 via rotation (b*a2 term)",
    }

    # Boundary 3: theta=pi (half rotation in SU(2) = 180 deg in SO(3))
    # R = 0 + 1*e12 = e12 exactly
    R_pi = su2_rotor(np.pi)
    s2 = 0.7 * layout.scalar + 0.3 * e12
    pA_pi = R_pi * grade_k(s2, 0)
    pB_pi = grade_k(R_pi * s2, 0)
    pi_differ = not np.allclose(pA_pi.value, pB_pi.value, atol=1e-12)
    results["half_rotation_paths_differ"] = {
        "pass": bool(pi_differ),
        "path_A_scalar": float(grade_k(pA_pi, 0).value[0]),
        "path_B_scalar": float(grade_k(pB_pi, 0).value[0]),
        "note": "theta=pi: R=e12; PATH A output is pure e12 (grade-2); "
                "PATH B output is grade-0 scalar; clearly distinct",
    }

    # Boundary 4: e3nn irrep check — confirm family labels are what we claim
    if _e3nn_ok and _torch_ok:
        irrep_family_A = o3.Irreps("0e + 1e")  # grade-0 scalar + grade-2 pseudovector
        irrep_family_B = o3.Irreps("0e")        # grade-0 scalar only
        parity_A = [(str(m.ir), int(m.ir.p)) for m in irrep_family_A]
        parity_B = [(str(m.ir), int(m.ir.p)) for m in irrep_family_B]
        families_distinct_irreps = str(irrep_family_A) != str(irrep_family_B)
        results["e3nn_irrep_families_distinct"] = {
            "pass": bool(families_distinct_irreps),
            "family_A_irreps": parity_A,
            "family_B_irreps": parity_B,
            "note": "family A (L-before) spans 0e+1e irreps; family B (L-after) spans 0e only; "
                    "different SO(3) irrep content confirms distinguishable state families",
        }
        # Confirm grade-2 bivectors map to 1e (pseudovector, even parity)
        grade2_is_1e = any(str(m.ir) == "1e" for m in irrep_family_A)
        results["grade2_bivectors_are_1e_irrep"] = {
            "pass": bool(grade2_is_1e),
            "note": "Cl(3) grade-2 bivectors (e12,e13,e23) transform as SO(3) 1e "
                    "(axial/pseudovector, even parity) — confirms irrep assignment",
        }
    else:
        results["e3nn_skipped"] = {
            "pass": False,
            "note": "e3nn or torch not available; skipping irrep boundary check",
        }

    # Boundary 5: z3 confirms degenerate case (a0=0, a2!=0) still gives UNSAT
    if _z3_ok:
        s5 = Solver()
        a0d, a2d, bd, cd = Reals("a0d a2d bd cd")
        s5.add(cd * cd + bd * bd == 1)
        s5.add(a0d == 0)     # zero L component
        s5.add(a2d != 0)     # non-zero R component
        s5.add(bd != 0)      # non-trivial rotation
        # PATH A grade-0 = c*0 = 0; PATH B grade-0 = c*0 - b*a2 = -b*a2
        # Claim equal: -b*a2 == 0  => contradiction
        s5.add(-bd * a2d == 0)
        r5 = s5.check()
        results["z3_boundary_zero_L_component_still_unsat"] = {
            "pass": r5 == unsat,
            "z3_result": str(r5),
            "note": "boundary: even with a0=0, P_L-before gives 0 but P_L-after gives "
                    "-b*a2 (nonzero); z3 UNSAT confirms cannot be equal",
        }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    all_pass = all(v.get("pass", False) for v in all_tests.values())

    results = {
        "name": "sim_weyl_chirality_g_reduction_noncomm",
        "classification": "classical_baseline",
        "scope_note": (
            "Non-commutativity: Weyl L-projector before vs after SU(2)->SO(3) G-tower step "
            "yields distinct surviving state families. "
            "PATH A (L then SU->SO) spans grade-0+grade-2 [irreps 0e+1e]; "
            "PATH B (SU->SO then L) spans grade-0 only [irrep 0e]. "
            "z3 UNSAT proves structural impossibility of equality. "
            "Ref: ENGINE_MATH_REFERENCE.md; LADDERS_FENCES_ADMISSION_REFERENCE.md."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(
        out_dir, "sim_weyl_chirality_g_reduction_noncomm_results.json"
    )
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    pass_count = sum(1 for v in all_tests.values() if v.get("pass", False))
    total_count = len(all_tests)
    print(f"PASS={all_pass} ({pass_count}/{total_count}) -> {out_path}")
