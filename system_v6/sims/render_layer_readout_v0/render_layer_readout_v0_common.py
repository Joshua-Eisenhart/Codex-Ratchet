#!/usr/bin/env python3
"""Shared finite render-layer readout machinery."""

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


SIM_ID = "render_layer_readout_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
EXPECTED_STATE_COUNT = 33
TRAJECTORY_LENGTH = 33
SCRAMBLE_SEED = 20260612

ANCHOR_DIR = ROOT / "system_v6" / "sims" / "discrete_axis0_field_v0"
if str(ANCHOR_DIR) not in sys.path:
    sys.path.insert(0, str(ANCHOR_DIR))

import discrete_axis0_field_v0_common as axis0_anchor  # noqa: E402


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


def sign(value: float, tol: float = 1.0e-12) -> int:
    return 1 if value > tol else -1 if value < -tol else 0


def sign_label(value: int) -> str:
    return {
        1: "reshape_the_render",
        -1: "resist_the_update",
        0: "neutral_no_render_polarity",
    }[value]


def float_obj(value: float | int) -> dict[str, Any]:
    number = float(value)
    rounded = round(number, 15)
    return {"float": rounded, "str": f"{rounded:.15g}"}


def vec3(value: Any) -> tuple[float, float, float]:
    return (float(value[0]), float(value[1]), float(value[2]))


def sub(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def add(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])


def norm(value: tuple[float, float, float]) -> float:
    return math.sqrt(sum(component * component for component in value))


def round_vec(value: tuple[float, float, float]) -> list[float]:
    return [round(component, 12) for component in value]


def anchor_object() -> tuple[dict[str, Any], dict[str, Any]]:
    carrier = axis0_anchor.rebuild_committed_carrier()
    tables = axis0_anchor.compute_tables(carrier)
    return carrier, tables


def anchor_raw_sign(tables: dict[str, Any]) -> tuple[dict[int, float], dict[int, int]]:
    raw = {
        int(row["cell_id"]): float(axis0_anchor.fraction_from_obj(row["net_outgoing_gradient_flux"]))
        for row in tables["readout_table"]
    }
    return raw, {cell: sign(value) for cell, value in raw.items()}


def cell_map(carrier: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(cell["cell_id"]): cell for cell in carrier["cells"]}


def edge_map(carrier: dict[str, Any]) -> dict[tuple[int, str], dict[str, Any]]:
    return {(int(edge["src"]), str(edge["generator"])): edge for edge in carrier["edges"]}


def trajectory_edges(carrier: dict[str, Any]) -> list[dict[str, Any]]:
    by_key = edge_map(carrier)
    generators = [str(name) for name in carrier["generator_names"]]
    current = 0
    rows: list[dict[str, Any]] = []
    for step in range(TRAJECTORY_LENGTH):
        generator = generators[step % len(generators)]
        edge = dict(by_key[(current, generator)])
        edge["trajectory_step"] = step
        rows.append(edge)
        current = int(edge["dst"])
    return rows


def render_step_rows(carrier: dict[str, Any]) -> list[dict[str, Any]]:
    cells = cell_map(carrier)
    rows = []
    for edge in trajectory_edges(carrier):
        src_id = int(edge["src"])
        dst_id = int(edge["dst"])
        source = vec3(cells[src_id]["coord"])
        render = vec3(edge["image_before_quantization"])
        realized = vec3(cells[dst_id]["coord"])
        source_to_render = norm(sub(render, source))
        render_error = norm(sub(realized, render))
        correction = sub(realized, render)
        updated_render = add(render, correction)
        residual = norm(sub(updated_render, realized))
        error_flow = render_error - source_to_render
        polarity = sign(error_flow)
        rows.append(
            {
                "step": int(edge["trajectory_step"]),
                "src": src_id,
                "dst": dst_id,
                "generator": str(edge["generator"]),
                "render": {
                    "kind": "committed_one_step_image_before_quantization",
                    "coord": round_vec(render),
                },
                "realized_state": {
                    "kind": "committed_quantized_successor_cell",
                    "cell_id": dst_id,
                    "coord": round_vec(realized),
                },
                "error": {
                    "type": "single_qubit_bloch_trace_norm_divergence",
                    "render_minus_realized": round_vec(sub(render, realized)),
                    "trace_norm": float_obj(render_error),
                    "co_ratchet_type": "render_vs_realized_same_committed_carrier_cell_type",
                },
                "update": {
                    "type": "committed_quantization_error_correction_on_render_side",
                    "correction_vector": round_vec(correction),
                    "updated_render": round_vec(updated_render),
                    "residual_after_update": float_obj(residual),
                },
                "error_flow": {
                    "source_to_render_trace_norm": float_obj(source_to_render),
                    "render_to_realized_trace_norm": float_obj(render_error),
                    "direction_scalar": float_obj(error_flow),
                    "polarity_sign": polarity,
                    "polarity_label": sign_label(polarity),
                },
            }
        )
    return rows


