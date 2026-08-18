#!/usr/bin/env python3
"""Contained, backup-first installer for the four host hook schemas.

This module is deliberately independent of the provider adapters and of the
portable hook runtime.  It only edits explicitly supplied fixture/host-root
configuration paths.  ``plan`` is the default operation and never mutates a
path.  ``apply`` writes a receipt and a backup before changing a configuration;
``verify`` checks the receipt and current files; ``rollback`` restores only
when the target still has the hash recorded by ``apply``.

No host process, provider, model, credential file, or network operation is
started by this module.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import shlex
import stat
import sys
import tomllib
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Sequence


SCHEMA = "constraintbox.integrated.host-hook-installer.v1"
RECEIPT_SCHEMA = "constraintbox.integrated.host-hook-install-receipt.v1"
PLAN_SCHEMA = "constraintbox.integrated.host-hook-install-plan.v2"
BOOTSTRAP_PYTHON = "/usr/bin/python3"
HOSTS = ("codex", "claude", "grok", "hermes")
TARGET_IDS = HOSTS + ("grok_compat",)
RUNS_RELATIVE = Path("integrated_system") / "runs" / "host-hook-installer"
SOURCE_RELATIVE = Path("integrated_system") / "hooks" / "portable_host_hook.py"
HOOKS_RELATIVE = Path("integrated_system") / "hooks"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
ABSENT_SHA256 = hashlib.sha256(b"constraintbox:absent:v1").hexdigest()
CLAIM_CEILING = (
    "configuration_installation_and_replay_only;"
    "no_host_activation;no_provider_or_model_launch;no_semantic_cb_decision;"
    "no_credential_read_or_copy;plan_receipt_integrity_not_authentication;"
    "caller_expected_hash_required_for_verify_rollback;promotion_allowed_false"
)


class InstallerError(RuntimeError):
    """A deterministic refusal that is safe to show in a receipt."""

    def __init__(self, code: str, detail: str | None = None):
        self.code = code
        self.detail = detail or code
        super().__init__(f"{code}: {self.detail}")


@dataclass(frozen=True)
class HostSpec:
    name: str
    events: tuple[str, ...]
    config_kind: str
    compatibility: str | None = None


# These event names are the current local inventory, not a promise that a
# future host version supports every event.  Hermes deliberately has only the
# pre-tool veto entry: an interrupted session end is passive evidence in the
# portable adapter and is not installed as a stop hook.
HOST_SPECS: dict[str, HostSpec] = {
    "codex": HostSpec("codex", ("SessionStart", "PreToolUse", "PostToolUse"), "json"),
    "claude": HostSpec(
        "claude", ("SessionStart", "PreToolUse", "PostToolUse", "Stop"), "json"
    ),
    "grok": HostSpec(
        "grok",
        ("SessionStart", "PreToolUse", "PostToolUse", "SessionEnd"),
        "json",
        compatibility="claude",
    ),
    "hermes": HostSpec("hermes", ("pre_tool_call",), "yaml"),
}


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _self_digest(value: Mapping[str, Any], field: str) -> str:
    body = {key: item for key, item in value.items() if key != field}
    return _hash_bytes(_canonical_json(body))


def _require_self_digest(value: Mapping[str, Any], field: str, code: str) -> str:
    supplied = value.get(field)
    if not isinstance(supplied, str) or supplied != _self_digest(value, field):
        raise InstallerError(code)
    return supplied


def _lexical(path: str | Path) -> Path:
    return Path(os.path.abspath(os.path.expanduser(str(path))))


def _canonical_alias(path: str | Path) -> Path:
    """Canonicalize the macOS ``/var`` -> ``/private/var`` spelling."""

    raw = Path(os.path.abspath(os.path.expanduser(str(path))))
    if raw.parts[:2] == (os.sep, "var") and Path("/private/var").exists():
        return Path("/private/var", *raw.parts[2:])
    return raw


def _has_traversal(path: str | Path) -> bool:
    return ".." in Path(str(path)).parts


def _require_absolute(path: str | Path, code: str) -> Path:
    raw = str(path)
    if not raw or not Path(raw).expanduser().is_absolute():
        raise InstallerError(code, "absolute path required")
    if _has_traversal(raw):
        raise InstallerError(code, "path traversal is not accepted")
    return _canonical_alias(raw)


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _validate_ancestor_custody(
    path: Path,
    *,
    allow_missing: bool,
    allow_final_symlink: bool = False,
) -> Path:
    """Validate every existing ancestor before any path is opened.

    ``Path.resolve`` by itself is not a custody check: it silently follows a
    redirected component.  Walk the supplied lexical spelling first, then
    return its canonical spelling only after every existing component has been
    checked.  Missing tails are allowed only for explicitly staged config/run
    creation.
    """

    raw = _require_absolute(path, "HOLD_PATH_CUSTODY")
    anchor = Path(raw.anchor or os.sep)
    current = anchor
    parts = raw.parts[1:] if raw.anchor else raw.parts
    for index, part in enumerate(parts):
        current = current / part
        is_final = index == len(parts) - 1
        if current.is_symlink() and not (allow_final_symlink and is_final):
            raise InstallerError("HOLD_SYMLINK_ANCESTOR", str(current))
        if current.exists():
            if is_final:
                if not current.is_file() and not current.is_dir() and not current.is_symlink():
                    raise InstallerError("HOLD_NONREGULAR_PATH", str(current))
            elif not current.is_dir():
                raise InstallerError("HOLD_NONDIRECTORY_ANCESTOR", str(current))
            continue
        if not allow_missing:
            raise InstallerError("HOLD_PATH_MISSING", str(current))
        # Once a component is missing, no later component can be an existing
        # symlink in this lexical path.  The creator validates each new
        # directory again immediately before making it.
        break
    return raw.resolve(strict=False)


def _check_component_chain(
    path: Path,
    root: Path,
    *,
    allow_missing: bool,
    allow_final_symlink: bool = False,
) -> None:
    """Refuse redirects while walking a path from ``root`` to ``path``."""

    path = _canonical_alias(path)
    root = _canonical_alias(root)
    _validate_ancestor_custody(
        path,
        allow_missing=allow_missing,
        allow_final_symlink=allow_final_symlink,
    )
    _validate_ancestor_custody(root, allow_missing=False)
    if not _is_under(path, root):
        raise InstallerError("HOLD_TARGET_ESCAPE", str(path))
    current = root
    if current.is_symlink():
        raise InstallerError("HOLD_TARGET_ROOT_SYMLINK", str(current))
    if current.exists() and not current.is_dir():
        raise InstallerError("HOLD_TARGET_ROOT_NOT_DIRECTORY", str(current))
    relative = path.relative_to(root)
    for part_index, part in enumerate(relative.parts):
        current = current / part
        if current.is_symlink() and not (
            allow_final_symlink and part_index == len(relative.parts) - 1
        ):
            raise InstallerError("HOLD_TARGET_SYMLINK", str(current))
        if current.exists() and current.is_dir():
            continue
        if current.exists():
            if not current.is_file():
                raise InstallerError("HOLD_TARGET_NONREGULAR", str(current))
            continue
        if not allow_missing:
            raise InstallerError("HOLD_TARGET_MISSING", str(current))


def _check_regular(path: Path, *, allow_missing: bool, code_prefix: str) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        if allow_missing:
            return False
        raise InstallerError(f"{code_prefix}_MISSING", str(path))
    except OSError as exc:
        raise InstallerError(f"{code_prefix}_UNREADABLE", type(exc).__name__) from exc
    if stat.S_ISLNK(info.st_mode):
        raise InstallerError(f"{code_prefix}_SYMLINK", str(path))
    if not stat.S_ISREG(info.st_mode):
        raise InstallerError(f"{code_prefix}_NONREGULAR", str(path))
    if info.st_nlink != 1:
        raise InstallerError(f"{code_prefix}_HARDLINK", str(path))
    return True


def _credential_path(path: Path) -> bool:
    """Reject obvious credential stores before opening them.

    Hook configuration is intentionally narrow.  A target named like a token,
    key, auth, secret, or credential store is never read or copied.
    """

    names = {part.lower() for part in path.parts}
    base = path.name.lower()
    if base in {".env", ".netrc", "credentials", "credentials.json", "auth.json"}:
        return True
    if any(word in base for word in ("credential", "secret", "token", "password", "private-key")):
        return True
    return bool(names.intersection({".ssh", ".aws", ".gnupg", "tokens", "credentials"}))


def _validate_config_location(host: str, host_root: Path, config: Path) -> None:
    """Enforce the inventoried host config format and filename surface."""

    spec = HOST_SPECS[host]
    suffix = config.suffix.lower()
    if spec.config_kind == "json" and suffix != ".json":
        raise InstallerError("HOLD_CONFIG_KIND_MISMATCH", f"{host} requires JSON")
    if spec.config_kind == "yaml" and suffix not in {".yaml", ".yml"}:
        raise InstallerError("HOLD_CONFIG_KIND_MISMATCH", f"{host} requires YAML")

    root_name = host_root.name.lower()
    relative = config.relative_to(host_root)
    if host == "codex":
        valid = (config.name == "hooks.json" and (root_name == ".codex" or relative.parts[:1] == (".codex",)))
    elif host == "claude":
        valid = config.name in {"settings.json", "settings.local.json"} and (
            root_name == ".claude" or relative.parts[:1] == (".claude",)
        )
    elif host == "grok":
        valid = config.name.endswith(".json") and (
            (root_name == ".grok" and (len(relative.parts) == 1 or relative.parts[:1] == ("hooks",)))
            or relative.parts[:2] == (".grok", "hooks")
            or relative.parts == (".grok", "hooks.json")
        )
    else:  # Hermes config.yaml is the only inventoried mutable hook surface.
        valid = config.name in {"config.yaml", "config.yml"} and (
            root_name == ".hermes" or relative.parts[:1] == (".hermes",)
        )
    if not valid:
        raise InstallerError("HOLD_CONFIG_FILENAME_UNSUPPORTED", f"{host}:{config}")


def _fsync_directory(path: Path) -> None:
    flags = getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_RDONLY", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise InstallerError("HOLD_DIRECTORY_FSYNC", str(path)) from exc
    try:
        os.fsync(fd)
    except OSError as exc:
        raise InstallerError("HOLD_DIRECTORY_FSYNC", str(path)) from exc
    finally:
        os.close(fd)


def _mkdir_chain(path: Path, root: Path) -> None:
    """Create only missing directories below an already checked root."""

    if not _is_under(path, root):
        raise InstallerError("HOLD_RUN_PATH_ESCAPE", str(path))
    _validate_ancestor_custody(path, allow_missing=True)
    missing: list[Path] = []
    current = path
    while current != root and not current.exists():
        missing.append(current)
        current = current.parent
    if current != root:
        _check_component_chain(current, root, allow_missing=False)
    for directory in reversed(missing):
        directory.mkdir()
        _fsync_directory(directory.parent)
    _check_component_chain(path, root, allow_missing=False)


def atomic_write(path: str | Path, data: bytes, *, mode: int = 0o600) -> None:
    """Write bytes through a same-directory temporary followed by replace."""

    target = Path(path)
    parent = target.parent
    _validate_ancestor_custody(parent, allow_missing=False)
    _check_regular(target, allow_missing=True, code_prefix="HOLD_ATOMIC_TARGET")
    token = f".{target.name}.cbtmp-{os.getpid()}-{uuid.uuid4().hex}"
    temporary = parent / token
    descriptor = -1
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(temporary, flags, mode)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), mode)
        os.replace(temporary, target)
        _fsync_directory(parent)
    except Exception:
        if descriptor >= 0:
            with contextlib.suppress(OSError):
                os.close(descriptor)
        with contextlib.suppress(FileNotFoundError, OSError):
            temporary.unlink()
        raise


def _native_interpreter(path: Path) -> bool:
    try:
        with path.open("rb") as stream:
            magic = stream.read(4)
    except OSError:
        return False
    return magic in {
        b"\x7fELF",
        b"\xfe\xed\xfa\xce",
        b"\xce\xfa\xed\xfe",
        b"\xfe\xed\xfa\xcf",
        b"\xcf\xfa\xed\xfe",
    }


def _runtime_binding(product_root: str | Path, light_interpreter: str | Path) -> dict[str, Any]:
    product = _require_absolute(product_root, "HOLD_PRODUCT_ROOT_PATH")
    _validate_ancestor_custody(product, allow_missing=False)
    if product.is_symlink():
        raise InstallerError("HOLD_PRODUCT_ROOT_SYMLINK", str(product))
    if not product.is_dir():
        raise InstallerError("HOLD_PRODUCT_ROOT_MISSING", str(product))
    light_raw = _require_absolute(light_interpreter, "HOLD_LIGHT_INTERPRETER_PATH")
    if not _is_under(light_raw, product):
        raise InstallerError("HOLD_LIGHT_INTERPRETER_OUTSIDE_PRODUCT", str(light_raw))
    if light_raw.parent.name != "bin":
        raise InstallerError("HOLD_LIGHT_INTERPRETER_NOT_VENV_ENTRYPOINT", str(light_raw))
    venv_root = light_raw.parent.parent
    if venv_root == product or not _is_under(venv_root, product):
        raise InstallerError("HOLD_LIGHT_VENV_OUTSIDE_PRODUCT", str(venv_root))
    _check_component_chain(
        light_raw, product, allow_missing=False, allow_final_symlink=True
    )
    try:
        light_info = light_raw.lstat()
    except OSError as exc:
        raise InstallerError("HOLD_LIGHT_INTERPRETER_UNREADABLE", str(light_raw)) from exc
    # A normal venv entrypoint is commonly a symlink to the system Python.  It
    # is accepted here, while every parent, the pyvenv.cfg, and the resolved
    # target remain receipt-bound and custody-checked.
    if stat.S_ISLNK(light_info.st_mode):
        if light_info.st_nlink != 1:
            raise InstallerError("HOLD_LIGHT_INTERPRETER_HARDLINK", str(light_raw))
    elif not stat.S_ISREG(light_info.st_mode) or light_info.st_nlink != 1:
        raise InstallerError("HOLD_LIGHT_INTERPRETER_NONREGULAR", str(light_raw))
    if not os.access(light_raw, os.X_OK):
        raise InstallerError("HOLD_LIGHT_INTERPRETER_NOT_EXECUTABLE", str(light_raw))
    cfg = venv_root / "pyvenv.cfg"
    if cfg.is_symlink():
        raise InstallerError("HOLD_LIGHT_PYVENV_CONFIG_SYMLINK", str(cfg))
    _check_regular(cfg, allow_missing=False, code_prefix="HOLD_LIGHT_PYVENV_CONFIG")
    _check_component_chain(cfg, product, allow_missing=False)
    resolved = light_raw.resolve(strict=True)
    if not _is_under(resolved, product) and not _native_interpreter(resolved):
        raise InstallerError("HOLD_LIGHT_INTERPRETER_TARGET_INVALID", str(resolved))
    if not _native_interpreter(resolved):
        raise InstallerError("HOLD_LIGHT_INTERPRETER_NOT_NATIVE", str(resolved))
    source = product / SOURCE_RELATIVE
    _check_component_chain(source, product, allow_missing=False)
    _check_regular(source, allow_missing=False, code_prefix="HOLD_HOOK_SOURCE")
    scripts: dict[str, str] = {}
    for host in HOSTS:
        script = product / HOOKS_RELATIVE / f"{host}.sh"
        _check_component_chain(script, product, allow_missing=False)
        _check_regular(script, allow_missing=False, code_prefix="HOLD_HOOK_SCRIPT")
        if not os.access(script, os.X_OK):
            raise InstallerError("HOLD_HOOK_SCRIPT_NOT_EXECUTABLE", str(script))
        scripts[host] = _hash_file(script)
    relevant = {
        "source": str(source),
        "source_sha256": _hash_file(source),
        "source_mode": stat.S_IMODE(source.stat().st_mode),
        "scripts": scripts,
        "script_modes": {
            host: stat.S_IMODE((product / HOOKS_RELATIVE / f"{host}.sh").stat().st_mode)
            for host in HOSTS
        },
        "bootstrap": BOOTSTRAP_PYTHON,
    }
    return {
        "product_root": str(product),
        "product_binding_sha256": _hash_bytes(_canonical_json(relevant)),
        "hook_source": str(source),
        "hook_source_sha256": relevant["source_sha256"],
        "hook_source_mode": relevant["source_mode"],
        "hook_scripts_sha256": scripts,
        "hook_scripts_mode": relevant["script_modes"],
        "light_interpreter_lexical": str(light_raw),
        "light_interpreter_resolved": str(resolved),
        "light_interpreter_sha256": _hash_file(light_raw),
        "light_interpreter_target_sha256": _hash_file(resolved),
        "light_interpreter_target_mode": stat.S_IMODE(resolved.stat().st_mode),
        "pyvenv_cfg": str(cfg),
        "pyvenv_cfg_sha256": _hash_file(cfg),
        "pyvenv_cfg_mode": stat.S_IMODE(cfg.stat().st_mode),
        "bootstrap_interpreter": BOOTSTRAP_PYTHON,
        "event_log": str(product / RUNS_RELATIVE.parent / "hook-events.jsonl"),
    }


def _render_command(host: str, binding: Mapping[str, Any]) -> str:
    product = Path(str(binding["product_root"]))
    script = product / HOOKS_RELATIVE / f"{host}.sh"
    values = {
        "CB_PRODUCT_ROOT": str(product),
        "CB_LIGHT_PYTHON": str(binding["light_interpreter_lexical"]),
        "CB_HOOK_EVENT_LOG": str(binding["event_log"]),
        "CB_HOOK_SOURCE": str(binding["hook_source"]),
        "CB_LIGHT_PYTHON_SHA256": str(binding["light_interpreter_sha256"]),
        "CB_HOOK_SOURCE_SHA256": str(binding["hook_source_sha256"]),
        "CB_HOOK_BINDING_SHA256": str(binding["product_binding_sha256"]),
    }
    parts = [BOOTSTRAP_PYTHON.replace("python3", "env")]
    parts.extend(f"{key}={value}" for key, value in values.items())
    parts.extend([str(script), host])
    return " ".join(shlex.quote(part) for part in parts)


def _command_product_root(command: str) -> Path:
    """Recover the explicit product root from a rendered env prefix."""

    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        raise InstallerError("HOLD_CONFIG_COMMAND_PARSE_FAILURE", type(exc).__name__) from exc
    for token in tokens:
        if token.startswith("CB_PRODUCT_ROOT="):
            return Path(token.split("=", 1)[1])
    for token in tokens:
        marker = "/integrated_system/hooks/"
        if marker in token:
            return Path(token.split(marker, 1)[0])
    raise InstallerError("HOLD_CONFIG_COMMAND_BINDING_MISSING")


def _command_identity(command: str, product_root: Path) -> tuple[str, str] | None:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    scripts = {str(product_root / HOOKS_RELATIVE / f"{host}.sh"): host for host in HOSTS}
    for index, token in enumerate(tokens):
        host = scripts.get(token)
        if host is None and token == str(product_root / HOOKS_RELATIVE / "cb_hook.sh"):
            host = None
        if host is not None:
            if index + 1 < len(tokens) and tokens[index + 1] in HOSTS:
                return tokens[index + 1], command
            return host, command
        if token.endswith("/cb_hook.sh") and index + 1 < len(tokens) and tokens[index + 1] in HOSTS:
            return tokens[index + 1], command
    return None


def _legacy_command_matches(
    command: str, host: str, binding: Mapping[str, Any] | None
) -> bool:
    """Match an old command only against an explicit sealed source binding."""

    if binding is None:
        return False
    source = binding.get("path")
    if not isinstance(source, str):
        return False
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    if tokens == [source, host]:
        return True
    return tokens == ["bash", source, host] or tokens == ["/bin/bash", source, host]


def _legacy_command_mentions(command: str, binding: Mapping[str, Any] | None) -> bool:
    source = binding.get("path") if isinstance(binding, Mapping) else None
    return isinstance(source, str) and source in command


def _walk_commands(value: Any, path: tuple[Any, ...] = ()) -> Iterable[tuple[tuple[Any, ...], MutableMapping[str, Any], str]]:
    if isinstance(value, MutableMapping):
        command = value.get("command")
        if isinstance(command, str):
            yield path, value, command
        for key, child in value.items():
            yield from _walk_commands(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_commands(child, path + (index,))


def _event_value(document: Mapping[str, Any], event: str) -> Any:
    hooks = document.get("hooks")
    if isinstance(hooks, Mapping):
        if event in hooks:
            return hooks[event]
        # A case-insensitive match is useful for old fixtures but does not
        # invent a new event name.
        for key, value in hooks.items():
            if str(key).lower() == event.lower():
                return value
        return None
    if isinstance(hooks, list):
        return [row for row in hooks if isinstance(row, Mapping) and str(row.get("event", "")).lower() == event.lower()]
    if event in document:
        return document[event]
    return None


def _all_config_commands(document: Mapping[str, Any]) -> Iterable[str]:
    yield from (command for _path, _obj, command in _walk_commands(document))


def _managed_hosts(
    document: Mapping[str, Any],
    product_root: Path,
    legacy_bindings: Mapping[str, Mapping[str, Any]] | None = None,
) -> set[str]:
    hosts: set[str] = set()
    for command in _all_config_commands(document):
        identity = _command_identity(command, product_root)
        if identity is not None:
            hosts.add(identity[0])
    for host, binding in (legacy_bindings or {}).items():
        if any(
            _legacy_command_matches(command, host, binding)
            for command in _all_config_commands(document)
        ):
            hosts.add(host)
    return hosts


def _make_json_handler(host: str, command: str, *, direct: bool) -> dict[str, Any]:
    if host == "hermes":
        return {"matcher": "terminal|execute_code|delegate_task", "command": command, "timeout": 30, "fail_closed": True}
    if direct:
        return {"type": "command", "command": command, "timeout": 30}
    return {"matcher": ".*", "hooks": [{"type": "command", "command": command, "timeout": 30}]}


def _append_event_json(document: MutableMapping[str, Any], host: str, event: str, command: str) -> bool:
    hooks = document.get("hooks")
    if hooks is None:
        hooks = {}
        document["hooks"] = hooks
    if isinstance(hooks, Mapping) and not isinstance(hooks, MutableMapping):
        raise InstallerError("HOLD_CONFIG_SCHEMA_UNSUPPORTED", "hooks mapping is immutable")
    if isinstance(hooks, MutableMapping):
        bucket = hooks.get(event)
        if bucket is None:
            bucket = []
            hooks[event] = bucket
        if not isinstance(bucket, list):
            raise InstallerError("HOLD_CONFIG_SCHEMA_INVALID", f"hooks.{event} is not an array")
        direct = host == "hermes" or any(isinstance(row, Mapping) and "command" in row and "hooks" not in row for row in bucket)
        bucket.append(_make_json_handler(host, command, direct=direct))
        return True
    if isinstance(hooks, list):
        hooks.append({"event": event, **_make_json_handler(host, command, direct=False)})
        return True
    raise InstallerError("HOLD_CONFIG_SCHEMA_INVALID", "hooks must be an object or array")


def _git_repository_identity(path: str | Path) -> dict[str, Any]:
    """Resolve a checkout/worktree to its canonical Git common directory."""

    start = _require_absolute(path, "HOLD_GIT_REPOSITORY_PATH")
    current = start if start.is_dir() else start.parent
    marker: Path | None = None
    repo_root: Path | None = None
    git_dir: Path | None = None
    while True:
        candidate = current / ".git"
        if candidate.is_dir():
            marker, repo_root, git_dir = candidate, current, candidate
            break
        if candidate.is_file():
            try:
                line = candidate.read_text(encoding="utf-8").splitlines()[0]
                if not line.startswith("gitdir:"):
                    raise ValueError("missing gitdir")
                raw_gitdir = line.split(":", 1)[1].strip()
                git_dir = _canonical_alias(
                    Path(raw_gitdir)
                    if Path(raw_gitdir).is_absolute()
                    else current / raw_gitdir
                )
            except Exception as exc:
                raise InstallerError("HOLD_GIT_METADATA_INVALID", str(candidate)) from exc
            marker, repo_root = candidate, current
            break
        if current == current.parent:
            break
        current = current.parent
    if marker is None or repo_root is None or git_dir is None:
        raise InstallerError("HOLD_GIT_REPOSITORY_IDENTITY_MISSING", str(start))
    _validate_ancestor_custody(git_dir, allow_missing=False)
    if not git_dir.is_dir():
        raise InstallerError("HOLD_GIT_COMMON_DIR_INVALID", str(git_dir))
    common_file = git_dir / "commondir"
    if common_file.exists():
        try:
            relative_common = common_file.read_text(encoding="utf-8").strip()
            common = _canonical_alias(
                Path(relative_common)
                if Path(relative_common).is_absolute()
                else git_dir / relative_common
            )
        except Exception as exc:
            raise InstallerError("HOLD_GIT_METADATA_INVALID", str(common_file)) from exc
    else:
        common = git_dir
    _validate_ancestor_custody(common, allow_missing=False)
    if not common.is_dir():
        raise InstallerError("HOLD_GIT_COMMON_DIR_INVALID", str(common))
    config = common / "config"
    config_hash = _hash_file(config) if config.is_file() and not config.is_symlink() else "MISSING"
    identity = {
        "git_common_dir": str(common),
        "git_common_dir_sha256": _hash_bytes(str(common).encode("utf-8")),
        "git_config_sha256": config_hash,
        "repository_identity_sha256": _hash_bytes(
            _canonical_json({"common": str(common), "config": config_hash})
        ),
    }
    return identity


def _validate_legacy_bindings(
    *,
    force_migration: bool,
    product_root: str | Path | None = None,
    legacy_hook_sources: Mapping[str, str | Path] | None,
    legacy_hook_source_hashes: Mapping[str, str] | None,
    legacy_hook_source_modes: Mapping[str, int] | None,
) -> dict[str, dict[str, Any]]:
    sources = dict(legacy_hook_sources or {})
    hashes = dict(legacy_hook_source_hashes or {})
    modes = dict(legacy_hook_source_modes or {})
    if not force_migration:
        if sources or hashes or modes:
            raise InstallerError("HOLD_LEGACY_SOURCE_UNEXPECTED")
        return {}
    if not sources:
        raise InstallerError("HOLD_LEGACY_SOURCE_REQUIRED")
    if product_root is None:
        raise InstallerError("HOLD_GIT_REPOSITORY_IDENTITY_MISSING")
    product_identity = _git_repository_identity(product_root)
    if set(sources) != set(hashes) or set(sources) != set(modes):
        raise InstallerError("HOLD_LEGACY_SOURCE_BINDING_SET_MISMATCH")
    bindings: dict[str, dict[str, Any]] = {}
    for host, raw_path in sources.items():
        if host not in HOSTS:
            raise InstallerError("HOLD_LEGACY_SOURCE_UNKNOWN_HOST", str(host))
        path = _require_absolute(raw_path, "HOLD_LEGACY_SOURCE_PATH")
        if path.parts[-5:] != ("Codex-Ratchet", "constraint_box", "hooks", "universal", "cb_hook.sh"):
            raise InstallerError("HOLD_LEGACY_SOURCE_NONCANONICAL", str(path))
        _validate_ancestor_custody(path, allow_missing=False)
        _check_regular(path, allow_missing=False, code_prefix="HOLD_LEGACY_SOURCE")
        mode = modes[host]
        if not isinstance(mode, int) or mode < 0 or mode > 0o7777:
            raise InstallerError("HOLD_LEGACY_SOURCE_MODE_INVALID", host)
        actual_hash = _hash_file(path)
        if actual_hash != hashes[host]:
            raise InstallerError("HOLD_LEGACY_SOURCE_SHA256_MISMATCH", host)
        actual_mode = stat.S_IMODE(path.stat().st_mode)
        if actual_mode != mode:
            raise InstallerError("HOLD_LEGACY_SOURCE_MODE_MISMATCH", host)
        legacy_identity = _git_repository_identity(path)
        if (
            legacy_identity["git_common_dir"] != product_identity["git_common_dir"]
            or legacy_identity["repository_identity_sha256"]
            != product_identity["repository_identity_sha256"]
        ):
            raise InstallerError("HOLD_LEGACY_REPOSITORY_MISMATCH", host)
        bindings[host] = {
            "path": str(path),
            "sha256": actual_hash,
            "mode": actual_mode,
            **legacy_identity,
        }
    return bindings


def _json_prepare(
    document: MutableMapping[str, Any],
    host: str,
    command_by_event: Mapping[str, str],
    *,
    force_migration: bool = False,
    legacy_bindings: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[MutableMapping[str, Any], bool]:
    product_root = _command_product_root(next(iter(command_by_event.values())))
    all_hosts = _managed_hosts(document, product_root, legacy_bindings)
    if all_hosts.intersection({"claude", "grok"}) == {"claude", "grok"}:
        raise InstallerError("HOLD_GROK_DOUBLE_EXECUTION", "direct_and_compatibility_entries")
    changed = False
    for event, command in command_by_event.items():
        value = _event_value(document, event)
        identities = [
            _command_identity(old, product_root)
            for _path, _obj, old in _walk_commands(value)
        ] if value is not None else []
        managed = [item for item in identities if item is not None and item[0] == host]
        legacy_matches = [
            old
            for _path, _obj, old in _walk_commands(value)
            if _legacy_command_matches(old, host, (legacy_bindings or {}).get(host))
        ]
        if len(legacy_matches) > 1:
            raise InstallerError("HOLD_DUPLICATE_CB_ENTRIES", f"{host}:{event}")
        if force_migration and any(
            _legacy_command_mentions(old, (legacy_bindings or {}).get(host))
            and not _legacy_command_matches(old, host, (legacy_bindings or {}).get(host))
            for _path, _obj, old in _walk_commands(value)
        ):
            raise InstallerError("HOLD_LEGACY_COMMAND_NOT_EXACT", f"{host}:{event}")
        if legacy_matches and not managed:
            managed = [(host, legacy_matches[0])]
        if len(managed) > 1:
            raise InstallerError("HOLD_DUPLICATE_CB_ENTRIES", f"{host}:{event}")
        foreign = {
            item[0]
            for item in identities
            if item is not None and item[0] in HOSTS and item[0] != host
        }
        if foreign.intersection({"claude", "grok"}) and host in {"claude", "grok"}:
            raise InstallerError("HOLD_GROK_DOUBLE_EXECUTION", f"{host}:{event}")
        if managed:
            if managed[0][1] != command:
                if not (force_migration and _legacy_command_matches(managed[0][1], host, (legacy_bindings or {}).get(host))):
                    raise InstallerError("HOLD_MANAGED_ENTRY_MIGRATION_REQUIRED", f"{host}:{event}")
                # Replace only the managed command string.  The surrounding
                # matcher and unrelated handler fields remain untouched.
                for _path, obj, old in _walk_commands(value):
                    if old == managed[0][1]:
                        obj["command"] = command
                        changed = True
            continue
        _append_event_json(document, host, event, command)
        changed = True
    return document, changed


def _yaml_insert(
    raw: bytes,
    document: Mapping[str, Any],
    host: str,
    command_by_event: Mapping[str, str],
    *,
    force_migration: bool = False,
    legacy_bindings: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[bytes, bool]:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - exercised on minimal Python images
        raise InstallerError("HOLD_CONFIG_FORMAT_UNAVAILABLE", "PyYAML is required for YAML fixtures") from exc
    text = raw.decode("utf-8")
    product_root = _command_product_root(next(iter(command_by_event.values())))
    for event, command in command_by_event.items():
        value = _event_value(document, event)
        identities = [_command_identity(old, product_root) for _p, _o, old in _walk_commands(value)] if value is not None else []
        managed = [item for item in identities if item is not None and item[0] == host]
        legacy_matches = [
            old
            for _path, _obj, old in _walk_commands(value)
            if _legacy_command_matches(old, host, (legacy_bindings or {}).get(host))
        ]
        if len(legacy_matches) > 1:
            raise InstallerError("HOLD_DUPLICATE_CB_ENTRIES", f"{host}:{event}")
        if force_migration and any(
            _legacy_command_mentions(old, (legacy_bindings or {}).get(host))
            and not _legacy_command_matches(old, host, (legacy_bindings or {}).get(host))
            for _path, _obj, old in _walk_commands(value)
        ):
            raise InstallerError("HOLD_LEGACY_COMMAND_NOT_EXACT", f"{host}:{event}")
        if legacy_matches and not managed:
            managed = [(host, legacy_matches[0])]
        if len(managed) > 1:
            raise InstallerError("HOLD_DUPLICATE_CB_ENTRIES", f"{host}:{event}")
        foreign = {
            item[0]
            for item in identities
            if item is not None and item[0] in HOSTS and item[0] != host
        }
        if foreign.intersection({"claude", "grok"}) and host in {"claude", "grok"}:
            raise InstallerError("HOLD_GROK_DOUBLE_EXECUTION", f"{host}:{event}")
        if managed:
            if managed[0][1] != command:
                if not (force_migration and _legacy_command_matches(managed[0][1], host, (legacy_bindings or {}).get(host))):
                    raise InstallerError("HOLD_MANAGED_ENTRY_MIGRATION_REQUIRED", f"{host}:{event}")
                # Replace only the legacy scalar command while preserving the
                # surrounding matcher/timeout/fail-closed settings.
                lines = text.splitlines(keepends=True)
                replaced = False
                binding = (legacy_bindings or {}).get(host)
                source = binding.get("path") if isinstance(binding, Mapping) else None
                for index, line in enumerate(lines):
                    if "command:" not in line or not isinstance(source, str):
                        continue
                    indent = len(line) - len(line.lstrip())
                    end = index + 1
                    while end < len(lines):
                        continuation = lines[end]
                        continuation_indent = len(continuation) - len(continuation.lstrip())
                        if continuation.strip() and continuation_indent <= indent:
                            break
                        end += 1
                    scalar = "".join(lines[index:end])
                    if source not in scalar:
                        continue
                    indent_text = line[: len(line) - len(line.lstrip())]
                    lines[index] = f"{indent_text}command: {json.dumps(command)}\n"
                    del lines[index + 1 : end]
                    replaced = True
                    break
                if not replaced:
                    raise InstallerError("HOLD_MANAGED_ENTRY_MIGRATION_REQUIRED", f"{host}:{event}")
                text = "".join(lines)
                document = _yaml_load_no_duplicates(text)
                changed = True
            continue
        lines = text.splitlines(keepends=True)
        hooks_index = next((i for i, line in enumerate(lines) if line.strip() == "hooks:" and not line.startswith(" ")), None)
        inline_empty_index = next(
            (
                i
                for i, line in enumerate(lines)
                if line.lstrip().startswith("hooks:")
                and line.lstrip()[len("hooks:") :].strip() in {"{}", "{ }"}
                and not line.startswith((" ", "\t"))
            ),
            None,
        )
        if inline_empty_index is not None:
            # ``hooks: {}`` is a valid empty mapping, but an indented event
            # cannot be appended beside the inline scalar.  Expand only the
            # empty form; non-empty inline mappings remain a deterministic
            # schema hold rather than being rewritten blindly.
            lines[inline_empty_index] = "hooks:\n"
            text = "".join(lines)
            hooks_index = inline_empty_index
        if hooks_index is None:
            if text and not text.endswith("\n"):
                text += "\n"
            text += "hooks:\n"
            hooks_index = len(text.splitlines(keepends=True)) - 1
            lines = text.splitlines(keepends=True)
        event_index = None
        for i in range(hooks_index + 1, len(lines)):
            stripped = lines[i].lstrip()
            if stripped and not lines[i].startswith((" ", "\t")):
                break
            if stripped.startswith(f"{event}:"):
                event_index = i
                break
        if event_index is None:
            insertion = hooks_index + 1
            while insertion < len(lines) and (not lines[insertion].strip() or lines[insertion].startswith((" ", "\t"))):
                insertion += 1
            block = [f"  {event}:\n", "    - matcher: terminal|execute_code|delegate_task\n", f"      command: {json.dumps(command)}\n", "      timeout: 30\n", "      fail_closed: true\n"]
        else:
            insertion = event_index + 1
            event_indent = len(lines[event_index]) - len(lines[event_index].lstrip())
            while insertion < len(lines):
                current = lines[insertion]
                if current.strip() and len(current) - len(current.lstrip()) <= event_indent:
                    break
                insertion += 1
            block = [f"{' ' * (event_indent + 2)}- matcher: terminal|execute_code|delegate_task\n", f"{' ' * (event_indent + 4)}command: {json.dumps(command)}\n", f"{' ' * (event_indent + 4)}timeout: 30\n", f"{' ' * (event_indent + 4)}fail_closed: true\n"]
        lines[insertion:insertion] = block
        text = "".join(lines)
        document = _yaml_load_no_duplicates(text)
    return text.encode("utf-8"), True


def _json_pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InstallerError("HOLD_CONFIG_DUPLICATE_KEY", key)
        result[key] = value
    return result


def _yaml_load_no_duplicates(text: str) -> Any:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - minimal runtime fallback
        raise InstallerError("HOLD_CONFIG_FORMAT_UNAVAILABLE", "PyYAML is unavailable") from exc

    class UniqueSafeLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader: Any, node: Any, deep: bool = False) -> dict[Any, Any]:
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise InstallerError("HOLD_CONFIG_DUPLICATE_KEY", str(key))
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    UniqueSafeLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
    )
    try:
        return yaml.load(text, Loader=UniqueSafeLoader)
    except InstallerError:
        raise
    except Exception as exc:
        # Never leak a raw PyYAML scanner/constructor traceback or message
        # into a plan/receipt surface.
        raise InstallerError("HOLD_CONFIG_PARSE_FAILURE", type(exc).__name__) from exc


def _load_toml_mapping(path: Path) -> tuple[dict[str, Any], bytes, bool]:
    if _credential_path(path):
        raise InstallerError("HOLD_CREDENTIAL_PATH", str(path))
    _validate_ancestor_custody(path, allow_missing=True)
    _check_regular(path, allow_missing=True, code_prefix="HOLD_CONFIG")
    if not path.exists():
        return {}, b"", False
    raw = path.read_bytes()
    try:
        loaded = tomllib.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise InstallerError("HOLD_CONFIG_PARSE_FAILURE", type(exc).__name__) from exc
    if not isinstance(loaded, dict):
        raise InstallerError("HOLD_CONFIG_ROOT_NOT_OBJECT", str(path))
    return loaded, raw, True


def _prepare_grok_compat(path: Path) -> dict[str, Any]:
    document, raw, existed = _load_toml_mapping(path)
    compat = document.get("compat")
    if compat is not None and not isinstance(compat, Mapping):
        raise InstallerError("HOLD_CONFIG_SCHEMA_INVALID", "compat must be a table")
    claude = compat.get("claude") if isinstance(compat, Mapping) else None
    if claude is not None and not isinstance(claude, Mapping):
        raise InstallerError("HOLD_CONFIG_SCHEMA_INVALID", "compat.claude must be a table")
    existing_hooks = claude.get("hooks") if isinstance(claude, Mapping) else None
    if existing_hooks is not None and not isinstance(existing_hooks, bool):
        raise InstallerError("HOLD_CONFIG_SCHEMA_INVALID", "compat.claude.hooks must be boolean")
    if existing_hooks is False:
        after = raw
        changed = False
    else:
        text = raw.decode("utf-8") if existed else ""
        lines = text.splitlines(keepends=True)
        section_index = next(
            (index for index, line in enumerate(lines) if line.strip() == "[compat.claude]"),
            None,
        )
        if section_index is None:
            if text and not text.endswith("\n"):
                text += "\n"
            text += "\n[compat.claude]\nhooks = false\n"
        else:
            section_end = section_index + 1
            while section_end < len(lines) and not lines[section_end].lstrip().startswith(("[", "[[")):
                section_end += 1
            hooks_index = next(
                (
                    index
                    for index in range(section_index + 1, section_end)
                    if "=" in lines[index]
                    and lines[index].split("=", 1)[0].strip() == "hooks"
                ),
                None,
            )
            if hooks_index is None:
                lines.insert(section_end, "hooks = false\n")
            else:
                line = lines[hooks_index]
                left, _right = line.split("=", 1)
                comment = ""
                if "#" in line.split("=", 1)[1]:
                    comment = " #" + line.split("#", 1)[1].strip()
                lines[hooks_index] = f"{left.rstrip()} = false{comment}\n"
            text = "".join(lines)
        try:
            parsed_after = tomllib.loads(text)
        except Exception as exc:
            raise InstallerError("HOLD_CONFIG_PARSE_FAILURE", type(exc).__name__) from exc
        compat_after = parsed_after.get("compat") if isinstance(parsed_after, dict) else None
        claude_after = compat_after.get("claude") if isinstance(compat_after, Mapping) else None
        if not isinstance(claude_after, Mapping) or claude_after.get("hooks") is not False:
            raise InstallerError("HOLD_CONFIG_SCHEMA_INVALID", "compat.claude.hooks not disabled")
        after = text.encode("utf-8")
        changed = after != raw
    return {
        "path": str(path),
        "kind": "toml",
        "existed": existed,
        "before_bytes": raw,
        "after_bytes": after,
        "changed": changed,
        "config_before_sha256": _hash_bytes(raw) if existed else ABSENT_SHA256,
        "config_after_sha256": _hash_bytes(after),
        "mode_before": stat.S_IMODE(path.stat().st_mode) if existed else None,
        "mode_after": stat.S_IMODE(path.stat().st_mode) if existed else 0o600,
        "backup_mode": stat.S_IMODE(path.stat().st_mode) if existed else 0o600,
        "commands": {},
        "events": [],
        "route": "grok_compat_disable_claude",
    }


def _load_document(path: Path) -> tuple[dict[str, Any], bytes, str, bool]:
    if _credential_path(path):
        raise InstallerError("HOLD_CREDENTIAL_PATH", str(path))
    _validate_ancestor_custody(path, allow_missing=True)
    exists = _check_regular(path, allow_missing=True, code_prefix="HOLD_CONFIG")
    if not exists:
        return {}, b"", "json" if path.suffix.lower() == ".json" else path.suffix.lower().lstrip("."), False
    raw = path.read_bytes()
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            try:
                loaded = json.loads(
                    raw.decode("utf-8"), object_pairs_hook=_json_pairs_no_duplicates
                )
            except InstallerError:
                raise
            except Exception as exc:
                raise InstallerError("HOLD_CONFIG_PARSE_FAILURE", type(exc).__name__) from exc
            kind = "json"
        elif suffix in {".yaml", ".yml"}:
            loaded = _yaml_load_no_duplicates(raw.decode("utf-8"))
            kind = "yaml"
        else:
            raise InstallerError("HOLD_CONFIG_FORMAT_UNSUPPORTED", str(path))
    except InstallerError:
        raise
    except Exception as exc:
        raise InstallerError("HOLD_CONFIG_PARSE_FAILURE", f"{path.name}:{type(exc).__name__}") from exc
    if loaded is None:
        loaded = {}
    if not isinstance(loaded, dict):
        raise InstallerError("HOLD_CONFIG_ROOT_NOT_OBJECT", str(path))
    return loaded, raw, kind, True


def _prepare_document(
    path: Path,
    host: str,
    binding: Mapping[str, Any],
    *,
    force_migration: bool = False,
    legacy_bindings: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    document, raw, kind, existed = _load_document(path)
    command_by_event = {event: _render_command(host, binding) for event in HOST_SPECS[host].events}
    if kind == "json":
        prepared, changed = _json_prepare(
            document,
            host,
            command_by_event,
            force_migration=force_migration,
            legacy_bindings=legacy_bindings,
        )
        after = (json.dumps(prepared, ensure_ascii=False, indent=2) + "\n").encode("utf-8") if changed or not existed else raw
    elif kind == "yaml":
        after, changed = _yaml_insert(
            raw,
            document,
            host,
            command_by_event,
            force_migration=force_migration,
            legacy_bindings=legacy_bindings,
        )
    else:  # pragma: no cover
        raise InstallerError("HOLD_CONFIG_FORMAT_UNSUPPORTED", str(path))
    return {
        "path": str(path),
        "kind": kind,
        "existed": existed,
        "before_bytes": raw,
        "after_bytes": after,
        "changed": changed and after != raw,
        "config_before_sha256": _hash_bytes(raw) if existed else ABSENT_SHA256,
        "config_after_sha256": _hash_bytes(after),
        "mode_before": stat.S_IMODE(path.stat().st_mode) if existed else None,
        "mode_after": stat.S_IMODE(path.stat().st_mode) if existed else 0o600,
        "backup_mode": stat.S_IMODE(path.stat().st_mode) if existed else 0o600,
        "commands": command_by_event,
    }


def _target_path(host: str, host_root: str | Path, config_path: str | Path) -> tuple[Path, Path]:
    root = _require_absolute(host_root, "HOLD_HOST_ROOT_PATH")
    _validate_ancestor_custody(root, allow_missing=False)
    if root.is_symlink():
        raise InstallerError("HOLD_HOST_ROOT_SYMLINK", str(root))
    if not root.is_dir():
        raise InstallerError("HOLD_HOST_ROOT_MISSING", str(root))
    config = _require_absolute(config_path, "HOLD_CONFIG_PATH")
    if not _is_under(config, root):
        raise InstallerError("HOLD_CONFIG_OUTSIDE_HOST_ROOT", str(config))
    _check_component_chain(config.parent, root, allow_missing=False)
    _check_regular(config, allow_missing=True, code_prefix="HOLD_CONFIG")
    _check_component_chain(config, root, allow_missing=True)
    if _credential_path(config):
        raise InstallerError("HOLD_CREDENTIAL_PATH", str(config))
    _validate_config_location(host, root, config)
    return root, config


def _grok_compat_target(
    grok_host_root: str | Path,
    compat_config: str | Path,
) -> tuple[Path, Path]:
    root = _require_absolute(grok_host_root, "HOLD_HOST_ROOT_PATH")
    _validate_ancestor_custody(root, allow_missing=False)
    if not root.is_dir() or root.is_symlink():
        raise InstallerError("HOLD_HOST_ROOT_INVALID", str(root))
    home = root.parent if root.name.lower() == ".grok" else root
    expected = home / ".grok" / "config.toml"
    config = _require_absolute(compat_config, "HOLD_GROK_COMPAT_CONFIG_PATH")
    if config != expected:
        raise InstallerError("HOLD_GROK_COMPAT_CONFIG_NONCANONICAL", str(config))
    if _credential_path(config):
        raise InstallerError("HOLD_CREDENTIAL_PATH", str(config))
    if config.suffix.lower() != ".toml":
        raise InstallerError("HOLD_CONFIG_KIND_MISMATCH", "Grok compatibility config requires TOML")
    _check_component_chain(config.parent, home, allow_missing=False)
    _check_regular(config, allow_missing=True, code_prefix="HOLD_CONFIG")
    return home, config


def _normalise_targets(
    host_roots: Mapping[str, str | Path] | None,
    config_paths: Mapping[str, str | Path] | None,
) -> dict[str, tuple[Path, Path]]:
    configs = dict(config_paths or {})
    roots = dict(host_roots or {})
    result: dict[str, tuple[Path, Path]] = {}
    for host, config_value in configs.items():
        if host not in HOSTS:
            raise InstallerError("HOLD_UNKNOWN_HOST", host)
        root_value = roots.get(host)
        if root_value is None:
            raise InstallerError("HOLD_HOST_ROOT_REQUIRED", host)
        result[host] = _target_path(host, root_value, config_value)
    for host in roots:
        if host not in HOSTS:
            raise InstallerError("HOLD_UNKNOWN_HOST", host)
    if set(roots) != set(configs):
        raise InstallerError("HOLD_HOST_CONFIG_SET_MISMATCH")
    if not result:
        raise InstallerError("HOLD_CONFIG_PATHS_REQUIRED", "at least one --config HOST=PATH is required")
    return result


def _compatibility_routes(
    targets: Mapping[str, tuple[Path, Path]],
    product_root: Path,
    *,
    grok_compat_enabled: bool = False,
    legacy_bindings: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, str | None]:
    def sibling_path(root: Path, vendor: str) -> tuple[Path, Path]:
        home = root.parent if root.name.lower() == f".{vendor}" else root
        path = home / f".{vendor}"
        if vendor == "claude":
            path = path / "settings.json"
        elif vendor == "grok":
            path = path / "hooks.json"
        return home, path

    def scan(vendor: str, root: Path, path: Path) -> set[str]:
        sibling_root, sibling = sibling_path(root, vendor)
        if sibling != path:
            sibling = path
        _validate_ancestor_custody(sibling.parent, allow_missing=True)
        if not sibling.parent.exists():
            return set()
        _target_path(vendor, sibling_root, sibling)
        if not path.exists():
            return set()
        document, _raw, _kind, _exists = _load_document(sibling)
        return _managed_hosts(document, product_root, legacy_bindings)

    routes = {host: None for host in targets}
    if "claude" in targets and "grok" in targets and targets["claude"][0] == targets["grok"][0]:
        root = targets["claude"][0]
        claude_hosts = scan("claude", root, targets["claude"][1])
        grok_hosts = scan("grok", root, targets["grok"][1])
        if claude_hosts.intersection({"claude", "grok"}) == {"claude", "grok"} or grok_hosts.intersection({"claude", "grok"}) == {"claude", "grok"}:
            routes["grok"] = "hold_grok_double_execution"
        elif "grok" in grok_hosts:
            routes["grok"] = None if grok_compat_enabled else "hold_grok_double_execution"
        else:
            # Grok discovers Claude settings by default.  One Claude-
            # compatible command is the only safe shared route; no Grok entry
            # is added to its own file in this case.
            routes["grok"] = None if grok_compat_enabled else "hold_grok_double_execution"
    if "grok" in targets and "claude" not in targets:
        # A separate Grok hook file is also discovered by Grok through the
        # Claude compatibility layer.  If a staged Claude settings file
        # already carries our command, route Grok through that one entry.
        root = targets["grok"][0]
        target_hosts = scan("grok", root, targets["grok"][1])
        _sibling_root, sibling = sibling_path(root, "claude")
        hosts = scan("claude", root, sibling)
        if target_hosts.intersection({"claude", "grok"}) == {"claude", "grok"} or hosts.intersection({"claude", "grok"}) == {"claude", "grok"}:
            routes["grok"] = "hold_grok_double_execution"
        elif "grok" in target_hosts and hosts.intersection({"claude", "grok"}):
            routes["grok"] = None if grok_compat_enabled else "hold_grok_double_execution"
        elif hosts.intersection({"claude", "grok"}):
            routes["grok"] = None if grok_compat_enabled else "hold_grok_double_execution"
    if "claude" in targets and "grok" not in targets:
        root = targets["claude"][0]
        _sibling_root, sibling = sibling_path(root, "grok")
        hosts = scan("grok", root, sibling)
        if hosts.intersection({"claude", "grok"}):
            routes["claude"] = "hold_grok_double_execution"
    return routes


def plan_install(
    *,
    product_root: str | Path,
    light_interpreter: str | Path,
    host_roots: Mapping[str, str | Path] | None = None,
    config_paths: Mapping[str, str | Path] | None = None,
    expected_source_sha256: str | None = None,
    run_id: str | None = None,
    grok_compat_config: str | Path | None = None,
    force_migration: bool = False,
    legacy_hook_sources: Mapping[str, str | Path] | None = None,
    legacy_hook_source_hashes: Mapping[str, str] | None = None,
    legacy_hook_source_modes: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    """Return a no-mutation plan for explicit staged host configurations."""

    try:
        binding = _runtime_binding(product_root, light_interpreter)
        legacy_bindings = _validate_legacy_bindings(
            force_migration=force_migration,
            product_root=binding["product_root"],
            legacy_hook_sources=legacy_hook_sources,
            legacy_hook_source_hashes=legacy_hook_source_hashes,
            legacy_hook_source_modes=legacy_hook_source_modes,
        )
        if expected_source_sha256 and expected_source_sha256 != binding["hook_source_sha256"]:
            raise InstallerError("HOLD_SOURCE_DRIFT", "approved source digest does not match")
        targets = _normalise_targets(host_roots, config_paths)
        if grok_compat_config is not None and "grok" not in targets:
            raise InstallerError("HOLD_GROK_COMPAT_UNEXPECTED")
        compat_target = (
            _grok_compat_target(targets["grok"][0], grok_compat_config)
            if grok_compat_config is not None
            else None
        )
        routes_without_compat = _compatibility_routes(
            targets,
            Path(binding["product_root"]),
            grok_compat_enabled=False,
            legacy_bindings=legacy_bindings,
        )
        if compat_target is not None and routes_without_compat.get("grok") != "hold_grok_double_execution":
            raise InstallerError("HOLD_GROK_COMPAT_UNEXPECTED")
        routes = _compatibility_routes(
            targets,
            Path(binding["product_root"]),
            grok_compat_enabled=compat_target is not None,
            legacy_bindings=legacy_bindings,
        )
    except InstallerError as exc:
        return {
            "schema": PLAN_SCHEMA,
            "mode": "plan",
            "status": "HOLD",
            "mutates": False,
            "promotion_allowed": False,
            "reason_code": exc.code,
            "detail": exc.detail,
            "claim_ceiling": CLAIM_CEILING,
        }
    plan_run_id = run_id or f"plan-{uuid.uuid4().hex}"
    try:
        _validate_run_id(plan_run_id)
    except InstallerError as exc:
        return {
            "schema": PLAN_SCHEMA,
            "mode": "plan",
            "status": "HOLD",
            "mutates": False,
            "promotion_allowed": False,
            "reason_code": exc.code,
            "detail": exc.detail,
            "claim_ceiling": CLAIM_CEILING,
        }
    rows: list[dict[str, Any]] = []
    overall = "PLAN"
    for host, (root, config) in targets.items():
        route = routes.get(host)
        if route == "claude_compatibility":
            rows.append({"host": host, "route": route, "status": "SKIP_DUPLICATE_ROUTE", "config_path": str(config), "host_root": str(root), "kind": HOST_SPECS[host].config_kind, "events": []})
            continue
        if route == "hold_grok_double_execution":
            overall = "HOLD"
            rows.append({"host": host, "route": route, "status": "HOLD", "reason_code": "HOLD_GROK_DOUBLE_EXECUTION", "config_path": str(config), "host_root": str(root)})
            continue
        try:
            prepared = _prepare_document(
                config,
                host,
                binding,
                force_migration=force_migration,
                legacy_bindings=legacy_bindings,
            )
            rows.append({
                "host": host,
                "route": "direct",
                "status": "WOULD_APPLY" if prepared["changed"] else "IDEMPOTENT",
                "host_root": str(root),
                "config_path": str(config),
                "events": list(HOST_SPECS[host].events),
                "kind": prepared["kind"],
                "config_before_sha256": prepared["config_before_sha256"],
                "config_after_sha256": prepared["config_after_sha256"],
                "backup_sha256": (
                    _hash_bytes(prepared["before_bytes"])
                    if prepared["existed"] and prepared["changed"]
                    else (_hash_bytes(b"constraintbox:absent:v1\n") if prepared["changed"] else ABSENT_SHA256)
                ),
                "mode_before": prepared["mode_before"],
                "mode_after": prepared["mode_after"],
                "backup_mode": prepared["backup_mode"],
                "existed_before": prepared["existed"],
                "commands": prepared["commands"],
            })
        except InstallerError as exc:
            overall = "HOLD"
            rows.append({"host": host, "status": "HOLD", "host_root": str(root), "config_path": str(config), "reason_code": exc.code, "detail": exc.detail})
    if compat_target is not None:
        try:
            compat_root, compat_path = compat_target
            prepared = _prepare_grok_compat(compat_path)
            rows.append(
                {
                    "host": "grok_compat",
                    "route": "grok_compat_disable_claude",
                    "status": "WOULD_APPLY" if prepared["changed"] else "IDEMPOTENT",
                    "host_root": str(compat_root),
                    "config_path": str(compat_path),
                    "kind": "toml",
                    "events": [],
                    "config_before_sha256": prepared["config_before_sha256"],
                    "config_after_sha256": prepared["config_after_sha256"],
                    "backup_sha256": (
                        _hash_bytes(prepared["before_bytes"])
                        if prepared["existed"] and prepared["changed"]
                        else (_hash_bytes(b"constraintbox:absent:v1\n") if prepared["changed"] else ABSENT_SHA256)
                    ),
                    "mode_before": prepared["mode_before"],
                    "mode_after": prepared["mode_after"],
                    "backup_mode": prepared["backup_mode"],
                    "existed_before": prepared["existed"],
                    "commands": {},
                }
            )
        except InstallerError as exc:
            overall = "HOLD"
            rows.append(
                {
                    "host": "grok_compat",
                    "route": "grok_compat_disable_claude",
                    "status": "HOLD",
                    "host_root": str(compat_target[0]),
                    "config_path": str(compat_target[1]),
                    "reason_code": exc.code,
                    "detail": exc.detail,
                }
            )
    result: dict[str, Any] = {
        "schema": PLAN_SCHEMA,
        "mode": "plan",
        "status": overall,
        "run_id": plan_run_id,
        "force_migration": force_migration,
        "legacy_sources": legacy_bindings,
        "grok_compat_config": str(compat_target[1]) if compat_target is not None else None,
        "mutates": False,
        "promotion_allowed": False,
        "product_root": binding["product_root"],
        "runtime_binding": binding,
        "source_sha256": binding["hook_source_sha256"],
        "config_before_sha256": {
            row["host"]: row.get("config_before_sha256")
            for row in rows
            if row.get("status") in {"WOULD_APPLY", "IDEMPOTENT"}
        },
        "config_after_sha256": {
            row["host"]: row.get("config_after_sha256")
            for row in rows
            if row.get("status") in {"WOULD_APPLY", "IDEMPOTENT"}
        },
        "backup_sha256": {
            row["host"]: row.get("backup_sha256")
            for row in rows
            if row.get("status") in {"WOULD_APPLY", "IDEMPOTENT"}
        },
        "targets": rows,
        "claim_ceiling": CLAIM_CEILING,
    }
    if overall == "HOLD":
        first_hold = next((row for row in rows if row.get("status") == "HOLD"), None)
        if first_hold is not None:
            result["reason_code"] = first_hold.get("reason_code", "HOLD_PLAN_TARGET")
    if routes.get("grok") == "hold_grok_double_execution" and compat_target is None:
        result["reason_code"] = "HOLD_GROK_DOUBLE_EXECUTION"
    result["plan_sha256"] = _self_digest(result, "plan_sha256")
    return result


def _validate_run_id(run_id: str) -> str:
    if not run_id or len(run_id) > 160 or any(
        char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
        for char in run_id
    ):
        raise InstallerError("HOLD_RUN_ID_INVALID", run_id)
    return run_id


def _run_directory(product_root: Path, run_id: str) -> Path:
    _validate_run_id(run_id)
    root = product_root / RUNS_RELATIVE / run_id
    _mkdir_chain(root, product_root)
    return root


def _write_receipt(path: Path, receipt: Mapping[str, Any]) -> dict[str, Any]:
    sealed = dict(receipt)
    sealed["receipt_sha256"] = _self_digest(sealed, "receipt_sha256")
    data = (json.dumps(sealed, ensure_ascii=True, indent=2) + "\n").encode("utf-8")
    atomic_write(path, data, mode=0o600)
    return sealed


def _plan_rows_by_host(plan: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = plan.get("targets")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise InstallerError("HOLD_PLAN_TARGETS_INVALID")
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        host = row.get("host")
        if not isinstance(host, str) or host not in TARGET_IDS or host in result:
            raise InstallerError("HOLD_PLAN_TARGETS_INVALID")
        result[host] = row
    return result


def _load_plan_artifact(
    *,
    plan_path: str | Path | None,
    plan: Mapping[str, Any] | None,
    expected_plan_sha256: str | None,
) -> tuple[dict[str, Any], str]:
    if not expected_plan_sha256:
        raise InstallerError("HOLD_EXPECTED_PLAN_SHA256_REQUIRED")
    if plan_path is None and plan is None:
        raise InstallerError("HOLD_PLAN_ARTIFACT_REQUIRED")
    loaded: Any = plan
    if plan_path is not None:
        path = _require_absolute(plan_path, "HOLD_PLAN_PATH")
        if _credential_path(path):
            raise InstallerError("HOLD_CREDENTIAL_PATH", str(path))
        _validate_ancestor_custody(path, allow_missing=False)
        _check_regular(path, allow_missing=False, code_prefix="HOLD_PLAN")
        try:
            loaded = json.loads(
                path.read_text(encoding="utf-8"),
                object_pairs_hook=_json_pairs_no_duplicates,
            )
        except InstallerError:
            raise
        except Exception as exc:
            raise InstallerError("HOLD_PLAN_PARSE_FAILURE", type(exc).__name__) from exc
    if not isinstance(loaded, Mapping):
        raise InstallerError("HOLD_PLAN_SCHEMA")
    sealed = dict(loaded)
    if sealed.get("schema") != PLAN_SCHEMA or sealed.get("mode") != "plan":
        raise InstallerError("HOLD_PLAN_SCHEMA")
    if sealed.get("status") != "PLAN" or sealed.get("mutates") is not False or sealed.get("promotion_allowed") is not False:
        raise InstallerError("HOLD_PLAN_NOT_APPLICABLE")
    digest = _require_self_digest(sealed, "plan_sha256", "HOLD_PLAN_SELF_DIGEST")
    if digest != expected_plan_sha256:
        raise InstallerError("HOLD_PLAN_EXPECTED_SHA256_MISMATCH")
    return sealed, digest


def _targets_from_plan(plan: Mapping[str, Any]) -> dict[str, tuple[Path, Path]]:
    rows = _plan_rows_by_host(plan)
    targets: dict[str, tuple[Path, Path]] = {}
    for host, row in rows.items():
        host_root = row.get("host_root")
        config_path = row.get("config_path")
        if not isinstance(host_root, str) or not isinstance(config_path, str):
            raise InstallerError("HOLD_PLAN_TARGET_INVALID", host)
        if host == "grok_compat":
            grok_row = rows.get("grok")
            if grok_row is None:
                raise InstallerError("HOLD_PLAN_TARGET_SET_MISMATCH")
            grok_root, _grok_path = _target_path(
                "grok", grok_row["host_root"], grok_row["config_path"]
            )
            targets[host] = _grok_compat_target(grok_root, config_path)
        else:
            targets[host] = _target_path(host, host_root, config_path)
    binding = plan.get("runtime_binding")
    if not isinstance(binding, Mapping):
        raise InstallerError("HOLD_PLAN_RUNTIME_BINDING_MISSING")
    _validate_plan_for_apply(
        plan,
        binding=binding,
        targets=targets,
        requested_run_id=str(plan.get("run_id")),
        replay=True,
    )
    return targets


def _validate_plan_for_apply(
    plan: Mapping[str, Any],
    *,
    binding: Mapping[str, Any],
    targets: Mapping[str, tuple[Path, Path]],
    requested_run_id: str | None,
    replay: bool = False,
    force_migration: bool | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Validate an authored plan as a precondition; never silently replan."""

    if plan.get("schema") != PLAN_SCHEMA:
        raise InstallerError("HOLD_PLAN_SCHEMA")
    if plan.get("mode") != "plan" or plan.get("status") != "PLAN":
        raise InstallerError("HOLD_PLAN_NOT_APPLICABLE")
    if plan.get("mutates") is not False or plan.get("promotion_allowed") is not False:
        raise InstallerError("HOLD_PLAN_AUTHORITY_FIELDS")
    planned_force = plan.get("force_migration", False)
    if not isinstance(planned_force, bool):
        raise InstallerError("HOLD_PLAN_FORCE_FIELD")
    if force_migration is not None and force_migration != planned_force:
        raise InstallerError("HOLD_PLAN_FORCE_MISMATCH")
    legacy_sources = plan.get("legacy_sources", {})
    if not isinstance(legacy_sources, Mapping):
        raise InstallerError("HOLD_PLAN_LEGACY_SOURCE_FIELD")
    legacy_paths = {
        host: value.get("path")
        for host, value in legacy_sources.items()
        if isinstance(value, Mapping)
    }
    legacy_hashes = {
        host: value.get("sha256")
        for host, value in legacy_sources.items()
        if isinstance(value, Mapping)
    }
    legacy_modes = {
        host: value.get("mode")
        for host, value in legacy_sources.items()
        if isinstance(value, Mapping)
    }
    legacy_bindings = _validate_legacy_bindings(
        force_migration=planned_force,
        product_root=binding["product_root"],
        legacy_hook_sources=legacy_paths,
        legacy_hook_source_hashes=legacy_hashes,
        legacy_hook_source_modes=legacy_modes,
    )
    if legacy_bindings != dict(legacy_sources):
        raise InstallerError("HOLD_PLAN_LEGACY_SOURCE_BINDING_STALE")
    plan_digest = _require_self_digest(plan, "plan_sha256", "HOLD_PLAN_SELF_DIGEST")
    plan_run_id = plan.get("run_id")
    if not isinstance(plan_run_id, str):
        raise InstallerError("HOLD_PLAN_RUN_ID_MISSING")
    _validate_run_id(plan_run_id)
    if requested_run_id is not None and requested_run_id != plan_run_id:
        raise InstallerError("HOLD_PLAN_RUN_ID_MISMATCH")
    if plan.get("product_root") != binding.get("product_root"):
        raise InstallerError("HOLD_PLAN_PRODUCT_ROOT_MISMATCH")
    if plan.get("source_sha256") != binding.get("hook_source_sha256"):
        raise InstallerError("HOLD_PLAN_SOURCE_MISMATCH")
    if plan.get("runtime_binding") != dict(binding):
        raise InstallerError("HOLD_PLAN_RUNTIME_BINDING_STALE")
    planned_rows = _plan_rows_by_host(plan)
    if set(planned_rows) != set(targets):
        raise InstallerError("HOLD_PLAN_TARGET_SET_MISMATCH")
    host_targets = {host: target for host, target in targets.items() if host in HOSTS}
    compat_target = targets.get("grok_compat")
    routes_without_compat = _compatibility_routes(
        host_targets,
        Path(binding["product_root"]),
        grok_compat_enabled=False,
        legacy_bindings=legacy_bindings,
    )
    if compat_target is not None and routes_without_compat.get("grok") != "hold_grok_double_execution":
        raise InstallerError("HOLD_GROK_COMPAT_UNEXPECTED")
    routes = _compatibility_routes(
        host_targets,
        Path(binding["product_root"]),
        grok_compat_enabled=compat_target is not None,
        legacy_bindings=legacy_bindings,
    )
    prepared_rows: list[dict[str, Any]] = []
    for host, (root, config) in host_targets.items():
        row = planned_rows[host]
        route = routes.get(host)
        expected_common = {
            "host": host,
            "host_root": str(root),
            "config_path": str(config),
            "kind": HOST_SPECS[host].config_kind,
        }
        if route == "claude_compatibility":
            expected_common.update({"route": route, "status": "SKIP_DUPLICATE_ROUTE", "events": []})
            if any(row.get(key) != value for key, value in expected_common.items()):
                raise InstallerError("HOLD_PLAN_TARGET_STALE", host)
            prepared_rows.append({"host": host, "route": route, "root": root, "config": config, "changed": False, "before_bytes": b"", "after_bytes": b""})
            continue
        if route == "hold_grok_double_execution":
            raise InstallerError("HOLD_GROK_DOUBLE_EXECUTION", host)
        if replay:
            if any(row.get(key) != value for key, value in expected_common.items()):
                raise InstallerError("HOLD_PLAN_TARGET_INVALID", host)
            required = (
                "route",
                "status",
                "events",
                "config_before_sha256",
                "config_after_sha256",
                "backup_sha256",
                "mode_before",
                "mode_after",
                "backup_mode",
                "existed_before",
                "commands",
            )
            if any(key not in row for key in required) or row.get("route") != "direct":
                raise InstallerError("HOLD_PLAN_TARGET_INVALID", host)
            if row.get("events") != list(HOST_SPECS[host].events):
                raise InstallerError("HOLD_PLAN_TARGET_INVALID", host)
            expected_commands = {
                event: _render_command(host, binding)
                for event in HOST_SPECS[host].events
            }
            if row.get("commands") != expected_commands:
                raise InstallerError("HOLD_PLAN_TARGET_INVALID", host)
            if row.get("kind") != HOST_SPECS[host].config_kind:
                raise InstallerError("HOLD_PLAN_TARGET_INVALID", host)
            if row.get("status") not in {"WOULD_APPLY", "IDEMPOTENT"}:
                raise InstallerError("HOLD_PLAN_TARGET_INVALID", host)
            prepared_rows.append({"host": host, "route": "direct", "root": root, "config": config, "changed": False, "before_bytes": b"", "after_bytes": b""})
            continue
        prepared = _prepare_document(
            config,
            host,
            binding,
            force_migration=planned_force,
            legacy_bindings=legacy_bindings,
        )
        expected_common.update(
            {
                "route": "direct",
                "status": "WOULD_APPLY" if prepared["changed"] else "IDEMPOTENT",
                "events": list(HOST_SPECS[host].events),
                "config_before_sha256": prepared["config_before_sha256"],
                "config_after_sha256": prepared["config_after_sha256"],
                    "backup_sha256": (
                        _hash_bytes(prepared["before_bytes"])
                        if prepared["existed"] and prepared["changed"]
                        else (_hash_bytes(b"constraintbox:absent:v1\n") if prepared["changed"] else ABSENT_SHA256)
                    ),
                "mode_before": prepared["mode_before"],
                "mode_after": prepared["mode_after"],
                "backup_mode": prepared["backup_mode"],
                "existed_before": prepared["existed"],
                "commands": prepared["commands"],
            }
        )
        if any(row.get(key) != value for key, value in expected_common.items()):
            raise InstallerError("HOLD_PLAN_STALE", host)
        prepared.update({"host": host, "root": root, "config": config, "route": "direct"})
        prepared_rows.append(prepared)
    if compat_target is not None:
        compat_root, compat_path = compat_target
        row = planned_rows.get("grok_compat")
        if row is None:
            raise InstallerError("HOLD_PLAN_TARGET_SET_MISMATCH")
        expected_common = {
            "host": "grok_compat",
            "host_root": str(compat_root),
            "config_path": str(compat_path),
            "kind": "toml",
            "route": "grok_compat_disable_claude",
            "events": [],
            "commands": {},
        }
        if any(row.get(key) != value for key, value in expected_common.items()):
            raise InstallerError("HOLD_PLAN_TARGET_INVALID", "grok_compat")
        if row.get("status") not in {"WOULD_APPLY", "IDEMPOTENT"}:
            raise InstallerError("HOLD_PLAN_TARGET_INVALID", "grok_compat")
        if replay:
            required = (
                "config_before_sha256",
                "config_after_sha256",
                "backup_sha256",
                "mode_before",
                "mode_after",
                "backup_mode",
                "existed_before",
            )
            if any(key not in row for key in required):
                raise InstallerError("HOLD_PLAN_TARGET_INVALID", "grok_compat")
            prepared_rows.append({"host": "grok_compat", "route": "grok_compat_disable_claude", "root": compat_root, "config": compat_path, "changed": False, "before_bytes": b"", "after_bytes": b""})
        else:
            prepared = _prepare_grok_compat(compat_path)
            expected_fields = {
                "config_before_sha256": prepared["config_before_sha256"],
                "config_after_sha256": prepared["config_after_sha256"],
                "backup_sha256": (
                    _hash_bytes(prepared["before_bytes"])
                    if prepared["existed"] and prepared["changed"]
                    else (_hash_bytes(b"constraintbox:absent:v1\n") if prepared["changed"] else ABSENT_SHA256)
                ),
                "mode_before": prepared["mode_before"],
                "mode_after": prepared["mode_after"],
                "backup_mode": prepared["backup_mode"],
                "existed_before": prepared["existed"],
            }
            if any(row.get(key) != value for key, value in expected_fields.items()):
                raise InstallerError("HOLD_PLAN_STALE", "grok_compat")
            prepared.update({"host": "grok_compat", "root": compat_root, "config": compat_path, "route": "grok_compat_disable_claude"})
            prepared_rows.append(prepared)
    return plan_digest, prepared_rows


