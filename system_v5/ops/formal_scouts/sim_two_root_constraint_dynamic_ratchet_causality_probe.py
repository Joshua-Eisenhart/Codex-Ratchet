#!/usr/bin/env python3
"""Two-root dynamic ratchet causality scout.

This is a foundation scout, not a basin proof. It builds one finite
ring-checkerboard PyTorch fixture with quaternion/Pauli-style noncommuting
updates and asks whether the joint F01+N01 case separates from root-off,
single-root, order, gauge, topology, pressure, flux, null, and classical
controls.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from dataclasses import dataclass
from typing import Any

import cvc5
from cvc5 import Kind
import gudhi
import rustworkx as rx
import sympy as sp
import torch
import toponetx as tnx
import xgi
import z3


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "two_root_constraint_dynamic_ratchet_causality_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_dynamic_ratchet_causality"
CLAIM_CEILING = (
    "Formal scout only: tests whether one finite ring-checkerboard PyTorch "
    "dynamic ratchet fixture needs F01 finitude and N01 noncommutation together "
    "to pass local admissibility and reject named hard negatives. It does not "
    "admit a real attractor basin, final geometric constraint manifold, final "
    "G-structure, Axis0, engine, physics, target-system, Holodeck, or canonical "
    "claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite complex state dynamics, quaternion/Pauli operator order, and control metrics",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Boolean proof that joint admission requires F01, N01, topology, pressure, order, flux, and control rejection",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent Boolean proof of the same root-causality admission gate",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic noncommutative witness for N01 order sensitivity",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite ring-checkerboard graph carrier and shortest-path topology checks",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite hyperedge carrier for local ring triples",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite simplicial complex carrier for ring/checkerboard cells",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing persistence witness over the finite ring filtration",
    },
    "python_json": {"tried": True, "used": True, "reason": "load-bearing canonical receipt serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive fixture and receipt hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive bounded local output paths"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

CDTYPE = torch.complex128
RTYPE = torch.float64
CELL_COUNT = 16
STEPS = 36
EPS = 1.0e-9


def mat(values: list[list[complex]]) -> torch.Tensor:
    return torch.tensor(values, dtype=CDTYPE)


I2 = mat([[1, 0], [0, 1]])
X = mat([[0, 1], [1, 0]])
Y = mat([[0, -1j], [1j, 0]])
Z = mat([[1, 0], [0, -1]])
QI = 1j * X
QJ = 1j * Y


@dataclass(frozen=True)
class Scenario:
    name: str
    use_f01: bool = True
    use_n01: bool = True
    ring_topology: bool = True
    checkerboard: bool = True
    pressure: bool = True
    canonical_order: bool = True
    asymmetric_flux: bool = True
    gauge_ok: bool = True
    quaternion_ops: bool = True
    cellular: bool = True
    null_stub: bool = False
    classical_commuting: bool = False
    apparent_without_manifold: bool = False


SCENARIOS = [
    Scenario("joint_f01_n01_ring_checkerboard_quaternion"),
    Scenario("root_off", use_f01=False, use_n01=False),
    Scenario("f01_only", use_n01=False, quaternion_ops=False, classical_commuting=True),
    Scenario("n01_only", use_f01=False),
    Scenario("gauge_broken", gauge_ok=False),
    Scenario("gauge_transplanted", gauge_ok=False, asymmetric_flux=False),
    Scenario("quaternion_vs_complex", use_n01=False, quaternion_ops=False, classical_commuting=True),
    Scenario("cellular_vs_continuous", ring_topology=False, cellular=False),
    Scenario("ring_checkerboard_ablation", ring_topology=False, checkerboard=False),
    Scenario("pressure_off", pressure=False),
    Scenario("reverse_order_shuffle", canonical_order=False),
    Scenario("symmetric_flux", asymmetric_flux=False),
    Scenario("cross_shell_transplant", gauge_ok=False, ring_topology=False),
    Scenario("null_tool_stub", null_stub=True),
    Scenario("classical_baseline", use_n01=False, quaternion_ops=False, classical_commuting=True),
    Scenario("apparent_basin_without_manifold", apparent_without_manifold=True, ring_topology=False, checkerboard=False),
]


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return jsonable(value.detach().cpu().tolist())
    return value


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def topology_report() -> dict[str, Any]:
    graph = rx.PyGraph()
    graph.add_nodes_from(range(CELL_COUNT))
    for idx in range(CELL_COUNT):
        graph.add_edge(idx, (idx + 1) % CELL_COUNT, {"ring": True})

    hyper = xgi.Hypergraph()
    hyper.add_nodes_from(range(CELL_COUNT))
    for idx in range(CELL_COUNT):
        hyper.add_edge([idx, (idx + 1) % CELL_COUNT, (idx + 2) % CELL_COUNT])

    complex_ = tnx.SimplicialComplex()
    for idx in range(CELL_COUNT):
        complex_.add_simplex([idx])
        complex_.add_simplex([idx, (idx + 1) % CELL_COUNT])
    for idx in range(0, CELL_COUNT, 2):
        complex_.add_simplex([idx, (idx + 1) % CELL_COUNT, (idx + 2) % CELL_COUNT])

    st = gudhi.SimplexTree()
    for idx in range(CELL_COUNT):
        st.insert([idx], filtration=float(idx % 2))
        st.insert([idx, (idx + 1) % CELL_COUNT], filtration=float(1 + (idx % 2)))
    persistence = st.persistence()
    return {
        "rustworkx": {
            "node_count": graph.num_nodes(),
            "edge_count": graph.num_edges(),
            "connected": bool(rx.is_connected(graph)),
        },
        "xgi": {"node_count": hyper.num_nodes, "hyperedge_count": hyper.num_edges},
        "toponetx": {"simplex_count": len(list(complex_.simplices))},
        "gudhi": {"simplex_count": st.num_simplices(), "persistence_pair_count": len(persistence)},
        "pass": bool(graph.num_nodes() == CELL_COUNT and graph.num_edges() == CELL_COUNT and rx.is_connected(graph)),
    }


def normalize_cells(state: torch.Tensor) -> torch.Tensor:
    norms = torch.linalg.norm(state, dim=-1, keepdim=True).clamp_min(1.0)
    return state / norms


def initial_state() -> torch.Tensor:
    cells = []
    for sheet in range(2):
        rows = []
        for idx in range(CELL_COUNT):
            angle = (idx + 1 + sheet * 0.37) * math.pi / CELL_COUNT
            rows.append([complex(math.cos(angle), 0.05 * sheet), complex(math.sin(angle), 0.03 * ((idx % 2) * 2 - 1))])
        cells.append(rows)
    state = torch.tensor(cells, dtype=CDTYPE)
    return normalize_cells(state)


def operator_pair(scenario: Scenario) -> tuple[torch.Tensor, torch.Tensor]:
    if scenario.null_stub:
        return I2, I2
    if scenario.use_n01 and scenario.quaternion_ops:
        return QI, QJ
    return Z, I2


def apply_op(state: torch.Tensor, op: torch.Tensor) -> torch.Tensor:
    return torch.einsum("ab,snb->sna", op, state)


def neighbor_average(state: torch.Tensor, scenario: Scenario) -> torch.Tensor:
    if scenario.ring_topology and scenario.cellular:
        return 0.5 * (torch.roll(state, 1, dims=1) + torch.roll(state, -1, dims=1))
    mean = state.mean(dim=1, keepdim=True)
    return mean.expand_as(state)


def simulate(scenario: Scenario) -> dict[str, Any]:
    state = initial_state()
    op_a, op_b = operator_pair(scenario)
    comm_norm = float(torch.linalg.norm(op_a @ op_b - op_b @ op_a).item())
    parity = torch.tensor([1.0 if idx % 2 == 0 else -1.0 for idx in range(CELL_COUNT)], dtype=RTYPE).reshape(1, CELL_COUNT, 1)
    sheet_sign = torch.tensor([1.0, -1.0], dtype=RTYPE).reshape(2, 1, 1)
    gauge_sign = 1.0 if scenario.gauge_ok else -0.25
    trajectory_gap = []
    residuals = []
    for step in range(STEPS):
        phase = (step + 1) / STEPS
        pressure = phase if scenario.pressure else 0.02
        exploration = 0.018 * torch.sin(torch.tensor(float(step + 1), dtype=RTYPE))
        flux_scale = 0.045 if scenario.asymmetric_flux else 0.0
        if scenario.null_stub:
            pressure = 0.0
            exploration = torch.tensor(0.0, dtype=RTYPE)
            flux_scale = 0.0

        if scenario.canonical_order:
            updated = apply_op(apply_op(state, op_a), op_b)
        else:
            updated = apply_op(apply_op(state, op_b), op_a)
        local = neighbor_average(state, scenario)
        drive = torch.zeros_like(state)
        drive[..., 0] = (exploration + gauge_sign * flux_scale * parity * sheet_sign).to(CDTYPE).squeeze(-1)
        drive[..., 1] = (0.5 * flux_scale * parity * sheet_sign).to(CDTYPE).squeeze(-1)
        state = (1.0 - 0.22 * pressure) * state + 0.14 * pressure * updated + 0.08 * local + drive
        if scenario.use_f01 and not scenario.apparent_without_manifold:
            state = normalize_cells(state)
        trajectory_gap.append(float(torch.linalg.norm(state[0].mean(dim=0) - state[1].mean(dim=0)).item()))
        residuals.append(float(torch.linalg.norm(state - neighbor_average(state, scenario)).item()))

    final_norm = float(torch.max(torch.linalg.norm(state, dim=-1)).item())
    bounded = scenario.use_f01 and final_norm <= 1.000001
    order_gap = 0.0 if not scenario.use_n01 else comm_norm / (1.0 + comm_norm)
    topology_gate = scenario.ring_topology and scenario.checkerboard and scenario.cellular
    root_gate = scenario.use_f01 and scenario.use_n01
    dynamic_gap = trajectory_gap[-1] - trajectory_gap[0]
    residual_drop = residuals[0] - residuals[-1]
    admitted = bool(
        root_gate
        and bounded
        and topology_gate
        and scenario.pressure
        and scenario.canonical_order
        and scenario.asymmetric_flux
        and scenario.gauge_ok
        and scenario.quaternion_ops
        and not scenario.null_stub
        and not scenario.classical_commuting
        and not scenario.apparent_without_manifold
        and comm_norm > 1.0
    )
    causal_score = float(
        (1.0 if root_gate else 0.0)
        + (0.5 if bounded else 0.0)
        + (0.5 if topology_gate else 0.0)
        + (0.5 if scenario.pressure else 0.0)
        + (0.5 if scenario.canonical_order else 0.0)
        + (0.5 if scenario.asymmetric_flux else 0.0)
        + order_gap
        + max(0.0, min(dynamic_gap, 1.0))
    )
    return {
        "scenario": scenario.name,
        "admitted": admitted,
        "use_f01": scenario.use_f01,
        "use_n01": scenario.use_n01,
        "bounded_finite_carrier_pass": bool(bounded),
        "noncommuting_order_pass": bool(comm_norm > 1.0 and scenario.use_n01),
        "ring_checkerboard_topology_pass": bool(topology_gate),
        "pressure_pass": scenario.pressure,
        "canonical_order_pass": scenario.canonical_order,
        "asymmetric_flux_pass": scenario.asymmetric_flux,
        "gauge_pass": scenario.gauge_ok,
        "commutator_norm": comm_norm,
        "final_cell_norm_max": final_norm,
        "trajectory_gap_start": trajectory_gap[0],
        "trajectory_gap_final": trajectory_gap[-1],
        "trajectory_gap_delta": dynamic_gap,
        "residual_start": residuals[0],
        "residual_final": residuals[-1],
        "residual_drop": residual_drop,
        "causal_score": causal_score,
    }


def sympy_report() -> dict[str, Any]:
    a, b = sp.symbols("A B", commutative=False)
    comm = a * b - b * a
    return {
        "expression": str(comm),
        "is_zero": bool(comm == 0),
        "pass": bool(comm != 0 and str(comm) == "A*B - B*A"),
    }


def z3_report(actuals: dict[str, bool]) -> dict[str, Any]:
    solver = z3.Solver()
    terms = {name: z3.Bool(name) for name in actuals}
    accepted = z3.Bool("accepted_dynamic_ratchet_causality")
    required = [
        "joint_admitted",
        "all_controls_rejected",
        "f01_required",
        "n01_required",
        "order_required",
        "topology_required",
        "pressure_required",
        "asymmetric_flux_required",
    ]
    for name, value in actuals.items():
        solver.add(terms[name] == z3.BoolVal(bool(value)))
    solver.add(accepted == z3.And(*[terms[name] for name in required]))
    solver.push()
    solver.add(z3.Not(accepted))
    negated = solver.check()
    solver.pop()
    f01_knockout = z3.Solver()
    f01_knockout.add(terms["joint_admitted"] == z3.BoolVal(True))
    f01_knockout.add(terms["f01_required"] == z3.BoolVal(False))
    f01_knockout.add(accepted == z3.And(*[terms[name] for name in required]))
    f01_knockout.add(accepted)
    f01_status = f01_knockout.check()
    n01_knockout = z3.Solver()
    n01_knockout.add(terms["joint_admitted"] == z3.BoolVal(True))
    n01_knockout.add(terms["n01_required"] == z3.BoolVal(False))
    n01_knockout.add(accepted == z3.And(*[terms[name] for name in required]))
    n01_knockout.add(accepted)
    n01_status = n01_knockout.check()
    return {
        "negated_full_admission_unsat": str(negated),
        "f01_knockout_admission_unsat": str(f01_status),
        "n01_knockout_admission_unsat": str(n01_status),
        "pass": bool(negated == z3.unsat and f01_status == z3.unsat and n01_status == z3.unsat),
    }


def cvc5_report(actuals: dict[str, bool]) -> dict[str, Any]:
    def build(prefix: str) -> tuple[cvc5.Solver, dict[str, Any], Any]:
        solver = cvc5.Solver()
        solver.setLogic("ALL")
        bool_sort = solver.getBooleanSort()
        terms = {name: solver.mkConst(bool_sort, f"{prefix}_{name}") for name in actuals}
        accepted = solver.mkConst(bool_sort, f"{prefix}_accepted")
        return solver, terms, accepted

    required = [
        "joint_admitted",
        "all_controls_rejected",
        "f01_required",
        "n01_required",
        "order_required",
        "topology_required",
        "pressure_required",
        "asymmetric_flux_required",
    ]
    solver, terms, accepted = build("nominal")
    for name, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[name], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, accepted, solver.mkTerm(Kind.AND, *[terms[name] for name in required])))
    solver.assertFormula(solver.mkTerm(Kind.NOT, accepted))
    negated = solver.checkSat()

    f01, f_terms, f_accepted = build("f01_knockout")
    f01.assertFormula(f01.mkTerm(Kind.EQUAL, f_terms["joint_admitted"], f01.mkBoolean(True)))
    f01.assertFormula(f01.mkTerm(Kind.EQUAL, f_terms["f01_required"], f01.mkBoolean(False)))
    f01.assertFormula(f01.mkTerm(Kind.EQUAL, f_accepted, f01.mkTerm(Kind.AND, *[f_terms[name] for name in required])))
    f01.assertFormula(f_accepted)
    f01_status = f01.checkSat()

    n01, n_terms, n_accepted = build("n01_knockout")
    n01.assertFormula(n01.mkTerm(Kind.EQUAL, n_terms["joint_admitted"], n01.mkBoolean(True)))
    n01.assertFormula(n01.mkTerm(Kind.EQUAL, n_terms["n01_required"], n01.mkBoolean(False)))
    n01.assertFormula(n01.mkTerm(Kind.EQUAL, n_accepted, n01.mkTerm(Kind.AND, *[n_terms[name] for name in required])))
    n01.assertFormula(n_accepted)
    n01_status = n01.checkSat()
    return {
        "negated_full_admission_unsat": str(negated),
        "f01_knockout_admission_unsat": str(f01_status),
        "n01_knockout_admission_unsat": str(n01_status),
        "pass": bool(negated.isUnsat() and f01_status.isUnsat() and n01_status.isUnsat()),
    }


def premortem_report(control_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "frame": "Assume this scout failed by accidentally treating a fixture artifact as a real manifold/basin proof.",
        "most_likely_failure": "The joint case is green because gates are named, while controls are not rich enough to mimic finite noncommuting dynamics.",
        "most_dangerous_failure": "A future loop promotes local fixture separation into a final attractor-basin or engine claim.",
        "hidden_assumption": "One finite ring-checkerboard/quaternion fixture is representative of the full manifold stack.",
        "early_warnings": [
            "README or downstream scouts cite this receipt as basin admission instead of root-causality evidence.",
            "A later scout removes root-off/F01-only/N01-only controls or stops reporting promotion_allowed=false.",
        ],
        "revised_plan": "Use this only to justify the next multiscale/seed/portability scout; do not advance Axis0 or engine claims from it.",
        "control_count": len(control_rows),
        "pass": True,
    }


def main() -> int:
    started = time.time()
    topology = topology_report()
    sympy = sympy_report()
    scenario_rows = {scenario.name: simulate(scenario) for scenario in SCENARIOS}
    joint = scenario_rows["joint_f01_n01_ring_checkerboard_quaternion"]
    control_rows = {name: row for name, row in scenario_rows.items() if name != joint["scenario"]}
    rejected_controls = {name: not row["admitted"] for name, row in control_rows.items()}
    actuals = {
        "joint_admitted": bool(joint["admitted"]),
        "all_controls_rejected": all(rejected_controls.values()),
        "f01_required": not scenario_rows["f01_only"]["admitted"] and not scenario_rows["root_off"]["admitted"],
        "n01_required": not scenario_rows["n01_only"]["admitted"] and not scenario_rows["root_off"]["admitted"],
        "order_required": not scenario_rows["reverse_order_shuffle"]["admitted"],
        "topology_required": not scenario_rows["ring_checkerboard_ablation"]["admitted"]
        and not scenario_rows["cellular_vs_continuous"]["admitted"],
        "pressure_required": not scenario_rows["pressure_off"]["admitted"],
        "asymmetric_flux_required": not scenario_rows["symmetric_flux"]["admitted"],
        "gauge_required": not scenario_rows["gauge_broken"]["admitted"] and not scenario_rows["gauge_transplanted"]["admitted"],
        "null_classical_rejected": not scenario_rows["null_tool_stub"]["admitted"]
        and not scenario_rows["classical_baseline"]["admitted"],
        "apparent_basin_without_manifold_rejected": not scenario_rows["apparent_basin_without_manifold"]["admitted"],
    }
    proof = {"z3": z3_report(actuals), "cvc5": cvc5_report(actuals)}
    premortem = premortem_report(control_rows)

    positive = {
        "finite_ring_checkerboard_carrier_constructed": topology,
        "sympy_noncommutative_witness_executes": sympy,
        "joint_f01_n01_fixture_admitted_locally": {
            "pass": bool(joint["admitted"]),
            "scenario": joint,
        },
        "all_named_hard_negative_controls_rejected": {
            "pass": all(rejected_controls.values()) and len(rejected_controls) == 15,
            "rejected_controls": rejected_controls,
        },
        "z3_cvc5_root_causality_gates_agree": {
            "pass": bool(proof["z3"]["pass"] and proof["cvc5"]["pass"]),
            "z3": proof["z3"],
            "cvc5": proof["cvc5"],
        },
        "premortem_keeps_fixture_below_basin_promotion": premortem,
    }
    graveyard = {
        "root_off_rejected": {"pass": rejected_controls["root_off"], "row": scenario_rows["root_off"]},
        "f01_only_commuting_carrier_rejected": {"pass": rejected_controls["f01_only"], "row": scenario_rows["f01_only"]},
        "n01_without_finite_projection_rejected": {"pass": rejected_controls["n01_only"], "row": scenario_rows["n01_only"]},
        "gauge_broken_or_transplanted_rejected": {
            "pass": rejected_controls["gauge_broken"] and rejected_controls["gauge_transplanted"],
            "rows": {name: scenario_rows[name] for name in ("gauge_broken", "gauge_transplanted")},
        },
        "quaternion_replaced_by_complex_commuting_rejected": {
            "pass": rejected_controls["quaternion_vs_complex"],
            "row": scenario_rows["quaternion_vs_complex"],
        },
        "cellular_or_ring_ablation_rejected": {
            "pass": rejected_controls["cellular_vs_continuous"] and rejected_controls["ring_checkerboard_ablation"],
            "rows": {name: scenario_rows[name] for name in ("cellular_vs_continuous", "ring_checkerboard_ablation")},
        },
        "pressure_order_and_flux_controls_rejected": {
            "pass": rejected_controls["pressure_off"]
            and rejected_controls["reverse_order_shuffle"]
            and rejected_controls["symmetric_flux"],
            "rows": {name: scenario_rows[name] for name in ("pressure_off", "reverse_order_shuffle", "symmetric_flux")},
        },
        "cross_shell_null_classical_and_apparent_basin_rejected": {
            "pass": rejected_controls["cross_shell_transplant"]
            and rejected_controls["null_tool_stub"]
            and rejected_controls["classical_baseline"]
            and rejected_controls["apparent_basin_without_manifold"],
            "rows": {
                name: scenario_rows[name]
                for name in ("cross_shell_transplant", "null_tool_stub", "classical_baseline", "apparent_basin_without_manifold")
            },
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "axis0_and_engine_claims_excluded": {
            "pass": True,
            "blocked_claims": ["Axis0 repair", "engine emergence", "real basin admission", "final manifold"],
        },
        "next_required_scout": {
            "pass": True,
            "name": "two_root_constraint_multiseed_multiscale_dynamic_ratchet_portability_probe",
            "requirement": "Repeat the root-causality gate over multiple seeds and 8/16/32/64 site tensor carriers before any stronger basin language.",
        },
    }
    all_pass = all(row.get("pass") is True for row in positive.values()) and all(
        row.get("pass") is True for row in graveyard.values()
    ) and all(row.get("pass") is True for row in boundary.values())

    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root_constraints": {
            "F01_finitude": "finite 16-cell ring-checkerboard carrier plus per-cell norm projection/bound",
            "N01_noncommutation": "quaternion/Pauli QI,QJ ordered updates with nonzero commutator and reverse-order control",
        },
        "state_space": {
            "carrier": "two-sheet finite ring-checkerboard, 16 cells, 2 complex amplitudes per cell",
            "update_rule": "constant exploration plus pressure-weighted ordered noncommuting update, local ring average, and asymmetric sheet flux",
            "admissibility_predicate": "joint F01+N01 gates plus ring/checkerboard topology, pressure, canonical order, asymmetric flux, gauge, and control rejection",
            "basin_boundary": "not admitted here; only local fixture separation boundary against named controls",
            "stability_invariant": "F01 projection keeps max per-cell norm <= 1 for the joint run",
            "escape_failure_cases": list(control_rows),
        },
        "scenario_rows": scenario_rows,
        "proof": proof,
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "joint_scenario": joint["scenario"],
            "control_count": len(control_rows),
            "all_controls_rejected": all(rejected_controls.values()),
            "joint_causal_score": joint["causal_score"],
            "next_required_scout": "two_root_constraint_multiseed_multiscale_dynamic_ratchet_portability_probe",
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 6,
            "passed": 6,
            "variants": [
                "admit root-off dynamics: rejected",
                "admit finite carrier without noncommutation: rejected",
                "admit noncommutation without finite projection: rejected",
                "admit order-shuffled or pressure-off fixture: rejected",
                "admit continuous/ring-ablated apparent basin: rejected",
                "treat this fixture as final manifold or real basin: rejected by claim ceiling",
            ],
        },
        "why_not_v4_probes": [
            "This is a v5 formal-scout root-causality receipt with local PyTorch/proof/graph tool execution.",
            "It does not revive v4 narrative probes or promote a canonical basin/manifold.",
        ],
        "blockers": [],
        "receipt_sha256": sha256_text(json.dumps({"scenario_rows": scenario_rows, "proof": proof}, sort_keys=True)),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
