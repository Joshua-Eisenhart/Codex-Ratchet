#!/usr/bin/env python3
"""Packet-local validator for basin_two_engine_joint_v4_within_sector_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from basin_two_engine_joint_v4_within_sector_v0_common import (
    FLUX_UPDATE_FAMILY,
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
    require(errors, "WITHIN-SECTOR" in text and "IN-CLASS FLUX FLIPPING" in text, "corrected target missing")
    require(errors, "conserved_flux_control" in text, "registered flux family missing from card")


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
    counts = payload.get("primary_terminal_counts")
    require(errors, isinstance(counts, dict) and counts, f"{name} primary terminal counts missing")
    require(errors, isinstance(payload.get("genuine_hit_count"), int), f"{name} genuine_hit_count missing")


def validate_realization_family(errors: list[str], env: dict[str, Any]) -> None:
    family = env.get("realization_family", {})
    rows = family.get("rows", {})
    require(errors, set(rows) == set(FLUX_UPDATE_FAMILY), "registered family mismatch")
    controls = env.get("controls", {})
    require(errors, controls.get("flux_erased_continuity", {}).get("all_pass") is True, "flux-erased continuity failed")
    require(errors, controls.get("conserved_flux", {}).get("all_pass") is True, "conserved-flux sector control failed")
    require(errors, controls.get("order_shuffle", {}).get("all_pass") is True, "order-shuffle controls did not all run")
    for row in controls.get("conserved_flux", {}).get("rows", []):
        require(errors, row.get("reproduces_v4_sector_decomposition") is True, "conserved row failed v4 sector decomposition")
        require(errors, row.get("terminal_class_count") == 2, "conserved row should expose exactly two Z/2 sector terminal classes")
    candidate_seen = False
    for law_id, law_rows in rows.items():
        for variant_id, engines in law_rows.get("variants", {}).items():
            for engine, row in engines.items():
                checks = row.get("projection_and_symmetry_checks", {})
                require(errors, checks.get("terminal_checks"), f"{law_id}/{variant_id}/{engine} terminal checks missing")
                require(errors, checks.get("all_terminals_absent_exit") is True, f"{law_id}/{variant_id}/{engine} absent-exit failed")
                require(errors, row.get("label_permutation_control", {}).get("all_pass") is True, f"{law_id}/{variant_id}/{engine} label control failed")
                require(errors, row.get("order_shuffle_control", {}).get("ran") is True, f"{law_id}/{variant_id}/{engine} order shuffle not run")
                if law_id != "conserved_flux_control":
                    candidate_seen = True
                for terminal in checks.get("terminal_checks", []):
                    require(errors, "projection_test_pass" in terminal, f"{law_id}/{variant_id}/{engine} projection field missing")
                    require(errors, "symmetry_orbit_test_pass" in terminal, f"{law_id}/{variant_id}/{engine} symmetry field missing")
                    if terminal.get("sector_duplicate_under_flux_involution") is True:
                        require(
                            errors,
                            terminal.get("genuine_candidate_under_panel6_q3") is False,
                            f"{law_id}/{variant_id}/{engine} sector duplicate accepted as genuine",
                        )
                    if terminal.get("full_projection_echo") is True and terminal.get("in_class_flux_flipping") is not True:
                        require(
                            errors,
                            terminal.get("genuine_candidate_under_panel6_q3") is False,
                            f"{law_id}/{variant_id}/{engine} projection echo accepted as genuine",
                        )
    require(errors, candidate_seen, "no candidate flux update law rows found")


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
    require(errors, bool(env.get("TOOL_MANIFEST")), "TOOL_MANIFEST missing")
    require(errors, bool(env.get("TOOL_INTEGRATION_DEPTH")), "TOOL_INTEGRATION_DEPTH missing")
    validate_realization_family(errors, env)
    adjudication = env.get("prediction_adjudication", {})
    require(errors, adjudication.get("pre_registered_owner_count") == 64, "owner count mismatch")
    require(errors, "within-sector" in adjudication.get("corrected_target", ""), "corrected target missing")
    require(errors, adjudication.get("realization_relative_only") is True, "realization-relative fence missing")
    require(errors, adjudication.get("no_canonical_confirmation_or_disproof") is True, "canonical fence missing")
    proofs = env.get("crossover_proofs", {})
    for key in ("z3", "cvc5", "julia_z3", "pytorch_z3", "pytorch_cvc5"):
        require(errors, proofs.get(key, {}).get("verdict") == "unsat", f"{key} count identity must be unsat")
        require(errors, proofs.get(key, {}).get("flipped_control_verdict") == "sat", f"{key} flipped control must be sat")
    comparison = env.get("engine_comparison", {})
    require(errors, comparison.get("primary_terminal_count_agreement") is True, "engine primary counts disagree")
    require(errors, comparison.get("genuine_hit_count_agreement") is True, "engine genuine hit counts disagree")
    require(errors, env.get("divergence", {}).get("max_divergence") == 0.0, "engine divergence must be zero")
    require(errors, bool(env.get("divergence_log")), "divergence_log missing")
    for key, value in env.get("build_gates", {}).items():
        require(errors, value is True, f"build gate {key} must be true")
    for key, value in env.get("payload_build_gates", {}).items():
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
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }
    write_json(VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
