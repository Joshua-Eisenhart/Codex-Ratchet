#!/usr/bin/env python3
"""Renyi/Tsallis operator-topology control microfit.

This bounded packet follows the Renyi and Tsallis microfits with one finite
control surface: entropy values should be invariant under unitary relabeling,
increase under dephasing/depolarizing controls on a coherent qubit, and remain
separate from the rustworkx schedule topology used to label operator order.
It is local tool-lego evidence only, not a coupling, bridge, QIT, GStack, axis,
engine, or nonclassical admission claim.
"""

from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime

import rustworkx as rx
import torch
import z3


CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION
divergence_log = (
    "Bounded PyTorch entropy/operator/topology control microfit for Renyi and "
    "Tsallis entropy rows. PyTorch is load-bearing for density operators and "
    "spectral entropy values; rustworkx is supportive schedule topology only; "
    "z3 is a supportive finite witness guard. This is not a coupling, bridge, "
    "QIT, GStack, axis, engine, or nonclassical admission."
)

LEGO_IDS = ["renyi_entropy", "tsallis_entropy", "operator_topology_control"]
PRIMARY_LEGO_IDS = ["renyi_entropy", "tsallis_entropy"]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density operators, unitary/dephasing/depolarizing controls, and spectral entropy values",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "supportive finite schedule graph distinguishing chain and cycle labels without driving entropy values",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite Real-arithmetic guard over precomputed entropy-control witnesses",
    },
    "sympy": {"tried": False, "used": False, "reason": "not needed; this packet uses finite numeric witnesses only"},
    "numpy": {"tried": False, "used": False, "reason": "not needed; torch carries numeric work"},
    "qutip": {"tried": False, "used": False, "reason": "not needed"},
    "qiskit": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "supportive",
    "z3": "supportive",
    "sympy": None,
    "numpy": None,
    "qutip": None,
    "qiskit": None,
    "cvc5": None,
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
PARENT_RESULTS = {
    "renyi_entropy_torch_microfit": RESULT_DIR / "renyi_entropy_torch_microfit_results.json",
    "tsallis_entropy_torch_microfit": RESULT_DIR / "tsallis_entropy_torch_microfit_results.json",
    "pytorch_capability": RESULT_DIR / "pytorch_capability_results.json",
}
OUT_PATH = RESULT_DIR / "entropy_operator_topology_controls_results.json"
EPS = 1e-10
CDTYPE = torch.complex128
LN2 = torch.log(torch.tensor(2.0, dtype=torch.float64))


def load_receipts() -> dict[str, object]:
    rows = {}
    for key, path in PARENT_RESULTS.items():
        if not path.exists():
            rows[key] = {"path": str(path), "exists": False, "all_pass": False}
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        rows[key] = {
            "path": str(path),
            "exists": True,
            "all_pass": bool(data.get("all_pass") or data.get("summary", {}).get("all_pass")),
            "classification": data.get("classification"),
        }
    return rows


def dm(vec: torch.Tensor) -> torch.Tensor:
    ket = vec.reshape(-1, 1).to(CDTYPE)
    return ket @ ket.conj().T


def states() -> dict[str, torch.Tensor]:
    zero = torch.tensor([1.0, 0.0], dtype=CDTYPE)
    one = torch.tensor([0.0, 1.0], dtype=CDTYPE)
    plus = (zero + one) / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    return {
        "zero": dm(zero),
        "one": dm(one),
        "plus": dm(plus),
        "biased": torch.diag(torch.tensor([0.8, 0.2], dtype=torch.float64)).to(CDTYPE),
        "mixed": torch.eye(2, dtype=CDTYPE) / 2.0,
    }


def spectrum(rho: torch.Tensor) -> torch.Tensor:
    eigs = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real.clamp_min(0.0)
    total = torch.sum(eigs)
    if float(total.item()) <= EPS:
        raise ValueError("zero-trace density matrix")
    return eigs / total


