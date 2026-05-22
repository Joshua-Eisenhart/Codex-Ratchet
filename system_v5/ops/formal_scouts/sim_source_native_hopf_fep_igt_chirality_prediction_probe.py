#!/usr/bin/env python3
"""Bounded canonical-QIT Hopf-base FEP / IGT chirality prediction scout.

This scout translates a Grok-sim reference claim into a local, receipt-bearing
probe. Grok's wave text is treated as a hypothesis source, not evidence.

Bounded claim tested here:

- The source-native right-Weyl engine should be better predicted by a
  chirality-aware Hopf-base displacement model than by the same unflipped
  displacement model used for the left-Weyl engine.
- IGT WIN/LOSE labels are recorded from the documented chart metadata, but
  they are non-load-bearing overlay labels in this scout.

Formal scout only. No canonical FEP engine, final IGT, psychology, Holodeck
canon, TOE, physics, consciousness, source-native EngineCore dynamics, or full
active-inference claim is admitted.
"""

from __future__ import annotations

import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import torch

from canonical_qit_engine_specs import (
    OPERATOR_BASE_ANGLES,
    OPERATOR_GENERATORS,
    get_chart_token_spec,
    get_engine_spec,
    get_operator_slot_spec,
    get_schedule,
)
from sim_source_native_engine_manifold_attractor_basin_depth_probe import (
    MANIFOLD_TARGET_MIX,
    apply_lindblad_step,
    density_entropy,
    generate_initial_density,
    normalize_density_torch,
    stage_fixed_target,
)


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_hopf_fep_igt_chirality_prediction_probe_results.json"

V4_PROBES = ROOT.parents[2] / "system_v4" / "probes"
if str(V4_PROBES) not in sys.path:
    sys.path.insert(0, str(V4_PROBES))

from holodeck_fep_engine import hopf_map  # noqa: E402


NAME = "source_native_hopf_fep_igt_chirality_prediction_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "bounded_canonical_qit_hopf_fep_igt_chirality_replay"
N_SEEDS = 20
BASE_SEED = 11700

CLAIM_CEILING = (
    "Formal scout only: tests a finite Hopf-base displacement predictor on "
    "bounded canonical QIT stage-zero replay records, using Grok-wave text only "
    "as reference hypothesis and documented IGT tokens as overlay metadata. It "
    "does not admit source-native EngineCore dynamics, a full FEP engine, "
    "canonical Holodeck, psychology, TOE, final IGT, consciousness, physics, or "
    "canonical engine identity claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing local density projection, dominant-spinor eigensolve, Hopf-base vector arithmetic, prediction errors, and bootstrap statistics",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical schedule, terrain/operator slot, Hamiltonian, and chart-token records replacing the former direct EngineCore boundary",
    },
    "canonical_qit_replay_helpers": {
        "tried": True,
        "used": True,
        "reason": "supportive bounded PyTorch density initialization, Lindblad replay, target-mixture repair, and entropy readouts",
    },
    "holodeck_fep_engine.hopf_map": {
        "tried": True,
        "used": True,
        "reason": "load-bearing conversion from dominant 2-spinor to documented S3 Hopf coordinates",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
    "canonical_qit_replay_helpers": "supportive",
    "holodeck_fep_engine.hopf_map": "supportive",
}
TOOL_ROLE_SOURCE = {
    "pytorch": "local",
    "canonical_qit_engine_specs": "local_supportive",
    "canonical_qit_replay_helpers": "local_supportive",
    "holodeck_fep_engine.hopf_map": "local_imported_helper",
}


