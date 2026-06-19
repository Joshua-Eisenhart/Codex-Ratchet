#!/usr/bin/env python3
"""Xi-shell coherent-information gradient bridge scout.

Formal scout only. This tests the correction that a scalar Xi/Phi0 readout is
too collapsible: the finite bridge object should be a nested shell family

    Xi_shell(r_k) -> rho_AB(r_k)
    Phi0(r_k) = I_c(A -> B)
    dPhi0 / dr

over a bounded four-qubit spinor/twistor cut. A positive result can only say
that the shell-gradient candidate survived this fenced scout.
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
NAME = "xi_shell_coherent_information_gradient_bridge_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
WIKI_SOURCE = pathlib.Path(
    "/Users/joshuaeisenhart/wiki/projects/codex-ratchet/"
    "holodeck-fep-igt-axis0-deep-content-correlation-2026-06-06.codex2-draft.md"
)

SCHEMA = "FORMAL_SCOUT_RESULT_v1"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "xi_shell_coherent_information_gradient_bridge_candidate"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite Xi_shell(r)->rho_AB(r) candidate and "
    "Phi0(r)=I_c(A->B) gradient over shell radius. It does not admit final Xi, "
    "final Phi0, Axis0, gravity, physics, bridge promotion, holography, ER=EPR, "
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
    "pathlib": {"tried": True, "used": True, "reason": "supportive local result and optional wiki-source readability checks"},
    "math": {"tried": True, "used": True, "reason": "supportive finite shell parameters and scalar summaries"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not needed for this bounded numeric/QIT gradient scout; nonpromotion is enforced by explicit result fences",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "not needed because no symbolic derivation is claimed",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "not needed for the fixed six-edge four-node graph",
    },
    "networkx": {
        "tried": False,
        "used": False,
        "reason": "not needed for the fixed six-edge four-node graph",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "math": "supportive",
    "time": "supportive",
    "z3": "None",
    "sympy": "None",
    "rustworkx": "None",
    "networkx": "None",
}

DTYPE = torch.float64
CDTYPE = torch.complex128
EPS = 1e-12
N_QUBITS = 4
N_SHELLS = 9
EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (1, 3)]
I2 = torch.eye(2, dtype=CDTYPE)
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


def kron_many(values: list[torch.Tensor]) -> torch.Tensor:
    out = values[0]
    for value in values[1:]:
        out = torch.kron(out, value)
    return out


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


def shell_radius(k: int) -> float:
    return 0.72 + 0.19 * k


def designed_twist(radius: float, k: int) -> float:
    t = k / (N_SHELLS - 1)
    return 0.28 + 1.35 * t + 0.16 * math.sin(math.pi * t) + 0.04 * radius


def shell_spinors(radius: float, twist: float, *, chiral: bool) -> list[torch.Tensor]:
    scale = 1.0 if chiral else 0.0
    rows = []
    for node in range(4):
        orientation = 1.0 if node % 2 == 0 else -1.0
        phi = 0.13 + 0.27 * node + 0.09 * radius + scale * orientation * 0.07 * math.sin(twist + node)
        chi = orientation * (0.18 + 0.025 * node) + scale * 0.11 * math.cos(twist + 0.41 * node)
        eta = 0.37 + 0.055 * node + 0.025 * math.sin(radius + 0.33 * node)
        rows.append(spinor(phi, chi, eta))
    return rows


def twistor_nodes(spinors: list[torch.Tensor], radius: float, twist: float, *, chiral: bool) -> list[dict[str, torch.Tensor]]:
    nodes = []
    scale = 1.0 if chiral else 0.0
    for idx, omega in enumerate(spinors):
        pi = spinor(
            0.21 + 0.19 * idx + 0.06 * radius + scale * 0.05 * math.sin(twist),
            -0.08 + 0.04 * idx + scale * 0.10 * math.cos(twist + idx),
            0.44 + 0.03 * idx,
        )
        nodes.append({"omega": normalize(omega), "pi": normalize(pi)})
    return nodes


def incidence(a: dict[str, torch.Tensor], b: dict[str, torch.Tensor]) -> torch.Tensor:
    return torch.vdot(a["pi"], b["omega"]) - torch.vdot(b["pi"], a["omega"])


def xi_shell_parameters(k: int, mode: str) -> dict[str, Any]:
    radius = shell_radius(k)
    t = k / (N_SHELLS - 1)
    chiral = mode not in {"zero_phase", "flat"}
    twist = designed_twist(radius, k) if chiral else 0.0
    spinors = shell_spinors(radius, twist, chiral=chiral)
    twistors = twistor_nodes(spinors, radius, twist, chiral=chiral)
    incs = [incidence(twistors[i], twistors[j]) for i, j in EDGES]
    inc_mags = [float(torch.abs(row).item()) for row in incs]
    inc_phases = [float(torch.angle(row).item()) for row in incs]
    mean_mag = sum(inc_mags) / len(inc_mags)
    mean_phase = math.atan2(
        sum(math.sin(row) for row in inc_phases),
        sum(math.cos(row) for row in inc_phases),
    )

    if mode == "candidate":
        lam = 0.17 + 0.46 * t + 0.025 * math.tanh(mean_mag)
        phase = mean_phase + twist
    elif mode == "flat":
        lam = 0.39
        phase = 0.0
    elif mode == "zero_phase":
        lam = 0.35 + 0.012 * math.tanh(mean_mag)
        phase = 0.0
    elif mode == "random_phase":
        gen = torch.Generator()
        gen.manual_seed(20260606 + k)
        lam = float((0.17 + 0.46 * torch.rand((), generator=gen)).item())
        phase = float(((torch.rand((), generator=gen) - 0.5) * 2.0 * math.pi).item())
    else:
        raise ValueError(mode)

    lam = min(0.70, max(0.04, lam))
    return {
        "k": k,
        "radius": radius,
        "shell_fraction": t,
        "designed_twist": twist,
        "lambda": lam,
        "phase": phase,
        "mean_incidence_magnitude": mean_mag,
        "mean_incidence_phase": mean_phase,
        "edge_count": len(EDGES),
        "spinors": spinors,
    }


def shell_density(k: int, mode: str) -> dict[str, Any]:
    params = xi_shell_parameters(k, mode)
    spinors = params["spinors"]
    a0 = normalize(torch.kron(spinors[0], spinors[1]))
    b0 = normalize(torch.kron(spinors[2], spinors[3]))
    a1 = normalize(torch.kron(orthogonal_spinor(spinors[0]), orthogonal_spinor(spinors[1])))
    b1 = normalize(torch.kron(orthogonal_spinor(spinors[2]), orthogonal_spinor(spinors[3])))
    state = normalize(
        math.cos(params["lambda"]) * torch.kron(a0, b0)
        + math.sin(params["lambda"]) * cexp(params["phase"]) * torch.kron(a1, b1)
    )
    rho = density(state)
    public_params = {key: value for key, value in params.items() if key != "spinors"}
    return {"rho": rho, "params": public_params}


def family(mode: str) -> dict[str, Any]:
    rows = [shell_density(k, mode) for k in range(N_SHELLS)]
    return family_from_rows(mode, rows)


def family_from_rows(label: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    radii = [row["params"]["radius"] for row in rows]
    twists = [row["params"]["designed_twist"] for row in rows]
    readouts = [cut_readouts(row["rho"]) for row in rows]
    health = [matrix_health(row["rho"]) for row in rows]
    phi0 = [row["I_c_A_to_B"] for row in readouts]
    gradients = finite_difference(phi0, radii)
    return {
        "label": label,
        "radii": radii,
        "twists": twists,
        "phi0": phi0,
        "gradient_dPhi0_dr": gradients,
        "readouts": readouts,
        "health": health,
        "shell_params": [row["params"] for row in rows],
        "metrics": gradient_metrics(phi0, radii, twists, gradients),
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


def gradient_metrics(phi0: list[float], radii: list[float], twists: list[float], gradients: list[float]) -> dict[str, float]:
    abs_grad = [abs(row) for row in gradients]
    positive_count = sum(1 for row in gradients if row > 0.0)
    mean_abs = sum(abs_grad) / len(abs_grad)
    grad_variation = max(gradients) - min(gradients)
    phi0_range = max(phi0) - min(phi0)
    corr_radius = pearson(radii, phi0)
    corr_twist = pearson(twists, phi0) if max(twists) - min(twists) > EPS else 0.0
    sign_consistency = positive_count / len(gradients)
    positive_signal_score = max(0.0, corr_radius) * sign_consistency * min(1.0, phi0_range / 0.10)
    return {
        "phi0_mean": sum(phi0) / len(phi0),
        "phi0_min": min(phi0),
        "phi0_max": max(phi0),
        "phi0_range": phi0_range,
        "gradient_mean_abs": mean_abs,
        "gradient_max_abs": max(abs_grad),
        "gradient_variation": grad_variation,
        "gradient_positive_fraction": sign_consistency,
        "gradient_min": min(gradients),
        "gradient_max": max(gradients),
        "radius_phi0_correlation": corr_radius,
        "twist_phi0_correlation": corr_twist,
        "positive_signal_score": positive_signal_score,
    }


def product_family(candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [{"rho": productize_cut(row["rho"]), "params": dict(row["params"])} for row in candidate_rows]
    return family_from_rows("product_cut_control", rows)


def flat_family(candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    base = candidate_rows[len(candidate_rows) // 2]
    rows = []
    for row in candidate_rows:
        params = dict(row["params"])
        params["lambda"] = base["params"]["lambda"]
        params["phase"] = base["params"]["phase"]
        params["flat_source_shell"] = base["params"]["k"]
        rows.append({"rho": base["rho"].clone(), "params": params})
    return family_from_rows("flat_shell_control", rows)


def scrambled_family(candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    perm = [0, 8, 1, 7, 2, 6, 3, 5, 4]
    rows = []
    for radius_row, source_idx in zip(candidate_rows, perm):
        params = dict(radius_row["params"])
        params["source_shell_after_scramble"] = source_idx
        rows.append({"rho": candidate_rows[source_idx]["rho"].clone(), "params": params})
    return family_from_rows("shell_order_scramble_control", rows)


def reversed_mean_matched_family(candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    reversed_rows = list(reversed(candidate_rows))
    for radius_row, source in zip(candidate_rows, reversed_rows):
        params = dict(radius_row["params"])
        params["source_shell_for_same_scalar_control"] = source["params"]["k"]
        rows.append({"rho": source["rho"].clone(), "params": params})
    return family_from_rows("same_scalar_different_gradient_control", rows)


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


def wiki_source_readable() -> bool:
    try:
        return bool(WIKI_SOURCE.read_text(encoding="utf-8")[:1])
    except OSError:
        return False


def run_probe() -> dict[str, Any]:
    candidate_rows = [shell_density(k, "candidate") for k in range(N_SHELLS)]
    candidate = family_from_rows("candidate", candidate_rows)
    flat = flat_family(candidate_rows)
    product = product_family(candidate_rows)
    zero_phase = family("zero_phase")
    random_phase = family("random_phase")
    scramble = scrambled_family(candidate_rows)
    same_scalar = reversed_mean_matched_family(candidate_rows)
    controls = {
        "flat_shell_control": flat,
        "product_cut_control": product,
        "shell_order_scramble_control": scramble,
        "no_chirality_or_zero_phase_control": zero_phase,
        "random_phase_control": random_phase,
        "same_scalar_different_gradient_control": same_scalar,
    }
    all_families = {"candidate": candidate, **controls}
    all_health = all(row["pass"] for family_row in all_families.values() for row in family_row["health"])

    cand_metrics = candidate["metrics"]
    random_metrics = random_phase["metrics"]
    control_scores = {
        label: row["metrics"]["positive_signal_score"]
        for label, row in controls.items()
        if label not in {"same_scalar_different_gradient_control"}
    }
    best_control_label, best_control_score = max(control_scores.items(), key=lambda row: row[1])
    best_random_or_control_margin = cand_metrics["positive_signal_score"] - best_control_score

    gradient_nontrivial = bool(
        cand_metrics["phi0_range"] > 0.15
        and cand_metrics["gradient_mean_abs"] > 0.15
        and cand_metrics["gradient_positive_fraction"] == 1.0
        and cand_metrics["radius_phi0_correlation"] > 0.98
    )
    flat_degrades = flat["metrics"]["phi0_range"] < 1e-9 and flat["metrics"]["gradient_mean_abs"] < 1e-9
    product_degrades = bool(
        product["metrics"]["phi0_max"] <= 1e-9
        and product["metrics"]["gradient_positive_fraction"] == 0.0
        and product["metrics"]["radius_phi0_correlation"] < -0.98
    )
    scramble_degrades = bool(
        scramble["metrics"]["radius_phi0_correlation"] < 0.75
        and scramble["metrics"]["gradient_positive_fraction"] < 0.75
    )
    zero_phase_degrades = bool(zero_phase["metrics"]["phi0_range"] < cand_metrics["phi0_range"] * 0.20)
    random_phase_degrades = bool(
        cand_metrics["positive_signal_score"] > random_metrics["positive_signal_score"] + 0.25
        and cand_metrics["radius_phi0_correlation"] > random_metrics["radius_phi0_correlation"] + 0.20
    )
    same_scalar_mean_gap = abs(cand_metrics["phi0_mean"] - same_scalar["metrics"]["phi0_mean"])
    same_scalar_gradient_gap = gradient_profile_l2(
        candidate["gradient_dPhi0_dr"],
        same_scalar["gradient_dPhi0_dr"],
    )
    same_scalar_pass = bool(same_scalar_mean_gap < 1e-12 and same_scalar_gradient_gap > 1.0)
    no_signal = local_unitary_no_signal_check(candidate_rows[N_SHELLS // 2]["rho"])

    scalar_value_only = {
        "single_shell_index": N_SHELLS // 2,
        "single_shell_I_c_A_to_B": candidate["phi0"][N_SHELLS // 2],
        "pass": True,
        "verdict": "insufficient_by_design",
        "reason": "A single Phi0 scalar is not accepted as bridge evidence without the shell gradient and controls.",
    }

    control_margins = {
        "candidate_score": cand_metrics["positive_signal_score"],
        "best_control_label": best_control_label,
        "best_control_score": best_control_score,
        "best_random_or_control_margin": best_random_or_control_margin,
        "candidate_minus_random_score": cand_metrics["positive_signal_score"] - random_metrics["positive_signal_score"],
        "candidate_phi0_range_minus_flat": cand_metrics["phi0_range"] - flat["metrics"]["phi0_range"],
        "candidate_phi0_range_minus_zero_phase": cand_metrics["phi0_range"] - zero_phase["metrics"]["phi0_range"],
        "same_scalar_mean_gap": same_scalar_mean_gap,
        "same_scalar_gradient_profile_l2_gap": same_scalar_gradient_gap,
        "product_max_Ic": product["metrics"]["phi0_max"],
    }
    controls_pass = bool(
        scalar_value_only["pass"]
        and flat_degrades
        and product_degrades
        and scramble_degrades
        and zero_phase_degrades
        and random_phase_degrades
        and same_scalar_pass
    )
    boundary_checks = {
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
    candidate_survived = bool(
        all_health and gradient_nontrivial and controls_pass and no_signal["pass"] and boundary_pass
    )
    blockers = []
    if not all_health:
        blockers.append("matrix_health_failed")
    if not gradient_nontrivial:
        blockers.append("candidate_gradient_not_nontrivial")
    if not controls_pass:
        blockers.append("one_or_more_controls_did_not_degrade")
    if random_metrics["positive_signal_score"] >= cand_metrics["positive_signal_score"]:
        blockers.append("random_phase_control_beat_or_tied_candidate")
    if not no_signal["pass"]:
        blockers.append("remote_local_unitary_no_signal_control_failed")
    if not boundary_pass:
        blockers.append("claim_ceiling_boundary_failed")

    positive = {
        "xi_shell_gradient_candidate_survived_this_fenced_scout": {
            "pass": candidate_survived,
            "status": "xi_shell_gradient_candidate_survived_this_fenced_scout" if candidate_survived else "open_or_killed",
            "gradient_nontrivial": gradient_nontrivial,
            "candidate_metrics": cand_metrics,
        },
        "matrix_health_all_shells_and_controls": {
            "pass": all_health,
            "health_counts": {
                label: sum(1 for row in family_row["health"] if row["pass"])
                for label, family_row in all_families.items()
            },
            "total_per_family": N_SHELLS,
        },
        "gradient_is_load_bearing_not_scalar_mean": {
            "pass": same_scalar_pass and scalar_value_only["pass"],
            "scalar_value_only_control": scalar_value_only,
            "same_scalar_different_gradient_control": {
                "candidate_mean_Ic": cand_metrics["phi0_mean"],
                "control_mean_Ic": same_scalar["metrics"]["phi0_mean"],
                "mean_gap": same_scalar_mean_gap,
                "gradient_profile_l2_gap": same_scalar_gradient_gap,
            },
        },
        "remote_local_unitary_no_signal_control": no_signal,
    }
    graveyard_companions = {
        "flat_shell_control_collapses_gradient": {
            "pass": flat_degrades,
            "candidate_phi0_range": cand_metrics["phi0_range"],
            "flat_phi0_range": flat["metrics"]["phi0_range"],
        },
        "product_cut_control_loses_positive_coherent_information_signal": {
            "pass": product_degrades,
            "product_metrics": product["metrics"],
        },
        "shell_order_scramble_control_degrades_radius_correlation": {
            "pass": scramble_degrades,
            "scramble_metrics": scramble["metrics"],
        },
        "no_chirality_or_zero_phase_control_degrades_gradient": {
            "pass": zero_phase_degrades,
            "zero_phase_metrics": zero_phase["metrics"],
        },
        "random_phase_control_does_not_beat_candidate": {
            "pass": random_phase_degrades,
            "candidate_metrics": cand_metrics,
            "random_phase_metrics": random_metrics,
        },
    }
    boundary = {
        "formal_scout_only": {
            "pass": boundary_pass,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "blocked_consumers": BLOCKED_CONSUMERS,
            "boundary_checks": boundary_checks,
        },
        "wizard_subagents_blocked_runtime_recorded": {
            "pass": True,
            "wizard_subagents_blocked_runtime": True,
            "reason": "Current task explicitly blocks spawn_agent/collab/subagents/Wizard full-matrix; direct-build scout only.",
        },
        "scalar_phi0_value_remains_insufficient": scalar_value_only,
        "no_signal_not_ftl_boundary": no_signal,
    }
    pass_rows = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [
        row["pass"] for row in boundary.values()
    ]
    nearby_variants = {
        "total": len(pass_rows),
        "passed": sum(1 for row in pass_rows if row),
        "variants": sorted(list(positive.keys()) + list(graveyard_companions.keys()) + list(boundary.keys())),
    }
    all_pass = bool(candidate_survived and nearby_variants["passed"] == nearby_variants["total"] and not blockers)
    verdicts = {
        "xi_shell_gradient_candidate_survived": candidate_survived,
        "gradient_nontrivial": gradient_nontrivial,
        "controls_pass": controls_pass,
        "scalar_value_only_insufficient": scalar_value_only["pass"],
        "no_signal_control_pass": no_signal["pass"],
        "promotion_allowed": PROMOTION_ALLOWED,
    }
    return {
        "schema": SCHEMA,
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
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
        "scores": {
            "candidate": cand_metrics,
            "controls": {label: row["metrics"] for label, row in controls.items()},
        },
        "readouts": {
            "candidate_per_shell": candidate["readouts"],
            "control_per_shell": {label: row["readouts"] for label, row in controls.items()},
        },
        "gradients": {
            "candidate": candidate["gradient_dPhi0_dr"],
            "controls": {label: row["gradient_dPhi0_dr"] for label, row in controls.items()},
            "radii": candidate["radii"],
            "twists": candidate["twists"],
        },
        "control_margins": control_margins,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": {
            "pass": True,
            "reason": "This is an unpromoted v5 formal scout over a finite Xi-shell gradient candidate, not a canonical v4 probe.",
        },
        "blockers": blockers,
        "wizard_subagents_blocked_runtime": True,
        "wiki_source_readable": wiki_source_readable(),
        "plain_sentence": (
            "The fenced scout measures Phi0 as coherent information over a finite nested shell family; "
            "the candidate survives only as a gradient-shaped Xi_shell bridge candidate, with scalar, product, "
            "flat, scrambled, zero-phase, random-phase, and no-signal controls still blocking promotion."
            if all_pass
            else "The fenced scout did not admit the Xi-shell gradient candidate; see blockers and controls."
        ),
        "shell_family": {
            "qubits": N_QUBITS,
            "shell_count": N_SHELLS,
            "edges": EDGES,
            "cut": {"A": [0, 1], "B": [2, 3]},
            "candidate_shell_params": candidate["shell_params"],
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
                "xi_shell_gradient_candidate_survived": result["verdicts"]["xi_shell_gradient_candidate_survived"],
                "controls_pass": result["verdicts"]["controls_pass"],
                "no_signal_control_pass": result["verdicts"]["no_signal_control_pass"],
                "best_random_or_control_margin": result["control_margins"]["best_random_or_control_margin"],
                "blockers": result["blockers"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
