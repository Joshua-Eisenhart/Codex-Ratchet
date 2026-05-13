from __future__ import annotations

import importlib.util
import json
import subprocess
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


def test_direct_sim_semantic_guard_rejects_claim_layer_basename(tmp_path: Path) -> None:
    guard = _load_module(
        "direct_sim_semantic_guard_under_test",
        SCRIPTS / "direct_sim_semantic_guard.py",
    )
    probes = tmp_path / "probes"
    probes.mkdir()
    (probes / "sim_carnot_axis4_cycle_ordering_bridge.py").write_text(
        "print('must not run')\n",
        encoding="utf-8",
    )

    result = guard.main(
        [
            "--name",
            "sim_carnot_axis4_cycle_ordering_bridge",
            "--probes-dir",
            str(probes),
        ]
    )

    assert result == 1


def test_direct_sim_semantic_guard_rejects_axis3_basename(tmp_path: Path) -> None:
    guard = _load_module(
        "direct_sim_semantic_guard_axis3_under_test",
        SCRIPTS / "direct_sim_semantic_guard.py",
    )
    probes = tmp_path / "probes"
    probes.mkdir()
    (probes / "sim_axis3_inner_outer_loop_geometry.py").write_text(
        "print('must not run')\n",
        encoding="utf-8",
    )

    result = guard.main(
        [
            "--name",
            "sim_axis3_inner_outer_loop_geometry",
            "--probes-dir",
            str(probes),
        ]
    )

    assert result == 1


def test_direct_sim_semantic_guard_rejects_ax4_shorthand_basename(tmp_path: Path) -> None:
    guard = _load_module(
        "direct_sim_semantic_guard_ax4_under_test",
        SCRIPTS / "direct_sim_semantic_guard.py",
    )
    probes = tmp_path / "probes"
    probes.mkdir()
    (probes / "sim_ax4_loop_ordering_probe.py").write_text(
        "print('must not run')\n",
        encoding="utf-8",
    )

    result = guard.main(
        [
            "--name",
            "sim_ax4_loop_ordering_probe",
            "--probes-dir",
            str(probes),
        ]
    )

    assert result == 1


def test_direct_sim_semantic_guard_rejects_axes_plural_basename(tmp_path: Path) -> None:
    guard = _load_module(
        "direct_sim_semantic_guard_axes_under_test",
        SCRIPTS / "direct_sim_semantic_guard.py",
    )
    probes = tmp_path / "probes"
    probes.mkdir()
    (probes / "sim_both_engines_axes_0_to_7_full_geometry.py").write_text(
        "print('must not run')\n",
        encoding="utf-8",
    )

    result = guard.main(
        [
            "--name",
            "sim_both_engines_axes_0_to_7_full_geometry",
            "--probes-dir",
            str(probes),
        ]
    )

    assert result == 1


def test_direct_sim_semantic_guard_rejects_type_sheet_as_sim_label(tmp_path: Path) -> None:
    guard = _load_module(
        "direct_sim_semantic_guard_type_sheet_under_test",
        SCRIPTS / "direct_sim_semantic_guard.py",
    )
    probes = tmp_path / "probes"
    probes.mkdir()
    (probes / "sim_type1_type2_hopf_loop_comparison.py").write_text(
        "print('must not run')\n",
        encoding="utf-8",
    )

    result = guard.main(
        [
            "--name",
            "sim_type1_type2_hopf_loop_comparison",
            "--probes-dir",
            str(probes),
        ]
    )

    assert result == 1


def test_direct_sim_semantic_guard_accepts_literal_inner_outer_hopf_basename(tmp_path: Path) -> None:
    guard = _load_module(
        "direct_sim_semantic_guard_inner_outer_under_test",
        SCRIPTS / "direct_sim_semantic_guard.py",
    )
    probes = tmp_path / "probes"
    probes.mkdir()
    (probes / "sim_hopf_inner_outer_loop_density_readout.py").write_text(
        "print('fixture')\n",
        encoding="utf-8",
    )

    result = guard.main(
        [
            "--name",
            "sim_hopf_inner_outer_loop_density_readout",
            "--probes-dir",
            str(probes),
        ]
    )

    assert result == 0


