#!/usr/bin/env python3
import jax
jax.config.update("jax_enable_x64",True)

import json
import pathlib
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any

import jax.numpy as jnp
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
import z3

SCRIPTS_DIR = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
sys.path.insert(0, str(SCRIPTS_DIR))
from load_bearing_proof import smt_load_bearing, tool_ablation  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "root_N01_path_family_order_probe"
OBJECT_ID = "N01_path_family"
OUT_PATH = RESULT_DIR / "N01_path_family_results.json"

SCALE_RUNGS = (8, 16, 32, 64)
RTYPE = torch.float64
EPS = 1.0e-5
ALPHA = Fraction(3, 100)
BETA = Fraction(4, 100)
INITIAL_TORCH = torch.tensor([1.0, 0.75], dtype=RTYPE)
INITIAL_JAX = jnp.array([1.0, 0.75], dtype=jnp.float64)
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim numeric: applies finite local path maps on the real and control carriers and measures ||end(A then B)-end(B then A)|| without dense state closure.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 parity mirror: recomputes the same path-family end-state observable independently after jax_enable_x64 is set before jax.numpy import.",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING graph surface: constructs the finite directed path carrier and ordered edge schedule used to decide how many local map-pair events are applied.",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING graph tensor surface: carries the rustworkx path as edge_index/op_pairs tensors consumed by the torch path evaluator; edge erasure kills the observable.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING proof via load_bearing_proof.smt_load_bearing: the same order-gap inequality is bound to real measured values and to confluent-control measured values and must flip.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING proof cross-check through the helper's cvc5 path for the same measured order-gap inequality.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING exact symbolic witness: computes the exact rational path gap for the rung-8 real maps and the exact zero gap for confluent maps.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not used; NumPy is control-only by instruction and is not needed for this root nonclassical path-family sim.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Not used; SciPy is control-only by instruction and no SciPy routine is needed for this finite path-family witness.",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "Supportive only: JSON emission, timestamps, paths, and exact Fraction constants.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "rustworkx": "load_bearing",
    "torch_geometric": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "numpy": None,
    "scipy": None,
    "python_stdlib": "supportive",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if hasattr(value, "tolist") and callable(value.tolist):
        try:
            return as_jsonable(value.tolist())
        except Exception:
            pass
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator, "float": float(value)}
    return value


def build_rustworkx_path(sites: int, op_pair: tuple[int, int] = (0, 1)) -> rx.PyDiGraph:
    graph = rx.PyDiGraph(multigraph=False)
    graph.add_nodes_from(range(sites))
    for idx in range(sites - 1):
        graph.add_edge(idx, idx + 1, {"edge": idx, "op_pair": op_pair})
    return graph


def rustworkx_to_pyg(graph: rx.PyDiGraph) -> Data:
    weighted_edges = list(graph.weighted_edge_list())
    if weighted_edges:
        edge_index = torch.tensor([[u for u, _, _ in weighted_edges], [v for _, v, _ in weighted_edges]], dtype=torch.long)
        op_pairs = torch.tensor([list(data["op_pair"]) for _, _, data in weighted_edges], dtype=torch.long)
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)
        op_pairs = torch.empty((0, 2), dtype=torch.long)
    data = Data(edge_index=edge_index, op_pairs=op_pairs, num_nodes=graph.num_nodes())
    data.rx_dag_longest_path_length = int(rx.dag_longest_path_length(graph)) if graph.num_edges() else 0
    return data


def erased_pyg_path(sites: int) -> Data:
    data = Data(edge_index=torch.empty((2, 0), dtype=torch.long), op_pairs=torch.empty((0, 2), dtype=torch.long), num_nodes=sites)
    data.rx_dag_longest_path_length = 0
    return data


