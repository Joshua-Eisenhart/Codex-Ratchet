"""Adapter tests after council R1 repairs."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import constraintbox.hook_adapter as hook_adapter_module

from constraintbox.hook_adapter import (
    classify_proposal_envelope,
    decide,
    detect_host,
    emit_host,
    is_cb_owned,
    is_llm_spawn,
    run_stdio,
)

ROOT = Path(__file__).resolve().parents[1]
SHIM = ROOT / "hooks" / "universal" / "cb_hook.sh"


def _contained_universal_runtime(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Build a relocatable root-shim fixture with a contained native Light."""

    product = tmp_path / "product"
    shim = product / "hooks" / "universal" / "cb_hook.sh"
    shim.parent.mkdir(parents=True)
    shutil.copy2(SHIM, shim)
    shim.chmod(0o755)
    shutil.copytree(
        ROOT / "integrated_system" / "hooks",
        product / "integrated_system" / "hooks",
    )
    light = product / "light" / "bin" / "python3"
    light.parent.mkdir(parents=True)
    light.symlink_to(Path(sys.executable).resolve())
    (product / "light" / "pyvenv.cfg").write_text(
        "home = /usr/bin\ninclude-system-site-packages = false\nversion = fixture\n",
        encoding="utf-8",
    )
    return product, shim, light


def _pre(cmd: str, event: str = "PreToolUse") -> dict:
    return {
        "hook_event_name": event,
        "tool_name": "Bash",
        "tool_input": {"command": cmd},
    }


def test_unmanaged_codex_blocked() -> None:
    d = decide(_pre("codex exec hi"))
    assert d["allow"] is False
    assert d["disposition"] == "REFUSE_UNMANAGED_LLM_SPAWN"


def test_spoof_substring_constraintbox_still_blocked() -> None:
    d = decide(_pre("echo constraintbox; claude -p hi"))
    assert d["allow"] is False
    assert d["cb_owned"] is False


def test_spoof_cb_dispatch_env_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CB_DISPATCH", "1")
    assert is_cb_owned("codex exec hi") is False
    d = decide(_pre("codex exec hi"))
    assert d["allow"] is False


def test_real_module_invocation_owned() -> None:
    assert is_cb_owned("python -m constraintbox doctor") is True
    d = decide(_pre("python -m constraintbox doctor"))
    assert d["allow"] is True
    assert d["cb_owned"] is True


def test_zip_agent_module_invocation_is_cb_owned() -> None:
    command = "python -m constraintbox_zip_agent.premortem_council_runner"
    assert is_cb_owned(command) is True
    assert decide(_pre(command))["allow"] is True


def test_cb_box_shim_is_cb_owned() -> None:
    command = "scripts/cb_box.py -- grok --version"
    assert is_cb_owned(command) is True
    assert decide(_pre(command))["allow"] is True


def test_cb_lookalike_module_is_not_owned() -> None:
    command = "python -m constraintbox_evil.codex_runner"
    assert is_cb_owned(command) is False
    assert decide(_pre(command))["cb_owned"] is False


def test_pytest_allowed() -> None:
    d = decide(_pre("pytest tests/test_hook_adapter.py -q"))
    assert d["allow"] is True
    assert d["llm_spawn"] is False


def test_edit_body_with_launch_words_is_content_not_process() -> None:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "apply_patch",
        "tool_input": "document " + "co" + "dex launch controls",
    }
    d = decide(payload)
    assert d["allow"] is True
    assert d["llm_spawn"] is False


def test_namespaced_edit_body_is_content_not_process() -> None:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "functions.apply_patch",
        "tool_input": "document " + "co" + "dex launch controls",
    }
    d = decide(payload)
    assert d["allow"] is True
    assert d["llm_spawn"] is False


def test_exact_nested_apply_patch_wrapper_is_content_not_process() -> None:
    patch = "*** Begin Patch\n+document " + "co" + "dex launch controls\n*** End Patch"
    wrapper = (
        f"const patch = {json.dumps(patch)};\n"
        "text(await tools.apply_patch(patch));"
    )
    d = decide(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "functions.exec",
            "tool_input": wrapper,
        }
    )
    assert d["allow"] is True
    assert d["llm_spawn"] is False


def test_nested_apply_patch_wrapper_with_extra_call_is_not_exempt() -> None:
    patch = "*** Begin Patch\n+document\n*** End Patch"
    unsafe = "co" + "dex exec hi"
    wrapper = (
        f"const patch = {json.dumps(patch)};\n"
        f"await tools.exec_command({{cmd: {json.dumps(unsafe)}}});\n"
        "text(await tools.apply_patch(patch));"
    )
    d = decide(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "functions.exec",
            "tool_input": wrapper,
        }
    )
    assert d["allow"] is False
    assert d["disposition"] == "REFUSE_UNMANAGED_LLM_SPAWN"


