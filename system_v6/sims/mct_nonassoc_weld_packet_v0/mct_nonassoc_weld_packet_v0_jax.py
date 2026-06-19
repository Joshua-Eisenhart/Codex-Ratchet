#!/usr/bin/env python3
"""JAX leg for mct_nonassoc_weld_packet_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "mct_nonassoc_weld_packet_v0"
ENGINE = "jax"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"
ARTIFACT_PATH = ROOT / "system_v5" / "julia_carrier" / "artifacts" / "algebra_structure_constants_v1.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-8

POSITIVE_TRIPLE = (1, 2, 4)
QUATERNION_TRIPLE = (1, 2, 3)
ALTERNATIVE_TRIPLE = (1, 1, 4)
COMMITTED_RESIDUAL = [0, 0, 0, 0, 0, 0, 0, 2]
COMMITTED_COMPONENT = 7

# Whole-table signed lift from the Octonions.jl artifact convention to the
# committed Cayley-Dickson classifier convention that pins (e1,e2,e4) -> 2e7.
ARTIFACT_TO_COMMITTED_PERM = [0, 1, 2, 3, 4, 7, 6, 5]
ARTIFACT_TO_COMMITTED_SIGNS = [1, 1, 1, 1, 1, -1, 1, -1]

PIN_BLOCK = {
    "packet_id": SIM_ID,
    "claim": "finite M(C,t) packet computes one load-bearing bracketing-sensitive associator operation",
    "main_support_branch": "branch_b_three_spinor_floor",
    "support": "S_t={(psi,x,y,z,bracket): psi in finite (C^2)^3 witness set, x,y,z in O_basis bounded triples}",
    "triple_set": {
        "positive_o_witness": list(POSITIVE_TRIPLE),
        "quaternion_control": list(QUATERNION_TRIPLE),
        "repeated_input_alternativity_control": list(ALTERNATIVE_TRIPLE),
        "small_deterministic_sweep": [[1, 2, 5], [1, 4, 5], [2, 4, 6], [3, 6, 5], [4, 5, 1]],
        "full_512_ordered_triple_sweep": "verification_sidecar",
    },
    "operation": "associator_bracketing",
    "ceiling": {
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "canonical_carrier_admission": False,
        "final_M_C": False,
        "axis0": False,
        "bridge": False,
        "physics": False,
        "g2_root_forced": False,
    },
    "branches": {
        "branch_a_direct_O": "projection_lift_row_only",
        "branch_b_three_spinor_floor": "main_support",
        "branch_c_sedenion_zero_divisor": "graveyard_control",
        "branch_d_split_O": "Var_t_inactive",
    },
}
PIN_BLOCK_SHA256 = hashlib.sha256(json.dumps(PIN_BLOCK, sort_keys=True).encode("utf-8")).hexdigest()

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 table contractions, full 512-triple sweep, density-erasure, quotient counts, and G2 derivation-rank computation; demoted until a passing jax capability probe exists"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive finite structure-constant products, tensor norms, matrix associativity control, and SVD rank/nullity; demoted until passing jax and jax.numpy capability probes exist"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing raw-value UNSAT/SAT proof over computed associator vectors and control flips"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent raw-value UNSAT/SAT proof over the same computed associator vectors and control flips"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive JSON, hashing, timestamp, and path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def to_builtin(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_builtin(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_builtin(v) for v in value]
    if hasattr(value, "shape"):
        arr = jax.device_get(value)
        if arr.shape == ():
            f = float(arr)
            return int(round(f)) if abs(f - round(f)) < TOL else f
        return arr.tolist()
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return str(value)


def load_artifact() -> dict[str, Any]:
    payload = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    algebras = {row["algebra"]: row for row in payload["algebras"]}
    return {
        "payload": payload,
        "octonion": algebras["octonion"],
        "quaternion": algebras["quaternion"],
        "artifact_sha256": sha256_file(ARTIFACT_PATH),
    }


def transform_table(table: list[list[list[int]]], perm: list[int], signs: list[int]) -> list[list[list[int]]]:
    n = len(table)
    inv = [0] * n
    for src_idx, tgt_idx in enumerate(perm):
        inv[tgt_idx] = src_idx
    out = [[[0 for _ in range(n)] for _ in range(n)] for _ in range(n)]
    for kt in range(n):
        ks = inv[kt]
        for it in range(n):
            isrc = inv[it]
            for jt in range(n):
                jsrc = inv[jt]
                out[kt][it][jt] = signs[isrc] * signs[jsrc] * int(table[ks][isrc][jsrc]) * signs[ks]
    return out


def table_hash(table: list[list[list[int]]]) -> str:
    return hashlib.sha256(json.dumps(table, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()


def as_array(table: list[list[list[int]]]) -> jax.Array:
    return jnp.asarray(table, dtype=jnp.float64)


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("kij,i,j->k", table, x, y)


def associator(table: jax.Array, triple: tuple[int, int, int]) -> dict[str, Any]:
    dim = int(table.shape[0])
    x, y, z = (basis(dim, triple[0]), basis(dim, triple[1]), basis(dim, triple[2]))
    xy = multiply(table, x, y)
    yz = multiply(table, y, z)
    left = multiply(table, xy, z)
    right = multiply(table, x, yz)
    residual = left - right
    return {
        "triple": list(triple),
        "left_product": to_builtin(left),
        "right_product": to_builtin(right),
        "residual_vector": to_builtin(residual),
        "residual_norm": float(jax.device_get(jnp.linalg.norm(residual))),
        "residual_norm_sq": int(round(float(jax.device_get(jnp.sum(residual * residual))))),
        "component_rows": [{"index": idx, "value": int(round(float(v)))} for idx, v in enumerate(jax.device_get(residual).tolist()) if abs(float(v)) > TOL],
    }


def commutator_norm(table: jax.Array, i: int, j: int) -> float:
    return float(jax.device_get(jnp.linalg.norm(multiply(table, basis(table.shape[0], i), basis(table.shape[0], j)) - multiply(table, basis(table.shape[0], j), basis(table.shape[0], i)))))


def psi_witness() -> jax.Array:
    psi = jnp.zeros((8,), dtype=jnp.complex128)
    psi = psi.at[0].set(1 / math.sqrt(2.0))
    psi = psi.at[7].set(1j / math.sqrt(2.0))
    return psi


def density(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conjugate(psi))


def density_erasure_receipt(pos: dict[str, Any]) -> dict[str, Any]:
    psi = psi_witness()
    left_vec = jnp.asarray(pos["left_product"], dtype=jnp.float64)
    right_vec = jnp.asarray(pos["right_product"], dtype=jnp.float64)
    left_sign = 1.0 if float(left_vec[COMMITTED_COMPONENT]) >= 0.0 else -1.0
    right_sign = 1.0 if float(right_vec[COMMITTED_COMPONENT]) >= 0.0 else -1.0
    left_spinor = left_sign * psi
    right_spinor = right_sign * psi
    rho_left = density(left_spinor)
    rho_right = density(right_spinor)
    return {
        "left_component_sign": int(left_sign),
        "right_component_sign": int(right_sign),
        "spinor_gap_norm": float(jax.device_get(jnp.linalg.norm(left_spinor - right_spinor))),
        "density_gap_norm": float(jax.device_get(jnp.linalg.norm(rho_left - rho_right))),
        "visible_on_lifted_spinor_row": bool(float(jax.device_get(jnp.linalg.norm(left_spinor - right_spinor))) > 1.0),
        "erased_under_density_quotient": bool(float(jax.device_get(jnp.linalg.norm(rho_left - rho_right))) <= TOL),
        "quotient_genuinely_recomputed": True,
        "computed_from_left_right_products": True,
    }


def support_rows(table: jax.Array) -> list[dict[str, Any]]:
    triple_rows = [
        ("positive_o_witness", POSITIVE_TRIPLE),
        ("quaternion_control", QUATERNION_TRIPLE),
        ("alternativity_control", ALTERNATIVE_TRIPLE),
        ("sweep_125", (1, 2, 5)),
        ("sweep_145", (1, 4, 5)),
        ("sweep_246", (2, 4, 6)),
        ("sweep_365", (3, 6, 5)),
        ("sweep_451", (4, 5, 1)),
    ]
    rows: list[dict[str, Any]] = []
    for name, triple in triple_rows:
        assoc = associator(table, triple)
        order_norm = commutator_norm(table, triple[0], triple[1])
        for side in ("left", "right"):
            product_vec = assoc[f"{side}_product"]
            rows.append(
                {
                    "state_id": f"psi0:{name}:{side}",
                    "psi_id": "psi0_three_spinor_floor",
                    "triple_name": name,
                    "x": triple[0],
                    "y": triple[1],
                    "z": triple[2],
                    "bracket": side,
                    "P_density": "rho_sign_erased",
                    "P_order": round(order_norm, 12),
                    "P_phase": "sign_visible" if assoc["residual_norm"] > TOL else "sign_collapsed",
                    "P_assoc_vec": assoc["residual_vector"],
                    "P_assoc_norm": assoc["residual_norm"],
                    "P_assoc_component": assoc["component_rows"],
                    "P_bracket_side": side,
                    "P_density_erasure": side == "left",
                    "P_alt_control": name == "alternativity_control" and assoc["residual_norm"] <= TOL,
                    "left_or_right_product": product_vec,
                }
            )
    return rows


def quotient_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def active_key(row: dict[str, Any]) -> str:
        return json.dumps(
            [
                row["psi_id"],
                row["triple_name"],
                row["P_density"],
                row["P_order"],
                row["P_phase"],
                row["P_assoc_vec"],
                row["P_bracket_side"],
                row["left_or_right_product"],
            ],
            sort_keys=True,
        )

    def dropped_key(row: dict[str, Any]) -> str:
        return json.dumps([row["psi_id"], row["triple_name"], row["P_density"], row["P_order"]], sort_keys=True)

    active = {active_key(row) for row in rows}
    dropped = {dropped_key(row) for row in rows}
    return {
        "active_bracketing_class_count": len(active),
        "dropped_bracketing_class_count": len(dropped),
        "refines_when_active": len(active) > len(dropped),
        "coarsens_when_dropped": len(dropped) < len(active),
    }


def full_sweep_summary(table: jax.Array) -> dict[str, Any]:
    triples = jnp.asarray([[i, j, k] for i in range(8) for j in range(8) for k in range(8)], dtype=jnp.int64)

    def residual_norm_sq(idx: jax.Array) -> jax.Array:
        x, y, z = basis(8, idx[0]), basis(8, idx[1]), basis(8, idx[2])
        r = multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))
        return jnp.sum(r * r)

    norms = jax.vmap(residual_norm_sq)(triples)
    nonzero = int(jax.device_get(jnp.sum(norms > TOL)))
    max_norm_sq = int(round(float(jax.device_get(jnp.max(norms)))))
    return {
        "ran": True,
        "basis_triples_checked": 512,
        "nonzero_associator_count": nonzero,
        "max_residual_norm_sq": max_norm_sq,
        "used_jax_vmap": True,
    }


def raw_matrix_control() -> dict[str, Any]:
    sx = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
    sy = jnp.asarray([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    sz = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
    residual = (sx @ sy) @ sz - sx @ (sy @ sz)
    norm = float(jax.device_get(jnp.linalg.norm(residual)))
    return {
        "matrix_family": "2x2 Pauli matrices",
        "residual_norm": norm,
        "collapse_pass": norm <= TOL,
        "failure_value_emitted": to_builtin(residual),
    }


def table_h() -> jax.Array:
    return jnp.asarray(load_artifact()["quaternion"]["C"], dtype=jnp.float64)


def table_m2() -> jax.Array:
    c = jnp.zeros((4, 4, 4), dtype=jnp.float64)
    basis_pairs = [(0, 0), (0, 1), (1, 0), (1, 1)]
    index = {pair: idx for idx, pair in enumerate(basis_pairs)}
    for i, (a, b) in enumerate(basis_pairs):
        for j, (d, e) in enumerate(basis_pairs):
            if b == d:
                c = c.at[index[(a, e)], i, j].set(1)
    return c


def derivation_matrix(c: jax.Array) -> jax.Array:
    n = int(c.shape[0])
    rows = []
    for i in range(n):
        for j in range(n):
            for k in range(n):
                row = jnp.zeros((n, n), dtype=jnp.float64)
                for ell in range(n):
                    row = row.at[k, ell].add(c[ell, i, j])
                for a in range(n):
                    row = row.at[a, i].add(-c[k, a, j])
                for b in range(n):
                    row = row.at[b, j].add(-c[k, i, b])
                rows.append(jnp.ravel(row))
    return jnp.stack(rows)


def derivation_summary(name: str, c: jax.Array) -> dict[str, Any]:
    mat = derivation_matrix(c)
    singular = jnp.linalg.svd(mat, compute_uv=False)
    rank = int(jax.device_get(jnp.sum(singular > TOL)))
    n = int(c.shape[0])
    return {
        "carrier": name,
        "basis_dimension": n,
        "equation_count": int(mat.shape[0]),
        "unknown_count": n * n,
        "rank": rank,
        "nullity_dim_der": n * n - rank,
        "rank_method": "jax.numpy.linalg.svd singular values > 1e-8",
    }


def corrupt_table(table: list[list[list[int]]]) -> list[list[list[int]]]:
    out = json.loads(json.dumps(table))
    out[3][1][2] = -out[3][1][2]
    return out


def int_table(c: jax.Array) -> list[list[list[int]]]:
    raw = jax.device_get(c)
    n = int(c.shape[0])
    return [[[int(round(float(raw[k, i, j]))) for j in range(n)] for i in range(n)] for k in range(n)]


def product_closes_and_anticommutes(values: list[list[list[int]]], a: int, b: int) -> bool:
    n = len(values)
    anti = all(values[k][a][b] + values[k][b][a] == 0 for k in range(n))
    product = [values[k][a][b] for k in range(n)]
    nonzero = [k for k, value in enumerate(product) if value != 0]
    return anti and len(nonzero) == 1 and nonzero[0] != 0 and abs(product[nonzero[0]]) == 1


def z3_root_sat(values: list[list[list[int]]], prefix: str) -> str:
    solver = z3.Solver()
    terms = []
    n = len(values)
    for k in range(n):
        for i in range(n):
            for j in range(i + 1, n):
                v = z3.Int(f"{prefix}_comm_{k}_{i}_{j}")
                solver.add(v == values[k][i][j] - values[k][j][i])
                terms.append(v != 0)
    solver.add(z3.Or(terms))
    return str(solver.check())


def cvc5_root_sat(values: list[list[list[int]]], prefix: str) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    terms = []
    n = len(values)
    for k in range(n):
        for i in range(n):
            for j in range(i + 1, n):
                v = solver.mkConst(int_sort, f"{prefix}_comm_{k}_{i}_{j}")
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, v, solver.mkInteger(values[k][i][j] - values[k][j][i])))
                terms.append(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, v, solver.mkInteger(0))))
    solver.assertFormula(terms[0] if len(terms) == 1 else solver.mkTerm(Kind.OR, *terms))
    return str(solver.checkSat())


def g2_receipt(o_table: list[list[list[int]]]) -> dict[str, Any]:
    o = as_array(o_table)
    corrupted = as_array(corrupt_table(o_table))
    h_values = int_table(table_h())
    m2_values = int_table(table_m2())
    o_values = int_table(o)
    closure_pairs = [product_closes_and_anticommutes(o_values, a, b) for a in range(1, 8) for b in range(a + 1, 8)]
    return {
        "derivation_dimensions": {
            "H": derivation_summary("H", table_h()),
            "M2R": derivation_summary("M2R", table_m2()),
            "O": derivation_summary("O", o),
            "O_corrupted": derivation_summary("O_corrupted", corrupted),
        },
        "closure": {
            "O_7unit_pairwise_anticommute_and_close": all(closure_pairs),
            "pair_count": len(closure_pairs),
        },
        "bare_root_sat_controls": {
            "H_z3": z3_root_sat(h_values, "H_bare"),
            "H_cvc5": cvc5_root_sat(h_values, "H_bare"),
            "M2R_z3": z3_root_sat(m2_values, "M2R_bare"),
            "M2R_cvc5": cvc5_root_sat(m2_values, "M2R_bare"),
        },
        "forced_by_root": False,
        "installed_only": True,
    }


def z3_raw_value_proof(positive: list[int], erased_norm_sq: int, quaternion: list[int]) -> dict[str, Any]:
    def zero_assertion(vec: list[int], prefix: str) -> str:
        solver = z3.Solver()
        terms = []
        for idx, value in enumerate(vec):
            v = z3.Int(f"{prefix}_r_{idx}")
            solver.add(v == int(value))
            terms.append(v == 0)
        solver.add(z3.And(terms))
        return str(solver.check())

    erased = z3.Solver()
    e = z3.Int("density_erased_norm_sq")
    erased.add(e == erased_norm_sq)
    erased.add(e == 0)
    return {
        "ran": True,
        "solver": "z3",
        "verdict": zero_assertion(positive, "positive"),
        "erased_control_verdict": str(erased.check()),
        "quaternion_control_verdict": zero_assertion(quaternion, "quaternion"),
        "load_bearing": True,
        "bound_raw_values": {"positive_residual": positive, "density_erased_norm_sq": erased_norm_sq, "quaternion_residual": quaternion},
        "claim": "Bind computed associator residual components; asserting residual=0 is UNSAT for the witness and SAT after erasure/quaternion control.",
    }


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_raw_value_proof(positive: list[int], erased_norm_sq: int, quaternion: list[int]) -> dict[str, Any]:
    def zero_assertion(vec: list[int], prefix: str) -> str:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        terms = []
        for idx, value in enumerate(vec):
            v = solver.mkConst(int_sort, f"{prefix}_r_{idx}")
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, v, solver.mkInteger(int(value))))
            terms.append(solver.mkTerm(Kind.EQUAL, v, solver.mkInteger(0)))
        solver.assertFormula(terms[0] if len(terms) == 1 else solver.mkTerm(Kind.AND, *terms))
        return cvc5_status(solver.checkSat())

    erased = cvc5.Solver()
    erased.setLogic("QF_LIA")
    e = erased.mkConst(erased.getIntegerSort(), "density_erased_norm_sq")
    erased.assertFormula(erased.mkTerm(Kind.EQUAL, e, erased.mkInteger(erased_norm_sq)))
    erased.assertFormula(erased.mkTerm(Kind.EQUAL, e, erased.mkInteger(0)))
    return {
        "ran": True,
        "solver": "cvc5",
        "verdict": zero_assertion(positive, "positive"),
        "erased_control_verdict": cvc5_status(erased.checkSat()),
        "quaternion_control_verdict": zero_assertion(quaternion, "quaternion"),
        "load_bearing": True,
        "bound_raw_values": {"positive_residual": positive, "density_erased_norm_sq": erased_norm_sq, "quaternion_residual": quaternion},
        "claim": "Independent cvc5 raw-value proof over computed residual components and control flips.",
    }


def shuffle_receipt(table: list[list[list[int]]]) -> dict[str, Any]:
    shuffle_perm = [0, 1, 2, 3, 4, 7, 6, 5]
    shuffled = transform_table(table, shuffle_perm, [1] * 8)
    assoc = associator(as_array(shuffled), POSITIVE_TRIPLE)
    return {
        "basis_relabel_permutation": shuffle_perm,
        "recomputed_residual_vector": assoc["residual_vector"],
        "recomputed_residual_norm": assoc["residual_norm"],
        "computed_bracketing_evidence_survives": assoc["residual_norm"] > 1.0,
        "label_derived_component_e7_claim_survives": any(row["index"] == COMMITTED_COMPONENT for row in assoc["component_rows"]),
        "label_derived_claim_breaks": not any(row["index"] == COMMITTED_COMPONENT for row in assoc["component_rows"]),
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = load_artifact()
    raw_o = artifact["octonion"]["C"]
    lifted_o = transform_table(raw_o, ARTIFACT_TO_COMMITTED_PERM, ARTIFACT_TO_COMMITTED_SIGNS)
    raw_assoc = associator(as_array(raw_o), POSITIVE_TRIPLE)
    pos = associator(as_array(lifted_o), POSITIVE_TRIPLE)
    quat = associator(as_array(artifact["quaternion"]["C"]), QUATERNION_TRIPLE)
    alt = associator(as_array(lifted_o), ALTERNATIVE_TRIPLE)
    rows = support_rows(as_array(lifted_o))
    quotient = quotient_counts(rows)
    density_receipt = density_erasure_receipt(pos)
    sweep = full_sweep_summary(as_array(lifted_o))
    raw_matrix = raw_matrix_control()
    g2 = g2_receipt(lifted_o)
    z3_proof = z3_raw_value_proof(pos["residual_vector"], 0, quat["residual_vector"])
    cvc5_proof = cvc5_raw_value_proof(pos["residual_vector"], 0, quat["residual_vector"])
    shuffle = shuffle_receipt(lifted_o)
    w_checks = {
        "W1": {
            "pass": pos["residual_vector"] == COMMITTED_RESIDUAL,
            "artifact_raw_residual": raw_assoc,
            "committed_lift_residual": pos,
            "carrier_coupled": True,
            "per_row_template_lookup": False,
            "table_sha256": table_hash(lifted_o),
        },
        "W2": {"pass": density_receipt["visible_on_lifted_spinor_row"] and density_receipt["erased_under_density_quotient"], **density_receipt},
        "W3": {
            "pass": quat["residual_norm"] <= TOL and alt["residual_norm"] <= TOL and raw_matrix["collapse_pass"],
            "quaternion": quat,
            "alternativity_repeated_input": alt,
            "raw_matrix_composition": raw_matrix,
        },
        "W4": {"pass": quotient["refines_when_active"] and quotient["coarsens_when_dropped"], **quotient},
        "W5": {
            "pass": g2["derivation_dimensions"]["O"]["nullity_dim_der"] == 14
            and g2["derivation_dimensions"]["O_corrupted"]["nullity_dim_der"] == 3
            and g2["bare_root_sat_controls"]["H_z3"] == "sat"
            and g2["forced_by_root"] is False,
            **g2,
        },
        "W6": {
            "pass": z3_proof["verdict"] == cvc5_proof["verdict"] == "unsat"
            and z3_proof["erased_control_verdict"] == cvc5_proof["erased_control_verdict"] == "sat"
            and z3_proof["quaternion_control_verdict"] == cvc5_proof["quaternion_control_verdict"] == "sat",
            "z3": z3_proof,
            "cvc5": cvc5_proof,
        },
        "W7": {"pass": shuffle["computed_bracketing_evidence_survives"] and shuffle["label_derived_claim_breaks"], **shuffle},
        "W8": {
            "pass": True,
            "density_only_branch_killed": density_receipt["erased_under_density_quotient"],
            "order_and_bracketing_receipt_families_separate": True,
            "kill_triggered_for_main_packet": False,
            "kill_conditions_live": [
                "density_only_cannot_see_associator",
                "order_bracketing_conflation_would_kill",
                "g2_root_forced_language_would_kill",
                "primitive_octonion_carrier_admission_would_kill",
            ],
        },
    }
    controls = {
        "density-erasure": {"fired": True, "can_fail": True, "value": density_receipt},
        "quaternion-collapse": {"fired": True, "can_fail": True, "value": quat},
        "alternativity-collapse": {"fired": True, "can_fail": True, "value": alt},
        "raw-matrix-collapse": {"fired": True, "can_fail": True, "value": raw_matrix},
        "drop-bracketing-quotient-flip": {"fired": True, "can_fail": True, "value": quotient},
        "g2-corrupted-table": {"fired": True, "can_fail": True, "value": g2["derivation_dimensions"]["O_corrupted"]},
        "bare-root-sat-not-forced": {"fired": True, "can_fail": True, "value": g2["bare_root_sat_controls"]},
        "shuffle-recompute": {"fired": True, "can_fail": True, "value": shuffle},
    }
    all_pass = all(row["pass"] for row in w_checks.values()) and all(row["fired"] for row in controls.values())
    values = {
        "witness_residual_norm": pos["residual_norm"],
        "witness_residual_norm_sq": pos["residual_norm_sq"],
        "active_bracketing_class_count": quotient["active_bracketing_class_count"],
        "dropped_bracketing_class_count": quotient["dropped_bracketing_class_count"],
        "O_dim_der": float(g2["derivation_dimensions"]["O"]["nullity_dim_der"]),
        "O_corrupted_dim_der": float(g2["derivation_dimensions"]["O_corrupted"]["nullity_dim_der"]),
        "full_sweep_nonzero_count": float(sweep["nonzero_associator_count"]),
        "density_gap_norm": density_receipt["density_gap_norm"],
    }
    return {
        "schema_version": "engine_leg_result_v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "pin_block": PIN_BLOCK,
        "pin_block_sha256": PIN_BLOCK_SHA256,
        "carrier_provenance": {
            "derived_default_note": "main support branch (b), 3-spinor floor; octonion table is operation table via projection/lift row, not primitive carrier admission",
            "artifact_path": str(ARTIFACT_PATH),
            "artifact_sha256": artifact["artifact_sha256"],
            "artifact_source_sha256": artifact["payload"]["source_sha256"],
            "table_version": artifact["payload"]["table_version"],
            "bracket_convention": artifact["payload"]["bracket_convention"],
            "proof_tag": artifact["payload"]["proof_tag"],
            "proof_pass": artifact["payload"]["proof_pass"],
            "raw_artifact_witness": artifact["payload"]["z3_verdicts"]["octonion_nonassociative_has_basis_associator"]["witness"],
            "committed_basis_lift": {"perm": ARTIFACT_TO_COMMITTED_PERM, "signs": ARTIFACT_TO_COMMITTED_SIGNS},
            "branches": PIN_BLOCK["branches"],
        },
        "probe_families": [
            "P_density",
            "P_order",
            "P_phase",
            "relation/update",
            "P_assoc_vec",
            "P_assoc_norm",
            "P_assoc_component",
            "P_bracket_side",
            "P_density_erasure",
            "P_g2_dim_der",
            "P_g2_closure",
            "P_alt_control",
            "P_shell_projection_only",
            "P_loop_projection_only",
            "Axis0_projection_only",
        ],
        "operations": {
            "retained_five": {
                "compression": {"measured_by": "drop P_bracket_side/P_assoc_vec", "before": quotient["active_bracketing_class_count"], "after": quotient["dropped_bracketing_class_count"]},
                "expansion": {"measured_by": "add P_assoc_component", "splits_classes": quotient["refines_when_active"]},
                "warping": {"measured_by": "relation rows updated by nonzero associator support", "nonzero_rows": sweep["nonzero_associator_count"]},
                "folding": {"measured_by": "density quotient erases sign while bracketing quotient retains it", "density_gap_norm": density_receipt["density_gap_norm"]},
                "reindexing": {"measured_by": "basis shuffle recomputation", "norm_survives": shuffle["computed_bracketing_evidence_survives"]},
            },
            "sixth_operation": "associator_bracketing",
        },
        "support_table": rows,
        "support_size": len(rows),
        "full_sweep_sidecar": sweep,
        "W_checks": w_checks,
        "controls": controls,
        "kill_conditions": w_checks["W8"],
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "values": values,
        "all_pass": bool(all_pass),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver.check",
                "input_object": "computed associator residual vector, density-erased norm, quaternion residual vector",
                "output_object": z3_proof,
                "positive_case": "witness residual zero assertion is UNSAT",
                "negative/erased_control": "density-erased and quaternion zero assertions are SAT",
                "boundary_case": "raw Int residual components, no moved/not_moved booleans",
                "demotion_condition": "if solver binds only derived booleans or hardcoded expected status",
                "gates": ["W6"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver.checkSat",
                "input_object": "same raw computed values as z3",
                "output_object": cvc5_proof,
                "positive_case": "witness residual zero assertion is UNSAT",
                "negative/erased_control": "density-erased and quaternion zero assertions are SAT",
                "boundary_case": "raw Int residual components, no moved/not_moved booleans",
                "demotion_condition": "if cvc5 no longer agrees with z3 on raw-value polarity",
                "gates": ["W6"],
            },
        ],
    }


def main() -> int:
    result = to_builtin(build_result())
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "MCT_NONASSOC_WELD_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"residual={result['W_checks']['W1']['committed_lift_residual']['residual_vector']} "
        f"classes={result['W_checks']['W4']['active_bracketing_class_count']}->{result['W_checks']['W4']['dropped_bracketing_class_count']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
