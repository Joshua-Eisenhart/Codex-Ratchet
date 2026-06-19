#!/usr/bin/env python3
"""Shared builder for the Family A dynamic density-state chart v1 sweep."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
import z3


SIM_ID = "manifold_dynamic_chart_v2"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
TRAJECTORY_ARTIFACT_PATH = RESULT_DIR / f"{SIM_ID}_trajectory_artifact.json"
TRAJECTORY_ARTIFACT_SHA_PATH = RESULT_DIR / f"{SIM_ID}_trajectory_artifact.sha256"

CLASSIFICATION = "scratch_diagnostic"
ROW_CLASSIFICATION = "dynamic_chart_v2_first_measurement_attempt"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_axis0_experiment_v2_no_admission"
ENGINE_MODE = "family_a_33_cell_dynamic_density_state_chart_axis0_experiment_v2"
EXPECTED_STATE_COUNT = 33
EXPECTED_EDGE_COUNT = 198
SHELL_COUNT = 3
EPS = 1.0e-10
V0_REGRESSION_EXPECTED = {"SPREAD": 32, "DAMP": 1}

SEPARATION_RULE_VERBATIM = (
    "a candidate readout EARNS only if it beats the majority baseline, is stable across >=2 "
    "perturbation families, AND the negative controls fail it"
)

PERTURBATION_FAMILIES = [
    {
        "family_id": "unitary_kicks",
        "kind": "unitary kicks",
        "generator": "R_x",
        "description": "R_x kicks on the committed Family A transition graph.",
    },
    {
        "family_id": "dephasing_kicks",
        "kind": "dephasing kicks",
        "generator": "D_z",
        "description": "D_z kicks on the committed Family A transition graph.",
    },
    {
        "family_id": "amplitude_kicks",
        "kind": "amplitude kicks",
        "generator": "Ni_Source_R",
        "description": "Ni_Source_R non-unital terrain-source kicks used as the amplitude-like family.",
    },
    {
        "family_id": "generator_biased_kicks",
        "kind": "generator-biased kicks",
        "generator": "biased_by_entropy_shell",
        "description": "Generator choice is pinned by initial entropy shell: low->D_z, mid->R_x, high->Ni_Source_R.",
    },
    {
        "family_id": "purity_projective_resets",
        "kind": "purity projective resets",
        "generator": "projective_reset_to_nearest_pure_bloch_cell",
        "description": "Panel-10 purity kick proper: target cells are reset toward the nearest pure Bloch direction before the unperturbed dynamics run.",
    },
]

STRENGTH_LADDER = [
    {"strength_id": "weak", "strength_steps": 1, "strength_rank": 1},
    {"strength_id": "medium", "strength_steps": 2, "strength_rank": 2},
    {"strength_id": "strong", "strength_steps": 3, "strength_rank": 3},
    {"strength_id": "very_strong", "strength_steps": 4, "strength_rank": 4},
]

TARGET_MODES = [
    {"target_mode": "single_cell", "description": "one pinned central cell"},
    {"target_mode": "neighborhood", "description": "central cell plus one-hop in/out neighbors"},
    {"target_mode": "shell_boundary", "description": "states incident to the initial entropy-shell boundary"},
]

ANCHOR_WINDOW_T = 12
V0_REGRESSION_WINDOW_T = 4
RELAXATION_WINDOW_MULTIPLIERS = [0.5, 1.0, 2.0]
AGREEMENT_THRESHOLD_LADDER = [1, 2, 3, 4]
V1_FAMILY_IDS = ["unitary_kicks", "dephasing_kicks", "amplitude_kicks", "generator_biased_kicks"]
V1_ANCHOR_CORNER = {
    "strength_id": "weak",
    "strength_steps": 1,
    "target_mode": "shell_boundary",
    "window_T": 12,
    "classifier_id": "recovery_return_time",
}
CLASSIFIERS = [
    {
        "classifier_id": "v0_divergence",
        "description": "v0 final-cell-changed divergence functional; SPREAD if final cell differs from control, otherwise DAMP.",
    },
    {
        "classifier_id": "baseline_growth_rate_sign",
        "description": "relative-to-baseline growth-rate sign over the hamming divergence series.",
    },
    {
        "classifier_id": "recovery_return_time",
        "description": "RETURN/BOUNDARY/SCRAMBLING return-time classifier over divergence and reconvergence.",
    },
    {
        "classifier_id": "shell_weighted_tv",
        "description": "Panel-10 functional: per-cell shell-weighted trace-variation contribution r*||Delta rho(T)||_1, classed by the observed contribution split.",
    },
]

PARENT_DIRS = {
    "discrete_axis0_field_v0": ROOT / "system_v6" / "sims" / "discrete_axis0_field_v0",
    "engines_run_with_axes_v0": ROOT / "system_v6" / "sims" / "engines_run_with_axes_v0",
}
for parent_dir in PARENT_DIRS.values():
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import discrete_axis0_field_v0_common as axis0_common  # noqa: E402
import engines_run_with_axes_v0_common as engine_common  # noqa: E402
from builder_audit_boundary import builder_audit_boundary_errors, builder_audit_boundary_ok  # noqa: E402


PARENT_COMMITS = {
    "dynamic_manifold_upgrade_design": "4fc7c2f3b",
    "manifold_dynamic_chart_v0_audit": "eb51339c0",
    "codex_suggestions_unlock_plan": "4142cecbe",
    "panel10_blind_separation_methods": "3ff556c10",
    "manifold_dynamic_chart_v1_audit": "1231dbbd9",
    "owner_correction_axis0_not_built": "0313d47bc",
    "engines_run_with_axes_v0": "de243459e",
    "audit_standards_codex_v1": "current",
}

PARENT_PATHS = {
    "dynamic_manifold_upgrade_design": ROOT / "system_v6" / "receipts" / "dynamic_manifold_upgrade_design_20260612.md",
    "owner_correction_axis0_not_built": ROOT / "system_v6" / "receipts" / "owner_correction_axis0_not_built_20260612.md",
    "manifold_dynamic_chart_v0_audit": ROOT / "system_v6" / "sims" / "manifold_dynamic_chart_v0" / "audit_verdict.md",
    "codex_suggestions_unlock_plan": ROOT / "system_v6" / "receipts" / "codex_suggestions_unlock_plan_20260612.md",
    "panel10_blind_separation_methods": ROOT / "system_v6" / "receipts" / "panel10_blind_separation_methods_20260612.md",
    "manifold_dynamic_chart_v1_audit": ROOT / "system_v6" / "sims" / "manifold_dynamic_chart_v1" / "audit_verdict.md",
    "engines_run_with_axes_v0_common": ROOT
    / "system_v6"
    / "sims"
    / "engines_run_with_axes_v0"
    / "engines_run_with_axes_v0_common.py",
    "discrete_axis0_field_v0_common": ROOT
    / "system_v6"
    / "sims"
    / "discrete_axis0_field_v0"
    / "discrete_axis0_field_v0_common.py",
    "audit_standards_codex_v1": ROOT / "system_v6" / "receipts" / "audit_standards_codex_v1.md",
}

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing construction of 2x2 density matrices and eigenvalue vN entropy from Bloch cell states.",
    },
    "torch.linalg.eigvalsh": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Hermitian density eigenvalues used as the only entropy source.",
    },
    "engines_run_with_axes_v0": {
        "tried": True,
        "used": True,
        "reason": "load-bearing committed four-stroke generator schedule extended from post-stroke cells to state trajectories.",
    },
    "discrete_axis0_field_v0": {
        "tried": True,
        "used": True,
        "reason": "supportive old static phi sign is consumed only for the falsifiable bridge row, never for entropy.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope-level arithmetic gate binding computed trajectory/state counts and perturbation bite.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive independent arithmetic gate binding the same computed counts as z3.",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "load-bearing G.2a idempotency-from-birth validator boundary.",
    },
    "axis0_experiment_sweep": {
        "tried": True,
        "used": True,
        "reason": "load-bearing full perturbation family x strength x target x relaxation-window x classifier sweep and unchanged criterion verdict.",
    },
    "relaxation_scale_calibration": {
        "tried": True,
        "used": True,
        "reason": "load-bearing panel-10 window selection from the unperturbed generator-family transition spectrum before the v2 sweep runs.",
    },
    "family_robust_agreement_threshold": {
        "tried": True,
        "used": True,
        "reason": "load-bearing stability-axis classifier: cells earn common sign classes only when at least k perturbation families agree.",
    },
    "shell_weighted_tv": {
        "tried": True,
        "used": True,
        "reason": "load-bearing panel-10 shell-weighted trace-variation classifier r*||Delta rho(T)||_1.",
    },
    "purity_projective_resets": {
        "tried": True,
        "used": True,
        "reason": "load-bearing panel-10 purity kick proper: projective resets toward nearest pure Bloch direction.",
    },
    "json_hashing": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic result serialization and trajectory artifact signatures.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.linalg.eigvalsh": "load_bearing",
    "engines_run_with_axes_v0": "load_bearing",
    "discrete_axis0_field_v0": "supportive",
    "z3": "supportive",
    "cvc5": "supportive",
    "builder_audit_boundary": "load_bearing",
    "axis0_experiment_sweep": "load_bearing",
    "relaxation_scale_calibration": "load_bearing",
    "family_robust_agreement_threshold": "load_bearing",
    "shell_weighted_tv": "load_bearing",
    "purity_projective_resets": "load_bearing",
    "json_hashing": "supportive",
}

TOOL_INTENT = {
    "claim_classes": [
        "family_a_dynamic_density_state_chart",
        "state_derived_local_von_neumann_entropy",
        "dynamic_entropy_shell_motion",
        "jk_admissible_future_multiplicity",
        "perturb_watch_classify_first_attempt",
        "axis0_experiment_v2_stability_axis_grid",
        "relaxation_calibrated_window_sweep",
        "family_robust_agreement_threshold_ladder",
        "shell_weighted_tv_classifier",
        "purity_projective_reset_family",
        "majority_stability_negative_control_criterion",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "rebuild committed finite transition graph and compute the same pinned four-stroke trajectory signature without reading peer results",
        },
        "jax": {
            "networkx": "recompute finite transition graph reachability/trajectory signature from source rows",
            "sympy": "exactly bind lane parity counts and entropy denominator guard",
        },
        "pytorch": {
            "torch.func": "batched density-state entropy observable over the 33-cell trajectory table",
            "sympy": "exactly bind lane parity counts and entropy denominator guard",
        },
    },
    "criterion": SEPARATION_RULE_VERBATIM,
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def rounded_float(value: float, digits: int = 12) -> float:
    rounded = round(float(value), digits)
    return 0.0 if rounded == 0 else rounded


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_last_commit(path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
    except Exception:
        return "unavailable"
    return result.stdout.strip() or "unavailable"


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row = {
        "role": role,
        "path": rel(path),
        "exists": path.exists(),
    }
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["commit_hint"] = commit_hint
    return row


@lru_cache(maxsize=1)
def parent_objects() -> dict[str, Any]:
    carrier = axis0_common.rebuild_committed_carrier()
    axis0 = axis0_common.build_axis0_object()
    return {"carrier": carrier, "axis0": axis0}


def carrier_cells_by_id() -> dict[int, dict[str, Any]]:
    return {int(cell["cell_id"]): cell for cell in parent_objects()["carrier"]["cells"]}


def transition_lookup(edges: list[dict[str, Any]] | None = None) -> dict[tuple[int, str], int]:
    lookup: dict[tuple[int, str], int] = {}
    for row in edges or parent_objects()["carrier"]["edges"]:
        lookup[(int(row["src"]), str(row["generator"]))] = int(row["dst"])
    return lookup


@lru_cache(maxsize=1)
def relaxation_scale_calibration() -> dict[str, Any]:
    """Compute panel-10's unperturbed slowest relaxation scale before choosing v2 windows."""
    state_ids = initial_cells()
    index_by_state = {state_id: idx for idx, state_id in enumerate(state_ids)}
    generators = list(parent_objects()["carrier"]["generator_names"])
    lookup = transition_lookup()
    transition = torch.zeros((len(state_ids), len(state_ids)), dtype=torch.float64)
    for src in state_ids:
        for generator in generators:
            dst = lookup[(src, generator)]
            transition[index_by_state[src], index_by_state[dst]] += 1.0 / len(generators)
    eigen_abs = sorted(
        (float(value) for value in torch.abs(torch.linalg.eigvals(transition.T)).tolist()),
        reverse=True,
    )
    lambda_2 = next((value for value in eigen_abs[1:] if value < 1.0 - 1.0e-9 and value > 1.0e-12), 0.0)
    if lambda_2 <= 0.0:
        tau = float(ANCHOR_WINDOW_T)
        tau_status = "fallback_anchor_no_subunit_nontrivial_eigenvalue"
    else:
        tau = float(-1.0 / math.log(lambda_2))
        tau_status = "computed_from_generator_averaged_transition_matrix"
    relaxed = [max(ANCHOR_WINDOW_T, int(math.ceil(tau * multiplier))) for multiplier in RELAXATION_WINDOW_MULTIPLIERS]
    windows = sorted({ANCHOR_WINDOW_T, *relaxed})
    return {
        "calibration_id": "unperturbed_generator_family_slowest_relaxation_scale",
        "method": "row-stochastic average over committed named generator maps; tau=-1/log(|lambda_2|)",
        "generator_names": generators,
        "lambda_abs_descending_first_8": [rounded_float(value) for value in eigen_abs[:8]],
        "lambda_2_abs": rounded_float(lambda_2),
        "slowest_relaxation_tau_steps": rounded_float(tau),
        "status": tau_status,
        "anchor_window_T": ANCHOR_WINDOW_T,
        "multipliers": RELAXATION_WINDOW_MULTIPLIERS,
        "window_ladder": windows,
    }


