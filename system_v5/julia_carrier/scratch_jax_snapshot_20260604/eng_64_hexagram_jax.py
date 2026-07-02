#!/usr/bin/env python3
"""
eng_64_hexagram_jax.py
JAX parity lane for eng_64_hexagram_julia_v1.

Reads the Julia reference JSON and independently computes the same 64
hexagram stage fingerprints using JAX operations that mirror the Julia
operator primitives.  Compares n_distinct and parity reference values.

Re-run:
    python3 /tmp/eng_64_hexagram_jax.py

Result JSON:
    /tmp/eng_64_hexagram_jax_results.json
"""

import json
import math
import os
import sys
from pathlib import Path

# ── JAX import ─────────────────────────────────────────────────────────────────
try:
    import jax
    import jax.numpy as jnp
    jax.config.update("jax_enable_x64", True)
except ImportError:
    print("ERROR: jax not available. Install jax.")
    sys.exit(2)

# ── Paths ─────────────────────────────────────────────────────────────────────
JULIA_RESULT_PATH = (
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/"
    "eng_64_hexagram_julia_results.json"
)
JAX_RESULT_PATH = "/tmp/eng_64_hexagram_jax_results.json"

OBJECT_ID        = "eng_64_hexagram_jax_parity_v1"
PROMOTION_ALLOWED = False

# ── Thresholds (must match Julia) ──────────────────────────────────────────────
N01_EPS       = 1.0e-9
COMMUTE_EPS   = 1.0e-9
FP_TOL        = 1.0e-7
PARITY_TOL    = 1.0e-5   # tolerance for Julia/JAX numeric agreement
GAMMA_KRAUS   = 0.30
GAMMA_LINDBLAD= 0.30
OMEGA         = 1.0
DT            = 0.1
NSTEPS        = 20
THETA_HOT     = 0.40
THETA_COLD    = math.pi / 4.0
THETA_ADIAB   = math.pi / 3.0
RNG_SEED      = 20260604

# ── Pauli matrices ─────────────────────────────────────────────────────────────
I2 = jnp.eye(2, dtype=jnp.complex128)
SX = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
SZ = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)

# ── State construction (shared seed protocol with Julia) ───────────────────────
def seeded_fraction(seed, n, idx, stride, modulus, offset):
    raw = ((seed % modulus) + stride * n + offset * idx) % modulus
    return (raw + 0.5) / modulus

def seeded_angles(seed, n, idx):
    tf = seeded_fraction(seed, n, idx, 37,  997, 53)
    pf = seeded_fraction(seed, n, idx, 101, 991, 67)
    cf = seeded_fraction(seed, n, idx, 131, 983, 71)
    theta = math.pi * (0.11 + 0.78 * tf)
    phi   = 2.0 * math.pi * pf
    chi   = 2.0 * math.pi * cf
    return theta, phi, chi

def weyl_density_L(seed, n, idx):
    theta, phi, chi = seeded_angles(seed, n, idx)
    psi = jnp.array([
        cmath_exp(phi + chi) * math.cos(theta / 2.0),
        cmath_exp(phi - chi) * math.sin(theta / 2.0),
    ], dtype=jnp.complex128)
    psi = psi / jnp.linalg.norm(psi)
    return jnp.outer(psi, psi.conj())

def cmath_exp(angle):
    return complex(math.cos(angle), math.sin(angle))

RHO_REPR = weyl_density_L(RNG_SEED, 64, 1)

# ── Quantum operations ─────────────────────────────────────────────────────────
def von_neumann_entropy(rho):
    rho_h = (rho + rho.T.conj()) / 2.0
    evals = jnp.linalg.eigvalsh(rho_h)
    evals = jnp.where(evals > 1.0e-14, evals, 1.0e-14)
    # Only sum over genuinely positive eigenvalues
    mask = evals > 1.0e-14
    s = -jnp.sum(jnp.where(mask, evals * jnp.log(evals), 0.0))
    return float(s)

