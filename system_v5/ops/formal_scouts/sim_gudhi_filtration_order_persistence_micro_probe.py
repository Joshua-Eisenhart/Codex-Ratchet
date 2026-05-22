#!/usr/bin/env python3
"""Formal scout for GUDHI filtration order persistence."""

from __future__ import annotations

import hashlib
import json
import pathlib

import gudhi


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "sim_gudhi_filtration_order_persistence_micro_probe_results.json"

NAME = "sim_gudhi_filtration_order_persistence_micro_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: observed GUDHI filtration-order persistence on one "
    "finite carrier and one swapped-control negative. This is local tool "
    "evidence, not promoted bridge, axis, engine, topology theorem, or target-system evidence."
)

TOOL_MANIFEST = {
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SimplexTree filtration insertion and persistence interval readout",
    },
    "python": {
        "tried": True,
        "used": True,
        "reason": "supportive finite fixture control flow and pass/fail checks",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive result receipt serialization",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical result path construction",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive stable observable digest",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "gudhi": "load_bearing",
    "python": "supportive",
    "json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
}


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def finite_float(value: float) -> str | float:
    if value == float("inf"):
        return "inf"
    return float(value)


def persistence_observable(edge_times: dict[tuple[int, int], float]) -> dict[str, object]:
    tree = gudhi.SimplexTree()
    for vertex in [0, 1, 2]:
        tree.insert([vertex], filtration=0.0)
    for edge, time in edge_times.items():
        tree.insert(list(edge), filtration=float(time))
    tree.make_filtration_non_decreasing()
    persistence = tree.persistence()
    h0_intervals = [
        [finite_float(float(birth)), finite_float(float(death))]
        for dim, (birth, death) in persistence
        if dim == 0
    ]
    filtration = [
        {"simplex": [int(node) for node in simplex], "filtration": float(value)}
        for simplex, value in tree.get_filtration()
    ]
    finite_deaths = sorted(interval[1] for interval in h0_intervals if interval[1] != "inf")
    return {
        "edge_times": {f"{src}-{dst}": float(time) for (src, dst), time in sorted(edge_times.items())},
        "num_simplices": tree.num_simplices(),
        "filtration": filtration,
        "h0_intervals": h0_intervals,
        "finite_h0_deaths": finite_deaths,
        "earliest_merge": finite_deaths[0] if finite_deaths else None,
        "latest_merge": finite_deaths[-1] if finite_deaths else None,
    }


def main() -> None:
    baseline = persistence_observable({(0, 1): 1.0, (1, 2): 3.0})
    swapped = persistence_observable({(0, 1): 3.0, (1, 2): 1.0})
    changed_observable = baseline["filtration"] != swapped["filtration"] and baseline["finite_h0_deaths"] == swapped["finite_h0_deaths"]
    checks = {
        "classification_is_formal_scout": CLASSIFICATION == "formal_scout",
        "execution_kind_is_nonclassical": SIM_EXECUTION_KIND == "nonclassical",
        "promotion_disabled": PROMOTION_ALLOWED is False,
        "finite_carrier_ran": baseline["num_simplices"] == 5,
        "persistence_readout_ran": len(baseline["h0_intervals"]) == 3,
        "swapped_control_changed_observable": changed_observable,
    }
    positive = {
        "gudhi_persistence_readout_runs": {
            "pass": checks["persistence_readout_ran"],
            "h0_interval_count": len(baseline["h0_intervals"]),
        },
        "filtration_order_swap_changes_local_observable": {
            "pass": checks["swapped_control_changed_observable"],
            "observable": "filtration_order",
        },
    }
    graveyard_companions = {
        "persistence_multiset_not_used_as_order_claim": {
            "pass": baseline["finite_h0_deaths"] == swapped["finite_h0_deaths"],
            "reason": "the local order-sensitive readout changes while the persistence death multiset stays fixed",
        },
        "promotion_remains_disabled": {
            "pass": PROMOTION_ALLOWED is False,
            "reason": "tool-function evidence stays scout-only",
        },
    }
    boundary = {
        "finite_fixture_only": {
            "pass": checks["finite_carrier_ran"],
            "claim": "bounded to one three-vertex filtered path carrier",
        },
        "not_topology_theorem": {
            "pass": True,
            "claim": "does not promote a topology theorem, bridge, axis, engine, or target-system result",
        },
    }
    nearby_variants = {
        "total": len(graveyard_companions),
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
    }
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "fixture": "finite three-vertex filtered path carrier",
        "baseline": baseline,
        "swapped_control_negative": swapped,
        "changed_observable_required": True,
        "changed_observable": changed_observable,
        "observable_note": "The tool persistence multiset is intentionally stable while the filtration-order observable changes.",
        "observable_digest": stable_hash({"baseline": baseline, "swapped": swapped}),
        "checks": checks,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "v5 formal scout receipt only",
            "GUDHI finite filtration-order micro-probe, not a canonical sim or promoted lego",
            "nonclassical execution kind with promotion explicitly blocked",
        ],
        "pass": all(checks.values()),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUT_PATH), "pass": result["pass"], "changed": changed_observable}, sort_keys=True))


if __name__ == "__main__":
    main()
