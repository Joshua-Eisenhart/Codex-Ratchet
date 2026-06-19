from __future__ import annotations

import json
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
RESULT_DIR = SIM_DIR / "results"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

import root_randomness_entropy_discriminator_v0_common as common  # noqa: E402
import validate_root_randomness_entropy_discriminator_v0 as validator  # noqa: E402


def load_envelope() -> dict:
    return json.loads((RESULT_DIR / f"{common.SIM_ID}_envelope_results.json").read_text(encoding="utf-8"))


def test_build_card_and_claim_boundary() -> None:
    build_card = SIM_DIR / "build_card.md"
    assert build_card.is_file()
    text = build_card.read_text(encoding="utf-8")
    assert "root_randomness_entropy_discriminator_v0" in text
    assert "root_layer_discriminator_only" in text
    envelope = load_envelope()
    assert envelope["classification"] == "scratch_diagnostic"
    assert envelope["claim_ceiling"] == "root_layer_discriminator_only"
    assert envelope["promotion_allowed"] is False
    assert envelope["formal_admission_allowed"] is False
    assert envelope["all_pass"] is True
    assert envelope["envelope_built_with_helper"] is True
    assert envelope["build_helper_path"] == "scripts/build_three_engine_envelope.py"
    assert not (SIM_DIR / "audit_verdict.md").exists()


def test_source_rows_and_finite_observables_are_locked() -> None:
    envelope = load_envelope()
    source_rows = envelope["source_rows"]
    assert set(source_rows) == {"R01", "R02", "R03", "R04", "R05"}
    assert source_rows["R01"]["packet"] == common.SIM_ID
    assert "randomness exists" in source_rows["R01"]["quotes"][0]["quote"]
    assert "Entropy splits" in source_rows["R02"]["quotes"][0]["quote"]
    assert "direction of entropy flow" in source_rows["R03"]["quotes"][0]["quote"]
    assert "all possibilities" in source_rows["R04"]["quotes"][1]["quote"]
    assert "a~b" in source_rows["R05"]["quotes"][1]["quote"]
    table = envelope["discriminator_table"]
    assert {row["row_id"] for row in table} == {"R01", "R02", "R03", "R04", "R05"}
    for row in table:
        assert row["tiny_observable"]
        assert row["negative_control"]
        assert row["fresh_receipt"] == envelope["result_path"]
        assert row["claim_ceiling"] == "root_layer_discriminator_only"


def test_root_rows_are_computed_before_labels_or_geometry() -> None:
    envelope = load_envelope()
    root = envelope["root_randomness_first"]
    assert root["order"] == ["pinned_random_ensemble", "entropy_ladder", "label_readout_excluded", "geometry_readout_excluded"]
    assert root["counting_entropy_bits"]["num"] > 0
    assert root["von_neumann_entropy_nats"]["float"] > 0
    assert root["typed_counting_vn_agree_on_diagonal_density"] is True
    assert root["entropy_is_first_derived_structure"] is True
    assert envelope["finite_carrier"]["seed"] == 1729
    assert envelope["finite_carrier"]["sample_count"] == 16
    assert envelope["finite_carrier"]["outcome_alphabet"] == ["00", "01", "10", "11"]


def test_controls_have_teeth_without_overclaiming() -> None:
    envelope = load_envelope()
    controls = envelope["controls"]
    label_structured = controls["label_structured_control"]
    assert label_structured["same_ensemble_counts"] is True
    assert label_structured["label_rows_distinguish"] is True
    assert label_structured["root_rows_alone_do_not_read_label_meaning"] is True
    assert label_structured["root_randomness_first_has_teeth"] is True
    label_shuffle = controls["label_shuffle_control"]
    assert label_shuffle["root_rows_invariant"] is True
    assert label_shuffle["label_dependent_rows_changed"] is True
    assert label_shuffle["nominalism_row_computed"] is True
    geometry = controls["geometry_first_control"]
    assert geometry["order_changed"] is True
    assert geometry["root_rows_differ_from_randomness_first"] is True
    assert geometry["n01_style_order_test"] == "survived"


def test_smt_and_validator_pass() -> None:
    envelope = load_envelope()
    proofs = envelope["crossover_proofs"]
    assert proofs["z3"]["verdict"] == "unsat"
    assert proofs["cvc5"]["verdict"] == "unsat"
    assert proofs["julia_z3"]["verdict"] == "unsat"
    assert proofs["z3"]["perturbed_control_verdict"] == "sat"
    assert proofs["cvc5"]["perturbed_control_verdict"] == "sat"
    assert proofs["julia_z3"]["perturbed_control_verdict"] == "sat"
    assert envelope["builder_gates"]["smt_binds_computed_rows"] is True
    assert envelope["builder_gates"]["controls_nonvacuous"] is True
    errors = validator.validate_payload(envelope)
    assert errors == []
