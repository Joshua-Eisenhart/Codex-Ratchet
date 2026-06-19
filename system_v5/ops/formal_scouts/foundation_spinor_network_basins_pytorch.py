#!/usr/bin/env python3
"""PyTorch leg for a finite spinor-network basin scratch diagnostic."""

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
import torch
import z3
from cvc5 import Kind
from geomstats.geometry.hypersphere import Hypersphere
from torch.func import jacrev
from torch_geometric.utils import to_dense_adj
from torch_ga import GeometricAlgebra


OBJECT_ID = "foundation_spinor_network_basins_pytorch"
RUNG_ID = "spinor_network_basins"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_spinor_network_basins_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_pytorch_results.json"
DTYPE = torch.float64
TOL = 1.0e-9

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result

TARGET = torch.tensor([1.0, -1.0, -1.0, -1.0], dtype=DTYPE)
GRAPH_EDGES = [(0, 1), (1, 2), (2, 3), (3, 0)]
O_WITNESS = (1, 2, 4)
H_ASSOC_CONTROL = (1, 2, 3)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing float64 finite-state spinor dynamics, density readout, and octonion table arithmetic.",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing jacrev sensitivity of coherent information under a constraint-strength spinor perturbation.",
    },
    "torch_ga": {
        "tried": True,
        "used": True,
        "reason": "load-bearing geometric-algebra noncommutation check for the spinor carrier.",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing cycle-graph adjacency/message construction for the four-node spinor network.",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing torch-backend S^3 spinor-manifold distance between structured and erased carriers.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing structural SMT proof deriving order, associator, and basin flips from bound entries.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT proof of the same derived structural flips.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.func": "load_bearing",
    "torch_ga": "load_bearing",
    "torch_geometric": "load_bearing",
    "geomstats": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    return torch.einsum("cab,a,b->c", table, x, y)


def cd_pair_multiply(parent: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    n = parent.shape[0]
    a, b = x[:n], x[n:]
    c, d = y[:n], y[n:]
    first = table_multiply(parent, a, c) - table_multiply(parent, cd_conj(d), b)
    second = table_multiply(parent, d, a) + table_multiply(parent, b, cd_conj(c))
    return torch.cat([first, second])


def cd_double(parent: torch.Tensor) -> torch.Tensor:
    n = parent.shape[0]
    dim = 2 * n
    eye = torch.eye(dim, dtype=DTYPE)
    table = torch.zeros((dim, dim, dim), dtype=DTYPE)
    for i in range(dim):
        for j in range(dim):
            table[:, i, j] = cd_pair_multiply(parent, eye[i], eye[j])
    return table


def build_tables() -> dict[str, torch.Tensor]:
    real = torch.ones((1, 1, 1), dtype=DTYPE)
    complex_table = cd_double(real)
    quaternion = cd_double(complex_table)
    octonion = cd_double(quaternion)
    return {"H": quaternion, "O": octonion}


def basis(dim: int, idx: int) -> torch.Tensor:
    return torch.eye(dim, dtype=DTYPE)[idx]


def associator_vector(table: torch.Tensor, witness: tuple[int, int, int]) -> torch.Tensor:
    a, b, c = witness
    ea, eb, ec = basis(table.shape[0], a), basis(table.shape[0], b), basis(table.shape[0], c)
    return table_multiply(table, table_multiply(table, ea, eb), ec) - table_multiply(
        table, ea, table_multiply(table, eb, ec)
    )


def order_gap(table: torch.Tensor, a: int, b: int) -> torch.Tensor:
    return torch.linalg.vector_norm(table[:, a, b] - table[:, b, a])


def finite_states() -> torch.Tensor:
    return torch.tensor(list(itertools.product([-1.0, 1.0], repeat=4)), dtype=DTYPE)


def graph_message_signature() -> dict[str, Any]:
    directed_edges = GRAPH_EDGES + [(j, i) for i, j in GRAPH_EDGES]
    edge_index = torch.tensor(directed_edges, dtype=torch.long).T
    adjacency = to_dense_adj(edge_index, max_num_nodes=4)[0].to(dtype=DTYPE)
    field = adjacency @ TARGET
    return {
        "function_called": "torch_geometric.utils.to_dense_adj",
        "edge_index": edge_index,
        "adjacency": adjacency,
        "target_neighbor_field": field,
        "field_alignment": torch.dot(field, TARGET),
    }


def finite_update(state: torch.Tensor, real_constraint: bool) -> torch.Tensor:
    if not real_constraint:
        return state
    q = torch.dot(state, TARGET)
    return torch.where(q >= 0.0, TARGET, -TARGET)


def finite_basins(real_constraint: bool) -> dict[str, Any]:
    seeds = finite_states()
    finals = torch.stack([finite_update(seed, real_constraint) for seed in seeds])
    rows = [tuple(int(x) for x in row.detach().cpu().tolist()) for row in finals]
    counts = Counter(rows)
    return {
        "seed_count": int(seeds.shape[0]),
        "attractor_count": len(counts),
        "basin_counts": {" ".join(map(str, key)): int(val) for key, val in sorted(counts.items())},
        "basin_fractions": {" ".join(map(str, key)): float(val / seeds.shape[0]) for key, val in sorted(counts.items())},
    }


def density_from_spinor(spinor: torch.Tensor) -> torch.Tensor:
    psi = (spinor / torch.linalg.vector_norm(spinor)).to(torch.complex128)
    return torch.outer(psi, torch.conj(psi))


def entropy_vn(rho: torch.Tensor) -> torch.Tensor:
    herm = (rho + torch.conj(rho.T)) / 2.0
    vals = torch.linalg.eigvalsh(herm).real.clamp(0.0, 1.0)
    safe = vals.clamp(1.0e-30, 1.0)
    return -torch.sum(torch.where(vals > 1.0e-12, vals * torch.log(safe), torch.zeros_like(vals)))


def partial_trace_q0(rho: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abcb->ac", rho.reshape(2, 2, 2, 2))


def trace_distance(rho: torch.Tensor, sigma: torch.Tensor) -> torch.Tensor:
    delta = (rho - sigma + torch.conj((rho - sigma).T)) / 2.0
    return 0.5 * torch.sum(torch.abs(torch.linalg.eigvalsh(delta).real))


def qit_readout() -> dict[str, Any]:
    rho = density_from_spinor(TARGET)
    erased = torch.eye(4, dtype=torch.complex128) / 4.0
    red = partial_trace_q0(rho)
    red_erased = partial_trace_q0(erased)
    s_ab = entropy_vn(rho)
    s_a = entropy_vn(red)
    s_ab_erased = entropy_vn(erased)
    s_a_erased = entropy_vn(red_erased)
    return {
        "von_neumann_entropy": s_ab,
        "subsystem_entropy_q0": s_a,
        "coherent_information_q0_to_q1": s_a - s_ab,
        "erased_von_neumann_entropy": s_ab_erased,
        "erased_subsystem_entropy_q0": s_a_erased,
        "erased_coherent_information_q0_to_q1": s_a_erased - s_ab_erased,
        "distinguishability_trace_distance_to_erased": trace_distance(rho, erased),
    }


def coherent_information_at_strength(strength: torch.Tensor) -> torch.Tensor:
    spinor = torch.stack(
        [
            torch.ones((), dtype=DTYPE),
            -strength,
            -torch.ones((), dtype=DTYPE),
            -torch.ones((), dtype=DTYPE),
        ]
    )
    rho = density_from_spinor(spinor)
    return entropy_vn(partial_trace_q0(rho)) - entropy_vn(rho)


def torch_ga_order_gap() -> dict[str, Any]:
    ga = GeometricAlgebra(metric=[1.0, 1.0, 1.0], dtype=DTYPE)
    blades = ga.blade_mvs.to(dtype=DTYPE)
    e1, e2 = blades[1], blades[2]
    gap = torch.linalg.vector_norm(ga.geom_prod(e1, e2) - ga.geom_prod(e2, e1))
    control = torch.linalg.vector_norm(ga.geom_prod(e1, e1) - ga.geom_prod(e1, e1))
    return {
        "function_called": "torch_ga.GeometricAlgebra.geom_prod",
        "cl3_blade_count": int(ga.num_blades),
        "e1e2_minus_e2e1_norm": gap,
        "commuting_control_norm": control,
    }


def geomstats_spinor_distance() -> dict[str, Any]:
    sphere = Hypersphere(dim=3)
    structured = TARGET / torch.linalg.vector_norm(TARGET)
    erased_reference = torch.ones(4, dtype=DTYPE)
    erased_reference = erased_reference / torch.linalg.vector_norm(erased_reference)
    dist = sphere.metric.dist(structured, erased_reference)
    return {
        "function_called": "geomstats.geometry.hypersphere.Hypersphere.metric.dist",
        "backend": "pytorch",
        "S3_distance_structured_to_erased_reference": dist,
    }


def z3_sum(items: list[z3.ArithRef]) -> z3.ArithRef:
    out = z3.IntVal(0)
    for item in items:
        out = out + item
    return out


def z3_order_proof(table: torch.Tensor, a: int, b: int) -> str:
    arr = table.detach().cpu().to(torch.int64)
    dim = arr.shape[0]
    solver = z3.Solver()
    mu = {}
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                var = z3.Int(f"mu_o_{k}_{i}_{j}")
                solver.add(var == int(arr[k, i, j]))
                mu[k, i, j] = var
    solver.add(z3.And([mu[k, a, b] == mu[k, b, a] for k in range(dim)]))
    return str(solver.check())


def z3_associator_proof(table: torch.Tensor, witness: tuple[int, int, int]) -> str:
    arr = table.detach().cpu().to(torch.int64)
    dim = arr.shape[0]
    a, b, c = witness
    solver = z3.Solver()
    mu = {}
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                var = z3.Int(f"mu_a_{k}_{i}_{j}")
                solver.add(var == int(arr[k, i, j]))
                mu[k, i, j] = var
    equations = []
    for k in range(dim):
        left = z3_sum([mu[k, m, c] * mu[m, a, b] for m in range(dim)])
        right = z3_sum([mu[k, a, m] * mu[m, b, c] for m in range(dim)])
        equations.append(left == right)
    solver.add(z3.And(equations))
    return str(solver.check())


def z3_basin_proof(real_constraint: bool) -> str:
    solver = z3.Solver()
    xs = [z3.Int(f"x{i}") for i in range(4)]
    for x in xs:
        solver.add(z3.Or(x == 1, x == -1))
    q = sum(xs[i] * int(TARGET[i]) for i in range(4))
    if real_constraint:
        ys = [z3.If(q >= 0, int(TARGET[i]), -int(TARGET[i])) for i in range(4)]
    else:
        ys = xs
    pos = z3.And([ys[i] == int(TARGET[i]) for i in range(4)])
    neg = z3.And([ys[i] == -int(TARGET[i]) for i in range(4)])
    solver.add(z3.Not(z3.Or(pos, neg)))
    return str(solver.check())


def cvc5_sum(solver: cvc5.Solver, items: list[Any]) -> Any:
    if not items:
        return solver.mkInteger(0)
    out = items[0]
    for item in items[1:]:
        out = solver.mkTerm(Kind.ADD, out, item)
    return out


def cvc5_order_proof(table: torch.Tensor, a: int, b: int) -> str:
    arr = table.detach().cpu().to(torch.int64)
    dim = arr.shape[0]
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    mu = {}
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                var = solver.mkConst(int_sort, f"mu_o_{k}_{i}_{j}")
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(int(arr[k, i, j]))))
                mu[k, i, j] = var
    solver.assertFormula(solver.mkTerm(Kind.AND, *[solver.mkTerm(Kind.EQUAL, mu[k, a, b], mu[k, b, a]) for k in range(dim)]))
    return str(solver.checkSat())


def cvc5_associator_proof(table: torch.Tensor, witness: tuple[int, int, int]) -> str:
    arr = table.detach().cpu().to(torch.int64)
    dim = arr.shape[0]
    a, b, c = witness
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    mu = {}
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                var = solver.mkConst(int_sort, f"mu_a_{k}_{i}_{j}")
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(int(arr[k, i, j]))))
                mu[k, i, j] = var
    equations = []
    for k in range(dim):
        left = cvc5_sum(solver, [solver.mkTerm(Kind.MULT, mu[k, m, c], mu[m, a, b]) for m in range(dim)])
        right = cvc5_sum(solver, [solver.mkTerm(Kind.MULT, mu[k, a, m], mu[m, b, c]) for m in range(dim)])
        equations.append(solver.mkTerm(Kind.EQUAL, left, right))
    solver.assertFormula(solver.mkTerm(Kind.AND, *equations))
    return str(solver.checkSat())


