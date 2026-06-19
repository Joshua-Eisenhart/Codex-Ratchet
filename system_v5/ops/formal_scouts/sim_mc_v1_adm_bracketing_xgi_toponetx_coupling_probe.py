#!/usr/bin/env python3
"""Scratch tool-tool coupling probe for M(C) v1 Adm_C and bracketing incidence."""

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


OBJECT_ID = "mc_v1_adm_bracketing_xgi_toponetx_coupling_probe"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_mc_v1_adm_bracketing_xgi_toponetx_coupling_probe.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_adm_bracketing_xgi_toponetx_coupling_probe_results.json"
MC_V1_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json"
CONSUMER_GATE_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quarantine_consumer_gate_probe_results.json"
PRIOR_XGI_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json"
PRIOR_TOPONETX_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json"
BLOCKED_REASON_PATH = ROOT / "system_v5/ops/wizard_admissions/mc_v1_adm_bracketing_xgi_toponetx_coupling_probe_blocked_reason.json"

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
    "Adm_C promotion",
    "bracketing promotion",
    "topological invariant or geometry claim",
]

CLAIM_CEILING = (
    "Scratch diagnostic tool-tool coupling only: XGI admissibility/constraint "
    "hyperedges can be converted into a TopoNetX finite signed-incidence fixture "
    "for the bracketing/readout records after both parent fit receipts. This does "
    "not admit M(C), does not promote either tool-lego, does not unlock Stage 4, "
    "and does not support same-carrier geometry, topology readout, AI/GNN readout, "
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
    "Demote if either parent fit receipt fails validation, if XGI no longer carries "
    "the finite admitted-record hyperedges, if TopoNetX no longer emits a nontrivial "
    "signed incidence matrix from those hyperedges, if projection/collapse/empty "
    "controls do not change the coupled observable, if strong consumers become "
    "eligible, or if any promotion/admission flag becomes true."
)

