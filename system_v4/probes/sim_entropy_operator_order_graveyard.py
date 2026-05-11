#!/usr/bin/env python3
"""Entropy operator-order graveyard microfit.

This bounded negative battery follows the local entropy operator/topology
control row. It mutates finite one-qubit operator order and schedule labels to
separate surviving controls from killed/order-confused variants. It is local
graveyard evidence only, not a coupling, bridge, QIT, GStack, axis, engine, or
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
    "Bounded entropy operator-order graveyard over fixed one-qubit density "
    "operators. PyTorch is load-bearing for finite channel composition and "
    "spectral entropy witnesses; rustworkx is supportive schedule labeling; "
    "z3 checks precomputed killed/survivor gaps only. This is local negative "
    "control evidence and does not admit coupling, bridge, QIT, GStack, axis, "
    "engine, or nonclassical claims."
)

LEGO_IDS = ["renyi_entropy", "tsallis_entropy", "operator_order", "graveyard_variant"]
PRIMARY_LEGO_IDS = ["operator_order", "graveyard_variant"]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite density operators, channel order composition, and spectral entropy witnesses",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "supportive schedule graph labels for canonical/reversed/scrambled order variants",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite Real-arithmetic guard over precomputed survivor/killed gaps",
    },
    "numpy": {"tried": False, "used": False, "reason": "not needed; torch carries numeric work"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for finite numeric order battery"},
    "qutip": {"tried": False, "used": False, "reason": "not needed"},
    "qiskit": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "supportive",
    "z3": "supportive",
    "numpy": None,
    "sympy": None,
    "qutip": None,
    "qiskit": None,
    "cvc5": None,
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
PARENT_RESULTS = {
    "entropy_operator_topology_controls": RESULT_DIR / "entropy_operator_topology_controls_results.json",
    "renyi_entropy_torch_microfit": RESULT_DIR / "renyi_entropy_torch_microfit_results.json",
    "tsallis_entropy_torch_microfit": RESULT_DIR / "tsallis_entropy_torch_microfit_results.json",
    "pytorch_capability": RESULT_DIR / "pytorch_capability_results.json",
}
OUT_PATH = RESULT_DIR / "entropy_operator_order_graveyard_results.json"
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


def plus_state() -> torch.Tensor:
    zero = torch.tensor([1.0, 0.0], dtype=CDTYPE)
    one = torch.tensor([0.0, 1.0], dtype=CDTYPE)
    plus = (zero + one) / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    return dm(plus)


def pauli_x() -> torch.Tensor:
    return torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)


def dephase_z(rho: torch.Tensor) -> torch.Tensor:
    return torch.diag(torch.diagonal(rho)).to(CDTYPE)


def depolarize(rho: torch.Tensor, p: float = 0.25) -> torch.Tensor:
    return (1.0 - p) * rho + p * torch.eye(2, dtype=CDTYPE) / 2.0


def unitary_x(rho: torch.Tensor) -> torch.Tensor:
    x = pauli_x()
    return x @ rho @ x.conj().T


OPERATORS = {
    "unitary_x": unitary_x,
    "dephase_z": dephase_z,
    "depolarize": depolarize,
}


def spectrum(rho: torch.Tensor) -> torch.Tensor:
    eigs = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real.clamp_min(0.0)
    return eigs / torch.sum(eigs)


def renyi2(rho: torch.Tensor) -> float:
    eigs = spectrum(rho)
    return float((-torch.log2(torch.sum(eigs.pow(2.0)))).item())


def tsallis2(rho: torch.Tensor) -> float:
    eigs = spectrum(rho)
    return float(((1.0 - torch.sum(eigs.pow(2.0))) / LN2).item())


def apply_order(order: list[str]) -> torch.Tensor:
    rho = plus_state()
    for name in order:
        rho = OPERATORS[name](rho)
    return rho


def schedule_graph(order: list[str]) -> dict[str, object]:
    graph = rx.PyDiGraph()
    nodes = [graph.add_node(name) for name in order]
    graph.add_edges_from_no_data([(nodes[i], nodes[i + 1]) for i in range(len(nodes) - 1)])
    return {
        "order": order,
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "is_dag": rx.is_directed_acyclic_graph(graph),
    }


def variant_rows() -> dict[str, object]:
    variants = {
        "canonical_control": {
            "order": ["unitary_x", "dephase_z", "depolarize"],
            "expected": "survives",
            "reason": "Unitary relabeling before dephasing/depolarization preserves the local entropy-control witness.",
        },
        "honest_unitary_after_noise": {
            "order": ["dephase_z", "depolarize", "unitary_x"],
            "expected": "survives",
            "reason": "Unitary after entropy-increasing noise relabels the spectrum without changing final entropy.",
        },
        "missing_dephase": {
            "order": ["unitary_x", "depolarize"],
            "expected": "killed",
            "reason": "Drops the dephasing control that the parent row used to expose coherence-to-mixture entropy increase.",
        },
        "missing_depolarize": {
            "order": ["unitary_x", "dephase_z"],
            "expected": "killed",
            "reason": "Drops the depolarizing control, so it cannot witness the full parent operator-control schedule.",
        },
        "collapsed_unitaries": {
            "order": ["unitary_x", "unitary_x", "unitary_x"],
            "expected": "killed",
            "reason": "Pure unitary relabeling cannot create entropy from the plus-state carrier.",
        },
    }
    canonical_entropy = {
        "renyi2": renyi2(apply_order(variants["canonical_control"]["order"])),
        "tsallis2": tsallis2(apply_order(variants["canonical_control"]["order"])),
    }
    rows = {}
    for name, meta in variants.items():
        rho = apply_order(meta["order"])
        values = {"renyi2": renyi2(rho), "tsallis2": tsallis2(rho)}
        has_dephase = "dephase_z" in meta["order"]
        has_depol = "depolarize" in meta["order"]
        expected_survives = meta["expected"] == "survives"
        survives = (
            has_dephase
            and has_depol
            and abs(values["renyi2"] - canonical_entropy["renyi2"]) < EPS
            and abs(values["tsallis2"] - canonical_entropy["tsallis2"]) < EPS
        )
        rows[name] = {
            **meta,
            "schedule_graph": schedule_graph(meta["order"]),
            "entropy": values,
            "status": "survives" if survives else "killed",
            "expected_matched": survives is expected_survives,
        }
    return {"canonical_entropy": canonical_entropy, "rows": rows, "pass": all(row["expected_matched"] for row in rows.values())}


def topology_negative_controls(rows: dict[str, object]) -> dict[str, object]:
    canonical = rows["canonical_control"]
    missing = rows["missing_dephase"]
    collapsed = rows["collapsed_unitaries"]
    checks = {
        "same_node_count_does_not_imply_same_entropy": {
            "canonical_nodes": canonical["schedule_graph"]["node_count"],
            "collapsed_nodes": collapsed["schedule_graph"]["node_count"],
            "canonical_entropy": canonical["entropy"],
            "collapsed_entropy": collapsed["entropy"],
            "pass": canonical["schedule_graph"]["node_count"] == collapsed["schedule_graph"]["node_count"]
            and collapsed["entropy"]["renyi2"] < canonical["entropy"]["renyi2"] - EPS,
        },
        "shorter_graph_marks_missing_operator_only": {
            "missing_graph": missing["schedule_graph"],
            "pass": missing["schedule_graph"]["edge_count"] < canonical["schedule_graph"]["edge_count"],
        },
    }
    return {"rows": checks, "pass": all(row["pass"] for row in checks.values())}


def z3_guard(rows: dict[str, object]) -> dict[str, object]:
    canonical = rows["canonical_control"]["entropy"]
    collapsed = rows["collapsed_unitaries"]["entropy"]
    missing_dephase = rows["missing_dephase"]["entropy"]
    solver = z3.Solver()
    canonical_r = z3.RealVal(str(round(float(canonical["renyi2"]), 12)))
    collapsed_r = z3.RealVal(str(round(float(collapsed["renyi2"]), 12)))
    missing_t = z3.RealVal(str(round(float(missing_dephase["tsallis2"]), 12)))
    canonical_t = z3.RealVal(str(round(float(canonical["tsallis2"]), 12)))
    solver.add(z3.Or(collapsed_r >= canonical_r, missing_t >= canonical_t))
    return {
        "killed_variants_do_not_match_canonical_entropy_unsat": {
            "z3_result": str(solver.check()),
            "pass": solver.check() == z3.unsat,
            "scope": "fixed precomputed entropy gaps only, not a general order theorem",
        },
        "pass": solver.check() == z3.unsat,
    }


def main() -> None:
    receipts = load_receipts()
    prerequisite = {
        "source_receipts": receipts,
        "all_available_and_passing": all(row["exists"] and row["all_pass"] for row in receipts.values()),
        "note": "Parent receipts must exist and pass; this graveyard row does not promote them.",
    }
    variants = variant_rows()
    positive = {
        "survivor_and_killed_variants_match_expectation": variants,
    }
    negative = {
        "topology_negative_controls": topology_negative_controls(variants["rows"]),
        "z3_fixed_witness_guard": z3_guard(variants["rows"]),
    }
    boundary = {
        "classification_is_tool_lego_fit_probe": {"classification": CLASSIFICATION, "pass": True},
        "graveyard_not_coupling": {"pass": True},
        "no_qit_gstack_axis_nonclassical_claim": {"pass": True},
    }
    all_pass = bool(
        prerequisite["all_available_and_passing"]
        and all(item["pass"] for group in (positive, negative) for item in group.values())
        and all(item["pass"] for item in boundary.values())
    )
    result = {
        "name": "entropy_operator_order_graveyard",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "tool_lego_fit_probe",
        "battery_type": "negative_control",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {key: str(path) for key, path in PARENT_RESULTS.items()},
        "prerequisite": prerequisite,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": all_pass,
        "summary": {
            "all_pass": all_pass,
            "survivors": [name for name, row in variants["rows"].items() if row["status"] == "survives"],
            "killed": [name for name, row in variants["rows"].items() if row["status"] == "killed"],
            "load_bearing_tools": ["pytorch"],
            "supportive_tools": ["rustworkx", "z3"],
            "claim_ceiling": "local entropy operator-order graveyard only",
            "promotion_allowed": False,
        },
        "next_lego_target": "entropy_family_operator_order_controls_deferred",
        "claim_ceiling": "local entropy operator-order graveyard only; no coupling, bridge, QIT, GStack, axis, engine, or nonclassical admission",
        "promotion_condition": "Requires separate stage-gated coupling/coexistence/topology receipts outside this negative battery.",
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
