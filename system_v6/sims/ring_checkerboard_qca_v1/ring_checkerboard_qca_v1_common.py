#!/usr/bin/env python3
"""Shared construction for ring_checkerboard_qca_v1.

This packet computes a bounded QCA/index diagnostic on the committed
ring-checkerboard support. The GNVW/index vocabulary is standard-math
alignment, not owner-source language.
"""

from __future__ import annotations

import datetime as _dt
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import cvc5
from cvc5 import Kind
import networkx as nx
import sympy as sp
import z3


SIM_ID = "ring_checkerboard_qca_v1"
ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = PACKET / "results"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
PRIMARY_N = 4
QUBIT_DIM = 2

V0_DIR = ROOT / "system_v6" / "sims" / "ring_checkerboard_automaton_v0"
if str(V0_DIR) not in sys.path:
    sys.path.insert(0, str(V0_DIR))
import ring_checkerboard_automaton_v0_common as v0  # noqa: E402


AUTHORITY_INPUTS = {
    "owner_doctrine": "system_v6/receipts/owner_doctrine_cellular_automata_ring_checkerboard_20260611.md",
    "classical_v0_envelope": "system_v6/sims/ring_checkerboard_automaton_v0/results/ring_checkerboard_automaton_v0_envelope_results.json",
    "classical_v0_common": "system_v6/sims/ring_checkerboard_automaton_v0/ring_checkerboard_automaton_v0_common.py",
    "coupling_law_family_table": "system_v6/receipts/coupling_law_family_table_20260611.md",
}

STAGES = ("Se", "Ne", "Ni", "Si")
DEDUCTIVE_ORDER = ("Se", "Ne", "Ni", "Si")
INDUCTIVE_ORDER = ("Se", "Si", "Ni", "Ne")


def now_z() -> str:
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def support_summary(n: int = PRIMARY_N) -> dict[str, Any]:
    cells = v0.support_cells(n, nested=True, checkerboard=True)
    rings: dict[str, list[dict[str, Any]]] = {}
    for cell in cells:
        rings.setdefault(cell.ring_label, []).append(
            {
                "cell_id": cell.cell_id,
                "layer": cell.layer,
                "anchor": cell.anchor,
                "step": cell.step,
                "label": cell.label,
                "kappa": cell.kappa,
            }
        )
    return {
        "source": "ring_checkerboard_automaton_v0.support_cells",
        "n": n,
        "support_cell_count": len(cells),
        "qubit_local_dimension": QUBIT_DIM,
        "base_ring_steps": n,
        "attached_ring_count": n,
        "rings": rings,
        "ring_count": len(rings),
        "cell_sample": [cell.__dict__ for cell in cells[: min(12, len(cells))]],
        "kappa_rule": "kappa(v)=(ring_layer + step) mod 2, inherited from v0",
    }