def _trusted_records_from_plan(
    receipt: Mapping[str, Any],
    plan: Mapping[str, Any],
    targets: Mapping[str, tuple[Path, Path]],
) -> list[dict[str, Any]]:
    """Cross-check receipt rows, then derive every authorized path from plan."""

    plan_rows = _plan_rows_by_host(plan)
    receipt_rows = _plan_rows_by_host(receipt)
    if set(plan_rows) != set(receipt_rows) or set(plan_rows) != set(targets):
        raise InstallerError("HOLD_RECEIPT_TARGET_SET_MISMATCH")
    product = _require_absolute(str(plan["product_root"]), "HOLD_PRODUCT_ROOT_PATH")
    run_id = _validate_run_id(str(plan["run_id"]))
    trusted: list[dict[str, Any]] = []
    for host, (host_root, config) in targets.items():
        planned = plan_rows[host]
        received = receipt_rows[host]
        route = planned.get("route")
        expected_status = (
            "SKIPPED_COMPATIBILITY"
            if route == "claude_compatibility"
            else ("APPLIED" if planned.get("status") == "WOULD_APPLY" else "IDEMPOTENT")
        )
        expected_kind = "toml" if host == "grok_compat" else HOST_SPECS[host].config_kind
        expected_common = {
            "host": host,
            "host_root": str(host_root),
            "config_path": str(config),
            "kind": expected_kind,
            "route": route,
            "events": planned.get("events"),
            "commands": planned.get("commands", {}),
        }
        for key, value in expected_common.items():
            if received.get(key) != value:
                raise InstallerError("HOLD_RECEIPT_TARGET_BINDING_MISMATCH", host)
        if received.get("status") != expected_status:
            raise InstallerError("HOLD_RECEIPT_STATUS_MISMATCH", host)
        if route == "claude_compatibility":
            trusted.append(dict(received))
            continue
        for key in (
            "config_before_sha256",
            "config_after_sha256",
            "backup_sha256",
            "mode_before",
            "mode_after",
            "backup_mode",
            "existed_before",
        ):
            if received.get(key) != planned.get(key):
                raise InstallerError("HOLD_RECEIPT_TARGET_BINDING_MISMATCH", host)
        expected_backup = (
            product / RUNS_RELATIVE / run_id / "backups" / f"{host}.config.before"
            if planned.get("status") == "WOULD_APPLY"
            else None
        )
        received_backup = received.get("backup_path")
        if received_backup != (str(expected_backup) if expected_backup is not None else None):
            raise InstallerError("HOLD_RECEIPT_BACKUP_PATH_MISMATCH", host)
        expected_backup_marker = (
            planned.get("backup_sha256")
            if planned.get("existed_before")
            else ABSENT_SHA256
        )
        if received.get("backup_expected_sha256") != expected_backup_marker:
            raise InstallerError("HOLD_RECEIPT_BACKUP_BINDING_MISMATCH", host)
        row = dict(received)
        # Receipt values above were compared, but these paths/identities are
        # replaced with plan-derived values before any filesystem access.
        row.update(
            {
                "host": host,
                "host_root": str(host_root),
                "config_path": str(config),
                "backup_path": str(expected_backup) if expected_backup is not None else None,
                "commands": dict(planned.get("commands", {})),
                "route": route,
            }
        )
        trusted.append(row)
    return trusted


