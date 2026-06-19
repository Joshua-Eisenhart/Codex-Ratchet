from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_geometry_attach_2q_v1"
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"


def load_common():
    common_path = SIM_DIR / f"{SIM_ID}_common.py"
    spec = importlib.util.spec_from_file_location(f"{SIM_ID}_common", common_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_envelope() -> dict:
    assert ENVELOPE.is_file(), f"missing envelope result: {ENVELOPE}"
    return json.loads(ENVELOPE.read_text(encoding="utf-8"))


def test_build_card_declares_2q_geometry_scope() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    assert "DECLARE: layers 3-12 + 17-18 | integrated-onto-the-carve | 2Q" in text
    assert "544 survivors" in text
    assert "16 entangled" in text
    assert "scripts/gcm_substrate_check.py" in text
    assert "G.2a" in text
    assert "NO git add/commit" in text


def test_common_packet_attaches_product_and_entangled_geometry() -> None:
    common = load_common()
    payload = common.build_packet()
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["three_axis_declaration"]["layers"]["declaration"] == "layers 3-12 + 17-18"
    assert payload["three_axis_declaration"]["nesting"]["coordinate"] == "integrated-onto-the-carve"
    assert payload["three_axis_declaration"]["qubit_depth"]["coordinate"] == "2Q"
    assert payload["counts"]["survivor_count"] == 544
    assert payload["counts"]["product_survivor_count"] == 528
    assert payload["counts"]["entangled_survivor_count"] == 16
    assert len(payload["geometry_packet"]["product_survivor_geometries"]) == 528
    assert len(payload["geometry_packet"]["entangled_survivor_geometries"]) == 16
    assert payload["controls"]["product_survivor_geometric_marginal_radii"]["all_exact_within_tolerance"] is True
    assert payload["controls"]["entangled_reduced_radii"]["all_strictly_between_zero_and_one"] is True


def test_entangled_rows_have_schmidt_and_correlation_fibers() -> None:
    common = load_common()
    payload = common.build_packet()
    rows = payload["geometry_packet"]["entangled_survivor_geometries"]
    assert all(0.0 < row["schmidt_decomposition"]["theta_rad"] < 0.7854 for row in rows)
    assert all(row["reduced_states"]["radii_strictly_less_than_one"] for row in rows)
    assert all(row["correlation_data_marginals_miss"]["marginals_determine_state"] is False for row in rows)
    fibers = payload["geometry_packet"]["entangled_fibers_over_marginals"]
    assert len(fibers) == 16
    assert all(fiber["phase_witness_count"] == 2 for fiber in fibers)
    assert all(fiber["marginals_determine_state"] is False for fiber in fibers)


def test_substrate_green_and_lineage_free_red() -> None:
    common = load_common()
    payload = common.build_packet()
    enforcement = payload["substrate_enforcement"]
    assert enforcement["positive_payload_ok"]["ok"] is True
    assert enforcement["registry"].endswith("gcm_2q_freeze_and_cut_v0_registry.json")
    assert "GCM2Q_LINEAGE_CONSUMPTION_MISSING" not in enforcement["positive_payload_ok"]["error_codes"]
    assert enforcement["lineage_free_negative"]["ok"] is False
    assert "GCM2Q_LINEAGE_CONSUMPTION_MISSING" in enforcement["lineage_free_negative"]["error_codes"]
    assert enforcement["negative_failed_as_required"] is True
    assert payload["gcm_lineage"]["gcm_2q_survivor_ids"]
    assert payload["two_q_lineage"]["claims_conditional_on_2q_registry_in_flight_audit"] is False
    assert payload["two_q_lineage"]["audit_resolved_by_commit"] == "8326405e6"
    assert payload["controls"]["one_q_regression_through_partial_trace"]["image_equals_1q_attach_hopf_set"] is True


def test_three_engine_envelope_validator_passes() -> None:
    payload = load_envelope()
    assert payload["schema_version"] == "three_engine_sim_result_v1"
    assert payload["schema"] == "gcm_geometry_attach_2q_v1_envelope_v1"
    assert payload["all_pass"] is True
    assert set(payload["engine_lanes"]) == {"julia", "jax", "pytorch"}
    assert payload["engine_consensus"]["survivor_count_agreement"] is True
    assert payload["engine_consensus"]["entangled_count_agreement"] is True

    validator = SIM_DIR / f"validate_{SIM_ID}.py"
    result = subprocess.run(
        [SIM_PY, str(validator.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
