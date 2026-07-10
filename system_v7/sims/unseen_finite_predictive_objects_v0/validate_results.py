#!/usr/bin/env python3
"""Independent fail-closed controller for the UFPO v0 pilot."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from fractions import Fraction
from itertools import product
from pathlib import Path
from typing import Any, Iterable


classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "nonclassical"
TOOL_MANIFEST = {
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing strict receipt validation and exact no-input baseline recomputation",
    }
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "load_bearing"}

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC = HERE / "spec.json"
MANIFEST = HERE / "object_manifest.json"
PREREG_VALIDATION = HERE / "results" / "preregistration_validation.json"
JULIA_RESULT = HERE / "results" / "julia_result.json"
JAX_RESULT = HERE / "results" / "unseen_finite_predictive_objects_v0_jax_results.json"
PYTORCH_SOURCE = HERE / "run_pytorch.py"
PYTORCH_RESULT = HERE / "results" / "pytorch_result.json"
OUTPUT = HERE / "results" / "controller_result.json"


class ControllerError(RuntimeError):
    pass


def reject_constant(token: str) -> None:
    raise ControllerError(f"non-finite JSON constant: {token}")


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ControllerError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def load(path: Path, required: bool = True) -> dict[str, Any] | None:
    if not path.is_file():
        if required:
            raise ControllerError(f"missing required input: {path}")
        return None
    value = json.loads(
        path.read_text(encoding="utf-8"),
        parse_constant=reject_constant,
        object_pairs_hook=reject_duplicates,
    )
    if not isinstance(value, dict):
        raise ControllerError(f"{path} must contain one JSON object")
    return value


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def word_probability(
    machine: list[list[int]], start: int, word: Iterable[int]
) -> Fraction:
    state = start
    probability = Fraction(1)
    for symbol in word:
        next_zero, next_one, p_one = machine[state]
        probability *= Fraction(p_one if symbol else 8 - p_one, 8)
        state = next_one if symbol else next_zero
    return probability


def signature(machine: list[list[int]]) -> list[list[Fraction]]:
    segments: list[list[Fraction]] = []
    for length in range(1, 9):
        segment = []
        for word in product((0, 1), repeat=length):
            total = sum(
                (word_probability(machine, state, word) for state in range(4)),
                Fraction(0),
            )
            segment.append(total / 4)
        if sum(segment, Fraction(0)) != 1:
            raise ControllerError("exact predictive segment is not normalized")
        segments.append(segment)
    return segments


def js(left: list[Fraction], right: list[Fraction]) -> float:
    total = 0.0
    for left_value, right_value in zip(left, right, strict=True):
        a = float(left_value)
        b = float(right_value)
        midpoint = 0.5 * (a + b)
        if a:
            total += 0.5 * a * math.log(a / midpoint)
        if b:
            total += 0.5 * b * math.log(b / midpoint)
    return total


def no_input_baseline(manifest: dict[str, Any]) -> dict[str, Any]:
    train = [signature(row["machine"]) for row in manifest["splits"]["train"]]
    test = [signature(row["machine"]) for row in manifest["splits"]["test"]]
    mean_segments = [
        [
            sum((item[length][coordinate] for item in train), Fraction(0))
            / len(train)
            for coordinate in range(len(train[0][length]))
        ]
        for length in range(8)
    ]
    per_object = [
        sum(js(mean_segments[length], target[length]) for length in range(8)) / 8
        for target in test
    ]
    ordered = sorted(per_object)
    return {
        "kind": "exact_train_mean_signature_with_no_view_input",
        "test_object_count": len(per_object),
        "mean_predictive_js": sum(per_object) / len(per_object),
        "median_predictive_js": 0.5 * (ordered[15] + ordered[16]),
        "minimum_predictive_js": ordered[0],
        "maximum_predictive_js": ordered[-1],
        "per_object_predictive_js": per_object,
    }


def source_tracked() -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(PYTORCH_SOURCE.relative_to(REPO))],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def recomputable_output_present(result: dict[str, Any] | None) -> bool:
    if result is None:
        return False
    arms = result.get("arm_results")
    if not isinstance(arms, dict):
        return False
    for seed_rows in arms.values():
        if not isinstance(seed_rows, dict):
            return False
        for row in seed_rows.values():
            outputs = (row.get("metrics") or {}).get("frozen_outputs") or {}
            required = {
                "cluster_assignments",
                "object_labels",
                "segmented_js_by_view",
                "short_horizon_matched_preference_checks",
            }
            if not required.issubset(outputs):
                return False
    return True


def main() -> int:
    spec = load(SPEC)
    manifest = load(MANIFEST)
    prereg = load(PREREG_VALIDATION)
    julia = load(JULIA_RESULT)
    jax = load(JAX_RESULT)
    pytorch = load(PYTORCH_RESULT, required=False)
    assert spec is not None and manifest is not None
    assert prereg is not None and julia is not None and jax is not None

    baseline = no_input_baseline(manifest)
    threshold = float(spec["metrics_and_gates"]["every_seed_predictive_js_max"])
    tracked_now = source_tracked()
    pytorch_hash_matches = bool(
        pytorch is not None
        and tracked_now
        and pytorch.get("source_sha256") == sha(PYTORCH_SOURCE)
    )
    gates = {
        "preregistration_validation": prereg.get("all_pass") is True,
        "julia_local_semantic_verification": julia.get("engine_all_pass") is True,
        "julia_packet_gate_stays_pending": julia.get("all_pass") is False,
        "jax_local_workhorse_verification": jax.get("all_local_gates_pass") is True,
        "jax_packet_gate_stays_pending": jax.get("all_pass") is False,
        "learner_source_tracked_before_test_evaluation": False,
        "current_learner_source_is_tracked": tracked_now,
        "pytorch_source_hash_matches": pytorch_hash_matches,
        "no_input_baseline_fails_absolute_js_threshold": baseline[
            "mean_predictive_js"
        ]
        > threshold,
        "pytorch_metrics_independently_recomputable": recomputable_output_present(
            pytorch
        ),
        "nonvacuous_torch_func_temporal_control": False,
    }
    fatal = [name for name, passed in gates.items() if not passed]
    result = {
        "schema": "codex_ratchet.unseen_finite_predictive_objects_v0.controller_result.v1",
        "sim_id": spec["sim_id"],
        "classification": classification,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "source_path": str(Path(__file__).resolve().relative_to(REPO)),
        "source_sha256": sha(Path(__file__).resolve()),
        "input_hashes": {
            "spec": sha(SPEC),
            "manifest": sha(MANIFEST),
            "preregistration_validation": sha(PREREG_VALIDATION),
            "julia_result": sha(JULIA_RESULT),
            "jax_result": sha(JAX_RESULT),
            "pytorch_source": sha(PYTORCH_SOURCE),
            "pytorch_result": sha(PYTORCH_RESULT) if PYTORCH_RESULT.is_file() else None,
        },
        "no_input_baseline": baseline,
        "frozen_predictive_js_threshold": threshold,
        "gates": gates,
        "fatal_blockers": fatal,
        "all_scientific_gates_pass": False,
        "all_pass": False,
        "status": "RED_V0_PILOT_PROSPECTIVE_LEARNING_CLAIM_INVALID",
        "accepted_claim_label": spec["accepted_red_ceiling"],
        "allowed_exact_ceiling": "Julia independently validates the frozen Python-proposed semantic records; the Python/JAX lane independently recomputes exact predictive numerators and matches the manifest",
        "blocked_consumers": spec["blocked_consumers"],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"all_pass": False, "fatal_blockers": fatal}, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