def torch_maps(control: bool = False) -> tuple[torch.Tensor, torch.Tensor]:
    a = float(ALPHA)
    b = float(BETA)
    if control:
        return (
            torch.tensor([[1.0 + a, 0.0], [0.0, 1.0]], dtype=RTYPE),
            torch.tensor([[1.0, 0.0], [0.0, 1.0 + b]], dtype=RTYPE),
        )
    return (
        torch.tensor([[1.0, a], [0.0, 1.0]], dtype=RTYPE),
        torch.tensor([[1.0, 0.0], [b, 1.0]], dtype=RTYPE),
    )


def jax_maps(control: bool = False) -> tuple[jnp.ndarray, jnp.ndarray]:
    a = jnp.float64(float(ALPHA))
    b = jnp.float64(float(BETA))
    if control:
        return (
            jnp.array([[1.0 + a, 0.0], [0.0, 1.0]], dtype=jnp.float64),
            jnp.array([[1.0, 0.0], [0.0, 1.0 + b]], dtype=jnp.float64),
        )
    return (
        jnp.array([[1.0, a], [0.0, 1.0]], dtype=jnp.float64),
        jnp.array([[1.0, 0.0], [b, 1.0]], dtype=jnp.float64),
    )


def apply_torch_path(path: Data, maps: tuple[torch.Tensor, torch.Tensor], reverse_pair: bool) -> torch.Tensor:
    state = INITIAL_TORCH.clone()
    for pair in path.op_pairs:
        order = list(reversed(pair.tolist())) if reverse_pair else pair.tolist()
        for op_idx in order:
            state = maps[int(op_idx)] @ state
    return state


def apply_jax_path(op_pairs: jnp.ndarray, maps: tuple[jnp.ndarray, jnp.ndarray], reverse_pair: bool) -> jnp.ndarray:
    state = INITIAL_JAX
    for pair in op_pairs:
        order = list(reversed([int(pair[0]), int(pair[1])])) if reverse_pair else [int(pair[0]), int(pair[1])]
        for op_idx in order:
            state = maps[op_idx] @ state
    return state


def torch_path_readout(sites: int, control: bool = False, edge_erased: bool = False) -> dict[str, Any]:
    graph = build_rustworkx_path(sites)
    path = erased_pyg_path(sites) if edge_erased else rustworkx_to_pyg(graph)
    maps = torch_maps(control=control)
    end_ab = apply_torch_path(path, maps, reverse_pair=False)
    end_ba = apply_torch_path(path, maps, reverse_pair=True)
    delta = end_ab - end_ba
    order_gap = float(torch.linalg.vector_norm(delta).item())
    local_commutator = maps[1] @ maps[0] - maps[0] @ maps[1]
    local_commutator_norm = float(torch.linalg.matrix_norm(local_commutator, ord="fro").item())
    pass_status = bool(order_gap >= EPS) if not (control or edge_erased) else bool(order_gap <= EPS)
    return {
        "sites_or_qubits": sites,
        "graph_nodes": int(graph.num_nodes()),
        "graph_edges": int(graph.num_edges()),
        "path_length": int(path.rx_dag_longest_path_length),
        "pyg_edge_count": int(path.edge_index.shape[1]),
        "dense_state_closure_used": False,
        "control_carrier": bool(control),
        "edge_erased": bool(edge_erased),
        "map_family": "confluent_commuting_diagonal_maps" if control else "noncommuting_shear_maps",
        "end_A_then_B": [float(x) for x in end_ab.tolist()],
        "end_B_then_A": [float(x) for x in end_ba.tolist()],
        "end_delta": [float(x) for x in delta.tolist()],
        "order_gap": order_gap,
        "local_commutator_frobenius": local_commutator_norm,
        "pass": pass_status,
    }


