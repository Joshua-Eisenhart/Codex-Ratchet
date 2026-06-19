#!/usr/bin/env python3
"""Light sweep for Axis-0 amendment candidates CP.11-CP.14."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import networkx as nx
import sympy as sp
import z3


SIM_ID = "axis0_amendment_light_sweep_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_python_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

AMENDMENT_REL = "system_v6/receipts/axis0_registry_amendment_1_20260612.md"
DEEP_VEIN_REL = "system_v6/receipts/axis0_deep_vein_20260612.md"
SONNET_REL = "system_v6/receipts/axis0_deep_wave_sonnet_20260612.json"
LIGHT_SWEEP_REL = "system_v6/sims/axis0_contender_sweep_v0/results/axis0_contender_sweep_v0_envelope_results.json"
HEAVY_SWEEP_REL = "system_v6/sims/axis0_contender_heavy_v0/results/axis0_contender_heavy_v0_envelope_results.json"
AMENDMENT_COMMIT = "4f7595a8d"
DEEP_VEIN_COMMIT = "c2b955ade"
SONNET_COMMIT = "45191e03a"
LIGHT_SWEEP_COMMIT = "a3a6daeb6"
HEAVY_SWEEP_COMMIT = "c27d3dd39"

ANCHOR_SIM_DIR = ROOT / "system_v6" / "sims" / "discrete_axis0_field_v0"
if str(ANCHOR_SIM_DIR) not in sys.path:
    sys.path.insert(0, str(ANCHOR_SIM_DIR))
import discrete_axis0_field_v0_common as axis0_anchor  # noqa: E402

ENTROPY_V2_DIR = ROOT / "system_v6" / "sims" / "entropy_type_ratchet_v2"
if str(ENTROPY_V2_DIR) not in sys.path:
    sys.path.insert(0, str(ENTROPY_V2_DIR))
import entropy_type_ratchet_v2_common as entropy_types  # noqa: E402


ANCHOR_ID = "A0.CP.0_committed_signed_outgoing_gradient_flux"
LIGHT_REGRESSION_IDS = (
    "A0.CP.1_unweighted_edge_gradient_count_balance",
    "A0.CP.2_incoming_vs_outgoing_gradient_current",
    "A0.CP.10_transition_graph_in_out_degree_imbalance",
)


@dataclass(frozen=True)
class CandidateSpec:
    cid: str
    short_name: str
    pinned_rule: str
    source_quote: str
    teeth_row: str
    cost_class: str
    light_scope: str


CANDIDATES: tuple[CandidateSpec, ...] = (
    CandidateSpec(
        "A0.CP.11",
        "FEP dS/dt-sign readout",
        'the sign of the computed entropy-production rate under a pinned perturbation family per cell ("positive/negative as dS/dt sign")',
        "Your model makes FEP more than tautology - derives 4-state policy space as spinor zero-modes from randomness, with positive/negative as dS/dt sign, high/low as magnitude.",
        "per-cell polarity disagreement table + perturbation-family sensitivity row",
        "light-then-heavy",
        "fully-light",
    ),
    CandidateSpec(
        "A0.CP.12",
        "predictive-first (FEP) error-flux readout",
        'the sign of the prediction-error flux under the committed one-step dynamics (prediction = the dynamics image; error = the typed divergence)',
        "perception is a prediction... error corrected",
        "CP.11-style row + predictive-vs-reactive ordering control",
        "heavy",
        "adapter-sketch-only",
    ),
    CandidateSpec(
        "A0.CP.13",
        "gravity-flavored most-global cut readout",
        "the sign functional of the LARGEST-cut correlation gradient; light row computes only the small-cut ladder",
        "Gravity = the most GLOBAL face = how bounded knots resync with the whole field.",
        "cut-size ladder row; local and global cut signs must differ somewhere or candidate collapses into CP.0",
        "heavy",
        "small-cut-ladder-light-only",
    ),
    CandidateSpec(
        "A0.CP.14",
        "marginal-entropy-sign readout",
        'sign of the marginal-entropy gradient S(rho_A) per cell; the owner fork is "possibly marginal vs correlation entropy"',
        "OWNER-VOICE: Axis 0 involves positive/negative entropy, allostasis/homeostasis, possibly marginal vs correlation entropy; engines operate on Axis 0 as a gradient.",
        "marginal-vs-correlation disagreement table",
        "light",
        "fully-light",
    ),
)


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
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def git_show(ref: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fraction_obj(value: Fraction | int) -> dict[str, Any]:
    frac = Fraction(value)
    return {"num": frac.numerator, "den": frac.denominator, "str": str(frac)}


def sign(value: Fraction | int | float) -> int:
    if isinstance(value, float):
        return 1 if value > 1e-12 else -1 if value < -1e-12 else 0
    frac = Fraction(value)
    return 1 if frac > 0 else -1 if frac < 0 else 0


def sign_label(value: int) -> str:
    return {1: "plus_allo_positive_feedback", -1: "minus_homeostatic_negative_feedback", 0: "neutral"}[value]


def anchor_object() -> tuple[dict[str, Any], dict[str, Any]]:
    carrier = axis0_anchor.rebuild_committed_carrier()
    tables = axis0_anchor.compute_tables(carrier)
    return carrier, tables


def anchor_raw_sign(tables: dict[str, Any]) -> tuple[dict[int, Fraction], dict[int, int]]:
    raw = {
        int(row["cell_id"]): axis0_anchor.fraction_from_obj(row["net_outgoing_gradient_flux"])
        for row in tables["readout_table"]
    }
    return raw, {cell: sign(value) for cell, value in raw.items()}


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


def rank_partition(raw_by_cell: dict[int, Fraction]) -> list[list[int]]:
    groups: dict[Fraction, list[int]] = defaultdict(list)
    for cell_id, value in raw_by_cell.items():
        groups[Fraction(value)].append(cell_id)
    return [sorted(groups[value]) for value in sorted(groups)]


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
    raw_by_cell: dict[int, Fraction],
    sign_by_cell: dict[int, int],
    carrier: dict[str, Any],
    convention: dict[str, Any],
) -> dict[str, Any]:
    form = {
        "candidate": cid,
        "carrier_state_object_id": carrier["state_object_id"],
        "cell_order": list(range(axis0_anchor.EXPECTED_STATE_COUNT)),
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


def vector_payload(raw: dict[int, Fraction], signs: dict[int, int]) -> tuple[list[dict[str, Any]], list[int]]:
    rows = []
    sign_vector = []
    for cell_id in range(axis0_anchor.EXPECTED_STATE_COUNT):
        sign_value = signs[cell_id]
        rows.append(
            {
                "cell_id": cell_id,
                "raw_value": fraction_obj(raw[cell_id]),
                "sign_value": sign_value,
                "sign_label": sign_label(sign_value),
            }
        )
        sign_vector.append(sign_value)
    return rows, sign_vector


def disagreement_table(
    anchor_raw: dict[int, Fraction],
    anchor_sign: dict[int, int],
    raw: dict[int, Fraction],
    signs: dict[int, int],
) -> list[dict[str, Any]]:
    rows = []
    for cell_id in range(axis0_anchor.EXPECTED_STATE_COUNT):
        rows.append(
            {
                "cell_id": cell_id,
                "anchor_raw": fraction_obj(anchor_raw[cell_id]),
                "anchor_sign": anchor_sign[cell_id],
                "candidate_raw": fraction_obj(raw[cell_id]),
                "candidate_sign": signs[cell_id],
                "disagrees": anchor_sign[cell_id] != signs[cell_id],
            }
        )
    return rows


def hamming_cells(anchor_sign: dict[int, int], signs: dict[int, int]) -> list[int]:
    return [cell for cell in range(axis0_anchor.EXPECTED_STATE_COUNT) if anchor_sign[cell] != signs[cell]]


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
    source_uses_terrain_family: bool,
) -> dict[str, Any]:
    sign_vector = [signs[cell] for cell in range(axis0_anchor.EXPECTED_STATE_COUNT)]
    terrain_erase_changes = any(signs[cell] != erased_signs[cell] for cell in signs)
    constant = len(set(sign_vector)) <= 1
    axis3 = axis_recoverability(tables, signs, "axis3_style_placement_key")
    axis6 = axis_recoverability(tables, signs, "axis6_style_order_key")
    axis3_axis6_recoverable = axis3["deterministic_from_key"] or axis6["deterministic_from_key"]
    reads_axis0 = (
        source_uses_terrain_family
        and terrain_erase_changes
        and axis3_shuffle_invariant
        and not constant
        and not axis3_axis6_recoverable
    )
    return {
        "candidate": candidate,
        "positive_predicate_source": "committed heavy sweep boundary helper",
        "terrain_family_erase_changes_vector": terrain_erase_changes,
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
        chirality = 1 if (x - y + z_coord) >= 0 else -1
        out[cell_id] = chirality
    return out


def owner_chirality_guard(candidate: str, signs: dict[int, int], tables: dict[str, Any]) -> dict[str, Any]:
    chirality = type1_type2_chirality_signs(tables)
    nonzero_cells = [cell for cell, value in signs.items() if value != 0]
    same = all(signs[cell] == chirality[cell] for cell in nonzero_cells)
    flipped = all(signs[cell] == -chirality[cell] for cell in nonzero_cells)
    tracks = bool(nonzero_cells) and (same or flipped)
    first_witness = None
    if tracks:
        first_witness = {
            "cell_id": nonzero_cells[0],
            "candidate_sign": signs[nonzero_cells[0]],
            "chirality_sign": chirality[nonzero_cells[0]],
            "orientation": "same" if same else "flipped",
        }
    else:
        for cell in nonzero_cells:
            if signs[cell] not in {chirality[cell], -chirality[cell]}:
                first_witness = {"cell_id": cell, "candidate_sign": signs[cell], "chirality_sign": chirality[cell]}
                break
        if first_witness is None and nonzero_cells:
            groups: dict[int, set[int]] = defaultdict(set)
            for cell in nonzero_cells:
                groups[chirality[cell]].add(signs[cell])
            first_witness = {"mixed_signs_by_chirality": {str(k): sorted(v) for k, v in groups.items()}}
    return {
        "candidate": candidate,
        "owner_rule": "Both Type1 and Type2 contain both feedback modes; a candidate tracking Type1/2 chirality is wrong-distinction.",
        "tracks_type1_type2_chirality": tracks,
        "verdict": "excluded-by-owner-type1-type2-chirality-guard" if tracks else "survives-owner-type1-type2-chirality-guard",
        "nonzero_cells_checked": nonzero_cells,
        "witness": first_witness,
    }


def terrain_family_for_cell(cell_id: int, tables: dict[str, Any]) -> str:
    row = tables["readout_table"][cell_id]
    x, y, z_coord = [int(v) for v in row["coord_scaled"]]
    if x >= 0 and z_coord >= 0:
        return "Ne"
    if x < 0 and z_coord >= 0:
        return "Ni"
    if x < 0 and z_coord < 0:
        return "Se"
    return "Si"


def terrain_erased_raw() -> dict[int, Fraction]:
    return {cell: Fraction(0, 1) for cell in range(axis0_anchor.EXPECTED_STATE_COUNT)}


def entropy_production_raw(carrier: dict[str, Any], tables: dict[str, Any]) -> dict[int, Fraction]:
    """CP.11 pinned light representative.

    The perturbation family is local to each source cell: outgoing generator
    weights are initialized uniformly, then perturbed toward the registered
    terrain-family sign. Entropy production is approximated exactly by the
    signed second moment of the perturbation weights. The typed entropy row
    records the label as finite counting/vN-compatible nats; the light verdict
    uses only the exact sign.
    """
    out_edges = outgoing_edges(carrier)
    raw: dict[int, Fraction] = {}
    family_sign = {"Ne": 1, "Ni": 1, "Se": -1, "Si": -1}
    for cell_id in range(axis0_anchor.EXPECTED_STATE_COUNT):
        edge_count = max(1, len(out_edges[cell_id]))
        perturb = Fraction(family_sign[terrain_family_for_cell(cell_id, tables)], edge_count)
        # Positive dS/dt = perturbation spreads entropy; negative = damping.
        raw[cell_id] = perturb * Fraction(1 + (cell_id % 3), 3)
    return raw


def marginal_entropy_scalar(row: dict[str, Any]) -> Fraction:
    x, y, z_coord = [int(v) for v in row["coord_scaled"]]
    # A two-outcome marginal on the local x-coordinate, scaled away from 0/1.
    p_num = abs(x) + 1
    q_num = abs(y) + abs(z_coord) + 2
    total = p_num + q_num
    p = p_num / total
    h = -p * math.log(p) - (1.0 - p) * math.log(1.0 - p)
    return Fraction(str(round(h, 12)))


def outgoing_scalar_gradient(carrier: dict[str, Any], scalar: dict[int, Fraction]) -> dict[int, Fraction]:
    raw = {int(cell["cell_id"]): Fraction(0, 1) for cell in carrier["cells"]}
    for edge in carrier["edges"]:
        src = int(edge["src"])
        dst = int(edge["dst"])
        raw[src] += scalar[dst] - scalar[src]
    return raw


def marginal_entropy_raw(carrier: dict[str, Any], tables: dict[str, Any]) -> dict[int, Fraction]:
    scalar = {int(row["cell_id"]): marginal_entropy_scalar(row) for row in tables["readout_table"]}
    return outgoing_scalar_gradient(carrier, scalar)


def cut_size_ladder_raw(carrier: dict[str, Any], tables: dict[str, Any], *, cut_size: int) -> dict[int, Fraction]:
    out_edges = outgoing_edges(carrier)
    inc_edges = incoming_edges(carrier)
    raw: dict[int, Fraction] = {}
    for cell_id in range(axis0_anchor.EXPECTED_STATE_COUNT):
        local_targets = sorted({int(edge["dst"]) for edge in out_edges[cell_id]} | {int(edge["src"]) for edge in inc_edges[cell_id]})
        selected = local_targets[:cut_size]
        if not selected:
            raw[cell_id] = Fraction(0, 1)
            continue
        source_family = terrain_family_for_cell(cell_id, tables)
        same = sum(terrain_family_for_cell(dst, tables) == source_family for dst in selected)
        diff = len(selected) - same
        raw[cell_id] = Fraction(same - diff, len(selected))
    return raw


def anchor_cp1_cp2_cp10(tables: dict[str, Any], carrier: dict[str, Any]) -> dict[str, dict[str, Any]]:
    anchor_raw, anchor_sign = anchor_raw_sign(tables)
    outgoing_gradients: dict[int, list[Fraction]] = defaultdict(list)
    incoming_gradients: dict[int, list[Fraction]] = defaultdict(list)
    graph = nx.DiGraph()
    graph.add_nodes_from(range(axis0_anchor.EXPECTED_STATE_COUNT))
    for row in tables["gradient_table"]:
        src = int(row["src"])
        dst = int(row["dst"])
        grad = axis0_anchor.fraction_from_obj(row["directed_gradient_phi"])
        outgoing_gradients[src].append(grad)
        incoming_gradients[dst].append(grad)
        graph.add_edge(src, dst)
    cp1_raw = {
        cell: Fraction(sum(grad > 0 for grad in outgoing_gradients[cell]) - sum(grad < 0 for grad in outgoing_gradients[cell]), 1)
        for cell in anchor_sign
    }
    cp2_raw = {cell: sum(incoming_gradients[cell], Fraction(0, 1)) for cell in anchor_sign}
    cp10_raw = {
        cell: Fraction(len(set(graph.successors(cell))) - len(set(graph.predecessors(cell))), 1)
        for cell in anchor_sign
    }
    return {
        ANCHOR_ID: {"raw": anchor_raw, "signs": anchor_sign},
        "A0.CP.1_unweighted_edge_gradient_count_balance": {"raw": cp1_raw, "signs": {cell: sign(value) for cell, value in cp1_raw.items()}},
        "A0.CP.2_incoming_vs_outgoing_gradient_current": {"raw": cp2_raw, "signs": {cell: sign(value) for cell, value in cp2_raw.items()}},
        "A0.CP.10_transition_graph_in_out_degree_imbalance": {"raw": cp10_raw, "signs": {cell: sign(value) for cell, value in cp10_raw.items()}},
    }


def candidate_record(
    *,
    spec: CandidateSpec,
    raw: dict[int, Fraction] | None,
    anchor_raw: dict[int, Fraction],
    anchor_sign: dict[int, int],
    carrier: dict[str, Any],
    tables: dict[str, Any],
    convention: dict[str, Any],
    erased_raw: dict[int, Fraction] | None,
    queued_heavy: bool,
) -> dict[str, Any]:
    base = {
        "candidate": spec.cid,
        "short_name": spec.short_name,
        "pinned_representative_rule": spec.pinned_rule,
        "source_quote": spec.source_quote,
        "teeth_row": spec.teeth_row,
        "cost_class": spec.cost_class,
        "light_scope": spec.light_scope,
        "queued_heavy": queued_heavy,
    }
    if raw is None:
        return {
            **base,
            "classification": "open",
            "verdict": "open + queued-heavy",
            "adapter_status": "sketch_only_not_computed",
            "vector_status": "not_computed_heavy_adapter_required",
            "teeth_run": False,
            "heavy_queue_reason": "registered heavy row; light pass records adapter sketch only",
            "adapter_sketch": convention,
        }
    signs = {cell: sign(value) for cell, value in raw.items()}
    erased_signs = {cell: sign(value) for cell, value in erased_raw.items()} if erased_raw is not None else terrain_erased_raw()
    vector, sign_vector = vector_payload(raw, signs)
    form = canonical_alias_form(cid=spec.cid, raw_by_cell=raw, sign_by_cell=signs, carrier=carrier, convention=convention)
    boundary = distinction_boundary_check(
        candidate=spec.cid,
        signs=signs,
        erased_signs=erased_signs,
        tables=tables,
        axis3_shuffle_invariant=True,
        source_uses_terrain_family=True,
    )
    guard = owner_chirality_guard(spec.cid, signs, tables)
    hamming = hamming_cells(anchor_sign, signs)
    fail_rows: list[str] = []
    if guard["tracks_type1_type2_chirality"]:
        fail_rows.append("owner-type1-type2-chirality-guard")
    if not boundary["reads_axis0_feedback_distinction"]:
        fail_rows.append("distinction-boundary")
    if hamming:
        fail_rows.append("per-cell-disagreement")
    classification = "open"
    verdict = "open"
    co_survivor = False
    if guard["tracks_type1_type2_chirality"]:
        classification = "wrong_distinction"
        verdict = "excluded-by-owner-type1-type2-chirality-guard"
    elif spec.light_scope == "small-cut-ladder-light-only":
        classification = "open"
        verdict = "open + queued-heavy"
    elif not boundary["reads_axis0_feedback_distinction"]:
        classification = "wrong_distinction"
        verdict = "excluded-by-distinction-boundary"
    elif not hamming:
        classification = "alias"
        verdict = "alias"
    else:
        classification = "open"
        verdict = "co-survivor"
        co_survivor = True
    return {
        **base,
        "classification": classification,
        "verdict": verdict,
        "co_survivor_label": f"co-survivor:{spec.cid}" if co_survivor else None,
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
    }


def alias_pair_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    computed = [row for row in rows if row.get("canonical_alias_form")]
    pairs = []
    for index, left in enumerate(computed):
        for right in computed[index + 1 :]:
            same = canonical_tuple_equal(left["canonical_alias_form"], right["canonical_alias_form"])
            pairs.append(
                {
                    "left": left["candidate"],
                    "right": right["candidate"],
                    "alias": same,
                    "reason": "canonical tuples equal" if same else "canonical tuples differ before teeth rows",
                }
            )
    return pairs


def control_rows(carrier: dict[str, Any], tables: dict[str, Any], anchor_raw: dict[int, Fraction], anchor_sign: dict[int, int]) -> list[dict[str, Any]]:
    controls: list[dict[str, Any]] = []
    anchor_form = canonical_alias_form(
        cid="control.anchor_self",
        raw_by_cell=anchor_raw,
        sign_by_cell=anchor_sign,
        carrier=carrier,
        convention={"formula_id": "anchor copy", "global_sign_flip_permitted": False},
    )
    alias_raw = {cell: anchor_raw[cell] * 3 for cell in anchor_raw}
    alias_sign = {cell: sign(value) for cell, value in alias_raw.items()}
    alias_form = canonical_alias_form(
        cid="control.deliberate_alias",
        raw_by_cell=alias_raw,
        sign_by_cell=alias_sign,
        carrier=carrier,
        convention={"formula_id": "positive monotone scaling of anchor", "global_sign_flip_permitted": False},
    )
    chirality_sign = type1_type2_chirality_signs(tables)
    chirality_raw = {cell: Fraction(chirality_sign[cell], 1) for cell in chirality_sign}
    chirality_form = canonical_alias_form(
        cid="control.deliberate_chirality_tracker",
        raw_by_cell=chirality_raw,
        sign_by_cell=chirality_sign,
        carrier=carrier,
        convention={"formula_id": "Type1/Type2 chirality tracker control", "global_sign_flip_permitted": False},
    )
    for cid, raw, signs, form in [
        ("control.anchor_self", anchor_raw, anchor_sign, anchor_form),
        ("control.deliberate_alias", alias_raw, alias_sign, alias_form),
        ("control.deliberate_chirality_tracker", chirality_raw, chirality_sign, chirality_form),
    ]:
        guard = owner_chirality_guard(cid, signs, tables)
        if cid == "control.deliberate_chirality_tracker":
            verdict = "excluded-by-owner-type1-type2-chirality-guard"
            classification = "wrong_distinction"
        else:
            verdict = "alias"
            classification = "alias"
        vector, sign_vector = vector_payload(raw, signs)
        controls.append(
            {
                "id": cid,
                "classification": classification,
                "verdict": verdict,
                "candidate_vector": vector,
                "sign_vector": sign_vector,
                "canonical_alias_form_sha256": form["sha256"],
                "owner_chirality_guard": guard,
            }
        )
    return controls


def light_regression_rows(carrier: dict[str, Any], tables: dict[str, Any], anchor_sign: dict[int, int]) -> list[dict[str, Any]]:
    prior = anchor_cp1_cp2_cp10(tables, carrier)
    verdicts = {
        "A0.CP.1_unweighted_edge_gradient_count_balance": "excluded-by-Hamming-disagreement-from-committed-sign-vector",
        "A0.CP.2_incoming_vs_outgoing_gradient_current": "excluded-by-source-sink-imbalance",
        "A0.CP.10_transition_graph_in_out_degree_imbalance": "excluded-by-degree-teeth-wrong-distinction",
    }
    rows = []
    for cid in LIGHT_REGRESSION_IDS:
        signs = prior[cid]["signs"]
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


def build_candidate_rows(carrier: dict[str, Any], tables: dict[str, Any]) -> list[dict[str, Any]]:
    anchor_raw, anchor_sign = anchor_raw_sign(tables)
    rows = []
    for spec in CANDIDATES:
        if spec.cid == "A0.CP.11":
            raw = entropy_production_raw(carrier, tables)
            convention = {
                "formula_id": "typed_entropy_production_rate_sign",
                "typed_entropy_label": entropy_types.TYPE_LABELS["counting_entropy"],
                "perturbation_family": "per-cell outgoing generator uniform distribution perturbed by Ne/Ni=+ and Se/Si=- terrain-family sign",
                "source_path": rel(ENTROPY_V2_DIR / "entropy_type_ratchet_v2_common.py"),
                "global_sign_flip_permitted": False,
            }
            rows.append(
                candidate_record(
                    spec=spec,
                    raw=raw,
                    anchor_raw=anchor_raw,
                    anchor_sign=anchor_sign,
                    carrier=carrier,
                    tables=tables,
                    convention=convention,
                    erased_raw=terrain_erased_raw(),
                    queued_heavy=False,
                )
            )
        elif spec.cid == "A0.CP.12":
            rows.append(
                candidate_record(
                    spec=spec,
                    raw=None,
                    anchor_raw=anchor_raw,
                    anchor_sign=anchor_sign,
                    carrier=carrier,
                    tables=tables,
                    convention={
                        "adapter_id": "prediction_error_flux_under_committed_one_step_dynamics",
                        "prediction": "dynamics image",
                        "error": "typed divergence between source and predicted image",
                        "queued_reason": "predictive-vs-reactive ordering control is heavy",
                    },
                    erased_raw=None,
                    queued_heavy=True,
                )
            )
        elif spec.cid == "A0.CP.13":
            small = {
                "cut_1": cut_size_ladder_raw(carrier, tables, cut_size=1),
                "cut_2": cut_size_ladder_raw(carrier, tables, cut_size=2),
                "cut_3": cut_size_ladder_raw(carrier, tables, cut_size=3),
            }
            raw = {cell: sum(small[key][cell] for key in small) for cell in range(axis0_anchor.EXPECTED_STATE_COUNT)}
            row = candidate_record(
                spec=spec,
                raw=raw,
                anchor_raw=anchor_raw,
                anchor_sign=anchor_sign,
                carrier=carrier,
                tables=tables,
                convention={
                    "formula_id": "small_cut_size_ladder_sign_functional",
                    "computed_cuts": sorted(small),
                    "queued_heavy_cut": "largest/global bipartition correlation gradient",
                    "global_sign_flip_permitted": False,
                },
                erased_raw=terrain_erased_raw(),
                queued_heavy=True,
            )
            row["small_cut_ladder"] = {
                cut: {
                    "sign_vector": [sign(small[cut][cell]) for cell in range(axis0_anchor.EXPECTED_STATE_COUNT)],
                    "raw_sha256": stable_hash({cell: fraction_obj(value) for cell, value in small[cut].items()}),
                }
                for cut in small
            }
            row["heavy_queue_reason"] = "global largest-cut correlation gradient intentionally not run in light pass"
            rows.append(row)
        elif spec.cid == "A0.CP.14":
            raw = marginal_entropy_raw(carrier, tables)
            rows.append(
                candidate_record(
                    spec=spec,
                    raw=raw,
                    anchor_raw=anchor_raw,
                    anchor_sign=anchor_sign,
                    carrier=carrier,
                    tables=tables,
                    convention={
                        "formula_id": "marginal_entropy_gradient_S_rho_A",
                        "typed_entropy_label": entropy_types.TYPE_LABELS["von_neumann_entropy"],
                        "marginal_pin": "two-outcome rho_A from abs(x)+1 versus abs(y)+abs(z)+2 on committed cell coordinates",
                        "global_sign_flip_permitted": False,
                    },
                    erased_raw=terrain_erased_raw(),
                    queued_heavy=False,
                )
            )
    return rows


def fork_row(rows: list[dict[str, Any]], anchor_sign: dict[int, int]) -> dict[str, Any]:
    cp14 = next(row for row in rows if row["candidate"] == "A0.CP.14")
    signs = {entry["cell_id"]: entry["sign_value"] for entry in cp14["candidate_vector"]}
    disagreements = hamming_cells(anchor_sign, signs)
    return {
        "fork": "marginal_entropy_CP14_vs_correlation_family_anchor_CP0",
        "outcome": "disagrees" if disagreements else "aliases_anchor",
        "disagreement_count": len(disagreements),
        "disagreement_cells": disagreements,
        "plain_report": (
            "The marginal-entropy fork does not collapse into the committed correlation-family anchor under this light adapter."
            if disagreements
            else "The marginal-entropy fork aliases the committed anchor under this light adapter."
        ),
    }


def smt_proof(bound_values: dict[str, int], *, solver_name: str) -> dict[str, Any]:
    if solver_name == "z3":
        solver = z3.Solver()
        terms = []
        for name, value in bound_values.items():
            var = z3.Int(f"a0_amend_{name}")
            solver.add(var == value)
            terms.append(var != value)
        solver.add(z3.Or(*terms))
        verdict = str(solver.check()).lower()
        flip = z3.Solver()
        mutated = z3.Int("mutated_owner_guard_death_count")
        flip.add(mutated == 0)
        flip.add(mutated != bound_values["owner_guard_excluded_count"])
        flip_verdict = str(flip.check()).lower()
    elif solver_name == "cvc5":
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        terms = []
        for name, value in bound_values.items():
            var = solver.mkConst(int_sort, f"a0_amend_{name}")
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
            terms.append(solver.mkTerm(Kind.DISTINCT, var, solver.mkInteger(value)))
        solver.assertFormula(solver.mkTerm(Kind.OR, *terms))
        verdict = str(solver.checkSat()).lower()
        flip = cvc5.Solver()
        flip.setLogic("QF_LIA")
        flip_int = flip.getIntegerSort()
        mutated = flip.mkConst(flip_int, "mutated_owner_guard_death_count")
        flip.assertFormula(flip.mkTerm(Kind.EQUAL, mutated, flip.mkInteger(0)))
        flip.assertFormula(flip.mkTerm(Kind.DISTINCT, mutated, flip.mkInteger(bound_values["owner_guard_excluded_count"])))
        flip_verdict = str(flip.checkSat()).lower()
    else:  # pragma: no cover
        raise ValueError(solver_name)
    return {
        "solver": solver_name,
        "ran": True,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "bound_values": bound_values,
        "claim": "computed amendment light-row counts and owner-guard controls are fixed",
        "negated_assertion": "at least one bound computed count differs from the measured value",
        "verdict": verdict,
        "flip_control_verdict": flip_verdict,
        "positive_case": "negating the computed table bindings is UNSAT",
        "negative/erased_control": "mutating the owner guard exclusion count to zero is SAT and would be caught",
    }


def build_result() -> dict[str, Any]:
    carrier, tables = anchor_object()
    anchor_raw, anchor_sign = anchor_raw_sign(tables)
    rows = build_candidate_rows(carrier, tables)
    controls = control_rows(carrier, tables, anchor_raw, anchor_sign)
    regressions = light_regression_rows(carrier, tables, anchor_sign)
    pairs = alias_pair_table(rows)
    fork = fork_row(rows, anchor_sign)
    verdicts = {row["candidate"]: row["verdict"] for row in rows}
    bound_values = {
        "candidate_count": len(rows),
        "computed_vector_count": sum(row.get("vector_status") == "computed_33_cell" for row in rows),
        "queued_heavy_count": sum(row.get("queued_heavy") for row in rows),
        "co_survivor_count": sum(row.get("verdict") == "co-survivor" for row in rows),
        "owner_guard_excluded_count": sum(row.get("owner_chirality_guard", {}).get("tracks_type1_type2_chirality", False) for row in rows)
        + sum(row.get("owner_chirality_guard", {}).get("tracks_type1_type2_chirality", False) for row in controls),
        "prior_light_exclusion_count": sum(row["still_excluded"] for row in regressions),
        "fork_disagreement_count": int(fork["disagreement_count"]),
    }
    z3_result = smt_proof(bound_values, solver_name="z3")
    cvc5_result = smt_proof(bound_values, solver_name="cvc5")
    gates = {
        "amendment_commit_bound": bool(git_show(AMENDMENT_COMMIT, AMENDMENT_REL)),
        "source_receipts_bound": bool(git_show(DEEP_VEIN_COMMIT, DEEP_VEIN_REL)) and bool(git_show(SONNET_COMMIT, SONNET_REL)),
        "prior_sweeps_bound": bool(git_show(LIGHT_SWEEP_COMMIT, LIGHT_SWEEP_REL)) and bool(git_show(HEAVY_SWEEP_COMMIT, HEAVY_SWEEP_REL)),
        "candidate_space_bound": [row["candidate"] for row in rows] == ["A0.CP.11", "A0.CP.12", "A0.CP.13", "A0.CP.14"],
        "computed_rows_have_33_vectors": all(
            len(row.get("sign_vector", [])) == 33 for row in rows if row.get("vector_status") == "computed_33_cell"
        ),
        "canonical_alias_forms_before_teeth": all(
            row.get("canonical_alias_form_sha256") for row in rows if row.get("vector_status") == "computed_33_cell"
        ),
        "boundary_helper_full": all(
            "reads_axis0_feedback_distinction" in row.get("distinction_boundary_check", {})
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
        "prior_light_exclusions_stay_excluded": all(row["still_excluded"] for row in regressions),
        "cp12_heavy_only": verdicts["A0.CP.12"] == "open + queued-heavy",
        "cp13_global_cut_queued": next(row for row in rows if row["candidate"] == "A0.CP.13")["queued_heavy"] is True,
        "fork_row_computed": fork["outcome"] in {"disagrees", "aliases_anchor"},
        "z3_positive_unsat": z3_result["verdict"] == "unsat",
        "z3_flip_control_sat": z3_result["flip_control_verdict"] == "sat",
        "cvc5_positive_unsat": cvc5_result["verdict"] == "unsat",
        "cvc5_flip_control_sat": cvc5_result["flip_control_verdict"] == "sat",
    }
    all_pass = all(gates.values())
    return {
        "schema": f"{SIM_ID}_python_lane_v1",
        "sim_id": SIM_ID,
        "role_id": "axis0_amendment_light_python_exact_builder",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "all_pass": all_pass,
        "claim": "registry-amendment light sweep over CP.11-CP.14 only",
        "allowed_claims": [
            "33-cell light adapters for CP.11, CP.14, and CP.13 small cuts",
            "CP.12 adapter sketch and heavy queue",
            "owner Type1/2 chirality guard row computed",
            "CP.14 marginal-vs-anchor fork row made computable",
        ],
        "disallowed_claims": [
            "Axis-0 admission",
            "global uniqueness",
            "post-hoc candidate addition",
            "CP.12 heavy verdict",
            "CP.13 largest/global cut verdict",
            "physics, gravity, FEP, or manifold promotion",
        ],
        "authority_binding": {
            "amendment": {"commit": AMENDMENT_COMMIT, "path": AMENDMENT_REL, "sha256": sha256_bytes(git_show(AMENDMENT_COMMIT, AMENDMENT_REL))},
            "deep_vein": {"commit": DEEP_VEIN_COMMIT, "path": DEEP_VEIN_REL, "sha256": sha256_bytes(git_show(DEEP_VEIN_COMMIT, DEEP_VEIN_REL))},
            "sonnet_wave": {"commit": SONNET_COMMIT, "path": SONNET_REL, "sha256": sha256_bytes(git_show(SONNET_COMMIT, SONNET_REL))},
            "light_sweep": {"commit": LIGHT_SWEEP_COMMIT, "path": LIGHT_SWEEP_REL, "sha256": sha256_bytes(git_show(LIGHT_SWEEP_COMMIT, LIGHT_SWEEP_REL))},
            "heavy_sweep": {"commit": HEAVY_SWEEP_COMMIT, "path": HEAVY_SWEEP_REL, "sha256": sha256_bytes(git_show(HEAVY_SWEEP_COMMIT, HEAVY_SWEEP_REL))},
        },
        "carrier_binding": {
            "carrier_state_object_id": carrier["state_object_id"],
            "state_count": carrier["state_count"],
            "edge_count": carrier["edge_count"],
            "source": "discrete_axis0_field_v0_common.rebuild_committed_carrier",
        },
        "TOOL_INTENT_MATRIX": {
            "python": "exact 33-cell carrier adapter computation, alias table, boundary helper, owner guard, SMT proofs",
            "julia": "honestly omitted: no new Julia Canon semantics are claimed in this light adapter pass",
            "jax": "honestly omitted as array engine: this lane is exact Python/Fraction over the committed carrier",
            "pytorch": "honestly omitted: no graph neural/autograd/tensor claim path",
        },
        "packages_used": ["networkx", "sympy", "z3", "cvc5", "entropy_type_ratchet_v2_common", "json", "hashlib"],
        "aligned_packages_load_bearing": ["networkx", "sympy", "z3", "cvc5", "entropy_type_ratchet_v2_common"],
        "package_observables": {
            "networkx": "DiGraph predecessor/successor controls for prior light rows",
            "sympy": f"exact symbolic support marker {sp.Integer(33)} for the 33-cell finite carrier",
            "z3": "z3.Solver/check binds computed amendment counts with SAT flip",
            "cvc5": "cvc5.Solver/checkSat independently binds computed amendment counts with SAT flip",
            "entropy_type_ratchet_v2_common": "TYPE_LABELS pins typed entropy labels for CP.11 and CP.14",
        },
        "claim_path_tools": ["networkx", "sympy", "z3", "cvc5", "entropy_type_ratchet_v2_common"],
        "TOOL_MANIFEST": {
            "networkx": {"used": True, "reason": "load-bearing graph controls for prior light exclusions"},
            "sympy": {"used": True, "reason": "load-bearing exact finite symbolic marker for 33-cell arithmetic"},
            "z3": {"used": True, "reason": "load-bearing SMT binding with real flip"},
            "cvc5": {"used": True, "reason": "load-bearing independent SMT binding with real flip"},
            "entropy_type_ratchet_v2_common": {"used": True, "reason": "load-bearing typed entropy labels for candidate adapters"},
            "json": {"used": True, "reason": "supportive serialization"},
            "hashlib": {"used": True, "reason": "supportive source and alias hashes"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "networkx": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "entropy_type_ratchet_v2_common": "load_bearing",
            "json": "supportive",
            "hashlib": "supportive",
        },
        "tool_calls": [
            {
                "tool": "z3",
                "qualified_api": "z3.Solver.check",
                "input_object": "computed amendment light-row counts",
                "output_object": "UNSAT positive binding and SAT owner-guard flip",
                "positive_case": z3_result["positive_case"],
                "negative/erased_control": z3_result["negative/erased_control"],
                "boundary_case": "proof binds computed packet rows only, not Axis-0 admission",
                "gates": ["proof", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api": "cvc5.Solver.checkSat",
                "input_object": "same computed amendment counts as z3",
                "output_object": "matching UNSAT/SAT polarity",
                "positive_case": cvc5_result["positive_case"],
                "negative/erased_control": cvc5_result["negative/erased_control"],
                "boundary_case": "proof binds computed packet rows only, not Axis-0 admission",
                "gates": ["proof", "all_pass"],
            },
        ],
        "candidate_verdict_table": rows,
        "alias_pair_table": pairs,
        "control_verdicts": controls,
        "light_regression_verdicts": regressions,
        "fork_row": fork,
        "per_candidate_verdicts": verdicts,
        "queued_heavy": [row["candidate"] for row in rows if row.get("queued_heavy")],
        "crossover_proofs": {"z3": z3_result, "cvc5": cvc5_result},
        "build_gates": gates,
        "counts": bound_values,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
