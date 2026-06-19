#!/usr/bin/env python3
"""Envelope builder for basin_two_engine_joint_v3_convention_sweep."""

from __future__ import annotations

import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

from basin_two_engine_joint_v3_convention_sweep_common import (
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

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402

TOOL_MANIFEST = {
    "build_three_engine_envelope.py": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical three-engine envelope assembly helper",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive leg-result loading and deterministic envelope write",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "build_three_engine_envelope.py": "supportive",
    "json": "supportive",
}

TOOL_INTENT = {
    "claim_classes": [
        "convention_relative_terminal_class_count",
        "finite_transition_partition",
        "order_shuffled_negative_control",
        "computed_count_identity_smt",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "independent Graphs.SimpleDiGraph SCC and terminal-count recomputation for every convention row",
            "Z3": "Julia-side computed terminal-count identity UNSAT with flipped expected-count SAT",
        },
        "jax": {
            "networkx": "workhorse SCC, terminal class, may/must, quotient, and Morse partition machinery",
            "sympy": "exact integer checksum for label-free terminal-count signatures",
            "z3": "computed terminal-count identity UNSAT with flipped expected-count SAT",
            "cvc5": "independent computed terminal-count identity UNSAT with flipped expected-count SAT",
        },
        "pytorch": {
            "torch.func": "batched torch transition materialization for convention-row graph tensors",
            "torch_geometric": "edge_index graph carrier for convention-row transition relations",
            "sympy": "exact integer checksum for torch-side terminal-count signatures",
            "z3": "torch-side computed terminal-count identity UNSAT with flipped expected-count SAT",
            "cvc5": "independent torch-side computed terminal-count identity UNSAT with flipped expected-count SAT",
        },
    },
}


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
    }


