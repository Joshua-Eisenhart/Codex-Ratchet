#!/usr/bin/env python3
"""JAX/Python lane for the <=3Q nesting tower packet."""

from __future__ import annotations

import json

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import sympy as sp
import z3

from gcm_nesting_tower_le3q_v0_common import RESULT_DIR, build_packet, rel, write_json


jax.config.update("jax_enable_x64", True)
RESULT_PATH = RESULT_DIR / "gcm_nesting_tower_le3q_v0_jax_results.json"


def contradiction_guards(exact: int, probe: int) -> dict[str, object]:
    solver = z3.Solver()
    exact_var = z3.Int("jax_exact_family_count")
    probe_var = z3.Int("jax_probe_family_count")
    solver.add(exact_var == exact)
    solver.add(probe_var == probe)
    solver.add(z3.Or(exact_var != exact, probe_var != probe))
    z3_verdict = str(solver.check())

    csolver = cvc5.Solver()
    csolver.setLogic("QF_LIA")
    int_sort = csolver.getIntegerSort()
    c_exact = csolver.mkConst(int_sort, "jax_exact_family_count")
    c_probe = csolver.mkConst(int_sort, "jax_probe_family_count")
    csolver.assertFormula(csolver.mkTerm(Kind.EQUAL, c_exact, csolver.mkInteger(exact)))
    csolver.assertFormula(csolver.mkTerm(Kind.EQUAL, c_probe, csolver.mkInteger(probe)))
    csolver.assertFormula(
        csolver.mkTerm(
            Kind.OR,
            csolver.mkTerm(Kind.NOT, csolver.mkTerm(Kind.EQUAL, c_exact, csolver.mkInteger(exact))),
            csolver.mkTerm(Kind.NOT, csolver.mkTerm(Kind.EQUAL, c_probe, csolver.mkInteger(probe))),
        )
    )
    return {"z3": z3_verdict, "cvc5": str(csolver.checkSat()).lower()}


def main() -> int:
    packet = build_packet(write_negative=False)
    exact_values = jnp.array(
        [row["family_multiplicity"] for row in packet["compatible_families"]["exact_rows"]],
        dtype=jnp.int64,
    )
    probe_values = jnp.array(
        [row["family_multiplicity"] for row in packet["compatible_families"]["probe_rows"]],
        dtype=jnp.int64,
    )
    exact_sum = int(jax.device_get(jnp.sum(exact_values))) if exact_values.size else 0
    probe_sum = int(jax.device_get(jnp.sum(probe_values))) if probe_values.size else 0
    exact_guard = sp.Rational(exact_sum, 1)
    probe_guard = sp.Rational(probe_sum, 1)
    result = {
        "engine": "jax",
        "ran": True,
        "reads_peer_result": False,
        "source_path": "system_v6/sims/gcm_nesting_tower_le3q_v0/gcm_nesting_tower_le3q_v0_jax.py",
        "result_path": rel(RESULT_PATH),
        "packages_used": ["jax", "jax.numpy", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
        "package_observables": {
            "sympy": "sp.Rational exact/probe family count guards",
            "z3": "z3.Solver contradiction guard over exact/probe family counts",
            "cvc5": "cvc5.Solver contradiction guard over exact/probe family counts",
        },
        "claim_values": {
            "exact_all_cut_compatible_family_count": exact_sum,
            "probe_all_cut_compatible_family_count": probe_sum,
            "exact_sympy_guard": str(exact_guard),
            "probe_sympy_guard": str(probe_guard),
        },
        "contradiction_guards": contradiction_guards(exact_sum, probe_sum),
    }
    write_json(RESULT_PATH, result)
    print(json.dumps({"ok": True, "result_path": rel(RESULT_PATH), "claim_values": result["claim_values"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
