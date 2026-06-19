#!/usr/bin/env python3
"""PyTorch tensor leg for geo_s2_connection_flux_foliation_v0."""

from __future__ import annotations

import datetime as dt
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
SIM_ID = "geo_s2_connection_flux_foliation_v0"
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
    "geo_s2_connection_flux_foliation_v0|"
    "holonomy_quantity=primary:accumulated_phi;separate:endpoint_global_spinor_phase,Berry_phase|"
    "berry_formula=one_base_loop:-Omega/2=-pi*(1-cos(2*eta));lifted_cycle_twice:-2*pi*(1-cos(2*eta))|"
    "phase_domain=lifted_real_with_mod_2pi_reconciliation|"
    "base_loop_count=lifted_torus_chart_cycle chi:0->2pi traverses base twice; one_base_loop chi:0->pi|"
    "orientation_and_c1_sign=F=-2*sin(2*eta)deta_wedge_dchi integrates -4*pi over double-covered chart; physical integral -2*pi; c1=-physical_integral/(2*pi)=1"
)

CONVENTION_PIN = {
    "holonomy_quantity": {
        "primary_reported": "accumulated_phi",
        "distinguished_from": ["endpoint_global_spinor_phase", "Berry_phase"],
        "target_lifted_cycle": "h(eta) = -2*pi*cos(2*eta)",
    },
    "berry_formula": {
        "one_base_loop": "-Omega/2 = -pi*(1 - cos(2*eta))",
        "lifted_torus_chart_cycle": "-2*pi*(1 - cos(2*eta))",
    },
    "phase_domain": {
        "primary": "lifted_real",
        "mod_reconciliation": "mod_2pi representatives are reported separately",
    },
    "base_loop_count": {
        "one_base_loop": "chi: 0 -> pi because base_angle = 2*chi",
        "lifted_torus_chart_cycle": "chi: 0 -> 2pi traverses the base twice",
    },
    "orientation_and_c1_sign": {
        "displayed_curvature": "F = -2*sin(2*eta) d eta wedge d chi",
        "double_covered_chart_integral": "-4*pi",
        "physical_base_integral": "-2*pi",
        "reported_c1": "c1 = -physical_base_integral/(2*pi) = 1",
    },
}

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive tensor substrate for horizontal transport and grid quotient rows",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing vmap route over eta shells for the horizontal ODE convergence lane",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact integer SMT check over torch-derived finite grid quotient cardinality",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent exact integer SMT check over the same grid quotient object",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "supportive",
    "torch.func": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def euler_delta_phi(eta: torch.Tensor, steps: int) -> torch.Tensor:
    t = torch.arange(steps, dtype=DTYPE) / float(steps)
    dchi_dt = 2.0 * math.pi + 0.1 * (1.0 - 2.0 * t)
    return torch.sum(-torch.cos(2.0 * eta) * dchi_dt / float(steps))


def horizontal_transport() -> dict[str, Any]:
    eta_values = torch.tensor([math.pi / 12, math.pi / 6, math.pi / 4, math.pi / 3, 5 * math.pi / 12], dtype=DTYPE)
    eta_labels = ["pi/12", "pi/6", "pi/4", "pi/3", "5*pi/12"]
    steps = [15, 31, 63, 127]
    rows = []
    for n in steps:
        deltas = vmap(lambda eta: euler_delta_phi(eta, n))(eta_values)
        targets = -2.0 * math.pi * torch.cos(2.0 * eta_values)
        residuals = deltas - targets
        rows.append(
            {
                "steps": n,
                "deltas": [float(x) for x in deltas],
                "targets": [float(x) for x in targets],
                "residuals": [float(x) for x in residuals],
            }
        )
    by_eta = []
    for idx, label in enumerate(eta_labels):
        abs_res = [abs(row["residuals"][idx]) for row in rows]
        by_eta.append(
            {
                "eta": label,
                "target_h_eta": rows[-1]["targets"][idx],
                "abs_residuals_by_steps": dict(zip([str(s) for s in steps], abs_res, strict=True)),
                "strictly_shrinking": all(abs_res[i + 1] < abs_res[i] for i in range(len(abs_res) - 1)),
            }
        )
    return {
        "method": "torch.func.vmap over eta values; each lane integrates A(gamma_dot)=0 with chi(t)=2*pi*t+0.1*t*(1-t)",
        "steps": steps,
        "rows_by_step": rows,
        "rows_by_eta": by_eta,
        "vmap_used": True,
        "nonzero_rhs_rows_strictly_shrink": all(
            row["strictly_shrinking"] for row in by_eta if row["eta"] != "pi/4"
        ),
    }


