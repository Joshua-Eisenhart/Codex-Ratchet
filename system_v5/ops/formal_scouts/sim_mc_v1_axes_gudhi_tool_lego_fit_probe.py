#!/usr/bin/env python3
"""GUDHI tool-lego fit probe for M(C) v1 axes_A_i finite filtration."""

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


OBJECT_ID = "mc_v1_axes_gudhi_tool_lego_fit_probe"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_mc_v1_axes_gudhi_tool_lego_fit_probe.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_axes_gudhi_tool_lego_fit_probe_results.json"
MC_V1_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json"
CONSUMER_GATE_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quarantine_consumer_gate_probe_results.json"
WAVE_A_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/wave_a_cs_ai_no_install_micro_probes_results.json"
PRIOR_CVC5_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json"
PRIOR_RUSTWORKX_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json"
PRIOR_XGI_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json"
PRIOR_TOPONETX_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json"
BLOCKED_REASON_PATH = ROOT / "system_v5/ops/wizard_admissions/mc_v1_axes_gudhi_tool_lego_fit_probe_blocked_reason.json"

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
    "axes_A_i promotion",
    "topological invariant promotion",
]

CLAIM_CEILING = (
    "Tool-lego fit probe only: GUDHI SimplexTree insert/get_filtration/"
    "compute_persistence can carry one bounded finite axes_A_i filtration fixture "
    "for M(C) v1 after the consumer gate. This does not admit M(C), does not "
    "unlock Stage 4, and does not support same-carrier geometry, topology readout, "
    "AI/GNN readout, bridge, Axis0, physics, manifold, or formal admission claims."
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
    "Demote if GUDHI cannot build the finite SimplexTree or persistence readout, "
    "if admitted axes records are not represented, if axis erasure or label-shuffle "
    "controls do not change the filtration observable, if the consumer gate stops "
    "all_pass, if strong consumers become eligible, or if any promotion/admission flag becomes true."
)

