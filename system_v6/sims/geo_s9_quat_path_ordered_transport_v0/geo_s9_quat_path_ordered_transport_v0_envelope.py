#!/usr/bin/env python3
"""Envelope for geo_s9_quat_path_ordered_transport_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s9_quat_path_ordered_transport_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PARENT_ID = "geo_s9_quaternionic_hopf_stack_v0"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
STAGE_MOVEMENT_ALLOWED = False
COMMITTED_GAP = 1.4999999999999998
PIN_SPEC = (
    "geo_s9_quat_path_ordered_transport_v0|stage:S9|mode:path_ordered_transport|"
    "parent=geo_s9_quaternionic_hopf_stack_v0 read_only|"
    "BPST Sp1 A=Im(x*dconj(x))/(1+|x|^2)|loops=(x0,x1)->i,(x0,x2)->j|"
    "theta=pi/3 transported calibration|abelian=S2 U1 horizontal holonomy|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from independent Julia and Python leg receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source, result, parent-lineage, and pin hash checks"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": rel(result_path),
        "result_sha256": file_sha256(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "role_id": payload["role_id"],
        "pin_sha256": payload["pin_sha256"],
        "parent_lineage": payload["parent_lineage"],
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
        "tool_calls": payload.get("tool_calls", []),
        "capability_receipts": payload.get("capability_receipts", {}),
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    out: set[str] = set()
    for payload in payloads.values():
        out.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(out)


def source_hash_current(payload: dict[str, Any]) -> bool:
    return file_sha256(ROOT / payload["source_path"]) == payload["source_sha256"]


def numeric_pair(julia_value: float, jax_value: float) -> dict[str, Any]:
    return {"julia": julia_value, "jax": jax_value, "abs_diff": abs(julia_value - jax_value)}


def divergence(julia: dict[str, Any], jax: dict[str, Any]) -> dict[str, Any]:
    js = julia["receipts"]["J1_path_ordered_sp1_transport"]
    ps = jax["receipts"]["P1_path_ordered_sp1_transport"]
    ju = julia["receipts"]["J3_abelian_u1_contrast"]
    pu = jax["receipts"]["P3_abelian_u1_contrast"]
    jst = julia["receipts"]["J2_small_loop_leading_stokes_boundary"]
    pst = jax["receipts"]["P2_small_loop_leading_stokes_boundary"]
    rows = {
        "commutator_gap": numeric_pair(js["commutator_gap"], ps["commutator_gap"]),
        "difference_from_committed_gap": numeric_pair(js["difference_from_committed_gap"], ps["difference_from_committed_gap"]),
        "u1_max_abs_error": numeric_pair(max(row["abs_error"] for row in ju["rows"]), max(row["abs_error"] for row in pu["rows"])),
        "small_loop_finest_distance": numeric_pair(jst["rows"][-1]["distance"], pst["rows"][-1]["distance"]),
        "coarse_raw_norm_drift": numeric_pair(js["coarse_integration_control"]["raw_norm_drift"], ps["coarse_integration_control"]["raw_norm_drift"]),
    }
    max_divergence = max(row["abs_diff"] for row in rows.values())
    return {
        "julia_authoritative": True,
        "engine_values": {
            "julia": {key: row["julia"] for key, row in rows.items()},
            "jax": {key: row["jax"] for key, row in rows.items()},
        },
        "comparison": rows,
        "max_divergence": max_divergence,
    }


def require_gate(condition: bool, name: str, details: Any) -> dict[str, Any]:
    return {"pass": bool(condition), "gate": name, "details": details}


def tool_call_coverage(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for engine, payload in payloads.items():
        claim_tools = set(str(tool) for tool in payload.get("claim_path_tools", []))
        called = set(str(row.get("tool")) for row in payload.get("tool_calls", []))
        rows[engine] = {
            "claim_path_tools": sorted(claim_tools),
            "called_tools": sorted(called),
            "claim_tools_have_calls": claim_tools <= called,
            "unique_tool_call_rows": len(called) == len(payload.get("tool_calls", [])),
        }
    return rows


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    payloads = {"julia": julia, "jax": jax}
    j_sp1 = julia["receipts"]["J1_path_ordered_sp1_transport"]
    p_sp1 = jax["receipts"]["P1_path_ordered_sp1_transport"]
    j_smt = julia["proofs"]["J4_computed_inverse_identity_smt"]
    p_smt = jax["proofs"]["P4_computed_inverse_identity_smt"]
    div = divergence(julia, jax)
    call_cov = tool_call_coverage(payloads)
    pin_hashes = {payload["pin_sha256"] for payload in payloads.values()}
    parent_hashes = {json.dumps(payload["parent_lineage"]["sha256"], sort_keys=True) for payload in payloads.values()}
    gates = {
        "legs_exit_0_by_receipt": require_gate(
            all(payload["all_pass"] is True for payload in payloads.values()),
            "legs_exit_0_by_receipt",
            {engine: payload["all_pass"] for engine, payload in payloads.items()},
        ),
        "pin_identical": require_gate(
            len(pin_hashes) == 1 and next(iter(pin_hashes)) == sha256_text(PIN_SPEC),
            "pin_identical",
            sorted(pin_hashes),
        ),
        "parent_lineage_identical": require_gate(
            len(parent_hashes) == 1 and all(payload["parent_lineage"]["read_only"] is True for payload in payloads.values()),
            "parent_lineage_identical",
            {engine: payload["parent_lineage"] for engine, payload in payloads.items()},
        ),
        "source_sha256_current": require_gate(
            all(source_hash_current(payload) for payload in payloads.values()),
            "source_sha256_current",
            {engine: payload["source_path"] for engine, payload in payloads.items()},
        ),
        "ceiling_exact": require_gate(
            all(
                payload["classification"] == CLASSIFICATION
                and payload["promotion_allowed"] is PROMOTION_ALLOWED
                and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
                for payload in payloads.values()
            ),
            "ceiling_exact",
            {engine: [payload["classification"], payload["promotion_allowed"], payload["formal_admission_allowed"]] for engine, payload in payloads.items()},
        ),
        "path_ordered_comparison_row": require_gate(
            j_sp1["pass"] is True
            and p_sp1["pass"] is True
            and abs(j_sp1["commutator_gap"] - COMMITTED_GAP) <= 2.0e-9
            and abs(p_sp1["commutator_gap"] - COMMITTED_GAP) <= 2.0e-9,
            "path_ordered_comparison_row",
            {"julia": j_sp1["commutator_gap"], "jax": p_sp1["commutator_gap"], "committed": COMMITTED_GAP},
        ),
        "small_loop_stokes_boundary": require_gate(
            julia["receipts"]["J2_small_loop_leading_stokes_boundary"]["pass"] is True
            and jax["receipts"]["P2_small_loop_leading_stokes_boundary"]["pass"] is True,
            "small_loop_stokes_boundary",
            {
                "boundary": julia["receipts"]["J2_small_loop_leading_stokes_boundary"]["boundary"],
                "julia_finest": julia["receipts"]["J2_small_loop_leading_stokes_boundary"]["rows"][-1],
                "jax_finest": jax["receipts"]["P2_small_loop_leading_stokes_boundary"]["rows"][-1],
            },
        ),
        "abelian_u1_contrast": require_gate(
            julia["receipts"]["J3_abelian_u1_contrast"]["pass"] is True
            and jax["receipts"]["P3_abelian_u1_contrast"]["pass"] is True,
            "abelian_u1_contrast",
            {"julia_rows": julia["receipts"]["J3_abelian_u1_contrast"]["rows"], "jax_rows": jax["receipts"]["P3_abelian_u1_contrast"]["rows"]},
        ),
        "controls_fired": require_gate(
            all(payload["controls"]["zero_curvature_identity"]["pass"] is True for payload in payloads.values())
            and all(payload["controls"]["reverse_loop_inverse"]["pass"] is True for payload in payloads.values())
            and all(payload["controls"]["coarse_integration_visible_drift"]["raw_norm_drift"] > 1.0e-3 for payload in payloads.values()),
            "controls_fired",
            {engine: payload["controls"] for engine, payload in payloads.items()},
        ),
        "smt_flip": require_gate(
            j_smt["z3_verdict"] == "unsat"
            and j_smt["z3_erased_flip_control"] == "sat"
            and p_smt["z3_verdict"] == "unsat"
            and p_smt["cvc5_verdict"] == "unsat"
            and p_smt["z3_erased_flip_control"] == "sat"
            and p_smt["cvc5_erased_flip_control"] == "sat",
            "smt_flip",
            {"julia": j_smt, "jax": p_smt},
        ),
        "cross_engine_numeric_divergence_bounded": require_gate(
            div["max_divergence"] <= 2.0e-9,
            "cross_engine_numeric_divergence_bounded",
            div,
        ),
        "tool_calls_one_to_one": require_gate(
            all(row["claim_tools_have_calls"] and row["unique_tool_call_rows"] for row in call_cov.values()),
            "tool_calls_one_to_one",
            call_cov,
        ),
    }
    all_pass = all(gate["pass"] for gate in gates.values())
    engines = {engine: engine_record(payload, JULIA_RESULT if engine == "julia" else JAX_RESULT) for engine, payload in payloads.items()}
    return {
        "schema_version": "three_engine_sim_result_v1",
        "name": "geo_s9_quat_path_ordered_transport_v0",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "Scratch diagnostic path-ordered BPST Sp(1) transport for the quaternionic Hopf S7->S4 row, including same-plane comparison with the committed algebraic gap, leading-order small-loop curvature check, and abelian U(1) contrast.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "stage_movement_allowed": STAGE_MOVEMENT_ALLOWED,
        "all_pass": bool(all_pass),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "parent_lineage": julia["parent_lineage"],
        "claim_ceiling": "scratch_diagnostic only; validates a bounded path-ordered transport diagnostic, not continuum holonomy admission, not formal geometry promotion, not bridge/axis/physics evidence",
        "allowed_claims": [
            "the two explicit BPST rectangular loops in parent planes have computed path-ordered Sp(1) holonomies",
            "for calibrated transported theta=pi/3 loops, the transported commutator gap agrees with the parent algebraic gap within the stated numeric tolerance",
            "small-loop transport agrees with exp(curvature area) to leading order only",
            "the S2 U(1) contrast reproduces committed lifted holonomy values because U(1) path ordering collapses",
        ],
        "out_of_scope": [
            "full nonabelian Stokes theorem",
            "surface-ordered holonomy proof",
            "global continuum holonomy claim",
            "canonical/admitted geometry status",
            "physics, bridge, axis, or manifold promotion",
        ],
        "demotion_condition": "demote to failed diagnostic if source hashes drift, peer-result reads appear, loop convention changes, gap tolerance fails, small-loop leading-order check fails, or flat/reverse/coarse controls stop firing",
        "next_lego_target": "a narrower surface-ordered small-patch Stokes scout with independently parameterized surfaces, still below promotion",
        "promotion_condition": "none in this packet; promotion_allowed=false by construction",
        "blocked_until": "full nonabelian Stokes or continuum holonomy wording remains blocked until a separate surface-ordered proof/sim exists",
        "engine_contract": {
            "mode": "julia_differentialequations_plus_python_high_order_diagnostic",
            "lanes": ["julia", "jax"],
            "pytorch": {"status": "excluded", "reason": "no tensor/autograd/PyTorch claim path is scoped for this transport packet"},
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": julia.get("julia_project"),
            "proof_tag": "bpst_sp1_path_ordered_transport_same_plane_gap",
            "proof_pass": julia["all_pass"],
            "consumer_policy": "consume only as scratch diagnostic transport evidence with parent caveat boundary preserved",
        },
        "foreign_runtime_manifest": {
            "julia": {"packages": julia["packages_used"], "role": "DifferentialEquations transport owner and Z3 identity check"},
            "jax": {"packages": jax["packages_used"], "role": "Python DOP853 high-order independent transport plus z3/cvc5 identity checks"},
            "pytorch": {"status": "excluded", "role": "not scoped"},
        },
        "engines": engines,
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
                "verdict": p_smt["z3_verdict"],
                "load_bearing": True,
                "proofs": {
                    "positive_identity": p_smt["z3_verdict"],
                    "erased_flip_control": p_smt["z3_erased_flip_control"],
                },
            },
            "cvc5": {
                "ran": True,
                "verdict": p_smt["cvc5_verdict"],
                "load_bearing": True,
                "proofs": {
                    "positive_identity": p_smt["cvc5_verdict"],
                    "erased_flip_control": p_smt["cvc5_erased_flip_control"],
                },
            },
            "julia_z3": {
                "ran": True,
                "verdict": j_smt["z3_verdict"],
                "load_bearing": True,
                "proofs": j_smt,
            },
        },
        "gate_pass": gates,
        "divergence": div,
        "claim_path_tools": collect_claim_tools(payloads),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {"tool": "json", "surface": "envelope assembly", "status": "used"},
            {"tool": "hashlib", "surface": "source/result/lineage hash checks", "status": "used"},
            {"tool": "pathlib", "surface": "deterministic path binding", "status": "used"},
        ],
        "seed_ledger": {"rng": "none", "deterministic_rows": ["explicit loops", "deterministic ODE tolerances", "finite SMT constants"]},
        "builder_self_check_is_evidence": False,
        "validator_expected_command": "SIM_PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 $SIM_PY scripts/validate_three_engine_sim_result.py system_v6/sims/geo_s9_quat_path_ordered_transport_v0/results/geo_s9_quat_path_ordered_transport_v0_envelope_results.json --require-source-backed",
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
