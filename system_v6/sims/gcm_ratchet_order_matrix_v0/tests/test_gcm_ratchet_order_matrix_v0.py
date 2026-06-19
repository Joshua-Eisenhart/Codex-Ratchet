from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_DIR = ROOT / "system_v6" / "sims" / "gcm_ratchet_order_matrix_v0"
RESULT_PATH = SIM_DIR / "results" / "gcm_ratchet_order_matrix_v0_results.json"
VALIDATOR_PATH = SIM_DIR / "validate_gcm_ratchet_order_matrix_v0.py"
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
    return load_json(SIM_DIR / "results" / "gcm_ratchet_order_matrix_v0_validator_results.json")


def test_build_card_and_boundary_are_present() -> None:
    build_card = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    assert "gcm_ratchet_order_matrix_v0" in build_card
    assert "blocked_no_frozen_gcm_substrate" in build_card
    assert "G.2a" in build_card
    assert "NO git add/commit" in build_card
    assert (SIM_DIR / "gcm_ratchet_order_matrix_v0_boundary.py").exists()


def test_result_passes_packet_validator_and_boundary() -> None:
    validator = run_validator()
    assert validator["ok"] is True
    assert validator["classification"] == "scratch_diagnostic"
    assert validator["substrate_check"]["ok"] is True
    assert validator["lineage_free_negative"]["ok"] is False
    assert validator["wrong_substrate_negative"]["ok"] is False
    assert validator["boundary"]["ok"] is True


def test_order_matrix_has_typed_alphabet_and_required_controls() -> None:
    payload = load_json(RESULT_PATH)
    steps = payload["step_registry"]
    matrix = payload["pairwise_matrix"]
    controls = payload["controls"]

    assert len(steps) == 5
    assert len(matrix) == len(steps) * len(steps)
    assert {step["step_id"] for step in steps} == {
        "SHELL_PI_OVER_4",
        "PHASE_DENSITY_QUOTIENT",
        "BRICKWORK_AB",
        "CHANNEL_DZ_RX",
        "FLUX_HOLONOMY_LOCK",
    }
    for step in steps:
        assert step["domain"]
        assert step["codomain"]
        assert step["source_lock"]

    required_controls = {
        "label_shuffle",
        "reversed_order",
        "quotient_erasure",
        "missing_layer_failure",
        "wrong_substrate_lineage",
        "local_only_replacement",
        "commuting_pair_zero_control",
        "mortality_replay",
        "depth_ablation",
        "entropy_readout_ablation",
        "lineage_free_negative",
    }
    assert required_controls <= set(controls)
    assert all(controls[name]["passed"] for name in required_controls)


def test_honest_nulls_deaths_and_forced_edges_are_reported() -> None:
    payload = load_json(RESULT_PATH)
    by_pair = {entry["pair_id"]: entry for entry in payload["pairwise_matrix"]}

    sq = by_pair["SHELL_PI_OVER_4__PHASE_DENSITY_QUOTIENT"]
    assert sq["status"] == "COMMUTES_ORDER_FREE"
    assert sq["survivor_symmetric_difference_count"] == 0

    sf = by_pair["SHELL_PI_OVER_4__FLUX_HOLONOMY_LOCK"]
    assert sf["status"] == "DIRECTIONAL_ENABLE"
    assert sf["forced_precedence"] == ["SHELL_PI_OVER_4", "FLUX_HOLONOMY_LOCK"]
    assert sf["mortality"]["missing_object"] == "occupied_T_eta_stratum"

    qb = by_pair["PHASE_DENSITY_QUOTIENT__BRICKWORK_AB"]
    assert qb["status"] == "NOT_COMPARABLE"
    assert qb["mortality"]["mortality_class"] == "both_orders_missing_required_objects"

    edges = {tuple(edge) for edge in payload["measured_order"]["forced_precedence_edges"]}
    assert ("SHELL_PI_OVER_4", "BRICKWORK_AB") in edges
    assert ("SHELL_PI_OVER_4", "FLUX_HOLONOMY_LOCK") in edges
    assert ("PHASE_DENSITY_QUOTIENT", "CHANNEL_DZ_RX") in edges


def test_substrate_helper_accepts_positive_and_rejects_negatives() -> None:
    positive = subprocess.run(
        [str(PYTHON), "scripts/gcm_substrate_check.py", str(RESULT_PATH)],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert positive.returncode == 0, positive.stdout + positive.stderr
    positive_payload = json.loads(positive.stdout)
    assert positive_payload["ok"] is True

    negative_path = SIM_DIR / "results" / "gcm_ratchet_order_matrix_v0_lineage_free_negative.json"
    negative = subprocess.run(
        [str(PYTHON), "scripts/gcm_substrate_check.py", str(negative_path)],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert negative.returncode != 0
    negative_payload = json.loads(negative.stdout)
    assert negative_payload["ok"] is False
    assert any("gcm_object_id mismatch" in error for error in negative_payload["errors"])


def test_boundary_helper_is_importable() -> None:
    spec = importlib.util.spec_from_file_location(
        "gcm_ratchet_order_matrix_v0_boundary",
        SIM_DIR / "gcm_ratchet_order_matrix_v0_boundary.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "boundary_errors")
