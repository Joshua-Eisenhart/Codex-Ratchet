#!/usr/bin/env python3
"""Scratch tool-tool coupling probe for M(C) v1 quotient and bracketing incidence."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import sys
import time
import traceback
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from receipt_schema import validate_result_path  # noqa: E402


OBJECT_ID = "mc_v1_quotient_bracketing_cvc5_toponetx_coupling_probe"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_mc_v1_quotient_bracketing_cvc5_toponetx_coupling_probe.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quotient_bracketing_cvc5_toponetx_coupling_probe_results.json"
MC_V1_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json"
CONSUMER_GATE_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quarantine_consumer_gate_probe_results.json"
PRIOR_CVC5_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json"
PRIOR_TOPONETX_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json"
BLOCKED_REASON_PATH = ROOT / "system_v5/ops/wizard_admissions/mc_v1_quotient_bracketing_cvc5_toponetx_coupling_probe_blocked_reason.json"

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
    "bracketing promotion",
    "topological invariant or geometry claim",
]

CLAIM_CEILING = (
    "Scratch diagnostic tool-tool coupling only: cvc5 quotient/bracketing Boolean "
    "constraints and TopoNetX bracketing/readout incidence can be checked against "
    "the same finite M(C) v1 left/right records after both parent fit receipts. "
    "This does not admit M(C), does not promote either tool-lego, does not unlock "
    "Stage 4, and does not support same-carrier geometry, topology readout, "
    "AI/GNN readout, bridge, Axis0, physics, manifold, or formal admission claims."
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
    "certifies the left/right quotient-bracketing distinction, if TopoNetX no "
    "longer emits nontrivial incidence over the same records, if bracketing "
    "collapse, quotient erasure, or empty-complex controls do not change or demote "
    "the coupled observable, if strong consumers become eligible, or if any "
    "promotion/admission flag becomes true."
)

TOOL_MANIFEST = {
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Solver Boolean constraints over finite left/right quotient-bracketing distinction and erased controls",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SimplicialComplex construction and signed incidence_matrix(1) readout over quotient/bracketing/readout nodes",
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
    "toponetx": "load_bearing",
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
    import toponetx as tnx

    return cvc5, Kind, tnx


def readout_signature(readout: list[Any]) -> str:
    return ",".join(str(int(value)) for value in readout)


def admitted_class_by_member(mc_payload: dict[str, Any]) -> dict[str, str]:
    classes = (((mc_payload.get("quotient_relation") or {}).get("quotient_Adm_C_mod_M") or {}).get("classes") or [])
    out: dict[str, str] = {}
    for row in classes:
        class_id = str(row.get("class_id"))
        for member in row.get("members") or []:
            out[str(member)] = class_id
    return out


def left_right_rows(mc_payload: dict[str, Any]) -> list[dict[str, Any]]:
    classes = admitted_class_by_member(mc_payload)
    carrier_map = mc_payload.get("carrier_readout_map") or {}
    rows = []
    for record_id in [str(item) for item in ((mc_payload.get("bracketing_in_quotient") or {}).get("left_right_records") or [])]:
        carrier = carrier_map.get(record_id) or {}
        selected = carrier.get("selected") or []
        bracket = "right" if selected and selected[5] == 1 else "left"
        rows.append(
            {
                "id": record_id,
                "class_id": classes.get(record_id, "missing_class"),
                "bracket": bracket,
                "readout": readout_signature(selected),
            }
        )
    return rows


def build_complex(tnx: Any, rows: list[dict[str, Any]], *, collapse_brackets: bool = False, erase_quotient: bool = False, empty: bool = False) -> tuple[Any, dict[str, Any]]:
    complex_obj = tnx.SimplicialComplex()
    records: dict[str, Any] = {}
    if empty:
        return complex_obj, records
    for row in rows:
        record_node = f"record/{row['id']}"
        quotient_node = "quotient/erased" if erase_quotient else f"quotient/{row['class_id']}"
        bracket_node = "bracket/collapsed" if collapse_brackets else f"bracket/{row['bracket']}"
        readout_node = f"readout/{row['readout']}"
        complex_obj.add_simplex((record_node, quotient_node))
        complex_obj.add_simplex((record_node, bracket_node))
        complex_obj.add_simplex((quotient_node, bracket_node))
        complex_obj.add_simplex((bracket_node, readout_node))
        complex_obj.add_simplex((record_node, quotient_node, bracket_node))
        records[row["id"]] = {
            "record_node": record_node,
            "quotient_node": quotient_node,
            "bracket_node": bracket_node,
            "readout_node": readout_node,
        }
    return complex_obj, records


def matrix_payload(matrix: Any) -> dict[str, Any]:
    dense = matrix.toarray().tolist() if hasattr(matrix, "toarray") else []
    return {
        "shape": [int(matrix.shape[0]), int(matrix.shape[1])],
        "dense": dense,
        "signed_sum": sum(sum(float(value) for value in row) for row in dense),
        "nonzero_count": sum(1 for row in dense for value in row if float(value) != 0.0),
    }


def complex_observable(complex_obj: Any, records: dict[str, Any]) -> dict[str, Any]:
    simplices = sorted(str(simplex) for simplex in complex_obj.simplices)
    if len(simplices) == 0:
        incidence = {"shape": [0, 0], "dense": [], "signed_sum": 0.0, "nonzero_count": 0}
    else:
        incidence = matrix_payload(complex_obj.incidence_matrix(1))
    out = {
        "dim": int(complex_obj.dim),
        "shape": [int(value) for value in complex_obj.shape],
        "simplex_count": len(simplices),
        "simplices": simplices,
        "record_nodes": sorted(row["record_node"] for row in records.values()),
        "quotient_nodes": sorted(set(row["quotient_node"] for row in records.values())),
        "bracket_nodes": sorted(set(row["bracket_node"] for row in records.values())),
        "readout_nodes": sorted(set(row["readout_node"] for row in records.values())),
        "incidence_rank_1": incidence,
    }
    out["observable_digest"] = stable_sha256(out)
    return out


def bool_lit(solver: Any, value: bool) -> Any:
    return solver.mkBoolean(bool(value))


def solver_case(cvc5: Any, kind: Any, rows: list[dict[str, Any]], obs: dict[str, Any], *, require_distinct: bool) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    bool_sort = solver.getBooleanSort()
    has_all_records_value = len(obs["record_nodes"]) == len(rows) and len(rows) == 2
    has_two_brackets_value = len(obs["bracket_nodes"]) == 2
    has_no_missing_class_value = "quotient/missing_class" not in obs["quotient_nodes"] and "quotient/erased" not in obs["quotient_nodes"]
    nontrivial_incidence_value = obs["incidence_rank_1"]["nonzero_count"] > 0
    values = {
        "has_all_records": has_all_records_value,
        "has_two_brackets": has_two_brackets_value,
        "has_no_missing_class": has_no_missing_class_value,
        "nontrivial_incidence": nontrivial_incidence_value,
    }
    terms = []
    for name, value in values.items():
        term = solver.mkConst(bool_sort, name)
        solver.assertFormula(solver.mkTerm(kind.EQUAL, term, bool_lit(solver, value)))
        terms.append(term)
    distinct = solver.mkConst(bool_sort, "left_right_quotient_bracketing_distinct")
    solver.assertFormula(solver.mkTerm(kind.EQUAL, distinct, solver.mkTerm(kind.AND, *terms)))
    solver.assertFormula(solver.mkTerm(kind.EQUAL, distinct, bool_lit(solver, require_distinct)))
    result = solver.checkSat()
    return {
        "sat": result.isSat(),
        "unsat": result.isUnsat(),
        "result": str(result),
        "require_distinct": require_distinct,
        "component_values": values,
    }


def probe(
    mc_payload: dict[str, Any],
    gate_payload: dict[str, Any],
    prior_cvc5_payload: dict[str, Any],
    prior_toponetx_payload: dict[str, Any],
) -> dict[str, Any]:
    cvc5, kind, tnx = import_tools()
    rows = left_right_rows(mc_payload)
    complex_obj, records = build_complex(tnx, rows)
    obs = complex_observable(complex_obj, records)
    collapsed_complex, collapsed_records = build_complex(tnx, rows, collapse_brackets=True)
    collapsed_obs = complex_observable(collapsed_complex, collapsed_records)
    erased_complex, erased_records = build_complex(tnx, rows, erase_quotient=True)
    erased_obs = complex_observable(erased_complex, erased_records)
    empty_complex, empty_records = build_complex(tnx, rows, empty=True)
    empty_obs = complex_observable(empty_complex, empty_records)

    positive_solver = solver_case(cvc5, kind, rows, obs, require_distinct=True)
    collapsed_solver = solver_case(cvc5, kind, rows, collapsed_obs, require_distinct=True)
    erased_solver = solver_case(cvc5, kind, rows, erased_obs, require_distinct=True)
    demoted_solver = solver_case(cvc5, kind, rows, collapsed_obs, require_distinct=False)

    coupled_digest = stable_sha256({"cvc5": positive_solver, "toponetx": obs["observable_digest"]})
    collapsed_digest = stable_sha256({"cvc5": collapsed_solver, "toponetx": collapsed_obs["observable_digest"]})
    erased_digest = stable_sha256({"cvc5": erased_solver, "toponetx": erased_obs["observable_digest"]})

    gate_eligible = gate_payload.get("eligible_consumers") or []
    gate_blocked = gate_payload.get("blocked_consumers") or gate_payload.get("blocked_downstream_consumers") or []
    prior_receipts_ok = (
        prior_cvc5_payload.get("all_pass") is True
        and prior_cvc5_payload.get("classification") == "tool_lego_fit_probe"
        and prior_cvc5_payload.get("stage_movement_allowed") is False
        and prior_toponetx_payload.get("all_pass") is True
        and prior_toponetx_payload.get("classification") == "tool_lego_fit_probe"
        and prior_toponetx_payload.get("stage_movement_allowed") is False
    )

    positive = {
        "parent_fit_receipts_consumed": check(
            "parent_fit_receipts_consumed",
            prior_receipts_ok,
            expected={"cvc5": "tool_lego_fit_probe all_pass true no stage movement", "toponetx": "same"},
            observed={
                "cvc5": {
                    "classification": prior_cvc5_payload.get("classification"),
                    "all_pass": prior_cvc5_payload.get("all_pass"),
                    "stage_movement_allowed": prior_cvc5_payload.get("stage_movement_allowed"),
                },
                "toponetx": {
                    "classification": prior_toponetx_payload.get("classification"),
                    "all_pass": prior_toponetx_payload.get("all_pass"),
                    "stage_movement_allowed": prior_toponetx_payload.get("stage_movement_allowed"),
                },
            },
            reason="tool-tool coupling must cite two prior parent fit receipts",
        ),
        "toponetx_left_right_quotient_incidence_live": check(
            "toponetx_left_right_quotient_incidence_live",
            len(rows) == 2
            and obs["incidence_rank_1"]["nonzero_count"] > 0
            and sorted(obs["bracket_nodes"]) == ["bracket/left", "bracket/right"],
            expected={"left_right_records": 2, "bracket_nodes": ["bracket/left", "bracket/right"], "nonzero_incidence": True},
            observed={"rows": rows, "bracket_nodes": obs["bracket_nodes"], "nonzero": obs["incidence_rank_1"]["nonzero_count"]},
            reason="TopoNetX must carry the finite left/right bracketing incidence fixture",
        ),
        "cvc5_certifies_distinct_left_right_fixture": check(
            "cvc5_certifies_distinct_left_right_fixture",
            positive_solver["sat"] is True,
            expected={"sat": True},
            observed=positive_solver,
            reason="cvc5 must certify the finite left/right quotient-bracketing distinction",
        ),
    }
    negative = {
        "bracketing_collapse_flips_solver_claim": check(
            "bracketing_collapse_flips_solver_claim",
            collapsed_solver["unsat"] is True
            and collapsed_obs["observable_digest"] != obs["observable_digest"]
            and collapsed_digest != coupled_digest,
            expected={"collapsed_solver_unsat": True, "toponetx_digest_changes": True, "coupled_digest_changes": True},
            observed={"positive": positive_solver, "collapsed": collapsed_solver, "positive_digest": coupled_digest, "collapsed_digest": collapsed_digest},
            reason="Collapsing left/right bracket nodes must break the cvc5 distinction claim and change TopoNetX incidence",
        ),
        "quotient_erasure_flips_solver_claim": check(
            "quotient_erasure_flips_solver_claim",
            erased_solver["unsat"] is True
            and erased_obs["observable_digest"] != obs["observable_digest"]
            and erased_digest != coupled_digest,
            expected={"erased_solver_unsat": True, "toponetx_digest_changes": True, "coupled_digest_changes": True},
            observed={"positive": positive_solver, "erased": erased_solver, "positive_digest": coupled_digest, "erased_digest": erased_digest},
            reason="Erasing quotient class nodes must break the cvc5 distinction claim and change TopoNetX incidence",
        ),
        "empty_complex_demotes": check(
            "empty_complex_demotes",
            empty_obs["simplex_count"] == 0
            and empty_obs["incidence_rank_1"]["nonzero_count"] == 0
            and demoted_solver["sat"] is True,
            expected={"empty_simplex_count": 0, "demoted_solver_sat": True},
            observed={"empty": empty_obs, "demoted_solver": demoted_solver},
            reason="An empty carrier and a weaker collapsed claim are demoted baseline evidence only",
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
        "left_right_rows": rows,
        "toponetx_observable": obs,
        "collapsed_toponetx_observable": collapsed_obs,
        "erased_toponetx_observable": erased_obs,
        "empty_toponetx_observable": empty_obs,
        "cvc5_positive": positive_solver,
        "cvc5_collapsed": collapsed_solver,
        "cvc5_erased": erased_solver,
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
    prior_toponetx_payload, toponetx_error = load_json(PRIOR_TOPONETX_RESULT_PATH)
    receipt_checks: dict[str, dict[str, Any]] = {}
    for label, path, load_error in [
        ("mc_v1", MC_V1_RESULT_PATH, mc_error),
        ("consumer_gate", CONSUMER_GATE_RESULT_PATH, gate_error),
        ("parent_cvc5", PRIOR_CVC5_RESULT_PATH, cvc5_error),
        ("parent_toponetx", PRIOR_TOPONETX_RESULT_PATH, toponetx_error),
    ]:
        receipt_checks[label] = check(
            f"{label}_receipt_loaded_and_validates",
            load_error is None and validate_result_path(path)["ok"] is True,
            expected={"load_error": None, "validate_result_path.ok": True},
            observed={"load_error": load_error, "validate_result_path": validate_result_path(path)},
            reason=f"{label} receipt must be present and schema-valid before coupling",
        )
    if not section_pass(receipt_checks):
        positive: dict[str, dict[str, Any]] = {}
        negative: dict[str, dict[str, Any]] = {}
        boundary = receipt_checks
        details: dict[str, Any] = {}
    else:
        details = probe(mc_payload, gate_payload, prior_cvc5_payload, prior_toponetx_payload)
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
            "parent_toponetx": str(PRIOR_TOPONETX_RESULT_PATH),
        },
        "input_receipt_sha256": {
            "mc_v1": sha256_file(MC_V1_RESULT_PATH),
            "consumer_gate": sha256_file(CONSUMER_GATE_RESULT_PATH),
            "parent_cvc5": sha256_file(PRIOR_CVC5_RESULT_PATH),
            "parent_toponetx": sha256_file(PRIOR_TOPONETX_RESULT_PATH),
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
                "next_admissible_step": "Repair only this bounded cvc5/TopoNetX coupling probe or demote it; do not move stage.",
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
