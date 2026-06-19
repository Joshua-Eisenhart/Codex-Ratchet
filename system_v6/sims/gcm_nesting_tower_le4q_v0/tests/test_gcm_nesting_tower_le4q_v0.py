"""Regression checks for gcm_nesting_tower_le4q_v0."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")

sys.path.insert(0, str(SIM_DIR))

import gcm_nesting_tower_le4q_v0_common as common  # noqa: E402
from validate_gcm_nesting_tower_le4q_v0 import validate_packet  # noqa: E402


def test_packet_counts_and_root_verdict() -> None:
    packet = common.load_json(common.RESULT_PATH)
    counts = packet["counts"]
    assert counts["four_q_survivor_count"] == 546
    assert counts["stored_reduced_matrix_pair_count"] == 546 * 7
    assert counts["exact_all_cut_compatible_4q_count"] + counts["exact_all_cut_orphan_4q_count"] == 546
    assert counts["probe_all_cut_compatible_4q_count"] + counts["probe_all_cut_orphan_4q_count"] == 546
    assert packet["root_axiom_verdict_at_4q"]["root_axiom_verdict_at_4q"] in {"HOLDS", "STRENGTHENS", "BREAKS"}


def test_exact_probe_relations_are_separate() -> None:
    packet = common.load_json(common.RESULT_PATH)
    assert packet["relation_boundary"]["strict_separation"] is True
    sample = packet["compatible_families"]["object_maps_sample"][0]
    for cut_row in sample["cut_relations"].values():
        assert "exact_count" in cut_row["left"]
        assert "probe_count" in cut_row["left"]
        assert "exact_count" in cut_row["right"]
        assert "probe_count" in cut_row["right"]


def test_validator_passes() -> None:
    packet = common.load_json(common.RESULT_PATH)
    assert validate_packet(packet) == []


def test_substrate_helper_accepts_packet() -> None:
    proc = subprocess.run(
        [
            str(SIM_PY),
            "scripts/gcm_substrate_check.py",
            str(common.RESULT_PATH.relative_to(ROOT)),
            "--registry",
            str(common.FOUR_Q_REGISTRY_PATH.relative_to(ROOT)),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_runner_and_validator_cli() -> None:
    run_proc = subprocess.run(
        [str(SIM_PY), str((SIM_DIR / f"{common.SIM_ID}_common.py").relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert run_proc.returncode == 0, run_proc.stdout + run_proc.stderr
    val_proc = subprocess.run(
        [str(SIM_PY), str((SIM_DIR / f"validate_{common.SIM_ID}.py").relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert val_proc.returncode == 0, val_proc.stdout + val_proc.stderr
