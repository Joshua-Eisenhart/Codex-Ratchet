#!/usr/bin/env python3
"""Report sim audit verdicts that predate the source files they audit.

This check intentionally uses git commit timestamps instead of mtimes. That
keeps it tied to committed history, but it can still flag cosmetic recommits
where source content did not materially change. Existing cases are therefore
grandfathered by baseline; strict mode is for new or materially worse staleness.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


SIMS_ROOT = Path("system_v6/sims")
DEFAULT_BASELINE = Path("scripts/stale_audit_baseline.json")
MATERIAL_GROWTH_SECONDS = 60


@dataclass(frozen=True)
class StaleAudit:
    audit_path: str
    audit_ts: int
    src_max_ts: int
    stale_sources: tuple[str, ...]


@dataclass(frozen=True)
class LintResult:
    stale: list[StaleAudit]
    clean_count: int
    no_audit_count: int
    no_source_count: int


def default_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise SystemExit(f"path is outside repo root: {path}") from exc


def run_git(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def require_git_repo(repo_root: Path) -> None:
    proc = run_git(repo_root, ["rev-parse", "--show-toplevel"])
    if proc.returncode != 0:
        raise SystemExit(f"not a git repo root: {repo_root}")

    actual_root = Path(proc.stdout.strip()).resolve()
    if actual_root != repo_root.resolve():
        raise SystemExit(
            f"--repo-root must be the git repo root: got {repo_root}, git root is {actual_root}"
        )


def git_commit_ts(repo_root: Path, path: Path) -> int:
    rel_path = repo_relative(path, repo_root)
    proc = run_git(repo_root, ["log", "-1", "--format=%ct", "--", rel_path])
    if proc.returncode != 0:
        raise SystemExit(f"git log failed for {rel_path}: {proc.stderr.strip()}")

    text = proc.stdout.strip()
    if not text:
        return 0

    try:
        return int(text)
    except ValueError as exc:
        raise SystemExit(f"unexpected git timestamp for {rel_path}: {text!r}") from exc


def sim_dirs(sims_root: Path) -> list[Path]:
    if not sims_root.is_dir():
        raise SystemExit(f"missing sims dir: {sims_root}")
    return sorted(path for path in sims_root.iterdir() if path.is_dir())


def source_files(sim_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in sim_dir.iterdir()
        if path.is_file() and path.suffix in {".py", ".jl"}
    )


def stale_sim_name(stale_audit: StaleAudit) -> str:
    parts = Path(stale_audit.audit_path).parts
    if len(parts) >= 4 and parts[:2] == ("system_v6", "sims"):
        return parts[2]
    return Path(stale_audit.audit_path).parent.name


def collect_stale_audits(repo_root: Path, sims_root_path: Path, verbose: bool) -> LintResult:
    sims_root = repo_root / SIMS_ROOT
    if sims_root_path.is_absolute():
        sims_root = sims_root_path
    else:
        sims_root = repo_root / sims_root_path

    stale: list[StaleAudit] = []
    clean_count = 0
    no_audit_count = 0
    no_source_count = 0

    for sim_dir in sim_dirs(sims_root):
        rel_sim_dir = repo_relative(sim_dir, repo_root)
        audit_path = sim_dir / "audit_verdict.md"

        if not audit_path.exists():
            no_audit_count += 1
            if verbose:
                print(f"NO-AUDIT: {rel_sim_dir}")
            continue

        sources = source_files(sim_dir)
        if not sources:
            no_source_count += 1
            if verbose:
                print(f"NO-SOURCE: {rel_sim_dir}")
            continue

        audit_ts = git_commit_ts(repo_root, audit_path)
        committed_sources: list[tuple[Path, int]] = []
        for source_path in sources:
            source_ts = git_commit_ts(repo_root, source_path)
            if source_ts > 0:
                committed_sources.append((source_path, source_ts))

        src_max_ts = max((source_ts for _, source_ts in committed_sources), default=0)
        stale_sources = tuple(
            repo_relative(source_path, repo_root)
            for source_path, source_ts in committed_sources
            if source_ts > audit_ts
        )

        if stale_sources:
            stale_audit = StaleAudit(
                audit_path=repo_relative(audit_path, repo_root),
                audit_ts=audit_ts,
                src_max_ts=src_max_ts,
                stale_sources=stale_sources,
            )
            stale.append(stale_audit)
            print(f"STALE: {stale_audit.audit_path}")
            print(
                f"  audit_ts={stale_audit.audit_ts}  "
                f"src_max_ts={stale_audit.src_max_ts}  "
                f"stale_by={stale_audit.src_max_ts - stale_audit.audit_ts}s"
            )
            for stale_source in stale_audit.stale_sources:
                print(f"  stale_source: {stale_source}")
            continue

        clean_count += 1
        if verbose:
            print(
                f"CLEAN: {rel_sim_dir}  "
                f"audit_ts={audit_ts}  src_max_ts={src_max_ts}"
            )

    return LintResult(
        stale=stale,
        clean_count=clean_count,
        no_audit_count=no_audit_count,
        no_source_count=no_source_count,
    )


def baseline_payload(stale: list[StaleAudit]) -> dict[str, dict[str, int]]:
    return {
        stale_sim_name(stale_audit): {
            "audit_ts": stale_audit.audit_ts,
            "src_max_ts": stale_audit.src_max_ts,
        }
        for stale_audit in sorted(stale, key=stale_sim_name)
    }


def write_baseline(repo_root: Path, baseline_path: Path, stale: list[StaleAudit]) -> None:
    if not baseline_path.is_absolute():
        baseline_path = repo_root / baseline_path
    payload = baseline_payload(stale)
    baseline_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"WROTE baseline: {repo_relative(baseline_path, repo_root)} ({len(payload)} entries)")


def load_baseline(repo_root: Path, baseline_path: Path) -> dict[str, dict[str, int]]:
    if not baseline_path.is_absolute():
        baseline_path = repo_root / baseline_path
    if not baseline_path.exists():
        raise SystemExit(f"missing stale audit baseline: {baseline_path}")

    try:
        raw = json.loads(baseline_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid stale audit baseline JSON: {baseline_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise SystemExit(f"stale audit baseline must be an object: {baseline_path}")

    baseline: dict[str, dict[str, int]] = {}
    for sim_name, entry in raw.items():
        if not isinstance(sim_name, str) or not isinstance(entry, dict):
            raise SystemExit(f"invalid stale audit baseline entry for {sim_name!r}")
        audit_ts = entry.get("audit_ts")
        src_max_ts = entry.get("src_max_ts")
        if not isinstance(audit_ts, int) or not isinstance(src_max_ts, int):
            raise SystemExit(f"baseline entry must contain integer audit_ts/src_max_ts: {sim_name}")
        baseline[sim_name] = {"audit_ts": audit_ts, "src_max_ts": src_max_ts}
    return baseline


def strict_failures(
    stale: list[StaleAudit],
    baseline: dict[str, dict[str, int]],
) -> list[tuple[StaleAudit, str]]:
    failures: list[tuple[StaleAudit, str]] = []
    for stale_audit in stale:
        sim_name = stale_sim_name(stale_audit)
        baseline_entry = baseline.get(sim_name)
        if baseline_entry is None:
            failures.append((stale_audit, "new_stale_audit_not_in_baseline"))
            continue

        baseline_stale_by = baseline_entry["src_max_ts"] - baseline_entry["audit_ts"]
        current_stale_by = stale_audit.src_max_ts - stale_audit.audit_ts
        growth = current_stale_by - baseline_stale_by
        if growth > MATERIAL_GROWTH_SECONDS:
            failures.append(
                (
                    stale_audit,
                    f"staleness_grew_by_{growth}s_over_baseline",
                )
            )
    return failures


def print_summary(result: LintResult, strict: bool, failures: list[tuple[StaleAudit, str]]) -> None:
    print(
        "lint_stale_audit: "
        f"{len(result.stale)} stale, "
        f"{result.clean_count} clean, "
        f"{result.no_audit_count} no-audit, "
        f"{result.no_source_count} no-source (skipped)"
    )
    if strict:
        if failures:
            print(f"FAIL: {len(failures)} new/materially-worse stale audit(s) found")
            for stale_audit, reason in failures:
                print(f"  {reason}: {stale_sim_name(stale_audit)}")
            return
        print("PASS: strict mode found no new or materially-worse stale audits")
        return

    if result.stale:
        print(
            "ADVISORY: stale audits found; default mode is report-only. "
            "Use --strict to block new/materially-worse staleness."
        )
    else:
        print("PASS: no stale audits found")


def lint(
    repo_root: Path,
    sims_root_path: Path,
    baseline_path: Path,
    verbose: bool,
    strict: bool,
    write_baseline_path: Path | None,
) -> int:
    result = collect_stale_audits(repo_root, sims_root_path, verbose)

    if write_baseline_path is not None:
        write_baseline(repo_root, write_baseline_path, result.stale)

    failures: list[tuple[StaleAudit, str]] = []
    if strict:
        baseline = load_baseline(repo_root, baseline_path)
        failures = strict_failures(result.stale, baseline)

    print_summary(result, strict, failures)
    if strict and failures:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lint sim audit verdicts for source commits newer than the audit."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=default_repo_root(),
        help="Git repo root; defaults to the parent of this script's directory.",
    )
    parser.add_argument(
        "--sims-root",
        type=Path,
        default=SIMS_ROOT,
        help="Sims root, relative to repo root unless absolute.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Baseline JSON for strict mode.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 only for stale audits not grandfathered by baseline or materially worse.",
    )
    parser.add_argument(
        "--write-baseline",
        type=Path,
        metavar="PATH",
        help="Write the current stale set as a baseline JSON.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print details for every checked sim, not just stale audits.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.expanduser().resolve()
    require_git_repo(repo_root)
    return lint(
        repo_root=repo_root,
        sims_root_path=args.sims_root,
        baseline_path=args.baseline,
        verbose=args.verbose,
        strict=args.strict,
        write_baseline_path=args.write_baseline,
    )


if __name__ == "__main__":
    raise SystemExit(main())
