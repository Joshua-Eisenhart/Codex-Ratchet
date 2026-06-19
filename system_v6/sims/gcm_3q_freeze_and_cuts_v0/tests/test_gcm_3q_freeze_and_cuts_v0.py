from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_3q_freeze_and_cuts_v0"
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


def test_build_card_declares_3q_attachment_surface() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for required in (
        SIM_ID,
        "freeze/registry + cut layers",
        "carve-attached",
        "3Q",
        "A|BC",
        "B|AC",
        "C|AB",
        "545",
        "gcm3qobj_",
        "CKW",
        "G.2a",
        "scratch_diagnostic",
        "runtime flux is blocked",
        "NO git add/commit",
    ):
        assert required in text


def test_packet_builds_content_derived_registry_and_cross_rung_lineage() -> None:
    common = load_common()
    packet = common.build_packet(write=False)
    registry = common.build_3q_registry(
        common.load_json(common.THREE_Q_CARVE_RESULT),
        common.load_json(common.TWO_Q_FREEZE_REGISTRY),
    )

    assert packet["classification"] == "scratch_diagnostic"
    assert packet["promotion_allowed"] is False
    assert packet["formal_admission_allowed"] is False
    assert packet["declared_surface"] == "freeze/registry + cut layers | carve-attached | 3Q"
    assert packet["coordinates"] == {
        "layers": "3Q freeze/registry plus all bipartition cut attachments",
        "nesting": "A|BC, B|AC, C|AB cut lattice",
        "qubit_depth": "3Q",
    }
    assert registry["gcm_3q_object_id"].startswith("gcm3qobj_")
    assert registry["counts"]["survivor_count"] == 545
    assert registry["counts"]["quotient_class_count"] == 9
    assert registry["counts"]["product_lift_survivor_count"] == 544
    assert registry["counts"]["tripartite_entangled_survivor_count"] == 1
    assert len(registry["frozen_3q_registry"]["survivors"]) == 545
    assert len(registry["frozen_3q_registry"]["quotient_classes"]) == 9
    assert len(registry["frozen_3q_registry"]["candidate_regions"]) >= 1

    lineage = packet["cross_rung_lineage"]
    assert lineage["two_q_to_3q_product_embedding"]["input_2q_survivor_count"] == 544
    assert lineage["two_q_to_3q_product_embedding"]["lifted_3q_survivor_count"] == 544
    assert lineage["two_q_to_3q_product_embedding"]["all_2q_survivors_have_one_3q_lift"] is True
    assert lineage["three_q_to_2q_projection"]["product_lift_TrC_reproduces_2q_local_pins"] is True
    assert lineage["three_q_to_2q_projection"]["max_abs_delta_TrC_vs_2q_local_pin_product"] == 0.0
    assert lineage["three_q_to_2q_projection"]["full_rho_AB_reproduced_product_rows"] == 528
    assert lineage["three_q_to_2q_projection"]["full_rho_AB_correlation_not_claimed_rows"] == 16


def test_all_three_cuts_store_reduced_matrices_entropy_and_schmidt_strata() -> None:
    common = load_common()
    packet = common.build_packet(write=False)
    rows = packet["cut_tables"]["survivor_cut_rows"]

    assert len(rows) == 545
    assert packet["cut_lattice"]["bipartitions"] == ["A|BC", "B|AC", "C|AB"]
    for row in rows[:12] + [packet["tripartite_only_anchor_profile"]]:
        assert set(row["cuts"]) == {"A|BC", "B|AC", "C|AB"}
        for cut_name, cut in row["cuts"].items():
            left, right = cut_name.split("|")
            assert cut["rho_left"]
            assert cut["rho_right"]
            assert cut["rho_left_id"].startswith(f"rho{left}")
            assert cut["rho_right_id"].startswith(f"rho{right}")
            assert set(cut["entropy_values"]) >= {
                "S_rho_left",
                "S_rho_right",
                "S_rho_ABC",
                "conditional_S_left_given_right",
                "conditional_S_right_given_left",
                "mutual_I_left_right",
                "coherent_I_c_left_to_right",
                "coherent_I_c_right_to_left",
                "negativity",
            }
            assert cut["schmidt_stratum"]["left_rank"] >= 1
            assert cut["schmidt_stratum"]["right_rank"] >= 1

    anchor = packet["tripartite_only_anchor_profile"]
    assert anchor["family"] == "entangled_boundary_anchor"
    assert anchor["tripartite_entangled_anchor"] is True
    assert all(cut["schmidt_stratum"]["schmidt_applicable"] for cut in anchor["cuts"].values())
    assert all(cut["schmidt_stratum"]["schmidt_rank"] == 2 for cut in anchor["cuts"].values())
    assert all(cut["entropy_values"]["negativity"] > 0.0 for cut in anchor["cuts"].values())


def test_ckw_monogamy_controls_and_helper_negatives_are_red() -> None:
    common = load_common()
    packet = common.build_packet(write=False)

    ckw = packet["monogamy_table"]
    assert ckw["computed_from_stored_rho_ABC"] is True
    assert ckw["entangled_survivor_count_checked"] == 1
    assert ckw["all_party_cuts_satisfy_ckw"] is True
    assert ckw["rows"][0]["state_id"] == "locally_rotated_generalized_GHZ_anchor"

    controls = packet["controls"]
    assert controls["two_q_regression"]["partial_traces_reproduce"] is True
    assert controls["two_q_regression"]["product_lift_checked_count"] == 544
    assert controls["two_q_regression"]["full_rho_AB_reproduced_product_rows"] == 528
    assert controls["two_q_regression"]["full_rho_AB_correlation_not_claimed_rows"] == 16
    for rung in ("1Q", "2Q", "3Q"):
        assert controls["substrate_negatives"][rung]["lineage_free"]["ok"] is False
        assert controls["substrate_negatives"][rung]["forged_registry"]["ok"] is False
        assert controls["substrate_negatives"][rung]["stale_lineage"]["ok"] is False
        assert controls["substrate_negatives"][rung]["lineage_free"]["error_codes"]
    assert controls["substrate_positive"]["1Q"]["ok"] is True
    assert controls["substrate_positive"]["2Q"]["ok"] is True
    assert controls["substrate_positive"]["3Q"]["ok"] is True


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
