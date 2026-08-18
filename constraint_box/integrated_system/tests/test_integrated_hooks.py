from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest


SYSTEM = Path(__file__).resolve().parents[1]
HOOKS = SYSTEM / "hooks"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


adapter = _load("integrated_portable_host_hook", HOOKS / "portable_host_hook.py")
plan = _load("integrated_hook_install_plan", HOOKS / "install_plan.py")


def _payload(host: str, event: str = "pre", command: str = "echo ready") -> dict:
    if host == "hermes":
        if event == "session":
            return {"event": "on_session_start", "extra": {"task_id": "s-hermes"}}
        if event == "cancel":
            return {
                "event": "on_session_end",
                "extra": {"task_id": "s-hermes", "interrupted": True},
            }
        return {
            "event": "pre_tool_call",
            "extra": {"task_id": "s-hermes"},
            "tool": "terminal",
            "args": {"call_id": "i-hermes", "command": command},
        }
    if host == "grok":
        if event == "session":
            return {"hookEventName": "SessionStart", "sessionId": "s-grok"}
        if event == "cancel":
            return {"hookEventName": "Stop", "sessionId": "s-grok", "cancelled": True}
        return {
            "hookEventName": "pre_tool_use",
            "sessionId": "s-grok",
            "toolUseId": "i-grok",
            "toolName": "terminal",
            "toolInput": {"command": command},
        }
    if event == "session":
        return {"hook_event_name": "SessionStart", "session_id": f"s-{host}"}
    if event == "cancel":
        return {"hook_event_name": "Stop", "session_id": f"s-{host}"}
    return {
        "hook_event_name": "PreToolUse",
        "session_id": f"s-{host}",
        "tool_use_id": f"i-{host}",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }


def _binding_env(root: Path, interpreter: Path) -> dict[str, str]:
    return {
        "CB_PRODUCT_ROOT": str(root),
        "CB_LIGHT_PYTHON": str(interpreter),
    }