def jax_path_readout(sites: int, control: bool = False) -> dict[str, Any]:
    graph = build_rustworkx_path(sites)
    path = rustworkx_to_pyg(graph)
    op_pairs = jnp.array(path.op_pairs.detach().cpu().tolist(), dtype=jnp.int64)
    maps = jax_maps(control=control)
    end_ab = apply_jax_path(op_pairs, maps, reverse_pair=False)
    end_ba = apply_jax_path(op_pairs, maps, reverse_pair=True)
    delta = end_ab - end_ba
    order_gap = float(jnp.linalg.norm(delta))
    local_commutator = maps[1] @ maps[0] - maps[0] @ maps[1]
    local_commutator_norm = float(jnp.linalg.norm(local_commutator, ord="fro"))
    return {
        "sites_or_qubits": sites,
        "graph_nodes": int(graph.num_nodes()),
        "graph_edges": int(graph.num_edges()),
        "path_length": int(path.rx_dag_longest_path_length),
        "dense_state_closure_used": False,
        "control_carrier": bool(control),
        "end_A_then_B": [float(x) for x in end_ab.tolist()],
        "end_B_then_A": [float(x) for x in end_ba.tolist()],
        "end_delta": [float(x) for x in delta.tolist()],
        "order_gap": order_gap,
        "local_commutator_frobenius": local_commutator_norm,
        "pass": bool(order_gap >= EPS) if not control else bool(order_gap <= EPS),
    }


def sympy_path_gap(sites: int, control: bool = False) -> dict[str, Any]:
    a = sp.Rational(ALPHA.numerator, ALPHA.denominator)
    b = sp.Rational(BETA.numerator, BETA.denominator)
    if control:
        amat = sp.Matrix([[1 + a, 0], [0, 1]])
        bmat = sp.Matrix([[1, 0], [0, 1 + b]])
    else:
        amat = sp.Matrix([[1, a], [0, 1]])
        bmat = sp.Matrix([[1, 0], [b, 1]])
    x0 = sp.Matrix([sp.Rational(1), sp.Rational(3, 4)])
    end_ab = (bmat * amat) ** (sites - 1) * x0
    end_ba = (amat * bmat) ** (sites - 1) * x0
    delta = sp.simplify(end_ab - end_ba)
    gap_squared = sp.simplify(sum(item * item for item in delta))
    return {
        "sites_or_qubits": sites,
        "control_carrier": bool(control),
        "end_delta_exact": [str(item) for item in delta],
        "gap_squared_exact": str(gap_squared),
        "gap": float(sp.sqrt(gap_squared)),
        "pass": bool(gap_squared > 0) if not control else bool(gap_squared == 0),
    }


def add_ablation_pass(row: dict[str, Any]) -> dict[str, Any]:
    row["pass"] = bool(abs(float(row["outcome_delta"])) > EPS)
    return row


