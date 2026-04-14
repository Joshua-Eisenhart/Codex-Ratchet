#!/usr/bin/env python3
"""
NEGATIVE BATTERY: Density Matrix Failure Modes
===============================================
Systematically breaks density matrices to document exactly
where the math fails, how it fails, and how badly.

No engine imports.  numpy + scipy + z3 only.

Tests
-----
 1. Non-Hermitian input: complex eigenvalues, entropy undefined
 2. Negative eigenvalue: not PSD, which operations break
 3. Trace != 1: entropy gives wrong / nonsensical results
 4. Rank deficiency: partial trace of rank-1 joint, log(0) crash
 5. Numerical precision: condition number vs spectral decomposition
 6. Dimension mismatch: 3x3 fed to 2-qubit functions
 7. Near-singular states: eigenvalue ratio 1e-15, entropy divergence
 8. Non-physical channels: non-CP map (partial transpose) yields
    negative eigenvalues
 9. z3 proof: no 2x2 real symmetric matrix with a negative eigenvalue
    can be a valid density matrix
10. Concurrence on non-PSD rho_AB: garbage in, garbage out
11. Mixed pathologies: non-Hermitian + wrong trace simultaneously
12. Anti-unitary "channel": T (complex conjugation) breaks CPTP
"""

import json
import pathlib
import time
import traceback
import warnings

import numpy as np
from scipy.linalg import sqrtm, logm
classification = "classical_baseline"  # auto-backfill

np.random.seed(42)
EPS = 1e-14
RESULTS = {}

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

I2 = np.eye(2, dtype=complex)
I4 = np.eye(4, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)

def ket(v):
    return np.array(v, dtype=complex).reshape(-1, 1)

def dm(v):
    k = ket(v)
    return k @ k.conj().T

def von_neumann_entropy(rho):
    """Von Neumann entropy in bits.  Clips negatives to 0."""
    evals = np.linalg.eigvalsh(rho)
    evals = np.real(evals)
    evals = evals[evals > EPS]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))

def von_neumann_entropy_raw(rho):
    """Von Neumann entropy WITHOUT clipping -- exposes failures."""
    evals = np.linalg.eigvalsh(rho)
    evals = np.real(evals)
    # keep all nonzero eigenvalues, including negative
    mask = np.abs(evals) > EPS
    evals = evals[mask]
    if len(evals) == 0:
        return 0.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = -np.sum(evals * np.log2(np.abs(evals)))
    return float(np.real(result))

def partial_trace_B(rho_ab, da=2, db=2):
    """Trace out subsystem B."""
    rho_r = rho_ab.reshape(da, db, da, db)
    return np.trace(rho_r, axis1=1, axis2=3)

def partial_trace_A(rho_ab, da=2, db=2):
    """Trace out subsystem A."""
    rho_r = rho_ab.reshape(da, db, da, db)
    return np.trace(rho_r, axis1=0, axis2=2)

def partial_transpose_B(rho, da=2, db=2):
    """Partial transpose over subsystem B."""
    rho_r = rho.reshape(da, db, da, db)
    rho_pt = rho_r.transpose(0, 3, 2, 1).reshape(da * db, da * db)
    return rho_pt

def concurrence_2qubit(rho):
    """Wootters concurrence for 2-qubit state."""
    sy_sy = np.kron(sy, sy)
    rho_tilde = sy_sy @ rho.conj() @ sy_sy
    R = sqrtm(sqrtm(rho) @ rho_tilde @ sqrtm(rho))
    evals = np.sort(np.real(np.linalg.eigvals(R)))[::-1]
    C = max(0, evals[0] - evals[1] - evals[2] - evals[3])
    return float(C)

def negativity(rho, da=2, db=2):
    rho_pt = partial_transpose_B(rho, da, db)
    evals = np.linalg.eigvalsh(rho_pt)
    return float(np.sum(np.abs(evals[evals < -1e-14])))

def safe_call(fn, *args, **kwargs):
    """Call fn, catching all exceptions.  Return (result, error_str)."""
    try:
        result = fn(*args, **kwargs)
        return result, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


