from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_DIR = ROOT / "system_v6" / "sims" / "gcm_ratchet_order_matrix_v1"
RESULT_PATH = SIM_DIR / "results" / "gcm_ratchet_order_matrix_v1_results.json"
VALIDATOR_PATH = SIM_DIR / "validate_gcm_ratchet_order_matrix_v1.py"
PYTHON = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_validator() -> dict:
    completed = subprocess.run(
        [str(PYTHON), str(VALIDATOR_PATH)],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return load_json(SIM_DIR / "results" / "gcm_ratchet_order_matrix_v1_validator_results.json")


def test_build_card_and_assessment_are_present() -> None:
    build_card = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    assert "gcm_ratchet_order_matrix_v1" in build_card
    assert "full Part-C alphabet" in build_card
    assert "blocked_no_realization" in build_card
    assert "NO git add/commit" in build_card
    assert (SIM_DIR / "builder_self_assessment.md").exists()


def test_result_passes_validator_boundary_and_substrate_negatives() -> None:
    validator = run_validator()
    assert validator["ok"] is True
    assert validator["classification"] == "scratch_diagnostic"
    assert validator["substrate_check"]["ok"] is True
    assert validator["lineage_free_negative"]["ok"] is False
    assert validator["boundary"]["ok"] is True


def test_full_part_c_alphabet_and_row_local_coordinates() -> None:
    payload = load_json(RESULT_PATH)
    steps = payload["step_registry"]
    assert [step["part_c_symbol"] for step in steps] == ["S", "Q", "W", "F", "T", "O", "D"]
    assert [step["step_id"] for step in steps] == [
        "SHELL_LEAF_CONDITIONING",
        "QUOTIENT_LENS_EQUIVALENCE",
        "LOCAL_WINDOW_SUPPORT_RESTRICTION",
        "FLUX_HOLONOMY_LOCK",
        "TERRAIN_CONDITIONING",
        "OPERATOR_RESIDENCY_PRECEDENCE",
        "DEPTH_LADDER_CLIMB",
    ]
    for step in steps:
        assert step["domain"]
        assert step["codomain"]
        assert step["coordinates"]["geometric_layer"]
        assert step["coordinates"]["nesting_state"] in {"free", "restricted", "quotiented", "ratcheted", "integrated"}
        assert step["coordinates"]["qubit_depth"] == "1Q"
    assert steps[-1]["realization_status"] == "realized_cross_rung_embedding"
    assert any(item["status"] == "blocked_no_realization" for item in payload["blocked_components"])


def test_realized_pair_matrix_extends_v0_regressions_exactly() -> None:
    payload = load_json(RESULT_PATH)
    realized = [step for step in payload["step_registry"] if step["realized"]]
    matrix = payload["pairwise_matrix"]
    assert len(realized) == 7
    assert len(matrix) == len(realized) * len(realized)
    assert payload["v0_regression"]["reproduced"] is True
    assert payload["v0_regression"]["checked_ordered_pair_count"] == 20
    assert {tuple(edge) for edge in payload["v0_regression"]["forced_edges"]} == {
        ("SHELL_PI_OVER_4", "BRICKWORK_AB"),
        ("SHELL_PI_OVER_4", "FLUX_HOLONOMY_LOCK"),
        ("PHASE_DENSITY_QUOTIENT", "CHANNEL_DZ_RX"),
    }
    assert payload["v0_regression"]["shell_quotient_status"] == "COMMUTES_ORDER_FREE"


def test_new_order_findings_and_executable_controls_are_reported() -> None:
    payload = load_json(RESULT_PATH)
    by_pair = {entry["pair_id"]: entry for entry in payload["pairwise_matrix"]}

    sq = by_pair["SHELL_LEAF_CONDITIONING__QUOTIENT_LENS_EQUIVALENCE"]
    assert sq["status"] == "COMMUTES_ORDER_FREE"
    assert sq["survivor_symmetric_difference_count"] == 0

    st = by_pair["SHELL_LEAF_CONDITIONING__TERRAIN_CONDITIONING"]
    assert st["status"] == "DIRECTIONAL_ENABLE"
    assert st["forced_precedence"] == ["SHELL_LEAF_CONDITIONING", "TERRAIN_CONDITIONING"]

    qo = by_pair["QUOTIENT_LENS_EQUIVALENCE__OPERATOR_RESIDENCY_PRECEDENCE"]
    assert qo["status"] == "DIRECTIONAL_ENABLE"
    assert qo["forced_precedence"] == ["QUOTIENT_LENS_EQUIVALENCE", "OPERATOR_RESIDENCY_PRECEDENCE"]

    controls = payload["controls"]
    assert controls
    assert all(control["executed"] is True for control in controls.values())
    assert all(control["passed"] is True for control in controls.values())
    assert controls["depth_ladder_cross_rung_embedding"]["result"]["alive"] is True
    assert controls["stage_region_operator_residency_blocked_no_realization"]["result"]["mortality_class"] == "blocked_no_realization"


def test_substrate_helper_accepts_positive_and_rejects_lineage_free_negative() -> None:
    positive = subprocess.run(
        [str(PYTHON), "scripts/gcm_substrate_check.py", str(RESULT_PATH)],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert positive.returncode == 0, positive.stdout + positive.stderr
    assert json.loads(positive.stdout)["ok"] is True

    negative_path = SIM_DIR / "results" / "gcm_ratchet_order_matrix_v1_lineage_free_negative.json"
    negative = subprocess.run(
        [str(PYTHON), "scripts/gcm_substrate_check.py", str(negative_path)],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert negative.returncode != 0
    assert json.loads(negative.stdout)["ok"] is False
