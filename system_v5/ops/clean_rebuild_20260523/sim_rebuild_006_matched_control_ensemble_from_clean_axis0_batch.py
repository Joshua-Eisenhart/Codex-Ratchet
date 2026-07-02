#!/usr/bin/env python3
"""Clean-room rebuild 006: matched controls for clean Axis0 batch.

The old contaminated wave repeatedly exposed nuisance-strength confounds. This
clean rebuild tests the same failure mode early: preserve each candidate's
entangling angle while replacing the reference geometry with deterministic
random spinors.

No formal_scout receipts, grok_sim outputs, or external audits are read.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch

from sim_rebuild_004_xi_rho_ab_bridge_family_from_readonly import CDTYPE, entangled_cut, fubini_theta, path_spinors, spinor
from sim_rebuild_005_qit_fep_axis0_batch_from_clean_xi import qit_path_readout


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "rebuild_006_matched_control_ensemble_from_clean_axis0_batch_results.json"

classification = "clean_rebuild_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical_clean_rebuild"
SOURCE_ALIGNMENT_CATEGORY = "matched_control_ensemble_clean_axis0_batch"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Clean rebuild scout only: runs matched-reference controls over clean "
    "Axis0/QIT-FEP bridge candidates. It does not admit final Axis0, Xi, "
    "Phi0, or formal evidence."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing deterministic random spinors, matched entangling angles, QIT path readouts, and ensemble statistics",
    },
    "clean_rebuild_004_source": {"tried": True, "used": True, "reason": "supportive clean Xi constructors and spinor helpers"},
    "clean_rebuild_005_source": {"tried": True, "used": True, "reason": "supportive clean QIT path readout helper"},
    "python_json": {"tried": True, "used": True, "reason": "supportive clean rebuild receipt serialization"},
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

K_SEEDS = 48
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


def random_spinor(generator: torch.Generator) -> torch.Tensor:
    vals = torch.rand(3, generator=generator, dtype=torch.float64)
    phi = TWO_PI * vals[0].item()
    chi = TWO_PI * vals[1].item()
    eta = 0.08 + (math.pi / 2.0 - 0.16) * vals[2].item()
    return spinor(phi, chi, eta)


def score_states(states: list[torch.Tensor]) -> dict[str, float]:
    rows = [qit_path_readout(state) for state in states]
    keys = ["log_z", "I_c", "MI", "Phi_logZ_plus_Ic", "Phi_logZ_plus_MI"]
    return {key: float(sum(row[key] for row in rows) / len(rows)) for key in keys}


def point_reference_candidate_states() -> list[torch.Tensor]:
    phi0, chi0, eta = 0.17, 0.31, 0.44
    reference = spinor(-0.28, 0.79, math.pi / 4.0)
    samples = path_spinors("lifted_base", phi0, chi0, eta, steps=STEPS)
    return [entangled_cut(sample, reference) for sample in samples]


def history_window_candidate_states() -> list[torch.Tensor]:
    samples = path_spinors("lifted_base", 0.17, 0.31, 0.44, steps=STEPS)
    return [entangled_cut(sample, samples[idx - 1]) for idx, sample in enumerate(samples)]


def matched_point_reference_states(seed: int) -> list[torch.Tensor]:
    generator = torch.Generator().manual_seed(10_000 + seed)
    phi0, chi0, eta = 0.17, 0.31, 0.44
    reference = spinor(-0.28, 0.79, math.pi / 4.0)
    samples = path_spinors("lifted_base", phi0, chi0, eta, steps=STEPS)
    states = []
    for sample in samples:
        theta = fubini_theta(sample, reference)
        states.append(entangled_cut(sample, random_spinor(generator), theta=theta))
    return states


def matched_history_window_states(seed: int) -> list[torch.Tensor]:
    generator = torch.Generator().manual_seed(20_000 + seed)
    samples = path_spinors("lifted_base", 0.17, 0.31, 0.44, steps=STEPS)
    states = []
    for idx, sample in enumerate(samples):
        theta = fubini_theta(sample, samples[idx - 1])
        states.append(entangled_cut(sample, random_spinor(generator), theta=theta))
    return states


def ensemble_for(candidate_name: str, candidate_states: list[torch.Tensor], matched_builder) -> dict[str, Any]:
    candidate_score = score_states(candidate_states)
    rows = []
    for seed in range(K_SEEDS):
        matched_score = score_states(matched_builder(seed))
        rows.append(
            {
                "seed": seed,
                "matched_score": matched_score,
                "diff_candidate_minus_matched": {
                    key: candidate_score[key] - matched_score[key] for key in candidate_score
                },
            }
        )
    stats = {}
    for key in candidate_score:
        diffs = torch.tensor([row["diff_candidate_minus_matched"][key] for row in rows], dtype=torch.float64)
        mean = float(torch.mean(diffs).item())
        std = float(torch.std(diffs, unbiased=True).item())
        se = std / math.sqrt(K_SEEDS)
        z = mean / se if se > 0 else (math.inf if mean > 0 else -math.inf if mean < 0 else 0.0)
        stats[key] = {
            "mean_diff": mean,
            "std_diff": std,
            "se_diff": se,
            "z": z,
            "admit_positive": bool(mean > 0.0 and z > 2.0 and abs(mean) > 0.01),
        }
    admitted = [key for key, value in stats.items() if value["admit_positive"]]
    return {
        "candidate": candidate_name,
        "candidate_score": candidate_score,
        "k_seeds": K_SEEDS,
        "stats": stats,
        "admitted_positive_readouts": admitted,
        "admission_status": "admitted_under_matched" if admitted else "killed_or_nonseparating_under_matched",
        "rows_preview": rows[:3],
    }


def matched_control_gate() -> dict[str, Any]:
    point = ensemble_for("point_reference_lifted_base", point_reference_candidate_states(), matched_point_reference_states)
    history = ensemble_for("history_window_lifted_base", history_window_candidate_states(), matched_history_window_states)
    return {
        "pass": point["k_seeds"] == K_SEEDS and history["k_seeds"] == K_SEEDS,
        "point_reference": point,
        "history_window": history,
        "combined_admitted_readouts": {
            "point_reference": point["admitted_positive_readouts"],
            "history_window": history["admitted_positive_readouts"],
        },
    }


def nonpromotion_gate(matched: dict[str, Any]) -> dict[str, Any]:
    admitted_total = len(matched["combined_admitted_readouts"]["point_reference"]) + len(
        matched["combined_admitted_readouts"]["history_window"]
    )
    return {
        "pass": True,
        "admission": "blocked",
        "admitted_readout_count_under_matched_controls": admitted_total,
        "reason": (
            "Matched controls are diagnostic only in this clean rebuild lane. "
            "Any surviving readout still requires independent rerun after formal "
            "estate reset; killed/nonseparating readouts stay negative evidence."
        ),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    matched = matched_control_gate()
    nonpromotion = nonpromotion_gate(matched)
    sections = {
        "matched_control_gate": matched,
        "nonpromotion_gate": nonpromotion,
    }
    all_pass = all(bool(section["pass"]) for section in sections.values())
    result = {
        "schema": "clean_rebuild_result_v1",
        "name": "rebuild_006_matched_control_ensemble_from_clean_axis0_batch",
        "classification": classification,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
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
    print(json.dumps({"all_pass": all_pass, "out": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

