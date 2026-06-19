#!/usr/bin/env python3
"""Envelope for geo_s9_octonionic_hopf_stack_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s9_octonionic_hopf_stack_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PROGRAM_RECEIPT = "system_v6/receipts/geometry_sim_program_canonical_20260610.md"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
PIN_SPEC = (
    "geo_s9_octonionic_hopf_stack_v0|stage:S9|mode:FREE_stack_deepening|"
    "psi=(z0..z7) in C8 normalized=S15 3Q state|basis=000,001,010,011,100,101,110,111|"
    "C8~=O2 by right-C_e1 convention: O basis over C_e1 is (e0,e2,e4,e5), complex i acts by right multiplication by e1|"
    "o1=C4(z0..z3),o2=C4(z4..z7)|Hopf_O=(2*o1*conj(o2),abs2(o1)-abs2(o2)) in OxR=S8|"
    "fiber=S7 unit octonions as Moufang loop not Lie group|N01=nonassociative reassociation visible|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from independent Julia and Python leg receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source hashing and pin equality checks"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result path binding"},
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload.get("all_pass") is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path.relative_to(ROOT)),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "role_id": payload["role_id"],
        "pin_sha256": payload["pin_sha256"],
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
        "tool_calls": payload.get("tool_calls", []),
        "claim_path_tools": payload.get("claim_path_tools", []),
        "capability_receipts": payload.get("capability_receipts", {}),
        "shared_scalars": payload.get("shared_scalars", {}),
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def require_gate(condition: bool, name: str, details: Any) -> dict[str, Any]:
    return {"pass": bool(condition), "gate": name, "details": details}


def tool_call_coverage(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = {}
    for engine, payload in payloads.items():
        declared = set(payload.get("claim_path_tools", []))
        called = {row.get("tool") for row in payload.get("tool_calls", [])}
        rows[engine] = {
            "declared": sorted(declared),
            "called": sorted(called),
            "one_to_one": declared <= called and len(payload.get("tool_calls", [])) == len(called),
        }
    return rows


def exact_divergence(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    keys = ["s8_norm_max_deviation", "moufang_basis_violations", "spin9_dim", "s15_volume_pi8_over_2520"]
    values = {engine: {key: payload["shared_scalars"][key] for key in keys} for engine, payload in payloads.items()}
    rows = []
    max_divergence = 0
    for key in keys:
        row_values = {engine: values[engine][key] for engine in values}
        exact_match = len(set(row_values.values())) == 1
        rows.append({"key": key, "values": row_values, "exact_match": exact_match})
        if not exact_match:
            max_divergence = 1
    return {
        "julia_authoritative": True,
        "engine_values": values,
        "max_divergence": max_divergence,
        "comparison": {"rows": rows, "exact_match": max_divergence == 0},
    }


def build_result() -> dict[str, Any]:
    payloads = {"julia": load_json(JULIA_RESULT), "jax": load_json(JAX_RESULT)}
    julia = payloads["julia"]
    jax = payloads["jax"]
    pin_hashes = {payload["pin_sha256"] for payload in payloads.values()}
    ceilings_exact = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is PROMOTION_ALLOWED
        and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
        for payload in payloads.values()
    )
    call_cov = tool_call_coverage(payloads)
    div = exact_divergence(payloads)
    j_receipts = julia["receipts"]
    p_receipts = jax["receipts"]
    j_proof = julia["proofs"]["P1_moufang_identity"]
    p_proof = jax["proofs"]["P1_moufang_identity"]
    gates = {
        "legs_exit_0_by_receipt": require_gate(
            all(payload["all_pass"] is True for payload in payloads.values()),
            "legs_exit_0_by_receipt",
            {engine: payload["all_pass"] for engine, payload in payloads.items()},
        ),
        "pin_identical": require_gate(len(pin_hashes) == 1 and next(iter(pin_hashes)) == sha256_text(PIN_SPEC), "pin_identical", sorted(pin_hashes)),
        "ceiling_exact": require_gate(ceilings_exact, "ceiling_exact", {engine: payload["classification"] for engine, payload in payloads.items()}),
        "map_s15_to_s8": require_gate(
            j_receipts["O1_map"]["pass"] is True
            and p_receipts["O1_map"]["pass"] is True
            and p_receipts["O1_map"]["rows"]["W_3"]["base_norm_squared"] == "1",
            "map_s15_to_s8",
            {"julia": j_receipts["O1_map"], "python": p_receipts["O1_map"]},
        ),
        "N01_moufang_nonassoc": require_gate(
            j_receipts["O2_moufang_nonassoc"]["pass"] is True
            and p_receipts["O2_moufang_nonassoc"]["pass"] is True
            and p_receipts["O2_moufang_nonassoc"]["associator_witness"]["gap_norm_squared"] > 0,
            "N01_moufang_nonassoc",
            {"julia": j_receipts["O2_moufang_nonassoc"], "python": p_receipts["O2_moufang_nonassoc"]},
        ),
        "qit_tau_miss_boundary": require_gate(
            p_receipts["O3_qit_entanglement"]["pass"] is True
            and p_receipts["O3_qit_entanglement"]["committed_three_qubit_floor_crosscheck"]["matched"] is True
            and "does not determine genuine tripartite tau" in p_receipts["O3_qit_entanglement"]["finding"],
            "qit_tau_miss_boundary",
            p_receipts["O3_qit_entanglement"],
        ),
        "no_connection_spin9": require_gate(
            j_receipts["O4_no_connection_spin9"]["pass"] is True
            and p_receipts["O4_no_connection_spin9"]["pass"] is True
            and p_receipts["O4_no_connection_spin9"]["no_c4_or_chern_row"] is True,
            "no_connection_spin9",
            {"julia": j_receipts["O4_no_connection_spin9"], "python": p_receipts["O4_no_connection_spin9"]},
        ),
        "foliation_exact": require_gate(
            j_receipts["O5_foliation"]["pass"] is True
            and p_receipts["O5_foliation"]["pass"] is True
            and p_receipts["O5_foliation"]["total_volume"] == "pi**8/2520",
            "foliation_exact",
            {"julia": j_receipts["O5_foliation"], "python": p_receipts["O5_foliation"]},
        ),
        "adams_sedenion_boundary": require_gate(
            j_receipts["O6_adams_sedenion_boundary"]["pass"] is True
            and p_receipts["O6_adams_sedenion_boundary"]["pass"] is True
            and p_receipts["O6_adams_sedenion_boundary"]["sedenion_zero_divisor_boundary"]["committed_same_class_zero_witness"]["zero_product"] is True
            and p_receipts["O6_adams_sedenion_boundary"]["sedenion_zero_divisor_boundary"]["requested_class_check"]["zero_product"] is False,
            "adams_sedenion_boundary",
            {"julia": j_receipts["O6_adams_sedenion_boundary"], "python": p_receipts["O6_adams_sedenion_boundary"]},
        ),
        "smt_flip": require_gate(
            j_proof["z3_positive"] == "unsat"
            and j_proof["z3_flipped_table_control"] == "sat"
            and p_proof["z3_positive"] == "unsat"
            and p_proof["cvc5_positive"] == "unsat"
            and p_proof["z3_flipped_table_control"] == "sat"
            and p_proof["cvc5_flipped_table_control"] == "sat",
            "smt_flip",
            {"julia": j_proof, "python": p_proof},
        ),
        "controls_fired": require_gate(
            all(row.get("fired") is True for payload in payloads.values() for row in payload.get("controls", {}).values()),
            "controls_fired",
            {engine: payload.get("controls", {}) for engine, payload in payloads.items()},
        ),
        "tool_calls_one_to_one": require_gate(
            all(row["one_to_one"] is True for row in call_cov.values()),
            "tool_calls_one_to_one",
            call_cov,
        ),
        "cross_engine_exact_scalars_match": require_gate(div["comparison"]["exact_match"] is True, "cross_engine_exact_scalars_match", div),
    }
    all_pass = all(gate["pass"] for gate in gates.values())
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "S9 scratch diagnostic for the octonionic Hopf fibration S7->S15->S8 on the three-qubit C8 carrier: pinned O2 map, Moufang-loop fiber boundary, QIT tau-miss honesty, no-principal-connection boundary, S7xS7 foliation, and Adams/sedenion termination.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "program_receipt": PROGRAM_RECEIPT,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "engine_contract": {
            "mode": "julia_canon_plus_jax_diagnostic",
            "lanes": ["julia", "jax"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
            "pytorch": {
                "status": "excluded",
                "reason": "No graph, network, or autograd claim path is scoped; Octonions.jl, SymPy, QuTiP, z3, and cvc5 carry the requested packet.",
            },
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": julia.get("julia_project"),
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": julia["source_sha256"],
            "receipt_path": julia["result_path"],
            "proof_tag": "octonionic_hopf_moufang_loop_z3_finite_identity",
            "proof_pass": julia["all_pass"],
            "table_version": SIM_ID,
            "bracket_convention": "Octonions.jl basis; right-C_e1 C8~=O2 coordinate pin; explicit parenthesization in Hopf and Moufang rows",
            "consumer_policy": "independent Julia/Python recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia.get("julia_project"), "packages": julia["packages_used"], "role": "Octonions.jl semantic owner and Z3 finite identity check"},
            "jax": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": jax["packages_used"], "role": "SymPy/QIT/SMT exact sidecar under repo jax lane convention"},
            "pytorch": {"status": "excluded", "role": "not scoped"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "allowed_claims": [
            "scratch diagnostic octonionic Hopf stacked geometry rows listed in claim",
            "QIT finding that the selected O2/A|BC base readout does not determine three-tangle tau",
            "boundary placement in the four Hopf fibration ladder",
        ],
        "must_not_claim_fences": [
            "formal admission",
            "canonical geometry admission",
            "bridge or axis-level claim",
            "principal S7 connection or Chern row",
            "fifth Hopf fibration",
        ],
        "claim_path_tools": collect_claim_tools(payloads),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
        },
        "receipts": {
            "julia": julia["receipts"],
            "jax": jax["receipts"],
        },
        "proofs": {
            "julia": julia["proofs"],
            "jax": jax["proofs"],
        },
        "controls": {
            "julia": julia["controls"],
            "jax": jax["controls"],
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "positive_identity": p_proof["z3_positive"],
                    "flipped_table_control": p_proof["z3_flipped_table_control"],
                },
            },
            "cvc5": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "positive_identity": p_proof["cvc5_positive"],
                    "flipped_table_control": p_proof["cvc5_flipped_table_control"],
                },
            },
            "julia_z3": {
                "ran": True,
                "verdict": j_proof["z3_positive"],
                "load_bearing": True,
                "proofs": j_proof,
            },
        },
        "gate_pass": gates,
        "divergence": div,
        "blind_audit_expected_values": jax["blind_audit_expected_values"],
        "seed_ledger": {
            "rng": "none",
            "deterministic_rows": ["Julia basis table from Octonions.jl", "Python symbolic rows", "finite Moufang SMT domain", "named QIT states"],
        },
        "builder_self_check_is_evidence": False,
        "validator_expected_command": "SIM_PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 $SIM_PY scripts/validate_three_engine_sim_result.py system_v6/sims/geo_s9_octonionic_hopf_stack_v0/results/geo_s9_octonionic_hopf_stack_v0_envelope_results.json --require-source-backed",
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
