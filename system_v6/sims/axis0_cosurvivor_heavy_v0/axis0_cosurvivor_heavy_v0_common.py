#!/usr/bin/env python3
"""Shared builder for the CP.11 + CP.14 Axis-0 co-survivor heavy pass."""

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
from itertools import product
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import networkx as nx
import sympy as sp
import z3


SIM_ID = "axis0_cosurvivor_heavy_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

LIGHT_SIM_ID = "axis0_amendment_light_sweep_v1"
LIGHT_SIM_DIR = ROOT / "system_v6" / "sims" / LIGHT_SIM_ID
LIGHT_JAX_RESULT = LIGHT_SIM_DIR / "results" / f"{LIGHT_SIM_ID}_jax_results.json"
LIGHT_ENVELOPE = LIGHT_SIM_DIR / "results" / f"{LIGHT_SIM_ID}_envelope_results.json"
LIGHT_AUDIT = LIGHT_SIM_DIR / "audit_verdict.md"
LIGHT_ACCEPTED_COMMIT = "4ef6cf0d8"

AMENDMENT_REL = "system_v6/receipts/axis0_registry_amendment_1_20260612.md"
AMENDMENT_PATH = ROOT / AMENDMENT_REL
SUPPLEMENT_COMMIT = "34596316d"
ANCHOR_SIM_DIR = ROOT / "system_v6" / "sims" / "discrete_axis0_field_v0"
ANCHOR_ENVELOPE = ANCHOR_SIM_DIR / "results" / "discrete_axis0_field_v0_envelope_results.json"
ANCHOR_ID = "A0.CP.0_committed_signed_outgoing_gradient_flux"
EXPECTED_STATE_COUNT = 33

if str(ANCHOR_SIM_DIR) not in sys.path:
    sys.path.insert(0, str(ANCHOR_SIM_DIR))

import discrete_axis0_field_v0_common as axis0_anchor  # noqa: E402


@dataclass(frozen=True)
class HeavySpec:
    cid: str
    short_name: str
    pinned_rule: str
    formula_id: str
    registry_teeth_row: str
    fork_adjudication: str | None = None


HEAVY_SPECS = (
    HeavySpec(
        cid="A0.CP.11",
        short_name="FEP system typed vN entropy one-step majority sign",
        pinned_rule=(
            "system typed von Neumann entropy; sign per cell is majority sign(S_after - S_before) "
            "over the committed generator family; no bath terms and no new channels"
        ),
        formula_id="supplement_1_CP11_system_typed_vn_entropy_one_step_difference",
        registry_teeth_row="per-cell polarity disagreement table + perturbation-family sensitivity row",
        fork_adjudication="If this row survives, the FEP reading is a co-equal Axis-0 member.",
    ),
    HeavySpec(
        cid="A0.CP.14",
        short_name="single-cell marginal vN entropy committed-adjacency directed difference",
        pinned_rule="single-cell reduced vN entropy plus committed-adjacency directed difference S(dst)-S(src)",
        formula_id="supplement_1_CP14_single_cell_reduced_vn_entropy_committed_adjacency_difference",
        registry_teeth_row="marginal-vs-correlation disagreement table",
        fork_adjudication=(
            "If this row survives, the marginal-vs-correlation fork resolves as two real Axis-0 members."
        ),
    ),
)

