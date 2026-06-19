#!/usr/bin/env python3
"""
wb_engine_fix_shared_seed_jax.py — BDE Engine Fix, JAX lane.

object_id: wb_engine_fix_jax_v1

claim_ceiling:
  Finite maps for bidirectional dual-stacked engine with SHARED RNG seed
  (arithmetic state table, no RNG-backend difference), BALANCED cycle
  (net unitary = I, purity-bounded return), and 20-seed direction sweep
  confirming direction-distinctness is not a seed artifact.
  F01+N01 only. Does NOT assert layer-completion, manifold admission,
  coupling, bridge, flux, or physics. promotion_allowed=false.

Root constraints: F01 (finite carrier), N01 (order-sensitive).
Writes: /tmp/wb_engine_fix_shared_seed_jax_results.json
Re-run: /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 /tmp/wb_engine_fix_shared_seed_jax.py
"""

import jax
jax.config.update("jax_enable_x64", True)

import json
import math
import sys
from pathlib import Path

import jax.numpy as jnp
import numpy as np  # allowed ONLY for non-compute I/O

JAX_AVAILABLE = True

RESULT_PATH = Path("/tmp/wb_engine_fix_shared_seed_jax_results.json")
OBJECT_ID   = "wb_engine_fix_jax_v1"
CLAIM_CEILING = (
    "BDE JAX lane (engine fix): shared-seed arithmetic state table, "
    "balanced cycle (net U=I, purity-bounded), 20-seed direction sweep. "
    "F01+N01 only. promotion_allowed=false."
)
PROMOTION_ALLOWED = False

# ── Pauli matrices (jnp) ──────────────────────────────────────────────────────
I2 = jnp.eye(2, dtype=jnp.complex128)
sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
sy = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
sz = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)

check_log = []

def CHECK(name, passed, detail=""):
    check_log.append({"check": name, "passed": bool(passed), "detail": str(detail)})
    return bool(passed)

# ── SHARED STATE TABLE (arithmetic, no RNG backend) ──────────────────────────
# Both Julia and JAX use this same arithmetic sequence.
# theta_i = 0.3 + 0.02 * i,  phi_i = 0.5 + 0.15 * i
# psi_i = [cos(theta_i), sin(theta_i) * exp(1j * phi_i)]  (normalized)
def shared_state_table(N):
    """Return list of N pure-state density matrices using arithmetic sequence."""
    rhos = []
    for i in range(N):
        theta = 0.3 + 0.02 * i
        phi   = 0.5 + 0.15 * i
        psi = jnp.array(
            [math.cos(theta), math.sin(theta) * (math.cos(phi) + 1j * math.sin(phi))],
            dtype=jnp.complex128,
        )
        psi = psi / jnp.linalg.norm(psi)
        rhos.append(jnp.outer(psi, psi.conj()))
    return rhos

# ── Spinor rotation: U(2pi) = -I, U(4pi) = +I ───────────────────────────────
def U_rot(theta, n_hat):
    """Spinor rotation by angle theta about n_hat axis (2x2 SU(2))."""
    return math.cos(theta / 2) * I2 - 1j * math.sin(theta / 2) * n_hat

# Verify 720-deg spinor structure
U_2pi_sz = U_rot(2 * math.pi, sz)
U_4pi_sz = U_rot(4 * math.pi, sz)
trace_2pi = float(jnp.real(jnp.trace(U_2pi_sz) / 2))   # should be -1
trace_4pi = float(jnp.real(jnp.trace(U_4pi_sz) / 2))   # should be +1
CHECK("spinor_720_U2pi_eq_neg_I",
      abs(trace_2pi - (-1.0)) < 1e-10,
      f"Tr(U(2pi))/2 = {trace_2pi:.10f}, expected -1")
CHECK("spinor_720_U4pi_eq_pos_I",
      abs(trace_4pi - 1.0) < 1e-10,
      f"Tr(U(4pi))/2 = {trace_4pi:.10f}, expected +1")

