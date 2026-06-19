from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_geometry_attach_v0"
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"


def load_common():
    common_path = SIM_DIR / f"{SIM_ID}_common.py"
    assert common_path.is_file(), f"missing common module: {common_path}"
    spec = importlib.util.spec_from_file_location(f"{SIM_ID}_common", common_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_envelope() -> dict:
    assert ENVELOPE.is_file(), f"missing envelope result: {ENVELOPE}"
    return json.loads(ENVELOPE.read_text(encoding="utf-8"))


def test_build_card_declares_three_axis_and_g2a_boundary() -> None:
    card = SIM_DIR / "build_card.md"
    assert card.is_file()
    text = card.read_text(encoding="utf-8")
    assert SIM_ID in text
    assert "layers 3-12" in text
    assert "integrated-onto-the-carve" in text
    assert "1Q" in text
    assert "gcm_object_id" in text
    assert "survivor_id" in text
    assert "quotient_class_id" in text
    assert "candidate_region_id" in text
    assert "gcm_substrate_check" in text
    assert "G.2a" in text
    assert "scripts/builder_audit_boundary.py" in text
    assert "NO git add/commit" in text


def test_common_packet_attaches_spinor_hopf_density_and_shells_to_frozen_ids() -> None:
    common = load_common()
    payload = common.build_packet()
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["gcm_object_id"] == common.EXPECTED_OBJECT_ID
    assert payload["registry_body_sha256"] == common.EXPECTED_REGISTRY_BODY_SHA256
    assert payload["three_axis_declaration"]["layer"]["layer_range"] == "3-12"
    assert payload["three_axis_declaration"]["nesting"]["coordinate"] == "integrated-onto-the-carve"
    assert payload["three_axis_declaration"]["qubit_depth"]["coordinate"] == "1Q"

    counts = payload["counts"]
    assert counts["survivor_count"] == 16
    assert counts["quotient_class_count"] == 8
    assert counts["density_quotient_unique_count"] == 8
    assert counts["candidate_region_count"] == 6
    assert counts["occupied_shell_count"] == 5

    attachment = payload["attachment_map"]
    assert len(attachment["survivor_spinor_maps"]) == 16
    assert attachment["class_structure_survives_density_quotient"] is True
    assert attachment["shell_occupancy"]["counts_by_T_eta"] == {
        "0": 2,
        "3pi/8": 4,
        "pi/2": 2,
        "pi/4": 4,
        "pi/8": 4,
    }
    assert all(abs(row["s3_norm"] - 1.0) <= 1e-12 for row in attachment["survivor_spinor_maps"])
    assert all(abs(row["hopf_norm"] - 1.0) <= 1e-12 for row in attachment["survivor_spinor_maps"])
    assert all(row["rho_readout"]["rank_one"] for row in attachment["survivor_spinor_maps"])


def test_nesting_controls_and_substrate_enforcement_have_green_and_red_teeth() -> None:
    common = load_common()
    payload = common.build_packet()
    controls = payload["nesting_controls"]
    assert controls["phase_quotient_remove_lower_layer"]["class_structure_survives"] is True
    assert "S3 fiber phase coordinate" in controls["phase_quotient_remove_lower_layer"]["lost"]
    assert controls["erase_carve_control"]["lineage_available"] is False
    assert controls["erase_carve_control"]["anchored_survivor_count_after_erasure"] == 0

    enforcement = payload["substrate_enforcement"]
    assert enforcement["positive_payload_ok"]["ok"] is True
    assert enforcement["lineage_free_negative"]["ok"] is False
    assert enforcement["negative_failed_as_required"] is True


def test_three_engine_envelope_validator_and_tests_pass() -> None:
    payload = load_envelope()
    assert payload["schema_version"] == "three_engine_sim_result_v1"
    assert payload["schema"] == "gcm_geometry_attach_v0_envelope_v1"
    assert payload["all_pass"] is True
    assert set(payload["engine_lanes"]) == {"pytorch", "jax", "julia"}
    assert payload["engine_consensus"]["survivor_count_agreement"] is True
    assert payload["engine_consensus"]["density_quotient_count_agreement"] is True
    assert payload["engine_consensus"]["shell_count_agreement"] is True
    assert payload["builder_gates"]["G_2a_idempotency_from_birth"] is True
    assert payload["no_builder_audit_verdict"] is True

    validator = SIM_DIR / f"validate_{SIM_ID}.py"
    result = subprocess.run(
        [SIM_PY, str(validator.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
