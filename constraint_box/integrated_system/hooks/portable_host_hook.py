#!/usr/bin/env python3
"""Portable, host-neutral ConstraintBox hook seam.

This file is deliberately self-contained.  It is launched by an explicitly
declared Light interpreter with ``-I``; it never imports the checkout, a
provider adapter, or a host's Python module.  Its only authority is the small
host seam needed to capture an event and remove unmanaged process-launch
authority before the host tool runs.

The adapter does not evaluate an operation, select a provider, or mint a CB
disposition.  A returned envelope is an observation/relay packet.  A refusal
means only that the host's requested process launch was not demonstrably
owned by ConstraintBox.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import fcntl
import hashlib
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "constraintbox.integrated.host-hook.v1"
INSTALL_SCHEMA = "constraintbox.integrated.host-hook-binding.v1"
CLAIM_CEILING = (
    "capture_relay_and_unmanaged_launch_seam_only;"
    "not_semantic_cb_decision;not_provider_selection;"
    "bounded_literal_process_shapes_only;unknown_dynamic_code_unclassified;"
    "promotion_allowed_false"
)

HOSTS = ("codex", "claude", "grok", "hermes")
_HOST_ALIASES = {
    "claude_code": "claude",
    "claude-code": "claude",
    "grok_cli": "grok",
    "grok-cli": "grok",
}

SESSION_BOUND = "SESSION_BOUND"
RELAYED = "RELAYED"
CAPTURED = "CAPTURED"
CANCELLED = "CANCELLED"
BYPASS_OBSERVED = "BYPASS_OBSERVED"

SESSION_START = "session_start"
PRE_TOOL = "pre_tool"
POST_TOOL = "post_tool"
CANCEL = "cancel"
UNKNOWN = "unknown"

_SPAWN_BINS = frozenset(HOSTS)
_SHELL_WRAPPERS = frozenset(
    {"command", "env", "exec", "nohup", "cb", "portable_host_hook.py", "cb_light_cli.py"}
)
_SHELL_BINS = frozenset({"sh", "bash", "zsh", "dash", "ksh"})
_SHELL_PREFIXES = frozenset({"!", "if", "then", "elif", "else", "do", "while", "until"})
_SEPARATORS = frozenset({";", "&&", "||", "|", "&", "(", ")"})
_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_KNOWN_MODULE_INVOCATION = re.compile(r"^(?:python|python3|python3\.[0-9]+)$", re.I)
_MAX_NESTED_CODE_DEPTH = 3
_LEASE_DIRS = (Path("state") / "leases", Path("receipts") / "box", Path("runs"))
_CANONICAL_EVENT_LOG_RELATIVE = Path("integrated_system") / "runs" / "hook-events.jsonl"


def canonical_json_bytes(value: Any) -> bytes:
    """Return the stable bytes used for an envelope digest."""

    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_value(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def sha256_file(path: str | Path) -> str:
    """Hash an already-bound source/interpreter file without importing it."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_native_interpreter(path: str | Path) -> bool:
    """Reject a shell/script shim masquerading as the Light executable."""

    try:
        with Path(path).resolve().open("rb") as stream:
            magic = stream.read(4)
    except OSError:
        return False
    # macOS Mach-O (32/64-bit, endian variants) and Unix ELF are the supported
    # native executable families for this macOS candidate/runtime fixture.
    return magic in {
        b"\xfe\xed\xfa\xce",
        b"\xce\xfa\xed\xfe",
        b"\xfe\xed\xfa\xcf",
        b"\xcf\xfa\xed\xfe",
        b"\x7fELF",
    }


def _light_venv_binding(
    light: Path,
    root: Path,
    *,
    raw_root: Path | None = None,
) -> dict[str, Any]:
    """Validate a lexical product venv and its resolved native entrypoint."""

    if _has_path_traversal(light):
        return {"status": "HOLD", "reason_code": "HOLD_CB_LIGHT_INTERPRETER_PATH_TRAVERSAL"}
    lexical_root = _lexical_absolute(root)
    raw_light = _lexical_absolute(light)
    if raw_root is not None:
        raw_root_abs = _lexical_absolute(raw_root)
    else:
        raw_root_abs = lexical_root
    try:
        relative_light = raw_light.relative_to(raw_root_abs)
        lexical_light = lexical_root / relative_light
    except ValueError:
        lexical_light = _canonical_member_path(light)
    if not lexical_light.is_file() or not os.access(lexical_light, os.X_OK):
        return {"status": "HOLD", "reason_code": "HOLD_CB_LIGHT_INTERPRETER_MISSING"}
    if not _lexically_under(lexical_light, lexical_root):
        return {
            "status": "HOLD",
            "reason_code": "HOLD_CB_LIGHT_INTERPRETER_OUTSIDE_PRODUCT",
        }
    if lexical_light.parent.name != "bin":
        return {
            "status": "HOLD",
            "reason_code": "HOLD_CB_LIGHT_INTERPRETER_NOT_VENV_ENTRYPOINT",
        }
    venv_root = lexical_light.parent.parent
    if venv_root == lexical_root or not _lexically_under(venv_root, lexical_root):
        return {"status": "HOLD", "reason_code": "HOLD_CB_LIGHT_VENV_OUTSIDE_PRODUCT"}
    if not _under(venv_root, lexical_root):
        return {"status": "HOLD", "reason_code": "HOLD_CB_LIGHT_VENV_ESCAPED"}
    cfg = venv_root / "pyvenv.cfg"
    if _has_path_traversal(cfg) or cfg.is_symlink() or not cfg.is_file():
        return {
            "status": "HOLD",
            "reason_code": "HOLD_CB_LIGHT_PYVENV_CONFIG_INVALID",
        }
    if not _lexically_under(cfg, lexical_root) or not _under(cfg, lexical_root):
        return {
            "status": "HOLD",
            "reason_code": "HOLD_CB_LIGHT_PYVENV_CONFIG_ESCAPED",
        }
    resolved = lexical_light.resolve()
    if not is_native_interpreter(resolved):
        return {
            "status": "HOLD",
            "reason_code": "HOLD_CB_LIGHT_INTERPRETER_NOT_NATIVE",
        }
    try:
        cfg_digest = sha256_file(cfg)
        target_digest = sha256_file(resolved)
    except OSError:
        return {"status": "HOLD", "reason_code": "HOLD_CB_LIGHT_BINDING_HASH_UNREADABLE"}
    return {
        "status": "PASS",
        "venv_root": str(venv_root),
        "venv_root_resolved": str(venv_root.resolve()),
        "pyvenv_cfg": str(cfg),
        "pyvenv_cfg_resolved": str(cfg.resolve()),
        "pyvenv_cfg_sha256": cfg_digest,
        "light_interpreter_lexical": str(lexical_light),
        "light_interpreter_resolved": str(resolved),
        "light_interpreter_sha256": target_digest,
        "light_interpreter_target_sha256": target_digest,
        "light_interpreter_is_symlink": lexical_light.is_symlink(),
    }