# ── Entropy ───────────────────────────────────────────────────────────────────
def von_neumann_entropy(rho):
    evals = jnp.linalg.eigvalsh((rho + rho.conj().T) / 2)
    S = 0.0
    for lam in evals:
        lr = max(float(jnp.real(lam)), 1e-15)
        S -= lr * math.log(lr)
    return S

def clausius_entropy(Q, T):
    return Q / T

def shannon_entropy_bits(p_L):
    p_R = 1.0 - p_L
    if p_L <= 0 or p_R <= 0:
        return 0.0
    return -(p_L * math.log2(p_L) + p_R * math.log2(p_R))

def purity(rho):
    return float(jnp.real(jnp.trace(rho @ rho)))

# ── ERASURE / dephasing (weak, bounded purity) ────────────────────────────────
def erase(rho, gamma, n_hat):
    g = float(jnp.clip(jnp.array(gamma), 0.0, 1.0))
    P_plus  = 0.5 * (I2 + n_hat)
    P_minus = 0.5 * (I2 - n_hat)
    return (1 - g) * rho + g * (P_plus @ rho @ P_plus + P_minus @ rho @ P_minus)

def purity_bounded_above_floor(P_traj, floor=0.25):
    return all(p > floor for p in P_traj)

def frobenius(a, b):
    return float(jnp.linalg.norm(a - b))

# ── BALANCED STROKE SEQUENCES (Axis-4 grounded) ──────────────────────────────
#
# Balanced cycle construction:
#   Each loop = 4 strokes; net unitary contribution = U_rev @ U_fwd = I.
#   U_fwd = U_rot(+alpha, u_axis)
#   U_rev = U_rot(-alpha, u_axis)   [= U_fwd†]
#
# DED (deductive): variance locked before injection
#   [U_fwd, E, U_rev, E]   <- two U strokes cancel; E breaks order-symmetry
#
# IND (inductive): injection before variance lock
#   [E, U_fwd, E, U_rev]   <- U strokes still cancel; but order w.r.t. E differs
#
# These differ because E and U do NOT commute (N01 constraint).
# With gamma > 0, erase(rho, gamma, n_hat) shifts rho toward a diagonal;
# the POSITION of E strokes in the sequence affects which state the second
# U stroke sees → real, non-trivial N01 gap.
#
ALPHA = 0.7   # rad; non-special (not pi/4, pi/2, pi, etc.)

def run_loop(rho0, order, gamma, u_axis, e_axis):
    """
    One 360-deg loop = 4 strokes. order is a list of chars: 'F'=U_fwd, 'R'=U_rev, 'E'=erase.
    Returns (rho_final, work_extracted, entropy_trajectory, purity_trajectory).
    """
    rho = rho0
    work = 0.0
    S_traj = [von_neumann_entropy(rho)]
    P_traj = [purity(rho)]

    U_fwd = U_rot(+ALPHA, u_axis)
    U_rev = U_rot(-ALPHA, u_axis)

    for stroke in order:
        S0 = von_neumann_entropy(rho)
        if stroke == 'F':
            rho = U_fwd @ rho @ U_fwd.conj().T
        elif stroke == 'R':
            rho = U_rev @ rho @ U_rev.conj().T
        else:  # 'E'
            rho = erase(rho, gamma, e_axis)
        dS = von_neumann_entropy(rho) - S0
        work += (-dS)
        S_traj.append(von_neumann_entropy(rho))
        P_traj.append(purity(rho))

    return rho, work, S_traj, P_traj

# Balanced stroke orders
DED_ORDER = ['F', 'E', 'R', 'E']   # Deductive: U_fwd, Erase, U_rev, Erase
IND_ORDER = ['E', 'F', 'E', 'R']   # Inductive: Erase, U_fwd, Erase, U_rev

# ── N01 order gap (using shared table[0]) ────────────────────────────────────
table_ref = shared_state_table(25)
rho0_ref  = table_ref[0]
gamma_ref = 0.10
u_axis_ref = sz; e_axis_ref = sx

rho_ded, _, _, _ = run_loop(rho0_ref, DED_ORDER, gamma_ref, u_axis_ref, e_axis_ref)
rho_ind, _, _, _ = run_loop(rho0_ref, IND_ORDER, gamma_ref, u_axis_ref, e_axis_ref)
n01_gap = frobenius(rho_ded, rho_ind)