TOOL_MANIFEST = {
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SimplexTree insertion, filtration ordering, and compute_persistence readout for the finite axes_A_i fixture",
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
    return {
        "name": name,
        "pass": bool(passed),
        "expected": expected,
        "observed": observed,
        "reason": reason,
    }


def section_pass(section: dict[str, dict[str, Any]]) -> bool:
    return all(row["pass"] is True for row in section.values())


def import_gudhi() -> Any:
    import gudhi

    return gudhi


def finite_value(value: float) -> str | float:
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return round(float(value), 12)


def persistence_payload(stree: Any) -> list[dict[str, Any]]:
    return [
        {"dim": int(dim), "birth": finite_value(pair[0]), "death": finite_value(pair[1])}
        for dim, pair in stree.persistence()
    ]


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


def build_axes_fixture(gudhi: Any, axes: dict[str, Any], admitted_ids: list[str], *, mode: str = "positive") -> tuple[Any, dict[int, str]]:
    id_by_vertex = {index: record_id for index, record_id in enumerate(admitted_ids)}
    vertex_by_id = {record_id: index for index, record_id in id_by_vertex.items()}
    entropy = axes.get("A_entropy_bits") or {}
    order_gap = axes.get("A_order_gap") or {}
    associator = axes.get("A_associator_norm") or {}
    stree = gudhi.SimplexTree()
    for record_id in admitted_ids:
        vertex = vertex_by_id[record_id]
        base = float(entropy.get(record_id, 0.0))
        if mode == "erased":
            base = 0.0
        if mode == "label_shuffle":
            base = float(entropy.get(admitted_ids[-(vertex + 1)], 0.0))
        stree.insert([vertex], filtration=base)
    if mode != "degenerate":
        for left, right in combinations(range(len(admitted_ids)), 2):
            left_id = id_by_vertex[left]
            right_id = id_by_vertex[right]
            edge_time = max(
                float(entropy.get(left_id, 0.0)),
                float(entropy.get(right_id, 0.0)),
            ) + max(float(order_gap.get(left_id, 0.0)), float(order_gap.get(right_id, 0.0)))
            if mode == "erased":
                edge_time = 0.0
            if mode == "label_shuffle":
                edge_time = 1.0 - min(edge_time, 1.0)
            stree.insert([left, right], filtration=edge_time)
        stree.insert([0, 1, 2], filtration=max(float(associator.get(admitted_ids[0], 2.0)), 2.0))
    stree.compute_persistence()
    return stree, id_by_vertex


def observable(stree: Any, id_by_vertex: dict[int, str]) -> dict[str, Any]:
    out = {
        "num_vertices": len(id_by_vertex),
        "num_simplices": int(stree.num_simplices()),
        "filtration": filtration_payload(stree, id_by_vertex),
        "persistence": persistence_payload(stree),
        "betti_numbers": [int(value) for value in stree.betti_numbers()],
    }
    out["observable_digest"] = stable_sha256(out)
    return out


def gudhi_probe(
    mc_payload: dict[str, Any],
    gate_payload: dict[str, Any],
    wave_a_payload: dict[str, Any],
    prior_payloads: list[dict[str, Any]],
) -> dict[str, Any]:
    gudhi = import_gudhi()
    axes = mc_payload.get("axes_A_i") or {}
    admitted_ids = sorted(str(item) for item in ((mc_payload.get("Adm_C") or {}).get("admitted_ids") or []))
    positive_tree, id_by_vertex = build_axes_fixture(gudhi, axes, admitted_ids)
    positive_obs = observable(positive_tree, id_by_vertex)
    erased_tree, erased_id_map = build_axes_fixture(gudhi, axes, admitted_ids, mode="erased")
    erased_obs = observable(erased_tree, erased_id_map)
    shuffled_tree, shuffled_id_map = build_axes_fixture(gudhi, axes, admitted_ids, mode="label_shuffle")
    shuffled_obs = observable(shuffled_tree, shuffled_id_map)
    degenerate_tree, degenerate_id_map = build_axes_fixture(gudhi, axes, admitted_ids, mode="degenerate")
    degenerate_obs = observable(degenerate_tree, degenerate_id_map)

    gate_eligible = gate_payload.get("eligible_consumers") or []
    gate_blocked = gate_payload.get("blocked_consumers") or gate_payload.get("blocked_downstream_consumers") or []
    wave_a_gudhi = next((row for row in wave_a_payload.get("probes", []) if isinstance(row, dict) and row.get("tool") == "gudhi"), {})
    negative_controls = mc_payload.get("negative_controls") or {}

    positive = {
        "consumed_axes_and_admitted_ids": check(
            "consumed_axes_and_admitted_ids",
            sorted(axes) == ["A_associator_norm", "A_entropy_bits", "A_order_gap"] and len(admitted_ids) == 4,
            expected={"axes": ["A_associator_norm", "A_entropy_bits", "A_order_gap"], "admitted_count": 4},
            observed={"axes": sorted(axes), "admitted_ids": admitted_ids},
            reason="The probe must consume M(C) v1 axes_A_i for the admitted records.",
        ),
        "finite_simplex_tree_represents_admitted_records": check(
            "finite_simplex_tree_represents_admitted_records",
            positive_obs["num_vertices"] == 4 and positive_obs["num_simplices"] >= 10,
            expected={"num_vertices": 4, "num_simplices_at_least": 10},
            observed={"num_vertices": positive_obs["num_vertices"], "num_simplices": positive_obs["num_simplices"]},
            reason="GUDHI must build a finite SimplexTree over the admitted M(C) axes records.",
        ),
        "filtration_and_persistence_readout_live": check(
            "filtration_and_persistence_readout_live",
            bool(positive_obs["filtration"]) and bool(positive_obs["persistence"]),
            expected={"filtration_nonempty": True, "persistence_nonempty": True},
            observed={"filtration_count": len(positive_obs["filtration"]), "persistence": positive_obs["persistence"]},
            reason="GUDHI get_filtration and compute_persistence must produce the decisive bounded readout.",
        ),
    }
    negative = {
        "axis_value_erasure_changes_filtration": check(
            "axis_value_erasure_changes_filtration",
            erased_obs["observable_digest"] != positive_obs["observable_digest"],
            expected="axis-value erasure changes filtration observable",
            observed={"positive_digest": positive_obs["observable_digest"], "erased_digest": erased_obs["observable_digest"]},
            reason="Erasing axis values changes the finite filtration and blocks stronger axes claims.",
        ),
        "label_shuffle_control_changes_filtration": check(
            "label_shuffle_control_changes_filtration",
            shuffled_obs["observable_digest"] != positive_obs["observable_digest"]
            and (negative_controls.get("label_shuffle") or {}).get("all_engines_flip") is True,
            expected="label shuffle changes filtration observable and matches M(C) control flip",
            observed={
                "positive_digest": positive_obs["observable_digest"],
                "shuffled_digest": shuffled_obs["observable_digest"],
                "mc_v1_label_shuffle_all_engines_flip": (negative_controls.get("label_shuffle") or {}).get("all_engines_flip"),
            },
            reason="The label-shuffle control changes the record-to-filtration assignment.",
        ),
        "degenerate_unfilled_control_demotes": check(
            "degenerate_unfilled_control_demotes",
            degenerate_obs["observable_digest"] != positive_obs["observable_digest"]
            and degenerate_obs["num_simplices"] == degenerate_obs["num_vertices"],
            expected="vertex-only control differs and has no filled higher simplices",
            observed={"degenerate": degenerate_obs, "positive_digest": positive_obs["observable_digest"]},
            reason="A vertex-only SimplexTree demotes to a weaker baseline and changes the GUDHI observable.",
        ),
    }
    boundary = {
        "consumer_gate_all_pass": check("consumer_gate_all_pass", gate_payload.get("all_pass") is True, expected=True, observed=gate_payload.get("all_pass"), reason="This tool-lego fit probe is only allowed after the consumer gate passes."),
        "allowed_consumer_present": check("allowed_consumer_present", "exact_tool_lego_fit_probe_after_consumer_gate" in gate_eligible, expected="exact_tool_lego_fit_probe_after_consumer_gate", observed=gate_eligible, reason="The consumer gate must explicitly allow this exact fit-probe shape."),
        "strong_consumers_still_exactly_blocked": check("strong_consumers_still_exactly_blocked", gate_blocked == STRONG_CONSUMERS, expected=STRONG_CONSUMERS, observed=gate_blocked, reason="The consumer gate must keep every strong downstream consumer blocked."),
        "stage_movement_forbidden": check("stage_movement_forbidden", gate_payload.get("stage_movement_allowed") is False and gate_payload.get("stage4_unlock_allowed") is False, expected={"stage_movement_allowed": False, "stage4_unlock_allowed": False}, observed={"stage_movement_allowed": gate_payload.get("stage_movement_allowed"), "stage4_unlock_allowed": gate_payload.get("stage4_unlock_allowed")}, reason="This probe must not move the ladder stage or unlock Stage 4."),
        "promotion_and_formal_admission_forbidden": check("promotion_and_formal_admission_forbidden", promotion_allowed is False and formal_admission_allowed is False, expected={"promotion_allowed": False, "formal_admission_allowed": False}, observed={"promotion_allowed": promotion_allowed, "formal_admission_allowed": formal_admission_allowed}, reason="The result must stay pre-lego fit evidence only."),
        "wave_a_gudhi_capability_available": check("wave_a_gudhi_capability_available", wave_a_payload.get("all_pass") is True and wave_a_gudhi.get("pass") is True, expected={"wave_a_all_pass": True, "gudhi_probe_pass": True}, observed={"wave_a_all_pass": wave_a_payload.get("all_pass"), "gudhi_probe": {"tool": wave_a_gudhi.get("tool"), "probe_id": wave_a_gudhi.get("probe_id"), "pass": wave_a_gudhi.get("pass")}}, reason="Wave A is consumed only as local no-install GUDHI capability evidence."),
        "prior_fit_probes_remain_sibling_evidence_only": check(
            "prior_fit_probes_remain_sibling_evidence_only",
            all(payload.get("all_pass") is True and payload.get("stage_movement_allowed") is False for payload in prior_payloads),
            expected={"prior_fit_all_pass": True, "stage_movement_allowed": False},
            observed=[{"name": payload.get("name"), "all_pass": payload.get("all_pass"), "stage_movement_allowed": payload.get("stage_movement_allowed")} for payload in prior_payloads],
            reason="Prior fit probes are sibling shakedown evidence only, not M(C) admission.",
        ),
    }
    return {
        "finite_carrier_input_object": {
            "field": "axes_A_i",
            "tool": "gudhi",
            "api_surface": "SimplexTree, insert, get_filtration, compute_persistence, persistence, betti_numbers",
            "admitted_ids": admitted_ids,
            "vertex_id_map": {str(key): value for key, value in id_by_vertex.items()},
        },
        "output_object": {
            "positive_filtration": positive_obs,
            "axis_erasure_control": erased_obs,
            "label_shuffle_control": shuffled_obs,
            "degenerate_unfilled_control": degenerate_obs,
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
        "next_admissible_step": "Rerun this exact source after the sim-stack GUDHI SimplexTree API is importable and usable; do not install packages in this bounded lane.",
        "recommended_next_move": "Keep M(C) v1 quarantined and do not move Stage 4.",
        "claim_ceiling": CLAIM_CEILING,
        "source_path": str(SOURCE_PATH),
        "intended_result_path": str(RESULT_PATH),
    }
    BLOCKED_REASON_PATH.parent.mkdir(parents=True, exist_ok=True)
    BLOCKED_REASON_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_result() -> dict[str, Any]:
    started_ns = time.perf_counter_ns()
    paths = [
        MC_V1_RESULT_PATH,
        CONSUMER_GATE_RESULT_PATH,
        WAVE_A_RESULT_PATH,
        PRIOR_CVC5_RESULT_PATH,
        PRIOR_RUSTWORKX_RESULT_PATH,
        PRIOR_XGI_RESULT_PATH,
        PRIOR_TOPONETX_RESULT_PATH,
    ]
    payloads = []
    load_errors = []
    validations = []
    for path in paths:
        payload, load_error = load_json(path)
        payloads.append(payload)
        load_errors.append(load_error)
        validations.append(validate_result_path(path, root=ROOT, strict_scope=True, require_run_boundary=True))
    mc_payload, gate_payload, wave_a_payload = payloads[:3]
    prior_payloads = payloads[3:]
    probe = gudhi_probe(mc_payload, gate_payload, wave_a_payload, prior_payloads)
    boundary = probe["boundary"]
    names = ["mc_v1", "consumer_gate", "wave_a", "prior_cvc5", "prior_rustworkx", "prior_xgi", "prior_toponetx"]
    for name, load_error, validation in zip(names, load_errors, validations):
        boundary[f"{name}_receipt_loaded"] = check(f"{name}_receipt_loaded", load_error is None, expected=None, observed=load_error, reason=f"{name} receipt must be readable JSON.")
        boundary[f"{name}_receipt_validates"] = check(f"{name}_receipt_validates", validation.get("ok") is True, expected=True, observed=validation.get("hard_findings"), reason=f"{name} receipt must pass strict receipt validation.")
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
        "claim": "GUDHI can carry a bounded finite axes_A_i filtration fixture for the exact M(C) v1 field after the consumer gate",
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
            **{f"{name}_result_sha256": sha256_file(path) for name, path in zip(names, paths)},
        },
        "receipt_schema_validation": dict(zip(names, validations)),
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
        write_blocked_reason("GUDHI API is not importable in the sim-stack interpreter", str(exc))
        print(f"BLOCKED gudhi_import error={exc}")
        return 2
    except Exception as exc:
        if "gudhi" in traceback.format_exc().lower():
            write_blocked_reason("GUDHI API is not usable for the requested SimplexTree surface", f"{type(exc).__name__}: {exc}")
            print(f"BLOCKED gudhi_usable error={type(exc).__name__}: {exc}")
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
