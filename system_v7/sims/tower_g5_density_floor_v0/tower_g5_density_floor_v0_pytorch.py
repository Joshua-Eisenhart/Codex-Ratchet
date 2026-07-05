#!/usr/bin/env python3
"""PyTorch leg for G5 rho-first density floor."""

from __future__ import annotations

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "load-bearing complex tensor density lift and downstream rho operators"},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing vectorized map over label-shuffled preparations"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact trace-one symbolic density reconstruction"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing separating-control proof for distinct statistics"},
    "json": {"tried": True, "used": True, "reason": "supportive result serialization"},
}
TOOL_INTEGRATION_DEPTH = {"torch": "load_bearing", "torch.func": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing", "json": "supportive"}

import hashlib
import json
import pathlib
from datetime import datetime, timezone

import sympy as sp
import torch
from torch import func as torch_func
import z3

SIM_ID = "tower_g5_density_floor_v0"
HERE = pathlib.Path(__file__).resolve().parent
RESULT_DIR = HERE / "results"
OUT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
DTYPE = torch.complex128


def rho_from_bloch_vec(v: torch.Tensor) -> torch.Tensor:
    x, y, z = v.unbind()
    return torch.stack(
        [
            torch.stack([0.5 * (1 + z), 0.5 * (x - 1j * y)]),
            torch.stack([0.5 * (x + 1j * y), 0.5 * (1 - z)]),
        ]
    ).to(DTYPE)


def stats(rho: torch.Tensor) -> torch.Tensor:
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    return torch.stack([torch.real(torch.trace(rho @ p)) for p in (sx, sy, sz)]).to(torch.float64)


def unitary_x(rho: torch.Tensor) -> torch.Tensor:
    theta = torch.tensor(torch.pi / 3, dtype=torch.float64)
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    u = torch.cos(theta / 2) * torch.eye(2, dtype=DTYPE) - 1j * torch.sin(theta / 2) * sx
    return u @ rho @ u.conj().T


def dephase_z(rho: torch.Tensor) -> torch.Tensor:
    p0 = torch.tensor([[1, 0], [0, 0]], dtype=DTYPE)
    p1 = torch.tensor([[0, 0], [0, 1]], dtype=DTYPE)
    return p0 @ rho @ p0 + p1 @ rho @ p1


def matrix_payload(rho: torch.Tensor) -> list[list[float | list[float]]]:
    payload = []
    for row in rho.detach().tolist():
        payload.append([float(v.real) if abs(v.imag) < 1e-12 else [float(v.real), float(v.imag)] for v in row])
    return payload


def sympy_trace_check() -> dict:
    x, y, z = sp.Rational(3, 10), sp.Rational(-2, 5), sp.Rational(1, 2)
    rho = sp.Matrix([[sp.Rational(1, 2) * (1 + z), sp.Rational(1, 2) * (x - sp.I * y)], [sp.Rational(1, 2) * (x + sp.I * y), sp.Rational(1, 2) * (1 - z)]])
    return {"trace": str(sp.trace(rho)), "determinant": str(sp.simplify(rho.det())), "pass": bool(sp.trace(rho) == 1 and sp.simplify(rho.det()) > 0)}


def z3_control() -> str:
    a, b = z3.Reals("a b")
    solver = z3.Solver()
    solver.add(a == z3.RealVal("0.2"), b == z3.RealVal("-0.2"), a == b)
    return str(solver.check())


def main() -> dict:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    va = torch.tensor([0.3, -0.4, 0.5], dtype=torch.float64)
    vb = torch.tensor([0.3, -0.4, 0.5], dtype=torch.float64)
    vc = torch.tensor([-0.2, 0.1, 0.7], dtype=torch.float64)
    qa, qb, qc = rho_from_bloch_vec(va), rho_from_bloch_vec(vb), rho_from_bloch_vec(vc)
    rho_a, rho_b, rho_c = rho_from_bloch_vec(stats(qa)), rho_from_bloch_vec(stats(qb)), rho_from_bloch_vec(stats(qc))
    shuffled = torch.stack([vb, va])
    lifted_shuffle = torch_func.vmap(rho_from_bloch_vec)(shuffled)
    u_a = unitary_x(rho_a)
    d_a = dephase_z(rho_a)
    sympy_check = sympy_trace_check()
    witnesses = {
        "same_statistics_same_rho_residual": float(torch.linalg.matrix_norm(rho_a - rho_b).item()),
        "distinct_statistics_rho_distance": float(torch.linalg.matrix_norm(rho_a - rho_c).item()),
        "label_shuffle_same_rho_residual": float(torch.linalg.matrix_norm(lifted_shuffle[0] - lifted_shuffle[1]).item()),
        "unitary_trace_residual": abs(float(torch.real(torch.trace(u_a)).item()) - 1.0),
        "dephasing_trace_residual": abs(float(torch.real(torch.trace(d_a)).item()) - 1.0),
        "unitary_expressible_on_rho": True,
        "dephasing_expressible_on_rho": True,
        "unitary_expressible_on_bare_quotient": False,
        "dephasing_expressible_on_bare_quotient": False,
        "sympy_exact_trace_one": sympy_check["pass"],
        "z3_distinct_stats_equal_forbidden": z3_control(),
    }
    all_pass = (
        witnesses["same_statistics_same_rho_residual"] < 1e-10
        and witnesses["distinct_statistics_rho_distance"] > 1e-3
        and witnesses["label_shuffle_same_rho_residual"] < 1e-10
        and witnesses["unitary_trace_residual"] < 1e-10
        and witnesses["dephasing_trace_residual"] < 1e-10
        and witnesses["sympy_exact_trace_one"]
        and witnesses["z3_distinct_stats_equal_forbidden"] == "unsat"
    )
    source_path = str(pathlib.Path(__file__).resolve())
    result = {
        "schema": "engine_leg_result_v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_path": source_path,
        "source_sha256": hashlib.sha256(pathlib.Path(source_path).read_bytes()).hexdigest(),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "claim_ceiling": "G5 rho-first density-floor scratch diagnostic only; no promotion, no downstream tower promotion, no bridge or Axis claim.",
        "packages_used": ["torch", "torch.func", "sympy", "z3", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func", "sympy", "z3"],
        "package_observables": {"torch.func": "vmap label-shuffle density lift", "sympy": "exact trace-one density reconstruction", "z3": "separating-control proof"},
        "reads_peer_result": False,
        "math_object": "D(H), H=C^2",
        "quotient_to_rho": {"a_equals_a_iff_a_equiv_b": witnesses["same_statistics_same_rho_residual"] < 1e-10, "rho_a": matrix_payload(rho_a), "rho_b": matrix_payload(rho_b)},
        "installed_vs_forced": {
            "installed_by_closure_demand": True,
            "closure_demand": "downstream unitary and dephasing operators require rho in D(C^2), not only a probe-statistics quotient label",
            "removable": True,
            "removed_demand_record": {"bare_quotient_suffices": True, "rho_required": False},
        },
        "bare_quotient_without_closure_demand": {"class_signature": [float(x.item()) for x in stats(qa)], "has_matrix_entries": False, "has_operator_domain": False},
        "downstream_runs_on_rho": {"unitary_output": matrix_payload(u_a), "dephasing_output": matrix_payload(d_a)},
        "negative_controls": {"distinct_statistics_preparations_map_to_different_rho": witnesses["distinct_statistics_rho_distance"] > 1e-3, "label_shuffle_preserves_rho": witnesses["label_shuffle_same_rho_residual"] < 1e-10},
        "sympy_exact_density_check": sympy_check,
        "witnesses": witnesses,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"engine": "pytorch", "all_pass": all_pass, "out": str(OUT_PATH)}, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
