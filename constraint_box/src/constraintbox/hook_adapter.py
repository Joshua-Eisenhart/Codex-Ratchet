"""Universal CB hook adapter.

Host shells translate payloads. This module is deterministic Python.
It does not admit models by name.

Initial adversarial review required:
- argv host hint wins
- no substring CB-ownership
- malformed JSON fail-closed
- receipt write failure cannot allow
- spawn classifier stays bounded (not a growing roster)
- talk-without-tools remains named out of scope
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import json
import os
import re
import shlex
import secrets
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(
    os.environ.get("CB_BOX_ROOT", str(Path(__file__).resolve().parents[2]))
).expanduser().absolute()
BOX_ROOT = ROOT / "receipts" / "box"
DEFAULT_LOG = ROOT / "receipts" / "hook_adapter" / "events.jsonl"
SCHEMA = "constraintbox.hook_adapter.v1"
CLAIM_CEILING = (
    "host-agnostic unmanaged-spawn seam only; not model policy, "
    "not admission of named models, not a process-creation kernel, "
    "not coverage of talk-without-tools, not Heavy, not completion"
)
OUT_OF_SCOPE = (
    "lead_llm_talk_without_tools",
    "direct_os_exec_after_allowed_parent",
)


@contextlib.contextmanager
def issue_dispatch_lease(request_id: str):
    """Issue one revocable child-process capability under the CB box root.

    A provider launched by a CB adapter must be able to use its declared host
    tools without those child calls looking like an unmanaged lead-model
    bypass.  The nonce exists only while the provider subprocess is alive and
    is bound to a box-owned directory.  The caller receives metadata without
    the nonce bytes; the capability is revoked on context exit.
    """

    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", request_id).strip("-._") or "request"
    run_id = f"provider-{safe[:64]}-{secrets.token_hex(8)}"
    run_root = BOX_ROOT / run_id
    run_root.mkdir(parents=True, exist_ok=False, mode=0o700)
    nonce_path = run_root / "dispatch.nonce"
    nonce = secrets.token_hex(32)
    descriptor = os.open(nonce_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(descriptor, (nonce + "\n").encode("ascii"))
    finally:
        os.close(descriptor)
    overlay = {
        "CB_BOX_RUN_ID": run_id,
        "CB_DISPATCH_NONCE": nonce,
        "CB_DISPATCH_NONCE_FILE": str(nonce_path),
    }
    metadata = {
        "run_id": run_id,
        "nonce_file": str(nonce_path),
        "nonce_sha256": hashlib.sha256(nonce.encode("ascii")).hexdigest(),
    }
    try:
        yield overlay, metadata
    finally:
        try:
            nonce_path.unlink()
        except FileNotFoundError:
            pass
        try:
            run_root.rmdir()
        except OSError:
            pass

# Bounded spawn classifier (harness CLIs), not a model roster.
_SPAWN_BINS = (
    "codex",
    "codex.js",
    "claude",
    "grok",
    "hermes",
    "cursor",
    "aider",
    "opencode",
    "continue",
)

# First-token / -m module ownership only (not later-arg substrings).
_CB_ARGV0_NAMES = {
    "constraintbox",
    "cb-light",
    "cb_light",
    "codex1_gated.py",
    "cb_box.py",
    "cb_hook.sh",
}
_CB_MODULES = {
    "constraintbox",
    "constraintbox.claude_bridge_adapter",
    "constraintbox.codex_cli_adapter",
    "constraintbox.hook_adapter",
    "constraintbox.core_cli",
    "constraintbox.grok_cli_adapter",
    "constraintbox.model_runner_probe",
    "hookkernel.cb_light_gate",
}


def _is_cb_module(module: str) -> bool:
    return (
        module in _CB_MODULES
        or module.startswith("constraintbox.")
        or module == "constraintbox_zip_agent"
        or module.startswith("constraintbox_zip_agent.")
    )

_SPAWN_RE = re.compile(
    r"(?:^|[\s/\\`'\"=])("
    + "|".join(re.escape(b) for b in _SPAWN_BINS)
    + r")(?:\s|$|[\"'])",
    re.IGNORECASE,
)

_PRE_EVENTS = {
    "pretooluse",
    "pre_tool_use",
    "pre_tool_call",
    "userpromptsubmit",
}

_KNOWN_HOSTS = {"hermes", "claude", "codex", "grok", "unknown"}
_PROPOSAL_REQUIRED_FIELDS = {
    "request_id",
    "operation_id",
    "probe_digest",
    "from_state",
    "to_state",
}
# A host may carry arbitrary metadata, but these fields are attempts to turn a
# typed observation into its own executor/authority.  They must not be quietly
# discarded before the broker sees the request.
_FORBIDDEN_PROPOSAL_FIELDS = {
    "execute",
    "spawn",
    "promote",
    "sqlite_write",
    "model",
    "disposition",
    "invocation_id",
}

_EXACT_APPLY_PATCH_WRAPPER = re.compile(
    r'\Aconst patch = (?P<literal>"(?:\\.|[^"\\])*");\s*'
    r'text\(await tools\.apply_patch\(patch\)\);\s*\Z',
    re.DOTALL,
)

_NESTED_EXEC_COMMAND = re.compile(
    r"""tools\.exec_command\(\s*\{\s*cmd\s*:\s*
    (?P<literal>"(?:\\.|[^"\\])*")
    """,
    re.VERBOSE | re.DOTALL,
)


def _canon(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canon(value)).hexdigest()


def _is_exact_apply_patch_wrapper(value: str) -> bool:
    """Recognize the single non-executing patch wrapper used by this host."""

    match = _EXACT_APPLY_PATCH_WRAPPER.fullmatch(value)
    if match is None:
        return False
    try:
        return isinstance(json.loads(match.group("literal")), str)
    except json.JSONDecodeError:
        return False


def _nested_exec_command(value: str) -> str | None:
    """Extract the actual shell argv from this host's JS exec wrapper.

    The outer JavaScript is orchestration source, not a shell command. Only
    the literal cmd passed to tools.exec_command is process input.
    """

    match = _NESTED_EXEC_COMMAND.search(value)
    if match is None:
        return None
    try:
        command = json.loads(match.group("literal"))
    except json.JSONDecodeError:
        return None
    return command if isinstance(command, str) else None


def detect_host(payload: dict[str, Any], argv_hint: str | None = None) -> str:
    """Shim argv hint is authoritative. Payload sniffing is fallback only."""
    if argv_hint in _KNOWN_HOSTS and argv_hint != "unknown":
        return "hermes" if argv_hint == "hermes" else argv_hint
    name = str(
        payload.get("hook_event_name")
        or payload.get("hookEventName")
        or payload.get("event")
        or ""
    )
    if name == "pre_tool_call":
        return "hermes"
    extra_obj = payload.get("extra")
    extra: dict[str, Any] = extra_obj if isinstance(extra_obj, dict) else {}
    if extra.get("task_id") and name.startswith("pre_tool"):
        return "hermes"
    if payload.get("hook_event_name") in {"PreToolUse", "PostToolUse", "SessionStart"}:
        return "claude_family"
    return "unknown"


def extract_command(payload: dict[str, Any]) -> str:
    tool = str(payload.get("tool_name") or payload.get("toolName") or payload.get("tool") or "")
    tool_key = tool.lower().rsplit(".", 1)[-1]
    shell_like = tool_key in {
        "bash",
        "exec",
        "shell",
        "terminal",
        "exec_command",
        "run_terminal_command",
        "run_command",
    }
    tool_input = payload.get("tool_input")
    if tool_input is None:
        tool_input = payload.get("toolInput")
    if (
        tool_key == "exec"
        and isinstance(tool_input, str)
        and _is_exact_apply_patch_wrapper(tool_input)
    ):
        return "apply_patch"
    if tool == "functions.exec" and isinstance(tool_input, str):
        nested_command = _nested_exec_command(tool_input)
        return nested_command if nested_command is not None else tool
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "argv"):
            val = tool_input.get(key)
            if isinstance(val, list):
                return " ".join(str(x) for x in val)
            if isinstance(val, str) and val.strip():
                return val
        return ""
    # A raw edit payload is content, not an argv.  Only command tools may
    # interpret an unstructured string as process input.
    if shell_like and isinstance(tool_input, str) and tool_input.strip():
        return tool_input
    # Edit-tool payloads are source/document bytes.  Some hosts duplicate that
    # body into a top-level ``command`` field even though no process is being
    # requested.  Keep the exception closed over explicit non-executing tools.
    if tool_key in {"apply_patch", "edit", "write", "write_file"}:
        return tool
    for key in ("command", "cmd"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return tool


def _tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def _basename(token: str) -> str:
    return Path(token).name.lower()


def is_cb_owned(command: str, env: dict[str, str] | None = None) -> bool:
    """True only for argv0 / -m module / box-bound dispatch nonce.

    Substring 'constraintbox' later in the line is NOT ownership.
    Bare CB_DISPATCH=1 is NOT ownership.
    A caller-created nonce file outside a box-owned invocation directory is
    NOT ownership either.
    """
    # An explicitly supplied empty environment is a real negative control.
    # Falling back on ambient state for ``{}`` launders a surrounding box
    # nonce into probes that are meant to model an unmanaged caller.
    env = dict(os.environ) if env is None else env
    nonce_env = (env.get("CB_DISPATCH_NONCE") or "").strip()
    run_id = (env.get("CB_BOX_RUN_ID") or "").strip()
    nonce_file = env.get("CB_DISPATCH_NONCE_FILE") or ""
    if nonce_env and nonce_file and run_id:
        try:
            # A nonce is a box-issued capability, not an ambient marker.  The
            # expected path is derived from the opaque box run ID; accepting a
            # caller-chosen file path would make `CB_DISPATCH_NONCE=...` a
            # self-authorization mechanism.
            expected = (BOX_ROOT / run_id / "dispatch.nonce").resolve()
            supplied = Path(nonce_file).resolve()
            if supplied != expected or expected.parent.parent != BOX_ROOT.resolve():
                raise OSError("nonce path is not box-bound")
            disk = expected.read_text(encoding="utf-8").strip()
        except OSError:
            disk = ""
        if disk and nonce_env == disk:
            return True

    toks = _tokens(command)
    if not toks:
        return False
    names = [_basename(t) for t in toks[:6]]
    if names[0] in _CB_ARGV0_NAMES:
        return True
    if names[0] in {"python", "python3", "python3.13", "python3.11"}:
        if "-m" in toks[:6]:
            i = toks.index("-m")
            if i + 1 < len(toks) and _is_cb_module(toks[i + 1]):
                return True
    return False


def is_llm_spawn(command: str) -> bool:
    """Classify executable positions, never incidental argument text.

    This is deliberately a thin host seam. It catches a harness CLI at a
    shell command head, including after a separator. It does not inspect the
    content consumed by an otherwise admitted executable.
    """
    if not command.strip():
        return False
    try:
        # shlex discards physical newlines as whitespace. Promote them to
        # separators first so a real command on the next line is a new head.
        lexer = shlex.shlex(
            command.replace("\n", " ; "),
            posix=True,
            punctuation_chars=";&|()",
        )
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return False

    # A literal Python -c subprocess launch is itself visible process input.
    # Parse that narrow form structurally; do not scan arbitrary Python text.
    for index, token in enumerate(tokens[:-2]):
        if Path(token).name.lower() not in {"python", "python3", "python3.13"}:
            continue
        if tokens[index + 1] != "-c":
            continue
        try:
            tree = ast.parse(tokens[index + 2])
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if not isinstance(node.func.value, ast.Name) or node.func.value.id != "subprocess":
                continue
            if node.func.attr not in {"run", "Popen", "call", "check_call", "check_output"}:
                continue
            if not node.args:
                continue
            argument = node.args[0]
            executable: str | None = None
            if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                executable = shlex.split(argument.value)[0] if argument.value.strip() else None
            elif isinstance(argument, (ast.List, ast.Tuple)) and argument.elts:
                first = argument.elts[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    executable = first.value
            if executable and Path(executable).name.lower() in _SPAWN_BINS:
                return True

    command_head = True
    shell_prefixes = {"!", "if", "then", "elif", "else", "do", "while", "until"}
    wrappers = {"command", "exec", "env", "nohup"}
    assignment = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
    skip_lookup_target = False
    for index, token in enumerate(tokens):
        if token in {";", "&&", "||", "|", "&", "(", ")"}:
            command_head = True
            skip_lookup_target = False
            continue
        if not command_head:
            continue
        if skip_lookup_target:
            # ``command -v/-V NAME`` inspects shell resolution; it does not
            # launch NAME.  Do not turn harmless availability probes into
            # unmanaged-spawn refusals.  The next command segment is still
            # classified normally.
            if token.startswith("-"):
                continue
            skip_lookup_target = False
            command_head = False
            continue
        if token in shell_prefixes or assignment.match(token):
            continue
        base = Path(token).name.lower()
        if base == "command" and index + 1 < len(tokens) and tokens[index + 1] in {"-v", "-V"}:
            skip_lookup_target = True
            continue
        if base in wrappers:
            continue
        if token.startswith("-"):
            continue
        if base in _SPAWN_BINS:
            return True
        command_head = False
    return False


def classify_proposal_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    """Classify only the proposal field envelope, with no broker side effect."""
    seen = _PROPOSAL_REQUIRED_FIELDS & set(payload)
    missing = sorted(_PROPOSAL_REQUIRED_FIELDS - seen)
    forbidden = sorted(_FORBIDDEN_PROPOSAL_FIELDS & set(payload))
    if not seen:
        disposition = "NOT_A_TYPED_PROPOSAL"
    elif missing:
        disposition = "REFUSE_INCOMPLETE_PROPOSAL"
    elif forbidden:
        disposition = "REFUSE_FORBIDDEN_PROPOSAL_FIELD"
    else:
        disposition = "ADMIT_TYPED_PROPOSAL_ENVELOPE"
    return {
        "disposition": disposition,
        "present": sorted(seen),
        "missing": missing,
        "forbidden": forbidden,
        "complete": not missing and bool(seen),
    }


def _decide_unchecked(
    payload: dict[str, Any],
    *,
    env: dict[str, str] | None = None,
    parse_error: str | None = None,
) -> dict[str, Any]:
    if parse_error:
        return {
            "schema": SCHEMA,
            "allow": False,
            "disposition": "REFUSE_MALFORMED_HOOK_PAYLOAD",
            "reason_code": "REFUSE_MALFORMED_HOOK_PAYLOAD",
            "event": "unknown",
            "tool_name": None,
            "command_sha256": None,
            "command_preview": "",
            "llm_spawn": False,
            "cb_owned": False,
            "parse_error": parse_error,
            "claim_ceiling": CLAIM_CEILING,
            "out_of_scope": list(OUT_OF_SCOPE),
            "promotion_allowed": False,
            "captured_at_unix": time.time(),
            "decision_sha256": _sha256({"d": "REFUSE_MALFORMED_HOOK_PAYLOAD"}),
        }

    command = extract_command(payload)
    tool_name = payload.get("tool_name") or payload.get("toolName") or payload.get("tool")
    stripped_command = command.strip()
    exact_patch_edit = (
        tool_name == "apply_patch"
        and stripped_command.startswith("*** Begin Patch\n")
        and stripped_command.endswith("*** End Patch")
    )
    spawn = False if exact_patch_edit else is_llm_spawn(command)
    owned = is_cb_owned(command, env)
    event = str(
        payload.get("hook_event_name")
        or payload.get("hookEventName")
        or payload.get("event")
        or payload.get("type")
        or "unknown"
    )
    pre = event.lower() in _PRE_EVENTS

    if spawn and not owned and pre:
        disposition = "REFUSE_UNMANAGED_LLM_SPAWN"
        allow = False
    else:
        disposition = "ALLOW_PASSTHROUGH"
        allow = True

    quarantine = None
    envelope = classify_proposal_envelope(payload)
    proposal_fields_seen = set(envelope["present"])
    if envelope["disposition"] == "REFUSE_INCOMPLETE_PROPOSAL":
        missing = envelope["missing"]
        disposition = "REFUSE_INCOMPLETE_PROPOSAL"
        allow = False
        quarantine = {
            "ok": False,
            "reason_code": disposition,
            "detail": f"missing proposal fields: {missing}",
        }
    elif proposal_fields_seen:
        forbidden = envelope["forbidden"]
        if envelope["disposition"] == "REFUSE_FORBIDDEN_PROPOSAL_FIELD":
            disposition = "REFUSE_FORBIDDEN_PROPOSAL_FIELD"
            allow = False
            quarantine = {
                "ok": False,
                "reason_code": disposition,
                "detail": f"forbidden proposal fields: {forbidden}",
            }
            # Do not call the broker.  This is an ingress rejection, so a
            # hostile request cannot create a quarantine receipt by claiming
            # side-effect or provider authority.
            proposal_fields_seen = set()
        else:
            from .quarantine_broker import BrokerRefuse, submit

            try:
                quarantine = submit(
                    {
                        "request_id": payload["request_id"],
                        "operation_id": payload["operation_id"],
                        "probe_digest": payload["probe_digest"],
                        "from_state": payload["from_state"],
                        "to_state": payload["to_state"],
                        **({"note": payload["note"]} if payload.get("note") else {}),
                    }
                )
                disposition = quarantine["reason_code"]
                allow = False
            except BrokerRefuse as exc:
                disposition = exc.reason_code
                allow = False
                quarantine = {"ok": False, "reason_code": exc.reason_code, "detail": exc.detail}
            except OSError as exc:
                # The broker receipt is part of the decision path.  A write failure
                # must become a typed refusal, never an uncaught hook crash.
                disposition = "REFUSE_QUARANTINE_RECEIPT_WRITE_FAILED"
                allow = False
                quarantine = {
                    "ok": False,
                    "reason_code": disposition,
                    "detail": str(exc),
                }
            except Exception as exc:
                # Preserve fail-closed behaviour for an unexpected broker failure
                # without allowing the host tool to proceed on a traceback.
                disposition = "REFUSE_QUARANTINE_INTERNAL_ERROR"
                allow = False
                quarantine = {
                    "ok": False,
                    "reason_code": disposition,
                    "detail": type(exc).__name__,
                }

    body = {
        "schema": SCHEMA,
        "allow": allow,
        "disposition": disposition,
        "reason_code": disposition,
        "event": event,
        "tool_name": tool_name,
        "command_sha256": _sha256(command) if command else None,
        "command_preview": command[:240],
        "llm_spawn": spawn,
        "cb_owned": owned,
        "claim_ceiling": CLAIM_CEILING,
        "out_of_scope": list(OUT_OF_SCOPE),
        "promotion_allowed": False,
        "captured_at_unix": time.time(),
        "quarantine": quarantine,
    }
    body["decision_sha256"] = _sha256(
        {
            k: body[k]
            for k in (
                "schema",
                "disposition",
                "event",
                "command_sha256",
                "llm_spawn",
                "cb_owned",
            )
        }
    )
    return body


def decide(
    payload: dict[str, Any],
    *,
    env: dict[str, str] | None = None,
    parse_error: str | None = None,
) -> dict[str, Any]:
    """Capture/route adapter. Not a basin gate and not a CB decider."""
    return _decide_unchecked(payload, env=env, parse_error=parse_error)


def append_receipt(decision: dict[str, Any], log_path: Path | None = None) -> Path:
    path = log_path or Path(os.environ.get("CB_HOOK_ADAPTER_LOG", str(DEFAULT_LOG)))
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(decision, sort_keys=True) + "\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())
    return path


def emit_host(decision: dict[str, Any], host: str) -> tuple[str, int]:
    if decision["allow"]:
        return "", 0
    msg = (
        f"{decision['disposition']}: LLM harness spawn must be a CB-owned "
        f"argv0/-m module or carry a matching CB_DISPATCH_NONCE. "
        f"Substring markers are not ownership. This adapter does not choose models. "
        f"Out of scope: {','.join(OUT_OF_SCOPE)}."
    )
    if host == "hermes":
        return json.dumps({"action": "block", "message": msg}), 2
    if host == "grok":
        return json.dumps({"decision": "deny", "reason": msg}), 0
    if host in {"claude", "codex"}:
        # Claude and Codex both require the typed PreToolUse denial wire. A
        # top-level decision:block is not a portable deny response for these
        # host engines; a successful hook process carries the decision.
        return (
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": msg,
                    }
                }
            ),
            0,
        )
    return json.dumps({"decision": "block", "reason": msg}), 2


def run_stdio(host_hint: str | None = None) -> int:
    raw = sys.stdin.read()
    parse_error = None
    payload: dict[str, Any]
    if not raw.strip():
        parse_error = "empty_stdin"
        payload = {}
    else:
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError:
            parse_error = "json_decode"
            loaded = {}
        if not isinstance(loaded, dict):
            parse_error = parse_error or "non_object"
            payload = {}
        else:
            payload = loaded

    host = detect_host(payload, host_hint)
    decision = decide(payload, parse_error=parse_error)
    decision["host"] = host
    try:
        log = append_receipt(decision)
        decision["receipt_path"] = str(log)
        decision["receipt_ok"] = True
    except OSError as exc:
        # Receipt failure cannot produce an allow.
        decision["allow"] = False
        decision["disposition"] = "REFUSE_RECEIPT_WRITE_FAILED"
        decision["reason_code"] = "REFUSE_RECEIPT_WRITE_FAILED"
        decision["receipt_ok"] = False
        decision["receipt_error"] = str(exc)

    out, code = emit_host(decision, host)
    if out:
        sys.stdout.write(out + "\n")
    return code


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    hint = None
    if args and args[0] in _KNOWN_HOSTS:
        hint = args[0]
    return run_stdio(hint)


if __name__ == "__main__":
    raise SystemExit(main())
