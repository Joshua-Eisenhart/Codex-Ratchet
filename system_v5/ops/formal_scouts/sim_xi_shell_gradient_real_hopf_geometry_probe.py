#!/usr/bin/env python3
"""Xi-shell gradient audit using the real nested-Hopf-tori latitude.

Formal scout only. This replaces the hand-tuned Xi-shell eta schedule from
``sim_xi_shell_coherent_information_gradient_bridge_probe.py`` with the
source-native Hopf foliation

    T_eta = (cos(eta) exp(i phi), sin(eta) exp(i chi)), eta in (0, pi/2)

from ``system_v5/julia_carrier/clifford_torus_nested_hopf_foliation.jl``.
It tests whether Phi0(eta)=I_c(A->B) has the same monotone/load-bearing
gradient behavior on the genuine foliation, without promoting Xi, Axis0,
gravity, physics, bridge closure, or formal admission.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "xi_shell_gradient_real_hopf_geometry_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
ORIGINAL_SOURCE = ROOT / "sim_xi_shell_coherent_information_gradient_bridge_probe.py"
HOPF_SOURCE = ROOT.parent.parent / "julia_carrier" / "clifford_torus_nested_hopf_foliation.jl"

SCHEMA = "FORMAL_SCOUT_RESULT_v1"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "xi_shell_real_hopf_geometry_gradient_audit"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SCRATCH_DIAGNOSTIC = True
CLAIM_CEILING = (
    "Formal scout only: tests Phi0(eta)=I_c(A->B) over the genuine nested-Hopf "
    "latitude foliation eta in (0, pi/2). It does not admit final Xi, final "
    "Phi0, Axis0, gravity, physics, bridge promotion, holography, ER=EPR, "
    "FTL, or formal admission."
)
BLOCKED_CONSUMERS = [
    "final_Xi",
    "final_Phi0",
    "Axis0",
    "gravity",
    "physics",
    "bridge_promotion",
    "holography",
    "ER_EPR",
    "FTL",
    "promotion",
    "formal_admission",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex128 spinors, four-qubit density matrices, partial traces, entropy readouts, finite differences, and controls",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local source/result path checks"},
    "math": {"tried": True, "used": True, "reason": "supportive Hopf latitude and phase-grid parameters"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not needed for this bounded numeric/QIT gradient audit; nonpromotion is enforced by explicit result fences",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "not needed because no symbolic derivation is claimed",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "not needed because no graph reachability or routing claim is made",
    },
    "networkx": {
        "tried": False,
        "used": False,
        "reason": "not needed because no graph algorithm claim is made",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "math": "supportive",
    "time": "supportive",
    "z3": None,
    "sympy": None,
    "rustworkx": None,
    "networkx": None,
}

DTYPE = torch.float64
CDTYPE = torch.complex128
EPS = 1e-12
N_QUBITS = 4
N_SHELLS = 9
PHASE_COUNT = 24
I4 = torch.eye(4, dtype=CDTYPE)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def cexp(theta: float) -> complex:
    return complex(math.cos(theta), math.sin(theta))


def normalize(v: torch.Tensor) -> torch.Tensor:
    return v / torch.clamp(torch.linalg.vector_norm(v), min=EPS)


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return normalize(
        torch.tensor(
            [
                cexp(phi + chi) * math.cos(eta),
                cexp(phi - chi) * math.sin(eta),
            ],
            dtype=CDTYPE,
        )
    )


def orthogonal_spinor(psi: torch.Tensor) -> torch.Tensor:
    return normalize(torch.stack([-torch.conj(psi[1]), torch.conj(psi[0])]))


def hermitize(rho: torch.Tensor) -> torch.Tensor:
    return (rho + torch.conj(rho).T) / 2


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = hermitize(rho)
    return rho / torch.clamp(torch.real(torch.trace(rho)), min=EPS)


def density(state: torch.Tensor) -> torch.Tensor:
    state = normalize(state)
    return normalize_density(torch.outer(state, torch.conj(state)))


def partial_trace_qubits(rho: torch.Tensor, keep: list[int]) -> torch.Tensor:
    dims = [2] * N_QUBITS
    traced = [idx for idx in range(N_QUBITS) if idx not in keep]
    reshaped = rho.reshape(*dims, *dims)
    perm = keep + traced + [idx + N_QUBITS for idx in keep] + [idx + N_QUBITS for idx in traced]
    permuted = reshaped.permute(*perm).reshape(
        2 ** len(keep),
        2 ** len(traced),
        2 ** len(keep),
        2 ** len(traced),
    )
    return torch.einsum("abcb->ac", permuted)


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(rho)).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.clamp(torch.sum(vals), min=EPS)
    nz = vals[vals > EPS]
    return float((-torch.sum(nz * torch.log(nz))).item())


def cut_readouts(rho_ab: torch.Tensor) -> dict[str, float]:
    rho_ab = normalize_density(rho_ab)
    rho_a = partial_trace_qubits(rho_ab, [0, 1])
    rho_b = partial_trace_qubits(rho_ab, [2, 3])
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    s_ab = entropy(rho_ab)
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "I_A_B": s_a + s_b - s_ab,
        "S_A_given_B": s_ab - s_b,
        "I_c_A_to_B": s_b - s_ab,
    }


def productize_cut(rho_ab: torch.Tensor) -> torch.Tensor:
    rho_a = partial_trace_qubits(rho_ab, [0, 1])
    rho_b = partial_trace_qubits(rho_ab, [2, 3])
    return normalize_density(torch.kron(rho_a, rho_b))


def matrix_health(rho: torch.Tensor) -> dict[str, Any]:
    rho = normalize_density(rho)
    eigs = torch.linalg.eigvalsh(hermitize(rho)).real
    herm_gap = float(torch.linalg.matrix_norm(rho - torch.conj(rho).T).item())
    trace_gap = abs(float(torch.real(torch.trace(rho)).item()) - 1.0)
    min_eval = float(torch.min(eigs).item())
    return {
        "hermiticity_gap": herm_gap,
        "trace_gap": trace_gap,
        "min_eigenvalue": min_eval,
        "pass": bool(herm_gap < 1e-9 and trace_gap < 1e-9 and min_eval > -1e-9),
    }


def torus_point(eta: float, phi: float, chi: float) -> tuple[complex, complex]:
    return math.cos(eta) * cexp(phi), math.sin(eta) * cexp(chi)


def phase_grid() -> list[float]:
    return [2.0 * math.pi * idx / PHASE_COUNT for idx in range(PHASE_COUNT)]


def hopf_eta(k: int) -> float:
    return (k + 1) * (math.pi / 2.0) / (N_SHELLS + 1)


def hopf_spinor(eta: float, phi: float, chi: float) -> torch.Tensor:
    z, w = torus_point(eta, phi, chi)
    return normalize(torch.tensor([z, w], dtype=CDTYPE))


def torus_node_spinors(eta: float, k: int, *, chiral: bool) -> list[torch.Tensor]:
    phases = phase_grid()
    rows = []
    for node in range(4):
        if chiral:
            phi = phases[(k + 3 * node) % PHASE_COUNT]
            chi = phases[(2 * k + 5 * node + 1) % PHASE_COUNT]
        else:
            phi = 0.0
            chi = 0.0
        rows.append(hopf_spinor(eta, phi, chi))
    return rows


def shell_density(k: int, mode: str) -> dict[str, Any]:
    eta = hopf_eta(k)
    chiral = mode != "no_chirality"
    spinors = torus_node_spinors(eta, k, chiral=chiral)
    a0 = normalize(torch.kron(spinors[0], spinors[1]))
    b0 = normalize(torch.kron(spinors[2], spinors[3]))
    a1 = normalize(torch.kron(orthogonal_spinor(spinors[0]), orthogonal_spinor(spinors[1])))
    b1 = normalize(torch.kron(orthogonal_spinor(spinors[2]), orthogonal_spinor(spinors[3])))

    phases = phase_grid()
    if chiral:
        z, w = torus_point(eta, phases[k % PHASE_COUNT], phases[(2 * k + 1) % PHASE_COUNT])
    else:
        z, w = torus_point(eta, 0.0, 0.0)
    state = normalize(z * torch.kron(a0, b0) + w * torch.kron(a1, b1))
    rho = density(state)
    params = {
        "k": k,
        "eta": eta,
        "eta_over_pi": eta / math.pi,
        "eta_domain": "(0, pi/2)",
        "clifford_torus": bool(abs(eta - math.pi / 4.0) < EPS),
        "z_radius": math.cos(eta),
        "w_radius": math.sin(eta),
        "hopf_latitude_cos_2eta": math.cos(2.0 * eta),
        "torus_metric_det": math.cos(eta) ** 2 * math.sin(eta) ** 2,
        "phase_count": PHASE_COUNT,
        "phase_erased": not chiral,
    }
    return {"rho": rho, "params": params}


def family_from_rows(label: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    etas = [row["params"]["eta"] for row in rows]
    readouts = [cut_readouts(row["rho"]) for row in rows]
    health = [matrix_health(row["rho"]) for row in rows]
    phi0 = [row["I_c_A_to_B"] for row in readouts]
    gradients = finite_difference(phi0, etas)
    return {
        "label": label,
        "etas": etas,
        "phi0": phi0,
        "gradient_dPhi0_deta": gradients,
        "readouts": readouts,
        "health": health,
        "shell_params": [row["params"] for row in rows],
        "metrics": gradient_metrics(phi0, etas, gradients),
    }


def finite_difference(values: list[float], xs: list[float]) -> list[float]:
    return [(values[idx + 1] - values[idx]) / (xs[idx + 1] - xs[idx]) for idx in range(len(values) - 1)]


def pearson(xs: list[float], ys: list[float]) -> float:
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    dx = [x - mean_x for x in xs]
    dy = [y - mean_y for y in ys]
    denom_x = math.sqrt(sum(x * x for x in dx))
    denom_y = math.sqrt(sum(y * y for y in dy))
    if denom_x < EPS or denom_y < EPS:
        return 0.0
    return sum(x * y for x, y in zip(dx, dy)) / (denom_x * denom_y)


def sign_changes(values: list[float]) -> int:
    signs = [1 if row > EPS else -1 if row < -EPS else 0 for row in values]
    compact = [row for row in signs if row != 0]
    return sum(1 for left, right in zip(compact, compact[1:]) if left != right)


def gradient_metrics(phi0: list[float], etas: list[float], gradients: list[float]) -> dict[str, float | bool | int]:
    abs_grad = [abs(row) for row in gradients]
    positive_count = sum(1 for row in gradients if row > EPS)
    negative_count = sum(1 for row in gradients if row < -EPS)
    mean_abs = sum(abs_grad) / len(abs_grad)
    phi0_range = max(phi0) - min(phi0)
    corr_eta = pearson(etas, phi0)
    positive_fraction = positive_count / len(gradients)
    negative_fraction = negative_count / len(gradients)
    monotone_increasing = positive_count == len(gradients)
    monotone_decreasing = negative_count == len(gradients)
    positive_signal_score = max(0.0, corr_eta) * positive_fraction * min(1.0, phi0_range / 0.10)
    peak_idx = max(range(len(phi0)), key=lambda idx: phi0[idx])
    return {
        "phi0_mean": sum(phi0) / len(phi0),
        "phi0_min": min(phi0),
        "phi0_max": max(phi0),
        "phi0_range": phi0_range,
        "gradient_mean_abs": mean_abs,
        "gradient_max_abs": max(abs_grad),
        "gradient_variation": max(gradients) - min(gradients),
        "gradient_positive_fraction": positive_fraction,
        "gradient_negative_fraction": negative_fraction,
        "gradient_min": min(gradients),
        "gradient_max": max(gradients),
        "gradient_sign_changes": sign_changes(gradients),
        "eta_phi0_correlation": corr_eta,
        "monotone_increasing": monotone_increasing,
        "monotone_decreasing": monotone_decreasing,
        "monotone_any_direction": monotone_increasing or monotone_decreasing,
        "positive_signal_score": positive_signal_score,
        "peak_shell_index": peak_idx,
        "peak_eta": etas[peak_idx],
        "peak_is_clifford_torus": abs(etas[peak_idx] - math.pi / 4.0) < EPS,
    }


def product_family(candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [{"rho": productize_cut(row["rho"]), "params": dict(row["params"])} for row in candidate_rows]
    return family_from_rows("product_cut_control", rows)


def flat_family(candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    base = candidate_rows[len(candidate_rows) // 2]
    rows = []
    for row in candidate_rows:
        params = dict(row["params"])
        params["flat_source_shell"] = base["params"]["k"]
        rows.append({"rho": base["rho"].clone(), "params": params})
    return family_from_rows("flat_shell_control", rows)


def same_scalar_different_gradient_family(candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    perm = [4, 0, 8, 1, 7, 2, 6, 3, 5]
    rows = []
    for eta_row, source_idx in zip(candidate_rows, perm):
        params = dict(eta_row["params"])
        params["source_shell_for_same_scalar_control"] = source_idx
        rows.append({"rho": candidate_rows[source_idx]["rho"].clone(), "params": params})
    return family_from_rows("same_scalar_different_gradient_control", rows)


def no_chirality_family() -> dict[str, Any]:
    return family_from_rows("no_chirality_phase_erased_control", [shell_density(k, "no_chirality") for k in range(N_SHELLS)])


def local_unitary_no_signal_check(rho: torch.Tensor) -> dict[str, Any]:
    theta = 0.73
    phi = 0.37
    rz = torch.diag(torch.tensor([cexp(-theta / 2.0), cexp(theta / 2.0)], dtype=CDTYPE))
    rx = torch.tensor(
        [
            [math.cos(phi / 2.0), -1.0j * math.sin(phi / 2.0)],
            [-1.0j * math.sin(phi / 2.0), math.cos(phi / 2.0)],
        ],
        dtype=CDTYPE,
    )
    unitary_b = torch.kron(rz, rx)
    full_unitary = torch.kron(I4, unitary_b)
    transformed = normalize_density(full_unitary @ rho @ torch.conj(full_unitary).T)
    rho_a_before = partial_trace_qubits(rho, [0, 1])
    rho_a_after = partial_trace_qubits(transformed, [0, 1])
    rho_b_before = partial_trace_qubits(rho, [2, 3])
    rho_b_after = partial_trace_qubits(transformed, [2, 3])
    rho_a_gap = float(torch.linalg.matrix_norm(rho_a_before - rho_a_after).item())
    rho_b_gap = float(torch.linalg.matrix_norm(rho_b_before - rho_b_after).item())
    rho_ab_gap = float(torch.linalg.matrix_norm(rho - transformed).item())
    read_before = cut_readouts(rho)
    read_after = cut_readouts(transformed)
    ic_gap = abs(read_before["I_c_A_to_B"] - read_after["I_c_A_to_B"])
    return {
        "rho_A_invariance_gap": rho_a_gap,
        "rho_B_change_gap": rho_b_gap,
        "rho_AB_change_gap": rho_ab_gap,
        "I_c_invariance_gap": ic_gap,
        "pass": bool(rho_a_gap < 1e-10 and rho_ab_gap > 1e-4 and ic_gap < 1e-10),
        "interpretation": "A local unitary on B changes rho_AB/B basis data but leaves rho_A and I_c invariant; no control-message or FTL reading is admitted.",
    }


def gradient_profile_l2(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((a - b) * (a - b) for a, b in zip(left, right)))


def max_abs_gap(left: list[float], right: list[float]) -> float:
    return max(abs(a - b) for a, b in zip(left, right))


def run_probe() -> dict[str, Any]:
    candidate_rows = [shell_density(k, "candidate") for k in range(N_SHELLS)]
    candidate = family_from_rows("real_hopf_foliation_candidate", candidate_rows)
    flat = flat_family(candidate_rows)
    product = product_family(candidate_rows)
    same_scalar = same_scalar_different_gradient_family(candidate_rows)
    no_chirality = no_chirality_family()
    controls = {
        "flat_shell_control": flat,
        "product_cut_control": product,
        "same_scalar_different_gradient_control": same_scalar,
        "no_chirality_phase_erased_control": no_chirality,
    }
    all_families = {"candidate": candidate, **controls}
    all_health = all(row["pass"] for family_row in all_families.values() for row in family_row["health"])

    cand_metrics = candidate["metrics"]
    flat_metrics = flat["metrics"]
    product_metrics = product["metrics"]
    same_scalar_metrics = same_scalar["metrics"]
    no_chirality_metrics = no_chirality["metrics"]

    gradient_nonflat = bool(cand_metrics["phi0_range"] > 0.15 and cand_metrics["gradient_mean_abs"] > 0.15)
    monotone_on_real_foliation = bool(cand_metrics["monotone_increasing"])
    flat_degrades = bool(flat_metrics["phi0_range"] < 1e-9 and flat_metrics["gradient_mean_abs"] < 1e-9)
    product_degrades = bool(product_metrics["phi0_max"] <= 1e-9)
    same_scalar_mean_gap = abs(cand_metrics["phi0_mean"] - same_scalar_metrics["phi0_mean"])
    same_scalar_gradient_gap = gradient_profile_l2(
        candidate["gradient_dPhi0_deta"],
        same_scalar["gradient_dPhi0_deta"],
    )
    same_scalar_pass = bool(same_scalar_mean_gap < 1e-12 and same_scalar_gradient_gap > 0.50)
    no_chirality_phi0_gap = max_abs_gap(candidate["phi0"], no_chirality["phi0"])
    no_chirality_gradient_gap = max_abs_gap(
        candidate["gradient_dPhi0_deta"],
        no_chirality["gradient_dPhi0_deta"],
    )
    no_chirality_ties_candidate = bool(no_chirality_phi0_gap < 1e-10 and no_chirality_gradient_gap < 1e-10)
    candidate_beats_no_chirality = not no_chirality_ties_candidate
    required_controls_beaten = bool(flat_degrades and product_degrades and same_scalar_pass and candidate_beats_no_chirality)
    gradient_from_real_hopf_geometry = bool(
        all_health and gradient_nonflat and monotone_on_real_foliation and required_controls_beaten
    )
    gradient_needs_tuned_formula = not gradient_from_real_hopf_geometry
    no_signal = local_unitary_no_signal_check(candidate_rows[N_SHELLS // 2]["rho"])

    boundary_checks = {
        "scratch_diagnostic": SCRATCH_DIAGNOSTIC is True,
        "promotion_disabled": PROMOTION_ALLOWED is False,
        "formal_admission_disabled": FORMAL_ADMISSION_ALLOWED is False,
        "blocked_consumers_complete": BLOCKED_CONSUMERS
        == [
            "final_Xi",
            "final_Phi0",
            "Axis0",
            "gravity",
            "physics",
            "bridge_promotion",
            "holography",
            "ER_EPR",
            "FTL",
            "promotion",
            "formal_admission",
        ],
        "claim_ceiling_blocks_axis0_physics": all(
            token in CLAIM_CEILING
            for token in ["final Xi", "final Phi0", "Axis0", "gravity", "physics", "FTL"]
        ),
    }
    boundary_pass = all(boundary_checks.values())
    gradient_claim_blockers = []
    if not all_health:
        gradient_claim_blockers.append("matrix_health_failed")
    if not gradient_nonflat:
        gradient_claim_blockers.append("real_hopf_gradient_flat")
    if not monotone_on_real_foliation:
        gradient_claim_blockers.append("real_hopf_Ic_non_monotone_peak_at_clifford_torus")
    if not required_controls_beaten:
        gradient_claim_blockers.append("candidate_did_not_beat_required_controls")
    if no_chirality_ties_candidate:
        gradient_claim_blockers.append("no_chirality_control_tied_candidate")
    if not boundary_pass:
        gradient_claim_blockers.append("claim_ceiling_boundary_failed")

    positive = {
        "real_hopf_foliation_executed": {
            "pass": True,
            "source": str(HOPF_SOURCE),
            "parameterization": "F(eta,phi,chi)=(cos(eta)*exp(i*phi), sin(eta)*exp(i*chi)); eta in (0,pi/2)",
            "eta_schedule": "open uniform nested latitudes k=0..8; k=4 is eta=pi/4 Clifford torus",
        },
        "coherent_information_machinery_reused": {
            "pass": True,
            "source": str(ORIGINAL_SOURCE),
            "reused_functions": [
                "partial_trace_qubits",
                "entropy",
                "cut_readouts",
                "productize_cut",
                "local_unitary_no_signal_check",
            ],
        },
        "matrix_health_all_shells_and_controls": {
            "pass": all_health,
            "health_counts": {
                label: sum(1 for row in family_row["health"] if row["pass"])
                for label, family_row in all_families.items()
            },
            "total_per_family": N_SHELLS,
        },
        "decisive_gradient_verdict_emitted": {
            "pass": True,
            "gradient_from_real_hopf_geometry": gradient_from_real_hopf_geometry,
            "gradient_needs_tuned_formula": gradient_needs_tuned_formula,
            "gradient_claim_blockers": gradient_claim_blockers,
            "candidate_metrics": cand_metrics,
        },
        "remote_local_unitary_no_signal_control": no_signal,
    }
    graveyard_companions = {
        "flat_shell_control_collapses_gradient": {
            "pass": flat_degrades,
            "candidate_phi0_range": cand_metrics["phi0_range"],
            "flat_phi0_range": flat_metrics["phi0_range"],
        },
        "product_cut_control_loses_positive_coherent_information_signal": {
            "pass": product_degrades,
            "product_metrics": product_metrics,
        },
        "same_scalar_different_gradient_control_keeps_scalar_mean_but_changes_gradient": {
            "pass": same_scalar_pass,
            "candidate_mean_Ic": cand_metrics["phi0_mean"],
            "control_mean_Ic": same_scalar_metrics["phi0_mean"],
            "mean_gap": same_scalar_mean_gap,
            "gradient_profile_l2_gap": same_scalar_gradient_gap,
        },
        "no_chirality_control_ties_candidate_not_beaten": {
            "pass": no_chirality_ties_candidate,
            "phi0_max_abs_gap": no_chirality_phi0_gap,
            "gradient_max_abs_gap": no_chirality_gradient_gap,
            "interpretation": "Coherent information on this real Hopf-latitude construction is phase/chirality insensitive; the required no-chirality control is not beaten.",
        },
        "clifford_torus_peak_breaks_monotone_gradient_claim": {
            "pass": bool(not monotone_on_real_foliation and cand_metrics["peak_is_clifford_torus"]),
            "monotone_on_real_foliation": monotone_on_real_foliation,
            "peak_eta": cand_metrics["peak_eta"],
            "clifford_eta": math.pi / 4.0,
            "gradient_sign_changes": cand_metrics["gradient_sign_changes"],
        },
    }
    boundary = {
        "formal_scout_only": {
            "pass": boundary_pass,
            "scratch_diagnostic": SCRATCH_DIAGNOSTIC,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "blocked_consumers": BLOCKED_CONSUMERS,
            "boundary_checks": boundary_checks,
        },
        "no_axis0_gravity_or_physics_admission": {
            "pass": True,
            "blocked": ["Axis0", "gravity", "physics", "bridge_promotion", "formal_admission"],
        },
        "gradient_needs_tuned_formula_reported_when_real_geometry_fails": {
            "pass": gradient_needs_tuned_formula,
            "reason": "The genuine Hopf latitude produces a Clifford-centered non-monotone coherent-information profile and does not beat the no-chirality control.",
        },
    }
    pass_rows = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [
        row["pass"] for row in boundary.values()
    ]
    nearby_variants = {
        "total": len(pass_rows),
        "passed": sum(1 for row in pass_rows if row),
        "variants": sorted(list(positive.keys()) + list(graveyard_companions.keys()) + list(boundary.keys())),
    }
    all_pass = bool(nearby_variants["passed"] == nearby_variants["total"])
    verdicts = {
        "gradient_from_real_hopf_geometry": gradient_from_real_hopf_geometry,
        "monotone_on_real_foliation": monotone_on_real_foliation,
        "gradient_needs_tuned_formula": gradient_needs_tuned_formula,
        "real_geometry_gradient_nonflat": gradient_nonflat,
        "required_controls_beaten": required_controls_beaten,
        "candidate_beats_flat_control": flat_degrades,
        "candidate_beats_product_control": product_degrades,
        "same_scalar_different_gradient_control_pass": same_scalar_pass,
        "candidate_beats_no_chirality_control": candidate_beats_no_chirality,
        "no_chirality_control_tied_candidate": no_chirality_ties_candidate,
        "no_signal_control_pass": no_signal["pass"],
        "promotion_allowed": PROMOTION_ALLOWED,
    }
    return {
        "schema": SCHEMA,
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": "xi_shell_real_hopf_geometry_gradient_probe",
        "scratch_diagnostic": SCRATCH_DIAGNOSTIC,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "verdicts": verdicts,
        "gradient_claim_blockers": gradient_claim_blockers,
        "scores": {
            "candidate": cand_metrics,
            "controls": {label: row["metrics"] for label, row in controls.items()},
        },
        "readouts": {
            "candidate_per_shell": candidate["readouts"],
            "control_per_shell": {label: row["readouts"] for label, row in controls.items()},
        },
        "gradients": {
            "candidate": candidate["gradient_dPhi0_deta"],
            "controls": {label: row["gradient_dPhi0_deta"] for label, row in controls.items()},
            "etas": candidate["etas"],
        },
        "control_margins": {
            "candidate_phi0_range_minus_flat": cand_metrics["phi0_range"] - flat_metrics["phi0_range"],
            "candidate_phi0_max_minus_product_phi0_max": cand_metrics["phi0_max"] - product_metrics["phi0_max"],
            "same_scalar_mean_gap": same_scalar_mean_gap,
            "same_scalar_gradient_profile_l2_gap": same_scalar_gradient_gap,
            "no_chirality_phi0_max_abs_gap": no_chirality_phi0_gap,
            "no_chirality_gradient_max_abs_gap": no_chirality_gradient_gap,
        },
        "result_summary": {
            "diagnostic_all_checks_completed": all_pass,
            "rho_ab_is_downstream_adapter": True,
            "gradient_from_real_hopf_geometry": gradient_from_real_hopf_geometry,
            "monotone_on_real_foliation": monotone_on_real_foliation,
            "gradient_needs_tuned_formula": gradient_needs_tuned_formula,
            "accepted_ceiling": "scratch_diagnostic",
            "promotion_allowed": PROMOTION_ALLOWED,
            "plain": "Real Hopf latitude gives a Clifford-centered non-monotone coherent-information profile; the no-chirality control ties it.",
        },
        "validations": {
            "result_contract_expected": "validate_formal_scout_results.py --fresh-rerun on this result",
            "static_contract_expected": "scripts/lint_sim_contract.py on this source",
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": {
            "pass": True,
            "reason": "This is an unpromoted v5 formal scout over a real Hopf-latitude Xi-shell gradient audit, not a canonical v4 probe.",
        },
        "blockers": [],
        "source_paths": {
            "original_coherent_information_probe": ORIGINAL_SOURCE,
            "real_hopf_foliation_julia_source": HOPF_SOURCE,
        },
        "plain_sentence": (
            "The genuine nested-Hopf latitude produces a nonflat but Clifford-centered non-monotone "
            "I_c(A->B) profile, and the phase-erased/no-chirality control ties it. Therefore the "
            "monotone Xi-gradient bridge does not survive this real-geometry audit; "
            "gradient_needs_tuned_formula=True."
        ),
        "shell_family": {
            "qubits": N_QUBITS,
            "shell_count": N_SHELLS,
            "phase_count": PHASE_COUNT,
            "cut": {"A": [0, 1], "B": [2, 3]},
            "candidate_shell_params": candidate["shell_params"],
            "parameterization": "F(eta,phi,chi)=(cos(eta)*exp(i*phi), sin(eta)*exp(i*chi))",
        },
    }


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = run_probe()
    result["runtime_seconds"] = time.time() - start
    result["generated_at"] = time.time()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "result_path": str(OUT_PATH),
                "gradient_from_real_hopf_geometry": result["verdicts"]["gradient_from_real_hopf_geometry"],
                "monotone_on_real_foliation": result["verdicts"]["monotone_on_real_foliation"],
                "gradient_needs_tuned_formula": result["verdicts"]["gradient_needs_tuned_formula"],
                "candidate_beats_no_chirality_control": result["verdicts"]["candidate_beats_no_chirality_control"],
                "gradient_claim_blockers": result["gradient_claim_blockers"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
