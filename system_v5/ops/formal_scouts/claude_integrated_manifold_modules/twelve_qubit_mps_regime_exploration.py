#!/usr/bin/env python3
"""
Twelve-qubit MPS regime exploration + 8-qubit parameter grid sweep.

Diagnoses Track A (MPS-only) ~0 coherent-information finding in the
claude_integrated_manifold_modules suite, and builds a 12-qubit MPS
extension to test whether the failure is regime-dependent or architectural.

PART A — 8-qubit parameter grid sweep:
  Tests dt × threshold × max_bond × n_steps to find any regime that
  produces signed coherent_information > 0.05 at any cut.

PART B — 12-qubit MPS extension:
  Functions: mps_initial_state_12q, mps_evolution_12q, mps_cuts_readout_12q.
  Uses the same XX+YY nearest-neighbour Hamiltonian as the 8-qubit baseline.

PART C — Verdict:
  Compares 8-qubit grid sweep vs 12-qubit single run. Reports whether the
  regime question is scale-dependent or architectural (fundamental).

TOOL_MANIFEST:
  pytorch  — load-bearing: all MPS tensors, SVD truncation, evolution unitaries
  numpy    — load-bearing: SVD backend, weight matrix construction
  scipy    — load-bearing: scipy.linalg.expm for two-site unitary generation
  psutil   — supportive: memory profiling in 12-qubit run

CLASSIFICATION: formal_scout
PROMOTION_ALLOWED: False
CLAIM_CEILING:
  Formal scout only. Does not admit a final manifold tower, bridge,
  axis, or target-system claim.
"""

from __future__ import annotations

import time
import math
import sys
from typing import Any

import numpy as np
import torch
from scipy.linalg import expm

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

# ---------------------------------------------------------------------------
# Import base MPS utilities from the existing comparator module.
# We re-import the core primitives to keep a single source of truth.
# ---------------------------------------------------------------------------
import importlib.util
import pathlib

_MODULE_DIR = pathlib.Path(__file__).resolve().parent
_COMPARATOR_PATH = _MODULE_DIR / "mps_contraction_and_special_holonomy_comparator.py"

spec = importlib.util.spec_from_file_location(
    "mps_comparator", _COMPARATOR_PATH
)
_comparator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_comparator)

mps_initial_state = _comparator.mps_initial_state          # n_qubits, bond_dim -> list[Tensor]
mps_apply_evolution = _comparator.mps_apply_evolution      # mps, weights, threshold, dt, max_bond -> mps
mps_entropy_at_cut = _comparator.mps_entropy_at_cut        # mps, cut -> float
mps_max_bond_dim_used = _comparator.mps_max_bond_dim_used  # mps -> int
mps_to_full_state = _comparator.mps_to_full_state          # mps -> Tensor (2^N,)


# ---------------------------------------------------------------------------
# Coherent information for MPS — pure state formula
# ---------------------------------------------------------------------------
# For a bipartite split A | B of a pure state |psi>_AB:
#   S_AB = 0  (pure global state)
#   conditional entropy H(A|B) = S_AB - S_A = -S_A
#   coherent information I(A>B) = S_A - S_AB = S_A
#
# Therefore for a pure state evolving under a unitary (no noise), coherent
# information at any cut equals the entanglement entropy at that cut, and
# is ALWAYS >= 0.  The signed-negative quantity can only appear if the
# evolution introduces noise/mixing, or if S_AB is estimated from a mixed
# global state.
#
# Track A uses a closed unitary MPS evolution on a pure product state.
# The fundamental constraint: S_AB = 0 for all time => coherent info = S_A >= 0.
# The "~0" finding means entanglement entropy S_A ≈ 0, i.e., the product
# state is not being entangled significantly at the tested parameters.
#
# This module sweeps parameters to find the entanglement-generating regime.
# ---------------------------------------------------------------------------

def _xx_plus_yy_generator() -> np.ndarray:
    """4×4 XX + YY operator as numpy array (complex128)."""
    X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    Y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    return np.kron(X, X) + np.kron(Y, Y)


_XX_YY = _xx_plus_yy_generator()


def _two_site_unitary(w: float, dt: float) -> torch.Tensor:
    """Build exp(-i * dt * w * (XX+YY)) as complex128 torch Tensor."""
    return torch.tensor(expm(-1j * dt * w * _XX_YY), dtype=torch.complex128)


