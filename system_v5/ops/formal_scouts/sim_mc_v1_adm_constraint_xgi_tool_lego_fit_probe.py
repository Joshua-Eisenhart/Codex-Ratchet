#!/usr/bin/env python3
"""xgi tool-lego fit probe for M(C) v1 admission/constraint incidence."""

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


OBJECT_ID = "mc_v1_adm_constraint_xgi_tool_lego_fit_probe"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_mc_v1_adm_constraint_xgi_tool_lego_fit_probe.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json"
MC_V1_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json"
CONSUMER_GATE_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quarantine_consumer_gate_probe_results.json"
WAVE_A_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/wave_a_cs_ai_no_install_micro_probes_results.json"
PRIOR_CVC5_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json"
PRIOR_RUSTWORKX_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json"
BLOCKED_REASON_PATH = ROOT / "system_v5/ops/wizard_admissions/mc_v1_adm_constraint_xgi_tool_lego_fit_probe_blocked_reason.json"

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

CONSTRAINT_DIMS = ["density_probe_C", "F01", "N01", "bracketing", "carrier"]
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
    "Adm_C promotion",
    "constraint_set_C promotion",
    "topology or geometry interpretation",
]

CLAIM_CEILING = (
    "Tool-lego fit probe only: xgi Hypergraph construction, edge member views, "
    "degree readouts, and incidence shape can carry one bounded finite Adm_C / "
    "constraint_set_C incidence fixture for M(C) v1 after the consumer gate. "
    "This does not admit M(C), does not unlock Stage 4, and does not support "
    "same-carrier geometry, topology readout, AI/GNN readout, bridge, Axis0, "
    "physics, manifold, or formal admission claims."
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
    "Demote if xgi cannot build the finite hypergraph, if the full five-constraint "
    "predicate does not reconstruct Adm_C.admitted_ids, if pairwise/scalar controls "
    "do not lose rejection-pattern information, if drop_F01/drop_N01 controls do not "
    "change the reconstructed pattern, if the consumer gate stops all_pass, if strong "
    "consumers become eligible, or if any promotion/admission flag becomes true."
)

