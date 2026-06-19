#!/usr/bin/env python3
"""Packet-local validator for basin_two_engine_joint_v2."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from basin_two_engine_joint_v2_common import ROOT, SIM_DIR, RESULT_DIR, SIM_ID, rel, sha256_file, write_json


RESULT_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
    "envelope": RESULT_DIR / f"{SIM_ID}_envelope_results.json",
}
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def scan_forbidden_words(errors: list[str]) -> None:
    forbidden = ["fix" + "ture", "to" + "y", "mo" + "ck", "dum" + "my"]
    for path in SIM_DIR.rglob("*"):
        if "__pycache__" in path.parts:
            continue
        if not path.is_file() or path.name == f"{SIM_ID}_validator_results.json":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for word in forbidden:
            if word in text:
                errors.append(f"forbidden wording {word!r} appears in {rel(path)}")


def validate_leg(errors: list[str], name: str, payload: dict[str, Any]) -> None:
    require(errors, payload.get("sim_id") == SIM_ID, f"{name} sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", f"{name} classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, f"{name} promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, f"{name} formal_admission_allowed must be false")
    require(errors, payload.get("reads_peer_result") is False, f"{name} reads_peer_result must be false")
    require(errors, payload.get("all_pass") is True, f"{name} all_pass must be true")
    require(errors, bool(payload.get("packages_used")), f"{name} packages_used missing")
    require(errors, bool(payload.get("aligned_packages_load_bearing")), f"{name} aligned load-bearing packages missing")
    require(errors, payload.get("one_to_one_tool_calls", {}).get("pass") is True, f"{name} one-to-one tool calls failed")
    source = ROOT / payload.get("source_path", "")
    require(errors, source.exists(), f"{name} source path missing")
    if source.exists():
        require(errors, payload.get("source_sha256") == sha256_file(source), f"{name} source sha drift")
    require(errors, payload.get("primary_64_level_count") == 0, f"{name} primary 64 count must be zero")
    require(errors, payload.get("control_terminal_class_count") == 64, f"{name} control terminal count must be 64")


def validate_envelope(errors: list[str], env: dict[str, Any], legs: dict[str, dict[str, Any]]) -> None:
    require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, env.get("sim_id") == SIM_ID, "envelope sim_id mismatch")
    require(errors, env.get("classification") == "scratch_diagnostic", "envelope classification mismatch")
    require(errors, env.get("promotion_allowed") is False, "envelope promotion_allowed must be false")
    require(errors, env.get("formal_admission_allowed") is False, "envelope formal_admission_allowed must be false")
    require(errors, env.get("all_pass") is True, "envelope all_pass must be true")
    require(errors, set(env.get("engines", {})) == {"julia", "jax", "pytorch"}, "envelope must include all three engines")
    joint = env.get("joint_object", {})
    require(errors, joint.get("per_engine_state_count") == 32, "per-engine state count must be 32")
    require(errors, joint.get("joint_state_count") == 1024, "joint state count must be 1024")
    adjudication = env.get("prediction_adjudication", {})
    require(errors, adjudication.get("pre_registered_count") == 64, "pre-registered count mismatch")
    require(errors, adjudication.get("primary_64_level_count") == 0, "primary 64 level count must be zero")
    require(errors, adjudication.get("computed_primary_64_level") is False, "primary 64 must not be reported")
    require(errors, adjudication.get("product_test", {}).get("status") == "not_run_no_primary_64_level", "primary product test status mismatch")
    hierarchy = env.get("hierarchy", {})
    primary = hierarchy.get("primary_rows", {})
    require(errors, primary.get("source_sync_full_tick", {}).get("terminal_class_count") == 32, "sync full tick must have 32 terminal classes")
    require(errors, primary.get("source_l_only_full_tick", {}).get("terminal_class_count") == 32, "L-only full tick must have 32 terminal classes")
    require(errors, primary.get("source_r_only_full_tick", {}).get("terminal_class_count") == 32, "R-only full tick must have 32 terminal classes")
    require(errors, primary.get("source_async_lr_union_full_tick", {}).get("terminal_class_count") == 1, "async LR union must have one terminal class")
    for row_id, row in primary.items():
        require(errors, bool(row.get("terminal_classes")), f"{row_id} terminal rows missing")
        require(errors, bool(row.get("morse_ordering", {}).get("nodes")), f"{row_id} Morse nodes missing")
        require(errors, bool(row.get("may_must_partition", {}).get("rows")), f"{row_id} may/must rows missing")
        for terminal in row.get("terminal_classes", []):
            require(errors, terminal.get("absent_exit_proof", {}).get("no_exit") is True, f"{row_id} terminal absent-exit proof failed")
    controls = env.get("controls", {})
    require(errors, controls.get("label_permutation", {}).get("all_pass") is True, "label permutation failed")
    require(errors, controls.get("decode_test", {}).get("passed") is True, "decode test failed")
    require(errors, controls.get("root_off", {}).get("fired") is True, "root-off did not fire")
    require(errors, controls.get("v1_replication", {}).get("status") == "by_construction_baseline", "v1 baseline status mismatch")
    require(errors, controls.get("v1_replication", {}).get("coarse_8x8_reproduces_v1_64") is True, "v1 baseline did not reproduce 64")
    require(errors, controls.get("v1_replication", {}).get("accepted_as_primary_evidence") is False, "v1 baseline accepted as evidence")
    merge = controls.get("dissipative_merge", {})
    require(errors, merge.get("terminal_class_count_less_than_1024") is True, "merge control did not merge")
    require(errors, merge.get("control_terminal_class_count") == 64, "merge control terminal count mismatch")
    require(errors, merge.get("accepted_as_primary_evidence") is False, "merge control accepted as primary")
    proofs = env.get("crossover_proofs", {})
    require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 proof must be unsat")
    require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 proof must be unsat")
    require(errors, proofs.get("julia_z3", {}).get("verdict") == "unsat", "julia_z3 proof must be unsat")
    require(errors, proofs.get("z3", {}).get("erased_flip_verdict") == "sat", "z3 erased flip must be sat")
    require(errors, proofs.get("cvc5", {}).get("erased_flip_verdict") == "sat", "cvc5 erased flip must be sat")
    comparison = env.get("engine_comparison", {})
    require(errors, comparison.get("primary_64_level_count_agreement") is True, "engine primary counts disagree")
    require(errors, comparison.get("control_terminal_count_agreement") is True, "engine control counts disagree")
    require(errors, env.get("divergence", {}).get("max_divergence") == 0.0, "engine divergence must be zero")
    errors.extend(builder_audit_boundary_errors(env, SIM_DIR / "audit_verdict.md"))
    gates = env.get("build_gates", {})
    for key, value in gates.items():
        require(errors, value is True, f"build gate {key} must be true")
    for name in ("julia", "jax", "pytorch"):
        require(errors, legs.get(name, {}).get("all_pass") is True, f"{name} leg did not pass")


def main() -> int:
    errors: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    for name, path in RESULT_PATHS.items():
        if not path.exists():
            errors.append(f"missing result {rel(path)}")
            continue
        payloads[name] = load(path)
    for name in ("julia", "jax", "pytorch"):
        if name in payloads:
            validate_leg(errors, name, payloads[name])
    if "envelope" in payloads and all(name in payloads for name in ("julia", "jax", "pytorch")):
        validate_envelope(errors, payloads["envelope"], payloads)
    scan_forbidden_words(errors)
    result = {
        "ok": not errors,
        "errors": errors,
        "result_json": rel(RESULT_PATHS["envelope"]),
        "validator": rel(Path(__file__).resolve()),
    }
    write_json(VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
