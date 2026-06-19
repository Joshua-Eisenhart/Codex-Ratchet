#!/usr/bin/env python3
"""JAX + z3/cvc5 leg for M(C) v1 finite admissibility object.

This leg builds the finite object locally from the canon algebra artifact.
The SMT checks derive F01/N01/bracketing flips from bound support indices,
matrix entries, and structure constants; they do not re-check precomputed
booleans.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
from cvc5 import Kind
import jax.numpy as jnp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_mc_v1_admissibility_object"
OBJECT_ID = "foundation_mc_v1_admissibility_object_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_mc_v1_admissibility_object_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_jax_results.json"
ARTIFACT_PATH = ROOT / "system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json"
ARTIFACT_RECEIPT_PATH = ROOT / "system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json"
TOL = 1.0e-10

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 finite density/probe, quotient, order-gap, and octonion readout construction",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing array contractions over density matrices and canon structure constants",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing in-solver derivation of F01/N01/bracketing negative-control flips from bound entries",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent derivation of the same F01/N01/bracketing flips",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON, hashing, paths, and timestamps",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def rounded(value: Any, digits: int = 12) -> float:
    return round(py_float(value), digits)


def load_artifact() -> tuple[dict[str, Any], dict[str, Any], jax.Array]:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    receipt = json.loads(ARTIFACT_RECEIPT_PATH.read_text(encoding="utf-8"))
    octonion = next(row for row in artifact["algebras"] if row["algebra"] == "octonion")
    table = jnp.asarray(octonion["C"], dtype=jnp.int64)
    return artifact, receipt, table


def mat(rows: list[list[float]]) -> jax.Array:
    return jnp.asarray(rows, dtype=jnp.float64)


P_Z0 = mat([[1.0, 0.0], [0.0, 0.0]])
P_Z1 = mat([[0.0, 0.0], [0.0, 1.0]])
P_XPLUS = mat([[0.5, 0.5], [0.5, 0.5]])
PROBES = {"P_z0": P_Z0, "P_z1": P_Z1, "P_xplus": P_XPLUS}


def rho_from_key(key: str) -> jax.Array:
    rows = {
        "rho_z0": [[1.0, 0.0], [0.0, 0.0]],
        "rho_z1": [[0.0, 0.0], [0.0, 1.0]],
        "rho_xplus": [[0.5, 0.5], [0.5, 0.5]],
        "rho_mixed": [[0.5, 0.0], [0.0, 0.5]],
        "rho_bad_trace": [[0.6, 0.0], [0.0, 0.6]],
        "rho_bad_psd": [[0.5, 0.6], [0.6, 0.5]],
    }
    return mat(rows[key])


def support_spec(nonassoc_triple: list[int], assoc_triple: list[int]) -> list[dict[str, Any]]:
    return [
        {"id": "s_z0_oct_left", "rho": "rho_z0", "triple": nonassoc_triple, "bracket": "left", "support_index": 0, "bounded_witness": True, "composition": ["Z", "X"]},
        {"id": "s_z0_oct_right", "rho": "rho_z0", "triple": nonassoc_triple, "bracket": "right", "support_index": 1, "bounded_witness": True, "composition": ["Z", "X"]},
        {"id": "s_z1_oct_left", "rho": "rho_z1", "triple": nonassoc_triple, "bracket": "left", "support_index": 2, "bounded_witness": True, "composition": ["Z", "X"]},
        {"id": "s_xplus_oct_left", "rho": "rho_xplus", "triple": nonassoc_triple, "bracket": "left", "support_index": 3, "bounded_witness": True, "composition": ["Z", "X"]},
        {"id": "s_bad_trace_oct_left", "rho": "rho_bad_trace", "triple": nonassoc_triple, "bracket": "left", "support_index": 4, "bounded_witness": True, "composition": ["Z", "X"]},
        {"id": "s_bad_psd_oct_left", "rho": "rho_bad_psd", "triple": nonassoc_triple, "bracket": "left", "support_index": 5, "bounded_witness": True, "composition": ["Z", "X"]},
        {"id": "s_bad_f01_unbounded_witness", "rho": "rho_z0", "triple": nonassoc_triple, "bracket": "left", "support_index": 99, "bounded_witness": False, "composition": ["Z", "X"]},
        {"id": "s_commuting_control", "rho": "rho_z0", "triple": nonassoc_triple, "bracket": "left", "support_index": 7, "bounded_witness": True, "composition": ["Z", "Z"]},
        {"id": "s_associative_bracket_control", "rho": "rho_z0", "triple": assoc_triple, "bracket": "left", "support_index": 8, "bounded_witness": True, "composition": ["Z", "X"]},
    ]


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("kab,a,b->k", table, x, y)


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.int64)[idx]


def bracket_readouts(table: jax.Array, triple: list[int]) -> dict[str, Any]:
    x, y, z = [basis(int(table.shape[0]), idx) for idx in triple]
    left = multiply(table, multiply(table, x, y), z)
    right = multiply(table, x, multiply(table, y, z))
    assoc = left - right
    return {
        "left": [int(v) for v in jax.device_get(left).tolist()],
        "right": [int(v) for v in jax.device_get(right).tolist()],
        "associator": [int(v) for v in jax.device_get(assoc).tolist()],
        "associator_norm": rounded(jnp.linalg.norm(assoc.astype(jnp.float64)), 12),
        "nonzero_components": int(jax.device_get(jnp.count_nonzero(assoc))),
    }


def find_nonassoc_triple(table: jax.Array) -> list[int]:
    dim = int(table.shape[0])
    for a in range(1, dim):
        for b in range(1, dim):
            for c in range(1, dim):
                if bracket_readouts(table, [a, b, c])["associator_norm"] > TOL:
                    return [a, b, c]
    raise RuntimeError("no octonion nonassociative triple found")


def measurement_stats(rho: jax.Array) -> dict[str, float]:
    return {name: rounded(jnp.trace(probe @ rho), 12) for name, probe in PROBES.items()}


def seq_prob(rho: jax.Array, first: jax.Array, second: jax.Array) -> float:
    return rounded(jnp.trace(second @ first @ rho @ first), 12)


def order_report(rho: jax.Array, composition: list[str]) -> dict[str, Any]:
    first = P_Z0 if composition[0] == "Z" else P_XPLUS
    second = P_Z0 if composition[1] == "Z" else P_XPLUS
    reverse_first = second
    reverse_second = first
    forward = seq_prob(rho, first, second)
    reverse = seq_prob(rho, reverse_first, reverse_second)
    return {
        "composition": composition,
        "forward_probability": forward,
        "reverse_probability": reverse,
        "order_gap": round(abs(forward - reverse), 12),
        "AB_not_BA_witness": abs(forward - reverse) > TOL,
    }


def density_checks(rho: jax.Array, stats: dict[str, float]) -> dict[str, Any]:
    trace = rounded(jnp.trace(rho), 12)
    hermitian_residual = rounded(jnp.max(jnp.abs(rho - rho.T)), 12)
    evals = jnp.linalg.eigvalsh((rho + rho.T) / 2.0)
    min_eval = rounded(jnp.min(evals), 12)
    return {
        "trace": trace,
        "trace_eq_1": abs(trace - 1.0) <= TOL,
        "hermitian_residual": hermitian_residual,
        "hermitian": hermitian_residual <= TOL,
        "psd_min_eigenvalue": min_eval,
        "psd": min_eval >= -TOL,
        "probe_bounds": all(-TOL <= value <= 1.0 + TOL for value in stats.values()),
    }


def entropy_from_z(stats: dict[str, float]) -> float:
    out = 0.0
    for p in (stats["P_z0"], stats["P_z1"]):
        if p > TOL:
            out -= p * float(jax.device_get(jnp.log2(jnp.asarray(p, dtype=jnp.float64))))
    return round(out, 12)


def record_for(spec: dict[str, Any], table: jax.Array, support_size: int) -> dict[str, Any]:
    rho = rho_from_key(spec["rho"])
    stats = measurement_stats(rho)
    density = density_checks(rho, stats)
    order = order_report(rho, spec["composition"])
    bracket = bracket_readouts(table, spec["triple"])
    f01_ok = bool(spec["bounded_witness"] and 0 <= int(spec["support_index"]) < support_size)
    n01_ok = bool(order["AB_not_BA_witness"])
    bracketing_ok = bracket["associator_norm"] > TOL
    carrier_ok = bracketing_ok and bracket["nonzero_components"] > 0
    admitted = bool(
        density["trace_eq_1"]
        and density["hermitian"]
        and density["psd"]
        and density["probe_bounds"]
        and f01_ok
        and n01_ok
        and bracketing_ok
        and carrier_ok
    )
    readout = bracket[spec["bracket"]]
    full_probe_key = {
        "density": stats,
        "f01": {"bounded_witness": f01_ok, "support_index": int(spec["support_index"])},
        "n01": {"composition": spec["composition"], "order_gap": order["order_gap"]},
        "bracketing": {"label": spec["bracket"], "readout": readout, "associator_norm": bracket["associator_norm"]},
        "carrier": {"octonion_nonzero_components": bracket["nonzero_components"], "cl6_dim": 64},
        "axes": {
            "A_entropy_bits": entropy_from_z(stats),
            "A_order_gap": order["order_gap"],
            "A_associator_norm": bracket["associator_norm"],
        },
    }
    return {
        "id": spec["id"],
        "rho_key": spec["rho"],
        "support_index": spec["support_index"],
        "bounded_witness": spec["bounded_witness"],
        "triple": spec["triple"],
        "bracketing": spec["bracket"],
        "density": density,
        "probe_values": stats,
        "composition": order,
        "bracketing_readout": bracket,
        "carrier_readout": {"selected": readout, "octonion": bracket, "cl6_surface": {"target": "Cl(6)", "dimension": 64, "even_subalgebra_dimension": 32}},
        "constraint_flags": {
            "density_probe_C": density["trace_eq_1"] and density["hermitian"] and density["psd"] and density["probe_bounds"],
            "F01": f01_ok,
            "N01": n01_ok,
            "bracketing": bracketing_ok,
            "carrier": carrier_ok,
        },
        "admitted_under_Adm_C": admitted,
        "rejection_reasons": [
            name
            for name, ok in [
                ("trace=1", density["trace_eq_1"]),
                ("Hermitian", density["hermitian"]),
                ("PSD", density["psd"]),
                ("probe_bounds", density["probe_bounds"]),
                ("F01", f01_ok),
                ("N01", n01_ok),
                ("bracketing_nonassociative", bracketing_ok),
                ("carrier_readout", carrier_ok),
            ]
            if not ok
        ],
        "full_probe_key": full_probe_key,
    }


def quotient(records: list[dict[str, Any]], *, admitted_only: bool, key_mode: str = "full") -> dict[str, Any]:
    selected = [row for row in records if row["admitted_under_Adm_C"] or not admitted_only]
    classes: dict[str, dict[str, Any]] = {}
    for row in selected:
        key_obj = row["full_probe_key"]
        if key_mode == "drop_bracketing":
            key_obj = {k: v for k, v in key_obj.items() if k not in {"bracketing", "carrier"}}
        elif key_mode == "label_shuffle":
            shuffled = json.loads(json.dumps(key_obj))
            shuffled["density"] = {
                "P_z1": key_obj["density"]["P_z0"],
                "P_z0": key_obj["density"]["P_z1"],
                "P_xplus": key_obj["density"]["P_xplus"],
            }
            key_obj = shuffled
        elif key_mode == "carrier_erasure":
            erased = json.loads(json.dumps(key_obj))
            erased["bracketing"] = {"label": "erased", "readout": [0] * 8, "associator_norm": 0.0}
            erased["carrier"] = {"octonion_nonzero_components": 0, "cl6_dim": 0}
            key_obj = erased
        key = json.dumps(key_obj, sort_keys=True, separators=(",", ":"))
        classes.setdefault(key, {"members": [], "key": key_obj})["members"].append(row["id"])
    ordered = [
        {"class_id": f"{'Adm' if admitted_only else 'S'}_q{idx}", "members": sorted(value["members"]), "key": value["key"]}
        for idx, (_, value) in enumerate(sorted(classes.items()))
    ]
    return {
        "admitted_only": admitted_only,
        "key_mode": key_mode,
        "class_count": len(ordered),
        "classes": ordered,
        "partition_member_ids": sorted(member for cls in ordered for member in cls["members"]),
        "signature_sha256": hashlib.sha256(json.dumps(ordered, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
    }


def apply_control(records: list[dict[str, Any]], control: str) -> tuple[list[dict[str, Any]], str]:
    mutated = json.loads(json.dumps(records))
    key_mode = "full"
    for row in mutated:
        flags = row["constraint_flags"]
        if control == "drop_F01":
            flags["F01"] = True
        elif control == "drop_N01":
            flags["N01"] = True
        elif control == "drop_bracketing":
            flags["bracketing"] = True
            key_mode = "drop_bracketing"
        elif control == "carrier_erasure":
            flags["carrier"] = False
            row["full_probe_key"]["carrier"] = {"octonion_nonzero_components": 0, "cl6_dim": 0}
            row["full_probe_key"]["bracketing"] = {"label": "erased", "readout": [0] * 8, "associator_norm": 0.0}
            key_mode = "carrier_erasure"
        elif control == "commuting":
            flags["N01"] = False
            row["full_probe_key"]["n01"]["composition"] = ["Z", "Z"]
            row["full_probe_key"]["n01"]["order_gap"] = 0.0
        elif control == "associative":
            flags["bracketing"] = False
            row["full_probe_key"]["bracketing"]["associator_norm"] = 0.0
            row["full_probe_key"]["bracketing"]["readout"] = [0] * 8
        elif control == "label_shuffle":
            key_mode = "label_shuffle"
        else:
            raise ValueError(control)
        density_ok = bool(flags["density_probe_C"])
        row["admitted_under_Adm_C"] = bool(density_ok and flags["F01"] and flags["N01"] and flags["bracketing"] and flags["carrier"])
    return mutated, key_mode


def control_report(records: list[dict[str, Any]], q_adm: dict[str, Any]) -> dict[str, Any]:
    baseline_admitted = sorted(row["id"] for row in records if row["admitted_under_Adm_C"])
    controls: dict[str, Any] = {}
    for name in ["drop_F01", "drop_N01", "drop_bracketing", "label_shuffle", "carrier_erasure", "commuting", "associative"]:
        mutated, key_mode = apply_control(records, name)
        q_mut = quotient(mutated, admitted_only=True, key_mode=key_mode)
        admitted = sorted(row["id"] for row in mutated if row["admitted_under_Adm_C"])
        controls[name] = {
            "admitted_before": baseline_admitted,
            "admitted_after": admitted,
            "admitted_changed": admitted != baseline_admitted,
            "quotient_class_count_before": q_adm["class_count"],
            "quotient_class_count_after": q_mut["class_count"],
            "quotient_signature_before": q_adm["signature_sha256"],
            "quotient_signature_after": q_mut["signature_sha256"],
            "quotient_changed": q_mut["signature_sha256"] != q_adm["signature_sha256"],
            "flips_value_coupled": (admitted != baseline_admitted) or (q_mut["signature_sha256"] != q_adm["signature_sha256"]),
        }
    return controls


def z3_f01_derivation(support_size: int) -> dict[str, Any]:
    idx = z3.Int("support_index")
    solver = z3.Solver()
    solver.add(idx == 99)
    solver.add(idx >= 0, idx < support_size)
    full = solver.check()
    drop = z3.Solver()
    drop.add(idx == 99)
    dropped = drop.check()
    return {"verdict": str(full), "drop_F01_verdict": str(dropped), "derived_in_solver": True, "bound_entries": {"support_index": 99, "support_size": support_size}}


def z3_matmul(a: list[list[z3.ArithRef]], b: list[list[z3.ArithRef]]) -> list[list[z3.ArithRef]]:
    return [[z3.Sum([a[i][k] * b[k][j] for k in range(2)]) for j in range(2)] for i in range(2)]


def z3_seq_expr(rho_vals: list[list[str]], first_vals: list[list[str]], second_vals: list[list[str]]) -> z3.ArithRef:
    rho = [[z3.Real(f"rho_{i}_{j}") for j in range(2)] for i in range(2)]
    first = [[z3.Real(f"first_{i}_{j}") for j in range(2)] for i in range(2)]
    second = [[z3.Real(f"second_{i}_{j}") for j in range(2)] for i in range(2)]
    constraints = []
    for i in range(2):
        for j in range(2):
            constraints.extend([rho[i][j] == z3.RealVal(rho_vals[i][j]), first[i][j] == z3.RealVal(first_vals[i][j]), second[i][j] == z3.RealVal(second_vals[i][j])])
    prod = z3_matmul(z3_matmul(z3_matmul(second, first), rho), first)
    return z3.Sum([prod[i][i] for i in range(2)]), constraints


def z3_n01_derivation() -> dict[str, Any]:
    rho = [["1", "0"], ["0", "0"]]
    pz = [["1", "0"], ["0", "0"]]
    px = [["1/2", "1/2"], ["1/2", "1/2"]]
    zx, c1 = z3_seq_expr(rho, pz, px)
    xz, c2 = z3_seq_expr(rho, px, pz)
    solver = z3.Solver()
    solver.add(*(c1 + c2))
    solver.add(zx == xz)
    full = solver.check()
    zz1, cz1 = z3_seq_expr(rho, pz, pz)
    zz2, cz2 = z3_seq_expr(rho, pz, pz)
    comm = z3.Solver()
    comm.add(*(cz1 + cz2))
    comm.add(zz1 == zz2)
    control = comm.check()
    return {"verdict": str(full), "commuting_control_verdict": str(control), "derived_expression": "Tr(B*A*rho*A) == Tr(A*B*rho*B) from bound rho/projector entries", "derived_in_solver": True}


def int_table_values(table: jax.Array) -> list[list[list[int]]]:
    host = jax.device_get(table)
    return [[[int(host[k, i, j]) for j in range(host.shape[2])] for i in range(host.shape[1])] for k in range(host.shape[0])]


def z3_bracket_expr(cvars: list[list[list[z3.ArithRef]]], triple: list[int], dim: int) -> list[z3.ArithRef]:
    a, b, c = triple
    left = []
    right = []
    for k in range(dim):
        left.append(z3.Sum([cvars[m][a][b] * cvars[k][m][c] for m in range(dim)]))
        right.append(z3.Sum([cvars[m][b][c] * cvars[k][a][m] for m in range(dim)]))
    return [left[k] - right[k] for k in range(dim)]


def z3_bracketing_derivation(table: jax.Array, triple: list[int], assoc_triple: list[int]) -> dict[str, Any]:
    values = int_table_values(table)
    dim = len(values)
    solver = z3.Solver()
    cvars = [[[z3.Int(f"c_{k}_{i}_{j}") for j in range(dim)] for i in range(dim)] for k in range(dim)]
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                solver.add(cvars[k][i][j] == values[k][i][j])
    assoc = z3_bracket_expr(cvars, triple, dim)
    for expr in assoc:
        solver.add(expr == 0)
    full = solver.check()
    ctl = z3.Solver()
    cctl = [[[z3.Int(f"ac_{k}_{i}_{j}") for j in range(dim)] for i in range(dim)] for k in range(dim)]
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                ctl.add(cctl[k][i][j] == values[k][i][j])
    assoc_ctl = z3_bracket_expr(cctl, assoc_triple, dim)
    for expr in assoc_ctl:
        ctl.add(expr == 0)
    control = ctl.check()
    return {"verdict": str(full), "associative_control_verdict": str(control), "derived_expression": "sum_m C[m,a,b]*C[k,m,c] - sum_m C[m,b,c]*C[k,a,m]", "bound_structure_constants": dim * dim * dim, "derived_in_solver": True}


def cvc5_real(solver: cvc5.Solver, value: str) -> Any:
    return solver.mkReal(value)


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(int(value))


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_add(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return cvc5_int(solver, 0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def cvc5_f01_derivation(support_size: int) -> dict[str, Any]:
    solver = cvc5.Solver()
    integer = solver.getIntegerSort()
    idx = solver.mkConst(integer, "support_index")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, idx, cvc5_int(solver, 99)))
    solver.assertFormula(solver.mkTerm(Kind.GEQ, idx, cvc5_int(solver, 0)))
    solver.assertFormula(solver.mkTerm(Kind.LT, idx, cvc5_int(solver, support_size)))
    full = solver.checkSat()
    drop = cvc5.Solver()
    integer2 = drop.getIntegerSort()
    idx2 = drop.mkConst(integer2, "support_index")
    drop.assertFormula(drop.mkTerm(Kind.EQUAL, idx2, cvc5_int(drop, 99)))
    dropped = drop.checkSat()
    return {"verdict": cvc5_status(full), "drop_F01_verdict": cvc5_status(dropped), "derived_in_solver": True, "bound_entries": {"support_index": 99, "support_size": support_size}}


def cvc5_matmul(solver: cvc5.Solver, a: list[list[Any]], b: list[list[Any]]) -> list[list[Any]]:
    return [[cvc5_add(solver, [solver.mkTerm(Kind.MULT, a[i][k], b[k][j]) for k in range(2)]) for j in range(2)] for i in range(2)]


def cvc5_seq_expr(solver: cvc5.Solver, rho_vals: list[list[str]], first_vals: list[list[str]], second_vals: list[list[str]], prefix: str) -> Any:
    real = solver.getRealSort()
    rho = [[solver.mkConst(real, f"{prefix}_rho_{i}_{j}") for j in range(2)] for i in range(2)]
    first = [[solver.mkConst(real, f"{prefix}_first_{i}_{j}") for j in range(2)] for i in range(2)]
    second = [[solver.mkConst(real, f"{prefix}_second_{i}_{j}") for j in range(2)] for i in range(2)]
    for i in range(2):
        for j in range(2):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, rho[i][j], cvc5_real(solver, rho_vals[i][j])))
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, first[i][j], cvc5_real(solver, first_vals[i][j])))
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, second[i][j], cvc5_real(solver, second_vals[i][j])))
    prod = cvc5_matmul(solver, cvc5_matmul(solver, cvc5_matmul(solver, second, first), rho), first)
    return cvc5_add(solver, [prod[i][i] for i in range(2)])


def cvc5_n01_derivation() -> dict[str, Any]:
    rho = [["1", "0"], ["0", "0"]]
    pz = [["1", "0"], ["0", "0"]]
    px = [["1/2", "1/2"], ["1/2", "1/2"]]
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    zx = cvc5_seq_expr(solver, rho, pz, px, "zx")
    xz = cvc5_seq_expr(solver, rho, px, pz, "xz")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, zx, xz))
    full = solver.checkSat()
    comm = cvc5.Solver()
    comm.setLogic("QF_NRA")
    zz1 = cvc5_seq_expr(comm, rho, pz, pz, "zz1")
    zz2 = cvc5_seq_expr(comm, rho, pz, pz, "zz2")
    comm.assertFormula(comm.mkTerm(Kind.EQUAL, zz1, zz2))
    control = comm.checkSat()
    return {"verdict": cvc5_status(full), "commuting_control_verdict": cvc5_status(control), "derived_expression": "Tr(B*A*rho*A) == Tr(A*B*rho*B) from bound rho/projector entries", "derived_in_solver": True}


def cvc5_bracket_expr(solver: cvc5.Solver, cvars: list[list[list[Any]]], triple: list[int], dim: int) -> list[Any]:
    a, b, c = triple
    out = []
    for k in range(dim):
        left = cvc5_add(solver, [solver.mkTerm(Kind.MULT, cvars[m][a][b], cvars[k][m][c]) for m in range(dim)])
        right = cvc5_add(solver, [solver.mkTerm(Kind.MULT, cvars[m][b][c], cvars[k][a][m]) for m in range(dim)])
        out.append(solver.mkTerm(Kind.SUB, left, right))
    return out


def cvc5_bracketing_derivation(table: jax.Array, triple: list[int], assoc_triple: list[int]) -> dict[str, Any]:
    values = int_table_values(table)
    dim = len(values)
    solver = cvc5.Solver()
    solver.setLogic("QF_NIA")
    integer = solver.getIntegerSort()
    cvars = [[[solver.mkConst(integer, f"c_{k}_{i}_{j}") for j in range(dim)] for i in range(dim)] for k in range(dim)]
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, cvars[k][i][j], cvc5_int(solver, values[k][i][j])))
    for expr in cvc5_bracket_expr(solver, cvars, triple, dim):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, expr, cvc5_int(solver, 0)))
    full = solver.checkSat()
    ctl = cvc5.Solver()
    ctl.setLogic("QF_NIA")
    integer2 = ctl.getIntegerSort()
    cctl = [[[ctl.mkConst(integer2, f"ac_{k}_{i}_{j}") for j in range(dim)] for i in range(dim)] for k in range(dim)]
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                ctl.assertFormula(ctl.mkTerm(Kind.EQUAL, cctl[k][i][j], cvc5_int(ctl, values[k][i][j])))
    for expr in cvc5_bracket_expr(ctl, cctl, assoc_triple, dim):
        ctl.assertFormula(ctl.mkTerm(Kind.EQUAL, expr, cvc5_int(ctl, 0)))
    control = ctl.checkSat()
    return {"verdict": cvc5_status(full), "associative_control_verdict": cvc5_status(control), "derived_expression": "sum_m C[m,a,b]*C[k,m,c] - sum_m C[m,b,c]*C[k,a,m]", "bound_structure_constants": dim * dim * dim, "derived_in_solver": True}


def build_result() -> dict[str, Any]:
    artifact, receipt, table = load_artifact()
    nonassoc_triple = find_nonassoc_triple(table)
    assoc_triple = [1, 2, 3]
    specs = support_spec(nonassoc_triple, assoc_triple)
    records = [record_for(spec, table, len(specs)) for spec in specs]
    q_s = quotient(records, admitted_only=False)
    q_adm = quotient(records, admitted_only=True)
    controls = control_report(records, q_adm)
    admitted = [row for row in records if row["admitted_under_Adm_C"]]
    axes_maps = {
        "A_entropy_bits": {row["id"]: row["full_probe_key"]["axes"]["A_entropy_bits"] for row in admitted},
        "A_order_gap": {row["id"]: row["full_probe_key"]["axes"]["A_order_gap"] for row in admitted},
        "A_associator_norm": {row["id"]: row["full_probe_key"]["axes"]["A_associator_norm"] for row in admitted},
    }
    z3_derivations = {
        "F01": z3_f01_derivation(len(specs)),
        "N01": z3_n01_derivation(),
        "bracketing": z3_bracketing_derivation(table, nonassoc_triple, assoc_triple),
    }
    cvc5_derivations = {
        "F01": cvc5_f01_derivation(len(specs)),
        "N01": cvc5_n01_derivation(),
        "bracketing": cvc5_bracketing_derivation(table, nonassoc_triple, assoc_triple),
    }
    smt_ok = (
        z3_derivations["F01"]["verdict"] == cvc5_derivations["F01"]["verdict"] == "unsat"
        and z3_derivations["F01"]["drop_F01_verdict"] == cvc5_derivations["F01"]["drop_F01_verdict"] == "sat"
        and z3_derivations["N01"]["verdict"] == cvc5_derivations["N01"]["verdict"] == "unsat"
        and z3_derivations["N01"]["commuting_control_verdict"] == cvc5_derivations["N01"]["commuting_control_verdict"] == "sat"
        and z3_derivations["bracketing"]["verdict"] == cvc5_derivations["bracketing"]["verdict"] == "unsat"
        and z3_derivations["bracketing"]["associative_control_verdict"] == cvc5_derivations["bracketing"]["associative_control_verdict"] == "sat"
    )
    controls_ok = all(row["flips_value_coupled"] for row in controls.values())
    field_coverage = {
        key: "present_in_object"
        for key in [
            "S",
            "C",
            "M/P",
            "~_M",
            "Adm_C",
            "composition",
            "bracketing",
            "local_path_rules",
            "carrier_readout_map",
            "axes_A_i",
            "controls",
            "receipts",
            "ceiling",
        ]
    }
    all_pass = bool(
        artifact.get("proof_pass") is True
        and receipt.get("proof_pass") is True
        and len(admitted) == 4
        and q_adm["class_count"] == 4
        and controls_ok
        and smt_ok
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "object_id": OBJECT_ID,
        "rung_id": RUNG_ID,
        "engine": "jax",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "ran": True,
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "python_executable": sys.executable,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "canon_runtime": {
            "artifact_path": str(ARTIFACT_PATH),
            "artifact_sha256": sha256_file(ARTIFACT_PATH),
            "receipt_path": str(ARTIFACT_RECEIPT_PATH),
            "receipt_artifact_sha256": receipt.get("artifact_sha256"),
            "proof_tag": artifact.get("proof_tag"),
            "proof_pass": artifact.get("proof_pass"),
            "table_version": artifact.get("table_version"),
            "bracket_convention": "left",
        },
        "field_coverage": field_coverage,
        "M_C_v1": {
            "S": {"size": len(records), "elements": records},
            "C": {
                "density_probe_constraints": ["trace=1", "Hermitian", "PSD", "0<=Tr(P rho)<=1 for P in finite M_density"],
                "F01": "bounded_witness=true and support_index in 0..|S|-1",
                "N01": "Z_then_X and X_then_Z sequential local paths have an explicit unequal probability witness",
                "composition_rules": ["sequential projective composition uses B*A*rho*A", "composition labels are local path labels inside S"],
                "bracketing_rules": ["octonion readout keeps ((a*b)*c) and (a*(b*c)) distinct", "global reassociation is forbidden"],
                "carrier_rules": ["consume canon algebra_structure_constants_v1 octonion C[k][i][j]", "map admitted records to octonion readout plus Cl(6) surface metadata"],
            },
            "M_over_P": {
                "P": ["density", "composition", "bracketing", "carrier", "axes"],
                "full_probe_family": ["P_z0", "P_z1", "P_xplus", "F01_support", "N01_order_gap", "octonion_left_right_readout", "Cl6_dim", "A_entropy_bits", "A_order_gap", "A_associator_norm"],
            },
            "quotient_S_mod_M": q_s,
            "quotient_Adm_C_mod_M": q_adm,
            "Adm_C_records": [{"id": row["id"], "admitted": row["admitted_under_Adm_C"], "rejection_reasons": row["rejection_reasons"]} for row in records],
            "composition": {"N01_witness": z3_derivations["N01"], "local_paths": ["Z_then_X", "X_then_Z", "Z_then_Z_control"]},
            "bracketing": {"witness_triple": nonassoc_triple, "associative_control_triple": assoc_triple, "in_quotient": True},
            "local_path_rules": {"allowed_paths": ["Z_then_X", "X_then_Z", "left_assoc", "right_assoc"], "forbidden": ["implicit_reassociation", "carrier_erasure"]},
            "carrier_readout_map": {row["id"]: row["carrier_readout"] for row in admitted},
            "axes_A_i": axes_maps,
            "controls": controls,
            "receipts": {"source_path": str(SOURCE_PATH), "source_sha256": sha256_file(SOURCE_PATH), "artifact_sha256": sha256_file(ARTIFACT_PATH)},
            "ceiling": {"classification": classification, "promotion_allowed": promotion_allowed, "formal_admission_allowed": formal_admission_allowed},
        },
        "smt_derivations": {"z3": z3_derivations, "cvc5": cvc5_derivations, "agreement": smt_ok},
        "negative_controls": controls,
        "summary": {
            "support_size": len(records),
            "admitted_count": len(admitted),
            "quotient_S_class_count": q_s["class_count"],
            "quotient_Adm_C_class_count": q_adm["class_count"],
            "nonassoc_witness_triple": nonassoc_triple,
            "controls_all_flip": controls_ok,
            "smt_all_derived_and_agree": smt_ok,
            "all_pass": all_pass,
        },
        "all_pass": all_pass,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = result["summary"]
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"admitted={summary['admitted_count']} "
        f"adm_classes={summary['quotient_Adm_C_class_count']} "
        f"controls_flip={str(summary['controls_all_flip']).lower()} "
        f"smt={str(summary['smt_all_derived_and_agree']).lower()} "
        f"reads_peer_result={str(result['reads_peer_result']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
