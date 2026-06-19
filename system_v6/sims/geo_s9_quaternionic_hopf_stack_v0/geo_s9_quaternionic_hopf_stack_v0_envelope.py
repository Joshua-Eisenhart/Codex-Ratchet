#!/usr/bin/env python3
"""Envelope for geo_s9_quaternionic_hopf_stack_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s9_quaternionic_hopf_stack_v0"
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
    "geo_s9_quaternionic_hopf_stack_v0|stage:S9|mode:FREE_stack_deepening|"
    "psi=(a,b,c,d) in C4 normalized=S7 2Q state|q1=a+b*j,q2=c+d*j|"
    "Hopf_H=(2*q1*conj(q2),abs2(q1)-abs2(q2)) in HxR=S4|"
    "coords=(ReH,IH,JH,KH,R)|concurrence=sqrt(JH^2+KH^2)=2|a*d-b*c||"
    "separable_locus:JH=KH=0 distinguished S2|connection:BPST Sp1 instanton orientation_pinned_c2_plus1|"
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
        "shared_scalars": payload.get("shared_scalars", {}),
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def require_gate(condition: bool, name: str, details: Any) -> dict[str, Any]:
    return {"pass": bool(condition), "gate": name, "details": details}


def exact_divergence(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    keys = ["product_concurrence_squared", "bell_concurrence_squared", "c2", "s7_volume_pi4_over_3"]
    values = {
        engine: {key: payload["shared_scalars"][key] for key in keys}
        for engine, payload in payloads.items()
    }
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
    j_proof = julia["proofs"]["P1_finite_concurrence_block_identity"]
    p_proof = jax["proofs"]["P1_finite_concurrence_block_identity"]
    gates = {
        "legs_exit_0_by_receipt": require_gate(
            all(payload["all_pass"] is True for payload in payloads.values()),
            "legs_exit_0_by_receipt",
            {engine: payload["all_pass"] for engine, payload in payloads.items()},
        ),
        "pin_identical": require_gate(len(pin_hashes) == 1 and next(iter(pin_hashes)) == sha256_text(PIN_SPEC), "pin_identical", sorted(pin_hashes)),
        "ceiling_exact": require_gate(ceilings_exact, "ceiling_exact", {engine: payload["classification"] for engine, payload in payloads.items()}),
        "map_fiber_sp1": require_gate(
            j_receipts["H1_map_and_fiber"]["pass"] is True
            and j_receipts["H1_map_and_fiber"]["right_sp1_orbit_invariance_max_deviation"] <= 1.0e-8
            and j_receipts["H1_map_and_fiber"]["fiber_converse_constructive_max_residual"] <= 1.0e-8,
            "map_fiber_sp1",
            j_receipts["H1_map_and_fiber"],
        ),
        "qit_concurrence_detection": require_gate(
            j_receipts["H3_qit_entanglement"]["pass"] is True
            and p_receipts["H1_symbolic_map_qit_identity"]["pass"] is True
            and p_receipts["H2_qutip_concurrence_crosscheck"]["pass"] is True
            and p_receipts["H2_qutip_concurrence_crosscheck"]["committed_two_qubit_boundary_crosscheck"]["matched"] is True,
            "qit_concurrence_detection",
            {"julia": j_receipts["H3_qit_entanglement"], "python": p_receipts["H2_qutip_concurrence_crosscheck"]},
        ),
        "connection_c2_exact": require_gate(
            j_receipts["H2_connection_curvature_c2"]["pass"] is True
            and p_receipts["H3_connection_curvature_c2"]["pass"] is True
            and p_receipts["H3_connection_curvature_c2"]["c2"] == "1"
            and p_receipts["H3_connection_curvature_c2"]["wrong_orientation_control"]["fired"] is True,
            "connection_c2_exact",
            {"julia": j_receipts["H2_connection_curvature_c2"], "python": p_receipts["H3_connection_curvature_c2"]},
        ),
        "nested_foliation_exact": require_gate(
            j_receipts["H5_nested_s3xs3_foliation"]["pass"] is True
            and p_receipts["H4_nested_s3xs3_foliation"]["pass"] is True
            and p_receipts["H4_nested_s3xs3_foliation"]["total_s7_volume"] == "pi**4/3",
            "nested_foliation_exact",
            {"julia": j_receipts["H5_nested_s3xs3_foliation"], "python": p_receipts["H4_nested_s3xs3_foliation"]},
        ),
        "density_quotient_distinction": require_gate(
            j_receipts["H4_density_quotient"]["pass"] is True
            and p_receipts["H6_density_quotient_distinction"]["pass"] is True,
            "density_quotient_distinction",
            {"julia": j_receipts["H4_density_quotient"], "python": p_receipts["H6_density_quotient_distinction"]},
        ),
        "nonabelian_holonomy_boundary": require_gate(
            p_receipts["H5_nonabelian_holonomy"]["pass"] is True
            and p_receipts["H7_boundary_adams"]["pass"] is True
            and j_receipts["H6_boundary_and_nonabelian_fiber"]["pass"] is True,
            "nonabelian_holonomy_boundary",
            {"python_holonomy": p_receipts["H5_nonabelian_holonomy"], "boundary": p_receipts["H7_boundary_adams"]},
        ),
        "smt_flip": require_gate(
            j_proof["positive_verdict"] == "unsat"
            and j_proof["erased_flip_verdict"] == "sat"
            and p_proof["z3_verdict"] == "unsat"
            and p_proof["cvc5_verdict"] == "unsat"
            and p_proof["z3_erased_flip_control"] == "sat"
            and p_proof["cvc5_erased_flip_control"] == "sat",
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
        "claim": "S9 scratch diagnostic deepening of the quaternionic Hopf fibration S3->S7->S4 as stacked geometry: map/fiber, Sp(1) instanton c2=1, QIT concurrence detection, density quotient distinction, S3xS3 foliation, Adams boundary, and nonabelian holonomy contrast.",
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
                "reason": "No graph, network, or autograd claim path is scoped; Quaternions.jl, SymPy, z3/cvc5, and QuTiP carry the requested packet.",
            },
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": julia.get("julia_project"),
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": julia["source_sha256"],
            "receipt_path": julia["result_path"],
            "proof_tag": "quaternionic_hopf_sp1_fiber_z3_finite_identity",
            "proof_pass": julia["all_pass"],
            "table_version": SIM_ID,
            "bracket_convention": "q1=a+b*j, q2=c+d*j; right Sp(1) fiber; c2 orientation pinned in BPST chart",
            "consumer_policy": "independent Julia/Python recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia.get("julia_project"), "packages": julia["packages_used"], "role": "quaternionic semantic owner and Z3 finite identity check"},
            "jax": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": jax["packages_used"], "role": "SymPy/QIT/SMT exact sidecar under repo jax lane convention"},
            "pytorch": {"status": "excluded", "role": "not scoped"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "allowed_claims": [
            "scratch diagnostic quaternionic Hopf stacked geometry rows listed in claim",
            "QIT concurrence detection for the pinned two-qubit coefficient convention",
            "boundary placement in the four Hopf fibration ladder",
        ],
        "must_not_claim_fences": [
            "formal admission",
            "canonical geometry admission",
            "bridge or axis-level claim",
            "octonionic S7->S15->S8 built",
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
                    "positive_identity": p_proof["z3_verdict"],
                    "erased_flip_control": p_proof["z3_erased_flip_control"],
                },
            },
            "cvc5": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "positive_identity": p_proof["cvc5_verdict"],
                    "erased_flip_control": p_proof["cvc5_erased_flip_control"],
                },
            },
            "julia_z3": {
                "ran": True,
                "verdict": j_proof["positive_verdict"],
                "load_bearing": True,
                "proofs": j_proof,
            },
        },
        "gate_pass": gates,
        "divergence": div,
        "blind_audit_expected_values": jax["blind_audit_expected_values"],
        "seed_ledger": {
            "rng": "none",
            "deterministic_rows": ["Julia trigonometric sample grid", "Python symbolic rows", "finite integer SMT domain", "named QIT states"],
        },
        "builder_self_check_is_evidence": False,
        "validator_expected_command": "SIM_PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 $SIM_PY scripts/validate_three_engine_sim_result.py system_v6/sims/geo_s9_quaternionic_hopf_stack_v0/results/geo_s9_quaternionic_hopf_stack_v0_envelope_results.json --require-source-backed",
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