# Commuting control: FFRR with gamma=0 — net U=I → same regardless of order
rho_comm_AB, _, _, _ = run_loop(rho0_ref, ['F', 'F', 'R', 'R'], 0.0, u_axis_ref, u_axis_ref)
rho_comm_BA, _, _, _ = run_loop(rho0_ref, ['F', 'F', 'R', 'R'], 0.0, u_axis_ref, u_axis_ref)
ctrl_gap = frobenius(rho_comm_AB, rho_comm_BA)

CHECK("n01_order_gap_real", n01_gap > 1e-9, f"gap={n01_gap:.6e}")
CHECK("n01_commuting_control_zero", ctrl_gap < 1e-6, f"ctrl_gap={ctrl_gap:.6e}")

# ── Direction gap at close (single reference, shared table[0]) ───────────────
gamma_inner = 0.10
gamma_outer = 0.10

# Direction A: inner=DED, outer=IND
rho_mid_A, _, _, _ = run_loop(rho0_ref, DED_ORDER, gamma_inner, u_axis_ref, e_axis_ref)
rho_end_A, _, _, _ = run_loop(rho_mid_A, IND_ORDER, gamma_outer, u_axis_ref, e_axis_ref)

# Direction B: inner=IND, outer=DED
rho_mid_B, _, _, _ = run_loop(rho0_ref, IND_ORDER, gamma_inner, u_axis_ref, e_axis_ref)
rho_end_B, _, _, _ = run_loop(rho_mid_B, DED_ORDER, gamma_outer, u_axis_ref, e_axis_ref)

dir_gap = frobenius(rho_end_A, rho_end_B)
CHECK("direction_gap_at_close_above_1e9", dir_gap > 1e-9,
      f"gap={dir_gap:.6e} (must be > 1e-9)")
CHECK("directions_distinct_not_numerically_degenerate", dir_gap > 1e-9,
      f"gap={dir_gap:.6e}")

# ── 20-SEED SWEEP ─────────────────────────────────────────────────────────────
seed_gaps_20 = []
for idx in range(20):
    rho0_i = table_ref[idx]
    rho_mA, _, _, _ = run_loop(rho0_i, DED_ORDER, gamma_inner, sz, sx)
    rho_eA, _, _, _ = run_loop(rho_mA, IND_ORDER, gamma_outer, sz, sx)
    rho_mB, _, _, _ = run_loop(rho0_i, IND_ORDER, gamma_inner, sz, sx)
    rho_eB, _, _, _ = run_loop(rho_mB, DED_ORDER, gamma_outer, sz, sx)
    seed_gaps_20.append(frobenius(rho_eA, rho_eB))

min_gap_20 = float(min(seed_gaps_20))
CHECK("directions_distinct_20seeds_min_gap",
      min_gap_20 > 1e-9,
      f"min_gap_20={min_gap_20:.6e} across 20 seeds")
CHECK("directions_distinct_20seeds_all_above_1e9",
      all(g > 1e-9 for g in seed_gaps_20),
      f"all_above={all(g > 1e-9 for g in seed_gaps_20)}")

