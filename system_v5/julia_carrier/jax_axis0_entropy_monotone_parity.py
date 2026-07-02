#!/usr/bin/env python3
"""
JAX parity audit for Axis-0 entropy monotones.

object_id: axis0_entropy_monotone_jax_parity
claim_ceiling: candidate — parity probe only. NOT layer-complete. NOT bridge claim.
  promotion_allowed: false

Finite map (mirrors axis0_entropy_monotone.jl exactly):
  domain:  L/R Weyl spinor states, 2 shells x 6x6x4 = 288 sites
  codomain: (S_L_inner, S_L_outer, S_R_inner, S_R_outer,
             MI_LR_inner, MI_LR_outer, MI_shells,
             CI_LR_inner, CI_LR_outer,
             corr_mono_inner, corr_mono_outer, corr_mono_full,
             n01_diff_MI, n01_diff_cm, n01_comm_norm)

JAX role (per JAX_AUDIT_LANE_CONTRACT.md): scale/stress/AUDIT lane.
Julia is the truth lane. This file reads Julia's result JSON and computes the
same monotones in JAX x64, then writes /tmp/ax0_parity.json.

F01: 288 sites — finite, terminates.
N01: Ti (z-dephase) vs Fi (x-rotation) — genuinely non-commuting.
"""

from jax import config
config.update("jax_enable_x64", True)

import json
import math
import sys
from pathlib import Path

import jax
import jax.numpy as jnp
import numpy as np

# ── Constants ──────────────────────────────────────────────────────────────────
SHELLS_RADII = [0.6, 1.0]
NPhi = 6
NChi = 6
NEta = 4

I2 = jnp.eye(2, dtype=jnp.complex128)
sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
sy = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
sz = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
P0 = jnp.array([[1, 0], [0, 0]], dtype=jnp.complex128)
P1 = jnp.array([[0, 0], [0, 1]], dtype=jnp.complex128)

# ── Weyl spinor ───────────────────────────────────────────────────────────────
def weyl_spinor(phi: float, chi: float, eta: float, s: int) -> jnp.ndarray:
    psi = jnp.array([
        jnp.exp(1j * (phi + s * chi)) * math.cos(eta),
        jnp.exp(1j * (phi - s * chi)) * math.sin(eta),
    ], dtype=jnp.complex128)
    n = jnp.linalg.norm(psi)
    if float(n) < 1e-15:
        return jnp.array([1.0 + 0j, 0.0 + 0j], dtype=jnp.complex128)
    return psi / n


def build_sites():
    sites = []
    for r in SHELLS_RADII:
        for i in range(NPhi):
            phi = 2 * math.pi * i / NPhi
            for j in range(NChi):
                chi = 2 * math.pi * j / NChi
                for k in range(NEta):
                    eta = (math.pi / 2) * (k + 0.5) / NEta
                    sites.append((r, phi, chi, eta))
    return sites


def build_density_matrices(sites):
    rhoL = []
    rhoR = []
    for (r, phi, chi, eta) in sites:
        psiL = weyl_spinor(phi, chi, eta * r, +1)
        psiR = weyl_spinor(phi, chi, eta * r, -1)
        rhoL.append(jnp.outer(psiL, jnp.conj(psiL)))
        rhoR.append(jnp.outer(psiR, jnp.conj(psiR)))
    return rhoL, rhoR


# ── Von Neumann entropy ───────────────────────────────────────────────────────
def vn_entropy(rho: jnp.ndarray) -> float:
    evals = jnp.linalg.eigvalsh(rho).real
    evals = jnp.clip(evals, 1e-15, None)
    return float(-jnp.sum(evals * jnp.log(evals)))


