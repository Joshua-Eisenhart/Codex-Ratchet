from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "engine_16_stage_definition_correspondence_v0"
RESULT_DIR = SIM_DIR / "results"
RESULT = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"


def load_common():
    common_path = SIM_DIR / f"{SIM_ID}_common.py"
    spec = importlib.util.spec_from_file_location(f"{SIM_ID}_common", common_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict:
    assert path.is_file(), f"missing {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def test_build_card_pins_owner_challenge_g2a_and_g7() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    assert "you don't actually have the geometry and operators" in text
    assert "G.2a idempotency-from-birth" in text
    assert "G7 Definition Pin" in text
    assert "Definitions are pinned before correspondence computation" in text
    assert "NO git add/commit" in text
    assert "Either correspondence outcome is valid" in text


def test_defined_16_emit_real_matrices_geometry_and_fingerprints() -> None:
    common = load_common()
    payload = common.build_packet()
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["claim_ceiling"] == "macro_stage_definition_correspondence_proposal_only"
    assert payload["definition_phase_pinned_before_correspondence"] is True
    assert len(payload["base_operator_rows"]) == 4
    assert len(payload["defined_stage_rows"]) == 16
    for row in payload["defined_stage_rows"]:
        assert len(row["matrix_bloch_3x3"]) == 3
        assert len(row["matrix_affine_4x4"]) == 4
        assert len(row["fingerprint"]) == 8
        assert row["component_id"].startswith("eng64_fp_")
        assert "fixed_point_subspace" in row["geometry"]
        assert "entropy_delta" in row["geometry"]
        assert "moved_bloch_directions" in row["geometry"]


def test_correspondence_matrix_is_full_and_outcome_is_honest() -> None:
    common = load_common()
    payload = common.build_packet()
    corr = payload["correspondence"]
    assert corr["result"] in {"MATCH", "MISMATCH"}
    assert corr["discovered_component_count"] == 16
    assert len(corr["match_matrix_16x16"]) == 16
    assert all(len(row) == 16 for row in corr["match_matrix_16x16"])
    if corr["perfect_bijection"]:
        assert corr["defined_components_without_discovered_counterpart"] == []
        assert corr["discovered_components_without_defined_counterpart"] == []
    else:
        assert corr["defined_components_without_discovered_counterpart"] or corr["discovered_components_without_defined_counterpart"]


def test_controls_are_killable_and_non_equivalence_is_computed() -> None:
    common = load_common()
    payload = common.build_packet()
    controls = payload["controls"]
    assert controls["erase_order_polarity"]["n_distinct"] <= 8
    assert controls["erase_chirality"]["all_lr_pairs_merge"] is True
    assert controls["scramble_operator_assignments"]["does_not_improve_correspondence"] is True
    assert controls["identity_stages"]["n_distinct"] == 1
    neq = payload["non_equivalence_matrix"]
    assert len(neq["alias_distinct_matrix_16x16"]) == 16
    assert len(neq["fingerprint_l2_distance_matrix_16x16"]) == 16


def test_envelope_and_validator_pass() -> None:
    envelope = load_json(ENVELOPE)
    assert envelope["schema_version"] == "three_engine_sim_result_v1"
    assert envelope["all_pass"] is True
    assert set(envelope["engines"]) == {"julia", "jax", "pytorch"}
    assert envelope["builder_gates"]["G_2a_idempotency_from_birth"] is True
    assert envelope["builder_gates"]["G7_definitions_pinned_before_correspondence"] is True
    assert envelope["promotion_allowed"] is False
    assert envelope["formal_admission_allowed"] is False

    validator = SIM_DIR / f"validate_{SIM_ID}.py"
    result = subprocess.run(
        ["/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", str(validator.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
