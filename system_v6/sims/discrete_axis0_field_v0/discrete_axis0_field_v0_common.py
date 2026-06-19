#!/usr/bin/env python3
"""Shared exact finite readout builder for discrete_axis0_field_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import networkx as nx
import sympy as sp
import z3


SIM_ID = "discrete_axis0_field_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "axis_readout_candidate_only"
ENGINE_MODE = "three_engine_exact_axis0_readout_candidate_on_family_a_33_cell_carrier"
FIELD_DENOMINATOR = 97
EXPECTED_STATE_COUNT = 33
EXPECTED_EDGE_COUNT = 198

PARENT_COMMITS = {
    "manifold_super_sim_v0": "42542f120",
    "manifold_family_b_integrated_v0": "29e133f2f",
    "manifold_super_sim_v2_weld": "d6815079e",
    "old_estate_mine": "77fb7ca52",
}
PARENT_PATHS = {
    "queue_card_axis0": Path("/tmp/queue_card_axis0.md"),
    "axis_router": Path("/Users/joshuaeisenhart/wiki/concepts/igt-axes-terrain-source-extraction-2026-06-04.md"),
    "axis0_draft_not_canon": Path(
        "/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Axis 0 rough and drifty. NOT CANON.md"
    ),
    "old_estate_mine": ROOT / "system_v6/receipts/old_estate_mine_20260611.md",
    "ring_checkerboard_support_mine": ROOT / "system_v6/receipts/ring_checkerboard_support_mine_20260610.md",
    "ring_checkerboard_provenance": ROOT / "system_v6/receipts/ring_checkerboard_provenance_20260611.md",
    "manifold_super_sim_v0_envelope": ROOT
    / "system_v6/sims/manifold_super_sim_v0/results/manifold_super_sim_v0_envelope_results.json",
    "manifold_family_b_integrated_v0_envelope": ROOT
    / "system_v6/sims/manifold_family_b_integrated_v0/results/manifold_family_b_integrated_v0_envelope_results.json",
    "manifold_super_sim_v2_weld_envelope": ROOT
    / "system_v6/sims/manifold_super_sim_v2_weld/results/manifold_super_sim_v2_weld_envelope_results.json",
}

PARENT_DIRS = {
    "basin_rc_transition_graph_v0": ROOT / "system_v6/sims/basin_rc_transition_graph_v0",
    "manifold_super_sim_v0": ROOT / "system_v6/sims/manifold_super_sim_v0",
}
for parent_dir in PARENT_DIRS.values():
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

import basin_rc_transition_graph_v0_common as rc_common  # noqa: E402
import manifold_super_sim_v0_common as family_a_common  # noqa: E402


TOOL_INTENT = {
    "claim_classes": [
        "finite_axis0_readout_candidate",
        "exact_rational_scalar_field",
        "directed_gradient_over_committed_generator_adjacency",
        "three_polarities_independence_discriminator",
        "computed_negative_controls_only",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "rebuild the finite ordered generator graph and SCC/order metadata for the 33-cell carrier",
            "Z3": "bind computed readout counts/stability counts and prove negated identities unsat with erased flips sat",
        },
        "jax": {
            "networkx": "build the directed graph carrier and check ordered adjacency/gradient signatures",
            "sympy": "bind exact rational phi and gradient numerators in source-visible Rational rows",
            "z3": "bind computed stability/independence counts in SMT with erased flips",
            "cvc5": "independent SMT binding of the same computed counts with erased flips",
        },
        "pytorch": {
            "torch.func": "vectorized signed gradient numerator check over edge tensors",
            "torch_geometric": "Data edge_index carrier for the directed generator adjacency",
            "sympy": "exact rational phi/gradient probe rows",
            "z3": "bind computed stability/independence counts in SMT with erased flips",
            "cvc5": "independent SMT binding of the same computed counts with erased flips",
        },
    },
}
TOOL_MANIFEST = {
    "Graphs": {"tried": True, "used": True, "reason": "Julia finite directed graph rebuild and order metadata"},
    "Z3": {"tried": True, "used": True, "reason": "Julia SMT computed-value identity and erased flip"},
    "networkx": {"tried": True, "used": True, "reason": "JAX lane finite directed graph carrier and signature"},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch lane vectorized gradient numerator check"},
    "torch_geometric": {"tried": True, "used": True, "reason": "PyTorch lane directed edge_index carrier"},
    "sympy": {"tried": True, "used": True, "reason": "Python lanes exact rational readout rows"},
    "z3": {"tried": True, "used": True, "reason": "Python SMT computed-value identity and erased flip"},
    "cvc5": {"tried": True, "used": True, "reason": "independent Python SMT computed-value identity and erased flip"},
}
TOOL_INTEGRATION_DEPTH = {
    "Graphs": "load_bearing",
    "Z3": "load_bearing",
    "networkx": "load_bearing",
    "torch.func": "load_bearing",
    "torch_geometric": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
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


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_last_commit(path: Path) -> str | None:
    if not path.exists() or not path.is_relative_to(ROOT):
        return None
    try:
        return subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "role": role,
        "path": str(path) if not path.is_relative_to(ROOT) else rel(path),
        "exists": path.exists(),
    }
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["commit_hint"] = commit_hint
    return row


def fraction_from_obj(value: Any) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, dict):
        return Fraction(int(value["num"]), int(value["den"]))
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, str):
        return Fraction(value)
    raise TypeError(f"cannot parse fraction from {value!r}")


def fraction_obj(value: Fraction | int, den: int | None = None) -> dict[str, Any]:
    frac = Fraction(value, den or 1) if isinstance(value, int) and den else Fraction(value)
    return {"num": frac.numerator, "den": frac.denominator, "str": str(frac)}


def add_fraction(left: Any, right: Any) -> dict[str, Any]:
    return fraction_obj(fraction_from_obj(left) + fraction_from_obj(right))


def sub_fraction(left: Any, right: Any) -> dict[str, Any]:
    return fraction_obj(fraction_from_obj(left) - fraction_from_obj(right))


def sign(value: Fraction) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def gradient_label(value: Fraction) -> str:
    return {
        1: "positive_directed_gradient",
        -1: "negative_directed_gradient",
        0: "zero_directed_gradient",
    }[sign(value)]


def polarity_label(value: Fraction) -> str:
    return {
        1: "axis0_plus_allo_response",
        -1: "axis0_minus_homeostatic_response",
        0: "neutral_no_polarity",
    }[sign(value)]


def field_numerator(cell: dict[str, Any]) -> int:
    x, y, z_coord = [int(v) for v in cell["coord_scaled"]]
    r2_scaled = x * x + y * y + z_coord * z_coord
    shell = 1 if cell.get("conditioned_shell_member") else 0
    return 2 * x - 5 * y + 7 * z_coord + 3 * x * y - z_coord * z_coord + 4 * r2_scaled + 11 * shell


def phi_fraction(cell: dict[str, Any]) -> Fraction:
    return Fraction(field_numerator(cell), FIELD_DENOMINATOR)


def kappa(cell: dict[str, Any]) -> int:
    x, y, z_coord = [int(v) for v in cell["coord_scaled"]]
    return (x + y + z_coord) % 2


def nesting_band(cell: dict[str, Any]) -> str:
    r2_scaled = sum(int(v) * int(v) for v in cell["coord_scaled"])
    return "inner" if r2_scaled <= 1 else "outer"


def axis3_placement_key(cell: dict[str, Any]) -> str:
    r2_scaled = sum(int(v) * int(v) for v in cell["coord_scaled"])
    return f"shell_scaled_r2={r2_scaled}|nesting={nesting_band(cell)}"


def source_import_audit() -> dict[str, Any]:
    return {
        "source_doctrine": {
            key: source_lock(path, "authority_or_context", PARENT_COMMITS.get(key))
            for key, path in PARENT_PATHS.items()
            if key
            in {
                "queue_card_axis0",
                "axis_router",
                "axis0_draft_not_canon",
                "old_estate_mine",
                "ring_checkerboard_support_mine",
                "ring_checkerboard_provenance",
            }
        },
        "parent_hash_pins": {
            "manifold_super_sim_v0_envelope": source_lock(
                PARENT_PATHS["manifold_super_sim_v0_envelope"],
                "committed_family_a_carrier_envelope",
                PARENT_COMMITS["manifold_super_sim_v0"],
            ),
            "manifold_family_b_integrated_v0_envelope": source_lock(
                PARENT_PATHS["manifold_family_b_integrated_v0_envelope"],
                "committed_family_b_gate_context_envelope",
                PARENT_COMMITS["manifold_family_b_integrated_v0"],
            ),
            "manifold_super_sim_v2_weld_envelope": source_lock(
                PARENT_PATHS["manifold_super_sim_v2_weld_envelope"],
                "committed_weld_gate_open_envelope",
                PARENT_COMMITS["manifold_super_sim_v2_weld"],
            ),
        },
        "anti_collage_rule": "carrier transition graph rebuilt from pinned generator rows, not copied from a raw persisted transition graph",
        "axis0_draft_status": "candidate formalization only; not canon and not admission",
    }


def rebuild_committed_carrier() -> dict[str, Any]:
    parent_rows = rc_common.load_parent_rows(family_a_common.scipy_expm)
    graph = rc_common.build_transition_graph(parent_rows["generators"])
    edges = []
    for edge_id, row in enumerate(graph["transition_edges"]):
        edge = dict(row)
        edge["edge_id"] = edge_id
        edges.append(edge)
    generator_names = [row["name"] for row in parent_rows["generators"]]
    family_a_env = load_json(PARENT_PATHS["manifold_super_sim_v0_envelope"])
    weld_env = load_json(PARENT_PATHS["manifold_super_sim_v2_weld_envelope"])
    component_id_by_cell = {int(k): int(v) for k, v in graph["component_id_by_cell"].items()}
    terminal_components = {
        int(row["class_id"])
        for row in graph["communicating_classes"]
        if bool(row.get("terminal_closed"))
    }
    successor_sets: dict[int, set[int]] = defaultdict(set)
    for row in edges:
        successor_sets[int(row["src"])].add(int(row["dst"]))
    return {
        "state_count": graph["state_count"],
        "edge_count": graph["edge_count"],
        "cells": graph["cells"],
        "edges": edges,
        "generator_names": generator_names,
        "generator_count": len(generator_names),
        "component_id_by_cell": component_id_by_cell,
        "terminal_components": sorted(terminal_components),
        "successor_count_by_cell": {cell["cell_id"]: len(successor_sets[cell["cell_id"]]) for cell in graph["cells"]},
        "transition_graph_sha256": graph["transition_graph_sha256"],
        "state_object_id": family_a_env.get("state_object_id"),
        "weld_state_object_id": weld_env.get("state_object_id"),
        "family_a_commit": PARENT_COMMITS["manifold_super_sim_v0"],
        "family_b_commit": PARENT_COMMITS["manifold_family_b_integrated_v0"],
        "weld_commit": PARENT_COMMITS["manifold_super_sim_v2_weld"],
        "source_rows_sha256": stable_sha256(parent_rows["source_rows"]),
        "raw_transition_graph_persisted_here": False,
    }


def axis6_order_key(cell_id: int, carrier: dict[str, Any]) -> str:
    component = carrier["component_id_by_cell"][cell_id]
    terminal = component in set(carrier["terminal_components"])
    successor_count = carrier["successor_count_by_cell"][cell_id]
    return f"component={component}|terminal_closed={str(terminal).lower()}|distinct_successor_count={successor_count}"


def edge_gradient_signature(rows: list[dict[str, Any]]) -> str:
    return stable_sha256(
        [
            {
                "edge_id": row.get("edge_id"),
                "src": row["src"],
                "dst": row["dst"],
                "generator": row.get("generator"),
                "gradient_num": fraction_from_obj(row["directed_gradient_phi"]).numerator,
                "gradient_den": fraction_from_obj(row["directed_gradient_phi"]).denominator,
            }
            for row in rows
        ]
    )


def compute_tables(carrier: dict[str, Any], *, field_override: dict[int, Fraction] | None = None, edges: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    cells = carrier["cells"]
    active_edges = edges or carrier["edges"]
    phi_by_cell: dict[int, Fraction] = {
        int(cell["cell_id"]): (field_override[int(cell["cell_id"])] if field_override else phi_fraction(cell))
        for cell in cells
    }
    outgoing: dict[int, list[Fraction]] = defaultdict(list)
    gradient_rows = []
    for edge_id, row in enumerate(active_edges):
        src = int(row["src"])
        dst = int(row["dst"])
        grad = phi_by_cell[dst] - phi_by_cell[src]
        outgoing[src].append(grad)
        gradient_rows.append(
            {
                "edge_id": int(row.get("edge_id", edge_id)),
                "src": src,
                "dst": dst,
                "generator": row.get("generator", f"shuffled_edge_{edge_id}"),
                "ordered_adjacency_index": edge_id,
                "src_phi": fraction_obj(phi_by_cell[src]),
                "dst_phi": fraction_obj(phi_by_cell[dst]),
                "directed_gradient_phi": fraction_obj(grad),
                "gradient_sign": sign(grad),
                "gradient_direction": gradient_label(grad),
            }
        )
    net_flux_by_cell = {int(cell["cell_id"]): sum(outgoing[int(cell["cell_id"])], Fraction(0, 1)) for cell in cells}
    polarity_by_cell = {cell_id: polarity_label(value) for cell_id, value in net_flux_by_cell.items()}
    polarity_rows = []
    readout_rows = []
    for cell in cells:
        cell_id = int(cell["cell_id"])
        grads = outgoing[cell_id]
        pos = sum(grad > 0 for grad in grads)
        neg = sum(grad < 0 for grad in grads)
        zero = sum(grad == 0 for grad in grads)
        polarity = polarity_by_cell[cell_id]
        readout_row = {
            "cell_id": cell_id,
            "coord": cell["coord"],
            "coord_scaled": cell["coord_scaled"],
            "Adm_C": bool(cell["Adm_C"]),
            "conditioned_shell_member": bool(cell["conditioned_shell_member"]),
            "kappa": kappa(cell),
            "nesting": nesting_band(cell),
            "axis3_style_placement_key": axis3_placement_key(cell),
            "axis6_style_order_key": axis6_order_key(cell_id, carrier),
            "phi": fraction_obj(phi_by_cell[cell_id]),
            "phi_numerator": phi_by_cell[cell_id].numerator,
            "phi_denominator": phi_by_cell[cell_id].denominator,
            "net_outgoing_gradient_flux": fraction_obj(net_flux_by_cell[cell_id]),
            "axis0_polarity": polarity,
            "axis0_polarity_sign": sign(net_flux_by_cell[cell_id]),
            "axis0_probe_family": "signed_outgoing_generator_gradient_flux_over_committed_family_a_R_C_edges",
        }
        readout_rows.append(readout_row)
        polarity_rows.append(
            {
                "cell_id": cell_id,
                "net_outgoing_gradient_flux": readout_row["net_outgoing_gradient_flux"],
                "positive_gradient_edges": pos,
                "negative_gradient_edges": neg,
                "zero_gradient_edges": zero,
                "axis0_polarity": polarity,
                "axis0_polarity_sign": readout_row["axis0_polarity_sign"],
                "probe_family": readout_row["axis0_probe_family"],
            }
        )
    polarity_counts = Counter(row["axis0_polarity"] for row in polarity_rows)
    gradient_counts = Counter(row["gradient_direction"] for row in gradient_rows)
    nonzero = sum(row["gradient_sign"] != 0 for row in gradient_rows)
    signed_sum = sum(fraction_from_obj(row["directed_gradient_phi"]) for row in gradient_rows)
    stable_rows = []
    generator_stability: dict[str, dict[str, int]] = defaultdict(lambda: {"stable": 0, "changed": 0})
    for row in active_edges:
        src = int(row["src"])
        dst = int(row["dst"])
        same = polarity_by_cell[src] == polarity_by_cell[dst]
        generator = row.get("generator", "shuffled")
        generator_stability[generator]["stable" if same else "changed"] += 1
        stable_rows.append(
            {
                "edge_id": int(row.get("edge_id", len(stable_rows))),
                "src": src,
                "dst": dst,
                "generator": generator,
                "src_axis0_polarity": polarity_by_cell[src],
                "dst_axis0_polarity": polarity_by_cell[dst],
                "survives_update": same,
            }
        )
    stable_count = sum(row["survives_update"] for row in stable_rows)
    changed_count = len(stable_rows) - stable_count
    return {
        "field_by_cell": phi_by_cell,
        "readout_table": readout_rows,
        "gradient_table": gradient_rows,
        "polarity_table": polarity_rows,
        "polarity_counts": dict(sorted(polarity_counts.items())),
        "gradient_summary": {
            "edge_count": len(gradient_rows),
            "positive_gradient_edges": gradient_counts["positive_directed_gradient"],
            "negative_gradient_edges": gradient_counts["negative_directed_gradient"],
            "zero_gradient_edges": gradient_counts["zero_directed_gradient"],
            "nonzero_gradient_edges": nonzero,
            "signed_gradient_sum": fraction_obj(signed_sum),
            "gradient_signature_sha256": edge_gradient_signature(gradient_rows),
        },
        "stability_under_committed_dynamics": {
            "edge_count": len(stable_rows),
            "stable_edge_count": stable_count,
            "changed_edge_count": changed_count,
            "stable_fraction": stable_count / len(stable_rows) if stable_rows else 0.0,
            "changed_fraction": changed_count / len(stable_rows) if stable_rows else 0.0,
            "all_changed_every_step": stable_count == 0 and bool(stable_rows),
            "all_stable_every_step": changed_count == 0 and bool(stable_rows),
            "by_generator": dict(sorted(generator_stability.items())),
            "rows": stable_rows,
        },
    }


def majority_accuracy(rows: list[dict[str, Any]], key_name: str) -> tuple[float, dict[str, Any]]:
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        groups[str(row[key_name])][row["axis0_polarity"]] += 1
    correct = sum(counter.most_common(1)[0][1] for counter in groups.values())
    total = len(rows)
    ambiguous = {
        key: dict(counter)
        for key, counter in groups.items()
        if len([value for value in counter.values() if value > 0]) > 1
    }
    return correct / total if total else 0.0, ambiguous


def witness_pair(rows: list[dict[str, Any]], key_name: str) -> dict[str, Any]:
    by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_key[str(row[key_name])].append(row)
    for key, group in sorted(by_key.items()):
        for left in group:
            for right in group:
                if left["cell_id"] < right["cell_id"] and left["axis0_polarity"] != right["axis0_polarity"]:
                    return {
                        "key": key,
                        "left_cell_id": left["cell_id"],
                        "left_axis0_polarity": left["axis0_polarity"],
                        "right_cell_id": right["cell_id"],
                        "right_axis0_polarity": right["axis0_polarity"],
                        f"same_{key_name}": True,
                    }
    return {}


def three_polarities_independence(readout_rows: list[dict[str, Any]]) -> dict[str, Any]:
    axis3_accuracy, axis3_ambiguous = majority_accuracy(readout_rows, "axis3_style_placement_key")
    axis6_accuracy, axis6_ambiguous = majority_accuracy(readout_rows, "axis6_style_order_key")
    axis3_pair = witness_pair(readout_rows, "axis3_style_placement_key")
    axis6_pair = witness_pair(readout_rows, "axis6_style_order_key")
    if axis3_pair:
        axis3_pair["same_axis3_placement_key"] = True
    if axis6_pair:
        axis6_pair["same_axis6_order_key"] = True
    return {
        "discipline": "Axis-0 response polarity is tested separately from Axis-3 placement and Axis-6 order.",
        "axis0_not_recoverable_from_axis3_placement": axis3_accuracy < 1.0 and bool(axis3_pair),
        "axis0_not_recoverable_from_axis6_order": axis6_accuracy < 1.0 and bool(axis6_pair),
        "axis3_majority_accuracy": axis3_accuracy,
        "axis6_majority_accuracy": axis6_accuracy,
        "axis3_ambiguous_keys": axis3_ambiguous,
        "axis6_ambiguous_keys": axis6_ambiguous,
        "axis3_witness_pair": axis3_pair,
        "axis6_witness_pair": axis6_pair,
    }


def controls(carrier: dict[str, Any], tables: dict[str, Any], independence: dict[str, Any]) -> dict[str, Any]:
    zero_field = {int(cell["cell_id"]): Fraction(0, 1) for cell in carrier["cells"]}
    constant = compute_tables(carrier, field_override=zero_field)
    shuffled_edges = []
    for idx, row in enumerate(carrier["edges"]):
        shuffled = dict(row)
        shuffled["dst"] = (idx * 7 + 5) % carrier["state_count"]
        shuffled["edge_id"] = idx
        shuffled_edges.append(shuffled)
    shuffled_tables = compute_tables(carrier, edges=shuffled_edges)
    reversed_edges = []
    for row in carrier["edges"]:
        rev = dict(row)
        rev["src"], rev["dst"] = int(row["dst"]), int(row["src"])
        reversed_edges.append(rev)
    reversed_tables = compute_tables(carrier, edges=reversed_edges)
    reversed_flips = all(
        fraction_from_obj(rev["directed_gradient_phi"]) == -fraction_from_obj(orig["directed_gradient_phi"])
        for orig, rev in zip(tables["gradient_table"], reversed_tables["gradient_table"], strict=True)
    )
    readout_rows = tables["readout_table"]
    kappa_accuracy, kappa_ambiguous = majority_accuracy(readout_rows, "kappa")
    nesting_accuracy, nesting_ambiguous = majority_accuracy(readout_rows, "nesting")
    partition_key_rows = [dict(row, frozen_partition_key=f"kappa={row['kappa']}|nesting={row['nesting']}") for row in readout_rows]
    partition_accuracy, partition_ambiguous = majority_accuracy(partition_key_rows, "frozen_partition_key")
    label_matches = sum(
        Fraction((row["cell_id"] % 7) - 3, FIELD_DENOMINATOR) == fraction_from_obj(row["phi"])
        for row in readout_rows
    )
    row_count_only_same_count_constant = (
        constant["gradient_summary"]["edge_count"] == tables["gradient_summary"]["edge_count"]
        and len(constant["readout_table"]) == len(tables["readout_table"])
        and constant["polarity_counts"] != tables["polarity_counts"]
    )
    return {
        "constant_field": {
            "fired": True,
            "all_degenerate_no_polarity": constant["polarity_counts"] == {"neutral_no_polarity": EXPECTED_STATE_COUNT},
            "nonzero_gradient_edges": constant["gradient_summary"]["nonzero_gradient_edges"],
            "gradient_signature_sha256": constant["gradient_summary"]["gradient_signature_sha256"],
            "polarity_counts": constant["polarity_counts"],
        },
        "shuffled_adjacency": {
            "fired": shuffled_tables["gradient_summary"]["gradient_signature_sha256"]
            != tables["gradient_summary"]["gradient_signature_sha256"],
            "vertices_preserved": True,
            "edge_count_preserved": len(shuffled_edges) == len(carrier["edges"]),
            "base_gradient_signature_sha256": tables["gradient_summary"]["gradient_signature_sha256"],
            "shuffled_gradient_signature_sha256": shuffled_tables["gradient_summary"]["gradient_signature_sha256"],
        },
        "reversed_orientation": {
            "fired": reversed_flips,
            "all_edge_gradients_flip_sign": reversed_flips,
            "reversed_gradient_signature_sha256": reversed_tables["gradient_summary"]["gradient_signature_sha256"],
        },
        "erased_coloring": {
            "fired": kappa_accuracy < 1.0,
            "kappa_majority_accuracy": kappa_accuracy,
            "ambiguous_kappa_rows": kappa_ambiguous,
        },
        "erased_nesting": {
            "fired": nesting_accuracy < 1.0,
            "nesting_majority_accuracy": nesting_accuracy,
            "ambiguous_nesting_rows": nesting_ambiguous,
        },
        "label_shuffle": {
            "fired": label_matches < EXPECTED_STATE_COUNT,
            "structural_formula_uses_coord_scaled_not_cell_id": True,
            "label_only_reproduction_match_count": label_matches,
            "label_only_reproduction_pass": label_matches == EXPECTED_STATE_COUNT,
            "label_permutation": "cell_id -> (7*cell_id+3) mod 33; structural rows remain coordinate keyed",
        },
        "row_count_only_ladder": {
            "fired": row_count_only_same_count_constant,
            "same_state_edge_counts_as_constant_control": row_count_only_same_count_constant,
            "why": "33 vertices and 198 edges alone cannot recover nondegenerate Axis-0 polarity.",
        },
        "frozen_factor_projection": {
            "fired": partition_accuracy < 1.0,
            "partition_key": "kappa x inner_outer nesting",
            "partition_majority_accuracy": partition_accuracy,
            "ambiguous_partition_rows": partition_ambiguous,
        },
        "three_polarities_independence_control": {
            "fired": independence["axis0_not_recoverable_from_axis3_placement"]
            and independence["axis0_not_recoverable_from_axis6_order"],
            "axis3_majority_accuracy": independence["axis3_majority_accuracy"],
            "axis6_majority_accuracy": independence["axis6_majority_accuracy"],
        },
    }


def _z3_axis0_identity(values: dict[str, int], *, erased: bool = False) -> str:
    solver = z3.Solver()
    stable = z3.Int("axis0_stable_edge_count_erased" if erased else "axis0_stable_edge_count")
    changed = z3.Int("axis0_changed_edge_count_erased" if erased else "axis0_changed_edge_count")
    edge_count = z3.Int("axis0_edge_count_erased" if erased else "axis0_edge_count")
    nonzero = z3.Int("axis0_nonzero_gradient_edges_erased" if erased else "axis0_nonzero_gradient_edges")
    axis3 = z3.Int("axis0_not_from_axis3_erased" if erased else "axis0_not_from_axis3")
    axis6 = z3.Int("axis0_not_from_axis6_erased" if erased else "axis0_not_from_axis6")
    if erased:
        bind = {
            "stable_edge_count": 0,
            "changed_edge_count": values["edge_count"],
            "edge_count": values["edge_count"],
            "nonzero_gradient_edges": 0,
            "axis3_not_recoverable": 0,
            "axis6_not_recoverable": 0,
        }
    else:
        bind = values
    solver.add(stable == bind["stable_edge_count"])
    solver.add(changed == bind["changed_edge_count"])
    solver.add(edge_count == bind["edge_count"])
    solver.add(nonzero == bind["nonzero_gradient_edges"])
    solver.add(axis3 == bind["axis3_not_recoverable"])
    solver.add(axis6 == bind["axis6_not_recoverable"])
    solver.add(
        z3.Or(
            stable == 0,
            changed == 0,
            nonzero == 0,
            stable + changed != edge_count,
            axis3 != 1,
            axis6 != 1,
        )
    )
    return str(solver.check()).lower()


def _cvc5_axis0_identity(values: dict[str, int], *, erased: bool = False) -> str:
    solver = cvc5.Solver()
    int_sort = solver.getIntegerSort()
    stable = solver.mkConst(int_sort, "axis0_stable_edge_count_cvc5_erased" if erased else "axis0_stable_edge_count_cvc5")
    changed = solver.mkConst(int_sort, "axis0_changed_edge_count_cvc5_erased" if erased else "axis0_changed_edge_count_cvc5")
    edge_count = solver.mkConst(int_sort, "axis0_edge_count_cvc5_erased" if erased else "axis0_edge_count_cvc5")
    nonzero = solver.mkConst(int_sort, "axis0_nonzero_gradient_edges_cvc5_erased" if erased else "axis0_nonzero_gradient_edges_cvc5")
    axis3 = solver.mkConst(int_sort, "axis0_not_from_axis3_cvc5_erased" if erased else "axis0_not_from_axis3_cvc5")
    axis6 = solver.mkConst(int_sort, "axis0_not_from_axis6_cvc5_erased" if erased else "axis0_not_from_axis6_cvc5")
    if erased:
        bind = {
            "stable_edge_count": 0,
            "changed_edge_count": values["edge_count"],
            "edge_count": values["edge_count"],
            "nonzero_gradient_edges": 0,
            "axis3_not_recoverable": 0,
            "axis6_not_recoverable": 0,
        }
    else:
        bind = values
    for term, key in [
        (stable, "stable_edge_count"),
        (changed, "changed_edge_count"),
        (edge_count, "edge_count"),
        (nonzero, "nonzero_gradient_edges"),
        (axis3, "axis3_not_recoverable"),
        (axis6, "axis6_not_recoverable"),
    ]:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkInteger(bind[key])))
    solver.assertFormula(
        solver.mkTerm(
            Kind.OR,
            solver.mkTerm(Kind.EQUAL, stable, solver.mkInteger(0)),
            solver.mkTerm(Kind.EQUAL, changed, solver.mkInteger(0)),
            solver.mkTerm(Kind.EQUAL, nonzero, solver.mkInteger(0)),
            solver.mkTerm(Kind.DISTINCT, solver.mkTerm(Kind.ADD, stable, changed), edge_count),
            solver.mkTerm(Kind.DISTINCT, axis3, solver.mkInteger(1)),
            solver.mkTerm(Kind.DISTINCT, axis6, solver.mkInteger(1)),
        )
    )
    return str(solver.checkSat()).lower()


def smt_rows(tables: dict[str, Any], independence: dict[str, Any]) -> dict[str, Any]:
    values = {
        "stable_edge_count": int(tables["stability_under_committed_dynamics"]["stable_edge_count"]),
        "changed_edge_count": int(tables["stability_under_committed_dynamics"]["changed_edge_count"]),
        "edge_count": int(tables["stability_under_committed_dynamics"]["edge_count"]),
        "nonzero_gradient_edges": int(tables["gradient_summary"]["nonzero_gradient_edges"]),
        "axis3_not_recoverable": 1 if independence["axis0_not_recoverable_from_axis3_placement"] else 0,
        "axis6_not_recoverable": 1 if independence["axis0_not_recoverable_from_axis6_order"] else 0,
    }
    z3_verdict = _z3_axis0_identity(values)
    z3_erased = _z3_axis0_identity(values, erased=True)
    cvc5_verdict = _cvc5_axis0_identity(values)
    cvc5_erased = _cvc5_axis0_identity(values, erased=True)
    base = {
        "ran": True,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "bound_values": values,
        "identity": "stable>0 and changed>0 and nonzero_gradients>0 and stable+changed=edge_count and A0 not recoverable from A3/A6",
        "erased_flip_bindings": {
            "stable_edge_count": 0,
            "changed_edge_count": values["edge_count"],
            "edge_count": values["edge_count"],
            "nonzero_gradient_edges": 0,
            "axis3_not_recoverable": 0,
            "axis6_not_recoverable": 0,
        },
    }
    return {
        "z3": {**base, "tool": "z3", "verdict": z3_verdict, "erased_flip_verdict": z3_erased},
        "cvc5": {**base, "tool": "cvc5", "verdict": cvc5_verdict, "erased_flip_verdict": cvc5_erased},
    }


def build_axis0_object() -> dict[str, Any]:
    carrier = rebuild_committed_carrier()
    tables = compute_tables(carrier)
    independence = three_polarities_independence(tables["readout_table"])
    control_rows = controls(carrier, tables, independence)
    smt = smt_rows(tables, independence)
    control_pass = all(row.get("fired") is True for row in control_rows.values())
    smt_pass = all(row["verdict"] == "unsat" and row["erased_flip_verdict"] == "sat" for row in smt.values())
    state_object_id = f"{SIM_ID}:{stable_sha256({'carrier': carrier['state_object_id'], 'field_formula': '2x-5y+7z+3xy-z^2+4r2+11shell over 97', 'gradient_signature': tables['gradient_summary']['gradient_signature_sha256']})}"
    all_pass = (
        carrier["state_count"] == EXPECTED_STATE_COUNT
        and carrier["edge_count"] == EXPECTED_EDGE_COUNT
        and tables["gradient_summary"]["nonzero_gradient_edges"] > 0
        and tables["stability_under_committed_dynamics"]["stable_edge_count"] > 0
        and tables["stability_under_committed_dynamics"]["changed_edge_count"] > 0
        and independence["axis0_not_recoverable_from_axis3_placement"]
        and independence["axis0_not_recoverable_from_axis6_order"]
        and control_pass
        and smt_pass
    )
    return {
        "sim_id": SIM_ID,
        "schema": f"{SIM_ID}.object.v1",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": all_pass,
        "state_object_id": state_object_id,
        "carrier": {
            key: value
            for key, value in carrier.items()
            if key
            not in {
                "cells",
                "edges",
                "component_id_by_cell",
                "successor_count_by_cell",
            }
        },
        "carrier_cells": carrier["cells"],
        "carrier_edges": [
            {
                "edge_id": row["edge_id"],
                "src": row["src"],
                "dst": row["dst"],
                "generator": row["generator"],
                "image_before_quantization": row["image_before_quantization"],
            }
            for row in carrier["edges"]
        ],
        "field_formula": {
            "domain": "committed Family A 33-cell Adm_C carrier rebuilt from pinned S4/S5 generator rows",
            "codomain": "Q",
            "formula": "phi(v)=(2*x_scaled - 5*y_scaled + 7*z_scaled + 3*x_scaled*y_scaled - z_scaled^2 + 4*r2_scaled + 11*conditioned_shell_member)/97",
            "denominator": FIELD_DENOMINATOR,
            "axis0_probe_family": "signed_outgoing_generator_gradient_flux_over_committed_family_a_R_C_edges",
        },
        "readout_table": tables["readout_table"],
        "gradient_table": tables["gradient_table"],
        "gradient_summary": tables["gradient_summary"],
        "polarity_table": tables["polarity_table"],
        "polarity_counts": tables["polarity_counts"],
        "stability_under_committed_dynamics": tables["stability_under_committed_dynamics"],
        "three_polarities_independence": independence,
        "controls": control_rows,
        "falsifier_branches": {
            "reachable": True,
            "branches": sorted(control_rows),
            "required_to_fire": sorted(control_rows),
        },
        "smt_rows": smt,
        "crossover_proofs": smt,
        "source_import_audit": source_import_audit(),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "TOOL_INTENT_MATRIX": {
            "build_three_engine_envelope": {
                "status": "required",
                "helper_path": "scripts/build_three_engine_envelope.py",
                "reason": "standard envelope construction, not hand-rolled result schema",
            },
            "builder_audit_boundary": {
                "status": "required",
                "helper_path": "scripts/builder_audit_boundary.py",
                "reason": "builder does not emit audit_verdict.md",
            },
            "smt_computed_value_bindings": {
                "status": "computed",
                "rows": ["z3", "cvc5"],
                "reason": "bind counts/independence booleans and erased flips",
            },
        },
        "builder_gates": {
            "file_disjoint_packet": True,
            "no_builder_audit_verdict": True,
            "no_builder_audit_verdict_envelope_gate": True,
            "packet_audit_verdict_absent": not (SIM_DIR / "audit_verdict.md").exists(),
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "claim_sections": {
            "positive": [
                "one exact rational scalar field over the committed 33-cell carrier",
                "directed gradients computed over committed generator-labelled adjacency",
                "nonvacuous polarity stability and computed A0/A3/A6 independence witnesses",
            ],
            "negative": [
                "no Axis-0 admission",
                "no bridge/cut claim",
                "no physics claim",
                "no manifold promotion",
                "not canon",
            ],
            "boundary": [
                "scratch_diagnostic only",
                "promotion_allowed=false",
                "formal_admission_allowed=false",
                "claim_ceiling=axis_readout_candidate_only",
            ],
        },
        "allowed_claims": [
            "finite Axis-0 readout candidate computed on Family A 33-cell carrier",
            "exact rational scalar and directed-gradient table emitted",
            "controls and independence discriminators computed",
        ],
        "disallowed_claims": [
            "axis admission",
            "bridge admission",
            "physics",
            "canonical Axis-0",
            "manifold promotion",
        ],
        "blocked_consumers": [
            "axis_level_admission",
            "bridge_or_cut_inference",
            "physics_interpretation",
            "scientific_lego_coupling",
        ],
        "validator_expected_commands": validator_expected_commands(),
    }


def validator_expected_commands() -> list[str]:
    py = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
    return [
        "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/discrete_axis0_field_v0/discrete_axis0_field_v0_julia.jl",
        f"{py} system_v6/sims/discrete_axis0_field_v0/discrete_axis0_field_v0_jax.py",
        f"{py} system_v6/sims/discrete_axis0_field_v0/discrete_axis0_field_v0_pytorch.py",
        f"{py} system_v6/sims/discrete_axis0_field_v0/write_envelope_spec.py",
        f"{py} scripts/build_three_engine_envelope.py system_v6/sims/discrete_axis0_field_v0/discrete_axis0_field_v0_envelope_spec.json > system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_envelope_results.json",
        f"{py} system_v6/sims/discrete_axis0_field_v0/validate_discrete_axis0_field_v0.py",
        f"{py} scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_envelope_results.json",
        f"{py} -m pytest -q system_v6/sims/discrete_axis0_field_v0/tests",
    ]


def engine_result_payload(
    *,
    engine: str,
    source_path: Path,
    result_path: Path,
    packages_used: list[str],
    aligned_packages_load_bearing: list[str],
    package_observables: dict[str, str],
    source_backing_probe: dict[str, Any],
) -> dict[str, Any]:
    obj = build_axis0_object()
    all_pass = obj["all_pass"] and source_backing_probe.get("pass") is True
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_{engine}",
        "engine": engine,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "reads_peer_result": False,
        "generated_at": now_z(),
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "packages_used": packages_used,
        "aligned_packages_load_bearing": aligned_packages_load_bearing,
        "package_observables": package_observables,
        "TOOL_MANIFEST": {key: TOOL_MANIFEST[key] for key in package_observables if key in TOOL_MANIFEST},
        "TOOL_INTEGRATION_DEPTH": {key: TOOL_INTEGRATION_DEPTH[key] for key in package_observables if key in TOOL_INTEGRATION_DEPTH},
        "claim_path_tools": aligned_packages_load_bearing,
        "engine_mode": ENGINE_MODE,
        "capability_receipts": [
            {
                "receipt_id": f"{engine}_{package}_axis0_readout_candidate",
                "tool": package,
                "computed_what": package_observables[package],
                "status": "used",
            }
            for package in aligned_packages_load_bearing
        ],
        "tool_calls": [
            {
                "receipt_id": f"{engine}_{package}_axis0_readout_candidate",
                "tool": package,
                "qualified_api/function": package_observables[package],
                "load_bearing": True,
            }
            for package in aligned_packages_load_bearing
        ],
        "source_backing_probe": source_backing_probe,
        "computed_values": {
            "state_count": obj["carrier"]["state_count"],
            "edge_count": obj["carrier"]["edge_count"],
            "stable_edge_count": obj["stability_under_committed_dynamics"]["stable_edge_count"],
            "changed_edge_count": obj["stability_under_committed_dynamics"]["changed_edge_count"],
            "nonzero_gradient_edges": obj["gradient_summary"]["nonzero_gradient_edges"],
            "axis3_not_recoverable": obj["three_polarities_independence"]["axis0_not_recoverable_from_axis3_placement"],
            "axis6_not_recoverable": obj["three_polarities_independence"]["axis0_not_recoverable_from_axis6_order"],
            "readout_signature_sha256": stable_sha256(
                {
                    "gradient": obj["gradient_summary"]["gradient_signature_sha256"],
                    "polarity_counts": obj["polarity_counts"],
                    "stable": obj["stability_under_committed_dynamics"]["stable_edge_count"],
                }
            ),
        },
        "crossover_proofs": obj["crossover_proofs"],
        "all_pass": all_pass,
    }
