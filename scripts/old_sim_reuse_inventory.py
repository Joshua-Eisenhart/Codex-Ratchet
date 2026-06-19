#!/usr/bin/env python3
"""Build a reuse-oriented index of old Codex Ratchet sim surfaces.

This is an inventory tool, not a promotion gate. It treats old sims as mines for
math objects, controls, negatives, tool recipes, and rebuild candidates while
keeping current tri-engine / formal-scout ceilings explicit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
}

SOURCE_SUFFIXES = {".py", ".jl", ".sh", ".bash", ".ipynb"}
DOC_SUFFIXES = {".md", ".txt", ".rst"}
RESULT_SUFFIXES = {".json", ".jsonl"}

FAMILY_PATTERNS: list[tuple[str, str]] = [
    ("root_distinguishability", r"distinguish|identity|root|r0"),
    ("finitude", r"f01|finit|finite"),
    ("noncommutation_order", r"n01|noncomm|order|commutative|composition"),
    ("quotient_admissibility", r"quotient|admiss|fence|adm_|r2"),
    ("mc_manifold", r"m\(c\)|mc_profile|manifold|constraint_complex|g_structure"),
    ("carrier_division_algebra", r"carrier|clifford|octonion|quaternion|sedenion|jordan|g2|spin7|division|fano"),
    ("associator_nonassoc", r"associat|nonassoc|bracket"),
    ("hopf_torus_holonomy", r"hopf|torus|berry|holonomy|fiber|fibration|loop"),
    ("weyl_spinor_chirality", r"weyl|spinor|chiral|chirality|left_right"),
    ("qit_density_entanglement", r"qit|density|rho|entangl|bell|bures|fubini|qfi|qgt|bloch|hilbert"),
    ("engine_axis_terrain_operator", r"engine|axis|terrain|operator|igt|win|lose|strategy"),
    ("entropy_classical_engine", r"entropy|carnot|szilard|heat|thermal|godel|horizon|metric"),
    ("graph_topology", r"graph|topolog|toponetx|gudhi|pyg|geometric|cell|complex|persistence|hypergraph"),
    ("proof_symbolic", r"z3|cvc5|sympy|symbolic|smt|proof|sat|unsat|validator"),
    ("tool_integration", r"tool|integration|manifest|capability|import|package"),
    ("external_archive", r"grok|oph|penrose|external|archive|legacy|read only|variant"),
    ("bridge_physics", r"bridge|axis0|gravity|cosmo|physics|dark|xi|phi|rosetta"),
]

STATUS_KEYS = (
    "classification",
    "all_pass",
    "promotion_allowed",
    "formal_admission_allowed",
    "schema_version",
    "schema",
    "object_id",
    "probe_id",
    "receipt_id",
    "source_path",
    "source_sha256",
)


def relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def small_sha256(path: Path, max_bytes: int = 1_000_000) -> str:
    """Hash the whole file for small files; prefix-hash huge files for identity hints."""
    h = hashlib.sha256()
    size = path.stat().st_size
    with path.open("rb") as handle:
        if size <= max_bytes:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(chunk)
        else:
            h.update(handle.read(max_bytes))
            h.update(str(size).encode())
    return h.hexdigest()[:16]


def iter_files(root: Path):
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        current_path = Path(current)
        for file_name in files:
            yield current_path / file_name


def surface_kind(path: Path, relative: str) -> str | None:
    lower = relative.lower()
    suffix = path.suffix.lower()
    name = path.name.lower()
    if suffix in RESULT_SUFFIXES and (
        "result" in lower
        or "receipt" in lower
        or "evidence" in lower
        or "manifest" in lower
        or "index" in lower
        or "audit" in lower
    ):
        return "result_or_index_json"
    if suffix in SOURCE_SUFFIXES and any(
        token in lower
        for token in (
            "sim",
            "probe",
            "scout",
            "validator",
            "audit",
            "bridge",
            "envelope",
            "carrier",
            "engine",
            "tool_integration",
        )
    ):
        return "sim_source"
    if suffix in DOC_SUFFIXES and any(
        token in lower
        for token in (
            "sim",
            "probe",
            "scout",
            "lego",
            "manifold",
            "engine",
            "axis",
            "entropy",
            "qit",
            "carrier",
            "constraint",
            "archive",
            "legacy",
            "index",
            "grok",
        )
    ):
        return "doc_or_reference"
    if name in {"readme.md", "00_manifest.md", "current_docs_map.md", "tier_status.md"} and "system_v5/docs" in lower:
        return "doc_or_reference"
    return None


def estate_bucket(relative: str, kind: str) -> str:
    lower = relative.lower()
    if lower.startswith("system_v5/ops/formal_scouts/results/"):
        return "current_formal_scout_results"
    if lower.startswith("system_v5/ops/formal_scouts/"):
        return "current_formal_scout_sources"
    if lower.startswith("system_v5/julia_carrier/results/"):
        return "current_julia_carrier_results"
    if lower.startswith("system_v5/julia_carrier/"):
        return "current_julia_carrier_sources"
    if lower.startswith("system_v5/evidence/"):
        return "current_machine_indexes"
    if lower.startswith("system_v5/docs/archive") or "/archive_old/" in lower:
        return "v5_doc_archive"
    if lower.startswith("system_v5/docs/"):
        return "v5_docs_and_ledgers"
    if lower.startswith("system_v5/grok_sim/"):
        return "grok_sim_archive"
    if lower.startswith("system_v5/legos/"):
        return "lego_estate"
    if lower.startswith("system_v4/probes/a2_state/sim_results/"):
        return "v4_a2_state_results"
    if lower.startswith("system_v4/probes/"):
        return "v4_probe_sources"
    if lower.startswith("system_v4/docs/"):
        return "v4_docs"
    if lower.startswith("read only legacy") or lower.startswith("system_v5/read only"):
        return "read_only_legacy_reference"
    if lower.startswith("work/"):
        return "workbench_or_tmp"
    if lower.startswith("receipts/"):
        return "repo_receipts"
    if lower.startswith("scripts/"):
        return "repo_inventory_or_validator_scripts"
    return f"other_{kind}"


def family_tags(text: str) -> list[str]:
    lower = text.lower()
    tags = [name for name, pattern in FAMILY_PATTERNS if re.search(pattern, lower)]
    return tags or ["unclassified"]


def read_json_summary(path: Path) -> tuple[dict[str, Any], str | None]:
    if path.suffix.lower() != ".json":
        return {}, None
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            data = json.load(handle)
    except Exception as exc:  # JSONL, partial writes, huge malformed, etc.
        return {}, f"json_parse_error:{exc.__class__.__name__}"
    if not isinstance(data, dict):
        return {"json_type": type(data).__name__}, None
    summary: dict[str, Any] = {key: data.get(key) for key in STATUS_KEYS if key in data}
    if "all_pass" not in summary:
        nested = data.get("summary")
        if isinstance(nested, dict) and "all_pass" in nested:
            summary["all_pass"] = nested.get("all_pass")
            summary["all_pass_source"] = "summary.all_pass"
    if "object_id" not in summary:
        for key in ("object", "name", "id", "probe", "receipt"):
            value = data.get(key)
            if isinstance(value, str):
                summary["object_id"] = value
                break
    engine_contract = data.get("engine_contract")
    if isinstance(engine_contract, dict):
        summary["engine_contract_present"] = True
        summary["engine_statuses"] = {
            str(k): v.get("status") if isinstance(v, dict) else None
            for k, v in engine_contract.items()
        }
        packages: list[str] = []
        for v in engine_contract.values():
            if isinstance(v, dict):
                for field in ("load_bearing_packages", "supportive_packages"):
                    value = v.get(field)
                    if isinstance(value, list):
                        packages.extend(str(x) for x in value)
        if packages:
            summary["engine_packages"] = sorted(set(packages))[:40]
    tool_claims = data.get("load_bearing_tool_claims")
    if isinstance(tool_claims, list):
        summary["load_bearing_tool_claim_count"] = len(tool_claims)
        claim_tools = []
        for item in tool_claims:
            if isinstance(item, dict) and item.get("tool"):
                claim_tools.append(str(item["tool"]))
        if claim_tools:
            summary["load_bearing_claim_tools"] = sorted(set(claim_tools))[:40]
    for key in ("TOOL_MANIFEST", "tool_manifest", "actual_tools_used", "tools_used", "load_bearing_tools"):
        value = data.get(key)
        if isinstance(value, dict):
            summary[f"{key}_keys"] = sorted(map(str, value.keys()))[:40]
        elif isinstance(value, list):
            summary[key] = sorted({str(v) for v in value})[:40]
    return summary, None


def reuse_mode(kind: str, bucket: str, summary: dict[str, Any], families: list[str]) -> str:
    classification = str(summary.get("classification") or "").lower()
    all_pass = summary.get("all_pass")
    promotion_allowed = summary.get("promotion_allowed")
    formal_allowed = summary.get("formal_admission_allowed")
    has_engine_contract = bool(summary.get("engine_contract_present"))
    if has_engine_contract or "three_engine" in str(summary.get("schema_version") or "").lower():
        if all_pass is True and promotion_allowed is False and formal_allowed is False:
            return "active_three_engine_scratch_template_or_receipt"
        return "tri_engine_contract_audit_needed"
    if bucket in {"v4_probe_sources", "v4_a2_state_results", "v4_docs"}:
        if all_pass is False:
            return "legacy_negative_or_failed_control_mine"
        return "legacy_translate_to_micro_lego_or_baseline_control"
    if bucket in {"read_only_legacy_reference", "v5_doc_archive", "grok_sim_archive"}:
        return "archive_mine_for_math_objects_controls_falsifiers"
    if bucket in {"current_formal_scout_results", "current_formal_scout_sources"}:
        if classification == "formal_scout":
            return "formal_scout_revalidate_or_use_as_bounded_pressure"
        if classification == "scratch_diagnostic":
            return "scratch_diagnostic_keep_under_no_promotion_ceiling"
        return "current_scout_surface_classify_before_reuse"
    if "tool_integration" in families:
        return "tool_recipe_or_capability_anchor"
    if kind == "doc_or_reference":
        return "doc_index_or_authority_surface"
    return "classify_before_reuse"


def compact_row(path: Path, root: Path) -> dict[str, Any]:
    relative = relpath(path, root)
    kind = surface_kind(path, relative)
    if kind is None:
        raise ValueError("not an indexed surface")
    stat = path.stat()
    bucket = estate_bucket(relative, kind)
    summary, error = read_json_summary(path) if kind == "result_or_index_json" else ({}, None)
    tags = family_tags(relative + " " + json.dumps(summary, sort_keys=True)[:500])
    return {
        "path": relative,
        "basename": path.name,
        "stem": path.stem,
        "suffix": path.suffix.lower(),
        "kind": kind,
        "bucket": bucket,
        "families": tags,
        "reuse_mode": reuse_mode(kind, bucket, summary, tags),
        "size_bytes": stat.st_size,
        "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "sha256_hint": small_sha256(path),
        "json_summary": summary,
        "parse_error": error,
    }


def bucket_role(bucket: str) -> str:
    roles = {
        "current_formal_scout_results": "bounded current scout receipts; useful only with claim ceilings and validators",
        "current_formal_scout_sources": "current scout/envelope source; rebuild templates and lint/audit targets",
        "current_julia_carrier_results": "Julia reference-lane receipts for current/recent tri-engine packets",
        "current_julia_carrier_sources": "Julia reference-lane source; package-native rebuild templates",
        "current_machine_indexes": "existing generated indexes; routing aids, not direct sim evidence",
        "v5_docs_and_ledgers": "current docs/ledgers; authority varies by status tag",
        "v5_doc_archive": "superseded docs; mine for provenance and objects only",
        "grok_sim_archive": "proposal/failure mining surface",
        "lego_estate": "lego result/support estate; pair with validators before promotion",
        "v4_a2_state_results": "legacy dated results; baseline/control/falsifier mine",
        "v4_probe_sources": "legacy runnable probes; translate into bounded micro-legos before use",
        "v4_docs": "legacy/session docs; provenance and old queue mine",
        "read_only_legacy_reference": "read-only source/reference; not current route truth",
        "workbench_or_tmp": "temporary/workbench surface; inspect before trusting",
        "repo_receipts": "receipt surface; pair to source and result before trusting",
        "repo_inventory_or_validator_scripts": "controller/inventory tooling",
    }
    return roles.get(bucket, "miscellaneous indexed surface")


def make_index(repo: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in iter_files(repo):
        try:
            relative = relpath(path, repo)
            if surface_kind(path, relative) is None:
                continue
            rows.append(compact_row(path, repo))
        except Exception as exc:
            rows.append(
                {
                    "path": relpath(path, repo),
                    "kind": "inventory_error",
                    "error": f"{exc.__class__.__name__}: {exc}",
                }
            )
    rows.sort(key=lambda row: row.get("path", ""))

    bucket_counts = Counter(row.get("bucket", "unknown") for row in rows)
    kind_counts = Counter(row.get("kind", "unknown") for row in rows)
    reuse_counts = Counter(row.get("reuse_mode", "unknown") for row in rows)
    family_counts: Counter[str] = Counter()
    for row in rows:
        family_counts.update(row.get("families", []))

    duplicates = {
        basename: paths
        for basename, paths in sorted(
            ((base, sorted(group)) for base, group in _basename_groups(rows).items() if len(group) > 1),
            key=lambda item: (-len(item[1]), item[0]),
        )
    }

    bucket_examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in sorted(rows, key=lambda row: (row.get("bucket", ""), -int(row.get("size_bytes", 0) or 0))):
        bucket = row.get("bucket", "unknown")
        if len(bucket_examples[bucket]) < 8:
            bucket_examples[bucket].append(
                {
                    "path": row.get("path"),
                    "kind": row.get("kind"),
                    "reuse_mode": row.get("reuse_mode"),
                    "families": row.get("families"),
                    "classification": row.get("json_summary", {}).get("classification"),
                    "all_pass": row.get("json_summary", {}).get("all_pass"),
                    "size_bytes": row.get("size_bytes"),
                }
            )

    duplicate_basenames_top = [
        {"basename": base, "count": len(paths), "paths": paths[:20]}
        for base, paths in list(duplicates.items())[:100]
    ]
    reuse_queue = build_reuse_queue(rows)
    reuse_queue["duplicate_lineage_hotspots"] = duplicate_basenames_top[:60]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": str(repo),
        "purpose": "Reuse-oriented index of old/current sim surfaces. This does not promote claims.",
        "rules": [
            "Old docs and old logs are mines, not current route authority.",
            "Passing legacy results are baseline/control/falsifier material until rebuilt or revalidated under current contracts.",
            "Current three_engine_sim_result_v1 envelopes require Julia/JAX/PyTorch and --require-pytorch validation.",
            "Scratch diagnostics and formal scouts keep promotion_allowed/formal_admission ceilings unless a separate gate changes them.",
        ],
        "summary": {
            "row_count": len(rows),
            "kind_counts": dict(kind_counts.most_common()),
            "bucket_counts": dict(bucket_counts.most_common()),
            "reuse_mode_counts": dict(reuse_counts.most_common()),
            "family_counts": dict(family_counts.most_common()),
            "duplicate_basename_count": len(duplicates),
        },
        "bucket_roles": {bucket: bucket_role(bucket) for bucket in sorted(bucket_counts)},
        "bucket_examples": dict(bucket_examples),
        "duplicate_basenames_top": duplicate_basenames_top,
        "reuse_queue": reuse_queue,
        "rows": rows,
    }


def _basename_groups(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        path = row.get("path")
        base = row.get("basename")
        if isinstance(path, str) and isinstance(base, str):
            groups[base].append(path)
    return groups


def build_reuse_queue(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Pick small, inspectable first queues from the full row set."""
    buckets: dict[str, list[dict[str, Any]]] = {
        "active_tri_engine_receipts_to_verify": [],
        "legacy_geometry_micro_lego_donors": [],
        "legacy_negative_controls_and_falsifiers": [],
        "tool_recipe_sources": [],
        "archive_math_object_mines": [],
        "duplicate_lineage_hotspots": [],
    }

    for row in rows:
        path = str(row.get("path", ""))
        mode = row.get("reuse_mode")
        families = set(row.get("families", []))
        summary = row.get("json_summary", {}) if isinstance(row.get("json_summary"), dict) else {}
        thin = {
            "path": path,
            "bucket": row.get("bucket"),
            "kind": row.get("kind"),
            "families": sorted(families),
            "reuse_mode": mode,
            "classification": summary.get("classification"),
            "all_pass": summary.get("all_pass"),
        }
        if mode == "active_three_engine_scratch_template_or_receipt" and len(buckets["active_tri_engine_receipts_to_verify"]) < 30:
            buckets["active_tri_engine_receipts_to_verify"].append(thin)
        if row.get("bucket") in {"v4_probe_sources", "v4_a2_state_results"} and families.intersection(
            {"hopf_torus_holonomy", "weyl_spinor_chirality", "carrier_division_algebra", "qit_density_entanglement", "graph_topology"}
        ) and len(buckets["legacy_geometry_micro_lego_donors"]) < 60:
            buckets["legacy_geometry_micro_lego_donors"].append(thin)
        if (summary.get("all_pass") is False or "negative" in path.lower() or "falsifier" in path.lower() or "ablation" in path.lower()) and len(buckets["legacy_negative_controls_and_falsifiers"]) < 60:
            buckets["legacy_negative_controls_and_falsifiers"].append(thin)
        if "tool_integration" in families and row.get("kind") == "sim_source" and len(buckets["tool_recipe_sources"]) < 60:
            buckets["tool_recipe_sources"].append(thin)
        if row.get("bucket") in {"read_only_legacy_reference", "v5_doc_archive", "grok_sim_archive"} and len(buckets["archive_math_object_mines"]) < 60:
            buckets["archive_math_object_mines"].append(thin)
    return buckets


