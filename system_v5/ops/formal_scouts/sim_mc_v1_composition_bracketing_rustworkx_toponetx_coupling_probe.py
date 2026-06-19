#!/usr/bin/env python3
"""Scratch tool-tool coupling probe for M(C) v1 composition paths and bracketing incidence."""

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


OBJECT_ID = "mc_v1_composition_bracketing_rustworkx_toponetx_coupling_probe"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_mc_v1_composition_bracketing_rustworkx_toponetx_coupling_probe.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_composition_bracketing_rustworkx_toponetx_coupling_probe_results.json"
MC_V1_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json"
CONSUMER_GATE_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quarantine_consumer_gate_probe_results.json"
PRIOR_RUSTWORKX_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json"
PRIOR_TOPONETX_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json"
BLOCKED_REASON_PATH = ROOT / "system_v5/ops/wizard_admissions/mc_v1_composition_bracketing_rustworkx_toponetx_coupling_probe_blocked_reason.json"

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
    "bracketing promotion",
    "carrier_readout_map promotion",
    "topological invariant or geometry claim",
]

CLAIM_CEILING = (
    "Scratch diagnostic tool-tool coupling only: rustworkx ordered local-path DAGs "
    "and TopoNetX finite signed-incidence complexes can be checked against the "
    "same admitted M(C) v1 records after both parent fit receipts. This does not "
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
    "Demote if either parent fit receipt fails validation, if rustworkx no longer "
    "emits a finite acyclic ordered-path graph, if TopoNetX no longer emits a "
    "nontrivial signed incidence complex over the same path/bracket/readout "
    "records, if path collapse, bracketing collapse, or cycle controls do not "
    "change or demote the coupled observable, if strong consumers become eligible, "
    "or if any promotion/admission flag becomes true."
)