# ---------------------------------------------------------------------------
# PART A — 8-qubit coherent information readout (extends existing MPS)
# ---------------------------------------------------------------------------

def mps_coherent_info_at_cut_pure(mps: list[torch.Tensor], cut: int) -> float:
    """Coherent information at cut for a pure global state.

    For |psi>_AB pure: I(A>B) = S(A) - S(AB) = S(A) - 0 = S(A).
    So coherent_info = entanglement entropy at cut, always >= 0.

    Args:
        mps: list of site tensors.
        cut: bond index in [0, N-2], splits sites [0..cut] from [cut+1..N-1].

    Returns:
        Coherent information value (= entropy for pure state, always >= 0).
    """
    return mps_entropy_at_cut(mps, cut)


def mps_cuts_readout_8q(mps: list[torch.Tensor]) -> list[dict]:
    """Compute 7 cuts for 8-qubit MPS; returns S_A, cond entropy, coherent info.

    For a pure state: S_AB = 0, cond_entropy = -S_A, coherent_info = S_A.
    """
    N = 8
    cuts = []
    for cut in range(N - 1):
        s_a = mps_entropy_at_cut(mps, cut)
        bond = mps[cut].shape[2]  # right bond dim at this cut
        cuts.append({
            "cut": cut + 1,          # 1-indexed
            "S_A": s_a,
            "S_AB": 0.0,             # pure state
            "conditional_entropy": -s_a,   # H(A|B) = S_AB - S_A = -S_A
            "coherent_information": s_a,   # I(A>B) = S_A - S_AB = S_A
            "bond_dim": bond,
        })
    return cuts


def run_8q_single(
    dt: float,
    threshold: float,
    max_bond: int,
    n_steps: int,
    n_qubits: int = 8,
) -> dict[str, Any]:
    """Run one 8-qubit MPS evolution and return max coherent info.

    Uses chain-topology weight matrix (w=0.8 on all nearest-neighbour bonds)
    as the baseline graph, matching the comparator module's __main__.

    Returns dict with max_coherent_info, max_bond_used, and cut results.
    """
    weights = torch.zeros(n_qubits, n_qubits, dtype=torch.float64)
    for i in range(n_qubits - 1):
        weights[i, i + 1] = 0.8
        weights[i + 1, i] = 0.8

    mps = mps_initial_state(n_qubits, max_bond)
    for _ in range(n_steps):
        mps = mps_apply_evolution(mps, weights, threshold, dt, max_bond)

    cuts = mps_cuts_readout_8q(mps)
    max_coh = max(c["coherent_information"] for c in cuts)
    max_bond_used = mps_max_bond_dim_used(mps)
    return {
        "max_coherent_info": max_coh,
        "max_bond_used": max_bond_used,
        "cuts": cuts,
        "params": {"dt": dt, "threshold": threshold, "max_bond": max_bond, "n_steps": n_steps},
    }


# ---------------------------------------------------------------------------
# PART B — 12-qubit MPS extension
# ---------------------------------------------------------------------------

def mps_initial_state_12q(bond_dim: int = 32) -> list[torch.Tensor]:
    """Initial 12-site product state |0...0⟩ MPS.

    Each site tensor shape (1, 2, 1); bond_dim argument sets the capacity
    for subsequent evolution (documented convention matches comparator).

    Args:
        bond_dim: maximum bond dimension for later evolution steps.

    Returns:
        List of 12 complex128 tensors, each shape (1, 2, 1), initialised to |0⟩.
    """
    return mps_initial_state(12, bond_dim)


def _mps_apply_two_site_unitary_12q(
    mps: list[torch.Tensor],
    site_i: int,
    unitary_4x4: torch.Tensor,
    max_bond: int,
) -> list[torch.Tensor]:
    """Apply nearest-neighbour two-site unitary at (site_i, site_i+1).

    Reuses the same SVD-truncation logic as the comparator module.
    Inline implementation to avoid import coupling issues at scale.
    """
    A = mps[site_i]       # (chi_L, 2, chi_M)
    B = mps[site_i + 1]   # (chi_M, 2, chi_R)
    chi_L = A.shape[0]
    chi_R = B.shape[2]

    theta = torch.einsum("lpm,mqr->lpqr", A, B)          # (chi_L, 2, 2, chi_R)
    theta_mat = theta.reshape(chi_L, 4, chi_R)
    theta_evolved = torch.einsum("ij,ljr->lir", unitary_4x4, theta_mat)  # (chi_L, 4, chi_R)
    theta_evolved = theta_evolved.reshape(chi_L, 2, 2, chi_R)
    theta_svd = theta_evolved.reshape(chi_L * 2, 2 * chi_R)

    U_svd, S, Vh = torch.linalg.svd(theta_svd, full_matrices=False)
    k = min(max_bond, S.shape[0])
    U_svd, S, Vh = U_svd[:, :k], S[:k], Vh[:k, :]

    S_diag = torch.diag(S.to(torch.complex128))
    mps[site_i] = U_svd.reshape(chi_L, 2, k)
    mps[site_i + 1] = (S_diag @ Vh).reshape(k, 2, chi_R)
    return mps


