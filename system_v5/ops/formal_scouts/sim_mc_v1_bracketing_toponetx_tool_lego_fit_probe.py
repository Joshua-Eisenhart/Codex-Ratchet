#!/usr/bin/env python3
"""TopoNetX tool-lego fit probe for M(C) v1 bracketing/readout incidence."""

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


OBJECT_ID = "mc_v1_bracketing_toponetx_tool_lego_fit_probe"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_mc_v1_bracketing_toponetx_tool_lego_fit_probe.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json"
MC_V1_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json"
CONSUMER_GATE_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quarantine_consumer_gate_probe_results.json"
WAVE_A_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/wave_a_cs_ai_no_install_micro_probes_results.json"
PRIOR_CVC5_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json"
PRIOR_RUSTWORKX_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json"
PRIOR_XGI_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json"
BLOCKED_REASON_PATH = ROOT / "system_v5/ops/wizard_admissions/mc_v1_bracketing_toponetx_tool_lego_fit_probe_blocked_reason.json"

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
    "bracketing promotion",
    "carrier_readout_map promotion",
    "topological invariant or geometry claim",
]

CLAIM_CEILING = (
    "Tool-lego fit probe only: TopoNetX SimplicialComplex construction and "
    "rank-1 signed incidence matrices can carry one bounded finite bracketing / "
    "carrier_readout_map incidence fixture for M(C) v1 after the consumer gate. "
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
    "Demote if TopoNetX cannot build the finite complex or signed incidence matrix, "
    "if left/right bracketing records collapse, if drop-bracketing or carrier-erasure "
    "controls do not change the incidence observable, if the consumer gate stops all_pass, "
    "if strong consumers become eligible, or if any promotion/admission flag becomes true."
)

