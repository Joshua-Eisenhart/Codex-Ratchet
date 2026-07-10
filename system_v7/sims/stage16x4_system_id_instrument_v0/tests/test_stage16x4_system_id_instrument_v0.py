from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_result_and_validator_are_fenced_and_green() -> None:
    result = json.loads((ROOT / "results" / "stage16x4_system_id_instrument_v0_results.json").read_text())
    validator = json.loads(
        (ROOT / "results" / "stage16x4_system_id_instrument_v0_validator_results.json").read_text()
    )
    assert result["all_pass"] is True
    assert validator["all_pass"] is True
    assert validator["checks"]["all_authority_source_hashes_match_live_files"] is True
    assert result["promotion_allowed"] is False
    assert result["formal_admission_allowed"] is False
    assert result["stage_movement_allowed"] is False
    assert result["premise_boundary"]["dual_ratchet_emergence_tested"] is False


def test_counts_are_candidate_scoped() -> None:
    result = json.loads((ROOT / "results" / "stage16x4_system_id_instrument_v0_results.json").read_text())
    aggregate = result["aggregate"]
    assert aggregate["macro_slot_count"] == 16
    assert aggregate["beats_per_one_orientation"] == 64
    assert aggregate["candidate_orientation_count"] == 2
    assert aggregate["candidate_beat_model_count"] == 128
    assert result["package_fingerprint"]["pykoopman"]["full_distribution_admitted"] is False
    for orientation in ("forward", "reverse"):
        rows = result["identity_ablation_clusters"]["by_orientation"][orientation]["rows"]
        assert rows["full"]["cluster_count"] == 16
        assert rows["operator_erased"]["cluster_count"] == 8
        assert rows["terrain_erased"]["cluster_count"] == 4
        assert rows["terrain_and_operator_erased"]["cluster_count"] == 1


def test_authority_inputs_are_hashed() -> None:
    result = json.loads((ROOT / "results" / "stage16x4_system_id_instrument_v0_results.json").read_text())
    hashes = result["source_hashes"]
    required = {
        "system_v4/probes/sim_pysindy_capability.py",
        "system_v4/probes/sim_pykoopman_capability.py",
        "system_v7/sims/stage16x4_system_id_instrument_v0/spec.json",
        "system_v7/sims/stage16x4_system_id_instrument_v0/stage16x4_system_id_instrument_v0.py",
        "system_v7/sims/stage16x4_system_id_instrument_v0/validate_stage16x4_system_id_instrument_v0.py",
        "system_v7/sims/stage16x4_system_id_instrument_v0/lev_verify.flow.yaml",
    }
    assert required <= set(hashes)
    assert all(len(value) == 64 for value in hashes.values())
