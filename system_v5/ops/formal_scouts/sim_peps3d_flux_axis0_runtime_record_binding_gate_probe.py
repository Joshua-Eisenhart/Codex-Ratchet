#!/usr/bin/env python3
"""Runtime-record binding gate for PEPS3D flux-bound Axis0 rows.

Formal scout only.

The PEPS3D flux-bound Axis0 rows currently run real spinor/quaternion shell
transport, but their local engine rows only carry topology, loop class,
operator, site, and substage index. This gate builds a source-conformant
runtime record surface with the missing IGT fields:

    engine type, sheet, chart token, terrain realization, path, A4,
    Axis5 family, Axis6 precedence/sign, native/non-native slot status.

It does not mutate the PEPS3D runner. It proves the missing binding can be
made explicitly and records that the raw rows are too shallow for promotion.
"""

from __future__ import annotations

import importlib.util
import json
import math
import pathlib
import sys
import time
from typing import Any

import torch

import canonical_qit_engine_specs as specs


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "peps3d_flux_axis0_runtime_record_binding_gate_probe_results.json"
SCALING_MODULE_PATH = ROOT / "sim_peps3d_spinor_network_flux_axis0_scaling_probe.py"

NAME = "peps3d_flux_axis0_runtime_record_binding_gate_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical_peps3d_flux_axis0_runtime_record_binding_gate"
SOURCE_ALIGNMENT_CATEGORY = "peps3d_flux_bound_axis0_runtime_record_binding"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: binds PEPS3D flux-bound Axis0 engine rows to source "
    "runtime-record metadata. It does not admit final Axis0, final flux, "
    "PEPS3D closure, Xi, Phi0, source-native dynamics, gravity, Standard "
    "Model, Yang-Mills, Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite tensor count and coverage checks over enriched runtime-record fields",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source schedule, operator slot, token, Axis5, and Axis6 metadata",
    },
    "peps3d_spinor_network_flux_axis0_scaling_probe": {
        "tried": True,
        "used": True,
        "reason": "supportive raw PEPS3D engine-row shape and site assignment source",
    },
    "python_importlib": {"tried": True, "used": True, "reason": "supportive local module loading"},
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "canonical_qit_engine_specs": "load_bearing",
    "peps3d_spinor_network_flux_axis0_scaling_probe": "supportive",
    "python_importlib": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