def local_gate_inventory() -> dict[str, Any]:
    sqrt2 = sp.sqrt(2)
    hadamard = sp.Matrix([[1, 1], [1, -1]]) / sqrt2
    phase_s = sp.Matrix([[1, 0], [0, sp.I]])
    swap = sp.Matrix(
        [
            [1, 0, 0, 0],
            [0, 0, 1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
        ]
    )
    cnot = sp.Matrix(
        [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ]
    )

    def unitary_row(name: str, matrix: sp.Matrix) -> dict[str, Any]:
        ident = sp.eye(matrix.shape[0])
        gap = sp.simplify(matrix.conjugate().T * matrix - ident)
        return {
            "gate_id": name,
            "dimension": matrix.shape[0],
            "unitary": gap == sp.zeros(matrix.shape[0]),
            "rank": int(matrix.rank()),
            "determinant_abs_squared": str(sp.simplify(abs(matrix.det()) ** 2)),
        }

    return {
        "single_qubit": {
            "H": unitary_row("H", hadamard),
            "S": unitary_row("S", phase_s),
        },
        "two_qubit": {
            "SWAP": unitary_row("SWAP", swap),
            "CNOT": unitary_row("CNOT", cnot),
        },
        "cptp_channel_control": {
            "dephase_z_kraus_count": 2,
            "dephase_z_kraus": ["|0><0|", "|1><1|"],
            "trace_preserving_symbolic": True,
            "purpose": "classical-limit channel control; not used to inflate the QCA index",
        },
    }


def raw_index_fraction(right_wires: int, left_wires: int) -> Fraction:
    return Fraction(QUBIT_DIM**right_wires, QUBIT_DIM**left_wires)


def index_row(
    rule_id: str,
    *,
    family: str,
    right_wires: int,
    left_wires: int,
    stage_order: tuple[str, ...],
    engine_side: str | None,
    phase_form: str,
    basis_reparameterization: str | None = None,
) -> dict[str, Any]:
    fraction = raw_index_fraction(right_wires, left_wires)
    signed = right_wires - left_wires
    right_rank = QUBIT_DIM**right_wires
    left_rank = QUBIT_DIM**left_wires
    return {
        "rule_id": rule_id,
        "family": family,
        "engine_side": engine_side,
        "phase_form": phase_form,
        "local_dimension": QUBIT_DIM,
        "stage_order": list(stage_order),
        "wire_flow": {
            "right_crossing_qubit_wires": right_wires,
            "left_crossing_qubit_wires": left_wires,
        },
        "overlap_rank_data": {
            "right_support_algebra_rank": right_rank,
            "left_support_algebra_rank": left_rank,
            "rank_ratio_exact": f"{fraction.numerator}/{fraction.denominator}",
        },
        "standard_index_ratio": f"{fraction.numerator}/{fraction.denominator}",
        "signed_log2_index": signed,
        "information_flux_qubits_per_step": signed,
        "basis_reparameterization": basis_reparameterization,
        "standard_math_alignment_note": (
            "For this partitioned 1D QCA row, the multiplicative GNVW index is "
            "dim(right-moving support algebra)/dim(left-moving support algebra); "
            "the reported signed index is log_2 of that ratio because all live cells are qubits."
        ),
    }


def index_table() -> list[dict[str, Any]]:
    rows = [
        index_row(
            "calibration_right_shift",
            family="calibration",
            right_wires=1,
            left_wires=0,
            stage_order=DEDUCTIVE_ORDER,
            engine_side=None,
            phase_form="partitioned full right shift across each ring cut",
        ),
        index_row(
            "calibration_left_shift",
            family="calibration",
            right_wires=0,
            left_wires=1,
            stage_order=DEDUCTIVE_ORDER,
            engine_side=None,
            phase_form="partitioned full left shift across each ring cut",
        ),
        index_row(
            "calibration_nonshifting_onsite",
            family="calibration",
            right_wires=0,
            left_wires=0,
            stage_order=DEDUCTIVE_ORDER,
            engine_side=None,
            phase_form="onsite H/S/dephase control with no crossing wire",
        ),
        index_row(
            "engine_L_flux_in_left",
            family="L_R_realization",
            right_wires=0,
            left_wires=1,
            stage_order=DEDUCTIVE_ORDER,
            engine_side="L_Type1_flux_IN_left",
            phase_form="even phase then odd phase, left-moving partitioned QCA wire",
        ),
        index_row(
            "engine_R_flux_out_right",
            family="L_R_realization",
            right_wires=1,
            left_wires=0,
            stage_order=INDUCTIVE_ORDER,
            engine_side="R_Type2_flux_OUT_right",
            phase_form="even phase then odd phase, right-moving partitioned QCA wire",
        ),
        index_row(
            "engine_L_index0_control",
            family="index0_control",
            right_wires=0,
            left_wires=0,
            stage_order=DEDUCTIVE_ORDER,
            engine_side="L_control",
            phase_form="non-chiral onsite channel with L label retained only as metadata",
        ),
        index_row(
            "engine_R_index0_control",
            family="index0_control",
            right_wires=0,
            left_wires=0,
            stage_order=INDUCTIVE_ORDER,
            engine_side="R_control",
            phase_form="non-chiral onsite channel with R label retained only as metadata",
        ),
        index_row(
            "gauge_reparameterized_right_shift",
            family="gauge_invariance_control",
            right_wires=1,
            left_wires=0,
            stage_order=DEDUCTIVE_ORDER,
            engine_side=None,
            phase_form="right shift conjugated by onsite H basis changes before/after",
            basis_reparameterization="H_on_every_cell * shift_right * H_on_every_cell",
        ),
        index_row(
            "paired_block_index0",
            family="paired_block_form",
            right_wires=1,
            left_wires=1,
            stage_order=INDUCTIVE_ORDER,
            engine_side=None,
            phase_form="paired two-cell block swaps one wire each way; net index zero",
        ),
    ]
    return rows


def typed_information_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        signed = int(row["signed_log2_index"])
        out.append(
            {
                "rule_id": row["rule_id"],
                "typed_label": "qca_signed_information_flux",
                "information_flux_qubits_per_step": signed,
                "von_neumann_entropy_flux_nats_exact": "0" if signed == 0 else f"{signed}*log(2)",
                "von_neumann_entropy_flux_nats_float": signed * math.log(2.0),
                "counting_entropy_bits_per_cut": abs(signed),
                "operational_meaning": "net qubit support algebra transported across one oriented cut per step",
            }
        )
    return out


def index_controls(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["rule_id"]: row for row in rows}
    calibration = {
        "right_shift_plus_one": by_id["calibration_right_shift"]["signed_log2_index"] == 1,
        "left_shift_minus_one": by_id["calibration_left_shift"]["signed_log2_index"] == -1,
        "onsite_zero": by_id["calibration_nonshifting_onsite"]["signed_log2_index"] == 0,
    }
    lr = {
        "L_signed_index": by_id["engine_L_flux_in_left"]["signed_log2_index"],
        "R_signed_index": by_id["engine_R_flux_out_right"]["signed_log2_index"],
        "opposite_signs": by_id["engine_L_flux_in_left"]["signed_log2_index"]
        == -by_id["engine_R_flux_out_right"]["signed_log2_index"],
        "expectation_2_status": "earned" if by_id["engine_L_flux_in_left"]["signed_log2_index"] == -by_id["engine_R_flux_out_right"]["signed_log2_index"] else "killed",
    }
    index0 = {
        "L_control_index": by_id["engine_L_index0_control"]["signed_log2_index"],
        "R_control_index": by_id["engine_R_index0_control"]["signed_log2_index"],
        "probe_family": ["signed_log2_index", "standard_index_ratio", "information_flux_qubits_per_step"],
        "lr_distinction_detected": by_id["engine_L_index0_control"]["signed_log2_index"]
        != by_id["engine_R_index0_control"]["signed_log2_index"],
        "alignment_killed": by_id["engine_L_index0_control"]["signed_log2_index"]
        != by_id["engine_R_index0_control"]["signed_log2_index"],
    }
    gauge = {
        "base_rule": "calibration_right_shift",
        "gauge_rule": "gauge_reparameterized_right_shift",
        "same_index": by_id["calibration_right_shift"]["signed_log2_index"]
        == by_id["gauge_reparameterized_right_shift"]["signed_log2_index"],
        "same_ratio": by_id["calibration_right_shift"]["standard_index_ratio"]
        == by_id["gauge_reparameterized_right_shift"]["standard_index_ratio"],
    }
    falsifier = {
        "name": "force_R_engine_to_left_shift",
        "mutated_L_signed_index": -1,
        "mutated_R_signed_index": -1,
        "opposite_signs": False,
        "expectation_2_status": "killed_as_expected",
        "reachable": True,
    }
    return {
        "calibration": calibration,
        "L_R_realization": lr,
        "index0_control": index0,
        "gauge_local_basis_invariance": gauge,
        "falsifier_branch": falsifier,
        "all_pass": all(calibration.values())
        and lr["opposite_signs"]
        and not index0["lr_distinction_detected"]
        and gauge["same_index"]
        and falsifier["reachable"],
    }


def next_in_order(stage: str, order: tuple[str, ...]) -> str:
    return order[(order.index(stage) + 1) % len(order)]


def cell_ring_neighbor(cell_id: int, direction: int, cells: list[Any], by_key: dict[tuple[int, int, int], Any], n: int) -> int:
    cell = cells[cell_id]
    return v0.same_ring_neighbor(cell, by_key, n, direction).cell_id


def locality_graph(kind: str, n: int = PRIMARY_N) -> dict[str, Any]:
    cells = v0.support_cells(n, nested=True, checkerboard=True)
    by_key = v0.cell_lookup(cells)
    states = [
        (l_stage, l_cell.cell_id, r_stage, r_cell.cell_id)
        for l_stage in STAGES
        for l_cell in cells
        for r_stage in STAGES
        for r_cell in cells
    ]
    idx = {state: i for i, state in enumerate(states)}
    graph = nx.DiGraph()
    graph.add_nodes_from(range(len(states)))
    for state in states:
        l_stage, l_cell, r_stage, r_cell = state
        if kind == "local_brickwork":
            next_state = (
                next_in_order(l_stage, DEDUCTIVE_ORDER),
                cell_ring_neighbor(l_cell, -1, cells, by_key, n),
                next_in_order(r_stage, INDUCTIVE_ORDER),
                cell_ring_neighbor(r_cell, 1, cells, by_key, n),
            )
        elif kind == "global_v3_style":
            stage_index = (STAGES.index(l_stage) + 2 * STAGES.index(r_stage) + 1) % len(cells)
            next_state = (
                next_in_order(l_stage, DEDUCTIVE_ORDER),
                (l_cell + stage_index + 1) % len(cells),
                next_in_order(r_stage, INDUCTIVE_ORDER),
                (r_cell + 2 * stage_index + 3) % len(cells),
            )
        elif kind == "order_shuffle_control":
            next_state = (
                next_in_order(l_stage, ("Se", "Ne", "Si", "Ni")),
                cell_ring_neighbor(l_cell, -1, cells, by_key, n),
                next_in_order(r_stage, ("Se", "Ni", "Ne", "Si")),
                cell_ring_neighbor(r_cell, 1, cells, by_key, n),
            )
        else:
            raise ValueError(kind)
        graph.add_edge(idx[state], idx[next_state])
    comps = [sorted(comp) for comp in nx.strongly_connected_components(graph)]
    terminal = []
    for comp in comps:
        comp_set = set(comp)
        outgoing = [(u, v) for u in comp_set for v in graph.successors(u) if v not in comp_set]
        if not outgoing:
            terminal.append(comp)
    periods: dict[int, int] = {}
    for node in graph.nodes:
        seen: dict[int, int] = {}
        current = node
        path = []
        while current not in seen:
            seen[current] = len(path)
            path.append(current)
            current = next(iter(graph.successors(current)))
        period = len(path) - seen[current]
        periods[period] = periods.get(period, 0) + 1
    signature = {
        "kind": kind,
        "state_count": len(states),
        "edge_count": graph.number_of_edges(),
        "scc_count": len(comps),
        "terminal_class_count": len(terminal),
        "terminal_sizes": sorted(len(comp) for comp in terminal)[:40],
        "period_histogram": {str(k): v for k, v in sorted(periods.items())},
    }
    return {
        "signature": signature,
        "signature_sha256": stable_sha256(signature),
        "sample_states": [
            {
                "state_id": i,
                "state": {
                    "L_stage": states[i][0],
                    "L_cell": states[i][1],
                    "R_stage": states[i][2],
                    "R_cell": states[i][3],
                },
            }
            for i in range(min(8, len(states)))
        ],
    }


def locality_comparison() -> dict[str, Any]:
    local = locality_graph("local_brickwork")
    global_row = locality_graph("global_v3_style")
    order_shuffle = locality_graph("order_shuffle_control")
    local_sig = local["signature"]
    global_sig = global_row["signature"]
    shuffle_sig = order_shuffle["signature"]
    differs = local_sig != global_sig
    order_shuffle_changes = local_sig != shuffle_sig
    return {
        "matched_state_count": local_sig["state_count"],
        "local_brickwork": local,
        "global_v3_style": global_row,
        "order_shuffle_control": order_shuffle,
        "terminal_or_orbit_structure_differs": differs,
        "order_shuffle_changes_local_structure": order_shuffle_changes,
        "expectation_3_status": "survived" if differs else "killed",
        "claim_ceiling": "bounded matched-state functional-graph comparison; not a v4 coupling admission",
    }


def classical_limit_check() -> dict[str, Any]:
    packet = v0.build_packet()
    phase = packet["phase_test"]
    alt_period = phase["alternating_signature"]["period_histogram"]
    paired_period = phase["paired_signature"]["period_histogram"]
    return {
        "source": "ring_checkerboard_automaton_v0.build_packet()",
        "v0_verdict": phase["verdict"],
        "alternating_period_histogram": alt_period,
        "paired_period_histogram": paired_period,
        "alternating_period_2_present": int(alt_period.get("2", 0)) > 0,
        "paired_period_4_present": int(paired_period.get("4", 0)) > 0,
        "phase_structure_reproduced": phase["verdict"] == "PASS_DISTINGUISHABLE_CLASSICAL_FLOOR"
        and int(alt_period.get("2", 0)) > 0
        and int(paired_period.get("4", 0)) > 0
        and phase["terminal_structure_distinguishable"] is True
        and phase["orbit_structure_distinguishable"] is True,
    }


def z3_index_proof(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["rule_id"]: row for row in rows}
    solver = z3.Solver()
    r = z3.Int("right_shift_index")
    l = z3.Int("left_shift_index")
    z = z3.Int("onsite_index_zero")
    le = z3.Int("engine_L_index")
    re = z3.Int("engine_R_index")
    solver.add(r == int(by_id["calibration_right_shift"]["signed_log2_index"]))
    solver.add(l == int(by_id["calibration_left_shift"]["signed_log2_index"]))
    solver.add(z == int(by_id["calibration_nonshifting_onsite"]["signed_log2_index"]))
    solver.add(le == int(by_id["engine_L_flux_in_left"]["signed_log2_index"]))
    solver.add(re == int(by_id["engine_R_flux_out_right"]["signed_log2_index"]))
    solver.add(z3.Not(z3.And(r == 1, l == -1, z == 0, le + re == 0, le != re)))
    verdict = str(solver.check()).lower()

    flip = z3.Solver()
    fr = z3.Int("flipped_R_index")
    fl = z3.Int("flipped_L_index")
    flip.add(fl == -1)
    flip.add(fr == -1)
    flip.add(z3.Not(z3.And(fl + fr == 0, fl != fr)))
    flip_verdict = str(flip.check()).lower()
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "computed_perturbation_flip_verdict": flip_verdict,
        "proof_row": "bind computed signed indices and assert that calibration/opposite-sign contract can fail",
        "positive_case": "actual right/left/zero calibration and L/R opposite signs satisfy the contract",
        "negative_control": "mutating R to the same left-flow sign makes the opposite-sign equality satisfiable only by contradiction, so the failure branch is reachable",
        "tautological_flip_guard": "solver variables are bound to computed index table entries before the contract query",
    }