def test_functions_exec_classifies_nested_cmd_not_js_or_argument_content() -> None:
    harmless = (
        'const r=await tools.exec_command({cmd:'
        + json.dumps(
            "for route in grok sonnet opus; do "
            "python3 prepare.py --route \"$route\"; done"
        )
        + ",workdir:'/tmp'}); text(r.output);"
    )
    d = decide(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "functions.exec",
            "tool_input": harmless,
        }
    )
    assert d["allow"] is True
    assert d["llm_spawn"] is False


@pytest.mark.parametrize(
    "command",
    [
        "python3 prepare.py --models 'grok sonnet opus'",
        "TARGET=grok python3 prepare.py",
        "for route in grok claude; do python3 prepare.py --route \"$route\"; done",
        "python3 -c 'print(\"grok\")'",
    ],
)
def test_model_labels_in_shell_arguments_are_not_process_heads(command: str) -> None:
    d = decide(_pre(command))
    assert d["allow"] is True
    assert d["llm_spawn"] is False


@pytest.mark.parametrize(
    "command",
    [
        "grok --version",
        "/usr/local/bin/claude -p hi",
        "echo ready; codex exec hi",
        "env TEST=1 grok --version",
    ],
)
def test_actual_harness_command_heads_are_refused(command: str) -> None:
    d = decide(_pre(command))
    assert d["allow"] is False
    assert d["disposition"] == "REFUSE_UNMANAGED_LLM_SPAWN"


@pytest.mark.parametrize(
    "command",
    [
        "command -v grok",
        "command -V claude",
        "command -v codex >/dev/null",
    ],
)
def test_shell_command_lookup_does_not_count_as_process_launch(command: str) -> None:
    d = decide(_pre(command))
    assert d["allow"] is True
    assert d["llm_spawn"] is False


def test_real_launch_after_shell_lookup_is_still_refused() -> None:
    d = decide(_pre("command -v grok; grok --version"))
    assert d["allow"] is False
    assert d["disposition"] == "REFUSE_UNMANAGED_LLM_SPAWN"


def test_edit_top_level_command_copy_is_content_not_process() -> None:
    content = "document " + "co" + "dex launch controls"
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "apply_patch",
        "tool_input": {"patch": content},
        "command": content,
    }
    d = decide(payload)
    assert d["allow"] is True
    assert d["llm_spawn"] is False


def test_malformed_payload_refused() -> None:
    d = decide({}, parse_error="json_decode")
    assert d["allow"] is False
    assert d["disposition"] == "REFUSE_MALFORMED_HOOK_PAYLOAD"


