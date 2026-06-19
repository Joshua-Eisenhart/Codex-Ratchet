#!/usr/bin/env python3
"""Envelope builder for basin_information_fusion_v1."""

from __future__ import annotations

import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

from basin_information_fusion_v1_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SIM_ID,
    TOOL_INTENT,
    now_z,
    parent_lineage,
    rel,
    sha256_file,
    stable_sha256,
    write_json,
)


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
HELPER_PATH = ROOT / "scripts" / "build_three_engine_envelope.py"
LEG_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
}

spec = importlib.util.spec_from_file_location("build_three_engine_envelope", HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(helper)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_lane(leg: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "source_path": leg["source_path"],
        "result_path": rel(result_path),
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "package_observables": leg["package_observables"],
        "claim_path_tools": leg.get("claim_path_tools", []),
        "package_versions": leg.get("package_versions", {}),
        "capability_receipts": leg.get("capability_receipts", []),
        "tool_calls": leg.get("tool_calls", []),
        "one_to_one_tool_calls": leg.get("one_to_one_tool_calls", {}),
        "reads_parent_results": leg.get("reads_parent_results", True),
    }


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {
        "julia": float(legs["julia"]["record_reference"]["syndrome_class_count"]),
        "jax": float(legs["jax"]["record_retention_at_g1_merge"]["syndrome_class_count"]),
        "pytorch": float(legs["pytorch"]["record_retention_at_g1_merge"]["syndrome_class_count"]),
    }
    first = values["julia"]
    return {
        "julia_authoritative": True,
        "metric": "computed_G1_syndrome_class_count",
        "engine_values": values,
        "max_divergence": max(abs(value - first) for value in values.values()),
    }


def key_summary(leg: dict[str, Any]) -> dict[str, Any]:
    if leg["engine"] == "julia":
        return {
            "syndrome_class_count": leg["record_reference"]["syndrome_class_count"],
            "full_record_count": leg["record_reference"]["full_record_count"],
            "erased_record_count": leg["record_reference"]["erased_record_count"],
            "julia_z3": leg["crossover_proofs"]["julia_z3"]["verdict"],
            "julia_z3_erased": leg["crossover_proofs"]["julia_z3"]["erased_flip_verdict"],
        }
    record = leg["record_retention_at_g1_merge"]
    controls = leg["controls"]
    return {
        "syndrome_class_count": record["syndrome_class_count"],
        "full_record_count": record["readout_recoverability"]["constructed_full_syndrome_record"]["readout_label_count"],
        "erased_record_count": record["readout_recoverability"]["erased_record_control"]["readout_label_count"],
        "full_record_defect": record["readout_recoverability"]["constructed_full_syndrome_record"]["conservation_defect_nats"],
        "erased_record_defect": record["readout_recoverability"]["erased_record_control"]["conservation_defect_nats"],
        "partial_record_entropy": record["readout_recoverability"]["partial_record_control"]["recoverable_counting_entropy_nats"],
        "shuffled_changed": controls["shuffled_order_control"]["production_trajectory_changed"],
        "similarity_fails": controls["similarity_only_control"]["basin_conditioned_rows_fail"],
    }


def flatten_tool_calls(legs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for engine, leg in legs.items():
        for call in leg.get("tool_calls", []):
            row = dict(call)
            row["engine"] = engine
            calls.append(row)
    return calls


def build_result() -> dict[str, Any]:
    legs = {engine: load(path) for engine, path in LEG_PATHS.items()}
    jax = legs["jax"]
    julia = legs["julia"]
    pytorch = legs["pytorch"]
    div = divergence(legs)
    proofs = {
        "z3": jax["crossover_proofs"]["z3"],
        "cvc5": jax["crossover_proofs"]["cvc5"],
        "julia_z3": julia["crossover_proofs"]["julia_z3"],
        "pytorch_z3": pytorch["crossover_proofs"]["z3"],
        "pytorch_cvc5": pytorch["crossover_proofs"]["cvc5"],
    }
    key_summaries = {engine: key_summary(leg) for engine, leg in legs.items()}
    common_gate_source = dict(jax["build_gates"])
    top_gates = {
        **common_gate_source,
        "all_engine_legs_pass": all(leg.get("all_pass") is True for leg in legs.values()),
        "three_engine_divergence_zero": div["max_divergence"] == 0.0,
        "tool_intent_present": bool(TOOL_INTENT["claim_classes"]) and set(TOOL_INTENT["engine_tool_intent"]) == {"julia", "jax", "pytorch"},
        "one_to_one_tool_calls": all(leg.get("one_to_one_tool_calls", {}).get("pass") is True for leg in legs.values()),
    }
    all_pass = bool(
        all(top_gates.values())
        and proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] == proofs["julia_z3"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_verdict"] == proofs["cvc5"]["erased_flip_verdict"] == proofs["julia_z3"]["erased_flip_verdict"] == "sat"
    )
    tool_calls = flatten_tool_calls(legs)
    extra_fields = {
        "ceiling": CLASSIFICATION,
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "standard_schema_mode": "all_three_full_sims",
        "builder_output_only": True,
        "tool_intent": TOOL_INTENT,
        "source_backed_validation": {
            "expected_command": (
                "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
                f"scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent {rel(RESULT_PATH)}"
            )
        },
        "TOOL_MANIFEST": {engine: leg.get("TOOL_MANIFEST", {}) for engine, leg in legs.items()},
        "TOOL_INTEGRATION_DEPTH": {engine: leg.get("TOOL_INTEGRATION_DEPTH", {}) for engine, leg in legs.items()},
        "capability_receipts": {engine: leg.get("capability_receipts", []) for engine, leg in legs.items()},
        "tool_calls": tool_calls,
        "one_to_one_tool_calls": {
            "pass": all(leg.get("one_to_one_tool_calls", {}).get("pass") is True for leg in legs.values()),
            "by_engine": {engine: leg.get("one_to_one_tool_calls", {}) for engine, leg in legs.items()},
        },
        "parent_lineage": parent_lineage(),
        "seed_ledger": jax["seed_ledger"],
        "sweep_partition_rows": jax["sweep_partition_rows"],
        "entropy_production_along_orbits": jax["entropy_production_along_orbits"],
        "record_retention_at_g1_merge": jax["record_retention_at_g1_merge"],
        "per_class_throughput": jax["per_class_throughput"],
        "basin_conditioned_flow": jax["basin_conditioned_flow"],
        "controls": jax["controls"],
        "binding_basin_packet_contract": jax["binding_basin_packet_contract"],
        "claim_sections": jax["claim_sections"],
        "engine_key_summary": key_summaries,
        "engine_comparison": {
            "joint_object_signature_sha256": {
                "jax": jax["joint_object_signature_sha256"],
                "pytorch": pytorch["joint_object_signature_sha256"],
                "julia": julia["joint_object_signature_sha256"],
            },
            "summary_sha256": {engine: stable_sha256(summary) for engine, summary in key_summaries.items()},
            "julia_reference_compares_record_counts": div["max_divergence"] == 0.0,
        },
        "runtime_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "legs": {engine: leg.get("package_versions", {}) for engine, leg in legs.items()},
        },
        "build_gates": top_gates,
        "result_integrity": {
            "leg_result_sha256": {engine: sha256_file(path) for engine, path in LEG_PATHS.items()},
            "build_helper_path": rel(HELPER_PATH),
            "build_helper_sha256": sha256_file(HELPER_PATH),
            "envelope_content_without_result_hash_sha256": stable_sha256(
                {
                    "entropy_production_along_orbits": jax["entropy_production_along_orbits"],
                    "record_retention_at_g1_merge": jax["record_retention_at_g1_merge"],
                    "per_class_throughput": jax["per_class_throughput"],
                    "basin_conditioned_flow": jax["basin_conditioned_flow"],
                    "controls": jax["controls"],
                    "tool_intent": TOOL_INTENT,
                }
            ),
        },
    }
    return helper.build_envelope(
        sim_id=SIM_ID,
        lanes={engine: engine_lane(leg, LEG_PATHS[engine]) for engine, leg in legs.items()},
        mode="all_three_full_sims",
        claim_path_tools=["Z3", "networkx", "sympy", "z3", "cvc5"],
        crossover_proofs=proofs,
        divergence=div,
        classification=CLASSIFICATION,
        promotion_allowed=PROMOTION_ALLOWED,
        formal_admission_allowed=FORMAL_ADMISSION_ALLOWED,
        parent_lineage=parent_lineage(),
        expected_lanes=("julia", "jax", "pytorch"),
        stability_pairs=[
            ("entropy_production_along_orbits", stable_sha256(jax["entropy_production_along_orbits"])),
            ("record_retention_at_g1_merge", stable_sha256(jax["record_retention_at_g1_merge"])),
            ("per_class_throughput", stable_sha256(jax["per_class_throughput"])),
            ("basin_conditioned_flow", stable_sha256(jax["basin_conditioned_flow"])),
            ("controls", stable_sha256(jax["controls"])),
        ],
        generated_at=now_z(),
        extra_fields=extra_fields,
    )


def main() -> int:
    payload = build_result()
    write_json(RESULT_PATH, payload)
    print({"ok": payload["all_pass"], "result_path": rel(RESULT_PATH)})
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