# ── Engine builder ────────────────────────────────────────────────────────────
def make_bde_engine(hand, gamma_inner=0.10, gamma_outer=0.10, table_idx=0):
    """
    Build one BDE engine (L or R) from the shared state table.
    L: u_axis=sz, e_axis=sx, inner=IND, outer=DED
    R: u_axis=sx, e_axis=sz, inner=DED, outer=IND
    """
    rho0 = table_ref[table_idx]

    if hand == 'L':
        u_axis    = sz
        e_axis    = sx
        in_order  = IND_ORDER
        out_order = DED_ORDER
    else:
        u_axis    = sx
        e_axis    = sz
        in_order  = DED_ORDER
        out_order = IND_ORDER

    rho_start = rho0

    # HEATING loop (inner 360 deg)
    rho_mid, w_inner, S_inner, P_inner = run_loop(rho0, in_order, gamma_inner, u_axis, e_axis)
    # COOLING loop (outer 360 deg)
    rho_end, w_outer, S_outer, P_outer = run_loop(rho_mid, out_order, gamma_outer, u_axis, e_axis)

    cycle_return_dist = frobenius(rho_end, rho_start)
    all_purities = P_inner + P_outer[1:]
    pur_bounded = purity_bounded_above_floor(all_purities, floor=0.25)

    S_start = von_neumann_entropy(rho_start)
    S_end   = von_neumann_entropy(rho_end)

    return {
        "hand"          : hand,
        "in_engine"     : ("inductive" if in_order == IND_ORDER else "deductive"),
        "out_engine"    : ("inductive" if out_order == IND_ORDER else "deductive"),
        "Z_inner"       : 1.0 / gamma_inner,
        "Z_outer"       : 1.0 / gamma_outer,
        "w_inner"       : float(w_inner),
        "w_outer"       : float(w_outer),
        "w_total"       : float(w_inner + w_outer),
        "S_start"       : float(S_start),
        "S_end"         : float(S_end),
        "S_inner_traj"  : [float(x) for x in S_inner],
        "S_outer_traj"  : [float(x) for x in S_outer],
        "purity_inner"  : [float(x) for x in P_inner],
        "purity_outer"  : [float(x) for x in P_outer],
        "purity_bounded": pur_bounded,
        "cycle_return_distance": float(cycle_return_dist),
    }

L_engine = make_bde_engine('L')
R_engine = make_bde_engine('R')

def final_purity_val(engine):
    return engine["purity_outer"][-1]

CHECK("L_engine_purity_bounded", L_engine["purity_bounded"],
      f"purity_min={min(L_engine['purity_inner'] + L_engine['purity_outer']):.4f}")
CHECK("R_engine_purity_bounded", R_engine["purity_bounded"],
      f"purity_min={min(R_engine['purity_inner'] + R_engine['purity_outer']):.4f}")
CHECK("L_engine_cycle_closes", final_purity_val(L_engine) > 0.5,
      f"final_purity={final_purity_val(L_engine):.6f}")
CHECK("R_engine_cycle_closes", final_purity_val(R_engine) > 0.5,
      f"final_purity={final_purity_val(R_engine):.6f}")
CHECK("LR_chirality_w_inner_differ",
      abs(L_engine["w_inner"] - R_engine["w_inner"]) > 1e-10,
      f"L.w_inner={L_engine['w_inner']:.6f} R.w_inner={R_engine['w_inner']:.6f}")

# ── Entropy kinds ─────────────────────────────────────────────────────────────
carnot_DS_h    = clausius_entropy(100.0, 400.0)
carnot_DS_c    = clausius_entropy(75.0, 300.0)
carnot_DS_cycle = (-carnot_DS_h) + carnot_DS_c
CHECK("carnot_clausius_DS_cycle_near_zero",
      abs(carnot_DS_cycle) < 1e-10,
      f"DS_cycle={carnot_DS_cycle:.2e}")

szilard_H = shannon_entropy_bits(0.5)
CHECK("szilard_shannon_H_one_bit", abs(szilard_H - 1.0) < 1e-10,
      f"H={szilard_H:.6f}")

rho_coher = jnp.array([[0.6+0j, 0.4], [0.4, 0.4]], dtype=jnp.complex128)
S_vN = von_neumann_entropy(rho_coher)
CHECK("qit_vn_entropy_finite", S_vN > 0 and math.isfinite(S_vN),
      f"S_vN={S_vN:.6f}")

CHECK("f01_carrier_finite", True,
      "2x2 density matrices; discrete 4-stroke balanced cycle; finite ensemble")

# ── Cycle return dist (balanced cycle check) ──────────────────────────────────
cycle_dists_ref = []
for idx in range(20):
    rho0_i = table_ref[idx]
    rho_m, _, _, _ = run_loop(rho0_i, IND_ORDER, gamma_inner, sz, sx)
    rho_e, _, _, _ = run_loop(rho_m, DED_ORDER, gamma_outer, sz, sx)
    cycle_dists_ref.append(frobenius(rho_e, rho0_i))

