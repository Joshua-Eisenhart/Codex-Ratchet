#!/usr/bin/env python3
"""JAX/Python lane for gcm_nested_geometry_delta_3q_v0."""

from __future__ import annotations

import json

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import sympy as sp
import z3

from gcm_nested_geometry_delta_3q_v0_common import RESULT_DIR, build_packet, engine_claim_values, rel, write_json


jax.config.update("jax_enable_x64", True)
RESULT_PATH = RESULT_DIR / "gcm_nested_geometry_delta_3q_v0_jax_results.json"


def contradiction_guards(values: dict[str, int]) -> dict[str, str]:
    solver = z3.Solver()
    z_vars = {name: z3.Int(name) for name in values}
    for name, value in values.items():
        solver.add(z_vars[name] == int(value))
    solver.add(z3.Or([z_vars[name] != int(value) for name, value in values.items()]))
    z3_verdict = str(solver.check())

    csolver = cvc5.Solver()
    csolver.setLogic("QF_LIA")
    int_sort = csolver.getIntegerSort()
    c_vars = {name: csolver.mkConst(int_sort, name) for name in values}
    for name, value in values.items():
        csolver.assertFormula(csolver.mkTerm(Kind.EQUAL, c_vars[name], csolver.mkInteger(int(value))))
    csolver.assertFormula(
        csolver.mkTerm(
            Kind.OR,
            *[
                csolver.mkTerm(Kind.NOT, csolver.mkTerm(Kind.EQUAL, c_vars[name], csolver.mkInteger(int(value))))
                for name, value in values.items()
            ],
        )
    )
    return {"z3": z3_verdict, "cvc5": str(csolver.checkSat()).lower()}


def main() -> int:
    packet = build_packet(write_result=False)
    values = engine_claim_values(packet)
    vector = jnp.array(
        [
            values["main_delta_l1_scaled"],
            values["same_input_null_delta_l1_scaled"],
            values["same_input_stable_delta_l1_scaled"],
            values["alternate_pin_delta_l1_scaled"],
            values["alternate_probe_delta_l1_scaled"],
        ],
        dtype=jnp.int64,
    )
    echoed = [int(value) for value in jax.device_get(vector)]
    rational_main = sp.Rational(echoed[0], 1_000_000_000)
    rational_null = sp.Rational(echoed[1], 1_000_000_000)
    rational_stable = sp.Rational(echoed[2], 1_000_000_000)
    rational_alt_pin = sp.Rational(echoed[3], 1_000_000_000)
    rational_alt_probe = sp.Rational(echoed[4], 1_000_000_000)
    result = {
        "engine": "jax",
        "ran": True,
        "reads_peer_result": False,
        "source_path": "system_v6/sims/gcm_nested_geometry_delta_3q_v0/gcm_nested_geometry_delta_3q_v0_jax.py",
        "result_path": rel(RESULT_PATH),
        "packages_used": ["jax", "jax.numpy", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": [],
        "aligned_packages_supportive": ["jax.numpy", "sympy", "z3", "cvc5"],
        "engine_role": "scaled_value_guard",
        "claim_path_depth": "supportive",
        "engine_independence_ceiling": "supportive scaled-value and solver guard over packet values; not an independent geometry recompute",
        "package_observables": {
            "jax.numpy": "jnp.array/device_get roundtrip for scaled packet values",
            "sympy": "supportive sp.Rational exact guards for scaled main/null/alternate delta values",
            "z3": "supportive z3.Solver contradiction guard over recorded scaled delta values",
            "cvc5": "supportive cvc5.Solver contradiction guard over recorded scaled delta values",
        },
        "claim_values": {
            **values,
            "main_delta_rational": str(rational_main),
            "same_input_null_delta_rational": str(rational_null),
            "same_input_stable_delta_rational": str(rational_stable),
            "alternate_pin_delta_rational": str(rational_alt_pin),
            "alternate_probe_delta_rational": str(rational_alt_probe),
        },
        "contradiction_guards": contradiction_guards(values),
    }
    write_json(RESULT_PATH, result)
    print(json.dumps({"ok": True, "result_path": rel(RESULT_PATH), "claim_values": result["claim_values"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
