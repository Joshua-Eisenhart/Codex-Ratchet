from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_constraint_carve_6q_v0"
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


def test_build_card_declares_6q_climb_contract() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for required in (
        SIM_ID,
        "layers 1-2 (+17 tensor) | carve | 6Q",
        "consume existing 6Q feedstock",
        "geo_s1_scaling_stress_678q_exact_v0",
        "stage_lifted_spinor_shell_n6_v0",
        "5Q carve survivors",
        "rho_ABCDEF",
        "full C1/C2/C3 matrix",
        "31 bipartitions",
        "GHZ6",
        "W6",
        "cluster_linear_6",
        "W-like",
        "Cl(12)",
        "G.2a",
        "scratch_diagnostic",
        "NO git add/commit",
    ):
        assert required in text


def test_packet_consumes_6q_feedstock_and_artifacts_every_candidate_state() -> None:
    common = load_common()
    packet = common.build_packet(write=False)

    assert packet["schema"] == "gcm_constraint_carve_6q_v0_result_v1"
    assert packet["classification"] == "scratch_diagnostic"
    assert packet["promotion_allowed"] is False
    assert packet["formal_admission_allowed"] is False
    assert packet["coordinates"] == {
        "layers": "1-2 (+17 tensor)",
        "operation": "carve",
        "qubit_depth": "6Q",
    }
    assert packet["candidate_space"]["candidate_count"] == 557
    assert packet["candidate_space"]["product_embedding_from_5q_count"] == 547
    assert packet["candidate_space"]["anchor_count"] == 10
    assert packet["survivor_count"] == 548
    assert packet["quotient"]["class_count"] == 9

    consumed = packet["consumed_6q_feedstock"]
    assert consumed["mode"] == "consume_existing_feedstock_never_rebuild"
    assert consumed["geo_s1_scaling_stress_678q_exact_v0"]["commit"] == "b27d22317"
    assert consumed["geo_s1_scaling_stress_678q_exact_v0"]["pin_sha256"] == "e4da6f5578731c0017ca6140646e893f84b296db78837413d88f0012f86721e8"
    assert consumed["stage_lifted_spinor_shell_n6_v0"]["pin_sha256"] == "52a2f3e9753cfd1c7080ef6e6f3091b131e69198cc5fcac2f27522baae8b2e87"
    assert consumed["five_q_carve_survivors"]["authority_commit"] == "16837555a"
    assert consumed["five_q_carve_survivors"]["source_commit"] == "b8b6e777e"

    state_artifacts = packet["state_artifacts"]
    states = state_artifacts["states_by_content_id"]
    index = state_artifacts["candidate_state_index"]
    matrix = packet["constraint_matrix"]
    assert len(index) == 557
    assert len(matrix) == 557
    assert len(packet["kill_ledger"]) == 557
    assert len(state_artifacts["survivor_states"]) == 548
    for row in index:
        content_id = row["rho_ABCDEF_content_id"]
        assert content_id in states
        assert states[content_id]["matrix_shape"] == [64, 64]
        assert "rho_ABCDEF" in states[content_id]
    for row in matrix:
        assert set(row["constraints"]) == {"C1", "C2", "C3"}
        assert all(isinstance(row["constraints"][key]["pass"], bool) for key in ("C1", "C2", "C3"))
        assert row["rho_ABCDEF_content_id"] in states
        assert "all_failed_constraints" in row
        assert row["first_failed_constraint_display_only"] == (row["all_failed_constraints"][0] if row["all_failed_constraints"] else None)


def test_ghz6_w6_cluster_rows_are_full_matrix_findings() -> None:
    common = load_common()
    packet = common.build_packet(write=False)
    finding = packet["ghz6_w6_cluster_admissibility_matrix"]

    assert finding["source"] == "full_constraint_matrix"
    assert finding["rows"]["GHZ6"]["pass_fail"] == {"C1": True, "C2": False, "C3": False}
    assert finding["rows"]["W6"]["pass_fail"] == {"C1": True, "C2": True, "C3": False}
    assert finding["rows"]["cluster_linear_6"]["pass_fail"] == {"C1": True, "C2": False, "C3": False}
    assert finding["rows"]["W6"]["failed_constraints"] == ["C3"]


