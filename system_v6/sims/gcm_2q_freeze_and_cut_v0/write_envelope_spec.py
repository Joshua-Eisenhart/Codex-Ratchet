#!/usr/bin/env python3
"""Write the three-engine envelope spec/result for gcm_2q_freeze_and_cut_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import gcm_2q_freeze_and_cut_v0_common as common


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
        "reads_peer_result": False,
        "packages_used": result["packages_used"],
        "aligned_packages_load_bearing": result["aligned_packages_load_bearing"],
        "package_observables": result["package_observables"],
        "result_all_pass": result["all_pass"],
        "survivor_count": result["survivor_count"],
        "quotient_class_count": result["quotient_class_count"],
        "candidate_region_count": result["candidate_region_count"],
        "product_survivor_count": result["product_survivor_count"],
        "entangled_survivor_count": result["entangled_survivor_count"],
        "embedded_1q_count": result["embedded_1q_count"],
        "metric_summary": result["metric_summary"],
    }


def engine_consensus(engine_results: dict[str, dict[str, Any]], packet: dict[str, Any]) -> dict[str, Any]:
    expected_counts = {
        "survivor_count": packet["counts"]["two_q_survivor_count"],
        "quotient_class_count": packet["counts"]["two_q_class_count"],
        "candidate_region_count": packet["counts"]["candidate_region_count"],
        "product_survivor_count": packet["counts"]["product_survivor_count"],
        "entangled_survivor_count": packet["counts"]["entangled_survivor_count"],
        "embedded_1q_count": packet["counts"]["one_q_product_embedding_count"],
    }
    by_count = {
        count_name: {engine: result[count_name] for engine, result in engine_results.items()}
        for count_name in expected_counts
    }
    metric_names = ("max_product_negativity", "min_entangled_negativity", "max_entangled_conditional")
    by_metric = {
        metric: {engine: result["metric_summary"][metric] for engine, result in engine_results.items()}
        for metric in metric_names
    }
    return {
        "all_engine_lanes_pass": all(result["all_pass"] is True for result in engine_results.values()),
        "count_agreement": {
            name: set(values.values()) == {expected_counts[name]} for name, values in by_count.items()
        },
        "metric_agreement_within_tolerance": {
            metric: max(values.values()) - min(values.values()) <= 1.0e-10 for metric, values in by_metric.items()
        },
        "counts_by_engine": by_count,
        "metrics_by_engine": by_metric,
    }


def build_spec() -> dict[str, Any]:
    packet = load(common.RESULT_PATH)
    registry = load(common.REGISTRY_PATH)
    engine_results = {name: load(path) for name, path in ENGINE_RESULT_PATHS.items()}
    consensus = engine_consensus(engine_results, packet)
    all_pass = bool(
        packet["all_pass"]
        and consensus["all_engine_lanes_pass"]
        and all(consensus["count_agreement"].values())
        and all(consensus["metric_agreement_within_tolerance"].values())
    )
    extra_fields = {
        "schema": f"{common.SIM_ID}_envelope_v1",
        "result_path": common.rel(common.ENVELOPE_PATH),
        "source_path": common.rel(Path(__file__).resolve()),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": common.CLAIM_CEILING,
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "three_coordinates": packet["three_coordinates"],
        "cut": packet["cut"],
        "registry_path": common.rel(common.REGISTRY_PATH),
        "registry_body_sha256": registry["registry_body_sha256"],
        "gcm_2q_object_id": registry["gcm_2q_object_id"],
        "counts": packet["counts"],
        "cross_rung_lineage_summary": {
            "partial_trace_A_image_equals_1q_survivor_set": packet["cross_rung_lineage"][
                "partial_trace_A_image_equals_1q_survivor_set"
            ],
            "product_control_embedding_count": packet["cross_rung_lineage"]["product_control_embedding_count"],
            "product_control_embedding_all_survive": packet["cross_rung_lineage"][
                "product_control_embedding_all_survive"
            ],
            "partial_trace_B_resolved_to_1q_survivor_count": packet["cross_rung_lineage"][
                "partial_trace_B_resolved_to_1q_survivor_count"
            ],
        },
        "entangled_vs_product_separation": packet["entangled_vs_product_separation"],
        "monogamy_row": packet["monogamy_row"],
        "controls": packet["controls"],
        "engine_lanes": sorted(engine_results),
        "engine_consensus": consensus,
        "TOOL_MANIFEST": common.TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": common.TOOL_INTEGRATION_DEPTH,
        "tool_intent": common.TOOL_INTENT,
        "source_locks": packet["source_locks"],
        "builder_gates": packet["builder_gates"],
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "all_pass": all_pass,
        "disallowed_claims": packet["disallowed_claims"],
    }
    rehomed_builder_fields = {
        key: extra_fields.pop(key)
        for key in (
            "classification",
            "formal_admission_allowed",
            "promotion_allowed",
        )
        if key in extra_fields
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
            "base_gcm_object_id": common.EXPECTED_BASE_OBJECT_ID,
            "base_registry_body_sha256": common.EXPECTED_BASE_REGISTRY_BODY_SHA256,
            "gcm_2q_object_id": registry["gcm_2q_object_id"],
            "gcm_2q_registry_body_sha256": registry["registry_body_sha256"],
            "two_q_carve_result_sha256": common.sha256_file(common.TWO_Q_CARVE_RESULT),
            "one_q_entropy_sweep_result_sha256": common.sha256_file(common.ONE_Q_ENTROPY_SWEEP_RESULT),
        },
        "expected_lanes": ["julia", "jax", "pytorch"],
        "stability_pairs": [
            {"subtree": common.rel(common.RESULT_PATH), "hash": common.sha256_file(common.RESULT_PATH)},
            {"subtree": common.rel(common.REGISTRY_PATH), "hash": common.sha256_file(common.REGISTRY_PATH)},
            {
                "subtree": "gcm_2q_registry_and_cut_summary",
                "hash": common.stable_sha256(
                    {
                        "registry": registry["frozen_2q_registry"],
                        "counts": packet["counts"],
                        "separation": packet["entangled_vs_product_separation"],
                        "monogamy": packet["monogamy_row"],
                    }
                ),
            },
        ],
        **rehomed_builder_fields,
        "extra_fields": extra_fields,
    }


def main() -> int:
    spec = build_spec()
    common.write_json(SPEC_PATH, spec)
    envelope = build_envelope(**spec)
    common.write_json(common.ENVELOPE_PATH, envelope)
    print(
        json.dumps(
            {"ok": envelope.get("all_pass") is True, "spec": common.rel(SPEC_PATH), "envelope": common.rel(common.ENVELOPE_PATH)},
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if envelope.get("all_pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