TOOL_MANIFEST = {
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Hypergraph admitted-record hyperedges and edge member views feeding the coupled incidence fixture",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SimplicialComplex conversion and signed incidence_matrix(1) readout over the XGI hyperedge members",
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
    "xgi": "load_bearing",
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
    return {
        "name": name,
        "pass": bool(passed),
        "expected": expected,
        "observed": observed,
        "reason": reason,
    }


def section_pass(section: dict[str, dict[str, Any]]) -> bool:
    return all(row["pass"] is True for row in section.values())


def import_tools() -> tuple[Any, Any]:
    import toponetx as tnx
    import xgi

    return xgi, tnx


def admitted_record_rows(mc_payload: dict[str, Any]) -> list[dict[str, Any]]:
    support_by_id = {
        str(row.get("id")): row
        for row in ((mc_payload.get("support_S") or {}).get("elements") or [])
        if isinstance(row, dict) and row.get("id")
    }
    rows = []
    for record_id in sorted(str(item) for item in ((mc_payload.get("Adm_C") or {}).get("admitted_ids") or [])):
        support = support_by_id.get(record_id) or {}
        carrier = ((mc_payload.get("carrier_readout_map") or {}).get(record_id) or {})
        rows.append(
            {
                "id": record_id,
                "bracketing": str(support.get("bracketing") or "unknown"),
                "readout": list(carrier.get("selected") or []),
                "rho_key": str(support.get("rho_key") or "unknown"),
            }
        )
    return rows


def readout_signature(readout: list[Any]) -> str:
    return ",".join(str(int(value)) for value in readout)


def build_xgi_admitted_hypergraph(xgi: Any, rows: list[dict[str, Any]], *, collapse_bracketing: bool = False) -> tuple[Any, dict[str, list[str]]]:
    graph = xgi.Hypergraph()
    for row in rows:
        bracket = "collapsed" if collapse_bracketing else row["bracketing"]
        members = [
            f"record/{row['id']}",
            f"bracket/{bracket}",
            f"readout/{readout_signature(row['readout'])}",
            f"rho/{row['rho_key']}",
            "status/admitted",
        ]
        graph.add_edge(members, idx=f"adm/{row['id']}")
    return graph, edge_members(graph)


def edge_members(graph: Any) -> dict[str, list[str]]:
    return {str(edge): sorted(str(node) for node in graph.edges.members(edge)) for edge in graph.edges}


def xgi_observable(xgi: Any, graph: Any, members: dict[str, list[str]]) -> dict[str, Any]:
    incidence_shape = [int(value) for value in xgi.incidence_matrix(graph).shape]
    out = {
        "node_count": len(list(graph.nodes)),
        "edge_count": len(list(graph.edges)),
        "edge_member_sizes": {key: len(value) for key, value in sorted(members.items())},
        "edge_members": {key: list(value) for key, value in sorted(members.items())},
        "incidence_shape": incidence_shape,
        "bracket_nodes": sorted(str(node) for node in graph.nodes if str(node).startswith("bracket/")),
        "readout_nodes": sorted(str(node) for node in graph.nodes if str(node).startswith("readout/")),
    }
    out["observable_digest"] = stable_sha256(out)
    return out


def matrix_payload(matrix: Any) -> dict[str, Any]:
    dense = matrix.toarray().tolist() if hasattr(matrix, "toarray") else []
    return {
        "shape": [int(matrix.shape[0]), int(matrix.shape[1])],
        "dense": dense,
        "signed_sum": sum(sum(float(value) for value in row) for row in dense),
        "nonzero_count": sum(1 for row in dense for value in row if float(value) != 0.0),
    }


def complex_from_hyperedges(tnx: Any, members: dict[str, list[str]], *, pairwise_projection: bool = False) -> Any:
    complex_obj = tnx.SimplicialComplex()
    for nodes in members.values():
        if pairwise_projection:
            record_nodes = [node for node in nodes if node.startswith("record/")]
            bracket_nodes = [node for node in nodes if node.startswith("bracket/")]
            if record_nodes and bracket_nodes:
                complex_obj.add_simplex((record_nodes[0], bracket_nodes[0]))
        else:
            complex_obj.add_simplex(tuple(nodes))
    return complex_obj


def complex_observable(complex_obj: Any) -> dict[str, Any]:
    if len(list(complex_obj.simplices)) == 0:
        incidence = {"shape": [0, 0], "dense": [], "signed_sum": 0.0, "nonzero_count": 0}
    else:
        incidence = matrix_payload(complex_obj.incidence_matrix(1))
    simplices = sorted(str(simplex) for simplex in complex_obj.simplices)
    out = {
        "dim": int(complex_obj.dim),
        "shape": [int(value) for value in complex_obj.shape],
        "simplex_count": len(simplices),
        "simplices": simplices,
        "incidence_rank_1": incidence,
    }
    out["observable_digest"] = stable_sha256(out)
    return out


def probe(
    mc_payload: dict[str, Any],
    gate_payload: dict[str, Any],
    prior_xgi_payload: dict[str, Any],
    prior_toponetx_payload: dict[str, Any],
) -> dict[str, Any]:
    xgi, tnx = import_tools()
    rows = admitted_record_rows(mc_payload)
    graph, members = build_xgi_admitted_hypergraph(xgi, rows)
    xgi_obs = xgi_observable(xgi, graph, members)
    complex_obj = complex_from_hyperedges(tnx, members)
    complex_obs = complex_observable(complex_obj)

    collapsed_graph, collapsed_members = build_xgi_admitted_hypergraph(xgi, rows, collapse_bracketing=True)
    collapsed_xgi_obs = xgi_observable(xgi, collapsed_graph, collapsed_members)
    collapsed_complex = complex_from_hyperedges(tnx, collapsed_members)
    collapsed_complex_obs = complex_observable(collapsed_complex)

    pairwise_complex = complex_from_hyperedges(tnx, members, pairwise_projection=True)
    pairwise_complex_obs = complex_observable(pairwise_complex)
    empty_complex_obs = complex_observable(tnx.SimplicialComplex())

    gate_eligible = gate_payload.get("eligible_consumers") or []
    gate_blocked = gate_payload.get("blocked_consumers") or gate_payload.get("blocked_downstream_consumers") or []
    prior_receipts_ok = (
        prior_xgi_payload.get("all_pass") is True
        and prior_xgi_payload.get("classification") == "tool_lego_fit_probe"
        and prior_xgi_payload.get("stage_movement_allowed") is False
        and prior_toponetx_payload.get("all_pass") is True
        and prior_toponetx_payload.get("classification") == "tool_lego_fit_probe"
        and prior_toponetx_payload.get("stage_movement_allowed") is False
    )

    positive = {
        "parent_fit_receipts_consumed": check(
            "parent_fit_receipts_consumed",
            prior_receipts_ok,
            expected={"xgi": "tool_lego_fit_probe all_pass true no stage movement", "toponetx": "same"},
            observed={
                "xgi": {
                    "classification": prior_xgi_payload.get("classification"),
                    "all_pass": prior_xgi_payload.get("all_pass"),
                    "stage_movement_allowed": prior_xgi_payload.get("stage_movement_allowed"),
                },
                "toponetx": {
                    "classification": prior_toponetx_payload.get("classification"),
                    "all_pass": prior_toponetx_payload.get("all_pass"),
                    "stage_movement_allowed": prior_toponetx_payload.get("stage_movement_allowed"),
                },
            },
            reason="tool-tool coupling must cite two prior parent fit receipts",
        ),
        "xgi_admitted_hyperedges_live": check(
            "xgi_admitted_hyperedges_live",
            len(rows) == 4 and xgi_obs["edge_count"] == 4 and sorted(xgi_obs["bracket_nodes"]) == ["bracket/left", "bracket/right"],
            expected={"admitted_rows": 4, "edge_count": 4, "bracket_nodes": ["bracket/left", "bracket/right"]},
            observed={"admitted_rows": len(rows), "edge_count": xgi_obs["edge_count"], "bracket_nodes": xgi_obs["bracket_nodes"], "incidence_shape": xgi_obs["incidence_shape"]},
            reason="XGI must carry the finite admitted-record hyperedges including left/right bracketing nodes",
        ),
        "toponetx_incidence_from_xgi_hyperedges_live": check(
            "toponetx_incidence_from_xgi_hyperedges_live",
            complex_obs["simplex_count"] > 4
            and complex_obs["incidence_rank_1"]["nonzero_count"] > 0
            and complex_obs["incidence_rank_1"]["shape"][0] > 0
            and complex_obs["incidence_rank_1"]["shape"][1] > 0,
            expected={"simplex_count_gt": 4, "nonzero_incidence": True},
            observed={
                "simplex_count": complex_obs["simplex_count"],
                "incidence_shape": complex_obs["incidence_rank_1"]["shape"],
                "nonzero_count": complex_obs["incidence_rank_1"]["nonzero_count"],
            },
            reason="TopoNetX must emit a nontrivial signed incidence readout from the XGI hyperedge members",
        ),
    }
    negative = {
        "bracketing_collapse_changes_coupled_observable": check(
            "bracketing_collapse_changes_coupled_observable",
            collapsed_xgi_obs["observable_digest"] != xgi_obs["observable_digest"]
            and collapsed_complex_obs["observable_digest"] != complex_obs["observable_digest"],
            expected={"xgi_digest_changes": True, "toponetx_digest_changes": True},
            observed={
                "xgi": {"positive": xgi_obs["observable_digest"], "collapsed": collapsed_xgi_obs["observable_digest"]},
                "toponetx": {"positive": complex_obs["observable_digest"], "collapsed": collapsed_complex_obs["observable_digest"]},
            },
            reason="Collapsing left/right bracketing must change both the XGI carrier and the TopoNetX incidence carrier",
        ),
        "pairwise_projection_loses_hyperedge_incidence": check(
            "pairwise_projection_loses_hyperedge_incidence",
            pairwise_complex_obs["observable_digest"] != complex_obs["observable_digest"]
            and pairwise_complex_obs["dim"] < complex_obs["dim"],
            expected={"digest_changes": True, "dimension_drops": True},
            observed={
                "positive_digest": complex_obs["observable_digest"],
                "pairwise_digest": pairwise_complex_obs["observable_digest"],
                "positive_dim": complex_obs["dim"],
                "pairwise_dim": pairwise_complex_obs["dim"],
            },
            reason="Pairwise record/bracket projection must not be equivalent to the full multiway hyperedge-to-simplex incidence fixture",
        ),
        "empty_complex_demotes": check(
            "empty_complex_demotes",
            empty_complex_obs["simplex_count"] == 0
            and empty_complex_obs["incidence_rank_1"]["nonzero_count"] == 0
            and empty_complex_obs["observable_digest"] != complex_obs["observable_digest"],
            expected={"empty_simplex_count": 0, "empty_nonzero_incidence": 0, "digest_changes": True},
            observed={
                "empty": empty_complex_obs,
                "positive_digest": complex_obs["observable_digest"],
            },
            reason="An empty TopoNetX carrier must demote the coupled evidence",
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
        "xgi_observable": xgi_obs,
        "toponetx_observable": complex_obs,
        "collapsed_xgi_observable": collapsed_xgi_obs,
        "collapsed_toponetx_observable": collapsed_complex_obs,
        "pairwise_toponetx_observable": pairwise_complex_obs,
        "empty_toponetx_observable": empty_complex_obs,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }


def build_result() -> dict[str, Any]:
    started = time.perf_counter()
    mc_payload, mc_error = load_json(MC_V1_RESULT_PATH)
    gate_payload, gate_error = load_json(CONSUMER_GATE_RESULT_PATH)
    prior_xgi_payload, xgi_error = load_json(PRIOR_XGI_RESULT_PATH)
    prior_toponetx_payload, toponetx_error = load_json(PRIOR_TOPONETX_RESULT_PATH)
    receipt_checks: dict[str, dict[str, Any]] = {}
    for label, path, load_error in [
        ("mc_v1", MC_V1_RESULT_PATH, mc_error),
        ("consumer_gate", CONSUMER_GATE_RESULT_PATH, gate_error),
        ("parent_xgi", PRIOR_XGI_RESULT_PATH, xgi_error),
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
        details = probe(mc_payload, gate_payload, prior_xgi_payload, prior_toponetx_payload)
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
            "parent_xgi": str(PRIOR_XGI_RESULT_PATH),
            "parent_toponetx": str(PRIOR_TOPONETX_RESULT_PATH),
        },
        "input_receipt_sha256": {
            "mc_v1": sha256_file(MC_V1_RESULT_PATH),
            "consumer_gate": sha256_file(CONSUMER_GATE_RESULT_PATH),
            "parent_xgi": sha256_file(PRIOR_XGI_RESULT_PATH),
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
                "next_admissible_step": "Repair only this bounded XGI/TopoNetX coupling probe or demote it; do not move stage.",
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

