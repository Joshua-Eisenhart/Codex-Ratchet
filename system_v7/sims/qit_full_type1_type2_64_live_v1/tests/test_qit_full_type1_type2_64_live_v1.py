from __future__ import annotations

import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from qit_full_type1_type2_64_live_v1_common import build_core_measurement, build_schedule


def test_schedule_shape() -> None:
    summary = build_core_measurement()["schedule_summary"]
    assert summary["slot_count"] == 64
    assert summary["macro_stage_count"] == 16
    assert summary["substage_count_per_macro"] == 4
    assert summary["type1_slots"] == 32
    assert summary["type2_slots"] == 32
    assert summary["chart_locked_slots"] == 16
    assert summary["runtime_probe_slots"] == 48
    assert len(build_schedule()) == 64


def test_ordered_object_formation_beats_erasure_controls() -> None:
    core = build_core_measurement()
    formation = core["ordered_object_formation"]
    controls = core["negative_controls"]
    assert formation["ordered_accuracy"] == 1.0
    assert formation["min_entropy_drop_bits"] > 0.0
    assert formation["all_entropy_gradients_monotone"]
    assert controls["bag_topology"]["unique_signature_count"] == 1
    assert controls["first_static"]["unique_signature_count"] == 1
    assert controls["bag_topology"]["expected_accuracy"] < formation["ordered_accuracy"]
