#!/usr/bin/env python3
"""PyTorch leg for terrain_spinor_shell_nest_v0."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import cvc5
from cvc5 import Kind
import clifford
from e3nn import o3
from geomstats.geometry.hypersphere import Hypersphere
import sympy as sp
import torch
from torch.func import jacrev, vmap
from torch_geometric.data import Data
from torch_geometric.utils import degree
import z3

from terrain_spinor_shell_nest_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    SEED,
    SIM_DIR,
    SIM_ID,
    TOL,
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


ENGINE = "pytorch"
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"
READS_PEER_RESULT = False
DTYPE = torch.float64
PACKAGES_USED = ["torch", "torch.func", "torch_geometric", "geomstats", "e3nn", "clifford", "sympy", "z3", "cvc5", "pathlib"]
ALIGNED_PACKAGES_LOAD_BEARING = ["torch.func", "sympy", "z3", "cvc5"]
TOOL_MANIFEST = {
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev/vmap derivative row for shell coordinate leakage"},
    "torch_geometric": {"tried": True, "used": True, "reason": "supportive graph support degree capability row for the three shell sites; not a nesting gate"},
    "geomstats": {"tried": True, "used": True, "reason": "supportive Hypersphere distance capability row for shell geometry support; not a nesting gate"},
    "e3nn": {"tried": True, "used": True, "reason": "supportive O(3) irrep dimension capability row for scalar/vector shell features; not a nesting gate"},
    "clifford": {"tried": True, "used": True, "reason": "supportive Cl(3) bivector carrier capability row for spinor/shell geometry; not a nesting gate"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact derivative sign row for z=cos(2 eta)"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing erased-placement SMT contradiction over computed non-preserve class count"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent erased-placement SMT contradiction over computed non-preserve class count"},
    "torch": {"tried": True, "used": True, "reason": "supportive float64 tensor arithmetic and matrix exponential check"},
}
TOOL_INTEGRATION_DEPTH = {
    "torch.func": "load_bearing",
    "torch_geometric": "supportive",
    "geomstats": "supportive",
    "e3nn": "supportive",
    "clifford": "supportive",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "torch": "supportive",
}


def graph_geometry_receipt() -> dict[str, Any]:
    edge_index = torch.tensor([[0, 1, 0], [1, 2, 2]], dtype=torch.long)
    data = Data(edge_index=edge_index, num_nodes=3)
    deg = degree(data.edge_index.reshape(-1), num_nodes=data.num_nodes, dtype=DTYPE)
    sphere = Hypersphere(dim=2)
    p = torch.tensor([1.0, 0.0, 0.0], dtype=DTYPE)
    q = torch.tensor([0.0, 1.0, 0.0], dtype=DTYPE)
    dist = sphere.metric.dist(p, q)
    irreps = o3.Irreps("1x0e + 1x1o")
    layout, blades = clifford.Cl(3)
    bivector = blades["e1"] * blades["e2"]
    return {
        "torch_geometric": {"node_count": int(data.num_nodes), "edge_count": int(data.num_edges), "degree": [r12(x) for x in deg.tolist()]},
        "geomstats": {"backend": os.environ.get("GEOMSTATS_BACKEND"), "orthogonal_distance": r12(dist)},
        "e3nn": {"irreps": str(irreps), "feature_dim": int(irreps.dim)},
        "clifford": {"vector_dimension": int(layout.dims), "blade_count": len(blades), "bivector": str(bivector)},
        "pass": int(data.num_nodes) == 3 and int(data.num_edges) == 3 and int(irreps.dim) == 4 and int(layout.dims) == 3 and "e12" in str(bivector),
    }


def leakage_derivative_receipt(core: dict[str, Any]) -> dict[str, Any]:
    etas = torch.tensor([float(site["eta"]) for site in core["shell_sites"]], dtype=DTYPE)
    rates = torch.tensor([0.05, -0.02, 0.01], dtype=DTYPE)

    def leakage_fn(eta: torch.Tensor, rate: torch.Tensor) -> torch.Tensor:
        return -2.0 * torch.sin(2.0 * eta) * rate

    derivs = vmap(jacrev(lambda eta, rate: leakage_fn(eta, rate)), in_dims=(0, 0))(etas, rates)
    values = vmap(leakage_fn, in_dims=(0, 0))(etas, rates)
    return {
        "tool": "torch.func.jacrev/vmap",
        "z_dot": [r12(x) for x in values.tolist()],
        "dz_dot_deta": [r12(x) for x in derivs.tolist()],
        "nonzero_count": int(torch.sum(torch.abs(values) > TOL).item()),
        "pass": bool(torch.linalg.norm(values) > TOL and torch.isfinite(derivs).all()),
    }


def sympy_receipt() -> dict[str, Any]:
    eta = sp.symbols("eta", real=True)
    expr = sp.simplify(sp.diff(sp.cos(2 * eta), eta) + 2 * sp.sin(2 * eta))
    return {"tool": "sympy.diff/simplify", "identity_residual": sp.sstr(expr), "pass": expr == 0}


def torch_matrix_receipt() -> dict[str, Any]:
    aug = torch.tensor(
        [
            [-0.8, -0.2309401076758503, 0.2309401076758503, 0.0],
            [0.2309401076758503, -0.8, -0.2309401076758503, 0.0],
            [-0.2309401076758503, 0.2309401076758503, -0.8, 0.0],
            [0.0, 0.0, 0.0, 0.0],
        ],
        dtype=DTYPE,
    )
    start = torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=DTYPE)
    out = torch.linalg.matrix_exp(aug) @ start
    return {"tool": "torch.linalg.matrix_exp", "norm": r12(torch.linalg.norm(out[:3]).item()), "pass": bool(torch.isfinite(out).all())}


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
    torch.manual_seed(SEED)
    core = build_core_nest()
    actual = int(core["smt_identity_values"]["actual_non_preserve_shell_site_count"])
    erased = int(core["smt_identity_values"]["erased_no_placement_non_preserve_count"])
    z3_proof = z3_erased_flip_proof_local(actual, erased)
    cvc5_proof = cvc5_erased_flip_proof_local(actual, erased)
    graph_geometry = graph_geometry_receipt()
    derivative = leakage_derivative_receipt(core)
    sympy_row = sympy_receipt()
    matrix_row = torch_matrix_receipt()
    acceptance = {
        "core_nest_pass": core["all_pass"] is True,
        "leakage_derivative": derivative["pass"] is True,
        "sympy_identity": sympy_row["pass"] is True,
        "smt_z3": z3_proof["pass"] is True,
        "smt_cvc5": cvc5_proof["pass"] is True,
        "matrix_exponential_finite": matrix_row["pass"] is True,
        "ceiling": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
    }
    supportive_checks = {
        "graph_geometry": graph_geometry["pass"] is True,
    }
    tool_calls = [
        tool_call("torch.func", "torch.func.jacrev/vmap", "shell eta vector and bounded terrain rates", derivative, "nonzero shell leakage derivative", "zero rate erases derivative", "eta=pi/4 finite derivative", "if derivative is zero for every site, demote shell leakage row", ["level_c_shell"]),
        tool_call("torch_geometric", "torch_geometric.data.Data/degree", "three shell sites and edge index", graph_geometry["torch_geometric"], "three-site support graph exists", "drop edges to erase graph support", "one node remains valid but not n=3 support", "support row only; no nesting gate", []),
        tool_call("geomstats", "geomstats.geometry.hypersphere.Hypersphere.metric.dist", "orthogonal shell support points", graph_geometry["geomstats"], "finite sphere distance", "coincident points erase distance", "pi/2 orthogonal boundary", "support row only; no nesting gate", []),
        tool_call("e3nn", "e3nn.o3.Irreps", "scalar plus vector shell feature declaration", graph_geometry["e3nn"], "feature dimension is 4", "scalar-only erases vector channel", "0e+1o boundary", "support row only; no nesting gate", []),
        tool_call("clifford", "clifford.Cl", "Cl(3) bivector support carrier", graph_geometry["clifford"], "bivector row exists", "scalar-only row erases bivector", "Cl(3) dimension boundary", "support row only; no nesting gate", []),
        tool_call("sympy", "sympy.diff/simplify", "z=cos(2 eta)", sympy_row, "closed derivative has zero residual", "wrong coordinate gives nonzero residual", "eta=pi/4 boundary", "if symbolic residual is nonzero, demote shell coordinate", ["shell_coordinate"]),
        tool_call("z3", "z3.Solver/check", "computed non-preserve count and erased no-placement count", z3_proof, "actual count differs from erased count", "erased count bound to actual zero count", "actual=0 control is satisfiable", "if erased flip does not change verdict, demote proof", ["crossover_proofs"]),
        tool_call("cvc5", "cvc5.Solver/checkSat", "computed non-preserve count and erased no-placement count", cvc5_proof, "actual count differs from erased count", "erased count bound to actual zero count", "actual=0 control is satisfiable", "if erased flip does not change verdict, demote proof", ["crossover_proofs"]),
    ]
    return {
        "schema_version": f"{SIM_ID}.{ENGINE}_result.v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "role_id": "pytorch_graph_network_sim_builder",
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
        "package_versions": {name: package_version(name) for name in ["torch", "torch-geometric", "geomstats", "e3nn", "clifford", "sympy", "z3-solver", "cvc5"]},
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": tool_calls,
        "capability_receipts": {
            "graph_geometry": graph_geometry,
            "leakage_derivative": derivative,
            "sympy_receipt": sympy_row,
            "torch_matrix_receipt": matrix_row,
        },
        "load_bearing_decomposition": core["load_bearing_decomposition"],
        "three_level_property_matrix": core["three_level_property_matrix"],
        "si_frame_row": core["si_frame_row"],
        "controls": core["controls"],
        "smt_identity_values": core["smt_identity_values"],
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "acceptance": acceptance,
        "supportive_checks": supportive_checks,
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
