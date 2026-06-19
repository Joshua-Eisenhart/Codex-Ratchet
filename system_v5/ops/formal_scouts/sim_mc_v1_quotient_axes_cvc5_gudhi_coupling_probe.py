#!/usr/bin/env python3
"""Scratch tool-tool coupling probe for M(C) v1 quotient classes and axes filtration."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import pathlib
import sys
import time
import traceback
from itertools import combinations
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from receipt_schema import validate_result_path  # noqa: E402


OBJECT_ID = "mc_v1_quotient_axes_cvc5_gudhi_coupling_probe"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_mc_v1_quotient_axes_cvc5_gudhi_coupling_probe.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quotient_axes_cvc5_gudhi_coupling_probe_results.json"
MC_V1_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json"
CONSUMER_GATE_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quarantine_consumer_gate_probe_results.json"
PRIOR_CVC5_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json"
PRIOR_GUDHI_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_axes_gudhi_tool_lego_fit_probe_results.json"
BLOCKED_REASON_PATH = ROOT / "system_v5/ops/wizard_admissions/mc_v1_quotient_axes_cvc5_gudhi_coupling_probe_blocked_reason.json"

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
sim_execution_kind = "classical"
SIM_EXECUTION_KIND = sim_execution_kind
evidence_level = "tool_tool_coupling_probe"
EVIDENCE_LEVEL = evidence_level

STRONG_CONSUMERS = [
    "M(C)_system_fit",
    "same_carrier_geometry",
    "topology_readout_promotion",
    "AI_GNN_readout_promotion",
    "bridge",
    "Axis0",
    "physics",
    "manifold_admission",
]
ELIGIBLE_CONSUMERS = [
    "quarantined_scratch_fuel",
    "exact_tool_tool_coupling_probe_after_parent_fit_receipts",
]
OUT_OF_SCOPE = STRONG_CONSUMERS + [
    "Stage 4 movement",
    "M(C) formal admission",
    "quotient_relation promotion",
    "axes_A_i promotion",
    "topological invariant or geometry claim",
]

CLAIM_CEILING = (
    "Scratch diagnostic tool-tool coupling only: cvc5 Boolean constraints over "
    "quotient-class and axes-field presence are coupled to a GUDHI finite "
    "axes filtration over the same admitted M(C) v1 records after both parent "
    "fit receipts. This does not admit M(C), does not promote either tool-lego, "
    "does not unlock Stage 4, and does not support same-carrier geometry, "
    "topology readout, AI/GNN readout, bridge, Axis0, physics, manifold, or "
    "formal admission claims."
)
NEXT_LEGO_TARGET = (
    "A later packet may couple another pair of already-receipted tool/API surfaces; "
    "this receipt itself is scratch coupling evidence and cannot move the ladder stage."
)
PROMOTION_CONDITION = (
    "No direct promotion path. Stronger use requires a separate admission packet "
    "with exact M(C) fields, parent receipts, coupled controls, stage gate, and "
    "consumer-specific claim ceiling."
)
BLOCKED_UNTIL = (
    "Stage movement remains blocked until a future admission packet, not this "
    "coupling probe, passes M(C), solver/control, composition/bracketing, "
    "carrier/readout, and stage gates."
)
DEMOTION_CONDITION = (
    "Demote if either parent fit receipt fails validation, if cvc5 no longer "
    "certifies the all-record quotient-plus-axes claim, if GUDHI no longer emits "
    "a nontrivial filtration over the same admitted records, if quotient erasure, "
    "axis erasure, or degenerate-filtration controls do not change or demote the "
    "coupled observable, if strong consumers become eligible, or if any promotion/"
    "admission flag becomes true."
)

TOOL_MANIFEST = {
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Solver Boolean constraints over finite quotient-class and axes-field presence with erased controls",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SimplexTree insertion, filtration ordering, and compute_persistence readout over finite admitted axes records",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON parsing/writing, repo-local paths, sha256 pinning, elapsed-time measurement, and blocked-reason error capture",
    },
    "receipt_schema": {
        "tried": True,
        "used": True,
        "reason": "supportive validation of parent fit receipts and M(C) v1 envelope",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "cvc5": "load_bearing",
    "gudhi": "load_bearing",
    "python_stdlib": "supportive",
    "receipt_schema": "supportive",
}


def sha256_file(path: pathlib.Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: pathlib.Path) -> tuple[dict[str, Any], str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"{exc.__class__.__name__}: {exc}"
    if not isinstance(payload, dict):
        return {}, f"non-object JSON payload: {type(payload).__name__}"
    return payload, None


def check(name: str, passed: bool, *, expected: Any, observed: Any, reason: str) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "expected": expected, "observed": observed, "reason": reason}


def section_pass(section: dict[str, dict[str, Any]]) -> bool:
    return all(row["pass"] is True for row in section.values())


def import_tools() -> tuple[Any, Any, Any]:
    import cvc5
    from cvc5 import Kind
    import gudhi

    return cvc5, Kind, gudhi


def finite_value(value: float) -> str | float:
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return round(float(value), 12)


def admitted_class_by_member(mc_payload: dict[str, Any]) -> dict[str, str]:
    classes = (((mc_payload.get("quotient_relation") or {}).get("quotient_Adm_C_mod_M") or {}).get("classes") or [])
    out: dict[str, str] = {}
    for row in classes:
        class_id = str(row.get("class_id"))
        for member in row.get("members") or []:
            out[str(member)] = class_id
    return out


def admitted_rows(mc_payload: dict[str, Any]) -> list[dict[str, Any]]:
    axes = mc_payload.get("axes_A_i") or {}
    entropy = axes.get("A_entropy_bits") or {}
    order_gap = axes.get("A_order_gap") or {}
    associator = axes.get("A_associator_norm") or {}
    classes = admitted_class_by_member(mc_payload)
    admitted_ids = sorted(str(item) for item in ((mc_payload.get("Adm_C") or {}).get("admitted_ids") or []))
    rows = []
    for record_id in admitted_ids:
        rows.append(
            {
                "id": record_id,
                "class_id": classes.get(record_id, "missing_class"),
                "has_class": record_id in classes,
                "has_entropy": record_id in entropy,
                "has_order_gap": record_id in order_gap,
                "has_associator": record_id in associator,
                "entropy": float(entropy.get(record_id, 0.0)),
                "order_gap": float(order_gap.get(record_id, 0.0)),
                "associator": float(associator.get(record_id, 0.0)),
            }
        )
    return rows


def build_filtration(gudhi: Any, rows: list[dict[str, Any]], *, mode: str = "positive") -> tuple[Any, dict[int, str]]:
    id_by_vertex = {index: row["id"] for index, row in enumerate(rows)}
    stree = gudhi.SimplexTree()
    for index, row in enumerate(rows):
        if mode == "axis_erased":
            base = 0.0
        elif mode == "axis_scramble":
            base = rows[-(index + 1)]["entropy"]
        else:
            base = row["entropy"]
        stree.insert([index], filtration=base)
    if mode != "degenerate":
        for left, right in combinations(range(len(rows)), 2):
            left_row = rows[left]
            right_row = rows[right]
            edge_time = max(left_row["entropy"], right_row["entropy"]) + max(left_row["order_gap"], right_row["order_gap"])
            if mode == "axis_erased":
                edge_time = 0.0
            elif mode == "axis_scramble":
                edge_time = 1.0 - min(edge_time, 1.0)
            stree.insert([left, right], filtration=edge_time)
        if len(rows) >= 3:
            tri_time = max(row["associator"] for row in rows[:3])
            if mode == "axis_erased":
                tri_time = 0.0
            stree.insert([0, 1, 2], filtration=tri_time)
    stree.compute_persistence()
    return stree, id_by_vertex


def filtration_payload(stree: Any, id_by_vertex: dict[int, str]) -> list[dict[str, Any]]:
    rows = []
    for simplex, value in stree.get_filtration():
        rows.append(
            {
                "simplex": [id_by_vertex.get(int(vertex), str(vertex)) for vertex in simplex],
                "vertex_ids": [int(vertex) for vertex in simplex],
                "filtration": finite_value(value),
            }
        )
    return rows


def persistence_payload(stree: Any) -> list[dict[str, Any]]:
    return [
        {"dim": int(dim), "birth": finite_value(pair[0]), "death": finite_value(pair[1])}
        for dim, pair in stree.persistence()
    ]


def filtration_observable(stree: Any, id_by_vertex: dict[int, str]) -> dict[str, Any]:
    out = {
        "record_ids": [id_by_vertex[index] for index in sorted(id_by_vertex)],
        "num_vertices": len(id_by_vertex),
        "num_simplices": int(stree.num_simplices()),
        "filtration": filtration_payload(stree, id_by_vertex),
        "persistence": persistence_payload(stree),
        "betti_numbers": [int(value) for value in stree.betti_numbers()],
    }
    out["observable_digest"] = stable_sha256(out)
    return out


def bool_lit(solver: Any, value: bool) -> Any:
    return solver.mkBoolean(bool(value))


def solver_case(
    cvc5: Any,
    kind: Any,
    rows: list[dict[str, Any]],
    obs: dict[str, Any],
    *,
    erase_quotient: bool = False,
    erase_axes: bool = False,
    require_all: bool,
) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    bool_sort = solver.getBooleanSort()
    values: dict[str, bool] = {
        "same_record_count": obs["num_vertices"] == len(rows) and len(rows) == 4,
        "nontrivial_filtration": obs["num_simplices"] > obs["num_vertices"],
    }
    for row in rows:
        safe_id = row["id"].replace("/", "_")
        values[f"{safe_id}_has_class"] = False if erase_quotient else bool(row["has_class"])
        values[f"{safe_id}_has_axes"] = False if erase_axes else bool(row["has_entropy"] and row["has_order_gap"] and row["has_associator"])
    terms = []
    for name, value in values.items():
        term = solver.mkConst(bool_sort, name)
        solver.assertFormula(solver.mkTerm(kind.EQUAL, term, bool_lit(solver, value)))
        terms.append(term)
    all_claim = solver.mkConst(bool_sort, "all_records_have_quotient_class_and_axes")
    solver.assertFormula(solver.mkTerm(kind.EQUAL, all_claim, solver.mkTerm(kind.AND, *terms)))
    solver.assertFormula(solver.mkTerm(kind.EQUAL, all_claim, bool_lit(solver, require_all)))
    result = solver.checkSat()
    return {
        "sat": result.isSat(),
        "unsat": result.isUnsat(),
        "result": str(result),
        "require_all": require_all,
        "erase_quotient": erase_quotient,
        "erase_axes": erase_axes,
        "component_values": values,
    }


def probe(
    mc_payload: dict[str, Any],
    gate_payload: dict[str, Any],
    prior_cvc5_payload: dict[str, Any],
    prior_gudhi_payload: dict[str, Any],
) -> dict[str, Any]:
    cvc5, kind, gudhi = import_tools()
    rows = admitted_rows(mc_payload)
    positive_tree, id_by_vertex = build_filtration(gudhi, rows)
    positive_obs = filtration_observable(positive_tree, id_by_vertex)
    erased_tree, erased_id_map = build_filtration(gudhi, rows, mode="axis_erased")
    erased_obs = filtration_observable(erased_tree, erased_id_map)
    scramble_tree, scramble_id_map = build_filtration(gudhi, rows, mode="axis_scramble")
    scramble_obs = filtration_observable(scramble_tree, scramble_id_map)
    degenerate_tree, degenerate_id_map = build_filtration(gudhi, rows, mode="degenerate")
    degenerate_obs = filtration_observable(degenerate_tree, degenerate_id_map)

    positive_solver = solver_case(cvc5, kind, rows, positive_obs, require_all=True)
    quotient_erased_solver = solver_case(cvc5, kind, rows, positive_obs, erase_quotient=True, require_all=True)
    axis_erased_solver = solver_case(cvc5, kind, rows, erased_obs, erase_axes=True, require_all=True)
    demoted_solver = solver_case(cvc5, kind, rows, degenerate_obs, require_all=False)

    coupled_digest = stable_sha256({"cvc5": positive_solver, "gudhi": positive_obs["observable_digest"]})
    quotient_erased_digest = stable_sha256({"cvc5": quotient_erased_solver, "gudhi": positive_obs["observable_digest"]})
    axis_erased_digest = stable_sha256({"cvc5": axis_erased_solver, "gudhi": erased_obs["observable_digest"]})
    scramble_digest = stable_sha256({"cvc5": positive_solver, "gudhi": scramble_obs["observable_digest"]})

    gate_eligible = gate_payload.get("eligible_consumers") or []
    gate_blocked = gate_payload.get("blocked_consumers") or gate_payload.get("blocked_downstream_consumers") or []
    prior_receipts_ok = (
        prior_cvc5_payload.get("all_pass") is True
        and prior_cvc5_payload.get("classification") == "tool_lego_fit_probe"
        and prior_cvc5_payload.get("stage_movement_allowed") is False
        and prior_gudhi_payload.get("all_pass") is True
        and prior_gudhi_payload.get("classification") == "tool_lego_fit_probe"
        and prior_gudhi_payload.get("stage_movement_allowed") is False
    )

    positive = {
        "parent_fit_receipts_consumed": check(
            "parent_fit_receipts_consumed",
            prior_receipts_ok,
            expected={"cvc5": "tool_lego_fit_probe all_pass true no stage movement", "gudhi": "same"},
            observed={
                "cvc5": {
                    "classification": prior_cvc5_payload.get("classification"),
                    "all_pass": prior_cvc5_payload.get("all_pass"),
                    "stage_movement_allowed": prior_cvc5_payload.get("stage_movement_allowed"),
                },
                "gudhi": {
                    "classification": prior_gudhi_payload.get("classification"),
                    "all_pass": prior_gudhi_payload.get("all_pass"),
                    "stage_movement_allowed": prior_gudhi_payload.get("stage_movement_allowed"),
                },
            },
            reason="tool-tool coupling must cite two prior parent fit receipts",
        ),
        "same_admitted_records_coupled": check(
            "same_admitted_records_coupled",
            len(rows) == 4
            and positive_obs["record_ids"] == [row["id"] for row in rows]
            and all(row["has_class"] and row["has_entropy"] and row["has_order_gap"] and row["has_associator"] for row in rows),
            expected={"record_count": 4, "all_records_have_class_and_axes": True},
            observed={"rows": rows, "filtration_record_ids": positive_obs["record_ids"]},
            reason="cvc5 and GUDHI must operate on the same admitted M(C) v1 records",
        ),
        "cvc5_and_gudhi_positive_claim_live": check(
            "cvc5_and_gudhi_positive_claim_live",
            positive_solver["sat"] is True and positive_obs["num_simplices"] > positive_obs["num_vertices"],
            expected={"solver_sat": True, "nontrivial_filtration": True},
            observed={"solver": positive_solver, "num_vertices": positive_obs["num_vertices"], "num_simplices": positive_obs["num_simplices"]},
            reason="cvc5 must certify all-record quotient-plus-axes presence while GUDHI emits a nontrivial finite filtration",
        ),
    }
    negative = {
        "quotient_erasure_flips_solver_claim": check(
            "quotient_erasure_flips_solver_claim",
            quotient_erased_solver["unsat"] is True and quotient_erased_digest != coupled_digest,
            expected={"quotient_erased_solver_unsat": True, "coupled_digest_changes": True},
            observed={"positive": positive_solver, "quotient_erased": quotient_erased_solver, "positive_digest": coupled_digest, "erased_digest": quotient_erased_digest},
            reason="Erasing quotient class membership must break the strict all-record cvc5 claim",
        ),
        "axis_erasure_flips_solver_and_filtration": check(
            "axis_erasure_flips_solver_and_filtration",
            axis_erased_solver["unsat"] is True
            and erased_obs["observable_digest"] != positive_obs["observable_digest"]
            and axis_erased_digest != coupled_digest,
            expected={"axis_erased_solver_unsat": True, "filtration_digest_changes": True, "coupled_digest_changes": True},
            observed={"positive": positive_solver, "axis_erased": axis_erased_solver, "positive_digest": coupled_digest, "axis_erased_digest": axis_erased_digest},
            reason="Erasing axes structure must break the strict cvc5 claim and change the GUDHI observable",
        ),
        "degenerate_filtration_demotes": check(
            "degenerate_filtration_demotes",
            degenerate_obs["num_simplices"] == degenerate_obs["num_vertices"]
            and demoted_solver["sat"] is True
            and scramble_digest != coupled_digest,
            expected={"degenerate_has_vertices_only": True, "weaker_solver_sat": True, "scramble_digest_changes": True},
            observed={"degenerate": degenerate_obs, "demoted_solver": demoted_solver, "scramble_digest": scramble_digest, "positive_digest": coupled_digest},
            reason="A vertices-only filtration or scrambled axes readout is demoted baseline evidence only",
        ),
    }
    boundary = {
        "consumer_gate_allows_only_narrow_use": check(
            "consumer_gate_allows_only_narrow_use",
            gate_payload.get("all_pass") is True
            and "quarantined_scratch_fuel" in gate_eligible
            and all(consumer in gate_blocked for consumer in STRONG_CONSUMERS),
            expected={"gate_all_pass": True, "strong_consumers_blocked": STRONG_CONSUMERS},
            observed={"gate_all_pass": gate_payload.get("all_pass"), "eligible": gate_eligible, "blocked": gate_blocked},
            reason="coupling probe may run only after the narrow consumer gate remains active",
        ),
        "classification_and_flags_block_promotion": check(
            "classification_and_flags_block_promotion",
            classification == "scratch_diagnostic"
            and promotion_allowed is False
            and formal_admission_allowed is False,
            expected={"classification": "scratch_diagnostic", "promotion_allowed": False, "formal_admission_allowed": False},
            observed={"classification": classification, "promotion_allowed": promotion_allowed, "formal_admission_allowed": formal_admission_allowed},
            reason="tool-tool coupling must remain scratch and non-promoting",
        ),
        "stage_movement_forbidden": check(
            "stage_movement_forbidden",
            True,
            expected={"stage_movement_allowed": False, "stage4_unlock_allowed": False},
            observed={"stage_movement_allowed": False, "stage4_unlock_allowed": False},
            reason="this scratch coupling cannot move ladder stage",
        ),
    }
    return {
        "admitted_rows": rows,
        "gudhi_observable": positive_obs,
        "axis_erased_gudhi_observable": erased_obs,
        "axis_scramble_gudhi_observable": scramble_obs,
        "degenerate_gudhi_observable": degenerate_obs,
        "cvc5_positive": positive_solver,
        "cvc5_quotient_erased": quotient_erased_solver,
        "cvc5_axis_erased": axis_erased_solver,
        "cvc5_demoted": demoted_solver,
        "coupled_digest": coupled_digest,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }


def build_result() -> dict[str, Any]:
    started = time.perf_counter()
    mc_payload, mc_error = load_json(MC_V1_RESULT_PATH)
    gate_payload, gate_error = load_json(CONSUMER_GATE_RESULT_PATH)
    prior_cvc5_payload, cvc5_error = load_json(PRIOR_CVC5_RESULT_PATH)
    prior_gudhi_payload, gudhi_error = load_json(PRIOR_GUDHI_RESULT_PATH)
    receipt_checks: dict[str, dict[str, Any]] = {}
    for label, path, load_error in [
        ("mc_v1", MC_V1_RESULT_PATH, mc_error),
        ("consumer_gate", CONSUMER_GATE_RESULT_PATH, gate_error),
        ("parent_cvc5", PRIOR_CVC5_RESULT_PATH, cvc5_error),
        ("parent_gudhi", PRIOR_GUDHI_RESULT_PATH, gudhi_error),
    ]:
        validation = validate_result_path(path)
        receipt_checks[label] = check(
            f"{label}_receipt_loaded_and_validates",
            load_error is None and validation["ok"] is True,
            expected={"load_error": None, "validate_result_path.ok": True},
            observed={"load_error": load_error, "validate_result_path": validation},
            reason=f"{label} receipt must be present and schema-valid before coupling",
        )
    if not section_pass(receipt_checks):
        positive: dict[str, dict[str, Any]] = {}
        negative: dict[str, dict[str, Any]] = {}
        boundary = receipt_checks
        details: dict[str, Any] = {}
    else:
        details = probe(mc_payload, gate_payload, prior_cvc5_payload, prior_gudhi_payload)
        positive = details["positive"]
        negative = details["negative"]
        boundary = {**details["boundary"], **receipt_checks}
    all_pass = section_pass(positive) and section_pass(negative) and section_pass(boundary)
    return {
        "schema_version": "codex_ratchet.tool_tool_coupling_probe.v1",
        "name": OBJECT_ID,
        "object_id": OBJECT_ID,
        "classification": classification,
        "evidence_level": evidence_level,
        "sim_execution_kind": sim_execution_kind,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "input_receipts": {
            "mc_v1": str(MC_V1_RESULT_PATH),
            "consumer_gate": str(CONSUMER_GATE_RESULT_PATH),
            "parent_cvc5": str(PRIOR_CVC5_RESULT_PATH),
            "parent_gudhi": str(PRIOR_GUDHI_RESULT_PATH),
        },
        "input_receipt_sha256": {
            "mc_v1": sha256_file(MC_V1_RESULT_PATH),
            "consumer_gate": sha256_file(CONSUMER_GATE_RESULT_PATH),
            "parent_cvc5": sha256_file(PRIOR_CVC5_RESULT_PATH),
            "parent_gudhi": sha256_file(PRIOR_GUDHI_RESULT_PATH),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "details": {key: value for key, value in details.items() if key not in {"positive", "negative", "boundary"}},
        "all_pass": all_pass,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "stage_movement_allowed": False,
        "stage4_unlock_allowed": False,
        "eligible_consumers": ELIGIBLE_CONSUMERS,
        "blocked_consumers": STRONG_CONSUMERS,
        "blocked_downstream_consumers": STRONG_CONSUMERS,
        "out_of_scope": OUT_OF_SCOPE,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": NEXT_LEGO_TARGET,
        "promotion_condition": PROMOTION_CONDITION,
        "blocked_until": BLOCKED_UNTIL,
        "demotion_condition": DEMOTION_CONDITION,
    }


def write_blocked_reason(exc: BaseException) -> None:
    BLOCKED_REASON_PATH.parent.mkdir(parents=True, exist_ok=True)
    BLOCKED_REASON_PATH.write_text(
        json.dumps(
            {
                "kind": "blocked_reason",
                "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "scope": OBJECT_ID,
                "reason": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
                "next_admissible_step": "Repair only this bounded cvc5/GUDHI coupling probe or demote it; do not move stage.",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    try:
        result = build_result()
    except Exception as exc:
        write_blocked_reason(exc)
        raise
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"positive={sum(1 for row in result['positive'].values() if row['pass'])}/{len(result['positive'])} "
        f"negative={sum(1 for row in result['negative'].values() if row['pass'])}/{len(result['negative'])} "
        f"boundary={sum(1 for row in result['boundary'].values() if row['pass'])}/{len(result['boundary'])} "
        f"classification={result['classification']} "
        f"stage_movement_allowed={str(result['stage_movement_allowed']).lower()}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
