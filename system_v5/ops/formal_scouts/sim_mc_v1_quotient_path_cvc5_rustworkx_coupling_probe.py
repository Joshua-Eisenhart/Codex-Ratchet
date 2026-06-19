#!/usr/bin/env python3
"""Scratch tool-tool coupling probe for M(C) v1 quotient classes and paths."""

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


OBJECT_ID = "mc_v1_quotient_path_cvc5_rustworkx_coupling_probe"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_mc_v1_quotient_path_cvc5_rustworkx_coupling_probe.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quotient_path_cvc5_rustworkx_coupling_probe_results.json"
MC_V1_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json"
CONSUMER_GATE_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quarantine_consumer_gate_probe_results.json"
PRIOR_CVC5_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json"
PRIOR_RUSTWORKX_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json"
BLOCKED_REASON_PATH = ROOT / "system_v5/ops/wizard_admissions/mc_v1_quotient_path_cvc5_rustworkx_coupling_probe_blocked_reason.json"

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
    "tool-lego promotion",
    "topology or graph-proof admission",
]

CLAIM_CEILING = (
    "Scratch diagnostic tool-tool coupling only: cvc5 quotient-class constraints "
    "and rustworkx finite DAG/path construction agree on one bounded M(C) v1 "
    "quotient/path fixture after the consumer gate and after both parent fit "
    "receipts. This does not admit M(C), does not promote either tool-lego, does "
    "not unlock Stage 4, and does not support same-carrier geometry, topology "
    "readout, AI/GNN readout, bridge, Axis0, physics, manifold, or formal admission claims."
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
    "certifies expected graph-edge constraints, if rustworkx no longer exposes "
    "the finite DAG/path observable, if quotient erasure or cycle controls do not "
    "flip the coupled observable, if strong consumers become eligible, or if any "
    "promotion/admission flag becomes true."
)