def grid_classes(n: int) -> dict[str, Any]:
    idx = torch.arange(n, dtype=torch.int64)
    ii, jj = torch.meshgrid(idx, idx, indexing="ij")
    points = torch.stack([ii.reshape(-1), jj.reshape(-1)], dim=1)
    shift = n // 2
    partners = (points + shift) % n
    classes = set()
    for point, partner in zip(points.tolist(), partners.tolist(), strict=True):
        key = tuple(sorted([tuple(point), tuple(partner)]))
        classes.add(key)
    parity_preserved = all(((a[0] - a[1]) - (b[0] - b[1])) % 2 == 0 for a, b in classes)
    return {
        "N": n,
        "torch_point_tensor_shape": list(points.shape),
        "chart_points": int(points.shape[0]),
        "quotient_classes": len(classes),
        "physical_points": len(classes),
        "target_N_squared_over_2": n * n // 2,
        "identification": "(i,j) ~ (i+N/2,j+N/2) mod N",
        "parity_relation_preserved": parity_preserved,
        "naive_control_points": n * n,
        "naive_control_fails": n * n != len(classes),
        "pass": len(classes) == n * n // 2 and parity_preserved,
    }


def z3_grid_proof(row: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    n = z3.Int("N")
    p = z3.Int("physical_points")
    solver.add(n == z3.IntVal(int(row["N"])))
    solver.add(p == z3.IntVal(int(row["physical_points"])))
    solver.add(2 * p != n * n)
    positive = solver.check()

    wrong = z3.Solver()
    wn = z3.Int("wrong_N")
    naive = z3.Int("naive_points")
    wrong.add(wn == z3.IntVal(int(row["N"])))
    wrong.add(naive == z3.IntVal(int(row["naive_control_points"])))
    wrong.add(2 * naive == wn * wn)
    wrong_status = wrong.check()
    return {
        "solver": "z3",
        "verdict": str(positive),
        "claim": "SMT binds torch-derived N and physical quotient-cardinality, then refutes 2*physical_points != N^2.",
        "derived_expression": "2*physical_points == N*N",
        "bound_raw_values": {"N": row["N"], "physical_points": row["physical_points"]},
        "asserted_precomputed_boolean": False,
        "naive_control_verdict": str(wrong_status),
        "naive_control_can_fail": str(wrong_status) == "unsat",
    }


def cvc5_grid_proof(row: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    ints = solver.getIntegerSort()
    n = solver.mkConst(ints, "N")
    p = solver.mkConst(ints, "physical_points")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, n, solver.mkInteger(int(row["N"]))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, p, solver.mkInteger(int(row["physical_points"]))))
    lhs = solver.mkTerm(Kind.MULT, solver.mkInteger(2), p)
    rhs = solver.mkTerm(Kind.MULT, n, n)
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, lhs, rhs)))
    positive = solver.checkSat()

    wrong = cvc5.Solver()
    wrong.setLogic("QF_LIA")
    ints2 = wrong.getIntegerSort()
    wn = wrong.mkConst(ints2, "wrong_N")
    naive = wrong.mkConst(ints2, "naive_points")
    wrong.assertFormula(wrong.mkTerm(Kind.EQUAL, wn, wrong.mkInteger(int(row["N"]))))
    wrong.assertFormula(wrong.mkTerm(Kind.EQUAL, naive, wrong.mkInteger(int(row["naive_control_points"]))))
    wrong_lhs = wrong.mkTerm(Kind.MULT, wrong.mkInteger(2), naive)
    wrong_rhs = wrong.mkTerm(Kind.MULT, wn, wn)
    wrong.assertFormula(wrong.mkTerm(Kind.EQUAL, wrong_lhs, wrong_rhs))
    wrong_result = wrong.checkSat()
    return {
        "solver": "cvc5",
        "verdict": "unsat" if positive.isUnsat() else "sat" if positive.isSat() else str(positive),
        "claim": "Independent CVC5 integer proof over torch-derived quotient cardinality.",
        "derived_expression": "2*physical_points == N*N",
        "bound_raw_values": {"N": row["N"], "physical_points": row["physical_points"]},
        "asserted_precomputed_boolean": False,
        "naive_control_verdict": "unsat" if wrong_result.isUnsat() else "sat" if wrong_result.isSat() else str(wrong_result),
        "naive_control_can_fail": wrong_result.isUnsat(),
    }


