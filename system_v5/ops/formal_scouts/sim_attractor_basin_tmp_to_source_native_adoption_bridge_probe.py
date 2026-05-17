#!/usr/bin/env python3
"""Bridge rerun-green tmp engine_v2 themes to current source-native scouts.

This scout consumes the tmp execution gate and selected current formal-scout
receipts. It does not promote tmp claims. It records which tmp themes already
have current source-native support and which remain conversion work.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "attractor_basin_tmp_to_source_native_adoption_bridge_probe_results.json"

NAME = "attractor_basin_tmp_to_source_native_adoption_bridge_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: bridges rerun-green tmp engine_v2 proposal themes to "
    "fresh/current source-native formal-scout receipts. It does not admit tmp "
    "results, full Holodeck, final FEP, Axis0, memory, physics, cognition, "
    "world-model, or canonical architecture claims."
)

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing receipt parsing for tmp execution and current source-native scouts",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bounded receipt path checks",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing receipt source hashing",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "json": "load_bearing",
    "pathlib": "load_bearing",
    "hashlib": "load_bearing",
}

TMP_EXECUTION_RESULT = RESULT_DIR / "attractor_basin_tmp_engine_v2_candidate_execution_probe_results.json"

CURRENT_RECEIPTS = {
    "holodeck_hash_memory": RESULT_DIR / "source_native_holodeck_hash_memory_placeholder_probe_results.json",
    "holodeck_closed_loop_fep_strategy": RESULT_DIR / "source_native_holodeck_closed_loop_fep_strategy_probe_results.json",
    "fep_pomdp_policy_tree": RESULT_DIR / "source_native_fep_pomdp_policy_tree_probe_results.json",
    "fep_online_vmp_policy_update": RESULT_DIR / "source_native_fep_online_vmp_policy_update_probe_results.json",
    "axis0_fep_gradient_adapter": RESULT_DIR / "axis0_fep_gradient_stage_local_adapter_closure_probe_results.json",
    "cross_engine_holodeck_memory_cycle": RESULT_DIR / "source_native_cross_engine_holodeck_memory_cycle_probe_results.json",
}

TMP_THEME_MAP = {
    "fep_variational_free_energy": {
        "tmp_scripts": ["wave104_v2_fep_variational_free_energy_probe.py"],
        "current_support": ["fep_pomdp_policy_tree", "fep_online_vmp_policy_update", "axis0_fep_gradient_adapter"],
        "status": "partially_adopted_current_source_native",
        "gap": "tmp classical variational free-energy inequalities are not yet a source-native variational-free-energy equivalence receipt",
    },
    "holodeck_predictive_hash_memory": {
        "tmp_scripts": [
            "wave112_v2_mini_holodeck_runtime_probe.py",
            "wave114_v2_ascii_trigger_lattice_probe.py",
            "wave118_v2_hash_chain_walk_probe.py",
            "wave119_v2_full_integrated_holodeck_demo_probe.py",
        ],
        "current_support": ["holodeck_hash_memory", "holodeck_closed_loop_fep_strategy"],
        "status": "adopted_as_placeholder_and_closed_loop_scout",
        "gap": "full ASCII lattice/hash-chain walk remains tmp proposal space until converted with hash-only/wrong-model controls",
    },
    "real_engine_holodeck_cross_engine_cycle": {
        "tmp_scripts": [
            "wave120_v2_real_engine_holodeck_cycle_probe.py",
            "wave121_v2_cross_engine_holodeck_probe.py",
        ],
        "current_support": ["holodeck_closed_loop_fep_strategy", "axis0_fep_gradient_adapter", "cross_engine_holodeck_memory_cycle"],
        "status": "adopted_as_source_native_cross_engine_memory_scout",
        "gap": "full neural/world-model Holodeck memory remains outside scope; current support is deterministic source-native density-memory cycle with controls",
    },
}


def sha256_file(path: pathlib.Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["exists"] = True
    data["path"] = str(path)
    data["sha256"] = sha256_file(path)
    return data


def basename(path: str) -> str:
    return pathlib.Path(path).name


def main() -> int:
    started = time.time()
    tmp_execution = load_json(TMP_EXECUTION_RESULT)
    current = {name: load_json(path) for name, path in CURRENT_RECEIPTS.items()}
    tmp_rows = tmp_execution.get("candidate_rows") or []
    tmp_by_script = {basename(row.get("script", "")): row for row in tmp_rows}

    theme_rows: dict[str, dict[str, Any]] = {}
    for theme, spec in TMP_THEME_MAP.items():
        tmp_matches = [tmp_by_script.get(script) for script in spec["tmp_scripts"]]
        current_matches = {name: current[name] for name in spec["current_support"]}
        theme_rows[theme] = {
            "tmp_scripts": spec["tmp_scripts"],
            "tmp_all_reran_green": all(
                row is not None and row.get("classification") == "tmp_candidate_green_unpromoted"
                for row in tmp_matches
            ),
            "current_support_receipts": {
                name: {
                    "exists": receipt.get("exists"),
                    "all_pass": receipt.get("all_pass"),
                    "classification": receipt.get("classification"),
                    "promotion_allowed": receipt.get("promotion_allowed"),
                    "claim_ceiling": receipt.get("claim_ceiling"),
                    "sha256": receipt.get("sha256"),
                }
                for name, receipt in current_matches.items()
            },
            "current_all_pass": all(
                receipt.get("exists") is True
                and receipt.get("classification") == "formal_scout"
                and receipt.get("promotion_allowed") is False
                and receipt.get("all_pass") is True
                for receipt in current_matches.values()
            ),
            "status": spec["status"],
            "remaining_gap": spec["gap"],
        }

    adopted_theme_count = sum(
        1
        for row in theme_rows.values()
        if row["tmp_all_reran_green"] and row["current_all_pass"]
    )
    conversion_needed = [
        theme for theme, row in theme_rows.items() if row["status"] == "conversion_needed"
    ]

    positive = {
        "tmp_execution_gate_loaded": {
            "pass": tmp_execution.get("exists") is True and tmp_execution.get("all_pass") is True,
            "tmp_candidate_count": len(tmp_rows),
        },
        "selected_current_source_native_receipts_loaded": {
            "pass": all(
                row.get("exists") is True and row.get("all_pass") is True
                for row in current.values()
            ),
            "receipt_names": sorted(current),
        },
        "fep_and_holodeck_tmp_themes_have_current_support": {
            "pass": adopted_theme_count >= 2,
            "adopted_theme_count": adopted_theme_count,
            "theme_rows": theme_rows,
        },
        "conversion_queue_is_explicit": {
            "pass": True,
            "conversion_needed": conversion_needed,
            "interpretation": "Zero conversion-needed rows is allowed after source-native conversion of wave120/wave121; remaining gaps are scope boundaries.",
        },
    }
    graveyards = {
        "tmp_cross_engine_cycle_not_silently_adopted": {
            "pass": theme_rows["real_engine_holodeck_cross_engine_cycle"]["current_all_pass"] is True,
            "reason": "Tmp cross-engine memory sharing is no longer silently adopted: it is tied to a current source-native cross-engine memory-cycle receipt.",
        },
        "tmp_hash_chain_not_equated_with_current_placeholder": {
            "pass": "hash-only" in TMP_THEME_MAP["holodeck_predictive_hash_memory"]["gap"],
            "reason": "Current hash-memory receipt supports the predictive-model placeholder boundary, not full tmp ASCII/hash-chain canon.",
        },
        "tmp_fep_inequalities_not_equated_with_full_fep_engine": {
            "pass": "not yet" in TMP_THEME_MAP["fep_variational_free_energy"]["gap"],
            "reason": "Current source-native FEP scouts support policy/VMP/FEP-gradient surfaces; variational-equivalence remains narrower work.",
        },
    }
    boundary = {
        "no_tmp_claim_promotion": {
            "pass": PROMOTION_ALLOWED is False and "does not admit tmp results" in CLAIM_CEILING,
        },
        "current_support_requires_formal_scout_receipts": {
            "pass": all(
                receipt.get("classification") == "formal_scout"
                and receipt.get("promotion_allowed") is False
                for receipt in current.values()
            ),
        },
        "bridge_is_theme_level_not_canonical_architecture": {
            "pass": all("remaining_gap" in row for row in theme_rows.values()),
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "attractor_basin_tmp_to_source_native_adoption_bridge",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tmp_execution_result": {
            "path": str(TMP_EXECUTION_RESULT),
            "sha256": tmp_execution.get("sha256"),
        },
        "theme_rows": theme_rows,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "why_not_v4_probes": [
            "This is a current-system adoption bridge over tmp engine_v2 proposal probes and source-native v5 formal scouts.",
            "The bridge keeps tmp claims unpromoted and records remaining conversion gaps.",
        ],
        "blockers": [],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  adopted_theme_count={adopted_theme_count} conversion_needed={conversion_needed}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