def mps_evolution_12q(
    weights: torch.Tensor,
    threshold: float,
    dt: float,
    max_bond: int,
) -> list[torch.Tensor]:
    """12-qubit MPS evolution under nearest-neighbour XX+YY Hamiltonian.

    Starts from |0...0⟩ product state and applies one round of evolution
    gates over all bonds with weight > threshold.

    Args:
        weights: (12, 12) real weight matrix; only upper-triangle used.
        threshold: pairs with weight <= threshold are skipped.
        dt: time step size.
        max_bond: maximum bond dimension cap.

    Returns:
        MPS state after one evolution pass (list of 12 tensors).
    """
    N = 12
    mps = mps_initial_state_12q(max_bond)
    for i in range(N - 1):
        w = float(weights[i, i + 1].item())
        if w <= threshold:
            continue
        U = _two_site_unitary(w, dt)
        mps = _mps_apply_two_site_unitary_12q(mps, i, U, max_bond)
    return mps


def mps_evolution_12q_multistep(
    weights: torch.Tensor,
    threshold: float,
    dt: float,
    max_bond: int,
    n_steps: int,
) -> list[torch.Tensor]:
    """12-qubit MPS evolution for n_steps passes.

    Applies mps_evolution_12q n_steps times, threading the MPS state
    through each step.

    Args:
        weights: (12, 12) real weight matrix.
        threshold: bond activation threshold.
        dt: time step size.
        max_bond: maximum bond dimension cap.
        n_steps: number of evolution passes.

    Returns:
        MPS state after n_steps passes.
    """
    N = 12
    mps = mps_initial_state_12q(max_bond)
    for _step in range(n_steps):
        for i in range(N - 1):
            w = float(weights[i, i + 1].item())
            if w <= threshold:
                continue
            U = _two_site_unitary(w, dt)
            mps = _mps_apply_two_site_unitary_12q(mps, i, U, max_bond)
    return mps


def mps_cuts_readout_12q(mps_state: list[torch.Tensor]) -> list[dict]:
    """Compute coherent information at all 11 cuts for a 12-qubit MPS.

    For a pure global state: coherent_info = S_A (entanglement entropy),
    always >= 0.  Cut k separates [0..k-1] from [k..11].

    Args:
        mps_state: list of 12 complex128 site tensors.

    Returns:
        List of 11 dicts, each with cut (1..11), S_A, S_AB=0,
        conditional_entropy=-S_A, coherent_information=S_A, bond_dim.
    """
    N = 12
    cuts = []
    for cut in range(N - 1):
        s_a = mps_entropy_at_cut(mps_state, cut)
        bond = mps_state[cut].shape[2]
        cuts.append({
            "cut": cut + 1,
            "S_A": s_a,
            "S_AB": 0.0,
            "conditional_entropy": -s_a,
            "coherent_information": s_a,
            "bond_dim": bond,
        })
    return cuts


