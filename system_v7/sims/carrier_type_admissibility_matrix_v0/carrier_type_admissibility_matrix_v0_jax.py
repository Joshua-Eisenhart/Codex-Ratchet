#!/usr/bin/env python3
"""Python/JAX SMT leg for carrier_type_admissibility_matrix_v0."""

from __future__ import annotations

from jax import config

config.update("jax_enable_x64", True)

import hashlib
import json
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Literal

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import z3

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "nonclassical"

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 fixture table readback; solver verdicts, not JAX numerics, decide allowed sets",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing QF_NRA/linear SMT existence search over free carrier variables for each type and fixture",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT existence search over the same carrier/readout constraints",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}

SIM_ID = "carrier_type_admissibility_matrix_v0"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
CarrierType = Literal["quotient", "classical_noncontextual", "real_rebit", "complex_rho"]
SolverName = Literal["z3", "cvc5"]
CARRIER_TYPES: tuple[CarrierType, ...] = (
    "quotient",
    "classical_noncontextual",
    "real_rebit",
    "complex_rho",
)
ASSIGNMENTS = tuple((z, x, y) for z in (0, 1) for x in (0, 1) for y in (0, 1))


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_spec() -> dict[str, Any]:
    return json.loads((HERE / "spec.json").read_text(encoding="utf-8"))


def parse_fraction(value: Any) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        return Fraction(str(value))
    if isinstance(value, str):
        return Fraction(value.strip())
    raise TypeError(f"cannot parse Fraction from {value!r}")


def fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def fixture_from_spec(spec: dict[str, Any], group: str, name: str) -> dict[str, Any]:
    fixture = dict(spec[group][name])
    fixture["name"] = name
    fixture["group"] = group
    return fixture


def ordered_names(spec: dict[str, Any], group: str) -> list[str]:
    order_key = f"{group[:-1]}_order" if group.endswith("s") else f"{group}_order"
    return list(spec.get(order_key, spec[group].keys()))


def measured_from_fixture(fixture: dict[str, Any]) -> dict[str, Fraction]:
    return {str(probe): parse_fraction(value) for probe, value in fixture["measured"].items()}


def _z3_real(value: Fraction) -> z3.ArithRef:
    return z3.RealVal(fraction_text(value))


def _z3_sum(items: list[z3.ArithRef]) -> z3.ArithRef:
    return z3.RealVal("0") if not items else sum(items, z3.RealVal("0"))


def _z3_classical_readout(probe: str, weights: dict[tuple[int, int, int], z3.ArithRef]) -> z3.ArithRef:
    if probe == "Z":
        return _z3_sum([w for (z, _x, _y), w in weights.items() if z == 1])
    if probe == "X":
        return _z3_sum([w for (_z, x, _y), w in weights.items() if x == 1])
    if probe == "Y":
        return _z3_sum([w for (_z, _x, y), w in weights.items() if y == 1])
    if probe in {"ZX", "XZ"}:
        return _z3_sum([w for (z, x, _y), w in weights.items() if z == 1 and x == 1])
    raise ValueError(f"unknown probe {probe!r}")


def _z3_real_readout(probe: str, a: z3.ArithRef, b: z3.ArithRef) -> z3.ArithRef:
    if probe == "Z":
        return a
    if probe == "X":
        return z3.RealVal("1/2") + b
    if probe == "Y":
        return z3.RealVal("1/2")
    if probe == "ZX":
        return a / 2
    if probe == "XZ":
        return z3.RealVal("1/4") + b / 2
    raise ValueError(f"unknown probe {probe!r}")


def _z3_complex_readout(probe: str, a: z3.ArithRef, b: z3.ArithRef, c: z3.ArithRef) -> z3.ArithRef:
    if probe == "Y":
        return z3.RealVal("1/2") + c
    return _z3_real_readout(probe, a, b)


def _z3_value_text(model: z3.ModelRef, var: z3.ArithRef) -> str:
    value = model.eval(var, model_completion=True)
    if isinstance(value, z3.RatNumRef):
        return fraction_text(Fraction(value.numerator_as_long(), value.denominator_as_long()))
    return str(value)


