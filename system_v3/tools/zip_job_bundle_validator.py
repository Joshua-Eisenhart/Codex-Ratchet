#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED_FIELDS = [
    "schema",
    "zip_job_id",
    "zip_job_kind",
    "producer_role",
    "consumer_role",
    "text_profile",
    "source_reference_list",
    "task_execution_order",
    "required_output_file_list",
    "file_sha256_registry",
]

TOPIC_SLUG_TOKEN = "<topic_slug>"
FILL_TOKEN = "<FILL>"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_tokens_in_text(path: Path, token_pattern: re.Pattern[str]) -> int:
    text = path.read_text(encoding="utf-8")
    return len(token_pattern.findall(text))


def _extract_topic_slugs(topic_index_path: Path) -> list[str]:
    if not topic_index_path.exists():
        return []
    text = topic_index_path.read_text(encoding="utf-8")
    # Accept both markdown and yaml-ish layouts:
    # - topic_slug: foo
    # - "topic_slug": "foo"
    pattern = re.compile(r'topic_slug"?\s*:\s*"?(?P<slug>[a-z0-9][a-z0-9_-]{1,120})"?', re.IGNORECASE)
    slugs = {m.group("slug") for m in pattern.finditer(text)}
    return sorted(slugs)


def _expand_topic_slug_paths(paths: list[str], slugs: list[str]) -> list[str]:
    expanded: list[str] = []
    for path in paths:
        if TOPIC_SLUG_TOKEN in path:
            for slug in slugs:
                expanded.append(path.replace(TOPIC_SLUG_TOKEN, slug))
        else:
            expanded.append(path)
    return expanded


def _normalize_source_refs(manifest: dict) -> list[str]:
    raw = manifest.get("source_reference_list")
    if raw is None:
        raw = manifest.get("source_refs", [])
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        if isinstance(item, str):
            out.append(item)
            continue
        if isinstance(item, dict):
            path = item.get("path") or item.get("rel_path")
            if isinstance(path, str):
                out.append(path)
    return out


def _matches_prefix(path: str, prefixes: list[str]) -> bool:
    for prefix in prefixes:
        if path == prefix or path.startswith(prefix) or path.startswith(prefix + "/"):
            return True
    return False


