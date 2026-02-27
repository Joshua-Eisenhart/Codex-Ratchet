#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TOPIC_SLUG_TOKEN = "<topic_slug>"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_topic_slugs(topic_index_path: Path) -> list[str]:
    if not topic_index_path.exists():
        return []
    text = topic_index_path.read_text(encoding="utf-8")
    pattern = re.compile(r'topic_slug"?\s*:\s*"?(?P<slug>[a-z0-9][a-z0-9_-]{1,120})"?', re.IGNORECASE)
    slugs = {m.group("slug") for m in pattern.finditer(text)}
    return sorted(slugs)


def _expand_paths(paths: list[str], slugs: list[str]) -> list[str]:
    expanded: list[str] = []
    for item in paths:
        if TOPIC_SLUG_TOKEN in item:
            for slug in slugs:
                expanded.append(item.replace(TOPIC_SLUG_TOKEN, slug))
        else:
            expanded.append(item)
    return expanded


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Realize ZIP_JOB required outputs by expanding <topic_slug> placeholders.")
    parser.add_argument("--bundle-root", required=True)
    parser.add_argument("--manifest-relpath", default="meta/ZIP_JOB_MANIFEST_v1.json")
    parser.add_argument(
        "--topic-index-relpath",
        default="output/DOCUMENT_TOPIC_INDEX__A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__source_scope__explicit_topic_map__primary_view__v1.0.md",
    )
    parser.add_argument(
        "--write-realized-manifest-relpath",
        default="meta/ZIP_JOB_MANIFEST_REALIZED_v1.json",
        help="Relative path to write realized manifest clone with expanded required_output_file_list.",
    )
    args = parser.parse_args(argv)

    bundle_root = Path(args.bundle_root).expanduser().resolve()
    manifest_path = bundle_root / args.manifest_relpath
    topic_index_path = bundle_root / args.topic_index_relpath
    if not manifest_path.exists():
        print(json.dumps({"schema": "ZIP_JOB_REALIZE_REQUIRED_OUTPUTS_RESULT_v1", "status": "FAIL", "error": f"missing_manifest:{manifest_path}"}))
        return 2

    manifest = _load_json(manifest_path)
    required = manifest.get("required_output_file_list", [])
    if not isinstance(required, list):
        print(json.dumps({"schema": "ZIP_JOB_REALIZE_REQUIRED_OUTPUTS_RESULT_v1", "status": "FAIL", "error": "required_output_file_list_must_be_list"}))
        return 2

    slugs = _extract_topic_slugs(topic_index_path)
    needs_slugs = any(isinstance(x, str) and TOPIC_SLUG_TOKEN in x for x in required)
    if needs_slugs and not slugs:
        print(
            json.dumps(
                {
                    "schema": "ZIP_JOB_REALIZE_REQUIRED_OUTPUTS_RESULT_v1",
                    "status": "FAIL",
                    "error": "topic_slug_required_but_no_topic_slugs_resolved",
                    "topic_index_path": str(topic_index_path),
                },
                sort_keys=True,
            )
        )
        return 1

    required_strings = [x for x in required if isinstance(x, str)]
    expanded_required = _expand_paths(required_strings, slugs)

    realized = dict(manifest)
    realized["required_output_file_list"] = expanded_required
    realized["topic_slug_count"] = len(slugs)
    realized["topic_slugs"] = slugs
    out_path = bundle_root / args.write_realized_manifest_relpath
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(realized, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "schema": "ZIP_JOB_REALIZE_REQUIRED_OUTPUTS_RESULT_v1",
                "status": "PASS",
                "manifest_path": str(manifest_path),
                "realized_manifest_path": str(out_path),
                "topic_slug_count": len(slugs),
                "required_output_count_original": len(required_strings),
                "required_output_count_realized": len(expanded_required),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