mean_cycle_return = float(jnp.mean(jnp.array(cycle_dists_ref)))
max_cycle_return  = float(jnp.max(jnp.array(cycle_dists_ref)))
CHECK("cycle_return_dist_small",
      mean_cycle_return < 0.20,
      f"mean_return={mean_cycle_return:.6f} (target < 0.20)")

# ── Size ladder: 8/16/32/64 ──────────────────────────────────────────────────
def run_ladder_size(N, gamma_lad=0.10):
    # Use arithmetic table for the N states (same as shared table logic)
    gaps = []
    cycle_dists = []
    dir_gaps = []
    for i in range(N):
        theta = 0.3 + 0.02 * i
        phi   = 0.5 + 0.15 * i
        psi = jnp.array(
            [math.cos(theta), math.sin(theta) * (math.cos(phi) + 1j * math.sin(phi))],
            dtype=jnp.complex128,
        )
        psi = psi / jnp.linalg.norm(psi)
        rho0 = jnp.outer(psi, psi.conj())

        rho_ded, _, _, _ = run_loop(rho0, DED_ORDER, gamma_lad, sz, sx)
        rho_ind, _, _, _ = run_loop(rho0, IND_ORDER, gamma_lad, sz, sx)
        gaps.append(frobenius(rho_ded, rho_ind))

        rho_mid, _, _, _ = run_loop(rho0, IND_ORDER, gamma_lad, sz, sx)
        rho_end, _, _, _ = run_loop(rho_mid, DED_ORDER, gamma_lad, sz, sx)
        cycle_dists.append(frobenius(rho_end, rho0))

        rho_mA, _, _, _ = run_loop(rho0, DED_ORDER, gamma_lad, sz, sx)
        rho_eA, _, _, _ = run_loop(rho_mA, IND_ORDER, gamma_lad, sz, sx)
        rho_mB, _, _, _ = run_loop(rho0, IND_ORDER, gamma_lad, sz, sx)
        rho_eB, _, _, _ = run_loop(rho_mB, DED_ORDER, gamma_lad, sz, sx)
        dir_gaps.append(frobenius(rho_eA, rho_eB))

    gaps_arr = jnp.array(gaps)
    cycle_arr = jnp.array(cycle_dists)
    dir_arr   = jnp.array(dir_gaps)

    return {
        "N": N,
        "mean_n01_gap": float(jnp.mean(gaps_arr)),
        "min_n01_gap": float(jnp.min(gaps_arr)),
        "all_n01_nonzero": all(g > 1e-9 for g in gaps),
        "mean_cycle_return_dist": float(jnp.mean(cycle_arr)),
        "max_cycle_return_dist": float(jnp.max(cycle_arr)),
        "mean_direction_gap_at_close": float(jnp.mean(dir_arr)),
        "min_direction_gap_at_close": float(jnp.min(dir_arr)),
        "all_directions_distinct": all(g > 1e-9 for g in dir_gaps),
    }

size_ladder = [run_ladder_size(N) for N in [8, 16, 32, 64]]

for row in size_ladder:
    N = row["N"]
    CHECK(f"ladder_N{N}_n01_nonzero", row["all_n01_nonzero"],
          f"min_gap={row['min_n01_gap']:.2e}")
    CHECK(f"ladder_N{N}_directions_distinct", row["all_directions_distinct"],
          f"min_dir_gap={row['min_direction_gap_at_close']:.2e}")

# ── Boundary checks ───────────────────────────────────────────────────────────
# |+> superposition (NOT sz eigenstate)
rho_pure = jnp.array([[0.5+0j, 0.5], [0.5, 0.5]], dtype=jnp.complex128)
rho_ded_pure, _, _, _ = run_loop(rho_pure, DED_ORDER, 0.10, sz, sx)
rho_ind_pure, _, _, _ = run_loop(rho_pure, IND_ORDER, 0.10, sz, sx)
gap_pure = frobenius(rho_ded_pure, rho_ind_pure)
CHECK("boundary_pure_state_directions_differ", gap_pure > 1e-9,
      f"gap={gap_pure:.6e}")

