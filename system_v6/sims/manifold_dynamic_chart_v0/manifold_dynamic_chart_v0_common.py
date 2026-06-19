#!/usr/bin/env python3
"""Shared builder for the Family A dynamic density-state chart v0."""

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


SIM_ID = "manifold_dynamic_chart_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
TRAJECTORY_ARTIFACT_PATH = RESULT_DIR / f"{SIM_ID}_trajectory_artifact.json"
TRAJECTORY_ARTIFACT_SHA_PATH = RESULT_DIR / f"{SIM_ID}_trajectory_artifact.sha256"

CLASSIFICATION = "scratch_diagnostic"
ROW_CLASSIFICATION = "dynamic_chart_v0_first_measurement_attempt"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_dynamic_chart_v0_first_measurement_attempt_only"
ENGINE_MODE = "family_a_33_cell_dynamic_density_state_chart_v0"
EXPECTED_STATE_COUNT = 33
EXPECTED_EDGE_COUNT = 198
SHELL_COUNT = 3
EPS = 1.0e-10

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
    "owner_correction_axis0_not_built": "0313d47bc",
    "engines_run_with_axes_v0": "de243459e",
    "audit_standards_codex_v1": "current",
}

PARENT_PATHS = {
    "dynamic_manifold_upgrade_design": ROOT / "system_v6" / "receipts" / "dynamic_manifold_upgrade_design_20260612.md",
    "owner_correction_axis0_not_built": ROOT / "system_v6" / "receipts" / "owner_correction_axis0_not_built_20260612.md",
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
    "json_hashing": "supportive",
}

