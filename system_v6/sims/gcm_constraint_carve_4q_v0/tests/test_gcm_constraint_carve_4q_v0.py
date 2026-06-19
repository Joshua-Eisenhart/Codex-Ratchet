from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_constraint_carve_4q_v0"
RESULT = SIM_DIR / "results" / f"{SIM_ID}_results.json"
VALIDATOR_RESULT = SIM_DIR / "results" / f"{SIM_ID}_validator_results.json"
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


def run_relative(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [SIM_PY, str(path.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def test_build_card_declares_4q_climb_contract() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for required in (
        SIM_ID,
        "layers 1-2 (+17 tensor) | carve | 4Q",
        "consume existing 4Q feedstock",
        "geo_s1_four_qubit_support_exact_v0",
        "stage_lifted_spinor_shell_n4_v0",
        "terrain_spinor_flux_nest_n4_v0",
        "gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5",
        "every candidate's `rho_ABCD`",
        "full C1/C2/C3 matrix",
        "7 bipartitions",
        "GHZ4",
        "W4",
        "cluster",
        "G.2a",
        "scratch_diagnostic",
        "NO git add/commit",
    ):
        assert required in text


def test_packet_consumes_feedstock_and_artifacts_every_candidate_state() -> None:
    common = load_common()
    packet = common.build_packet(write=False)

    assert packet["schema"] == "gcm_constraint_carve_4q_v0_result_v1"
    assert packet["classification"] == "scratch_diagnostic"
    assert packet["promotion_allowed"] is False
    assert packet["formal_admission_allowed"] is False
    assert packet["coordinates"] == {
        "layers": "1-2 (+17 tensor)",
        "operation": "carve",
        "qubit_depth": "4Q",
    }
    assert packet["candidate_space"]["candidate_count"] == 555
    assert packet["candidate_space"]["product_embedding_from_3q_count"] == 545
    assert packet["candidate_space"]["anchor_count"] == 10
    assert packet["survivor_count"] == 546
    assert packet["quotient"]["class_count"] == 9

    consumed = packet["consumed_4q_feedstock"]
    assert consumed["geo_s1_four_qubit_support_exact_v0"]["pin_sha256"] == "acd40027098ca7074723cbb63c21dc9598637363e0a821372830f71b5a6f42ab"
    assert consumed["stage_lifted_spinor_shell_n4_v0"]["pin_sha256"] == "6d5fb046d0ca2813e22b02fa9d9ae2e669311ae52f9ea3853486b0834f13eaa4"
    assert consumed["terrain_spinor_flux_nest_n4_v0"]["pin_sha256"] == "939b812785cd98ae25bc977345f38f4298a62643215d3cc2c5732c0a2c721acc"
    assert consumed["mode"] == "consume_existing_feedstock_never_rebuild"

    state_artifacts = packet["state_artifacts"]
    states = state_artifacts["states_by_content_id"]
    index = state_artifacts["candidate_state_index"]
    matrix = packet["constraint_matrix"]
    assert len(index) == 555
    assert len(matrix) == 555
    assert len(packet["kill_ledger"]) == 555
    assert len(state_artifacts["survivor_states"]) == 546
    for row in index:
        content_id = row["rho_ABCD_content_id"]
        assert content_id in states
        assert states[content_id]["matrix_shape"] == [16, 16]
        assert "rho_ABCD" in states[content_id]
    for row in matrix:
        assert set(row["constraints"]) == {"C1", "C2", "C3"}
        assert all(isinstance(row["constraints"][key]["pass"], bool) for key in ("C1", "C2", "C3"))
        assert row["rho_ABCD_content_id"] in states
        assert "all_failed_constraints" in row
        assert row["first_failed_constraint_display_only"] == (row["all_failed_constraints"][0] if row["all_failed_constraints"] else None)


def test_ghz4_w4_cluster_rows_are_full_matrix_findings() -> None:
    common = load_common()
    packet = common.build_packet(write=False)
    finding = packet["ghz4_w4_cluster_admissibility_matrix"]

    assert finding["source"] == "full_constraint_matrix"
    assert finding["rows"]["GHZ4"]["pass_fail"] == {"C1": True, "C2": False, "C3": False}
    assert finding["rows"]["W4"]["pass_fail"] == {"C1": True, "C2": True, "C3": False}
    assert finding["rows"]["cluster_linear_4"]["pass_fail"] == {"C1": True, "C2": False, "C3": False}
    assert finding["rows"]["W4"]["failed_constraints"] == ["C3"]


def test_cross_rung_cut_lattice_and_narrowed_4party_ckw() -> None:
    common = load_common()
    packet = common.build_packet(write=False)

    cross = packet["cross_rung_rows"]
    assert cross["three_q_to_4q_product_embedding"]["input_3q_survivor_count"] == 545
    assert cross["three_q_to_4q_product_embedding"]["lifted_4q_survivor_count"] == 545
    assert cross["three_q_to_4q_product_embedding"]["all_3q_survivors_have_one_4q_lift"] is True
    assert cross["partial_trace_D_vs_3q_survivors"]["Tr_D_reproduces_3q_state_count"] == 545
    assert cross["partial_trace_D_vs_3q_survivors"]["max_abs_delta_TrD_vs_3q_rho"] == 0.0

    assert packet["cut_lattice"]["bipartitions"] == [
        "q0|q123",
        "q1|q023",
        "q2|q013",
        "q3|q012",
        "q01|q23",
        "q02|q13",
        "q03|q12",
    ]
    assert packet["cut_lattice"]["count"] == 7

    ckw = packet["four_party_ckw_monogamy_narrowed"]
    assert ckw["computed_from_stored_rho_ABCD"] is True
    assert ckw["generalization"] == "Osborne-Verstraete N-qubit CKW focus-qubit inequality"
    assert ckw["residual_4_tangle_claimed"] is False
    assert ckw["pure_survivor_count_checked"] >= 2
    anchor = next(row for row in ckw["rows"] if row["state_id"] == "locally_rotated_generalized_GHZ4_anchor")
    assert set(anchor["focus_qubits"]) == {"q0", "q1", "q2", "q3"}
    assert all(focus["satisfies_focus_ckw"] for focus in anchor["focus_qubits"].values())


def test_controls_negatives_script_and_validator() -> None:
    common = load_common()
    packet = common.build_packet(write=False)

    assert packet["terrain_blindness_guard"]["clean"] is True
    assert packet["controls"]["source_recompute_injection_red"]["red"] is True
    assert packet["controls"]["source_recompute_injection_red"]["error_codes"]
    assert packet["controls"]["empty_C"]["survivor_count"] == 555
    assert packet["controls"]["cliff_overconstrained"]["survivor_count"] == 0
    assert all(row["bite"] for row in packet["controls"]["erasure_bite"])
    assert packet["controls"]["probe_scramble"]["quotient_moved"] is True
    assert packet["controls"]["regressions"]["one_q"]["object_id_match"] is True
    assert packet["controls"]["regressions"]["two_q"]["object_id_match"] is True
    assert packet["controls"]["regressions"]["three_q"]["object_id_match"] is True
    assert packet["substrate_checks"]["one_q_default_registry"]["ok"] is True
    assert packet["substrate_checks"]["two_q_registry"]["ok"] is True
    assert packet["substrate_checks"]["three_q_registry"]["ok"] is True
    for rung in ("1Q", "2Q", "3Q"):
        assert packet["substrate_negatives"][rung]["lineage_free"]["ok"] is False
        assert packet["substrate_negatives"][rung]["lineage_free"]["error_codes"]

    run = run_relative(SIM_DIR / f"{SIM_ID}.py")
    assert run.returncode == 0, run.stdout + run.stderr
    assert RESULT.is_file()

    for lane in ("jax", "pytorch"):
        lane_run = run_relative(SIM_DIR / f"{SIM_ID}_{lane}.py")
        assert lane_run.returncode == 0, lane_run.stdout + lane_run.stderr

    julia_env = {**os.environ, "JULIA_LOAD_PATH": "@:@stdlib"}
    julia = subprocess.run(
        [
            "/opt/homebrew/bin/julia",
            "--startup-file=no",
            f"--project={ROOT / 'system_v5/julia_carrier'}",
            str((SIM_DIR / f"{SIM_ID}_julia.jl").relative_to(ROOT)),
        ],
        cwd=ROOT,
        env=julia_env,
        text=True,
        capture_output=True,
    )
    assert julia.returncode == 0, julia.stdout + julia.stderr

    spec = run_relative(SIM_DIR / "write_envelope_spec.py")
    assert spec.returncode == 0, spec.stdout + spec.stderr
    envelope = run_relative(SIM_DIR / f"{SIM_ID}_envelope.py")
    assert envelope.returncode == 0, envelope.stdout + envelope.stderr

    validator = run_relative(SIM_DIR / f"validate_{SIM_ID}.py")
    assert validator.returncode == 0, validator.stdout + validator.stderr
    payload = json.loads(VALIDATOR_RESULT.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["errors"] == []