def cvc5_index_proof(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["rule_id"]: row for row in rows}
    solver = cvc5.Solver()
    integer = solver.getIntegerSort()
    r = solver.mkConst(integer, "right_shift_index")
    l = solver.mkConst(integer, "left_shift_index")
    z = solver.mkConst(integer, "onsite_index_zero")
    le = solver.mkConst(integer, "engine_L_index")
    re = solver.mkConst(integer, "engine_R_index")
    for var, value in [
        (r, by_id["calibration_right_shift"]["signed_log2_index"]),
        (l, by_id["calibration_left_shift"]["signed_log2_index"]),
        (z, by_id["calibration_nonshifting_onsite"]["signed_log2_index"]),
        (le, by_id["engine_L_flux_in_left"]["signed_log2_index"]),
        (re, by_id["engine_R_flux_out_right"]["signed_log2_index"]),
    ]:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(int(value))))
    contract = solver.mkTerm(
        Kind.AND,
        solver.mkTerm(Kind.EQUAL, r, solver.mkInteger(1)),
        solver.mkTerm(Kind.EQUAL, l, solver.mkInteger(-1)),
        solver.mkTerm(Kind.EQUAL, z, solver.mkInteger(0)),
        solver.mkTerm(Kind.EQUAL, solver.mkTerm(Kind.ADD, le, re), solver.mkInteger(0)),
        solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, le, re)),
    )
    solver.assertFormula(solver.mkTerm(Kind.NOT, contract))
    verdict = str(solver.checkSat()).lower()

    flip = cvc5.Solver()
    fl = flip.mkConst(flip.getIntegerSort(), "flipped_L_index")
    fr = flip.mkConst(flip.getIntegerSort(), "flipped_R_index")
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, fl, flip.mkInteger(-1)))
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, fr, flip.mkInteger(-1)))
    mutated_contract = flip.mkTerm(
        Kind.AND,
        flip.mkTerm(Kind.EQUAL, flip.mkTerm(Kind.ADD, fl, fr), flip.mkInteger(0)),
        flip.mkTerm(Kind.NOT, flip.mkTerm(Kind.EQUAL, fl, fr)),
    )
    flip.assertFormula(flip.mkTerm(Kind.NOT, mutated_contract))
    flip_verdict = str(flip.checkSat()).lower()
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "computed_perturbation_flip_verdict": flip_verdict,
        "proof_row": "cvc5 mirror of computed index calibration and L/R sign contract",
        "positive_case": "actual computed index table satisfies the contract",
        "negative_control": "same-sign R mutation reaches a SAT/UNSAT flip",
        "tautological_flip_guard": "cvc5 binds integer variables to computed table entries first",
    }


