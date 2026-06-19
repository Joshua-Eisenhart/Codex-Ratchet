#!/usr/bin/env python3
"""Build helper-backed envelope for render_layer_readout_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import render_layer_readout_v0_common as common


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
JAX_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json"
PYTORCH_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json"
JULIA_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_julia_results.json"
AUDIT_VERDICT = common.SIM_DIR / "audit_verdict.md"

sys.path.insert(0, str(common.ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


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
    boundary = jax["axis0_boundary"]["boundary_verdict"]
    boundary_flags = {
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "packet_audit_verdict_absent": not AUDIT_VERDICT.exists(),
        "file_disjoint_packet": True,
        "builder_surface_no_audit_verdict": True,
    }
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
        "render_error_update_finite": jax["build_gates"]["finite_render_error_update_objects"],
        "own_readout_question_answered": boundary["relation_to_axis0_phi"]
        in {"same_distinction_alias_into_axis0", "different_distinction_from_axis0", "falsifier"},
        "decorative_falsifier_recorded": boundary["verdict"] != "decorative_on_this_carrier"
        or boundary["same_as_axis0_alias_tuple"] is True,
        "controls_recorded": (
            boundary["controls_pass"] is True
            or boundary["relation_to_axis0_phi"] == "falsifier"
        ),
        "julia_z3_agrees": julia["crossover_proofs"]["julia_z3"]["verdict"] == "unsat",
        "z3_cvc5_agree": jax["crossover_proofs"]["z3"]["verdict"] == jax["crossover_proofs"]["cvc5"]["verdict"] == "unsat",
        "builder_audit_boundary_ok": not builder_audit_boundary_errors(boundary_flags, AUDIT_VERDICT),
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
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "claim": "finite render/error/update trajectory and render-polarity readout boundary on the committed carrier",
        "allowed_claims": jax["allowed_claims"],
        "disallowed_claims": jax["disallowed_claims"],
        "authority_binding": {
            "owner_doctrine": "system_v6/receipts/owner_doctrine_holodeck_render_layer_20260612.md",
            "cp12_exclusion_commit": "7c839050c",
            "holodeck_deepread": "system_v6/receipts/holodeck_model_deepread_20260612.md",
            "gate_order_satisfied_commit": "4ef6cf0d8",
        },
        "carrier_binding": jax["carrier"],
        "trajectory": jax["trajectory"],
        "render_readout": jax["render_readout"],
        "axis0_boundary": jax["axis0_boundary"],
        "controls": jax["controls"],
        "counts": jax["counts"],
        "build_gates": gates,
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
                "render_polarity_boundary_against_axis0",
                "control_bound_scratch_diagnostic",
            ],
            "engine_tool_intent": {
                "jax": jax["package_observables"],
                "pytorch": pytorch["package_observables"],
                "julia": julia["package_observables"],
            },
        },
        "validator_expected_commands": [
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/render_layer_readout_v0/render_layer_readout_v0_jax.py",
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/render_layer_readout_v0/render_layer_readout_v0_pytorch.py",
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/render_layer_readout_v0/render_layer_readout_v0_julia.jl",
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/render_layer_readout_v0/render_layer_readout_v0_envelope.py",
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/render_layer_readout_v0/validate_render_layer_readout_v0.py",
        ],
    }
    envelope = build_envelope(
        sim_id=common.SIM_ID,
        lanes={"jax": lane_record(jax), "pytorch": lane_record(pytorch), "julia": lane_record(julia)},
        expected_lanes=("julia", "jax", "pytorch"),
        mode="all_three_render_layer_readout_candidate",
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
            "cp12_exclusion": "7c839050c:system_v6/receipts/owner_doctrine_holodeck_render_layer_20260612.md",
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
