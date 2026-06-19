#!/usr/bin/env python3
"""cvc5 tool-lego fit probe for the quarantined M(C) v1 quotient relation."""

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


OBJECT_ID = "mc_v1_quotient_relation_cvc5_tool_lego_fit_probe"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_mc_v1_quotient_relation_cvc5_tool_lego_fit_probe.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json"
MC_V1_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json"
CONSUMER_GATE_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quarantine_consumer_gate_probe_results.json"
BLOCKED_REASON_PATH = ROOT / "system_v5/ops/wizard_admissions/mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_blocked_reason.json"

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
    "Tool-lego fit probe only: cvc5 Solver Boolean constraints can carry one bounded "
    "finite quotient_relation fixture for the quarantined M(C) v1 field after the "
    "consumer gate. This does not admit M(C), does not unlock Stage 4, and does not "
    "support same-carrier geometry, topology readout, AI/GNN readout, bridge, Axis0, "
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
    "Demote if cvc5 cannot build the Boolean equality fixture, if positive UNSAT or "
    "drop-bracketing SAT flips fail, if the consumer gate stops all_pass, if strong "
    "consumers become eligible, or if any promotion/admission flag becomes true."
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
    "quotient_relation promotion",
]

TOOL_MANIFEST = {
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Solver Boolean equality/AND/OR/NOT/IMPLIES constraints for the finite quotient_relation fixture",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive parsing of the two consumed receipts and deterministic receipt writing",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive repo-local path binding for the source and result artifacts",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive sha256 pinning of source and consumed result artifacts",
    },
    "time": {
        "tried": True,
        "used": True,
        "reason": "supportive elapsed-time measurement for the bounded executable receipt",
    },
    "receipt_schema": {
        "tried": True,
        "used": True,
        "reason": "supportive validation of the two consumed receipts against the current repo schema",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "cvc5": "load_bearing",
    "json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
    "time": "supportive",
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


def flatten_key(value: Any, prefix: str = "") -> dict[str, str]:
    if isinstance(value, dict):
        out: dict[str, str] = {}
        for key in sorted(value):
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            out.update(flatten_key(value[key], child_prefix))
        return out
    return {prefix: json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)}


def class_key_by_member(quotient: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in quotient.get("classes") or []:
        if not isinstance(row, dict):
            continue
        key = row.get("key")
        if not isinstance(key, dict):
            continue
        for member in row.get("members") or []:
            out[str(member)] = key
    return out


def clone_jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str))


def make_solver() -> tuple[Any, Any]:
    import cvc5
    from cvc5 import Kind

    solver = cvc5.Solver()
    solver.setLogic("ALL")
    solver.setOption("produce-models", "true")
    return solver, Kind


def bool_const(solver: Any, name: str) -> Any:
    return solver.mkConst(solver.getBooleanSort(), name)


def bool_lit(solver: Any, value: bool) -> Any:
    return solver.mkBoolean(bool(value))


def term_and(solver: Any, kind: Any, terms: list[Any]) -> Any:
    if not terms:
        return bool_lit(solver, True)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(kind.AND, *terms)


def term_eq(solver: Any, kind: Any, left: Any, right: Any) -> Any:
    return solver.mkTerm(kind.EQUAL, left, right)


def term_not(solver: Any, kind: Any, term: Any) -> Any:
    return solver.mkTerm(kind.NOT, term)


def term_implies(solver: Any, kind: Any, left: Any, right: Any) -> Any:
    return solver.mkTerm(kind.IMPLIES, left, right)


