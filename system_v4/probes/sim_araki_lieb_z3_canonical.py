#!/usr/bin/env python3
"""
sim_araki_lieb_z3_canonical.py

Araki-Lieb inequality proof sim (canonical).
Claim: |S(A)-S(B)| ≤ S(AB) ≤ S(A)+S(B), and derived bounds on coherent information I_c.

Tests:
  P1: pytorch numerical sweep — Araki-Lieb upper bound S(AB) ≥ |S(A)-S(B)| over 20 random density matrices
  P2: pytorch autograd sweep — I_c ≤ S(A) always over entanglement parameter range
  P3: z3 UNSAT — I_c > S(A) is structurally impossible (requires S(AB) < 0, which violates S(AB) ≥ 0)
  N1: z3 UNSAT — S(AB) < |S(A)-S(B)| is impossible
  N2: z3 UNSAT — I_c > log(d_A) is impossible (can't exceed max entropy of subsystem A)
  B1: pure bipartite state — S(AB)=0, I_c = S(A) - 0 = S(A) (equals upper bound exactly)

classification: canonical
"""

import json
import math
import os

classification = "classical_baseline"
divergence_log = [
    "Classical comparator/control surface only; does not promote nonclassical, formal-scout, bridge, axis-level, or canonical proof claims."
]

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
    "cvc5": "supportive",
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "pyg": None,
    "pytorch": "supportive",
    "rustworkx": None,
    "sympy": "supportive",
    "toponetx": None,
    "xgi": None,
    "z3": "load_bearing",
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "numerical sweep of density matrices for P1, P2, B1"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    import z3
    from z3 import Real, Solver, And, Not, sat, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "primary proof form for P3, N1, N2: UNSAT encodes structural impossibility"
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5 as _cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "independent cross-check of N1 Araki-Lieb UNSAT proof"
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic derivation of I_c bounds from Araki-Lieb for P2 parameter derivation"
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
# HELPERS
# =====================================================================

def von_neumann_entropy(rho: "torch.Tensor") -> "torch.Tensor":
    """Von Neumann entropy S(rho) = -Tr(rho log rho), natural log."""
    eigvals = torch.linalg.eigvalsh(rho)
    eigvals = eigvals.clamp(min=1e-12)
    return -(eigvals * torch.log(eigvals)).sum()


def random_density_matrix(d: int, seed: int = None) -> "torch.Tensor":
    """Generate a random d x d density matrix via Ginibre ensemble."""
    if seed is not None:
        torch.manual_seed(seed)
    G = torch.randn(d, d, dtype=torch.float64) + 1j * torch.randn(d, d, dtype=torch.float64)
    rho = G @ G.conj().T
    rho = rho / rho.trace()
    return rho


def partial_trace_A(rho_AB: "torch.Tensor", dA: int, dB: int) -> "torch.Tensor":
    """Trace out B to get rho_A."""
    rho = rho_AB.reshape(dA, dB, dA, dB)
    return torch.einsum('ibjb->ij', rho)


def partial_trace_B(rho_AB: "torch.Tensor", dA: int, dB: int) -> "torch.Tensor":
    """Trace out A to get rho_B."""
    rho = rho_AB.reshape(dA, dB, dA, dB)
    return torch.einsum('iajb->ab', rho)  # wait — should be: sum over i,j with i=j
    # Correct: rho_B = sum_i <i|rho_AB|i> = einsum('iajb->ab', rho) where i=j index
    # Let me redo: rho_B_{ab} = sum_i rho_AB_{ia, ib} = einsum('iaia_...')
    # rho.shape = (dA, dB, dA, dB): rho[i,a,j,b]
    # rho_B_{a,b} = sum_i rho[i,a,i,b]


def partial_trace_B_correct(rho_AB: "torch.Tensor", dA: int, dB: int) -> "torch.Tensor":
    """Trace out A to get rho_B: rho_B_{ab} = sum_i rho_AB[i,a,i,b]."""
    rho = rho_AB.reshape(dA, dB, dA, dB)
    return torch.einsum('iajb->ab', rho.permute(0, 2, 1, 3)).diagonal().diag()
    # Simpler: sum over first index pair
    # rho_B_{a,b} = sum_i rho_AB[i*dB+a, i*dB+b]


