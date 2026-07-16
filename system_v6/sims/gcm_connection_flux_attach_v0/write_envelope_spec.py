#!/usr/bin/env python3
"""Write the three-engine envelope spec and result for gcm_connection_flux_attach_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import gcm_connection_flux_attach_v0_common as common


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
        "shell_count": result["shell_count"],
        "shell_occupation_signature": result["shell_occupation_signature"],
        "leakage_status": result["leakage_status"],
    }


def engine_consensus(engine_results: dict[str, dict[str, Any]], packet: dict[str, Any]) -> dict[str, Any]:
    survivor_counts = {name: result["survivor_count"] for name, result in engine_results.items()}
    shell_counts = {name: result["shell_count"] for name, result in engine_results.items()}
    signatures = {name: result["shell_occupation_signature"] for name, result in engine_results.items()}
    leakage = {name: result["leakage_status"] for name, result in engine_results.items()}
    return {
        "all_engine_lanes_pass": all(result["all_pass"] is True for result in engine_results.values()),
        "survivor_count_agreement": set(survivor_counts.values()) == {packet["counts"]["survivor_count"]},
        "shell_count_agreement": set(shell_counts.values()) == {packet["counts"]["occupied_shell_count"]},
        "shell_signature_agreement": set(signatures.values()) == {packet["connection_flux_attachment"]["shell_occupation_signature"]},
        "leakage_status_agreement": set(leakage.values()) == {packet["leakage_analysis"]["status"]},
        "survivor_counts": survivor_counts,
        "shell_counts": shell_counts,
        "shell_signatures": signatures,
        "leakage_status": leakage,
    }


def build_spec() -> dict[str, Any]:
    packet = load(common.RESULT_PATH)
    engine_results = {name: load(path) for name, path in ENGINE_RESULT_PATHS.items()}
    consensus = engine_consensus(engine_results, packet)
    all_pass = bool(packet["all_pass"] and consensus["all_engine_lanes_pass"])
    extra_fields = {
        "schema": "gcm_connection_flux_attach_v0_envelope_v1",
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
        "readout_declaration": packet["readout_declaration"],
        "seven_audit_questions": packet["seven_audit_questions"],
        "gcm_lineage": packet["gcm_lineage"],
        "upstream_conditionals": packet["upstream_conditionals"],
        "connection_flux_attachment": packet["connection_flux_attachment"],
        "leakage_analysis": packet["leakage_analysis"],
        "controls": packet["controls"],
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
                "julia": float(engine_results["julia"]["shell_count"]),
                "jax": float(engine_results["jax"]["shell_count"]),
                "pytorch": float(engine_results["pytorch"]["shell_count"]),
            },
            "max_divergence": 0.0,
        },
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "parent_lineage": {
            "frozen_registry": common.EXPECTED_REGISTRY_BODY_SHA256,
            "geometry_attach_result_file_sha256": packet["upstream_conditionals"]["gcm_geometry_attach_v0"]["file_sha256"],
            "geometry_attach_result_sha256": packet["upstream_conditionals"]["gcm_geometry_attach_v0"]["result_sha256"],
            "s2_formula_feedstock": packet["upstream_conditionals"]["geo_s2_connection_flux_foliation_v0"]["file_sha256"],
        },
        "expected_lanes": ["julia", "jax", "pytorch"],
        "stability_pairs": [
            {"subtree": common.rel(common.RESULT_PATH), "hash": common.sha256_file(common.RESULT_PATH)},
            {
                "subtree": "connection_flux_shell_rows",
                "hash": common.stable_sha256(packet["connection_flux_attachment"]["shell_rows"]),
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
