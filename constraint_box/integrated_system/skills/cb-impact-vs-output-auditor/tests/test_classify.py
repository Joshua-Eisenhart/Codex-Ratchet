from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.classify import OPERATION, SCHEMA, classify, verify_payload_receipt, verify_receipt


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "classify.py"


def _payload(claim: str = "artifact", evidence: list[str] | None = None) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "operation": OPERATION,
        "target": "claim-1",
        "claim": claim,
        "evidence": [claim] if evidence is None else evidence,
    }


def test_each_exact_class_is_classified_without_promotion() -> None:
    for claim, expected in (
        ("artifact", "artifact_only"),
        ("metric", "metric_only"),
        ("external_condition", "external_condition"),
    ):
        receipt = classify(_payload(claim))
        assert receipt["status"] == "CLASSIFIED"
        assert receipt["class"] == expected
        assert receipt["claim"] == claim
        assert receipt["evidence"] == [claim]
        assert receipt["promotion_allowed"] is False
        assert receipt["audit_only"] is True
        assert receipt["proposal_only"] is True
        assert receipt["writes_performed"] is False
        assert receipt["provider_call_receipt"] is None
        assert verify_receipt(receipt)
        assert verify_receipt(receipt, _payload(claim))


def test_claim_and_evidence_enums_are_nonempty_and_strict() -> None:
    unknown_claim = _payload("unknown")
    assert classify(unknown_claim)["reason"] == "REFUSE_CLAIM_ENUM"
    empty_claim = _payload("")
    assert classify(empty_claim)["reason"] == "REFUSE_CLAIM_ENUM"
    empty_evidence = _payload("artifact", [])
    assert classify(empty_evidence)["reason"] == "REFUSE_EVIDENCE_EMPTY"
    unknown_evidence = _payload("artifact", ["artifact_output"])
    assert classify(unknown_evidence)["reason"] == "REFUSE_EVIDENCE_ENUM"
    duplicate = _payload("artifact", ["artifact", "artifact"])
    assert classify(duplicate)["reason"] == "REFUSE_EVIDENCE_ENUM"


def test_cross_class_evidence_cannot_promote_or_cross_check() -> None:
    artifact_to_metric = _payload("artifact", ["metric"])
    assert classify(artifact_to_metric)["reason"] == "REFUSE_EVIDENCE_CLASS_MISMATCH"
    metric_to_external = _payload("metric", ["external_condition"])
    assert classify(metric_to_external)["reason"] == "REFUSE_EVIDENCE_CLASS_MISMATCH"
    external_without_external = _payload("external_condition", ["metric"])
    assert classify(external_without_external)["reason"] == "REFUSE_OUTPUT_AS_IMPACT"


def test_exact_schema_operation_target_unknown_and_authority_refuse() -> None:
    assert classify([])["reason"] == "REFUSE_MALFORMED_INPUT"
    bad_schema = _payload()
    bad_schema["schema"] = "other.v1"
    assert classify(bad_schema)["reason"] == "REFUSE_SCHEMA_MISMATCH"
    bad_operation = _payload()
    bad_operation["operation"] = "classify_artifact_metric_external"
    assert classify(bad_operation)["reason"] == "REFUSE_OPERATION_MISMATCH"
    alias = _payload()
    alias["operation_id"] = "impact-1"
    assert classify(alias)["reason"] == "REFUSE_UNKNOWN_KEY"
    provider = _payload()
    provider["provider"] = "model"
    assert classify(provider)["reason"] == "REFUSE_UNKNOWN_KEY"
    conflict = _payload()
    conflict["target_id"] = "claim-1"
    assert classify(conflict)["reason"] == "REFUSE_TARGET_CONFLICT"
    authority = _payload()
    authority["promotion_allowed"] = True
    assert classify(authority)["reason"] == "REFUSE_AUTHORITY_SHAPED"


def test_replay_embedded_receipt_current_binding_and_tamper() -> None:
    payload = _payload("metric")
    first = classify(payload)
    assert first == classify(copy.deepcopy(payload))
    assert verify_payload_receipt(payload, first)
    embedded = copy.deepcopy(payload)
    embedded["receipt"] = first
    assert classify(embedded) == first
    changed_target = copy.deepcopy(embedded)
    changed_target["target"] = "claim-2"
    assert classify(changed_target)["reason"] == "REFUSE_RECEIPT_TAMPER"
    changed_claim = copy.deepcopy(embedded)
    changed_claim["claim"] = "artifact"
    assert classify(changed_claim)["reason"] == "REFUSE_RECEIPT_TAMPER"
    tampered = copy.deepcopy(first)
    tampered["claim"] = "external_condition"
    assert not verify_receipt(tampered)
    forged = copy.deepcopy(payload)
    forged["receipt"] = tampered
    assert classify(forged)["reason"] == "REFUSE_RECEIPT_TAMPER"


def test_strict_cancellation_bounds_and_no_write() -> None:
    bad_cancel = _payload()
    bad_cancel["cancelled"] = "false"
    assert classify(bad_cancel)["reason"] == "REFUSE_CANCEL_TYPE"
    deep = _payload()
    value: object = "x"
    for _ in range(12):
        value = [value]
    deep["evidence"] = [value]
    assert classify(deep)["reason"] == "REFUSE_INPUT_BOUNDS"
    cancelled = _payload()
    cancelled["cancelled"] = True
    receipt = classify(cancelled)
    assert receipt["status"] == "CANCELLED_NO_AUTHORITY"
    assert receipt["cancellation_state"] == "CANCELLED"
    assert receipt["writes_performed"] is False


def test_cli_accepts_explicit_json_without_writing(tmp_path: Path) -> None:
    before = sorted(tmp_path.iterdir())
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", json.dumps(_payload("metric"))],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["status"] == "CLASSIFIED"
    assert sorted(tmp_path.iterdir()) == before


def test_cli_rejects_12k_depth_without_traceback() -> None:
    raw = "[" * 12000 + "0" + "]" * 12000
    proc = subprocess.run([sys.executable, str(SCRIPT), "--json", raw], check=False, capture_output=True, text=True)
    assert proc.returncode == 2
    assert "Traceback" not in proc.stderr
    assert json.loads(proc.stdout)["reason"] == "REFUSE_MALFORMED_JSON"