def _replay_existing_apply(
    run: Path,
    *,
    plan_digest: str,
    plan: Mapping[str, Any],
    binding: Mapping[str, Any],
    targets: Mapping[str, tuple[Path, Path]],
) -> dict[str, Any]:
    """Return an existing receipt without replacing its rollback authority."""

    receipt_path = run / "receipt.json"
    receipt = _load_receipt(
        receipt_path,
        expected_path=run / "receipt.json",
        expected_product_root=Path(str(plan["product_root"])),
    )
    if receipt.get("mode") != "apply":
        raise InstallerError("HOLD_RECEIPT_MODE")
    if receipt.get("mode") != "apply" or receipt.get("status") != "APPLIED":
        raise InstallerError("HOLD_RUN_ID_EXISTS")
    if receipt.get("run_id") != run.name or receipt.get("plan_sha256") != plan_digest:
        raise InstallerError("HOLD_RUN_ID_EXISTS")
    if receipt.get("product_root") != binding.get("product_root"):
        raise InstallerError("HOLD_RECEIPT_PRODUCT_ROOT_MISMATCH")
    if receipt.get("runtime_binding") != dict(binding):
        raise InstallerError("HOLD_RECEIPT_RUNTIME_BINDING_DRIFT")
    if receipt.get("source_sha256") != binding.get("hook_source_sha256"):
        raise InstallerError("HOLD_RECEIPT_SOURCE_SHA256_MISMATCH")
    trusted_records = _trusted_records_from_plan(receipt, plan, targets)
    results = [
        (
            {"host": record.get("host"), "status": "SKIPPED_COMPATIBILITY", "route": record.get("route")}
            if record.get("route") == "claude_compatibility"
            else _verify_record(record, Path(str(plan["product_root"])), str(plan["run_id"]))
        )
        for record in trusted_records
    ]
    if any(result.get("status") not in {"VERIFIED", "SKIPPED_COMPATIBILITY"} for result in results):
        raise InstallerError("HOLD_REPLAY_TARGET_DRIFT")
    receipt = dict(receipt)
    receipt["replayed"] = True
    receipt["receipt_path"] = str(receipt_path)
    return receipt


