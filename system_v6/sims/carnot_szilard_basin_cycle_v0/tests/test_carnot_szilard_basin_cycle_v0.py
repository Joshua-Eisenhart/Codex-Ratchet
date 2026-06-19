from __future__ import annotations

import json
import math
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
RESULT_DIR = SIM_DIR / "results"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

import carnot_szilard_basin_cycle_v0_common as common  # noqa: E402
import validate_carnot_szilard_basin_cycle_v0 as validator  # noqa: E402


def load_envelope() -> dict:
    return json.loads((RESULT_DIR / f"{common.SIM_ID}_envelope_results.json").read_text(encoding="utf-8"))


def test_packet_boundary_and_build_card() -> None:
    build_card = SIM_DIR / "build_card.md"
    assert build_card.is_file()
    text = build_card.read_text(encoding="utf-8")
    assert common.SIM_ID in text
    assert "NO git add/commit" in text
    assert "boundaries 1 and 4 stay open" in text
    envelope = load_envelope()
    assert envelope["classification"] == "scratch_diagnostic"
    assert envelope["promotion_allowed"] is False
    assert envelope["formal_admission_allowed"] is False
    assert envelope["row_classification"] == "classical_baseline"
    assert "heat/work variables on the basin carrier" in envelope["honest_boundaries"][0]
    assert "bath-gating" in envelope["honest_boundaries"][3]


def test_basin_cycle_rows_compute_sample_and_full_floor() -> None:
    envelope = load_envelope()
    rows = envelope["basin_cycle_rows"]
    assert {row["dof_id"] for row in rows} == {"G0", "G2", "stage_shift_Rx_to_Rz"}
    for row in rows:
        assert row["m_sample"] == 9
        assert row["m_full_graph"] == 33
        assert row["m_readings_reported"] == ["sample", "full_graph"]
        assert math.isclose(row["readings"]["sample"]["floor_nats"], math.log(9), rel_tol=0, abs_tol=1e-12)
        assert math.isclose(row["readings"]["full_graph"]["floor_nats"], math.log(33), rel_tol=0, abs_tol=1e-12)
        for reading in ("sample", "full_graph"):
            account = row["readings"][reading]
            assert account["floor_test"]["status"] == "pass"
            assert account["closure_account"]["closed_under_state_plus_record"] is True
            assert account["closure_account"]["ledger_defect_nats"] == 0.0
            assert account["record_variant"]["honesty_clause_pass"] is True
            assert account["record_variant"]["full_cycle_with_reset_cost_nats"] == account["floor_nats"]
            assert account["record_erased_control"]["status"] == "floor_binds"
            assert account["over_recorded_control"]["reset_charge_appears"] is True


def test_controls_and_misledger_gate_are_nonvacuous() -> None:
    envelope = load_envelope()
    controls = envelope["controls"]
    assert controls["record_erased"]["all_floor_rows_bind"] is True
    assert controls["over_recorded"]["all_reset_charges_appear"] is True
    assert controls["commuting_control_D_I"]["D_equals_I"] is True
    assert controls["shuffled_order_N01"]["status"] in {"BOUNDARY", "fail"}
    assert controls["misledgered_omitted_entry"]["caught_by_closure_gate"] is True
    assert controls["misledgered_omitted_entry"]["omitted_field"] == "reset_charge_nats"


def test_alternation_gap_and_structure_map() -> None:
    envelope = load_envelope()
    alt = envelope["alternation_rows"]
    assert alt["commuting_control"]["D_equals_I"] is True
    assert alt["noncommuting_small_stroke"]["gap_matches_leading_order"] is True
    assert alt["noncommuting_small_stroke"]["relative_error"] < 0.03
    assert alt["noncommuting_small_stroke"]["gap_norm"] > 0
    assert len(envelope["structure_map_table"]) >= 7
    boundaries = "\n".join(row["boundary"] for row in envelope["structure_map_table"])
    assert "no heat bath variable" in boundaries
    assert "no basin counterpart to adiabatic isolation" in boundaries
    assert "do not reuse Z4 record" in boundaries


def test_smt_rows_and_packet_validator_pass() -> None:
    envelope = load_envelope()
    proofs = envelope["crossover_proofs"]
    for name in ("z3", "cvc5"):
        assert proofs[name]["ran"] is True
        assert proofs[name]["load_bearing"] is True
        assert proofs[name]["verdict"] == "unsat"
        assert proofs[name]["erased_flip_verdict"] == "sat"
        assert proofs[name]["misledger_flip_verdict"] == "sat"
        assert proofs[name]["bound_values"]["sample_m"] == 9
        assert proofs[name]["bound_values"]["full_graph_m"] == 33
    errors = validator.validate_payload(envelope)
    assert errors == []