def _z3_decide(fixture: dict[str, Any], carrier_type: CarrierType, *, include_reproduce: bool) -> dict[str, Any]:
    measured = measured_from_fixture(fixture)
    probes = [str(probe) for probe in fixture["probes"]]
    solver = z3.SolverFor("QF_NRA")
    readout_terms: dict[str, z3.ArithRef] = {}
    variables: dict[str, z3.ArithRef] = {}
    prefix = f"z3_{fixture['name']}_{carrier_type}"
    validity: list[str] = []

    if carrier_type == "quotient":
        for probe in probes:
            var = z3.Real(f"{prefix}_{probe}")
            variables[f"q_{probe}"] = var
            solver.add(var >= 0, var <= 1)
            readout_terms[probe] = var
        validity.append("0 <= q_probe <= 1 for each measured probe")
    elif carrier_type == "classical_noncontextual":
        weights = {
            assignment: z3.Real(f"{prefix}_w_{assignment[0]}{assignment[1]}{assignment[2]}")
            for assignment in ASSIGNMENTS
        }
        variables = {f"w_z{z}x{x}y{y}": w for (z, x, y), w in weights.items()}
        for weight in weights.values():
            solver.add(weight >= 0)
        solver.add(_z3_sum(list(weights.values())) == 1)
        for probe in probes:
            readout_terms[probe] = _z3_classical_readout(probe, weights)
        validity.append("weights over deterministic Z/X/Y assignments are nonnegative and sum to 1")
        validity.append("ZX and XZ are the same non-disturbing joint event")
    elif carrier_type == "real_rebit":
        a = z3.Real(f"{prefix}_a")
        b = z3.Real(f"{prefix}_b")
        variables = {"a": a, "b": b}
        solver.add(a >= 0, a <= 1)
        solver.add(a * (1 - a) - b * b >= 0)
        for probe in probes:
            readout_terms[probe] = _z3_real_readout(probe, a, b)
        validity.append("rho_R=[[a,b],[b,1-a]], 0 <= a <= 1, a*(1-a)-b^2 >= 0")
    elif carrier_type == "complex_rho":
        a = z3.Real(f"{prefix}_a")
        b = z3.Real(f"{prefix}_b")
        c = z3.Real(f"{prefix}_c")
        variables = {"a": a, "b": b, "c": c}
        solver.add(a >= 0, a <= 1)
        solver.add(a * (1 - a) - b * b - c * c >= 0)
        for probe in probes:
            readout_terms[probe] = _z3_complex_readout(probe, a, b, c)
        validity.append("rho=[[a,b-i*c],[b+i*c,1-a]], 0 <= a <= 1, a*(1-a)-b^2-c^2 >= 0")
    else:
        raise ValueError(f"unknown carrier_type {carrier_type!r}")

    if include_reproduce:
        for probe in probes:
            solver.add(readout_terms[probe] == _z3_real(measured[probe]))

    status = str(solver.check()).lower()
    witness = None
    if status == "sat":
        model = solver.model()
        witness = {
            name: _z3_value_text(model, var)
            for name, var in sorted(variables.items())
        }
    return {
        "solver": "z3",
        "solver_logic": "QF_NRA",
        "solver_status": status,
        "carrier_type": carrier_type,
        "fixture": fixture["name"],
        "admission": "admitted" if status == "sat" else "excluded" if status == "unsat" else "unknown",
        "verdict_source": "str(solver.check())",
        "probes": probes,
        "measured": {probe: fraction_text(value) for probe, value in measured.items()},
        "include_reproduce": include_reproduce,
        "readout_binding": "readout_T(C, probe) == measured_probe for every listed probe" if include_reproduce else "omitted",
        "validity_constraints": validity,
        "free_variables": {name: f"{name}:Real" for name in sorted(variables)},
        "readout_definitions": fixture.get("readout_definitions", {}),
        "witness": witness,
    }


def _cvc5_real(tm: cvc5.TermManager, value: Fraction) -> cvc5.Term:
    return tm.mkReal(fraction_text(value))


def _cvc5_add(tm: cvc5.TermManager, items: list[cvc5.Term]) -> cvc5.Term:
    if not items:
        return tm.mkReal("0")
    return items[0] if len(items) == 1 else tm.mkTerm(Kind.ADD, *items)


