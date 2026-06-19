#!/usr/bin/env python3
"""rustworkx tool-lego fit probe for M(C) v1 composition/local paths."""

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


OBJECT_ID = "mc_v1_composition_paths_rustworkx_tool_lego_fit_probe"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_mc_v1_composition_paths_rustworkx_tool_lego_fit_probe.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json"
MC_V1_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json"
CONSUMER_GATE_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quarantine_consumer_gate_probe_results.json"
WAVE_A_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/wave_a_cs_ai_no_install_micro_probes_results.json"
PRIOR_CVC5_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json"
BLOCKED_REASON_PATH = ROOT / "system_v5/ops/wizard_admissions/mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_blocked_reason.json"

classification = "tool_lego_fit_probe"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
sim_execution_kind = "classical"
SIM_EXECUTION_KIND = sim_execution_kind
evidence_level = "tool_lego_fit_probe"
EVIDENCE_LEVEL = evidence_level

CLAIM_CEILING = (
    "Tool-lego fit probe only: rustworkx PyDiGraph, node/edge construction, "
    "topological order, DAG failure, and path reachability can carry one bounded "
    "finite composition_and_local_paths fixture for the quarantined M(C) v1 field "
    "after the consumer gate. This does not admit M(C), does not unlock Stage 4, "
    "and does not support same-carrier geometry, topology readout, AI/GNN readout, "
    "bridge, Axis0, physics, manifold, or formal admission claims."
)
NEXT_LEGO_TARGET = (
    "A later packet may audit another exact M(C) v1 field/tool/API fixture; this "
    "receipt itself stays pre-lego fit evidence and cannot move the ladder stage."
)
PROMOTION_CONDITION = (
    "No direct promotion path. Any stronger use needs a separate consumer-aware "
    "admission packet with exact field, controls, stage gate, and receipt evidence."
)
BLOCKED_UNTIL = (
    "Stage movement remains blocked until a future admission packet, not this probe, "
    "passes the relevant M(C), solver/control, composition/bracketing, carrier/readout, "
    "and stage gates."
)
DEMOTION_CONDITION = (
    "Demote if rustworkx cannot build or sort the finite directed path fixture, if "
    "Z_then_X and X_then_Z collapse to one path key, if implicit_reassociation or "
    "carrier_erasure controls do not change the observable, if the consumer gate "
    "stops all_pass, if strong consumers become eligible, or if any promotion/"
    "admission flag becomes true."
)

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
    "exact_tool_lego_fit_probe_after_consumer_gate",
]
OUT_OF_SCOPE = STRONG_CONSUMERS + [
    "Stage 4 movement",
    "M(C) formal admission",
    "composition_and_local_paths promotion",
    "broad topology or geometry interpretation",
]

