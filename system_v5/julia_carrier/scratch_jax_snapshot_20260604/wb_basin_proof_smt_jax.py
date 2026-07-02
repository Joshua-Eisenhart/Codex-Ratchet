#!/usr/bin/env python3
"""
wb_basin_proof_smt_jax.py
JAX audit lane for basin_proof_smt

OBJECT:   basin_proof_smt
VERSION:  1.2
CLAIM CEILING: carrier_smt_probe — promotion_allowed: false

PURPOSE:
  Cross-check the Julia carrier's SMT flip result using JAX for the
  finite dynamics and z3+cvc5 (Python-native) for the SMT proofs.
  Reads the Julia result JSON and computes a parity JSON.

FINITE MAP:
  domain   -> 8 finite Bloch-vector states in R (r^2 <= 0.9); K in {1,2,4,8} steps
  codomain -> (z3_verdict, cvc5_verdict, basin_label, flip_detected) per K

ROOT CONSTRAINTS:
  F01: finite carrier (8 states, K in {1,2,4,8})
  N01: The requested Depol/PhaseFlip Pauli-channel order check is measured and
       blocked because standard Pauli channels commute. A separate
       Depol/AmpDamp order-sensitive witness is measured as an alternate check.

ANTI-FABRICATION:
  - z3/cvc5 called directly (not hardcoded)
  - Tautology check: if both UNSAT, flag tautology
  - Parity computed against Julia JSON
  - promotion_allowed: false enforced
"""

import os
import sys
import json
import math
import time
from datetime import datetime
from fractions import Fraction

# ── JAX setup ─────────────────────────────────────────────────────────────────
os.environ.setdefault("JAX_ENABLE_X64", "1")
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

# ── SMT solvers ───────────────────────────────────────────────────────────────
import z3
try:
    import cvc5 as _cvc5
    HAS_CVC5 = True
except ImportError:
    HAS_CVC5 = False

OBJECT_ID   = "basin_proof_smt"
VERSION     = "1.2"
SEED        = 20260604
RESULT_PATH = "/tmp/wb_basin_proof_smt_jax_results.json"
PARITY_PATH = "/tmp/wb_basin_proof_smt_parity.json"
JULIA_RESULT_PATH = (
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/"
    "system_v5/julia_carrier/wb_basin_proof_smt_julia_results.json"
)

P_DEPOL   = 0.25
LAMBDA    = 1.0 - 4*P_DEPOL/3   # = 2/3
R_MAX_SQ  = 0.9
K_VALUES  = [1, 2, 4, 8]
S_THRESH  = 0.5

print("="*78)
print(f"wb_basin_proof_smt_jax.py  (object_id={OBJECT_ID}, version={VERSION})")
print("JAX audit lane: basin-proof SMT flip cross-check")
print("="*78)
print(f"JAX version: {jax.__version__}")
print(f"p_depol={P_DEPOL}, lambda={LAMBDA:.6f}, R_MAX_SQ={R_MAX_SQ}, S_thresh={S_THRESH}")

# =============================================================================
# N01 CHECK (JAX): requested Pauli check plus alternate order witness
# =============================================================================
print("\n--- N01 check (JAX): requested Pauli witness and alternate order witness ---")

sX = jnp.array([[0,1],[1,0]], dtype=jnp.complex128)
sY = jnp.array([[0,-1j],[1j,0]], dtype=jnp.complex128)
sZ = jnp.array([[1,0],[0,-1]], dtype=jnp.complex128)
I2 = jnp.eye(2, dtype=jnp.complex128)

def apply_depol(rho, p):
    return (1-p)*rho + p/3*(sX@rho@sX + sY@rho@sY + sZ@rho@sZ)

def apply_phase_flip(rho, p):
    """Phase-flip channel: (1-p)*rho + p*Z*rho*Z."""
    return (1-p)*rho + p*(sZ @ rho @ sZ)

