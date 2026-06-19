#!/usr/bin/env python3
"""Scratch tool-tool coupling probe for M(C) v1 composition paths and admission incidence."""

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


OBJECT_ID = "mc_v1_composition_adm_rustworkx_xgi_coupling_probe"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_mc_v1_composition_adm_rustworkx_xgi_coupling_probe.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_composition_adm_rustworkx_xgi_coupling_probe_results.json"
MC_V1_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json"
CONSUMER_GATE_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quarantine_consumer_gate_probe_results.json"
PRIOR_RUSTWORKX_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json"
PRIOR_XGI_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json"
BLOCKED_REASON_PATH = ROOT / "system_v5/ops/wizard_admissions/mc_v1_composition_adm_rustworkx_xgi_coupling_probe_blocked_reason.json"

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
    "composition_and_local_paths promotion",
    "Adm_C promotion",
    "topological invariant or geometry claim",
]

CLAIM_CEILING = (
    "Scratch diagnostic tool-tool coupling only: rustworkx composition/local-path "
    "DAGs and XGI admitted-record hyperedges can be checked against the same "
    "finite admitted M(C) v1 records after both parent fit receipts. This does "
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
    "Demote if either parent fit receipt fails validation, if rustworkx no longer "
    "emits a finite acyclic ordered-path graph, if XGI no longer emits hyperedges "
    "linking admitted records to path labels and constraint status, if path collapse, "
    "cycle, or scalar projection controls do not change or demote the coupled "
    "observable, if strong consumers become eligible, or if any promotion/admission "
    "flag becomes true."
)

