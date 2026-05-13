#!/usr/bin/env python3
"""Audit executable sim and result filenames for claim-layer labels."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from direct_sim_semantic_guard import matched_claim_labels


REPO_ROOT = Path(__file__).resolve().parents[1]
PROBES_DIR = REPO_ROOT / "system_v4" / "probes"
RESULTS_DIR = PROBES_DIR / "a2_state" / "sim_results"
OUT_DIR = REPO_ROOT / "system_v5" / "ops" / "semantic_naming"
OUT_PATH = OUT_DIR / "sim_name_claim_label_audit.json"

CLAIM_LAYER_WORDS = {
    "axis",
    "bridge",
    "qit",
    "gstack",
    "engine",
    "type1",
    "type2",
    "rosetta",
    "nonclassical",
    "holodeck",
    "leviathan",
    "iching",
    "igt",
    "fep",
}


def split_tokens(name: str) -> list[str]:
    return [token for token in re.split(r"[^A-Za-z0-9]+", name.lower()) if token]


def claim_label_matches(path: Path) -> list[str]:
    direct_matches = matched_claim_labels(path.stem)
    if direct_matches:
        return sorted(set(direct_matches))
    tokens = split_tokens(path.stem)
    loose_matches = []
    for token in tokens:
        if token in CLAIM_LAYER_WORDS:
            loose_matches.append(token)
        elif re.fullmatch(r"axis\d+", token):
            loose_matches.append("axis")
        elif re.fullmatch(r"type[12]", token):
            loose_matches.append(token)
    if "flux" in tokens and "pauli" in tokens:
        loose_matches.append("flux_pauli_phrase")
    return sorted(set(loose_matches))


def audit_files(root: Path, pattern: str) -> list[dict[str, object]]:
    rows = []
    for path in sorted(root.glob(pattern)):
        if not path.is_file():
            continue
        matches = claim_label_matches(path)
        if not matches:
            continue
        rows.append(
            {
                "path": str(path.relative_to(REPO_ROOT)),
                "stem": path.stem,
                "matched_claim_labels": matches,
                "rename_when_reused": True,
            }
        )
    return rows


def summarize(rows: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for label in row["matched_claim_labels"]:
            counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def main() -> int:
    source_rows = audit_files(PROBES_DIR, "sim_*.py") + audit_files(PROBES_DIR, "*_sim.py")
    result_rows = audit_files(RESULTS_DIR, "*_results.json")
    payload = {
        "schema": "sim_name_claim_label_audit.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "naming_audit_only",
        "claim_ceiling": (
            "filename audit only; does not classify, demote, admit, or rename any sim/result by itself"
        ),
        "policy": {
            "new_direct_sims": "blocked by direct_sim_semantic_guard when claim-layer tokens appear in executable sim basename",
            "legacy_reuse": "rename or quarantine before rerun/reuse rather than inheriting old claim-layer labels",
            "matrix_roles": "matrix role values are metadata only and are not executable sim labels",
        },
        "summary": {
            "source_match_count": len(source_rows),
            "result_match_count": len(result_rows),
            "source_match_counts_by_label": summarize(source_rows),
            "result_match_counts_by_label": summarize(result_rows),
        },
        "source_matches": source_rows,
        "result_matches": result_rows,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    print(f"wrote {OUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
