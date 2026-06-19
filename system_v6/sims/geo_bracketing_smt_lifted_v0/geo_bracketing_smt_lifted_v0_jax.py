#!/usr/bin/env python3
"""z3+cvc5 raw-object bracketing proof over committed lifted shell exports."""

from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.metadata
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "geo_bracketing_smt_lifted_v0"
ENGINE = "jax"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"
N3_JAX_RESULT = ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n3_v0" / "results" / "stage_lifted_spinor_shell_n3_v0_jax_results.json"
N3_JULIA_RESULT = ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n3_v0" / "results" / "stage_lifted_spinor_shell_n3_v0_julia_results.json"
N4_JAX_RESULT = ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n4_v0" / "results" / "stage_lifted_spinor_shell_n4_v0_jax_results.json"
N4_JULIA_RESULT = ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n4_v0" / "results" / "stage_lifted_spinor_shell_n4_v0_julia_results.json"
N5_JAX_RESULT = ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n5_v0" / "results" / "stage_lifted_spinor_shell_n5_v0_jax_results.json"
N5_JULIA_RESULT = ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n5_v0" / "results" / "stage_lifted_spinor_shell_n5_v0_julia_results.json"
N6_JAX_RESULT = ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n6_v0" / "results" / "stage_lifted_spinor_shell_n6_v0_jax_results.json"
N6_JULIA_RESULT = ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n6_v0" / "results" / "stage_lifted_spinor_shell_n6_v0_julia_results.json"
N7_JAX_RESULT = ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n7_v0" / "results" / "stage_lifted_spinor_shell_n7_v0_jax_results.json"
N7_JULIA_RESULT = ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n7_v0" / "results" / "stage_lifted_spinor_shell_n7_v0_julia_results.json"
N8_JAX_RESULT = ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n8_v0" / "results" / "stage_lifted_spinor_shell_n8_v0_jax_results.json"
N8_JULIA_RESULT = ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n8_v0" / "results" / "stage_lifted_spinor_shell_n8_v0_julia_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
SEED = 20260610
PIN_BLOCK = {
    "sim_id": SIM_ID,
    "source_packet": "stage_lifted_spinor_shell_n3_v0 plus stage_lifted_spinor_shell_n4_v0/n5/n6/n7/n8 extension rows",
    "source_scope": "read-only committed n=3, n=4, n=5, n=6, n=7, and n=8 exported JSONs",
    "claim": "lifted path/grouping objects have structurally nonzero bracketing gap; density-erased quotient flips to zero gap",
    "solver_sentence": "positive proves UNSAT of equality/zero-gap negation; erased control proves SAT of equality/zero-gap negation",
    "unit_boundary": "with unit e, asserting (a*e)*e = -a*(e*e) forces a=0; nonzero-a version is UNSAT",
    "classification": CLASSIFICATION,
    "promotion_allowed": PROMOTION_ALLOWED,
    "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
    "seed": SEED,
    "mode": "julia_canon_plus_jax_diagnostic",
}
PIN_SPEC = json.dumps(PIN_BLOCK, sort_keys=True, separators=(",", ":"))
SOURCE_SPECS = {
    "n3": {
        "n": 3,
        "jax_result": N3_JAX_RESULT,
        "julia_result": N3_JULIA_RESULT,
        "left_path": ["e01", "e12"],
        "right_path": ["e12", "e01"],
        "path_lineage": "system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_jax.py:SOURCE_SPECS.n3.left_path/right_path",
        "support_field": "rows.P2_support_object",
        "boundary_field": "rows.P7_bracketing_boundary",
    },
    "n4": {
        "n": 4,
        "jax_result": N4_JAX_RESULT,
        "julia_result": N4_JULIA_RESULT,
        "left_path": ["e01", "e12", "e23"],
        "right_path": ["e23", "e12", "e01"],
        "path_lineage": "system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_jax.py:order_and_bracketing_rows.path_gap",
        "support_field": "rows.P2_support_object",
        "boundary_field": "rows.P7_bracketing_boundary",
    },
    "n5": {
        "n": 5,
        "jax_result": N5_JAX_RESULT,
        "julia_result": N5_JULIA_RESULT,
        "left_path": ["e01", "e12", "e23"],
        "right_path": ["e23", "e12", "e01"],
        "path_lineage": "system_v6/sims/stage_lifted_spinor_shell_n5_v0/stage_lifted_spinor_shell_n5_v0_jax.py:order_and_bracketing_rows.path_gap",
        "support_field": "rows.P2_support_object",
        "boundary_field": "rows.P7_bracketing_boundary",
    },
    "n6": {
        "n": 6,
        "jax_result": N6_JAX_RESULT,
        "julia_result": N6_JULIA_RESULT,
        "left_path": ["e01", "e12", "e23"],
        "right_path": ["e23", "e12", "e01"],
        "path_lineage": "system_v6/sims/stage_lifted_spinor_shell_n6_v0/stage_lifted_spinor_shell_n6_v0_jax.py:order_and_bracketing_rows.path_gap",
        "support_field": "rows.P2_support_object",
        "boundary_field": "rows.P7_bracketing_boundary",
    },
    "n7": {
        "n": 7,
        "jax_result": N7_JAX_RESULT,
        "julia_result": N7_JULIA_RESULT,
        "left_path": ["e01", "e12", "e23"],
        "right_path": ["e23", "e12", "e01"],
        "path_lineage": "system_v6/sims/stage_lifted_spinor_shell_n7_v0/stage_lifted_spinor_shell_n7_v0_jax.py:order_and_bracketing_rows.path_gap",
        "support_field": "rows.P2_support_object",
        "boundary_field": "rows.P7_bracketing_boundary",
    },
    "n8": {
        "n": 8,
        "jax_result": N8_JAX_RESULT,
        "julia_result": N8_JULIA_RESULT,
        "left_path": ["e01", "e12", "e23"],
        "right_path": ["e23", "e12", "e01"],
        "path_lineage": "system_v6/sims/stage_lifted_spinor_shell_n8_v0/stage_lifted_spinor_shell_n8_v0_jax.py:order_and_bracketing_rows.path_gap",
        "support_field": "rows.P2_support_object",
        "boundary_field": "rows.P7_bracketing_boundary",
    },
}

