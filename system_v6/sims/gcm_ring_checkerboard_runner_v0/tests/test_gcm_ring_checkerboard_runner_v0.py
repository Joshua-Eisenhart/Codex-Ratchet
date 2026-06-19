from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_ring_checkerboard_runner_v0"
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
    assert payload["support_map"]["presentation_equivalence_checks"][0]["support_count_agrees"] is True
    assert payload["support_map"]["presentation_equivalence_checks"][1]["shell_id_present_for_all_cells"] is True


def test_local_update_preserves_mc_and_records_phase_blocks() -> None:
    common = load_common()
    payload = common.build_packet()
    blocks = payload["local_update"]["phase_blocks"]

    assert len(blocks["A_hidden_probe_flip"]) == 8
    assert len(blocks["B_reflections"]) == 4
    assert payload["dynamics"]["alternating_AB"]["dynamic_admissibility"]["preserves_M_C"] is True
    assert payload["dynamics"]["paired_AABB"]["dynamic_admissibility"]["preserves_M_C"] is True
    assert payload["dynamics"]["two_phase_two_loop_row"]["alternating_period_spectrum"] == [2]
    assert payload["dynamics"]["two_phase_two_loop_row"]["paired_period_spectrum"] == [1]
    assert payload["dynamics"]["two_phase_two_loop_row"]["periodicity_changed"] is True


def test_controls_break_locality_phase_and_substrate_anchor() -> None:
    common = load_common()
    payload = common.build_packet()
    controls = payload["controls"]
    substrate = payload["substrate_enforcement"]

    assert controls["locality_removal_all_to_all"]["carved_edge_subset"] is False
    assert controls["locality_removal_all_to_all"]["periods"]["spectrum"] == [16]
    assert controls["phase_merge_single_phase"]["periodicity_changed_vs_alternating"] is True
    assert controls["carve_erasure_anchoring_break"]["expected_substrate_check"] == "red"
    assert substrate["positive_payload_ok"]["ok"] is True
    assert substrate["lineage_free_negative"]["ok"] is False
    assert substrate["negative_failed_as_required"] is True


def test_written_envelope_and_validator_pass() -> None:
    envelope = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
    assert envelope.is_file()
    payload = json.loads(envelope.read_text(encoding="utf-8"))
    assert payload["all_pass"] is True
    assert payload["substrate_positive_ok"] is True
    assert payload["substrate_lineage_free_negative_ok"] is True

    validator = SIM_DIR / f"validate_{SIM_ID}.py"
    result = subprocess.run(
        [SIM_PY, str(validator.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

