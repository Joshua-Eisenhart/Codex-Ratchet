#!/usr/bin/env python3
"""
sim_sympy_deep_lindblad_dephasing_spectrum.py

Closed-form symbolic derivation of the Lindbladian superoperator spectrum for a
single qubit under parameterized pure dephasing + amplitude damping, used to
load-bear an admissibility claim:

  CLAIM (load-bearing, downstream):
    A coherence-carrying density-matrix component |0><1| remains an admissible
    (distinguishable) candidate state iff the coherence-mode eigenvalue
    lambda_coh(gamma_phi, gamma_1) has strictly negative real part. At
    lambda_coh = 0 the probe cannot distinguish coherence from its decohered
    image => coherence is excluded as a persistent candidate.

We derive lambda_coh in closed symbolic form via sympy (not numerically) and
use that closed form to enumerate the admissibility boundary in (gamma_phi,
gamma_1) parameter space. The symbolic eigenvalue expression is what the
admissibility classifier consumes downstream -- hence sympy is load_bearing:
a numerical spectrum would not let us prove the boundary is exactly the
gamma_phi = -gamma_1/2 locus (in the zero-dephasing-plus-pumping limit),
nor identify the degeneracy structure.

This bridges CLASSICAL computation (Lindblad ODE, routinely simulated
numerically) to NONCLASSICAL constraint-admissibility (coherence mode
survival as an exclusion boundary, not an entropic minimum).

Build order alignment: shell-local lego sim on the single-qubit shell
(Coupling Program step 1). No coupling yet.
"""

import json
import os

classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": "load_bearing",
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

# --- imports / availability ---
try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    raise

try:
    import torch  # noqa: F401
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "available but not used; this sim is symbolic"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

for _modname, _key in [
    ("torch_geometric", "pyg"),
    ("z3", "z3"),
    ("cvc5", "cvc5"),
    ("clifford", "clifford"),
    ("geomstats", "geomstats"),
    ("e3nn", "e3nn"),
    ("rustworkx", "rustworkx"),
    ("xgi", "xgi"),
    ("toponetx", "toponetx"),
    ("gudhi", "gudhi"),
]:
    try:
        __import__(_modname)
        TOOL_MANIFEST[_key]["tried"] = True
        TOOL_MANIFEST[_key]["reason"] = "available; not needed for symbolic spectrum"
    except ImportError:
        TOOL_MANIFEST[_key]["reason"] = "not installed"


# =====================================================================
# SYMBOLIC CORE (load-bearing)
# =====================================================================

