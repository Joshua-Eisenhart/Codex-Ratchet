from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_constraint_carve_7q_v1"
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
RESULT = SIM_DIR / "results" / f"{SIM_ID}_results.json"
SAMPLE = SIM_DIR / "results" / f"{SIM_ID}_sample_matrices.json"
VALIDATOR_RESULT = SIM_DIR / "results" / f"{SIM_ID}_validator_results.json"


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


def test_build_card_declares_lean_7q_scale_wall_contract() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for required in (
        SIM_ID,
        "layers 1-2 (+17) | carve | 7Q",
        "SCALE-WALL",
        "LEAN",
        "hash per candidate rho",
        "NO every-candidate 128x128 rho blob",
        "GHZ7",
        "W7",
        "cluster_linear_7",
        "stage_lifted_spinor_shell_n7_v0",
        "Cl(14)",
        "63 bipartitions",
        "G.2a",
        "scratch_diagnostic",
        "NO git add/commit",
    ):
        assert required in text


def test_lean_packet_uses_hashes_not_full_rho_blob_for_all_candidates() -> None:
    common = load_common()
    packet, sample = common.build_packet(write=False)

    assert packet["schema"] == "gcm_constraint_carve_7q_v1_result_v1"
    assert packet["classification"] == "scratch_diagnostic"
    assert packet["promotion_allowed"] is False
    assert packet["formal_admission_allowed"] is False
    assert packet["coordinates"] == {
        "layers": "1-2 (+17)",
        "operation": "carve",
        "qubit_depth": "7Q",
    }
    assert packet["scale_wall_fix"]["main_packet_stores_every_candidate_full_rho"] is False
    assert packet["candidate_space"]["candidate_count"] == 558
    assert packet["candidate_space"]["product_embedding_from_6q_count"] == 548
    assert packet["candidate_space"]["anchor_count"] == 10
    assert len(packet["candidate_fingerprints"]) == 558
    assert len(packet["constraint_matrix"]) == 558
    assert len(packet["kill_ledger"]) == 558
    assert "state_artifacts" not in packet
    assert "states_by_content_id" not in json.dumps(packet)

    for row in packet["candidate_fingerprints"]:
        assert row["rho_ABCDEFG_content_sha256"]
        assert row["rho_ABCDEFG_content_id"].startswith("rhoabcdefg_")
        assert "rho_ABCDEFG" not in row
    for row in packet["constraint_matrix"]:
        assert set(row["constraints"]) == {"C1", "C2", "C3"}
        assert all(isinstance(row["constraints"][key]["pass"], bool) for key in ("C1", "C2", "C3"))
        assert row["rho_ABCDEFG_content_id"].startswith("rhoabcdefg_")

    assert sample["sample_kind"] == "bounded_full_rho_spotcheck_sample"
    assert sample["sample_count"] <= 13
    labels = {row["candidate_label"] for row in sample["sample_matrices"]}
    assert {"GHZ7", "W7", "cluster_linear_7"}.issubset(labels)
    assert sum(1 for row in sample["sample_matrices"] if row["sample_reason"] == "survivor_spotcheck") >= 5
    assert sum(1 for row in sample["sample_matrices"] if row["sample_reason"] == "kill_spotcheck") >= 5
    for row in sample["sample_matrices"]:
        assert len(row["rho_ABCDEFG"]) == 128
        assert len(row["rho_ABCDEFG"][0]) == 128
        assert row["rho_ABCDEFG_content_id"] in {fp["rho_ABCDEFG_content_id"] for fp in packet["candidate_fingerprints"]}


def test_feedstock_counts_cross_rung_cuts_monogamy_and_controls() -> None:
    common = load_common()
    packet, sample = common.build_packet(write=False)

    consumed = packet["consumed_7q_feedstock"]
    assert consumed["mode"] == "consume_existing_7q_feedstock_by_hash_never_rebuild"
    assert consumed["stage_lifted_spinor_shell_n7_v0"]["pin_sha256"] == "8a07108fdeb158bc6b504b71cb59d92a3fa33c124e52ee7e719a28ca5b0e21db"
    assert consumed["geo_s1_scaling_stress_678q_exact_v0"]["pin_sha256"] == "e4da6f5578731c0017ca6140646e893f84b296db78837413d88f0012f86721e8"
    assert consumed["geo_s1_scaling_stress_678q_exact_v0"]["clifford_floor"] == "Cl(14)"

    assert packet["survivor_count"] == 549
    assert packet["m_c_7q"]["survivor_count"] == 549
    assert packet["quotient"]["class_count"] == 9
    assert packet["cross_rung_rows"]["six_q_to_7q_product_embedding"]["input_6q_survivor_count"] == 548
    assert packet["cross_rung_rows"]["six_q_to_7q_product_embedding"]["lifted_7q_survivor_count"] == 548
    assert packet["cross_rung_rows"]["partial_trace_G_vs_6q_survivors"]["Tr_G_reproduces_6q_state_count"] == 548
    assert packet["cross_rung_rows"]["partial_trace_G_vs_6q_survivors"]["max_abs_delta_TrG_vs_6q_rho"] == 0.0
    assert packet["cross_rung_rows"]["embedding_via_hashes"] is True

    assert packet["cut_lattice"]["count"] == 63
    assert packet["cut_lattice"]["per_cut_reduced_matrices_stored"] is False
    assert "not stored" in packet["cut_lattice"]["reduced_matrix_caveat"]
    assert len(packet["cut_lattice"]["bipartitions"]) == 63
    assert packet["seven_party_ckw_monogamy_narrowed"]["residual_7_tangle_claimed"] is False
    assert packet["seven_party_ckw_monogamy_narrowed"]["higher_party_residual_allocation_claimed"] is False
    assert packet["seven_party_ckw_monogamy_narrowed"]["pure_sample_count_checked"] >= 2

    assert packet["controls"]["empty_C"]["survivor_count"] == 558
    assert packet["controls"]["cliff_overconstrained"]["survivor_count"] == 0
    assert all(row["bite"] for row in packet["controls"]["erasure_bite"])
    assert packet["controls"]["source_recompute_injection_red"]["red"] is True
    assert packet["controls"]["regressions"]["six_q"]["survivor_count"] == 548
    for rung in ("1Q", "2Q", "3Q", "4Q", "5Q", "6Q"):
        assert packet["substrate_negatives"][rung]["lineage_free"]["ok"] is False
        assert packet["substrate_negatives"][rung]["lineage_free"]["error_codes"]
    assert sample["spotcheck_recompute"]["all_match"] is True


def test_builder_validator_and_size_wall() -> None:
    build = run_relative(SIM_DIR / f"{SIM_ID}.py")
    assert build.returncode == 0, build.stdout + build.stderr
    assert RESULT.is_file()
    assert SAMPLE.is_file()

    validate = run_relative(SIM_DIR / f"validate_{SIM_ID}.py")
    assert validate.returncode == 0, validate.stdout + validate.stderr
    payload = json.loads(VALIDATOR_RESULT.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["errors"] == []
    assert payload["dir_size_bytes"] < 5_000_000
    assert payload["oversize_files_over_50mb"] == []

    assert RESULT.stat().st_size < 2_500_000
    assert SAMPLE.stat().st_size < 3_500_000
