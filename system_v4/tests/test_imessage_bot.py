from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import imessage_bot as im  # noqa: E402

FIX_MANIFEST_SCRIPT = REPO_ROOT / "scripts" / "fix_manifest_reasons.py"
FIX_MANIFEST_RESULTS_DIR = Path("system_v4/probes/a2_state/sim_results")
FIX_MANIFEST_TOOLS = (
    "pyg",
    "cvc5",
    "clifford",
    "geomstats",
    "e3nn",
    "rustworkx",
    "xgi",
    "toponetx",
    "gudhi",
    "pytorch",
    "z3",
    "sympy",
)


def test_claude_freeform_uses_read_only_tools(monkeypatch):
    captured = {}

    def fake_claude_call(prompt, system_prompt, tools):
        captured["prompt"] = prompt
        captured["system_prompt"] = system_prompt
        captured["tools"] = tools
        return "ok"

    monkeypatch.setattr(im, "_claude_call", fake_claude_call)

    assert im.claude_freeform("what changed?") == "ok"
    assert captured["prompt"] == "what changed?"
    assert captured["tools"] == "Read,Glob,Grep,Bash"
    assert "Do not edit files" in captured["system_prompt"]
    assert "mutate git" in captured["system_prompt"]
    assert "long-running sims" in captured["system_prompt"]


def test_redact_log_text_hides_imessage_handles(monkeypatch):
    monkeypatch.setattr(im, "PHONE_HANDLE", "+1 707 867 3323")
    monkeypatch.setattr(im, "EMAIL_HANDLE", "user@example.com")
    monkeypatch.setattr(im, "REPLY_HANDLE", "reply@example.com")

    redacted = im._redact_log_text(
        "to +1 707 867 3323 from user@example.com reply reply@example.com"
    )

    assert "+1 707 867 3323" not in redacted
    assert "user@example.com" not in redacted
    assert "reply@example.com" not in redacted
    assert "[redacted-number]" in redacted
    assert "[redacted-email]" in redacted


def test_handle_run_stops_on_cleanup_guard_failure(monkeypatch):
    monkeypatch.setattr(im, "_sim_allowlist", lambda: {"foo"})
    monkeypatch.setattr(im, "_run_cleanup_guard", lambda context: (False, "guard failed"))

    def fail_run(*args, **kwargs):
        raise AssertionError("sim subprocess should not launch when cleanup guard fails")

    monkeypatch.setattr(im.subprocess, "run", fail_run)

    assert im.handle_run("foo") == "guard failed"


def test_handle_tools_run_stops_on_cleanup_guard_failure(monkeypatch):
    monkeypatch.setattr(im, "_run_cleanup_guard", lambda context: (False, "guard failed"))

    def fail_run(*args, **kwargs):
        raise AssertionError("tools subprocess should not launch when cleanup guard fails")

    monkeypatch.setattr(im.subprocess, "run", fail_run)

    assert im.handle_tools("run") == "guard failed"


def _run_manifest_fixer(tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(FIX_MANIFEST_SCRIPT)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )


def test_manifest_fixer_does_not_fabricate_positive_negative_stubs(tmp_path):
    results = tmp_path / FIX_MANIFEST_RESULTS_DIR
    results.mkdir(parents=True)
    target = results / "canonical_missing_sections_results.json"
    target.write_text(
        json.dumps(
            {
                "classification": "canonical",
                "tool_manifest": {
                    tool: {
                        "tried": False,
                        "used": False,
                        "reason": f"{tool} was not required for this focused canonical result check",
                    }
                    for tool in FIX_MANIFEST_TOOLS
                },
            }
        ),
        encoding="utf-8",
    )

    _run_manifest_fixer(tmp_path)

    payload = json.loads(target.read_text(encoding="utf-8"))
    assert "positive" not in payload
    assert "negative" not in payload
    assert "stub" not in json.dumps(payload).lower()


def test_manifest_fixer_skips_non_dict_manifest(tmp_path):
    results = tmp_path / FIX_MANIFEST_RESULTS_DIR
    results.mkdir(parents=True)
    target = results / "bad_manifest_results.json"
    original = {
        "classification": "supporting",
        "tool_manifest": ["not", "a", "dict"],
    }
    target.write_text(json.dumps(original), encoding="utf-8")

    completed = _run_manifest_fixer(tmp_path)

    assert "Skipped non-dict tool_manifest JSON: 1" in completed.stdout
    assert json.loads(target.read_text(encoding="utf-8")) == original
