#!/usr/bin/env python3
"""Audit formal scouts for source-native Weyl/terrain/loop semantics.

This is an incident-audit helper, not a scientific probe. It checks whether the
current formal-scout estate actually carries the source-defined left/right Weyl
density spaces, terrain laws, and Hopf loop placements, instead of only generic
gamma5/channel vocabulary.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
from collections import Counter
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULTS = ROOT / "results"
AUDITS = ROOT / "audits"


CATEGORIES: dict[str, list[str]] = {
    "left_right_weyl_density": [
        r"\bpsi_L\b",
        r"\bpsi_R\b",
        r"\brho_L\b",
        r"\brho_R\b",
        r"left[_ -]weyl",
        r"right[_ -]weyl",
        r"left[_ -]chiral[_ -]operating[_ -]space",
        r"right[_ -]chiral[_ -]operating[_ -]space",
    ],
    "hopf_loop_placement": [
        r"\bGamma_f\b",
        r"\bGamma_b\b",
        r"fiber[_ -]loop",
        r"base[_ -]lift",
        r"density[_ -]stationary",
        r"density[_ -]traversing",
        r"inner[_ -]loop",
        r"outer[_ -]loop",
    ],
    "terrain_law_family": [
        r"\bX_F\b",
        r"\bX_V\b",
        r"\bX_P\b",
        r"\bX_H\b",
        r"\bX_C\b",
        r"\bX_S\b",
        r"\bX_So\b",
        r"\bX_Ci\b",
        r"\bterrain\b",
        r"\bterrain_law\b",
    ],
    "left_right_generator_difference": [
        r"\bH_L\b",
        r"\bH_R\b",
        r"sigma_-",
        r"sigma_\+",
        r"lowering",
        r"raising",
        r"ladder",
        r"Hamiltonian sign",
    ],
    "traversal_and_stage_structure": [
        r"inductive",
        r"deductive",
        r"eight[_ -]stage",
        r"8[_ -]stage",
        r"subcycle",
        r"current_stage",
        r"current_operator",
        r"operator[_ -]order",
        r"traversal",
    ],
    "generic_chirality_or_gamma5": [
        r"\bgamma5\b",
        r"\bgamma_5\b",
        r"\bchirality\b",
        r"\bchiral\b",
        r"\bP_L\b",
        r"\bP_R\b",
    ],
    "boundary_or_shell_downstream": [
        r"\bboundary\b",
        r"conditional[_ -]expectation",
        r"\bshell\b",
        r"area[_ -]law",
        r"inverse[_ -]square",
    ],
}


RESULT_REQUIRED_KEYS = [
    "classification",
    "promotion_allowed",
    "claim_ceiling",
    "TOOL_MANIFEST",
    "TOOL_INTEGRATION_DEPTH",
]


def load_text(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def category_hits(text: str) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for category, patterns in CATEGORIES.items():
        matched = []
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                matched.append(pattern)
        hits[category] = matched
    return hits


def result_path_for(script: pathlib.Path) -> pathlib.Path:
    stem = script.stem.removeprefix("sim_")
    return RESULTS / f"{stem}_results.json"


def classify(hits: dict[str, list[str]]) -> str:
    source_core = [
        "left_right_weyl_density",
        "hopf_loop_placement",
        "terrain_law_family",
        "left_right_generator_difference",
    ]
    source_count = sum(bool(hits[key]) for key in source_core)
    has_gamma = bool(hits["generic_chirality_or_gamma5"])
    has_downstream = bool(hits["boundary_or_shell_downstream"])
    if source_count == len(source_core):
        return "source_native_operating_space_candidate"
    if has_gamma and source_count == 0:
        return "detached_gamma5_or_chirality_scout"
    if has_gamma and source_count < 3:
        return "partial_gamma5_without_source_operating_space"
    if has_downstream and source_count == 0:
        return "downstream_geometry_without_source_operating_space"
    if source_count:
        return "partial_source_alignment"
    return "unrelated_or_non_engine_formal_scout"


def inspect_result(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "missing_keys": RESULT_REQUIRED_KEYS}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"exists": True, "json_error": str(exc), "missing_keys": RESULT_REQUIRED_KEYS}
    missing = [key for key in RESULT_REQUIRED_KEYS if key not in data]
    return {
        "exists": True,
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "source_alignment_category": data.get("source_alignment_category"),
        "missing_keys": missing,
        "claim_ceiling": str(data.get("claim_ceiling", ""))[:300],
    }


def main() -> int:
    AUDITS.mkdir(parents=True, exist_ok=True)
    scripts = sorted(ROOT.glob("sim_*.py"))
    rows = []
    for script in scripts:
        source_text = load_text(script)
        result_path = result_path_for(script)
        result_text = load_text(result_path) if result_path.exists() else ""
        combined = source_text + "\n" + result_text
        hits = category_hits(combined)
        result_contract = inspect_result(result_path)
        declared_source_category = result_contract.get("source_alignment_category")
        category = classify(hits)
        if declared_source_category == "source_native_operating_space":
            category = "source_native_operating_space_candidate"
        elif declared_source_category == "downstream_on_source_native_operating_space":
            category = "downstream_on_source_native_operating_space"
        missing_source_core = [
            key
            for key in [
                "left_right_weyl_density",
                "hopf_loop_placement",
                "terrain_law_family",
                "left_right_generator_difference",
            ]
            if not hits[key]
        ]
        rows.append(
            {
                "script": str(script.relative_to(ROOT.parent.parent.parent)),
                "result": str(result_path.relative_to(ROOT.parent.parent.parent)),
                "alignment_class": category,
                "source_core_categories_present": [
                    key
                    for key in [
                        "left_right_weyl_density",
                        "hopf_loop_placement",
                        "terrain_law_family",
                        "left_right_generator_difference",
                    ]
                    if hits[key]
                ],
                "missing_source_core_categories": missing_source_core,
                "has_traversal_and_stage_structure": bool(hits["traversal_and_stage_structure"]),
                "has_generic_chirality_or_gamma5": bool(hits["generic_chirality_or_gamma5"]),
                "has_boundary_or_shell_downstream": bool(hits["boundary_or_shell_downstream"]),
                "matched_patterns": {key: value for key, value in hits.items() if value},
                "declared_source_alignment_category": declared_source_category,
                "result_contract": result_contract,
            }
        )

    counts = Counter(row["alignment_class"] for row in rows)
    gamma_rows = [row for row in rows if row["has_generic_chirality_or_gamma5"]]
    source_native = [row for row in rows if row["alignment_class"] == "source_native_operating_space_candidate"]
    downstream_on_source = [row for row in rows if row["alignment_class"] == "downstream_on_source_native_operating_space"]
    detached_gamma = [
        row
        for row in rows
        if row["alignment_class"]
        in {"detached_gamma5_or_chirality_scout", "partial_gamma5_without_source_operating_space"}
    ]
    downstream_detached = [
        row
        for row in rows
        if row["alignment_class"] == "downstream_geometry_without_source_operating_space"
    ]

    report = {
        "schema": "WEYL_TERRAIN_SOURCE_ALIGNMENT_AUDIT_v1",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "scope": {
            "formal_scout_scripts": len(scripts),
            "formal_scout_results_expected": len(scripts),
            "root": str(ROOT),
        },
        "source_contract_categories": [
            "left_right_weyl_density",
            "hopf_loop_placement",
            "terrain_law_family",
            "left_right_generator_difference",
            "traversal_and_stage_structure",
        ],
        "summary": {
            "alignment_class_counts": dict(sorted(counts.items())),
            "gamma_or_chirality_scouts": len(gamma_rows),
            "source_native_operating_space_candidates": len(source_native),
            "downstream_on_source_native_operating_space": len(downstream_on_source),
            "detached_or_partial_gamma5_scouts": len(detached_gamma),
            "downstream_geometry_without_source_operating_space": len(downstream_detached),
            "result_contract_missing_count": sum(
                bool(row["result_contract"].get("missing_keys")) for row in rows
            ),
        },
        "incident_read": {
            "severity": "high",
            "finding": (
                "Most formal scouts that discuss chirality/gamma5 or downstream shell/boundary geometry "
                "do not instantiate the source-defined left/right Weyl density spaces, terrain law families, "
                "Hamiltonian/ladder differences, and Hopf loop placements. This means gamma5/channel readouts "
                "have been allowed to stand in for the operating-space object."
            ),
            "repair_direction": (
                "Build and lint against the source-native operating-space object first: rho_L/rho_R, "
                "H_L/H_R, sigma_-/sigma_+, terrain laws, Gamma_f/Gamma_b placements, and traversal/stage semantics."
            ),
        },
        "top_detached_gamma5_scouts": detached_gamma[:20],
        "top_downstream_detached_scouts": downstream_detached[:20],
        "source_native_candidates": source_native,
        "downstream_on_source_native_operating_space": downstream_on_source,
        "rows": rows,
    }

    out = AUDITS / "weyl_terrain_source_alignment_audit.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out), "summary": report["summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