def apply_install(
    *,
    product_root: str | Path,
    light_interpreter: str | Path,
    host_roots: Mapping[str, str | Path] | None = None,
    config_paths: Mapping[str, str | Path] | None = None,
    expected_source_sha256: str | None = None,
    plan: Mapping[str, Any] | None = None,
    plan_path: str | Path | None = None,
    run_id: str | None = None,
    grok_compat_config: str | Path | None = None,
    force_migration: bool | None = None,
    legacy_hook_sources: Mapping[str, str | Path] | None = None,
    legacy_hook_source_hashes: Mapping[str, str] | None = None,
    legacy_hook_source_modes: Mapping[str, int] | None = None,
    fail_after_host: str | None = None,
) -> dict[str, Any]:
    """Apply a preflighted plan with backups and atomic writes."""

    if plan_path is not None:
        plan_file = _require_absolute(plan_path, "HOLD_PLAN_PATH")
        _validate_ancestor_custody(plan_file, allow_missing=False)
        _check_regular(plan_file, allow_missing=False, code_prefix="HOLD_PLAN")
        try:
            loaded_plan = json.loads(
                plan_file.read_text(encoding="utf-8"),
                object_pairs_hook=_json_pairs_no_duplicates,
            )
        except InstallerError:
            raise
        except Exception as exc:
            raise InstallerError("HOLD_PLAN_PARSE_FAILURE", type(exc).__name__) from exc
        if not isinstance(loaded_plan, Mapping):
            raise InstallerError("HOLD_PLAN_SCHEMA")
        plan = loaded_plan
    if plan is None:
        raise InstallerError("HOLD_PLAN_REQUIRED")
    if not isinstance(plan, Mapping):
        raise InstallerError("HOLD_PLAN_SCHEMA")
    if legacy_hook_sources or legacy_hook_source_hashes or legacy_hook_source_modes:
        supplied_legacy = _validate_legacy_bindings(
            force_migration=bool(plan.get("force_migration", False)),
            product_root=product_root,
            legacy_hook_sources=legacy_hook_sources,
            legacy_hook_source_hashes=legacy_hook_source_hashes,
            legacy_hook_source_modes=legacy_hook_source_modes,
        )
        if supplied_legacy != plan.get("legacy_sources", {}):
            raise InstallerError("HOLD_PLAN_LEGACY_SOURCE_MISMATCH")
    plan_compat = plan.get("grok_compat_config")
    if grok_compat_config is not None:
        supplied_compat = _require_absolute(grok_compat_config, "HOLD_GROK_COMPAT_CONFIG_PATH")
        if plan_compat != str(supplied_compat):
            raise InstallerError("HOLD_PLAN_COMPAT_CONFIG_MISMATCH")
    binding = _runtime_binding(product_root, light_interpreter)
    if expected_source_sha256 and expected_source_sha256 != binding["hook_source_sha256"]:
        raise InstallerError("HOLD_SOURCE_DRIFT", "approved source digest does not match")
    targets = _normalise_targets(host_roots, config_paths)
    if plan_compat is not None:
        if not isinstance(plan_compat, str) or "grok" not in targets:
            raise InstallerError("HOLD_PLAN_COMPAT_CONFIG_INVALID")
        compat_root, compat_path = _grok_compat_target(targets["grok"][0], plan_compat)
        targets["grok_compat"] = (compat_root, compat_path)
    elif "grok_compat" in targets:
        raise InstallerError("HOLD_PLAN_COMPAT_CONFIG_INVALID")
    product = Path(binding["product_root"])
    run_candidate = product / RUNS_RELATIVE / str(plan.get("run_id"))
    replay = run_candidate.exists()
    plan_digest, prepared_rows = _validate_plan_for_apply(
        plan,
        binding=binding,
        targets=targets,
        requested_run_id=run_id,
        replay=replay,
        force_migration=force_migration,
    )
    run_id = str(plan["run_id"])
    run = product / RUNS_RELATIVE / run_id
    _validate_ancestor_custody(run, allow_missing=True)
    if run.exists():
        return _replay_existing_apply(
            run,
            plan_digest=plan_digest,
            plan=plan,
            binding=binding,
            targets=targets,
        )
    run = _run_directory(product, run_id)
    backups = run / "backups"
    _mkdir_chain(backups, product)
    records: list[dict[str, Any]] = []
    # Back up every file that will change before changing any target.
    for row in prepared_rows:
        host = row["host"]
        config: Path = row["config"]
        if row.get("route") == "claude_compatibility":
            records.append({"host": host, "status": "SKIPPED_COMPATIBILITY", "route": row["route"], "config_path": str(config), "host_root": str(row["root"]), "kind": HOST_SPECS[host].config_kind, "events": [], "commands": {}})
            continue
        backup_path = backups / f"{host}.config.before"
        _check_component_chain(backup_path, product, allow_missing=True)
        backup_sha = ABSENT_SHA256 if not row["existed"] else _hash_bytes(row["before_bytes"])
        if row["changed"]:
            if row["existed"]:
                atomic_write(backup_path, row["before_bytes"], mode=stat.S_IMODE(config.stat().st_mode))
            else:
                atomic_write(backup_path, b"constraintbox:absent:v1\n", mode=0o600)
            recorded_backup_sha = _hash_file(backup_path)
        else:
            backup_path = None
            recorded_backup_sha = ABSENT_SHA256
        records.append({
            "host": host,
            "status": "APPLY_PENDING" if row["changed"] else "IDEMPOTENT",
            "route": row["route"],
            "config_path": str(config),
            "host_root": str(row["root"]),
            "kind": row["kind"],
            "events": list(HOST_SPECS[host].events) if host in HOSTS else [],
            "commands": row["commands"],
            "config_before_sha256": row["config_before_sha256"],
            "config_after_sha256": row["config_after_sha256"],
            "backup_path": str(backup_path) if backup_path else None,
            "backup_sha256": recorded_backup_sha,
            "backup_expected_sha256": backup_sha if row["changed"] else ABSENT_SHA256,
            "mode_before": row["mode_before"],
            "mode_after": row["mode_after"],
            "backup_mode": row["backup_mode"],
            "existed_before": row["existed"],
            "before_bytes_internal": row["before_bytes"],
            "after_bytes_internal": row["after_bytes"],
        })
    changed = [record for record in records if record["status"] == "APPLY_PENDING"]
    applied: list[dict[str, Any]] = []
    try:
        for record in changed:
            config = Path(record["config_path"])
            _check_regular(config, allow_missing=not record["existed_before"], code_prefix="HOLD_CONFIG")
            # Register the target before the replace so a directory-fsync or
            # post-replace interruption also enters the compensating restore.
            applied.append(record)
            if record["existed_before"]:
                atomic_write(config, record["after_bytes_internal"], mode=record["mode_before"])
            else:
                atomic_write(config, record["after_bytes_internal"], mode=0o600)
            record["status"] = "APPLIED"
            if fail_after_host and record["host"] == fail_after_host:
                raise OSError("injected interrupted write")
    except Exception as exc:
        # Restore from the in-memory before image, not from an untrusted path.
        for record in reversed(applied):
            config = Path(record["config_path"])
            with contextlib.suppress(Exception):
                if record["existed_before"]:
                    atomic_write(config, record["before_bytes_internal"], mode=record["mode_before"])
                elif config.exists() and not config.is_symlink():
                    config.unlink()
                    _fsync_directory(config.parent)
        raise InstallerError("HOLD_APPLY_INTERRUPTED", type(exc).__name__) from exc
    receipt_records: list[dict[str, Any]] = []
    for record in records:
        safe_record = dict(record)
        safe_record.pop("before_bytes_internal", None)
        safe_record.pop("after_bytes_internal", None)
        receipt_records.append(safe_record)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "installer_schema": SCHEMA,
        "mode": "apply",
        "status": "APPLIED" if changed else "IDEMPOTENT",
        "plan_sha256": plan_digest,
        "force_migration": plan.get("force_migration", False),
        "legacy_sources": plan.get("legacy_sources", {}),
        "grok_compat_config": plan.get("grok_compat_config"),
        "run_id": run.name,
        "product_root": binding["product_root"],
        "runtime_binding": binding,
        "source_sha256": binding["hook_source_sha256"],
        "config_before_sha256": {
            record["host"]: record.get("config_before_sha256")
            for record in records
            if record.get("route") != "claude_compatibility"
        },
        "config_after_sha256": {
            record["host"]: record.get("config_after_sha256")
            for record in records
            if record.get("route") != "claude_compatibility"
        },
        "backup_sha256": {
            record["host"]: record.get("backup_sha256")
            for record in records
            if record.get("route") != "claude_compatibility"
        },
        "targets": receipt_records,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }
    receipt_path = run / "receipt.json"
    receipt["receipt_path"] = str(receipt_path)
    try:
        sealed_receipt = _write_receipt(receipt_path, receipt)
    except Exception as exc:
        # A config install without a durable receipt is not an install.  Keep
        # the backup directory as forensic/rollback evidence, but compensate
        # every changed config before reporting the write failure.
        for record in reversed(applied):
            config = Path(record["config_path"])
            with contextlib.suppress(Exception):
                if record["existed_before"]:
                    atomic_write(config, record["before_bytes_internal"], mode=record["mode_before"])
                elif config.exists() and not config.is_symlink():
                    config.unlink()
                    _fsync_directory(config.parent)
        raise InstallerError("HOLD_RECEIPT_WRITE_FAILED", type(exc).__name__) from exc
    for record in records:
        record.pop("before_bytes_internal", None)
        record.pop("after_bytes_internal", None)
    return sealed_receipt


