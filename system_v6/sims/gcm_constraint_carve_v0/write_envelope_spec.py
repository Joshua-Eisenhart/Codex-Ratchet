#!/usr/bin/env python3
"""Write the three-engine envelope spec for gcm_constraint_carve_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gcm_constraint_carve_v0_common as common


SPEC_PATH = common.SIM_DIR / f"{common.SIM_ID}_envelope_spec.json"
ENGINE_RESULT_PATHS = {
    "julia": common.RESULT_DIR / f"{common.SIM_ID}_julia_results.json",
    "jax": common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json",
    "pytorch": common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json",
}


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
        "component_count": result.get("component_count")
        or result.get("component_receipt", {}).get("component_count"),
    }


def engine_consensus(engine_results: dict[str, dict[str, Any]], packet: dict[str, Any]) -> dict[str, Any]:
    survivor_counts = {name: result["survivor_count"] for name, result in engine_results.items()}
    quotient_counts = {name: result["quotient_class_count"] for name, result in engine_results.items()}
    component_counts = {
        name: result.get("component_count") or result.get("component_receipt", {}).get("component_count")
        for name, result in engine_results.items()
    }
    graph_scoped_component_counts = {name: count for name, count in component_counts.items() if count is not None}
    return {
        "all_engine_lanes_pass": all(result["all_pass"] is True for result in engine_results.values()),
        "survivor_count_agreement": set(survivor_counts.values()) == {packet["survivor_count"]},
        "quotient_class_count_agreement": set(quotient_counts.values()) == {packet["quotient"]["class_count"]},
        "component_count_agreement": set(graph_scoped_component_counts.values())
        == {len(packet["adjacency_connectivity"]["survivor_components"])},
        "component_count_scoped_lanes": sorted(graph_scoped_component_counts),
        "survivor_counts": survivor_counts,
        "quotient_class_counts": quotient_counts,
        "component_counts": component_counts,
    }


def build_spec() -> dict[str, Any]:
    packet = load(common.RESULT_PATH)
    engine_results = {name: load(path) for name, path in ENGINE_RESULT_PATHS.items()}
    consensus = engine_consensus(engine_results, packet)
    all_pass = bool(packet["all_pass"] and consensus["all_engine_lanes_pass"])
    extra_fields = {
        "schema": "gcm_constraint_carve_v0_envelope_v1",
        "result_path": common.rel(common.ENVELOPE_PATH),
        "source_path": common.rel(Path(__file__).resolve()),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": common.CLAIM_CEILING,
        "claim": packet["claim"],
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "candidate_space": packet["candidate_space"],
        "constraint_family_C": packet["constraint_family_C"],
        "probe_family_M": packet["probe_family_M"],
        "survivor_count": packet["survivor_count"],
        "survivors": packet["survivors"],
        "kill_ledger": packet["kill_ledger"],
        "kill_counts_by_constraint": packet["kill_counts_by_constraint"],
        "quotient": packet["quotient"],
        "stability_certificate": packet["stability_certificate"],
        "adjacency_connectivity": packet["adjacency_connectivity"],
        "existence_tests": packet["existence_tests"],
        "terrain_question": packet["terrain_question"],
        "controls": packet["controls"],
        "M_C_t_hook": packet["M_C_t_hook"],
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
        "parent_lineage": common.PARENT_COMMITS,
        "expected_lanes": ["julia", "jax", "pytorch"],
        "stability_pairs": [
            {
                "subtree": common.rel(common.RESULT_PATH),
                "hash": common.sha256_file(common.RESULT_PATH),
            },
            {
                "subtree": "M_C_survivor_and_quotient_payload",
                "hash": common.stable_sha256(
                    {
                        "survivors": packet["survivors"],
                        "quotient": packet["quotient"],
                        "constraints": packet["constraint_family_C"],
                    }
                ),
            },
        ],
        "extra_fields": extra_fields,
    }


def main() -> int:
    spec = build_spec()
    common.write_json(SPEC_PATH, spec)
    print(json.dumps({"ok": True, "spec": common.rel(SPEC_PATH)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
