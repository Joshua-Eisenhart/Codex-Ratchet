#!/usr/bin/env python3
"""Independent cvc5 encoding for the finite count-free dual-ratchet scout."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC_PATH = HERE / "spec.json"
OBJECT_CARD_PATH = HERE / "wizard_v4_3_object_card.json"
DEFAULT_OUTPUT = HERE / "results" / "cvc5_raw_solver_receipt.json"

STATE_COUNT = 9
COORDINATE_SIZE = 3
GEOMETRY = True
ENTROPY = False
UP = True
DOWN = False

CANDIDATE_IDS = (
    "A1_cyclic_alternation",
    "A2_every_leg_primary_progress",
    "A3_simple_phase_cycle",
    "A4_no_early_return",
    "A5_noncommutation_witness_on_cycle",
    "A6_opposite_sign_breaks_closure",
    "A7_selected_maps_bijective",
    "A8_single_kind_flip_breaks_closure",
    "A9_single_leg_deletion_breaks_closure",
    "A10_reverse_word_breaks_closure",
)
FORBIDDEN_IDS = (
    "F1_exactly_two_of_each_kind",
    "F2_binary_x_binary_exact_coverage",
    "F3_explicit_four_step_word",
    "F4_exactly_four_legs",
)

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

TOOL_MANIFEST = {
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing independent SAT/UNSAT search over finite total work maps, "
            "ordered traces, closure, and one-at-a-time axiom variants"
        ),
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive preregistration loading, hashing, model projection, and JSON receipt output",
    },
}
TOOL_INTEGRATION_DEPTH = {"cvc5": "load_bearing", "python_stdlib": "supportive"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO))


def run_word(
    word: list[str],
    sign: str,
    transition_tables: dict[str, dict[str, list[int]]],
    start: int,
) -> list[int]:
    states = [start]
    for work in word:
        states.append(transition_tables[sign][work][states[-1]])
    return states


class CVC5Query:
    """One fresh cvc5 solver for one scenario and one fixed query length."""

    def __init__(self, length: int, scenario_id: str) -> None:
        self.length = length
        self.scenario_id = scenario_id
        self.solver = cvc5.Solver()
        self.solver.setLogic("QF_LIA")
        self.solver.setOption("produce-models", "true")
        self.bool_sort = self.solver.getBooleanSort()
        self.int_sort = self.solver.getIntegerSort()
        self.true = self.solver.mkBoolean(True)
        self.false = self.solver.mkBoolean(False)
        self.zero = self.solver.mkInteger(0)
        self.eight = self.solver.mkInteger(STATE_COUNT - 1)
        self.assertion_count = 0
        self.kinds = [self.solver.mkConst(self.bool_sort, f"kind_{index}") for index in range(length)]
        self.leg_signs = [
            self.solver.mkConst(self.bool_sort, f"leg_sign_{index}") for index in range(length)
        ]
        self.shared_sign = self.solver.mkConst(self.bool_sort, "shared_sign")
        self.states = [
            self.solver.mkConst(self.int_sort, f"state_{index}") for index in range(length + 1)
        ]
        self.tables = {
            (work, sign, state): self.solver.mkConst(
                self.int_sort,
                f"next_{'G' if work else 'E'}_{'up' if sign else 'down'}_{state}",
            )
            for work in (ENTROPY, GEOMETRY)
            for sign in (DOWN, UP)
            for state in range(STATE_COUNT)
        }
        self.binary_roles: list[cvc5.Term] | None = None
        self._add_baseline()

    def add(self, *formulas: cvc5.Term) -> None:
        for formula in formulas:
            self.solver.assertFormula(formula)
            self.assertion_count += 1

    def boolean(self, value: bool) -> cvc5.Term:
        return self.true if value else self.false

    def integer(self, value: int) -> cvc5.Term:
        return self.solver.mkInteger(value)

    def equal(self, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
        return self.solver.mkTerm(Kind.EQUAL, left, right)

    def not_(self, term: cvc5.Term) -> cvc5.Term:
        return self.solver.mkTerm(Kind.NOT, term)

    def different(self, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
        return self.not_(self.equal(left, right))

    def and_(self, terms: list[cvc5.Term]) -> cvc5.Term:
        if not terms:
            return self.true
        if len(terms) == 1:
            return terms[0]
        return self.solver.mkTerm(Kind.AND, *terms)

    def or_(self, terms: list[cvc5.Term]) -> cvc5.Term:
        if not terms:
            return self.false
        if len(terms) == 1:
            return terms[0]
        return self.solver.mkTerm(Kind.OR, *terms)

    def ite(self, condition: cvc5.Term, when_true: cvc5.Term, when_false: cvc5.Term) -> cvc5.Term:
        return self.solver.mkTerm(Kind.ITE, condition, when_true, when_false)

    def sum_(self, terms: list[cvc5.Term]) -> cvc5.Term:
        if not terms:
            return self.zero
        if len(terms) == 1:
            return terms[0]
        return self.solver.mkTerm(Kind.ADD, *terms)

    def add_state_bounds(self, states: list[cvc5.Term]) -> None:
        for state in states:
            self.add(
                self.solver.mkTerm(Kind.GEQ, state, self.zero),
                self.solver.mkTerm(Kind.LEQ, state, self.eight),
            )

    def coordinate(self, state: cvc5.Term, geometry: bool) -> cvc5.Term:
        values = [index // COORDINATE_SIZE if geometry else index % COORDINATE_SIZE for index in range(STATE_COUNT)]
        expression = self.integer(values[-1])
        for index in reversed(range(STATE_COUNT - 1)):
            expression = self.ite(
                self.equal(state, self.integer(index)),
                self.integer(values[index]),
                expression,
            )
        return expression

    def lookup(self, work: cvc5.Term, sign: cvc5.Term, state: cvc5.Term) -> cvc5.Term:
        expression = self.tables[(ENTROPY, DOWN, STATE_COUNT - 1)]
        for work_value in (ENTROPY, GEOMETRY):
            for sign_value in (DOWN, UP):
                for state_value in range(STATE_COUNT):
                    condition = self.and_(
                        [
                            self.equal(work, self.boolean(work_value)),
                            self.equal(sign, self.boolean(sign_value)),
                            self.equal(state, self.integer(state_value)),
                        ]
                    )
                    expression = self.ite(
                        condition,
                        self.tables[(work_value, sign_value, state_value)],
                        expression,
                    )
        return expression

    def commutator_differs(self, state: cvc5.Term) -> cvc5.Term:
        entropy_then_geometry = self.lookup(
            self.boolean(GEOMETRY),
            self.shared_sign,
            self.lookup(self.boolean(ENTROPY), self.shared_sign, state),
        )
        geometry_then_entropy = self.lookup(
            self.boolean(ENTROPY),
            self.shared_sign,
            self.lookup(self.boolean(GEOMETRY), self.shared_sign, state),
        )
        return self.different(entropy_then_geometry, geometry_then_entropy)

    def primary_progress(self, index: int) -> cvc5.Term:
        geometry_changed = self.different(
            self.coordinate(self.states[index], True),
            self.coordinate(self.states[index + 1], True),
        )
        entropy_changed = self.different(
            self.coordinate(self.states[index], False),
            self.coordinate(self.states[index + 1], False),
        )
        return self.ite(self.kinds[index], geometry_changed, entropy_changed)

    def new_trace(self, prefix: str, leg_count: int) -> list[cvc5.Term]:
        trace = [
            self.solver.mkConst(self.int_sort, f"{prefix}_{index}") for index in range(leg_count + 1)
        ]
        self.add_state_bounds(trace)
        return trace

    def _add_baseline(self) -> None:
        self.add_state_bounds(list(self.tables.values()))
        self.add_state_bounds(self.states)
        for index in range(self.length):
            self.add(self.equal(self.leg_signs[index], self.shared_sign))
            self.add(
                self.equal(
                    self.states[index + 1],
                    self.lookup(self.kinds[index], self.leg_signs[index], self.states[index]),
                )
            )

        self.add(self.or_(self.kinds))
        self.add(self.or_([self.not_(kind) for kind in self.kinds]))
        self.add(
            self.or_(
                [
                    self.different(
                        self.lookup(self.boolean(GEOMETRY), self.shared_sign, self.integer(state)),
                        self.lookup(self.boolean(ENTROPY), self.shared_sign, self.integer(state)),
                    )
                    for state in range(STATE_COUNT)
                ]
            )
        )
        self.add(
            self.or_([self.commutator_differs(self.integer(state)) for state in range(STATE_COUNT)])
        )
        self.add(
            self.or_(
                [
                    self.and_(
                        [
                            self.kinds[index],
                            self.different(
                                self.coordinate(self.states[index], True),
                                self.coordinate(self.states[index + 1], True),
                            ),
                        ]
                    )
                    for index in range(self.length)
                ]
            )
        )
        self.add(
            self.or_(
                [
                    self.and_(
                        [
                            self.not_(self.kinds[index]),
                            self.different(
                                self.coordinate(self.states[index], False),
                                self.coordinate(self.states[index + 1], False),
                            ),
                        ]
                    )
                    for index in range(self.length)
                ]
            )
        )
        self.add(self.equal(self.states[-1], self.states[0]))

    def add_candidate(self, candidate_id: str) -> None:
        if candidate_id == "A1_cyclic_alternation":
            self.add(
                self.and_(
                    [
                        self.different(self.kinds[index], self.kinds[(index + 1) % self.length])
                        for index in range(self.length)
                    ]
                )
            )
        elif candidate_id == "A2_every_leg_primary_progress":
            self.add(self.and_([self.primary_progress(index) for index in range(self.length)]))
        elif candidate_id == "A3_simple_phase_cycle":
            self.add(self.solver.mkTerm(Kind.DISTINCT, *self.states[:-1]))
        elif candidate_id == "A4_no_early_return":
            self.add(
                self.and_([self.different(self.states[index], self.states[0]) for index in range(1, self.length)])
            )
        elif candidate_id == "A5_noncommutation_witness_on_cycle":
            self.add(self.or_([self.commutator_differs(state) for state in self.states[:-1]]))
        elif candidate_id == "A6_opposite_sign_breaks_closure":
            shadow = self.new_trace("opposite_sign", self.length)
            self.add(self.equal(shadow[0], self.states[0]))
            for index in range(self.length):
                self.add(
                    self.equal(
                        shadow[index + 1],
                        self.lookup(self.kinds[index], self.not_(self.shared_sign), shadow[index]),
                    )
                )
            self.add(self.different(shadow[-1], self.states[0]))
        elif candidate_id == "A7_selected_maps_bijective":
            for work in (ENTROPY, GEOMETRY):
                outputs = [
                    self.lookup(self.boolean(work), self.shared_sign, self.integer(state))
                    for state in range(STATE_COUNT)
                ]
                self.add(self.solver.mkTerm(Kind.DISTINCT, *outputs))
        elif candidate_id == "A8_single_kind_flip_breaks_closure":
            for flipped in range(self.length):
                shadow = self.new_trace(f"kind_flip_{flipped}", self.length)
                self.add(self.equal(shadow[0], self.states[0]))
                for index in range(self.length):
                    kind = self.not_(self.kinds[index]) if index == flipped else self.kinds[index]
                    self.add(
                        self.equal(
                            shadow[index + 1],
                            self.lookup(kind, self.shared_sign, shadow[index]),
                        )
                    )
                self.add(self.different(shadow[-1], self.states[0]))
        elif candidate_id == "A9_single_leg_deletion_breaks_closure":
            for deleted in range(self.length):
                kept = [index for index in range(self.length) if index != deleted]
                shadow = self.new_trace(f"delete_{deleted}", len(kept))
                self.add(self.equal(shadow[0], self.states[0]))
                for shadow_index, source_index in enumerate(kept):
                    self.add(
                        self.equal(
                            shadow[shadow_index + 1],
                            self.lookup(self.kinds[source_index], self.shared_sign, shadow[shadow_index]),
                        )
                    )
                self.add(self.different(shadow[-1], self.states[0]))
        elif candidate_id == "A10_reverse_word_breaks_closure":
            shadow = self.new_trace("reverse_word", self.length)
            self.add(self.equal(shadow[0], self.states[0]))
            for index, source_index in enumerate(reversed(range(self.length))):
                self.add(
                    self.equal(
                        shadow[index + 1],
                        self.lookup(self.kinds[source_index], self.shared_sign, shadow[index]),
                    )
                )
            self.add(self.different(shadow[-1], self.states[0]))
        else:
            raise ValueError(f"unknown candidate axiom: {candidate_id}")

    def add_forbidden_control(self, control_id: str) -> None:
        if control_id == "F1_exactly_two_of_each_kind":
            geometry_count = self.sum_([self.ite(kind, self.integer(1), self.zero) for kind in self.kinds])
            entropy_count = self.sum_([self.ite(kind, self.zero, self.integer(1)) for kind in self.kinds])
            self.add(self.equal(geometry_count, self.integer(2)))
            self.add(self.equal(entropy_count, self.integer(2)))
        elif control_id == "F2_binary_x_binary_exact_coverage":
            self.binary_roles = [
                self.solver.mkConst(self.bool_sort, f"binary_role_{index}") for index in range(self.length)
            ]
            for work in (ENTROPY, GEOMETRY):
                for role in (False, True):
                    count = self.sum_(
                        [
                            self.ite(
                                self.and_(
                                    [
                                        self.equal(kind, self.boolean(work)),
                                        self.equal(role_term, self.boolean(role)),
                                    ]
                                ),
                                self.integer(1),
                                self.zero,
                            )
                            for kind, role_term in zip(self.kinds, self.binary_roles)
                        ]
                    )
                    self.add(self.equal(count, self.integer(1)))
        elif control_id == "F3_explicit_four_step_word":
            self.add(self.boolean(self.length == 4))
            if self.length == 4:
                pattern = (GEOMETRY, ENTROPY, GEOMETRY, ENTROPY)
                self.add(
                    self.and_(
                        [
                            self.equal(kind, self.boolean(value))
                            for kind, value in zip(self.kinds, pattern)
                        ]
                    )
                )
        elif control_id == "F4_exactly_four_legs":
            self.add(self.boolean(self.length == 4))
        else:
            raise ValueError(f"unknown forbidden control: {control_id}")

    def bool_value(self, term: cvc5.Term) -> bool:
        value = str(self.solver.getValue(term))
        if value not in {"true", "false"}:
            raise RuntimeError(f"unexpected cvc5 Boolean model value: {value}")
        return value == "true"

    def int_value(self, term: cvc5.Term) -> int:
        return int(str(self.solver.getValue(term)))

    def extract_model(self) -> dict[str, Any]:
        shared_sign = "up" if self.bool_value(self.shared_sign) else "down"
        word = ["geometry" if self.bool_value(kind) else "entropy" for kind in self.kinds]
        states = [self.int_value(state) for state in self.states]
        transition_tables: dict[str, dict[str, list[int]]] = {}
        for sign, sign_label in ((DOWN, "down"), (UP, "up")):
            transition_tables[sign_label] = {}
            for work, work_label in ((GEOMETRY, "geometry"), (ENTROPY, "entropy")):
                transition_tables[sign_label][work_label] = [
                    self.int_value(self.tables[(work, sign, state)]) for state in range(STATE_COUNT)
                ]

        selected = transition_tables[shared_sign]
        commutator_witnesses = [
            state
            for state in range(STATE_COUNT)
            if selected["geometry"][selected["entropy"][state]]
            != selected["entropy"][selected["geometry"][state]]
        ]
        geometry_progress_legs = [
            index
            for index, work in enumerate(word)
            if work == "geometry" and states[index] // 3 != states[index + 1] // 3
        ]
        entropy_progress_legs = [
            index
            for index, work in enumerate(word)
            if work == "entropy" and states[index] % 3 != states[index + 1] % 3
        ]
        receipt = {
            "length": self.length,
            "word": word,
            "shared_axis6_sign": shared_sign,
            "leg_axis6_signs": ["up" if self.bool_value(sign) else "down" for sign in self.leg_signs],
            "states": states,
            "state_coordinates": [
                {"geometry": state // 3, "entropy": state % 3} for state in states
            ],
            "transition_tables": transition_tables,
            "selected_maps_distinct_witnesses": [
                state
                for state in range(STATE_COUNT)
                if selected["geometry"][state] != selected["entropy"][state]
            ],
            "commutator_witnesses": commutator_witnesses,
            "geometry_progress_legs": geometry_progress_legs,
            "entropy_progress_legs": entropy_progress_legs,
            "replayed_states": run_word(word, shared_sign, transition_tables, states[0]),
            "countermodel_to_forced_four": self.length != 4,
        }
        if self.binary_roles is not None:
            receipt["auxiliary"] = {
                "binary_roles": ["one" if self.bool_value(role) else "zero" for role in self.binary_roles]
            }
        return receipt

    def solve(self) -> dict[str, Any]:
        result = self.solver.checkSat()
        if result.isSat():
            return {
                "length": self.length,
                "status": "sat",
                "assertion_count": self.assertion_count,
                "model": self.extract_model(),
            }
        if result.isUnsat():
            return {
                "length": self.length,
                "status": "unsat",
                "assertion_count": self.assertion_count,
            }
        return {
            "length": self.length,
            "status": "unknown",
            "solver_result": str(result),
            "assertion_count": self.assertion_count,
        }


def summarize_scenario(
    scenario_id: str,
    category: str,
    cardinality_contaminated: bool,
    queries: list[dict[str, Any]],
) -> dict[str, Any]:
    admitted = [row["length"] for row in queries if row["status"] == "sat"]
    decided = all(row["status"] in {"sat", "unsat"} for row in queries)
    return {
        "scenario_id": scenario_id,
        "category": category,
        "tested_one_at_a_time": scenario_id != "baseline",
        "cardinality_contaminated": cardinality_contaminated,
        "queries": queries,
        "admitted_lengths": admitted,
        "nonfour_countermodel_lengths": [length for length in admitted if length != 4],
        "four_admitted": 4 in admitted,
        "forces_exactly_four_in_2_8_nonvacuously": admitted == [4],
        "all_queries_decided": decided,
    }


def run_scenario(scenario_id: str, category: str, lengths: list[int]) -> dict[str, Any]:
    queries = []
    for length in lengths:
        query = CVC5Query(length, scenario_id)
        if category == "candidate_addition":
            query.add_candidate(scenario_id)
        elif category == "forbidden_control":
            query.add_forbidden_control(scenario_id)
        queries.append(query.solve())
    return summarize_scenario(
        scenario_id,
        category,
        category == "forbidden_control",
        queries,
    )


def build_receipt() -> dict[str, Any]:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    lengths = list(spec["finite_formalization"]["search_lengths"])
    spec_candidates = tuple(row["id"] for row in spec["candidate_additional_axioms"])
    spec_forbidden = tuple(row["id"] for row in spec["forbidden_cardinality_controls"])
    if spec_candidates != CANDIDATE_IDS:
        raise RuntimeError("candidate axiom registry differs from preregistered cvc5 encoding")
    if spec_forbidden != FORBIDDEN_IDS:
        raise RuntimeError("forbidden control registry differs from preregistered cvc5 encoding")
    if lengths != list(range(2, 9)):
        raise RuntimeError("search range differs from preregistered 2..8 window")

    baseline = run_scenario("baseline", "baseline", lengths)
    candidates = {
        candidate_id: run_scenario(candidate_id, "candidate_addition", lengths)
        for candidate_id in CANDIDATE_IDS
    }
    forbidden = {
        control_id: run_scenario(control_id, "forbidden_control", lengths)
        for control_id in FORBIDDEN_IDS
    }
    scenarios = [baseline, *candidates.values(), *forbidden.values()]
    all_queries_decided = all(row["all_queries_decided"] for row in scenarios)
    candidate_forcers = [
        scenario_id
        for scenario_id, row in candidates.items()
        if row["forces_exactly_four_in_2_8_nonvacuously"]
    ]
    contaminated_forcers = [
        scenario_id
        for scenario_id, row in forbidden.items()
        if row["forces_exactly_four_in_2_8_nonvacuously"]
    ]
    return {
        "schema": "codex_ratchet.dual_ratchet_four_count_nonforcing_smt_v0.cvc5_raw.v1",
        "sim_id": spec["sim_id"],
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "stage_movement_allowed": False,
        "reads_peer_result": False,
        "solver": {
            "name": "cvc5",
            "api": "cvc5 Python API",
            "version": getattr(cvc5, "__version__", "unknown"),
            "logic_fragment": "QF_LIA with finite-domain constraints encoded by Bool, Int, and ITE",
        },
        "source_hashes": {
            relative(SPEC_PATH): sha256(SPEC_PATH),
            relative(OBJECT_CARD_PATH): sha256(OBJECT_CARD_PATH),
            relative(Path(__file__).resolve()): sha256(Path(__file__).resolve()),
        },
        "finite_formalization": spec["finite_formalization"],
        "premise_audit": {
            "baseline_axiom_ids": [row["id"] for row in spec["baseline_axioms"]],
            "candidate_axioms_tested_one_at_a_time": list(CANDIDATE_IDS),
            "desired_cardinality_supplied_to_clean_scenarios": False,
            "source_operator_names_supplied": False,
            "source_16x4_schedule_supplied": False,
        },
        "baseline": baseline,
        "candidate_additions": candidates,
        "forbidden_cardinality_controls": forbidden,
        "summary": {
            "baseline_admitted_lengths": baseline["admitted_lengths"],
            "baseline_forces_four": baseline["forces_exactly_four_in_2_8_nonvacuously"],
            "clean_candidate_forcers": candidate_forcers,
            "cardinality_contaminated_forcers": contaminated_forcers,
            "all_queries_decided": all_queries_decided,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": spec["claim_ceiling"],
        "schedule_16x4_boundary": spec["schedule_16x4_boundary"],
        "blocked_consumers": spec["blocked_consumers"],
        "all_pass": all_queries_decided,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    receipt = build_receipt()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "solver": "cvc5",
                "version": receipt["solver"]["version"],
                "baseline_admitted_lengths": receipt["summary"]["baseline_admitted_lengths"],
                "clean_candidate_forcers": receipt["summary"]["clean_candidate_forcers"],
                "cardinality_contaminated_forcers": receipt["summary"][
                    "cardinality_contaminated_forcers"
                ],
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