def run_12q_single(
    dt: float,
    threshold: float,
    max_bond: int,
    n_steps: int,
) -> dict[str, Any]:
    """Run one 12-qubit MPS evolution and return diagnostics.

    Uses the same chain-topology weight matrix as 8-qubit baseline.

    Returns dict with max_coherent_info, max_bond_used, wall_time_s,
    memory_mb (if psutil available), cut results, and params.
    """
    N = 12
    weights = torch.zeros(N, N, dtype=torch.float64)
    for i in range(N - 1):
        weights[i, i + 1] = 0.8
        weights[i + 1, i] = 0.8

    t0 = time.time()
    mem_before = _mem_mb() if _HAS_PSUTIL else None

    mps = mps_evolution_12q_multistep(weights, threshold, dt, max_bond, n_steps)

    wall_time = time.time() - t0
    mem_after = _mem_mb() if _HAS_PSUTIL else None
    mem_delta = (mem_after - mem_before) if (mem_before is not None and mem_after is not None) else None

    cuts = mps_cuts_readout_12q(mps)
    max_coh = max(c["coherent_information"] for c in cuts)
    max_bond_used = mps_max_bond_dim_used(mps)

    return {
        "max_coherent_info": max_coh,
        "max_bond_used": max_bond_used,
        "wall_time_s": wall_time,
        "memory_delta_mb": mem_delta,
        "cuts": cuts,
        "params": {"dt": dt, "threshold": threshold, "max_bond": max_bond, "n_steps": n_steps},
    }


def _mem_mb() -> float:
    """Current process RSS memory in MB."""
    if not _HAS_PSUTIL:
        return 0.0
    import psutil
    return psutil.Process().memory_info().rss / 1024 / 1024


# ---------------------------------------------------------------------------
# PART A grid sweep — 8-qubit
# ---------------------------------------------------------------------------

GRID_DT = [0.05, 0.12, 0.25, 0.5, 1.0, 2.0]
GRID_THRESHOLD = [0.05, 0.10, 0.18, 0.30, 0.50]
GRID_MAX_BOND = [4, 8, 16, 32]
GRID_N_STEPS = [5, 10, 20, 40]

# Total: 6 × 5 × 4 × 4 = 480 combos
# Timeout cap: 5 min = 300 s

GRID_TIMEOUT_S = 300.0


def run_8q_grid_sweep() -> list[dict[str, Any]]:
    """Sweep 8-qubit parameter grid; return all results sorted by max_coh_info desc.

    Caps at GRID_TIMEOUT_S total wall time. Reports partial results if timeout hit.
    """
    results = []
    t_start = time.time()
    total = len(GRID_DT) * len(GRID_THRESHOLD) * len(GRID_MAX_BOND) * len(GRID_N_STEPS)
    done = 0

    for dt in GRID_DT:
        for threshold in GRID_THRESHOLD:
            for max_bond in GRID_MAX_BOND:
                for n_steps in GRID_N_STEPS:
                    elapsed = time.time() - t_start
                    if elapsed >= GRID_TIMEOUT_S:
                        print(
                            f"  [TIMEOUT] Grid sweep capped at {elapsed:.1f}s — "
                            f"{done}/{total} combos evaluated."
                        )
                        results.sort(key=lambda r: r["max_coherent_info"], reverse=True)
                        return results
                    try:
                        r = run_8q_single(dt, threshold, max_bond, n_steps)
                        results.append(r)
                    except Exception as exc:
                        results.append({
                            "max_coherent_info": float("nan"),
                            "max_bond_used": 0,
                            "cuts": [],
                            "params": {
                                "dt": dt, "threshold": threshold,
                                "max_bond": max_bond, "n_steps": n_steps,
                            },
                            "error": str(exc),
                        })
                    done += 1

    results.sort(key=lambda r: r["max_coherent_info"] if not math.isnan(r["max_coherent_info"]) else -1.0, reverse=True)
    return results


# ---------------------------------------------------------------------------
# PART C — verdict
# ---------------------------------------------------------------------------