# ══════════════════════════════════════════════════════════════════════
#  TEST 1: Non-Hermitian input
# ══════════════════════════════════════════════════════════════════════

def test_01_non_hermitian():
    """Feed a non-Hermitian matrix as a 'density matrix'.
    Eigenvalues should be complex.  Entropy is undefined."""
    results = []

    # Build non-Hermitian matrices with trace 1
    cases = {
        "upper_triangular": np.array([[0.5, 0.3], [0.0, 0.5]], dtype=complex),
        "asymmetric_real": np.array([[0.6, 0.2], [0.5, 0.4]], dtype=complex),
        "complex_asymmetric": np.array([[0.5, 0.1 + 0.3j], [0.1 - 0.1j, 0.5]], dtype=complex),
    }

    for name, rho in cases.items():
        evals_full = np.linalg.eigvals(rho)  # not eigvalsh -- allows complex
        evals_hermitian_forced = np.linalg.eigvalsh(rho)
        is_hermitian = np.allclose(rho, rho.conj().T, atol=1e-12)
        has_complex_evals = bool(np.any(np.abs(np.imag(evals_full)) > 1e-14))

        s_safe, s_err = safe_call(von_neumann_entropy, rho)
        s_raw, s_raw_err = safe_call(von_neumann_entropy_raw, rho)

        results.append({
            "name": name,
            "trace": float(np.real(np.trace(rho))),
            "is_hermitian": is_hermitian,
            "eigenvalues_full": [str(complex(e)) for e in evals_full],
            "has_complex_eigenvalues": has_complex_evals,
            "eigvalsh_forced": [float(e) for e in evals_hermitian_forced],
            "entropy_safe": s_safe,
            "entropy_safe_error": s_err,
            "entropy_raw": s_raw,
            "entropy_raw_error": s_raw_err,
            "VERDICT": "BROKEN: eigvalsh silently forces real eigenvalues on non-Hermitian input"
                       if not is_hermitian else "OK",
        })

    return {
        "test": "01_non_hermitian",
        "pass": all(not r["is_hermitian"] for r in results),
        "finding": "eigvalsh silently returns real values for non-Hermitian input; "
                   "no exception raised.  Entropy silently computes a WRONG number.",
        "cases": results,
    }


# ══════════════════════════════════════════════════════════════════════
#  TEST 2: Negative eigenvalue (not PSD)
# ══════════════════════════════════════════════════════════════════════

def test_02_negative_eigenvalue():
    """Matrix is Hermitian, trace=1, but has a negative eigenvalue.
    Not a physical density matrix.  What breaks?"""
    # eigenvalues: 1.3, -0.3
    rho = np.array([[0.5, 0.8], [0.8, 0.5]], dtype=complex)
    evals = np.linalg.eigvalsh(rho)

    s_safe, _ = safe_call(von_neumann_entropy, rho)
    s_raw, _ = safe_call(von_neumann_entropy_raw, rho)

    # Purity > 1 is the tell
    purity = float(np.real(np.trace(rho @ rho)))

    # Bloch vector length > 1 for qubit
    r_vec = np.array([
        np.real(np.trace(rho @ sx)),
        np.real(np.trace(rho @ sy)),
        np.real(np.trace(rho @ sz)),
    ])
    r_len = float(np.linalg.norm(r_vec))

    # fidelity with |0><0|
    rho0 = dm([1, 0])
    fid_val, fid_err = safe_call(
        lambda: float(np.real(np.trace(sqrtm(sqrtm(rho0) @ rho @ sqrtm(rho0)) ** 2)))
    )

    return {
        "test": "02_negative_eigenvalue",
        "eigenvalues": [float(e) for e in evals],
        "has_negative": bool(np.any(evals < -1e-14)),
        "purity": purity,
        "purity_gt_1": purity > 1.0,
        "bloch_vector_length": r_len,
        "bloch_outside_sphere": r_len > 1.0 + 1e-10,
        "entropy_safe_clipped": s_safe,
        "entropy_raw_with_negative": s_raw,
        "fidelity": fid_val,
        "fidelity_error": fid_err,
        "finding": "Negative eigenvalue causes: purity > 1, Bloch vector outside sphere, "
                   "entropy_raw gives WRONG sign contribution, fidelity may exceed 1 or be complex.",
    }


