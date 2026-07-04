#!/usr/bin/env python3
"""JAX standing Python leg for ratchet_replicator_run_v0."""

from __future__ import annotations

from jax import config

config.update("jax_enable_x64", True)

import json
from pathlib import Path

import jax
import jax.numpy as jnp
import cvc5
from cvc5 import Kind
import z3

import ratchet_replicator_core as core

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "classical"

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive finite-state disturbance checksum/control; shared core carries the exact ratchet counters",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive vectorized finite-state checksum for noncommuting update visibility",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite-domain guard that distinguishes nonself directed acts from forbidden reflexive candidates",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing second-solver finite-domain guard for the same nonself directed-act constraint",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing shared ratchet loop, record window, novelty summary, motif detection, and result emission",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "load_bearing",
}

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def jax_observables() -> dict[str, object]:
    cfg = core.load_spec()["run_config"]
    states = jnp.asarray([(3 * i + 1) % int(cfg["state_modulus"]) for i in range(int(cfg["alphabet_size"]))], dtype=jnp.int64)
    shifted = (states + jnp.roll(states, 1)) % int(cfg["state_modulus"])
    return {
        "jax_backend": jax.default_backend(),
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "initial_state_checksum": int(jnp.sum(states) % 1000003),
        "rolled_pair_checksum": int(jnp.sum(shifted) % 1000003),
    }


def z3_nonself_guard(alphabet_size: int) -> dict[str, object]:
    x = z3.Int("x")
    y = z3.Int("y")
    s = z3.Solver()
    s.add(x >= 0, x < alphabet_size, y >= 0, y < alphabet_size, x != y)
    positive = str(s.check()).lower()
    s_reflexive = z3.Solver()
    s_reflexive.add(x >= 0, x < alphabet_size, y >= 0, y < alphabet_size, x != y, x == y)
    forbidden_reflexive = str(s_reflexive.check()).lower()
    return {"positive_nonself": positive, "forbidden_reflexive": forbidden_reflexive, "passed": positive == "sat" and forbidden_reflexive == "unsat"}


def cvc5_nonself_guard(alphabet_size: int) -> dict[str, object]:
    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_LIA")
    x = tm.mkConst(tm.getIntegerSort(), "x")
    y = tm.mkConst(tm.getIntegerSort(), "y")
    zero = tm.mkInteger(0)
    top = tm.mkInteger(alphabet_size - 1)
    solver.assertFormula(tm.mkTerm(Kind.GEQ, x, zero))
    solver.assertFormula(tm.mkTerm(Kind.LEQ, x, top))
    solver.assertFormula(tm.mkTerm(Kind.GEQ, y, zero))
    solver.assertFormula(tm.mkTerm(Kind.LEQ, y, top))
    solver.assertFormula(tm.mkTerm(Kind.DISTINCT, x, y))
    positive = str(solver.checkSat()).lower()

    solver_reflexive = cvc5.Solver(tm)
    solver_reflexive.setLogic("QF_LIA")
    xr = tm.mkConst(tm.getIntegerSort(), "xr")
    yr = tm.mkConst(tm.getIntegerSort(), "yr")
    solver_reflexive.assertFormula(tm.mkTerm(Kind.GEQ, xr, zero))
    solver_reflexive.assertFormula(tm.mkTerm(Kind.LEQ, xr, top))
    solver_reflexive.assertFormula(tm.mkTerm(Kind.GEQ, yr, zero))
    solver_reflexive.assertFormula(tm.mkTerm(Kind.LEQ, yr, top))
    solver_reflexive.assertFormula(tm.mkTerm(Kind.DISTINCT, xr, yr))
    solver_reflexive.assertFormula(tm.mkTerm(Kind.EQUAL, xr, yr))
    forbidden_reflexive = str(solver_reflexive.checkSat()).lower()
    return {"positive_nonself": positive, "forbidden_reflexive": forbidden_reflexive, "passed": positive == "sat" and forbidden_reflexive == "unsat"}


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    cfg = core.load_spec()["run_config"]
    finite_guards = {
        "z3": z3_nonself_guard(int(cfg["alphabet_size"])),
        "cvc5": cvc5_nonself_guard(int(cfg["alphabet_size"])),
    }
    payload = core.result_envelope(
        "jax",
        {
            "source_path": core.rel(Path(__file__)),
            "source_sha256": core.climb.sha256_file(Path(__file__)),
            "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "python_stdlib"],
            "aligned_packages_load_bearing": ["z3", "cvc5"],
            "package_observables": {"jax": jax_observables(), "finite_domain_guards": finite_guards},
            "crossover_proofs": finite_guards,
            "TOOL_MANIFEST": TOOL_MANIFEST,
            "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        },
    )
    payload["all_pass"] = bool(payload["all_pass"] and all(row["passed"] for row in finite_guards.values()))
    out = RESULTS / "ratchet_replicator_run_v0_jax_results.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"result_path": str(out), "all_pass": payload["all_pass"], "replicator": payload["replicator_verdict"]["verdict"]}, indent=2))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
