from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_4q_freeze_and_cuts_v0"
RESULT = SIM_DIR / "results" / f"{SIM_ID}_results.json"
REGISTRY = SIM_DIR / "results" / f"{SIM_ID}_registry.json"
VALIDATOR = SIM_DIR / "results" / f"{SIM_ID}_validator_results.json"
LINEAGE_FREE = SIM_DIR / "results" / f"{SIM_ID}_lineage_free_negative.json"
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


def test_build_card_declares_4q_cut_state_surface() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for required in (
        SIM_ID,
        "freeze/registry + cut layers",
        "carve-attached",
        "4Q",
        "1|234",
        "2|134",
        "3|124",
        "4|123",
        "12|34",
        "13|24",
        "14|23",
        "546",
        "cut_state_available=true",
        "G.2a",
        "scratch_diagnostic",
        "NO git add/commit",
    ):
        assert required in text


def test_packet_builds_content_derived_registry_and_3q_4q_lineage() -> None:
    common = load_common()
    packet = common.build_packet(write=False)
    registry = common.build_4q_registry(
        common.load_json(common.FOUR_Q_CARVE_RESULT),
        common.load_json(common.THREE_Q_FREEZE_REGISTRY),
    )

    assert packet["classification"] == "scratch_diagnostic"
    assert packet["promotion_allowed"] is False
    assert packet["formal_admission_allowed"] is False
    assert packet["declared_surface"] == "freeze/registry + cut layers | carve-attached | 4Q"
    assert packet["cut_state_available"] is True
    assert registry["gcm_4q_object_id"].startswith("gcm4qobj_")
    assert registry["counts"]["survivor_count"] == 546
    assert registry["counts"]["quotient_class_count"] == 9
    assert registry["counts"]["product_lift_survivor_count"] == 545
    assert registry["counts"]["four_partite_entangled_survivor_count"] == 1

    lineage = packet["cross_rung_lineage"]
    assert lineage["three_q_to_4q_product_embedding"]["input_3q_survivor_count"] == 545
    assert lineage["three_q_to_4q_product_embedding"]["lifted_4q_survivor_count"] == 545
    assert lineage["three_q_to_4q_product_embedding"]["all_3q_survivors_have_one_4q_lift"] is True
    assert lineage["four_q_to_3q_projection"]["product_lift_TrD_reproduces_3q_states"] is True
    assert lineage["four_q_to_3q_projection"]["max_abs_delta_TrD_vs_3q_rho"] == 0.0


def test_all_seven_cuts_store_reduced_matrices_and_entropy_family() -> None:
    common = load_common()
    packet = common.build_packet(write=False)
    rows = packet["cut_tables"]["survivor_cut_rows"]

    assert len(rows) == 546
    assert packet["cut_lattice"]["bipartitions"] == ["1|234", "2|134", "3|124", "4|123", "12|34", "13|24", "14|23"]
    assert packet["cut_state_available_evidence"]["stored_matrix_pair_count"] == 546 * 7
    for row in rows[:8] + [packet["four_partite_anchor_profile"]]:
        assert row["cut_state_available"] is True
        assert set(row["cuts"]) == set(common.CUTS)
        for cut_name, cut in row["cuts"].items():
            assert cut["rho_left"]
            assert cut["rho_right"]
            assert cut["rho_left_id"]
            assert cut["rho_right_id"]
            assert cut["stored_reduced_matrices"] is True
            assert set(cut["entropy_values"]) >= {
                "S_rho_left",
                "S_rho_right",
                "S_rho_ABCD",
                "conditional_S_left_given_right",
                "conditional_S_right_given_left",
                "mutual_I_left_right",
                "coherent_I_c_left_to_right",
                "coherent_I_c_right_to_left",
                "negativity",
                "log_negativity",
            }
            assert cut["schmidt_stratum"]["left_rank"] >= 1
            assert cut["schmidt_stratum"]["right_rank"] >= 1

    anchor = packet["four_partite_anchor_profile"]
    assert anchor["candidate_label"] == "locally_rotated_generalized_GHZ4_anchor"
    assert anchor["four_partite_entangled_anchor"] is True
    assert all(cut["schmidt_stratum"]["schmidt_applicable"] for cut in anchor["cuts"].values())
    assert all(cut["entropy_values"]["negativity"] > 0.0 for cut in anchor["cuts"].values())


def test_monogamy_controls_and_helper_negatives_are_red() -> None:
    common = load_common()
    packet = common.build_packet(write=False)

    mono = packet["monogamy_table"]
    assert mono["computed_from_stored_rho_ABCD"] is True
    assert mono["residual_4_tangle_claimed"] is False
    assert mono["pure_survivor_count_checked"] >= 1
    assert mono["all_focus_qubits_satisfy_ckw"] is True

    controls = packet["controls"]
    assert controls["three_q_regression"]["partial_traces_reproduce"] is True
    assert controls["three_q_regression"]["product_lift_checked_count"] == 545
    for rung in ("1Q", "2Q", "3Q", "4Q"):
        assert controls["substrate_positive"][rung]["ok"] is True
        assert controls["substrate_negatives"][rung]["lineage_free"]["ok"] is False
        assert controls["substrate_negatives"][rung]["forged_registry"]["ok"] is False
        assert controls["substrate_negatives"][rung]["stale_lineage"]["ok"] is False
        assert controls["substrate_negatives"][rung]["lineage_free"]["error_codes"]


def test_script_writes_results_negatives_and_validator_accepts_them() -> None:
    run = subprocess.run(
        [SIM_PY, str((SIM_DIR / f"{SIM_ID}_common.py").relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert RESULT.is_file()
    assert REGISTRY.is_file()
    assert LINEAGE_FREE.is_file()

    validator = subprocess.run(
        [SIM_PY, str((SIM_DIR / f"validate_{SIM_ID}.py").relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert validator.returncode == 0, validator.stdout + validator.stderr
    payload = json.loads(VALIDATOR.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["errors"] == []

    helper = subprocess.run(
        [SIM_PY, "scripts/gcm_substrate_check.py", str(RESULT.relative_to(ROOT)), "--registry", str(REGISTRY.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )
    assert helper.returncode == 0, helper.stdout + helper.stderr