TOOL_MANIFEST = {
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Hypergraph node/edge construction, edge member views, degree, and incidence shape for the finite Adm_C constraint-incidence fixture",
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


def import_xgi() -> Any:
    import xgi

    return xgi


def record_flags(record: dict[str, Any]) -> dict[str, bool]:
    flags = record.get("constraint_flags") or {}
    density = record.get("density") or {}
    return {
        "density_probe_C": bool(flags.get("density_probe_C")),
        "F01": bool(flags.get("F01")),
        "N01": bool(flags.get("N01")),
        "bracketing": bool(flags.get("bracketing")),
        "carrier": bool(flags.get("carrier")),
        "trace_eq_1": bool(density.get("trace_eq_1")),
        "psd": bool(density.get("psd")),
        "probe_bounds": bool(density.get("probe_bounds")),
    }


def full_predicate(flags: dict[str, bool], *, drop: str | None = None) -> bool:
    dims = [dim for dim in CONSTRAINT_DIMS if dim != drop]
    return all(flags.get(dim) is True for dim in dims)


def support_records(mc_payload: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {
        str(row.get("id")): row
        for row in ((mc_payload.get("support_S") or {}).get("elements") or [])
        if isinstance(row, dict) and row.get("id")
    }
    out = []
    for row in ((mc_payload.get("Adm_C") or {}).get("records") or []):
        if not isinstance(row, dict):
            continue
        sid = str(row.get("id"))
        merged = dict(by_id.get(sid, {}))
        merged.update(row)
        merged["id"] = sid
        merged["constraint_flags"] = record_flags(merged)
        merged["rejection_reasons"] = list(row.get("rejection_reasons") or merged.get("rejection_reasons") or [])
        merged["admitted"] = bool(row.get("admitted"))
        out.append(merged)
    return out


def build_xgi_hypergraph(xgi: Any, records: list[dict[str, Any]]) -> tuple[Any, dict[str, Any]]:
    hypergraph = xgi.Hypergraph()
    for dim in CONSTRAINT_DIMS:
        hypergraph.add_node(f"constraint/{dim}/pass")
        hypergraph.add_node(f"constraint/{dim}/fail")
    hypergraph.add_node("predicate/Adm_C/full-five")
    hypergraph.add_node("status/admitted")
    hypergraph.add_node("status/rejected")

    edge_ids = []
    for row in records:
        sid = row["id"]
        hypergraph.add_node(f"support/{sid}")
        members = [f"support/{sid}"]
        flags = row["constraint_flags"]
        for dim in CONSTRAINT_DIMS:
            members.append(f"constraint/{dim}/{'pass' if flags[dim] else 'fail'}")
        members.append("predicate/Adm_C/full-five")
        members.append("status/admitted" if row["admitted"] else "status/rejected")
        edge_id = f"record/{sid}/constraint-incidence"
        hypergraph.add_edge(members, idx=edge_id)
        edge_ids.append(edge_id)

    return hypergraph, {"edge_ids": edge_ids}


def edge_members(hypergraph: Any) -> dict[str, list[str]]:
    return {
        str(edge): sorted(str(node) for node in hypergraph.edges.members(edge))
        for edge in hypergraph.edges
    }


def incidence_shape(xgi: Any, hypergraph: Any) -> list[int]:
    shape = xgi.incidence_matrix(hypergraph).shape
    return [int(shape[0]), int(shape[1])]


def reconstruct_from_edges(members: dict[str, list[str]], *, drop: str | None = None) -> dict[str, Any]:
    admitted = []
    rejected_reasons = {}
    for edge_id, edge_nodes in members.items():
        sid = edge_id.split("/")[1]
        dim_values = {}
        reasons = []
        for dim in CONSTRAINT_DIMS:
            if f"constraint/{dim}/pass" in edge_nodes:
                dim_values[dim] = True
            elif f"constraint/{dim}/fail" in edge_nodes:
                dim_values[dim] = False
                reasons.append(dim)
            else:
                dim_values[dim] = False
                reasons.append(f"missing_{dim}")
        if full_predicate(dim_values, drop=drop):
            admitted.append(sid)
        else:
            rejected_reasons[sid] = reasons
    return {
        "admitted_ids": sorted(admitted),
        "rejected_reasons": {key: rejected_reasons[key] for key in sorted(rejected_reasons)},
        "drop": drop,
    }


def scalar_status_projection(records: list[dict[str, Any]]) -> dict[str, Any]:
    admitted = sorted(row["id"] for row in records if row["admitted"])
    rejected = sorted(row["id"] for row in records if not row["admitted"])
    return {
        "admitted_ids": admitted,
        "rejected_reasons": {sid: ["status_only"] for sid in rejected},
        "edge_count": len(records),
        "relation_rank": 2,
    }


def degenerate_hypergraph(xgi: Any, records: list[dict[str, Any]]) -> tuple[Any, dict[str, list[str]]]:
    hypergraph = xgi.Hypergraph()
    for row in records:
        sid = row["id"]
        status = "admitted" if row["admitted"] else "rejected"
        hypergraph.add_edge([f"support/{sid}", f"status/{status}"], idx=f"status/{sid}")
    return hypergraph, edge_members(hypergraph)


def xgi_observable(xgi: Any, hypergraph: Any, members: dict[str, list[str]]) -> dict[str, Any]:
    degree_samples = {
        node: int(hypergraph.degree(node))
        for node in sorted(hypergraph.nodes)
        if node.startswith("constraint/") or node in {"status/admitted", "status/rejected", "predicate/Adm_C/full-five"}
    }
    out = {
        "node_count": len(list(hypergraph.nodes)),
        "edge_count": len(list(hypergraph.edges)),
        "edge_member_sizes": {edge: len(nodes) for edge, nodes in sorted(members.items())},
        "edge_members": members,
        "incidence_shape": incidence_shape(xgi, hypergraph),
        "degree_samples": degree_samples,
    }
    out["observable_digest"] = stable_sha256(out)
    return out


def xgi_probe(
    mc_payload: dict[str, Any],
    gate_payload: dict[str, Any],
    wave_a_payload: dict[str, Any],
    prior_cvc5_payload: dict[str, Any],
    prior_rustworkx_payload: dict[str, Any],
) -> dict[str, Any]:
    xgi = import_xgi()
    records = support_records(mc_payload)
    adm_c = mc_payload.get("Adm_C") or {}
    constraint_set = mc_payload.get("constraint_set_C") or {}
    expected_admitted = sorted(str(item) for item in (adm_c.get("admitted_ids") or []))
    expected_rejections = {
        str(row.get("id")): list(row.get("rejection_reasons") or [])
        for row in (adm_c.get("records") or [])
        if isinstance(row, dict) and row.get("admitted") is False
    }

    hypergraph, handles = build_xgi_hypergraph(xgi, records)
    members = edge_members(hypergraph)
    observable = xgi_observable(xgi, hypergraph, members)
    reconstructed = reconstruct_from_edges(members)
    pairwise_projection = scalar_status_projection(records)
    degenerate_graph, degenerate_members = degenerate_hypergraph(xgi, records)
    degenerate_observable = xgi_observable(xgi, degenerate_graph, degenerate_members)
    drop_f01 = reconstruct_from_edges(members, drop="F01")
    drop_n01 = reconstruct_from_edges(members, drop="N01")

    gate_eligible = gate_payload.get("eligible_consumers") or []
    gate_blocked = gate_payload.get("blocked_consumers") or gate_payload.get("blocked_downstream_consumers") or []
    wave_a_xgi = next(
        (row for row in wave_a_payload.get("probes", []) if isinstance(row, dict) and row.get("tool") == "xgi"),
        {},
    )
    negative_controls = mc_payload.get("negative_controls") or {}

    positive = {
        "consumed_adm_c_and_constraint_set": check(
            "consumed_adm_c_and_constraint_set",
            bool(records) and bool(constraint_set) and bool(adm_c),
            expected={"records": 9, "constraint_set_present": True},
            observed={"records": len(records), "constraint_set_keys": sorted(constraint_set)},
            reason="The probe must consume M(C) v1 Adm_C.records and constraint_set_C.",
        ),
        "finite_hypergraph_represents_all_support_records": check(
            "finite_hypergraph_represents_all_support_records",
            len(records) == 9 and observable["edge_count"] == 9 and all(size == 8 for size in observable["edge_member_sizes"].values()),
            expected={"support_records": 9, "record_edges": 9, "edge_member_size": 8},
            observed={
                "support_records": len(records),
                "edge_count": observable["edge_count"],
                "edge_member_sizes": observable["edge_member_sizes"],
                "incidence_shape": observable["incidence_shape"],
            },
            reason="Each support record must be a finite xgi hyperedge containing support id, five constraints, predicate node, and status node.",
        ),
        "adm_c_reconstructed_from_full_hyperedges": check(
            "adm_c_reconstructed_from_full_hyperedges",
            reconstructed["admitted_ids"] == expected_admitted,
            expected=expected_admitted,
            observed=reconstructed["admitted_ids"],
            reason="The admitted set must be reconstructed from the five-constraint hyperedge relation, not copied from a scalar label.",
        ),
        "full_predicate_is_rank_seven_relation": check(
            "full_predicate_is_rank_seven_relation",
            min(observable["edge_member_sizes"].values()) == 8
            and observable["degree_samples"].get("predicate/Adm_C/full-five") == 9,
            expected={"min_edge_member_size": 8, "predicate_degree": 9},
            observed={
                "min_edge_member_size": min(observable["edge_member_sizes"].values()),
                "predicate_degree": observable["degree_samples"].get("predicate/Adm_C/full-five"),
            },
            reason="The full predicate is represented by multi-node hyperedges over support, five constraints, predicate, and status.",
        ),
    }
    negative = {
        "pairwise_status_projection_loses_rejection_pattern": check(
            "pairwise_status_projection_loses_rejection_pattern",
            pairwise_projection["admitted_ids"] == expected_admitted
            and pairwise_projection["rejected_reasons"] != expected_rejections
            and stable_sha256(pairwise_projection) != observable["observable_digest"],
            expected="same admitted set but lost rejected-reason pattern and changed observable",
            observed={
                "projection_admitted_ids": pairwise_projection["admitted_ids"],
                "projection_rejected_reasons": pairwise_projection["rejected_reasons"],
                "expected_rejected_reasons": expected_rejections,
                "projection_digest": stable_sha256(pairwise_projection),
                "hypergraph_digest": observable["observable_digest"],
            },
            reason="A scalar admitted/rejected pairwise projection can preserve the admitted set while losing why rejected records failed.",
        ),
        "drop_f01_control_changes_pattern": check(
            "drop_f01_control_changes_pattern",
            drop_f01["admitted_ids"] != reconstructed["admitted_ids"]
            and (negative_controls.get("drop_F01") or {}).get("all_engines_flip") is True,
            expected="dropping F01 changes reconstructed admission pattern",
            observed={
                "full": reconstructed["admitted_ids"],
                "drop_F01": drop_f01["admitted_ids"],
                "mc_v1_drop_F01_all_engines_flip": (negative_controls.get("drop_F01") or {}).get("all_engines_flip"),
            },
            reason="The F01 dimension is load-bearing in the incidence relation and matches the M(C) v1 control flip.",
        ),
        "drop_n01_control_changes_pattern": check(
            "drop_n01_control_changes_pattern",
            drop_n01["admitted_ids"] != reconstructed["admitted_ids"]
            and (negative_controls.get("drop_N01") or {}).get("all_engines_flip") is True,
            expected="dropping N01 changes reconstructed admission pattern",
            observed={
                "full": reconstructed["admitted_ids"],
                "drop_N01": drop_n01["admitted_ids"],
                "mc_v1_drop_N01_all_engines_flip": (negative_controls.get("drop_N01") or {}).get("all_engines_flip"),
            },
            reason="The N01 dimension is load-bearing in the incidence relation and matches the M(C) v1 control flip.",
        ),
        "degenerate_hypergraph_demotes_to_status_baseline": check(
            "degenerate_hypergraph_demotes_to_status_baseline",
            degenerate_observable["observable_digest"] != observable["observable_digest"]
            and max(degenerate_observable["edge_member_sizes"].values()) == 2,
            expected="rank-2 status baseline differs from full constraint hypergraph",
            observed={
                "full_digest": observable["observable_digest"],
                "degenerate_digest": degenerate_observable["observable_digest"],
                "degenerate_edge_member_sizes": degenerate_observable["edge_member_sizes"],
            },
            reason="A degenerate support/status-only hypergraph removes the five-constraint relation and changes the xgi observable.",
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
            reason="The consumer gate must keep every strong downstream consumer blocked.",
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
        "wave_a_xgi_capability_available": check(
            "wave_a_xgi_capability_available",
            wave_a_payload.get("all_pass") is True and wave_a_xgi.get("pass") is True,
            expected={"wave_a_all_pass": True, "xgi_probe_pass": True},
            observed={
                "wave_a_all_pass": wave_a_payload.get("all_pass"),
                "xgi_probe": {
                    "tool": wave_a_xgi.get("tool"),
                    "probe_id": wave_a_xgi.get("probe_id"),
                    "pass": wave_a_xgi.get("pass"),
                },
            },
            reason="Wave A is consumed only as local no-install xgi capability evidence.",
        ),
        "prior_fit_probes_remain_sibling_evidence_only": check(
            "prior_fit_probes_remain_sibling_evidence_only",
            prior_cvc5_payload.get("all_pass") is True
            and prior_rustworkx_payload.get("all_pass") is True
            and prior_cvc5_payload.get("stage_movement_allowed") is False
            and prior_rustworkx_payload.get("stage_movement_allowed") is False,
            expected={"prior_fit_all_pass": True, "stage_movement_allowed": False},
            observed={
                "cvc5": {
                    "all_pass": prior_cvc5_payload.get("all_pass"),
                    "stage_movement_allowed": prior_cvc5_payload.get("stage_movement_allowed"),
                },
                "rustworkx": {
                    "all_pass": prior_rustworkx_payload.get("all_pass"),
                    "stage_movement_allowed": prior_rustworkx_payload.get("stage_movement_allowed"),
                },
            },
            reason="Prior fit probes are sibling shakedown evidence only, not M(C) admission.",
        ),
    }
    return {
        "finite_carrier_input_object": {
            "field": "Adm_C / constraint_set_C",
            "tool": "xgi",
            "api_surface": "Hypergraph, add_node/add_edge, edge member views, degree, incidence_matrix shape",
            "support_record_count": len(records),
            "constraint_dimensions": CONSTRAINT_DIMS,
            "adm_c_predicate": adm_c.get("predicate"),
            "expected_admitted_ids": expected_admitted,
        },
        "output_object": {
            "full_hypergraph": observable,
            "reconstructed_from_full_hyperedges": reconstructed,
            "pairwise_status_projection": pairwise_projection,
            "drop_F01_control": drop_f01,
            "drop_N01_control": drop_n01,
            "degenerate_hypergraph": degenerate_observable,
        },
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
            "Rerun this exact source after the sim-stack xgi Hypergraph API is "
            "importable and usable; do not install packages in this bounded lane."
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
    prior_rustworkx_payload, prior_rustworkx_load_error = load_json(PRIOR_RUSTWORKX_RESULT_PATH)

    mc_validation = validate_result_path(MC_V1_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True)
    gate_validation = validate_result_path(CONSUMER_GATE_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True)
    wave_a_validation = validate_result_path(WAVE_A_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True)
    prior_cvc5_validation = validate_result_path(PRIOR_CVC5_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True)
    prior_rustworkx_validation = validate_result_path(PRIOR_RUSTWORKX_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True)

    probe = xgi_probe(mc_payload, gate_payload, wave_a_payload, prior_cvc5_payload, prior_rustworkx_payload)
    boundary = probe["boundary"]
    boundary.update(
        {
            "mc_v1_receipt_loaded": check("mc_v1_receipt_loaded", mc_load_error is None, expected=None, observed=mc_load_error, reason="M(C) v1 envelope must be readable JSON."),
            "consumer_gate_receipt_loaded": check("consumer_gate_receipt_loaded", gate_load_error is None, expected=None, observed=gate_load_error, reason="Consumer-gate result must be readable JSON."),
            "wave_a_receipt_loaded": check("wave_a_receipt_loaded", wave_a_load_error is None, expected=None, observed=wave_a_load_error, reason="Wave A result must be readable JSON."),
            "prior_cvc5_receipt_loaded": check("prior_cvc5_receipt_loaded", prior_cvc5_load_error is None, expected=None, observed=prior_cvc5_load_error, reason="Prior cvc5 fit result must be readable JSON."),
            "prior_rustworkx_receipt_loaded": check("prior_rustworkx_receipt_loaded", prior_rustworkx_load_error is None, expected=None, observed=prior_rustworkx_load_error, reason="Prior rustworkx fit result must be readable JSON."),
            "mc_v1_receipt_validates": check("mc_v1_receipt_validates", mc_validation.get("ok") is True, expected=True, observed=mc_validation.get("hard_findings"), reason="Consumed M(C) v1 receipt must pass strict receipt validation."),
            "consumer_gate_receipt_validates": check("consumer_gate_receipt_validates", gate_validation.get("ok") is True, expected=True, observed=gate_validation.get("hard_findings"), reason="Consumed consumer-gate receipt must pass strict receipt validation."),
            "wave_a_receipt_validates": check("wave_a_receipt_validates", wave_a_validation.get("ok") is True, expected=True, observed=wave_a_validation.get("hard_findings"), reason="Consumed Wave A receipt must pass strict receipt validation."),
            "prior_cvc5_receipt_validates": check("prior_cvc5_receipt_validates", prior_cvc5_validation.get("ok") is True, expected=True, observed=prior_cvc5_validation.get("hard_findings"), reason="Prior cvc5 fit receipt must pass strict receipt validation."),
            "prior_rustworkx_receipt_validates": check("prior_rustworkx_receipt_validates", prior_rustworkx_validation.get("ok") is True, expected=True, observed=prior_rustworkx_validation.get("hard_findings"), reason="Prior rustworkx fit receipt must pass strict receipt validation."),
        }
    )
    positive = probe["positive"]
    negative = probe["negative"]
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
        "claim": "xgi can carry a bounded finite Adm_C / constraint_set_C incidence fixture for the exact M(C) v1 fields after the consumer gate",
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
            "consumer_gate_result_path": str(CONSUMER_GATE_RESULT_PATH),
            "consumer_gate_result_sha256": sha256_file(CONSUMER_GATE_RESULT_PATH),
            "wave_a_result_path": str(WAVE_A_RESULT_PATH),
            "wave_a_result_sha256": sha256_file(WAVE_A_RESULT_PATH),
            "prior_cvc5_result_path": str(PRIOR_CVC5_RESULT_PATH),
            "prior_cvc5_result_sha256": sha256_file(PRIOR_CVC5_RESULT_PATH),
            "prior_rustworkx_result_path": str(PRIOR_RUSTWORKX_RESULT_PATH),
            "prior_rustworkx_result_sha256": sha256_file(PRIOR_RUSTWORKX_RESULT_PATH),
        },
        "receipt_schema_validation": {
            "mc_v1_envelope_strict": mc_validation,
            "consumer_gate_strict": gate_validation,
            "wave_a_strict": wave_a_validation,
            "prior_cvc5_strict": prior_cvc5_validation,
            "prior_rustworkx_strict": prior_rustworkx_validation,
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
        write_blocked_reason("xgi API is not importable in the sim-stack interpreter", str(exc))
        print(f"BLOCKED xgi_import error={exc}")
        return 2
    except Exception as exc:
        if "xgi" in traceback.format_exc().lower():
            write_blocked_reason("xgi API is not usable for the requested Hypergraph surface", f"{type(exc).__name__}: {exc}")
            print(f"BLOCKED xgi_usable error={type(exc).__name__}: {exc}")
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
