from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.portfolio import portfolio, replay, verify_receipt


def payload() -> dict[str, object]:
    return {
        "schema": "constraintbox.strategy-portfolio.v1",
        "operation_id": "cb-strategy-portfolio-cell.v1",
        "target": "strategy-1",
        "operation": "cb-strategy-portfolio-cell.v1",
        "direct": "follow the current path",
        "alternative": "use a different path",
        "reframe": "change the question",
        "back": "revisit a prior state",
        "wildcard": "test an unexpected branch",
        "stop": "stop and preserve options",
    }


def test_positive_portfolio_retains_all_six_branches_without_selection() -> None:
    receipt = portfolio(payload())
    assert receipt["status"] == "PORTED"
    assert set(receipt["strategies"]) == {"direct", "alternative", "reframe", "back", "wildcard", "stop"}
    assert "winner" not in receipt
    assert "selected_strategy" not in receipt
    assert receipt["target_binding"] == {"target": "strategy-1"}
    assert receipt["promotion_allowed"] is False
    assert receipt["writes_performed"] is False
    assert verify_receipt(receipt)


def test_missing_stop_holds() -> None:
    bad = payload()
    bad.pop("stop")
    receipt = portfolio(bad)
    assert receipt["status"] == "HOLD"
    assert receipt["reason"] == "HOLD_PORTFOLIO"
    assert receipt["missing"] == ["stop"]
    assert verify_receipt(receipt)


def test_authority_shaped_and_promotion_requests_refuse() -> None:
    authority = payload()
    authority["winner"] = "direct"
    assert portfolio(authority)["status"] == "REFUSE"
    promotion = payload()
    promotion["promotion_allowed"] = True
    assert portfolio(promotion)["status"] == "REFUSE"


def test_replay_and_tamper_checks() -> None:
    first = portfolio(payload())
    assert replay(copy.deepcopy(payload()), first)["status"] == "REPLAY_MATCH"
    tampered = copy.deepcopy(first)
    tampered["strategies"]["direct"] = "changed"
    assert not verify_receipt(tampered)
    assert replay(payload(), tampered)["reason"] == "REFUSE_RECEIPT_TAMPER"


def test_cancellation_is_no_write(tmp_path: Path) -> None:
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("unchanged", encoding="utf-8")
    cancelled = payload()
    cancelled["cancelled"] = True
    receipt = portfolio(cancelled)
    assert receipt["status"] == "CANCELLED_NO_AUTHORITY"
    assert receipt["cancellation_state"] == "CANCELLED"
    assert receipt["receipt_written"] is False
    assert receipt["writes_performed"] is False
    assert sentinel.read_text(encoding="utf-8") == "unchanged"
    assert verify_receipt(receipt)


def test_collapsed_arms_refuse_but_explicit_distinguishers_survive() -> None:
    collapsed = payload()
    for key in ("direct", "alternative", "reframe", "back", "wildcard", "stop"):
        collapsed[key] = "same proposal"
    assert portfolio(collapsed)["reason"] == "REFUSE_PORTFOLIO_COLLAPSED"
    distinguished = payload()
    for index, key in enumerate(("direct", "alternative", "reframe", "back", "wildcard", "stop")):
        distinguished[key] = {"proposal": "same proposal", "distinguisher": f"arm-{index}"}
    assert portfolio(distinguished)["status"] == "PORTED"


def test_unknown_case_variant_bounds_and_embedded_receipt_attacks() -> None:
    for key in ("Schema", "schema_version", "unknown"):
        bad = payload()
        bad[key] = 1
        assert portfolio(bad)["status"] == "REFUSE"
    bad_operation = payload()
    bad_operation["operation"] = "CB-STRATEGY-PORTFOLIO-CELL.V1"
    assert portfolio(bad_operation)["reason"] == "REFUSE_OPERATION_MISMATCH"
    oversized = payload()
    oversized["direct"] = "x" * 9000
    assert portfolio(oversized)["reason"] == "REFUSE_INPUT_BOUNDS"
    receipt = portfolio(payload())
    embedded = payload()
    embedded["receipt"] = copy.deepcopy(receipt)
    assert portfolio(embedded)["status"] == "PORTED"
    tampered = copy.deepcopy(receipt)
    tampered["promotion_allowed"] = True
    embedded["receipt"] = tampered
    assert portfolio(embedded)["reason"] == "REFUSE_RECEIPT_TAMPER"
    alias = payload()
    alias["cancel_requested"] = True
    assert portfolio(alias)["status"] == "REFUSE"


def test_operation_id_is_required_and_exact() -> None:
    missing = payload()
    del missing["operation_id"]
    assert portfolio(missing)["reason"] == "REFUSE_OPERATION_ID_REQUIRED"
    wrong = payload()
    wrong["operation_id"] = "alias"
    assert portfolio(wrong)["reason"] == "REFUSE_OPERATION_MISMATCH"