def _load_receipt(
    receipt_path: str | Path,
    *,
    expected_receipt_sha256: str | None = None,
    expected_path: Path | None = None,
    expected_product_root: Path | None = None,
) -> dict[str, Any]:
    path = _require_absolute(receipt_path, "HOLD_RECEIPT_PATH")
    if _credential_path(path):
        raise InstallerError("HOLD_CREDENTIAL_PATH", str(path))
    _validate_ancestor_custody(path, allow_missing=False)
    _check_regular(path, allow_missing=False, code_prefix="HOLD_RECEIPT")
    try:
        loaded = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_json_pairs_no_duplicates
        )
    except InstallerError:
        raise
    except Exception as exc:
        raise InstallerError("HOLD_RECEIPT_PARSE_FAILURE", type(exc).__name__) from exc
    if not isinstance(loaded, dict) or loaded.get("schema") != RECEIPT_SCHEMA:
        raise InstallerError("HOLD_RECEIPT_SCHEMA", str(path))
    digest = _require_self_digest(loaded, "receipt_sha256", "HOLD_RECEIPT_SELF_DIGEST")
    if expected_receipt_sha256 is not None and digest != expected_receipt_sha256:
        raise InstallerError("HOLD_RECEIPT_EXPECTED_SHA256_MISMATCH")
    if expected_path is not None:
        expected_path = _canonical_alias(expected_path)
        if path != expected_path:
            raise InstallerError("HOLD_RECEIPT_PATH_MISMATCH")
        if expected_product_root is None:
            raise InstallerError("HOLD_RECEIPT_PRODUCT_ROOT_REQUIRED")
        # The caller-supplied plan controls the trusted product boundary; this
        # check only validates custody of the already-derived path.
        _check_component_chain(
            expected_path, _canonical_alias(expected_product_root), allow_missing=False
        )
    loaded["receipt_path"] = str(path)
    return loaded


