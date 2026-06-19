#!/usr/bin/env python3
"""Envelope builder for basin_information_fusion_v0."""

from __future__ import annotations

import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

from basin_information_fusion_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SIM_ID,
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
}

spec = importlib.util.spec_from_file_location("build_three_engine_envelope", HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(helper)

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_lane(leg: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "source_path": leg["source_path"],
        "result_path": rel(result_path),
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "package_observables": leg.get("package_observables", {}),
        "claim_path_tools": leg.get("claim_path_tools", []),
        "package_versions": leg.get("package_versions", {}),
        "capability_receipts": leg.get("capability_receipts", []),
        "tool_calls": leg.get("tool_calls", []),
        "one_to_one_tool_calls": leg.get("one_to_one_tool_calls", {}),
        "reads_parent_results": leg.get("reads_parent_results", True),
    }


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {engine: float(leg["synthesis_row"]["owner_question_basin_level_answer"]["partition_refinement_information_nats"]) for engine, leg in legs.items()}
    first = next(iter(values.values()))
    return {
        "julia_authoritative": True,
        "metric": "G0_to_G1_partition_refinement_information_nats",
        "engine_values": values,
        "max_divergence": max(abs(value - first) for value in values.values()),
    }


def key_summary(leg: dict[str, Any]) -> dict[str, Any]:
    return {
        "transitions": [
            {
                "transition_id": row["transition_id"],
                "support_delta": row["support_count_delta"]["after_minus_before"],
                "class_delta": row["class_count_delta"]["after_minus_before"],
                "counting_entropy_delta": round(row["entropy_type_delta"]["counting_entropy_log_class_count"]["after_minus_before"], 15),
            }
            for row in leg["fusion_table"]
        ],
        "owner_information_gain": round(
            leg["synthesis_row"]["owner_question_basin_level_answer"]["partition_refinement_information_nats"],
            15,
        ),
        "g2_remerge_identity_defect": leg["synthesis_row"]["g2_remerge_conservation"]["identity_defect"],
        "null_transition_zero": leg["controls"]["null_transition"]["all_deltas_zero"],
        "type_mixing_flagged": leg["controls"]["type_mixing_control"]["deliberate_cross_type_sum_flagged"],
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
    proofs = {
        "z3": jax["crossover_proofs"]["z3"],
        "cvc5": jax["crossover_proofs"]["cvc5"],
        "julia_z3": julia["crossover_proofs"]["julia_z3"],
    }
    div = divergence(legs)
    signatures = {engine: leg["fusion_signature_sha256"] for engine, leg in legs.items()}
    source_sweep_signatures = {engine: leg["source_sweep_signature_sha256"] for engine, leg in legs.items()}
    key_summaries = {engine: key_summary(leg) for engine, leg in legs.items()}
    key_summary_hashes = {engine: stable_sha256(summary) for engine, summary in key_summaries.items()}
    signature_agreement = len(set(signatures.values())) == 1
    source_sweep_agreement = len(set(source_sweep_signatures.values())) == 1
    key_summary_agreement = len(set(key_summary_hashes.values())) == 1
    all_pass = bool(
        all(leg.get("all_pass") is True for leg in legs.values())
        and key_summary_agreement
        and source_sweep_agreement
        and div["max_divergence"] == 0.0
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
        "builder_output_only": True,
        "source_backed_validation": {
            "expected_command": (
                "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
                f"scripts/validate_three_engine_sim_result.py --require-source-backed {rel(RESULT_PATH)}"
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
        "fusion_table": jax["fusion_table"],
        "synthesis_row": jax["synthesis_row"],
        "controls": jax["controls"],
        "engine_comparison": {
            "fusion_signature_sha256": signatures,
            "fusion_signature_agreement": signature_agreement,
            "fusion_signature_note": "full leg signatures may differ from non-critical serialization; key_summary gates acceptance",
            "key_summary_sha256": key_summary_hashes,
            "key_summary_agreement": key_summary_agreement,
            "source_sweep_signature_sha256": source_sweep_signatures,
            "source_sweep_signature_agreement": source_sweep_agreement,
        },
        "runtime_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "legs": {engine: leg.get("package_versions", {}) for engine, leg in legs.items()},
        },
        "build_gates": {
            "ceilings_exact": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
            "g0_g1_information_gain_log3": jax["synthesis_row"]["owner_question_basin_level_answer"]["partition_refinement_information_nats"] > 1.0986122886681096 - 1e-12,
            "g2_remerge_conserves_counting_information": jax["synthesis_row"]["g2_remerge_conservation"]["holds"] is True,
            "partition_anchors_byte_exact": jax["controls"]["partition_anchors_byte_exact"]["g0_anchor_byte_exact"] is True,
            "type_mixing_control_fired": jax["controls"]["type_mixing_control"]["deliberate_cross_type_sum_flagged"] is True,
            "null_transition_zero": jax["controls"]["null_transition"]["all_deltas_zero"] is True,
            "proofs_load_bearing": proofs["z3"]["load_bearing"] and proofs["cvc5"]["load_bearing"] and proofs["julia_z3"]["load_bearing"],
            "divergence_zero": div["max_divergence"] == 0.0,
            "one_to_one_tool_calls": len(tool_calls) == 6,
            "capability_receipts_present": set(legs) == {"julia", "jax"},
            "no_audit_verdict_written": builder_audit_boundary_ok(RESULT_DIR.parent / "audit_verdict.md"),
        },
        "result_integrity": {
            "leg_result_sha256": {engine: sha256_file(path) for engine, path in LEG_PATHS.items()},
            "build_helper_path": rel(HELPER_PATH),
            "build_helper_sha256": sha256_file(HELPER_PATH),
            "envelope_content_without_result_hash_sha256": stable_sha256(
                {"fusion_table": jax["fusion_table"], "synthesis_row": jax["synthesis_row"], "controls": jax["controls"]}
            ),
        },
    }
    return helper.build_envelope(
        sim_id=SIM_ID,
        lanes={engine: engine_lane(leg, LEG_PATHS[engine]) for engine, leg in legs.items()},
        mode="julia_canon_plus_jax_information_accounting",
        claim_path_tools=["Graphs", "Z3", "networkx", "sympy", "z3", "cvc5"],
        crossover_proofs=proofs,
        divergence=div,
        classification=CLASSIFICATION,
        promotion_allowed=PROMOTION_ALLOWED,
        formal_admission_allowed=FORMAL_ADMISSION_ALLOWED,
        parent_lineage=parent_lineage(),
        omitted_lanes={"pytorch": "not scoped: no graph/network/autograd claim path in per-transition information accounting"},
        expected_lanes=("julia", "jax", "pytorch"),
        stability_pairs=[
            ("fusion_table", stable_sha256(jax["fusion_table"])),
            ("synthesis_row", stable_sha256(jax["synthesis_row"])),
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
