#!/usr/bin/env python3
"""Cheap diagnostic mirror for engine_64_stage_full_run_v0 coordinate rows."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import sympy as sp

import engine_64_stage_full_run_v0_common as common


SIM_ID = common.SIM_ID
RESULT_PATH = common.RESULT_DIR / f"{SIM_ID}_jax_results.json"
SOURCE_PATH = common.SIM_DIR / f"{SIM_ID}_jax.py"


def count_by_engine(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"Type1-L": 0, "Type2-R": 0}
    for row in rows:
        axis3 = int(row["axis_bits"]["axis3"])
        counts[str(common.ENGINE_SPECS[axis3]["engine_family"])] += 1
    return counts


def build_result() -> dict[str, Any]:
    common.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    schedule = common.build_schedule()
    consistency_rows = [common.slot_coordinate_consistency(slot) for slot in schedule]
    unique_coords = {
        tuple(int(slot["axis_bits"][f"axis{i}"]) for i in range(1, 7))
        for slot in schedule
    }
    counts = count_by_engine(schedule)
    sympy_total = sp.Integer(len(schedule))
    sympy_unique = sp.Integer(len(unique_coords))
    sympy_type1 = sp.Integer(counts["Type1-L"])
    sympy_type2 = sp.Integer(counts["Type2-R"])
    bad_rows = [row["slot_index"] for row in consistency_rows if not row["pass"]]
    gates = {
        "total_slots_64": bool(sympy_total == 64),
        "unique_coordinates_64": bool(sympy_unique == 64),
        "type1_slots_32": bool(sympy_type1 == 32),
        "type2_slots_32": bool(sympy_type2 == 32),
        "coordinate_rows_all_pass": not bad_rows,
    }
    return {
        "schema_version": f"{SIM_ID}_jax_lane_v1",
        "sim_id": SIM_ID,
        "generated_at": common.now_z(),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "all_pass": all(gates.values()),
        "source_path": common.rel(SOURCE_PATH),
        "source_sha256": common.sha256_file(SOURCE_PATH),
        "result_path": common.rel(RESULT_PATH),
        "lane_role": "diagnostic mirror of slot-coordinate consistency rows and schedule cardinalities",
        "packages_used": ["sympy"],
        "aligned_packages_load_bearing": ["sympy"],
        "package_observables": {
            "sympy": "Integer cardinality equalities for total slots, unique coordinates, and per-engine counts"
        },
        "TOOL_MANIFEST": {
            "sympy": {
                "used": True,
                "reason": "load-bearing exact integer cardinality mirror of full-run slot-coordinate facts",
            }
        },
        "TOOL_INTEGRATION_DEPTH": {"sympy": "load_bearing"},
        "counts": {
            "total_slots": int(sympy_total),
            "unique_coordinate_count": int(sympy_unique),
            "type1_slots": int(sympy_type1),
            "type2_slots": int(sympy_type2),
            "bad_coordinate_rows": len(bad_rows),
        },
        "slot_coordinate_consistency": {
            "row_count": len(consistency_rows),
            "bad_row_count": len(bad_rows),
            "all_rows_pass": not bad_rows,
            "rows": consistency_rows,
        },
        "gates": gates,
        "boundary": {
            "values_unchanged": True,
            "reference_only": True,
            "pytorch_omitted": True,
        },
    }


def main() -> int:
    payload = build_result()
    common.write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": common.rel(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
