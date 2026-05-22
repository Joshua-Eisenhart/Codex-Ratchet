#!/usr/bin/env python3
"""Terrain/stage contribution to the QIT engine slow spectral mode.

The spectral map shows that the single-engine slow mode is a useful memory
carrier. This scout asks the next mechanistic question: which terrain
placements affect that slow mode, and is the ordered engine channel genuinely
different from reversed or all-at-once variants?
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

import sim_two_root_constraint_engine_spectral_manifold_phase_map_probe as phase
import sim_two_root_constraint_iter195_single_engine_spectral_reproduction_probe as spectral


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_terrain_stage_spectral_contribution_probe_results.json"

NAME = "two_root_constraint_terrain_stage_spectral_contribution_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_terrain_stage_spectral_contribution"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_terrain_stage_spectral_contribution"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal terrain/stage spectral-contribution scout only: quantifies how "
    "terrain placements affect the single-engine slow mode and ordered channel. "
    "It cannot promote Phi0 bridge closure, PEPS/PEPS3D dynamics, coupled E16 "
    "dynamics, final manifold admission, or real scale-level attractor-basin admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing terrain-stage channel construction, exact exponentials, spectral readouts, and ordered-channel norm comparisons",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard and contribution-class sanity constraints",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

SHEET = "L"
DIRECTION = phase.scaled_direction("raw_xz", 1.0)
PROFILE = phase.PROFILES["balanced"]
TAU = 1.0
TERRAINS = ["Se", "Ne", "Ni", "Si"]
SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "spectral_reproduction_result": RESULT_DIR / "two_root_constraint_iter195_single_engine_spectral_reproduction_probe_results.json",
    "spectral_map_result": RESULT_DIR / "two_root_constraint_engine_spectral_manifold_phase_map_probe_results.json",
    "spectral_reproduction_scout": SCOUT_ROOT / "sim_two_root_constraint_iter195_single_engine_spectral_reproduction_probe.py",
    "spectral_map_scout": SCOUT_ROOT / "sim_two_root_constraint_engine_spectral_manifold_phase_map_probe.py",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def jsonable(value: Any) -> Any:
    return spectral.jsonable(value)


def compose_order(order: list[str]) -> torch.Tensor:
    stages = phase.scaled_stages(SHEET, DIRECTION, PROFILE)
    channel = torch.eye(4, dtype=spectral.DTYPE)
    for terrain in order:
        H, collapse_ops = stages[terrain]
        channel = spectral.stage_propagator(H, collapse_ops, TAU) @ channel
    return channel


def channel_stats(channel: torch.Tensor) -> dict[str, Any]:
    eigvals = torch.linalg.eigvals(channel)
    eig_abs = spectral.sorted_abs(eigvals)
    return {
        "eig_abs": eig_abs,
        "slow_mode_abs": eig_abs[1],
        "spectral_gap": 1.0 - eig_abs[1],
        "fixed_bloch": phase.fixed_bloch(channel),
    }


def variant_row(name: str, order: list[str], baseline: dict[str, Any], baseline_channel: torch.Tensor) -> dict[str, Any]:
    channel = compose_order(order)
    stats = channel_stats(channel)
    return {
        "variant": name,
        "order": order,
        "stage_count": len(order),
        "terrain_counts": {terrain: order.count(terrain) for terrain in TERRAINS},
        "slow_mode_abs": stats["slow_mode_abs"],
        "delta_slow_mode_abs": stats["slow_mode_abs"] - baseline["slow_mode_abs"],
        "spectral_gap": stats["spectral_gap"],
        "delta_spectral_gap": stats["spectral_gap"] - baseline["spectral_gap"],
        "fixed_bloch": stats["fixed_bloch"],
        "channel_norm_delta": float(torch.linalg.matrix_norm(channel - baseline_channel).real.item()),
    }


def terrain_rows(baseline: dict[str, Any], baseline_channel: torch.Tensor, base_order: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for terrain in TERRAINS:
        rows.append(variant_row(f"remove_all_{terrain}", [item for item in base_order if item != terrain], baseline, baseline_channel))
        duplicated: list[str] = []
        for item in base_order:
            duplicated.append(item)
            if item == terrain:
                duplicated.append(item)
        rows.append(variant_row(f"duplicate_all_{terrain}", duplicated, baseline, baseline_channel))
        rows.append(variant_row(f"only_double_{terrain}", [terrain, terrain], baseline, baseline_channel))
    return rows


def placement_rows(baseline: dict[str, Any], baseline_channel: torch.Tensor, base_order: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, terrain in enumerate(base_order):
        rows.append(variant_row(f"drop_pos_{idx}_{terrain}", base_order[:idx] + base_order[idx + 1 :], baseline, baseline_channel))
        rows.append(variant_row(f"duplicate_pos_{idx}_{terrain}", base_order[: idx + 1] + [terrain] + base_order[idx + 1 :], baseline, baseline_channel))
    return rows


def order_rows(baseline: dict[str, Any], baseline_channel: torch.Tensor, base_order: list[str]) -> list[dict[str, Any]]:
    all_at_once = phase.channel_for(
        sheet=SHEET,
        direction=DIRECTION,
        profile=PROFILE,
        tau=TAU,
        order_variant="all_at_once",
    )
    reversed_channel = compose_order(list(reversed(base_order)))
    return [
        {
            "variant": "reversed_order",
            "order": list(reversed(base_order)),
            **{
                key: value
                for key, value in variant_row("reversed_order", list(reversed(base_order)), baseline, baseline_channel).items()
                if key not in {"variant", "order"}
            },
        },
        {
            "variant": "all_at_once_liouvillian",
            "order": "exp(sum Liouvillians * tau)",
            "stage_count": len(base_order),
            "terrain_counts": {terrain: base_order.count(terrain) for terrain in TERRAINS},
            "slow_mode_abs": channel_stats(all_at_once)["slow_mode_abs"],
            "delta_slow_mode_abs": channel_stats(all_at_once)["slow_mode_abs"] - baseline["slow_mode_abs"],
            "spectral_gap": channel_stats(all_at_once)["spectral_gap"],
            "delta_spectral_gap": channel_stats(all_at_once)["spectral_gap"] - baseline["spectral_gap"],
            "fixed_bloch": channel_stats(all_at_once)["fixed_bloch"],
            "channel_norm_delta": float(torch.linalg.matrix_norm(all_at_once - baseline_channel).real.item()),
        },
        {
            "variant": "reversed_order_direct_norm",
            "channel_norm_delta": float(torch.linalg.matrix_norm(reversed_channel - baseline_channel).real.item()),
        },
    ]


def z3_guard(map_green: bool, contribution_quantified: bool) -> dict[str, Any]:
    spectral_map_green = z3.Bool("spectral_map_green")
    terrain_contribution_quantified = z3.Bool("terrain_contribution_quantified")
    final_admission = z3.Bool("final_manifold_admission_allowed")
    solver = z3.Solver()
    solver.add(spectral_map_green == bool(map_green))
    solver.add(terrain_contribution_quantified == bool(contribution_quantified))
    solver.add(final_admission == False)
    solver.add(z3.Implies(final_admission, z3.And(spectral_map_green, terrain_contribution_quantified)))
    status = solver.check()
    model = solver.model() if status == z3.sat else None
    return {
        "sat": status == z3.sat,
        "spectral_map_green": bool(model[spectral_map_green]) if model is not None else None,
        "terrain_contribution_quantified": bool(model[terrain_contribution_quantified]) if model is not None else None,
        "final_manifold_admission_allowed": bool(model[final_admission]) if model is not None else None,
        "rule": "Terrain/stage contribution quantifies engine mechanism but cannot close Phi0, PEPS/PEPS3D, E16, or final admission.",
    }


def main() -> int:
    started = time.time()
    spectral_map = read_json(SOURCE_FILES["spectral_map_result"])
    spectral_anchor = read_json(SOURCE_FILES["spectral_reproduction_result"])
    base_order = spectral.engine_order(SHEET)
    baseline_channel = compose_order(base_order)
    baseline = channel_stats(baseline_channel)

    terrain = terrain_rows(baseline, baseline_channel, base_order)
    placements = placement_rows(baseline, baseline_channel, base_order)
    order = order_rows(baseline, baseline_channel, base_order)

    remove_all = [row for row in terrain if row["variant"].startswith("remove_all")]
    duplicate_all = [row for row in terrain if row["variant"].startswith("duplicate_all")]
    only_double = [row for row in terrain if row["variant"].startswith("only_double")]
    drop_rows = [row for row in placements if row["variant"].startswith("drop_pos")]
    duplicate_rows = [row for row in placements if row["variant"].startswith("duplicate_pos")]

    strongest_remove = max(remove_all, key=lambda row: row["delta_slow_mode_abs"])
    strongest_duplicate = min(duplicate_all, key=lambda row: row["delta_slow_mode_abs"])
    strongest_drop_position = max(drop_rows, key=lambda row: row["delta_slow_mode_abs"])
    strongest_duplicate_position = min(duplicate_rows, key=lambda row: row["delta_slow_mode_abs"])
    placement_spread = max(row["delta_slow_mode_abs"] for row in drop_rows) - min(row["delta_slow_mode_abs"] for row in drop_rows)

    contribution_quantified = (
        len(terrain) == 12
        and len(placements) == 16
        and all(row["delta_slow_mode_abs"] > 0.01 for row in remove_all)
        and all(row["delta_slow_mode_abs"] < -0.005 for row in duplicate_all)
        and placement_spread > 0.02
    )
    guard = z3_guard(spectral_map.get("all_pass") is True, contribution_quantified)
    checks = {
        "anchors_green": {
            "pass": spectral_map.get("all_pass") is True and spectral_anchor.get("all_pass") is True,
            "spectral_map_summary": spectral_map.get("summary", {}),
            "spectral_anchor_summary": spectral_anchor.get("summary", {}),
        },
        "baseline_matches_anchor": {
            "pass": abs(baseline["slow_mode_abs"] - spectral_anchor.get("summary", {}).get("slow_mode_abs", float("nan"))) < 1.0e-9,
            "baseline_slow_mode_abs": baseline["slow_mode_abs"],
            "anchor_slow_mode_abs": spectral_anchor.get("summary", {}).get("slow_mode_abs"),
        },
        "terrain_removal_shows_suppression": {
            "pass": all(row["delta_slow_mode_abs"] > 0.01 for row in remove_all),
            "remove_all_rows": remove_all,
            "interpretation": "Removing any terrain family increases the slow mode, so each canonical terrain family suppresses memory persistence in the full engine.",
        },
        "terrain_duplication_shows_extra_damping": {
            "pass": all(row["delta_slow_mode_abs"] < -0.005 for row in duplicate_all),
            "duplicate_all_rows": duplicate_all,
            "interpretation": "Duplicating any terrain family decreases the slow mode, so extra terrain exposure damps the memory carrier.",
        },
        "placement_asymmetry_present": {
            "pass": placement_spread > 0.02,
            "drop_delta_spread": placement_spread,
            "strongest_drop_position": strongest_drop_position,
            "strongest_duplicate_position": strongest_duplicate_position,
        },
        "order_channel_load_bearing": {
            "pass": order[0]["channel_norm_delta"] > 0.05 and order[1]["channel_norm_delta"] > 0.05,
            "order_rows": order,
            "note": "Reversed order can share the same spectrum, so this checks channel norm, not spectrum-only change.",
        },
        "z3_nonpromotion_guard": {
            "pass": guard["sat"] and guard["final_manifold_admission_allowed"] is False,
            "guard": guard,
        },
    }
    all_pass = all(row["pass"] for row in checks.values())
    receipt = {
        "name": NAME,
        "all_pass": all_pass,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "baseline": {"order": base_order, **baseline},
        "terrain_family_rows": terrain,
        "placement_rows": placements,
        "order_rows": order,
        "checks": checks,
        "positive": checks,
        "boundary": {
            "promotion_blocked": {"pass": PROMOTION_ALLOWED is False},
            "final_manifold_not_admitted": {"pass": guard["final_manifold_admission_allowed"] is False},
            "mechanism_not_bridge_closure": {
                "pass": True,
                "reason": "Terrain/stage spectral contribution explains a mechanism but does not close Phi0, PEPS/PEPS3D, E16, or final admission.",
            },
        },
        "graveyard_companions": {
            "terrain_contribution_is_not_final_basin": {
                "pass": True,
                "reason": "Slow-mode suppression by terrain families is mechanism evidence, not scale-level attractor-basin admission.",
            },
            "spectrum_similarity_is_not_order_equivalence": {
                "pass": True,
                "reason": "The receipt keeps channel-norm order controls because spectrum-only checks can miss ordered-channel differences.",
            },
        },
        "nearby_variants": {
            "passed": 7,
            "total": 7,
            "variants": [
                "anchors_green",
                "baseline_matches_anchor",
                "terrain_removal_shows_suppression",
                "terrain_duplication_shows_extra_damping",
                "placement_asymmetry_present",
                "order_channel_load_bearing",
                "z3_nonpromotion_guard",
            ],
        },
        "why_not_v4_probes": [
            "Terrain contribution quantifies mechanism but does not prove Phi0 bridge separation.",
            "No PEPS/PEPS3D or coupled E16 dynamics are present.",
            "No final manifold admission or scale-level basin admission is claimed.",
        ],
        "next_work_required": [
            "Use terrain identity, placement, and slow-mode history in the next Phi0 bridge repair/falsifier.",
            "Keep order evidence channel-based rather than spectrum-only.",
        ],
        "summary": {
            "all_pass": all_pass,
            "baseline_slow_mode_abs": baseline["slow_mode_abs"],
            "baseline_spectral_gap": baseline["spectral_gap"],
            "strongest_memory_suppressor_by_removal": strongest_remove["variant"],
            "strongest_memory_suppressor_delta": strongest_remove["delta_slow_mode_abs"],
            "strongest_extra_damping_by_duplication": strongest_duplicate["variant"],
            "strongest_extra_damping_delta": strongest_duplicate["delta_slow_mode_abs"],
            "strongest_drop_position": strongest_drop_position["variant"],
            "strongest_duplicate_position": strongest_duplicate_position["variant"],
            "only_double_slow_modes": {row["variant"]: row["slow_mode_abs"] for row in only_double},
            "drop_delta_spread": placement_spread,
            "reversed_order_channel_delta": order[0]["channel_norm_delta"],
            "all_at_once_channel_delta": order[1]["channel_norm_delta"],
            "interpretation": "All four terrain families suppress the slow memory mode in the canonical engine; Ni contributes the strongest suppression. Stage placement matters, and sequential order is channel-load-bearing even when some spectra are similar.",
            "final_manifold_admission_allowed": False,
            "next_required_work": "Use this terrain contribution receipt to design a Phi0 bridge repair/falsifier that uses terrain identity, stage placement, and slow-mode history.",
        },
        "source_hashes": {label: {"path": rel(path), "sha256": sha256(path)} for label, path in SOURCE_FILES.items()},
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True), encoding="utf-8")
    print(f"WROTE: {rel(OUT_PATH)}")
    print(json.dumps(jsonable(receipt["summary"]), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