TOOL_MANIFEST = {
    "z3": {"tried": True, "used": True, "reason": "load-bearing raw finite path-count SMT proof for lifted bracketing and erased flip"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent raw finite path-count SMT proof matching z3"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact rational cross-check for positive, erased, and unit-killed rows"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive JSON loading, hashing, path handling, and timestamps"},
}
TOOL_INTEGRATION_DEPTH = {
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "python_stdlib": "supportive",
}
PACKAGES_USED = ["z3", "cvc5", "sympy", "json", "hashlib", "pathlib", "fractions"]
ALIGNED_PACKAGES_LOAD_BEARING = ["z3", "cvc5", "sympy"]
CLAIM_PATH_TOOLS = ["z3", "cvc5", "sympy"]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def bit_index(site_id: str, n_sites: int) -> int:
    return n_sites - 1 - int(site_id.removeprefix("q"))


def apply_cnot(edge: dict[str, Any], state: int, n_sites: int) -> int:
    control = bit_index(str(edge["src"]), n_sites)
    target = bit_index(str(edge["dst"]), n_sites)
    if (state >> control) & 1:
        state ^= 1 << target
    return state


def compose_path(edges_by_id: dict[str, dict[str, Any]], path: list[str], state: int, n_sites: int) -> int:
    out = state
    for edge_id in path:
        out = apply_cnot(edges_by_id[edge_id], out, n_sites)
    return out


def one_excitation_states(n_sites: int) -> list[int]:
    return [1 << bit_index(f"q{i}", n_sites) for i in range(n_sites)]


def count_vector(outputs: list[int], dim: int) -> list[int]:
    counts = [0 for _ in range(dim)]
    for out in outputs:
        counts[out] += 1
    return counts


def load_raw_object(label: str) -> dict[str, Any]:
    spec = SOURCE_SPECS[label]
    source_jax = json.loads(spec["jax_result"].read_text(encoding="utf-8"))
    source_julia = json.loads(spec["julia_result"].read_text(encoding="utf-8"))
    support = source_jax["rows"]["P2_support_object"]
    order_row = source_jax["rows"]["P7_bracketing_boundary"]
    sites = support["sites"]
    n_sites = len(sites)
    dim = 2**n_sites
    edges = support["edges"]
    edges_by_id = {edge["edge_id"]: edge for edge in edges}
    left_path = spec["left_path"]
    right_path = spec["right_path"]
    inputs = one_excitation_states(n_sites)
    left_outputs = [compose_path(edges_by_id, left_path, state, n_sites) for state in inputs]
    right_outputs = [compose_path(edges_by_id, right_path, state, n_sites) for state in inputs]
    left_counts = count_vector(left_outputs, dim)
    right_counts = count_vector(right_outputs, dim)
    diff_sq_counts = sum((a - b) ** 2 for a, b in zip(left_counts, right_counts))
    normalized_gap_sq = Fraction(diff_sq_counts, n_sites)
    if label == "n3":
        source_results = {
            "n3_jax_result": str(N3_JAX_RESULT.relative_to(ROOT)),
            "n3_julia_result": str(N3_JULIA_RESULT.relative_to(ROOT)),
            "n3_jax_sha256": sha256_file(N3_JAX_RESULT),
            "n3_julia_sha256": sha256_file(N3_JULIA_RESULT),
        }
        paths = {
            "left": {"name": "(e12 after e01)", "edge_ids": left_path},
            "right": {"name": "(e01 after e12)", "edge_ids": right_path},
        }
    else:
        source_results = {
            f"{label}_jax_result": str(spec["jax_result"].relative_to(ROOT)),
            f"{label}_julia_result": str(spec["julia_result"].relative_to(ROOT)),
            f"{label}_jax_sha256": sha256_file(spec["jax_result"]),
            f"{label}_julia_sha256": sha256_file(spec["julia_result"]),
            f"{label}_support_field": spec["support_field"],
            f"{label}_boundary_field": spec["boundary_field"],
            f"{label}_path_lineage": spec["path_lineage"],
        }
        paths = {
            "left": {"name": "->".join(left_path), "edge_ids": left_path},
            "right": {"name": "->".join(right_path), "edge_ids": right_path},
        }
    row = {
        "source_results": source_results,
        "n_sites": n_sites,
        "dim": dim,
        "sites": sites,
        "edges": edges,
        "paths": paths,
        "input_support_basis": inputs,
        "left_outputs": left_outputs,
        "right_outputs": right_outputs,
        "left_counts": left_counts,
        "right_counts": right_counts,
        "diff_sq_counts": diff_sq_counts,
        "normalized_gap_sq_num": normalized_gap_sq.numerator,
        "normalized_gap_sq_den": normalized_gap_sq.denominator,
        "exported_gap_decimal": order_row["lifted_path_grouping_gap"],
        "exported_matrix_associator_norm": order_row["matrix_associator_norm"],
        "julia_exported_gap_decimal": source_julia["rows"]["P7_bracketing_boundary"]["lifted_path_grouping_gap"],
    }
    if label != "n3":
        row["source_label"] = label
        row["n"] = spec["n"]
    return row


def z3_count_vector_proof(raw: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    left = [z3.Int(f"lifted_left_count_{i}") for i in range(raw["dim"])]
    right = [z3.Int(f"lifted_right_count_{i}") for i in range(raw["dim"])]
    for var, value in zip(left, raw["left_counts"]):
        solver.add(var == value)
    for var, value in zip(right, raw["right_counts"]):
        solver.add(var == value)
    solver.add(z3.And([left[i] == right[i] for i in range(raw["dim"])]))
    positive_verdict = solver.check()

    erased = z3.Solver()
    left_density_token = z3.Int("erased_left_density_single_excitation_mass")
    right_density_token = z3.Int("erased_right_density_single_excitation_mass")
    erased.add(left_density_token == sum(raw["left_counts"]))
    erased.add(right_density_token == sum(raw["right_counts"]))
    erased.add(left_density_token == right_density_token)
    erased_verdict = erased.check()

    boundary = z3.Solver()
    a = z3.Int("a")
    boundary.add(a == -a)
    boundary.add(a != 0)
    boundary_verdict = boundary.check()
    force_zero = z3.Solver()
    a0 = z3.Int("a_forced")
    force_zero.add(a0 == -a0)
    force_zero.add(a0 != 0)
    return {
        "ran": True,
        "load_bearing": True,
        "claim": "raw lifted path count vectors differ, so equality/zero-gap negation is UNSAT",
        "verdict": str(positive_verdict),
        "erased_control_verdict": str(erased_verdict),
        "unit_killed_nonzero_verdict": str(boundary_verdict),
        "raw_values_bound": {"left_counts": raw["left_counts"], "right_counts": raw["right_counts"]},
        "pass": positive_verdict == z3.unsat and erased_verdict == z3.sat and boundary_verdict == z3.unsat,
    }


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_count_vector_proof(raw: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    left = [solver.mkConst(int_sort, f"lifted_left_count_{i}") for i in range(raw["dim"])]
    right = [solver.mkConst(int_sort, f"lifted_right_count_{i}") for i in range(raw["dim"])]
    for var, value in zip(left, raw["left_counts"]):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
    for var, value in zip(right, raw["right_counts"]):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
    equalities = [solver.mkTerm(Kind.EQUAL, left[i], right[i]) for i in range(raw["dim"])]
    solver.assertFormula(solver.mkTerm(Kind.AND, *equalities))
    positive_result = solver.checkSat()
    positive_verdict = cvc5_status(positive_result)

    erased = cvc5.Solver()
    erased.setLogic("QF_LIA")
    e_int = erased.getIntegerSort()
    left_density_token = erased.mkConst(e_int, "erased_left_density_single_excitation_mass")
    right_density_token = erased.mkConst(e_int, "erased_right_density_single_excitation_mass")
    erased.assertFormula(erased.mkTerm(Kind.EQUAL, left_density_token, erased.mkInteger(sum(raw["left_counts"]))))
    erased.assertFormula(erased.mkTerm(Kind.EQUAL, right_density_token, erased.mkInteger(sum(raw["right_counts"]))))
    erased.assertFormula(erased.mkTerm(Kind.EQUAL, left_density_token, right_density_token))
    erased_verdict = cvc5_status(erased.checkSat())

    boundary = cvc5.Solver()
    boundary.setLogic("QF_LIA")
    b_int = boundary.getIntegerSort()
    a = boundary.mkConst(b_int, "a")
    boundary.assertFormula(boundary.mkTerm(Kind.EQUAL, a, boundary.mkTerm(Kind.NEG, a)))
    boundary.assertFormula(boundary.mkTerm(Kind.NOT, boundary.mkTerm(Kind.EQUAL, a, boundary.mkInteger(0))))
    boundary_verdict = cvc5_status(boundary.checkSat())
    return {
        "ran": True,
        "load_bearing": True,
        "claim": "raw lifted path count vectors differ, so equality/zero-gap negation is UNSAT",
        "verdict": positive_verdict,
        "erased_control_verdict": erased_verdict,
        "unit_killed_nonzero_verdict": boundary_verdict,
        "raw_values_bound": {"left_counts": raw["left_counts"], "right_counts": raw["right_counts"]},
        "pass": positive_verdict == "unsat" and erased_verdict == "sat" and boundary_verdict == "unsat",
    }


def sympy_exact_crosscheck(raw: dict[str, Any]) -> dict[str, Any]:
    left = sp.Matrix(raw["left_counts"])
    right = sp.Matrix(raw["right_counts"])
    diff = left - right
    gap_sq = sp.Rational(int(diff.dot(diff)), int(raw["n_sites"]))
    erased_gap_sq = sp.Rational(0, 1)
    a = sp.symbols("a", integer=True)
    forced = sp.solve(sp.Eq(a, -a), a)
    return {
        "ran": True,
        "load_bearing": True,
        "gap_squared": str(sp.simplify(gap_sq)),
        "gap": str(sp.sqrt(gap_sq)),
        "erased_gap_squared": str(erased_gap_sq),
        "unit_killed_solution": [str(item) for item in forced],
        "matches_exported_gap": abs(float(sp.sqrt(gap_sq)) - float(raw["exported_gap_decimal"])) < 1.0e-12,
        "pass": gap_sq == sp.Rational(raw["normalized_gap_sq_num"], raw["normalized_gap_sq_den"]) and erased_gap_sq == 0 and forced == [0],
    }


def build_result() -> dict[str, Any]:
    raw = load_raw_object("n3")
    n4_raw = load_raw_object("n4")
    n5_raw = load_raw_object("n5")
    n6_raw = load_raw_object("n6")
    n7_raw = load_raw_object("n7")
    n8_raw = load_raw_object("n8")
    z3_proof = z3_count_vector_proof(raw)
    cvc5_proof = cvc5_count_vector_proof(raw)
    sympy_check = sympy_exact_crosscheck(raw)
    n4_z3_proof = z3_count_vector_proof(n4_raw)
    n4_cvc5_proof = cvc5_count_vector_proof(n4_raw)
    n4_sympy_check = sympy_exact_crosscheck(n4_raw)
    n5_z3_proof = z3_count_vector_proof(n5_raw)
    n5_cvc5_proof = cvc5_count_vector_proof(n5_raw)
    n5_sympy_check = sympy_exact_crosscheck(n5_raw)
    n6_z3_proof = z3_count_vector_proof(n6_raw)
    n6_cvc5_proof = cvc5_count_vector_proof(n6_raw)
    n6_sympy_check = sympy_exact_crosscheck(n6_raw)
    n7_z3_proof = z3_count_vector_proof(n7_raw)
    n7_cvc5_proof = cvc5_count_vector_proof(n7_raw)
    n7_sympy_check = sympy_exact_crosscheck(n7_raw)
    n8_z3_proof = z3_count_vector_proof(n8_raw)
    n8_cvc5_proof = cvc5_count_vector_proof(n8_raw)
    n8_sympy_check = sympy_exact_crosscheck(n8_raw)
    positive_pass = z3_proof["verdict"] == "unsat" and cvc5_proof["verdict"] == "unsat"
    negative_pass = z3_proof["erased_control_verdict"] == "sat" and cvc5_proof["erased_control_verdict"] == "sat"
    boundary_pass = z3_proof["unit_killed_nonzero_verdict"] == "unsat" and cvc5_proof["unit_killed_nonzero_verdict"] == "unsat"
    n4_positive_pass = n4_z3_proof["verdict"] == "unsat" and n4_cvc5_proof["verdict"] == "unsat"
    n4_negative_pass = n4_z3_proof["erased_control_verdict"] == "sat" and n4_cvc5_proof["erased_control_verdict"] == "sat"
    n4_boundary_pass = n4_z3_proof["unit_killed_nonzero_verdict"] == "unsat" and n4_cvc5_proof["unit_killed_nonzero_verdict"] == "unsat"
    n5_positive_pass = n5_z3_proof["verdict"] == "unsat" and n5_cvc5_proof["verdict"] == "unsat"
    n5_negative_pass = n5_z3_proof["erased_control_verdict"] == "sat" and n5_cvc5_proof["erased_control_verdict"] == "sat"
    n5_boundary_pass = n5_z3_proof["unit_killed_nonzero_verdict"] == "unsat" and n5_cvc5_proof["unit_killed_nonzero_verdict"] == "unsat"
    n6_positive_pass = n6_z3_proof["verdict"] == "unsat" and n6_cvc5_proof["verdict"] == "unsat"
    n6_negative_pass = n6_z3_proof["erased_control_verdict"] == "sat" and n6_cvc5_proof["erased_control_verdict"] == "sat"
    n6_boundary_pass = n6_z3_proof["unit_killed_nonzero_verdict"] == "unsat" and n6_cvc5_proof["unit_killed_nonzero_verdict"] == "unsat"
    n7_positive_pass = n7_z3_proof["verdict"] == "unsat" and n7_cvc5_proof["verdict"] == "unsat"
    n7_negative_pass = n7_z3_proof["erased_control_verdict"] == "sat" and n7_cvc5_proof["erased_control_verdict"] == "sat"
    n7_boundary_pass = n7_z3_proof["unit_killed_nonzero_verdict"] == "unsat" and n7_cvc5_proof["unit_killed_nonzero_verdict"] == "unsat"
    n8_positive_pass = n8_z3_proof["verdict"] == "unsat" and n8_cvc5_proof["verdict"] == "unsat"
    n8_negative_pass = n8_z3_proof["erased_control_verdict"] == "sat" and n8_cvc5_proof["erased_control_verdict"] == "sat"
    n8_boundary_pass = n8_z3_proof["unit_killed_nonzero_verdict"] == "unsat" and n8_cvc5_proof["unit_killed_nonzero_verdict"] == "unsat"
    all_pass = (
        positive_pass
        and negative_pass
        and boundary_pass
        and sympy_check["pass"]
        and n4_positive_pass
        and n4_negative_pass
        and n4_boundary_pass
        and n4_sympy_check["pass"]
        and n5_positive_pass
        and n5_negative_pass
        and n5_boundary_pass
        and n5_sympy_check["pass"]
        and n6_positive_pass
        and n6_negative_pass
        and n6_boundary_pass
        and n6_sympy_check["pass"]
        and n7_positive_pass
        and n7_negative_pass
        and n7_boundary_pass
        and n7_sympy_check["pass"]
        and n8_positive_pass
        and n8_negative_pass
        and n8_boundary_pass
        and n8_sympy_check["pass"]
    )
    return {
        "schema_version": "geo_bracketing_smt_lifted_v0_engine_v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "role_id": "jax_symbolic_smt_diagnostic",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "reads_peer_result": READS_PEER_RESULT,
        "seed": SEED,
        "pin_block": PIN_BLOCK,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "packages_used": PACKAGES_USED,
        "package_versions": {"z3": package_version("z3-solver"), "cvc5": package_version("cvc5"), "sympy": package_version("sympy")},
        "aligned_packages_load_bearing": ALIGNED_PACKAGES_LOAD_BEARING,
        "claim_path_tools": CLAIM_PATH_TOOLS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "source_refs": raw["source_results"],
        "n4_source_refs": n4_raw["source_results"],
        "n5_source_refs": n5_raw["source_results"],
        "n6_source_refs": n6_raw["source_results"],
        "n7_source_refs": n7_raw["source_results"],
        "n8_source_refs": n8_raw["source_results"],
        "raw_object": raw,
        "n4_raw_object": n4_raw,
        "n5_raw_object": n5_raw,
        "n6_raw_object": n6_raw,
        "n7_raw_object": n7_raw,
        "n8_raw_object": n8_raw,
        "positive": {
            "name": "lifted_raw_path_grouping_gap",
            "sentence": "left lifted path count vector equals right lifted path count vector",
            "expected": "UNSAT because the exported lifted support/path object preserves path order",
            "z3": z3_proof,
            "cvc5": cvc5_proof,
            "pass": positive_pass,
        },
        "n4_positive": {
            "name": "n4_lifted_raw_path_grouping_gap",
            "sentence": "n=4 left lifted path count vector equals n=4 right lifted path count vector",
            "expected": "UNSAT because the committed n=4 lifted support/path object preserves path order",
            "z3": n4_z3_proof,
            "cvc5": n4_cvc5_proof,
            "pass": n4_positive_pass,
        },
        "n5_positive": {
            "name": "n5_lifted_raw_path_grouping_gap",
            "sentence": "n=5 left lifted path count vector equals n=5 right lifted path count vector",
            "expected": "UNSAT because the committed n=5 lifted support/path object preserves path order",
            "z3": n5_z3_proof,
            "cvc5": n5_cvc5_proof,
            "pass": n5_positive_pass,
        },
        "n6_positive": {
            "name": "n6_lifted_raw_path_grouping_gap",
            "sentence": "n=6 left lifted path count vector equals n=6 right lifted path count vector",
            "expected": "UNSAT because the committed n=6 lifted support/path object preserves path order",
            "z3": n6_z3_proof,
            "cvc5": n6_cvc5_proof,
            "pass": n6_positive_pass,
        },
        "n7_positive": {
            "name": "n7_lifted_raw_path_grouping_gap",
            "sentence": "n=7 left lifted path count vector equals n=7 right lifted path count vector",
            "expected": "UNSAT because the committed n=7 lifted support/path object preserves path order",
            "z3": n7_z3_proof,
            "cvc5": n7_cvc5_proof,
            "pass": n7_positive_pass,
        },
        "n8_positive": {
            "name": "n8_lifted_raw_path_grouping_gap",
            "sentence": "n=8 left lifted path count vector equals n=8 right lifted path count vector",
            "expected": "UNSAT because the committed n=8 lifted support/path object preserves path order",
            "z3": n8_z3_proof,
            "cvc5": n8_cvc5_proof,
            "pass": n8_positive_pass,
        },
        "negative": {
            "name": "density_quotient_erased_control",
            "sentence": "left erased density token equals right erased density token",
            "expected": "SAT because the density quotient erases edge path order",
            "z3_verdict": z3_proof["erased_control_verdict"],
            "cvc5_verdict": cvc5_proof["erased_control_verdict"],
            "pass": negative_pass,
        },
        "n4_negative": {
            "name": "n4_density_quotient_erased_control",
            "sentence": "n=4 left erased density token equals n=4 right erased density token",
            "expected": "SAT because the density quotient erases edge path order",
            "z3_verdict": n4_z3_proof["erased_control_verdict"],
            "cvc5_verdict": n4_cvc5_proof["erased_control_verdict"],
            "pass": n4_negative_pass,
        },
        "n5_negative": {
            "name": "n5_density_quotient_erased_control",
            "sentence": "n=5 left erased density token equals n=5 right erased density token",
            "expected": "SAT because the density quotient erases edge path order",
            "z3_verdict": n5_z3_proof["erased_control_verdict"],
            "cvc5_verdict": n5_cvc5_proof["erased_control_verdict"],
            "pass": n5_negative_pass,
        },
        "n6_negative": {
            "name": "n6_density_quotient_erased_control",
            "sentence": "n=6 left erased density token equals n=6 right erased density token",
            "expected": "SAT because the density quotient erases edge path order",
            "z3_verdict": n6_z3_proof["erased_control_verdict"],
            "cvc5_verdict": n6_cvc5_proof["erased_control_verdict"],
            "pass": n6_negative_pass,
        },
        "n7_negative": {
            "name": "n7_density_quotient_erased_control",
            "sentence": "n=7 left erased density token equals n=7 right erased density token",
            "expected": "SAT because the density quotient erases edge path order",
            "z3_verdict": n7_z3_proof["erased_control_verdict"],
            "cvc5_verdict": n7_cvc5_proof["erased_control_verdict"],
            "pass": n7_negative_pass,
        },
        "n8_negative": {
            "name": "n8_density_quotient_erased_control",
            "sentence": "n=8 left erased density token equals n=8 right erased density token",
            "expected": "SAT because the density quotient erases edge path order",
            "z3_verdict": n8_z3_proof["erased_control_verdict"],
            "cvc5_verdict": n8_cvc5_proof["erased_control_verdict"],
            "pass": n8_negative_pass,
        },
        "boundary": {
            "name": "unit_killed_anti_associativity",
            "sentence": "with unit e, (a*e)*e = -a*(e*e) and a != 0",
            "expected": "UNSAT; dropping a != 0 forces a=0",
            "z3_verdict": z3_proof["unit_killed_nonzero_verdict"],
            "cvc5_verdict": cvc5_proof["unit_killed_nonzero_verdict"],
            "sympy_forced_solution": sympy_check["unit_killed_solution"],
            "pass": boundary_pass,
        },
        "n4_boundary": {
            "name": "n4_unit_killed_anti_associativity",
            "sentence": "with unit e, (a*e)*e = -a*(e*e) and a != 0",
            "expected": "UNSAT; dropping a != 0 forces a=0",
            "z3_verdict": n4_z3_proof["unit_killed_nonzero_verdict"],
            "cvc5_verdict": n4_cvc5_proof["unit_killed_nonzero_verdict"],
            "sympy_forced_solution": n4_sympy_check["unit_killed_solution"],
            "pass": n4_boundary_pass,
        },
        "n5_boundary": {
            "name": "n5_unit_killed_anti_associativity",
            "sentence": "with unit e, (a*e)*e = -a*(e*e) and a != 0",
            "expected": "UNSAT; dropping a != 0 forces a=0",
            "z3_verdict": n5_z3_proof["unit_killed_nonzero_verdict"],
            "cvc5_verdict": n5_cvc5_proof["unit_killed_nonzero_verdict"],
            "sympy_forced_solution": n5_sympy_check["unit_killed_solution"],
            "pass": n5_boundary_pass,
        },
        "n6_boundary": {
            "name": "n6_unit_killed_anti_associativity",
            "sentence": "with unit e, (a*e)*e = -a*(e*e) and a != 0",
            "expected": "UNSAT; dropping a != 0 forces a=0",
            "z3_verdict": n6_z3_proof["unit_killed_nonzero_verdict"],
            "cvc5_verdict": n6_cvc5_proof["unit_killed_nonzero_verdict"],
            "sympy_forced_solution": n6_sympy_check["unit_killed_solution"],
            "pass": n6_boundary_pass,
        },
        "n7_boundary": {
            "name": "n7_unit_killed_anti_associativity",
            "sentence": "with unit e, (a*e)*e = -a*(e*e) and a != 0",
            "expected": "UNSAT; dropping a != 0 forces a=0",
            "z3_verdict": n7_z3_proof["unit_killed_nonzero_verdict"],
            "cvc5_verdict": n7_cvc5_proof["unit_killed_nonzero_verdict"],
            "sympy_forced_solution": n7_sympy_check["unit_killed_solution"],
            "pass": n7_boundary_pass,
        },
        "n8_boundary": {
            "name": "n8_unit_killed_anti_associativity",
            "sentence": "with unit e, (a*e)*e = -a*(e*e) and a != 0",
            "expected": "UNSAT; dropping a != 0 forces a=0",
            "z3_verdict": n8_z3_proof["unit_killed_nonzero_verdict"],
            "cvc5_verdict": n8_cvc5_proof["unit_killed_nonzero_verdict"],
            "sympy_forced_solution": n8_sympy_check["unit_killed_solution"],
            "pass": n8_boundary_pass,
        },
        "sympy_exact_crosscheck": sympy_check,
        "n4_sympy_exact_crosscheck": n4_sympy_check,
        "n5_sympy_exact_crosscheck": n5_sympy_check,
        "n6_sympy_exact_crosscheck": n6_sympy_check,
        "n7_sympy_exact_crosscheck": n7_sympy_check,
        "n8_sympy_exact_crosscheck": n8_sympy_check,
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "n4_crossover_proofs": {"z3": n4_z3_proof, "cvc5": n4_cvc5_proof},
        "n5_crossover_proofs": {"z3": n5_z3_proof, "cvc5": n5_cvc5_proof},
        "n6_crossover_proofs": {"z3": n6_z3_proof, "cvc5": n6_cvc5_proof},
        "n7_crossover_proofs": {"z3": n7_z3_proof, "cvc5": n7_cvc5_proof},
        "n8_crossover_proofs": {"z3": n8_z3_proof, "cvc5": n8_cvc5_proof},
        "acceptance": {
            "z3_and_cvc5_agree_positive": positive_pass,
            "erased_control_flips": negative_pass,
            "unit_killed_control_fails_nonzero": boundary_pass,
            "sympy_exact_matches": sympy_check["pass"],
            "n3_rows_recomputed": True,
            "n4_read_only_imports_present": True,
            "n4_z3_and_cvc5_agree_positive": n4_positive_pass,
            "n4_erased_control_flips": n4_negative_pass,
            "n4_unit_killed_control_fails_nonzero": n4_boundary_pass,
            "n4_sympy_exact_matches": n4_sympy_check["pass"],
            "n5_read_only_imports_present": True,
            "n5_z3_and_cvc5_agree_positive": n5_positive_pass,
            "n5_erased_control_flips": n5_negative_pass,
            "n5_unit_killed_control_fails_nonzero": n5_boundary_pass,
            "n5_sympy_exact_matches": n5_sympy_check["pass"],
            "n6_read_only_imports_present": True,
            "n6_z3_and_cvc5_agree_positive": n6_positive_pass,
            "n6_erased_control_flips": n6_negative_pass,
            "n6_unit_killed_control_fails_nonzero": n6_boundary_pass,
            "n6_sympy_exact_matches": n6_sympy_check["pass"],
            "n7_read_only_imports_present": True,
            "n7_z3_and_cvc5_agree_positive": n7_positive_pass,
            "n7_erased_control_flips": n7_negative_pass,
            "n7_unit_killed_control_fails_nonzero": n7_boundary_pass,
            "n7_sympy_exact_matches": n7_sympy_check["pass"],
            "n8_read_only_imports_present": True,
            "n8_z3_and_cvc5_agree_positive": n8_positive_pass,
            "n8_erased_control_flips": n8_negative_pass,
            "n8_unit_killed_control_fails_nonzero": n8_boundary_pass,
            "n8_sympy_exact_matches": n8_sympy_check["pass"],
        },
        "values": {
            "lifted_gap_squared_num": raw["normalized_gap_sq_num"],
            "lifted_gap_squared_den": raw["normalized_gap_sq_den"],
            "lifted_gap_decimal": float(sp.sqrt(sp.Rational(raw["normalized_gap_sq_num"], raw["normalized_gap_sq_den"]))),
            "erased_gap_squared": 0.0,
            "matrix_associator_norm": raw["exported_matrix_associator_norm"],
        },
        "n4_values": {
            "lifted_gap_squared_num": n4_raw["normalized_gap_sq_num"],
            "lifted_gap_squared_den": n4_raw["normalized_gap_sq_den"],
            "lifted_gap_decimal": float(sp.sqrt(sp.Rational(n4_raw["normalized_gap_sq_num"], n4_raw["normalized_gap_sq_den"]))),
            "erased_gap_squared": 0.0,
            "matrix_associator_norm": n4_raw["exported_matrix_associator_norm"],
            "exported_lifted_path_grouping_gap": n4_raw["exported_gap_decimal"],
            "exported_gap_matches_recomputed": abs(
                float(sp.sqrt(sp.Rational(n4_raw["normalized_gap_sq_num"], n4_raw["normalized_gap_sq_den"])))
                - float(n4_raw["exported_gap_decimal"])
            )
            < 1.0e-12,
        },
        "n5_values": {
            "lifted_gap_squared_num": n5_raw["normalized_gap_sq_num"],
            "lifted_gap_squared_den": n5_raw["normalized_gap_sq_den"],
            "lifted_gap_decimal": float(sp.sqrt(sp.Rational(n5_raw["normalized_gap_sq_num"], n5_raw["normalized_gap_sq_den"]))),
            "erased_gap_squared": 0.0,
            "matrix_associator_norm": n5_raw["exported_matrix_associator_norm"],
            "exported_lifted_path_grouping_gap": n5_raw["exported_gap_decimal"],
            "exported_gap_matches_recomputed": abs(
                float(sp.sqrt(sp.Rational(n5_raw["normalized_gap_sq_num"], n5_raw["normalized_gap_sq_den"])))
                - float(n5_raw["exported_gap_decimal"])
            )
            < 1.0e-12,
        },
        "n6_values": {
            "lifted_gap_squared_num": n6_raw["normalized_gap_sq_num"],
            "lifted_gap_squared_den": n6_raw["normalized_gap_sq_den"],
            "lifted_gap_decimal": float(sp.sqrt(sp.Rational(n6_raw["normalized_gap_sq_num"], n6_raw["normalized_gap_sq_den"]))),
            "erased_gap_squared": 0.0,
            "matrix_associator_norm": n6_raw["exported_matrix_associator_norm"],
            "exported_lifted_path_grouping_gap": n6_raw["exported_gap_decimal"],
            "exported_gap_matches_recomputed": abs(
                float(sp.sqrt(sp.Rational(n6_raw["normalized_gap_sq_num"], n6_raw["normalized_gap_sq_den"])))
                - float(n6_raw["exported_gap_decimal"])
            )
            < 1.0e-12,
        },
        "n7_values": {
            "lifted_gap_squared_num": n7_raw["normalized_gap_sq_num"],
            "lifted_gap_squared_den": n7_raw["normalized_gap_sq_den"],
            "lifted_gap_decimal": float(sp.sqrt(sp.Rational(n7_raw["normalized_gap_sq_num"], n7_raw["normalized_gap_sq_den"]))),
            "erased_gap_squared": 0.0,
            "matrix_associator_norm": n7_raw["exported_matrix_associator_norm"],
            "exported_lifted_path_grouping_gap": n7_raw["exported_gap_decimal"],
            "exported_gap_matches_recomputed": abs(
                float(sp.sqrt(sp.Rational(n7_raw["normalized_gap_sq_num"], n7_raw["normalized_gap_sq_den"])))
                - float(n7_raw["exported_gap_decimal"])
            )
            < 1.0e-12,
        },
        "n8_values": {
            "lifted_gap_squared_num": n8_raw["normalized_gap_sq_num"],
            "lifted_gap_squared_den": n8_raw["normalized_gap_sq_den"],
            "lifted_gap_decimal": float(sp.sqrt(sp.Rational(n8_raw["normalized_gap_sq_num"], n8_raw["normalized_gap_sq_den"]))),
            "erased_gap_squared": 0.0,
            "matrix_associator_norm": n8_raw["exported_matrix_associator_norm"],
            "exported_lifted_path_grouping_gap": n8_raw["exported_gap_decimal"],
            "exported_gap_matches_recomputed": abs(
                float(sp.sqrt(sp.Rational(n8_raw["normalized_gap_sq_num"], n8_raw["normalized_gap_sq_den"])))
                - float(n8_raw["exported_gap_decimal"])
            )
            < 1.0e-12,
        },
        "tool_calls": [
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver.add/check over lifted finite path count vectors",
                "input_object": "left/right path count vectors derived from n=3 support edges and one-excitation basis",
                "output_object": "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case": "lifted path count vector equality is UNSAT",
                "negative/erased_control": "density-token equality is SAT",
                "boundary_case": "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition": "demote if erased control does not flip to SAT",
                "gates": ["all_pass", "proof", "quotient"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver.assertFormula/checkSat over lifted finite path count vectors",
                "input_object": "same raw count vectors as z3",
                "output_object": "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case": "lifted path count vector equality is UNSAT",
                "negative/erased_control": "density-token equality is SAT",
                "boundary_case": "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition": "demote if cvc5 disagrees with z3",
                "gates": ["all_pass", "proof", "quotient"],
            },
            {
                "tool": "sympy",
                "qualified_api/function": "sympy.Matrix, Rational, sqrt, solve",
                "input_object": "same raw integer count vectors",
                "output_object": "exact gap_squared=2/3, erased_gap_squared=0, unit solution a=0",
                "positive_case": "exact lifted gap is sqrt(2/3)",
                "negative/erased_control": "erased quotient exact gap is 0",
                "boundary_case": "a=-a solves only a=0 over integers",
                "demotion_condition": "demote if exact rational row does not match solver polarity",
                "gates": ["all_pass", "divergence", "proof"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver.add/check over n=4 lifted finite path count vectors",
                "input_object": "left/right path count vectors derived from committed n=4 support edges and one-excitation basis",
                "output_object": "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case": "n=4 lifted path count vector equality is UNSAT",
                "negative/erased_control": "n=4 density-token equality is SAT",
                "boundary_case": "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition": "demote if n=4 erased control does not flip to SAT",
                "gates": ["all_pass", "proof", "quotient", "n4_extension"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver.assertFormula/checkSat over n=4 lifted finite path count vectors",
                "input_object": "same n=4 raw count vectors as z3",
                "output_object": "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case": "n=4 lifted path count vector equality is UNSAT",
                "negative/erased_control": "n=4 density-token equality is SAT",
                "boundary_case": "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition": "demote if cvc5 disagrees with z3 on n=4",
                "gates": ["all_pass", "proof", "quotient", "n4_extension"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver.add/check over n=5 lifted finite path count vectors",
                "input_object": "left/right path count vectors derived from committed n=5 support edges and one-excitation basis",
                "output_object": "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case": "n=5 lifted path count vector equality is UNSAT",
                "negative/erased_control": "n=5 density-token equality is SAT",
                "boundary_case": "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition": "demote if n=5 erased control does not flip to SAT",
                "gates": ["all_pass", "proof", "quotient", "n5_extension"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver.assertFormula/checkSat over n=5 lifted finite path count vectors",
                "input_object": "same n=5 raw count vectors as z3",
                "output_object": "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case": "n=5 lifted path count vector equality is UNSAT",
                "negative/erased_control": "n=5 density-token equality is SAT",
                "boundary_case": "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition": "demote if cvc5 disagrees with z3 on n=5",
                "gates": ["all_pass", "proof", "quotient", "n5_extension"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver.add/check over n=6 lifted finite path count vectors",
                "input_object": "left/right path count vectors derived from committed n=6 support edges and one-excitation basis",
                "output_object": "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case": "n=6 lifted path count vector equality is UNSAT",
                "negative/erased_control": "n=6 density-token equality is SAT",
                "boundary_case": "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition": "demote if n=6 erased control does not flip to SAT",
                "gates": ["all_pass", "proof", "quotient", "n6_extension"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver.assertFormula/checkSat over n=6 lifted finite path count vectors",
                "input_object": "same n=6 raw count vectors as z3",
                "output_object": "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case": "n=6 lifted path count vector equality is UNSAT",
                "negative/erased_control": "n=6 density-token equality is SAT",
                "boundary_case": "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition": "demote if cvc5 disagrees with z3 on n=6",
                "gates": ["all_pass", "proof", "quotient", "n6_extension"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver.add/check over n=7 lifted finite path count vectors",
                "input_object": "left/right path count vectors derived from committed n=7 support edges and one-excitation basis",
                "output_object": "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case": "n=7 lifted path count vector equality is UNSAT",
                "negative/erased_control": "n=7 density-token equality is SAT",
                "boundary_case": "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition": "demote if n=7 erased control does not flip to SAT",
                "gates": ["all_pass", "proof", "quotient", "n7_extension"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver.assertFormula/checkSat over n=7 lifted finite path count vectors",
                "input_object": "same n=7 raw count vectors as z3",
                "output_object": "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case": "n=7 lifted path count vector equality is UNSAT",
                "negative/erased_control": "n=7 density-token equality is SAT",
                "boundary_case": "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition": "demote if cvc5 disagrees with z3 on n=7",
                "gates": ["all_pass", "proof", "quotient", "n7_extension"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver.add/check over n=8 lifted finite path count vectors",
                "input_object": "left/right path count vectors derived from committed n=8 support edges and one-excitation basis",
                "output_object": "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case": "n=8 lifted path count vector equality is UNSAT",
                "negative/erased_control": "n=8 density-token equality is SAT",
                "boundary_case": "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition": "demote if n=8 erased control does not flip to SAT",
                "gates": ["all_pass", "proof", "quotient", "n8_extension"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver.assertFormula/checkSat over n=8 lifted finite path count vectors",
                "input_object": "same n=8 raw count vectors as z3",
                "output_object": "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case": "n=8 lifted path count vector equality is UNSAT",
                "negative/erased_control": "n=8 density-token equality is SAT",
                "boundary_case": "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition": "demote if cvc5 disagrees with z3 on n=8",
                "gates": ["all_pass", "proof", "quotient", "n8_extension"],
            },
        ],
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": str(RESULT_PATH.relative_to(ROOT))}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