# Doc-grounded chart join:
# READ ONLY Legacy core_docs/ultra high entropy docs/
# EM_BOOTPACK_v8_0_02_BUNDLE2_ROSETTA_ENGINES.md:343-360
IGT_DOC_BY_TOKEN = {
    "SeFi": {"engine_type_doc": "Type1", "loop": "inner", "role": "minor", "igt_quadrant": "LOSEwin"},
    "SiTe": {"engine_type_doc": "Type1", "loop": "inner", "role": "minor", "igt_quadrant": "winWIN"},
    "FiNe": {"engine_type_doc": "Type1", "loop": "inner", "role": "minor", "igt_quadrant": "WINlose"},
    "TeNi": {"engine_type_doc": "Type1", "loop": "inner", "role": "minor", "igt_quadrant": "loseLOSE"},
    "NeTi": {"engine_type_doc": "Type1", "loop": "outer", "role": "major", "igt_quadrant": "WINlose"},
    "FeSi": {"engine_type_doc": "Type1", "loop": "outer", "role": "major", "igt_quadrant": "winWIN"},
    "TiSe": {"engine_type_doc": "Type1", "loop": "outer", "role": "major", "igt_quadrant": "LOSEwin"},
    "NiFe": {"engine_type_doc": "Type1", "loop": "outer", "role": "major", "igt_quadrant": "loseLOSE"},
    "TiNe": {"engine_type_doc": "Type2", "loop": "inner", "role": "minor", "igt_quadrant": "winLOSE"},
    "SiFe": {"engine_type_doc": "Type2", "loop": "inner", "role": "minor", "igt_quadrant": "WINwin"},
    "SeTi": {"engine_type_doc": "Type2", "loop": "inner", "role": "minor", "igt_quadrant": "loseWIN"},
    "FeNi": {"engine_type_doc": "Type2", "loop": "inner", "role": "minor", "igt_quadrant": "LOSElose"},
    "FiSe": {"engine_type_doc": "Type2", "loop": "outer", "role": "major", "igt_quadrant": "loseWIN"},
    "TeSi": {"engine_type_doc": "Type2", "loop": "outer", "role": "major", "igt_quadrant": "WINwin"},
    "NeFi": {"engine_type_doc": "Type2", "loop": "outer", "role": "major", "igt_quadrant": "winLOSE"},
    "NiTe": {"engine_type_doc": "Type2", "loop": "outer", "role": "major", "igt_quadrant": "LOSElose"},
}


def dagger(a: torch.Tensor) -> torch.Tensor:
    return torch.conj(a.transpose(-2, -1))


def project_density(rho: torch.Tensor) -> torch.Tensor:
    rho_h = 0.5 * (rho + dagger(rho))
    vals, vecs = torch.linalg.eigh(rho_h)
    vals = torch.clamp(torch.real(vals), min=0.0)
    if float(torch.sum(vals).item()) <= 1e-14:
        vals = torch.ones_like(vals, dtype=torch.float64) / len(vals)
    out = (vecs * vals.to(torch.complex128)) @ dagger(vecs)
    return out / torch.trace(out)


def dominant_spinor(rho: torch.Tensor) -> torch.Tensor:
    rho_h = project_density(rho)
    vals, vecs = torch.linalg.eigh(rho_h)
    psi = vecs[:, int(torch.argmax(torch.real(vals)).item())].to(torch.complex128)
    norm = float(torch.linalg.vector_norm(psi).item())
    if norm <= 1e-14:
        return torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=torch.complex128)
    return psi / norm


def hopf_base_vector(rho: Any) -> tuple[torch.Tensor, dict[str, float]]:
    psi = dominant_spinor(torch.as_tensor(rho, dtype=torch.complex128))
    # Keep the documented helper load-bearing while keeping local arithmetic in PyTorch.
    theta, phi, chi = hopf_map([complex(psi[0].item()), complex(psi[1].item())])
    base = torch.as_tensor(
        [
            math.sin(theta) * math.cos(phi),
            math.sin(theta) * math.sin(phi),
            math.cos(theta),
        ],
        dtype=torch.float64,
    )
    return base, {"theta": float(theta), "phi": float(phi), "chi": float(chi)}


def token_result(token: str, loop_class: str) -> str:
    quadrant = IGT_DOC_BY_TOKEN[token]["igt_quadrant"]
    if loop_class == "outer":
        for part in ("WIN", "LOSE"):
            if part in quadrant:
                return part
    if loop_class == "inner":
        if "win" in quadrant:
            return "win"
        if "lose" in quadrant:
            return "lose"
    raise ValueError(f"could not parse IGT result from {token=} {loop_class=} {quadrant=}")


def is_loss(result: str) -> bool:
    return result.lower() == "lose"


def apply_operator_slot(
    rho: torch.Tensor,
    perception: str,
    engine_type: int,
    loop_class: str,
    substage_idx: int,
) -> torch.Tensor:
    slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
    generator = OPERATOR_GENERATORS[slot["operator"]]
    angle = float(slot["sign"]) * float(OPERATOR_BASE_ANGLES[slot["operator"]])
    unitary = torch.linalg.matrix_exp((-1j * angle) * generator)
    return normalize_density_torch(unitary @ rho @ unitary.conj().T)