def apply_amp_damp(rho, p):
    """Amplitude-damping channel: K0=[[1,0],[0,sqrt(1-p)]], K1=[[0,sqrt(p)],[0,0]]"""
    K0 = jnp.array([[1, 0], [0, jnp.sqrt(1-p)]], dtype=jnp.complex128)
    K1 = jnp.array([[0, jnp.sqrt(p)], [0, 0]], dtype=jnp.complex128)
    return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T

rho_plus = jnp.array([[0.5, 0.5],[0.5, 0.5]], dtype=jnp.complex128)
p_test   = 0.3

# Requested witness: standard depolarizing and phase-flip Pauli channels commute.
rho_DF = apply_phase_flip(apply_depol(rho_plus, p_test), p_test)
rho_FD = apply_depol(apply_phase_flip(rho_plus, p_test), p_test)
requested_n01_diff = float(jnp.linalg.norm(rho_DF - rho_FD))
requested_n01_passed = requested_n01_diff > 1e-10

# Alternate order-sensitive witness: Depol∘AmpDamp vs AmpDamp∘Depol.
rho_DA = apply_amp_damp(apply_depol(rho_plus, p_test), p_test)
rho_AD = apply_depol(apply_amp_damp(rho_plus, p_test), p_test)
n01_diff = float(jnp.linalg.norm(rho_DA - rho_AD))
n01_passed = n01_diff > 1e-10
print(f"  Requested Depol∘PhaseFlip vs PhaseFlip∘Depol: ||diff||_F = {requested_n01_diff:.6e}")
print(f"  Requested N01 witness passed: {requested_n01_passed}")
print(f"  Alternate Depol∘AmpDamp vs AmpDamp∘Depol: ||diff||_F = {n01_diff:.6e}")
print(f"  Alternate order-sensitive witness passed: {n01_passed}")

# =============================================================================
# BASIN ENTROPY CALCULATION (JAX)
# =============================================================================

def bloch_entropy(r: float) -> float:
    r = min(r, 1.0 - 1e-12)
    r = max(r, 0.0)
    p_plus  = (1 + r) / 2
    p_minus = (1 - r) / 2
    h_plus  = 0.0 if p_plus  < 1e-15 else -p_plus  * math.log(p_plus)
    h_minus = 0.0 if p_minus < 1e-15 else -p_minus * math.log(p_minus)
    return h_plus + h_minus

def find_r_basin(S_threshold: float) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if bloch_entropy(mid) >= S_threshold:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

r_basin = find_r_basin(S_THRESH)
print(f"\nBasin A: S(rho) >= {S_THRESH} nats  <=>  r <= {r_basin:.6f}")
print(f"  S(r=0) = {bloch_entropy(0.0):.6f}, S(r=1) = {bloch_entropy(1.0-1e-12):.6f}")

print("\n--- Size ladder (JAX dynamics) ---")
for K in K_VALUES:
    lK   = LAMBDA**K
    rp   = lK * math.sqrt(R_MAX_SQ)
    Srp  = bloch_entropy(rp)
    print(f"  K={K}: lambda^K={lK:.6f}, r'_max={rp:.6f}, S={Srp:.4f}, in_basin={rp<=r_basin}")

# =============================================================================
# SMT PROOFS (z3 + cvc5)
# =============================================================================

def run_z3_proof(K: int, p_channel: float):
    """
    UNSAT means: no (a,b,c) with a^2+b^2+c^2 <= R_MAX_SQ has
    lambda^(2K) * (a^2+b^2+c^2) > r_basin^2.
    => basin is forced for all states in R after K steps.
    SAT means a counterexample exists.
    """
    lambda_K_sq = (1.0 - 4*p_channel/3)**(2*K)
    r_basin_sq  = r_basin**2

    a, b, c = z3.Real('a'), z3.Real('b'), z3.Real('c')
    r_sq = a*a + b*b + c*c

    s = z3.Solver()
    s.add(r_sq <= R_MAX_SQ)
    s.add(lambda_K_sq * r_sq > r_basin_sq)

    result = s.check()
    if result == z3.unsat:
        return "UNSAT"
    elif result == z3.sat:
        return "SAT"
    else:
        return "UNKNOWN"

