#!/usr/bin/env python3
"""Contract tests for the source-faithful Type-1 engine v0."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import type1_engine_common as common


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def test_stage_chart_is_exact_type1_extraction() -> None:
    stages = {stage["stage_id"]: stage for stage in common.STAGES}
    assert list(stages) == [
        "TiSe",
        "SeFi",
        "NeTi",
        "FiNe",
        "NiFe",
        "TeNi",
        "FeSi",
        "SiTe",
    ]
    assert stages["TiSe"]["casing"] == "LOSE"
    assert stages["SeFi"]["casing"] == "win"
    assert stages["NeTi"]["casing"] == "WIN"
    assert stages["FiNe"]["casing"] == "lose"
    assert stages["NiFe"]["casing"] == "LOSE"
    assert stages["TeNi"]["casing"] == "lose"
    assert stages["FeSi"]["casing"] == "WIN"
    assert stages["SiTe"]["casing"] == "win"
    assert common.OUTER_LOOP_STAGE_IDS == ["TiSe", "NeTi", "NiFe", "FeSi"]
    assert common.INNER_LOOP_STAGE_IDS == ["SeFi", "SiTe", "TeNi", "FiNe"]


def test_owner_xlsx_annotations_are_labels_only() -> None:
    annotation = common.MBTI_ANNOTATION
    assert annotation["source"] == "owner_xlsx_pre_llm"
    assert annotation["load_bearing"] is False
    by_stage = annotation["by_stage"]
    assert by_stage["TiSe"]["mbti"] == "ISTP"
    assert by_stage["SeFi"]["mbti"] == "ESFP"
    assert by_stage["NeTi"]["mbti"] == "ENTP"
    assert by_stage["FiNe"]["mbti"] == "INFP"
    assert by_stage["NiFe"]["mbti"] == "INFJ"
    assert by_stage["TeNi"]["mbti"] == "ENTJ"
    assert by_stage["FeSi"]["mbti"] == "ESFJ"
    assert by_stage["SiTe"]["mbti"] == "ISTJ"


def test_numpy_leg_emits_required_contract_fields() -> None:
    subprocess.run(["python3", str(HERE / "type1_engine_v0_numpy.py")], check=True, cwd=HERE)
    data = json.loads((RESULTS / "type1_engine_v0_numpy_results.json").read_text())
    assert data["classification"] == "scratch_diagnostic"
    assert data["promotion_allowed"] is False
    assert data["formal_admission_allowed"] is False
    assert data["substrates_queued"] == ["jax", "torch"]
    assert data["distinctness"]["all_8_distinct"] is True
    assert data["distinctness"]["min_pairwise_distance"] > data["distinctness"]["threshold"]
    assert len(data["stage_fingerprints"]) == 8
    assert set(data["order_sensitivity_by_terrain"]) == {"Se-in", "Ne-in", "Ni-in", "Si-in"}


def test_cross_check_records_raw_and_normalized_casing() -> None:
    data = common.build_casing_cross_check()
    assert all(row["normalized_agree"] for row in data)
    raw = {row["stage_id"]: row["raw_case_agree"] for row in data}
    assert raw["TeNi"] is False
    assert all(v is True for k, v in raw.items() if k != "TeNi")
