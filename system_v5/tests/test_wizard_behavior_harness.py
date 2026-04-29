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