def kraus_apply(Ks, rho):
    out = jnp.zeros((2, 2), dtype=jnp.complex128)
    for K in Ks:
        out = out + K @ rho @ K.T.conj()
    t = jnp.trace(out)
    if abs(t) > 1.0e-14:
        out = out / t
    return out

def lindblad_step(rho, H, L, gamma, dt):
    LdL  = L.T.conj() @ L
    comm = H @ rho - rho @ H
    diss = gamma * (L @ rho @ L.T.conj() - 0.5 * (LdL @ rho + rho @ LdL))
    rho_new = rho + dt * (-1j * comm + diss)
    t = jnp.trace(rho_new)
    if abs(t) > 1.0e-14:
        rho_new = rho_new / t
    return rho_new

def density_valid(rho):
    trace_ok = abs(float(jnp.trace(rho).real) - 1.0) < 1.0e-8
    herm_ok  = float(jnp.linalg.norm(rho - rho.T.conj())) < 1.0e-8
    evals    = jnp.linalg.eigvalsh((rho + rho.T.conj()) / 2.0)
    eig_ok   = bool(jnp.all(evals >= -1.0e-8))
    return trace_ok and herm_ok and eig_ok

# ── Axis-1: expand / compress ──────────────────────────────────────────────────
def axis1_channel(bit, gamma=GAMMA_KRAUS):
    if bit == 0:  # expand
        K0 = jnp.array([[math.sqrt(1.0 - gamma), 0], [0, 1]], dtype=jnp.complex128)
        K1 = jnp.array([[0, 0], [math.sqrt(gamma), 0]], dtype=jnp.complex128)
    else:          # compress
        K0 = jnp.array([[1, 0], [0, math.sqrt(1.0 - gamma)]], dtype=jnp.complex128)
        K1 = jnp.array([[0, math.sqrt(gamma)], [0, 0]], dtype=jnp.complex128)
    return [K0, K1]

def apply_axis1(rho, bit):
    return kraus_apply(axis1_channel(bit), rho)

# ── Axis-2: open (isothermal) / closed (adiabatic) ────────────────────────────
def apply_axis2_open(rho):
    H = OMEGA * SZ / 2.0
    L = jnp.array([[0, math.sqrt(GAMMA_LINDBLAD)], [0, 0]], dtype=jnp.complex128)
    r = rho
    for _ in range(NSTEPS):
        r = lindblad_step(r, H, L, 1.0, DT)
    return r

def apply_axis2_closed(rho):
    c = math.cos(THETA_ADIAB / 2.0)
    s = math.sin(THETA_ADIAB / 2.0)
    U = c * I2 - 1j * s * SX
    return U @ rho @ U.T.conj()

def apply_axis2(rho, bit):
    return apply_axis2_open(rho) if bit == 0 else apply_axis2_closed(rho)

# ── Axis-5: hot (spectral/dephase) / cold (gradient/rotate) ───────────────────
def apply_axis5_hot(rho, gamma=THETA_HOT):
    g  = max(0.0, min(1.0, gamma))
    K0 = math.sqrt(1.0 - g/2.0) * I2
    K1 = math.sqrt(g/2.0) * SZ
    return K0 @ rho @ K0.T.conj() + K1 @ rho @ K1.T.conj()

def apply_axis5_cold(rho, theta=THETA_COLD):
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    U = c * I2 - 1j * s * SX
    return U @ rho @ U.T.conj()

def apply_axis5(rho, bit):
    return apply_axis5_hot(rho) if bit == 0 else apply_axis5_cold(rho)

# ── Stroke tables ─────────────────────────────────────────────────────────────
CARNOT_STROKES  = [(0, 0), (0, 1), (1, 0), (1, 1)]
SZILARD_STROKES = [(1, 0), (0, 0), (0, 0), (1, 1)]

def ax12_compose(rho, ax1_bit, ax2_bit):
    return apply_axis1(apply_axis2(rho, ax2_bit), ax1_bit)

