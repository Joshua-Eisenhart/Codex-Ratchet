#!/usr/bin/env python3
"""
A0-Kernel Discriminator Probe
==============================
Bounded sim from the AXIS next-sims table (row 1).

Input:  small bipartite cut states rho_AB (no bridge assumption)
Observables:
  K1: -S(A|B)  = I_c(A>B)   (coherent information)
  K2: I(A:B)                  (mutual information)
  K3: sum_r w_r I_c(A_r>B_r) (weighted shell-cut coherent information)
Discriminates: strongest entropy primitive for Axis 0.

Design constraints (from AXIS_0_1_2_QIT_MATH.md):
  - Ax0 needs a signed entropy/correlation primitive
  - -S(A|B) / I_c is the strongest simple working candidate
  - I(A:B) alone cannot go negative  (companion diagnostic only)
  - Shell-cut weighted form remains live but not yet cleanly realised

State battery:
  1. Separable product states
  2. Maximally entangled Bell states
  3. Werner states (entanglement parameter sweep)
  4. Partially entangled pure states (Schmidt sweep)
  5. Classical-quantum states (one side dephased)
  6. Rank-deficient mixed states

Token: E_A0_KERNEL_DISCRIMINATOR
"""

import json
import os
import sys
from datetime import datetime, UTC
from typing import Dict, List

import numpy as np
classification = "classical_baseline"  # auto-backfill

# ---------------------------------------------------------------------------
# QIT primitives (self-contained, no engine dependency)
# ---------------------------------------------------------------------------

def _ensure_density(rho: np.ndarray) -> np.ndarray:
    rho = (rho + rho.conj().T) / 2
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(evals, 0.0)
    rho = (evecs * evals) @ evecs.conj().T
    tr = np.real(np.trace(rho))
    if tr > 1e-15:
        rho /= tr
    return rho


def vn_entropy(rho: np.ndarray) -> float:
    """S(rho) = -Tr(rho log2 rho)."""
    rho = _ensure_density(rho)
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def partial_trace_B(rho_AB: np.ndarray) -> np.ndarray:
    return np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def partial_trace_A(rho_AB: np.ndarray) -> np.ndarray:
    return np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def coherent_info(rho_AB: np.ndarray) -> float:
    """I_c(A>B) = S(B) - S(AB) = -S(A|B)."""
    return vn_entropy(partial_trace_A(rho_AB)) - vn_entropy(rho_AB)


def mutual_info(rho_AB: np.ndarray) -> float:
    """I(A:B) = S(A) + S(B) - S(AB)."""
    return max(0.0,
               vn_entropy(partial_trace_B(rho_AB))
               + vn_entropy(partial_trace_A(rho_AB))
               - vn_entropy(rho_AB))


def shell_cut_Ic(rho_AB: np.ndarray, n_shells: int = 3) -> float:
    """
    Weighted shell-cut coherent information: sum_r w_r I_c(A_r>B_r).

    Simulates shell cuts by partial depolarisation at different strengths,
    keeping the bridge assumption *explicit*: each shell r is a convex
    mixture  rho_r = (1 - lambda_r) rho_AB + lambda_r (I/4)  with
    lambda_r in [0, 0.3, 0.6].  Weights are uniform (1/n_shells).

    This is the simplest honest shell-cut proxy that can run without
    geometry — it tests whether the *functional form* discriminates,
    not whether a concrete geometric shell family exists.
    """
    lambdas = np.linspace(0.0, 0.6, n_shells)
    I4 = np.eye(4, dtype=complex) / 4.0
    w = 1.0 / n_shells
    total = 0.0
    for lam in lambdas:
        rho_r = _ensure_density((1.0 - lam) * rho_AB + lam * I4)
        total += w * coherent_info(rho_r)
    return float(total)


# ---------------------------------------------------------------------------
# State battery
# ---------------------------------------------------------------------------

def _ket(bits: str) -> np.ndarray:
    """Return a 4-vector for a two-qubit computational basis ket."""
    idx = int(bits, 2)
    v = np.zeros(4, dtype=complex)
    v[idx] = 1.0
    return v


def _proj(psi: np.ndarray) -> np.ndarray:
    return np.outer(psi, psi.conj())