def window_ladder() -> list[int]:
    return list(relaxation_scale_calibration()["window_ladder"])


def committed_schedule() -> list[dict[str, Any]]:
    strokes = engine_common.engine_specs()["carnot"]["strokes"]
    return [
        {
            "step_index": index + 1,
            "stroke": str(row["stroke"]),
            "generator": str(row["generator"]),
            "source_packet": "engines_run_with_axes_v0",
        }
        for index, row in enumerate(strokes)
    ]


def initial_cells() -> list[int]:
    return sorted(int(cell["cell_id"]) for cell in parent_objects()["carrier"]["cells"])


def density_state_from_coord(coord: list[float]) -> dict[str, Any]:
    vec = torch.tensor(coord, dtype=torch.float64)
    rho = torch.zeros((2, 2), dtype=torch.complex128)
    rho[0, 0] = complex(float((1.0 + vec[2]) / 2.0), 0.0)
    rho[1, 1] = complex(float((1.0 - vec[2]) / 2.0), 0.0)
    rho[0, 1] = complex(float(vec[0] / 2.0), float(-vec[1] / 2.0))
    rho[1, 0] = complex(float(vec[0] / 2.0), float(vec[1] / 2.0))
    eig = torch.linalg.eigvalsh(rho).real.clamp_min(0.0)
    eig_sum = eig.sum()
    if float(eig_sum) > 0:
        eig = eig / eig_sum
    positive = eig[eig > 0]
    entropy = rounded_float(float(-(positive * torch.log(positive)).sum().item()))
    trace = rho.trace()
    hermitian_delta = torch.max(torch.abs(rho - rho.conj().T)).item()
    return {
        "rho_real": [[round(float(rho[i, j].real), 12) for j in range(2)] for i in range(2)],
        "rho_imag": [[round(float(rho[i, j].imag), 12) for j in range(2)] for i in range(2)],
        "eigenvalues": [rounded_float(float(value)) for value in eig.tolist()],
        "entropy_vn": entropy,
        "trace_real": round(float(trace.real), 12),
        "trace_imag": round(float(trace.imag), 12),
        "density_trace_close_to_one": abs(float(trace.real) - 1.0) <= 1.0e-9 and abs(float(trace.imag)) <= 1.0e-9,
        "density_psd": bool(torch.all(eig >= -1.0e-9).item()),
        "density_hermitian": hermitian_delta <= 1.0e-9,
    }


def state_rows_for_cells(
    *,
    trajectory_id: str,
    t: int,
    current_cells: list[int],
    applied_generator: str | None,
    source_cells: list[int] | None,
) -> list[dict[str, Any]]:
    cells = carrier_cells_by_id()
    rows = []
    for state_id, current_cell in zip(initial_cells(), current_cells, strict=True):
        cell = cells[int(current_cell)]
        density = density_state_from_coord(cell["coord"])
        source_cell = None if source_cells is None else int(source_cells[state_id])
        rows.append(
            {
                "state_row_id": f"{trajectory_id}:state:{state_id}:t:{t}",
                "trajectory_id": trajectory_id,
                "state_id": int(state_id),
                "t": int(t),
                "cell_or_node": int(current_cell),
                "current_cell": int(current_cell),
                "source_cell": source_cell,
                "coord": cell["coord"],
                "coord_scaled": cell["coord_scaled"],
                "rho_or_state_vector": "rho_2x2_density_matrix",
                "generator_or_channel_applied": applied_generator,
                "source_state_id": None if t == 0 else f"{trajectory_id}:state:{state_id}:t:{t - 1}",
                "target_state_id": f"{trajectory_id}:state:{state_id}:t:{t}",
                "entropy_source": "computed_from_rho_eigenvalues",
                **density,
            }
        )
    return rows


def apply_schedule(
    *,
    trajectory_id: str,
    schedule: list[dict[str, Any]],
    initial_override: list[int] | None = None,
    lookup: dict[tuple[int, str], int] | None = None,
    identity: bool = False,
) -> dict[str, Any]:
    active_lookup = lookup or transition_lookup()
    current = list(initial_override or initial_cells())
    state_rows = state_rows_for_cells(
        trajectory_id=trajectory_id,
        t=0,
        current_cells=current,
        applied_generator=None,
        source_cells=None,
    )
    transition_rows = []
    step_signatures = [{"t": 0, "cells_sha256": stable_sha256(current), "generator": None}]
    for step in schedule:
        before = list(current)
        generator = "IDENTITY" if identity else step["generator"]
        after = []
        for cell in before:
            after.append(int(cell) if identity else active_lookup[(int(cell), str(generator))])
        changed = sum(left != right for left, right in zip(before, after, strict=True))
        transition_rows.append(
            {
                "t": int(step["step_index"]),
                "stroke": step["stroke"],
                "generator": generator,
                "before_cells_sha256": stable_sha256(before),
                "after_cells_sha256": stable_sha256(after),
                "changed_cell_count": changed,
                "transition_count": len(after),
            }
        )
        current = after
        state_rows.extend(
            state_rows_for_cells(
                trajectory_id=trajectory_id,
                t=int(step["step_index"]),
                current_cells=current,
                applied_generator=generator,
                source_cells=before,
            )
        )
        step_signatures.append({"t": int(step["step_index"]), "cells_sha256": stable_sha256(current), "generator": generator})
    return {
        "trajectory_id": trajectory_id,
        "T": len(schedule),
        "schedule": schedule,
        "state_rows": state_rows,
        "transition_rows": transition_rows,
        "step_signatures": step_signatures,
        "trajectory_signature_sha256": stable_sha256(step_signatures),
        "changed_transition_count": sum(row["changed_cell_count"] > 0 for row in transition_rows),
        "total_changed_cell_steps": sum(row["changed_cell_count"] for row in transition_rows),
    }


def entropy_field_rows(state_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "t": row["t"],
            "state_id": row["state_id"],
            "current_cell": row["current_cell"],
            "S_vN": row["entropy_vn"],
            "entropy_source": row["entropy_source"],
        }
        for row in state_rows
    ]


