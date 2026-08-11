#!/usr/bin/env python3
"""Exercise actual CB Light pre-install hook boundaries without installing.

Each case sends a Claude-style Bash payload to the installed root hook and to
the legacy adapter.  The hook only evaluates the proposed command; no package
manager subprocess from the payload is executed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
ROOT_HOOK = REPO / ".claude" / "hooks" / "cb_pretooluse_guard.sh"
LEGACY_ADAPTER = ROOT / "hooks" / "pre_tool.sh"
REFUSAL = "PACKAGE_OUTSIDE_CB_LIGHT_PROPOSAL_DOMAIN"


def payload(command: str) -> bytes:
    return json.dumps(
        {"tool_name": "Bash", "tool_input": {"command": command}}
    ).encode("utf-8")


def invoke(hook: Path, command: str, db: Path) -> dict[str, Any]:
    completed = subprocess.run(
        ["bash", str(hook)],
        cwd=REPO,
        input=payload(command),
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "CLAUDE_PROJECT_DIR": str(REPO),
            "CB_LIGHT_STATE_DB": str(db),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )
    stdout = completed.stdout.decode("utf-8", errors="replace").strip()
    stderr = completed.stderr.decode("utf-8", errors="replace").strip()
    body: dict[str, Any] | None = None
    body_stream = ""
    for stream_name, candidate in (("stdout", stdout), ("stderr", stderr)):
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
            body = parsed if isinstance(parsed, dict) else None
            body_stream = stream_name if body is not None else ""
            if body is not None:
                break
        except json.JSONDecodeError:
            continue
    return {
        "hook": str(hook),
        "returncode": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "body": body,
        "body_stream": body_stream,
    }


def expected_pass(
    result: dict[str, Any], *, expected_disposition: str, expected_reason: str | None
) -> bool:
    if expected_disposition == "ADMIT":
        return result["returncode"] == 0
    body = result.get("body")
    return bool(
        result["returncode"] == 2
        and isinstance(body, dict)
        and body.get("disposition") == expected_disposition
        and body.get("reason_code") == expected_reason
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="exercise-cb-light-hook-boundaries")
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    cases = [
        (
            "declared_static_candidate",
            "/Users/joshuaeisenhart/Codex-Ratchet/constraint_box/.venv/bin/python "
            "-m pip install z3-solver==4.16.0.0",
            "ADMIT",
            None,
        ),
        (
            "undeclared_heavy_adjacent_package",
            "/Users/joshuaeisenhart/Codex-Ratchet/constraint_box/.venv/bin/python "
            "-m pip install jax==0.6.2",
            "REFUSE",
            REFUSAL,
        ),
        (
            "mixed_declared_and_undeclared_package",
            "/Users/joshuaeisenhart/Codex-Ratchet/constraint_box/.venv/bin/python "
            "-m pip install z3-solver==4.16.0.0 requests==2.34.2",
            "REFUSE",
            REFUSAL,
        ),
        (
            "control_profile_package_not_static_candidate",
            "/Users/joshuaeisenhart/Codex-Ratchet/constraint_box/.venv/bin/python "
            "-m pip install pydantic==2.12.5",
            "HOLD",
            "CANDIDATE_NOT_SELECTED_FOR_INSTALL",
        ),
    ]
    hooks = {"root": ROOT_HOOK, "legacy_adapter": LEGACY_ADAPTER}
    rows: list[dict[str, Any]] = []
    for case_id, command, expected_disposition, expected_reason in cases:
        for route, hook in hooks.items():
            result = invoke(hook, command, args.db)
            rows.append(
                {
                    "case_id": case_id,
                    "route": route,
                    "command": command,
                    "expected_disposition": expected_disposition,
                    "expected_reason_code": expected_reason,
                    "passed": expected_pass(
                        result,
                        expected_disposition=expected_disposition,
                        expected_reason=expected_reason,
                    ),
                    "result": result,
                }
            )
    body = {
        "schema": "constraintbox.cb-light-hook-boundary-exercise.v1",
        "exercised_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "db": str(args.db),
        "claim_ceiling": (
            "Synthetic pre-install hook payload exercise only; no payload package "
            "installation was executed, no adoption or CB Heavy claim."
        ),
        "routes": {name: str(path) for name, path in hooks.items()},
        "counts": {"cases": len(cases), "route_exercises": len(rows)},
        "all_passed": all(row["passed"] for row in rows),
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_passed": body["all_passed"], "counts": body["counts"]}))
    return 0 if body["all_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
