#!/usr/bin/env python3
"""Independent fail-closed all-three controller for the frozen UFPO v1 run."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RESULTS = HERE / "results"
PATHS = {"spec": HERE / "spec.json", "manifest": HERE / "object_manifest.json",
         "preregistration": RESULTS / "preregistration_validation.json",
         "julia": RESULTS / "julia_result.json",
         "jax": RESULTS / "unseen_finite_predictive_objects_v1_jax_results.json",
         "pytorch": RESULTS / "pytorch_result.json"}
SOURCES = {"julia": HERE / "run_julia.jl", "jax": HERE / "run_jax.py",
           "pytorch": HERE / "run_pytorch.py", "recompute_metrics": HERE / "recompute_metrics.py",
           "controller": Path(__file__).resolve()}
OUTPUT = RESULTS / "controller_result.json"
SIM_ID = "unseen_finite_predictive_objects_v1"
GREEN = "BOUNDED_SUPERVISED_MULTI_VIEW_PREDICTIVE_RETRIEVAL_ON_UNSEEN_FOUR_STATE_OBJECTS_UNDER_FROZEN_LOSSY_VIEWS"
RED = "UNSEEN_PREDICTIVE_OBJECT_LEARNING_NOT_ESTABLISHED"


class ControllerError(RuntimeError):
    pass


def reject_constant(token: str) -> None:
    raise ControllerError(f"non-finite JSON constant: {token}")


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ControllerError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def loads(text: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(text, parse_constant=reject_constant, object_pairs_hook=reject_duplicates)
    except json.JSONDecodeError as exc:
        raise ControllerError(f"invalid JSON from {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ControllerError(f"{label} must contain one JSON object")
    return value


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ControllerError(f"missing required input: {path}")
    return loads(path.read_text(encoding="utf-8"), str(path))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ControllerError(message)


def recompute(pytorch_path: Path) -> dict[str, Any]:
    completed = subprocess.run([sys.executable, str(SOURCES["recompute_metrics"]), "--input", str(pytorch_path)],
                               cwd=REPO, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
        raise ControllerError(f"independent metric recomputation failed: {detail}")
    return loads(completed.stdout, "recompute_metrics.py")


def build() -> dict[str, Any]:
    spec, manifest, prereg, julia, jax, pytorch = (load(PATHS[name]) for name in ("spec", "manifest", "preregistration", "julia", "jax", "pytorch"))
    expected_sources = prereg.get("expected_source_sha256", {})
    source_hashes = {name: sha(path) for name, path in SOURCES.items()}
    input_hashes = {name: sha(path) for name, path in PATHS.items()}
    require(spec.get("accepted_green_ceiling") == GREEN and spec.get("accepted_red_ceiling") == RED, "spec claim ceiling drift")
    require(spec.get("engine_contract", {}).get("mode") == "all_three_full_sims", "engine mode drift")
    require(prereg.get("schema") == f"codex_ratchet.{SIM_ID}.preregistration_validation.v1" and prereg.get("all_pass") is True, "preregistration validation is not green")
    require(prereg.get("spec_sha256") == input_hashes["spec"] and prereg.get("object_manifest_sha256") == input_hashes["manifest"], "preregistration input hash drift")
    require(all(expected_sources.get(name) == value for name, value in source_hashes.items()), "owned source hash drift after preregistration validation")
    require(julia.get("schema") == "codex_ratchet.engine_leg_result.v1", "Julia result schema drift")
    require(jax.get("schema") == f"codex_ratchet.{SIM_ID}.jax_result.v1", "JAX result schema drift")
    require(pytorch.get("schema") == f"codex_ratchet.{SIM_ID}.pytorch_result.v1", "PyTorch result schema drift")
    for name, result in (("julia", julia), ("jax", jax), ("pytorch", pytorch)):
        require(result.get("spec_sha256") == input_hashes["spec"], f"{name} spec hash mismatch")
        require(result.get("object_manifest_sha256") == input_hashes["manifest"], f"{name} manifest hash mismatch")
        require(result.get("source_sha256") == source_hashes[name], f"{name} source hash mismatch")
    require(julia.get("engine_all_pass") is True and julia.get("all_pass") is False, "Julia local pass/pending-controller contract drift")
    require(julia.get("claim_ceiling") == RED, "Julia exceeded pending-controller claim ceiling")
    require(jax.get("all_local_gates_pass") is True and jax.get("all_pass") is False, "JAX local pass/pending-controller contract drift")
    require(jax.get("claim_ceiling") == RED, "JAX exceeded pending-controller claim ceiling")
    require(pytorch.get("recompute_metrics_sha256") == source_hashes["recompute_metrics"], "PyTorch recompute source binding mismatch")
    require(pytorch.get("accepted_ceiling") in (GREEN, RED), "PyTorch claim ceiling is not exact")
    receipt = recompute(PATHS["pytorch"])
    require(receipt.get("schema") == f"codex_ratchet.{SIM_ID}.recompute_receipt.v1", "recompute receipt schema drift")
    require(receipt.get("spec_sha256") == input_hashes["spec"] and receipt.get("object_manifest_sha256") == input_hashes["manifest"], "recompute input hash mismatch")
    require(receipt.get("source_sha256") == source_hashes["pytorch"], "recompute learner source hash mismatch")
    require(receipt.get("raw_outputs_sha256") == pytorch.get("raw_outputs_sha256"), "recomputed raw-output hash mismatch")
    require(receipt.get("retrained") is False, "metric validator retrained learner")
    require(receipt.get("all_pass") is pytorch.get("all_pass"), "recomputed/PyTorch pass mismatch")
    require(pytorch.get("accepted_ceiling") == (GREEN if receipt["all_pass"] else RED), "PyTorch ceiling/pass mismatch")
    require(receipt.get("all_pass") is True, "one or more frozen scientific gates are red")
    return {
        "schema": f"codex_ratchet.{SIM_ID}.controller_result.v1", "sim_id": SIM_ID,
        "classification": "scratch_diagnostic", "source_path": str(Path(__file__).resolve().relative_to(REPO)),
        "source_sha256": source_hashes["controller"], "input_hashes": input_hashes,
        "engine_result_hashes": {name: input_hashes[name] for name in ("julia", "jax", "pytorch")},
        "source_hashes": source_hashes, "independent_recompute_receipt": receipt,
        "engine_contract": {"mode": "all_three_full_sims", "semantic_owner": "Julia independent exact finite predictive-equivalence verification and arbitration",
                            "pytorch_scope": "load-bearing supervised GRU/DeepSets learner and frozen controls for this bounded benchmark only",
                            "pytorch_broad_capability_not_claimed": True},
        "all_scientific_gates_pass": True, "all_pass": True, "fatal_blockers": [],
        "status": "GREEN_BOUNDED_FROZEN_V1_RESULT_ENVELOPE", "accepted_claim_label": GREEN,
        "blocked_consumers": spec["blocked_consumers"], "promotion_allowed": False, "formal_admission_allowed": False,
    }


def red(error: Exception) -> dict[str, Any]:
    hashes = {name: sha(path) if path.is_file() else None for name, path in PATHS.items()}
    return {"schema": f"codex_ratchet.{SIM_ID}.controller_result.v1", "sim_id": SIM_ID,
            "classification": "scratch_diagnostic", "source_path": str(Path(__file__).resolve().relative_to(REPO)),
            "source_sha256": sha(Path(__file__).resolve()), "input_hashes": hashes,
            "engine_result_hashes": {name: hashes[name] for name in ("julia", "jax", "pytorch")},
            "all_scientific_gates_pass": False, "all_pass": False, "fatal_blockers": [str(error)],
            "status": "RED_FAIL_CLOSED", "accepted_claim_label": RED,
            "pytorch_scope_note": "PyTorch is broadly capable, but this packet uses it only for the scoped frozen supervised learner and controls.",
            "promotion_allowed": False, "formal_admission_allowed": False}


def main() -> int:
    try:
        result = build()
    except Exception as exc:  # The controller must emit red for every malformed or missing dependency.
        result = red(exc)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "status": result["status"], "fatal_blockers": result["fatal_blockers"]}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