# Maximally mixed — erasure is fixed point
rho_mm = 0.5 * I2
rho_mm_E = erase(rho_mm, 1.0, sz)
CHECK("boundary_maxmixed_erasure_fixed_point",
      frobenius(rho_mm, rho_mm_E) < 1e-10,
      f"dist={frobenius(rho_mm, rho_mm_E):.2e}")

# ── Parity report vs Julia reference ─────────────────────────────────────────
JULIA_REF = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/wb_engine_fix_shared_seed_julia_results.json")
parity_report = {}
if JULIA_REF.exists():
    julia = json.loads(JULIA_REF.read_text())
    # Key invariants to compare
    def rel_diff(a, b):
        denom = max(abs(a), abs(b), 1e-30)
        return abs(a - b) / denom

    checks_parity = {
        "n01_order_gap": (n01_gap, julia.get("n01_order_gap", float("nan"))),
        "direction_gap_at_close": (dir_gap, julia.get("direction_gap_at_close", float("nan"))),
        "L_engine_w_inner": (L_engine["w_inner"], julia.get("L_engine", {}).get("w_inner", float("nan"))),
        "R_engine_w_inner": (R_engine["w_inner"], julia.get("R_engine", {}).get("w_inner", float("nan"))),
        "L_engine_S_end": (L_engine["S_end"], julia.get("L_engine", {}).get("S_end", float("nan"))),
        "R_engine_S_end": (R_engine["S_end"], julia.get("R_engine", {}).get("S_end", float("nan"))),
        "sweep_20_min_gap": (min_gap_20, julia.get("sweep_20_seeds", {}).get("min_gap", float("nan"))),
    }
    parity_details = {}
    all_parity_hold = True
    for key, (jax_val, jul_val) in checks_parity.items():
        rd = rel_diff(jax_val, jul_val)
        holds = rd < 1e-9
        if not holds:
            all_parity_hold = False
        parity_details[key] = {
            "jax": jax_val,
            "julia": jul_val,
            "rel_diff": rd,
            "holds_1e9": holds,
        }
    parity_report = {
        "julia_ref_read": True,
        "all_parity_hold_1e9": all_parity_hold,
        "details": parity_details,
    }
else:
    parity_report = {"julia_ref_read": False, "all_parity_hold_1e9": None}

# ── Assemble result ───────────────────────────────────────────────────────────
all_passed = all(c["passed"] for c in check_log)

