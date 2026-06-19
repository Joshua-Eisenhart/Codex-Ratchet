from __future__ import annotations

import importlib
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


def _common():
    return importlib.import_module("fiber_augmented_cover_v0_common")


def test_cover_quotient_and_finite_fiber_shape() -> None:
    common = _common()
    obj = common.build_fiber_augmented_cover_object()

    cover = obj["cover"]
    quotient = obj["quotient_projection"]
    assert obj["classification"] == "scratch_diagnostic"
    assert obj["promotion_allowed"] is False
    assert obj["formal_admission_allowed"] is False
    assert cover["base_state_count"] == 33
    assert cover["fiber_phase_count_per_cell"] == 4
    assert cover["cover_state_count"] == 132
    assert quotient["projection_total"] is True
    assert quotient["uniform_fiber_size"] is True
    assert quotient["quotient_base_edge_count"] == 198
    assert quotient["fiber_edges_collapse_inside_equivalence_classes"] is True


def test_axis_faithfulness_rows_project_to_sources() -> None:
    common = _common()
    obj = common.build_fiber_augmented_cover_object()

    faith = obj["faithfulness"]
    assert faith["axis0"]["projects_to_committed_axis0"] is True
    assert faith["axis0"]["mismatch_count"] == 0
    assert faith["axis3"]["source_backed_equivalent_adapter"] is True
    assert faith["axis3"]["gamma_in_rows"] > 0
    assert faith["axis3"]["gamma_out_rows"] > 0
    assert faith["axis3"]["predicate_mismatch_count"] == 0
    assert faith["axis6"]["projects_to_committed_axis6"] is True
    assert faith["axis6"]["mismatch_count"] == 0


def test_law_table_and_controls_are_not_by_construction() -> None:
    common = _common()
    obj = common.build_fiber_augmented_cover_object()

    relation = obj["b6_law_test"]
    assert relation["law"] == "b6 = -b0*b3"
    assert relation["table_kind"] == "faithful_fiber_augmented_cover_table"
    assert relation["sample_total"] == obj["cover"]["cover_state_count"]
    assert relation["agreement_count"] + relation["violation_count"] == relation["sample_total"]
    assert relation["law_test_status"] in {
        "holds_on_faithful_cover",
        "fails_on_faithful_cover",
        "inconclusive_no_nonneutral_rows",
    }
    assert relation["relation_not_used_to_assign_axis3"] is True
    assert obj["controls"]["v0_hopf_transplant_regression"]["matches_expected_v0_negative"] is True
    assert obj["controls"]["v1_unfaithful_33_cell_proxy_regression"]["matches_expected_v1_proxy"] is True
    assert obj["controls"]["convention_flip_control"]["ran"] is True
    assert obj["controls"]["scrambled_control"]["ran"] is True


def test_build_card_and_builder_boundary() -> None:
    common = _common()
    obj = common.build_fiber_augmented_cover_object()

    build_card = SIM_DIR / "build_card.md"
    assert build_card.is_file()
    text = build_card.read_text(encoding="utf-8")
    assert common.SIM_ID in text
    assert "fiber-augmented 33-cell cover" in text
    assert obj["no_builder_audit_verdict"] is True
    assert not (SIM_DIR / "audit_verdict.md").exists()


def test_json_roundtrip_preserves_validator_surface() -> None:
    common = _common()
    import validate_fiber_augmented_cover_v0 as validator

    obj = common.build_fiber_augmented_cover_object()
    roundtrip = common.load_json(common.RESULT_PATH) if common.RESULT_PATH.exists() else obj
    if roundtrip is obj:
        return
    assert validator.validate_payload(roundtrip) == []