def compute_verdict(
    grid_results: list[dict],
    result_12q: dict,
    threshold_signed: float = 0.05,
) -> dict[str, Any]:
    """Compare 8-qubit grid vs 12-qubit and emit verdict.

    Returns:
        dict with:
          - verdict_class: "regime-dependent" | "architectural"
          - verdict_text: concise human-readable finding
          - best_8q_params: best combo found in grid (if any)
          - max_coh_8q: best max coherent info from 8-qubit grid
          - max_coh_12q: max coherent info from 12-qubit run
          - signed_info_found_8q: bool — any 8-qubit combo > threshold_signed
          - signed_info_found_12q: bool — 12-qubit > threshold_signed
          - architectural_note: explanation of pure-state coherent info constraint
    """
    # Filter to valid (non-error, non-nan) results
    valid = [r for r in grid_results if not math.isnan(r.get("max_coherent_info", float("nan")))]
    max_coh_8q = max((r["max_coherent_info"] for r in valid), default=0.0)
    signed_8q = max_coh_8q > threshold_signed
    max_coh_12q = result_12q.get("max_coherent_info", 0.0)
    signed_12q = max_coh_12q > threshold_signed

    best_8q = valid[0] if valid else None
    best_params = best_8q["params"] if best_8q else {}

    # Pure-state note: for unitary MPS evolution, coh_info = S_A >= 0 always.
    # "Negative coh_info" requires mixed state (noisy channel) or mixed global state.
    architectural_note = (
        "PURE-STATE CONSTRAINT: Under closed unitary MPS evolution starting from "
        "|0...0⟩, S_AB = 0 for all time. Coherent information = S_A - S_AB = S_A >= 0 "
        "always. Negative values are structurally impossible without noise/mixing. "
        "The Track A '~0 coherent info' finding means S_A ≈ 0 (insufficient entanglement "
        "generation), not a sign failure. Increasing dt, n_steps, or lowering threshold "
        "drives S_A toward its regime maximum (bounded by min(|A|, |B|) * log 2)."
    )

    if signed_8q or signed_12q:
        if signed_8q:
            p = best_params
            verdict_text = (
                f"regime-dependent: signed coherent info (>{threshold_signed}) found at "
                f"dt={p.get('dt')}, threshold={p.get('threshold')}, "
                f"max_bond={p.get('max_bond')}, n_steps={p.get('n_steps')} — "
                f"max_coh_info={max_coh_8q:.4f}. "
                "Track A fix: tune parameters to the identified regime."
            )
        else:
            p = result_12q.get("params", {})
            verdict_text = (
                f"scale-dependent: 8-qubit fails all tested params but 12-qubit "
                f"(dt={p.get('dt')}, threshold={p.get('threshold')}) produces "
                f"coherent_info={max_coh_12q:.4f}. "
                "Track A fix: increase n_qubits or use 12-qubit scale."
            )
        verdict_class = "regime-dependent"
    else:
        verdict_text = (
            f"architectural (under tested params): no parameter combo among "
            f"{len(valid)} 8-qubit runs produced coherent_info > {threshold_signed} "
            f"(best={max_coh_8q:.6f}). 12-qubit also failed (best={max_coh_12q:.6f}). "
            "Root cause: pure-state MPS evolution on product state with weight=0.8 "
            "chain topology generates too little entanglement at tested scales. "
            "Track A fix: add noise channel (amplitude damping) to create mixed global "
            "state, OR use GHZ/Bell initial state with pre-entanglement, OR accept that "
            "signed-negative coherent info is structurally incompatible with unitary MPS."
        )
        verdict_class = "architectural"

    return {
        "verdict_class": verdict_class,
        "verdict_text": verdict_text,
        "best_8q_params": best_params,
        "max_coh_8q": max_coh_8q,
        "max_coh_12q": max_coh_12q,
        "signed_info_found_8q": signed_8q,
        "signed_info_found_12q": signed_12q,
        "threshold_signed": threshold_signed,
        "n_8q_combos_evaluated": len(valid),
        "architectural_note": architectural_note,
    }


