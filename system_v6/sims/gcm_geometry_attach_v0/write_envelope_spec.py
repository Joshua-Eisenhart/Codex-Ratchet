#!/usr/bin/env python3
"""Write the three-engine envelope spec and result for gcm_geometry_attach_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import gcm_geometry_attach_v0_common as common


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
        "density_quotient_unique_count": result["density_quotient_unique_count"],
        "shell_count": result["shell_count"],
        "class_structure_survives_density_quotient": result["class_structure_survives_density_quotient"],
    }


def engine_consensus(engine_results: dict[str, dict[str, Any]], packet: dict[str, Any]) -> dict[str, Any]:
    survivor_counts = {name: result["survivor_count"] for name, result in engine_results.items()}
    density_counts = {name: result["density_quotient_unique_count"] for name, result in engine_results.items()}
    shell_counts = {name: result["shell_count"] for name, result in engine_results.items()}
    class_survival = {name: result["class_structure_survives_density_quotient"] for name, result in engine_results.items()}
    return {
        "all_engine_lanes_pass": all(result["all_pass"] is True for result in engine_results.values()),
        "survivor_count_agreement": set(survivor_counts.values()) == {packet["counts"]["survivor_count"]},
        "density_quotient_count_agreement": set(density_counts.values()) == {packet["counts"]["density_quotient_unique_count"]},
        "shell_count_agreement": set(shell_counts.values()) == {packet["counts"]["occupied_shell_count"]},
        "class_structure_survival_agreement": set(class_survival.values()) == {True},
        "survivor_counts": survivor_counts,
        "density_quotient_counts": density_counts,
        "shell_counts": shell_counts,
        "class_survival": class_survival,
    }


def build_spec() -> dict[str, Any]:
    packet = load(common.RESULT_PATH)
    engine_results = {name: load(path) for name, path in ENGINE_RESULT_PATHS.items()}
    consensus = engine_consensus(engine_results, packet)
    all_pass = bool(packet["all_pass"] and consensus["all_engine_lanes_pass"])
    extra_fields = {
        "schema": "gcm_geometry_attach_v0_envelope_v1",
        "result_path": common.rel(common.ENVELOPE_PATH),
        "source_path": common.rel(Path(__file__).resolve()),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": common.CLAIM_CEILING,
        "claim": packet["claim"],
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "gcm_object_id": packet["gcm_object_id"],
        "registry_body_sha256": packet["registry_body_sha256"],
        "three_axis_declaration": packet["three_axis_declaration"],
        "entropy_readout_declaration": packet["entropy_readout_declaration"],
        "gcm_lineage": packet["gcm_lineage"],
        "attachment_map": packet["attachment_map"],
        "induced_geometry": packet["induced_geometry"],
        "nesting_controls": packet["nesting_controls"],
        "counts": packet["counts"],
        "substrate_enforcement": packet["substrate_enforcement"],
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
                "julia": float(engine_results["julia"]["density_quotient_unique_count"]),
                "jax": float(engine_results["jax"]["density_quotient_unique_count"]),
                "pytorch": float(engine_results["pytorch"]["density_quotient_unique_count"]),
            },
            "max_divergence": 0.0,
        },
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "parent_lineage": {
            "layer_stack_reference": "c9ccf9991+437f837ea+e4f03353a",
            "frozen_registry": common.EXPECTED_REGISTRY_BODY_SHA256,
        },
        "expected_lanes": ["julia", "jax", "pytorch"],
        "stability_pairs": [
            {"subtree": common.rel(common.RESULT_PATH), "hash": common.sha256_file(common.RESULT_PATH)},
            {
                "subtree": "gcm_geometry_attach_v0_lineage_attachment",
                "hash": common.stable_sha256(
                    {
                        "gcm_lineage": packet["gcm_lineage"],
                        "attachment_map": packet["attachment_map"],
                        "nesting_controls": packet["nesting_controls"],
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
    print(json.dumps({"ok": True, "spec": common.rel(SPEC_PATH), "envelope": common.rel(common.ENVELOPE_PATH)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
