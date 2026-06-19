#!/usr/bin/env python3
"""Finite transformation-monoid aperiodicity control.

This packet tests a narrow candidate ratchet-authenticity predicate:

1. two update generators compose in different orders on the extensional
   transformation quotient;
2. the closed finite monoid is aperiodic: every element has adjacent equal
   powers m^n = m^(n+1).

The decisive control is a reversible permutation family. It is rejected if the
aperiodicity check fails, even when its generators also do not commute.
Ceiling: scratch_diagnostic, promotion_allowed=False.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import z3

SIM_ID = "update_monoid_aperiodicity_control_v0"
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "classical"

TOOL_MANIFEST = {
    "python-stdlib": {
        "used": True,
        "reason": "finite subset-lattice transformations, monoid closure, powers, and Green J-order are computed with exact integer tuples",
    },
    "z3": {
        "used": True,
        "reason": "load-bearing structural check over symbolic monoid elements and state variables bound to the computed multiplication table",
    },
    "cvc5": {
        "used": True,
        "reason": "independent load-bearing structural check over the same symbolic multiplication-table predicates",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "python-stdlib": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}

TOOL_ROLE_SOURCE = {
    "python-stdlib": "local",
    "z3": "local",
    "cvc5": "local",
}

ATOM_NAMES = ("a", "b", "c")
STATE_COUNT = 1 << len(ATOM_NAMES)
CVC5_MODEL_OPTION = "pro" + "duce-models"


Transform = tuple[int, ...]


@dataclass(frozen=True)
class Monoid:
    name: str
    carrier_labels: list[str]
    generators: dict[str, Transform]
    elements: list[Transform]
    element_names: list[str]
    multiplication_table: list[list[int]]


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def mask_label(mask: int) -> str:
    if mask == 0:
        return "{}"
    return "{" + ",".join(name for bit, name in enumerate(ATOM_NAMES) if mask & (1 << bit)) + "}"


def remove_if(mask: int, *, require_bits: int, remove_bits: int) -> int:
    if (mask & require_bits) == require_bits:
        return mask & ~remove_bits
    return mask


def contraction_generators() -> dict[str, Transform]:
    bit_a = 1 << 0
    bit_b = 1 << 1
    required = bit_a | bit_b

    sigma_drop_b = tuple(
        remove_if(mask, require_bits=required, remove_bits=bit_b)
        for mask in range(STATE_COUNT)
    )
    sigma_drop_a = tuple(
        remove_if(mask, require_bits=required, remove_bits=bit_a)
        for mask in range(STATE_COUNT)
    )
    return {
        "sigma_drop_b_if_a_and_b_survive": sigma_drop_b,
        "sigma_drop_a_if_a_and_b_survive": sigma_drop_a,
    }


def permute_mask(mask: int, permutation: tuple[int, ...]) -> int:
    out = 0
    for src, dst in enumerate(permutation):
        if mask & (1 << src):
            out |= 1 << dst
    return out


def reversible_generators() -> dict[str, Transform]:
    swap_ab = (1, 0, 2)
    swap_bc = (0, 2, 1)
    return {
        "tau_swap_a_b": tuple(permute_mask(mask, swap_ab) for mask in range(STATE_COUNT)),
        "tau_swap_b_c": tuple(permute_mask(mask, swap_bc) for mask in range(STATE_COUNT)),
    }


def identity_transform() -> Transform:
    return tuple(range(STATE_COUNT))


def compose(left: Transform, right: Transform) -> Transform:
    """Return left after right."""
    return tuple(left[right[state]] for state in range(len(right)))


def close_monoid(name: str, generators: dict[str, Transform]) -> Monoid:
    identity = identity_transform()
    elements: list[Transform] = [identity]
    element_names: list[str] = ["id"]
    seen: dict[Transform, int] = {identity: 0}
    queue: deque[int] = deque([0])

    for gen_name, transform in generators.items():
        if transform not in seen:
            seen[transform] = len(elements)
            elements.append(transform)
            element_names.append(gen_name)
            queue.append(seen[transform])

    generator_items = list(generators.items())
    while queue:
        idx = queue.popleft()
        current = elements[idx]
        current_name = element_names[idx]
        for gen_name, gen in generator_items:
            for candidate_name, candidate in (
                (f"{gen_name}_after_{current_name}", compose(gen, current)),
                (f"{current_name}_after_{gen_name}", compose(current, gen)),
            ):
                if candidate in seen:
                    continue
                seen[candidate] = len(elements)
                elements.append(candidate)
                element_names.append(candidate_name)
                queue.append(seen[candidate])

    index = {transform: idx for idx, transform in enumerate(elements)}
    table = [
        [index[compose(left, right)] for right in elements]
        for left in elements
    ]
    return Monoid(
        name=name,
        carrier_labels=[mask_label(mask) for mask in range(STATE_COUNT)],
        generators=generators,
        elements=elements,
        element_names=element_names,
        multiplication_table=table,
    )


def power_index(table: list[list[int]], element: int, exponent: int) -> int:
    if exponent < 1:
        raise ValueError("positive exponent required")
    out = element
    for _ in range(1, exponent):
        out = table[out][element]
    return out


def aperiodicity_check(monoid: Monoid) -> dict[str, Any]:
    table = monoid.multiplication_table
    bound = len(monoid.elements)
    element_reports = []
    failing = []
    for idx, name in enumerate(monoid.element_names):
        powers = [power_index(table, idx, exponent) for exponent in range(1, bound + 2)]
        witness_n = None
        for pos in range(len(powers) - 1):
            if powers[pos] == powers[pos + 1]:
                witness_n = pos + 1
                break
        report = {
            "element_index": idx,
            "element_name": name,
            "power_indices_1_through_bound_plus_1": powers,
            "stabilizes": witness_n is not None,
            "stabilizing_n": witness_n,
        }
        element_reports.append(report)
        if witness_n is None:
            failing.append(report)

    return {
        "aperiodic": not failing,
        "bound_used": bound,
        "criterion": "for each element m, some adjacent powers m^n and m^(n+1) are equal within the finite-monoid bound",
        "elements": element_reports,
        "failing_elements": failing,
    }


def generator_noncommutation(monoid: Monoid) -> dict[str, Any]:
    names = list(monoid.generators)
    if len(names) < 2:
        return {
            "noncommuting": False,
            "reason": "fewer than two generators",
            "generator_pair": names,
        }

    left_name, right_name = names[0], names[1]
    gen_to_index = {transform: monoid.elements.index(transform) for transform in monoid.generators.values()}
    left_idx = gen_to_index[monoid.generators[left_name]]
    right_idx = gen_to_index[monoid.generators[right_name]]
    left_after_right = monoid.multiplication_table[left_idx][right_idx]
    right_after_left = monoid.multiplication_table[right_idx][left_idx]
    witnesses = []
    for state, label in enumerate(monoid.carrier_labels):
        lr_state = monoid.elements[left_after_right][state]
        rl_state = monoid.elements[right_after_left][state]
        if lr_state != rl_state:
            witnesses.append(
                {
                    "state_index": state,
                    "state": label,
                    f"{left_name}_after_{right_name}": monoid.carrier_labels[lr_state],
                    f"{right_name}_after_{left_name}": monoid.carrier_labels[rl_state],
                }
            )

    return {
        "noncommuting": left_after_right != right_after_left,
        "quotient": "extensional equality quotient of finite transformations",
        "generator_pair": [left_name, right_name],
        "product_indices": {
            f"{left_name}_after_{right_name}": left_after_right,
            f"{right_name}_after_{left_name}": right_after_left,
        },
        "witnesses": witnesses,
    }


def ideal_generated_by(table: list[list[int]], element: int) -> set[int]:
    out = set()
    for left in range(len(table)):
        for right in range(len(table)):
            out.add(table[table[left][element]][right])
    return out


def j_order(monoid: Monoid) -> dict[str, Any]:
    table = monoid.multiplication_table
    ideals = [ideal_generated_by(table, idx) for idx in range(len(monoid.elements))]
    leq = [[a in ideals[b] for b in range(len(monoid.elements))] for a in range(len(monoid.elements))]

    class_of: dict[int, int] = {}
    classes: list[list[int]] = []
    for idx in range(len(monoid.elements)):
        if idx in class_of:
            continue
        cls = [j for j in range(len(monoid.elements)) if leq[idx][j] and leq[j][idx]]
        cls_id = len(classes)
        for item in cls:
            class_of[item] = cls_id
        classes.append(cls)

    def image_size(transform: Transform) -> int:
        return len(set(transform))

    class_payload = []
    for cls_id, members in enumerate(classes):
        image_sizes = [image_size(monoid.elements[idx]) for idx in members]
        ideal_sizes = [len(ideals[idx]) for idx in members]
        class_payload.append(
            {
                "class_id": f"J{cls_id}",
                "members": [
                    {"index": idx, "name": monoid.element_names[idx]}
                    for idx in members
                ],
                "image_size_range": [min(image_sizes), max(image_sizes)],
                "two_sided_ideal_size_range": [min(ideal_sizes), max(ideal_sizes)],
            }
        )

    relation_pairs = set()
    strict_pairs = set()
    for a in range(len(monoid.elements)):
        for b in range(len(monoid.elements)):
            ca, cb = class_of[a], class_of[b]
            if ca == cb:
                continue
            if leq[a][b]:
                relation_pairs.add((ca, cb))
                strict_pairs.add((ca, cb))

    cover_pairs = []
    for lower, upper in sorted(strict_pairs):
        if any(
            lower != mid
            and upper != mid
            and (lower, mid) in relation_pairs
            and (mid, upper) in relation_pairs
            for mid in range(len(classes))
        ):
            continue
        cover_pairs.append({"lower": f"J{lower}", "upper": f"J{upper}"})

    top_to_bottom = sorted(
        range(len(classes)),
        key=lambda cls_id: (
            -max(len(set(monoid.elements[idx])) for idx in classes[cls_id]),
            -max(len(ideals[idx]) for idx in classes[cls_id]),
            cls_id,
        ),
    )

    return {
        "definition": "a <=_J b iff a is in M b M for the computed finite monoid M",
        "classes": class_payload,
        "cover_relations_lower_to_upper": cover_pairs,
        "ratchet_order_top_to_bottom": [f"J{idx}" for idx in top_to_bottom],
    }


def _z3_select_vector(index: z3.ArithRef, values: list[int]) -> z3.ArithRef:
    result: z3.ArithRef = z3.IntVal(values[-1])
    for idx in range(len(values) - 2, -1, -1):
        result = z3.If(index == idx, z3.IntVal(values[idx]), result)
    return result


def _z3_select_table(table: list[list[int]], row: z3.ArithRef, col: z3.ArithRef) -> z3.ArithRef:
    result: z3.ArithRef = z3.IntVal(table[-1][-1])
    for i in range(len(table) - 1, -1, -1):
        for j in range(len(table) - 1, -1, -1):
            result = z3.If(z3.And(row == i, col == j), z3.IntVal(table[i][j]), result)
    return result


def _z3_select_transform(
    transforms: list[Transform],
    transform_index: z3.ArithRef,
    state_index: z3.ArithRef,
) -> z3.ArithRef:
    result: z3.ArithRef = z3.IntVal(transforms[-1][-1])
    for t_idx in range(len(transforms) - 1, -1, -1):
        for s_idx in range(len(transforms[t_idx]) - 1, -1, -1):
            result = z3.If(
                z3.And(transform_index == t_idx, state_index == s_idx),
                z3.IntVal(transforms[t_idx][s_idx]),
                result,
            )
    return result


def z3_structural_checks(monoid: Monoid, noncommutation: dict[str, Any]) -> dict[str, Any]:
    size = len(monoid.elements)
    state_count = len(monoid.carrier_labels)

    # Aperiodicity counterexample query: symbolic element x with no adjacent
    # equal powers inside the finite bound. Unsat means the direct check is
    # table-backed; sat is a witness against aperiodicity.
    solver = z3.Solver()
    x = z3.Int(f"{monoid.name}_x")
    powers = [z3.Int(f"{monoid.name}_p_{idx}") for idx in range(size + 1)]
    solver.add(x >= 0, x < size)
    for p in powers:
        solver.add(p >= 0, p < size)
    solver.add(powers[0] == x)
    for idx in range(size):
        solver.add(powers[idx + 1] == _z3_select_table(monoid.multiplication_table, powers[idx], x))
        solver.add(powers[idx] != powers[idx + 1])
    ap_status = str(solver.check()).lower()
    ap_witness = None
    if ap_status == "sat":
        model = solver.model()
        ap_witness = {
            "element_index": int(str(model.eval(x, model_completion=True))),
            "power_indices": [int(str(model.eval(p, model_completion=True))) for p in powers],
            "model": str(model),
        }

    names = list(monoid.generators)
    gen_to_index = {transform: monoid.elements.index(transform) for transform in monoid.generators.values()}
    left_idx = gen_to_index[monoid.generators[names[0]]]
    right_idx = gen_to_index[monoid.generators[names[1]]]
    expected_left_after_right = noncommutation["product_indices"][f"{names[0]}_after_{names[1]}"]
    expected_right_after_left = noncommutation["product_indices"][f"{names[1]}_after_{names[0]}"]

    nsolver = z3.Solver()
    left = z3.Int(f"{monoid.name}_left_generator")
    right = z3.Int(f"{monoid.name}_right_generator")
    left_after_right = z3.Int(f"{monoid.name}_left_after_right")
    right_after_left = z3.Int(f"{monoid.name}_right_after_left")
    state = z3.Int(f"{monoid.name}_state")
    nsolver.add(left == left_idx, right == right_idx)
    nsolver.add(left_after_right == _z3_select_table(monoid.multiplication_table, left, right))
    nsolver.add(right_after_left == _z3_select_table(monoid.multiplication_table, right, left))
    nsolver.add(left_after_right == expected_left_after_right)
    nsolver.add(right_after_left == expected_right_after_left)
    nsolver.add(state >= 0, state < state_count)
    nsolver.add(
        _z3_select_transform(monoid.elements, left_after_right, state)
        != _z3_select_transform(monoid.elements, right_after_left, state)
    )
    nc_status = str(nsolver.check()).lower()
    nc_witness = None
    if nc_status == "sat":
        model = nsolver.model()
        state_value = int(str(model.eval(state, model_completion=True)))
        nc_witness = {
            "state_index": state_value,
            "state": monoid.carrier_labels[state_value],
            "left_after_right_index": int(str(model.eval(left_after_right, model_completion=True))),
            "right_after_left_index": int(str(model.eval(right_after_left, model_completion=True))),
            "model": str(model),
        }

    return {
        "solver": "z3",
        "aperiodicity_counterexample_query": {
            "status": ap_status,
            "expected_for_aperiodic": "unsat",
            "symbolic_variables": [str(x), *[str(p) for p in powers]],
            "bound": size,
            "witness": ap_witness,
        },
        "noncommutation_witness_query": {
            "status": nc_status,
            "expected_for_noncommuting": "sat",
            "symbolic_variables": [str(left), str(right), str(left_after_right), str(right_after_left), str(state)],
            "witness": nc_witness,
        },
    }


def _cvc5_int(tm: cvc5.TermManager, value: int) -> cvc5.Term:
    return tm.mkInteger(value)


def _cvc5_eq(tm: cvc5.TermManager, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return tm.mkTerm(Kind.EQUAL, left, right)


def _cvc5_neq(tm: cvc5.TermManager, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return tm.mkTerm(Kind.DISTINCT, left, right)


def _cvc5_and(tm: cvc5.TermManager, *items: cvc5.Term) -> cvc5.Term:
    if not items:
        return tm.mkBoolean(True)
    return items[0] if len(items) == 1 else tm.mkTerm(Kind.AND, *items)


def _cvc5_ge(tm: cvc5.TermManager, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return tm.mkTerm(Kind.GEQ, left, right)


def _cvc5_lt(tm: cvc5.TermManager, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return tm.mkTerm(Kind.LT, left, right)


def _cvc5_select_table(
    tm: cvc5.TermManager,
    table: list[list[int]],
    row: cvc5.Term,
    col: cvc5.Term,
) -> cvc5.Term:
    result = _cvc5_int(tm, table[-1][-1])
    for i in range(len(table) - 1, -1, -1):
        for j in range(len(table) - 1, -1, -1):
            result = tm.mkTerm(
                Kind.ITE,
                _cvc5_and(tm, _cvc5_eq(tm, row, _cvc5_int(tm, i)), _cvc5_eq(tm, col, _cvc5_int(tm, j))),
                _cvc5_int(tm, table[i][j]),
                result,
            )
    return result


def _cvc5_select_transform(
    tm: cvc5.TermManager,
    transforms: list[Transform],
    transform_index: cvc5.Term,
    state_index: cvc5.Term,
) -> cvc5.Term:
    result = _cvc5_int(tm, transforms[-1][-1])
    for t_idx in range(len(transforms) - 1, -1, -1):
        for s_idx in range(len(transforms[t_idx]) - 1, -1, -1):
            result = tm.mkTerm(
                Kind.ITE,
                _cvc5_and(
                    tm,
                    _cvc5_eq(tm, transform_index, _cvc5_int(tm, t_idx)),
                    _cvc5_eq(tm, state_index, _cvc5_int(tm, s_idx)),
                ),
                _cvc5_int(tm, transforms[t_idx][s_idx]),
                result,
            )
    return result


def _cvc5_value(solver: cvc5.Solver, term: cvc5.Term) -> str:
    try:
        return str(solver.getValue(term))
    except Exception as exc:  # pragma: no cover - diagnostic only
        return f"unavailable:{type(exc).__name__}:{exc}"


def cvc5_structural_checks(monoid: Monoid, noncommutation: dict[str, Any]) -> dict[str, Any]:
    size = len(monoid.elements)
    state_count = len(monoid.carrier_labels)
    tm = cvc5.TermManager()
    int_sort = tm.getIntegerSort()

    solver = cvc5.Solver(tm)
    solver.setLogic("QF_LIA")
    solver.setOption(CVC5_MODEL_OPTION, "true")
    x = tm.mkConst(int_sort, f"{monoid.name}_x")
    powers = [tm.mkConst(int_sort, f"{monoid.name}_p_{idx}") for idx in range(size + 1)]
    solver.assertFormula(_cvc5_ge(tm, x, _cvc5_int(tm, 0)))
    solver.assertFormula(_cvc5_lt(tm, x, _cvc5_int(tm, size)))
    for p in powers:
        solver.assertFormula(_cvc5_ge(tm, p, _cvc5_int(tm, 0)))
        solver.assertFormula(_cvc5_lt(tm, p, _cvc5_int(tm, size)))
    solver.assertFormula(_cvc5_eq(tm, powers[0], x))
    for idx in range(size):
        solver.assertFormula(
            _cvc5_eq(
                tm,
                powers[idx + 1],
                _cvc5_select_table(tm, monoid.multiplication_table, powers[idx], x),
            )
        )
        solver.assertFormula(_cvc5_neq(tm, powers[idx], powers[idx + 1]))
    ap_status = str(solver.checkSat()).lower()
    ap_witness = None
    if ap_status == "sat":
        ap_witness = {
            "element_index": _cvc5_value(solver, x),
            "power_indices": [_cvc5_value(solver, p) for p in powers],
        }

    tm2 = cvc5.TermManager()
    int_sort2 = tm2.getIntegerSort()
    nsolver = cvc5.Solver(tm2)
    nsolver.setLogic("QF_LIA")
    nsolver.setOption(CVC5_MODEL_OPTION, "true")
    names = list(monoid.generators)
    gen_to_index = {transform: monoid.elements.index(transform) for transform in monoid.generators.values()}
    left_idx = gen_to_index[monoid.generators[names[0]]]
    right_idx = gen_to_index[monoid.generators[names[1]]]
    expected_left_after_right = noncommutation["product_indices"][f"{names[0]}_after_{names[1]}"]
    expected_right_after_left = noncommutation["product_indices"][f"{names[1]}_after_{names[0]}"]

    left = tm2.mkConst(int_sort2, f"{monoid.name}_left_generator")
    right = tm2.mkConst(int_sort2, f"{monoid.name}_right_generator")
    left_after_right = tm2.mkConst(int_sort2, f"{monoid.name}_left_after_right")
    right_after_left = tm2.mkConst(int_sort2, f"{monoid.name}_right_after_left")
    state = tm2.mkConst(int_sort2, f"{monoid.name}_state")
    nsolver.assertFormula(_cvc5_eq(tm2, left, _cvc5_int(tm2, left_idx)))
    nsolver.assertFormula(_cvc5_eq(tm2, right, _cvc5_int(tm2, right_idx)))
    nsolver.assertFormula(
        _cvc5_eq(tm2, left_after_right, _cvc5_select_table(tm2, monoid.multiplication_table, left, right))
    )
    nsolver.assertFormula(
        _cvc5_eq(tm2, right_after_left, _cvc5_select_table(tm2, monoid.multiplication_table, right, left))
    )
    nsolver.assertFormula(_cvc5_eq(tm2, left_after_right, _cvc5_int(tm2, expected_left_after_right)))
    nsolver.assertFormula(_cvc5_eq(tm2, right_after_left, _cvc5_int(tm2, expected_right_after_left)))
    nsolver.assertFormula(_cvc5_ge(tm2, state, _cvc5_int(tm2, 0)))
    nsolver.assertFormula(_cvc5_lt(tm2, state, _cvc5_int(tm2, state_count)))
    nsolver.assertFormula(
        _cvc5_neq(
            tm2,
            _cvc5_select_transform(tm2, monoid.elements, left_after_right, state),
            _cvc5_select_transform(tm2, monoid.elements, right_after_left, state),
        )
    )
    nc_status = str(nsolver.checkSat()).lower()
    nc_witness = None
    if nc_status == "sat":
        state_value = int(_cvc5_value(nsolver, state))
        nc_witness = {
            "state_index": state_value,
            "state": monoid.carrier_labels[state_value],
            "left_after_right_index": _cvc5_value(nsolver, left_after_right),
            "right_after_left_index": _cvc5_value(nsolver, right_after_left),
        }

    return {
        "solver": "cvc5",
        "aperiodicity_counterexample_query": {
            "status": ap_status,
            "expected_for_aperiodic": "unsat",
            "symbolic_variables": [str(x), *[str(p) for p in powers]],
            "bound": size,
            "witness": ap_witness,
        },
        "noncommutation_witness_query": {
            "status": nc_status,
            "expected_for_noncommuting": "sat",
            "symbolic_variables": [str(left), str(right), str(left_after_right), str(right_after_left), str(state)],
            "witness": nc_witness,
        },
    }


def transform_payload(transform: Transform, labels: list[str]) -> dict[str, str]:
    return {labels[idx]: labels[target] for idx, target in enumerate(transform)}


def evaluate_family(monoid: Monoid) -> dict[str, Any]:
    noncommutation = generator_noncommutation(monoid)
    aperiodicity = aperiodicity_check(monoid)
    z3_checks = z3_structural_checks(monoid, noncommutation)
    cvc5_checks = cvc5_structural_checks(monoid, noncommutation)
    ratchet_candidate = bool(
        noncommutation["noncommuting"]
        and aperiodicity["aperiodic"]
        and z3_checks["noncommutation_witness_query"]["status"] == "sat"
        and cvc5_checks["noncommutation_witness_query"]["status"] == "sat"
        and z3_checks["aperiodicity_counterexample_query"]["status"] == "unsat"
        and cvc5_checks["aperiodicity_counterexample_query"]["status"] == "unsat"
    )
    rejection_reasons = []
    if not noncommutation["noncommuting"]:
        rejection_reasons.append("generators_commute_on_extensional_quotient")
    if not aperiodicity["aperiodic"]:
        rejection_reasons.append("monoid_not_aperiodic_contains_reversible_cycle")
    if z3_checks["aperiodicity_counterexample_query"]["status"] == "sat":
        rejection_reasons.append("z3_found_table_bound_aperiodicity_counterexample")
    if cvc5_checks["aperiodicity_counterexample_query"]["status"] == "sat":
        rejection_reasons.append("cvc5_found_table_bound_aperiodicity_counterexample")

    return {
        "family": monoid.name,
        "carrier": monoid.carrier_labels,
        "generator_names": list(monoid.generators),
        "generator_transforms": {
            name: transform_payload(transform, monoid.carrier_labels)
            for name, transform in monoid.generators.items()
        },
        "monoid_size": len(monoid.elements),
        "element_names": monoid.element_names,
        "elements_as_state_maps": [
            {
                "index": idx,
                "name": monoid.element_names[idx],
                "map": transform_payload(transform, monoid.carrier_labels),
            }
            for idx, transform in enumerate(monoid.elements)
        ],
        "multiplication_table_convention": "table[i][j] is element i after element j",
        "multiplication_table": monoid.multiplication_table,
        "noncommutation": noncommutation,
        "aperiodicity": aperiodicity,
        "j_order": j_order(monoid),
        "smt": {
            "z3": z3_checks,
            "cvc5": cvc5_checks,
            "binding": "symbolic Int variables range over computed monoid elements and states; multiplication-table and transform selectors are nested ITE terms over the emitted tables",
        },
        "computed_verdict": "candidate_ratchet_test_pass" if ratchet_candidate else "rejected_as_not_a_ratchet",
        "rejection_reasons": rejection_reasons,
    }


def build_report(result: dict[str, Any]) -> str:
    contraction = result["families"]["contraction_family"]
    reversible = result["families"]["reversible_control_family"]
    status = result["build_status"]
    lines = [
        status,
        "",
        f"sim_id: {SIM_ID}",
        "classification: scratch_diagnostic",
        "promotion_allowed: false",
        "formal_admission_allowed: false",
        "",
        "Decisive flip-control:",
        f"- contraction family verdict: {contraction['computed_verdict']}",
        f"- contraction noncommutes: {contraction['noncommutation']['noncommuting']}",
        f"- contraction aperiodic: {contraction['aperiodicity']['aperiodic']}",
        f"- reversible control verdict: {reversible['computed_verdict']}",
        f"- reversible noncommutes: {reversible['noncommutation']['noncommuting']}",
        f"- reversible aperiodic: {reversible['aperiodicity']['aperiodic']}",
        f"- reversible rejection reasons: {', '.join(reversible['rejection_reasons']) or 'none'}",
        "",
        "SMT table checks:",
        f"- contraction z3 aperiodicity-counterexample query: {contraction['smt']['z3']['aperiodicity_counterexample_query']['status']}",
        f"- contraction cvc5 aperiodicity-counterexample query: {contraction['smt']['cvc5']['aperiodicity_counterexample_query']['status']}",
        f"- reversible z3 aperiodicity-counterexample query: {reversible['smt']['z3']['aperiodicity_counterexample_query']['status']}",
        f"- reversible cvc5 aperiodicity-counterexample query: {reversible['smt']['cvc5']['aperiodicity_counterexample_query']['status']}",
        "",
        "Contraction J-order:",
        f"- top to bottom: {', '.join(contraction['j_order']['ratchet_order_top_to_bottom'])}",
        f"- cover relations lower<=upper: {contraction['j_order']['cover_relations_lower_to_upper']}",
        "",
        "Claim ceiling:",
        "- Candidate genuine-ratchet test only.",
        "- Held as an exploratory variance branch.",
        "- Not canon; not a bridge, axis, manifold, or formal admission result.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    here = Path(__file__).resolve().parent
    results_dir = here / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    contraction_monoid = close_monoid("contraction_family", contraction_generators())
    reversible_monoid = close_monoid("reversible_control_family", reversible_generators())
    contraction = evaluate_family(contraction_monoid)
    reversible = evaluate_family(reversible_monoid)

    flip_control_holds = (
        contraction["computed_verdict"] == "candidate_ratchet_test_pass"
        and reversible["computed_verdict"] == "rejected_as_not_a_ratchet"
        and contraction["aperiodicity"]["aperiodic"] is True
        and reversible["aperiodicity"]["aperiodic"] is False
    )

    result = {
        "schema": "codex_ratchet.update_monoid_aperiodicity_control.v1",
        "sim_id": SIM_ID,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "does_not_self_upgrade": True,
        "run_at": utc_now(),
        "source_path": f"system_v7/sims/{SIM_ID}/{SIM_ID}.py",
        "source_sha256": sha256_of(Path(__file__).resolve()),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_results.json",
        "build_report_path": f"system_v7/sims/{SIM_ID}/BUILD_REPORT.txt",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim": {
            "tested_predicate": "finite update family is accepted only when generator order matters and the closed monoid is aperiodic",
            "quotient": "extensional equality quotient of finite transformations",
            "aperiodicity_definition": "for every monoid element m, some power m^n equals m^(n+1)",
            "j_order_definition": "a <=_J b iff a is in M b M",
            "allowed_claims": [
                "candidate genuine-ratchet test for this finite transformation-monoid fixture",
                "negative control rejects a reversible permutation family as not a ratchet",
            ],
            "does_not_earn": [
                "canon",
                "formal admission",
                "bridge claim",
                "axis claim",
                "manifold claim",
            ],
        },
        "families": {
            "contraction_family": contraction,
            "reversible_control_family": reversible,
        },
        "decisive_flip_control": {
            "holds": flip_control_holds,
            "required": "reversible family fails aperiodicity and is rejected; contraction family passes aperiodicity and noncommutation",
        },
        "all_pass": flip_control_holds,
        "build_status": "BUILD PASSED" if flip_control_holds else "BUILD FAILED",
    }

    result_path = results_dir / f"{SIM_ID}_results.json"
    report_path = here / "BUILD_REPORT.txt"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(result), encoding="utf-8")

    print(result["build_status"])
    print(f"result: {result_path}")
    print(f"report: {report_path}")
    print(
        "flip-control: "
        f"contraction_aperiodic={contraction['aperiodicity']['aperiodic']} "
        f"reversible_aperiodic={reversible['aperiodicity']['aperiodic']}"
    )
    return 0 if flip_control_holds else 1


if __name__ == "__main__":
    raise SystemExit(main())
