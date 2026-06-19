from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "engine_16_stage_correspondence_v1"
RESULT_DIR = SIM_DIR / "results"
RESULT = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
LINEAGE_FREE_NEGATIVE = RESULT_DIR / f"{SIM_ID}_lineage_free_negative.json"


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


def test_build_card_pins_stage_table_substrate_and_g2a() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    assert "G.2a idempotency-from-birth" in text
    assert "G7 Definition Pin" in text
    assert "NO git add/commit" in text
    assert "Ti <-> D_z" in text
    assert "`TiSe` | `T_Se o D_z`" in text
    assert "gcmobj_a40e54e13cec01466c9d675028b3574b" in text
    assert "Either correspondence outcome is the result" in text


def test_defined_16_emit_real_affine_maps_and_eng64_fingerprints() -> None:
    common = load_common()
    payload = common.build_packet()
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["claim_ceiling"] == "hypothesis_test_only"
    assert payload["layer_declaration"]["layer"] == "15 ordered compositions"
    assert payload["definition_phase_pinned_before_correspondence"] is True
    assert len(payload["terrain_flow_rows"]) == 4
    assert len(payload["base_operator_rows"]) == 4
    assert len(payload["defined_stage_rows"]) == 16
    assert [row["authority_stage_token"] for row in payload["defined_stage_rows"]] == [row["stage_token"] for row in common.STAGE_TABLE]
    for row in payload["defined_stage_rows"]:
        assert len(row["matrix_bloch_3x3"]) == 3
        assert len(row["translation_bloch_3"]) == 3
        assert len(row["matrix_affine_4x4"]) == 4
        assert len(row["fingerprint"]) == 8
        assert row["component_id"].startswith("eng64_fp_")
        assert "entropy_delta" in row["geometry"]
        assert "affine_fixed_equation_augmented_nullspace" in row["geometry"]


def test_correspondence_matrix_is_full_and_outcome_is_honest() -> None:
    common = load_common()
    payload = common.build_packet()
    corr = payload["correspondence"]
    assert corr["verdict"] in {"full_bijection", "partial", "0-match_again"}
    assert corr["result"] in {"MATCH", "MISMATCH"}
    assert corr["discovered_component_count"] == 16
    assert len(corr["match_matrix_16x16"]) == 16
    assert all(len(row) == 16 for row in corr["match_matrix_16x16"])
    if corr["verdict"] == "full_bijection":
        assert corr["defined_components_without_discovered_counterpart"] == []
        assert corr["discovered_components_without_defined_counterpart"] == []
    elif corr["verdict"] == "partial":
        assert corr["failing_pairings"]
    else:
        assert corr["exact_matched_component_count"] == 0


def test_controls_and_substrate_are_killable() -> None:
    common = load_common()
    payload = common.build_packet()
    controls = payload["controls"]
    assert controls["order_erasure"]["collapsed_toward_8"] is True
    assert controls["pairing_scramble"]["wrong_pairing_scores_worse"] is True or controls["pairing_scramble"]["pairing_convention_doing_nothing"] is True
    assert controls["label_permutation_invariance"]["fingerprint_ids_unchanged"] is True
    assert controls["commuting_pair_honest_null_rule"]["reported_all_commuting_pairs"] is True
    assert payload["substrate_check"]["ok"] is True
    assert payload["lineage_free_negative_control"]["ok"] is False
    assert payload["gcm_lineage"]["gcm_object_id"] == "gcmobj_a40e54e13cec01466c9d675028b3574b"


def test_envelope_substrate_and_validator_pass() -> None:
    envelope = load_json(ENVELOPE)
    assert envelope["schema_version"] == "three_engine_sim_result_v1"
    assert envelope["all_pass"] is True
    assert set(envelope["engines"]) == {"julia", "jax", "pytorch"}
    assert envelope["builder_gates"]["G_2a_idempotency_from_birth"] is True
    assert envelope["builder_gates"]["substrate_first_gcm_lineage"] is True
    assert envelope["promotion_allowed"] is False
    assert envelope["formal_admission_allowed"] is False
    assert load_json(LINEAGE_FREE_NEGATIVE)["sim_id"] == SIM_ID

    validator = SIM_DIR / f"validate_{SIM_ID}.py"
    result = subprocess.run(
        ["/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", str(validator.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