def make_state_battery() -> List[Dict]:
    """Return a list of (label, rho_AB) dicts covering the Ax0-relevant space."""
    battery = []

    # --- 1. Separable product states ---
    # |0>|0>
    battery.append({"label": "sep_00", "class": "separable",
                     "rho_AB": _proj(_ket("00"))})
    # |+>|->
    plus = np.array([1, 1], dtype=complex) / np.sqrt(2)
    minus = np.array([1, -1], dtype=complex) / np.sqrt(2)
    battery.append({"label": "sep_plus_minus", "class": "separable",
                     "rho_AB": _proj(np.kron(plus, minus))})
    # maximally mixed product  (I/2 x I/2)
    battery.append({"label": "sep_maxmix", "class": "separable",
                     "rho_AB": np.eye(4, dtype=complex) / 4.0})

    # --- 2. Bell states ---
    bell_plus = (_ket("00") + _ket("11")) / np.sqrt(2)
    bell_minus = (_ket("00") - _ket("11")) / np.sqrt(2)
    psi_plus = (_ket("01") + _ket("10")) / np.sqrt(2)
    psi_minus = (_ket("01") - _ket("10")) / np.sqrt(2)
    for name, psi in [("Phi+", bell_plus), ("Phi-", bell_minus),
                       ("Psi+", psi_plus), ("Psi-", psi_minus)]:
        battery.append({"label": f"bell_{name}", "class": "bell",
                         "rho_AB": _proj(psi)})

    # --- 3. Werner states  rho_W(p) = p |Psi->< Psi-| + (1-p) I/4 ---
    for p in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        rho_w = p * _proj(psi_minus) + (1.0 - p) * np.eye(4, dtype=complex) / 4.0
        battery.append({"label": f"werner_p{p:.1f}", "class": "werner",
                         "rho_AB": _ensure_density(rho_w),
                         "param": float(p)})

    # --- 4. Schmidt sweep:  cos(t)|00> + sin(t)|11> ---
    for t_deg in [10, 20, 30, 45, 60, 70, 80]:
        t = np.radians(t_deg)
        psi = np.cos(t) * _ket("00") + np.sin(t) * _ket("11")
        battery.append({"label": f"schmidt_{t_deg}deg", "class": "schmidt",
                         "rho_AB": _proj(psi), "param": t_deg})

    # --- 5. Classical-quantum states (A dephased in Z) ---
    # rho_cq = p|0><0| x rho_0 + (1-p)|1><1| x rho_1
    rho_0 = np.array([[0.8, 0.1], [0.1, 0.2]], dtype=complex)
    rho_1 = np.array([[0.3, -0.2], [-0.2, 0.7]], dtype=complex)
    for p in [0.3, 0.5, 0.7]:
        zero_proj = np.array([[1, 0], [0, 0]], dtype=complex)
        one_proj = np.array([[0, 0], [0, 1]], dtype=complex)
        rho_cq = p * np.kron(zero_proj, _ensure_density(rho_0)) \
                 + (1.0 - p) * np.kron(one_proj, _ensure_density(rho_1))
        battery.append({"label": f"cq_p{p:.1f}", "class": "classical_quantum",
                         "rho_AB": _ensure_density(rho_cq), "param": float(p)})

    # --- 6. Rank-deficient mixed (equal mix of two non-orthogonal products) ---
    psi_a = np.kron(np.array([1, 0], dtype=complex),
                    np.array([1, 1], dtype=complex) / np.sqrt(2))
    psi_b = np.kron(np.array([1, 1], dtype=complex) / np.sqrt(2),
                    np.array([0, 1], dtype=complex))
    rho_rd = 0.5 * _proj(psi_a) + 0.5 * _proj(psi_b)
    battery.append({"label": "rank_deficient_mix", "class": "rank_deficient",
                     "rho_AB": _ensure_density(rho_rd)})

    return battery


# ---------------------------------------------------------------------------
# Evaluation and discrimination
# ---------------------------------------------------------------------------

def evaluate_battery(battery: List[Dict]) -> List[Dict]:
    rows = []
    for entry in battery:
        rho = entry["rho_AB"]
        ic = coherent_info(rho)
        mi = mutual_info(rho)
        sc = shell_cut_Ic(rho)
        rows.append({
            "label": entry["label"],
            "class": entry["class"],
            "param": entry.get("param"),
            "K1_Ic": round(ic, 8),
            "K2_MI": round(mi, 8),
            "K3_shell_Ic": round(sc, 8),
        })
    return rows


