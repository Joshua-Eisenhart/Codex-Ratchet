#!/usr/bin/env python3
"""Inventory Codex skill and agent source surfaces.

The goal is a deterministic starting point for skill/agent upgrades. The script
does not promote anything; it reports what exists and where it lives.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - repo env has PyYAML, fallback is defensive.
    yaml = None


DEFAULT_CODEX_PRIMARY_HOME = Path.home() / ".codex"
DEFAULT_CODEX_HOME = Path.home() / ".codex-second"
DEFAULT_AGENTS_HOME = Path.home() / ".agents"
DEFAULT_HERMES_HOME = Path.home() / ".hermes"
DEFAULT_WIKI_ROOT = Path.home() / "wiki"
KNOWN_GAP_SKILLS = {
    "bounded-hermes-intake",
    "codex-skill-agent-upgrader",
    "codex-ratchet-sim-audit-spine",
    "codex-ratchet-tool-status-auditor",
    "lego-sim-classifier",
}
CODEX_RATCHET_SKILLS = {
    "three-engine-sim",
    "julia-sim",
    "jax-sim",
    "pytorch-sim",
    "codex-ratchet-tool-status-auditor",
    "lego-sim-classifier",
    "codex-skill-agent-upgrader",
    "karpathy-bounded-improve",
    "three-council-wizard-v4-3",
}


@dataclass(frozen=True)
class SkillRecord:
    name: str
    description: str
    path: str
    root: str
    valid_frontmatter: bool


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _parse_frontmatter(path: Path) -> dict[str, Any]:
    text = _read_text(path)
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    raw = match.group(1)
    if yaml is None:
        result: dict[str, Any] = {}
        for line in raw.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip().strip('"')
        return result
    parsed = yaml.safe_load(raw)
    return parsed if isinstance(parsed, dict) else {}


def _skill_records(root: Path, label: str) -> list[SkillRecord]:
    if not root.exists():
        return []
    records: list[SkillRecord] = []
    for skill_md in sorted(root.rglob("SKILL.md")):
        frontmatter = _parse_frontmatter(skill_md)
        name = frontmatter.get("name")
        description = frontmatter.get("description")
        records.append(
            SkillRecord(
                name=name if isinstance(name, str) else "",
                description=description if isinstance(description, str) else "",
                path=str(skill_md),
                root=label,
                valid_frontmatter=bool(name and description),
            )
        )
    return records


def _openai_yaml_records(root: Path, label: str) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("agents/openai.yaml")):
        relative_parts = path.relative_to(root).parts
        skill_name = relative_parts[0] if relative_parts else ""
        errors: list[str] = []
        payload: dict[str, Any] = {}
        try:
            parsed = yaml.safe_load(_read_text(path)) if yaml is not None else {}
            payload = parsed if isinstance(parsed, dict) else {}
        except Exception as exc:  # pragma: no cover - exact parser errors vary.
            errors.append(f"yaml_parse_error:{exc.__class__.__name__}")
        interface = payload.get("interface") if isinstance(payload, dict) else None
        if not isinstance(interface, dict):
            errors.append("missing_interface")
            interface = {}
        display_name = interface.get("display_name")
        short_description = interface.get("short_description")
        default_prompt = interface.get("default_prompt")
        if not isinstance(display_name, str) or not display_name.strip():
            errors.append("missing_display_name")
        if not isinstance(short_description, str) or not short_description.strip():
            errors.append("missing_short_description")
        elif not 25 <= len(short_description) <= 64:
            errors.append(f"short_description_length:{len(short_description)}")
        if not isinstance(default_prompt, str) or not default_prompt.strip():
            errors.append("missing_default_prompt")
        records.append(
            {
                "skill_name": skill_name,
                "path": str(path),
                "root": label,
                "valid": not errors,
                "errors": errors,
                "short_description_length": len(short_description) if isinstance(short_description, str) else None,
            }
        )
    return records


def _dir_compare(left: Path, right: Path) -> dict[str, Any]:
    if not left.exists() or not right.exists():
        return {
            "left": str(left),
            "right": str(right),
            "matches": False,
            "missing_left": not left.exists(),
            "missing_right": not right.exists(),
            "left_only": [],
            "right_only": [],
            "changed": [],
        }

    comparison = filecmp.dircmp(left, right)
    left_only: list[str] = []
    right_only: list[str] = []
    changed: list[str] = []

    def walk(cmp: filecmp.dircmp[str], prefix: Path = Path()) -> None:
        left_only.extend(str(prefix / name) for name in cmp.left_only)
        right_only.extend(str(prefix / name) for name in cmp.right_only)
        changed.extend(str(prefix / name) for name in cmp.diff_files)
        for name, subcmp in cmp.subdirs.items():
            walk(subcmp, prefix / name)

    walk(comparison)
    return {
        "left": str(left),
        "right": str(right),
        "matches": not (left_only or right_only or changed),
        "missing_left": False,
        "missing_right": False,
        "left_only": sorted(left_only),
        "right_only": sorted(right_only),
        "changed": sorted(changed),
    }


def _markdown_files(root: Path) -> list[dict[str, str]]:
    if not root.exists():
        return []
    records: list[dict[str, str]] = []
    for path in sorted(root.glob("*.md")):
        text = _read_text(path)
        first_heading = ""
        for line in text.splitlines():
            if line.startswith("#"):
                first_heading = line.lstrip("#").strip()
                break
        records.append({"name": path.stem, "path": str(path), "heading": first_heading})
    return records


def _markdown_tree(root: Path, label: str) -> dict[str, Any]:
    if not root.exists():
        return {"root": str(root), "label": label, "count": 0, "items": []}
    items = []
    for path in sorted(root.rglob("*.md")):
        text = _read_text(path)
        first_heading = ""
        title = ""
        for line in text.splitlines():
            if line.startswith("title:") and not title:
                title = line.split(":", 1)[1].strip().strip('"')
            if line.startswith("#") and not first_heading:
                first_heading = line.lstrip("#").strip()
            if title and first_heading:
                break
        items.append(
            {
                "path": str(path),
                "relative_path": str(path.relative_to(root)),
                "title": title,
                "heading": first_heading,
            }
        )
    return {"root": str(root), "label": label, "count": len(items), "items": items}


def _count_by_prefix(records: list[SkillRecord]) -> dict[str, int]:
    prefixes: dict[str, int] = {}
    for record in records:
        prefix = record.name.split("-", 1)[0] if record.name else "_unnamed"
        prefixes[prefix] = prefixes.get(prefix, 0) + 1
    return dict(sorted(prefixes.items()))


def build_inventory(
    repo_root: Path,
    codex_primary_home: Path,
    codex_home: Path,
    agents_home: Path,
    hermes_home: Path,
    wiki_root: Path,
) -> dict[str, Any]:
    codex_primary_installed = _skill_records(codex_primary_home / "skills", "codex_primary_installed")
    codex_secondary_installed = _skill_records(codex_home / "skills", "codex_installed")
    codex_installed = codex_primary_installed + codex_secondary_installed
    agents_installed = _skill_records(agents_home / "skills", "agents_installed")
    hermes_installed = _skill_records(hermes_home / "skills", "hermes_installed")
    repo_codex = _skill_records(repo_root / "system_v5" / "codex_skills", "repo_codex_skills")
    claude_skills = _skill_records(repo_root / ".claude" / "skills", "claude_skills")
    system_v4_specs = _skill_records(repo_root / "system_v4" / "skill_specs", "system_v4_skill_specs")
    all_known_skill_names = {record.name for record in codex_installed + agents_installed + repo_codex if record.name}
    missing_gap_skills = sorted(KNOWN_GAP_SKILLS - all_known_skill_names)
    openai_yaml_records = {
        "codex_primary_installed": _openai_yaml_records(
            codex_primary_home / "skills", "codex_primary_installed"
        ),
        "repo_codex_skills": _openai_yaml_records(repo_root / "system_v5" / "codex_skills", "repo_codex_skills"),
        "codex_installed": _openai_yaml_records(codex_home / "skills", "codex_installed"),
    }
    repo_active_skill_parity = {
        skill: _dir_compare(repo_root / "system_v5" / "codex_skills" / skill, codex_primary_home / "skills" / skill)
        for skill in sorted(CODEX_RATCHET_SKILLS)
    }
    repo_secondary_skill_parity = {
        skill: _dir_compare(repo_root / "system_v5" / "codex_skills" / skill, codex_home / "skills" / skill)
        for skill in sorted(CODEX_RATCHET_SKILLS)
    }

    sections = {
        "codex_installed": codex_installed,
        "agents_installed": agents_installed,
        "repo_codex_skills": repo_codex,
        "claude_skills": claude_skills,
        "system_v4_skill_specs": system_v4_specs,
    }

    return {
        "repo_root": str(repo_root),
        "codex_primary_home": str(codex_primary_home),
        "codex_home": str(codex_home),
        "agents_home": str(agents_home),
        "hermes_home": str(hermes_home),
        "wiki_root": str(wiki_root),
        "sections": {
            name: {
                "count": len(records),
                "valid_frontmatter": sum(1 for record in records if record.valid_frontmatter),
                "prefix_counts": _count_by_prefix(records),
                "items": [record.__dict__ for record in records],
            }
            for name, records in sections.items()
        },
        "hermes_installed": {
            "count": len(hermes_installed),
            "valid_frontmatter": sum(1 for record in hermes_installed if record.valid_frontmatter),
            "prefix_counts": _count_by_prefix(hermes_installed),
            "items": [record.__dict__ for record in hermes_installed],
        },
        "claude_agents": {
            "count": len(_markdown_files(repo_root / ".claude" / "agents")),
            "items": _markdown_files(repo_root / ".claude" / "agents"),
        },
        "openai_yaml": {
            root_name: {
                "count": len(records),
                "valid": sum(1 for record in records if record["valid"]),
                "items": records,
            }
            for root_name, records in openai_yaml_records.items()
        },
        "repo_active_skill_parity": repo_active_skill_parity,
        "repo_secondary_skill_parity": repo_secondary_skill_parity,
        "wiki_surfaces": {
            "hermes_current": _markdown_tree(wiki_root / "hermes-current", "hermes_current"),
            "hermes_wizard_current": _markdown_tree(
                wiki_root / "wizard" / "hermes-version-current", "hermes_wizard_current"
            ),
            "queries": _markdown_tree(wiki_root / "queries", "queries"),
            "concepts_skill_and_hermes": (lambda items: {
                "root": str(wiki_root / "concepts"),
                "label": "concepts_skill_and_hermes",
                "count": len(items),
                "items": items,
            })(
                [
                    item
                    for item in _markdown_tree(wiki_root / "concepts", "concepts")["items"]
                    if any(term in item["relative_path"].lower() for term in ("skill", "agent", "hermes", "karpathy"))
                ]
            ),
        },
        "upgrade_gaps": {
            "missing_codex_skills": missing_gap_skills,
            "notes": [
                "Missing means no installed .codex-second/.agents or repo-held Codex SKILL.md with that exact name was found.",
                "Claude and Hermes sources remain reference-only until ported through authority and validation gates.",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--codex-primary-home", type=Path, default=DEFAULT_CODEX_PRIMARY_HOME)
    parser.add_argument("--codex-home", type=Path, default=DEFAULT_CODEX_HOME)
    parser.add_argument("--agents-home", type=Path, default=DEFAULT_AGENTS_HOME)
    parser.add_argument("--hermes-home", type=Path, default=DEFAULT_HERMES_HOME)
    parser.add_argument("--wiki-root", type=Path, default=DEFAULT_WIKI_ROOT)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    payload = build_inventory(
        args.repo_root.resolve(),
        args.codex_primary_home.expanduser().resolve(),
        args.codex_home.expanduser().resolve(),
        args.agents_home.expanduser().resolve(),
        args.hermes_home.expanduser().resolve(),
        args.wiki_root.expanduser().resolve(),
    )
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
