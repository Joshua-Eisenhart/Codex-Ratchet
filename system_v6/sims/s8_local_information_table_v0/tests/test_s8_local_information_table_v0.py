from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest


PACKET = Path(__file__).resolve().parents[1]
ROOT = PACKET.parents[2]
RESULT = PACKET / "results" / "s8_local_information_table_v0_envelope_results.json"
if str(PACKET) not in sys.path:
    sys.path.insert(0, str(PACKET))


def load_common():
    spec = importlib.util.spec_from_file_location(
        "s8_local_information_table_v0_common",
        PACKET / "s8_local_information_table_v0_common.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def load_envelope_generator():
    spec = importlib.util.spec_from_file_location(
        "s8_local_information_table_v0_envelope_under_test",
        PACKET / "s8_local_information_table_v0_envelope.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_build_card_is_present_and_builder_boundary_is_clean() -> None:
    card = (PACKET / "build_card.md").read_text(encoding="utf-8")
    assert "s8_local_information_table_v0" in card
    assert "NO git add/commit" in card
    audit = PACKET / "audit_verdict.md"
    assert audit.is_file()
    audit_header = "\n".join(audit.read_text(encoding="utf-8").splitlines()[:40]).lower()
    assert "independent recomputation" in audit_header


def test_common_computes_exact_s8_qit_rows_and_anchors() -> None:
    common = load_common()
    packet = common.build_packet_payload()
    assert packet["object_quote"] == "three-spinor/Clifford floor: (C^2)^x3 with dimension 8"
    assert packet["classification"] == "scratch_diagnostic"
    assert packet["promotion_allowed"] is False

    rows = packet["local_information_table"]["rows"]
    by_key = {(row["state_id"], row["bipartition_id"]): row for row in rows}
    ghz = by_key[("GHZ", "q0__q1q2")]
    assert ghz["S_A_given_B"]["nats"] == pytest.approx(-math.log(2), abs=1e-12)
    assert ghz["I_A_colon_B"]["nats"] == pytest.approx(2 * math.log(2), abs=1e-12)
    assert ghz["I_c"]["nats"] == pytest.approx(math.log(2), abs=1e-12)
    assert ghz["negativity"] == pytest.approx(0.5, abs=1e-12)

    product = by_key[("product_000", "q0__q1q2")]
    assert product["S_A_given_B"]["nats"] >= -1e-12
    assert product["I_c"]["nats"] <= 1e-12

    anchors = packet["continuity_anchors"]
    assert anchors["nested_ratchet"]["all_match"] is True
    assert anchors["nested_ratchet"]["max_abs_divergence"] <= 1e-12
    assert anchors["dual_stack"]["Phi0_Ic_S_to_M"]["computed"] == pytest.approx(0.4164955306996874, abs=1e-12)


def test_structural_controls_are_real_failure_paths() -> None:
    common = load_common()
    packet = common.build_packet_payload()
    controls = packet["controls"]
    assert controls["premature_evaluation"]["bipartition_missing"]["exception_type"] == "MissingStructure"
    assert controls["premature_evaluation"]["channel_missing"]["exception_type"] == "MissingStructure"
    assert controls["typed_confusion_rejection"]["pass"] is True
    assert controls["erased_channel_Ic_flip"]["coherent_Ic_positive"] is True
    assert controls["erased_channel_Ic_flip"]["erased_Ic_nonpositive"] is True


def test_envelope_generator_uses_only_standard_contract_ownership() -> None:
    generator = load_envelope_generator()
    spec = generator.build_spec()
    assert "engine_contract" not in spec["extra_fields"]
    assert all(lane["reads_peer_result"] is False for lane in spec["lanes"].values())
    assert spec["extra_fields"]["s8_engine_contract_details"] == {
        "mode": "all_three_full_sims",
        "lanes": ["julia", "jax", "pytorch"],
        "reads_peer_result": {"julia": False, "jax": False, "pytorch": False},
    }
    envelope = generator.build_envelope(**spec)
    assert envelope["engine_contract"]["lanes"] == ["jax", "julia", "pytorch"]
    assert envelope["engine_contract"]["omitted_lanes"] == {}


def test_envelope_if_present_has_builder_gate_and_strict_shape() -> None:
    if not RESULT.exists():
        pytest.skip("envelope not built yet")
    env = json.loads(RESULT.read_text(encoding="utf-8"))
    assert env["schema_version"] == "three_engine_sim_result_v1"
    assert env["sim_id"] == "s8_local_information_table_v0"
    assert env["classification"] == "scratch_diagnostic"
    assert env["promotion_allowed"] is False
    assert env["formal_admission_allowed"] is False
    assert env["all_pass"] is True
    assert env["builder_gates"]["no_builder_audit_verdict"] is True
    assert env["no_builder_audit_verdict"] is True
    assert set(env["engines"]) == {"julia", "jax", "pytorch"}
    assert env["engine_contract"]["mode"] == "all_three_full_sims"
    assert env["engine_contract"]["lanes"] == ["jax", "julia", "pytorch"]
    assert env["engine_contract"]["omitted_lanes"] == {}
    assert env["s8_engine_contract_details"] == {
        "mode": "all_three_full_sims",
        "lanes": ["julia", "jax", "pytorch"],
        "reads_peer_result": {"julia": False, "jax": False, "pytorch": False},
    }
    assert env["continuity_anchors"]["nested_ratchet"]["all_match"] is True
    assert env["continuity_anchors"]["dual_stack"]["Phi0_Ic_S_to_M"]["computed"] == pytest.approx(
        0.4164955306996874,
        abs=1e-12,
    )
