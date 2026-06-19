from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_constraint_carve_2q_v0"
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


def test_build_card_declares_coordinates_and_g2a_boundary() -> None:
    card = SIM_DIR / "build_card.md"
    assert card.is_file()
    text = card.read_text(encoding="utf-8")
    assert "DECLARE: layers 1-2 | carve (order B) | 2Q" in text
    assert "C1 predicate source line" in text
    assert "C2 predicate source line" in text
    assert "C3 predicate source line" in text
    assert "cross-rung" in text
    assert "seven audit questions" in text
    assert "scratch_diagnostic" in text
    assert "NO git add/commit" in text
    assert "G.2a" in text
    assert "scripts/builder_audit_boundary.py" in text


def test_common_packet_computes_2q_carve_and_unchanged_c_forms() -> None:
    common = load_common()
    payload = common.build_packet()
    assert payload["coordinates"] == {"layer": "layers 1-2", "nesting": "carve (order B)", "qubit_depth": "2Q"}
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["candidate_space"]["candidate_count"] == 15783
    assert payload["candidate_space"]["density_subcarrier_count"] == 1167
    assert payload["survivor_count"] == 544
    assert payload["survivor_family_counts"] == {"product_grid": 528, "purification_boundary": 16}
    assert payload["entangled_survivor_count"] == 16
    assert payload["quotient"]["class_count"] == 8
    assert [row["one_q_source_predicate_id"] for row in payload["constraint_family_C"]] == [
        "C1_finite_density_carrier",
        "C2_probe_distinguishability_xz_local_adapter_pin",
        "C3_persistence_n01_order_gap",
    ]
    assert payload["kill_counts_by_constraint"] == {
        "C1_finite_2q_density_carrier": 14616,
        "C2_probe_distinguishability_xz_local_adapter_pin": 215,
        "C3_persistence_n01_order_gap": 408,
    }
    assert payload["terrain_blindness_guard"]["clean"] is True
    assert payload["controls"]["blindness_control"]["injected_variant_caught"] is True


def test_controls_cross_rung_and_boundary_phenomena_are_computed() -> None:
    common = load_common()
    payload = common.build_packet()
    controls = payload["controls"]
    assert controls["empty_C"]["survivor_count"] == 15783
    assert controls["overconstrained_C"]["survivor_count"] == 0
    assert all(row["bite"] for row in controls["constraint_erasure"])
    assert controls["probe_family_scramble"]["quotient_moved"] is True

    cross = payload["cross_rung_lineage_row"]
    assert cross["product_control_embedding_count"] == 16
    assert cross["product_control_embedding_all_survive"] is True
    assert cross["partial_trace_A_image_equals_1q_survivor_set"] is True
    assert all(cross["one_q_hashes_match_expected"].values())
    assert set(cross["partial_trace_A_fiber_counts"].values()) == {34}

    boundary = payload["boundary_phenomena_2q_only"]
    assert boundary["entanglement_enters_candidate_space"] is True
    assert boundary["valid_entangled_candidate_count"] == 46
    assert boundary["entangled_survivor_count"] == 16
    assert boundary["bell_diagonal_valid_entangled_count"] == 20
    assert boundary["bell_diagonal_entangled_killed_by"] == {
        "C2_probe_distinguishability_xz_local_adapter_pin": 20
    }


def test_mct_and_seven_audit_questions_are_answerable() -> None:
    common = load_common()
    payload = common.build_packet()
    hook = payload["M_C_t_hook"]
    assert hook["survivor_count"] == 272
    assert hook["quotient_class_count"] == 4
    questions = payload["seven_audit_questions"]
    assert len(questions) == 7
    assert questions["which_layer"] == "layers 1-2: constraint set plus carved object M(C)+S/~_M"
    assert questions["which_qubit_depth"] == "2Q"
    assert "Julia" in questions["which_three_engines_ran"]


def test_three_engine_envelope_validator_and_tests_pass() -> None:
    payload = load_envelope()
    assert payload["schema_version"] == "three_engine_sim_result_v1"
    assert payload["schema"] == "gcm_constraint_carve_2q_v0_envelope_v1"
    assert payload["all_pass"] is True
    assert payload["coordinates"] == {"layer": "layers 1-2", "nesting": "carve (order B)", "qubit_depth": "2Q"}
    assert set(payload["engine_lanes"]) == {"pytorch", "jax", "julia"}
    assert payload["engine_consensus"]["survivor_count_agreement"] is True
    assert payload["engine_consensus"]["quotient_class_count_agreement"] is True
    assert payload["engine_consensus"]["component_count_agreement"] is True
    assert payload["engine_consensus"]["entangled_survivor_count_agreement"] is True
    assert payload["engine_consensus"]["embedded_1q_count_agreement"] is True
    assert payload["builder_gates"]["G_2a_idempotency_from_birth"] is True
    assert payload["no_builder_audit_verdict"] is True
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False

    validator = SIM_DIR / f"validate_{SIM_ID}.py"
    result = subprocess.run(
        [SIM_PY, str(validator.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
