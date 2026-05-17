#!/usr/bin/env python3
"""Audit sim filenames for literal-math naming discipline."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBES = ROOT / "system_v4" / "probes"
MANIFEST = ROOT / "system_v5" / "evidence" / "qit_gstack_exploratory_wave_manifest_20260513.json"
FORBIDDEN = re.compile(
    r"(axis|engine|qit|bridge|type[12]?|carnot|szilard|landauer|thermo)",
    re.IGNORECASE,
)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def manifest_source_paths() -> set[str]:
    payload = load_json(MANIFEST)
    paths = set()
    for entry in payload.get("entries", []):
        result_path = str(entry.get("path") or "")
        if not result_path.endswith("_results.json"):
            continue
        stem = Path(result_path).name.removesuffix("_results.json")
        paths.add(str(PROBES / f"{stem}.py"))
        paths.add(str(Path("system_v4/probes") / f"{stem}.py"))
    return paths


def main() -> int:
    manifest_paths = manifest_source_paths()
    rows = []
    manifest_hits = []
    legacy_hits = []
    for path in sorted(PROBES.glob("sim_*.py")):
        match = FORBIDDEN.search(path.name)
        if not match:
            continue
        rel = str(path.relative_to(ROOT))
        row = {"path": rel, "term": match.group(0)}
        rows.append(row)
        if rel in manifest_paths or str(path) in manifest_paths:
            manifest_hits.append(row)
        else:
            legacy_hits.append(row)

    payload = {
        "all_pass": len(manifest_hits) == 0,
        "forbidden_source_filename_count": len(rows),
        "manifest_forbidden_filename_count": len(manifest_hits),
        "manifest_forbidden_filenames": manifest_hits,
        "legacy_forbidden_filename_count": len(legacy_hits),
        "legacy_forbidden_sample": legacy_hits[:80],
        "policy": "new and manifest-tracked sims should use literal math names; legacy hits are repair backlog, not current proof failure",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
