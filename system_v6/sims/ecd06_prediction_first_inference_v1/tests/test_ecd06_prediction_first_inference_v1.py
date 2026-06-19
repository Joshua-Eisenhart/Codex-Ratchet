from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_DIR = ROOT / "system_v6" / "sims" / "ecd06_prediction_first_inference_v1"
PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"

if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


def test_core_builds_two_sided_searched_result() -> None:
    common = importlib.import_module("ecd06_prediction_first_inference_v1_common")
    result = common.build_prediction_first_object()
    assert result["all_pass"] is True
    assert result["regime_validity_gate"]["status"] == common.REGIME_PASS_STATUS
    assert result["regime_validity_gate"]["computably_not_exactly_learnable"] is True
    assert result["baseline_side"]["v0_killer_included"] is True
    assert result["qit_side"]["searched"] is True
    assert result["baseline_side"]["searched"] is True
    assert result["metric_pin"]["penalizes_trivially_injective_readouts_both_sides"] is True
    assert result["trajectory_pin"]["uses_exact_3_cell_set_invariant"] is False


def test_no_identity_leak_standard_fields_present() -> None:
    common = importlib.import_module("ecd06_prediction_first_inference_v1_common")
    result = common.build_prediction_first_object()
    leak = result["controls"]["no_identity_leak"]
    assert leak["status"] == "pass"
    assert "identity_leak_detected" in leak
    assert leak["direct_eval_target_lookup_allowed"] is False
    assert "heldout labels" in leak["identity_leak_exclusion_rule"] or "heldout_label" in str(leak["excluded_fields"])


def test_full_observability_regression_keeps_v0_death() -> None:
    common = importlib.import_module("ecd06_prediction_first_inference_v1_common")
    result = common.build_prediction_first_object()
    control = result["controls"]["v0_regression_full_observability"]
    assert control["passes"] is True
    assert control["transition_table_adjusted_error"] == 0.0
    assert control["regime_gate_status"] == common.REGIME_FAILURE_STATUS


def test_full_packet_commands_and_validator() -> None:
    subprocess.run([PY, str(SIM_DIR / "ecd06_prediction_first_inference_v1.py")], cwd=ROOT, check=True)
    subprocess.run([PY, str(SIM_DIR / "ecd06_prediction_first_inference_v1_jax.py")], cwd=ROOT, check=True)
    subprocess.run([PY, str(SIM_DIR / "ecd06_prediction_first_inference_v1_pytorch.py")], cwd=ROOT, check=True)
    subprocess.run(
        [
            "/opt/homebrew/bin/julia",
            "--startup-file=no",
            f"--project={ROOT / 'system_v5' / 'julia_carrier'}",
            str(SIM_DIR / "ecd06_prediction_first_inference_v1_julia.jl"),
        ],
        cwd=ROOT,
        check=True,
        env={"JULIA_LOAD_PATH": "@:@stdlib"},
    )
    subprocess.run([PY, str(SIM_DIR / "ecd06_prediction_first_inference_v1_envelope.py")], cwd=ROOT, check=True)
    subprocess.run([PY, str(SIM_DIR / "validate_ecd06_prediction_first_inference_v1.py")], cwd=ROOT, check=True)
    validator = json.loads((SIM_DIR / "results" / "ecd06_prediction_first_inference_v1_validator_results.json").read_text())
    assert validator["ok"] is True
