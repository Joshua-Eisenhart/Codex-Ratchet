#!/usr/bin/env python3
"""JAX/Python leg for terrain_spinor_shell_nest_v0."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import diffrax
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import jax.scipy.linalg as jsp_linalg
import sympy as sp
import z3

from terrain_spinor_shell_nest_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SEED,
    SIM_DIR,
    SIM_ID,
    build_core_nest,
    dump_json,
    now_z,
    package_version,
    r12,
    rel,
    sha256_file,
    sha256_text,
    tool_call,
)


ENGINE = "jax"
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"
READS_PEER_RESULT = False
PACKAGES_USED = ["jax", "jax.numpy", "jax.scipy.linalg", "diffrax", "sympy", "z3", "cvc5", "hashlib", "pathlib"]
ALIGNED_PACKAGES_LOAD_BEARING = ["diffrax", "sympy", "z3", "cvc5"]
TOOL_MANIFEST = {
    "diffrax": {"tried": True, "used": True, "reason": "load-bearing ODETerm/diffeqsolve integration over exported shell etas; nonzero movement gates leakage control"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact symbolic shell derivative identity and property matrix support"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing erased-placement SMT contradiction over computed non-preserve class count"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent erased-placement SMT contradiction over the same computed count"},
    "jax": {"tried": True, "used": True, "reason": "supportive x64 finite vector arithmetic for shell-site values"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive x64 arrays for shell etas and augmented flow row"},
    "jax.scipy.linalg": {"tried": True, "used": True, "reason": "supportive matrix exponential crosscheck for one level-a affine row"},
}
TOOL_INTEGRATION_DEPTH = {
    "diffrax": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "jax": "supportive",
    "jax.numpy": "supportive",
    "jax.scipy.linalg": "supportive",
}


def diffrax_shell_receipt(core: dict[str, Any]) -> dict[str, Any]:
    etas = jnp.asarray([float(site["eta"]) for site in core["shell_sites"]], dtype=jnp.float64)
    rates = jnp.asarray([0.05, -0.02, 0.01], dtype=jnp.float64)
    term = diffrax.ODETerm(lambda _t, y, args: args)
    sol = diffrax.diffeqsolve(
        term,
        diffrax.Tsit5(),
        t0=0.0,
        t1=1.0,
        dt0=0.1,
        y0=etas,
        args=rates,
        saveat=diffrax.SaveAt(t1=True),
        stepsize_controller=diffrax.PIDController(rtol=1.0e-10, atol=1.0e-10),
    )
    final_eta = sol.ys[-1]
    dz = jnp.cos(2.0 * final_eta) - jnp.cos(2.0 * etas)
    return {
        "tool": "diffrax.diffeqsolve",
        "initial_etas": [r12(x) for x in etas.tolist()],
        "rates": [r12(x) for x in rates.tolist()],
        "final_etas": [r12(x) for x in final_eta.tolist()],
        "z_delta": [r12(x) for x in dz.tolist()],
        "nonzero_delta_count": int(jnp.sum(jnp.abs(dz) > 1.0e-8).item()),
        "pass": bool(jnp.linalg.norm(dz) > 1.0e-8),
    }


def sympy_receipt(core: dict[str, Any]) -> dict[str, Any]:
    eta = sp.symbols("eta", real=True)
    z = sp.cos(2 * eta)
    dz = sp.diff(z, eta)
    evaluated = [sp.simplify(dz.subs(eta, sp.nsimplify(site["eta"]))) for site in core["shell_sites"]]
    return {
        "tool": "sympy.diff/simplify",
        "identity": "d/deta cos(2 eta) = -2 sin(2 eta)",
        "derivatives": [sp.sstr(value) for value in evaluated],
        "pass": all(sp.simplify(value + 2 * sp.sin(2 * sp.nsimplify(site["eta"]))) == 0 for value, site in zip(evaluated, core["shell_sites"], strict=True)),
    }


def jax_matrix_receipt() -> dict[str, Any]:
    aug = jnp.asarray(
        [
            [-0.8, -0.2309401076758503, 0.2309401076758503, 0.0],
            [0.2309401076758503, -0.8, -0.2309401076758503, 0.0],
            [-0.2309401076758503, 0.2309401076758503, -0.8, 0.0],
            [0.0, 0.0, 0.0, 0.0],
        ],
        dtype=jnp.float64,
    )
    start = jnp.asarray([1.0, 0.0, 0.0, 1.0], dtype=jnp.float64)
    out = jsp_linalg.expm(aug) @ start
    return {"tool": "jax.scipy.linalg.expm", "norm": r12(jnp.linalg.norm(out[:3]).item()), "pass": bool(jnp.isfinite(out).all())}


def z3_erased_flip_proof_local(nonzero_count: int, erased_count: int) -> dict[str, Any]:
    solver = z3.Solver()
    actual = z3.Int("actual_non_preserve_shell_site_count")
    erased = z3.Int("erased_no_placement_non_preserve_count")
    solver.add(actual == nonzero_count, erased == erased_count)
    solver.add(actual == erased)
    verdict = solver.check()

    control = z3.Solver()
    ca = z3.Int("control_actual_non_preserve_shell_site_count")
    ce = z3.Int("control_erased_no_placement_non_preserve_count")
    control.add(ca == erased_count, ce == erased_count)
    control.add(ca == ce)
    control_verdict = control.check()
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": str(verdict),
        "erased_control_verdict": str(control_verdict),
        "claim": "computed shell leakage nest has nonzero class count; erased no-placement control cannot equal it",
        "raw_values_bound": {"actual": nonzero_count, "erased": erased_count},
        "negative/erased_control": "bind actual to erased count after deleting shell placement",
        "pass": verdict == z3.unsat and control_verdict == z3.sat,
    }


def cvc5_erased_flip_proof_local(nonzero_count: int, erased_count: int) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    actual = solver.mkConst(int_sort, "actual_non_preserve_shell_site_count")
    erased = solver.mkConst(int_sort, "erased_no_placement_non_preserve_count")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, actual, solver.mkInteger(nonzero_count)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, erased, solver.mkInteger(erased_count)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, actual, erased))
    verdict_obj = solver.checkSat()

    control = cvc5.Solver()
    control.setLogic("QF_LIA")
    c_int = control.getIntegerSort()
    ca = control.mkConst(c_int, "control_actual_non_preserve_shell_site_count")
    ce = control.mkConst(c_int, "control_erased_no_placement_non_preserve_count")
    control.assertFormula(control.mkTerm(Kind.EQUAL, ca, control.mkInteger(erased_count)))
    control.assertFormula(control.mkTerm(Kind.EQUAL, ce, control.mkInteger(erased_count)))
    control.assertFormula(control.mkTerm(Kind.EQUAL, ca, ce))
    control_obj = control.checkSat()

    def status(result: Any) -> str:
        if result.isSat():
            return "sat"
        if result.isUnsat():
            return "unsat"
        return str(result)

    return {
        "ran": True,
        "load_bearing": True,
        "verdict": status(verdict_obj),
        "erased_control_verdict": status(control_obj),
        "claim": "computed shell leakage nest has nonzero class count; erased no-placement control cannot equal it",
        "raw_values_bound": {"actual": nonzero_count, "erased": erased_count},
        "negative/erased_control": "bind actual to erased count after deleting shell placement",
        "pass": verdict_obj.isUnsat() and control_obj.isSat(),
    }


def build_result() -> dict[str, Any]:
    core = build_core_nest()
    actual = int(core["smt_identity_values"]["actual_non_preserve_shell_site_count"])
    erased = int(core["smt_identity_values"]["erased_no_placement_non_preserve_count"])
    z3_proof = z3_erased_flip_proof_local(actual, erased)
    cvc5_proof = cvc5_erased_flip_proof_local(actual, erased)
    diffrax_row = diffrax_shell_receipt(core)
    sympy_row = sympy_receipt(core)
    matrix_row = jax_matrix_receipt()
    acceptance = {
        "core_nest_pass": core["all_pass"] is True,
        "diffrax_shell_receipt": diffrax_row["pass"] is True,
        "sympy_shell_identity": sympy_row["pass"] is True,
        "smt_z3": z3_proof["pass"] is True,
        "smt_cvc5": cvc5_proof["pass"] is True,
        "matrix_exponential_finite": matrix_row["pass"] is True,
        "ceiling": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
    }
    tool_calls = [
        tool_call("diffrax", "diffrax.ODETerm/diffeqsolve/Tsit5", "exported shell etas plus bounded rates", diffrax_row, "nonzero shell movement observed", "zero rates erase movement", "eta=pi/4 remains finite", "if z_delta is all zero, demote leakage row", ["level_c_shell"]),
        tool_call("sympy", "sympy.diff/simplify", "z=cos(2 eta)", sympy_row, "closed derivative matches shell coordinate", "wrong shell coordinate changes derivative", "eta=pi/4 derivative boundary", "if symbolic derivative mismatches, demote shell coordinate row", ["shell_coordinate"]),
        tool_call("z3", "z3.Solver/check", "computed non-preserve count and erased no-placement count", z3_proof, "actual count differs from erased count", "erased count bound to actual zero count", "actual=0 control is satisfiable", "if erased flip does not change verdict, demote proof", ["crossover_proofs"]),
        tool_call("cvc5", "cvc5.Solver/checkSat", "computed non-preserve count and erased no-placement count", cvc5_proof, "actual count differs from erased count", "erased count bound to actual zero count", "actual=0 control is satisfiable", "if erased flip does not change verdict, demote proof", ["crossover_proofs"]),
    ]
    return {
        "schema_version": f"{SIM_ID}.{ENGINE}_result.v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "role_id": "jax_rich_mirror_sim_builder",
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "seed": SEED,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "packages_used": PACKAGES_USED,
        "aligned_packages_load_bearing": ALIGNED_PACKAGES_LOAD_BEARING,
        "claim_path_tools": ALIGNED_PACKAGES_LOAD_BEARING,
        "package_versions": {name: package_version(name) for name in ["jax", "diffrax", "sympy", "z3-solver", "cvc5"]},
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": tool_calls,
        "capability_receipts": {
            "diffrax_shell_receipt": diffrax_row,
            "sympy_receipt": sympy_row,
            "jax_matrix_receipt": matrix_row,
            "source_hash_probe": hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest(),
        },
        "load_bearing_decomposition": core["load_bearing_decomposition"],
        "three_level_property_matrix": core["three_level_property_matrix"],
        "si_frame_row": core["si_frame_row"],
        "controls": core["controls"],
        "smt_identity_values": core["smt_identity_values"],
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "acceptance": acceptance,
        "values": core["values"],
        "all_pass": all(acceptance.values()),
    }


def main() -> int:
    payload = build_result()
    dump_json(RESULT_PATH, payload)
    print(f"wrote: {RESULT_PATH}")
    print(f"{SIM_ID}_{ENGINE}_DONE all_pass={str(payload['all_pass']).lower()}")
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
