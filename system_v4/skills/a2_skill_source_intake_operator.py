"""
a2_skill_source_intake_operator.py

Bounded A2-side intake audit for the broad skill-source corpus and the first
imported lev-os/agents intake/discovery/build cluster.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
A2_INTAKE_REPORT_JSON = "system_v4/a2_state/audit_logs/A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.json"
A2_INTAKE_REPORT_MD = "system_v4/a2_state/audit_logs/A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.md"

FRONT_DOOR_DOCS = {
    "skill_source_corpus": "SKILL_SOURCE_CORPUS.md",
    "repo_skill_integration_tracker": "REPO_SKILL_INTEGRATION_TRACKER.md",
    "skill_candidates_backlog": "SKILL_CANDIDATES_BACKLOG.md",
    "local_source_repo_inventory": "LOCAL_SOURCE_REPO_INVENTORY.md",
}

CANONICAL_A2_INDEX_TARGETS = set(FRONT_DOOR_DOCS.values())

LEV_CLUSTER_MEMBER_PATHS = {
    "lev-intake": "work/reference_repos/lev-os/agents/skills/lev-intake/SKILL.md",
    "skill-discovery": "work/reference_repos/lev-os/agents/skills/skill-discovery/SKILL.md",
    "skill-builder": "work/reference_repos/lev-os/agents/skills/skill-builder/SKILL.md",
}

EXPECTED_LEV_COUNTS = {
    "total": 635,
    "curated": 61,
    "library": 574,
}

FIRST_CLUSTER_MEMBER_CLASSIFICATION = {
    "lev-intake": {
        "classification": "adapt",
        "ratchet_role": "a2-side source intake front door",
        "keep": "bounded intake and smallest-useful-disposition framing",
        "adapt_away_from": [".lev/workshop", "~/.config/lev/config.yaml", "project-doc assumptions"],
    },
    "skill-discovery": {
        "classification": "adapt",
        "ratchet_role": "local-first skill/source resolver over registry and corpus metadata",
        "keep": "local-first discovery and ranking behavior",
        "adapt_away_from": ["qmd", "cm", "~/.agents/skills collections"],
    },
    "skill-builder": {
        "classification": "adapt",
        "ratchet_role": "staged build/admission evaluator for imported material",
        "keep": "staged validation, prior-art checks, and propose-not-activate rule",
        "adapt_away_from": ["skill-seekers", "skills.sh", "Claude-specific packaging"],
    },
}

FIRST_CLUSTER_RECOMMENDATIONS = [
    "Keep the first imported cluster bounded to A2-side intake, discovery, and staged build/admission semantics.",
    "Do not port qmd/cm, skill-seekers, or workshop path overlays into the first Ratchet-native slice.",
    "Promote the next imported cluster only after the current intake report is repo-held and stable.",
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _count_skill_docs(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    for _, dirnames, filenames in os.walk(path):
        dirnames[:] = [dirname for dirname in dirnames if dirname != ".git"]
        for filename in filenames:
            if filename == "SKILL.md":
                count += 1
    return count


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _doc_index_paths(repo_root: Path) -> set[str]:
    doc_index_path = repo_root / "system_v3" / "a2_state" / "doc_index.json"
    if not doc_index_path.exists():
        return set()
    doc_index = _load_json(doc_index_path)
    documents = doc_index.get("documents", [])
    if not isinstance(documents, list):
        return set()
    paths: set[str] = set()
    for entry in documents:
        if isinstance(entry, dict):
            path = entry.get("path")
            if isinstance(path, str):
                paths.add(path)
    return paths


def _render_markdown_report(report: dict[str, Any]) -> str:
    front_door_lines = []
    for label, info in report.get("front_door", {}).items():
        front_door_lines.append(
            f"- `{label}`: exists={info.get('exists')} indexed_in_a2={info.get('indexed_in_a2')}"
        )

    member_lines = []
    for skill_id, info in report.get("lev_os_agents", {}).get("member_classification", {}).items():
        member_lines.append(
            f"- `{skill_id}`: {info.get('classification')} -> {info.get('ratchet_role')}"
        )

    recommendation_lines = [f"- {line}" for line in report.get("recommended_next_actions", [])]
    issue_lines = [f"- {line}" for line in report.get("issues", [])] or ["- none"]

    return "\n".join(
        [
            "# A2 Skill Source Intake Report",
            "",
            f"- generated_utc: `{report.get('generated_utc', '')}`",
            f"- status: `{report.get('status', '')}`",
            "",
            "## Front Door",
            *front_door_lines,
            "",
            "## lev-os/agents Counts",
            f"- total: `{report.get('lev_os_agents', {}).get('skill_doc_counts', {}).get('total')}`",
            f"- curated: `{report.get('lev_os_agents', {}).get('skill_doc_counts', {}).get('curated')}`",
            f"- library: `{report.get('lev_os_agents', {}).get('skill_doc_counts', {}).get('library')}`",
            "",
            "## First Cluster Classification",
            *member_lines,
            "",
            "## Recommended Next Actions",
            *recommendation_lines,
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def build_a2_skill_source_intake_report(repo_root: str | Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    doc_index_paths = _doc_index_paths(root)
    issues: list[str] = []

    front_door: dict[str, dict[str, Any]] = {}
    for label, rel_path in FRONT_DOOR_DOCS.items():
        path = root / rel_path
        exists = path.exists()
        indexed_in_a2 = rel_path in doc_index_paths if rel_path in CANONICAL_A2_INDEX_TARGETS else None
        front_door[label] = {
            "path": rel_path,
            "exists": exists,
            "indexed_in_a2": indexed_in_a2,
        }
        if not exists:
            issues.append(f"missing front-door corpus doc: {rel_path}")
        elif indexed_in_a2 is False:
            issues.append(f"front-door corpus doc not indexed in canonical A2: {rel_path}")

    lev_root = root / "work/reference_repos/lev-os/agents"
    curated_root = lev_root / "skills"
    library_root = lev_root / "skills-db"
    lev_counts = {
        "total": _count_skill_docs(lev_root),
        "curated": _count_skill_docs(curated_root),
        "library": _count_skill_docs(library_root),
    }
    for key, expected in EXPECTED_LEV_COUNTS.items():
        if lev_counts[key] != expected:
            issues.append(
                f"lev-os/agents {key} SKILL.md count mismatch: expected {expected}, found {lev_counts[key]}"
            )

    cluster_members: dict[str, dict[str, Any]] = {}
    for skill_id, rel_path in LEV_CLUSTER_MEMBER_PATHS.items():
        exists = (root / rel_path).exists()
        cluster_members[skill_id] = {
            "path": rel_path,
            "exists": exists,
        }
        if not exists:
            issues.append(f"missing imported cluster member surface: {rel_path}")

    corpus_text = _load_text(root / "SKILL_SOURCE_CORPUS.md")
    tracker_text = _load_text(root / "REPO_SKILL_INTEGRATION_TRACKER.md")
    backlog_text = _load_text(root / "SKILL_CANDIDATES_BACKLOG.md")
    imported_cluster_map_path = root / "system_v4" / "V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md"
    cluster_spec_path = root / "system_v4" / "skill_specs" / "SKILL_CLUSTER_SCHEMA__v1.md"

    corpus_text_lower = corpus_text.lower()
    tracker_text_lower = tracker_text.lower()
    backlog_text_lower = backlog_text.lower()
    text_alignment = {
        "corpus_mentions_cluster": "skill-source intake cluster" in corpus_text_lower,
        "tracker_mentions_first_cluster": "a2-skill-source-intake-operator" in tracker_text
        or "skill-source intake cluster" in tracker_text_lower,
        "backlog_mentions_first_slice": "a2-skill-source-intake-operator" in backlog_text_lower,
        "imported_cluster_map_exists": imported_cluster_map_path.exists(),
        "cluster_schema_exists": cluster_spec_path.exists(),
    }
    if not text_alignment["corpus_mentions_cluster"]:
        issues.append("umbrella corpus doc does not mention the skill-source intake cluster")
    if not text_alignment["tracker_mentions_first_cluster"]:
        issues.append("integration tracker does not mention the first imported intake cluster")
    if not text_alignment["backlog_mentions_first_slice"]:
        issues.append("backlog does not mention a2-skill-source-intake-operator")
    if not text_alignment["imported_cluster_map_exists"]:
        issues.append("missing imported cluster map surface")
    if not text_alignment["cluster_schema_exists"]:
        issues.append("missing shared skill-cluster schema surface")

    report = {
        "schema": "A2_SKILL_SOURCE_INTAKE_REPORT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": "ok" if not issues else "attention_required",
        "front_door": front_door,
        "lev_os_agents": {
            "path": str(lev_root),
            "skill_doc_counts": lev_counts,
            "expected_skill_doc_counts": EXPECTED_LEV_COUNTS,
            "first_cluster_members": cluster_members,
            "member_classification": FIRST_CLUSTER_MEMBER_CLASSIFICATION,
        },
        "cluster_alignment": {
            "cluster_id": "SKILL_CLUSTER::skill-source-intake",
            "first_slice": "a2-skill-source-intake-operator",
            "text_alignment": text_alignment,
        },
        "staged_output_targets": {
            "json_report": A2_INTAKE_REPORT_JSON,
            "md_report": A2_INTAKE_REPORT_MD,
        },
        "recommended_next_actions": FIRST_CLUSTER_RECOMMENDATIONS,
        "issues": issues,
    }
    return report


def run_a2_skill_source_intake(ctx: dict[str, Any]) -> dict[str, Any]:
    repo_root = ctx.get("repo", REPO_ROOT)
    report = build_a2_skill_source_intake_report(repo_root)
    root = Path(repo_root).resolve()
    report_path = ctx.get("report_path") or str(root / A2_INTAKE_REPORT_JSON)
    markdown_path = ctx.get("markdown_path") or str(root / A2_INTAKE_REPORT_MD)
    out_path = Path(report_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path = Path(markdown_path)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_render_markdown_report(report), encoding="utf-8")
    report["report_path"] = str(out_path)
    report["markdown_path"] = str(md_path)
    return report


if __name__ == "__main__":
    report = build_a2_skill_source_intake_report(REPO_ROOT)
    assert report["lev_os_agents"]["skill_doc_counts"]["total"] == EXPECTED_LEV_COUNTS["total"]
    assert report["lev_os_agents"]["skill_doc_counts"]["curated"] == EXPECTED_LEV_COUNTS["curated"]
    assert report["lev_os_agents"]["skill_doc_counts"]["library"] == EXPECTED_LEV_COUNTS["library"]
    assert report["front_door"]["skill_source_corpus"]["exists"]
    assert report["front_door"]["skill_source_corpus"]["indexed_in_a2"]
    assert not report["issues"], f"unexpected intake issues: {report['issues']}"
    print("PASS: a2_skill_source_intake_operator self-test")
