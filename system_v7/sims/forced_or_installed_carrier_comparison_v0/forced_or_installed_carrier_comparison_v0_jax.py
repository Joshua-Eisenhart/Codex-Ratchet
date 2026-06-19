#!/usr/bin/env python3
"""Python/JAX leg for forced_or_installed_carrier_comparison_v0."""

from __future__ import annotations

from jax import config

config.update("jax_enable_x64", True)

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import z3

from carrier_decision_core import (
    PROBES,
    carrier_from_spec,
    headline_checks,
    parse_fraction,
    readouts_for,
    run_all_decisions,
)

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "nonclassical"

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 readback of C1 readout vector before SMT checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing QF_NRA second-density-carrier existence search bound to measured readouts",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent QF_NRA check of the same readout-bound carrier search",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}

SIM_ID = "forced_or_installed_carrier_comparison_v0"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_spec() -> dict[str, Any]:
    return json.loads((HERE / "spec.json").read_text(encoding="utf-8"))


def jax_readout_vector(first_carrier: dict[str, str]) -> dict[str, float]:
    a = jnp.asarray(float(parse_fraction(first_carrier["a"])), dtype=jnp.float64)
    b = jnp.asarray(float(parse_fraction(first_carrier["b"])), dtype=jnp.float64)
    c = jnp.asarray(float(parse_fraction(first_carrier["c"])), dtype=jnp.float64)
    return {
        "Z": float(2 * a - 1),
        "X": float(2 * b),
        "Y": float(2 * c),
    }


def assert_solver_source_backing() -> None:
    z3_solver = z3.Solver()
    z3_a = z3.Real("jax_source_backed_a")
    z3_solver.add(z3_a == z3.RealVal("1/2"))
    if str(z3_solver.check()).lower() != "sat":
        raise RuntimeError("z3 source-backing smoke check failed")

    tm = cvc5.TermManager()
    cvc5_solver = cvc5.Solver(tm)
    cvc5_solver.setLogic("QF_NRA")
    real_sort = tm.getRealSort()
    cvc5_a = tm.mkConst(real_sort, "jax_source_backed_a")
    cvc5_solver.assertFormula(tm.mkTerm(Kind.EQUAL, cvc5_a, tm.mkReal("1/2")))
    if str(cvc5_solver.checkSat()).lower() != "sat":
        raise RuntimeError("cvc5 source-backing smoke check failed")


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    assert_solver_source_backing()
    spec = load_spec()
    first_carrier = carrier_from_spec(spec["first_carrier"])
    decisions = run_all_decisions(spec)
    checks = headline_checks(decisions)
    all_pass = (
        checks["installed_fixture_sat"]
        and checks["forced_fixture_unsat"]
        and checks["no_unknown_headline"]
        and checks["noniso_off_is_sat"]
        and checks["reproduce_on_off_differs"]
        and checks["scramble_changes_forced_verdict"]
        and checks["scramble_keeps_installed_sat_with_different_table"]
    )
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
        "carrier_type": spec["carrier_type"],
        "readout_definition": spec["readout_definition"],
        "first_carrier": first_carrier.as_json(),
        "first_carrier_readouts": readouts_for(first_carrier, PROBES),
        "jax_observables": {
            "x64_enabled": bool(jax.config.jax_enable_x64),
            "first_carrier_readout_vector_float": jax_readout_vector(spec["first_carrier"]),
        },
        "fixture_results": decisions,
        "headline_checks": checks,
        "same_decide_code": "carrier_decision_core.decide_fixture",
        "non_isomorphism_predicate": spec["non_isomorphism_predicate"],
        "positive_tests": {
            "installed_incomplete": "SAT under z3 and cvc5; C2 reproduces Z/X and differs in the unmeasured carrier coordinate",
            "forced_complete": "UNSAT under z3 and cvc5; Z/X/Y pins C2 coordinates to C1",
        },
        "negative_tests": {
            "reproduce_off_mismatch": "SAT controls show that removing reproduce admits table-mismatch witnesses",
            "non_isomorphism_off": "SAT controls show C2=C1 remains available when non-isomorphism is removed",
            "scrambled_complete": "SAT control shows forced does not hold for all same-cardinality complete tables",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "package_observables": {
            "jax": "supportive C1 readout vector only",
            "jax.numpy": "supportive x64 scalar readback only",
            "z3": "QF_NRA installed SAT and forced UNSAT second-carrier searches plus load-bearing controls",
            "cvc5": "independent QF_NRA installed SAT and forced UNSAT second-carrier searches plus load-bearing controls",
        },
        "tool_calls": [
            {
                "tool": "z3",
                "qualified_api/function": "z3.SolverFor('QF_NRA')/z3.Real/solver.check/model.eval",
                "input_object": "free C2 density coordinates a,b,c with PSD, reproduce, and non-isomorphism constraints",
                "output_object": "SAT installed witness and UNSAT complete-table coordinate-uniqueness result",
                "positive_case": "Z/X incomplete table admits a coordinate-distinct C2",
                "negative/erased_control": "Z/X/Y complete table rejects coordinate-distinct C2; reproduce-off mismatch controls are SAT",
                "boundary_case": "scrambled complete table is SAT, so forced is value-coupled",
                "demotion_condition": "demote if C2 variables are not free or reproduce readout equalities are removed from the claim path",
                "gates": ["proof", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver/checkSat/getValue with QF_NRA",
                "input_object": "same free C2 density coordinates and readout constraints",
                "output_object": "independent SAT/UNSAT agreement with z3",
                "positive_case": "Z/X incomplete table admits a coordinate-distinct C2",
                "negative/erased_control": "Z/X/Y complete table rejects coordinate-distinct C2; reproduce-off mismatch controls are SAT",
                "boundary_case": "invalid Z=2 table is UNSAT with reproduce ON and SAT with reproduce OFF",
                "demotion_condition": "demote if cvc5 returns unknown or does not bind readout_k(C2)==measured_k",
                "gates": ["proof", "all_pass"],
            },
        ],
        "claim_path_tools": ["z3", "cvc5"],
        "all_pass": all_pass,
        "criteria_checked": [
            "installed_incomplete z3/cvc5 SAT",
            "forced_complete z3/cvc5 UNSAT",
            "no headline solver returned unknown",
            "reproduce ON/OFF controls differ for forced and invalid measured tables",
            "scrambled complete table flips to SAT",
            "non-isomorphism OFF controls are SAT",
        ],
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
                "installed": {k: v["verdict"] for k, v in decisions["installed_incomplete"].items()},
                "forced": {k: v["verdict"] for k, v in decisions["forced_complete"].items()},
                "reproduce_on_off": checks["reproduce_on_off"],
                "z3_installed_C2": decisions["installed_incomplete"]["z3"]["witness"],
                "cvc5_installed_C2": decisions["installed_incomplete"]["cvc5"]["witness"],
            },
            indent=2,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