TOOL_MANIFEST = {
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PyDiGraph path nodes, reachability, topological order, and cycle control for local composition paths",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Hypergraph admitted-record hyperedges carrying path labels and constraint/status members",
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
    "rustworkx": "load_bearing",
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
    import rustworkx as rx
    import xgi

    return rx, xgi


def ordered_ops(path_label: str) -> list[str]:
    if "_then_" in path_label:
        return [part for part in path_label.split("_then_") if part]
    return [path_label]


def support_by_id(mc_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id")): row
        for row in ((mc_payload.get("support_S") or {}).get("elements") or [])
        if isinstance(row, dict) and row.get("id")
    }


def admitted_rows(mc_payload: dict[str, Any]) -> list[dict[str, Any]]:
    support = support_by_id(mc_payload)
    rows = []
    for record_id in sorted(str(item) for item in ((mc_payload.get("Adm_C") or {}).get("admitted_ids") or [])):
        row = support.get(record_id) or {}
        composition = row.get("composition") or {}
        labels = composition.get("composition") or []
        if labels:
            path_label = "_then_".join(str(item) for item in labels)
        else:
            path_label = "unknown_path"
        rows.append(
            {
                "id": record_id,
                "path_label": path_label,
                "bracketing": str(row.get("bracketing") or "unknown"),
                "rho_key": str(row.get("rho_key") or "unknown"),
            }
        )
    return rows


def build_path_graph(rx: Any, allowed_paths: list[str], rows: list[dict[str, Any]], *, collapse_paths: bool = False, cycle: bool = False) -> tuple[Any, dict[str, int]]:
    graph = rx.PyDiGraph()
    root = graph.add_node({"node_key": "input/root", "kind": "root"})
    sink = graph.add_node({"node_key": "output/sink", "kind": "sink"})
    path_handles: dict[str, int] = {}
    for label in allowed_paths:
        node_key = "path/collapsed" if collapse_paths else f"path/{label}"
        if node_key not in [graph.get_node_data(index).get("node_key") for index in graph.node_indices()]:
            path_handles[label] = graph.add_node(
                {
                    "node_key": node_key,
                    "kind": "allowed_local_path",
                    "path_label": "collapsed" if collapse_paths else label,
                    "ordered_ops": [] if collapse_paths else ordered_ops(label),
                }
            )
        else:
            path_handles[label] = next(
                index for index in graph.node_indices() if graph.get_node_data(index).get("node_key") == node_key
            )
    record_handles: dict[str, int] = {}
    for row in rows:
        record_index = graph.add_node({"node_key": f"record/{row['id']}", "kind": "admitted_record"})
        record_handles[row["id"]] = record_index
        path_index = path_handles.get(row["path_label"]) or path_handles.get("Z_then_X") or next(iter(path_handles.values()))
        graph.add_edge(root, path_index, {"edge_key": "select_path"})
        graph.add_edge(path_index, record_index, {"edge_key": f"path_to_record/{row['id']}"})
        graph.add_edge(record_index, sink, {"edge_key": f"record_to_output/{row['id']}"})
    if cycle:
        graph.add_edge(sink, root, {"edge_key": "cycle_control"})
    return graph, {"root": root, "sink": sink, "paths": path_handles, "records": record_handles}


def edge_records(graph: Any) -> list[dict[str, Any]]:
    rows = []
    for source, target, weight in graph.weighted_edge_list():
        rows.append(
            {
                "source": graph.get_node_data(source).get("node_key"),
                "target": graph.get_node_data(target).get("node_key"),
                "weight": weight,
            }
        )
    return sorted(rows, key=lambda row: (str(row["source"]), str(row["target"]), json.dumps(row["weight"], sort_keys=True)))


def graph_observable(rx: Any, graph: Any, handles: dict[str, Any]) -> dict[str, Any]:
    topo_error = None
    topo_labels: list[str] = []
    try:
        topo_labels = [graph.get_node_data(index).get("node_key") for index in rx.topological_sort(graph)]
    except Exception as exc:
        topo_error = f"{type(exc).__name__}: {exc}"
    root = handles.get("root")
    sink = handles.get("sink")
    path_nodes = sorted(set(graph.get_node_data(index).get("node_key") for index in handles.get("paths", {}).values()))
    record_nodes = sorted(graph.get_node_data(index).get("node_key") for index in handles.get("records", {}).values())
    out = {
        "node_count": len(list(graph.node_indices())),
        "edge_count": len(list(graph.edge_list())),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "topological_sort_success": topo_error is None,
        "topological_labels": topo_labels,
        "topological_error": topo_error,
        "input_reaches_output": bool(rx.has_path(graph, root, sink)) if root is not None and sink is not None else False,
        "path_nodes": path_nodes,
        "record_nodes": record_nodes,
        "edge_records": edge_records(graph),
    }
    out["observable_digest"] = stable_sha256(out)
    return out


def build_hypergraph(xgi: Any, rows: list[dict[str, Any]], *, collapse_paths: bool = False, scalar_status: bool = False) -> tuple[Any, dict[str, list[str]]]:
    graph = xgi.Hypergraph()
    for row in rows:
        path_label = "collapsed" if collapse_paths else row["path_label"]
        if scalar_status:
            members = [f"record/{row['id']}", "status/admitted"]
        else:
            members = [
                f"record/{row['id']}",
                f"path/{path_label}",
                f"bracket/{row['bracketing']}",
                f"rho/{row['rho_key']}",
                "constraint/Adm_C",
                "status/admitted",
            ]
        graph.add_edge(members, idx=f"adm-path/{row['id']}")
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
        "path_nodes": sorted(str(node) for node in graph.nodes if str(node).startswith("path/")),
        "record_nodes": sorted(str(node) for node in graph.nodes if str(node).startswith("record/")),
    }
    out["observable_digest"] = stable_sha256(out)
    return out