TOOL_MANIFEST = {
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PyDiGraph node/edge construction, topological order, DAG failure, and finite path reachability for the composition_and_local_paths fixture",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON parsing/writing, repo-local paths, sha256 pinning, elapsed-time measurement, and blocked-reason error capture",
    },
    "receipt_schema": {
        "tried": True,
        "used": True,
        "reason": "supportive strict validation of the consumed receipts against the current repo schema",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "rustworkx": "load_bearing",
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


def ordered_ops(path_label: str) -> list[str]:
    if "_then_" in path_label:
        return [part for part in path_label.split("_then_") if part]
    return [path_label]


def order_key(path_label: str) -> str:
    return ">".join(ordered_ops(path_label))


def reassociated_key(path_label: str) -> str:
    return "|".join(sorted(ordered_ops(path_label)))


def import_rustworkx() -> Any:
    import rustworkx as rx

    return rx


def edge_records(graph: Any) -> list[dict[str, Any]]:
    records = []
    for source, target, weight in graph.weighted_edge_list():
        records.append(
            {
                "source": graph.get_node_data(source).get("node_key"),
                "target": graph.get_node_data(target).get("node_key"),
                "weight": weight,
            }
        )
    return sorted(records, key=lambda row: (str(row["source"]), str(row["target"]), json.dumps(row["weight"], sort_keys=True)))


def graph_observable(rx: Any, graph: Any, handles: dict[str, int]) -> dict[str, Any]:
    topo_error = None
    topo_labels: list[str] = []
    try:
        topo_labels = [graph.get_node_data(index).get("node_key") for index in rx.topological_sort(graph)]
    except Exception as exc:  # rustworkx raises DAGHasCycle for the cycle control.
        topo_error = f"{type(exc).__name__}: {exc}"

    reduction_error = None
    reduction_edges: list[dict[str, Any]] = []
    try:
        reduced, _node_map = rx.transitive_reduction(graph)
        reduction_edges = edge_records(reduced)
    except Exception as exc:
        reduction_error = f"{type(exc).__name__}: {exc}"

    root = handles.get("root")
    sink = handles.get("sink")
    path_handles = handles.get("paths", {})
    path_reachability = {}
    for label, index in sorted(path_handles.items()):
        path_reachability[label] = {
            "input_reaches_path": bool(rx.has_path(graph, root, index)) if root is not None else False,
            "path_reaches_output": bool(rx.has_path(graph, index, sink)) if sink is not None else False,
        }

    represented = sorted(path_handles)
    pair_labels = ["Z_then_X", "X_then_Z"]
    pair_keys = {
        label: graph.get_node_data(path_handles[label]).get("order_sensitive_key")
        for label in pair_labels
        if label in path_handles
    }
    observable = {
        "node_count": len(list(graph.node_indices())),
        "edge_count": len(list(graph.edge_list())),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "topological_sort_success": topo_error is None,
        "topological_labels": topo_labels,
        "topological_error": topo_error,
        "input_reaches_output": bool(rx.has_path(graph, root, sink)) if root is not None and sink is not None else False,
        "represented_allowed_paths": represented,
        "path_reachability": path_reachability,
        "order_sensitive_pair_keys": pair_keys,
        "distinct_order_sensitive_pair_key_count": len(set(pair_keys.values())),
        "edges": edge_records(graph),
        "transitive_reduction_edges": reduction_edges,
        "transitive_reduction_error": reduction_error,
    }
    observable["observable_digest"] = stable_sha256(observable)
    return observable


def build_allowed_path_graph(rx: Any, allowed_consumed_paths: list[str]) -> tuple[Any, dict[str, int]]:
    graph = rx.PyDiGraph()
    root = graph.add_node({"node_key": "input/root", "kind": "root"})
    sink = graph.add_node({"node_key": "output/sink", "kind": "sink"})
    path_handles: dict[str, int] = {}
    for label in allowed_consumed_paths:
        index = graph.add_node(
            {
                "node_key": f"path/{label}",
                "kind": "allowed_local_path",
                "path_label": label,
                "ordered_ops": ordered_ops(label),
                "order_sensitive_key": order_key(label),
            }
        )
        path_handles[label] = index
        graph.add_edge(
            root,
            index,
            {
                "edge_key": f"input_to_{label}",
                "kind": "select_allowed_path",
                "path_label": label,
                "ordered_ops": ordered_ops(label),
            },
        )
        graph.add_edge(
            index,
            sink,
            {
                "edge_key": f"{label}_to_output",
                "kind": "emit_allowed_path",
                "path_label": label,
                "ordered_ops": ordered_ops(label),
            },
        )
    return graph, {"root": root, "sink": sink, "paths": path_handles}


def build_implicit_reassociation_graph(rx: Any, allowed_consumed_paths: list[str]) -> tuple[Any, dict[str, int], dict[str, list[str]]]:
    graph = rx.PyDiGraph()
    root = graph.add_node({"node_key": "input/root", "kind": "root"})
    sink = graph.add_node({"node_key": "output/sink", "kind": "sink"})
    groups: dict[str, list[str]] = {}
    for label in allowed_consumed_paths:
        groups.setdefault(reassociated_key(label), []).append(label)

    path_handles: dict[str, int] = {}
    for collapsed_key, labels in sorted(groups.items()):
        node_label = "+".join(sorted(labels))
        index = graph.add_node(
            {
                "node_key": f"collapsed_path/{collapsed_key}",
                "kind": "forbidden_implicit_reassociation",
                "source_path_labels": sorted(labels),
                "collapsed_order_key": collapsed_key,
            }
        )
        for label in labels:
            path_handles[label] = index
        graph.add_edge(
            root,
            index,
            {
                "edge_key": f"input_to_collapsed_{collapsed_key}",
                "kind": "forbidden_reassociation_select",
                "source_path_labels": sorted(labels),
            },
        )
        graph.add_edge(
            index,
            sink,
            {
                "edge_key": f"collapsed_{node_label}_to_output",
                "kind": "forbidden_reassociation_emit",
                "source_path_labels": sorted(labels),
            },
        )
    return graph, {"root": root, "sink": sink, "paths": path_handles}, groups


def build_carrier_erasure_graph(rx: Any) -> tuple[Any, dict[str, int]]:
    graph = rx.PyDiGraph()
    root = graph.add_node({"node_key": "input/root", "kind": "root"})
    sink = graph.add_node({"node_key": "output/sink", "kind": "sink"})
    graph.add_edge(
        root,
        sink,
        {
            "edge_key": "input_to_output_erased",
            "kind": "forbidden_carrier_erasure",
            "path_label": None,
        },
    )
    return graph, {"root": root, "sink": sink, "paths": {}}


def build_cycle_control_graph(rx: Any, allowed_consumed_paths: list[str]) -> tuple[Any, dict[str, int]]:
    graph, handles = build_allowed_path_graph(rx, allowed_consumed_paths)
    graph.add_edge(
        handles["sink"],
        handles["root"],
        {
            "edge_key": "forbidden_output_to_input_cycle",
            "kind": "cycle_control",
        },
    )
    return graph, handles


def rustworkx_probe(
    mc_payload: dict[str, Any],
    gate_payload: dict[str, Any],
    wave_a_payload: dict[str, Any],
    prior_cvc5_payload: dict[str, Any],
) -> dict[str, Any]:
    rx = import_rustworkx()
    composition = mc_payload.get("composition_and_local_paths") or {}
    rules = composition.get("local_path_rules") or {}
    consumed_local_paths = [str(path) for path in (composition.get("local_paths") or [])]
    consumed_allowed_paths = [str(path) for path in (rules.get("allowed_paths") or [])]
    consumed_forbidden = [str(path) for path in (rules.get("forbidden") or [])]
    allowed_consumed_paths = [
        label for label in consumed_local_paths if label in set(consumed_allowed_paths) and "_then_" in label
    ]
    excluded_local_paths = [label for label in consumed_local_paths if label not in set(allowed_consumed_paths)]
    if not allowed_consumed_paths:
        raise RuntimeError("composition_and_local_paths has no allowed consumed local paths")

    positive_graph, positive_handles = build_allowed_path_graph(rx, allowed_consumed_paths)
    positive_observable = graph_observable(rx, positive_graph, positive_handles)

    reassoc_graph, reassoc_handles, reassoc_groups = build_implicit_reassociation_graph(rx, allowed_consumed_paths)
    reassoc_observable = graph_observable(rx, reassoc_graph, reassoc_handles)

    erasure_graph, erasure_handles = build_carrier_erasure_graph(rx)
    erasure_observable = graph_observable(rx, erasure_graph, erasure_handles)

    cycle_graph, cycle_handles = build_cycle_control_graph(rx, allowed_consumed_paths)
    cycle_observable = graph_observable(rx, cycle_graph, cycle_handles)

    gate_eligible = gate_payload.get("eligible_consumers") or []
    gate_blocked = gate_payload.get("blocked_consumers") or gate_payload.get("blocked_downstream_consumers") or []
    wave_a_rustworkx = next(
        (
            row
            for row in wave_a_payload.get("probes", [])
            if isinstance(row, dict) and row.get("tool") == "rustworkx"
        ),
        {},
    )
    carrier_erasure_control = (mc_payload.get("negative_controls") or {}).get("carrier_erasure") or {}

    finite_input_object = {
        "field": "composition_and_local_paths",
        "tool": "rustworkx",
        "api_surface": "PyDiGraph, add_node/add_edge, topological_sort, is_directed_acyclic_graph, transitive_reduction, has_path",
        "consumed_local_paths": consumed_local_paths,
        "consumed_allowed_paths": consumed_allowed_paths,
        "consumed_forbidden_controls": consumed_forbidden,
        "allowed_consumed_path_nodes": allowed_consumed_paths,
        "excluded_local_paths_not_encoded_as_allowed_nodes": excluded_local_paths,
        "order_sensitive_required_pair": ["Z_then_X", "X_then_Z"],
    }
    output_object = {
        "positive_graph": positive_observable,
        "implicit_reassociation_control_graph": {
            "collapsed_groups": {key: sorted(value) for key, value in sorted(reassoc_groups.items())},
            "observable": reassoc_observable,
        },
        "carrier_erasure_control_graph": erasure_observable,
        "cycle_failure_control_graph": cycle_observable,
        "observable": "finite directed graph observables over consumed composition_and_local_paths labels",
    }
    positive = {
        "consumed_composition_field_present": check(
            "consumed_composition_field_present",
            isinstance(composition, dict) and bool(composition),
            expected=True,
            observed=bool(composition),
            reason="The probe must consume the explicit M(C) v1 composition_and_local_paths field.",
        ),
        "allowed_consumed_paths_represented": check(
            "allowed_consumed_paths_represented",
            positive_observable["represented_allowed_paths"] == sorted(allowed_consumed_paths)
            and all(
                row["input_reaches_path"] is True and row["path_reaches_output"] is True
                for row in positive_observable["path_reachability"].values()
            ),
            expected=sorted(allowed_consumed_paths),
            observed={
                "represented": positive_observable["represented_allowed_paths"],
                "path_reachability": positive_observable["path_reachability"],
            },
            reason="Every allowed consumed order-sensitive local path must be a finite rustworkx node with input and output edges.",
        ),
        "positive_graph_is_dag": check(
            "positive_graph_is_dag",
            positive_observable["is_dag"] is True and positive_observable["topological_sort_success"] is True,
            expected={"is_dag": True, "topological_sort_success": True},
            observed={
                "is_dag": positive_observable["is_dag"],
                "topological_sort_success": positive_observable["topological_sort_success"],
                "topological_error": positive_observable["topological_error"],
            },
            reason="The positive fixture must have an executable rustworkx DAG/topological-order observable.",
        ),
        "z_then_x_and_x_then_z_distinct": check(
            "z_then_x_and_x_then_z_distinct",
            set(["Z_then_X", "X_then_Z"]) <= set(positive_observable["represented_allowed_paths"])
            and positive_observable["distinct_order_sensitive_pair_key_count"] == 2,
            expected={"represented_pair": ["Z_then_X", "X_then_Z"], "distinct_order_keys": 2},
            observed=positive_observable["order_sensitive_pair_keys"],
            reason="The graph must preserve local ordering so Z_then_X and X_then_Z do not collapse to one node/key.",
        ),
        "positive_reachability_load_bearing": check(
            "positive_reachability_load_bearing",
            positive_observable["input_reaches_output"] is True
            and len(positive_observable["transitive_reduction_edges"]) == positive_observable["edge_count"],
            expected={"input_reaches_output": True, "reduction_edges_equal_positive_edges": True},
            observed={
                "input_reaches_output": positive_observable["input_reaches_output"],
                "edge_count": positive_observable["edge_count"],
                "transitive_reduction_edge_count": len(positive_observable["transitive_reduction_edges"]),
            },
            reason="rustworkx path reachability and reduction readouts must observe the finite carrier rather than a decorative import.",
        ),
    }
    negative = {
        "implicit_reassociation_control_flips": check(
            "implicit_reassociation_control_flips",
            "implicit_reassociation" in consumed_forbidden
            and reassoc_observable["observable_digest"] != positive_observable["observable_digest"]
            and reassoc_observable["distinct_order_sensitive_pair_key_count"] < 2
            and any(set(labels) >= {"Z_then_X", "X_then_Z"} for labels in reassoc_groups.values()),
            expected="forbidden collapse changes graph observable and collapses the order-sensitive pair",
            observed={
                "forbidden_present": "implicit_reassociation" in consumed_forbidden,
                "positive_digest": positive_observable["observable_digest"],
                "control_digest": reassoc_observable["observable_digest"],
                "control_pair_keys": reassoc_observable["order_sensitive_pair_keys"],
                "collapsed_groups": {key: sorted(value) for key, value in sorted(reassoc_groups.items())},
            },
            reason="The implicit_reassociation control encodes the forbidden order-erasing collapse and changes the rustworkx observable.",
        ),
        "carrier_erasure_control_flips": check(
            "carrier_erasure_control_flips",
            "carrier_erasure" in consumed_forbidden
            and erasure_observable["observable_digest"] != positive_observable["observable_digest"]
            and erasure_observable["represented_allowed_paths"] == []
            and carrier_erasure_control.get("all_engines_flip") is True,
            expected="path-node erasure changes observable and removes allowed path nodes",
            observed={
                "forbidden_present": "carrier_erasure" in consumed_forbidden,
                "positive_digest": positive_observable["observable_digest"],
                "control_digest": erasure_observable["observable_digest"],
                "represented_allowed_paths": erasure_observable["represented_allowed_paths"],
                "consumed_v1_carrier_erasure_all_engines_flip": carrier_erasure_control.get("all_engines_flip"),
            },
            reason="Removing local path labels/path nodes demotes the carrier and makes rustworkx load-bearing.",
        ),
        "cycle_control_blocks_topological_sort": check(
            "cycle_control_blocks_topological_sort",
            cycle_observable["is_dag"] is False and cycle_observable["topological_sort_success"] is False,
            expected={"is_dag": False, "topological_sort_success": False},
            observed={
                "is_dag": cycle_observable["is_dag"],
                "topological_sort_success": cycle_observable["topological_sort_success"],
                "topological_error": cycle_observable["topological_error"],
            },
            reason="The requested DAG failure surface must be live: a forbidden cycle blocks topological sorting.",
        ),
    }
    boundary = {
        "consumer_gate_all_pass": check(
            "consumer_gate_all_pass",
            gate_payload.get("all_pass") is True,
            expected=True,
            observed=gate_payload.get("all_pass"),
            reason="This tool-lego fit probe is only allowed after the consumer gate passes.",
        ),
        "allowed_consumer_present": check(
            "allowed_consumer_present",
            "exact_tool_lego_fit_probe_after_consumer_gate" in gate_eligible,
            expected="exact_tool_lego_fit_probe_after_consumer_gate",
            observed=gate_eligible,
            reason="The consumer gate must explicitly allow this exact fit-probe shape.",
        ),
        "strong_consumers_still_exactly_blocked": check(
            "strong_consumers_still_exactly_blocked",
            gate_blocked == STRONG_CONSUMERS,
            expected=STRONG_CONSUMERS,
            observed=gate_blocked,
            reason="The consumer gate must keep every strong downstream consumer blocked and add no new eligible strong use.",
        ),
        "stage_movement_forbidden": check(
            "stage_movement_forbidden",
            gate_payload.get("stage_movement_allowed") is False and gate_payload.get("stage4_unlock_allowed") is False,
            expected={"stage_movement_allowed": False, "stage4_unlock_allowed": False},
            observed={
                "stage_movement_allowed": gate_payload.get("stage_movement_allowed"),
                "stage4_unlock_allowed": gate_payload.get("stage4_unlock_allowed"),
            },
            reason="This probe must not move the ladder stage or unlock Stage 4.",
        ),
        "promotion_and_formal_admission_forbidden": check(
            "promotion_and_formal_admission_forbidden",
            promotion_allowed is False and formal_admission_allowed is False,
            expected={"promotion_allowed": False, "formal_admission_allowed": False},
            observed={"promotion_allowed": promotion_allowed, "formal_admission_allowed": formal_admission_allowed},
            reason="The result must stay pre-lego fit evidence only.",
        ),
        "wave_a_rustworkx_capability_available": check(
            "wave_a_rustworkx_capability_available",
            wave_a_payload.get("all_pass") is True
            and wave_a_rustworkx.get("pass") is True
            and wave_a_rustworkx.get("tool") == "rustworkx",
            expected={"wave_a_all_pass": True, "rustworkx_probe_pass": True},
            observed={
                "wave_a_all_pass": wave_a_payload.get("all_pass"),
                "rustworkx_probe": {
                    "tool": wave_a_rustworkx.get("tool"),
                    "probe_id": wave_a_rustworkx.get("probe_id"),
                    "pass": wave_a_rustworkx.get("pass"),
                },
            },
            reason="Wave A is consumed only as local no-install rustworkx capability evidence.",
        ),
        "prior_cvc5_probe_accepted_as_prior_fit_only": check(
            "prior_cvc5_probe_accepted_as_prior_fit_only",
            prior_cvc5_payload.get("all_pass") is True
            and prior_cvc5_payload.get("classification") == "tool_lego_fit_probe"
            and prior_cvc5_payload.get("stage_movement_allowed") is False,
            expected={"all_pass": True, "classification": "tool_lego_fit_probe", "stage_movement_allowed": False},
            observed={
                "all_pass": prior_cvc5_payload.get("all_pass"),
                "classification": prior_cvc5_payload.get("classification"),
                "stage_movement_allowed": prior_cvc5_payload.get("stage_movement_allowed"),
            },
            reason="The prior cvc5 quotient fit receipt is only sibling shakedown evidence, not M(C) admission.",
        ),
    }
    return {
        "finite_carrier_input_object": finite_input_object,
        "output_object": output_object,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }


def write_blocked_reason(reason: str, error: str) -> None:
    payload = {
        "kind": "blocked_reason",
        "created_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "scope": OBJECT_ID,
        "reason": reason,
        "error": error,
        "next_admissible_step": (
            "Rerun this exact source after the sim-stack rustworkx PyDiGraph/DAG API "
            "is importable and usable; do not install packages in this bounded lane."
        ),
        "recommended_next_move": "Keep M(C) v1 quarantined and do not move Stage 4.",
        "claim_ceiling": CLAIM_CEILING,
        "source_path": str(SOURCE_PATH),
        "intended_result_path": str(RESULT_PATH),
    }
    BLOCKED_REASON_PATH.parent.mkdir(parents=True, exist_ok=True)
    BLOCKED_REASON_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_result() -> dict[str, Any]:
    started_ns = time.perf_counter_ns()
    mc_payload, mc_load_error = load_json(MC_V1_RESULT_PATH)
    gate_payload, gate_load_error = load_json(CONSUMER_GATE_RESULT_PATH)
    wave_a_payload, wave_a_load_error = load_json(WAVE_A_RESULT_PATH)
    prior_cvc5_payload, prior_cvc5_load_error = load_json(PRIOR_CVC5_RESULT_PATH)

    mc_validation = validate_result_path(MC_V1_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True)
    gate_validation = validate_result_path(CONSUMER_GATE_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True)
    wave_a_validation = validate_result_path(WAVE_A_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True)
    prior_cvc5_validation = validate_result_path(PRIOR_CVC5_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True)

    probe = rustworkx_probe(mc_payload, gate_payload, wave_a_payload, prior_cvc5_payload)
    positive = probe["positive"]
    negative = probe["negative"]
    boundary = probe["boundary"]
    boundary.update(
        {
            "mc_v1_receipt_loaded": check(
                "mc_v1_receipt_loaded",
                mc_load_error is None,
                expected=None,
                observed=mc_load_error,
                reason="The M(C) v1 envelope result must be readable JSON.",
            ),
            "consumer_gate_receipt_loaded": check(
                "consumer_gate_receipt_loaded",
                gate_load_error is None,
                expected=None,
                observed=gate_load_error,
                reason="The consumer-gate result must be readable JSON.",
            ),
            "wave_a_receipt_loaded": check(
                "wave_a_receipt_loaded",
                wave_a_load_error is None,
                expected=None,
                observed=wave_a_load_error,
                reason="The Wave A tool-capability result must be readable JSON.",
            ),
            "prior_cvc5_receipt_loaded": check(
                "prior_cvc5_receipt_loaded",
                prior_cvc5_load_error is None,
                expected=None,
                observed=prior_cvc5_load_error,
                reason="The prior cvc5 tool-lego fit result must be readable JSON.",
            ),
            "mc_v1_receipt_validates": check(
                "mc_v1_receipt_validates",
                mc_validation.get("ok") is True,
                expected=True,
                observed=mc_validation.get("hard_findings"),
                reason="The consumed M(C) v1 envelope receipt must pass strict receipt validation.",
            ),
            "consumer_gate_receipt_validates": check(
                "consumer_gate_receipt_validates",
                gate_validation.get("ok") is True,
                expected=True,
                observed=gate_validation.get("hard_findings"),
                reason="The consumed consumer-gate receipt must pass strict receipt validation.",
            ),
            "wave_a_receipt_validates": check(
                "wave_a_receipt_validates",
                wave_a_validation.get("ok") is True,
                expected=True,
                observed=wave_a_validation.get("hard_findings"),
                reason="The consumed Wave A capability receipt must pass strict receipt validation.",
            ),
            "prior_cvc5_receipt_validates": check(
                "prior_cvc5_receipt_validates",
                prior_cvc5_validation.get("ok") is True,
                expected=True,
                observed=prior_cvc5_validation.get("hard_findings"),
                reason="The prior cvc5 tool-lego fit receipt must pass strict receipt validation.",
            ),
        }
    )
    all_pass = section_pass(positive) and section_pass(negative) and section_pass(boundary)
    result: dict[str, Any] = {
        "schema_version": "codex_ratchet.tool_lego_fit_probe.v1",
        "name": OBJECT_ID,
        "object_id": OBJECT_ID,
        "classification": classification,
        "evidence_level": evidence_level,
        "sim_execution_kind": sim_execution_kind,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "all_pass": all_pass,
        "pass": all_pass,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "elapsed_ns": time.perf_counter_ns() - started_ns,
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim": "rustworkx can carry a bounded finite composition_and_local_paths fixture for the exact M(C) v1 field after the consumer gate",
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": NEXT_LEGO_TARGET,
        "promotion_condition": PROMOTION_CONDITION,
        "blocked_until": BLOCKED_UNTIL,
        "demotion_condition": DEMOTION_CONDITION,
        "out_of_scope": OUT_OF_SCOPE,
        "stage_movement_allowed": False,
        "stage_after_probe": "unchanged",
        "stage4_unlock_allowed": False,
        "eligible_consumers": ELIGIBLE_CONSUMERS,
        "blocked_consumers": STRONG_CONSUMERS,
        "blocked_downstream_consumers": STRONG_CONSUMERS,
        "finite_carrier_input_object": probe["finite_carrier_input_object"],
        "output_object": probe["output_object"],
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "source_result_sha256s": {
            "probe_source_sha256": sha256_file(SOURCE_PATH),
            "consumed_mc_v1_result_path": str(MC_V1_RESULT_PATH),
            "consumed_mc_v1_result_sha256": sha256_file(MC_V1_RESULT_PATH),
            "consumed_mc_v1_source_sha256_claimed": mc_payload.get("source_sha256"),
            "consumer_gate_result_path": str(CONSUMER_GATE_RESULT_PATH),
            "consumer_gate_result_sha256": sha256_file(CONSUMER_GATE_RESULT_PATH),
            "consumer_gate_source_sha256_claimed": gate_payload.get("source_sha256"),
            "wave_a_result_path": str(WAVE_A_RESULT_PATH),
            "wave_a_result_sha256": sha256_file(WAVE_A_RESULT_PATH),
            "wave_a_source_sha256_claimed": wave_a_payload.get("source_sha256"),
            "prior_cvc5_result_path": str(PRIOR_CVC5_RESULT_PATH),
            "prior_cvc5_result_sha256": sha256_file(PRIOR_CVC5_RESULT_PATH),
            "prior_cvc5_source_sha256_claimed": prior_cvc5_payload.get("source_sha256"),
        },
        "receipt_schema_validation": {
            "mc_v1_envelope_strict": mc_validation,
            "consumer_gate_strict": gate_validation,
            "wave_a_strict": wave_a_validation,
            "prior_cvc5_strict": prior_cvc5_validation,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    result["result_payload_sha256_excluding_this_field"] = stable_sha256(result)
    return result


def main() -> int:
    try:
        result = build_result()
    except ImportError as exc:
        write_blocked_reason("rustworkx API is not importable in the sim-stack interpreter", str(exc))
        print(f"BLOCKED rustworkx_import error={exc}")
        return 2
    except Exception as exc:
        if "rustworkx" in traceback.format_exc().lower():
            write_blocked_reason("rustworkx API is not usable for the requested PyDiGraph/DAG surface", f"{type(exc).__name__}: {exc}")
            print(f"BLOCKED rustworkx_usable error={type(exc).__name__}: {exc}")
            return 2
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
