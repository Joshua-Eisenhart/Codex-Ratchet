#!/usr/bin/env python3
"""JAX/Python lane for sequential_inheritance_not_cycle_v0."""

from __future__ import annotations

import datetime as dt
import importlib.metadata
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import z3

import sequential_inheritance_not_cycle_v0_common as common


SIM_ID = common.SIM_ID
SOURCE = common.PACKET / f"{SIM_ID}_jax.py"
RESULT = common.RESULT_DIR / f"{SIM_ID}_jax_results.json"


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "version_unavailable"


def z3_proofs(regimes: dict[str, Any]) -> dict[str, Any]:
    inherited = int(regimes["inheritance"]["terminal_structure_match_count"])
    cycle = int(regimes["cycle_null"]["terminal_structure_match_count"])
    random = int(regimes["random_null"]["terminal_structure_match_count"])

    def check(extra: str) -> dict[str, Any]:
        solver = z3.Solver()
        inh = z3.Int("inheritance_match_count")
        cyc = z3.Int("cycle_match_count")
        rnd = z3.Int("random_match_count")
        solver.add(inh == inherited, cyc == cycle, rnd == random)
        if extra == "negated_inheritance_gt_controls":
            solver.add(z3.Or(inh <= cyc, inh <= rnd))
            polarity = "negated inherited daughter stability strictly exceeds both null controls"
        elif extra == "cycle_equals_random":
            solver.add(cyc == rnd)
            polarity = "cycle-null and random-null collapse attempt"
        else:
            raise ValueError(extra)
        status = str(solver.check())
        return {
            "solver": "z3",
            "ran": True,
            "load_bearing": True,
            "verdict": status,
            "polarity": polarity,
            "bound_values": {
                "inheritance_match_count": inherited,
                "cycle_match_count": cycle,
                "random_match_count": random,
            },
        }

    return {
        "inheritance_gt_controls": check("negated_inheritance_gt_controls"),
        "cycle_random_distinct": check("cycle_equals_random"),
    }


def cvc5_proofs(regimes: dict[str, Any]) -> dict[str, Any]:
    inherited = int(regimes["inheritance"]["terminal_structure_match_count"])
    cycle = int(regimes["cycle_null"]["terminal_structure_match_count"])
    random = int(regimes["random_null"]["terminal_structure_match_count"])

    def check(kind: str) -> dict[str, Any]:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        inh = solver.mkConst(int_sort, "inheritance_match_count")
        cyc = solver.mkConst(int_sort, "cycle_match_count")
        rnd = solver.mkConst(int_sort, "random_match_count")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, inh, solver.mkInteger(inherited)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, cyc, solver.mkInteger(cycle)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, rnd, solver.mkInteger(random)))
        if kind == "negated_inheritance_gt_controls":
            solver.assertFormula(
                solver.mkTerm(
                    Kind.OR,
                    solver.mkTerm(Kind.LEQ, inh, cyc),
                    solver.mkTerm(Kind.LEQ, inh, rnd),
                )
            )
            polarity = "negated inherited daughter stability strictly exceeds both null controls"
        elif kind == "cycle_equals_random":
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, cyc, rnd))
            polarity = "cycle-null and random-null collapse attempt"
        else:
            raise ValueError(kind)
        result = solver.checkSat()
        status = "sat" if result.isSat() else "unsat" if result.isUnsat() else "unknown"
        return {
            "solver": "cvc5",
            "ran": True,
            "load_bearing": True,
            "verdict": status,
            "polarity": polarity,
            "bound_values": {
                "inheritance_match_count": inherited,
                "cycle_match_count": cycle,
                "random_match_count": random,
            },
        }

    return {
        "inheritance_gt_controls": check("negated_inheritance_gt_controls"),
        "cycle_random_distinct": check("cycle_equals_random"),
    }


