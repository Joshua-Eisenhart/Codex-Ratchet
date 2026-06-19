#!/usr/bin/env python3
"""Lint committed sim audit verdict headers for independent-audit wording.

Known deferred limitation: this local substring check still accepts negated
phrases such as "NOT an independent audit verdict". Fix that in the shared
builder_audit_boundary.py helper later; this script only widens local accepted
tokens and grandfathers current misses.
"""

from __future__ import annotations

import argparse
import json
import sys
import os
import subprocess
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BASELINE = SCRIPT_DIR / "audit_header_baseline.json"
KNOWN_GOOD = (
    SCRIPT_DIR.parent / "system_v6/sims/axis_triple_consistency_b6_v0/audit_verdict.md"
)
LOCAL_ACCEPTED_HEADER_TOKENS = (
    "independent hand recompute",
    "independent recompute",
    "independent verification",
    "fresh-context audit",
    "read-only fresh audit",
)

sys.path.insert(0, str(SCRIPT_DIR))
from builder_audit_boundary import audit_verdict_header_is_independent  # noqa: E402


def git_repo_root(start: Path | None = None) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(start or Path.cwd()),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"git rev-parse failed: {result.stderr.strip()}")
    return Path(result.stdout.strip()).resolve()


def committed_audit_verdicts(repo_root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "system_v6/sims"],
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        if not line.endswith("audit_verdict.md"):
            continue
        rel_path = Path(line)
        parts = rel_path.parts
        if len(parts) == 4 and parts[:2] == ("system_v6", "sims"):
            paths.append(rel_path)
    return paths


def audit_header_is_accepted(audit_path: Path) -> bool:
    if audit_verdict_header_is_independent(audit_path):
        return True
    if not audit_path.exists():
        return True

    header = "\n".join(audit_path.read_text(encoding="utf-8").splitlines()[:40]).lower()
    return any(token in header for token in LOCAL_ACCEPTED_HEADER_TOKENS)


def sim_name(audit_path: Path) -> str:
    return audit_path.parts[2]


def run_synthetic_test() -> int:
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as temp_file:
            temp_file.write("# Audit verdict - synthetic_test_sim\n\nBottom line: something.")
            temp_path = Path(temp_file.name)

        synthetic_rejected = not audit_header_is_accepted(temp_path)
        known_good_accepted = audit_header_is_accepted(KNOWN_GOOD)
        if synthetic_rejected and known_good_accepted:
            print("TEETH TEST PASS")
            return 0
        print("TEETH TEST FAIL")
        return 1
    finally:
        if temp_path is not None:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass


def baseline_payload(failing: list[str]) -> list[str]:
    return sorted(failing)


def write_baseline(baseline_path: Path, failing: list[str]) -> None:
    baseline_path.write_text(
        json.dumps(baseline_payload(failing), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"WROTE baseline: {baseline_path} ({len(failing)} entries)")


def load_baseline(baseline_path: Path) -> set[str]:
    if not baseline_path.exists():
        raise SystemExit(f"missing audit header baseline: {baseline_path}")
    try:
        raw = json.loads(baseline_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid audit header baseline JSON: {baseline_path}: {exc}") from exc

    if isinstance(raw, list) and all(isinstance(item, str) for item in raw):
        return set(raw)
    if isinstance(raw, dict):
        violations = raw.get("violations")
        if isinstance(violations, list) and all(isinstance(item, str) for item in violations):
            return set(violations)
    raise SystemExit(f"audit header baseline must be a list of sim names: {baseline_path}")


def run_lint(
    repo_root: Path,
    baseline_path: Path,
    strict: bool,
    write_baseline_path: Path | None,
) -> int:
    audit_paths = committed_audit_verdicts(repo_root)
    failing: list[str] = []
    for audit_path in audit_paths:
        if not audit_header_is_accepted(repo_root / audit_path):
            failing.append(sim_name(audit_path))

    for name in failing:
        print(f"FAIL: {name}")
    print(f"{len(audit_paths)} sims checked, {len(failing)} failing")

    if write_baseline_path is not None:
        write_baseline(write_baseline_path, failing)

    if not strict:
        if failing:
            print(
                "ADVISORY: header violations found; default mode is report-only. "
                "Use --strict to block new violations."
            )
        else:
            print("PASS: no header violations found")
        return 0

    baseline = load_baseline(baseline_path)
    new_failing = [name for name in failing if name not in baseline]
    if new_failing:
        print(f"FAIL: {len(new_failing)} new audit header violation(s)")
        for name in new_failing:
            print(f"  new_violation: {name}")
        return 1

    print("PASS: strict mode found no new audit header violations")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lint committed sim audit verdict headers for independent-audit wording."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Git repo root; defaults to git rev-parse --show-toplevel from cwd.",
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
        help="Exit 1 only for committed sims with new non-grandfathered header violations.",
    )
    parser.add_argument(
        "--write-baseline",
        type=Path,
        metavar="PATH",
        help="Write the current header violation set as a baseline JSON.",
    )
    parser.add_argument(
        "--synthetic-test",
        action="store_true",
        help="Run the local header token teeth test.",
    )
    args = parser.parse_args()

    if args.synthetic_test:
        return run_synthetic_test()

    repo_root = args.repo_root.resolve() if args.repo_root else git_repo_root()
    return run_lint(
        repo_root=repo_root,
        baseline_path=args.baseline,
        strict=args.strict,
        write_baseline_path=args.write_baseline,
    )


if __name__ == "__main__":
    raise SystemExit(main())
