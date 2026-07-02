#!/usr/bin/env python3
"""
axorth_jax.py — JAX audit lane for axorth_axis045_independence_v1

Claim ceiling:
  Finite-map axis-independence probe over F01+N01.
  Does NOT assert layer-completion, manifold admission, coupling,
  bridge, flux, or physics. promotion_allowed=false.

Root constraints:
  F01: finite carrier — 2x2x2 factorial = 8 cells; 2x2 qubit density matrices.
  N01: Ti (z-dephase) and Fi (x-rotation) do NOT commute;
       Fe (z-rotation) and Ti DO commute (wrong-structure control).

Finite map:
  Domain:  (axis0 in {low_q=0.1, high_q=0.9}) x
           (axis4 in {deductive, inductive}) x
           (axis5 in {spectral, gradient})
  Codomain: (final_rho, von_Neumann_entropy, purity, Tr_rho_sz,
             trajectory_purity_complement, order_gap, commuting_control_gap)

Axis definitions (three DIFFERENT KINDS):
  axis0 = entropy MAGNITUDE (dephasing amount q)
  axis4 = loop DIRECTION (stroke order UEUE vs EUEU)
  axis5 = REGIME/ALGEBRA (which unitary family: Fi=spectral vs Ry_pi3=gradient)

Parity:
  Compares Julia reference values from axorth_julia_results.json.
  Max diff must be < 1e-8 on entropy, purity, Tz for all 8 cells.

Re-run:
  /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 /tmp/axorth_jax.py
"""

import os
import json
import math
import cmath

def cmath_exp(phi):
    """Return e^(i*phi) as a Python complex."""
    return complex(math.cos(phi), math.sin(phi))

# ── JAX setup ────────────────────────────────────────────────────────────────
os.environ["JAX_ENABLE_X64"] = "1"
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
from jax import jit
import numpy as np  # only for JSON serialization helpers — not for compute

RESULT_PATH   = "/tmp/axorth_jax_results.json"
JULIA_RESULT  = "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/axorth_julia_results.json"
OBJECT_ID     = "axorth_axis045_independence_v1_jax"
PROMOTION_ALLOWED = False
PARITY_EPS    = 1.0e-8
COLLAPSE_COS_THRESH = 0.99

# ── Constants ──────────────────────────────────────────────────────────────────
I2 = jnp.eye(2, dtype=jnp.complex128)
sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
sz = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
sy = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)

# Fi: x-rotation by pi/2
_a = math.pi / 4.0
Fi = math.cos(_a) * I2 - 1j * math.sin(_a) * sx

# Fe: z-rotation by pi/2 (commutes with Ti)
Fe = math.cos(_a) * I2 - 1j * math.sin(_a) * sz

# Ry_pi3: y-rotation by pi/3
_b = (math.pi / 3.0) / 2.0
Ry_pi3 = math.cos(_b) * I2 - 1j * math.sin(_b) * sy

# ── Operators ──────────────────────────────────────────────────────────────────
def apply_U(U, rho):
    """Unitary channel: U rho U†"""
    return U @ rho @ U.conj().T

def Ti_dephase(rho, q):
    """Partial z-dephase: (1-q)*rho + q*diag(rho)"""
    diag_rho = jnp.diag(jnp.diag(rho))
    return (1.0 - q) * rho + q * diag_rho

# ── Observables ───────────────────────────────────────────────────────────────
def von_neumann_entropy(rho):
    """von Neumann entropy via eigenvalues of Hermitian part."""
    rho_h = (rho + rho.conj().T) / 2.0
    evals = jnp.linalg.eigvalsh(rho_h)
    # clip negative eigenvalues from numerical noise
    evals = jnp.where(evals > 1e-14, evals, 0.0)
    s = -jnp.sum(jnp.where(evals > 0, evals * jnp.log(evals), 0.0))
    return jnp.real(s)

def purity(rho):
    return jnp.real(jnp.trace(rho @ rho))

def Tr_rho_sz(rho):
    return jnp.real(jnp.trace(rho @ sz))

def density_valid(rho, tol=1e-8):
    trace_ok = abs(float(jnp.real(jnp.trace(rho))) - 1.0) < tol
    herm_ok  = float(jnp.linalg.norm(rho - rho.conj().T)) < tol
    evals    = jnp.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    pos_ok   = bool(jnp.all(evals >= -tol))
    return trace_ok and herm_ok and pos_ok

