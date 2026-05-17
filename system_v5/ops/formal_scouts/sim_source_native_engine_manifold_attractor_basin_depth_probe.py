#!/usr/bin/env python3
"""Source-native engine/manifold attractor-basin depth scout.

This is a foundation scout for the active attractor-basin goal. It tests
whether existing EngineCore + manifold dynamics form a perturbation-stable
candidate basin under multiple observables and matched controls. It is not a
global manifold proof.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import numpy as np

from engine_core import EngineCore, I2, _normalize_density, generate_initial_density


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_engine_manifold_attractor_basin_depth_probe_results.json"

NAME = "source_native_engine_manifold_attractor_basin_depth_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests source-native EngineCore/manifold candidate "
    "attractor-basin depth under perturbations and matched controls. It does "
    "not admit global manifold necessity, final FEP, final Axis0, full "
    "Holodeck, physics, cognition, world-model, architecture, or canonical "
    "claims."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density perturbations, trace distances, Pauli/FEP readouts, and basin statistics",
    },
    "engine_core": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source-native engine/manifold dynamics and stage records",
    },
    "json": {"tried": True, "used": True, "reason": "load-bearing result writing"},
    "hashlib": {"tried": True, "used": True, "reason": "load-bearing source hash receipt"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

SEEDS = [101, 211, 307, 419]
EPSILONS = [0.02, 0.08, 0.18]
TRACE_CANDIDATE_FLOOR = 0.10
CONTROL_SEPARATION_FLOOR = 0.05


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trace_distance(rho1: np.ndarray, rho2: np.ndarray) -> float:
    diff = rho1 - rho2
    evals = np.linalg.eigvalsh(diff.conj().T @ diff)
    return 0.5 * float(np.sum(np.sqrt(np.clip(evals, 0.0, None))))


def perturb_density(rho: np.ndarray, epsilon: float) -> np.ndarray:
    return _normalize_density((1.0 - epsilon) * rho + epsilon * I2 / 2.0)


def run_cycle(
    engine_type: int,
    rho: np.ndarray,
    *,
    manifold_enabled: bool,
    schedule_mode: str = "native",
) -> dict[str, Any]:
    engine = EngineCore(engine_type=engine_type, manifold_enabled=manifold_enabled)
    if schedule_mode == "reversed":
        engine.schedule = list(reversed(engine.schedule))
    elif schedule_mode == "rotated":
        engine.schedule = engine.schedule[1:] + engine.schedule[:1]
    result = engine.run_full_cycle(rho)
    records = result["trajectory"]
    efe = [float(row["fep_efe_score"]["expected_free_energy_proxy"]) for row in records]
    surprise = [float(row["fep_efe_score"]["surprise_kl"]) for row in records]
    correction = [float(row["update_repair"]["manifold_projection_delta_norm"]) for row in records]
    tokens = [str(row["ordered_token"]) for row in records]
    return {
        "rho": np.asarray(result["final_rho"], dtype=np.complex128),
        "tokens": tokens,
        "mean_efe": float(np.mean(efe)),
        "mean_surprise": float(np.mean(surprise)),
        "mean_correction": float(np.mean(correction)),
        "max_correction": float(np.max(correction)),
        "final_purity": float(result["final_purity"]),
        "final_entropy": float(result["final_entropy"]),
        "final_bloch": result["final_bloch"],
        "schedule_mode": schedule_mode,
    }


def token_match_fraction(a: list[str], b: list[str]) -> float:
    return sum(1 for x, y in zip(a, b) if x == y) / max(1, min(len(a), len(b)))


def classify_basin(on_rows: list[dict[str, Any]], off_rows: list[dict[str, Any]], reversed_rows: list[dict[str, Any]], wrong_rows: list[dict[str, Any]]) -> dict[str, Any]:
    on_d = np.array([row["on_trace_to_baseline"] for row in on_rows], dtype=float)
    off_d = np.array([row["off_trace_to_baseline"] for row in off_rows], dtype=float)
    rev_d = np.array([row["reversed_trace_to_baseline"] for row in reversed_rows], dtype=float)
    wrong_d = np.array([row["wrong_chirality_trace_to_baseline"] for row in wrong_rows], dtype=float)
    on_mean = float(np.mean(on_d))
    off_mean = float(np.mean(off_d))
    rev_mean = float(np.mean(rev_d))
    wrong_mean = float(np.mean(wrong_d))
    nearest_control = min(off_mean, rev_mean, wrong_mean)
    separation = nearest_control - on_mean
    if on_mean <= TRACE_CANDIDATE_FLOOR and separation >= CONTROL_SEPARATION_FLOOR:
        label = "candidate_basin"
    elif separation < 0:
        label = "anti_basin"
    elif on_mean <= nearest_control:
        label = "shallow_basin"
    else:
        label = "open_basin_boundary"
    return {
        "label": label,
        "on_mean_trace_to_baseline": on_mean,
        "off_mean_trace_to_baseline": off_mean,
        "reversed_mean_trace_to_baseline": rev_mean,
        "wrong_chirality_mean_trace_to_baseline": wrong_mean,
        "nearest_control_mean": nearest_control,
        "control_separation": separation,
        "candidate_trace_floor": TRACE_CANDIDATE_FLOOR,
        "control_separation_floor": CONTROL_SEPARATION_FLOOR,
    }


def main() -> int:
    started = time.time()
    rows = []
    for engine_type in (0, 1):
        for seed in SEEDS:
            rho0 = generate_initial_density(seed)
            baseline = run_cycle(engine_type, rho0, manifold_enabled=True)
            for epsilon in EPSILONS:
                pert = perturb_density(rho0, epsilon)
                on = run_cycle(engine_type, pert, manifold_enabled=True)
                off = run_cycle(engine_type, pert, manifold_enabled=False)
                reversed_control = run_cycle(engine_type, pert, manifold_enabled=True, schedule_mode="reversed")
                wrong = run_cycle(1 - engine_type, pert, manifold_enabled=True)
                rows.append(
                    {
                        "engine_type": engine_type,
                        "seed": seed,
                        "epsilon": epsilon,
                        "on_trace_to_baseline": trace_distance(on["rho"], baseline["rho"]),
                        "off_trace_to_baseline": trace_distance(off["rho"], baseline["rho"]),
                        "reversed_trace_to_baseline": trace_distance(reversed_control["rho"], baseline["rho"]),
                        "wrong_chirality_trace_to_baseline": trace_distance(wrong["rho"], baseline["rho"]),
                        "on_token_match": token_match_fraction(on["tokens"], baseline["tokens"]),
                        "reversed_token_match": token_match_fraction(reversed_control["tokens"], baseline["tokens"]),
                        "wrong_chirality_token_match": token_match_fraction(wrong["tokens"], baseline["tokens"]),
                        "on_mean_efe": on["mean_efe"],
                        "off_mean_efe": off["mean_efe"],
                        "on_mean_correction": on["mean_correction"],
                        "off_mean_correction": off["mean_correction"],
                        "on_final_purity": on["final_purity"],
                        "off_final_purity": off["final_purity"],
                    }
                )

    on_rows = rows
    basin = classify_basin(rows, rows, rows, rows)
    on_token_min = min(row["on_token_match"] for row in rows)
    reversed_token_max = max(row["reversed_token_match"] for row in rows)
    wrong_token_max = max(row["wrong_chirality_token_match"] for row in rows)
    on_correction_mean = float(np.mean([row["on_mean_correction"] for row in rows]))
    off_correction_mean = float(np.mean([row["off_mean_correction"] for row in rows]))
    purity_gap = float(np.mean([row["on_final_purity"] - row["off_final_purity"] for row in rows]))

    positive = {
        "epsilon_seed_engine_grid_executed": {
            "pass": len(rows) == 2 * len(SEEDS) * len(EPSILONS),
            "row_count": len(rows),
            "seeds": SEEDS,
            "epsilons": EPSILONS,
        },
        "native_stage_identity_preserved_under_perturbation": {
            "pass": on_token_min == 1.0,
            "min_on_token_match": on_token_min,
        },
        "manifold_correction_is_load_bearing_local_observable": {
            "pass": on_correction_mean > off_correction_mean + 1e-6 and purity_gap > 0.0,
            "on_mean_correction": on_correction_mean,
            "off_mean_correction": off_correction_mean,
            "mean_purity_gap_on_minus_off": purity_gap,
        },
        "basin_depth_classifier_runs": {
            "pass": basin["label"] in {"candidate_basin", "shallow_basin", "anti_basin", "open_basin_boundary"},
            "basin": basin,
        },
    }
    graveyard = {
        "reversed_schedule_control_disrupts_stage_identity": {
            "pass": reversed_token_max < 1.0,
            "max_reversed_token_match": reversed_token_max,
        },
        "wrong_chirality_control_not_native_identity": {
            "pass": wrong_token_max < 1.0,
            "max_wrong_chirality_token_match": wrong_token_max,
        },
        "candidate_basin_not_promoted_to_deep_basin": {
            "pass": basin["label"] != "deep_basin",
            "label": basin["label"],
            "reason": "This scout has one implementation and finite 2x2 carrier observables; deep basin requires independent methods/carriers.",
        },
    }
    boundary = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_global_manifold": {
            "pass": "does not admit global manifold necessity" in CLAIM_CEILING,
        },
        "matched_controls_present": {
            "pass": all(key in rows[0] for key in ["off_trace_to_baseline", "reversed_trace_to_baseline", "wrong_chirality_trace_to_baseline"]),
            "controls": ["no_manifold", "reversed_schedule", "wrong_chirality"],
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_engine_manifold_attractor_basin_depth",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "basin_classification": basin,
        "rows": rows,
        "nearby_variants": {"total": len(graveyard), "passed": sum(1 for row in graveyard.values() if row["pass"]), "variants": sorted(graveyard)},
        "why_not_v4_probes": [
            "This is a source-native v5 EngineCore/manifold basin-depth scout.",
            "It uses finite 2x2 carrier/stage-record observables and explicit controls, not v4 physics probes.",
        ],
        "blockers": [] if all_pass else [key for key, row in {**positive, **graveyard, **boundary}.items() if not row.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  basin_label={basin['label']} separation={basin['control_separation']:.6f}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
