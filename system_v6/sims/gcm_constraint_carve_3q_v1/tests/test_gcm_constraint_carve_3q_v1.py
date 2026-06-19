from __future__ import annotations

import json
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[3]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))


def test_build_card_carries_v0_fail_contract() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for needle in (
        "G.2a",
        "every candidate's `rho_ABC`",
        "full constraint matrix per candidate",
        "CKW from the stored `rho_ABC`",
        "GHZ fails C2 and C3",
        "W fails C3 only",
        "552",
        "545",
        "9",
    ):
        assert needle in text


def test_common_packet_artifacts_states_and_full_matrix() -> None:
    import gcm_constraint_carve_3q_v1_common as common

    packet = common.build_packet()
    assert packet["candidate_space"]["candidate_count"] == 552
    assert packet["survivor_count"] == 545
    assert packet["quotient"]["class_count"] == 9

    state_artifacts = packet["state_artifacts"]
    states = state_artifacts["states_by_content_id"]
    index = state_artifacts["candidate_state_index"]
    assert len(index) == 552
    assert all(row["rho_ABC_content_id"] in states for row in index)
    assert all("rho_ABC" in states[row["rho_ABC_content_id"]] for row in index)
    assert len(state_artifacts["survivor_states"]) == 545
    assert all(row["rho_ABC_content_id"] in states for row in packet["survivors"])

    matrix = packet["constraint_matrix"]
    assert len(matrix) == 552
    assert len(packet["kill_ledger"]) == 552
    for row in matrix:
        assert set(row["constraints"]) == {"C1", "C2", "C3"}
        assert all(isinstance(row["constraints"][key]["pass"], bool) for key in ("C1", "C2", "C3"))
        assert row["rho_ABC_content_id"] in states


def test_ghz_w_rows_are_matrix_based_not_first_failed_label() -> None:
    import gcm_constraint_carve_3q_v1_common as common

    packet = common.build_packet()
    rows = packet["ghz_w_matrix_finding"]["rows"]
    assert rows["GHZ"]["pass_fail"] == {"C1": True, "C2": False, "C3": False}
    assert rows["GHZ"]["failed_constraints"] == ["C2", "C3"]
    assert rows["W"]["pass_fail"] == {"C1": True, "C2": True, "C3": False}
    assert rows["W"]["failed_constraints"] == ["C3"]
    assert packet["ghz_w_matrix_finding"]["source"] == "full_constraint_matrix"


def test_ckw_is_recomputed_from_stored_rho_for_survivors() -> None:
    import gcm_constraint_carve_3q_v1_common as common

    packet = common.build_packet()
    ckw = packet["monogamy_ckw_recomputed_from_stored_rho"]
    assert ckw["computed_from_stored_rho_ABC"] is True
    assert ckw["survivor_count_checked"] == 1
    assert ckw["all_party_cuts_satisfy_ckw"] is True
    row = ckw["rows"][0]
    assert row["state_id"] == "locally_rotated_generalized_GHZ_anchor"
    assert row["rho_ABC_content_id"] in packet["state_artifacts"]["states_by_content_id"]
    assert set(row["party_cuts"]) == {"A|BC", "B|AC", "C|AB"}
    for cut in row["party_cuts"].values():
        assert cut["satisfies_ckw"] is True
        assert cut["ckw_margin"] >= -1.0e-10


def test_substrate_controls_and_validator_result_when_present() -> None:
    import gcm_constraint_carve_3q_v1_common as common
    from gcm_substrate_check import gcm_substrate_check

    packet = common.build_packet()
    assert gcm_substrate_check(packet)["ok"] is True
    assert packet["lineage_free_negative"]["red"] is True
    assert packet["terrain_blindness_guard"]["clean"] is True
    assert packet["controls"]["injection_red"]["red"] is True
    assert packet["controls"]["regressions"]["one_q"]["object_id_match"] is True
    assert packet["controls"]["regressions"]["two_q"]["survivor_count"] == 544

    result_path = SIM_DIR / "results" / "gcm_constraint_carve_3q_v1_validator_results.json"
    if result_path.exists():
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        assert payload["ok"] is True