# ── Partial traces of 4x4 density matrix ─────────────────────────────────────
def partial_trace_A(rhoAB: jnp.ndarray) -> jnp.ndarray:
    """Trace out A (first 2 dims): rho_B[i,j] = sum_{k} rhoAB[2k+i, 2k+j]  (0-indexed)"""
    rho_B = jnp.zeros((2, 2), dtype=jnp.complex128)
    for k in range(2):
        block = rhoAB[2*k:2*k+2, 2*k:2*k+2]
        rho_B = rho_B + block
    return rho_B


def partial_trace_B(rhoAB: jnp.ndarray) -> jnp.ndarray:
    """Trace out B (second 2 dims): rho_A[a,b] = sum_i rhoAB[2a+i, 2b+i]  (0-indexed)"""
    rho_A = jnp.zeros((2, 2), dtype=jnp.complex128)
    for i in range(2):
        for a in range(2):
            for b in range(2):
                rho_A = rho_A.at[a, b].add(rhoAB[2*a+i, 2*b+i])
    return rho_A


# ── Ensemble joint ────────────────────────────────────────────────────────────
def ensemble_joint(rhoL_batch, rhoR_batch) -> jnp.ndarray:
    N = len(rhoL_batch)
    joint = jnp.zeros((4, 4), dtype=jnp.complex128)
    for rl, rr in zip(rhoL_batch, rhoR_batch):
        joint = joint + jnp.kron(rl, rr)
    return joint / N


# ── Mutual information ────────────────────────────────────────────────────────
def mutual_information(rhoA, rhoB, rhoAB) -> float:
    return vn_entropy(rhoA) + vn_entropy(rhoB) - vn_entropy(rhoAB)


# ── Coherent information CI(A>B) = S(B) - S(AB) ──────────────────────────────
def coherent_information(rhoAB) -> float:
    rho_B = partial_trace_A(rhoAB)
    return vn_entropy(rho_B) - vn_entropy(rhoAB)


# ── Correlation monotone: trace norm of (rhoAB - rhoA⊗rhoB) ─────────────────
def correlation_monotone(rhoAB, rhoA, rhoB) -> float:
    diff = rhoAB - jnp.kron(rhoA, rhoB)
    evals = jnp.linalg.eigvalsh(diff).real
    return float(jnp.sum(jnp.abs(evals)))


# ── Operator channels (match Julia exactly) ───────────────────────────────────
def Ti_channel(rho, q: float = 0.5):
    return (1 - q) * rho + q * (P0 @ rho @ P0 + P1 @ rho @ P1)


def Ux(t: float):
    return math.cos(t / 2) * I2 - 1j * math.sin(t / 2) * sx


def Uz(p: float):
    return math.cos(p / 2) * I2 - 1j * math.sin(p / 2) * sz


def Fi_channel(rho, t: float = 0.7):
    U = Ux(t)
    return U @ rho @ jnp.conj(U).T


def Fe_channel(rho, p: float = 0.7):
    U = Uz(p)
    return U @ rho @ jnp.conj(U).T


# ── MAIN ──────────────────────────────────────────────────────────────────────
print("=" * 60)
print("AXIS 0 — JAX parity audit lane")
print("object_id: axis0_entropy_monotone_jax_parity")
print("claim_ceiling: candidate | promotion_allowed: false")
print("=" * 60)

sites = build_sites()
N = len(sites)
n_per_shell = NPhi * NChi * NEta  # 144
print(f"\nF01 check: N={N} sites, {len(SHELLS_RADII)} shells x {NPhi}x{NChi}x{NEta} grid")
assert N < 1_000_000_000, "F01 violated"

rhoL, rhoR = build_density_matrices(sites)
assert all(r.shape == (2, 2) for r in rhoL), "F01: shape"
assert all(jnp.all(jnp.isfinite(r)) for r in rhoL), "F01: finite"

# Per-site entropy (pure -> 0)
entropies_L = [vn_entropy(r) for r in rhoL]
entropies_R = [vn_entropy(r) for r in rhoR]
mean_eL = sum(entropies_L) / N
mean_eR = sum(entropies_R) / N
print(f"\n--- Per-site entropy (pure spinors -> ~0 expected) ---")
print(f"  Entropy L per-site mean: {mean_eL:.4g}")
print(f"  Entropy R per-site mean: {mean_eR:.4g}")

