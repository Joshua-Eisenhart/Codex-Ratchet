#!/usr/bin/env python3
"""Controller envelope for s8_local_information_table_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from s8_local_information_table_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PACKET,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SIM_ID,
    build_packet_payload,
    parent_lineage,
    rel,
    sha256_file,
    stable_hash,
    write_json,
)


sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402
from build_three_engine_envelope import build_envelope  # noqa: E402


SOURCE = Path(__file__).resolve()
RESULT = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
SPEC = PACKET / f"{SIM_ID}_envelope_spec.json"
ENGINES = ("julia", "jax", "pytorch")
TOL = 1.0e-10


def load_leg(engine: str) -> dict[str, Any]:
    return json.loads((RESULT_DIR / f"{SIM_ID}_{engine}_results.json").read_text(encoding="utf-8"))


def lane_record(leg: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_path": leg["source_path"],
        "result_path": leg["result_path"],
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "package_observables": leg["package_observables"],
        "role_id": leg["role_id"],
        "all_pass": leg["all_pass"],
        "claim_path_tools": leg["claim_path_tools"],
        "tool_calls": leg["tool_calls"],
    }


def shared_engine_values(legs: dict[str, dict[str, Any]]) -> tuple[dict[str, dict[str, float]], float, list[str]]:
    raw = {engine: {str(k): float(v) for k, v in legs[engine]["engine_values"].items()} for engine in ENGINES}
    shared_keys = sorted(set.intersection(*(set(values) for values in raw.values())))
    values = {engine: {key: raw[engine][key] for key in shared_keys} for engine in ENGINES}
    max_divergence = 0.0
    for key in shared_keys:
        row = [values[engine][key] for engine in ENGINES]
        max_divergence = max(max_divergence, max(row) - min(row))
    return values, max_divergence, shared_keys


def combine_tool_manifest(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "build_three_engine_envelope": {
            "tried": True,
            "used": True,
            "reason": "load-bearing standard envelope assembly through scripts/build_three_engine_envelope.py",
        }
    }
    for engine, leg in legs.items():
        for tool, entry in leg.get("TOOL_MANIFEST", {}).items():
            manifest[f"{engine}:{tool}"] = entry
    return manifest


def combine_tool_depth(legs: dict[str, dict[str, Any]]) -> dict[str, str]:
    depth = {"build_three_engine_envelope": "load_bearing"}
    for engine, leg in legs.items():
        for tool, value in leg.get("TOOL_INTEGRATION_DEPTH", {}).items():
            depth[f"{engine}:{tool}"] = str(value)
    return depth


def build_spec() -> dict[str, Any]:
    legs = {engine: load_leg(engine) for engine in ENGINES}
    packet = build_packet_payload("controller")
    engine_values, max_divergence, shared_keys = shared_engine_values(legs)
    z3 = legs["jax"]["crossover_proofs"]["z3"]
    cvc5 = legs["jax"]["crossover_proofs"]["cvc5"]
    julia_z3 = legs["julia"]["crossover_proofs"]["julia_z3"]
    no_audit = builder_audit_boundary_ok(PACKET / "audit_verdict.md")
    all_pass = bool(
        packet["all_pass"]
        and no_audit
        and all(legs[engine]["all_pass"] for engine in ENGINES)
        and max_divergence <= TOL
        and z3["verdict"] == cvc5["verdict"] == julia_z3["verdict"] == "unsat"
        and z3["perturbed_construction_path_verdict"] == "sat"
        and cvc5["perturbed_construction_path_verdict"] == "sat"
        and julia_z3["perturbed_construction_path_verdict"] == "sat"
    )
    tool_matrix = {engine: legs[engine]["package_observables"] for engine in ENGINES}
    extra_fields = {
        "schema": f"{SIM_ID}_envelope_v1",
        "source_path": rel(SOURCE),
        "source_sha256": sha256_file(SOURCE),
        "result_path": rel(RESULT),
        "spec_path": rel(SPEC),
        "all_pass": all_pass,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "object_quote": packet["object_quote"],
        "claim_ceiling": packet["claim_ceiling"],
        "local_information_table": packet["local_information_table"],
        "continuity_anchors": packet["continuity_anchors"],
        "controls": packet["controls"],
        "builder_gates": packet["builder_gates"],
        "no_builder_audit_verdict": no_audit,
        "no_builder_audit_verdict_envelope_gate": no_audit,
        "shared_engine_scalar_keys": shared_keys,
        "TOOL_INTENT_MATRIX": tool_matrix,
        "tool_intent": {
            "claim_classes": [
                "S8-local typed information table",
                "continuity anchors",
                "structural failure controls",
                "SMT identity flips",
            ],
            "engine_tool_intent": tool_matrix,
        },
        "TOOL_MANIFEST": combine_tool_manifest(legs),
        "TOOL_INTEGRATION_DEPTH": combine_tool_depth(legs),
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": list(ENGINES),
            "reads_peer_result": {engine: legs[engine]["reads_peer_result"] for engine in ENGINES},
        },
        "tool_calls": legs["julia"]["tool_calls"] + legs["jax"]["tool_calls"] + legs["pytorch"]["tool_calls"],
        "validator_expected_commands": [
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/s8_local_information_table_v0/s8_local_information_table_v0_jax.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/s8_local_information_table_v0/s8_local_information_table_v0_pytorch.py",
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/s8_local_information_table_v0/s8_local_information_table_v0_julia.jl",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/s8_local_information_table_v0/write_envelope_spec.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/s8_local_information_table_v0/s8_local_information_table_v0_envelope.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/s8_local_information_table_v0/validate_s8_local_information_table_v0.py --phase builder",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/s8_local_information_table_v0/results/s8_local_information_table_v0_envelope_results.json",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/s8_local_information_table_v0/tests",
        ],
        "table_hash": stable_hash(packet["local_information_table"]),
        "controls_hash": stable_hash(packet["controls"]),
    }
    return {
        "sim_id": SIM_ID,
        "lanes": {engine: lane_record(legs[engine]) for engine in ENGINES},
        "mode": "all_three_full_sims",
        "claim_path_tools": ["QuantumOptics", "Z3", "qutip", "z3", "cvc5", "sympy", "torch.func"],
        "crossover_proofs": {"z3": z3, "cvc5": cvc5, "julia_z3": julia_z3},
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": max_divergence,
            "observable": "shared q0|q1q2 S(A|B), I(A:B), and I_c scalar vector",
            "within_tolerance": max_divergence <= TOL,
            "tolerance": TOL,
        },
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "parent_lineage": parent_lineage(),
        "expected_lanes": list(ENGINES),
        "stability_pairs": [
            {"subtree": "local_information_table", "hash": stable_hash(packet["local_information_table"])},
            {"subtree": "continuity_anchors", "hash": stable_hash(packet["continuity_anchors"])},
            {"subtree": "controls", "hash": stable_hash(packet["controls"])},
        ],
        "extra_fields": extra_fields,
    }


def build_result() -> dict[str, Any]:
    spec = build_spec()
    return build_envelope(**spec)


def main() -> int:
    result = build_result()
    write_json(RESULT, result)
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT), "max_divergence": result["divergence"]["max_divergence"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