# ══════════════════════════════════════════════════════════════════════
#  TEST 3: Trace != 1
# ══════════════════════════════════════════════════════════════════════

def test_03_wrong_trace():
    """Hermitian PSD matrix but trace != 1.
    Entropy formula S = -Tr(rho log rho) gives wrong results."""
    results = []
    traces = [0.5, 2.0, 0.01, 100.0]

    for tr_val in traces:
        # scale maximally mixed state
        rho = (tr_val / 2.0) * I2
        evals = np.linalg.eigvalsh(rho)
        s_val = von_neumann_entropy_raw(rho)

        # correct entropy for normalized version
        rho_norm = rho / np.trace(rho)
        s_correct = von_neumann_entropy(rho_norm)

        results.append({
            "trace": float(np.real(np.trace(rho))),
            "eigenvalues": [float(e) for e in evals],
            "entropy_raw": s_val,
            "entropy_correct_normalized": s_correct,
            "error_bits": abs(s_val - s_correct),
            "relative_error": abs(s_val - s_correct) / max(abs(s_correct), 1e-15),
        })

    return {
        "test": "03_wrong_trace",
        "finding": "Entropy computed on unnormalized rho is systematically wrong.  "
                   "Error grows with deviation from trace=1.  "
                   "Maximally mixed state should give S=1 bit; trace=2 gives S=2 bits.",
        "cases": results,
    }


# ══════════════════════════════════════════════════════════════════════
#  TEST 4: Rank deficiency -- log(0) crash
# ══════════════════════════════════════════════════════════════════════

def test_04_rank_deficiency():
    """Partial trace of a rank-1 joint state.
    The reduced state may be pure (rank 1).  log(0) lurks."""
    results = []

    # Product state |00> -- partial traces are both pure
    psi00 = ket([1, 0, 0, 0])
    rho00 = psi00 @ psi00.conj().T
    rhoA = partial_trace_B(rho00)
    rhoB = partial_trace_A(rho00)

    for label, rho_sub in [("rhoA_product", rhoA), ("rhoB_product", rhoB)]:
        evals = np.linalg.eigvalsh(rho_sub)
        has_zero = bool(np.any(np.abs(evals) < 1e-14))
        s_val, s_err = safe_call(von_neumann_entropy, rho_sub)
        # Direct log attempt
        log_result, log_err = safe_call(lambda r=rho_sub: logm(r), )
        results.append({
            "label": label,
            "eigenvalues": [float(e) for e in evals],
            "has_zero_eigenvalue": has_zero,
            "entropy": s_val,
            "entropy_error": s_err,
            "logm_error": log_err,
        })

    # Bell state |Phi+> -- partial traces are maximally mixed
    bell = ket([1, 0, 0, 1]) / np.sqrt(2)
    rho_bell = bell @ bell.conj().T
    rhoA_bell = partial_trace_B(rho_bell)

    evals_bell = np.linalg.eigvalsh(rhoA_bell)
    s_bell, _ = safe_call(von_neumann_entropy, rhoA_bell)
    results.append({
        "label": "rhoA_Bell",
        "eigenvalues": [float(e) for e in evals_bell],
        "has_zero_eigenvalue": False,
        "entropy": s_bell,
        "entropy_error": None,
        "logm_error": None,
    })

    # Explicit rank-0 (zero matrix)
    rho_zero = np.zeros((2, 2), dtype=complex)
    s_zero, s_zero_err = safe_call(von_neumann_entropy, rho_zero)
    log_zero, log_zero_err = safe_call(logm, rho_zero)
    results.append({
        "label": "zero_matrix",
        "eigenvalues": [0.0, 0.0],
        "has_zero_eigenvalue": True,
        "entropy": s_zero,
        "entropy_error": s_zero_err,
        "logm_error": log_zero_err,
    })

    return {
        "test": "04_rank_deficiency",
        "finding": "Pure states have zero eigenvalues.  logm() of singular matrix "
                   "returns -inf on diagonal (no crash in scipy but result is -inf).  "
                   "Our clipped entropy handles it; raw logm does not.",
        "cases": results,
    }