# ── Reference state ───────────────────────────────────────────────────────────
def reference_state():
    theta = math.pi / 3.0
    phi   = math.pi / 4.0
    c0 = complex(math.cos(theta / 2.0), 0.0)
    c1 = cmath_exp(phi) * math.sin(theta / 2.0)
    psi = jnp.array([c0, c1], dtype=jnp.complex128)
    psi = psi / jnp.linalg.norm(psi)
    return jnp.outer(psi, psi.conj())

# ── Stroke sequences ──────────────────────────────────────────────────────────
def make_strokes(axis4: str, axis5: str, q: float):
    """Returns list of (kind, op) tuples."""
    E = lambda rho: Ti_dephase(rho, q)
    if axis5 == "spectral":
        U1, U2 = Fi, Fe
    else:  # gradient
        U1, U2 = Ry_pi3, Fi
    if axis4 == "deductive":
        return [("U", U1), ("E", E), ("U", U2), ("E", E)]
    else:
        return [("E", E), ("U", U1), ("E", E), ("U", U2)]

def apply_strokes_with_traj(rho0, strokes):
    """Apply strokes, recording purity_complement trajectory."""
    rho  = rho0
    traj = []
    for (kind, op) in strokes:
        if kind == "U":
            rho = apply_U(op, rho)
        else:
            rho = op(rho)
        traj.append(float(jnp.real(1.0 - jnp.trace(rho @ rho))))
    return rho, traj

def apply_strokes(rho0, strokes):
    rho = rho0
    for (kind, op) in strokes:
        if kind == "U":
            rho = apply_U(op, rho)
        else:
            rho = op(rho)
    return rho

# ── Order gap ─────────────────────────────────────────────────────────────────
def order_gap(rho0, q, axis5):
    s_ded = make_strokes("deductive", axis5, q)
    s_ind = make_strokes("inductive", axis5, q)
    rho_ded = apply_strokes(rho0, s_ded)
    rho_ind = apply_strokes(rho0, s_ind)
    return float(jnp.linalg.norm(rho_ded - rho_ind))

def commuting_control_gap(rho0, q):
    E = lambda rho: Ti_dephase(rho, q)
    s_ue = [("U", Fe), ("E", E), ("U", Fe), ("E", E)]
    s_eu = [("E", E), ("U", Fe), ("E", E), ("U", Fe)]
    rho_ue = apply_strokes(rho0, s_ue)
    rho_eu = apply_strokes(rho0, s_eu)
    return float(jnp.linalg.norm(rho_ue - rho_eu))

# ── Compute 2x2x2 factorial ───────────────────────────────────────────────────
Q_LOW  = 0.1
Q_HIGH = 0.9

def compute_factorial():
    rho0 = reference_state()
    assert density_valid(rho0), "Reference state invalid"
    cells = []
    for q in [Q_LOW, Q_HIGH]:
        axis0_label = "low_q" if q < 0.5 else "high_q"
        for axis4 in ["deductive", "inductive"]:
            for axis5 in ["spectral", "gradient"]:
                strokes = make_strokes(axis4, axis5, q)
                rho_f, traj = apply_strokes_with_traj(rho0, strokes)
                S_f  = float(von_neumann_entropy(rho_f))
                p_f  = float(purity(rho_f))
                tz_f = float(Tr_rho_sz(rho_f))
                og   = order_gap(rho0, q, axis5)
                cc   = commuting_control_gap(rho0, q)
                cells.append({
                    "axis0": axis0_label,
                    "axis4": axis4,
                    "axis5": axis5,
                    "q": q,
                    "von_Neumann_entropy": S_f,
                    "purity": p_f,
                    "Tr_rho_sz": tz_f,
                    "trajectory_purity_complement": traj,
                    "order_gap_axis4": og,
                    "commuting_control_gap": cc,
                    "rho_valid": density_valid(rho_f),
                })
    return cells, rho0