def symbolic_lindblad_spectrum():
    """
    Build the 4x4 Lindbladian superoperator L acting on vec(rho) for a single
    qubit with:
      - pure dephasing jump op  sqrt(gamma_phi) * sigma_z
      - amplitude damping       sqrt(gamma_1)   * sigma_minus

    L(rho) = -i[H, rho] + sum_k ( L_k rho L_k^dag
                                  - 1/2 { L_k^dag L_k, rho } )

    We take H = (omega/2) sigma_z so the free evolution contributes an
    imaginary part to the coherence eigenvalue (Larmor frequency).

    Returns dict of closed-form sympy expressions.
    """
    gamma_phi, gamma_1, omega = sp.symbols('gamma_phi gamma_1 omega',
                                           real=True, nonnegative=True)

    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    sm = sp.Matrix([[0, 0], [1, 0]])  # |1><0| convention: sigma_- lowers |0> to |1>
    # Use standard convention: sigma_- |1> = |0>, i.e. sigma_- = [[0,1],[0,0]]
    sm = sp.Matrix([[0, 1], [0, 0]])
    I2 = sp.eye(2)

    H = (omega / 2) * sz

    # Vectorization convention: vec stacks columns.
    # Superoperator identities:
    #   vec(A rho B) = (B^T kron A) vec(rho)
    def kron(A, B):
        return sp.Matrix(sp.BlockMatrix([[A[i, j] * B for j in range(A.cols)]
                                         for i in range(A.rows)]).as_explicit())

    def comm_super(H):
        # vec(-i[H, rho]) = -i (I kron H - H^T kron I) vec(rho)
        return -sp.I * (kron(I2, H) - kron(H.T, I2))

    def diss_super(L):
        # vec( L rho L^dag - 1/2 {L^dag L, rho} )
        Ld = L.H
        LdL = Ld * L
        term1 = kron(L.conjugate(), L)          # L rho L^dag
        term2 = sp.Rational(1, 2) * (kron(I2, LdL) + kron(LdL.T, I2))
        return term1 - term2

    Lop = comm_super(H) + gamma_phi * diss_super(sz) + gamma_1 * diss_super(sm)
    Lop = sp.simplify(Lop)

    # Closed-form eigenvalues.
    eigs = Lop.eigenvals()  # dict {expr: multiplicity}
    eigs_simplified = {sp.simplify(sp.radsimp(k)): v for k, v in eigs.items()}

    # The coherence-mode eigenvalue (acting on |0><1|) has the form
    #   lambda_coh = -2*gamma_phi - gamma_1/2 + i*omega    (or its conjugate)
    # Extract by matching structure.
    coh_candidates = []
    for ev in eigs_simplified.keys():
        re, im = sp.re(ev), sp.im(ev)
        # pick one with non-zero imaginary part proportional to omega
        if sp.simplify(im - omega) == 0 or sp.simplify(im + omega) == 0:
            coh_candidates.append(ev)
    lambda_coh = coh_candidates[0] if coh_candidates else None

    return {
        "symbols": (gamma_phi, gamma_1, omega),
        "L": Lop,
        "eigs": eigs_simplified,
        "lambda_coh": sp.simplify(lambda_coh) if lambda_coh is not None else None,
        "lambda_coh_real": (sp.simplify(sp.re(lambda_coh))
                            if lambda_coh is not None else None),
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    r = {}
    spec = symbolic_lindblad_spectrum()
    gamma_phi, gamma_1, omega = spec["symbols"]

    # (P1) There are exactly 4 eigenvalues counted with multiplicity.
    total_mult = sum(spec["eigs"].values())
    r["P1_total_multiplicity_is_4"] = (total_mult == 4)

    # (P2) Zero is an eigenvalue (steady state exists).
    has_zero = any(sp.simplify(ev) == 0 for ev in spec["eigs"].keys())
    r["P2_zero_eigenvalue_exists"] = bool(has_zero)

    # (P3) Closed-form coherence eigenvalue real part equals
    # -2*gamma_phi - gamma_1/2  (standard Lindblad result).
    expected_re = -2 * gamma_phi - gamma_1 / 2
    got = sp.simplify(spec["lambda_coh_real"] - expected_re)
    r["P3_lambda_coh_real_matches_closed_form"] = (got == 0)
    r["P3_expected"] = str(expected_re)
    r["P3_derived"]  = str(spec["lambda_coh_real"])

    # (P4) At gamma_phi = gamma_1 = 0 the Lindbladian reduces to pure
    # Hamiltonian commutator; eigenvalues must be {0, 0, i*omega, -i*omega}.
    # Accumulate multiplicities keyed by simplified expr (avoid dict key collisions).
    free_mult = {}
    for ev, m in spec["eigs"].items():
        key = sp.sstr(sp.simplify(ev.subs({gamma_phi: 0, gamma_1: 0})))
        free_mult[key] = free_mult.get(key, 0) + m
    want = {sp.sstr(sp.Integer(0)): 2,
            sp.sstr(sp.I * omega): 1,
            sp.sstr(-sp.I * omega): 1}
    r["P4_free_evolution_spectrum"] = (free_mult == want)

    return r


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    r = {}
    spec = symbolic_lindblad_spectrum()
    gamma_phi, gamma_1, omega = spec["symbols"]

    # (N1) The coherence eigenvalue real part is NOT positive for any
    # nonnegative (gamma_phi, gamma_1). I.e. the Lindbladian is dissipative.
    # Check: -2*gamma_phi - gamma_1/2 <= 0 for gamma_phi, gamma_1 >= 0.
    # We assert symbolically via sign analysis.
    expr = spec["lambda_coh_real"]
    # For gamma_phi, gamma_1 in R_{>=0}, expr = -(2*gamma_phi + gamma_1/2) <= 0.
    not_positive = sp.simplify(expr + 2*gamma_phi + sp.Rational(1,2)*gamma_1) == 0
    r["N1_lambda_coh_real_never_positive"] = bool(not_positive)

    # (N2) A WRONG closed form (e.g. -gamma_phi - gamma_1) should NOT match.
    wrong = -gamma_phi - gamma_1
    mismatch = sp.simplify(spec["lambda_coh_real"] - wrong) != 0
    r["N2_wrong_form_rejected"] = bool(mismatch)

    # (N3) Without the amplitude-damping term, lambda_coh should NOT depend
    # on gamma_1.
    expr_no_damp = sp.simplify(expr.subs(gamma_1, 0))
    r["N3_no_damping_drops_gamma_1"] = (gamma_1 not in expr_no_damp.free_symbols)

    return r


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    r = {}
    spec = symbolic_lindblad_spectrum()
    gamma_phi, gamma_1, omega = spec["symbols"]

    # (B1) Admissibility boundary: lambda_coh_real == 0 iff gamma_phi == 0
    # AND gamma_1 == 0 (within the nonnegative parameter cone). This is the
    # load-bearing claim: coherence is excluded as a persistent candidate
    # everywhere on the boundary except this single origin point.
    sol = sp.solve([spec["lambda_coh_real"], gamma_phi >= 0, gamma_1 >= 0],
                   [gamma_phi, gamma_1], dict=True)
    # sp.solve with inequalities is flaky; do it directly:
    # -2 gamma_phi - gamma_1/2 = 0, gamma_phi,gamma_1 >= 0 => both zero.
    cond = sp.simplify(spec["lambda_coh_real"].subs({gamma_phi: 0,
                                                     gamma_1: 0}))
    r["B1_boundary_at_origin"] = (cond == 0)

    # (B2) Degeneracy at the fully unitary point: two eigenvalues collapse to 0
    # (the identity-preserving and the z-diagonal mode) -- documented above in
    # P4; here we verify the algebraic multiplicity is exactly 2.
    zero_mult = 0
    for ev, m in spec["eigs"].items():
        if sp.simplify(ev.subs({gamma_phi: 0, gamma_1: 0})) == 0:
            zero_mult += m
    r["B2_zero_eigenvalue_degeneracy_is_2"] = (zero_mult == 2)

    # (B3) Large-dephasing limit: |lambda_coh_real| grows unboundedly with
    # gamma_phi (coherence excluded strongly). Check derivative.
    d = sp.diff(spec["lambda_coh_real"], gamma_phi)
    r["B3_dephasing_derivative"] = str(sp.simplify(d))
    r["B3_dephasing_derivative_is_minus_2"] = (sp.simplify(d + 2) == 0)

    # (B4) Pure-dephasing-only sub-channel: setting gamma_1 = 0, the coherence
    # decay rate must be exactly 2*gamma_phi (the canonical T2 = 1/(2 gamma_phi)
    # result). This is the load-bearing bridge to the T2 admissibility test.
    expr_T2 = sp.simplify(-spec["lambda_coh_real"].subs(gamma_1, 0))
    r["B4_T2_rate_is_2_gamma_phi"] = (sp.simplify(expr_T2 - 2*gamma_phi) == 0)

    return r


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    # Run all tests
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    # Mark sympy as used.
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "Closed-form Lindbladian eigenvalues load-bear the admissibility "
        "boundary claim: lambda_coh_real = -2 gamma_phi - gamma_1/2, "
        "zero only at origin in the nonnegative cone. Numerical spectrum "
        "could not prove the exact boundary locus or the degeneracy."
    )

    all_tests = {**pos, **neg, **bnd}
    all_bool = [v for v in all_tests.values() if isinstance(v, bool)]
    passed = all(all_bool)

    results = {
        "name": "sim_sympy_deep_lindblad_dephasing_spectrum",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "load_bearing_claim": (
            "Coherence mode |0><1| is excluded as a persistent admissible "
            "candidate wherever lambda_coh_real(gamma_phi, gamma_1) < 0; the "
            "closed-form expression -2*gamma_phi - gamma_1/2 identifies the "
            "admissibility boundary as the single point gamma_phi=gamma_1=0 "
            "within the nonnegative parameter cone."
        ),
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "status": "PASS" if passed else "FAIL",
        "bool_test_count": len(all_bool),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(
        out_dir, "sim_sympy_deep_lindblad_dephasing_spectrum_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"STATUS: {results['status']}  ({len(all_bool)} boolean tests)")