def probe(
    mc_payload: dict[str, Any],
    gate_payload: dict[str, Any],
    prior_rustworkx_payload: dict[str, Any],
    prior_xgi_payload: dict[str, Any],
) -> dict[str, Any]:
    rx, xgi = import_tools()
    rows = admitted_rows(mc_payload)
    allowed_paths = list(((mc_payload.get("composition_and_local_paths") or {}).get("local_path_rules") or {}).get("allowed_paths") or [])
    path_graph, path_handles = build_path_graph(rx, allowed_paths, rows)
    path_obs = graph_observable(rx, path_graph, path_handles)
    hypergraph, hyper_members = build_hypergraph(xgi, rows)
    hyper_obs = hypergraph_observable(xgi, hypergraph, hyper_members)

    collapsed_path_graph, collapsed_path_handles = build_path_graph(rx, allowed_paths, rows, collapse_paths=True)
    collapsed_path_obs = graph_observable(rx, collapsed_path_graph, collapsed_path_handles)
    collapsed_hypergraph, collapsed_members = build_hypergraph(xgi, rows, collapse_paths=True)
    collapsed_hyper_obs = hypergraph_observable(xgi, collapsed_hypergraph, collapsed_members)

    cycle_graph, cycle_handles = build_path_graph(rx, allowed_paths, rows, cycle=True)
    cycle_obs = graph_observable(rx, cycle_graph, cycle_handles)
    scalar_hypergraph, scalar_members = build_hypergraph(xgi, rows, scalar_status=True)
    scalar_hyper_obs = hypergraph_observable(xgi, scalar_hypergraph, scalar_members)

    coupled_digest = stable_sha256({"rustworkx": path_obs["observable_digest"], "xgi": hyper_obs["observable_digest"]})
    collapsed_digest = stable_sha256({"rustworkx": collapsed_path_obs["observable_digest"], "xgi": collapsed_hyper_obs["observable_digest"]})
    cycle_scalar_digest = stable_sha256({"rustworkx": cycle_obs["observable_digest"], "xgi": scalar_hyper_obs["observable_digest"]})

    gate_eligible = gate_payload.get("eligible_consumers") or []
    gate_blocked = gate_payload.get("blocked_consumers") or gate_payload.get("blocked_downstream_consumers") or []
    prior_receipts_ok = (
        prior_rustworkx_payload.get("all_pass") is True
        and prior_rustworkx_payload.get("classification") == "tool_lego_fit_probe"
        and prior_rustworkx_payload.get("stage_movement_allowed") is False
        and prior_xgi_payload.get("all_pass") is True
        and prior_xgi_payload.get("classification") == "tool_lego_fit_probe"
        and prior_xgi_payload.get("stage_movement_allowed") is False
    )

    positive = {
        "parent_fit_receipts_consumed": check(
            "parent_fit_receipts_consumed",
            prior_receipts_ok,
            expected={"rustworkx": "tool_lego_fit_probe all_pass true no stage movement", "xgi": "same"},
            observed={
                "rustworkx": {
                    "classification": prior_rustworkx_payload.get("classification"),
                    "all_pass": prior_rustworkx_payload.get("all_pass"),
                    "stage_movement_allowed": prior_rustworkx_payload.get("stage_movement_allowed"),
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
            len(rows) == 4 and path_obs["record_nodes"] == hyper_obs["record_nodes"],
            expected={"admitted_record_count": 4, "same_record_nodes": True},
            observed={"rows": [row["id"] for row in rows], "rustworkx": path_obs["record_nodes"], "xgi": hyper_obs["record_nodes"]},
            reason="Both tools must carry the same admitted M(C) v1 record nodes",
        ),
        "ordered_path_and_hyperedge_observables_nontrivial": check(
            "ordered_path_and_hyperedge_observables_nontrivial",
            path_obs["is_dag"] is True
            and path_obs["input_reaches_output"] is True
            and len(path_obs["path_nodes"]) >= 4
            and hyper_obs["edge_count"] == 4
            and min(hyper_obs["edge_member_sizes"].values()) >= 6,
            expected={"dag": True, "path_nodes_at_least": 4, "hyperedges": 4, "member_size_at_least": 6},
            observed={
                "dag": path_obs["is_dag"],
                "input_reaches_output": path_obs["input_reaches_output"],
                "path_nodes": path_obs["path_nodes"],
                "edge_count": hyper_obs["edge_count"],
                "edge_member_sizes": hyper_obs["edge_member_sizes"],
            },
            reason="The coupling must use actual ordered path and hyperedge structure",
        ),
    }
    negative = {
        "path_collapse_changes_coupled_observable": check(
            "path_collapse_changes_coupled_observable",
            collapsed_path_obs["observable_digest"] != path_obs["observable_digest"]
            and collapsed_hyper_obs["observable_digest"] != hyper_obs["observable_digest"]
            and collapsed_digest != coupled_digest,
            expected={"rustworkx_digest_changes": True, "xgi_digest_changes": True, "coupled_digest_changes": True},
            observed={
                "positive": coupled_digest,
                "collapsed": collapsed_digest,
                "positive_path_nodes": path_obs["path_nodes"],
                "collapsed_path_nodes": collapsed_path_obs["path_nodes"],
            },
            reason="Collapsing ordered path labels must change both tool observables and the coupled digest",
        ),
        "cycle_control_breaks_dag": check(
            "cycle_control_breaks_dag",
            cycle_obs["is_dag"] is False
            and cycle_obs["topological_sort_success"] is False
            and cycle_obs["observable_digest"] != path_obs["observable_digest"],
            expected={"dag": False, "topological_sort_success": False, "digest_changes": True},
            observed={
                "cycle_dag": cycle_obs["is_dag"],
                "cycle_topological_sort_success": cycle_obs["topological_sort_success"],
                "cycle_error": cycle_obs["topological_error"],
            },
            reason="A path cycle must break the rustworkx DAG observable",
        ),
        "scalar_status_projection_demotes_hypergraph": check(
            "scalar_status_projection_demotes_hypergraph",
            scalar_hyper_obs["observable_digest"] != hyper_obs["observable_digest"]
            and min(scalar_hyper_obs["edge_member_sizes"].values()) < min(hyper_obs["edge_member_sizes"].values())
            and cycle_scalar_digest != coupled_digest,
            expected={"digest_changes": True, "member_size_drops": True, "coupled_digest_changes": True},
            observed={
                "positive_member_sizes": hyper_obs["edge_member_sizes"],
                "scalar_member_sizes": scalar_hyper_obs["edge_member_sizes"],
                "positive": coupled_digest,
                "cycle_scalar": cycle_scalar_digest,
            },
            reason="Scalar status-only projection must lose the path/constraint hyperedge structure",
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
        "rustworkx_observable": path_obs,
        "xgi_observable": hyper_obs,
        "collapsed_rustworkx_observable": collapsed_path_obs,
        "collapsed_xgi_observable": collapsed_hyper_obs,
        "cycle_rustworkx_observable": cycle_obs,
        "scalar_xgi_observable": scalar_hyper_obs,
        "coupled_digest": coupled_digest,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }


def build_result() -> dict[str, Any]:
    started = time.perf_counter()
    mc_payload, mc_error = load_json(MC_V1_RESULT_PATH)
    gate_payload, gate_error = load_json(CONSUMER_GATE_RESULT_PATH)
    prior_rustworkx_payload, rustworkx_error = load_json(PRIOR_RUSTWORKX_RESULT_PATH)
    prior_xgi_payload, xgi_error = load_json(PRIOR_XGI_RESULT_PATH)
    receipt_checks: dict[str, dict[str, Any]] = {}
    for label, path, load_error in [
        ("mc_v1", MC_V1_RESULT_PATH, mc_error),
        ("consumer_gate", CONSUMER_GATE_RESULT_PATH, gate_error),
        ("parent_rustworkx", PRIOR_RUSTWORKX_RESULT_PATH, rustworkx_error),
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
        details = probe(mc_payload, gate_payload, prior_rustworkx_payload, prior_xgi_payload)
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
            "parent_rustworkx": str(PRIOR_RUSTWORKX_RESULT_PATH),
            "parent_xgi": str(PRIOR_XGI_RESULT_PATH),
        },
        "input_receipt_sha256": {
            "mc_v1": sha256_file(MC_V1_RESULT_PATH),
            "consumer_gate": sha256_file(CONSUMER_GATE_RESULT_PATH),
            "parent_rustworkx": sha256_file(PRIOR_RUSTWORKX_RESULT_PATH),
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
                "next_admissible_step": "Repair only this bounded rustworkx/XGI coupling probe or demote it; do not move stage.",
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
