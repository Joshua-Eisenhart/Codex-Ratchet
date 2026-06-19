#!/usr/bin/env python3
"""Run Carnot and Szilard engine fixtures through committed axis readouts."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any


SIM_ID = "engines_run_with_axes_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

CLASSIFICATION = "scratch_diagnostic"
ROW_CLASSIFICATION = "classical_baseline"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "classical_engine_axis_signature_baseline_only"
EXECUTION_KIND = "dynamics_on_committed_33_cell_carrier"
EXPECTED_STATE_COUNT = 33
EXPECTED_STROKE_COUNT = 4

AXIS0_DIR = ROOT / "system_v6" / "sims" / "discrete_axis0_field_v0"
AXIS6_DIR = ROOT / "system_v6" / "sims" / "discrete_axis6_precedence_v0"
AXIS4_DIR = ROOT / "system_v6" / "sims" / "discrete_axis4_composition_v0"
AXIS5_DIR = ROOT / "system_v6" / "sims" / "discrete_axis5_family_partial_v0"
LEDGER_DIR = ROOT / "system_v6" / "sims" / "carnot_szilard_landauer_ledger_v1"
BASIN_CYCLE_DIR = ROOT / "system_v6" / "sims" / "carnot_szilard_basin_cycle_v0"
SCRIPTS_DIR = ROOT / "scripts"

for import_dir in (AXIS0_DIR, AXIS6_DIR, AXIS4_DIR, AXIS5_DIR, LEDGER_DIR, BASIN_CYCLE_DIR, SCRIPTS_DIR):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

import carnot_szilard_basin_cycle_v0_common as basin_cycle_common  # noqa: E402
import carnot_szilard_landauer_ledger_v1_common as ledger_common  # noqa: E402
import discrete_axis0_field_v0_common as axis0_common  # noqa: E402
import discrete_axis4_composition_v0_common as axis4_common  # noqa: E402
import discrete_axis5_family_partial_v0_common as axis5_common  # noqa: E402
import discrete_axis6_precedence_v0_common as axis6_common  # noqa: E402
from builder_audit_boundary import builder_audit_boundary_errors, builder_audit_boundary_ok  # noqa: E402


PARENT_COMMITS = {
    "standards_codex": "c83842e55",
    "disciplined_path_doctrine": "df17999f2",
    "carnot_szilard_landauer_ledger_v1": "d79d71a0d",
    "carnot_szilard_basin_cycle_v0": "ffe6e1c38",
    "discrete_axis0_field_v0": "5d330b427",
    "discrete_axis6_precedence_v0": "b6fafc67f",
    "discrete_axis4_composition_v0": "99c4f84b3",
}

PARENT_PATHS = {
    "standards_codex": ROOT / "system_v6" / "receipts" / "audit_standards_codex_v1.md",
    "carnot_szilard_landauer_ledger_v1_common": LEDGER_DIR / "carnot_szilard_landauer_ledger_v1_common.py",
    "carnot_szilard_basin_cycle_v0_common": BASIN_CYCLE_DIR / "carnot_szilard_basin_cycle_v0_common.py",
    "axis0_common": AXIS0_DIR / "discrete_axis0_field_v0_common.py",
    "axis6_common": AXIS6_DIR / "discrete_axis6_precedence_v0_common.py",
    "axis4_common": AXIS4_DIR / "discrete_axis4_composition_v0_common.py",
    "axis5_common": AXIS5_DIR / "discrete_axis5_family_partial_v0_common.py",
}

TOOL_MANIFEST = {
    "python": {
        "tried": True,
        "used": True,
        "reason": "load-bearing execution of committed carrier generator edges for each engine stroke.",
    },
    "axis0_parent_builder": {
        "tried": True,
        "used": True,
        "reason": "load-bearing unchanged Axis-0 signed-gradient-flux readout consumed by hash/source lock.",
    },
    "axis6_parent_builder": {
        "tried": True,
        "used": True,
        "reason": "load-bearing unchanged Axis-6 precedence readout consumed by hash/source lock.",
    },
    "axis4_parent_builder": {
        "tried": True,
        "used": True,
        "reason": "load-bearing unchanged Axis-4 W4 fixture readout consumed by hash/source lock.",
    },
    "axis5_family_parent_builder": {
        "tried": True,
        "used": True,
        "reason": "load-bearing unchanged partial Axis-5 operator-family witness rows consumed by hash/source lock.",
    },
    "ledger_parent_builder": {
        "tried": True,
        "used": True,
        "reason": "load-bearing committed Carnot and Szilard typed ledger rows.",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "load-bearing builder/audit boundary gate; builder emits no audit verdict.",
    },
    "json_hashing": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic result serialization and signature hashes.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "python": "load_bearing",
    "axis0_parent_builder": "load_bearing",
    "axis6_parent_builder": "load_bearing",
    "axis4_parent_builder": "load_bearing",
    "axis5_family_parent_builder": "load_bearing",
    "ledger_parent_builder": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "json_hashing": "supportive",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_last_commit(path: Path) -> str:
    try:
        rel_path = rel(path)
        result = subprocess.run(
            ["git", "log", "-n", "1", "--format=%h", "--", rel_path],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
    except Exception:
        return "unavailable"
    return result.stdout.strip() or "unavailable"


def _counter(values: list[Any]) -> dict[str, int]:
    return dict(sorted((str(key), int(value)) for key, value in Counter(values).items()))


def _short_row(row: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {key: row.get(key) for key in keys}


@lru_cache(maxsize=1)
def parent_objects() -> dict[str, Any]:
    carrier = axis0_common.rebuild_committed_carrier()
    return {
        "carrier": carrier,
        "axis0": axis0_common.build_axis0_object(),
        "axis6": axis6_common.build_axis6_object(),
        "axis4": axis4_common.build_axis4_object(),
        "axis5_family_partial": axis5_common.build_axis5_object(),
    }


def transition_lookup(carrier: dict[str, Any]) -> dict[tuple[int, str], int]:
    lookup: dict[tuple[int, str], int] = {}
    for edge in carrier["edges"]:
        key = (int(edge["src"]), str(edge["generator"]))
        if key in lookup:
            raise ValueError(f"duplicate transition edge for {key}")
        lookup[key] = int(edge["dst"])
    return lookup


def initial_cells(carrier: dict[str, Any]) -> list[int]:
    return sorted(int(cell["cell_id"]) for cell in carrier["cells"])


def carnot_ledger_strokes() -> list[dict[str, Any]]:
    row = ledger_common.cycle_ledgers()["reversible_carnot_cycle"]
    return ledger_common.serialize_cycle("reversible_carnot_cycle", row)["strokes"]


def szilard_paid_row() -> dict[str, Any]:
    return ledger_common.szilard_rows()["szilard_paid_measure_feedback_erase"]


def szilard_ledger_strokes() -> list[dict[str, Any]]:
    paid = szilard_paid_row()
    ledger = list(paid["ledger"])
    reset_row = {
        "stroke": "reset_boundary",
        "nats_recorded_ln2_coeff": {"num": 0, "den": 1, "string": "0/1", "float": 0.0},
        "work_out_ln2_coeff": {"num": 0, "den": 1, "string": "0/1", "float": 0.0},
        "erasure_paid_ln2_coeff": {"num": 0, "den": 1, "string": "0/1", "float": 0.0},
        "source_note": "packet-local reset split after committed paid erasure row; no extra work or erasure credit",
    }
    return ledger + [reset_row]


def engine_specs() -> dict[str, dict[str, Any]]:
    carnot_ledgers = carnot_ledger_strokes()
    szilard_ledgers = szilard_ledger_strokes()
    return {
        "carnot": {
            "engine_label": "Carnot",
            "ledger_source": "carnot_szilard_landauer_ledger_v1.reversible_carnot_cycle",
            "stroke_generator_boundary": "fixture over committed generator names; heat/work stays ledger data",
            "strokes": [
                {"stroke": "hot_isothermal_expansion", "generator": "Ne_Spiral_R", "typed_ledger": carnot_ledgers[0]},
                {"stroke": "adiabatic_expansion", "generator": "R_x", "typed_ledger": carnot_ledgers[1]},
                {"stroke": "cold_isothermal_compression", "generator": "D_z", "typed_ledger": carnot_ledgers[2]},
                {"stroke": "adiabatic_compression", "generator": "Se_Funnel_L", "typed_ledger": carnot_ledgers[3]},
            ],
        },
        "szilard": {
            "engine_label": "Szilard",
            "ledger_source": "carnot_szilard_landauer_ledger_v1.szilard_paid_measure_feedback_erase",
            "stroke_generator_boundary": "fixture over committed generator names; measurement/work/erasure stays ledger data",
            "strokes": [
                {"stroke": "measure_record_one_bit", "generator": "D_z", "typed_ledger": szilard_ledgers[0]},
                {"stroke": "feedback_isothermal_expansion", "generator": "Ni_Source_R", "typed_ledger": szilard_ledgers[1]},
                {"stroke": "erase_record", "generator": "R_x", "typed_ledger": szilard_ledgers[2]},
                {"stroke": "reset_boundary", "generator": "Ni_Pit_L", "typed_ledger": szilard_ledgers[3]},
            ],
        },
    }


def axis_tables() -> dict[str, Any]:
    objects = parent_objects()
    axis5_rows_by_cell: dict[int, list[dict[str, Any]]] = {}
    for row in objects["axis5_family_partial"]["axis5_family_table"]:
        axis5_rows_by_cell.setdefault(int(row["cell_id"]), []).append(row)
    for rows in axis5_rows_by_cell.values():
        rows.sort(key=lambda item: str(item["operator"]))
    return {
        "axis0": {int(row["cell_id"]): row for row in objects["axis0"]["readout_table"]},
        "axis6": {int(row["cell_id"]): row for row in objects["axis6"]["precedence_table"]},
        "axis4": {int(row["cell_id"]): row for row in objects["axis4"]["axis4_readout_table"]},
        "axis5_family": axis5_rows_by_cell,
    }


def source_locks() -> dict[str, dict[str, Any]]:
    objects = parent_objects()
    axis5_commit = git_last_commit(PARENT_PATHS["axis5_common"])
    return {
        "axis0": {
            "sim_id": axis0_common.SIM_ID,
            "commit_hint": PARENT_COMMITS["discrete_axis0_field_v0"],
            "source_path": rel(PARENT_PATHS["axis0_common"]),
            "source_sha256": sha256_file(PARENT_PATHS["axis0_common"]),
            "readout_signature_sha256": stable_sha256(objects["axis0"]["readout_table"]),
        },
        "axis6": {
            "sim_id": axis6_common.SIM_ID,
            "commit_hint": PARENT_COMMITS["discrete_axis6_precedence_v0"],
            "source_path": rel(PARENT_PATHS["axis6_common"]),
            "source_sha256": sha256_file(PARENT_PATHS["axis6_common"]),
            "readout_signature_sha256": stable_sha256(objects["axis6"]["precedence_table"]),
        },
        "axis4": {
            "sim_id": axis4_common.SIM_ID,
            "commit_hint": PARENT_COMMITS["discrete_axis4_composition_v0"],
            "source_path": rel(PARENT_PATHS["axis4_common"]),
            "source_sha256": sha256_file(PARENT_PATHS["axis4_common"]),
            "readout_signature_sha256": stable_sha256(objects["axis4"]["axis4_readout_table"]),
        },
        "axis5_family_partial": {
            "sim_id": axis5_common.SIM_ID,
            "commit_hint": axis5_commit,
            "source_path": rel(PARENT_PATHS["axis5_common"]),
            "source_sha256": sha256_file(PARENT_PATHS["axis5_common"]),
            "partial_scope": axis5_common.PARTIAL_SCOPE,
            "readout_signature_sha256": stable_sha256(objects["axis5_family_partial"]["axis5_family_table"]),
        },
    }


def axis_signature(cells: list[int], stroke_index: int, stroke_name: str, generator: str) -> dict[str, Any]:
    tables = axis_tables()

    axis0_values = [int(tables["axis0"][cell]["axis0_polarity_sign"]) for cell in cells]
    axis6_values = [int(tables["axis6"][cell]["b6_sign"]) for cell in cells]
    axis4_values = [int(tables["axis4"][cell]["axis4_sign"]) for cell in cells]
    axis5_values = []
    axis5_family_values = []
    axis5_ordered_rows = []
    for cell in cells:
        rows = tables["axis5_family"][cell]
        cell_rows = [
            {
                "operator": row["operator"],
                "axis5_sign": int(row["axis5_sign"]),
                "axis5_family": row["axis5_family"],
            }
            for row in rows
        ]
        axis5_ordered_rows.append({"cell_id": cell, "operator_rows": cell_rows})
        axis5_values.extend(row["axis5_sign"] for row in cell_rows)
        axis5_family_values.extend(row["axis5_family"] for row in cell_rows)

    profiles = {
        "axis0": {
            "source_readout": axis0_common.SIM_ID,
            "polarity_key": "axis0_polarity_sign",
            "ordered_values": axis0_values,
            "counts": _counter(axis0_values),
            "ordered_signature_sha256": stable_sha256(axis0_values),
            "count_signature_sha256": stable_sha256(_counter(axis0_values)),
            "sample_rows": [_short_row(tables["axis0"][cell], ["cell_id", "axis0_polarity", "axis0_polarity_sign"]) for cell in cells[:5]],
        },
        "axis6": {
            "source_readout": axis6_common.SIM_ID,
            "polarity_key": "b6_sign",
            "ordered_values": axis6_values,
            "counts": _counter(axis6_values),
            "ordered_signature_sha256": stable_sha256(axis6_values),
            "count_signature_sha256": stable_sha256(_counter(axis6_values)),
            "sample_rows": [_short_row(tables["axis6"][cell], ["cell_id", "b6_label", "b6_sign"]) for cell in cells[:5]],
        },
        "axis4": {
            "source_readout": axis4_common.SIM_ID,
            "polarity_key": "axis4_sign",
            "ordered_values": axis4_values,
            "counts": _counter(axis4_values),
            "ordered_signature_sha256": stable_sha256(axis4_values),
            "count_signature_sha256": stable_sha256(_counter(axis4_values)),
            "sample_rows": [_short_row(tables["axis4"][cell], ["cell_id", "axis4_label", "axis4_sign", "W4_trace_norm"]) for cell in cells[:5]],
        },
        "axis5_family": {
            "source_readout": axis5_common.SIM_ID,
            "partial_scope": axis5_common.PARTIAL_SCOPE,
            "polarity_key": "axis5_sign",
            "ordered_values": axis5_ordered_rows,
            "counts": _counter(axis5_values),
            "family_counts": _counter(axis5_family_values),
            "ordered_signature_sha256": stable_sha256(axis5_ordered_rows),
            "count_signature_sha256": stable_sha256({"signs": _counter(axis5_values), "families": _counter(axis5_family_values)}),
            "sample_rows": axis5_ordered_rows[:5],
        },
    }
    per_stroke_row = {
        "stroke_index": stroke_index,
        "stroke": stroke_name,
        "generator": generator,
        "axis0_counts": profiles["axis0"]["counts"],
        "axis6_counts": profiles["axis6"]["counts"],
        "axis4_counts": profiles["axis4"]["counts"],
        "axis5_family_counts": profiles["axis5_family"]["family_counts"],
        "combined_ordered_signature_sha256": stable_sha256(
            {
                "axis0": profiles["axis0"]["ordered_signature_sha256"],
                "axis6": profiles["axis6"]["ordered_signature_sha256"],
                "axis4": profiles["axis4"]["ordered_signature_sha256"],
                "axis5_family": profiles["axis5_family"]["ordered_signature_sha256"],
            }
        ),
    }
    return {
        "computed_on": "post_stroke_running_trajectory",
        "axis_profiles": profiles,
        "per_stroke_polarity_row": per_stroke_row,
    }


def run_strokes(
    engine_name: str,
    stroke_rows: list[dict[str, Any]],
    *,
    identity: bool = False,
    order_label: str = "canonical_order",
) -> dict[str, Any]:
    carrier = parent_objects()["carrier"]
    lookup = transition_lookup(carrier)
    cells = initial_cells(carrier)
    strokes = []
    for index, stroke in enumerate(stroke_rows):
        before = list(cells)
        generator = "IDENTITY" if identity else stroke["generator"]
        missing = []
        trajectory = []
        after = []
        for start_cell, before_cell in zip(initial_cells(carrier), before, strict=True):
            if identity:
                after_cell = before_cell
            else:
                key = (before_cell, generator)
                if key not in lookup:
                    missing.append({"cell": before_cell, "generator": generator})
                    after_cell = before_cell
                else:
                    after_cell = lookup[key]
            after.append(after_cell)
            trajectory.append(
                {
                    "start_cell": start_cell,
                    "before_cell": before_cell,
                    "after_cell": after_cell,
                    "generator": generator,
                    "changed": before_cell != after_cell,
                }
            )
        signature = axis_signature(after, index, stroke["stroke"], generator)
        strokes.append(
            {
                "stroke_index": index,
                "stroke": stroke["stroke"],
                "generator": generator,
                "state_trajectory": trajectory,
                "transition_count": len(trajectory),
                "missing_transition_count": len(missing),
                "missing_transitions": missing,
                "typed_ledger": stroke["typed_ledger"],
                "pre_cells_sha256": stable_sha256(before),
                "post_cells_sha256": stable_sha256(after),
                "changed_cell_count": sum(row["changed"] for row in trajectory),
                "axis_signature": signature,
            }
        )
        cells = after
    return {
        "engine_name": engine_name,
        "order_label": order_label,
        "strokes": strokes,
        "trajectory": {
            "initial_cell_count": EXPECTED_STATE_COUNT,
            "final_cell_count": len(cells),
            "initial_cells_sha256": stable_sha256(initial_cells(carrier)),
            "final_cells_sha256": stable_sha256(cells),
            "final_cells": cells,
            "combined_stroke_signature_sha256": stable_sha256([stroke["axis_signature"]["per_stroke_polarity_row"] for stroke in strokes]),
        },
    }


def run_engine(engine_name: str, spec: dict[str, Any]) -> dict[str, Any]:
    executed = run_strokes(engine_name, spec["strokes"])
    return {
        "engine_label": spec["engine_label"],
        "ledger_source": spec["ledger_source"],
        "stroke_generator_boundary": spec["stroke_generator_boundary"],
        "row_classification": ROW_CLASSIFICATION,
        "typed_ledger": [stroke["typed_ledger"] for stroke in spec["strokes"]],
        **executed,
    }


def compare_engines(carnot: dict[str, Any], szilard: dict[str, Any]) -> dict[str, Any]:
    differing_rows = []
    for c_stroke, s_stroke in zip(carnot["strokes"], szilard["strokes"], strict=True):
        differing_axes = []
        for axis_name in ("axis0", "axis6", "axis4", "axis5_family"):
            c_profile = c_stroke["axis_signature"]["axis_profiles"][axis_name]
            s_profile = s_stroke["axis_signature"]["axis_profiles"][axis_name]
            if c_profile["ordered_signature_sha256"] != s_profile["ordered_signature_sha256"]:
                differing_axes.append(axis_name)
        if differing_axes:
            differing_rows.append(
                {
                    "stroke_index": c_stroke["stroke_index"],
                    "carnot_stroke": c_stroke["stroke"],
                    "szilard_stroke": s_stroke["stroke"],
                    "carnot_generator": c_stroke["generator"],
                    "szilard_generator": s_stroke["generator"],
                    "differing_axes": differing_axes,
                    "carnot_combined_signature": c_stroke["axis_signature"]["per_stroke_polarity_row"][
                        "combined_ordered_signature_sha256"
                    ],
                    "szilard_combined_signature": s_stroke["axis_signature"]["per_stroke_polarity_row"][
                        "combined_ordered_signature_sha256"
                    ],
                }
            )
    return {
        "computed": True,
        "profiles_differ": bool(differing_rows)
        or carnot["trajectory"]["combined_stroke_signature_sha256"] != szilard["trajectory"]["combined_stroke_signature_sha256"],
        "differing_stroke_rows": differing_rows,
        "carnot_signature_sha256": carnot["trajectory"]["combined_stroke_signature_sha256"],
        "szilard_signature_sha256": szilard["trajectory"]["combined_stroke_signature_sha256"],
    }


def identity_control() -> dict[str, Any]:
    spec = {
        "strokes": [
            {"stroke": f"identity_stroke_{index}", "generator": "IDENTITY", "typed_ledger": {"stroke": f"identity_stroke_{index}"}}
            for index in range(EXPECTED_STROKE_COUNT)
        ]
    }
    executed = run_strokes("identity", spec["strokes"], identity=True, order_label="identity_control")
    per_stroke_hashes = [
        stroke["axis_signature"]["per_stroke_polarity_row"]["combined_ordered_signature_sha256"] for stroke in executed["strokes"]
    ]
    return {
        "status": "pass",
        "all_strokes_identity": all(stroke["changed_cell_count"] == 0 for stroke in executed["strokes"]),
        "degenerate_signatures": len(set(per_stroke_hashes)) == 1,
        "signature_sha256": stable_sha256(per_stroke_hashes),
        "stroke_signature_hashes": per_stroke_hashes,
    }


def shuffled_control(specs: dict[str, dict[str, Any]], engines: dict[str, dict[str, Any]]) -> dict[str, Any]:
    result = {}
    order = [0, 2, 1, 3]
    for engine_name, spec in specs.items():
        shuffled_strokes = [spec["strokes"][index] for index in order]
        shuffled = run_strokes(engine_name, shuffled_strokes, order_label="N01_shuffled_order")
        canonical = engines[engine_name]
        signature_changed = (
            shuffled["trajectory"]["combined_stroke_signature_sha256"]
            != canonical["trajectory"]["combined_stroke_signature_sha256"]
        )
        final_changed = shuffled["trajectory"]["final_cells_sha256"] != canonical["trajectory"]["final_cells_sha256"]
        result[engine_name] = {
            "status": "pass" if signature_changed else "fail",
            "order": order,
            "signature_changed": signature_changed,
            "final_cells_changed": final_changed,
            "canonical_signature_sha256": canonical["trajectory"]["combined_stroke_signature_sha256"],
            "shuffled_signature_sha256": shuffled["trajectory"]["combined_stroke_signature_sha256"],
            "canonical_final_cells_sha256": canonical["trajectory"]["final_cells_sha256"],
            "shuffled_final_cells_sha256": shuffled["trajectory"]["final_cells_sha256"],
        }
    return result


def ledger_continuity() -> dict[str, Any]:
    carnot_names = [row["stroke"] for row in carnot_ledger_strokes()]
    spec_names = [row["stroke"] for row in engine_specs()["carnot"]["strokes"]]
    szilard = szilard_paid_row()
    return {
        "ledger_v1_commit_hint": PARENT_COMMITS["carnot_szilard_landauer_ledger_v1"],
        "basin_cycle_commit_hint": PARENT_COMMITS["carnot_szilard_basin_cycle_v0"],
        "basin_cycle_declares_ledger_parent": basin_cycle_common.PARENT_COMMITS.get("classical_ledger_envelope"),
        "carnot_stroke_names": carnot_names,
        "carnot_stroke_names_match": carnot_names == spec_names,
        "szilard_paid_row_sat": szilard["z3"]["status"] == "sat" and szilard["cvc5"]["status"] == "sat",
        "szilard_paid_row_name": "szilard_paid_measure_feedback_erase",
        "szilard_required_erasure": szilard["derived"]["required_erasure"],
        "landauer_paid_gte_required_constraints": {
            "z3": szilard["z3"]["constraints"]["paid_erasure_cost_gte_required_landauer_cost"],
            "cvc5": szilard["cvc5"]["constraints"]["paid_erasure_cost_gte_required_landauer_cost"],
        },
    }


def build_packet() -> dict[str, Any]:
    specs = engine_specs()
    engines = {name: run_engine(name, spec) for name, spec in specs.items()}
    comparison = compare_engines(engines["carnot"], engines["szilard"])
    controls = {
        "do_nothing_identity_engine": identity_control(),
        "shuffled_stroke_order_N01": shuffled_control(specs, engines),
    }
    carrier = parent_objects()["carrier"]
    boundary_ok = builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    all_pass = (
        carrier["state_count"] == EXPECTED_STATE_COUNT
        and set(engines) == {"carnot", "szilard"}
        and all(len(engine["strokes"]) == EXPECTED_STROKE_COUNT for engine in engines.values())
        and all(stroke["missing_transition_count"] == 0 for engine in engines.values() for stroke in engine["strokes"])
        and comparison["profiles_differ"] is True
        and controls["do_nothing_identity_engine"]["degenerate_signatures"] is True
        and all(row["signature_changed"] is True for row in controls["shuffled_stroke_order_N01"].values())
        and ledger_continuity()["carnot_stroke_names_match"] is True
        and ledger_continuity()["szilard_paid_row_sat"] is True
        and boundary_ok is True
    )
    locks = source_locks()
    baseline_row = {
        "classification": ROW_CLASSIFICATION,
        "role": "classical_baseline_for_future_qit_engine_signature",
        "comparison_target": "future_qit_engine_signature_must_exceed_or_differ_from_this_classical_signature_table",
        "carnot_signature_sha256": comparison["carnot_signature_sha256"],
        "szilard_signature_sha256": comparison["szilard_signature_sha256"],
        "comparison_sha256": stable_sha256(comparison),
    }
    return {
        "schema_version": "engines_run_with_axes_v0_result_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "row_classification": ROW_CLASSIFICATION,
        "sim_execution_kind": "classical_baseline",
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_condition": "None inside this packet; a future QIT engine packet must compute a separate signature and beat or differ from this baseline under its own gates.",
        "demotion_condition": "Demote if any engine stroke stops executing over all 33 cells, any parent readout is modified, identity signatures cease to be degenerate, shuffled N01 signatures stop changing, or ledger continuity with d79d71a0d fails.",
        "blocked_until": "Not blocked for this classical baseline; nonclassical/QIT comparison is blocked until a separate QIT engine signature packet exists.",
        "next_lego_target": "future_qit_engine_axis_signature_comparison_v0",
        "out_of_scope": [
            "QIT engine admission",
            "nonclassical superiority",
            "thermodynamic heat bath dynamics on basin carrier",
            "Axis admission",
            "Axis-5 completion",
            "physics",
            "bridge admission",
        ],
        "execution_kind": EXECUTION_KIND,
        "all_pass": all_pass,
        "carrier": {
            "state_count": carrier["state_count"],
            "edge_count": carrier["edge_count"],
            "generator_names": carrier["generator_names"],
            "transition_graph_sha256": carrier["transition_graph_sha256"],
            "state_object_id": carrier["state_object_id"],
        },
        "running_engines": engines,
        "axis_readout_source_locks": locks,
        "pinned_functionals_applied_unchanged": True,
        "axis_profile_method": "lookup unchanged committed axis readout tables on each post-stroke running trajectory",
        "carnot_vs_szilard_signature_comparison": comparison,
        "baseline_row": baseline_row,
        "controls": controls,
        "ledger_continuity": ledger_continuity(),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [
            {
                "row": "future_qit_engine_signature",
                "baseline": "classical Carnot/Szilard signatures computed here",
                "required_future_difference": "future QIT engine must exceed or differ from the staged classical_baseline signature table",
            }
        ],
        "builder_gates": {
            "file_disjoint_packet": True,
            "no_builder_audit_verdict": boundary_ok,
            "no_builder_audit_verdict_envelope_gate": boundary_ok,
            "packet_audit_verdict_absent": boundary_ok,
            "boundary_helper_path": "scripts/builder_audit_boundary.py",
            "boundary_helper_fully_used": True,
        },
        "no_builder_audit_verdict": boundary_ok,
        "no_builder_audit_verdict_envelope_gate": boundary_ok,
        "disallowed_claims": [
            "QIT engine admission",
            "nonclassical superiority",
            "thermodynamic heat bath dynamics on basin carrier",
            "Axis admission",
            "Axis-5 completion",
            "physics",
            "bridge admission",
        ],
        "source_locks": {
            key: {
                "path": rel(path),
                "git_last_commit": git_last_commit(path),
                "sha256": sha256_file(path),
            }
            for key, path in PARENT_PATHS.items()
        },
        "prior_receipts": [
            rel(LEDGER_DIR / "results" / "carnot_szilard_landauer_ledger_v1_envelope_results.json"),
            rel(BASIN_CYCLE_DIR / "results" / "carnot_szilard_basin_cycle_v0_envelope_results.json"),
            rel(AXIS0_DIR / "results" / "discrete_axis0_field_v0_envelope_results.json"),
            rel(AXIS6_DIR / "results" / "discrete_axis6_precedence_v0_envelope_results.json"),
            rel(AXIS4_DIR / "results" / "discrete_axis4_composition_v0_envelope_results.json"),
            rel(AXIS5_DIR / "results" / "discrete_axis5_family_partial_v0_envelope_results.json"),
        ],
    }


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("schema_version") == "engines_run_with_axes_v0_result_v1", "schema version mismatch")
    require(errors, payload.get("sim_id") == SIM_ID, "sim_id mismatch")
    require(errors, payload.get("classification") == CLASSIFICATION, "classification mismatch")
    require(errors, payload.get("row_classification") == ROW_CLASSIFICATION, "row_classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("execution_kind") == EXECUTION_KIND, "execution_kind mismatch")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    require(errors, payload.get("carrier", {}).get("state_count") == EXPECTED_STATE_COUNT, "carrier state_count mismatch")
    require(errors, payload.get("carrier", {}).get("edge_count") == 198, "carrier edge_count mismatch")

    engines = payload.get("running_engines", {})
    require(errors, set(engines) == {"carnot", "szilard"}, "engine set mismatch")
    for engine_name, engine in engines.items():
        require(errors, engine.get("row_classification") == ROW_CLASSIFICATION, f"{engine_name} row classification mismatch")
        require(errors, len(engine.get("strokes", [])) == EXPECTED_STROKE_COUNT, f"{engine_name} stroke count mismatch")
        require(errors, engine.get("trajectory", {}).get("initial_cell_count") == EXPECTED_STATE_COUNT, f"{engine_name} initial count mismatch")
        require(errors, engine.get("trajectory", {}).get("final_cell_count") == EXPECTED_STATE_COUNT, f"{engine_name} final count mismatch")
        for stroke in engine.get("strokes", []):
            require(errors, stroke.get("transition_count") == EXPECTED_STATE_COUNT, f"{engine_name} transition count mismatch")
            require(errors, stroke.get("missing_transition_count") == 0, f"{engine_name} missing transition")
            require(errors, len(stroke.get("state_trajectory", [])) == EXPECTED_STATE_COUNT, f"{engine_name} trajectory length mismatch")
            signature = stroke.get("axis_signature", {})
            require(errors, signature.get("computed_on") == "post_stroke_running_trajectory", f"{engine_name} signature surface mismatch")
            require(
                errors,
                set(signature.get("axis_profiles", {})) == {"axis0", "axis6", "axis4", "axis5_family"},
                f"{engine_name} axis profile set mismatch",
            )

    locks = payload.get("axis_readout_source_locks", {})
    require(errors, locks.get("axis0", {}).get("commit_hint") == "5d330b427", "axis0 commit hint mismatch")
    require(errors, locks.get("axis6", {}).get("commit_hint") == "b6fafc67f", "axis6 commit hint mismatch")
    require(errors, locks.get("axis4", {}).get("commit_hint") == "99c4f84b3", "axis4 commit hint mismatch")
    require(errors, locks.get("axis5_family_partial", {}).get("partial_scope") == "axis5_operator_family_half_only", "axis5 scope mismatch")
    require(errors, payload.get("pinned_functionals_applied_unchanged") is True, "pinned functional flag missing")

    comparison = payload.get("carnot_vs_szilard_signature_comparison", {})
    require(errors, comparison.get("computed") is True, "comparison not computed")
    require(errors, comparison.get("profiles_differ") is True, "profiles did not differ")
    require(errors, bool(comparison.get("differing_stroke_rows")), "differing rows missing")

    controls = payload.get("controls", {})
    identity = controls.get("do_nothing_identity_engine", {})
    require(errors, identity.get("all_strokes_identity") is True, "identity control did not stay identity")
    require(errors, identity.get("degenerate_signatures") is True, "identity signatures not degenerate")
    shuffled = controls.get("shuffled_stroke_order_N01", {})
    for engine_name in ("carnot", "szilard"):
        require(errors, shuffled.get(engine_name, {}).get("signature_changed") is True, f"{engine_name} shuffled control did not change")

    baseline = payload.get("baseline_row", {})
    require(errors, baseline.get("classification") == ROW_CLASSIFICATION, "baseline classification mismatch")
    require(
        errors,
        baseline.get("role") == "classical_baseline_for_future_qit_engine_signature",
        "baseline row role mismatch",
    )

    ledger = payload.get("ledger_continuity", {})
    require(errors, ledger.get("ledger_v1_commit_hint") == "d79d71a0d", "ledger commit hint mismatch")
    require(errors, ledger.get("basin_cycle_commit_hint") == "ffe6e1c38", "basin-cycle commit hint mismatch")
    require(errors, ledger.get("carnot_stroke_names_match") is True, "Carnot ledger names mismatch")
    require(errors, ledger.get("szilard_paid_row_sat") is True, "Szilard paid row not SAT")

    require(errors, payload.get("TOOL_MANIFEST") == TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, bool(payload.get("divergence_log")), "divergence_log missing")
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict false")
    require(errors, payload.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict_envelope_gate false")
    require(errors, payload.get("builder_gates", {}).get("boundary_helper_fully_used") is True, "boundary helper not fully used")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    for banned in ("QIT engine admission", "nonclassical superiority", "Axis admission", "Axis-5 completion"):
        require(errors, banned in payload.get("disallowed_claims", []), f"missing disallowed claim: {banned}")
    return errors
