#!/usr/bin/env python3
"""Envelope for mct_dynamic_deformation_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "mct_dynamic_deformation_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402

COMMON_VALUE_KEYS = [
    "support_size",
    "adm_free",
    "adm_f01",
    "adm_active",
    "release_N01_gain",
    "q_without_phase",
    "q_with_phase",
    "warp_edge_count_before",
    "warp_edge_count_after",
    "c1_abs",
    "chain_additivity_defect_zero",
    "cover_factor",
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": payload["result_path"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "reads_peer_result": payload["reads_peer_result"],
        "reads_parent_results": payload["reads_parent_results"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "values": payload["values"],
        "capability_receipts": payload["capability_receipts"],
        "all_pass": payload["all_pass"],
    }


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    max_div = 0.0
    max_key = None
    for key in COMMON_VALUE_KEYS:
        values = {engine: float(payload["values"][key]) for engine, payload in legs.items()}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_div:
            max_div = diff
            max_key = key
    return {
        "julia_authoritative": True,
        "engine_values": {engine: {key: float(payload["values"][key]) for key in COMMON_VALUE_KEYS} for engine, payload in legs.items()},
        "max_divergence": max_div,
        "max_divergence_key": max_key,
        "comparison": {"rows": rows, "within_tolerance": max_div <= 1.0e-8},
    }


def build_result() -> dict[str, Any]:
    legs = {"julia": load(JULIA_RESULT), "jax": load(JAX_RESULT)}
    z3 = legs["jax"]["crossover_proofs"]["z3"]
    cvc5 = legs["jax"]["crossover_proofs"]["cvc5"]
    julia_z3 = legs["julia"]["crossover_proofs"]["julia_z3"]
    quotient_z3 = legs["jax"]["crossover_proofs"]["quotient_irreversibility_z3"]
    quotient_cvc5 = legs["jax"]["crossover_proofs"]["quotient_irreversibility_cvc5"]
    div = divergence(legs)
    all_controls_fired = all(row.get("fired") is True for row in legs["jax"]["controls"].values()) and all(
        row.get("fired") is True for row in legs["julia"]["controls"].values()
    )
    ceiling_ok = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        for payload in legs.values()
    )
    proof_ok = (
        z3["verdict"] == cvc5["verdict"] == julia_z3["verdict"] == "unsat"
        and z3["erased_release_control_verdict"] == cvc5["erased_release_control_verdict"] == julia_z3["erased_release_control_verdict"] == "sat"
        and quotient_z3["verdict"] == quotient_cvc5["verdict"] == "unsat"
        and quotient_z3["phase_refined_control_verdict"] == quotient_cvc5["phase_refined_control_verdict"] == "sat"
    )
    tool_calls = legs["jax"]["tool_calls"] + legs["julia"]["tool_calls"]
    claim_path_tools = ["jax", "sympy", "z3", "cvc5", "Graphs", "Z3"]
    one_to_one = sorted(call["tool"] for call in tool_calls) == sorted(claim_path_tools)
    capability_receipts = {engine: legs[engine]["capability_receipts"] for engine in legs}
    capability_receipts_present = all(bool(receipt) for receipt in capability_receipts.values())
    all_pass = bool(
        all(payload["all_pass"] for payload in legs.values())
        and all_controls_fired
        and ceiling_ok
        and proof_ok
        and div["comparison"]["within_tolerance"]
        and one_to_one
        and capability_receipts_present
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "engine_contract": {
            "mode": "julia_canon_plus_jax_smt_deformation_diagnostic",
            "lanes": ["julia", "jax"],
            "omitted_lanes": {"pytorch": "not scoped: no graph/network/autograd claim path beyond Julia Graphs finite relation check"},
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
            "reads_peer_result": False,
        },
        "engines": {engine: engine_record(payload) for engine, payload in legs.items()},
        "claim_path_tools": claim_path_tools,
        "crossover_proofs": {
            "z3": z3,
            "cvc5": cvc5,
            "julia_z3": julia_z3,
            "quotient_irreversibility_z3": quotient_z3,
            "quotient_irreversibility_cvc5": quotient_cvc5,
        },
        "divergence": div,
        "parent_lineage": legs["jax"]["parent_lineage"],
        "source_refs": legs["jax"]["source_refs"],
        "M_C_t_object": legs["jax"]["M_C_t_object"],
        "deformation_mode_ledger": legs["jax"]["deformation_mode_ledger"],
        "rigidity_rows": legs["jax"]["rigidity_rows"],
        "compress_radiate_link": legs["jax"]["compress_radiate_link"],
        "committed_ratchet_anchor_summary": legs["jax"]["committed_ratchet_anchor_summary"],
        "controls": {engine: legs[engine]["controls"] for engine in legs},
        "TOOL_MANIFEST": {engine: legs[engine]["TOOL_MANIFEST"] for engine in legs},
        "TOOL_INTEGRATION_DEPTH": {engine: legs[engine]["TOOL_INTEGRATION_DEPTH"] for engine in legs},
        "capability_receipts": capability_receipts,
        "tool_calls": tool_calls,
        "build_gates": {
            "ceilings_exact": ceiling_ok,
            "all_controls_fired": all_controls_fired,
            "proofs_load_bearing": proof_ok,
            "divergence_zero": div["comparison"]["within_tolerance"],
            "one_to_one_tool_calls": one_to_one,
            "capability_receipts_present": capability_receipts_present,
            "no_audit_verdict_written": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        },
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "MCT_DYNAMIC_DEFORMATION_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"divergence={result['divergence']['max_divergence']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