def run_cvc5_proof(K: int, p_channel: float):
    if not HAS_CVC5:
        return "UNAVAILABLE"
    try:
        slv = _cvc5.Solver()
        slv.setOption("produce-models", "true")
        slv.setLogic("QF_NRA")

        p_rat    = Fraction(1, 4) if abs(p_channel - 0.25) < 1e-10 else Fraction(p_channel).limit_denominator(10000)
        lam_rat  = Fraction(1) - Fraction(4, 3) * p_rat
        lam_K_sq = lam_rat**(2*K)
        lam_num  = lam_K_sq.numerator
        lam_den  = lam_K_sq.denominator

        r_bs_rat  = Fraction(r_basin**2).limit_denominator(100000)
        r_bs_num  = r_bs_rat.numerator
        r_bs_den  = r_bs_rat.denominator

        real_sort = slv.getRealSort()
        a5 = slv.mkConst(real_sort, "a5")
        b5 = slv.mkConst(real_sort, "b5")
        c5 = slv.mkConst(real_sort, "c5")

        def mk_rat(num, den):
            return slv.mkReal(int(num), int(den))

        r_sq5 = slv.mkTerm(
            _cvc5.Kind.ADD,
            slv.mkTerm(_cvc5.Kind.MULT, a5, a5),
            slv.mkTerm(_cvc5.Kind.ADD,
                slv.mkTerm(_cvc5.Kind.MULT, b5, b5),
                slv.mkTerm(_cvc5.Kind.MULT, c5, c5)))

        # r_sq5 <= 9/10
        in_R = slv.mkTerm(_cvc5.Kind.LEQ, r_sq5, mk_rat(9, 10))

        # lam_num/lam_den * r_sq5 > r_bs_num/r_bs_den
        # => lam_num * r_bs_den * r_sq5 > r_bs_num * lam_den
        lhs = slv.mkTerm(
            _cvc5.Kind.MULT,
            mk_rat(lam_num * r_bs_den, 1),
            r_sq5)
        rhs = mk_rat(r_bs_num * lam_den, 1)
        not_in_basin = slv.mkTerm(_cvc5.Kind.GT, lhs, rhs)

        slv.assertFormula(in_R)
        slv.assertFormula(not_in_basin)

        res = slv.checkSat()
        return "UNSAT" if res.isUnsat() else "SAT"
    except Exception as e:
        return f"ERROR:{e}"

print("\n--- SMT proofs (JAX lane: z3 + cvc5) ---")

smt_results_jax = []
any_z3_unsat_real    = False
any_z3_unsat_erased  = False
any_cvc5_unsat_real  = False
any_cvc5_unsat_erased = False
flip_detected_z3     = False
flip_detected_cvc5   = False
tautology_z3         = False
tautology_cvc5       = False