def build_result() -> dict[str, Any]:
    horizontal = horizontal_transport()
    grid_rows = [grid_classes(n) for n in [4, 6, 8, 10]]
    primary_grid = next(row for row in grid_rows if row["N"] == 8)
    z3_proof = z3_grid_proof(primary_grid)
    cvc5_proof = cvc5_grid_proof(primary_grid)
    receipts = {
        "S2.H1": {
            "id": "S2.H1",
            "exact_strength": "diagnostic_float_nonclaim",
            "pass": horizontal["nonzero_rhs_rows_strictly_shrink"],
            "convention_pin": CONVENTION_PIN,
            "torch_native_route": horizontal,
        },
        "S2.G": {
            "id": "S2.G",
            "exact_strength": "exact_integer_combinatorial",
            "pass": all(row["pass"] for row in grid_rows),
            "convention_pin": CONVENTION_PIN,
            "grid_rows": grid_rows,
        },
    }
    tool_calls = [
        {
            "tool": "torch.func",
            "qualified_api/function": "torch.func.vmap",
            "input_object": "eta tensor [pi/12, pi/6, pi/4, pi/3, 5*pi/12] and step counts [15,31,63,127]",
            "output_object": "batched horizontal ODE endpoint deltas and residual rows",
            "positive_case": "nonzero-holonomy eta rows have shrinking residuals",
            "negative/erased_control": "pi/4 zero-holonomy row is separately visible and not used to fake convergence",
            "boundary_case": "eta=pi/4 Clifford torus has h(eta)=0",
            "role": "supportive",
            "demotion_condition": "passing torch.func capability probe required before this can gate claim metadata",
            "gates": [],
        },
        {
            "tool": "z3",
            "qualified_api/function": "z3.Solver/check",
            "input_object": "torch-derived N=8 physical grid cardinality",
            "output_object": z3_proof,
            "positive_case": "pinned quotient cardinality refutes disequality",
            "negative/erased_control": "naive N^2 control cannot satisfy 2*points=N^2",
            "boundary_case": "even N required",
            "demotion_condition": "if bound values are replaced by booleans, SMT is decorative",
            "gates": ["all_pass", "S2.G", "crossover_proofs"],
        },
        {
            "tool": "cvc5",
            "qualified_api/function": "cvc5.Solver/checkSat",
            "input_object": "same torch-derived N=8 physical grid cardinality",
            "output_object": cvc5_proof,
            "positive_case": "independent integer proof agrees with z3",
            "negative/erased_control": "naive N^2 control fails",
            "boundary_case": "even N required",
            "demotion_condition": "if CVC5 does not bind raw integers, demote proof",
            "gates": ["all_pass", "S2.G", "crossover_proofs"],
        },
    ]
    all_pass = (
        all(item["pass"] for item in receipts.values())
        and z3_proof["verdict"] == cvc5_proof["verdict"] == "unsat"
        and z3_proof["naive_control_can_fail"]
        and cvc5_proof["naive_control_can_fail"]
        and READS_PEER_RESULT is False
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
    )
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_pytorch",
        "engine": "pytorch",
        "role_id": "pytorch_tensor_ode_grid_smt_builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "convention_pin": CONVENTION_PIN,
        "packages_used": ["torch", "torch.func", "z3", "cvc5", "json", "hashlib", "pathlib", "math"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": tool_calls,
        "receipts": receipts,
        "exact_smt": {"z3": z3_proof, "cvc5": cvc5_proof},
        "crossover_proofs": {
            "z3": {"ran": True, "verdict": z3_proof["verdict"], "load_bearing": True, **z3_proof},
            "cvc5": {"ran": True, "verdict": cvc5_proof["verdict"], "load_bearing": True, **cvc5_proof},
        },
        "all_pass": bool(all_pass),
        "summary": {
            "torch_version": torch.__version__,
            "grid_N8_physical_points": primary_grid["physical_points"],
            "horizontal_nonzero_rows_shrink": horizontal["nonzero_rhs_rows_strictly_shrink"],
            "smt": {"z3": z3_proof["verdict"], "cvc5": cvc5_proof["verdict"]},
            "all_pass": bool(all_pass),
        },
    }


def main() -> int:
    result = build_result()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": str(RESULT_PATH.relative_to(ROOT))}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
