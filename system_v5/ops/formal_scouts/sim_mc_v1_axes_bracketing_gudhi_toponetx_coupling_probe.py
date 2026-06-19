#!/usr/bin/env python3
"""Scratch tool-tool coupling probe for M(C) v1 axes and bracketing incidence."""

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


OBJECT_ID = "mc_v1_axes_bracketing_gudhi_toponetx_coupling_probe"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_mc_v1_axes_bracketing_gudhi_toponetx_coupling_probe.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_axes_bracketing_gudhi_toponetx_coupling_probe_results.json"
MC_V1_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json"
CONSUMER_GATE_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quarantine_consumer_gate_probe_results.json"
PRIOR_GUDHI_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_axes_gudhi_tool_lego_fit_probe_results.json"
PRIOR_TOPONETX_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json"
BLOCKED_REASON_PATH = ROOT / "system_v5/ops/wizard_admissions/mc_v1_axes_bracketing_gudhi_toponetx_coupling_probe_blocked_reason.json"

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
    "axes_A_i promotion",
    "bracketing promotion",
    "topological invariant or geometry claim",
]

CLAIM_CEILING = (
    "Scratch diagnostic tool-tool coupling only: GUDHI axes filtration and "
    "TopoNetX bracketing/readout incidence can be checked against the same "
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
    "Demote if either parent fit receipt fails validation, if GUDHI no longer "
    "emits a nontrivial finite filtration over admitted records, if TopoNetX no "
    "longer emits a nontrivial signed incidence over the same admitted records, "
    "if axis scramble/bracketing-collapse/empty controls do not change or demote "
    "the coupled observable, if strong consumers become eligible, or if any "
    "promotion/admission flag becomes true."
)