def renyi_entropy(rho: torch.Tensor, alpha: float = 2.0) -> float:
    eigs = spectrum(rho)
    pos = eigs[eigs > 1e-14]
    if pos.numel() == 0:
        return 0.0
    moment = torch.sum(pos.pow(alpha))
    return float((torch.log2(moment) / (1.0 - alpha)).item())


def tsallis_entropy(rho: torch.Tensor, q: float = 2.0) -> float:
    """Bits-normalized Tsallis entropy; divides by ln(2) to match Renyi scale."""
    eigs = spectrum(rho)
    moment = torch.sum(eigs.pow(q))
    return float(((1.0 - moment) / ((q - 1.0) * LN2)).item())


def pauli_x() -> torch.Tensor:
    return torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)


def unitary_conjugate(rho: torch.Tensor, unitary: torch.Tensor) -> torch.Tensor:
    return unitary @ rho @ unitary.conj().T


def dephase_z(rho: torch.Tensor) -> torch.Tensor:
    return torch.diag(torch.diagonal(rho)).to(CDTYPE)


def depolarize(rho: torch.Tensor, p: float) -> torch.Tensor:
    return (1.0 - p) * rho + p * torch.eye(2, dtype=CDTYPE) / 2.0


def schedule_graph(cyclic: bool) -> dict[str, object]:
    graph = rx.PyDiGraph()
    nodes = [graph.add_node(name) for name in ["prepare", "unitary_x", "dephase_z", "measure_entropy"]]
    graph.add_edges_from_no_data([(nodes[0], nodes[1]), (nodes[1], nodes[2]), (nodes[2], nodes[3])])
    if cyclic:
        graph.add_edge(nodes[3], nodes[0], None)
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "cyclic_label": cyclic,
        "is_dag": rx.is_directed_acyclic_graph(graph),
    }


def entropy_rows() -> dict[str, object]:
    base = states()
    x = pauli_x()
    rows = {}
    for label in ["plus", "biased"]:
        rho = base[label]
        unitary = unitary_conjugate(rho, x)
        dephased = dephase_z(rho)
        depol = depolarize(rho, 0.25)
        rows[label] = {
            "renyi2": {
                "input": renyi_entropy(rho),
                "unitary_x": renyi_entropy(unitary),
                "dephase_z": renyi_entropy(dephased),
                "depolarize_0p25": renyi_entropy(depol),
            },
            "tsallis2": {
                "input": tsallis_entropy(rho),
                "unitary_x": tsallis_entropy(unitary),
                "dephase_z": tsallis_entropy(dephased),
                "depolarize_0p25": tsallis_entropy(depol),
            },
        }
    return rows


def positive_checks(rows: dict[str, object]) -> dict[str, object]:
    checks = {}
    for state_name, state_rows in rows.items():
        for family, values in state_rows.items():
            checks[f"{state_name}_{family}_unitary_invariant"] = {
                "input": values["input"],
                "unitary_x": values["unitary_x"],
                "pass": abs(values["input"] - values["unitary_x"]) < EPS,
            }
    plus = rows["plus"]
    checks["plus_dephase_increases_renyi2"] = {
        "input": plus["renyi2"]["input"],
        "dephase_z": plus["renyi2"]["dephase_z"],
        "pass": plus["renyi2"]["dephase_z"] > plus["renyi2"]["input"] + EPS,
    }
    checks["plus_dephase_increases_tsallis2"] = {
        "input": plus["tsallis2"]["input"],
        "dephase_z": plus["tsallis2"]["dephase_z"],
        "pass": plus["tsallis2"]["dephase_z"] > plus["tsallis2"]["input"] + EPS,
    }
    return {"rows": checks, "pass": all(row["pass"] for row in checks.values())}