def _verify_record(
    record: Mapping[str, Any], product_root: Path, run_id: str | None = None
) -> dict[str, Any]:
    if record.get("route") not in {"direct", "grok_compat_disable_claude"}:
        return {
            "host": record.get("host"),
            "status": "HOLD",
            "reason_code": "HOLD_UNKNOWN_TARGET_ROUTE",
        }
    config = Path(str(record["config_path"]))
    try:
        host_root = _require_absolute(str(record["host_root"]), "HOLD_HOST_ROOT_PATH")
        _check_regular(config, allow_missing=True, code_prefix="HOLD_CONFIG")
        _check_component_chain(config, host_root, allow_missing=True)
    except InstallerError as exc:
        return {"host": record.get("host"), "status": "HOLD", "reason_code": exc.code}
    if _credential_path(config):
        return {"host": record.get("host"), "status": "HOLD", "reason_code": "HOLD_CREDENTIAL_PATH"}
    try:
        exists = _check_regular(config, allow_missing=True, code_prefix="HOLD_CONFIG")
    except InstallerError as exc:
        return {"host": record.get("host"), "status": "HOLD", "reason_code": exc.code}
    current = _hash_file(config) if exists else ABSENT_SHA256
    expected = record.get("config_after_sha256")
    if current != expected:
        return {"host": record.get("host"), "status": "HOLD", "reason_code": "HOLD_TARGET_TAMPERED", "config_sha256": current, "expected_sha256": expected}
    current_mode = stat.S_IMODE(config.stat().st_mode) if exists else None
    if current_mode != record.get("mode_after"):
        return {"host": record.get("host"), "status": "HOLD", "reason_code": "HOLD_CONFIG_MODE_TAMPERED", "mode": current_mode, "expected_mode": record.get("mode_after")}
    backup_path = record.get("backup_path")
    if backup_path:
        backup = Path(str(backup_path))
        if not _is_under(backup, product_root):
            return {"host": record.get("host"), "status": "HOLD", "reason_code": "HOLD_BACKUP_OUTSIDE_PRODUCT"}
        if run_id is not None:
            expected_backup = product_root / RUNS_RELATIVE / run_id / "backups" / f"{record.get('host')}.config.before"
            if backup != expected_backup:
                return {"host": record.get("host"), "status": "HOLD", "reason_code": "HOLD_BACKUP_PATH_MISMATCH"}
        try:
            _check_regular(backup, allow_missing=False, code_prefix="HOLD_BACKUP")
            _check_component_chain(backup, product_root, allow_missing=False)
            backup_sha = _hash_file(backup)
        except InstallerError as exc:
            return {"host": record.get("host"), "status": "HOLD", "reason_code": exc.code}
        if backup_sha != record.get("backup_sha256"):
            return {"host": record.get("host"), "status": "HOLD", "reason_code": "HOLD_BACKUP_TAMPERED"}
        if stat.S_IMODE(backup.stat().st_mode) != record.get("backup_mode"):
            return {"host": record.get("host"), "status": "HOLD", "reason_code": "HOLD_BACKUP_MODE_TAMPERED"}
    try:
        if record.get("kind") == "toml":
            document, _raw, _existed = _load_toml_mapping(config)
            compat = document.get("compat")
            claude = compat.get("claude") if isinstance(compat, Mapping) else None
            if not isinstance(claude, Mapping) or claude.get("hooks") is not False:
                return {"host": record.get("host"), "status": "HOLD", "reason_code": "HOLD_GROK_COMPAT_NOT_DISABLED"}
        else:
            document, _raw, _kind, _existed = _load_document(config)
        host = str(record.get("host"))
        commands = record.get("commands")
        if isinstance(commands, Mapping):
            for event, expected_command in commands.items():
                value = _event_value(document, str(event))
                identities = [
                    item
                    for item in (_command_identity(old, product_root) for _p, _o, old in _walk_commands(value))
                    if item is not None and item[0] == host
                ]
                if len(identities) != 1 or identities[0][1] != expected_command:
                    return {"host": host, "status": "HOLD", "reason_code": "HOLD_MANAGED_ENTRY_MISSING", "event": event}
    except InstallerError as exc:
        return {"host": record.get("host"), "status": "HOLD", "reason_code": exc.code}
    return {"host": record.get("host"), "status": "VERIFIED", "config_sha256": current, "route": record.get("route")}


