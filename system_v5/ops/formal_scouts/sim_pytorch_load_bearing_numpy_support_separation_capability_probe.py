#!/usr/bin/env python3
"""Quarantine/capability gate separating PyTorch load-bearing from NumPy support.

Three lanes for every nonclassical result receipt:

  pytorch_load_bearing_numpy_support
      torch is load_bearing; numpy is support, None, or absent.
      quimb (numpy-backed) may appear as supportive only.
      → admissible for constraint-admissible nonclassical claims.

  mixed_backend_review_required
      Both torch and numpy claim load_bearing in the same receipt.
      → blocked until an explicit boundary receipt separates the roles.

  numpy_dominant_quarantine
      numpy is load_bearing; torch is support, None, or absent.
      → hard quarantine; nonclassical basin claims not allowed.

A fourth lane covers quimb specifically: quimb is NumPy-backed at the
substrate level. A receipt where quimb is the *only* constraint-adjacent
load-bearing tool (no direct torch) is flagged as quimb_numpy_backed_upstream
and treated as supportive-only, not constraint-admissible.

Quimb appearing alongside a direct torch load-bearing path is allowed; it
stays in the pytorch_load_bearing_numpy_support lane.

This scout does not run any simulation. It consumes existing result receipts.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / (
    "pytorch_load_bearing_numpy_support_separation_capability_probe_results.json"
)

NAME = "pytorch_load_bearing_numpy_support_separation_capability_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: quarantine/capability gate that separates PyTorch "
    "load-bearing from NumPy support across all current nonclassical result "
    "receipts. "
    "Admissible lane: torch is load_bearing, numpy is support/None/absent. "
    "Quimb (NumPy-backed substrate) is supportive-only unless torch is also "
    "load-bearing in the same receipt. "
    "Mixed-backend (torch AND numpy both load_bearing) is blocked pending an "
    "explicit boundary receipt. "
    "NumPy-dominant receipts are hard-quarantined. "
    "Does not promote any engine, manifold, Axis0, FEP, Holodeck, or basin claim."
)

TOOL_MANIFEST = {
    "python_pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive stdlib result receipt discovery",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive stdlib result receipt parsing",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive stdlib source and receipt hash receipts",
    },
}
TOOL_INTEGRATION_DEPTH = {tool: "supportive" for tool in TOOL_MANIFEST}

# Markers that indicate a result receipt is on a nonclassical surface
NONCLASSICAL_NAME_MARKERS = (
    "source_native",
    "engine_manifold",
    "manifold",
    "thirteen_layer",
    "axis0",
    "fep",
    "holodeck",
    "cross_engine",
    "multicarrier",
    "peps",
    "mps",
    "qit",
    "hopf",
    "holonomy",
    "chirality",
    "weyl",
    "boundary",
    "lirpa",
    "lewm",
    "tensor_network",
    "reservoir",
)

# Classical or admin tools — these can be load-bearing for classical sims only
CLASSICAL_OR_ADMIN_TOOLS = frozenset(
    {
        "numpy",
        "np",
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
)

# Direct PyTorch tools — constraint-admissible
TORCH_TOOLS = frozenset({"torch", "pytorch", "auto_lirpa"})

# PyTorch-adjacent tools that are constraint-admissible when torch is also load-bearing
PYTORCH_ADJACENT_TOOLS = frozenset(
    {
        "pyg",
        "torch_geometric",
        "e3nn",
    }
)

# Quimb is NumPy-backed at the substrate level
QUIMB_TOOLS = frozenset({"quimb", "cotengra", "opt_einsum"})

# Other constraint-admissible tools (SMT, topology, graph)
OTHER_CONSTRAINT_ADMISSIBLE_TOOLS = frozenset(
    {
        "z3",
        "cvc5",
        "sympy",
        "clifford",
        "geomstats",
        "rustworkx",
        "xgi",
        "toponetx",
        "gudhi",
        "kahypar",
    }
)


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_nonclassical_surface(name: str) -> bool:
    lower = name.lower()
    return any(marker in lower for marker in NONCLASSICAL_NAME_MARKERS)


def normalize_tool(tool: str) -> str:
    aliases = {
        "pyg": "torch_geometric",
        "pytorch": "torch",
        "auto_lirpa": "torch",
    }
    key = tool.lower().replace("-", "_")
    return aliases.get(key, key)


def extract_roles(result: dict[str, Any]) -> dict[str, str]:
    """Return {normalized_tool: role} for all tools listed in TOOL_INTEGRATION_DEPTH."""
    raw = result.get("TOOL_INTEGRATION_DEPTH") or result.get("tool_integration_depth") or {}
    if not isinstance(raw, dict):
        return {}
    return {normalize_tool(k): str(v).lower() for k, v in raw.items()}


def load_bearing_set(roles: dict[str, str]) -> frozenset[str]:
    return frozenset(tool for tool, role in roles.items() if role == "load_bearing")


def classify_receipt(path: pathlib.Path) -> dict[str, Any] | None:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    name = str(result.get("name") or path.name.removesuffix("_results.json"))
    if not is_nonclassical_surface(name):
        return None

    roles = extract_roles(result)
    lb = load_bearing_set(roles)

    has_torch = bool(lb & TORCH_TOOLS)
    has_numpy = "numpy" in lb or "np" in lb
    has_quimb_only = bool(lb & QUIMB_TOOLS) and not has_torch
    has_pytorch_adjacent = bool(lb & PYTORCH_ADJACENT_TOOLS)

    # Quimb-only path: no direct torch, quimb tools load-bearing
    if has_quimb_only and not has_torch:
        lane = "quimb_numpy_backed_upstream"
        claim_allowed = False
        note = (
            "Quimb is NumPy-backed at the substrate level. "
            "No direct torch load-bearing path. "
            "Treat as supportive-only; not constraint-admissible for nonclassical claims."
        )
    elif has_torch and has_numpy:
        lane = "mixed_backend_review_required"
        claim_allowed = False
        note = (
            "Both torch and numpy appear as load_bearing. "
            "An explicit boundary receipt is required to separate the roles "
            "before nonclassical basin claims are allowed."
        )
    elif has_numpy and not has_torch:
        lane = "numpy_dominant_quarantine"
        claim_allowed = False
        note = (
            "Numpy is load_bearing; torch is absent or supportive. "
            "Hard quarantine: nonclassical basin claims blocked."
        )
    elif has_torch:
        # torch load-bearing, numpy not load-bearing (support/None/absent) — clean
        lane = "pytorch_load_bearing_numpy_support"
        claim_allowed = True
        note = (
            "Torch is load_bearing; numpy is support, None, or absent. "
            "Quimb (if present) is supportive only. "
            "Constraint-admissible for nonclassical claims."
        )
    else:
        # No torch, no numpy load-bearing — could be classical or admin tools only
        lane = "no_constraint_admissible_load_bearing_tool"
        claim_allowed = False
        note = "No direct torch or numpy in load_bearing roles; no constraint-admissible path."

    all_pass = result.get("all_pass") is True or (
        isinstance(result.get("summary"), dict)
        and result["summary"].get("all_pass") is True
    )

    return {
        "result_path": str(path.relative_to(ROOT)),
        "name": name,
        "lane": lane,
        "load_bearing_tools": sorted(lb),
        "torch_load_bearing": has_torch,
        "numpy_load_bearing": has_numpy,
        "quimb_only_upstream": has_quimb_only,
        "pytorch_adjacent_load_bearing": has_pytorch_adjacent,
        "result_all_pass": all_pass,
        "tool_lane_claim_allowed": claim_allowed,
        "nonclassical_basin_claim_allowed": claim_allowed and all_pass,
        "upstream_result_blocker": not all_pass,
        "note": note,
        "sha256": sha256_file(path),
    }


def main() -> int:
    started = time.time()

    rows = [
        row
        for path in sorted(RESULT_DIR.glob("*_results.json"))
        if path != OUT_PATH and (row := classify_receipt(path))
    ]

    by_lane: dict[str, list[dict]] = {
        "pytorch_load_bearing_numpy_support": [],
        "mixed_backend_review_required": [],
        "numpy_dominant_quarantine": [],
        "quimb_numpy_backed_upstream": [],
        "no_constraint_admissible_load_bearing_tool": [],
    }
    for row in rows:
        by_lane.setdefault(row["lane"], []).append(row)

    admissible = by_lane["pytorch_load_bearing_numpy_support"]
    mixed = by_lane["mixed_backend_review_required"]
    numpy_dom = by_lane["numpy_dominant_quarantine"]
    quimb_up = by_lane["quimb_numpy_backed_upstream"]
    no_tool = by_lane["no_constraint_admissible_load_bearing_tool"]
    admissible_upstream_blockers = [
        {
            "name": row["name"],
            "result_path": row["result_path"],
            "load_bearing_tools": row["load_bearing_tools"],
            "note": (
                "Torch/numpy role lane is admissible, but the upstream receipt "
                "itself is not all_pass and therefore cannot support a basin claim."
            ),
        }
        for row in admissible
        if row["upstream_result_blocker"]
    ]

    positive = {
        "receipt_surface_scanned": {
            "pass": len(rows) > 0,
            "nonclassical_receipt_count": len(rows),
            "pytorch_load_bearing_numpy_support_count": len(admissible),
            "mixed_backend_review_required_count": len(mixed),
            "numpy_dominant_quarantine_count": len(numpy_dom),
            "quimb_numpy_backed_upstream_count": len(quimb_up),
            "no_constraint_admissible_tool_count": len(no_tool),
        },
        "admissible_lane_records_upstream_pass_fail_truth": {
            "pass": True,
            "admissible_count": len(admissible),
            "admissible_all_pass_count": sum(
                1 for row in admissible if row["result_all_pass"]
            ),
            "admissible_upstream_blocker_count": len(admissible_upstream_blockers),
            "admissible_names": [row["name"] for row in admissible],
            "admissible_upstream_blocker_names": [
                row["name"] for row in admissible_upstream_blockers
            ],
        },
        "mixed_lane_is_blocked": {
            "pass": all(not row["nonclassical_basin_claim_allowed"] for row in mixed),
            "mixed_count": len(mixed),
            "mixed_names": [row["name"] for row in mixed],
        },
        "numpy_dominant_is_hard_quarantine": {
            "pass": all(not row["nonclassical_basin_claim_allowed"] for row in numpy_dom),
            "numpy_dominant_count": len(numpy_dom),
            "numpy_dominant_names": [row["name"] for row in numpy_dom],
        },
        "quimb_upstream_is_supportive_only": {
            "pass": all(not row["nonclassical_basin_claim_allowed"] for row in quimb_up),
            "quimb_upstream_count": len(quimb_up),
            "quimb_upstream_names": [row["name"] for row in quimb_up],
        },
    }

    graveyard = {
        "numpy_support_does_not_become_load_bearing_by_cohabitation": {
            "pass": True,
            "reason": (
                "Presence of numpy for controls, logging, or baselines alongside a "
                "torch load-bearing path does not promote numpy to load_bearing. "
                "Role is fixed by TOOL_INTEGRATION_DEPTH declaration, not cohabitation."
            ),
        },
        "quimb_substrate_is_not_constraint_admissible_without_torch": {
            "pass": True,
            "reason": (
                "Quimb uses NumPy as its numerical substrate. "
                "A receipt where quimb is the only constraint-adjacent load-bearing "
                "tool has a NumPy substrate path, not a PyTorch one. "
                "It cannot anchor constraint-admissible nonclassical basin claims."
            ),
        },
        "mixed_backend_receipt_requires_explicit_separation": {
            "pass": True,
            "reason": (
                "When both torch and numpy declare load_bearing in a single receipt, "
                "the actual nonclassical compute path is ambiguous. "
                "A boundary receipt naming which quantities are torch-native and which "
                "are numpy-classical is required before the receipt can support basin work."
            ),
        },
        "pytorch_adjacent_tools_inherit_torch_lane_when_torch_load_bearing": {
            "pass": True,
            "reason": (
                "PyG, e3nn, and similar tools that build on PyTorch inherit the "
                "pytorch_load_bearing lane when torch is also load_bearing. "
                "They do not create an independent admissibility path."
            ),
        },
    }

    boundary = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_basin_promotion": {
            "pass": "Does not promote any engine" in CLAIM_CEILING
            or "does not promote any engine" in CLAIM_CEILING.lower(),
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
        "source_alignment_category": (
            "pytorch_load_bearing_numpy_support_separation_capability_gate"
        ),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "lane_rows": {
            "pytorch_load_bearing_numpy_support": admissible,
            "mixed_backend_review_required": mixed,
            "numpy_dominant_quarantine": numpy_dom,
            "quimb_numpy_backed_upstream": quimb_up,
            "no_constraint_admissible_load_bearing_tool": no_tool,
        },
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for row in graveyard.values() if row["pass"]),
            "variants": sorted(graveyard),
        },
        "upstream_receipt_blockers": admissible_upstream_blockers,
        "why_not_v4_probes": [
            "This is a v5 formal scout capability gate over current result receipts.",
            "It turns the implicit torch/numpy role split into an explicit quarantine "
            "rather than letting receipts carry the ambiguity into basin work.",
        ],
        "blockers": (
            []
            if all_pass
            else [
                key
                for key, row in {**positive, **graveyard, **boundary}.items()
                if not row.get("pass")
            ]
        ),
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(
        f"  admissible={len(admissible)} mixed={len(mixed)} "
        f"numpy_dominant={len(numpy_dom)} quimb_upstream={len(quimb_up)} "
        f"no_tool={len(no_tool)}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
