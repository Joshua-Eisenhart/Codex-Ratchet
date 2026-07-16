#!/usr/bin/env python3
"""Fail closed when the v0.7 project-memory surface is incomplete or stale."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "preservation" / "preservation_manifest.json"
LEDGER = ROOT / "reports" / "SIM_REGISTRATION_LEDGER.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def current_files() -> dict[str, dict[str, object]]:
    files = {}
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file()):
        relative = path.relative_to(ROOT).as_posix()
        if ".ratchet_deps" in path.parts or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if relative == "preservation/preservation_manifest.json":
            continue
        if relative == "run_all_report.json" or relative.endswith("_results.json"):
            continue  # regenerated harness OUTPUT, not preserved evidence
        files[relative] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return files


def main() -> int:
    errors: list[str] = []
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL unreadable preservation state: {exc}")
        return 1

    for relative in manifest.get("mandatory_memory_surfaces", []):
        if not (ROOT / relative).is_file():
            errors.append(f"missing mandatory memory surface: {relative}")

    for row in manifest.get("restored_artifacts", []):
        path = ROOT / row["path"]
        if not path.is_file():
            errors.append(f"restored artifact absent: {row['path']}")
        elif sha256(path) != row["expected_sha256_from_127"]:
            errors.append(f"restored artifact changed: {row['path']}")

    scripts = sorted(path.name for path in (ROOT / "sims_and_scripts").glob("*.py"))
    run_all = (ROOT / "run_all.py").read_text(encoding="utf-8")
    registered = sorted(set(re.findall(r'^\s*\("([^"]+\.py)"\s*,\s*\d+', run_all, re.M)))
    counts = ledger.get("counts", {})
    expected = (196, 150, 46)  # +2 registered (ratchet_mechanism_and_depth, manifold_L5_binding_discriminator); 46 unregistered unchanged
    actual = (len(scripts), len(registered), len(set(scripts) - set(registered)))
    if actual != expected:
        errors.append(f"simulation visibility partition changed: expected {expected}, got {actual}; regenerate and review")
    if (
        counts.get("all_top_level_python_scripts"),
        counts.get("registered_in_run_all"),
        counts.get("unregistered"),
    ) != actual:
        errors.append("SIM_REGISTRATION_LEDGER.json is stale")

    listed = {
        row["path"]: {"bytes": row["bytes"], "sha256": row["sha256"]}
        for row in manifest.get("content_files", [])
    }
    current = current_files()
    if set(listed) != set(current):
        missing = sorted(set(listed) - set(current))
        added = sorted(set(current) - set(listed))
        if missing:
            errors.append(f"files vanished after manifest: {missing}")
        if added:
            errors.append(f"unmanifested files appeared: {added}")
    for relative in sorted(set(listed) & set(current)):
        if listed[relative] != current[relative]:
            errors.append(f"manifested file changed without preservation regeneration: {relative}")

    if not manifest.get("lineage_comparison", {}).get("all_dropped_paths_restored_in_131"):
        errors.append("manifest does not attest restoration of all four 127->130 omissions")

    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print("PASS preservation verification")
    print("196 scripts surfaced; 150 registered; 46 unregistered; four lineage omissions hash-restored")
    return 0


if __name__ == "__main__":
    sys.exit(main())