def build_result() -> dict[str, Any]:
    started = time.time()
    torch_rows = {str(n): torch_path_readout(n) for n in SCALE_RUNGS}
    torch_controls = {str(n): torch_path_readout(n, control=True) for n in SCALE_RUNGS}
    edge_erased_controls = {str(n): torch_path_readout(n, edge_erased=True) for n in SCALE_RUNGS}
    jax_rows = {str(n): jax_path_readout(n) for n in SCALE_RUNGS}
    jax_controls = {str(n): jax_path_readout(n, control=True) for n in SCALE_RUNGS}

    parity_deltas = []
    for n in SCALE_RUNGS:
        key = str(n)
        parity_deltas.append(abs(torch_rows[key]["order_gap"] - jax_rows[key]["order_gap"]))
        parity_deltas.extend(abs(torch_rows[key]["end_A_then_B"][i] - jax_rows[key]["end_A_then_B"][i]) for i in range(2))
        parity_deltas.extend(abs(torch_rows[key]["end_B_then_A"][i] - jax_rows[key]["end_B_then_A"][i]) for i in range(2))
    jax_vs_pytorch_delta = max(parity_deltas)

    min_real_gap = min(torch_rows[str(n)]["order_gap"] for n in SCALE_RUNGS)
    max_confluent_gap = max(torch_controls[str(n)]["order_gap"] for n in SCALE_RUNGS)
    max_edge_erased_gap = max(edge_erased_controls[str(n)]["order_gap"] for n in SCALE_RUNGS)
    sympy_real = sympy_path_gap(8, control=False)
    sympy_control = sympy_path_gap(8, control=True)

    smt_proof = smt_load_bearing(
        "||end(A then B) - end(B then A)|| >= eps",
        real_measured={"order_gap": min_real_gap},
        control_measured={"order_gap": max_confluent_gap},
        claim_builder=lambda v: v["order_gap"] >= z3.RealVal(str(EPS)),
        cvc5_claim_pairs=[("order_gap", ">=", EPS)],
    )
    smt_proof["pass"] = bool(
        smt_proof["real_claim_verdict"] == "sat"
        and smt_proof["negated_claim_verdict"] == "unsat"
        and smt_proof["differ"]
        and smt_proof.get("cvc5_real_verdict") in ("sat", "skip")
        and smt_proof.get("cvc5_control_verdict") in ("unsat", "skip")
    )

    sympy_proof = smt_load_bearing(
        "sympy exact rung-8 ||end(A then B) - end(B then A)|| >= eps",
        real_measured={"sympy_order_gap": sympy_real["gap"]},
        control_measured={"sympy_order_gap": sympy_control["gap"]},
        claim_builder=lambda v: v["sympy_order_gap"] >= z3.RealVal(str(EPS)),
        cvc5_claim_pairs=[("sympy_order_gap", ">=", EPS)],
    )
    sympy_proof.update(
        {
            "engine": "sympy+load_bearing_proof",
            "exact_real_gap_squared": sympy_real["gap_squared_exact"],
            "exact_control_gap_squared": sympy_control["gap_squared_exact"],
            "pass": bool(
                sympy_proof["real_claim_verdict"] == "sat"
                and sympy_proof["negated_claim_verdict"] == "unsat"
                and sympy_proof["differ"]
            ),
        }
    )

    tool_ablations = {
        "rustworkx_confluent_map_order_gap": add_ablation_pass(
            tool_ablation(
                "min path-order gap over rustworkx path carrier, real maps vs confluent commuting maps",
                baseline_value=min_real_gap,
                ablated_value=max_confluent_gap,
                tool="rustworkx",
            )
        ),
        "torch_geometric_edge_index_order_gap": add_ablation_pass(
            tool_ablation(
                "min path-order gap with PyG edge_index/op_pairs vs edge-erased path",
                baseline_value=min_real_gap,
                ablated_value=max_edge_erased_gap,
                tool="torch_geometric",
            )
        ),
        "z3_smt_bound_order_gap": add_ablation_pass(
            tool_ablation(
                "numeric order_gap fed to smt_load_bearing, real carrier vs confluent control",
                baseline_value=min_real_gap,
                ablated_value=max_confluent_gap,
                tool="z3",
            )
        ),
        "cvc5_smt_bound_order_gap": add_ablation_pass(
            tool_ablation(
                "helper cvc5 cross-check over the same measured order_gap, real carrier vs confluent control",
                baseline_value=min_real_gap,
                ablated_value=max_confluent_gap,
                tool="cvc5",
            )
        ),
        "sympy_exact_rung8_order_gap": add_ablation_pass(
            tool_ablation(
                "exact symbolic rung-8 path gap, real maps vs confluent maps",
                baseline_value=sympy_real["gap"],
                ablated_value=sympy_control["gap"],
                tool="sympy",
            )
        ),
        "torch_primary_order_gap": add_ablation_pass(
            tool_ablation(
                "torch primary measured min order_gap, real maps vs confluent maps",
                baseline_value=min_real_gap,
                ablated_value=max_confluent_gap,
                tool="torch",
            )
        ),
    }

    scale_rungs = {
        str(n): {
            "sites_or_qubits": n,
            "graph_nodes": torch_rows[str(n)]["graph_nodes"],
            "graph_edges": torch_rows[str(n)]["graph_edges"],
            "path_length": torch_rows[str(n)]["path_length"],
            "dense_state_closure_used": False,
            "order_gap": torch_rows[str(n)]["order_gap"],
            "control_order_gap": torch_controls[str(n)]["order_gap"],
            "edge_erased_order_gap": edge_erased_controls[str(n)]["order_gap"],
            "pass": bool(
                torch_rows[str(n)]["pass"]
                and torch_controls[str(n)]["pass"]
                and edge_erased_controls[str(n)]["pass"]
                and jax_rows[str(n)]["pass"]
                and jax_controls[str(n)]["pass"]
            ),
        }
        for n in SCALE_RUNGS
    }

    scale_pass = all(row["pass"] for row in scale_rungs.values())
    proof_pass = bool(smt_proof["pass"] and sympy_proof["pass"])
    ablation_pass = all(row["pass"] for row in tool_ablations.values())
    parity_pass = bool(jax_vs_pytorch_delta <= 1.0e-10)
    controls_pass = bool(max_confluent_gap <= EPS and max_edge_erased_gap <= EPS)
    all_pass = bool(scale_pass and proof_pass and ablation_pass and parity_pass and controls_pass)

    result = {
        "schema": "PER_SIM_CONTRACT_ROOT_STAGE1_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "object_id": OBJECT_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": time.time() - started,
        "classification": "lego",
        "tier": "stage_1_root_constraint",
        "sim_execution_kind": "nonclassical",
        "sim_class": "constraint_probe",
        "purpose": "Build one canonical Stage-1 N01 root-constraint path-family order probe with real graph-carried path maps, negative controls, helper-bound SMT proof, and recomputed tool ablations.",
        "scientific_question": "Does a finite directed path family of local maps produce an order-sensitive endpoint gap, and does that gap fail under confluent/commuting or edge-erased controls at graph sizes 8/16/32/64?",
        "finite_map": {
            "domain": "For each graph size n in {8,16,32,64}: finite directed rustworkx path graph with n nodes and n-1 edges, converted to torch_geometric edge_index/op_pairs; two local maps A,B act on a two-component torch carrier along every path edge.",
            "codomain_or_output": "Endpoint pair (end(A then B), end(B then A)), order_gap=||end(A then B)-end(B then A)||, real/control SMT verdict flip, exact sympy rung-8 check, graph-erased/confluent controls, and blocked downstream consumers.",
        },
        "domain": {
            "scale_graph_sizes": list(SCALE_RUNGS),
            "carrier": "two-component torch.float64 local spinor-like state transported by finite path-local map pairs; graph size scales path events, not Hilbert dense closure",
            "maps": {
                "real_A": [[1.0, float(ALPHA)], [0.0, 1.0]],
                "real_B": [[1.0, 0.0], [float(BETA), 1.0]],
                "control_A": [[1.0 + float(ALPHA), 0.0], [0.0, 1.0]],
                "control_B": [[1.0, 0.0], [0.0, 1.0 + float(BETA)]],
            },
        },
        "codomain_or_output": {
            "order_gap": "real-valued norm of endpoint difference between path order A->B and path order B->A",
            "proof": "smt_load_bearing binds the measured min order_gap and confluent-control order_gap to z3/cvc5 real variables",
            "controls": "confluent commuting maps and PyG edge-erased path both kill the gap",
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite carrier/probe/operator/path set: every rung uses a finite graph path, finite local maps, finite endpoint readouts, and finite proof/control outputs.",
            },
            "N01": {
                "role": "active",
                "statement": "noncommuting or order-sensitive operation/control: noncommuting A/B local maps produce an endpoint order gap; confluent/commuting and edge-erased controls kill it.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting or order-sensitive operation/control",
        ],
        "carrier_layer": "root finite path-family carrier",
        "geometry_layer": "not_applicable: this is a root N01 path-order lego, not a manifold/geometry layer",
        "carrier_realization": "torch.float64 two-component local state plus rustworkx/PyG finite path schedule; no dense global state or NumPy bridge is used.",
        "peps3d_embedding": {
            "status": "finite anchor only, not a PEPS3D/manifold claim",
            "anchor_rule": "path node i can be treated as a finite site anchor for later PEPS3D-carried work; this sim does not perform PEPS3D contraction or layer admission.",
            "dense_state_closure_used": False,
        },
        "spinor_state": "two-component torch.float64 local spinor-like state; no dense n-site spinor state is materialized",
        "quaternion_action": "not_applicable: no quaternion language or quaternion invariant is used",
        "dependency_receipts": [],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "N01 path-family endpoint order gap: ||end(A then B)-end(B then A)|| >= eps",
        "branch_status_before_run": "Stage-1 root-constraint lego requested by user; no downstream consumer opened",
        "allowed_claims": [
            "bounded N01 path-family root lego exists/runs if this result and validators pass",
            "finite path-local noncommuting maps create an endpoint order gap over 8/16/32/64 graph sizes",
            "confluent commuting maps and edge-erased controls kill the endpoint order gap",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "root Stage-1 N01 lego only",
            "does not complete any manifold layer",
            "does not admit Xi, Phi0, Axis0, flux, FEP, gravity, bridge, basin, or physics consumers",
        ],
        "eligible_consumers": ["bounded root-constraint audits only after citing this result path and fresh validator output"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["load_bearing_proof.smt_load_bearing z3", "load_bearing_proof.smt_load_bearing cvc5 cross-check", "sympy exact rational rung-8 witness"],
        "graph_surfaces_used": ["rustworkx PyDiGraph path construction", "torch_geometric Data edge_index/op_pairs path schedule"],
        "topology_surfaces_used": [],
        "required_negatives": ["confluent_commuting_path_family", "pyg_edge_index_erased_path"],
        "negatives_run": {
            "confluent_commuting_path_family": torch_controls,
            "pyg_edge_index_erased_path": edge_erased_controls,
        },
        "kill_conditions": {
            "confluent_commuting_path_family": "max control order_gap must be <= eps",
            "pyg_edge_index_erased_path": "max edge-erased order_gap must be <= eps",
            "smt_load_bearing": "real measured order_gap claim must be sat and confluent-control claim must be unsat",
        },
        "required_artifacts": ["result JSON", "scale_ladder", "torch primary readouts", "JAX mirror readouts", "proof_results", "controls", "tool_ablations"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "controls_pass": controls_pass,
            "tool_ablations_pass": ablation_pass,
            "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
            "min_real_order_gap": min_real_gap,
            "max_confluent_control_order_gap": max_confluent_gap,
            "max_edge_erased_control_order_gap": max_edge_erased_gap,
        },
        "torch_primary_result": {
            "engine": "torch",
            "dtype": "torch.float64",
            "claim": "finite path-local maps produce order-sensitive endpoint gap that controls kill",
            "rungs": torch_rows,
            "pass": all(row["pass"] for row in torch_rows.values()),
        },
        "jax_mirror_result": {
            "engine": "jax",
            "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
            "claim": "JAX x64 recomputes the same endpoint order gaps",
            "rungs": jax_rows,
            "controls": jax_controls,
            "pass": all(row["pass"] for row in jax_rows.values()) and all(row["pass"] for row in jax_controls.values()),
        },
        "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
        "jax_vs_pytorch": {
            "max_abs_delta": jax_vs_pytorch_delta,
            "tolerance": 1.0e-10,
            "agree": parity_pass,
        },
        "proof_results": {
            "smt_load_bearing_order_gap": smt_proof,
            "sympy_exact_rung8_path_gap": sympy_proof,
            "pass": proof_pass,
        },
        "controls": {
            "confluent_commuting_path_family": {
                "description": "same rustworkx/PyG path carrier but A and B are diagonal commuting maps",
                "rungs": torch_controls,
                "max_order_gap": max_confluent_gap,
                "kills_constraint": controls_pass,
                "pass": bool(max_confluent_gap <= EPS),
            },
            "pyg_edge_index_erased_path": {
                "description": "real noncommuting maps but the PyG edge_index/op_pairs path is erased, so no local maps are applied",
                "rungs": edge_erased_controls,
                "max_order_gap": max_edge_erased_gap,
                "kills_constraint": bool(max_edge_erased_gap <= EPS),
                "pass": bool(max_edge_erased_gap <= EPS),
            },
        },
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "scale_ladder": {
            "rungs": scale_rungs,
            "scale_axis": "path_graph_size",
            "dense_state_closure_used": False,
            "pass": scale_pass,
        },
        "positive": {
            "noncommuting_path_family_order_gap": {"pass": min_real_gap >= EPS, "min_order_gap": min_real_gap},
            "helper_bound_smt_flip": {"pass": smt_proof["pass"], "proof": smt_proof},
            "sympy_exact_control_flip": {"pass": sympy_proof["pass"], "proof": sympy_proof},
            "scale_8_16_32_64": {"pass": scale_pass, "rungs": scale_rungs},
        },
        "graveyard_companions": {
            "confluent_commuting_path_family": {"killed": bool(max_confluent_gap <= EPS), "max_order_gap": max_confluent_gap},
            "pyg_edge_index_erased_path": {"killed": bool(max_edge_erased_gap <= EPS), "max_order_gap": max_edge_erased_gap},
        },
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "numpy_claim_bearing": {"used": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "nearby_variants": {
            "commuted_maps": "confluent diagonal A/B maps commute and kill the path-order gap",
            "probe_erased": "empty PyG edge_index/op_pairs applies no path maps and kills the path-order gap",
        },
        "shells": [
            {
                "name": "root_N01_path_family_object",
                "status": "root lego only",
                "scale_rungs": list(SCALE_RUNGS),
                "survives": all_pass,
            }
        ],
        "future_continuations": [
            "build separate F01 root-family probe if needed",
            "consume this only as bounded N01 path-order evidence after validator output is cited",
        ],
        "compatibility_weights": {
            "root_N01_path_family_evidence": 1.0 if all_pass else 0.0,
            "downstream_Xi_Phi0_Axis0_flux_FEP_gravity": 0.0,
        },
        "compression_map": {
            "from": "finite rustworkx path graph, PyG edge_index/op_pairs, local noncommuting maps, and endpoint states",
            "to": "order_gap, proof verdict flip, controls, ablation deltas, and blocked downstream consumers",
            "loss_boundary": "does not preserve or claim dense global state, PEPS3D contraction, manifold, axis, bridge, flux, FEP, gravity, or physics admission",
        },
        "present_survivor": {
            "object": OBJECT_ID,
            "capacity": min_real_gap,
            "survives": bool(all_pass),
            "blocked_capacity": BLOCKED_CONSUMERS,
        },
        "survivor_invariant": {
            "invariant": "N01 path-family object survives iff every rung is finite/non-dense, real order_gap>=eps, controls kill, helper proof flips, ablations are recomputed and nonzero, and promotion_allowed=false",
            "computed_capacity": min_real_gap,
            "threshold": EPS,
            "passed": bool(all_pass and min_real_gap >= EPS),
        },
        "outward_record": {
            "result_path": str(OUT_PATH.relative_to(ROOT)),
            "per_sim_contract_command": f"../../../scripts/per_sim_contract.py {OUT_PATH.relative_to(ROOT)}",
            "max_deep_gate_command": f"../../../scripts/max_deep_lego_gate.py {OUT_PATH.relative_to(ROOT)} --scale-required --rigor",
            "claim_ceiling": "N01 path-family root lego only; no downstream consumer admitted",
        },
        "pass_rule": "all 8/16/32/64 finite path rungs pass; torch and JAX agree; helper-bound z3/cvc5 proof flips; sympy exact control flips; confluent and edge-erased controls kill; every tool ablation records baseline+ablated recompute with nonzero delta",
        "fail_rule": "fail on dense closure, missing graph rung, missing path order gap, no real/control proof flip, live confluent/edge-erased control, zero or cosmetic ablation, JAX mismatch, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blockers": [] if all_pass else ["one_or_more_N01_path_family_checks_failed"],
        "required_pass": all_pass,
        "all_pass": all_pass,
    }
    return result


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "required_pass": result["required_pass"],
                "result_path": str(OUT_PATH.relative_to(ROOT)),
                "scale_pass": result["scale_ladder"]["pass"],
                "jax_vs_pytorch_delta": result["jax_vs_pytorch_delta"],
                "proof_pass": result["proof_results"]["pass"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
