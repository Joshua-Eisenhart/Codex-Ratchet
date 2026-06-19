#!/usr/bin/env python3
"""Packet-local validator for gcm_entropy_family_sweep_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import gcm_entropy_family_sweep_v0 as sim


ROOT = sim.ROOT
SIM_DIR = sim.SIM_DIR
RESULT = sim.RESULT_PATH
ENVELOPE = sim.ENVELOPE_PATH
VALIDATOR_RESULT = sim.VALIDATOR_RESULT_PATH

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


REQUIRED_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    f"{sim.SIM_ID}.py",
    f"validate_{sim.SIM_ID}.py",
    f"tests/test_{sim.SIM_ID}.py",
    f"results/{sim.SIM_ID}_results.json",
    f"results/{sim.SIM_ID}_envelope_results.json",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_required_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required file: {rel_path}")
    card = SIM_DIR / "build_card.md"
    text = card.read_text(encoding="utf-8") if card.exists() else ""
    for required in (
        sim.SIM_ID,
        "layers 3-12",
        "integrated-onto-the-carve",
        "1Q",
        sim.EXPECTED_OBJECT_ID,
        sim.EXPECTED_REGISTRY_BODY_SHA256,
        "lineage-free negative",
        "G.2a",
        "scratch_diagnostic",
        "carrier-and-pins-relative",
        "NO git add/commit",
    ):
        require(errors, required in text, f"build_card.md missing {required}")


def validate_payload(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema_version") == "gcm_entropy_family_sweep_v0_result_v1", "schema mismatch")
    require(errors, payload.get("sim_id") == sim.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("classification") == sim.CLASSIFICATION, "classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("carrier_and_pins_relative") is True, "carrier_and_pins_relative missing")
    require(errors, payload.get("not_THE_manifold") is True, "not_THE_manifold missing")
    require(errors, payload.get("three_coordinates", {}).get("layers") == "3-12 (entropy dimension)", "layers coordinate mismatch")
    require(
        errors,
        payload.get("three_coordinates", {}).get("nesting") == "integrated-onto-the-carve",
        "nesting coordinate mismatch",
    )
    require(errors, payload.get("three_coordinates", {}).get("qubit_depth") == "1Q", "qubit coordinate mismatch")
    require(errors, payload.get("counts", {}).get("survivor_count") == sim.EXPECTED_SURVIVOR_COUNT, "survivor count mismatch")
    require(
        errors,
        payload.get("counts", {}).get("quotient_class_count") == sim.EXPECTED_QUOTIENT_CLASS_COUNT,
        "quotient class count mismatch",
    )
    require(
        errors,
        payload.get("counts", {}).get("occupied_shell_count") == sim.EXPECTED_OCCUPIED_SHELL_COUNT,
        "occupied shell count mismatch",
    )
    require(errors, payload.get("TOOL_MANIFEST") == sim.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == sim.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, bool(payload.get("divergence_log")), "divergence_log must be non-empty")

    substrate = gcm_substrate_check(payload, sim.FREEZE_REGISTRY)
    negative = gcm_substrate_check(sim.lineage_free_variant(payload), sim.FREEZE_REGISTRY)
    require(errors, substrate.get("ok") is True, f"fresh gcm_substrate_check failed: {substrate.get('errors')}")
    require(errors, negative.get("ok") is False, "fresh lineage-free negative did not fail")

    rows = payload.get("entropy_tables", {}).get("survivor_entropy_rows", [])
    require(errors, len(rows) == sim.EXPECTED_SURVIVOR_COUNT, "survivor entropy row count mismatch")
    for row in rows:
        families = row.get("computed_families", {})
        require(errors, families.get("von_neumann_nats") == 0.0, f"vN entropy nonzero for {row.get('survivor_id')}")
        require(errors, set(families.get("renyi_nats_by_alpha", {})) == set(sim.RENyi_ALPHAS), "Renyi alpha set mismatch")
        require(errors, set(families.get("tsallis_by_q", {})) == set(sim.TSALLIS_QS), "Tsallis q set mismatch")

    class_rows = payload.get("entropy_tables", {}).get("class_mixed_state_entropy_rows", [])
    require(errors, len(class_rows) == sim.EXPECTED_QUOTIENT_CLASS_COUNT, "class mixed row count mismatch")
    require(
        errors,
        all(row.get("mixed_von_neumann_nats") == 0.0 for row in class_rows),
        "class-level mixed entropies must remain zero on this object",
    )

    nesting = {row.get("family"): row for row in payload.get("nesting_constraint_rows", [])}
    for family in ("conditional_entropy", "mutual_information", "coherent_information", "entanglement_negativity"):
        require(errors, nesting.get(family, {}).get("status") == "requires_more_structure", f"{family} availability mismatch")
    for family in ("von_neumann_1q", "renyi_ladder_1q", "tsallis_ladder_1q"):
        require(errors, nesting.get(family, {}).get("status") == "admissible_at_this_layer", f"{family} must be admissible")

    survival = {row.get("family"): row for row in payload.get("survival_rows", [])}
    require(errors, survival.get("von_neumann_1q", {}).get("separates_8_classes") is False, "vN must not separate classes")
    require(
        errors,
        survival.get("shell_log_surprisal", {}).get("shell_separation_count") == 2,
        "shell surprisal should separate exactly two occupancy bins",
    )

    controls = payload.get("controls", {})
    require(errors, controls.get("substrate_positive", {}).get("ok") is True, "recorded substrate positive failed")
    require(errors, controls.get("lineage_free_negative", {}).get("ok") is False, "recorded lineage negative failed")
    require(
        errors,
        controls.get("phase_quotient_invariance", {}).get("all_entropy_families_invariant") is True,
        "phase quotient invariance failed",
    )
    require(errors, payload.get("all_pass") is True, "payload all_pass false")


def validate_envelope(errors: list[str], envelope: dict[str, Any], payload: dict[str, Any]) -> None:
    require(errors, envelope.get("schema_version") == "single_packet_sim_envelope_v1", "envelope schema mismatch")
    require(errors, envelope.get("schema") == f"{sim.SIM_ID}_envelope_v1", "envelope packet schema mismatch")
    require(errors, envelope.get("sim_id") == sim.SIM_ID, "envelope sim_id mismatch")
    require(errors, envelope.get("classification") == sim.CLASSIFICATION, "envelope classification mismatch")
    require(errors, envelope.get("promotion_allowed") is False, "envelope promotion_allowed must be false")
    require(errors, envelope.get("formal_admission_allowed") is False, "envelope formal_admission_allowed must be false")
    require(errors, envelope.get("all_pass") is True, "envelope all_pass false")
    require(errors, envelope.get("result_sha256") == sim.stable_sha256(payload), "envelope result hash drift")
    require(errors, envelope.get("TOOL_MANIFEST") == sim.TOOL_MANIFEST, "envelope TOOL_MANIFEST mismatch")
    require(errors, envelope.get("TOOL_INTEGRATION_DEPTH") == sim.TOOL_INTEGRATION_DEPTH, "envelope TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, envelope.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict false")
    require(
        errors,
        envelope.get("builder_gates", {}).get("G_2a_idempotency_from_birth") is True,
        "G.2a builder gate false",
    )
    errors.extend(f"builder boundary: {err}" for err in builder_audit_boundary_errors(envelope, SIM_DIR / "audit_verdict.md"))


def validate() -> dict[str, Any]:
    errors: list[str] = []
    validate_required_files(errors)
    payload = load(RESULT) if RESULT.is_file() else {}
    envelope = load(ENVELOPE) if ENVELOPE.is_file() else {}
    if payload:
        validate_payload(errors, payload)
    else:
        errors.append("result JSON missing")
    if envelope and payload:
        validate_envelope(errors, envelope, payload)
    else:
        errors.append("envelope JSON missing")
    return {"ok": not errors, "errors": errors, "result_json": sim.rel(ENVELOPE)}


def main() -> int:
    report = validate()
    sim.write_json(VALIDATOR_RESULT, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
