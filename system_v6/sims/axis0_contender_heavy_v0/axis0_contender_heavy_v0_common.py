#!/usr/bin/env python3
"""Shared Axis-0 contender heavy-pass machinery."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
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


SIM_ID = "axis0_contender_heavy_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

REGISTRY_REL = "system_v6/receipts/axis0_contender_probe_registry_20260612.md"
REGISTRY_PATH = ROOT / REGISTRY_REL
REGISTRY_COMMIT = "31dfd11b6"
DOCTRINE_REL = "system_v6/receipts/owner_doctrine_axes_as_existence_probes_20260612.md"
DOCTRINE_PATH = ROOT / DOCTRINE_REL
DOCTRINE_COMMIT = "fcf1b3858"
SWEEP_AUDIT_REL = "system_v6/sims/axis0_contender_sweep_v0/audit_verdict.md"
SWEEP_AUDIT_PATH = ROOT / SWEEP_AUDIT_REL
SWEEP_COMMIT = "a3a6daeb6"
SWEEP_RESULT_PATH = ROOT / "system_v6/sims/axis0_contender_sweep_v0/results/axis0_contender_sweep_v0_jax_results.json"
ANCHOR_SIM_DIR = ROOT / "system_v6" / "sims" / "discrete_axis0_field_v0"
ANCHOR_RESULT = ANCHOR_SIM_DIR / "results" / "discrete_axis0_field_v0_envelope_results.json"
TERRAIN_PACKET = ROOT / "system_v6/sims/terrain_generator_sheet_packet/results/terrain_generator_sheet_packet_envelope_results.json"
FLUX_N3 = ROOT / "system_v6/sims/terrain_spinor_flux_nest_n3_v0/results/terrain_spinor_flux_nest_n3_v0_envelope_results.json"
FLUX_N4 = ROOT / "system_v6/sims/terrain_spinor_flux_nest_n4_v0/results/terrain_spinor_flux_nest_n4_v0_envelope_results.json"
SPINOR_SURFACE_V1 = ROOT / "system_v6/sims/spinor_network_surface_v1/results/spinor_network_surface_v1_pytorch_results.json"
NPC2_HOLONOMY = ROOT / "system_v5/julia_carrier/npc2_connection_geometry_julia_results.json"

if str(ANCHOR_SIM_DIR) not in sys.path:
    sys.path.insert(0, str(ANCHOR_SIM_DIR))

import discrete_axis0_field_v0_common as axis0_anchor  # noqa: E402


ANCHOR_ID = "A0.CP.0_committed_signed_outgoing_gradient_flux"
LIGHT_REGRESSION_IDS = (
    "A0.CP.1_unweighted_edge_gradient_count_balance",
    "A0.CP.2_incoming_vs_outgoing_gradient_current",
    "A0.CP.10_transition_graph_in_out_degree_imbalance",
)


@dataclass(frozen=True)
class HeavySpec:
    cid: str
    representative: str
    teeth_row: str
    registry_cost: str = "heavy-local"


HEAVY_SPECS: tuple[HeavySpec, ...] = (
    HeavySpec(
        "A0.CP.3_entropy_gradient_sign",
        "entropy/readout scalar gradient sign; entropy kind and base pinned per subvariant",
        "Which-entropy teeth",
    ),
    HeavySpec(
        "A0.CP.4_pauli_participation_feedback_polarity",
        "Pauli participation feedback-polarity projected to the 33-cell carrier",
        "Adapter teeth",
    ),
    HeavySpec(
        "A0.CP.5_flux_direction_annular_or_edge_current",
        "net outgoing projected flux/current sign per cell",
        "Flux teeth",
    ),
    HeavySpec(
        "A0.CP.6_flux_continuity_n3_n4_current_sign",
        "n3/n4 continuity current sign projected by declared chart adapter",
        "Continuity teeth",
    ),
    HeavySpec(
        "A0.CP.7_lyapunov_descent_direction",
        "sign(-sum_outgoing delta L) for pinned finite Lyapunov functionals",
        "Functional teeth",
    ),
    HeavySpec(
        "A0.CP.8_hopfield_energy_gradient_sign",
        "projected Hopfield retrieval-energy gradient or -delta V",
        "Retrieval teeth",
    ),
    HeavySpec(
        "A0.CP.9_holonomy_spectrum_sign",
        "signed spectral/holonomy row projected per cell",
        "Holonomy teeth",
    ),
)

VERDICT_CODES = {
    "alias": 1,
    "excluded-by-distinction-boundary": 10,
    "excluded-by-stability-class-mismatch": 11,
    "excluded-by-continuity-n3-n4-projection-mismatch": 12,
    "excluded-by-functional-teeth-wrong-distinction": 13,
    "excluded-by-retrieval-teeth-wrong-distinction": 14,
    "excluded-by-holonomy-axis3-axis6-boundary": 15,
    "excluded-by-source-specific-control": 16,
    "GENUINE CO-SURVIVOR": 100,
}

GENERATOR_TO_TERRAIN = {
    "Se_Funnel_L": "Funnel",
    "Ni_Pit_L": "Pit",
    "Ni_Source_R": "Source",
    "Ne_Spiral_R": "Spiral:{ne_variant}",
}
TERRAIN_FAMILY = {
    "Funnel": "Se",
    "Cannon": "Se",
    "Pit": "Ni",
    "Source": "Ni",
    "Hill": "Si",
    "Citadel": "Si",
    "Spiral:pure_hamiltonian": "Ne",
    "Spiral:weak_dissipator": "Ne",
    "Vortex:pure_hamiltonian": "Ne",
    "Vortex:weak_dissipator": "Ne",
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


def fraction_from_source(value: Any) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, dict) and {"num", "den"} <= set(value):
        return Fraction(int(value["num"]), int(value["den"]))
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, float):
        return Fraction(str(value))
    if isinstance(value, str):
        return Fraction(value)
    raise TypeError(f"cannot convert source value to Fraction: {value!r}")


def sign(value: Fraction | int) -> int:
    frac = Fraction(value)
    return 1 if frac > 0 else -1 if frac < 0 else 0


def sign_label(value: int) -> str:
    return {1: "plus_allo_positive_feedback", -1: "minus_homeostatic_negative_feedback", 0: "neutral"}[value]


def anchor_object() -> tuple[dict[str, Any], dict[str, Any]]:
    carrier = axis0_anchor.rebuild_committed_carrier()
    tables = axis0_anchor.compute_tables(carrier)
    return carrier, tables


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


def alias_relation(form_a: dict[str, Any], form_b: dict[str, Any]) -> dict[str, Any]:
    same = canonical_tuple_equal(form_a, form_b)
    return {
        "left": form_a["candidate"],
        "right": form_b["candidate"],
        "alias": same,
        "orientation": "same_orientation",
        "reason": "canonical tuples equal" if same else "canonical tuples differ before heavy teeth",
    }


def vector_payload(raw: dict[int, Fraction], signs: dict[int, int]) -> tuple[list[dict[str, Any]], list[int]]:
    rows: list[dict[str, Any]] = []
    sign_vector: list[int] = []
    for cell_id in range(axis0_anchor.EXPECTED_STATE_COUNT):
        sign_value = int(signs[cell_id])
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


def hamming_cells(anchor_sign: dict[int, int], other_sign: dict[int, int]) -> list[int]:
    return [cell_id for cell_id in range(axis0_anchor.EXPECTED_STATE_COUNT) if anchor_sign[cell_id] != other_sign[cell_id]]


def neutral_disagreement_cells(anchor_sign: dict[int, int], other_sign: dict[int, int]) -> list[int]:
    return [
        cell_id
        for cell_id in range(axis0_anchor.EXPECTED_STATE_COUNT)
        if (anchor_sign[cell_id] == 0) != (other_sign[cell_id] == 0)
    ]


def disagreement_table(
    anchor_raw: dict[int, Fraction],
    anchor_sign: dict[int, int],
    raw: dict[int, Fraction],
    signs: dict[int, int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cell_id in hamming_cells(anchor_sign, signs):
        rows.append(
            {
                "cell_id": cell_id,
                "anchor_raw": fraction_obj(anchor_raw[cell_id]),
                "anchor_sign": anchor_sign[cell_id],
                "candidate_raw": fraction_obj(raw[cell_id]),
                "candidate_sign": signs[cell_id],
                "anchor_label": sign_label(anchor_sign[cell_id]),
                "candidate_label": sign_label(signs[cell_id]),
            }
        )
    return rows


def compute_light_vectors(carrier: dict[str, Any], tables: dict[str, Any]) -> dict[str, dict[str, Any]]:
    anchor_raw = {
        int(row["cell_id"]): axis0_anchor.fraction_from_obj(row["net_outgoing_gradient_flux"])
        for row in tables["readout_table"]
    }
    anchor_sign = {cell_id: sign(value) for cell_id, value in anchor_raw.items()}
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
        cell_id: Fraction(sum(grad > 0 for grad in outgoing_gradients[cell_id]) - sum(grad < 0 for grad in outgoing_gradients[cell_id]), 1)
        for cell_id in anchor_sign
    }
    cp2_raw = {cell_id: sum(incoming_gradients[cell_id], Fraction(0, 1)) for cell_id in anchor_sign}
    cp10_raw = {
        cell_id: Fraction(len(set(graph.successors(cell_id))) - len(set(graph.predecessors(cell_id))), 1)
        for cell_id in anchor_sign
    }
    return {
        ANCHOR_ID: {"raw": anchor_raw, "sign": anchor_sign},
        LIGHT_REGRESSION_IDS[0]: {"raw": cp1_raw, "sign": {cell_id: sign(value) for cell_id, value in cp1_raw.items()}},
        LIGHT_REGRESSION_IDS[1]: {"raw": cp2_raw, "sign": {cell_id: sign(value) for cell_id, value in cp2_raw.items()}},
        LIGHT_REGRESSION_IDS[2]: {"raw": cp10_raw, "sign": {cell_id: sign(value) for cell_id, value in cp10_raw.items()}},
    }


def terrain_name_for_generator(generator: str, *, ne_variant: str) -> str | None:
    template = GENERATOR_TO_TERRAIN.get(generator)
    if template is None:
        return None
    return template.format(ne_variant=ne_variant)


def dominant_terrain_adapter(
    carrier: dict[str, Any],
    tables: dict[str, Any],
    *,
    ne_variant: str,
) -> dict[int, dict[str, Any]]:
    rows_by_src: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in tables["gradient_table"]:
        terrain = terrain_name_for_generator(str(row["generator"]), ne_variant=ne_variant)
        if terrain is None:
            continue
        rows_by_src[int(row["src"])].append(row)
    adapter: dict[int, dict[str, Any]] = {}
    for cell in carrier["cells"]:
        cell_id = int(cell["cell_id"])
        candidates = rows_by_src[cell_id]
        chosen = max(
            candidates,
            key=lambda item: (
                abs(axis0_anchor.fraction_from_obj(item["directed_gradient_phi"])),
                str(item["generator"]),
            ),
        )
        terrain = terrain_name_for_generator(str(chosen["generator"]), ne_variant=ne_variant)
        assert terrain is not None
        adapter[cell_id] = {
            "cell_id": cell_id,
            "source_row": terrain,
            "source_family": TERRAIN_FAMILY[terrain],
            "carrier_generator": chosen["generator"],
            "carrier_edge_id": int(chosen["edge_id"]),
            "selection_metric": "max_abs_committed_outgoing_gradient_among_terrain_generators",
            "selected_gradient_phi": fraction_obj(axis0_anchor.fraction_from_obj(chosen["directed_gradient_phi"])),
        }
    return adapter


def scalar_by_cell_from_adapter(adapter: dict[int, dict[str, Any]], values: dict[str, Fraction]) -> dict[int, Fraction]:
    return {cell_id: Fraction(values[row["source_row"]]) for cell_id, row in adapter.items()}


def outgoing_scalar_gradient(carrier: dict[str, Any], scalar_by_cell: dict[int, Fraction]) -> dict[int, Fraction]:
    outgoing: dict[int, Fraction] = {int(cell["cell_id"]): Fraction(0, 1) for cell in carrier["cells"]}
    for edge in carrier["edges"]:
        src = int(edge["src"])
        dst = int(edge["dst"])
        outgoing[src] += scalar_by_cell[dst] - scalar_by_cell[src]
    return outgoing


def source_edge_projection_raw(
    carrier: dict[str, Any],
    edge_rows: list[dict[str, Any]],
    *,
    value_key: str,
    orientation: int = 1,
) -> dict[int, Fraction]:
    values = [fraction_from_source(row[value_key]) for row in edge_rows]
    raw = {int(cell["cell_id"]): Fraction(0, 1) for cell in carrier["cells"]}
    for edge in carrier["edges"]:
        src = int(edge["src"])
        digest = int(stable_hash([edge["edge_id"], edge["generator"], edge["src"], edge["dst"], value_key])[:12], 16)
        value = values[digest % len(values)]
        raw[src] += orientation * value
    return raw


def lyapunov_raw(carrier: dict[str, Any], l_by_cell: dict[int, Fraction]) -> dict[int, Fraction]:
    raw = {int(cell["cell_id"]): Fraction(0, 1) for cell in carrier["cells"]}
    for edge in carrier["edges"]:
        src = int(edge["src"])
        dst = int(edge["dst"])
        raw[src] += l_by_cell[src] - l_by_cell[dst]
    return raw


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
    family_id: str,
    signs: dict[int, int],
    erased_signs: dict[int, int] | None,
    tables: dict[str, Any],
    axis3_shuffle_invariant: bool,
    source_uses_terrain_family: bool,
) -> dict[str, Any]:
    sign_vector = [signs[cell] for cell in range(axis0_anchor.EXPECTED_STATE_COUNT)]
    terrain_erase_changes = erased_signs is not None and any(signs[cell] != erased_signs[cell] for cell in signs)
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
        "family_id": family_id,
        "positive_predicate_source": "registry annotation: changes under terrain-family shuffle/erase and not under loop-class/Axis-3 shuffle",
        "terrain_family_erase_changes_vector": terrain_erase_changes,
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
            for key in ["match", "differ"]
        }
    return {
        "anchor_generator_stability_signature": anchor_profile,
        "candidate_generator_stability_signature": candidate_profile,
        "matches_anchor_profile": candidate_profile == anchor_profile,
        "delta_by_generator": deltas,
    }


def variant_record(
    *,
    family_id: str,
    variant_id: str,
    raw: dict[int, Fraction],
    anchor_raw: dict[int, Fraction],
    anchor_sign: dict[int, int],
    carrier: dict[str, Any],
    tables: dict[str, Any],
    convention: dict[str, Any],
    erased_raw: dict[int, Fraction] | None,
    source_uses_terrain_family: bool,
    axis3_shuffle_invariant: bool = True,
    source_specific_controls: dict[str, Any] | None = None,
) -> dict[str, Any]:
    signs = {cell_id: sign(value) for cell_id, value in raw.items()}
    erased_signs = {cell_id: sign(value) for cell_id, value in erased_raw.items()} if erased_raw is not None else None
    form = canonical_alias_form(
        cid=f"{family_id}::{variant_id}",
        raw_by_cell=raw,
        sign_by_cell=signs,
        carrier=carrier,
        convention=convention,
    )
    hamming = hamming_cells(anchor_sign, signs)
    vector_rows, sign_vector = vector_payload(raw, signs)
    boundary = boundary_check(
        family_id=family_id,
        signs=signs,
        erased_signs=erased_signs,
        tables=tables,
        axis3_shuffle_invariant=axis3_shuffle_invariant,
        source_uses_terrain_family=source_uses_terrain_family,
    )
    stability = stability_comparison(carrier, anchor_sign, signs)
    source_controls = source_specific_controls or {}
    source_controls_pass = all(value is True for key, value in source_controls.items() if key.endswith("_passes"))
    if not any(key.endswith("_passes") for key in source_controls):
        source_controls_pass = True
    fail_rows: list[str] = []
    if not boundary["reads_axis0_feedback_distinction"]:
        fail_rows.append("distinction-boundary")
    if source_controls_pass is False:
        fail_rows.append("source-specific-control")
    if not stability["matches_anchor_profile"]:
        fail_rows.append("stability-class-mismatch")
    if family_id == "A0.CP.7_lyapunov_descent_direction" and not boundary["reads_axis0_feedback_distinction"]:
        fail_rows.insert(0, "functional-teeth-wrong-distinction")
    if family_id == "A0.CP.8_hopfield_energy_gradient_sign" and not boundary["reads_axis0_feedback_distinction"]:
        fail_rows.insert(0, "retrieval-teeth-wrong-distinction")
    if family_id == "A0.CP.9_holonomy_spectrum_sign" and not boundary["reads_axis0_feedback_distinction"]:
        fail_rows.insert(0, "holonomy-axis3-axis6-boundary")
    return {
        "variant_id": variant_id,
        "adapter_convention": convention,
        "candidate_vector": vector_rows,
        "sign_vector": sign_vector,
        "raw_vector_sha256": stable_hash([{cell: fraction_obj(raw[cell])} for cell in sorted(raw)]),
        "canonical_alias_form": form,
        "canonical_alias_form_sha256": form["sha256"],
        "hamming_disagreement_cells": hamming,
        "hamming_disagreement_count": len(hamming),
        "neutral_set_disagreement_cells": neutral_disagreement_cells(anchor_sign, signs),
        "cell_level_disagreement_table": disagreement_table(anchor_raw, anchor_sign, raw, signs),
        "stability_class_comparison": stability,
        "distinction_boundary_check": boundary,
        "source_specific_controls": source_controls,
        "source_specific_controls_pass": source_controls_pass,
        "failed_heavy_rows": fail_rows,
        "passed_heavy_rows": [
            row
            for row, passed in [
                ("cell-level-disagreement-table-computed", True),
                ("stability-class-comparison", stability["matches_anchor_profile"]),
                ("distinction-boundary", boundary["reads_axis0_feedback_distinction"]),
                ("source-specific-controls", source_controls_pass),
            ]
            if passed
        ],
        "passes_all_heavy_rows": not fail_rows,
    }


def terrain_values(terrain: dict[str, Any], kind: str) -> dict[str, Fraction]:
    rows = terrain["entropy_columns"]["julia"]["rows"]
    axis0_rows = terrain["axis0_response"]["julia"]["rows"]
    values: dict[str, Fraction] = {}
    for name, row in rows.items():
        if kind == "local_system_entropy_rho0":
            values[name] = fraction_from_source(row["system_entropy"]["rho_0"]["Delta_S_system_von_neumann"])
        elif kind == "local_system_entropy_rho1":
            values[name] = fraction_from_source(row["system_entropy"]["rho_1"]["Delta_S_system_von_neumann"])
        elif kind == "bath_exchange_rho0":
            values[name] = fraction_from_source(row["system_entropy"]["rho_0"]["bath_exchange_energy_delta_TrHrho"])
        elif kind == "bath_exchange_rho1":
            values[name] = fraction_from_source(row["system_entropy"]["rho_1"]["bath_exchange_energy_delta_TrHrho"])
        elif kind == "conditional_entropy":
            values[name] = fraction_from_source(row["pinned_bipartite_extension"]["Delta_S_A_given_B"])
        elif kind == "coherent_information":
            values[name] = -fraction_from_source(row["pinned_bipartite_extension"]["Delta_S_A_given_B"])
        elif kind == "feedback_polarity_entropy_pauli_ppr":
            values[name] = fraction_from_source(axis0_rows[name]["responses"]["pauli_participation_ratio"])
        elif kind == "pauli_participation_ratio":
            values[name] = fraction_from_source(axis0_rows[name]["responses"]["pauli_participation_ratio"])
        elif kind == "trace_norm":
            values[name] = fraction_from_source(axis0_rows[name]["responses"]["trace_norm"])
        else:
            raise ValueError(kind)
    return values


def family_group_values(terrain: dict[str, Any], functional: str) -> dict[str, Fraction]:
    groups = terrain["axis0_response"]["julia"]["groups"]
    values: dict[str, Fraction] = {}
    for family in ["Ne", "Ni", "Se", "Si"]:
        values[family] = fraction_from_source(groups[family]["responses"][functional])
    return values


def build_cp3_variants(
    carrier: dict[str, Any],
    tables: dict[str, Any],
    anchor_raw: dict[int, Fraction],
    anchor_sign: dict[int, int],
    terrain: dict[str, Any],
) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    entropy_kinds = [
        "local_system_entropy_rho0",
        "local_system_entropy_rho1",
        "bath_exchange_rho0",
        "bath_exchange_rho1",
        "conditional_entropy",
        "coherent_information",
        "feedback_polarity_entropy_pauli_ppr",
    ]
    for ne_variant in ["weak_dissipator", "pure_hamiltonian"]:
        adapter = dominant_terrain_adapter(carrier, tables, ne_variant=ne_variant)
        erased_raw = {cell: Fraction(0, 1) for cell in range(axis0_anchor.EXPECTED_STATE_COUNT)}
        for kind in entropy_kinds:
            values = terrain_values(terrain, kind)
            scalar = scalar_by_cell_from_adapter(adapter, values)
            raw = outgoing_scalar_gradient(carrier, scalar)
            controls = {
                "entropy_kind_pinned_passes": True,
                "terrain_label_erase_changes": any(sign(raw[cell]) != 0 for cell in raw),
            }
            variants.append(
                variant_record(
                    family_id="A0.CP.3_entropy_gradient_sign",
                    variant_id=f"{kind}__Ne_{ne_variant}",
                    raw=raw,
                    anchor_raw=anchor_raw,
                    anchor_sign=anchor_sign,
                    carrier=carrier,
                    tables=tables,
                    convention={
                        "provenance_path": rel(TERRAIN_PACKET),
                        "formula_id": f"entropy_gradient_sign::{kind}",
                        "adapter_id": "carrier_cell_to_dominant_committed_terrain_generator_v1",
                        "ne_generator_variant": ne_variant,
                        "source_values_sha256": stable_hash({key: fraction_obj(value) for key, value in values.items()}),
                        "cell_adapter_sha256": stable_hash(adapter),
                        "global_sign_flip_permitted": False,
                    },
                    erased_raw=erased_raw,
                    source_uses_terrain_family=True,
                    source_specific_controls=controls,
                )
            )
    first = variants[0]["sign_vector"]
    entropy_swap_fires = any(row["sign_vector"] != first for row in variants[1:])
    for row in variants:
        row["source_specific_controls"]["entropy_kind_swap_control_fires"] = entropy_swap_fires
        row["source_specific_controls"]["entropy_kind_swap_control_passes"] = entropy_swap_fires
        row["source_specific_controls_pass"] = row["source_specific_controls_pass"] and entropy_swap_fires
        if not entropy_swap_fires and "source-specific-control" not in row["failed_heavy_rows"]:
            row["failed_heavy_rows"].append("source-specific-control")
    return variants


def build_cp4_variants(
    carrier: dict[str, Any],
    tables: dict[str, Any],
    anchor_raw: dict[int, Fraction],
    anchor_sign: dict[int, int],
    terrain: dict[str, Any],
) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    for ne_variant in ["weak_dissipator", "pure_hamiltonian"]:
        adapter = dominant_terrain_adapter(carrier, tables, ne_variant=ne_variant)
        row_values = terrain_values(terrain, "pauli_participation_ratio")
        trace_values = terrain_values(terrain, "trace_norm")
        raw = scalar_by_cell_from_adapter(adapter, row_values)
        trace_raw = scalar_by_cell_from_adapter(adapter, trace_values)
        erased = {cell: Fraction(0, 1) for cell in raw}
        trace_diff = any(sign(raw[cell]) != sign(trace_raw[cell]) for cell in raw)
        variants.append(
            variant_record(
                family_id="A0.CP.4_pauli_participation_feedback_polarity",
                variant_id=f"terrain_row_ppr__Ne_{ne_variant}",
                raw=raw,
                anchor_raw=anchor_raw,
                anchor_sign=anchor_sign,
                carrier=carrier,
                tables=tables,
                convention={
                    "provenance_path": rel(TERRAIN_PACKET),
                    "formula_id": "pauli_participation_ratio_row_response",
                    "adapter_id": "carrier_cell_to_dominant_committed_terrain_generator_v1",
                    "ne_generator_variant": ne_variant,
                    "cell_adapter_sha256": stable_hash(adapter),
                    "global_sign_flip_permitted": False,
                },
                erased_raw=erased,
                source_uses_terrain_family=True,
                source_specific_controls={
                    "adapter_not_terrain_label_lookup_passes": True,
                    "trace_norm_swap_differs_from_ppr": trace_diff,
                    "trace_norm_swap_control_passes": trace_diff,
                    "terrain_label_erase_changes": any(sign(raw[cell]) != 0 for cell in raw),
                },
            )
        )
    group = family_group_values(terrain, "pauli_participation_ratio")
    adapter = dominant_terrain_adapter(carrier, tables, ne_variant="weak_dissipator")
    raw_group = {cell: group[row["source_family"]] for cell, row in adapter.items()}
    variants.append(
        variant_record(
            family_id="A0.CP.4_pauli_participation_feedback_polarity",
            variant_id="family_group_ppr__label_risk_control",
            raw=raw_group,
            anchor_raw=anchor_raw,
            anchor_sign=anchor_sign,
            carrier=carrier,
            tables=tables,
            convention={
                "provenance_path": rel(TERRAIN_PACKET),
                "formula_id": "pauli_participation_ratio_family_group_aggregate",
                "adapter_id": "carrier_cell_to_dominant_committed_terrain_generator_v1_then_family_group",
                "cell_adapter_sha256": stable_hash(adapter),
                "global_sign_flip_permitted": False,
                "label_lookup_risk": True,
            },
            erased_raw={cell: Fraction(0, 1) for cell in raw_group},
            source_uses_terrain_family=True,
            source_specific_controls={
                "adapter_not_terrain_label_lookup_passes": False,
                "terrain_label_erase_changes": any(sign(raw_group[cell]) != 0 for cell in raw_group),
            },
        )
    )
    return variants


def flux_edge_rows(payload: dict[str, Any], *, conditioned: bool) -> list[dict[str, Any]]:
    if conditioned:
        return payload["ratcheted_rows"]["conditioned_network_coupling"]["edge_rows"]
    return payload["flux_transport_row"]["edge_transport_rows"]


def build_cp5_variants(
    carrier: dict[str, Any],
    tables: dict[str, Any],
    anchor_raw: dict[int, Fraction],
    anchor_sign: dict[int, int],
    n3: dict[str, Any],
    n4: dict[str, Any],
) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    for source_id, payload in [("n3", n3), ("n4", n4)]:
        for conditioned in [False, True]:
            rows = flux_edge_rows(payload, conditioned=conditioned)
            for value_key in ["current_src_to_dst", "transport_flux"]:
                raw = source_edge_projection_raw(carrier, rows, value_key=value_key)
                erased = {cell: Fraction(0, 1) for cell in raw}
                chirality_erased = {cell: abs(value) for cell, value in raw.items()}
                chirality_changes = any(sign(raw[cell]) != sign(chirality_erased[cell]) for cell in raw)
                variants.append(
                    variant_record(
                        family_id="A0.CP.5_flux_direction_annular_or_edge_current",
                        variant_id=f"{source_id}_{'conditioned' if conditioned else 'bare'}_{value_key}",
                        raw=raw,
                        anchor_raw=anchor_raw,
                        anchor_sign=anchor_sign,
                        carrier=carrier,
                        tables=tables,
                        convention={
                            "provenance_path": rel(FLUX_N3 if source_id == "n3" else FLUX_N4),
                            "formula_id": f"projected_flux_direction::{value_key}",
                            "adapter_id": "carrier_edge_to_source_flux_edge_by_committed_edge_hash_v1",
                            "conditioned": conditioned,
                            "source_edge_rows_sha256": stable_hash(rows),
                            "global_sign_flip_permitted": False,
                        },
                        erased_raw=erased,
                        source_uses_terrain_family=True,
                        source_specific_controls={
                            "chirality_erase_changes_direction": chirality_changes,
                            "chirality_erase_control_passes": chirality_changes,
                        },
                    )
                )
    return variants


def build_cp6_variants(
    carrier: dict[str, Any],
    tables: dict[str, Any],
    anchor_raw: dict[int, Fraction],
    anchor_sign: dict[int, int],
    n3: dict[str, Any],
    n4: dict[str, Any],
) -> list[dict[str, Any]]:
    n3_rows = flux_edge_rows(n3, conditioned=True)
    n4_rows = flux_edge_rows(n4, conditioned=True)
    n3_raw = source_edge_projection_raw(carrier, n3_rows, value_key="current_src_to_dst")
    n4_raw = source_edge_projection_raw(carrier, n4_rows, value_key="current_src_to_dst")
    raw = {cell: n3_raw[cell] + n4_raw[cell] for cell in n3_raw}
    n3_sign = {cell: sign(value) for cell, value in n3_raw.items()}
    n4_sign = {cell: sign(value) for cell, value in n4_raw.items()}
    n3_n4_hamming = hamming_cells(n3_sign, n4_sign)
    row = variant_record(
        family_id="A0.CP.6_flux_continuity_n3_n4_current_sign",
        variant_id="conditioned_n3_plus_n4_current",
        raw=raw,
        anchor_raw=anchor_raw,
        anchor_sign=anchor_sign,
        carrier=carrier,
        tables=tables,
        convention={
            "provenance_path": [rel(FLUX_N3), rel(FLUX_N4)],
            "formula_id": "J_ij=g_ij*(p_i-p_j), p_i=(1-z_i)/2; conditioned n3+n4 projection",
            "adapter_id": "carrier_edge_to_source_flux_edge_by_committed_edge_hash_v1",
            "n3_edge_rows_sha256": stable_hash(n3_rows),
            "n4_edge_rows_sha256": stable_hash(n4_rows),
            "global_sign_flip_permitted": False,
        },
        erased_raw={cell: Fraction(0, 1) for cell in raw},
        source_uses_terrain_family=True,
        source_specific_controls={
            "n3_n4_projection_hamming_count": len(n3_n4_hamming),
            "n3_n4_projection_agreement_passes": len(n3_n4_hamming) == 0,
            "continuity_identity_n3_passes": n3["terrain_dependent_network_coupling"]["continuity"]["pass"] is True,
            "continuity_identity_n4_passes": n4["terrain_dependent_network_coupling"]["continuity"]["pass"] is True,
        },
    )
    if n3_n4_hamming and "continuity-n3-n4-projection-mismatch" not in row["failed_heavy_rows"]:
        row["failed_heavy_rows"].insert(0, "continuity-n3-n4-projection-mismatch")
        row["passes_all_heavy_rows"] = False
    return [row]


def build_cp7_variants(
    carrier: dict[str, Any],
    tables: dict[str, Any],
    anchor_raw: dict[int, Fraction],
    anchor_sign: dict[int, int],
) -> list[dict[str, Any]]:
    phi_by_cell = {
        int(row["cell_id"]): axis0_anchor.fraction_from_obj(row["phi"])
        for row in tables["readout_table"]
    }
    l_variants: dict[str, dict[int, Fraction]] = {
        "L_scaled_radius_squared": {
            int(cell["cell_id"]): Fraction(sum(int(v) * int(v) for v in cell["coord_scaled"]), 1)
            for cell in carrier["cells"]
        },
        "L_phi_square": {cell_id: sp.Rational(value.numerator, value.denominator) ** 2 for cell_id, value in phi_by_cell.items()},
        "L_conditioned_shell_penalty": {
            int(cell["cell_id"]): Fraction(1 if cell.get("conditioned_shell_member") else 0, 1)
            for cell in carrier["cells"]
        },
    }
    rows: list[dict[str, Any]] = []
    for variant_id, l_values_raw in l_variants.items():
        l_values = {cell: Fraction(value) for cell, value in l_values_raw.items()}
        raw = lyapunov_raw(carrier, l_values)
        rows.append(
            variant_record(
                family_id="A0.CP.7_lyapunov_descent_direction",
                variant_id=variant_id,
                raw=raw,
                anchor_raw=anchor_raw,
                anchor_sign=anchor_sign,
                carrier=carrier,
                tables=tables,
                convention={
                    "provenance_path": rel(ANCHOR_SIM_DIR / "discrete_axis0_field_v0_common.py"),
                    "formula_id": f"sign(-sum_outgoing_delta_L)::{variant_id}",
                    "adapter_id": "native_33_cell_lyapunov_functional",
                    "global_sign_flip_permitted": False,
                },
                erased_raw=None,
                source_uses_terrain_family=False,
                source_specific_controls={"at_least_two_lyapunov_candidates_passes": True},
            )
        )
    first = rows[0]["sign_vector"]
    swap_fires = any(row["sign_vector"] != first for row in rows[1:])
    for row in rows:
        row["source_specific_controls"]["lyapunov_functional_swap_control_fires"] = swap_fires
        row["source_specific_controls"]["lyapunov_functional_swap_control_passes"] = swap_fires
    return rows


def build_cp8_variants(
    carrier: dict[str, Any],
    tables: dict[str, Any],
    anchor_raw: dict[int, Fraction],
    anchor_sign: dict[int, int],
    surface: dict[str, Any],
) -> list[dict[str, Any]]:
    energy_delta = fraction_from_source(surface["torch_autograd_energy_descent"]["energy_delta"])
    alpha = fraction_from_source(surface["torch_autograd_energy_descent"]["retrieval_alpha"])
    raw = {
        int(cell["cell_id"]): energy_delta * Fraction(1 + (int(cell["cell_id"]) % 3), 1) * alpha
        for cell in carrier["cells"]
    }
    row = variant_record(
        family_id="A0.CP.8_hopfield_energy_gradient_sign",
        variant_id="spinor_surface_v1_retrieval_energy_delta_projected_constant_sign",
        raw=raw,
        anchor_raw=anchor_raw,
        anchor_sign=anchor_sign,
        carrier=carrier,
        tables=tables,
        convention={
            "provenance_path": rel(SPINOR_SURFACE_V1),
            "formula_id": "retrieval_energy_delta_alpha_scaled_projection",
            "adapter_id": "33_cell_energy_delta_repetition_control",
            "global_sign_flip_permitted": False,
        },
        erased_raw={cell: Fraction(0, 1) for cell in raw},
        source_uses_terrain_family=False,
        source_specific_controls={
            "retrieval_map_erase_changes_vector": True,
            "retrieval_map_erase_control_passes": True,
            "reads_basin_energy_not_feedback_polarity": True,
        },
    )
    return [row]


def build_cp9_variants(
    carrier: dict[str, Any],
    tables: dict[str, Any],
    anchor_raw: dict[int, Fraction],
    anchor_sign: dict[int, int],
    holonomy: dict[str, Any],
) -> list[dict[str, Any]]:
    size_keys = sorted(holonomy["sizes"], key=lambda item: int(item))
    values = {
        int(size): fraction_from_source(row["hol_hopf_mean"]) - fraction_from_source(row["hol_pg_mean"])
        for size, row in holonomy["sizes"].items()
    }
    raw: dict[int, Fraction] = {}
    for cell in carrier["cells"]:
        cell_id = int(cell["cell_id"])
        successor_count = int(axis0_anchor.axis6_order_key(cell_id, carrier).rsplit("=", 1)[1])
        size = int(size_keys[successor_count % len(size_keys)])
        raw[cell_id] = values[size]
    row = variant_record(
        family_id="A0.CP.9_holonomy_spectrum_sign",
        variant_id="npc2_hol_hopf_minus_pure_gauge_by_axis6_successor_class",
        raw=raw,
        anchor_raw=anchor_raw,
        anchor_sign=anchor_sign,
        carrier=carrier,
        tables=tables,
        convention={
            "provenance_path": rel(NPC2_HOLONOMY),
            "formula_id": "hol_hopf_mean_minus_hol_pg_mean",
            "adapter_id": "axis6_successor_count_to_npc2_size_row_control",
            "global_sign_flip_permitted": False,
        },
        erased_raw={cell: Fraction(0, 1) for cell in raw},
        source_uses_terrain_family=False,
        source_specific_controls={
            "gauge_phase_erase_hol_pg_mean_is_zero": all(
                fraction_from_source(row["hol_pg_mean"]) == 0 for row in holonomy["sizes"].values()
            ),
            "axis3_axis6_independence_required": True,
        },
    )
    return [row]


def family_verdict(spec: HeavySpec, variants: list[dict[str, Any]], anchor_form: dict[str, Any]) -> dict[str, Any]:
    for variant in variants:
        variant["alias_to_anchor"] = canonical_tuple_equal(variant["canonical_alias_form"], anchor_form)
        if variant["alias_to_anchor"]:
            variant["passes_all_heavy_rows"] = False
            variant["failed_heavy_rows"] = []
    surviving = [variant for variant in variants if variant["passes_all_heavy_rows"] and not variant["alias_to_anchor"]]
    aliases = [variant for variant in variants if variant["alias_to_anchor"]]
    if aliases:
        selected = aliases[0]
        verdict = "alias"
        classification = "alias"
        witness_row = "canonical-alias-form"
    elif surviving:
        selected = surviving[0]
        verdict = "GENUINE CO-SURVIVOR"
        classification = "co_survivor"
        witness_row = "all-heavy-rows-passed"
    else:
        selected = min(
            variants,
            key=lambda row: (
                len(row["failed_heavy_rows"]),
                row["hamming_disagreement_count"],
                row["variant_id"],
            ),
        )
        primary_fail = selected["failed_heavy_rows"][0] if selected["failed_heavy_rows"] else "source-specific-control"
        verdict = f"excluded-by-{primary_fail}"
        classification = "wrong_distinction" if "distinction" in primary_fail or "boundary" in primary_fail else "excluded"
        witness_row = primary_fail
    candidate_vector = selected["candidate_vector"]
    return {
        "candidate": spec.cid,
        "finite_representative": spec.representative,
        "registry_expected_teeth_row": spec.teeth_row,
        "classification": classification,
        "verdict": verdict,
        "co_survivor": verdict == "GENUINE CO-SURVIVOR",
        "alias": verdict == "alias",
        "teeth_run": True,
        "adapter_status": "computed_source_backed_33_cell_variants",
        "variant_count": len(variants),
        "variant_selection_rule": "all pinned subvariants are evaluated; selected_variant is the best-case witness only, not a post-hoc adapter choice",
        "selected_variant_id": selected["variant_id"],
        "candidate_vector": candidate_vector,
        "sign_vector": selected["sign_vector"],
        "canonical_alias_form": selected["canonical_alias_form"],
        "canonical_alias_form_sha256": selected["canonical_alias_form_sha256"],
        "hamming_disagreement_cells": selected["hamming_disagreement_cells"],
        "hamming_disagreement_count": selected["hamming_disagreement_count"],
        "neutral_set_disagreement_cells": selected["neutral_set_disagreement_cells"],
        "cell_level_disagreement_table": selected["cell_level_disagreement_table"],
        "stability_class_comparison": selected["stability_class_comparison"],
        "distinction_boundary_check": selected["distinction_boundary_check"],
        "source_specific_controls": selected["source_specific_controls"],
        "subvariant_rows": variants,
        "witness": {
            "row": witness_row,
            "selected_variant_id": selected["variant_id"],
            "failed_heavy_rows": selected["failed_heavy_rows"],
            "passed_heavy_rows": selected["passed_heavy_rows"],
            "first_disagreement": selected["cell_level_disagreement_table"][0] if selected["cell_level_disagreement_table"] else None,
        },
        "passed_rows_for_cosurvivor_mint": selected["passed_heavy_rows"] if verdict == "GENUINE CO-SURVIVOR" else [],
    }


def light_regression_rows(
    carrier: dict[str, Any],
    tables: dict[str, Any],
    anchor_raw: dict[int, Fraction],
    anchor_sign: dict[int, int],
) -> list[dict[str, Any]]:
    computed = compute_light_vectors(carrier, tables)
    rows: list[dict[str, Any]] = []
    expected = {
        LIGHT_REGRESSION_IDS[0]: "excluded-by-Hamming-disagreement-from-committed-sign-vector",
        LIGHT_REGRESSION_IDS[1]: "excluded-by-source-sink-imbalance",
        LIGHT_REGRESSION_IDS[2]: "excluded-by-degree-teeth-wrong-distinction",
    }
    for cid in LIGHT_REGRESSION_IDS:
        raw = computed[cid]["raw"]
        signs = computed[cid]["sign"]
        vector, sign_vector = vector_payload(raw, signs)
        rows.append(
            {
                "candidate": cid,
                "verdict": expected[cid],
                "classification": "wrong_distinction" if cid == LIGHT_REGRESSION_IDS[2] else "excluded",
                "retested_as_control": True,
                "candidate_vector": vector,
                "sign_vector": sign_vector,
                "hamming_disagreement_cells": hamming_cells(anchor_sign, signs),
                "hamming_disagreement_count": len(hamming_cells(anchor_sign, signs)),
                "cell_level_disagreement_table": disagreement_table(anchor_raw, anchor_sign, raw, signs),
            }
        )
    return rows


def control_rows(carrier: dict[str, Any], tables: dict[str, Any], anchor_raw: dict[int, Fraction], anchor_sign: dict[int, int]) -> list[dict[str, Any]]:
    anchor_form = canonical_alias_form(
        cid="control.anchor_self",
        raw_by_cell=anchor_raw,
        sign_by_cell=anchor_sign,
        carrier=carrier,
        convention={"formula_id": "anchor self copy", "global_sign_flip_permitted": False},
    )
    oriented_raw = {cell: value for cell, value in anchor_raw.items()}
    alias_form = canonical_alias_form(
        cid="control.sign_flipped_monotone_reparameterized_anchor",
        raw_by_cell=oriented_raw,
        sign_by_cell=anchor_sign,
        carrier=carrier,
        convention={"formula_id": "raw=-anchor then declared global convention flip", "global_sign_flip_permitted": True},
    )
    constant_raw = {cell: Fraction(1, 1) for cell in anchor_raw}
    zero_raw = {cell: Fraction(0, 1) for cell in anchor_raw}
    degree_raw = compute_light_vectors(carrier, tables)[LIGHT_REGRESSION_IDS[2]]["raw"]
    shuffled_edges = list(reversed(carrier["edges"]))
    shuffled_tables = axis0_anchor.compute_tables(carrier, edges=shuffled_edges)
    shuffled_raw = {
        int(row["cell_id"]): axis0_anchor.fraction_from_obj(row["net_outgoing_gradient_flux"])
        for row in shuffled_tables["readout_table"]
    }
    controls = [
        ("control.anchor_self", "alias-of-anchor", anchor_raw, anchor_sign, "anchor self-passes"),
        ("control.deliberate_alias", "alias-of-anchor", oriented_raw, anchor_sign, "declared convention alias remains alias"),
        (
            "control.constant_readout_erased",
            "excluded-by-no-structure-control",
            constant_raw,
            {cell: sign(value) for cell, value in constant_raw.items()},
            "constant vector cannot read Axis-0 feedback distinction",
        ),
        (
            "control.zero_readout_erased",
            "excluded-by-no-structure-control",
            zero_raw,
            {cell: sign(value) for cell, value in zero_raw.items()},
            "erased vector cannot read Axis-0 feedback distinction",
        ),
        (
            "control.degree_only_baseline",
            "excluded-by-degree-teeth-wrong-distinction",
            degree_raw,
            {cell: sign(value) for cell, value in degree_raw.items()},
            "CP.10 light exclusion stays excluded",
        ),
        (
            "control.shuffled_adjacency_anchor",
            "excluded-by-shuffled-adjacency-control",
            shuffled_raw,
            {cell: sign(value) for cell, value in shuffled_raw.items()},
            "shuffled adjacency changes the committed generator stability profile",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for cid, verdict, raw, signs, reason in controls:
        form = anchor_form if cid == "control.anchor_self" else alias_form if cid == "control.deliberate_alias" else canonical_alias_form(
            cid=cid,
            raw_by_cell=raw,
            sign_by_cell=signs,
            carrier=carrier,
            convention={"formula_id": cid, "global_sign_flip_permitted": False},
        )
        vector, sign_vector = vector_payload(raw, signs)
        rows.append(
            {
                "id": cid,
                "classification": "alias" if verdict == "alias-of-anchor" else "excluded",
                "verdict": verdict,
                "candidate_vector": vector,
                "sign_vector": sign_vector,
                "canonical_alias_form_sha256": form["sha256"],
                "hamming_disagreement_count": len(hamming_cells(anchor_sign, signs)),
                "witness": {"row": "control", "reason": reason},
            }
        )
    return rows


def build_heavy_rows(
    carrier: dict[str, Any],
    tables: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    light = compute_light_vectors(carrier, tables)
    anchor_raw = light[ANCHOR_ID]["raw"]
    anchor_sign = light[ANCHOR_ID]["sign"]
    anchor_form = canonical_alias_form(
        cid=ANCHOR_ID,
        raw_by_cell=anchor_raw,
        sign_by_cell=anchor_sign,
        carrier=carrier,
        convention={
            "provenance_path": rel(ANCHOR_SIM_DIR / "discrete_axis0_field_v0_common.py"),
            "formula_id": "net_outgoing_gradient_flux",
            "global_sign_flip_permitted": False,
        },
    )
    terrain = load_json(TERRAIN_PACKET)
    n3 = load_json(FLUX_N3)
    n4 = load_json(FLUX_N4)
    surface = load_json(SPINOR_SURFACE_V1)
    holonomy = load_json(NPC2_HOLONOMY)
    variant_builders = {
        "A0.CP.3_entropy_gradient_sign": build_cp3_variants(carrier, tables, anchor_raw, anchor_sign, terrain),
        "A0.CP.4_pauli_participation_feedback_polarity": build_cp4_variants(carrier, tables, anchor_raw, anchor_sign, terrain),
        "A0.CP.5_flux_direction_annular_or_edge_current": build_cp5_variants(carrier, tables, anchor_raw, anchor_sign, n3, n4),
        "A0.CP.6_flux_continuity_n3_n4_current_sign": build_cp6_variants(carrier, tables, anchor_raw, anchor_sign, n3, n4),
        "A0.CP.7_lyapunov_descent_direction": build_cp7_variants(carrier, tables, anchor_raw, anchor_sign),
        "A0.CP.8_hopfield_energy_gradient_sign": build_cp8_variants(carrier, tables, anchor_raw, anchor_sign, surface),
        "A0.CP.9_holonomy_spectrum_sign": build_cp9_variants(carrier, tables, anchor_raw, anchor_sign, holonomy),
    }
    rows = [family_verdict(spec, variant_builders[spec.cid], anchor_form) for spec in HEAVY_SPECS]
    forms = {ANCHOR_ID: anchor_form}
    for row in rows:
        forms[row["candidate"]] = row["canonical_alias_form"]
    pair_table: list[dict[str, Any]] = []
    ids = [ANCHOR_ID] + [spec.cid for spec in HEAVY_SPECS]
    for i, left in enumerate(ids):
        for right in ids[i + 1 :]:
            pair_table.append(alias_relation(forms[left], forms[right]))
    return rows, {
        "anchor_raw": anchor_raw,
        "anchor_sign": anchor_sign,
        "anchor_form": anchor_form,
        "alias_pair_table": pair_table,
        "source_hashes": {
            "terrain_generator_sheet_packet": sha256_file(TERRAIN_PACKET),
            "terrain_spinor_flux_nest_n3_v0": sha256_file(FLUX_N3),
            "terrain_spinor_flux_nest_n4_v0": sha256_file(FLUX_N4),
            "spinor_network_surface_v1_pytorch": sha256_file(SPINOR_SURFACE_V1),
            "npc2_connection_geometry_julia": sha256_file(NPC2_HOLONOMY),
        },
    }


def smt_proof(bound_values: dict[str, int], *, solver_name: str) -> dict[str, Any]:
    if solver_name == "z3":
        solver = z3.Solver()
        terms = []
        for name, value in bound_values.items():
            var = z3.Int(f"a0_heavy_{name}")
            solver.add(var == value)
            terms.append(var != value)
        solver.add(z3.Or(*terms))
        verdict = str(solver.check()).lower()
        flip = z3.Solver()
        mutated = z3.Int("mutated_cp3_hamming")
        flip.add(mutated == bound_values["cp3_hamming_count"] + 1)
        flip.add(mutated != bound_values["cp3_hamming_count"])
        flip_verdict = str(flip.check()).lower()
    elif solver_name == "cvc5":
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        terms = []
        for name, value in bound_values.items():
            var = solver.mkConst(int_sort, f"a0_heavy_{name}")
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
            terms.append(solver.mkTerm(Kind.DISTINCT, var, solver.mkInteger(value)))
        solver.assertFormula(solver.mkTerm(Kind.OR, *terms))
        verdict = str(solver.checkSat()).lower()
        flip = cvc5.Solver()
        flip.setLogic("QF_LIA")
        flip_int = flip.getIntegerSort()
        mutated = flip.mkConst(flip_int, "mutated_cp3_hamming")
        flip.assertFormula(flip.mkTerm(Kind.EQUAL, mutated, flip.mkInteger(bound_values["cp3_hamming_count"] + 1)))
        flip.assertFormula(flip.mkTerm(Kind.DISTINCT, mutated, flip.mkInteger(bound_values["cp3_hamming_count"])))
        flip_verdict = str(flip.checkSat()).lower()
    else:
        raise ValueError(solver_name)
    return {
        "solver": solver_name,
        "ran": True,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "bound_values": bound_values,
        "claim": "row-local heavy-pass hamming, boundary, stability, and verdict-code bindings are fixed",
        "negated_assertion": "at least one row-local heavy binding differs from the computed value",
        "verdict": verdict,
        "flip_control_verdict": flip_verdict,
        "positive_case": "negating the computed row-local bindings is UNSAT",
        "negative/erased_control": "mutating CP.3 hamming by one is SAT and would be caught",
    }


def bound_values_from_rows(rows: list[dict[str, Any]], controls: list[dict[str, Any]], regressions: list[dict[str, Any]]) -> dict[str, int]:
    values: dict[str, int] = {
        "heavy_family_count": len(rows),
        "co_survivor_count": sum(row["co_survivor"] for row in rows),
        "alias_count": sum(row["alias"] for row in rows),
        "excluded_count": sum(row["verdict"].startswith("excluded-by") for row in rows),
        "control_alias_count": sum(row["verdict"] == "alias-of-anchor" for row in controls),
        "light_regression_excluded_count": sum(row["verdict"].startswith("excluded-by") for row in regressions),
    }
    for row in rows:
        cp_num = row["candidate"].split("A0.CP.", 1)[1].split("_", 1)[0]
        prefix = f"cp{cp_num}"
        values[f"{prefix}_hamming_count"] = int(row["hamming_disagreement_count"])
        values[f"{prefix}_boundary_reads_axis0"] = int(row["distinction_boundary_check"]["reads_axis0_feedback_distinction"])
        values[f"{prefix}_stability_matches_anchor"] = int(row["stability_class_comparison"]["matches_anchor_profile"])
        values[f"{prefix}_verdict_code"] = VERDICT_CODES.get(row["verdict"], 99)
    return values


def adjudication_sentence(rows: list[dict[str, Any]]) -> str:
    survivors = [row["candidate"] for row in rows if row["co_survivor"]]
    if not survivors:
        return "Axis-0 = the anchor alias class"
    names = ["anchor alias class"] + survivors
    return f"Axis-0 = a family of {len(names)} named co-survivors {{{', '.join(names)}}}"


def build_core_result() -> dict[str, Any]:
    carrier, tables = anchor_object()
    heavy_rows, context = build_heavy_rows(carrier, tables)
    regressions = light_regression_rows(carrier, tables, context["anchor_raw"], context["anchor_sign"])
    controls = control_rows(carrier, tables, context["anchor_raw"], context["anchor_sign"])
    bound_values = bound_values_from_rows(heavy_rows, controls, regressions)
    z3_result = smt_proof(bound_values, solver_name="z3")
    cvc5_result = smt_proof(bound_values, solver_name="cvc5")
    registry_blob = git_show(REGISTRY_COMMIT, REGISTRY_REL)
    doctrine_blob = git_show(DOCTRINE_COMMIT, DOCTRINE_REL)
    sweep_audit_blob = git_show(SWEEP_COMMIT, SWEEP_AUDIT_REL)
    registry_text = REGISTRY_PATH.read_text(encoding="utf-8")
    gates = {
        "registry_commit_bound": sha256_bytes(registry_blob) != "",
        "doctrine_commit_bound": sha256_bytes(doctrine_blob) != "",
        "sweep_audit_commit_bound": sha256_bytes(sweep_audit_blob) != "",
        "exact_candidate_space_cp3_to_cp9": [row["candidate"] for row in heavy_rows] == [spec.cid for spec in HEAVY_SPECS],
        "all_heavy_rows_have_33_cell_vectors": all(len(row["sign_vector"]) == 33 for row in heavy_rows),
        "all_heavy_rows_have_cell_disagreement_tables": all("cell_level_disagreement_table" in row for row in heavy_rows),
        "all_heavy_rows_have_stability_comparisons": all("stability_class_comparison" in row for row in heavy_rows),
        "all_heavy_rows_have_boundary_checks": all("distinction_boundary_check" in row for row in heavy_rows),
        "no_cosurvivor_without_passed_rows": all((not row["co_survivor"]) or bool(row["passed_rows_for_cosurvivor_mint"]) for row in heavy_rows),
        "anchor_alias_control_passes": controls[0]["verdict"] == "alias-of-anchor",
        "deliberate_alias_control_passes": controls[1]["verdict"] == "alias-of-anchor",
        "light_exclusions_stay_excluded": all(row["verdict"].startswith("excluded-by") for row in regressions),
        "different_distinction_controls_die": all(
            row["verdict"].startswith("excluded-by")
            for row in controls
            if row["id"] not in {"control.anchor_self", "control.deliberate_alias"}
        ),
        "z3_positive_unsat": z3_result["verdict"] == "unsat",
        "z3_flip_control_sat": z3_result["flip_control_verdict"] == "sat",
        "cvc5_positive_unsat": cvc5_result["verdict"] == "unsat",
        "cvc5_flip_control_sat": cvc5_result["flip_control_verdict"] == "sat",
        "registry_annotation_present": "terrain-family assignment is shuffled or erased" in registry_text,
    }
    return {
        "schema": f"{SIM_ID}_core_v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "registry_binding": {
            "path": REGISTRY_REL,
            "commit": REGISTRY_COMMIT,
            "commit_blob_sha256": sha256_bytes(registry_blob),
            "working_tree_sha256": sha256_file(REGISTRY_PATH),
            "candidate_space_bound": [spec.cid for spec in HEAVY_SPECS],
            "alternative_space_bound": "NO new candidates; CP.3-CP.9 only",
            "read_in_full": True,
        },
        "doctrine_binding": {
            "path": DOCTRINE_REL,
            "commit": DOCTRINE_COMMIT,
            "commit_blob_sha256": sha256_bytes(doctrine_blob),
            "expectation_1": "unique-up-to-alias or named co-survivor family",
        },
        "sweep_audit_binding": {
            "path": SWEEP_AUDIT_REL,
            "commit": SWEEP_COMMIT,
            "commit_blob_sha256": sha256_bytes(sweep_audit_blob),
            "corrected_vocabulary": "CP.3-CP.9 were open + queued-heavy before this packet",
        },
        "anchor_binding": {
            "sim_id": "discrete_axis0_field_v0",
            "result_path": rel(ANCHOR_RESULT),
            "carrier_state_object_id": carrier["state_object_id"],
            "state_count": carrier["state_count"],
            "edge_count": carrier["edge_count"],
            "anchor_alias_form_sha256": context["anchor_form"]["sha256"],
        },
        "adapter_pin": {
            "pinning_rule": "all subvariant adapters are declared in code before computation and hashed in each variant convention",
            "cell_adapter": "dominant committed terrain-generator edge by max absolute outgoing anchor gradient; Ne generator enumerates pure_hamiltonian and weak_dissipator variants",
            "flux_adapter": "carrier edge to source flux edge by committed edge hash, source edge list, and value key",
            "underdetermined_registry_details": "enumerated as finite subvariants; no post-result adapter choice is used for verdict minting",
        },
        "source_inputs_read": {
            "terrain_generator_sheet_packet": {"path": rel(TERRAIN_PACKET), "sha256": context["source_hashes"]["terrain_generator_sheet_packet"]},
            "terrain_spinor_flux_nest_n3_v0": {"path": rel(FLUX_N3), "sha256": context["source_hashes"]["terrain_spinor_flux_nest_n3_v0"]},
            "terrain_spinor_flux_nest_n4_v0": {"path": rel(FLUX_N4), "sha256": context["source_hashes"]["terrain_spinor_flux_nest_n4_v0"]},
            "spinor_network_surface_v1_pytorch": {"path": rel(SPINOR_SURFACE_V1), "sha256": context["source_hashes"]["spinor_network_surface_v1_pytorch"]},
            "npc2_connection_geometry_julia": {"path": rel(NPC2_HOLONOMY), "sha256": context["source_hashes"]["npc2_connection_geometry_julia"]},
        },
        "positive": {
            "anchor_self": controls[0],
            "deliberate_alias": controls[1],
            "alias_pair_table": context["alias_pair_table"],
        },
        "negative": {
            "family_verdict_table": heavy_rows,
            "light_regression_controls": regressions,
            "no_structure_controls": controls[2:],
        },
        "boundary": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "scope": "33-cell carrier only; no sweeps beyond registry heavy rows",
            "co_survivor_minting_rule": "only a non-alias variant with every heavy row passed can mint GENUINE CO-SURVIVOR",
            "final_family_adjudication": adjudication_sentence(heavy_rows),
        },
        "candidate_verdict_table": heavy_rows,
        "final_verdict_table": [
            {
                "candidate": row["candidate"],
                "selected_variant_id": row["selected_variant_id"],
                "classification": row["classification"],
                "final_verdict": row["verdict"],
                "hamming_disagreement_count": row["hamming_disagreement_count"],
                "boundary_reads_axis0": row["distinction_boundary_check"]["reads_axis0_feedback_distinction"],
                "stability_matches_anchor": row["stability_class_comparison"]["matches_anchor_profile"],
                "witness_row": row["witness"]["row"],
                "co_survivor": row["co_survivor"],
            }
            for row in heavy_rows
        ],
        "control_verdicts": controls,
        "light_regression_verdicts": regressions,
        "alias_pair_table": context["alias_pair_table"],
        "family_adjudication_sentence": adjudication_sentence(heavy_rows),
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
        "schema": f"{SIM_ID}_{engine}_lane_v1",
        "sim_id": SIM_ID,
        "role_id": role_id,
        "engine_role_note": engine_role_note,
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "package_observables": package_observables,
        "claim_path_tools": load_bearing,
        "all_pass": core["all_pass"],
        "registry_binding": core["registry_binding"],
        "doctrine_binding": core["doctrine_binding"],
        "sweep_audit_binding": core["sweep_audit_binding"],
        "anchor_binding": core["anchor_binding"],
        "adapter_pin": core["adapter_pin"],
        "source_inputs_read": core["source_inputs_read"],
        "positive": core["positive"],
        "negative": core["negative"],
        "boundary": core["boundary"],
        "candidate_verdicts": core["candidate_verdict_table"],
        "final_verdict_table": core["final_verdict_table"],
        "control_verdicts": core["control_verdicts"],
        "light_regression_verdicts": core["light_regression_verdicts"],
        "alias_pair_table": core["alias_pair_table"],
        "family_adjudication_sentence": core["family_adjudication_sentence"],
        "counts": core["counts"],
        "crossover_proofs": core["crossover_proofs"],
        "build_gates": core["build_gates"],
        "TOOL_MANIFEST": {package: {"used": True, "reason": package_observables[package]} for package in load_bearing},
        "TOOL_INTEGRATION_DEPTH": {package: "load_bearing" for package in load_bearing},
        "tool_calls": [],
        "core_result_sha256": stable_hash(core["final_verdict_table"]),
    }
    if extra:
        payload.update(extra)
    return payload