# ── Fingerprint and distinctness ──────────────────────────────────────────────
def fingerprint_ext(cell, digits=4):
    traj = cell["trajectory_purity_complement"]
    return (
        round(cell["von_Neumann_entropy"], digits),
        round(cell["purity"], digits),
        round(cell["Tr_rho_sz"], digits),
        round(traj[0], digits),
        round(traj[1], digits),
        round(traj[2], digits),
        round(traj[3], digits),
    )

def fingerprint_base(cell, digits=6):
    return (
        round(cell["von_Neumann_entropy"], digits),
        round(cell["purity"], digits),
        round(cell["Tr_rho_sz"], digits),
    )

def count_distinct(cells):
    fps_ext  = [fingerprint_ext(c) for c in cells]
    fps_base = [fingerprint_base(c) for c in cells]
    return len(set(fps_ext)), len(set(fps_base))

# ── Marginal effect vectors (extended, 28-dim) ─────────────────────────────────
def extended_sig(cell):
    traj = cell["trajectory_purity_complement"]
    return [cell["von_Neumann_entropy"], cell["purity"], cell["Tr_rho_sz"]] + traj

def marginal_effect(cells, vary_axis):
    lookup = {}
    for c in cells:
        k = (c["axis0"], c["axis4"], c["axis5"])
        lookup[k] = extended_sig(c)

    if vary_axis == "axis0":
        pairs = [
            ("deductive", "spectral"),
            ("deductive", "gradient"),
            ("inductive", "spectral"),
            ("inductive", "gradient"),
        ]
        effects = []
        for (a4, a5) in pairs:
            hi = lookup[("high_q", a4, a5)]
            lo = lookup[("low_q", a4, a5)]
            effects.extend([h - l for h, l in zip(hi, lo)])
        return effects

    elif vary_axis == "axis4":
        pairs = [
            ("low_q",  "spectral"),
            ("low_q",  "gradient"),
            ("high_q", "spectral"),
            ("high_q", "gradient"),
        ]
        effects = []
        for (a0, a5) in pairs:
            ded = lookup[(a0, "deductive", a5)]
            ind = lookup[(a0, "inductive", a5)]
            effects.extend([d - i for d, i in zip(ded, ind)])
        return effects

    else:  # axis5
        pairs = [
            ("low_q",  "deductive"),
            ("low_q",  "inductive"),
            ("high_q", "deductive"),
            ("high_q", "inductive"),
        ]
        effects = []
        for (a0, a4) in pairs:
            spec = lookup[(a0, a4, "spectral")]
            grad = lookup[(a0, a4, "gradient")]
            effects.extend([s - g for s, g in zip(spec, grad)])
        return effects

def cosine_similarity(u, v):
    u, v = np.array(u, dtype=float), np.array(v, dtype=float)
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    if nu < 1e-14 or nv < 1e-14:
        return 0.0
    return float(np.dot(u, v) / (nu * nv))

# ── Six-axis collapse matrix ──────────────────────────────────────────────────
def six_axis_collapse_matrix(cells):
    e0 = marginal_effect(cells, "axis0")
    e4 = marginal_effect(cells, "axis4")
    e5 = marginal_effect(cells, "axis5")
    # Commuting control: effect of commuting_control_gap across axis0 levels
    ctrl_vals = [c["commuting_control_gap"] for c in cells]
    e_ctrl = [ctrl_vals[i] - ctrl_vals[i + 4] for i in range(min(4, len(ctrl_vals) - 4))]
    # Pad to same length
    e_ctrl_full = e_ctrl + [0.0] * (len(e0) - len(e_ctrl))

    pairs = [
        ("axis0", "axis4", e0, e4),
        ("axis0", "axis5", e0, e5),
        ("axis4", "axis5", e4, e5),
        ("axis0", "ctrl",  e0, e_ctrl_full),
        ("axis4", "ctrl",  e4, e_ctrl_full),
        ("axis5", "ctrl",  e5, e_ctrl_full),
    ]
    matrix = []
    for (n1, n2, u, v) in pairs:
        cs = cosine_similarity(u, v)
        matrix.append({
            "axis_pair": f"{n1} vs {n2}",
            "cos_sim": cs,
            "collapsed": abs(cs) >= COLLAPSE_COS_THRESH,
        })
    return matrix

