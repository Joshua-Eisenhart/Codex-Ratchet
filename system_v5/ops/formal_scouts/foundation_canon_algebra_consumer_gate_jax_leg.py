#!/usr/bin/env python3
"""JAX exhaustive/TMR consumer leg for the canon algebra table gate.

Scratch diagnostic only. JAX consumes the Julia-owned JSON structure constants
directly, computes the full octonion/quaternion basis associator maps locally,
uses vmap/jit for the 512-triple octonion batch, runs a high-volume random
vmap distribution, and derives the SAT/UNSAT SMT controls from bound C entries.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_jax_leg_results.json"
ARTIFACT_PATH = ROOT / "system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json"
OBJECT_ID = "foundation_canon_algebra_consumer_gate_jax_leg"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
EXPECTED_PROOF_TAG = "sha256:a9470fc299d39917a791bba0144d3e526866ad217b90fac1a6622b25d2c4652a"
TOL = 1.0e-12
RANDOM_TRIPLE_COUNT = 10_000
FAULT_INDEX = [3, 1, 2]


def utc_now() -> str:
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_artifact() -> dict[str, Any]:
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def algebra_record(artifact: dict[str, Any], name: str) -> dict[str, Any]:
    for record in artifact["algebras"]:
        if record["algebra"] == name:
            return record
    raise KeyError(f"missing algebra record: {name}")


def basis(dim: int, index: jax.Array) -> jax.Array:
    return jax.nn.one_hot(index, dim, dtype=jnp.float64)


def mul(C: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("kij,i,j->k", C, x, y)


def associator_vector(C: jax.Array, a: jax.Array, b: jax.Array, c: jax.Array) -> jax.Array:
    return mul(C, mul(C, a, b), c) - mul(C, a, mul(C, b, c))


def basis_associator_norm(C: jax.Array, triple: jax.Array) -> jax.Array:
    dim = int(C.shape[0])
    a = basis(dim, triple[0])
    b = basis(dim, triple[1])
    c = basis(dim, triple[2])
    return jnp.linalg.norm(associator_vector(C, a, b, c))


def all_triples(dim: int) -> jax.Array:
    return jnp.indices((dim, dim, dim), dtype=jnp.int32).reshape(3, -1).T


@jax.jit
def batched_basis_norms(C: jax.Array, triples: jax.Array) -> jax.Array:
    return jax.vmap(lambda triple: basis_associator_norm(C, triple))(triples)


def full_basis_map(C: jax.Array) -> dict[str, Any]:
    triples = all_triples(int(C.shape[0]))
    norms = batched_basis_norms(C, triples)
    triple_list = jax.device_get(triples).tolist()
    norm_list = [float(item) for item in jax.device_get(norms).tolist()]
    entries = [{"triple": [int(x) for x in triple], "norm": norm} for triple, norm in zip(triple_list, norm_list, strict=True)]
    nonzero_count = sum(1 for item in norm_list if item > TOL)
    return {
        "entries": entries,
        "entry_count": len(entries),
        "nonzero_count_gt_tol": nonzero_count,
        "zero_count_le_tol": len(entries) - nonzero_count,
        "max_norm": max(norm_list) if norm_list else 0.0,
        "tol": TOL,
        "batched_shape": {
            "C": list(C.shape),
            "triples": list(triples.shape),
            "norms": list(norms.shape),
        },
    }


@jax.jit
def normalize_unit_triples(raw: jax.Array) -> jax.Array:
    norms = jnp.linalg.norm(raw, axis=-1, keepdims=True)
    return raw / norms


@jax.jit
def random_associator_norms(C: jax.Array, triples: jax.Array) -> jax.Array:
    return jax.vmap(lambda triple: jnp.linalg.norm(associator_vector(C, triple[0], triple[1], triple[2])))(triples)


def random_distribution(C: jax.Array, count: int = RANDOM_TRIPLE_COUNT) -> dict[str, Any]:
    key = jax.random.PRNGKey(20260608)
    raw = jax.random.normal(key, (count, 3, int(C.shape[0])), dtype=jnp.float64)
    triples = normalize_unit_triples(raw)
    norms = random_associator_norms(C, triples)
    nonzero = jnp.count_nonzero(norms > TOL)
    return {
        "random_seed": 20260608,
        "triple_count": count,
        "input_shape": list(triples.shape),
        "output_shape": list(norms.shape),
        "count_nonzero_gt_tol": int(nonzero),
        "mean_norm": float(jnp.mean(norms)),
        "max_norm": float(jnp.max(norms)),
        "tol": TOL,
    }


def first_nonzero_triple(map_payload: dict[str, Any]) -> list[int]:
    for entry in map_payload["entries"]:
        if float(entry["norm"]) > TOL:
            return [int(x) for x in entry["triple"]]
    raise ValueError("octonion map has no nonzero associator triple")


def fault_injection(C: jax.Array) -> dict[str, Any]:
    original = float(C[FAULT_INDEX[0], FAULT_INDEX[1], FAULT_INDEX[2]])
    if abs(original) <= TOL:
        fault_value = 1.0
    else:
        fault_value = -original
    fault_C = C.at[FAULT_INDEX[0], FAULT_INDEX[1], FAULT_INDEX[2]].set(fault_value)
    fault_map = full_basis_map(fault_C)
    normal_map = full_basis_map(C)
    divergences = [
        abs(float(a["norm"]) - float(b["norm"]))
        for a, b in zip(normal_map["entries"], fault_map["entries"], strict=True)
    ]
    changed = sum(1 for item in divergences if item > TOL)
    return {
        "engine_copy": "jax_only",
        "fault_index_C_k_i_j_zero_based": FAULT_INDEX,
        "original_value": original,
        "fault_value": fault_value,
        "restored_by_copy": True,
        "detected_divergence": max(divergences) if divergences else 0.0,
        "changed_entry_count": changed,
        "fault_associator_norm_map": fault_map,
    }


def z3_sum(terms: list[Any]) -> Any:
    return z3.IntVal(0) if not terms else z3.Sum(terms)


def z3_bound_C(table: list[list[list[int]]], prefix: str) -> tuple[z3.Solver, list[list[list[Any]]]]:
    solver = z3.Solver()
    dim = len(table)
    C: list[list[list[Any]]] = []
    for k in range(dim):
        Ck = []
        for i in range(dim):
            Cki = []
            for j in range(dim):
                var = z3.Int(f"{prefix}_C_{k}_{i}_{j}")
                solver.add(var == int(table[k][i][j]))
                Cki.append(var)
            Ck.append(Cki)
        C.append(Ck)
    return solver, C


def z3_basis(dim: int, index: int) -> list[Any]:
    return [z3.IntVal(1 if i == index else 0) for i in range(dim)]


def z3_mul(C: list[list[list[Any]]], x: list[Any], y: list[Any]) -> list[Any]:
    dim = len(C)
    return [
        z3_sum([C[k][i][j] * x[i] * y[j] for i in range(dim) for j in range(dim)])
        for k in range(dim)
    ]


def z3_associator(C: list[list[list[Any]]], a: int, b: int, c: int) -> list[Any]:
    dim = len(C)
    av = z3_basis(dim, a)
    bv = z3_basis(dim, b)
    cv = z3_basis(dim, c)
    left = z3_mul(C, z3_mul(C, av, bv), cv)
    right = z3_mul(C, av, z3_mul(C, bv, cv))
    return [left[k] - right[k] for k in range(dim)]


def z3_fixed_nonzero(table: list[list[list[int]]], prefix: str, triple: list[int]) -> dict[str, Any]:
    solver, C = z3_bound_C(table, prefix)
    assoc = z3_associator(C, triple[0], triple[1], triple[2])
    solver.add(z3.Or([term != 0 for term in assoc]))
    verdict = str(solver.check())
    erased, _ = z3_bound_C(table, f"{prefix}_erased")
    return {
        "solver": "z3",
        "verdict": verdict,
        "drop_nonzero_assertion_verdict": str(erased.check()),
        "derive_in_solver": True,
        "bound_structure_constant_count": len(table) ** 3,
        "triple_indices_zero_based": triple,
        "asserted_shape": "exists k: associator(C,e_a,e_b,e_c)[k] != 0",
    }


def z3_no_basis_associator(table: list[list[list[int]]], prefix: str) -> dict[str, Any]:
    solver, C = z3_bound_C(table, prefix)
    dim = len(table)
    terms = []
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                terms.extend([term != 0 for term in z3_associator(C, a, b, c)])
    solver.add(z3.Or(terms))
    verdict = str(solver.check())
    erased, _ = z3_bound_C(table, f"{prefix}_erased")
    return {
        "solver": "z3",
        "verdict": verdict,
        "drop_nonzero_assertion_verdict": str(erased.check()),
        "derive_in_solver": True,
        "basis_triples_checked": dim**3,
        "bound_structure_constant_count": dim**3,
        "asserted_shape": "exists basis triple and k: associator(C,e_a,e_b,e_c)[k] != 0",
    }


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkInteger(0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def cvc5_product(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkInteger(1)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.MULT, *terms)


def cvc5_or(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(False)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.OR, *terms)


def cvc5_bound_C(table: list[list[list[int]]], prefix: str) -> tuple[cvc5.Solver, list[list[list[Any]]]]:
    solver = cvc5.Solver()
    solver.setLogic("QF_NIA")
    int_sort = solver.getIntegerSort()
    dim = len(table)
    C: list[list[list[Any]]] = []
    for k in range(dim):
        Ck = []
        for i in range(dim):
            Cki = []
            for j in range(dim):
                var = solver.mkConst(int_sort, f"{prefix}_C_{k}_{i}_{j}")
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(int(table[k][i][j]))))
                Cki.append(var)
            Ck.append(Cki)
        C.append(Ck)
    return solver, C


def cvc5_basis(solver: cvc5.Solver, dim: int, index: int) -> list[Any]:
    return [solver.mkInteger(1 if i == index else 0) for i in range(dim)]


def cvc5_mul(solver: cvc5.Solver, C: list[list[list[Any]]], x: list[Any], y: list[Any]) -> list[Any]:
    dim = len(C)
    return [
        cvc5_sum(
            solver,
            [cvc5_product(solver, [C[k][i][j], x[i], y[j]]) for i in range(dim) for j in range(dim)],
        )
        for k in range(dim)
    ]


def cvc5_associator(solver: cvc5.Solver, C: list[list[list[Any]]], a: int, b: int, c: int) -> list[Any]:
    dim = len(C)
    av = cvc5_basis(solver, dim, a)
    bv = cvc5_basis(solver, dim, b)
    cv = cvc5_basis(solver, dim, c)
    left = cvc5_mul(solver, C, cvc5_mul(solver, C, av, bv), cv)
    right = cvc5_mul(solver, C, av, cvc5_mul(solver, C, bv, cv))
    return [solver.mkTerm(Kind.SUB, left[k], right[k]) for k in range(dim)]


def cvc5_fixed_nonzero(table: list[list[list[int]]], prefix: str, triple: list[int]) -> dict[str, Any]:
    solver, C = cvc5_bound_C(table, prefix)
    zero = solver.mkInteger(0)
    assoc = cvc5_associator(solver, C, triple[0], triple[1], triple[2])
    nonzero = [solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, term, zero)) for term in assoc]
    solver.assertFormula(cvc5_or(solver, nonzero))
    verdict = cvc5_status(solver.checkSat())
    erased, _ = cvc5_bound_C(table, f"{prefix}_erased")
    return {
        "solver": "cvc5",
        "verdict": verdict,
        "drop_nonzero_assertion_verdict": cvc5_status(erased.checkSat()),
        "derive_in_solver": True,
        "bound_structure_constant_count": len(table) ** 3,
        "triple_indices_zero_based": triple,
        "asserted_shape": "exists k: associator(C,e_a,e_b,e_c)[k] != 0",
    }


def cvc5_no_basis_associator(table: list[list[list[int]]], prefix: str) -> dict[str, Any]:
    solver, C = cvc5_bound_C(table, prefix)
    dim = len(table)
    zero = solver.mkInteger(0)
    terms = []
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                terms.extend(
                    [
                        solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, term, zero))
                        for term in cvc5_associator(solver, C, a, b, c)
                    ]
                )
    solver.assertFormula(cvc5_or(solver, terms))
    verdict = cvc5_status(solver.checkSat())
    erased, _ = cvc5_bound_C(table, f"{prefix}_erased")
    return {
        "solver": "cvc5",
        "verdict": verdict,
        "drop_nonzero_assertion_verdict": cvc5_status(erased.checkSat()),
        "derive_in_solver": True,
        "basis_triples_checked": dim**3,
        "bound_structure_constant_count": dim**3,
        "asserted_shape": "exists basis triple and k: associator(C,e_a,e_b,e_c)[k] != 0",
    }


def tool_call(
    *,
    tool: str,
    api_surface: str,
    input_object: Any,
    output_object: Any,
    positive_case: Any,
    negative_control: Any,
    boundary_case: Any,
    demotion_condition: str,
) -> dict[str, Any]:
    return {
        "tool": tool,
        "api_surface": api_surface,
        "input_object": input_object,
        "output_object": output_object,
        "positive_case": positive_case,
        "negative_control": negative_control,
        "boundary_case": boundary_case,
        "demotion_condition": demotion_condition,
    }


def build_result() -> dict[str, Any]:
    artifact = load_artifact()
    artifact_sha = sha256_file(ARTIFACT_PATH)
    artifact_source = Path(str(artifact["source_path"]))
    artifact_source_sha = sha256_file(artifact_source) if artifact_source.is_file() else "missing"
    oct_record = algebra_record(artifact, "octonion")
    quat_record = algebra_record(artifact, "quaternion")
    oct_table = oct_record["C"]
    quat_table = quat_record["C"]
    oct_C = jnp.array(oct_table, dtype=jnp.float64)
    quat_C = jnp.array(quat_table, dtype=jnp.float64)

    oct_map = full_basis_map(oct_C)
    quat_map = full_basis_map(quat_C)
    sampled_nonzero_triple = first_nonzero_triple(oct_map)
    oct_z3 = z3_fixed_nonzero(oct_table, "jax_octonion_sampled_nonzero", sampled_nonzero_triple)
    quat_z3 = z3_no_basis_associator(quat_table, "jax_quaternion_all_basis")
    oct_cvc5 = cvc5_fixed_nonzero(oct_table, "jax_octonion_sampled_nonzero", sampled_nonzero_triple)
    quat_cvc5 = cvc5_no_basis_associator(quat_table, "jax_quaternion_all_basis")
    random_stats = random_distribution(oct_C, RANDOM_TRIPLE_COUNT)
    fault = fault_injection(oct_C)

    source_checks = {
        "artifact_path": str(ARTIFACT_PATH),
        "artifact_sha256": artifact_sha,
        "artifact_source_path": str(artifact_source),
        "artifact_source_sha256_expected": artifact["source_sha256"],
        "artifact_source_sha256_current": artifact_source_sha,
        "artifact_source_sha256_matches": artifact_source_sha == artifact["source_sha256"],
        "proof_tag": artifact["proof_tag"],
        "proof_tag_matches_expected": artifact["proof_tag"] == EXPECTED_PROOF_TAG,
        "proof_pass": artifact["proof_pass"],
        "table_version": artifact["table_version"],
        "bracket_convention": artifact["bracket_convention"],
    }
    proofs = {
        "z3": {
            "version": z3.get_version_string(),
            "octonion_sampled_nonzero_assoc": oct_z3,
            "quaternion_associator_nonzero_exists": quat_z3,
        },
        "cvc5": {
            "version": getattr(cvc5, "__version__", None),
            "octonion_sampled_nonzero_assoc": oct_cvc5,
            "quaternion_associator_nonzero_exists": quat_cvc5,
        },
    }
    all_pass = (
        source_checks["artifact_source_sha256_matches"]
        and source_checks["proof_tag_matches_expected"]
        and source_checks["proof_pass"] is True
        and source_checks["bracket_convention"] == "left"
        and bool(jax.config.jax_enable_x64)
        and oct_map["entry_count"] == 512
        and oct_map["nonzero_count_gt_tol"] > 0
        and quat_map["entry_count"] == 64
        and quat_map["nonzero_count_gt_tol"] == 0
        and random_stats["triple_count"] >= 10_000
        and random_stats["count_nonzero_gt_tol"] > 0
        and fault["detected_divergence"] > TOL
        and oct_z3["verdict"] == "sat"
        and oct_cvc5["verdict"] == "sat"
        and quat_z3["verdict"] == "unsat"
        and quat_cvc5["verdict"] == "unsat"
    )

    vmap_shapes = {
        "exhaustive_basis_batch": oct_map["batched_shape"],
        "random_unit_triples": {"input": random_stats["input_shape"], "output": random_stats["output_shape"]},
    }
    tool_calls = [
        tool_call(
            tool="json",
            api_surface="json.loads(ARTIFACT_PATH.read_text(encoding='utf-8'))",
            input_object={"source_path": str(ARTIFACT_PATH)},
            output_object={"table_version": artifact["table_version"], "proof_tag": artifact["proof_tag"], "artifact_sha256": artifact_sha},
            positive_case="Loaded the Julia-owned canon table without reading peer engine results.",
            negative_control="Demotes if the leg recomputes C or reads Julia/JAX/PyTorch result JSON as input.",
            boundary_case="Quaternion and octonion records preserve bracket_convention=left.",
            demotion_condition="Demote if artifact source hash, proof tag, proof pass, or bracket convention fails.",
        ),
        tool_call(
            tool="jax.vmap",
            api_surface="jax.jit(jax.vmap(lambda triple: basis_associator_norm(C, triple)))",
            input_object={"algebra": "octonion", "C_shape": list(oct_C.shape), "triples_shape": oct_map["batched_shape"]["triples"]},
            output_object={"norms_shape": oct_map["batched_shape"]["norms"], "entry_count": oct_map["entry_count"], "nonzero_count_gt_tol": oct_map["nonzero_count_gt_tol"]},
            positive_case="JAX computes all 512 octonion basis associator norms as one batched vmap/jit kernel.",
            negative_control={"jax_only_fault_injection_detected_divergence": fault["detected_divergence"], "changed_entry_count": fault["changed_entry_count"]},
            boundary_case={"quaternion_entry_count": quat_map["entry_count"], "quaternion_nonzero_count_gt_tol": quat_map["nonzero_count_gt_tol"]},
            demotion_condition="Demote if exhaustive basis norms are computed by a Python loop or if vmap shapes are absent.",
        ),
        tool_call(
            tool="jax.vmap",
            api_surface="jax.jit(jax.vmap(lambda triple: norm(associator(C, triple[0], triple[1], triple[2]))))",
            input_object={"random_unit_octonion_triples_shape": random_stats["input_shape"], "count": random_stats["triple_count"]},
            output_object={"norms_shape": random_stats["output_shape"], "count_nonzero": random_stats["count_nonzero_gt_tol"], "mean": random_stats["mean_norm"], "max": random_stats["max_norm"]},
            positive_case="JAX performs high-volume random unit-triple associator coverage that the other legs do not run.",
            negative_control="Demotes if random triples are not normalized or count is below 10000.",
            boundary_case="Distribution is scratch diagnostic only and does not promote the basis TMR result.",
            demotion_condition="Demote if this uses numpy, a Python loop over triples, or a non-JAX random source.",
        ),
        tool_call(
            tool="z3",
            api_surface="z3.Solver().add(bound C equations and associator expression); Solver.check()",
            input_object={"octonion_sampled_nonzero_triple": sampled_nonzero_triple, "quaternion_scope": "all basis triples"},
            output_object=proofs["z3"],
            positive_case="z3 derives octonion associator nonzero SAT from bound C entries.",
            negative_control={"drop_nonzero_assertion_verdict": oct_z3["drop_nonzero_assertion_verdict"]},
            boundary_case="z3 derives quaternion nonzero associator exists is UNSAT over all basis triples.",
            demotion_condition="Demote if z3 is handed a precomputed associator scalar instead of bound C algebra.",
        ),
        tool_call(
            tool="cvc5",
            api_surface="cvc5.Solver().assertFormula(bound C equations and associator expression); checkSat()",
            input_object={"octonion_sampled_nonzero_triple": sampled_nonzero_triple, "quaternion_scope": "all basis triples"},
            output_object=proofs["cvc5"],
            positive_case="cvc5 derives octonion associator nonzero SAT from bound C entries.",
            negative_control={"drop_nonzero_assertion_verdict": oct_cvc5["drop_nonzero_assertion_verdict"]},
            boundary_case="cvc5 derives quaternion nonzero associator exists is UNSAT over all basis triples.",
            demotion_condition="Demote if cvc5 disagrees with z3 or receives a precomputed scalar claim.",
        ),
    ]

    canon_runtime = {
        "semantic_owner": "julia",
        "artifact_path": str(ARTIFACT_PATH),
        "artifact_sha256": artifact_sha,
        "source_sha256": artifact["source_sha256"],
        "receipt_path": str(ROOT / "system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json"),
        "proof_tag": artifact["proof_tag"],
        "proof_pass": artifact["proof_pass"],
        "table_version": artifact["table_version"],
        "bracket_convention": artifact["bracket_convention"],
        "consumer_policy": "compute_from_exported_C_tensor_with_fixed_parenthesization",
    }

    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "schema_version": "codex_ratchet.engine_leg_result.v1",
        "object_id": OBJECT_ID,
        "engine": "jax",
        "generated_at": utc_now(),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "sys_executable": sys.executable,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json"],
        "aligned_packages_load_bearing": ["jax", "z3", "cvc5"],
        "claim_path_tools": ["jax", "jax.numpy", "z3", "cvc5", "json"],
        "control_only_tools": [],
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "source_checks": source_checks,
        "canon_runtime": canon_runtime,
        "associator_norm_maps": {
            "octonion_basis_triples": oct_map,
            "quaternion_basis_triples": quat_map,
        },
        "sampled_nonzero_triple": sampled_nonzero_triple,
        "jax_parallel_workhorse": {
            "uses_jax_vmap": True,
            "uses_jax_jit": True,
            "batched_shapes": vmap_shapes,
            "random_unit_triple_distribution": random_stats,
        },
        "fault_injection": fault,
        "proofs": proofs,
        "tool_calls": tool_calls,
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "load-bearing batched exhaustive and random associator kernels"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing derive-in-solver SAT/UNSAT controls from bound C"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent SMT agreement with z3"},
            "json": {"tried": True, "used": True, "reason": "supportive canon artifact intake"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "json": "supportive",
        },
        "all_pass": all_pass,
        "GAINED": [
            "JAX consumed the Julia-owned canon table and computed the full 512-entry octonion associator-norm map with vmap/jit.",
            "JAX vmap produced a 10000-random-unit-triple associator norm distribution.",
            "JAX-side z3+cvc5 derived octonion SAT and quaternion UNSAT from bound C entries.",
        ],
        "NOT_GAINED": ["No independent JAX table authority; no promotion; no formal admission."],
        "CONTROLS": [
            "quaternion all-basis associator map is zero",
            "jax-only fault injection changes the associator map",
            "z3/cvc5 agree on octonion SAT and quaternion UNSAT",
        ],
        "CEILING": "classification=scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false",
    }


def main() -> int:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": str(RESULT_PATH), "source_sha256": result["source_sha256"]}))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
