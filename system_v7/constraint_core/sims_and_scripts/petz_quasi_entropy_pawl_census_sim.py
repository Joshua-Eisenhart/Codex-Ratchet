#!/usr/bin/env python3
"""Petz quasi-entropy pawl census on the terrain ratchet.

Additive scratch diagnostic.  Reuses the seeded 256-state grid, eight terrain
flows, and repaired fixed-point machinery from terrain_lyapunov_pawl_census_sim
without changing that source.

classification=scratch_diagnostic; promotion_allowed=false.
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np

from terrain_lyapunov_pawl_census_sim import (
    FLOW_SEGMENTS,
    FLOW_T,
    I2,
    NOISE_THRESHOLD,
    SEED,
    TERR,
    TERRAIN_LABELS,
    bloch,
    long_fixed_point,
    monotonicity_class,
    round_float,
    seeded_state_grid,
    terrain_flow,
)


HERE = Path(__file__).resolve().parent
RESULT_PATH = HERE / "petz_quasi_entropy_pawl_census_sim_results.json"

SIM_ID = "petz_quasi_entropy_pawl_census_sim"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

SPECTRAL_FLOOR = 1e-12

TOOL_MANIFEST = {
    "numpy": {
        "used": True,
        "reason": "2x2 density matrices, spectral Petz quasi-entropy formula, monotonicity census, controls",
    },
    "terrain_lyapunov_pawl_census_sim": {
        "used": True,
        "reason": "verbatim reuse of seeded_state_grid, terrain_flow, long_fixed_point, terrain constants, and monotonicity classifier",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "terrain_lyapunov_pawl_census_sim": "load_bearing",
}


@dataclass(frozen=True)
class QuasiEntropy:
    name: str
    family: str
    operator_convex_claim: bool
    impostor_control: bool
    formula: str
    f: Callable[[float], float]


def f_umegaki(t: float) -> float:
    if t <= 0.0:
        return 1.0
    return t * math.log(t) - t + 1.0


def centered_power_f(alpha: float) -> Callable[[float], float]:
    denom = alpha * (alpha - 1.0)

    def f(t: float) -> float:
        if t <= 0.0:
            return 1.0 / alpha
        return (t**alpha - 1.0 - alpha * (t - 1.0)) / denom

    return f


def f_sqrt_divergence(t: float) -> float:
    if t <= 0.0:
        return 1.0
    return (math.sqrt(t) - 1.0) ** 2


def f_wavy_nonconvex(t: float) -> float:
    if t <= 0.0:
        return 1.0
    centered = math.log(t)
    return (t - 1.0) ** 2 * (1.0 + 0.85 * math.sin(5.0 * centered))


QUASI_ENTROPIES = [
    QuasiEntropy(
        name="umegaki_x_log_x",
        family="operator_convex_petz",
        operator_convex_claim=True,
        impostor_control=False,
        formula="f(t)=t log(t)-t+1; affine-equivalent to U(rho||sigma)",
        f=f_umegaki,
    ),
    QuasiEntropy(
        name="petz_alpha_0_5_centered",
        family="operator_convex_petz_alpha",
        operator_convex_claim=True,
        impostor_control=False,
        formula="f_alpha(t)=(t^alpha-1-alpha(t-1))/(alpha(alpha-1)), alpha=0.5",
        f=centered_power_f(0.5),
    ),
    QuasiEntropy(
        name="petz_alpha_0_75_centered",
        family="operator_convex_petz_alpha",
        operator_convex_claim=True,
        impostor_control=False,
        formula="f_alpha(t)=(t^alpha-1-alpha(t-1))/(alpha(alpha-1)), alpha=0.75",
        f=centered_power_f(0.75),
    ),
    QuasiEntropy(
        name="petz_alpha_1_5_centered",
        family="operator_convex_petz_alpha",
        operator_convex_claim=True,
        impostor_control=False,
        formula="f_alpha(t)=(t^alpha-1-alpha(t-1))/(alpha(alpha-1)), alpha=1.5",
        f=centered_power_f(1.5),
    ),
    QuasiEntropy(
        name="petz_alpha_2_centered",
        family="operator_convex_petz_alpha",
        operator_convex_claim=True,
        impostor_control=False,
        formula="f_alpha(t)=(t^alpha-1-alpha(t-1))/(alpha(alpha-1)), alpha=2",
        f=centered_power_f(2.0),
    ),
    QuasiEntropy(
        name="sqrt_hellinger_divergence",
        family="operator_convex_sqrt",
        operator_convex_claim=True,
        impostor_control=False,
        formula="f(t)=(sqrt(t)-1)^2",
        f=f_sqrt_divergence,
    ),
    QuasiEntropy(
        name="impostor_petz_alpha_3_centered",
        family="non_operator_convex_impostor",
        operator_convex_claim=False,
        impostor_control=True,
        formula="same centered power form with alpha=3; outside operator-convex validity",
        f=centered_power_f(3.0),
    ),
    QuasiEntropy(
        name="impostor_wavy_nonconvex",
        family="non_operator_convex_impostor",
        operator_convex_claim=False,
        impostor_control=True,
        formula="f(t)=(t-1)^2*(1+0.85*sin(5*log(t)))",
        f=f_wavy_nonconvex,
    ),
]


def normalize_rho_local(rho: np.ndarray) -> np.ndarray:
    rho = 0.5 * (rho + rho.conj().T)
    return rho / np.trace(rho).real


def petz_quasi_entropy(rho: np.ndarray, sigma: np.ndarray, f: Callable[[float], float]) -> float:
    """Finite-dimensional Petz quasi-entropy via the relative modular spectrum."""
    rho = normalize_rho_local(rho)
    sigma = normalize_rho_local(sigma)
    rho_vals, rho_vecs = np.linalg.eigh(0.5 * (rho + rho.conj().T))
    sig_vals, sig_vecs = np.linalg.eigh(0.5 * (sigma + sigma.conj().T))
    rho_vals = np.clip(rho_vals.real, 0.0, None)
    sig_vals = np.clip(sig_vals.real, SPECTRAL_FLOOR, None)
    total = 0.0
    for i, lam in enumerate(rho_vals):
        for j, mu in enumerate(sig_vals):
            overlap = abs(np.vdot(rho_vecs[:, i], sig_vecs[:, j])) ** 2
            total += mu * f(float(lam / mu)) * float(overlap)
    if abs(total) < 1e-14:
        total = 0.0
    return float(total)


def trajectory_sequences(
    states: list[np.ndarray],
    fixed_points: dict[int, np.ndarray],
    entropy: QuasiEntropy,
) -> dict[int, list[list[float]]]:
    by_terrain = {}
    for ti in range(8):
        sigma = fixed_points[ti]
        trajectories = [terrain_flow(ti, state.copy()) for state in states]
        by_terrain[ti] = [
            [petz_quasi_entropy(rho, sigma, entropy.f) for rho in traj]
            for traj in trajectories
        ]
    return by_terrain


def per_family_census(states: list[np.ndarray], fixed_points: dict[int, np.ndarray]) -> dict[str, Any]:
    rows = []
    by_f: dict[str, dict[str, Any]] = {}
    for entropy in QUASI_ENTROPIES:
        per_terrain = {}
        for ti, seqs in trajectory_sequences(states, fixed_points, entropy).items():
            mono = monotonicity_class(seqs, threshold=NOISE_THRESHOLD)
            per_terrain[str(ti)] = mono
            rows.append(
                {
                    "f": entropy.name,
                    "family": entropy.family,
                    "operator_convex_claim": entropy.operator_convex_claim,
                    "impostor_control": entropy.impostor_control,
                    "terrain": ti,
                    "label": TERRAIN_LABELS[ti],
                    "kind": TERR[ti][1],
                    "classification": mono["classification"],
                    "direction": mono["direction"],
                    "pawl": mono["pawl"],
                    "max_violation": mono["max_violation_against_assigned_direction"],
                    "net_delta_min": mono["net_delta_min"],
                    "net_delta_max": mono["net_delta_max"],
                    "worst_case": mono["worst_case"],
                }
            )
            if not mono["pawl"]:
                per_terrain[str(ti)]["failure_label"] = TERRAIN_LABELS[ti]
        by_f[entropy.name] = {
            "family": entropy.family,
            "operator_convex_claim": entropy.operator_convex_claim,
            "impostor_control": entropy.impostor_control,
            "formula": entropy.formula,
            "all_terrains_pawl": all(item["pawl"] for item in per_terrain.values()),
            "terrain_verdicts": per_terrain,
            "failed_terrains": [
                int(ti) for ti, item in per_terrain.items() if not item["pawl"]
            ],
        }
    return {"rows": rows, "by_f": by_f}


def farthest_foreign_fixed_points(fixed_points: dict[int, np.ndarray]) -> dict[int, int]:
    fp_bloch = {ti: bloch(fp) for ti, fp in fixed_points.items()}
    choices = {}
    for ti in range(8):
        choices[ti] = max(
            (other for other in range(8) if other != ti),
            key=lambda other: float(np.linalg.norm(fp_bloch[ti] - fp_bloch[other])),
        )
    return choices


def wrong_fixed_point_control(
    states: list[np.ndarray],
    fixed_points: dict[int, np.ndarray],
) -> dict[str, Any]:
    foreign = farthest_foreign_fixed_points(fixed_points)
    rows = []
    by_f = {}
    for entropy in QUASI_ENTROPIES:
        lost_terrains = []
        for ti in range(8):
            sigma = fixed_points[foreign[ti]]
            trajectories = [terrain_flow(ti, state.copy()) for state in states]
            seqs = [
                [petz_quasi_entropy(rho, sigma, entropy.f) for rho in traj]
                for traj in trajectories
            ]
            mono = monotonicity_class(seqs, threshold=NOISE_THRESHOLD)
            lost = mono["classification"] != "monotone-decreasing"
            if lost:
                lost_terrains.append(ti)
            rows.append(
                {
                    "f": entropy.name,
                    "terrain": ti,
                    "native_label": TERRAIN_LABELS[ti],
                    "foreign_fixed_point_terrain": foreign[ti],
                    "foreign_label": TERRAIN_LABELS[foreign[ti]],
                    "classification": mono["classification"],
                    "lost_monotone_decreasing": bool(lost),
                    "max_violation": mono["max_violation_against_assigned_direction"],
                }
            )
        by_f[entropy.name] = {
            "lost_count": len(lost_terrains),
            "lost_terrains": lost_terrains,
            "breaks_this_family_member": bool(lost_terrains),
        }
    return {
        "control": "wrong_fixed_point_uses_farthest_foreign_fixed_point_by_bloch_distance",
        "rows": rows,
        "by_f": by_f,
        "breaks_every_family_member": all(item["breaks_this_family_member"] for item in by_f.values()),
    }


def summarize_verdict(census: dict[str, Any], wrong_control: dict[str, Any]) -> dict[str, Any]:
    op_failures = {}
    impostor_findings = {}
    for entropy in QUASI_ENTROPIES:
        item = census["by_f"][entropy.name]
        if entropy.operator_convex_claim and not item["all_terrains_pawl"]:
            op_failures[entropy.name] = item["failed_terrains"]
        if entropy.impostor_control:
            failed = item["failed_terrains"]
            impostor_findings[entropy.name] = {
                "fails_monotonicity_somewhere": bool(failed),
                "failed_terrains": failed,
                "loud_if_pawls_everywhere": None
                if failed
                else "IMPOSTOR_PAWLED_EVERYWHERE: finding about this gate, not a pass",
            }
    family_pawls = not op_failures
    return {
        "family_verdict": "family_pawls_uniformly" if family_pawls else "umegaki_special",
        "interpretation": (
            "Umegaki is installed within a forced Petz operator-convex family on this grid"
            if family_pawls
            else "At least one tested operator-convex Petz f failed the universal pawl census; see operator_convex_failures"
        ),
        "operator_convex_failures": op_failures,
        "impostor_controls": impostor_findings,
        "impostors_all_flip_somewhere": all(
            item["fails_monotonicity_somewhere"] for item in impostor_findings.values()
        ),
        "wrong_fixed_point_breaks_every_family_member": wrong_control["breaks_every_family_member"],
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "exit_policy": "always_exit_0_for_honest_verdict_mix",
    }


def build_result() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    states = seeded_state_grid(rng)
    fixed_points = {ti: long_fixed_point(ti) for ti in range(8)}
    census = per_family_census(states, fixed_points)
    wrong_control = wrong_fixed_point_control(states, fixed_points)
    verdict = summarize_verdict(census, wrong_control)
    return {
        "sim_id": SIM_ID,
        "name": "Petz quasi-entropy pawl census",
        "version": "1.0",
        "seed": SEED,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": "scratch_diagnostic; runs/pass-local-rerun only; no canonical, bridge, axis, manifold-completion, or admission claim",
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "source_spine": [
            "system_v7/constraint_core/sims_and_scripts/terrain_lyapunov_pawl_census_sim.py",
            "system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md",
            "system_v5/ops/AXES_TERRAINS_OPERATORS_MANIFOLD_SOURCE_LAYOUT_20260522.md",
            "system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md",
        ],
        "run_parameters": {
            "state_grid_size": len(states),
            "flow_segments": FLOW_SEGMENTS,
            "flow_t": FLOW_T,
            "noise_threshold": NOISE_THRESHOLD,
            "spectral_floor": SPECTRAL_FLOOR,
        },
        "fixed_points_bloch": {
            str(ti): [round_float(x, 12) for x in bloch(fixed_points[ti])] for ti in range(8)
        },
        "quasi_entropy_family": [
            {
                "name": entropy.name,
                "family": entropy.family,
                "operator_convex_claim": entropy.operator_convex_claim,
                "impostor_control": entropy.impostor_control,
                "formula": entropy.formula,
            }
            for entropy in QUASI_ENTROPIES
        ],
        "petz_formula": (
            "S_f(rho||sigma)=sum_{i,j} mu_j f(lambda_i/mu_j) |<rho_i|sigma_j>|^2 "
            "from spectral decompositions rho=sum_i lambda_i |rho_i><rho_i| and "
            "sigma=sum_j mu_j |sigma_j><sigma_j|"
        ),
        "f_x_terrain_census": census,
        "controls": {
            "wrong_fixed_point_control": wrong_control,
        },
        "verdict": verdict,
    }


def short_class(name: str) -> str:
    return name.replace("monotone-", "")


def print_census_table(result: dict[str, Any]) -> None:
    print("F x TERRAIN PETZ QUASI-ENTROPY PAWL CENSUS")
    print("threshold=%.1e; cell=class:max_assigned_direction_violation" % NOISE_THRESHOLD)
    header = "f".ljust(34) + " | " + " | ".join(f"t{ti}" for ti in range(8)) + " | verdict"
    print(header)
    print("-" * len(header))
    by_f = result["f_x_terrain_census"]["by_f"]
    for entropy in QUASI_ENTROPIES:
        item = by_f[entropy.name]
        cells = []
        for ti in range(8):
            mono = item["terrain_verdicts"][str(ti)]
            cells.append(f"{short_class(mono['classification'])}:{mono['max_violation_against_assigned_direction']:.1e}")
        verdict = "ALL_PAWL" if item["all_terrains_pawl"] else f"FAIL@{item['failed_terrains']}"
        print(f"{entropy.name:<34s} | " + " | ".join(f"{cell:<18s}" for cell in cells) + f" | {verdict}")


def print_controls(result: dict[str, Any]) -> None:
    wrong = result["controls"]["wrong_fixed_point_control"]
    print("\nCONTROLS")
    print("wrong-fixed-point: farthest foreign fixed point by Bloch distance")
    for entropy in QUASI_ENTROPIES:
        item = wrong["by_f"][entropy.name]
        print(
            f"  {entropy.name:<34s} lost={item['lost_count']}/8 "
            f"breaks_member={item['breaks_this_family_member']} terrains={item['lost_terrains']}"
        )


def print_verdict(result: dict[str, Any]) -> None:
    verdict = result["verdict"]
    print("\nVERDICT")
    print(f"family_verdict: {verdict['family_verdict']}")
    print(f"interpretation: {verdict['interpretation']}")
    print(f"operator_convex_failures: {verdict['operator_convex_failures']}")
    print(f"impostor_controls: {verdict['impostor_controls']}")
    print(f"impostors_all_flip_somewhere: {verdict['impostors_all_flip_somewhere']}")
    print(f"wrong_fixed_point_breaks_every_family_member: {verdict['wrong_fixed_point_breaks_every_family_member']}")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("PETZ QUASI-ENTROPY PAWL CENSUS")
    print("classification=scratch_diagnostic promotion_allowed=false formal_admission_allowed=false")
    print("seed=0; states=256; terrain source=terrain_lyapunov_pawl_census_sim.py")
    print("operator-convex candidates=6; impostor controls=2")
    print_census_table(result)
    print_controls(result)
    print_verdict(result)
    print(f"\nALL_GATES: HONEST_MIX_EXIT_0 -> {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
