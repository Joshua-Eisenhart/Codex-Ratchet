#!/usr/bin/env python3
"""Envelope builder for basin_two_engine_joint_v0."""

from __future__ import annotations

import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

from basin_two_engine_joint_v0_common import (
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


def merge_tool_manifest(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {engine: leg.get("TOOL_MANIFEST", {}) for engine, leg in legs.items()}


def merge_tool_depth(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {engine: leg.get("TOOL_INTEGRATION_DEPTH", {}) for engine, leg in legs.items()}


def compare_engines(legs: dict[str, dict[str, Any]], payload: dict[str, Any]) -> dict[str, Any]:
    subsub_counts = {
        "julia": legs["julia"]["computed_subsubbasin_count"],
        "jax": legs["jax"]["joint_payload"]["prediction_adjudication"]["computed_subsubbasin_count"],
        "pytorch": legs["pytorch"]["joint_payload"]["prediction_adjudication"]["computed_subsubbasin_count"],
    }
    terminal_counts = {
        "julia": {
            row: legs["julia"]["joint_graphs"][row]["terminal_class_count"]
            for row in ("both", "synchronous", "l_only", "r_only")
        },
        "jax": {
            "both": payload["hierarchy"]["basins"]["both"]["terminal_class_count"],
            "synchronous": payload["hierarchy"]["subbasins"]["synchronous"]["terminal_class_count"],
            "l_only": payload["hierarchy"]["subbasins"]["l_only"]["terminal_class_count"],
            "r_only": payload["hierarchy"]["subbasins"]["r_only"]["terminal_class_count"],
        },
        "pytorch": {
            "both": legs["pytorch"]["joint_payload"]["hierarchy"]["basins"]["both"]["terminal_class_count"],
            "synchronous": legs["pytorch"]["joint_payload"]["hierarchy"]["subbasins"]["synchronous"]["terminal_class_count"],
            "l_only": legs["pytorch"]["joint_payload"]["hierarchy"]["subbasins"]["l_only"]["terminal_class_count"],
            "r_only": legs["pytorch"]["joint_payload"]["hierarchy"]["subbasins"]["r_only"]["terminal_class_count"],
        },
    }
    return {
        "subsubbasin_counts": subsub_counts,
        "subsubbasin_count_agreement": len(set(subsub_counts.values())) == 1,
        "terminal_class_counts": terminal_counts,
        "terminal_count_agreement": len({json.dumps(v, sort_keys=True) for v in terminal_counts.values()}) == 1,
        "joint_signature_sha256": {engine: leg.get("joint_signature_sha256") for engine, leg in legs.items()},
        "julia_note": "Julia recomputes graph/SCC/count with Graphs.jl and Z3.jl; Python legs carry the full shared hierarchy payload.",
    }


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {
        "julia": float(legs["julia"]["computed_subsubbasin_count"]),
        "jax": float(legs["jax"]["joint_payload"]["prediction_adjudication"]["computed_subsubbasin_count"]),
        "pytorch": float(legs["pytorch"]["joint_payload"]["prediction_adjudication"]["computed_subsubbasin_count"]),
    }
    return {
        "julia_authoritative": True,
        "metric": "computed_subsubbasin_count",
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
        "state_count_64": payload["joint_object"]["state_count"] == 64,
        "basin_terminal_class_count_1": payload["hierarchy"]["basins"]["both"]["terminal_class_count"] == 1,
        "sync_subbasin_terminal_class_count_8": payload["hierarchy"]["subbasins"]["synchronous"]["terminal_class_count"] == 8,
        "l_subbasin_terminal_class_count_8": payload["hierarchy"]["subbasins"]["l_only"]["terminal_class_count"] == 8,
        "r_subbasin_terminal_class_count_8": payload["hierarchy"]["subbasins"]["r_only"]["terminal_class_count"] == 8,
        "subsubbasin_count_64": payload["hierarchy"]["subsubbasins"]["earned_count"] == 64,
        "subsubbasin_classes_singletons": payload["hierarchy"]["subsubbasins"]["class_size_multiset"] == [1] * 64,
        "label_free_signature": payload["signature_discipline"]["label_free"] is True,
        "order_blind_signature": payload["signature_discipline"]["order_blind"] is True,
        "no_forbidden_signature_components": payload["signature_discipline"]["forbidden_components_present"] == [],
        "decode_test_passed": payload["controls"]["decode_test"]["passed"] is True,
        "label_permutation_invariant": payload["controls"]["label_permutation"]["count_invariant"] is True,
        "similarity_contrast_fired": payload["controls"]["similarity_cluster_contrast"]["fired"] is True,
        "root_off_fired": payload["controls"]["root_off"]["fired"] is True,
        "single_engine_marginals_8_each": payload["controls"]["single_engine_marginals"]["l_terminal_count"] == 8
        and payload["controls"]["single_engine_marginals"]["r_terminal_count"] == 8,
        "z3_cvc5_unsat": proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] == "unsat",
        "erased_flip_sat": proofs["z3"]["erased_flip_verdict"] == proofs["cvc5"]["erased_flip_verdict"] == "sat",
        "julia_z3_unsat": proofs["julia_z3"]["verdict"] == "unsat",
        "engine_count_agreement": comparison["subsubbasin_count_agreement"] is True,
        "engine_terminal_count_agreement": comparison["terminal_count_agreement"] is True,
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
            ),
            "strict_expected_command": (
                "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
                f"scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed {rel(RESULT_PATH)}"
            ),
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
        "joint_object": payload["joint_object"],
        "hierarchy": payload["hierarchy"],
        "prediction_adjudication": payload["prediction_adjudication"],
        "signature_discipline": payload["signature_discipline"],
        "lr_structure_rows": payload["lr_structure_rows"],
        "controls": payload["controls"],
        "secondary_carrier_grid_product_sample": payload["secondary_carrier_grid_product_sample"],
        "engine_comparison": comparison,
        "runtime_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "legs": {engine: leg.get("package_versions", {}) for engine, leg in legs.items()},
        },
        "build_gates": gates,
        "child_agent_receipts": [
            {
                "agent_id": "019eb8b6-0569-7ec1-8d1b-cfa8c8bfa8e8",
                "role": "source_archaeology",
                "status": "completed",
                "accepted": True,
            },
            {
                "agent_id": "019eb8b6-23ed-7c53-9b76-18ccf881125f",
                "role": "matrix64_and_two_engine_correspondence",
                "status": "completed",
                "accepted": True,
            },
            {
                "agent_id": "019eb8b6-3a9f-7431-8fac-c9d85e933e57",
                "role": "validator_and_envelope_pattern",
                "status": "completed",
                "accepted": True,
            },
        ],
        "result_integrity": {
            "leg_result_sha256": {engine: sha256_file(path) for engine, path in LEG_PATHS.items()},
            "build_helper_path": rel(HELPER_PATH),
            "build_helper_sha256": sha256_file(HELPER_PATH),
            "joint_payload_stability_sha256": payload["result_stability_sha256"],
            "envelope_content_without_result_hash_sha256": stable_sha256(
                {
                    "joint_object": payload["joint_object"],
                    "hierarchy_signatures": {
                        "both": payload["hierarchy"]["basins"]["both"]["partition_signature"],
                        "synchronous": payload["hierarchy"]["subbasins"]["synchronous"]["partition_signature"],
                        "l_only": payload["hierarchy"]["subbasins"]["l_only"]["partition_signature"],
                        "r_only": payload["hierarchy"]["subbasins"]["r_only"]["partition_signature"],
                    },
                    "subsubbasins": {
                        "earned_count": payload["hierarchy"]["subsubbasins"]["earned_count"],
                        "class_size_multiset": payload["hierarchy"]["subsubbasins"]["class_size_multiset"],
                    },
                    "proofs": proofs,
                    "controls": payload["controls"],
                }
            ),
        },
    }
    envelope = helper.build_envelope(
        sim_id=SIM_ID,
        lanes={engine: engine_lane(leg, LEG_PATHS[engine]) for engine, leg in legs.items()},
        mode="joint_stage_basin_hierarchy_scratch_diagnostic",
        claim_path_tools=["Graphs", "Z3", "networkx", "sympy", "z3", "cvc5", "torch.func", "torch_geometric"],
        crossover_proofs=proofs,
        divergence=div,
        classification=CLASSIFICATION,
        promotion_allowed=PROMOTION_ALLOWED,
        formal_admission_allowed=FORMAL_ADMISSION_ALLOWED,
        parent_lineage=parent_lineage(),
        expected_lanes=("julia", "jax", "pytorch"),
        stability_pairs=[
            ("joint_payload", payload["result_stability_sha256"]),
            ("engine_count_comparison", stable_sha256(comparison)),
        ],
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
