from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_constraint_carve_v0"
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"


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


def test_build_card_pins_constraint_carve_and_g2a_boundary() -> None:
    card = SIM_DIR / "build_card.md"
    assert card.is_file()
    text = card.read_text(encoding="utf-8")
    assert SIM_ID in text
    assert "M(C) = {x : x admissible under C}" in text
    assert "where is the constraint set and what did it carve?" in text
    assert "scratch_diagnostic" in text
    assert "not THE manifold" in text
    assert "NO git add/commit" in text
    assert "G.2a idempotency-from-birth" in text
    assert "scripts/builder_audit_boundary.py" in text


def test_common_packet_computes_m_c_quotient_and_carving_data() -> None:
    common = load_common()
    payload = common.build_packet()
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["candidate_space"]["candidate_count"] == 125
    assert payload["candidate_space"]["density_subcarrier_count"] == 33
    assert payload["survivor_count"] == 8
    assert len(payload["kill_ledger"]) == 117
    assert payload["kill_counts_by_constraint"] == {
        "C1_finite_density_carrier": 92,
        "C2_probe_distinguishability_xz": 5,
        "C3_persistence_n01_order_gap": 12,
        "C4_G7_operator_residency_pin": 8,
    }
    assert payload["quotient"]["probe_family"] == ["sigma_x", "sigma_z"]
    assert payload["quotient"]["class_count"] == 4
    assert payload["stability_certificate"]["stable"] is True
    assert len(payload["adjacency_connectivity"]["survivor_components"]) == 3
    assert payload["terrain_question"]["answer"] == "partial_macro_match_not_full_atlas"


def test_existence_probes_and_controls_are_killable() -> None:
    common = load_common()
    payload = common.build_packet()
    existence = payload["existence_tests"]
    assert existence["stable"] is True
    assert existence["independent"] is True
    assert existence["chart_recoverable"] is True
    assert existence["negative_controlled"] is True

    controls = payload["controls"]
    assert controls["empty_C"]["survivor_count"] == 125
    assert controls["empty_C"]["degenerate_no_manifold"] is True
    assert controls["overconstrained_C"]["survivor_count"] == 0
    assert controls["overconstrained_C"]["all_killed"] is True
    assert controls["probe_family_scramble"]["quotient_moved"] is True
    erasures = controls["constraint_erasure"]
    assert {row["dropped_constraint"] for row in erasures} == {
        "C1_finite_density_carrier",
        "C2_probe_distinguishability_xz",
        "C3_persistence_n01_order_gap",
        "C4_G7_operator_residency_pin",
    }
    assert all(row["bite"] for row in erasures)
    assert all(row["delta_count"] > 0 for row in erasures)


def test_m_c_t_hook_is_recomputed_not_relabelled() -> None:
    common = load_common()
    payload = common.build_packet()
    hook = payload["M_C_t_hook"]
    assert hook["update"] == "C -> C_prime = C plus C5_t1_orientation_pin"
    assert hook["survivor_count"] == 4
    assert hook["quotient_class_count"] == 2
    assert hook["survivor_candidate_ids"] == [58, 68, 82, 92]


def test_three_engine_envelope_validator_and_tests_pass() -> None:
    payload = load_envelope()
    assert payload["schema_version"] == "three_engine_sim_result_v1"
    assert payload["schema"] == "gcm_constraint_carve_v0_envelope_v1"
    assert payload["all_pass"] is True
    assert set(payload["engine_lanes"]) == {"pytorch", "jax", "julia"}
    assert payload["engine_consensus"]["survivor_count_agreement"] is True
    assert payload["engine_consensus"]["quotient_class_count_agreement"] is True
    assert payload["engine_consensus"]["component_count_agreement"] is True
    assert payload["builder_gates"]["G_2a_idempotency_from_birth"] is True
    assert payload["no_builder_audit_verdict"] is True
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False

    validator = SIM_DIR / f"validate_{SIM_ID}.py"
    result = subprocess.run(
        ["/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", str(validator.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
