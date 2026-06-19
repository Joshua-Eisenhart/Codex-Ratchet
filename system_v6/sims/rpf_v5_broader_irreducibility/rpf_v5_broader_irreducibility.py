#!/usr/bin/env python3
"""
rpf_v5_broader_irreducibility

Scratch diagnostic for the grok-4.3 objection to rpf_v4:

  rpf_v4 tested the global-selection sequence measure only against deterministic
  embedding forward kernels. A stochastic HMM forward model is a wider model class.

This packet fits a time-inhomogeneous stochastic HMM by weighted Baum-Welch EM and
reports the best TV distance found between the empirical global-selection sequence
measure mu and the fitted HMM sequence measure. It runs the test on:

  1. the toy rpf_v3 carrier family used by rpf_v4;
  2. the grounded M(C) carrier from retrocausal_possibility_field_carrier_grounded_v0.

It also runs a genuinely reducible control on both carrier surfaces. The control is
per-shell independent, so a one-state time-inhomogeneous HMM can reproduce it exactly.

Honest ceiling: scratch_diagnostic only. Baum-Welch is a real stochastic-HMM fit, but
continuous HMM optimization is non-convex; the reported TV infimum is the best value
found by deterministic multi-start EM under the stated model class, not a formal global
optimization certificate.
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import math
import os
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np


SIM_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SIM_DIR, "..", "..", ".."))
RESULT_PATH = os.path.join(SIM_DIR, "results", "rpf_v5_broader_irreducibility_results.json")
TV_THRESHOLD = 0.05
EM_EPS = 1e-12


def _load_module(name: str, rel_path: str):
    path = os.path.join(REPO_ROOT, rel_path)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v4 = _load_module(
    "rpf_v4",
    "system_v6/sims/retrocausal_possibility_field_v4_irreducibility/"
    "retrocausal_possibility_field_v4_irreducibility.py",
)
grounded = _load_module(
    "rpf_grounded",
    "system_v6/sims/retrocausal_possibility_field_carrier_grounded_v0/"
    "retrocausal_possibility_field_carrier_grounded_v0.py",
)


TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing: implements the weighted forward-backward / Baum-Welch "
        "updates for stochastic HMM parameters and computes the generated sequence "
        "measure over the finite observation cube.",
    },
    "importlib": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing: imports the actual rpf_v4 and grounded M(C) carrier "
        "modules so v5 consumes their carrier and compressor surfaces instead of "
        "re-deriving them.",
    },
    "itertools": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing: enumerates independent carrier-family subsets and the "
        "finite observation cube used to compute total variation against the HMM.",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "Supportive: serializes the scratch diagnostic receipt.",
    },
    "scipy": {
        "tried": True,
        "used": False,
        "reason": "Available but not used. The packet uses explicit Baum-Welch EM so "
        "the stochastic-HMM fit is inspectable line-by-line.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "importlib": "load_bearing",
    "itertools": "load_bearing",
    "json": "supportive",
    "scipy": None,
}


@dataclass(frozen=True)
class SequenceMeasure:
    sequences: list[tuple[str, ...]]
    weights: np.ndarray
    mu: dict[tuple[str, ...], float]
    symbols: list[str]
    encoded: np.ndarray


def build_sequence_measure(sequences: list[tuple[str, ...]]) -> SequenceMeasure:
    if not sequences:
        raise ValueError("empty sequence list")
    length = len(sequences[0])
    if any(len(s) != length for s in sequences):
        raise ValueError("all sequences must have the same length")

    raw_weight = 1.0 / len(sequences)
    mu: dict[tuple[str, ...], float] = {}
    for seq in sequences:
        mu[seq] = mu.get(seq, 0.0) + raw_weight

    unique = sorted(mu)
    weights = np.array([mu[s] for s in unique], dtype=float)
    symbols = sorted({x for s in unique for x in s}, key=lambda x: int(x[1:]) if x.startswith("b") else x)
    sym_to_i = {s: i for i, s in enumerate(symbols)}
    encoded = np.array([[sym_to_i[x] for x in seq] for seq in unique], dtype=int)
    return SequenceMeasure(unique, weights, {s: float(mu[s]) for s in unique}, symbols, encoded)


def total_variation(a: dict[Any, float], b: dict[Any, float]) -> float:
    keys = set(a) | set(b)
    return 0.5 * sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys)


def _normalize(v: np.ndarray, axis: int | None = None) -> np.ndarray:
    v = np.maximum(v, EM_EPS)
    if axis is None:
        return v / v.sum()
    return v / v.sum(axis=axis, keepdims=True)


def _random_hmm(rng: np.random.Generator, k: int, length: int, n_symbols: int) -> dict[str, np.ndarray]:
    return {
        "pi": rng.dirichlet(np.ones(k)),
        "A": np.stack([rng.dirichlet(np.ones(k), size=k) for _ in range(length - 1)]),
        "B": np.stack([rng.dirichlet(np.ones(n_symbols), size=k) for _ in range(length)]),
    }


def _seeded_hmm_from_positions(sm: SequenceMeasure, k: int, rng: np.random.Generator) -> dict[str, np.ndarray]:
    """A deterministic-ish initializer: cluster each position's symbols by rank modulo k.
    This gives EM a clock/memory-like start while retaining stochastic emissions."""
    length = sm.encoded.shape[1]
    n_symbols = len(sm.symbols)
    pi = np.full(k, 0.05 / k)
    A = np.full((length - 1, k, k), 0.05 / k)
    B = np.full((length, k, n_symbols), 0.05 / n_symbols)

    for row, w in zip(sm.encoded, sm.weights):
        states = [int(row[t] % k) for t in range(length)]
        pi[states[0]] += w
        for t, obs in enumerate(row):
            B[t, states[t], obs] += w
        for t in range(length - 1):
            A[t, states[t], states[t + 1]] += w

    return {"pi": _normalize(pi), "A": _normalize(A, axis=2), "B": _normalize(B, axis=2)}


def _forward_backward_one(obs: np.ndarray, params: dict[str, np.ndarray]) -> tuple[float, np.ndarray, np.ndarray]:
    pi = params["pi"]
    A = params["A"]
    B = params["B"]
    length = len(obs)
    k = len(pi)

    alpha = np.zeros((length, k), dtype=float)
    scales = np.zeros(length, dtype=float)

    alpha[0] = pi * B[0, :, obs[0]]
    scales[0] = max(alpha[0].sum(), EM_EPS)
    alpha[0] /= scales[0]
    for t in range(1, length):
        alpha[t] = (alpha[t - 1] @ A[t - 1]) * B[t, :, obs[t]]
        scales[t] = max(alpha[t].sum(), EM_EPS)
        alpha[t] /= scales[t]

    beta = np.zeros((length, k), dtype=float)
    beta[-1] = 1.0
    for t in range(length - 2, -1, -1):
        beta[t] = A[t] @ (B[t + 1, :, obs[t + 1]] * beta[t + 1])
        beta[t] /= scales[t + 1]

    logp = float(np.log(scales).sum())
    return logp, alpha, beta


def hmm_sequence_probability(seq_i: tuple[int, ...], params: dict[str, np.ndarray]) -> float:
    logp, _, _ = _forward_backward_one(np.array(seq_i, dtype=int), params)
    return float(math.exp(logp))


def baum_welch(
    sm: SequenceMeasure,
    k: int,
    *,
    n_restarts: int = 12,
    max_iter: int = 250,
    tol: float = 1e-10,
    seed: int = 20260613,
) -> dict[str, Any]:
    length = sm.encoded.shape[1]
    n_symbols = len(sm.symbols)
    best: dict[str, Any] | None = None

    for restart in range(n_restarts):
        rng = np.random.default_rng(seed + 1009 * k + restart)
        if restart == 0:
            params = _seeded_hmm_from_positions(sm, k, rng)
        else:
            params = _random_hmm(rng, k, length, n_symbols)

        prev_ll: float | None = None
        converged = False
        for iteration in range(max_iter):
            pi_acc = np.full(k, EM_EPS)
            A_acc = np.full((length - 1, k, k), EM_EPS)
            A_den = np.full((length - 1, k), EM_EPS)
            B_acc = np.full((length, k, n_symbols), EM_EPS)
            B_den = np.full((length, k), EM_EPS)
            ll = 0.0

            for obs, w in zip(sm.encoded, sm.weights):
                logp, alpha, beta = _forward_backward_one(obs, params)
                ll += float(w * logp)
                gamma = alpha * beta
                gamma = gamma / np.maximum(gamma.sum(axis=1, keepdims=True), EM_EPS)
                pi_acc += w * gamma[0]

                for t in range(length):
                    B_acc[t, :, obs[t]] += w * gamma[t]
                    B_den[t] += w * gamma[t]

                for t in range(length - 1):
                    next_factor = params["B"][t + 1, :, obs[t + 1]] * beta[t + 1]
                    xi = alpha[t][:, None] * params["A"][t] * next_factor[None, :]
                    xi = xi / max(xi.sum(), EM_EPS)
                    A_acc[t] += w * xi
                    A_den[t] += w * gamma[t]

            params = {
                "pi": _normalize(pi_acc),
                "A": A_acc / np.maximum(A_den[:, :, None], EM_EPS),
                "B": B_acc / np.maximum(B_den[:, :, None], EM_EPS),
            }
            params["A"] = _normalize(params["A"], axis=2)
            params["B"] = _normalize(params["B"], axis=2)

            if prev_ll is not None and abs(ll - prev_ll) < tol:
                converged = True
                break
            prev_ll = ll

        fit = {"params": params, "log_likelihood": prev_ll if prev_ll is not None else ll,
               "restart": restart, "iterations": iteration + 1, "converged": converged}
        if best is None or fit["log_likelihood"] > best["log_likelihood"]:
            best = fit

    assert best is not None
    return best


def hmm_measure(symbols: list[str], length: int, params: dict[str, np.ndarray]) -> dict[tuple[str, ...], float]:
    out: dict[tuple[str, ...], float] = {}
    for seq_i in itertools.product(range(len(symbols)), repeat=length):
        p = hmm_sequence_probability(seq_i, params)
        if p > 1e-14:
            out[tuple(symbols[i] for i in seq_i)] = p
    # absorb numerical drift into normalization
    z = sum(out.values())
    if z > 0:
        out = {k: float(v / z) for k, v in out.items()}
    return out


def fit_stochastic_hmm_tv(
    sequences: list[tuple[str, ...]],
    hidden_state_counts: list[int],
    *,
    restarts: int,
    max_iter: int,
    seed: int,
) -> dict[str, Any]:
    sm = build_sequence_measure(sequences)
    rows = []
    for k in hidden_state_counts:
        fit = baum_welch(sm, k, n_restarts=restarts, max_iter=max_iter, seed=seed)
        gen = hmm_measure(sm.symbols, sm.encoded.shape[1], fit["params"])
        tv = total_variation(sm.mu, gen)
        support_mass = sum(gen.get(s, 0.0) for s in sm.mu)
        rows.append({
            "hidden_states": k,
            "tv": tv,
            "weighted_log_likelihood": fit["log_likelihood"],
            "best_restart": fit["restart"],
            "iterations": fit["iterations"],
            "converged": fit["converged"],
            "generated_support_mass_on_empirical_support": support_mass,
        })
    best = min(rows, key=lambda r: r["tv"])
    return {
        "method": "weighted Baum-Welch EM for a time-inhomogeneous categorical HMM; "
        "best row chosen by TV after multi-start maximum-likelihood fitting",
        "n_unique_sequences": len(sm.sequences),
        "n_symbols": len(sm.symbols),
        "symbols": sm.symbols,
        "hidden_state_counts": hidden_state_counts,
        "rows": rows,
        "best": best,
        "tv_infimum_estimate": best["tv"],
        "irreducible_under_stochastic_hmm": best["tv"] > TV_THRESHOLD,
    }


def toy_positive_sequences() -> list[tuple[str, ...]]:
    return [v4.global_output_sequence(fc) for fc in v4.perturbation_family()]


def toy_negative_sequences() -> list[tuple[str, ...]]:
    return [v4.reducible_output_sequence(fc) for fc in v4.perturbation_family()]


def grounded_family() -> list[list[list[str]]]:
    """Independent subset family on the real M(C) canonical shell pools.

    The pools are the grounded packet's canonical shell pools. They are sampled
    independently, so the reducible control really is per-position independent.
    """
    shells = grounded.CANONICAL_SHELLS_OUTER_TO_INNER
    family = []
    for outer in itertools.combinations(shells[0], 4):
        for mid in itertools.combinations(shells[1], 4):
            for inner in itertools.combinations(shells[2], 4):
                family.append([list(outer), list(mid), list(inner)])
    return family


def grounded_global_sequence(carrier: dict[str, Any], shells: list[list[str]]) -> tuple[str, ...]:
    glob = grounded.global_compressor(carrier, shells, grounded.PROBE_FAMILY_C)
    return tuple(glob["global_joint_assignment"][i] for i in range(3))


def grounded_reducible_sequence(shells: list[list[str]]) -> tuple[str, ...]:
    return tuple(sorted(s, key=lambda b: int(b[1:]))[0] for s in shells)


def grounded_positive_sequences() -> list[tuple[str, ...]]:
    carrier = grounded.load_frozen_carrier()
    return [grounded_global_sequence(carrier, shells) for shells in grounded_family()]


def grounded_negative_sequences() -> list[tuple[str, ...]]:
    return [grounded_reducible_sequence(shells) for shells in grounded_family()]


def hidden_counts(n_f: int) -> list[int]:
    values = list(range(1, n_f + 1))
    for k in (n_f + max(1, n_f // 2), 2 * n_f):
        if k not in values:
            values.append(k)
    return values


def measured_grounded_Nf() -> dict[str, Any]:
    carrier = grounded.load_frozen_carrier()
    glob = grounded.global_compressor(carrier, grounded.CANONICAL_SHELLS_OUTER_TO_INNER, grounded.PROBE_FAMILY_C)
    per_shell = [s["fiber_cardinality"]["max_fiber"] for s in glob["per_stratum"]]
    return {"N_f": max(per_shell), "per_shell_max_fiber": per_shell}


def summarize_case(
    label: str,
    sequences_fn: Callable[[], list[tuple[str, ...]]],
    n_f: int,
    *,
    deterministic_v4_tv: float | None,
    restarts: int,
    max_iter: int,
    seed: int,
) -> dict[str, Any]:
    sequences = sequences_fn()
    fit = fit_stochastic_hmm_tv(
        sequences,
        hidden_counts(n_f),
        restarts=restarts,
        max_iter=max_iter,
        seed=seed,
    )
    return {
        "label": label,
        "family_size": len(sequences),
        "N_f": n_f,
        "threshold": TV_THRESHOLD,
        "deterministic_embedding_v4_tv": deterministic_v4_tv,
        "stochastic_hmm_fit": fit,
        "verdict": "OPEN" if fit["irreducible_under_stochastic_hmm"] else "KILLED",
        "conclusion": (
            "OPEN under this stochastic-HMM fit: best TV remains above threshold."
            if fit["irreducible_under_stochastic_hmm"]
            else "KILLED under this stochastic-HMM fit: a wider stochastic forward HMM "
            "reproduces the sequence measure within threshold."
        ),
    }


def build_result(*, restarts: int = 14, max_iter: int = 300, seed: int = 20260613) -> dict[str, Any]:
    toy_n_f = v4.measured_fiber_size_Nf()["N_f"]
    grounded_nf = measured_grounded_Nf()
    grounded_n_f = grounded_nf["N_f"]

    toy_pos = summarize_case(
        "toy_v3_global_selection",
        toy_positive_sequences,
        toy_n_f,
        deterministic_v4_tv=0.046783625730994205,
        restarts=restarts,
        max_iter=max_iter,
        seed=seed,
    )
    toy_neg = summarize_case(
        "toy_v3_reducible_negative_control",
        toy_negative_sequences,
        toy_n_f,
        deterministic_v4_tv=None,
        restarts=max(6, restarts // 2),
        max_iter=max_iter,
        seed=seed + 1,
    )
    grounded_pos = summarize_case(
        "grounded_M_C_global_selection",
        grounded_positive_sequences,
        grounded_n_f,
        deterministic_v4_tv=None,
        restarts=restarts,
        max_iter=max_iter,
        seed=seed + 2,
    )
    grounded_neg = summarize_case(
        "grounded_M_C_reducible_negative_control",
        grounded_negative_sequences,
        grounded_n_f,
        deterministic_v4_tv=None,
        restarts=max(6, restarts // 2),
        max_iter=max_iter,
        seed=seed + 3,
    )

    controls_pass = (
        toy_neg["stochastic_hmm_fit"]["tv_infimum_estimate"] <= 1e-8
        and grounded_neg["stochastic_hmm_fit"]["tv_infimum_estimate"] <= 1e-8
    )
    any_open = (
        toy_pos["stochastic_hmm_fit"]["irreducible_under_stochastic_hmm"]
        or grounded_pos["stochastic_hmm_fit"]["irreducible_under_stochastic_hmm"]
    )

    if any_open:
        bottom_line = (
            "OPEN at scratch_diagnostic ceiling: at least one carrier remains above "
            "the TV threshold under the wider stochastic-HMM fit."
        )
        strong_claim_status = "OPEN"
    else:
        bottom_line = (
            "KILLED at scratch_diagnostic ceiling: the rpf_v4 reducible verdict survives "
            "the wider stochastic-HMM forward class on both the toy v3 and grounded M(C) "
            "carrier families; the negative controls fit at tv~0."
        )
        strong_claim_status = "KILLED"

    invariants = {
        "toy_negative_control_tv_near_zero": toy_neg["stochastic_hmm_fit"]["tv_infimum_estimate"] <= 1e-8,
        "grounded_negative_control_tv_near_zero": grounded_neg["stochastic_hmm_fit"]["tv_infimum_estimate"] <= 1e-8,
        "toy_hidden_sweep_reaches_2Nf": max(toy_pos["stochastic_hmm_fit"]["hidden_state_counts"]) == 2 * toy_n_f,
        "grounded_hidden_sweep_reaches_2Nf": max(grounded_pos["stochastic_hmm_fit"]["hidden_state_counts"]) == 2 * grounded_n_f,
        "toy_primary_ran": toy_pos["family_size"] > 0,
        "grounded_primary_ran": grounded_pos["family_size"] > 0,
    }

    return {
        "name": "rpf_v5_broader_irreducibility",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "method": {
            "fit": "weighted Baum-Welch EM / forward-backward for a stochastic "
            "time-inhomogeneous categorical HMM",
            "model": "P(x_1..x_L)=sum_z pi(z1) B_1(z1,x1) prod_t A_t(zt,z_{t+1}) "
            "B_{t+1}(z_{t+1},x_{t+1}); A_t and B_t are stochastic, hidden size K",
            "honesty": "non-convex continuous fit; TV infimum is the best TV found by "
            "deterministic multi-start EM, not a formal global certificate",
            "restarts": restarts,
            "max_iter": max_iter,
            "seed": seed,
        },
        "threshold": TV_THRESHOLD,
        "measured_N_f": {
            "toy_v3": v4.measured_fiber_size_Nf(),
            "grounded_M_C": grounded_nf,
        },
        "cases": {
            "toy_v3_global": toy_pos,
            "toy_v3_negative_control": toy_neg,
            "grounded_M_C_global": grounded_pos,
            "grounded_M_C_negative_control": grounded_neg,
        },
        "invariants": invariants,
        "all_invariants_hold": all(invariants.values()),
        "negative_controls_pass": controls_pass,
        "strong_retrocausal_global_claim_status": strong_claim_status,
        "bottom_line": bottom_line,
        "claim_ceiling": (
            "This tests only finite sequence-measure reducibility against a fitted "
            "bounded stochastic HMM forward model. It does not prove physics, temporal "
            "retrocausation, Axis0, manifold structure, or canonical status."
        ),
        "all_pass": all(invariants.values()) and controls_pass,
    }


def main() -> int:
    result = build_result()
    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    print(json.dumps({
        "ok": result["all_pass"],
        "bottom_line": result["bottom_line"],
        "toy_tv": result["cases"]["toy_v3_global"]["stochastic_hmm_fit"]["tv_infimum_estimate"],
        "grounded_tv": result["cases"]["grounded_M_C_global"]["stochastic_hmm_fit"]["tv_infimum_estimate"],
        "toy_negative_tv": result["cases"]["toy_v3_negative_control"]["stochastic_hmm_fit"]["tv_infimum_estimate"],
        "grounded_negative_tv": result["cases"]["grounded_M_C_negative_control"]["stochastic_hmm_fit"]["tv_infimum_estimate"],
        "result_path": RESULT_PATH,
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
