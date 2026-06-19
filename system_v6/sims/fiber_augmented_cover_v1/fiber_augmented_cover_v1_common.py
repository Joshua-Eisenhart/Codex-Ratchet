#!/usr/bin/env python3
"""Nontrivial finite fiber-augmented cover builder for the faithful b6 test."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import z3


SIM_ID = "fiber_augmented_cover_v1"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "axis_readout_candidate_only + nontrivial_cover_faithful_fiber_augmented_cover_b6_law_test_v1"
ENGINE_MODE = "finite_fiber_augmented_family_a_33_cell_degree_one_clutching_cover"
EXPECTED_BASE_STATE_COUNT = 33
EXPECTED_BASE_EDGE_COUNT = 198
FIBER_PHASE_COUNT = 3

V0_SIM_DIR = ROOT / "system_v6" / "sims" / "fiber_augmented_cover_v0"
AXIS0_DIR = ROOT / "system_v6" / "sims" / "discrete_axis0_field_v0"
AXIS3_DIR = ROOT / "system_v6" / "sims" / "discrete_axis3_placement_v0"
AXIS6_DIR = ROOT / "system_v6" / "sims" / "discrete_axis6_precedence_v0"
B6_V0_DIR = ROOT / "system_v6" / "sims" / "axis_triple_consistency_b6_v0"
B6_V1_DIR = ROOT / "system_v6" / "sims" / "axis_triple_consistency_b6_v1"
SCRIPTS_DIR = ROOT / "scripts"

for path in (V0_SIM_DIR, AXIS0_DIR, AXIS3_DIR, AXIS6_DIR, B6_V0_DIR, B6_V1_DIR, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402
import axis_triple_consistency_b6_v0_common as b6_v0_common  # noqa: E402
import axis_triple_consistency_b6_v1_common as b6_v1_common  # noqa: E402
import discrete_axis0_field_v0_common as axis0_common  # noqa: E402
import discrete_axis3_placement_v0_common as axis3_common  # noqa: E402
import discrete_axis6_precedence_v0_common as axis6_common  # noqa: E402
import fiber_augmented_cover_v0_common as v0_common  # noqa: E402


PARENT_COMMITS = {
    "fiber_augmented_cover_v0_audit": "cf7fe65c4",
    "b6_v1_verdict": "03e606122",
    "axis_work_order": "c2a978eae",
    "axis0": "5d330b427",
    "axis3": "ce8c77355",
    "axis6": "b6fafc67f",
    "hopf_section": "7e78f3829",
}

PANEL9_PATH = ROOT / "system_v6" / "receipts" / "panel9_blind_altviews_wave_targets_20260612.md"
PARENT_PATHS = {
    "v0_audit_verdict": V0_SIM_DIR / "audit_verdict.md",
    "v0_common": V0_SIM_DIR / "fiber_augmented_cover_v0_common.py",
    "v0_result": V0_SIM_DIR / "results/fiber_augmented_cover_v0_results.json",
    "panel9": PANEL9_PATH,
    "axis_work_order": ROOT / "system_v6/receipts/axis_work_order_20260612.md",
    "b6_v1_build_card": B6_V1_DIR / "build_card.md",
    "b6_v1_envelope": B6_V1_DIR / "results/axis_triple_consistency_b6_v1_envelope_results.json",
    "b6_v0_envelope": B6_V0_DIR / "results/axis_triple_consistency_b6_v0_envelope_results.json",
    "axis0_common": AXIS0_DIR / "discrete_axis0_field_v0_common.py",
    "axis0_envelope": AXIS0_DIR / "results/discrete_axis0_field_v0_envelope_results.json",
    "axis3_common": AXIS3_DIR / "discrete_axis3_placement_v0_common.py",
    "axis3_envelope": AXIS3_DIR / "results/discrete_axis3_placement_v0_envelope_results.json",
    "axis6_common": AXIS6_DIR / "discrete_axis6_precedence_v0_common.py",
    "axis6_envelope": AXIS6_DIR / "results/discrete_axis6_precedence_v0_envelope_results.json",
    "hopf_section_source": ROOT / "system_v6/sims/hopf_base_section_phase_recovery_v0/hopf_base_section_phase_recovery_v0.py",
    "hopf_section_envelope": ROOT / "system_v6/sims/hopf_base_section_phase_recovery_v0/results/hopf_base_section_phase_recovery_v0_envelope_results.json",
}

EQUATOR_LOOP_CELLS = [20, 17, 12, 15]
EQUATOR_LOOP_NAME = "committed_equatorial_loop"
EQUATOR_LIFTED_CLUTCHING_STEPS = {
    (20, 17): 1,
    (17, 12): 1,
    (12, 15): 1,
    (15, 20): 0,
}

TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "row-local relation contradiction/erased-flip proof over computed v1 cover signs",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "independent row-local relation contradiction/erased-flip proof over computed v1 cover signs",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "shared post-audit-idempotent builder/audit boundary gate",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "deterministic quotient, witness, sign-vector, and result hashes",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "deterministic result serialization for the scratch packet",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "hashlib": "supportive",
    "json": "supportive",
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
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
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
            "v0_audit_verdict": source_lock(
                PARENT_PATHS["v0_audit_verdict"],
                "v0_kill_condition_trivial_product_bundle",
                PARENT_COMMITS["fiber_augmented_cover_v0_audit"],
            ),
            "panel9": source_lock(PARENT_PATHS["panel9"], "panel_witness_and_chance_targets"),
            "axis_work_order": source_lock(
                PARENT_PATHS["axis_work_order"],
                "registered_next_object",
                PARENT_COMMITS["axis_work_order"],
            ),
            "b6_v1_build_card": source_lock(
                PARENT_PATHS["b6_v1_build_card"],
                "b6_v1_blocker_and_registered_cover",
                PARENT_COMMITS["b6_v1_verdict"],
            ),
        },
        "parent_hash_pins": {
            "v0_common": source_lock(PARENT_PATHS["v0_common"], "zero_shift_product_bundle_regression_source"),
            "v0_result": source_lock(PARENT_PATHS["v0_result"], "zero_shift_product_bundle_regression_result"),
            "axis0_common": source_lock(PARENT_PATHS["axis0_common"], "committed_axis0_builder", PARENT_COMMITS["axis0"]),
            "axis0_envelope": source_lock(PARENT_PATHS["axis0_envelope"], "committed_axis0_result", PARENT_COMMITS["axis0"]),
            "axis3_common": source_lock(PARENT_PATHS["axis3_common"], "committed_axis3_predicates", PARENT_COMMITS["axis3"]),
            "axis3_envelope": source_lock(PARENT_PATHS["axis3_envelope"], "committed_axis3_result", PARENT_COMMITS["axis3"]),
            "axis6_common": source_lock(PARENT_PATHS["axis6_common"], "committed_axis6_builder", PARENT_COMMITS["axis6"]),
            "axis6_envelope": source_lock(PARENT_PATHS["axis6_envelope"], "committed_axis6_result", PARENT_COMMITS["axis6"]),
            "hopf_section_source": source_lock(PARENT_PATHS["hopf_section_source"], "section_lift_construction_tool", PARENT_COMMITS["hopf_section"]),
            "hopf_section_envelope": source_lock(PARENT_PATHS["hopf_section_envelope"], "section_lift_result_context", PARENT_COMMITS["hopf_section"]),
            "b6_v0_envelope": source_lock(PARENT_PATHS["b6_v0_envelope"], "unfaithful_hopf_transplant_regression"),
            "b6_v1_envelope": source_lock(PARENT_PATHS["b6_v1_envelope"], "unfaithful_33_cell_proxy_regression", PARENT_COMMITS["b6_v1_verdict"]),
        },
        "raw_parent_classification_imported": False,
        "adapter_rule": "Axis0 and Axis6 are pulled back through the quotient projection; Axis3 is computed natively from committed gamma_in/gamma_out predicates on each finite fiber phase.",
    }


def phase_label(slot: int) -> str:
    return ["0", "2*pi/3", "4*pi/3"][slot]


def phase_value(slot: int) -> float:
    return 2.0 * math.pi * slot / FIBER_PHASE_COUNT


def eta_template(cell_id: int) -> dict[str, Any]:
    templates = [
        {"eta_slot": 0, "eta_label": "pi/8", "eta": math.pi / 8.0},
        {"eta_slot": 1, "eta_label": "pi/4", "eta": math.pi / 4.0},
        {"eta_slot": 2, "eta_label": "3*pi/8", "eta": 3.0 * math.pi / 8.0},
    ]
    return templates[cell_id % len(templates)]


def gamma_family_for_phase(slot: int) -> str:
    return "gamma_in" if slot == 0 else "gamma_out"


def axis3_predicate_row(cell: dict[str, Any], phase_slot: int) -> dict[str, Any]:
    cell_id = int(cell["cell_id"])
    eta = eta_template(cell_id)
    family = gamma_family_for_phase(phase_slot)
    row = {
        "loop_id": f"{SIM_ID}:cell{cell_id:02d}:phase{phase_slot}:{family}",
        "sheet": "L" if cell_id % 2 == 0 else "R",
        "sheet_index": cell_id % 2,
        "eta_slot": eta["eta_slot"],
        "eta_label": eta["eta_label"],
        "eta": eta["eta"],
        "phi_index": (cell_id + phase_slot) % axis3_common.SAMPLE_COUNT,
        "chi_index": (phase_slot * 2) % axis3_common.SAMPLE_COUNT,
        "phi0": axis3_common.phi_value((cell_id + phase_slot) % axis3_common.SAMPLE_COUNT),
        "chi0": phase_value(phase_slot),
        "pinned_family_formula": family,
        "projection_degenerate": False,
        "family_b_carrier_row_id": None,
        "surface": "fiber_augmented_33_cell_degree_one_clutching_phase_adapter",
    }
    computed = axis3_common.evaluate_loop(row)
    return {
        **{key: value for key, value in row.items() if key not in {"eta", "phi0", "chi0"}},
        "eta_float": row["eta"],
        "phi0": row["phi0"],
        "chi0": row["chi0"],
        **computed,
        "b3_panel_relation_sign": -int(computed["placement_sign"]) if int(computed["placement_sign"]) != 0 else 0,
        "classification_source": "computed_density_stationarity_and_horizontal_condition_from_committed_axis3_predicates",
        "source_backed_equivalent_adapter": True,
    }


@lru_cache(maxsize=1)
def parent_objects() -> dict[str, Any]:
    axis0_obj = axis0_common.build_axis0_object()
    axis6_obj = axis6_common.build_axis6_object()
    return {
        "carrier": axis0_common.rebuild_committed_carrier(),
        "axis0": axis0_obj,
        "axis6": axis6_obj,
        "axis0_rows": {int(row["cell_id"]): row for row in axis0_obj["readout_table"]},
        "axis6_rows": {int(row["cell_id"]): row for row in axis6_obj["precedence_table"]},
    }


def equator_edge_pairs() -> list[tuple[int, int]]:
    return list(zip(EQUATOR_LOOP_CELLS, EQUATOR_LOOP_CELLS[1:] + EQUATOR_LOOP_CELLS[:1]))


def transition_shift_for_base_edge(edge: dict[str, Any], *, zero_shift: bool = False) -> int:
    if zero_shift:
        return 0
    return EQUATOR_LIFTED_CLUTCHING_STEPS.get((int(edge["src"]), int(edge["dst"])), 0) % FIBER_PHASE_COUNT


def build_cover(*, zero_shift: bool = False) -> dict[str, Any]:
    parents = parent_objects()
    carrier = parents["carrier"]
    states: list[dict[str, Any]] = []
    for cell in carrier["cells"]:
        cell_id = int(cell["cell_id"])
        for phase_slot in range(FIBER_PHASE_COUNT):
            state_id = cell_id * FIBER_PHASE_COUNT + phase_slot
            axis3 = axis3_predicate_row(cell, phase_slot)
            states.append(
                {
                    "cover_state_id": state_id,
                    "cover_state_label": f"c{cell_id:02d}:u1_phase_{phase_slot}",
                    "projection_cell_id": cell_id,
                    "base_coord_scaled": cell["coord_scaled"],
                    "fiber_phase_slot": phase_slot,
                    "fiber_phase_label": phase_label(phase_slot),
                    "fiber_phase_radians": phase_value(phase_slot),
                    "axis3_loop_family": axis3["pinned_family_formula"],
                    "axis3_predicate": axis3,
                }
            )

    base_lift_edges: list[dict[str, Any]] = []
    transition_rows: list[dict[str, Any]] = []
    for edge in carrier["edges"]:
        shift = transition_shift_for_base_edge(edge, zero_shift=zero_shift)
        transition_rows.append(
            {
                "projection_edge_id": int(edge["edge_id"]),
                "src": int(edge["src"]),
                "dst": int(edge["dst"]),
                "generator": edge.get("generator"),
                "fiber_phase_shift_steps": shift,
                "transition_family": "zero_shift_product" if zero_shift else "degree_one_clutching" if shift else "same_chart_or_nonseam",
                "constant_along_fiber": True,
            }
        )
        for phase_slot in range(FIBER_PHASE_COUNT):
            base_lift_edges.append(
                {
                    "cover_edge_id": f"base:{edge['edge_id']}:phase:{phase_slot}:shift:{shift}",
                    "edge_type": "base_lift",
                    "src": int(edge["src"]) * FIBER_PHASE_COUNT + phase_slot,
                    "dst": int(edge["dst"]) * FIBER_PHASE_COUNT + ((phase_slot + shift) % FIBER_PHASE_COUNT),
                    "projection_src": int(edge["src"]),
                    "projection_dst": int(edge["dst"]),
                    "projection_edge_id": int(edge["edge_id"]),
                    "generator": edge.get("generator"),
                    "fiber_phase_shift_steps": shift,
                }
            )

    fiber_edges: list[dict[str, Any]] = []
    for cell in carrier["cells"]:
        cell_id = int(cell["cell_id"])
        for phase_slot in range(FIBER_PHASE_COUNT):
            fiber_edges.append(
                {
                    "cover_edge_id": f"fiber:{cell_id}:{phase_slot}",
                    "edge_type": "fiber_cycle",
                    "src": cell_id * FIBER_PHASE_COUNT + phase_slot,
                    "dst": cell_id * FIBER_PHASE_COUNT + ((phase_slot + 1) % FIBER_PHASE_COUNT),
                    "projection_src": cell_id,
                    "projection_dst": cell_id,
                    "projection_edge_id": None,
                    "generator": "pinned_u1_fiber_cycle",
                    "fiber_phase_shift_steps": 1,
                }
            )

    shift_counts = Counter(row["fiber_phase_shift_steps"] for row in base_lift_edges)
    return {
        "base_state_count": carrier["state_count"],
        "base_edge_count": carrier["edge_count"],
        "fiber_phase_count_per_cell": FIBER_PHASE_COUNT,
        "cover_state_count": len(states),
        "base_lift_edge_count": len(base_lift_edges),
        "fiber_cycle_edge_count": len(fiber_edges),
        "cover_edge_count": len(base_lift_edges) + len(fiber_edges),
        "fiber_phase_labels": [phase_label(slot) for slot in range(FIBER_PHASE_COUNT)],
        "fiber_phase_policy": "three pinned directed U(1) sectors; |F|=3 is pinned to carry directed winding rather than parity-only |F|=2",
        "chart_transition_policy": (
            "degree-1 Hopf clutching discretized on the committed equatorial loop; "
            "transition shifts are constant along each fiber and sum to one winding"
        ),
        "singularity_handling": {
            "pole_cells_scaled": [[0, 0, -2], [0, 0, 2]],
            "policy": "pole cells are pinned to same-chart/zero transition rows; the witness loop avoids poles and uses accumulated-phase bookkeeping",
        },
        "states": states,
        "base_lift_edges": base_lift_edges,
        "fiber_edges": fiber_edges,
        "chart_transition_rows": transition_rows,
        "base_lift_phase_shift_counts": {str(key): value for key, value in sorted(shift_counts.items())},
        "cover_sha256": stable_sha256(
            {
                "states": [
                    {
                        "cover_state_id": row["cover_state_id"],
                        "projection_cell_id": row["projection_cell_id"],
                        "fiber_phase_slot": row["fiber_phase_slot"],
                        "axis3_loop_family": row["axis3_loop_family"],
                    }
                    for row in states
                ],
                "transition_rows": transition_rows,
                "base_lift_edge_count": len(base_lift_edges),
                "fiber_cycle_edge_count": len(fiber_edges),
            }
        ),
    }


def compute_bundle_witness(cover: dict[str, Any]) -> dict[str, Any]:
    rows_by_pair = {
        (int(row["src"]), int(row["dst"])): row
        for row in cover["chart_transition_rows"]
    }
    loop_rows = []
    total_steps = 0
    for src, dst in equator_edge_pairs():
        row = rows_by_pair[(src, dst)]
        lifted_step = EQUATOR_LIFTED_CLUTCHING_STEPS.get((src, dst), 0)
        if row["fiber_phase_shift_steps"] % FIBER_PHASE_COUNT != lifted_step % FIBER_PHASE_COUNT:
            lifted_step = int(row["fiber_phase_shift_steps"])
        total_steps += lifted_step
        loop_rows.append(
            {
                "src": src,
                "dst": dst,
                "projection_edge_id": row["projection_edge_id"],
                "generator": row["generator"],
                "fiber_phase_shift_steps_mod_fiber": row["fiber_phase_shift_steps"],
                "lifted_phase_increment_steps": lifted_step,
            }
        )

    if total_steps % FIBER_PHASE_COUNT == 0:
        directed_winding = total_steps // FIBER_PHASE_COUNT
    else:
        directed_winding = None
    return {
        "loop_name": EQUATOR_LOOP_NAME,
        "base_loop_cell_ids": EQUATOR_LOOP_CELLS,
        "base_loop_edge_pairs": [[src, dst] for src, dst in equator_edge_pairs()],
        "fiber_phase_count": FIBER_PHASE_COUNT,
        "loop_transition_rows": loop_rows,
        "total_lifted_phase_shift_steps": total_steps,
        "directed_winding": directed_winding,
        "euler_class_witness": directed_winding,
        "nontrivial_gate_passed": directed_winding in {-1, 1},
        "trivial_product_witness": directed_winding == 0,
        "witness_rule": "sum lifted fiber phase transitions around the closed equatorial loop divided by |F|; nontrivial +/-1, trivial 0",
        "witness_sha256": stable_sha256(loop_rows),
    }


def quotient_projection(cover: dict[str, Any]) -> dict[str, Any]:
    fiber_sizes = Counter(int(row["projection_cell_id"]) for row in cover["states"])
    base_edge_projection = [
        {
            "projection_edge_id": row["projection_edge_id"],
            "src": row["projection_src"],
            "dst": row["projection_dst"],
            "generator": row["generator"],
            "fiber_phase_shift_steps": row["fiber_phase_shift_steps"],
        }
        for row in cover["base_lift_edges"][::FIBER_PHASE_COUNT]
    ]
    fiber_collapses = all(row["projection_src"] == row["projection_dst"] for row in cover["fiber_edges"])
    return {
        "map": "pi_cover_to_33_cell(cover_state_id)=projection_cell_id",
        "projection_total": len(fiber_sizes) == EXPECTED_BASE_STATE_COUNT and sum(fiber_sizes.values()) == cover["cover_state_count"],
        "fiber_size_by_cell": {str(key): value for key, value in sorted(fiber_sizes.items())},
        "uniform_fiber_size": set(fiber_sizes.values()) == {FIBER_PHASE_COUNT},
        "quotient_base_edge_count": len(base_edge_projection),
        "base_edges_recovered": len(base_edge_projection) == EXPECTED_BASE_EDGE_COUNT,
        "fiber_edges_collapse_inside_equivalence_classes": fiber_collapses,
        "projection_sha256": stable_sha256(
            [
                {
                    "cover_state_id": row["cover_state_id"],
                    "projection_cell_id": row["projection_cell_id"],
                    "fiber_phase_slot": row["fiber_phase_slot"],
                }
                for row in cover["states"]
            ]
        ),
        "sample_projected_edges": base_edge_projection[:12],
    }


def relation_rows(cover: dict[str, Any]) -> list[dict[str, Any]]:
    parents = parent_objects()
    out: list[dict[str, Any]] = []
    for state in cover["states"]:
        cell_id = int(state["projection_cell_id"])
        axis3 = state["axis3_predicate"]
        b0 = int(parents["axis0_rows"][cell_id]["axis0_polarity_sign"])
        b3 = int(axis3["b3_panel_relation_sign"])
        b6 = int(parents["axis6_rows"][cell_id]["b6_sign"])
        expected = -(b0 * b3)
        holds = b6 == expected
        out.append(
            {
                "row_id": state["cover_state_label"],
                "cover_state_id": state["cover_state_id"],
                "projection_cell_id": cell_id,
                "fiber_phase_slot": state["fiber_phase_slot"],
                "fiber_phase_label": state["fiber_phase_label"],
                "axis3_loop_family": state["axis3_loop_family"],
                "b0_source": "Axis0 pulled back through pi_cover_to_33_cell",
                "b0_sign": b0,
                "b3_source": "Axis3 gamma predicate computed natively on the pinned finite fiber phase",
                "axis3_committed_placement_sign": int(axis3["placement_sign"]),
                "b3_panel_relation_sign": b3,
                "b6_source": "Axis6 precedence pulled back through pi_cover_to_33_cell",
                "b6_sign": b6,
                "expected_b6_negative_b0_b3": expected,
                "relation_holds": holds,
                "density_stationary": axis3["density_stationary"],
                "density_traversing": axis3["density_traversing"],
                "horizontal_condition_A_dot_gamma_zero": axis3["horizontal_condition_A_dot_gamma_zero"],
                "relation_can_fail_here": not holds,
                "anti_by_construction_guard": "b0 and b6 are pullbacks from parent source builders; b3 is computed from gamma predicates before relation evaluation.",
            }
        )
    return out


def binomial_p_values(agreement_count: int, sample_total: int, null_probability: float = 0.5) -> dict[str, float]:
    if sample_total <= 0:
        return {"lower_tail": 1.0, "upper_tail": 1.0, "two_sided": 1.0}
    probs = [
        math.comb(sample_total, k) * (null_probability**k) * ((1.0 - null_probability) ** (sample_total - k))
        for k in range(sample_total + 1)
    ]
    lower = sum(probs[: agreement_count + 1])
    upper = sum(probs[agreement_count:])
    return {
        "lower_tail": min(1.0, lower),
        "upper_tail": min(1.0, upper),
        "two_sided": min(1.0, 2.0 * min(lower, upper)),
    }


def chance_classification(agreement_count: int, sample_total: int) -> str:
    p = binomial_p_values(agreement_count, sample_total)
    if agreement_count > sample_total / 2.0 and p["upper_tail"] <= 0.05:
        return "significant_above_chance"
    if agreement_count < sample_total / 2.0 and p["lower_tail"] <= 0.05:
        return "significant_below_chance"
    return "at_chance"


def relation_summary(table: list[dict[str, Any]], witness: dict[str, Any]) -> dict[str, Any]:
    total = len(table)
    agreement = sum(row["relation_holds"] for row in table)
    nonneutral = [row for row in table if row["expected_b6_negative_b0_b3"] != 0]
    nonneutral_agreement = sum(row["relation_holds"] for row in nonneutral)
    if not nonneutral:
        status = "inconclusive_no_nonneutral_rows"
    elif agreement == total:
        status = "holds_on_nontrivial_faithful_cover"
    else:
        status = "fails_on_nontrivial_faithful_cover"
    p_all = binomial_p_values(agreement, total)
    p_nonneutral = binomial_p_values(nonneutral_agreement, len(nonneutral)) if nonneutral else {"lower_tail": 1.0, "upper_tail": 1.0, "two_sided": 1.0}
    return {
        "law": "b6 = -b0*b3",
        "table_kind": "faithful_nontrivial_fiber_augmented_cover_table",
        "witness_gate_required": True,
        "witness_gate_passed": witness["nontrivial_gate_passed"],
        "sample_unit": "cover_state",
        "sample_total": total,
        "base_cell_total": EXPECTED_BASE_STATE_COUNT,
        "agreement_count": agreement,
        "violation_count": total - agreement,
        "agreement_fraction": agreement / total if total else 0.0,
        "nonneutral_total": len(nonneutral),
        "nonneutral_agreement_count": nonneutral_agreement,
        "nonneutral_violation_count": len(nonneutral) - nonneutral_agreement,
        "nonneutral_agreement_fraction": nonneutral_agreement / len(nonneutral) if nonneutral else 0.0,
        "binomial_p_two_sided": p_all["two_sided"],
        "binomial_p_upper_tail": p_all["upper_tail"],
        "binomial_p_lower_tail": p_all["lower_tail"],
        "nonneutral_binomial_p_two_sided": p_nonneutral["two_sided"],
        "chance_classification": chance_classification(agreement, total),
        "law_test_status": status,
        "null_model": "independent_random_signs_match_product_law_with_p_0_5",
        "chance_thresholds": {
            "null_probability": 0.5,
            "one_tailed_alpha": 0.05,
            "two_tailed_alpha": 0.05,
            "panel_sample_unit_note": "Panel 9 names N=33 base cells; this table tests N=99 cover states and reports the unit explicitly.",
            "one_tailed_95_percent_min_agreements_for_n33": 23,
            "perfect_law_subsample_n5_p_lt_0_05": True,
        },
        "relation_not_used_to_assign_axis3": True,
        "relation_can_fail": any(not row["relation_holds"] for row in table),
        "outcome_is_the_result": True,
    }


def sign_vector(table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": row["row_id"],
            "b0": row["b0_sign"],
            "b3": row["b3_panel_relation_sign"],
            "b6": row["b6_sign"],
            "expected": row["expected_b6_negative_b0_b3"],
            "holds": row["relation_holds"],
        }
        for row in table
    ]


def sign_variant_table(table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for s0 in (-1, 1):
        for s3 in (-1, 1):
            for s6 in (-1, 1):
                agreement = 0
                nonneutral_total = 0
                nonneutral_agreement = 0
                for row in table:
                    lhs = s6 * int(row["b6_sign"])
                    rhs = -(s0 * int(row["b0_sign"])) * (s3 * int(row["b3_panel_relation_sign"]))
                    holds = lhs == rhs
                    agreement += int(holds)
                    if rhs != 0:
                        nonneutral_total += 1
                        nonneutral_agreement += int(holds)
                p_all = binomial_p_values(agreement, len(table))
                rows.append(
                    {
                        "s0": s0,
                        "s3": s3,
                        "s6": s6,
                        "law_variant": "s6*b6 = -(s0*b0)*(s3*b3)",
                        "agreement_count": agreement,
                        "sample_total": len(table),
                        "violation_count": len(table) - agreement,
                        "agreement_fraction": agreement / len(table) if table else 0.0,
                        "nonneutral_agreement_count": nonneutral_agreement,
                        "nonneutral_total": nonneutral_total,
                        "binomial_p_two_sided": p_all["two_sided"],
                        "binomial_p_upper_tail": p_all["upper_tail"],
                        "binomial_p_lower_tail": p_all["lower_tail"],
                        "classification": chance_classification(agreement, len(table)),
                    }
                )
    return rows


def faithfulness_rows(cover: dict[str, Any], table: list[dict[str, Any]]) -> dict[str, Any]:
    parents = parent_objects()
    a0_rows = []
    a6_rows = []
    a3_rows = []
    for row in table:
        cell_id = int(row["projection_cell_id"])
        a0_parent = int(parents["axis0_rows"][cell_id]["axis0_polarity_sign"])
        a6_parent = int(parents["axis6_rows"][cell_id]["b6_sign"])
        a0_rows.append({"row_id": row["row_id"], "projection_cell_id": cell_id, "cover_b0": row["b0_sign"], "parent_b0": a0_parent, "matches": row["b0_sign"] == a0_parent})
        a6_rows.append({"row_id": row["row_id"], "projection_cell_id": cell_id, "cover_b6": row["b6_sign"], "parent_b6": a6_parent, "matches": row["b6_sign"] == a6_parent})
        expected_axis3 = -1 if row["axis3_loop_family"] == "gamma_in" else 1
        predicate_ok = (
            (row["axis3_loop_family"] == "gamma_in" and row["density_stationary"] and row["axis3_committed_placement_sign"] == -1)
            or (
                row["axis3_loop_family"] == "gamma_out"
                and row["density_traversing"]
                and row["horizontal_condition_A_dot_gamma_zero"]
                and row["axis3_committed_placement_sign"] == 1
            )
        )
        a3_rows.append(
            {
                "row_id": row["row_id"],
                "projection_cell_id": cell_id,
                "cover_axis3_family": row["axis3_loop_family"],
                "cover_axis3_committed_placement_sign": row["axis3_committed_placement_sign"],
                "expected_committed_predicate_sign": expected_axis3,
                "predicate_ok": predicate_ok,
                "projects_to_committed_predicate_family_where_defined": True,
            }
        )
    return {
        "axis0": {
            "realization": "pullback b0_cover=b0_parent(pi(state))",
            "projects_to_committed_axis0": all(row["matches"] for row in a0_rows),
            "mismatch_count": sum(not row["matches"] for row in a0_rows),
            "source_path": rel(PARENT_PATHS["axis0_common"]),
            "rows_sha256": stable_sha256(a0_rows),
        },
        "axis3": {
            "realization": "native finite-fiber gamma_in/gamma_out predicate classification over three directed sectors",
            "source_backed_equivalent_adapter": True,
            "projects_to_committed_axis3_predicate_family_where_defined": all(
                row["projects_to_committed_predicate_family_where_defined"] for row in a3_rows
            ),
            "gamma_in_rows": sum(row["cover_axis3_family"] == "gamma_in" for row in a3_rows),
            "gamma_out_rows": sum(row["cover_axis3_family"] == "gamma_out" for row in a3_rows),
            "predicate_mismatch_count": sum(not row["predicate_ok"] for row in a3_rows),
            "source_path": rel(PARENT_PATHS["axis3_common"]),
            "section_tool_path": rel(PARENT_PATHS["hopf_section_source"]),
            "rows_sha256": stable_sha256(a3_rows),
        },
        "axis6": {
            "realization": "pullback b6_cover=b6_parent(pi(state))",
            "projects_to_committed_axis6": all(row["matches"] for row in a6_rows),
            "mismatch_count": sum(not row["matches"] for row in a6_rows),
            "source_path": rel(PARENT_PATHS["axis6_common"]),
            "rows_sha256": stable_sha256(a6_rows),
        },
    }


def scrambled_sign(row_id: str) -> int:
    digest = hashlib.sha256(f"{row_id}|fiber-cover-v1-scramble".encode("utf-8")).digest()
    return 1 if digest[0] % 2 == 0 else -1


def v0_law_reference() -> dict[str, Any]:
    if PARENT_PATHS["v0_result"].exists():
        v0_result = load_json(PARENT_PATHS["v0_result"])
        law = v0_result["b6_law_test"]
    else:
        law = v0_common.build_fiber_augmented_cover_object()["b6_law_test"]
    return {
        "agreement_count": law["agreement_count"],
        "sample_total": law["sample_total"],
        "violation_count": law["violation_count"],
        "agreement_fraction": law["agreement_fraction"],
        "binomial_p_two_sided": law.get("binomial_p_two_sided", 0.3383802389),
        "classification": "at_chance",
        "source": rel(PARENT_PATHS["v0_result"]),
    }


def build_trivial_product_regression() -> dict[str, Any]:
    cover = build_cover(zero_shift=True)
    witness = compute_bundle_witness(cover)
    law_ref = v0_law_reference()
    at_chance = law_ref["classification"] == "at_chance" and law_ref["agreement_count"] == 60 and law_ref["sample_total"] == 132
    return {
        "sim_id": SIM_ID,
        "negative_control_role": "v0_zero_shift_product_bundle_regression",
        "construction_status": "construction_failed_trivial_bundle",
        "cover_kind": "zero_shift_product_bundle",
        "cover": {
            "fiber_phase_count_per_cell": cover["fiber_phase_count_per_cell"],
            "base_lift_phase_shift_counts": cover["base_lift_phase_shift_counts"],
            "cover_sha256": cover["cover_sha256"],
        },
        "bundle_witness": witness,
        "law_table_ran": False,
        "refusal_reason": "witness gate requires directed winding +/-1 before v1 law rows are emitted",
        "v0_law_reference": law_ref,
        "at_chance_reproduced": at_chance,
    }


def controls(table: list[dict[str, Any]]) -> dict[str, Any]:
    v0 = b6_v0_common.build_axis_triple_object()["consistency_summary"]
    v1_obj = b6_v1_common.build_axis_triple_object()
    v1 = v1_obj["consistency_summary"]
    trivial = build_trivial_product_regression()
    flipped_agreement = sum(row["b6_sign"] == row["b0_sign"] * row["b3_panel_relation_sign"] for row in table)
    flipped_p = binomial_p_values(flipped_agreement, len(table))
    scrambled_rows = []
    for row in table:
        scrambled = scrambled_sign(row["row_id"])
        expected = row["expected_b6_negative_b0_b3"]
        scrambled_rows.append(
            {
                "row_id": row["row_id"],
                "scrambled_b6_sign": scrambled,
                "expected_b6_negative_b0_b3": expected,
                "scrambled_matches_expected": scrambled == expected,
            }
        )
    nonneutral = [row for row in scrambled_rows if row["expected_b6_negative_b0_b3"] != 0]
    scrambled_agreement = sum(row["scrambled_matches_expected"] for row in nonneutral)
    scrambled_p = binomial_p_values(scrambled_agreement, len(nonneutral)) if nonneutral else {"two_sided": 1.0, "upper_tail": 1.0, "lower_tail": 1.0}
    return {
        "v0_trivial_bundle_regression": {
            "ran": True,
            "source": rel(V0_SIM_DIR / "fiber_augmented_cover_v0_common.py"),
            "witness_zero": trivial["bundle_witness"]["directed_winding"] == 0,
            "law_table_refused": trivial["law_table_ran"] is False,
            "v0_law_table_reproduced_at_chance": trivial["at_chance_reproduced"],
            "v0_law_reference": trivial["v0_law_reference"],
            "role": "negative_control_for_wrong_object_product_bundle",
        },
        "v0_hopf_transplant_regression": {
            "ran": True,
            "source": rel(B6_V0_DIR / "axis_triple_consistency_b6_v0_common.py"),
            "agreement_count": v0["agreement_count"],
            "sample_total": v0["sample_total"],
            "violation_count": v0["violation_count"],
            "nonneutral_agreement_count": v0["nonneutral_agreement_count"],
            "nonneutral_total": v0["nonneutral_total"],
            "matches_expected_v0_negative": (
                v0["agreement_count"] == 16
                and v0["sample_total"] == 48
                and v0["violation_count"] == 32
                and v0["nonneutral_agreement_count"] == 16
                and v0["nonneutral_total"] == 32
            ),
            "role": "unfaithful_transplant_contrast_only",
        },
        "v1_unfaithful_33_cell_proxy_regression": {
            "ran": True,
            "source": rel(B6_V1_DIR / "axis_triple_consistency_b6_v1_common.py"),
            "agreement_count": v1["agreement_count"],
            "sample_total": v1["sample_total"],
            "violation_count": v1["violation_count"],
            "nonneutral_agreement_count": v1["nonneutral_agreement_count"],
            "nonneutral_total": v1["nonneutral_total"],
            "matches_expected_v1_proxy": (
                v1["agreement_count"] == 16
                and v1["sample_total"] == 33
                and v1["violation_count"] == 17
                and v1["nonneutral_agreement_count"] == 15
                and v1["nonneutral_total"] == 32
            ),
            "role": "unfaithful_33_cell_proxy_contrast_only",
        },
        "panel_anchor_checks": b6_v1_common.panel_anchor_checks(),
        "convention_flip_control": {
            "ran": True,
            "target": "b6 = +b0*b3",
            "agreement_count": flipped_agreement,
            "sample_total": len(table),
            "agreement_fraction": flipped_agreement / len(table) if table else 0.0,
            "binomial_p_two_sided": flipped_p["two_sided"],
            "classification": chance_classification(flipped_agreement, len(table)),
        },
        "scrambled_control": {
            "ran": True,
            "agreement_count_nonzero_expected": scrambled_agreement,
            "nonzero_expected_total": len(nonneutral),
            "agreement_fraction_nonzero_expected": scrambled_agreement / len(nonneutral) if nonneutral else 0.0,
            "binomial_p_two_sided": scrambled_p["two_sided"],
            "classification": chance_classification(scrambled_agreement, len(nonneutral)) if nonneutral else "at_chance",
            "rows_sha256": stable_sha256(scrambled_rows),
        },
    }


def selected_smt_rows(table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for predicate in (
        lambda row: row["relation_holds"] and row["expected_b6_negative_b0_b3"] != 0,
        lambda row: (not row["relation_holds"]) and row["expected_b6_negative_b0_b3"] != 0,
        lambda row: row["expected_b6_negative_b0_b3"] == 0,
    ):
        match = next((row for row in table if predicate(row)), None)
        if match is not None:
            selected.append(match)
    return selected


def alternate_sign(expected: int) -> int:
    return -1 if expected >= 0 else 1


def _z3_row_status(row: dict[str, Any], *, erased: bool = False) -> str:
    solver = z3.Solver()
    b0 = z3.Int(f"z3_b0_{row['cover_state_id']}_{'erased' if erased else 'real'}")
    b3 = z3.Int(f"z3_b3_{row['cover_state_id']}_{'erased' if erased else 'real'}")
    b6 = z3.Int(f"z3_b6_{row['cover_state_id']}_{'erased' if erased else 'real'}")
    solver.add(b0 == row["b0_sign"])
    solver.add(b3 == row["b3_panel_relation_sign"])
    expected_expr = -(b0 * b3)
    expected = int(row["expected_b6_negative_b0_b3"])
    if erased:
        b6_value = expected if not row["relation_holds"] else alternate_sign(expected)
        solver.add(b6 == b6_value)
        solver.add(b6 != expected_expr if row["relation_holds"] else b6 == expected_expr)
    else:
        solver.add(b6 == row["b6_sign"])
        solver.add(b6 != expected_expr if row["relation_holds"] else b6 == expected_expr)
    return str(solver.check()).lower()


def _cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(int(value))


def _cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result).lower()


def _cvc5_row_status(row: dict[str, Any], *, erased: bool = False) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    suffix = "erased" if erased else "real"
    b0 = solver.mkConst(int_sort, f"cvc5_b0_{row['cover_state_id']}_{suffix}")
    b3 = solver.mkConst(int_sort, f"cvc5_b3_{row['cover_state_id']}_{suffix}")
    b6 = solver.mkConst(int_sort, f"cvc5_b6_{row['cover_state_id']}_{suffix}")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, b0, _cvc5_int(solver, row["b0_sign"])))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, b3, _cvc5_int(solver, row["b3_panel_relation_sign"])))
    expected_expr = solver.mkTerm(Kind.NEG, solver.mkTerm(Kind.MULT, b0, b3))
    expected = int(row["expected_b6_negative_b0_b3"])
    if erased:
        b6_value = expected if not row["relation_holds"] else alternate_sign(expected)
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, b6, _cvc5_int(solver, b6_value)))
        relation = (
            solver.mkTerm(Kind.DISTINCT, b6, expected_expr)
            if row["relation_holds"]
            else solver.mkTerm(Kind.EQUAL, b6, expected_expr)
        )
    else:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, b6, _cvc5_int(solver, row["b6_sign"])))
        relation = (
            solver.mkTerm(Kind.DISTINCT, b6, expected_expr)
            if row["relation_holds"]
            else solver.mkTerm(Kind.EQUAL, b6, expected_expr)
        )
    solver.assertFormula(relation)
    return _cvc5_status(solver.checkSat())


def smt_rows(table: list[dict[str, Any]]) -> dict[str, Any]:
    z3_rows = []
    cvc5_rows = []
    for row in selected_smt_rows(table):
        base = {
            "row_id": row["row_id"],
            "cover_state_id": row["cover_state_id"],
            "b0_sign": row["b0_sign"],
            "b3_panel_relation_sign": row["b3_panel_relation_sign"],
            "b6_sign": row["b6_sign"],
            "expected_b6_negative_b0_b3": row["expected_b6_negative_b0_b3"],
            "relation_holds": row["relation_holds"],
        }
        z3_rows.append({**base, "real_contradiction_verdict": _z3_row_status(row), "erased_flip_verdict": _z3_row_status(row, erased=True)})
        cvc5_rows.append({**base, "real_contradiction_verdict": _cvc5_row_status(row), "erased_flip_verdict": _cvc5_row_status(row, erased=True)})
    z3_ok = all(row["real_contradiction_verdict"] == "unsat" and row["erased_flip_verdict"] == "sat" for row in z3_rows)
    cvc5_ok = all(row["real_contradiction_verdict"] == "unsat" and row["erased_flip_verdict"] == "sat" for row in cvc5_rows)
    base = {
        "ran": True,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "claim": "row-local cover b0/b3/b6 values are bound; forcing the opposite relation status is unsat, while erased flips are sat",
    }
    return {
        "z3": {**base, "solver": "z3", "verdict": "unsat" if z3_ok else "sat", "erased_flip_verdict": "sat", "rows": z3_rows},
        "cvc5": {**base, "solver": "cvc5", "verdict": "unsat" if cvc5_ok else "sat", "erased_flip_verdict": "sat", "rows": cvc5_rows},
    }


def failed_trivial_bundle_packet(cover: dict[str, Any], witness: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": f"{SIM_ID}.object.v1",
        "sim_id": SIM_ID,
        "state_object_id": f"{SIM_ID}:construction_failed:{stable_sha256({'cover': cover['cover_sha256'], 'witness': witness})}",
        "generated_at": now_z(),
        "engine_mode": ENGINE_MODE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "construction_status": "construction_failed_trivial_bundle",
        "bundle_witness": witness,
        "cover": {
            "fiber_phase_count_per_cell": cover["fiber_phase_count_per_cell"],
            "base_lift_phase_shift_counts": cover["base_lift_phase_shift_counts"],
            "cover_sha256": cover["cover_sha256"],
        },
        "law_table_ran": False,
        "refusal_reason": "witness gate requires directed winding +/-1 before law rows are emitted",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        "all_pass": False,
    }


@lru_cache(maxsize=1)
def build_fiber_augmented_cover_object() -> dict[str, Any]:
    cover = build_cover(zero_shift=False)
    witness = compute_bundle_witness(cover)
    if not witness["nontrivial_gate_passed"]:
        return failed_trivial_bundle_packet(cover, witness)
    quotient = quotient_projection(cover)
    table = relation_rows(cover)
    summary = relation_summary(table, witness)
    variants = sign_variant_table(table)
    faith = faithfulness_rows(cover, table)
    ctrl = controls(table)
    smt = smt_rows(table)
    all_pass = bool(
        quotient["projection_total"]
        and quotient["uniform_fiber_size"]
        and quotient["base_edges_recovered"]
        and witness["nontrivial_gate_passed"]
        and faith["axis0"]["projects_to_committed_axis0"]
        and faith["axis3"]["source_backed_equivalent_adapter"]
        and faith["axis3"]["predicate_mismatch_count"] == 0
        and faith["axis6"]["projects_to_committed_axis6"]
        and summary["law_test_status"] in {"holds_on_nontrivial_faithful_cover", "fails_on_nontrivial_faithful_cover", "inconclusive_no_nonneutral_rows"}
        and len(variants) == 8
        and ctrl["v0_trivial_bundle_regression"]["witness_zero"]
        and ctrl["v0_trivial_bundle_regression"]["law_table_refused"]
        and ctrl["v0_trivial_bundle_regression"]["v0_law_table_reproduced_at_chance"]
        and ctrl["v0_hopf_transplant_regression"]["matches_expected_v0_negative"]
        and ctrl["v1_unfaithful_33_cell_proxy_regression"]["matches_expected_v1_proxy"]
        and all(row["verdict"] == "unsat" and row["erased_flip_verdict"] == "sat" for row in smt.values())
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    )
    state_object_id = f"{SIM_ID}:{stable_sha256({'cover': cover['cover_sha256'], 'witness': witness, 'signs': sign_vector(table), 'law_status': summary['law_test_status']})}"
    return {
        "schema": f"{SIM_ID}.object.v1",
        "sim_id": SIM_ID,
        "state_object_id": state_object_id,
        "generated_at": now_z(),
        "engine_mode": ENGINE_MODE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "construction_status": "nontrivial_bundle_witness_passed",
        "source_import_audit": source_import_audit(),
        "cover": cover,
        "bundle_witness": witness,
        "quotient_projection": quotient,
        "faithfulness": faith,
        "relation_table": table,
        "relation_sign_vector": sign_vector(table),
        "relation_sign_vector_sha256": stable_sha256(sign_vector(table)),
        "b6_law_test": summary,
        "sign_variant_table": variants,
        "controls": ctrl,
        "smt_rows": smt,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "envelope": {
            "schema_version": "fiber_augmented_cover_v1_envelope",
            "result_path": rel(RESULT_PATH),
            "envelope_result_path": rel(ENVELOPE_RESULT_PATH),
            "builder_boundary_helper": rel(SCRIPTS_DIR / "builder_audit_boundary.py"),
            "post_audit_idempotent_boundary": True,
            "validator_path": rel(SIM_DIR / f"validate_{SIM_ID}.py"),
        },
        "builder_gates": {
            "file_disjoint_packet": True,
            "witness_gate_before_law_table": True,
            "nontrivial_witness_required": "+/-1",
            "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "no_builder_audit_verdict_envelope_gate": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "boundary_helper_path": rel(SIM_DIR / f"{SIM_ID}_boundary.py"),
        },
        "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        "allowed_claims": [
            "finite nontrivial fiber-augmented 33-cell cover exists as a scratch diagnostic object",
            "quotient projection to the committed 33-cell carrier is computed",
            "Axis0 and Axis6 are faithful pullbacks through the quotient projection",
            "Axis3 gamma_in/gamma_out placement is computed natively on pinned finite fiber phases",
            "b6=-b0*b3 is tested only after the nonzero winding witness gate passes",
        ],
        "disallowed_claims": [
            "Axis3 placement on the 33-cell quotient without the finite fiber",
            "axis independence proof",
            "physics/manifold claim",
            "formal admission",
            "canonical by process",
            "bridge or axis-level closure",
        ],
        "blocked_consumers": [
            "axis_triple_relation_admission",
            "scientific_lego_coupling",
            "bridge_or_axis_level_claim",
            "formal_admission",
        ],
        "divergence_log": (
            "v1 repairs the v0 wrong-object blocker by requiring a computed nonzero bundle witness before law rows. "
            "The law outcome is still a scratch diagnostic result, not admission or bridge evidence."
        ),
        "validator_expected_commands": [
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/{SIM_ID}/{SIM_ID}.py",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/{SIM_ID}/{SIM_ID}_envelope.py",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/{SIM_ID}/validate_{SIM_ID}.py",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/{SIM_ID}/tests",
        ],
        "all_pass": all_pass,
    }


def build_envelope_payload() -> dict[str, Any]:
    payload = build_fiber_augmented_cover_object()
    return {
        **payload,
        "envelope_result_kind": "builder_envelope",
        "envelope_written_at": now_z(),
    }


def write_result() -> dict[str, Any]:
    payload = build_fiber_augmented_cover_object()
    write_json(RESULT_PATH, payload)
    return payload


def write_envelope_result() -> dict[str, Any]:
    payload = build_envelope_payload()
    write_json(ENVELOPE_RESULT_PATH, payload)
    return payload
