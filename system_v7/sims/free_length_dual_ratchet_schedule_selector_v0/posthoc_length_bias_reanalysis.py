#!/usr/bin/env python3
"""Post-hoc sensitivity audit for length-coupled selector terms.

This is not preregistered and cannot flip the v0 verdict. It tests whether the
existing red is an artifact of the MDL penalty or fixed-total exposure.
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
SPEC = HERE / "spec.json"
CATALOG = RESULTS / "candidate_catalog.json"
RAW = RESULTS / "free_length_dual_ratchet_schedule_selector_v0_raw_scores.json"
OUTPUT = RESULTS / "posthoc_length_bias_reanalysis.json"
EXPECTED = {
    SPEC: "1a4530ed6d807ac02024c2cbf52b15bef504811c2e49bb3848175a0a92509397",
    CATALOG: "19480a92baafee069f66928fde10f2fa26309742ddd8d9ad29839c85950c4163",
    RAW: "8193955d34153c1625876bfd9777d57cc0b0f6e5fd8f9a49459bb87965186300",
}

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
SIM_EXECUTION_KIND = "nonclassical"
TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing decoding and exact re-ranking of retained raw score arrays",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive hash binding and deterministic JSON serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing", "python_stdlib": "supportive"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_array(row: dict[str, Any]) -> np.ndarray:
    payload = base64.b64decode(row["data"], validate=True)
    if hashlib.sha256(payload).hexdigest() != row["sha256"]:
        raise ValueError("raw array hash mismatch")
    value = np.frombuffer(payload, dtype=np.dtype(row["dtype"]))
    return value.reshape(row["shape"])


def summarize(
    scores: np.ndarray,
    candidates: list[dict[str, Any]],
    engines: list[str],
    spec: dict[str, Any],
) -> dict[str, Any]:
    delta = float(spec["selection_rule"]["scientific_margin_delta"])
    absolute = float(spec["selection_rule"]["tie_absolute_tolerance"])
    relative = float(spec["selection_rule"]["tie_relative_tolerance"])
    result: dict[str, Any] = {}
    for engine_index, engine in enumerate(engines):
        winner_counts: dict[str, int] = {}
        qualifying_counts: dict[str, int] = {}
        winner_length_counts: dict[str, int] = {}
        for scenario_index in range(scores.shape[0]):
            values = scores[scenario_index, engine_index]
            order = np.argsort(values, kind="stable")
            best = float(values[order[0]])
            tolerance = absolute + relative * abs(best)
            winners = np.flatnonzero(values <= best + tolerance)
            for index in winners:
                row = candidates[int(index)]
                winner_counts[row["cycle_id"]] = winner_counts.get(row["cycle_id"], 0) + 1
                key = str(row["length"])
                winner_length_counts[key] = winner_length_counts.get(key, 0) + 1
            if len(winners) != 1:
                continue
            winner = candidates[int(winners[0])]
            margin = float(values[order[1]] - best)
            qualifies = (
                winner["length"] == 4
                and winner["primitive_period"] == 4
                and winner["uses_all_four_exactly_once"] is True
                and margin > delta
            )
            if qualifies:
                cycle = winner["cycle_id"]
                qualifying_counts[cycle] = qualifying_counts.get(cycle, 0) + 1
        result[engine] = {
            "scenario_count": int(scores.shape[0]),
            "winner_counts": dict(sorted(winner_counts.items())),
            "winner_length_counts": dict(sorted(winner_length_counts.items())),
            "qualifying_primitive_length4_all_four_once_counts": dict(sorted(qualifying_counts.items())),
        }
    return result


def main() -> int:
    for path, expected in EXPECTED.items():
        if sha256(path) != expected:
            raise RuntimeError(f"frozen input hash mismatch: {path}")
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    candidates = catalog["candidates"]
    engines = raw["engine_axis"]

    geometry = decode_array(raw["arrays"]["geometry_loss"])
    entropy = decode_array(raw["arrays"]["entropy_loss"])
    zero_mdl_scores = np.maximum(geometry, entropy)
    fixed_per_beat_scores = decode_array(
        raw["control_combined_score_arrays"]["fixed_per_beat_exposure"]
    )
    zero_mdl = summarize(zero_mdl_scores, candidates, engines, spec)
    fixed_per_beat = summarize(fixed_per_beat_scores, candidates, engines, spec)
    no_qualifiers = all(
        not row["qualifying_primitive_length4_all_four_once_counts"]
        for analysis in (zero_mdl, fixed_per_beat)
        for row in analysis.values()
    )

    output = {
        "schema": "codex_ratchet.free_length_dual_ratchet_schedule_selector_v0.posthoc_length_bias.v1",
        "classification": "posthoc_sensitivity_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "preregistered": False,
        "input_hashes": {str(path.relative_to(HERE)): digest for path, digest in EXPECTED.items()},
        "analyses": {
            "zero_mdl_penalty": zero_mdl,
            "fixed_per_beat_exposure_existing_control": fixed_per_beat,
        },
        "all_length_bias_analyses_have_no_qualifying_primitive_length4_all_four_once_cycle": no_qualifiers,
        "verdict": "RED_SURVIVES_POSTHOC_MDL_ERASURE_AND_FIXED_PER_BEAT_SENSITIVITY"
        if no_qualifiers
        else "POSTHOC_SENSITIVITY_FINDS_QUALIFIER_REQUIRES_NEW_PREREGISTERED_PACKET",
        "claim_ceiling": "Post-hoc sensitivity only. It can identify score-induced fragility but cannot promote or replace the preregistered v0 verdict.",
        "blocked_consumers": spec["blocked_consumers"],
    }
    OUTPUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