REQUIRED_BINDING_FIELDS = {
    "engine_type",
    "engine_label",
    "sheet",
    "shape",
    "site",
    "macro_stage_index",
    "substage_index",
    "topology",
    "terrain_realization",
    "loop_class",
    "path_class",
    "A4",
    "chart_token",
    "chart_operator",
    "slot_operator",
    "operator_family",
    "axis5_family",
    "axis6_token_precedence",
    "axis6_sign",
    "axis6_label",
    "substage_token",
    "is_native_operator",
    "is_chart_locked_slot",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    return value


def load_scaling_module() -> Any:
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("peps3d_axis0_scaling", SCALING_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {SCALING_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def path_class(engine_type: int, loop_class: str) -> str:
    if engine_type == 0:
        return "base" if loop_class == "outer" else "fiber"
    return "fiber" if loop_class == "outer" else "base"


def a4_class(engine_type: int, loop_class: str) -> str:
    if engine_type == 0:
        return "deductive" if loop_class == "outer" else "inductive"
    return "inductive" if loop_class == "outer" else "deductive"


def axis5_family(slot_operator: str) -> str:
    if slot_operator in {"Ti", "Te"}:
        return "dephasing"
    if slot_operator in {"Fi", "Fe"}:
        return "rotation"
    raise ValueError(slot_operator)


def enriched_records_for_shape(module: Any, shape: tuple[int, int, int]) -> list[dict[str, Any]]:
    all_sites = module.sites(shape)
    records: list[dict[str, Any]] = []
    for engine_type in [0, 1]:
        engine_spec = specs.get_engine_spec(engine_type)
        for sheet in ["L", "R"]:
            for macro_idx, (topology, loop_class) in enumerate(specs.get_schedule(engine_type)):
                topology_spec = specs.get_topology_spec(topology, engine_type)
                chart = specs.get_chart_token_spec(topology, engine_type, loop_class)
                for sub_idx in range(specs.N_SUBSTAGES_PER_MAIN):
                    slot = specs.get_operator_slot_spec(topology, engine_type, loop_class, sub_idx)
                    site = all_sites[(macro_idx + 2 * sub_idx + 3 * engine_type) % len(all_sites)]
                    records.append(
                        {
                            "engine_type": engine_type,
                            "engine_label": engine_spec["type_label"],
                            "sheet": sheet,
                            "shape": shape,
                            "site_count": math.prod(shape),
                            "site": site,
                            "macro_stage_index": macro_idx,
                            "substage_index": sub_idx,
                            "topology": topology,
                            "terrain_realization": topology_spec["realization"],
                            "terrain_dynamics_family": topology_spec["dynamics_family"],
                            "loop_class": loop_class,
                            "path_class": path_class(engine_type, loop_class),
                            "A4": a4_class(engine_type, loop_class),
                            "chart_token": chart["token"],
                            "chart_operator": chart["operator"],
                            "chart_axis6_token_precedence": chart["precedence"],
                            "chart_axis6_sign": chart["sign"],
                            "slot_operator": slot["operator"],
                            "operator_family": slot["operator_family"],
                            "axis5_family": axis5_family(slot["operator"]),
                            "axis6_token_precedence": slot["precedence"],
                            "axis6_sign": slot["sign"],
                            "axis6_label": slot["axis6"],
                            "substage_token": slot["token"],
                            "is_native_operator": slot["is_native_operator"],
                            "is_chart_locked_slot": slot["is_chart_locked"],
                        }
                    )
    return records


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        value = str(row[key])
        out[value] = out.get(value, 0) + 1
    return dict(sorted(out.items()))


def main() -> int:
    started = time.time()
    module = load_scaling_module()
    shapes = list(module.SHAPES)
    raw_rows = [row for shape in shapes for engine_type in [0, 1] for row in module.engine_rows(engine_type, shape)]
    raw_fields = set(raw_rows[0])
    raw_missing = sorted(REQUIRED_BINDING_FIELDS - raw_fields)
    enriched = [row for shape in shapes for row in enriched_records_for_shape(module, shape)]
    missing_by_row = [sorted(REQUIRED_BINDING_FIELDS - set(row)) for row in enriched]

    chart_tokens = sorted({row["chart_token"] for row in enriched})
    substage_tokens = sorted({row["substage_token"] for row in enriched})
    terrain_realizations = sorted({row["terrain_realization"] for row in enriched})
    chart_locked_count = sum(1 for row in enriched if row["is_chart_locked_slot"])
    native_count = sum(1 for row in enriched if row["is_native_operator"])
    records_per_shape_engine_sheet = {
        f"{row['shape']}|engine={row['engine_type']}|sheet={row['sheet']}": 0 for row in enriched
    }
    for row in enriched:
        key = f"{row['shape']}|engine={row['engine_type']}|sheet={row['sheet']}"
        records_per_shape_engine_sheet[key] += 1
    per_bucket_counts = torch.tensor(list(records_per_shape_engine_sheet.values()), dtype=torch.int64)

    checks = {
        "P1_raw_peps3d_engine_rows_missing_runtime_binding_fields": len(raw_missing) > 0,
        "P2_enriched_records_have_required_binding_fields": all(len(missing) == 0 for missing in missing_by_row),
        "P3_counts_match_32_substages_per_engine_sheet": bool(torch.all(per_bucket_counts == 32).item()),
        "P4_chart_tokens_cover_16_igt_tokens": len(chart_tokens) == 16,
        "P5_substage_records_cover_all_four_operators": set(count_by(enriched, "slot_operator")) == {"Ti", "Te", "Fi", "Fe"},
        "P6_axis5_and_axis6_fields_are_nontrivial": set(count_by(enriched, "axis5_family")) == {"dephasing", "rotation"}
        and set(count_by(enriched, "axis6_sign")) == {"-1", "1"},
        "P7_terrain_realization_count_is_8": len(terrain_realizations) == 8,
        "P8_chart_locked_and_non_native_slots_are_visible": 0 < chart_locked_count < len(enriched)
        and 0 < native_count < len(enriched),
        "P9_nonpromotion_boundary_intact": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
    }
    positive = {
        "runtime_binding_surface_built": {
            "pass": checks["P2_enriched_records_have_required_binding_fields"] and checks["P3_counts_match_32_substages_per_engine_sheet"],
            "total_enriched_records": len(enriched),
            "records_per_shape_engine_sheet": records_per_shape_engine_sheet,
        },
        "source_igt_coverage": {
            "pass": checks["P4_chart_tokens_cover_16_igt_tokens"] and checks["P7_terrain_realization_count_is_8"],
            "chart_tokens": chart_tokens,
            "terrain_realizations": terrain_realizations,
        },
        "axis5_axis6_coverage": {
            "pass": checks["P5_substage_records_cover_all_four_operators"] and checks["P6_axis5_and_axis6_fields_are_nontrivial"],
            "axis5_family_counts": count_by(enriched, "axis5_family"),
            "axis6_sign_counts": count_by(enriched, "axis6_sign"),
            "slot_operator_counts": count_by(enriched, "slot_operator"),
        },
    }
    graveyard = {
        "raw_peps3d_rows_are_too_shallow_for_runtime_claims": {
            "pass": checks["P1_raw_peps3d_engine_rows_missing_runtime_binding_fields"],
            "raw_fields": sorted(raw_fields),
            "missing_required_fields": raw_missing,
        },
        "slot_layer_must_not_collapse_to_chart_token_only": {
            "pass": checks["P8_chart_locked_and_non_native_slots_are_visible"],
            "chart_locked_slot_count": chart_locked_count,
            "native_operator_count": native_count,
            "total_record_count": len(enriched),
        },
    }
    boundary = {
        "formal_scout_only": {"pass": checks["P9_nonpromotion_boundary_intact"]},
        "binding_gate_not_runner_mutation": {
            "pass": True,
            "runner_mutated": False,
            "next_admissible_step": "consume enriched records in the PEPS3D flux Axis0 runner and rerun boundary/calibration stress",
        },
    }
    variants = list(positive.values()) + list(graveyard.values()) + list(boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "coverage": {
            "shape_count": len(shapes),
            "raw_row_count": len(raw_rows),
            "enriched_record_count": len(enriched),
            "records_per_shape_engine_sheet": records_per_shape_engine_sheet,
            "sample_records": enriched[:8],
        },
        "checks": checks,
        "nearby_variants": {
            "passed": sum(1 for row in variants if row["pass"]) + sum(1 for value in checks.values() if value),
            "total": len(variants) + len(checks),
            "failed_checks": [key for key, value in checks.items() if not value],
        },
        "all_pass": all(checks.values()) and all(row["pass"] for row in variants),
        "why_not_final": [
            "This gate builds metadata binding; it does not rerun PEPS3D dynamics with the enriched records.",
            "Raw PEPS3D Axis0 rows remain too shallow until they consume these runtime records directly.",
            "Pauli/Bloch chart metadata remains adapter/source-spec context, not root substrate evidence.",
        ],
        "divergence_log": [
            "Raw PEPS3D rows omit chart token, Axis5, Axis6, sheet, path, terrain realization, and native slot metadata.",
            "The enriched surface keeps chart-locked macro tokens separate from all-four-operator substage slots.",
        ],
        "why_not_v4_probes": "This is a v5 PEPS3D flux-bound Axis0 runtime-binding gate, not a legacy v4 probe.",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "enriched_record_count": len(enriched),
                "raw_missing_field_count": len(raw_missing),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