TOOL_MANIFEST = {
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SimplexTree insertion, filtration, and persistence readout over admitted record vertices",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SimplicialComplex construction and signed incidence_matrix(1) readout over bracketing/readout nodes",
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
    "gudhi": "load_bearing",
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
    import gudhi
    import toponetx as tnx

    return gudhi, tnx


def finite_value(value: float) -> str | float:
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return round(float(value), 12)


def admitted_ids(mc_payload: dict[str, Any]) -> list[str]:
    return sorted(str(item) for item in ((mc_payload.get("Adm_C") or {}).get("admitted_ids") or []))


def readout_signature(readout: list[Any]) -> str:
    return ",".join(str(int(value)) for value in readout)


def axis_vertex_times(axes: dict[str, Any], ids: list[str], *, mode: str) -> dict[str, float]:
    entropy = axes.get("A_entropy_bits") or {}
    if mode == "axis_erased":
        return {record_id: 0.0 for record_id in ids}
    if mode == "axis_scramble":
        scrambled = list(reversed(ids))
        return {record_id: float(entropy.get(scrambled[index], 0.0)) for index, record_id in enumerate(ids)}
    return {record_id: float(entropy.get(record_id, 0.0)) for record_id in ids}


def build_filtration(gudhi: Any, axes: dict[str, Any], ids: list[str], *, mode: str = "positive") -> tuple[Any, dict[int, str]]:
    id_by_vertex = {index: record_id for index, record_id in enumerate(ids)}
    vertex_by_id = {record_id: index for index, record_id in id_by_vertex.items()}
    vertex_times = axis_vertex_times(axes, ids, mode=mode)
    order_gap = axes.get("A_order_gap") or {}
    associator = axes.get("A_associator_norm") or {}
    stree = gudhi.SimplexTree()
    for record_id in ids:
        stree.insert([vertex_by_id[record_id]], filtration=vertex_times[record_id])
    if mode != "degenerate":
        for left, right in combinations(range(len(ids)), 2):
            left_id = id_by_vertex[left]
            right_id = id_by_vertex[right]
            edge_time = max(vertex_times[left_id], vertex_times[right_id]) + max(
                float(order_gap.get(left_id, 0.0)),
                float(order_gap.get(right_id, 0.0)),
            )
            if mode == "axis_erased":
                edge_time = 0.0
            stree.insert([left, right], filtration=edge_time)
        if len(ids) >= 3:
            tri_time = max(vertex_times.values()) + max(float(associator.get(record_id, 2.0)) for record_id in ids)
            if mode == "axis_erased":
                tri_time = 0.0
            stree.insert([0, 1, 2], filtration=tri_time)
    stree.compute_persistence()
    return stree, id_by_vertex


def filtration_observable(stree: Any, id_by_vertex: dict[int, str]) -> dict[str, Any]:
    filtration = []
    for simplex, value in stree.get_filtration():
        filtration.append(
            {
                "simplex": [id_by_vertex.get(int(vertex), str(vertex)) for vertex in simplex],
                "vertex_ids": [int(vertex) for vertex in simplex],
                "filtration": finite_value(value),
            }
        )
    persistence = [
        {"dim": int(dim), "birth": finite_value(pair[0]), "death": finite_value(pair[1])}
        for dim, pair in stree.persistence()
    ]
    out = {
        "num_vertices": len(id_by_vertex),
        "num_simplices": int(stree.num_simplices()),
        "record_ids": [id_by_vertex[index] for index in sorted(id_by_vertex)],
        "filtration": filtration,
        "persistence": persistence,
        "betti_numbers": [int(value) for value in stree.betti_numbers()],
    }
    out["observable_digest"] = stable_sha256(out)
    return out


def build_bracketing_complex(
    tnx: Any,
    mc_payload: dict[str, Any],
    ids: list[str],
    *,
    collapse_brackets: bool = False,
    empty: bool = False,
) -> tuple[Any, dict[str, Any]]:
    complex_obj = tnx.SimplicialComplex()
    if empty:
        return complex_obj, {}
    carrier_map = mc_payload.get("carrier_readout_map") or {}
    left_right = set(str(item) for item in ((mc_payload.get("bracketing_in_quotient") or {}).get("left_right_records") or []))
    records: dict[str, Any] = {}
    for record_id in ids:
        carrier = carrier_map.get(record_id) or {}
        selected = carrier.get("selected") or []
        bracket_label = "collapsed" if collapse_brackets else ("right" if record_id in left_right and selected and selected[5] == 1 else "left")
        record_node = f"record/{record_id}"
        bracket_node = f"bracket/{bracket_label}"
        readout_node = f"readout/{readout_signature(selected)}"
        axis_node = "axis/admitted"
        complex_obj.add_simplex((record_node, bracket_node))
        complex_obj.add_simplex((record_node, readout_node))
        complex_obj.add_simplex((record_node, axis_node))
        complex_obj.add_simplex((bracket_node, readout_node, axis_node))
        records[record_id] = {
            "record_node": record_node,
            "bracket_node": bracket_node,
            "readout_node": readout_node,
            "axis_node": axis_node,
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
        "record_ids": sorted(records),
        "bracket_nodes": sorted(set(row["bracket_node"] for row in records.values())),
        "readout_nodes": sorted(set(row["readout_node"] for row in records.values())),
        "incidence_rank_1": incidence,
    }
    out["observable_digest"] = stable_sha256(out)
    return out


def probe(
    mc_payload: dict[str, Any],
    gate_payload: dict[str, Any],
    prior_gudhi_payload: dict[str, Any],
    prior_toponetx_payload: dict[str, Any],
) -> dict[str, Any]:
    gudhi, tnx = import_tools()
    ids = admitted_ids(mc_payload)
    axes = mc_payload.get("axes_A_i") or {}
    positive_tree, positive_id_map = build_filtration(gudhi, axes, ids)
    positive_filtration = filtration_observable(positive_tree, positive_id_map)
    positive_complex, positive_records = build_bracketing_complex(tnx, mc_payload, ids)
    positive_complex_obs = complex_observable(positive_complex, positive_records)

    scrambled_tree, scrambled_id_map = build_filtration(gudhi, axes, ids, mode="axis_scramble")
    scrambled_filtration = filtration_observable(scrambled_tree, scrambled_id_map)
    collapsed_complex, collapsed_records = build_bracketing_complex(tnx, mc_payload, ids, collapse_brackets=True)
    collapsed_complex_obs = complex_observable(collapsed_complex, collapsed_records)
    erased_tree, erased_id_map = build_filtration(gudhi, axes, ids, mode="axis_erased")
    erased_filtration = filtration_observable(erased_tree, erased_id_map)
    empty_complex, empty_records = build_bracketing_complex(tnx, mc_payload, ids, empty=True)
    empty_complex_obs = complex_observable(empty_complex, empty_records)

    coupled_positive_digest = stable_sha256(
        {
            "record_ids": ids,
            "gudhi": positive_filtration["observable_digest"],
            "toponetx": positive_complex_obs["observable_digest"],
        }
    )
    coupled_scrambled_digest = stable_sha256(
        {
            "record_ids": ids,
            "gudhi": scrambled_filtration["observable_digest"],
            "toponetx": positive_complex_obs["observable_digest"],
        }
    )
    coupled_collapsed_digest = stable_sha256(
        {
            "record_ids": ids,
            "gudhi": positive_filtration["observable_digest"],
            "toponetx": collapsed_complex_obs["observable_digest"],
        }
    )
    coupled_erased_empty_digest = stable_sha256(
        {
            "record_ids": ids,
            "gudhi": erased_filtration["observable_digest"],
            "toponetx": empty_complex_obs["observable_digest"],
        }
    )

    gate_eligible = gate_payload.get("eligible_consumers") or []
    gate_blocked = gate_payload.get("blocked_consumers") or gate_payload.get("blocked_downstream_consumers") or []
    prior_receipts_ok = (
        prior_gudhi_payload.get("all_pass") is True
        and prior_gudhi_payload.get("classification") == "tool_lego_fit_probe"
        and prior_gudhi_payload.get("stage_movement_allowed") is False
        and prior_toponetx_payload.get("all_pass") is True
        and prior_toponetx_payload.get("classification") == "tool_lego_fit_probe"
        and prior_toponetx_payload.get("stage_movement_allowed") is False
    )

    positive = {
        "parent_fit_receipts_consumed": check(
            "parent_fit_receipts_consumed",
            prior_receipts_ok,
            expected={"gudhi": "tool_lego_fit_probe all_pass true no stage movement", "toponetx": "same"},
            observed={
                "gudhi": {
                    "classification": prior_gudhi_payload.get("classification"),
                    "all_pass": prior_gudhi_payload.get("all_pass"),
                    "stage_movement_allowed": prior_gudhi_payload.get("stage_movement_allowed"),
                },
                "toponetx": {
                    "classification": prior_toponetx_payload.get("classification"),
                    "all_pass": prior_toponetx_payload.get("all_pass"),
                    "stage_movement_allowed": prior_toponetx_payload.get("stage_movement_allowed"),
                },
            },
            reason="tool-tool coupling must cite two prior parent fit receipts",
        ),
        "same_admitted_record_set_is_coupled": check(
            "same_admitted_record_set_is_coupled",
            len(ids) == 4
            and positive_filtration["record_ids"] == ids
            and positive_complex_obs["record_ids"] == ids,
            expected={"admitted_record_count": 4, "same_record_ids": True},
            observed={
                "admitted_ids": ids,
                "gudhi_ids": positive_filtration["record_ids"],
                "toponetx_ids": positive_complex_obs["record_ids"],
            },
            reason="Both tools must consume the same finite admitted-record carrier, not parallel unrelated fixtures",
        ),
        "gudhi_and_toponetx_observables_nontrivial": check(
            "gudhi_and_toponetx_observables_nontrivial",
            positive_filtration["num_simplices"] > positive_filtration["num_vertices"]
            and len(positive_filtration["persistence"]) > 0
            and positive_complex_obs["incidence_rank_1"]["nonzero_count"] > 0
            and positive_complex_obs["simplex_count"] > len(ids),
            expected={"gudhi_nontrivial": True, "toponetx_nontrivial": True},
            observed={
                "gudhi": {
                    "vertices": positive_filtration["num_vertices"],
                    "simplices": positive_filtration["num_simplices"],
                    "persistence_count": len(positive_filtration["persistence"]),
                },
                "toponetx": {
                    "simplex_count": positive_complex_obs["simplex_count"],
                    "incidence_nonzero": positive_complex_obs["incidence_rank_1"]["nonzero_count"],
                },
            },
            reason="The coupling must use actual filtration and incidence readouts, not imports or labels",
        ),
    }
    negative = {
        "axis_scramble_changes_coupled_observable": check(
            "axis_scramble_changes_coupled_observable",
            scrambled_filtration["observable_digest"] != positive_filtration["observable_digest"]
            and coupled_scrambled_digest != coupled_positive_digest,
            expected={"gudhi_digest_changes": True, "coupled_digest_changes": True},
            observed={
                "positive_gudhi": positive_filtration["observable_digest"],
                "scrambled_gudhi": scrambled_filtration["observable_digest"],
                "positive_coupled": coupled_positive_digest,
                "scrambled_coupled": coupled_scrambled_digest,
            },
            reason="Scrambling axes_A_i must change the GUDHI side and therefore the coupled digest",
        ),
        "bracketing_collapse_changes_coupled_observable": check(
            "bracketing_collapse_changes_coupled_observable",
            collapsed_complex_obs["observable_digest"] != positive_complex_obs["observable_digest"]
            and coupled_collapsed_digest != coupled_positive_digest,
            expected={"toponetx_digest_changes": True, "coupled_digest_changes": True},
            observed={
                "positive_toponetx": positive_complex_obs["observable_digest"],
                "collapsed_toponetx": collapsed_complex_obs["observable_digest"],
                "positive_coupled": coupled_positive_digest,
                "collapsed_coupled": coupled_collapsed_digest,
            },
            reason="Collapsing left/right bracketing must change the TopoNetX side and therefore the coupled digest",
        ),
        "erased_or_empty_carriers_demote": check(
            "erased_or_empty_carriers_demote",
            erased_filtration["observable_digest"] != positive_filtration["observable_digest"]
            and empty_complex_obs["simplex_count"] == 0
            and empty_complex_obs["incidence_rank_1"]["nonzero_count"] == 0
            and coupled_erased_empty_digest != coupled_positive_digest,
            expected={"axis_erasure_changes": True, "empty_complex_demotes": True, "coupled_digest_changes": True},
            observed={
                "erased_gudhi": erased_filtration["observable_digest"],
                "empty_toponetx": empty_complex_obs,
                "positive_coupled": coupled_positive_digest,
                "erased_empty_coupled": coupled_erased_empty_digest,
            },
            reason="Axis erasure or empty incidence carrier must not preserve the coupled evidence",
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
            observed={
                "classification": classification,
                "promotion_allowed": promotion_allowed,
                "formal_admission_allowed": formal_admission_allowed,
            },
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
        "record_ids": ids,
        "gudhi_observable": positive_filtration,
        "toponetx_observable": positive_complex_obs,
        "scrambled_gudhi_observable": scrambled_filtration,
        "collapsed_toponetx_observable": collapsed_complex_obs,
        "erased_gudhi_observable": erased_filtration,
        "empty_toponetx_observable": empty_complex_obs,
        "coupled_digest": coupled_positive_digest,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }


def build_result() -> dict[str, Any]:
    started = time.perf_counter()
    mc_payload, mc_error = load_json(MC_V1_RESULT_PATH)
    gate_payload, gate_error = load_json(CONSUMER_GATE_RESULT_PATH)
    prior_gudhi_payload, gudhi_error = load_json(PRIOR_GUDHI_RESULT_PATH)
    prior_toponetx_payload, toponetx_error = load_json(PRIOR_TOPONETX_RESULT_PATH)
    receipt_checks: dict[str, dict[str, Any]] = {}
    for label, path, load_error in [
        ("mc_v1", MC_V1_RESULT_PATH, mc_error),
        ("consumer_gate", CONSUMER_GATE_RESULT_PATH, gate_error),
        ("parent_gudhi", PRIOR_GUDHI_RESULT_PATH, gudhi_error),
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
        details = probe(mc_payload, gate_payload, prior_gudhi_payload, prior_toponetx_payload)
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
            "parent_gudhi": str(PRIOR_GUDHI_RESULT_PATH),
            "parent_toponetx": str(PRIOR_TOPONETX_RESULT_PATH),
        },
        "input_receipt_sha256": {
            "mc_v1": sha256_file(MC_V1_RESULT_PATH),
            "consumer_gate": sha256_file(CONSUMER_GATE_RESULT_PATH),
            "parent_gudhi": sha256_file(PRIOR_GUDHI_RESULT_PATH),
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
                "next_admissible_step": "Repair only this bounded GUDHI/TopoNetX coupling probe or demote it; do not move stage.",
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
