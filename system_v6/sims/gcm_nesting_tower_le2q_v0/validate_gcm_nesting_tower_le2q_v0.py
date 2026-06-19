#!/usr/bin/env python3
"""Packet-local validator for gcm_nesting_tower_le2q_v0."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import gcm_nesting_tower_le2q_v0_boundary as boundary
import gcm_nesting_tower_le2q_v0_common as common


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
    f"results/{common.SIM_ID}_results.json",
    f"results/{common.SIM_ID}_lineage_free_negative.json",
    f"results/{common.SIM_ID}_julia_results.json",
    f"results/{common.SIM_ID}_jax_results.json",
    f"results/{common.SIM_ID}_pytorch_results.json",
    f"results/{common.SIM_ID}_envelope_results.json",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def without_runtime_fields(payload: dict[str, Any]) -> dict[str, Any]:
    clone = copy.deepcopy(payload)
    clone.pop("generated_at", None)
    clone.pop("result_sha256", None)
    controls = clone.get("controls")
    if isinstance(controls, dict):
        for key in (
            "substrate_positive_1q",
            "substrate_positive_2q",
            "substrate_lineage_free_negative_1q",
            "substrate_lineage_free_negative_2q",
        ):
            controls.pop(key, None)
    source_locks = clone.get("source_locks")
    if isinstance(source_locks, dict):
        for row in source_locks.values():
            if isinstance(row, dict):
                row.pop("git_last_commit", None)
        source_locks.pop("gcm_substrate_check", None)
    return clone


def validate_packet_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    card = SIM_DIR / "build_card.md"
    text = card.read_text(encoding="utf-8") if card.exists() else ""
    for phrase in (
        common.SIM_ID,
        "THE NESTING LAW",
        "X_{<=2}^max",
        "exact-vs-probe",
        "extension fibers",
        "tower-orphans",
        "product-only sub-tower",
        "lineage-free negative",
        common.EXPECTED_1Q_OBJECT_ID,
        common.EXPECTED_2Q_OBJECT_ID,
        "G.2a",
        "scratch_diagnostic",
        "carrier-and-pins-relative",
        "NO git add/commit",
    ):
        require(errors, phrase in text, f"build_card.md missing {phrase}")


def validate_packet(errors: list[str], packet: dict[str, Any]) -> None:
    rebuilt = common.build_packet(write=False)
    require(errors, without_runtime_fields(packet) == without_runtime_fields(rebuilt), "packet drift against source rebuild")
    require(errors, packet.get("schema_version") == common.SCHEMA, "packet schema mismatch")
    require(errors, packet.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, packet.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, packet.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, packet.get("axis_declaration") == {"axis": "nesting/tower", "object": "inverse-limit", "rung": "<=2Q"}, "axis declaration mismatch")
    counts = packet.get("counts", {})
    expected_counts = {
        "one_q_survivor_count": 16,
        "two_q_survivor_count": 544,
        "exact_compatible_2q_count": 256,
        "exact_compatible_family_triple_count": 256,
        "exact_orphan_2q_count": 288,
        "probe_compatible_2q_count": 464,
        "probe_compatible_family_triple_count": 1856,
        "probe_orphan_2q_count": 80,
        "probe_rescued_exact_orphan_2q_count": 208,
        "quotient_multiplicity_added_family_triples": 1600,
        "product_exact_subtower_count": 256,
        "product_probe_compatible_2q_count": 448,
        "product_probe_family_triple_count": 1792,
        "entangled_probe_compatible_2q_count": 16,
        "entangled_probe_family_triple_count": 64,
    }
    for key, value in expected_counts.items():
        require(errors, counts.get(key) == value, f"count mismatch {key}: {counts.get(key)} != {value}")
    require(errors, len(packet.get("compatible_families", {}).get("exact_relation", [])) == 256, "exact triple enumeration count mismatch")
    require(errors, len(packet.get("compatible_families", {}).get("probe_equivalence_relation", [])) == 1856, "probe triple enumeration count mismatch")
    fibers = packet.get("fiber_summary", {})
    require(errors, fibers.get("fiber_size_distribution", {}).get("exact_A") == {"34": 16}, "exact A fiber distribution mismatch")
    require(errors, fibers.get("fiber_size_distribution", {}).get("exact_B") == {"16": 16}, "exact B fiber distribution mismatch")
    require(errors, fibers.get("fiber_size_distribution", {}).get("probe_A") == {"68": 16}, "probe A fiber distribution mismatch")
    require(errors, fibers.get("fiber_size_distribution", {}).get("probe_B") == {"48": 8, "64": 6, "80": 2}, "probe B fiber distribution mismatch")
    cover = fibers.get("cover_partition_checks", {})
    require(errors, cover.get("exact_A_partitions_all_2q_survivors") is True, "exact A fiber partition failed")
    require(errors, cover.get("exact_B_partitions_exact_compatible_2q_survivors") is True, "exact B fiber partition failed")
    ent = packet.get("entangled_16_fiber_membership", {})
    require(errors, ent.get("exact_compatible_count") == 0, "entangled exact compatibility mismatch")
    require(errors, ent.get("probe_compatible_count") == 16, "entangled probe compatibility mismatch")
    require(errors, ent.get("verdict") == "entangled_16_are_exact_B_orphans_but_probe_compatible_fiber_members", "entangled verdict mismatch")
    products = packet.get("controls", {}).get("product_only_subtower", {})
    require(errors, products.get("exact_product_subtower_count") == 256, "product exact subtower mismatch")
    require(errors, products.get("pinned_product_embedding_row_count") == 16, "pinned product embedding mismatch")
    require(errors, products.get("pinned_product_embedding_all_survive") is True, "pinned product embedding failed")
    scrambled = packet.get("controls", {}).get("scrambled_pairing_tower", {})
    require(errors, scrambled.get("all_probe_compatibility_destroyed") is True, "scrambled pairing did not break probe compatibility")
    require(errors, packet.get("bidirectional_check", {}).get("all_round_trips_pass") is True, "bidirectional round trip failed")
    require(errors, packet.get("controls", {}).get("substrate_positive_1q", {}).get("ok") is True, "1Q substrate positive failed")
    require(errors, packet.get("controls", {}).get("substrate_positive_2q", {}).get("ok") is True, "2Q substrate positive failed")
    require(errors, packet.get("controls", {}).get("substrate_lineage_free_negative_1q", {}).get("ok") is False, "1Q lineage-free negative did not fail")
    require(errors, packet.get("controls", {}).get("substrate_lineage_free_negative_2q", {}).get("ok") is False, "2Q lineage-free negative did not fail")
    require(errors, gcm_substrate_check(packet, common.ONE_Q_REGISTRY_PATH).get("ok") is True, "helper 1Q substrate check failed")
    require(errors, gcm_substrate_check(packet, common.TWO_Q_REGISTRY_PATH).get("ok") is True, "helper 2Q substrate check failed")
    require(errors, packet.get("crossover_proofs", {}).get("z3", {}).get("verdict") == "sat", "z3 proof did not pass")
    require(errors, packet.get("crossover_proofs", {}).get("cvc5", {}).get("verdict") == "sat", "cvc5 proof did not pass")
    require(errors, packet.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, packet.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    errors.extend(f"boundary: {err}" for err in boundary.boundary_errors(packet, SIM_DIR))
    require(errors, packet.get("all_pass") is True, "packet all_pass false")


def validate_engine_results(errors: list[str]) -> None:
    for engine in ("julia", "jax", "pytorch"):
        result = load(common.RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")
        require(errors, result.get("all_pass") is True, f"{engine} all_pass false")
        require(errors, result.get("reads_peer_result") is False, f"{engine} reads_peer_result must be false")
        require(errors, result.get("exact_tower_cardinality") == 256, f"{engine} exact cardinality mismatch")
        require(errors, result.get("probe_tower_cardinality") == 1856, f"{engine} probe cardinality mismatch")
        require(errors, result.get("probe_orphan_2q_count") == 80, f"{engine} probe orphan mismatch")


def validate_envelope(errors: list[str], envelope: dict[str, Any]) -> None:
    rebuilt = common.build_envelope(write=False)
    require(errors, without_runtime_fields(envelope) == without_runtime_fields(rebuilt), "envelope drift against source rebuild")
    require(errors, envelope.get("schema_version") == "three_engine_sim_result_v1", "envelope schema mismatch")
    require(errors, envelope.get("schema") == common.ENVELOPE_SCHEMA, "packet envelope schema mismatch")
    require(errors, envelope.get("mode") == common.ENGINE_MODE, "engine mode mismatch")
    require(errors, envelope.get("classification") == common.CLASSIFICATION, "envelope classification mismatch")
    require(errors, envelope.get("promotion_allowed") is False, "envelope promotion_allowed must be false")
    require(errors, set(envelope.get("engine_lanes", [])) == {"julia", "jax", "pytorch"}, "engine lanes mismatch")
    require(errors, envelope.get("engine_consensus", {}).get("all_engine_lanes_pass") is True, "engine consensus false")
    require(errors, all(envelope.get("engine_consensus", {}).get("count_agreement", {}).values()), "engine count agreement failed")
    require(errors, envelope.get("divergence", {}).get("max_divergence") == 0, "nonzero engine divergence")
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
    validate_packet(errors, load(common.RESULT_PATH))
    validate_engine_results(errors)
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