def render_markdown(index: dict[str, Any], json_path: str) -> str:
    summary = index["summary"]
    lines: list[str] = []
    lines.append("# Old Sim Reuse Index — 2026-06-08")
    lines.append("")
    lines.append("Status: generated inventory / routing surface. Not a promotion gate.")
    lines.append("")
    lines.append("## Bottom line")
    lines.append("")
    lines.append("Old sims should not drive the current route directly. They are still valuable as:")
    lines.append("- math-object mines;")
    lines.append("- negative controls and falsifiers;")
    lines.append("- baseline/classical comparison fixtures;")
    lines.append("- package/tool recipes;")
    lines.append("- rebuild templates for current tri-engine micro-legos.")
    lines.append("")
    lines.append("Current route truth still comes from current front-door docs, current result validators, and the tri-engine contract. Old docs/logs are mines, not authority.")
    lines.append("")
    lines.append("## Machine index")
    lines.append("")
    lines.append(f"Full JSON index: `{json_path}`")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- indexed rows: `{summary['row_count']}`")
    lines.append(f"- duplicate basenames: `{summary['duplicate_basename_count']}`")
    lines.append("")
    lines.append("### By kind")
    lines.append("")
    for key, value in summary["kind_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    lines.append("### By bucket")
    lines.append("")
    lines.append("| bucket | count | role |")
    lines.append("|---|---:|---|")
    for bucket, count in summary["bucket_counts"].items():
        lines.append(f"| `{bucket}` | {count} | {index['bucket_roles'].get(bucket, '')} |")
    lines.append("")
    lines.append("### By reuse mode")
    lines.append("")
    lines.append("| reuse mode | count |")
    lines.append("|---|---:|")
    for mode, count in summary["reuse_mode_counts"].items():
        lines.append(f"| `{mode}` | {count} |")
    lines.append("")
    lines.append("### Top family tags")
    lines.append("")
    lines.append("| family | count |")
    lines.append("|---|---:|")
    for family, count in list(summary["family_counts"].items())[:24]:
        lines.append(f"| `{family}` | {count} |")
    lines.append("")
    lines.append("## Reuse map")
    lines.append("")
    lines.append("| Old surface type | Safe use now | Unsafe use |")
    lines.append("|---|---|---|")
    lines.append("| `system_v4/probes` source/results | translate into bounded micro-legos, mine controls, rerun in temp/copy if needed | promote old pass labels as current truth |")
    lines.append("| v5 formal-scout receipts | bounded pressure, known failure/negative rows, validator input | call `all_pass` admission |")
    lines.append("| old docs / READ ONLY docs | recover math objects, owner language, candidate controls | use as execution roadmap |")
    lines.append("| Grok/archive/provider outputs | variant/failure mining | doctrine or evidence without translation |")
    lines.append("| tool-integration probes | package recipes and bridge examples | proof that a model claim is admitted |")
    lines.append("| duplicate basenames | lineage audit targets | canonical selection by name alone |")
    lines.append("")
    lines.append("## First queue from the generated index")
    lines.append("")
    queue = index.get("reuse_queue", {})
    for queue_name, items in queue.items():
        lines.append(f"### `{queue_name}`")
        lines.append("")
        if not items:
            lines.append("- none selected in first pass")
            lines.append("")
            continue
        for item in items[:12]:
            if "path" in item:
                families = ", ".join(item.get("families", [])[:4])
                lines.append(f"- `{item['path']}` — `{item['reuse_mode']}`; families: {families}")
            else:
                paths = item.get("paths", [])
                first_paths = "; ".join(f"`{path}`" for path in paths[:3])
                lines.append(f"- `{item.get('basename')}` — `{item.get('count')}` copies; examples: {first_paths}")
        if len(items) > 12:
            lines.append(f"- ... {len(items) - 12} more in JSON")
        lines.append("")
    lines.append("## Next organization move")
    lines.append("")
    lines.append("Do not mass-clean or mass-promote. Split the old sim estate into small reuse packets:")
    lines.append("")
    lines.append("1. `carrier_geometry_micro_lego_donors`: Hopf/torus/Weyl/spinor/Clifford rows from v4 + v5 scouts.")
    lines.append("2. `negative_control_bank`: ablations, falsifiers, failed validators, blocked rows.")
    lines.append("3. `tool_recipe_bank`: z3/cvc5/sympy/toponetx/gudhi/PyG/quimb/clifford bridge patterns.")
    lines.append("4. `classical_baseline_bank`: Carnot/Szilard/entropy/engine rows as side-lane controls.")
    lines.append("5. `graveyard_and_variant_bank`: Grok/provider/external-theory rows as donor/falsifier candidates only.")
    lines.append("")
    lines.append("Each packet should keep: source path, result path, old claim, safe current reuse, required current validator, and claim ceiling.")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path("system_v5/evidence/old_sim_reuse_index_20260608.json"),
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=Path("system_v5/docs/maintenance/old_sim_reuse_index_20260608.md"),
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    index = make_index(repo)
    json_out = args.json_out if args.json_out.is_absolute() else repo / args.json_out
    md_out = args.md_out if args.md_out.is_absolute() else repo / args.md_out
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")
    md_out.write_text(render_markdown(index, json_out.relative_to(repo).as_posix()), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "repo": str(repo),
                "json_out": json_out.relative_to(repo).as_posix(),
                "md_out": md_out.relative_to(repo).as_posix(),
                "row_count": index["summary"]["row_count"],
                "bucket_counts": index["summary"]["bucket_counts"],
                "reuse_mode_counts": index["summary"]["reuse_mode_counts"],
                "duplicate_basename_count": index["summary"]["duplicate_basename_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
