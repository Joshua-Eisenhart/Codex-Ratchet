from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_constraint_carve_3q_v0"
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
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
    assert RESULT_PATH.is_file(), f"missing result packet: {RESULT_PATH}"
    return json.loads(RESULT_PATH.read_text(encoding="utf-8"))


def load_envelope() -> dict:
    assert ENVELOPE_PATH.is_file(), f"missing envelope result: {ENVELOPE_PATH}"
    return json.loads(ENVELOPE_PATH.read_text(encoding="utf-8"))


def test_build_card_declares_3q_floor_rung_and_feedstock() -> None:
    card = SIM_DIR / "build_card.md"
    assert card.is_file()
    text = card.read_text(encoding="utf-8")
    assert "DECLARE: layers 1-2 (+17 tensor) | carve | 3Q" in text
    assert "gcmobj_a40e54e13cec01466c9d675028b3574b" in text
    assert "gcm_constraint_carve_2q_v0" in text
    assert "geo_s1_three_qubit_floor_exact_v0" in text
    assert "6ed5e961e" in text
    assert "stage_lifted_spinor_shell_n3_v0" in text
    assert "f7b0ee5fe" in text
    assert "CKW" in text
    assert "GHZ" in text
    assert "W" in text
    assert "G.2a" in text
    assert "NO git add/commit" in text
    assert "scratch_diagnostic" in text


def test_common_packet_computes_3q_carve_from_locked_sources() -> None:
    common = load_common()
    payload = common.build_packet()
    assert payload["coordinates"] == {
        "layer": "layers 1-2 (+17 tensor)",
        "nesting": "carve",
        "qubit_depth": "3Q",
    }
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["claim_ceiling"] == "scratch_diagnostic_carrier_and_pins_relative_3q_floor_rung"
    assert payload["substrate_first"]["one_q_registry"]["gcm_object_id"] == "gcmobj_a40e54e13cec01466c9d675028b3574b"
    assert payload["substrate_first"]["two_q_registry"]["sim_id"] == "gcm_constraint_carve_2q_v0"
    assert payload["source_locks"]["three_q_floor"]["commit_hint"] == "6ed5e961e"
    assert payload["source_locks"]["climb_ledger_correction"]["commit_hint"] == "f7b0ee5fe"
    assert payload["candidate_space"]["candidate_count"] == 552
    assert payload["candidate_space"]["product_embedding_from_2q_count"] == 544
    assert payload["candidate_space"]["entangled_anchor_count"] == 8
    assert payload["survivor_count"] == 545
    assert payload["survivor_family_counts"]["2q_survivor_product_lift"] == 544
    assert payload["survivor_family_counts"]["entangled_boundary_anchor"] == 1
    assert payload["quotient"]["class_count"] == 9
    assert len(payload["kill_ledger"]) == 7
    assert payload["kill_counts_by_constraint"] == {
        "C1_finite_3q_density_carrier": 1,
        "C2_probe_distinguishability_xz_local_adapter_pin": 4,
        "C3_persistence_n01_order_gap": 2,
    }
    assert [row["one_q_source_predicate_id"] for row in payload["constraint_family_C"]] == [
        "C1_finite_density_carrier",
        "C2_probe_distinguishability_xz_local_adapter_pin",
        "C3_persistence_n01_order_gap",
    ]
    assert payload["terrain_blindness_guard"]["clean"] is True
    assert payload["controls"]["injection_red"]["injected_variant_caught"] is True
    assert payload["lineage_free_negative"]["red"] is True


def test_cross_rung_monogamy_floor_and_ghz_w_rows_are_explicit() -> None:
    common = load_common()
    payload = common.build_packet()
    cross = payload["cross_rung_rows"]
    assert cross["product_embedding_vs_2q"]["input_2q_survivor_count"] == 544
    assert cross["product_embedding_vs_2q"]["lifted_survivor_count"] == 544
    assert cross["product_embedding_vs_2q"]["all_lifted_survive"] is True
    assert cross["partial_trace_vs_2q"]["image_equals_2q_survivor_set"] is True
    assert set(cross["partial_trace_vs_2q"]["fiber_counts"].values()) == {1}

    ghz = payload["ghz_vs_w_admissibility"]["GHZ"]
    w = payload["ghz_vs_w_admissibility"]["W"]
    assert ghz["admissible"] is False
    assert ghz["killed_by"] == "C2_probe_distinguishability_xz_local_adapter_pin"
    assert w["admissible"] is False
    assert w["killed_by"] == "C3_persistence_n01_order_gap"
    assert payload["ghz_vs_w_admissibility"]["constraints_distinguish_GHZ_and_W"] is True

    monogamy = payload["monogamy_ckw_row"]
    assert monogamy["opened_by_2q_audit"] == "OPEN_closes_at_3_parties"
    assert monogamy["computed_on_entangled_survivors"] is True
    assert monogamy["survivor_count_checked"] == 1
    assert monogamy["all_survivors_satisfy_ckw"] is True
    assert monogamy["rows"][0]["state_id"] == "locally_rotated_generalized_GHZ_anchor"
    assert monogamy["rows"][0]["tau_A_BC"] == 0.1875
    assert monogamy["rows"][0]["tau_AB_plus_tau_AC"] == 0.0
    assert monogamy["rows"][0]["ckw_margin"] == 0.1875

    floor = payload["floor_rows"]
    assert floor["source_object_id"] == "geo_s1_three_qubit_floor_exact_v0"
    assert floor["cl6_structure_carried_by_survivors"]["carrier"] == "C^8"
    assert floor["cl6_structure_carried_by_survivors"]["gamma7_split"] == {"-1": 4, "1": 4}
    assert floor["cl6_structure_carried_by_survivors"]["max_anticommuting_counts"] == {"1Q": 3, "2Q": 5, "3Q": 7}
    assert floor["shell_supports"]["source_object_id"] == "stage_lifted_spinor_shell_n3_v0"
    assert floor["shell_supports"]["support_counts"] == {"nodes": 3, "edges": 3, "faces": 1}


def test_controls_and_validator_pass_after_build() -> None:
    payload = load_result()
    controls = payload["controls"]
    assert controls["empty_C"]["survivor_count"] == 552
    assert controls["cliff"]["survivor_count"] == 0
    assert all(row["bite"] for row in controls["erasure_bite"])
    assert controls["probe_scramble"]["quotient_moved"] is True
    assert controls["regressions"]["one_q"]["object_id_match"] is True
    assert controls["regressions"]["two_q"]["source_hash_present"] is True

    validator = SIM_DIR / f"validate_{SIM_ID}.py"
    result = subprocess.run(
        [SIM_PY, str(validator.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_envelope_lanes_agree_and_generic_contract_fields_exist() -> None:
    payload = load_envelope()
    assert payload["schema_version"] == "three_engine_sim_result_v1"
    assert payload["schema"] == "gcm_constraint_carve_3q_v0_envelope_v1"
    assert payload["all_pass"] is True
    assert set(payload["engine_lanes"]) == {"julia", "jax", "pytorch"}
    assert payload["engine_consensus"]["survivor_count_agreement"] is True
    assert payload["engine_consensus"]["quotient_class_count_agreement"] is True
    assert payload["engine_consensus"]["ckw_survivor_count_agreement"] is True
    assert payload["engine_consensus"]["floor_row_agreement"] is True
    assert payload["builder_gates"]["G_2a_idempotency_from_birth"] is True
    assert payload["no_builder_audit_verdict"] is True
    assert payload["TOOL_MANIFEST"]
    assert payload["TOOL_INTEGRATION_DEPTH"]
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
