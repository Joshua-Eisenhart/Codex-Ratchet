#!/usr/bin/env python3
"""
Lev-OS Skills Sync
========================
Diffs lev-os/agents skills against existing ingested state in obsidian.
Optionally pulls latest from upstream with --pull flag.
Outputs a manifest of new/changed/removed skills for C-layer evaluation.

Note: Default behavior is a LOCAL DIFF only. Upstream refresh requires --pull.

This script runs at the C1 layer — it reads external skill repos but does NOT
modify the owner graph or A2 state. C → A2 promotion happens through the
normal intake pipeline only.

Usage:
    python3 system_v4/skills/levos_skills_sync.py              # local diff only
    python3 system_v4/skills/levos_skills_sync.py --pull       # pull then diff
    python3 system_v4/skills/levos_skills_sync.py --diff-only  # diff, skip manifest write
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
LEVOS_DIR = REPO_ROOT / "work" / "reference_repos" / "lev-os" / "agents"
SKILLS_DIR = LEVOS_DIR / "skills"
MANIFEST_DIR = REPO_ROOT / "work" / "c_layer" / "levos_sync"
MANIFEST_FILE = MANIFEST_DIR / "skills_manifest.json"
OBSIDIAN_DIR = REPO_ROOT / "obsidian_vault"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _git_pull(repo_dir: Path) -> dict[str, Any]:
    """Pull latest from origin."""
    try:
        result = subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            cwd=str(repo_dir),
            capture_output=True, text=True, timeout=30,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _scan_levos_skills() -> list[dict[str, Any]]:
    """Scan lev-os/agents/skills for SKILL.md files."""
    skills = []
    if not SKILLS_DIR.exists():
        return skills

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        # Read frontmatter
        content = skill_md.read_text(encoding="utf-8", errors="replace")
        lines = content.split("\n")

        # Extract name and description from YAML frontmatter
        name = skill_dir.name
        description = ""
        in_frontmatter = False
        for line in lines:
            if line.strip() == "---":
                in_frontmatter = not in_frontmatter
                continue
            if in_frontmatter:
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip().strip("'\"")
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip().strip("'\"")

        # Count files in skill dir
        file_count = sum(1 for _ in skill_dir.rglob("*") if _.is_file())

        skills.append({
            "skill_id": skill_dir.name,
            "name": name,
            "description": description,
            "path": str(skill_dir.relative_to(REPO_ROOT)),
            "file_count": file_count,
            "skill_md_size": len(content),
        })

    return skills


def _check_obsidian_ingested() -> set[str]:
    """Check which lev-os skills have already been ingested into obsidian."""
    ingested = set()
    if not OBSIDIAN_DIR.exists():
        return ingested

    for md in OBSIDIAN_DIR.glob("lev_skill_*.md"):
        # Extract skill name from filename: lev_skill_foo.md → foo
        name = md.stem.replace("lev_skill_", "").replace("-", "_")
        ingested.add(name)

    return ingested


def _build_diff(current_skills: list[dict], ingested: set[str]) -> dict[str, list]:
    """Compare current lev-os skills against obsidian ingestion state."""
    current_ids = {s["skill_id"].replace("-", "_") for s in current_skills}

    new_skills = [s for s in current_skills if s["skill_id"].replace("-", "_") not in ingested]
    removed = ingested - current_ids
    existing = [s for s in current_skills if s["skill_id"].replace("-", "_") in ingested]

    return {
        "new": [s["skill_id"] for s in new_skills],
        "existing": [s["skill_id"] for s in existing],
        "removed_from_upstream": list(removed),
    }


def run_sync(pull: bool = False, diff_only: bool = False) -> dict[str, Any]:
    """Run the lev-os skills sync."""
    print(f"\n{'='*60}")
    print("LEV-OS SKILLS SYNC (C1 Layer)")
    print(f"{'='*60}")

    # 1. Optionally pull latest
    pull_result = None
    if pull:
        if LEVOS_DIR.exists():
            pull_result = _git_pull(LEVOS_DIR.parent)
            print(f"  git pull: {'✓' if pull_result['success'] else '✗'}")
            if not pull_result["success"]:
                print(f"    {pull_result.get('stderr', pull_result.get('error', ''))}")
        else:
            print(f"  ⚠ lev-os repo not found at {LEVOS_DIR}")
            return {"status": "REPO_NOT_FOUND", "path": str(LEVOS_DIR)}

    # 2. Scan skills
    skills = _scan_levos_skills()
    print(f"  Skills found: {len(skills)}")

    # 3. Check ingestion state
    ingested = _check_obsidian_ingested()
    print(f"  Already ingested in obsidian: {len(ingested)}")

    # 4. Build diff
    diff = _build_diff(skills, ingested)
    print(f"  New (not yet ingested): {len(diff['new'])}")
    if diff["new"]:
        for s in diff["new"][:10]:
            print(f"    + {s}")
    print(f"  Existing (already ingested): {len(diff['existing'])}")
    print(f"  Removed from upstream: {len(diff['removed_from_upstream'])}")

    result = {
        "timestamp_utc": _utc_iso(),
        "levos_repo_path": str(LEVOS_DIR),
        "total_skills": len(skills),
        "ingested_count": len(ingested),
        "diff": diff,
        "skills": skills,
        "pull_result": pull_result,
    }

    # 5. Write manifest
    if not diff_only:
        MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
        MANIFEST_FILE.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"\n  Manifest: {MANIFEST_FILE}")

    print(f"  Status: SYNCED")
    return result


if __name__ == "__main__":
    import sys
    pull = "--pull" in sys.argv
    diff_only = "--diff-only" in sys.argv
    run_sync(pull=pull, diff_only=diff_only)