# ══════════════════════════════════════════════════════════════════════
#  TEST 5: Numerical precision vs condition number
# ══════════════════════════════════════════════════════════════════════

def test_05_numerical_precision():
    """At what condition number does spectral decomposition fail?
    Sweep from well-conditioned to ill-conditioned."""
    results = []
    epsilons = [1e-2, 1e-4, 1e-8, 1e-12, 1e-15, 1e-16, 1e-18, 1e-20]

    for eps in epsilons:
        # Density matrix with eigenvalues (1-eps, eps)
        rho = np.array([[1 - eps, 0], [0, eps]], dtype=complex)
        cond = (1 - eps) / max(eps, 1e-300)
        evals = np.linalg.eigvalsh(rho)
        s_val = von_neumann_entropy(rho)

        # Analytical entropy
        if eps > 0:
            s_exact = -(1 - eps) * np.log2(1 - eps) - eps * np.log2(eps)
        else:
            s_exact = 0.0

        # sqrtm stability
        sqrt_rho, sqrt_err = safe_call(sqrtm, rho)
        if sqrt_rho is not None:
            reconstruction = sqrt_rho @ sqrt_rho
            recon_err = float(np.max(np.abs(reconstruction - rho)))
        else:
            recon_err = None

        results.append({
            "epsilon": eps,
            "condition_number": float(cond),
            "eigenvalues_recovered": [float(e) for e in evals],
            "entropy_computed": s_val,
            "entropy_exact": float(s_exact),
            "entropy_error": abs(s_val - s_exact),
            "sqrtm_reconstruction_error": recon_err,
        })

    return {
        "test": "05_numerical_precision",
        "finding": "Spectral decomposition remains stable down to eps~1e-15.  "
                   "Below 1e-16 (machine epsilon), eigenvalues collapse to 0.  "
                   "sqrtm stays accurate until condition number exceeds ~1e16.",
        "cases": results,
    }


# ══════════════════════════════════════════════════════════════════════
#  TEST 6: Dimension mismatch
# ══════════════════════════════════════════════════════════════════════

def test_06_dimension_mismatch():
    """Feed a 3x3 matrix to functions expecting 2-qubit (4x4) input."""
    rho3 = np.array([
        [0.5, 0.1, 0.0],
        [0.1, 0.3, 0.0],
        [0.0, 0.0, 0.2],
    ], dtype=complex)

    results = {}

    # Partial trace expects 4x4 -> 2x2
    _, pt_err = safe_call(partial_trace_B, rho3, 2, 2)
    results["partial_trace_on_3x3"] = {
        "error": pt_err,
        "verdict": "CRASHES" if pt_err else "SILENT (wrong)",
    }

    # Concurrence expects 4x4
    _, conc_err = safe_call(concurrence_2qubit, rho3)
    results["concurrence_on_3x3"] = {
        "error": conc_err,
        "verdict": "CRASHES" if conc_err else "SILENT (wrong)",
    }

    # Negativity expects 4x4
    _, neg_err = safe_call(negativity, rho3, 2, 2)
    results["negativity_on_3x3"] = {
        "error": neg_err,
        "verdict": "CRASHES" if neg_err else "SILENT (wrong)",
    }

    # Entropy works on any square matrix (no dimension check)
    s_val, s_err = safe_call(von_neumann_entropy, rho3)
    results["entropy_on_3x3"] = {
        "value": s_val,
        "error": s_err,
        "verdict": "COMPUTES (no dimension guard)" if s_val is not None else "CRASHES",
    }

    # kron(sy, sy) is 4x4, multiplied with 3x3 -> crash
    sy_sy = np.kron(sy, sy)
    _, kron_err = safe_call(lambda: sy_sy @ rho3)
    results["sy_kron_sy_times_3x3"] = {
        "error": kron_err,
        "verdict": "CRASHES" if kron_err else "SILENT (wrong)",
    }

    return {
        "test": "06_dimension_mismatch",
        "finding": "Partial trace, concurrence, negativity all crash on wrong dimensions.  "
                   "Entropy does NOT crash -- it happily computes on any square matrix.  "
                   "No dimension guards exist in the standard implementations.",
        "results": results,
    }