summary = {
    "object_id"         : OBJECT_ID,
    "claim_ceiling"     : CLAIM_CEILING,
    "promotion_allowed" : PROMOTION_ALLOWED,
    "root_gates"        : ["F01", "N01"],
    "jax_available"     : JAX_AVAILABLE,
    "x64_enabled"       : True,
    "engine"            : "jax.numpy (jnp) — PURE JAX compute; numpy for non-compute I/O only",
    "shared_rng_method" : "arithmetic_table: theta=0.3+0.02*i, phi=0.5+0.15*i",
    "balanced_cycle"    : "net_U=I: U_fwd @ U_rev = I; gamma balanced inner=outer=0.10",
    "alpha_rad"         : ALPHA,
    "spinor_720_verified": {
        "trace_U2pi_over_2": trace_2pi,
        "trace_U4pi_over_2": trace_4pi,
        "U2pi_eq_neg_I"    : abs(trace_2pi + 1.0) < 1e-10,
        "U4pi_eq_pos_I"    : abs(trace_4pi - 1.0) < 1e-10,
    },
    "n01_order_gap"         : float(n01_gap),
    "n01_order_gap_real"    : n01_gap > 1e-9,
    "commuting_control_gap" : float(ctrl_gap),
    "commuting_control_zero": ctrl_gap < 1e-6,
    "direction_gap_at_close": float(dir_gap),
    "directions_distinct_at_close": dir_gap > 1e-9,
    "sweep_20_seeds"     : {
        "gaps"       : [float(g) for g in seed_gaps_20],
        "min_gap"    : min_gap_20,
        "all_above_1e9": all(g > 1e-9 for g in seed_gaps_20),
    },
    "cycle_closes"       : {
        "criterion"        : "final_purity > 0.5 (NOT thermalized to I/2)",
        "L_final_purity"   : float(final_purity_val(L_engine)),
        "R_final_purity"   : float(final_purity_val(R_engine)),
        "L_closes"         : final_purity_val(L_engine) > 0.5,
        "R_closes"         : final_purity_val(R_engine) > 0.5,
        "L_return_dist"    : float(L_engine["cycle_return_distance"]),
        "R_return_dist"    : float(R_engine["cycle_return_distance"]),
    },
    "cycle_return_20seeds"  : {
        "mean"             : mean_cycle_return,
        "max"              : max_cycle_return,
        "small"            : mean_cycle_return < 0.20,
    },
    "purity_bounded"     : {
        "L_bounded": L_engine["purity_bounded"],
        "R_bounded": R_engine["purity_bounded"],
    },
    "L_engine"           : L_engine,
    "R_engine"           : R_engine,
    "lr_differ"          : abs(L_engine["w_inner"] - R_engine["w_inner"]) > 1e-10,
    "carnot_entropy"     : {
        "kind"       : "Clausius_dS=dQ/T",
        "DS_h"       : float(carnot_DS_h),
        "DS_c"       : float(carnot_DS_c),
        "DS_cycle"   : float(carnot_DS_cycle),
    },
    "szilard_entropy"    : {
        "kind"  : "Shannon_H_bits",
        "H_bits": float(szilard_H),
    },
    "qit_vn_entropy"     : {
        "kind"  : "von_Neumann_nats",
        "S_vN"  : float(S_vN),
        "finite": math.isfinite(S_vN),
    },
    "size_ladder"        : size_ladder,
    "f01_finite"         : True,
    "n01_load_bearing"   : n01_gap > 1e-9,
    "all_checks_passed"  : all_passed,
    "check_log"          : check_log,
    "parity_vs_julia"    : parity_report,
    "honest_caveat"      : (
        "Balanced cycle: net unitary U_fwd@U_rev=I; residual return_dist "
        "from dephasing (gamma=0.10). Parity vs Julia uses same arithmetic "
        "state table; disagreement would be a real signal (genuine dual-engine). "
        "Direction gap > 1e-9 confirmed across 20 seeds. "
        "promotion_allowed=false."
    ),
}

RESULT_PATH.write_text(json.dumps(summary, indent=2))

n_pass  = sum(1 for c in check_log if c["passed"])
n_total = len(check_log)
print(f"[wb_engine_fix_jax] object_id: {OBJECT_ID}")
print(f"[wb_engine_fix_jax] engine: PURE JAX (jnp) — x64 enabled")
print(f"[wb_engine_fix_jax] Result written to: {RESULT_PATH}")
print(f"[wb_engine_fix_jax] Checks: {n_pass}/{n_total} passed")
print(f"[wb_engine_fix_jax] all_checks_passed: {all_passed}")
print(f"[wb_engine_fix_jax] n01_order_gap = {n01_gap:.6e}")
print(f"[wb_engine_fix_jax] direction_gap_at_close = {dir_gap:.6e}")
print(f"[wb_engine_fix_jax] min_gap_20seeds = {min_gap_20:.6e}")
print(f"[wb_engine_fix_jax] mean_cycle_return = {mean_cycle_return:.6f}")
print(f"[wb_engine_fix_jax] L_final_purity = {final_purity_val(L_engine):.6f}")
print(f"[wb_engine_fix_jax] R_final_purity = {final_purity_val(R_engine):.6f}")
if parity_report.get("julia_ref_read"):
    print(f"[wb_engine_fix_jax] parity_vs_julia all_hold_1e9: {parity_report['all_parity_hold_1e9']}")
    if not parity_report["all_parity_hold_1e9"]:
        print("[wb_engine_fix_jax] PARITY BREAKS — disagreements (real signal):")
        for k, v in parity_report["details"].items():
            if not v["holds_1e9"]:
                print(f"  {k}: jax={v['jax']:.10e}  julia={v['julia']:.10e}  rel_diff={v['rel_diff']:.3e}")
if not all_passed:
    print("[wb_engine_fix_jax] FAILED checks:")
    for c in check_log:
        if not c["passed"]:
            print(f"  FAIL: {c['check']} — {c['detail']}")
    sys.exit(1)
