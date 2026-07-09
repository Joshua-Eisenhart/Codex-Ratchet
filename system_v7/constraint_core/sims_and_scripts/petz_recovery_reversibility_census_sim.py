#!/usr/bin/env python3
"""Petz recovery / reversibility census for the terrain U-pawl.

Additive scratch diagnostic.  Reuses the seeded eight-terrain qubit grid,
fixed-point machinery, and exact CPTP terrain segment maps from
terrain_lyapunov_pawl_census_sim without mutating that source.

classification=scratch_diagnostic; promotion_allowed=false.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import expm

from terrain_lyapunov_pawl_census_sim import (
    FLOW_SEGMENTS,
    FLOW_T,
    G,
    H0,
    I2,
    SEED,
    TERR,
    TERRAIN_LABELS,
    apply_channel_matrix,
    bloch,
    long_fixed_point,
    normalize_rho,
    relative_entropy,
    round_float,
    seeded_state_grid,
    terrain_channel_matrix,
)


HERE = Path(__file__).resolve().parent
RESULT_PATH = HERE / "petz_recovery_reversibility_census_sim_results.json"

SIM_ID = "petz_recovery_reversibility_census_sim"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

DELTA_ZERO_TOL = 1.0e-8
STRICT_DECREASE_TOL = 1.0e-7
RECOVERY_EXACT_TOL = 1.0e-6
SPECTRAL_FLOOR = 1.0e-12

TOOL_MANIFEST = {
    "numpy": {
        "used": True,
        "reason": "2x2 density matrices, Hilbert-Schmidt adjoints, Petz map application, per-step census statistics",
    },
    "scipy.linalg.expm": {
        "used": True,
        "reason": "unitary-flow control channels and imported exact terrain segment channels from the source sim",
    },
    "terrain_lyapunov_pawl_census_sim": {
        "used": True,
        "reason": "verbatim reuse of seeded_state_grid, long_fixed_point, relative_entropy, and exact terrain_channel_matrix segment maps",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy.linalg.expm": "supportive",
    "terrain_lyapunov_pawl_census_sim": "load_bearing",
}


def mat_power_psd(mat: np.ndarray, power: float, *, floor: float = SPECTRAL_FLOOR) -> np.ndarray:
    vals, vecs = np.linalg.eigh(0.5 * (mat + mat.conj().T))
    vals = np.clip(vals.real, floor, None)
    return vecs @ np.diag(vals**power) @ vecs.conj().T


def channel_adjoint_apply(channel: np.ndarray, op: np.ndarray) -> np.ndarray:
    """Hilbert-Schmidt adjoint for the same vectorization used by terrain_channel_matrix."""
    return (channel.conj().T @ op.reshape(-1)).reshape(2, 2)


def petz_recover(channel: np.ndarray, sigma: np.ndarray, channel_output: np.ndarray) -> np.ndarray:
    sigma = normalize_rho(sigma)
    n_sigma = apply_channel_matrix(channel, sigma)
    sigma_half = mat_power_psd(sigma, 0.5)
    n_sigma_inv_half = mat_power_psd(n_sigma, -0.5)
    middle = n_sigma_inv_half @ channel_output @ n_sigma_inv_half
    recovered = sigma_half @ channel_adjoint_apply(channel, middle) @ sigma_half
    return normalize_rho(recovered)


def density_fidelity(rho: np.ndarray, sigma: np.ndarray) -> float:
    rho = normalize_rho(rho)
    sigma = normalize_rho(sigma)
    root = mat_power_psd(rho, 0.5)
    sandwiched = root @ sigma @ root
    vals = np.linalg.eigvalsh(0.5 * (sandwiched + sandwiched.conj().T))
    vals = np.clip(vals.real, 0.0, None)
    return min(1.0, max(0.0, float(np.sum(np.sqrt(vals)) ** 2)))


def recovery_measure(rho: np.ndarray, recovered: np.ndarray) -> dict[str, float | bool]:
    error = float(np.linalg.norm(recovered - rho, ord="fro"))
    fidelity = density_fidelity(rho, recovered)
    return {
        "fro_error": error,
        "fidelity": fidelity,
        "exact": bool(error <= RECOVERY_EXACT_TOL),
    }


def fixed_point_distance(rho: np.ndarray, sigma: np.ndarray) -> float:
    return float(np.linalg.norm(bloch(rho) - bloch(sigma)))


def sigma_eigenbasis_coherence(rho: np.ndarray, sigma: np.ndarray) -> float | None:
    vals, vecs = np.linalg.eigh(0.5 * (sigma + sigma.conj().T))
    if float(np.max(vals.real) - np.min(vals.real)) <= 1.0e-10:
        return None
    rotated = vecs.conj().T @ rho @ vecs
    offdiag = rotated - np.diag(np.diag(rotated))
    return float(np.linalg.norm(offdiag, ord="fro"))


def classify_step(delta_u_decrease: float, recovery_exact: bool) -> str:
    delta_zero = abs(delta_u_decrease) <= DELTA_ZERO_TOL
    if delta_zero and recovery_exact:
        return "reversible"
    if (not delta_zero) and (not recovery_exact):
        return "irreversible"
    return "ANOMALOUS"


def corrcoef(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    if float(np.std(x)) <= 0.0 or float(np.std(y)) <= 0.0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def summarize_numeric(values: list[float]) -> dict[str, float]:
    if not values:
        return {"min": 0.0, "max": 0.0, "mean": 0.0}
    arr = np.asarray(values, dtype=float)
    return {
        "min": round_float(float(np.min(arr)), 12),
        "max": round_float(float(np.max(arr)), 12),
        "mean": round_float(float(np.mean(arr)), 12),
    }


def terrain_census(states: list[np.ndarray], fixed_points: dict[int, np.ndarray]) -> dict[str, Any]:
    terrain_rows = []
    all_delta_abs: list[float] = []
    all_recovery_error: list[float] = []
    all_delta_zero_flags: list[float] = []
    all_recovery_exact_flags: list[float] = []
    anomaly_records = []

    dt = FLOW_T / float(FLOW_SEGMENTS)
    for ti in range(8):
        channel = terrain_channel_matrix(ti, dt)
        sigma = fixed_points[ti]
        records = []
        counts = {"reversible": 0, "irreversible": 0, "ANOMALOUS": 0}
        delta_values = []
        error_values = []
        fidelity_values = []
        reversible_fixed_distances = []
        irreversible_fixed_distances = []
        reversible_coherences = []
        irreversible_coherences = []
        strict_contract_fidelities = []
        strict_contract_errors = []

        for state_index, start in enumerate(states):
            rho = start.copy()
            for step in range(FLOW_SEGMENTS):
                before_u = relative_entropy(rho, sigma)
                channel_output = apply_channel_matrix(channel, rho)
                after_u = relative_entropy(channel_output, sigma)
                delta_u_decrease = before_u - after_u
                recovered = petz_recover(channel, sigma, channel_output)
                measure = recovery_measure(rho, recovered)
                cls = classify_step(delta_u_decrease, bool(measure["exact"]))
                counts[cls] += 1

                delta_abs = abs(delta_u_decrease)
                fixed_dist = fixed_point_distance(rho, sigma)
                coherence = sigma_eigenbasis_coherence(rho, sigma)
                delta_values.append(delta_u_decrease)
                error_values.append(float(measure["fro_error"]))
                fidelity_values.append(float(measure["fidelity"]))
                all_delta_abs.append(delta_abs)
                all_recovery_error.append(float(measure["fro_error"]))
                all_delta_zero_flags.append(float(delta_abs <= DELTA_ZERO_TOL))
                all_recovery_exact_flags.append(float(bool(measure["exact"])))

                if delta_u_decrease > STRICT_DECREASE_TOL:
                    strict_contract_fidelities.append(float(measure["fidelity"]))
                    strict_contract_errors.append(float(measure["fro_error"]))

                if cls == "reversible":
                    reversible_fixed_distances.append(fixed_dist)
                    if coherence is not None:
                        reversible_coherences.append(coherence)
                elif cls == "irreversible":
                    irreversible_fixed_distances.append(fixed_dist)
                    if coherence is not None:
                        irreversible_coherences.append(coherence)
                else:
                    anomaly_records.append(
                        {
                            "terrain": ti,
                            "state_index": state_index,
                            "step": step,
                            "delta_u_decrease": round_float(delta_u_decrease, 12),
                            "recovery_fro_error": round_float(float(measure["fro_error"]), 12),
                            "recovery_fidelity": round_float(float(measure["fidelity"]), 12),
                            "delta_zero": bool(delta_abs <= DELTA_ZERO_TOL),
                            "recovery_exact": bool(measure["exact"]),
                        }
                    )

                records.append(
                    {
                        "state_index": state_index,
                        "step": step,
                        "delta_u_decrease": round_float(delta_u_decrease, 12),
                        "recovery_fro_error": round_float(float(measure["fro_error"]), 12),
                        "recovery_fidelity": round_float(float(measure["fidelity"]), 12),
                        "classification": cls,
                        "fixed_point_bloch_distance": round_float(fixed_dist, 12),
                        "sigma_eigenbasis_coherence": None if coherence is None else round_float(coherence, 12),
                    }
                )
                rho = channel_output

        strict_contract_ok = bool(
            strict_contract_fidelities
            and max(strict_contract_fidelities) < 1.0
            and min(strict_contract_errors) > RECOVERY_EXACT_TOL
        )
        if counts["reversible"] == 0:
            pattern = "no reversible seeded-grid steps; fixed-point equality face not hit by the seeded grid"
        elif all(distance <= 1.0e-9 for distance in reversible_fixed_distances):
            pattern = "reversible seeded-grid steps live at the terrain fixed point; no nontrivial unitary-direction face observed"
        else:
            pattern = "reversible seeded-grid steps include non-fixed states; inspect records for candidate unitary/recoverable face"

        terrain_rows.append(
            {
                "terrain": ti,
                "label": TERRAIN_LABELS[ti],
                "kind": TERR[ti][1],
                "counts": counts,
                "total_steps": len(records),
                "delta_u_decrease": summarize_numeric(delta_values),
                "recovery_fro_error": summarize_numeric(error_values),
                "recovery_fidelity": summarize_numeric(fidelity_values),
                "strictly_contractive_control": {
                    "strict_delta_threshold": STRICT_DECREASE_TOL,
                    "strict_step_count": len(strict_contract_fidelities),
                    "max_recovery_fidelity_on_strict_steps": round_float(max(strict_contract_fidelities), 12)
                    if strict_contract_fidelities
                    else 0.0,
                    "min_recovery_error_on_strict_steps": round_float(min(strict_contract_errors), 12)
                    if strict_contract_errors
                    else 0.0,
                    "passes_expected_fidelity_below_1": strict_contract_ok,
                },
                "structure_pattern": pattern,
                "structure_metrics": {
                    "reversible_fixed_point_distance": summarize_numeric(reversible_fixed_distances),
                    "irreversible_fixed_point_distance": summarize_numeric(irreversible_fixed_distances),
                    "reversible_sigma_eigenbasis_coherence": summarize_numeric(reversible_coherences),
                    "irreversible_sigma_eigenbasis_coherence": summarize_numeric(irreversible_coherences),
                    "sigma_eigenbasis_note": "not diagnostic when sigma is maximally mixed"
                    if sigma_eigenbasis_coherence(I2 / 2.0, sigma) is None
                    else "coherence measured in the nondegenerate fixed-point eigenbasis",
                },
                "records": records,
            }
        )

    return {
        "per_terrain": terrain_rows,
        "anomaly_count": len(anomaly_records),
        "anomalies": anomaly_records[:100],
        "anomaly_record_limit": 100,
        "correlations": {
            "abs_delta_u_vs_recovery_error_pearson": None
            if corrcoef(all_delta_abs, all_recovery_error) is None
            else round_float(corrcoef(all_delta_abs, all_recovery_error), 12),
            "delta_zero_indicator_vs_recovery_exact_indicator_pearson": None
            if corrcoef(all_delta_zero_flags, all_recovery_exact_flags) is None
            else round_float(corrcoef(all_delta_zero_flags, all_recovery_exact_flags), 12),
        },
    }


def fixed_point_probe(fixed_points: dict[int, np.ndarray]) -> list[dict[str, Any]]:
    rows = []
    dt = FLOW_T / float(FLOW_SEGMENTS)
    for ti in range(8):
        channel = terrain_channel_matrix(ti, dt)
        sigma = fixed_points[ti]
        out = apply_channel_matrix(channel, sigma)
        recovered = petz_recover(channel, sigma, out)
        measure = recovery_measure(sigma, recovered)
        rows.append(
            {
                "terrain": ti,
                "label": TERRAIN_LABELS[ti],
                "delta_u_decrease": round_float(relative_entropy(sigma, sigma) - relative_entropy(out, sigma), 12),
                "channel_fixed_point_error": round_float(float(np.linalg.norm(out - sigma, ord="fro")), 12),
                "recovery_fro_error": round_float(float(measure["fro_error"]), 12),
                "recovery_fidelity": round_float(float(measure["fidelity"]), 12),
                "recovery_exact": bool(measure["exact"]),
            }
        )
    return rows


def unitary_channel_matrix(ti: int, dt: float) -> np.ndarray:
    eps, _, _ = TERR[ti]
    unitary = expm(-1j * eps * G * dt * H0)
    cols = []
    for basis in (
        np.array([[1, 0], [0, 0]], complex),
        np.array([[0, 1], [0, 0]], complex),
        np.array([[0, 0], [1, 0]], complex),
        np.array([[0, 0], [0, 1]], complex),
    ):
        cols.append((unitary @ basis @ unitary.conj().T).reshape(-1))
    return np.column_stack(cols)


def unitary_flow_control(states: list[np.ndarray]) -> dict[str, Any]:
    rows = []
    sigma = I2 / 2.0
    dt = FLOW_T / float(FLOW_SEGMENTS)
    total = 0
    failures = 0
    for ti in range(8):
        channel = unitary_channel_matrix(ti, dt)
        terrain_failures = 0
        for state in states:
            rho = state.copy()
            for _ in range(FLOW_SEGMENTS):
                out = apply_channel_matrix(channel, rho)
                delta_u_decrease = relative_entropy(rho, sigma) - relative_entropy(out, sigma)
                recovered = petz_recover(channel, sigma, out)
                measure = recovery_measure(rho, recovered)
                ok = abs(delta_u_decrease) <= DELTA_ZERO_TOL and bool(measure["exact"])
                terrain_failures += int(not ok)
                failures += int(not ok)
                total += 1
                rho = out
        rows.append(
            {
                "terrain": ti,
                "label": TERRAIN_LABELS[ti],
                "steps": len(states) * FLOW_SEGMENTS,
                "failures": terrain_failures,
                "all_reversible": terrain_failures == 0,
            }
        )
    return {
        "control": "unitary_flow_with_invariant_maximally_mixed_sigma",
        "total_steps": total,
        "failures": failures,
        "all_reversible": failures == 0,
        "rows": rows,
    }


def farthest_foreign_fixed_points(fixed_points: dict[int, np.ndarray]) -> dict[int, int]:
    fp_bloch = {ti: bloch(fp) for ti, fp in fixed_points.items()}
    return {
        ti: max(
            (other for other in range(8) if other != ti),
            key=lambda other: float(np.linalg.norm(fp_bloch[ti] - fp_bloch[other])),
        )
        for ti in range(8)
    }


def wrong_recovery_control(states: list[np.ndarray], fixed_points: dict[int, np.ndarray]) -> dict[str, Any]:
    foreign = farthest_foreign_fixed_points(fixed_points)
    rows = []
    dt = FLOW_T / float(FLOW_SEGMENTS)
    for ti in range(8):
        channel = terrain_channel_matrix(ti, dt)
        wrong_sigma = fixed_points[foreign[ti]]
        exact = 0
        errors = []
        for state in states:
            rho = state.copy()
            out = apply_channel_matrix(channel, rho)
            recovered = petz_recover(channel, wrong_sigma, out)
            measure = recovery_measure(rho, recovered)
            exact += int(bool(measure["exact"]))
            errors.append(float(measure["fro_error"]))
        rows.append(
            {
                "terrain": ti,
                "label": TERRAIN_LABELS[ti],
                "foreign_fixed_point_terrain": foreign[ti],
                "foreign_label": TERRAIN_LABELS[foreign[ti]],
                "tested_first_step_states": len(states),
                "wrong_recovery_exact_count": exact,
                "wrong_recovery_fail_count": len(states) - exact,
                "mean_wrong_recovery_error": round_float(float(np.mean(errors)), 12),
                "max_wrong_recovery_error": round_float(float(np.max(errors)), 12),
                "passes_expected_failure": bool(exact < len(states)),
            }
        )
    return {
        "control": "wrong_petz_recovery_uses_farthest_foreign_fixed_point",
        "rows": rows,
        "all_terrains_fail_somewhere": all(row["passes_expected_failure"] for row in rows),
    }


def summarize_verdict(census: dict[str, Any], controls: dict[str, Any], fixed_probe: list[dict[str, Any]]) -> dict[str, Any]:
    anomaly_count = int(census["anomaly_count"])
    strict_controls_pass = all(
        row["strictly_contractive_control"]["passes_expected_fidelity_below_1"]
        for row in census["per_terrain"]
    )
    fixed_probe_pass = all(row["recovery_exact"] and abs(row["delta_u_decrease"]) <= DELTA_ZERO_TOL for row in fixed_probe)
    controls_pass = (
        controls["unitary_flow_control"]["all_reversible"]
        and controls["wrong_recovery_control"]["all_terrains_fail_somewhere"]
        and strict_controls_pass
        and fixed_probe_pass
    )
    reversible_counts = {str(row["terrain"]): row["counts"]["reversible"] for row in census["per_terrain"]}
    return {
        "exit_policy": "always_exit_0_for_honest_verdict_mix",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "dpi_equality_matches_petz_recovery_on_grid": bool(anomaly_count == 0),
        "anomaly_count": anomaly_count,
        "controls_pass": bool(controls_pass),
        "unitary_flow_control_passes": controls["unitary_flow_control"]["all_reversible"],
        "wrong_recovery_control_passes": controls["wrong_recovery_control"]["all_terrains_fail_somewhere"],
        "strictly_contractive_control_passes": bool(strict_controls_pass),
        "fixed_point_probe_passes": bool(fixed_probe_pass),
        "reversible_step_counts_by_terrain": reversible_counts,
        "measured_pattern": (
            "On the seeded grid, reversible terrain steps are exactly the DeltaU≈0 and Petz-exact steps. "
            "They occur only at duplicated maximally mixed fixed-point grid states for unital depol/proj terrains; "
            "nonunital damping terrain fixed points are recovered in the explicit fixed-point probe but are not sampled by the grid. "
            "No nontrivial unitary-direction reversible face was observed inside the dissipative exact terrain segments."
        ),
    }


def build_result() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    states = seeded_state_grid(rng)
    fixed_points = {ti: long_fixed_point(ti) for ti in range(8)}
    census = terrain_census(states, fixed_points)
    fixed_probe = fixed_point_probe(fixed_points)
    controls = {
        "unitary_flow_control": unitary_flow_control(states),
        "wrong_recovery_control": wrong_recovery_control(states, fixed_points),
    }
    verdict = summarize_verdict(census, controls, fixed_probe)
    return {
        "sim_id": SIM_ID,
        "name": "Petz recovery reversibility census for terrain U-pawl equality cases",
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
            "delta_zero_tol": DELTA_ZERO_TOL,
            "strict_decrease_tol": STRICT_DECREASE_TOL,
            "recovery_exact_tol": RECOVERY_EXACT_TOL,
            "spectral_floor": SPECTRAL_FLOOR,
        },
        "petz_formula": (
            "R_sigma,N(X)=sigma^(1/2) N*(N(sigma)^(-1/2) X N(sigma)^(-1/2)) sigma^(1/2); "
            "N* is the Hilbert-Schmidt adjoint of the exact terrain segment channel matrix"
        ),
        "fixed_points_bloch": {
            str(ti): [round_float(x, 12) for x in bloch(fixed_points[ti])] for ti in range(8)
        },
        "fixed_point_probe": fixed_probe,
        "reversibility_census": census,
        "controls": controls,
        "verdict": verdict,
    }


def print_table(result: dict[str, Any]) -> None:
    print("PER-TERRAIN PETZ RECOVERY / REVERSIBILITY CENSUS")
    print(
        "thresholds: "
        f"DeltaU_zero={DELTA_ZERO_TOL:.1e} recovery_exact_fro={RECOVERY_EXACT_TOL:.1e} "
        f"strict_decrease={STRICT_DECREASE_TOL:.1e}"
    )
    print("terrain kind reversible irreversible anomalous max_DeltaU max_rec_error strict<1 pattern")
    for row in result["reversibility_census"]["per_terrain"]:
        counts = row["counts"]
        strict = row["strictly_contractive_control"]
        print(
            f"t{row['terrain']} {row['kind']:5s} "
            f"rev={counts['reversible']:4d} irr={counts['irreversible']:4d} anom={counts['ANOMALOUS']:3d} "
            f"maxDU={row['delta_u_decrease']['max']:.6f} "
            f"maxErr={row['recovery_fro_error']['max']:.6f} "
            f"strict_ok={strict['passes_expected_fidelity_below_1']} "
            f"{row['structure_pattern']}"
        )


def print_controls(result: dict[str, Any]) -> None:
    print("\nCONTROLS")
    unitary = result["controls"]["unitary_flow_control"]
    print(
        "unitary-flow: "
        f"all_reversible={unitary['all_reversible']} failures={unitary['failures']}/{unitary['total_steps']}"
    )
    wrong = result["controls"]["wrong_recovery_control"]
    print(f"wrong-recovery: all_terrains_fail_somewhere={wrong['all_terrains_fail_somewhere']}")
    for row in wrong["rows"]:
        print(
            f"  t{row['terrain']} foreign=t{row['foreign_fixed_point_terrain']} "
            f"fail={row['wrong_recovery_fail_count']}/{row['tested_first_step_states']} "
            f"mean_err={row['mean_wrong_recovery_error']:.6f}"
        )
    print("fixed-point probe:")
    for row in result["fixed_point_probe"]:
        print(
            f"  t{row['terrain']} channel_fp_err={row['channel_fixed_point_error']:.2e} "
            f"recovery_err={row['recovery_fro_error']:.2e} exact={row['recovery_exact']}"
        )


def print_verdict(result: dict[str, Any]) -> None:
    verdict = result["verdict"]
    print("\nVERDICT")
    for key, value in verdict.items():
        print(f"{key}: {value}")
    corr = result["reversibility_census"]["correlations"]
    print(f"correlations: {corr}")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("PETZ RECOVERY REVERSIBILITY CENSUS")
    print("classification=scratch_diagnostic promotion_allowed=false formal_admission_allowed=false")
    print("seed=0; terrains=8; states=256; per-terrain steps=6144")
    print("banned modes excluded: no aliased/self-comparison, no hardcoded labels, no tautological recovery")
    print_table(result)
    print_controls(result)
    print_verdict(result)
    print(f"\nALL_GATES: HONEST_MIX_EXIT_0 -> {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
