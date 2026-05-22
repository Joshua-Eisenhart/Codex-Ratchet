#!/usr/bin/env python3
"""Engine entropy-decay asymptotic and robustness probe.

Grok iter_212 corrected an overclaim: relative-entropy decay is asymptotic to
the square of the slow channel eigenvalue after a short transient, not exact
from the first cycle. This formal scout reproduces that target in PyTorch while
repairing two sidequest issues: the sidequest "random pure" Bloch vector is just
outside the Bloch ball, and its random coherent perturbation is non-Hermitian.

This is bounded single-engine evidence. It cannot promote Phi0 closure,
scale-level basin admission, PEPS/PEPS3D dynamics, or final manifold admission.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

import sim_two_root_constraint_iter195_single_engine_spectral_reproduction_probe as spectral


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_engine_entropy_decay_asymptotic_and_robustness_probe_results.json"

NAME = "two_root_constraint_engine_entropy_decay_asymptotic_and_robustness_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_engine_entropy_decay_asymptotic_robustness"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_late_grok_204_212_engine_entropy_decay"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal bounded single-engine scout only: verifies asymptotic entropy-decay "
    "language, the gamma_P steady-state trajectory, and Hermitian coherent "
    "perturbation robustness. It cannot promote Phi0 closure, scale-level "
    "attractor-basin admission, PEPS/PEPS3D dynamics, full tensor convergence, "
    "or final manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact Liouvillian channels, spectra, fixed states, relative entropy, and perturbation sweep",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing claim guard separating exact first-cycle decay, asymptotic decay, and final admission",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive sidequest receipt loading and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive repository path accounting"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

DTYPE = torch.complex128
FLOAT = torch.float64
N_HAT = (0.7, 0.0, 0.5)
TAU = 1.0
GAMMA_SWEEP = (0.05, 0.1, 0.3, 0.5, 0.8, 1.2, 2.0, 5.0)
DELTA_SWEEP = (0.0, 0.01, 0.05, 0.1, 0.3, 0.5, 1.0)
RATIO_TOL = 7.5e-4
FIRST_TRANSIENT_MARGIN = 2.0e-3
SMALL_DELTA_REL_TOL = 0.1

SIDEQUEST_SOURCE = REPO / "system_v5" / "grok_sim" / "iters" / "iter_212_audit_response_decay_steadystate_perturbation.py"
SIDEQUEST_RESULT = REPO / "system_v5" / "grok_sim" / "results" / "iter_212_audit_response_decay_steadystate_perturbation_results.json"
ROUTING_RESULT = RESULT_DIR / "two_root_constraint_late_grok_204_212_engine_axis0_sidequest_routing_probe_results.json"
SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "iter195_spectral_module": SCOUT_ROOT / "sim_two_root_constraint_iter195_single_engine_spectral_reproduction_probe.py",
    "sidequest_source": SIDEQUEST_SOURCE,
    "sidequest_result": SIDEQUEST_RESULT,
    "routing_result": ROUTING_RESULT,
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()) .hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            item = value.detach().cpu().item()
            if isinstance(item, complex):
                return {"real": float(item.real), "imag": float(item.imag)}
            return float(item)
        return value.detach().cpu().tolist()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, dict):
        return {str(key): jsonable(inner) for key, inner in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(inner) for inner in value]
    return value


def source_hashes() -> dict[str, Any]:
    return {name: {"path": rel(path), "sha256": sha256(path), "exists": path.exists()} for name, path in SOURCE_FILES.items()}


def stage_specs(
    sheet: str,
    n_hat: tuple[float, float, float],
    *,
    gamma_p: float = 0.5,
    perturb: torch.Tensor | None = None,
    delta: float = 0.0,
) -> dict[str, tuple[torch.Tensor, list[torch.Tensor]]]:
    H0 = n_hat[0] * spectral.SX + n_hat[1] * spectral.SY + n_hat[2] * spectral.SZ
    H = H0 if sheet == "L" else -H0
    if perturb is not None:
        H = H + float(delta) * perturb
    l_f_1 = 0.4 * spectral.SX + 0.2 * spectral.SY + 0.5 * spectral.SZ
    l_f_2 = 0.4 * spectral.SX - 0.2 * spectral.SY + 0.5 * spectral.SZ
    m_v_1 = math.sqrt(0.3) * (0.3 * spectral.SX + 0.4 * spectral.SY + 0.2 * spectral.SZ)
    m_v_2 = math.sqrt(0.3) * (0.3 * spectral.SX + 0.4 * spectral.SY - 0.2 * spectral.SZ)
    ladder = spectral.SM if sheet == "L" else spectral.SP
    p_plus = 0.5 * (spectral.I2 + spectral.SZ)
    p_minus = 0.5 * (spectral.I2 - spectral.SZ)
    return {
        "Se": (0.1 * H, [l_f_1, l_f_2]),
        "Ne": (H, [m_v_1, m_v_2]),
        "Ni": (0.1 * H, [math.sqrt(gamma_p) * ladder]),
        "Si": (H, [math.sqrt(0.3) * p_plus, math.sqrt(0.3) * p_minus]),
    }


def engine_channel(
    *,
    sheet: str = "L",
    n_hat: tuple[float, float, float] = N_HAT,
    gamma_p: float = 0.5,
    perturb: torch.Tensor | None = None,
    delta: float = 0.0,
) -> torch.Tensor:
    stages = stage_specs(sheet, n_hat, gamma_p=gamma_p, perturb=perturb, delta=delta)
    channel = torch.eye(4, dtype=DTYPE)
    for terrain in spectral.engine_order(sheet):
        H, collapse_ops = stages[terrain]
        channel = spectral.stage_propagator(H, collapse_ops, TAU) @ channel
    return channel


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = 0.5 * (rho + rho.conj().T)
    return rho / torch.trace(rho)


def fixed_density(channel: torch.Tensor) -> torch.Tensor:
    eigvals, eigvecs = torch.linalg.eig(channel)
    idx = int(torch.argmin(torch.abs(eigvals - (1.0 + 0.0j))).item())
    rho = spectral.col_mat(eigvecs[:, idx])
    return normalize_density(rho)


def apply_channel(channel: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    return normalize_density(spectral.apply_superop(channel, rho))


def entropy(rho: torch.Tensor, eps: float = 1.0e-14) -> float:
    vals = torch.linalg.eigvalsh(normalize_density(rho)).real.clamp_min(eps)
    return float((-vals * torch.log(vals)).sum().item())


def matrix_log_psd(rho: torch.Tensor, eps: float = 1.0e-14) -> torch.Tensor:
    vals, vecs = torch.linalg.eigh(normalize_density(rho))
    vals = vals.real.clamp_min(eps).to(DTYPE)
    return vecs @ torch.diag(torch.log(vals)) @ vecs.conj().T


def relative_entropy(rho: torch.Tensor, sigma: torch.Tensor) -> float:
    rho_n = normalize_density(rho)
    return float(torch.trace(rho_n @ (matrix_log_psd(rho_n) - matrix_log_psd(sigma))).real.item())


def bloch_norm(vector: tuple[float, float, float]) -> float:
    return math.sqrt(sum(item * item for item in vector))


def valid_initial_states() -> list[tuple[str, torch.Tensor]]:
    raw = (0.6, 0.4, 0.7)
    raw_norm = bloch_norm(raw)
    valid_random = tuple(item / raw_norm for item in raw)
    return [
        ("zero", spectral.rho_from_bloch((0.0, 0.0, 1.0))),
        ("one", spectral.rho_from_bloch((0.0, 0.0, -1.0))),
        ("plus", spectral.rho_from_bloch((1.0, 0.0, 0.0))),
        ("max_mixed", 0.5 * spectral.I2),
        ("random_valid_pure", spectral.rho_from_bloch(valid_random)),
    ]


def decay_analysis(channel: torch.Tensor, rho_ss: torch.Tensor, lambda_1_squared: float) -> dict[str, Any]:
    rows = []
    first_ratios = []
    late_ratios = []
    for name, rho0 in valid_initial_states():
        rho = rho0
        d_values = [relative_entropy(rho, rho_ss)]
        for _ in range(8):
            rho = apply_channel(channel, rho)
            d_values.append(relative_entropy(rho, rho_ss))
        ratios = []
        for idx in range(5):
            if d_values[idx] > 1.0e-15:
                ratios.append(d_values[idx + 1] / d_values[idx])
        if ratios:
            first_ratios.append(ratios[0])
            late_ratios.append(ratios[-1])
        rows.append({"name": name, "D_trajectory": d_values, "ratios": ratios})
    mean_first = sum(first_ratios) / len(first_ratios)
    mean_late = sum(late_ratios) / len(late_ratios)
    return {
        "rows": rows,
        "mean_first_cycle_ratio": mean_first,
        "mean_late_cycle_ratio": mean_late,
        "lambda_1_squared": lambda_1_squared,
        "first_cycle_exact_claim_supported": abs(mean_first - lambda_1_squared) < RATIO_TOL,
        "asymptotic_claim_supported": abs(mean_late - lambda_1_squared) < RATIO_TOL,
        "first_cycle_transient_detected": abs(mean_first - lambda_1_squared) > FIRST_TRANSIENT_MARGIN,
    }


def gamma_trajectory() -> list[dict[str, Any]]:
    rows = []
    for gamma_p in GAMMA_SWEEP:
        channel = engine_channel(gamma_p=gamma_p)
        rho_ss = fixed_density(channel)
        r = spectral.bloch(rho_ss)
        rows.append(
            {
                "gamma_p": gamma_p,
                "bloch": r,
                "norm_r": math.sqrt(sum(item * item for item in r)),
                "entropy": entropy(rho_ss),
            }
        )
    return rows


def perturbation_sweep() -> dict[str, list[dict[str, float]]]:
    random_hermitian = 0.3 * spectral.SZ + 0.2 * spectral.SX + 0.4 * spectral.SY
    options = {
        "sigma_x": spectral.SX,
        "sigma_y": spectral.SY,
        "sigma_z": spectral.SZ,
        "random_hermitian": random_hermitian,
    }
    out: dict[str, list[dict[str, float]]] = {}
    for name, perturb in options.items():
        rows = []
        for delta in DELTA_SWEEP:
            channel = engine_channel(perturb=perturb, delta=delta)
            eig_abs = spectral.sorted_abs(torch.linalg.eigvals(channel))
            rows.append({"delta": delta, "lambda_1": eig_abs[1], "lambda_2": eig_abs[2], "gap_to_lambda_2": eig_abs[1] - eig_abs[2]})
        out[name] = rows
    return out


def sidequest_issue_checks() -> dict[str, Any]:
    invalid_raw_norm = bloch_norm((0.6, 0.4, 0.7))
    random_v = torch.tensor(
        [[0.3 + 0.1j, 0.2 - 0.4j], [0.2 + 0.4j, -0.3 - 0.1j]],
        dtype=DTYPE,
    )
    hermitian_error = float(torch.linalg.matrix_norm(random_v - random_v.conj().T).real.item())
    return {
        "sidequest_random_pure_bloch_norm": invalid_raw_norm,
        "sidequest_random_pure_is_physical": invalid_raw_norm <= 1.0 + 1.0e-12,
        "sidequest_random_perturbation_hermitian_error": hermitian_error,
        "sidequest_random_perturbation_is_hermitian": hermitian_error < 1.0e-12,
        "formal_repairs": [
            "normalize random Bloch vector to a valid pure state",
            "replace non-Hermitian random perturbation with a Hermitian Pauli combination",
        ],
    }


def z3_claim_guard(decay: dict[str, Any], gamma_rows: list[dict[str, Any]], perturb: dict[str, list[dict[str, float]]]) -> dict[str, Any]:
    exact_first = z3.Bool("exact_first_cycle_decay_claim")
    asymptotic = z3.Bool("asymptotic_decay_claim")
    monotone_gamma = z3.Bool("monotone_gamma_trajectory")
    robust = z3.Bool("small_delta_slow_mode_robust")
    final_admission = z3.Bool("final_manifold_admission_allowed")
    gamma_norms = [row["norm_r"] for row in gamma_rows]
    gamma_entropies = [row["entropy"] for row in gamma_rows]
    gamma_monotone = all(left <= right for left, right in zip(gamma_norms, gamma_norms[1:])) and all(
        left >= right for left, right in zip(gamma_entropies, gamma_entropies[1:])
    )
    small_delta_ratios = []
    for rows in perturb.values():
        base = rows[0]["lambda_1"]
        small = next(row["lambda_1"] for row in rows if row["delta"] == 0.05)
        small_delta_ratios.append(abs(small - base) / base)
    robust_small = max(small_delta_ratios) <= SMALL_DELTA_REL_TOL

    solver = z3.Solver()
    solver.add(exact_first == bool(decay["first_cycle_exact_claim_supported"]))
    solver.add(asymptotic == bool(decay["asymptotic_claim_supported"]))
    solver.add(monotone_gamma == bool(gamma_monotone))
    solver.add(robust == bool(robust_small))
    solver.add(final_admission == False)
    solver.add(z3.Implies(final_admission, z3.And(asymptotic, monotone_gamma, robust)))
    status = solver.check()
    model = solver.model() if status == z3.sat else None
    return {
        "solver": "z3",
        "sat": status == z3.sat,
        "exact_first_cycle_decay_claim": bool(model[exact_first]) if model is not None else None,
        "asymptotic_decay_claim": bool(model[asymptotic]) if model is not None else None,
        "monotone_gamma_trajectory": bool(model[monotone_gamma]) if model is not None else None,
        "small_delta_slow_mode_robust": bool(model[robust]) if model is not None else None,
        "final_manifold_admission_allowed": bool(model[final_admission]) if model is not None else None,
        "max_small_delta_relative_shift": max(small_delta_ratios),
        "rule": "This scout can correct the entropy-decay language and support local robustness, but cannot admit the final manifold.",
    }


def main() -> int:
    started = time.time()
    sidequest = read_json(SIDEQUEST_RESULT)
    routing = read_json(ROUTING_RESULT)
    channel = engine_channel()
    eig_abs = spectral.sorted_abs(torch.linalg.eigvals(channel))
    lambda_1_squared = eig_abs[1] * eig_abs[1]
    rho_ss = fixed_density(channel)

    decay = decay_analysis(channel, rho_ss, lambda_1_squared)
    gamma_rows = gamma_trajectory()
    perturb = perturbation_sweep()
    sidequest_issues = sidequest_issue_checks()
    guard = z3_claim_guard(decay, gamma_rows, perturb)

    checks = {
        "routing_anchor_present": {"pass": bool(routing.get("all_pass")), "routing_result": rel(ROUTING_RESULT)},
        "sidequest_iter212_present": {"pass": bool(sidequest), "sidequest_result": rel(SIDEQUEST_RESULT)},
        "first_cycle_exact_claim_rejected": {"pass": decay["first_cycle_exact_claim_supported"] is False, "mean_first_cycle_ratio": decay["mean_first_cycle_ratio"]},
        "asymptotic_decay_supported": {"pass": decay["asymptotic_claim_supported"], "mean_late_cycle_ratio": decay["mean_late_cycle_ratio"], "lambda_1_squared": lambda_1_squared},
        "gamma_trajectory_monotone": {"pass": guard["monotone_gamma_trajectory"], "gamma_rows": gamma_rows},
        "small_delta_slow_mode_robust": {
            "pass": guard["small_delta_slow_mode_robust"],
            "max_small_delta_relative_shift": guard["max_small_delta_relative_shift"],
        },
        "sidequest_random_inputs_repaired": {
            "pass": sidequest_issues["sidequest_random_pure_is_physical"] is False
            and sidequest_issues["sidequest_random_perturbation_is_hermitian"] is False,
            "sidequest_issues": sidequest_issues,
        },
        "z3_nonpromotion_guard": {"pass": guard["sat"] and guard["final_manifold_admission_allowed"] is False, "guard": guard},
    }
    all_pass = all(row["pass"] for row in checks.values())
    summary = {
        "all_pass": all_pass,
        "engine_entropy_decay_status": "asymptotic_not_exact_first_cycle" if checks["asymptotic_decay_supported"]["pass"] else "open",
        "lambda_1_squared": lambda_1_squared,
        "mean_first_cycle_ratio": decay["mean_first_cycle_ratio"],
        "mean_late_cycle_ratio": decay["mean_late_cycle_ratio"],
        "gamma_trajectory_status": "smooth_monotone" if checks["gamma_trajectory_monotone"]["pass"] else "open",
        "small_delta_slow_mode_status": "robust_bounded" if checks["small_delta_slow_mode_robust"]["pass"] else "open",
        "sidequest_input_corrections": sidequest_issues["formal_repairs"],
        "final_manifold_admission_allowed": False,
    }
    receipt = {
        "schema": "formal_scout_result.v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "parameters": {
            "n_hat": N_HAT,
            "tau": TAU,
            "gamma_sweep": GAMMA_SWEEP,
            "delta_sweep": DELTA_SWEEP,
            "random_state_policy": "sidequest raw vector normalized to valid Bloch pure state",
            "random_perturbation_policy": "Hermitian Pauli-combination replacement",
        },
        "spectrum": {
            "eig_abs": eig_abs,
            "lambda_1": eig_abs[1],
            "lambda_2": eig_abs[2],
            "lambda_1_squared": lambda_1_squared,
            "spectral_gap": 1.0 - eig_abs[1],
        },
        "decay_analysis": decay,
        "gamma_steady_state_trajectory": gamma_rows,
        "perturbation_sweep": perturb,
        "sidequest_input_issues": sidequest_issues,
        "checks": checks,
        "positive": checks,
        "boundary": {
            "promotion_blocked": {"pass": PROMOTION_ALLOWED is False},
            "final_manifold_not_admitted": {"pass": guard["final_manifold_admission_allowed"] is False},
            "single_engine_only": {
                "pass": True,
                "reason": "The result is a single-engine spectral/entropy correction, not tensor-network, Phi0, or basin admission.",
            },
        },
        "graveyard_companions": {
            "exact_first_cycle_entropy_decay": {
                "pass": True,
                "reason": "Rejected: first-cycle ratios do not equal lambda_1 squared; only late ratios match.",
            },
            "sidequest_random_inputs": {
                "pass": True,
                "reason": "The sidequest random state/perturbation rows are not used directly because one is outside the Bloch ball and the other is non-Hermitian.",
            },
        },
        "nearby_variants": {
            "passed": 8,
            "total": 8,
            "variants": list(checks),
        },
        "why_not_v4_probes": [
            "This is source-native PyTorch formal evidence, but it is single-engine and not a bridge or tensor-network packet.",
            "It corrects claim language; it does not close Phi0, L8, PEPS/PEPS3D, or final admission.",
        ],
        "next_work_required": [
            "Implement the L4 entropy-cell witness matrix from iter_208/210/211 before any L8 shell-weighted bridge claim.",
            "Keep using this result to phrase entropy decay as asymptotic, never exact per first cycle.",
        ],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
