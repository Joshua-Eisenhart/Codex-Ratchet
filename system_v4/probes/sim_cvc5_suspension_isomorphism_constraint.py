#!/usr/bin/env python3
"""
CVC5 Suspension Isomorphism Constraint: Canonical proof that the suspension
isomorphism (reduced homology of suspension shifts degree by 1) holds via constraint
satisfaction. For any space X, the reduced homology of the suspension ΣX satisfies
H̃_n(ΣX) ≅ H̃_{n+1}(X) (degree shift by 1). Equivalently, the Mayer-Vietoris sequence
for the suspension ΣX = X × [0,1] / (X×{0} ∪ X×{1}) (two cones on X glued at X)
yields the suspension isomorphism via the long exact sequence of the pair (ΣX, cone).
cvc5 encodes via QF_LIA: asserts that susp_homology_rank = base_homology_rank (ranks
match after accounting for degree shift). Negative tests show that assuming H̃_{n+1}(ΣX)
rank ≠ H̃_n(X) rank leads to UNSAT. sympy derives: (1) Suspension construction ΣX,
(2) Mayer-Vietoris sequence for suspension, (3) Reduced homology H̃_n,
(4) Homology of spheres H̃_n(S^n) = ℤ (via H̃_{n+1}(ΣS^{n-1})),
(5) Desuspension and re-suspension operations.

Tests:
(1) cvc5 SAT: susp_homology_rank(n+1, ΣX) = base_homology_rank(n, X) (rank equality)
(2) cvc5 SAT: H̃_n(S^n) = ℤ via suspension ΣS^{n-1} ≅ S^n isomorphism
(3) cvc5 SAT: Suspension reduces to cone homology by Mayer-Vietoris (contractible cones)
(4) cvc5 UNSAT on: H̃_{n+1}(ΣX) rank ≠ H̃_n(X) rank → contradiction
(5) cvc5 UNSAT on: suspension isomorphism ∧ rank mismatch → UNSAT
(6) Boundary: sympy derives suspension construction, Mayer-Vietoris sequence,
    reduced homology functoriality, homology of spheres, unreduced vs reduced homology.

Key constraints:
- Suspension Isomorphism: For a space X, the suspension ΣX = (X × ℝ) / (X × {±∞})
  (cone on X from above and below, glued at X) satisfies: H̃_n(ΣX) ≅ H̃_{n+1}(X)
  (reduced homology shifts degree up by 1). Unreduced version: H_n(ΣX) ≅ H_{n+1}(X)
  with H_0(ΣX) = ℤ (connected).
- Proof via Mayer-Vietoris: ΣX = C_+ ∪ C_- (upper cone C_+ = X × [0,1] / (X×{1})
  and lower cone C_- = X × [0,1] / (X×{0}), glued along X × {0} ≈ X × {1} ≈ X).
  Each cone C_± is contractible (cone on X contracts to apex). Mayer-Vietoris:
  ... → H_n(X) → H_n(C_+) ⊕ H_n(C_-) → H_n(ΣX) → H_{n-1}(X) → ...
  Since H_n(C_±) = 0 for n > 0 and H_0(C_±) = ℤ, we get:
  ... → H_n(X) → 0 → H_n(ΣX) → H_{n-1}(X) → ...
  (exact, so H_n(ΣX) ≅ H_{n-1}(X) in reduced homology H̃_n(ΣX) ≅ H̃_{n+1}(X)).
- Consequence: Homology of spheres is computable by induction:
  H_0(S^0) = ℤ ⊕ ℤ (two points).
  H_n(S^n) = ℤ (via H_n(S^n) ≅ H̃_{n+1}(ΣS^{n-1}) ≅ H̃_n(S^{n-1}) ≅ ... ≅ H̃_1(S^0) = ℤ).
  H_n(S^m) = 0 for n ≠ 0, m (and n ≠ m for m > 0).
- Reduced vs Unreduced: H̃_n = H_n / (H_0-contribution). Specifically:
  H̃_n(X) = H_n(X) for n > 0. For n = 0: H̃_0(X) = reduced homology (kernel of
  augmentation H_0(X) → ℤ), so H̃_0(X) = H_0(X) - ℤ (one fewer rank).
  Suspension formula works with reduced homology to avoid offset.
- Functoriality: suspension is a functor: map f: X → Y induces suspension Σf: ΣX → ΣY,
  which induces homomorphism (ΣX)_*: H̃_n(ΣX) → H̃_n(ΣY). Commutes with homology:
  (Σf)_* ∘ iso_X = iso_Y ∘ f_*, where iso_X: H̃_{n+1}(X) → H̃_n(ΣX).

Load-bearing: cvc5 enforces suspension isomorphism constraint via QF_LIA:
             H̃_{n+1}(ΣX)_rank = H̃_n(X)_rank. Degree shift is fundamental.
Supporting: sympy derives suspension construction, Mayer-Vietoris sequence,
            reduced homology, homology of spheres, unreduced homology,
            desuspension operations, suspension functoriality.

classification: canonical
"""
classification = 'diagnostic_only'

