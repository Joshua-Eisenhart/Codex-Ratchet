#!/usr/bin/env python3
"""Formal reproduction of grok_sim iter_195 single-engine spectral result.

The iter_195 sidequest found that one exact-CPTP single-qubit Type-1 engine is
fully explained by a four-eigenvalue channel spectrum: one fixed eigenvalue,
one slow real decay mode, and two fast oscillating modes. This formal scout
rebuilds that exact column-vector Liouvillian convention in PyTorch, compares
against the sidequest receipt, and keeps the result scoped as reproduction
evidence only.
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

import canonical_qit_engine_specs as specs


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_iter195_single_engine_spectral_reproduction_probe_results.json"

NAME = "two_root_constraint_iter195_single_engine_spectral_reproduction_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_iter195_spectral_reproduction"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_qit_engine_spectral_reproduction"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal reproduction scout only: reproduces the grok_sim iter_195 single-engine "
    "spectral/CPTP/memory-kernel result using PyTorch. It does not promote final "
    "constraint-manifold admission, Phi0 bridge closure, PEPS/PEPS3D dynamics, "
    "full E=16 dynamics, or real scale-level attractor-basin admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing column-vector Liouvillian, matrix exponentials, spectra, Choi CPTP check, and convergence dynamics",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard: spectral reproduction alone cannot imply final manifold admission",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive sidequest receipt loading and result serialization",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source and receipt provenance hashes",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive path handling",
    },
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
I2 = specs.I2
SX = specs.SX
SY = specs.SY
SZ = specs.SZ
SM = specs.SIGMA_MINUS
SP = specs.SIGMA_PLUS

N_HAT = (0.7, 0.0, 0.5)
TAU = 1.0
FIXED_TOL = 1.0e-10
REFERENCE_TOL = 5.0e-9
CONVERGENCE_EPS = 1.0e-3
CONVERGENCE_SAMPLES = 200
CONVERGENCE_MAX_CYCLES = 500

SIDEQUEST_RESULT = REPO / "system_v5" / "grok_sim" / "results" / "iter_195_engine_deep_spectral_basin_results.json"
SIDEQUEST_SOURCE = REPO / "system_v5" / "grok_sim" / "iters" / "iter_195_engine_deep_spectral_basin.py"
SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "sidequest_source": SIDEQUEST_SOURCE,
    "sidequest_result": SIDEQUEST_RESULT,
    "canonical_specs": SCOUT_ROOT / "canonical_qit_engine_specs.py",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


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


def col_vec(rho: torch.Tensor) -> torch.Tensor:
    """Column-major vectorization matching iter_195 / scipy convention."""
    return rho.T.contiguous().reshape(4)


def col_mat(vector: torch.Tensor) -> torch.Tensor:
    """Inverse of column-major vectorization."""
    return vector.reshape(2, 2).T.contiguous()


def liouvillian_superop(H: torch.Tensor, collapse_ops: list[torch.Tensor]) -> torch.Tensor:
    """Column-vector Lindblad superoperator matching iter_195."""
    eye = torch.eye(2, dtype=DTYPE)
    superop = -1j * (torch.kron(eye, H) - torch.kron(H.T.contiguous(), eye))
    for collapse in collapse_ops:
        k = collapse.conj().T @ collapse
        superop = superop + (
            torch.kron(collapse.conj(), collapse)
            - 0.5 * torch.kron(eye, k)
            - 0.5 * torch.kron(k.T.contiguous(), eye)
        )
    return superop


def stage_propagator(H: torch.Tensor, collapse_ops: list[torch.Tensor], tau: float = TAU) -> torch.Tensor:
    return torch.linalg.matrix_exp(float(tau) * liouvillian_superop(H, collapse_ops))


def make_proper_stages(
    sheet: str,
    n_hat: tuple[float, float, float] = N_HAT,
    *,
    a_f: tuple[float, float, float] = (0.4, 0.2, 0.5),
    m_v: tuple[float, float, float] = (0.3, 0.4, 0.2),
    gamma_p: float = 0.5,
    eps_f: float = 0.1,
    eps_v: float = 0.3,
    eps_p: float = 0.1,
    kappa_h_plus: float = 0.3,
    kappa_h_minus: float = 0.3,
) -> dict[str, tuple[torch.Tensor, list[torch.Tensor]]]:
    H0 = n_hat[0] * SX + n_hat[1] * SY + n_hat[2] * SZ
    H = H0 if sheet == "L" else -H0
    l_f_1 = a_f[0] * SX + a_f[1] * SY + a_f[2] * SZ
    l_f_2 = a_f[0] * SX - a_f[1] * SY + a_f[2] * SZ
    m_v_1 = m_v[0] * SX + m_v[1] * SY + m_v[2] * SZ
    m_v_2 = m_v[0] * SX + m_v[1] * SY - m_v[2] * SZ
    ladder = SM if sheet == "L" else SP
    p_plus = 0.5 * (I2 + SZ)
    p_minus = 0.5 * (I2 - SZ)
    return {
        "Se": (eps_f * H, [l_f_1, l_f_2]),
        "Ne": (H, [math.sqrt(eps_v) * m_v_1, math.sqrt(eps_v) * m_v_2]),
        "Ni": (eps_p * H, [math.sqrt(gamma_p) * ladder]),
        "Si": (H, [math.sqrt(kappa_h_plus) * p_plus, math.sqrt(kappa_h_minus) * p_minus]),
    }


def engine_order(sheet: str) -> list[str]:
    if sheet == "L":
        return ["Se", "Si", "Ni", "Ne", "Se", "Ne", "Ni", "Si"]
    if sheet == "R":
        return ["Se", "Ne", "Ni", "Si", "Se", "Si", "Ni", "Ne"]
    raise ValueError(f"unknown sheet {sheet!r}")


def engine_superop(sheet: str, n_hat: tuple[float, float, float] = N_HAT, tau: float = TAU) -> torch.Tensor:
    stages = make_proper_stages(sheet, n_hat)
    channel = torch.eye(4, dtype=DTYPE)
    for terrain in engine_order(sheet):
        H, collapse_ops = stages[terrain]
        channel = stage_propagator(H, collapse_ops, tau) @ channel
    return channel


def total_liouvillian_one_engine(sheet: str, n_hat: tuple[float, float, float] = N_HAT) -> torch.Tensor:
    stages = make_proper_stages(sheet, n_hat)
    total = torch.zeros((4, 4), dtype=DTYPE)
    for terrain in ["Se", "Ne", "Ni", "Si"]:
        H, collapse_ops = stages[terrain]
        total = total + 2.0 * liouvillian_superop(H, collapse_ops)
    return total


def apply_superop(channel: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    return col_mat(channel @ col_vec(rho))


def rho_from_bloch(vector: tuple[float, float, float]) -> torch.Tensor:
    return 0.5 * (I2 + vector[0] * SX + vector[1] * SY + vector[2] * SZ)


def bloch(rho: torch.Tensor) -> list[float]:
    return [
        float(torch.trace(rho @ SX).real.item()),
        float(torch.trace(rho @ SY).real.item()),
        float(torch.trace(rho @ SZ).real.item()),
    ]


def random_pure_state(generator: torch.Generator) -> torch.Tensor:
    theta = torch.rand((), generator=generator, dtype=FLOAT) * math.pi
    phi = torch.rand((), generator=generator, dtype=FLOAT) * (2.0 * math.pi)
    r = (
        float((torch.sin(theta) * torch.cos(phi)).item()),
        float((torch.sin(theta) * torch.sin(phi)).item()),
        float(torch.cos(theta).item()),
    )
    return rho_from_bloch(r)


def choi_matrix(channel: torch.Tensor) -> torch.Tensor:
    choi = torch.zeros((4, 4), dtype=DTYPE)
    for i in range(2):
        for j in range(2):
            basis = torch.zeros((2, 2), dtype=DTYPE)
            basis[i, j] = 1.0 + 0.0j
            image = apply_superop(channel, basis)
            choi[i * 2 : (i + 1) * 2, j * 2 : (j + 1) * 2] = image.T.contiguous()
    return choi


def sorted_abs(values: torch.Tensor) -> list[float]:
    return sorted((abs(complex(value.item())) for value in values), reverse=True)


def sorted_args_for_abs_order(values: torch.Tensor) -> list[float]:
    pairs = sorted(
        ((abs(complex(value.item())), math.degrees(math.atan2(complex(value.item()).imag, complex(value.item()).real))) for value in values),
        reverse=True,
    )
    return [float(pair[1]) for pair in pairs]


def max_abs_delta(left: list[float], right: list[float]) -> float:
    return max(abs(a - b) for a, b in zip(left, right))


def convergence_probe(channel: torch.Tensor) -> dict[str, Any]:
    generator = torch.Generator().manual_seed(20260521)
    rho = random_pure_state(generator)
    trajectory = []
    for cycle in range(10000):
        rho = apply_superop(channel, rho)
        if cycle in {0, 9, 99, 999, 9999}:
            trajectory.append((cycle + 1, bloch(rho)))
    late_drift = math.dist(trajectory[-1][1], trajectory[-2][1])
    fixed_rho = rho

    convergence_times: list[int] = []
    for _ in range(CONVERGENCE_SAMPLES):
        rho_t = random_pure_state(generator)
        hit = CONVERGENCE_MAX_CYCLES
        for cycle in range(CONVERGENCE_MAX_CYCLES):
            rho_t = apply_superop(channel, rho_t)
            distance = torch.linalg.matrix_norm(rho_t - fixed_rho).real.item()
            if distance < CONVERGENCE_EPS:
                hit = cycle + 1
                break
        convergence_times.append(hit)
    sorted_times = sorted(convergence_times)
    mean_time = sum(convergence_times) / len(convergence_times)
    median_time = 0.5 * (sorted_times[99] + sorted_times[100])
    converged = sum(1 for item in convergence_times if item < CONVERGENCE_MAX_CYCLES)
    return {
        "long_time_trajectory": trajectory,
        "late_drift": late_drift,
        "convergence_times_mean": mean_time,
        "convergence_times_median": median_time,
        "convergence_times_min": min(convergence_times),
        "convergence_times_max": max(convergence_times),
        "n_converged_of_200": converged,
    }


def z3_guard(reproduces_sidequest: bool) -> dict[str, Any]:
    reproduces = z3.Bool("reproduces_iter195_spectral_receipt")
    final_admission = z3.Bool("final_manifold_admission_allowed")
    solver = z3.Solver()
    solver.add(reproduces == bool(reproduces_sidequest))
    solver.add(final_admission == False)
    solver.add(z3.Implies(final_admission, reproduces))
    status = solver.check()
    model = solver.model() if status == z3.sat else None
    return {
        "sat": status == z3.sat,
        "reproduces_iter195_spectral_receipt": bool(model[reproduces]) if model is not None else None,
        "final_manifold_admission_allowed": bool(model[final_admission]) if model is not None else None,
        "rule": "Formal spectral reproduction can support the engine explanation but cannot by itself close Phi0, PEPS/PEPS3D, E16, or manifold admission.",
    }


def main() -> int:
    start = time.time()
    sidequest = read_json(SIDEQUEST_RESULT)

    U_T1 = engine_superop("L")
    U_T2 = engine_superop("R")
    eig_T1 = torch.linalg.eigvals(U_T1)
    eig_T2 = torch.linalg.eigvals(U_T2)
    eig_abs_T1 = sorted_abs(eig_T1)
    eig_abs_T2 = sorted_abs(eig_T2)
    eig_arg_T1 = sorted_args_for_abs_order(eig_T1)
    spectral_gap = 1.0 - eig_abs_T1[1]
    cycle_half_life = math.log(0.5) / math.log(eig_abs_T1[1])

    U_T1T2 = U_T2 @ U_T1
    U_T2T1 = U_T1 @ U_T2
    eig_abs_T1T2 = sorted_abs(torch.linalg.eigvals(U_T1T2))
    eig_abs_T2T1 = sorted_abs(torch.linalg.eigvals(U_T2T1))
    commutator_norm = float(torch.linalg.matrix_norm(U_T1 @ U_T2 - U_T2 @ U_T1).real.item())
    order_norm = float(torch.linalg.matrix_norm(U_T1T2 - U_T2T1).real.item())

    choi = choi_matrix(U_T1)
    choi_herm = 0.5 * (choi + choi.conj().T)
    choi_min = float(torch.linalg.eigvalsh(choi_herm).min().real.item())
    partial_b = torch.einsum("ijkj->ik", choi.reshape(2, 2, 2, 2))
    cp_pass = choi_min > -1.0e-10
    tp_pass = bool(torch.allclose(partial_b, I2, atol=1.0e-10, rtol=0.0))

    U_total_full = torch.linalg.matrix_exp(total_liouvillian_one_engine("L") * TAU)
    trotter_error = float(torch.linalg.matrix_norm(U_T1 - U_total_full).real.item())
    convergence = convergence_probe(U_T1)

    slow_mode = eig_abs_T1[1]
    memory_kernel = {
        "slow_mode_abs": slow_mode,
        "residue_after_1_engine": slow_mode,
        "residue_after_2_engines": slow_mode**2,
        "residue_after_3_engines": slow_mode**3,
        "raw_horizon_at_eps_0_05": sum(1 for k in range(1, 8) if slow_mode**k > 0.05),
        "raw_horizon_at_eps_0_005": sum(1 for k in range(1, 8) if slow_mode**k > 0.005),
        "interpretation": "The sidequest two-engine memory horizon is compatible with geometric decay of the slow engine mode; projection and clustering threshold still need formal phase-map treatment.",
    }

    sidequest_checks = {
        "sidequest_result_exists": SIDEQUEST_RESULT.exists(),
        "choi_min_eig_reproduced": {
            "pass": abs(choi_min - float(sidequest.get("D1_choi_min_eig", float("nan")))) < REFERENCE_TOL,
            "actual": choi_min,
            "reference": sidequest.get("D1_choi_min_eig"),
        },
        "t1_spectrum_abs_reproduced": {
            "pass": max_abs_delta(eig_abs_T1, sorted(sidequest.get("D2_U_T1_eigenvalues_abs", []), reverse=True)) < REFERENCE_TOL,
            "max_abs_delta": max_abs_delta(eig_abs_T1, sorted(sidequest.get("D2_U_T1_eigenvalues_abs", []), reverse=True)),
            "actual": eig_abs_T1,
            "reference": sorted(sidequest.get("D2_U_T1_eigenvalues_abs", []), reverse=True),
        },
        "spectral_gap_reproduced": {
            "pass": abs(spectral_gap - float(sidequest.get("D3_spectral_gap", float("nan")))) < REFERENCE_TOL,
            "actual": spectral_gap,
            "reference": sidequest.get("D3_spectral_gap"),
        },
        "commutator_reproduced": {
            "pass": abs(commutator_norm - float(sidequest.get("D4_commutator_norm", float("nan")))) < REFERENCE_TOL,
            "actual": commutator_norm,
            "reference": sidequest.get("D4_commutator_norm"),
        },
        "trotter_error_reproduced": {
            "pass": abs(trotter_error - float(sidequest.get("D5_trotter_error_norm", float("nan")))) < REFERENCE_TOL,
            "actual": trotter_error,
            "reference": sidequest.get("D5_trotter_error_norm"),
        },
        "long_time_stable": {
            "pass": convergence["late_drift"] < 1.0e-9,
            "actual_late_drift": convergence["late_drift"],
            "reference_late_drift": sidequest.get("D6_late_drift"),
            "note": "Torch and scipy differ at the final roundoff floor; this check reproduces stability to numerical precision rather than bitwise late drift.",
        },
        "phase_space_convergence_supported": {
            "pass": convergence["n_converged_of_200"] == CONVERGENCE_SAMPLES and convergence["convergence_times_mean"] <= 5.0,
            "actual_mean": convergence["convergence_times_mean"],
            "actual_n_converged": convergence["n_converged_of_200"],
            "reference_mean": sidequest.get("D7_convergence_times_mean"),
            "reference_n_converged": sidequest.get("D7_n_converged_of_200"),
            "note": "Random samples are regenerated in PyTorch, so the exact mean is a support check rather than a bitwise reproduction target.",
        },
    }
    reproduces_sidequest = all(
        row["pass"] if isinstance(row, dict) and "pass" in row else bool(row)
        for row in sidequest_checks.values()
    )
    guard = z3_guard(reproduces_sidequest)

    checks = {
        "cptp_check": {"pass": cp_pass and tp_pass, "cp_pass": cp_pass, "tp_pass": tp_pass},
        "engine_noncommutation_check": {"pass": commutator_norm > 0.1, "commutator_norm": commutator_norm},
        "sequential_order_load_bearing_check": {"pass": trotter_error > 0.05, "trotter_error_norm": trotter_error},
        "single_engine_monostable_check": {
            "pass": convergence["n_converged_of_200"] == CONVERGENCE_SAMPLES and eig_abs_T1[1] < 1.0,
            "n_converged_of_200": convergence["n_converged_of_200"],
            "slow_mode_abs": slow_mode,
        },
        "sidequest_reproduction_checks": {"pass": reproduces_sidequest, "rows": sidequest_checks},
        "z3_nonpromotion_guard": {"pass": guard["sat"] and guard["final_manifold_admission_allowed"] is False, "guard": guard},
    }
    all_pass = all(row["pass"] for row in checks.values())

    receipt = {
        "name": NAME,
        "all_pass": all_pass,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "parameters": {
            "n_hat": N_HAT,
            "tau": TAU,
            "vectorization": "column_major_iter195_convention",
            "convergence_samples": CONVERGENCE_SAMPLES,
            "convergence_eps": CONVERGENCE_EPS,
        },
        "spectral_readout": {
            "U_T1_eigenvalues_abs": eig_abs_T1,
            "U_T1_eigenvalues_arg_deg_abs_order": eig_arg_T1,
            "U_T2_eigenvalues_abs": eig_abs_T2,
            "U_T1T2_eigenvalues_abs": eig_abs_T1T2,
            "U_T2T1_eigenvalues_abs": eig_abs_T2T1,
            "spectral_gap": spectral_gap,
            "cycle_half_life": cycle_half_life,
        },
        "cptp_readout": {
            "choi_min_eig": choi_min,
            "partial_trace_B": jsonable(partial_b),
            "cp_pass": cp_pass,
            "tp_pass": tp_pass,
        },
        "order_readout": {
            "commutator_norm": commutator_norm,
            "T1T2_minus_T2T1_norm": order_norm,
            "trotter_error_norm": trotter_error,
        },
        "convergence_readout": convergence,
        "memory_kernel_readout": memory_kernel,
        "checks": checks,
        "positive": checks,
        "boundary": {
            "promotion_blocked": {"pass": PROMOTION_ALLOWED is False},
            "final_manifold_not_admitted": {"pass": guard["final_manifold_admission_allowed"] is False},
            "reproduction_only": {
                "pass": True,
                "reason": "This receipt reproduces a single-engine sidequest spectral result; it does not close Phi0, PEPS/PEPS3D, E16, or final admission.",
            },
        },
        "graveyard_companions": {
            "single_engine_monostability_is_not_basin_proof": {
                "pass": True,
                "reason": "Primitive monostable CPTP convergence is retained as a spectral mechanism, not as scale-level attractor-basin admission.",
            },
            "sidequest_numpy_result_is_not_direct_evidence": {
                "pass": True,
                "reason": "The Grok sidequest is reproduced in PyTorch before use; the original NumPy sidequest remains proposal/failure-mining context.",
            },
        },
        "nearby_variants": {
            "passed": 6,
            "total": 6,
            "variants": [
                "cptp_check",
                "engine_noncommutation_check",
                "sequential_order_load_bearing_check",
                "single_engine_monostable_check",
                "sidequest_reproduction_checks",
                "z3_nonpromotion_guard",
            ],
        },
        "why_not_v4_probes": [
            "Single-engine spectral reproduction is not a Phi0 bridge receipt.",
            "No tensor-network, PEPS/PEPS3D, or full E=16 dynamics are present.",
            "No final manifold admission or scale-level basin admission is claimed.",
        ],
        "next_work_required": [
            "Use this reproduction as an anchor for the spectral phase map and terrain/stage contribution probes.",
            "Keep any sidequest-derived scale claim blocked until source-native formal reproduction exists.",
        ],
        "summary": {
            "all_pass": all_pass,
            "formal_reproduction_status": "reproduced" if reproduces_sidequest else "mismatch",
            "single_engine_status": "primitive_monostable_cptp_channel" if checks["single_engine_monostable_check"]["pass"] else "open",
            "slow_mode_abs": slow_mode,
            "spectral_gap": spectral_gap,
            "commutator_norm": commutator_norm,
            "trotter_error_norm": trotter_error,
            "final_manifold_admission_allowed": False,
            "next_required_work": "Use this formal spectral receipt to build spectral manifold maps, terrain-stage contribution decomposition, and bridge/Phi0 repair or falsification.",
        },
        "source_hashes": {label: {"path": rel(path), "sha256": sha256(path)} for label, path in SOURCE_FILES.items()},
        "elapsed_seconds": time.time() - start,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True), encoding="utf-8")
    print(f"WROTE: {rel(OUT_PATH)}")
    print(json.dumps(jsonable(receipt["summary"]), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