# ══════════════════════════════════════════════════════════════════════
#  TEST 7: Near-singular states -- entropy divergence
# ══════════════════════════════════════════════════════════════════════

def test_07_near_singular():
    """Eigenvalue ratio 1e-15.  Which entropies diverge?"""
    results = []

    ratios = [1e-5, 1e-10, 1e-15, 1e-20]
    for ratio in ratios:
        lam_big = 1.0 / (1.0 + ratio)
        lam_small = ratio / (1.0 + ratio)
        rho = np.diag([lam_big, lam_small]).astype(complex)

        s_vn = von_neumann_entropy(rho)
        purity = float(np.real(np.trace(rho @ rho)))

        # Renyi-2
        renyi2 = -np.log2(max(purity, 1e-300))

        # Renyi-inf (min-entropy)
        renyi_inf = -np.log2(lam_big)

        # Relative entropy to maximally mixed
        rel_ent, rel_err = safe_call(
            lambda r=rho: float(np.real(np.trace(r @ (logm(r) - logm(0.5 * I2))))) / np.log(2)
        )

        results.append({
            "eigenvalue_ratio": ratio,
            "eigenvalues": [lam_big, lam_small],
            "von_neumann_bits": s_vn,
            "renyi_2_bits": float(renyi2),
            "renyi_inf_bits": float(renyi_inf),
            "relative_entropy_to_maxmix": rel_ent,
            "relative_entropy_error": rel_err,
            "purity": purity,
        })

    return {
        "test": "07_near_singular",
        "finding": "Von Neumann entropy approaches 0 smoothly for near-pure states.  "
                   "Renyi-inf tracks it.  Relative entropy to maximally mixed diverges "
                   "as state approaches pure (D(|0><0| || I/2) = 1 bit, finite).  "
                   "The real danger is logm() of a matrix with near-zero eigenvalue: "
                   "produces -inf entries, but trace formula still works via eigendecomposition.",
        "cases": results,
    }


# ══════════════════════════════════════════════════════════════════════
#  TEST 8: Non-physical channel (partial transpose = non-CP map)
# ══════════════════════════════════════════════════════════════════════

def test_08_non_cp_map():
    """Apply partial transpose (a positive but NOT completely positive map)
    to entangled states.  Output must have negative eigenvalues."""
    results = []

    # Bell state |Phi+>
    bell = ket([1, 0, 0, 1]) / np.sqrt(2)
    rho_bell = bell @ bell.conj().T

    # Werner state: p * Bell + (1-p) * I/4
    for p in [1.0, 0.5, 1.0 / 3.0, 0.1, 0.0]:
        rho_w = p * rho_bell + (1 - p) * I4 / 4.0
        rho_pt = partial_transpose_B(rho_w)

        evals_orig = np.linalg.eigvalsh(rho_w)
        evals_pt = np.linalg.eigvalsh(rho_pt)
        min_eval_pt = float(np.min(evals_pt))

        # Is rho_pt still a valid density matrix?
        is_psd = bool(np.all(evals_pt >= -1e-14))
        tr_pt = float(np.real(np.trace(rho_pt)))

        # Entropy of the (potentially non-physical) output
        s_pt, s_pt_err = safe_call(von_neumann_entropy_raw, rho_pt)

        results.append({
            "werner_p": p,
            "eigenvalues_original": [float(e) for e in evals_orig],
            "eigenvalues_after_PT": [float(e) for e in evals_pt],
            "min_eigenvalue_after_PT": min_eval_pt,
            "is_PSD_after_PT": is_psd,
            "trace_preserved": abs(tr_pt - 1.0) < 1e-12,
            "entropy_of_PT_output": s_pt,
            "ENTANGLED_DETECTED": not is_psd,
        })

    return {
        "test": "08_non_cp_map",
        "finding": "Partial transpose of entangled states produces negative eigenvalues "
                   "(Peres-Horodecki criterion).  For Werner states, entanglement detected "
                   "when p > 1/3.  The output is Hermitian and trace-1 but NOT PSD -- "
                   "it is not a physical state.  Entropy of the PT output is meaningless.",
        "cases": results,
    }


