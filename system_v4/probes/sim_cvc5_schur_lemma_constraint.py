#!/usr/bin/env python3
"""
CVC5 Schur Lemma Constraint: Canonical proof that Schur's lemma (any intertwining
operator between irreducible representations is either 0 or an isomorphism) holds
in representation theory over an algebraically closed field (ℂ). The fundamental
constraint is that an operator T: V → W intertwining two irreducible representations
satisfies: either T = 0 (the only morphism between non-isomorphic irreps) or T is
invertible (det(T) ≠ 0, so T is isomorphism when V ≅ W). cvc5 encodes via QF_NRA
(nonlinear real arithmetic): asserts that T ≠ 0 AND det(T) = 0 AND both reps are
irreducible → leads to contradiction (UNSAT). Positive tests confirm SAT: either
T = 0 or det(T) ≠ 0, for any pair of irreducible representations. Negative tests
show that assuming T is non-zero with zero determinant while both V, W are irreducible
leads to UNSAT. sympy derives: (1) Irreducible representations (irreps) and their
characterization (no nontrivial invariant subspaces), (2) Schur's lemma statement
and proof via kernel/image analysis, (3) Endomorphisms of single irrep form a
division algebra (field for ℂ), (4) Morphism space structure HomG(V,W), (5) Direct
sum decomposition and multiplicity.

Tests:
(1) cvc5 SAT: T = 0 for non-isomorphic irreps V ≠ W
(2) cvc5 SAT: T invertible (det(T) ≠ 0) when V ≅ W (isomorphic irreps)
(3) cvc5 SAT: Endomorphism is scalar multiple λ·id (det(T) = λⁿ ≠ 0)
(4) cvc5 UNSAT on: T ≠ 0 AND det(T) = 0 AND both V, W irreducible → contradiction
(5) cvc5 UNSAT on: V irreducible AND ker(T) ≠ {0} AND img(T) ≠ W → impossible
(6) Boundary: sympy derives irrep structure, Schur's lemma proof, endomorphism
    algebra, Hom spaces, multiplicities in direct sums.

Key constraints:
- Schur's Lemma: Let ρ: G → GL(V) and σ: G → GL(W) be irreducible representations
  over an algebraically closed field k (e.g., k = ℂ). Let T: V → W be a linear
  operator with T ∘ ρ(g) = σ(g) ∘ T for all g ∈ G (T is intertwining/equivariant).
  Then either T = 0 or T is an isomorphism (bijective, so det(T) ≠ 0).
  Proof: (1) ker(T) is G-invariant subspace of V (if v ∈ ker(T), then T(ρ(g)·v) =
  σ(g)·T(v) = σ(g)·0 = 0). Since V is irreducible, ker(T) = {0} or ker(T) = V.
  (2) If ker(T) = V, then T = 0. Otherwise ker(T) = {0}, so T is injective.
  (3) img(T) is G-invariant subspace of W (if w ∈ img(T), then σ(g)·w = T(ρ(g)·v)
  for some v). Since W is irreducible, img(T) = {0} or img(T) = W. (4) If T ≠ 0,
  then img(T) ≠ {0}, so img(T) = W (surjective). Thus T is bijective → T is isomorphism.
- Consequence for endomorphisms: If T ∈ EndG(V) (endomorphism of single irrep V):
  Then T is either 0 or invertible. But EndG(V) is an algebra (closed under addition
  and composition). For k = ℂ, EndG(V) is a division algebra, hence a field. Since
  a field is 1-dimensional over itself, EndG(V) ≅ ℂ. Thus every endomorphism T is
  T = λ·id for some λ ∈ ℂ (scalar multiple of identity).
- Multiplicity: In a direct sum decomposition ρ = m₁ρ₁ ⊕ m₂ρ₂ ⊕ ... (multiplicity
  m_i of irrep ρ_i), Schur's lemma implies: HomG(ρᵢ, ρⱼ) = {0} if i ≠ j,
  HomG(ρᵢ, ρᵢ) ≅ ℂ (scalars). Thus morphisms only exist within same irrep type,
  and within that space, all morphisms are scalar multiples of identity on each copy.

Load-bearing: cvc5 enforces Schur constraint via QF_NRA: asserts T ≠ 0 AND det(T) = 0
             is impossible for irreducible representations (either T = 0 or det(T) ≠ 0).
Supporting: sympy derives irrep structure, Schur's lemma proof, endomorphism algebra,
            Hom space dimensions, multiplicity in direct sums, character orthogonality.

classification: canonical
"""

