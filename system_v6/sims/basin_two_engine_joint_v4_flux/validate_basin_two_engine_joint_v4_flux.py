#!/usr/bin/env python3
"""Packet-local validator for basin_two_engine_joint_v4_flux."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from basin_two_engine_joint_v4_flux_common import (
    BASELINE_EXPECTED,
    RESULT_DIR,
    ROOT,
    SIM_DIR,
    SIM_ID,
    rel,
    sha256_file,
    write_json,
)


RESULT_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
    "envelope": RESULT_DIR / f"{SIM_ID}_envelope_results.json",
}
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive validator result loading and emission"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive packet-local path checks"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_build_card(errors: list[str]) -> None:
    path = SIM_DIR / "build_card.md"
    require(errors, path.exists(), "build_card.md missing")
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    require(errors, "BUILD CARD" in text and SIM_ID in text, "build card title missing")
    require(errors, "NO git add/commit" in text, "build card no-git boundary missing")
    require(errors, "never write audit_verdict.md" in text, "build card no audit verdict boundary missing")
    require(errors, "BY_CONSTRUCTION FALSIFIER" in text, "build card by-construction falsifier missing")


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


def validate_stage1(errors: list[str], env: dict[str, Any]) -> None:
    stage1 = env.get("stage1", {})
    within = stage1.get("within_engine", {})
    for variant_id, expected in BASELINE_EXPECTED.items():
        require(errors, variant_id in within, f"stage1 variant {variant_id} missing")
        for engine in ("L", "R"):
            row = within.get(variant_id, {}).get(engine, {})
            erased = row.get("flux_erased", {})
            carried = row.get("flux_carried", {})
            require(errors, erased.get("terminal_class_count") == expected["terminal_class_count"], f"{variant_id}/{engine} erased count mismatch")
            require(errors, erased.get("terminal_sizes") == expected["terminal_sizes"], f"{variant_id}/{engine} erased core mismatch")
            require(errors, carried.get("state_count") == 64, f"{variant_id}/{engine} flux state count must be 64")
            require(errors, row.get("label_permutation_control", {}).get("all_pass") is True, f"{variant_id}/{engine} label control failed")
            for terminal in carried.get("terminal_classes", []):
                require(errors, terminal.get("absent_exit_proof", {}).get("no_exit") is True, f"{variant_id}/{engine} terminal lacks absent-exit proof")
    sign = stage1.get("sign_flip_control", {})
    require(errors, all(row.get("mirrors_nonzero_delta") is True for row in sign.values()), "sign flip control did not mirror")


def validate_stage2(errors: list[str], env: dict[str, Any]) -> None:
    stage2 = env.get("stage2", {})
    rows = stage2.get("coupling_rows", {})
    require(errors, rows, "stage2 coupling rows missing")
    for variant_id, coupling_rows in rows.items():
        require(errors, "C1_constrained_fibered_placement" in coupling_rows, f"{variant_id} C1 row missing")
        for coupling_id, row in coupling_rows.items():
            require(errors, row.get("state_count") == 4096, f"{variant_id}/{coupling_id} state count must be 4096")
            require(errors, row.get("terminal_class_count") is not None, f"{variant_id}/{coupling_id} terminal count missing")
            require(errors, row.get("by_construction") is False, f"{variant_id}/{coupling_id} primary graph row cannot be by-construction")
            require(errors, row.get("controls", {}).get("label_permutation", {}).get("all_pass") is True, f"{variant_id}/{coupling_id} label control failed")
            if row.get("accepted_as_primary_evidence") is True:
                require(errors, row.get("source_valid_under_controls") is True, f"{variant_id}/{coupling_id} primary row not source-valid under controls")
            for terminal in row.get("terminal_classes", []):
                require(errors, terminal.get("absent_exit_proof", {}).get("no_exit") is True, f"{variant_id}/{coupling_id} terminal lacks absent-exit proof")
    product = stage2.get("product_controls", {})
    require(errors, product, "product controls missing")
    for variant_id, control in product.items():
        require(errors, control.get("by_construction") is True, f"{variant_id} product control not marked by-construction")
        require(errors, control.get("accepted_as_primary_evidence") is False, f"{variant_id} product control accepted as evidence")
    checks = stage2.get("one_sided_projection_checks", [])
    require(errors, len(checks) == 4, "expected four one-sided frozen projection checks")
    for check in checks:
        require(errors, check.get("frozen_factor_echo_detected") is True, f"{check.get('variant_id')}/{check.get('coupling_id')} frozen echo not detected")
        require(errors, check.get("accepted_as_primary_evidence") is False, "one-sided check accepted as evidence")


def validate_envelope(errors: list[str], env: dict[str, Any], legs: dict[str, dict[str, Any]]) -> None:
    require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, env.get("sim_id") == SIM_ID, "envelope sim_id mismatch")
    require(errors, env.get("classification") == "scratch_diagnostic", "envelope classification mismatch")
    require(errors, env.get("promotion_allowed") is False, "envelope promotion_allowed must be false")
    require(errors, env.get("formal_admission_allowed") is False, "envelope formal_admission_allowed must be false")
    require(errors, env.get("all_pass") is True, "envelope all_pass must be true")
    require(errors, set(env.get("engines", {})) == {"julia", "jax", "pytorch"}, "envelope must include all three engines")
    require(errors, env.get("engine_contract", {}).get("omitted_lanes") == {}, "no lane may be omitted")
    require(errors, env.get("TOOL_INTENT_MATRIX", {}).get("claim_classes"), "TOOL_INTENT_MATRIX claim classes missing")
    validate_stage1(errors, env)
    validate_stage2(errors, env)
    controls = env.get("controls", {})
    require(errors, controls.get("flux_erased_continuity", {}).get("all_pass") is True, "flux-erased continuity failed")
    adjudication = env.get("prediction_adjudication", {})
    require(errors, adjudication.get("pre_registered_owner_count") == 64, "owner count mismatch")
    require(errors, adjudication.get("source_valid_primary_64_level_count") == 0, "unexpected source-valid primary 64 row")
    require(errors, adjudication.get("realization_relative_only") is True, "realization-relative fence missing")
    require(errors, adjudication.get("no_canonical_confirmation_or_disproof") is True, "canonical fence missing")
    proofs = env.get("crossover_proofs", {})
    require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 count identity must be unsat")
    require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 count identity must be unsat")
    require(errors, proofs.get("z3", {}).get("flipped_control_verdict") == "sat", "z3 flipped control must be sat")
    require(errors, proofs.get("cvc5", {}).get("flipped_control_verdict") == "sat", "cvc5 flipped control must be sat")
    require(errors, proofs.get("julia_z3", {}).get("verdict") == "unsat", "julia_z3 count identity must be unsat")
    comparison = env.get("engine_comparison", {})
    require(errors, comparison.get("primary_terminal_count_agreement") is True, "engine primary counts disagree")
    require(errors, env.get("divergence", {}).get("max_divergence") == 0.0, "engine divergence must be zero")
    gates = env.get("build_gates", {})
    for key, value in gates.items():
        require(errors, value is True, f"build gate {key} must be true")
    payload_gates = env.get("payload_build_gates", {})
    for key, value in payload_gates.items():
        require(errors, value is True, f"payload gate {key} must be true")
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
