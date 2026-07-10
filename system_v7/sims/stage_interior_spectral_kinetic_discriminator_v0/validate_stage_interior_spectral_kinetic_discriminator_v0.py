#!/usr/bin/env python3
"""Fail-closed validator for the finite two-order discriminator packet."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from contract_utils import load_json, sha256, write_json


classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
stage_movement_allowed = False
TOOL_MANIFEST = {
    "numpy": {
        "used": True,
        "reason": "Mechanically verifies NPZ shapes, exact permutations, and exact marginal preservation.",
    },
    "sha256": {
        "used": True,
        "reason": "Binds source, contract, receipt, and assembled-result identities.",
    },
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "sha256": "supportive"}


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC_PATH = HERE / "spec.json"
MANIFEST_PATH = HERE / "artifacts" / "trajectory_contract_v1.json"
NPZ_PATH = HERE / "artifacts" / "trajectory_contract_v1.npz"
PYDMD_PATH = HERE / "receipts" / "pydmd_receipt.json"
DEEPTIME_PATH = HERE / "receipts" / "deeptime_vamp_receipt.json"
RESULT_PATH = HERE / "results" / "stage_interior_spectral_kinetic_discriminator_v0_results.json"
VALIDATION_PATH = HERE / "results" / "stage_interior_spectral_kinetic_discriminator_v0_validation.json"


def main() -> int:
    spec = load_json(SPEC_PATH)
    manifest = load_json(MANIFEST_PATH)
    pydmd = load_json(PYDMD_PATH)
    deeptime = load_json(DEEPTIME_PATH)
    result = load_json(RESULT_PATH)
    with np.load(NPZ_PATH, allow_pickle=False) as data:
        train = data["train_trajectories"]
        heldout = data["heldout_trajectories"]
        control_indices = data["control_indices"]
        orders = data["candidate_orders"].tolist()
        heldout_seeds = data["heldout_seeds"].tolist()

    marginal_controls_exact = True
    permutations_exact = True
    for label in range(heldout.shape[0]):
        for seed_index in range(heldout.shape[1]):
            for probe_index in range(heldout.shape[2]):
                original = heldout[label, seed_index, probe_index]
                for control_index in range(control_indices.shape[2]):
                    indices = control_indices[seed_index, probe_index, control_index]
                    permutations_exact &= np.array_equal(np.sort(indices), np.arange(len(indices)))
                    transformed = original[indices]
                    marginal_controls_exact &= np.array_equal(
                        np.sort(original, axis=0),
                        np.sort(transformed, axis=0),
                    )

    source_hashes_current = all(
        sha256(REPO / relative_path if not relative_path.startswith("spec.json") else HERE / relative_path)
        == expected
        for relative_path, expected in manifest["source_hashes"].items()
    )
    checks = {
        "exactly_two_declared_orders_present": orders == spec["candidate_orders"] and len(orders) == 2,
        "required_competing_orders_present": (
            ["Ti", "Te", "Fi", "Fe"] in orders and ["Ti", "Te", "Fe", "Fi"] in orders
        ),
        "four_operators_are_input_premise_not_latent_dimension": (
            deeptime["model"]["latent_dimension_policy"].startswith("VAMP dim=None")
        ),
        "train_and_heldout_seeds_are_disjoint": set(spec["train_seeds"]).isdisjoint(heldout_seeds),
        "heldout_probe_tensor_is_nonempty": heldout.shape[1] >= 2 and heldout.shape[2] >= 2,
        "train_probe_tensor_is_nonempty": train.shape[1] >= 2 and train.shape[2] >= 2,
        "npz_hash_matches_manifest": sha256(NPZ_PATH) == manifest["npz_sha256"],
        "source_hashes_are_current": source_hashes_current,
        "both_runtime_receipts_bind_same_npz": (
            pydmd["contract"]["npz_sha256"]
            == deeptime["contract"]["npz_sha256"]
            == manifest["npz_sha256"]
        ),
        "pydmd_version_and_interpreter_exact": (
            pydmd["runtime"]["pydmd"] == "2025.8.1"
            and pydmd["runtime"]["launcher"] == "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
            and pydmd["runtime"]["launcher_samefile_as_runtime"] is True
        ),
        "deeptime_version_and_interpreter_exact": (
            deeptime["runtime"]["deeptime"] == "0.4.5"
            and deeptime["runtime"]["launcher"]
            == "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/deeptime-0.4.5-py313/bin/python"
            and deeptime["runtime"]["launcher_samefile_as_runtime"] is True
        ),
        "deeptime_did_not_read_other_lane_outputs": (
            deeptime["input_isolation"]["reads_pydmd_receipt"] is False
            and deeptime["input_isolation"]["reads_assembled_result"] is False
        ),
        "control_indices_are_exact_permutations": bool(permutations_exact),
        "all_controls_preserve_per_trajectory_marginals_exactly": bool(marginal_controls_exact),
        "both_lanes_require_clean_advantage_and_control_collapse": bool(pydmd["lane_pass"] and deeptime["lane_pass"]),
        "assembled_result_passes_all_gates": bool(result["result_pass"] and all(result["gates"].values())),
        "claim_ceiling_exact": result["claim_ceiling"] == spec["claim_ceiling"],
        "all_admission_and_promotion_flags_false": all(
            packet["classification"] == "scratch_diagnostic"
            and packet["promotion_allowed"] is False
            and packet["formal_admission_allowed"] is False
            and packet["stage_movement_allowed"] is False
            for packet in (pydmd, deeptime, result)
        ),
        "blocked_consumers_exact": result["blocked_consumers"] == spec["blocked_consumers"],
    }
    validation = {
        "schema": "codex_ratchet.stage_interior_spectral_kinetic_discriminator.validation.v1",
        "sim_id": spec["sim_id"],
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "validated_files": {
            str(path.relative_to(HERE)): sha256(path)
            for path in (SPEC_PATH, MANIFEST_PATH, NPZ_PATH, PYDMD_PATH, DEEPTIME_PATH, RESULT_PATH)
        },
        "claim_ceiling": spec["claim_ceiling"],
    }
    write_json(VALIDATION_PATH, validation)
    print(json.dumps({"validation": str(VALIDATION_PATH), "all_checks_pass": validation["all_checks_pass"], "checks": checks}))
    return 0 if validation["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