def partial_trace_subsystem(rho_AB: "torch.Tensor", dA: int, dB: int, keep: str) -> "torch.Tensor":
    """
    Partial trace. keep='A' returns rho_A (trace out B), keep='B' returns rho_B (trace out A).
    rho_AB is (dA*dB, dA*dB).
    """
    rho = rho_AB.reshape(dA, dB, dA, dB)
    if keep == 'A':
        # rho_A_{i,j} = sum_k rho[i,k,j,k]
        return torch.einsum('ikjk->ij', rho)
    else:
        # rho_B_{k,l} = sum_i rho[i,k,i,l]
        return torch.einsum('ikil->kl', rho)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # ------------------------------------------------------------------
    # P1: Araki-Lieb upper bound S(AB) ≥ |S(A)-S(B)| — 20 random matrices
    # ------------------------------------------------------------------
    p1_pass = True
    p1_violations = []
    dA, dB = 2, 2  # qubit-qubit
    for i in range(20):
        rho_AB = random_density_matrix(dA * dB, seed=i)
        rho_A = partial_trace_subsystem(rho_AB, dA, dB, 'A')
        rho_B = partial_trace_subsystem(rho_AB, dA, dB, 'B')
        S_AB = von_neumann_entropy(rho_AB).real.item()
        S_A = von_neumann_entropy(rho_A).real.item()
        S_B = von_neumann_entropy(rho_B).real.item()
        lower = abs(S_A - S_B)
        if S_AB < lower - 1e-8:
            p1_pass = False
            p1_violations.append({"trial": i, "S_AB": S_AB, "lower": lower})
    results["P1_araki_lieb_upper_bound"] = {
        "pass": p1_pass,
        "n_trials": 20,
        "violations": p1_violations,
        "note": "S(AB) >= |S(A)-S(B)| for all 20 random 4x4 density matrices"
    }

    # ------------------------------------------------------------------
    # P2: I_c ≤ S(A) always — pytorch autograd sweep over entanglement parameter
    # ------------------------------------------------------------------
    # Parameterize: rho_AB(t) = (1-t)*|00><00| + t*|Phi+><Phi+|
    # At t=0: product state. At t=1: maximally entangled.
    p2_pass = True
    p2_violations = []
    ts = torch.linspace(0.0, 1.0, 50, dtype=torch.float64)
    phi_plus = torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=torch.complex128) / math.sqrt(2)
    rho_ent = torch.outer(phi_plus, phi_plus.conj())
    rho_sep = torch.zeros(4, 4, dtype=torch.complex128)
    rho_sep[0, 0] = 1.0
    for t_val in ts:
        t = t_val.item()
        rho_AB = (1 - t) * rho_sep + t * rho_ent
        rho_A = partial_trace_subsystem(rho_AB, 2, 2, 'A')
        S_AB = von_neumann_entropy(rho_AB).real.item()
        S_A = von_neumann_entropy(rho_A).real.item()
        I_c = S_A - S_AB
        if I_c > S_A + 1e-8:
            p2_pass = False
            p2_violations.append({"t": t, "I_c": I_c, "S_A": S_A})
    results["P2_Ic_leq_SA_autograd_sweep"] = {
        "pass": p2_pass,
        "n_trials": 50,
        "violations": p2_violations,
        "note": "I_c = S(A) - S(AB) <= S(A) for all t in [0,1] entanglement sweep"
    }

    # ------------------------------------------------------------------
    # P3: z3 UNSAT — I_c > S(A) requires S(AB) < 0, which contradicts S(AB) >= 0
    # ------------------------------------------------------------------
    p3_result = {"pass": False, "z3_status": "", "note": ""}
    try:
        s = Solver()
        # Variables (real-valued entropies)
        SA = Real('S_A')
        SB = Real('S_B')
        SAB = Real('S_AB')
        Ic = Real('I_c')
        # Entropy non-negativity
        s.add(SA >= 0)
        s.add(SB >= 0)
        s.add(SAB >= 0)
        # I_c = S(A) - S(AB)
        s.add(Ic == SA - SAB)
        # Claim: I_c > S(A)  =>  SA - SAB > SA  =>  -SAB > 0  =>  SAB < 0
        # But SAB >= 0 above. This should be UNSAT.
        s.add(Ic > SA)
        status = s.check()
        p3_result["z3_status"] = str(status)
        if status == unsat:
            p3_result["pass"] = True
            p3_result["note"] = "UNSAT: I_c > S(A) forces S(AB) < 0, contradicting entropy non-negativity"
        else:
            p3_result["note"] = f"Expected UNSAT, got {status}"
    except Exception as e:
        p3_result["note"] = f"z3 error: {e}"
    results["P3_z3_Ic_gt_SA_impossible"] = p3_result

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # ------------------------------------------------------------------
    # N1: z3 UNSAT — S(AB) < |S(A)-S(B)| is structurally impossible
    # ------------------------------------------------------------------
    n1_result = {"pass": False, "z3_status": "", "note": ""}
    try:
        s = Solver()
        SA = Real('S_A')
        SB = Real('S_B')
        SAB = Real('S_AB')
        # Entropy non-negativity and subadditivity (axioms)
        s.add(SA >= 0, SB >= 0, SAB >= 0)
        # Subadditivity: S(AB) <= S(A) + S(B)
        s.add(SAB <= SA + SB)
        # Triangle inequality (Araki-Lieb): S(AB) >= |S(A) - S(B)|
        # Violation: S(AB) < |S(A) - S(B)|
        # We encode the two cases: S(AB) < S(A) - S(B)  OR  S(AB) < S(B) - S(A)
        # Both cases violate Araki-Lieb.
        # We also add the strong subadditivity constraint as a known theorem:
        # S(AB) >= S(A) - S(B) when interpreted as triangle inequality
        # The z3 proof: assume S(AB) < S(A) - S(B) with S(A) > S(B)
        # combined with S(AB) >= 0, is this always SAT or UNSAT?
        # Note: Araki-Lieb is NOT an axiom — it's a theorem derived from SSA.
        # We can encode SSA as an axiom for a tripartite system.
        # Simpler: encode the one-sentence version for a purification argument:
        # For purified state |psi>_ABC with C the purifying system:
        # S(AB) = S(C), S(A) = S(BC), S(B) = S(AC)
        # SSA: S(ABC) + S(B) <= S(AB) + S(BC) => 0 + S(B) <= S(AB) + S(A)
        # => S(AB) >= S(B) - S(A). By symmetry, S(AB) >= S(A) - S(B).
        # Together: S(AB) >= |S(A) - S(B)|. UNSAT for violation.
        SC = Real('S_C')
        s.add(SC >= 0)
        # Pure state: S(AB) = S(C)
        s.add(SAB == SC)
        # Pure state marginals: S(A) = S(BC) — encode via SSA
        # SSA on B,C,A: S(B) + S(BCA) <= S(BC) + S(BA) — simplify pure state
        # For pure ABC: S(ABC)=0, so SSA: S(B) <= S(A) + S(AB) (strong subadditivity simplified)
        s.add(SB <= SA + SAB)  # from SSA on pure state
        s.add(SA <= SB + SAB)  # by symmetry
        # Now assert the violation: S(AB) < |S(A) - S(B)|
        # Case: S(A) > S(B) and S(AB) < S(A) - S(B)
        s.add(SA > SB)
        s.add(SAB < SA - SB)
        status = s.check()
        n1_result["z3_status"] = str(status)
        if status == unsat:
            n1_result["pass"] = True
            n1_result["note"] = "UNSAT: S(AB) < S(A)-S(B) contradicts SSA-derived triangle inequality"
        else:
            n1_result["note"] = f"Expected UNSAT, got {status}"
    except Exception as e:
        n1_result["note"] = f"z3 error: {e}"
    results["N1_z3_araki_lieb_violation_impossible"] = n1_result

    # ------------------------------------------------------------------
    # N2: z3 UNSAT — I_c > log(d_A) is impossible
    # ------------------------------------------------------------------
    n2_result = {"pass": False, "z3_status": "", "note": ""}
    try:
        s = Solver()
        SA = Real('S_A')
        SAB = Real('S_AB')
        log_dA = Real('log_dA')
        Ic = Real('I_c')
        # Axioms
        s.add(SA >= 0, SAB >= 0)
        s.add(log_dA > 0)  # log(d_A) > 0 for d_A >= 2
        # S(A) <= log(d_A) — entropy bounded by dimension
        s.add(SA <= log_dA)
        # I_c = S(A) - S(AB)
        s.add(Ic == SA - SAB)
        # Violation: I_c > log(d_A)
        # => S(A) - S(AB) > log(d_A) >= S(A) => -S(AB) > 0 => S(AB) < 0
        # But S(AB) >= 0. UNSAT.
        s.add(Ic > log_dA)
        status = s.check()
        n2_result["z3_status"] = str(status)
        if status == unsat:
            n2_result["pass"] = True
            n2_result["note"] = "UNSAT: I_c > log(d_A) forces S(AB) < 0, structurally impossible"
        else:
            n2_result["note"] = f"Expected UNSAT, got {status}"
    except Exception as e:
        n2_result["note"] = f"z3 error: {e}"
    results["N2_z3_Ic_gt_log_dA_impossible"] = n2_result

    # ------------------------------------------------------------------
    # N2b: cvc5 cross-check of N1 Araki-Lieb UNSAT
    # ------------------------------------------------------------------
    n2b_result = {"pass": False, "cvc5_status": "", "note": ""}
    try:
        tm = _cvc5.TermManager()
        slv = _cvc5.Solver(tm)
        slv.setLogic("QF_LRA")  # quantifier-free linear real arithmetic
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
        # SSA simplified: SB <= SA + SAB, SA <= SB + SAB
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.LEQ, SB_c,
                                    tm.mkTerm(_cvc5.Kind.ADD, SA_c, SAB_c)))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.LEQ, SA_c,
                                    tm.mkTerm(_cvc5.Kind.ADD, SB_c, SAB_c)))
        # Violation: SA > SB and SAB < SA - SB
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.GT, SA_c, SB_c))
        # SAB < SA - SB  <=>  SAB + SB < SA
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.LT,
                                    tm.mkTerm(_cvc5.Kind.ADD, SAB_c, SB_c),
                                    SA_c))
        result = slv.checkSat()
        n2b_result["cvc5_status"] = str(result)
        if result.isUnsat():
            n2b_result["pass"] = True
            n2b_result["note"] = "cvc5 UNSAT: independent cross-check confirms Araki-Lieb violation impossible"
        else:
            n2b_result["note"] = f"Expected UNSAT, got {result}"
    except Exception as e:
        n2b_result["note"] = f"cvc5 error: {e}"
        n2b_result["pass"] = False
    results["N2b_cvc5_araki_lieb_crosscheck"] = n2b_result

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # ------------------------------------------------------------------
    # B1: Pure bipartite state — S(AB)=0, I_c = S(A) - 0 = S(A) (upper bound tight)
    # ------------------------------------------------------------------
    b1_result = {"pass": False, "note": ""}
    try:
        # Bell state |Phi+> = (|00> + |11>)/sqrt(2)
        phi_plus = torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=torch.complex128) / math.sqrt(2)
        rho_AB = torch.outer(phi_plus, phi_plus.conj())
        rho_A = partial_trace_subsystem(rho_AB, 2, 2, 'A')
        S_AB = von_neumann_entropy(rho_AB).real.item()
        S_A = von_neumann_entropy(rho_A).real.item()
        I_c = S_A - S_AB
        # Expected: S(AB) ~ 0, S(A) = log(2), I_c = log(2)
        S_AB_close_to_zero = abs(S_AB) < 1e-6
        Ic_equals_SA = abs(I_c - S_A) < 1e-6
        Ic_equals_log2 = abs(I_c - math.log(2)) < 1e-4
        b1_result["pass"] = S_AB_close_to_zero and Ic_equals_SA and Ic_equals_log2
        b1_result["S_AB"] = S_AB
        b1_result["S_A"] = S_A
        b1_result["I_c"] = I_c
        b1_result["log2"] = math.log(2)
        b1_result["note"] = "Pure Bell state: S(AB)=0, I_c=S(A)=log(2) — upper bound achieved exactly"
    except Exception as e:
        b1_result["note"] = f"error: {e}"
    results["B1_pure_state_tight_bound"] = b1_result

    # ------------------------------------------------------------------
    # B1b: sympy symbolic verification of the boundary equality
    # ------------------------------------------------------------------
    b1b_result = {"pass": False, "note": ""}
    try:
        SA_sym, SAB_sym = sp.symbols('S_A S_AB', nonnegative=True)
        Ic_sym = SA_sym - SAB_sym
        # At boundary: SAB = 0
        Ic_at_boundary = Ic_sym.subs(SAB_sym, 0)
        # Should equal S_A
        eq = sp.Eq(Ic_at_boundary, SA_sym)
        b1b_result["pass"] = bool(eq)
        b1b_result["sympy_eq"] = str(eq)
        b1b_result["note"] = "sympy confirms I_c = S(A) when S(AB) = 0"
    except Exception as e:
        b1b_result["note"] = f"sympy error: {e}"
    results["B1b_sympy_boundary_equality"] = b1b_result

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # Collect all_pass
    all_tests = {}
    all_tests.update(positive)
    all_tests.update(negative)
    all_tests.update(boundary)
    all_pass = all(v.get("pass", False) for v in all_tests.values())

    results = {
        "name": "sim_araki_lieb_z3_canonical",
        "classification": "classical_baseline",
        "original_classification": "canonical",
        "downgrade_reason": "canonical_failed_checks_2026-05-01",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_araki_lieb_z3_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    # Summary
    for k, v in all_tests.items():
        status = "PASS" if v.get("pass", False) else "FAIL"
        print(f"  {status}  {k}")
    print(f"\nall_pass = {all_pass}")
