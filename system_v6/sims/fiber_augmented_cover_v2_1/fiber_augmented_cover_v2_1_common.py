#!/usr/bin/env python3
"""Decisive finite-clutching repair for the fiber augmented cover.

This packet keeps the v2 cellular base fixed and re-pins the finite fiber
clutching data so the mod-|F| seam holonomy, not the old integer-lift winding,
is the witness gate.
"""

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


SIM_ID = "fiber_augmented_cover_v2_1"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

FIBER_V2_DIR = ROOT / "system_v6" / "sims" / "fiber_augmented_cover_v2"
FIBER_V1_DIR = ROOT / "system_v6" / "sims" / "fiber_augmented_cover_v1"
GUARD_V2_DIR = ROOT / "system_v6" / "sims" / "topology_parity_guard_v2"
SCRIPTS_DIR = ROOT / "scripts"

for path in (FIBER_V2_DIR, FIBER_V1_DIR, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402
import fiber_augmented_cover_v1_common as v1_common  # noqa: E402
import fiber_augmented_cover_v2_common as v2_common  # noqa: E402


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "axis_readout_candidate_only + decisive_repair_cover_no_admission"
SCHEMA = f"{SIM_ID}.object.v1"

FIBER_PHASE_COUNT = 3
SEAM_LOOP_CELLS = [20, 17, 12, 15]
V2_1_SEAM_STEPS = [1, 0, 0, 0]
ZERO_SEAM_STEPS = [0, 0, 0, 0]
OLD_V2_SEAM_STEPS = [1, 1, 1, 0]
WRONG_GLUE_SEAM_STEPS = [1, 0, 0, 0]

EXPECTED_V2_BASE_CHAIN_SHA256 = "9d6655a51782305f80409cce0bd42a57329fb14ea19b05c32b95ec36016b883c"
SOURCE_COMMITS = {
    "guard_v2_audit": "2137ae3e8",
    "fiber_augmented_cover_v2": "cc2f61b2a",
}

TOOL_MANIFEST = {
    "fiber_augmented_cover_v2_common": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source for the unchanged v2 cellular base and source hash lock",
    },
    "fiber_augmented_cover_v1_common": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source for axis realizations, law rows, sign variants, controls, and SMT rows",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite clutching bookkeeping, sparse chain emission, hashing, and result serialization",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing row-local erased-flip contradiction checks through v1 law machinery",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent row-local erased-flip contradiction checks through v1 law machinery",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "load-bearing G.2a idempotency-from-birth builder/audit boundary",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "fiber_augmented_cover_v2_common": "load_bearing",
    "fiber_augmented_cover_v1_common": "load_bearing",
    "python_stdlib": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "builder_audit_boundary": "load_bearing",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def seam_pairs() -> list[tuple[int, int]]:
    return list(zip(SEAM_LOOP_CELLS, SEAM_LOOP_CELLS[1:] + SEAM_LOOP_CELLS[:1]))


def seam_step_map(steps: list[int]) -> dict[tuple[int, int], int]:
    return {pair: int(step) for pair, step in zip(seam_pairs(), steps)}


def canonical_edge_shift(edge: dict[str, Any], steps: list[int]) -> int:
    mapping = seam_step_map(steps)
    src = int(edge["src"])
    dst = int(edge["dst"])
    if (src, dst) in mapping:
        return mapping[(src, dst)] % FIBER_PHASE_COUNT
    if (dst, src) in mapping:
        return (-mapping[(dst, src)]) % FIBER_PHASE_COUNT
    return 0


def add_entry(entries: dict[tuple[int, int], int], row: int, col: int, value: int) -> None:
    if value == 0:
        return
    key = (int(row), int(col))
    entries[key] = entries.get(key, 0) + int(value)
    if entries[key] == 0:
        del entries[key]


def sparse_matrix(rows: int, cols: int, entries: dict[tuple[int, int], int], role: str) -> dict[str, Any]:
    coo = [
        {"row": row, "col": col, "value": value}
        for (row, col), value in sorted(entries.items(), key=lambda item: (item[0][1], item[0][0]))
    ]
    return {
        "role": role,
        "format": "sparse_coo",
        "shape": [rows, cols],
        "entry_count": len(coo),
        "entries": coo,
        "sha256": stable_sha256({"shape": [rows, cols], "entries": coo}),
    }


def compose(left: dict[str, Any], right: dict[str, Any]) -> dict[tuple[int, int], int]:
    if left["shape"][1] != right["shape"][0]:
        raise ValueError(f"shape mismatch: {left['shape']} after {right['shape']}")
    left_by_col: dict[int, list[tuple[int, int]]] = {}
    for item in left["entries"]:
        left_by_col.setdefault(int(item["col"]), []).append((int(item["row"]), int(item["value"])))
    product: dict[tuple[int, int], int] = {}
    for item in right["entries"]:
        mid = int(item["row"])
        right_col = int(item["col"])
        right_value = int(item["value"])
        for left_row, left_value in left_by_col.get(mid, []):
            add_entry(product, left_row, right_col, left_value * right_value)
    return product


def chain_checks(boundaries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks: dict[str, Any] = {"d_squared_zero": True, "composition_errors": [], "composition_entry_counts": {}}
    for left_name, right_name in (("d1", "d2"), ("d2", "d3")):
        product = compose(boundaries[left_name], boundaries[right_name])
        checks["composition_entry_counts"][f"{left_name}_{right_name}"] = len(product)
        if product:
            checks["d_squared_zero"] = False
            checks["composition_errors"].append(
                {
                    "composition": f"{left_name}*{right_name}",
                    "nonzero_entry_count": len(product),
                    "sample": [
                        {"row": row, "col": col, "value": value}
                        for (row, col), value in sorted(product.items())[:12]
                    ],
                }
            )
    return checks


@lru_cache(maxsize=1)
def v2_base() -> dict[str, Any]:
    return v2_common.build_cellular_base()


def holonomy_witness(complex_id: str, steps: list[int]) -> dict[str, Any]:
    loop_rows = []
    integer_sum = 0
    for (src, dst), step in zip(seam_pairs(), steps):
        step_int = int(step)
        integer_sum += step_int
        loop_rows.append(
            {
                "src": src,
                "dst": dst,
                "integer_lift_step": step_int,
                "mod_fiber_step": step_int % FIBER_PHASE_COUNT,
            }
        )
    mod_holonomy = integer_sum % FIBER_PHASE_COUNT
    old_integer_winding = integer_sum // FIBER_PHASE_COUNT if integer_sum % FIBER_PHASE_COUNT == 0 else None
    return {
        "complex_id": complex_id,
        "base_loop_cell_ids": SEAM_LOOP_CELLS,
        "fiber_phase_count": FIBER_PHASE_COUNT,
        "loop_rows": loop_rows,
        "integer_lift_sum": integer_sum,
        "old_integer_lift_winding_if_divisible": old_integer_winding,
        "mod_fiber_holonomy": mod_holonomy,
        "mod_holonomy_is_generator": mod_holonomy in {1, 2},
        "mod_holonomy_is_pinned_degree_one": mod_holonomy == 1,
        "finite_witness_gate_passed": mod_holonomy == 1,
        "witness_rule": "sum seam shifts mod |F|; v2.1 positive requires holonomy 1 mod 3, not integer-lift sum 3",
        "witness_sha256": stable_sha256(loop_rows),
    }


def build_repin_cover(base: dict[str, Any], steps: list[int], family: str) -> dict[str, Any]:
    states = []
    parent_cells = {int(row["cell_id"]): row for row in v2_common.parent_carrier()["cells"]}
    for vertex in base["cells"]["C0"]:
        cell_id = int(vertex["cell_id"])
        parent_cell = parent_cells[cell_id]
        for phase_slot in range(FIBER_PHASE_COUNT):
            axis3 = v1_common.axis3_predicate_row(parent_cell, phase_slot)
            states.append(
                {
                    "cover_state_id": cell_id * FIBER_PHASE_COUNT + phase_slot,
                    "cover_state_label": f"c{cell_id:02d}:v2_1_phase_{phase_slot}",
                    "projection_cell_id": cell_id,
                    "base_coord_scaled": vertex["coord_scaled"],
                    "fiber_phase_slot": phase_slot,
                    "fiber_phase_label": v1_common.phase_label(phase_slot),
                    "fiber_phase_radians": v1_common.phase_value(phase_slot),
                    "axis3_loop_family": axis3["pinned_family_formula"],
                    "axis3_predicate": axis3,
                }
            )

    horizontal_edges = []
    transition_rows = []
    for edge in base["cells"]["C1"]:
        shift = canonical_edge_shift(edge, steps)
        transition_rows.append(
            {
                "cellular_edge_id": int(edge["edge_id"]),
                "src": int(edge["src"]),
                "dst": int(edge["dst"]),
                "fiber_phase_shift_steps": shift,
                "transition_family": family,
            }
        )
        for phase in range(FIBER_PHASE_COUNT):
            horizontal_edges.append(
                {
                    "cover_edge_id": f"v2_1_cellular:{edge['edge_id']}:phase:{phase}:shift:{shift}",
                    "edge_type": "cellular_base_lift",
                    "src": int(edge["src"]) * FIBER_PHASE_COUNT + phase,
                    "dst": int(edge["dst"]) * FIBER_PHASE_COUNT + ((phase + shift) % FIBER_PHASE_COUNT),
                    "cellular_edge_id": int(edge["edge_id"]),
                    "projection_src": int(edge["src"]),
                    "projection_dst": int(edge["dst"]),
                    "fiber_phase_slot": phase,
                    "fiber_phase_shift_steps": shift,
                }
            )

    fiber_edges = []
    for vertex in base["cells"]["C0"]:
        cell_id = int(vertex["cell_id"])
        for phase in range(FIBER_PHASE_COUNT):
            fiber_edges.append(
                {
                    "cover_edge_id": f"v2_1_fiber:{cell_id}:{phase}",
                    "edge_type": "fiber_cycle",
                    "src": cell_id * FIBER_PHASE_COUNT + phase,
                    "dst": cell_id * FIBER_PHASE_COUNT + ((phase + 1) % FIBER_PHASE_COUNT),
                    "projection_cell_id": cell_id,
                    "fiber_phase_slot": phase,
                }
            )

    cover = {
        "cover_kind": family,
        "base_state_count": 33,
        "cellular_base_edge_count": len(base["cells"]["C1"]),
        "fiber_phase_count_per_cell": FIBER_PHASE_COUNT,
        "cover_state_count": len(states),
        "cellular_base_lift_edge_count": len(horizontal_edges),
        "fiber_cycle_edge_count": len(fiber_edges),
        "cover_edge_count": len(horizontal_edges) + len(fiber_edges),
        "states": states,
        "cellular_base_lift_edges": horizontal_edges,
        "fiber_edges": fiber_edges,
        "chart_transition_rows": transition_rows,
        "base_lift_phase_shift_counts": {str(key): value for key, value in sorted(Counter(row["fiber_phase_shift_steps"] for row in horizontal_edges).items())},
    }
    cover["cover_sha256"] = stable_sha256(
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
            "cover_edge_count": cover["cover_edge_count"],
        }
    )
    return cover


def build_clutching_complex(
    complex_id: str,
    role: str,
    steps: list[int],
    attachment_coefficient: int,
    threading_required: bool,
    refusal_reason: str | None = None,
) -> dict[str, Any]:
    d1 = sparse_matrix(1, 1, {}, f"{complex_id}_C1_to_C0")
    d2_entries: dict[tuple[int, int], int] = {}
    add_entry(d2_entries, 0, 0, int(attachment_coefficient))
    d2 = sparse_matrix(1, 1, d2_entries, f"{complex_id}_C2_to_C1")
    d3 = sparse_matrix(1, 1, {}, f"{complex_id}_C3_to_C2")
    boundaries = {"d1": d1, "d2": d2, "d3": d3}
    witness = holonomy_witness(complex_id, steps)
    threaded = witness["finite_witness_gate_passed"] and int(attachment_coefficient) == FIBER_PHASE_COUNT
    gate_passed = threaded if threading_required else not threaded
    payload = {
        "complex_id": complex_id,
        "complex_role": role,
        "classification": CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "cell_counts": {"C0": 1, "C1": 1, "C2": 1, "C3": 1},
        "cell_model_note": "guard-facing finite clutching quotient complex pinned to the unchanged v2 cellular base hash",
        "v2_base_chain_sha256": EXPECTED_V2_BASE_CHAIN_SHA256,
        "clutching": {
            "fiber_phase_count": FIBER_PHASE_COUNT,
            "seam_steps": steps,
            "attaches_fiber_cycle_with_coefficient": int(attachment_coefficient),
            "threading_required": threading_required,
            "threading_gate_passed": threaded,
            "gate_passed": gate_passed,
            "refusal_reason": refusal_reason,
        },
        "integer_lift_and_mod_holonomy": witness,
        "boundary_matrices": boundaries,
        "chain_checks": chain_checks(boundaries),
        "betti_computed": False,
        "homology_computed": False,
    }
    payload["chain_sha256"] = stable_sha256(
        {
            "complex_id": complex_id,
            "cell_counts": payload["cell_counts"],
            "clutching": payload["clutching"],
            "holonomy": witness,
            "boundary_hashes": {name: matrix["sha256"] for name, matrix in boundaries.items()},
        }
    )
    return payload


def build_complex_family() -> dict[str, Any]:
    shifted = build_clutching_complex(
        "v2_1_shifted_degree_one_mod3",
        "positive decisive repair complex; mod-3 seam holonomy 1 with fiber-order torsion attachment",
        V2_1_SEAM_STEPS,
        FIBER_PHASE_COUNT,
        True,
    )
    zero = build_clutching_complex(
        "zero_shift_product_control",
        "zero-shift product control; finite holonomy 0",
        ZERO_SEAM_STEPS,
        0,
        False,
        "finite holonomy is 0, so the witness gate refuses the shifted claim",
    )
    wrong = build_clutching_complex(
        "wrong_gluing_generator_not_threaded_control",
        "wrong-gluing control; generator seam row is present but the chain attachment is not threaded",
        WRONG_GLUE_SEAM_STEPS,
        0,
        False,
        "generator holonomy without the fiber-order attachment is not an admissible repaired complex",
    )
    old = build_clutching_complex(
        "old_v2_regression_coboundary_control",
        "old v2 shifts rebuilt as a negative control; integer-lift sum 3 but finite holonomy 0",
        OLD_V2_SEAM_STEPS,
        0,
        False,
        "old v2 shifts reduce to 0 mod 3 and reproduce the finite-trivial control",
    )
    complexes = [shifted, zero, wrong, old]
    return {
        "family_role": "guard_v3_input_family_no_betti",
        "complexes": {row["complex_id"]: row for row in complexes},
        "complex_order": [row["complex_id"] for row in complexes],
        "chain_hashes": {row["complex_id"]: row["chain_sha256"] for row in complexes},
        "boundary_hashes": {
            row["complex_id"]: {name: matrix["sha256"] for name, matrix in row["boundary_matrices"].items()}
            for row in complexes
        },
        "all_d_squared_zero": all(row["chain_checks"]["d_squared_zero"] for row in complexes),
        "betti_computed": False,
        "homology_computed": False,
    }


def quotient_projection(cover: dict[str, Any]) -> dict[str, Any]:
    fiber_sizes = Counter(int(row["projection_cell_id"]) for row in cover["states"])
    return {
        "map": "pi_v2_1_cover_to_committed_v2_base_axis_cell(cover_state_id)=projection_cell_id",
        "projection_total": len(fiber_sizes) == 33 and sum(fiber_sizes.values()) == cover["cover_state_count"],
        "uniform_fiber_size": set(fiber_sizes.values()) == {FIBER_PHASE_COUNT},
        "fiber_size_by_cell": {str(key): value for key, value in sorted(fiber_sizes.items())},
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
    }


def relation_summary(table: list[dict[str, Any]], witness: dict[str, Any]) -> dict[str, Any]:
    total = len(table)
    agreement = sum(row["relation_holds"] for row in table)
    nonneutral = [row for row in table if row["expected_b6_negative_b0_b3"] != 0]
    nonneutral_agreement = sum(row["relation_holds"] for row in nonneutral)
    p_all = v1_common.binomial_p_values(agreement, total)
    p_nonneutral = (
        v1_common.binomial_p_values(nonneutral_agreement, len(nonneutral))
        if nonneutral
        else {"lower_tail": 1.0, "upper_tail": 1.0, "two_sided": 1.0}
    )
    if not nonneutral:
        status = "inconclusive_no_nonneutral_rows"
    elif agreement == total:
        status = "holds_on_decisive_repin_cover"
    else:
        status = "fails_on_decisive_repin_cover"
    return {
        "law": "b6 = -b0*b3",
        "table_kind": "faithful_decisive_repin_fiber_augmented_cover_table",
        "construction_row": "third_construction_v2_1_mod3_repin",
        "witness_gate_required": True,
        "witness_gate": "mod_fiber_holonomy_equals_1",
        "witness_gate_passed": witness["finite_witness_gate_passed"],
        "sample_unit": "cover_state",
        "sample_total": total,
        "base_cell_total": 33,
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
        "chance_classification": v1_common.chance_classification(agreement, total),
        "law_test_status": status,
        "relation_not_used_to_assign_axis3": True,
        "relation_can_fail": any(not row["relation_holds"] for row in table),
        "outcome_is_the_result": True,
    }


def old_v2_regression_control(family: dict[str, Any]) -> dict[str, Any]:
    row = family["complexes"]["old_v2_regression_coboundary_control"]
    return {
        "control_role": "v2_regression_old_shifts_rebuilt",
        "old_v2_seam_steps": OLD_V2_SEAM_STEPS,
        "integer_lift_sum": row["integer_lift_and_mod_holonomy"]["integer_lift_sum"],
        "old_integer_lift_winding_if_divisible": row["integer_lift_and_mod_holonomy"]["old_integer_lift_winding_if_divisible"],
        "mod_fiber_holonomy": row["integer_lift_and_mod_holonomy"]["mod_fiber_holonomy"],
        "finite_triviality_reproduced": row["integer_lift_and_mod_holonomy"]["mod_fiber_holonomy"] == 0,
        "complex_sha256": row["chain_sha256"],
        "negative_control_note": "the old construction's integer-lift winding remains recorded, but its finite mod-3 holonomy is 0",
    }


def controls(table: list[dict[str, Any]], family: dict[str, Any]) -> dict[str, Any]:
    carried = v1_common.controls(table)
    carried["zero_shift_product_control"] = {
        "control_role": "zero_shift_product_control",
        "complex_sha256": family["complexes"]["zero_shift_product_control"]["chain_sha256"],
        "finite_holonomy": family["complexes"]["zero_shift_product_control"]["integer_lift_and_mod_holonomy"]["mod_fiber_holonomy"],
        "law_table_ran": False,
        "law_table_refused": True,
        "refusal_reason": "finite holonomy gate requires 1 mod 3",
    }
    carried["wrong_gluing_control"] = {
        "control_role": "wrong_gluing_generator_not_threaded_control",
        "complex_sha256": family["complexes"]["wrong_gluing_generator_not_threaded_control"]["chain_sha256"],
        "finite_holonomy": family["complexes"]["wrong_gluing_generator_not_threaded_control"]["integer_lift_and_mod_holonomy"]["mod_fiber_holonomy"],
        "threading_gate_passed": family["complexes"]["wrong_gluing_generator_not_threaded_control"]["clutching"]["threading_gate_passed"],
        "law_table_ran": False,
        "law_table_refused": True,
        "refusal_reason": "generator holonomy without fiber-order chain attachment is a wrong-gluing control",
    }
    carried["v2_regression_old_shifts"] = old_v2_regression_control(family)
    return carried


def source_import_audit(base: dict[str, Any]) -> dict[str, Any]:
    return {
        "guard_v2_audit": source_lock(
            GUARD_V2_DIR / "audit_verdict.md",
            "2137ae3e8_guard_v2_diagnosis_old_shifts_coboundary_repair_contract",
            SOURCE_COMMITS["guard_v2_audit"],
        ),
        "axis_work_order": source_lock(
            ROOT / "system_v6/receipts/axis_work_order_20260612.md",
            "b6_status_update_3_two_live_readings_and_decisive_test",
        ),
        "fiber_augmented_cover_v2_common": source_lock(
            FIBER_V2_DIR / "fiber_augmented_cover_v2_common.py",
            "cc2f61b2a_v2_committed_cw_machinery_extended",
            SOURCE_COMMITS["fiber_augmented_cover_v2"],
        ),
        "fiber_augmented_cover_v2_results": source_lock(
            FIBER_V2_DIR / "results/fiber_augmented_cover_v2_results.json",
            "cc2f61b2a_v2_result_surface_for_base_hash_regression",
            SOURCE_COMMITS["fiber_augmented_cover_v2"],
        ),
        "audit_standards_codex": source_lock(
            ROOT / "system_v6/receipts/audit_standards_codex_v1.md",
            "G.2a_from_birth_and_standards_codex",
        ),
        "v2_base_chain_sha256": base["chain_sha256"],
        "v2_base_hash_matches_guard_lock": base["chain_sha256"] == EXPECTED_V2_BASE_CHAIN_SHA256,
    }


@lru_cache(maxsize=1)
def build_fiber_augmented_cover_v2_1_object() -> dict[str, Any]:
    base = v2_base()
    cover = build_repin_cover(base, V2_1_SEAM_STEPS, "v2_1_mod3_degree_one_repin")
    positive_witness = holonomy_witness("v2_1_shifted_degree_one_mod3", V2_1_SEAM_STEPS)
    family = build_complex_family()
    shifted = family["complexes"]["v2_1_shifted_degree_one_mod3"]
    table = v1_common.relation_rows(cover)
    summary = relation_summary(table, positive_witness)
    variants = v1_common.sign_variant_table(table)
    faith = v1_common.faithfulness_rows(cover, table)
    ctrl = controls(table, family)
    smt = v1_common.smt_rows(table)
    boundary_ok = builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    base_hash_ok = base["chain_sha256"] == EXPECTED_V2_BASE_CHAIN_SHA256
    all_pass = bool(
        base_hash_ok
        and base["chain_checks"]["d_squared_zero"]
        and positive_witness["mod_fiber_holonomy"] == 1
        and shifted["clutching"]["attaches_fiber_cycle_with_coefficient"] == FIBER_PHASE_COUNT
        and shifted["clutching"]["threading_gate_passed"] is True
        and family["all_d_squared_zero"]
        and family["complexes"]["zero_shift_product_control"]["integer_lift_and_mod_holonomy"]["mod_fiber_holonomy"] == 0
        and family["complexes"]["wrong_gluing_generator_not_threaded_control"]["clutching"]["threading_gate_passed"] is False
        and ctrl["v2_regression_old_shifts"]["finite_triviality_reproduced"] is True
        and summary["sample_total"] == 99
        and faith["axis0"]["projects_to_committed_axis0"]
        and faith["axis3"]["source_backed_equivalent_adapter"]
        and faith["axis3"]["predicate_mismatch_count"] == 0
        and faith["axis6"]["projects_to_committed_axis6"]
        and len(variants) == 8
        and all(row["verdict"] == "unsat" and row["erased_flip_verdict"] == "sat" for row in smt.values())
        and boundary_ok
    )
    return {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "state_object_id": f"{SIM_ID}:{stable_sha256({'base': base['chain_sha256'], 'family': family['chain_hashes'], 'law': summary})}",
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "engine_contract": {
            "mode": "single_python_finite_clutching_chain_packet",
            "three_engine_scoped": False,
            "three_engine_not_scoped_reason": "v2.1 emits hash-pinned finite clutching chain complexes and law rows; no independent Julia/JAX/PyTorch parity claim is made",
        },
        "source_import_audit": source_import_audit(base),
        "central_math_adjudication": {
            "old_v1_v2_status": "old shifts [1,1,1,0] have integer-lift sum 3 and old winding 1, but mod-3 holonomy 0; they are not reinterpreted as finite-nontrivial",
            "v2_1_status": "different pinned construction registered by kill-then-earn cycle",
            "v2_1_seam_steps": V2_1_SEAM_STEPS,
            "v2_1_mod_fiber_holonomy": positive_witness["mod_fiber_holonomy"],
            "v2_1_integer_lift_sum": positive_witness["integer_lift_sum"],
            "finite_witness_gate": "accept only mod-3 holonomy 1 for the positive degree-1 re-pin",
            "two_live_readings_settled_for_builder": "reading B killed for this new pinned construction if guard v3 confirms the threaded complex; old construction remains finite-trivial negative control",
            "not_a_reinterpretation_of_old_construction": True,
        },
        "cellular_base": {
            "source": "fiber_augmented_cover_v2",
            "v2_base_unchanged_by_hash": base_hash_ok,
            "chain_sha256": base["chain_sha256"],
            "expected_chain_sha256": EXPECTED_V2_BASE_CHAIN_SHA256,
            "cell_counts": base["cell_counts"],
            "euler_characteristic": base["euler_characteristic"],
            "boundary_hashes": {name: matrix["sha256"] for name, matrix in base["boundary_matrices"].items()},
            "chain_checks": base["chain_checks"],
        },
        "cover": cover,
        "quotient_projection": quotient_projection(cover),
        "integer_lift_rows": [
            family["complexes"][complex_id]["integer_lift_and_mod_holonomy"]
            for complex_id in family["complex_order"]
        ],
        "complex_family": family,
        "faithfulness": faith,
        "relation_table": table,
        "relation_sign_vector": v1_common.sign_vector(table),
        "relation_sign_vector_sha256": stable_sha256(v1_common.sign_vector(table)),
        "b6_law_test": summary,
        "sign_variant_table": variants,
        "controls": ctrl,
        "smt_rows": smt,
        "betti_computed": False,
        "homology_computed": False,
        "consumer_boundary": {
            "intended_consumer": "topology_parity_guard_v3",
            "allowed_next_use": "consume the shifted, zero-shift, wrong-gluing, and old-v2-regression chain complexes and compute torsion-aware homology outside this builder packet",
            "blocked_use": "do not cite Betti, homology, topology admission, bridge, physics, manifold, axis closure, or formal admission from this builder packet",
            "builder_consumer_separation": True,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "no_builder_audit_verdict": boundary_ok,
        "no_builder_audit_verdict_envelope_gate": boundary_ok,
        "builder_gates": {
            "file_disjoint_packet": True,
            "g2a_boundary_from_birth": boundary_ok,
            "v2_base_hash_unchanged": base_hash_ok,
            "mod_3_holonomy_positive_generator_gate": positive_witness["finite_witness_gate_passed"],
            "old_v2_regression_mod_3_zero": ctrl["v2_regression_old_shifts"]["finite_triviality_reproduced"],
            "full_control_family_emitted": set(family["complex_order"]) == {
                "v2_1_shifted_degree_one_mod3",
                "zero_shift_product_control",
                "wrong_gluing_generator_not_threaded_control",
                "old_v2_regression_coboundary_control",
            },
            "all_complexes_d_squared_zero": family["all_d_squared_zero"],
            "no_betti_computation": True,
            "boundary_helper_path": rel(SIM_DIR / f"{SIM_ID}_boundary.py"),
            "shared_boundary_helper": rel(SCRIPTS_DIR / "builder_audit_boundary.py"),
        },
        "allowed_claims": [
            "v2.1 keeps the v2 CW base unchanged by hash",
            "v2.1 is a different pinned finite clutching construction with seam holonomy 1 mod 3",
            "v2.1 emits shifted, zero-shift, wrong-gluing, and old-v2-regression complexes with d^2=0 for guard v3",
            "v2.1 records both mod-3 holonomy and integer-lift sum for the emitted complexes",
            "v2.1 recomputes Axis0, Axis3, and Axis6 faithfulness obligations and the b6 law table at scratch ceiling",
        ],
        "disallowed_claims": [
            "Betti computation",
            "homology certificate",
            "lens-space certificate",
            "SECOND certificate",
            "formal admission",
            "canonical by process",
            "axis independence proof",
            "bridge or axis-level closure",
            "physics/manifold claim",
            "global disproof of b6 law",
        ],
        "blocked_consumers": [
            "formal_admission",
            "axis_triple_relation_admission",
            "topology_admission_without_guard_v3",
            "bridge_or_physics_or_manifold_claim",
        ],
        "divergence_log": (
            "v2.1 kills the old finite-nontrivial label for the [1,1,1,0] shifts by recording "
            "their mod-3 holonomy as 0, then registers a new [1,0,0,0] finite clutching pin."
        ),
        "validator_expected_commands": [
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/{SIM_ID}/{SIM_ID}.py",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/{SIM_ID}/{SIM_ID}_envelope.py",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/{SIM_ID}/validate_{SIM_ID}.py",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/{SIM_ID}/tests",
        ],
        "all_pass": all_pass,
        "result_summary": {
            "v2_base_unchanged_by_hash": base_hash_ok,
            "positive_mod_3_holonomy": positive_witness["mod_fiber_holonomy"],
            "positive_integer_lift_sum": positive_witness["integer_lift_sum"],
            "old_v2_mod_3_holonomy": ctrl["v2_regression_old_shifts"]["mod_fiber_holonomy"],
            "old_v2_integer_lift_sum": ctrl["v2_regression_old_shifts"]["integer_lift_sum"],
            "law_agreement_count": summary["agreement_count"],
            "law_sample_total": summary["sample_total"],
            "law_status": summary["law_test_status"],
            "betti_computed": False,
            "all_pass": all_pass,
        },
    }


def build_envelope_payload() -> dict[str, Any]:
    payload = build_fiber_augmented_cover_v2_1_object()
    return {
        **payload,
        "envelope_result_kind": "builder_envelope",
        "envelope_written_at": now_z(),
        "result_path": rel(RESULT_PATH),
        "envelope_result_path": rel(ENVELOPE_RESULT_PATH),
        "complex_chain_hashes": payload["complex_family"]["chain_hashes"],
        "complex_boundary_hashes": payload["complex_family"]["boundary_hashes"],
    }


def write_result() -> dict[str, Any]:
    payload = build_fiber_augmented_cover_v2_1_object()
    write_json(RESULT_PATH, payload)
    return payload


def write_envelope_result() -> dict[str, Any]:
    payload = build_envelope_payload()
    write_json(ENVELOPE_RESULT_PATH, payload)
    return payload
