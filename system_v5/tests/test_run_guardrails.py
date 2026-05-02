from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    inserted = False
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
        inserted = True
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(module_name, None)
        if inserted:
            sys.path.remove(str(path.parent))


def _canonical_payload(**extra):
    payload = {
        "name": "sim_guardrail_fixture",
        "classification": "canonical",
        "all_pass": True,
        "tool_manifest": {
            "z3": {
                "tried": True,
                "used": True,
                "reason": "z3 is load-bearing for this exact guardrail fixture.",
            }
        },
        "tool_integration_depth": {"z3": "load_bearing"},
        "positive": {"fixture_passes": {"passed": True}},
        "negative": {"wrong_fixture_rejected": {"passed": True}},
        "boundary": {"zero_boundary_checked": {"passed": True}},
        "demotion_condition": "Demote if the exact guardrail fixture fails.",
        "out_of_scope": ["no lego promotion", "no bridge claim"],
    }
    payload.update(extra)
    return payload


def test_receipt_run_boundary_fields_are_separate_from_existing_strict_scope() -> None:
    receipt_schema = _load_module("receipt_schema_under_test", SCRIPTS / "receipt_schema.py")

    strict_only = receipt_schema.validate_result_payload(
        _canonical_payload(),
        strict_scope=True,
    )
    assert strict_only["ok"] is True
    assert {item["kind"] for item in strict_only["warnings"]} >= {
        "missing_claim_ceiling",
        "missing_next_lego_target",
        "missing_promotion_condition",
        "missing_blocked_until",
    }

    run_boundary = receipt_schema.validate_result_payload(
        _canonical_payload(),
        strict_scope=True,
        require_run_boundary=True,
    )
    assert run_boundary["ok"] is False
    assert {item["kind"] for item in run_boundary["hard_findings"]} >= {
        "missing_claim_ceiling",
        "missing_next_lego_target",
        "missing_promotion_condition",
        "missing_blocked_until",
    }


def test_receipt_executable_admission_rejects_supporting_and_audit_classes() -> None:
    receipt_schema = _load_module("receipt_schema_exec_under_test", SCRIPTS / "receipt_schema.py")

    result = receipt_schema.validate_result_payload(
        _canonical_payload(classification="audit"),
        require_executable=True,
    )

    assert result["ok"] is False
    assert any(
        finding["kind"] == "non_executable_receipt_classification"
        for finding in result["hard_findings"]
    )


def test_micro_packet_run_boundary_fields_are_required_in_run_boundary_mode(tmp_path: Path) -> None:
    reconcile_state = _load_module("reconcile_state_boundary_under_test", SCRIPTS / "reconcile_state.py")

    packet = {
        "type": "MICRO",
        "line": 1,
        "payload": {
            "tool_target": "z3",
            "function_surface": "SolverFor('QF_LIA').check",
            "micro_claim": "one bounded SAT fixture",
            "lego_target": "minimal arithmetic fixture",
            "function_receipt": "new",
            "prior_function_receipts": [],
            "why_this_lego": "the fixture exposes the solver surface",
            "positive_case": "SAT fixture passes",
            "negative_case": "contradiction fails",
            "boundary_case": "zero boundary checked",
            "demotion_condition": "demote if SAT/UNSAT verdicts are wrong",
            "out_of_scope": ["no lego promotion"],
        },
    }

    _, hard, _ = reconcile_state.reconcile_packet(
        packet,
        root=tmp_path,
        require_run_boundary=True,
        stage_gate={"ok": True, "active_stage": "lego", "allow_tier_d_launch": False},
    )

    assert {item["kind"] for item in hard} >= {"queue_packet_required_field_empty"}
    assert {item["field"] for item in hard if item["kind"] == "queue_packet_required_field_empty"} >= {
        "claim_ceiling",
        "next_lego_target",
        "promotion_condition",
        "blocked_until",
    }


def test_claim_ceiling_blocks_bridge_language_before_coupling_stage(tmp_path: Path) -> None:
    reconcile_state = _load_module("reconcile_state_claim_under_test", SCRIPTS / "reconcile_state.py")

    packet = {
        "type": "MICRO",
        "line": 1,
        "payload": {
            "tool_target": "z3",
            "function_surface": "SolverFor('QF_LIA').check",
            "micro_claim": "proves bridge readiness from one solver fixture",
            "lego_target": "minimal arithmetic fixture",
            "function_receipt": "new",
            "prior_function_receipts": [],
            "why_this_lego": "the fixture exposes the solver surface",
            "positive_case": "SAT fixture passes",
            "negative_case": "contradiction fails",
            "boundary_case": "zero boundary checked",
            "demotion_condition": "demote if SAT/UNSAT verdicts are wrong",
            "out_of_scope": ["no lego promotion"],
            "claim_ceiling": "tool_function_micro_only",
            "next_lego_target": "none",
            "promotion_condition": "requires later lego row",
            "blocked_until": "exact lego target and parent receipts are reconciled",
        },
    }

    _, hard, _ = reconcile_state.reconcile_packet(
        packet,
        root=tmp_path,
        require_run_boundary=True,
        stage_gate={"ok": True, "active_stage": "lego", "allow_tier_d_launch": False},
    )

    assert any(
        finding["kind"] == "claim_ceiling_violation" and finding["claim"] == "bridge"
        for finding in hard
    )


