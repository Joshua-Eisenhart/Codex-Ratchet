#!/usr/bin/env python3
"""Packet-local validator for gcm_2q_freeze_and_cut_v0."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import gcm_2q_freeze_and_cut_v0_boundary as boundary
import gcm_2q_freeze_and_cut_v0_common as common


ROOT = common.ROOT
SIM_DIR = common.SIM_DIR
ENVELOPE = common.ENVELOPE_PATH
VALIDATOR_RESULT = common.VALIDATOR_RESULT_PATH

sys.path.insert(0, str(ROOT / "scripts"))
from gcm_substrate_check import gcm_substrate_check  # noqa: E402
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


REQUIRED_PACKET_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    f"{common.SIM_ID}_common.py",
    f"{common.SIM_ID}_boundary.py",
    f"{common.SIM_ID}_julia.jl",
    f"{common.SIM_ID}_jax.py",
    f"{common.SIM_ID}_pytorch.py",
    "write_envelope_spec.py",
    f"validate_{common.SIM_ID}.py",
    f"tests/test_{common.SIM_ID}.py",
    f"results/{common.SIM_ID}_registry.json",
    f"results/{common.SIM_ID}_results.json",
    f"results/{common.SIM_ID}_lineage_free_negative.json",
    f"results/{common.SIM_ID}_envelope_results.json",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# These control subtrees echo gcm_substrate_check's raw output, whose diagnostic schema
# grows as later rungs add error codes / object-id fields. They are helper-version-dependent
# demonstrations, NOT part of this rung's reproducible math identity, so the byte-reproduce
# check excludes them. Their verdicts are asserted independently below (substrate_positive
# ok is True / substrate_lineage_free_negative ok is False) and re-run live against the
# helper, so excluding them from the reproduce-compare loses no coverage.
HELPER_OUTPUT_CONTROL_KEYS = (
    "substrate_positive_1q",
    "substrate_positive_2q",
    "substrate_lineage_free_negative_1q",
    "substrate_lineage_free_negative_2q",
)


def without_runtime_fields(payload: dict[str, Any]) -> dict[str, Any]:
    clone = copy.deepcopy(payload)
    clone.pop("generated_at", None)
    clone.pop("result_sha256", None)
    controls = clone.get("controls")
    if isinstance(controls, dict):
        for key in HELPER_OUTPUT_CONTROL_KEYS:
            controls.pop(key, None)
    return clone


def validate_packet_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    card = SIM_DIR / "build_card.md"
    text = card.read_text(encoding="utf-8") if card.exists() else ""
    for required in (
        common.SIM_ID,
        "2Q freeze",
        "qubit A | qubit B",
        "S(A|B)",
        "I(A:B)",
        "I_c(A>B)",
        "negativity",
        "monogamy",
        "lineage-free negative",
        common.EXPECTED_BASE_OBJECT_ID,
        common.EXPECTED_BASE_REGISTRY_BODY_SHA256,
        "G.2a",
        "scratch_diagnostic",
        "carrier-and-pins-relative",
        "NO git add/commit",
    ):
        require(errors, required in text, f"build_card.md missing {required}")


def validate_registry(errors: list[str], registry: dict[str, Any]) -> None:
    rebuilt = common.build_2q_registry(load(common.TWO_Q_CARVE_RESULT), load(common.ONE_Q_FREEZE_REGISTRY))
    require(errors, registry == rebuilt, "2Q registry drift against source rebuild")
    require(errors, registry.get("schema") == common.REGISTRY_SCHEMA, "registry schema mismatch")
    require(errors, registry.get("gcm_object_id") == common.EXPECTED_BASE_OBJECT_ID, "base gcm_object_id mismatch")
    require(errors, registry.get("base_registry_body_sha256") == common.EXPECTED_BASE_REGISTRY_BODY_SHA256, "base registry hash mismatch")
    require(errors, isinstance(registry.get("gcm_2q_object_id"), str) and registry["gcm_2q_object_id"].startswith("gcm2qobj_"), "bad gcm_2q_object_id")
    frozen = registry.get("frozen_2q_registry", {})
    survivors = frozen.get("survivors", [])
    qclasses = frozen.get("quotient_classes", [])
    regions = frozen.get("candidate_regions", [])
    require(errors, len(survivors) == common.EXPECTED_TWO_Q_SURVIVOR_COUNT, "2Q survivor registry count mismatch")
    require(errors, len(qclasses) == common.EXPECTED_TWO_Q_CLASS_COUNT, "2Q class registry count mismatch")
    require(errors, len(regions) == common.EXPECTED_TWO_Q_REGION_COUNT, "2Q region registry count mismatch")
    require(errors, len({row["gcm_2q_survivor_id"] for row in survivors}) == len(survivors), "2Q survivor ids not unique")
    require(errors, len({row["gcm_2q_quotient_class_id"] for row in qclasses}) == len(qclasses), "2Q class ids not unique")
    require(errors, len({row["gcm_2q_candidate_region_id"] for row in regions}) == len(regions), "2Q region ids not unique")
    require(errors, registry.get("counts", {}).get("product_survivor_count") == common.EXPECTED_PRODUCT_SURVIVOR_COUNT, "product registry count mismatch")
    require(errors, registry.get("counts", {}).get("entangled_survivor_count") == common.EXPECTED_ENTANGLED_SURVIVOR_COUNT, "entangled registry count mismatch")


def validate_packet(errors: list[str], packet: dict[str, Any], registry: dict[str, Any]) -> None:
    rebuilt = common.build_packet(write=False)
    require(errors, without_runtime_fields(packet) == without_runtime_fields(rebuilt), "packet drift against source rebuild")
    require(errors, packet.get("schema_version") == common.SCHEMA, "packet schema mismatch")
    require(errors, packet.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, packet.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, packet.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, packet.get("three_coordinates") == {
        "layers": "3-12 entropy availability rung",
        "nesting": "2Q freeze plus first bipartition cut",
        "qubit_depth": "2Q",
    }, "three_coordinates mismatch")
    require(errors, packet.get("cut", {}).get("bipartition") == "qubit A | qubit B", "cut bipartition mismatch")
    counts = packet.get("counts", {})
    require(errors, counts.get("two_q_survivor_count") == common.EXPECTED_TWO_Q_SURVIVOR_COUNT, "survivor count mismatch")
    require(errors, counts.get("two_q_class_count") == common.EXPECTED_TWO_Q_CLASS_COUNT, "class count mismatch")
    require(errors, counts.get("product_survivor_count") == common.EXPECTED_PRODUCT_SURVIVOR_COUNT, "product count mismatch")
    require(errors, counts.get("entangled_survivor_count") == common.EXPECTED_ENTANGLED_SURVIVOR_COUNT, "entangled count mismatch")
    require(errors, counts.get("one_q_product_embedding_count") == common.EXPECTED_ONE_Q_SURVIVOR_COUNT, "embedding count mismatch")
    rows = packet.get("entropy_tables", {}).get("survivor_cut_entropy_rows", [])
    require(errors, len(rows) == common.EXPECTED_TWO_Q_SURVIVOR_COUNT, "entropy row count mismatch")
    require(errors, len(packet.get("entropy_tables", {}).get("class_cut_entropy_rows", [])) == common.EXPECTED_TWO_Q_CLASS_COUNT, "class entropy row count mismatch")
    product = [row for row in rows if row.get("family") == "product_grid"]
    entangled = [row for row in rows if row.get("entangled") is True]
    require(errors, len(product) == common.EXPECTED_PRODUCT_SURVIVOR_COUNT, "product entropy row count mismatch")
    require(errors, len(entangled) == common.EXPECTED_ENTANGLED_SURVIVOR_COUNT, "entangled entropy row count mismatch")
    require(errors, all(row["entropy_values"]["negativity"] == 0.0 for row in product), "product negativity not exactly zero")
    require(errors, all(row["entropy_values"]["negativity"] > 0.0 for row in entangled), "entangled negativity did not separate")
    require(errors, all(row["entropy_values"]["conditional_S_A_given_B"] < 0.0 for row in entangled), "entangled conditional entropy not negative")
    sep = packet.get("entangled_vs_product_separation", {}).get("metrics", {})
    require(errors, sep.get("negativity", {}).get("separates") is True, "negativity separation failed")
    require(errors, sep.get("mutual_I_A_B", {}).get("separates") is True, "mutual information separation failed")
    require(errors, sep.get("coherent_I_c_A_to_B", {}).get("separates_by_sign") is True, "coherent information separation failed")
    require(errors, packet.get("monogamy_row", {}).get("status") == "OPEN_REQUIRES_3Q_FOR_CKW", "monogamy status overpromoted")
    controls = packet.get("controls", {})
    require(errors, controls.get("product_entanglement_zero", {}).get("all_product_negativity_zero") is True, "product zero control failed")
    require(errors, controls.get("scrambled_pairing", {}).get("negativity_after_scramble_all_zero") is True, "scrambled pairing control failed")
    require(errors, controls.get("one_q_regression", {}).get("all_A_fibers_have_expected_size") is True, "1Q fiber count regression failed")
    require(errors, controls.get("one_q_regression", {}).get("partial_trace_A_reproduces_1q_id_degeneracy") is True, "1Q degeneracy regression failed")
    require(errors, controls.get("substrate_positive_1q", {}).get("ok") is True, "1Q substrate positive failed")
    require(errors, controls.get("substrate_positive_2q", {}).get("ok") is True, "2Q substrate positive failed")
    require(errors, controls.get("substrate_lineage_free_negative_1q", {}).get("ok") is False, "1Q lineage-free negative did not fail")
    require(errors, controls.get("substrate_lineage_free_negative_2q", {}).get("ok") is False, "2Q lineage-free negative did not fail")
    require(errors, gcm_substrate_check(packet, common.ONE_Q_FREEZE_REGISTRY).get("ok") is True, "CLI helper default 1Q substrate failed")
    require(errors, gcm_substrate_check(packet, common.REGISTRY_PATH).get("ok") is True, "CLI helper 2Q substrate failed")
    # Live negative-rejection gate. The helper-output controls are excluded from the byte-reproduce
    # check (they are version-dependent diagnostics), so the negative-rejection property must be
    # asserted LIVE here, not only via the frozen committed control — otherwise a helper regression
    # that stops rejecting lineage-free payloads could survive green.
    require(errors, gcm_substrate_check(common.lineage_free_variant(packet), common.ONE_Q_FREEZE_REGISTRY).get("ok") is False, "live 1Q lineage-free negative did not fail")
    require(errors, gcm_substrate_check(common.lineage_free_variant(packet), common.REGISTRY_PATH).get("ok") is False, "live 2Q lineage-free negative did not fail")
    errors.extend(f"boundary: {err}" for err in boundary.boundary_errors(packet, SIM_DIR))
    require(errors, packet.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, packet.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, packet.get("all_pass") is True, "packet all_pass false")


def validate_envelope(errors: list[str], envelope: dict[str, Any]) -> None:
    require(errors, envelope.get("schema_version") == "three_engine_sim_result_v1", "envelope schema_version mismatch")
    require(errors, envelope.get("schema") == f"{common.SIM_ID}_envelope_v1", "packet envelope schema mismatch")
    require(errors, envelope.get("mode") == common.ENGINE_MODE, "engine mode mismatch")
    require(errors, envelope.get("classification") == common.CLASSIFICATION, "envelope classification mismatch")
    require(errors, envelope.get("promotion_allowed") is False, "envelope promotion_allowed must be false")
    require(errors, envelope.get("formal_admission_allowed") is False, "envelope formal_admission_allowed must be false")
    require(errors, set(envelope.get("engine_lanes", [])) == {"julia", "jax", "pytorch"}, "engine_lanes mismatch")
    consensus = envelope.get("engine_consensus", {})
    require(errors, consensus.get("all_engine_lanes_pass") is True, "engine consensus all pass false")
    require(errors, all(consensus.get("count_agreement", {}).values()), "engine count agreement failed")
    require(errors, all(consensus.get("metric_agreement_within_tolerance", {}).values()), "engine metric agreement failed")
    for engine in ("julia", "jax", "pytorch"):
        lane = load(common.RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")
        require(errors, lane.get("all_pass") is True, f"{engine} lane all_pass false")
        require(errors, envelope.get("engines", {}).get(engine, {}).get("result_all_pass") is True, f"{engine} envelope result_all_pass false")
        require(errors, envelope.get("engines", {}).get(engine, {}).get("reads_peer_result") is False, f"{engine} reads_peer_result must be false")
    generic_errors = validate_three_engine(
        envelope,
        require_pytorch=True,
        strict_source_backed=True,
        require_tool_intent=True,
    )
    errors.extend(f"generic three-engine validator: {err}" for err in generic_errors)
    errors.extend(f"boundary: {err}" for err in boundary.boundary_errors(envelope, SIM_DIR))
    require(errors, envelope.get("all_pass") is True, "envelope all_pass false")


def validate_payload(envelope: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    registry = load(common.REGISTRY_PATH)
    packet = load(common.RESULT_PATH)
    validate_registry(errors, registry)
    validate_packet(errors, packet, registry)
    validate_envelope(errors, envelope)
    return errors


def main() -> int:
    payload = load(ENVELOPE)
    errors = validate_payload(payload)
    result = {"ok": not errors, "result_json": common.rel(ENVELOPE), "errors": errors}
    common.write_json(VALIDATOR_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