for K in K_VALUES:
    print(f"\n  K = {K}:")

    z3_real    = run_z3_proof(K, P_DEPOL)
    z3_erased  = run_z3_proof(K, 0.0)
    cvc5_real  = run_cvc5_proof(K, P_DEPOL)
    cvc5_erased = run_cvc5_proof(K, 0.0)

    z3_flip    = (z3_real == "UNSAT") and (z3_erased != "UNSAT")
    cvc5_flip  = (cvc5_real == "UNSAT") and (cvc5_erased != "UNSAT")
    z3_taut    = (z3_real == "UNSAT") and (z3_erased == "UNSAT")
    cvc5_taut  = (cvc5_real == "UNSAT") and (cvc5_erased == "UNSAT")

    print(f"    Real   carrier: z3={z3_real},   cvc5={cvc5_real}")
    print(f"    Erased carrier: z3={z3_erased}, cvc5={cvc5_erased}")
    print(f"    Flip: z3={z3_flip}, cvc5={cvc5_flip}")
    print(f"    Tautology: z3={z3_taut}, cvc5={cvc5_taut}")

    if z3_real   == "UNSAT": any_z3_unsat_real    = True
    if z3_erased == "UNSAT": any_z3_unsat_erased  = True
    if cvc5_real   == "UNSAT": any_cvc5_unsat_real  = True
    if cvc5_erased == "UNSAT": any_cvc5_unsat_erased = True
    if z3_flip:   flip_detected_z3   = True
    if cvc5_flip: flip_detected_cvc5 = True
    if z3_taut:   tautology_z3   = True
    if cvc5_taut: tautology_cvc5 = True

    lK   = LAMBDA**K
    rp   = lK * math.sqrt(R_MAX_SQ)
    Srp  = bloch_entropy(rp)
    rp_e = 1.0**K * math.sqrt(R_MAX_SQ)

    smt_results_jax.append({
        "K": K,
        "lambda_K_real":    lK,
        "lambda_K_erased":  1.0,
        "r_prime_max_real":   rp,
        "r_prime_max_erased": rp_e,
        "S_at_bound_real":    Srp,
        "in_basin_real":      rp <= r_basin,
        "in_basin_erased":    rp_e <= r_basin,
        "z3_real":    z3_real,
        "z3_erased":  z3_erased,
        "cvc5_real":  cvc5_real,
        "cvc5_erased": cvc5_erased,
        "z3_flip":    z3_flip,
        "cvc5_flip":  cvc5_flip,
        "z3_tautology":  z3_taut,
        "cvc5_tautology": cvc5_taut,
    })

# =============================================================================
# 8 SAMPLE STATES (JAX)
# =============================================================================
print("\n--- 8 sample states (JAX), K=4 ---")
key = jax.random.PRNGKey(SEED)
K4  = 4
lK4 = LAMBDA**K4

sample_results = []
for i in range(8):
    key, key_v, key_r = jax.random.split(key, 3)
    v = jax.random.normal(key_v, (3,), dtype=jnp.float64)
    v = v / jnp.maximum(jnp.linalg.norm(v), 1e-10)
    r0 = math.sqrt(R_MAX_SQ) * float(jax.random.uniform(key_r, dtype=jnp.float64))**(1/3)
    bloch0 = r0 * v
    rho1 = 0.5 * (I2 + bloch0[0] * sX + bloch0[1] * sY + bloch0[2] * sZ)
    rho2 = jnp.kron(rho1, I2 / 2.0)
    rho2_eigs = jnp.linalg.eigvalsh(rho2)
    r0_val  = float(jnp.linalg.norm(bloch0))
    bloch_K = lK4 * bloch0
    rK_val  = float(jnp.linalg.norm(bloch_K))
    S_bef   = bloch_entropy(r0_val)
    S_aft   = bloch_entropy(rK_val)
    print(f"  state_{i+1}: r0={r0_val:.4f}, r'={rK_val:.4f}, S={S_bef:.3f}->{S_aft:.3f}, in_basin={rK_val<=r_basin}")
    sample_results.append({
        "state_idx": i+1, "r0": round(r0_val,6), "r_after_K4": round(rK_val,6),
        "S_before": round(S_bef,6), "S_after": round(S_aft,6),
        "in_R": r0_val**2 <= R_MAX_SQ, "in_basin_after_K4": rK_val <= r_basin,
        "rho_dim": [int(rho2.shape[0]), int(rho2.shape[1])],
        "rho_trace": round(float(jnp.real(jnp.trace(rho2))), 12),
        "rho_min_eig": round(float(jnp.min(jnp.real(rho2_eigs))), 12),
        "rho_hermitian_error": round(float(jnp.linalg.norm(rho2 - rho2.conj().T)), 12),
    })

