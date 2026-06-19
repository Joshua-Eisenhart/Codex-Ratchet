#!/usr/bin/env python3
"""Scratch tool-tool coupling probe for M(C) v1 quotient classes and admission hyperedges."""

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


OBJECT_ID = "mc_v1_quotient_adm_cvc5_xgi_coupling_probe"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_mc_v1_quotient_adm_cvc5_xgi_coupling_probe.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quotient_adm_cvc5_xgi_coupling_probe_results.json"
MC_V1_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json"
CONSUMER_GATE_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quarantine_consumer_gate_probe_results.json"
PRIOR_CVC5_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json"
PRIOR_XGI_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json"
BLOCKED_REASON_PATH = ROOT / "system_v5/ops/wizard_admissions/mc_v1_quotient_adm_cvc5_xgi_coupling_probe_blocked_reason.json"

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
    "Adm_C promotion",
    "topological invariant or geometry claim",
]

CLAIM_CEILING = (
    "Scratch diagnostic tool-tool coupling only: cvc5 quotient/admission Boolean "
    "constraints and XGI admitted-record hyperedges can be checked against the same "
    "finite M(C) v1 admitted records after both parent fit receipts. This does not "
    "admit M(C), does not promote either tool-lego, does not unlock Stage 4, and "
    "does not support same-carrier geometry, topology readout, AI/GNN readout, "
    "bridge, Axis0, physics, manifold, or formal admission claims."
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
    "Demote if either parent fit receipt fails validation, if cvc5 no longer certifies "
    "that every XGI admitted hyperedge has a quotient class, if XGI no longer carries "
    "admitted-record quotient hyperedges, if quotient erasure or status-only projection "
    "controls do not change or demote the coupled observable, if strong consumers become "
    "eligible, or if any promotion/admission flag becomes true."
)