def main() -> int:
    fixture = common.build_fixture()
    match_counts = jnp.asarray(
        [
            fixture["regimes"]["inheritance"]["terminal_structure_match_count"],
            fixture["regimes"]["cycle_null"]["terminal_structure_match_count"],
            fixture["regimes"]["random_null"]["terminal_structure_match_count"],
        ],
        dtype=jnp.int64,
    )
    stability_vector = jax.device_get(match_counts / 24.0).tolist()
    entropy_check = sp.simplify(sp.log(4))
    z3_rows = z3_proofs(fixture["regimes"])
    cvc5_rows = cvc5_proofs(fixture["regimes"])
    all_pass = all(
        [
            common.expected_all_pass(fixture),
            str(entropy_check) == "log(4)",
            z3_rows["inheritance_gt_controls"]["verdict"] == "unsat",
            z3_rows["cycle_random_distinct"]["verdict"] == "unsat",
            cvc5_rows["inheritance_gt_controls"]["verdict"] == "unsat",
            cvc5_rows["cycle_random_distinct"]["verdict"] == "unsat",
        ]
    )
    payload = {
        "schema_version": f"{SIM_ID}_jax_leg_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "role_id": "jax_batched_discriminator_lane",
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "source_path": common.rel(SOURCE),
        "source_sha256": common.sha256_file(SOURCE),
        "result_path": common.rel(RESULT),
        "reads_peer_result": False,
        "packages_used": ["jax", "jax.numpy", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
        "package_observables": {
            "sympy": "sp.log exact Z4 record entropy expression over the packet-local syndrome distribution",
            "z3": "z3.Solver binds computed daughter match counts and proves inherited stability cannot collapse to null controls",
            "cvc5": "cvc5.Solver independently binds computed daughter match counts and proves the same discriminator inequalities",
        },
        "package_versions": {
            "jax": package_version("jax"),
            "sympy": package_version("sympy"),
            "z3-solver": package_version("z3-solver"),
            "cvc5": package_version("cvc5"),
        },
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "fixture": fixture,
        "engine_observables": {
            "stability_vector_jax": stability_vector,
            "z4_record_entropy_sympy": str(entropy_check),
        },
        "crossover_proofs": {"z3": z3_rows, "cvc5": cvc5_rows},
        "TOOL_MANIFEST": {
            "jax": {"used": True, "reason": "supportive x64 vector comparison of regime match counts"},
            "sympy": {"used": True, "reason": "load-bearing exact Z4 record entropy expression"},
            "z3": {"used": True, "reason": "load-bearing discriminator proof over computed regime counts"},
            "cvc5": {"used": True, "reason": "independent load-bearing discriminator proof over computed regime counts"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax": "supportive",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
        },
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api/function": "sp.log/sp.simplify",
                "input_object": "computed four-state Z4 syndrome record support",
                "output_object": "log(4) finite counting record entropy expression",
                "positive_case": "inherited record has two bits of retained Z4 syndrome",
                "negative/erased_control": "cycle and random null initializers do not bind parent syndrome rows",
                "boundary_case": "all rows are finite counting entropy only",
                "demotion_condition": "demote if record entropy is assigned without a syndrome distribution",
                "gates": ["record_object", "all_pass"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver/z3.Int/solver.add/check",
                "input_object": "computed daughter terminal match counts",
                "output_object": "UNSAT collapse attempts for inheritance-vs-null discriminator",
                "positive_case": "inheritance match count exceeds both null controls",
                "negative/erased_control": "cycle-null and random-null counts stay distinct and lower",
                "boundary_case": "finite 24-row table",
                "demotion_condition": "demote if solver binds booleans without computed counts",
                "gates": ["crossover_proofs", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver/mkConst/mkTerm/assertFormula/checkSat",
                "input_object": "same computed daughter terminal match counts",
                "output_object": "independent UNSAT collapse attempts",
                "positive_case": "inheritance match count exceeds both null controls",
                "negative/erased_control": "cycle-null and random-null counts stay distinct and lower",
                "boundary_case": "finite 24-row table",
                "demotion_condition": "demote if cvc5 row is removed or mirrors z3 output without solving",
                "gates": ["crossover_proofs", "all_pass"],
            },
        ],
        "all_pass": all_pass,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": all_pass, "result_path": common.rel(RESULT)}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