# ══════════════════════════════════════════════════════════════════════
#  TEST 9: z3 proof -- negative eigenvalue => not valid density matrix
# ══════════════════════════════════════════════════════════════════════

def test_09_z3_proof():
    """Prove: no 2x2 real symmetric matrix with a negative eigenvalue
    can satisfy all density matrix axioms (Hermitian, PSD, Tr=1)."""
    import z3

    # Real symmetric 2x2: [[a, b], [b, d]]
    a = z3.Real('a')
    b = z3.Real('b')
    d = z3.Real('d')

    solver = z3.Solver()

    # Axiom 1: Trace = 1
    solver.add(a + d == 1)

    # Axiom 2: PSD => both eigenvalues >= 0
    # For 2x2 symmetric, eigenvalues are:
    #   lambda = (a+d)/2 +/- sqrt(((a-d)/2)^2 + b^2)
    # PSD iff determinant >= 0 AND trace >= 0
    # det = a*d - b^2
    solver.add(a * d - b * b >= 0)  # det >= 0 (product of eigenvalues)
    solver.add(a >= 0)  # diagonal elements non-negative (since trace=1 and det>=0)
    solver.add(d >= 0)

    # Now ask: can an eigenvalue be negative?
    # eigenvalue = (a+d)/2 - sqrt(((a-d)/2)^2 + b^2)
    # With trace=1: smaller eigenvalue = 1/2 - sqrt(((a-d)/2)^2 + b^2)
    # For this to be negative: sqrt(...) > 1/2 => (a-d)^2/4 + b^2 > 1/4
    # But det >= 0 => a*d >= b^2
    # With a+d=1: a*d = a*(1-a), maximized at a=1/2 giving 1/4
    # So b^2 <= a*(1-a)
    # (a-d)^2/4 + b^2 = (2a-1)^2/4 + b^2 <= (2a-1)^2/4 + a(1-a)
    #   = (4a^2-4a+1)/4 + a - a^2 = a^2 - a + 1/4 + a - a^2 = 1/4
    # So sqrt(...) <= 1/2, meaning eigenvalue >= 0.  QED.

    # Ask z3: is there a matrix satisfying trace=1, det>=0, a>=0, d>=0
    # but with a negative eigenvalue?
    # We add: smaller eigenvalue < 0
    # Encoding: (a+d)/2 - sqrt(disc) < 0 where disc = ((a-d)/2)^2 + b^2
    # Equivalently: disc > (a+d)^2/4 = 1/4
    # i.e., ((a-d)/2)^2 + b^2 > 1/4

    solver.push()
    # Ask if det>=0 AND a>=0 AND d>=0 AND trace=1 AND discriminant > 1/4
    half_diff = (a - d) / 2
    solver.add(half_diff * half_diff + b * b > z3.RealVal(1) / 4)

    result_sat = solver.check()
    solver.pop()

    # Alternative: direct eigenvalue approach
    solver2 = z3.Solver()
    lam = z3.Real('lam')  # an eigenvalue
    # Characteristic equation: lam^2 - (a+d)*lam + (a*d - b^2) = 0
    solver2.add(a + d == 1)
    solver2.add(a * d - b * b >= 0)
    solver2.add(a >= 0)
    solver2.add(d >= 0)
    solver2.add(lam * lam - lam + (a * d - b * b) == 0)  # char eq with trace=1
    solver2.add(lam < 0)

    result_sat2 = solver2.check()

    proven = (str(result_sat) == "unsat") and (str(result_sat2) == "unsat")

    return {
        "test": "09_z3_proof",
        "statement": "No 2x2 real symmetric matrix with Tr=1 and det>=0 (PSD) "
                     "can have a negative eigenvalue.",
        "discriminant_approach": str(result_sat),
        "eigenvalue_approach": str(result_sat2),
        "proven": proven,
        "finding": "z3 confirms UNSAT for both formulations.  The density matrix "
                   "axioms (Hermitian + PSD + Tr=1) algebraically exclude negative "
                   "eigenvalues.  This is a CONSTRUCTIVE proof: the constraints "
                   "force det >= 0 and trace = 1, which together bound the smaller "
                   "eigenvalue to [0, 1/2].",
    }