def _load_authorized_plan_receipt(
    *,
    receipt_path: str | Path,
    plan_path: str | Path | None,
    plan: Mapping[str, Any] | None,
    expected_receipt_sha256: str | None,
    expected_plan_sha256: str | None,
    product_root: str | Path | None,
    light_interpreter: str | Path | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, tuple[Path, Path]], dict[str, Any], list[dict[str, Any]]]:
    trusted_plan, plan_digest = _load_plan_artifact(
        plan_path=plan_path,
        plan=plan,
        expected_plan_sha256=expected_plan_sha256,
    )
    binding = trusted_plan.get("runtime_binding")
    if not isinstance(binding, Mapping):
        raise InstallerError("HOLD_PLAN_RUNTIME_BINDING_MISSING")
    targets = _targets_from_plan(trusted_plan)
    product = _require_absolute(str(binding["product_root"]), "HOLD_PRODUCT_ROOT_PATH")
    if product_root is not None and _require_absolute(product_root, "HOLD_PRODUCT_ROOT_PATH") != product:
        raise InstallerError("HOLD_PRODUCT_ROOT_MISMATCH")
    current_binding = _runtime_binding(
        str(binding["product_root"]),
        light_interpreter or str(binding["light_interpreter_lexical"]),
    )
    if current_binding != dict(binding):
        raise InstallerError("HOLD_RUNTIME_BINDING_DRIFT")
    run_id = _validate_run_id(str(trusted_plan["run_id"]))
    expected_path = product / RUNS_RELATIVE / run_id / "receipt.json"
    supplied_path = _require_absolute(receipt_path, "HOLD_RECEIPT_PATH")
    if supplied_path != expected_path:
        raise InstallerError("HOLD_RECEIPT_PATH_MISMATCH")
    receipt = _load_receipt(
        supplied_path,
        expected_receipt_sha256=expected_receipt_sha256,
        expected_path=expected_path,
        expected_product_root=product,
    )
    if receipt.get("receipt_path") != str(expected_path):
        raise InstallerError("HOLD_RECEIPT_PATH_MISMATCH")
    if receipt.get("plan_sha256") != plan_digest:
        raise InstallerError("HOLD_RECEIPT_PLAN_SHA256_MISMATCH")
    if receipt.get("run_id") != run_id or receipt.get("product_root") != str(product):
        raise InstallerError("HOLD_RECEIPT_BINDING_MISMATCH")
    if receipt.get("force_migration", False) != trusted_plan.get("force_migration", False):
        raise InstallerError("HOLD_RECEIPT_FORCE_BINDING_MISMATCH")
    if receipt.get("legacy_sources", {}) != trusted_plan.get("legacy_sources", {}):
        raise InstallerError("HOLD_RECEIPT_LEGACY_SOURCE_BINDING_MISMATCH")
    if receipt.get("grok_compat_config") != trusted_plan.get("grok_compat_config"):
        raise InstallerError("HOLD_RECEIPT_COMPAT_BINDING_MISMATCH")
    if receipt.get("runtime_binding") != dict(binding):
        raise InstallerError("HOLD_RECEIPT_RUNTIME_BINDING_DRIFT")
    trusted_records = _trusted_records_from_plan(receipt, trusted_plan, targets)
    plan_rows = _plan_rows_by_host(trusted_plan)
    for field in ("config_before_sha256", "config_after_sha256", "backup_sha256"):
        expected_map = {
            host: row.get(field)
            for host, row in plan_rows.items()
            if row.get("route") != "claude_compatibility"
        }
        if receipt.get(field) != expected_map:
            raise InstallerError("HOLD_RECEIPT_HASH_BINDING_MISMATCH", field)
    return trusted_plan, dict(binding), targets, receipt, trusted_records