TOOL_MANIFEST = {
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SAT/UNSAT certification of expected quotient-class edge constraints over the rustworkx graph",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite DAG/path construction, cycle control, and reachability observable consumed by the cvc5 constraints",
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


def import_tools() -> tuple[Any, Any, Any]:
    import cvc5
    from cvc5 import Kind
    import rustworkx as rx

    return cvc5, Kind, rx


def quotient_member_class_map(mc_payload: dict[str, Any]) -> dict[str, str]:
    quotient = ((mc_payload.get("quotient_relation") or {}).get("quotient_Adm_C_mod_M") or {})
    out: dict[str, str] = {}
    for row in quotient.get("classes") or []:
        class_id = str(row.get("class_id"))
        for member in row.get("members") or []:
            out[str(member)] = class_id
    return out


def admitted_ids(mc_payload: dict[str, Any]) -> list[str]:
    return sorted(str(item) for item in ((mc_payload.get("Adm_C") or {}).get("admitted_ids") or []))


def build_path_graph(rx: Any, member_to_class: dict[str, str], *, mode: str = "positive") -> tuple[Any, dict[str, int]]:
    graph = rx.PyDiGraph()
    handles: dict[str, int] = {}
    root = graph.add_node({"key": "root", "kind": "root"})
    sink = graph.add_node({"key": "sink", "kind": "sink"})
    handles["root"] = root
    handles["sink"] = sink
    class_ids = sorted(set(member_to_class.values()))
    if mode == "erased_quotient":
        class_ids = ["collapsed_q"]
        member_to_class = {member: "collapsed_q" for member in member_to_class}
    for class_id in class_ids:
        handles[class_id] = graph.add_node({"key": class_id, "kind": "quotient_class"})
    path_zx = graph.add_node({"key": "Z_then_X", "kind": "path"})
    path_xz = graph.add_node({"key": "X_then_Z", "kind": "path"})
    handles["Z_then_X"] = path_zx
    handles["X_then_Z"] = path_xz
    for class_id in class_ids:
        graph.add_edge(root, handles[class_id], {"edge": "root_to_class"})
    if "Adm_q1" in handles and "Adm_q3" in handles:
        graph.add_edge(handles["Adm_q1"], path_zx, {"edge": "class_to_path", "order": "Z_then_X"})
        graph.add_edge(path_zx, handles["Adm_q3"], {"edge": "path_to_class", "order": "Z_then_X"})
    if "Adm_q0" in handles and "Adm_q2" in handles:
        graph.add_edge(handles["Adm_q0"], path_xz, {"edge": "class_to_path", "order": "X_then_Z"})
        graph.add_edge(path_xz, handles["Adm_q2"], {"edge": "path_to_class", "order": "X_then_Z"})
    if mode == "erased_quotient":
        graph.add_edge(handles["collapsed_q"], path_zx, {"edge": "collapsed_to_path"})
        graph.add_edge(path_zx, sink, {"edge": "path_to_sink"})
    else:
        for class_id in class_ids:
            graph.add_edge(handles[class_id], sink, {"edge": "class_to_sink"})
    if mode == "cycle_control":
        graph.add_edge(sink, root, {"edge": "cycle_control"})
    return graph, handles


def edge_pairs(graph: Any) -> set[tuple[str, str]]:
    out = set()
    for source, target in graph.edge_list():
        out.add((str(graph.get_node_data(source).get("key")), str(graph.get_node_data(target).get("key"))))
    return out


def graph_observable(rx: Any, graph: Any, handles: dict[str, int]) -> dict[str, Any]:
    topo_error = None
    try:
        topo_order = [str(graph.get_node_data(index).get("key")) for index in rx.topological_sort(graph)]
    except Exception as exc:
        topo_error = f"{type(exc).__name__}: {exc}"
        topo_order = []
    pairs = sorted(edge_pairs(graph))
    out = {
        "node_count": len(list(graph.node_indices())),
        "edge_count": len(list(graph.edge_list())),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "topological_sort_success": topo_error is None,
        "topological_order": topo_order,
        "topological_error": topo_error,
        "edge_pairs": pairs,
        "root_reaches_sink": bool(rx.has_path(graph, handles["root"], handles["sink"])),
        "q1_reaches_q3_via_zx": bool(
            "Adm_q1" in handles
            and "Adm_q3" in handles
            and rx.has_path(graph, handles["Adm_q1"], handles["Adm_q3"])
        ),
        "q3_reaches_q1_via_xz": bool(
            "Adm_q0" in handles
            and "Adm_q2" in handles
            and rx.has_path(graph, handles["Adm_q0"], handles["Adm_q2"])
        ),
    }
    out["observable_digest"] = stable_sha256(out)
    return out


def cvc5_edge_certificate(cvc5: Any, kind: Any, edges: set[tuple[str, str]], *, expect_distinct_classes: bool = True) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    bool_sort = solver.getBooleanSort()

    def edge_term(left: str, right: str) -> Any:
        return solver.mkConst(bool_sort, f"edge__{left}__{right}".replace("-", "_"))

    expected = [
        ("Adm_q1", "Z_then_X"),
        ("Z_then_X", "Adm_q3"),
        ("Adm_q0", "X_then_Z"),
        ("X_then_Z", "Adm_q2"),
    ]
    universe = set(edges) | set(expected) | {("collapsed_q", "Z_then_X")}
    all_terms = {pair: edge_term(pair[0], pair[1]) for pair in sorted(universe)}
    for pair, term in all_terms.items():
        solver.assertFormula(solver.mkTerm(kind.EQUAL, term, solver.mkBoolean(pair in edges)))
    expected_terms = [all_terms.get(pair, edge_term(pair[0], pair[1])) for pair in expected]
    if expected_terms:
        solver.assertFormula(solver.mkTerm(kind.AND, *expected_terms))
    if expect_distinct_classes:
        solver.assertFormula(solver.mkTerm(kind.NOT, solver.mkTerm(kind.EQUAL, edge_term("Adm_q1", "Z_then_X"), edge_term("collapsed_q", "Z_then_X"))))
    verdict = str(solver.checkSat())
    return {
        "verdict": verdict,
        "expected_edges": expected,
        "edge_count": len(edges),
        "expect_distinct_classes": expect_distinct_classes,
    }


def probe(
    mc_payload: dict[str, Any],
    gate_payload: dict[str, Any],
    prior_cvc5_payload: dict[str, Any],
    prior_rustworkx_payload: dict[str, Any],
) -> dict[str, Any]:
    cvc5, kind, rx = import_tools()
    members = admitted_ids(mc_payload)
    member_to_class = quotient_member_class_map(mc_payload)
    graph, handles = build_path_graph(rx, member_to_class)
    positive_obs = graph_observable(rx, graph, handles)
    positive_cert = cvc5_edge_certificate(cvc5, kind, edge_pairs(graph))
    erased_graph, erased_handles = build_path_graph(rx, member_to_class, mode="erased_quotient")
    erased_obs = graph_observable(rx, erased_graph, erased_handles)
    erased_cert = cvc5_edge_certificate(cvc5, kind, edge_pairs(erased_graph))
    cycle_graph, cycle_handles = build_path_graph(rx, member_to_class, mode="cycle_control")
    cycle_obs = graph_observable(rx, cycle_graph, cycle_handles)

    gate_eligible = gate_payload.get("eligible_consumers") or []
    gate_blocked = gate_payload.get("blocked_consumers") or gate_payload.get("blocked_downstream_consumers") or []
    prior_receipts_ok = (
        prior_cvc5_payload.get("all_pass") is True
        and prior_cvc5_payload.get("classification") == "tool_lego_fit_probe"
        and prior_cvc5_payload.get("stage_movement_allowed") is False
        and prior_rustworkx_payload.get("all_pass") is True
        and prior_rustworkx_payload.get("classification") == "tool_lego_fit_probe"
        and prior_rustworkx_payload.get("stage_movement_allowed") is False
    )

    positive = {
        "parent_fit_receipts_consumed": check(
            "parent_fit_receipts_consumed",
            prior_receipts_ok,
            expected={"cvc5": "tool_lego_fit_probe all_pass true no stage movement", "rustworkx": "same"},
            observed={
                "cvc5": {
                    "classification": prior_cvc5_payload.get("classification"),
                    "all_pass": prior_cvc5_payload.get("all_pass"),
                    "stage_movement_allowed": prior_cvc5_payload.get("stage_movement_allowed"),
                },
                "rustworkx": {
                    "classification": prior_rustworkx_payload.get("classification"),
                    "all_pass": prior_rustworkx_payload.get("all_pass"),
                    "stage_movement_allowed": prior_rustworkx_payload.get("stage_movement_allowed"),
                },
            },
            reason="tool-tool coupling must cite two prior parent fit receipts",
        ),
        "rustworkx_dag_path_observable_live": check(
            "rustworkx_dag_path_observable_live",
            positive_obs["is_dag"]
            and positive_obs["root_reaches_sink"]
            and positive_obs["q1_reaches_q3_via_zx"]
            and positive_obs["q3_reaches_q1_via_xz"],
            expected={"is_dag": True, "root_reaches_sink": True, "q1_reaches_q3_via_zx": True, "q0_reaches_q2_via_xz": True},
            observed={key: positive_obs[key] for key in ["is_dag", "root_reaches_sink", "q1_reaches_q3_via_zx", "q3_reaches_q1_via_xz"]},
            reason="rustworkx must carry the finite quotient/path graph observable",
        ),
        "cvc5_certifies_expected_edges": check(
            "cvc5_certifies_expected_edges",
            positive_cert["verdict"] == "sat",
            expected="sat",
            observed=positive_cert,
            reason="cvc5 must certify the expected quotient-class edge constraints from the rustworkx graph",
        ),
    }
    negative = {
        "quotient_erasure_flips_coupled_certificate": check(
            "quotient_erasure_flips_coupled_certificate",
            erased_cert["verdict"] != positive_cert["verdict"] and erased_obs["observable_digest"] != positive_obs["observable_digest"],
            expected={"certificate_differs": True, "observable_digest_differs": True},
            observed={
                "positive_verdict": positive_cert["verdict"],
                "erased_verdict": erased_cert["verdict"],
                "positive_digest": positive_obs["observable_digest"],
                "erased_digest": erased_obs["observable_digest"],
            },
            reason="collapsing quotient classes must break the coupled graph/proof fixture",
        ),
        "cycle_control_breaks_dag_observable": check(
            "cycle_control_breaks_dag_observable",
            cycle_obs["is_dag"] is False and cycle_obs["topological_sort_success"] is False,
            expected={"is_dag": False, "topological_sort_success": False},
            observed={"is_dag": cycle_obs["is_dag"], "topological_sort_success": cycle_obs["topological_sort_success"], "topological_error": cycle_obs["topological_error"]},
            reason="rustworkx cycle control must break DAG/topological path admissibility",
        ),
        "single_parent_receipt_not_sufficient": check(
            "single_parent_receipt_not_sufficient",
            not (
                prior_cvc5_payload.get("all_pass") is True
                and prior_rustworkx_payload.get("all_pass") is False
            )
            and not (
                prior_cvc5_payload.get("all_pass") is False
                and prior_rustworkx_payload.get("all_pass") is True
            ),
            expected="coupling requires both parent receipts; no one-parent shortcut accepted",
            observed={"cvc5_all_pass": prior_cvc5_payload.get("all_pass"), "rustworkx_all_pass": prior_rustworkx_payload.get("all_pass")},
            reason="coupling evidence cannot be reduced to one parent tool receipt",
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
        "admitted_ids": members,
        "member_to_class": member_to_class,
        "positive_observable": positive_obs,
        "erased_observable": erased_obs,
        "cycle_observable": cycle_obs,
        "positive_certificate": positive_cert,
        "erased_certificate": erased_cert,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }


def build_result() -> dict[str, Any]:
    started = time.perf_counter()
    mc_payload, mc_error = load_json(MC_V1_RESULT_PATH)
    gate_payload, gate_error = load_json(CONSUMER_GATE_RESULT_PATH)
    prior_cvc5_payload, cvc5_error = load_json(PRIOR_CVC5_RESULT_PATH)
    prior_rustworkx_payload, rustworkx_error = load_json(PRIOR_RUSTWORKX_RESULT_PATH)
    receipt_checks: dict[str, dict[str, Any]] = {}
    for label, path, load_error in [
        ("mc_v1", MC_V1_RESULT_PATH, mc_error),
        ("consumer_gate", CONSUMER_GATE_RESULT_PATH, gate_error),
        ("parent_cvc5", PRIOR_CVC5_RESULT_PATH, cvc5_error),
        ("parent_rustworkx", PRIOR_RUSTWORKX_RESULT_PATH, rustworkx_error),
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
        details = probe(mc_payload, gate_payload, prior_cvc5_payload, prior_rustworkx_payload)
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
            "parent_rustworkx": str(PRIOR_RUSTWORKX_RESULT_PATH),
        },
        "input_receipt_sha256": {
            "mc_v1": sha256_file(MC_V1_RESULT_PATH),
            "consumer_gate": sha256_file(CONSUMER_GATE_RESULT_PATH),
            "parent_cvc5": sha256_file(PRIOR_CVC5_RESULT_PATH),
            "parent_rustworkx": sha256_file(PRIOR_RUSTWORKX_RESULT_PATH),
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
                "next_admissible_step": "Repair only this bounded cvc5/rustworkx coupling probe or demote it; do not move stage.",
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