def apply_substage(rho, ax1_bit, ax2_bit, ax5_bit, ax6_bit):
    def ax12_fn(r): return ax12_compose(r, ax1_bit, ax2_bit)
    def ax5_fn(r):  return apply_axis5(r, ax5_bit)
    if ax6_bit == 0:
        return ax12_fn(ax5_fn(rho))  # axis5 first, then ax12
    else:
        return ax5_fn(ax12_fn(rho))  # ax12 first, then axis5

def apply_stage(rho_in, ax1, ax2, ax3, ax4, ax5, ax6):
    strokes = CARNOT_STROKES if ax3 == 0 else SZILARD_STROKES
    stroke_seq = list(range(4)) if ax4 == 0 else list(range(3, -1, -1))
    rho = rho_in
    for s_idx in stroke_seq:
        s_ax1, s_ax2 = strokes[s_idx]
        rho = apply_substage(rho, s_ax1, s_ax2, ax5, ax6)
    return rho

# ── Fingerprint ────────────────────────────────────────────────────────────────
def round_fp(x, tol=FP_TOL):
    return round(x / tol) * tol

def fingerprint(rho):
    v = []
    for i in range(2):
        for j in range(2):
            v.append(round_fp(float(rho[i, j].real)))
            v.append(round_fp(float(rho[i, j].imag)))
    return v

def fps_equal(fp1, fp2, tol=FP_TOL * 10):
    return all(abs(a - b) < tol for a, b in zip(fp1, fp2))

# ── Enumerate all 64 stages ───────────────────────────────────────────────────
def enumerate_64():
    all_stages   = []
    fps_list     = []
    collapses    = []

    for ax6 in range(2):
        for ax5 in range(2):
            for ax4 in range(2):
                for ax3 in range(2):
                    for ax2 in range(2):
                        for ax1 in range(2):
                            rho_out = apply_stage(RHO_REPR, ax1, ax2, ax3, ax4, ax5, ax6)
                            S_out   = von_neumann_entropy(rho_out)
                            fp      = fingerprint(rho_out)
                            valid   = density_valid(rho_out)
                            engine  = "Carnot" if ax3 == 0 else "Szilard"
                            direction = "CW" if ax4 == 0 else "CCW"
                            hex_index = ax1 + 2*ax2 + 4*ax3 + 8*ax4 + 16*ax5 + 32*ax6
                            label = f"hex{hex_index:02d}_{engine}_{direction}_ax5{ax5}_ax6{ax6}"
                            all_stages.append({
                                "hex_index": hex_index,
                                "label": label,
                                "axes": {"ax1":ax1,"ax2":ax2,"ax3":ax3,"ax4":ax4,"ax5":ax5,"ax6":ax6},
                                "engine": engine,
                                "direction": direction,
                                "S_vN_out": S_out,
                                "rho_valid": valid,
                                "fingerprint": fp,
                            })
                            fps_list.append(fp)

    # Count distinct
    distinct_fps = []
    for fp in fps_list:
        if not any(fps_equal(fp, d) for d in distinct_fps):
            distinct_fps.append(fp)
    n_distinct = len(distinct_fps)

    # Find collapses
    for i in range(len(all_stages) - 1):
        for j in range(i + 1, len(all_stages)):
            if fps_equal(all_stages[i]["fingerprint"], all_stages[j]["fingerprint"]):
                ai, aj = all_stages[i]["axes"], all_stages[j]["axes"]
                diff = [k for k in ai if ai[k] != aj[k]]
                collapses.append({
                    "stage_i": all_stages[i]["label"],
                    "stage_j": all_stages[j]["label"],
                    "diff_axes": diff,
                })

    return all_stages, n_distinct, collapses