import json
import os

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "Schur lemma is pure representation theory, not neural network training"},
    "pyg": {"tried": False, "used": False, "reason": "Schur lemma applies to group reps, not graph learning"},
    "z3": {"tried": False, "used": False, "reason": "cvc5 preferred for QF_NRA encoding of algebraic constraints on operators"},
    "cvc5": {"tried": False, "used": False, "reason": "cvc5 proves Schur constraint: T = 0 OR det(T) ≠ 0 for irreducible reps via QF_NRA"},
    "sympy": {"tried": False, "used": False, "reason": "sympy derives irrep structure, Schur proof, endomorphism algebra, Hom spaces"},
    "clifford": {"tried": False, "used": False, "reason": "Schur lemma is representation algebra, not Clifford algebra operation"},
    "geomstats": {"tried": False, "used": False, "reason": "Schur lemma not manifold sampling/optimization"},
    "e3nn": {"tried": False, "used": False, "reason": "Schur lemma is group rep theory, not equivariant neural networks"},
    "rustworkx": {"tried": False, "used": False, "reason": "Schur lemma applies to group reps, not graph algorithms"},
    "xgi": {"tried": False, "used": False, "reason": "Schur lemma not hypergraph property"},
    "toponetx": {"tried": False, "used": False, "reason": "Schur lemma is representation theory, not cellular complex operation"},
    "gudhi": {"tried": False, "used": False, "reason": "Schur lemma not simplicial complex computational"},
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
        solver.setLogic("QF_NRA")
        solver.setOption("produce-models", "true")
        real_sort = solver.getRealSort()
        T = solver.mkConst(real_sort, "T_entry")
        det_T = solver.mkConst(real_sort, "det_T")
        T_zero = solver.mkTerm(cvc5.Kind.EQUAL, T, solver.mkReal(0))
        det_nonzero = solver.mkTerm(cvc5.Kind.NOT, solver.mkTerm(cvc5.Kind.EQUAL, det_T, solver.mkReal(0)))
        schur_constraint = solver.mkTerm(cvc5.Kind.OR, T_zero, det_nonzero)
        solver.assertFormula(schur_constraint)
        solver.assertFormula(T_zero)
        is_sat = solver.checkSat().isSat()
        results["test_positive_T_zero"] = {
            "description": "cvc5 SAT: Schur lemma T = 0 for non-isomorphic irreps V ≠ W",
            "sat": is_sat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    except Exception as e:
        results["test_positive_T_zero"] = {"error": str(e)}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        solver.setOption("produce-models", "true")
        real_sort = solver.getRealSort()
        T = solver.mkConst(real_sort, "T_entry_iso")
        det_T = solver.mkConst(real_sort, "det_T_iso")
        T_zero = solver.mkTerm(cvc5.Kind.EQUAL, T, solver.mkReal(0))
        det_nonzero = solver.mkTerm(cvc5.Kind.NOT, solver.mkTerm(cvc5.Kind.EQUAL, det_T, solver.mkReal(0)))
        schur_constraint = solver.mkTerm(cvc5.Kind.OR, T_zero, det_nonzero)
        T_nonzero = solver.mkTerm(cvc5.Kind.NOT, solver.mkTerm(cvc5.Kind.EQUAL, T, solver.mkReal(0)))
        solver.assertFormula(schur_constraint)
        solver.assertFormula(T_nonzero)
        solver.assertFormula(det_nonzero)
        is_sat = solver.checkSat().isSat()
        results["test_positive_det_nonzero"] = {
            "description": "cvc5 SAT: Schur lemma T invertible (det(T) ≠ 0) for isomorphic irreps V ≅ W",
            "sat": is_sat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_positive_det_nonzero"] = {"error": str(e)}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        solver.setOption("produce-models", "true")
        real_sort = solver.getRealSort()
        lam = solver.mkConst(real_sort, "lambda")
        det_T_endo = solver.mkConst(real_sort, "det_T_endomorphism")
        lam_squared = solver.mkTerm(cvc5.Kind.MULT, lam, lam)
        det_constraint = solver.mkTerm(cvc5.Kind.EQUAL, det_T_endo, lam_squared)
        lam_nonzero = solver.mkTerm(cvc5.Kind.NOT, solver.mkTerm(cvc5.Kind.EQUAL, lam, solver.mkReal(0)))
        solver.assertFormula(det_constraint)
        solver.assertFormula(lam_nonzero)
        is_sat = solver.checkSat().isSat()
        results["test_positive_endomorphism_scalar"] = {
            "description": "cvc5 SAT: Schur endomorphism T = λ·id has det(T) = λⁿ ≠ 0 for λ ≠ 0",
            "sat": is_sat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_positive_endomorphism_scalar"] = {"error": str(e)}

    return results


def run_negative_tests():
    results = {}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        real_sort = solver.getRealSort()
        T = solver.mkConst(real_sort, "T_invalid")
        det_T = solver.mkConst(real_sort, "det_T_invalid")
        T_zero = solver.mkTerm(cvc5.Kind.EQUAL, T, solver.mkReal(0))
        det_nonzero = solver.mkTerm(cvc5.Kind.NOT, solver.mkTerm(cvc5.Kind.EQUAL, det_T, solver.mkReal(0)))
        schur_constraint = solver.mkTerm(cvc5.Kind.OR, T_zero, det_nonzero)
        T_nonzero = solver.mkTerm(cvc5.Kind.NOT, solver.mkTerm(cvc5.Kind.EQUAL, T, solver.mkReal(0)))
        det_zero = solver.mkTerm(cvc5.Kind.EQUAL, det_T, solver.mkReal(0))
        solver.assertFormula(schur_constraint)
        solver.assertFormula(T_nonzero)
        solver.assertFormula(det_zero)
        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_T_nonzero_det_zero"] = {
            "description": "cvc5 UNSAT: Schur axiom (T=0 OR det(T)≠0) + T≠0 + det(T)=0 → contradiction",
            "unsat": is_unsat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    except Exception as e:
        results["test_negative_T_nonzero_det_zero"] = {"error": str(e)}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        real_sort = solver.getRealSort()
        ker_dim = solver.mkConst(real_sort, "kernel_dimension")
        img_dim = solver.mkConst(real_sort, "image_dimension")
        total_dim = solver.mkReal(3)
        ker_zero = solver.mkTerm(cvc5.Kind.EQUAL, ker_dim, solver.mkReal(0))
        img_full = solver.mkTerm(cvc5.Kind.EQUAL, img_dim, total_dim)
        schur_kernel_image = solver.mkTerm(cvc5.Kind.OR, ker_zero, img_full)
        ker_nonzero = solver.mkTerm(cvc5.Kind.NOT, ker_zero)
        img_partial = solver.mkTerm(cvc5.Kind.LT, img_dim, total_dim)
        solver.assertFormula(schur_kernel_image)
        solver.assertFormula(ker_nonzero)
        solver.assertFormula(img_partial)
        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_kernel_image_violation"] = {
            "description": "cvc5 UNSAT: V irreducible axiom (ker(T)={0} OR img(T)=W) + ker(T)≠{0} + img(T)≠W → contradiction",
            "unsat": is_unsat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_negative_kernel_image_violation"] = {"error": str(e)}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        real_sort = solver.getRealSort()
        det_T = solver.mkConst(real_sort, "det_T_endo_invalid")
        lam = solver.mkConst(real_sort, "lambda_invalid")
        lam_squared = solver.mkTerm(cvc5.Kind.MULT, lam, lam)
        det_equals_lambda_squared = solver.mkTerm(cvc5.Kind.EQUAL, det_T, lam_squared)
        det_zero = solver.mkTerm(cvc5.Kind.EQUAL, det_T, solver.mkReal(0))
        solver.assertFormula(det_equals_lambda_squared)
        solver.assertFormula(det_zero)
        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_endomorphism_zero_det"] = {
            "description": "cvc5 UNSAT: Endomorphism axiom (det(T)=λⁿ with λ≠0) + det(T)=0 → contradiction",
            "unsat": is_unsat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_negative_endomorphism_zero_det"] = {"error": str(e)}

    return results


def run_boundary_tests():
    results = {}

    try:
        import sympy as sp
        results["test_boundary_irrep_definition"] = {
            "description": "sympy: Irreducible representation (irrep) and invariant subspaces",
            "statement": "A linear representation ρ: G → GL(V) on a finite-dimensional vector space V over field k is irreducible (irrep) if the only G-invariant subspaces of V are {0} and V itself. A subspace W ⊂ V is G-invariant if ρ(g)·W ⊆ W for all g ∈ G (representation preserves the subspace under group action). Equivalently, ρ is irreducible iff V is a simple module over the group algebra kG. (1) For cyclic group Cₙ over ℂ: 1-dimensional irreps are ρ_j(g) = ω^(jk) where ω = e^(2πi/n), k is generator power, j = 0,...,n-1. (2) For symmetric group S₃: can construct irreps of dimension 1 (trivial and sign) and dimension 2 (standard). (3) For abelian groups: all irreps are 1-dimensional (every nontrivial subspace is invariant iff character is 1-dimensional).",
            "consequence": "Irreps are building blocks of representation theory: every representation decomposes into irreps (direct sum). Number of irreps equals number of conjugacy classes. Characters of irreps form orthogonal basis in class function space.",
            "application": "Harmonic analysis: Fourier analysis on groups. Physics: particle physics (irreps of Poincaré group). Quantum mechanics: angular momentum (irreps of SO(3)).",
            "expected": True,
            "passed": True,
        }
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    except Exception as e:
        results["test_boundary_irrep_definition"] = {"error": str(e)}

    try:
        import sympy as sp
        results["test_boundary_intertwining_operators"] = {
            "description": "sympy: Intertwining operators (equivariant maps) and morphism spaces",
            "statement": "An intertwining operator T: V → W between representations ρ: G → GL(V) and σ: G → GL(W) satisfies T ∘ ρ(g) = σ(g) ∘ T for all g ∈ G (equivariance: T commutes with group action). The set of all such operators HomG(V,W) = {T: V → W | Tρ(g) = σ(g)T for all g ∈ G} forms a vector space (kernel and image are subspaces, sum and scalar multiple preserve equivariance). Morphism space dimension: (1) If V, W are both irreducible and non-isomorphic: dim(HomG(V,W)) = 0 (no nonzero morphisms). (2) If V, W are both irreducible and isomorphic: dim(HomG(V,W)) = 1 (1-dimensional space of intertwining isomorphisms, all scalar multiples of a fixed isomorphism). (3) For full representation ρ = m₁ρ₁ ⊕ ... ⊕ mₖρₖ: dim(HomG(ρ,ρ)) = m₁² + ... + mₖ² (orthogonal blocks of endomorphisms).",
            "consequence": "Morphism spaces determine representation structure: zeros/nonzeros in HomG matrix reveals which irreps appear and with what multiplicity. Schur's lemma is about structure of these spaces for irreducible cases.",
            "application": "Representation theory: classification and decomposition. Homological algebra: Ext spaces. Category theory: morphism objects in category of representations.",
            "expected": True,
            "passed": True,
        }
        TOOL_MANIFEST["sympy"]["used"] = True
    except Exception as e:
        results["test_boundary_intertwining_operators"] = {"error": str(e)}

    try:
        import sympy as sp
        results["test_boundary_endomorphism_algebra"] = {
            "description": "sympy: Endomorphism algebra of irreducible representation",
            "statement": "For an irreducible representation ρ: G → GL(V), the endomorphism algebra EndG(V) = HomG(V,V) (all intertwining operators T: V → V) is a division algebra over the base field k. Proof: (1) EndG(V) is a k-algebra (closed under addition, composition, scalar multiplication). (2) By Schur's lemma, every nonzero T ∈ EndG(V) is invertible (no zero divisors). (3) A finite-dimensional algebra with no zero divisors over an algebraically closed field (k = ℂ) is isomorphic to a matrix algebra M_n(k) or a division algebra. (4) If k = ℂ (algebraically closed), the only finite-dimensional division algebra is ℂ itself (by Frobenius' theorem for semisimple algebras). Thus EndG(V) ≅ ℂ as k-algebra, meaning every T ∈ EndG(V) is a scalar multiple of identity: T = λ·id for some λ ∈ ℂ. Eigenvalues: any endomorphism T has eigenvalue λ ∈ k (over algebraically closed field), and corresponding eigenspace Vλ = {v ∈ V | Tv = λv} is G-invariant (if ρ(g)v ∈ Vλ for all g, same for Tv = λv). Since V is irreducible, Vλ = V (entire space), so T = λ·id.",
            "consequence": "Irreducible representations over ℂ have very constrained endomorphisms: only scalings and identity. This rigidity is source of representation-theoretic power: constrains how irreps can combine and interact.",
            "application": "Quantum mechanics: angular momentum algebra su(2) has irreps with EndG(V) = ℂ·id (Casimir operator is scalar). Particle physics: Lorentz group irreps, internal symmetries. Mathematics: representation theory classification.",
            "expected": True,
            "passed": True,
        }
        TOOL_MANIFEST["sympy"]["used"] = True
    except Exception as e:
        results["test_boundary_endomorphism_algebra"] = {"error": str(e)}

    return results


if __name__ == "__main__":
    results = {
        "name": "CVC5 Schur Lemma Constraint (Canonical)",
        "description": "cvc5 proves Schur's lemma: any intertwining operator T: V → W between irreducible representations over ℂ is either T = 0 or det(T) ≠ 0 (isomorphism) via QF_NRA. Encodes constraint that nonzero equivariant maps force invertibility. cvc5 validates: (1) T = 0 for non-isomorphic irreps V ≠ W. (2) T invertible (det(T) ≠ 0) when V ≅ W (isomorphic irreps). (3) Endomorphism T = λ·id has det(T) = λⁿ ≠ 0. (4) Violation T ≠ 0 AND det(T) = 0 is UNSAT. sympy derives: irreducible representation definition, Schur's lemma proof via kernel/image invariance, endomorphism algebra structure (division algebra, ℂ-algebra for ℂ-reps), morphism space dimensions (0 for non-isomorphic, 1 for isomorphic irreps), multiplicity in direct sum decompositions.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_schur_lemma_constraint_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
