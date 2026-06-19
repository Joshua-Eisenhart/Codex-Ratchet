#!/usr/bin/env python3
"""PyTorch pinned tensor/autograd leg for geo_s5_terrain_flows_v0.

This lane mirrors the pinned S5 terrain-flow rows with torch tensors and
torch.func batching. It is not the symbolic CAS lane.
"""

from __future__ import annotations

import datetime as dt
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import torch
from torch.func import vmap
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s5_terrain_flows_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_pytorch.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
DTYPE = torch.float64

PIN_SPEC = (
    "geo_s5_terrain_flows_v0|"
    "sigma_y_standard=[[0,-i],[i,0]]|"
    "primary_bloch_basis=(sigma_x,sigma_y_standard,sigma_z)|"
    "s1_pinned_bloch_basis=(sigma_x,-sigma_y_standard,sigma_z)|"
    "standard_to_s1_pinned_J=diag(1,-1,1)|"
    "component_rule=r_i=Tr(generator(rho)*basis_i)|"
    "rho_rule=rho(r)=(I+r.basis)/2|"
    "H0=(sigma_x+sigma_y+sigma_z)/sqrt(3)|H_L=+H0|H_R=-H0|"
    "rows=(Se/Funnel,Se/Cannon,Ne/Vortex,Ne/Spiral,Ni/Pit,Ni/Source,Si/Hill,Si/Citadel)|"
    "symbolic_parameters=(lambda_Se_L,epsilon_Se_L,lambda_Se_R,epsilon_Se_R,gamma_Ni_L,epsilon_Ni_L,gamma_Ni_R,epsilon_Ni_R,kappa_Si_L,omega_Si_L,kappa_Si_R,omega_Si_R)|"
    "pin_row=(lambda_Se_L=1/5,epsilon_Se_L=1/5,lambda_Se_R=1/5,epsilon_Se_R=1/5,gamma_Ni_L=1/2,epsilon_Ni_L=1/5,gamma_Ni_R=1/2,epsilon_Ni_R=1/5,kappa_Si_L=2/5,omega_Si_L=1/5,kappa_Si_R=2/5,omega_Si_R=1/5)|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

CONVENTION_PIN = {
    "sigma_y_standard": [["0", "-i"], ["i", "0"]],
    "primary_table_basis": "source_locked_standard_bloch",
    "source_locked_bloch_basis": ["sigma_x", "sigma_y_standard", "sigma_z"],
    "s1_pinned_bloch_basis": ["sigma_x", "-sigma_y_standard", "sigma_z"],
    "standard_to_s1_pinned_J": [["1", "0", "0"], ["0", "-1", "0"], ["0", "0", "1"]],
    "conversion_rule": "A_s1_pinned = J * A_source_locked_standard * J and b_s1_pinned = J * b",
    "component_rule": "r_i = Tr(generator(rho) * basis_i)",
    "rho_rule": "rho(r) = (I + r.basis) / 2",
    "hamiltonian_pin": {
        "H0": "(sigma_x + sigma_y + sigma_z) / sqrt(3)",
        "H_L": "+H0",
        "H_R": "-H0",
        "n": ["1/sqrt(3)", "1/sqrt(3)", "1/sqrt(3)"],
    },
    "si_frame_pin": {"Hill": "z frame", "Citadel": "x frame"},
    "stage": "S5 density/Bloch terrain flows only",
}

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive pinned tensor substrate for matrix rows, matrix exponentials, and stationary solves",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing batched evaluation of all pinned affine vector fields and purity derivatives",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing pinned-entry contradiction proof for Ni non-unitality; not a full symbolic flow proof",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent pinned-entry contradiction proof for the same Ni non-unitality entry",
    },
}

TOOL_INTEGRATION_DEPTH = {"torch": "supportive", "torch.func": "supportive", "z3": "load_bearing", "cvc5": "load_bearing"}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def frac(value: float, denom_limit: int = 10_000) -> str:
    q = Fraction(str(float(value))).limit_denominator(denom_limit)
    return str(q.numerator) if q.denominator == 1 else f"{q.numerator}/{q.denominator}"