def verify_install(
    *,
    receipt_path: str | Path,
    plan_path: str | Path | None = None,
    plan: Mapping[str, Any] | None = None,
    expected_receipt_sha256: str | None = None,
    expected_plan_sha256: str | None = None,
    product_root: str | Path | None = None,
    light_interpreter: str | Path | None = None,
) -> dict[str, Any]:
    """Verify target, backup, source, venv, and receipt bindings."""

    if not expected_receipt_sha256:
        raise InstallerError("HOLD_EXPECTED_RECEIPT_SHA256_REQUIRED")
    try:
        trusted_plan, binding, targets, receipt, trusted_records = _load_authorized_plan_receipt(
            receipt_path=receipt_path,
            plan_path=plan_path,
            plan=plan,
            expected_receipt_sha256=expected_receipt_sha256,
            expected_plan_sha256=expected_plan_sha256,
            product_root=product_root,
            light_interpreter=light_interpreter,
        )
    except InstallerError as exc:
        if exc.code in {"HOLD_RUNTIME_BINDING_DRIFT", "HOLD_HOOK_SCRIPT_NOT_EXECUTABLE"}:
            return {
                "schema": RECEIPT_SCHEMA,
                "mode": "verify",
                "status": "HOLD",
                "reason_code": exc.code,
                "receipt_path": str(receipt_path),
                "claim_ceiling": CLAIM_CEILING,
                "promotion_allowed": False,
            }
        raise
    if receipt.get("mode") != "apply":
        raise InstallerError("HOLD_RECEIPT_MODE")
    rows = [
        (
            {"host": record.get("host"), "status": "SKIPPED_COMPATIBILITY", "route": record.get("route")}
            if record.get("route") == "claude_compatibility"
            else _verify_record(record, Path(str(trusted_plan["product_root"])), str(trusted_plan["run_id"]))
        )
        for record in trusted_records
    ]
    ok = all(row.get("status") in {"VERIFIED", "SKIPPED_COMPATIBILITY"} for row in rows)
    return {
        "schema": RECEIPT_SCHEMA,
        "mode": "verify",
        "status": "VERIFIED" if ok else "HOLD",
        "receipt_path": str(receipt_path),
        "runtime_binding_sha256": binding["product_binding_sha256"],
        "targets": rows,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }


def rollback_install(
    *,
    receipt_path: str | Path,
    plan_path: str | Path | None = None,
    plan: Mapping[str, Any] | None = None,
    expected_receipt_sha256: str | None = None,
    expected_plan_sha256: str | None = None,
    product_root: str | Path | None = None,
    light_interpreter: str | Path | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Restore only paths derived from an explicitly verified plan artifact."""

    if force:
        raise InstallerError("HOLD_FORCE_ROLLBACK_DISABLED")
    if not expected_receipt_sha256:
        raise InstallerError("HOLD_EXPECTED_RECEIPT_SHA256_REQUIRED")
    trusted_plan, _binding, targets, receipt, trusted_records = _load_authorized_plan_receipt(
        receipt_path=receipt_path,
        plan_path=plan_path,
        plan=plan,
        expected_receipt_sha256=expected_receipt_sha256,
        expected_plan_sha256=expected_plan_sha256,
        product_root=product_root,
        light_interpreter=light_interpreter,
    )
    if receipt.get("mode") != "apply" or receipt.get("status") != "APPLIED":
        raise InstallerError("HOLD_ROLLBACK_RECEIPT_NOT_APPLIED")
    product_root = _require_absolute(str(trusted_plan["product_root"]), "HOLD_PRODUCT_ROOT_PATH")
    pending: list[tuple[Mapping[str, Any], Path, bytes, bytes | None, int]] = []
    for record in trusted_records:
        if record.get("route") == "claude_compatibility" or not record.get("backup_path"):
            continue
        config = Path(str(record["config_path"]))
        host_root = _require_absolute(str(record["host_root"]), "HOLD_HOST_ROOT_PATH")
        _check_regular(config, allow_missing=True, code_prefix="HOLD_CONFIG")
        _check_component_chain(config, host_root, allow_missing=True)
        exists = _check_regular(config, allow_missing=True, code_prefix="HOLD_CONFIG")
        current = _hash_file(config) if exists else ABSENT_SHA256
        if current != record.get("config_after_sha256"):
            raise InstallerError("HOLD_TARGET_TAMPERED", str(config))
        if (stat.S_IMODE(config.stat().st_mode) if exists else None) != record.get("mode_after"):
            raise InstallerError("HOLD_CONFIG_MODE_TAMPERED", str(config))
        backup = Path(str(record["backup_path"]))
        _check_regular(backup, allow_missing=False, code_prefix="HOLD_BACKUP")
        _check_component_chain(backup, product_root, allow_missing=False)
        if _hash_file(backup) != record.get("backup_sha256"):
            raise InstallerError("HOLD_BACKUP_TAMPERED", str(backup))
        if stat.S_IMODE(backup.stat().st_mode) != record.get("backup_mode"):
            raise InstallerError("HOLD_BACKUP_MODE_TAMPERED", str(backup))
        current_bytes = config.read_bytes() if exists else None
        current_mode = stat.S_IMODE(config.stat().st_mode) if exists else 0o600
        pending.append((record, config, backup.read_bytes(), current_bytes, current_mode))
    # All custody, target hashes, and backup hashes are checked before the
    # first restore.  A later tamper therefore cannot leave an earlier host
    # partially rolled back.
    changed: list[dict[str, Any]] = []
    applied: list[tuple[Path, bytes | None, int]] = []
    try:
        for record, config, backup_bytes, current_bytes, current_mode in pending:
            applied.append((config, current_bytes, current_mode))
            if record.get("existed_before"):
                atomic_write(config, backup_bytes, mode=int(record.get("mode_before", 0o600)))
            else:
                if config.exists():
                    _check_regular(config, allow_missing=False, code_prefix="HOLD_CONFIG")
                    config.unlink()
                    _fsync_directory(config.parent)
            changed.append({"host": record.get("host"), "config_path": str(config), "status": "ROLLED_BACK"})
    except Exception as exc:
        for config, current_bytes, current_mode in reversed(applied):
            with contextlib.suppress(Exception):
                if current_bytes is None:
                    if config.exists() and not config.is_symlink():
                        config.unlink()
                        _fsync_directory(config.parent)
                else:
                    atomic_write(config, current_bytes, mode=current_mode)
        raise InstallerError("HOLD_ROLLBACK_INTERRUPTED", type(exc).__name__) from exc
    return {
        "schema": RECEIPT_SCHEMA,
        "mode": "rollback",
        "status": "ROLLED_BACK" if changed else "IDEMPOTENT",
        "receipt_path": str(receipt_path),
        "targets": changed,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }


def _parse_pairs(values: Sequence[str] | None, flag: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values or ():
        if "=" not in value:
            raise InstallerError("HOLD_ARGUMENT", f"{flag} requires HOST=PATH")
        host, path = value.split("=", 1)
        if host not in HOSTS or not path:
            raise InstallerError("HOLD_ARGUMENT", f"invalid {flag}: {value}")
        if host in result:
            raise InstallerError("HOLD_DUPLICATE_HOST_ARGUMENT", host)
        result[host] = path
    return result


def _parse_modes(values: Sequence[str] | None, flag: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values or ():
        if "=" not in value:
            raise InstallerError("HOLD_ARGUMENT", f"{flag} requires HOST=MODE")
        host, raw_mode = value.split("=", 1)
        if host not in HOSTS or host in result:
            raise InstallerError("HOLD_ARGUMENT", f"invalid {flag}: {value}")
        try:
            mode = int(raw_mode, 0) if raw_mode.startswith("0o") else int(raw_mode, 8)
        except ValueError as exc:
            raise InstallerError("HOLD_ARGUMENT", f"invalid {flag}: {value}") from exc
        result[host] = mode
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", nargs="?", choices=("plan", "apply", "verify", "rollback"), default=None)
    parser.add_argument("--mode", dest="mode_option", choices=("plan", "apply", "verify", "rollback"))
    parser.add_argument("--product-root")
    parser.add_argument("--light-interpreter")
    parser.add_argument("--host-root", action="append", default=[])
    parser.add_argument("--config", action="append", default=[])
    parser.add_argument("--expected-source-sha256")
    parser.add_argument("--expected-plan-sha256")
    parser.add_argument("--expected-receipt-sha256")
    parser.add_argument("--plan", dest="plan_path")
    parser.add_argument("--grok-compat-config")
    parser.add_argument("--force-migration", action="store_true")
    parser.add_argument("--legacy-hook-source", action="append", default=[])
    parser.add_argument("--legacy-hook-source-sha256", "--legacy-hook-sha256", action="append", default=[])
    parser.add_argument("--legacy-hook-source-mode", "--legacy-hook-mode", action="append", default=[])
    parser.add_argument("--receipt")
    parser.add_argument("--run-id")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    args.mode = args.mode_option or args.mode or "plan"
    try:
        roots = _parse_pairs(args.host_root, "--host-root")
        configs = _parse_pairs(args.config, "--config")
        legacy_sources = _parse_pairs(args.legacy_hook_source, "--legacy-hook-source")
        legacy_hashes = _parse_pairs(args.legacy_hook_source_sha256, "--legacy-hook-source-sha256")
        legacy_modes = _parse_modes(args.legacy_hook_source_mode, "--legacy-hook-source-mode")
        if args.mode in {"plan", "apply"}:
            if not args.product_root or not args.light_interpreter:
                raise InstallerError("HOLD_ARGUMENT", "--product-root and --light-interpreter are required")
            if args.mode == "plan":
                result = plan_install(product_root=args.product_root, light_interpreter=args.light_interpreter, host_roots=roots, config_paths=configs, expected_source_sha256=args.expected_source_sha256, run_id=args.run_id, grok_compat_config=args.grok_compat_config, force_migration=args.force_migration, legacy_hook_sources=legacy_sources, legacy_hook_source_hashes=legacy_hashes, legacy_hook_source_modes=legacy_modes)
            else:
                result = apply_install(product_root=args.product_root, light_interpreter=args.light_interpreter, host_roots=roots, config_paths=configs, expected_source_sha256=args.expected_source_sha256, plan_path=args.plan_path, run_id=args.run_id, grok_compat_config=args.grok_compat_config, force_migration=(args.force_migration if args.force_migration else None))
        elif args.mode == "verify":
            if not args.receipt:
                raise InstallerError("HOLD_ARGUMENT", "--receipt is required")
            result = verify_install(receipt_path=args.receipt, plan_path=args.plan_path, expected_receipt_sha256=args.expected_receipt_sha256, expected_plan_sha256=args.expected_plan_sha256, product_root=args.product_root, light_interpreter=args.light_interpreter)
        else:
            if not args.receipt:
                raise InstallerError("HOLD_ARGUMENT", "--receipt is required")
            result = rollback_install(receipt_path=args.receipt, plan_path=args.plan_path, expected_receipt_sha256=args.expected_receipt_sha256, expected_plan_sha256=args.expected_plan_sha256, product_root=args.product_root, light_interpreter=args.light_interpreter, force=args.force)
    except InstallerError as exc:
        result = {"schema": SCHEMA, "mode": args.mode, "status": "HOLD", "reason_code": exc.code, "detail": exc.detail, "promotion_allowed": False, "claim_ceiling": CLAIM_CEILING}
    sys.stdout.write(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True) + "\n")
    return 0 if result.get("status") in {"PLAN", "APPLIED", "IDEMPOTENT", "VERIFIED", "ROLLED_BACK"} else 2


# Short aliases make this module convenient for focused fixture tests.
plan = plan_install
apply = apply_install
verify = verify_install
rollback = rollback_install


if __name__ == "__main__":
    raise SystemExit(main())