def discriminate(rows: List[Dict]) -> Dict:
    """
    Score each kernel candidate on the Ax0 requirements:
      R1 — signed:  can produce both positive and negative values
      R2 — separable anchor:  equals zero on all separable states
      R3 — Bell ceiling:  reaches extremum on Bell states
      R4 — monotonic on Werner sweep:  monotone in entanglement param
      R5 — Schmidt sensitivity:  varies across Schmidt sweep
      R6 — classical-quantum honesty:  zero on CQ states (no quantum correlation)
    """
    kernels = ["K1_Ic", "K2_MI", "K3_shell_Ic"]
    verdicts = {}

    for k in kernels:
        vals = [r[k] for r in rows]

        # R1 signed
        has_pos = any(v > 1e-8 for v in vals)
        has_neg = any(v < -1e-8 for v in vals)
        r1 = has_pos and has_neg

        # R2 separable anchor
        sep_vals = [r[k] for r in rows if r["class"] == "separable"]
        r2 = all(abs(v) < 1e-6 for v in sep_vals)

        # R3 Bell ceiling
        bell_vals = [r[k] for r in rows if r["class"] == "bell"]
        all_vals_abs = [abs(v) for v in vals]
        max_abs = max(all_vals_abs) if all_vals_abs else 0
        r3 = len(bell_vals) > 0 and max(abs(v) for v in bell_vals) >= max_abs - 1e-6

        # R4 Werner monotonicity
        werner = sorted([(r["param"], r[k]) for r in rows if r["class"] == "werner"],
                        key=lambda x: x[0])
        if len(werner) >= 2:
            diffs = [werner[i + 1][1] - werner[i][1] for i in range(len(werner) - 1)]
            r4 = all(d >= -1e-8 for d in diffs) or all(d <= 1e-8 for d in diffs)
        else:
            r4 = False

        # R5 Schmidt sensitivity
        schmidt_vals = [r[k] for r in rows if r["class"] == "schmidt"]
        r5 = (max(schmidt_vals) - min(schmidt_vals)) > 1e-4 if schmidt_vals else False

        # R6 CQ honesty — I_c should be <= 0 on CQ states (no quantum advantage)
        cq_vals = [r[k] for r in rows if r["class"] == "classical_quantum"]
        r6 = all(v <= 1e-6 for v in cq_vals) if cq_vals else False

        score = sum([r1, r2, r3, r4, r5, r6])
        verdicts[k] = {
            "R1_signed": r1,
            "R2_sep_anchor": r2,
            "R3_bell_ceiling": r3,
            "R4_werner_monotone": r4,
            "R5_schmidt_sensitive": r5,
            "R6_cq_honest": r6,
            "score": score,
            "max_score": 6,
        }

    return verdicts


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run():
    print("=" * 72)
    print("A0-KERNEL DISCRIMINATOR PROBE")
    print("=" * 72)

    battery = make_state_battery()
    print(f"  State battery: {len(battery)} states")

    rows = evaluate_battery(battery)

    # Print compact table
    print(f"\n  {'Label':<25} {'K1 Ic':>10} {'K2 MI':>10} {'K3 shell':>10}")
    print(f"  {'─'*25} {'─'*10} {'─'*10} {'─'*10}")
    for r in rows:
        print(f"  {r['label']:<25} {r['K1_Ic']:>10.6f} {r['K2_MI']:>10.6f} {r['K3_shell_Ic']:>10.6f}")

    verdicts = discriminate(rows)

    print(f"\n  DISCRIMINATION SCORECARD")
    print(f"  {'─'*50}")
    for k, v in verdicts.items():
        checks = " ".join(
            f"{'Y' if v[f] else 'N'}"
            for f in ["R1_signed", "R2_sep_anchor", "R3_bell_ceiling",
                       "R4_werner_monotone", "R5_schmidt_sensitive", "R6_cq_honest"]
        )
        print(f"  {k:<15} score={v['score']}/{v['max_score']}  [{checks}]")

    winner = max(verdicts, key=lambda k: verdicts[k]["score"])
    print(f"\n  WINNER: {winner} (score {verdicts[winner]['score']}/{verdicts[winner]['max_score']})")

    # Overall verdict
    all_pass = verdicts[winner]["score"] >= 4
    verdict = "PASS" if all_pass else "DIAGNOSTIC_ONLY"
    print(f"\n{'=' * 72}")
    print(f"  PROBE VERDICT: {verdict}")
    print(f"{'=' * 72}")

    # Save artifact
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, "a0_kernel_discriminator_results.json")

    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "probe": "sim_a0_kernel_discriminator",
        "verdict": verdict,
        "winner": winner,
        "state_battery_size": len(battery),
        "scorecard": verdicts,
        "bridge_assumption": "none (pure cut-state evaluation)",
        "kernel_candidates": {
            "K1_Ic": "-S(A|B) = I_c(A>B) (coherent information)",
            "K2_MI": "I(A:B) (mutual information)",
            "K3_shell_Ic": "sum_r w_r I_c(A_r>B_r) (shell-cut weighted coherent info, depolarisation proxy)",
        },
        "results": rows,
    }

    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  Results saved: {out_path}")

    return verdict, winner, verdicts


if __name__ == "__main__":
    run()