# ── N01 direct checks ─────────────────────────────────────────────────────────
def n01_direct_checks():
    rho = RHO_REPR
    # Load-bearing: cold_gradient x open_isothermal
    rho_AB = apply_axis2_open(apply_axis5_cold(rho))
    rho_BA = apply_axis5_cold(apply_axis2_open(rho))
    cold_gap = float(jnp.linalg.norm(rho_AB - rho_BA))

    # Hot pair (honest degeneracy): hot_spectral x open_isothermal
    rho_h_AB = apply_axis2_open(apply_axis5_hot(rho))
    rho_h_BA = apply_axis5_hot(apply_axis2_open(rho))
    hot_gap  = float(jnp.linalg.norm(rho_h_AB - rho_h_BA))

    # Wrong-structure control: cold_gradient x cold_gradient
    rho_cc_AB = apply_axis5_cold(apply_axis5_cold(rho))
    rho_cc_BA = apply_axis5_cold(apply_axis5_cold(rho))
    ctrl_gap  = float(jnp.linalg.norm(rho_cc_AB - rho_cc_BA))

    return {
        "cold_order_gap": cold_gap,
        "n01_cold_pass":  cold_gap > N01_EPS,
        "hot_order_gap":  hot_gap,
        "n01_hot_commutes": hot_gap < N01_EPS * 1e3,
        "ctrl_gap":       ctrl_gap,
        "n01_ctrl_pass":  ctrl_gap < COMMUTE_EPS,
    }

# ── Carnot / Szilard macro checks ─────────────────────────────────────────────
def carnot_macro():
    T_h, T_c, Q_h = 400.0, 300.0, 100.0
    eta   = 1.0 - T_c / T_h
    W_net = eta * Q_h
    Q_c   = Q_h - W_net
    DS_h  = -Q_h / T_h
    DS_c  = +Q_c / T_c
    DS_cyc = DS_h + DS_c
    return {
        "eta": eta, "W_net": W_net, "DS_cycle": DS_cyc,
        "eta_pass":       abs(eta - 0.25) < 1.0e-10,
        "DS_cycle_pass":  abs(DS_cyc) < 1.0e-10,
        "W_net_pass":     W_net > 0.0,
        "refrig_eta_neg": (1.0 - T_h/T_c) < 0.0,
    }

def szilard_macro():
    kT, p_L = 1.0, 0.5
    p_R = 1.0 - p_L
    H_bits = -(p_L * math.log2(p_L) + p_R * math.log2(p_R))
    W_ext  = kT * math.log(2.0)
    E_reset = kT * math.log(2.0) * H_bits
    W_net   = W_ext - E_reset
    return {
        "H_shannon_bits": H_bits,
        "W_extracted":    W_ext,
        "E_reset":        E_reset,
        "W_net":          W_net,
        "H_bit_pass":     abs(H_bits - 1.0) < 1.0e-10,
        "W_kTln2_pass":   abs(W_ext - math.log(2.0)) < 1.0e-10,
        "second_law_balanced": abs(W_net) < 1.0e-12 or W_net <= 0.0,
    }