def _cvc5_sub(tm: cvc5.TermManager, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return tm.mkTerm(Kind.SUB, left, right)


def _cvc5_mul(tm: cvc5.TermManager, *items: cvc5.Term) -> cvc5.Term:
    return items[0] if len(items) == 1 else tm.mkTerm(Kind.MULT, *items)


def _cvc5_eq(tm: cvc5.TermManager, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return tm.mkTerm(Kind.EQUAL, left, right)


def _cvc5_ge(tm: cvc5.TermManager, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return tm.mkTerm(Kind.GEQ, left, right)


def _cvc5_le(tm: cvc5.TermManager, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return tm.mkTerm(Kind.LEQ, left, right)


def _cvc5_classical_readout(tm: cvc5.TermManager, probe: str, weights: dict[tuple[int, int, int], cvc5.Term]) -> cvc5.Term:
    if probe == "Z":
        return _cvc5_add(tm, [w for (z, _x, _y), w in weights.items() if z == 1])
    if probe == "X":
        return _cvc5_add(tm, [w for (_z, x, _y), w in weights.items() if x == 1])
    if probe == "Y":
        return _cvc5_add(tm, [w for (_z, _x, y), w in weights.items() if y == 1])
    if probe in {"ZX", "XZ"}:
        return _cvc5_add(tm, [w for (z, x, _y), w in weights.items() if z == 1 and x == 1])
    raise ValueError(f"unknown probe {probe!r}")


def _cvc5_real_readout(tm: cvc5.TermManager, probe: str, a: cvc5.Term, b: cvc5.Term) -> cvc5.Term:
    half = tm.mkReal("1/2")
    quarter = tm.mkReal("1/4")
    if probe == "Z":
        return a
    if probe == "X":
        return tm.mkTerm(Kind.ADD, half, b)
    if probe == "Y":
        return half
    if probe == "ZX":
        return _cvc5_mul(tm, half, a)
    if probe == "XZ":
        return tm.mkTerm(Kind.ADD, quarter, _cvc5_mul(tm, half, b))
    raise ValueError(f"unknown probe {probe!r}")


def _cvc5_complex_readout(tm: cvc5.TermManager, probe: str, a: cvc5.Term, b: cvc5.Term, c: cvc5.Term) -> cvc5.Term:
    if probe == "Y":
        return tm.mkTerm(Kind.ADD, tm.mkReal("1/2"), c)
    return _cvc5_real_readout(tm, probe, a, b)


def _cvc5_decide(fixture: dict[str, Any], carrier_type: CarrierType, *, include_reproduce: bool) -> dict[str, Any]:
    measured = measured_from_fixture(fixture)
    probes = [str(probe) for probe in fixture["probes"]]
    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_NRA")
    solver.setOption("produce-models", "true")
    real_sort = tm.getRealSort()
    readout_terms: dict[str, cvc5.Term] = {}
    variables: dict[str, cvc5.Term] = {}
    prefix = f"cvc5_{fixture['name']}_{carrier_type}"
    zero = tm.mkReal("0")
    one = tm.mkReal("1")
    validity: list[str] = []

    if carrier_type == "quotient":
        for probe in probes:
            var = tm.mkConst(real_sort, f"{prefix}_{probe}")
            variables[f"q_{probe}"] = var
            solver.assertFormula(_cvc5_ge(tm, var, zero))
            solver.assertFormula(_cvc5_le(tm, var, one))
            readout_terms[probe] = var
        validity.append("0 <= q_probe <= 1 for each measured probe")
    elif carrier_type == "classical_noncontextual":
        weights = {
            assignment: tm.mkConst(real_sort, f"{prefix}_w_{assignment[0]}{assignment[1]}{assignment[2]}")
            for assignment in ASSIGNMENTS
        }
        variables = {f"w_z{z}x{x}y{y}": w for (z, x, y), w in weights.items()}
        for weight in weights.values():
            solver.assertFormula(_cvc5_ge(tm, weight, zero))
        solver.assertFormula(_cvc5_eq(tm, _cvc5_add(tm, list(weights.values())), one))
        for probe in probes:
            readout_terms[probe] = _cvc5_classical_readout(tm, probe, weights)
        validity.append("weights over deterministic Z/X/Y assignments are nonnegative and sum to 1")
        validity.append("ZX and XZ are the same non-disturbing joint event")
    elif carrier_type == "real_rebit":
        a = tm.mkConst(real_sort, f"{prefix}_a")
        b = tm.mkConst(real_sort, f"{prefix}_b")
        variables = {"a": a, "b": b}
        solver.assertFormula(_cvc5_ge(tm, a, zero))
        solver.assertFormula(_cvc5_le(tm, a, one))
        solver.assertFormula(
            _cvc5_ge(
                tm,
                _cvc5_sub(tm, _cvc5_mul(tm, a, _cvc5_sub(tm, one, a)), _cvc5_mul(tm, b, b)),
                zero,
            )
        )
        for probe in probes:
            readout_terms[probe] = _cvc5_real_readout(tm, probe, a, b)
        validity.append("rho_R=[[a,b],[b,1-a]], 0 <= a <= 1, a*(1-a)-b^2 >= 0")
    elif carrier_type == "complex_rho":
        a = tm.mkConst(real_sort, f"{prefix}_a")
        b = tm.mkConst(real_sort, f"{prefix}_b")
        c = tm.mkConst(real_sort, f"{prefix}_c")
        variables = {"a": a, "b": b, "c": c}
        solver.assertFormula(_cvc5_ge(tm, a, zero))
        solver.assertFormula(_cvc5_le(tm, a, one))
        solver.assertFormula(
            _cvc5_ge(
                tm,
                _cvc5_sub(
                    tm,
                    _cvc5_mul(tm, a, _cvc5_sub(tm, one, a)),
                    tm.mkTerm(Kind.ADD, _cvc5_mul(tm, b, b), _cvc5_mul(tm, c, c)),
                ),
                zero,
            )
        )
        for probe in probes:
            readout_terms[probe] = _cvc5_complex_readout(tm, probe, a, b, c)
        validity.append("rho=[[a,b-i*c],[b+i*c,1-a]], 0 <= a <= 1, a*(1-a)-b^2-c^2 >= 0")
    else:
        raise ValueError(f"unknown carrier_type {carrier_type!r}")

    if include_reproduce:
        for probe in probes:
            solver.assertFormula(_cvc5_eq(tm, readout_terms[probe], _cvc5_real(tm, measured[probe])))

    status = str(solver.checkSat()).lower()
    witness = None
    if status == "sat":
        witness = {name: str(solver.getValue(var)) for name, var in sorted(variables.items())}
    return {
        "solver": "cvc5",
        "solver_logic": "QF_NRA",
        "solver_status": status,
        "carrier_type": carrier_type,
        "fixture": fixture["name"],
        "admission": "admitted" if status == "sat" else "excluded" if status == "unsat" else "unknown",
        "verdict_source": "str(solver.checkSat())",
        "probes": probes,
        "measured": {probe: fraction_text(value) for probe, value in measured.items()},
        "include_reproduce": include_reproduce,
        "readout_binding": "readout_T(C, probe) == measured_probe for every listed probe" if include_reproduce else "omitted",
        "validity_constraints": validity,
        "free_variables": {name: f"{name}:Real" for name in sorted(variables)},
        "witness": witness,
    }


def decide(
    fixture: dict[str, Any],
    carrier_type: CarrierType,
    solver_name: SolverName,
    *,
    include_reproduce: bool = True,
) -> dict[str, Any]:
    if solver_name == "z3":
        return _z3_decide(fixture, carrier_type, include_reproduce=include_reproduce)
    if solver_name == "cvc5":
        return _cvc5_decide(fixture, carrier_type, include_reproduce=include_reproduce)
    raise ValueError(f"unknown solver_name {solver_name!r}")


def solve_fixture(fixture: dict[str, Any], solver_name: SolverName, *, include_reproduce: bool = True) -> dict[str, Any]:
    by_type = {
        carrier_type: decide(fixture, carrier_type, solver_name, include_reproduce=include_reproduce)
        for carrier_type in CARRIER_TYPES
    }
    allowed = [carrier_type for carrier_type, row in by_type.items() if row["solver_status"] == "sat"]
    excluded = [carrier_type for carrier_type, row in by_type.items() if row["solver_status"] == "unsat"]
    unknown = [carrier_type for carrier_type, row in by_type.items() if row["solver_status"] not in {"sat", "unsat"}]
    return {
        "solver": solver_name,
        "fixture": fixture["name"],
        "include_reproduce": include_reproduce,
        "allowed_set": allowed,
        "excluded_set": excluded,
        "unknown_set": unknown,
        "fixture_verdict": "installed" if len(allowed) >= 2 else "single_allowed_by_panel" if len(allowed) == 1 else "none_allowed",
        "by_type": by_type,
    }


def solve_group(spec: dict[str, Any], group: str, solver_name: SolverName, *, include_reproduce: bool = True) -> dict[str, Any]:
    return {
        name: solve_fixture(fixture_from_spec(spec, group, name), solver_name, include_reproduce=include_reproduce)
        for name in ordered_names(spec, group)
    }


def jax_fixture_table(spec: dict[str, Any]) -> dict[str, Any]:
    rows = []
    fixture_names = []
    for name, fixture in spec["headline_fixtures"].items():
        fixture_names.append(name)
        measured = measured_from_fixture(fixture)
        rows.append([float(measured[probe]) for probe in fixture["probes"]])
    widths = [len(row) for row in rows]
    flattened = jnp.asarray([value for row in rows for value in row], dtype=jnp.float64)
    return {
        "x64_enabled": bool(jax.config.jax_enable_x64),
        "fixture_names": fixture_names,
        "row_widths": widths,
        "measured_value_sum": float(jnp.sum(flattened)),
        "measured_value_count": int(flattened.size),
    }


def first_reproduce_diff_for_type(
    spec: dict[str, Any],
    headline: dict[str, Any],
    controls: dict[str, Any],
    carrier_type: CarrierType,
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for solver_name in ("z3", "cvc5"):
        selected = None
        for group_name, group in (("headline_fixtures", headline[solver_name]), ("load_bearing_controls", controls[solver_name])):
            for fixture_name in ordered_names(spec, group_name):
                on_row = group[fixture_name]
                off_row = None
                if group_name == "headline_fixtures":
                    off_row = headline[f"{solver_name}_reproduce_off"][fixture_name]
                else:
                    off_row = controls[f"{solver_name}_reproduce_off"][fixture_name]
                on_status = on_row["by_type"][carrier_type]["solver_status"]
                off_status = off_row["by_type"][carrier_type]["solver_status"]
                if on_status != off_status:
                    selected = {
                        "fixture": fixture_name,
                        "fixture_group": group_name,
                        "on": on_status,
                        "off": off_status,
                        "differs": True,
                    }
                    break
            if selected is not None:
                break
        if selected is None:
            selected = {"fixture": None, "on": None, "off": None, "differs": False}
        out[solver_name] = selected
    return out


def summarize_checks(spec: dict[str, Any], headline: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    solvers = ("z3", "cvc5")
    no_unknown = True
    for solver_name in solvers:
        for section in (headline[solver_name], controls[solver_name]):
            for row in section.values():
                if row["unknown_set"]:
                    no_unknown = False
    multiplicity = {
        solver_name: len(headline[solver_name]["marginal_multiplicity"]["allowed_set"]) >= 2
        for solver_name in solvers
    }
    exclusion = {
        solver_name: any(row["excluded_set"] and row["allowed_set"] for row in headline[solver_name].values())
        for solver_name in solvers
    }
    reproduce_by_type = {
        carrier_type: first_reproduce_diff_for_type(spec, headline, controls, carrier_type)
        for carrier_type in CARRIER_TYPES
    }
    reproduce_all = all(
        reproduce_by_type[carrier_type][solver_name]["differs"]
        for carrier_type in CARRIER_TYPES
        for solver_name in solvers
    )
    original = spec["scramble_pair"]["original"]
    scrambled = spec["scramble_pair"]["scrambled"]
    scramble_changes = {
        solver_name: headline[solver_name][original]["allowed_set"] != headline[solver_name][scrambled]["allowed_set"]
        for solver_name in solvers
    }
    allowed_sets = {
        solver_name: {name: row["allowed_set"] for name, row in headline[solver_name].items()}
        for solver_name in solvers
    }
    excluded_sets = {
        solver_name: {name: row["excluded_set"] for name, row in headline[solver_name].items()}
        for solver_name in solvers
    }
    allowed_varies = {
        solver_name: len({tuple(value) for value in allowed_sets[solver_name].values()}) > 1
        for solver_name in solvers
    }
    excluded_varies = {
        solver_name: len({tuple(value) for value in excluded_sets[solver_name].values()}) > 1
        for solver_name in solvers
    }
    expected_ok: dict[str, dict[str, bool]] = {}
    for solver_name in solvers:
        expected_ok[solver_name] = {}
        for name, fixture in spec["headline_fixtures"].items():
            row = headline[solver_name][name]
            allowed = set(row["allowed_set"])
            excluded = set(row["excluded_set"])
            allowed_contains = set(fixture.get("expected_allowed_contains", []))
            excluded_contains = set(fixture.get("expected_excluded_contains", fixture.get("expected_excluded", [])))
            expected_ok[solver_name][name] = allowed_contains <= allowed and excluded_contains <= excluded
    all_pass = (
        no_unknown
        and all(multiplicity.values())
        and all(exclusion.values())
        and reproduce_all
        and all(scramble_changes.values())
        and all(allowed_varies.values())
        and all(excluded_varies.values())
        and all(ok for solver_rows in expected_ok.values() for ok in solver_rows.values())
    )
    return {
        "no_unknown_headline_or_controls": no_unknown,
        "multiplicity_fixture_admits_at_least_two_types": multiplicity,
        "has_genuine_exclusion_fixture": exclusion,
        "reproduce_on_off_by_type": reproduce_by_type,
        "reproduce_on_off_all_types_differ": reproduce_all,
        "scramble_changes_allowed_set": scramble_changes,
        "allowed_set_varies_across_matrix": allowed_varies,
        "excluded_set_varies_across_matrix": excluded_varies,
        "expected_fixture_sets_present": expected_ok,
        "all_pass": all_pass,
    }


def subset_fixture(fixture: dict[str, Any], name: str, probes: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "group": "order_gap_clean_isolation",
        "role": "ISOLATION_CHECK",
        "probes": probes,
        "measured": {probe: fixture["measured"][probe] for probe in probes},
    }


def order_gap_clean_isolation(spec: dict[str, Any], solver_name: SolverName) -> dict[str, Any]:
    fixture = fixture_from_spec(spec, "headline_fixtures", "order_gap_clean")
    classical_base = decide(
        subset_fixture(fixture, "order_gap_clean_ZX_marginals", ["Z", "X"]),
        "classical_noncontextual",
        solver_name,
    )
    classical_zx = decide(
        subset_fixture(fixture, "order_gap_clean_ZX_branch", ["Z", "X", "ZX"]),
        "classical_noncontextual",
        solver_name,
    )
    classical_xz = decide(
        subset_fixture(fixture, "order_gap_clean_XZ_branch", ["Z", "X", "XZ"]),
        "classical_noncontextual",
        solver_name,
    )
    classical_joint = decide(fixture, "classical_noncontextual", solver_name)
    complex_joint = decide(fixture, "complex_rho", solver_name)
    passed = (
        classical_base["solver_status"] == "sat"
        and classical_zx["solver_status"] == "sat"
        and classical_xz["solver_status"] == "sat"
        and classical_joint["solver_status"] == "unsat"
        and complex_joint["solver_status"] == "sat"
    )
    return {
        "solver": solver_name,
        "fixture": "order_gap_clean",
        "expected_clean_values": {
            "Z": "1/2",
            "X": "3/4",
            "ZX": "1/4",
            "XZ": "3/8",
            "complex_rho_witness": {"a": "1/2", "b": "1/4"},
        },
        "classical_noncontextual": {
            "marginals_Z_X": classical_base["solver_status"],
            "branch_Z_X_ZX": classical_zx["solver_status"],
            "branch_Z_X_XZ": classical_xz["solver_status"],
            "joint_Z_X_ZX_XZ": classical_joint["solver_status"],
            "exclusion_mechanism": "one non-disturbing classical joint J cannot equal both ZX=1/4 and XZ=3/8",
        },
        "complex_rho": {
            "joint_Z_X_ZX_XZ": complex_joint["solver_status"],
            "witness": complex_joint["witness"],
        },
        "passed": passed,
    }


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    spec = load_spec()
    headline: dict[str, Any] = {}
    controls: dict[str, Any] = {}
    for solver_name in ("z3", "cvc5"):
        headline[solver_name] = solve_group(spec, "headline_fixtures", solver_name)
        headline[f"{solver_name}_reproduce_off"] = solve_group(spec, "headline_fixtures", solver_name, include_reproduce=False)
        controls[solver_name] = solve_group(spec, "load_bearing_controls", solver_name)
        controls[f"{solver_name}_reproduce_off"] = solve_group(spec, "load_bearing_controls", solver_name, include_reproduce=False)
    checks = summarize_checks(spec, headline, controls)
    isolation = {
        solver_name: order_gap_clean_isolation(spec, solver_name)
        for solver_name in ("z3", "cvc5")
    }
    isolation_pass = all(row["passed"] for row in isolation.values())
    checks["order_gap_clean_isolation_pass"] = isolation_pass
    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "jax_python_z3_cvc5",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": False,
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_path": str(Path(__file__).resolve()),
        "source_sha256": sha256_of(Path(__file__).resolve()),
        "spec_sha256": sha256_of(HERE / "spec.json"),
        "carrier_types": list(CARRIER_TYPES),
        "carrier_type_non_isomorphism": spec["carrier_type_non_isomorphism"],
        "readout_definitions": spec["readout_definitions"],
        "jax_observables": jax_fixture_table(spec),
        "headline_matrix": headline,
        "load_bearing_controls": controls,
        "headline_checks": checks,
        "multiplicity_witness": {
            "fixture": spec["multiplicity_witness_fixture"],
            "classical_noncontextual": headline["z3"][spec["multiplicity_witness_fixture"]]["by_type"]["classical_noncontextual"]["witness"],
            "complex_rho": headline["z3"][spec["multiplicity_witness_fixture"]]["by_type"]["complex_rho"]["witness"],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "package_observables": {
            "jax": "supportive x64 measured-table readback only",
            "jax.numpy": "supportive x64 measured-table readback only",
            "z3": "SAT/UNSAT allowed-set matrix and reproduce controls over free carrier variables",
            "cvc5": "independent SAT/UNSAT allowed-set matrix and reproduce controls over free carrier variables",
        },
        "tool_calls": [
            {
                "tool": "z3",
                "qualified_api/function": "z3.SolverFor('QF_NRA')/z3.Real/solver.check/model.eval",
                "input_object": "per-type free variables and readout equalities for each finite probe-table fixture",
                "output_object": "allowed/excluded carrier-type matrix",
                "positive_case": "marginal_multiplicity admits multiple non-isomorphic carrier categories",
                "negative/erased_control": "order_gap_clean excludes classical_noncontextual through the non-disturbing joint; invalid_probability flips reproduce ON/OFF",
                "boundary_case": "scrambled_order_gap changes the allowed set",
                "demotion_condition": "demote if any headline verdict is unknown or reproduce ON/OFF does not differ for every carrier type",
                "gates": ["proof", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver/checkSat/getValue with QF_NRA",
                "input_object": "same per-type free variables and readout equalities",
                "output_object": "independent allowed/excluded carrier-type matrix",
                "positive_case": "marginal_multiplicity admits multiple non-isomorphic carrier categories",
                "negative/erased_control": "order_gap_clean excludes classical_noncontextual through the non-disturbing joint; invalid_probability flips reproduce ON/OFF",
                "boundary_case": "scrambled_order_gap changes the allowed set",
                "demotion_condition": "demote if cvc5 returns unknown or disagrees with z3 on headline sets",
                "gates": ["proof", "all_pass"],
            },
        ],
        "claim_path_tools": ["z3", "cvc5"],
        "order_gap_clean_isolation": isolation,
        "all_pass": checks["all_pass"] and isolation_pass,
        "claim_ceiling": spec["claim_ceiling"],
        "surviving_alternatives": spec["surviving_alternatives"],
    }
    out_path = RESULTS / f"{SIM_ID}_jax_results.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": result["all_pass"],
                "result_path": str(out_path),
                "headline_allowed_sets": {
                    solver: {fixture: row["allowed_set"] for fixture, row in result["headline_matrix"][solver].items()}
                    for solver in ("z3", "cvc5")
                },
                "headline_excluded_sets": {
                    solver: {fixture: row["excluded_set"] for fixture, row in result["headline_matrix"][solver].items()}
                    for solver in ("z3", "cvc5")
                },
                "reproduce_on_off_by_type": checks["reproduce_on_off_by_type"],
                "order_gap_clean_isolation": isolation,
                "scramble_changes_allowed_set": checks["scramble_changes_allowed_set"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