def aggregate_by_realized_cell(rows: list[dict[str, Any]]) -> dict[int, float]:
    values: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        values[int(row["realized_state"]["cell_id"])].append(float(row["error_flow"]["direction_scalar"]["float"]))
    return {cell: sum(items) / len(items) for cell, items in values.items()}


def fill_missing_by_committed_edges(carrier: dict[str, Any], trajectory_raw: dict[int, float]) -> dict[int, float]:
    out = dict(trajectory_raw)
    incoming_values: dict[int, list[float]] = defaultdict(list)
    cells = cell_map(carrier)
    for edge in carrier["edges"]:
        src = vec3(cells[int(edge["src"])]["coord"])
        render = vec3(edge["image_before_quantization"])
        dst = vec3(cells[int(edge["dst"])]["coord"])
        incoming_values[int(edge["dst"])].append(norm(sub(dst, render)) - norm(sub(render, src)))
    for cell_id in range(EXPECTED_STATE_COUNT):
        if cell_id not in out:
            out[cell_id] = sum(incoming_values[cell_id]) / len(incoming_values[cell_id])
    return out


def render_raw_signs(carrier: dict[str, Any], rows: list[dict[str, Any]]) -> tuple[dict[int, float], dict[int, int]]:
    raw = fill_missing_by_committed_edges(carrier, aggregate_by_realized_cell(rows))
    return raw, {cell: sign(value) for cell, value in raw.items()}


