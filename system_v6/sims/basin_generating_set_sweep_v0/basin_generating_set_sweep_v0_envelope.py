#!/usr/bin/env python3
"""Envelope builder for basin_generating_set_sweep_v0."""

from __future__ import annotations

import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

from basin_generating_set_sweep_v0_common import (
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
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
}

spec = importlib.util.spec_from_file_location("build_three_engine_envelope", HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(helper)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def package_observables(leg: dict[str, Any]) -> dict[str, str]:
    existing = leg.get("package_observables")
    if isinstance(existing, dict):
        return {str(key): str(value) for key, value in existing.items()}
    calls = leg.get("tool_calls", [])
    observables: dict[str, str] = {}
    for package in leg["aligned_packages_load_bearing"]:
        for call in calls:
            if isinstance(call, dict) and call.get("tool") == package:
                api = call.get("qualified_api/function") or call.get("qualified_api") or package
                output = call.get("output_object") or call.get("gates") or "claim-path observable"
                observables[package] = f"{api}: {output}"
                break
        else:
            observables[package] = leg.get("tool_manifest", {}).get(package, {}).get(
                "reason",
                f"{package} claim-path observable",
            )
    return observables


def engine_lane(leg: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "source_path": leg["source_path"],
        "result_path": rel(result_path),
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "package_observables": package_observables(leg),
        "claim_path_tools": leg.get("claim_path_tools", []),
        "package_versions": leg.get("package_versions", {}),
        "capability_receipts": leg.get("capability_receipts", []),
        "tool_calls": leg.get("tool_calls", []),
        "one_to_one_tool_calls": leg.get("one_to_one_tool_calls", {}),
    }


def compare_leg_signatures(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    signatures = {engine: leg["sweep_signature_sha256"] for engine, leg in legs.items()}
    return {
        "sweep_signature_sha256": signatures,
        "sweep_signature_agreement": len(set(signatures.values())) == 1,
        "sweep_signature_text": {engine: leg.get("sweep_signature_text") for engine, leg in legs.items()},
    }


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {
        engine: float(sum(row["terminal_class_count"] for row in leg["partition_fate_table"]))
        for engine, leg in legs.items()
    }
    first = next(iter(values.values()))
    return {
        "julia_authoritative": True,
        "metric": "sum_terminal_class_counts",
        "engine_values": values,
        "max_divergence": max(abs(value - first) for value in values.values()),
    }


def build_result() -> dict[str, Any]:
    legs = {engine: load(path) for engine, path in LEG_PATHS.items()}
    jax = legs["jax"]
    julia = legs["julia"]
    pytorch = legs["pytorch"]
    comparison = compare_leg_signatures(legs)
    div = divergence(legs)
    proofs = {
        "z3": jax["crossover_proofs"]["z3"],
        "cvc5": jax["crossover_proofs"]["cvc5"],
        "julia_z3": julia["crossover_proofs"]["julia_z3"],
        "pytorch_z3": pytorch["crossover_proofs"]["z3"],
        "pytorch_cvc5": pytorch["crossover_proofs"]["cvc5"],
    }
    all_pass = bool(
        all(leg.get("all_pass") is True for leg in legs.values())
        and comparison["sweep_signature_agreement"]
        and div["max_divergence"] == 0.0
        and proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_verdict"] == proofs["cvc5"]["erased_flip_verdict"] == "sat"
        and proofs["julia_z3"]["verdict"] == "unsat"
        and proofs["julia_z3"]["erased_flip_verdict"] == "sat"
    )
    extra_fields = {
        "ceiling": CLASSIFICATION,
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "standard_schema_mode": "all_three_full_sims",
        "builder_output_only": True,
        "source_backed_validation": {
            "expected_command": (
                "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
                f"scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed {rel(RESULT_PATH)}"
            )
        },
        "TOOL_MANIFEST": {engine: leg.get("TOOL_MANIFEST", {}) for engine, leg in legs.items()},
        "TOOL_INTEGRATION_DEPTH": {engine: leg.get("TOOL_INTEGRATION_DEPTH", {}) for engine, leg in legs.items()},
        "capability_receipts": {engine: leg.get("capability_receipts", []) for engine, leg in legs.items()},
        "tool_calls": {engine: leg.get("tool_calls", []) for engine, leg in legs.items()},
        "one_to_one_tool_calls": {
            "pass": all(leg.get("one_to_one_tool_calls", {}).get("pass") is True for leg in legs.values()),
            "by_engine": {engine: leg.get("one_to_one_tool_calls", {}) for engine, leg in legs.items()},
        },
        "parent_lineage": parent_lineage(),
        "seed_ledger": jax["seed_ledger"],
        "partition_fate_table": jax["partition_fate_table"],
        "sweep": jax["sweep"],
        "controls": jax["controls"],
        "sub_basin_answer": jax["sub_basin_answer"],
        "engine_dof_reading": jax["engine_dof_reading"],
        "engine_comparison": comparison,
        "runtime_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "legs": {engine: leg.get("package_versions", {}) for engine, leg in legs.items()},
        },
        "build_gates": {
            "classification_scratch": CLASSIFICATION == "scratch_diagnostic",
            "promotion_blocked": PROMOTION_ALLOWED is False,
            "formal_admission_blocked": FORMAL_ADMISSION_ALLOWED is False,
            "g0_anchor_byte_exact": jax["sweep"]["G0"]["baseline_anchor_byte_exact"] is True,
            "g1_splits": jax["sweep"]["G1"]["terminal_class_count"] == 3,
            "g2_survives": jax["sweep"]["G2"]["terminal_class_count"] == 1,
            "g3_left_splits": jax["sweep"]["G3L"]["terminal_class_count"] == 3,
            "g3_right_splits": jax["sweep"]["G3R"]["terminal_class_count"] == 3,
            "g4_conditioned_shrinks": jax["sweep"]["G4"]["state_count"] == 4 and jax["sweep"]["G4"]["terminal_class_count"] == 1,
            "g5_composite_splits": jax["sweep"]["G5"]["terminal_class_count"] == 5,
            "source_backed_lanes_present": set(legs) == {"julia", "jax", "pytorch"},
            "partition_signature_cross_engine_agreement": comparison["sweep_signature_agreement"],
        },
        "result_integrity": {
            "leg_result_sha256": {engine: sha256_file(path) for engine, path in LEG_PATHS.items()},
            "build_helper_path": rel(HELPER_PATH),
            "build_helper_sha256": sha256_file(HELPER_PATH),
            "envelope_content_without_result_hash_sha256": stable_sha256(
                {
                    "partition_fate_table": jax["partition_fate_table"],
                    "controls": jax["controls"],
                    "sub_basin_answer": jax["sub_basin_answer"],
                    "engine_dof_reading": jax["engine_dof_reading"],
                    "comparison": comparison,
                }
            ),
        },
    }
    envelope = helper.build_envelope(
        sim_id=SIM_ID,
        lanes={engine: engine_lane(leg, LEG_PATHS[engine]) for engine, leg in legs.items()},
        mode="generating_set_partition_sweep",
        claim_path_tools=["Z3", "sympy", "z3", "cvc5", "torch.func", "torch_geometric"],
        crossover_proofs=proofs,
        divergence=div,
        classification=CLASSIFICATION,
        promotion_allowed=PROMOTION_ALLOWED,
        formal_admission_allowed=FORMAL_ADMISSION_ALLOWED,
        parent_lineage=parent_lineage(),
        expected_lanes=("julia", "jax", "pytorch"),
        stability_pairs=[
            ("partition_fate_table", stable_sha256(jax["partition_fate_table"])),
            ("sub_basin_answer", stable_sha256(jax["sub_basin_answer"])),
            ("engine_dof_reading", stable_sha256(jax["engine_dof_reading"])),
        ],
        generated_at=now_z(),
        extra_fields=extra_fields,
    )
    return envelope


def main() -> int:
    payload = build_result()
    write_json(RESULT_PATH, payload)
    print({"ok": payload["all_pass"], "result_path": rel(RESULT_PATH)})
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