def test_cross_rung_cut_lattice_and_narrowed_6party_ckw() -> None:
    common = load_common()
    packet = common.build_packet(write=False)

    cross = packet["cross_rung_rows"]
    assert cross["five_q_to_6q_product_embedding"]["input_5q_survivor_count"] == 547
    assert cross["five_q_to_6q_product_embedding"]["lifted_6q_survivor_count"] == 547
    assert cross["five_q_to_6q_product_embedding"]["all_5q_survivors_have_one_6q_lift"] is True
    assert cross["partial_trace_F_vs_5q_survivors"]["Tr_F_reproduces_5q_state_count"] == 547
    assert cross["partial_trace_F_vs_5q_survivors"]["max_abs_delta_TrF_vs_5q_rho"] == 0.0

    assert packet["cut_lattice"]["count"] == 31
    assert packet["cut_lattice"]["bipartitions"] == [
        "q0|q12345",
        "q1|q02345",
        "q2|q01345",
        "q3|q01245",
        "q4|q01235",
        "q5|q01234",
        "q01|q2345",
        "q02|q1345",
        "q03|q1245",
        "q04|q1235",
        "q05|q1234",
        "q12|q0345",
        "q13|q0245",
        "q14|q0235",
        "q15|q0234",
        "q23|q0145",
        "q24|q0135",
        "q25|q0134",
        "q34|q0125",
        "q35|q0124",
        "q45|q0123",
        "q012|q345",
        "q013|q245",
        "q014|q235",
        "q015|q234",
        "q023|q145",
        "q024|q135",
        "q025|q134",
        "q034|q125",
        "q035|q124",
        "q045|q123",
    ]
    assert packet["cut_lattice"]["per_cut_reduced_matrices_stored"] is False
    assert "not stored" in packet["cut_lattice"]["reduced_matrix_caveat"]

    ckw = packet["six_party_ckw_monogamy_narrowed"]
    assert ckw["computed_from_stored_rho_ABCDEF"] is True
    assert ckw["generalization"] == "Osborne-Verstraete N-qubit CKW focus-qubit inequality"
    assert ckw["residual_6_tangle_claimed"] is False
    assert ckw["higher_party_residual_allocation_claimed"] is False
    assert ckw["pure_survivor_count_checked"] >= 2
    anchor = next(row for row in ckw["rows"] if row["state_id"] == "locally_rotated_generalized_GHZ6_anchor")
    assert set(anchor["focus_qubits"]) == {"q0", "q1", "q2", "q3", "q4", "q5"}
    assert all(focus["satisfies_focus_ckw"] for focus in anchor["focus_qubits"].values())


def test_controls_floor_rows_script_and_validator() -> None:
    common = load_common()
    packet = common.build_packet(write=False)

    assert packet["floor_rows_extended"]["consumed_not_rebuilt"] is True
    assert packet["floor_rows_extended"]["geo_s1_scaling_stress_678q_exact_v0"]["proofs_6"]["max_family_bound"]["pass"] is True
    assert packet["floor_rows_extended"]["geo_s1_scaling_stress_678q_exact_v0"]["receipt_table_6"]["W2_Cl2n_exact_floor"]["jax"] is True
    assert packet["floor_rows_extended"]["stage_lifted_spinor_shell_n6_v0"]["Cl12_anchor"]["pass"] is True
    assert packet["terrain_blindness_guard"]["clean"] is True
    assert packet["controls"]["source_recompute_injection_red"]["red"] is True
    assert packet["controls"]["source_recompute_injection_red"]["error_codes"]
    assert packet["controls"]["empty_C"]["survivor_count"] == 557
    assert packet["controls"]["cliff_overconstrained"]["survivor_count"] == 0
    assert all(row["bite"] for row in packet["controls"]["erasure_bite"])
    assert packet["controls"]["probe_scramble"]["quotient_moved"] is True
    assert packet["controls"]["regressions"]["five_q"]["survivor_count"] == 547
    for rung in ("1Q", "2Q", "3Q", "5Q"):
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