def _text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _first_string(objects: tuple[Mapping[str, Any], ...], keys: tuple[str, ...]) -> str | None:
    for obj in objects:
        for key in keys:
            found = _text(obj.get(key))
            if found is not None:
                return found
    return None


def _nested_objects(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    objects: list[Mapping[str, Any]] = [payload]
    for key in ("extra", "context", "metadata", "args", "input", "tool_input", "toolInput"):
        nested = _mapping(payload.get(key))
        if nested is not None:
            objects.append(nested)
    return tuple(objects)


def normalize_host(host: str | None) -> str:
    """Normalize a shim hint without guessing from a filesystem path."""

    value = (host or "").strip().lower()
    value = _HOST_ALIASES.get(value, value)
    return value if value in HOSTS else "unknown"


def infer_host(payload: Mapping[str, Any], host_hint: str | None = None) -> str:
    """Use the explicit shim host first; payload sniffing is conservative."""

    hinted = normalize_host(host_hint)
    if hinted != "unknown":
        return hinted
    supplied = _first_string(_nested_objects(payload), ("host", "host_name", "hostName"))
    supplied_host = normalize_host(supplied)
    if supplied_host != "unknown":
        return supplied_host
    event = _first_string(
        (payload,),
        ("event", "hook_event_name", "hookEventName", "event_type", "eventType", "type"),
    )
    compact = _compact_event(event)
    if compact in {"pretoolcall", "posttoolcall", "onsessionstart", "onstop"}:
        extra = _mapping(payload.get("extra"))
        if extra is not None and _text(extra.get("task_id")):
            return "hermes"
    # CamelCase hook fields are the common Claude-family wire shape.  The
    # adapter only uses this as a fallback; a shim hint remains authoritative.
    if "hookEventName" in payload:
        return "claude"
    return "unknown"


def _compact_event(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def event_type(payload: Mapping[str, Any]) -> tuple[str, str | None]:
    """Map host spellings into neutral lifecycle verbs, never policy."""

    raw = _first_string(
        (payload,),
        ("event", "hook_event_name", "hookEventName", "event_type", "eventType", "type"),
    )
    compact = _compact_event(raw)
    if compact in {"onsessionend", "sessionend", "onsessionended"}:
        extra = _mapping(payload.get("extra"))
        if extra is not None and extra.get("interrupted") is True:
            return CANCEL, "hermes_interrupted_session_end"

    cancel_flags = (
        "cancelled",
        "canceled",
        "cancel",
        "cancel_requested",
        "stop_requested",
        "abort_requested",
        "interrupted",
    )
    for obj in _nested_objects(payload):
        for key in cancel_flags:
            if obj.get(key) is True:
                return CANCEL, "host_cancel_flag"

    if compact in {"sessionstart", "sessionstarted", "onsessionstart", "bind", "startup", "resume"}:
        return SESSION_START, None
    if compact in {
        "pretooluse",
        "pretoolcall",
        "preexecution",
        "beforetool",
        "beforeexecution",
        "relay",
    }:
        return PRE_TOOL, None
    if compact in {
        "posttooluse",
        "posttoolcall",
        "postexecution",
        "aftertool",
        "afterexecution",
        "result",
        "capture",
    }:
        return POST_TOOL, None
    if compact in {
        "stop",
        "onstop",
        "cancel",
        "cancelled",
        "canceled",
        "abort",
        "abortrequested",
        "cancellation",
    }:
        return CANCEL, None
    return UNKNOWN, "unknown_or_missing_event"


def _identifiers(payload: Mapping[str, Any]) -> tuple[str | None, str | None, str | None]:
    objects = _nested_objects(payload)
    session = _first_string(
        objects,
        (
            "session_id",
            "sessionId",
            "conversation_id",
            "conversationId",
            "thread_id",
            "threadId",
            "task_id",
        ),
    )
    invocation = _first_string(
        objects,
        (
            "tool_use_id",
            "toolUseId",
            "tool_call_id",
            "toolCallId",
            "call_id",
            "callId",
            "invocation_id",
            "invocationId",
        ),
    )
    tool = _first_string(objects, ("tool_name", "toolName", "tool"))
    return session, invocation, tool


def _command_from_value(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    if isinstance(value, (list, tuple)) and value:
        return " ".join(str(item) for item in value)
    if isinstance(value, Mapping):
        for key in ("command", "cmd", "argv"):
            result = _command_from_value(value.get(key))
            if result is not None:
                return result
    return None


def extract_command(payload: Mapping[str, Any]) -> str:
    """Extract process input only from command-shaped fields.

    Edit/document bodies are not interpreted as process input.  This keeps a
    host's content payload from becoming an accidental spawn refusal.
    """

    tool = (_first_string(_nested_objects(payload), ("tool_name", "toolName", "tool")) or "").lower()
    tool_key = tool.rsplit(".", 1)[-1]
    edit_like = {"apply_patch", "edit", "write", "write_file", "notebookedit"}
    if tool_key not in edit_like:
        for key in ("command", "cmd", "argv"):
            result = _command_from_value(payload.get(key))
            if result is not None:
                return result
    tool_input = payload.get("tool_input")
    if tool_input is None:
        tool_input = payload.get("toolInput")
    if tool_key not in edit_like:
        if isinstance(tool_input, (Mapping, list, tuple)):
            result = _command_from_value(tool_input)
            if result is not None:
                return result
        elif tool_key in {"bash", "exec", "shell", "terminal", "command", "run_command", "run_terminal_command"}:
            raw = _text(tool_input)
            if raw is not None:
                return raw
    nested_args = _mapping(payload.get("args"))
    if nested_args is not None:
        result = _command_from_value(nested_args)
        if result is not None:
            return result
    # A raw string is process input only for a shell-like tool.  Named edit
    # tools are closed over as content, even when their body contains host
    # command words.
    if tool_key not in edit_like:
        if tool_key in {"bash", "exec", "shell", "terminal", "command", "run_command", "run_terminal_command"}:
            raw = _text(tool_input)
            if raw is not None:
                return raw
    return ""


def _tokens(command: str) -> list[str]:
    try:
        lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=";&|()")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except (TypeError, ValueError):
        try:
            return shlex.split(command, posix=True)
        except ValueError:
            return command.split()


def _basename(token: str) -> str:
    return Path(token).name.lower()


def _ast_string(value: ast.AST | None) -> str | None:
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    return None


def _ast_executable(value: ast.AST | None) -> str | None:
    """Extract a literal executable from a bounded Python call shape."""

    direct = _ast_string(value)
    if direct is not None:
        pieces = _tokens(direct)
        return pieces[0] if pieces else None
    if isinstance(value, (ast.List, ast.Tuple)) and value.elts:
        return _ast_string(value.elts[0])
    return None


def _call_argument(node: ast.Call, positional: int, *keyword_names: str) -> ast.AST | None:
    if len(node.args) > positional:
        return node.args[positional]
    names = set(keyword_names)
    for keyword in node.keywords:
        if keyword.arg in names:
            return keyword.value
    return None


def _python_call_spawns(node: ast.Call, depth: int) -> bool:
    if depth > _MAX_NESTED_CODE_DEPTH or not isinstance(node.func, ast.Attribute):
        return False
    owner = node.func.value
    if not isinstance(owner, ast.Name) or (not node.args and not node.keywords):
        return False
    owner_name = owner.id
    method = node.func.attr
    executable: str | None = None
    nested_command: str | None = None
    if owner_name == "subprocess" and method in {
        "run",
        "Popen",
        "call",
        "check_call",
        "check_output",
    }:
        executable = _ast_executable(_call_argument(node, 0, "args"))
    elif owner_name == "os" and method == "system":
        nested_command = _ast_string(_call_argument(node, 0, "command"))
    elif owner_name == "os" and method.startswith("exec"):
        executable = _ast_executable(_call_argument(node, 0, "path", "file"))
    elif owner_name == "asyncio" and method.startswith("create_subprocess"):
        if method == "create_subprocess_shell":
            nested_command = _ast_string(_call_argument(node, 0, "cmd"))
        else:
            executable = _ast_executable(_call_argument(node, 0, "program"))
    if executable is not None and _basename(executable) in _SPAWN_BINS:
        return True
    return nested_command is not None and _command_has_unmanaged_spawn(nested_command, depth + 1)


def _python_subprocess_spawns(tokens: list[str], depth: int = 0) -> bool:
    """Inspect only literal Python ``-c`` process-call forms.

    Dynamic values are intentionally not guessed.  The bounded static seam
    covers subprocess, os.system/os.exec*, and asyncio subprocess calls;
    arbitrary generated code remains outside this adapter's claim ceiling.
    """

    if depth > _MAX_NESTED_CODE_DEPTH:
        return False
    for index, token in enumerate(tokens[:-2]):
        if not _KNOWN_MODULE_INVOCATION.fullmatch(_basename(token)):
            continue
        if tokens[index + 1] != "-c":
            continue
        try:
            tree = ast.parse(tokens[index + 2])
        except SyntaxError:
            continue
        if any(_python_call_spawns(node, depth) for node in ast.walk(tree) if isinstance(node, ast.Call)):
            return True
    return False


def _shell_wrapper_command(tokens: list[str], index: int) -> str | None:
    """Return a literal command passed to ``sh/bash/zsh -c/-lc``."""

    if _basename(tokens[index]) not in _SHELL_BINS:
        return None
    cursor = index + 1
    while cursor < len(tokens) and cursor < index + 6:
        token = tokens[cursor]
        if token in {"-c", "-lc", "--command", "--command=", "-cl"}:
            if token == "--command=":
                return None
            return tokens[cursor + 1] if cursor + 1 < len(tokens) else None
        if token == "--":
            cursor += 1
            continue
        if token.startswith("-"):
            cursor += 1
            continue
        # The first non-option is a script path, not a command string.
        return None
    return None


def _cb_module_provider_arg(tokens: list[str], index: int) -> bool:
    """Treat a provider executable after a CB module as a launch request."""

    if not _KNOWN_MODULE_INVOCATION.fullmatch(_basename(tokens[index])):
        return False
    if index + 2 >= len(tokens) or tokens[index + 1] != "-m":
        return False
    module = tokens[index + 2]
    if not module.startswith("constraintbox"):
        return False
    module_parts = re.split(r"[._-]+", module.lower())
    if any(part in _SPAWN_BINS for part in module_parts):
        return True
    for token in tokens[index + 3 : index + 12]:
        if token in _SEPARATORS:
            break
        token_base = _basename(token)
        if token_base in _SPAWN_BINS:
            return True
        if "=" in token and _basename(token.rsplit("=", 1)[-1]) in _SPAWN_BINS:
            return True
    return False


def _command_has_unmanaged_spawn(command: str, depth: int = 0) -> bool:
    if depth > _MAX_NESTED_CODE_DEPTH or not command.strip():
        return False
    tokens = _tokens(command)
    if not tokens:
        return False
    if _python_subprocess_spawns(tokens, depth):
        return True

    command_head = True
    skip_lookup_target = False
    for index, token in enumerate(tokens):
        if token in _SEPARATORS:
            command_head = True
            skip_lookup_target = False
            continue
        if not command_head:
            continue
        if skip_lookup_target:
            if token.startswith("-"):
                continue
            skip_lookup_target = False
            command_head = False
            continue
        if token in _SHELL_PREFIXES or _ASSIGNMENT.match(token):
            continue
        if token == "command" and index + 1 < len(tokens) and tokens[index + 1] in {"-v", "-V"}:
            skip_lookup_target = True
            continue
        if _cb_module_provider_arg(tokens, index):
            return True
        nested = _shell_wrapper_command(tokens, index)
        if nested is not None and _command_has_unmanaged_spawn(nested, depth + 1):
            return True
        if token in _SHELL_WRAPPERS or _basename(token) in _SHELL_BINS:
            continue
        if token.startswith("-"):
            continue
        if _basename(token) in _SPAWN_BINS:
            return True
        command_head = False
    return False


def is_unmanaged_spawn(command: str) -> bool:
    """Classify bounded literal host launches, including common wrappers."""

    return _command_has_unmanaged_spawn(command)


def _safe_run_id(value: str) -> str | None:
    if not value or value in {".", ".."} or "/" in value or "\\" in value:
        return None
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,128}", value):
        return None
    return value


def _under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _has_path_traversal(path: str | Path) -> bool:
    return ".." in Path(str(path)).parts


def _lexical_absolute(path: str | Path) -> Path:
    return Path(os.path.abspath(os.path.expanduser(str(path))))


def _canonical_member_path(path: str | Path) -> Path:
    """Resolve parent aliases while retaining the final entrypoint name."""

    lexical = _lexical_absolute(path)
    return lexical.parent.resolve(strict=False) / lexical.name


def _lexically_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def canonical_event_log(product_root: str | Path) -> Path:
    return _lexical_absolute(product_root) / _CANONICAL_EVENT_LOG_RELATIVE


def _canonical_log_custody(
    root: Path,
    path: Path,
    *,
    raw_root: Path | None = None,
    raw_path: Path | None = None,
) -> str | None:
    """Check every canonical log component without following redirects."""

    lexical_root = _lexical_absolute(root)
    lexical_path = _lexical_absolute(path)
    if lexical_root.is_symlink():
        return "HOLD_CB_HOOK_EVENT_ROOT_SYMLINK"
    if not _lexically_under(lexical_path, lexical_root):
        return "HOLD_CB_HOOK_EVENT_LOG_OUTSIDE_PRODUCT"
    if raw_root is not None and raw_path is not None:
        raw_root_abs = _lexical_absolute(raw_root)
        raw_path_abs = _lexical_absolute(raw_path)
        try:
            raw_relative = raw_path_abs.relative_to(raw_root_abs)
        except ValueError:
            return "HOLD_CB_HOOK_EVENT_OUTSIDE_PRODUCT"
        if raw_relative != _CANONICAL_EVENT_LOG_RELATIVE:
            return "HOLD_CB_HOOK_EVENT_LOG_NONCANONICAL"
        raw_current = raw_root_abs
        for component in _CANONICAL_EVENT_LOG_RELATIVE.parts[:-1]:
            raw_current = raw_current / component
            if raw_current.is_symlink():
                return "HOLD_CB_HOOK_EVENT_PARENT_SYMLINK"
            if raw_current.exists() and not raw_current.is_dir():
                return "HOLD_CB_HOOK_EVENT_PARENT_NOT_DIRECTORY"
        if raw_path_abs.is_symlink():
            return "HOLD_CB_HOOK_EVENT_LOG_SYMLINK"
        if raw_path_abs.exists() and not raw_path_abs.is_file():
            return "HOLD_CB_HOOK_EVENT_LOG_NOT_REGULAR"
    current = lexical_root
    for component in _CANONICAL_EVENT_LOG_RELATIVE.parts[:-1]:
        current = current / component
        if current.is_symlink():
            return "HOLD_CB_HOOK_EVENT_PARENT_SYMLINK"
        if current.exists() and not current.is_dir():
            return "HOLD_CB_HOOK_EVENT_PARENT_NOT_DIRECTORY"
    if lexical_path.is_symlink():
        return "HOLD_CB_HOOK_EVENT_LOG_SYMLINK"
    if lexical_path.exists() and not lexical_path.is_file():
        return "HOLD_CB_HOOK_EVENT_LOG_NOT_REGULAR"
    if lexical_path.exists() and os.lstat(lexical_path).st_nlink != 1:
        return "HOLD_CB_HOOK_EVENT_LOG_MULTILINK"
    return None


def _lease_owned(env: Mapping[str, str]) -> bool:
    nonce = (env.get("CB_DISPATCH_NONCE") or "").strip()
    nonce_file = (env.get("CB_DISPATCH_NONCE_FILE") or "").strip()
    run_id = _safe_run_id((env.get("CB_BOX_RUN_ID") or "").strip())
    product = (env.get("CB_PRODUCT_ROOT") or "").strip()
    if not nonce or not nonce_file or not run_id or not product:
        return False
    root = Path(product).expanduser().absolute()
    candidate = Path(nonce_file).expanduser().absolute()
    if not _under(candidate, root) or candidate.name != "dispatch.nonce" or candidate.parent.name != run_id:
        return False
    try:
        candidate_relative = candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    if not any(
        len(candidate_relative.parts) == len(prefix.parts) + 2
        and candidate_relative.parts[: len(prefix.parts)] == prefix.parts
        and candidate_relative.parts[-2:] == (run_id, "dispatch.nonce")
        for prefix in _LEASE_DIRS
    ):
        return False
    try:
        return candidate.read_text(encoding="utf-8").strip() == nonce
    except (OSError, UnicodeError):
        return False


def is_cb_owned(command: str, env: Mapping[str, str] | None = None) -> bool:
    """Recognize only a product-confined, nonce-backed dispatch lease.

    Executable names, script names, module names, and ambient marker
    variables are intentionally never ownership evidence.  A CB command that
    is not a provider spawn can pass as ordinary host traffic; provider
    authority requires the lease path and on-disk nonce to agree.
    """

    # An explicitly empty map is a negative control, not ambient inheritance.
    effective = dict(os.environ) if env is None else dict(env)
    return _lease_owned(effective)


def _proposal(payload: Mapping[str, Any]) -> Any:
    for key in ("typed_proposal", "typedProposal", "proposal"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            return value
    return None


def normalize_event(
    payload: Mapping[str, Any] | Any,
    *,
    host_hint: str | None = None,
    source_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Build one neutral envelope from any of the four host shapes."""

    if not isinstance(payload, Mapping):
        raw = source_bytes if source_bytes is not None else repr(payload).encode("utf-8")
        return {
            "schema": SCHEMA,
            "host": normalize_host(host_hint),
            "event_type": UNKNOWN,
            "source_event": None,
            "session_id": None,
            "invocation_id": None,
            "tool_name": None,
            "command_sha256": None,
            "payload_sha256": sha256_bytes(raw),
            "typed_proposal": None,
            "status": BYPASS_OBSERVED,
            "disposition": "REFUSE_NON_OBJECT_PAYLOAD",
            "allow": False,
            "authority_removed": True,
            "cancelled": False,
            "normalization_note": "non_object_payload",
            "claim_ceiling": CLAIM_CEILING,
            "promotion_allowed": False,
        }

    raw_event = _first_string(
        (payload,),
        ("event", "hook_event_name", "hookEventName", "event_type", "eventType", "type"),
    )
    kind, note = event_type(payload)
    session, invocation, tool = _identifiers(payload)
    command = extract_command(payload)
    proposal = _proposal(payload)
    if kind == SESSION_START:
        status = SESSION_BOUND
    elif kind == PRE_TOOL:
        status = RELAYED
    elif kind == POST_TOOL:
        status = CAPTURED
    elif kind == CANCEL:
        status = CANCELLED
    else:
        status = BYPASS_OBSERVED
    return {
        "schema": SCHEMA,
        "host": infer_host(payload, host_hint),
        "event_type": kind,
        "source_event": raw_event,
        "session_id": session,
        "invocation_id": invocation,
        "tool_name": tool,
        "command_sha256": sha256_value(command) if command else None,
        "payload_sha256": sha256_bytes(source_bytes) if source_bytes is not None else sha256_value(dict(payload)),
        "typed_proposal": proposal,
        "status": status,
        "disposition": "OBSERVE_ONLY",
        "allow": True,
        "authority_removed": False,
        "cancelled": kind == CANCEL,
        "normalization_note": note,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }


def process_event(
    payload: Mapping[str, Any] | Any,
    *,
    host_hint: str | None = None,
    env: Mapping[str, str] | None = None,
    product_root: str | Path | None = None,
    source_bytes: bytes | None = None,
    parse_error: str | None = None,
) -> dict[str, Any]:
    """Capture/relay one event and strip only unmanaged launch authority."""

    if parse_error:
        raw = source_bytes if source_bytes is not None else b""
        return {
            "schema": SCHEMA,
            "host": normalize_host(host_hint),
            "event_type": UNKNOWN,
            "source_event": None,
            "session_id": None,
            "invocation_id": None,
            "tool_name": None,
            "command_sha256": None,
            "payload_sha256": sha256_bytes(raw),
            "typed_proposal": None,
            "status": BYPASS_OBSERVED,
            "disposition": "REFUSE_MALFORMED_HOOK_PAYLOAD",
            "allow": False,
            "authority_removed": True,
            "cancelled": False,
            "parse_error": parse_error,
            "claim_ceiling": CLAIM_CEILING,
            "promotion_allowed": False,
        }

    effective_env = dict(os.environ) if env is None else dict(env)
    if product_root is not None:
        effective_env["CB_PRODUCT_ROOT"] = str(Path(product_root).expanduser().resolve())
    envelope = normalize_event(payload, host_hint=host_hint, source_bytes=source_bytes)
    if envelope["event_type"] == CANCEL:
        envelope.update(
            {
                "disposition": "CANCELLED_NO_AUTHORITY",
                "allow": False,
                "authority_removed": True,
                "cancelled": True,
            }
        )
        return envelope
    command = extract_command(payload) if isinstance(payload, Mapping) else ""
    command_shaped = bool(command.strip())
    if envelope["event_type"] in {PRE_TOOL, UNKNOWN} and command_shaped:
        unmanaged = is_unmanaged_spawn(command)
        owned = is_cb_owned(command, effective_env) if unmanaged else False
        envelope["llm_spawn"] = unmanaged
        envelope["cb_owned"] = owned
        if unmanaged and not owned:
            envelope.update(
                {
                    "disposition": "REFUSE_UNMANAGED_LLM_SPAWN",
                    "allow": False,
                    "authority_removed": True,
                }
            )
            return envelope
    else:
        envelope["llm_spawn"] = False
        envelope["cb_owned"] = False

    if envelope.get("typed_proposal") is not None:
        envelope["disposition"] = "RELAY_TYPED_PROPOSAL"
        envelope["relay_only"] = True
    elif envelope["event_type"] == UNKNOWN:
        envelope["disposition"] = "BYPASS_OBSERVED"
        envelope["authority_removed"] = True
    else:
        envelope["disposition"] = "ALLOW_PASSTHROUGH"
    return envelope


# Stable descriptive aliases keep the fixture seam easy to consume without
# introducing a second implementation or a package import requirement.
normalize_host_payload = normalize_event
is_llm_spawn = is_unmanaged_spawn
decide = process_event


def binding_status(
    product_root: str | Path | None,
    light_interpreter: str | Path | None,
    event_log: str | Path | None = None,
    hook_source: str | Path | None = None,
) -> dict[str, Any]:
    """Validate explicit product, Light, source, and event-log bindings.

    Both executable and hook source are resolved before admission.  This
    intentionally rejects a symlink to an interpreter outside the product and
    rejects running a copied hook from outside the declared product root.
    """

    root_value = str(product_root or "").strip()
    light_value = str(light_interpreter or "").strip()
    if not root_value:
        return {"status": "HOLD", "reason_code": "HOLD_CB_PRODUCT_ROOT_REQUIRED"}
    if _has_path_traversal(root_value):
        return {"status": "HOLD", "reason_code": "HOLD_CB_PRODUCT_ROOT_PATH_TRAVERSAL"}
    root_input = Path(root_value).expanduser()
    if not root_input.is_absolute():
        return {"status": "HOLD", "reason_code": "HOLD_BINDING_PATHS_MUST_BE_ABSOLUTE"}
    root = root_input.resolve(strict=False)
    if not root.is_dir():
        return {"status": "HOLD", "reason_code": "HOLD_CB_PRODUCT_ROOT_MISSING", "product_root": str(root)}

    expected_log = canonical_event_log(root)
    log_value = str(event_log or "").strip()
    raw_log = Path(log_value).expanduser() if log_value else expected_log
    if _has_path_traversal(raw_log) or not raw_log.is_absolute():
        return {"status": "HOLD", "reason_code": "HOLD_CB_HOOK_EVENT_LOG_PATH_TRAVERSAL"}
    if raw_log.is_symlink():
        return {
            "status": "HOLD",
            "reason_code": "HOLD_CB_HOOK_EVENT_LOG_SYMLINK",
            "event_log": str(raw_log),
            "product_root": str(root),
        }
    log = _canonical_member_path(raw_log)
    if _lexical_absolute(log) != _lexical_absolute(expected_log):
        return {
            "status": "HOLD",
            "reason_code": "HOLD_CB_HOOK_EVENT_LOG_NONCANONICAL",
            "event_log": str(log),
            "product_root": str(root),
        }
    log_custody = _canonical_log_custody(root, expected_log, raw_root=root_input, raw_path=raw_log)
    if log_custody is not None:
        return {
            "status": "HOLD",
            "reason_code": log_custody,
            "event_log": str(expected_log),
            "product_root": str(root),
        }

    raw_source = Path(hook_source or __file__).expanduser()
    if _has_path_traversal(raw_source) or not raw_source.is_absolute():
        return {"status": "HOLD", "reason_code": "HOLD_CB_HOOK_SOURCE_PATH_TRAVERSAL"}
    source = _canonical_member_path(raw_source)
    if raw_source.is_symlink():
        return {
            "status": "HOLD",
            "reason_code": "HOLD_CB_HOOK_SOURCE_SYMLINK",
            "hook_source": str(raw_source),
        }
    if not source.is_file():
        return {
            "status": "HOLD",
            "reason_code": "HOLD_CB_HOOK_SOURCE_MISSING",
            "hook_source": str(source),
        }
    if not _lexically_under(_lexical_absolute(source), _lexical_absolute(root)):
        return {
            "status": "HOLD",
            "reason_code": "HOLD_CB_HOOK_SOURCE_OUTSIDE_PRODUCT",
            "hook_source": str(source),
            "product_root": str(root),
        }
    if not _under(source, root):
        return {
            "status": "HOLD",
            "reason_code": "HOLD_CB_HOOK_SOURCE_ESCAPED",
            "hook_source": str(source),
            "product_root": str(root),
        }
    try:
        source_digest = sha256_file(source.resolve())
    except OSError:
        return {
            "status": "HOLD",
            "reason_code": "HOLD_BINDING_HASH_UNREADABLE",
            "hook_source": str(source),
        }

    light = Path(light_value).expanduser() if light_value else None
    base: dict[str, Any] = {
        "product_root": str(root.resolve()),
        "light_interpreter": str(_lexical_absolute(light)) if light is not None else None,
        "light_interpreter_sha256": None,
        "interpreter_sha256": None,
        "hook_source": str(source.resolve()),
        "hook_source_sha256": source_digest,
        "source_sha256": source_digest,
        "event_log": str(expected_log),
        # A Light hold still has enough trusted product/source/log binding to
        # capture the refusal through the fixed bootstrap interpreter.
        "capture_ready": True,
        "capability_valid": False,
    }
    if light is None:
        return {
            "status": "HOLD",
            "reason_code": "HOLD_CB_LIGHT_INTERPRETER_REQUIRED",
            **base,
        }
    light_binding = _light_venv_binding(light, root, raw_root=root_input)
    if light_binding["status"] != "PASS":
        return {
            "status": "HOLD",
            "reason_code": light_binding["reason_code"],
            **base,
            **{key: value for key, value in light_binding.items() if key != "status"},
        }
    return {
        "status": "PASS",
        "reason_code": "BOUND_TO_EXPLICIT_LIGHT_VENV",
        **base,
        **{key: value for key, value in light_binding.items() if key != "status"},
        "capability_valid": True,
        "capture_ready": True,
        "interpreter_sha256": light_binding["light_interpreter_sha256"],
    }


def append_event_log(
    envelope: Mapping[str, Any],
    *,
    event_log: str | Path,
    product_root: str | Path,
) -> dict[str, Any]:
    """Append one canonical, fsynced event under the product root.

    The log itself is the lock.  A caller-controlled path outside the bound
    product is rejected before any directory or file operation.  A failed
    append raises and therefore cannot be converted into an allow.
    """

    raw_root = Path(product_root).expanduser()
    root = raw_root.resolve(strict=False)
    raw_path = Path(event_log).expanduser()
    path = _canonical_member_path(raw_path)
    expected = canonical_event_log(root)
    if _has_path_traversal(event_log) or path != expected:
        raise OSError("event log is not the canonical runtime log")
    if not root.is_dir() or not _under(path, root):
        raise OSError("event log is outside the product root")
    custody = _canonical_log_custody(root, expected, raw_root=raw_root, raw_path=raw_path)
    if custody is not None:
        raise OSError(custody)
    for parent in (root / "integrated_system", root / "integrated_system" / "runs"):
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            raise OSError("event log parent is redirected")
        if not parent.exists():
            parent.mkdir()
        custody = _canonical_log_custody(root, expected, raw_root=raw_root, raw_path=raw_path)
        if custody is not None:
            raise OSError(custody)
    record = dict(envelope)
    binding = record.get("binding")
    if isinstance(binding, Mapping):
        for key in (
            "light_interpreter_sha256",
            "hook_source_sha256",
            "interpreter_sha256",
            "source_sha256",
        ):
            if key in binding:
                record[key] = binding[key]
    record["event_sha256"] = sha256_value(record)
    line = canonical_json_bytes(record) + b"\n"
    flags = os.O_RDWR | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "a+b") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            stream.seek(0, os.SEEK_END)
            stream.write(line)
            stream.flush()
            os.fsync(stream.fileno())
        finally:
            with contextlib.suppress(OSError):
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    return record


def _refusal_reason(envelope: Mapping[str, Any]) -> str:
    return (
        f"{envelope.get('disposition', 'REFUSE')};status={envelope.get('status')};"
        "portable hook strips unmanaged authority only;"
        "semantic CB decisions remain outside this shim"
    )


def emit_host(envelope: Mapping[str, Any], host: str | None = None) -> tuple[str, int]:
    """Render the smallest denial wire each host can consume."""

    selected = normalize_host(host) if host is not None else normalize_host(str(envelope.get("host", "")))
    if bool(envelope.get("allow")):
        return "", 0
    reason = _refusal_reason(envelope)
    if selected in {"claude", "codex"}:
        return (
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason,
                    }
                },
                sort_keys=True,
            ),
            0,
        )
    if selected == "grok":
        return json.dumps({"decision": "deny", "reason": reason}, sort_keys=True), 0
    if selected == "hermes":
        if envelope.get("event_type") != PRE_TOOL:
            # Hermes lifecycle/end hooks are observational.  Only a
            # pre_tool_call may carry a blocking action; cancellation/end
            # evidence must not become a stop veto.
            return json.dumps({"action": "allow"}, sort_keys=True), 0
        return json.dumps({"action": "block", "message": reason}, sort_keys=True), 2
    return json.dumps({"decision": "block", "reason": reason}, sort_keys=True), 2


def _read_stdin_bytes() -> bytes:
    stream = getattr(sys.stdin, "buffer", None)
    if stream is not None:
        data = stream.read()
        return data if isinstance(data, bytes) else str(data).encode("utf-8")
    value = sys.stdin.read()
    return value.encode("utf-8") if isinstance(value, str) else bytes(value)


def _load_payload(raw: bytes) -> tuple[Mapping[str, Any] | Any, str | None]:
    if not raw.strip():
        return {}, "empty_stdin"
    try:
        loaded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}, "json_decode"
    if not isinstance(loaded, Mapping):
        return {}, "non_object"
    return loaded, None


def run_stdio(
    host_hint: str | None = None,
    *,
    product_root: str | Path | None = None,
    light_interpreter: str | Path | None = None,
    event_log: str | Path | None = None,
    hook_source: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    print_envelope: bool = False,
) -> int:
    """Run the explicit-interpreter stdin seam."""

    effective = dict(os.environ) if env is None else dict(env)
    root = product_root or effective.get("CB_PRODUCT_ROOT")
    light = light_interpreter or effective.get("CB_LIGHT_PYTHON") or effective.get("CB_LIGHT_INTERPRETER")
    log = event_log or effective.get("CB_HOOK_EVENT_LOG")
    bound = binding_status(root, light, log, hook_source=hook_source)
    if not log:
        log = bound.get("event_log")
    raw = _read_stdin_bytes()
    if bound["status"] != "PASS" and not bound.get("capture_ready"):
        envelope: dict[str, Any] = {
            "schema": SCHEMA,
            "host": normalize_host(host_hint),
            "event_type": UNKNOWN,
            "source_event": None,
            "session_id": None,
            "invocation_id": None,
            "tool_name": None,
            "command_sha256": None,
            "payload_sha256": sha256_bytes(raw),
            "typed_proposal": None,
            "status": "HOLD",
            "disposition": bound["reason_code"],
            "allow": False,
            "authority_removed": True,
            "cancelled": False,
            "binding": bound,
            "claim_ceiling": CLAIM_CEILING,
            "promotion_allowed": False,
        }
        if print_envelope:
            sys.stdout.write(json.dumps(envelope, sort_keys=True) + "\n")
            return 2
        wire, _ = emit_host(envelope, host_hint)
        if wire:
            sys.stdout.write(wire + "\n")
        return 2

    payload, parse_error = _load_payload(raw)
    envelope = process_event(
        payload,
        host_hint=host_hint,
        env=effective,
        product_root=root,
        source_bytes=raw,
        parse_error=parse_error,
    )
    envelope["binding"] = bound
    if bound["status"] != "PASS":
        envelope.update(
            {
                "allow": False,
                "authority_removed": True,
                "disposition": bound["reason_code"],
                "capability_hold": True,
            }
        )
    try:
        envelope = append_event_log(
            envelope,
            event_log=str(log),
            product_root=str(root),
        )
    except (OSError, ValueError) as exc:
        envelope = dict(envelope)
        envelope.update(
            {
                "allow": False,
                "authority_removed": True,
                "disposition": "REFUSE_EVENT_LOG_WRITE_FAILED",
                "event_log_error": type(exc).__name__,
            }
        )
    if print_envelope:
        sys.stdout.write(json.dumps(envelope, sort_keys=True) + "\n")
        if envelope.get("capability_hold"):
            return 2
        if envelope.get("host") == "hermes" and envelope.get("event_type") != PRE_TOOL:
            return 0
        return 0 if envelope.get("allow") else (2 if envelope.get("host") == "hermes" else 0)
    wire, code = emit_host(envelope, host_hint)
    if wire:
        sys.stdout.write(wire + "\n")
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host_positional", nargs="?", choices=HOSTS)
    parser.add_argument("--host", dest="host_option", choices=HOSTS, default=None)
    parser.add_argument("--product-root", default=None)
    parser.add_argument("--light-interpreter", default=None)
    parser.add_argument("--event-log", default=None)
    parser.add_argument("--hook-source", default=None)
    parser.add_argument("--print-envelope", action="store_true")
    args = parser.parse_args(argv)
    host = args.host_option or args.host_positional
    if host is None:
        parser.error("one of --host or the positional host is required")
    return run_stdio(
        host,
        product_root=args.product_root,
        light_interpreter=args.light_interpreter,
        event_log=args.event_log,
        hook_source=args.hook_source,
        print_envelope=args.print_envelope,
    )


if __name__ == "__main__":
    raise SystemExit(main())