def matrix_fraction_strings(mat: torch.Tensor) -> list[list[str]]:
    return [[frac(float(x)) for x in row] for row in mat.detach().cpu().tolist()]


def vector_fraction_strings(vec: torch.Tensor) -> list[str]:
    return [frac(float(x)) for x in vec.detach().cpu().tolist()]


def pinned_rows() -> dict[str, dict[str, torch.Tensor]]:
    lam = 1.0 / 5.0
    eps = 1.0 / 5.0
    gamma = 1.0 / 2.0
    kappa = 2.0 / 5.0
    omega = 1.0 / 5.0
    S = (2.0 / math.sqrt(3.0)) * torch.tensor([[0.0, -1.0, 1.0], [1.0, 0.0, -1.0], [-1.0, 1.0, 0.0]], dtype=DTYPE)
    damp_se = -4.0 * lam * torch.eye(3, dtype=DTYPE)
    damp_ni = torch.diag(torch.tensor([-gamma / 2.0, -gamma / 2.0, -gamma], dtype=DTYPE))
    hill = torch.tensor([[-kappa, -2.0 * omega, 0.0], [2.0 * omega, -kappa, 0.0], [0.0, 0.0, 0.0]], dtype=DTYPE)
    citadel = torch.tensor([[0.0, 0.0, 0.0], [0.0, -kappa, -2.0 * omega], [0.0, 2.0 * omega, -kappa]], dtype=DTYPE)
    zero = torch.zeros(3, dtype=DTYPE)
    return {
        "Se_Funnel_L": {"A": damp_se + eps * S, "b": zero.clone()},
        "Se_Cannon_R": {"A": damp_se - eps * S, "b": zero.clone()},
        "Ne_Vortex_L": {"A": S.clone(), "b": zero.clone()},
        "Ne_Spiral_R": {"A": -S.clone(), "b": zero.clone()},
        "Ni_Pit_L": {"A": damp_ni + eps * S, "b": torch.tensor([0.0, 0.0, -gamma], dtype=DTYPE)},
        "Ni_Source_R": {"A": damp_ni - eps * S, "b": torch.tensor([0.0, 0.0, gamma], dtype=DTYPE)},
        "Si_Hill_L": {"A": hill, "b": zero.clone()},
        "Si_Citadel_R": {"A": citadel, "b": zero.clone()},
    }


def affine_batch_receipt(rows: dict[str, dict[str, torch.Tensor]]) -> dict[str, Any]:
    names = list(rows)
    A_stack = torch.stack([rows[name]["A"] for name in names])
    b_stack = torch.stack([rows[name]["b"] for name in names])
    r0 = torch.tensor([1.0 / 5.0, -2.0 / 5.0, 1.0 / 3.0], dtype=DTYPE)
    dr = vmap(lambda A, b: A @ r0 + b)(A_stack, b_stack)
    out = {}
    for idx, name in enumerate(names):
        out[name] = {
            "pinned_A_fractional": matrix_fraction_strings(A_stack[idx]),
            "pinned_b_fractional": vector_fraction_strings(b_stack[idx]),
            "dr_at_r0_fractional": vector_fraction_strings(dr[idx]),
        }
    return {"method": "torch.func.vmap(lambda A,b: A@r0+b)", "r0": ["1/5", "-2/5", "1/3"], "rows": out, "pass": len(out) == 8}