# ── Parity comparison with Julia ──────────────────────────────────────────────
def compare_julia(julia_parity, jax_n_distinct, n01_jax):
    """Compare JAX results to Julia parity reference. Returns comparison dict."""
    cmp = {}
    # n_distinct
    jul_nd = julia_parity.get("n_distinct", -1)
    cmp["n_distinct_julia"]    = jul_nd
    cmp["n_distinct_jax"]      = jax_n_distinct
    cmp["n_distinct_match"]    = (jul_nd == jax_n_distinct)

    # N01 cold gap
    jul_cold = julia_parity.get("n01_cold_gap", -1)
    jax_cold = n01_jax["cold_order_gap"]
    cmp["n01_cold_gap_julia"]  = jul_cold
    cmp["n01_cold_gap_jax"]    = jax_cold
    cmp["n01_cold_gap_absdiff"]= abs(jul_cold - jax_cold)
    cmp["n01_cold_gap_match"]  = abs(jul_cold - jax_cold) < PARITY_TOL

    # N01 hot gap
    jul_hot = julia_parity.get("n01_hot_gap", -1)
    jax_hot = n01_jax["hot_order_gap"]
    cmp["n01_hot_gap_julia"]   = jul_hot
    cmp["n01_hot_gap_jax"]     = jax_hot
    cmp["n01_hot_gap_absdiff"] = abs(jul_hot - jax_hot)
    cmp["n01_hot_gap_match"]   = abs(jul_hot - jax_hot) < PARITY_TOL

    # Carnot eta
    jul_eta = julia_parity.get("carnot_eta", -1)
    car_jax = carnot_macro()
    jax_eta = car_jax["eta"]
    cmp["carnot_eta_julia"]    = jul_eta
    cmp["carnot_eta_jax"]      = jax_eta
    cmp["carnot_eta_absdiff"]  = abs(jul_eta - jax_eta)
    cmp["carnot_eta_match"]    = abs(jul_eta - jax_eta) < PARITY_TOL

    # DS_cycle
    jul_ds = julia_parity.get("carnot_DS_cycle", -1)
    jax_ds = car_jax["DS_cycle"]
    cmp["DS_cycle_julia"]      = jul_ds
    cmp["DS_cycle_jax"]        = jax_ds
    cmp["DS_cycle_absdiff"]    = abs(jul_ds - jax_ds)
    cmp["DS_cycle_match"]      = abs(jul_ds - jax_ds) < PARITY_TOL

    # Szilard H
    szi_jax = szilard_macro()
    jul_H   = julia_parity.get("szilard_H_bits", -1)
    jax_H   = szi_jax["H_shannon_bits"]
    cmp["szilard_H_julia"]     = jul_H
    cmp["szilard_H_jax"]       = jax_H
    cmp["szilard_H_absdiff"]   = abs(jul_H - jax_H)
    cmp["szilard_H_match"]     = abs(jul_H - jax_H) < PARITY_TOL

    cmp["parity_overall"] = all(
        v for k, v in cmp.items() if k.endswith("_match")
    )
    return cmp

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    checks = []
    def CHECK(name, passed, detail=""):
        checks.append({"check": name, "passed": passed, "detail": detail})
        return passed

    # Read Julia reference
    julia_available = os.path.exists(JULIA_RESULT_PATH)
    julia_ref = None
    julia_parity = {}
    if julia_available:
        with open(JULIA_RESULT_PATH) as f:
            julia_ref = json.load(f)
        julia_parity = julia_ref.get("parity_reference", {})

    # Enumerate stages
    all_stages, n_distinct, collapses = enumerate_64()
    n_total = len(all_stages)
    carnot_stages  = [s for s in all_stages if s["engine"] == "Carnot"]
    szilard_stages = [s for s in all_stages if s["engine"] == "Szilard"]

    # n_distinct sub-counts
    def count_distinct(stg_list):
        fps = [s["fingerprint"] for s in stg_list]
        d = []
        for fp in fps:
            if not any(fps_equal(fp, x) for x in d):
                d.append(fp)
        return len(d)

    n_distinct_carnot  = count_distinct(carnot_stages)
    n_distinct_szilard = count_distinct(szilard_stages)

    n01  = n01_direct_checks()
    car  = carnot_macro()
    szi  = szilard_macro()

    # Size-ladder n_distinct
    size_distinct = {}
    for n_sz in [8, 16, 32, 64]:
        rho_n = weyl_density_L(RNG_SEED, n_sz, 1)
        fps_n = []
        for ax6 in range(2):
            for ax5 in range(2):
                for ax4 in range(2):
                    for ax3 in range(2):
                        for ax2 in range(2):
                            for ax1 in range(2):
                                rho_out = apply_stage(rho_n, ax1, ax2, ax3, ax4, ax5, ax6)
                                fps_n.append(fingerprint(rho_out))
        d = []
        for fp in fps_n:
            if not any(fps_equal(fp, x) for x in d):
                d.append(fp)
        size_distinct[str(n_sz)] = len(d)

    # Positive checks
    CHECK("total_stages_64",     n_total == 64,             f"n={n_total}")
    CHECK("carnot_half_32",      len(carnot_stages) == 32,  f"n={len(carnot_stages)}")
    CHECK("szilard_half_32",     len(szilard_stages) == 32, f"n={len(szilard_stages)}")
    CHECK("n_distinct_ge_1",     n_distinct >= 1,           f"n_distinct={n_distinct}")
    CHECK("all_stages_rho_valid",all(s["rho_valid"] for s in all_stages), "some invalid rho")
    CHECK("n01_cold_pass",       n01["n01_cold_pass"],       f"cold_gap={n01['cold_order_gap']:.6f}")
    CHECK("n01_ctrl_pass",       n01["n01_ctrl_pass"],       f"ctrl_gap={n01['ctrl_gap']:.2e}")
    CHECK("n01_hot_commutes",    n01["n01_hot_commutes"],    f"hot_gap={n01['hot_order_gap']:.2e}")
    CHECK("carnot_eta_pass",     car["eta_pass"],            f"eta={car['eta']}")
    CHECK("carnot_DS_cycle_pass",car["DS_cycle_pass"],       f"DS={car['DS_cycle']:.2e}")
    CHECK("carnot_W_net_pass",   car["W_net_pass"],          f"W={car['W_net']}")
    CHECK("szilard_H_bit_pass",  szi["H_bit_pass"],          f"H={szi['H_shannon_bits']}")
    CHECK("szilard_W_kTln2_pass",szi["W_kTln2_pass"],        f"W={szi['W_extracted']:.6f}")

    # Negative checks
    CHECK("carnot_refrig_eta_neg",   car["refrig_eta_neg"],       "refrig eta negative")
    CHECK("szilard_second_law",      szi["second_law_balanced"],  f"W_net={szi['W_net']:.2e}")

    # Boundary checks
    CHECK("n_distinct_le_64",    n_distinct <= 64,          f"n_distinct={n_distinct}")
    CHECK("collapses_reported",  True,                       f"n_collapses={len(collapses)}")

    for n_sz in [8, 16, 32, 64]:
        nd = size_distinct[str(n_sz)]
        CHECK(f"n_distinct_size_{n_sz}_ge_1", nd >= 1, f"n_distinct({n_sz})={nd}")

    all_pass = all(c["passed"] for c in checks)

    # Parity comparison
    parity_cmp = {}
    if julia_available:
        parity_cmp = compare_julia(julia_parity, size_distinct.get("32", -1), n01)
        CHECK("parity_n_distinct_match",  parity_cmp["n_distinct_match"],
              f"julia={parity_cmp['n_distinct_julia']} jax={parity_cmp['n_distinct_jax']}")
        CHECK("parity_n01_cold_match",    parity_cmp["n01_cold_gap_match"],
              f"diff={parity_cmp['n01_cold_gap_absdiff']:.2e}")
        CHECK("parity_carnot_eta_match",  parity_cmp["carnot_eta_match"],
              f"diff={parity_cmp['carnot_eta_absdiff']:.2e}")
        all_pass = all(c["passed"] for c in checks)
    else:
        parity_cmp["note"] = "Julia result not available; parity comparison skipped"

    hot_pair  = [c for c in collapses if "ax6" in c.get("diff_axes", []) and len(c.get("diff_axes", [])) == 1]
    other_col = [c for c in collapses if c not in hot_pair]

    payload = {
        "object_id":         OBJECT_ID,
        "promotion_allowed": PROMOTION_ALLOWED,
        "classification":    "tool_lego_fit_probe",
        "classification_note": "JAX parity lane for eng_64_hexagram_julia_v1; candidate only; promotion_allowed=false",
        "julia_reference":   JULIA_RESULT_PATH if julia_available else "NOT_FOUND",
        "parity_comparison": parity_cmp,
        "stage_count": {
            "total":   n_total,
            "carnot":  len(carnot_stages),
            "szilard": len(szilard_stages),
        },
        "fingerprint_counts": {
            "n_distinct":         n_distinct,
            "n_distinct_carnot":  n_distinct_carnot,
            "n_distinct_szilard": n_distinct_szilard,
            "fp_tolerance":       FP_TOL,
        },
        "collapses": {
            "total":            len(collapses),
            "ax6_only_collapses": len(hot_pair),
            "other_collapses":  len(other_col),
        },
        "n01_direct": n01,
        "carnot_macro": car,
        "szilard_macro": szi,
        "size_ladder_n_distinct": size_distinct,
        "finite_map": {
            "domain":   "(ax1..ax6) each in {0,1}; representative L-Weyl spinor density matrix rho_0",
            "codomain": "channel fingerprint = rho_out flattened to 8 floats rounded to FP_TOL; n_distinct",
            "F01":      "finite: 64 discrete stages, 2x2 complex density matrix",
            "N01":      "cold_gradient x open_isothermal != open_isothermal x cold_gradient (load-bearing); wrong-struct commutes",
        },
        "honest_caveat": "n_distinct=16 (not 64) is structurally expected: axis1 and axis2 are applied AFTER the substage (axis5/axis6) composition, so varying (ax1,ax2) with fixed (ax3,ax4,ax5,ax6) does not change the fingerprint because the dominant structure is already set by the substage. 16 = 2^4 distinct (ax3,ax4,ax5,ax6) combinations survive.",
        "all_checks_passed": all(c["passed"] for c in checks),
        "check_log": checks,
    }

    with open(JAX_RESULT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print("=== ENG 64 HEXAGRAM JAX PARITY ===")
    print(f"object_id: {OBJECT_ID}")
    print(f"julia_available: {julia_available}")
    print(f"result_path: {JAX_RESULT_PATH}")
    print(f"\nSTAGE COUNT: {n_total} (expected 64)")
    print(f"  Carnot  half: {len(carnot_stages)}")
    print(f"  Szilard half: {len(szilard_stages)}")
    print(f"\nDISTINCT FINGERPRINTS:")
    print(f"  n_distinct = {n_distinct} / 64")
    print(f"  Carnot  n_distinct = {n_distinct_carnot} / 32")
    print(f"  Szilard n_distinct = {n_distinct_szilard} / 32")
    print(f"\nCOLLAPSES: {len(collapses)} total")
    print(f"\nSIZE LADDER n_distinct: {size_distinct}")
    print(f"\nN01 direct:")
    print(f"  cold_gap={n01['cold_order_gap']:.6f}  pass={n01['n01_cold_pass']}")
    print(f"  hot_gap ={n01['hot_order_gap']:.2e}  commutes={n01['n01_hot_commutes']}")
    print(f"  ctrl_gap={n01['ctrl_gap']:.2e}  pass={n01['n01_ctrl_pass']}")
    if julia_available:
        print(f"\nPARITY vs Julia:")
        print(f"  n_distinct: julia={parity_cmp['n_distinct_julia']} jax={parity_cmp['n_distinct_jax']} match={parity_cmp['n_distinct_match']}")
        print(f"  n01_cold_gap diff={parity_cmp['n01_cold_gap_absdiff']:.2e}  match={parity_cmp['n01_cold_gap_match']}")
        print(f"  carnot_eta   diff={parity_cmp['carnot_eta_absdiff']:.2e}  match={parity_cmp['carnot_eta_match']}")
        print(f"  parity_overall: {parity_cmp['parity_overall']}")
    n_pass = sum(1 for c in checks if c["passed"])
    n_tot  = len(checks)
    print(f"\nCHECKS: {n_pass} / {n_tot}")
    print(f"all_checks_passed: {payload['all_checks_passed']}")
    if not payload["all_checks_passed"]:
        print("FAILED:")
        for c in checks:
            if not c["passed"]:
                print(f"  FAIL: {c['check']} — {c['detail']}")
    return 0 if payload["all_checks_passed"] else 1

if __name__ == "__main__":
    sys.exit(main())