def _contained_runtime(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Make a product-confined executable/source pair for binding fixtures."""

    root = tmp_path / "product"
    source = root / "integrated_system" / "hooks" / "portable_host_hook.py"
    interpreter = root / "light" / "bin" / "python3.13"
    source.parent.mkdir(parents=True)
    interpreter.parent.mkdir(parents=True)
    shutil.copy2(HOOKS / "portable_host_hook.py", source)
    interpreter.symlink_to(Path(sys.executable).resolve())
    (root / "light" / "pyvenv.cfg").write_text(
        "home = /usr/bin\ninclude-system-site-packages = false\nversion = fixture\n",
        encoding="utf-8",
    )
    return root, interpreter, source


def _contained_shell_runtime(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    root, interpreter, source = _contained_runtime(tmp_path)
    shell = root / "integrated_system" / "hooks" / "cb_hook.sh"
    shutil.copy2(HOOKS / "cb_hook.sh", shell)
    shell.chmod(0o755)
    return root, interpreter, source, shell


def test_one_neutral_envelope_normalizes_all_four_host_shapes() -> None:
    for host in adapter.HOSTS:
        session = adapter.normalize_event(_payload(host, "session"), host_hint=host)
        pre = adapter.normalize_event(_payload(host), host_hint=host)
        assert session["schema"] == adapter.SCHEMA
        assert session["host"] == host
        assert session["event_type"] == adapter.SESSION_START
        assert session["session_id"] == f"s-{host}"
        assert pre["event_type"] == adapter.PRE_TOOL
        assert pre["session_id"] == f"s-{host}"
        assert pre["invocation_id"] == f"i-{host}"
        assert pre["promotion_allowed"] is False


def test_unmanaged_host_launch_is_refused_for_each_host() -> None:
    for host in adapter.HOSTS:
        result = adapter.process_event(
            _payload(host, command="codex --version"),
            host_hint=host,
            env={},
        )
        assert result["allow"] is False
        assert result["disposition"] == "REFUSE_UNMANAGED_LLM_SPAWN"
        assert result["authority_removed"] is True
        assert result["llm_spawn"] is True


def test_cb_owned_lease_passes_without_semantic_gate(tmp_path: Path) -> None:
    lease = tmp_path / "state" / "leases" / "run-1" / "dispatch.nonce"
    lease.parent.mkdir(parents=True)
    lease.write_text("nonce-1\n", encoding="utf-8")
    env = _binding_env(tmp_path, Path(sys.executable))
    env.update(
        {
            "CB_BOX_RUN_ID": "run-1",
            "CB_DISPATCH_NONCE": "nonce-1",
            "CB_DISPATCH_NONCE_FILE": str(lease),
        }
    )
    result = adapter.process_event(
        _payload("grok", command="codex --version"),
        host_hint="codex",
        env=env,
    )
    assert result["allow"] is True
    assert result["disposition"] == "ALLOW_PASSTHROUGH"
    assert result["cb_owned"] is True
    assert result["promotion_allowed"] is False


def test_provider_ownership_rejects_names_modules_and_forged_environment(tmp_path: Path) -> None:
    # Command names and module names are not ownership evidence.  The
    # bounded ``cb --`` wrapper is still classified as a provider launch, so
    # the absence of a lease becomes a refusal rather than a bypass.
    assert adapter.is_cb_owned("cb -- grok --version", env={}) is False
    assert adapter.is_cb_owned("portable_host_hook.py -- grok --version", env={}) is False
    assert adapter.is_cb_owned("python -m constraintbox.provider", env={}) is False
    ordinary_cb = adapter.process_event(
        _payload("codex", command="python -m constraintbox doctor"),
        host_hint="codex",
        env={},
    )
    assert ordinary_cb["allow"] is True
    assert ordinary_cb["llm_spawn"] is False
    for command in (
        "cb -- grok --version",
        "portable_host_hook.py -- grok --version",
        "python -m constraintbox.provider grok --version",
    ):
        result = adapter.process_event(
            _payload("codex", command=command),
            host_hint="codex",
            env={},
        )
        assert result["llm_spawn"] is True
        assert result["cb_owned"] is False
        assert result["disposition"] == "REFUSE_UNMANAGED_LLM_SPAWN"

    forged = {
        "CB_PRODUCT_ROOT": str(tmp_path),
        "CB_LIGHT_PYTHON": sys.executable,
        "CB_BOX_RUN_ID": "run-forged",
        "CB_DISPATCH_NONCE": "nonce-forged",
        "CB_DISPATCH": "1",
    }
    assert adapter.is_cb_owned("grok --version", env=forged) is False
    assert adapter.is_cb_owned("python -m constraintbox.provider grok", env=forged) is False


def test_wrong_and_outside_nonce_files_are_not_leases(tmp_path: Path) -> None:
    root = tmp_path / "product"
    inside = root / "state" / "leases" / "run-1" / "dispatch.nonce"
    inside.parent.mkdir(parents=True)
    inside.write_text("actual\n", encoding="utf-8")
    wrong = {
        "CB_PRODUCT_ROOT": str(root),
        "CB_BOX_RUN_ID": "run-1",
        "CB_DISPATCH_NONCE": "not-actual",
        "CB_DISPATCH_NONCE_FILE": str(inside),
    }
    assert adapter.is_cb_owned("grok --version", env=wrong) is False

    outside = tmp_path / "outside" / "dispatch.nonce"
    outside.parent.mkdir()
    outside.write_text("actual\n", encoding="utf-8")
    escaped = dict(wrong)
    escaped.update(
        {
            "CB_DISPATCH_NONCE": "actual",
            "CB_DISPATCH_NONCE_FILE": str(outside),
        }
    )
    assert adapter.is_cb_owned("grok --version", env=escaped) is False


def test_explicit_product_root_overrides_ambient_lease_root(tmp_path: Path) -> None:
    explicit_root = tmp_path / "explicit"
    ambient_root = tmp_path / "ambient"
    nonce = ambient_root / "state" / "leases" / "run-ambient" / "dispatch.nonce"
    nonce.parent.mkdir(parents=True)
    nonce.write_text("ambient-nonce\n", encoding="utf-8")
    env = {
        "CB_PRODUCT_ROOT": str(ambient_root),
        "CB_BOX_RUN_ID": "run-ambient",
        "CB_DISPATCH_NONCE": "ambient-nonce",
        "CB_DISPATCH_NONCE_FILE": str(nonce),
    }
    result = adapter.process_event(
        _payload("codex", command="grok --version"),
        host_hint="codex",
        env=env,
        product_root=explicit_root,
    )
    assert result["allow"] is False
    assert result["cb_owned"] is False
    assert result["disposition"] == "REFUSE_UNMANAGED_LLM_SPAWN"


def test_run_stdio_binds_lease_and_event_to_explicit_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, interpreter, source = _contained_runtime(tmp_path)
    ambient_root = tmp_path / "ambient"
    nonce = ambient_root / "state" / "leases" / "run-ambient" / "dispatch.nonce"
    nonce.parent.mkdir(parents=True)
    nonce.write_text("ambient-nonce\n", encoding="utf-8")
    event_log = root / "integrated_system" / "runs" / "hook-events.jsonl"
    env = _binding_env(ambient_root, interpreter)
    env.update(
        {
            "CB_BOX_RUN_ID": "run-ambient",
            "CB_DISPATCH_NONCE": "ambient-nonce",
            "CB_DISPATCH_NONCE_FILE": str(nonce),
            "CB_HOOK_EVENT_LOG": str(event_log),
        }
    )
    monkeypatch.setattr(
        adapter.sys,
        "stdin",
        io.StringIO(json.dumps(_payload("codex", command="grok --version"))),
    )
    assert (
        adapter.run_stdio(
            "codex",
            product_root=root,
            light_interpreter=interpreter,
            event_log=event_log,
            hook_source=source,
            env=env,
            print_envelope=True,
        )
        == 0
    )
    row = json.loads(event_log.read_text(encoding="utf-8").splitlines()[0])
    assert row["binding"]["product_root"] == str(root.resolve())
    assert row["cb_owned"] is False
    assert row["disposition"] == "REFUSE_UNMANAGED_LLM_SPAWN"


def test_unknown_event_with_command_still_refuses_unleased_provider() -> None:
    unknown = {
        "tool_name": "Bash",
        "tool_input": {"command": "grok --version"},
    }
    result = adapter.process_event(unknown, host_hint="claude", env={})
    assert result["event_type"] == adapter.UNKNOWN
    assert result["llm_spawn"] is True
    assert result["cb_owned"] is False
    assert result["allow"] is False
    assert result["disposition"] == "REFUSE_UNMANAGED_LLM_SPAWN"

    non_command = {"session_id": "s-unknown", "status": "waiting"}
    observed = adapter.process_event(non_command, host_hint="claude", env={})
    assert observed["event_type"] == adapter.UNKNOWN
    assert observed["allow"] is True
    assert observed["disposition"] == "BYPASS_OBSERVED"

    edit_body = adapter.process_event(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": "grok --version",
        },
        host_hint="claude",
        env={},
    )
    assert edit_body["allow"] is True
    assert edit_body["llm_spawn"] is False


def test_versioned_python_cb_module_provider_shapes_are_unmanaged() -> None:
    commands = [
        "python3.13 -m constraintbox.provider grok --version",
        "python3.13 -m constraintbox.grok_cli_adapter --version",
        "/opt/light/bin/python3.13 -m constraintbox.provider --provider=grok",
        "python3.13 -m constraintbox.provider --route grok --version",
    ]
    assert all(adapter.is_unmanaged_spawn(command) for command in commands)
    for command in commands:
        result = adapter.process_event(
            {"tool_input": {"command": command}},
            host_hint="codex",
            env={},
        )
        assert result["allow"] is False
        assert result["disposition"] == "REFUSE_UNMANAGED_LLM_SPAWN"


def test_binding_requires_contained_interpreter_and_hook_source(tmp_path: Path) -> None:
    root, interpreter, source = _contained_runtime(tmp_path)
    event_log = root / "integrated_system" / "runs" / "hook-events.jsonl"
    good = adapter.binding_status(root, interpreter, event_log, hook_source=source)
    assert good["status"] == "PASS", good
    assert good["light_interpreter_sha256"] == adapter.sha256_file(interpreter)
    assert good["hook_source_sha256"] == adapter.sha256_file(source)

    outside_interpreter = adapter.binding_status(
        root,
        sys.executable,
        event_log,
        hook_source=source,
    )
    assert outside_interpreter["status"] == "HOLD"
    assert outside_interpreter["reason_code"] == "HOLD_CB_LIGHT_INTERPRETER_OUTSIDE_PRODUCT"

    outside_source = tmp_path / "copied-outside-hook.py"
    shutil.copy2(source, outside_source)
    outside_hook = adapter.binding_status(
        root,
        interpreter,
        event_log,
        hook_source=outside_source,
    )
    assert outside_hook["status"] == "HOLD"
    assert outside_hook["reason_code"] == "HOLD_CB_HOOK_SOURCE_OUTSIDE_PRODUCT"

    fake = root / "fake-light" / "bin" / "python3"
    fake.parent.mkdir(parents=True)
    (fake.parent.parent / "pyvenv.cfg").write_text(
        "home = /usr/bin\nversion = fixture\n", encoding="utf-8"
    )
    fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    fake_light = adapter.binding_status(root, fake, event_log, hook_source=source)
    assert fake_light["status"] == "HOLD"
    assert fake_light["reason_code"] == "HOLD_CB_LIGHT_INTERPRETER_NOT_NATIVE"


def test_binding_rejects_arbitrary_symlink_config_escape_and_traversal(tmp_path: Path) -> None:
    root, interpreter, source = _contained_runtime(tmp_path)
    event_log = root / "integrated_system" / "runs" / "hook-events.jsonl"
    cfg = root / "light" / "pyvenv.cfg"
    escaped_cfg = tmp_path / "escaped-pyvenv.cfg"
    escaped_cfg.write_text("home = /usr/bin\nversion = escaped\n", encoding="utf-8")
    cfg.unlink()
    cfg.symlink_to(escaped_cfg)
    symlink_cfg = adapter.binding_status(root, interpreter, event_log, hook_source=source)
    assert symlink_cfg["status"] == "HOLD"
    assert symlink_cfg["reason_code"] == "HOLD_CB_LIGHT_PYVENV_CONFIG_INVALID"

    cfg.unlink()
    cfg.write_text("home = /usr/bin\nversion = restored\n", encoding="utf-8")
    outside_venv = tmp_path / "outside-venv"
    (outside_venv / "bin").mkdir(parents=True)
    (outside_venv / "bin" / "python3.13").symlink_to(Path(sys.executable).resolve())
    (outside_venv / "pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")
    escaped_root = root / "escaped-venv"
    escaped_root.symlink_to(outside_venv, target_is_directory=True)
    escaped_light = escaped_root / "bin" / "python3.13"
    escaped = adapter.binding_status(root, escaped_light, event_log, hook_source=source)
    assert escaped["status"] == "HOLD"
    assert escaped["reason_code"] == "HOLD_CB_LIGHT_VENV_ESCAPED"

    traversal = Path(str(root / "light" / "bin") + "/../bin/python3.13")
    traversed = adapter.binding_status(root, traversal, event_log, hook_source=source)
    assert traversed["status"] == "HOLD"
    assert traversed["reason_code"] == "HOLD_CB_LIGHT_INTERPRETER_PATH_TRAVERSAL"

    arbitrary = root / "arbitrary-link"
    arbitrary.symlink_to(Path(sys.executable).resolve())
    arbitrary_result = adapter.binding_status(root, arbitrary, event_log, hook_source=source)
    assert arbitrary_result["status"] == "HOLD"
    assert arbitrary_result["reason_code"] == "HOLD_CB_LIGHT_INTERPRETER_NOT_VENV_ENTRYPOINT"


def test_bounded_nested_shell_and_python_process_forms_are_detected() -> None:
    commands = [
        "sh -c 'grok --version'",
        "bash -lc 'echo ready; codex --version'",
        "zsh -c 'python3 -c \"import os; os.system(\\\"hermes --version\\\")\"'",
        "python3 -c 'import os; os.system(\"grok --version\")'",
        "python3 -c 'import os; os.execvp(\"claude\", [\"claude\"])'",
        "python3 -c 'import asyncio; asyncio.create_subprocess_exec(\"hermes\")'",
        "python3 -c 'import asyncio; asyncio.create_subprocess_shell(\"codex --version\")'",
        "python3 -c 'import subprocess; subprocess.run([\"grok\", \"--version\"])'",
        "python3.13 -c 'import subprocess; subprocess.run(args=[\"grok\"])'",
        "python3.13 -c 'import subprocess; subprocess.Popen(args=[\"claude\"])'",
        "python3.13 -c 'import asyncio; asyncio.create_subprocess_exec(program=\"hermes\")'",
        "python3.13 -c 'import asyncio; asyncio.create_subprocess_shell(cmd=\"codex --version\")'",
        "python3.13 -c 'import os; os.system(command=\"grok --version\")'",
    ]
    assert all(adapter.is_unmanaged_spawn(command) for command in commands)
    # Dynamic values are deliberately outside the bounded static claim.
    assert not adapter.is_unmanaged_spawn("python3 -c 'import os; os.system(command)'")


def test_exact_denial_wire_shape_for_each_host() -> None:
    reason = (
        "REFUSE_UNMANAGED_LLM_SPAWN;status=RELAYED;"
        "portable hook strips unmanaged authority only;"
        "semantic CB decisions remain outside this shim"
    )
    for host in adapter.HOSTS:
        result = adapter.process_event(
            _payload(host, command=f"{host} --version"),
            host_hint=host,
            env={},
        )
        wire, code = adapter.emit_host(result, host)
        body = json.loads(wire)
        if host in {"codex", "claude"}:
            assert code == 0
            assert body == {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        elif host == "grok":
            assert code == 0
            assert body == {"decision": "deny", "reason": reason}
        else:
            assert code == 2
            assert body == {"action": "block", "message": reason}


def test_ordinary_passthrough_and_typed_proposal_are_observational() -> None:
    ordinary = adapter.process_event(_payload("claude"), host_hint="claude", env={})
    assert ordinary["allow"] is True
    assert ordinary["disposition"] == "ALLOW_PASSTHROUGH"
    proposal = {"operation_id": "fixture-op", "probe_digest": "a" * 64}
    relayed = adapter.process_event(
        {**_payload("claude"), "typed_proposal": proposal},
        host_hint="claude",
        env={},
    )
    assert relayed["allow"] is True
    assert relayed["disposition"] == "RELAY_TYPED_PROPOSAL"
    assert relayed["typed_proposal"] == proposal


def test_malformed_payload_fails_closed_and_host_wire_is_typed() -> None:
    result = adapter.process_event(
        {},
        host_hint="claude",
        source_bytes=b"not-json",
        parse_error="json_decode",
        env={},
    )
    assert result["allow"] is False
    assert result["disposition"] == "REFUSE_MALFORMED_HOOK_PAYLOAD"
    wire, code = adapter.emit_host(result, "claude")
    assert code == 0
    body = json.loads(wire)
    assert body["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "REFUSE_MALFORMED_HOOK_PAYLOAD" in body["hookSpecificOutput"]["permissionDecisionReason"]


def test_cancel_is_preserved_and_never_passes() -> None:
    for host in adapter.HOSTS:
        result = adapter.process_event(_payload(host, "cancel"), host_hint=host, env={})
        assert result["status"] == adapter.CANCELLED
        assert result["cancelled"] is True
        assert result["allow"] is False
        assert result["disposition"] == "CANCELLED_NO_AUTHORITY"
        wire, code = adapter.emit_host(result, host)
        if host == "hermes":
            assert code == 0
            assert json.loads(wire) == {"action": "allow"}
        else:
            assert "CANCELLED" in wire


def test_hermes_interrupted_session_end_is_logged_as_passive_cancel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, interpreter, source = _contained_runtime(tmp_path)
    payload = {
        "event": "on_session_end",
        "extra": {"task_id": "s-hermes", "interrupted": True},
    }
    normalized = adapter.normalize_event(payload, host_hint="hermes")
    assert normalized["event_type"] == adapter.CANCEL
    assert normalized["normalization_note"] == "hermes_interrupted_session_end"
    result = adapter.process_event(payload, host_hint="hermes", env={})
    assert result["status"] == adapter.CANCELLED
    assert result["disposition"] == "CANCELLED_NO_AUTHORITY"
    assert result["allow"] is False
    wire, code = adapter.emit_host(result, "hermes")
    assert code == 0
    assert json.loads(wire) == {"action": "allow"}

    event_log = root / "integrated_system" / "runs" / "hook-events.jsonl"
    monkeypatch.setattr(adapter.sys, "stdin", io.StringIO(json.dumps(payload)))
    assert (
        adapter.run_stdio(
            "hermes",
            product_root=root,
            light_interpreter=interpreter,
            event_log=event_log,
            hook_source=source,
            env=_binding_env(root, interpreter),
            print_envelope=True,
        )
        == 0
    )
    row = json.loads(event_log.read_text(encoding="utf-8").splitlines()[0])
    assert row["status"] == adapter.CANCELLED
    assert row["disposition"] == "CANCELLED_NO_AUTHORITY"
    assert row["normalization_note"] == "hermes_interrupted_session_end"


def test_missing_interpreter_is_a_hold_before_payload_route(tmp_path: Path) -> None:
    root, _interpreter, source, hook = _contained_shell_runtime(tmp_path)
    event_log = root / "integrated_system" / "runs" / "hook-events.jsonl"
    env = {
        "CB_PRODUCT_ROOT": str(root),
        "CB_LIGHT_PYTHON": str(root / "missing-python"),
        "CB_HOOK_EVENT_LOG": str(event_log),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    proc = subprocess.run(
        ["sh", str(hook), "codex"],
        input=json.dumps(_payload("codex")),
        text=True,
        capture_output=True,
        env={**os.environ, **env},
        check=False,
    )
    # The Codex wire carries a typed denial, so the hook process itself exits
    # zero after the fixed bootstrap has logged the Light hold.
    assert proc.returncode == 0
    assert proc.stderr == ""
    denial = json.loads(proc.stdout)
    assert denial["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "HOLD_CB_LIGHT_INTERPRETER_MISSING" in denial["hookSpecificOutput"]["permissionDecisionReason"]
    rows = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert rows[0]["binding"]["hook_source"] == str(source.resolve())
    assert rows[0]["disposition"] == "HOLD_CB_LIGHT_INTERPRETER_MISSING"


def test_fake_light_is_not_executed_by_shell_and_is_logged_as_hold(tmp_path: Path) -> None:
    root, _interpreter, _source, hook = _contained_shell_runtime(tmp_path)
    marker = root / "fake-light-executed"
    fake = root / "fake-light" / "bin" / "python3"
    fake.parent.mkdir(parents=True)
    (fake.parent.parent / "pyvenv.cfg").write_text(
        "home = /usr/bin\nversion = fixture\n", encoding="utf-8"
    )
    fake.write_text(f"#!/bin/sh\ntouch '{marker}'\n", encoding="utf-8")
    fake.chmod(0o755)
    event_log = root / "integrated_system" / "runs" / "hook-events.jsonl"
    env = {
        "CB_PRODUCT_ROOT": str(root),
        "CB_LIGHT_PYTHON": str(fake),
        "CB_HOOK_EVENT_LOG": str(event_log),
    }
    proc = subprocess.run(
        ["sh", str(hook), "codex"],
        input=json.dumps(_payload("codex", command="echo ready")),
        text=True,
        capture_output=True,
        env={**os.environ, **env},
        check=False,
    )
    assert proc.returncode == 0
    assert not marker.exists()
    row = json.loads(event_log.read_text(encoding="utf-8").splitlines()[0])
    assert row["disposition"] == "HOLD_CB_LIGHT_INTERPRETER_NOT_NATIVE"


def test_shell_refuses_product_local_hook_symlink_before_bootstrap(tmp_path: Path) -> None:
    root, interpreter, source, hook = _contained_shell_runtime(tmp_path)
    marker = tmp_path / "symlink-source-executed"
    outside_source = tmp_path / "outside-source.py"
    outside_source.write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
        encoding="utf-8",
    )
    source.unlink()
    source.symlink_to(outside_source)
    event_log = root / "integrated_system" / "runs" / "hook-events.jsonl"
    plan_result = plan.build_plan(
        product_root=root,
        light_interpreter=interpreter,
        hook_source=source,
        target_root=tmp_path / "plan-target",
    )
    assert plan_result["status"] == "HOLD"
    assert any(
        row["reason_code"] == "HOLD_CB_HOOK_SOURCE_SYMLINK"
        for row in plan_result["checks"]
    )
    env = {
        "CB_PRODUCT_ROOT": str(root),
        "CB_LIGHT_PYTHON": str(interpreter),
        "CB_HOOK_EVENT_LOG": str(event_log),
    }
    proc = subprocess.run(
        ["sh", str(hook), "codex"],
        input=json.dumps(_payload("codex", command="echo ready")),
        text=True,
        capture_output=True,
        env={**os.environ, **env},
        check=False,
    )
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert "HOLD_HOOK_SOURCE_SYMLINK" in proc.stderr
    assert not marker.exists()
    assert not event_log.exists()


def test_shell_refuses_multilink_hook_before_bootstrap(tmp_path: Path) -> None:
    root, interpreter, source, hook = _contained_shell_runtime(tmp_path)
    hardlink = tmp_path / "portable-host-hook-hardlink.py"
    hardlink.hardlink_to(source)
    event_log = root / "integrated_system" / "runs" / "hook-events.jsonl"
    proc = subprocess.run(
        ["sh", str(hook), "codex"],
        input=json.dumps(_payload("codex", command="echo hardlink")),
        text=True,
        capture_output=True,
        env={
            **os.environ,
            "CB_PRODUCT_ROOT": str(root),
            "CB_LIGHT_PYTHON": str(interpreter),
        },
        check=False,
    )
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert "HOLD_HOOK_SOURCE_MULTILINK" in proc.stderr
    assert not event_log.exists()


def test_shell_refuses_external_hook_directory_relocation_before_bootstrap(
    tmp_path: Path,
) -> None:
    root, interpreter, source, hook = _contained_shell_runtime(tmp_path)
    relocated_root = tmp_path / "relocated-product"
    relocated_hooks = relocated_root / "integrated_system" / "hooks"
    relocated_hooks.mkdir(parents=True)
    relocated_hook = relocated_hooks / "cb_hook.sh"
    relocated_source = relocated_hooks / "portable_host_hook.py"
    shutil.copy2(hook, relocated_hook)
    shutil.copy2(source, relocated_source)
    marker = tmp_path / "relocated-source-executed"
    relocated_source.write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
        encoding="utf-8",
    )
    relocated_hook.chmod(0o755)
    event_log = root / "integrated_system" / "runs" / "hook-events.jsonl"
    env = {
        "CB_PRODUCT_ROOT": str(root),
        "CB_LIGHT_PYTHON": str(interpreter),
        "CB_HOOK_EVENT_LOG": str(event_log),
    }
    proc = subprocess.run(
        ["sh", str(relocated_hook), "codex"],
        input=json.dumps(_payload("codex", command="echo ready")),
        text=True,
        capture_output=True,
        env={**os.environ, **env},
        check=False,
    )
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert "HOLD_HOOK_SHIM_PRODUCT_ROOT_MISMATCH" in proc.stderr
    assert not marker.exists()
    assert not event_log.exists()


def test_run_stdio_appends_one_auditable_event_for_each_lifecycle_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, interpreter, source = _contained_runtime(tmp_path)
    event_log = root / "integrated_system" / "runs" / "hook-events.jsonl"
    env = _binding_env(root, interpreter)
    env["CB_HOOK_EVENT_LOG"] = str(event_log)
    payloads = [
        _payload("codex", "session"),
        _payload("codex", command="echo ready"),
        _payload("codex", command="grok --version"),
        _payload("codex", "cancel"),
    ]
    for payload in payloads:
        monkeypatch.setattr(adapter.sys, "stdin", io.StringIO(json.dumps(payload)))
        assert (
            adapter.run_stdio(
                "codex",
                product_root=root,
                light_interpreter=interpreter,
                event_log=event_log,
                hook_source=source,
                env=env,
                print_envelope=True,
            )
            == 0
        )
    rows = event_log.read_bytes().splitlines()
    assert len(rows) == len(payloads)
    decoded = [json.loads(row) for row in rows]
    assert [row["status"] for row in decoded] == [
        adapter.SESSION_BOUND,
        adapter.RELAYED,
        adapter.RELAYED,
        adapter.CANCELLED,
    ]
    for raw, row in zip(rows, decoded):
        assert raw == adapter.canonical_json_bytes(row)
        assert row["light_interpreter_sha256"] == row["binding"]["light_interpreter_sha256"]
        assert row["hook_source_sha256"] == row["binding"]["hook_source_sha256"]
        unsigned = dict(row)
        digest = unsigned.pop("event_sha256")
        assert digest == adapter.sha256_value(unsigned)


def test_event_log_write_failure_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, interpreter, source = _contained_runtime(tmp_path)
    event_log = root / "integrated_system" / "runs" / "hook-events.jsonl"
    env = _binding_env(root, interpreter)
    env["CB_HOOK_EVENT_LOG"] = str(event_log)
    def fail_append(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise OSError("injected append failure")

    monkeypatch.setattr(adapter, "append_event_log", fail_append)
    monkeypatch.setattr(
        adapter.sys,
        "stdin",
        io.StringIO(json.dumps(_payload("grok", command="echo ready"))),
    )
    assert (
        adapter.run_stdio(
            "grok",
            product_root=root,
            light_interpreter=interpreter,
            event_log=event_log,
            hook_source=source,
            env=env,
            print_envelope=True,
        )
        == 0
    )
    printed = json.loads(capsys.readouterr().out)
    assert printed["allow"] is False
    assert printed["disposition"] == "REFUSE_EVENT_LOG_WRITE_FAILED"
    # The printed envelope is not needed for authority: the route is
    # fail-closed even though Grok's typed denial wire normally exits zero.


def test_canonical_log_file_symlink_refuses_without_target_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, interpreter, source = _contained_runtime(tmp_path)
    runs = root / "integrated_system" / "runs"
    runs.mkdir(parents=True)
    target = tmp_path / "internal-target.jsonl"
    target.write_text("sentinel\n", encoding="utf-8")
    log = runs / "hook-events.jsonl"
    log.symlink_to(target)
    monkeypatch.setattr(
        adapter.sys,
        "stdin",
        io.StringIO(json.dumps(_payload("claude", command="echo ready"))),
    )
    assert (
        adapter.run_stdio(
            "claude",
            product_root=root,
            light_interpreter=interpreter,
            event_log=log,
            hook_source=source,
            env=_binding_env(root, interpreter),
            print_envelope=True,
        )
        == 2
    )
    assert target.read_text(encoding="utf-8") == "sentinel\n"
    assert log.is_symlink()


def test_canonical_log_symlinked_parent_refuses_without_target_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, interpreter, source = _contained_runtime(tmp_path)
    integrated = root / "integrated_system"
    integrated.mkdir(parents=True, exist_ok=True)
    target = tmp_path / "redirected-runs"
    target.mkdir()
    sentinel = target / "sentinel.txt"
    sentinel.write_text("sentinel\n", encoding="utf-8")
    (integrated / "runs").symlink_to(target, target_is_directory=True)
    log = root / "integrated_system" / "runs" / "hook-events.jsonl"
    monkeypatch.setattr(
        adapter.sys,
        "stdin",
        io.StringIO(json.dumps(_payload("claude", command="echo ready"))),
    )
    assert (
        adapter.run_stdio(
            "claude",
            product_root=root,
            light_interpreter=interpreter,
            event_log=log,
            hook_source=source,
            env=_binding_env(root, interpreter),
            print_envelope=True,
        )
        == 2
    )
    assert sentinel.read_text(encoding="utf-8") == "sentinel\n"
    assert not (target / "hook-events.jsonl").exists()


def test_tmp_private_tmp_alias_plan_and_shell_share_one_canonical_event(
    tmp_path: Path,
) -> None:
    if not Path("/private/tmp").is_dir() or Path("/tmp").resolve() != Path("/private/tmp").resolve():
        pytest.skip("macOS /tmp alias is unavailable")
    with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
        root, interpreter, source, hook = _contained_shell_runtime(Path(temporary))
        alias_root = Path(str(root).replace("/private", "", 1))
        alias_interpreter = Path(str(interpreter).replace("/private", "", 1))
        alias_source = Path(str(source).replace("/private", "", 1))
        assert alias_root.resolve() == root.resolve()
        plan_result = plan.build_plan(
            product_root=alias_root,
            light_interpreter=alias_interpreter,
            hook_source=alias_source,
            target_root=tmp_path / "plan-target",
        )
        assert plan_result["status"] == "DRY_RUN", plan_result
        assert plan_result["product_root"] == str(root.resolve())
        expected_log = root / "integrated_system" / "runs" / "hook-events.jsonl"
        assert plan_result["event_log"] == str(expected_log)
        proc = subprocess.run(
            ["sh", str(hook), "claude"],
            input=json.dumps(_payload("claude", command="echo alias")),
            text=True,
            capture_output=True,
            env={
                **os.environ,
                "CB_PRODUCT_ROOT": str(alias_root),
                "CB_LIGHT_PYTHON": str(alias_interpreter),
            },
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout == ""
        rows = [json.loads(line) for line in expected_log.read_text(encoding="utf-8").splitlines()]
        assert len(rows) == 1
        assert rows[0]["binding"]["product_root"] == str(root.resolve())
        assert rows[0]["binding"]["event_log"] == str(expected_log)


def test_default_canonical_or_outside_event_log_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, interpreter, source = _contained_runtime(tmp_path)
    payload = _payload("claude", command="echo ready")
    monkeypatch.setattr(adapter.sys, "stdin", io.StringIO(json.dumps(payload)))
    defaulted = adapter.run_stdio(
        "claude",
        product_root=root,
        light_interpreter=interpreter,
        hook_source=source,
        env=_binding_env(root, interpreter),
        print_envelope=True,
    )
    assert defaulted == 0
    canonical = root / "integrated_system" / "runs" / "hook-events.jsonl"
    assert canonical.is_file()

    outside = root.parent / "outside-hook-events.jsonl"
    env = _binding_env(root, interpreter)
    env["CB_HOOK_EVENT_LOG"] = str(outside)
    monkeypatch.setattr(adapter.sys, "stdin", io.StringIO(json.dumps(payload)))
    assert (
        adapter.run_stdio(
            "claude",
            product_root=root,
            light_interpreter=interpreter,
            event_log=outside,
            hook_source=source,
            env=env,
            print_envelope=True,
        )
        == 2
    )


def test_installer_plan_is_dry_run_and_does_not_create_target(tmp_path: Path) -> None:
    root, interpreter, source = _contained_runtime(tmp_path)
    target = tmp_path / "target"
    result = plan.build_plan(
        product_root=root,
        light_interpreter=interpreter,
        target_root=target,
        hook_source=source,
    )
    assert result["status"] == "DRY_RUN"
    assert result["dry_run"] is True
    assert result["mutates"] is False
    assert not target.exists()
    assert {row["host"] for row in result["changes"] if "host" in row} == set(adapter.HOSTS)
    assert all(row["action"].startswith("WOULD_") for row in result["changes"])
    assert result["event_log"] == str(root / "integrated_system" / "runs" / "hook-events.jsonl")
    assert any(row["action"] == "WOULD_BIND_EVENT_LOG" for row in result["changes"])
    assert result["light_interpreter_sha256"] == adapter.sha256_file(interpreter)
    assert result["hook_source_sha256"] == adapter.sha256_file(source)
    assert result["bootstrap_interpreter"] == "/usr/bin/python3"


def test_installer_plan_holds_without_light_interpreter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CB_LIGHT_PYTHON", raising=False)
    monkeypatch.delenv("CB_LIGHT_INTERPRETER", raising=False)
    root, _interpreter, source = _contained_runtime(tmp_path)
    result = plan.build_plan(product_root=root, target_root=tmp_path / "target", hook_source=source)
    assert result["status"] == "HOLD"
    assert "HOLD_CB_LIGHT_INTERPRETER_REQUIRED" in {
        row["reason_code"] for row in result["checks"]
    }
    assert not (tmp_path / "target").exists()


def test_portable_sources_have_no_checkout_or_import_overlay_binding() -> None:
    source_paths = [
        HOOKS / "portable_host_hook.py",
        HOOKS / "install_plan.py",
        HOOKS / "cb_hook.sh",
        HOOKS / "codex.sh",
        HOOKS / "claude.sh",
        HOOKS / "grok.sh",
        HOOKS / "hermes.sh",
    ]
    forbidden = ("/Users/", ".codex", ".claude", "PYTHONPATH", "gpt-", "sonnet", "opus")
    for path in source_paths:
        text = path.read_text(encoding="utf-8").lower()
        assert not any(marker.lower() in text for marker in forbidden), path