def test_direct_sim_semantic_guard_rejects_flux_to_pauli_shortcut_basename(tmp_path: Path) -> None:
    guard = _load_module(
        "direct_sim_semantic_guard_flux_to_pauli_under_test",
        SCRIPTS / "direct_sim_semantic_guard.py",
    )
    probes = tmp_path / "probes"
    probes.mkdir()
    (probes / "boundary_flux_to_pauli_admissibility.py").write_text(
        "print('must not run')\n",
        encoding="utf-8",
    )

    result = guard.main(
        [
            "--name",
            "boundary_flux_to_pauli_admissibility",
            "--probes-dir",
            str(probes),
        ]
    )

    assert result == 1


def test_direct_sim_semantic_guard_accepts_geometric_flux_basename(tmp_path: Path) -> None:
    guard = _load_module(
        "direct_sim_semantic_guard_geometric_flux_under_test",
        SCRIPTS / "direct_sim_semantic_guard.py",
    )
    probes = tmp_path / "probes"
    probes.mkdir()
    (probes / "sim_geometric_constraint_flux_orientation_fixture.py").write_text(
        "print('fixture')\n",
        encoding="utf-8",
    )

    result = guard.main(
        [
            "--name",
            "sim_geometric_constraint_flux_orientation_fixture",
            "--probes-dir",
            str(probes),
        ]
    )

    assert result == 0


def test_direct_sim_semantic_guard_accepts_literal_cycle_basename(tmp_path: Path) -> None:
    guard = _load_module(
        "direct_sim_semantic_guard_accept_under_test",
        SCRIPTS / "direct_sim_semantic_guard.py",
    )
    probes = tmp_path / "probes"
    probes.mkdir()
    (probes / "sim_carnot_cycle_direction_work_sign_closure.py").write_text(
        "print('fixture')\n",
        encoding="utf-8",
    )

    result = guard.main(
        [
            "--name",
            "sim_carnot_cycle_direction_work_sign_closure",
            "--probes-dir",
            str(probes),
        ]
    )

    assert result == 0


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


def test_receipt_run_boundary_fields_are_reported_as_facts() -> None:
    receipt_schema = _load_module("receipt_schema_facts_under_test", SCRIPTS / "receipt_schema.py")

    result = receipt_schema.validate_result_payload(
        _canonical_payload(
            claim_ceiling="tool_function_micro_only",
            next_lego_target="minimal arithmetic fixture",
            promotion_condition="requires later admitted lego row",
            blocked_until="downstream queue row declares target and parent receipts",
        ),
        strict_scope=True,
        require_run_boundary=True,
    )

    assert result["ok"] is True
    assert result["facts"]["claim_ceiling"] == "tool_function_micro_only"
    assert result["facts"]["next_lego_target"] == "minimal arithmetic fixture"


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


def test_receipt_used_tool_requires_depth_entry() -> None:
    receipt_schema = _load_module("receipt_schema_depth_under_test", SCRIPTS / "receipt_schema.py")

    result = receipt_schema.validate_result_payload(
        _canonical_payload(
            tool_manifest={
                "z3": {
                    "tried": True,
                    "used": True,
                    "reason": "z3 is used for the fixture witness.",
                },
                "sympy": {
                    "tried": True,
                    "used": True,
                    "reason": "sympy is load-bearing for the fixture check.",
                },
            },
            tool_integration_depth={"sympy": "load_bearing"},
        )
    )

    assert result["ok"] is False
    assert any(
        finding["kind"] == "used_tool_missing_integration_depth" and finding["tool"] == "z3"
        for finding in result["hard_findings"]
    )


def test_receipt_depth_entry_requires_manifest_tool() -> None:
    receipt_schema = _load_module("receipt_schema_manifest_under_test", SCRIPTS / "receipt_schema.py")

    result = receipt_schema.validate_result_payload(
        _canonical_payload(
            tool_integration_depth={"z3": "load_bearing", "sympy": "supportive"},
        )
    )

    assert result["ok"] is False
    assert any(
        finding["kind"] == "depth_tool_missing_manifest" and finding["tool"] == "sympy"
        for finding in result["hard_findings"]
    )


