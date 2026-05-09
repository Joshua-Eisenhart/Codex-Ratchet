from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "wizard_behavior_harness.py"
ADAPTER_PATH = REPO_ROOT / "scripts" / "codex_harness_adapter.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        pytest.fail(f"unable to load {name} module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def source_lift_gate() -> dict:
    return {
        "gate_id": "source_lift_fixture_gate",
        "route_id": "direct_fixture_route",
        "source_bundle_ref": ["fixture-record"],
        "source_slice_used": ["direct lane behavior record"],
        "loaded_salience_surfaces": ["fixture mini-MMM body"],
        "raw_launch_receipt_refs": ["wizard_behavior_harness input record"],
        "raw_completion_receipt_refs": ["wizard_behavior_harness receipt JSON"],
        "claim_tested": "local fixture receipt can carry a source-and-lift gate",
        "claim_scope": "local harness fixture only",
        "execution_evidence": ["generated receipt JSON"],
        "terminal_status": "simulated",
        "not_run_or_simulated_accounting": "no live route completion credit",
        "evidence_boundary": "proves fixture shape only, not live Wizard behavior",
        "lift_probe": "fixture keeps execution evidence separate from salience terms",
        "counter_probe_seed": "strip labels; separation should remain",
        "label_strip_result": "partial_survival",
        "counter_probe_result": "partial_survival",
        "strongest_omitted_falsifier": "gate fields could become decorative metadata",
        "salience_status": {
            "load_axis": "loaded",
            "salience_axis": "lift",
            "counter_probe_axis": "partial_survival",
            "corpus_axis": "named_current",
        },
        "gate_verdict": "harden",
        "expansion_permission": False,
    }


def test_harness_writes_adapter_valid_receipt_and_lane_resolution(tmp_path: Path):
    harness = load_module(SCRIPT_PATH, "wizard_behavior_harness")
    adapter = load_module(ADAPTER_PATH, "codex_harness_adapter_for_wizard")
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    record = {
        "lane": "Direct",
        "output": "The candidate returned a plain behavior probe result.",
        "checked": "captured stdout",
        "concluded": "probe completed",
        "open": "manual interpretation still required",
        "evidence": ["logs/direct.out"],
        "source_and_lift_receipt_gate": source_lift_gate(),
    }

    result = harness.run_harness(candidate, tmp_path / "out", [record])

    assert result["ok"]
    assert result["lane_resolution_path"].endswith("lane_resolution.jsonl")
    assert result["receipts_dir"].endswith("receipts")

    ok, report = adapter.validate(
        lane_resolution_path=Path(result["lane_resolution_path"]),
        receipts_dir=Path(result["receipts_dir"]),
        final_answer_path=None,
        allow_controller_local=False,
        allow_local_receipt=True,
        require_source_and_lift_gate=True,
    )

    assert ok, report["findings"]
    assert report["lanes_seen"] == ["Direct"]

    row = json.loads(Path(result["lane_resolution_path"]).read_text(encoding="utf-8").strip())
    receipt = json.loads((Path(result["receipts_dir"]) / "direct.json").read_text(encoding="utf-8"))
    assert row["status"] == "local_receipt"
    assert row["receipt_path"] == "direct.json"
    assert row["mini_mmm_scope"] == "lane_local"
    assert receipt["lane"] == "Direct"
    assert "plain behavior probe result" in receipt["output_excerpt"]
    assert receipt["source_and_lift_receipt_gate"]["expansion_permission"] is False


def test_strict_source_lift_gate_rejects_receipts_without_gate(tmp_path: Path):
    harness = load_module(SCRIPT_PATH, "wizard_behavior_harness_missing_source_lift")
    adapter = load_module(ADAPTER_PATH, "codex_harness_adapter_missing_source_lift")
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    record = {
        "lane": "Direct",
        "output": "The candidate returned a plain behavior probe result.",
        "checked": "captured stdout",
        "concluded": "probe completed",
        "open": "manual interpretation still required",
        "evidence": ["logs/direct.out"],
    }

    result = harness.run_harness(candidate, tmp_path / "out", [record])
    ok, report = adapter.validate(
        lane_resolution_path=Path(result["lane_resolution_path"]),
        receipts_dir=Path(result["receipts_dir"]),
        final_answer_path=None,
        allow_controller_local=False,
        allow_local_receipt=True,
        require_source_and_lift_gate=True,
    )

    assert not ok
    codes = {finding["code"] for finding in report["findings"]}
    assert "missing_source_and_lift_gate" in codes


def test_harness_cli_accepts_json_string_and_jsonl_file_records(tmp_path: Path):
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    records_file = tmp_path / "records.jsonl"
    records_file.write_text(
        json.dumps(
            {
                "lane": "Systems",
                "status": "blocked",
                "output": "Probe could not run because the fixture was unavailable.",
                "reason": "fixture unavailable",
                "checked": "fixture path",
                "concluded": "blocked before execution",
                "open": "rerun with fixture",
                "evidence": "fixture missing",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    direct_record = json.dumps(
        {
            "lane": "Pushback",
            "output": "The behavior probe challenged the claim.",
            "checked": "stdout",
            "concluded": "challenge recorded",
            "open": "needs adjudication",
            "evidence": "probe stdout",
        }
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--candidate-root",
            str(candidate),
            "--out-dir",
            str(tmp_path / "out"),
            "--lane-record",
            direct_record,
            "--lane-record",
            str(records_file),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    rows = [
        json.loads(line)
        for line in Path(result["lane_resolution_path"]).read_text(encoding="utf-8").splitlines()
    ]
    assert [row["lane"] for row in rows] == ["Pushback", "Systems"]
    assert rows[0]["status"] == "local_receipt"
    assert rows[1]["status"] == "blocked"
    assert rows[1]["blocker_or_defer_reason"] == "fixture unavailable"


def test_harness_preserves_runtime_ceiling_batch_states(tmp_path: Path):
    harness = load_module(SCRIPT_PATH, "wizard_behavior_harness_ceiling")
    adapter = load_module(ADAPTER_PATH, "codex_harness_adapter_ceiling")
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    record = {
        "lane": "Follow-up Scout L1",
        "status": "deferred_by_ceiling",
        "output": "Planned as rolling batch slot after active child-agent ceiling resets.",
        "reason": "active Codex child-agent ceiling reached; queued for rolling reset",
        "checked": "runtime ceiling plan",
        "concluded": "not failed; deferred by concurrency ceiling",
        "open": "spawn after prior batch closes",
        "evidence": "runtime registry ceiling",
        "batch_id": "wave-8-batch-2",
        "batch_index": 2,
        "batch_total": 2,
        "runtime_ceiling": 13,
        "reset_id": "codex-child-reset-1",
        "attempt": 1,
        "planned_not_failed_reason": "rolling reset batch",
    }

    result = harness.run_harness(candidate, tmp_path / "out", [record])
    ok, report = adapter.validate(
        lane_resolution_path=Path(result["lane_resolution_path"]),
        receipts_dir=Path(result["receipts_dir"]),
        final_answer_path=None,
        allow_controller_local=False,
        allow_local_receipt=True,
    )

    assert ok, report["findings"]
    row = json.loads(Path(result["lane_resolution_path"]).read_text(encoding="utf-8").strip())
    receipt = json.loads((Path(result["receipts_dir"]) / "follow_up_scout_l1.json").read_text(encoding="utf-8"))
    assert row["status"] == "deferred_by_ceiling"
    assert row["runtime_ceiling"] == 13
    assert receipt["batch_id"] == "wave-8-batch-2"
