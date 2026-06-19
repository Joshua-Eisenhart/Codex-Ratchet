from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SIM_ID = "gcm_g2_licensing_attach_v0"
RESULT = SIM_DIR / "results" / f"{SIM_ID}_results.json"
ENVELOPE = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"


def load_sim():
    path = SIM_DIR / f"{SIM_ID}.py"
    spec = importlib.util.spec_from_file_location(SIM_ID, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_result() -> dict:
    assert RESULT.is_file(), f"missing result: {RESULT}"
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_build_card_declares_layer_coordinates_and_controls() -> None:
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    assert SIM_ID in text
    assert "layer 22" in text
    assert "integrated" in text
    assert "3Q" in text
    assert "W_A" in text
    assert "e123+e145+e167+e246-e257-e347-e356" in text
    assert "scrambled-phi" in text
    assert "random 7-subspace" in text
    assert "quotient-erasure" in text
    assert "G.2a" in text
    assert "NO git add/commit" in text


def test_payload_declares_pinned_convention_only_g2_licensing() -> None:
    payload = load_result()
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["carrier_and_pins_relative"] is True
    assert payload["layer_declaration"] == {
        "layer": "22 (the G2 compatibility layer)",
        "nesting": "integrated",
        "qubit_depth": "3Q",
    }
    assert payload["licensing"]["natural_W_A_from_owner_sources"] is False
    assert payload["licensing"]["pinned_convention_flagged"] is True
    assert payload["W_A"]["dimension"] == 7
    assert payload["W_A"]["basis_labels"] == ["XII", "ZII", "IXI", "IZI", "IIX", "IIZ", "XXX"]


def test_phi_associator_and_negative_controls_have_teeth() -> None:
    payload = load_result()
    tests = payload["tests"]
    assert tests["phi_preservation"]["preserving_map_count"] >= 2
    assert tests["phi_preservation"]["failing_map_count"] >= 2
    assert tests["phi_preservation"]["scrambled_phi_control"]["red"] is True
    assert tests["cross_product_closure"]["all_basis_pairs_closed_in_W_A"] is True
    assert tests["associator_rows"]["count_matches_feedstock"] is True
    assert tests["associator_rows"]["visibility_on_states"]["visible_nonzero_rows"] > 0
    assert tests["associator_rows"]["density_quotient_erasure"]["all_classes_erase_associator_labels"] is True
    assert payload["controls"]["random_7_subspace"]["pinned_outperforms_random"] is True
    assert payload["controls"]["lineage_free_negative"]["ok"] is False


def test_validator_passes() -> None:
    result = subprocess.run(
        [SIM_PY, str((SIM_DIR / f"validate_{SIM_ID}.py").relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_envelope_binds_result_hash_and_contract() -> None:
    sim = load_sim()
    payload = load_result()
    envelope = json.loads(ENVELOPE.read_text(encoding="utf-8"))
    assert envelope["schema_version"] == "single_packet_sim_envelope_v1"
    assert envelope["schema"] == f"{SIM_ID}_envelope_v1"
    assert envelope["all_pass"] is True
    assert envelope["result_sha256"] == sim.stable_sha256(payload)
    assert envelope["control_summary"]["scrambled_phi_red"] is True
    assert envelope["control_summary"]["random_7_subspace_underperforms"] is True