def test_receipt_non_string_tool_keys_are_explicit_not_symmetry_noise() -> None:
    receipt_schema = _load_module("receipt_schema_key_under_test", SCRIPTS / "receipt_schema.py")

    result = receipt_schema.validate_result_payload(
        _canonical_payload(
            tool_manifest={
                1: {
                    "tried": True,
                    "used": True,
                    "reason": "direct Python payload fixture uses a non-string key.",
                },
            },
            tool_integration_depth={1: "load_bearing"},
        )
    )

    assert result["ok"] is False
    kinds = {finding["kind"] for finding in result["hard_findings"]}
    assert "non_string_tool_manifest_key" in kinds
    assert "non_string_tool_integration_depth_key" in kinds
    assert "used_tool_missing_integration_depth" not in kinds
    assert "load_bearing_tool_not_used_in_manifest" not in kinds


def test_receipt_tried_unused_tool_does_not_require_depth_entry() -> None:
    receipt_schema = _load_module("receipt_schema_unused_under_test", SCRIPTS / "receipt_schema.py")

    result = receipt_schema.validate_result_payload(
        _canonical_payload(
            tool_manifest={
                "z3": {
                    "tried": True,
                    "used": True,
                    "reason": "z3 is load-bearing for the fixture.",
                },
                "sympy": {
                    "tried": True,
                    "used": False,
                    "reason": "sympy was checked but not needed for this fixture.",
                },
            },
            tool_integration_depth={"z3": "load_bearing"},
        )
    )

    assert result["ok"] is True


def test_receipt_legacy_decorative_depth_remains_warning() -> None:
    receipt_schema = _load_module("receipt_schema_legacy_under_test", SCRIPTS / "receipt_schema.py")

    result = receipt_schema.validate_result_payload(
        _canonical_payload(
            tool_manifest={
                "z3": {
                    "tried": True,
                    "used": True,
                    "reason": "z3 is load-bearing for the fixture.",
                },
                "sympy": {
                    "tried": True,
                    "used": False,
                    "reason": "sympy is legacy decorative metadata only.",
                },
            },
            tool_integration_depth={"z3": "load_bearing", "sympy": "decorative"},
        )
    )

    assert result["ok"] is True
    assert any(
        finding["kind"] == "invalid_tool_integration_depth"
        and finding["severity"] == "warning"
        and finding["tool"] == "sympy"
        for finding in result["warnings"]
    )


def test_find_admitted_result_accepts_literal_result_name_mismatch(tmp_path: Path) -> None:
    finder = _load_module("find_admitted_result_under_test", SCRIPTS / "find_admitted_result.py")

    probe_dir = tmp_path / "system_v4" / "probes"
    result_dir = probe_dir / "a2_state" / "sim_results"
    result_dir.mkdir(parents=True)
    probe = probe_dir / "sim_cvc5_shells_crosscheck.py"
    probe.write_text('OUT = "cvc5_shells_crosscheck_results.json"\n', encoding="utf-8")
    result_path = result_dir / "cvc5_shells_crosscheck_results.json"
    result_path.write_text(
        json.dumps(
            _canonical_payload(
                claim_ceiling="tool_function_micro_only",
                next_lego_target="none",
                promotion_condition="requires later admitted lego row",
                blocked_until="exact lego target and parent receipts are reconciled",
            )
        ),
        encoding="utf-8",
    )

    report = finder.find_admitted_result(
        root=tmp_path,
        basename="sim_cvc5_shells_crosscheck",
        probe=probe,
        result_root=result_dir,
        run_start=0,
    )

    assert report["all_pass"] is True
    assert report["admitted_result"] == str(result_path)


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