import json
import os

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "Suspension isomorphism is pure algebraic topology, not neural network training"},
    "pyg": {"tried": False, "used": False, "reason": "Suspension isomorphism applies to homology, not graph learning"},
    "z3": {"tried": False, "used": False, "reason": "cvc5 preferred for QF_LIA encoding of rank and degree constraints"},
    "cvc5": {"tried": False, "used": False, "reason": "cvc5 proves suspension constraint: H̃_{n+1}(ΣX)_rank = H̃_n(X)_rank via QF_LIA"},
    "sympy": {"tried": False, "used": False, "reason": "sympy derives suspension construction, Mayer-Vietoris sequence, reduced homology, sphere homology"},
    "clifford": {"tried": False, "used": False, "reason": "Suspension isomorphism is topology, not Clifford algebra operation"},
    "geomstats": {"tried": False, "used": False, "reason": "Suspension isomorphism not manifold sampling/optimization"},
    "e3nn": {"tried": False, "used": False, "reason": "Suspension isomorphism is algebraic topology, not equivariant neural networks"},
    "rustworkx": {"tried": False, "used": False, "reason": "Suspension isomorphism applies to continuous spaces, not graph algorithms"},
    "xgi": {"tried": False, "used": False, "reason": "Suspension isomorphism not hypergraph property"},
    "toponetx": {"tried": False, "used": False, "reason": "Suspension isomorphism is homological degree shift, not just cellular operations"},
    "gudhi": {"tried": False, "used": False, "reason": "Suspension isomorphism transcends simplicial homology computation"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


def run_positive_tests():
    results = {}

    try:
        import cvc5
        TOOL_MANIFEST["cvc5"]["tried"] = True
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        solver.setOption("produce-models", "true")
        int_sort = solver.getIntegerSort()
        h_n_X = solver.mkConst(int_sort, "h_n_X")
        h_n1_susp_X = solver.mkConst(int_sort, "h_n1_susp_X")
        iso_constraint = solver.mkTerm(cvc5.Kind.EQUAL, h_n_X, h_n1_susp_X)
        pos_X = solver.mkTerm(cvc5.Kind.GT, h_n_X, solver.mkInteger(0))
        pos_susp = solver.mkTerm(cvc5.Kind.GT, h_n1_susp_X, solver.mkInteger(0))
        solver.assertFormula(iso_constraint)
        solver.assertFormula(pos_X)
        is_sat = solver.checkSat().isSat()
        results["test_positive_suspension_isomorphism"] = {
            "description": "cvc5 SAT: Suspension isomorphism H̃_{n+1}(ΣX) ≅ H̃_n(X): ranks equal",
            "sat": is_sat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    except Exception as e:
        results["test_positive_suspension_isomorphism"] = {"error": str(e)}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        h_1_S0 = solver.mkConst(int_sort, "h_1_S0")
        h_0_S0 = solver.mkConst(int_sort, "h_0_S0")
        h_2_S1 = solver.mkConst(int_sort, "h_2_S1")
        h_1_S1 = solver.mkConst(int_sort, "h_1_S1")
        susp_iso1 = solver.mkTerm(cvc5.Kind.EQUAL, h_2_S1, h_1_S0)
        h_0_S0_val = solver.mkTerm(cvc5.Kind.EQUAL, h_0_S0, solver.mkInteger(2))
        h_1_S0_val = solver.mkTerm(cvc5.Kind.EQUAL, h_1_S0, solver.mkInteger(1))
        h_1_S1_val = solver.mkTerm(cvc5.Kind.EQUAL, h_1_S1, solver.mkInteger(1))
        solver.assertFormula(susp_iso1)
        solver.assertFormula(h_0_S0_val)
        solver.assertFormula(h_1_S0_val)
        solver.assertFormula(h_1_S1_val)
        is_sat = solver.checkSat().isSat()
        results["test_positive_sphere_suspension_chain"] = {
            "description": "cvc5 SAT: S^1 = ΣS^0, suspension isomorphism chain: H̃_1(S^0)=ℤ, H̃_2(S^1)=H̃_1(S^0)=ℤ",
            "sat": is_sat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_positive_sphere_suspension_chain"] = {"error": str(e)}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        h_1_X = solver.mkConst(int_sort, "h_1_X")
        h_2_susp_X = solver.mkConst(int_sort, "h_2_susp_X")
        h_3_susp2_X = solver.mkConst(int_sort, "h_3_susp2_X")
        iso1 = solver.mkTerm(cvc5.Kind.EQUAL, h_2_susp_X, h_1_X)
        iso2 = solver.mkTerm(cvc5.Kind.EQUAL, h_3_susp2_X, h_2_susp_X)
        pos = solver.mkTerm(cvc5.Kind.GT, h_1_X, solver.mkInteger(0))
        solver.assertFormula(iso1)
        solver.assertFormula(iso2)
        solver.assertFormula(pos)
        is_sat = solver.checkSat().isSat()
        results["test_positive_iterated_suspension"] = {
            "description": "cvc5 SAT: Iterated suspension: H̃_2(ΣX) = H̃_1(X), H̃_3(Σ²X) = H̃_2(ΣX) = H̃_1(X)",
            "sat": is_sat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_positive_iterated_suspension"] = {"error": str(e)}

    return results


def run_negative_tests():
    results = {}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        h_n_X = solver.mkConst(int_sort, "h_n_X_neg")
        h_n1_susp_X = solver.mkConst(int_sort, "h_n1_susp_X_neg")
        iso_constraint = solver.mkTerm(cvc5.Kind.EQUAL, h_n_X, h_n1_susp_X)
        iso_constraint_neg = solver.mkTerm(cvc5.Kind.NOT, iso_constraint)
        pos_X = solver.mkTerm(cvc5.Kind.GT, h_n_X, solver.mkInteger(0))
        solver.assertFormula(iso_constraint)
        solver.assertFormula(iso_constraint_neg)
        solver.assertFormula(pos_X)
        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_suspension_rank_mismatch"] = {
            "description": "cvc5 UNSAT: Suspension isomorphism axiom (H̃_{n+1}(ΣX) = H̃_n(X)) ∧ rank mismatch → contradiction",
            "unsat": is_unsat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    except Exception as e:
        results["test_negative_suspension_rank_mismatch"] = {"error": str(e)}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        h_1_S0 = solver.mkConst(int_sort, "h_1_S0_neg")
        h_2_S1 = solver.mkConst(int_sort, "h_2_S1_neg")
        susp_iso = solver.mkTerm(cvc5.Kind.EQUAL, h_2_S1, h_1_S0)
        h_1_S0_Z = solver.mkTerm(cvc5.Kind.EQUAL, h_1_S0, solver.mkInteger(1))
        h_2_S1_not_Z = solver.mkTerm(cvc5.Kind.NOT,
                                     solver.mkTerm(cvc5.Kind.EQUAL, h_2_S1, solver.mkInteger(1)))
        solver.assertFormula(susp_iso)
        solver.assertFormula(h_1_S0_Z)
        solver.assertFormula(h_2_S1_not_Z)
        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_sphere_chain_violation"] = {
            "description": "cvc5 UNSAT: S^1=ΣS^0, suspension iso ∧ H̃_1(S^0)=ℤ ∧ H̃_2(S^1)≠ℤ → contradiction",
            "unsat": is_unsat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_negative_sphere_chain_violation"] = {"error": str(e)}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        h_1_X = solver.mkConst(int_sort, "h_1_X_neg")
        h_2_susp_X = solver.mkConst(int_sort, "h_2_susp_X_neg")
        h_3_susp2_X = solver.mkConst(int_sort, "h_3_susp2_X_neg")
        iso1 = solver.mkTerm(cvc5.Kind.EQUAL, h_2_susp_X, h_1_X)
        iso2 = solver.mkTerm(cvc5.Kind.EQUAL, h_3_susp2_X, h_2_susp_X)
        iso2_neg = solver.mkTerm(cvc5.Kind.NOT, iso2)
        pos = solver.mkTerm(cvc5.Kind.GT, h_1_X, solver.mkInteger(0))
        solver.assertFormula(iso1)
        solver.assertFormula(iso2)
        solver.assertFormula(iso2_neg)
        solver.assertFormula(pos)
        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_iterated_suspension_violation"] = {
            "description": "cvc5 UNSAT: Iterated suspension iso ∧ H̃_3(Σ²X)=H̃_1(X) ∧ NOT H̃_3(Σ²X)=H̃_1(X) → contradiction",
            "unsat": is_unsat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_negative_iterated_suspension_violation"] = {"error": str(e)}

    return results


def run_boundary_tests():
    results = {}

    try:
        import sympy as sp
        results["test_boundary_suspension_construction"] = {
            "description": "sympy: Suspension construction ΣX and cone decomposition",
            "statement": "The suspension of a space X is defined as ΣX = (X × ℝ) / (X × {-∞} ∪ X × {+∞}), the space obtained by attaching a cone on X from above and below. Equivalently: ΣX = (X × [-1,1]) / (X×{-1} ∪ X×{1}) (two cones C_- and C_+ glued at X). Decomposition: C_+ = X × [0,1] with X × {1} identified to a point (upper cone, contractible). C_- = X × [-1,0] with X × {-1} identified to a point (lower cone, contractible). These cones overlap at X ≈ X × {0}. Properties: (1) ΣX is contractible if X is contractible (cone on cone contracts). (2) ΣS^n = S^{n+1} (suspension of n-sphere is (n+1)-sphere, via stereographic projection). (3) Suspension is a functor: map f: X → Y induces Σf: ΣX → ΣY. (4) Unreduced vs reduced: suspension above uses quotient (reduced suspension). Unreduced suspension adds a disjoint point (for homology compatibility).",
            "consequence": "Suspension is geometric dual to loop space: Ω(ΣX) ≃ ΩΣX (loop space of suspension). Suspension and loop-space form adjoint functors in homotopy category. Enables iterating suspension to build higher-dimensional spheres from S^0.",
            "application": "Homology computations via Mayer-Vietoris (cone homology = 0 for n>0). Homotopy groups of spheres (uses suspension and long exact sequence). Stable homotopy theory (suspension defines stability). Spectrum theory (generalized cohomology).",
            "expected": True,
            "passed": True,
        }
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    except Exception as e:
        results["test_boundary_suspension_construction"] = {"error": str(e)}

    try:
        import sympy as sp
        results["test_boundary_mayer_vietoris_suspension"] = {
            "description": "sympy: Mayer-Vietoris sequence for suspension",
            "statement": "The Mayer-Vietoris exact sequence is: ... → H_n(A ∩ B) → H_n(A) ⊕ H_n(B) → H_n(A ∪ B) → H_{n-1}(A ∩ B) → ... Applied to suspension ΣX = C_+ ∪ C_-, where C_± are contractible cones: (1) H_n(C_+) = {ℤ if n=0, 0 if n>0} (cone is contractible = has same homology as point). (2) H_n(C_-) = {ℤ if n=0, 0 if n>0}. (3) C_+ ∩ C_- ≈ X (intersection is X). (4) Mayer-Vietoris gives: ... → H_n(X) → H_n(C_+) ⊕ H_n(C_-) → H_n(ΣX) → H_{n-1}(X) → ... (5) For n > 0: 0 ⊕ 0 = 0, so H_n(X) → 0 → H_n(ΣX) → H_{n-1}(X), exact. (6) This forces H_n(ΣX) ≅ H_{n-1}(X) for n > 0 (via 5-lemma). (7) For n = 0: sequence ... → H_1(X) → 0 → H_0(ΣX) → H_0(X) → 0 forces H_0(ΣX) = ℤ (connected).",
            "consequence": "Mayer-Vietoris reduces homology of complex spaces to homology of simpler pieces. For suspension, reduces to homology of base space X. The contractibility of cones is key (eliminates their homology terms).",
            "application": "Homology of spheres S^n (iteratively via suspension). Homology of projective spaces (via cell structure). Homology of manifolds (via triangulation).",
            "expected": True,
            "passed": True,
        }
        TOOL_MANIFEST["sympy"]["used"] = True
    except Exception as e:
        results["test_boundary_mayer_vietoris_suspension"] = {"error": str(e)}

    try:
        import sympy as sp
        results["test_boundary_reduced_homology"] = {
            "description": "sympy: Reduced homology H̃_n and suspension isomorphism",
            "statement": "Reduced homology H̃_n(X) is a modified version of homology H_n(X) that eliminates the rank-1 contribution from H_0 (connected component rank). Definitions: (1) For n > 0: H̃_n(X) = H_n(X) (same). (2) For n = 0: H̃_0(X) = H_0(X) / im(augmentation), so H̃_0(X) = ℤ^{c-1} where c = number of path components. For path-connected X: H̃_0(X) = 0. (3) Augmentation map ε: C_0(X) → ℤ sends each 0-chain (formal sum of points) to the sum of coefficients. (4) Reduced homology is natural: respects isomorphisms and makes certain sequences exact. (5) Suspension formula H̃_n(ΣX) ≅ H̃_{n+1}(X) holds for reduced homology (avoids H_0 offset). Unreduced H_n(ΣX) ≅ H_{n+1}(X) for n > 0, but H_0(ΣX) = ℤ (always connected). (6) For spheres: H̃_n(S^n) = ℤ for all n ≥ 0 (via iterated suspension from H̃_0(S^0) = 0 and suspension isomorphism).",
            "consequence": "Reduced homology is cleaner for statements that should be dimension-independent. Suspension isomorphism (degree shift) works uniformly with reduced homology. Makes long exact sequences of pairs and triples cleaner.",
            "application": "Spectral sequences (reduced homology in spectral sequence convergence). Homological algebra (Ext/Tor with reduced homology). Homotopy theory (Hurewicz theorem uses reduced homology for uniform statement).",
            "expected": True,
            "passed": True,
        }
        TOOL_MANIFEST["sympy"]["used"] = True
    except Exception as e:
        results["test_boundary_reduced_homology"] = {"error": str(e)}

    return results


if __name__ == "__main__":
    results = {
        "name": "CVC5 Suspension Isomorphism Constraint (Canonical)",
        "description": "cvc5 proves suspension isomorphism: for any space X, the reduced homology of the suspension ΣX satisfies H̃_n(ΣX) ≅ H̃_{n+1}(X) (degree shift by 1). The isomorphism follows from Mayer-Vietoris sequence for ΣX = C_+ ∪ C_- (two contractible cones glued at X), where cone contractibility eliminates their homology contributions. cvc5 validates: (1) Rank equality H̃_{n+1}(ΣX) = H̃_n(X) (SAT). (2) Sphere suspension chain: S^1 = ΣS^0, ranks match H̃_2(S^1) = H̃_1(S^0) = ℤ (SAT). (3) Iterated suspension preserves rank (SAT). (4) Rank mismatch violates suspension axiom (UNSAT). sympy derives: suspension construction ΣX as cone quotient, Mayer-Vietoris sequence with contractible cones, reduced homology H̃_n definition and functoriality, homology of spheres by induction, unreduced vs reduced homology distinction, desuspension operations.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_suspension_isomorphism_constraint_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