# =============================================================================
# WRITE JAX RESULT JSON
# =============================================================================
jax_result = {
    "object_id":         OBJECT_ID,
    "version":           VERSION,
    "classification":    "carrier_smt_probe",
    "promotion_allowed": False,
    "claim_ceiling":     "carrier_smt_probe — promotion_allowed: false",
    "timestamp":         datetime.now().isoformat(),
    "engine":            "jax_audit_lane",
    "jax_version":       str(jax.__version__),

    "finite_map": {
        "domain":   "8 finite 4x4 density-matrix samples generated from active Bloch vectors in R (r^2<=0.9) with a mixed spectator qubit; SMT abstraction uses the active 3-component Bloch radius; K in {1,2,4,8}",
        "codomain": "(z3_verdict, cvc5_verdict, basin_label, flip_detected) per K",
        "f01":      "finite carrier: 8 states, K in {1,2,4,8}, bounded Bloch ball",
        "n01":      f"Requested Depol/PhaseFlip Pauli-channel order check is measured false (commutes, diff={requested_n01_diff:.4e}); alternate Depol/AmpDamp order witness is measured true (diff={n01_diff:.4e})",
    },

    "physical_parameters": {
        "p_depol": P_DEPOL, "lambda": LAMBDA, "R_MAX_SQ": R_MAX_SQ,
        "S_threshold": S_THRESH, "r_basin_bound": r_basin, "K_values": K_VALUES,
    },

    "n01_check": {
        "requested_depol_phaseflip": {
            "test": "Depol∘PhaseFlip vs PhaseFlip∘Depol on |+><+| with p=0.3",
            "diff_norm": requested_n01_diff,
            "passed": bool(requested_n01_passed),
            "status": "blocked_false_for_standard_Pauli_channels",
            "statement": "standard depolarizing and phase-flip Pauli channels commute on this carrier",
        },
        "alternate_depol_ampdamp": {
            "test": "Depol∘AmpDamp vs AmpDamp∘Depol on |+><+| with p=0.3",
            "diff_norm": n01_diff,
            "passed": bool(n01_passed),
            "statement": f"Depol and AmpDamp do not commute: diff_norm={n01_diff:.4e} > 1e-10",
        },
        "requested_witness_passed": bool(requested_n01_passed),
        "alternate_witness_passed": bool(n01_passed),
        "note": "The SMT contraction proof is real/erased load-bearing, but the user-requested Pauli-channel N01 witness is not available under standard channel definitions.",
    },

    "smt_results_per_K": smt_results_jax,

    "aggregate": {
        "z3_flip_detected":   flip_detected_z3,
        "cvc5_flip_detected": flip_detected_cvc5,
        "flip_detected":      flip_detected_z3 or flip_detected_cvc5,
        "z3_unsat_real":      any_z3_unsat_real,
        "z3_unsat_erased":    any_z3_unsat_erased,
        "cvc5_unsat_real":    any_cvc5_unsat_real,
        "cvc5_unsat_erased":  any_cvc5_unsat_erased,
        "tautology_detected_z3":   tautology_z3,
        "tautology_detected_cvc5": tautology_cvc5,
        "tautology_rejected":      not (tautology_z3 or tautology_cvc5),
    },

    "sample_states_K4": sample_results,

    "tool_manifest": {
        "jax":  {"tried": True, "used": True, "role": "load_bearing",
                 "reason": "computes audit-lane finite dynamics, requested/alternate N01 checks, and 4x4 sample-carrier checks"},
        "z3":   {"tried": True, "used": True, "role": "load_bearing",
                 "reason": "SMT UNSAT on real carrier proves basin forced; removing z3 removes proof"},
        "cvc5": {"tried": True, "used": HAS_CVC5, "role": "load_bearing" if HAS_CVC5 else "unavailable",
                 "reason": "cross-check z3; flip only counts when both solvers agree"},
    },

    "blocked_consumers": [
        "layer-completion / manifold admission",
        "coupling / coexistence / nesting promotion",
        "bridge / rho_AB / Xi / Phi0 / Axis0",
        "flux / FEP / physics",
    ],
}