TOOL_MANIFEST = {
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SimplicialComplex construction and signed incidence_matrix(1) readout for the finite bracketing/readout fixture",
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


def import_toponetx() -> Any:
    import toponetx as tnx

    return tnx


def matrix_payload(matrix: Any) -> dict[str, Any]:
    dense = matrix.toarray().tolist() if hasattr(matrix, "toarray") else []
    return {
        "shape": [int(matrix.shape[0]), int(matrix.shape[1])],
        "dense": dense,
        "signed_sum": sum(sum(float(value) for value in row) for row in dense),
        "nonzero_count": sum(1 for row in dense for value in row if float(value) != 0.0),
    }


def readout_signature(readout: list[Any]) -> str:
    return ",".join(str(int(value)) for value in readout)


def build_complex(tnx: Any, bracketing: dict[str, Any], carrier_map: dict[str, Any], *, collapse_brackets: bool = False, erase_carrier: bool = False) -> tuple[Any, dict[str, Any]]:
    complex_obj = tnx.SimplicialComplex()
    left_right_records = [str(item) for item in bracketing.get("left_right_records") or []]
    records = {}
    for record_id in left_right_records:
        carrier = carrier_map.get(record_id) or {}
        selected = carrier.get("selected") or []
        octonion = carrier.get("octonion") or {}
        bracket_label = "collapsed" if collapse_brackets else ("right" if selected and selected[5] == 1 else "left")
        readout_node = "readout/erased" if erase_carrier else f"readout/{readout_signature(selected)}"
        record_node = f"record/{record_id}"
        bracket_node = f"bracket/{bracket_label}"
        carrier_node = "carrier/erased" if erase_carrier else f"carrier/nonzero/{octonion.get('nonzero_components')}"
        complex_obj.add_simplex((record_node, bracket_node))
        complex_obj.add_simplex((record_node, readout_node))
        complex_obj.add_simplex((bracket_node, readout_node))
        complex_obj.add_simplex((readout_node, carrier_node))
        records[record_id] = {
            "record_node": record_node,
            "bracket_node": bracket_node,
            "readout_node": readout_node,
            "carrier_node": carrier_node,
            "selected_readout": selected,
        }
    return complex_obj, records


def complex_observable(tnx: Any, complex_obj: Any, records: dict[str, Any]) -> dict[str, Any]:
    incidence = matrix_payload(complex_obj.incidence_matrix(1))
    simplices = sorted(str(simplex) for simplex in complex_obj.simplices)
    out = {
        "dim": int(complex_obj.dim),
        "shape": [int(value) for value in complex_obj.shape],
        "simplex_count": len(simplices),
        "simplices": simplices,
        "record_nodes": sorted(row["record_node"] for row in records.values()),
        "bracket_nodes": sorted(set(row["bracket_node"] for row in records.values())),
        "readout_nodes": sorted(set(row["readout_node"] for row in records.values())),
        "carrier_nodes": sorted(set(row["carrier_node"] for row in records.values())),
        "incidence_rank_1": incidence,
    }
    out["observable_digest"] = stable_sha256(out)
    return out


def toponetx_probe(
    mc_payload: dict[str, Any],
    gate_payload: dict[str, Any],
    wave_a_payload: dict[str, Any],
    prior_cvc5_payload: dict[str, Any],
    prior_rustworkx_payload: dict[str, Any],
    prior_xgi_payload: dict[str, Any],
) -> dict[str, Any]:
    tnx = import_toponetx()
    bracketing = mc_payload.get("bracketing_in_quotient") or {}
    carrier_map = mc_payload.get("carrier_readout_map") or {}
    positive_complex, positive_records = build_complex(tnx, bracketing, carrier_map)
    positive_observable = complex_observable(tnx, positive_complex, positive_records)
    collapsed_complex, collapsed_records = build_complex(tnx, bracketing, carrier_map, collapse_brackets=True)
    collapsed_observable = complex_observable(tnx, collapsed_complex, collapsed_records)
    erased_complex, erased_records = build_complex(tnx, bracketing, carrier_map, erase_carrier=True)
    erased_observable = complex_observable(tnx, erased_complex, erased_records)
    empty_complex = tnx.SimplicialComplex()
    empty_observable = {
        "dim": int(empty_complex.dim),
        "shape": [int(value) for value in empty_complex.shape],
        "simplex_count": len(list(empty_complex.simplices)),
        "observable_digest": stable_sha256({"empty": True, "shape": [int(value) for value in empty_complex.shape]}),
    }

    gate_eligible = gate_payload.get("eligible_consumers") or []
    gate_blocked = gate_payload.get("blocked_consumers") or gate_payload.get("blocked_downstream_consumers") or []
    wave_a_toponetx = next(
        (row for row in wave_a_payload.get("probes", []) if isinstance(row, dict) and row.get("tool") == "toponetx"),
        {},
    )
    negative_controls = mc_payload.get("negative_controls") or {}

    positive = {
        "consumed_bracketing_and_carrier_fields": check(
            "consumed_bracketing_and_carrier_fields",
            bracketing.get("wired_in") is True and len(carrier_map) >= 4,
            expected={"wired_in": True, "carrier_records_at_least": 4},
            observed={"wired_in": bracketing.get("wired_in"), "carrier_records": sorted(carrier_map)},
            reason="The probe must consume M(C) v1 bracketing_in_quotient and carrier_readout_map fields.",
        ),
        "finite_complex_represents_left_right_records": check(
            "finite_complex_represents_left_right_records",
            positive_observable["record_nodes"] == ["record/s_z0_oct_left", "record/s_z0_oct_right"]
            and positive_observable["incidence_rank_1"]["shape"][1] >= 6,
            expected=["record/s_z0_oct_left", "record/s_z0_oct_right"],
            observed={
                "record_nodes": positive_observable["record_nodes"],
                "incidence_shape": positive_observable["incidence_rank_1"]["shape"],
            },
            reason="The finite TopoNetX complex must represent the explicit left/right bracketing records.",
        ),
        "left_right_bracketing_readouts_distinct": check(
            "left_right_bracketing_readouts_distinct",
            positive_observable["bracket_nodes"] == ["bracket/left", "bracket/right"]
            and len(positive_observable["readout_nodes"]) == 2,
            expected={"bracket_nodes": ["bracket/left", "bracket/right"], "readout_node_count": 2},
            observed={
                "bracket_nodes": positive_observable["bracket_nodes"],
                "readout_nodes": positive_observable["readout_nodes"],
            },
            reason="The left/right bracketing distinction and selected readout vectors must stay visible in the finite incidence object.",
        ),
        "signed_incidence_is_load_bearing": check(
            "signed_incidence_is_load_bearing",
            positive_observable["incidence_rank_1"]["nonzero_count"] > 0
            and positive_observable["incidence_rank_1"]["shape"][0] == positive_observable["shape"][0],
            expected="nonempty signed rank-1 incidence over finite complex",
            observed=positive_observable["incidence_rank_1"],
            reason="TopoNetX incidence_matrix(1) must compute the decisive finite signed boundary/incidence readout.",
        ),
    }
    negative = {
        "drop_bracketing_control_changes_incidence": check(
            "drop_bracketing_control_changes_incidence",
            collapsed_observable["observable_digest"] != positive_observable["observable_digest"]
            and collapsed_observable["bracket_nodes"] == ["bracket/collapsed"]
            and (negative_controls.get("drop_bracketing") or {}).get("all_engines_flip") is True,
            expected="collapsing bracketing changes incidence observable and matches M(C) control flip",
            observed={
                "positive_digest": positive_observable["observable_digest"],
                "collapsed_digest": collapsed_observable["observable_digest"],
                "collapsed_bracket_nodes": collapsed_observable["bracket_nodes"],
                "mc_v1_drop_bracketing_all_engines_flip": (negative_controls.get("drop_bracketing") or {}).get("all_engines_flip"),
            },
            reason="The drop-bracketing control removes the left/right distinction and changes the TopoNetX incidence object.",
        ),
        "carrier_erasure_control_changes_incidence": check(
            "carrier_erasure_control_changes_incidence",
            erased_observable["observable_digest"] != positive_observable["observable_digest"]
            and erased_observable["carrier_nodes"] == ["carrier/erased"]
            and (negative_controls.get("carrier_erasure") or {}).get("all_engines_flip") is True,
            expected="carrier erasure changes incidence observable and matches M(C) control flip",
            observed={
                "positive_digest": positive_observable["observable_digest"],
                "erased_digest": erased_observable["observable_digest"],
                "erased_carrier_nodes": erased_observable["carrier_nodes"],
                "mc_v1_carrier_erasure_all_engines_flip": (negative_controls.get("carrier_erasure") or {}).get("all_engines_flip"),
            },
            reason="Carrier/readout erasure changes the finite incidence object and blocks stronger carrier claims.",
        ),
        "empty_complex_demotes": check(
            "empty_complex_demotes",
            empty_observable["simplex_count"] == 0 and empty_observable["observable_digest"] != positive_observable["observable_digest"],
            expected={"simplex_count": 0, "different_digest": True},
            observed=empty_observable,
            reason="The empty-complex control demotes to no finite incidence fixture.",
        ),
    }
    boundary = {
        "consumer_gate_all_pass": check("consumer_gate_all_pass", gate_payload.get("all_pass") is True, expected=True, observed=gate_payload.get("all_pass"), reason="This tool-lego fit probe is only allowed after the consumer gate passes."),
        "allowed_consumer_present": check("allowed_consumer_present", "exact_tool_lego_fit_probe_after_consumer_gate" in gate_eligible, expected="exact_tool_lego_fit_probe_after_consumer_gate", observed=gate_eligible, reason="The consumer gate must explicitly allow this exact fit-probe shape."),
        "strong_consumers_still_exactly_blocked": check("strong_consumers_still_exactly_blocked", gate_blocked == STRONG_CONSUMERS, expected=STRONG_CONSUMERS, observed=gate_blocked, reason="The consumer gate must keep every strong downstream consumer blocked."),
        "stage_movement_forbidden": check("stage_movement_forbidden", gate_payload.get("stage_movement_allowed") is False and gate_payload.get("stage4_unlock_allowed") is False, expected={"stage_movement_allowed": False, "stage4_unlock_allowed": False}, observed={"stage_movement_allowed": gate_payload.get("stage_movement_allowed"), "stage4_unlock_allowed": gate_payload.get("stage4_unlock_allowed")}, reason="This probe must not move the ladder stage or unlock Stage 4."),
        "promotion_and_formal_admission_forbidden": check("promotion_and_formal_admission_forbidden", promotion_allowed is False and formal_admission_allowed is False, expected={"promotion_allowed": False, "formal_admission_allowed": False}, observed={"promotion_allowed": promotion_allowed, "formal_admission_allowed": formal_admission_allowed}, reason="The result must stay pre-lego fit evidence only."),
        "wave_a_toponetx_capability_available": check("wave_a_toponetx_capability_available", wave_a_payload.get("all_pass") is True and wave_a_toponetx.get("pass") is True, expected={"wave_a_all_pass": True, "toponetx_probe_pass": True}, observed={"wave_a_all_pass": wave_a_payload.get("all_pass"), "toponetx_probe": {"tool": wave_a_toponetx.get("tool"), "probe_id": wave_a_toponetx.get("probe_id"), "pass": wave_a_toponetx.get("pass")}}, reason="Wave A is consumed only as local no-install TopoNetX capability evidence."),
        "prior_fit_probes_remain_sibling_evidence_only": check(
            "prior_fit_probes_remain_sibling_evidence_only",
            all(payload.get("all_pass") is True and payload.get("stage_movement_allowed") is False for payload in [prior_cvc5_payload, prior_rustworkx_payload, prior_xgi_payload]),
            expected={"prior_fit_all_pass": True, "stage_movement_allowed": False},
            observed={
                "cvc5": {"all_pass": prior_cvc5_payload.get("all_pass"), "stage_movement_allowed": prior_cvc5_payload.get("stage_movement_allowed")},
                "rustworkx": {"all_pass": prior_rustworkx_payload.get("all_pass"), "stage_movement_allowed": prior_rustworkx_payload.get("stage_movement_allowed")},
                "xgi": {"all_pass": prior_xgi_payload.get("all_pass"), "stage_movement_allowed": prior_xgi_payload.get("stage_movement_allowed")},
            },
            reason="Prior fit probes are sibling shakedown evidence only, not M(C) admission.",
        ),
    }
    return {
        "finite_carrier_input_object": {
            "field": "bracketing_in_quotient / carrier_readout_map",
            "tool": "toponetx",
            "api_surface": "SimplicialComplex, add_simplex, simplices, incidence_matrix(1)",
            "left_right_records": bracketing.get("left_right_records"),
            "witness_triple": bracketing.get("witness_triple"),
        },
        "output_object": {
            "positive_complex": positive_observable,
            "drop_bracketing_control_complex": collapsed_observable,
            "carrier_erasure_control_complex": erased_observable,
            "empty_complex_control": empty_observable,
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
        "next_admissible_step": "Rerun this exact source after the sim-stack TopoNetX SimplicialComplex API is importable and usable; do not install packages in this bounded lane.",
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
    prior_xgi_payload, prior_xgi_load_error = load_json(PRIOR_XGI_RESULT_PATH)
    validations = {
        "mc_v1_envelope_strict": validate_result_path(MC_V1_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True),
        "consumer_gate_strict": validate_result_path(CONSUMER_GATE_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True),
        "wave_a_strict": validate_result_path(WAVE_A_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True),
        "prior_cvc5_strict": validate_result_path(PRIOR_CVC5_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True),
        "prior_rustworkx_strict": validate_result_path(PRIOR_RUSTWORKX_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True),
        "prior_xgi_strict": validate_result_path(PRIOR_XGI_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True),
    }
    probe = toponetx_probe(mc_payload, gate_payload, wave_a_payload, prior_cvc5_payload, prior_rustworkx_payload, prior_xgi_payload)
    boundary = probe["boundary"]
    for name, load_error, validation in [
        ("mc_v1", mc_load_error, validations["mc_v1_envelope_strict"]),
        ("consumer_gate", gate_load_error, validations["consumer_gate_strict"]),
        ("wave_a", wave_a_load_error, validations["wave_a_strict"]),
        ("prior_cvc5", prior_cvc5_load_error, validations["prior_cvc5_strict"]),
        ("prior_rustworkx", prior_rustworkx_load_error, validations["prior_rustworkx_strict"]),
        ("prior_xgi", prior_xgi_load_error, validations["prior_xgi_strict"]),
    ]:
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
        "claim": "TopoNetX can carry a bounded finite bracketing/readout incidence fixture for the exact M(C) v1 fields after the consumer gate",
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
            "consumed_mc_v1_result_sha256": sha256_file(MC_V1_RESULT_PATH),
            "consumer_gate_result_sha256": sha256_file(CONSUMER_GATE_RESULT_PATH),
            "wave_a_result_sha256": sha256_file(WAVE_A_RESULT_PATH),
            "prior_cvc5_result_sha256": sha256_file(PRIOR_CVC5_RESULT_PATH),
            "prior_rustworkx_result_sha256": sha256_file(PRIOR_RUSTWORKX_RESULT_PATH),
            "prior_xgi_result_sha256": sha256_file(PRIOR_XGI_RESULT_PATH),
        },
        "receipt_schema_validation": validations,
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
        write_blocked_reason("TopoNetX API is not importable in the sim-stack interpreter", str(exc))
        print(f"BLOCKED toponetx_import error={exc}")
        return 2
    except Exception as exc:
        if "toponetx" in traceback.format_exc().lower():
            write_blocked_reason("TopoNetX API is not usable for the requested SimplicialComplex surface", f"{type(exc).__name__}: {exc}")
            print(f"BLOCKED toponetx_usable error={type(exc).__name__}: {exc}")
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
