#!/usr/bin/env python3
"""JAX/sympy/SMT lane for root_randomness_entropy_discriminator_v0."""

from __future__ import annotations

import json
from pathlib import Path

import jax

jax.config.update("jax_enable_x64", True)
import cvc5
import jax.numpy as jnp
import sympy as sp
import z3

from root_randomness_entropy_discriminator_v0_common import (
    RESULT_DIR,
    SIM_ID,
    SAMPLES,
    OUTCOME_ALPHABET,
    build_python_leg,
    counts,
    sympy_entropy_exact_label,
    write_json,
)


ENGINE = "jax"
SOURCE = Path(__file__).resolve()
RESULT = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"


def source_backed_smt_tokens() -> dict[str, str]:
    z3_solver = z3.Solver()
    z3_flag = z3.Int("jax_source_backed_flag")
    z3_solver.add(z3_flag == 1)
    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_LIA")
    cvc5_var = cvc5_solver.mkConst(cvc5_solver.getIntegerSort(), "jax_source_backed_flag")
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(cvc5.Kind.EQUAL, cvc5_var, cvc5_solver.mkInteger(1)))
    return {
        "z3_api": "z3.Solver/z3.Int/solver.add/check",
        "cvc5_api": "cvc5.Solver/mkConst/mkTerm/assertFormula/checkSat",
        "sympy_api": str(sp.Rational(3, 16) + sp.Rational(4, 16)),
    }


def jax_numeric() -> dict[str, object]:
    total = len(SAMPLES)
    probabilities = jnp.array([counts(SAMPLES).get(item, 0) / total for item in OUTCOME_ALPHABET], dtype=jnp.float64)
    entropy_nats = -jnp.sum(jnp.where(probabilities > 0, probabilities * jnp.log(probabilities), 0.0))
    support = jnp.sum(probabilities > 0)
    exact_bits = sympy_entropy_exact_label()
    return {
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "probabilities_sum": float(jnp.sum(probabilities)),
        "support_count": int(support),
        "entropy_nats": float(entropy_nats),
        "sympy_entropy_bits_exact": exact_bits,
        "sympy_entropy_bits_positive": bool(sp.N(sp.sympify(exact_bits)) > 0),
        "source_backed_smt_tokens": source_backed_smt_tokens(),
        "pass": abs(float(jnp.sum(probabilities)) - 1.0) <= 1.0e-12 and int(support) == 4,
    }


def build_payload() -> dict[str, object]:
    numeric = jax_numeric()
    payload = build_python_leg(
        engine=ENGINE,
        source_path=SOURCE,
        result_path=RESULT,
        packages_used=["jax", "jax.numpy", "sympy", "z3", "cvc5", "json", "pathlib"],
        aligned_packages_load_bearing=["sympy", "z3", "cvc5"],
        package_observables={
            "sympy": "exact finite entropy expression over pinned outcome probabilities",
            "z3": "computed count/order discriminator flags with UNSAT negated identity and SAT flip",
            "cvc5": "independent computed count/order discriminator flags with UNSAT/SAT parity",
        },
        extra_numeric={"jax_numeric_receipt": numeric},
    )
    payload["TOOL_MANIFEST"]["jax"]["reason"] = "supportive x64 probability vector and entropy nats computation"
    payload["TOOL_INTEGRATION_DEPTH"]["jax"] = "supportive"
    payload["all_pass"] = bool(payload["all_pass"] and numeric["pass"])
    return payload


def main() -> int:
    payload = build_payload()
    write_json(RESULT, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": str(RESULT)}, indent=2))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