def test_truth_reconcile_rows_are_ledger_only_work_items(tmp_path: Path) -> None:
    reconcile_state = _load_module("reconcile_state_truth_reconcile_under_test", SCRIPTS / "reconcile_state.py")

    row = {
        "queue": "system_v5/ops/queue_tier_a_second_wave.txt",
        "line": 15,
        "status": "LEDGER_DONE",
        "timestamp": "2026-05-02_16:13",
        "basename": "truth_reconcile_hdbscan",
        "result_basename": "truth_reconcile_hdbscan",
        "raw": "# LEDGER_DONE 2026-05-02_16:13 truth_reconcile_hdbscan",
        "packet": None,
    }
    ledger_text = "| **hdbscan** | `sim_capability_hdbscan_isolated.py` | passes local rerun |\n"

    normal = reconcile_state.reconcile_row(
        row,
        root=tmp_path,
        ledger_text=ledger_text,
        strict_scope=True,
        require_run_boundary=True,
        require_executable_receipt=False,
        stage_gate={"ok": True, "active_stage": "lego", "allow_tier_d_launch": False},
    )
    assert normal["ok"] is True
    assert normal["facts"]["ledger_only_tool"] == "hdbscan"
    assert normal["facts"]["receipt_class"] == "ledger_only"

    executable = reconcile_state.reconcile_row(
        row,
        root=tmp_path,
        ledger_text=ledger_text,
        strict_scope=True,
        require_run_boundary=True,
        require_executable_receipt=True,
        stage_gate={"ok": True, "active_stage": "lego", "allow_tier_d_launch": False},
    )
    assert executable["ok"] is False
    assert any(
        finding["kind"] == "ledger_only_not_executable_receipt"
        for finding in executable["hard_findings"]
    )


def test_ledger_done_rows_are_excluded_from_default_selection(tmp_path: Path) -> None:
    reconcile_state = _load_module("reconcile_state_ledger_done_under_test", SCRIPTS / "reconcile_state.py")

    queue = tmp_path / "queue.txt"
    queue.write_text(
        "\n".join(
            [
                "# LEDGER_DONE 2026-05-02_13:22 manifest_repair_deap",
                "# DONE 2026-05-02_13:23 sim_real_micro",
            ]
        ),
        encoding="utf-8",
    )
    parsed = reconcile_state.parse_queue(queue, tmp_path)

    assert [row["status"] for row in parsed] == ["LEDGER_DONE", "DONE"]
    assert not reconcile_state.selected(
        parsed[0],
        set(),
        "2026-05-02",
        include_legacy=False,
    )
    assert reconcile_state.selected(
        parsed[0],
        set(),
        "2026-05-02",
        include_legacy=False,
        include_ledger_done=True,
    )
    assert reconcile_state.selected(parsed[1], set(), "2026-05-02", include_legacy=False)