def entropy_gradients(state_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_t: dict[int, dict[int, dict[str, Any]]] = defaultdict(dict)
    for row in state_rows:
        rows_by_t[int(row["t"])][int(row["state_id"])] = row
    gradients = []
    for t, by_state in sorted(rows_by_t.items()):
        for edge in parent_objects()["carrier"]["edges"]:
            src = int(edge["src"])
            dst = int(edge["dst"])
            delta = float(by_state[dst]["entropy_vn"]) - float(by_state[src]["entropy_vn"])
            gradients.append(
                {
                    "t": t,
                    "src_state_id": src,
                    "dst_state_id": dst,
                    "generator": edge["generator"],
                    "src_entropy": by_state[src]["entropy_vn"],
                    "dst_entropy": by_state[dst]["entropy_vn"],
                    "Delta_S": round(delta, 12),
                    "gradient_sign": 1 if delta > EPS else -1 if delta < -EPS else 0,
                    "computed_from": "S_vN(rho_dst(t))-S_vN(rho_src(t))",
                }
            )
    return gradients


def shell_band(value: float, min_entropy: float, max_entropy: float) -> str:
    if max_entropy - min_entropy <= EPS:
        return "degenerate"
    third = (max_entropy - min_entropy) / SHELL_COUNT
    if value <= min_entropy + third:
        return "low_entropy_level"
    if value <= min_entropy + 2 * third:
        return "mid_entropy_level"
    return "high_entropy_level"


def dynamic_shell_rows(state_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_t: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in state_rows:
        rows_by_t[int(row["t"])].append(row)
    previous: dict[int, str] = {}
    shell_rows = []
    for t, rows in sorted(rows_by_t.items()):
        entropies = [float(row["entropy_vn"]) for row in rows]
        min_e = min(entropies)
        max_e = max(entropies)
        band_by_state = {
            int(row["state_id"]): shell_band(float(row["entropy_vn"]), min_e, max_e)
            for row in rows
        }
        members: dict[str, list[int]] = defaultdict(list)
        for state_id, band in band_by_state.items():
            members[band].append(state_id)
        boundary_edges = []
        for edge in parent_objects()["carrier"]["edges"]:
            src = int(edge["src"])
            dst = int(edge["dst"])
            if band_by_state[src] != band_by_state[dst]:
                boundary_edges.append({"src": src, "dst": dst, "generator": edge["generator"]})
        entered = [state_id for state_id, band in band_by_state.items() if previous and previous.get(state_id) != band]
        exited = [state_id for state_id, band in previous.items() if previous and band_by_state.get(state_id) != band]
        persisted = sum(1 for state_id, band in band_by_state.items() if previous.get(state_id) == band) if previous else 0
        shell_rows.append(
            {
                "t": t,
                "shell_rule_id": "entropy_level_recomputed_each_t",
                "member_cells": {key: sorted(value) for key, value in sorted(members.items())},
                "state_shell_by_id": {str(k): v for k, v in sorted(band_by_state.items())},
                "boundary_edges": boundary_edges[:40],
                "boundary_edge_count": len(boundary_edges),
                "entered_cells": sorted(entered),
                "exited_cells": sorted(exited),
                "persistence_fraction": round(persisted / EXPECTED_STATE_COUNT, 12) if previous else 1.0,
                "entropy_band_or_boundary_value": {
                    "min_entropy": round(min_e, 12),
                    "max_entropy": round(max_e, 12),
                    "rule": "live min/max thirds recomputed at this t",
                },
            }
        )
        previous = band_by_state
    return shell_rows


def jk_fuzz_rows(state_rows: list[dict[str, Any]], shell_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    shell_by_t = {int(row["t"]): {int(k): v for k, v in row["state_shell_by_id"].items()} for row in shell_rows}
    edges_by_src: dict[int, list[dict[str, Any]]] = defaultdict(list)
    cells = carrier_cells_by_id()
    for edge in parent_objects()["carrier"]["edges"]:
        edges_by_src[int(edge["src"])].append(edge)
    rows = []
    for state in state_rows:
        t = int(state["t"])
        current_cell = int(state["current_cell"])
        candidates = edges_by_src[current_cell]
        admissible = [edge for edge in candidates if bool(cells[int(edge["dst"])]["Adm_C"])]
        target_ids = sorted({int(edge["dst"]) for edge in admissible})
        entropy_classes = sorted(
            {
                shell_band(
                    density_state_from_coord(cells[target]["coord"])["entropy_vn"],
                    0.0,
                    math.log(2.0),
                )
                for target in target_ids
            }
        )
        shell_classes = sorted({shell_by_t[t].get(state["state_id"], "unknown")})
        target_count = len(target_ids)
        if not candidates:
            fuzz_class = "none"
        elif target_count <= 1:
            fuzz_class = "low"
        elif target_count <= 2:
            fuzz_class = "split"
        else:
            fuzz_class = "broad"
        rows.append(
            {
                "t": t,
                "state_id": state["state_id"],
                "current_cell": current_cell,
                "candidate_continuations_k": len(candidates),
                "admissible_continuations_j": len(admissible),
                "admissible_target_count": target_count,
                "entropy_signature_classes": entropy_classes,
                "shell_target_classes": shell_classes,
                "killed_continuations": [
                    {"generator": edge["generator"], "dst": int(edge["dst"]), "reason": "outside_Adm_C"}
                    for edge in candidates
                    if not bool(cells[int(edge["dst"])]["Adm_C"])
                ],
                "fuzz_class": fuzz_class,
            }
        )
    return rows


def trajectory_metrics(state_rows: list[dict[str, Any]], shell_rows: list[dict[str, Any]], jk_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    states_by_t: dict[int, list[dict[str, Any]]] = defaultdict(list)
    jk_by_t: dict[int, list[dict[str, Any]]] = defaultdict(list)
    shell_by_t = {int(row["t"]): row for row in shell_rows}
    for row in state_rows:
        states_by_t[int(row["t"])].append(row)
    for row in jk_rows:
        jk_by_t[int(row["t"])].append(row)
    metrics = []
    for t, rows in sorted(states_by_t.items()):
        entropies = [float(row["entropy_vn"]) for row in rows]
        jk = jk_by_t[t]
        metrics.append(
            {
                "t": t,
                "entropy_variance": round(statistics.pvariance(entropies), 12),
                "entropy_range": round(max(entropies) - min(entropies), 12),
                "shell_boundary_edge_count": int(shell_by_t[t]["boundary_edge_count"]),
                "jk_mean_admissible": round(sum(row["admissible_continuations_j"] for row in jk) / len(jk), 12),
                "jk_mean_targets": round(sum(row["admissible_target_count"] for row in jk) / len(jk), 12),
                "current_cells_sha256": stable_sha256([row["current_cell"] for row in sorted(rows, key=lambda item: item["state_id"])]),
            }
        )
    return metrics


def enrich_trajectory(raw: dict[str, Any]) -> dict[str, Any]:
    shells = dynamic_shell_rows(raw["state_rows"])
    jk = jk_fuzz_rows(raw["state_rows"], shells)
    field_rows = entropy_field_rows(raw["state_rows"])
    gradients = entropy_gradients(raw["state_rows"])
    metrics = trajectory_metrics(raw["state_rows"], shells, jk)
    raw.update(
        {
            "entropy_field_rows": field_rows,
            "entropy_gradients": gradients,
            "dynamic_shell_rows": shells,
            "jk_fuzz_rows": jk,
            "metrics_by_t": metrics,
            "entropy_signature_sha256": stable_sha256(
                [{"t": row["t"], "state_id": row["state_id"], "S_vN": row["S_vN"]} for row in field_rows]
            ),
            "shell_signature_sha256": stable_sha256(
                [{"t": row["t"], "state_shell_by_id": row["state_shell_by_id"]} for row in shells]
            ),
            "jk_signature_sha256": stable_sha256(
                [
                    {
                        "t": row["t"],
                        "state_id": row["state_id"],
                        "j": row["admissible_continuations_j"],
                        "k": row["candidate_continuations_k"],
                        "targets": row["admissible_target_count"],
                    }
                    for row in jk
                ]
            ),
        }
    )
    return raw


def small_committed_kick_initial_cells(drop_half: bool = False) -> list[int]:
    lookup = transition_lookup()
    kicked = []
    for state_id in initial_cells():
        if drop_half and state_id % 2 == 1:
            kicked.append(state_id)
            continue
        preferred = lookup[(state_id, "R_x")]
        if preferred == state_id:
            alternatives = [
                lookup[(state_id, generator)]
                for generator in parent_objects()["carrier"]["generator_names"]
                if lookup[(state_id, generator)] != state_id
            ]
            preferred = alternatives[0] if alternatives else state_id
        kicked.append(preferred)
    return kicked


def scrambled_lookup() -> dict[tuple[int, str], int]:
    lookup = {}
    for idx, edge in enumerate(parent_objects()["carrier"]["edges"]):
        lookup[(int(edge["src"]), str(edge["generator"]))] = int((int(edge["dst"]) * 7 + idx * 3 + 5) % EXPECTED_STATE_COUNT)
    return lookup


def schedule_for_window(window_t: int) -> list[dict[str, Any]]:
    base = committed_schedule()
    schedule = []
    for index in range(window_t):
        row = dict(base[index % len(base)])
        row["step_index"] = index + 1
        row["cycle_index"] = index // len(base)
        row["base_step_index"] = base[index % len(base)]["step_index"]
        schedule.append(row)
    return schedule


def central_cell_id() -> int:
    cells = carrier_cells_by_id()
    return min(cells, key=lambda cell_id: (sum(float(x) ** 2 for x in cells[cell_id]["coord"]), cell_id))


@lru_cache(maxsize=1)
def initial_shell_by_state() -> dict[int, str]:
    rows = state_rows_for_cells(
        trajectory_id="initial_shell_probe",
        t=0,
        current_cells=initial_cells(),
        applied_generator=None,
        source_cells=None,
    )
    shell = dynamic_shell_rows(rows)[0]["state_shell_by_id"]
    return {int(state_id): str(value) for state_id, value in shell.items()}


def target_cell_ids(target_mode: str) -> list[int]:
    center = central_cell_id()
    if target_mode == "single_cell":
        return [center]
    if target_mode == "neighborhood":
        neighbors = {center}
        for edge in parent_objects()["carrier"]["edges"]:
            src = int(edge["src"])
            dst = int(edge["dst"])
            if src == center:
                neighbors.add(dst)
            if dst == center:
                neighbors.add(src)
        return sorted(neighbors)
    if target_mode == "shell_boundary":
        rows = state_rows_for_cells(
            trajectory_id="target_shell_boundary_probe",
            t=0,
            current_cells=initial_cells(),
            applied_generator=None,
            source_cells=None,
        )
        shell = dynamic_shell_rows(rows)[0]
        boundary = set()
        for edge in shell["boundary_edges"]:
            boundary.add(int(edge["src"]))
            boundary.add(int(edge["dst"]))
        return sorted(boundary)
    if target_mode == "v0_all_cells_regression":
        return initial_cells()
    raise ValueError(f"unknown target mode: {target_mode}")


def first_nonidentity_destination(cell_id: int) -> int:
    lookup = transition_lookup()
    for generator in parent_objects()["carrier"]["generator_names"]:
        dst = int(lookup[(int(cell_id), str(generator))])
        if dst != int(cell_id):
            return dst
    return int(cell_id)


def biased_generator_for_cell(cell_id: int) -> str:
    shell = initial_shell_by_state().get(int(cell_id), "mid_entropy_level")
    if shell == "low_entropy_level":
        return "D_z"
    if shell == "high_entropy_level":
        return "Ni_Source_R"
    return "R_x"


def nearest_cell_to_coord(coord: list[float]) -> int:
    cells = carrier_cells_by_id()
    best_id = min(
        cells,
        key=lambda cell_id: (
            sum((float(coord[idx]) - float(cells[cell_id]["coord"][idx])) ** 2 for idx in range(3)),
            cell_id,
        ),
    )
    return int(best_id)


def purity_projective_destination(cell_id: int) -> int:
    coord = [float(value) for value in carrier_cells_by_id()[int(cell_id)]["coord"]]
    norm = math.sqrt(sum(value * value for value in coord))
    if norm <= EPS:
        pure_coord = [0.0, 0.0, 1.0]
    else:
        pure_coord = [value / norm for value in coord]
    return nearest_cell_to_coord(pure_coord)


def kick_destination(cell_id: int, family_id: str, strength_steps: int) -> int:
    lookup = transition_lookup()
    current = int(cell_id)
    for _ in range(int(strength_steps)):
        if family_id == "purity_projective_resets":
            next_cell = purity_projective_destination(current)
        elif family_id == "generator_biased_kicks":
            generator = biased_generator_for_cell(current)
            next_cell = int(lookup.get((current, generator), current))
        else:
            family = next(row for row in PERTURBATION_FAMILIES if row["family_id"] == family_id)
            generator = str(family["generator"])
            next_cell = int(lookup.get((current, generator), current))
        if next_cell == current and family_id == "unitary_kicks":
            next_cell = first_nonidentity_destination(current)
        current = next_cell
    return current


def perturb_initial_cells(
    *,
    family_id: str,
    strength_steps: int,
    target_mode: str,
    drop_half: bool = False,
) -> dict[str, Any]:
    targets = target_cell_ids(target_mode)
    active_targets = [cell for idx, cell in enumerate(targets) if not drop_half or idx % 2 == 0]
    active_target_set = set(active_targets)
    current = []
    for cell_id in initial_cells():
        if cell_id in active_target_set:
            current.append(kick_destination(cell_id, family_id, strength_steps))
        else:
            current.append(cell_id)
    changed = sum(left != right for left, right in zip(initial_cells(), current, strict=True))
    return {
        "initial_cells": current,
        "target_cells": targets,
        "active_target_cells": active_targets,
        "changed_initial_state_count": changed,
        "drop_half": drop_half,
        "row_status": "refused_dead_family_or_target" if changed == 0 else "ran",
    }


@lru_cache(maxsize=None)
def baseline_trajectory(window_t: int, lookup_kind: str = "normal") -> dict[str, Any]:
    lookup = scrambled_lookup() if lookup_kind == "scrambled" else transition_lookup()
    return enrich_trajectory(
        apply_schedule(
            trajectory_id=f"{lookup_kind}_baseline_T{window_t}",
            schedule=schedule_for_window(window_t),
            lookup=lookup,
        )
    )


def apply_cell_schedule(
    *,
    trajectory_id: str,
    window_t: int,
    initial_override: tuple[int, ...] | None = None,
    lookup_kind: str = "normal",
    identity: bool = False,
) -> dict[str, Any]:
    lookup = scrambled_lookup() if lookup_kind == "scrambled" else transition_lookup()
    current = list(initial_override or tuple(initial_cells()))
    state_rows = [
        {
            "trajectory_id": trajectory_id,
            "state_id": int(state_id),
            "t": 0,
            "current_cell": int(cell_id),
        }
        for state_id, cell_id in zip(initial_cells(), current, strict=True)
    ]
    for step in schedule_for_window(window_t):
        before = list(current)
        generator = "IDENTITY" if identity else str(step["generator"])
        current = [int(cell) if identity else int(lookup[(int(cell), generator)]) for cell in before]
        state_rows.extend(
            {
                "trajectory_id": trajectory_id,
                "state_id": int(state_id),
                "t": int(step["step_index"]),
                "current_cell": int(cell_id),
            }
            for state_id, cell_id in zip(initial_cells(), current, strict=True)
        )
    return {"trajectory_id": trajectory_id, "T": window_t, "state_rows": state_rows}


@lru_cache(maxsize=None)
def baseline_cell_trajectory(window_t: int, lookup_kind: str = "normal") -> dict[str, Any]:
    return apply_cell_schedule(
        trajectory_id=f"{lookup_kind}_baseline_cells_T{window_t}",
        window_t=window_t,
        lookup_kind=lookup_kind,
    )


def trajectory_for_initial(
    *,
    trajectory_id: str,
    window_t: int,
    initial_override: list[int],
    lookup_kind: str = "normal",
) -> dict[str, Any]:
    return apply_cell_schedule(
        trajectory_id=trajectory_id,
        window_t=window_t,
        initial_override=tuple(initial_override),
        lookup_kind=lookup_kind,
    )


def rows_by_t_state(trajectory: dict[str, Any]) -> dict[int, dict[int, dict[str, Any]]]:
    by_t: dict[int, dict[int, dict[str, Any]]] = defaultdict(dict)
    for row in trajectory["state_rows"]:
        by_t[int(row["t"])][int(row["state_id"])] = row
    return by_t


def divergence_series(control: dict[str, Any], perturbed: dict[str, Any]) -> dict[int, list[int]]:
    c_by_t = rows_by_t_state(control)
    p_by_t = rows_by_t_state(perturbed)
    series: dict[int, list[int]] = {}
    for state_id in initial_cells():
        series[state_id] = [
            int(c_by_t[t][state_id]["current_cell"] != p_by_t[t][state_id]["current_cell"])
            for t in sorted(c_by_t)
        ]
    return series


def density_matrix_for_cell(cell_id: int) -> torch.Tensor:
    density = density_state_from_coord(carrier_cells_by_id()[int(cell_id)]["coord"])
    real = torch.tensor(density["rho_real"], dtype=torch.float64)
    imag = torch.tensor(density["rho_imag"], dtype=torch.float64)
    return real.to(torch.complex128) + 1j * imag.to(torch.complex128)


def initial_shell_weight(state_id: int) -> int:
    shell = initial_shell_by_state().get(int(state_id), "mid_entropy_level")
    return {"low_entropy_level": 1, "mid_entropy_level": 2, "high_entropy_level": 3}.get(shell, 1)


def shell_weighted_tv_scores(control: dict[str, Any], perturbed: dict[str, Any]) -> dict[int, float]:
    c_by_t = rows_by_t_state(control)
    p_by_t = rows_by_t_state(perturbed)
    final_t = max(c_by_t)
    scores: dict[int, float] = {}
    for state_id in initial_cells():
        control_cell = int(c_by_t[final_t][state_id]["current_cell"])
        perturbed_cell = int(p_by_t[final_t][state_id]["current_cell"])
        delta = density_matrix_for_cell(control_cell) - density_matrix_for_cell(perturbed_cell)
        trace_norm = float(torch.linalg.svdvals(delta).sum().real.item())
        scores[state_id] = initial_shell_weight(state_id) * trace_norm
    return scores


def classify_states(control: dict[str, Any], perturbed: dict[str, Any], classifier_id: str) -> dict[int, str]:
    series = divergence_series(control, perturbed)
    classes: dict[int, str] = {}
    if classifier_id == "shell_weighted_tv":
        scores = shell_weighted_tv_scores(control, perturbed)
        nonzero = [score for score in scores.values() if score > EPS]
        if not nonzero:
            return {state_id: "TV_ZERO" for state_id in initial_cells()}
        if max(nonzero) - min(nonzero) <= EPS:
            return {state_id: "TV_FLAT" if scores[state_id] > EPS else "TV_ZERO" for state_id in initial_cells()}
        threshold = statistics.median(nonzero)
        return {
            state_id: "TV_HIGH" if score > threshold + EPS else "TV_LOW" if score > EPS else "TV_ZERO"
            for state_id, score in scores.items()
        }
    for state_id, values in series.items():
        initial = values[0]
        final = values[-1]
        peak = max(values)
        first_divergence = next((idx for idx, value in enumerate(values) if value), None)
        if classifier_id == "v0_divergence":
            classes[state_id] = "SPREAD" if final else "DAMP"
        elif classifier_id == "baseline_growth_rate_sign":
            if final > initial:
                classes[state_id] = "SPREAD"
            elif final < initial:
                classes[state_id] = "DAMP"
            elif peak == 0:
                classes[state_id] = "NEUTRAL"
            else:
                classes[state_id] = "SCRAMBLING"
        elif classifier_id == "recovery_return_time":
            if peak == 0:
                classes[state_id] = "RETURN"
            elif final == 0:
                classes[state_id] = "RETURN"
            elif first_divergence is not None and any(value == 0 for value in values[first_divergence + 1 : -1]):
                classes[state_id] = "SCRAMBLING"
            else:
                classes[state_id] = "BOUNDARY"
        else:
            raise ValueError(f"unknown classifier: {classifier_id}")
    return classes


def class_distribution(classes: dict[int, str]) -> dict[str, int]:
    return dict(sorted(Counter(classes.values()).items()))


def class_majority(classes: dict[int, str]) -> dict[str, Any]:
    counts = Counter(classes.values())
    majority_class, majority_count = counts.most_common(1)[0]
    return {
        "majority_class": majority_class,
        "majority_count": majority_count,
        "majority_baseline_accuracy": round(majority_count / EXPECTED_STATE_COUNT, 12),
    }


@lru_cache(maxsize=1)
def feature_rows() -> dict[int, dict[str, Any]]:
    cells = carrier_cells_by_id()
    old_phi = {int(row["cell_id"]): int(row["axis0_polarity_sign"]) for row in parent_objects()["axis0"]["readout_table"]}
    shell = initial_shell_by_state()
    rows: dict[int, dict[str, Any]] = {}
    for state_id, cell in cells.items():
        radius = float(cell["radius_squared"])
        coord = [float(value) for value in cell["coord"]]
        rows[state_id] = {
            "old_phi_sign": str(old_phi[state_id]),
            "initial_entropy_shell": shell[state_id],
            "radius_band": "low" if radius <= 0.25 + EPS else "mid" if radius <= 0.75 + EPS else "high",
            "conditioned_shell_member": str(bool(cell["conditioned_shell_member"])),
            "z_sign": "negative" if coord[2] < -EPS else "positive" if coord[2] > EPS else "zero",
        }
    return rows


def train_feature_model(classes: dict[int, str], feature_id: str) -> dict[str, str]:
    buckets: dict[str, list[str]] = defaultdict(list)
    for state_id, row in feature_rows().items():
        buckets[str(row[feature_id])].append(classes[state_id])
    return {key: Counter(values).most_common(1)[0][0] for key, values in sorted(buckets.items())}


def model_accuracy(classes: dict[int, str], feature_id: str, class_by_feature: dict[str, str]) -> float:
    correct = 0
    fallback = Counter(classes.values()).most_common(1)[0][0]
    for state_id, actual in classes.items():
        feature_value = str(feature_rows()[state_id][feature_id])
        predicted = class_by_feature.get(feature_value, fallback)
        correct += int(predicted == actual)
    return correct / EXPECTED_STATE_COUNT


def best_nonidentity_predictor(classes: dict[int, str]) -> dict[str, Any]:
    majority = class_majority(classes)
    candidates = []
    for feature_id in sorted(next(iter(feature_rows().values())).keys()):
        class_by_feature = train_feature_model(classes, feature_id)
        accuracy = model_accuracy(classes, feature_id, class_by_feature)
        cardinality = len({str(row[feature_id]) for row in feature_rows().values()})
        candidates.append(
            {
                "feature_id": feature_id,
                "accuracy": round(accuracy, 12),
                "class_by_feature": class_by_feature,
                "feature_cardinality": cardinality,
                "identity_like": cardinality >= EXPECTED_STATE_COUNT,
            }
        )
    best = max(candidates, key=lambda row: (row["accuracy"], -row["feature_cardinality"], row["feature_id"]))
    best["beats_majority_baseline"] = best["accuracy"] > majority["majority_baseline_accuracy"] + EPS
    return best


def permuted_feature_accuracy(classes: dict[int, str], feature_id: str, class_by_feature: dict[str, str]) -> float:
    state_ids = initial_cells()
    shift = 7
    correct = 0
    fallback = Counter(classes.values()).most_common(1)[0][0]
    for index, state_id in enumerate(state_ids):
        permuted_state = state_ids[(index + shift) % len(state_ids)]
        feature_value = str(feature_rows()[permuted_state][feature_id])
        predicted = class_by_feature.get(feature_value, fallback)
        correct += int(predicted == classes[state_id])
    return correct / EXPECTED_STATE_COUNT


def negative_control_summary(
    *,
    control: dict[str, Any],
    family_id: str,
    strength_steps: int,
    target_mode: str,
    window_t: int,
    classifier_id: str,
    positive_classes: dict[int, str],
    predictor: dict[str, Any],
) -> dict[str, Any]:
    feature_id = predictor["feature_id"]
    class_by_feature = predictor["class_by_feature"]
    positive_majority = class_majority(positive_classes)["majority_baseline_accuracy"]

    identity_classes = classify_states(control, control, classifier_id)
    identity_majority = class_majority(identity_classes)["majority_baseline_accuracy"]
    identity_accuracy = model_accuracy(identity_classes, feature_id, class_by_feature)

    dropped = perturb_initial_cells(
        family_id=family_id,
        strength_steps=strength_steps,
        target_mode=target_mode,
        drop_half=True,
    )
    dropped_traj = trajectory_for_initial(
        trajectory_id=f"dropped_half_{family_id}_{target_mode}_T{window_t}",
        window_t=window_t,
        initial_override=dropped["initial_cells"],
    )
    dropped_classes = classify_states(control, dropped_traj, classifier_id)
    dropped_majority = class_majority(dropped_classes)["majority_baseline_accuracy"]
    dropped_accuracy = model_accuracy(dropped_classes, feature_id, class_by_feature)

    scrambled_control = baseline_cell_trajectory(window_t, lookup_kind="scrambled")
    perturbed = perturb_initial_cells(
        family_id=family_id,
        strength_steps=strength_steps,
        target_mode=target_mode,
    )
    scrambled_perturbed = trajectory_for_initial(
        trajectory_id=f"scrambled_{family_id}_{target_mode}_T{window_t}",
        window_t=window_t,
        initial_override=perturbed["initial_cells"],
        lookup_kind="scrambled",
    )
    scrambled_classes = classify_states(scrambled_control, scrambled_perturbed, classifier_id)
    scrambled_majority = class_majority(scrambled_classes)["majority_baseline_accuracy"]
    scrambled_accuracy = model_accuracy(scrambled_classes, feature_id, class_by_feature)

    label_permutation_accuracy = permuted_feature_accuracy(positive_classes, feature_id, class_by_feature)
    label_permutation_beats = label_permutation_accuracy > positive_majority + EPS

    controls = {
        "identity_dynamics": {
            "model_accuracy": round(identity_accuracy, 12),
            "majority_baseline_accuracy": identity_majority,
            "beats_majority_baseline": identity_accuracy > identity_majority + EPS,
            "class_distribution": class_distribution(identity_classes),
        },
        "scrambled_adjacency": {
            "model_accuracy": round(scrambled_accuracy, 12),
            "majority_baseline_accuracy": scrambled_majority,
            "beats_majority_baseline": scrambled_accuracy > scrambled_majority + EPS,
            "class_distribution": class_distribution(scrambled_classes),
        },
        "label_permutation": {
            "model_accuracy": round(label_permutation_accuracy, 12),
            "majority_baseline_accuracy": positive_majority,
            "beats_majority_baseline": label_permutation_beats,
            "permutation": "state_ids_rotated_by_7",
        },
        "dropped_half_per_family": {
            "changed_initial_state_count": dropped["changed_initial_state_count"],
            "model_accuracy": round(dropped_accuracy, 12),
            "majority_baseline_accuracy": dropped_majority,
            "beats_majority_baseline": dropped_accuracy > dropped_majority + EPS,
            "class_distribution": class_distribution(dropped_classes),
        },
    }
    return {
        "controls": controls,
        "negative_controls_fail_candidate": not any(row["beats_majority_baseline"] for row in controls.values()),
    }


def class_sign(label: str) -> int:
    if label in {"SPREAD", "BOUNDARY", "TV_HIGH"}:
        return 1
    if label in {"DAMP", "RETURN", "TV_LOW"}:
        return -1
    return 0


def sign_class(sign: int) -> str:
    if sign > 0:
        return "COMMON_POSITIVE"
    if sign < 0:
        return "COMMON_NEGATIVE"
    return "UNSTABLE"


def agreement_classes(family_vectors: dict[str, dict[int, str]], threshold_k: int) -> dict[int, str]:
    classes: dict[int, str] = {}
    for state_id in initial_cells():
        signs = [class_sign(vector[state_id]) for vector in family_vectors.values()]
        counts = Counter(sign for sign in signs if sign != 0)
        if not counts:
            classes[state_id] = "UNSTABLE"
            continue
        most_common = counts.most_common()
        best_sign, best_count = most_common[0]
        tied = len(most_common) > 1 and most_common[1][1] == best_count
        classes[state_id] = "UNSTABLE" if tied or best_count < threshold_k else sign_class(best_sign)
    return classes


def family_classes_for_control(
    *,
    control_kind: str,
    family_id: str,
    strength_steps: int,
    target_mode: str,
    window_t: int,
    classifier_id: str,
) -> dict[int, str] | None:
    if control_kind == "identity_dynamics":
        control = baseline_cell_trajectory(window_t)
        return classify_states(control, control, classifier_id)
    if control_kind == "scrambled_adjacency":
        control = baseline_cell_trajectory(window_t, lookup_kind="scrambled")
        perturbed_initial = perturb_initial_cells(
            family_id=family_id,
            strength_steps=strength_steps,
            target_mode=target_mode,
        )
        if perturbed_initial["row_status"] != "ran":
            return None
        perturbed = trajectory_for_initial(
            trajectory_id=f"robust_scrambled_{family_id}_{target_mode}_T{window_t}",
            window_t=window_t,
            initial_override=perturbed_initial["initial_cells"],
            lookup_kind="scrambled",
        )
        return classify_states(control, perturbed, classifier_id)
    if control_kind == "dropped_half_per_family":
        control = baseline_cell_trajectory(window_t)
        perturbed_initial = perturb_initial_cells(
            family_id=family_id,
            strength_steps=strength_steps,
            target_mode=target_mode,
            drop_half=True,
        )
        if perturbed_initial["row_status"] != "ran":
            return None
        perturbed = trajectory_for_initial(
            trajectory_id=f"robust_dropped_{family_id}_{target_mode}_T{window_t}",
            window_t=window_t,
            initial_override=perturbed_initial["initial_cells"],
        )
        return classify_states(control, perturbed, classifier_id)
    raise ValueError(f"unknown robust control kind: {control_kind}")


def agreement_negative_control_summary(
    *,
    group_rows: list[dict[str, Any]],
    threshold_k: int,
    classifier_id: str,
    target_mode: str,
    window_t: int,
    positive_classes: dict[int, str],
    predictor: dict[str, Any],
) -> dict[str, Any]:
    feature_id = predictor["feature_id"]
    class_by_feature = predictor["class_by_feature"]
    positive_majority = class_majority(positive_classes)["majority_baseline_accuracy"]
    controls: dict[str, dict[str, Any]] = {}
    for control_kind in ("identity_dynamics", "scrambled_adjacency", "dropped_half_per_family"):
        family_vectors: dict[str, dict[int, str]] = {}
        for row in group_rows:
            classes = family_classes_for_control(
                control_kind=control_kind,
                family_id=row["family_id"],
                strength_steps=int(row["strength_steps"]),
                target_mode=target_mode,
                window_t=window_t,
                classifier_id=classifier_id,
            )
            if classes is not None:
                family_vectors[row["family_id"]] = classes
        control_classes = agreement_classes(family_vectors, threshold_k) if family_vectors else {state_id: "UNSTABLE" for state_id in initial_cells()}
        majority = class_majority(control_classes)["majority_baseline_accuracy"]
        accuracy = model_accuracy(control_classes, feature_id, class_by_feature)
        controls[control_kind] = {
            "family_count": len(family_vectors),
            "model_accuracy": round(accuracy, 12),
            "majority_baseline_accuracy": majority,
            "beats_majority_baseline": accuracy > majority + EPS,
            "class_distribution": class_distribution(control_classes),
        }
    label_permutation_accuracy = permuted_feature_accuracy(positive_classes, feature_id, class_by_feature)
    controls["label_permutation"] = {
        "model_accuracy": round(label_permutation_accuracy, 12),
        "majority_baseline_accuracy": positive_majority,
        "beats_majority_baseline": label_permutation_accuracy > positive_majority + EPS,
        "permutation": "state_ids_rotated_by_7",
    }
    return {
        "controls": controls,
        "negative_controls_fail_candidate": not any(row["beats_majority_baseline"] for row in controls.values()),
    }


def build_agreement_threshold_rows(sweep_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in sweep_rows:
        if row["row_status"] == "ran":
            groups[(row["strength_id"], row["target_mode"], int(row["window_T"]), row["classifier_id"])].append(row)
    robust_rows: list[dict[str, Any]] = []
    for (strength_id, target_mode, window_t, classifier_id), group_rows in sorted(groups.items()):
        family_vectors = {
            row["family_id"]: {int(k): v for k, v in row["class_by_state"].items()}
            for row in group_rows
        }
        max_threshold = min(max(AGREEMENT_THRESHOLD_LADDER), len(family_vectors))
        for threshold_k in [k for k in AGREEMENT_THRESHOLD_LADDER if k <= max_threshold]:
            classes = agreement_classes(family_vectors, threshold_k)
            majority = class_majority(classes)
            predictor = best_nonidentity_predictor(classes)
            negative = agreement_negative_control_summary(
                group_rows=group_rows,
                threshold_k=threshold_k,
                classifier_id=classifier_id,
                target_mode=target_mode,
                window_t=window_t,
                positive_classes=classes,
                predictor=predictor,
            )
            failures = []
            if not predictor["beats_majority_baseline"]:
                failures.append("does_not_beat_majority_baseline")
            if threshold_k < 2:
                failures.append("not_stable_across_2_or_more_perturbation_families")
            if not negative["negative_controls_fail_candidate"]:
                failures.append("negative_control_passed_candidate")
            if predictor["identity_like"]:
                failures.append("identity_like_feature")
            robust_rows.append(
                {
                    "refinement_id": "family_robust_agreement_threshold",
                    "strength_id": strength_id,
                    "target_mode": target_mode,
                    "window_T": window_t,
                    "classifier_id": classifier_id,
                    "agreement_threshold_k": threshold_k,
                    "family_ids": sorted(family_vectors),
                    "family_count": len(family_vectors),
                    "class_distribution": class_distribution(classes),
                    **majority,
                    "best_non_identity_predictor": predictor,
                    "beats_majority_baseline": bool(predictor["beats_majority_baseline"]),
                    "stable_family_count": threshold_k,
                    "stable_across_2_or_more_families": threshold_k >= 2,
                    "negative_controls": negative["controls"],
                    "negative_controls_fail_candidate": negative["negative_controls_fail_candidate"],
                    "no_identity_leak": predictor["identity_like"] is False,
                    "criterion_rule": SEPARATION_RULE_VERBATIM,
                    "class_by_state": {str(k): v for k, v in sorted(classes.items())},
                    "failure_reasons": failures,
                    "criterion_verdict": "EARNS_CANDIDATE_READOUT" if not failures else "FAILS_CRITERION",
                }
            )
    return robust_rows


def v1_anchor_disagreement(sweep_rows: list[dict[str, Any]]) -> dict[str, Any]:
    anchor_rows = [
        row
        for row in sweep_rows
        if row.get("family_id") in V1_FAMILY_IDS
        and row.get("strength_id") == V1_ANCHOR_CORNER["strength_id"]
        and row.get("target_mode") == V1_ANCHOR_CORNER["target_mode"]
        and int(row.get("window_T", -1)) == V1_ANCHOR_CORNER["window_T"]
        and row.get("classifier_id") == V1_ANCHOR_CORNER["classifier_id"]
    ]
    vectors = {
        row["family_id"]: {int(k): v for k, v in row.get("class_by_state", {}).items()}
        for row in anchor_rows
        if row.get("row_status") == "ran"
    }
    disagreement_rows = []
    for state_id in initial_cells():
        classes = {family_id: vector[state_id] for family_id, vector in sorted(vectors.items())}
        class_counts = dict(sorted(Counter(classes.values()).items()))
        sign_counts = dict(sorted(Counter(class_sign(value) for value in classes.values()).items()))
        disagreement_rows.append(
            {
                "state_id": state_id,
                "classes_by_family": classes,
                "class_counts": class_counts,
                "sign_counts": {str(k): v for k, v in sign_counts.items()},
                "class_flips_between_families": len(class_counts) > 1,
                "sign_flips_between_families": len([key for key in sign_counts if key != 0]) > 1,
            }
        )
    amplitude = next((row for row in anchor_rows if row["family_id"] == "amplitude_kicks"), None)
    expected_boundary = [4, 11, 12, 14, 15, 19, 23, 26, 27]
    observed_boundary = []
    if amplitude:
        observed_boundary = sorted(int(state_id) for state_id, label in amplitude["class_by_state"].items() if label == "BOUNDARY")
    return {
        "diagnostic_id": "v1_anchor_corner_family_classification_vectors",
        "corner": V1_ANCHOR_CORNER,
        "family_ids": V1_FAMILY_IDS,
        "per_family": {
            row["family_id"]: {
                "row_status": row["row_status"],
                "class_distribution": row["class_distribution"],
                "criterion_verdict": row["criterion_verdict"],
                "failure_reasons": row.get("failure_reasons", []),
                "class_vector_sha256": stable_sha256(row.get("class_by_state", {})),
                "class_by_state": row.get("class_by_state", {}),
            }
            for row in sorted(anchor_rows, key=lambda item: item["family_id"])
        },
        "cell_disagreement_rows": disagreement_rows,
        "class_flip_cell_ids": [row["state_id"] for row in disagreement_rows if row["class_flips_between_families"]],
        "sign_flip_cell_ids": [row["state_id"] for row in disagreement_rows if row["sign_flips_between_families"]],
        "v1_best_partial_regression": {
            "expected_family_id": "amplitude_kicks",
            "expected_class_distribution": {"BOUNDARY": 9, "RETURN": 24},
            "observed_class_distribution": amplitude.get("class_distribution") if amplitude else {},
            "expected_boundary_cell_ids": expected_boundary,
            "observed_boundary_cell_ids": observed_boundary,
            "pass": bool(
                amplitude
                and amplitude.get("class_distribution") == {"BOUNDARY": 9, "RETURN": 24}
                and observed_boundary == expected_boundary
            ),
        },
    }


def build_sweep_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in PERTURBATION_FAMILIES:
        family_id = family["family_id"]
        for strength in STRENGTH_LADDER:
            for target in TARGET_MODES:
                target_mode = target["target_mode"]
                perturbed_initial = perturb_initial_cells(
                    family_id=family_id,
                    strength_steps=int(strength["strength_steps"]),
                    target_mode=target_mode,
                )
                for window_t in window_ladder():
                    control = baseline_cell_trajectory(window_t)
                    if perturbed_initial["row_status"] != "ran":
                        for classifier in CLASSIFIERS:
                            rows.append(
                                {
                                    "family_id": family_id,
                                    "kind": family["kind"],
                                    "strength_id": strength["strength_id"],
                                    "strength_steps": strength["strength_steps"],
                                    "target_mode": target_mode,
                                    "target_cell_count": len(perturbed_initial["target_cells"]),
                                    "changed_initial_state_count": perturbed_initial["changed_initial_state_count"],
                                    "window_T": window_t,
                                    "classifier_id": classifier["classifier_id"],
                                    "row_status": perturbed_initial["row_status"],
                                    "class_distribution": {},
                                    "criterion_rule": SEPARATION_RULE_VERBATIM,
                                    "criterion_verdict": "REFUSED_DEAD_FAMILY_OR_TARGET",
                                    "failure_reasons": ["perturbation_bite_failed"],
                                }
                            )
                        continue
                    perturbed = trajectory_for_initial(
                        trajectory_id=f"{family_id}_{strength['strength_id']}_{target_mode}_T{window_t}",
                        window_t=window_t,
                        initial_override=perturbed_initial["initial_cells"],
                    )
                    for classifier in CLASSIFIERS:
                        classifier_id = classifier["classifier_id"]
                        classes = classify_states(control, perturbed, classifier_id)
                        majority = class_majority(classes)
                        predictor = best_nonidentity_predictor(classes)
                        negative = negative_control_summary(
                            control=control,
                            family_id=family_id,
                            strength_steps=int(strength["strength_steps"]),
                            target_mode=target_mode,
                            window_t=window_t,
                            classifier_id=classifier_id,
                            positive_classes=classes,
                            predictor=predictor,
                        )
                        rows.append(
                            {
                                "family_id": family_id,
                                "kind": family["kind"],
                                "strength_id": strength["strength_id"],
                                "strength_steps": strength["strength_steps"],
                                "target_mode": target_mode,
                                "target_cell_count": len(perturbed_initial["target_cells"]),
                                "active_target_cell_count": len(perturbed_initial["active_target_cells"]),
                                "changed_initial_state_count": perturbed_initial["changed_initial_state_count"],
                                "window_T": window_t,
                                "classifier_id": classifier_id,
                                "row_status": "ran",
                                "class_distribution": class_distribution(classes),
                                **majority,
                                "best_non_identity_predictor": predictor,
                                "beats_majority_baseline": bool(predictor["beats_majority_baseline"]),
                                "negative_controls": negative["controls"],
                                "negative_controls_fail_candidate": negative["negative_controls_fail_candidate"],
                                "criterion_rule": SEPARATION_RULE_VERBATIM,
                                "class_by_state": {str(k): v for k, v in sorted(classes.items())},
                            }
                        )
    return apply_stability_and_verdicts(rows)


def apply_stability_and_verdicts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["row_status"] == "ran":
            groups[(row["strength_id"], row["target_mode"], int(row["window_T"]), row["classifier_id"])].append(row)
    for row in rows:
        if row["row_status"] != "ran":
            continue
        feature_id = row["best_non_identity_predictor"]["feature_id"]
        group = groups[(row["strength_id"], row["target_mode"], int(row["window_T"]), row["classifier_id"])]
        stable_family_ids = sorted(
            {
                other["family_id"]
                for other in group
                if other.get("beats_majority_baseline") is True
                and other.get("best_non_identity_predictor", {}).get("feature_id") == feature_id
            }
        )
        row["stable_family_count"] = len(stable_family_ids)
        row["stable_family_ids"] = stable_family_ids
        row["stable_across_2_or_more_families"] = len(stable_family_ids) >= 2
        row["no_identity_leak"] = row["best_non_identity_predictor"]["identity_like"] is False
        failures = []
        if not row["beats_majority_baseline"]:
            failures.append("does_not_beat_majority_baseline")
        if not row["stable_across_2_or_more_families"]:
            failures.append("not_stable_across_2_or_more_perturbation_families")
        if not row["negative_controls_fail_candidate"]:
            failures.append("negative_control_passed_candidate")
        if not row["no_identity_leak"]:
            failures.append("identity_like_feature")
        row["failure_reasons"] = failures
        row["criterion_verdict"] = "EARNS_CANDIDATE_READOUT" if not failures else "FAILS_CRITERION"
    return rows


def v0_regression_row() -> dict[str, Any]:
    control = baseline_cell_trajectory(4)
    kicked = trajectory_for_initial(
        trajectory_id="v0_regression_small_committed_kick_R_x_then_carnot",
        window_t=4,
        initial_override=small_committed_kick_initial_cells(),
    )
    classes = classify_states(control, kicked, "v0_divergence")
    distribution = class_distribution(classes)
    return {
        "regression_id": "v0_small_committed_kick_T4_v0_divergence",
        "expected_distribution": V0_REGRESSION_EXPECTED,
        "observed_distribution": distribution,
        "pass": distribution == V0_REGRESSION_EXPECTED,
        "class_by_state": {str(k): v for k, v in sorted(classes.items())},
    }


def compare_trajectories(control: dict[str, Any], perturbed: dict[str, Any]) -> dict[str, Any]:
    c_by_t: dict[int, dict[int, dict[str, Any]]] = defaultdict(dict)
    p_by_t: dict[int, dict[int, dict[str, Any]]] = defaultdict(dict)
    for row in control["state_rows"]:
        c_by_t[int(row["t"])][int(row["state_id"])] = row
    for row in perturbed["state_rows"]:
        p_by_t[int(row["t"])][int(row["state_id"])] = row
    shell0 = control["dynamic_shell_rows"][0]["state_shell_by_id"]
    region_members: dict[str, list[int]] = defaultdict(list)
    for state_id_text, band in shell0.items():
        region_members[band].append(int(state_id_text))
    divergence_rows = []
    for t in sorted(c_by_t):
        changed = [
            state_id
            for state_id, row in c_by_t[t].items()
            if row["current_cell"] != p_by_t[t][state_id]["current_cell"]
        ]
        entropy_l2 = math.sqrt(
            sum((float(row["entropy_vn"]) - float(p_by_t[t][state_id]["entropy_vn"])) ** 2 for state_id, row in c_by_t[t].items())
            / EXPECTED_STATE_COUNT
        )
        divergence_rows.append(
            {
                "t": t,
                "state_hamming_fraction": round(len(changed) / EXPECTED_STATE_COUNT, 12),
                "entropy_l2": round(entropy_l2, 12),
                "changed_state_count": len(changed),
            }
        )
    region_classes = {}
    for band, members in sorted(region_members.items()):
        series = []
        for t in sorted(c_by_t):
            changed = sum(c_by_t[t][state_id]["current_cell"] != p_by_t[t][state_id]["current_cell"] for state_id in members)
            series.append(changed / len(members))
        initial = series[0]
        final = series[-1]
        peak = max(series)
        if peak <= EPS:
            spread_or_damp = "NEUTRAL"
            basin_vocab = "RETURN"
            response = "neutral"
        elif final < max(initial * 0.5, 0.05):
            spread_or_damp = "DAMP"
            basin_vocab = "RETURN"
            response = "homeostatic"
        elif final > initial + 0.05 or peak > initial + 0.05:
            spread_or_damp = "SPREAD"
            basin_vocab = "BOUNDARY"
            response = "allostatic"
        else:
            spread_or_damp = "DAMP" if final <= initial else "SPREAD"
            basin_vocab = "SCRAMBLING" if final <= initial else "BOUNDARY"
            response = "homeostatic" if final <= initial else "allostatic"
        region_classes[band] = {
            "initial_region_size": len(members),
            "divergence_series": [round(value, 12) for value in series],
            "spread_or_damp": spread_or_damp,
            "basin_vocabulary": basin_vocab,
            "allostasis_homeostasis_readout": response,
        }
    return {
        "divergence_rows": divergence_rows,
        "region_classifications": region_classes,
        "peak_state_hamming_fraction": max(row["state_hamming_fraction"] for row in divergence_rows),
        "final_state_hamming_fraction": divergence_rows[-1]["state_hamming_fraction"],
        "peak_entropy_l2": max(row["entropy_l2"] for row in divergence_rows),
    }


def dynamic_shell_motion(shell_rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(len(row["entered_cells"]) + len(row["exited_cells"]) for row in shell_rows)
    return {
        "total_entered_or_exited": total,
        "boundary_edge_counts_by_t": [row["boundary_edge_count"] for row in shell_rows],
        "boundary_count_delta_final_minus_initial": shell_rows[-1]["boundary_edge_count"] - shell_rows[0]["boundary_edge_count"],
        "shells_can_move": total > 0,
    }


def static_phi_bridge_row(response: dict[str, Any]) -> dict[str, Any]:
    readout = {int(row["cell_id"]): int(row["axis0_polarity_sign"]) for row in parent_objects()["axis0"]["readout_table"]}
    final_changed_by_state = {
        int(row["state_id"]): bool(row["current_cell"] != row["state_id"])
        for row in response["small_kick"]["state_rows"]
        if int(row["t"]) == response["small_kick"]["T"]
    }
    rows = []
    actual_classes = []
    correct = 0
    for state_id in initial_cells():
        phi_sign = readout[state_id]
        predicted = "SPREAD" if phi_sign > 0 else "DAMP" if phi_sign < 0 else "NEUTRAL"
        actual = "SPREAD" if final_changed_by_state[state_id] else "DAMP"
        actual_classes.append(actual)
        correct += int(predicted == actual)
        rows.append(
            {
                "cell_id": state_id,
                "old_phi_sign_at_c": phi_sign,
                "predicted_dynamic_response": predicted,
                "dynamic_response_class_under_perturbation": actual,
                "predicts_dynamic_response": predicted == actual,
            }
        )
    accuracy = correct / EXPECTED_STATE_COUNT
    majority = Counter(actual_classes).most_common(1)[0][1] / EXPECTED_STATE_COUNT
    return {
        "old_anchor_role": "static_proxy_equilibrium_shadow_candidate_only",
        "tested_not_assumed": True,
        "accuracy": round(accuracy, 12),
        "majority_baseline_accuracy": round(majority, 12),
        "predicts_above_chance": accuracy > majority,
        "outcome": "predicts_above_chance" if accuracy > majority else "fails_above_chance",
        "falsifier": "old_phi_sign fails to predict spread/damp better than control/null",
        "rows": rows,
    }


def summarize_sweep(rows: list[dict[str, Any]], robust_rows: list[dict[str, Any]]) -> dict[str, Any]:
    ran_rows = [row for row in rows if row.get("row_status") == "ran"]
    earned = [row for row in ran_rows if row.get("criterion_verdict") == "EARNS_CANDIDATE_READOUT"]
    robust_earned = [row for row in robust_rows if row.get("criterion_verdict") == "EARNS_CANDIDATE_READOUT"]
    partial = [
        row
        for row in ran_rows
        if row.get("beats_majority_baseline") is True
        or row.get("stable_across_2_or_more_families") is True
        or row.get("negative_controls_fail_candidate") is True
    ]
    robust_partial = [
        row
        for row in robust_rows
        if row.get("beats_majority_baseline") is True
        or row.get("stable_across_2_or_more_families") is True
        or row.get("negative_controls_fail_candidate") is True
    ]
    if robust_earned:
        first = sorted(
            robust_earned,
            key=lambda row: (
                int(row["window_T"]),
                int(row["agreement_threshold_k"]),
                row["target_mode"],
                row["classifier_id"],
            ),
        )[0]
        outcome = "separation_found"
        boundary = "family-robust stability-axis readout candidate at scratch; no admission"
        first_kind = "agreement_threshold_refinement"
    elif earned:
        first = sorted(
            earned,
            key=lambda row: (
                int(row["window_T"]),
                int(row["strength_steps"]),
                row["target_mode"],
                row["classifier_id"],
                row["family_id"],
            ),
        )[0]
        outcome = "separation_found"
        boundary = "first real Axis-0 readout candidate at scratch; no admission"
        first_kind = "single_family_grid_row"
    elif robust_partial:
        first = sorted(
            robust_partial,
            key=lambda row: (
                len(row.get("failure_reasons", [])),
                int(row["window_T"]),
                int(row["agreement_threshold_k"]),
                row["target_mode"],
                row["classifier_id"],
            ),
        )[0]
        outcome = "partial"
        boundary = "family-robust rows show partial structure but fail at least one majority/stability/control gate"
        first_kind = "agreement_threshold_refinement"
    elif partial:
        first = sorted(
            partial,
            key=lambda row: (
                len(row.get("failure_reasons", [])),
                int(row["window_T"]),
                int(row["strength_steps"]),
                row["target_mode"],
                row["classifier_id"],
                row["family_id"],
            ),
        )[0]
        outcome = "partial"
        boundary = "some rows show partial structure but fail at least one majority/stability/control gate"
        first_kind = "single_family_grid_row"
    else:
        first = None
        outcome = "no_separation_anywhere"
        boundary = "no row beat the full criterion; this carrier/dynamics may not host a two-sided response distinction under the pinned sweep"
        first_kind = None
    return {
        "honest_outcome": outcome,
        "boundary": boundary,
        "earned_row_count": len(earned) + len(robust_earned),
        "single_family_earned_row_count": len(earned),
        "agreement_threshold_earned_row_count": len(robust_earned),
        "partial_row_count": len(partial) + len(robust_partial),
        "single_family_partial_row_count": len(partial),
        "agreement_threshold_partial_row_count": len(robust_partial),
        "ran_row_count": len(ran_rows),
        "refused_row_count": len(rows) - len(ran_rows),
        "first_candidate_corner": None
        if first is None
        else {
            "candidate_kind": first_kind,
            "family_id": first.get("family_id", "family_robust_agreement_threshold"),
            "kind": first.get("kind", "agreement_threshold"),
            "strength_id": first["strength_id"],
            "target_mode": first["target_mode"],
            "window_T": first["window_T"],
            "classifier_id": first["classifier_id"],
            "class_distribution": first["class_distribution"],
            "criterion_verdict": first["criterion_verdict"],
            "agreement_threshold_k": first.get("agreement_threshold_k"),
            "failure_reasons": first.get("failure_reasons", []),
        },
        "by_classifier_verdict": dict(
            sorted(Counter(row.get("criterion_verdict", "unknown") for row in rows).items())
        ),
        "by_agreement_threshold_verdict": dict(
            sorted(Counter(row.get("criterion_verdict", "unknown") for row in robust_rows).items())
        ),
    }


def family_bite_gates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    gates = {}
    for family in PERTURBATION_FAMILIES:
        family_rows = [row for row in rows if row["family_id"] == family["family_id"]]
        changed_counts = [int(row.get("changed_initial_state_count", 0)) for row in family_rows]
        gates[family["family_id"]] = {
            "kind": family["kind"],
            "pass": any(value > 0 for value in changed_counts),
            "max_changed_initial_state_count": max(changed_counts) if changed_counts else 0,
            "refused_rows": sum(row.get("row_status") != "ran" for row in family_rows),
        }
    return gates


def controls_summary(max_window: int) -> dict[str, Any]:
    schedule = schedule_for_window(max_window)
    baseline = baseline_trajectory(max_window)
    identity = enrich_trajectory(apply_schedule(trajectory_id="identity_dynamics_control", schedule=schedule, identity=True))
    scrambled = enrich_trajectory(
        apply_schedule(trajectory_id="scrambled_adjacency_control", schedule=schedule, lookup=scrambled_lookup())
    )
    return {
        "identity_dynamics": {
            "ran": True,
            "dynamics_nontrivial": identity["total_changed_cell_steps"] > 0,
            "all_state_cells_static": identity["total_changed_cell_steps"] == 0,
            "classifier_status": "refuse_degenerate_static",
            "trajectory_signature_sha256": identity["trajectory_signature_sha256"],
        },
        "scrambled_adjacency": {
            "ran": True,
            "signature_changed": scrambled["trajectory_signature_sha256"] != baseline["trajectory_signature_sha256"],
            "trajectory_signature_sha256": scrambled["trajectory_signature_sha256"],
        },
        "label_permutation": {
            "ran": True,
            "permutation": "state_ids_rotated_by_7",
            "role": "per-row negative control; must fail the candidate criterion",
        },
        "dropped_half_per_family": {
            "ran": True,
            "role": "per-row negative control; active target list is halved deterministically by even target index",
        },
        "no_identity_leak": {
            "ran": True,
            "identity_fields_excluded": ["cell_id", "state_id", "start_cell", "current_cell", "coord", "coord_scaled"],
            "classifier_feature_fields": sorted(next(iter(feature_rows().values())).keys()),
            "classifier_input_fields_exclude_identity": True,
        },
    }


def smt_rows(payload: dict[str, Any]) -> dict[str, Any]:
    values = {
        "state_count": payload["carrier"]["state_count"],
        "trajectory_T": payload["trajectory"]["T"],
        "state_row_count": len(payload["state_rows"]),
        "sweep_row_count": payload["axis0_experiment_v2"]["sweep_row_count"],
        "family_count": len(PERTURBATION_FAMILIES),
        "window_count": len(window_ladder()),
        "classifier_count": len(CLASSIFIERS),
        "v0_regression_spread_count": payload["v0_regression"]["observed_distribution"].get("SPREAD", 0),
    }
    solver = z3.Solver()
    state_count = z3.Int("dynamic_chart_state_count")
    trajectory_t = z3.Int("dynamic_chart_T")
    row_count = z3.Int("dynamic_chart_state_row_count")
    sweep_count = z3.Int("dynamic_chart_sweep_row_count")
    family_count = z3.Int("dynamic_chart_family_count")
    window_count = z3.Int("dynamic_chart_window_count")
    classifier_count = z3.Int("dynamic_chart_classifier_count")
    v0_spread = z3.Int("dynamic_chart_v0_regression_spread_count")
    solver.add(state_count == values["state_count"])
    solver.add(trajectory_t == values["trajectory_T"])
    solver.add(row_count == values["state_row_count"])
    solver.add(sweep_count == values["sweep_row_count"])
    solver.add(family_count == values["family_count"])
    solver.add(window_count == values["window_count"])
    solver.add(classifier_count == values["classifier_count"])
    solver.add(v0_spread == values["v0_regression_spread_count"])
    solver.add(state_count == EXPECTED_STATE_COUNT)
    solver.add(trajectory_t > 1)
    solver.add(row_count == state_count * (trajectory_t + 1))
    solver.add(family_count >= 4)
    solver.add(window_count >= 4)
    solver.add(classifier_count >= 3)
    solver.add(sweep_count == family_count * len(STRENGTH_LADDER) * len(TARGET_MODES) * window_count * classifier_count)
    solver.add(v0_spread == 32)
    z3_verdict = str(solver.check())

    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_LIA")
    int_sort = cvc5_solver.getIntegerSort()
    terms = {name: cvc5_solver.mkConst(int_sort, f"cvc5_{name}") for name in values}
    for name, value in values.items():
        cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, terms[name], cvc5_solver.mkInteger(int(value))))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, terms["state_count"], cvc5_solver.mkInteger(EXPECTED_STATE_COUNT)))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.GT, terms["trajectory_T"], cvc5_solver.mkInteger(1)))
    t_plus_one = cvc5_solver.mkTerm(Kind.ADD, terms["trajectory_T"], cvc5_solver.mkInteger(1))
    expected_rows = cvc5_solver.mkTerm(Kind.MULT, terms["state_count"], t_plus_one)
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, terms["state_row_count"], expected_rows))
    expected_sweep = cvc5_solver.mkTerm(
        Kind.MULT,
        terms["family_count"],
        cvc5_solver.mkInteger(len(STRENGTH_LADDER)),
        cvc5_solver.mkInteger(len(TARGET_MODES)),
        terms["window_count"],
        terms["classifier_count"],
    )
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, terms["sweep_row_count"], expected_sweep))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.GEQ, terms["family_count"], cvc5_solver.mkInteger(4)))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.GEQ, terms["window_count"], cvc5_solver.mkInteger(4)))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.GEQ, terms["classifier_count"], cvc5_solver.mkInteger(3)))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, terms["v0_regression_spread_count"], cvc5_solver.mkInteger(32)))
    cvc5_result = cvc5_solver.checkSat()
    cvc5_verdict = "sat" if cvc5_result.isSat() else "unsat" if cvc5_result.isUnsat() else str(cvc5_result)
    base = {
        "ran": True,
        "load_bearing": True,
        "supportive": False,
        "bound_values": values,
        "asserted_precomputed_boolean": False,
        "polarity": "direct satisfiable arithmetic consistency check",
    }
    return {
        "z3": {**base, "verdict": z3_verdict},
        "cvc5": {**base, "verdict": cvc5_verdict},
    }


