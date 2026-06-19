#!/usr/bin/env python3
"""Build the three-engine envelope for ECD.06."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import ecd06_prediction_first_inference_v2_common as common


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.ENVELOPE_PATH
JAX_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json"
PYTORCH_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json"
JULIA_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_julia_results.json"

sys.path.insert(0, str(common.ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def lane_record(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_path": payload["source_path"],
        "result_path": payload["result_path"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "package_observables": payload["package_observables"],
        "all_pass": payload["all_pass"],
        "role_id": payload["role_id"],
        "claim_path_tools": payload["claim_path_tools"],
        "package_smoke": payload.get("package_smoke", {}),
    }


def build_result() -> dict[str, Any]:
    base = common.load_json(common.RESULT_PATH)
    jax = load(JAX_RESULT)
    pytorch = load(PYTORCH_RESULT)
    julia = load(JULIA_RESULT)
    lane_errors = {
        "julia": 0.0 if julia["all_pass"] else 1.0,
        "jax": abs(float(jax["discriminator"]["qit_minus_baseline_adjusted_error_margin"])),
        "pytorch": abs(float(pytorch["discriminator"]["qit_minus_baseline_adjusted_error_margin"])),
    }
    max_divergence = 0.0 if jax["discriminator"] == pytorch["discriminator"] and julia["all_pass"] else 1.0
    gates = {
        "base_pass": base["all_pass"] is True,
        "jax_lane_pass": jax["all_pass"] is True,
        "pytorch_lane_pass": pytorch["all_pass"] is True,
        "julia_lane_pass": julia["all_pass"] is True,
        "jax_pytorch_discriminator_match": jax["discriminator"] == pytorch["discriminator"],
        "scratch_no_promotion": all(
            payload.get("classification") == "scratch_diagnostic"
            and payload.get("promotion_allowed") is False
            and payload.get("formal_admission_allowed") is False
            for payload in [base, jax, pytorch, julia]
        ),
        "boundary_helper_ok": common.builder_audit_boundary_ok(common.SIM_DIR / "audit_verdict.md"),
        "no_identity_leak_pass": base["controls"]["no_identity_leak"]["status"] == "pass",
        "baseline_positive_predicate": base["baseline_side"]["baseline_able_to_win_positive_predicate"] is True,
        "information_parity_pass": base["information_parity_gate"]["parity_passed"] is True,
        "render_access_negative_control_pass": base["controls"]["v1_render_access_regression_equalizer"]["tie_reproduced"] is True,
    }
    all_pass = all(gates.values())
    extra_fields = {
        "schema": common.ENVELOPE_SCHEMA_VERSION,
        "source_path": common.rel(SOURCE_PATH),
        "source_sha256": common.sha256_file(SOURCE_PATH),
        "result_path": common.rel(RESULT_PATH),
        "all_pass": all_pass,
        "classification": common.CLASSIFICATION,
        "claim_ceiling": common.CLAIM_CEILING,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "file_disjoint_packet": True,
        "claim": "ECD.06 prediction-first typed-error discriminator over committed render v1 edge trajectories",
        "authority": base["authority"],
        "status": base["status"],
        "discriminator_refused": base["discriminator_refused"],
        "regime_validity_gate": base["regime_validity_gate"],
        "information_parity_gate": base["information_parity_gate"],
        "source_locks": base["source_locks"],
        "trajectory_pin": base["trajectory_pin"],
        "metric_pin": base["metric_pin"],
        "qit_side_summary": {
            "best_policy_id": base["qit_side"]["best_policy_id"],
            "best_adjusted_error": base["qit_side"]["best_adjusted_error"],
        },
        "qit_side": base["qit_side"],
        "baseline_side_summary": {
            "best_fair_policy_id": base["baseline_side"]["best_fair_policy_id"],
            "best_fair_adjusted_error": base["baseline_side"]["best_fair_adjusted_error"],
            "best_raw_policy_id": base["baseline_side"]["best_raw_policy_id"],
            "v0_killer_included": base["baseline_side"]["v0_killer_included"],
            "train_selected_policy_id": base["baseline_side"]["train_selected_policy_id"],
            "train_selected_adjusted_error": base["baseline_side"]["train_selected_adjusted_error"],
            "candidates": base["baseline_side"]["candidates"],
        },
        "baseline_side": base["baseline_side"],
        "discriminator": base["discriminator"],
        "stability_rows": base["stability_rows"],
        "controls": base["controls"],
        "build_gates": gates,
        "allowed_claims": base["allowed_claims"],
        "disallowed_claims": base["disallowed_claims"],
        "TOOL_MANIFEST": common.TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": common.TOOL_INTEGRATION_DEPTH,
    }
    return build_envelope(
        sim_id=common.SIM_ID,
        lanes={
            "julia": lane_record(julia),
            "jax": lane_record(jax),
            "pytorch": lane_record(pytorch),
        },
        mode="all_three_full_sims",
        claim_path_tools=["Graphs", "Z3", "networkx", "sympy", "z3", "cvc5", "torch.func", "torch_geometric"],
        crossover_proofs=base["crossover_proofs"],
        divergence={
            "julia_authoritative": True,
            "engine_values": lane_errors,
            "max_divergence": max_divergence,
        },
        classification=common.CLASSIFICATION,
        promotion_allowed=False,
        formal_admission_allowed=False,
        parent_lineage={
            "render_layer_readout_v1": "system_v6/sims/render_layer_readout_v1/results/render_layer_readout_v1_envelope_results.json",
            "ecd_registry": "system_v6/receipts/engine_capability_differentiators_20260612.md",
            "ecd_supplement_1": "system_v6/receipts/ecd_registry_supplement_1_20260612.md",
        },
        stability_pairs=[
            ("base_result", common.sha256_file(common.RESULT_PATH)),
            ("jax_result", common.sha256_file(JAX_RESULT)),
            ("pytorch_result", common.sha256_file(PYTORCH_RESULT)),
            ("julia_result", common.sha256_file(JULIA_RESULT)),
        ],
        extra_fields=extra_fields,
    )


def main() -> int:
    result = build_result()
    common.write_json(RESULT_PATH, result)
    print(json.dumps({"result_path": common.rel(RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
