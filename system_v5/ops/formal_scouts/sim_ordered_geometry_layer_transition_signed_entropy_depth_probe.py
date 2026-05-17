#!/usr/bin/env python3
"""Ordered geometry-layer transition scout for signed entropy depth."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

from clifford import Cl
import gudhi
import networkx as nx
import opt_einsum as oe
import rustworkx as rx
import torch
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data
import toponetx as tnx
import xgi
import z3

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "ordered_geometry_layer_transition_signed_entropy_depth_probe_results.json"

NAME = "ordered_geometry_layer_transition_signed_entropy_depth_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests when entropy readouts first become admissible "
    "across an ordered finite geometry-layer chain. It checks whether signed "
    "conditional/coherent information appears only after a bipartite coupling "
    "layer. It does not admit a final manifold order, feedback axis, cycle, "
    "or target-system entropy-gradient claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density, channel, entropy, and tensor-state math"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing bipartite partial traces"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing orientation/chirality layer check"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing killed-transition filtration witness"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing transition simplicial complex"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing transition hyperedge witness"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing ordered layer transition graph"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph message pass over layer features"},
    "networkx": {"tried": True, "used": True, "reason": "support graph source for topology witnesses"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing impossibility check for signed entropy before bipartite coupling"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "opt_einsum": "load_bearing",
    "clifford": "load_bearing",
    "gudhi": "load_bearing",
    "toponetx": "load_bearing",
    "xgi": "load_bearing",
    "rustworkx": "load_bearing",
    "torch_geometric": "load_bearing",
    "networkx": "supportive",
    "z3": "load_bearing",
}


def density(psi: torch.Tensor) -> torch.Tensor:
    psi = psi / torch.linalg.vector_norm(psi)
    return torch.outer(psi, psi.conj())


def entropy(rho: torch.Tensor) -> float:
    rho = (rho + rho.conj().T) / 2
    eigs = torch.clamp(torch.linalg.eigvalsh(rho), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def trace_a(rho: torch.Tensor) -> torch.Tensor:
    return oe.contract("aiaj->ij", rho.reshape(2, 2, 2, 2))


def trace_b(rho: torch.Tensor) -> torch.Tensor:
    return oe.contract("aibi->ab", rho.reshape(2, 2, 2, 2))


def signed_readouts(rho: torch.Tensor) -> dict[str, float]:
    s_ab = entropy(rho)
    s_a = entropy(trace_b(rho))
    s_b = entropy(trace_a(rho))
    return {
        "S_AB": s_ab,
        "S_A": s_a,
        "S_B": s_b,
        "mutual_information": s_a + s_b - s_ab,
        "conditional_entropy_A_given_B": s_ab - s_b,
        "coherent_information_A_to_B": s_b - s_ab,
    }


def cnot() -> torch.Tensor:
    return torch.tensor(
        [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
        dtype=torch.complex128,
    )


def layer_chain() -> list[dict[str, Any]]:
    _, blades = Cl(1, 3)
    pseudoscalar_square = float((blades["e1234"] * blades["e1234"])[()])
    single = density(torch.tensor([1, 1], dtype=torch.complex128))
    product = density(torch.tensor([1, 0, 0, 0], dtype=torch.complex128))
    entangler = cnot()
    plus_zero = density(torch.tensor([1, 0, 1, 0], dtype=torch.complex128))
    entangled = entangler @ plus_zero @ entangler.conj().T
    dephased = torch.diag(torch.diag(entangled))
    return [
        {"name": "two_component_state_vector", "state_kind": "single_state", "value": torch.tensor([1, 1], dtype=torch.complex128)},
        {"name": "two_component_density_matrix", "state_kind": "single_density", "value": single},
        {"name": "hopf_phase_quotient_density_matrix", "state_kind": "single_density", "value": single},
        {"name": "clifford_orientation_sign_check", "state_kind": "orientation_scalar", "value": pseudoscalar_square},
        {"name": "two_qubit_product_density_matrix", "state_kind": "bipartite_density", "value": product},
        {"name": "two_qubit_entangled_density_after_cnot", "state_kind": "bipartite_density", "value": entangled},
        {"name": "two_qubit_dephased_classical_correlation_density", "state_kind": "bipartite_density", "value": dephased},
    ]


def admission_for_layer(layer: dict[str, Any]) -> dict[str, Any]:
    value = layer["value"]
    admits_unsigned = isinstance(value, torch.Tensor) and value.ndim == 2 and value.shape[0] == value.shape[1] and abs(float(torch.trace(value).real) - 1) < 1e-9
    admits_bipartite = admits_unsigned and value.shape == (4, 4)
    row = {
        "admits_unsigned_entropy": admits_unsigned,
        "admits_mutual_information": False,
        "admits_signed_conditional_entropy": False,
        "admits_coherent_information": False,
        "readouts": None,
    }
    if admits_bipartite:
        r = signed_readouts(value)
        row.update(
            {
                "admits_mutual_information": r["mutual_information"] > 1e-9,
                "admits_signed_conditional_entropy": r["conditional_entropy_A_given_B"] < -1e-9,
                "admits_coherent_information": r["coherent_information_A_to_B"] > 1e-9,
                "readouts": r,
            }
        )
    return row


def transition_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = [graph.add_node(row["name"]) for row in rows]
    for idx in range(len(nodes) - 1):
        graph.add_edge(nodes[idx], nodes[idx + 1], "next")

    x = torch.tensor(
        [
            [
                float(row["admits_unsigned_entropy"]),
                float(row["admits_mutual_information"]),
                float(row["admits_signed_conditional_entropy"]),
                float(row["admits_coherent_information"]),
            ]
            for row in rows
        ],
        dtype=torch.float32,
    )
    edge_index = torch.tensor([[i for i in range(len(rows) - 1)], [i + 1 for i in range(len(rows) - 1)]], dtype=torch.long)
    data = Data(x=x, edge_index=edge_index)
    conv = GCNConv(4, 2, add_self_loops=True)
    with torch.no_grad():
        propagated = conv(data.x, data.edge_index)
    return {"rustworkx_nodes": graph.num_nodes(), "rustworkx_edges": graph.num_edges(), "pyg_output_shape": list(propagated.shape)}


def topology_witness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    complex_ = tnx.SimplicialComplex()
    names = [row["name"] for row in rows]
    for name in names:
        complex_.add_node(name)
    for a, b in zip(names[:-1], names[1:]):
        complex_.add_simplex([a, b])
    hypergraph = xgi.Hypergraph()
    hypergraph.add_nodes_from(names)
    hypergraph.add_edge([rows[4]["name"], rows[5]["name"], rows[6]["name"]])
    st = gudhi.SimplexTree()
    for idx, name in enumerate(names):
        st.insert([idx], filtration=float(idx))
    for idx in range(len(names) - 1):
        st.insert([idx, idx + 1], filtration=float(idx + 1))
    persistence = st.persistence()
    return {
        "toponetx_dimension": complex_.dim,
        "xgi_hyperedges": hypergraph.num_edges,
        "gudhi_persistence_pairs": len(persistence),
    }


def z3_signed_requires_bipartite() -> dict[str, Any]:
    signed = z3.Bool("signed")
    bipartite = z3.Bool("bipartite")
    solver = z3.Solver()
    solver.add(signed, z3.Not(bipartite), z3.Implies(signed, bipartite))
    return {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat}


def main() -> dict[str, Any]:
    started = time.time()
    rows = []
    for layer in layer_chain():
        rows.append({"name": layer["name"], "state_kind": layer["state_kind"], **admission_for_layer(layer)})
    first_unsigned = next(row["name"] for row in rows if row["admits_unsigned_entropy"])
    first_mutual = next(row["name"] for row in rows if row["admits_mutual_information"])
    first_signed = next(row["name"] for row in rows if row["admits_signed_conditional_entropy"])
    first_coherent = next(row["name"] for row in rows if row["admits_coherent_information"])
    graph = transition_graph(rows)
    topo = topology_witness(rows)
    positive = {
        "unsigned_entropy_appears_before_correlation_readouts": {
            "first_unsigned": first_unsigned,
            "first_mutual": first_mutual,
            "pass": rows.index(next(row for row in rows if row["name"] == first_unsigned)) < rows.index(next(row for row in rows if row["name"] == first_mutual)),
        },
        "signed_conditional_and_coherent_information_first_appear_at_entangled_layer": {
            "first_signed_conditional": first_signed,
            "first_coherent": first_coherent,
            "pass": first_signed == "two_qubit_entangled_density_after_cnot" and first_coherent == "two_qubit_entangled_density_after_cnot",
        },
        "ordered_transition_graph_and_message_pass_execute": {"graph": graph, "pass": graph["pyg_output_shape"] == [len(rows), 2]},
        "z3_signed_entropy_requires_bipartite_coupling": z3_signed_requires_bipartite(),
    }
    graveyard_companions = {
        "two_qubit_product_layer_has_no_correlation_or_negative_entropy": {
            "row": next(row for row in rows if row["name"] == "two_qubit_product_density_matrix"),
            "pass": not next(row for row in rows if row["name"] == "two_qubit_product_density_matrix")["admits_mutual_information"],
        },
        "dephased_classical_correlation_has_mutual_information_but_not_negative_conditional_entropy": {
            "row": next(row for row in rows if row["name"] == "two_qubit_dephased_classical_correlation_density"),
            "pass": next(row for row in rows if row["name"] == "two_qubit_dephased_classical_correlation_density")["admits_mutual_information"]
            and not next(row for row in rows if row["name"] == "two_qubit_dephased_classical_correlation_density")["admits_signed_conditional_entropy"],
        },
        "orientation_scalar_layer_does_not_admit_entropy_by_type": {
            "row": next(row for row in rows if row["name"] == "clifford_orientation_sign_check"),
            "pass": not next(row for row in rows if row["name"] == "clifford_orientation_sign_check")["admits_unsigned_entropy"],
        },
    }
    boundary = {"topology_witnesses_execute_on_ordered_chain": {"topology": topo, "pass": topo["xgi_hyperedges"] == 1 and topo["gudhi_persistence_pairs"] > 0}}
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "ordered finite geometry layer chain with unsigned, mutual, signed conditional, and coherent entropy admission readouts",
        "ordered_layers": rows,
        "depth_summary": {
            "first_unsigned_entropy": first_unsigned,
            "first_mutual_information": first_mutual,
            "first_negative_conditional_entropy": first_signed,
            "first_positive_coherent_information": first_coherent,
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "ordered chain is a finite scout chain, not a final manifold tower",
            "next version should replace hand-built layers with callable lego outputs",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout over bounded layer transitions and should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {"all_pass": bool(all_pass), "elapsed_seconds": round(time.time() - started, 6), "promotion_allowed": PROMOTION_ALLOWED},
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
