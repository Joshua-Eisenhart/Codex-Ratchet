from __future__ import annotations

import json
import pathlib
import subprocess


CB = pathlib.Path(__file__).resolve().parents[1]


def test_status_ledger_is_a_bound_read_only_row_level_consumer(
    tmp_path: pathlib.Path,
) -> None:
    output = tmp_path / "ledger.json"
    completed = subprocess.run(
        [
            str(CB / ".venv/bin/python"),
            "-I",
            str(CB / "scripts/cb_light_tool_status_ledger.py"),
            "--output",
            str(output),
        ],
        cwd=CB,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    body = json.loads(output.read_text(encoding="utf-8"))
    assert body["schema"] == "constraintbox.cb-light-tool-status-ledger.v1"
    assert body["counts"] == {
        "proposed_light_tools": 91,
        "preinstall_excluded_candidates": 15,
        "runtime_installed_exact": 91,
        "clean_installed_exact": 91,
        "operation_admit": 87,
        "operation_hold": 4,
        "selected_for_work": 86,
        "held_for_missing_evidence": 5,
        "owner_approved_adoptions": 0,
        "portable_adoptions": 0,
        "cb_heavy_authorizations": 0,
    }
    assert len(body["tools"]) == 91
    assert len(body["preinstall_excluded_candidates"]) == 15
    held = {
        row["normalized_name"]: row["lifecycle"]["current_work_selection"]
        for row in body["tools"]
        if row["lifecycle"]["current_work_selection"]["disposition"]
        != "SELECTED_FOR_WORK"
    }
    assert set(held) == {
        "annotated-types",
        "ecdsa",
        "platformdirs",
        "satispy",
        "typing-extensions",
    }
    assert body["controller_infrastructure"]["distributions"] == [
        "pip",
        "constraintbox",
    ]
