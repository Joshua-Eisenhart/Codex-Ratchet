#!/usr/bin/env python3
"""
sim_mutual_information_monotone_canonical.py

Canonical proof sim: Quantum mutual information I(A;B) ≥ 0 and I_c ≤ I(A;B).

Key relationships:
  I(A;B) = S(A) + S(B) - S(AB)          (quantum mutual information)
  I_c(A;B) = S(A) - S(AB)               (coherent information)
  Relation: I(A;B) = I_c(A;B) + S(B)
  Consequence: I_c ≤ I(A;B)  iff  S(B) ≥ 0  (always true)
  For pure bipartite states: I(A;B) = 2*S(A)

Step 6 bridge prerequisites:
  - I(A;B) ≥ 0 always (from strong subadditivity: S(A)+S(B) ≥ S(AB))
  - I_c(A;B) ≤ I(A;B) always (since S(B) ≥ 0)

classification: canonical
"""

import json
import math
import os

classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "clifford": None,
    "cvc5": "load_bearing",
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "pyg": None,
    "pytorch": "load_bearing",
    "rustworkx": None,
    "sympy": "load_bearing",
    "toponetx": None,
    "xgi": None,
    "z3": "load_bearing",
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Load-bearing: random density matrix generation via Ginibre ensemble, "
        "partial trace via einsum, von Neumann entropy via eigvalsh, Schmidt "
        "decomposition for pure state identity I(A;B)=2*S(A), Bell state boundary checks."
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    import z3
    from z3 import Real, Solver, And, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "Load-bearing: P3 UNSAT proof that I(A;B)<0 is structurally impossible "
        "(strong subadditivity axiom encoded as linear constraint); "
        "N1 UNSAT proof that I_c > I(A;B) forces S(B)<0 which contradicts S(B)>=0."
    )
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5 as _cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = (
        "Load-bearing: N2 independent cross-check of I(A;B)>=0 via strong subadditivity "
        "in QF_LRA logic, confirming z3 result with separate solver."
    )
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "Load-bearing: symbolic derivation of I(A;B) = I_c + S(B) relation, "
        "and pure-state identity I(A;B) = 2*S(A) when S(AB)=0."
    )
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# HELPERS (pytorch)
# =====================================================================

