#!/usr/bin/env python3
"""Min/max entropy operator-topology control microfit.

This bounded packet follows the min/max entropy PyTorch microfit with one
finite control surface: H_min/H_max should be invariant under unitary relabeling,
react differently to dephasing versus support-rank changes, and stay separate
from the rustworkx schedule topology used to label operator order. It is local
tool-lego evidence only, not a coupling, bridge, QIT, GStack, axis, engine, or
nonclassical admission claim.
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
    "Bounded PyTorch min/max entropy operator/topology control microfit. "
    "PyTorch is load-bearing for density operators, support-rank H_max, "
    "dominant-eigenvalue H_min, and finite channel controls; rustworkx is "
    "supportive schedule topology only; z3 is a supportive finite witness "
    "guard. This is not a coupling, bridge, QIT, GStack, axis, engine, or "
    "nonclassical admission."
)

LEGO_IDS = ["min_entropy", "max_entropy", "operator_topology_control"]
PRIMARY_LEGO_IDS = ["min_entropy", "max_entropy"]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density operators, unitary/dephasing/erasure controls, H_min, and H_max values",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "supportive finite schedule graph distinguishing chain and branch labels without driving entropy values",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite Real-arithmetic guard over precomputed min/max entropy witnesses",
    },
    "sympy": {"tried": False, "used": False, "reason": "not needed; parent min/max microfit covers symbolic support"},
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
    "min_max_entropy_classical": RESULT_DIR / "min_max_entropy_classical_results.json",
    "min_max_entropy_torch_microfit": RESULT_DIR / "min_max_entropy_torch_microfit_results.json",
    "pure_lego_density_matrices": RESULT_DIR / "pure_lego_density_matrices_results.json",
    "pytorch_capability": RESULT_DIR / "pytorch_capability_results.json",
}
OUT_PATH = RESULT_DIR / "min_max_entropy_operator_topology_controls_results.json"
EPS = 1e-10
CDTYPE = torch.complex128


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


def density_states() -> dict[str, torch.Tensor]:
    zero = torch.tensor([1.0, 0.0], dtype=CDTYPE)
    plus = torch.tensor([1.0, 1.0], dtype=CDTYPE) / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    return {
        "pure_plus": dm(plus),
        "pure_zero": dm(zero),
        "diag_0p8_0p2": torch.diag(torch.tensor([0.8, 0.2], dtype=torch.float64)).to(CDTYPE),
        "max_mixed": torch.eye(2, dtype=CDTYPE) / 2.0,
    }


def spectrum(rho: torch.Tensor) -> torch.Tensor:
    eigs = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real.clamp_min(0.0)
    total = torch.sum(eigs)
    if float(total.item()) <= EPS:
        raise ValueError("zero-trace density matrix")
    return eigs / total


def min_entropy(rho: torch.Tensor) -> float:
    eigs = spectrum(rho)
    pos = eigs[eigs > 1e-14]
    if pos.numel() == 0:
        return 0.0
    return float((-torch.log2(torch.max(pos))).item())


def max_entropy(rho: torch.Tensor) -> float:
    eigs = spectrum(rho)
    rank = int(torch.sum(eigs > 1e-14).item())
    return float(torch.log2(torch.tensor(float(max(1, rank)), dtype=torch.float64)).item())


def pauli_x() -> torch.Tensor:
    return torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)


def unitary_conjugate(rho: torch.Tensor, unitary: torch.Tensor) -> torch.Tensor:
    return unitary @ rho @ unitary.conj().T


def dephase_z(rho: torch.Tensor) -> torch.Tensor:
    return torch.diag(torch.diagonal(rho)).to(CDTYPE)


def erasure_to_zero(rho: torch.Tensor, p: float) -> torch.Tensor:
    zero = density_states()["pure_zero"]
    return (1.0 - p) * rho + p * zero


def schedule_graph(branch: bool) -> dict[str, object]:
    graph = rx.PyDiGraph()
    nodes = [graph.add_node(name) for name in ["prepare", "unitary_x", "dephase_z", "measure_min_max"]]
    graph.add_edges_from_no_data([(nodes[0], nodes[1]), (nodes[1], nodes[2]), (nodes[2], nodes[3])])
    if branch:
        graph.add_node("erasure_control")
        graph.add_edges_from_no_data([(nodes[0], 4), (4, nodes[3])])
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "branch_label": branch,
        "is_dag": rx.is_directed_acyclic_graph(graph),
    }


def entropy_rows() -> dict[str, object]:
    base = density_states()
    x = pauli_x()
    rows = {}
    for label in ["pure_plus", "diag_0p8_0p2"]:
        rho = base[label]
        unitary = unitary_conjugate(rho, x)
        dephased = dephase_z(rho)
        erased = erasure_to_zero(rho, 0.25)
        rows[label] = {
            "input": {"H_min": min_entropy(rho), "H_max": max_entropy(rho)},
            "unitary_x": {"H_min": min_entropy(unitary), "H_max": max_entropy(unitary)},
            "dephase_z": {"H_min": min_entropy(dephased), "H_max": max_entropy(dephased)},
            "erasure_0p25": {"H_min": min_entropy(erased), "H_max": max_entropy(erased)},
        }
    return rows


def positive_checks(rows: dict[str, object]) -> dict[str, object]:
    checks = {}
    for state_name, state_rows in rows.items():
        for family in ["H_min", "H_max"]:
            checks[f"{state_name}_{family}_unitary_invariant"] = {
                "input": state_rows["input"][family],
                "unitary_x": state_rows["unitary_x"][family],
                "pass": abs(state_rows["input"][family] - state_rows["unitary_x"][family]) < EPS,
            }
    plus = rows["pure_plus"]
    mixed = rows["diag_0p8_0p2"]
    checks["pure_plus_dephase_increases_both_min_and_max"] = {
        "input": plus["input"],
        "dephase_z": plus["dephase_z"],
        "pass": plus["dephase_z"]["H_min"] > plus["input"]["H_min"] + EPS
        and plus["dephase_z"]["H_max"] > plus["input"]["H_max"] + EPS,
    }
    checks["erasure_can_lower_mixed_min_entropy"] = {
        "input": mixed["input"],
        "erasure_0p25": mixed["erasure_0p25"],
        "pass": mixed["erasure_0p25"]["H_min"] < mixed["input"]["H_min"] - EPS,
    }
    return {"rows": checks, "pass": all(row["pass"] for row in checks.values())}


def topology_controls(rows: dict[str, object]) -> dict[str, object]:
    chain = schedule_graph(branch=False)
    branch = schedule_graph(branch=True)
    control_rows = {
        "schedule_topology_labels_are_distinct": {
            "chain": chain,
            "branch": branch,
            "pass": chain["is_dag"] is True and branch["is_dag"] is True and branch["edge_count"] > chain["edge_count"],
            "scope": "rustworkx support only: this distinguishes finite schedule labels, not entropy dynamics",
        },
    }
    return {
        "rows": control_rows,
        "pass": all(row["pass"] for row in control_rows.values()),
    }


def z3_guard(rows: dict[str, object]) -> dict[str, object]:
    plus = rows["pure_plus"]
    hmin_gap = plus["dephase_z"]["H_min"] - plus["input"]["H_min"]
    hmax_gap = plus["dephase_z"]["H_max"] - plus["input"]["H_max"]
    solver = z3.Solver()
    solver.add(
        z3.Or(
            z3.RealVal(str(round(float(hmin_gap), 12))) <= 0,
            z3.RealVal(str(round(float(hmax_gap), 12))) <= 0,
        )
    )
    verdict = solver.check()
    return {
        "fixed_plus_dephase_min_max_gap_positive_unsat": {
            "H_min_gap": hmin_gap,
            "H_max_gap": hmax_gap,
            "z3_result": str(verdict),
            "pass": verdict == z3.unsat,
            "scope": "fixed precomputed plus-state min/max entropy gaps only, not a general entropy theorem",
        },
        "pass": verdict == z3.unsat,
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
        "min_max_operator_controls": positive_checks(rows),
        "topology_schedule_controls": topology_controls(rows),
    }
    negative = {
        "z3_fixed_witness_guard": z3_guard(rows),
    }
    boundary = {
        "classification_is_tool_lego_fit_probe": {"classification": CLASSIFICATION, "pass": True},
        "no_topology_coupling_claim": {"pass": True},
        "no_qit_gstack_axis_nonclassical_claim": {"pass": True},
        "topology_is_not_entropy_mechanism": {
            "pass": True,
            "scope": "rustworkx graph labels schedule shape only; no topology-label invariance theorem is claimed",
        },
        "topology_entropy_independence_deferred": {
            "pass": True,
            "scope": "a future coupling packet must explicitly connect topology labels to operator execution before testing invariance",
        },
    }
    all_pass = bool(
        prerequisite["all_available_and_passing"]
        and all(item["pass"] for group in (positive, negative) for item in group.values())
        and all(item["pass"] for item in boundary.values())
    )
    result = {
        "name": "min_max_entropy_operator_topology_controls",
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
            "claim_ceiling": "local min/max entropy operator/topology control evidence only",
            "promotion_allowed": False,
        },
        "next_lego_target": "min_max_entropy_operator_order_graveyard_controls",
        "claim_ceiling": "local min/max entropy operator/topology control evidence only; no coupling, bridge, QIT, GStack, axis, engine, or nonclassical admission",
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
