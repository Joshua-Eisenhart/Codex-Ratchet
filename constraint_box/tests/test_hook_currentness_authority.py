"""The currentness constraint binds to the authoritative registry, not the caller.

A gate bypass was demonstrated in-session: a session_start payload carrying a
forged-fresh estate_rows override wrote a CURRENTNESS_VALID receipt to the
production chain, which cleared a genuinely stale estate. A constraint an LLM
can satisfy by supplying its own input is not a constraint.

The fix: when the authoritative registry config exists, it wins and any payload
override is ignored. The override is honored only in an isolated root that has
no config, which is how tests drive the fact both ways.

This probe pins both sides.
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


def _kernel(cwd, root, event, payload):
    proc = subprocess.run(
        [PY, "-m", "hookkernel.kernel", event, "--payload-json", json.dumps(payload)],
        capture_output=True, text=True, cwd=cwd,
        env={"PYTHONPATH": str(cwd), "CB_HOOKKERNEL_ROOT": str(root), "PATH": "/usr/bin:/bin"},
    )
    assert proc.stdout.strip(), proc.stderr
    return json.loads(proc.stdout.strip().splitlines()[-1])["payload"]


@pytest.mark.skipif(SOURCE is None, reason="hookkernel package not found")
def test_forged_override_is_ignored_when_authoritative_config_exists(tmp_path):
    # A root WITH an authoritative config that declares one stale package.
    root = tmp_path / "hookkernel"
    shutil.copytree(SOURCE, root)
    (root / "receipts.jsonl").unlink(missing_ok=True)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "cb_light_library_candidates.json").write_text(json.dumps({
        "stale_days_max": 548,
        "candidates": [{"pypi_name": "stalelib", "verified": {"release_date": "2023-01-01"}}],
    }))

    # A forged-fresh override must NOT clear the real staleness.
    forged = {"estate_rows": [{"id": "stalelib", "date": "2026-08-08"}], "today": "2026-08-09"}
    r = _kernel(tmp_path, root, "session_start", forged)
    assert r["reason_code"] == "CURRENTNESS_EXPIRED", r
    assert any(row["id"] == "stalelib" for row in r["details"]["stale"]), r


@pytest.mark.skipif(SOURCE is None, reason="hookkernel package not found")
def test_override_is_honored_in_isolated_root_without_config(tmp_path):
    # No config beside the root: the isolated test may drive the fact.
    root = tmp_path / "hookkernel"
    shutil.copytree(SOURCE, root)
    (root / "receipts.jsonl").unlink(missing_ok=True)

    fresh = {"estate_rows": [{"id": "x", "date": "2026-08-01"}], "today": "2026-08-09"}
    assert _kernel(tmp_path, root, "session_start", fresh)["reason_code"] == "CURRENTNESS_VALID"
    stale = {"estate_rows": [{"id": "x", "date": "2023-01-01"}], "today": "2026-08-09"}
    assert _kernel(tmp_path, root, "session_start", stale)["reason_code"] == "CURRENTNESS_EXPIRED"
