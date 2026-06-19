#!/usr/bin/env python3
"""Shared real-carrier SMT discriminator for forced_or_installed_carrier_comparison_v0."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Literal

import cvc5
from cvc5 import Kind
import z3

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "nonclassical"

TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing QF_NRA search for a second coordinate-distinct density carrier bound to measured probe readouts",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent QF_NRA search over the same carrier/readout constraints",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}

SolverName = Literal["z3", "cvc5"]
ProbeName = Literal["Z", "X", "Y"]
PROBES: tuple[ProbeName, ...] = ("Z", "X", "Y")


@dataclass(frozen=True)
class DensityCarrier:
    a: Fraction
    b: Fraction
    c: Fraction

    def readout(self, probe: str) -> Fraction:
        if probe == "Z":
            return 2 * self.a - 1
        if probe == "X":
            return 2 * self.b
        if probe == "Y":
            return 2 * self.c
        raise ValueError(f"unknown probe {probe!r}")

    @property
    def psd_margin(self) -> Fraction:
        return self.a * (1 - self.a) - self.b * self.b - self.c * self.c

    @property
    def is_psd(self) -> bool:
        return Fraction(0) <= self.a <= Fraction(1) and self.psd_margin >= 0

    def as_json(self) -> dict[str, str]:
        return {
            "a": fraction_text(self.a),
            "b": fraction_text(self.b),
            "c": fraction_text(self.c),
            "psd_margin": fraction_text(self.psd_margin),
        }


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


def carrier_from_spec(raw: dict[str, Any]) -> DensityCarrier:
    return DensityCarrier(
        a=parse_fraction(raw["a"]),
        b=parse_fraction(raw["b"]),
        c=parse_fraction(raw["c"]),
    )


def fixture_from_spec(spec: dict[str, Any], fixture_name: str) -> dict[str, Any]:
    fixture = dict(spec["fixtures"][fixture_name])
    fixture["name"] = fixture_name
    return fixture


def measured_from_fixture(fixture: dict[str, Any]) -> dict[str, Fraction]:
    return {str(probe): parse_fraction(value) for probe, value in fixture["measured"].items()}


def readouts_for(carrier: DensityCarrier, probes: list[str] | tuple[str, ...]) -> dict[str, str]:
    return {probe: fraction_text(carrier.readout(probe)) for probe in probes}


def readout_matches(carrier: DensityCarrier, measured: dict[str, Fraction]) -> bool:
    return all(carrier.readout(probe) == value for probe, value in measured.items())


def decision_from_status(status: str) -> str:
    if status == "sat":
        return "installed"
    if status == "unsat":
        return "forced"
    return "unknown"


def _z3_real(value: Fraction) -> z3.ArithRef:
    return z3.RealVal(fraction_text(value))


def _z3_readout(probe: str, a: z3.ArithRef, b: z3.ArithRef, c: z3.ArithRef) -> z3.ArithRef:
    if probe == "Z":
        return 2 * a - 1
    if probe == "X":
        return 2 * b
    if probe == "Y":
        return 2 * c
    raise ValueError(f"unknown probe {probe!r}")


def _z3_value_text(model: z3.ModelRef, var: z3.ArithRef) -> str:
    value = model.eval(var, model_completion=True)
    if isinstance(value, z3.RatNumRef):
        return fraction_text(Fraction(value.numerator_as_long(), value.denominator_as_long()))
    return str(value)


def _z3_decide(
    fixture: dict[str, Any],
    first_carrier: DensityCarrier,
    *,
    include_reproduce: bool,
    include_non_isomorphism: bool,
    require_readout_mismatch: bool,
    variable_prefix: str,
) -> dict[str, Any]:
    measured = measured_from_fixture(fixture)
    probes = [str(probe) for probe in fixture["probe_set"]]
    solver = z3.SolverFor("QF_NRA")
    a = z3.Real(f"{variable_prefix}_a")
    b = z3.Real(f"{variable_prefix}_b")
    c = z3.Real(f"{variable_prefix}_c")

    solver.add(a >= 0, a <= 1)
    solver.add(a * (1 - a) - (b * b + c * c) >= 0)

    if include_reproduce:
        for probe in probes:
            solver.add(_z3_readout(probe, a, b, c) == _z3_real(measured[probe]))

    if require_readout_mismatch:
        solver.add(
            z3.Or(
                [
                    _z3_readout(probe, a, b, c) != _z3_real(measured[probe])
                    for probe in probes
                ]
            )
        )

    if include_non_isomorphism:
        solver.add(
            z3.Or(
                a != _z3_real(first_carrier.a),
                b != _z3_real(first_carrier.b),
                c != _z3_real(first_carrier.c),
            )
        )

    status = str(solver.check()).lower()
    witness: dict[str, Any] | None = None
    if status == "sat":
        model = solver.model()
        witness = {
            "carrier": {
                "a": _z3_value_text(model, a),
                "b": _z3_value_text(model, b),
                "c": _z3_value_text(model, c),
            },
            "model_string": str(model),
        }

    return {
        "solver": "z3",
        "solver_logic": "QF_NRA",
        "solver_status": status,
        "verdict": decision_from_status(status),
        "verdict_source": "str(solver.check())",
        "fixture": fixture["name"],
        "carrier_type": "qubit_density_2x2_real_coordinates",
        "readout_definition": {
            "Z": "Tr(sigma_z rho)=2a-1",
            "X": "Tr(sigma_x rho)=2b",
            "Y": "declared sigma_y-orientation readout=2c",
        },
        "first_carrier": first_carrier.as_json(),
        "first_carrier_readouts": readouts_for(first_carrier, PROBES),
        "measured_probe_table": {probe: fraction_text(value) for probe, value in measured.items()},
        "probe_set": probes,
        "second_carrier_variables": {
            "a": f"{variable_prefix}_a:Real",
            "b": f"{variable_prefix}_b:Real",
            "c": f"{variable_prefix}_c:Real",
        },
        "constraints": {
            "carrier_psd": "0 <= a <= 1 and a*(1-a)-b^2-c^2 >= 0",
            "reproduce_table": include_reproduce,
            "reproduce_binding": "readout_k(C2) == measured_k for every active probe" if include_reproduce else "omitted",
            "non_isomorphism": include_non_isomorphism,
            "require_readout_mismatch": require_readout_mismatch,
        },
        "non_isomorphism_predicate": "coordinate inequality: (a,b,c) for C2 differs from C1; no gauge quotient is applied in v0",
        "first_carrier_reproduces_measured": readout_matches(first_carrier, measured),
        "witness": witness,
    }


def _cvc5_real(tm: cvc5.TermManager, value: Fraction) -> cvc5.Term:
    return tm.mkReal(fraction_text(value))


def _cvc5_and(tm: cvc5.TermManager, items: list[cvc5.Term]) -> cvc5.Term:
    if not items:
        return tm.mkBoolean(True)
    return items[0] if len(items) == 1 else tm.mkTerm(Kind.AND, *items)


def _cvc5_or(tm: cvc5.TermManager, items: list[cvc5.Term]) -> cvc5.Term:
    if not items:
        return tm.mkBoolean(False)
    return items[0] if len(items) == 1 else tm.mkTerm(Kind.OR, *items)


def _cvc5_add(tm: cvc5.TermManager, *items: cvc5.Term) -> cvc5.Term:
    return items[0] if len(items) == 1 else tm.mkTerm(Kind.ADD, *items)


def _cvc5_sub(tm: cvc5.TermManager, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return tm.mkTerm(Kind.SUB, left, right)


def _cvc5_mul(tm: cvc5.TermManager, *items: cvc5.Term) -> cvc5.Term:
    return items[0] if len(items) == 1 else tm.mkTerm(Kind.MULT, *items)


def _cvc5_eq(tm: cvc5.TermManager, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return tm.mkTerm(Kind.EQUAL, left, right)


def _cvc5_neq(tm: cvc5.TermManager, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return tm.mkTerm(Kind.DISTINCT, left, right)


def _cvc5_ge(tm: cvc5.TermManager, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return tm.mkTerm(Kind.GEQ, left, right)


def _cvc5_le(tm: cvc5.TermManager, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return tm.mkTerm(Kind.LEQ, left, right)


def _cvc5_readout(tm: cvc5.TermManager, probe: str, a: cvc5.Term, b: cvc5.Term, c: cvc5.Term) -> cvc5.Term:
    two = tm.mkReal("2")
    one = tm.mkReal("1")
    if probe == "Z":
        return _cvc5_sub(tm, _cvc5_mul(tm, two, a), one)
    if probe == "X":
        return _cvc5_mul(tm, two, b)
    if probe == "Y":
        return _cvc5_mul(tm, two, c)
    raise ValueError(f"unknown probe {probe!r}")


def _cvc5_decide(
    fixture: dict[str, Any],
    first_carrier: DensityCarrier,
    *,
    include_reproduce: bool,
    include_non_isomorphism: bool,
    require_readout_mismatch: bool,
    variable_prefix: str,
) -> dict[str, Any]:
    measured = measured_from_fixture(fixture)
    probes = [str(probe) for probe in fixture["probe_set"]]
    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_NRA")
    solver.setOption("produce-models", "true")
    real_sort = tm.getRealSort()
    a = tm.mkConst(real_sort, f"{variable_prefix}_a")
    b = tm.mkConst(real_sort, f"{variable_prefix}_b")
    c = tm.mkConst(real_sort, f"{variable_prefix}_c")
    zero = tm.mkReal("0")
    one = tm.mkReal("1")

    solver.assertFormula(_cvc5_ge(tm, a, zero))
    solver.assertFormula(_cvc5_le(tm, a, one))
    solver.assertFormula(
        _cvc5_ge(
            tm,
            _cvc5_sub(
                tm,
                _cvc5_mul(tm, a, _cvc5_sub(tm, one, a)),
                _cvc5_add(tm, _cvc5_mul(tm, b, b), _cvc5_mul(tm, c, c)),
            ),
            zero,
        )
    )

    if include_reproduce:
        for probe in probes:
            solver.assertFormula(_cvc5_eq(tm, _cvc5_readout(tm, probe, a, b, c), _cvc5_real(tm, measured[probe])))

    if require_readout_mismatch:
        solver.assertFormula(
            _cvc5_or(
                tm,
                [
                    _cvc5_neq(tm, _cvc5_readout(tm, probe, a, b, c), _cvc5_real(tm, measured[probe]))
                    for probe in probes
                ],
            )
        )

    if include_non_isomorphism:
        solver.assertFormula(
            _cvc5_or(
                tm,
                [
                    _cvc5_neq(tm, a, _cvc5_real(tm, first_carrier.a)),
                    _cvc5_neq(tm, b, _cvc5_real(tm, first_carrier.b)),
                    _cvc5_neq(tm, c, _cvc5_real(tm, first_carrier.c)),
                ],
            )
        )

    status = str(solver.checkSat()).lower()
    witness: dict[str, Any] | None = None
    if status == "sat":
        witness = {
            "carrier": {
                "a": str(solver.getValue(a)),
                "b": str(solver.getValue(b)),
                "c": str(solver.getValue(c)),
            },
            "model_string": "\n".join(
                [
                    f"{variable_prefix}_a -> {solver.getValue(a)}",
                    f"{variable_prefix}_b -> {solver.getValue(b)}",
                    f"{variable_prefix}_c -> {solver.getValue(c)}",
                ]
            ),
        }

    return {
        "solver": "cvc5",
        "solver_logic": "QF_NRA",
        "solver_status": status,
        "verdict": decision_from_status(status),
        "verdict_source": "str(solver.checkSat())",
        "fixture": fixture["name"],
        "carrier_type": "qubit_density_2x2_real_coordinates",
        "readout_definition": {
            "Z": "Tr(sigma_z rho)=2a-1",
            "X": "Tr(sigma_x rho)=2b",
            "Y": "declared sigma_y-orientation readout=2c",
        },
        "first_carrier": first_carrier.as_json(),
        "first_carrier_readouts": readouts_for(first_carrier, PROBES),
        "measured_probe_table": {probe: fraction_text(value) for probe, value in measured.items()},
        "probe_set": probes,
        "second_carrier_variables": {
            "a": f"{variable_prefix}_a:Real",
            "b": f"{variable_prefix}_b:Real",
            "c": f"{variable_prefix}_c:Real",
        },
        "constraints": {
            "carrier_psd": "0 <= a <= 1 and a*(1-a)-b^2-c^2 >= 0",
            "reproduce_table": include_reproduce,
            "reproduce_binding": "readout_k(C2) == measured_k for every active probe" if include_reproduce else "omitted",
            "non_isomorphism": include_non_isomorphism,
            "require_readout_mismatch": require_readout_mismatch,
        },
        "non_isomorphism_predicate": "coordinate inequality: (a,b,c) for C2 differs from C1; no gauge quotient is applied in v0",
        "first_carrier_reproduces_measured": readout_matches(first_carrier, measured),
        "witness": witness,
    }


def decide_fixture(
    fixture: dict[str, Any],
    first_carrier: DensityCarrier,
    solver_name: SolverName,
    *,
    include_reproduce: bool = True,
    include_non_isomorphism: bool = True,
    require_readout_mismatch: bool = False,
    variable_prefix: str = "c2",
) -> dict[str, Any]:
    if include_reproduce and require_readout_mismatch:
        raise ValueError("include_reproduce and require_readout_mismatch are contradictory")
    if solver_name == "z3":
        return _z3_decide(
            fixture,
            first_carrier,
            include_reproduce=include_reproduce,
            include_non_isomorphism=include_non_isomorphism,
            require_readout_mismatch=require_readout_mismatch,
            variable_prefix=variable_prefix,
        )
    if solver_name == "cvc5":
        return _cvc5_decide(
            fixture,
            first_carrier,
            include_reproduce=include_reproduce,
            include_non_isomorphism=include_non_isomorphism,
            require_readout_mismatch=require_readout_mismatch,
            variable_prefix=variable_prefix,
        )
    raise ValueError(f"unknown solver_name: {solver_name}")


def run_all_decisions(spec: dict[str, Any]) -> dict[str, Any]:
    first_carrier = carrier_from_spec(spec["first_carrier"])
    installed = fixture_from_spec(spec, "installed_incomplete")
    forced = fixture_from_spec(spec, "forced_complete")
    forced_scrambled = fixture_from_spec(spec, "forced_complete_scrambled")
    installed_scrambled = fixture_from_spec(spec, "installed_incomplete_scrambled")
    impossible = fixture_from_spec(spec, "invalid_measured_z")

    solvers: tuple[SolverName, ...] = ("z3", "cvc5")
    return {
        "installed_incomplete": {
            solver: decide_fixture(installed, first_carrier, solver, variable_prefix=f"{solver}_installed_c2")
            for solver in solvers
        },
        "forced_complete": {
            solver: decide_fixture(forced, first_carrier, solver, variable_prefix=f"{solver}_forced_c2")
            for solver in solvers
        },
        "load_bearing_controls": {
            "installed_reproduce_off": {
                solver: decide_fixture(
                    installed,
                    first_carrier,
                    solver,
                    include_reproduce=False,
                    variable_prefix=f"{solver}_installed_no_reproduce_c2",
                )
                for solver in solvers
            },
            "installed_reproduce_off_mismatch": {
                solver: decide_fixture(
                    installed,
                    first_carrier,
                    solver,
                    include_reproduce=False,
                    require_readout_mismatch=True,
                    variable_prefix=f"{solver}_installed_no_reproduce_mismatch_c2",
                )
                for solver in solvers
            },
            "forced_reproduce_off": {
                solver: decide_fixture(
                    forced,
                    first_carrier,
                    solver,
                    include_reproduce=False,
                    variable_prefix=f"{solver}_forced_no_reproduce_c2",
                )
                for solver in solvers
            },
            "forced_reproduce_off_mismatch": {
                solver: decide_fixture(
                    forced,
                    first_carrier,
                    solver,
                    include_reproduce=False,
                    require_readout_mismatch=True,
                    variable_prefix=f"{solver}_forced_no_reproduce_mismatch_c2",
                )
                for solver in solvers
            },
            "installed_without_non_isomorphism": {
                solver: decide_fixture(
                    installed,
                    first_carrier,
                    solver,
                    include_non_isomorphism=False,
                    variable_prefix=f"{solver}_installed_no_noniso_c2",
                )
                for solver in solvers
            },
            "forced_without_non_isomorphism": {
                solver: decide_fixture(
                    forced,
                    first_carrier,
                    solver,
                    include_non_isomorphism=False,
                    variable_prefix=f"{solver}_forced_no_noniso_c2",
                )
                for solver in solvers
            },
            "installed_scrambled_values": {
                solver: decide_fixture(
                    installed_scrambled,
                    first_carrier,
                    solver,
                    variable_prefix=f"{solver}_installed_scrambled_c2",
                )
                for solver in solvers
            },
            "forced_scrambled_values": {
                solver: decide_fixture(
                    forced_scrambled,
                    first_carrier,
                    solver,
                    variable_prefix=f"{solver}_forced_scrambled_c2",
                )
                for solver in solvers
            },
            "invalid_measured_z_reproduce_on": {
                solver: decide_fixture(
                    impossible,
                    first_carrier,
                    solver,
                    variable_prefix=f"{solver}_invalid_z_c2",
                )
                for solver in solvers
            },
            "invalid_measured_z_reproduce_off": {
                solver: decide_fixture(
                    impossible,
                    first_carrier,
                    solver,
                    include_reproduce=False,
                    variable_prefix=f"{solver}_invalid_z_no_reproduce_c2",
                )
                for solver in solvers
            },
            "invalid_measured_z_reproduce_off_mismatch": {
                solver: decide_fixture(
                    impossible,
                    first_carrier,
                    solver,
                    include_reproduce=False,
                    require_readout_mismatch=True,
                    variable_prefix=f"{solver}_invalid_z_no_reproduce_mismatch_c2",
                )
                for solver in solvers
            },
        },
    }


def status_matrix(decisions: dict[str, Any], fixture_key: str) -> dict[str, str]:
    return {
        solver: row["solver_status"]
        for solver, row in decisions[fixture_key].items()
    }


def verdict_matrix(decisions: dict[str, Any], fixture_key: str) -> dict[str, str]:
    return {
        solver: row["verdict"]
        for solver, row in decisions[fixture_key].items()
    }


def headline_checks(decisions: dict[str, Any]) -> dict[str, Any]:
    solvers = ("z3", "cvc5")
    forced_status = status_matrix(decisions, "forced_complete")
    installed_status = status_matrix(decisions, "installed_incomplete")
    controls = decisions["load_bearing_controls"]
    unknowns: list[str] = []
    for section_name, section in decisions.items():
        if section_name == "load_bearing_controls":
            for control_name, control in section.items():
                for solver, row in control.items():
                    if row["solver_status"] == "unknown":
                        unknowns.append(f"{control_name}:{solver}")
        else:
            for solver, row in section.items():
                if row["solver_status"] == "unknown":
                    unknowns.append(f"{section_name}:{solver}")

    reproduce_diff = {
        solver: {
            "installed_on": installed_status[solver],
            "installed_off": controls["installed_reproduce_off"][solver]["solver_status"],
            "installed_off_mismatch": controls["installed_reproduce_off_mismatch"][solver]["solver_status"],
            "forced_on": forced_status[solver],
            "forced_off": controls["forced_reproduce_off"][solver]["solver_status"],
            "forced_off_mismatch": controls["forced_reproduce_off_mismatch"][solver]["solver_status"],
            "forced_status_differs": forced_status[solver] != controls["forced_reproduce_off"][solver]["solver_status"],
            "invalid_on": controls["invalid_measured_z_reproduce_on"][solver]["solver_status"],
            "invalid_off": controls["invalid_measured_z_reproduce_off"][solver]["solver_status"],
            "invalid_off_mismatch": controls["invalid_measured_z_reproduce_off_mismatch"][solver]["solver_status"],
            "invalid_status_differs": controls["invalid_measured_z_reproduce_on"][solver]["solver_status"]
            != controls["invalid_measured_z_reproduce_off"][solver]["solver_status"],
        }
        for solver in solvers
    }
    return {
        "installed_fixture_sat": all(installed_status[solver] == "sat" for solver in solvers),
        "forced_fixture_unsat": all(forced_status[solver] == "unsat" for solver in solvers),
        "no_unknown_headline": not unknowns,
        "unknowns": unknowns,
        "noniso_off_is_sat": all(
            controls[control][solver]["solver_status"] == "sat"
            for control in ("installed_without_non_isomorphism", "forced_without_non_isomorphism")
            for solver in solvers
        ),
        "reproduce_on_off_differs": all(
            reproduce_diff[solver]["forced_status_differs"] and reproduce_diff[solver]["invalid_status_differs"]
            for solver in solvers
        ),
        "scramble_changes_forced_verdict": all(
            controls["forced_scrambled_values"][solver]["solver_status"] == "sat"
            for solver in solvers
        ),
        "scramble_keeps_installed_sat_with_different_table": all(
            controls["installed_scrambled_values"][solver]["solver_status"] == "sat"
            for solver in solvers
        ),
        "reproduce_on_off": reproduce_diff,
    }