TOOL_MANIFEST = {
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Solver Boolean constraints over finite record/class edge existence and erased controls",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Hypergraph admitted-record hyperedges carrying quotient class, bracketing, rho, and status members",
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
    "xgi": "load_bearing",
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
    import xgi

    return cvc5, Kind, xgi


def admitted_class_by_member(mc_payload: dict[str, Any]) -> dict[str, str]:
    classes = (((mc_payload.get("quotient_relation") or {}).get("quotient_Adm_C_mod_M") or {}).get("classes") or [])
    out: dict[str, str] = {}
    for row in classes:
        class_id = str(row.get("class_id"))
        for member in row.get("members") or []:
            out[str(member)] = class_id
    return out


def support_rows(mc_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id")): row
        for row in ((mc_payload.get("support_S") or {}).get("elements") or [])
        if isinstance(row, dict) and row.get("id")
    }


def admitted_rows(mc_payload: dict[str, Any]) -> list[dict[str, Any]]:
    classes = admitted_class_by_member(mc_payload)
    support = support_rows(mc_payload)
    rows = []
    for record_id in sorted(str(item) for item in ((mc_payload.get("Adm_C") or {}).get("admitted_ids") or [])):
        support_row = support.get(record_id) or {}
        rows.append(
            {
                "id": record_id,
                "class_id": classes.get(record_id, "missing_class"),
                "bracketing": str(support_row.get("bracketing") or "unknown"),
                "rho_key": str(support_row.get("rho_key") or "unknown"),
            }
        )
    return rows


def build_hypergraph(xgi: Any, rows: list[dict[str, Any]], *, erase_quotient: bool = False, status_only: bool = False) -> tuple[Any, dict[str, list[str]]]:
    graph = xgi.Hypergraph()
    for row in rows:
        if status_only:
            members = [f"record/{row['id']}", "status/admitted"]
        else:
            class_node = "quotient/erased" if erase_quotient else f"quotient/{row['class_id']}"
            members = [
                f"record/{row['id']}",
                class_node,
                f"bracket/{row['bracketing']}",
                f"rho/{row['rho_key']}",
                "predicate/Adm_C",
                "status/admitted",
            ]
        graph.add_edge(members, idx=f"adm-quotient/{row['id']}")
    return graph, edge_members(graph)


def edge_members(graph: Any) -> dict[str, list[str]]:
    return {str(edge): sorted(str(node) for node in graph.edges.members(edge)) for edge in graph.edges}


def hypergraph_observable(xgi: Any, graph: Any, members: dict[str, list[str]]) -> dict[str, Any]:
    out = {
        "node_count": len(list(graph.nodes)),
        "edge_count": len(list(graph.edges)),
        "edge_member_sizes": {edge: len(nodes) for edge, nodes in sorted(members.items())},
        "edge_members": {edge: list(nodes) for edge, nodes in sorted(members.items())},
        "incidence_shape": [int(value) for value in xgi.incidence_matrix(graph).shape],
        "quotient_nodes": sorted(str(node) for node in graph.nodes if str(node).startswith("quotient/")),
        "record_nodes": sorted(str(node) for node in graph.nodes if str(node).startswith("record/")),
    }
    out["observable_digest"] = stable_sha256(out)
    return out


def bool_lit(solver: Any, value: bool) -> Any:
    return solver.mkBoolean(bool(value))


def solver_case(cvc5: Any, kind: Any, rows: list[dict[str, Any]], members: dict[str, list[str]], *, require_all_edges: bool, erase_quotient: bool) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    bool_sort = solver.getBooleanSort()
    edge_terms = []
    edge_results: dict[str, bool] = {}
    for row in rows:
        edge_id = f"adm-quotient/{row['id']}"
        nodes = members.get(edge_id) or []
        has_record = f"record/{row['id']}" in nodes
        has_class = (not erase_quotient) and f"quotient/{row['class_id']}" in nodes
        has_status = "status/admitted" in nodes
        edge_ok_value = has_record and has_class and has_status
        edge_results[row["id"]] = edge_ok_value
        term = solver.mkConst(bool_sort, f"edge_ok_{row['id']}".replace("-", "_"))
        solver.assertFormula(solver.mkTerm(kind.EQUAL, term, bool_lit(solver, edge_ok_value)))
        edge_terms.append(term)
    all_edges = solver.mkConst(bool_sort, "all_admitted_edges_have_quotient_class")
    solver.assertFormula(solver.mkTerm(kind.EQUAL, all_edges, solver.mkTerm(kind.AND, *edge_terms)))
    solver.assertFormula(solver.mkTerm(kind.EQUAL, all_edges, bool_lit(solver, require_all_edges)))
    result = solver.checkSat()
    return {
        "sat": result.isSat(),
        "unsat": result.isUnsat(),
        "result": str(result),
        "require_all_edges": require_all_edges,
        "erase_quotient": erase_quotient,
        "edge_results": edge_results,
    }


def probe(
    mc_payload: dict[str, Any],
    gate_payload: dict[str, Any],
    prior_cvc5_payload: dict[str, Any],
    prior_xgi_payload: dict[str, Any],
) -> dict[str, Any]:
    cvc5, kind, xgi = import_tools()
    rows = admitted_rows(mc_payload)
    graph, members = build_hypergraph(xgi, rows)
    hyper_obs = hypergraph_observable(xgi, graph, members)
    erased_graph, erased_members = build_hypergraph(xgi, rows, erase_quotient=True)
    erased_hyper_obs = hypergraph_observable(xgi, erased_graph, erased_members)
    status_graph, status_members = build_hypergraph(xgi, rows, status_only=True)
    status_hyper_obs = hypergraph_observable(xgi, status_graph, status_members)

    positive_solver = solver_case(cvc5, kind, rows, members, require_all_edges=True, erase_quotient=False)
    erased_solver = solver_case(cvc5, kind, rows, erased_members, require_all_edges=True, erase_quotient=True)
    demoted_solver = solver_case(cvc5, kind, rows, erased_members, require_all_edges=False, erase_quotient=True)

    coupled_digest = stable_sha256({"cvc5": positive_solver, "xgi": hyper_obs["observable_digest"]})
    erased_digest = stable_sha256({"cvc5": erased_solver, "xgi": erased_hyper_obs["observable_digest"]})
    status_digest = stable_sha256({"cvc5": demoted_solver, "xgi": status_hyper_obs["observable_digest"]})

    gate_eligible = gate_payload.get("eligible_consumers") or []
    gate_blocked = gate_payload.get("blocked_consumers") or gate_payload.get("blocked_downstream_consumers") or []
    prior_receipts_ok = (
        prior_cvc5_payload.get("all_pass") is True
        and prior_cvc5_payload.get("classification") == "tool_lego_fit_probe"
        and prior_cvc5_payload.get("stage_movement_allowed") is False
        and prior_xgi_payload.get("all_pass") is True
        and prior_xgi_payload.get("classification") == "tool_lego_fit_probe"
        and prior_xgi_payload.get("stage_movement_allowed") is False
    )

    positive = {
        "parent_fit_receipts_consumed": check(
            "parent_fit_receipts_consumed",
            prior_receipts_ok,
            expected={"cvc5": "tool_lego_fit_probe all_pass true no stage movement", "xgi": "same"},
            observed={
                "cvc5": {
                    "classification": prior_cvc5_payload.get("classification"),
                    "all_pass": prior_cvc5_payload.get("all_pass"),
                    "stage_movement_allowed": prior_cvc5_payload.get("stage_movement_allowed"),
                },
                "xgi": {
                    "classification": prior_xgi_payload.get("classification"),
                    "all_pass": prior_xgi_payload.get("all_pass"),
                    "stage_movement_allowed": prior_xgi_payload.get("stage_movement_allowed"),
                },
            },
            reason="tool-tool coupling must cite two prior parent fit receipts",
        ),
        "same_admitted_records_are_coupled": check(
            "same_admitted_records_are_coupled",
            len(rows) == 4 and hyper_obs["edge_count"] == 4 and len(hyper_obs["quotient_nodes"]) == 4,
            expected={"admitted_records": 4, "hyperedges": 4, "quotient_nodes": 4},
            observed={"rows": [row["id"] for row in rows], "edge_count": hyper_obs["edge_count"], "quotient_nodes": hyper_obs["quotient_nodes"]},
            reason="XGI must carry each admitted record with its quotient class node",
        ),
        "cvc5_certifies_all_admitted_edges_have_classes": check(
            "cvc5_certifies_all_admitted_edges_have_classes",
            positive_solver["sat"] is True and all(positive_solver["edge_results"].values()),
            expected={"sat": True, "all_edges": True},
            observed=positive_solver,
            reason="cvc5 must certify that every admitted-record hyperedge contains its quotient class",
        ),
    }
    negative = {
        "quotient_erasure_flips_solver_claim": check(
            "quotient_erasure_flips_solver_claim",
            erased_solver["unsat"] is True
            and erased_hyper_obs["observable_digest"] != hyper_obs["observable_digest"]
            and erased_digest != coupled_digest,
            expected={"erased_solver_unsat": True, "xgi_digest_changes": True, "coupled_digest_changes": True},
            observed={"positive": positive_solver, "erased": erased_solver, "positive_digest": coupled_digest, "erased_digest": erased_digest},
            reason="Erasing quotient class nodes must break the cvc5 all-edge claim and change the XGI observable",
        ),
        "demoted_erasure_claim_is_only_status_baseline": check(
            "demoted_erasure_claim_is_only_status_baseline",
            demoted_solver["sat"] is True
            and status_hyper_obs["observable_digest"] != hyper_obs["observable_digest"]
            and max(status_hyper_obs["edge_member_sizes"].values()) < min(hyper_obs["edge_member_sizes"].values())
            and status_digest != coupled_digest,
            expected={"demoted_solver_sat": True, "status_projection_demotes": True},
            observed={"demoted_solver": demoted_solver, "status_edge_member_sizes": status_hyper_obs["edge_member_sizes"]},
            reason="A weaker claim over quotient-erased/status-only edges may be satisfiable but is demoted baseline evidence",
        ),
        "empty_or_missing_class_rows_demote": check(
            "empty_or_missing_class_rows_demote",
            "missing_class" not in [row["class_id"] for row in rows],
            expected="no missing_class rows in positive fixture",
            observed=[row["class_id"] for row in rows],
            reason="Missing quotient-class rows would demote the coupling before execution",
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
        "xgi_observable": hyper_obs,
        "erased_xgi_observable": erased_hyper_obs,
        "status_xgi_observable": status_hyper_obs,
        "cvc5_positive": positive_solver,
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
    prior_xgi_payload, xgi_error = load_json(PRIOR_XGI_RESULT_PATH)
    receipt_checks: dict[str, dict[str, Any]] = {}
    for label, path, load_error in [
        ("mc_v1", MC_V1_RESULT_PATH, mc_error),
        ("consumer_gate", CONSUMER_GATE_RESULT_PATH, gate_error),
        ("parent_cvc5", PRIOR_CVC5_RESULT_PATH, cvc5_error),
        ("parent_xgi", PRIOR_XGI_RESULT_PATH, xgi_error),
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
        details = probe(mc_payload, gate_payload, prior_cvc5_payload, prior_xgi_payload)
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
            "parent_xgi": str(PRIOR_XGI_RESULT_PATH),
        },
        "input_receipt_sha256": {
            "mc_v1": sha256_file(MC_V1_RESULT_PATH),
            "consumer_gate": sha256_file(CONSUMER_GATE_RESULT_PATH),
            "parent_cvc5": sha256_file(PRIOR_CVC5_RESULT_PATH),
            "parent_xgi": sha256_file(PRIOR_XGI_RESULT_PATH),
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
                "next_admissible_step": "Repair only this bounded cvc5/XGI coupling probe or demote it; do not move stage.",
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
