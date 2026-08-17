"""Operational hook/gate front door for the CB Light library lifecycle."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Mapping

from .cb_light_domain import (
    ROOT,
    canonical_json,
    compile_domain,
    normalize_distribution,
    sha256_bytes,
    sha256_file,
)
from .cb_light_runtime import MANDATED_INTERPRETER
from .cb_light_state import (
    connect,
    connect_readonly,
    record_domain,
    record_hook_event,
    record_probe_matrix,
    record_selection,
    status as state_status,
)


# Keep the existing public name for callers, but derive it from the one Light
# runtime identity.  A hook and its recomputation now observe the same process.
DEFAULT_INTERPRETER = MANDATED_INTERPRETER
_CONTROL_TOKENS = {";", "&&", "||", "|", "&"}
_MUTATION_WRAPPERS = {
    "command",
    "env",
    "nice",
    "nohup",
    "parallel",
    "sudo",
    "time",
    "timeout",
    "xargs",
}
_OPTIONS_WITH_VALUE = {
    "--python",
}
_UNBOUNDED_OPTION_REASONS = {
    "UNBOUNDED_REQUIREMENT_FILE": {"-r", "--requirement", "-c", "--constraint"},
    "UNBOUNDED_PACKAGE_SOURCE": {
        "--index-url",
        "--extra-index-url",
        "--find-links",
    },
    "INSTALL_DESTINATION_OUTSIDE_MANDATED_INTERPRETER": {
        "--target",
        "--prefix",
        "--root",
        "--user",
    },
    "UNBOUNDED_BUILD_CONFIGURATION": {"--config-settings"},
}


def _resolved_executable(value: str) -> Path | None:
    if "/" not in value:
        return None
    try:
        return Path(value).expanduser().resolve()
    except OSError:
        return None


def _same_executable(left: str, right: Path) -> bool:
    resolved = _resolved_executable(left)
    try:
        expected = right.expanduser().resolve()
    except OSError:
        expected = right.expanduser().absolute()
    return resolved == expected


def _command_from_payload(payload: Mapping[str, Any]) -> str:
    command = payload.get("command")
    if isinstance(command, str):
        return command
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, Mapping) and isinstance(tool_input.get("command"), str):
        return tool_input["command"]
    return ""


def _strip_environment_prefix(tokens: list[str]) -> list[str]:
    remaining = list(tokens)
    if remaining and Path(remaining[0]).name == "env":
        remaining.pop(0)
    while remaining and "=" in remaining[0] and not remaining[0].startswith(("-", "/")):
        key, _, _ = remaining[0].partition("=")
        if not key.replace("_", "").isalnum():
            break
        remaining.pop(0)
    return remaining


def _has_package_mutation_signature(tokens: list[str]) -> bool:
    words = [
        Path(word).name.lower()
        for word in re.sub(r"[^A-Za-z0-9_./+~-]+", " ", " ".join(tokens)).split()
    ]
    for index, word in enumerate(words):
        following = words[index + 1 : index + 10]
        if word.startswith("pip") and any(
            value in {"install", "uninstall"} for value in following
        ):
            return True
        if word == "uv" and any(
            value in {"add", "remove", "sync"} for value in following
        ):
            return True
        if word == "uv" and "pip" in following and any(
            value in {"install", "uninstall"} for value in following
        ):
            return True
        if word in {"poetry", "conda", "pipx"} and any(
            value
            in {"add", "remove", "install", "uninstall", "sync", "update"}
            for value in following
        ):
            return True
    return False


def _find_verb(
    tokens: list[str], start: int, allowed: set[str]
) -> tuple[int, str] | None:
    for index in range(start, len(tokens)):
        value = tokens[index].lower()
        if value in allowed:
            return index, value
    return None


def _option_matches(token: str, option: str) -> bool:
    if token == option or token.startswith(f"{option}="):
        return True
    return len(option) == 2 and option.startswith("-") and token.startswith(option)


def _unbounded_option_reason(arguments: list[str]) -> str | None:
    for reason, options in _UNBOUNDED_OPTION_REASONS.items():
        if any(
            _option_matches(token, option)
            for token in arguments
            for option in options
        ):
            return reason
    return None


def _mutation_shape(command: str, *, depth: int = 0) -> dict[str, Any]:
    if depth > 3:
        return {"mutation": True, "error": "MUTATION_WRAPPER_DEPTH_EXCEEDED"}
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as exc:
        return {"mutation": True, "error": "COMMAND_PARSE_FAILED", "detail": str(exc)}
    if any(token in _CONTROL_TOKENS for token in tokens):
        return {"mutation": True, "error": "COMPOUND_MUTATION_COMMAND"}
    raw_executable = Path(tokens[0]).name.lower() if tokens else ""
    if raw_executable in _MUTATION_WRAPPERS and _has_package_mutation_signature(tokens):
        return {
            "mutation": True,
            "error": "INDIRECT_MUTATION_WRAPPER",
            "wrapper": raw_executable,
            "tokens": tokens,
        }
    tokens = _strip_environment_prefix(tokens)
    if not tokens:
        return {"mutation": False, "tokens": []}

    executable = Path(tokens[0]).name.lower()
    if (
        executable in {"bash", "sh", "zsh"}
        and len(tokens) >= 3
        and tokens[1] in {"-c", "-lc"}
    ):
        nested = _mutation_shape(tokens[2], depth=depth + 1)
        if nested.get("mutation"):
            return {
                "mutation": True,
                "error": "INDIRECT_MUTATION_WRAPPER",
                "wrapper": executable,
                "nested": nested,
            }
        return {"mutation": False, "tokens": tokens}
    if executable in _MUTATION_WRAPPERS and len(tokens) >= 2:
        nested_command = " ".join(shlex.quote(token) for token in tokens[1:])
        nested = _mutation_shape(nested_command, depth=depth + 1)
        if nested.get("mutation"):
            return {
                "mutation": True,
                "error": "INDIRECT_MUTATION_WRAPPER",
                "wrapper": executable,
                "nested": nested,
            }
        return {"mutation": False, "tokens": tokens}
    module_index = next(
        (
            index
            for index in range(1, len(tokens) - 1)
            if tokens[index : index + 2] == ["-m", "pip"]
        ),
        None,
    )
    if module_index is not None:
        found = _find_verb(tokens, module_index + 2, {"install", "uninstall"})
        if found is not None:
            verb_index, verb = found
            return {
                "mutation": True,
                "tool": "python-pip",
                "executable": tokens[0],
                "verb": verb,
                "prefix_arguments": tokens[module_index + 2 : verb_index],
                "arguments": tokens[verb_index + 1 :],
                "tokens": tokens,
            }
    if executable.startswith("pip") and len(tokens) >= 2:
        found = _find_verb(tokens, 1, {"install", "uninstall"})
        if found is not None:
            verb_index, verb = found
            return {
                "mutation": True,
                "tool": "bare-pip",
                "executable": tokens[0],
                "verb": verb,
                "prefix_arguments": tokens[1:verb_index],
                "arguments": tokens[verb_index + 1 :],
                "tokens": tokens,
            }
    if executable == "uv":
        pip_index = next(
            (index for index in range(1, len(tokens)) if tokens[index].lower() == "pip"),
            None,
        )
        found = (
            _find_verb(tokens, pip_index + 1, {"install", "uninstall"})
            if pip_index is not None
            else None
        )
        if found is not None:
            verb_index, verb = found
            return {
                "mutation": True,
                "tool": "uv-pip",
                "executable": tokens[0],
                "verb": verb,
                "prefix_arguments": tokens[1:verb_index],
                "arguments": tokens[verb_index + 1 :],
                "tokens": tokens,
            }
        project = _find_verb(tokens, 1, {"add", "remove", "sync"})
        if project is not None:
            verb_index, verb = project
            return {
                "mutation": True,
                "tool": "uv-project",
                "executable": tokens[0],
                "verb": verb,
                "prefix_arguments": tokens[1:verb_index],
                "arguments": tokens[verb_index + 1 :],
                "tokens": tokens,
            }
    if executable in {"poetry", "conda", "pipx"}:
        found = _find_verb(
            tokens,
            1,
            {"add", "remove", "install", "uninstall", "sync", "update"},
        )
    else:
        found = None
    if found is not None:
        verb_index, verb = found
        return {
            "mutation": True,
            "tool": executable,
            "executable": tokens[0],
            "verb": verb,
            "prefix_arguments": tokens[1:verb_index],
            "arguments": tokens[verb_index + 1 :],
            "tokens": tokens,
        }
    if _has_package_mutation_signature(tokens):
        return {
            "mutation": True,
            "error": "UNPARSED_PACKAGE_MUTATION",
            "tokens": tokens,
        }
    return {"mutation": False, "tokens": tokens}


def _requested(
    arguments: list[str],
) -> tuple[list[str], list[str], dict[str, str], str | None]:
    names: list[str] = []
    projects: list[str] = []
    specifications: dict[str, str] = {}
    index = 0
    while index < len(arguments):
        token = arguments[index]
        if token in {"-e", "--editable"}:
            if index + 1 >= len(arguments):
                return names, projects, specifications, "EDITABLE_TARGET_MISSING"
            projects.append(arguments[index + 1])
            index += 2
            continue
        if token.startswith(("-e=", "--editable=")):
            projects.append(token.split("=", 1)[1])
            index += 1
            continue
        if token.startswith("-e") and not token.startswith("--"):
            projects.append(token[2:])
            index += 1
            continue
        if token in {"-r", "--requirement", "-c", "--constraint"}:
            return names, projects, specifications, "UNBOUNDED_REQUIREMENT_FILE"
        if token in _OPTIONS_WITH_VALUE:
            index += 2
            continue
        if token.startswith("--python="):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        if token in {".", "constraint_box", str(ROOT)} or token.startswith(("./", "../", "/")):
            projects.append(token)
            index += 1
            continue
        if "://" in token or token.startswith(("git+", "hg+", "svn+", "bzr+")):
            return names, projects, specifications, "DIRECT_URL_NOT_BOUNDED"
        name = token.split("[", 1)[0]
        for marker in ("===", "==", ">=", "<=", "~=", "!=", ">", "<"):
            name = name.split(marker, 1)[0]
        try:
            normalized = normalize_distribution(name)
        except Exception:
            return names, projects, specifications, "PACKAGE_SPEC_PARSE_FAILED"
        if normalized in specifications and specifications[normalized] != token:
            return names, projects, specifications, "CONFLICTING_PACKAGE_SPECS"
        names.append(normalized)
        specifications[normalized] = token
        index += 1
    return sorted(set(names)), projects, specifications, None


def _canonical_requirement(value: str) -> str | None:
    match = re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9_.-]*)(.*)$", value)
    if match is None or "[" in match.group(2):
        return None
    try:
        name = normalize_distribution(match.group(1))
    except Exception:
        return None
    return name + re.sub(r"\s+", "", match.group(2))


def _project_is_constraint_box(value: str, cwd: Path) -> bool:
    try:
        path = Path(value)
        if not path.is_absolute():
            path = cwd / path
        return path.resolve() == ROOT.resolve()
    except OSError:
        return False


def evaluate_install_command(
    payload: Mapping[str, Any],
    domain: Mapping[str, Any],
    *,
    mandated_interpreter: Path = DEFAULT_INTERPRETER,
    cwd: Path | None = None,
) -> dict[str, Any]:
    command = _command_from_payload(payload)
    shape = _mutation_shape(command)
    common = {
        "event": "pre_install",
        "command_sha256": __import__("hashlib").sha256(command.encode()).hexdigest(),
        "claim_ceiling": "configured Bash-hook package mutation only",
    }
    if not shape.get("mutation"):
        return {
            **common,
            "disposition": "ADMIT",
            "reason_code": "NOT_A_PACKAGE_MUTATION",
            "details": {"tokens": shape.get("tokens", [])},
        }
    if shape.get("error"):
        return {
            **common,
            "disposition": "REFUSE",
            "reason_code": shape["error"],
            "details": shape,
        }
    if shape["tool"] in {"uv-project", "poetry", "conda", "pipx"}:
        return {
            **common,
            "disposition": "REFUSE",
            "reason_code": "UNBOUNDED_ENVIRONMENT_MUTATION",
            "details": shape,
        }
    if shape["verb"] == "uninstall":
        return {
            **common,
            "disposition": "REFUSE",
            "reason_code": "UNINSTALL_REQUIRES_EXPLICIT_MAINTENANCE_TRANSITION",
            "details": shape,
        }
    if shape["tool"] == "bare-pip":
        return {
            **common,
            "disposition": "REFUSE",
            "reason_code": "MANDATED_INTERPRETER_REQUIRED",
            "details": shape,
        }
    if shape["tool"] == "python-pip" and not _same_executable(
        shape["executable"], mandated_interpreter
    ):
        return {
            **common,
            "disposition": "REFUSE",
            "reason_code": "MANDATED_INTERPRETER_REQUIRED",
            "details": shape,
        }
    if shape["tool"] == "uv-pip":
        python_values = []
        arguments = shape.get("prefix_arguments", []) + shape["arguments"]
        for index, token in enumerate(arguments):
            if token == "--python" and index + 1 < len(arguments):
                python_values.append(arguments[index + 1])
            elif token.startswith("--python="):
                python_values.append(token.split("=", 1)[1])
        if len(python_values) != 1 or not _same_executable(
            python_values[0], mandated_interpreter
        ):
            return {
                **common,
                "disposition": "REFUSE",
                "reason_code": "UV_MANDATED_INTERPRETER_REQUIRED",
                "details": shape,
            }

    all_arguments = shape.get("prefix_arguments", []) + shape["arguments"]
    option_error = _unbounded_option_reason(all_arguments)
    if option_error:
        return {
            **common,
            "disposition": "REFUSE",
            "reason_code": option_error,
            "details": {**shape, "bounded_arguments": shape["arguments"]},
        }
    if shape["tool"] == "python-pip" and any(
        _option_matches(token, "--python") for token in all_arguments
    ):
        return {
            **common,
            "disposition": "REFUSE",
            "reason_code": "PIP_TARGET_INTERPRETER_OVERRIDE",
            "details": shape,
        }

    names, projects, specifications, parse_error = _requested(shape["arguments"])
    if parse_error:
        return {
            **common,
            "disposition": "REFUSE",
            "reason_code": parse_error,
            "details": {
                **shape,
                "requested": names,
                "specifications": specifications,
                "projects": projects,
            },
        }
    active_cwd = (cwd or Path.cwd()).resolve()
    if projects and not all(_project_is_constraint_box(value, active_cwd) for value in projects):
        return {
            **common,
            "disposition": "REFUSE",
            "reason_code": "PROJECT_INSTALL_OUTSIDE_CB_LIGHT",
            "details": {**shape, "requested": names, "projects": projects},
        }
    domain_names = {
        row["normalized_name"]
        for row in domain["rows"]
        if row["kind"] == "distribution"
    }
    direct = {
        row["normalized_name"]
        for row in domain["rows"]
        if row["kind"] == "distribution"
        and row["declarations"].get("pyproject_direct")
    }
    core_contract = {
        row["normalized_name"]
        for row in domain["rows"]
        if row["kind"] == "distribution" and row.get("core_contract")
    }
    installable_core = direct & core_contract
    direct_rows = {
        row["normalized_name"]: row
        for row in domain["rows"]
        if row["kind"] == "distribution"
        and row["declarations"].get("pyproject_direct")
    }
    outside = sorted(set(names) - domain_names)
    unselected = sorted(set(names) - installable_core)
    if outside:
        return {
            **common,
            "disposition": "REFUSE",
            "reason_code": "PACKAGE_OUTSIDE_CB_LIGHT_PROPOSAL_DOMAIN",
            "details": {"outside": outside, "requested": names, "projects": projects},
        }
    if unselected:
        return {
            **common,
            "disposition": "HOLD",
            "reason_code": "CANDIDATE_NOT_SELECTED_FOR_INSTALL",
            "details": {"unselected": unselected, "requested": names, "projects": projects},
        }
    if names and projects:
        return {
            **common,
            "disposition": "REFUSE",
            "reason_code": "MIXED_PROJECT_AND_PACKAGE_INSTALL",
            "details": {"requested": names, "projects": projects},
        }
    if projects and direct != core_contract:
        return {
            **common,
            "disposition": "REFUSE",
            "reason_code": "PROJECT_DEPENDENCY_SET_NOT_CURRENT_CORE",
            "details": {
                "unexpected_direct": sorted(direct - core_contract),
                "undeclared_core": sorted(core_contract - direct),
                "projects": projects,
            },
        }
    invalid_specs: list[dict[str, Any]] = []
    for name in names:
        row = direct_rows[name]
        declared = row["declarations"].get("pyproject_direct_requirement")
        requested = specifications[name]
        installed_version = row["observation"].get("installed_version")
        allowed = {_canonical_requirement(str(declared))}
        if installed_version:
            allowed.add(_canonical_requirement(f"{name}=={installed_version}"))
        if _canonical_requirement(requested) not in allowed:
            invalid_specs.append(
                {
                    "name": name,
                    "requested": requested,
                    "required": declared,
                    "current_exact": installed_version,
                }
            )
    if invalid_specs:
        return {
            **common,
            "disposition": "HOLD",
            "reason_code": "DECLARED_VERSION_CONSTRAINT_REQUIRED",
            "details": {"invalid_specs": invalid_specs},
        }
    if not names and not projects:
        return {
            **common,
            "disposition": "REFUSE",
            "reason_code": "EMPTY_INSTALL_TARGET",
            "details": shape,
        }
    return {
        **common,
        "disposition": "ADMIT",
        "reason_code": "DECLARED_CORE_INSTALL_BOUNDED",
        "details": {
            "requested": names,
            "project_install": bool(projects),
            "mandated_interpreter": str(mandated_interpreter),
        },
    }


def _load_payload(value: str | None) -> dict[str, Any]:
    if value is None:
        return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("payload must be a JSON object")
    return parsed


def _write_output(path: Path | None, body: Mapping[str, Any]) -> None:
    rendered = json.dumps(body, indent=2, sort_keys=True) + "\n"
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def _write_full_and_print_summary(
    path: Path | None, full: Mapping[str, Any], summary: Mapping[str, Any]
) -> None:
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(full, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    _write_output(None, summary)


def _probe_and_select(connection: Any, domain: Mapping[str, Any]) -> dict[str, Any]:
    # Resolve the separately installed Light distribution.  Do not inject the
    # legacy ``src/constraintbox`` tree here: that tree carries CB Heavy
    # adapters and would collapse the Light/Heavy package boundary.
    from constraintbox.cb_light_probes import run_core_probe_matrix
    from constraintbox.cb_light_selection import decide_domain

    snapshot_id = record_domain(connection, domain)
    matrix = run_core_probe_matrix()
    probe_run_id = record_probe_matrix(connection, matrix)
    selection = decide_domain(domain, matrix)
    selection_id = record_selection(
        connection,
        selection,
        snapshot_id=snapshot_id,
        probe_run_id=probe_run_id,
    )
    implementation_paths = {
        "hookkernel/cb_light_gate.py": Path(__file__).resolve(),
        "hookkernel/cb_light_state.py": Path(__file__).with_name(
            "cb_light_state.py"
        ),
    }
    repo = ROOT.parent
    project_hook_paths = {
        ".claude/settings.json": repo / ".claude" / "settings.json",
        ".claude/hooks/cb_pretooluse_guard.sh": repo
        / ".claude"
        / "hooks"
        / "cb_pretooluse_guard.sh",
        ".claude/hooks/cb_posttooluse_record.sh": repo
        / ".claude"
        / "hooks"
        / "cb_posttooluse_record.sh",
        ".claude/hooks/session-start.sh": repo
        / ".claude"
        / "hooks"
        / "session-start.sh",
        ".claude/hooks/post-compact-reinject.sh": repo
        / ".claude"
        / "hooks"
        / "post-compact-reinject.sh",
        ".claude/hooks/cb_stop_completion_check.sh": repo
        / ".claude"
        / "hooks"
        / "cb_stop_completion_check.sh",
    }
    project_hooks_bound = all(path.is_file() for path in project_hook_paths.values())
    if project_hooks_bound:
        implementation_paths.update(project_hook_paths)
    implementation_source_hashes = {
        name: sha256_file(path) for name, path in implementation_paths.items()
    }
    from .cb_light_basin_view import apply_view_hold, read_current_view

    body = {
        "schema": "constraintbox.cb-light-gate-run.v1",
        "snapshot_id": snapshot_id,
        "probe_run_id": probe_run_id,
        "selection_id": selection_id,
        "domain": domain,
        "probe_matrix": matrix,
        "selection": selection,
        "implementation_source_hashes": implementation_source_hashes,
        "implementation_source_set_sha256": sha256_bytes(
            canonical_json(implementation_source_hashes)
        ),
        "project_hook_source_status": (
            "BOUND_IN_PROJECT" if project_hooks_bound else "NOT_PACKAGED"
        ),
        "disposition": "ADMIT" if matrix["all_contracts_satisfied"] else "HOLD",
        "reason_code": (
            "TOOL_PROBE_CONTRACTS_SATISFIED"
            if matrix["all_contracts_satisfied"]
            else "TOOL_PROBE_CONTRACTS_INCOMPLETE"
        ),
        "claim_ceiling": (
            f"{len(matrix.get('tool_decisions', []))} current declared-tool "
            "contracts plus full proposal selection state; no adoption"
        ),
    }
    return apply_view_hold(body, read_current_view("tool_matrix"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cb-light-gate")
    parser.add_argument("--db", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("snapshot", "probe"):
        command = commands.add_parser(name)
        command.add_argument("--output", type=Path)
    pre = commands.add_parser("pre-install")
    pre.add_argument("--payload-json")
    pre.add_argument("--mandated-interpreter", type=Path, default=DEFAULT_INTERPRETER)
    session = commands.add_parser("session-start")
    session.add_argument("--payload-json")
    post = commands.add_parser("post-tool")
    post.add_argument("--payload-json")
    post.add_argument("--output", type=Path)
    commands.add_parser("status")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "status":
        connection = connect_readonly(args.db)
        _write_output(None, state_status(connection))
        return 0

    # Ordinary Bash commands take the zero-state fast path. Domain compilation
    # and SQLite writes happen only for actual package mutations.
    if args.command in {"pre-install", "post-tool"}:
        payload = _load_payload(args.payload_json)
        shape = _mutation_shape(_command_from_payload(payload))
        if not shape.get("mutation"):
            return 0

    connection = connect(args.db)

    domain = compile_domain(interpreter=str(DEFAULT_INTERPRETER))
    if args.command == "snapshot":
        snapshot_id = record_domain(connection, domain)
        environment = domain["environment_observation"]
        body = {
            "schema": "constraintbox.cb-light-domain-snapshot.v1",
            "snapshot_id": snapshot_id,
            "domain_sha256": domain["domain_sha256"],
            "source_manifest_sha256": domain["source_manifest_sha256"],
            "completeness": domain["completeness"],
            "counts": domain["counts"],
            "environment_observation": {
                key: value
                for key, value in environment.items()
                if key != "ambient_installed"
            },
            "forbidden_membership_sources": domain["forbidden_membership_sources"],
            "claim_ceiling": domain["claim_ceiling"],
        }
        _write_full_and_print_summary(args.output, domain, body)
        return 0
    if args.command == "probe":
        body = _probe_and_select(connection, domain)
        summary = {
            "schema": body["schema"],
            "disposition": body["disposition"],
            "reason_code": body["reason_code"],
            "snapshot_id": body["snapshot_id"],
            "probe_run_id": body["probe_run_id"],
            "selection_id": body["selection_id"],
            "domain_counts": body["domain"]["counts"],
            "tool_decisions": [
                {
                    "contract_id": decision["contract_id"],
                    "disposition": decision["disposition"],
                    "reason_code": decision["reason_code"],
                }
                for decision in body["probe_matrix"]["tool_decisions"]
            ],
            "selection_counts": body["selection"]["counts"],
            "owner_approved_adoptions": body["selection"][
                "owner_approved_adoptions"
            ],
            "claim_ceiling": body["claim_ceiling"],
        }
        _write_full_and_print_summary(args.output, body, summary)
        return 0 if body["disposition"] == "ADMIT" else 3
    if args.command == "pre-install":
        result = evaluate_install_command(
            payload,
            domain,
            mandated_interpreter=args.mandated_interpreter,
            cwd=Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd())),
        )
        record_hook_event(
            connection,
            event="pre_install",
            disposition=result["disposition"],
            reason_code=result["reason_code"],
            payload=payload,
            details=result["details"],
        )
        _write_output(None, result)
        return 0 if result["disposition"] == "ADMIT" else 2
    if args.command == "post-tool":
        body = _probe_and_select(connection, domain)
        record_hook_event(
            connection,
            event="post_install",
            disposition=body["disposition"],
            reason_code=body["reason_code"],
            payload=payload,
            details={
                "snapshot_id": body["snapshot_id"],
                "probe_run_id": body["probe_run_id"],
                "selection_id": body["selection_id"],
                "tool": shape.get("tool"),
                "verb": shape.get("verb"),
            },
        )
        _write_output(args.output, body)
        return 0 if body["disposition"] == "ADMIT" else 3
    if args.command == "session-start":
        payload = _load_payload(args.payload_json)
        snapshot_id = record_domain(connection, domain)
        pyproject_rows = [
            row
            for row in domain["rows"]
            if row["kind"] == "distribution"
            and row["declarations"].get("pyproject_direct")
        ]
        core_rows = [
            row
            for row in domain["rows"]
            if row["kind"] == "distribution" and row.get("core_contract")
        ]
        pyproject_names = {row["normalized_name"] for row in pyproject_rows}
        core_names = {row["normalized_name"] for row in core_rows}
        unexpected_direct = sorted(pyproject_names - core_names)
        undeclared_core = sorted(core_names - pyproject_names)
        missing = [
            row["normalized_name"]
            for row in core_rows
            if not row["observation"]["installed"]
            or row["observation"]["import_visible"] is not True
        ]
        invalid_versions = [
            {
                "name": row["normalized_name"],
                "installed": row["observation"]["installed_version"],
                "required": row["declarations"]["pyproject_direct_requirement"],
            }
            for row in core_rows
            if row["observation"]["installed"]
            and row["declarations"].get("pyproject_direct_requirement")
            and row["observation"]["version_satisfies_declaration"] is not True
        ]
        set_drift = bool(unexpected_direct or undeclared_core)
        disposition = (
            "ADMIT"
            if not set_drift and not missing and not invalid_versions
            else "HOLD"
        )
        if set_drift:
            reason = "DECLARED_CORE_SET_DRIFT"
        elif disposition == "ADMIT":
            reason = "DECLARED_CORE_VISIBLE_AND_VERSION_BOUNDED"
        elif missing and invalid_versions:
            reason = "DECLARED_CORE_INCOMPLETE_AND_VERSION_DRIFT"
        elif invalid_versions:
            reason = "DECLARED_CORE_VERSION_DRIFT"
        else:
            reason = "DECLARED_CORE_INCOMPLETE"
        details = {
            "snapshot_id": snapshot_id,
            "domain_counts": domain["counts"],
            "declared_core": sorted(core_names),
            "pyproject_direct": sorted(pyproject_names),
            "unexpected_direct": unexpected_direct,
            "undeclared_core": undeclared_core,
            "missing": missing,
            "invalid_versions": invalid_versions,
            "adoption_state": "UNRESOLVED_OWNER_SELECTION",
        }
        record_hook_event(
            connection,
            event="session_start",
            disposition=disposition,
            reason_code=reason,
            payload=payload,
            details=details,
        )
        _write_output(
            None,
            {
                "schema": "constraintbox.cb-light-session-start.v1",
                "disposition": disposition,
                "reason_code": reason,
                "details": details,
                "claim_ceiling": "declared core install/import observation only",
            },
        )
        return 0 if disposition == "ADMIT" else 3
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