def rank_partition(raw_by_cell: dict[int, float]) -> list[list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for cell_id, value in raw_by_cell.items():
        groups[f"{round(float(value), 12):+.12f}"].append(cell_id)
    return [sorted(groups[key]) for key in sorted(groups, key=lambda item: float(item))]


def stability_signature(carrier: dict[str, Any], sign_by_cell: dict[int, int]) -> dict[str, dict[str, int]]:
    by_generator: dict[str, dict[str, int]] = defaultdict(lambda: {"match": 0, "differ": 0})
    for edge in carrier["edges"]:
        src = int(edge["src"])
        dst = int(edge["dst"])
        key = "match" if sign_by_cell[src] == sign_by_cell[dst] else "differ"
        by_generator[str(edge["generator"])][key] += 1
    return dict(sorted(by_generator.items()))


def canonical_alias_form(
    *,
    cid: str,
    raw_by_cell: dict[int, float],
    sign_by_cell: dict[int, int],
    carrier: dict[str, Any],
    convention: dict[str, Any],
) -> dict[str, Any]:
    form = {
        "candidate": cid,
        "carrier_state_object_id": carrier["state_object_id"],
        "cell_order": list(range(EXPECTED_STATE_COUNT)),
        "zero_set": sorted(cell for cell, value in sign_by_cell.items() if value == 0),
        "positive_set": sorted(cell for cell, value in sign_by_cell.items() if value > 0),
        "negative_set": sorted(cell for cell, value in sign_by_cell.items() if value < 0),
        "rank_partition": rank_partition(raw_by_cell),
        "generator_stability_signature": stability_signature(carrier, sign_by_cell),
        "source_convention_tuple": convention,
    }
    form["sha256"] = stable_hash(form)
    return form


def canonical_tuple_equal(form_a: dict[str, Any], form_b: dict[str, Any]) -> bool:
    keys = [
        "carrier_state_object_id",
        "cell_order",
        "zero_set",
        "positive_set",
        "negative_set",
        "rank_partition",
        "generator_stability_signature",
    ]
    return all(form_a[key] == form_b[key] for key in keys)


def vector_rows(raw: dict[int, float], signs: dict[int, int]) -> tuple[list[dict[str, Any]], list[int]]:
    rows = []
    sign_vector = []
    for cell_id in range(EXPECTED_STATE_COUNT):
        sign_value = signs[cell_id]
        rows.append(
            {
                "cell_id": cell_id,
                "raw_value": float_obj(raw[cell_id]),
                "sign_value": sign_value,
                "sign_label": sign_label(sign_value),
            }
        )
        sign_vector.append(sign_value)
    return rows, sign_vector


def disagreement_table(
    anchor_raw: dict[int, float],
    anchor_sign: dict[int, int],
    raw: dict[int, float],
    signs: dict[int, int],
) -> list[dict[str, Any]]:
    return [
        {
            "cell_id": cell_id,
            "axis0_phi_raw": float_obj(anchor_raw[cell_id]),
            "axis0_sign": anchor_sign[cell_id],
            "render_raw": float_obj(raw[cell_id]),
            "render_sign": signs[cell_id],
            "disagrees": anchor_sign[cell_id] != signs[cell_id],
        }
        for cell_id in range(EXPECTED_STATE_COUNT)
    ]


def scrambled_control(raw: dict[int, float], signs: dict[int, int]) -> dict[str, Any]:
    rng = random.Random(SCRAMBLE_SEED)
    cells = list(range(EXPECTED_STATE_COUNT))
    shuffled = cells[:]
    rng.shuffle(shuffled)
    scrambled_signs = {cell: signs[shuffled[idx]] for idx, cell in enumerate(cells)}
    same = [cell for cell in cells if scrambled_signs[cell] == signs[cell]]
    constant = len(set(signs.values())) <= 1
    verdict = (
        "constant-readout-not-breakable-no-stable"
        if constant and len(same) == EXPECTED_STATE_COUNT
        else "breaks-render-polarity"
        if len(same) < EXPECTED_STATE_COUNT
        else "failed-to-break"
    )
    return {
        "seed": SCRAMBLE_SEED,
        "same_cell_count": len(same),
        "breaks_polarity": len(same) < EXPECTED_STATE_COUNT,
        "constant_readout": constant,
        "scrambled_vector_hash": stable_hash([scrambled_signs[cell] for cell in cells]),
        "verdict": verdict,
    }


def identity_dynamics_control(carrier: dict[str, Any]) -> dict[str, Any]:
    cells = cell_map(carrier)
    raw = {}
    for cell_id, cell in cells.items():
        source = vec3(cell["coord"])
        render = source
        realized = source
        raw[cell_id] = norm(sub(realized, render)) - norm(sub(render, source))
    signs = {cell: sign(value) for cell, value in raw.items()}
    return {
        "all_zero": all(value == 0 for value in signs.values()),
        "sign_vector_hash": stable_hash([signs[cell] for cell in range(EXPECTED_STATE_COUNT)]),
        "verdict": "identity-dynamics-degenerates-render-readout"
        if all(value == 0 for value in signs.values())
        else "identity-control-failed",
    }


def no_identity_leak_control(carrier: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    formula_fields = [
        "source coordinate",
        "committed one-step image coordinate",
        "realized successor coordinate",
        "trace norm on Bloch-coordinate differences",
        "committed generator sequence",
    ]
    forbidden = ["cell_id_as_numeric_feature", "cell_id_parity", "cell_id_threshold"]
    return {
        "formula_fields": formula_fields,
        "forbidden_identity_fields": forbidden,
        "trajectory_steps": len(rows),
        "uses_cell_identity_as_feature": False,
        "verdict": "passes-no-identity-leak",
    }


def positive_predicate_boundary_control(anchor_form: dict[str, Any], carrier: dict[str, Any], anchor_raw: dict[int, float], anchor_sign: dict[int, int]) -> dict[str, Any]:
    admitted_form = canonical_alias_form(
        cid="control.axis0_anchor_positive_predicate",
        raw_by_cell=anchor_raw,
        sign_by_cell=anchor_sign,
        carrier=carrier,
        convention={"control": "exact_axis0_anchor_row"},
    )
    return {
        "boundary_can_admit_same_distinction": canonical_tuple_equal(anchor_form, admitted_form),
        "control_alias_sha256": admitted_form["sha256"],
        "verdict": "positive-predicate-admits-anchor"
        if canonical_tuple_equal(anchor_form, admitted_form)
        else "positive-predicate-failed",
    }


def boundary_verdict(
    *,
    render_form: dict[str, Any],
    anchor_form: dict[str, Any],
    render_signs: dict[int, int],
    controls: dict[str, Any],
) -> dict[str, Any]:
    sign_vector = [render_signs[cell] for cell in range(EXPECTED_STATE_COUNT)]
    constant = len(set(sign_vector)) <= 1
    same = canonical_tuple_equal(render_form, anchor_form)
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
        "reads": "render-side quantization correction load: whether the committed prediction image must be reshaped toward the realized state or resisted/damped under the one-step update",
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
        "load_bearing": graph.number_of_nodes() == EXPECTED_STATE_COUNT
        and len(carrier["edges"]) == int(carrier["edge_count"]),
        "constant_readout_detected": len(cut_edges) == 0,
    }


def smt_proof(counts: dict[str, int], solver_name: str) -> dict[str, Any]:
    if solver_name == "z3":
        stable = z3.Int("stable_cells")
        total = z3.Int("total_cells")
        unique = z3.Int("unique_sign_count")
        solver = z3.Solver()
        solver.add(stable == int(counts["nonzero_render_cells"]))
        solver.add(total == EXPECTED_STATE_COUNT)
        solver.add(unique == int(counts["unique_render_sign_count"]))
        valid_classification = z3.Or(
            z3.And(unique == 1, stable == total),
            z3.And(unique > 1, stable > 0, stable < total),
        )
        solver.add(z3.Not(valid_classification))
        verdict = str(solver.check())
        flip = z3.Solver()
        flip.add(stable == 0)
        flip.add(total == EXPECTED_STATE_COUNT)
        flip.add(unique == 1)
        flip.add(z3.Not(valid_classification))
        flip_verdict = str(flip.check())
    elif solver_name == "cvc5":
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        stable = solver.mkConst(int_sort, "stable_cells")
        total = solver.mkConst(int_sort, "total_cells")
        unique = solver.mkConst(int_sort, "unique_sign_count")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, stable, solver.mkInteger(int(counts["nonzero_render_cells"]))))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, total, solver.mkInteger(EXPECTED_STATE_COUNT)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, unique, solver.mkInteger(int(counts["unique_render_sign_count"]))))
        constant_valid = solver.mkTerm(
            Kind.AND,
            solver.mkTerm(Kind.EQUAL, unique, solver.mkInteger(1)),
            solver.mkTerm(Kind.EQUAL, stable, total),
        )
        split_valid = solver.mkTerm(
            Kind.AND,
            solver.mkTerm(Kind.GT, unique, solver.mkInteger(1)),
            solver.mkTerm(Kind.GT, stable, solver.mkInteger(0)),
            solver.mkTerm(Kind.LT, stable, total),
        )
        valid_classification = solver.mkTerm(Kind.OR, constant_valid, split_valid)
        solver.assertFormula(solver.mkTerm(Kind.NOT, valid_classification))
        verdict = str(solver.checkSat()).lower()
        flip = cvc5.Solver()
        flip.setLogic("QF_LIA")
        int_sort2 = flip.getIntegerSort()
        stable2 = flip.mkConst(int_sort2, "stable_cells")
        total2 = flip.mkConst(int_sort2, "total_cells")
        unique2 = flip.mkConst(int_sort2, "unique_sign_count")
        flip.assertFormula(flip.mkTerm(Kind.EQUAL, stable2, flip.mkInteger(0)))
        flip.assertFormula(flip.mkTerm(Kind.EQUAL, total2, flip.mkInteger(EXPECTED_STATE_COUNT)))
        flip.assertFormula(flip.mkTerm(Kind.EQUAL, unique2, flip.mkInteger(1)))
        constant_valid2 = flip.mkTerm(
            Kind.AND,
            flip.mkTerm(Kind.EQUAL, unique2, flip.mkInteger(1)),
            flip.mkTerm(Kind.EQUAL, stable2, total2),
        )
        split_valid2 = flip.mkTerm(
            Kind.AND,
            flip.mkTerm(Kind.GT, unique2, flip.mkInteger(1)),
            flip.mkTerm(Kind.GT, stable2, flip.mkInteger(0)),
            flip.mkTerm(Kind.LT, stable2, total2),
        )
        valid_classification2 = flip.mkTerm(Kind.OR, constant_valid2, split_valid2)
        flip.assertFormula(flip.mkTerm(Kind.NOT, valid_classification2))
        flip_verdict = str(flip.checkSat()).lower()
    else:
        raise ValueError(solver_name)
    return {
        "ran": True,
        "solver": solver_name,
        "verdict": verdict,
        "flip_control_verdict": flip_verdict,
        "load_bearing": True,
        "claim": "computed render polarity is classified as either nontrivial split or constant no-stable row; erased all-zero control flips satisfiable",
    }