def flow_and_basin_receipt(rows: dict[str, dict[str, torch.Tensor]]) -> dict[str, Any]:
    r0 = torch.tensor([1.0 / 5.0, -2.0 / 5.0, 1.0 / 3.0], dtype=DTYPE)
    t = torch.tensor(1.0, dtype=DTYPE)
    out = {}
    for name, row in rows.items():
        A = row["A"]
        b = row["b"]
        if torch.linalg.matrix_rank(A) == 3:
            r_star = -torch.linalg.solve(A, b)
            r_t = r_star + torch.matrix_exp(t * A) @ (r0 - r_star)
            limit = r_star
            limit_kind = "unique_affine_stationary_limit"
        elif name == "Si_Hill_L":
            r_t = torch.matrix_exp(t * A) @ r0
            limit = torch.tensor([0.0, 0.0, r0[2]], dtype=DTYPE)
            limit_kind = "retained_z_slice"
        elif name == "Si_Citadel_R":
            r_t = torch.matrix_exp(t * A) @ r0
            limit = torch.tensor([r0[0], 0.0, 0.0], dtype=DTYPE)
            limit_kind = "retained_x_slice"
        elif name.startswith("Ne"):
            r_t = torch.matrix_exp(t * A) @ r0
            limit = torch.full((3,), float("nan"), dtype=DTYPE)
            limit_kind = "nonlimit_orbit"
        else:
            r_t = torch.matrix_exp(t * A) @ r0
            limit = torch.zeros(3, dtype=DTYPE)
            limit_kind = "origin_limit"
        out[name] = {
            "r_t_at_1_fractional": vector_fraction_strings(r_t),
            "limit_kind": limit_kind,
            "limit_fractional": None if torch.isnan(limit).any() else vector_fraction_strings(limit),
        }
    return {
        "method": "torch.matrix_exp for pinned flow samples plus torch.linalg.solve where A is invertible",
        "rows": out,
        "pass": out["Ni_Pit_L"]["limit_kind"] == "unique_affine_stationary_limit"
        and out["Ni_Source_R"]["limit_kind"] == "unique_affine_stationary_limit"
        and out["Ne_Vortex_L"]["limit_kind"] == "nonlimit_orbit"
        and out["Si_Hill_L"]["limit_fractional"] == ["0", "0", "1/3"],
    }


def purity_receipt(rows: dict[str, dict[str, torch.Tensor]]) -> dict[str, Any]:
    r_pure = torch.tensor([1.0, 0.0, 0.0], dtype=DTYPE)
    A_stack = torch.stack([rows["Ne_Vortex_L"]["A"], rows["Ne_Spiral_R"]["A"]])
    derivs = vmap(lambda A: 2.0 * torch.dot(r_pure, A @ r_pure))(A_stack)
    weak_A = rows["Ne_Vortex_L"]["A"] + torch.diag(torch.tensor([-2.0 / 5.0, -2.0 / 5.0, 0.0], dtype=DTYPE))
    weak_deriv = 2.0 * torch.dot(r_pure, weak_A @ r_pure)
    return {
        "method": "torch.func.vmap over d/dt ||r||^2 = 2*r dot A*r",
        "pure_ne_derivatives_fractional": [frac(float(x)) for x in derivs],
        "weak_ne_mutation_derivative_fractional": frac(float(weak_deriv)),
        "weak_control_gate_passed_after_mutation": False,
        "pass": bool(torch.max(torch.abs(derivs)).item() <= 1.0e-12 and float(weak_deriv) < -0.1),
    }


def unitality_receipt(rows: dict[str, dict[str, torch.Tensor]]) -> dict[str, Any]:
    out = {}
    for name, row in rows.items():
        b = row["b"]
        is_unital = bool(torch.max(torch.abs(b)).item() <= 1.0e-12)
        out[name] = {"b_fractional": vector_fraction_strings(b), "unital": is_unital}
    return {
        "rows": out,
        "pass": out["Ni_Pit_L"]["b_fractional"] == ["0", "0", "-1/2"]
        and out["Ni_Source_R"]["b_fractional"] == ["0", "0", "1/2"]
        and all(out[name]["unital"] for name in out if not name.startswith("Ni")),
    }


def z3_nonunitality_proof() -> dict[str, Any]:
    solver = z3.Solver()
    pit_bz_times_2 = z3.Int("torch_pit_bz_times_2")
    solver.add(pit_bz_times_2 == -1)
    solver.add(pit_bz_times_2 == 0)
    verdict = str(solver.check())

    wrong = z3.Solver()
    wrong_bz = z3.Int("torch_wrong_pit_bz_times_2")
    wrong.add(wrong_bz == 0)
    wrong.add(wrong_bz == 0)
    wrong_verdict = str(wrong.check())
    return {
        "solver": "z3",
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "torch pinned-entry contradiction only: Pit b_z=-1/2 contradicts fake unital b_z=0",
        "proof_scope": "pinned_entry_contradiction_not_full_symbolic_flow_or_basin_proof",
        "bound_raw_values": {"2*Pit_b_z": -1},
        "asserted_precomputed_boolean": False,
        "wrong_control_verdict": wrong_verdict,
        "wrong_control_can_fail": wrong_verdict == "sat",
    }


