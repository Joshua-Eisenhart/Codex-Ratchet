#!/usr/bin/env python3
"""Report ClaimGate slop findings for Python lines added by a pull request.

Exit codes:

    0  no blocking findings (advisory findings may be present)
    1  one or more blocking findings
    2  usage error, bad ref, or git failure; the check could not be performed

The changed-file set is derived exclusively from git objects. The working tree
is used only because ``slop_gate.scan`` reads the selected files after the
committed HEAD-tree membership boundary has been established.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Iterator, Mapping, Sequence


BLOCKING_SOURCES = ("slop_gate",)
DEPENDENCY_STATES = (
    "OK",
    "BEHIND",
    "AHEAD",
    "MISSING",
    "UNDECLARED",
    "UNKNOWN",
)
class ReportError(RuntimeError):
    """A usage or git failure that means the blocking check did not run."""


def _git(repo_root: Path, arguments: Sequence[str]) -> bytes:
    process = subprocess.run(
        ["git", "-C", str(repo_root), *arguments],
        capture_output=True,
        check=False,
    )
    if process.returncode:
        detail = process.stderr.decode("utf-8", errors="replace").strip()
        command = "git " + " ".join(arguments)
        raise ReportError(f"{command} failed: {detail or f'exit {process.returncode}'}")
    return process.stdout


def _nul_paths(payload: bytes) -> list[str]:
    return sorted(
        {
            item.decode("utf-8", errors="surrogateescape")
            for item in payload.split(b"\0")
            if item
        }
    )


def _merge_base(repo_root: Path, base: str, head: str) -> tuple[str, str]:
    process = subprocess.run(
        ["git", "-C", str(repo_root), "merge-base", base, head],
        capture_output=True,
        check=False,
    )
    if process.returncode == 0:
        value = process.stdout.decode("ascii", errors="replace").strip()
        if value:
            return value, "git_merge_base"
    return base, "base_fallback"


def _changed_set(
    repo_root: Path,
    base: str,
    head: str,
) -> tuple[str, str, list[str], list[str], set[str]]:
    merge_base, merge_base_source = _merge_base(repo_root, base, head)
    changed = _nul_paths(
        _git(
            repo_root,
            [
                "diff",
                "--name-only",
                "-z",
                "--diff-filter=ACMR",
                merge_base,
                head,
                "--",
            ],
        )
    )
    head_tree = set(
        _nul_paths(
            _git(
                repo_root,
                ["ls-tree", "-r", "--name-only", "-z", head],
            )
        )
    )
    python_paths = sorted(path for path in changed if path.endswith(".py"))
    included = sorted(path for path in python_paths if path in head_tree)
    excluded = sorted(path for path in python_paths if path not in head_tree)
    return merge_base, merge_base_source, included, excluded, head_tree


@contextlib.contextmanager
def _at(path: Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def _relative_path(repo_root: Path, value: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        return path.as_posix()
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _blocking_findings(
    repo_root: Path,
    paths: list[str],
    diff_spec: str,
) -> tuple[list[dict[str, object]], list[str]]:
    try:
        import slop_gate
    except ImportError as exc:
        raise ReportError(f"cannot import claimgate_plugin/slop_gate.py: {exc}") from exc

    try:
        with _at(repo_root):
            findings, errors = slop_gate.scan(
                [Path(path) for path in paths],
                diff_spec,
            )
    except (OSError, ValueError) as exc:
        raise ReportError(f"slop gate could not scan the changed set: {exc}") from exc

    rows: list[dict[str, object]] = []
    for finding in findings:
        row = finding.as_dict()
        row["path"] = _relative_path(repo_root, str(row["path"]))
        row["source"] = "slop_gate"
        row["severity"] = "blocking"
        rows.append(row)

    normalized_errors = sorted(str(error) for error in errors)
    for error in normalized_errors:
        raw_path = error.split(":", 1)[0]
        rows.append(
            {
                "signature_id": "SLOP_PARSE_ERROR",
                "path": _relative_path(repo_root, raw_path),
                "line": 1,
                "excerpt": "",
                "why": error,
                "source": "slop_gate",
                "severity": "blocking",
            }
        )
    rows.sort(
        key=lambda row: (
            str(row["path"]),
            int(row["line"]),
            str(row["signature_id"]),
            str(row["why"]),
        )
    )
    return rows, normalized_errors


def _dependency_check(repo_root: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    source_root = repo_root / "constraint_box" / "src"
    sys.path.insert(0, str(source_root))
    try:
        from constraintbox.dependencies import (
            DependencyScanError,
            EXIT_CODES,
            exit_code_for,
            render_check,
            scan,
        )
        try:
            report = scan(project_root=repo_root / "constraint_box")
        except DependencyScanError as exc:
            reason = str(exc)
            finding = {
                "signature_id": "DEPENDENCY_IO_ERROR",
                "path": "constraint_box/requirements/locks",
                "line": 1,
                "excerpt": "",
                "why": f"dependency check did not run: {reason}",
                "source": "dependencies",
                "severity": "advisory",
            }
            return (
                {
                    "ran": False,
                    "exit_code": EXIT_CODES["IO_ERROR"],
                    "io_error": reason,
                    "state_counts": {state: 0 for state in DEPENDENCY_STATES},
                    "rendered_check": None,
                },
                [finding],
            )

        rows = [
            row
            for row in report.get("rows", [])
            if isinstance(row, Mapping)
        ]
        counts = Counter(str(row.get("state")) for row in rows)
        state_counts = {state: counts.get(state, 0) for state in DEPENDENCY_STATES}
        findings: list[dict[str, object]] = []
        for state in DEPENDENCY_STATES:
            count = state_counts[state]
            if state == "OK" or count == 0:
                continue
            findings.append(
                {
                    "signature_id": f"DEPENDENCY_{state}",
                    "path": "constraint_box",
                    "line": 1,
                    "excerpt": f"{count} dependency row(s)",
                    "why": f"{count} dependency row(s) have state {state}",
                    "source": "dependencies",
                    "severity": "advisory",
                }
            )
        findings.sort(
            key=lambda row: (
                str(row["path"]),
                str(row["signature_id"]),
                str(row["excerpt"]),
            )
        )
        return (
            {
                "ran": True,
                "exit_code": exit_code_for(report),
                "io_error": None,
                "state_counts": state_counts,
                "rendered_check": render_check(report),
            },
            findings,
        )
    finally:
        if sys.path and sys.path[0] == str(source_root):
            sys.path.pop(0)


def _exit_code(findings: Sequence[Mapping[str, object]]) -> int:
    blocking = any(
        finding.get("severity") == "blocking"
        and finding.get("source") in BLOCKING_SOURCES
        for finding in findings
    )
    return 1 if blocking else 0


def _workflow_preconditions(head_tree: set[str]) -> dict[str, object]:
    slop_path = "claimgate_plugin/slop_gate.py"
    regression_path = "claimgate_plugin/run_slop_regression.py"
    return {
        "slop_gate_committed_in_head": slop_path in head_tree,
        "slop_gate_required_for_ci_import": True,
        "run_slop_regression_committed_in_head": regression_path in head_tree,
        "note": (
            "claimgate_plugin/slop_gate.py must be committed in the pull-request "
            "head or the workflow fails with ModuleNotFoundError; "
            "run_slop_regression.py is currently a related untracked regression "
            "runner but is not imported by this workflow."
        ),
    }


def build_report(repo_root: Path, base: str, head: str) -> dict[str, object]:
    root = repo_root.resolve()
    if not (root / ".git").exists():
        raise ReportError(f"repo root is not a git checkout: {root}")

    merge_base, source, paths, excluded, head_tree = _changed_set(root, base, head)
    blocking, parse_errors = _blocking_findings(
        root,
        paths,
        f"{merge_base}...{head}",
    )
    dependency, advisory = _dependency_check(root)
    findings = sorted(
        [*blocking, *advisory],
        key=lambda row: (
            0 if row["severity"] == "blocking" else 1,
            str(row["path"]),
            int(row["line"]),
            str(row["signature_id"]),
            str(row["why"]),
        ),
    )
    report: dict[str, object] = {
        "schema": "claimgate.ci_slop_report.v1",
        "base": base,
        "head": head,
        "merge_base": merge_base,
        "merge_base_source": source,
        "diff_spec": f"{merge_base}...{head}",
        "changed_python_paths": paths,
        "excluded_untracked": excluded,
        "blocking_sources": list(BLOCKING_SOURCES),
        "dependency_action_required_is_advisory": True,
        "dependency_policy_note": (
            "MISSING, BEHIND, and UNKNOWN are advisory today; making dependency "
            "action-required states blocking is an open owner decision."
        ),
        "dependency_check": dependency,
        "slop_parse_errors": parse_errors,
        "workflow_preconditions": _workflow_preconditions(head_tree),
        "findings": findings,
    }
    report["blocking_count"] = sum(
        finding["severity"] == "blocking" for finding in findings
    )
    report["advisory_count"] = sum(
        finding["severity"] == "advisory" for finding in findings
    )
    report["exit_code"] = _exit_code(findings)
    report["blocking_check_state"] = (
        "error"
        if parse_errors
        else "findings"
        if report["blocking_count"]
        else "clean"
    )
    return report


def _markdown_cell(value: object) -> str:
    return str(value).replace("|", r"\|").replace("\n", " ")


def render_summary(report: Mapping[str, object]) -> str:
    preconditions = report["workflow_preconditions"]
    dependency = report["dependency_check"]
    findings = report["findings"]
    blocking = [row for row in findings if row["severity"] == "blocking"]
    advisory = [row for row in findings if row["severity"] == "advisory"]
    lines = [
        "# ClaimGate pull-request slop report",
        "",
        f"- Base: `{report['base']}`",
        f"- Head: `{report['head']}`",
        (
            f"- Merge base: `{report['merge_base']}` "
            f"(`{report['merge_base_source']}`)"
        ),
        f"- Diff: `{report['diff_spec']}`",
        f"- Changed Python files scanned: {len(report['changed_python_paths'])}",
        f"- Excluded from the head tree: {len(report['excluded_untracked'])}",
        f"- Exit code: **{report['exit_code']}**",
        "",
        "## Blocking",
        "",
        "Blocking sources: `slop_gate` only.",
        "",
    ]
    if blocking:
        lines.extend(
            [
                "| Signature | Path | Line | Why |",
                "|---|---|---:|---|",
                *[
                    "| {signature} | `{path}` | {line} | {why} |".format(
                        signature=_markdown_cell(row["signature_id"]),
                        path=_markdown_cell(row["path"]),
                        line=row["line"],
                        why=_markdown_cell(row["why"]),
                    )
                    for row in blocking
                ],
            ]
        )
    else:
        lines.append("No blocking findings.")

    lines.extend(
        [
            "",
            "## Advisory",
            "",
            (
                "Dependency MISSING, BEHIND, and UNKNOWN states are advisory "
                "today. Making them blocking is an open owner decision."
            ),
            "",
        ]
    )
    if dependency["ran"]:
        counts = dependency["state_counts"]
        lines.append(
            "Dependency check ran with exit "
            f"`{dependency['exit_code']}`: "
            + ", ".join(f"{state}={counts[state]}" for state in DEPENDENCY_STATES)
            + "."
        )
    else:
        lines.append(
            "Dependency check did not run: "
            + _markdown_cell(dependency["io_error"])
            + "."
        )
    lines.append("")
    if advisory:
        lines.extend(
            [
                "| Signature | Path | Why |",
                "|---|---|---|",
                *[
                    "| {signature} | `{path}` | {why} |".format(
                        signature=_markdown_cell(row["signature_id"]),
                        path=_markdown_cell(row["path"]),
                        why=_markdown_cell(row["why"]),
                    )
                    for row in advisory
                ],
            ]
        )
    else:
        lines.append("No advisory findings.")

    lines.extend(
        [
            "",
            "## Workflow precondition",
            "",
            f"- `slop_gate.py` committed in head: `{str(preconditions['slop_gate_committed_in_head']).lower()}`",
            f"- `run_slop_regression.py` committed in head: `{str(preconditions['run_slop_regression_committed_in_head']).lower()}`",
            f"- {preconditions['note']}",
            "",
        ]
    )
    if report["excluded_untracked"]:
        lines.extend(
            [
                "## Excluded untracked",
                "",
                *[f"- `{path}`" for path in report["excluded_untracked"]],
                "",
            ]
        )
    return "\n".join(lines)


def _command_property(value: object) -> str:
    return (
        str(value)
        .replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
        .replace(":", "%3A")
        .replace(",", "%2C")
    )


def _command_message(value: object) -> str:
    return (
        str(value)
        .replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
    )


def emit_annotations(report: Mapping[str, object]) -> None:
    for finding in report["findings"]:
        level = "error" if finding["severity"] == "blocking" else "notice"
        print(
            f"::{level} "
            f"file={_command_property(finding['path'])},"
            f"line={int(finding['line'])},"
            f"title={_command_property(finding['signature_id'])}"
            f"::{_command_message(finding['why'])}"
        )


def _write_summary(path: Path, markdown: str) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(markdown)
        if not markdown.endswith("\n"):
            handle.write("\n")


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--repo-root", type=Path, default=_default_repo_root())
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--annotations", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.json and args.annotations:
        parser.error("--json and --annotations are mutually exclusive")
    if args.annotations and not args.summary:
        parser.error("--annotations requires --summary so stdout stays annotation-only")

    try:
        report = build_report(args.repo_root, args.base, args.head)
    except (OSError, ReportError) as exc:
        print(f"ci_slop_report: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        markdown = render_summary(report)
        if args.summary:
            try:
                _write_summary(args.summary, markdown)
            except OSError as exc:
                print(f"ci_slop_report: cannot append summary: {exc}", file=sys.stderr)
                return 2
        else:
            print(markdown)
        if args.annotations:
            emit_annotations(report)
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