# Split by shell
shell_inner_L = rhoL[:n_per_shell]
shell_outer_L = rhoL[n_per_shell:]
shell_inner_R = rhoR[:n_per_shell]
shell_outer_R = rhoR[n_per_shell:]

# Ensemble joint states
joint_inner = ensemble_joint(shell_inner_L, shell_inner_R)
joint_outer = ensemble_joint(shell_outer_L, shell_outer_R)
joint_full  = ensemble_joint(rhoL, rhoR)

# Marginals
avg_L_inner = partial_trace_B(joint_inner)
avg_R_inner = partial_trace_A(joint_inner)
avg_L_outer = partial_trace_B(joint_outer)
avg_R_outer = partial_trace_A(joint_outer)

S_L_inner = vn_entropy(avg_L_inner)
S_L_outer = vn_entropy(avg_L_outer)
S_R_inner = vn_entropy(avg_R_inner)
S_R_outer = vn_entropy(avg_R_outer)

print("\n--- Von Neumann entropy per sector/shell ---")
print(f"  S(L, inner shell r=0.6): {S_L_inner:.8f}")
print(f"  S(L, outer shell r=1.0): {S_L_outer:.8f}")
print(f"  S(R, inner shell r=0.6): {S_R_inner:.8f}")
print(f"  S(R, outer shell r=1.0): {S_R_outer:.8f}")

# Mutual information
MI_LR_inner = mutual_information(avg_L_inner, avg_R_inner, joint_inner)
MI_LR_outer = mutual_information(avg_L_outer, avg_R_outer, joint_outer)

# Shell-to-shell MI
joint_shells_L = ensemble_joint(shell_inner_L, shell_outer_L)
avg_Li = partial_trace_B(joint_shells_L)
avg_Lo = partial_trace_A(joint_shells_L)
MI_shells = mutual_information(avg_Li, avg_Lo, joint_shells_L)

CI_LR_inner = coherent_information(joint_inner)
CI_LR_outer = coherent_information(joint_outer)

print("\n--- Mutual information ---")
print(f"  MI(L:R, inner shell): {MI_LR_inner:.8f}")
print(f"  MI(L:R, outer shell): {MI_LR_outer:.8f}")
print(f"  MI(L_inner:L_outer):  {MI_shells:.8f}")

print("\n--- Coherent information ---")
print(f"  CI(L>R, inner shell): {CI_LR_inner:.8f}")
print(f"  CI(L>R, outer shell): {CI_LR_outer:.8f}")

# Correlation monotone
cm_inner = correlation_monotone(joint_inner, avg_L_inner, avg_R_inner)
cm_outer = correlation_monotone(joint_outer, avg_L_outer, avg_R_outer)
marg_full_L = partial_trace_B(joint_full)
marg_full_R = partial_trace_A(joint_full)
cm_full = correlation_monotone(joint_full, marg_full_L, marg_full_R)

# Dephasing ladder
dephase_strengths = [i / 7.0 for i in range(8)]  # 0..1 in 8 steps (matches Julia range(0,1,length=8))
corr_monos_by_strength = []
for q in dephase_strengths:
    rhoL_d = [Ti_channel(r, q) for r in rhoL]
    joint_d = ensemble_joint(rhoL_d, rhoR)
    marg_L_d = partial_trace_B(joint_d)
    marg_R_d = partial_trace_A(joint_d)
    corr_monos_by_strength.append(correlation_monotone(joint_d, marg_L_d, marg_R_d))

threshold = sum(corr_monos_by_strength) / len(corr_monos_by_strength)
homeostasis = [cm for cm in corr_monos_by_strength if cm <= threshold]
allostasis  = [cm for cm in corr_monos_by_strength if cm > threshold]

