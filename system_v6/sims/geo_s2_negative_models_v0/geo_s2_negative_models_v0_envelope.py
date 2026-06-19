#!/usr/bin/env python3
"""Three-engine envelope for geo_s2_negative_models_v0."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

from geo_s2_negative_models_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SIM_DIR,
    SIM_ID,
    file_sha256,
    sha256_text,
)


SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from independently regenerated S2 negative receipts",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source hashing and identical PIN checks via common helper",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic result path binding",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


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


def gate(condition: bool, name: str, details: Any) -> dict[str, Any]:
    return {"pass": bool(condition), "gate": name, "details": details}


def build_result() -> dict[str, Any]:
    payloads = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    julia = payloads["julia"]
    jax = payloads["jax"]
    pytorch = payloads["pytorch"]
    pin_hashes = {payload["pin_sha256"] for payload in payloads.values()}
    ceilings_exact = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is PROMOTION_ALLOWED
        and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
        for payload in payloads.values()
    )
    selectivity = jax["selectivity_matrix"]
    proofs = jax["proofs"]
    p_wrong = proofs["wrong_connection_holonomy_nonzero"]
    p_broken = proofs["broken_stokes_residual_nonzero"]
    p_cover = proofs["naive_cover_ratio_exactly_two"]
    proof_flip = (
        p_wrong["z3_assert_wrong_residual_zero"] == "unsat"
        and p_wrong["cvc5_assert_wrong_residual_zero"] == "unsat"
        and p_wrong["z3_positive_control_assert_residual_zero"] == "sat"
        and p_wrong["cvc5_positive_control_assert_residual_zero"] == "sat"
        and p_broken["z3_assert_broken_residual_zero"] == "unsat"
        and p_broken["cvc5_assert_broken_residual_zero"] == "unsat"
        and p_broken["z3_positive_control_assert_residual_zero"] == "sat"
        and p_broken["cvc5_positive_control_assert_residual_zero"] == "sat"
        and p_cover["z3_assert_ratio_not_2"] == "unsat"
        and p_cover["cvc5_assert_ratio_not_2"] == "unsat"
        and p_cover["z3_corrected_assert_ratio_not_1"] == "unsat"
        and p_cover["cvc5_corrected_assert_ratio_not_1"] == "unsat"
    )
    engine_values = {
        engine: float(payload["shared_scalars"]["wrong_connection_max_holonomy_residual"])
        for engine, payload in payloads.items()
    }
    magnitude_rows = {
        engine: payload["shared_scalars"]
        for engine, payload in payloads.items()
    }
    build_gates = {
        "legs_exit_0_by_receipt": gate(
            all(payload["all_pass"] is True for payload in payloads.values()),
            "legs_exit_0_by_receipt",
            {engine: payload["all_pass"] for engine, payload in payloads.items()},
        ),
        "pin_identical": gate(
            len(pin_hashes) == 1 and next(iter(pin_hashes)) == sha256_text(PIN_SPEC),
            "pin_identical",
            sorted(pin_hashes),
        ),
        "ceiling_exact": gate(
            ceilings_exact,
            "ceiling_exact",
            {engine: [payload["classification"], payload["promotion_allowed"], payload["formal_admission_allowed"]] for engine, payload in payloads.items()},
        ),
        "common_adapter_selectivity": gate(
            selectivity["complete"] is True and selectivity["selectivity_pass"] is True,
            "common_adapter_selectivity",
            {
                "predicted_failures": selectivity["predicted_failures"],
                "observed_failures": selectivity["observed_failures"],
            },
        ),
        "positive_control_passes_shared_adapter": gate(
            jax["positive_control"]["pass"] is True and julia["positive_control"]["pass"] is True and pytorch["positive_control"]["pass"] is True,
            "positive_control_passes_shared_adapter",
            {
                "jax": jax["positive_control"]["pass"],
                "julia": julia["positive_control"]["pass"],
                "pytorch": pytorch["positive_control"]["pass"],
            },
        ),
        "raw_value_proofs_flip": gate(
            proof_flip,
            "raw_value_proofs_flip",
            {"wrong_connection": p_wrong, "broken_stokes": p_broken, "naive_cover": p_cover},
        ),
    }
    all_pass = all(item["pass"] for item in build_gates.values())
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": (
            "S2 negative models for wrong connection, broken Stokes pairing, and naive torus cover "
            "fail only the predicted common-adapter receipt families with measured magnitudes; "
            "this is a scratch diagnostic selectivity suite, not a positive S2 claim."
        ),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
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
            "proof_tag": "S2_negative_models_Z3jl_wrong_residual_check",
            "proof_pass": julia["proofs"]["julia_z3_wrong_connection_holonomy"]["pass"],
            "table_version": None,
            "bracket_convention": "not_applicable_connection_flux_foliation_negative_models",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia.get("julia_project"), "packages": julia["packages_used"], "role": "canon negative-model receipt and Z3.jl raw-value check"},
            "jax": {"packages": jax["packages_used"], "role": "vectorized negative suite plus z3/cvc5 proof polarity"},
            "pytorch": {"packages": pytorch["packages_used"], "role": "independent torch.func batched negative-model magnitude recomputation"},
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
                    "wrong_connection_assert_residual_zero": p_wrong["z3_assert_wrong_residual_zero"],
                    "broken_stokes_assert_residual_zero": p_broken["z3_assert_broken_residual_zero"],
                    "naive_cover_assert_ratio_not_2": p_cover["z3_assert_ratio_not_2"],
                    "naive_cover_corrected_assert_ratio_not_1": p_cover["z3_corrected_assert_ratio_not_1"],
                },
                "raw_value_binding": {
                    "wrong_connection_residual_scaled": p_wrong["wrong_residual_scaled"],
                    "broken_stokes_residual_scaled": p_broken["broken_stokes_residual_scaled"],
                    "naive_cover_ratio_num_den": p_cover["ratio_num_den"],
                },
            },
            "cvc5": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "wrong_connection_assert_residual_zero": p_wrong["cvc5_assert_wrong_residual_zero"],
                    "broken_stokes_assert_residual_zero": p_broken["cvc5_assert_broken_residual_zero"],
                    "naive_cover_assert_ratio_not_2": p_cover["cvc5_assert_ratio_not_2"],
                    "naive_cover_corrected_assert_ratio_not_1": p_cover["cvc5_corrected_assert_ratio_not_1"],
                },
                "raw_value_binding": {
                    "wrong_connection_residual_scaled": p_wrong["wrong_residual_scaled"],
                    "broken_stokes_residual_scaled": p_broken["broken_stokes_residual_scaled"],
                    "naive_cover_ratio_num_den": p_cover["ratio_num_den"],
                },
            },
            "julia_z3": {
                "ran": True,
                "verdict": julia["proofs"]["julia_z3_wrong_connection_holonomy"]["z3_assert_wrong_residual_zero"],
                "load_bearing": True,
                "proof": julia["proofs"]["julia_z3_wrong_connection_holonomy"],
            },
        },
        "negative_models": jax["negative_models"],
        "positive_control": jax["positive_control"],
        "selectivity_matrix": selectivity,
        "engine_negative_receipts": {
            "julia": julia["negative_model_receipts"],
            "jax": jax["negative_models"],
            "pytorch": pytorch["negative_model_receipts"],
        },
        "measured_failure_magnitudes": magnitude_rows,
        "build_gates": build_gates,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": max(abs(value - engine_values["julia"]) for value in engine_values.values()),
            "meaning": "cross-engine wrong-connection max holonomy residual disagreement, not a promotion metric",
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
