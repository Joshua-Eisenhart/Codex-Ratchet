#!/usr/bin/env python3
"""Envelope builder for basin_two_engine_joint_v2."""

from __future__ import annotations

import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

from basin_two_engine_joint_v2_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SIM_ID,
    build_joint_payload,
    now_z,
    parent_lineage,
    rel,
    sha256_file,
    stable_sha256,
    write_json,
)


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
LEG_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
}

TOOL_MANIFEST = {
    "build_three_engine_envelope.py": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical envelope assembly helper",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive leg-result merge and deterministic payload write",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "build_three_engine_envelope.py": "supportive",
    "json": "supportive",
}

HELPER_PATH = ROOT / "scripts" / "build_three_engine_envelope.py"
spec = importlib.util.spec_from_file_location("build_three_engine_envelope", HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(helper)

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_lane(leg: dict[str, Any], result_path: Path) -> dict[str, Any]:
    observables = {
        package: f"{leg['engine']} load-bearing observable recorded in capability/tool receipts"
        for package in leg.get("aligned_packages_load_bearing", [])
    }
    return {
        "source_path": leg["source_path"],
        "result_path": rel(result_path),
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "package_observables": observables,
        "claim_path_tools": leg.get("claim_path_tools", []),
        "package_versions": leg.get("package_versions", {}),
        "capability_receipts": leg.get("capability_receipts", []),
        "tool_calls": leg.get("tool_calls", []),
        "one_to_one_tool_calls": leg.get("one_to_one_tool_calls", {}),
    }


def merge_tool_manifest(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {engine: leg.get("TOOL_MANIFEST", {}) for engine, leg in legs.items()}


def merge_tool_depth(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {engine: leg.get("TOOL_INTEGRATION_DEPTH", {}) for engine, leg in legs.items()}


def compare_engines(legs: dict[str, dict[str, Any]], payload: dict[str, Any]) -> dict[str, Any]:
    primary_64_counts = {
        "julia": legs["julia"]["primary_64_level_count"],
        "jax": legs["jax"]["primary_64_level_count"],
        "pytorch": legs["pytorch"]["primary_64_level_count"],
    }
    control_counts = {
        "julia": legs["julia"]["control_terminal_class_count"],
        "jax": legs["jax"]["control_terminal_class_count"],
        "pytorch": legs["pytorch"]["control_terminal_class_count"],
    }
    selected_terminal_counts = {
        "payload": {
            row: payload["hierarchy"]["primary_rows"][row]["terminal_class_count"]
            for row in (
                "source_sync_full_tick",
                "source_l_only_full_tick",
                "source_r_only_full_tick",
                "source_async_lr_union_full_tick",
                "source_all_interleavings_full_tick",
            )
        },
        "julia": {
            row: legs["julia"]["primary_terminal_counts"][row]
            for row in (
                "source_sync_full_tick",
                "source_l_only_full_tick",
                "source_r_only_full_tick",
                "source_async_lr_union_full_tick",
                "source_all_interleavings_full_tick",
            )
        },
    }
    return {
        "primary_64_level_counts": primary_64_counts,
        "primary_64_level_count_agreement": len(set(primary_64_counts.values())) == 1,
        "control_terminal_counts": control_counts,
        "control_terminal_count_agreement": len(set(control_counts.values())) == 1,
        "selected_terminal_counts": selected_terminal_counts,
        "selected_terminal_count_agreement": selected_terminal_counts["payload"] == selected_terminal_counts["julia"],
        "joint_signature_sha256": {engine: leg.get("joint_signature_sha256") for engine, leg in legs.items()},
        "julia_note": "Julia recomputes graph/SCC/count with Graphs.jl and Z3.jl; Python payload carries full may/must and quotient rows.",
    }


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {
        "julia": float(legs["julia"]["primary_64_level_count"]),
        "jax": float(legs["jax"]["primary_64_level_count"]),
        "pytorch": float(legs["pytorch"]["primary_64_level_count"]),
    }
    return {
        "julia_authoritative": True,
        "metric": "primary_64_level_count",
        "engine_values": values,
        "max_divergence": max(abs(value - values["julia"]) for value in values.values()),
    }


def build_result() -> dict[str, Any]:
    legs = {engine: load(path) for engine, path in LEG_PATHS.items()}
    payload = build_joint_payload()
    comparison = compare_engines(legs, payload)
    div = divergence(legs)
    proofs = {
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": payload["crossover_proofs"]["z3"]["verdict"],
            "erased_flip_verdict": payload["crossover_proofs"]["z3"]["erased_flip_verdict"],
            "proof_row": payload["crossover_proofs"]["z3"]["proof_row"],
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": payload["crossover_proofs"]["cvc5"]["verdict"],
            "erased_flip_verdict": payload["crossover_proofs"]["cvc5"]["erased_flip_verdict"],
            "proof_row": payload["crossover_proofs"]["cvc5"]["proof_row"],
        },
        "julia_z3": legs["julia"]["crossover_proofs"]["julia_z3"],
        "pytorch_z3": legs["pytorch"]["crossover_proofs"]["z3"],
        "pytorch_cvc5": legs["pytorch"]["crossover_proofs"]["cvc5"],
    }
    gates = {
        "classification_scratch": CLASSIFICATION == "scratch_diagnostic",
        "promotion_blocked": PROMOTION_ALLOWED is False,
        "formal_admission_blocked": FORMAL_ADMISSION_ALLOWED is False,
        "joint_state_count_1024": payload["joint_object"]["joint_state_count"] == 1024,
        "per_engine_state_count_32": payload["joint_object"]["per_engine_state_count"] == 32,
        "no_primary_64_level": payload["prediction_adjudication"]["primary_64_level_count"] == 0,
        "source_sync_count_32": payload["hierarchy"]["primary_rows"]["source_sync_full_tick"]["terminal_class_count"] == 32,
        "source_l_only_count_32": payload["hierarchy"]["primary_rows"]["source_l_only_full_tick"]["terminal_class_count"] == 32,
        "source_r_only_count_32": payload["hierarchy"]["primary_rows"]["source_r_only_full_tick"]["terminal_class_count"] == 32,
        "source_async_lr_union_count_1": payload["hierarchy"]["primary_rows"]["source_async_lr_union_full_tick"]["terminal_class_count"] == 1,
        "v1_baseline_reproduces_64": payload["controls"]["v1_replication"]["coarse_8x8_reproduces_v1_64"] is True,
        "v1_baseline_not_primary": payload["controls"]["v1_replication"]["accepted_as_primary_evidence"] is False,
        "dissipative_merge_less_than_1024": payload["controls"]["dissipative_merge"]["terminal_class_count_less_than_1024"] is True,
        "label_permutation_pass": payload["controls"]["label_permutation"]["all_pass"] is True,
        "root_off_fired": payload["controls"]["root_off"]["fired"] is True,
        "decode_test_passed": payload["controls"]["decode_test"]["passed"] is True,
        "z3_cvc5_unsat": proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] == "unsat",
        "erased_flip_sat": proofs["z3"]["erased_flip_verdict"] == proofs["cvc5"]["erased_flip_verdict"] == "sat",
        "julia_z3_unsat": proofs["julia_z3"]["verdict"] == "unsat",
        "engine_primary_count_agreement": comparison["primary_64_level_count_agreement"] is True,
        "engine_control_count_agreement": comparison["control_terminal_count_agreement"] is True,
        "one_to_one_tool_calls": all(leg.get("one_to_one_tool_calls", {}).get("pass") is True for leg in legs.values()),
        "packet_audit_verdict_absent": builder_audit_boundary_ok(SOURCE_PATH.parent / "audit_verdict.md"),
    }
    all_pass = bool(
        payload["all_pass"] is True
        and all(leg.get("all_pass") is True for leg in legs.values())
        and div["max_divergence"] == 0.0
        and all(gates.values())
    )
    extra_fields = {
        "ceiling": CLASSIFICATION,
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "standard_schema_mode": "all_three_full_sims",
        "source_backed_validation": {
            "expected_command": (
                "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
                f"scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed {rel(RESULT_PATH)}"
            )
        },
        "TOOL_MANIFEST": {"envelope": TOOL_MANIFEST, "legs": merge_tool_manifest(legs)},
        "TOOL_INTEGRATION_DEPTH": {"envelope": TOOL_INTEGRATION_DEPTH, "legs": merge_tool_depth(legs)},
        "capability_receipts": {engine: leg.get("capability_receipts", []) for engine, leg in legs.items()},
        "tool_calls": {engine: leg.get("tool_calls", []) for engine, leg in legs.items()},
        "one_to_one_tool_calls": {
            "pass": all(leg.get("one_to_one_tool_calls", {}).get("pass") is True for leg in legs.values()),
            "by_engine": {engine: leg.get("one_to_one_tool_calls", {}) for engine, leg in legs.items()},
        },
        "parent_lineage": parent_lineage(),
        "seed_ledger": payload["seed_ledger"],
        "substage_convention": payload["substage_convention"],
        "joint_object": payload["joint_object"],
        "cycle_structure_analysis": payload["cycle_structure_analysis"],
        "hierarchy": payload["hierarchy"],
        "prediction_adjudication": payload["prediction_adjudication"],
        "controls": payload["controls"],
        "engine_comparison": comparison,
        "runtime_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "legs": {engine: leg.get("package_versions", {}) for engine, leg in legs.items()},
        },
        "build_gates": gates,
        "child_agent_receipts": [
            {
                "agent_id": "019eb8d2-794f-7293-9c6c-f718965d557b",
                "role": "v1_failure_archaeology",
                "status": "completed",
                "accepted": True,
            },
            {
                "agent_id": "019eb8d2-9806-74c3-aec6-1c934b3938dd",
                "role": "source_semantics",
                "status": "completed",
                "accepted": True,
            },
            {
                "agent_id": "019eb8d2-b1a2-70d3-a13a-c279c48e1fec",
                "role": "validator_envelope_conventions",
                "status": "completed",
                "accepted": True,
            },
        ],
        "result_integrity": {
            "leg_result_sha256": {engine: sha256_file(path) for engine, path in LEG_PATHS.items()},
            "build_helper_path": rel(HELPER_PATH),
            "build_helper_sha256": sha256_file(HELPER_PATH),
            "joint_payload_stability_sha256": payload["result_stability_sha256"],
        },
    }
    envelope = helper.build_envelope(
        sim_id=SIM_ID,
        lanes={engine: engine_lane(leg, LEG_PATHS[engine]) for engine, leg in legs.items()},
        mode="builder_output_only_1024_joint_dynamics",
        claim_path_tools=["Graphs", "Z3", "networkx", "sympy", "z3", "cvc5", "torch.func", "torch_geometric"],
        crossover_proofs=proofs,
        divergence=div,
        classification=CLASSIFICATION,
        promotion_allowed=PROMOTION_ALLOWED,
        formal_admission_allowed=FORMAL_ADMISSION_ALLOWED,
        parent_lineage={"packet_parent_lineage": "see parent_lineage field in extra_fields"},
        stability_pairs=[("joint_payload", payload["result_stability_sha256"])],
        generated_at=now_z(),
        extra_fields=extra_fields,
    )
    return envelope


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
