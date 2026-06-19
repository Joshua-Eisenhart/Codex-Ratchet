import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_v43(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "scripts/wizard_v4_3_object_preservation.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_selftest_loop_passes(tmp_path: Path) -> None:
    out = tmp_path / "selftest.json"
    result = run_v43("selftest", "--out", str(out))

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(out.read_text())
    assert payload["ok"] is True
    assert {case["name"] for case in payload["cases"]} >= {
        "valid_retrocausal_packet",
        "reject_axis0_proxy_promotion",
        "reject_fep_analogy_promotion",
        "reject_underdefined_jk_fuzz",
        "reject_missing_evidence_spine",
        "reject_missing_method_contracts",
        "reject_weak_order_contract",
        "reject_unclear_claude_authority",
    }


def test_valid_example_validates(tmp_path: Path) -> None:
    packet = tmp_path / "packet.json"
    example = run_v43("example", "--out", str(packet))
    assert example.returncode == 0, example.stdout + example.stderr

    result = run_v43("validate", "--input", str(packet))
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert set(payload["checked"]["method_contracts"]) >= {
        "question_is_not_authorization",
        "order_check_separate",
        "baseline_preservation",
        "falsifier_first",
        "feynman_testability",
        "synthesis_refusal",
        "human_offload",
    }
    assert payload["checked"]["claude_pattern_cards"] >= 1


def test_loop_stops_when_selftest_clean(tmp_path: Path) -> None:
    out = tmp_path / "loop.json"
    result = run_v43("loop", "--max-loops", "3", "--out", str(out))

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(out.read_text())
    assert payload["ok"] is True
    assert payload["loops_completed"] == 1
    assert payload["loops"][0]["failed_cases"] == []


def test_proxy_promotion_is_rejected(tmp_path: Path) -> None:
    packet = tmp_path / "packet.json"
    example = run_v43("example", "--out", str(packet))
    assert example.returncode == 0, example.stdout + example.stderr
    payload = json.loads(packet.read_text())
    payload["lateral_mappings"][1]["promotion_allowed"] = True
    packet.write_text(json.dumps(payload), encoding="utf-8")

    result = run_v43("validate", "--input", str(packet))
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert any(error["code"] == "mapping.unpromotable_type_promoted" for error in output["errors"])


def test_retrocausal_packet_must_keep_shell_fields(tmp_path: Path) -> None:
    packet = tmp_path / "packet.json"
    example = run_v43("example", "--out", str(packet))
    assert example.returncode == 0, example.stdout + example.stderr
    payload = json.loads(packet.read_text())
    payload["primary_object_card"]["first_class_fields"] = ["state_t", "entropy", "Axis0"]
    packet.write_text(json.dumps(payload), encoding="utf-8")

    result = run_v43("validate", "--input", str(packet))
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert any(error["code"] == "card.retrocausal_missing_fields" for error in output["errors"])


def test_root_and_extended_constraints_cannot_collapse(tmp_path: Path) -> None:
    packet = tmp_path / "packet.json"
    example = run_v43("example", "--out", str(packet))
    assert example.returncode == 0, example.stdout + example.stderr
    payload = json.loads(packet.read_text())
    payload["constraint_bands"]["extended_constraints"].append("finite carrier/probe/path set")
    packet.write_text(json.dumps(payload), encoding="utf-8")

    result = run_v43("validate", "--input", str(packet))
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert any(error["code"] == "constraint_bands.root_extended_overlap" for error in output["errors"])


def test_evidence_spine_is_required(tmp_path: Path) -> None:
    packet = tmp_path / "packet.json"
    example = run_v43("example", "--out", str(packet))
    assert example.returncode == 0, example.stdout + example.stderr
    payload = json.loads(packet.read_text())
    payload.pop("evidence_spine")
    packet.write_text(json.dumps(payload), encoding="utf-8")

    result = run_v43("validate", "--input", str(packet))
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert any(error["code"] == "evidence_spine.missing" for error in output["errors"])


def test_method_contracts_are_required(tmp_path: Path) -> None:
    packet = tmp_path / "packet.json"
    example = run_v43("example", "--out", str(packet))
    assert example.returncode == 0, example.stdout + example.stderr
    payload = json.loads(packet.read_text())
    payload.pop("method_contracts")
    packet.write_text(json.dumps(payload), encoding="utf-8")

    result = run_v43("validate", "--input", str(packet))
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert any(error["code"] == "method_contracts.missing" for error in output["errors"])


def test_order_contract_must_separate_order_from_content(tmp_path: Path) -> None:
    packet = tmp_path / "packet.json"
    example = run_v43("example", "--out", str(packet))
    assert example.returncode == 0, example.stdout + example.stderr
    payload = json.loads(packet.read_text())
    payload["method_contracts"]["order_check_separate"] = "Check the content."
    packet.write_text(json.dumps(payload), encoding="utf-8")

    result = run_v43("validate", "--input", str(packet))
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert any(error["code"] == "method_contracts.order_check_unclear" for error in output["errors"])


def test_claude_pattern_cards_must_stay_reference_only(tmp_path: Path) -> None:
    packet = tmp_path / "packet.json"
    example = run_v43("example", "--out", str(packet))
    assert example.returncode == 0, example.stdout + example.stderr
    payload = json.loads(packet.read_text())
    payload["evidence_spine"]["claude_pattern_cards"][0]["authority_reason"] = (
        "Claude skill is canonical behavior law."
    )
    packet.write_text(json.dumps(payload), encoding="utf-8")

    result = run_v43("validate", "--input", str(packet))
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert any(error["code"] == "evidence_spine.claude_card_authority_unclear" for error in output["errors"])


def test_gate_v42_preflight_receipt_passes_without_claiming_council_run(tmp_path: Path) -> None:
    packet = tmp_path / "packet.json"
    receipt = tmp_path / "gate.json"
    example = run_v43("example", "--out", str(packet))
    assert example.returncode == 0, example.stdout + example.stderr

    result = run_v43(
        "gate-v42",
        "--input",
        str(packet),
        "--task",
        "audit Wizard v4.3 object preservation before a v4.2 council run",
        "--out",
        str(receipt),
        "--out-dir",
        str(tmp_path / "runs"),
        "--no-capacity-preflight",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(receipt.read_text())
    assert payload["ok"] is True
    assert payload["schema_version"] == "wizard_v4_3_gated_v4_2_receipt_v1"
    assert payload["v4_3_validation"]["ok"] is True
    assert payload["v4_2_boot_surface"]["ok"] is True
    assert payload["v4_2_conformance"]["ok"] is True
    assert payload["v4_2_launch"]["status"] == "not_requested"
    assert "no council completion claim" in payload["claim_ceiling"]


def test_gate_v42_blocks_launch_when_object_card_fails(tmp_path: Path) -> None:
    packet = tmp_path / "packet.json"
    example = run_v43("example", "--out", str(packet))
    assert example.returncode == 0, example.stdout + example.stderr
    payload = json.loads(packet.read_text())
    payload["lateral_mappings"][1]["promotion_allowed"] = True
    packet.write_text(json.dumps(payload), encoding="utf-8")

    result = run_v43(
        "gate-v42",
        "--input",
        str(packet),
        "--task",
        "this should not launch v4.2 because the object card is invalid",
        "--out-dir",
        str(tmp_path / "runs"),
        "--launch-v42",
        "--dry-run-v42",
        "--no-capacity-preflight",
    )

    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["v4_3_validation"]["ok"] is False
    assert output["v4_2_launch"]["status"] == "blocked"
    assert output["v4_2_launch"]["blocked_by"]["v4_3_validation"] is True
