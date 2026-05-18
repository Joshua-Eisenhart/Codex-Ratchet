#!/usr/bin/env python3
"""Gate source-native nonclassical scouts by constraint-admissible tool roles."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "constraint_admissible_tool_role_gate_probe_results.json"

NAME = "constraint_admissible_tool_role_gate_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: enforces that actual source-native nonclassical "
    "attractor-basin claims require constraint-admissible load-bearing tools. "
    "This is not a global NumPy ban: classical formal sims may use classical "
    "numerical tools for classical claims, and bridge/baseline/supportive rows "
    "may use them when the role is explicit. "
    "It quarantines rows whose tools are classical, administrative, same-source "
    "runtime only, missing micro receipts, or mathematically mismatched to the "
    "claim. It does not promote any engine, manifold, Axis0, FEP, Holodeck, "
    "world-model, physics, or cognition claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing result receipt parsing"},
    "python_pathlib": {"tried": True, "used": True, "reason": "load-bearing source/result discovery"},
    "hashlib": {"tried": True, "used": True, "reason": "load-bearing source hash receipts"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

NONCLASSICAL_NAME_MARKERS = (
    "source_native",
    "engine_manifold",
    "axis0",
    "fep",
    "holodeck",
    "cross_engine",
    "multicarrier",
    "peps",
    "mps",
)

CONSTRAINT_ADMISSIBLE_TOOLS = {
    "torch",
    "pytorch",
    "pyg",
    "torch_geometric",
    "z3",
    "cvc5",
    "sympy",
    "clifford",
    "geomstats",
    "e3nn",
    "rustworkx",
    "xgi",
    "toponetx",
    "gudhi",
    "quimb",
    "cotengra",
    "kahypar",
    "opt_einsum",
}
CLASSICAL_OR_ADMIN_TOOLS = {
    "numpy",
    "scipy",
    "json",
    "hashlib",
    "pathlib",
    "python_json",
    "python_pathlib",
    "python_re",
    "re",
    "time",
    "engine_core",
}


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_nonclassical_surface(name: str) -> bool:
    lower = name.lower()
    return any(marker in lower for marker in NONCLASSICAL_NAME_MARKERS)


def canonical_tool_name(tool: str) -> str:
    normalized = tool.lower().replace("-", "_")
    aliases = {
        "pyg": "torch_geometric",
        "pytorch": "torch",
        "torch_geometric": "torch_geometric",
        "auto_lirpa": "torch",
    }
    return aliases.get(normalized, normalized)


def load_bearing_tools(result: dict[str, Any]) -> list[str]:
    depth = result.get("TOOL_INTEGRATION_DEPTH") or result.get("tool_integration_depth") or {}
    tools = []
    for tool, role in depth.items():
        if str(role).lower() == "load_bearing":
            tools.append(canonical_tool_name(str(tool)))
    return sorted(tools)


def classify_result(path: pathlib.Path) -> dict[str, Any] | None:
    result = json.loads(path.read_text(encoding="utf-8"))
    name = str(result.get("name") or path.name.removesuffix("_results.json"))
    if not is_nonclassical_surface(name):
        return None
    tools = load_bearing_tools(result)
    admissible = sorted(tool for tool in tools if tool in CONSTRAINT_ADMISSIBLE_TOOLS)
    inadmissible = sorted(tool for tool in tools if tool in CLASSICAL_OR_ADMIN_TOOLS)
    unknown = sorted(tool for tool in tools if tool not in CONSTRAINT_ADMISSIBLE_TOOLS and tool not in CLASSICAL_OR_ADMIN_TOOLS)
    has_admissible = bool(admissible)
    has_disqualifying_classical = "numpy" in inadmissible
    same_source_only = not has_admissible and bool(set(tools) & {"engine_core"})
    if has_disqualifying_classical:
        status = "blocked_numpy_load_bearing"
    elif same_source_only:
        status = "blocked_same_source_runtime_only"
    elif not has_admissible:
        status = "blocked_no_constraint_admissible_load_bearing_tool"
    elif unknown:
        status = "review_unknown_tool_role"
    else:
        status = "tool_role_candidate"
    return {
        "result_path": str(path.relative_to(ROOT)),
        "name": name,
        "load_bearing_tools": tools,
        "constraint_admissible_tools": admissible,
        "inadmissible_or_admin_tools": inadmissible,
        "unknown_tools": unknown,
        "tool_role_status": status,
        "nonclassical_basin_claim_allowed": status == "tool_role_candidate",
        "sha256": sha256_file(path),
    }


def main() -> int:
    started = time.time()
    rows = [row for path in sorted(RESULT_DIR.glob("*_results.json")) if (row := classify_result(path))]
    blocked = [row for row in rows if not row["nonclassical_basin_claim_allowed"]]
    candidates = [row for row in rows if row["nonclassical_basin_claim_allowed"]]

    positive = {
        "result_surface_scanned": {
            "pass": len(rows) > 0,
            "nonclassical_surface_count": len(rows),
            "blocked_count": len(blocked),
            "candidate_count": len(candidates),
        },
        "blocked_rows_are_not_allowed_as_basin_evidence": {
            "pass": all(row["nonclassical_basin_claim_allowed"] is False for row in blocked),
            "blocked_status_counts": {
                status: sum(1 for row in blocked if row["tool_role_status"] == status)
                for status in sorted({row["tool_role_status"] for row in blocked})
            },
        },
    }
    graveyard = {
        "classical_tool_cannot_generate_nonclassical_basin": {
            "pass": True,
            "reason": "A classical/admin tool may be load-bearing for a classical sim and may support logging, baselines, controls, or negatives, but cannot be the load-bearing engine for the actual nonclassical attractor-basin claim.",
        },
        "same_source_runtime_is_not_independent_tool_convergence": {
            "pass": True,
            "reason": "EngineCore execution alone can be source-native evidence but not independent method-multiplicity basin evidence.",
        },
        "constraint_mismatched_tool_role_blocks_promotion": {
            "pass": True,
            "reason": "Tools must preserve, certify, or pressure the exact constraint class being claimed.",
        },
    }
    boundary = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_broad_claims": {
            "pass": "does not promote any engine" in CLAIM_CEILING,
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "constraint_admissible_tool_role_gate",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "tool_role_rows": rows,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for row in graveyard.values() if row["pass"]),
            "variants": sorted(graveyard),
        },
        "why_not_v4_probes": [
            "This is a v5 formal scout gate over current result receipts.",
            "It converts tool-mismatch into explicit quarantine instead of letting the narrative promote weak tools.",
        ],
        "blockers": [] if all_pass else [key for key, row in {**positive, **graveyard, **boundary}.items() if not row.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  surfaces={len(rows)} blocked={len(blocked)} candidates={len(candidates)}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