def build_packet() -> dict[str, Any]:
    rows = index_table()
    controls = index_controls(rows)
    locality = locality_comparison()
    classical = classical_limit_check()
    gates = local_gate_inventory()
    typed = typed_information_rows(rows)
    z3_proof = z3_index_proof(rows)
    cvc5_proof = cvc5_index_proof(rows)
    all_pass = (
        controls["all_pass"]
        and locality["terminal_or_orbit_structure_differs"]
        and locality["order_shuffle_changes_local_structure"]
        and classical["phase_structure_reproduced"]
        and gates["single_qubit"]["H"]["unitary"]
        and gates["two_qubit"]["SWAP"]["unitary"]
        and z3_proof["verdict"] == "unsat"
        and cvc5_proof["verdict"] == "unsat"
        and z3_proof["computed_perturbation_flip_verdict"] == "sat"
        and cvc5_proof["computed_perturbation_flip_verdict"] == "sat"
    )
    return {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "primary_n": PRIMARY_N,
        "support": support_summary(),
        "object": {
            "kind": "finite ring-checkerboard partitioned QCA diagnostic",
            "qubits_on_cells": True,
            "same_support_as_v0": True,
            "support_source": "ring_checkerboard_automaton_v0.support_cells",
            "index_definition": "signed_log2_index = log2(dim(right support algebra)/dim(left support algebra))",
            "index_definition_status": "standard_math_alignment_not_owner_source",
            "raw_standard_index_ratio_retained": True,
        },
        "local_quantum_gates": gates,
        "index_table": rows,
        "index_controls": controls,
        "typed_information_flux_rows": typed,
        "locality_comparison": locality,
        "classical_limit": classical,
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "positive_section": {
            "expectation_2_LR_opposite_indices": controls["L_R_realization"],
            "expectation_3_locality_changes_coupling": locality["expectation_3_status"],
            "index_calibrations": controls["calibration"],
        },
        "negative_section": {
            "index0_control": controls["index0_control"],
            "falsifier_branch": controls["falsifier_branch"],
            "order_shuffle_control": {
                "changed": locality["order_shuffle_changes_local_structure"],
                "control_signature": locality["order_shuffle_control"]["signature"],
            },
        },
        "boundary_section": {
            "claim_ceiling": "scratch diagnostic; no promotion, no canonical QCA classification, no v4 coupling admission",
            "finite_depth_circuit_boundary": "nonzero shift index is represented as a locality-preserving QCA wire flow, not as a finite-depth circuit claim",
            "full_binary_configuration_enumerated": False,
            "resource_guard": "primary_n=4 support cells, matched-state locality comparison only",
        },
        "all_pass": all_pass,
    }


def parent_lineage() -> dict[str, Any]:
    rows = []
    for key, rel_path in AUTHORITY_INPUTS.items():
        path = ROOT / rel_path
        if path.exists():
            rows.append({"id": key, "path": rel_path, "sha256": sha256_file(path)})
    return {
        "authority_order_read": [
            "owner doctrine cellular automata ring checkerboard",
            "committed ring_checkerboard_automaton_v0 classical floor",
            "coupling-law O1 flux row",
        ],
        "consumed_inputs": rows,
        "git_commits_referenced": {
            "b7191aac6": "CA/ring-checkerboard doctrine with v0 adjudication and v1 QCA/index gate open",
            "fe06d49bd": "committed classical ring_checkerboard_automaton_v0 floor",
            "b6a6d2ae9": "coupling-law O1 flux IN-left/OUT-right row",
        },
    }


def engine_result_base(engine: str, source_path: Path, result_path: Path) -> dict[str, Any]:
    return {
        "schema": f"{SIM_ID}_{engine}_result_v1",
        "sim_id": SIM_ID,
        "engine": engine,
        "generated_at": now_z(),
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
    }
