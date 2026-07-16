#!/usr/bin/env python3
"""Write the build_three_engine_envelope.py spec for manifold_dynamic_chart_v2."""

from __future__ import annotations

import json
from typing import Any

import manifold_dynamic_chart_v2_common as common


SPEC_PATH = common.SIM_DIR / f"{common.SIM_ID}_envelope_spec.json"
ENVELOPE_PATH = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"


def load_lane(engine: str) -> dict[str, Any]:
    return common.load_json(common.RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")


def lane_spec(engine: str) -> dict[str, Any]:
    result = load_lane(engine)
    return {
        "source_path": result["source_path"],
        "result_path": result["result_path"],
        "reads_peer_result": False,
        "packages_used": result["packages_used"],
        "aligned_packages_load_bearing": result["aligned_packages_load_bearing"],
        "package_observables": result["package_observables"],
        "result_all_pass": result["all_pass"],
        "computed_values": result.get("computed_values", {}),
        "engine_mode": common.ENGINE_MODE,
    }


def hash_from_lane(engine: str, key: str) -> str:
    lane = load_lane(engine)
    return common.stable_sha256(lane["computed_values"][key])


def build_spec() -> dict[str, Any]:
    packet = common.build_packet()
    artifact = common.write_trajectory_artifact(packet)
    lanes = {engine: load_lane(engine) for engine in ("julia", "jax", "pytorch")}
    all_lanes_pass = all(lane.get("all_pass") is True for lane in lanes.values())
    cell_hashes = {engine: hash_from_lane(engine, "cells_by_t") for engine in lanes}
    entropy_hashes = {engine: hash_from_lane(engine, "entropy_by_t") for engine in lanes}
    state_counts = {engine: int(lane["computed_values"]["state_count"]) for engine, lane in lanes.items()}
    row_counts = {engine: int(lane["computed_values"]["state_row_count"]) for engine, lane in lanes.items()}
    consensus = {
        "state_count_agreement": len(set(state_counts.values())) == 1,
        "state_row_count_agreement": len(set(row_counts.values())) == 1,
        "trajectory_signature_agreement": len(set(cell_hashes.values())) == 1,
        "entropy_signature_agreement": len(set(entropy_hashes.values())) == 1,
        "cells_by_t_sha256": cell_hashes,
        "entropy_by_t_sha256": entropy_hashes,
    }
    extra_fields = {
        **packet,
        "schema": f"{common.SIM_ID}_envelope_v1",
        "source_path": common.rel(common.SIM_DIR / "write_envelope_spec.py"),
        "source_sha256": common.sha256_file(common.SIM_DIR / "write_envelope_spec.py"),
        "result_path": common.rel(ENVELOPE_PATH),
        "all_pass": packet["all_pass"] and artifact["sha_verified"] and all_lanes_pass and all([
            consensus["state_count_agreement"],
            consensus["state_row_count_agreement"],
            consensus["trajectory_signature_agreement"],
            consensus["entropy_signature_agreement"],
        ]),
        "engine_lanes": sorted(lanes),
        "engine_consensus": consensus,
        "trajectory_artifact": artifact,
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "validator_expected_commands": [
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/manifold_dynamic_chart_v2/manifold_dynamic_chart_v2_julia.jl",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_dynamic_chart_v2/manifold_dynamic_chart_v2_jax.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_dynamic_chart_v2/manifold_dynamic_chart_v2_pytorch.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_dynamic_chart_v2/write_envelope_spec.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/manifold_dynamic_chart_v2/manifold_dynamic_chart_v2_envelope_spec.json > system_v6/sims/manifold_dynamic_chart_v2/results/manifold_dynamic_chart_v2_envelope_results.json",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_dynamic_chart_v2/validate_manifold_dynamic_chart_v2.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/manifold_dynamic_chart_v2/results/manifold_dynamic_chart_v2_envelope_results.json",
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/manifold_dynamic_chart_v2/tests",
        ],
    }
    rehomed_builder_fields = {
        key: extra_fields.pop(key)
        for key in (
            "classification",
            "formal_admission_allowed",
            "generated_at",
            "promotion_allowed",
            "sim_id",
        )
        if key in extra_fields
    }
    return {
        "sim_id": common.SIM_ID,
        "mode": common.ENGINE_MODE,
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "expected_lanes": ["julia", "jax", "pytorch"],
        "lanes": {
            "julia": lane_spec("julia"),
            "jax": lane_spec("jax"),
            "pytorch": lane_spec("pytorch"),
        },
        "claim_path_tools": [
            "build_three_engine_envelope",
            "axis0_experiment_sweep",
            "relaxation_scale_calibration",
            "family_robust_agreement_threshold",
            "shell_weighted_tv",
            "purity_projective_resets",
            "Graphs",
            "networkx",
            "torch.func",
            "sympy",
            "z3",
            "cvc5",
        ],
        "crossover_proofs": {
            "z3": packet["smt_rows"]["z3"],
            "cvc5": packet["smt_rows"]["cvc5"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": row_counts,
            "max_divergence": max(row_counts.values()) - min(row_counts.values()),
            "tolerance": 0,
            "basis": "state-row count agreement plus stable trajectory/entropy array hashes across Julia/JAX/PyTorch lanes",
        },
        "parent_lineage": {
            key: row["path"]
            for key, row in packet["source_locks"].items()
            if row.get("exists")
        },
        "stability_pairs": [
            {"subtree": "trajectory.cells_by_t", "hash": common.stable_sha256(common.cells_and_entropy_by_t(packet)["cells_by_t"])},
            {"subtree": "entropy_field.rows", "hash": packet["trajectory"]["entropy_signature_sha256"]},
            {"subtree": "dynamic_shell_rows", "hash": packet["trajectory"]["shell_signature_sha256"]},
            {"subtree": "jk_fuzz_rows", "hash": packet["trajectory"]["jk_signature_sha256"]},
            {"subtree": "axis0_experiment_v2.full_sweep_grid", "hash": common.stable_sha256(packet["axis0_experiment_v2"]["full_sweep_grid"])},
            {"subtree": "axis0_experiment_v2.agreement_threshold_rows", "hash": common.stable_sha256(packet["axis0_experiment_v2"]["agreement_threshold_rows"])},
            {"subtree": "axis0_experiment_v2.v1_anchor_disagreement", "hash": common.stable_sha256(packet["axis0_experiment_v2"]["v1_anchor_disagreement"])},
            {"subtree": "v0_regression", "hash": common.stable_sha256(packet["v0_regression"])},
        ],
        **rehomed_builder_fields,
        "extra_fields": extra_fields,
    }


def main() -> int:
    spec = build_spec()
    common.write_json(SPEC_PATH, spec)
    print(json.dumps({"ok": True, "spec_path": common.rel(SPEC_PATH)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
