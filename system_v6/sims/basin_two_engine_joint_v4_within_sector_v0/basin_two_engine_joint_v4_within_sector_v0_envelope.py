#!/usr/bin/env python3
"""Envelope builder for basin_two_engine_joint_v4_within_sector_v0."""

from __future__ import annotations

import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

from basin_two_engine_joint_v4_within_sector_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SIM_ID,
    build_flux_payload,
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
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
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
    "json": {"tried": True, "used": True, "reason": "supportive deterministic leg-result loading"},
}
TOOL_INTEGRATION_DEPTH = {"build_three_engine_envelope.py": "supportive", "json": "supportive"}

TOOL_INTENT_MATRIX = {
    "claim_classes": [
        "within_sector_terminal_structure",
        "in_class_flux_flipping",
        "conserved_flux_sector_control",
        "projection_and_symmetry_orbit_discriminator",
        "computed_count_identity_smt",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "independent Graphs.SimpleDiGraph SCC and terminal-count recomputation for registered flip-law rows",
            "Z3": "Julia-side computed-count identity UNSAT with flipped expected-count SAT",
        },
        "jax": {
            "networkx": "workhorse SCC terminal-class cross-check for the conserved-sector control",
            "sympy": "exact integer checksum over measured realization-family counts",
            "z3": "computed-count identity UNSAT with flipped expected-count SAT",
            "cvc5": "independent computed-count identity UNSAT with flipped expected-count SAT",
        },
        "pytorch": {
            "torch.func": "batched torch transition image materialization for graph controls",
            "torch_geometric": "edge_index graph carrier for a registered flip-law transition relation",
            "sympy": "exact integer checksum over measured realization-family counts",
            "z3": "computed-count identity UNSAT with flipped expected-count SAT",
            "cvc5": "independent computed-count identity UNSAT with flipped expected-count SAT",
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
        "genuine_hit_counts": {engine: int(leg["genuine_hit_count"]) for engine, leg in legs.items()},
        "genuine_hit_count_agreement": len({int(leg["genuine_hit_count"]) for leg in legs.values()}) == 1,
        "joint_signature_sha256": {engine: leg.get("joint_signature_sha256") for engine, leg in legs.items()},
        "julia_independence_note": "Julia recomputes terminal counts through Graphs.jl/Z3.jl; Python payload carries the richer projection/symmetry lattice.",
        "payload_honest_outcome": payload["prediction_adjudication"]["honest_outcome"],
    }


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {engine: float(leg["genuine_hit_count"]) for engine, leg in legs.items()}
    julia_value = values["julia"]
    return {
        "julia_authoritative": True,
        "metric": "genuine_hit_count",
        "engine_values": values,
        "max_divergence": max(abs(value - julia_value) for value in values.values()),
    }


def build_result() -> dict[str, Any]:
    legs = {engine: load(path) for engine, path in LEG_PATHS.items()}
    payload = build_flux_payload()
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
        "engine_primary_count_agreement": comparison["primary_terminal_count_agreement"] is True,
        "engine_genuine_hit_count_agreement": comparison["genuine_hit_count_agreement"] is True,
        "divergence_zero": div["max_divergence"] == 0.0,
        "payload_gates_pass": payload["all_pass"] is True,
        "no_builder_audit_verdict": builder_audit_boundary_ok(SOURCE_PATH.parent / "audit_verdict.md"),
        "z3_cvc5_count_identity_unsat": proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] == "unsat",
        "flipped_controls_sat": proofs["z3"]["flipped_control_verdict"] == proofs["cvc5"]["flipped_control_verdict"] == "sat",
        "julia_z3_count_identity_unsat": proofs["julia_z3"]["verdict"] == "unsat",
        "julia_z3_flipped_sat": proofs["julia_z3"]["flipped_control_verdict"] == "sat",
        "one_to_one_tool_calls": all(leg.get("one_to_one_tool_calls", {}).get("pass") is True for leg in legs.values()),
    }
    all_pass = bool(all(gates.values()))
    extra_fields = {
        "ceiling": CLASSIFICATION,
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "standard_schema_mode": "all_three_full_sims",
        "builder_output_only": True,
        "no_builder_audit_verdict": True,
        "tool_intent": TOOL_INTENT_MATRIX,
        "TOOL_INTENT_MATRIX": TOOL_INTENT_MATRIX,
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
        "registered_flip_family": payload["registered_flip_family"],
        "realization_family": payload["realization_family"],
        "controls": payload["controls"],
        "evidence_sections": payload["evidence_sections"],
        "prediction_adjudication": payload["prediction_adjudication"],
        "engine_comparison": comparison,
        "runtime_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "legs": {engine: leg.get("package_versions", {}) for engine, leg in legs.items()},
        },
        "build_gates": gates,
        "payload_build_gates": payload["build_gates"],
        "result_integrity": {
            "payload_stability_sha256": payload["result_stability_sha256"],
            "leg_result_sha256": {engine: sha256_file(path) for engine, path in LEG_PATHS.items()},
        },
        "crossover_proofs": proofs,
        "divergence": div,
        "divergence_log": [
            {
                "metric": "genuine_hit_count",
                "values": div["engine_values"],
                "max_divergence": div["max_divergence"],
                "status": "agree" if div["max_divergence"] == 0.0 else "diverged",
            }
        ],
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
        omitted_lanes={},
        parent_lineage={"packet_parent_lineage": "see parent_lineage field in extra_fields"},
        expected_lanes=("julia", "jax", "pytorch"),
        stability_pairs=[
            ("realization_family", stable_sha256(payload["realization_family"])),
            ("controls", stable_sha256(payload["controls"])),
            ("adjudication", stable_sha256(payload["prediction_adjudication"])),
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
