from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gcm_nesting_tower_le3q_v0_common import (
    EXPECTED_3Q_PRODUCT_LIFT_COUNT,
    EXPECTED_3Q_SURVIVOR_COUNT,
    RESULT_PATH,
    load_json,
)


def test_counts_partition_generated_result() -> None:
    packet = load_json(RESULT_PATH)
    counts = packet["counts"]
    assert counts["three_q_survivor_count"] == EXPECTED_3Q_SURVIVOR_COUNT
    assert counts["product_lift_3q_count"] == EXPECTED_3Q_PRODUCT_LIFT_COUNT
    assert counts["exact_all_cut_compatible_3q_count"] + counts["exact_all_cut_orphan_3q_count"] == EXPECTED_3Q_SURVIVOR_COUNT
    assert counts["probe_all_cut_compatible_3q_count"] + counts["probe_all_cut_orphan_3q_count"] == EXPECTED_3Q_SURVIVOR_COUNT


def test_all_three_cut_rows_present() -> None:
    packet = load_json(RESULT_PATH)
    for row in packet["object_maps"]:
        assert set(row["cut_relations"]) == {"A|BC", "B|AC", "C|AB"}
        assert all(cut_row["partial_trace_tested"] is True for cut_row in row["cut_relations"].values())


def test_controls_red_and_regression_green() -> None:
    packet = load_json(RESULT_PATH)
    assert packet["controls"]["le2_regression"]["all_counts_reproduced"] is True
    assert packet["controls"]["scrambled_pairing"]["red"] is True
    assert packet["substrate_checks"]["all_positive_ok"] is True
    assert packet["substrate_checks"]["negatives_red"] is True
