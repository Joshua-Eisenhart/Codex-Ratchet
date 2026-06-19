#!/usr/bin/env python3
"""Packet-local validator for basin_two_engine_joint_v3_convention_sweep."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from basin_two_engine_joint_v3_convention_sweep_common import ROOT, SIM_DIR, RESULT_DIR, SIM_ID, rel, sha256_file, write_json


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


def validate_build_card(errors: list[str]) -> None:
    path = SIM_DIR / "build_card.md"
    require(errors, path.exists(), "build_card.md missing")
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    require(errors, "BUILD CARD - basin_two_engine_joint_v3_convention_sweep" in text, "build card title missing")
    require(errors, "TOOL_INTENT_MATRIX" in text, "build card TOOL_INTENT_MATRIX missing")
    require(errors, "scripts/build_three_engine_envelope.py" in text, "build card envelope helper rule missing")
    require(errors, "NO git add/commit" in text, "build card no-git boundary missing")


def validate_leg(errors: list[str], name: str, payload: dict[str, Any]) -> None:
    require(errors, payload.get("sim_id") == SIM_ID, f"{name} sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", f"{name} classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, f"{name} promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, f"{name} formal_admission_allowed must be false")
    require(errors, payload.get("reads_peer_result") is False, f"{name} reads_peer_result must be false")
    require(errors, payload.get("all_pass") is True, f"{name} all_pass must be true")
    require(errors, bool(payload.get("packages_used")), f"{name} packages_used missing")
    require(errors, bool(payload.get("aligned_packages_load_bearing")), f"{name} aligned load-bearing packages missing")
    require(errors, bool(payload.get("package_observables")), f"{name} package_observables missing")
    require(errors, payload.get("one_to_one_tool_calls", {}).get("pass") is True, f"{name} one-to-one tool calls failed")
    source = ROOT / payload.get("source_path", "")
    require(errors, source.exists(), f"{name} source path missing")
    if source.exists():
        require(errors, payload.get("source_sha256") == sha256_file(source), f"{name} source sha drift")
    require(errors, isinstance(payload.get("primary_terminal_counts"), dict), f"{name} primary terminal counts missing")


def validate_variant(errors: list[str], variant_id: str, row: dict[str, Any]) -> None:
    require(errors, row.get("variant_id") == variant_id, f"{variant_id} variant id mismatch")
    require(errors, "actual_class_lattice" in row, f"{variant_id} class lattice missing")
    require(errors, "controls" in row, f"{variant_id} controls missing")
    controls = row.get("controls", {})
    order = controls.get("order_shuffled", {})
    label = controls.get("label_permutation", {})
    merge = controls.get("dissipative_merge", {})
    require(errors, isinstance(order.get("changed_terminal_structure_by_mode"), dict), f"{variant_id} order control missing")
    require(errors, label.get("all_pass") is True, f"{variant_id} label permutation must pass")
    require(errors, merge.get("accepted_as_primary_evidence") is False, f"{variant_id} dissipative merge accepted as primary")
    if order.get("changed_any_primary_terminal_structure") is not True:
        require(
            errors,
            row.get("source_valid_under_B_controls") is False
            and "order_blind_under_B_control" in row.get("invalid_reasons", []),
            f"{variant_id} order-blind row not excluded",
        )
    if row.get("contrast_only") is True:
        require(
            errors,
            row.get("source_valid_under_B_controls") is False
            and "contrast_only_not_source_admitted" in row.get("invalid_reasons", []),
            f"{variant_id} contrast row not excluded",
        )
    for mode, summary in row.get("actual_class_lattice", {}).items():
        require(errors, summary.get("state_count") == 1024, f"{variant_id}/{mode} state count must be 1024")
        require(errors, summary.get("terminal_class_count") is not None, f"{variant_id}/{mode} terminal count missing")


def validate_envelope(errors: list[str], env: dict[str, Any], legs: dict[str, dict[str, Any]]) -> None:
    require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, env.get("sim_id") == SIM_ID, "envelope sim_id mismatch")
    require(errors, env.get("classification") == "scratch_diagnostic", "envelope classification mismatch")
    require(errors, env.get("promotion_allowed") is False, "envelope promotion_allowed must be false")
    require(errors, env.get("formal_admission_allowed") is False, "envelope formal_admission_allowed must be false")
    require(errors, env.get("all_pass") is True, "envelope all_pass must be true")
    require(errors, set(env.get("engines", {})) == {"julia", "jax", "pytorch"}, "envelope must include all three engines")
    require(errors, env.get("engine_contract", {}).get("omitted_lanes") == {}, "no lane may be omitted")
    require(errors, env.get("tool_intent", {}).get("claim_classes"), "tool_intent claim classes missing")
    for engine, rec in env.get("engines", {}).items():
        intent = env.get("tool_intent", {}).get("engine_tool_intent", {}).get(engine, {})
        for package in rec.get("aligned_packages_load_bearing", []):
            require(errors, package in intent, f"tool_intent missing {engine}.{package}")
            require(errors, package in rec.get("package_observables", {}), f"package_observables missing {engine}.{package}")

    joint = env.get("joint_object", {})
    require(errors, joint.get("per_engine_state_count") == 32, "per-engine state count must be 32")
    require(errors, joint.get("joint_state_count") == 1024, "joint state count must be 1024")
    variants = env.get("convention_variants", {})
    require(errors, set(variants) >= {"A_readout_transition_dwell", "v2_cyclic_wrap_contrast"}, "expected variants missing")
    for variant_id, row in variants.items():
        validate_variant(errors, variant_id, row)

    adjudication = env.get("prediction_adjudication", {})
    require(errors, adjudication.get("pre_registered_count") == 64, "pre-registered count mismatch")
    require(errors, adjudication.get("registered_product") == "2 engines x 2 loops x 4 stages x 4 substages", "registered product mismatch")
    for observed in adjudication.get("source_valid_primary_64_levels", []):
        product = observed.get("product_test", {})
        require(errors, product.get("status") == "registered_product_projection_checked", "source-valid 64 lacks product test")
    controls = env.get("controls", {})
    v1 = controls.get("v1_replication", {})
    require(errors, v1.get("status") == "by_construction_baseline", "v1 baseline status mismatch")
    require(errors, v1.get("coarse_8x8_reproduces_64") is True, "v1 baseline did not reproduce 64")
    require(errors, v1.get("accepted_as_primary_evidence") is False, "v1 baseline accepted as evidence")
    proofs = env.get("crossover_proofs", {})
    require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 count identity must be unsat")
    require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 count identity must be unsat")
    require(errors, proofs.get("z3", {}).get("flipped_control_verdict") == "sat", "z3 flipped control must be sat")
    require(errors, proofs.get("cvc5", {}).get("flipped_control_verdict") == "sat", "cvc5 flipped control must be sat")
    require(errors, proofs.get("julia_z3", {}).get("verdict") == "unsat", "julia_z3 count identity must be unsat")
    comparison = env.get("engine_comparison", {})
    require(errors, comparison.get("primary_terminal_count_agreement") is True, "engine primary counts disagree")
    require(errors, comparison.get("source_valid_primary_64_level_count_agreement") is True, "engine source-valid 64 counts disagree")
    require(errors, env.get("divergence", {}).get("max_divergence") == 0.0, "engine divergence must be zero")
    gates = env.get("build_gates", {})
    for key, value in gates.items():
        require(errors, value is True, f"build gate {key} must be true")
    for section in ("positive", "negative", "boundary"):
        require(errors, bool(env.get("evidence_sections", {}).get(section)), f"{section} evidence section missing")
    errors.extend(builder_audit_boundary_errors(env, SIM_DIR / "audit_verdict.md"))
    for name in ("julia", "jax", "pytorch"):
        require(errors, legs.get(name, {}).get("all_pass") is True, f"{name} leg did not pass")


def main() -> int:
    errors: list[str] = []
    validate_build_card(errors)
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
