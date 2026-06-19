from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_connection_flux_attach_v0"
RESULT_DIR = SIM_DIR / "results"
RESULT = RESULT_DIR / f"{SIM_ID}_results.json"
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


def load_result() -> dict:
    assert RESULT.is_file(), f"missing result: {RESULT}"
    return json.loads(RESULT.read_text(encoding="utf-8"))


def load_envelope() -> dict:
    assert ENVELOPE.is_file(), f"missing envelope result: {ENVELOPE}"
    return json.loads(ENVELOPE.read_text(encoding="utf-8"))


def test_build_card_declares_step_4_coordinates_and_boundaries() -> None:
    card = SIM_DIR / "build_card.md"
    assert card.is_file()
    text = card.read_text(encoding="utf-8")
    for required in (
        SIM_ID,
        "layers 10-12",
        "integrated-onto-the-carve",
        "1Q",
        "gcmobj_a40e54e13cec01466c9d675028b3574b",
        "gcm_object_id_freeze_v0",
        "gcm_geometry_attach_v0",
        "geo_s2_connection_flux_foliation_v0",
        "audit is in flight",
        "conditional on its verdict",
        "geometric flux only",
        "NEVER runtime/QIT flux",
        "scratch_diagnostic",
        "carrier-and-pins-relative",
        "G.2a",
        "NO git add/commit",
    ):
        assert required in text


def test_common_packet_consumes_real_lineage_and_declares_audit_questions() -> None:
    common = load_common()
    payload = common.build_packet()
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["claim_ceiling"] == common.CLAIM_CEILING
    assert payload["gcm_object_id"] == common.EXPECTED_OBJECT_ID
    assert payload["registry_body_sha256"] == common.EXPECTED_REGISTRY_BODY_SHA256
    assert payload["upstream_conditionals"]["gcm_geometry_attach_v0"]["audit_status"] == "in_flight"

    coords = payload["three_axis_declaration"]
    assert coords["layer"]["layer_range"] == "10-12"
    assert coords["nesting"]["coordinate"] == "integrated-onto-the-carve"
    assert coords["qubit_depth"]["coordinate"] == "1Q"

    answers = payload["seven_audit_questions"]
    assert answers["which_layer"] == "layers 10-12"
    assert answers["which_nesting_relation"] == "integrated-onto-the-carve"
    assert answers["which_qubit_depth"] == "1Q"
    assert "attached survivor shell strata" in answers["which_surface_network"]
    assert answers["which_three_engines_ran"] == ["julia", "jax", "pytorch"]
    assert "geometric_curvature_flux" in answers["which_entropy_readout_families_varied"]
    assert "lineage-free substrate negative" in answers["what_broke_when_removed"]

    enforcement = payload["substrate_enforcement"]
    assert enforcement["positive_payload_ok"]["ok"] is True
    assert enforcement["lineage_free_negative"]["ok"] is False
    assert enforcement["negative_failed_as_required"] is True


def test_connection_flux_rows_are_recomputed_on_the_five_occupied_shells() -> None:
    payload = load_result()
    rows = payload["connection_flux_attachment"]["shell_rows"]
    assert [row["T_eta_label"] for row in rows] == ["0", "pi/8", "pi/4", "3pi/8", "pi/2"]
    assert [row["occupied_survivor_count"] for row in rows] == [2, 4, 4, 4, 2]
    assert payload["connection_flux_attachment"]["shell_occupation_signature"] == "2-4-4-4-2"
    assert payload["connection_flux_attachment"]["formula_pin"]["connection_form"] == "A = d phi + cos(2*eta) d chi"
    assert payload["connection_flux_attachment"]["formula_pin"]["curvature_form"] == "F = -2*sin(2*eta) d eta wedge d chi"
    assert payload["connection_flux_attachment"]["geometric_flux_only_fence"]["runtime_or_qit_flux_claimed"] is False

    for row in rows:
        assert row["survivor_ids"]
        assert row["quotient_class_ids"]
        assert row["candidate_region_ids"]
        assert row["holonomy_lifted_cycle"]["formula"] == "h(eta) = -2*pi*cos(2*eta)"
        assert row["shell_flux"]["formula"] == "F strip flux to previous occupied shell"
        assert row["source"] == "recomputed_on_survivor_loci"


def test_controls_and_leakage_rows_have_red_teeth() -> None:
    payload = load_result()
    controls = payload["controls"]
    assert controls["phase_quotient"]["pass"] is True
    assert controls["carve_erasure"]["pass"] is True
    assert controls["carve_erasure"]["anchoring_breaks"] is True
    assert controls["shell_permutation"]["pass"] is True
    assert controls["shell_permutation"]["detects_order_change"] is True

    leakage = payload["leakage_analysis"]
    assert leakage["status"] in {"closed", "leaky"}
    assert len(leakage["adjacency_rows"]) == 4
    assert all(row["between_shells"] for row in leakage["adjacency_rows"])
    assert all("leakage_status" in row for row in leakage["adjacency_rows"])
    assert leakage["honest_outcome"] in {"boring_flux", "nontrivial_closed_flux", "leaky_flux"}


def test_three_engine_envelope_validator_and_substrate_cli_pass() -> None:
    envelope = load_envelope()
    assert envelope["schema_version"] == "three_engine_sim_result_v1"
    assert envelope["schema"] == "gcm_connection_flux_attach_v0_envelope_v1"
    assert envelope["all_pass"] is True
    assert set(envelope["engine_lanes"]) == {"pytorch", "jax", "julia"}
    assert envelope["builder_gates"]["G_2a_idempotency_from_birth"] is True
    assert envelope["no_builder_audit_verdict"] is True

    validator = SIM_DIR / f"validate_{SIM_ID}.py"
    result = subprocess.run(
        [SIM_PY, str(validator.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    substrate = subprocess.run(
        [SIM_PY, "scripts/gcm_substrate_check.py", str(RESULT.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert substrate.returncode == 0, substrate.stdout + substrate.stderr

    common = load_common()
    negative_path = RESULT_DIR / f"{SIM_ID}_lineage_free_negative.json"
    common.write_json(negative_path, common.lineage_free_variant(load_result()))
    negative = subprocess.run(
        [SIM_PY, "scripts/gcm_substrate_check.py", str(negative_path.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert negative.returncode != 0