def test_claim_ceiling_allows_negated_bridge_and_incidental_axis_text(tmp_path: Path) -> None:
    reconcile_state = _load_module("reconcile_state_negated_under_test", SCRIPTS / "reconcile_state.py")

    packet = {
        "type": "MICRO",
        "line": 1,
        "payload": {
            "tool_target": "geomstats",
            "function_surface": "SO(3) axis parameter extraction",
            "micro_claim": "one bounded log/exp fixture; no bridge claim is made",
            "lego_target": "minimal rotation fixture",
            "function_receipt": "new",
            "prior_function_receipts": [],
            "why_this_lego": "the fixture exposes branch selection without axis-level promotion",
            "positive_case": "rotation fixture passes",
            "negative_case": "wrong branch rejected",
            "boundary_case": "identity boundary checked",
            "demotion_condition": "demote if branch selection is wrong",
            "out_of_scope": ["no bridge claim", "no axis claim"],
            "claim_ceiling": "tool_function_micro_only",
            "next_lego_target": "none",
            "promotion_condition": "requires later lego row",
            "blocked_until": "exact lego target and parent receipts are reconciled",
        },
    }

    _, hard, _ = reconcile_state.reconcile_packet(
        packet,
        root=tmp_path,
        require_run_boundary=True,
        stage_gate={"ok": True, "active_stage": "lego", "allow_tier_d_launch": False},
    )

    assert not [
        finding
        for finding in hard
        if finding["kind"] in {"claim_ceiling_violation", "claim_language_requires_prior_receipts"}
    ]


def test_ledger_only_rows_can_pass_loopback_but_fail_executable_mode(tmp_path: Path) -> None:
    reconcile_state = _load_module("reconcile_state_ledger_under_test", SCRIPTS / "reconcile_state.py")

    row = {
        "queue": "system_v5/ops/queue_tier_a_second_wave.txt",
        "line": 23,
        "status": "DONE",
        "timestamp": "2026-05-02_13:22",
        "basename": "manifest_repair_deap",
        "result_basename": "manifest_repair_deap",
        "raw": "# DONE 2026-05-02_13:22 manifest_repair_deap",
        "packet": None,
    }
    ledger_text = "| **deap** | `sim_capability_deap_isolated.py` | passes local rerun |\n"

    normal = reconcile_state.reconcile_row(
        row,
        root=tmp_path,
        ledger_text=ledger_text,
        strict_scope=True,
        require_run_boundary=False,
        require_executable_receipt=False,
        stage_gate={"ok": True, "active_stage": "lego", "allow_tier_d_launch": False},
    )
    assert normal["ok"] is True
    assert normal["facts"]["executable_receipt"] is False

    executable = reconcile_state.reconcile_row(
        row,
        root=tmp_path,
        ledger_text=ledger_text,
        strict_scope=True,
        require_run_boundary=False,
        require_executable_receipt=True,
        stage_gate={"ok": True, "active_stage": "lego", "allow_tier_d_launch": False},
    )
    assert executable["ok"] is False
    assert any(
        finding["kind"] == "ledger_only_not_executable_receipt"
        for finding in executable["hard_findings"]
    )


def test_ledger_only_fail_rows_never_reconcile_as_ok(tmp_path: Path) -> None:
    reconcile_state = _load_module("reconcile_state_ledger_fail_under_test", SCRIPTS / "reconcile_state.py")

    row = {
        "queue": "system_v5/ops/queue_tier_a_second_wave.txt",
        "line": 23,
        "status": "FAIL",
        "timestamp": "2026-05-02_13:22",
        "basename": "manifest_repair_deap",
        "result_basename": "manifest_repair_deap",
        "raw": "# FAIL 2026-05-02_13:22 manifest_repair_deap",
        "packet": None,
    }
    ledger_text = "| **deap** | `sim_capability_deap_isolated.py` | passes local rerun |\n"

    result = reconcile_state.reconcile_row(
        row,
        root=tmp_path,
        ledger_text=ledger_text,
        strict_scope=True,
        require_run_boundary=False,
        require_executable_receipt=False,
        stage_gate={"ok": True, "active_stage": "lego", "allow_tier_d_launch": False},
    )

    assert result["ok"] is False
    assert any(finding["kind"] == "queue_row_failed" for finding in result["hard_findings"])
