from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_ID = "gcm_runtime_flux_3q_v0"
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


def test_build_card_declares_runtime_flux_floor_and_fences() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for phrase in (
        "layer 24 (runtime flux) | integrated-onto-the-carve | 3Q",
        "gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5",
        "J_cut",
        "J_ent",
        "J_chi",
        "scratch_diagnostic",
        "carrier-and-pins-relative",
        "not admitted invariants",
        "product-control subset",
        "NO git add/commit",
    ):
        assert phrase in text


def test_packet_declares_3q_runtime_flux_surface_and_consumes_frozen_cuts() -> None:
    common = load_common()
    packet = common.build_packet(write=False)

    assert packet["classification"] == "scratch_diagnostic"
    assert packet["promotion_allowed"] is False
    assert packet["formal_admission_allowed"] is False
    assert packet["declared_surface"] == "layer 24 (runtime flux) | integrated-onto-the-carve | 3Q"
    assert packet["coordinates"] == {
        "layer": "24_runtime_flux",
        "nesting": "integrated-onto-the-carve",
        "qubit_depth": "3Q",
    }
    assert packet["gcm_3q_object_id"] == "gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5"
    assert packet["gcm_3q_registry_body_sha256"] == "623785e4ec0f41bd8cd040c44ceefbc5f1bd3c14d3257487a82afc0a89439fb0"
    assert packet["source_locks"]["three_q_freeze_result"]["path"].endswith(
        "system_v6/sims/gcm_3q_freeze_and_cuts_v0/results/gcm_3q_freeze_and_cuts_v0_results.json"
    )
    assert packet["current_definitions"]["J_cut"]["observable"] == "delta mutual information across each 3Q bipartition"
    assert packet["current_definitions"]["J_ent"]["observable"] == "delta negativity and log-negativity across each 3Q bipartition"
    assert packet["current_definitions"]["J_chi"]["observable"] == "GNVW signed log2 transport seed lifted from committed 2Q runner"


def test_l_r_currents_are_signed_and_time_reversal_flips() -> None:
    common = load_common()
    packet = common.build_packet(write=False)
    rows = {row["row_id"]: row for row in packet["runtime_current_rows"]}

    left = rows["engine_L_flux_IN_left_3q"]
    right = rows["engine_R_flux_OUT_right_3q"]
    reverse = rows["time_reverse_of_R_flux_OUT_right_3q"]

    assert left["J_chi"]["signed_log2_qubits_per_step"] == -2
    assert right["J_chi"]["signed_log2_qubits_per_step"] == 2
    assert packet["flux_in_left_out_right_doctrine_test"]["J_chi_L_negative_R_positive"] is True
    assert packet["flux_in_left_out_right_doctrine_test"]["J_cut_LR_opposite_signs"] is True
    assert right["J_cut"]["net_delta_mutual_I"] > 0.0
    assert left["J_cut"]["net_delta_mutual_I"] < 0.0
    assert right["J_ent"]["net_delta_negativity"] > 0.0
    assert left["J_ent"]["net_delta_negativity"] < 0.0
    assert reverse["time_reversal_of"] == "engine_R_flux_OUT_right_3q"
    assert reverse["J_cut"]["net_delta_mutual_I"] == -right["J_cut"]["net_delta_mutual_I"]
    assert reverse["J_ent"]["net_delta_negativity"] == -right["J_ent"]["net_delta_negativity"]


def test_3q_necessity_and_controls_are_explicit() -> None:
    common = load_common()
    packet = common.build_packet(write=False)

    need = packet["three_q_necessity_row"]
    assert need["three_q_cut_count"] == 3
    assert need["two_q_cut_count"] == 1
    assert need["anchor_has_nonzero_negativity_on_all_three_cuts"] is True
    assert need["ckw_margin_positive_on_all_party_cuts"] is True
    assert need["computed_floor_verdict"] == "runtime_flux_nontrivial_at_3Q_floor_not_below"

    controls = packet["controls"]
    assert controls["static_no_evolution"]["all_currents_zero"] is True
    assert controls["time_reversal"]["J_cut_flips_sign"] is True
    assert controls["time_reversal"]["J_ent_flips_sign"] is True
    assert controls["product_survivor_controls"]["all_selected_product_controls_zero"] is True
    assert controls["product_survivor_controls"]["selected_product_control_count"] >= 4
    assert controls["scrambled_dynamics"]["differs_from_committed_LR_currents"] is True
    assert controls["carve_erasure"]["substrate_check_ok"] is False
    assert controls["carve_erasure"]["error_codes"]


def test_script_writes_results_envelope_and_validator_accepts_them() -> None:
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