print("\n--- Correlation monotone vs dephasing strength ---")
for q, cm in zip(dephase_strengths, corr_monos_by_strength):
    print(f"  q={q:.3f}  corr_mono={cm:.8f}")

print(f"\n--- AXIS-0 SPLIT (threshold={threshold:.6f}) ---")
print(f"  homeostasis: {len(homeostasis)} states")
print(f"  allostasis:  {len(allostasis)} states")
print(f"  split non-trivial: {len(homeostasis) > 0 and len(allostasis) > 0}")

# N01 checks
r0 = rhoL[0]
r_Ti_Fi = Fi_channel(Ti_channel(r0))
r_Fi_Ti = Ti_channel(Fi_channel(r0))
comm_diff = Ti_channel(Fi_channel(r0)) - Fi_channel(Ti_channel(r0))
comm_norm = float(jnp.linalg.norm(comm_diff))

S_TiFi_site = vn_entropy(r_Ti_Fi)
S_FiTi_site = vn_entropy(r_Fi_Ti)
n01_diff_entropy_site = abs(S_TiFi_site - S_FiTi_site)

rhoL_TiFi = [Fi_channel(Ti_channel(r)) for r in rhoL]
rhoL_FiTi = [Ti_channel(Fi_channel(r)) for r in rhoL]

joint_TiFi = ensemble_joint(rhoL_TiFi, rhoR)
joint_FiTi = ensemble_joint(rhoL_FiTi, rhoR)

marg_L_TiFi = partial_trace_B(joint_TiFi)
marg_R_TiFi = partial_trace_A(joint_TiFi)
marg_L_FiTi = partial_trace_B(joint_FiTi)
marg_R_FiTi = partial_trace_A(joint_FiTi)

MI_TiFi = mutual_information(marg_L_TiFi, marg_R_TiFi, joint_TiFi)
MI_FiTi = mutual_information(marg_L_FiTi, marg_R_FiTi, joint_FiTi)

cm_TiFi = correlation_monotone(joint_TiFi, marg_L_TiFi, marg_R_TiFi)
cm_FiTi = correlation_monotone(joint_FiTi, marg_L_FiTi, marg_R_FiTi)

n01_diff_MI = abs(MI_TiFi - MI_FiTi)
n01_diff_cm = abs(cm_TiFi - cm_FiTi)

n01_sensitive = comm_norm > 1e-10 or n01_diff_MI > 1e-10 or n01_diff_cm > 1e-10

print(f"\n--- N01 order-sensitivity ---")
print(f"  [Ti,Fi] commutator Frobenius norm: {comm_norm:.6g}")
print(f"  |MI diff|: {n01_diff_MI:.6g}")
print(f"  |corr_mono diff|: {n01_diff_cm:.6g}")
print(f"  N01 sensitive: {n01_sensitive}")

f01_ok = (N < 1_000_000_000 and
          all(math.isfinite(cm) for cm in corr_monos_by_strength) and
          math.isfinite(S_L_inner) and
          math.isfinite(MI_LR_inner))

print(f"\n--- GATE SUMMARY ---")
print(f"  F01 (finite, terminates): {f01_ok}")
print(f"  N01 (order-sensitive): {n01_sensitive}")
print(f"  Axis-0 split real: {len(homeostasis) > 0 and len(allostasis) > 0}")