# ── Wrong-structure controls ──────────────────────────────────────────────────
def wrong_structure_controls(rho0):
    results = []

    # (a) Commuting Fe+Ti — order gap should collapse
    for q in [Q_LOW, Q_HIGH]:
        gap = commuting_control_gap(rho0, q)
        results.append({
            "label": f"commuting_Fe_Ti_q={q}",
            "q": q,
            "order_gap": gap,
            "expect_near_zero": True,
            "passed": gap < 1e-6,
        })

    # (b) Owner example: spectral-at-low-entropy vs gradient-at-high-entropy
    rho_spec_low  = apply_strokes(rho0, make_strokes("deductive", "spectral", Q_LOW))
    rho_grad_high = apply_strokes(rho0, make_strokes("deductive", "gradient", Q_HIGH))
    s_sl  = float(von_neumann_entropy(rho_spec_low))
    s_gh  = float(von_neumann_entropy(rho_grad_high))
    fp_sl = fingerprint_base({"von_Neumann_entropy": s_sl,
                               "purity": float(purity(rho_spec_low)),
                               "Tr_rho_sz": float(Tr_rho_sz(rho_spec_low))})
    fp_gh = fingerprint_base({"von_Neumann_entropy": s_gh,
                               "purity": float(purity(rho_grad_high)),
                               "Tr_rho_sz": float(Tr_rho_sz(rho_grad_high))})
    results.append({
        "label": "owner_example_spec_low_vs_grad_high",
        "S_spectral_low_q": s_sl,
        "S_gradient_high_q": s_gh,
        "fingerprints_distinct": fp_sl != fp_gh,
        "passed": fp_sl != fp_gh,
    })

    # (c) Inductive vs deductive at high_q spectral
    rho_ind = apply_strokes(rho0, make_strokes("inductive", "spectral", Q_HIGH))
    rho_ded = apply_strokes(rho0, make_strokes("deductive", "spectral", Q_HIGH))
    s_ind   = float(von_neumann_entropy(rho_ind))
    s_ded   = float(von_neumann_entropy(rho_ded))
    fp_ind  = fingerprint_base({"von_Neumann_entropy": s_ind,
                                 "purity": float(purity(rho_ind)),
                                 "Tr_rho_sz": float(Tr_rho_sz(rho_ind))})
    fp_ded  = fingerprint_base({"von_Neumann_entropy": s_ded,
                                 "purity": float(purity(rho_ded)),
                                 "Tr_rho_sz": float(Tr_rho_sz(rho_ded))})
    results.append({
        "label": "owner_example_inductive_positive_feedback",
        "S_inductive_high_q": s_ind,
        "S_deductive_high_q": s_ded,
        "fingerprints_distinct": fp_ind != fp_ded,
        "passed": fp_ind != fp_ded,
    })

    return results

# ── Parity check against Julia ────────────────────────────────────────────────
def parity_check(cells, julia_path):
    if not os.path.exists(julia_path):
        return {"status": "julia_result_not_found", "max_diff": None, "passed": False}

    with open(julia_path) as f:
        julia_data = json.load(f)

    julia_targets = julia_data.get("parity_targets", [])
    if not julia_targets:
        return {"status": "no_parity_targets_in_julia_result", "max_diff": None, "passed": False}

    # Build JAX lookup by cell_key
    jax_lookup = {}
    for c in cells:
        key = f"{c['axis0']}_{c['axis4']}_{c['axis5']}"
        jax_lookup[key] = c

    diffs = []
    cell_diffs = []
    for jt in julia_targets:
        key = jt["cell_key"]
        if key not in jax_lookup:
            cell_diffs.append({"key": key, "status": "missing_from_jax"})
            continue
        jc = jax_lookup[key]
        d_S  = abs(jc["von_Neumann_entropy"] - jt["von_Neumann_entropy"])
        d_p  = abs(jc["purity"] - jt["purity"])
        d_tz = abs(jc["Tr_rho_sz"] - jt["Tr_rho_sz"])
        max_d = max(d_S, d_p, d_tz)
        diffs.append(max_d)
        cell_diffs.append({
            "key": key,
            "jax_S": jc["von_Neumann_entropy"],
            "julia_S": jt["von_Neumann_entropy"],
            "diff_S": d_S,
            "diff_purity": d_p,
            "diff_Tz": d_tz,
            "max_diff": max_d,
            "passed": max_d < PARITY_EPS,
        })

    max_diff = max(diffs) if diffs else None
    return {
        "status": "checked",
        "max_diff": max_diff,
        "parity_eps": PARITY_EPS,
        "passed": max_diff is not None and max_diff < PARITY_EPS,
        "cell_diffs": cell_diffs,
    }

