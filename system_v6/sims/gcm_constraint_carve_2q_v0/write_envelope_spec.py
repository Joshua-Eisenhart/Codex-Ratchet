#!/usr/bin/env python3
"""Write the three-engine envelope spec and result for gcm_constraint_carve_2q_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import gcm_constraint_carve_2q_v0_common as common


SPEC_PATH = common.SIM_DIR / f"{common.SIM_ID}_envelope_spec.json"
ENGINE_RESULT_PATHS = {
    "julia": common.RESULT_DIR / f"{common.SIM_ID}_julia_results.json",
    "jax": common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json",
    "pytorch": common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json",
}

sys.path.insert(0, str(common.ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def lane_spec(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_path": result["source_path"],
        "result_path": result["result_path"],
        "packages_used": result["packages_used"],
        "aligned_packages_load_bearing": result["aligned_packages_load_bearing"],
        "package_observables": result["package_observables"],
        "result_all_pass": result["all_pass"],
        "survivor_count": result["survivor_count"],
        "quotient_class_count": result["quotient_class_count"],
        "component_count": result.get("component_count") or result.get("component_receipt", {}).get("component_count"),
        "entangled_survivor_count": result.get("entangled_survivor_count"),
        "embedded_1q_count": result.get("embedded_1q_count"),
    }


def engine_consensus(engine_results: dict[str, dict[str, Any]], packet: dict[str, Any]) -> dict[str, Any]:
    survivor_counts = {name: result["survivor_count"] for name, result in engine_results.items()}
    quotient_counts = {name: result["quotient_class_count"] for name, result in engine_results.items()}
    component_counts = {
        name: result.get("component_count") or result.get("component_receipt", {}).get("component_count")
        for name, result in engine_results.items()
    }
    entangled_counts = {name: result.get("entangled_survivor_count") for name, result in engine_results.items()}
    embedded_counts = {name: result.get("embedded_1q_count") for name, result in engine_results.items()}
    return {
        "all_engine_lanes_pass": all(result["all_pass"] is True for result in engine_results.values()),
        "survivor_count_agreement": set(survivor_counts.values()) == {packet["survivor_count"]},
        "quotient_class_count_agreement": set(quotient_counts.values()) == {packet["quotient"]["class_count"]},
        "component_count_agreement": set(component_counts.values()) == {len(packet["adjacency_connectivity"]["survivor_components"])},
        "entangled_survivor_count_agreement": set(entangled_counts.values()) == {packet["entangled_survivor_count"]},
        "embedded_1q_count_agreement": set(embedded_counts.values()) == {packet["cross_rung_lineage_row"]["product_control_embedding_count"]},
        "survivor_counts": survivor_counts,
        "quotient_class_counts": quotient_counts,
        "component_counts": component_counts,
        "entangled_survivor_counts": entangled_counts,
        "embedded_1q_counts": embedded_counts,
    }


def build_spec() -> dict[str, Any]:
    packet = load(common.RESULT_PATH)
    engine_results = {name: load(path) for name, path in ENGINE_RESULT_PATHS.items()}
    consensus = engine_consensus(engine_results, packet)
    all_pass = bool(packet["all_pass"] and consensus["all_engine_lanes_pass"])
    extra_fields = {
        "schema": "gcm_constraint_carve_2q_v0_envelope_v1",
        "result_path": common.rel(common.ENVELOPE_PATH),
        "source_path": common.rel(Path(__file__).resolve()),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": common.CLAIM_CEILING,
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "coordinates": packet["coordinates"],
        "claim": packet["claim"],
        "candidate_space": packet["candidate_space"],
        "constraint_family_C": packet["constraint_family_C"],
        "terrain_blindness_guard": packet["terrain_blindness_guard"],
        "probe_family_M": packet["probe_family_M"],
        "survivor_count": packet["survivor_count"],
        "survivor_family_counts": packet["survivor_family_counts"],
        "entangled_survivor_count": packet["entangled_survivor_count"],
        "survivors": packet["survivors"],
        "kill_ledger": packet["kill_ledger"],
        "kill_counts_by_constraint": packet["kill_counts_by_constraint"],
        "kill_ledger_diff_vs_1q": packet["kill_ledger_diff_vs_1q"],
        "quotient": packet["quotient"],
        "stability_certificate": packet["stability_certificate"],
        "adjacency_connectivity": packet["adjacency_connectivity"],
        "existence_tests": packet["existence_tests"],
        "identity_leak_detected": packet["identity_leak_detected"],
        "identity_leak_excluded_best_accuracy": packet["identity_leak_excluded_best_accuracy"],
        "identity_leak_exclusion_rule": packet["identity_leak_exclusion_rule"],
        "post_carve_structure_readout": packet["post_carve_structure_readout"],
        "boundary_phenomena_2q_only": packet["boundary_phenomena_2q_only"],
        "cross_rung_lineage_row": packet["cross_rung_lineage_row"],
        "controls": packet["controls"],
        "M_C_t_hook": packet["M_C_t_hook"],
        "seven_audit_questions": packet["seven_audit_questions"],
        "engine_lanes": sorted(engine_results),
        "engine_consensus": consensus,
        "TOOL_MANIFEST": common.TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": common.TOOL_INTEGRATION_DEPTH,
        "tool_intent": common.TOOL_INTENT,
        "source_locks": packet["source_locks"],
        "builder_gates": packet["builder_gates"],
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "all_pass": all_pass,
        "disallowed_claims": packet["disallowed_claims"],
    }
    return {
        "sim_id": common.SIM_ID,
        "lanes": {name: lane_spec(result) for name, result in engine_results.items()},
        "mode": common.ENGINE_MODE,
        "claim_path_tools": sorted(common.TOOL_MANIFEST),
        "crossover_proofs": packet["crossover_proofs"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": float(engine_results["julia"]["survivor_count"]),
                "jax": float(engine_results["jax"]["survivor_count"]),
                "pytorch": float(engine_results["pytorch"]["survivor_count"]),
            },
            "max_divergence": 0.0,
        },
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "parent_lineage": {
            "one_q_carve_result_sha256": packet["cross_rung_lineage_row"]["one_q_authority_hashes"]["one_q_result_sha256"],
            "one_q_carve_envelope_sha256": packet["cross_rung_lineage_row"]["one_q_authority_hashes"]["one_q_envelope_sha256"],
            "one_q_common_sha256": packet["cross_rung_lineage_row"]["one_q_authority_hashes"]["one_q_common_sha256"],
            "one_q_freeze_registry_sha256": packet["cross_rung_lineage_row"]["one_q_authority_hashes"]["one_q_freeze_registry_sha256"],
        },
        "expected_lanes": ["julia", "jax", "pytorch"],
        "stability_pairs": [
            {"subtree": common.rel(common.RESULT_PATH), "hash": common.sha256_file(common.RESULT_PATH)},
            {
                "subtree": "M_C_2Q_survivor_quotient_cross_rung_payload",
                "hash": common.stable_sha256(
                    {
                        "survivors": packet["survivors"],
                        "quotient": packet["quotient"],
                        "constraints": packet["constraint_family_C"],
                        "cross_rung": packet["cross_rung_lineage_row"],
                    }
                ),
            },
        ],
        "extra_fields": extra_fields,
    }


def main() -> int:
    spec = build_spec()
    common.write_json(SPEC_PATH, spec)
    envelope = build_envelope(**spec)
    common.write_json(common.ENVELOPE_PATH, envelope)
    print(
        json.dumps(
            {"ok": True, "spec": common.rel(SPEC_PATH), "envelope": common.rel(common.ENVELOPE_PATH)},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
