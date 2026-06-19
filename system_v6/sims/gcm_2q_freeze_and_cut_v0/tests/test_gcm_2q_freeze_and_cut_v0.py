from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_2q_freeze_and_cut_v0"
RESULT = SIM_DIR / "results" / f"{SIM_ID}_results.json"
REGISTRY = SIM_DIR / "results" / f"{SIM_ID}_registry.json"
ENVELOPE = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
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


def test_build_card_declares_contract_and_boundaries() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for required in (
        SIM_ID,
        "2Q freeze",
        "qubit A | qubit B",
        "S(A|B)",
        "I(A:B)",
        "I_c(A>B)",
        "negativity",
        "monogamy",
        "lineage-free negative",
        "gcmobj_a40e54e13cec01466c9d675028b3574b",
        "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed",
        "G.2a",
        "scratch_diagnostic",
        "carrier-and-pins-relative",
        "NO git add/commit",
    ):
        assert required in text


def test_packet_builds_2q_registry_cut_and_entropy_families() -> None:
    common = load_common()
    packet = common.build_packet(write=False)
    registry = common.build_2q_registry(
        common.load_json(common.TWO_Q_CARVE_RESULT),
        common.load_json(common.ONE_Q_FREEZE_REGISTRY),
    )

    assert packet["classification"] == "scratch_diagnostic"
    assert packet["promotion_allowed"] is False
    assert packet["formal_admission_allowed"] is False
    assert packet["carrier_and_pins_relative"] is True
    assert packet["three_coordinates"] == {
        "layers": "3-12 entropy availability rung",
        "nesting": "2Q freeze plus first bipartition cut",
        "qubit_depth": "2Q",
    }
    assert packet["cut"]["bipartition"] == "qubit A | qubit B"
    assert registry["counts"]["survivor_count"] == 544
    assert registry["counts"]["quotient_class_count"] == 8
    assert registry["counts"]["candidate_region_count"] == 6
    assert registry["counts"]["product_survivor_count"] == 528
    assert registry["counts"]["entangled_survivor_count"] == 16
    assert registry["gcm_2q_object_id"].startswith("gcm2qobj_")

    rows = packet["entropy_tables"]["survivor_cut_entropy_rows"]
    assert len(rows) == 544
    assert len(packet["entropy_tables"]["class_cut_entropy_rows"]) == 8
    for row in rows[:3]:
        assert row["rho_AB"]
        assert row["rho_A"]
        assert row["rho_B"]
        assert set(row["entropy_values"]) >= {
            "S_rho_A",
            "S_rho_B",
            "S_rho_AB",
            "conditional_S_A_given_B",
            "mutual_I_A_B",
            "coherent_I_c_A_to_B",
            "negativity",
        }


def test_entangled_product_separation_and_controls() -> None:
    common = load_common()
    packet = common.build_packet(write=False)
    rows = packet["entropy_tables"]["survivor_cut_entropy_rows"]
    product = [row for row in rows if row["family"] == "product_grid"]
    entangled = [row for row in rows if row["entangled"]]

    assert len(product) == 528
    assert len(entangled) == 16
    assert all(row["entropy_values"]["negativity"] == 0.0 for row in product)
    assert all(row["entropy_values"]["mutual_I_A_B"] == 0.0 for row in product)
    assert all(row["entropy_values"]["negativity"] > 0.0 for row in entangled)
    assert all(row["entropy_values"]["conditional_S_A_given_B"] < 0.0 for row in entangled)
    assert all(row["entropy_values"]["coherent_I_c_A_to_B"] > 0.0 for row in entangled)

    sep = packet["entangled_vs_product_separation"]["metrics"]
    assert sep["negativity"]["separates"] is True
    assert sep["mutual_I_A_B"]["separates"] is True
    assert sep["coherent_I_c_A_to_B"]["separates_by_sign"] is True
    assert packet["controls"]["product_entanglement_zero"]["all_product_negativity_zero"] is True
    assert packet["controls"]["scrambled_pairing"]["negativity_after_scramble_all_zero"] is True
    assert packet["controls"]["scrambled_pairing"]["conditional_negative_signal_destroyed"] is True


def test_cross_rung_lineage_substrate_and_monogamy_are_honest() -> None:
    common = load_common()
    packet = common.build_packet(write=False)
    lineage = packet["cross_rung_lineage"]

    assert lineage["product_control_embedding_count"] == 16
    assert lineage["product_control_embedding_all_survive"] is True
    assert lineage["partial_trace_A_image_equals_1q_survivor_set"] is True
    assert set(lineage["partial_trace_A_fiber_counts_by_1q_survivor_id"].values()) == {34}
    assert packet["controls"]["one_q_regression"]["partial_trace_A_reproduces_1q_id_degeneracy"] is True
    assert packet["controls"]["one_q_regression"]["upstream_1q_entropy_sweep_zero_degeneracy"] is True
    assert packet["controls"]["substrate_positive_1q"]["ok"] is True
    assert packet["controls"]["substrate_positive_2q"]["ok"] is True
    assert packet["controls"]["substrate_lineage_free_negative_1q"]["ok"] is False
    assert packet["controls"]["substrate_lineage_free_negative_2q"]["ok"] is False
    assert packet["monogamy_row"]["status"] == "OPEN_REQUIRES_3Q_FOR_CKW"
    assert "rho_ABC" in packet["monogamy_row"]["required_3q_next_object"]["need"]


def test_script_writes_results_envelope_and_validator_accepts_them() -> None:
    run = subprocess.run([SIM_PY, str((SIM_DIR / f"{SIM_ID}_common.py").relative_to(ROOT))], cwd=ROOT, text=True, capture_output=True)
    assert run.returncode == 0, run.stdout + run.stderr
    assert RESULT.is_file()
    assert REGISTRY.is_file()

    for script in (f"{SIM_ID}_jax.py", f"{SIM_ID}_pytorch.py"):
        result = subprocess.run([SIM_PY, str((SIM_DIR / script).relative_to(ROOT))], cwd=ROOT, text=True, capture_output=True)
        assert result.returncode == 0, result.stdout + result.stderr

    env = os.environ.copy()
    env["JULIA_LOAD_PATH"] = "@:@stdlib"
    julia = subprocess.run(
        [
            "/opt/homebrew/bin/julia",
            "--startup-file=no",
            f"--project={ROOT / 'system_v5' / 'julia_carrier'}",
            str((SIM_DIR / f"{SIM_ID}_julia.jl").relative_to(ROOT)),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
    )
    assert julia.returncode == 0, julia.stdout + julia.stderr

    envelope_run = subprocess.run([SIM_PY, str((SIM_DIR / "write_envelope_spec.py").relative_to(ROOT))], cwd=ROOT, text=True, capture_output=True)
    assert envelope_run.returncode == 0, envelope_run.stdout + envelope_run.stderr
    assert ENVELOPE.is_file()
    envelope = json.loads(ENVELOPE.read_text(encoding="utf-8"))
    assert envelope["all_pass"] is True

    validator = subprocess.run(
        [SIM_PY, str((SIM_DIR / f"validate_{SIM_ID}.py").relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert validator.returncode == 0, validator.stdout + validator.stderr
