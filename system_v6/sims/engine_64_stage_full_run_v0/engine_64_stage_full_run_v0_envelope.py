#!/usr/bin/env python3
"""Canonical three-engine envelope builder for engine_64_stage_full_run_v0."""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

import engine_64_stage_full_run_v0_common as common


SIM_ID = common.SIM_ID
RESULT_PATH = common.RESULT_DIR / f"{SIM_ID}_envelope_results.json"
SOURCE_PATH = common.SIM_DIR / f"{SIM_ID}_envelope.py"
BASE_RESULT_PATH = common.RESULT_PATH
LEG_PATHS = {
    "julia": common.RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": common.RESULT_DIR / f"{SIM_ID}_jax_results.json",
}

HELPER_PATH = common.ROOT / "scripts" / "build_three_engine_envelope.py"
spec = importlib.util.spec_from_file_location("build_three_engine_envelope", HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(helper)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_lane(leg: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "source_path": leg["source_path"],
        "result_path": common.rel(result_path),
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "package_observables": leg["package_observables"],
        "TOOL_MANIFEST": leg.get("TOOL_MANIFEST", {}),
        "TOOL_INTEGRATION_DEPTH": leg.get("TOOL_INTEGRATION_DEPTH", {}),
    }


def compare_leg_to_base(base: dict[str, Any], leg: dict[str, Any]) -> dict[str, bool]:
    base_values = base["gate_values"]
    leg_counts = leg["counts"]
    base_rows = base["coordinate_consistency"]
    leg_rows = leg["slot_coordinate_consistency"]
    return {
        "total_slots_match_base": leg_counts["total_slots"] == base_values["total_slots"] == 64,
        "unique_coordinate_count_matches_base": leg_counts["unique_coordinate_count"]
        == base_values["unique_coordinate_count"]
        == 64,
        "type1_slots_match_base": leg_counts["type1_slots"] == base_values["type1_slots"] == 32,
        "type2_slots_match_base": leg_counts["type2_slots"] == base_values["type2_slots"] == 32,
        "bad_coordinate_rows_match_base": leg_counts["bad_coordinate_rows"]
        == base_values["bad_coordinate_rows"]
        == 0,
        "coordinate_row_count_matches_base": leg_rows["row_count"] == len(base_rows["rows"]) == 64,
        "coordinate_rows_all_pass_match_base": leg_rows["all_rows_pass"] is True
        and base_rows["all_rows_pass"] is True,
    }


def full_run_summary(base: dict[str, Any]) -> dict[str, Any]:
    runs = base["runs"]
    controls = base["controls"]
    consistency = base["coordinate_consistency"]
    comparison = base["type1_l_vs_type2_r_comparison"]
    gate_values = base["gate_values"]
    full = runs["full_64_slot_trajectory"]
    summary = {
        "all_64_slots_executed_per_engine": {
            "present": gate_values.get("total_slots") == 64
            and gate_values.get("type1_slots") == 32
            and gate_values.get("type2_slots") == 32
            and full.get("slot_count") == 64,
            "total_slots": gate_values.get("total_slots"),
            "type1_l_slots": gate_values.get("type1_slots"),
            "type2_r_slots": gate_values.get("type2_slots"),
            "full_trajectory_rows": len(full.get("trajectory", [])),
        },
        "slot_coordinate_consistency_verdicts": {
            "present": consistency.get("all_rows_pass") is True and len(consistency.get("rows", [])) == 64,
            "row_count": len(consistency.get("rows", [])),
            "bad_row_count": consistency.get("bad_row_count"),
            "all_rows_pass": consistency.get("all_rows_pass"),
        },
        "l_vs_r_full_run_comparison": {
            "present": comparison.get("same_initial_state") is True
            and comparison.get("chirality_difference_detected") is True,
            "same_initial_state": comparison.get("same_initial_state"),
            "final_state_l2": comparison.get("final_state_l2"),
            "chirality_difference_detected": comparison.get("chirality_difference_detected"),
        },
        "shuffled_schedule_control": {
            "present": controls.get("shuffled_schedule_control", {}).get("pass") is True,
            **controls.get("shuffled_schedule_control", {}),
        },
        "truncated_schedule_boundary": {
            "present": controls.get("truncated_schedule_boundary", {}).get("pass") is True,
            **controls.get("truncated_schedule_boundary", {}),
        },
        "bit_coordinate_erasure_control": {
            "present": controls.get("bit_coordinate_erasure_control", {}).get("pass") is True,
            **controls.get("bit_coordinate_erasure_control", {}),
        },
    }
    summary["present_absent"] = {
        name: "present" if row.get("present") else "absent"
        for name, row in summary.items()
        if isinstance(row, dict) and "present" in row
    }
    summary["all_required_present"] = all(value == "present" for value in summary["present_absent"].values())
    return summary


def build_result() -> dict[str, Any]:
    common.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    base = load_json(BASE_RESULT_PATH)
    legs = {engine: load_json(path) for engine, path in LEG_PATHS.items()}
    parity = {engine: compare_leg_to_base(base, leg) for engine, leg in legs.items()}
    summary = full_run_summary(base)
    gates = {
        "base_result_all_pass": base["all_pass"] is True,
        "classification_scratch": base["classification"] == common.CLASSIFICATION
        and all(leg["classification"] == common.CLASSIFICATION for leg in legs.values()),
        "promotion_blocked": base["promotion_allowed"] is False
        and all(leg["promotion_allowed"] is False for leg in legs.values()),
        "formal_admission_blocked": base["formal_admission_allowed"] is False
        and all(leg["formal_admission_allowed"] is False for leg in legs.values()),
        "legs_all_pass": all(leg["all_pass"] is True for leg in legs.values()),
        "all_values_match_base": all(all(checks.values()) for checks in parity.values()),
        "full_run_summary_complete": summary["all_required_present"] is True,
    }
    engine_values = {
        "julia": float(legs["julia"]["counts"]["unique_coordinate_count"]),
        "jax": float(legs["jax"]["counts"]["unique_coordinate_count"]),
    }
    extra_fields = {
        "all_pass": all(gates.values()),
        "source_path": common.rel(SOURCE_PATH),
        "source_sha256": common.sha256_file(SOURCE_PATH),
        "result_path": common.rel(RESULT_PATH),
        "base_result_path": common.rel(BASE_RESULT_PATH),
        "base_result_sha256": common.sha256_file(BASE_RESULT_PATH),
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "standard_schema_mode": "julia_canon_plus_jax_diagnostic_pytorch_omitted",
        "builder_gates": gates,
        "engine_value_parity": parity,
        "result_values_unchanged": True,
        "full_run_summary_check": summary,
        "boundary": {
            "classification": common.CLASSIFICATION,
            "claim_ceiling": base["claim_ceiling"],
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "realization_relative_only": True,
            "source_admitted_substage_convention": False,
            "match_lane_claim": False,
            "basin_claim": False,
            "not_qit_admission": True,
            "not_axis_admission": True,
            "pytorch_omission": "honest omission: no tensor/autograd/graph PyTorch claim path in this realization-relative finite schedule packet",
        },
        "allowed_claims": base["allowed_claims"],
        "disallowed_claims": base["disallowed_claims"],
        "coordinate_consistency": base["coordinate_consistency"],
        "type1_l_vs_type2_r_comparison": base["type1_l_vs_type2_r_comparison"],
        "controls": base["controls"],
        "gate_values": base["gate_values"],
        "TOOL_INTENT_MATRIX": {
            "build_three_engine_envelope": {
                "reason": "load-bearing standard envelope construction; this packet does not hand-roll three_engine_sim_result_v1",
                "helper_path": "scripts/build_three_engine_envelope.py",
                "load_bearing": True,
            },
            "julia": {
                "mode": "exact Julia mirror of the slot-coordinate consistency rows and schedule cardinalities",
                "load_bearing": ["julia_gf4_stdlib"],
                "boundary": "reference lane only; no Julia package promotion beyond exact finite schedule checking",
            },
            "jax": {
                "mode": "SymPy exact-cardinality diagnostic mirror for the JAX/workhorse envelope lane",
                "load_bearing": ["sympy"],
                "boundary": "diagnostic parity lane only; no vectorized dynamics or JAX-array strength claim",
            },
            "pytorch": {
                "mode": "omitted",
                "load_bearing": [],
                "boundary": "honestly omitted because this packet has no tensor/autograd/graph claim path",
            },
        },
        "TOOL_MANIFEST": {
            "base": base["TOOL_MANIFEST"],
            "julia": legs["julia"]["TOOL_MANIFEST"],
            "jax": legs["jax"]["TOOL_MANIFEST"],
            "build_three_engine_envelope": "load_bearing canonical envelope construction",
        },
        "TOOL_INTEGRATION_DEPTH": {
            "base": base["TOOL_INTEGRATION_DEPTH"],
            "julia": legs["julia"]["TOOL_INTEGRATION_DEPTH"],
            "jax": legs["jax"]["TOOL_INTEGRATION_DEPTH"],
            "build_three_engine_envelope": "load_bearing",
        },
        "validator_commands": [
            f"/opt/homebrew/bin/julia --startup-file=no {common.rel(common.SIM_DIR / (SIM_ID + '_julia.jl'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(common.SIM_DIR / (SIM_ID + '_jax.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(SOURCE_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py {common.rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(common.SIM_DIR / ('validate_' + SIM_ID + '.py'))}",
        ],
        "runtime_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
    }
    envelope = helper.build_envelope(
        sim_id=SIM_ID,
        lanes={engine: engine_lane(leg, LEG_PATHS[engine]) for engine, leg in legs.items()},
        mode="julia_canon_plus_jax_diagnostic_pytorch_omitted",
        claim_path_tools=["julia_gf4_stdlib", "sympy", "build_three_engine_envelope"],
        crossover_proofs=base["crossover_proofs"],
        divergence={
            "julia_authoritative": True,
            "metric": "unique_coordinate_count",
            "engine_values": engine_values,
            "max_divergence": max(engine_values.values()) - min(engine_values.values()),
        },
        classification=common.CLASSIFICATION,
        promotion_allowed=False,
        formal_admission_allowed=False,
        parent_lineage={
            "base_single_file_result": common.rel(BASE_RESULT_PATH),
            "authority": "contract-completion envelope repair; values unchanged",
        },
        omitted_lanes={
            "pytorch": "honest omission: no tensor/autograd/graph PyTorch claim path in this realization-relative finite schedule packet",
        },
        stability_pairs=[
            ("base_result", common.sha256_file(BASE_RESULT_PATH)),
            ("julia_lane", common.sha256_file(LEG_PATHS["julia"])),
            ("jax_lane", common.sha256_file(LEG_PATHS["jax"])),
        ],
        generated_at=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        extra_fields=extra_fields,
    )
    common.write_json(RESULT_PATH, envelope)
    print(json.dumps({"ok": envelope["all_pass"], "result_path": common.rel(RESULT_PATH)}, sort_keys=True))
    return envelope


if __name__ == "__main__":
    raise SystemExit(0 if build_result()["all_pass"] else 1)