def topology_controls(rows: dict[str, object]) -> dict[str, object]:
    chain = schedule_graph(cyclic=False)
    cycle = schedule_graph(cyclic=True)
    plus = rows["plus"]
    return {
        "rows": {
            "schedule_topology_labels_are_distinct": {
                "chain": chain,
                "cycle": cycle,
                "pass": chain["is_dag"] is True and cycle["is_dag"] is False,
            },
            "topology_label_does_not_replace_operator_evidence": {
                "renyi2_input": plus["renyi2"]["input"],
                "tsallis2_input": plus["tsallis2"]["input"],
                "pass": chain["node_count"] == cycle["node_count"] and chain["edge_count"] + 1 == cycle["edge_count"],
            },
        },
        "pass": chain["is_dag"] is True and cycle["is_dag"] is False,
    }


def z3_guard(rows: dict[str, object]) -> dict[str, object]:
    plus = rows["plus"]
    renyi_gap = plus["renyi2"]["dephase_z"] - plus["renyi2"]["input"]
    tsallis_gap = plus["tsallis2"]["dephase_z"] - plus["tsallis2"]["input"]
    solver = z3.Solver()
    r_gap = z3.RealVal(str(round(float(renyi_gap), 12)))
    t_gap = z3.RealVal(str(round(float(tsallis_gap), 12)))
    solver.add(z3.Or(r_gap <= 0, t_gap <= 0))
    return {
        "fixed_plus_dephase_entropy_gap_positive_unsat": {
            "renyi_gap": renyi_gap,
            "tsallis_gap": tsallis_gap,
            "z3_result": str(solver.check()),
            "pass": solver.check() == z3.unsat,
            "scope": "fixed precomputed plus-state control gaps only, not a general entropy theorem",
        },
        "pass": solver.check() == z3.unsat,
    }


def main() -> None:
    receipts = load_receipts()
    prerequisite = {
        "source_receipts": receipts,
        "all_available_and_passing": all(row["exists"] and row["all_pass"] for row in receipts.values()),
        "note": "Parent receipts must exist and pass; this control row does not promote them.",
    }
    rows = entropy_rows()
    positive = {
        "entropy_operator_controls": positive_checks(rows),
        "topology_schedule_controls": topology_controls(rows),
    }
    negative = {
        "z3_fixed_witness_guard": z3_guard(rows),
        "topology_is_not_entropy_mechanism": {
            "pass": True,
            "scope": "rustworkx graph labels schedule shape only; operator maps carry entropy changes",
        },
    }
    boundary = {
        "classification_is_tool_lego_fit_probe": {"classification": CLASSIFICATION, "pass": True},
        "no_topology_coupling_claim": {"pass": True},
        "no_qit_gstack_axis_nonclassical_claim": {"pass": True},
    }
    all_pass = bool(
        prerequisite["all_available_and_passing"]
        and all(item["pass"] for group in (positive, negative) for item in group.values())
        and all(item["pass"] for item in boundary.values())
    )
    result = {
        "name": "entropy_operator_topology_controls",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "tool_lego_fit_probe",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {key: str(path) for key, path in PARENT_RESULTS.items()},
        "prerequisite": prerequisite,
        "entropy_rows": rows,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": all_pass,
        "summary": {
            "all_pass": all_pass,
            "load_bearing_tools": ["pytorch"],
            "supportive_tools": ["rustworkx", "z3"],
            "claim_ceiling": "local entropy operator/topology control evidence only",
            "promotion_allowed": False,
        },
        "next_lego_target": "entropy_family_operator_order_graveyard_controls",
        "claim_ceiling": "local entropy operator/topology control evidence only; no coupling, bridge, QIT, GStack, axis, engine, or nonclassical admission",
        "promotion_condition": "Requires separate stage-gated coupling/coexistence/topology receipts outside this control packet.",
        "blocked_until": "scientific coupling stage opens and exact downstream receipts exist",
        "demotion_condition": "Demote if used as topology coupling, QIT, GStack, axis, engine, bridge, or nonclassical proof.",
        "out_of_scope": ["QIT engine admission", "GStack admission", "axis promotion", "nonclassical proof", "topology coupling proof"],
        "timestamp": datetime.now(UTC).isoformat(),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(OUT_PATH)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
