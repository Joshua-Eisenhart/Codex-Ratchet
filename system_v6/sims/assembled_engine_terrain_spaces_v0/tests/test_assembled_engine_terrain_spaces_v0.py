from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


def _common():
    spec = importlib.util.find_spec("assembled_engine_terrain_spaces_v0_common")
    assert spec is not None, "assembled_engine_terrain_spaces_v0_common module must exist"
    return importlib.import_module("assembled_engine_terrain_spaces_v0_common")


def test_builds_eight_source_locked_terrain_spaces_with_defaults() -> None:
    common = _common()
    obj = common.build_assembled_engine_terrain_spaces_v0_object()

    assert obj["classification"] == "scratch_diagnostic"
    assert obj["claim_ceiling"] == "rung_1_terrain_spaces_component_only_no_stage_or_engine_claim"
    assert obj["promotion_allowed"] is False
    assert obj["formal_admission_allowed"] is False
    assert obj["component_boundary"] == "terrain spaces only; not the terrains simmed; no stages, engine traversal, axes, bridge, physics, or admission"

    assert [row["terrain_id"] for row in obj["terrain_spaces"]] == [
        "Se-in",
        "Se-out",
        "Ne-in",
        "Ne-out",
        "Ni-in",
        "Ni-out",
        "Si-in",
        "Si-out",
    ]
    assert {row["topology_family"] for row in obj["terrain_spaces"]} == {"Se", "Ne", "Ni", "Si"}
    assert {row["flux_orientation"]["computed_orientation"] for row in obj["terrain_spaces"]} == {"in", "out"}
    assert {row["source_name"] for row in obj["terrain_spaces"]} == {
        "Funnel",
        "Cannon",
        "Vortex",
        "Spiral",
        "Pit",
        "Source",
        "Hill",
        "Citadel",
    }

    flags = obj["design_conformance"]["owner_choice_flags"]
    assert flags["substrate"]["default_value"] == "chart_level_finite_hopf_cell_complex"
    assert flags["topology4_meaning"]["default_value"] == ["Se", "Ne", "Ni", "Si"]
    assert flags["flux_invariant"]["default_value"] == "source_locked_in_out_chirality_sign_rows"
    assert flags["ne_policy"]["default_value"] == "pure_hamiltonian_circulation"
    assert flags["si_projector_frame"]["default_value"] == {"Si-in": "z_projector_strata", "Si-out": "x_projector_strata"}
    assert flags["finite_time_policy"]["default_value"] == {"tau": 0.4, "step_policy": "one_small_residency_step"}
    assert flags["closure"]["default_value"] == "density_level_loop_closure_sufficient_for_smallest_v0"
    assert flags["matrix64"]["default_value"] == "sixteen_chart_locked_stages_only_full_64_deferred"
    assert all(flag["owner_override_allowed"] is True for flag in flags.values())
    assert obj["design_conformance"]["all_design_defaults_consumed"] is True


def test_each_terrain_has_real_chain_homology_and_flux_certificate() -> None:
    common = _common()
    obj = common.build_assembled_engine_terrain_spaces_v0_object()

    for terrain in obj["terrain_spaces"]:
        cells = terrain["carrier_cells"]
        cert = terrain["topology_certificate"]
        assert set(cells) == {"C0", "C1", "C2"}
        assert cert["d_squared_zero"] is True
        assert cert["euler_cross_check"]["passed"] is True
        assert cert["chain_euler_characteristic"] == cert["betti_euler_characteristic"]
        assert cert["boundary_matrices"]["d1"]["sha256"]
        assert cert["boundary_matrices"]["d2"]["sha256"]
        assert terrain["terrain_space_sha256"]
        assert terrain["homology_certificate_ref"] == cert["certificate_sha256"]
        assert terrain["flux_orientation"]["computed_from_committed_structure"] is True
        assert terrain["flux_orientation"]["sign_erasure_control"]["collapses_orientation"] is True
        assert terrain["label_erasure_control"]["terrain_id_erased_but_structure_hash_preserved"] is True
        assert terrain["terrain_generator"]["law_ref"]["source_refs"]
        assert terrain["terrain_generator"]["residency_contract_rung2_law_kind"] in {
            "dissipative_side",
            "circulation_side",
        }


def test_pairwise_distinctness_table_is_complete_and_honest() -> None:
    common = _common()
    obj = common.build_assembled_engine_terrain_spaces_v0_object()

    distinctness = obj["cross_terrain_distinctness"]
    rows = distinctness["pairwise_rows"]
    assert len(rows) == 28
    assert distinctness["all_pairs_distinguished_by_computed_structure"] is True
    assert distinctness["homology_only_indistinguishable_pairs"], "must report homology-only collisions honestly"

    for row in rows:
        assert row["terrain_a"] < row["terrain_b"]
        assert row["distinguished"] is True
        assert row["distinguishing_fields"]
        assert set(row["distinguishing_fields"]).issubset({"homology", "flux_orientation", "law_type", "marked_region_witness"})


def test_validator_accepts_payload_and_g2a_boundary_from_birth() -> None:
    common = _common()
    validator_spec = importlib.util.find_spec("validate_assembled_engine_terrain_spaces_v0")
    assert validator_spec is not None, "validate_assembled_engine_terrain_spaces_v0 module must exist"
    validator = importlib.import_module("validate_assembled_engine_terrain_spaces_v0")

    obj = common.build_assembled_engine_terrain_spaces_v0_object()
    assert validator.validate_payload(obj) == []
    assert obj["builder_gates"]["g2a_boundary_from_birth"] is True
    assert obj["builder_gates"]["file_disjoint_packet"] is True
    assert obj["no_builder_audit_verdict"] is True
    assert obj["no_builder_audit_verdict_envelope_gate"] is True
    assert obj["all_pass"] is True