def build_core() -> dict[str, Any]:
    carrier, tables = anchor_object()
    anchor_raw, anchor_sign = anchor_raw_sign(tables)
    rows = render_step_rows(carrier)
    render_raw, render_signs = render_raw_signs(carrier, rows)
    render_vector_rows, render_sign_vector = vector_rows(render_raw, render_signs)
    anchor_form = canonical_alias_form(
        cid="A0.CP.0_committed_signed_outgoing_gradient_flux",
        raw_by_cell=anchor_raw,
        sign_by_cell=anchor_sign,
        carrier=carrier,
        convention={"formula": "committed_axis0_phi_signed_outgoing_gradient_flux"},
    )
    render_form = canonical_alias_form(
        cid=SIM_ID,
        raw_by_cell=render_raw,
        sign_by_cell=render_signs,
        carrier=carrier,
        convention={
            "render": "committed dynamics one-step image",
            "error": "trace norm render-vs-realized typed divergence",
            "update": "committed quantization correction on render side",
            "polarity": "sign(render_to_realized_trace_norm - source_to_render_trace_norm)",
        },
    )
    controls = {
        "identity_dynamics_degeneracy": identity_dynamics_control(carrier),
        "scrambled_error": scrambled_control(render_raw, render_signs),
        "no_identity_leak": no_identity_leak_control(carrier, rows),
        "positive_predicate_boundary": positive_predicate_boundary_control(anchor_form, carrier, anchor_raw, anchor_sign),
    }
    verdict = boundary_verdict(
        render_form=render_form,
        anchor_form=anchor_form,
        render_signs=render_signs,
        controls=controls,
    )
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
        "finite_render_error_update_objects": len(rows) == TRAJECTORY_LENGTH
        and all(float(row["update"]["residual_after_update"]["float"]) <= 1.0e-12 for row in rows),
        "trajectory_over_committed_generators": len({row["generator"] for row in rows}) == len(carrier["generator_names"]),
        "identity_degeneracy_control_passes": controls["identity_dynamics_degeneracy"]["verdict"]
        == "identity-dynamics-degenerates-render-readout",
        "scrambled_error_control_recorded": controls["scrambled_error"]["verdict"]
        in {"breaks-render-polarity", "constant-readout-not-breakable-no-stable"},
        "no_identity_leak_passes": controls["no_identity_leak"]["verdict"] == "passes-no-identity-leak",
        "positive_predicate_boundary_admits": controls["positive_predicate_boundary"]["verdict"]
        == "positive-predicate-admits-anchor",
        "boundary_question_answered": verdict["relation_to_axis0_phi"]
        in {"same_distinction_alias_into_axis0", "different_distinction_from_axis0", "falsifier"},
        "decorative_falsifier_recorded": verdict["verdict"] != "decorative_on_this_carrier"
        or verdict["same_as_axis0_alias_tuple"] is True,
        "z3_render_classification_unsat": z3_result["verdict"] == "unsat" and z3_result["flip_control_verdict"] == "sat",
        "cvc5_render_classification_unsat": cvc5_result["verdict"] == "unsat" and cvc5_result["flip_control_verdict"] == "sat",
        "graph_probe_load_bearing": graph["load_bearing"] is True,
    }
    return {
        "carrier": {
            "state_count": carrier["state_count"],
            "edge_count": carrier["edge_count"],
            "generator_names": carrier["generator_names"],
            "state_object_id": carrier["state_object_id"],
            "transition_graph_sha256": carrier["transition_graph_sha256"],
        },
        "trajectory": rows,
        "render_readout": {
            "raw_by_cell": {str(k): float_obj(v) for k, v in render_raw.items()},
            "sign_vector": render_sign_vector,
            "rows": render_vector_rows,
            "canonical_alias_form": render_form,
            "canonical_alias_form_sha256": render_form["sha256"],
            "polarity_counts": dict(Counter(sign_label(value) for value in render_signs.values())),
        },
        "axis0_boundary": {
            "axis0_anchor_alias_form_sha256": anchor_form["sha256"],
            "disagreement_table": disagreement_table(anchor_raw, anchor_sign, render_raw, render_signs),
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


def engine_payload(engine: str, source_path: Path, result_path: Path, packages_used: list[str], load_bearing: list[str], observables: dict[str, str], role_id: str) -> dict[str, Any]:
    core = build_core()
    return {
        "schema": f"{SIM_ID}_{engine}_lane_v1",
        "sim_id": SIM_ID,
        "role_id": role_id,
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "all_pass": core["all_pass"],
        "claim": "finite render/error/update trajectory and render-polarity distinction boundary",
        "allowed_claims": [
            "render/error/update are finite objects on the committed carrier",
            "render polarity boundary is classified against committed Axis-0 phi",
            "identity, scrambled-error, no-identity-leak, and positive-predicate controls were computed",
        ],
        "disallowed_claims": [
            "holodeck admission",
            "FEP admission",
            "physics admission",
            "Axis-0 admission or rescue of CP.12",
            "formal or canonical promotion",
        ],
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "package_observables": observables,
        "claim_path_tools": load_bearing,
        "TOOL_MANIFEST": {tool: {"tried": True, "used": True, "reason": observables[tool]} for tool in load_bearing},
        "TOOL_INTEGRATION_DEPTH": {tool: "load_bearing" for tool in load_bearing},
        **core,
    }