# ── Size-ladder check ─────────────────────────────────────────────────────────
def run_size_ladder():
    """Random-state ensemble checks for each N in [8, 16, 32, 64]."""
    rng = np.random.default_rng(20260604)
    results = []
    for N in [8, 16, 32, 64]:
        cc_gaps = []
        og_spec = []
        og_grad = []
        for _ in range(N):
            theta = math.pi * rng.random()
            phi   = 2 * math.pi * rng.random()
            psi   = jnp.array([complex(math.cos(theta / 2.0), 0.0),
                                cmath_exp(phi) * math.sin(theta / 2.0)],
                               dtype=jnp.complex128)
            psi  /= jnp.linalg.norm(psi)
            rho0  = jnp.outer(psi, psi.conj())
            cc_gaps.append(commuting_control_gap(rho0, Q_HIGH))
            og_spec.append(order_gap(rho0, Q_HIGH, "spectral"))
            og_grad.append(order_gap(rho0, Q_HIGH, "gradient"))

        results.append({
            "N": N,
            "max_commuting_control_gap": float(max(cc_gaps)),
            "mean_commuting_control_gap": float(sum(cc_gaps) / len(cc_gaps)),
            "commuting_control_near_zero": max(cc_gaps) < 1e-6,
            "min_order_gap_spectral": float(min(og_spec)),
            "min_order_gap_gradient": float(min(og_grad)),
            "axis4_split_spectral": min(og_spec) > 1e-9,
            "axis4_split_gradient": min(og_grad) > 1e-9,
        })
    return results

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("Running axorth_axis045_independence_v1_jax ...")

    cells, rho0 = compute_factorial()

    # Test 1: distinct fingerprints
    n_distinct_ext, n_distinct_base = count_distinct(cells)

    # Test 2: marginal independence
    e0 = marginal_effect(cells, "axis0")
    e4 = marginal_effect(cells, "axis4")
    e5 = marginal_effect(cells, "axis5")
    cs_04 = cosine_similarity(e0, e4)
    cs_05 = cosine_similarity(e0, e5)
    cs_45 = cosine_similarity(e4, e5)
    axis0_marginal_independent = abs(cs_04) < COLLAPSE_COS_THRESH and abs(cs_05) < COLLAPSE_COS_THRESH
    axis4_marginal_independent = abs(cs_04) < COLLAPSE_COS_THRESH and abs(cs_45) < COLLAPSE_COS_THRESH
    axis5_marginal_independent = abs(cs_05) < COLLAPSE_COS_THRESH and abs(cs_45) < COLLAPSE_COS_THRESH

    # Test 3: six-axis collapse matrix
    collapse_matrix = six_axis_collapse_matrix(cells)
    any_pair_collapses = any(m["collapsed"] for m in collapse_matrix)

    # Parity
    parity = parity_check(cells, JULIA_RESULT)
    parity_max_diff = parity["max_diff"]

    # Size ladder
    ladder = run_size_ladder()

    # Wrong-structure controls
    wsc = wrong_structure_controls(rho0)

    # Parity targets (sorted canonical order)
    sorted_cells = sorted(cells, key=lambda c: (c["axis0"], c["axis4"], c["axis5"]))
    parity_targets = [{
        "cell_key": f"{c['axis0']}_{c['axis4']}_{c['axis5']}",
        "von_Neumann_entropy": c["von_Neumann_entropy"],
        "purity": c["purity"],
        "Tr_rho_sz": c["Tr_rho_sz"],
    } for c in sorted_cells]

    all_pass = (
        n_distinct_ext == 8 and
        axis0_marginal_independent and
        axis4_marginal_independent and
        axis5_marginal_independent and
        not any_pair_collapses and
        parity["passed"]
    )

    result = {
        "object_id": OBJECT_ID,
        "claim_ceiling": "Finite-map axis-independence probe over F01+N01. NOT layer-complete. NOT bridge. promotion_allowed=false.",
        "promotion_allowed": PROMOTION_ALLOWED,
        "classification": "tool_lego_fit_probe",
        "jax_version": jax.__version__,
        "jax_x64_enabled": jax.config.jax_enable_x64,
        "root_constraints_in_force": {
            "F01": "finite carrier: 2x2x2 factorial = 8 cells; 8/16/32/64 random ensembles; 2x2 complex128 density matrices",
            "N01": "Ti (z-dephase) and Fi (x-rotation) noncommuting; Fe and Ti commuting control",
        },
        "finite_map": {
            "domain": "(axis0 in {low_q=0.1, high_q=0.9}) x (axis4 in {deductive, inductive}) x (axis5 in {spectral, gradient})",
            "codomain": "(final_rho, von_Neumann_entropy, purity, Tr_rho_sz, trajectory_purity_complement, order_gap, commuting_control_gap)",
        },
        "factorial_cells": cells,
        "factorial_n_distinct": n_distinct_ext,
        "factorial_n_distinct_base_fingerprint": n_distinct_base,
        "marginal_effects": {
            "axis0_effect_vector": e0,
            "axis4_effect_vector": e4,
            "axis5_effect_vector": e5,
        },
        "pairwise_cos_similarities": {
            "axis0_vs_axis4": cs_04,
            "axis0_vs_axis5": cs_05,
            "axis4_vs_axis5": cs_45,
        },
        "axis0_marginal_independent": axis0_marginal_independent,
        "axis4_marginal_independent": axis4_marginal_independent,
        "axis5_marginal_independent": axis5_marginal_independent,
        "any_pair_collapses": any_pair_collapses,
        "six_axis_collapse_matrix": collapse_matrix,
        "parity": parity,
        "parity_max_diff": parity_max_diff,
        "parity_targets": parity_targets,
        "size_ladder_results": ladder,
        "wrong_structure_controls": wsc,
        "all_pass": all_pass,
        "honest_caveat": (
            "factorial_n_distinct=8 and !any_pair_collapses and all marginals independent required. "
            "Parity max diff must be < 1e-8 vs Julia reference. "
            "If any fails, axes collapse at that point — say so plainly."
        ),
        "blocked_consumers": [
            "layer_completion", "manifold_admission", "coupling",
            "bridge", "Axis0_bridge", "flux", "physics"
        ],
        "TOOL_MANIFEST": {
            "jax.numpy": {"used": True, "role": "load_bearing",
                          "reason": "all matrix operations and entropy computed via jnp; removal changes every verdict"},
            "jax_enable_x64": {"used": True, "role": "load_bearing",
                                "reason": "float64 required for parity < 1e-8 vs Julia; float32 would fail parity check"},
            "numpy": {"used": True, "role": "supportive",
                      "reason": "cosine similarity and JSON serialization only; not used for density matrix compute"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax.numpy": "load_bearing",
            "jax_enable_x64": "load_bearing",
            "numpy": "supportive",
        },
    }

    with open(RESULT_PATH, "w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(f"Result written to: {RESULT_PATH}")

    print("\n=== AXORTH JAX Summary ===")
    print(f"  factorial_n_distinct (ext)  : {n_distinct_ext}  (target=8)")
    print(f"  factorial_n_distinct (base) : {n_distinct_base}  (final-state only)")
    print(f"  axis0_marginal_indep        : {axis0_marginal_independent}")
    print(f"  axis4_marginal_indep        : {axis4_marginal_independent}")
    print(f"  axis5_marginal_indep        : {axis5_marginal_independent}")
    print(f"  any_pair_collapses          : {any_pair_collapses}")
    print(f"  cos_sim axis0 vs axis4      : {cs_04:.6f}")
    print(f"  cos_sim axis0 vs axis5      : {cs_05:.6f}")
    print(f"  cos_sim axis4 vs axis5      : {cs_45:.6f}")
    print(f"  parity_max_diff             : {parity_max_diff}")
    print(f"  parity_passed               : {parity['passed']}")
    print(f"  all_pass                    : {all_pass}")
    print("\nCollapse matrix:")
    for m in collapse_matrix:
        print(f"  {m['axis_pair']}: cos_sim={m['cos_sim']:.4f} collapsed={m['collapsed']}")

    return all_pass

if __name__ == "__main__":
    ok = main()
    exit(0 if ok else 1)