# ── Build JAX result dict ──────────────────────────────────────────────────────
jax_results = {
    "object_id": "axis0_entropy_monotone_jax_parity",
    "engine": "jax_x64",
    "N_sites": N,
    "S_L_inner": S_L_inner,
    "S_L_outer": S_L_outer,
    "S_R_inner": S_R_inner,
    "S_R_outer": S_R_outer,
    "MI_LR_inner": MI_LR_inner,
    "MI_LR_outer": MI_LR_outer,
    "MI_shells": MI_shells,
    "CI_LR_inner": CI_LR_inner,
    "CI_LR_outer": CI_LR_outer,
    "corr_mono_inner": cm_inner,
    "corr_mono_outer": cm_outer,
    "corr_mono_full": cm_full,
    "corr_mono_ladder": corr_monos_by_strength,
    "threshold": threshold,
    "n_homeostasis": len(homeostasis),
    "n_allostasis": len(allostasis),
    "n01_diff_MI": n01_diff_MI,
    "n01_diff_cm": n01_diff_cm,
    "n01_comm_norm": comm_norm,
    "f01_finite": f01_ok,
    "n01_sensitive": n01_sensitive,
    "axis0_split_real": len(homeostasis) > 0 and len(allostasis) > 0,
    "promotion_allowed": False,
    "claim_ceiling": "candidate",
}

jax_result_path = Path("/tmp/ax0_jax_results.json")
with open(jax_result_path, "w") as f:
    json.dump(jax_results, f, indent=2)
print(f"\nJAX results written to {jax_result_path}")

# ── Load Julia results and compute parity ─────────────────────────────────────
julia_result_path = Path("/tmp/ax0_julia_results.json")

if not julia_result_path.exists():
    print(f"\nWARNING: Julia result not found at {julia_result_path}")
    print("Cannot compute parity. Run axis0_entropy_monotone.jl first.")
    sys.exit(1)

with open(julia_result_path) as f:
    julia_results = json.load(f)

# Named monotones to compare
NAMED_MONOTONES = [
    "S_L_inner",
    "S_L_outer",
    "S_R_inner",
    "S_R_outer",
    "MI_LR_inner",
    "MI_LR_outer",
    "MI_shells",
    "CI_LR_inner",
    "CI_LR_outer",
    "corr_mono_inner",
    "corr_mono_outer",
    "corr_mono_full",
    "n01_diff_MI",
    "n01_diff_cm",
    "n01_comm_norm",
]

print("\n" + "=" * 60)
print("PARITY: JAX vs Julia (named Axis-0 monotones)")
print("=" * 60)
print(f"{'Monotone':<25}  {'Julia':>18}  {'JAX':>18}  {'|diff|':>14}")
print("-" * 80)

diffs = {}
max_diff = 0.0
max_diff_name = ""
for name in NAMED_MONOTONES:
    j_val = julia_results.get(name)
    x_val = jax_results.get(name)
    if j_val is None or x_val is None:
        print(f"  {name:<25}  MISSING in one engine")
        continue
    diff = abs(float(j_val) - float(x_val))
    diffs[name] = diff
    if diff > max_diff:
        max_diff = diff
        max_diff_name = name
    marker = " <-- MAX" if name == max_diff_name else ""
    print(f"  {name:<25}  {float(j_val):>18.12f}  {float(x_val):>18.12f}  {diff:>14.3e}{marker}")

agree = max_diff <= 1e-10
print(f"\nmax_diff = {max_diff:.6e}  (on '{max_diff_name}')")
print(f"agree (<=1e-10): {agree}")

parity = {
    "object_id": "ax0_parity",
    "julia_result_path": str(julia_result_path),
    "jax_result_path": str(jax_result_path),
    "named_monotones_compared": NAMED_MONOTONES,
    "diffs": diffs,
    "max_diff": max_diff,
    "max_diff_monotone": max_diff_name,
    "agree_le_1e10": agree,
    "julia_engine": julia_results.get("engine"),
    "jax_engine": jax_results.get("engine"),
    "promotion_allowed": False,
    "claim_ceiling": "candidate",
    "note": (
        "JAX dephasing ladder uses q in range(0,1,8) = [0,1/7,...,1]. "
        "Julia uses range(0,1,length=8) which is linspace(0,1,8) = [0,1/7,...,1]. "
        "These match. Ladder values not compared elementally in max_diff (scalar monotones only)."
    ),
}

parity_path = Path("/tmp/ax0_parity.json")
with open(parity_path, "w") as f:
    json.dump(parity, f, indent=2)
print(f"\nParity written to {parity_path}")
