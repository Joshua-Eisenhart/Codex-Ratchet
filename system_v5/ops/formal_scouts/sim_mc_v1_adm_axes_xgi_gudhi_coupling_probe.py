#!/usr/bin/env python3
"""Scratch tool-tool coupling probe for M(C) v1 Adm_C hyperedges and axes filtration."""

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


OBJECT_ID = "mc_v1_adm_axes_xgi_gudhi_coupling_probe"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_mc_v1_adm_axes_xgi_gudhi_coupling_probe.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_adm_axes_xgi_gudhi_coupling_probe_results.json"
MC_V1_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json"
CONSUMER_GATE_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quarantine_consumer_gate_probe_results.json"
PRIOR_XGI_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json"
PRIOR_GUDHI_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_axes_gudhi_tool_lego_fit_probe_results.json"
BLOCKED_REASON_PATH = ROOT / "system_v5/ops/wizard_admissions/mc_v1_adm_axes_xgi_gudhi_coupling_probe_blocked_reason.json"

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
stage_movement_allowed = False
STAGE_MOVEMENT_ALLOWED = stage_movement_allowed
stage4_unlock_allowed = False
STAGE4_UNLOCK_ALLOWED = stage4_unlock_allowed
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
    "constraint_set_C promotion",
    "axes_A_i promotion",
    "topological invariant or geometry claim",
]

CLAIM_CEILING = (
    "Scratch diagnostic tool-tool coupling only: XGI admitted-record hyperedges "
    "and GUDHI finite axes filtrations can be checked against the same admitted "
    "M(C) v1 records after both parent fit receipts. This does not admit M(C), "
    "does not promote either tool-lego, does not unlock Stage 4, and does not "
    "support same-carrier geometry, topology readout, AI/GNN readout, bridge, "
    "Axis0, physics, manifold, or formal admission claims."
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
    "Demote if either parent fit receipt fails validation, if XGI no longer emits "
    "finite admitted-record hyperedges with predicate/status/bracketing/rho/axes "
    "members, if GUDHI no longer emits a nontrivial filtration over the same "
    "admitted records, if status-only projection, axis erasure, label shuffle, "
    "or empty/degenerate controls do not change or demote the coupled observable, "
    "if strong consumers become eligible, or if any promotion/admission flag becomes true."
)