def primary_counts(leg: dict[str, Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in leg.get("primary_terminal_counts", {}).items()}


def compare_engines(legs: dict[str, dict[str, Any]], payload: dict[str, Any]) -> dict[str, Any]:
    count_maps = {engine: primary_counts(leg) for engine, leg in legs.items()}
    jax_counts = count_maps["jax"]
    return {
        "primary_terminal_count_agreement": all(counts == jax_counts for counts in count_maps.values()),
        "source_valid_primary_64_level_counts": {
            engine: leg["source_valid_primary_64_level_count"] for engine, leg in legs.items()
        },
        "source_valid_primary_64_level_count_agreement": len(
            {leg["source_valid_primary_64_level_count"] for leg in legs.values()}
        )
        == 1,
        "joint_signature_sha256": {engine: leg.get("joint_signature_sha256") for engine, leg in legs.items()},
        "julia_independence_note": (
            "Julia recomputes every convention-row terminal count through Graphs.jl and Z3.jl; "
            "Python/JAX payload carries the full quotient and may/must lattice."
        ),
        "payload_count_result": payload["prediction_adjudication"]["count_result"],
    }


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {
        engine: float(leg["source_valid_primary_64_level_count"])
        for engine, leg in legs.items()
    }
    julia_value = values["julia"]
    return {
        "julia_authoritative": True,
        "metric": "source_valid_primary_64_level_count",
        "engine_values": values,
        "max_divergence": max(abs(value - julia_value) for value in values.values()),
    }


def build_result() -> dict[str, Any]:
    legs = {engine: load(path) for engine, path in LEG_PATHS.items()}
    payload = build_joint_payload()
    comparison = compare_engines(legs, payload)
    div = divergence(legs)
    proofs = {
        "z3": payload["crossover_proofs"]["z3"],
        "cvc5": payload["crossover_proofs"]["cvc5"],
        "julia_z3": legs["julia"]["crossover_proofs"]["julia_z3"],
        "pytorch_z3": legs["pytorch"]["crossover_proofs"]["z3"],
        "pytorch_cvc5": legs["pytorch"]["crossover_proofs"]["cvc5"],
    }
    gates = {
        "classification_scratch": CLASSIFICATION == "scratch_diagnostic",
        "promotion_blocked": PROMOTION_ALLOWED is False,
        "formal_admission_blocked": FORMAL_ADMISSION_ALLOWED is False,
        "all_legs_pass": all(leg.get("all_pass") is True for leg in legs.values()),
        "joint_state_count_1024": payload["joint_object"]["joint_state_count"] == 1024,
        "engine_primary_count_agreement": comparison["primary_terminal_count_agreement"] is True,
        "engine_source_valid_64_count_agreement": comparison["source_valid_primary_64_level_count_agreement"] is True,
        "label_permutation_pass": payload["build_gates"]["label_permutation_all_pass"] is True,
        "order_blind_rows_excluded": payload["build_gates"]["order_blind_rows_excluded"] is True,
        "v1_replication_fenced": payload["build_gates"]["v1_replication_fenced"] is True,
        "dissipative_controls_fenced": payload["build_gates"]["dissipative_controls_fenced"] is True,
        "z3_cvc5_count_identity_unsat": proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] == "unsat",
        "flipped_controls_sat": proofs["z3"]["flipped_control_verdict"] == proofs["cvc5"]["flipped_control_verdict"] == "sat",
        "julia_z3_count_identity_unsat": proofs["julia_z3"]["verdict"] == "unsat",
        "julia_z3_flipped_sat": proofs["julia_z3"]["flipped_control_verdict"] == "sat",
        "one_to_one_tool_calls": all(leg.get("one_to_one_tool_calls", {}).get("pass") is True for leg in legs.values()),
        "packet_audit_verdict_absent": builder_audit_boundary_ok(SOURCE_PATH.parent / "audit_verdict.md"),
    }
    all_pass = bool(payload["all_pass"] is True and div["max_divergence"] == 0.0 and all(gates.values()))
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
                f"scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed {rel(RESULT_PATH)}"
            ),
            "tool_intent_command": (
                "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
                f"scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent {rel(RESULT_PATH)}"
            ),
        },
        "TOOL_MANIFEST": {"envelope": TOOL_MANIFEST, "legs": {engine: leg.get("TOOL_MANIFEST", {}) for engine, leg in legs.items()}},
        "TOOL_INTEGRATION_DEPTH": {
            "envelope": TOOL_INTEGRATION_DEPTH,
            "legs": {engine: leg.get("TOOL_INTEGRATION_DEPTH", {}) for engine, leg in legs.items()},
        },
        "capability_receipts": {engine: leg.get("capability_receipts", []) for engine, leg in legs.items()},
        "tool_calls": {engine: leg.get("tool_calls", []) for engine, leg in legs.items()},
        "one_to_one_tool_calls": {
            "pass": all(leg.get("one_to_one_tool_calls", {}).get("pass") is True for leg in legs.values()),
            "by_engine": {engine: leg.get("one_to_one_tool_calls", {}) for engine, leg in legs.items()},
        },
        "parent_lineage": parent_lineage(),
        "seed_ledger": payload["seed_ledger"],
        "joint_object": payload["joint_object"],
        "convention_variants": payload["convention_variants"],
        "hierarchy": payload["hierarchy"],
        "prediction_adjudication": payload["prediction_adjudication"],
        "cross_row_comparison": payload["cross_row_comparison"],
        "controls": payload["controls"],
        "evidence_sections": payload["evidence_sections"],
        "engine_comparison": comparison,
        "runtime_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "legs": {engine: leg.get("package_versions", {}) for engine, leg in legs.items()},
        },
        "build_gates": gates,
        "result_integrity": {
            "leg_result_sha256": {engine: sha256_file(path) for engine, path in LEG_PATHS.items()},
            "build_helper_path": rel(HELPER_PATH),
            "build_helper_sha256": sha256_file(HELPER_PATH),
            "joint_payload_stability_sha256": payload["result_stability_sha256"],
            "envelope_content_without_result_hash_sha256": stable_sha256(
                {
                    "prediction_adjudication": payload["prediction_adjudication"],
                    "comparison": comparison,
                    "build_gates": gates,
                }
            ),
        },
    }
    return helper.build_envelope(
        sim_id=SIM_ID,
        lanes={engine: engine_lane(leg, LEG_PATHS[engine]) for engine, leg in legs.items()},
        mode="all_three_full_sims",
        claim_path_tools=["Graphs", "Z3", "networkx", "sympy", "z3", "cvc5", "torch.func", "torch_geometric"],
        crossover_proofs=proofs,
        divergence=div,
        classification=CLASSIFICATION,
        promotion_allowed=PROMOTION_ALLOWED,
        formal_admission_allowed=FORMAL_ADMISSION_ALLOWED,
        parent_lineage={"packet_parent_lineage": "see parent_lineage field in extra_fields"},
        expected_lanes=("julia", "jax", "pytorch"),
        stability_pairs=[
            ("prediction_adjudication", stable_sha256(payload["prediction_adjudication"])),
            ("cross_row_comparison", stable_sha256(payload["cross_row_comparison"])),
            ("controls", stable_sha256(payload["controls"])),
        ],
        generated_at=now_z(),
        extra_fields=extra_fields,
    )


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