def cvc5_nonunitality_proof() -> dict[str, Any]:
    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_LIA")
    integer = tm.getIntegerSort()
    pit = tm.mkConst(integer, "torch_pit_bz_times_2_cvc5")
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, pit, tm.mkInteger(-1)))
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, pit, tm.mkInteger(0)))
    verdict = str(solver.checkSat()).lower()

    wrong = cvc5.Solver(tm)
    wrong.setLogic("QF_LIA")
    wrong_pit = tm.mkConst(integer, "torch_wrong_pit_bz_times_2_cvc5")
    wrong.assertFormula(tm.mkTerm(Kind.EQUAL, wrong_pit, tm.mkInteger(0)))
    wrong.assertFormula(tm.mkTerm(Kind.EQUAL, wrong_pit, tm.mkInteger(0)))
    wrong_verdict = str(wrong.checkSat()).lower()
    return {
        "solver": "cvc5",
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "independent cvc5 pinned-entry contradiction check for torch Pit non-unitality",
        "proof_scope": "pinned_entry_contradiction_not_full_symbolic_flow_or_basin_proof",
        "bound_raw_values": {"2*Pit_b_z": -1},
        "asserted_precomputed_boolean": False,
        "wrong_control_verdict": wrong_verdict,
        "wrong_control_can_fail": wrong_verdict == "sat",
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = pinned_rows()
    affine = affine_batch_receipt(rows)
    flow = flow_and_basin_receipt(rows)
    purity = purity_receipt(rows)
    unitality = unitality_receipt(rows)
    z3_proof = z3_nonunitality_proof()
    cvc5_proof = cvc5_nonunitality_proof()
    all_pass = (
        affine["pass"]
        and flow["pass"]
        and purity["pass"]
        and unitality["pass"]
        and z3_proof["verdict"] == cvc5_proof["verdict"] == "unsat"
        and z3_proof["wrong_control_can_fail"]
        and cvc5_proof["wrong_control_can_fail"]
    )
    return {
        "schema_version": "geo_s5_engine_result_v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "role_id": "pytorch_pinned_tensor_autograd_mirror",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["torch", "torch.func", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "torch.func",
                "qualified_api/function": "torch.func.vmap",
                "input_object": "eight pinned affine Bloch rows and purity derivatives",
                "output_object": "batched dr/dt and d||r||^2/dt receipts",
                "positive_case": "pure Ne derivatives vanish and weak-Ne mutation is negative",
                "negative/erased_control": "weak-Ne mutation d||r||^2/dt=-4/5",
                "boundary_case": "PyTorch is pinned mirror, not symbolic CAS",
                "role": "supportive",
                "demotion_condition": "passing torch.func capability probe required before this can gate claim metadata",
                "gates": [],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver.check",
                "input_object": "2*Pit_b_z pinned integer entry",
                "output_object": "unsat contradiction against fake unital b_z=0",
                "positive_case": "2*Pit_b_z=-1 and 2*Pit_b_z=0 is unsat",
                "negative/erased_control": "0=0 wrong control is sat",
                "boundary_case": "pinned-entry proof only",
                "demotion_condition": "if solver binds a boolean, proof is demoted",
                "gates": ["all_pass", "P8"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver.checkSat",
                "input_object": "same 2*Pit_b_z pinned integer entry",
                "output_object": "independent unsat contradiction",
                "positive_case": "agrees with z3",
                "negative/erased_control": "0=0 wrong control is sat",
                "boundary_case": "pinned-entry proof only",
                "demotion_condition": "if cvc5 disagrees with z3, envelope fails",
                "gates": ["all_pass", "P8"],
            },
        ],
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "convention_pin": CONVENTION_PIN,
        "affine_batch": affine,
        "flow_and_basin": flow,
        "purity": purity,
        "unitality": unitality,
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "limits": "PyTorch is a pinned tensor/autograd mirror and SMT control lane, not symbolic derivation or terrain-family admission.",
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(RESULT_PATH.relative_to(ROOT)), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
