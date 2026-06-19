#!/usr/bin/env python3
"""Three-engine envelope for geo_s1_negative_models_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_negative_models_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
PIN_SPEC = (
    "geo_s1_negative_models_v0|stage:S1|negative_models:no_conjugate_hopf,"
    "naive_phi_chi_grid,classical_bit|positive_control:true_hopf_corrected_grid_spinor|"
    "classification:scratch_diagnostic|promotion_allowed:false|formal_admission_allowed:false"
)

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from independently regenerated leg receipts",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source hashing and identical PIN checks",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic result path binding",
    },
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
        "shared_scalars": payload.get("shared_scalars", {}),
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def require_gate(condition: bool, name: str, details: Any) -> dict[str, Any]:
    return {"pass": bool(condition), "gate": name, "details": details}


def build_result() -> dict[str, Any]:
    payloads = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    jax = payloads["jax"]
    julia = payloads["julia"]
    pytorch = payloads["pytorch"]
    pin_hashes = {payload["pin_sha256"] for payload in payloads.values()}
    ceilings_exact = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is PROMOTION_ALLOWED
        and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
        for payload in payloads.values()
    )
    proofs = jax["proofs"]
    p1 = proofs["negative_1_orbit_spread_nonzero"]
    p2 = proofs["negative_2_ratio_exactly_two"]
    selectivity = jax["selectivity_matrix"]
    positive = jax["positive_control"]
    engine_values = {
        engine: float(payload["shared_scalars"]["negative_1_orbit_spread"])
        for engine, payload in payloads.items()
    }
    negative_flags = [
        item["negative_model"] is True for item in jax["negative_models"]
    ]
    proof_flip = (
        p1["z3_assert_spread_zero"] == "unsat"
        and p1["cvc5_assert_spread_zero"] == "unsat"
        and p1["z3_true_hopf_control_assert_spread_zero"] == "sat"
        and p1["cvc5_true_hopf_control_assert_spread_zero"] == "sat"
        and p2["z3_assert_ratio_not_2"] == "unsat"
        and p2["cvc5_assert_ratio_not_2"] == "unsat"
        and p2["z3_corrected_assert_ratio_not_1"] == "unsat"
        and p2["cvc5_corrected_assert_ratio_not_1"] == "unsat"
    )
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
        "ceiling_exact": require_gate(
            ceilings_exact,
            "ceiling_exact",
            {engine: [payload["classification"], payload["promotion_allowed"], payload["formal_admission_allowed"]] for engine, payload in payloads.items()},
        ),
        "negative_labels_exact": require_gate(
            len(negative_flags) == 3 and all(negative_flags),
            "negative_labels_exact",
            negative_flags,
        ),
        "selectivity_matrix_complete": require_gate(
            selectivity["complete"] is True and selectivity["selectivity_pass"] is True,
            "selectivity_matrix_complete",
            {
                "observed_failures": selectivity["observed_failures"],
                "predicted_failures": selectivity["predicted_failures"],
            },
        ),
        "positive_control_passes_shared_path": require_gate(
            positive["pass"] is True,
            "positive_control_passes_shared_path",
            positive,
        ),
        "proofs_flip": require_gate(
            proof_flip,
            "proofs_flip",
            {"negative_1": p1, "negative_2": p2},
        ),
    }
    all_pass = all(gate["pass"] for gate in gates.values())
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": (
            "Stage-1 negative foundation models fail only their predicted S1 geometry receipts "
            "with measured magnitudes; this is a scratch diagnostic suite-tooth test, not a claim candidate."
        ),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "audit_surface_note": "JAX leg = primary selectivity surface; Julia and PyTorch legs are envelope-level independent magnitude mirrors.",
        "negative_suite_scope": "shows three named bad models fail as predicted; supports NO positive S1 claim",
        "all_pass": bool(all_pass),
        "negative_model": True,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": julia.get("julia_project"),
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": julia["source_sha256"],
            "receipt_path": julia["result_path"],
            "proof_tag": "S1_negative_models_raw_value_Z3jl_spread_check",
            "proof_pass": julia["proofs"]["julia_z3_negative_1_spread"]["pass"],
            "table_version": None,
            "bracket_convention": "not_applicable_pure_S1_geometry_negative_models",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia.get("julia_project"), "packages": julia["packages_used"], "role": "canon negative-model receipt and Z3.jl raw-value check"},
            "jax": {"packages": jax["packages_used"], "role": "dense vectorized negative suite plus z3/cvc5 proof polarity"},
            "pytorch": {"packages": pytorch["packages_used"], "role": "independent torch.func negative-model magnitude recomputation"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": collect_claim_tools(payloads),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "negative_1_assert_spread_zero": p1["z3_assert_spread_zero"],
                    "negative_1_true_hopf_control_assert_spread_zero": p1["z3_true_hopf_control_assert_spread_zero"],
                    "negative_2_assert_ratio_not_2": p2["z3_assert_ratio_not_2"],
                    "negative_2_corrected_assert_ratio_not_1": p2["z3_corrected_assert_ratio_not_1"],
                },
                "raw_value_binding": {
                    "negative_1_spread_scaled": p1["spread_scaled"],
                    "negative_1_true_hopf_control_spread_scaled": p1["true_hopf_control_spread_scaled"],
                    "negative_2_ratio_num_den": p2["ratio_num_den"],
                    "negative_2_corrected_ratio_num_den": p2["corrected_ratio_num_den"],
                },
            },
            "cvc5": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "negative_1_assert_spread_zero": p1["cvc5_assert_spread_zero"],
                    "negative_1_true_hopf_control_assert_spread_zero": p1["cvc5_true_hopf_control_assert_spread_zero"],
                    "negative_2_assert_ratio_not_2": p2["cvc5_assert_ratio_not_2"],
                    "negative_2_corrected_assert_ratio_not_1": p2["cvc5_corrected_assert_ratio_not_1"],
                },
                "raw_value_binding": {
                    "negative_1_spread_scaled": p1["spread_scaled"],
                    "negative_1_true_hopf_control_spread_scaled": p1["true_hopf_control_spread_scaled"],
                    "negative_2_ratio_num_den": p2["ratio_num_den"],
                    "negative_2_corrected_ratio_num_den": p2["corrected_ratio_num_den"],
                },
            },
            "julia_z3": {
                "ran": True,
                "verdict": julia["proofs"]["julia_z3_negative_1_spread"]["z3_assert_spread_zero"],
                "load_bearing": True,
                "proof": julia["proofs"]["julia_z3_negative_1_spread"],
            },
        },
        "negative_models": jax["negative_models"],
        "positive_control": positive,
        "selectivity_matrix": selectivity,
        "engine_negative_receipts": {
            "julia": julia["negative_model_receipts"],
            "jax": jax["negative_models"],
            "pytorch": pytorch["negative_model_receipts"],
        },
        "build_gates": gates,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": max(abs(value - engine_values["julia"]) for value in engine_values.values()),
            "meaning": "cross-engine negative-1 orbit-spread disagreement, not a promotion metric",
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result_path": str(RESULT_PATH), "engine": "envelope"}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
