#!/usr/bin/env python3
"""Packet-local validator for gcm_g2_licensing_attach_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import gcm_g2_licensing_attach_v0 as sim


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
        "layer 22",
        "integrated",
        "3Q",
        "W_A",
        "e123+e145+e167+e246-e257-e347-e356",
        "scrambled-phi",
        "random 7-subspace",
        "quotient-erasure",
        "G.2a",
        "scratch_diagnostic",
        "carrier-and-pins-relative",
        "NO git add/commit",
    ):
        require(errors, required in text, f"build_card.md missing {required}")


def validate_payload(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema_version") == f"{sim.SIM_ID}_result_v1", "schema mismatch")
    require(errors, payload.get("sim_id") == sim.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("classification") == sim.CLASSIFICATION, "classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("carrier_and_pins_relative") is True, "carrier_and_pins_relative missing")
    require(errors, payload.get("not_THE_manifold") is True, "not_THE_manifold missing")
    require(errors, payload.get("layer_declaration") == sim.THREE_COORDINATES, "three coordinates mismatch")
    require(errors, payload.get("W_A", {}).get("dimension") == 7, "W_A dimension mismatch")
    require(errors, payload.get("W_A", {}).get("basis_labels") == sim.PINNED_W_A_LABELS, "W_A labels mismatch")
    require(errors, payload.get("W_A", {}).get("source_status", "").startswith("not natural"), "W_A naturality boundary missing")
    require(errors, payload.get("licensing", {}).get("natural_W_A_from_owner_sources") is False, "natural W_A overclaimed")
    require(errors, payload.get("licensing", {}).get("pinned_convention_flagged") is True, "pinning flag missing")
    require(
        errors,
        payload.get("parent_3q_facts", {}).get("survivor_count") == sim.EXPECTED_THREE_Q_SURVIVOR_COUNT,
        "3Q survivor count mismatch",
    )
    require(
        errors,
        payload.get("parent_3q_facts", {}).get("quotient_class_count") == sim.EXPECTED_THREE_Q_QUOTIENT_CLASS_COUNT,
        "3Q quotient class count mismatch",
    )
    require(
        errors,
        payload.get("parent_3q_facts", {}).get("pauli_string_count_3q_traceless")
        == sim.EXPECTED_TRACeless_PAULI_COUNT_3Q,
        "3Q traceless Pauli count mismatch",
    )
    require(errors, payload.get("TOOL_MANIFEST") == sim.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == sim.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, bool(payload.get("divergence_log")), "divergence_log missing")

    tests = payload.get("tests", {})
    preservation = tests.get("phi_preservation", {})
    require(errors, preservation.get("scrambled_phi_control", {}).get("red") is True, "scrambled phi did not fail")
    require(errors, preservation.get("preserving_map_count", 0) >= 2, "missing preserving maps")
    require(errors, preservation.get("failing_map_count", 0) >= 2, "missing failing map controls")
    require(
        errors,
        tests.get("cross_product_closure", {}).get("all_basis_pairs_closed_in_W_A") is True,
        "cross-product closure failed",
    )
    associator = tests.get("associator_rows", {})
    require(errors, associator.get("count_matches_feedstock") is True, "associator count mismatch")
    require(
        errors,
        associator.get("visibility_on_states", {}).get("visible_nonzero_rows", 0) > 0,
        "associator visibility absent",
    )
    require(
        errors,
        associator.get("density_quotient_erasure", {}).get("all_classes_erase_associator_labels") is True,
        "density quotient erasure failed",
    )
    branch = tests.get("compact_vs_split_branch", {})
    require(errors, branch.get("compact_der_dim") == sim.EXPECTED_OCTONION_DER_DIM, "compact Der(O) feedstock mismatch")
    require(errors, branch.get("split_der_dim") == sim.EXPECTED_OCTONION_DER_DIM, "split Der(O) feedstock mismatch")
    require(errors, branch.get("corrupt_der_dim") == 3, "corrupt control feedstock mismatch")

    controls = payload.get("controls", {})
    require(errors, controls.get("scrambled_phi", {}).get("red") is True, "recorded scrambled control not red")
    require(
        errors,
        controls.get("random_7_subspace", {}).get("pinned_outperforms_random") is True,
        "random 7-subspace control did not underperform",
    )
    require(errors, controls.get("substrate_positive", {}).get("ok") is True, "recorded substrate positive failed")
    require(errors, controls.get("lineage_free_negative", {}).get("ok") is False, "recorded lineage negative not red")

    fresh_positive = gcm_substrate_check(payload, sim.TWO_Q_REGISTRY)
    fresh_negative = gcm_substrate_check(sim.lineage_free_variant(payload), sim.TWO_Q_REGISTRY)
    require(errors, fresh_positive.get("ok") is True, f"fresh substrate check failed: {fresh_positive.get('errors')}")
    require(errors, fresh_negative.get("ok") is False, "fresh lineage-free negative did not fail")
    errors.extend(f"builder boundary: {err}" for err in builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
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
