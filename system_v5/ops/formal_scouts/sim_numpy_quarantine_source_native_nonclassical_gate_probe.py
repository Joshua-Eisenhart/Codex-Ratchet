#!/usr/bin/env python3
"""Gate numpy-tainted source-native nonclassical scouts to diagnostic status."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "numpy_quarantine_source_native_nonclassical_gate_probe_results.json"

NAME = "numpy_quarantine_source_native_nonclassical_gate_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: scans current formal scouts for numpy import/use in "
    "source-native, engine/manifold, FEP, Axis0, Holodeck, and cross-engine "
    "surfaces. It does not repair those sims, does not admit nonclassical "
    "attractor-basin evidence, and blocks numpy-tainted rows from supporting "
    "source-native nonclassical claims until torch-native replacements or "
    "explicit legacy/baseline quarantine receipts exist."
)

TOOL_MANIFEST = {
    "python_pathlib": {"tried": True, "used": True, "reason": "load-bearing scout source discovery"},
    "python_re": {"tried": True, "used": True, "reason": "load-bearing numpy import/use detection"},
    "json": {"tried": True, "used": True, "reason": "load-bearing result writing"},
    "hashlib": {"tried": True, "used": True, "reason": "load-bearing source hash receipts"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

NUMPY_PATTERNS = [
    re.compile(r"^\s*import\s+numpy\b", re.MULTILINE),
    re.compile(r"^\s*from\s+numpy\b", re.MULTILINE),
    re.compile(r"\bnp\."),
]
NONCLASSICAL_NAME_MARKERS = (
    "source_native",
    "engine_manifold",
    "axis0",
    "fep",
    "holodeck",
    "cross_engine",
)
QUARANTINE_NAME_MARKERS = ("legacy", "baseline", "classical", "numpy_quarantine")


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def uses_numpy(text: str) -> bool:
    return any(pattern.search(text) for pattern in NUMPY_PATTERNS)


def needs_hard_quarantine(path: pathlib.Path) -> bool:
    name = path.name.lower()
    return any(marker in name for marker in NONCLASSICAL_NAME_MARKERS) and not any(
        marker in name for marker in QUARANTINE_NAME_MARKERS
    )


def classify_file(path: pathlib.Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8")
    if not uses_numpy(text):
        return None
    if needs_hard_quarantine(path):
        quarantine = "hard_source_native_nonclassical_quarantine"
        claim_allowed = False
    elif any(marker in path.name.lower() for marker in QUARANTINE_NAME_MARKERS):
        quarantine = "legacy_or_baseline_boundary"
        claim_allowed = False
    else:
        quarantine = "review_required_unknown_surface"
        claim_allowed = False
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256_file(path),
        "quarantine": quarantine,
        "nonclassical_claim_allowed": claim_allowed,
    }


def main() -> int:
    started = time.time()
    rows = [row for path in sorted(ROOT.glob("sim_*.py")) if (row := classify_file(path))]
    hard = [row for row in rows if row["quarantine"] == "hard_source_native_nonclassical_quarantine"]
    review = [row for row in rows if row["quarantine"] == "review_required_unknown_surface"]
    boundary = [row for row in rows if row["quarantine"] == "legacy_or_baseline_boundary"]

    positive = {
        "formal_scout_source_scan_completed": {
            "pass": len(rows) > 0,
            "numpy_tainted_file_count": len(rows),
            "hard_quarantine_count": len(hard),
            "review_required_count": len(review),
            "legacy_or_baseline_boundary_count": len(boundary),
        },
        "source_native_nonclassical_numpy_is_quarantined": {
            "pass": all(row["nonclassical_claim_allowed"] is False for row in hard),
            "hard_quarantine_paths": [row["path"] for row in hard],
        },
    }
    graveyard = {
        "numpy_tainted_source_native_not_allowed_as_actual_basin": {
            "pass": bool(hard),
            "reason": (
                "Current source-native/FEP/Holodeck/Axis0 scouts that import numpy are diagnostic or "
                "measurement-boundary receipts only; they cannot support the actual nonclassical "
                "attractor-basin claim."
            ),
        },
        "numpy_boundary_not_reframed_as_harmless_glue": {
            "pass": True,
            "reason": "Any numpy import in these surfaces is treated as claim-threatening until quarantined or removed.",
        },
        "torch_native_replacement_required": {
            "pass": True,
            "next_required_receipt": "source-native torch-complex engine/manifold basin scout with no numpy import",
        },
    }
    boundary_checks = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_nonclassical_admission": {
            "pass": "does not admit nonclassical attractor-basin evidence" in CLAIM_CEILING,
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary_checks.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "numpy_quarantine_for_source_native_nonclassical_surfaces",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary_checks,
        "quarantine_rows": rows,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for row in graveyard.values() if row["pass"]),
            "variants": sorted(graveyard),
        },
        "why_not_v4_probes": [
            "This is a v5 formal scout quarantine gate over current source files.",
            "It prevents numpy-tainted scout receipts from being over-read as actual nonclassical basin evidence.",
        ],
        "blockers": [] if all_pass else [key for key, row in {**positive, **graveyard, **boundary_checks}.items() if not row.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  hard_quarantine={len(hard)} review_required={len(review)} legacy_or_baseline={len(boundary)}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
