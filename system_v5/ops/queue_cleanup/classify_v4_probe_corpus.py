#!/usr/bin/env python3
"""Classify the v4 probe corpus without moving or deleting files."""

from __future__ import annotations

import json
import pathlib
import subprocess
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parents[3]
PROBES = ROOT / "system_v4" / "probes"
OUT = pathlib.Path(__file__).resolve().parent / "v4_probe_corpus_classification_20260514.json"
ADMISSION_DIR = ROOT / "system_v5" / "ops" / "wizard_admissions"

CONTAMINATION_TOKENS = ["axis", "engine", "rosetta", "iching", "type1", "type2", "gstack"]


def git_status_map() -> dict[str, str]:
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1", "--", str(PROBES.relative_to(ROOT))],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    statuses: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if not line:
            continue
        status = line[:2].strip()
        path = line[3:]
        statuses[path] = status
    return statuses


def admitted_stems() -> set[str]:
    stems = set()
    if not ADMISSION_DIR.exists():
        return stems
    for path in ADMISSION_DIR.glob("*.json"):
        stems.add(path.stem)
    return stems


def classify(path: pathlib.Path, statuses: dict[str, str], admitted: set[str]) -> dict[str, object]:
    rel = path.relative_to(ROOT).as_posix()
    name = path.name
    stem = path.stem
    lower = name.lower()
    tokens = [token for token in CONTAMINATION_TOKENS if token in lower]
    status = statuses.get(rel, "tracked_or_clean")
    is_sim_source = name.startswith("sim_") and path.suffix == ".py"
    is_result_json = path.suffix == ".json"
    is_generated_survivor = name.endswith("_survivor_classes.py")
    is_admitted = stem in admitted or stem.removeprefix("sim_") in admitted

    if status == "??" and is_generated_survivor:
        action = "quarantine_by_manifest_candidate"
    elif tokens and is_admitted:
        action = "wrap_from_v5_when_reused"
    elif tokens:
        action = "review_naming_contamination"
    elif is_admitted:
        action = "keep_reference"
    elif status == "??":
        action = "review_untracked"
    elif is_result_json:
        action = "review_result_linkage"
    else:
        action = "keep_reference_or_review"

    return {
        "path": rel,
        "name": name,
        "stem": stem,
        "git_status": status,
        "is_sim_source": is_sim_source,
        "is_result_json": is_result_json,
        "is_generated_survivor_class": is_generated_survivor,
        "is_admitted_reference": is_admitted,
        "naming_contamination_tokens": tokens,
        "candidate_action": action,
    }


def main() -> int:
    statuses = git_status_map()
    admitted = admitted_stems()
    rows = [classify(path, statuses, admitted) for path in sorted(PROBES.iterdir()) if path.is_file()]
    action_counts = Counter(str(row["candidate_action"]) for row in rows)
    status_counts = Counter(str(row["git_status"]) for row in rows)
    contamination_counts = Counter(token for row in rows for token in row["naming_contamination_tokens"])
    summary = {
        "schema": "V4_PROBE_CORPUS_CLASSIFICATION_v1",
        "generated_by": "system_v5/ops/queue_cleanup/classify_v4_probe_corpus.py",
        "scope": "system_v4/probes direct files only",
        "total_files": len(rows),
        "sim_source_files": sum(1 for row in rows if row["is_sim_source"]),
        "result_json_files": sum(1 for row in rows if row["is_result_json"]),
        "generated_survivor_class_files": sum(1 for row in rows if row["is_generated_survivor_class"]),
        "admitted_reference_matches": sum(1 for row in rows if row["is_admitted_reference"]),
        "status_counts": dict(sorted(status_counts.items())),
        "candidate_action_counts": dict(sorted(action_counts.items())),
        "naming_contamination_counts": dict(sorted(contamination_counts.items())),
        "note": "Read-only classifier. No files moved, renamed, deleted, staged, or promoted.",
    }
    OUT.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