def _validate_manifest_shape(manifest: dict, bundle_root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in manifest:
            errors.append(f"missing_required_field:{field}")

    if manifest.get("schema") != "ZIP_JOB_MANIFEST_v1":
        errors.append("schema_mismatch:expected:ZIP_JOB_MANIFEST_v1")

    task_order = manifest.get("task_execution_order")
    if not isinstance(task_order, list) or not task_order:
        errors.append("task_execution_order_must_be_nonempty_list")
    else:
        for rel in task_order:
            if not isinstance(rel, str):
                errors.append("task_execution_order_contains_non_string")
                continue
            if not (bundle_root / rel).exists():
                errors.append(f"missing_task_file:{rel}")

    required_outputs = manifest.get("required_output_file_list")
    if not isinstance(required_outputs, list) or not required_outputs:
        errors.append("required_output_file_list_must_be_nonempty_list")

    if "expected_outputs" not in manifest:
        warnings.append("missing_expected_outputs")
    elif not isinstance(manifest.get("expected_outputs"), list):
        errors.append("expected_outputs_must_be_list")

    if "task_order" in manifest and manifest.get("task_order") != manifest.get("task_execution_order"):
        warnings.append("legacy_task_order_differs_from_task_execution_order")
    if "source_refs" in manifest and manifest.get("source_refs") != manifest.get("source_reference_list"):
        warnings.append("legacy_source_refs_differs_from_source_reference_list")

    return errors, warnings


def _validate_source_ref_hygiene(
    source_refs: list[str],
    *,
    require_nonempty: bool,
    warn_prefixes: list[str],
    forbid_prefixes: list[str],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if require_nonempty and not source_refs:
        errors.append("source_reference_list_required_nonempty")

    for ref in source_refs:
        if _matches_prefix(ref, forbid_prefixes):
            errors.append(f"forbidden_source_ref:{ref}")
        elif _matches_prefix(ref, warn_prefixes):
            warnings.append(f"warn_source_ref:{ref}")

    return errors, warnings


def _collect_manifest_fill_tokens(manifest: dict) -> list[str]:
    found: list[str] = []
    manifest_text = json.dumps(manifest, sort_keys=True)
    if FILL_TOKEN in manifest_text:
        found.append("manifest_contains_fill_tokens")
    return found


def _audit_template_placeholders(bundle_root: Path) -> dict[str, int]:
    fill_pattern = re.compile(re.escape(FILL_TOKEN))
    token_counts: dict[str, int] = {}
    for path in sorted(bundle_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in {".md", ".json", ".txt", ".task"} and path.name.find(".task.") < 0:
            continue
        try:
            count = _find_tokens_in_text(path, fill_pattern)
        except UnicodeDecodeError:
            continue
        if count > 0:
            token_counts[path.relative_to(bundle_root).as_posix()] = count
    return token_counts


def _validate_run_outputs(bundle_root: Path, manifest: dict, topic_slugs: list[str]) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    required_outputs = manifest.get("required_output_file_list", [])
    if not isinstance(required_outputs, list):
        return ["required_output_file_list_must_be_list"], warnings, []

    uses_topic_slug = any(TOPIC_SLUG_TOKEN in p for p in required_outputs if isinstance(p, str))
    if uses_topic_slug and not topic_slugs:
        errors.append("topic_slug_required_but_no_topic_slugs_resolved")

    expanded = _expand_topic_slug_paths([p for p in required_outputs if isinstance(p, str)], topic_slugs)
    missing = []
    for rel in expanded:
        if not (bundle_root / rel).exists():
            missing.append(rel)
    if missing:
        errors.append(f"missing_required_outputs:{len(missing)}")

    expected_outputs = manifest.get("expected_outputs", [])
    if isinstance(expected_outputs, list):
        for rel in expected_outputs:
            if isinstance(rel, str) and not (bundle_root / rel).exists():
                warnings.append(f"missing_expected_output:{rel}")

    return errors, warnings, missing


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate ZIP_JOB bundle manifests and outputs.")
    parser.add_argument("--bundle-root", required=True, help="Path to ZIP_JOB bundle root directory.")
    parser.add_argument(
        "--manifest-relpath",
        default="meta/ZIP_JOB_MANIFEST_v1.json",
        help="Relative path to manifest from bundle root.",
    )
    parser.add_argument(
        "--mode",
        choices=["template", "run"],
        default="template",
        help="template: schema + placeholders; run: schema + required output presence checks.",
    )
    parser.add_argument(
        "--topic-index-relpath",
        default="output/DOCUMENT_TOPIC_INDEX__A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__source_scope__explicit_topic_map__primary_view__v1.0.md",
        help="Relative path to topic index file used to resolve <topic_slug> in run mode.",
    )
    parser.add_argument(
        "--strict-template",
        action="store_true",
        help="Fail template mode when fill tokens are present in manifest placeholders.",
    )
    parser.add_argument(
        "--require-source-refs",
        action="store_true",
        help="Fail when source_reference_list resolves to an empty set.",
    )
    parser.add_argument(
        "--warn-source-ref-prefix",
        action="append",
        default=[],
        help="Warn when a normalized source ref starts with this prefix. May be repeated.",
    )
    parser.add_argument(
        "--forbid-source-ref-prefix",
        action="append",
        default=[],
        help="Fail when a normalized source ref starts with this prefix. May be repeated.",
    )
    args = parser.parse_args(argv)

    bundle_root = Path(args.bundle_root).expanduser().resolve()
    manifest_path = bundle_root / args.manifest_relpath
    if not manifest_path.exists():
        print(json.dumps({"schema": "ZIP_JOB_BUNDLE_VALIDATION_RESULT_v1", "status": "FAIL", "errors": [f"missing_manifest:{manifest_path}"]}))
        return 2

    manifest = _load_json(manifest_path)
    errors, warnings = _validate_manifest_shape(manifest, bundle_root)
    manifest_fill = _collect_manifest_fill_tokens(manifest)
    source_refs = _normalize_source_refs(manifest)
    ref_errors, ref_warnings = _validate_source_ref_hygiene(
        source_refs,
        require_nonempty=bool(args.require_source_refs),
        warn_prefixes=[str(v).strip().strip("/") for v in args.warn_source_ref_prefix if str(v).strip()],
        forbid_prefixes=[str(v).strip().strip("/") for v in args.forbid_source_ref_prefix if str(v).strip()],
    )
    errors.extend(ref_errors)
    warnings.extend(ref_warnings)

    placeholder_counts: dict[str, int] = {}
    if args.mode == "template":
        placeholder_counts = _audit_template_placeholders(bundle_root)
        if manifest_fill:
            if args.strict_template:
                errors.extend(manifest_fill)
            else:
                warnings.extend(manifest_fill)
    else:
        topic_index_path = bundle_root / args.topic_index_relpath
        topic_slugs = _extract_topic_slugs(topic_index_path)
        run_errors, run_warnings, missing_required_outputs = _validate_run_outputs(bundle_root, manifest, topic_slugs)
        errors.extend(run_errors)
        warnings.extend(run_warnings)
        if manifest_fill:
            errors.extend(manifest_fill)
        result = {
            "schema": "ZIP_JOB_BUNDLE_VALIDATION_RESULT_v1",
            "status": "PASS" if not errors else "FAIL",
            "mode": args.mode,
            "bundle_root": str(bundle_root),
            "manifest_path": str(manifest_path),
            "source_ref_count": len(source_refs),
            "source_refs": source_refs,
            "topic_slug_count": len(topic_slugs),
            "topic_slugs": topic_slugs,
            "missing_required_outputs": missing_required_outputs,
            "errors": errors,
            "warnings": warnings,
        }
        print(json.dumps(result, sort_keys=True))
        return 0 if not errors else 1

    result = {
        "schema": "ZIP_JOB_BUNDLE_VALIDATION_RESULT_v1",
        "status": "PASS" if not errors else "FAIL",
        "mode": args.mode,
        "bundle_root": str(bundle_root),
        "manifest_path": str(manifest_path),
        "source_ref_count": len(source_refs),
        "source_refs": source_refs,
        "placeholder_file_count": len(placeholder_counts),
        "placeholder_counts": placeholder_counts,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
