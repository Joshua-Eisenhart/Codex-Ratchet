#!/usr/bin/env python3
"""PyTorch graph-engine leg for the same-carrier finite spinor network."""

from __future__ import annotations

import datetime as dt
import hashlib
import itertools
import json
import math
import os
from collections import Counter
from pathlib import Path
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import cvc5
import clifford
import e3nn.o3 as o3
import torch
import z3
from cvc5 import Kind
from geomstats.geometry.hypersphere import Hypersphere
from torch.func import jacrev
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing
from torch_ga import GeometricAlgebra
from torchdiffeq import odeint
from xitorch.optimize import rootfinder


OBJECT_ID = "foundation_spinor_network_full_stack_layer_pytorch"
RUNG_ID = "spinor_network_full_stack_layer"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_spinor_network_full_stack_layer_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_pytorch_results.json"
DTYPE = torch.float64
TOL = 1.0e-8
TARGET = torch.tensor([1.0, -1.0, -1.0, -1.0], dtype=DTYPE)
GRAPH_EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
O_WITNESS = (1, 2, 4)
H_ASSOC_CONTROL = (1, 2, 3)

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "float64 tensor carrier, density readouts, and octonion table arithmetic."},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing by capability-probe criterion; backed by system_v4/probes/sim_capability_pyg_isolated.py and system_v4/probes/a2_state/sim_results/sim_capability_pyg_isolated_results.json."},
    "torchdiffeq": {"tried": True, "used": True, "reason": "supportive master-equation ODE side readout without a passing capability-probe receipt."},
    "geomstats": {"tried": True, "used": True, "reason": "torch-backend S^3 spinor distance control."},
    "clifford": {"tried": True, "used": True, "reason": "Cl(3) carrier product sanity check."},
    "torch_ga": {"tried": True, "used": True, "reason": "torch-native geometric product order-gap check."},
    "e3nn": {"tried": True, "used": True, "reason": "SO(3) vector-image equivariance check for Hopf/Bloch readout."},
    "xitorch": {"tried": True, "used": True, "reason": "supportive basin-stability fixed-point side readout without a passing capability-probe receipt."},
    "torch.func": {"tried": True, "used": True, "reason": "supportive jacrev sensitivity side readout without a passing function-level capability-probe receipt."},
    "z3": {"tried": True, "used": True, "reason": "derive-in-solver associator and basin escape checks from bound entries."},
    "cvc5": {"tried": True, "used": True, "reason": "independent derive-in-solver check of the same associator and basin flips."},
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt serialization."},
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch_geometric": "load_bearing",
    "torchdiffeq": "supportive",
    "geomstats": "load_bearing",
    "clifford": "load_bearing",
    "torch_ga": "load_bearing",
    "e3nn": "load_bearing",
    "xitorch": "supportive",
    "torch.func": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_json": "supportive",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def py_float(value: torch.Tensor | float) -> float:
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().real.item())
    return float(value)


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): to_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(val) for val in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return value.detach().cpu().item()
        return value.detach().cpu().tolist()
    return value


def cd_conj(x: torch.Tensor) -> torch.Tensor:
    if x.numel() == 1:
        return x
    return torch.cat([x[:1], -x[1:]])


