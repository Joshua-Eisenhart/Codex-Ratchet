#!/usr/bin/env python3
"""Solver-free validation and malformed-input tests for the dual-SMT scout."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC_PATH = HERE / "spec.json"
OBJECT_CARD_PATH = HERE / "wizard_v4_3_object_card.json"
Z3_SOURCE = HERE / "dual_ratchet_four_count_nonforcing_smt_v0_z3.py"
CVC5_SOURCE = HERE / "dual_ratchet_four_count_nonforcing_smt_v0_cvc5.py"
DEFAULT_Z3 = HERE / "results" / "z3_raw_solver_receipt.json"
DEFAULT_CVC5 = HERE / "results" / "cvc5_raw_solver_receipt.json"
DEFAULT_OUTPUT = HERE / "results" / "agreement_validation.json"
DEFAULT_SELFTEST_OUTPUT = HERE / "results" / "malformed_input_selftest.json"

STATE_COUNT = 9
LENGTHS = list(range(2, 9))
CLASSIFICATION = "scratch_diagnostic"
classification = CLASSIFICATION
promotion_allowed = False
formal_admission_allowed = False
SIM_EXECUTION_KIND = "nonclassical"
TOOL_MANIFEST = {
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing solver-free JSON schema checks, finite model replay, hash verification, and malformed-input mutation tests",
    }
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "load_bearing"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO))


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def error(errors: list[dict[str, str]], code: str, message: str, path: str) -> None:
    errors.append({"code": code, "message": message, "path": path})


def run_word(
    word: list[str],
    sign: str,
    tables: dict[str, dict[str, list[int]]],
    start: int,
) -> list[int]:
    states = [start]
    for work in word:
        states.append(tables[sign][work][states[-1]])
    return states


def candidate_holds(
    scenario_id: str,
    model: dict[str, Any],
) -> bool:
    word = model["word"]
    states = model["states"]
    sign = model["shared_axis6_sign"]
    tables = model["transition_tables"]
    start = states[0]
    selected = tables[sign]
    commutator_witnesses = {
        state
        for state in range(STATE_COUNT)
        if selected["geometry"][selected["entropy"][state]]
        != selected["entropy"][selected["geometry"][state]]
    }
    if scenario_id == "A1_cyclic_alternation":
        return all(word[index] != word[(index + 1) % len(word)] for index in range(len(word)))
    if scenario_id == "A2_every_leg_primary_progress":
        return all(
            states[index] // 3 != states[index + 1] // 3
            if work == "geometry"
            else states[index] % 3 != states[index + 1] % 3
            for index, work in enumerate(word)
        )
    if scenario_id == "A3_simple_phase_cycle":
        return len(set(states[:-1])) == len(states) - 1
    if scenario_id == "A4_no_early_return":
        return all(state != start for state in states[1:-1])
    if scenario_id == "A5_noncommutation_witness_on_cycle":
        return any(state in commutator_witnesses for state in states[:-1])
    if scenario_id == "A6_opposite_sign_breaks_closure":
        opposite = "down" if sign == "up" else "up"
        return run_word(word, opposite, tables, start)[-1] != start
    if scenario_id == "A7_selected_maps_bijective":
        expected = list(range(STATE_COUNT))
        return all(sorted(selected[work]) == expected for work in ("geometry", "entropy"))
    if scenario_id == "A8_single_kind_flip_breaks_closure":
        for index in range(len(word)):
            changed = list(word)
            changed[index] = "entropy" if changed[index] == "geometry" else "geometry"
            if run_word(changed, sign, tables, start)[-1] == start:
                return False
        return True
    if scenario_id == "A9_single_leg_deletion_breaks_closure":
        return all(
            run_word(word[:index] + word[index + 1 :], sign, tables, start)[-1] != start
            for index in range(len(word))
        )
    if scenario_id == "A10_reverse_word_breaks_closure":
        return run_word(list(reversed(word)), sign, tables, start)[-1] != start
    raise ValueError(f"unknown candidate scenario: {scenario_id}")


def forbidden_control_holds(scenario_id: str, model: dict[str, Any]) -> bool:
    word = model["word"]
    if scenario_id == "F1_exactly_two_of_each_kind":
        return word.count("geometry") == 2 and word.count("entropy") == 2
    if scenario_id == "F2_binary_x_binary_exact_coverage":
        roles = model.get("auxiliary", {}).get("binary_roles")
        if not isinstance(roles, list) or len(roles) != len(word):
            return False
        pairs = [(work, role) for work, role in zip(word, roles)]
        expected = {
            ("geometry", "zero"),
            ("geometry", "one"),
            ("entropy", "zero"),
            ("entropy", "one"),
        }
        return len(pairs) == 4 and set(pairs) == expected and len(set(pairs)) == 4
    if scenario_id == "F3_explicit_four_step_word":
        return word == ["geometry", "entropy", "geometry", "entropy"]
    if scenario_id == "F4_exactly_four_legs":
        return len(word) == 4
    raise ValueError(f"unknown forbidden scenario: {scenario_id}")


def validate_model(
    model: dict[str, Any],
    length: int,
    scenario_id: str,
    category: str,
    path: str,
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    word = model.get("word")
    states = model.get("states")
    sign = model.get("shared_axis6_sign")
    leg_signs = model.get("leg_axis6_signs")
    tables = model.get("transition_tables")
    if model.get("length") != length:
        error(errors, "model.length", "model length does not match query length", path)
    if not isinstance(word, list) or len(word) != length or any(
        work not in {"geometry", "entropy"} for work in word
    ):
        error(errors, "model.word", "word must contain exactly length geometry/entropy labels", path)
        return errors
    if set(word) != {"geometry", "entropy"}:
        error(errors, "model.both_kinds", "both work kinds must be used", path)
    if sign not in {"up", "down"}:
        error(errors, "model.shared_sign", "shared sign must be up or down", path)
        return errors
    if leg_signs != [sign] * length:
        error(errors, "model.axis6_signs", "every leg sign must equal the shared sign", path)
    if not isinstance(states, list) or len(states) != length + 1 or any(
        not isinstance(state, int) or isinstance(state, bool) or not 0 <= state < STATE_COUNT
        for state in states
    ):
        error(errors, "model.states", "states must be length+1 integers on the nine-state carrier", path)
        return errors
    if not isinstance(tables, dict):
        error(errors, "model.tables", "transition_tables must be an object", path)
        return errors
    try:
        for sign_label in ("down", "up"):
            for work in ("geometry", "entropy"):
                values = tables[sign_label][work]
                if len(values) != STATE_COUNT or any(
                    not isinstance(value, int) or isinstance(value, bool) or not 0 <= value < STATE_COUNT
                    for value in values
                ):
                    raise ValueError(f"invalid table {sign_label}/{work}")
    except (KeyError, TypeError, ValueError) as exc:
        error(errors, "model.tables", str(exc), path)
        return errors

    replayed = run_word(word, sign, tables, states[0])
    if replayed != states or model.get("replayed_states") != replayed:
        error(errors, "model.transition_trace", "serialized states do not replay through the selected maps", path)
    if states[-1] != states[0]:
        error(errors, "model.closure", "final state does not equal initial state", path)

    selected = tables[sign]
    distinct_witnesses = [
        state
        for state in range(STATE_COUNT)
        if selected["geometry"][state] != selected["entropy"][state]
    ]
    if not distinct_witnesses or model.get("selected_maps_distinct_witnesses") != distinct_witnesses:
        error(errors, "model.distinct_maps", "selected work maps lack or misreport a distinctness witness", path)
    commutator_witnesses = [
        state
        for state in range(STATE_COUNT)
        if selected["geometry"][selected["entropy"][state]]
        != selected["entropy"][selected["geometry"][state]]
    ]
    if not commutator_witnesses or model.get("commutator_witnesses") != commutator_witnesses:
        error(errors, "model.noncommutation", "selected maps lack or misreport a commutator witness", path)

    geometry_progress = [
        index
        for index, work in enumerate(word)
        if work == "geometry" and states[index] // 3 != states[index + 1] // 3
    ]
    entropy_progress = [
        index
        for index, work in enumerate(word)
        if work == "entropy" and states[index] % 3 != states[index + 1] % 3
    ]
    if not geometry_progress or model.get("geometry_progress_legs") != geometry_progress:
        error(errors, "model.geometry_progress", "geometry progress is absent or misreported", path)
    if not entropy_progress or model.get("entropy_progress_legs") != entropy_progress:
        error(errors, "model.entropy_progress", "entropy progress is absent or misreported", path)

    expected_coordinates = [
        {"geometry": state // 3, "entropy": state % 3} for state in states
    ]
    if model.get("state_coordinates") != expected_coordinates:
        error(errors, "model.coordinates", "state-coordinate projection is malformed", path)
    if model.get("countermodel_to_forced_four") is not (length != 4):
        error(errors, "model.countermodel_flag", "non-four countermodel flag is incorrect", path)

    if category == "candidate_addition" and not candidate_holds(scenario_id, model):
        error(errors, "model.candidate_axiom", f"model does not satisfy {scenario_id}", path)
    if category == "forbidden_control" and not forbidden_control_holds(scenario_id, model):
        error(errors, "model.forbidden_control", f"model does not satisfy {scenario_id}", path)
    return errors


def validate_scenario(
    scenario: dict[str, Any],
    scenario_id: str,
    category: str,
    contaminated: bool,
    solver_name: str,
) -> tuple[list[dict[str, str]], int]:
    errors: list[dict[str, str]] = []
    model_count = 0
    root = f"{solver_name}.{scenario_id}"
    if scenario.get("scenario_id") != scenario_id:
        error(errors, "scenario.id", "scenario id mismatch", root)
    if scenario.get("category") != category:
        error(errors, "scenario.category", "scenario category mismatch", root)
    if scenario.get("cardinality_contaminated") is not contaminated:
        error(errors, "scenario.cardinality_contamination", "cardinality contamination flag mismatch", root)
    queries = scenario.get("queries")
    if not isinstance(queries, list):
        error(errors, "scenario.queries", "queries must be a list", root)
        return errors, model_count
    query_lengths = [row.get("length") for row in queries if isinstance(row, dict)]
    if query_lengths != LENGTHS:
        error(errors, "scenario.query_lengths", "queries must cover ordered lengths 2..8 exactly once", root)
    admitted = []
    for query in queries:
        if not isinstance(query, dict):
            error(errors, "query.shape", "query must be an object", root)
            continue
        length = query.get("length")
        status = query.get("status")
        query_path = f"{root}.L{length}"
        if status not in {"sat", "unsat"}:
            error(errors, "query.status", "query status must be sat or unsat", query_path)
            continue
        if not isinstance(query.get("assertion_count"), int) or query["assertion_count"] <= 0:
            error(errors, "query.assertion_count", "assertion count must be a positive integer", query_path)
        if status == "sat":
            admitted.append(length)
            model = query.get("model")
            if not isinstance(model, dict):
                error(errors, "query.model_missing", "SAT query must include a model", query_path)
            elif isinstance(length, int):
                model_errors = validate_model(model, length, scenario_id, category, query_path)
                errors.extend(model_errors)
                model_count += 1
        elif "model" in query:
            error(errors, "query.unsat_has_model", "UNSAT query must not include a model", query_path)

    expected_nonfour = [length for length in admitted if length != 4]
    if scenario.get("admitted_lengths") != admitted:
        error(errors, "scenario.admitted_lengths", "admitted length summary differs from query statuses", root)
    if scenario.get("nonfour_countermodel_lengths") != expected_nonfour:
        error(errors, "scenario.nonfour_lengths", "non-four countermodel summary is wrong", root)
    if scenario.get("four_admitted") is not (4 in admitted):
        error(errors, "scenario.four_admitted", "four-admitted flag is wrong", root)
    if scenario.get("forces_exactly_four_in_2_8_nonvacuously") is not (admitted == [4]):
        error(errors, "scenario.forces_four", "force-four summary is wrong", root)
    if scenario.get("all_queries_decided") is not all(
        isinstance(row, dict) and row.get("status") in {"sat", "unsat"} for row in queries
    ):
        error(errors, "scenario.decided", "all-queries-decided flag is wrong", root)
    return errors, model_count


def validate_source_locks(spec: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for index, lock in enumerate(spec.get("source_locks", [])):
        path = REPO / lock.get("path", "")
        lock_path = f"spec.source_locks[{index}]"
        if not path.is_file():
            error(errors, "source_lock.missing", f"missing source lock {path}", lock_path)
        elif sha256(path) != lock.get("sha256"):
            error(errors, "source_lock.hash", f"source lock hash changed for {path}", lock_path)
    return errors


def validate_receipt(
    receipt: dict[str, Any],
    solver_name: str,
    solver_source: Path,
    spec: dict[str, Any],
) -> tuple[list[dict[str, str]], int]:
    errors: list[dict[str, str]] = []
    model_count = 0
    expected_schema = f"codex_ratchet.dual_ratchet_four_count_nonforcing_smt_v0.{solver_name}_raw.v1"
    if receipt.get("schema") != expected_schema:
        error(errors, "receipt.schema", "raw receipt schema mismatch", solver_name)
    if receipt.get("sim_id") != spec.get("sim_id"):
        error(errors, "receipt.sim_id", "sim id mismatch", solver_name)
    if receipt.get("classification") != CLASSIFICATION:
        error(errors, "receipt.classification", "classification must be scratch_diagnostic", solver_name)
    for field in ("promotion_allowed", "formal_admission_allowed", "stage_movement_allowed"):
        if receipt.get(field) is not False:
            error(errors, f"receipt.{field}", f"{field} must be false", solver_name)
    if receipt.get("reads_peer_result") is not False:
        error(errors, "receipt.peer_read", "solver receipt must not read its peer", solver_name)
    solver = receipt.get("solver", {})
    if solver.get("name") != solver_name or not solver.get("version"):
        error(errors, "receipt.solver", "solver identity/version missing or wrong", solver_name)
    source_hashes = receipt.get("source_hashes", {})
    expected_hashes = {
        relative(SPEC_PATH): sha256(SPEC_PATH),
        relative(OBJECT_CARD_PATH): sha256(OBJECT_CARD_PATH),
        relative(solver_source): sha256(solver_source),
    }
    if source_hashes != expected_hashes:
        error(errors, "receipt.source_hashes", "source hashes do not match current packet", solver_name)
    premise = receipt.get("premise_audit", {})
    if any(
        premise.get(field) is not False
        for field in (
            "desired_cardinality_supplied_to_clean_scenarios",
            "source_operator_names_supplied",
            "source_16x4_schedule_supplied",
        )
    ):
        error(errors, "receipt.premise_audit", "clean scenarios received a forbidden premise", solver_name)

    baseline = receipt.get("baseline")
    if not isinstance(baseline, dict):
        error(errors, "receipt.baseline", "missing baseline scenario", solver_name)
    else:
        scenario_errors, count = validate_scenario(baseline, "baseline", "baseline", False, solver_name)
        errors.extend(scenario_errors)
        model_count += count

    expected_candidates = [row["id"] for row in spec["candidate_additional_axioms"]]
    candidates = receipt.get("candidate_additions")
    if not isinstance(candidates, dict) or set(candidates) != set(expected_candidates):
        error(errors, "receipt.candidate_registry", "candidate scenario registry mismatch", solver_name)
    else:
        for scenario_id in expected_candidates:
            scenario_errors, count = validate_scenario(
                candidates[scenario_id], scenario_id, "candidate_addition", False, solver_name
            )
            errors.extend(scenario_errors)
            model_count += count

    expected_forbidden = [row["id"] for row in spec["forbidden_cardinality_controls"]]
    forbidden = receipt.get("forbidden_cardinality_controls")
    if not isinstance(forbidden, dict) or set(forbidden) != set(expected_forbidden):
        error(errors, "receipt.forbidden_registry", "forbidden-control registry mismatch", solver_name)
    else:
        for scenario_id in expected_forbidden:
            scenario_errors, count = validate_scenario(
                forbidden[scenario_id], scenario_id, "forbidden_control", True, solver_name
            )
            errors.extend(scenario_errors)
            model_count += count

    if receipt.get("all_pass") is not True or receipt.get("summary", {}).get("all_queries_decided") is not True:
        error(errors, "receipt.all_pass", "raw solver receipt did not decide every query", solver_name)
    return errors, model_count


def scenario_map(receipt: dict[str, Any]) -> dict[str, dict[int, str]]:
    scenarios = {"baseline": receipt["baseline"]}
    scenarios.update(receipt["candidate_additions"])
    scenarios.update(receipt["forbidden_cardinality_controls"])
    return {
        scenario_id: {row["length"]: row["status"] for row in scenario["queries"]}
        for scenario_id, scenario in scenarios.items()
    }


def scenario_admitted_map(receipt: dict[str, Any], section: str) -> dict[str, list[int]]:
    return {
        scenario_id: row["admitted_lengths"]
        for scenario_id, row in receipt[section].items()
    }


def validate_pair(
    z3_receipt: dict[str, Any],
    cvc5_receipt: dict[str, Any],
    z3_path: Path,
    cvc5_path: Path,
) -> dict[str, Any]:
    spec = load(SPEC_PATH)
    z3_errors, z3_models = validate_receipt(z3_receipt, "z3", Z3_SOURCE, spec)
    cvc5_errors, cvc5_models = validate_receipt(cvc5_receipt, "cvc5", CVC5_SOURCE, spec)
    source_lock_errors = validate_source_locks(spec)
    projection_agrees = False
    projection_error: list[dict[str, str]] = []
    try:
        projection_agrees = scenario_map(z3_receipt) == scenario_map(cvc5_receipt)
    except (KeyError, TypeError) as exc:
        error(projection_error, "agreement.projection_shape", str(exc), "cross_solver")
    if not projection_agrees:
        error(
            projection_error,
            "agreement.status_projection",
            "Z3 and cvc5 SAT/UNSAT projections disagree",
            "cross_solver",
        )

    all_errors = [*source_lock_errors, *z3_errors, *cvc5_errors, *projection_error]
    baseline_admitted = z3_receipt.get("baseline", {}).get("admitted_lengths", [])
    clean_forcers = z3_receipt.get("summary", {}).get("clean_candidate_forcers", [])
    contaminated_forcers = z3_receipt.get("summary", {}).get(
        "cardinality_contaminated_forcers", []
    )
    baseline_has_nonfour = any(length != 4 for length in baseline_admitted)
    finite_nonforcing = bool(baseline_has_nonfour and not clean_forcers)
    only_contaminated_force = bool(finite_nonforcing and contaminated_forcers)
    if all_errors:
        scientific_verdict = "BLOCKED_VALIDATION_OR_SOLVER_DISAGREEMENT"
    elif only_contaminated_force:
        scientific_verdict = (
            "FINITE_COUNT_FREE_AXIOMS_NONFORCING_ONLY_CARDINALITY_CONTAMINATED_CONTROLS_FORCE_FOUR"
        )
    elif clean_forcers:
        scientific_verdict = "FINITE_CLEAN_CANDIDATE_FORCES_FOUR_WITHIN_DECLARED_SCOPE"
    elif not baseline_admitted:
        scientific_verdict = "INCONCLUSIVE_BASELINE_INCONSISTENT"
    else:
        scientific_verdict = "FINITE_NONFORCING_WITHOUT_A_FORCING_CONTROL"

    checks = {
        "source_locks_match": not source_lock_errors,
        "z3_receipt_valid": not z3_errors,
        "cvc5_receipt_valid": not cvc5_errors,
        "all_sat_models_replayed": not z3_errors and not cvc5_errors,
        "all_lengths_2_through_8_decided": all(
            row.get("summary", {}).get("all_queries_decided") is True
            for row in (z3_receipt, cvc5_receipt)
        ),
        "solver_status_projections_agree": projection_agrees,
        "both_solvers_independent_no_peer_reads": z3_receipt.get("reads_peer_result") is False
        and cvc5_receipt.get("reads_peer_result") is False,
        "classification_scratch_diagnostic": z3_receipt.get("classification")
        == cvc5_receipt.get("classification")
        == CLASSIFICATION,
        "promotion_and_admission_false": all(
            receipt.get("promotion_allowed") is False
            and receipt.get("formal_admission_allowed") is False
            for receipt in (z3_receipt, cvc5_receipt)
        ),
    }
    all_pass = all(checks.values()) and not all_errors
    return {
        "schema": "codex_ratchet.dual_ratchet_four_count_nonforcing_smt_v0.agreement.v1",
        "sim_id": spec["sim_id"],
        "classification": CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "accepted_status_label": "passes local rerun" if all_pass else "blocked",
        "solver_versions": {
            "z3": z3_receipt.get("solver", {}).get("version"),
            "cvc5": cvc5_receipt.get("solver", {}).get("version"),
        },
        "source_hashes": {
            relative(SPEC_PATH): sha256(SPEC_PATH),
            relative(OBJECT_CARD_PATH): sha256(OBJECT_CARD_PATH),
            relative(Z3_SOURCE): sha256(Z3_SOURCE),
            relative(CVC5_SOURCE): sha256(CVC5_SOURCE),
            relative(Path(__file__).resolve()): sha256(Path(__file__).resolve()),
            "raw_solver_receipt:z3": sha256(z3_path),
            "raw_solver_receipt:cvc5": sha256(cvc5_path),
        },
        "checks": checks,
        "errors": all_errors,
        "validation_counts": {
            "scenario_count_per_solver": 1
            + len(spec["candidate_additional_axioms"])
            + len(spec["forbidden_cardinality_controls"]),
            "query_count_per_solver": (
                1
                + len(spec["candidate_additional_axioms"])
                + len(spec["forbidden_cardinality_controls"])
            )
            * len(LENGTHS),
            "validated_sat_models": {"z3": z3_models, "cvc5": cvc5_models},
        },
        "measured": {
            "baseline_admitted_lengths": baseline_admitted,
            "candidate_admitted_lengths": scenario_admitted_map(
                z3_receipt, "candidate_additions"
            ),
            "forbidden_control_admitted_lengths": scenario_admitted_map(
                z3_receipt, "forbidden_cardinality_controls"
            ),
            "clean_candidate_forcers": clean_forcers,
            "cardinality_contaminated_forcers": contaminated_forcers,
            "baseline_has_nonfour_countermodels": baseline_has_nonfour,
            "finite_nonforcing": finite_nonforcing,
            "only_cardinality_contaminated_controls_force_four": only_contaminated_force,
        },
        "scientific_verdict": scientific_verdict,
        "precise_meaning_for_16x4": spec["schedule_16x4_boundary"],
        "claim_ceiling": spec["claim_ceiling"],
        "blocked_consumers": spec["blocked_consumers"],
        "all_pass": all_pass,
    }


def run_selftest(
    z3_receipt: dict[str, Any],
    cvc5_receipt: dict[str, Any],
    z3_path: Path,
    cvc5_path: Path,
) -> dict[str, Any]:
    cases = []

    def check_case(name: str, mutated_z3: dict[str, Any], mutated_cvc5: dict[str, Any], expected: str) -> None:
        receipt = validate_pair(mutated_z3, mutated_cvc5, z3_path, cvc5_path)
        codes = sorted({row["code"] for row in receipt["errors"]})
        cases.append(
            {
                "name": name,
                "expected_error_code": expected,
                "observed_error_codes": codes,
                "validator_rejected": receipt["all_pass"] is False,
                "pass": receipt["all_pass"] is False and expected in codes,
            }
        )

    missing_length = copy.deepcopy(z3_receipt)
    missing_length["baseline"]["queries"].pop()
    check_case("missing_length_query", missing_length, cvc5_receipt, "scenario.query_lengths")

    bad_trace = copy.deepcopy(z3_receipt)
    model = next(row["model"] for row in bad_trace["baseline"]["queries"] if row["status"] == "sat")
    model["states"][1] = (model["states"][1] + 1) % STATE_COUNT
    check_case("invalid_transition_trace", bad_trace, cvc5_receipt, "model.transition_trace")

    bad_sign = copy.deepcopy(z3_receipt)
    model = next(row["model"] for row in bad_sign["baseline"]["queries"] if row["status"] == "sat")
    model["leg_axis6_signs"][0] = "down" if model["shared_axis6_sign"] == "up" else "up"
    check_case("mixed_axis6_signs", bad_sign, cvc5_receipt, "model.axis6_signs")

    unknown = copy.deepcopy(z3_receipt)
    unknown["baseline"]["queries"][0]["status"] = "unknown"
    unknown["baseline"]["queries"][0].pop("model", None)
    check_case("unknown_solver_status", unknown, cvc5_receipt, "query.status")

    disagreement = copy.deepcopy(cvc5_receipt)
    first = disagreement["baseline"]["queries"][0]
    first["status"] = "unsat" if first["status"] == "sat" else "sat"
    first.pop("model", None)
    check_case(
        "cross_solver_status_disagreement",
        z3_receipt,
        disagreement,
        "agreement.status_projection",
    )

    laundered = copy.deepcopy(z3_receipt)
    laundered["forbidden_cardinality_controls"]["F1_exactly_two_of_each_kind"][
        "cardinality_contaminated"
    ] = False
    check_case(
        "cardinality_contamination_laundered",
        laundered,
        cvc5_receipt,
        "scenario.cardinality_contamination",
    )

    all_pass = all(row["pass"] for row in cases)
    return {
        "schema": "codex_ratchet.dual_ratchet_four_count_nonforcing_smt_v0.malformed_selftest.v1",
        "sim_id": load(SPEC_PATH)["sim_id"],
        "classification": CLASSIFICATION,
        "promotion_allowed": False,
        "selftest_kind": "in_memory_receipt_corruption",
        "cases": cases,
        "case_count": len(cases),
        "all_pass": all_pass,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--z3", type=Path, default=DEFAULT_Z3)
    parser.add_argument("--cvc5", type=Path, default=DEFAULT_CVC5)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--self-test-output", type=Path, default=DEFAULT_SELFTEST_OUTPUT)
    args = parser.parse_args()
    z3_receipt = load(args.z3)
    cvc5_receipt = load(args.cvc5)
    if args.self_test:
        receipt = run_selftest(z3_receipt, cvc5_receipt, args.z3, args.cvc5)
        write_json(args.self_test_output, receipt)
        print(
            json.dumps(
                {
                    "mode": "malformed_input_selftest",
                    "case_count": receipt["case_count"],
                    "all_pass": receipt["all_pass"],
                    "output": str(args.self_test_output),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if receipt["all_pass"] else 1

    receipt = validate_pair(z3_receipt, cvc5_receipt, args.z3, args.cvc5)
    write_json(args.output, receipt)
    print(
        json.dumps(
            {
                "mode": "agreement_validation",
                "scientific_verdict": receipt["scientific_verdict"],
                "baseline_admitted_lengths": receipt["measured"]["baseline_admitted_lengths"],
                "clean_candidate_forcers": receipt["measured"]["clean_candidate_forcers"],
                "cardinality_contaminated_forcers": receipt["measured"][
                    "cardinality_contaminated_forcers"
                ],
                "validated_sat_models": receipt["validation_counts"]["validated_sat_models"],
                "all_pass": receipt["all_pass"],
                "output": str(args.output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if receipt["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
