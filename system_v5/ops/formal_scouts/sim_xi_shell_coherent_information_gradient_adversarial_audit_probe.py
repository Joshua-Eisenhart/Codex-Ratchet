#!/usr/bin/env python3
"""Adversarial audit for the Xi-shell coherent-information gradient candidate.

Formal scout only. This is an independent local reimplementation of the
density/partial-trace/entropy/profile machinery used to pressure the current
Xi-shell gradient candidate. It compares against the prior result but does not
call or import the prior scout.
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
NAME = "xi_shell_coherent_information_gradient_adversarial_audit_probe"
SOURCE_PATH = pathlib.Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{NAME}_results.json"
RECEIPT_PATH = RESULT_DIR / f"{NAME}_codex2_receipt.json"
ORIGINAL_RESULT_PATH = RESULT_DIR / "xi_shell_coherent_information_gradient_bridge_probe_results.json"

SCHEMA = "FORMAL_SCOUT_RESULT_v1"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "xi_shell_coherent_information_gradient_adversarial_audit"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
INDEPENDENT_REIMPLEMENTATION = True

CLAIM_CEILING = (
    "Formal scout only: adversarially audits the finite Xi_shell(r)->rho_AB(r) "
    "coherent-information gradient candidate. It does not admit final Xi, final "
    "Phi0, Axis0, gravity, physics, bridge promotion, holography, ER=EPR, FTL, "
    "or formal admission."
)
TARGET_CLAIM = (
    "A finite shell-indexed density family has a nontrivial monotone "
    "Phi0(r)=I_c(A->B) gradient on the declared [0,1]|[2,3] cut, and that "
    "gradient is not reproduced by product/null, phase/twist-randomized, "
    "shell-order-scrambled, wrong-cut, no-boundary, no-chirality, no-signal, "
    "or scalar-only controls."
)
BLOCKED_DOWNSTREAM_CONSUMERS = [
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
        "reason": (
            "load-bearing complex128 state vectors, density matrices, generic "
            "partial traces, eigvalsh von Neumann entropy, coherent information, "
            "local unitaries, and all finite-shell controls"
        ),
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result and receipt serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive source/result path handling"},
    "math": {"tried": True, "used": True, "reason": "supportive shell parameters and scalar scoring"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not needed for this bounded numeric QIT adversarial audit; no proof or promotion claim is made",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "not needed because no symbolic identity or derivation is claimed",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "not needed because no graph algorithm is load-bearing in this bounded audit",
    },
    "networkx": {
        "tried": False,
        "used": False,
        "reason": "not needed because no graph algorithm is load-bearing in this bounded audit",
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

CDTYPE = torch.complex128
EPS = 1e-12
N_QUBITS = 4
N_SHELLS = 9
DIMS = [2, 2, 2, 2]
DECLARED_A = [0, 1]
DECLARED_B = [2, 3]
WRONG_CUTS = [[0, 2], [0, 3], [1, 2], [1, 3]]
I2 = torch.eye(2, dtype=CDTYPE)
I4 = torch.eye(4, dtype=CDTYPE)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(row) for key, row in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(row) for row in value]
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


def prod(values: list[int]) -> int:
    out = 1
    for value in values:
        out *= value
    return out


def normalize_vector(vec: torch.Tensor) -> torch.Tensor:
    return vec / torch.clamp(torch.linalg.vector_norm(vec), min=EPS)


def spinor(theta: float, phi: float) -> torch.Tensor:
    return normalize_vector(
        torch.tensor(
            [math.cos(theta / 2.0), cexp(phi) * math.sin(theta / 2.0)],
            dtype=CDTYPE,
        )
    )


def orthogonal_spinor(vec: torch.Tensor) -> torch.Tensor:
    return normalize_vector(torch.stack([-torch.conj(vec[1]), torch.conj(vec[0])]))


def kron_many(values: list[torch.Tensor]) -> torch.Tensor:
    out = values[0]
    for value in values[1:]:
        out = torch.kron(out, value)
    return out


def hermitize(rho: torch.Tensor) -> torch.Tensor:
    return (rho + torch.conj(rho).T) / 2.0


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = hermitize(rho)
    tr = torch.real(torch.trace(rho))
    return rho / torch.clamp(tr, min=EPS)


def density_from_state(state: torch.Tensor) -> torch.Tensor:
    state = normalize_vector(state)
    return normalize_density(torch.outer(state, torch.conj(state)))


def partial_trace(rho: torch.Tensor, dims: list[int], keep: list[int]) -> torch.Tensor:
    n = len(dims)
    keep = list(keep)
    traced = [idx for idx in range(n) if idx not in keep]
    keep_dims = [dims[idx] for idx in keep]
    trace_dims = [dims[idx] for idx in traced]
    reshaped = rho.reshape(*dims, *dims)
    perm = keep + traced + [idx + n for idx in keep] + [idx + n for idx in traced]
    folded = reshaped.permute(*perm).reshape(prod(keep_dims), prod(trace_dims), prod(keep_dims), prod(trace_dims))
    return normalize_density(torch.einsum("abcb->ac", folded))


def von_neumann_entropy(rho: torch.Tensor) -> float:
    evals = torch.linalg.eigvalsh(hermitize(rho)).real
    evals = torch.clamp(evals, min=0.0)
    evals = evals / torch.clamp(torch.sum(evals), min=EPS)
    nonzero = evals[evals > EPS]
    return float((-torch.sum(nonzero * torch.log(nonzero))).item())


def cut_readout(rho: torch.Tensor, cut_a: list[int]) -> dict[str, float]:
    cut_b = [idx for idx in range(N_QUBITS) if idx not in cut_a]
    rho_ab = normalize_density(rho)
    rho_a = partial_trace(rho_ab, DIMS, cut_a)
    rho_b = partial_trace(rho_ab, DIMS, cut_b)
    s_a = von_neumann_entropy(rho_a)
    s_b = von_neumann_entropy(rho_b)
    s_ab = von_neumann_entropy(rho_ab)
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "I_A_B": s_a + s_b - s_ab,
        "S_A_given_B": s_ab - s_b,
        "I_c_A_to_B": s_b - s_ab,
    }


def matrix_health(rho: torch.Tensor) -> dict[str, Any]:
    rho = normalize_density(rho)
    evals = torch.linalg.eigvalsh(hermitize(rho)).real
    hermiticity_gap = float(torch.linalg.matrix_norm(rho - torch.conj(rho).T).item())
    trace_gap = abs(float(torch.real(torch.trace(rho)).item()) - 1.0)
    min_eval = float(torch.min(evals).item())
    return {
        "hermiticity_gap": hermiticity_gap,
        "trace_gap": trace_gap,
        "min_eigenvalue": min_eval,
        "pass": bool(hermiticity_gap < 1e-9 and trace_gap < 1e-9 and min_eval > -1e-9),
    }


def shell_radius(k: int) -> float:
    return 0.72 + 0.19 * k


def shell_fraction(k: int) -> float:
    return k / (N_SHELLS - 1)


def shell_twist(k: int) -> float:
    t = shell_fraction(k)
    return 0.31 + 1.38 * t + 0.12 * math.sin(math.pi * t)


def entanglement_angle(k: int) -> float:
    t = shell_fraction(k)
    raw = 0.17 + 0.46 * t + 0.012 * math.sin(math.pi * t)
    return min(0.70, max(0.04, raw))


def local_shell_basis(k: int, *, symmetrized: bool, phase_seed: int | None = None) -> dict[str, torch.Tensor]:
    radius = shell_radius(k)
    twist = shell_twist(k)
    gen = torch.Generator()
    if phase_seed is not None:
        gen.manual_seed(20260606 + 7919 * phase_seed + k)
    spinors = []
    for node in range(N_QUBITS):
        orientation = 1.0 if node % 2 == 0 else -1.0
        orient_scale = 0.0 if symmetrized else orientation
        random_phase = 0.0
        random_theta = 0.0
        if phase_seed is not None:
            random_phase = float(((torch.rand((), generator=gen) - 0.5) * 2.0 * math.pi).item())
            random_theta = float(((torch.rand((), generator=gen) - 0.5) * 0.32).item())
        theta = 0.72 + 0.05 * node + 0.035 * math.sin(radius + 0.23 * node) + 0.025 * orient_scale * math.cos(twist)
        phi = 0.17 + 0.29 * node + 0.13 * radius + orient_scale * 0.19 * math.sin(twist + 0.41 * node)
        spinors.append(spinor(theta + random_theta, phi + random_phase))
    a0 = normalize_vector(torch.kron(spinors[0], spinors[1]))
    b0 = normalize_vector(torch.kron(spinors[2], spinors[3]))
    a1 = normalize_vector(torch.kron(orthogonal_spinor(spinors[0]), orthogonal_spinor(spinors[1])))
    b1 = normalize_vector(torch.kron(orthogonal_spinor(spinors[2]), orthogonal_spinor(spinors[3])))
    return {"a0": a0, "a1": a1, "b0": b0, "b1": b1}


def shell_state(
    k: int,
    *,
    alpha: float | None = None,
    symmetrized: bool = False,
    phase_seed: int | None = None,
    phase_override: float | None = None,
    fixed_basis: bool = False,
) -> torch.Tensor:
    alpha = entanglement_angle(k) if alpha is None else alpha
    if fixed_basis:
        zero = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=CDTYPE)
        one = torch.tensor([0.0 + 0.0j, 1.0 + 0.0j], dtype=CDTYPE)
        a0 = torch.kron(zero, zero)
        a1 = torch.kron(one, one)
        b0 = torch.kron(zero, zero)
        b1 = torch.kron(one, one)
    else:
        basis = local_shell_basis(k, symmetrized=symmetrized, phase_seed=phase_seed)
        a0 = basis["a0"]
        a1 = basis["a1"]
        b0 = basis["b0"]
        b1 = basis["b1"]
    phase = shell_twist(k) + 0.07 * shell_radius(k)
    if phase_override is not None:
        phase = phase_override
    return normalize_vector(math.cos(alpha) * torch.kron(a0, b0) + math.sin(alpha) * cexp(phase) * torch.kron(a1, b1))


def candidate_rows() -> list[dict[str, Any]]:
    rows = []
    for k in range(N_SHELLS):
        state = shell_state(k)
        rows.append(
            {
                "rho": density_from_state(state),
                "params": {
                    "k": k,
                    "radius": shell_radius(k),
                    "shell_fraction": shell_fraction(k),
                    "twist": shell_twist(k),
                    "entanglement_angle": entanglement_angle(k),
                    "cut": {"A": DECLARED_A, "B": DECLARED_B},
                },
            }
        )
    return rows


def finite_difference(values: list[float], xs: list[float]) -> list[float]:
    return [(values[idx + 1] - values[idx]) / (xs[idx + 1] - xs[idx]) for idx in range(len(values) - 1)]


def pearson(xs: list[float], ys: list[float]) -> float:
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    dx = [x - mean_x for x in xs]
    dy = [y - mean_y for y in ys]
    denom_x = math.sqrt(sum(row * row for row in dx))
    denom_y = math.sqrt(sum(row * row for row in dy))
    if denom_x < EPS or denom_y < EPS:
        return 0.0
    return sum(x * y for x, y in zip(dx, dy)) / (denom_x * denom_y)


def gradient_profile_l2(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((a - b) * (a - b) for a, b in zip(left, right)))


def profile_metrics(phi0: list[float], radii: list[float]) -> dict[str, float]:
    gradients = finite_difference(phi0, radii)
    abs_grad = [abs(row) for row in gradients]
    positive_fraction = sum(1 for row in gradients if row > 0.0) / len(gradients)
    phi0_range = max(phi0) - min(phi0)
    radius_correlation = pearson(radii, phi0)
    score = max(0.0, radius_correlation) * positive_fraction * min(1.0, phi0_range / 0.10)
    return {
        "phi0_mean": sum(phi0) / len(phi0),
        "phi0_min": min(phi0),
        "phi0_max": max(phi0),
        "phi0_range": phi0_range,
        "gradient_mean_abs": sum(abs_grad) / len(abs_grad),
        "gradient_max_abs": max(abs_grad),
        "gradient_min": min(gradients),
        "gradient_max": max(gradients),
        "gradient_positive_fraction": positive_fraction,
        "gradient_variation": max(gradients) - min(gradients),
        "radius_phi0_correlation": radius_correlation,
        "positive_signal_score": score,
    }


def family_from_rows(label: str, rows: list[dict[str, Any]], cut_a: list[int] | None = None) -> dict[str, Any]:
    cut_a = DECLARED_A if cut_a is None else cut_a
    radii = [row["params"]["radius"] for row in rows]
    readouts = [cut_readout(row["rho"], cut_a) for row in rows]
    phi0 = [row["I_c_A_to_B"] for row in readouts]
    metrics = profile_metrics(phi0, radii)
    return {
        "label": label,
        "cut_A": cut_a,
        "cut_B": [idx for idx in range(N_QUBITS) if idx not in cut_a],
        "radii": radii,
        "phi0": phi0,
        "gradient_dPhi0_dr": finite_difference(phi0, radii),
        "metrics": metrics,
        "readouts": readouts,
        "health": [matrix_health(row["rho"]) for row in rows],
        "shell_params": [row["params"] for row in rows],
    }


def productize_declared_cut(rho: torch.Tensor) -> torch.Tensor:
    rho_a = partial_trace(rho, DIMS, DECLARED_A)
    rho_b = partial_trace(rho, DIMS, DECLARED_B)
    return normalize_density(torch.kron(rho_a, rho_b))


def product_null_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"rho": productize_declared_cut(row["rho"]), "params": dict(row["params"])} for row in rows]


def phase_randomized_rows() -> list[dict[str, Any]]:
    rows = []
    for k in range(N_SHELLS):
        gen = torch.Generator()
        gen.manual_seed(45013 + k)
        phase = float(((torch.rand((), generator=gen) - 0.5) * 2.0 * math.pi).item())
        state = shell_state(k, phase_seed=17, phase_override=phase)
        rows.append(
            {
                "rho": density_from_state(state),
                "params": {
                    "k": k,
                    "radius": shell_radius(k),
                    "shell_fraction": shell_fraction(k),
                    "twist": "randomized",
                    "entanglement_angle": entanglement_angle(k),
                    "phase_override": phase,
                },
            }
        )
    return rows


def shell_order_scramble_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    permutation = [0, 8, 1, 7, 2, 6, 3, 5, 4]
    scrambled = []
    for radius_row, source_idx in zip(rows, permutation):
        params = dict(radius_row["params"])
        params["scrambled_source_shell"] = source_idx
        scrambled.append({"rho": rows[source_idx]["rho"].clone(), "params": params})
    return scrambled


def no_boundary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mean_alpha = sum(row["params"]["entanglement_angle"] for row in rows) / len(rows)
    flat = []
    for row in rows:
        k = row["params"]["k"]
        state = shell_state(k, alpha=mean_alpha, symmetrized=True, phase_override=0.0)
        params = dict(row["params"])
        params["entanglement_angle"] = mean_alpha
        params["boundary_structure"] = "flattened"
        flat.append({"rho": density_from_state(state), "params": params})
    return flat


def no_chirality_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        k = row["params"]["k"]
        state = shell_state(k, symmetrized=True, phase_override=0.0)
        params = dict(row["params"])
        params["orientation_chirality"] = "symmetrized_erased"
        out.append({"rho": density_from_state(state), "params": params})
    return out


def entanglement_angle_only_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        k = row["params"]["k"]
        state = shell_state(k, fixed_basis=True, phase_override=0.0)
        params = dict(row["params"])
        params["local_shell_geometry"] = "fixed_computational_basis_countermodel"
        params["falsifier"] = "same entanglement-angle schedule without shell/twist/chirality geometry"
        out.append({"rho": density_from_state(state), "params": params})
    return out


def same_scalar_reversed_profile_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reversed_rows = list(reversed(rows))
    out = []
    for radius_row, source in zip(rows, reversed_rows):
        params = dict(radius_row["params"])
        params["same_scalar_source_shell"] = source["params"]["k"]
        out.append({"rho": source["rho"].clone(), "params": params})
    return out


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
    rho_a_before = partial_trace(rho, DIMS, DECLARED_A)
    rho_a_after = partial_trace(transformed, DIMS, DECLARED_A)
    rho_b_before = partial_trace(rho, DIMS, DECLARED_B)
    rho_b_after = partial_trace(transformed, DIMS, DECLARED_B)
    read_before = cut_readout(rho, DECLARED_A)
    read_after = cut_readout(transformed, DECLARED_A)
    rho_a_gap = float(torch.linalg.matrix_norm(rho_a_before - rho_a_after).item())
    rho_b_gap = float(torch.linalg.matrix_norm(rho_b_before - rho_b_after).item())
    rho_ab_gap = float(torch.linalg.matrix_norm(rho - transformed).item())
    ic_gap = abs(read_before["I_c_A_to_B"] - read_after["I_c_A_to_B"])
    passed = rho_a_gap < 1e-10 and rho_ab_gap > 1e-4 and rho_b_gap > 1e-4 and ic_gap < 1e-10
    return {
        "operation": "local_unitary_on_B",
        "observable": "rho_AB and rho_B basis data change while rho_A and I_c(A->B) remain invariant",
        "rho_A_invariance_gap": rho_a_gap,
        "rho_B_change_gap": rho_b_gap,
        "rho_AB_change_gap": rho_ab_gap,
        "I_c_invariance_gap": ic_gap,
        "pass": bool(passed),
        "interpretation": (
            "No signal or FTL reading is admitted: a B-local unitary can change "
            "rho_AB/rho_B representation while leaving A-local state and coherent "
            "information invariant."
        ),
    }


def load_original_summary() -> dict[str, Any]:
    if not ORIGINAL_RESULT_PATH.exists():
        return {"available": False, "path": str(ORIGINAL_RESULT_PATH), "comparison_note": "original result missing"}
    data = json.loads(ORIGINAL_RESULT_PATH.read_text(encoding="utf-8"))
    original_scores = data.get("scores", {})
    original_candidate = original_scores.get("candidate", {})
    return {
        "available": True,
        "path": str(ORIGINAL_RESULT_PATH),
        "original_all_pass": data.get("all_pass"),
        "original_candidate_survived": data.get("verdicts", {}).get("xi_shell_gradient_candidate_survived"),
        "original_controls_pass": data.get("verdicts", {}).get("controls_pass"),
        "original_no_signal_control_pass": data.get("verdicts", {}).get("no_signal_control_pass"),
        "original_best_random_or_control_margin": data.get("control_margins", {}).get("best_random_or_control_margin"),
        "original_candidate_score": original_candidate.get("positive_signal_score"),
        "original_candidate_phi0_range": original_candidate.get("phi0_range"),
        "comparison_note": (
            "prior local scout reported survival; this audit reimplements the core QIT observables "
            "and adds stricter invariance and countermodel controls"
        ),
    }


def expected_degrade(candidate_score: float, control_score: float, *, margin: float = 0.25) -> bool:
    return candidate_score > control_score + margin


def score_gap(candidate_score: float, control_score: float) -> float:
    return candidate_score - control_score


def build_control_row(
    label: str,
    family: dict[str, Any],
    candidate: dict[str, Any],
    expected: str,
    observed: str,
    pass_rule: str,
    passed: bool,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "label": label,
        "expected": expected,
        "observed": observed,
        "pass_rule": pass_rule,
        "pass": bool(passed),
        "candidate_score": candidate["metrics"]["positive_signal_score"],
        "control_score": family["metrics"]["positive_signal_score"],
        "candidate_minus_control_score": score_gap(
            candidate["metrics"]["positive_signal_score"],
            family["metrics"]["positive_signal_score"],
        ),
        "control_metrics": family["metrics"],
    }
    if extra:
        row.update(extra)
    return row


def run_probe() -> dict[str, Any]:
    rows = candidate_rows()
    candidate = family_from_rows("candidate_reimplementation", rows, DECLARED_A)
    candidate_score = candidate["metrics"]["positive_signal_score"]

    product = family_from_rows("product_null_control", product_null_rows(rows), DECLARED_A)
    phase_random = family_from_rows("phase_twist_randomization_control", phase_randomized_rows(), DECLARED_A)
    scramble = family_from_rows("shell_radius_order_scramble_control", shell_order_scramble_rows(rows), DECLARED_A)
    no_boundary = family_from_rows("no_boundary_flattened_coupling_control", no_boundary_rows(rows), DECLARED_A)
    no_chirality = family_from_rows("no_chirality_symmetrized_orientation_control", no_chirality_rows(rows), DECLARED_A)
    angle_only = family_from_rows("entanglement_angle_only_countermodel", entanglement_angle_only_rows(rows), DECLARED_A)
    same_scalar = family_from_rows("same_scalar_mean_reversed_profile_control", same_scalar_reversed_profile_rows(rows), DECLARED_A)
    wrong_cut_families = {
        "cut_" + "_".join(str(idx) for idx in cut): family_from_rows("wrong_cut_control", rows, cut)
        for cut in WRONG_CUTS
    }
    best_wrong_cut_label, best_wrong_cut = max(
        wrong_cut_families.items(),
        key=lambda item: item[1]["metrics"]["positive_signal_score"],
    )
    no_signal = local_unitary_no_signal_check(rows[N_SHELLS // 2]["rho"])

    all_families = {
        "candidate": candidate,
        "product_null_control": product,
        "phase_twist_randomization_control": phase_random,
        "shell_radius_order_scramble_control": scramble,
        "no_boundary_flattened_coupling_control": no_boundary,
        "no_chirality_symmetrized_orientation_control": no_chirality,
        "entanglement_angle_only_countermodel": angle_only,
        "same_scalar_mean_reversed_profile_control": same_scalar,
        **wrong_cut_families,
    }
    all_health = all(row["pass"] for family in all_families.values() for row in family["health"])

    candidate_profile_pass = bool(
        candidate["metrics"]["phi0_range"] > 0.15
        and candidate["metrics"]["gradient_mean_abs"] > 0.15
        and candidate["metrics"]["gradient_positive_fraction"] >= 0.875
        and candidate["metrics"]["radius_phi0_correlation"] > 0.98
    )
    product_pass = bool(product["metrics"]["positive_signal_score"] < 0.05 and product["metrics"]["phi0_max"] <= 1e-9)
    phase_pass = expected_degrade(candidate_score, phase_random["metrics"]["positive_signal_score"])
    scramble_pass = expected_degrade(candidate_score, scramble["metrics"]["positive_signal_score"])
    no_boundary_pass = expected_degrade(candidate_score, no_boundary["metrics"]["positive_signal_score"])
    no_chirality_pass = expected_degrade(candidate_score, no_chirality["metrics"]["positive_signal_score"])
    angle_only_profile_gap = gradient_profile_l2(candidate["phi0"], angle_only["phi0"])
    angle_only_pass = expected_degrade(candidate_score, angle_only["metrics"]["positive_signal_score"]) and angle_only_profile_gap > 0.20
    wrong_cut_gap = score_gap(candidate_score, best_wrong_cut["metrics"]["positive_signal_score"])
    wrong_cut_profile_gap = gradient_profile_l2(candidate["phi0"], best_wrong_cut["phi0"])
    wrong_cut_pass = wrong_cut_gap > 0.25 and wrong_cut_profile_gap > 0.20
    same_scalar_mean_gap = abs(candidate["metrics"]["phi0_mean"] - same_scalar["metrics"]["phi0_mean"])
    same_scalar_gradient_gap = gradient_profile_l2(candidate["gradient_dPhi0_dr"], same_scalar["gradient_dPhi0_dr"])
    scalar_only_pass = same_scalar_mean_gap < 1e-12 and same_scalar_gradient_gap > 1.0

    controls = {
        "product_null_control": build_control_row(
            "product/null control",
            product,
            candidate,
            "disentangled product states must not reproduce a positive candidate gradient",
            "productizing the declared cut flips coherent information negative and removes positive score",
            "product score < 0.05 and product max I_c <= 0",
            product_pass,
            {"control_phi0": product["phi0"]},
        ),
        "phase_twist_randomization_control": build_control_row(
            "phase randomization control",
            phase_random,
            candidate,
            "randomized phases/twists should kill coherent shell-gradient structure",
            "phase/twist-only randomization leaves the coherent-information profile essentially unchanged",
            "candidate score exceeds control score by > 0.25",
            phase_pass,
            {"profile_l2_gap": gradient_profile_l2(candidate["phi0"], phase_random["phi0"])},
        ),
        "shell_radius_order_scramble_control": build_control_row(
            "shell-radius randomization / shell-order scramble",
            scramble,
            candidate,
            "destroying radius order while reusing the same shell states should break monotone radius binding",
            "scrambling the shell order breaks the monotone radius profile",
            "candidate score exceeds control score by > 0.25",
            scramble_pass,
        ),
        "cut_swap_wrong_cut_control": {
            "label": "cut-swap / wrong-cut control",
            "expected": "alternate two-qubit cuts should not tie or beat the declared [0,1]|[2,3] cut",
            "observed": "the best alternate cut ties the declared coherent-information gradient profile",
            "pass_rule": "best alternate cut score is lower by > 0.25 and profile L2 gap > 0.20",
            "pass": bool(wrong_cut_pass),
            "declared_cut_score": candidate_score,
            "best_wrong_cut_label": best_wrong_cut_label,
            "best_wrong_cut_score": best_wrong_cut["metrics"]["positive_signal_score"],
            "declared_minus_best_wrong_cut_score": wrong_cut_gap,
            "best_wrong_cut_profile_l2_gap": wrong_cut_profile_gap,
            "wrong_cut_metrics": {label: family["metrics"] for label, family in wrong_cut_families.items()},
        },
        "no_boundary_flattened_coupling_control": build_control_row(
            "no-boundary control",
            no_boundary,
            candidate,
            "flattening boundary/coupling structure should remove the gradient signal",
            "fixed entanglement angle and flattened basis collapse the gradient",
            "candidate score exceeds control score by > 0.25",
            no_boundary_pass,
        ),
        "no_chirality_symmetrized_orientation_control": build_control_row(
            "no-chirality / symmetrized-orientation control",
            no_chirality,
            candidate,
            "erasing orientation/chirality/twist sign should reduce or kill the gradient signal",
            "symmetrized local shell orientation leaves the coherent-information profile unchanged",
            "candidate score exceeds control score by > 0.25",
            no_chirality_pass,
            {"profile_l2_gap": gradient_profile_l2(candidate["phi0"], no_chirality["phi0"])},
        ),
        "no_signal_control": no_signal,
        "scalar_only_insufficiency_control": {
            "label": "scalar-only insufficiency control",
            "expected": "a scalar mean/value alone is insufficient; profile/gradient discrimination is required",
            "observed": "same mean coherent information can carry the opposite gradient profile",
            "pass_rule": "mean gap < 1e-12 and gradient L2 gap > 1.0",
            "pass": bool(scalar_only_pass),
            "same_scalar_mean_gap": same_scalar_mean_gap,
            "same_scalar_gradient_profile_l2_gap": same_scalar_gradient_gap,
            "same_scalar_control_metrics": same_scalar["metrics"],
        },
        "entanglement_angle_only_countermodel": build_control_row(
            "entanglement-angle-only countermodel",
            angle_only,
            candidate,
            "removing shell/twist/chirality geometry while preserving only the entanglement-angle schedule should not reproduce the candidate",
            "fixed-basis states with the same entanglement-angle schedule reproduce the candidate profile",
            "candidate score exceeds control score by > 0.25 and profile L2 gap > 0.20",
            angle_only_pass,
            {"profile_l2_gap": angle_only_profile_gap, "control_phi0": angle_only["phi0"]},
        ),
    }

    required_control_keys = [
        "product_null_control",
        "phase_twist_randomization_control",
        "shell_radius_order_scramble_control",
        "cut_swap_wrong_cut_control",
        "no_boundary_flattened_coupling_control",
        "no_chirality_symmetrized_orientation_control",
        "no_signal_control",
        "scalar_only_insufficiency_control",
    ]
    required_controls_pass = all(bool(controls[key]["pass"]) for key in required_control_keys)
    adversarial_controls_pass = required_controls_pass and controls["entanglement_angle_only_countermodel"]["pass"]

    strongest_falsifier_first = [
        {
            "rank": 1,
            "name": "entanglement_angle_only_countermodel",
            "breaks": "shell/twist/chirality geometry load-bearing reading",
            "observed": "same entanglement-angle schedule on a fixed computational basis reproduces the candidate coherent-information profile",
            "candidate_score": candidate_score,
            "control_score": angle_only["metrics"]["positive_signal_score"],
            "profile_l2_gap": angle_only_profile_gap,
            "pass": bool(angle_only_pass),
        },
        {
            "rank": 2,
            "name": "cut_swap_wrong_cut_control",
            "breaks": "declared cut uniqueness",
            "observed": "alternate two-qubit cuts tie the declared cut in this pure rank-2 construction",
            "candidate_score": candidate_score,
            "best_wrong_cut_score": best_wrong_cut["metrics"]["positive_signal_score"],
            "profile_l2_gap": wrong_cut_profile_gap,
            "pass": bool(wrong_cut_pass),
        },
        {
            "rank": 3,
            "name": "phase_twist_randomization_control",
            "breaks": "phase/twist load-bearing reading",
            "observed": "coherent information is phase-blind for the reconstructed Schmidt-rank-2 pure-state profile",
            "candidate_score": candidate_score,
            "control_score": phase_random["metrics"]["positive_signal_score"],
            "profile_l2_gap": gradient_profile_l2(candidate["phi0"], phase_random["phi0"]),
            "pass": bool(phase_pass),
        },
        {
            "rank": 4,
            "name": "no_chirality_symmetrized_orientation_control",
            "breaks": "orientation/chirality load-bearing reading",
            "observed": "erasing local orientation/chirality leaves the coherent-information profile unchanged when the entanglement schedule is preserved",
            "candidate_score": candidate_score,
            "control_score": no_chirality["metrics"]["positive_signal_score"],
            "profile_l2_gap": gradient_profile_l2(candidate["phi0"], no_chirality["phi0"]),
            "pass": bool(no_chirality_pass),
        },
    ]

    blockers = []
    if not all_health:
        blockers.append("density_matrix_health_failed")
    if not candidate_profile_pass:
        blockers.append("candidate_gradient_profile_not_reproduced")
    if not required_controls_pass:
        failed_required = [key for key in required_control_keys if not controls[key]["pass"]]
        blockers.append("required_controls_failed:" + ",".join(failed_required))
    if not controls["entanglement_angle_only_countermodel"]["pass"]:
        blockers.append("entanglement_angle_only_countermodel_reproduces_candidate_profile")
    if PROMOTION_ALLOWED or FORMAL_ADMISSION_ALLOWED:
        blockers.append("promotion_or_formal_admission_boundary_failed")

    verdicts = {
        "independent_reimplementation": INDEPENDENT_REIMPLEMENTATION,
        "candidate_gradient_profile_present": candidate_profile_pass,
        "required_controls_pass": required_controls_pass,
        "adversarial_controls_pass": adversarial_controls_pass,
        "xi_shell_gradient_candidate_survived_adversarial_audit": bool(
            all_health and candidate_profile_pass and adversarial_controls_pass and not blockers
        ),
        "original_local_candidate_survived_preserved_as_comparison_only": load_original_summary().get("original_candidate_survived"),
        "no_signal_control_pass": bool(no_signal["pass"]),
        "scalar_value_only_insufficient": bool(scalar_only_pass),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
    }
    all_pass = bool(verdicts["xi_shell_gradient_candidate_survived_adversarial_audit"])

    positive = {
        "independent_density_trace_entropy_reimplementation_executed": {
            "pass": True,
            "implemented_locally": [
                "density_from_state",
                "partial_trace",
                "von_neumann_entropy",
                "cut_readout",
                "profile_metrics",
                "control_scoring",
            ],
            "imported_original_scout": False,
        },
        "matrix_health_all_candidate_and_controls": {
            "pass": all_health,
            "health_counts": {
                label: sum(1 for row in family["health"] if row["pass"])
                for label, family in all_families.items()
            },
            "total_per_family": N_SHELLS,
        },
        "candidate_gradient_profile_reimplemented": {
            "pass": candidate_profile_pass,
            "candidate_metrics": candidate["metrics"],
            "candidate_gradients": candidate["gradient_dPhi0_dr"],
        },
        "adversarial_audit_contract_passed": {
            "pass": all_pass,
            "reason": "all required controls plus the extra angle-only countermodel must pass for local audit survival",
        },
    }
    graveyard_companions = {
        key: value
        for key, value in controls.items()
        if key
        in {
            "product_null_control",
            "phase_twist_randomization_control",
            "shell_radius_order_scramble_control",
            "cut_swap_wrong_cut_control",
            "no_boundary_flattened_coupling_control",
            "no_chirality_symmetrized_orientation_control",
            "scalar_only_insufficiency_control",
            "entanglement_angle_only_countermodel",
        }
    }
    boundary = {
        "formal_scout_only_no_promotion": {
            "pass": PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
            "blocked_downstream_consumers": BLOCKED_DOWNSTREAM_CONSUMERS,
        },
        "no_signal_not_ftl_boundary": no_signal,
        "prior_scalar_value_xi_remains_insufficient": {
            "pass": bool(scalar_only_pass),
            "reason": "single scalar/mean value does not identify a shell-gradient profile",
            "same_scalar_mean_gap": same_scalar_mean_gap,
            "same_scalar_gradient_profile_l2_gap": same_scalar_gradient_gap,
        },
        "direct_build_no_subagents_runtime_boundary": {
            "pass": True,
            "reason": "user explicitly routed codex2 direct-build only; no spawn_agent, collab, subagents, child agents, or Wizard full-matrix used",
        },
    }

    variant_sections = {**positive, **graveyard_companions, **boundary}
    nearby_variants = {
        "total": len(variant_sections),
        "passed": sum(1 for row in variant_sections.values() if bool(row.get("pass"))),
        "failed": sorted(key for key, row in variant_sections.items() if not bool(row.get("pass"))),
        "variants": sorted(variant_sections),
    }

    operation_observable_pass_fail = {
        key: {
            "operation": row.get("label", key),
            "observable": row.get("observed", row.get("observable", "")),
            "pass": bool(row.get("pass")),
            "pass_rule": row.get("pass_rule", ""),
        }
        for key, row in controls.items()
    }
    operation_observable_pass_fail["candidate_gradient_profile"] = {
        "operation": "finite shell family -> coherent information profile",
        "observable": "monotone positive dPhi0/dr over declared shell radius",
        "pass": bool(candidate_profile_pass),
        "pass_rule": "phi0_range > 0.15, mean |gradient| > 0.15, positive fraction >= 0.875, radius correlation > 0.98",
    }

    original_summary = load_original_summary()
    comparison_summary = {
        **original_summary,
        "audit_all_pass": all_pass,
        "audit_candidate_score": candidate_score,
        "audit_candidate_phi0_range": candidate["metrics"]["phi0_range"],
        "audit_blocker_delta": (
            "prior result survived local controls; this stricter independent audit blocks promotion because "
            "angle-only, phase/twist-only, no-chirality, and wrong-cut controls reproduce or tie the profile"
        ),
    }

    next_hardening_tests = [
        "Replace pure Schmidt-rank-2 shell states with mixed/channel families where phases, twist, orientation, and boundary coupling are observable in I_c.",
        "Add a proof or symbolic check showing which state parameters coherent information can and cannot see under the declared cut.",
        "Require cut-unique observables: declared A|B cut must beat all alternate two-qubit cuts with a predeclared margin.",
        "Constrain the entanglement-angle schedule by independently measured shell geometry instead of inserting it as the load-bearing scalar.",
        "Rerun the prior bridge scout with phase-only, chirality-only, and angle-only ablations that preserve Schmidt coefficients.",
    ]

    return {
        "schema": SCHEMA,
        "name": NAME,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "independent_reimplementation": INDEPENDENT_REIMPLEMENTATION,
        "original_result_path": str(ORIGINAL_RESULT_PATH),
        "comparison_summary": comparison_summary,
        "target_claim": TARGET_CLAIM,
        "strongest_falsifier_first": strongest_falsifier_first,
        "operation_observable_pass_fail": operation_observable_pass_fail,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "blocked_downstream_consumers": BLOCKED_DOWNSTREAM_CONSUMERS,
        "blocked_consumers": BLOCKED_DOWNSTREAM_CONSUMERS,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "candidate_metrics": candidate["metrics"],
        "candidate_readouts": candidate["readouts"],
        "candidate_phi0": candidate["phi0"],
        "candidate_gradients": candidate["gradient_dPhi0_dr"],
        "control_suite_metrics": {
            key: value
            for key, value in controls.items()
            if key != "no_signal_control"
        },
        "control_readouts": {
            "product_null_control": product["readouts"],
            "phase_twist_randomization_control": phase_random["readouts"],
            "shell_radius_order_scramble_control": scramble["readouts"],
            "no_boundary_flattened_coupling_control": no_boundary["readouts"],
            "no_chirality_symmetrized_orientation_control": no_chirality["readouts"],
            "entanglement_angle_only_countermodel": angle_only["readouts"],
            "same_scalar_mean_reversed_profile_control": same_scalar["readouts"],
            "wrong_cut_controls": {label: family["readouts"] for label, family in wrong_cut_families.items()},
        },
        "verdicts": verdicts,
        "blockers": blockers,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": {
            "pass": True,
            "reason": "This is an unpromoted v5 formal scout/adversarial audit, not a canonical v4 probe.",
        },
        "next_hardening_tests": next_hardening_tests,
        "claim_boundary_note": (
            "This audit does not alter the prior result file. It preserves the prior local survival as comparison "
            "while blocking stronger shell-geometry, cut-unique, bridge, or admission readings."
        ),
        "plain_sentence": (
            "The independent audit reproduces a monotone coherent-information gradient, but the strongest controls "
            "show the profile is carried by the entanglement-angle schedule rather than by shell/twist/chirality "
            "or a unique declared cut; no promotion or formal admission is allowed."
        ),
        "shell_family": {
            "qubits": N_QUBITS,
            "shell_count": N_SHELLS,
            "declared_cut": {"A": DECLARED_A, "B": DECLARED_B},
            "wrong_cuts": WRONG_CUTS,
            "candidate_shell_params": candidate["shell_params"],
        },
    }


def write_receipt(result: dict[str, Any], elapsed_seconds: float) -> None:
    receipt = {
        "schema": "CODEX2_DIRECT_BUILD_RECEIPT_v1",
        "name": NAME,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "receipt_path": str(RECEIPT_PATH),
        "original_result_path": str(ORIGINAL_RESULT_PATH),
        "generated_at": time.time(),
        "elapsed_seconds": elapsed_seconds,
        "all_pass": result["all_pass"],
        "key_metrics": {
            "candidate_score": result["candidate_metrics"]["positive_signal_score"],
            "candidate_phi0_range": result["candidate_metrics"]["phi0_range"],
            "strongest_falsifier": result["strongest_falsifier_first"][0],
        },
        "blockers": result["blockers"],
        "claim_ceiling": CLAIM_CEILING,
        "no_staging_no_commit": True,
    }
    RECEIPT_PATH.write_text(json.dumps(as_jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = run_probe()
    result["generated_at"] = time.time()
    result["elapsed_seconds"] = result["generated_at"] - start
    RESULT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_receipt(result, time.time() - start)
    print(
        json.dumps(
            {
                "name": NAME,
                "all_pass": result["all_pass"],
                "result_path": str(RESULT_PATH),
                "receipt_path": str(RECEIPT_PATH),
                "candidate_score": result["candidate_metrics"]["positive_signal_score"],
                "strongest_falsifier": result["strongest_falsifier_first"][0]["name"],
                "blockers": result["blockers"],
                "promotion_allowed": PROMOTION_ALLOWED,
                "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
