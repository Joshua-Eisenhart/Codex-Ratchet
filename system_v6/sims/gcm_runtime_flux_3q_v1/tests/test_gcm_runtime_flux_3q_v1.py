from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_ID = "gcm_runtime_flux_3q_v1"
ROOT = Path(__file__).resolve().parents[4]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
COMMON_PATH = SIM_DIR / f"{SIM_ID}_common.py"
SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
RESULT = SIM_DIR / "results" / f"{SIM_ID}_results.json"
ENVELOPE = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
VALIDATOR = SIM_DIR / "results" / f"{SIM_ID}_validator_results.json"
LINEAGE_FREE = SIM_DIR / "results" / f"{SIM_ID}_lineage_free_negative.json"


def load_common():
    assert COMMON_PATH.is_file(), f"missing common module: {COMMON_PATH}"
    spec = importlib.util.spec_from_file_location(f"{SIM_ID}_common", COMMON_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_card_declares_doctrine_repair_and_independent_generators() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for phrase in (
        "layer 24 (runtime flux) | integrated | 3Q",
        "gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5",
        "DOCTRINE REPAIR",
        "independent Type1-L generator",
        "independent Type2-R generator",
        "R is not reverse(L)",
        "R is not reflection(L)",
        "max|R - reflect(L)|",
        "scratch_diagnostic",
        "carrier-and-pins-relative",
        "NO git add/commit",
    ):
        assert phrase in text


def test_common_source_does_not_reuse_reverse_row_constructor() -> None:
    text = COMMON_PATH.read_text(encoding="utf-8")
    assert "reverse_current_row" not in text
    assert "time_reverse_of_R_flux_OUT_right_3q" in text
    assert "engine_L_flux_IN_left_3q" in text
    assert "engine_R_flux_OUT_right_3q" in text


def test_packet_declares_independent_l_r_generator_pins() -> None:
    common = load_common()
    packet = common.build_packet(write=False)

    assert packet["classification"] == "scratch_diagnostic"
    assert packet["promotion_allowed"] is False
    assert packet["formal_admission_allowed"] is False
    assert packet["declared_surface"] == "layer 24 (runtime flux) | integrated | 3Q"
    assert packet["gcm_3q_object_id"] == "gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5"
    assert packet["carrier_and_pins_relative"] is True

    independence = packet["generator_independence"]
    assert independence["left_generator_id"] == "engine64_Type1-L_32slot_local_update"
    assert independence["right_generator_id"] == "engine64_Type2-R_32slot_local_update"
    assert independence["distinct_committed_generator_assignments"] is True
    assert independence["R_not_reverse_of_L"] is True
    assert independence["R_not_reflection_of_L"] is True
    assert independence["max_abs_R_minus_reflect_L"] > 1.0e-8
    assert independence["left_schedule_sha256"] != independence["right_schedule_sha256"]
    assert independence["source_locks"]["engine_64_stage_full_run_common"]["exists"] is True


def test_l_r_currents_are_computed_from_each_engine_own_trajectory() -> None:
    common = load_common()
    packet = common.build_packet(write=False)
    rows = {row["row_id"]: row for row in packet["runtime_current_rows"]}

    left = rows["engine_L_flux_IN_left_3q"]
    right = rows["engine_R_flux_OUT_right_3q"]
    reverse = rows["time_reverse_of_R_flux_OUT_right_3q"]

    assert left["constructed_from_peer_row"] is False
    assert right["constructed_from_peer_row"] is False
    assert left["trajectory_source"] == "own_engine_evolution"
    assert right["trajectory_source"] == "own_engine_evolution"
    assert left["initial_state_sha256"] == right["initial_state_sha256"]
    assert left["final_state_sha256"] != right["final_state_sha256"]
    assert left["time_reversal_of"] is None
    assert right["time_reversal_of"] is None

    assert reverse["time_reversal_of"] == "engine_R_flux_OUT_right_3q"
    assert reverse["constructed_from_peer_row"] is False
    assert reverse["trajectory_source"] == "explicit_inverse_evolution_control"
    assert reverse["J_cut"]["net_delta_mutual_I"] == -right["J_cut"]["net_delta_mutual_I"]
    assert reverse["J_ent"]["net_delta_negativity"] == -right["J_ent"]["net_delta_negativity"]


def test_doctrine_test_records_either_independent_outcome_without_forcing_opposition() -> None:
    common = load_common()
    packet = common.build_packet(write=False)
    doctrine = packet["flux_in_left_out_right_doctrine_test"]

    assert doctrine["non_tautological_by_construction"] is True
    assert doctrine["opposition_forced_by_reflection_or_reversal"] is False
    assert doctrine["outcome"] in {
        "independent_opposition_emerged",
        "independent_opposition_not_clean",
    }
    if doctrine["outcome"] == "independent_opposition_emerged":
        assert doctrine["J_cut_LR_opposite_signs"] is True
        assert doctrine["J_ent_LR_opposite_signs"] is True


def test_controls_include_scrambled_pair_product_vanish_carve_erasure_and_smt_flip() -> None:
    common = load_common()
    packet = common.build_packet(write=False)

    controls = packet["controls"]
    assert controls["scramble_pair"]["left_row_id"] == "scrambled_engine_L_flux_IN_left_3q"
    assert controls["scramble_pair"]["right_row_id"] == "scrambled_engine_R_flux_OUT_right_3q"
    assert controls["scramble_pair"]["left_current_changed_or_vanished"] is True
    assert controls["scramble_pair"]["right_current_changed_or_vanished"] is True
    assert controls["time_reversal"]["J_cut_flips_sign"] is True
    assert controls["time_reversal"]["J_ent_flips_sign"] is True
    assert controls["product_survivor_controls"]["all_selected_product_controls_zero"] is True
    assert controls["product_survivor_controls"]["selected_product_control_count"] >= 4
    assert controls["carve_erasure"]["substrate_check_ok"] is False
    assert controls["carve_erasure"]["error_codes"]

    for solver_name in ("z3", "cvc5"):
        proof = packet["crossover_proofs"][solver_name]
        assert proof["ran"] is True
        assert proof["load_bearing"] is True
        assert proof["polarity"] == "negated_violation_unsat_real_erasure_sat"
        assert proof["verdict"] == "unsat"
        assert proof["erased_control_verdict"] == "sat"
        assert proof["proof_flips_under_erasure"] is True


def test_script_writes_results_envelope_and_validators_accept_them() -> None:
    runner = subprocess.run(
        [str(SIM_PY), str(SIM_DIR / f"{SIM_ID}_pytorch.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert runner.returncode == 0, runner.stderr + runner.stdout
    assert RESULT.is_file()
    assert ENVELOPE.is_file()
    assert LINEAGE_FREE.is_file()

    validator = subprocess.run(
        [str(SIM_PY), str(SIM_DIR / f"validate_{SIM_ID}.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert validator.returncode == 0, validator.stderr + validator.stdout
    payload = json.loads(VALIDATOR.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["errors"] == []

    three_engine = subprocess.run(
        [
            str(SIM_PY),
            "scripts/validate_three_engine_sim_result.py",
            "--require-pytorch",
            "--strict-source-backed",
            "--require-tool-intent",
            str(ENVELOPE.relative_to(ROOT)),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert three_engine.returncode == 0, three_engine.stderr + three_engine.stdout
