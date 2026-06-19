from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_constraint_carve_v1"
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


def test_build_card_carries_v0_repair_contract_and_g2a_boundary() -> None:
    card = SIM_DIR / "build_card.md"
    assert card.is_file()
    text = card.read_text(encoding="utf-8")
    assert SIM_ID in text
    assert "Split C4 out of the admissibility carve" in text
    assert "identity_leak_*" in text
    assert "terrain readout as a downstream post-carve analysis" in text
    assert "C2 predicate source line" in text
    assert "scratch_diagnostic" in text
    assert "not THE manifold" in text
    assert "NO git add/commit" in text
    assert "G.2a" in text
    assert "scripts/builder_audit_boundary.py" in text


def test_common_packet_is_blind_c1_to_c3_and_reproduces_decisive_v0_diff() -> None:
    common = load_common()
    payload = common.build_packet()
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["candidate_space"]["candidate_count"] == 125
    assert payload["candidate_space"]["density_subcarrier_count"] == 33
    assert payload["survivor_count"] == 16
    assert len(payload["kill_ledger"]) == 109
    assert payload["kill_counts_by_constraint"] == {
        "C1_finite_density_carrier": 92,
        "C2_probe_distinguishability_xz_local_adapter_pin": 5,
        "C3_persistence_n01_order_gap": 12,
    }
    assert [row["id"] for row in payload["constraint_family_C"]] == [
        "C1_finite_density_carrier",
        "C2_probe_distinguishability_xz_local_adapter_pin",
        "C3_persistence_n01_order_gap",
    ]
    assert payload["terrain_blindness_guard"]["clean"] is True
    assert payload["controls"]["blindness_control"]["injected_variant_caught"] is True
    assert payload["quotient"]["probe_family"] == ["sigma_x", "sigma_z"]
    assert payload["quotient"]["class_count"] == 8

    regression = payload["v0_regression_row"]
    assert regression["v0_regression_survivor_count"] == 8
    assert regression["v0_regression_quotient_class_count"] == 4
    assert regression["diff_demonstrates_contamination"] is True
    assert regression["removed_by_v0_C4_candidate_ids"] == [31, 33, 41, 43, 81, 83, 91, 93]


def test_existence_probes_controls_and_post_carve_readout_are_bounded() -> None:
    common = load_common()
    payload = common.build_packet()
    existence = payload["existence_tests"]
    assert existence["stable"] is True
    assert existence["independent"] is True
    assert existence["identity_leak_detected"] is True
    assert existence["identity_leak_excluded_best_accuracy"] < 1.0
    assert existence["chart_recoverable"] is True
    assert existence["negative_controlled"] is True

    controls = payload["controls"]
    assert controls["empty_C"]["survivor_count"] == 125
    assert controls["empty_C"]["degenerate_no_manifold"] is True
    assert controls["overconstrained_C"]["survivor_count"] == 0
    assert controls["overconstrained_C"]["all_killed"] is True
    assert controls["probe_family_scramble"]["quotient_moved"] is True
    assert all(row["bite"] for row in controls["constraint_erasure"])

    readout = payload["post_carve_terrain_readout"]
    assert readout["can_affect_survival"] is False
    assert readout["survival_inputs"] == []
    assert readout["class_counts_by_readout_label"] == {
        "mixed_active_probe_region": 4,
        "x_axis_active_region": 2,
        "z_axis_active_region": 2,
    }


def test_m_c_t_hook_is_recomputed_from_blind_c_not_v0_c4() -> None:
    common = load_common()
    payload = common.build_packet()
    hook = payload["M_C_t_hook"]
    assert hook["update"] == "C -> C_prime = C plus C5_t1_positive_active_coordinate_pin"
    assert hook["survivor_count"] == 8
    assert hook["quotient_class_count"] == 4
    assert hook["survivor_candidate_ids"] == [58, 68, 81, 82, 83, 91, 92, 93]


def test_three_engine_envelope_validator_and_tests_pass() -> None:
    payload = load_envelope()
    assert payload["schema_version"] == "three_engine_sim_result_v1"
    assert payload["schema"] == "gcm_constraint_carve_v1_envelope_v1"
    assert payload["all_pass"] is True
    assert set(payload["engine_lanes"]) == {"pytorch", "jax", "julia"}
    assert payload["engine_consensus"]["survivor_count_agreement"] is True
    assert payload["engine_consensus"]["quotient_class_count_agreement"] is True
    assert payload["engine_consensus"]["component_count_agreement"] is True
    assert payload["engine_consensus"]["v0_regression_survivor_count_agreement"] is True
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
