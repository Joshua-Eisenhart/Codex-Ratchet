from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


def _common():
    spec = importlib.util.find_spec("fiber_augmented_cover_v2_common")
    assert spec is not None, "fiber_augmented_cover_v2_common module must exist"
    return importlib.import_module("fiber_augmented_cover_v2_common")


def test_cellular_base_commits_sphere_cells_and_fences_dense_graph() -> None:
    common = _common()
    obj = common.build_fiber_augmented_cover_v2_object()
    base = obj["cellular_base"]

    assert obj["classification"] == "scratch_diagnostic"
    assert obj["promotion_allowed"] is False
    assert obj["formal_admission_allowed"] is False
    assert obj["claim_ceiling"].startswith("axis_readout_candidate_only")
    assert base["construction_status"] == "committed_cellular_sphere_mesh"
    assert base["cell_counts"] == {"C0": 33, "C1": 92, "C2": 61}
    assert base["euler_characteristic"] == 2
    assert base["euler_gate_passed"] is True
    assert base["edge_incidence_counts"] == {"2": 92}
    assert base["face_size_counts"] == {"3": 60, "4": 1}
    assert base["committed_seam_loop_cell_ids"] == [20, 17, 12, 15]
    assert base["committed_seam_lifted_steps"] == [1, 1, 1, 0]
    assert base["all_face_transition_sums_close_mod_fiber"] is True
    assert base["v1_dense_graph_relation"]["v1_dense_graph_edge_count"] == 198
    assert base["v1_dense_graph_relation"]["cellular_edge_count"] == 92
    assert base["v1_dense_graph_relation"]["objects_have_different_roles"] is True


def test_degree_one_cover_chain_complex_and_zero_shift_refusal() -> None:
    common = _common()
    obj = common.build_fiber_augmented_cover_v2_object()

    assert obj["cover"]["fiber_phase_count_per_cell"] == 3
    assert obj["cover"]["cover_state_count"] == 99
    assert obj["bundle_witness"]["total_lifted_phase_shift_steps"] == 3
    assert obj["bundle_witness"]["directed_winding"] == 1
    assert obj["bundle_witness"]["nontrivial_gate_passed"] is True
    assert obj["total_space_cellular_structure"]["cell_counts"] == {"C0": 99, "C1": 375, "C2": 459, "C3": 183}
    assert obj["total_space_cellular_structure"]["euler_characteristic"] == 0
    assert obj["total_space_cellular_structure"]["chain_checks"]["d_squared_zero"] is True
    assert obj["total_space_cellular_structure"]["boundary_matrices"]["d1"]["sha256"]
    assert obj["total_space_cellular_structure"]["boundary_matrices"]["d2"]["sha256"]
    assert obj["total_space_cellular_structure"]["boundary_matrices"]["d3"]["sha256"]

    trivial = obj["controls"]["zero_shift_v2_cover_regression"]
    assert trivial["bundle_witness"]["directed_winding"] == 0
    assert trivial["law_table_ran"] is False
    assert trivial["law_table_refused"] is True


def test_law_table_faithfulness_and_v1_comparison_are_carried() -> None:
    common = _common()
    obj = common.build_fiber_augmented_cover_v2_object()

    law = obj["b6_law_test"]
    assert law["law"] == "b6 = -b0*b3"
    assert law["sample_total"] == 99
    assert law["witness_gate_passed"] is True
    assert law["law_test_status"] in {
        "holds_on_cellular_nontrivial_cover",
        "fails_on_cellular_nontrivial_cover",
        "inconclusive_no_nonneutral_rows",
    }
    assert len(obj["sign_variant_table"]) == 8
    assert obj["faithfulness"]["axis0"]["projects_to_committed_axis0"] is True
    assert obj["faithfulness"]["axis3"]["source_backed_equivalent_adapter"] is True
    assert obj["faithfulness"]["axis3"]["predicate_mismatch_count"] == 0
    assert obj["faithfulness"]["axis6"]["projects_to_committed_axis6"] is True
    assert obj["controls"]["scrambled_control"]["ran"] is True
    assert obj["controls"]["convention_flip_control"]["ran"] is True
    assert obj["controls"]["v1_comparison_row"]["agreement_count"] == 46
    assert obj["controls"]["v1_comparison_row"]["sample_total"] == 99


def test_validator_accepts_roundtrip_payload_and_g2a_boundary() -> None:
    common = _common()
    validator_spec = importlib.util.find_spec("validate_fiber_augmented_cover_v2")
    assert validator_spec is not None, "validate_fiber_augmented_cover_v2 module must exist"
    validator = importlib.import_module("validate_fiber_augmented_cover_v2")

    obj = common.build_fiber_augmented_cover_v2_object()
    assert validator.validate_payload(obj) == []
    assert obj["betti_computed"] is False
    assert "betti" not in obj
    assert obj["no_builder_audit_verdict"] is True
    assert obj["no_builder_audit_verdict_envelope_gate"] is True