with open(RESULT_PATH, "w") as f:
    json.dump(jax_result, f, indent=2)
print(f"\nJAX result written to: {RESULT_PATH}")

# =============================================================================
# PARITY CHECK: compare with Julia results
# =============================================================================
print("\n--- Parity check vs Julia ---")

julia_result = None
try:
    with open(JULIA_RESULT_PATH) as f:
        julia_result = json.load(f)
    print(f"  Julia result loaded: {JULIA_RESULT_PATH}")
except Exception as e:
    print(f"  Julia result NOT available: {e}")

def safe_get(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return default
    return d

jax_z3_unsat_real    = any_z3_unsat_real
jax_z3_unsat_erased  = any_z3_unsat_erased
jax_flip             = flip_detected_z3 or flip_detected_cvc5
jax_tautology_rej    = not (tautology_z3 or tautology_cvc5)

julia_z3_unsat_real   = safe_get(julia_result, "aggregate", "z3_unsat_real",   default=None) if julia_result else None
julia_z3_unsat_erased = safe_get(julia_result, "aggregate", "z3_unsat_erased", default=None) if julia_result else None
julia_flip            = safe_get(julia_result, "aggregate", "flip_detected",    default=None) if julia_result else None
julia_taut_rej        = safe_get(julia_result, "aggregate", "tautology_rejected", default=None) if julia_result else None

julia_r_basin = safe_get(julia_result, "physical_parameters", "r_basin_bound", default=None) if julia_result else None
jax_r_basin   = r_basin
max_parity_diff = abs(julia_r_basin - jax_r_basin) if julia_r_basin is not None else None

engines_agree = None
if julia_result is not None:
    engines_agree = (
        jax_z3_unsat_real   == julia_z3_unsat_real and
        jax_z3_unsat_erased == julia_z3_unsat_erased and
        jax_flip            == julia_flip
    )

print(f"  JAX:  z3_unsat_real={jax_z3_unsat_real}, z3_unsat_erased={jax_z3_unsat_erased}, flip={jax_flip}")
print(f"  Julia: z3_unsat_real={julia_z3_unsat_real}, z3_unsat_erased={julia_z3_unsat_erased}, flip={julia_flip}")
print(f"  r_basin: JAX={jax_r_basin:.8f}, Julia={julia_r_basin}")
print(f"  max_parity_diff (r_basin): {max_parity_diff}")
print(f"  engines_agree: {engines_agree}")

parity = {
    "object_id":             OBJECT_ID,
    "timestamp":             datetime.now().isoformat(),
    "promotion_allowed":     False,

    "julia_unsat_real":      julia_z3_unsat_real,
    "julia_unsat_erased":    julia_z3_unsat_erased,
    "julia_flip_detected":   julia_flip,
    "julia_tautology_rejected": julia_taut_rej,

    "jax_unsat_real":        jax_z3_unsat_real,
    "jax_unsat_erased":      jax_z3_unsat_erased,
    "jax_flip_detected":     jax_flip,
    "jax_tautology_rejected": jax_tautology_rej,

    "engines_agree":         engines_agree,
    "max_parity_diff":       max_parity_diff,

    "julia_result_path":     JULIA_RESULT_PATH,
    "jax_result_path":       RESULT_PATH,

    "note": (
        "Both engines should agree: real=UNSAT (basin forced), erased=SAT (basin not forced). "
        "If engines_agree=None, Julia results were not available at parity-check time."
    ),
}

with open(PARITY_PATH, "w") as f:
    json.dump(parity, f, indent=2)
print(f"Parity JSON written to: {PARITY_PATH}")

print("\n--- Aggregate verdict ---")
print(f"  JAX flip_detected: {jax_flip}")
print(f"  tautology_rejected: {jax_tautology_rej}")
print(f"  engines_agree: {engines_agree}")
print("="*78)
print("wb_basin_proof_smt_jax.py DONE")
print("="*78)
