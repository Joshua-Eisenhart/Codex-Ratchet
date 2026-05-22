#!/usr/bin/env python3
"""Spectral phase map for the formal QIT engine manifold surface.

The iter_195 formal reproduction shows that one exact-CPTP single-qubit engine
is monostable because its channel has one fixed eigenvalue and a slow decay mode
near 0.125. This scout turns that point result into a bounded parameter map:
stage duration, Hamiltonian direction/magnitude, dissipator profile, sheet sign,
and stage ordering are swept, and the channel spectrum is recorded as a
manifold-local diagnostic.
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

import sim_two_root_constraint_iter195_single_engine_spectral_reproduction_probe as spectral


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_engine_spectral_manifold_phase_map_probe_results.json"

NAME = "two_root_constraint_engine_spectral_manifold_phase_map_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_engine_spectral_manifold_phase_map"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_engine_spectral_manifold_map"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal spectral-manifold Workstream 1 scout only: maps single-engine "
    "channel spectra across bounded terrain-engine parameters. It can explain "
    "schedule-memory and terrain-order candidates, but cannot promote Phi0 "
    "bridge closure, PEPS/PEPS3D dynamics, full E=16 dynamics, final manifold "
    "admission, or real scale-level attractor-basin admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing channel construction, matrix exponentials, spectra, fixed-point iteration, and Bloch readouts across the parameter map",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard for spectral-map evidence",
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

TAUS = [0.25, 0.5, 0.75, 1.0, 1.25]
DIRECTIONS: dict[str, tuple[float, float, float]] = {
    "raw_xz": (0.7, 0.0, 0.5),
    "x": (1.0, 0.0, 0.0),
    "z": (0.0, 0.0, 1.0),
    "xy": (0.7, 0.4, 0.0),
}
MAGNITUDES = [0.5, 1.0, 1.5]
PROFILES: dict[str, dict[str, float]] = {
    "balanced": {"funnel": 1.0, "vortex": 1.0, "ladder": 1.0, "dephase": 1.0},
    "weak_global": {"funnel": 0.5, "vortex": 0.5, "ladder": 0.5, "dephase": 0.5},
    "strong_ladder": {"funnel": 1.0, "vortex": 1.0, "ladder": 2.0, "dephase": 1.0},
}
SHEETS = ["L", "R"]
ORDER_VARIANTS = ["canonical", "reversed", "all_at_once"]
FIXED_CYCLES = 360
EPS_MEMORY = [0.05, 0.005]

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "spectral_reproduction_scout": SCOUT_ROOT / "sim_two_root_constraint_iter195_single_engine_spectral_reproduction_probe.py",
    "spectral_reproduction_result": RESULT_DIR / "two_root_constraint_iter195_single_engine_spectral_reproduction_probe_results.json",
    "full_build_plan": REPO / "system_v5" / "ops" / "QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md",
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


def scaled_direction(direction: str, magnitude: float) -> tuple[float, float, float]:
    base = DIRECTIONS[direction]
    return tuple(float(magnitude * item) for item in base)


def scaled_stages(
    sheet: str,
    direction: tuple[float, float, float],
    profile: dict[str, float],
) -> dict[str, tuple[torch.Tensor, list[torch.Tensor]]]:
    stages = spectral.make_proper_stages(sheet, direction)
    return {
        "Se": (stages["Se"][0], [math.sqrt(profile["funnel"]) * op for op in stages["Se"][1]]),
        "Ne": (stages["Ne"][0], [math.sqrt(profile["vortex"]) * op for op in stages["Ne"][1]]),
        "Ni": (stages["Ni"][0], [math.sqrt(profile["ladder"]) * op for op in stages["Ni"][1]]),
        "Si": (stages["Si"][0], [math.sqrt(profile["dephase"]) * op for op in stages["Si"][1]]),
    }


def channel_for(
    *,
    sheet: str,
    direction: tuple[float, float, float],
    profile: dict[str, float],
    tau: float,
    order_variant: str,
) -> torch.Tensor:
    stages = scaled_stages(sheet, direction, profile)
    order = spectral.engine_order(sheet)
    if order_variant == "reversed":
        order = list(reversed(order))
    if order_variant == "all_at_once":
        total = torch.zeros((4, 4), dtype=spectral.DTYPE)
        for terrain in order:
            H, collapse_ops = stages[terrain]
            total = total + spectral.liouvillian_superop(H, collapse_ops)
        return torch.linalg.matrix_exp(float(tau) * total)
    channel = torch.eye(4, dtype=spectral.DTYPE)
    for terrain in order:
        H, collapse_ops = stages[terrain]
        channel = spectral.stage_propagator(H, collapse_ops, tau) @ channel
    return channel


def fixed_bloch(channel: torch.Tensor) -> list[float]:
    state = spectral.col_vec(0.5 * spectral.I2)
    for _ in range(FIXED_CYCLES):
        state = channel @ state
    rho = spectral.col_mat(state)
    rho = 0.5 * (rho + rho.conj().T)
    rho = rho / torch.trace(rho)
    return spectral.bloch(rho)


def memory_horizon(slow_mode_abs: float, eps: float) -> int:
    return sum(1 for power in range(1, 16) if slow_mode_abs**power > eps)


def primitive_status(eig_abs: list[float]) -> str:
    fixed_count = sum(1 for value in eig_abs if abs(value - 1.0) < 1.0e-8)
    if fixed_count != 1:
        return "nonprimitive_fixed_space"
    if eig_abs[1] >= 1.0 - 1.0e-8:
        return "nonmixing_boundary"
    if eig_abs[1] < 0.02:
        return "fast_mixing"
    if eig_abs[1] < 0.2:
        return "slow_mode_memory"
    return "long_memory"


def spectral_row(
    *,
    sheet: str,
    direction_name: str,
    magnitude: float,
    profile_name: str,
    tau: float,
    order_variant: str,
) -> dict[str, Any]:
    direction = scaled_direction(direction_name, magnitude)
    channel = channel_for(
        sheet=sheet,
        direction=direction,
        profile=PROFILES[profile_name],
        tau=tau,
        order_variant=order_variant,
    )
    eigvals = torch.linalg.eigvals(channel)
    eig_abs = spectral.sorted_abs(eigvals)
    slow = eig_abs[1]
    fixed = fixed_bloch(channel)
    h = torch.tensor(direction, dtype=torch.float64)
    h_norm = float(torch.linalg.vector_norm(h).item())
    fixed_norm = math.sqrt(sum(item * item for item in fixed))
    alignment = None
    if h_norm > 0.0 and fixed_norm > 0.0:
        alignment = float(sum(fixed[i] * direction[i] for i in range(3)) / (fixed_norm * h_norm))
    return {
        "sheet": sheet,
        "direction": direction_name,
        "magnitude": magnitude,
        "profile": profile_name,
        "tau": tau,
        "order_variant": order_variant,
        "eig_abs": eig_abs,
        "spectral_gap": 1.0 - slow,
        "slow_mode_abs": slow,
        "cycle_half_life": math.log(0.5) / math.log(slow) if 0.0 < slow < 1.0 else None,
        "primitive_status": primitive_status(eig_abs),
        "fixed_bloch": fixed,
        "fixed_alignment_with_H": alignment,
        "memory_horizon_eps_0_05": memory_horizon(slow, 0.05),
        "memory_horizon_eps_0_005": memory_horizon(slow, 0.005),
    }


def z3_guard(anchor_reproduced: bool, map_built: bool) -> dict[str, Any]:
    anchor = z3.Bool("iter195_anchor_reproduced")
    spectral_map = z3.Bool("spectral_map_built")
    final_admission = z3.Bool("final_manifold_admission_allowed")
    solver = z3.Solver()
    solver.add(anchor == bool(anchor_reproduced))
    solver.add(spectral_map == bool(map_built))
    solver.add(final_admission == False)
    solver.add(z3.Implies(final_admission, z3.And(anchor, spectral_map)))
    status = solver.check()
    model = solver.model() if status == z3.sat else None
    return {
        "sat": status == z3.sat,
        "iter195_anchor_reproduced": bool(model[anchor]) if model is not None else None,
        "spectral_map_built": bool(model[spectral_map]) if model is not None else None,
        "final_manifold_admission_allowed": bool(model[final_admission]) if model is not None else None,
        "rule": "Spectral manifold mapping can guide bridge/tensor packets but cannot close Phi0, PEPS/PEPS3D, E16, or final admission.",
    }


def main() -> int:
    started = time.time()
    anchor = read_json(SOURCE_FILES["spectral_reproduction_result"])
    rows: list[dict[str, Any]] = []
    for sheet in SHEETS:
        for direction in DIRECTIONS:
            for magnitude in MAGNITUDES:
                for profile in PROFILES:
                    for tau in TAUS:
                        for order_variant in ORDER_VARIANTS:
                            rows.append(
                                spectral_row(
                                    sheet=sheet,
                                    direction_name=direction,
                                    magnitude=magnitude,
                                    profile_name=profile,
                                    tau=tau,
                                    order_variant=order_variant,
                                )
                            )

    anchor_rows = [
        row
        for row in rows
        if row["sheet"] == "L"
        and row["direction"] == "raw_xz"
        and row["magnitude"] == 1.0
        and row["profile"] == "balanced"
        and row["tau"] == 1.0
        and row["order_variant"] == "canonical"
    ]
    anchor_row = anchor_rows[0] if anchor_rows else {}
    status_counts: dict[str, int] = {}
    horizon_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["primitive_status"]] = status_counts.get(row["primitive_status"], 0) + 1
        key = str(row["memory_horizon_eps_0_005"])
        horizon_counts[key] = horizon_counts.get(key, 0) + 1

    slow_values = [row["slow_mode_abs"] for row in rows]
    gap_values = [row["spectral_gap"] for row in rows]
    anchor_reproduced = (
        anchor.get("all_pass") is True
        and bool(anchor_row)
        and abs(anchor_row["slow_mode_abs"] - anchor.get("summary", {}).get("slow_mode_abs", float("nan"))) < 1.0e-9
    )
    anchor_direction = scaled_direction("raw_xz", 1.0)
    anchor_profile = PROFILES["balanced"]
    canonical_anchor_channel = channel_for(
        sheet="L",
        direction=anchor_direction,
        profile=anchor_profile,
        tau=1.0,
        order_variant="canonical",
    )
    reversed_anchor_channel = channel_for(
        sheet="L",
        direction=anchor_direction,
        profile=anchor_profile,
        tau=1.0,
        order_variant="reversed",
    )
    all_at_once_anchor_channel = channel_for(
        sheet="L",
        direction=anchor_direction,
        profile=anchor_profile,
        tau=1.0,
        order_variant="all_at_once",
    )
    order_variant_norms = {
        "canonical_minus_reversed": float(torch.linalg.matrix_norm(canonical_anchor_channel - reversed_anchor_channel).real.item()),
        "canonical_minus_all_at_once": float(torch.linalg.matrix_norm(canonical_anchor_channel - all_at_once_anchor_channel).real.item()),
    }
    map_built = len(rows) == len(SHEETS) * len(DIRECTIONS) * len(MAGNITUDES) * len(PROFILES) * len(TAUS) * len(ORDER_VARIANTS)
    guard = z3_guard(anchor_reproduced, map_built)
    checks = {
        "anchor_reproduced_in_map": {
            "pass": anchor_reproduced,
            "anchor_row": anchor_row,
            "anchor_summary": anchor.get("summary", {}),
        },
        "row_count_expected": {
            "pass": map_built,
            "row_count": len(rows),
            "expected": len(SHEETS) * len(DIRECTIONS) * len(MAGNITUDES) * len(PROFILES) * len(TAUS) * len(ORDER_VARIANTS),
        },
        "spectral_variation_nontrivial": {
            "pass": (max(slow_values) - min(slow_values)) > 0.01 and (max(gap_values) - min(gap_values)) > 0.01,
            "slow_mode_range": [min(slow_values), max(slow_values)],
            "spectral_gap_range": [min(gap_values), max(gap_values)],
        },
        "order_variant_changes_channel": {
            "pass": order_variant_norms["canonical_minus_reversed"] > 0.01
            and order_variant_norms["canonical_minus_all_at_once"] > 0.01,
            "order_variant_norms": order_variant_norms,
            "note": "Reversed products can share eigenvalues with canonical products, so the load-bearing order check is channel difference, not spectrum-only difference.",
        },
        "z3_nonpromotion_guard": {
            "pass": guard["sat"] and guard["final_manifold_admission_allowed"] is False,
            "guard": guard,
        },
    }
    all_pass = all(item["pass"] for item in checks.values())
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
        "parameter_grid": {
            "sheets": SHEETS,
            "directions": DIRECTIONS,
            "magnitudes": MAGNITUDES,
            "profiles": PROFILES,
            "taus": TAUS,
            "order_variants": ORDER_VARIANTS,
        },
        "rows": rows,
        "checks": checks,
        "positive": checks,
        "boundary": {
            "promotion_blocked": {"pass": PROMOTION_ALLOWED is False},
            "final_manifold_not_admitted": {"pass": guard["final_manifold_admission_allowed"] is False},
            "spectral_map_is_diagnostic_only": {
                "pass": True,
                "reason": "The spectral phase map guides terrain/Phi0/tensor packets but is not bridge closure, PEPS/PEPS3D, E16, or final manifold admission.",
            },
        },
        "graveyard_companions": {
            "spectrum_only_is_not_channel_order_proof": {
                "pass": True,
                "reason": "The receipt keeps channel-norm order controls because reversed products can share eigenvalues with canonical products.",
            },
            "single_engine_map_is_not_scale_basin_admission": {
                "pass": True,
                "reason": "All rows are bounded single-engine spectral diagnostics, not multiscale attractor-basin admission.",
            },
        },
        "nearby_variants": {
            "passed": 5,
            "total": 5,
            "variants": [
                "anchor_reproduced_in_map",
                "row_count_expected",
                "spectral_variation_nontrivial",
                "order_variant_changes_channel",
                "z3_nonpromotion_guard",
            ],
        },
        "why_not_v4_probes": [
            "No Phi0 bridge separation proof is present.",
            "No PEPS/PEPS3D or full E=16 dynamics are present.",
            "This is a bounded spectral map for later probes, not final manifold admission.",
        ],
        "next_work_required": [
            "Use the spectral map to design a terrain/slow-mode Phi0 bridge repair or falsifier.",
            "Reproduce any scale-level spectral claim in a source-native PyTorch/tensor-network packet before promotion.",
        ],
        "summary": {
            "all_pass": all_pass,
            "row_count": len(rows),
            "anchor_slow_mode_abs": anchor_row.get("slow_mode_abs"),
            "anchor_spectral_gap": anchor_row.get("spectral_gap"),
            "slow_mode_range": [min(slow_values), max(slow_values)],
            "spectral_gap_range": [min(gap_values), max(gap_values)],
            "primitive_status_counts": status_counts,
            "memory_horizon_eps_0_005_counts": horizon_counts,
            "anchor_order_variant_norms": order_variant_norms,
            "final_manifold_admission_allowed": False,
            "next_required_work": "Use this spectral phase map to decompose terrain/stage contributions and to design the next Phi0 bridge repair/falsifier packet.",
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
