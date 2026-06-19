#!/usr/bin/env python3
"""Build helper-backed envelope for render_layer_readout_v1."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import render_layer_readout_v1_boundary as boundary
import render_layer_readout_v1_common as common


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
JAX_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json"
PYTORCH_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json"
JULIA_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_julia_results.json"

sys.path.insert(0, str(common.ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402


classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "build_three_engine_envelope": {"tried": True, "used": True, "reason": "constructs the standard three-engine envelope"},
    "render_layer_readout_v1_boundary": {"tried": True, "used": True, "reason": "gates the envelope with packet-local boundary checks"},
}
TOOL_INTEGRATION_DEPTH = {"build_three_engine_envelope": "load_bearing", "render_layer_readout_v1_boundary": "supportive"}


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
        "tool_calls": payload.get("tool_calls", []),
        "observables": payload["build_gates"],
    }


def build_result() -> dict[str, Any]:
    jax = load(JAX_RESULT)
    pytorch = load(PYTORCH_RESULT)
    julia = load(JULIA_RESULT)
    sign_hashes = {
        "jax": jax["computed_hashes"]["render_sign_vector_sha256"],
        "pytorch": pytorch["computed_hashes"]["render_sign_vector_sha256"],
        "julia": julia["computed_hashes"]["render_sign_vector_sha256"],
    }
    max_divergence = 0 if len(set(sign_hashes.values())) == 1 else 1
    core_errors = boundary.boundary_errors(jax, common.SIM_DIR)
    gates = {
        "jax_lane_pass": jax["all_pass"] is True,
        "pytorch_lane_pass": pytorch["all_pass"] is True,
        "julia_lane_pass": julia["all_pass"] is True,
        "lane_hashes_match": max_divergence == 0,
        "scratch_no_promotion": all(
            payload["classification"] == "scratch_diagnostic"
            and payload["promotion_allowed"] is False
            and payload["formal_admission_allowed"] is False
            for payload in [jax, pytorch, julia]
        ),
        "boundary_helper_ok": not core_errors,
        "old_pin_regression_refused": jax["controls"]["v0_old_pin_regression"]["readout_table_ran"] is False,
        "scrambled_error_breaks": jax["controls"]["scrambled_error"]["breaks_polarity"] is True,
        "z3_cvc5_agree": jax["crossover_proofs"]["z3"]["verdict"] == jax["crossover_proofs"]["cvc5"]["verdict"] == "unsat",
        "julia_z3_agrees": julia["crossover_proofs"]["julia_z3"]["verdict"] == "unsat",
    }
    all_pass = all(gates.values())
    extra_fields = {
        "schema": f"{common.SIM_ID}_envelope_v1",
        "source_path": common.rel(SOURCE_PATH),
        "source_sha256": common.sha256_file(SOURCE_PATH),
        "result_path": common.rel(RESULT_PATH),
        "all_pass": all_pass,
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "classification": common.CLASSIFICATION,
        "claim_ceiling": common.CLAIM_CEILING,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "file_disjoint_packet": True,
        "claim": "v1 re-pinned finite render/update polarity readout boundary on the committed carrier",
        "allowed_claims": jax["allowed_claims"],
        "disallowed_claims": jax["disallowed_claims"],
        "authority_binding": {
            "v0_audit_verdict": "system_v6/sims/render_layer_readout_v0/audit_verdict.md",
            "owner_doctrine": "system_v6/receipts/owner_doctrine_holodeck_render_layer_20260612.md",
            "cover_v1_pattern": "system_v6/sims/fiber_augmented_cover_v1/build_card.md",
        },
        "construction_status": jax["construction_status"],
        "readout_table_ran": jax["readout_table_ran"],
        "repin_reachability_gate": jax["repin_reachability_gate"],
        "polarity_pin": jax["polarity_pin"],
        "machinery_reuse": jax["machinery_reuse"],
        "carrier": jax["carrier"],
        "trajectory": jax["trajectory"],
        "render_readout": jax["render_readout"],
        "axis0_boundary": jax["axis0_boundary"],
        "controls": jax["controls"],
        "counts": jax["counts"],
        "build_gates": gates,
        "boundary_helper_errors": core_errors,
        "computed_hashes": {
            "lane_render_sign_vector_sha256": sign_hashes,
            "trajectory_sha256": jax["computed_hashes"]["trajectory_sha256"],
            "axis0_boundary_sha256": jax["computed_hashes"]["axis0_boundary_sha256"],
        },
        "TOOL_MANIFEST": {
            **jax["TOOL_MANIFEST"],
            **pytorch["TOOL_MANIFEST"],
            **julia["TOOL_MANIFEST"],
            "build_three_engine_envelope": {
                "tried": True,
                "used": True,
                "reason": "load-bearing standard controller envelope construction",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            **jax["TOOL_INTEGRATION_DEPTH"],
            **pytorch["TOOL_INTEGRATION_DEPTH"],
            **julia["TOOL_INTEGRATION_DEPTH"],
            "build_three_engine_envelope": "load_bearing",
        },
        "tool_intent": {
            "claim_classes": [
                "finite_render_error_update_packet",
                "two_sided_render_polarity_reachability_gate",
                "render_polarity_boundary_against_axis0",
                "control_bound_scratch_diagnostic",
            ],
            "engine_tool_intent": {
                "jax": jax["package_observables"],
                "pytorch": pytorch["package_observables"],
                "julia": julia["package_observables"],
            },
        },
    }
    envelope = build_envelope(
        sim_id=common.SIM_ID,
        lanes={"jax": lane_record(jax), "pytorch": lane_record(pytorch), "julia": lane_record(julia)},
        expected_lanes=("julia", "jax", "pytorch"),
        mode="all_three_render_layer_readout_candidate_v1_repin",
        claim_path_tools=["networkx", "sympy", "z3", "cvc5", "torch.func", "torch_geometric", "Graphs", "Z3", "build_three_engine_envelope"],
        crossover_proofs={**jax["crossover_proofs"], "julia_z3": julia["crossover_proofs"]["julia_z3"]},
        divergence={
            "julia_authoritative": True,
            "engine_values": sign_hashes,
            "max_divergence": max_divergence,
            "verdict": "aligned" if max_divergence == 0 else "diverged",
        },
        classification="scratch_diagnostic",
        promotion_allowed=False,
        formal_admission_allowed=False,
        parent_lineage={
            "committed_carrier": "system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_envelope_results.json",
            "v0_kill_audit": "system_v6/sims/render_layer_readout_v0/audit_verdict.md",
        },
        stability_pairs=[
            ("render_sign_vector", sign_hashes["jax"]),
            ("axis0_boundary", jax["computed_hashes"]["axis0_boundary_sha256"]),
        ],
        extra_fields=extra_fields,
    )
    envelope["all_pass"] = all_pass
    return envelope


def main() -> int:
    result = build_result()
    common.write_json(RESULT_PATH, result)
    print(json.dumps({"result_path": common.rel(RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
