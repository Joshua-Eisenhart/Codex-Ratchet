from __future__ import annotations

import importlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


def _common():
    spec = importlib.util.find_spec("render_layer_readout_v1_common")
    assert spec is not None, "render_layer_readout_v1_common module must exist"
    return importlib.import_module("render_layer_readout_v1_common")


def test_repin_reachability_gate_precedes_readout_table() -> None:
    common = _common()
    payload = common.build_core()

    gate = payload["repin_reachability_gate"]
    assert payload["construction_status"] == "repin_reachability_passed"
    assert payload["readout_table_ran"] is True
    assert gate["status"] == "passed"
    assert gate["required_labels"] == ["reshape_the_render", "resist_the_update"]
    assert gate["label_counts"]["reshape_the_render"] > 0
    assert gate["label_counts"]["resist_the_update"] > 0
    assert gate["witnesses"]["reshape_the_render"]["committed_dynamics_trajectory"] is True
    assert gate["witnesses"]["resist_the_update"]["committed_dynamics_trajectory"] is True


def test_old_v0_pin_regression_is_refused_before_readout_rows() -> None:
    common = _common()
    blocked = common.build_packet_for_pin(common.old_v0_distance_pin())

    assert blocked["construction_status"] == "repin_failed_unreachable"
    assert blocked["readout_table_ran"] is False
    assert blocked["repin_reachability_gate"]["status"] == "failed_unreachable"
    assert blocked["repin_reachability_gate"]["label_counts"].get("reshape_the_render", 0) == 0
    assert "render_readout" not in blocked

    core = common.build_core()
    control = core["controls"]["v0_old_pin_regression"]
    assert control["reproduces_unreachable_reshape"] is True
    assert control["law"] == "v0 negative control: old distance pin must fail the v1 reachability gate"


def test_scrambled_error_breaks_nonconstant_readout_and_boundary_is_own_family() -> None:
    common = _common()
    payload = common.build_core()

    assert payload["render_readout"]["polarity_counts"]["reshape_the_render"] > 0
    assert payload["render_readout"]["polarity_counts"]["resist_the_update"] > 0
    scrambled = payload["controls"]["scrambled_error"]
    assert scrambled["verdict"] == "breaks-render-polarity"
    assert scrambled["breaks_polarity"] is True
    assert scrambled["constant_readout"] is False
    assert scrambled["same_cell_count"] < common.EXPECTED_STATE_COUNT

    boundary = payload["axis0_boundary"]["boundary_verdict"]
    assert boundary["question"] == "same distinction, different distinction, or no stable distinction"
    assert boundary["relation_to_axis0_phi"] == "different_distinction_from_axis0"
    assert boundary["verdict"] == "own_readout_family"
    assert payload["counts"]["axis0_disagreement_cells"] > 0


def test_boundary_helper_accepts_rebuilt_payload_and_keeps_claim_ceiling() -> None:
    common = _common()
    boundary_spec = importlib.util.find_spec("render_layer_readout_v1_boundary")
    assert boundary_spec is not None, "render_layer_readout_v1_boundary module must exist"
    boundary = importlib.import_module("render_layer_readout_v1_boundary")

    payload = common.build_core()
    assert boundary.boundary_errors(payload, common.SIM_DIR) == []
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["claim_ceiling"] == common.CLAIM_CEILING
    assert payload["no_builder_audit_verdict"] is True


def test_validator_roundtrip_writes_clean_receipt() -> None:
    subprocess.run([PY, str(SIM_DIR / "render_layer_readout_v1_jax.py")], cwd=ROOT, check=True)
    subprocess.run([PY, str(SIM_DIR / "render_layer_readout_v1_pytorch.py")], cwd=ROOT, check=True)
    subprocess.run(
        [
            "/opt/homebrew/bin/julia",
            "--startup-file=no",
            "--project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier",
            str(SIM_DIR / "render_layer_readout_v1_julia.jl"),
        ],
        cwd=ROOT,
        check=True,
        env={**os.environ, "JULIA_LOAD_PATH": "@:@stdlib"},
    )
    subprocess.run([PY, str(SIM_DIR / "render_layer_readout_v1_envelope.py")], cwd=ROOT, check=True)
    subprocess.run([PY, str(SIM_DIR / "validate_render_layer_readout_v1.py")], cwd=ROOT, check=True)
    result = json.loads((SIM_DIR / "results" / "render_layer_readout_v1_validator_results.json").read_text())
    assert result["all_pass"] is True
    assert result["errors"] == []