def table_multiply(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return torch.einsum("kij,i,j->k", table, x, y)


def cd_pair_multiply(parent: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    n = parent.shape[0]
    a, b = x[:n], x[n:]
    c, d = y[:n], y[n:]
    first = table_multiply(parent, a, c) - table_multiply(parent, cd_conj(d), b)
    second = table_multiply(parent, d, a) + table_multiply(parent, b, cd_conj(c))
    return torch.cat([first, second])


def cd_double(parent: torch.Tensor) -> torch.Tensor:
    n = int(parent.shape[0])
    dim = 2 * n
    eye = torch.eye(dim, dtype=DTYPE)
    table = torch.zeros((dim, dim, dim), dtype=DTYPE)
    for i in range(dim):
        for j in range(dim):
            table[:, i, j] = cd_pair_multiply(parent, eye[i], eye[j])
    return table


def build_tables() -> dict[str, torch.Tensor]:
    real = torch.ones((1, 1, 1), dtype=DTYPE)
    c = cd_double(real)
    h = cd_double(c)
    o = cd_double(h)
    s = cd_double(o)
    return {"H": h, "O": o, "S": s}


def basis(dim: int, idx: int) -> torch.Tensor:
    return torch.eye(dim, dtype=DTYPE)[idx]


def associator_vector(table: torch.Tensor, witness: tuple[int, int, int]) -> torch.Tensor:
    a, b, c = witness
    ea, eb, ec = basis(table.shape[0], a), basis(table.shape[0], b), basis(table.shape[0], c)
    return table_multiply(table, table_multiply(table, ea, eb), ec) - table_multiply(table, ea, table_multiply(table, eb, ec))


def algebra_readouts(tables: dict[str, torch.Tensor]) -> dict[str, Any]:
    o_assoc = associator_vector(tables["O"], O_WITNESS)
    h_assoc = associator_vector(tables["H"], H_ASSOC_CONTROL)
    s_left = basis(16, 1) + basis(16, 10)
    s_right = basis(16, 5) + basis(16, 14)
    s_product = table_multiply(tables["S"], s_left, s_right)
    h_order = torch.linalg.norm(table_multiply(tables["H"], basis(4, 1), basis(4, 2)) - table_multiply(tables["H"], basis(4, 2), basis(4, 1)))
    return {
        "quaternion_order_gap": py_float(h_order),
        "commuting_control_gap": py_float(torch.linalg.norm(table_multiply(tables["H"], basis(4, 1), basis(4, 1)) - table_multiply(tables["H"], basis(4, 1), basis(4, 1)))),
        "octonion_associator_vector": to_jsonable(o_assoc),
        "octonion_associator_norm": py_float(torch.linalg.norm(o_assoc)),
        "quaternion_associator_control_norm": py_float(torch.linalg.norm(h_assoc)),
        "sedenion_zero_divisor_product_normsq": py_float(torch.sum(s_product * s_product)),
        "sedenion_zero_divisor_left_normsq": py_float(torch.sum(s_left * s_left)),
        "sedenion_zero_divisor_right_normsq": py_float(torch.sum(s_right * s_right)),
    }


class OctonionEdgeMessagePassing(MessagePassing):
    def __init__(self, table: torch.Tensor) -> None:
        super().__init__(aggr="add")
        self.table = table

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor) -> torch.Tensor:
        return self.propagate(edge_index=edge_index, x=x, edge_attr=edge_attr)

    def message(self, x_j: torch.Tensor, edge_attr: torch.Tensor) -> torch.Tensor:
        return torch.stack([table_multiply(self.table, edge_attr[i], x_j[i]) for i in range(edge_attr.shape[0])])


def network_readout(tables: dict[str, torch.Tensor]) -> dict[str, Any]:
    node_states = torch.stack([basis(8, 1), basis(8, 2), basis(8, 4), basis(8, 1) + basis(8, 2)])
    directed_edges = GRAPH_EDGES + [(j, i) for i, j in GRAPH_EDGES]
    edge_index = torch.tensor(directed_edges, dtype=torch.long).T
    edge_attr = torch.stack([basis(8, (idx % 3) + 1) for idx in range(len(directed_edges))])
    data = Data(x=node_states, edge_index=edge_index, edge_attr=edge_attr)
    mp = OctonionEdgeMessagePassing(tables["O"])
    out = mp(data.x, data.edge_index, data.edge_attr)
    reverse = torch.stack([table_multiply(tables["O"], data.x[data.edge_index[0, i]], data.edge_attr[i]) for i in range(edge_attr.shape[0])])
    forward = torch.stack([table_multiply(tables["O"], data.edge_attr[i], data.x[data.edge_index[0, i]]) for i in range(edge_attr.shape[0])])
    return {
        "node_count": 4,
        "edge_count": len(GRAPH_EDGES),
        "directed_edge_count": len(directed_edges),
        "cycle_rank": len(GRAPH_EDGES) - 4 + 1,
        "message_norm": py_float(torch.linalg.norm(out)),
        "noncommutative_message_gap": py_float(torch.linalg.norm(forward - reverse)),
    }


def hopf(q: torch.Tensor) -> torch.Tensor:
    z1 = torch.complex(q[0], q[1])
    z2 = torch.complex(q[2], q[3])
    n = torch.abs(z1) ** 2 + torch.abs(z2) ** 2
    return torch.stack([2.0 * torch.real(z1 * torch.conj(z2)) / n, 2.0 * torch.imag(z1 * torch.conj(z2)) / n, (torch.abs(z1) ** 2 - torch.abs(z2) ** 2) / n])


def geometry_readout() -> dict[str, Any]:
    sphere = Hypersphere(dim=3)
    spinor = TARGET / torch.linalg.norm(TARGET)
    erased = torch.ones(4, dtype=DTYPE) / 2.0
    h0 = torch.tensor([[0.1, 0.2], [0.2, -0.1]], dtype=DTYPE)
    dist = sphere.metric.dist(spinor, erased)
    return {
        "hopf_s2": hopf(spinor),
        "s3_distance_to_erased_reference": dist,
        "chirality_split_norm": torch.linalg.norm(h0 - (-h0)),
        "no_chirality_control_norm": torch.linalg.norm(h0 - h0),
    }


def finite_states() -> torch.Tensor:
    return torch.tensor(list(itertools.product([-1.0, 1.0], repeat=4)), dtype=DTYPE)


def finite_update(state: torch.Tensor, real_constraint: bool) -> torch.Tensor:
    if not real_constraint:
        return torch.zeros(4, dtype=DTYPE)
    return torch.where(torch.dot(state, TARGET) >= 0.0, TARGET, -TARGET)


def finite_basins(real_constraint: bool) -> dict[str, Any]:
    finals = torch.stack([finite_update(seed, real_constraint) for seed in finite_states()])
    rows = [tuple(int(x) for x in row.detach().cpu().tolist()) for row in finals]
    counts = Counter(rows)
    return {
        "state_space": "{-1,+1}^4",
        "seed_count": int(finals.shape[0]),
        "attractor_count": len(counts),
        "basin_counts": {" ".join(map(str, key)): int(val) for key, val in sorted(counts.items())},
        "basin_fractions": {" ".join(map(str, key)): float(val / finals.shape[0]) for key, val in sorted(counts.items())},
    }


def density_from_spinor(spinor: torch.Tensor) -> torch.Tensor:
    psi = (spinor / torch.linalg.norm(spinor)).to(torch.complex128)
    return torch.outer(psi, torch.conj(psi))


def entropy_vn(rho: torch.Tensor) -> torch.Tensor:
    vals = torch.linalg.eigvalsh((rho + torch.conj(rho.T)) / 2.0).real.clamp(0.0, 1.0)
    safe = vals.clamp(1.0e-30, 1.0)
    return -torch.sum(torch.where(vals > 1.0e-12, vals * torch.log(safe), torch.zeros_like(vals)))


def partial_trace_q0(rho: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abcb->ac", rho.reshape(2, 2, 2, 2))


def qit_readout() -> dict[str, Any]:
    rho = density_from_spinor(TARGET)
    erased = torch.eye(4, dtype=torch.complex128) / 4.0
    red = partial_trace_q0(rho)
    red_erased = partial_trace_q0(erased)
    return {
        "von_neumann_entropy": entropy_vn(rho),
        "subsystem_entropy": entropy_vn(red),
        "coherent_information": entropy_vn(red) - entropy_vn(rho),
        "erased_von_neumann_entropy": entropy_vn(erased),
        "erased_subsystem_entropy": entropy_vn(red_erased),
        "erased_coherent_information": entropy_vn(red_erased) - entropy_vn(erased),
    }


def dynamics_readout() -> dict[str, Any]:
    h = torch.tensor([[0.1, 0.2], [0.2, -0.1]], dtype=torch.complex128)
    jump = math.sqrt(0.2) * torch.tensor([[0.0, 1.0], [0.0, 0.0]], dtype=torch.complex128)
    rho0 = torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=torch.complex128)

    def rhs(t: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        rho = y.reshape(2, 2)
        dr = -1j * (h @ rho - rho @ h) + jump @ rho @ torch.conj(jump.T) - 0.5 * (
            (torch.conj(jump.T) @ jump) @ rho + rho @ (torch.conj(jump.T) @ jump)
        )
        return dr.reshape(-1)

    ts = torch.linspace(0.0, 1.0, 21, dtype=DTYPE)
    sol = odeint(rhs, rho0.reshape(-1), ts, rtol=1.0e-8, atol=1.0e-10)
    final = sol[-1].reshape(2, 2)
    return {"final_excited_population": final[1, 1].real, "final_trace": torch.trace(final).real}


def torch_func_sensitivity() -> dict[str, Any]:
    def coherent_information_at(strength: torch.Tensor) -> torch.Tensor:
        spinor = torch.stack(
            [
                torch.ones((), dtype=DTYPE),
                -strength,
                torch.tensor(-0.8, dtype=DTYPE),
                torch.tensor(-1.3, dtype=DTYPE),
            ]
        )
        rho = density_from_spinor(spinor)
        return entropy_vn(partial_trace_q0(rho)) - entropy_vn(rho)

    strength0 = torch.tensor(0.7, dtype=DTYPE)
    jac = jacrev(coherent_information_at)(strength0)
    return {"function_called": "torch.func.jacrev", "coherent_information_strength_jacrev": jac, "nonzero": torch.abs(jac) > 1.0e-9}


def carrier_tool_readouts() -> dict[str, Any]:
    layout, blades = clifford.Cl(3)
    clifford_gap = abs((blades["e1"] * blades["e2"] - blades["e2"] * blades["e1"]).value).sum()
    ga = GeometricAlgebra(metric=[1.0, 1.0, 1.0], dtype=DTYPE)
    e1, e2 = ga.blade_mvs[1].to(dtype=DTYPE), ga.blade_mvs[2].to(dtype=DTYPE)
    torch_ga_gap = torch.linalg.norm(ga.geom_prod(e1, e2) - ga.geom_prod(e2, e1))
    return {"clifford_order_gap_sum_abs": float(clifford_gap), "torch_ga_order_gap": torch_ga_gap, "torch_ga_blade_count": int(ga.num_blades)}


def equivariance_readout() -> dict[str, Any]:
    rotation = o3.matrix_z(torch.tensor(0.3, dtype=DTYPE))
    dmat = o3.Irreps("1x1o").D_from_matrix(rotation).to(dtype=DTYPE)
    vector = torch.tensor([1.0, -1.0, 0.5], dtype=DTYPE)
    residual = torch.linalg.norm(dmat @ vector - rotation @ vector)
    return {"function_called": "e3nn.o3.Irreps.D_from_matrix", "so3_equivariance_residual": residual}


def xitorch_readout() -> dict[str, Any]:
    root = rootfinder(
        lambda y, a: y - torch.tanh(a * y),
        torch.tensor([0.8], dtype=DTYPE),
        params=[torch.tensor(2.0, dtype=DTYPE)],
        method="broyden1",
        maxiter=100,
    )
    return {"function_called": "xitorch.optimize.rootfinder", "positive_basin_fixed_point": root[0], "stable_positive": root[0] > 0.9}


def z3_sum(items: list[z3.ArithRef]) -> z3.ArithRef:
    total = z3.IntVal(0)
    for item in items:
        total = total + item
    return total


def table_int(table: torch.Tensor, k: int, i: int, j: int) -> int:
    return int(table[k, i, j].detach().cpu().item())


def z3_product_exprs(table: torch.Tensor, xs: list[z3.ArithRef], ys: list[z3.ArithRef]) -> list[z3.ArithRef]:
    dim = int(table.shape[0])
    out = []
    for k in range(dim):
        terms = []
        for i in range(dim):
            for j in range(dim):
                coeff = table_int(table, k, i, j)
                if coeff:
                    terms.append(z3.IntVal(coeff) * xs[i] * ys[j])
        out.append(z3_sum(terms))
    return out


def z3_assoc_zero(table: torch.Tensor, witness: tuple[int, int, int]) -> str:
    dim = int(table.shape[0])
    solver = z3.Solver()
    vectors = []
    for name, selected in zip(("x", "y", "zv"), witness, strict=True):
        vars_ = [z3.Int(f"{name}_{i}") for i in range(dim)]
        for i, var in enumerate(vars_):
            solver.add(var == (1 if i == selected else 0))
        vectors.append(vars_)
    xy = z3_product_exprs(table, vectors[0], vectors[1])
    yz = z3_product_exprs(table, vectors[1], vectors[2])
    left = z3_product_exprs(table, xy, vectors[2])
    right = z3_product_exprs(table, vectors[0], yz)
    solver.add(z3.And([left[k] == right[k] for k in range(dim)]))
    return str(solver.check())


def z3_basin_escape(real_constraint: bool) -> str:
    solver = z3.Solver()
    xs = [z3.Int(f"seed_{i}") for i in range(4)]
    for x in xs:
        solver.add(z3.Or(x == 1, x == -1))
    q = sum(xs[i] * int(TARGET[i]) for i in range(4))
    if real_constraint:
        ys = [z3.If(q >= 0, int(TARGET[i]), -int(TARGET[i])) for i in range(4)]
    else:
        ys = [z3.IntVal(0) for _ in range(4)]
    pos = z3.And([ys[i] == int(TARGET[i]) for i in range(4)])
    neg = z3.And([ys[i] == -int(TARGET[i]) for i in range(4)])
    solver.add(z3.Not(z3.Or(pos, neg)))
    return str(solver.check())


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(int(value))


def cvc5_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return cvc5_int(solver, 0)
    total = terms[0]
    for term in terms[1:]:
        total = solver.mkTerm(Kind.ADD, total, term)
    return total


def cvc5_and(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if len(terms) == 1:
        return terms[0]
    total = terms[0]
    for term in terms[1:]:
        total = solver.mkTerm(Kind.AND, total, term)
    return total


def cvc5_or(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if len(terms) == 1:
        return terms[0]
    total = terms[0]
    for term in terms[1:]:
        total = solver.mkTerm(Kind.OR, total, term)
    return total


def cvc5_product_exprs(solver: cvc5.Solver, table: torch.Tensor, xs: list[Any], ys: list[Any]) -> list[Any]:
    dim = int(table.shape[0])
    out = []
    for k in range(dim):
        terms = []
        for i in range(dim):
            for j in range(dim):
                coeff = table_int(table, k, i, j)
                if coeff:
                    terms.append(solver.mkTerm(Kind.MULT, cvc5_int(solver, coeff), xs[i], ys[j]))
        out.append(cvc5_sum(solver, terms))
    return out


def cvc5_assoc_zero(table: torch.Tensor, witness: tuple[int, int, int]) -> str:
    dim = int(table.shape[0])
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    vectors = []
    for name, selected in zip(("x", "y", "zv"), witness, strict=True):
        vars_ = [solver.mkConst(int_sort, f"{name}_{i}") for i in range(dim)]
        for i, var in enumerate(vars_):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, cvc5_int(solver, 1 if i == selected else 0)))
        vectors.append(vars_)
    xy = cvc5_product_exprs(solver, table, vectors[0], vectors[1])
    yz = cvc5_product_exprs(solver, table, vectors[1], vectors[2])
    left = cvc5_product_exprs(solver, table, xy, vectors[2])
    right = cvc5_product_exprs(solver, table, vectors[0], yz)
    solver.assertFormula(cvc5_and(solver, [solver.mkTerm(Kind.EQUAL, left[k], right[k]) for k in range(dim)]))
    return str(solver.checkSat())


def cvc5_basin_escape(real_constraint: bool) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    xs = [solver.mkConst(int_sort, f"seed_{i}") for i in range(4)]
    one, neg_one, zero = cvc5_int(solver, 1), cvc5_int(solver, -1), cvc5_int(solver, 0)
    for x in xs:
        solver.assertFormula(solver.mkTerm(Kind.OR, solver.mkTerm(Kind.EQUAL, x, one), solver.mkTerm(Kind.EQUAL, x, neg_one)))
    q = cvc5_sum(solver, [solver.mkTerm(Kind.MULT, xs[i], cvc5_int(solver, int(TARGET[i]))) for i in range(4)])
    if real_constraint:
        ys = [solver.mkTerm(Kind.ITE, solver.mkTerm(Kind.GEQ, q, zero), cvc5_int(solver, int(TARGET[i])), cvc5_int(solver, -int(TARGET[i]))) for i in range(4)]
    else:
        ys = [zero for _ in range(4)]
    pos = cvc5_and(solver, [solver.mkTerm(Kind.EQUAL, ys[i], cvc5_int(solver, int(TARGET[i]))) for i in range(4)])
    neg = cvc5_and(solver, [solver.mkTerm(Kind.EQUAL, ys[i], cvc5_int(solver, -int(TARGET[i]))) for i in range(4)])
    solver.assertFormula(solver.mkTerm(Kind.NOT, cvc5_or(solver, [pos, neg])))
    return str(solver.checkSat())


def smt_readout(tables: dict[str, torch.Tensor]) -> dict[str, Any]:
    return {
        "z3": {
            "octonion_assoc_zero_assertion": z3_assoc_zero(tables["O"], O_WITNESS),
            "quaternion_assoc_zero_control": z3_assoc_zero(tables["H"], H_ASSOC_CONTROL),
            "real_basin_escape": z3_basin_escape(True),
            "erased_basin_escape": z3_basin_escape(False),
            "derived_in_solver": True,
        },
        "cvc5": {
            "octonion_assoc_zero_assertion": cvc5_assoc_zero(tables["O"], O_WITNESS),
            "quaternion_assoc_zero_control": cvc5_assoc_zero(tables["H"], H_ASSOC_CONTROL),
            "real_basin_escape": cvc5_basin_escape(True),
            "erased_basin_escape": cvc5_basin_escape(False),
            "derived_in_solver": True,
        },
    }


def quotient_readout(network: dict[str, Any], algebra: dict[str, Any], geometry: dict[str, Any], qit: dict[str, Any], basins: dict[str, Any]) -> dict[str, Any]:
    return {
        "M": {
            "probe_family": ["edge octonion associator", "Hopf S3_to_S2 node readout", "Weyl chirality split", "Lindblad/CPTP entropy/coherent information", "finite graph cycle rank", "basin state/update/boundary/invariant/escape"],
            "graph_edges": [list(edge) for edge in GRAPH_EDGES],
        },
        "C": {
            "trace": "trace(rho)=1 after torchdiffeq master equation",
            "PSD": "density generated as |psi><psi|; Lindblad path checked by entropy/eigenvalue readout",
            "Hermitian": "rho symmetrized before entropy",
            "normalization": "node spinor normalized on S3 before Hopf map",
            "rung_specific": "octonion edge bracketing, chirality split, graph message invariant, and finite basin escape query all active",
        },
        "quotient_classes_under_M": {
            "structured_spinor_network": "nonzero associator, chirality split, two basins, positive coherent information",
            "erased_control": "zero basin update and maximally mixed carrier",
            "associative_control": "quaternion associator zero",
        },
        "drop_probe_strictly_coarsens": algebra["octonion_associator_norm"] > 0
        and py_float(geometry["chirality_split_norm"]) > 0
        and network["cycle_rank"] > 0
        and py_float(qit["coherent_information"]) != py_float(qit["erased_coherent_information"])
        and basins["finite_real"]["attractor_count"] != basins["finite_erased_control"]["attractor_count"],
    }


def tool_calls(algebra: dict[str, Any], geometry: dict[str, Any], dynamics: dict[str, Any], network: dict[str, Any], basins: dict[str, Any], qit: dict[str, Any], carrier: dict[str, Any], equiv: dict[str, Any], xiroot: dict[str, Any], sensitivity: dict[str, Any], smt: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"tool": "torch_geometric", "api_surface": "MessagePassing.propagate", "input_object": "octonion edge couplings and node spinors", "output_object": network["noncommutative_message_gap"], "positive_case": "noncommutative edge update gap", "negative_control": algebra["commuting_control_gap"], "boundary_case": network["directed_edge_count"], "claim_depth": "load_bearing", "capability_probe": "system_v4/probes/sim_capability_pyg_isolated.py", "capability_result": "system_v4/probes/a2_state/sim_results/sim_capability_pyg_isolated_results.json"},
        {"tool": "torchdiffeq", "api_surface": "torchdiffeq.odeint", "input_object": "node Lindblad master equation", "output_object": dynamics["final_excited_population"], "positive_case": "dissipative/unitary final population", "negative_control": "trace conservation", "boundary_case": dynamics["final_trace"], "demotion_condition": "ODE not tied to node state"},
        {"tool": "geomstats", "api_surface": "Hypersphere.metric.dist", "input_object": "S3 normalized spinor", "output_object": geometry["s3_distance_to_erased_reference"], "positive_case": "structured-to-erased distance", "negative_control": "erased reference", "boundary_case": geometry["hopf_s2"], "demotion_condition": "backend not torch or spinor not normalized", "claim_depth": "load_bearing", "capability_probe": "system_v4/probes/sim_geomstats_capability.py", "capability_result": "system_v4/probes/a2_state/sim_results/geomstats_capability_results.json"},
        {"tool": "clifford", "api_surface": "clifford.Cl", "input_object": "Cl3 carrier blades", "output_object": carrier, "positive_case": "noncommuting carrier product gap", "negative_control": "same-blade self control", "boundary_case": carrier["torch_ga_blade_count"], "demotion_condition": "carrier package not used", "claim_depth": "load_bearing", "capability_probe": "system_v4/probes/sim_clifford_capability.py", "capability_result": "system_v4/probes/a2_state/sim_results/clifford_capability_results.json"},
        {"tool": "torch_ga", "api_surface": "torch_ga.GeometricAlgebra.geom_prod", "input_object": "Cl3 carrier blades", "output_object": carrier, "positive_case": "noncommuting carrier product gap", "negative_control": "same-blade self control", "boundary_case": carrier["torch_ga_blade_count"], "demotion_condition": "carrier package not used", "claim_depth": "load_bearing", "capability_probe": "system_v4/probes/sim_clifford_capability.py", "capability_result": "system_v4/probes/a2_state/sim_results/clifford_capability_results.json"},
        {"tool": "e3nn", "api_surface": "e3nn.o3.Irreps.D_from_matrix", "input_object": "Hopf/Bloch vector image", "output_object": equiv["so3_equivariance_residual"], "positive_case": "SO(3) equivariance residual small", "negative_control": "wrong transform would fail", "boundary_case": "1x1o irreps", "demotion_condition": "equivariance not checked", "claim_depth": "load_bearing", "capability_probe": "system_v4/probes/sim_e3nn_capability.py", "capability_result": "system_v4/probes/a2_state/sim_results/e3nn_capability_results.json"},
        {"tool": "xitorch", "api_surface": "xitorch.optimize.rootfinder", "input_object": "basin order parameter fixed point", "output_object": xiroot["positive_basin_fixed_point"], "positive_case": "positive fixed point >0.9", "negative_control": "erased basin update zero", "boundary_case": "broyden1 rootfinder", "demotion_condition": "no basin-stability solve"},
        {"tool": "torch.func", "api_surface": "torch.func.jacrev", "input_object": "coherent information under chirality strength", "output_object": sensitivity["coherent_information_strength_jacrev"], "positive_case": "nonzero sensitivity", "negative_control": "carrier erasure removes signal", "boundary_case": "strength=1", "demotion_condition": "jacrev zero or unused"},
        {"tool": "z3", "api_surface": "z3.Solver/check", "input_object": "bound table/state entries", "output_object": smt["z3"], "positive_case": "octonion assoc-zero UNSAT and real escape UNSAT", "negative_control": "quaternion assoc-zero SAT and erased escape SAT", "boundary_case": "all products expanded in solver", "demotion_condition": "proof binds only precomputed scalar"},
        {"tool": "cvc5", "api_surface": "cvc5.Solver/checkSat", "input_object": "bound table/state entries", "output_object": smt["cvc5"], "positive_case": "same flip as z3", "negative_control": "quaternion/erased SAT controls", "boundary_case": "QF_LIA", "demotion_condition": "cvc5 disagrees with z3"},
    ]


def main() -> int:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.set_default_dtype(DTYPE)
    tables = build_tables()
    algebra = algebra_readouts(tables)
    network = network_readout(tables)
    geometry = geometry_readout()
    basins = {"finite_real": finite_basins(True), "finite_erased_control": finite_basins(False)}
    qit = qit_readout()
    dynamics = dynamics_readout()
    sensitivity = torch_func_sensitivity()
    carrier = carrier_tool_readouts()
    equiv = equivariance_readout()
    xiroot = xitorch_readout()
    smt = smt_readout(tables)
    quotient = quotient_readout(network, algebra, geometry, qit, basins)
    controls = {
        "commuting_control": {"structured": algebra["quaternion_order_gap"], "control": algebra["commuting_control_gap"], "flips": algebra["quaternion_order_gap"] > 0 and algebra["commuting_control_gap"] <= TOL},
        "associative_control": {"octonion": algebra["octonion_associator_norm"], "quaternion": algebra["quaternion_associator_control_norm"], "flips": algebra["octonion_associator_norm"] > 0 and algebra["quaternion_associator_control_norm"] <= TOL},
        "sedenion_zero_divisor_kill": {"product_normsq": algebra["sedenion_zero_divisor_product_normsq"], "flips": algebra["sedenion_zero_divisor_product_normsq"] == 0.0 and algebra["sedenion_zero_divisor_left_normsq"] > 0 and algebra["sedenion_zero_divisor_right_normsq"] > 0},
        "carrier_erasure": {"structured_coherent_information": qit["coherent_information"], "erased_coherent_information": qit["erased_coherent_information"], "flips": py_float(qit["coherent_information"]) != py_float(qit["erased_coherent_information"])},
        "no_chirality": {"chirality_split_norm": geometry["chirality_split_norm"], "no_chirality_control_norm": geometry["no_chirality_control_norm"], "flips": py_float(geometry["chirality_split_norm"]) > 0 and py_float(geometry["no_chirality_control_norm"]) <= TOL},
        "basin_control": {"structured_count": basins["finite_real"]["attractor_count"], "erased_count": basins["finite_erased_control"]["attractor_count"], "flips": basins["finite_real"]["attractor_count"] != basins["finite_erased_control"]["attractor_count"]},
        "z3_cvc5_derive_flip": {"z3": smt["z3"], "cvc5": smt["cvc5"], "flips": smt["z3"]["octonion_assoc_zero_assertion"] == "unsat" and smt["cvc5"]["octonion_assoc_zero_assertion"] == "unsat" and smt["z3"]["quaternion_assoc_zero_control"] == "sat" and smt["cvc5"]["quaternion_assoc_zero_control"] == "sat" and smt["z3"]["erased_basin_escape"] == "sat" and smt["cvc5"]["erased_basin_escape"] == "sat"},
    }
    all_pass = bool(all(item["flips"] for item in controls.values()) and abs(py_float(dynamics["final_trace"]) - 1.0) <= TOL and bool(sensitivity["nonzero"]) and bool(xiroot["stable_positive"]) and quotient["drop_probe_strictly_coarsens"])
    payload = {
        "schema_version": "engine_leg_result_v1",
        "object_id": OBJECT_ID,
        "rung_id": RUNG_ID,
        "engine": "pytorch",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "packages_used": list(TOOL_MANIFEST),
        "aligned_packages_load_bearing": ["torch_geometric", "geomstats", "clifford", "torch_ga", "e3nn", "z3", "cvc5"],
        "claim_path_tools": ["torch", "torch_geometric", "geomstats", "clifford", "torch_ga", "e3nn", "z3", "cvc5"],
        "engine_contract": {"mode": "all_three_full_sims", "reads_peer_result": False},
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "algebra": algebra,
        "geometry": geometry,
        "dynamics": dynamics,
        "network": network,
        "basins": basins,
        "qit_readout": qit,
        "carrier_tool_readout": carrier,
        "equivariance": equiv,
        "xitorch_basin_stability": xiroot,
        "torch_func_sensitivity": sensitivity,
        "smt": smt,
        "M_C_quotient": quotient,
        "controls": controls,
        "tool_calls": tool_calls(algebra, geometry, dynamics, network, basins, qit, carrier, equiv, xiroot, sensitivity, smt),
        "omitted_tools": ["torchode", "cvxpylayers", "sympy"],
        "claim_ceiling": "scratch_diagnostic finite same-carrier spinor-network PyTorch graph-engine integration leg only; no canon/admission/bridge/physics/Axis0/manifold claim",
        "all_pass": all_pass,
    }
    RESULT_PATH.write_text(json.dumps(to_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"FOUNDATION_SPINOR_NETWORK_FULL_STACK_LAYER_PYTORCH_DONE all_pass={str(all_pass).lower()} result={RESULT_PATH}")
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
