"""Boundary map for HOLD resolution in the completion gate.

The gate first shipped counting every HOLD ever written, with no resolution
path, so a single HOLD deadlocked completion permanently and spurious no-fact
HOLDs (a transient HOOK_RESULT_INVALID) blocked forever. The fix computes open
HOLDs from the LATEST state of each constraint fact: a HOLD closes when a later
receipt restores its fact.

This probe drives the real kernel as a subprocess against an isolated receipt
chain and pins both sides: an unresolved HOLD still blocks; a HOLD followed by
its resolving ADMIT clears.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess

import pytest

PY = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
_CANDIDATES = [
    pathlib.Path(__file__).resolve().parents[1] / "hookkernel",
    pathlib.Path(__file__).resolve().parents[2] / "constraint_box" / "hookkernel",
]
SOURCE = next((p for p in _CANDIDATES if (p / "kernel.py").exists()), None)

OLD_DATE = "2023-01-01"    # far past the 548-day staleness bar
FRESH_DATE = "2026-08-01"  # within the bar


@pytest.mark.skipif(SOURCE is None, reason="hookkernel package not found")
def test_hold_resolves_when_fact_is_restored(tmp_path):
    root = tmp_path / "hookkernel"
    shutil.copytree(SOURCE, root)  # manifest hashes are content-based, still verify
    # Start from a genuinely empty chain — copytree brings the live receipts.jsonl
    # along, and its real HOLDs would otherwise leak into this isolated probe.
    (root / "receipts.jsonl").unlink(missing_ok=True)

    def kernel(event, payload):
        proc = subprocess.run(
            [PY, "-m", "hookkernel.kernel", event, "--payload-json", json.dumps(payload)],
            capture_output=True, text=True, cwd=tmp_path,
            env={"PYTHONPATH": str(tmp_path), "CB_HOOKKERNEL_ROOT": str(root), "PATH": "/usr/bin:/bin"},
        )
        assert proc.stdout.strip(), proc.stderr
        return json.loads(proc.stdout.strip().splitlines()[-1])["payload"]

    stale = {"estate_rows": [{"id": "tabulate", "date": OLD_DATE}], "today": "2026-08-09"}
    fresh = {"estate_rows": [{"id": "tabulate", "date": FRESH_DATE}], "today": "2026-08-09"}

    # 1. a locally old date cannot prove abandonment; it requires a live
    #    authority review and therefore raises a typed HOLD.
    assert kernel("session_start", stale)["reason_code"] == "MAINTENANCE_REVIEW_REQUIRED"

    # 2. completion is refused and names that hold
    r = kernel("task_completion_claimed", {})
    assert r["verdict"] == "REFUSE"
    assert "MAINTENANCE_REVIEW_REQUIRED" in r["details"]["open_holds"]

    # 3. a later fresh local row removes the maintenance-review HOLD, but local
    #    metadata still cannot earn authority-confirmed completion.
    assert kernel("session_start", fresh)["reason_code"] == "CURRENTNESS_LOCAL_OK"
    assert kernel("task_completion_claimed", {})["verdict"] == "REFUSE"

    # 4. the explicit live-authority resolution event settles the fact.
    receipts = root.parent / "receipts"
    receipts.mkdir()
    (receipts / "estate_metadata_authority_v1.json").write_text(json.dumps({
        "rows": [{"name": "tabulate", "status": "agree", "age_days": 1}],
    }))
    assert kernel("estate_metadata_refreshed", {})["reason_code"] == "CURRENTNESS_AUTHORITY_CONFIRMED"

    # 5. the original hold has cleared and the authority-confirmed fact is current.
    r = kernel("task_completion_claimed", {})
    assert "MAINTENANCE_REVIEW_REQUIRED" not in r["details"].get("open_holds", []), r
    assert r["verdict"] == "ADMIT", r