def run_solver_case(
    case_id: str,
    equality_values: dict[str, bool],
    *,
    drop_prefixes: tuple[str, ...] = (),
    assert_separated: bool = False,
    assert_full_equal: bool | None = None,
    assert_drop_equal: bool | None = None,
) -> dict[str, Any]:
    solver, kind = make_solver()
    eq_terms: dict[str, Any] = {}
    for raw_path, equal_value in sorted(equality_values.items()):
        safe_name = raw_path.replace(".", "_").replace("[", "_").replace("]", "_")
        var = bool_const(solver, f"{case_id}_{safe_name}_eq")
        eq_terms[raw_path] = var
        solver.assertFormula(term_eq(solver, kind, var, bool_lit(solver, equal_value)))

    full_equal = bool_const(solver, f"{case_id}_quotient_equal_full")
    full_conjunction = term_and(solver, kind, list(eq_terms.values()))
    solver.assertFormula(term_eq(solver, kind, full_equal, full_conjunction))

    separated = bool_const(solver, f"{case_id}_separated")
    solver.assertFormula(term_implies(solver, kind, full_equal, term_not(solver, kind, separated)))
    if assert_separated:
        solver.assertFormula(separated)
    if assert_full_equal is not None:
        solver.assertFormula(term_eq(solver, kind, full_equal, bool_lit(solver, assert_full_equal)))

    drop_terms = [
        term
        for path, term in eq_terms.items()
        if not any(path.startswith(prefix) for prefix in drop_prefixes)
    ]
    drop_equal = bool_const(solver, f"{case_id}_quotient_equal_drop_control")
    solver.assertFormula(term_eq(solver, kind, drop_equal, term_and(solver, kind, drop_terms)))
    if assert_drop_equal is not None:
        solver.assertFormula(term_eq(solver, kind, drop_equal, bool_lit(solver, assert_drop_equal)))

    result = solver.checkSat()
    model = {}
    if result.isSat():
        model = {
            "quotient_equal_full": str(solver.getValue(full_equal)),
            "quotient_equal_drop_control": str(solver.getValue(drop_equal)),
            "separated": str(solver.getValue(separated)),
        }
    return {
        "case_id": case_id,
        "result": str(result),
        "sat": result.isSat(),
        "unsat": result.isUnsat(),
        "component_count": len(equality_values),
        "drop_component_count": len(drop_terms),
        "false_components": sorted(path for path, value in equality_values.items() if value is False),
        "model": model,
    }


