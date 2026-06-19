from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_ring_checkerboard_runner_v1"
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"


def load_common():
    path = SIM_DIR / f"{SIM_ID}_common.py"
    spec = importlib.util.spec_from_file_location(f"{SIM_ID}_common", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_card_declares_substrate_first_coordinates_and_fences() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    assert SIM_ID in text
    assert "layers 1-2 + 12 support" in text
    assert "integrated-onto-the-carve" in text
    assert "1Q" in text
    assert "gcmobj_a40e54e13cec01466c9d675028b3574b" in text
    assert "QCA/GNVW index row = named not run" in text
    assert "G.2a" in text
    assert "NO git add/commit" in text
    assert "strict ring-site light-cone" in text
    assert "dead-rule honest refusals" in text


def test_support_map_consumes_frozen_survivor_class_region_lineage() -> None:
    common = load_common()
    payload = common.build_packet()
    cells = payload["support_map"]["cells"]

    assert payload["gcm_object_id"] == common.EXPECTED_OBJECT_ID
    assert payload["registry_body_sha256"] == common.EXPECTED_REGISTRY_BODY_SHA256
    assert payload["three_axis_declaration"]["layer"]["declared_dimension"] == "layers 1-2 + 12 support"
    assert payload["three_axis_declaration"]["nesting"]["coordinate"] == "integrated-onto-the-carve"
    assert payload["three_axis_declaration"]["qubit_depth"]["coordinate"] == "1Q"
    assert len(cells) == 16
    assert len({cell["survivor_id"] for cell in cells}) == 16
    assert len({cell["quotient_class_id"] for cell in cells}) == 8
    assert len({cell["candidate_region_id"] for cell in cells}) == 6


def test_nontrivial_paired_schedule_moves_and_preserves_mc() -> None:
    common = load_common()
    payload = common.build_packet()
    paired = payload["dynamics"]["paired_nontrivial_AABB"]
    alternating = payload["dynamics"]["alternating_AB"]
    row = payload["dynamics"]["two_phase_two_loop_row"]

    assert paired["phase_pattern"] == "AABB"
    assert paired["subphase_count"] == 4
    assert paired["moved_count"] > 0
    assert paired["fixed_count"] < 16
    assert paired["periods"]["spectrum"] != [1]
    assert paired["periods"]["spectrum"] != alternating["periods"]["spectrum"]
    assert paired["dynamic_admissibility"]["preserves_M_C"] is True
    assert row["paired_period_spectrum"] == paired["periods"]["spectrum"]
    assert row["periodicity_changed"] is True
    assert row["v0_identity_tooth_applied"] is True


def test_strict_ring_local_variant_passes_one_site_light_cone() -> None:
    common = load_common()
    payload = common.build_packet()
    strict = payload["ring_local_update"]

    assert strict["variant"] == "ring_adjacent_cell_pairs"
    assert strict["strict_one_site_per_half_step_light_cone_pass"] is True
    assert strict["obstruction"] is None
    assert strict["max_cyclic_ring_distance_by_half_step"] == {"A": 1, "B": 1}
    assert strict["M_C_preservation_by_rule"]["ring_local_AB"]["preserves_M_C"] is True
    assert strict["orbit_nontriviality_by_rule"]["ring_local_AB"]["moved_count"] > 0


def test_full_presentation_equivalence_checked_on_object() -> None:
    common = load_common()
    payload = common.build_packet()
    checks = payload["support_map"]["presentation_equivalence_checks"]
    by_pair = {(row["from"], row["to"]): row for row in checks}

    assert ("flat_nested_checkerboard", "nested_rings_torus_loops") in by_pair
    assert ("nested_rings_torus_loops", "spherical_checkerboard") in by_pair
    assert ("flat_nested_checkerboard", "spherical_checkerboard") in by_pair
    assert all(row["status"] == "checked_on_frozen_object" for row in checks)
    assert all(row["finite_support_count_agrees"] for row in checks)
    assert all(row["lineage_bijection_agrees"] for row in checks)
    assert all(row["relation_readouts_agree"] for row in checks)
    assert payload["support_map"]["presentation_equivalence_summary"]["status"] == "completed_for_frozen_object"


def test_mc_preservation_and_orbit_nontriviality_for_every_rule() -> None:
    common = load_common()
    payload = common.build_packet()
    preservation = payload["M_C_preservation_rerun_by_rule"]
    orbits = payload["orbit_nontriviality_by_rule"]
    expected_rules = {
        "A_half_step",
        "B_half_step",
        "alternating_AB",
        "paired_nontrivial_AABB",
        "ring_local_AB",
    }

    assert set(preservation) == expected_rules
    assert set(orbits) == expected_rules
    assert all(row["preserves_M_C"] for row in preservation.values())
    assert all(row["carve_predicate_text_sha256"] == common.EXPECTED_CARVE_PREDICATE_SHA256 for row in preservation.values())
    assert all(row["moved_count"] > 0 for row in orbits.values())


def test_controls_and_dead_rule_refusals_are_carried() -> None:
    common = load_common()
    payload = common.build_packet()
    controls = payload["controls"]
    dead = payload["dead_rule_honest_refusals"]

    assert controls["all_to_all"]["carved_edge_subset"] is False
    assert controls["all_to_all"]["periods"]["spectrum"] == [16]
    assert controls["phase_merge"]["periodicity_changed_vs_paired"] is True
    assert controls["carve_erasure"]["expected_substrate_check"] == "red"
    assert controls["strict_ring_locality_obstruction_control"]["status"] in {"not_needed_passed", "obstruction_named"}
    assert dead["v0_AABB_identity"]["status"] == "refused_dead_rule"
    assert dead["GNVW_1Q"]["status"] == "named_not_run"
    assert payload["fences"]["qca_gnvw_index_row"] == "named_not_run_2Q_plus_ladder"


def test_written_envelope_and_validator_pass() -> None:
    envelope = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
    assert envelope.is_file()
    payload = json.loads(envelope.read_text(encoding="utf-8"))
    assert payload["all_pass"] is True
    assert payload["substrate_positive_ok"] is True
    assert payload["substrate_lineage_free_negative_ok"] is True
    assert payload["paired_nontrivial"] is True
    assert payload["ring_locality_pass"] is True
    assert payload["presentation_equivalence_completed"] is True

    validator = SIM_DIR / f"validate_{SIM_ID}.py"
    result = subprocess.run(
        [SIM_PY, str(validator.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
