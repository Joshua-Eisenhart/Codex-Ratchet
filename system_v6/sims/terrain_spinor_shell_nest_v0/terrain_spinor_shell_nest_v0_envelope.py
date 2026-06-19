#!/usr/bin/env python3
"""Three-engine envelope for terrain_spinor_shell_nest_v0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from terrain_spinor_shell_nest_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SIM_DIR,
    SIM_ID,
    build_core_nest,
    dump_json,
    now_z,
    rel,
    sha256_file,
    sha256_text,
)


SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from engine results"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive result and source hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}
ENGINES = ("julia", "jax", "pytorch")
VALUE_KEYS = [
    "site_count",
    "required_terrain_count",
    "non_preserve_shell_site_count",
    "spinor_blind_max_signal",
    "shell_conditioned_gamma5_positive_rows",
    "si_own_frame_pass",
]


def load_leg(engine: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{SIM_ID}_{engine}_results.json"
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(engine: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": payload["result_path"],
        "result_sha256": sha256_file(ROOT / payload["result_path"]),
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "reads_peer_result": payload["reads_peer_result"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "role_id": payload["role_id"],
        "pin_sha256": payload["pin_sha256"],
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
        "tool_calls": payload["tool_calls"],
        "capability_receipts": payload["capability_receipts"],
        "acceptance": payload["acceptance"],
        "values": payload["values"],
    }


def collect_claim_path_tools(legs: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in legs.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def flatten_tool_calls(legs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for engine, payload in legs.items():
        for row in payload.get("tool_calls", []):
            rows.append({"engine": engine, **row})
    return rows


def source_hash_fresh(payload: dict[str, Any]) -> bool:
    source = ROOT / payload["source_path"]
    return source.exists() and sha256_file(source) == payload["source_sha256"]


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    engine_values = {engine: {key: float(legs[engine]["values"][key]) for key in VALUE_KEYS} for engine in ENGINES}
    rows = []
    max_div = 0.0
    max_key = None
    for key in VALUE_KEYS:
        values = {engine: engine_values[engine][key] for engine in ENGINES}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_div:
            max_div = diff
            max_key = key
    return {
        "julia_authoritative": True,
        "engine_values": engine_values,
        "max_divergence": max_div,
        "max_divergence_key": max_key,
        "comparison": {"rows": rows, "within_tolerance": max_div <= 1.0e-8, "same_named_observable_sets": True},
    }


def build_result() -> dict[str, Any]:
    legs = {engine: load_leg(engine) for engine in ENGINES}
    core = build_core_nest()
    pin_hashes = {payload["pin_sha256"] for payload in legs.values()}
    expected_pin = sha256_text(PIN_SPEC)
    div = divergence(legs)
    z3_proof = legs["jax"]["crossover_proofs"]["z3"]
    cvc5_proof = legs["jax"]["crossover_proofs"]["cvc5"]
    gate_pass = {
        "engine_legs_pass": all(payload["all_pass"] is True for payload in legs.values()),
        "pin_identical": len(pin_hashes) == 1 and expected_pin in pin_hashes,
        "source_hashes_fresh": all(source_hash_fresh(payload) for payload in legs.values()),
        "ceiling_exact": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is PROMOTION_ALLOWED
            and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for payload in legs.values()
        ),
        "no_peer_result_reads": all(payload["reads_peer_result"] is False for payload in legs.values()),
        "three_level_rows_present": all(
            set(payload["load_bearing_decomposition"]) >= {"Se_Funnel_L", "Ni_Pit_L", "Si_Hill_L", "Se_Cannon_R"}
            for payload in legs.values()
        ),
        "required_controls_pass": all(all(control.get("pass") is True for control in payload["controls"].values()) for payload in legs.values()),
        "si_frame_honest": all(payload["si_frame_row"]["honest_status"] in {"own_frame_computed", "incompatible_not_forced"} and payload["si_frame_row"]["pass"] is True for payload in legs.values()),
        "smt_z3_cvc5_agree": z3_proof["verdict"] == "unsat" and cvc5_proof["verdict"] == "unsat" and z3_proof["erased_control_verdict"] == "sat" and cvc5_proof["erased_control_verdict"] == "sat",
        "julia_z3_mirror": legs["julia"]["crossover_proofs"]["julia_z3"]["verdict"] == "unsat" and legs["julia"]["crossover_proofs"]["julia_z3"]["erased_control_verdict"] == "sat",
        "pytorch_z3_cvc5_mirror": legs["pytorch"]["crossover_proofs"]["z3"]["verdict"] == "unsat" and legs["pytorch"]["crossover_proofs"]["cvc5"]["verdict"] == "unsat",
        "divergence_ok": div["comparison"]["within_tolerance"],
        "rung1_unraveling_text_pinned": core["rung1_unraveling_convention_text_pin"] in PIN_SPEC,
        "mirror_parent_lineage_present": any(row.get("sim_id") == "terrain_exact_mirror_finder_v0" and row.get("commit_hint") == "81b38c3e6" for row in core["parent_lineage"]["consumed_inputs"]),
        "se_funnel_l_anchor_4_25_local": core["se_funnel_l_anchor_4_25"]["pass"] is True and core["se_funnel_l_anchor_4_25"]["computed_in_packet"] is True,
    }
    all_pass = all(gate_pass.values())
    claim_path_tools = collect_claim_path_tools(legs)
    return {
        "schema_version": "three_engine_sim_result_v1",
        "standard_schema_mode": "FIELD",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "claim": "Three-level terrain nest: committed S5 Bloch terrain flows, rung-1 Weyl spinor L/R lift, and committed n=3 shell support are computed together under scratch-only ceiling.",
        "honest_outcome": "Bare terrain Bloch flow exists at level (a); L/R signed separation needs spinor level (b); shell leakage class and shell-conditioned gamma5 shifts require shell placement level (c).",
        "owner_cant_work_test": {
            "operational_property_P": "shell_leakage_class plus shell_conditioned_gamma5_shift",
            "level_a_status": "undefined_or_degenerate",
            "level_b_status": "signed rows exist but shell leakage remains undefined",
            "level_c_status": "exists",
            "computed_matrix_keys": ["shell_leakage_class", "shell_conditioned_gamma5_shift"],
        },
        "allowed_claims": [
            "scratch diagnostic builder packet exists and runs",
            "the three-level nest was computed for required terrain rows",
            "level requirements are split by computed property matrix",
        ],
        "disallowed_claims": [
            "promotion beyond scratch_diagnostic",
            "full shell program admission",
            "exact sigma_y mirror survival",
            "nested/multi-layer disintegration proof beyond fixed-eta parent rule",
        ],
        "pin_spec": PIN_SPEC,
        "pin_sha256": expected_pin,
        "rung1_unraveling_convention_text_pin": core["rung1_unraveling_convention_text_pin"],
        "parent_lineage": core["parent_lineage"],
        "se_funnel_l_anchor_4_25": core["se_funnel_l_anchor_4_25"],
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
            "reads_peer_result": False,
            "standard_schema_binding": "schema_version is a field with value three_engine_sim_result_v1; packet-local standard_schema_mode is FIELD",
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": legs["julia"].get("julia_project"),
            "role": "Julia strict-carrier leg owns QuantumOptics/Grassmann/Z3 capability receipts; envelope compares bounded finite rows.",
            "classification": CLASSIFICATION,
            "proof_tag": "terrain_spinor_shell_nest_v0_erased_shell_placement_flip",
            "proof_pass": gate_pass["julia_z3_mirror"],
            "consumer_policy": "scratch diagnostic only; no promotion or admission",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": legs["julia"].get("julia_project"), "packages": legs["julia"]["packages_used"], "role": "semantic_owner"},
            "jax": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": legs["jax"]["packages_used"], "role": "diffrax/sympy/z3/cvc5 shell workhorse"},
            "pytorch": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": legs["pytorch"]["packages_used"], "role": "torch graph geometry derivative mirror"},
            "tensor_exchange": "none; no cross-engine tensor exchange on claim path",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": claim_path_tools,
        "TOOL_MANIFEST": {engine: legs[engine]["TOOL_MANIFEST"] for engine in ENGINES},
        "TOOL_INTEGRATION_DEPTH": {engine: legs[engine]["TOOL_INTEGRATION_DEPTH"] for engine in ENGINES},
        "engines": {engine: engine_record(engine, payload) for engine, payload in legs.items()},
        "load_bearing_decomposition": legs["jax"]["load_bearing_decomposition"],
        "three_level_property_matrix": legs["jax"]["three_level_property_matrix"],
        "si_frame_row": legs["jax"]["si_frame_row"],
        "controls": legs["jax"]["controls"],
        "capability_receipts": {engine: legs[engine]["capability_receipts"] for engine in ENGINES},
        "tool_calls": flatten_tool_calls(legs),
        "smt_identity_values": legs["jax"]["smt_identity_values"],
        "crossover_proofs": {
            "z3": z3_proof,
            "cvc5": cvc5_proof,
            "julia_z3": legs["julia"]["crossover_proofs"]["julia_z3"],
            "pytorch_z3": legs["pytorch"]["crossover_proofs"]["z3"],
            "pytorch_cvc5": legs["pytorch"]["crossover_proofs"]["cvc5"],
        },
        "divergence": div,
        "gate_pass": gate_pass,
        "engine_result_sha256": {engine: sha256_file(ROOT / legs[engine]["result_path"]) for engine in ENGINES},
    }


def main() -> int:
    payload = build_result()
    dump_json(RESULT_PATH, payload)
    print(f"wrote: {RESULT_PATH}")
    print(f"{SIM_ID}_ENVELOPE_DONE all_pass={str(payload['all_pass']).lower()} max_divergence={payload['divergence']['max_divergence']}")
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
