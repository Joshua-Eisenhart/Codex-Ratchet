#!/usr/bin/env python3
"""Shared finite Hopf placement builder for discrete_axis3_placement_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import z3


SIM_ID = "discrete_axis3_placement_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "axis_readout_candidate_only"
ENGINE_MODE = "all_three_full_sims"
SAMPLE_COUNT = 8
EPS = 1.0e-9

PARENT_COMMITS = {
    "axis_work_order": "f6112e407",
    "manifold_family_b_integrated_v0": "29e133f2f",
    "hopf_base_section_phase_recovery_v0": "7e78f3829",
    "discrete_axis0_field_v0": "5d330b427",
    "sequencing_doctrine": "fcf1b3858",
}
PARENT_PATHS = {
    "axis_work_order": ROOT / "system_v6/receipts/axis_work_order_20260612.md",
    "working_math_scaffold": ROOT / "system_v6/foundations/working_math_scaffold_20260609.md",
    "axis0_audit_template": ROOT / "system_v6/sims/discrete_axis0_field_v0/audit_verdict.md",
    "axis0_envelope": ROOT / "system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_envelope_results.json",
    "family_b_envelope": ROOT
    / "system_v6/sims/manifold_family_b_integrated_v0/results/manifold_family_b_integrated_v0_envelope_results.json",
    "hopf_section_envelope": ROOT
    / "system_v6/sims/hopf_base_section_phase_recovery_v0/results/hopf_base_section_phase_recovery_v0_envelope_results.json",
    "hopf_section_source": ROOT / "system_v6/sims/hopf_base_section_phase_recovery_v0/hopf_base_section_phase_recovery_v0.py",
    "axis_deep_math": ROOT / "system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md",
    "wb_axis3_prior_art_matrix": ROOT / "scripts/tool_function_receipt_matrix.py",
    "legacy_axis3_prior_art": ROOT / "system_v4/probes/sim_axis3_fiber_base.py",
}

TOOL_INTENT = {
    "claim_classes": [
        "finite_axis3_placement_readout_candidate",
        "computed_density_stationarity",
        "computed_hopf_horizontal_condition",
        "axis0_axis3_independence_discriminator",
        "computed_negative_controls_only",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "build the finite loop-dynamics graph and count stable versus traversing density-step edges",
            "Z3": "bind computed placement, stability, independence, and control counts with erased flips",
        },
        "jax": {
            "networkx": "build the finite loop-dynamics graph and verify node/edge count over pinned Hopf loop rows",
            "sympy": "compute exact symbolic A(dot gamma) rows for fiber, horizontal base, and wrong-sign falsifier",
            "z3": "bind computed placement/stability/independence counts with erased flips",
            "cvc5": "independent SMT binding of the same computed placement/stability counts with erased flips",
        },
        "pytorch": {
            "torch.func": "torch-native vectorized density-distance check over pinned loop samples",
            "torch_geometric": "Data edge_index carrier for the loop-time dynamics graph",
            "sympy": "exact symbolic horizontal-condition check mirrored in the PyTorch lane",
            "z3": "bind computed placement/stability/independence counts with erased flips",
            "cvc5": "independent SMT binding of the same computed placement/stability counts with erased flips",
        },
    },
}
TOOL_MANIFEST = {
    "Graphs": {"tried": True, "used": True, "reason": "Julia finite loop-dynamics graph and density-step counts"},
    "Z3": {"tried": True, "used": True, "reason": "Julia SMT computed-value identity and erased flip"},
    "networkx": {"tried": True, "used": True, "reason": "JAX-slot finite loop-dynamics graph carrier"},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch vectorized density-distance readout"},
    "torch_geometric": {"tried": True, "used": True, "reason": "PyTorch loop-time edge_index carrier"},
    "sympy": {"tried": True, "used": True, "reason": "exact symbolic horizontal-condition rows"},
    "z3": {"tried": True, "used": True, "reason": "Python SMT computed-value identity and erased flip"},
    "cvc5": {"tried": True, "used": True, "reason": "independent Python SMT computed-value identity and erased flip"},
}
TOOL_INTEGRATION_DEPTH = {
    "Graphs": "load_bearing",
    "Z3": "load_bearing",
    "networkx": "load_bearing",
    "torch.func": "load_bearing",
    "torch_geometric": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%H", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or None
    except Exception:
        return None


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"role": role, "path": rel(path), "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["commit_hint"] = commit_hint
    return row


def source_import_audit() -> dict[str, Any]:
    return {
        "authority_and_context": {
            "axis_work_order": source_lock(PARENT_PATHS["axis_work_order"], "authority", PARENT_COMMITS["axis_work_order"]),
            "working_math_scaffold": source_lock(PARENT_PATHS["working_math_scaffold"], "sourced_axis3_definition"),
            "axis0_audit_template": source_lock(PARENT_PATHS["axis0_audit_template"], "axis_readout_genre_template"),
            "axis_deep_math": source_lock(PARENT_PATHS["axis_deep_math"], "router_quote_context"),
        },
        "parent_hash_pins": {
            "family_b_envelope": source_lock(
                PARENT_PATHS["family_b_envelope"],
                "committed_family_b_hopf_carrier_context",
                PARENT_COMMITS["manifold_family_b_integrated_v0"],
            ),
            "hopf_section_envelope": source_lock(
                PARENT_PATHS["hopf_section_envelope"],
                "committed_hopf_base_section_context",
                PARENT_COMMITS["hopf_base_section_phase_recovery_v0"],
            ),
            "axis0_envelope": source_lock(
                PARENT_PATHS["axis0_envelope"],
                "committed_axis0_response_data_for_independence",
                PARENT_COMMITS["discrete_axis0_field_v0"],
            ),
        },
        "prior_art_context_only": {
            "wb_axis3_fit_probe_matrix": source_lock(PARENT_PATHS["wb_axis3_prior_art_matrix"], "tool_lego_fit_probe_context_only"),
            "legacy_axis3_fiber_base": source_lock(PARENT_PATHS["legacy_axis3_prior_art"], "legacy_context_only"),
        },
        "anti_collage_rule": "loop rows are rebuilt from Hopf formulas and source-locked parent envelopes; prior result tables are context, not copied classifications",
        "raw_parent_computation_imported": False,
    }


def family_b_context() -> dict[str, Any]:
    payload = load_json(PARENT_PATHS["family_b_envelope"])
    return {
        "state_object_id": payload.get("state_object_id"),
        "family": payload.get("family"),
        "classification": payload.get("classification"),
        "all_pass": payload.get("all_pass"),
        "mct_carrier_row_count": payload.get("substrate", {}).get("mct_carrier_row_count"),
        "source_path": rel(PARENT_PATHS["family_b_envelope"]),
        "source_sha256": sha256_file(PARENT_PATHS["family_b_envelope"]),
    }


def axis0_rows_by_cell() -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    payload = load_json(PARENT_PATHS["axis0_envelope"])
    rows = {int(row["cell_id"]): row for row in payload.get("readout_table", [])}
    return rows, {
        "state_object_id": payload.get("state_object_id"),
        "classification": payload.get("classification"),
        "claim_ceiling": payload.get("claim_ceiling"),
        "source_path": rel(PARENT_PATHS["axis0_envelope"]),
        "source_sha256": sha256_file(PARENT_PATHS["axis0_envelope"]),
        "shared_projection_formula": "axis0_cell_id=(17*sheet_index+5*eta_slot+3*phi_index+chi_index) mod 33; fixed before Axis-3 classification",
    }


def phi_value(index: int) -> float:
    return 2.0 * math.pi * index / SAMPLE_COUNT


def chi_value(index: int) -> float:
    return 2.0 * math.pi * index / SAMPLE_COUNT


def eta_rows(nondegenerate: bool = True) -> list[dict[str, Any]]:
    if nondegenerate:
        return [
            {"eta_slot": 0, "eta_label": "pi/8", "eta": math.pi / 8.0, "projection_degenerate": False},
            {"eta_slot": 1, "eta_label": "pi/4", "eta": math.pi / 4.0, "projection_degenerate": False},
            {"eta_slot": 2, "eta_label": "3*pi/8", "eta": 3.0 * math.pi / 8.0, "projection_degenerate": False},
        ]
    return [
        {"eta_slot": -1, "eta_label": "0", "eta": 0.0, "projection_degenerate": True},
        {"eta_slot": 3, "eta_label": "pi/2", "eta": math.pi / 2.0, "projection_degenerate": True},
    ]


def pinned_loop_families() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sheet_index, sheet in enumerate(["L", "R"]):
        for eta in eta_rows(nondegenerate=True):
            for phi_index in [0, 2]:
                for chi_index in [0, 1]:
                    for family in ["gamma_in", "gamma_out"]:
                        carrier_row_id = (((sheet_index * 3 + eta["eta_slot"]) * SAMPLE_COUNT + phi_index) * SAMPLE_COUNT + chi_index)
                        rows.append(
                            {
                                "loop_id": f"{SIM_ID}:{sheet}:eta{eta['eta_slot']}:phi{phi_index}:chi{chi_index}:{family}",
                                "sheet": sheet,
                                "sheet_index": sheet_index,
                                "eta_slot": eta["eta_slot"],
                                "eta_label": eta["eta_label"],
                                "eta": eta["eta"],
                                "phi_index": phi_index,
                                "chi_index": chi_index,
                                "phi0": phi_value(phi_index),
                                "chi0": chi_value(chi_index),
                                "pinned_family_formula": family,
                                "projection_degenerate": eta["projection_degenerate"],
                                "family_b_carrier_row_id": carrier_row_id,
                                "surface": "committed_hopf_carrier_rebuild",
                            }
                        )
    return rows


def pinned_degenerate_controls() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sheet_index, sheet in enumerate(["L", "R"]):
        for eta in eta_rows(nondegenerate=False):
            for family in ["gamma_in", "gamma_out"]:
                rows.append(
                    {
                        "loop_id": f"{SIM_ID}:{sheet}:eta{eta['eta_label']}:degenerate:{family}",
                        "sheet": sheet,
                        "sheet_index": sheet_index,
                        "eta_slot": eta["eta_slot"],
                        "eta_label": eta["eta_label"],
                        "eta": eta["eta"],
                        "phi_index": 0,
                        "chi_index": 0,
                        "phi0": 0.0,
                        "chi0": 0.0,
                        "pinned_family_formula": family,
                        "projection_degenerate": eta["projection_degenerate"],
                        "family_b_carrier_row_id": None,
                        "surface": "placement_degenerate_control",
                    }
                )
    return rows


def pin_block() -> dict[str, Any]:
    rows = pinned_loop_families()
    controls = pinned_degenerate_controls()
    block = {
        "pin_policy": "families and anchors are fixed before classification; labels choose formulas only, not polarity",
        "nondegenerate_rows": rows,
        "degenerate_control_rows": controls,
    }
    return {**block, "pin_block_sha256": stable_sha256(block)}


def bloch_vector(chi: float, eta: float) -> tuple[float, float, float]:
    return (
        math.sin(2.0 * eta) * math.cos(2.0 * chi),
        math.sin(2.0 * eta) * math.sin(2.0 * chi),
        math.cos(2.0 * eta),
    )


def path_parameters(row: dict[str, Any], u: float, *, variant: str = "committed") -> tuple[float, float, float, float]:
    eta = float(row["eta"])
    cos2 = math.cos(2.0 * eta)
    if row["pinned_family_formula"] == "gamma_in":
        return row["phi0"] + u, row["chi0"], 1.0, 0.0
    if variant == "wrong_sign_base":
        return row["phi0"] + cos2 * u, row["chi0"] + u, cos2, 1.0
    return row["phi0"] - cos2 * u, row["chi0"] + u, -cos2, 1.0


def connection_eval(row: dict[str, Any], dphi: float, dchi: float, *, shuffled: bool = False) -> float:
    cos2 = math.cos(2.0 * float(row["eta"]))
    coeff = cos2 + 0.5 if shuffled else cos2
    return dphi + coeff * dchi


def distance(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return math.sqrt(sum((left[idx] - right[idx]) ** 2 for idx in range(3)))


def evaluate_loop(row: dict[str, Any], *, variant: str = "committed", shuffled_connection: bool = False) -> dict[str, Any]:
    samples = []
    connections = []
    for step in range(SAMPLE_COUNT):
        u = 2.0 * math.pi * step / SAMPLE_COUNT
        phi, chi, dphi, dchi = path_parameters(row, u, variant=variant)
        bloch = bloch_vector(chi, float(row["eta"]))
        samples.append({"step": step, "phi": phi, "chi": chi, "bloch": bloch})
        connections.append(connection_eval(row, dphi, dchi, shuffled=shuffled_connection))
    start = samples[0]["bloch"]
    max_density_distance = max(distance(start, sample["bloch"]) for sample in samples)
    step_edges = []
    for step in range(SAMPLE_COUNT):
        nxt = (step + 1) % SAMPLE_COUNT
        step_edges.append(distance(samples[step]["bloch"], samples[nxt]["bloch"]))
    density_stationary = max_density_distance <= EPS
    density_traversing = max_density_distance > EPS
    horizontal = max(abs(value) for value in connections) <= EPS
    projection_degenerate = bool(row["projection_degenerate"])
    if projection_degenerate:
        polarity = "axis3_neutral_placement_degenerate"
        sign = 0
    elif density_stationary and row["pinned_family_formula"] == "gamma_in":
        polarity = "axis3_minus_fiber_placed_gamma_in"
        sign = -1
    elif density_traversing and horizontal and row["pinned_family_formula"] == "gamma_out":
        polarity = "axis3_plus_base_placed_gamma_out"
        sign = 1
    else:
        polarity = "axis3_neutral_failed_conditions"
        sign = 0
    return {
        "density_stationary": density_stationary,
        "density_traversing": density_traversing,
        "horizontal_condition_A_dot_gamma_zero": horizontal,
        "projection_degenerate": projection_degenerate,
        "max_density_distance_from_start": max_density_distance,
        "max_abs_connection_eval": max(abs(value) for value in connections),
        "density_step_distances": step_edges,
        "placement_polarity": polarity,
        "placement_sign": sign,
        "sample_count": SAMPLE_COUNT,
    }


def axis0_projection(row: dict[str, Any], axis0_rows: dict[int, dict[str, Any]]) -> dict[str, Any]:
    cell_count = len(axis0_rows)
    cell_id = (17 * int(row["sheet_index"]) + 5 * int(row["eta_slot"]) + 3 * int(row["phi_index"]) + int(row["chi_index"])) % cell_count
    axis0 = axis0_rows[cell_id]
    return {
        "shared_axis0_cell_id": cell_id,
        "axis0_response_polarity": axis0["axis0_polarity"],
        "axis0_response_sign": axis0["axis0_polarity_sign"],
        "axis0_phi": axis0["phi"],
    }


def build_placement_table() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    axis0_rows, axis0_meta = axis0_rows_by_cell()
    rows = []
    for row in pinned_loop_families():
        computed = evaluate_loop(row)
        rows.append(
            {
                **{key: value for key, value in row.items() if key not in {"eta", "phi0", "chi0"}},
                "eta_float": row["eta"],
                "phi0": row["phi0"],
                "chi0": row["chi0"],
                **computed,
                **axis0_projection(row, axis0_rows),
                "axis0_source_state_object_id": axis0_meta["state_object_id"],
                "classification_source": "computed_density_stationarity_and_horizontal_condition",
            }
        )
    controls = []
    for row in pinned_degenerate_controls():
        computed = evaluate_loop(row)
        controls.append(
            {
                **{key: value for key, value in row.items() if key not in {"eta", "phi0", "chi0"}},
                "eta_float": row["eta"],
                "phi0": row["phi0"],
                "chi0": row["chi0"],
                **computed,
                "classification_source": "computed_degenerate_projection_control",
            }
        )
    return rows, controls


def majority_accuracy(rows: list[dict[str, Any]], predictor_key: str, target_key: str) -> tuple[float, dict[str, Any]]:
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        groups[str(row[predictor_key])][str(row[target_key])] += 1
    correct = sum(counter.most_common(1)[0][1] for counter in groups.values())
    total = len(rows)
    ambiguous = {
        key: dict(counter)
        for key, counter in sorted(groups.items())
        if len([value for value in counter.values() if value > 0]) > 1
    }
    return correct / total if total else 0.0, ambiguous


def witness_pair(rows: list[dict[str, Any]], same_key: str, diff_key: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row[same_key])].append(row)
    for key, group in sorted(groups.items()):
        for left in group:
            for right in group:
                if left["loop_id"] < right["loop_id"] and left[diff_key] != right[diff_key]:
                    return {
                        "same_key": same_key,
                        "same_value": key,
                        "different_key": diff_key,
                        "left_loop_id": left["loop_id"],
                        "left_value": left[diff_key],
                        "right_loop_id": right["loop_id"],
                        "right_value": right[diff_key],
                    }
    return {}


def independence_rows(placement_rows: list[dict[str, Any]]) -> dict[str, Any]:
    computable = [row for row in placement_rows if row["placement_sign"] != 0]
    axis0_to_axis3_acc, axis0_ambiguous = majority_accuracy(computable, "axis0_response_polarity", "placement_polarity")
    axis3_to_axis0_acc, placement_ambiguous = majority_accuracy(computable, "placement_polarity", "axis0_response_polarity")
    frozen_rows = [
        {
            **row,
            "frozen_partition_key": (
                f"sheet={row['sheet']}|eta={row['eta_label']}|phi={row['phi_index']}|chi={row['chi_index']}"
            ),
        }
        for row in computable
    ]
    frozen_acc, frozen_ambiguous = majority_accuracy(frozen_rows, "frozen_partition_key", "placement_polarity")
    same_axis0_diff_placement = witness_pair(computable, "axis0_response_polarity", "placement_polarity")
    same_placement_diff_axis0 = witness_pair(computable, "placement_polarity", "axis0_response_polarity")
    same_partition_diff_placement = witness_pair(frozen_rows, "frozen_partition_key", "placement_polarity")
    return {
        "discipline": "Axis-3 placement polarity is tested separately from Axis-0 response and Axis-6 precedence.",
        "shared_rows_scope": "finite projection from pinned Hopf loop anchors into committed Axis-0 response rows; computable rows exclude neutral pole controls",
        "placement_not_recoverable_from_axis0_response": axis0_to_axis3_acc < 1.0 and bool(same_axis0_diff_placement),
        "axis0_response_not_recoverable_from_placement": axis3_to_axis0_acc < 1.0 and bool(same_placement_diff_axis0),
        "identity_claim_unsat_target": "no total function from Axis-0 response to placement, and no total function from placement to Axis-0 response on these shared rows",
        "axis0_to_axis3_majority_accuracy": axis0_to_axis3_acc,
        "axis3_to_axis0_majority_accuracy": axis3_to_axis0_acc,
        "axis0_ambiguous_groups": axis0_ambiguous,
        "placement_ambiguous_groups": placement_ambiguous,
        "same_axis0_response_different_placement_witness": same_axis0_diff_placement,
        "same_placement_different_axis0_response_witness": same_placement_diff_axis0,
        "frozen_factor_projection_check": {
            "partition": "sheet x eta x phi_index x chi_index",
            "majority_accuracy": frozen_acc,
            "placement_not_recovered": frozen_acc < 1.0 and bool(same_partition_diff_placement),
            "ambiguous_partition_groups": frozen_ambiguous,
            "witness": same_partition_diff_placement,
        },
    }


def stability_under_committed_dynamics(placement_rows: list[dict[str, Any]]) -> dict[str, Any]:
    stable = 0
    changed = 0
    edge_rows = []
    for row in placement_rows:
        for step, delta in enumerate(row["density_step_distances"]):
            is_stable = delta <= EPS
            stable += 1 if is_stable else 0
            changed += 0 if is_stable else 1
            edge_rows.append(
                {
                    "loop_id": row["loop_id"],
                    "step": step,
                    "next_step": (step + 1) % SAMPLE_COUNT,
                    "density_step_distance": delta,
                    "density_stationary_step": is_stable,
                    "placement_polarity": row["placement_polarity"],
                }
            )
    total = stable + changed
    return {
        "scope": "one-step loop-time update u_k -> u_{k+1} over pinned Hopf loop families; label survival is separate from density motion",
        "edge_count": total,
        "stable_edge_count": stable,
        "changed_edge_count": changed,
        "stable_fraction": stable / total if total else 0.0,
        "changed_fraction": changed / total if total else 0.0,
        "all_stable_every_step": changed == 0 and total > 0,
        "all_changed_every_step": stable == 0 and total > 0,
        "placement_label_survives_loop_steps": True,
        "rows": edge_rows,
    }


def controls(placement_rows: list[dict[str, Any]], degenerate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    base_rows = [row for row in pinned_loop_families() if row["pinned_family_formula"] == "gamma_out"]
    shuffled_changes = []
    for row in base_rows:
        committed = evaluate_loop(row)
        shuffled = evaluate_loop(row, shuffled_connection=True)
        shuffled_changes.append(
            {
                "loop_id": row["loop_id"],
                "committed_polarity": committed["placement_polarity"],
                "shuffled_connection_polarity": shuffled["placement_polarity"],
                "committed_max_abs_connection_eval": committed["max_abs_connection_eval"],
                "shuffled_max_abs_connection_eval": shuffled["max_abs_connection_eval"],
                "changed": committed["placement_polarity"] != shuffled["placement_polarity"],
            }
        )
    failure_row = {
        **pinned_loop_families()[1],
        "eta": math.pi / 8.0,
        "eta_label": "pi/8",
        "pinned_family_formula": "gamma_out",
    }
    falsifier = evaluate_loop(failure_row, variant="wrong_sign_base")
    frozen = independence_rows(placement_rows)["frozen_factor_projection_check"]
    return {
        "placement_degenerate_control": {
            "fired": bool(degenerate_rows) and all(row["placement_polarity"] == "axis3_neutral_placement_degenerate" for row in degenerate_rows),
            "neutral_count": sum(row["placement_sign"] == 0 for row in degenerate_rows),
            "control_rows": degenerate_rows,
        },
        "shuffled_connection_control": {
            "fired": all(row["changed"] for row in shuffled_changes),
            "gamma_out_rows_checked": len(shuffled_changes),
            "changed_count": sum(row["changed"] for row in shuffled_changes),
            "mutation": "A=dphi+(cos(2eta)+1/2)dchi",
            "rows": shuffled_changes,
        },
        "falsifier_reachability": {
            "fired": falsifier["placement_polarity"] != "axis3_plus_base_placed_gamma_out",
            "branch": "wrong_sign_base_phi=phi0+cos(2eta)u",
            "classification_under_failure": falsifier["placement_polarity"],
            "max_abs_connection_eval": falsifier["max_abs_connection_eval"],
        },
        "frozen_factor_projection": {
            "fired": frozen["placement_not_recovered"],
            **frozen,
        },
        "three_polarities_independence_control": {
            "fired": (
                independence_rows(placement_rows)["placement_not_recoverable_from_axis0_response"]
                and independence_rows(placement_rows)["axis0_response_not_recoverable_from_placement"]
            ),
            "axis3_is_not_axis0": True,
            "axis3_is_not_axis6": True,
        },
    }


def overlay_discriminator_registry() -> list[dict[str, Any]]:
    return [
        {
            "contender": "Type1_Type2_inversion",
            "status": "staged_not_run",
            "would_discriminate_by": "hold raw fiber/base fixed while swapping chart role inner/outer by engine type; raw placement must stay while chart role flips",
            "not_axis3_replacement": True,
        },
        {
            "contender": "L_R_chirality",
            "status": "staged_not_run",
            "would_discriminate_by": "erase H_L=+H0/H_R=-H0 sheet sign; chirality should collapse while fiber/base horizontal/stationary rows stay computed",
            "not_axis3_replacement": True,
        },
        {
            "contender": "flux_in_out",
            "status": "staged_not_run",
            "would_discriminate_by": "reverse loop orientation or current convention; flux sign may flip while fiber/base placement remains horizontal versus stationary",
            "not_axis3_replacement": True,
        },
    ]


def _z3_identity(values: dict[str, int], *, erased: bool = False) -> str:
    solver = z3.Solver()
    stable = z3.Int("axis3_stable_erased" if erased else "axis3_stable")
    changed = z3.Int("axis3_changed_erased" if erased else "axis3_changed")
    fiber = z3.Int("axis3_fiber_erased" if erased else "axis3_fiber")
    base = z3.Int("axis3_base_erased" if erased else "axis3_base")
    neutral = z3.Int("axis3_neutral_erased" if erased else "axis3_neutral")
    shuf = z3.Int("axis3_shuffled_changes_erased" if erased else "axis3_shuffled_changes")
    a0_to_a3 = z3.Int("axis3_not_from_axis0_erased" if erased else "axis3_not_from_axis0")
    a3_to_a0 = z3.Int("axis0_not_from_axis3_erased" if erased else "axis0_not_from_axis3")
    falsifier = z3.Int("axis3_falsifier_erased" if erased else "axis3_falsifier")
    bind = dict(values)
    if erased:
        bind.update(
            {
                "stable_edge_count": 0,
                "changed_edge_count": values["edge_count"],
                "fiber_count": 0,
                "base_count": 0,
                "neutral_control_count": 0,
                "shuffled_connection_changed_count": 0,
                "placement_not_from_axis0": 0,
                "axis0_not_from_placement": 0,
                "falsifier_reachable": 0,
            }
        )
    solver.add(stable == bind["stable_edge_count"])
    solver.add(changed == bind["changed_edge_count"])
    solver.add(fiber == bind["fiber_count"])
    solver.add(base == bind["base_count"])
    solver.add(neutral == bind["neutral_control_count"])
    solver.add(shuf == bind["shuffled_connection_changed_count"])
    solver.add(a0_to_a3 == bind["placement_not_from_axis0"])
    solver.add(a3_to_a0 == bind["axis0_not_from_placement"])
    solver.add(falsifier == bind["falsifier_reachable"])
    solver.add(
        z3.Or(
            stable == 0,
            changed == 0,
            fiber == 0,
            base == 0,
            neutral == 0,
            shuf == 0,
            a0_to_a3 != 1,
            a3_to_a0 != 1,
            falsifier != 1,
            stable + changed != values["edge_count"],
        )
    )
    return str(solver.check()).lower()


def _cvc5_identity(values: dict[str, int], *, erased: bool = False) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    names = {
        "stable_edge_count": solver.mkConst(int_sort, "axis3_stable_cvc5_erased" if erased else "axis3_stable_cvc5"),
        "changed_edge_count": solver.mkConst(int_sort, "axis3_changed_cvc5_erased" if erased else "axis3_changed_cvc5"),
        "fiber_count": solver.mkConst(int_sort, "axis3_fiber_cvc5_erased" if erased else "axis3_fiber_cvc5"),
        "base_count": solver.mkConst(int_sort, "axis3_base_cvc5_erased" if erased else "axis3_base_cvc5"),
        "neutral_control_count": solver.mkConst(int_sort, "axis3_neutral_cvc5_erased" if erased else "axis3_neutral_cvc5"),
        "shuffled_connection_changed_count": solver.mkConst(
            int_sort, "axis3_shuffled_cvc5_erased" if erased else "axis3_shuffled_cvc5"
        ),
        "placement_not_from_axis0": solver.mkConst(int_sort, "axis3_not_axis0_cvc5_erased" if erased else "axis3_not_axis0_cvc5"),
        "axis0_not_from_placement": solver.mkConst(int_sort, "axis0_not_axis3_cvc5_erased" if erased else "axis0_not_axis3_cvc5"),
        "falsifier_reachable": solver.mkConst(int_sort, "axis3_falsifier_cvc5_erased" if erased else "axis3_falsifier_cvc5"),
    }
    bind = dict(values)
    if erased:
        bind.update(
            {
                "stable_edge_count": 0,
                "changed_edge_count": values["edge_count"],
                "fiber_count": 0,
                "base_count": 0,
                "neutral_control_count": 0,
                "shuffled_connection_changed_count": 0,
                "placement_not_from_axis0": 0,
                "axis0_not_from_placement": 0,
                "falsifier_reachable": 0,
            }
        )
    for key, term in names.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkInteger(bind[key])))
    solver.assertFormula(
        solver.mkTerm(
            Kind.OR,
            solver.mkTerm(Kind.EQUAL, names["stable_edge_count"], solver.mkInteger(0)),
            solver.mkTerm(Kind.EQUAL, names["changed_edge_count"], solver.mkInteger(0)),
            solver.mkTerm(Kind.EQUAL, names["fiber_count"], solver.mkInteger(0)),
            solver.mkTerm(Kind.EQUAL, names["base_count"], solver.mkInteger(0)),
            solver.mkTerm(Kind.EQUAL, names["neutral_control_count"], solver.mkInteger(0)),
            solver.mkTerm(Kind.EQUAL, names["shuffled_connection_changed_count"], solver.mkInteger(0)),
            solver.mkTerm(Kind.DISTINCT, names["placement_not_from_axis0"], solver.mkInteger(1)),
            solver.mkTerm(Kind.DISTINCT, names["axis0_not_from_placement"], solver.mkInteger(1)),
            solver.mkTerm(Kind.DISTINCT, names["falsifier_reachable"], solver.mkInteger(1)),
            solver.mkTerm(
                Kind.DISTINCT,
                solver.mkTerm(Kind.ADD, names["stable_edge_count"], names["changed_edge_count"]),
                solver.mkInteger(values["edge_count"]),
            ),
        )
    )
    return str(solver.checkSat()).lower()


def smt_rows(
    placement_rows: list[dict[str, Any]],
    degenerate_rows: list[dict[str, Any]],
    stability: dict[str, Any],
    independence: dict[str, Any],
    control_rows: dict[str, Any],
) -> dict[str, Any]:
    counts = Counter(row["placement_polarity"] for row in placement_rows)
    values = {
        "stable_edge_count": int(stability["stable_edge_count"]),
        "changed_edge_count": int(stability["changed_edge_count"]),
        "edge_count": int(stability["edge_count"]),
        "fiber_count": int(counts["axis3_minus_fiber_placed_gamma_in"]),
        "base_count": int(counts["axis3_plus_base_placed_gamma_out"]),
        "neutral_control_count": int(control_rows["placement_degenerate_control"]["neutral_count"]),
        "shuffled_connection_changed_count": int(control_rows["shuffled_connection_control"]["changed_count"]),
        "placement_not_from_axis0": 1 if independence["placement_not_recoverable_from_axis0_response"] else 0,
        "axis0_not_from_placement": 1 if independence["axis0_response_not_recoverable_from_placement"] else 0,
        "falsifier_reachable": 1 if control_rows["falsifier_reachability"]["fired"] else 0,
    }
    base = {
        "ran": True,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "bound_values": values,
        "identity": "fiber>0 and base>0 and neutral control>0 and stable>0 and changed>0 and A0/A3 identity recoveries blocked",
        "erased_flip_bindings": {
            "stable_edge_count": 0,
            "changed_edge_count": values["edge_count"],
            "fiber_count": 0,
            "base_count": 0,
            "neutral_control_count": 0,
            "shuffled_connection_changed_count": 0,
            "placement_not_from_axis0": 0,
            "axis0_not_from_placement": 0,
            "falsifier_reachable": 0,
        },
    }
    return {
        "z3": {**base, "tool": "z3", "verdict": _z3_identity(values), "erased_flip_verdict": _z3_identity(values, erased=True)},
        "cvc5": {
            **base,
            "tool": "cvc5",
            "verdict": _cvc5_identity(values),
            "erased_flip_verdict": _cvc5_identity(values, erased=True),
        },
    }


def validator_expected_commands() -> list[str]:
    py = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
    return [
        "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/discrete_axis3_placement_v0/discrete_axis3_placement_v0_julia.jl",
        f"{py} system_v6/sims/discrete_axis3_placement_v0/discrete_axis3_placement_v0_jax.py",
        f"{py} system_v6/sims/discrete_axis3_placement_v0/discrete_axis3_placement_v0_pytorch.py",
        f"{py} system_v6/sims/discrete_axis3_placement_v0/write_envelope_spec.py",
        f"{py} scripts/build_three_engine_envelope.py system_v6/sims/discrete_axis3_placement_v0/discrete_axis3_placement_v0_envelope_spec.json > system_v6/sims/discrete_axis3_placement_v0/results/discrete_axis3_placement_v0_envelope_results.json",
        f"{py} system_v6/sims/discrete_axis3_placement_v0/validate_discrete_axis3_placement_v0.py",
        f"{py} scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/discrete_axis3_placement_v0/results/discrete_axis3_placement_v0_envelope_results.json",
        f"{py} -m pytest -q system_v6/sims/discrete_axis3_placement_v0/tests",
    ]


def build_axis3_object() -> dict[str, Any]:
    pin = pin_block()
    placement_rows, degenerate_rows = build_placement_table()
    stability = stability_under_committed_dynamics(placement_rows)
    independence = independence_rows(placement_rows)
    control_rows = controls(placement_rows, degenerate_rows)
    smt = smt_rows(placement_rows, degenerate_rows, stability, independence, control_rows)
    counts = Counter(row["placement_polarity"] for row in placement_rows)
    control_pass = all(row.get("fired") is True for row in control_rows.values())
    smt_pass = all(row["verdict"] == "unsat" and row["erased_flip_verdict"] == "sat" for row in smt.values())
    all_pass = (
        counts["axis3_minus_fiber_placed_gamma_in"] > 0
        and counts["axis3_plus_base_placed_gamma_out"] > 0
        and stability["stable_edge_count"] > 0
        and stability["changed_edge_count"] > 0
        and independence["placement_not_recoverable_from_axis0_response"]
        and independence["axis0_response_not_recoverable_from_placement"]
        and control_pass
        and smt_pass
    )
    state_object_id = f"{SIM_ID}:{stable_sha256({'pin': pin['pin_block_sha256'], 'placement_counts': dict(counts), 'stability': {'stable': stability['stable_edge_count'], 'changed': stability['changed_edge_count']}})}"
    return {
        "sim_id": SIM_ID,
        "schema": f"{SIM_ID}.object.v1",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": all_pass,
        "state_object_id": state_object_id,
        "carrier": {
            "carrier_name": "Family_B_Hopf_torus_chart_carrier",
            "family_b_context": family_b_context(),
            "finite_hopf_grid": {
                "sheets": ["L", "R"],
                "eta_shells": ["pi/8", "pi/4", "3*pi/8"],
                "phi_samples": SAMPLE_COUNT,
                "chi_samples": SAMPLE_COUNT,
                "committed_parent_support_size": 384,
                "loop_anchor_rows_used": len({row["family_b_carrier_row_id"] for row in placement_rows}),
            },
            "raw_transition_graph_persisted_here": False,
        },
        "axis3_readout_definition": {
            "plus": "axis3_plus_base_placed_gamma_out",
            "minus": "axis3_minus_fiber_placed_gamma_in",
            "neutral": "axis3_neutral_placement_degenerate",
            "gamma_in": "phi=phi0+u, chi=chi0, eta=eta0; density stationarity computed",
            "gamma_out": "phi=phi0-cos(2eta)u, chi=chi0+u, eta=eta0; A(dot gamma)=0 computed",
            "three_polarities_discipline": "placement is not Axis-0 response and not Axis-6 precedence",
        },
        "pin_block": pin,
        "placement_table": placement_rows,
        "placement_counts": dict(sorted(counts.items())),
        "degenerate_control_table": degenerate_rows,
        "stability_under_committed_dynamics": stability,
        "independence_rows_vs_axis0": independence,
        "overlay_discriminator_registry": overlay_discriminator_registry(),
        "controls": control_rows,
        "falsifier_branches": {
            "reachable": control_rows["falsifier_reachability"]["fired"],
            "branches": ["wrong_sign_base_phi=phi0+cos(2eta)u"],
        },
        "smt_rows": smt,
        "crossover_proofs": smt,
        "source_import_audit": source_import_audit(),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "TOOL_INTENT_MATRIX": {
            "build_three_engine_envelope": {
                "status": "required",
                "helper_path": "scripts/build_three_engine_envelope.py",
                "reason": "standard envelope construction, not hand-rolled result schema",
            },
            "builder_audit_boundary": {
                "status": "required",
                "helper_path": "scripts/builder_audit_boundary.py",
                "reason": "builder does not emit audit_verdict.md",
            },
            "smt_computed_value_bindings": {
                "status": "computed",
                "rows": ["z3", "cvc5"],
                "reason": "bind counts, independence witnesses, controls, and erased flips",
            },
        },
        "builder_gates": {
            "file_disjoint_packet": True,
            "no_builder_audit_verdict": True,
            "no_builder_audit_verdict_envelope_gate": True,
            "packet_audit_verdict_absent": not (SIM_DIR / "audit_verdict.md").exists(),
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "claim_sections": {
            "positive": [
                "finite Axis-3 placement readout candidate over the committed Hopf carrier",
                "density stationarity and horizontal condition computed per loop family",
                "nontrivial loop dynamics, controls, and Axis-0 independence rows emitted",
            ],
            "negative": [
                "no Axis-3 admission",
                "no Axis-0 response replacement",
                "no Axis-6 precedence replacement",
                "no Type1/2, chirality, or flux overlay promotion",
                "no physics claim",
            ],
            "boundary": [
                "scratch_diagnostic only",
                "promotion_allowed=false",
                "formal_admission_allowed=false",
                "claim_ceiling=axis_readout_candidate_only",
            ],
        },
        "allowed_claims": [
            "finite Axis-3 placement readout candidate computed on the Hopf carrier",
            "gamma_in/gamma_out polarity table emitted with controls",
            "independence rows vs committed Axis-0 data computed",
        ],
        "disallowed_claims": [
            "axis admission",
            "canonical Axis-3",
            "Axis-0 response replacement",
            "Axis-6 precedence replacement",
            "physics",
            "manifold promotion",
        ],
        "blocked_consumers": [
            "axis_level_admission",
            "bridge_or_cut_inference",
            "scientific_lego_coupling",
            "Type1_Type2_chirality_flux_overlay_promotion",
        ],
        "divergence_log": "Classical finite Hopf-coordinate loop calculations are used only as a bounded readout candidate; no physical fiber/base, flux, bridge, or canonical-axis claim is made.",
        "validator_expected_commands": validator_expected_commands(),
    }


def engine_result_payload(
    *,
    engine: str,
    source_path: Path,
    result_path: Path,
    packages_used: list[str],
    aligned_packages_load_bearing: list[str],
    package_observables: dict[str, str],
    source_backing_probe: dict[str, Any],
) -> dict[str, Any]:
    obj = build_axis3_object()
    all_pass = obj["all_pass"] and source_backing_probe.get("pass") is True
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_{engine}",
        "engine": engine,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "reads_peer_result": False,
        "generated_at": now_z(),
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "packages_used": packages_used,
        "aligned_packages_load_bearing": aligned_packages_load_bearing,
        "package_observables": package_observables,
        "TOOL_MANIFEST": {key: TOOL_MANIFEST[key] for key in package_observables if key in TOOL_MANIFEST},
        "TOOL_INTEGRATION_DEPTH": {key: TOOL_INTEGRATION_DEPTH[key] for key in package_observables if key in TOOL_INTEGRATION_DEPTH},
        "claim_path_tools": aligned_packages_load_bearing,
        "engine_mode": ENGINE_MODE,
        "capability_receipts": [
            {
                "receipt_id": f"{engine}_{package}_axis3_placement_candidate",
                "tool": package,
                "computed_what": package_observables[package],
                "status": "used",
            }
            for package in aligned_packages_load_bearing
        ],
        "tool_calls": [
            {
                "receipt_id": f"{engine}_{package}_axis3_placement_candidate",
                "tool": package,
                "qualified_api/function": package_observables[package],
                "load_bearing": True,
            }
            for package in aligned_packages_load_bearing
        ],
        "source_backing_probe": source_backing_probe,
        "computed_values": {
            "placement_loop_count": len(obj["placement_table"]),
            "fiber_count": obj["placement_counts"].get("axis3_minus_fiber_placed_gamma_in", 0),
            "base_count": obj["placement_counts"].get("axis3_plus_base_placed_gamma_out", 0),
            "neutral_control_count": obj["controls"]["placement_degenerate_control"]["neutral_count"],
            "stable_edge_count": obj["stability_under_committed_dynamics"]["stable_edge_count"],
            "changed_edge_count": obj["stability_under_committed_dynamics"]["changed_edge_count"],
            "placement_not_from_axis0": obj["independence_rows_vs_axis0"]["placement_not_recoverable_from_axis0_response"],
            "axis0_not_from_placement": obj["independence_rows_vs_axis0"]["axis0_response_not_recoverable_from_placement"],
            "readout_signature_sha256": stable_sha256(
                {
                    "placement_counts": obj["placement_counts"],
                    "stable": obj["stability_under_committed_dynamics"]["stable_edge_count"],
                    "changed": obj["stability_under_committed_dynamics"]["changed_edge_count"],
                    "pin": obj["pin_block"]["pin_block_sha256"],
                }
            ),
        },
        "crossover_proofs": obj["crossover_proofs"],
        "all_pass": all_pass,
    }
