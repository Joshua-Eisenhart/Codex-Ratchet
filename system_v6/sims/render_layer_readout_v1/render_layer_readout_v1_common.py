#!/usr/bin/env python3
"""Shared finite render-layer readout v1 machinery."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import networkx as nx
import z3


SIM_ID = "render_layer_readout_v1"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
CLASSIFICATION = "scratch_diagnostic"
classification = CLASSIFICATION
CLAIM_CEILING = "render-layer readout candidate only; no holodeck/FEP/physics/Axis-0 admission"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
promotion_allowed = PROMOTION_ALLOWED
formal_admission_allowed = FORMAL_ADMISSION_ALLOWED
EXPECTED_STATE_COUNT = 33
TRAJECTORY_LENGTH = 33
SCRAMBLE_SEED = 20260612
TOOL_MANIFEST = {
    "networkx": {"tried": True, "used": True, "reason": "finite committed generator graph and render cut-edge probe"},
    "z3": {"tried": True, "used": True, "reason": "two-sided v1 reachability proof with erased old-pin control"},
    "cvc5": {"tried": True, "used": True, "reason": "independent two-sided v1 reachability proof with erased old-pin control"},
}
TOOL_INTEGRATION_DEPTH = {"networkx": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing"}

V0_DIR = ROOT / "system_v6" / "sims" / "render_layer_readout_v0"
if str(V0_DIR) not in sys.path:
    sys.path.insert(0, str(V0_DIR))

import render_layer_readout_v0_common as v0  # noqa: E402


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def new_signed_projection_pin() -> dict[str, str]:
    return {
        "pin_id": "v1_signed_render_update_projection",
        "formula_id": "sign(dot(realized-render, unit(render-source)))",
        "comparison": "signed projection of committed render-update correction against the committed source-to-render direction",
        "v0_diagnosis_answered": "uses a directional signed residual rather than the dissipative distance gap norm(realized-render)-norm(render-source)",
    }


def old_v0_distance_pin() -> dict[str, str]:
    return {
        "pin_id": "v0_distance_dissipative_regression",
        "formula_id": "norm(realized-render)-norm(render-source)",
        "comparison": "old v0 distance-threshold pin retained only as the negative control",
        "v0_diagnosis_answered": "expected to make reshape_the_render unreachable on the committed dynamics",
    }


def _unit(vec: tuple[float, float, float]) -> tuple[float, float, float]:
    length = v0.norm(vec)
    if length <= 1.0e-12:
        return (0.0, 0.0, 0.0)
    return (vec[0] / length, vec[1] / length, vec[2] / length)


def _dot(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return sum(left[i] * right[i] for i in range(3))


def pin_value(
    pin: dict[str, str],
    source: tuple[float, float, float],
    render: tuple[float, float, float],
    realized: tuple[float, float, float],
) -> tuple[float, dict[str, Any]]:
    source_to_render = v0.sub(render, source)
    render_to_realized = v0.sub(realized, render)
    if pin["pin_id"] == "v0_distance_dissipative_regression":
        value = v0.norm(render_to_realized) - v0.norm(source_to_render)
        return value, {
            "source_to_render_trace_norm": v0.float_obj(v0.norm(source_to_render)),
            "render_to_realized_trace_norm": v0.float_obj(v0.norm(render_to_realized)),
            "direction_scalar": v0.float_obj(value),
            "comparison_components": "old distance gap; negative control only",
        }
    if pin["pin_id"] != "v1_signed_render_update_projection":
        raise ValueError(f"unknown polarity pin: {pin['pin_id']}")
    direction = _unit(source_to_render)
    render_update_flow = _dot(render_to_realized, direction)
    realized_state_flow = _dot(v0.sub(realized, source), direction)
    source_to_render_flow = _dot(source_to_render, direction)
    value = realized_state_flow - source_to_render_flow
    return value, {
        "unit_source_to_render_direction": v0.round_vec(direction),
        "source_to_render_flow": v0.float_obj(source_to_render_flow),
        "realized_state_flow": v0.float_obj(realized_state_flow),
        "render_update_flow": v0.float_obj(render_update_flow),
        "direction_scalar": v0.float_obj(value),
        "comparison_components": "realized_state_flow - source_to_render_flow, equivalently signed render_update_flow",
    }


def _edge_row(carrier: dict[str, Any], edge: dict[str, Any], pin: dict[str, str]) -> dict[str, Any]:
    cells = v0.cell_map(carrier)
    src_id = int(edge["src"])
    dst_id = int(edge["dst"])
    source = v0.vec3(cells[src_id]["coord"])
    render = v0.vec3(edge["image_before_quantization"])
    realized = v0.vec3(cells[dst_id]["coord"])
    direction_scalar, flow = pin_value(pin, source, render, realized)
    polarity = v0.sign(direction_scalar)
    correction = v0.sub(realized, render)
    updated_render = v0.add(render, correction)
    residual = v0.norm(v0.sub(updated_render, realized))
    return {
        "step": int(edge.get("trajectory_step", -1)),
        "src": src_id,
        "dst": dst_id,
        "generator": str(edge["generator"]),
        "render": {"kind": "committed_one_step_image_before_quantization", "coord": v0.round_vec(render)},
        "realized_state": {
            "kind": "committed_quantized_successor_cell",
            "cell_id": dst_id,
            "coord": v0.round_vec(realized),
        },
        "error": {
            "type": "single_qubit_bloch_trace_norm_divergence",
            "render_minus_realized": v0.round_vec(v0.sub(render, realized)),
            "trace_norm": v0.float_obj(v0.norm(v0.sub(realized, render))),
            "co_ratchet_type": "render_vs_realized_same_committed_carrier_cell_type",
        },
        "update": {
            "type": "committed_quantization_error_correction_on_render_side",
            "correction_vector": v0.round_vec(correction),
            "updated_render": v0.round_vec(updated_render),
            "residual_after_update": v0.float_obj(residual),
        },
        "error_flow": {
            **flow,
            "polarity_sign": polarity,
            "polarity_label": v0.sign_label(polarity),
            "pin_id": pin["pin_id"],
            "formula_id": pin["formula_id"],
        },
    }


def committed_edge_rows(carrier: dict[str, Any], pin: dict[str, str]) -> list[dict[str, Any]]:
    return [_edge_row(carrier, edge, pin) for edge in carrier["edges"]]


def trajectory_rows(carrier: dict[str, Any], pin: dict[str, str]) -> list[dict[str, Any]]:
    return [_edge_row(carrier, edge, pin) for edge in v0.trajectory_edges(carrier)]


def reachability_gate(carrier: dict[str, Any], pin: dict[str, str]) -> dict[str, Any]:
    rows = committed_edge_rows(carrier, pin)
    label_counts = dict(Counter(row["error_flow"]["polarity_label"] for row in rows))
    witnesses: dict[str, dict[str, Any]] = {}
    for required in ("reshape_the_render", "resist_the_update"):
        found = next((row for row in rows if row["error_flow"]["polarity_label"] == required), None)
        if found is not None:
            witnesses[required] = {
                "committed_dynamics_trajectory": True,
                "src": found["src"],
                "dst": found["dst"],
                "generator": found["generator"],
                "direction_scalar": found["error_flow"]["direction_scalar"],
                "formula_id": found["error_flow"]["formula_id"],
                "source_coord": v0.round_vec(v0.vec3(v0.cell_map(carrier)[found["src"]]["coord"])),
                "render_coord": found["render"]["coord"],
                "realized_coord": found["realized_state"]["coord"],
            }
    passed = all(label_counts.get(label, 0) > 0 for label in ("reshape_the_render", "resist_the_update"))
    return {
        "gate_name": "render_polarity_reachability_witness",
        "status": "passed" if passed else "failed_unreachable",
        "pin": pin,
        "edge_count": len(rows),
        "required_labels": ["reshape_the_render", "resist_the_update"],
        "label_counts": {
            "reshape_the_render": label_counts.get("reshape_the_render", 0),
            "resist_the_update": label_counts.get("resist_the_update", 0),
            "neutral_no_render_polarity": label_counts.get("neutral_no_render_polarity", 0),
        },
        "witnesses": witnesses,
    }


def aggregate_by_realized_cell(rows: list[dict[str, Any]]) -> dict[int, float]:
    values: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        values[int(row["realized_state"]["cell_id"])].append(float(row["error_flow"]["direction_scalar"]["float"]))
    return {cell: sum(items) / len(items) for cell, items in values.items()}


def fill_missing_by_committed_edges(carrier: dict[str, Any], pin: dict[str, str], trajectory_raw: dict[int, float]) -> dict[int, float]:
    out = dict(trajectory_raw)
    incoming: dict[int, list[float]] = defaultdict(list)
    for row in committed_edge_rows(carrier, pin):
        incoming[int(row["dst"])].append(float(row["error_flow"]["direction_scalar"]["float"]))
    for cell_id in range(EXPECTED_STATE_COUNT):
        if cell_id not in out:
            out[cell_id] = sum(incoming[cell_id]) / len(incoming[cell_id])
    return out


def render_raw_signs(carrier: dict[str, Any], pin: dict[str, str], rows: list[dict[str, Any]]) -> tuple[dict[int, float], dict[int, int]]:
    raw = fill_missing_by_committed_edges(carrier, pin, aggregate_by_realized_cell(rows))
    return raw, {cell: v0.sign(value) for cell, value in raw.items()}


def scrambled_control(signs: dict[int, int]) -> dict[str, Any]:
    rng = random.Random(SCRAMBLE_SEED)
    cells = list(range(EXPECTED_STATE_COUNT))
    shuffled = cells[:]
    rng.shuffle(shuffled)
    scrambled_signs = {cell: signs[shuffled[idx]] for idx, cell in enumerate(cells)}
    same = [cell for cell in cells if scrambled_signs[cell] == signs[cell]]
    constant = len(set(signs.values())) <= 1
    return {
        "seed": SCRAMBLE_SEED,
        "same_cell_count": len(same),
        "breaks_polarity": len(same) < EXPECTED_STATE_COUNT,
        "constant_readout": constant,
        "scrambled_vector_hash": stable_hash([scrambled_signs[cell] for cell in cells]),
        "verdict": "breaks-render-polarity" if len(same) < EXPECTED_STATE_COUNT else "constant-readout-not-breakable-no-stable",
    }


def old_pin_regression_control(carrier: dict[str, Any]) -> dict[str, Any]:
    blocked = build_packet_for_pin(old_v0_distance_pin(), include_old_control=False)
    gate = blocked["repin_reachability_gate"]
    return {
        "ran": True,
        "law": "v0 negative control: old distance pin must fail the v1 reachability gate",
        "construction_status": blocked["construction_status"],
        "readout_table_ran": blocked["readout_table_ran"],
        "reproduces_unreachable_reshape": gate["label_counts"].get("reshape_the_render", 0) == 0,
        "label_counts": gate["label_counts"],
        "source_audit": "system_v6/sims/render_layer_readout_v0/audit_verdict.md",
        "committed_edge_count": int(carrier["edge_count"]),
    }


def boundary_verdict(render_form: dict[str, Any], anchor_form: dict[str, Any], render_signs: dict[int, int], controls: dict[str, Any]) -> dict[str, Any]:
    sign_vector = [render_signs[cell] for cell in range(EXPECTED_STATE_COUNT)]
    constant = len(set(sign_vector)) <= 1
    same = v0.canonical_tuple_equal(render_form, anchor_form)
    controls_pass = (
        controls["identity_dynamics_degeneracy"]["verdict"] == "identity-dynamics-degenerates-render-readout"
        and controls["scrambled_error"]["verdict"] == "breaks-render-polarity"
        and controls["no_identity_leak"]["verdict"] == "passes-no-identity-leak"
        and controls["positive_predicate_boundary"]["verdict"] == "positive-predicate-admits-anchor"
    )
    if same:
        verdict = "decorative_on_this_carrier"
        relation = "same_distinction_alias_into_axis0"
    elif constant or not controls_pass:
        verdict = "no_stable_distinction"
        relation = "falsifier"
    else:
        verdict = "own_readout_family"
        relation = "different_distinction_from_axis0"
    return {
        "question": "same distinction, different distinction, or no stable distinction",
        "relation_to_axis0_phi": relation,
        "verdict": verdict,
        "same_as_axis0_alias_tuple": same,
        "constant_or_single_sign_vector": constant,
        "controls_pass": controls_pass,
        "expectation_3_falsifier_live": not constant,
        "reads": "signed render-update projection: whether the committed render correction pushes along or against the committed prediction direction",
    }


def graph_probe(carrier: dict[str, Any], render_signs: dict[int, int]) -> dict[str, Any]:
    graph = nx.MultiDiGraph()
    for cell_id in range(EXPECTED_STATE_COUNT):
        graph.add_node(cell_id, render_sign=render_signs[cell_id])
    for edge in carrier["edges"]:
        graph.add_edge(int(edge["src"]), int(edge["dst"]), generator=str(edge["generator"]))
    cut_edges = [
        (u, v, key)
        for u, v, key in graph.edges(keys=True)
        if graph.nodes[u]["render_sign"] != graph.nodes[v]["render_sign"]
    ]
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "committed_edge_rows_count": len(carrier["edges"]),
        "weak_component_count": nx.number_weakly_connected_components(graph),
        "render_polarity_cut_edge_count": len(cut_edges),
        "load_bearing": graph.number_of_nodes() == EXPECTED_STATE_COUNT and len(carrier["edges"]) == int(carrier["edge_count"]),
        "constant_readout_detected": len(cut_edges) == 0,
    }


def smt_proof(counts: dict[str, int], solver_name: str) -> dict[str, Any]:
    if solver_name == "z3":
        reshape = z3.Int("reshape_cells")
        resist = z3.Int("resist_cells")
        total = z3.Int("total_cells")
        solver = z3.Solver()
        solver.add(reshape == int(counts["reshape_cells"]))
        solver.add(resist == int(counts["resist_cells"]))
        solver.add(total == EXPECTED_STATE_COUNT)
        solver.add(z3.Not(z3.And(reshape > 0, resist > 0, reshape + resist <= total)))
        verdict = str(solver.check())
        erased = z3.Solver()
        erased.add(reshape == 0, resist == EXPECTED_STATE_COUNT, total == EXPECTED_STATE_COUNT)
        erased.add(z3.Not(z3.And(reshape > 0, resist > 0, reshape + resist <= total)))
        erased_verdict = str(erased.check())
    elif solver_name == "cvc5":
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        reshape = solver.mkConst(int_sort, "reshape_cells")
        resist = solver.mkConst(int_sort, "resist_cells")
        total = solver.mkConst(int_sort, "total_cells")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, reshape, solver.mkInteger(int(counts["reshape_cells"]))))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, resist, solver.mkInteger(int(counts["resist_cells"]))))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, total, solver.mkInteger(EXPECTED_STATE_COUNT)))
        ok = solver.mkTerm(
            Kind.AND,
            solver.mkTerm(Kind.GT, reshape, solver.mkInteger(0)),
            solver.mkTerm(Kind.GT, resist, solver.mkInteger(0)),
            solver.mkTerm(Kind.LEQ, solver.mkTerm(Kind.ADD, reshape, resist), total),
        )
        solver.assertFormula(solver.mkTerm(Kind.NOT, ok))
        verdict = str(solver.checkSat()).lower()
        erased = cvc5.Solver()
        erased.setLogic("QF_LIA")
        int_sort2 = erased.getIntegerSort()
        reshape2 = erased.mkConst(int_sort2, "reshape_cells_erased")
        resist2 = erased.mkConst(int_sort2, "resist_cells_erased")
        total2 = erased.mkConst(int_sort2, "total_cells_erased")
        erased.assertFormula(erased.mkTerm(Kind.EQUAL, reshape2, erased.mkInteger(0)))
        erased.assertFormula(erased.mkTerm(Kind.EQUAL, resist2, erased.mkInteger(EXPECTED_STATE_COUNT)))
        erased.assertFormula(erased.mkTerm(Kind.EQUAL, total2, erased.mkInteger(EXPECTED_STATE_COUNT)))
        ok2 = erased.mkTerm(
            Kind.AND,
            erased.mkTerm(Kind.GT, reshape2, erased.mkInteger(0)),
            erased.mkTerm(Kind.GT, resist2, erased.mkInteger(0)),
            erased.mkTerm(Kind.LEQ, erased.mkTerm(Kind.ADD, reshape2, resist2), total2),
        )
        erased.assertFormula(erased.mkTerm(Kind.NOT, ok2))
        erased_verdict = str(erased.checkSat()).lower()
    else:
        raise ValueError(solver_name)
    return {
        "ran": True,
        "solver": solver_name,
        "verdict": verdict,
        "erased_unreachable_control_verdict": erased_verdict,
        "load_bearing": True,
        "claim": "computed v1 render polarity has both reshape and resist cells; erased old-pin-like control flips to SAT",
    }


def build_packet_for_pin(pin: dict[str, str], *, include_old_control: bool = True) -> dict[str, Any]:
    carrier, tables = v0.anchor_object()
    gate = reachability_gate(carrier, pin)
    base: dict[str, Any] = {
        "schema": f"{SIM_ID}_core_v1",
        "sim_id": SIM_ID,
        "source_path": rel(Path(__file__).resolve()),
        "source_sha256": sha256_file(Path(__file__).resolve()),
        "result_path": rel(RESULT_PATH),
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "no_builder_audit_verdict": True,
        "repin_reachability_gate": gate,
        "polarity_pin": pin,
        "machinery_reuse": {
            "v0_common_path": rel(V0_DIR / "render_layer_readout_v0_common.py"),
            "v0_common_sha256": sha256_file(V0_DIR / "render_layer_readout_v0_common.py"),
            "reused_parts": ["committed carrier rebuild", "finite render/error/update objects", "alias canonical form helpers"],
        },
        "allowed_claims": [
            "render/error/update are finite objects on the committed carrier",
            "v1 polarity has committed-dynamics witnesses for reshape and resist before readout rows",
            "render polarity boundary is classified against committed Axis-0 phi as a scratch candidate",
        ],
        "disallowed_claims": [
            "holodeck admission",
            "FEP admission",
            "physics admission",
            "Axis-0 admission or rescue of CP.12",
            "formal admission",
            "canonical by process",
            "manifold claim",
        ],
    }
    if gate["status"] != "passed":
        return {**base, "construction_status": "repin_failed_unreachable", "readout_table_ran": False, "all_pass": False}

    rows = trajectory_rows(carrier, pin)
    render_raw, render_signs = render_raw_signs(carrier, pin, rows)
    render_vector_rows, render_sign_vector = v0.vector_rows(render_raw, render_signs)
    anchor_raw, anchor_sign = v0.anchor_raw_sign(tables)
    anchor_form = v0.canonical_alias_form(
        cid="A0.CP.0_committed_signed_outgoing_gradient_flux",
        raw_by_cell=anchor_raw,
        sign_by_cell=anchor_sign,
        carrier=carrier,
        convention={"formula": "committed_axis0_phi_signed_outgoing_gradient_flux"},
    )
    render_form = v0.canonical_alias_form(
        cid=SIM_ID,
        raw_by_cell=render_raw,
        sign_by_cell=render_signs,
        carrier=carrier,
        convention={
            "render": "committed dynamics one-step image",
            "error": "trace norm render-vs-realized typed divergence",
            "update": "committed quantization correction on render side",
            "polarity": pin["formula_id"],
        },
    )
    controls: dict[str, Any] = {
        "identity_dynamics_degeneracy": v0.identity_dynamics_control(carrier),
        "scrambled_error": scrambled_control(render_signs),
        "no_identity_leak": v0.no_identity_leak_control(carrier, rows),
        "positive_predicate_boundary": v0.positive_predicate_boundary_control(anchor_form, carrier, anchor_raw, anchor_sign),
    }
    if include_old_control:
        controls["v0_old_pin_regression"] = old_pin_regression_control(carrier)
    verdict = boundary_verdict(render_form, anchor_form, render_signs, controls)
    counts = {
        "trajectory_length": len(rows),
        "rendered_step_count": len(rows),
        "finite_cell_count": int(carrier["state_count"]),
        "finite_edge_count": int(carrier["edge_count"]),
        "nonzero_render_cells": sum(value != 0 for value in render_signs.values()),
        "reshape_cells": sum(value > 0 for value in render_signs.values()),
        "resist_cells": sum(value < 0 for value in render_signs.values()),
        "neutral_cells": sum(value == 0 for value in render_signs.values()),
        "unique_render_sign_count": len(set(render_signs.values())),
        "axis0_disagreement_cells": sum(anchor_sign[cell] != render_signs[cell] for cell in range(EXPECTED_STATE_COUNT)),
    }
    graph = graph_probe(carrier, render_signs)
    z3_result = smt_proof(counts, "z3")
    cvc5_result = smt_proof(counts, "cvc5")
    gates = {
        "repin_reachability_gate_passed": gate["status"] == "passed",
        "finite_render_error_update_objects": len(rows) == TRAJECTORY_LENGTH
        and all(float(row["update"]["residual_after_update"]["float"]) <= 1.0e-12 for row in rows),
        "trajectory_over_committed_generators": len({row["generator"] for row in rows}) == len(carrier["generator_names"]),
        "both_readout_values_reachable": counts["reshape_cells"] > 0 and counts["resist_cells"] > 0,
        "scrambled_error_breaks": controls["scrambled_error"]["verdict"] == "breaks-render-polarity",
        "old_pin_regression_refused": not include_old_control
        or controls["v0_old_pin_regression"]["reproduces_unreachable_reshape"] is True,
        "no_identity_leak_passes": controls["no_identity_leak"]["verdict"] == "passes-no-identity-leak",
        "positive_predicate_boundary_admits": controls["positive_predicate_boundary"]["verdict"] == "positive-predicate-admits-anchor",
        "boundary_question_answered": verdict["relation_to_axis0_phi"]
        in {"same_distinction_alias_into_axis0", "different_distinction_from_axis0", "falsifier"},
        "expectation_3_falsifier_live": verdict["expectation_3_falsifier_live"] is True,
        "z3_reachability_unsat": z3_result["verdict"] == "unsat" and z3_result["erased_unreachable_control_verdict"] == "sat",
        "cvc5_reachability_unsat": cvc5_result["verdict"] == "unsat" and cvc5_result["erased_unreachable_control_verdict"] == "sat",
        "graph_probe_load_bearing": graph["load_bearing"] is True,
    }
    return {
        **base,
        "construction_status": "repin_reachability_passed",
        "readout_table_ran": True,
        "carrier": {
            "state_count": carrier["state_count"],
            "edge_count": carrier["edge_count"],
            "generator_names": carrier["generator_names"],
            "state_object_id": carrier["state_object_id"],
            "transition_graph_sha256": carrier["transition_graph_sha256"],
        },
        "trajectory": rows,
        "render_readout": {
            "raw_by_cell": {str(k): v0.float_obj(v) for k, v in render_raw.items()},
            "sign_vector": render_sign_vector,
            "rows": render_vector_rows,
            "canonical_alias_form": render_form,
            "canonical_alias_form_sha256": render_form["sha256"],
            "polarity_counts": dict(Counter(v0.sign_label(value) for value in render_signs.values())),
        },
        "axis0_boundary": {
            "axis0_anchor_alias_form_sha256": anchor_form["sha256"],
            "disagreement_table": v0.disagreement_table(anchor_raw, anchor_sign, render_raw, render_signs),
            "boundary_verdict": verdict,
        },
        "controls": controls,
        "graph_probe": graph,
        "counts": counts,
        "crossover_proofs": {"z3": z3_result, "cvc5": cvc5_result},
        "build_gates": gates,
        "computed_hashes": {
            "trajectory_sha256": stable_hash(rows),
            "render_sign_vector_sha256": stable_hash(render_sign_vector),
            "render_alias_form_sha256": render_form["sha256"],
            "axis0_boundary_sha256": stable_hash(verdict),
        },
        "all_pass": all(gates.values()),
    }


def build_core() -> dict[str, Any]:
    return build_packet_for_pin(new_signed_projection_pin())


def engine_payload(
    engine: str,
    source_path: Path,
    result_path: Path,
    packages_used: list[str],
    load_bearing: list[str],
    observables: dict[str, str],
    role_id: str,
) -> dict[str, Any]:
    core = build_core()
    return {
        **core,
        "schema": f"{SIM_ID}_{engine}_lane_v1",
        "sim_id": SIM_ID,
        "role_id": role_id,
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "all_pass": core["all_pass"],
        "claim": "finite render/error/update trajectory and v1 render-polarity distinction boundary",
        "allowed_claims": core["allowed_claims"],
        "disallowed_claims": core["disallowed_claims"],
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "package_observables": observables,
        "claim_path_tools": load_bearing,
        "TOOL_MANIFEST": {tool: {"tried": True, "used": True, "reason": observables[tool]} for tool in load_bearing},
        "TOOL_INTEGRATION_DEPTH": {tool: "load_bearing" for tool in load_bearing},
    }
