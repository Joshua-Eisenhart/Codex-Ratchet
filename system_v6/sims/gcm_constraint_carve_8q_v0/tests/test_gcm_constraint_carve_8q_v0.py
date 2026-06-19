from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_constraint_carve_8q_v0"
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


def test_build_card_declares_lean_8q_scale_wall_contract() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for required in (
        SIM_ID,
        "layers 1-2 (+17) | carve | 8Q",
        "SCALE-WALL",
        "LEAN",
        "hash per candidate rho",
        "NO every-candidate 256x256 rho blob",
        "GHZ8",
        "W8",
        "cluster_linear_8",
        "stage_lifted_spinor_shell_n8_v0",
        "Cl(16)",
        "127 bipartitions",
        "G.2a",
        "scratch_diagnostic",
        "NO git add/commit",
    ):
        assert required in text


def test_lean_packet_uses_hashes_not_full_rho_blob_for_all_candidates() -> None:
    common = load_common()
    packet, sample = common.build_packet(write=False)

    assert packet["schema"] == "gcm_constraint_carve_8q_v0_result_v1"
    assert packet["classification"] == "scratch_diagnostic"
    assert packet["promotion_allowed"] is False
    assert packet["formal_admission_allowed"] is False
    assert packet["coordinates"] == {
        "layers": "1-2 (+17)",
        "operation": "carve",
        "qubit_depth": "8Q",
    }
    assert packet["scale_wall_fix"]["main_packet_stores_every_candidate_full_rho"] is False
    assert packet["candidate_space"]["candidate_count"] == 559
    assert packet["candidate_space"]["product_embedding_from_7q_count"] == 549
    assert packet["candidate_space"]["anchor_count"] == 10
    assert len(packet["candidate_fingerprints"]) == 559
    assert len(packet["constraint_matrix"]) == 559
    assert len(packet["kill_ledger"]) == 559
    assert "state_artifacts" not in packet
    assert "states_by_content_id" not in json.dumps(packet)

    for row in packet["candidate_fingerprints"]:
        assert row["rho_ABCDEFGH_content_sha256"]
        assert row["rho_ABCDEFGH_content_id"].startswith("rhoabcdefgh_")
        assert "rho_ABCDEFGH" not in row
    for row in packet["constraint_matrix"]:
        assert set(row["constraints"]) == {"C1", "C2", "C3"}
        assert all(isinstance(row["constraints"][key]["pass"], bool) for key in ("C1", "C2", "C3"))
        assert row["rho_ABCDEFGH_content_id"].startswith("rhoabcdefgh_")

    assert sample["sample_kind"] == "bounded_full_rho_spotcheck_sample"
    assert sample["sample_count"] <= 13
    labels = {row["candidate_label"] for row in sample["sample_matrices"]}
    assert {"GHZ8", "W8", "cluster_linear_8"}.issubset(labels)
    assert sum(1 for row in sample["sample_matrices"] if row["sample_reason"] == "survivor_spotcheck") >= 5
    assert sum(1 for row in sample["sample_matrices"] if row["sample_reason"] == "kill_spotcheck") >= 5
    for row in sample["sample_matrices"]:
        assert len(row["rho_ABCDEFGH"]) == 256
        assert len(row["rho_ABCDEFGH"][0]) == 256
        assert row["rho_ABCDEFGH_content_id"] in {fp["rho_ABCDEFGH_content_id"] for fp in packet["candidate_fingerprints"]}


def test_feedstock_counts_cross_rung_cuts_monogamy_and_controls() -> None:
    common = load_common()
    packet, sample = common.build_packet(write=False)

    consumed = packet["consumed_8q_feedstock"]
    assert consumed["mode"] == "consume_existing_8q_feedstock_by_hash_never_rebuild"
    assert consumed["stage_lifted_spinor_shell_n8_v0"]["pin_sha256"] == "6330ff1ce5b81363666b35caafee6a451f825ebab8fef908d375635bf71b09b2"
    assert consumed["geo_s1_scaling_stress_678q_exact_v0"]["pin_sha256"] == "e4da6f5578731c0017ca6140646e893f84b296db78837413d88f0012f86721e8"
    assert consumed["geo_s1_scaling_stress_678q_exact_v0"]["clifford_floor"] == "Cl(16)"

    assert packet["survivor_count"] == 550
    assert packet["m_c_8q"]["survivor_count"] == 550
    assert packet["quotient"]["class_count"] == 9
    assert packet["cross_rung_rows"]["seven_q_to_8q_product_embedding"]["input_7q_survivor_count"] == 549
    assert packet["cross_rung_rows"]["seven_q_to_8q_product_embedding"]["lifted_8q_survivor_count"] == 549
    assert packet["cross_rung_rows"]["partial_trace_H_vs_7q_survivors"]["Tr_H_reproduces_7q_state_count"] == 549
    assert packet["cross_rung_rows"]["partial_trace_H_vs_7q_survivors"]["max_abs_delta_TrH_vs_7q_rho"] == 0.0
    assert packet["cross_rung_rows"]["embedding_via_hashes"] is True

    assert packet["cut_lattice"]["count"] == 127
    assert packet["cut_lattice"]["per_cut_reduced_matrices_stored"] is False
    assert "not stored" in packet["cut_lattice"]["reduced_matrix_caveat"]
    assert len(packet["cut_lattice"]["bipartitions"]) == 127
    assert packet["eight_party_ckw_monogamy_narrowed"]["residual_8_tangle_claimed"] is False
    assert packet["eight_party_ckw_monogamy_narrowed"]["higher_party_residual_allocation_claimed"] is False
    assert packet["eight_party_ckw_monogamy_narrowed"]["pure_sample_count_checked"] >= 2

    assert packet["controls"]["empty_C"]["survivor_count"] == 559
    assert packet["controls"]["cliff_overconstrained"]["survivor_count"] == 0
    assert all(row["bite"] for row in packet["controls"]["erasure_bite"])
    assert packet["controls"]["source_recompute_injection_red"]["red"] is True
    assert packet["controls"]["regressions"]["six_q"]["survivor_count"] == 548
    for rung in ("1Q", "2Q", "3Q", "4Q", "5Q", "6Q", "7Q"):
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
    assert payload["dir_size_bytes"] < 50_000_000
    assert payload["oversize_files_over_50mb"] == []

    assert RESULT.stat().st_size < 5_000_000
    assert SAMPLE.stat().st_size < 15_000_000