def test_run_boundary_packet_result_mismatch_is_hard(tmp_path: Path) -> None:
    reconcile_state = _load_module("reconcile_state_mismatch_under_test", SCRIPTS / "reconcile_state.py")
    result_dir = tmp_path / "system_v4" / "probes" / "a2_state" / "sim_results"
    result_dir.mkdir(parents=True)
    result_path = result_dir / "sim_guardrail_fixture_results.json"
    result_path.write_text(
        json.dumps(
            _canonical_payload(
                name="sim_guardrail_fixture",
                claim_ceiling="tool_function_micro_only",
                next_lego_target="different target",
                promotion_condition="requires later admitted lego row",
                blocked_until="downstream queue row declares target and parent receipts",
            )
        ),
        encoding="utf-8",
    )
    row = {
        "queue": "queue.txt",
        "line": 1,
        "status": "DONE",
        "timestamp": "2026-05-02_13:23",
        "basename": "sim_guardrail_fixture",
        "result_basename": "sim_guardrail_fixture",
        "raw": "# DONE 2026-05-02_13:23 sim_guardrail_fixture",
        "packet": {
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
                "claim_ceiling": "tool_function_micro_only",
                "next_lego_target": "minimal arithmetic fixture",
                "promotion_condition": "requires later admitted lego row",
                "blocked_until": "downstream queue row declares target and parent receipts",
            },
        },
    }

    result = reconcile_state.reconcile_row(
        row,
        root=tmp_path,
        ledger_text="sim_guardrail_fixture",
        strict_scope=True,
        require_run_boundary=True,
        require_executable_receipt=True,
        stage_gate={"ok": True, "active_stage": "lego", "allow_tier_d_launch": False},
    )

    assert result["ok"] is False
    assert any(
        finding["kind"] == "run_boundary_packet_result_mismatch"
        and finding["field"] == "next_lego_target"
        for finding in result["hard_findings"]
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


def test_skipped_and_ineligible_rows_are_terminal_failures(tmp_path: Path) -> None:
    reconcile_state = _load_module("reconcile_state_terminal_under_test", SCRIPTS / "reconcile_state.py")

    queue = tmp_path / "queue.txt"
    queue.write_text(
        "\n".join(
            [
                "# SKIPPED 2026-05-02_13:22 missing_probe_fixture (0s)",
                "# INELIGIBLE 2026-05-02_13:23 ineligible_probe_fixture (0s)",
            ]
        ),
        encoding="utf-8",
    )
    parsed = reconcile_state.parse_queue(queue, tmp_path)
    assert [row["status"] for row in parsed] == ["SKIPPED", "INELIGIBLE"]
    assert reconcile_state.selected(parsed[0], set(), "2026-05-02", include_legacy=False)
    assert reconcile_state.selected(parsed[1], set(), "2026-05-02", include_legacy=False)

    for status, kind in (
        ("SKIPPED", "queue_row_skipped"),
        ("INELIGIBLE", "queue_row_ineligible"),
    ):
        row = {
            "queue": "system_v5/ops/queue_tier_a.txt",
            "line": 7,
            "status": status,
            "timestamp": "2026-05-02_13:22",
            "basename": "missing_probe_fixture",
            "result_basename": "missing_probe_fixture",
            "raw": f"# {status} 2026-05-02_13:22 missing_probe_fixture (0s)",
            "packet": None,
        }

        result = reconcile_state.reconcile_row(
            row,
            root=tmp_path,
            ledger_text="",
            strict_scope=True,
            require_run_boundary=False,
            require_executable_receipt=False,
            stage_gate={"ok": True, "active_stage": "lego", "allow_tier_d_launch": False},
        )

        assert result["ok"] is False
        assert any(finding["kind"] == kind for finding in result["hard_findings"])


def test_strict_reconcile_fails_on_empty_selection(tmp_path: Path) -> None:
    queue = tmp_path / "queue.txt"
    queue.write_text("# empty queue\n", encoding="utf-8")
    ledger = tmp_path / "ledger.md"
    ledger.write_text("", encoding="utf-8")
    stage_gate = tmp_path / "stage_gate.json"
    stage_gate.write_text('{"active_stage": "lego", "allow_tier_d_launch": false}', encoding="utf-8")

    command = [
        sys.executable,
        str(SCRIPTS / "reconcile_state.py"),
        "--queue",
        str(queue),
        "--ledger",
        str(ledger),
        "--stage-gate",
        str(stage_gate),
        "--since",
        "2999-01-01",
        "--require-clean",
    ]
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["all_pass"] is False
    assert payload["selection_findings"][0]["kind"] == "strict_reconcile_selected_no_rows"


def test_strict_reconcile_empty_selection_can_be_explicitly_allowed(tmp_path: Path) -> None:
    queue = tmp_path / "queue.txt"
    queue.write_text("# DONE 2026-05-02_13:22 old_contract_row (1s)\n", encoding="utf-8")
    ledger = tmp_path / "ledger.md"
    ledger.write_text("", encoding="utf-8")
    stage_gate = tmp_path / "stage_gate.json"
    stage_gate.write_text('{"active_stage": "lego", "allow_tier_d_launch": false}', encoding="utf-8")

    command = [
        sys.executable,
        str(SCRIPTS / "reconcile_state.py"),
        "--queue",
        str(queue),
        "--ledger",
        str(ledger),
        "--stage-gate",
        str(stage_gate),
        "--since",
        "2999-01-01",
        "--require-clean",
        "--allow-empty",
    ]
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["all_pass"] is True
    assert payload["selected_rows"] == 0
    assert payload["selection_findings"][0]["kind"] == "strict_reconcile_selected_no_rows"
    assert payload["selection_findings"][0]["severity"] == "warning"
    assert payload["selection_findings"][0]["terminal_rows_available"] == 1