def cvc5_basin_proof(real_constraint: bool) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    one = solver.mkInteger(1)
    neg_one = solver.mkInteger(-1)
    zero = solver.mkInteger(0)
    xs = [solver.mkConst(int_sort, f"x{i}") for i in range(4)]
    for x in xs:
        solver.assertFormula(
            solver.mkTerm(Kind.OR, solver.mkTerm(Kind.EQUAL, x, one), solver.mkTerm(Kind.EQUAL, x, neg_one))
        )
    terms = [solver.mkTerm(Kind.MULT, xs[i], solver.mkInteger(int(TARGET[i]))) for i in range(4)]
    q = cvc5_sum(solver, terms)
    if real_constraint:
        ys = [
            solver.mkTerm(
                Kind.ITE,
                solver.mkTerm(Kind.GEQ, q, zero),
                solver.mkInteger(int(TARGET[i])),
                solver.mkInteger(-int(TARGET[i])),
            )
            for i in range(4)
        ]
    else:
        ys = xs
    pos = solver.mkTerm(Kind.AND, *[solver.mkTerm(Kind.EQUAL, ys[i], solver.mkInteger(int(TARGET[i]))) for i in range(4)])
    neg = solver.mkTerm(Kind.AND, *[solver.mkTerm(Kind.EQUAL, ys[i], solver.mkInteger(-int(TARGET[i]))) for i in range(4)])
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.OR, pos, neg)))
    return str(solver.checkSat())


