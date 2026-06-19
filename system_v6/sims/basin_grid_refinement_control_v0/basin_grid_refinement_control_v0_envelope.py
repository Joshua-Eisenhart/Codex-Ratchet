#!/usr/bin/env python3
"""Envelope builder for basin_grid_refinement_control_v0."""

from __future__ import annotations

import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

from basin_grid_refinement_control_v0_common import (
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


def engine_lane(leg: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "source_path": leg["source_path"],
        "result_path": rel(result_path),
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "claim_path_tools": leg.get("claim_path_tools", []),
        "package_versions": leg.get("package_versions", {}),
        "capability_receipts": leg.get("capability_receipts", []),
        "tool_calls": leg.get("tool_calls", []),
        "one_to_one_tool_calls": leg.get("one_to_one_tool_calls", {}),
    }


def key_fate_summary(leg: dict[str, Any]) -> dict[str, Any]:
    table = leg["persistence_table"]
    return {
        "refinement_counts": [
            {
                "label": row["label"],
                "state_count": row["state_count"],
                "terminal_class_count": row["terminal_class_count"],
                "overall_fate": row["persistence"]["overall_fate"],
                "class_fates": {
                    key: value["fate"]
                    for key, value in sorted(row["persistence"]["committed_class_fates"].items())
                },
            }
            for row in table["refinement"]
        ],
        "rotated_terminal_class_count": table["rotated_grid"]["terminal_class_count"],
        "rotated_overall_fate": table["rotated_grid"]["persistence"]["overall_fate"],
        "rotated_class_fates": {
            key: value["fate"]
            for key, value in sorted(table["rotated_grid"]["persistence"]["committed_class_fates"].items())
        },
        "g0_refined_terminal_counts": [
            row["terminal_class_count"] for row in table["g0_dissipative_refined_control"]
        ],
        "artifact_dies_under_rotation": table["axis_artifact_control"]["dies_under_rotation"],
    }


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {
        engine: float(leg["persistence_table"]["rotated_grid"]["terminal_class_count"])
        for engine, leg in legs.items()
    }
    first = next(iter(values.values()))
    return {
        "julia_authoritative": True,
        "metric": "rotated_grid_terminal_class_count",
        "engine_values": values,
        "max_divergence": max(abs(value - first) for value in values.values()),
    }


def build_result() -> dict[str, Any]:
    legs = {engine: load(path) for engine, path in LEG_PATHS.items()}
    jax = legs["jax"]
    julia = legs["julia"]
    pytorch = legs["pytorch"]
    key_summaries = {engine: key_fate_summary(leg) for engine, leg in legs.items()}
    jax_pytorch_signature_agreement = jax["analysis_signature_sha256"] == pytorch["analysis_signature_sha256"]
    key_summary_agreement = len({stable_sha256(summary) for summary in key_summaries.values()}) == 1
    proofs = {
        "z3": jax["crossover_proofs"]["z3"],
        "cvc5": jax["crossover_proofs"]["cvc5"],
        "julia_z3": julia["crossover_proofs"]["julia_z3"],
        "pytorch_z3": pytorch["crossover_proofs"]["z3"],
        "pytorch_cvc5": pytorch["crossover_proofs"]["cvc5"],
    }
    div = divergence(legs)
    all_pass = bool(
        all(leg.get("all_pass") is True for leg in legs.values())
        and jax_pytorch_signature_agreement
        and key_summary_agreement
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
        "grid_declaration": jax["analysis"]["grid_declaration"],
        "persistence_table": jax["persistence_table"],
        "c1_answer": jax["c1_answer"],
        "engine_key_fate_summary": key_summaries,
        "engine_comparison": {
            "jax_pytorch_analysis_signature_agreement": jax_pytorch_signature_agreement,
            "key_summary_agreement": key_summary_agreement,
            "analysis_signature_sha256": {
                engine: leg["analysis_signature_sha256"] for engine, leg in legs.items()
            },
        },
        "runtime_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "legs": {engine: leg.get("package_versions", {}) for engine, leg in legs.items()},
        },
        "build_gates": {
            "classification_scratch": CLASSIFICATION == "scratch_diagnostic",
            "promotion_blocked": PROMOTION_ALLOWED is False,
            "formal_admission_blocked": FORMAL_ADMISSION_ALLOWED is False,
            "g1_anchor_byte_exact": jax["persistence_table"]["anchor"]["byte_exact"] is True,
            "refined_2x_persists": jax["persistence_table"]["refinement"][0]["persistence"]["overall_fate"] == "PERSIST",
            "refined_3x_persists": jax["persistence_table"]["refinement"][1]["persistence"]["overall_fate"] == "PERSIST",
            "rotated_grid_changes_classes": jax["persistence_table"]["rotated_grid"]["persistence"]["overall_fate"] == "CHANGED",
            "g0_refined_stays_one_class": all(row["stays_one_class"] for row in jax["persistence_table"]["g0_dissipative_refined_control"]),
            "axis_artifact_dies": jax["persistence_table"]["axis_artifact_control"]["dies_under_rotation"] is True,
            "continuous_closure_so3": jax["persistence_table"]["continuous_cross_check"]["closure_result"] == "SO(3)",
            "source_backed_lanes_present": set(legs) == {"julia", "jax", "pytorch"},
        },
        "result_integrity": {
            "leg_result_sha256": {engine: sha256_file(path) for engine, path in LEG_PATHS.items()},
            "build_helper_path": rel(HELPER_PATH),
            "build_helper_sha256": sha256_file(HELPER_PATH),
            "envelope_content_without_result_hash_sha256": stable_sha256(
                {
                    "persistence_table": jax["persistence_table"],
                    "c1_answer": jax["c1_answer"],
                    "comparison": key_summaries,
                }
            ),
        },
    }
    return helper.build_envelope(
        sim_id=SIM_ID,
        lanes={engine: engine_lane(leg, LEG_PATHS[engine]) for engine, leg in legs.items()},
        mode="basin_grid_refinement_control",
        claim_path_tools=["Graphs", "Z3", "networkx", "sympy", "z3", "cvc5", "torch.func", "torch_geometric"],
        crossover_proofs=proofs,
        divergence=div,
        classification=CLASSIFICATION,
        promotion_allowed=PROMOTION_ALLOWED,
        formal_admission_allowed=FORMAL_ADMISSION_ALLOWED,
        parent_lineage=parent_lineage(),
        expected_lanes=("julia", "jax", "pytorch"),
        stability_pairs=[
            ("persistence_table", stable_sha256(jax["persistence_table"])),
            ("c1_answer", stable_sha256(jax["c1_answer"])),
            ("engine_key_fate_summary", stable_sha256(key_summaries)),
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
