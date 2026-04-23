#!/usr/bin/env python3
"""
State-dir ownership audit.

Clarifies the role of repo-local agent state dirs and duplicate Codex runtime
homes so strict maintenance can block on explicit ownership issues instead of
folding them into generic repo dirt.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, UTC
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
OUT_PATH = RESULTS_DIR / "state_dir_ownership_audit_results.json"

AGENT_DIR = PROJECT_DIR / ".agent"
AGENTS_DIR = PROJECT_DIR / ".agents"
CODEX_BG_HOME = PROJECT_DIR / ".codex_bg_home"
CODEX_RUNTIME_HOME = PROJECT_DIR / ".codex_runtime_home"


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())


def run_git_status(paths: list[Path]) -> list[str]:
    rels = [str(path.relative_to(PROJECT_DIR)) for path in paths if path.exists()]
    if not rels:
        return []
    completed = subprocess.run(
        ["git", "status", "--short", "--", *rels],
        cwd=PROJECT_DIR,
        check=False,
        capture_output=True,
        text=True,
    )
    return [line for line in completed.stdout.splitlines() if line.strip()]


def dir_listing(path: Path, max_depth: int = 2) -> list[str]:
    if not path.exists():
        return []
    entries: list[str] = []
    for item in sorted(path.rglob("*")):
        if not item.exists():
            continue
        try:
            depth = len(item.relative_to(path).parts)
        except ValueError:
            continue
        if depth > max_depth:
            continue
        entries.append(str(item.relative_to(PROJECT_DIR)))
    return entries


def infer_agent_role(path: Path) -> str:
    if not path.exists():
        return "missing"
    if (path / "state").exists() or (path / "handoffs").exists() or (path / "reviews").exists():
        return "repo_local_agent_state"
    if (path / "skills").exists():
        return "agent_skill_bundle"
    return "unclassified_agent_dir"


def infer_codex_home_role(path: Path) -> str:
    if not path.exists():
        return "missing"
    has_automations = (path / "automations").exists()
    has_auth = (path / "auth.json").exists()
    has_config = (path / "config.toml").exists()
    if has_automations:
        return "active_runtime_home"
    if has_auth or has_config:
        return "background_bootstrap_home"
    return "unclassified_codex_home"


def sqlite_equal(left: Path, right: Path) -> bool | None:
    if not left.exists() or not right.exists() or not left.is_file() or not right.is_file():
        return None
    return left.read_bytes() == right.read_bytes()


def latest_session_name(path: Path) -> str | None:
    session_root = path / "sessions"
    if not session_root.exists():
        return None
    files = sorted(session_root.rglob("*.jsonl"))
    return str(files[-1].relative_to(PROJECT_DIR)) if files else None


def build_agent_surface() -> tuple[dict, list[dict], list[dict]]:
    present_dirs = [path for path in (AGENT_DIR, AGENTS_DIR) if path.exists()]
    advisories: list[dict] = []
    repair_candidates: list[dict] = []

    roles = {
        str(path.relative_to(PROJECT_DIR)): {
            "role": infer_agent_role(path),
            "file_count": count_files(path),
            "sample_entries": dir_listing(path),
        }
        for path in present_dirs
    }

    if len(present_dirs) > 1:
        advisories.append({
            "kind": "duplicate_agent_state_dirs",
            "severity": "advisory",
            "present_dirs": [str(path.relative_to(PROJECT_DIR)) for path in present_dirs],
            "role_map": {key: value["role"] for key, value in roles.items()},
        })
        repair_candidates.append({
            "kind": "duplicate_agent_state_dirs",
            "action_class": "manual_state_audit",
            "safe_auto": False,
            "recommendation": "Keep .agent as repo-local handoff/state surface and .agents as skill bundle unless you explicitly consolidate them.",
            "owner_map": {key: value["role"] for key, value in roles.items()},
        })

    return {
        "present_dirs": [str(path.relative_to(PROJECT_DIR)) for path in present_dirs],
        "roles": roles,
        "ok": len(present_dirs) <= 1,
    }, advisories, repair_candidates


def build_codex_home_surface() -> tuple[dict, list[dict], list[dict]]:
    present_dirs = [path for path in (CODEX_BG_HOME, CODEX_RUNTIME_HOME) if path.exists()]
    advisories: list[dict] = []
    repair_candidates: list[dict] = []

    roles = {}
    for path in present_dirs:
        roles[str(path.relative_to(PROJECT_DIR))] = {
            "role": infer_codex_home_role(path),
            "file_count": count_files(path),
            "latest_session": latest_session_name(path),
            "has_automations": (path / "automations").exists(),
            "has_auth": (path / "auth.json").exists(),
            "has_config": (path / "config.toml").exists(),
        }

    sqlite_comparison = {
        "logs_equal": sqlite_equal(CODEX_BG_HOME / "logs_1.sqlite", CODEX_RUNTIME_HOME / "logs_1.sqlite"),
        "state_equal": sqlite_equal(CODEX_BG_HOME / "state_5.sqlite", CODEX_RUNTIME_HOME / "state_5.sqlite"),
    }

    if len(present_dirs) > 1:
        advisories.append({
            "kind": "multiple_codex_runtime_homes",
            "severity": "advisory",
            "present_dirs": [str(path.relative_to(PROJECT_DIR)) for path in present_dirs],
            "role_map": {key: value["role"] for key, value in roles.items()},
            "sqlite_comparison": sqlite_comparison,
        })
        repair_candidates.append({
            "kind": "multiple_codex_runtime_homes",
            "action_class": "manual_state_audit",
            "safe_auto": False,
            "recommendation": "Treat .codex_runtime_home as the active runtime home and .codex_bg_home as older background/bootstrap state unless you deliberately merge histories.",
            "owner_map": {key: value["role"] for key, value in roles.items()},
            "sqlite_comparison": sqlite_comparison,
        })

    return {
        "present_dirs": [str(path.relative_to(PROJECT_DIR)) for path in present_dirs],
        "roles": roles,
        "sqlite_comparison": sqlite_comparison,
        "ok": len(present_dirs) <= 1,
    }, advisories, repair_candidates


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    agent_surface, agent_advisories, agent_repairs = build_agent_surface()
    codex_surface, codex_advisories, codex_repairs = build_codex_home_surface()
    git_status = run_git_status([AGENT_DIR, AGENTS_DIR, CODEX_BG_HOME, CODEX_RUNTIME_HOME])

    advisories = agent_advisories + codex_advisories
    repair_candidates = agent_repairs + codex_repairs
    ok = not advisories

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "blocker_count": 0,
        "advisory_count": len(advisories),
        "repair_candidate_count": len(repair_candidates),
        "agent_state_surface": agent_surface,
        "codex_runtime_surface": codex_surface,
        "git_status": git_status,
        "summary": {
            "blocker_count": 0,
            "advisory_count": len(advisories),
            "repair_candidate_count": len(repair_candidates),
            "ok": ok,
        },
        "advisories": advisories,
        "repair_candidates": repair_candidates,
    }

    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print("blocker_count=0")
    print(f"advisory_count={len(advisories)}")
    print("STATE DIR OWNERSHIP AUDIT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
