from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_nested_geometry_delta_3q_v0"
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
    assert RESULT_PATH.is_file(), f"missing result: {RESULT_PATH}"
    return json.loads(RESULT_PATH.read_text(encoding="utf-8"))


def test_packet_declares_nested_geometry_delta_integrated_3q_and_schema_fields() -> None:
    packet = load_result()
    common = load_common()
    assert packet["sim_id"] == SIM_ID
    assert packet["classification"] == "scratch_diagnostic"
    assert packet["layer_declaration"] == {
        "layer": "nested-geometry-delta",
        "integration": "integrated",
        "qubit_depth": "3Q",
    }
    for field in common.REQUIRED_NESTED_FIELDS:
        assert field in packet, f"missing nested schema field {field}"
    assert packet["cut_state_available"] is True
    assert packet["blocked_consumer_enforced"] is True
    assert packet["claim_ceiling"] == "scratch_diagnostic_first_flip_controlled_geometry_delta_carrier_and_pins_relative"


def test_geometry_delta_flip_runs_store_main_alternate_pin_and_alternate_probe_numbers() -> None:
    packet = load_result()
    delta = packet["geometry_delta_from_free"]
    assert delta["quantity"] == "A_marginal_probe_shell_occupation_distribution"
    assert delta["main"]["free_count"] == 551
    assert delta["main"]["nested_count"] == 545
    assert delta["main"]["delta_l1"] > 0.0

    flip = packet["flip_control_runs"]
    assert flip["main"]["delta_vector_sha256"] == delta["main"]["delta_vector_sha256"]
    assert flip["same_input_stable_null"]["pin_name"] == delta["main"]["pin_name"]
    assert flip["same_input_stable_null"]["probe_family"] == delta["main"]["probe_family"]
    assert packet["same_input_stability_control"]["stable"] is True
    assert packet["same_input_stability_control"]["null_delta_l1"] <= 1.0e-12
    assert flip["alternate_registry_pin"]["pin_name"] == "alternate_C1_C2_pin_without_C3"
    assert flip["alternate_registry_pin"]["nested_count"] > delta["main"]["nested_count"]
    assert flip["alternate_registry_pin"]["delta_vector_sha256"] != delta["main"]["delta_vector_sha256"]
    assert flip["alternate_probe_family"]["probe_family"] == "M_prime_xy"
    assert flip["alternate_probe_family"]["delta_vector_sha256"] != delta["main"]["delta_vector_sha256"]
    assert packet["geometry_delta_stability_class"] in {"pin_relative", "probe_relative"}
    assert packet["cross_pin_stability"]["stable"] is False
    assert packet["cross_probe_stability"]["stable"] is False


def test_negative_control_flags_known_pin_relative_quantity() -> None:
    packet = load_result()
    negative = packet["negative_control_status"]
    assert negative["control"] == "killed_candidate_count_delta"
    assert negative["expected"] == "pin_relative"
    assert negative["observed"] == "pin_relative"
    assert negative["pass"] is True
    assert negative["main_pin_value"] != negative["alternate_pin_value"]


def test_local_validator_and_nested_schema_checker_pass() -> None:
    validator = SIM_DIR / f"validate_{SIM_ID}.py"
    result = subprocess.run(
        [SIM_PY, str(validator.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    schema = subprocess.run(
        [SIM_PY, "scripts/gcm_nested_schema_check.py", str(RESULT_PATH.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert schema.returncode == 0, schema.stdout + schema.stderr
    schema_payload = json.loads(schema.stdout)
    assert schema_payload["ok"] is True
    assert schema_payload["geometry_delta_claimed"] is True


def test_three_engine_envelope_is_present_and_divergence_free() -> None:
    assert ENVELOPE_PATH.is_file(), f"missing envelope: {ENVELOPE_PATH}"
    envelope = json.loads(ENVELOPE_PATH.read_text(encoding="utf-8"))
    assert envelope["schema_version"] == "three_engine_sim_result_v1"
    assert envelope["classification"] == "scratch_diagnostic"
    assert set(envelope["engines"]) == {"julia", "jax", "pytorch"}
    assert envelope["engine_contract"]["mode"] == "julia_python_packet_geometry_with_supportive_jax_pytorch_guards"
    assert envelope["engine_role_ceiling"]["claim"] == "no all-three-engine independence claim"
    assert envelope["engines"]["julia"]["claim_path_depth"] == "load_bearing"
    assert envelope["engines"]["jax"]["claim_path_depth"] == "supportive"
    assert envelope["engines"]["pytorch"]["claim_path_depth"] == "supportive"
    assert envelope["TOOL_INTEGRATION_DEPTH"]["z3"] == "supportive"
    assert envelope["TOOL_INTEGRATION_DEPTH"]["cvc5"] == "supportive"
    assert "z3" not in envelope["claim_path_tools"]
    assert "cvc5" not in envelope["claim_path_tools"]
    assert envelope["crossover_proofs"]["z3"]["load_bearing"] is False
    assert envelope["crossover_proofs"]["cvc5"]["load_bearing"] is False
    assert envelope["same_input_stability_control"]["stable"] is True
    assert envelope["same_input_stability_control"]["null_delta_l1"] <= 1.0e-12
    assert envelope["divergence"]["max_divergence"] == 0
    assert envelope["no_builder_audit_verdict"] is True