def test_stale_map_does_not_block_ordinary_passthrough(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def basin_must_not_run(*_args, **_kwargs):
        raise AssertionError("hook must not call require_basin_view")

    monkeypatch.setattr(
        "constraintbox.basin_view_valve.require_basin_view",
        basin_must_not_run,
    )
    d = decide(_pre("python -m constraintbox doctor"))
    assert d["allow"] is True
    assert d["disposition"] == "ALLOW_PASSTHROUGH"
    assert "basin_view" not in d


def test_host_hint_wins() -> None:
    payload = {
        "hook_event_name": "pre_tool_call",
        "tool_name": "Bash",
        "tool_input": {"command": "codex exec"},
    }
    assert detect_host(payload, "codex") == "codex"
    assert detect_host(payload, "hermes") == "hermes"


def test_hermes_block_shape() -> None:
    d = decide(_pre("grok -p x", event="pre_tool_call"))
    out, code = emit_host(d, "hermes")
    assert code == 2
    assert json.loads(out)["action"] == "block"


def test_codex_pre_tool_use_deny_shape() -> None:
    d = decide(_pre("codex exec hi"))
    out, code = emit_host(d, "codex")
    wire = json.loads(out)
    assert code == 0
    assert wire["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert wire["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "REFUSE_UNMANAGED_LLM_SPAWN" in wire["hookSpecificOutput"]["permissionDecisionReason"]


def test_claude_pre_tool_use_uses_same_typed_deny_shape() -> None:
    d = decide(_pre("claude -p hi"))
    codex_out, codex_code = emit_host(d, "codex")
    claude_out, claude_code = emit_host(d, "claude")
    assert claude_code == codex_code == 0
    assert json.loads(claude_out) == json.loads(codex_out)


def test_adapter_source_does_not_embed_model_slugs() -> None:
    source = Path(hook_adapter_module.__file__).read_text(encoding="utf-8").lower()
    for forbidden in ("gpt-", "claude-", "grok-", "luna", "sonnet", "opus", "fable"):
        assert forbidden not in source


def test_grok_camel_case_pre_tool_payload_is_refused() -> None:
    payload = {
        "hookEventName": "pre_tool_use",
        "toolName": "run_terminal_command",
        "toolInput": {"command": "grok --version"},
    }
    decision = decide(payload)
    out, code = emit_host(decision, "grok")
    wire = json.loads(out)
    assert decision["disposition"] == "REFUSE_UNMANAGED_LLM_SPAWN"
    assert decision["event"] == "pre_tool_use"
    assert decision["tool_name"] == "run_terminal_command"
    assert code == 0
    assert wire["decision"] == "deny"


def test_nonce_ownership(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    box_root = tmp_path / "box"
    run_id = "boxv1-test-nonce"
    nonce = box_root / run_id / "dispatch.nonce"
    nonce.parent.mkdir(parents=True)
    nonce.write_text("abc123\n", encoding="utf-8")
    monkeypatch.setattr("constraintbox.hook_adapter.BOX_ROOT", box_root)
    monkeypatch.setenv("CB_DISPATCH_NONCE", "abc123")
    monkeypatch.setenv("CB_DISPATCH_NONCE_FILE", str(nonce))
    monkeypatch.setenv("CB_BOX_RUN_ID", run_id)
    assert is_cb_owned("codex exec hi") is True


def test_explicit_empty_env_does_not_inherit_ambient_nonce(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    box_root = tmp_path / "box"
    run_id = "boxv1-test-explicit-empty"
    nonce = box_root / run_id / "dispatch.nonce"
    nonce.parent.mkdir(parents=True)
    nonce.write_text("abc123\n", encoding="utf-8")
    monkeypatch.setattr("constraintbox.hook_adapter.BOX_ROOT", box_root)
    monkeypatch.setenv("CB_DISPATCH_NONCE", "abc123")
    monkeypatch.setenv("CB_DISPATCH_NONCE_FILE", str(nonce))
    monkeypatch.setenv("CB_BOX_RUN_ID", run_id)

    assert is_cb_owned("codex exec hi") is True
    assert is_cb_owned("codex exec hi", env={}) is False
    decision = decide(_pre("codex exec hi"), env={})
    assert decision["allow"] is False
    assert decision["disposition"] == "REFUSE_UNMANAGED_LLM_SPAWN"


def test_wrong_nonce_not_owned(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    box_root = tmp_path / "box"
    run_id = "boxv1-test-wrong"
    nonce = box_root / run_id / "dispatch.nonce"
    nonce.parent.mkdir(parents=True)
    nonce.write_text("abc123\n", encoding="utf-8")
    monkeypatch.setattr("constraintbox.hook_adapter.BOX_ROOT", box_root)
    monkeypatch.setenv("CB_DISPATCH_NONCE", "nope")
    monkeypatch.setenv("CB_DISPATCH_NONCE_FILE", str(nonce))
    monkeypatch.setenv("CB_BOX_RUN_ID", run_id)
    assert is_cb_owned("codex exec hi") is False


def test_nonce_outside_box_is_not_ownership(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    nonce = tmp_path / "caller-controlled.nonce"
    nonce.write_text("abc123\n", encoding="utf-8")
    monkeypatch.setattr("constraintbox.hook_adapter.BOX_ROOT", tmp_path / "box")
    monkeypatch.setenv("CB_DISPATCH_NONCE", "abc123")
    monkeypatch.setenv("CB_DISPATCH_NONCE_FILE", str(nonce))
    monkeypatch.setenv("CB_BOX_RUN_ID", "boxv1-fake")
    assert is_cb_owned("codex exec hi") is False


def test_python_subprocess_classified_as_spawn() -> None:
    assert is_llm_spawn("python -c \"import subprocess; subprocess.run(['codex'])\"")


def test_run_stdio_malformed_emits_claude_deny(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", type("S", (), {"read": staticmethod(lambda: "not-json")})())
    monkeypatch.setenv("CB_HOOK_ADAPTER_LOG", str(tmp_path / "e.jsonl"))
    rc = run_stdio("claude")
    wire = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert wire["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "REFUSE_MALFORMED_HOOK_PAYLOAD" in wire["hookSpecificOutput"]["permissionDecisionReason"]


def test_receipt_write_fail_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    blocked = tmp_path / "nope"
    blocked.write_text("x", encoding="utf-8")  # file, not dir — mkdir will fail...
    # point log at a path whose parent cannot be created
    monkeypatch.setenv("CB_HOOK_ADAPTER_LOG", str(blocked / "events.jsonl"))
    monkeypatch.setattr(
        "sys.stdin",
        type("S", (), {"read": staticmethod(lambda: json.dumps(_pre("ls")))})(),
    )
    rc = run_stdio("claude")
    wire = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert wire["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "REFUSE_RECEIPT_WRITE_FAILED" in wire["hookSpecificOutput"]["permissionDecisionReason"]


def test_out_of_scope_named() -> None:
    d = decide(_pre("ls"))
    assert "lead_llm_talk_without_tools" in d["out_of_scope"]


def test_typed_proposal_never_allows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "constraintbox.quarantine_broker.submit",
        lambda raw, **kw: {
            "reason_code": "QUARANTINED_FIXTURE",
            "connector": {"authoritative": False},
        },
    )
    d = decide(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Unknown",
            "request_id": "req-adapter-01",
            "operation_id": "family:launch_classify",
            "probe_digest": "abcd1234ffff",
            "from_state": "propose",
            "to_state": "quarantine",
        }
    )
    assert d["allow"] is False
    assert d["disposition"] == "QUARANTINED_FIXTURE"
    assert d["quarantine"]["reason_code"] == "QUARANTINED_FIXTURE"


def test_proposal_envelope_classifier_is_read_only_and_shape_only() -> None:
    valid = {
        "request_id": "req-shape",
        "operation_id": "family:launch_classify",
        "probe_digest": "abcd1234ffff",
        "from_state": "propose",
        "to_state": "quarantine",
    }
    assert classify_proposal_envelope(valid)["disposition"] == "ADMIT_TYPED_PROPOSAL_ENVELOPE"
    assert classify_proposal_envelope({**valid, "execute": True})["disposition"] == (
        "REFUSE_FORBIDDEN_PROPOSAL_FIELD"
    )
    partial = dict(valid)
    partial.pop("request_id")
    assert classify_proposal_envelope(partial)["missing"] == ["request_id"]


def test_partial_typed_proposal_refuses_before_broker() -> None:
    d = decide(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Unknown",
            "operation_id": "family:launch_classify",
            "probe_digest": "abcd1234ffff",
            "from_state": "propose",
            "to_state": "quarantine",
        }
    )
    assert d["allow"] is False
    assert d["disposition"] == "REFUSE_INCOMPLETE_PROPOSAL"
    assert "request_id" in d["quarantine"]["detail"]


def test_forbidden_typed_proposal_field_refuses_before_broker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broker_must_not_run(*_args, **_kwargs):
        raise AssertionError("forbidden proposal reached the broker")

    monkeypatch.setattr("constraintbox.quarantine_broker.submit", broker_must_not_run)
    d = decide(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Unknown",
            "request_id": "req-adapter-forbidden-01",
            "operation_id": "family:launch_classify",
            "probe_digest": "abcd1234ffff",
            "from_state": "propose",
            "to_state": "quarantine",
            "execute": True,
            "model": "untrusted-metadata",
        }
    )
    assert d["allow"] is False
    assert d["disposition"] == "REFUSE_FORBIDDEN_PROPOSAL_FIELD"
    assert "execute" in d["quarantine"]["detail"]
    assert "model" in d["quarantine"]["detail"]


def test_typed_proposal_receipt_write_failure_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_write(raw, **kw):
        raise OSError("read-only receipt path")

    monkeypatch.setattr("constraintbox.quarantine_broker.submit", fail_write)
    d = decide(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Unknown",
            "request_id": "req-adapter-02",
            "operation_id": "family:launch_classify",
            "probe_digest": "abcd1234ffff",
            "from_state": "propose",
            "to_state": "quarantine",
        }
    )
    assert d["allow"] is False
    assert d["disposition"] == "REFUSE_QUARANTINE_RECEIPT_WRITE_FAILED"


def test_universal_shim_blocks_bare_harness_and_records_receipt(tmp_path: Path) -> None:
    product, shim, light = _contained_universal_runtime(tmp_path)
    log = product / "integrated_system" / "runs" / "hook-events.jsonl"
    env = dict(os.environ)
    # Inherited root and legacy log variables must not select another root or
    # redirect the canonical ignored runtime log.
    env["CB_PRODUCT_ROOT"] = str(tmp_path / "ambient-product")
    env["CB_LIGHT_PYTHON"] = str(light)
    env["CB_HOOK_ADAPTER_LOG"] = str(tmp_path / "outside-legacy-hook-events.jsonl")
    env.pop("CB_HOOK_EVENT_LOG", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    blocked = subprocess.run(
        ["bash", str(shim), "claude"],
        input=json.dumps(_pre("codex exec hello")),
        text=True,
        capture_output=True,
        cwd=product,
        env=env,
        check=False,
    )
    wire = json.loads(blocked.stdout)
    assert blocked.returncode == 0
    assert wire["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert wire["hookSpecificOutput"]["permissionDecision"] == "deny"

    allowed = subprocess.run(
        ["bash", str(shim), "claude"],
        input=json.dumps(_pre("python -m constraintbox doctor")),
        text=True,
        capture_output=True,
        cwd=product,
        env=env,
        check=False,
    )
    assert allowed.returncode == 0
    assert allowed.stdout == ""

    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert [row["disposition"] for row in rows] == [
        "REFUSE_UNMANAGED_LLM_SPAWN",
        "ALLOW_PASSTHROUGH",
    ]
    assert all(row["binding"]["product_root"] == str(product.resolve()) for row in rows)
    assert all("basin_view" not in row for row in rows)


def test_universal_shim_ignores_ambient_product_and_event_roots(tmp_path: Path) -> None:
    product, shim, light = _contained_universal_runtime(tmp_path)
    ambient = tmp_path / "ambient-product"
    ambient.mkdir()
    ambient_log = ambient / "hook-events.jsonl"
    env = dict(os.environ)
    env.update(
        {
            "CB_PRODUCT_ROOT": str(ambient),
            "CB_HOOK_EVENT_LOG": str(ambient_log),
            "CB_LIGHT_PYTHON": str(light),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    env.pop("CB_HOOK_ADAPTER_LOG", None)

    blocked = subprocess.run(
        ["bash", str(shim), "claude"],
        input=json.dumps(_pre("codex exec hello")),
        text=True,
        capture_output=True,
        cwd=product,
        env=env,
        check=False,
    )
    wire = json.loads(blocked.stdout)
    assert blocked.returncode == 0
    assert wire["hookSpecificOutput"]["permissionDecision"] == "deny"

    allowed = subprocess.run(
        ["bash", str(shim), "claude"],
        input=json.dumps(_pre("python -m constraintbox doctor")),
        text=True,
        capture_output=True,
        cwd=product,
        env=env,
        check=False,
    )
    assert allowed.returncode == 0
    assert allowed.stdout == ""
    assert not ambient_log.exists()

    canonical_log = product / "integrated_system" / "runs" / "hook-events.jsonl"
    rows = [json.loads(line) for line in canonical_log.read_text(encoding="utf-8").splitlines()]
    assert [row["disposition"] for row in rows] == [
        "REFUSE_UNMANAGED_LLM_SPAWN",
        "ALLOW_PASSTHROUGH",
    ]
    assert all(row["binding"]["product_root"] == str(product.resolve()) for row in rows)


def test_universal_shim_does_not_relay_legacy_log_outside_product(tmp_path: Path) -> None:
    product, shim, light = _contained_universal_runtime(tmp_path)
    outside_log = tmp_path / "outside" / "hook-events.jsonl"
    env = dict(os.environ)
    env.update(
        {
            "CB_PRODUCT_ROOT": str(tmp_path / "ambient-product"),
            "CB_HOOK_ADAPTER_LOG": str(outside_log),
            "CB_LIGHT_PYTHON": str(light),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    env.pop("CB_HOOK_EVENT_LOG", None)

    proc = subprocess.run(
        ["bash", str(shim), "claude"],
        input=json.dumps(_pre("python -m constraintbox doctor")),
        text=True,
        capture_output=True,
        cwd=product,
        env=env,
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout == ""
    assert not outside_log.exists()
    canonical_log = product / "integrated_system" / "runs" / "hook-events.jsonl"
    row = json.loads(canonical_log.read_text(encoding="utf-8").splitlines()[0])
    assert row["disposition"] == "ALLOW_PASSTHROUGH"
    assert row["binding"]["product_root"] == str(product.resolve())


def test_apply_patch_payload_is_edit_data_not_a_launch() -> None:
    patch = "*** Begin Patch\n*** Add File: note.txt\n+codex exec is documentation\n*** End Patch"
    decision = decide(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {"patch": patch},
        },
        env={},
    )
    assert decision["allow"] is True
    assert decision["llm_spawn"] is False


def test_patch_markers_do_not_exempt_a_shell_tool() -> None:
    patch = "*** Begin Patch\ncodex exec hello\n*** End Patch"
    decision = decide(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": patch},
        },
        env={},
    )
    assert decision["allow"] is False
    assert decision["disposition"] == "REFUSE_UNMANAGED_LLM_SPAWN"
