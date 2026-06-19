#!/usr/bin/env python3
"""Controller envelope for entropy_type_ratchet_v2."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

from entropy_type_ratchet_v2_common import (
    RESULT_DIR,
    ROOT,
    SIM_ID,
    TYPE_ORDER,
    build_discovery_packet,
    final_values,
    parent_lineage,
    rel,
    sha256_file,
    stable_hash,
    write_json,
)

sys.path.insert(0, str(ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402


SOURCE = Path(__file__).resolve()
RESULT = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
ENGINES = ("julia", "jax", "pytorch")


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


def max_delta(values: list[float]) -> float:
    return max(values) - min(values)


def typed_label(row: dict[str, Any]) -> str:
    value = row.get("value")
    if isinstance(value, dict) and "typed_label" in value:
        return str(value["typed_label"])
    return str(row["typed_label"])


def markdown_table(rows: list[dict[str, Any]]) -> str:
    header = ["step"] + list(TYPE_ORDER)
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    for row in rows:
        cells = [row["step_id"]]
        for type_id in TYPE_ORDER:
            type_row = row["entropy_types"][type_id]
            if type_row["status"] == "undefined":
                cells.append("missing:" + type_row["missing_structure"])
            else:
                cells.append(type_row["status"])
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def build_result() -> dict[str, Any]:
    legs = {engine: load_leg(engine) for engine in ENGINES}
    packet = build_discovery_packet()
    table = packet["type_admissibility_table"]
    values = {engine: legs[engine]["engine_values"] for engine in ENGINES}
    rho_values = [float(values[engine]["rho_entropy_nats"]) for engine in ENGINES]
    final_counts = [int(values[engine]["final_available_type_count"]) for engine in ENGINES]
    z3 = legs["jax"]["crossover_proofs"]["z3"]
    cvc5 = legs["jax"]["crossover_proofs"]["cvc5"]
    julia_z3 = legs["julia"]["crossover_proofs"]["julia_z3"]
    all_pass = (
        packet["all_pass"]
        and all(leg["all_pass"] for leg in legs.values())
        and len(set(final_counts)) == 1
        and final_counts[0] == len(TYPE_ORDER)
        and max_delta(rho_values) <= 1.0e-10
        and z3["verdict"] == "unsat"
        and cvc5["verdict"] == "unsat"
        and julia_z3["verdict"] == "unsat"
        and z3["perturbed_construction_path_verdict"] == "sat"
        and cvc5["perturbed_construction_path_verdict"] == "sat"
        and julia_z3["perturbed_construction_path_verdict"] == "sat"
        and not (RESULT.parent.parent / "audit_verdict.md").exists()
    )
    lanes = {engine: lane_record(legs[engine]) for engine in ENGINES}
    extra_fields = {
        "schema": f"{SIM_ID}_envelope_v2",
        "source_path": rel(SOURCE),
        "source_sha256": sha256_file(SOURCE),
        "result_path": rel(RESULT),
        "all_pass": all_pass,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim": "the admissible entropy/information type set and operator applications are tested by constructors against a parent-derived operation sequence",
        "allowed_claims": [
            "per-step availability table over the consumed parent state lineage",
            "primary operation order read from consumed parent artifact rows and hashes",
            "alternative committed parent order tested for off-doctrine availability steps",
            "structural missing-object failures for premature evaluations",
            "order-sensitive availability under actual operation permutation",
            "operator co-ratchet applications/failures tied to the same constructed objects",
            "SMT identity over construction-derived status table with erased-quotient SAT flip",
        ],
        "disallowed_claims": [
            "formal admission",
            "physics theorem",
            "universal entropy scalar",
            "doctrine confirmation beyond this scratch diagnostic packet",
        ],
        "type_admissibility_table": table,
        "per_step_type_admissibility_table": table["rows"],
        "discovered_per_step_table_markdown": markdown_table(table["rows"]),
        "sequence_derivation": packet["sequence_derivation"],
        "alternative_sequence_findings": packet["alternative_sequence_findings"],
        "availability_sequence": table["availability_sequence"],
        "named_change_steps": table["change_steps"],
        "doctrine_table_comparison": packet["doctrine_table_comparison"],
        "controls": packet["controls"],
        "builder_gates": packet["builder_gates"],
        "positive_section": {
            "final_available_types": table["rows"][-1]["available_types"],
            "doctrine_table_agreement": packet["doctrine_table_comparison"]["agreement"],
            "sequence_from_parent": packet["builder_gates"]["sequence_from_parent"],
            "operator_co_ratchet_final": table["rows"][-1]["operator_co_ratchet"],
        },
        "negative_section": {
            "premature_evaluation": packet["controls"]["premature_evaluation"],
            "spoofed_enable": packet["controls"]["spoofed_enable"],
            "composed_sequence_rejection": packet["controls"]["composed_sequence_rejection"],
            "type_confusion": packet["controls"]["type_confusion"],
            "order_shuffle": packet["controls"]["order_shuffle"],
            "alternative_sequence": packet["controls"]["alternative_sequence"],
        },
        "boundary_section": {
            "degenerate_flag": packet["controls"]["degenerate_flag"],
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        },
        "typed_entropy_discipline": {
            "log_base": "e",
            "typed_labels": {type_id: typed_label(table["rows"][-1]["entropy_types"][type_id]) for type_id in TYPE_ORDER},
            "cross_type_sum_without_convention": "rejected",
        },
        "operator_co_ratchet": [row["operator_co_ratchet"] for row in table["rows"]],
        "TOOL_INTENT_MATRIX": {engine: legs[engine]["package_observables"] for engine in ENGINES},
        "tool_intent": {
            "claim_classes": ["discovered_availability_table", "structural_failures", "operator_co_ratchet", "smt_identity_flip"],
            "engine_tool_intent": {engine: legs[engine]["package_observables"] for engine in ENGINES},
        },
        "TOOL_MANIFEST": {
            "build_three_engine_envelope": {"tried": True, "used": True, "reason": "load-bearing standard envelope construction"},
            "QuantumOptics": legs["julia"]["TOOL_MANIFEST"]["QuantumOptics"],
            "Z3": legs["julia"]["TOOL_MANIFEST"]["Z3"],
            "sympy": legs["jax"]["TOOL_MANIFEST"]["sympy"],
            "z3": legs["jax"]["TOOL_MANIFEST"]["z3"],
            "cvc5": legs["jax"]["TOOL_MANIFEST"]["cvc5"],
            "torch": legs["pytorch"]["TOOL_MANIFEST"]["torch"],
            "torch_geometric": legs["pytorch"]["TOOL_MANIFEST"]["torch_geometric"],
            "torch.func": legs["pytorch"]["TOOL_MANIFEST"]["torch.func"],
        },
        "TOOL_INTEGRATION_DEPTH": {
            "build_three_engine_envelope": "load_bearing",
            "QuantumOptics": "load_bearing",
            "Z3": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "torch": "supportive",
            "torch_geometric": "load_bearing",
            "torch.func": "supportive",
        },
        "tool_calls": legs["julia"]["tool_calls"] + legs["jax"]["tool_calls"] + legs["pytorch"]["tool_calls"],
        "validator_expected_commands": [
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/entropy_type_ratchet_v2/entropy_type_ratchet_v2_jax.py",
            "env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/entropy_type_ratchet_v2/entropy_type_ratchet_v2_pytorch.py",
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/entropy_type_ratchet_v2/entropy_type_ratchet_v2_julia.jl",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/entropy_type_ratchet_v2/entropy_type_ratchet_v2_envelope.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/entropy_type_ratchet_v2/validate_entropy_type_ratchet_v2.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/entropy_type_ratchet_v2/test_entropy_type_ratchet_v2.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/entropy_type_ratchet_v2/results/entropy_type_ratchet_v2_envelope_results.json",
        ],
        "table_hash": stable_hash(table),
    }
    return build_envelope(
        sim_id=SIM_ID,
        lanes=lanes,
        mode="all_three_full_sims",
        claim_path_tools=["QuantumOptics", "Z3", "sympy", "z3", "cvc5", "torch_geometric"],
        crossover_proofs={"z3": z3, "cvc5": cvc5, "julia_z3": julia_z3},
        divergence={
            "julia_authoritative": True,
            "engine_values": {
                "julia": {"final_available_type_count": final_counts[0], "rho_entropy_nats": rho_values[0]},
                "jax": {"final_available_type_count": final_counts[1], "rho_entropy_nats": rho_values[1]},
                "pytorch": {"final_available_type_count": final_counts[2], "rho_entropy_nats": rho_values[2]},
            },
            "max_divergence": max(max_delta(rho_values), float(max(final_counts) - min(final_counts))),
            "observable": "rho_entropy_nats_and_final_available_type_count",
        },
        parent_lineage=parent_lineage(),
        stability_pairs=[
            {"subtree": "type_admissibility_table", "hash": stable_hash(table)},
            {"subtree": "sequence_derivation", "hash": stable_hash(packet["sequence_derivation"])},
            {"subtree": "alternative_sequence_findings", "hash": stable_hash(packet["alternative_sequence_findings"])},
            {"subtree": "doctrine_table_comparison", "hash": stable_hash(packet["doctrine_table_comparison"])},
            {"subtree": "controls", "hash": stable_hash(packet["controls"])},
        ],
        extra_fields=extra_fields,
    )


def main() -> int:
    payload = build_result()
    write_json(RESULT, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": rel(RESULT)}, indent=2))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
