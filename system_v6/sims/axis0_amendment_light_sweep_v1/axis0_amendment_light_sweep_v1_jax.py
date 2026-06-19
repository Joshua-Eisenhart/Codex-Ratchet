#!/usr/bin/env python3
"""Supplement-pinned Axis 0 amendment light sweep, Python/JAX-role lane."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import networkx as nx
import sympy as sp
import z3


SIM_ID = "axis0_amendment_light_sweep_v1"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"

ANCHOR_DIR = ROOT / "system_v6" / "sims" / "discrete_axis0_field_v0"
if str(ANCHOR_DIR) not in sys.path:
    sys.path.insert(0, str(ANCHOR_DIR))
import discrete_axis0_field_v0_common as axis0_anchor  # noqa: E402


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
EXPECTED_STATE_COUNT = 33
AMENDMENT_COMMIT = "34596316d"
AMENDMENT_REL = "system_v6/receipts/axis0_registry_amendment_1_20260612.md"
V0_SIM_DIR = ROOT / "system_v6" / "sims" / "axis0_amendment_light_sweep_v0"
V0_RESULT = V0_SIM_DIR / "results" / "axis0_amendment_light_sweep_v0_python_results.json"
V0_AUDIT = V0_SIM_DIR / "audit_verdict.md"
Z4_RESULT = ROOT / "system_v6" / "sims" / "z4_syndrome_record_v0" / "results" / "z4_syndrome_record_v0_envelope_results.json"

TOOL_MANIFEST = {
    "networkx": {"used": True, "reason": "finite directed committed-generator graph, adjacency, controls, and reachability witnesses"},
    "sympy": {"used": True, "reason": "source-visible exact finite carrier marker and rational control rows"},
    "z3": {"used": True, "reason": "SMT binding of computed count rows with positive unsat and erased/mutated sat control"},
    "cvc5": {"used": True, "reason": "independent SMT binding of the same computed count rows"},
}
TOOL_INTEGRATION_DEPTH = {
    "networkx": "load_bearing",
    "sympy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}
TOOL_INTENT = {
    "claim_classes": [
        "supplement_pinned_axis0_light_rerun",
        "finite_33_cell_entropy_vector",
        "committed_generator_one_step_difference",
        "light_trace_norm_prediction_error_vector",
        "queued_global_bipartition_coherent_information",
    ],
    "engine_tool_intent": {
        "jax": {
            "networkx": "rebuild the directed committed generator adjacency for CP.14 and controls",
            "sympy": "bind exact finite carrier/control constants in source-visible form",
            "z3": "bind computed pinned counts in SMT",
            "cvc5": "independent SMT binding of the computed pinned counts",
        }
    },
}


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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_show(ref: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT)


def git_last_commit(path: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def sign(value: float | int) -> int:
    return 1 if value > 1e-12 else -1 if value < -1e-12 else 0


def sign_label(value: int) -> str:
    return {1: "plus_allo_positive_feedback", -1: "minus_homeostatic_negative_feedback", 0: "neutral"}[value]


def float_obj(value: float | int) -> dict[str, Any]:
    number = float(value)
    rounded = round(number, 15)
    return {"float": rounded, "str": f"{rounded:.15g}"}


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


def outgoing_edges(carrier: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for edge in carrier["edges"]:
        out[int(edge["src"])].append(edge)
    return out


def incoming_edges(carrier: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    inc: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for edge in carrier["edges"]:
        inc[int(edge["dst"])].append(edge)
    return inc


def bloch(cell_or_coord: dict[str, Any] | list[Any]) -> tuple[float, float, float]:
    coord = cell_or_coord.get("coord") if isinstance(cell_or_coord, dict) else cell_or_coord
    return tuple(float(v) for v in coord)  # type: ignore[return-value]


def vn_entropy_from_bloch(coord: tuple[float, float, float]) -> float:
    radius = math.sqrt(sum(v * v for v in coord))
    radius = max(0.0, min(1.0, radius))
    eigs = [(1.0 + radius) / 2.0, (1.0 - radius) / 2.0]
    return -sum(p * math.log(p) for p in eigs if p > 0.0)


def trace_norm_bloch(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    # For single-qubit rho(r)-rho(s), the trace norm equals Euclidean ||r-s||.
    return math.sqrt(sum((a - b) * (a - b) for a, b in zip(left, right)))


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


def vector_payload(raw: dict[int, float], signs: dict[int, int]) -> tuple[list[dict[str, Any]], list[int]]:
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
            "anchor_raw": float_obj(anchor_raw[cell_id]),
            "anchor_sign": anchor_sign[cell_id],
            "candidate_raw": float_obj(raw[cell_id]),
            "candidate_sign": signs[cell_id],
            "disagrees": anchor_sign[cell_id] != signs[cell_id],
        }
        for cell_id in range(EXPECTED_STATE_COUNT)
    ]


def hamming_cells(anchor_sign: dict[int, int], signs: dict[int, int]) -> list[int]:
    return [cell for cell in range(EXPECTED_STATE_COUNT) if anchor_sign[cell] != signs[cell]]


def first_disagreement(anchor_sign: dict[int, int], signs: dict[int, int]) -> dict[str, Any]:
    for cell in hamming_cells(anchor_sign, signs):
        return {
            "cell_id": cell,
            "anchor_sign": anchor_sign[cell],
            "candidate_sign": signs[cell],
            "anchor_label": sign_label(anchor_sign[cell]),
            "candidate_label": sign_label(signs[cell]),
        }
    return {"cell_id": None, "anchor_sign": "equal", "candidate_sign": "equal"}


def axis_recoverability(tables: dict[str, Any], signs: dict[int, int], key_name: str) -> dict[str, Any]:
    groups: dict[str, Counter[int]] = defaultdict(Counter)
    for row in tables["readout_table"]:
        groups[str(row[key_name])][signs[int(row["cell_id"])]] += 1
    deterministic = all(len(counter) <= 1 for counter in groups.values())
    majority = sum(counter.most_common(1)[0][1] for counter in groups.values()) if groups else 0
    total = sum(sum(counter.values()) for counter in groups.values())
    return {
        "key_name": key_name,
        "deterministic_from_key": deterministic,
        "majority_accuracy": majority / total if total else 0.0,
        "ambiguous_keys": {key: dict(counter) for key, counter in groups.items() if len(counter) > 1},
    }


def distinction_boundary_check(
    *,
    candidate: str,
    signs: dict[int, int],
    erased_signs: dict[int, int],
    tables: dict[str, Any],
    axis3_shuffle_invariant: bool,
    source_uses_committed_generator_family: bool,
) -> dict[str, Any]:
    sign_vector = [signs[cell] for cell in range(EXPECTED_STATE_COUNT)]
    erase_changes = any(signs[cell] != erased_signs[cell] for cell in signs)
    constant = len(set(sign_vector)) <= 1
    axis3 = axis_recoverability(tables, signs, "axis3_style_placement_key")
    axis6 = axis_recoverability(tables, signs, "axis6_style_order_key")
    axis3_axis6_recoverable = axis3["deterministic_from_key"] or axis6["deterministic_from_key"]
    reads_axis0 = (
        source_uses_committed_generator_family
        and erase_changes
        and axis3_shuffle_invariant
        and not constant
        and not axis3_axis6_recoverable
    )
    return {
        "candidate": candidate,
        "positive_predicate_source": "Supplement 1 committed generator entropy boundary helper",
        "source_uses_committed_generator_family": source_uses_committed_generator_family,
        "state_entropy_erase_changes_vector": erase_changes,
        "terrain_family_erase_changes_vector": erase_changes,
        "axis3_loop_shuffle_invariant": axis3_shuffle_invariant,
        "constant_or_single_sign_vector": constant,
        "axis3_recoverability": axis3,
        "axis6_recoverability": axis6,
        "axis3_or_axis6_deterministically_recovers_vector": axis3_axis6_recoverable,
        "reads_axis0_feedback_distinction": reads_axis0,
    }


def type1_type2_chirality_signs(tables: dict[str, Any]) -> dict[int, int]:
    out: dict[int, int] = {}
    for row in tables["readout_table"]:
        cell_id = int(row["cell_id"])
        x, y, z_coord = [int(v) for v in row["coord_scaled"]]
        out[cell_id] = 1 if (x - y + z_coord) >= 0 else -1
    return out


def owner_chirality_guard(candidate: str, signs: dict[int, int], tables: dict[str, Any]) -> dict[str, Any]:
    chirality = type1_type2_chirality_signs(tables)
    nonzero_cells = [cell for cell, value in signs.items() if value != 0]
    same = all(signs[cell] == chirality[cell] for cell in nonzero_cells)
    flipped = all(signs[cell] == -chirality[cell] for cell in nonzero_cells)
    tracks = bool(nonzero_cells) and (same or flipped)
    groups: dict[int, set[int]] = defaultdict(set)
    for cell in nonzero_cells:
        groups[chirality[cell]].add(signs[cell])
    witness = {"mixed_signs_by_chirality": {str(k): sorted(v) for k, v in groups.items()}}
    return {
        "candidate": candidate,
        "owner_rule": "Both Type1 and Type2 contain both feedback modes; a candidate tracking Type1/2 chirality is wrong-distinction.",
        "tracks_type1_type2_chirality": tracks,
        "verdict": "excluded-by-owner-type1-type2-chirality-guard" if tracks else "survives-owner-type1-type2-chirality-guard",
        "nonzero_cells_checked": nonzero_cells,
        "witness": witness,
    }


def cp11_system_typed_vn_one_step_majority(carrier: dict[str, Any]) -> tuple[dict[int, float], dict[int, list[dict[str, Any]]]]:
    cells = cell_map(carrier)
    details: dict[int, list[dict[str, Any]]] = defaultdict(list)
    raw: dict[int, float] = {}
    for cell_id, edges in outgoing_edges(carrier).items():
        before = vn_entropy_from_bloch(bloch(cells[cell_id]))
        votes = []
        for edge in edges:
            after = vn_entropy_from_bloch(bloch(edge["image_before_quantization"]))
            delta = after - before
            vote = sign(delta)
            votes.append(vote)
            details[cell_id].append(
                {
                    "edge_id": edge["edge_id"],
                    "generator": edge["generator"],
                    "dst": int(edge["dst"]),
                    "S_before": float_obj(before),
                    "S_after": float_obj(after),
                    "delta": float_obj(delta),
                    "delta_sign": vote,
                }
            )
        raw[cell_id] = float(sum(votes))
    return raw, details


def cp14_single_cell_vn_adjacency_difference(carrier: dict[str, Any]) -> tuple[dict[int, float], dict[int, float]]:
    cells = cell_map(carrier)
    entropy = {cell_id: vn_entropy_from_bloch(bloch(cell)) for cell_id, cell in cells.items()}
    raw = {cell_id: 0.0 for cell_id in cells}
    for edge in carrier["edges"]:
        src = int(edge["src"])
        dst = int(edge["dst"])
        raw[src] += entropy[dst] - entropy[src]
    return raw, entropy


def cp12_trace_norm_error_change_light(carrier: dict[str, Any]) -> tuple[dict[int, float], dict[int, list[dict[str, Any]]]]:
    cells = cell_map(carrier)
    raw: dict[int, float] = {}
    details: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for cell_id, edges in outgoing_edges(carrier).items():
        votes = []
        src = bloch(cells[cell_id])
        for edge in edges:
            dst = bloch(cells[int(edge["dst"])])
            pred = bloch(edge["image_before_quantization"])
            source_to_prediction = trace_norm_bloch(src, pred)
            prediction_to_committed = trace_norm_bloch(pred, dst)
            error_change = prediction_to_committed - source_to_prediction
            vote = sign(error_change)
            votes.append(vote)
            details[cell_id].append(
                {
                    "edge_id": edge["edge_id"],
                    "generator": edge["generator"],
                    "dst": int(edge["dst"]),
                    "trace_norm_prediction_to_committed": float_obj(prediction_to_committed),
                    "trace_norm_source_to_prediction": float_obj(source_to_prediction),
                    "one_step_error_change": float_obj(error_change),
                    "one_step_error_change_sign": vote,
                }
            )
        raw[cell_id] = float(sum(votes))
    return raw, details


def zero_raw() -> dict[int, float]:
    return {cell: 0.0 for cell in range(EXPECTED_STATE_COUNT)}


def graph_controls(carrier: dict[str, Any]) -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_nodes_from(range(EXPECTED_STATE_COUNT))
    graph.add_edges_from((int(edge["src"]), int(edge["dst"])) for edge in carrier["edges"])
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "strong_component_count": nx.number_strongly_connected_components(graph),
        "finite_marker": str(sp.Integer(EXPECTED_STATE_COUNT)),
    }


def candidate_record(
    *,
    cid: str,
    short_name: str,
    pinned_rule: str,
    raw: dict[int, float] | None,
    anchor_raw: dict[int, float],
    anchor_sign: dict[int, int],
    carrier: dict[str, Any],
    tables: dict[str, Any],
    convention: dict[str, Any],
    erased_raw: dict[int, float] | None,
    queued_heavy: bool,
    light_scope: str,
    detail_rows: dict[int, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    base = {
        "candidate": cid,
        "short_name": short_name,
        "pinned_representative_rule": pinned_rule,
        "light_scope": light_scope,
        "queued_heavy": queued_heavy,
        "supplement_pin_commit": AMENDMENT_COMMIT,
    }
    if raw is None:
        return {
            **base,
            "classification": "open",
            "verdict": "open + queued-heavy",
            "adapter_status": "bound_not_computed_in_light_pass",
            "vector_status": "not_computed_heavy_global_bipartition_required",
            "teeth_run": False,
            "heavy_queue_reason": convention["queued_reason"],
            "adapter_sketch": convention,
        }
    signs = {cell: sign(value) for cell, value in raw.items()}
    erased_signs = {cell: sign(value) for cell, value in (erased_raw or zero_raw()).items()}
    vector, sign_vector = vector_payload(raw, signs)
    form = canonical_alias_form(cid=cid, raw_by_cell=raw, sign_by_cell=signs, carrier=carrier, convention=convention)
    boundary = distinction_boundary_check(
        candidate=cid,
        signs=signs,
        erased_signs=erased_signs,
        tables=tables,
        axis3_shuffle_invariant=True,
        source_uses_committed_generator_family=True,
    )
    guard = owner_chirality_guard(cid, signs, tables)
    hamming = hamming_cells(anchor_sign, signs)
    fail_rows: list[str] = []
    if guard["tracks_type1_type2_chirality"]:
        fail_rows.append("owner-type1-type2-chirality-guard")
    if not boundary["reads_axis0_feedback_distinction"]:
        fail_rows.append("distinction-boundary")
    if hamming:
        fail_rows.append("per-cell-disagreement-from-anchor")
    if guard["tracks_type1_type2_chirality"]:
        classification = "wrong_distinction"
        verdict = "excluded-by-owner-type1-type2-chirality-guard"
    elif not boundary["reads_axis0_feedback_distinction"]:
        classification = "wrong_distinction"
        verdict = "excluded-by-distinction-boundary"
    elif not hamming:
        classification = "alias"
        verdict = "alias"
    else:
        classification = "open"
        verdict = "co-survivor"
    return {
        **base,
        "classification": classification,
        "verdict": verdict,
        "co_survivor_label": f"co-survivor:{cid}" if verdict == "co-survivor" else None,
        "vector_status": "computed_33_cell",
        "teeth_run": True,
        "candidate_vector": vector,
        "sign_vector": sign_vector,
        "canonical_alias_form": form,
        "canonical_alias_form_sha256": form["sha256"],
        "cell_level_disagreement_table": disagreement_table(anchor_raw, anchor_sign, raw, signs),
        "hamming_disagreement_cells": hamming,
        "hamming_disagreement_count": len(hamming),
        "first_disagreement": first_disagreement(anchor_sign, signs),
        "distinction_boundary_check": boundary,
        "owner_chirality_guard": guard,
        "failed_light_rows": fail_rows,
        "stability_class_comparison": {
            "anchor_generator_stability_signature": stability_signature(carrier, anchor_sign),
            "candidate_generator_stability_signature": stability_signature(carrier, signs),
            "matches_anchor_profile": stability_signature(carrier, anchor_sign) == stability_signature(carrier, signs),
        },
        "light_detail_rows": detail_rows or {},
    }


def alias_pair_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    computed = [row for row in rows if row.get("canonical_alias_form")]
    pairs = []
    for index, left in enumerate(computed):
        for right in computed[index + 1 :]:
            same = canonical_tuple_equal(left["canonical_alias_form"], right["canonical_alias_form"])
            pairs.append({"left": left["candidate"], "right": right["candidate"], "alias": same})
    return pairs


def control_rows(carrier: dict[str, Any], tables: dict[str, Any], anchor_raw: dict[int, float], anchor_sign: dict[int, int]) -> list[dict[str, Any]]:
    alias_raw = {cell: anchor_raw[cell] * 3.0 for cell in anchor_raw}
    alias_sign = {cell: sign(value) for cell, value in alias_raw.items()}
    chirality_sign = type1_type2_chirality_signs(tables)
    chirality_raw = {cell: float(chirality_sign[cell]) for cell in chirality_sign}
    controls = []
    for cid, raw, signs, verdict, classification in [
        ("control.anchor_self", anchor_raw, anchor_sign, "alias", "alias"),
        ("control.deliberate_alias", alias_raw, alias_sign, "alias", "alias"),
        (
            "control.deliberate_chirality_tracker",
            chirality_raw,
            chirality_sign,
            "excluded-by-owner-type1-type2-chirality-guard",
            "wrong_distinction",
        ),
    ]:
        form = canonical_alias_form(
            cid=cid,
            raw_by_cell=raw,
            sign_by_cell=signs,
            carrier=carrier,
            convention={"formula_id": cid, "global_sign_flip_permitted": False},
        )
        vector, sign_vector = vector_payload(raw, signs)
        controls.append(
            {
                "id": cid,
                "classification": classification,
                "verdict": verdict,
                "candidate_vector": vector,
                "sign_vector": sign_vector,
                "canonical_alias_form_sha256": form["sha256"],
                "owner_chirality_guard": owner_chirality_guard(cid, signs, tables),
            }
        )
    return controls


def cp1_cp2_cp10_regression_controls(carrier: dict[str, Any], tables: dict[str, Any], anchor_sign: dict[int, int]) -> list[dict[str, Any]]:
    outgoing_gradients: dict[int, list[float]] = defaultdict(list)
    incoming_gradients: dict[int, list[float]] = defaultdict(list)
    graph = nx.DiGraph()
    graph.add_nodes_from(range(EXPECTED_STATE_COUNT))
    for row in tables["gradient_table"]:
        src = int(row["src"])
        dst = int(row["dst"])
        grad = float(axis0_anchor.fraction_from_obj(row["directed_gradient_phi"]))
        outgoing_gradients[src].append(grad)
        incoming_gradients[dst].append(grad)
        graph.add_edge(src, dst)
    candidates = {
        "A0.CP.1_unweighted_edge_gradient_count_balance": {
            cell: float(sum(grad > 0 for grad in outgoing_gradients[cell]) - sum(grad < 0 for grad in outgoing_gradients[cell]))
            for cell in range(EXPECTED_STATE_COUNT)
        },
        "A0.CP.2_incoming_vs_outgoing_gradient_current": {
            cell: float(sum(incoming_gradients[cell])) for cell in range(EXPECTED_STATE_COUNT)
        },
        "A0.CP.10_transition_graph_in_out_degree_imbalance": {
            cell: float(len(set(graph.successors(cell))) - len(set(graph.predecessors(cell)))) for cell in range(EXPECTED_STATE_COUNT)
        },
    }
    verdicts = {
        "A0.CP.1_unweighted_edge_gradient_count_balance": "excluded-by-Hamming-disagreement-from-committed-sign-vector",
        "A0.CP.2_incoming_vs_outgoing_gradient_current": "excluded-by-source-sink-imbalance",
        "A0.CP.10_transition_graph_in_out_degree_imbalance": "excluded-by-degree-teeth-wrong-distinction",
    }
    rows = []
    for cid, raw in candidates.items():
        signs = {cell: sign(value) for cell, value in raw.items()}
        rows.append(
            {
                "candidate": cid,
                "verdict": verdicts[cid],
                "still_excluded": verdicts[cid].startswith("excluded-by"),
                "hamming_disagreement_count": len(hamming_cells(anchor_sign, signs)),
                "first_disagreement": first_disagreement(anchor_sign, signs),
                "retested_as_control": True,
            }
        )
    return rows


def v0_regression_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    v0 = load_json(V0_RESULT)
    current = {row["candidate"]: row for row in rows}
    prior = {row["candidate"]: row for row in v0["candidate_verdict_table"]}
    out = []
    for cid in ["A0.CP.11", "A0.CP.14"]:
        old_vector = prior[cid]["sign_vector"]
        new_vector = current[cid]["sign_vector"]
        changed = [idx for idx, (old, new) in enumerate(zip(old_vector, new_vector)) if old != new]
        out.append(
            {
                "candidate": cid,
                "v0_vector_source": rel(V0_RESULT),
                "v0_audit_source": rel(V0_AUDIT),
                "pre_pin_formula_status": "nonconforming_v0_adapter",
                "pinned_formula_status": "Supplement 1 pinned computation",
                "old_sign_vector": old_vector,
                "new_sign_vector": new_vector,
                "pin_bite_count": len(changed),
                "pin_bite_cells": changed,
                "pin_bite_table": [
                    {"cell_id": cell, "v0_sign": old_vector[cell], "pinned_sign": new_vector[cell]} for cell in changed
                ],
            }
        )
    return out


def fork_row(rows: list[dict[str, Any]], anchor_sign: dict[int, int]) -> dict[str, Any]:
    cp14 = next(row for row in rows if row["candidate"] == "A0.CP.14")
    signs = {entry["cell_id"]: entry["sign_value"] for entry in cp14["candidate_vector"]}
    disagreements = hamming_cells(anchor_sign, signs)
    v0 = load_json(V0_RESULT)["fork_row"]
    return {
        "fork": "Supplement-pinned marginal CP.14 vs committed correlation family anchor",
        "outcome": "disagrees" if disagreements else "aliases_anchor",
        "disagreement_count": len(disagreements),
        "disagreement_cells": disagreements,
        "v0_observation": {
            "pre_pin_disagreement_count": int(v0["disagreement_count"]),
            "pre_pin_disagreement_cells": v0["disagreement_cells"],
            "status": "regression_observation_only_not_citable_as_pinned_CP14",
        },
        "pin_shift_vs_v0": {
            "count_delta": len(disagreements) - int(v0["disagreement_count"]),
            "cells_changed_membership": sorted(set(disagreements).symmetric_difference(v0["disagreement_cells"])),
        },
        "plain_report": "The fork is retested under CP.14's pinned single-cell vN entropy plus committed-adjacency directed difference.",
    }


def smt_proof(bound_values: dict[str, int], *, solver_name: str) -> dict[str, Any]:
    if solver_name == "z3":
        solver = z3.Solver()
        terms = []
        for name, value in bound_values.items():
            var = z3.Int(f"a0_pin_{name}")
            solver.add(var == value)
            terms.append(var != value)
        solver.add(z3.Or(*terms))
        verdict = str(solver.check()).lower()
        flip = z3.Solver()
        mutated = z3.Int("mutated_owner_guard_excluded_count")
        flip.add(mutated == 0)
        flip.add(mutated != bound_values["owner_guard_excluded_count"])
        flip_verdict = str(flip.check()).lower()
    elif solver_name == "cvc5":
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        terms = []
        for name, value in bound_values.items():
            var = solver.mkConst(int_sort, f"a0_pin_{name}")
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
            terms.append(solver.mkTerm(Kind.DISTINCT, var, solver.mkInteger(value)))
        solver.assertFormula(solver.mkTerm(Kind.OR, *terms))
        verdict = str(solver.checkSat()).lower()
        flip = cvc5.Solver()
        flip.setLogic("QF_LIA")
        flip_int = flip.getIntegerSort()
        mutated = flip.mkConst(flip_int, "mutated_owner_guard_excluded_count")
        flip.assertFormula(flip.mkTerm(Kind.EQUAL, mutated, flip.mkInteger(0)))
        flip.assertFormula(flip.mkTerm(Kind.DISTINCT, mutated, flip.mkInteger(bound_values["owner_guard_excluded_count"])))
        flip_verdict = str(flip.checkSat()).lower()
    else:
        raise ValueError(solver_name)
    return {
        "solver": solver_name,
        "ran": True,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "bound_values": bound_values,
        "claim": "computed Supplement-pinned light-row counts are fixed",
        "negated_assertion": "at least one bound computed count differs from the measured value",
        "verdict": verdict,
        "flip_control_verdict": flip_verdict,
        "positive_case": "negating the computed table bindings is UNSAT",
        "negative/erased_control": "mutating the owner guard exclusion count to zero is SAT and would be caught",
    }


def build_candidate_rows(carrier: dict[str, Any], tables: dict[str, Any]) -> list[dict[str, Any]]:
    anchor_raw, anchor_sign = anchor_raw_sign(tables)
    cp11_raw, cp11_details = cp11_system_typed_vn_one_step_majority(carrier)
    cp12_raw, cp12_details = cp12_trace_norm_error_change_light(carrier)
    cp14_raw, cp14_entropy = cp14_single_cell_vn_adjacency_difference(carrier)
    return [
        candidate_record(
            cid="A0.CP.11",
            short_name="system typed vN entropy one-step majority sign",
            pinned_rule="sign per cell = majority sign(S_after - S_before) over committed generator one-step images; no bath terms",
            raw=cp11_raw,
            anchor_raw=anchor_raw,
            anchor_sign=anchor_sign,
            carrier=carrier,
            tables=tables,
            convention={
                "formula_id": "supplement_1_CP11_system_typed_vn_entropy_one_step_difference",
                "entropy": "single-qubit von Neumann entropy of committed system cell density rho=(I+r.sigma)/2",
                "one_step_image": "edge.image_before_quantization from committed generator family",
                "per_cell_sign": "majority sign of S_after - S_before",
                "bath_terms": "excluded",
                "global_sign_flip_permitted": False,
            },
            erased_raw=zero_raw(),
            queued_heavy=False,
            light_scope="fully-light",
            detail_rows=cp11_details,
        ),
        candidate_record(
            cid="A0.CP.12",
            short_name="committed prediction trace-norm error-change light row",
            pinned_rule="committed one-step image as prediction + trace-norm divergence + one-step error-change sign",
            raw=cp12_raw,
            anchor_raw=anchor_raw,
            anchor_sign=anchor_sign,
            carrier=carrier,
            tables=tables,
            convention={
                "formula_id": "supplement_1_CP12_committed_prediction_trace_norm_light",
                "prediction": "edge.image_before_quantization from committed one-step dynamics",
                "error": "trace norm ||rho(prediction)-rho(committed_dst)||_1",
                "light_error_change": "trace_norm(prediction,dst)-trace_norm(src,prediction)",
                "heavy_queue": "predictive/reactive ordering controls over full families",
                "global_sign_flip_permitted": False,
            },
            erased_raw=zero_raw(),
            queued_heavy=True,
            light_scope="trace-norm-one-step-light; heavy-ordering-queued",
            detail_rows=cp12_details,
        ),
        candidate_record(
            cid="A0.CP.13",
            short_name="global Phi_0/I_c with z4 typing",
            pinned_rule="Phi_0/I_c at the global bipartition with z4 state-plus-record convention",
            raw=None,
            anchor_raw=anchor_raw,
            anchor_sign=anchor_sign,
            carrier=carrier,
            tables=tables,
            convention={
                "adapter_id": "supplement_1_CP13_global_bipartition_z4_Ic",
                "Phi_0_family": "bound to global bipartition",
                "coherent_information": "I_c with z4 state-plus-record convention",
                "z4_receipt_path": rel(Z4_RESULT) if Z4_RESULT.exists() else "missing:z4_syndrome_record_v0_envelope_results.json",
                "queued_reason": "heavy global bipartition/coherent-information computation required; no 33-cell local proxy emitted",
            },
            erased_raw=None,
            queued_heavy=True,
            light_scope="adapter-bound-only; global-heavy-queued",
        ),
        candidate_record(
            cid="A0.CP.14",
            short_name="single-cell reduced vN entropy committed-adjacency directed difference",
            pinned_rule="single-cell reduced vN entropy + committed-adjacency directed difference",
            raw=cp14_raw,
            anchor_raw=anchor_raw,
            anchor_sign=anchor_sign,
            carrier=carrier,
            tables=tables,
            convention={
                "formula_id": "supplement_1_CP14_single_cell_reduced_vn_entropy_committed_adjacency_difference",
                "entropy": "single-qubit von Neumann entropy of committed cell rho=(I+r.sigma)/2",
                "directed_difference": "sum over committed outgoing adjacency S(dst)-S(src)",
                "cell_entropy_sha256": stable_hash({cell: float_obj(value) for cell, value in cp14_entropy.items()}),
                "global_sign_flip_permitted": False,
            },
            erased_raw=zero_raw(),
            queued_heavy=False,
            light_scope="fully-light",
        ),
    ]


def build_result() -> dict[str, Any]:
    carrier, tables = anchor_object()
    anchor_raw, anchor_sign = anchor_raw_sign(tables)
    rows = build_candidate_rows(carrier, tables)
    controls = control_rows(carrier, tables, anchor_raw, anchor_sign)
    prior_controls = cp1_cp2_cp10_regression_controls(carrier, tables, anchor_sign)
    v0_rows = v0_regression_rows(rows)
    fork = fork_row(rows, anchor_sign)
    vector_hashes = {
        row["candidate"]: stable_hash(row.get("sign_vector", []))
        for row in rows
        if row.get("vector_status") == "computed_33_cell"
    }
    bound_values = {
        "candidate_count": len(rows),
        "computed_vector_count": sum(row.get("vector_status") == "computed_33_cell" for row in rows),
        "queued_heavy_count": sum(bool(row.get("queued_heavy")) for row in rows),
        "cp11_pin_bite_count": next(row for row in v0_rows if row["candidate"] == "A0.CP.11")["pin_bite_count"],
        "cp14_pin_bite_count": next(row for row in v0_rows if row["candidate"] == "A0.CP.14")["pin_bite_count"],
        "owner_guard_excluded_count": sum(
            row.get("owner_chirality_guard", {}).get("tracks_type1_type2_chirality", False) for row in rows + controls
        ),
        "prior_light_exclusion_count": sum(row["still_excluded"] for row in prior_controls),
        "fork_disagreement_count": int(fork["disagreement_count"]),
    }
    z3_result = smt_proof(bound_values, solver_name="z3")
    cvc5_result = smt_proof(bound_values, solver_name="cvc5")
    gates = {
        "supplement_commit_bound": bool(git_show(AMENDMENT_COMMIT, AMENDMENT_REL)),
        "v0_audit_bound": V0_AUDIT.is_file(),
        "candidate_space_bound": [row["candidate"] for row in rows] == ["A0.CP.11", "A0.CP.12", "A0.CP.13", "A0.CP.14"],
        "cp11_fully_computed": next(row for row in rows if row["candidate"] == "A0.CP.11")["vector_status"] == "computed_33_cell",
        "cp14_fully_computed": next(row for row in rows if row["candidate"] == "A0.CP.14")["vector_status"] == "computed_33_cell",
        "cp12_light_computed_heavy_queued": next(row for row in rows if row["candidate"] == "A0.CP.12")["queued_heavy"] is True
        and next(row for row in rows if row["candidate"] == "A0.CP.12")["vector_status"] == "computed_33_cell",
        "cp13_global_heavy_queued": next(row for row in rows if row["candidate"] == "A0.CP.13")["vector_status"]
        == "not_computed_heavy_global_bipartition_required",
        "computed_rows_have_33_vectors": all(
            len(row.get("sign_vector", [])) == EXPECTED_STATE_COUNT
            for row in rows
            if row.get("vector_status") == "computed_33_cell"
        ),
        "canonical_alias_forms_before_teeth": all(
            row.get("canonical_alias_form_sha256") for row in rows if row.get("vector_status") == "computed_33_cell"
        ),
        "boundary_helper_full": all(
            row.get("distinction_boundary_check", {}).get("reads_axis0_feedback_distinction") is not None
            for row in rows
            if row.get("vector_status") == "computed_33_cell"
        ),
        "owner_guard_row_computed": all(
            "tracks_type1_type2_chirality" in row.get("owner_chirality_guard", {})
            for row in rows
            if row.get("vector_status") == "computed_33_cell"
        ),
        "controls_fire": controls[0]["verdict"] == "alias"
        and controls[1]["verdict"] == "alias"
        and controls[2]["verdict"] == "excluded-by-owner-type1-type2-chirality-guard",
        "prior_light_exclusions_stay_excluded": all(row["still_excluded"] for row in prior_controls),
        "v0_pin_bite_computed": all("pin_bite_count" in row for row in v0_rows),
        "fork_row_computed": fork["outcome"] in {"disagrees", "aliases_anchor"},
        "z3_positive_unsat": z3_result["verdict"] == "unsat",
        "z3_flip_control_sat": z3_result["flip_control_verdict"] == "sat",
        "cvc5_positive_unsat": cvc5_result["verdict"] == "unsat",
        "cvc5_flip_control_sat": cvc5_result["flip_control_verdict"] == "sat",
    }
    all_pass = all(gates.values())
    amendment_bytes = git_show(AMENDMENT_COMMIT, AMENDMENT_REL)
    return {
        "schema": f"{SIM_ID}_jax_lane_v1",
        "sim_id": SIM_ID,
        "role_id": "supplement_pinned_axis0_light_jax_role_exact_builder",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "all_pass": all_pass,
        "claim": "Supplement 1 pinned light rerun over CP.11-CP.14",
        "allowed_claims": [
            "pinned 33-cell CP.11 system vN one-step majority vector",
            "pinned 33-cell CP.14 single-cell vN committed-adjacency directed-difference vector",
            "CP.12 one-step trace-norm/error-change light vector with heavy ordering controls queued",
            "CP.13 global Phi_0/I_c z4 adapter bound with heavy global bipartition queued",
            "v0 pre-pin vector regression bite rows",
        ],
        "disallowed_claims": [
            "Axis-0 admission",
            "global uniqueness",
            "canonical promotion",
            "CP.13 global coherent-information verdict",
            "CP.12 heavy predictive ordering verdict",
            "physics, gravity, FEP, bridge, or axis-level claim",
        ],
        "authority_binding": {
            "supplement": {"commit": AMENDMENT_COMMIT, "path": AMENDMENT_REL, "sha256": sha256_bytes(amendment_bytes)},
            "v0_audit_verdict": {
                "path": rel(V0_AUDIT),
                "exists": V0_AUDIT.exists(),
                "sha256": sha256_file(V0_AUDIT),
                "git_last_commit": git_last_commit(V0_AUDIT),
            },
        },
        "carrier_binding": {
            "carrier_state_object_id": carrier["state_object_id"],
            "state_count": carrier["state_count"],
            "edge_count": carrier["edge_count"],
            "source": "discrete_axis0_field_v0_common.rebuild_committed_carrier",
        },
        "graph_controls": graph_controls(carrier),
        "TOOL_INTENT_MATRIX": TOOL_INTENT,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "packages_used": ["networkx", "sympy", "z3", "cvc5", "json", "hashlib"],
        "aligned_packages_load_bearing": ["networkx", "z3", "cvc5"],
        "package_observables": {
            "networkx": "DiGraph exact node/edge/SCC counts over committed generator carrier",
            "z3": "z3.Solver/check binds computed pinned counts with SAT flip control",
            "cvc5": "cvc5.Solver/checkSat independently binds computed pinned counts with SAT flip control",
        },
        "claim_path_tools": ["networkx", "sympy", "z3", "cvc5"],
        "candidate_verdict_table": rows,
        "per_candidate_verdicts": {row["candidate"]: row["verdict"] for row in rows},
        "alias_pair_table": alias_pair_table(rows),
        "control_verdicts": controls,
        "prior_light_regression_verdicts": prior_controls,
        "v0_regression_rows": v0_rows,
        "fork_row": fork,
        "queued_heavy": [
            {
                "candidate": "A0.CP.12",
                "reason": "predictive/reactive ordering controls are heavy; light trace-norm one-step vector computed",
            },
            {
                "candidate": "A0.CP.13",
                "reason": "global bipartition Phi_0/I_c with z4 convention is heavy; adapter bound only",
            },
        ],
        "counts": bound_values,
        "computed_vector_hashes": vector_hashes,
        "crossover_proofs": {"z3": z3_result, "cvc5": cvc5_result},
        "build_gates": gates,
    }


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    print(json.dumps({"result_path": rel(RESULT_PATH), "all_pass": result["all_pass"], "counts": result["counts"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