def cvc5_probe(mc_payload: dict[str, Any], gate_payload: dict[str, Any]) -> dict[str, Any]:
    quotient_relation = mc_payload.get("quotient_relation") or {}
    admitted_quotient = quotient_relation.get("quotient_Adm_C_mod_M") or {}
    full_quotient = quotient_relation.get("quotient_S_mod_M") or {}
    admitted_classes = admitted_quotient.get("classes") or []
    if not admitted_classes:
        raise RuntimeError("quotient_relation.quotient_Adm_C_mod_M.classes is empty")

    positive_class = admitted_classes[0]
    positive_key = positive_class["key"]
    positive_member = str((positive_class.get("members") or ["missing_member"])[0])
    positive_components = {path: True for path in flatten_key(positive_key)}
    positive_case = run_solver_case(
        "positive_identical_full_key_cannot_be_separated",
        positive_components,
        assert_separated=True,
    )

    keys_by_member = class_key_by_member(full_quotient)
    left_id, right_id = (mc_payload.get("bracketing_in_quotient") or {}).get("left_right_records") or [None, None]
    if left_id not in keys_by_member or right_id not in keys_by_member:
        raise RuntimeError("left_right_records are missing from quotient_S_mod_M member keys")

    left_key = clone_jsonable(keys_by_member[str(left_id)])
    right_key = clone_jsonable(left_key)
    right_key["bracketing"] = clone_jsonable(keys_by_member[str(right_id)]["bracketing"])
    left_components = flatten_key(left_key)
    right_components = flatten_key(right_key)
    equality_values = {
        path: left_components[path] == right_components[path]
        for path in sorted(set(left_components) | set(right_components))
    }
    negative_case = run_solver_case(
        "negative_drop_bracketing_erasure_collision",
        equality_values,
        drop_prefixes=("bracketing.",),
        assert_full_equal=False,
        assert_drop_equal=True,
    )

    full_collision_case = run_solver_case(
        "control_full_encoding_rejects_bracketing_collision",
        equality_values,
        assert_full_equal=True,
    )

    drop_control = (mc_payload.get("negative_controls") or {}).get("drop_bracketing") or {}
    gate_eligible = gate_payload.get("eligible_consumers") or []
    gate_blocked = gate_payload.get("blocked_consumers") or gate_payload.get("blocked_downstream_consumers") or []

    finite_input_object = {
        "field": "quotient_relation",
        "tool": "cvc5",
        "api_surface": "Solver, Boolean terms, EQUAL/AND/OR/NOT/IMPLIES finite constraints",
        "consumed_member_for_positive_duplicate": positive_member,
        "consumed_positive_class_id": positive_class.get("class_id"),
        "positive_full_probe_key_sha256": stable_sha256(positive_key),
        "drop_bracketing_left_record": left_id,
        "drop_bracketing_right_bracketing_slice_record": right_id,
        "drop_bracketing_fixture_note": (
            "right fixture copies the left consumed full key and replaces only the "
            "bracketing component with the consumed right-record bracketing slice"
        ),
        "component_paths": sorted(left_components),
    }
    output_object = {
        "positive_case": positive_case,
        "negative_case": negative_case,
        "full_collision_control_case": full_collision_case,
        "observable": "SAT/UNSAT over finite quotient equality components derived from consumed quotient_relation keys",
    }
    positive = {
        "consumed_quotient_relation_present": check(
            "consumed_quotient_relation_present",
            isinstance(quotient_relation, dict) and bool(quotient_relation),
            expected=True,
            observed=bool(quotient_relation),
            reason="The probe must consume the explicit M(C) v1 quotient_relation field.",
        ),
        "identical_full_key_separation_unsat": check(
            "identical_full_key_separation_unsat",
            positive_case["unsat"] is True,
            expected="unsat",
            observed=positive_case["result"],
            reason="Two finite records with identical full probe-key components cannot be separated by the encoded quotient equality rule.",
        ),
        "positive_fixture_has_components": check(
            "positive_fixture_has_components",
            positive_case["component_count"] > 0,
            expected="non-empty full finite probe key",
            observed=positive_case["component_count"],
            reason="The cvc5 claim must be carried by actual finite key components, not an empty tautology.",
        ),
    }
    negative = {
        "drop_bracketing_erasure_counterexample_sat": check(
            "drop_bracketing_erasure_counterexample_sat",
            negative_case["sat"] is True and "bracketing.label" in negative_case["false_components"],
            expected="sat with bracketing component erased",
            observed={"result": negative_case["result"], "false_components": negative_case["false_components"]},
            reason="Dropping bracketing creates a satisfiable false-equality/collision control rather than a decorative contradiction.",
        ),
        "full_encoding_rejects_bracketing_collision_unsat": check(
            "full_encoding_rejects_bracketing_collision_unsat",
            full_collision_case["unsat"] is True,
            expected="unsat",
            observed=full_collision_case["result"],
            reason="The same bracketing-different fixture cannot be equal under the full quotient encoding.",
        ),
        "consumed_drop_bracketing_control_flipped": check(
            "consumed_drop_bracketing_control_flipped",
            drop_control.get("all_engines_flip") is True,
            expected=True,
            observed=drop_control.get("all_engines_flip"),
            reason="The finite fixture is tied to the consumed v1 drop_bracketing control.",
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
        "strong_consumers_still_blocked": check(
            "strong_consumers_still_blocked",
            set(STRONG_CONSUMERS) <= set(gate_blocked) <= set(STRONG_CONSUMERS),
            expected=STRONG_CONSUMERS,
            observed=gate_blocked,
            reason="The consumer gate must not expose any strong downstream consumer.",
        ),
        "stage_movement_forbidden": check(
            "stage_movement_forbidden",
            gate_payload.get("stage_movement_allowed") is False,
            expected=False,
            observed=gate_payload.get("stage_movement_allowed"),
            reason="This probe must not move the ladder stage.",
        ),
        "promotion_and_formal_admission_forbidden": check(
            "promotion_and_formal_admission_forbidden",
            promotion_allowed is False and formal_admission_allowed is False,
            expected={"promotion_allowed": False, "formal_admission_allowed": False},
            observed={"promotion_allowed": promotion_allowed, "formal_admission_allowed": formal_admission_allowed},
            reason="The result must stay pre-lego fit evidence only.",
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
            "Rerun this exact source after the sim-stack cvc5 Solver Boolean API is "
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
    mc_validation = validate_result_path(MC_V1_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True)
    gate_validation = validate_result_path(CONSUMER_GATE_RESULT_PATH, root=ROOT, strict_scope=True, require_run_boundary=True)

    probe = cvc5_probe(mc_payload, gate_payload)
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
        "claim": "cvc5 can carry a bounded finite quotient_relation fixture for the exact M(C) v1 field after the consumer gate",
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
        },
        "receipt_schema_validation": {
            "mc_v1_envelope_strict": mc_validation,
            "consumer_gate_strict": gate_validation,
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
        write_blocked_reason("cvc5 API is not importable in the sim-stack interpreter", str(exc))
        print(f"BLOCKED cvc5_import error={exc}")
        return 2
    except Exception as exc:
        if "cvc5" in traceback.format_exc().lower():
            write_blocked_reason("cvc5 API is not usable for the requested Boolean Solver surface", f"{type(exc).__name__}: {exc}")
            print(f"BLOCKED cvc5_usable error={type(exc).__name__}: {exc}")
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