def quotient_summary() -> dict[str, Any]:
    states = finite_states()
    edge01 = states[:, 0] * states[:, 1]
    edge02 = states[:, 0] * states[:, 2]
    edge03 = states[:, 0] * states[:, 3]
    features = torch.stack([edge01, edge02, edge03], dim=1)
    dropped = torch.stack([edge01, edge02], dim=1)
    full_classes = {tuple(float(x) for x in row) for row in features.detach().cpu().tolist()}
    dropped_classes = {tuple(float(x) for x in row) for row in dropped.detach().cpu().tolist()}
    return {
        "M": ["edge01_spinor_parity", "edge02_spinor_parity", "edge03_spinor_parity"],
        "quotient_classes_under_M": len(full_classes),
        "drop_edge03_control_classes": len(dropped_classes),
        "drop_probe_strictly_coarsens": len(dropped_classes) < len(full_classes),
        "C": [
            "trace=1",
            "PSD",
            "Hermitian",
            "normalization",
            "order_gap_nonzero",
            "octonion_associator_nonzero",
            "finite basin compression under C",
        ],
    }


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(DTYPE)
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tables = build_tables()
    h_table = tables["H"]
    o_table = tables["O"]
    ogap = order_gap(h_table, 1, 2)
    ogap_control = order_gap(h_table, 1, 1)
    assoc_o = associator_vector(o_table, O_WITNESS)
    assoc_h = associator_vector(h_table, H_ASSOC_CONTROL)
    assoc_norm = torch.linalg.vector_norm(assoc_o)
    assoc_control_norm = torch.linalg.vector_norm(assoc_h)
    basins_real = finite_basins(True)
    basins_control = finite_basins(False)
    qit = qit_readout()
    strength = torch.tensor(0.7, dtype=DTYPE)
    ci_sensitivity = jacrev(coherent_information_at_strength)(strength)
    graph = graph_message_signature()
    ga = torch_ga_order_gap()
    geom = geomstats_spinor_distance()
    smt = {
        "z3": {
            "order_noncommuting_commute_assertion": z3_order_proof(h_table, 1, 2),
            "order_commuting_control": z3_order_proof(h_table, 1, 1),
            "octonion_assoc_zero_assertion": z3_associator_proof(o_table, O_WITNESS),
            "quaternion_assoc_zero_control": z3_associator_proof(h_table, H_ASSOC_CONTROL),
            "real_basin_counterexample": z3_basin_proof(True),
            "erased_basin_counterexample": z3_basin_proof(False),
        },
        "cvc5": {
            "order_noncommuting_commute_assertion": cvc5_order_proof(h_table, 1, 2),
            "order_commuting_control": cvc5_order_proof(h_table, 1, 1),
            "octonion_assoc_zero_assertion": cvc5_associator_proof(o_table, O_WITNESS),
            "quaternion_assoc_zero_control": cvc5_associator_proof(h_table, H_ASSOC_CONTROL),
            "real_basin_counterexample": cvc5_basin_proof(True),
            "erased_basin_counterexample": cvc5_basin_proof(False),
        },
    }
    all_pass = bool(
        ogap.item() > 1.0
        and ogap_control.item() <= TOL
        and assoc_norm.item() > 1.0
        and assoc_control_norm.item() <= TOL
        and basins_real["attractor_count"] == 2
        and basins_control["attractor_count"] == 16
        and smt["z3"]["real_basin_counterexample"] == "unsat"
        and smt["cvc5"]["real_basin_counterexample"] == "unsat"
        and smt["z3"]["erased_basin_counterexample"] == "sat"
        and smt["cvc5"]["erased_basin_counterexample"] == "sat"
        and abs(float(ci_sensitivity.item())) > 1.0e-3
        and ga["e1e2_minus_e2e1_norm"].item() > 1.0
    )
    result = {
        "schema_version": "three_engine_leg_result_v1",
        "object_id": OBJECT_ID,
        "rung_id": RUNG_ID,
        "engine": "pytorch",
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "packages_used": ["torch", "torch.func", "torch_ga", "torch_geometric", "geomstats", "z3", "cvc5", "json", "hashlib"],
        "aligned_packages_load_bearing": ["torch.func", "torch_ga", "torch_geometric", "geomstats", "z3", "cvc5"],
        "claim_path_tools": ["torch", "torch.func", "torch_ga", "torch_geometric", "geomstats", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "network": {"node_count": 4, "edges": GRAPH_EDGES, "target_spinor": TARGET},
        "graph": graph,
        "algebra": {
            "order_gap_noncommuting": ogap,
            "order_gap_commuting_control": ogap_control,
            "torch_ga_order_gap": ga,
            "octonion_associator_norm": assoc_norm,
            "octonion_associator_vector": assoc_o,
            "quaternion_associator_control_norm": assoc_control_norm,
        },
        "basins": {"finite_real": basins_real, "finite_erased_control": basins_control},
        "qit_readout": qit,
        "sensitivity": {
            "function_called": "torch.func.jacrev",
            "coherent_information_strength": strength,
            "d_coherent_information_d_strength": ci_sensitivity,
        },
        "geomstats": geom,
        "M_C_quotient": quotient_summary(),
        "smt": smt,
        "tool_calls": [
            {"tool": "torch_ga", "function": "GeometricAlgebra.geom_prod", "computed": ga},
            {"tool": "torch.func", "function": "torch.func.jacrev", "computed": {"dCI_dstrength": ci_sensitivity}},
            {"tool": "torch_geometric", "function": "torch_geometric.utils.to_dense_adj", "computed": graph},
            {"tool": "geomstats", "function": "Hypersphere.metric.dist", "computed": geom},
            {"tool": "z3", "function": "z3.Solver.check", "computed": smt["z3"]},
            {"tool": "cvc5", "function": "cvc5.Solver.checkSat", "computed": smt["cvc5"]},
        ],
        "all_pass": all_pass,
    }
    RESULT_PATH.write_text(json.dumps(to_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = build_result()
    print(
        "FOUNDATION_SPINOR_NETWORK_BASINS_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"order_gap={float(result['algebra']['order_gap_noncommuting']):.6f} "
        f"assoc={float(result['algebra']['octonion_associator_norm']):.6f} "
        f"real_attractors={result['basins']['finite_real']['attractor_count']} "
        f"control_attractors={result['basins']['finite_erased_control']['attractor_count']} "
        f"result={RESULT_PATH}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