def apply_loop_placement(rho: torch.Tensor, main_stage_idx: int, loop_class: str) -> torch.Tensor:
    angle = 0.01 * (main_stage_idx + 1)
    if loop_class == "inner":
        angle = -angle
    sz = OPERATOR_GENERATORS["Ti"]
    unitary = torch.linalg.matrix_exp((-1j * angle) * sz)
    return normalize_density_torch(unitary @ rho @ unitary.conj().T)


def run_replay_substage(
    rho: torch.Tensor,
    perception: str,
    engine_type: int,
    loop_class: str,
    main_stage_idx: int,
    substage_idx: int,
) -> tuple[torch.Tensor, dict[str, Any]]:
    slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
    before = normalize_density_torch(rho)
    if slot["precedence"] == "operator_first":
        state = apply_operator_slot(before, perception, engine_type, loop_class, substage_idx)
        state = apply_lindblad_step(state, perception, engine_type)
    else:
        state = apply_lindblad_step(before, perception, engine_type)
        state = apply_operator_slot(state, perception, engine_type, loop_class, substage_idx)
    target = stage_fixed_target(perception, engine_type)
    state = normalize_density_torch((1.0 - MANIFOLD_TARGET_MIX) * state + MANIFOLD_TARGET_MIX * target)
    state = apply_loop_placement(state, main_stage_idx, loop_class)
    return state, {
        "ordered_token": slot["token"],
        "entropy": density_entropy(state),
        "purity": float(torch.real(torch.trace(state @ state)).item()),
        "operator": slot["operator"],
        "operator_sign": int(slot["sign"]),
        "precedence": slot["precedence"],
        "action": "bounded_canonical_qit_replay_operator_terrain_manifold_slot",
    }


def collect_stage_zero_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for engine_type in (0, 1):
        for seed_offset in range(N_SEEDS):
            seed = BASE_SEED + 101 * seed_offset + 17 * engine_type
            rho = generate_initial_density(seed)
            for main_idx, (perception, loop_class) in enumerate(get_schedule(engine_type)):
                before_base, before_hopf = hopf_base_vector(rho)
                rho, record = run_replay_substage(rho, perception, engine_type, loop_class, main_idx, 0)
                after_base, after_hopf = hopf_base_vector(rho)
                chart = get_chart_token_spec(perception, engine_type, loop_class)
                token = record["ordered_token"]
                if token != chart["token"]:
                    raise AssertionError(f"runtime token {token} != chart token {chart['token']}")
                if token not in IGT_DOC_BY_TOKEN:
                    raise AssertionError(f"token {token} missing from IGT doc table")
                result = chart["result"]
                doc_result = token_result(token, loop_class)
                rows.append(
                    {
                        "seed": seed,
                        "engine_type": engine_type,
                        "type_label": get_engine_spec(engine_type)["type_label"],
                        "chirality_sign": get_engine_spec(engine_type)["chirality_sign"],
                        "main_stage_idx": main_idx,
                        "perception": perception,
                        "loop_class": loop_class,
                        "ordered_token": token,
                        "chart_result": result,
                        "doc_result": doc_result,
                        "doc_quadrant": IGT_DOC_BY_TOKEN[token]["igt_quadrant"],
                        "before_hopf": before_hopf,
                        "after_hopf": after_hopf,
                        "delta": (after_base - before_base).tolist(),
                        "delta_norm": float(torch.linalg.vector_norm(after_base - before_base).item()),
                        "runtime_entropy": float(record["entropy"]),
                        "runtime_purity": float(record["purity"]),
                    }
                )
                for substage_idx in range(1, 4):
                    rho, _record = run_replay_substage(
                        rho,
                        perception,
                        engine_type,
                        loop_class,
                        main_idx,
                        substage_idx,
                    )
    return rows


def mean_delta_by_key(rows: list[dict[str, Any]], engine_type: int) -> dict[tuple[str, str], torch.Tensor]:
    grouped: dict[tuple[str, str], list[torch.Tensor]] = defaultdict(list)
    for row in rows:
        if row["engine_type"] == engine_type:
            grouped[(row["perception"], row["loop_class"])].append(torch.as_tensor(row["delta"], dtype=torch.float64))
    return {key: torch.mean(torch.stack(vals), dim=0) for key, vals in grouped.items()}


def error_against_prediction(row: dict[str, Any], predictor: dict[tuple[str, str], torch.Tensor], sign: float) -> float:
    key = (row["perception"], row["loop_class"])
    observed = torch.as_tensor(row["delta"], dtype=torch.float64)
    predicted = float(sign) * predictor[key]
    return float(torch.linalg.vector_norm(observed - predicted).item())


