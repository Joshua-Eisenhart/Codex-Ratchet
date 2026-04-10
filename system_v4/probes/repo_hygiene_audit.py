#!/usr/bin/env python3
"""
Repo hygiene audit.

Builds one machine-readable report for:
  - dirty worktree pressure
  - misplaced root-level result JSONs
  - split result directory drift
  - duplicate control/session state directories
  - bulky path classes that should stay out of normal coding loops
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, UTC
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
OUT_PATH = RESULTS_DIR / "repo_hygiene_audit_results.json"
SECONDARY_RESULTS_DIR = SCRIPT_DIR / "sim_results"
HYGIENE_QUARANTINE_DIR = PROJECT_DIR / "work" / "hygiene_quarantine"

ROOT_RESULT_GLOBS = ("results*.json",)
AGENT_STATE_DIRS = (".agent", ".agents")
CODEX_HOME_DIRS = (".codex_bg_home", ".codex_runtime_home")
AUTORESEARCH_STATE_PATH = PROJECT_DIR / "autoresearch-state.json"
GENERATED_DIR_HINTS = (
    "/obsidian_vault/",
    "/work/",
    "/system_v4/probes/a2_state/",
    "/system_v4/probes/sim_results/",
    "/system_v3/a2_state/",
)
GENERATED_ROOT_FILES = {
    "autoresearch-state.json",
}
RECENT_COMMIT_WINDOW = 12
LANE_SCOPE_MAX_FILES = 6
SOURCE_BUCKET_RULES = (
    ("build_contract", ("Makefile", "requirements-runtime.txt", "requirements-sim-stack.txt", "pyproject.toml")),
    ("root_runtime", ("imessage_bot.py",)),
    ("probe_source", ("system_v4/probes/",)),
    ("skill_runtime", ("system_v4/skills/",)),
    ("legacy_runtime", ("system_v3/", "system_v5/")),
    ("docs_and_specs", ("CLAUDE.md", "new docs/", "docs/", "specs/")),
    ("agent_state", (".agent/", ".agents/", ".codex_bg_home/", ".codex_runtime_home/")),
)

PATH_CLASS_LIMITS = {
    "obsidian_vault": (PROJECT_DIR / "obsidian_vault", 5000),
    "work_zip_dropins": (PROJECT_DIR / "work" / "zip_dropins", 1000),
    "primary_sim_results": (RESULTS_DIR, 500),
    "secondary_sim_results": (SECONDARY_RESULTS_DIR, 1),
}


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())


def parse_status_path(line: str) -> str:
    payload = line[3:]
    if " -> " in payload:
        payload = payload.split(" -> ", 1)[1]
    return payload.strip().strip('"')


def is_generated_artifact_path(rel_path: str) -> bool:
    normalized = f"/{rel_path}"
    return (
        (rel_path.startswith("results") and rel_path.endswith(".json"))
        or rel_path.endswith("_results.json")
        or "/a2_state/sim_results/" in normalized
        or "/probes/sim_results/" in normalized
        or rel_path in GENERATED_ROOT_FILES
        or any(hint in normalized for hint in GENERATED_DIR_HINTS)
    )


def bucket_source_dirty_path(rel_path: str) -> str:
    normalized = rel_path.strip().strip('"')
    for label, prefixes in SOURCE_BUCKET_RULES:
        if any(normalized == prefix or normalized.startswith(prefix) for prefix in prefixes):
            return label
    return "other_source"


def sample_counter(counter: Counter[str], limit: int = 8) -> list[dict[str, int]]:
    return [
        {"label": label, "count": count}
        for label, count in counter.most_common(limit)
    ]


def git_stdout(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout


def branch_divergence_summary() -> dict[str, int | None]:
    raw = git_stdout("rev-list", "--left-right", "--count", "origin/main...HEAD").strip()
    if not raw:
        return {"behind_count": None, "ahead_count": None}
    parts = raw.split()
    if len(parts) != 2:
        return {"behind_count": None, "ahead_count": None}
    try:
        behind_count = int(parts[0])
        ahead_count = int(parts[1])
    except ValueError:
        return {"behind_count": None, "ahead_count": None}
    return {"behind_count": behind_count, "ahead_count": ahead_count}


def recent_checkpoint_scope_findings(limit: int = RECENT_COMMIT_WINDOW) -> list[dict]:
    findings: list[dict] = []
    raw = git_stdout("log", f"-n{limit}", "--format=%H%x09%s")
    if not raw:
        return findings

    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            commit_sha, subject = line.split("\t", 1)
        except ValueError:
            continue
        subject_lower = subject.lower()
        if "checkpoint" not in subject_lower or "lane" not in subject_lower:
            continue
        changed_paths = [
            item
            for item in git_stdout("diff-tree", "--no-commit-id", "--name-only", "-r", commit_sha).splitlines()
            if item.strip()
        ]
        if len(changed_paths) <= LANE_SCOPE_MAX_FILES:
            continue
        findings.append({
            "kind": "checkpoint_scope_drift",
            "severity": "advisory",
            "commit": commit_sha[:8],
            "subject": subject,
            "changed_path_count": len(changed_paths),
            "max_expected_for_lane": LANE_SCOPE_MAX_FILES,
            "sample_paths": changed_paths[:12],
        })

    return findings


def git_status_summary() -> dict:
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=PROJECT_DIR,
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": f"{exc.__class__.__name__}: {exc}",
            "tracked_dirty_count": 0,
            "untracked_count": 0,
            "total_dirty_count": 0,
            "status_class_counts": {},
            "top_dirty_prefixes": [],
        }

    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    tracked_dirty = 0
    untracked = 0
    source_dirty = 0
    generated_dirty = 0
    status_classes: Counter[str] = Counter()
    prefixes: Counter[str] = Counter()
    source_buckets: Counter[str] = Counter()
    generated_buckets: Counter[str] = Counter()

    for line in lines:
        if line.startswith("?? "):
            untracked += 1
            status_classes["untracked"] += 1
        else:
            tracked_dirty += 1
            index_status, worktree_status = line[:2]
            if "M" in (index_status, worktree_status):
                status_classes["modified"] += 1
            if "A" in (index_status, worktree_status):
                status_classes["added"] += 1
            if "D" in (index_status, worktree_status):
                status_classes["deleted"] += 1
            if "R" in (index_status, worktree_status):
                status_classes["renamed"] += 1

        rel_path = parse_status_path(line)
        if is_generated_artifact_path(rel_path):
            generated_dirty += 1
            generated_buckets["generated_artifacts"] += 1
        else:
            source_dirty += 1
            source_buckets[bucket_source_dirty_path(rel_path)] += 1
        parts = Path(rel_path).parts
        prefix = parts[0] if parts else "(root)"
        prefixes[prefix] += 1

    return {
        "ok": completed.returncode == 0,
        "tracked_dirty_count": tracked_dirty,
        "untracked_count": untracked,
        "source_dirty_count": source_dirty,
        "generated_dirty_count": generated_dirty,
        "total_dirty_count": tracked_dirty + untracked,
        "status_class_counts": dict(status_classes),
        "dirty_source_buckets": sample_counter(source_buckets, limit=12),
        "dirty_generated_buckets": sample_counter(generated_buckets, limit=12),
        "top_dirty_prefixes": [
            {"prefix": prefix, "count": count}
            for prefix, count in prefixes.most_common(12)
        ],
    }


def root_result_files() -> list[str]:
    matches: list[str] = []
    for pattern in ROOT_RESULT_GLOBS:
        for path in sorted(PROJECT_DIR.glob(pattern)):
            if path.is_file():
                matches.append(path.name)
    return matches


def split_secondary_results() -> tuple[list[str], list[str]]:
    primary = {path.name for path in RESULTS_DIR.glob("*.json")}
    unique: list[str] = []
    duplicates: list[str] = []
    for path in sorted(SECONDARY_RESULTS_DIR.glob("*.json")):
        if path.name in primary:
            duplicates.append(path.name)
        else:
            unique.append(path.name)
    return unique, duplicates


def directory_presence(names: tuple[str, ...]) -> list[str]:
    return [name for name in names if (PROJECT_DIR / name).exists()]


def build_findings(
    git_summary: dict,
    branch_divergence: dict,
    recent_checkpoint_findings: list[dict],
    root_results: list[str],
    secondary_unique_results: list[str],
    secondary_duplicate_results: list[str],
    agent_dirs: list[str],
    codex_dirs: list[str],
    path_class_counts: dict[str, dict],
) -> tuple[list[dict], list[dict], list[dict]]:
    blockers: list[dict] = []
    advisories: list[dict] = []
    repair_candidates: list[dict] = []

    source_dirty = git_summary.get("source_dirty_count", 0)
    generated_dirty = git_summary.get("generated_dirty_count", 0)
    total_dirty = git_summary.get("total_dirty_count", 0)

    if source_dirty >= 25:
        blockers.append({
            "kind": "dirty_source_pressure",
            "severity": "high",
            "source_dirty_count": source_dirty,
            "dirty_source_buckets": git_summary.get("dirty_source_buckets", []),
            "top_dirty_prefixes": git_summary.get("top_dirty_prefixes", []),
        })
        repair_candidates.append({
            "kind": "dirty_source_pressure",
            "action_class": "human_scoped_checkpoint",
            "safe_auto": False,
            "recommendation": "Checkpoint or quarantine bounded source/config work instead of letting active surfaces drift.",
            "dirty_source_buckets": git_summary.get("dirty_source_buckets", []),
        })

    if generated_dirty >= 100:
        advisories.append({
            "kind": "dirty_generated_pressure",
            "severity": "advisory",
            "generated_dirty_count": generated_dirty,
            "total_dirty_count": total_dirty,
        })

    ahead_count = branch_divergence.get("ahead_count")
    if isinstance(ahead_count, int) and ahead_count >= 6:
        advisories.append({
            "kind": "local_commit_stack_depth",
            "severity": "advisory",
            "ahead_count": ahead_count,
            "recommended_push_threshold": 5,
        })

    advisories.extend(recent_checkpoint_findings)

    if root_results:
        blockers.append({
            "kind": "root_result_json_orphans",
            "severity": "high",
            "files": root_results,
        })
        repair_candidates.append({
            "kind": "root_result_json_orphans",
            "action_class": "quarantine_root_results",
            "safe_auto": True,
            "recommendation": "Quarantine root-level result JSONs into a bounded hygiene quarantine instead of leaving them at repo root.",
            "files": root_results,
            "suggested_quarantine_root": str((HYGIENE_QUARANTINE_DIR / "root_result_orphans").relative_to(PROJECT_DIR)),
        })

    if secondary_duplicate_results:
        blockers.append({
            "kind": "duplicate_result_basenames",
            "severity": "high",
            "count": len(secondary_duplicate_results),
            "files": secondary_duplicate_results[:20],
        })
        repair_candidates.append({
            "kind": "duplicate_result_basenames",
            "action_class": "manual_result_routing",
            "safe_auto": False,
            "recommendation": "Resolve duplicate result basenames between canonical and legacy result roots.",
            "files": secondary_duplicate_results[:20],
        })

    secondary_result_count = len(secondary_unique_results) + len(secondary_duplicate_results)
    if secondary_result_count > 0:
        blockers.append({
            "kind": "secondary_result_directory_populated",
            "severity": "high",
            "path": str(SECONDARY_RESULTS_DIR.relative_to(PROJECT_DIR)),
            "json_file_count": secondary_result_count,
            "unique_json_file_count": len(secondary_unique_results),
            "duplicate_json_file_count": len(secondary_duplicate_results),
        })
        repair_candidates.append({
            "kind": "secondary_result_directory_populated",
            "action_class": "quarantine_secondary_unique_results",
            "safe_auto": len(secondary_duplicate_results) == 0 and len(secondary_unique_results) > 0,
            "opt_in_only": True,
            "recommendation": "Only the unique legacy results are candidates for bounded quarantine; duplicate basenames still require manual routing.",
            "path": str(SECONDARY_RESULTS_DIR.relative_to(PROJECT_DIR)),
            "safe_unique_files": secondary_unique_results[:50],
            "blocked_duplicate_files": secondary_duplicate_results[:20],
            "suggested_quarantine_root": str((HYGIENE_QUARANTINE_DIR / "secondary_unique_results").relative_to(PROJECT_DIR)),
        })

    if len(agent_dirs) > 1:
        advisories.append({
            "kind": "duplicate_agent_state_dirs",
            "severity": "advisory",
            "present_dirs": agent_dirs,
        })
        repair_candidates.append({
            "kind": "duplicate_agent_state_dirs",
            "action_class": "manual_state_audit",
            "safe_auto": False,
            "recommendation": "Audit .agent vs .agents ownership before any consolidation.",
        })

    if len(codex_dirs) > 1:
        advisories.append({
            "kind": "multiple_codex_runtime_homes",
            "severity": "advisory",
            "present_dirs": codex_dirs,
        })
        repair_candidates.append({
            "kind": "multiple_codex_runtime_homes",
            "action_class": "manual_state_audit",
            "safe_auto": False,
            "recommendation": "Audit .codex_bg_home vs .codex_runtime_home before cleanup or automation.",
        })

    if AUTORESEARCH_STATE_PATH.exists():
        advisories.append({
            "kind": "repo_root_autoresearch_state_present",
            "severity": "advisory",
            "path": AUTORESEARCH_STATE_PATH.name,
        })

    for label, info in path_class_counts.items():
        if info["file_count"] >= info["threshold"]:
            advisories.append({
                "kind": "bulky_path_class",
                "severity": "advisory",
                "label": label,
                "path": info["path"],
                "file_count": info["file_count"],
                "threshold": info["threshold"],
            })

    return blockers, advisories, repair_candidates


def main() -> int:
    strict = "--strict" in sys.argv[1:]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    git_summary = git_status_summary()
    branch_divergence = branch_divergence_summary()
    recent_checkpoint_findings = recent_checkpoint_scope_findings()
    root_results = root_result_files()
    secondary_unique_results, secondary_duplicate_results = split_secondary_results()
    secondary_result_count = len(secondary_unique_results) + len(secondary_duplicate_results)
    primary_result_count = sum(1 for _ in RESULTS_DIR.glob("*.json"))
    agent_dirs = directory_presence(AGENT_STATE_DIRS)
    codex_dirs = directory_presence(CODEX_HOME_DIRS)

    path_class_counts: dict[str, dict] = {}
    for label, (path, threshold) in PATH_CLASS_LIMITS.items():
        path_class_counts[label] = {
            "path": str(path.relative_to(PROJECT_DIR)) if is_within(path, PROJECT_DIR) else str(path),
            "file_count": count_files(path),
            "threshold": threshold,
        }

    blockers, advisories, repair_candidates = build_findings(
        git_summary=git_summary,
        branch_divergence=branch_divergence,
        recent_checkpoint_findings=recent_checkpoint_findings,
        root_results=root_results,
        secondary_unique_results=secondary_unique_results,
        secondary_duplicate_results=secondary_duplicate_results,
        agent_dirs=agent_dirs,
        codex_dirs=codex_dirs,
        path_class_counts=path_class_counts,
    )

    summary = {
        "blocker_count": len(blockers),
        "advisory_count": len(advisories),
        "repair_candidate_count": len(repair_candidates),
        "primary_result_count": primary_result_count,
        "secondary_result_count": secondary_result_count,
        "secondary_unique_result_count": len(secondary_unique_results),
        "secondary_duplicate_result_count": len(secondary_duplicate_results),
        "root_result_orphan_count": len(root_results),
        "duplicate_result_basename_count": len(secondary_duplicate_results),
        "source_dirty_count": git_summary.get("source_dirty_count", 0),
        "generated_dirty_count": git_summary.get("generated_dirty_count", 0),
        "dirty_worktree_count": git_summary.get("total_dirty_count", 0),
        "dirty_source_bucket_count": len(git_summary.get("dirty_source_buckets", [])),
        "ok": len(blockers) == 0,
    }

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "strict": strict,
        "blocker_count": len(blockers),
        "advisory_count": len(advisories),
        "repair_candidate_count": len(repair_candidates),
        "source_dirty_count": git_summary.get("source_dirty_count", 0),
        "generated_dirty_count": git_summary.get("generated_dirty_count", 0),
        "dirty_worktree_count": git_summary.get("total_dirty_count", 0),
        "git": git_summary,
        "branch_divergence": branch_divergence,
        "recent_checkpoint_scope_findings": recent_checkpoint_findings,
        "root_result_files": root_results,
        "secondary_unique_results": secondary_unique_results,
        "duplicate_result_basenames": secondary_duplicate_results,
        "primary_result_dir": str(RESULTS_DIR.relative_to(PROJECT_DIR)),
        "secondary_result_dir": str(SECONDARY_RESULTS_DIR.relative_to(PROJECT_DIR)),
        "agent_state_dirs": agent_dirs,
        "codex_runtime_dirs": codex_dirs,
        "path_class_counts": path_class_counts,
        "summary": summary,
        "blockers": blockers,
        "advisories": advisories,
        "repair_candidates": repair_candidates,
    }

    OUT_PATH.write_text(json.dumps(report, indent=2))
    print(f"Wrote {OUT_PATH}")
    print(f"blocker_count={summary['blocker_count']}")
    print(f"advisory_count={summary['advisory_count']}")
    print(f"dirty_worktree_count={summary['dirty_worktree_count']}")

    if strict and blockers:
        print("REPO HYGIENE AUDIT FAILED")
        return 1

    if blockers:
        print("REPO HYGIENE AUDIT WARN")
    else:
        print("REPO HYGIENE AUDIT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