TOOL_MANIFEST = {
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PyDiGraph path nodes, record reachability, topological order, and cycle control for local composition paths",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SimplicialComplex construction and signed incidence_matrix(1) readout over path/bracket/readout records",
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


def import_tools() -> tuple[Any, Any]:
    import rustworkx as rx
    import toponetx as tnx

    return rx, tnx


def ordered_ops(path_label: str) -> list[str]:
    if "_then_" in path_label:
        return [part for part in path_label.split("_then_") if part]
    return [path_label]


def readout_signature(readout: list[Any]) -> str:
    return ",".join(str(int(value)) for value in readout)


def support_by_id(mc_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id")): row
        for row in ((mc_payload.get("support_S") or {}).get("elements") or [])
        if isinstance(row, dict) and row.get("id")
    }


def admitted_rows(mc_payload: dict[str, Any]) -> list[dict[str, Any]]:
    support = support_by_id(mc_payload)
    carrier_map = mc_payload.get("carrier_readout_map") or {}
    rows = []
    for record_id in sorted(str(item) for item in ((mc_payload.get("Adm_C") or {}).get("admitted_ids") or [])):
        row = support.get(record_id) or {}
        composition = row.get("composition") or {}
        labels = composition.get("composition") or []
        path_label = "_then_".join(str(item) for item in labels) if labels else "unknown_path"
        carrier = carrier_map.get(record_id) or {}
        rows.append(
            {
                "id": record_id,
                "path_label": path_label,
                "bracketing": str(row.get("bracketing") or "unknown"),
                "readout": list(carrier.get("selected") or []),
                "rho_key": str(row.get("rho_key") or "unknown"),
            }
        )
    return rows


def allowed_paths(mc_payload: dict[str, Any]) -> list[str]:
    rules = (mc_payload.get("composition_and_local_paths") or {}).get("local_path_rules") or {}
    paths = [str(item) for item in (rules.get("allowed_paths") or [])]
    return paths or ["Z_then_X", "X_then_Z", "left_assoc", "right_assoc"]


def node_with_key(graph: Any, key: str) -> int | None:
    for index in graph.node_indices():
        if graph.get_node_data(index).get("node_key") == key:
            return int(index)
    return None


def build_path_graph(
    rx: Any,
    rows: list[dict[str, Any]],
    paths: list[str],
    *,
    collapse_paths: bool = False,
    cycle: bool = False,
) -> tuple[Any, dict[str, Any]]:
    graph = rx.PyDiGraph()
    root = graph.add_node({"node_key": "input/root", "kind": "root"})
    sink = graph.add_node({"node_key": "output/sink", "kind": "sink"})
    path_handles: dict[str, int] = {}
    for label in paths:
        node_key = "path/collapsed" if collapse_paths else f"path/{label}"
        existing = node_with_key(graph, node_key)
        if existing is None:
            path_handles[label] = graph.add_node(
                {
                    "node_key": node_key,
                    "kind": "local_path",
                    "path_label": "collapsed" if collapse_paths else label,
                    "ordered_ops": [] if collapse_paths else ordered_ops(label),
                }
            )
        else:
            path_handles[label] = existing
    record_handles: dict[str, int] = {}
    for row in rows:
        record_index = graph.add_node({"node_key": f"record/{row['id']}", "kind": "admitted_record"})
        record_handles[row["id"]] = record_index
        path_index = path_handles.get(row["path_label"]) or path_handles.get("Z_then_X") or next(iter(path_handles.values()))
        graph.add_edge(root, path_index, {"edge_key": "select_path", "path_label": row["path_label"]})
        graph.add_edge(path_index, record_index, {"edge_key": f"path_to_record/{row['id']}", "path_label": row["path_label"]})
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


def matrix_payload(matrix: Any) -> dict[str, Any]:
    dense = matrix.toarray().tolist() if hasattr(matrix, "toarray") else []
    return {
        "shape": [int(matrix.shape[0]), int(matrix.shape[1])],
        "dense": dense,
        "signed_sum": sum(sum(float(value) for value in row) for row in dense),
        "nonzero_count": sum(1 for row in dense for value in row if float(value) != 0.0),
    }


def build_complex(
    tnx: Any,
    rows: list[dict[str, Any]],
    paths: list[str],
    *,
    collapse_paths: bool = False,
    collapse_brackets: bool = False,
    empty: bool = False,
) -> Any:
    complex_obj = tnx.SimplicialComplex()
    if empty:
        return complex_obj
    for path in paths:
        path_node = "path/collapsed" if collapse_paths else f"path/{path}"
        complex_obj.add_simplex((path_node,))
    for row in rows:
        path_node = "path/collapsed" if collapse_paths else f"path/{row['path_label']}"
        record_node = f"record/{row['id']}"
        bracket_node = "bracket/collapsed" if collapse_brackets else f"bracket/{row['bracketing']}"
        readout_node = f"readout/{readout_signature(row['readout'])}"
        complex_obj.add_simplex((path_node, record_node))
        complex_obj.add_simplex((record_node, bracket_node))
        complex_obj.add_simplex((bracket_node, readout_node))
        complex_obj.add_simplex((path_node, record_node, bracket_node))
    return complex_obj


def complex_observable(complex_obj: Any) -> dict[str, Any]:
    simplices = sorted(str(simplex) for simplex in complex_obj.simplices)
    if not simplices:
        incidence = {"shape": [0, 0], "dense": [], "signed_sum": 0.0, "nonzero_count": 0}
    else:
        incidence = matrix_payload(complex_obj.incidence_matrix(1))
    out = {
        "dim": int(complex_obj.dim),
        "shape": [int(value) for value in complex_obj.shape],
        "simplex_count": len(simplices),
        "simplices": simplices,
        "path_nodes": sorted({item for simplex in simplices for item in simplex.split(",") if "path/" in item}),
        "bracket_nodes": sorted({item for simplex in simplices for item in simplex.split(",") if "bracket/" in item}),
        "incidence_rank_1": incidence,
    }
    out["observable_digest"] = stable_sha256(out)
    return out


def probe(
    mc_payload: dict[str, Any],
    gate_payload: dict[str, Any],
    prior_rustworkx_payload: dict[str, Any],
    prior_toponetx_payload: dict[str, Any],
) -> dict[str, Any]:
    rx, tnx = import_tools()
    rows = admitted_rows(mc_payload)
    paths = allowed_paths(mc_payload)

    graph, handles = build_path_graph(rx, rows, paths)
    graph_obs = graph_observable(rx, graph, handles)
    complex_obj = build_complex(tnx, rows, paths)
    complex_obs = complex_observable(complex_obj)

    collapsed_graph, collapsed_handles = build_path_graph(rx, rows, paths, collapse_paths=True)
    collapsed_graph_obs = graph_observable(rx, collapsed_graph, collapsed_handles)
    collapsed_complex = build_complex(tnx, rows, paths, collapse_paths=True)
    collapsed_complex_obs = complex_observable(collapsed_complex)

    bracket_complex = build_complex(tnx, rows, paths, collapse_brackets=True)
    bracket_complex_obs = complex_observable(bracket_complex)

    cycle_graph, cycle_handles = build_path_graph(rx, rows, paths, cycle=True)
    cycle_graph_obs = graph_observable(rx, cycle_graph, cycle_handles)
    empty_complex = build_complex(tnx, rows, paths, empty=True)
    empty_complex_obs = complex_observable(empty_complex)

    coupled_digest = stable_sha256({"rustworkx": graph_obs["observable_digest"], "toponetx": complex_obs["observable_digest"]})
    collapsed_digest = stable_sha256({"rustworkx": collapsed_graph_obs["observable_digest"], "toponetx": collapsed_complex_obs["observable_digest"]})
    bracket_digest = stable_sha256({"rustworkx": graph_obs["observable_digest"], "toponetx": bracket_complex_obs["observable_digest"]})
    cycle_digest = stable_sha256({"rustworkx": cycle_graph_obs["observable_digest"], "toponetx": empty_complex_obs["observable_digest"]})

    gate_eligible = gate_payload.get("eligible_consumers") or []
    gate_blocked = gate_payload.get("blocked_consumers") or gate_payload.get("blocked_downstream_consumers") or []
    prior_receipts_ok = (
        prior_rustworkx_payload.get("all_pass") is True
        and prior_rustworkx_payload.get("classification") == "tool_lego_fit_probe"
        and prior_rustworkx_payload.get("stage_movement_allowed") is False
        and prior_toponetx_payload.get("all_pass") is True
        and prior_toponetx_payload.get("classification") == "tool_lego_fit_probe"
        and prior_toponetx_payload.get("stage_movement_allowed") is False
    )

    positive = {
        "parent_fit_receipts_consumed": check(
            "parent_fit_receipts_consumed",
            prior_receipts_ok,
            expected={"rustworkx": "tool_lego_fit_probe all_pass true no stage movement", "toponetx": "same"},
            observed={
                "rustworkx": {
                    "classification": prior_rustworkx_payload.get("classification"),
                    "all_pass": prior_rustworkx_payload.get("all_pass"),
                    "stage_movement_allowed": prior_rustworkx_payload.get("stage_movement_allowed"),
                },
                "toponetx": {
                    "classification": prior_toponetx_payload.get("classification"),
                    "all_pass": prior_toponetx_payload.get("all_pass"),
                    "stage_movement_allowed": prior_toponetx_payload.get("stage_movement_allowed"),
                },
            },
            reason="tool-tool coupling must cite two prior parent fit receipts",
        ),
        "same_records_and_paths_coupled": check(
            "same_records_and_paths_coupled",
            len(rows) == 4
            and graph_obs["record_nodes"] == sorted(f"record/{row['id']}" for row in rows)
            and len(complex_obs["path_nodes"]) >= 1,
            expected={"admitted_records": 4, "record_nodes_match": True, "path_nodes_present": True},
            observed={"rows": rows, "graph_record_nodes": graph_obs["record_nodes"], "complex_path_nodes": complex_obs["path_nodes"]},
            reason="rustworkx and TopoNetX must operate on the same admitted records and local path labels",
        ),
        "dag_and_incidence_positive_claim_live": check(
            "dag_and_incidence_positive_claim_live",
            graph_obs["is_dag"] is True
            and graph_obs["input_reaches_output"] is True
            and complex_obs["incidence_rank_1"]["nonzero_count"] > 0,
            expected={"rustworkx_dag": True, "reachability": True, "toponetx_nonzero_incidence": True},
            observed={"rustworkx": graph_obs, "toponetx_incidence": complex_obs["incidence_rank_1"]},
            reason="rustworkx must carry ordered path reachability while TopoNetX carries the finite incidence readout",
        ),
    }
    negative = {
        "path_collapse_changes_both_observables": check(
            "path_collapse_changes_both_observables",
            collapsed_graph_obs["observable_digest"] != graph_obs["observable_digest"]
            and collapsed_complex_obs["observable_digest"] != complex_obs["observable_digest"]
            and collapsed_digest != coupled_digest,
            expected={"rustworkx_digest_changes": True, "toponetx_digest_changes": True, "coupled_digest_changes": True},
            observed={"positive_digest": coupled_digest, "collapsed_digest": collapsed_digest, "collapsed_path_nodes": collapsed_graph_obs["path_nodes"]},
            reason="Collapsing local paths must change both the rustworkx path object and the TopoNetX incidence object",
        ),
        "bracketing_collapse_changes_incidence": check(
            "bracketing_collapse_changes_incidence",
            bracket_complex_obs["observable_digest"] != complex_obs["observable_digest"]
            and bracket_digest != coupled_digest,
            expected={"toponetx_digest_changes": True, "coupled_digest_changes": True},
            observed={"positive_digest": coupled_digest, "bracket_digest": bracket_digest, "collapsed_brackets": bracket_complex_obs["bracket_nodes"]},
            reason="Collapsing bracket nodes must change the TopoNetX side of the coupled observable",
        ),
        "cycle_and_empty_complex_demote": check(
            "cycle_and_empty_complex_demote",
            cycle_graph_obs["is_dag"] is False
            and cycle_graph_obs["topological_sort_success"] is False
            and empty_complex_obs["simplex_count"] == 0
            and cycle_digest != coupled_digest,
            expected={"cycle_breaks_dag": True, "empty_complex": True, "coupled_digest_changes": True},
            observed={"cycle_rustworkx": cycle_graph_obs, "empty_toponetx": empty_complex_obs, "cycle_digest": cycle_digest, "positive_digest": coupled_digest},
            reason="A cyclic graph plus empty incidence fixture is demoted baseline/control evidence only",
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
        "allowed_paths": paths,
        "rustworkx_observable": graph_obs,
        "toponetx_observable": complex_obs,
        "path_collapsed_rustworkx_observable": collapsed_graph_obs,
        "path_collapsed_toponetx_observable": collapsed_complex_obs,
        "bracket_collapsed_toponetx_observable": bracket_complex_obs,
        "cycle_rustworkx_observable": cycle_graph_obs,
        "empty_toponetx_observable": empty_complex_obs,
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
    prior_toponetx_payload, toponetx_error = load_json(PRIOR_TOPONETX_RESULT_PATH)
    receipt_checks: dict[str, dict[str, Any]] = {}
    for label, path, load_error in [
        ("mc_v1", MC_V1_RESULT_PATH, mc_error),
        ("consumer_gate", CONSUMER_GATE_RESULT_PATH, gate_error),
        ("parent_rustworkx", PRIOR_RUSTWORKX_RESULT_PATH, rustworkx_error),
        ("parent_toponetx", PRIOR_TOPONETX_RESULT_PATH, toponetx_error),
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
        details = probe(mc_payload, gate_payload, prior_rustworkx_payload, prior_toponetx_payload)
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
            "parent_toponetx": str(PRIOR_TOPONETX_RESULT_PATH),
        },
        "input_receipt_sha256": {
            "mc_v1": sha256_file(MC_V1_RESULT_PATH),
            "consumer_gate": sha256_file(CONSUMER_GATE_RESULT_PATH),
            "parent_rustworkx": sha256_file(PRIOR_RUSTWORKX_RESULT_PATH),
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
                "next_admissible_step": "Repair only this bounded rustworkx/TopoNetX coupling probe or demote it; do not move stage.",
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