def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log rho), natural log."""
    eigvals = torch.linalg.eigvalsh(rho).real
    eigvals = eigvals.clamp(min=1e-12)
    return -(eigvals * torch.log(eigvals)).sum().real.item()


def partial_trace(rho_AB, dA, dB, keep):
    """Partial trace. keep='A' -> rho_A, keep='B' -> rho_B."""
    rho = rho_AB.reshape(dA, dB, dA, dB)
    if keep == 'A':
        return torch.einsum('ikjk->ij', rho)
    else:
        return torch.einsum('ikil->kl', rho)


def random_density_matrix(d, seed=None):
    """Random d x d density matrix via Ginibre ensemble."""
    if seed is not None:
        torch.manual_seed(seed)
    G = torch.randn(d, d, dtype=torch.float64) + 1j * torch.randn(d, d, dtype=torch.float64)
    rho = G @ G.conj().T
    rho = rho / rho.trace()
    return rho


def mutual_information(rho_AB, dA, dB):
    """I(A;B) = S(A) + S(B) - S(AB)."""
    rho_A = partial_trace(rho_AB, dA, dB, 'A')
    rho_B = partial_trace(rho_AB, dA, dB, 'B')
    return (von_neumann_entropy(rho_A)
            + von_neumann_entropy(rho_B)
            - von_neumann_entropy(rho_AB))


def coherent_information(rho_AB, dA, dB):
    """I_c(A;B) = S(A) - S(AB)."""
    rho_A = partial_trace(rho_AB, dA, dB, 'A')
    return von_neumann_entropy(rho_A) - von_neumann_entropy(rho_AB)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # ------------------------------------------------------------------
    # P1: I(A;B) >= 0 for 20 random density matrices (pytorch numerical sweep)
    # ------------------------------------------------------------------
    dA, dB = 2, 2
    p1_violations = []
    for i in range(20):
        rho_AB = random_density_matrix(dA * dB, seed=i)
        mi = mutual_information(rho_AB, dA, dB)
        if mi < -1e-8:
            p1_violations.append({"trial": i, "I_AB": mi})
    results["P1_MI_nonnegative_random_sweep"] = {
        "pass": len(p1_violations) == 0,
        "n_trials": 20,
        "violations": p1_violations,
        "note": "I(A;B) = S(A)+S(B)-S(AB) >= 0 for 20 random 4x4 density matrices"
    }

    # ------------------------------------------------------------------
    # P2: I(A;B) = 2*S(A) for pure bipartite states (Schmidt decomposition)
    # ------------------------------------------------------------------
    # For a pure state |psi>_AB: S(AB)=0, S(A)=S(B) (Schmidt).
    # So I(A;B) = S(A) + S(B) - 0 = 2*S(A).
    p2_results = {}
    # Test several pure states with different Schmidt ranks/coefficients
    test_pure_states = [
        # Bell state (maximally entangled)
        torch.tensor([1, 0, 0, 1], dtype=torch.complex128) / math.sqrt(2),
        # Partially entangled: sqrt(0.8)|00> + sqrt(0.2)|11>
        torch.tensor([math.sqrt(0.8), 0, 0, math.sqrt(0.2)], dtype=torch.complex128),
        # Product state |00>
        torch.tensor([1, 0, 0, 0], dtype=torch.complex128),
    ]
    labels = ["bell_state", "partial_entangle_0.8_0.2", "product_00"]
    for lbl, psi in zip(labels, test_pure_states):
        rho_AB = torch.outer(psi, psi.conj())
        rho_A = partial_trace(rho_AB, 2, 2, 'A')
        S_AB = von_neumann_entropy(rho_AB)
        S_A = von_neumann_entropy(rho_A)
        mi = mutual_information(rho_AB, 2, 2)
        expected = 2 * S_A
        p2_results[lbl] = {
            "S_AB": S_AB,
            "S_A": S_A,
            "I_AB": mi,
            "expected_2SA": expected,
            "diff": abs(mi - expected),
            "pass": abs(S_AB) < 1e-6 and abs(mi - expected) < 1e-6,
        }
    results["P2_pure_state_MI_equals_2SA"] = {
        "pass": all(v["pass"] for v in p2_results.values()),
        "cases": p2_results,
        "note": "For pure |psi>_AB: S(AB)=0 and I(A;B)=2*S(A) via Schmidt symmetry"
    }

    # ------------------------------------------------------------------
    # P3: z3 UNSAT — I(A;B) < 0 is structurally impossible
    # Strong subadditivity (SSA) implies S(A)+S(B) >= S(AB),
    # so I(A;B) = S(A)+S(B)-S(AB) >= 0. Encoding violation as UNSAT.
    # ------------------------------------------------------------------
    p3_result = {"pass": False, "z3_status": "", "note": ""}
    try:
        s = Solver()
        SA = Real('S_A')
        SB = Real('S_B')
        SAB = Real('S_AB')
        IAB = Real('I_AB')
        # Entropy non-negativity axioms
        s.add(SA >= 0, SB >= 0, SAB >= 0)
        # Strong subadditivity (simplified for bipartite): S(A) + S(B) >= S(AB)
        # This is subadditivity — a weaker form of SSA but sufficient here.
        # Full SSA: S(A)+S(C) >= S(AB)+S(BC) for tripartite. For bipartite,
        # S(A)+S(B) >= S(AB) follows from subadditivity (standard quantum axiom).
        s.add(SA + SB >= SAB)
        # I(A;B) = S(A) + S(B) - S(AB)
        s.add(IAB == SA + SB - SAB)
        # Violation: I(A;B) < 0 => S(A)+S(B)-S(AB) < 0 => S(AB) > S(A)+S(B)
        # But that contradicts the subadditivity constraint above.
        s.add(IAB < 0)
        status = s.check()
        p3_result["z3_status"] = str(status)
        if status == unsat:
            p3_result["pass"] = True
            p3_result["note"] = (
                "UNSAT: I(A;B)<0 requires S(AB)>S(A)+S(B), "
                "which contradicts subadditivity S(A)+S(B)>=S(AB)"
            )
        else:
            p3_result["note"] = f"Expected UNSAT, got {status}"
    except Exception as e:
        p3_result["note"] = f"z3 error: {e}"
    results["P3_z3_MI_negative_impossible"] = p3_result

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # ------------------------------------------------------------------
    # N1: z3 UNSAT — I_c > I(A;B) is structurally impossible
    # Since I(A;B) = I_c + S(B) and S(B) >= 0, I_c <= I(A;B).
    # Violation I_c > I(A;B) => I_c > I_c + S(B) => S(B) < 0. UNSAT.
    # ------------------------------------------------------------------
    n1_result = {"pass": False, "z3_status": "", "note": ""}
    try:
        s = Solver()
        SA = Real('S_A')
        SB = Real('S_B')
        SAB = Real('S_AB')
        Ic = Real('I_c')
        IAB = Real('I_AB')
        # Axioms
        s.add(SA >= 0, SB >= 0, SAB >= 0)
        # Definitions
        s.add(Ic == SA - SAB)
        s.add(IAB == SA + SB - SAB)
        # Violation: I_c > I(A;B)
        # => SA - SAB > SA + SB - SAB
        # => 0 > SB
        # But SB >= 0 above. UNSAT.
        s.add(Ic > IAB)
        status = s.check()
        n1_result["z3_status"] = str(status)
        if status == unsat:
            n1_result["pass"] = True
            n1_result["note"] = (
                "UNSAT: I_c > I(A;B) requires S(B)<0, "
                "which contradicts entropy non-negativity S(B)>=0. "
                "Since I(A;B) = I_c + S(B) and S(B)>=0, I_c <= I(A;B) always."
            )
        else:
            n1_result["note"] = f"Expected UNSAT, got {status}"
    except Exception as e:
        n1_result["note"] = f"z3 error: {e}"
    results["N1_z3_Ic_gt_MI_impossible"] = n1_result

    # ------------------------------------------------------------------
    # N2: cvc5 cross-check — I(A;B) >= 0 via subadditivity (independent solver)
    # ------------------------------------------------------------------
    n2_result = {"pass": False, "cvc5_status": "", "note": ""}
    try:
        tm = _cvc5.TermManager()
        slv = _cvc5.Solver(tm)
        slv.setLogic("QF_LRA")
        slv.setOption("produce-models", "true")
        real_sort = tm.getRealSort()
        SA_c = tm.mkConst(real_sort, "S_A")
        SB_c = tm.mkConst(real_sort, "S_B")
        SAB_c = tm.mkConst(real_sort, "S_AB")
        zero = tm.mkReal(0)
        # Entropy non-negativity
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, SA_c, zero))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, SB_c, zero))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, SAB_c, zero))
        # Subadditivity: S(A) + S(B) >= S(AB)
        SA_plus_SB = tm.mkTerm(_cvc5.Kind.ADD, SA_c, SB_c)
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, SA_plus_SB, SAB_c))
        # Violation: I(A;B) = S(A)+S(B)-S(AB) < 0
        # i.e., S(A)+S(B) < S(AB)  <=>  SAB > SA+SB
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.GT, SAB_c, SA_plus_SB))
        result = slv.checkSat()
        n2_result["cvc5_status"] = str(result)
        if result.isUnsat():
            n2_result["pass"] = True
            n2_result["note"] = (
                "cvc5 UNSAT: cross-check confirms I(A;B)<0 impossible via subadditivity"
            )
        else:
            n2_result["note"] = f"Expected UNSAT, got {result}"
    except Exception as e:
        n2_result["note"] = f"cvc5 error: {e}"
    results["N2_cvc5_MI_nonnegative_crosscheck"] = n2_result

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # ------------------------------------------------------------------
    # B1: Product state — I(A;B) = 0 (A and B independent); I_c = -S(B)
    # ------------------------------------------------------------------
    b1_result = {"pass": False, "note": ""}
    try:
        # rho_AB = rho_A ⊗ rho_B  (product state)
        # Use maximally mixed on each qubit: rho_A = I/2, rho_B = I/2
        rho_A_mm = torch.eye(2, dtype=torch.complex128) / 2
        rho_B_mm = torch.eye(2, dtype=torch.complex128) / 2
        rho_AB_prod = torch.kron(rho_A_mm, rho_B_mm)
        mi = mutual_information(rho_AB_prod, 2, 2)
        ic = coherent_information(rho_AB_prod, 2, 2)
        S_B = von_neumann_entropy(rho_B_mm)
        expected_ic = -S_B  # I_c = I(A;B) - S(B) = 0 - S(B) = -S(B)
        mi_zero = abs(mi) < 1e-6
        ic_neg_sb = abs(ic - expected_ic) < 1e-6
        b1_result["pass"] = mi_zero and ic_neg_sb
        b1_result["I_AB"] = mi
        b1_result["I_c"] = ic
        b1_result["S_B"] = S_B
        b1_result["expected_I_c"] = expected_ic
        b1_result["note"] = "Product state: I(A;B)=0, I_c=-S(B)<0 (no coherent info to transmit)"
    except Exception as e:
        b1_result["note"] = f"error: {e}"
    results["B1_product_state_MI_zero"] = b1_result

    # ------------------------------------------------------------------
    # B2: Bell state — I(A;B) = 2*log(2); I_c = log(2) exactly
    # ------------------------------------------------------------------
    b2_result = {"pass": False, "note": ""}
    try:
        phi_plus = torch.tensor([1, 0, 0, 1], dtype=torch.complex128) / math.sqrt(2)
        rho_AB = torch.outer(phi_plus, phi_plus.conj())
        mi = mutual_information(rho_AB, 2, 2)
        ic = coherent_information(rho_AB, 2, 2)
        expected_mi = 2 * math.log(2)
        expected_ic = math.log(2)
        mi_pass = abs(mi - expected_mi) < 1e-6
        ic_pass = abs(ic - expected_ic) < 1e-6
        b2_result["pass"] = mi_pass and ic_pass
        b2_result["I_AB"] = mi
        b2_result["expected_I_AB"] = expected_mi
        b2_result["I_c"] = ic
        b2_result["expected_I_c"] = expected_ic
        b2_result["diff_MI"] = abs(mi - expected_mi)
        b2_result["diff_Ic"] = abs(ic - expected_ic)
        b2_result["note"] = "Bell state: I(A;B)=2*log(2), I_c=log(2); gap=S(B)=log(2)"
    except Exception as e:
        b2_result["note"] = f"error: {e}"
    results["B2_bell_state_MI_and_Ic"] = b2_result

    # ------------------------------------------------------------------
    # B3: sympy symbolic confirmation of I(A;B) = I_c + S(B) decomposition
    # ------------------------------------------------------------------
    b3_result = {"pass": False, "note": ""}
    try:
        SA_sym, SB_sym, SAB_sym = sp.symbols('S_A S_B S_AB', nonnegative=True)
        MI_sym = SA_sym + SB_sym - SAB_sym
        Ic_sym = SA_sym - SAB_sym
        # Verify: I(A;B) = I_c + S(B)
        diff = sp.simplify(MI_sym - (Ic_sym + SB_sym))
        decomp_holds = diff == 0
        # Verify: pure state (SAB=0) => I(A;B) = 2*S(A), using S(B)=S(A) for pure
        mi_pure = MI_sym.subs(SAB_sym, 0).subs(SB_sym, SA_sym)
        pure_identity = sp.simplify(mi_pure - 2 * SA_sym) == 0
        b3_result["pass"] = bool(decomp_holds and pure_identity)
        b3_result["decomp_diff"] = str(diff)
        b3_result["pure_state_MI"] = str(mi_pure)
        b3_result["note"] = "sympy: I(A;B)=I_c+S(B) confirmed; pure state I(A;B)=2*S(A) confirmed"
    except Exception as e:
        b3_result["note"] = f"sympy error: {e}"
    results["B3_sympy_decomposition_identity"] = b3_result

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_tests = {}
    all_tests.update(positive)
    all_tests.update(negative)
    all_tests.update(boundary)
    all_pass = all(v.get("pass", False) for v in all_tests.values())

    results = {
        "name": "sim_mutual_information_monotone_canonical",
        "description": (
            "Canonical: I(A;B)>=0 always (z3+cvc5+pytorch); I_c<=I(A;B) always; "
            "I(A;B)=2*S(A) for pure states; boundary Bell and product state checks. "
            "Step 6 bridge prerequisites established."
        ),
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_mutual_information_monotone_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    for k, v in all_tests.items():
        status = "PASS" if v.get("pass", False) else "FAIL"
        print(f"  {status}  {k}")
    print(f"\nall_pass = {all_pass}")
    if not all_pass:
        raise SystemExit(1)
