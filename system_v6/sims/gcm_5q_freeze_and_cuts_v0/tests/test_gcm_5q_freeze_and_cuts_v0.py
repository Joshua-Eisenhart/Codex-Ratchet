from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_5q_freeze_and_cuts_v0"
RESULT = SIM_DIR / "results" / f"{SIM_ID}_results.json"
REGISTRY = SIM_DIR / "results" / f"{SIM_ID}_registry.json"
VALIDATOR = SIM_DIR / "results" / f"{SIM_ID}_validator_results.json"
LINEAGE_FREE = SIM_DIR / "results" / f"{SIM_ID}_lineage_free_negative.json"
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"


def load_common():
    common_path = SIM_DIR / f"{SIM_ID}_common.py"
    assert common_path.is_file(), f"missing common module: {common_path}"
    spec = importlib.util.spec_from_file_location(f"{SIM_ID}_common", common_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_card_declares_5q_lean_cut_surface() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for required in (
        SIM_ID,
        "5Q freeze/registry",
        "Cl(10)",
        "1024",
        "547",
        "9",
        "15",
        "cut_state_available=true",
        "hash-per-(survivor,cut)",
        "sample full reduced matrices",
        "scratch_diagnostic",
        "NO git add/commit",
    ):
        assert required in text


def test_packet_builds_5q_registry_and_lean_cut_hash_map() -> None:
    common = load_common()
    packet = common.build_packet(write=False)
    registry = common.build_5q_registry(
        common.load_json(common.FIVE_Q_CARVE_RESULT),
        common.load_json(common.FOUR_Q_FREEZE_REGISTRY),
    )

    assert packet["classification"] == "scratch_diagnostic"
    assert packet["promotion_allowed"] is False
    assert packet["formal_admission_allowed"] is False
    assert packet["cut_state_available"] is True
    assert packet["lean_storage_policy"]["full_all_survivor_cut_matrices_stored"] is False
    assert registry["gcm_5q_object_id"].startswith("gcm5qobj_")
    assert registry["counts"]["candidate_count"] == 556
    assert registry["counts"]["survivor_count"] == 547
    assert registry["counts"]["killed_count"] == 9
    assert registry["counts"]["quotient_class_count"] == 9
    assert registry["counts"]["candidate_region_count"] == 9
    assert registry["counts"]["product_lift_survivor_count"] == 546
    assert registry["counts"]["five_partite_entangled_survivor_count"] == 1

    evidence = packet["cut_state_available_evidence"]
    assert evidence["cut_count"] == 15
    assert evidence["hash_pair_count"] == 547 * 15
    assert evidence["sample_candidate_count"] == len(common.SAMPLE_LABELS)
    assert evidence["sample_cut_pair_count"] == len(common.SAMPLE_LABELS) * 15


def test_hash_rows_do_not_store_full_matrices_but_sample_does() -> None:
    common = load_common()
    packet = common.build_packet(write=False)

    rows = packet["cut_tables"]["survivor_cut_hash_rows"]
    assert len(rows) == 547
    for row in rows[:8] + rows[-8:]:
        assert row["cut_state_available"] is True
        assert row["full_reduced_matrices_stored"] is False
        assert set(row["cuts"]) == set(common.CUTS)
        for cut in row["cuts"].values():
            assert "rho_left_hash" in cut
            assert "rho_right_hash" in cut
            assert "rho_left" not in cut
            assert "rho_right" not in cut

    sample = packet["cut_tables"]["sample_cut_matrix_pairs"]
    assert [row["candidate_label"] for row in sample] == common.SAMPLE_LABELS
    assert {row["survives"] for row in sample} == {True, False}
    for row in sample:
        assert set(row["cuts"]) == set(common.CUTS)
        for cut in row["cuts"].values():
            assert cut["sample_full_reduced_matrices_stored"] is True
            assert cut["rho_left"]
            assert cut["rho_right"]
            assert cut["rho_left_hash"]
            assert cut["rho_right_hash"]


def test_sample_recompute_mutation_and_substrate_controls() -> None:
    common = load_common()
    packet = common.build_packet(write=False)

    assert packet["controls"]["sample_recompute"]["sample_recompute_pass"] is True
    assert packet["controls"]["sample_recompute"]["checked_sample_cut_pairs"] == len(common.SAMPLE_LABELS) * 15
    assert packet["controls"]["mutation_sensitivity"]["mutation_detected"] is True
    assert packet["controls"]["substrate_positive"]["4Q"]["ok"] is True
    assert packet["controls"]["substrate_negatives"]["4Q"]["lineage_free"]["ok"] is False
    assert packet["controls"]["substrate_negatives"]["4Q"]["lineage_free"]["error_codes"]
    assert packet["controls"]["substrate_negatives"]["4Q"]["stale_4q_lineage"]["ok"] is False


def test_script_writes_results_validator_accepts_and_helper_accepts() -> None:
    run = subprocess.run(
        [SIM_PY, str((SIM_DIR / f"{SIM_ID}_common.py").relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert RESULT.is_file()
    assert REGISTRY.is_file()
    assert LINEAGE_FREE.is_file()

    validator = subprocess.run(
        [SIM_PY, str((SIM_DIR / f"validate_{SIM_ID}.py").relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert validator.returncode == 0, validator.stdout + validator.stderr
    payload = json.loads(VALIDATOR.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["errors"] == []

    helper = subprocess.run(
        [
            SIM_PY,
            "scripts/gcm_substrate_check.py",
            str(RESULT.relative_to(ROOT)),
            "--registry",
            "system_v6/sims/gcm_4q_freeze_and_cuts_v0/results/gcm_4q_freeze_and_cuts_v0_registry.json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )
    assert helper.returncode == 0, helper.stdout + helper.stderr

    guard = json.loads(RESULT.read_text(encoding="utf-8"))["file_size_guard"]
    assert guard["all_files_under_50mb"] is True
