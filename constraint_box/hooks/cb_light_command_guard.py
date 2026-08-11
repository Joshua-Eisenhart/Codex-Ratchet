"""Pure-stdlib command guard for the contained CB Light Claude hooks.

This is an early-warning classifier, not the security boundary. Shell text can
hide a program through files, variables, or subprocesses. The postcondition in
``cb_light_hook.py`` therefore remeasures the contained runtime after Bash.
"""

from __future__ import annotations

import pathlib
import re
import shlex
from collections.abc import Mapping
from typing import Any


_PACKAGE_MANAGERS = {
    "conda",
    "easy_install",
    "hatch",
    "mamba",
    "micromamba",
    "pdm",
    "pip",
    "pip-sync",
    "pipx",
    "pixi",
    "poetry",
    "rye",
    "spack",
    "uv",
    "uvx",
}
_MUTATION_VERBS = {
    "add",
    "create",
    "develop",
    "inject",
    "install",
    "remove",
    "run",
    "sync",
    "uninstall",
    "update",
    "upgrade",
}
_GIT_VALUE_OPTIONS = {
    "-C",
    "-c",
    "--exec-path",
    "--git-dir",
    "--namespace",
    "--work-tree",
}
_DYNAMIC_SHELL = re.compile(r"\$\(|`|<\(|>\(|\$\{|\$[A-Za-z_]")
_PACKAGE_TEXT = re.compile(
    r"(?i)(?:\bpip(?:\d+(?:\.\d+)*)?\b|\bpip-sync\b|\bpipx\b|\buvx?\b|"
    r"\bpoetry\b|\bconda\b|\bmamba\b|\bmicromamba\b|\bpdm\b|\bhatch\b|"
    r"\brye\b|\bpixi\b|\bspack\b|\beasy_install\b|\bsetup\.py\b|"
    r"\bsite-packages\b|\bensurepip\b|\bupgrade-deps\b|\bpip\._internal\b)"
)
_ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*", re.DOTALL)
_SHELLS = {"bash", "dash", "ksh", "sh", "zsh"}
_FILE_MUTATORS = {
    "chmod",
    "cp",
    "install",
    "ln",
    "mv",
    "rm",
    "rsync",
    "sed",
    "tar",
    "tee",
    "touch",
    "unzip",
}


def command_from_payload(payload: Mapping[str, Any]) -> str:
    direct = payload.get("command")
    if isinstance(direct, str):
        return direct
    for key in ("tool_input", "inputs"):
        nested = payload.get(key)
        if isinstance(nested, Mapping) and isinstance(nested.get("command"), str):
            return str(nested["command"])
    return ""


def _tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def _resolve(value: str, cwd: pathlib.Path) -> pathlib.Path:
    path = pathlib.Path(value).expanduser()
    if not path.is_absolute():
        path = cwd / path
    return path.resolve()


def broker_subcommand(
    command: str, *, cwd: pathlib.Path, broker: pathlib.Path
) -> tuple[str | None, str | None]:
    """Return ``(subcommand, error)`` for a direct broker invocation."""

    try:
        segments = _segment_tokens(_tokens(command))
    except ValueError:
        return None, "COMMAND_PARSE_FAILED"
    if len(segments) != 1:
        return None, None
    return _broker_segment(segments[0], cwd=cwd, broker=broker)


