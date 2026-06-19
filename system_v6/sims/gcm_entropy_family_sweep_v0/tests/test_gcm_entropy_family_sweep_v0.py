from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_entropy_family_sweep_v0"
RESULT = SIM_DIR / "results" / f"{SIM_ID}_results.json"
ENVELOPE = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"


def load_module():
    source = SIM_DIR / f"{SIM_ID}.py"
    assert source.is_file(), f"missing sim module: {source}"
    spec = importlib.util.spec_from_file_location(SIM_ID, source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_card_declares_contract_coordinates_and_boundaries() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for required in (
        SIM_ID,
        "layers 3-12",
        "integrated-onto-the-carve",
        "1Q",
        "gcmobj_a40e54e13cec01466c9d675028b3574b",
        "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed",
        "gcm_substrate_check",
        "lineage-free negative",
        "G.2a",
        "scratch_diagnostic",
        "carrier-and-pins-relative",
        "NO git add/commit",
    ):
        assert required in text


def test_packet_computes_all_requested_entropy_families_over_lineage() -> None:
    module = load_module()
    payload = module.build_packet(write=False)

    assert payload["sim_id"] == SIM_ID
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["gcm_lineage"]["gcm_object_id"] == module.EXPECTED_OBJECT_ID
    assert payload["gcm_lineage"]["registry_body_sha256"] == module.EXPECTED_REGISTRY_BODY_SHA256
    assert payload["three_coordinates"] == {
        "layers": "3-12 (entropy dimension)",
        "nesting": "integrated-onto-the-carve",
        "qubit_depth": "1Q",
    }

    counts = payload["counts"]
    assert counts["survivor_count"] == 16
    assert counts["quotient_class_count"] == 8
    assert counts["occupied_shell_count"] == 5

    rows = payload["entropy_tables"]["survivor_entropy_rows"]
    assert len(rows) == 16
    for row in rows:
        families = row["computed_families"]
        assert families["von_neumann_nats"] == pytest.approx(0.0, abs=1e-12)
        assert set(families["renyi_nats_by_alpha"]) == {"0", "0.5", "2", "4", "inf"}
        assert set(families["tsallis_by_q"]) == {"0.5", "2", "4"}
        assert families["min_entropy_nats"] == pytest.approx(0.0, abs=1e-12)
        assert families["max_entropy_nats"] == pytest.approx(0.0, abs=1e-12)
        assert families["linear_entropy"] == pytest.approx(0.0, abs=1e-12)
        assert row["survivor_id"].startswith("surv_")
        assert row["quotient_class_id"].startswith("qcls_")
        assert row["shell_id"].startswith("shell_")

    class_rows = payload["entropy_tables"]["class_mixed_state_entropy_rows"]
    assert len(class_rows) == 8
    assert all(row["mixed_von_neumann_nats"] == pytest.approx(0.0, abs=1e-12) for row in class_rows)
    assert payload["entropy_tables"]["shell_weighted_forms"]["occupied_shell_count"] == 5
    assert payload["entropy_tables"]["shell_weighted_forms"]["shell_distribution_entropy_nats"] > 0


def test_nesting_and_survival_rows_are_honest_about_1q_availability() -> None:
    module = load_module()
    payload = module.build_packet(write=False)

    nesting = {row["family"]: row for row in payload["nesting_constraint_rows"]}
    assert nesting["conditional_entropy"]["status"] == "requires_more_structure"
    assert "bipartition" in nesting["conditional_entropy"]["enabling_requirement"]
    assert nesting["mutual_information"]["status"] == "requires_more_structure"
    assert nesting["coherent_information"]["status"] == "requires_more_structure"
    assert nesting["entanglement_negativity"]["status"] == "requires_more_structure"
    assert nesting["von_neumann_1q"]["status"] == "admissible_at_this_layer"
    assert nesting["renyi_ladder_1q"]["status"] == "admissible_at_this_layer"

    survival = {row["family"]: row for row in payload["survival_rows"]}
    assert survival["von_neumann_1q"]["class_separation_count"] == 1
    assert survival["von_neumann_1q"]["separates_8_classes"] is False
    assert survival["linear_entropy_1q"]["degeneracy"] == "all_16_survivors_same_value"
    assert survival["shell_log_surprisal"]["separates_5_shells"] is False
    assert survival["shell_log_surprisal"]["shell_separation_count"] == 2


def test_controls_have_substrate_teeth_phase_invariance_and_scramble_boundary() -> None:
    module = load_module()
    payload = module.build_packet(write=False)
    controls = payload["controls"]

    assert controls["substrate_positive"]["ok"] is True
    assert controls["lineage_free_negative"]["ok"] is False
    assert controls["lineage_free_negative_failed_as_required"] is True
    assert controls["phase_quotient_invariance"]["all_entropy_families_invariant"] is True
    assert controls["phase_quotient_invariance"]["checked_family_count"] >= 10
    assert controls["scrambled_class_assignment"]["separating_entropy_family_count"] == 0
    assert controls["scrambled_class_assignment"]["control_interpretation"] == "no_1Q_entropy_family_separates_classes_on_this_object"


def test_script_writes_results_envelope_and_validator_accepts_them() -> None:
    run = subprocess.run([SIM_PY, str((SIM_DIR / f"{SIM_ID}.py").relative_to(ROOT))], cwd=ROOT, text=True, capture_output=True)
    assert run.returncode == 0, run.stdout + run.stderr
    assert RESULT.is_file()
    assert ENVELOPE.is_file()
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    envelope = json.loads(ENVELOPE.read_text(encoding="utf-8"))
    assert result["all_pass"] is True
    assert envelope["all_pass"] is True
    assert envelope["no_builder_audit_verdict"] is True

    validator = subprocess.run(
        [SIM_PY, str((SIM_DIR / f"validate_{SIM_ID}.py").relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert validator.returncode == 0, validator.stdout + validator.stderr