TOOL_MANIFEST = {
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Hypergraph admitted-record edges, edge member views, and incidence shape for the finite Adm_C plus axes fixture",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SimplexTree insertion, filtration ordering, and compute_persistence readout over the same admitted axes records",
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


def import_tools() -> tuple[Any, Any]:
    import gudhi
    import xgi

    return xgi, gudhi


def finite_value(value: float) -> str | float:
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return round(float(value), 12)


def support_by_id(mc_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id")): row
        for row in ((mc_payload.get("support_S") or {}).get("elements") or [])
        if isinstance(row, dict) and row.get("id")
    }


def admitted_rows(mc_payload: dict[str, Any]) -> list[dict[str, Any]]:
    support = support_by_id(mc_payload)
    axes = mc_payload.get("axes_A_i") or {}
    entropy = axes.get("A_entropy_bits") or {}
    order_gap = axes.get("A_order_gap") or {}
    associator = axes.get("A_associator_norm") or {}
    rows = []
    for record_id in sorted(str(item) for item in ((mc_payload.get("Adm_C") or {}).get("admitted_ids") or [])):
        row = support.get(record_id) or {}
        rows.append(
            {
                "id": record_id,
                "predicate": "Adm_C",
                "bracketing": str(row.get("bracketing") or "unknown"),
                "rho_key": str(row.get("rho_key") or "unknown"),
                "entropy": float(entropy.get(record_id, 0.0)),
                "order_gap": float(order_gap.get(record_id, 0.0)),
                "associator": float(associator.get(record_id, 0.0)),
                "has_axes": record_id in entropy and record_id in order_gap and record_id in associator,
            }
        )
    return rows


def edge_members(hypergraph: Any) -> dict[str, list[str]]:
    return {
        str(edge): sorted(str(node) for node in hypergraph.edges.members(edge))
        for edge in hypergraph.edges
    }


def build_hypergraph(xgi: Any, rows: list[dict[str, Any]], *, scalar_status: bool = False, empty: bool = False) -> tuple[Any, dict[str, list[str]]]:
    hypergraph = xgi.Hypergraph()
    if empty:
        return hypergraph, {}
    for row in rows:
        if scalar_status:
            members = [f"record/{row['id']}", "status/admitted"]
        else:
            members = [
                f"record/{row['id']}",
                "predicate/Adm_C",
                f"bracket/{row['bracketing']}",
                f"rho/{row['rho_key']}",
                f"axis_entropy/{finite_value(row['entropy'])}",
                f"axis_order/{finite_value(row['order_gap'])}",
                f"axis_associator/{finite_value(row['associator'])}",
                "status/admitted",
            ]
        hypergraph.add_edge(members, idx=f"adm-axis/{row['id']}")
    return hypergraph, edge_members(hypergraph)


def hypergraph_observable(xgi: Any, hypergraph: Any, members: dict[str, list[str]]) -> dict[str, Any]:
    edge_ids = list(hypergraph.edges)
    node_ids = sorted(str(node) for node in hypergraph.nodes)
    shape = [0, 0] if not edge_ids else [int(value) for value in xgi.incidence_matrix(hypergraph).shape]
    out = {
        "node_count": len(node_ids),
        "edge_count": len(edge_ids),
        "edge_member_sizes": {edge: len(nodes) for edge, nodes in sorted(members.items())},
        "edge_members": members,
        "incidence_shape": shape,
        "record_nodes": sorted(node for node in node_ids if node.startswith("record/")),
        "axis_nodes": sorted(node for node in node_ids if node.startswith("axis_")),
        "predicate_nodes": sorted(node for node in node_ids if node.startswith("predicate/")),
        "status_nodes": sorted(node for node in node_ids if node.startswith("status/")),
    }
    out["observable_digest"] = stable_sha256(out)
    return out


def build_filtration(gudhi: Any, rows: list[dict[str, Any]], *, mode: str = "positive") -> tuple[Any, dict[int, str]]:
    id_by_vertex = {index: row["id"] for index, row in enumerate(rows)}
    stree = gudhi.SimplexTree()
    for index, row in enumerate(rows):
        if mode == "axis_erased":
            base = 0.0
        elif mode == "label_shuffle":
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
            elif mode == "label_shuffle":
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


def probe(
    mc_payload: dict[str, Any],
    gate_payload: dict[str, Any],
    prior_xgi_payload: dict[str, Any],
    prior_gudhi_payload: dict[str, Any],
) -> dict[str, Any]:
    xgi, gudhi = import_tools()
    rows = admitted_rows(mc_payload)

    hypergraph, members = build_hypergraph(xgi, rows)
    hypergraph_obs = hypergraph_observable(xgi, hypergraph, members)
    tree, id_by_vertex = build_filtration(gudhi, rows)
    filtration_obs = filtration_observable(tree, id_by_vertex)

    scalar_graph, scalar_members = build_hypergraph(xgi, rows, scalar_status=True)
    scalar_obs = hypergraph_observable(xgi, scalar_graph, scalar_members)
    empty_graph, empty_members = build_hypergraph(xgi, rows, empty=True)
    empty_obs = hypergraph_observable(xgi, empty_graph, empty_members)
    erased_tree, erased_id_by_vertex = build_filtration(gudhi, rows, mode="axis_erased")
    erased_obs = filtration_observable(erased_tree, erased_id_by_vertex)
    shuffled_tree, shuffled_id_by_vertex = build_filtration(gudhi, rows, mode="label_shuffle")
    shuffled_obs = filtration_observable(shuffled_tree, shuffled_id_by_vertex)
    degenerate_tree, degenerate_id_by_vertex = build_filtration(gudhi, rows, mode="degenerate")
    degenerate_obs = filtration_observable(degenerate_tree, degenerate_id_by_vertex)

    coupled_digest = stable_sha256({"xgi": hypergraph_obs["observable_digest"], "gudhi": filtration_obs["observable_digest"]})
    scalar_digest = stable_sha256({"xgi": scalar_obs["observable_digest"], "gudhi": filtration_obs["observable_digest"]})
    erased_digest = stable_sha256({"xgi": hypergraph_obs["observable_digest"], "gudhi": erased_obs["observable_digest"]})
    empty_degenerate_digest = stable_sha256({"xgi": empty_obs["observable_digest"], "gudhi": degenerate_obs["observable_digest"]})

    gate_eligible = gate_payload.get("eligible_consumers") or []
    gate_blocked = gate_payload.get("blocked_consumers") or gate_payload.get("blocked_downstream_consumers") or []
    prior_receipts_ok = (
        prior_xgi_payload.get("all_pass") is True
        and prior_xgi_payload.get("classification") == "tool_lego_fit_probe"
        and prior_xgi_payload.get("stage_movement_allowed") is False
        and prior_gudhi_payload.get("all_pass") is True
        and prior_gudhi_payload.get("classification") == "tool_lego_fit_probe"
        and prior_gudhi_payload.get("stage_movement_allowed") is False
    )

    positive = {
        "parent_fit_receipts_consumed": check(
            "parent_fit_receipts_consumed",
            prior_receipts_ok,
            expected={"xgi": "tool_lego_fit_probe all_pass true no stage movement", "gudhi": "same"},
            observed={
                "xgi": {
                    "classification": prior_xgi_payload.get("classification"),
                    "all_pass": prior_xgi_payload.get("all_pass"),
                    "stage_movement_allowed": prior_xgi_payload.get("stage_movement_allowed"),
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
            and hypergraph_obs["record_nodes"] == sorted(f"record/{row['id']}" for row in rows)
            and filtration_obs["record_ids"] == [row["id"] for row in rows]
            and all(row["has_axes"] for row in rows),
            expected={"admitted_records": 4, "hypergraph_records_match": True, "filtration_records_match": True, "all_axes_present": True},
            observed={"rows": rows, "hypergraph_record_nodes": hypergraph_obs["record_nodes"], "filtration_record_ids": filtration_obs["record_ids"]},
            reason="XGI and GUDHI must operate on the same admitted records",
        ),
        "hypergraph_and_filtration_positive_claim_live": check(
            "hypergraph_and_filtration_positive_claim_live",
            hypergraph_obs["edge_count"] == 4
            and min(hypergraph_obs["edge_member_sizes"].values()) == 8
            and filtration_obs["num_simplices"] > filtration_obs["num_vertices"],
            expected={"xgi_edges": 4, "xgi_edge_member_size": 8, "gudhi_nontrivial_filtration": True},
            observed={"xgi": hypergraph_obs, "gudhi": filtration_obs},
            reason="XGI must carry admitted-record hyperedges while GUDHI carries the finite axes filtration",
        ),
    }
    negative = {
        "status_only_projection_changes_hypergraph_side": check(
            "status_only_projection_changes_hypergraph_side",
            scalar_obs["observable_digest"] != hypergraph_obs["observable_digest"]
            and scalar_digest != coupled_digest
            and max(scalar_obs["edge_member_sizes"].values()) == 2,
            expected={"xgi_digest_changes": True, "coupled_digest_changes": True, "status_only_rank": 2},
            observed={"positive_digest": coupled_digest, "scalar_digest": scalar_digest, "scalar_edge_member_sizes": scalar_obs["edge_member_sizes"]},
            reason="A status-only admitted-record projection must change the XGI side of the coupled observable",
        ),
        "axis_erasure_changes_filtration_side": check(
            "axis_erasure_changes_filtration_side",
            erased_obs["observable_digest"] != filtration_obs["observable_digest"]
            and erased_digest != coupled_digest
            and shuffled_obs["observable_digest"] != filtration_obs["observable_digest"],
            expected={"axis_erasure_changes": True, "coupled_digest_changes": True, "label_shuffle_changes": True},
            observed={"positive_digest": coupled_digest, "erased_digest": erased_digest, "shuffled_digest": shuffled_obs["observable_digest"]},
            reason="Erasing or shuffling axes must change the GUDHI side of the coupled observable",
        ),
        "empty_hypergraph_and_degenerate_filtration_demote": check(
            "empty_hypergraph_and_degenerate_filtration_demote",
            empty_obs["edge_count"] == 0
            and empty_obs["node_count"] == 0
            and degenerate_obs["num_simplices"] == degenerate_obs["num_vertices"]
            and empty_degenerate_digest != coupled_digest,
            expected={"empty_xgi": True, "vertices_only_filtration": True, "coupled_digest_changes": True},
            observed={"empty_xgi": empty_obs, "degenerate_gudhi": degenerate_obs, "positive_digest": coupled_digest, "empty_degenerate_digest": empty_degenerate_digest},
            reason="An empty hypergraph plus vertices-only filtration is demoted baseline/control evidence only",
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
            stage_movement_allowed is False and stage4_unlock_allowed is False,
            expected={"stage_movement_allowed": False, "stage4_unlock_allowed": False},
            observed={"stage_movement_allowed": stage_movement_allowed, "stage4_unlock_allowed": stage4_unlock_allowed},
            reason="this scratch coupling cannot move ladder stage",
        ),
    }
    return {
        "admitted_rows": rows,
        "xgi_observable": hypergraph_obs,
        "gudhi_observable": filtration_obs,
        "status_only_xgi_observable": scalar_obs,
        "axis_erased_gudhi_observable": erased_obs,
        "axis_shuffled_gudhi_observable": shuffled_obs,
        "empty_xgi_observable": empty_obs,
        "degenerate_gudhi_observable": degenerate_obs,
        "coupled_digest": coupled_digest,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }


def build_result() -> dict[str, Any]:
    started = time.perf_counter()
    mc_payload, mc_error = load_json(MC_V1_RESULT_PATH)
    gate_payload, gate_error = load_json(CONSUMER_GATE_RESULT_PATH)
    prior_xgi_payload, xgi_error = load_json(PRIOR_XGI_RESULT_PATH)
    prior_gudhi_payload, gudhi_error = load_json(PRIOR_GUDHI_RESULT_PATH)
    receipt_checks: dict[str, dict[str, Any]] = {}
    for label, path, load_error in [
        ("mc_v1", MC_V1_RESULT_PATH, mc_error),
        ("consumer_gate", CONSUMER_GATE_RESULT_PATH, gate_error),
        ("parent_xgi", PRIOR_XGI_RESULT_PATH, xgi_error),
        ("parent_gudhi", PRIOR_GUDHI_RESULT_PATH, gudhi_error),
    ]:
        validation = validate_result_path(path, root=ROOT, strict_scope=True, require_run_boundary=True)
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
        details = probe(mc_payload, gate_payload, prior_xgi_payload, prior_gudhi_payload)
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
            "parent_gudhi": str(PRIOR_GUDHI_RESULT_PATH),
        },
        "prior_receipts": [str(PRIOR_XGI_RESULT_PATH), str(PRIOR_GUDHI_RESULT_PATH)],
        "input_receipt_sha256": {
            "mc_v1": sha256_file(MC_V1_RESULT_PATH),
            "consumer_gate": sha256_file(CONSUMER_GATE_RESULT_PATH),
            "parent_xgi": sha256_file(PRIOR_XGI_RESULT_PATH),
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
        "stage_movement_allowed": stage_movement_allowed,
        "stage4_unlock_allowed": stage4_unlock_allowed,
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
                "next_admissible_step": "Repair only this bounded XGI/GUDHI coupling probe or demote it; do not move stage.",
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
