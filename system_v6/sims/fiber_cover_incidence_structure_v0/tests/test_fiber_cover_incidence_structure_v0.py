from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


def _common():
    spec = importlib.util.find_spec("fiber_cover_incidence_structure_v0_common")
    assert spec is not None, "fiber_cover_incidence_structure_v0_common module must exist"
    return importlib.import_module("fiber_cover_incidence_structure_v0_common")


def test_source_derived_faces_have_no_introduced_rows() -> None:
    common = _common()
    obj = common.build_fiber_cover_incidence_structure_object()
    derivation = obj["derivation_honesty"]

    assert obj["classification"] == "scratch_diagnostic"
    assert obj["promotion_allowed"] is False
    assert obj["formal_admission_allowed"] is False
    assert obj["betti_computed"] is False
    assert "betti" not in obj
    assert derivation["derivation_introduced_count"] == 0
    assert derivation["face_derivation_rule"] == "all simple committed directed non-self 4-cycles"
    assert derivation["base_2_cell_count"] == len(obj["base_incidence"]["cells"]["C2"])
    assert derivation["base_2_cell_count"] > 0
    assert all(row["introduced"] is False for row in derivation["face_derivation_table"])
    assert all(len(row["source_edge_ids"]) == 4 for row in derivation["face_derivation_table"])


def test_total_space_uses_cover_v1_fiber_and_seam_shifts() -> None:
    common = _common()
    obj = common.build_fiber_cover_incidence_structure_object()
    total = obj["total_space_incidence"]

    assert obj["source_cover"]["cover_sha256"] == "618678a9cfb00ec88a722faa7fe5f2111145e5a9385bab8e6987b1949e53f696"
    assert obj["source_cover"]["fiber_phase_count"] == 3
    assert obj["source_cover"]["seam_lifted_shift_steps"] == [1, 1, 1, 0]
    assert total["cell_counts"]["C0"] == 99
    assert total["cell_counts"]["C1"] == 693
    assert total["cell_counts"]["C2"] == 630
    assert total["cell_counts"]["C3"] == 36
    assert total["gluing_source"] == "committed chart_transition_rows from fiber_augmented_cover_v1"
    assert total["chain_checks"]["d_squared_zero"] is True
    assert total["boundary_matrices"]["d1"]["sha256"]
    assert total["boundary_matrices"]["d2"]["sha256"]
    assert total["boundary_matrices"]["d3"]["sha256"]


def test_base_and_total_chain_closure_and_euler_are_reported() -> None:
    common = _common()
    obj = common.build_fiber_cover_incidence_structure_object()

    base = obj["base_incidence"]
    total = obj["total_space_incidence"]
    assert base["chain_checks"]["d_squared_zero"] is True
    assert total["chain_checks"]["d_squared_zero"] is True
    assert isinstance(base["euler_characteristic"], int)
    assert isinstance(total["euler_characteristic"], int)
    assert base["boundary_matrices"]["d1"]["format"] == "sparse_coo"
    assert base["boundary_matrices"]["d2"]["format"] == "sparse_coo"
    assert total["boundary_matrices"]["d1"]["format"] == "sparse_coo"
    assert total["boundary_matrices"]["d2"]["format"] == "sparse_coo"
    assert total["boundary_matrices"]["d3"]["format"] == "sparse_coo"


def test_validator_accepts_roundtrip_payload_and_g2a_boundary() -> None:
    common = _common()
    validator_spec = importlib.util.find_spec("validate_fiber_cover_incidence_structure_v0")
    assert validator_spec is not None, "validate_fiber_cover_incidence_structure_v0 module must exist"
    validator = importlib.import_module("validate_fiber_cover_incidence_structure_v0")

    obj = common.build_fiber_cover_incidence_structure_object()
    assert validator.validate_payload(obj) == []
    assert obj["no_builder_audit_verdict"] is True
    assert obj["no_builder_audit_verdict_envelope_gate"] is True