def _segment_tokens(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = [[]]
    for token in tokens:
        if token in {";", "&&", "||", "|", "&"}:
            if segments[-1]:
                segments.append([])
            continue
        segments[-1].append(token)
    return [segment for segment in segments if segment]


def _command_head(segment: list[str]) -> tuple[int, str] | None:
    """Return the executable position/name after env assignments and ``env``."""

    cursor = 0
    while cursor < len(segment) and _ASSIGNMENT.fullmatch(segment[cursor]):
        cursor += 1
    if cursor >= len(segment):
        return None
    if pathlib.Path(segment[cursor]).name.lower() == "env":
        cursor += 1
        while cursor < len(segment):
            token = segment[cursor]
            if token == "--":
                cursor += 1
                break
            if token.startswith("-") or _ASSIGNMENT.fullmatch(token):
                cursor += 1
                continue
            break
    if cursor >= len(segment):
        return None
    return cursor, pathlib.Path(segment[cursor]).name.lower()


def _broker_segment(
    segment: list[str], *, cwd: pathlib.Path, broker: pathlib.Path
) -> tuple[str | None, str | None]:
    head = _command_head(segment)
    if head is None:
        return None, None
    cursor, _ = head
    try:
        executable = _resolve(segment[cursor], cwd)
    except OSError:
        return None, None
    if executable != broker.resolve():
        return None, None
    rest = segment[cursor + 1 :]
    if len(rest) != 1 or rest[0] not in {
        "complete",
        "install",
        "list",
        "refresh",
        "status",
    }:
        return None, "MALFORMED_BROKER_INVOCATION"
    return rest[0], None


def _nested_shell_command(segment: list[str]) -> str | None:
    head = _command_head(segment)
    if head is None:
        return None
    cursor, executable = head
    if executable not in _SHELLS:
        return None
    rest = segment[cursor + 1 :]
    for index, token in enumerate(rest):
        if token == "-c" and index + 1 < len(rest):
            return rest[index + 1]
        if token.startswith("-") and "c" in token[1:] and index + 1 < len(rest):
            return rest[index + 1]
    return None


def _segment_mutates(segment: list[str]) -> bool:
    head = _command_head(segment)
    if head is None:
        return False
    cursor, executable = head
    arguments = segment[cursor + 1 :]
    lowered = [pathlib.Path(token).name.lower() for token in arguments]
    nested = _nested_shell_command(segment)
    if nested is not None:
        try:
            return any(
                _segment_mutates(child)
                for child in _segment_tokens(_tokens(nested))
            )
        except ValueError:
            return bool(
                _PACKAGE_TEXT.search(nested)
                and re.search(r"(?i)\b(?:install|uninstall|sync|upgrade)\b", nested)
            )
    if executable in _PACKAGE_MANAGERS or executable.startswith("pip"):
        return bool(set(lowered[:12]).intersection(_MUTATION_VERBS))
    if executable in {"python", "python3", "python3.13"} or executable.startswith(
        "python3."
    ):
        module: str | None = None
        for index, token in enumerate(arguments):
            if token == "-m" and index + 1 < len(arguments):
                module = arguments[index + 1].lower()
                break
            if token.startswith("-m") and len(token) > 2:
                module = token[2:].lower()
                break
        if module in {"ensurepip", "venv"}:
            return True
        if module in {"installer", "pip", "pip._internal"} and set(
            lowered
        ).intersection(_MUTATION_VERBS):
            return True
        if "-c" in arguments:
            code_index = arguments.index("-c") + 1
            code = arguments[code_index] if code_index < len(arguments) else ""
            if _PACKAGE_TEXT.search(code) and re.search(
                r"(?i)\b(?:install|uninstall|sync|upgrade)\b", code
            ):
                return True
    if executable == "setup.py" and set(lowered).intersection({"develop", "install"}):
        return True
    if executable in _FILE_MUTATORS and any(
        "site-packages" in token.lower() for token in arguments
    ):
        return True
    return False


def classify_command(
    command: str, *, cwd: pathlib.Path, broker: pathlib.Path
) -> dict[str, Any]:
    if not command.strip():
        return {
            "disposition": "DENY",
            "reason_code": "EMPTY_BASH_COMMAND",
            "postcondition_required": True,
        }
    try:
        tokens = _tokens(command)
    except ValueError:
        return {
            "disposition": "DENY",
            "reason_code": "COMMAND_PARSE_FAILED",
            "postcondition_required": True,
        }
    segments = _segment_tokens(tokens)
    broker_commands: list[str] = []
    malformed_broker = False
    mutation = False
    segment_cwd = cwd
    for segment in segments:
        head = _command_head(segment)
        if head is not None and head[1] == "cd":
            arguments = segment[head[0] + 1 :]
            if len(arguments) == 1:
                try:
                    segment_cwd = _resolve(arguments[0], segment_cwd)
                except OSError:
                    pass
            continue
        subcommand, broker_error = _broker_segment(
            segment, cwd=segment_cwd, broker=broker
        )
        malformed_broker = malformed_broker or broker_error is not None
        if subcommand is not None:
            broker_commands.append(subcommand)
            continue
        mutation = mutation or _segment_mutates(segment)
    if malformed_broker or len(broker_commands) > 1:
        return {
            "disposition": "DENY",
            "reason_code": (
                "MULTIPLE_BROKER_INVOCATIONS"
                if len(broker_commands) > 1
                else "MALFORMED_BROKER_INVOCATION"
            ),
            "postcondition_required": True,
        }
    package_text = bool(_PACKAGE_TEXT.search(command))
    dynamic_package_mutation = bool(
        _DYNAMIC_SHELL.search(command)
        and package_text
        and re.search(r"(?i)\b(?:install|uninstall|sync|upgrade)\b", command)
    )
    if dynamic_package_mutation:
        return {
            "disposition": "DENY",
            "reason_code": "DYNAMIC_PACKAGE_MUTATION_REFUSED",
            "postcondition_required": True,
        }
    if mutation:
        return {
            "disposition": "DENY",
            "reason_code": "DIRECT_PACKAGE_MUTATION_REFUSED",
            "postcondition_required": True,
        }
    if broker_commands:
        subcommand = broker_commands[0]
        return {
            "disposition": "ADMIT",
            "reason_code": "CONTAINED_CB_LIGHT_BROKER",
            "broker": True,
            "broker_subcommand": subcommand,
            "mutation": subcommand == "install",
            "postcondition_required": True,
        }
    return {
        "disposition": "ADMIT",
        "reason_code": "NO_RECOGNIZED_PACKAGE_MUTATION",
        "mutation": False,
        "postcondition_required": True,
    }


def git_transition(command: str) -> str | None:
    """Find a commit/push subcommand after Git global options."""

    try:
        tokens = _tokens(command)
    except ValueError:
        return None
    for segment in _segment_tokens(tokens):
        nested = _nested_shell_command(segment)
        if nested is not None:
            transition = git_transition(nested)
            if transition:
                return transition
        head = _command_head(segment)
        if head is None or head[1] != "git":
            continue
        rest = segment[head[0] + 1 :]
        cursor = 0
        while cursor < len(rest) and rest[cursor].startswith("-"):
            option = rest[cursor].split("=", 1)[0]
            cursor += 2 if option in _GIT_VALUE_OPTIONS and "=" not in rest[cursor] else 1
        if cursor < len(rest) and rest[cursor] in {"commit", "push"}:
            return rest[cursor]
    return None
