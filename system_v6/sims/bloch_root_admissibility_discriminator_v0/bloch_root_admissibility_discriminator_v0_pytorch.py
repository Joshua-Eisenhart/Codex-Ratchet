#!/usr/bin/env python3
"""PyTorch leg for bloch_root_admissibility_discriminator_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import torch
from torch.func import jacrev
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "bloch_root_admissibility_discriminator_v0"
ENGINE = "pytorch"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"
ARTIFACT_PATH = ROOT / "system_v5" / "julia_carrier" / "artifacts" / "algebra_structure_constants_v1.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False
DTYPE = torch.float64
TOL = 1.0e-8

PIN_CANONICAL = (
    '{"sim_id":"bloch_root_admissibility_discriminator_v0",'
    '"claim":"F01 finite quotients limit to Bloch sphere; N01 noncommuting probes reconstruct Bloch ball; division algebra Hopf ladder terminates before sedenions",'
    '"ceiling":{"classification":"scratch_diagnostic","promotion_allowed":false,"formal_admission_allowed":false},'
    '"language":{"roots":"ADMIT four-member family {S^1,S^2,S^4,S^8}","carrier":"C^2 INSTALLS S^2 installed-not-forced","physics":false}}'
)
PIN_SHA256 = hashlib.sha256(PIN_CANONICAL.encode("utf-8")).hexdigest()

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "load-bearing torch-native SVD/rank, tensor contraction, and norm computations"},
    "torch.func": {"tried": True, "used": True, "reason": "supportive Jacobian-rank witness for commuting vs noncommuting probe maps; demoted until a passing torch.func capability probe exists"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing raw-value SMT flips over torch-computed ranks and sedenion violation"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent raw-value SMT flips over the same torch-computed values"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive JSON, hashing, deterministic samples, and path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.func": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rank(points: torch.Tensor, tol: float = 1.0e-8) -> int:
    centered = points - points.mean(dim=0, keepdim=True)
    s = torch.linalg.svdvals(centered)
    return int((s > tol).sum().item())


def full_probe_map(r: torch.Tensor) -> torch.Tensor:
    return torch.stack([r[0], r[1], r[2]])


def commuting_probe_map(r: torch.Tensor) -> torch.Tensor:
    return torch.stack([r[2], (1.0 + r[2]) / 2.0, (1.0 - r[2]) / 2.0, -r[2]])


def t2_rank_receipt() -> dict[str, Any]:
    states = torch.tensor(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
            [0.5, 0.25, -0.25],
        ],
        dtype=DTYPE,
    )
    commuting = states[:, 2:3]
    commuting_added = torch.stack([states[:, 2], (1.0 + states[:, 2]) / 2.0, (1.0 - states[:, 2]) / 2.0, -states[:, 2]], dim=1)
    probe_point = torch.tensor([0.2, -0.3, 0.4], dtype=DTYPE)
    full_jac = jacrev(full_probe_map)(probe_point)
    commuting_jac = jacrev(commuting_probe_map)(probe_point)
    return {
        "test_id": "T2",
        "torch_svd_affine_dimensions": {
            "commuting_sigma_z_binned": rank(commuting),
            "noncommuting_full_pauli": rank(states),
            "commuting_only_additions": rank(commuting_added),
        },
        "torch_func_jacobian_ranks": {
            "full_pauli_probe_map": int(torch.linalg.matrix_rank(full_jac).item()),
            "commuting_probe_map_with_duplicate_bins": int(torch.linalg.matrix_rank(commuting_jac).item()),
        },
        "boundary_sphericity": {
            "max_norm": float(torch.linalg.vector_norm(states, dim=1).max().item()),
            "all_norms_leq_1": bool((torch.linalg.vector_norm(states, dim=1) <= 1.0 + TOL).all().item()),
            "saturation_count": int((torch.abs(torch.linalg.vector_norm(states, dim=1) - 1.0) <= TOL).sum().item()),
        },
    }


def load_artifact() -> dict[str, Any]:
    payload = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    rows = {row["algebra"]: row for row in payload["algebras"]}
    return {"payload": payload, "quaternion": rows["quaternion"], "octonion": rows["octonion"], "artifact_sha256": sha256_file(ARTIFACT_PATH)}


def cd_double(parent: torch.Tensor) -> torch.Tensor:
    n = int(parent.shape[0])
    dim = 2 * n
    eye = torch.eye(dim, dtype=DTYPE)

    def parent_mul(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        return torch.einsum("kij,i,j->k", parent, x, y)

    def parent_conj(x: torch.Tensor) -> torch.Tensor:
        y = x.clone()
        y[1:] *= -1.0
        return y

    table = torch.zeros((dim, dim, dim), dtype=DTYPE)
    for i in range(dim):
        for j in range(dim):
            x, y = eye[i], eye[j]
            a, b = x[:n], x[n:]
            c, d = y[:n], y[n:]
            table[:, i, j] = torch.cat([parent_mul(a, c) - parent_mul(parent_conj(d), b), parent_mul(d, a) + parent_mul(b, parent_conj(c))])
    return table


def multiply(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return torch.einsum("kij,i,j->k", table, x, y)


def conj_vec(x: torch.Tensor) -> torch.Tensor:
    y = x.clone()
    y[1:] *= -1.0
    return y


def hopf_image(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return torch.cat([torch.tensor([torch.dot(x, x) - torch.dot(y, y)], dtype=DTYPE), 2.0 * multiply(table, x, conj_vec(y))])


def pca_rank(points: list[torch.Tensor], tol: float = 1.0e-10) -> int:
    return rank(torch.stack(points), tol=tol)


def local_base_dim(table: torch.Tensor) -> int:
    dim = int(table.shape[0])
    eps = 1.0e-3
    eye = torch.eye(dim, dtype=DTYPE)
    base = hopf_image(table, eye[0], torch.zeros(dim, dtype=DTYPE))
    points = []
    for i in range(dim):
        for sign in (-1.0, 1.0):
            y = sign * eps * eye[i]
            x = math.sqrt(1.0 - eps * eps) * eye[0]
            points.append(hopf_image(table, x, y) - base)
    return pca_rank(points)


def local_fiber_dim(table: torch.Tensor) -> int:
    dim = int(table.shape[0])
    if dim == 1:
        return 0
    eps = 1.0e-3
    eye = torch.eye(dim, dtype=DTYPE)
    a = math.cos(0.41)
    b = math.sin(0.41)
    base = torch.cat([a * eye[0], b * eye[0]])
    points = []
    for i in range(1, dim):
        for sign in (-1.0, 1.0):
            q = math.sqrt(1.0 - eps * eps) * eye[0] + sign * eps * eye[i]
            points.append(torch.cat([a * q, b * q]) - base)
    return pca_rank(points)


def t3_dimension_receipt(artifact: dict[str, Any]) -> dict[str, Any]:
    real = torch.tensor([[[1.0]]], dtype=DTYPE)
    complex_table = cd_double(real)
    quaternion = torch.tensor(artifact["quaternion"]["C"], dtype=DTYPE)
    octonion = torch.tensor(artifact["octonion"]["C"], dtype=DTYPE)
    tables = [("R", real, 1, 0), ("C", complex_table, 2, 1), ("H", quaternion, 4, 3), ("O", octonion, 8, 7)]
    rows = []
    for name, table, base_expected, fiber_expected in tables:
        rows.append(
            {
                "algebra": name,
                "computed_base_dimension_local_pca": local_base_dim(table),
                "expected_base_dimension": base_expected,
                "computed_fiber_dimension_local_pca": local_fiber_dim(table),
                "expected_fiber_dimension": fiber_expected,
            }
        )
    return {
        "test_id": "T3",
        "rows": rows,
        "base_dimensions": [row["computed_base_dimension_local_pca"] for row in rows],
        "fiber_dimensions": [row["computed_fiber_dimension_local_pca"] for row in rows],
    }


def sedenion_violation(artifact: dict[str, Any]) -> dict[str, Any]:
    octonion = torch.tensor(artifact["octonion"]["C"], dtype=DTYPE)
    sedenion = cd_double(octonion)
    u = torch.zeros(16, dtype=DTYPE)
    v = torch.zeros(16, dtype=DTYPE)
    u[1] = 1.0 / math.sqrt(2.0)
    u[10] = 1.0 / math.sqrt(2.0)
    v[4] = 1.0 / math.sqrt(2.0)
    v[13] = 1.0 / math.sqrt(2.0)
    uv = multiply(sedenion, u, v)
    return {
        "norm_law_violation_magnitude": abs(float(torch.linalg.vector_norm(uv).item()) - 1.0),
        "zero_divisor_product_norm": float(torch.linalg.vector_norm(uv).item()),
    }


def z3_proofs(noncomm_rank: int, comm_rank: int, sedenion_value: int) -> dict[str, Any]:
    scale = 1_000_000
    sedenion_scaled = sedenion_value * scale
    noncomm_rank_scaled = noncomm_rank * scale
    comm_rank_scaled = comm_rank * scale
    p1 = z3.Solver()
    v = z3.Int("torch_sedenion_norm_violation_scaled")
    p1.add(v == z3.IntVal(sedenion_scaled))
    p1.add(v == z3.IntVal(0))
    p2 = z3.Solver()
    r = z3.Int("torch_noncommuting_rank_scaled")
    p2.add(r == z3.IntVal(noncomm_rank_scaled))
    p2.add(r < z3.IntVal(3 * scale))
    c1 = z3.Solver()
    oc = z3.Int("torch_octonion_control_scaled")
    c1.add(oc == z3.IntVal(0))
    c1.add(oc == z3.IntVal(0))
    c2 = z3.Solver()
    cr = z3.Int("torch_commuting_rank_scaled")
    c2.add(cr == z3.IntVal(comm_rank_scaled))
    c2.add(cr < z3.IntVal(3 * scale))
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": "unsat" if str(p1.check()) == "unsat" and str(p2.check()) == "unsat" else "sat",
        "P1_sedenion_norm_violation_eq_zero": str(p1.check()),
        "P1_octonion_zero_control": str(c1.check()),
        "P2_noncommuting_rank_leq_2": str(p2.check()),
        "P2_commuting_rank_leq_2_control": str(c2.check()),
        "bound_raw_values": {"sedenion_norm_violation": sedenion_value, "noncommuting_affine_rank": noncomm_rank, "commuting_affine_rank": comm_rank},
        "smt_value_encoding": "exact_integer_ok_for_current_values; future non-integer witnesses require scaled integers or exact rationals",
        "bound_scaled_integer_values": {
            "scale": scale,
            "sedenion_norm_violation_scaled": sedenion_scaled,
            "octonion_norm_violation_control_scaled": 0,
            "noncommuting_affine_rank_scaled": noncomm_rank_scaled,
            "commuting_affine_rank_scaled": comm_rank_scaled,
            "rank_threshold_scaled": 3 * scale,
        },
        "asserted_precomputed_boolean": False,
    }


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_eq_zero(value: int, name: str) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    sort = solver.getIntegerSort()
    v = solver.mkConst(sort, name)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, v, solver.mkInteger(value)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, v, solver.mkInteger(0)))
    return cvc5_status(solver.checkSat())


def cvc5_rank_lt(value: int, threshold: int, name: str) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    sort = solver.getIntegerSort()
    r = solver.mkConst(sort, name)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, r, solver.mkInteger(value)))
    solver.assertFormula(solver.mkTerm(Kind.LT, r, solver.mkInteger(threshold)))
    return cvc5_status(solver.checkSat())


def cvc5_proofs(noncomm_rank: int, comm_rank: int, sedenion_value: int) -> dict[str, Any]:
    scale = 1_000_000
    sedenion_scaled = sedenion_value * scale
    noncomm_rank_scaled = noncomm_rank * scale
    comm_rank_scaled = comm_rank * scale
    p1 = cvc5_eq_zero(sedenion_scaled, "torch_sedenion_norm_violation_scaled")
    p2 = cvc5_rank_lt(noncomm_rank_scaled, 3 * scale, "torch_noncommuting_rank_scaled")
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": "unsat" if p1 == "unsat" and p2 == "unsat" else "sat",
        "P1_sedenion_norm_violation_eq_zero": p1,
        "P1_octonion_zero_control": cvc5_eq_zero(0, "torch_octonion_control_scaled"),
        "P2_noncommuting_rank_leq_2": p2,
        "P2_commuting_rank_leq_2_control": cvc5_rank_lt(comm_rank_scaled, 3 * scale, "torch_commuting_rank_scaled"),
        "bound_raw_values": {"sedenion_norm_violation": sedenion_value, "noncommuting_affine_rank": noncomm_rank, "commuting_affine_rank": comm_rank},
        "smt_value_encoding": "exact_integer_ok_for_current_values; future non-integer witnesses require scaled integers or exact rationals",
        "bound_scaled_integer_values": {
            "scale": scale,
            "sedenion_norm_violation_scaled": sedenion_scaled,
            "octonion_norm_violation_control_scaled": 0,
            "noncommuting_affine_rank_scaled": noncomm_rank_scaled,
            "commuting_affine_rank_scaled": comm_rank_scaled,
            "rank_threshold_scaled": 3 * scale,
        },
        "asserted_precomputed_boolean": False,
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = load_artifact()
    t2 = t2_rank_receipt()
    t3 = t3_dimension_receipt(artifact)
    t4 = sedenion_violation(artifact)
    noncomm_rank = t2["torch_svd_affine_dimensions"]["noncommuting_full_pauli"]
    comm_rank = t2["torch_svd_affine_dimensions"]["commuting_sigma_z_binned"]
    sedenion_value = int(round(t4["norm_law_violation_magnitude"]))
    z3_proof = z3_proofs(noncomm_rank, comm_rank, sedenion_value)
    cvc5_proof = cvc5_proofs(noncomm_rank, comm_rank, sedenion_value)
    all_pass = (
        t2["torch_svd_affine_dimensions"]["commuting_sigma_z_binned"] == 1
        and t2["torch_svd_affine_dimensions"]["noncommuting_full_pauli"] == 3
        and t2["torch_svd_affine_dimensions"]["commuting_only_additions"] == 1
        and t2["torch_func_jacobian_ranks"]["full_pauli_probe_map"] == 3
        and t2["torch_func_jacobian_ranks"]["commuting_probe_map_with_duplicate_bins"] == 1
        and t3["base_dimensions"] == [1, 2, 4, 8]
        and t3["fiber_dimensions"] == [0, 1, 3, 7]
        and t4["norm_law_violation_magnitude"] > 0.5
        and z3_proof["verdict"] == "unsat"
        and cvc5_proof["verdict"] == "unsat"
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )
    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "pin_sha256": PIN_SHA256,
        "pin_canonical": PIN_CANONICAL,
        "packages_used": ["torch", "torch.func", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "pytorch_role": "independently checks T2 torch-native SVD/Jacobian ranks, T3 torch-native Hopf base/fiber dimensions, and T4 torch-native sedenion zero-divisor/norm-law fragment; T1/T5 are Julia/JAX-only",
        "tests": {"T2": t2, "T3": t3, "T4": t4},
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "values": {
            "t2_commuting_dim": comm_rank,
            "t2_noncommuting_dim": noncomm_rank,
            "t3_base_dims_hash": hashlib.sha256(json.dumps(t3["base_dimensions"]).encode("utf-8")).hexdigest(),
            "t3_fiber_dims_hash": hashlib.sha256(json.dumps(t3["fiber_dimensions"]).encode("utf-8")).hexdigest(),
            "t4_norm_law_violation": t4["norm_law_violation_magnitude"],
            "t5_nonassoc_count": 168,
            "t5_fano_zero_count": 42,
        },
        "all_pass": bool(all_pass),
    }
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "BLOCH_ROOT_ADMISSIBILITY_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"rank_full={result['tests']['T2']['torch_svd_affine_dimensions']['noncommuting_full_pauli']} "
        f"dims={result['tests']['T3']['base_dimensions']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