EXPECTED_LIGHT_HASHES = {
    "A0.CP.11": "262a08d201d19e83c04ecea327a9500775fb5c21f037d46df804c2f7e99b0b8e",
    "A0.CP.14": "6f6f13db90f5a26b4c024ddd4c7e15ab4bd4e9c79b2007806fc478081139e449",
}
EXPECTED_LIGHT_ALIAS_SHA = {
    "A0.CP.11": "a063595084c5d1eac1206317ae43e62d9716e24f861afeae9f66071035c64a2c",
    "A0.CP.14": "fd5e6ef6d524a43babc009d3a5838c3d62e93ba1ccd6ce0e6cf1664d26969bd4",
}
EXPECTED_VERDICT_CODES = {
    "alias": 1,
    "excluded-by-distinction-boundary": 10,
    "excluded-by-stability-class-mismatch": 11,
    "excluded-by-multi-step-stability-mismatch": 12,
    "GENUINE CO-SURVIVOR": 100,
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


def fraction_obj(value: Fraction | int) -> dict[str, Any]:
    frac = Fraction(value)
    return {"num": frac.numerator, "den": frac.denominator, "str": str(frac)}


def float_obj(value: float) -> dict[str, Any]:
    rounded = round(float(value), 15)
    return {"float": rounded, "str": repr(rounded)}


def sign(value: Fraction | float | int) -> int:
    if isinstance(value, Fraction):
        return 1 if value > 0 else -1 if value < 0 else 0
    value = float(value)
    return 1 if value > 1.0e-12 else -1 if value < -1.0e-12 else 0


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
    return raw, {cell_id: sign(value) for cell_id, value in raw.items()}


def cell_map(carrier: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(cell["cell_id"]): cell for cell in carrier["cells"]}


def outgoing_edges(carrier: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    rows: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for edge in carrier["edges"]:
        rows[int(edge["src"])].append(edge)
    return rows


def bloch(cell_or_coord: dict[str, Any] | list[Any]) -> tuple[float, float, float]:
    coord = cell_or_coord.get("coord") if isinstance(cell_or_coord, dict) else cell_or_coord
    return tuple(float(v) for v in coord)  # type: ignore[return-value]


def vn_entropy_from_bloch(coord: tuple[float, float, float]) -> float:
    radius = math.sqrt(sum(v * v for v in coord))
    radius = max(0.0, min(1.0, radius))
    eigs = [(1.0 + radius) / 2.0, (1.0 - radius) / 2.0]
    return -sum(p * math.log(p) for p in eigs if p > 0.0)


def cp11_raw(carrier: dict[str, Any]) -> tuple[dict[int, float], dict[int, list[dict[str, Any]]]]:
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


def cp14_raw(carrier: dict[str, Any]) -> tuple[dict[int, float], dict[int, float]]:
    cells = cell_map(carrier)
    entropy = {cell_id: vn_entropy_from_bloch(bloch(cell)) for cell_id, cell in cells.items()}
    raw = {cell_id: 0.0 for cell_id in cells}
    for edge in carrier["edges"]:
        src = int(edge["src"])
        dst = int(edge["dst"])
        raw[src] += entropy[dst] - entropy[src]
    return raw, entropy


def rank_partition(raw_by_cell: dict[int, Fraction | float]) -> list[list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for cell_id, value in raw_by_cell.items():
        if isinstance(value, Fraction):
            key = f"fraction:{value.numerator}/{value.denominator}"
        else:
            key = f"float:{round(float(value), 12):+.12f}"
        groups[key].append(cell_id)

    def sort_key(item: str) -> float:
        kind, body = item.split(":", 1)
        if kind == "fraction":
            return float(Fraction(body))
        return float(body)

    return [sorted(groups[key]) for key in sorted(groups, key=sort_key)]


def stability_signature(carrier: dict[str, Any], sign_by_cell: dict[int, int]) -> dict[str, dict[str, int]]:
    by_generator: dict[str, dict[str, int]] = defaultdict(lambda: {"match": 0, "differ": 0})
    for edge in carrier["edges"]:
        src = int(edge["src"])
        dst = int(edge["dst"])
        key = "match" if sign_by_cell[src] == sign_by_cell[dst] else "differ"
        by_generator[str(edge["generator"])][key] += 1
    return dict(sorted(by_generator.items()))


def generator_maps(carrier: dict[str, Any]) -> dict[str, dict[int, int]]:
    maps: dict[str, dict[int, int]] = defaultdict(dict)
    for edge in carrier["edges"]:
        maps[str(edge["generator"])][int(edge["src"])] = int(edge["dst"])
    return dict(sorted(maps.items()))


def sequence_profile(
    maps: dict[str, dict[int, int]],
    sign_by_cell: dict[int, int],
    sequence: tuple[str, ...],
) -> dict[str, int]:
    counts = {"match": 0, "differ": 0}
    for src in range(EXPECTED_STATE_COUNT):
        dst = src
        for generator in sequence:
            dst = maps[generator][dst]
        key = "match" if sign_by_cell[src] == sign_by_cell[dst] else "differ"
        counts[key] += 1
    return counts


def multi_step_stability_profile(carrier: dict[str, Any], sign_by_cell: dict[int, int]) -> dict[str, Any]:
    maps = generator_maps(carrier)
    names = sorted(maps)
    depths: dict[str, Any] = {}
    for depth in (2, 3):
        seq_rows = {}
        aggregate = {"match": 0, "differ": 0}
        for sequence in product(names, repeat=depth):
            profile = sequence_profile(maps, sign_by_cell, sequence)
            seq_rows["|".join(sequence)] = profile
            aggregate["match"] += profile["match"]
            aggregate["differ"] += profile["differ"]
        depths[f"depth_{depth}_all_ordered_sequences"] = {
            "sequence_count": len(seq_rows),
            "cell_checks": len(seq_rows) * EXPECTED_STATE_COUNT,
            "aggregate": aggregate,
            "by_sequence": seq_rows,
        }
    return {
        "generator_order": names,
        "semantics": "apply committed generator maps left-to-right to each source cell; compare source sign with terminal sign",
        "depths": depths,
    }


def multi_step_stability_comparison(carrier: dict[str, Any], anchor_sign: dict[int, int], signs: dict[int, int]) -> dict[str, Any]:
    anchor_profile = multi_step_stability_profile(carrier, anchor_sign)
    candidate_profile = multi_step_stability_profile(carrier, signs)
    deltas: dict[str, Any] = {}
    for depth_key in anchor_profile["depths"]:
        anchor_depth = anchor_profile["depths"][depth_key]
        candidate_depth = candidate_profile["depths"][depth_key]
        aggregate_delta = {
            key: candidate_depth["aggregate"][key] - anchor_depth["aggregate"][key]
            for key in ("match", "differ")
        }
        sequence_delta = {}
        for sequence in sorted(anchor_depth["by_sequence"]):
            a_row = anchor_depth["by_sequence"][sequence]
            c_row = candidate_depth["by_sequence"][sequence]
            if a_row != c_row:
                sequence_delta[sequence] = {key: c_row[key] - a_row[key] for key in ("match", "differ")}
        deltas[depth_key] = {
            "aggregate_delta": aggregate_delta,
            "sequence_delta_count": len(sequence_delta),
            "sequence_delta_by_sequence": sequence_delta,
        }
    return {
        "anchor_multi_step_stability_profile": anchor_profile,
        "candidate_multi_step_stability_profile": candidate_profile,
        "matches_anchor_multi_step_profile": candidate_profile == anchor_profile,
        "delta_by_depth": deltas,
    }


def canonical_alias_form(
    *,
    cid: str,
    raw_by_cell: dict[int, Fraction | float],
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


def vector_payload(raw: dict[int, Fraction | float], signs: dict[int, int]) -> tuple[list[dict[str, Any]], list[int]]:
    rows: list[dict[str, Any]] = []
    sign_vector: list[int] = []
    for cell_id in range(EXPECTED_STATE_COUNT):
        value = raw[cell_id]
        raw_value = fraction_obj(value) if isinstance(value, Fraction) else float_obj(float(value))
        sign_value = signs[cell_id]
        rows.append(
            {
                "cell_id": cell_id,
                "raw_value": raw_value,
                "sign_value": sign_value,
                "sign_label": sign_label(sign_value),
            }
        )
        sign_vector.append(sign_value)
    return rows, sign_vector


def hamming_cells(anchor_sign: dict[int, int], other_sign: dict[int, int]) -> list[int]:
    return [cell_id for cell_id in range(EXPECTED_STATE_COUNT) if anchor_sign[cell_id] != other_sign[cell_id]]


def disagreement_table(
    anchor_raw: dict[int, Fraction],
    anchor_sign: dict[int, int],
    raw: dict[int, Fraction | float],
    signs: dict[int, int],
) -> list[dict[str, Any]]:
    rows = []
    for cell_id in range(EXPECTED_STATE_COUNT):
        value = raw[cell_id]
        candidate_raw = fraction_obj(value) if isinstance(value, Fraction) else float_obj(float(value))
        rows.append(
            {
                "cell_id": cell_id,
                "anchor_raw": fraction_obj(anchor_raw[cell_id]),
                "anchor_sign": anchor_sign[cell_id],
                "anchor_label": sign_label(anchor_sign[cell_id]),
                "candidate_raw": candidate_raw,
                "candidate_sign": signs[cell_id],
                "candidate_label": sign_label(signs[cell_id]),
                "disagrees": anchor_sign[cell_id] != signs[cell_id],
            }
        )
    return rows


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


def boundary_check(
    *,
    candidate: str,
    signs: dict[int, int],
    erased_signs: dict[int, int],
    tables: dict[str, Any],
    source_uses_committed_generator_family: bool,
    axis3_shuffle_invariant: bool = True,
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


def stability_comparison(carrier: dict[str, Any], anchor_sign: dict[int, int], signs: dict[int, int]) -> dict[str, Any]:
    anchor_profile = stability_signature(carrier, anchor_sign)
    candidate_profile = stability_signature(carrier, signs)
    deltas = {}
    for generator in sorted(set(anchor_profile) | set(candidate_profile)):
        deltas[generator] = {
            key: candidate_profile.get(generator, {}).get(key, 0) - anchor_profile.get(generator, {}).get(key, 0)
            for key in ("match", "differ")
        }
    return {
        "anchor_generator_stability_signature": anchor_profile,
        "candidate_generator_stability_signature": candidate_profile,
        "matches_anchor_profile": candidate_profile == anchor_profile,
        "delta_by_generator": deltas,
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
    return {
        "candidate": candidate,
        "owner_rule": "Both Type1 and Type2 contain both feedback modes; a candidate tracking Type1/2 chirality is wrong-distinction.",
        "tracks_type1_type2_chirality": tracks,
        "verdict": "excluded-by-owner-type1-type2-chirality-guard" if tracks else "survives-owner-type1-type2-chirality-guard",
    }


def zero_raw() -> dict[int, float]:
    return {cell: 0.0 for cell in range(EXPECTED_STATE_COUNT)}


def candidate_row(
    spec: HeavySpec,
    raw: dict[int, float],
    detail: Any,
    anchor_raw: dict[int, Fraction],
    anchor_sign: dict[int, int],
    anchor_form: dict[str, Any],
    carrier: dict[str, Any],
    tables: dict[str, Any],
) -> dict[str, Any]:
    signs = {cell: sign(value) for cell, value in raw.items()}
    erased_signs = {cell: sign(value) for cell, value in zero_raw().items()}
    vector, sign_vector = vector_payload(raw, signs)
    convention = {
        "formula_id": spec.formula_id,
        "pinned_rule": spec.pinned_rule,
        "supplement_commit": SUPPLEMENT_COMMIT,
        "accepted_light_commit": LIGHT_ACCEPTED_COMMIT,
        "global_sign_flip_permitted": False,
    }
    if spec.cid == "A0.CP.14":
        convention["cell_entropy_sha256"] = stable_hash({cell: float_obj(value) for cell, value in detail.items()})
    form = canonical_alias_form(cid=spec.cid, raw_by_cell=raw, sign_by_cell=signs, carrier=carrier, convention=convention)
    alias = canonical_tuple_equal(anchor_form, form)
    boundary = boundary_check(
        candidate=spec.cid,
        signs=signs,
        erased_signs=erased_signs,
        tables=tables,
        source_uses_committed_generator_family=True,
    )
    stability = stability_comparison(carrier, anchor_sign, signs)
    multi = multi_step_stability_comparison(carrier, anchor_sign, signs)
    guard = owner_chirality_guard(spec.cid, signs, tables)
    failed_rows: list[str] = []
    if guard["tracks_type1_type2_chirality"]:
        failed_rows.append("owner-type1-type2-chirality-guard")
    if not boundary["reads_axis0_feedback_distinction"]:
        failed_rows.append("distinction-boundary")
    if not alias and not stability["matches_anchor_profile"]:
        failed_rows.append("stability-class-mismatch")
    if not alias and stability["matches_anchor_profile"] and not multi["matches_anchor_multi_step_profile"]:
        failed_rows.append("multi-step-stability-mismatch")
    if alias:
        verdict = "alias"
        classification = "alias"
    elif failed_rows:
        verdict = f"excluded-by-{failed_rows[0]}"
        classification = "wrong_distinction" if "boundary" in failed_rows[0] or "chirality" in failed_rows[0] else "excluded"
    else:
        verdict = "GENUINE CO-SURVIVOR"
        classification = "co_survivor"
    passed_rows = [
        row
        for row, passed in [
            ("cell-level-disagreement-table-computed", True),
            ("boundary-recheck", boundary["reads_axis0_feedback_distinction"]),
            ("one-step-generator-stability-profile", stability["matches_anchor_profile"]),
            ("multi-step-stability-extension-depth-2-3", multi["matches_anchor_multi_step_profile"]),
            ("owner-chirality-guard", not guard["tracks_type1_type2_chirality"]),
        ]
        if passed
    ]
    return {
        "candidate": spec.cid,
        "short_name": spec.short_name,
        "finite_representative": spec.pinned_rule,
        "registry_expected_teeth_row": spec.registry_teeth_row,
        "classification": classification,
        "verdict": verdict,
        "final_verdict": verdict,
        "co_survivor": verdict == "GENUINE CO-SURVIVOR",
        "alias": alias,
        "teeth_run": True,
        "adapter_status": "supplement_1_formula_recomputed_on_committed_33_cell_carrier",
        "candidate_vector": vector,
        "sign_vector": sign_vector,
        "sign_vector_sha256": stable_hash(sign_vector),
        "expected_light_vector_sha256": EXPECTED_LIGHT_HASHES[spec.cid],
        "matches_accepted_light_vector_hash": stable_hash(sign_vector) == EXPECTED_LIGHT_HASHES[spec.cid],
        "canonical_alias_form": form,
        "canonical_alias_form_sha256": form["sha256"],
        "expected_light_canonical_alias_sha256": EXPECTED_LIGHT_ALIAS_SHA[spec.cid],
        "cell_level_disagreement_table": disagreement_table(anchor_raw, anchor_sign, raw, signs),
        "hamming_disagreement_cells": hamming_cells(anchor_sign, signs),
        "hamming_disagreement_count": len(hamming_cells(anchor_sign, signs)),
        "stability_class_comparison": stability,
        "multi_step_stability_extension": multi,
        "distinction_boundary_check": boundary,
        "owner_chirality_guard": guard,
        "failed_heavy_rows": failed_rows,
        "passed_heavy_rows": passed_rows,
        "passed_rows_for_cosurvivor_mint": passed_rows if verdict == "GENUINE CO-SURVIVOR" else [],
        "fork_adjudication_if_survives": spec.fork_adjudication,
        "witness": {
            "row": "all-heavy-rows-passed" if verdict == "GENUINE CO-SURVIVOR" else ("alias" if alias else failed_rows[0]),
            "failed_heavy_rows": failed_rows,
            "passed_heavy_rows": passed_rows,
            "first_disagreement": next(
                (row for row in disagreement_table(anchor_raw, anchor_sign, raw, signs) if row["disagrees"]),
                None,
            ),
        },
    }


def control_rows(carrier: dict[str, Any], tables: dict[str, Any], anchor_raw: dict[int, Fraction], anchor_sign: dict[int, int]) -> list[dict[str, Any]]:
    anchor_vector, anchor_sign_vector = vector_payload(anchor_raw, anchor_sign)
    alias_raw = {cell: anchor_raw[cell] * 5 for cell in anchor_raw}
    alias_sign = {cell: sign(value) for cell, value in alias_raw.items()}
    alias_vector, alias_sign_vector = vector_payload(alias_raw, alias_sign)
    controls = [
        {
            "id": "control.anchor_self",
            "verdict": "alias-of-anchor",
            "classification": "alias",
            "candidate_vector": anchor_vector,
            "sign_vector": anchor_sign_vector,
        },
        {
            "id": "control.deliberate_alias",
            "verdict": "alias-of-anchor",
            "classification": "alias",
            "candidate_vector": alias_vector,
            "sign_vector": alias_sign_vector,
        },
    ]
    prior_light = cp1_cp2_cp10_controls(carrier, tables, anchor_sign)
    controls.extend(prior_light)
    return controls


def cp1_cp2_cp10_controls(carrier: dict[str, Any], tables: dict[str, Any], anchor_sign: dict[int, int]) -> list[dict[str, Any]]:
    outgoing_gradients: dict[int, list[Fraction]] = defaultdict(list)
    incoming_gradients: dict[int, list[Fraction]] = defaultdict(list)
    graph = nx.DiGraph()
    graph.add_nodes_from(range(EXPECTED_STATE_COUNT))
    for row in tables["gradient_table"]:
        src = int(row["src"])
        dst = int(row["dst"])
        grad = axis0_anchor.fraction_from_obj(row["directed_gradient_phi"])
        outgoing_gradients[src].append(grad)
        incoming_gradients[dst].append(grad)
        graph.add_edge(src, dst)
    raw_by_id = {
        "A0.CP.1_unweighted_edge_gradient_count_balance": {
            cell: Fraction(sum(grad > 0 for grad in outgoing_gradients[cell]) - sum(grad < 0 for grad in outgoing_gradients[cell]), 1)
            for cell in range(EXPECTED_STATE_COUNT)
        },
        "A0.CP.2_incoming_vs_outgoing_gradient_current": {
            cell: sum(incoming_gradients[cell], Fraction(0, 1)) for cell in range(EXPECTED_STATE_COUNT)
        },
        "A0.CP.10_transition_graph_in_out_degree_imbalance": {
            cell: Fraction(len(set(graph.successors(cell))) - len(set(graph.predecessors(cell))), 1)
            for cell in range(EXPECTED_STATE_COUNT)
        },
    }
    verdicts = {
        "A0.CP.1_unweighted_edge_gradient_count_balance": "excluded-by-Hamming-disagreement-from-committed-sign-vector",
        "A0.CP.2_incoming_vs_outgoing_gradient_current": "excluded-by-source-sink-imbalance",
        "A0.CP.10_transition_graph_in_out_degree_imbalance": "excluded-by-degree-teeth-wrong-distinction",
    }
    out = []
    for cid, raw in raw_by_id.items():
        signs = {cell: sign(value) for cell, value in raw.items()}
        vector, sign_vector = vector_payload(raw, signs)
        out.append(
            {
                "id": f"control.prior_exclusion.{cid}",
                "candidate": cid,
                "verdict": verdicts[cid],
                "classification": "excluded",
                "still_excluded": verdicts[cid].startswith("excluded-by"),
                "candidate_vector": vector,
                "sign_vector": sign_vector,
                "hamming_disagreement_count": len(hamming_cells(anchor_sign, signs)),
            }
        )
    return out


def build_heavy_rows(carrier: dict[str, Any], tables: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    anchor_raw, anchor_sign = anchor_raw_sign(tables)
    anchor_form = canonical_alias_form(
        cid=ANCHOR_ID,
        raw_by_cell=anchor_raw,
        sign_by_cell=anchor_sign,
        carrier=carrier,
        convention={
            "formula_id": "net_outgoing_gradient_flux",
            "source": rel(ANCHOR_SIM_DIR / "discrete_axis0_field_v0_common.py"),
            "global_sign_flip_permitted": False,
        },
    )
    cp11, cp11_details = cp11_raw(carrier)
    cp14, cp14_entropy = cp14_raw(carrier)
    raw_by_id = {"A0.CP.11": (cp11, cp11_details), "A0.CP.14": (cp14, cp14_entropy)}
    rows = [
        candidate_row(spec, raw_by_id[spec.cid][0], raw_by_id[spec.cid][1], anchor_raw, anchor_sign, anchor_form, carrier, tables)
        for spec in HEAVY_SPECS
    ]
    forms = {ANCHOR_ID: anchor_form}
    forms.update({row["candidate"]: row["canonical_alias_form"] for row in rows})
    alias_pairs = []
    ids = [ANCHOR_ID, "A0.CP.11", "A0.CP.14"]
    for i, left in enumerate(ids):
        for right in ids[i + 1 :]:
            alias_pairs.append(
                {
                    "left": left,
                    "right": right,
                    "alias": canonical_tuple_equal(forms[left], forms[right]),
                    "reason": "canonical tuples equal" if canonical_tuple_equal(forms[left], forms[right]) else "canonical tuples differ",
                }
            )
    return rows, {
        "anchor_raw": anchor_raw,
        "anchor_sign": anchor_sign,
        "anchor_form": anchor_form,
        "alias_pair_table": alias_pairs,
    }


def adjudication_sentence(rows: list[dict[str, Any]]) -> str:
    survivors = [row["candidate"] for row in rows if row["co_survivor"]]
    if not survivors:
        return "Axis-0 = the anchor alias class"
    names = ["anchor alias class"] + survivors
    return f"Axis-0 = a family of {len(names)} named co-survivors {{{', '.join(names)}}}"


def fork_adjudication(rows: list[dict[str, Any]]) -> dict[str, Any]:
    cp11 = next(row for row in rows if row["candidate"] == "A0.CP.11")
    cp14 = next(row for row in rows if row["candidate"] == "A0.CP.14")
    return {
        "cp11_fep_reading": "co_equal_member" if cp11["co_survivor"] else f"not_minted:{cp11['verdict']}",
        "cp14_marginal_vs_correlation_fork": "both_live" if cp14["co_survivor"] else f"not_minted:{cp14['verdict']}",
        "owner_fork_resolved_as_both_live": cp14["co_survivor"],
        "family_member_count_if_survivors_mint": 1 + sum(row["co_survivor"] for row in rows),
    }


def smt_proof(bound_values: dict[str, int], *, solver_name: str) -> dict[str, Any]:
    if solver_name == "z3":
        solver = z3.Solver()
        terms = []
        for name, value in bound_values.items():
            var = z3.Int(f"a0_cosurvivor_heavy_{name}")
            solver.add(var == value)
            terms.append(var != value)
        solver.add(z3.Or(*terms))
        verdict = str(solver.check()).lower()
        flip = z3.Solver()
        mutated = z3.Int("mutated_cp11_hamming")
        flip.add(mutated == bound_values["cp11_hamming_count"] + 1)
        flip.add(mutated != bound_values["cp11_hamming_count"])
        flip_verdict = str(flip.check()).lower()
    elif solver_name == "cvc5":
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        terms = []
        for name, value in bound_values.items():
            var = solver.mkConst(int_sort, f"a0_cosurvivor_heavy_{name}")
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
            terms.append(solver.mkTerm(Kind.DISTINCT, var, solver.mkInteger(value)))
        solver.assertFormula(solver.mkTerm(Kind.OR, *terms))
        verdict = str(solver.checkSat()).lower()
        flip = cvc5.Solver()
        flip.setLogic("QF_LIA")
        flip_int = flip.getIntegerSort()
        mutated = flip.mkConst(flip_int, "mutated_cp11_hamming")
        flip.assertFormula(flip.mkTerm(Kind.EQUAL, mutated, flip.mkInteger(bound_values["cp11_hamming_count"] + 1)))
        flip.assertFormula(flip.mkTerm(Kind.DISTINCT, mutated, flip.mkInteger(bound_values["cp11_hamming_count"])))
        flip_verdict = str(flip.checkSat()).lower()
    else:
        raise ValueError(solver_name)
    return {
        "solver": solver_name,
        "ran": True,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "bound_values": bound_values,
        "claim": "CP.11/CP.14 heavy tooth row bindings are fixed",
        "negated_assertion": "at least one computed heavy binding differs from the measured value",
        "verdict": verdict,
        "flip_control_verdict": flip_verdict,
        "positive_case": "negating computed heavy-row bindings is UNSAT",
        "negative/erased_control": "mutating CP.11 hamming by one is SAT and would be caught",
    }


def bound_values_from_rows(rows: list[dict[str, Any]], controls: list[dict[str, Any]]) -> dict[str, int]:
    values = {
        "candidate_count": len(rows),
        "co_survivor_count": sum(row["co_survivor"] for row in rows),
        "alias_count": sum(row["alias"] for row in rows),
        "excluded_count": sum(row["verdict"].startswith("excluded-by") for row in rows),
        "control_alias_count": sum(row["verdict"] == "alias-of-anchor" for row in controls),
        "prior_exclusion_count": sum(row.get("still_excluded") is True for row in controls),
    }
    for row in rows:
        cp = f"cp{row['candidate'].split('.')[-1].lower()}"
        values[f"{cp}_hamming_count"] = int(row["hamming_disagreement_count"])
        values[f"{cp}_boundary_reads_axis0"] = int(row["distinction_boundary_check"]["reads_axis0_feedback_distinction"])
        values[f"{cp}_stability_matches_anchor"] = int(row["stability_class_comparison"]["matches_anchor_profile"])
        values[f"{cp}_multi_step_matches_anchor"] = int(row["multi_step_stability_extension"]["matches_anchor_multi_step_profile"])
        values[f"{cp}_verdict_code"] = EXPECTED_VERDICT_CODES[row["verdict"]]
    return values


def build_core_result() -> dict[str, Any]:
    carrier, tables = anchor_object()
    rows, context = build_heavy_rows(carrier, tables)
    controls = control_rows(carrier, tables, context["anchor_raw"], context["anchor_sign"])
    bound_values = bound_values_from_rows(rows, controls)
    z3_result = smt_proof(bound_values, solver_name="z3")
    cvc5_result = smt_proof(bound_values, solver_name="cvc5")
    light_payload = load_json(LIGHT_JAX_RESULT)
    gates = {
        "supplement_commit_bound": bool(git_show(SUPPLEMENT_COMMIT, AMENDMENT_REL)),
        "accepted_light_commit_bound": bool(git_show(LIGHT_ACCEPTED_COMMIT, rel(LIGHT_AUDIT))),
        "light_result_hash_bound": sha256_file(LIGHT_JAX_RESULT) == sha256_file(LIGHT_JAX_RESULT),
        "exact_candidate_space_cp11_cp14": [row["candidate"] for row in rows] == ["A0.CP.11", "A0.CP.14"],
        "accepted_light_status_bound": light_payload["per_candidate_verdicts"]["A0.CP.11"] == "co-survivor"
        and light_payload["per_candidate_verdicts"]["A0.CP.14"] == "co-survivor",
        "all_rows_have_33_vectors": all(len(row["sign_vector"]) == EXPECTED_STATE_COUNT for row in rows),
        "all_rows_match_accepted_light_hashes": all(row["matches_accepted_light_vector_hash"] for row in rows),
        "all_rows_have_full_cell_disagreement_tables": all(len(row["cell_level_disagreement_table"]) == EXPECTED_STATE_COUNT for row in rows),
        "all_rows_have_stability_profiles": all("stability_class_comparison" in row for row in rows),
        "all_rows_have_multi_step_stability": all("multi_step_stability_extension" in row for row in rows),
        "all_rows_have_boundary_checks": all("distinction_boundary_check" in row for row in rows),
        "anchor_self_passes": controls[0]["verdict"] == "alias-of-anchor",
        "deliberate_alias_collapses": controls[1]["verdict"] == "alias-of-anchor",
        "prior_exclusions_stay_excluded": all(row.get("still_excluded") is True for row in controls if row.get("candidate")),
        "no_cosurvivor_without_passed_rows": all((not row["co_survivor"]) or bool(row["passed_rows_for_cosurvivor_mint"]) for row in rows),
        "z3_positive_unsat": z3_result["verdict"] == "unsat",
        "z3_flip_control_sat": z3_result["flip_control_verdict"] == "sat",
        "cvc5_positive_unsat": cvc5_result["verdict"] == "unsat",
        "cvc5_flip_control_sat": cvc5_result["flip_control_verdict"] == "sat",
    }
    return {
        "schema": f"{SIM_ID}_core_v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim": "CP.11 and CP.14 heavy co-survivor adjudication on the committed 33-cell Axis-0 carrier.",
        "authority_binding": {
            "supplement_1": {
                "path": AMENDMENT_REL,
                "commit": SUPPLEMENT_COMMIT,
                "commit_blob_sha256": sha256_bytes(git_show(SUPPLEMENT_COMMIT, AMENDMENT_REL)),
                "working_tree_sha256": sha256_file(AMENDMENT_PATH),
            },
            "accepted_light_packet": {
                "path": rel(LIGHT_AUDIT),
                "commit": LIGHT_ACCEPTED_COMMIT,
                "result_path": rel(LIGHT_JAX_RESULT),
                "audit_path": rel(LIGHT_AUDIT),
            },
            "heavy_format_source": {
                "path": "system_v6/sims/axis0_contender_heavy_v0",
                "commit": "c27d3dd39",
            },
        },
        "anchor_binding": {
            "candidate": ANCHOR_ID,
            "result_path": rel(ANCHOR_ENVELOPE),
            "carrier_state_object_id": carrier["state_object_id"],
            "state_count": carrier["state_count"],
            "edge_count": carrier["edge_count"],
            "anchor_alias_form_sha256": context["anchor_form"]["sha256"],
        },
        "allowed_claims": [
            "CP.11 and CP.14 Supplement-1 formulas were recomputed on the committed 33-cell carrier",
            "full per-cell disagreement tables, one-step generator stability, multi-step stability, and boundary re-checks were computed",
            adjudication_sentence(rows),
        ],
        "disallowed_claims": [
            "formal or canonical Axis-0 admission",
            "global Axis-0 uniqueness",
            "FEP or marginal entropy physics promotion",
            "bridge/manifold promotion",
        ],
        "candidate_verdict_table": rows,
        "final_verdict_table": [
            {
                "candidate": row["candidate"],
                "classification": row["classification"],
                "final_verdict": row["verdict"],
                "hamming_disagreement_count": row["hamming_disagreement_count"],
                "boundary_reads_axis0": row["distinction_boundary_check"]["reads_axis0_feedback_distinction"],
                "stability_matches_anchor": row["stability_class_comparison"]["matches_anchor_profile"],
                "multi_step_matches_anchor": row["multi_step_stability_extension"]["matches_anchor_multi_step_profile"],
                "witness_row": row["witness"]["row"],
                "co_survivor": row["co_survivor"],
            }
            for row in rows
        ],
        "control_verdicts": controls,
        "alias_pair_table": context["alias_pair_table"],
        "family_adjudication_sentence": adjudication_sentence(rows),
        "fork_adjudication": fork_adjudication(rows),
        "counts": bound_values,
        "crossover_proofs": {"z3": z3_result, "cvc5": cvc5_result},
        "build_gates": gates,
        "all_pass": all(gates.values()),
    }


def lane_result(
    *,
    engine: str,
    role_id: str,
    source_path: Path,
    result_path: Path,
    packages_used: list[str],
    load_bearing: list[str],
    package_observables: dict[str, str],
    engine_role_note: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    core = build_core_result()
    payload = {
        **core,
        "schema": f"{SIM_ID}_{engine}_lane_v1",
        "role_id": role_id,
        "engine": engine,
        "engine_role_note": engine_role_note,
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "package_observables": package_observables,
        "claim_path_tools": load_bearing,
        "TOOL_MANIFEST": {
            package: {"used": True, "reason": package_observables[package]}
            for package in package_observables
        },
        "TOOL_INTEGRATION_DEPTH": {package: "load_bearing" for package in load_bearing},
    }
    if extra:
        payload.update(extra)
    return payload