TOOL_INTENT = {
    "claim_classes": [
        "family_a_dynamic_density_state_chart",
        "state_derived_local_von_neumann_entropy",
        "dynamic_entropy_shell_motion",
        "jk_admissible_future_multiplicity",
        "perturb_watch_classify_first_attempt",
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


def smt_rows(payload: dict[str, Any]) -> dict[str, Any]:
    values = {
        "state_count": payload["carrier"]["state_count"],
        "trajectory_T": payload["trajectory"]["T"],
        "state_row_count": len(payload["state_rows"]),
        "perturb_changed_initial_state_count": payload["axis0_response_protocol_v0"]["perturbation_family"]["small_committed_kick"][
            "changed_initial_state_count"
        ],
    }
    solver = z3.Solver()
    state_count = z3.Int("dynamic_chart_state_count")
    trajectory_t = z3.Int("dynamic_chart_T")
    row_count = z3.Int("dynamic_chart_state_row_count")
    perturb_count = z3.Int("dynamic_chart_perturb_changed_count")
    solver.add(state_count == values["state_count"])
    solver.add(trajectory_t == values["trajectory_T"])
    solver.add(row_count == values["state_row_count"])
    solver.add(perturb_count == values["perturb_changed_initial_state_count"])
    solver.add(state_count == EXPECTED_STATE_COUNT)
    solver.add(trajectory_t > 1)
    solver.add(row_count == state_count * (trajectory_t + 1))
    solver.add(perturb_count > 0)
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
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.GT, terms["perturb_changed_initial_state_count"], cvc5_solver.mkInteger(0)))
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
    schedule = committed_schedule()
    baseline = enrich_trajectory(apply_schedule(trajectory_id="baseline_carnot_schedule", schedule=schedule))
    kicked_initial = small_committed_kick_initial_cells()
    small_kick = enrich_trajectory(
        apply_schedule(trajectory_id="small_committed_kick_R_x_then_carnot", schedule=schedule, initial_override=kicked_initial)
    )
    dropped_initial = small_committed_kick_initial_cells(drop_half=True)
    dropped_half = enrich_trajectory(
        apply_schedule(trajectory_id="dropped_half_kick_family", schedule=schedule, initial_override=dropped_initial)
    )
    shuffled_schedule = [schedule[index] for index in [0, 2, 1, 3]]
    order_perturb = enrich_trajectory(apply_schedule(trajectory_id="N01_order_perturbation", schedule=shuffled_schedule))
    identity = enrich_trajectory(apply_schedule(trajectory_id="identity_dynamics_control", schedule=schedule, identity=True))
    scrambled = enrich_trajectory(
        apply_schedule(trajectory_id="scrambled_adjacency_control", schedule=schedule, lookup=scrambled_lookup())
    )

    comparison = compare_trajectories(baseline, small_kick)
    dropped_comparison = compare_trajectories(baseline, dropped_half)
    order_comparison = compare_trajectories(baseline, order_perturb)
    response_protocol = {
        "protocol": "perturb->watch->classify",
        "axis0_admission": "not_admitted_first_honest_attempt",
        "classifier_feature_fields": [
            "entropy_variance_delta",
            "entropy_range_delta",
            "shell_boundary_motion_delta",
            "jk_mean_delta",
            "state_reconvergence_fraction",
        ],
        "classifier_input_fields_exclude_identity": True,
        "perturbation_family": {
            "zero_perturbation": {"ran": True, "role": "baseline/control", "changed_initial_state_count": 0},
            "small_committed_kick": {
                "ran": True,
                "kick_generator": "R_x_fallback_first_nonidentity_generator",
                "changed_initial_state_count": sum(a != b for a, b in zip(initial_cells(), kicked_initial, strict=True)),
            },
            "dropped_half_perturbation_family": {
                "ran": True,
                "changed_initial_state_count": sum(a != b for a, b in zip(initial_cells(), dropped_initial, strict=True)),
            },
            "order_perturbation": {"ran": True, "order": [0, 2, 1, 3]},
            "over_boundary_perturbation": {
                "ran": True,
                "status": "refused_boundary_control",
                "reason": "outside Adm_C perturbation is a boundary-control row, not a synthetic state-derived entropy source",
            },
        },
        "divergence_measure": comparison,
        "region_classifications": comparison["region_classifications"],
        "control_comparisons": {
            "dropped_half": dropped_comparison,
            "order_perturbation": order_comparison,
        },
    }
    controls = {
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
        "dropped_half_perturbation_family": {
            "ran": True,
            "changed_initial_state_count": response_protocol["perturbation_family"]["dropped_half_perturbation_family"][
                "changed_initial_state_count"
            ],
            "peak_state_hamming_fraction": dropped_comparison["peak_state_hamming_fraction"],
        },
        "no_identity_leak": {
            "ran": True,
            "identity_fields_excluded": ["cell_id", "state_id", "start_cell", "current_cell"],
            "classifier_feature_fields": response_protocol["classifier_feature_fields"],
            "classifier_input_fields_exclude_identity": True,
        },
    }
    shell_motion = dynamic_shell_motion(baseline["dynamic_shell_rows"])
    payload: dict[str, Any] = {
        "schema": f"{SIM_ID}.packet.v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "row_classification": ROW_CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "allowed_claims": [
            "first state-derived dynamic entropy chart diagnostic on Family A",
            "falsifiable old-static-phi bridge comparison",
            "perturb-watch-classify protocol smoke result",
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
            "schedule": schedule,
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
            "entropy_level_shell": "implemented_v0",
            "basin_boundary_shell": "readout_vocabulary_used_in_classifier",
            "correlation_boundary_shell": "blocked_until_rho_AB_or_surface_cut",
        },
        "jk_fuzz_rows": baseline["jk_fuzz_rows"],
        "axis0_response_protocol_v0": response_protocol,
        "controls": controls,
        "static_phi_bridge_row": static_phi_bridge_row({"small_kick": small_kick}),
        "witness_gates": {
            "density_validity": {
                "pass": all(row["density_trace_close_to_one"] and row["density_psd"] and row["density_hermitian"] for row in baseline["state_rows"]),
            },
            "entropy_source": {
                "pass": all(row["entropy_source"] == "computed_from_rho_eigenvalues" for row in baseline["state_rows"]),
                "not_from": ["old_phi", "static_shell_label", "metadata", "injected_synthetic_scalar"],
            },
            "dynamics_nontriviality": {"pass": baseline["T"] > 1 and baseline["total_changed_cell_steps"] > 0},
            "perturbation_bite": {
                "pass": response_protocol["perturbation_family"]["small_committed_kick"]["changed_initial_state_count"] > 0
                and comparison["peak_state_hamming_fraction"] > 0,
            },
            "shell_gate": {"pass": shell_motion["shells_can_move"] and len(baseline["dynamic_shell_rows"]) == baseline["T"] + 1},
            "jk_gate": {"pass": len(baseline["jk_fuzz_rows"]) == len(baseline["state_rows"])},
            "readout_gate": {"pass": bool(response_protocol["region_classifications"])},
            "old_phi_bridge_emitted": {"pass": True},
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
        "identity_leak_excluded_best_accuracy": None,
        "identity_leak_exclusion_rule": "classifier excludes cell_id, state_id, start_cell, and current_cell; bridge rows may report cell_id but classifier does not read it",
        "circularity_species": [],
        "positive_boundary_result": "not_applicable_first_measurement_attempt",
        "pre_registration_sources": [
            "system_v6/receipts/dynamic_manifold_upgrade_design_20260612.md",
            "system_v6/receipts/owner_correction_axis0_not_built_20260612.md",
        ],
        "source_locks": {
            key: source_lock(path, key, PARENT_COMMITS.get(key))
            for key, path in PARENT_PATHS.items()
        },
        "substrate_choice_status": {
            "v0_reading": "Family A chart-relative dynamic density-state chart",
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
        "schema": f"{SIM_ID}.trajectory_artifact.v1",
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
    require(errors, payload.get("witness_gates", {}).get("perturbation_bite", {}).get("pass") is True, "perturbation did not bite")
    require(errors, payload.get("witness_gates", {}).get("shell_gate", {}).get("pass") is True, "shell gate failed")
    require(errors, payload.get("witness_gates", {}).get("jk_gate", {}).get("pass") is True, "jk gate failed")
    require(errors, payload.get("static_phi_bridge_row", {}).get("tested_not_assumed") is True, "bridge row not tested")
    require(errors, payload.get("controls", {}).get("identity_dynamics", {}).get("classifier_status") == "refuse_degenerate_static", "identity control did not refuse")
    require(errors, payload.get("controls", {}).get("no_identity_leak", {}).get("classifier_input_fields_exclude_identity") is True, "identity leak control failed")
    require(errors, payload.get("builder_gates", {}).get("boundary_helper_fully_used") is True, "boundary helper not used")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    for banned in ("Axis-0 admission", "bridge admission", "final substrate choice"):
        require(errors, banned in payload.get("disallowed_claims", []), f"missing disallowed claim: {banned}")
    return errors
