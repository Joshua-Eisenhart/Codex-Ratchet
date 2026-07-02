#!/usr/bin/env python3
"""Clean-room rebuild 007: stress the point-reference MI survivor.

rebuild_006 found that the clean point-reference lifted-base bridge survives a
first matched-random control on MI and logZ+MI. This scout stresses that exact
survivor with stricter nuisance-preserving controls.

No formal_scout receipts, grok_sim outputs, external audits, or cross-lane docs
are read.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any, Callable

import torch

from sim_rebuild_004_xi_rho_ab_bridge_family_from_readonly import (
    CDTYPE,
    entangled_cut,
    fubini_theta,
    path_spinors,
    spinor,
)
from sim_rebuild_005_qit_fep_axis0_batch_from_clean_xi import qit_path_readout


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "rebuild_007_point_reference_survivor_stress_results.json"

classification = "clean_rebuild_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical_clean_rebuild"
SOURCE_ALIGNMENT_CATEGORY = "point_reference_survivor_stress"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Clean rebuild scout only: stresses the point-reference MI survivor from "
    "rebuild_006. It does not admit final Xi, Phi0, Axis0, or formal evidence."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing deterministic matched controls, spinor transformations, QIT path readouts, and stress statistics",
    },
    "clean_rebuild_004_source": {"tried": True, "used": True, "reason": "supportive clean spinor/Xi constructors"},
    "clean_rebuild_005_source": {"tried": True, "used": True, "reason": "supportive clean QIT path readout"},
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result paths"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "clean_rebuild_004_source": "supportive",
    "clean_rebuild_005_source": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

K_SEEDS = 64
STEPS = 18
TWO_PI = 2.0 * math.pi


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


def base_samples(path: str = "lifted_base") -> list[torch.Tensor]:
    return path_spinors(path, 0.17, 0.31, 0.44, steps=STEPS)


def reference() -> torch.Tensor:
    return spinor(-0.28, 0.79, math.pi / 4.0)


def score_states(states: list[torch.Tensor]) -> dict[str, float]:
    rows = [qit_path_readout(state) for state in states]
    keys = ["log_z", "I_c", "MI", "Phi_logZ_plus_Ic", "Phi_logZ_plus_MI"]
    return {key: float(sum(row[key] for row in rows) / len(rows)) for key in keys}


def candidate_states() -> list[torch.Tensor]:
    ref = reference()
    return [entangled_cut(sample, ref) for sample in base_samples("lifted_base")]


def random_spinor(generator: torch.Generator) -> torch.Tensor:
    vals = torch.rand(3, generator=generator, dtype=torch.float64)
    return spinor(
        TWO_PI * vals[0].item(),
        TWO_PI * vals[1].item(),
        0.08 + (math.pi / 2.0 - 0.16) * vals[2].item(),
    )


def phase_scrambled_ref(seed: int) -> torch.Tensor:
    generator = torch.Generator().manual_seed(31_000 + seed)
    vals = torch.rand(2, generator=generator, dtype=torch.float64)
    # Preserve eta/amplitudes of the reference, randomize phase coordinates.
    return spinor(TWO_PI * vals[0].item(), TWO_PI * vals[1].item(), math.pi / 4.0)


def amplitude_scrambled_ref(seed: int) -> torch.Tensor:
    generator = torch.Generator().manual_seed(32_000 + seed)
    val = torch.rand(1, generator=generator, dtype=torch.float64)[0].item()
    # Preserve reference phases, randomize eta/amplitude.
    return spinor(-0.28, 0.79, 0.08 + (math.pi / 2.0 - 0.16) * val)


def shell_matched_ref(seed: int, idx: int) -> torch.Tensor:
    # Deterministically rotate around the same eta shell; seed offsets phase.
    phase_offset = (seed % STEPS) / STEPS * TWO_PI
    return spinor(-0.28 + phase_offset, 2.0 * math.pi * idx / STEPS, math.pi / 4.0)


def history_matched_ref(seed: int, idx: int) -> torch.Tensor:
    samples = base_samples("lifted_base")
    shift = 1 + (seed % (STEPS - 1))
    return samples[(idx - shift) % STEPS]


def control_states(name: str, seed: int) -> list[torch.Tensor]:
    samples = base_samples("lifted_base")
    ref = reference()
    states = []
    for idx, sample in enumerate(samples):
        theta = fubini_theta(sample, ref)
        if name == "matched_random":
            generator = torch.Generator().manual_seed(30_000 + seed * 100 + idx)
            ctrl = random_spinor(generator)
        elif name == "phase_scrambled":
            ctrl = phase_scrambled_ref(seed + idx)
        elif name == "amplitude_scrambled":
            ctrl = amplitude_scrambled_ref(seed + idx)
        elif name == "shell_matched":
            ctrl = shell_matched_ref(seed, idx)
        elif name == "history_matched":
            ctrl = history_matched_ref(seed, idx)
        else:
            raise ValueError(name)
        states.append(entangled_cut(sample, ctrl, theta=theta))
    return states


def fixed_path_control(name: str) -> list[torch.Tensor]:
    ref = reference()
    if name == "fiber_candidate":
        return [entangled_cut(sample, ref) for sample in base_samples("fiber")]
    if name == "product_like_zero_angle":
        return [entangled_cut(sample, ref, theta=0.0) for sample in base_samples("lifted_base")]
    raise ValueError(name)


def stress_against_control(candidate_score: dict[str, float], control_name: str) -> dict[str, Any]:
    rows = []
    for seed in range(K_SEEDS):
        score = score_states(control_states(control_name, seed))
        rows.append({key: candidate_score[key] - score[key] for key in candidate_score})
    stats = {}
    for key in candidate_score:
        diffs = torch.tensor([row[key] for row in rows], dtype=torch.float64)
        mean = float(torch.mean(diffs).item())
        std = float(torch.std(diffs, unbiased=True).item())
        se = std / math.sqrt(K_SEEDS)
        z = mean / se if se > 0 else (math.inf if mean > 0 else -math.inf if mean < 0 else 0.0)
        stats[key] = {
            "mean_diff": mean,
            "std_diff": std,
            "se_diff": se,
            "z": z,
            "survives_positive": bool(mean > 0.0 and abs(mean) > 0.01 and z > 2.5),
        }
    return {
        "control": control_name,
        "k_seeds": K_SEEDS,
        "stats": stats,
        "surviving_readouts": [key for key, value in stats.items() if value["survives_positive"]],
    }


def fixed_control_stats(candidate_score: dict[str, float], control_name: str) -> dict[str, Any]:
    score = score_states(fixed_path_control(control_name))
    diffs = {key: candidate_score[key] - score[key] for key in candidate_score}
    return {
        "control": control_name,
        "score": score,
        "diff_candidate_minus_control": diffs,
        "positive_readouts_over_floor": [key for key, value in diffs.items() if value > 0.01],
    }


def survivor_stress_gate() -> dict[str, Any]:
    candidate_score = score_states(candidate_states())
    ensemble_controls = [
        stress_against_control(candidate_score, name)
        for name in ("matched_random", "phase_scrambled", "amplitude_scrambled", "shell_matched", "history_matched")
    ]
    fixed_controls = [
        fixed_control_stats(candidate_score, "fiber_candidate"),
        fixed_control_stats(candidate_score, "product_like_zero_angle"),
    ]
    readouts = ["MI", "Phi_logZ_plus_MI"]
    readout_survival = {
        readout: all(readout in control["surviving_readouts"] for control in ensemble_controls)
        and all(readout in control["positive_readouts_over_floor"] for control in fixed_controls)
        for readout in readouts
    }
    return {
        "pass": True,
        "candidate_score": candidate_score,
        "ensemble_controls": ensemble_controls,
        "fixed_controls": fixed_controls,
        "readout_survival": readout_survival,
        "survived_all_controls": [key for key, value in readout_survival.items() if value],
    }


def nonpromotion_gate(stress: dict[str, Any]) -> dict[str, Any]:
    survivors = stress["survived_all_controls"]
    return {
        "pass": True,
        "admission": "blocked",
        "survivors": survivors,
        "reason": (
            "This stress scout can kill or narrow the clean point-reference survivor, "
            "but formal admission is blocked until the formal estate is reset and "
            "the survivor is rerun as an isolated formal scout."
        ),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    stress = survivor_stress_gate()
    nonpromotion = nonpromotion_gate(stress)
    sections = {"survivor_stress_gate": stress, "nonpromotion_gate": nonpromotion}
    result = {
        "schema": "clean_rebuild_result_v1",
        "name": "rebuild_007_point_reference_survivor_stress",
        "classification": classification,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "all_pass": all(bool(section["pass"]) for section in sections.values()),
        "sections": sections,
        "source_boundary": {
            "reads_formal_scout_results": False,
            "reads_grok_sim": False,
            "reads_external_audits": False,
            "reads_cross_lane_synthesis_docs": False,
            "reads_clean_rebuild_source": [
                "sim_rebuild_004_xi_rho_ab_bridge_family_from_readonly.py",
                "sim_rebuild_005_qit_fep_axis0_batch_from_clean_xi.py",
            ],
            "reads_clean_rebuild_results": False,
        },
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "out": str(OUT_PATH)}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