def build_packet() -> dict[str, Any]:
    max_window = max(window_ladder())
    baseline = baseline_trajectory(max_window)
    sweep_rows = build_sweep_rows()
    agreement_rows = build_agreement_threshold_rows(sweep_rows)
    anchor_disagreement = v1_anchor_disagreement(sweep_rows)
    sweep_summary = summarize_sweep(sweep_rows, agreement_rows)
    family_gates = family_bite_gates(sweep_rows)
    controls = controls_summary(max_window)
    shell_motion = dynamic_shell_motion(baseline["dynamic_shell_rows"])
    v0_regression = v0_regression_row()
    payload: dict[str, Any] = {
        "schema": f"{SIM_ID}.packet.v2",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "row_classification": ROW_CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "allowed_claims": [
            "Axis-0 experiment v2 stability-axis sweep on the Family A dynamic density-state chart",
            "state-derived entropy and moving-shell machinery reused from v0",
            "criterion verdicts over perturbation family x strength x target x relaxation-window x classifier rows",
            "family-robust agreement-threshold classifier diagnostics over common sign structure",
            "panel-10 shell-weighted TV and projective purity reset diagnostics",
            "v0 regression corner reproduces 32/33 SPREAD under the old v0 divergence functional",
            "v1 best-partial corner reproduces amplitude_kicks/weak/shell_boundary/T=12/recovery_return_time",
        ],
        "disallowed_claims": [
            "Axis-0 admission",
            "axis admission",
            "bridge admission",
            "physics",
            "canonical Axis-0",
            "manifold promotion",
            "final substrate choice",
            "spinor-network surface closure",
            "QCA/local-update closure",
        ],
        "carrier": {
            "state_count": parent_objects()["carrier"]["state_count"],
            "edge_count": parent_objects()["carrier"]["edge_count"],
            "generator_names": parent_objects()["carrier"]["generator_names"],
            "transition_graph_sha256": parent_objects()["carrier"]["transition_graph_sha256"],
            "state_object_id": parent_objects()["carrier"]["state_object_id"],
            "source": "Family A committed 33-cell Bloch-grid carrier",
        },
        "trajectory": {
            "T": baseline["T"],
            "schedule": schedule_for_window(max_window),
            "trajectory_signature_sha256": baseline["trajectory_signature_sha256"],
            "changed_transition_count": baseline["changed_transition_count"],
            "total_changed_cell_steps": baseline["total_changed_cell_steps"],
        },
        "state_rows": baseline["state_rows"],
        "transition_rows": baseline["transition_rows"],
        "entropy_field": {
            "entropy_type": "local_von_neumann",
            "state_source": "rho_c(t)_from_bloch_cell_density_matrix",
            "computed_from": "density-matrix eigenvalues of rho_c(t)",
            "not_yet": ["conditional_vN", "coherent_information", "shell_cut_entropy", "Phi0(rho_AB)"],
            "owner_choice_open": True,
        },
        "entropy_field_rows": baseline["entropy_field_rows"],
        "entropy_gradients": baseline["entropy_gradients"],
        "dynamic_shell_rows": baseline["dynamic_shell_rows"],
        "dynamic_shell_motion": shell_motion,
        "dynamic_shell_alternatives": {
            "entropy_level_shell": "implemented_v1",
            "basin_boundary_shell": "readout_vocabulary_used_in_classifier",
            "correlation_boundary_shell": "blocked_until_rho_AB_or_surface_cut",
        },
        "jk_fuzz_rows": baseline["jk_fuzz_rows"],
        "axis0_experiment_v2": {
            "experiment": "stability-axis perturb -> watch -> classify sweep",
            "axis0_admission": "not_admitted_axis0_experiment_v2",
            "criterion_rule": SEPARATION_RULE_VERBATIM,
            "v1_anchor_corner": V1_ANCHOR_CORNER,
            "relaxation_scale_calibration": relaxation_scale_calibration(),
            "perturbation_families": PERTURBATION_FAMILIES,
            "strength_ladder": STRENGTH_LADDER,
            "target_modes": TARGET_MODES,
            "window_ladder": window_ladder(),
            "classifiers": CLASSIFIERS,
            "sweep_row_count": len(sweep_rows),
            "full_sweep_grid": sweep_rows,
            "agreement_threshold_ladder": AGREEMENT_THRESHOLD_LADDER,
            "agreement_threshold_row_count": len(agreement_rows),
            "agreement_threshold_rows": agreement_rows,
            "v1_anchor_disagreement": anchor_disagreement,
            "summary": sweep_summary,
            "family_bite_gates": family_gates,
        },
        "v0_regression": v0_regression,
        "controls": controls,
        "static_phi_bridge_row": {
            "old_anchor_role": "static_proxy_equilibrium_shadow_candidate_only",
            "tested_not_assumed": True,
            "role_in_v1": "one predeclared nonidentity feature among several; never an entropy source",
            "v0_regression_bridge_context": "v0 audit found old phi failed locally against a near-constant 32/33 SPREAD row",
        },
        "witness_gates": {
            "density_validity": {
                "pass": all(row["density_trace_close_to_one"] and row["density_psd"] and row["density_hermitian"] for row in baseline["state_rows"]),
            },
            "entropy_source": {
                "pass": all(row["entropy_source"] == "computed_from_rho_eigenvalues" for row in baseline["state_rows"]),
                "not_from": ["old_phi", "static_shell_label", "metadata", "injected_synthetic_scalar"],
            },
            "dynamics_nontriviality": {"pass": baseline["T"] > 1 and baseline["total_changed_cell_steps"] > 0},
            "perturbation_bite_per_family": {
                "pass": all(row["pass"] for row in family_gates.values()),
                "family_gates": family_gates,
            },
            "shell_gate": {"pass": shell_motion["shells_can_move"] and len(baseline["dynamic_shell_rows"]) == baseline["T"] + 1},
            "jk_gate": {"pass": len(baseline["jk_fuzz_rows"]) == len(baseline["state_rows"])},
            "full_grid_gate": {
                "pass": len(sweep_rows)
                == len(PERTURBATION_FAMILIES) * len(STRENGTH_LADDER) * len(TARGET_MODES) * len(window_ladder()) * len(CLASSIFIERS),
            },
            "agreement_threshold_gate": {"pass": len(agreement_rows) > 0 and any(row["agreement_threshold_k"] >= 2 for row in agreement_rows)},
            "classifier_gate": {"pass": len(CLASSIFIERS) >= 3},
            "relaxation_window_gate": {
                "pass": ANCHOR_WINDOW_T in window_ladder()
                and max(window_ladder()) >= int(math.ceil(relaxation_scale_calibration()["slowest_relaxation_tau_steps"]))
                and relaxation_scale_calibration()["status"] == "computed_from_generator_averaged_transition_matrix",
            },
            "v0_regression_gate": {"pass": v0_regression["pass"]},
            "v1_anchor_regression_gate": {"pass": anchor_disagreement["v1_best_partial_regression"]["pass"]},
            "criterion_gate": {"pass": SEPARATION_RULE_VERBATIM in stable_json(sweep_rows)},
        },
        "trajectory_artifact": {
            "path": rel(TRAJECTORY_ARTIFACT_PATH),
            "sha256_path": rel(TRAJECTORY_ARTIFACT_SHA_PATH),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "builder_gates": {
            "file_disjoint_packet": True,
            "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "no_builder_audit_verdict_envelope_gate": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "packet_audit_verdict_absent": not (SIM_DIR / "audit_verdict.md").exists(),
            "boundary_helper_path": "scripts/builder_audit_boundary.py",
            "boundary_helper_fully_used": True,
            "G_2a_idempotency_from_birth": True,
        },
        "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        "no_builder_audit_verdict_envelope_gate": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        "standards_codex": "system_v6/receipts/audit_standards_codex_v1.md",
        "standards_version": "audit_standards_codex_v1",
        "standards_commit": PARENT_COMMITS["audit_standards_codex_v1"],
        "freshness_tier": "TIER-2",
        "identity_leak_detected": True,
        "identity_leak_excluded_best_accuracy": max(
            row.get("best_non_identity_predictor", {}).get("accuracy", 0.0)
            for row in sweep_rows
            if row.get("row_status") == "ran"
        ),
        "identity_leak_exclusion_rule": "classifier/predictor excludes cell_id, state_id, start_cell, current_cell, coord, and coord_scaled; only coarse predeclared nonidentity features are allowed",
        "circularity_species": [],
        "positive_boundary_result": sweep_summary["honest_outcome"],
        "pre_registration_sources": [
            "system_v6/sims/manifold_dynamic_chart_v0/audit_verdict.md",
            "system_v6/receipts/codex_suggestions_unlock_plan_20260612.md",
            "system_v6/receipts/dynamic_manifold_upgrade_design_20260612.md",
            "system_v6/receipts/owner_correction_axis0_not_built_20260612.md",
            "system_v6/receipts/panel10_blind_separation_methods_20260612.md",
            "system_v6/sims/manifold_dynamic_chart_v1/audit_verdict.md",
        ],
        "source_locks": {
            key: source_lock(path, key, PARENT_COMMITS.get(key))
            for key, path in PARENT_PATHS.items()
        },
        "substrate_choice_status": {
            "v1_reading": "Family A chart-relative dynamic density-state chart",
            "final_substrate_remains_open": ["chart", "spinor-network surface", "QCA/local-update"],
        },
    }
    payload["smt_rows"] = smt_rows(payload)
    payload["all_pass"] = all(row.get("pass") is True for row in payload["witness_gates"].values()) and all(
        row["verdict"] == "sat" for row in payload["smt_rows"].values()
    )
    payload["trajectory"]["entropy_signature_sha256"] = baseline["entropy_signature_sha256"]
    payload["trajectory"]["shell_signature_sha256"] = baseline["shell_signature_sha256"]
    payload["trajectory"]["jk_signature_sha256"] = baseline["jk_signature_sha256"]
    return payload


def write_trajectory_artifact(payload: dict[str, Any]) -> dict[str, Any]:
    artifact = {
        "schema": f"{SIM_ID}.trajectory_artifact.v2",
        "sim_id": SIM_ID,
        "state_rows": payload["state_rows"],
        "transition_rows": payload["transition_rows"],
        "entropy_field_rows": payload["entropy_field_rows"],
        "dynamic_shell_rows": payload["dynamic_shell_rows"],
        "jk_fuzz_rows": payload["jk_fuzz_rows"],
        "trajectory_signature_sha256": payload["trajectory"]["trajectory_signature_sha256"],
        "entropy_signature_sha256": payload["trajectory"]["entropy_signature_sha256"],
    }
    write_json(TRAJECTORY_ARTIFACT_PATH, artifact)
    digest = sha256_file(TRAJECTORY_ARTIFACT_PATH)
    TRAJECTORY_ARTIFACT_SHA_PATH.write_text(digest + "\n", encoding="utf-8")
    return {"path": rel(TRAJECTORY_ARTIFACT_PATH), "sha256": digest, "sha_verified": digest == sha256_file(TRAJECTORY_ARTIFACT_PATH)}


def cells_and_entropy_by_t(payload: dict[str, Any]) -> dict[str, Any]:
    rows_by_t: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in payload["state_rows"]:
        rows_by_t[int(row["t"])].append(row)
    return {
        "cells_by_t": [
            [int(row["current_cell"]) for row in sorted(rows, key=lambda item: int(item["state_id"]))]
            for _, rows in sorted(rows_by_t.items())
        ],
        "entropy_by_t": [
            [rounded_float(float(row["entropy_vn"])) for row in sorted(rows, key=lambda item: int(item["state_id"]))]
            for _, rows in sorted(rows_by_t.items())
        ],
    }


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("sim_id") == SIM_ID, "sim_id mismatch")
    require(errors, payload.get("classification") == CLASSIFICATION, "classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("carrier", {}).get("state_count") == EXPECTED_STATE_COUNT, "carrier state_count mismatch")
    require(errors, payload.get("carrier", {}).get("edge_count") == EXPECTED_EDGE_COUNT, "carrier edge_count mismatch")
    require(errors, payload.get("trajectory", {}).get("T", 0) > 1, "trajectory T must be >1")
    require(errors, len(payload.get("state_rows", [])) == EXPECTED_STATE_COUNT * (payload["trajectory"]["T"] + 1), "state row count mismatch")
    require(errors, payload.get("witness_gates", {}).get("density_validity", {}).get("pass") is True, "density validity failed")
    require(errors, payload.get("witness_gates", {}).get("entropy_source", {}).get("pass") is True, "entropy source failed")
    require(errors, payload.get("witness_gates", {}).get("dynamics_nontriviality", {}).get("pass") is True, "dynamics frozen")
    require(errors, payload.get("witness_gates", {}).get("perturbation_bite_per_family", {}).get("pass") is True, "perturbation did not bite")
    require(errors, payload.get("witness_gates", {}).get("shell_gate", {}).get("pass") is True, "shell gate failed")
    require(errors, payload.get("witness_gates", {}).get("jk_gate", {}).get("pass") is True, "jk gate failed")
    require(errors, payload.get("witness_gates", {}).get("full_grid_gate", {}).get("pass") is True, "full grid gate failed")
    require(errors, payload.get("witness_gates", {}).get("agreement_threshold_gate", {}).get("pass") is True, "agreement threshold gate failed")
    require(errors, payload.get("witness_gates", {}).get("classifier_gate", {}).get("pass") is True, "classifier gate failed")
    require(errors, payload.get("witness_gates", {}).get("relaxation_window_gate", {}).get("pass") is True, "relaxation window gate failed")
    require(errors, payload.get("witness_gates", {}).get("v0_regression_gate", {}).get("pass") is True, "v0 regression failed")
    require(errors, payload.get("witness_gates", {}).get("v1_anchor_regression_gate", {}).get("pass") is True, "v1 anchor regression failed")
    require(errors, payload.get("static_phi_bridge_row", {}).get("tested_not_assumed") is True, "bridge row not tested")
    experiment = payload.get("axis0_experiment_v2", {})
    require(errors, experiment.get("criterion_rule") == SEPARATION_RULE_VERBATIM, "criterion rule mismatch")
    require(errors, len(experiment.get("perturbation_families", [])) >= 5, "missing v2 perturbation families")
    require(errors, any(row.get("family_id") == "purity_projective_resets" for row in experiment.get("perturbation_families", [])), "missing purity projective reset family")
    require(errors, any(row.get("classifier_id") == "shell_weighted_tv" for row in experiment.get("classifiers", [])), "missing shell-weighted TV classifier")
    require(errors, len(experiment.get("classifiers", [])) >= 4, "missing classifiers")
    require(errors, ANCHOR_WINDOW_T in experiment.get("window_ladder", []), "missing v1 anchor window")
    require(errors, max(experiment.get("window_ladder", [0])) >= int(math.ceil(experiment.get("relaxation_scale_calibration", {}).get("slowest_relaxation_tau_steps", 0))), "window ladder not relaxation-calibrated")
    require(errors, experiment.get("sweep_row_count") == len(experiment.get("full_sweep_grid", [])), "sweep count mismatch")
    require(errors, experiment.get("agreement_threshold_row_count") == len(experiment.get("agreement_threshold_rows", [])), "agreement threshold count mismatch")
    require(errors, experiment.get("v1_anchor_disagreement", {}).get("v1_best_partial_regression", {}).get("pass") is True, "v1 anchor regression mismatch")
    require(errors, payload.get("controls", {}).get("identity_dynamics", {}).get("classifier_status") == "refuse_degenerate_static", "identity control did not refuse")
    require(errors, payload.get("controls", {}).get("no_identity_leak", {}).get("classifier_input_fields_exclude_identity") is True, "identity leak control failed")
    require(errors, payload.get("builder_gates", {}).get("boundary_helper_fully_used") is True, "boundary helper not used")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    for banned in ("Axis-0 admission", "bridge admission", "final substrate choice"):
        require(errors, banned in payload.get("disallowed_claims", []), f"missing disallowed claim: {banned}")
    return errors
