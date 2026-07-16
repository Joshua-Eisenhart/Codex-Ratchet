#!/usr/bin/env python3
"""Deterministically inventory the bounded Codex Ratchet skill surface.

This audit is intentionally read-only with respect to skill homes.  It records
what is present in the repo, ``~/.codex``, and ``~/.agents`` and keeps
installation/parity gaps red instead of synchronizing them.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "codex-ratchet-skill-surface-audit-v1"
CLASSIFICATION = "audit"
AUDIT_KIND = "v8_skill_surface"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "python_stdlib": {
        "used": True,
        "reason": "Standard-library path, hash, and text inspection builds the read-only skill inventory.",
    },
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}
SCOPE = (
    "codex-ratchet-sim-audit-spine",
    "codex-ratchet-deep-stack-stress",
    "codex-ratchet-env-agent-coordination",
    "codex-ratchet-tool-status-auditor",
    "jax-sim",
    "julia-sim",
    "pytorch-sim",
    "three-engine-sim",
    "sim-stack-maintenance",
    "claude-bridge",
)

EXTERNAL_ROUTE_TARGETS = ("lego-sim-classifier",)
ROUTE_TARGETS = SCOPE + EXTERNAL_ROUTE_TARGETS
NORMALIZABLE_ENGINE_SKILLS = frozenset(
    {"jax-sim", "julia-sim", "pytorch-sim", "three-engine-sim", "sim-stack-maintenance"}
)
NORMALIZATION_RULE_ID = "source-family-preamble-v1"

REPO_PREAMBLE = """This is the repo-held Codex skill source governed by `AGENTS.md`.
Claude-family skills and agents are reference-only, not authority or a sync
source. Current tool membership comes from the runtime target map and
`system_v5/ops/tooling/deep_stack_stress_20260714/registry/tool_roster_v1.json`;
"""

CODEX_PREAMBLE = """This active Codex skill is reconciled from the repo-held source governed by
`AGENTS.md`. Claude-family skills and agents are reference-only, not authority
or a sync source. Current tool membership comes from the repo runtime target
map and
`system_v5/ops/tooling/deep_stack_stress_20260714/registry/tool_roster_v1.json`;
"""

IGNORED_DIRS = frozenset({"__pycache__", ".pytest_cache"})
IGNORED_SUFFIXES = frozenset({".pyc", ".pyo"})
EXECUTABLE_SUFFIXES = frozenset({".py", ".sh", ".jl", ".ts", ".js"})


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def source_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    files = []
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(directory)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if path.suffix in IGNORED_SUFFIXES:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(directory).as_posix())


def subtree_files(files: Iterable[Path], root: Path, subtree: str) -> list[Path]:
    return [path for path in files if path.relative_to(root).parts[0] == subtree]


def tree_manifest(directory: Path) -> list[dict[str, str]]:
    return [
        {"path": path.relative_to(directory).as_posix(), "sha256": sha256_file(path)}
        for path in source_files(directory)
    ]


def tree_sha256(manifest: list[dict[str, str]]) -> str | None:
    if not manifest:
        return None
    canonical = "".join(f"{item['path']}\0{item['sha256']}\n" for item in manifest)
    return sha256_bytes(canonical.encode("utf-8"))


def implementation_details(directory: Path, files: list[Path]) -> dict[str, Any]:
    scripts = subtree_files(files, directory, "scripts")
    tests = subtree_files(files, directory, "tests")
    executable_scripts = [path for path in scripts if path.suffix in EXECUTABLE_SUFFIXES]
    validators = [
        path
        for path in executable_scripts
        if path.name.startswith("validate") or "validator" in path.stem
    ]
    runners = [path for path in executable_scripts if path not in validators]
    test_sources = [path for path in tests if path.suffix in EXECUTABLE_SUFFIXES]

    if runners and validators and test_sources:
        level = "tested_candidate"
    elif runners and validators:
        level = "runner_and_validator"
    elif validators:
        level = "validator_backed"
    else:
        level = "guidance_only"

    gaps: list[str] = []
    if runners and not validators:
        gaps.append("runner_without_local_validator")
    if not runners and not validators:
        gaps.append("no_local_runner_or_validator")

    def relative(paths: Iterable[Path]) -> list[str]:
        return [path.relative_to(directory).as_posix() for path in paths]

    return {
        "level": level,
        "runner_files": relative(runners),
        "validator_files": relative(validators),
        "test_files": relative(test_sources),
        "gaps": gaps,
    }


def inspect_location(skill: str, root: Path, surface: str) -> dict[str, Any]:
    directory = root / skill
    if not directory.is_dir():
        return {
            "surface": surface,
            "path": str(directory),
            "state": "missing",
            "skill_sha256": None,
            "source_tree_sha256": None,
            "source_file_count": 0,
            "scripts_count": 0,
            "references_count": 0,
            "agents_count": 0,
            "tests_count": 0,
            "source_files": [],
            "implementation": {
                "level": "guidance_only",
                "runner_files": [],
                "validator_files": [],
                "test_files": [],
                "gaps": ["surface_missing"],
            },
        }

    skill_file = directory / "SKILL.md"
    files = source_files(directory)
    manifest = tree_manifest(directory)
    return {
        "surface": surface,
        "path": str(directory),
        "state": "present" if skill_file.is_file() else "invalid_missing_skill_md",
        "skill_sha256": sha256_file(skill_file) if skill_file.is_file() else None,
        "source_tree_sha256": tree_sha256(manifest),
        "source_file_count": len(files),
        "scripts_count": len(subtree_files(files, directory, "scripts")),
        "references_count": len(subtree_files(files, directory, "references")),
        "agents_count": len(subtree_files(files, directory, "agents")),
        "tests_count": len(subtree_files(files, directory, "tests")),
        "source_files": manifest,
        "implementation": implementation_details(directory, files),
    }


def normalize_operational_body(skill: str, text: str) -> tuple[str, bool, str | None]:
    if skill not in NORMALIZABLE_ENGINE_SKILLS:
        return text, False, None
    repo_count = text.count(REPO_PREAMBLE)
    codex_count = text.count(CODEX_PREAMBLE)
    if repo_count + codex_count != 1:
        return text, False, None
    source = REPO_PREAMBLE if repo_count == 1 else CODEX_PREAMBLE
    return text.replace(source, "[[SOURCE_FAMILY_PREAMBLE]]\n", 1), True, NORMALIZATION_RULE_ID


def compare_skill_bodies(skill: str, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    if left["state"] != "present" or right["state"] != "present":
        return {
            "status": "missing_surface",
            "raw_equal": False,
            "normalized_equal": False,
            "normalization_applied": False,
            "normalization_rule": None,
        }

    left_text = (Path(left["path"]) / "SKILL.md").read_text(encoding="utf-8")
    right_text = (Path(right["path"]) / "SKILL.md").read_text(encoding="utf-8")
    if left_text == right_text:
        return {
            "status": "exact",
            "raw_equal": True,
            "normalized_equal": True,
            "normalization_applied": False,
            "normalization_rule": None,
        }

    left_normalized, left_applied, left_rule = normalize_operational_body(skill, left_text)
    right_normalized, right_applied, right_rule = normalize_operational_body(skill, right_text)
    normalization_applied = left_applied and right_applied and left_rule == right_rule
    normalized_equal = normalization_applied and left_normalized == right_normalized
    return {
        "status": "normalized_source_family_preamble" if normalized_equal else "drift",
        "raw_equal": False,
        "normalized_equal": normalized_equal,
        "normalization_applied": normalization_applied,
        "normalization_rule": left_rule if normalization_applied else None,
    }


def compare_payloads(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    if left["state"] != "present" or right["state"] != "present":
        return {"status": "missing_surface", "exact": False}
    exact = left["source_tree_sha256"] == right["source_tree_sha256"]
    return {"status": "exact" if exact else "drift", "exact": exact}


def route_resolution(target: str, roots: dict[str, Path]) -> dict[str, str]:
    return {
        surface: ("present" if (root / target / "SKILL.md").is_file() else "missing")
        for surface, root in roots.items()
    }


def extract_routes(skill: str, skill_file: Path, roots: dict[str, Path]) -> list[dict[str, Any]]:
    if not skill_file.is_file():
        return []
    lines = skill_file.read_text(encoding="utf-8").splitlines()
    routes: list[dict[str, Any]] = []
    for target in ROUTE_TARGETS:
        if target == skill:
            continue
        pattern = re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(target)}(?![A-Za-z0-9_-])")
        evidence = [
            {"line": number, "text": line.strip()}
            for number, line in enumerate(lines, 1)
            if pattern.search(line)
        ]
        if evidence:
            routes.append(
                {
                    "target": target,
                    "in_scope": target in SCOPE,
                    "evidence": evidence,
                    "resolution": route_resolution(target, roots),
                }
            )
    return routes


def source_state(skill: str, locations: dict[str, dict[str, Any]], parity: dict[str, Any]) -> str:
    repo = locations["repo_held"]
    codex = locations["codex_installed"]
    if repo["state"] != "present" and codex["state"] == "present":
        return "installed_only_no_repo_source"
    if repo["state"] == "present" and skill == "claude-bridge" and parity["status"] == "drift":
        return "repo_candidate_not_installed"
    if repo["state"] == "present" and codex["state"] == "present" and parity["status"] == "drift":
        return "repo_installed_body_drift"
    if repo["state"] == "present":
        return "repo_source_present"
    return "missing_everywhere"


def inspect_skill(skill: str, roots: dict[str, Path]) -> dict[str, Any]:
    locations = {
        surface: inspect_location(skill, root, surface) for surface, root in roots.items()
    }
    body_parity = {
        "repo_vs_codex": compare_skill_bodies(
            skill, locations["repo_held"], locations["codex_installed"]
        ),
        "repo_vs_agents": compare_skill_bodies(
            skill, locations["repo_held"], locations["agents_installed"]
        ),
        "codex_vs_agents": compare_skill_bodies(
            skill, locations["codex_installed"], locations["agents_installed"]
        ),
    }
    payload_parity = {
        "repo_vs_codex": compare_payloads(locations["repo_held"], locations["codex_installed"]),
        "repo_vs_agents": compare_payloads(locations["repo_held"], locations["agents_installed"]),
        "codex_vs_agents": compare_payloads(
            locations["codex_installed"], locations["agents_installed"]
        ),
    }
    state = source_state(skill, locations, body_parity["repo_vs_codex"])
    selected_surface = "repo_held" if locations["repo_held"]["state"] == "present" else "codex_installed"
    selected = locations[selected_surface]
    selected_skill_file = Path(selected["path"]) / "SKILL.md"

    findings: list[str] = []
    if state == "installed_only_no_repo_source":
        findings.append("missing_repo_source")
    if state == "repo_candidate_not_installed":
        findings.append("candidate_not_installed")
    if body_parity["repo_vs_codex"]["status"] == "drift":
        findings.append("repo_codex_operational_body_drift")
    if payload_parity["repo_vs_codex"]["status"] == "drift":
        findings.append("repo_codex_payload_drift")
    if selected["implementation"]["gaps"]:
        findings.extend(selected["implementation"]["gaps"])
    if locations["agents_installed"]["state"] != "present":
        findings.append("agents_surface_absent")

    return {
        "name": skill,
        "source_state": state,
        "selected_audit_surface": selected_surface,
        "selected_implementation_level": selected["implementation"]["level"],
        "locations": locations,
        "operational_body_parity": body_parity,
        "source_payload_parity": payload_parity,
        "nested_skill_routes": extract_routes(skill, selected_skill_file, roots),
        "findings": sorted(set(findings)),
    }


def build_audit(
    repo_root: Path,
    codex_root: Path,
    agents_root: Path,
    observed_at_utc: str | None = None,
) -> dict[str, Any]:
    roots = {
        "repo_held": (repo_root / "system_v5/codex_skills").resolve(),
        "codex_installed": codex_root.resolve(),
        "agents_installed": agents_root.resolve(),
    }
    skills = [inspect_skill(skill, roots) for skill in SCOPE]
    by_name = {entry["name"]: entry for entry in skills}

    missing_repo_source = sorted(
        entry["name"] for entry in skills if entry["source_state"] == "installed_only_no_repo_source"
    )
    candidate_not_installed = sorted(
        entry["name"] for entry in skills if entry["source_state"] == "repo_candidate_not_installed"
    )
    repo_codex_drift = sorted(
        entry["name"]
        for entry in skills
        if entry["operational_body_parity"]["repo_vs_codex"]["status"] == "drift"
    )
    normalized_parity = sorted(
        entry["name"]
        for entry in skills
        if entry["operational_body_parity"]["repo_vs_codex"]["status"]
        == "normalized_source_family_preamble"
    )
    exact_parity = sorted(
        entry["name"]
        for entry in skills
        if entry["operational_body_parity"]["repo_vs_codex"]["status"] == "exact"
    )
    implementation_counts = Counter(entry["selected_implementation_level"] for entry in skills)
    blocking_gaps: list[str] = []
    next_repairs: list[str] = []
    if missing_repo_source:
        blocking_gaps.append(f"missing repo source: {', '.join(missing_repo_source)}")
        next_repairs.append(
            "author reviewed repo-held candidates for every installed-only skill before sync"
        )
    if candidate_not_installed:
        blocking_gaps.append(
            f"candidate not installed: {', '.join(candidate_not_installed)}"
        )
        next_repairs.append(
            "review and explicitly install the tested claude-bridge candidate only after owner approval"
        )
    if repo_codex_drift:
        blocking_gaps.append(
            f"repo/Codex operational-body drift: {', '.join(repo_codex_drift)}"
        )
    if "codex-ratchet-deep-stack-stress" in repo_codex_drift:
        next_repairs.append(
            "reconcile deep-stack-stress wording and active repo-path contract without normalizing it away"
        )
    next_repairs.append(
        "decide whether repo-only validator payloads are intentionally checkout-routed or should be installed"
    )

    observed_at = observed_at_utc or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "schema": SCHEMA,
        "classification": CLASSIFICATION,
        "audit_kind": AUDIT_KIND,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "observed_at_utc": observed_at,
        "roots": {surface: str(root) for surface, root in roots.items()},
        "scope": list(SCOPE),
        "normalization_policy": {
            "rule_id": NORMALIZATION_RULE_ID,
            "allowed_skills": sorted(NORMALIZABLE_ENGINE_SKILLS),
            "boundary": "only the exact repo-held versus active-Codex source-family preamble literals",
            "semantic_or_operational_drift_normalized": False,
        },
        "skills": skills,
        "summary": {
            "scope_count": len(skills),
            "surface_presence": {
                surface: sum(entry["locations"][surface]["state"] == "present" for entry in skills)
                for surface in roots
            },
            "selected_implementation_levels": dict(sorted(implementation_counts.items())),
            "exact_repo_codex_body_parity": exact_parity,
            "normalized_repo_codex_body_parity": normalized_parity,
            "repo_codex_body_drift": repo_codex_drift,
            "missing_repo_source": missing_repo_source,
            "candidate_not_installed": candidate_not_installed,
            "repo_payload_not_mirrored": sorted(
                entry["name"]
                for entry in skills
                if entry["source_payload_parity"]["repo_vs_codex"]["status"] == "drift"
            ),
            "nested_route_count": sum(len(entry["nested_skill_routes"]) for entry in skills),
        },
        "claim_boundaries": {
            "all_skills_updated": False,
            "all_operational_body_parity_green": False,
            "candidate_installed": False,
            "skill_sync_authorized": False,
            "provider_calls_made": False,
            "llm_gate_authority": False,
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "release_allowed": False,
            "official_launch_allowed": False,
            "scientific_claim_allowed": False,
        },
        "verdict": {
            "audit_status": "valid_with_blocking_gaps",
            "operational_surface_ready": False,
            "blocking_gaps": blocking_gaps,
            "next_smallest_repairs": next_repairs,
        },
        "_selected_sources": {
            entry["name"]: str(
                Path(entry["locations"][entry["selected_audit_surface"]]["path"]) / "SKILL.md"
            )
            for entry in skills
        },
        "_index": {
            name: {
                "state": by_name[name]["source_state"],
                "level": by_name[name]["selected_implementation_level"],
            }
            for name in SCOPE
        },
    }


def render_markdown(document: dict[str, Any]) -> str:
    def formatted(items: list[str]) -> str:
        return ", ".join(f"`{item}`" for item in items) if items else "none"

    lines = [
        "# V8 skill surface audit",
        "",
        f"Observed: `{document['observed_at_utc']}`",
        "",
        "Verdict: **valid inventory with blocking gaps**. This report does not install, sync, or update skills. "
        "It does not grant any LLM gate authority or launch/science promotion.",
        "",
        "## Surface matrix",
        "",
        "| Skill | Source state | Selected level | repo files (s/r/a/t) | Codex files (s/r/a/t) | Agents files (s/r/a/t) | repo vs Codex body |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for entry in document["skills"]:
        cells = []
        for surface in ("repo_held", "codex_installed", "agents_installed"):
            location = entry["locations"][surface]
            cells.append(
                f"{location['scripts_count']}/{location['references_count']}/"
                f"{location['agents_count']}/{location['tests_count']}"
                if location["state"] == "present"
                else "missing"
            )
        lines.append(
            "| {name} | {state} | {level} | {repo} | {codex} | {agents} | {parity} |".format(
                name=entry["name"],
                state=entry["source_state"],
                level=entry["selected_implementation_level"],
                repo=cells[0],
                codex=cells[1],
                agents=cells[2],
                parity=entry["operational_body_parity"]["repo_vs_codex"]["status"],
            )
        )

    lines.extend(["", "Counts are `scripts/references/agents/tests`; generated bytecode is excluded.", ""])
    lines.extend(["## Exact source hashes", ""])
    for entry in document["skills"]:
        lines.append(f"### {entry['name']}")
        lines.append("")
        for surface in ("repo_held", "codex_installed", "agents_installed"):
            location = entry["locations"][surface]
            lines.append(
                f"- `{surface}`: `{location['path']}`; state `{location['state']}`; "
                f"SKILL.md `{location['skill_sha256']}`; tree `{location['source_tree_sha256']}`; "
                f"implementation `{location['implementation']['level']}`."
            )
        if entry["findings"]:
            lines.append(f"- Findings: {', '.join(f'`{finding}`' for finding in entry['findings'])}.")
        lines.append("")

    lines.extend(["## Explicit nested routes", ""])
    for entry in document["skills"]:
        routes = entry["nested_skill_routes"]
        if not routes:
            lines.append(f"- `{entry['name']}`: none observed in the selected SKILL.md.")
            continue
        route_text = []
        for route in routes:
            evidence_lines = ",".join(str(item["line"]) for item in route["evidence"])
            route_text.append(f"`{route['target']}` (lines {evidence_lines})")
        lines.append(f"- `{entry['name']}` -> {', '.join(route_text)}.")

    summary = document["summary"]
    lines.extend(
        [
            "",
            "## Preserved gaps",
            "",
            f"- Missing repo source: {formatted(summary['missing_repo_source'])}.",
            f"- Candidate not installed: {formatted(summary['candidate_not_installed'])}.",
            f"- Unnormalized repo/Codex body drift: {formatted(summary['repo_codex_body_drift'])}.",
            f"- Narrow preamble-only normalization: {formatted(summary['normalized_repo_codex_body_parity'])}.",
            "- `codex-ratchet-tool-status-auditor` has an exact installed SKILL.md but its repo validator/reference payload is not mirrored into the active skill home.",
            "- Installed Claude surfaces are runner-only locally; the repo candidate adds the deterministic validator and tests but remains uninstalled.",
            "",
            "## Claim ceiling",
            "",
            "`all_skills_updated=false`, `all_operational_body_parity_green=false`, "
            "`candidate_installed=false`, and `official_launch_allowed=false`.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--codex-root", type=Path, default=Path("/Users/joshuaeisenhart/.codex/skills")
    )
    parser.add_argument(
        "--agents-root", type=Path, default=Path("/Users/joshuaeisenhart/.agents/skills")
    )
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--markdown-out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    document = build_audit(args.repo_root, args.codex_root, args.agents_root)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(render_markdown(document), encoding="utf-8")
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "scope_count": document["summary"]["scope_count"],
                "missing_repo_source": document["summary"]["missing_repo_source"],
                "candidate_not_installed": document["summary"]["candidate_not_installed"],
                "repo_codex_body_drift": document["summary"]["repo_codex_body_drift"],
                "operational_surface_ready": document["verdict"]["operational_surface_ready"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