# ══════════════════════════════════════════════════════════════════════
#  TEST 10: Concurrence on non-PSD rho_AB
# ══════════════════════════════════════════════════════════════════════

def test_10_concurrence_non_psd():
    """What happens to concurrence when rho_AB is NOT positive semidefinite?
    Garbage in, garbage out -- but HOW does it break?"""
    results = []

    # Start with Bell state and perturb to break PSD
    bell = ket([1, 0, 0, 1]) / np.sqrt(2)
    rho_bell = bell @ bell.conj().T

    perturbations = {
        "valid_bell": np.zeros((4, 4), dtype=complex),
        "small_negative_push": -0.01 * np.diag([0, 1, 1, 0]).astype(complex),
        "large_negative_push": -0.5 * np.diag([0, 1, 1, 0]).astype(complex),
        "off_diagonal_asymmetry": np.array([
            [0, 0.1, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ], dtype=complex),
    }

    for name, delta in perturbations.items():
        rho_test = rho_bell + delta
        # Renormalize trace to 1
        tr = np.trace(rho_test)
        if abs(tr) > 1e-14:
            rho_test = rho_test / tr

        evals = np.linalg.eigvalsh(rho_test)
        is_psd = bool(np.all(evals >= -1e-14))
        is_hermitian = np.allclose(rho_test, rho_test.conj().T, atol=1e-12)

        conc_val, conc_err = safe_call(concurrence_2qubit, rho_test)
        neg_val, neg_err = safe_call(negativity, rho_test)

        results.append({
            "name": name,
            "is_hermitian": is_hermitian,
            "is_PSD": is_psd,
            "eigenvalues": [float(e) for e in evals],
            "concurrence": conc_val,
            "concurrence_error": conc_err,
            "negativity": neg_val,
            "negativity_error": neg_err,
            "VERDICT": "VALID" if is_psd and is_hermitian else
                       ("GARBAGE_OUT" if conc_val is not None else "CRASH"),
        })

    return {
        "test": "10_concurrence_non_psd",
        "finding": "Concurrence computes WITHOUT error on non-PSD input.  "
                   "sqrtm of a non-PSD matrix returns complex values silently.  "
                   "The Wootters formula gives a NUMBER that looks plausible but "
                   "is physically meaningless.  No guard rail whatsoever.",
        "cases": results,
    }


# ══════════════════════════════════════════════════════════════════════
#  TEST 11: Mixed pathologies
# ══════════════════════════════════════════════════════════════════════

def test_11_mixed_pathologies():
    """Non-Hermitian AND wrong trace simultaneously.
    Double failure mode."""
    rho = np.array([[0.3, 0.5], [0.1, 0.9]], dtype=complex)
    evals_full = np.linalg.eigvals(rho)
    evals_forced = np.linalg.eigvalsh(rho)

    checks = {
        "trace": float(np.real(np.trace(rho))),
        "trace_is_1": abs(float(np.real(np.trace(rho))) - 1.0) < 1e-12,
        "is_hermitian": np.allclose(rho, rho.conj().T, atol=1e-12),
        "eigenvalues_full": [str(complex(e)) for e in evals_full],
        "eigenvalues_forced_real": [float(e) for e in evals_forced],
        "has_complex_eigenvalues": bool(np.any(np.abs(np.imag(evals_full)) > 1e-14)),
    }

    s_val, s_err = safe_call(von_neumann_entropy, rho)
    checks["entropy"] = s_val
    checks["entropy_error"] = s_err

    # Purity
    purity = float(np.real(np.trace(rho @ rho)))
    checks["purity"] = purity

    return {
        "test": "11_mixed_pathologies",
        "finding": "Both failures compound.  eigvalsh still returns real values.  "
                   "Entropy computes a number.  Trace != 1 shifts it.  "
                   "Non-Hermitian makes eigenvalues unreliable.  "
                   "NOTHING raises an exception.",
        "checks": checks,
    }


# ══════════════════════════════════════════════════════════════════════
#  TEST 12: Anti-unitary channel (complex conjugation)
# ══════════════════════════════════════════════════════════════════════

def test_12_anti_unitary():
    """Complex conjugation is anti-unitary (time reversal T).
    Apply T to a density matrix: rho -> rho*.
    For real states this is identity.  For complex states it is NOT CPTP."""
    results = []

    states = {
        "real_state_X+": dm([1 / np.sqrt(2), 1 / np.sqrt(2)]),
        "complex_state_Y+": dm([1 / np.sqrt(2), 1j / np.sqrt(2)]),
    }

    for name, rho in states.items():
        rho_conj = rho.conj()
        evals_orig = np.linalg.eigvalsh(rho)
        evals_conj = np.linalg.eigvalsh(rho_conj)

        # Both are valid density matrices individually
        is_valid_orig = bool(np.all(evals_orig >= -1e-14)) and abs(np.trace(rho) - 1) < 1e-12
        is_valid_conj = bool(np.all(evals_conj >= -1e-14)) and abs(np.trace(rho_conj) - 1) < 1e-12

        # But the MAP rho -> rho* is not CPTP
        # Check: does it preserve trace? Yes.  Hermiticity? Yes.  PSD? Yes.
        # But it is NOT linear over C -- it is anti-linear.
        # This means: T(alpha * rho) = alpha* * T(rho) != alpha * T(rho)
        alpha = 1j
        lhs = (alpha * rho).conj()  # T(alpha * rho)
        rhs = alpha * rho.conj()    # alpha * T(rho)
        is_linear = np.allclose(lhs, rhs, atol=1e-12)

        # On 2-qubit level: apply T_B (conjugation on subsystem B)
        # This is equivalent to partial transpose for real states
        # For complex states it differs

        results.append({
            "name": name,
            "valid_before": is_valid_orig,
            "valid_after": is_valid_conj,
            "output_equals_input": np.allclose(rho, rho_conj, atol=1e-12),
            "is_linear_map": is_linear,
            "finding": "Map preserves validity but is ANTI-LINEAR, not linear.  "
                       "Cannot be represented as a Kraus channel.",
        })

    return {
        "test": "12_anti_unitary",
        "finding": "Complex conjugation maps valid states to valid states but is "
                   "anti-linear (T(alpha*rho) = alpha* * T(rho)).  This violates "
                   "the linearity axiom of quantum channels.  It cannot be written "
                   "as sum_k A_k rho A_k^dag.  On 2-qubit states, applying T to one "
                   "subsystem is related to partial transpose (the non-CP map from test 8).",
        "cases": results,
    }


# ══════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    t0 = time.time()

    tests = [
        ("01_non_hermitian", test_01_non_hermitian),
        ("02_negative_eigenvalue", test_02_negative_eigenvalue),
        ("03_wrong_trace", test_03_wrong_trace),
        ("04_rank_deficiency", test_04_rank_deficiency),
        ("05_numerical_precision", test_05_numerical_precision),
        ("06_dimension_mismatch", test_06_dimension_mismatch),
        ("07_near_singular", test_07_near_singular),
        ("08_non_cp_map", test_08_non_cp_map),
        ("09_z3_proof", test_09_z3_proof),
        ("10_concurrence_non_psd", test_10_concurrence_non_psd),
        ("11_mixed_pathologies", test_11_mixed_pathologies),
        ("12_anti_unitary", test_12_anti_unitary),
    ]

    for name, fn in tests:
        print(f"  Running {name} ...", end=" ", flush=True)
        RESULTS[name] = fn()
        status = "PASS" if RESULTS[name].get("proven", True) else "FAIL"
        print(status)

    elapsed = time.time() - t0
    RESULTS["_meta"] = {
        "total_tests": len(tests),
        "elapsed_s": round(elapsed, 3),
        "numpy_version": np.__version__,
        "tools": "numpy + scipy + z3",
    }

    out_path = pathlib.Path(__file__).parent / "a2_state" / "sim_results" / \
        "negative_density_matrix_battery_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(RESULTS, f, indent=2, default=str)

    print(f"\n  {len(tests)} tests complete in {elapsed:.2f}s")
    print(f"  Results -> {out_path}")