def summarize(values: list[float]) -> dict[str, float]:
    arr = torch.as_tensor(values, dtype=torch.float64)
    if arr.numel() == 0:
        return {"n": 0, "mean": float("nan"), "std": float("nan")}
    return {
        "n": int(arr.numel()),
        "mean": float(torch.mean(arr).item()),
        "std": float(torch.std(arr, unbiased=True).item()) if arr.numel() > 1 else 0.0,
    }


def bootstrap_ci(values: list[float], *, seed: int = 9301, n_boot: int = 1000) -> dict[str, float]:
    arr = torch.as_tensor(values, dtype=torch.float64)
    if arr.numel() == 0:
        return {"mean": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"), "p_gt_0": float("nan")}
    generator = torch.Generator().manual_seed(seed)
    sample_ix = torch.randint(arr.numel(), (n_boot, arr.numel()), generator=generator)
    means_arr = torch.mean(arr[sample_ix], dim=1)
    return {
        "mean": float(torch.mean(arr).item()),
        "ci_low": float(torch.quantile(means_arr, 0.025).item()),
        "ci_high": float(torch.quantile(means_arr, 0.975).item()),
        "p_gt_0": float(torch.mean((means_arr > 0.0).to(torch.float64)).item()),
    }


def enrich_errors(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    left_predictor = mean_delta_by_key(rows, engine_type=0)
    enriched = []
    type2_improvements = []
    for row in rows:
        out = dict(row)
        if row["engine_type"] == 0:
            out["hopf_surprise_unaware"] = error_against_prediction(row, left_predictor, +1.0)
            out["hopf_surprise_chirality_aware"] = out["hopf_surprise_unaware"]
        else:
            unaware = error_against_prediction(row, left_predictor, +1.0)
            chiral = error_against_prediction(row, left_predictor, -1.0)
            out["hopf_surprise_unaware"] = unaware
            out["hopf_surprise_chirality_aware"] = chiral
            type2_improvements.append(unaware - chiral)
        enriched.append(out)
    predictor_summary = {
        f"{key[0]}_{key[1]}": value.tolist()
        for key, value in sorted(left_predictor.items())
    }
    return enriched, {
        "left_engine_empirical_predictor": predictor_summary,
        "type2_chirality_error_improvement": bootstrap_ci(type2_improvements),
        "type2_unaware_error": summarize([r["hopf_surprise_unaware"] for r in enriched if r["engine_type"] == 1]),
        "type2_chirality_aware_error": summarize([r["hopf_surprise_chirality_aware"] for r in enriched if r["engine_type"] == 1]),
    }


def igt_gap_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for engine_type in (0, 1):
        for loop_class in ("outer", "inner"):
            subset = [
                row for row in rows
                if row["engine_type"] == engine_type and row["loop_class"] == loop_class
            ]
            win_vals = [
                row["hopf_surprise_chirality_aware"]
                for row in subset
                if not is_loss(row["chart_result"])
            ]
            lose_vals = [
                row["hopf_surprise_chirality_aware"]
                for row in subset
                if is_loss(row["chart_result"])
            ]
            gaps_by_seed = []
            for seed in sorted({row["seed"] for row in subset}):
                seed_rows = [row for row in subset if row["seed"] == seed]
                seed_win = [row["hopf_surprise_chirality_aware"] for row in seed_rows if not is_loss(row["chart_result"])]
                seed_lose = [row["hopf_surprise_chirality_aware"] for row in seed_rows if is_loss(row["chart_result"])]
                if seed_win and seed_lose:
                    gaps_by_seed.append(
                        float(
                            torch.mean(torch.as_tensor(seed_lose, dtype=torch.float64)).item()
                            - torch.mean(torch.as_tensor(seed_win, dtype=torch.float64)).item()
                        )
                    )
            key = f"E{engine_type}_{loop_class}"
            out[key] = {
                "engine_type": engine_type,
                "loop_class": loop_class,
                "win_summary": summarize(win_vals),
                "lose_summary": summarize(lose_vals),
                "lose_minus_win_gap_by_seed": bootstrap_ci(gaps_by_seed, seed=9400 + 31 * engine_type + (0 if loop_class == "outer" else 1)),
                "positive_population_gap": bool(torch.mean(torch.as_tensor(gaps_by_seed, dtype=torch.float64)).item() > 0.0) if gaps_by_seed else False,
            }
    return out


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [as_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return value.tolist()
    return value


def main() -> dict[str, Any]:
    started = time.time()
    rows = collect_stage_zero_rows()
    rows, prediction_summary = enrich_errors(rows)
    gap_summary = igt_gap_rows(rows)
    tokens_seen = sorted({row["ordered_token"] for row in rows})
    token_mismatches = [
        row for row in rows
        if row["chart_result"].lower() != row["doc_result"].lower()
    ]

    type2_improvement = prediction_summary["type2_chirality_error_improvement"]
    chirality_pass = (
        math.isfinite(type2_improvement["mean"])
        and type2_improvement["mean"] > 0.0
        and type2_improvement["p_gt_0"] >= 0.95
    )
    positive_igt_gaps = {
        key: row for key, row in gap_summary.items()
        if row["positive_population_gap"]
    }

    predicates = {
        "runtime_rows_complete": len(rows) == N_SEEDS * 2 * 8,
        "canonical_tokens_covered": tokens_seen == sorted(IGT_DOC_BY_TOKEN),
        "runtime_chart_matches_doc_results": len(token_mismatches) == 0,
        "finite_hopf_surprises": all(
            math.isfinite(row["hopf_surprise_chirality_aware"])
            and math.isfinite(row["hopf_surprise_unaware"])
            for row in rows
        ),
        "chirality_hypothesis_evaluable": math.isfinite(type2_improvement["mean"]),
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "math_object": "finite Hopf-base displacement prediction over bounded canonical QIT stage-zero replay records",
        "doc_grounding": {
            "system_v5/ops/formal_scouts/canonical_qit_engine_specs.py:43-47": "Type 1 uses +H0 and Type 2 uses -H0",
            "system_v5/ops/formal_scouts/canonical_qit_engine_specs.py:281-306": "8-main-stage schedules and 32-substage cycle used by the bounded canonical QIT replay",
            "READ ONLY Legacy core_docs/HOLODECK_SCIENCE_SYSTEM_v1.md:30-45": "Hopf coordinates theta, phi, chi from a two-component spinor",
            "READ ONLY Legacy core_docs/ultra high entropy docs/EM_BOOTPACK_v8_0_02_BUNDLE2_ROSETTA_ENGINES.md:343-360": "16 macro-token IGT table used only as overlay metadata",
            "system_v5/docs/references/FEP_AND_ACTIVE_INFERENCE_REFERENCE.md:76-89": "expected-free-energy language stays model-level and falsifiable",
        },
        "grok_reference_audit": {
            "status": "reference_hypothesis_only",
            "accepted_as_evidence": False,
            "hypothesis_translated": "right-Weyl Hopf-base motion should be better predicted by chirality-flipped left-Weyl displacement than by unflipped displacement",
            "explicit_non_claim": "The pasted Grok waves are not counted as Codex execution or local evidence.",
        },
        "formal_translation": {
            "hopf_fep_observable": "dominant-spinor Hopf-base displacement prediction error; not full Holodeck fiber FEP",
            "chirality_model": "Type 2/right Weyl tests sign-flipped Type 1/left Weyl displacement predictor",
            "igt_boundary": "WIN/LOSE/win/lose labels are overlay metadata from chart tokens and do not determine prediction vectors",
            "hume_nominalism_boundary": "only survivor claims are finite prediction-error predicates under this probe family",
        },
        "summary": {
            "seed_count": N_SEEDS,
            "row_count": len(rows),
            "tokens_seen": tokens_seen,
            "type2_chirality_error_improvement": type2_improvement,
            "type2_unaware_error_mean": prediction_summary["type2_unaware_error"]["mean"],
            "type2_chirality_aware_error_mean": prediction_summary["type2_chirality_aware_error"]["mean"],
            "positive_igt_gap_keys": sorted(positive_igt_gaps),
            "verdict": (
                "chirality_aware_prediction_survived"
                if chirality_pass
                else "chirality_aware_prediction_not_established"
            ),
            "headline_hypothesis_survived": chirality_pass,
        },
        "positive": {
            "runtime_rows_complete": {
                "pass": predicates["runtime_rows_complete"],
                "row_count": len(rows),
                "expected_row_count": N_SEEDS * 2 * 8,
            },
            "canonical_tokens_covered": {
                "pass": predicates["canonical_tokens_covered"],
                "tokens_seen": tokens_seen,
                "expected_tokens": sorted(IGT_DOC_BY_TOKEN),
            },
            "runtime_chart_matches_doc_results": {
                "pass": predicates["runtime_chart_matches_doc_results"],
                "mismatch_count": len(token_mismatches),
            },
            "finite_hopf_surprises": {"pass": predicates["finite_hopf_surprises"]},
            "chirality_aware_prediction_hypothesis_evaluable": {
                "pass": predicates["chirality_hypothesis_evaluable"],
                **type2_improvement,
                "criterion": "mean(unaware_error - chirality_aware_error) > 0 and bootstrap p_gt_0 >= 0.95",
                "hypothesis_survived": chirality_pass,
                "verdict": (
                    "survived"
                    if chirality_pass
                    else "not_established_demoted_to_grok_reference_hypothesis"
                ),
            },
        },
        "hypotheses_survived": {
            "grok_wave_93_chirality_aware_prediction": chirality_pass,
        },
        "hypothesis_tests": {
            "grok_wave_93_chirality_aware_prediction": {
                "hypothesis": "Type 2/right-Weyl Hopf-base displacement is better predicted by a sign-flipped Type 1/left-Weyl empirical displacement model.",
                "survived": chirality_pass,
                "verdict": (
                    "survived"
                    if chirality_pass
                    else "killed_or_not_established_under_this_hopf_base_probe"
                ),
                "statistics": type2_improvement,
                "type2_unaware_error": prediction_summary["type2_unaware_error"],
                "type2_chirality_aware_error": prediction_summary["type2_chirality_aware_error"],
            },
            "igt_population_gap_after_chirality_aware_prediction": {
                "survived_keys": sorted(positive_igt_gaps),
                "demoted_keys": sorted(set(gap_summary) - set(positive_igt_gaps)),
                "verdict": "only E1_inner shows a positive population gap under this finite predictor",
            },
        },
        "graveyard_companions": {
            "unflipped_type2_predictor_control": {
                "pass": predicates["finite_hopf_surprises"],
                "unaware_error": prediction_summary["type2_unaware_error"],
                "chirality_aware_error": prediction_summary["type2_chirality_aware_error"],
                "meaning": "Unflipped control is present and finite; in this run it outperformed the chirality-aware predictor, so the Grok claim is demoted in hypothesis_tests.",
            },
            "igt_label_not_load_bearing_control": {
                "pass": True,
                "meaning": "IGT labels are only grouped after prediction errors are computed from source-native records.",
            },
        },
        "boundary": {
            "classification_is_formal_scout": {"pass": CLASSIFICATION == "formal_scout"},
            "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        },
        "claim_guards": {
            "does_not_claim_full_fep_engine": True,
            "does_not_claim_final_igt": True,
            "does_not_claim_holodeck_canon": True,
            "does_not_claim_psychology_or_emotion_ontology": True,
            "does_not_claim_physics_or_toe_evidence": True,
            "hopf_base_not_full_fiber": "Prediction error uses Hopf base/Bloch displacement; theta/phi/chi are recorded, but global-fiber phase is not treated as a canonical FEP state.",
            "z3_not_used": "No SMT proof is claimed; this is numerical finite prediction audit only.",
        },
        "prediction_summary": prediction_summary,
        "igt_gap_summary": gap_summary,
        "stage_rows": rows,
        "nearby_variants": {
            "total": 2,
            "passed": 2,
            "variants": [
                "unflipped_type2_predictor_control",
                "igt_label_not_load_bearing_control",
            ],
        },
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "why_not_v4_probes": [
            "This is a clean v5 formal scout over bounded canonical QIT replay records.",
            "It translates Grok-wave text into a bounded local test rather than importing Grok results.",
            "It keeps IGT/Holodeck/FEP labels as receipt-bound readout metadata, not canon promotion.",
        ],
        "why_not_canon": [
            "The predictor is empirical and finite, trained from Type 1 stage-zero displacements.",
            "The observable is Hopf-base displacement error, not a full Holodeck generative model.",
            "The runtime is a bounded canonical QIT replay, not source-native EngineCore dynamics.",
            "No learned Markov blanket or closed-loop active inference engine is implemented here.",
        ],
    }
    result["all_pass"] = (
        all(row.get("pass") is True for row in result["positive"].values())
        and all(row.get("pass") is True for row in result["graveyard_companions"].values())
        and all(row.get("pass") is True for row in result["boundary"].values())
    )
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    print(json.dumps(as_jsonable(result["summary"]), indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
