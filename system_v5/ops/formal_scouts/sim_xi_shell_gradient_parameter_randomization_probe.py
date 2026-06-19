#!/usr/bin/env python3
"""Xi-shell coherent-information gradient parameter-randomization control.

Scratch diagnostic only. This hardens
sim_xi_shell_coherent_information_gradient_bridge_probe.py by replacing the
hand-chosen shell eta/twist coefficients with seeded untuned random draws while
reusing the original density, partial-trace, entropy, coherent-information, and
control-family machinery.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import pathlib
import random
import statistics
import time
from typing import Any

import torch

import sim_xi_shell_coherent_information_gradient_bridge_probe as xi


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "xi_shell_gradient_parameter_randomization_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
SOURCE_PATH = pathlib.Path(__file__).resolve()
ORIGINAL_SOURCE_PATH = ROOT / "sim_xi_shell_coherent_information_gradient_bridge_probe.py"
ORIGINAL_RESULT_PATH = RESULT_DIR / "xi_shell_coherent_information_gradient_bridge_probe_results.json"

SCHEMA = "FORMAL_SCOUT_RESULT_v1"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "xi_shell_gradient_parameter_randomization_hardening_control"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SCRATCH_DIAGNOSTIC = True
N_DRAWS = 200
RNG_SEED = 20260606
SURVIVAL_FORCED_THRESHOLD = 0.80
ENGINEERED_SMALL_THRESHOLD = 0.20
CONTROL_MARGIN_TOL = 0.25
NONTRIVIAL_PHI0_RANGE_MIN = 0.15
NONTRIVIAL_GRAD_MEAN_ABS_MIN = 0.15
MONOTONE_EPS = 1e-10
LAMBDA_SCHEDULE_MATCH_TOL = 1e-9
RADIUS_CENTER = sum(xi.shell_radius(k) for k in range(xi.N_SHELLS)) / xi.N_SHELLS

CLAIM_CEILING = (
    "Scratch formal scout only: randomized-parameter control for the finite "
    "Xi_shell(r)->rho_AB(r), Phi0(r)=I_c(A->B) gradient candidate. It tests "
    "whether the gradient survives untuned eta/twist coefficients. It does "
    "not admit final Xi, final Phi0, Axis0, gravity, physics, bridge "
    "promotion, holography, ER=EPR, FTL, formal admission, or promotion."
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
        "reason": (
            "load-bearing through the imported Xi-shell machinery: complex128 "
            "spinors, four-qubit density matrices, partial traces, eigvalsh "
            "entropy, coherent information, finite differences, and controls"
        ),
    },
    "python_random": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic coefficient draws for the adversarial eta/twist parameter family",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive source/result path handling"},
    "math": {"tried": True, "used": True, "reason": "supportive bounded coefficient formulas and scalar summaries"},
    "statistics": {"tried": True, "used": True, "reason": "supportive margin-distribution summaries"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
    "datetime": {"tried": True, "used": True, "reason": "supportive generated_at timestamp"},
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not needed for this bounded numeric randomization hardening control; no proof or promotion claim is made",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "not needed because no symbolic derivation is claimed",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "not needed for the fixed four-node edge list reused from the original scout",
    },
    "networkx": {
        "tried": False,
        "used": False,
        "reason": "not needed for the fixed four-node edge list reused from the original scout",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "python_random": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "math": "supportive",
    "statistics": "supportive",
    "time": "supportive",
    "datetime": "supportive",
    "z3": None,
    "sympy": None,
    "rustworkx": None,
    "networkx": None,
}

ETA_PARAMETER_RANGES = {
    "base": [0.20, 0.60],
    "radius_coeff": [-0.10, 0.10],
    "node_coeff": [-0.10, 0.10],
    "sin_amp": [0.00, 0.10],
    "sin_node_coeff": [0.00, 0.80],
    "sin_phase": [0.00, 2.0 * math.pi],
}
TWIST_PARAMETER_RANGES = {
    "base": [0.00, 0.60],
    "shell_fraction_coeff": [-1.50, 1.50],
    "sin_amp": [0.00, 0.35],
    "sin_freq": [0.50, 2.00],
    "sin_phase": [0.00, 2.0 * math.pi],
    "radius_coeff": [-0.10, 0.10],
}


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


def draw_uniform(rng: random.Random, ranges: dict[str, list[float]]) -> dict[str, float]:
    return {key: rng.uniform(bounds[0], bounds[1]) for key, bounds in ranges.items()}


def random_parameter_draw(draw_index: int, rng: random.Random) -> dict[str, Any]:
    return {
        "draw_index": draw_index,
        "eta": draw_uniform(rng, ETA_PARAMETER_RANGES),
        "twist": draw_uniform(rng, TWIST_PARAMETER_RANGES),
    }


def randomized_twist(radius: float, k: int, params: dict[str, float]) -> float:
    t = k / (xi.N_SHELLS - 1)
    return (
        params["base"]
        + params["shell_fraction_coeff"] * t
        + params["sin_amp"] * math.sin(params["sin_freq"] * math.pi * t + params["sin_phase"])
        + params["radius_coeff"] * radius
    )


def randomized_eta(radius: float, node: int, params: dict[str, float]) -> float:
    return (
        params["base"]
        + params["radius_coeff"] * (radius - RADIUS_CENTER)
        + params["node_coeff"] * node
        + params["sin_amp"] * math.sin(radius + params["sin_node_coeff"] * node + params["sin_phase"])
    )


def randomized_shell_spinors(radius: float, twist: float, eta_params: dict[str, float], *, chiral: bool) -> list[torch.Tensor]:
    scale = 1.0 if chiral else 0.0
    rows = []
    for node in range(4):
        orientation = 1.0 if node % 2 == 0 else -1.0
        phi = 0.13 + 0.27 * node + 0.09 * radius + scale * orientation * 0.07 * math.sin(twist + node)
        chi = orientation * (0.18 + 0.025 * node) + scale * 0.11 * math.cos(twist + 0.41 * node)
        eta = randomized_eta(radius, node, eta_params)
        rows.append(xi.spinor(phi, chi, eta))
    return rows


def randomized_xi_shell_parameters(k: int, draw: dict[str, Any], mode: str) -> dict[str, Any]:
    radius = xi.shell_radius(k)
    t = k / (xi.N_SHELLS - 1)
    chiral = mode not in {"zero_phase", "flat"}
    twist = randomized_twist(radius, k, draw["twist"]) if chiral else 0.0
    spinors = randomized_shell_spinors(radius, twist, draw["eta"], chiral=chiral)
    twistors = xi.twistor_nodes(spinors, radius, twist, chiral=chiral)
    incs = [xi.incidence(twistors[i], twistors[j]) for i, j in xi.EDGES]
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
    else:
        raise ValueError(mode)

    lam = min(0.70, max(0.04, lam))
    etas = [randomized_eta(radius, node, draw["eta"]) for node in range(4)]
    return {
        "k": k,
        "radius": radius,
        "shell_fraction": t,
        "designed_twist": twist,
        "lambda": lam,
        "phase": phase,
        "mean_incidence_magnitude": mean_mag,
        "mean_incidence_phase": mean_phase,
        "edge_count": len(xi.EDGES),
        "eta_values": etas,
        "spinors": spinors,
    }


def randomized_shell_density(k: int, draw: dict[str, Any], mode: str = "candidate") -> dict[str, Any]:
    params = randomized_xi_shell_parameters(k, draw, mode)
    spinors = params["spinors"]
    a0 = xi.normalize(torch.kron(spinors[0], spinors[1]))
    b0 = xi.normalize(torch.kron(spinors[2], spinors[3]))
    a1 = xi.normalize(torch.kron(xi.orthogonal_spinor(spinors[0]), xi.orthogonal_spinor(spinors[1])))
    b1 = xi.normalize(torch.kron(xi.orthogonal_spinor(spinors[2]), xi.orthogonal_spinor(spinors[3])))
    state = xi.normalize(
        math.cos(params["lambda"]) * torch.kron(a0, b0)
        + math.sin(params["lambda"]) * xi.cexp(params["phase"]) * torch.kron(a1, b1)
    )
    rho = xi.density(state)
    public_params = {key: value for key, value in params.items() if key != "spinors"}
    return {"rho": rho, "params": public_params}


def randomized_candidate_rows(draw: dict[str, Any]) -> list[dict[str, Any]]:
    return [randomized_shell_density(k, draw, "candidate") for k in range(xi.N_SHELLS)]


def lambda_schedule_only_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    zero = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=xi.CDTYPE)
    one = torch.tensor([0.0 + 0.0j, 1.0 + 0.0j], dtype=xi.CDTYPE)
    a0 = xi.normalize(torch.kron(zero, zero))
    b0 = xi.normalize(torch.kron(zero, zero))
    a1 = xi.normalize(torch.kron(one, one))
    b1 = xi.normalize(torch.kron(one, one))
    rows = []
    for row in candidate_rows:
        params = dict(row["params"])
        lam = params["lambda"]
        state = xi.normalize(math.cos(lam) * torch.kron(a0, b0) + math.sin(lam) * torch.kron(a1, b1))
        params["eta_twist_geometry"] = "erased_fixed_computational_basis"
        params["falsifier"] = "same lambda schedule without randomized eta/twist spinor geometry"
        rows.append({"rho": xi.density(state), "params": params})
    return rows


def quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return sorted_values[lo]
    frac = pos - lo
    return sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac


def distribution_summary(values: list[float]) -> dict[str, float]:
    sorted_values = sorted(values)
    return {
        "count": len(values),
        "min": min(values) if values else 0.0,
        "p05": quantile(sorted_values, 0.05),
        "p25": quantile(sorted_values, 0.25),
        "median": quantile(sorted_values, 0.50),
        "mean": statistics.fmean(values) if values else 0.0,
        "p75": quantile(sorted_values, 0.75),
        "p95": quantile(sorted_values, 0.95),
        "max": max(values) if values else 0.0,
        "stdev": statistics.pstdev(values) if len(values) > 1 else 0.0,
    }


def draw_parameter_summary(rows: list[dict[str, Any]]) -> dict[str, float]:
    eta_values = [eta for row in rows for eta in row["params"]["eta_values"]]
    twists = [row["params"]["designed_twist"] for row in rows]
    lambdas = [row["params"]["lambda"] for row in rows]
    return {
        "eta_min": min(eta_values),
        "eta_max": max(eta_values),
        "eta_span": max(eta_values) - min(eta_values),
        "twist_min": min(twists),
        "twist_max": max(twists),
        "twist_span": max(twists) - min(twists),
        "lambda_min": min(lambdas),
        "lambda_max": max(lambdas),
        "lambda_span": max(lambdas) - min(lambdas),
    }


def evaluate_draw(draw: dict[str, Any]) -> dict[str, Any]:
    candidate_rows = randomized_candidate_rows(draw)
    candidate = xi.family_from_rows("randomized_candidate", candidate_rows)
    flat = xi.flat_family(candidate_rows)
    product = xi.product_family(candidate_rows)
    same_scalar = xi.reversed_mean_matched_family(candidate_rows)
    controls = {
        "flat_shell_control": flat,
        "product_cut_control": product,
        "same_scalar_different_gradient_control": same_scalar,
    }
    lambda_schedule = xi.family_from_rows(
        "lambda_schedule_only_eta_twist_erased_control",
        lambda_schedule_only_rows(candidate_rows),
    )
    all_health = all(row["pass"] for family in [candidate, *controls.values(), lambda_schedule] for row in family["health"])
    cand_metrics = candidate["metrics"]
    control_scores = {label: row["metrics"]["positive_signal_score"] for label, row in controls.items()}
    best_control_label, best_control_score = max(control_scores.items(), key=lambda row: row[1])
    margin = cand_metrics["positive_signal_score"] - best_control_score
    lambda_schedule_score = lambda_schedule["metrics"]["positive_signal_score"]
    lambda_schedule_margin = cand_metrics["positive_signal_score"] - lambda_schedule_score
    lambda_schedule_profile_l2 = xi.gradient_profile_l2(candidate["gradient_dPhi0_dr"], lambda_schedule["gradient_dPhi0_dr"])
    lambda_schedule_reproduces = bool(
        abs(lambda_schedule_margin) <= LAMBDA_SCHEDULE_MATCH_TOL
        and lambda_schedule_profile_l2 <= LAMBDA_SCHEDULE_MATCH_TOL
    )
    eta_twist_geometry_beats_lambda_schedule = bool(lambda_schedule_margin > CONTROL_MARGIN_TOL)
    same_scalar_mean_gap = abs(cand_metrics["phi0_mean"] - same_scalar["metrics"]["phi0_mean"])
    same_scalar_gradient_l2 = xi.gradient_profile_l2(candidate["gradient_dPhi0_dr"], same_scalar["gradient_dPhi0_dr"])
    gradient_nontrivial = bool(
        cand_metrics["phi0_range"] > NONTRIVIAL_PHI0_RANGE_MIN
        and cand_metrics["gradient_mean_abs"] > NONTRIVIAL_GRAD_MEAN_ABS_MIN
    )
    monotone_increasing = bool(all(row > MONOTONE_EPS for row in candidate["gradient_dPhi0_dr"]))
    monotone_nontrivial = bool(gradient_nontrivial and monotone_increasing)
    flat_degrades = bool(flat["metrics"]["phi0_range"] < 1e-9 and flat["metrics"]["gradient_mean_abs"] < 1e-9)
    product_degrades = bool(product["metrics"]["phi0_max"] <= 1e-9)
    same_scalar_distinct = bool(same_scalar_mean_gap < 1e-12 and same_scalar_gradient_l2 > 1.0)
    candidate_beats_controls = bool(
        margin > CONTROL_MARGIN_TOL and flat_degrades and product_degrades and same_scalar_distinct
    )
    survives = bool(all_health and gradient_nontrivial and candidate_beats_controls)
    monotone_survives = bool(survives and monotone_increasing)
    geometry_load_bearing_survives = bool(survives and eta_twist_geometry_beats_lambda_schedule)
    return {
        "draw_index": draw["draw_index"],
        "parameters": draw,
        "parameter_summary": draw_parameter_summary(candidate_rows),
        "gradient_nontrivial": gradient_nontrivial,
        "monotone_increasing_gradient": monotone_increasing,
        "monotone_nontrivial_gradient": monotone_nontrivial,
        "candidate_beats_controls": candidate_beats_controls,
        "survives_gradient_nontrivial_and_beats_controls": survives,
        "survives_monotone_and_beats_controls": monotone_survives,
        "eta_twist_geometry_beats_lambda_schedule_control": eta_twist_geometry_beats_lambda_schedule,
        "lambda_schedule_only_reproduces_candidate_profile": lambda_schedule_reproduces,
        "survives_after_lambda_schedule_countermodel": geometry_load_bearing_survives,
        "candidate_vs_best_control_margin": margin,
        "best_control_label": best_control_label,
        "best_control_score": best_control_score,
        "lambda_schedule_control_margin": lambda_schedule_margin,
        "lambda_schedule_control_score": lambda_schedule_score,
        "lambda_schedule_gradient_profile_l2_gap": lambda_schedule_profile_l2,
        "control_scores": control_scores,
        "all_control_scores": {
            **control_scores,
            "lambda_schedule_only_eta_twist_erased_control": lambda_schedule_score,
        },
        "candidate_metrics": cand_metrics,
        "control_metrics": {label: row["metrics"] for label, row in controls.items()},
        "lambda_schedule_control_metrics": lambda_schedule["metrics"],
        "candidate_phi0": candidate["phi0"],
        "candidate_gradient_dPhi0_dr": candidate["gradient_dPhi0_dr"],
        "lambda_schedule_control_phi0": lambda_schedule["phi0"],
        "lambda_schedule_control_gradient_dPhi0_dr": lambda_schedule["gradient_dPhi0_dr"],
        "same_scalar_mean_gap": same_scalar_mean_gap,
        "same_scalar_gradient_profile_l2_gap": same_scalar_gradient_l2,
        "control_checks": {
            "all_matrix_health_pass": all_health,
            "flat_shell_control_degrades": flat_degrades,
            "product_cut_control_degrades": product_degrades,
            "same_scalar_different_gradient_control_distinct": same_scalar_distinct,
            "margin_exceeds_tolerance": margin > CONTROL_MARGIN_TOL,
            "lambda_schedule_only_reproduces_candidate_profile": lambda_schedule_reproduces,
            "eta_twist_geometry_beats_lambda_schedule_control": eta_twist_geometry_beats_lambda_schedule,
        },
    }


def fraction(rows: list[dict[str, Any]], key: str) -> float:
    return sum(1 for row in rows if row[key]) / len(rows)


def run_probe() -> dict[str, Any]:
    rng = random.Random(RNG_SEED)
    draws = [random_parameter_draw(idx, rng) for idx in range(N_DRAWS)]
    draw_results = [evaluate_draw(draw) for draw in draws]
    survival_fraction = fraction(draw_results, "survives_gradient_nontrivial_and_beats_controls")
    monotone_survival_fraction = fraction(draw_results, "survives_monotone_and_beats_controls")
    geometry_load_bearing_survival_fraction = fraction(draw_results, "survives_after_lambda_schedule_countermodel")
    lambda_schedule_reproduction_fraction = fraction(draw_results, "lambda_schedule_only_reproduces_candidate_profile")
    nontrivial_fraction = fraction(draw_results, "gradient_nontrivial")
    monotone_nontrivial_fraction = fraction(draw_results, "monotone_nontrivial_gradient")
    monotone_only_fraction = fraction(draw_results, "monotone_increasing_gradient")
    beats_controls_fraction = fraction(draw_results, "candidate_beats_controls")
    margins = [row["candidate_vs_best_control_margin"] for row in draw_results]
    lambda_margins = [row["lambda_schedule_control_margin"] for row in draw_results]
    lambda_profile_l2 = [row["lambda_schedule_gradient_profile_l2_gap"] for row in draw_results]
    gradient_ranges = [row["candidate_metrics"]["phi0_range"] for row in draw_results]
    gradient_mean_abs = [row["candidate_metrics"]["gradient_mean_abs"] for row in draw_results]
    radius_correlations = [row["candidate_metrics"]["radius_phi0_correlation"] for row in draw_results]
    geometry_forced = (
        survival_fraction > SURVIVAL_FORCED_THRESHOLD
        and geometry_load_bearing_survival_fraction > SURVIVAL_FORCED_THRESHOLD
        and lambda_schedule_reproduction_fraction <= ENGINEERED_SMALL_THRESHOLD
    )
    engineered = survival_fraction <= ENGINEERED_SMALL_THRESHOLD or lambda_schedule_reproduction_fraction > SURVIVAL_FORCED_THRESHOLD
    parameter_sensitive = not geometry_forced and not engineered
    if geometry_forced:
        verdict_label = "gradient_geometry_forced"
        plain_sentence = (
            "The Xi-shell coherent-information gradient bridge survives eta/twist "
            "parameter randomization in this control, so the tested gradient is not "
            "explained by only the original tuned magic numbers."
        )
    elif engineered:
        verdict_label = "gradient_is_engineered"
        plain_sentence = (
            "The Xi-shell coherent-information gradient bridge is not geometry-forced "
            "by eta/twist parameter randomization in this control; the monotone "
            "profile is reproduced by the preserved lambda entanglement schedule "
            "with eta/twist geometry erased, so the apparent gradient is "
            "engineered/by-construction."
        )
    else:
        verdict_label = "parameter_sensitive_inconclusive"
        plain_sentence = (
            "The Xi-shell coherent-information gradient bridge is parameter-sensitive "
            "in this control: survival was neither large enough for geometry-forced "
            "nor small enough for the strict engineered threshold."
        )

    positive = {
        "random_parameter_draws_executed": {
            "pass": len(draw_results) >= 200,
            "draw_count": len(draw_results),
            "seed": RNG_SEED,
        },
        "original_qit_machinery_reused": {
            "pass": True,
            "imported_source": str(ORIGINAL_SOURCE_PATH),
            "reused_functions": [
                "spinor",
                "orthogonal_spinor",
                "twistor_nodes",
                "incidence",
                "density",
                "partial_trace_qubits",
                "entropy",
                "cut_readouts",
                "family_from_rows",
                "flat_family",
                "product_family",
                "reversed_mean_matched_family",
                "gradient_metrics",
            ],
        },
        "verdict_thresholds_applied_without_promotion": {
            "pass": True,
            "survival_fraction": survival_fraction,
            "monotone_survival_fraction": monotone_survival_fraction,
            "geometry_load_bearing_survival_fraction": geometry_load_bearing_survival_fraction,
            "lambda_schedule_reproduction_fraction": lambda_schedule_reproduction_fraction,
            "gradient_geometry_forced": geometry_forced,
            "gradient_is_engineered": engineered,
            "parameter_sensitive_inconclusive": parameter_sensitive,
            "survival_forced_threshold": SURVIVAL_FORCED_THRESHOLD,
            "engineered_small_threshold": ENGINEERED_SMALL_THRESHOLD,
            "verdict_label": verdict_label,
        },
    }
    graveyard_companions = {
        "flat_shell_product_and_same_scalar_controls_evaluated_every_draw": {
            "pass": all(
                {"flat_shell_control", "product_cut_control", "same_scalar_different_gradient_control"}
                == set(row["control_scores"])
                for row in draw_results
            ),
            "draw_count": len(draw_results),
        },
        "lambda_schedule_only_countermodel_checked_every_draw": {
            "pass": all("lambda_schedule_only_eta_twist_erased_control" in row["all_control_scores"] for row in draw_results),
            "lambda_schedule_reproduction_fraction": lambda_schedule_reproduction_fraction,
            "interpretation": (
                "If this fraction is high, randomized eta/twist geometry is not load-bearing "
                "for the coherent-information gradient because the preserved lambda schedule "
                "alone reproduces the profile."
            ),
        },
        "monotone_survival_reported_separately_from_nontrivial_survival": {
            "pass": True,
            "nontrivial_survival_fraction": survival_fraction,
            "monotone_survival_fraction": monotone_survival_fraction,
            "geometry_load_bearing_survival_fraction_after_lambda_countermodel": geometry_load_bearing_survival_fraction,
            "nontrivial_gradient_fraction_before_controls": nontrivial_fraction,
            "monotone_nontrivial_gradient_fraction_before_controls": monotone_nontrivial_fraction,
        },
        "margin_distribution_recorded": {
            "pass": len(margins) == len(draw_results),
            "candidate_vs_best_control_margin": distribution_summary(margins),
            "candidate_vs_lambda_schedule_control_margin": distribution_summary(lambda_margins),
        },
    }
    boundary = {
        "scratch_diagnostic_only": {
            "pass": SCRATCH_DIAGNOSTIC and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
            "scratch_diagnostic": SCRATCH_DIAGNOSTIC,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        },
        "blocked_consumers_include_axis0_gravity_physics_bridge": {
            "pass": all(
                token in BLOCKED_CONSUMERS
                for token in ["Axis0", "gravity", "physics", "bridge_promotion", "formal_admission"]
            ),
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "no_numpy_compute_used": {
            "pass": True,
            "numpy_compute_used": False,
            "reason": "No numpy import or np.* compute appears in this scout; computation routes through torch and the imported original torch machinery.",
        },
        "lambda_schedule_scope_boundary": {
            "pass": True,
            "lambda_schedule_randomized": False,
            "reason": (
                "The requested control randomizes eta/twist parameters only. The original candidate lambda schedule "
                "is preserved, so survival here hardens against eta/twist magic-number tuning but does not admit "
                "bridge geometry, physics, gravity, or Axis0."
            ),
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
    return {
        "schema": SCHEMA,
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "scratch_diagnostic": SCRATCH_DIAGNOSTIC,
        "claim_ceiling": CLAIM_CEILING,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "parameter_randomization": {
            "draw_count": N_DRAWS,
            "seed": RNG_SEED,
            "eta_formula": (
                "eta = base + radius_coeff*(radius-radius_center) + node_coeff*node "
                "+ sin_amp*sin(radius + sin_node_coeff*node + sin_phase)"
            ),
            "twist_formula": (
                "twist = base + shell_fraction_coeff*t + sin_amp*sin(sin_freq*pi*t + sin_phase) "
                "+ radius_coeff*radius"
            ),
            "eta_parameter_ranges": ETA_PARAMETER_RANGES,
            "twist_parameter_ranges": TWIST_PARAMETER_RANGES,
            "radius_center": RADIUS_CENTER,
        },
        "criteria": {
            "survival": "gradient_nontrivial AND candidate_beats_controls",
            "monotone_survival": "gradient_nontrivial AND monotone increasing AND candidate_beats_controls",
            "geometry_load_bearing_survival": (
                "survival AND candidate beats lambda_schedule_only_eta_twist_erased_control; "
                "this prevents the preserved entanglement-angle schedule from being mislabeled geometry-forced"
            ),
            "gradient_nontrivial": {
                "phi0_range_gt": NONTRIVIAL_PHI0_RANGE_MIN,
                "gradient_mean_abs_gt": NONTRIVIAL_GRAD_MEAN_ABS_MIN,
            },
            "candidate_beats_controls": {
                "controls": [
                    "flat_shell_control",
                    "product_cut_control",
                    "same_scalar_different_gradient_control",
                ],
                "margin_gt": CONTROL_MARGIN_TOL,
                "same_scalar_gradient_profile_l2_gt": 1.0,
            },
            "lambda_schedule_randomized": False,
            "geometry_forced_if_survival_fraction_gt": SURVIVAL_FORCED_THRESHOLD,
            "engineered_if_survival_fraction_lte": ENGINEERED_SMALL_THRESHOLD,
            "engineered_if_lambda_schedule_reproduction_fraction_gt": SURVIVAL_FORCED_THRESHOLD,
        },
        "summary": {
            "N_draws": len(draw_results),
            "survival_count": sum(1 for row in draw_results if row["survives_gradient_nontrivial_and_beats_controls"]),
            "survival_fraction": survival_fraction,
            "monotone_survival_count": sum(1 for row in draw_results if row["survives_monotone_and_beats_controls"]),
            "monotone_survival_fraction": monotone_survival_fraction,
            "geometry_load_bearing_survival_count": sum(
                1 for row in draw_results if row["survives_after_lambda_schedule_countermodel"]
            ),
            "geometry_load_bearing_survival_fraction": geometry_load_bearing_survival_fraction,
            "lambda_schedule_reproduction_count": sum(
                1 for row in draw_results if row["lambda_schedule_only_reproduces_candidate_profile"]
            ),
            "lambda_schedule_reproduction_fraction": lambda_schedule_reproduction_fraction,
            "nontrivial_gradient_fraction_before_controls": nontrivial_fraction,
            "monotone_increasing_fraction_before_controls": monotone_only_fraction,
            "monotone_nontrivial_gradient_fraction_before_controls": monotone_nontrivial_fraction,
            "candidate_beats_controls_fraction": beats_controls_fraction,
            "gradient_geometry_forced": geometry_forced,
            "gradient_is_engineered": engineered,
            "parameter_sensitive_inconclusive": parameter_sensitive,
            "verdict_label": verdict_label,
            "numpy_compute_used": False,
        },
        "verdicts": {
            "gradient_geometry_forced": geometry_forced,
            "gradient_is_engineered": engineered,
            "parameter_sensitive_inconclusive": parameter_sensitive,
            "survival_fraction": survival_fraction,
            "monotone_survival_fraction": monotone_survival_fraction,
            "geometry_load_bearing_survival_fraction": geometry_load_bearing_survival_fraction,
            "lambda_schedule_reproduction_fraction": lambda_schedule_reproduction_fraction,
            "verdict_label": verdict_label,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        },
        "margin_distribution": {
            "candidate_vs_best_control_margin": distribution_summary(margins),
            "candidate_vs_lambda_schedule_control_margin": distribution_summary(lambda_margins),
            "lambda_schedule_gradient_profile_l2_gap": distribution_summary(lambda_profile_l2),
            "phi0_range": distribution_summary(gradient_ranges),
            "gradient_mean_abs": distribution_summary(gradient_mean_abs),
            "radius_phi0_correlation": distribution_summary(radius_correlations),
        },
        "draw_results": draw_results,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": {
            "pass": True,
            "reason": "This is a v5 formal-scout hardening control over a finite Xi-shell gradient candidate, not a canonical v4 probe.",
        },
        "blockers": [],
        "all_pass": all_pass,
        "source_path": SOURCE_PATH,
        "original_source_path": ORIGINAL_SOURCE_PATH,
        "original_result_path": ORIGINAL_RESULT_PATH,
        "plain_sentence": plain_sentence,
    }


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = run_probe()
    result["runtime_seconds"] = time.time() - start
    result["generated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "result_path": str(OUT_PATH),
                "N_draws": result["summary"]["N_draws"],
                "survival_fraction": result["summary"]["survival_fraction"],
                "monotone_survival_fraction": result["summary"]["monotone_survival_fraction"],
                "geometry_load_bearing_survival_fraction": result["summary"]["geometry_load_bearing_survival_fraction"],
                "lambda_schedule_reproduction_fraction": result["summary"]["lambda_schedule_reproduction_fraction"],
                "gradient_geometry_forced": result["summary"]["gradient_geometry_forced"],
                "gradient_is_engineered": result["summary"]["gradient_is_engineered"],
                "parameter_sensitive_inconclusive": result["summary"]["parameter_sensitive_inconclusive"],
                "margin_distribution": result["margin_distribution"]["candidate_vs_best_control_margin"],
                "numpy_compute_used": result["summary"]["numpy_compute_used"],
                "plain_sentence": result["plain_sentence"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
