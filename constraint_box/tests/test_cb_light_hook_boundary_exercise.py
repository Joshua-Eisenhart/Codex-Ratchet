from __future__ import annotations

import json
import pathlib
import subprocess


CB = pathlib.Path(__file__).resolve().parents[1]


def test_root_and_legacy_hooks_enforce_four_boundary_cases(
    tmp_path: pathlib.Path,
) -> None:
    db_path = tmp_path / "hook-boundary.sqlite"
    output = tmp_path / "hook-boundary.json"
    completed = subprocess.run(
        [
            str(CB / ".venv/bin/python"),
            "-I",
            str(CB / "scripts/exercise_cb_light_hook_boundaries.py"),
            "--db",
            str(db_path),
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
    assert body["schema"] == "constraintbox.cb-light-hook-boundary-exercise.v1"
    assert body["all_passed"] is True
    assert body["counts"] == {"cases": 4, "route_exercises": 8}
    assert {row["route"] for row in body["rows"]} == {"root", "legacy_adapter"}
    assert all(row["passed"] is True for row in body["rows"])
    admitted = [
        row for row in body["rows"] if row["expected_disposition"] == "ADMIT"
    ]
    refused = [
        row for row in body["rows"] if row["expected_disposition"] == "REFUSE"
    ]
    held = [row for row in body["rows"] if row["expected_disposition"] == "HOLD"]
    assert len(admitted) == 2
    assert len(refused) == 4
    assert len(held) == 2
    assert all(
        row["result"]["body"]["reason_code"]
        == "PACKAGE_OUTSIDE_CB_LIGHT_PROPOSAL_DOMAIN"
        for row in refused
    )
    assert all(
        row["result"]["body"]["reason_code"]
        == "CANDIDATE_NOT_SELECTED_FOR_INSTALL"
        for row in held
    )