# ---------------------------------------------------------------------------
# __main__
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    WALL_START = time.time()

    print("=" * 72)
    print("12-Qubit MPS Regime Exploration — Track A Diagnosis")
    print("=" * 72)

    # ------------------------------------------------------------------
    # PART A: 8-qubit grid sweep
    # ------------------------------------------------------------------
    print("\n[PART A] 8-qubit parameter grid sweep")
    print(f"  Grid: dt×{len(GRID_DT)} × threshold×{len(GRID_THRESHOLD)} × "
          f"max_bond×{len(GRID_MAX_BOND)} × n_steps×{len(GRID_N_STEPS)} "
          f"= {len(GRID_DT)*len(GRID_THRESHOLD)*len(GRID_MAX_BOND)*len(GRID_N_STEPS)} combos")
    print(f"  Timeout: {GRID_TIMEOUT_S:.0f}s")
    print()

    grid_t0 = time.time()
    grid_results = run_8q_grid_sweep()
    grid_wall = time.time() - grid_t0

    valid_results = [r for r in grid_results if "error" not in r and not math.isnan(r.get("max_coherent_info", float("nan")))]
    print(f"\n  Grid sweep complete: {len(valid_results)} valid combos in {grid_wall:.1f}s")

    top10 = valid_results[:10]
    print("\n  TOP 10 combos by max_coherent_information:")
    print(f"  {'rank':>4}  {'dt':>6}  {'thresh':>6}  {'bond':>5}  {'steps':>6}  {'max_coh':>10}  {'max_bond_used':>14}")
    print("  " + "-" * 60)
    for i, r in enumerate(top10, 1):
        p = r["params"]
        print(
            f"  {i:>4}  {p['dt']:>6.3f}  {p['threshold']:>6.3f}  "
            f"{p['max_bond']:>5}  {p['n_steps']:>6}  "
            f"{r['max_coherent_info']:>10.6f}  {r['max_bond_used']:>14}"
        )

    # Find best params for 12q run
    best_8q = valid_results[0] if valid_results else None
    if best_8q:
        bp = best_8q["params"]
        best_dt = bp["dt"]
        best_threshold = bp["threshold"]
        best_max_bond = min(bp["max_bond"], 32)  # cap for 12q
        best_n_steps = bp["n_steps"]
    else:
        # Fallback to highest-entanglement-expected params
        best_dt, best_threshold, best_max_bond, best_n_steps = 2.0, 0.05, 32, 40

    # ------------------------------------------------------------------
    # PART B: 12-qubit run at best params
    # ------------------------------------------------------------------
    print(f"\n[PART B] 12-qubit MPS at best params from 8q sweep:")
    print(f"  dt={best_dt}, threshold={best_threshold}, max_bond={best_max_bond}, n_steps={best_n_steps}")

    result_12q = run_12q_single(best_dt, best_threshold, best_max_bond, best_n_steps)

    print(f"\n  12-qubit results:")
    print(f"    max_coherent_info  : {result_12q['max_coherent_info']:.6f}")
    print(f"    max_bond_used      : {result_12q['max_bond_used']}")
    print(f"    wall_time          : {result_12q['wall_time_s']:.3f}s")
    if result_12q["memory_delta_mb"] is not None:
        print(f"    memory_delta       : {result_12q['memory_delta_mb']:.1f} MB")
    else:
        print(f"    memory_delta       : (psutil not available)")

    print("\n  12-qubit cut breakdown (all 11 cuts):")
    print(f"  {'cut':>4}  {'S_A':>10}  {'coh_info':>10}  {'bond_dim':>10}")
    print("  " + "-" * 40)
    for c in result_12q["cuts"]:
        print(f"  {c['cut']:>4}  {c['S_A']:>10.6f}  {c['coherent_information']:>10.6f}  {c['bond_dim']:>10}")

    # ------------------------------------------------------------------
    # PART C: Verdict
    # ------------------------------------------------------------------
    print("\n[PART C] Verdict")
    verdict = compute_verdict(grid_results, result_12q, threshold_signed=0.05)

    print(f"\n  Verdict class : {verdict['verdict_class'].upper()}")
    print(f"  Verdict text  : {verdict['verdict_text']}")
    print(f"\n  max_coh_8q    : {verdict['max_coh_8q']:.6f}")
    print(f"  max_coh_12q   : {verdict['max_coh_12q']:.6f}")
    print(f"  signed_8q     : {verdict['signed_info_found_8q']}")
    print(f"  signed_12q    : {verdict['signed_info_found_12q']}")
    print(f"  combos tested : {verdict['n_8q_combos_evaluated']}")

    print(f"\n  ARCHITECTURAL NOTE:")
    for line in verdict["architectural_note"].split(". "):
        if line:
            print(f"    {line}.")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    total_wall = time.time() - WALL_START
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"  8-qubit grid combos evaluated : {verdict['n_8q_combos_evaluated']}")
    print(f"  8-qubit best max_coh_info     : {verdict['max_coh_8q']:.6f}")
    print(f"  12-qubit max_coh_info         : {verdict['max_coh_12q']:.6f}")
    print(f"  Total wall time               : {total_wall:.1f}s")
    print(f"  Track A verdict               : {verdict['verdict_class'].upper()}")
    if verdict["verdict_class"] == "regime-dependent":
        bp = verdict["best_8q_params"]
        print(f"  Regime fix: dt={bp.get('dt')}, threshold={bp.get('threshold')}, "
              f"max_bond={bp.get('max_bond')}, n_steps={bp.get('n_steps')}")
    else:
        print("  Architectural fix: add noise channel or change initial state for signed info.")
    print("=" * 72)

    # Exit code: 0 if we found any regime, 1 if architectural
    sys.exit(0 if verdict["verdict_class"] == "regime-dependent" else 1)
