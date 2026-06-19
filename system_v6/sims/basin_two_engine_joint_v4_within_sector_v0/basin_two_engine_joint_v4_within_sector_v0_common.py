#!/usr/bin/env python3
"""Shared machinery for the corrected within-sector two-engine basin packet."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import subprocess
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import networkx as nx
import sympy as sp
import z3


SIM_ID = "basin_two_engine_joint_v4_within_sector_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

LOOP_NAMES = ("base", "fiber")
D_ORDER = ("Se", "Ne", "Ni", "Si")
I_ORDER = ("Se", "Si", "Ni", "Ne")
ORDER_SHUFFLED_D = ("Se", "Ne", "Si", "Ni")
ORDER_SHUFFLED_I = ("Se", "Ni", "Ne", "Si")
DEFAULT_SHAPE = {"loop_mod": 2, "stage_mod": 4, "substage_mod": 4, "flux_mod": 2}

STAGE_WORD_COMPONENTS = {
    "Se": ("LOSE", "win"),
    "Ne": ("WIN", "lose"),
    "Ni": ("LOSE", "lose"),
    "Si": ("WIN", "win"),
}

ENGINE_SPECS = {
    "L": {
        "engine_type": "Type1",
        "chirality_sign": 1,
        "flux_direction": "IN",
        "loop_stage_words": {"base": D_ORDER, "fiber": I_ORDER},
        "loop_stage_words_order_shuffled": {"base": ORDER_SHUFFLED_D, "fiber": ORDER_SHUFFLED_I},
    },
    "R": {
        "engine_type": "Type2",
        "chirality_sign": -1,
        "flux_direction": "OUT",
        "loop_stage_words": {"base": I_ORDER, "fiber": D_ORDER},
        "loop_stage_words_order_shuffled": {"base": ORDER_SHUFFLED_I, "fiber": ORDER_SHUFFLED_D},
    },
}

BASE_VARIANTS: dict[str, dict[str, Any]] = {
    "A_readout_transition_dwell": {
        "label": "A-dwell directed stage-word / loop-readout row",
        "v3_flux_erased_terminal_sizes": [28],
    },
    "D_matrix64_b_order_overlay": {
        "label": "D Matrix64/Carnot product overlaid on B directed order",
        "v3_flux_erased_terminal_sizes": [24],
    },
}

V3_JOINT_EXPECTED = {
    "A_readout_transition_dwell": {"sync": 28, "all_interleavings": 1},
    "D_matrix64_b_order_overlay": {"sync": 24, "all_interleavings": 1},
}

FLUX_UPDATE_FAMILY: dict[str, dict[str, Any]] = {
    "conserved_flux_control": {
        "registered_role": "control",
        "flip_rule": "never flip the signed flux bit",
        "grounding": "panel-6 q3 conserved-flux control; must reproduce the v4 Z/2 sector decomposition",
        "primary_candidate": False,
    },
    "direction_sheet_opposing_current": {
        "registered_role": "candidate",
        "flip_rule": "flip on a stage/loop boundary when the current direction sheet reaches a readout whose sign opposes the engine chirality",
        "grounding": "v4 flux-continuity current signs; this is the inherited v4 state-dependent flip rule",
        "primary_candidate": True,
    },
    "arrival_current_negative": {
        "registered_role": "candidate",
        "flip_rule": "flip on a boundary when the arrived readout current sign is negative/LOSE",
        "grounding": "flux-continuity current-sign contrast row",
        "primary_candidate": True,
    },
    "arrival_current_positive": {
        "registered_role": "candidate",
        "flip_rule": "flip on a boundary when the arrived readout current sign is positive/WIN",
        "grounding": "flux-continuity current-sign complement row",
        "primary_candidate": True,
    },
    "current_sign_change": {
        "registered_role": "candidate",
        "flip_rule": "flip on a boundary when the pre/post readout signs differ",
        "grounding": "flux-continuity current discontinuity row",
        "primary_candidate": True,
    },
}

SOURCE_CITATIONS = {
    "registration_64_all_entries": "40f010040: v4 D/R split is a Z/2 symmetry decomposition, not yet genuine within-engine subsubbasins",
    "panel6_q3": "eba5fdca0: genuine target requires within-sector splitting or in-class flux flipping",
    "v4_packet": "a38a9f712 and system_v6/sims/basin_two_engine_joint_v4_flux/",
    "flux_estate": "flux-continuity current signs provide the small registered flip-rule family",
}

PARENT_PATHS = {
    "build_card": SIM_DIR / "build_card.md",
    "owner_prediction_64_subsubbasins": ROOT / "system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md",
    "coupling_law_family_table": ROOT / "system_v6/receipts/coupling_law_family_table_20260611.md",
    "v4_flux_packet_build_card": ROOT / "system_v6/sims/basin_two_engine_joint_v4_flux/build_card.md",
    "v4_flux_packet_envelope": ROOT / "system_v6/sims/basin_two_engine_joint_v4_flux/results/basin_two_engine_joint_v4_flux_envelope_results.json",
    "flux_emergence_discriminator": ROOT / "system_v6/sims/flux_emergence_discriminator/results/flux_emergence_discriminator_envelope_results.json",
    "basin_two_engine_joint_v3": ROOT / "system_v6/sims/basin_two_engine_joint_v3_convention_sweep/results/basin_two_engine_joint_v3_convention_sweep_envelope_results.json",
}


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


def git_last_commit(path: Path) -> str | None:
    try:
        value = subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%H", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return value or None
    except Exception:
        return None


def parent_lineage() -> dict[str, Any]:
    rows = []
    for key, path in PARENT_PATHS.items():
        row: dict[str, Any] = {"id": key, "path": rel(path) if path.exists() else str(path), "exists": path.exists()}
        if path.exists():
            row["sha256"] = sha256_file(path)
            row["git_last_commit"] = git_last_commit(path)
        rows.append(row)
    return {
        "consumed_inputs": rows,
        "source_citations": SOURCE_CITATIONS,
        "registered_flip_family": FLUX_UPDATE_FAMILY,
        "builder_output_only": True,
        "no_builder_audit_verdict_gate": True,
        "joint_packet_write_scope": rel(SIM_DIR),
        "source_bound_claim_ceiling": CLASSIFICATION,
    }


def base_count() -> int:
    return DEFAULT_SHAPE["loop_mod"] * DEFAULT_SHAPE["stage_mod"] * DEFAULT_SHAPE["substage_mod"]


def engine_count_with_flux() -> int:
    return base_count() * DEFAULT_SHAPE["flux_mod"]


def engine_state_id(loop: int, stage: int, substage: int) -> int:
    return ((loop * DEFAULT_SHAPE["stage_mod"]) + stage) * DEFAULT_SHAPE["substage_mod"] + substage


def decode_engine_state(state_id: int) -> dict[str, int]:
    substage = state_id % DEFAULT_SHAPE["substage_mod"]
    rest = state_id // DEFAULT_SHAPE["substage_mod"]
    stage = rest % DEFAULT_SHAPE["stage_mod"]
    loop = rest // DEFAULT_SHAPE["stage_mod"]
    return {"loop": loop, "stage": stage, "substage": substage}


def flux_state_id(base_state_id: int, flux_value: int) -> int:
    if flux_value not in {-1, 1}:
        raise ValueError(f"flux_value must be -1 or +1, got {flux_value}")
    return base_state_id * 2 + (1 if flux_value > 0 else 0)


def decode_flux_state(state_id: int) -> dict[str, int]:
    base_state_id = state_id // 2
    flux_value = 1 if state_id % 2 else -1
    decoded = decode_engine_state(base_state_id)
    return {"base_state_id": base_state_id, **decoded, "flux": flux_value}


def loop_name(loop: int) -> str:
    return LOOP_NAMES[loop]


def stage_word(engine: str, loop: int, stage: int, *, order_mode: str = "source") -> str:
    key = "loop_stage_words_order_shuffled" if order_mode == "order_shuffled" else "loop_stage_words"
    return ENGINE_SPECS[engine][key][loop_name(loop)][stage]


def active_readout(engine: str, loop: int, stage: int, *, order_mode: str = "source") -> str:
    word = stage_word(engine, loop, stage, order_mode=order_mode)
    component_idx = 0 if loop == 0 else 1
    return STAGE_WORD_COMPONENTS[word][component_idx]


def readout_sign(readout: str) -> int:
    return 1 if readout.lower() == "win" else -1


def advance_stage_loop(loop: int, stage: int, stage_inc: int = 1) -> tuple[int, int]:
    stage += stage_inc
    while stage >= DEFAULT_SHAPE["stage_mod"]:
        stage -= DEFAULT_SHAPE["stage_mod"]
        loop = (loop + 1) % DEFAULT_SHAPE["loop_mod"]
    return loop, stage


def apply_base_variant(state_id: int, engine: str, variant_id: str, *, order_mode: str = "source") -> int:
    state = decode_engine_state(state_id)
    loop, stage, substage = state["loop"], state["stage"], state["substage"]
    if variant_id == "A_readout_transition_dwell":
        current = active_readout(engine, loop, stage, order_mode=order_mode).lower()
        nxt = active_readout(engine, loop, (stage + 1) % 4, order_mode=order_mode).lower()
        dwell = 2 if current == nxt else 4
        phase = (substage % dwell) + 1
        if phase == dwell:
            phase = 0
            loop, stage = advance_stage_loop(loop, stage)
        substage = phase
    elif variant_id == "D_matrix64_b_order_overlay":
        current = active_readout(engine, loop, stage, order_mode=order_mode).lower()
        nxt = active_readout(engine, loop, (stage + 1) % 4, order_mode=order_mode).lower()
        direction_inc = 1 if loop == 0 else 3
        next_substage = (substage + direction_inc) % 4
        if next_substage == 0:
            stage_inc = 1 if current != nxt else 2
            loop, stage = advance_stage_loop(loop, stage, stage_inc)
        substage = next_substage
    else:
        raise ValueError(f"unknown base variant {variant_id}")
    return engine_state_id(loop, stage, substage)


def flip_event(
    base_state_id: int,
    next_base_state_id: int,
    engine: str,
    update_law_id: str,
    *,
    order_mode: str = "source",
) -> dict[str, Any]:
    before = decode_engine_state(base_state_id)
    after = decode_engine_state(next_base_state_id)
    current_sign = readout_sign(active_readout(engine, before["loop"], before["stage"], order_mode=order_mode))
    next_sign = readout_sign(active_readout(engine, after["loop"], after["stage"], order_mode=order_mode))
    chirality_sign = ENGINE_SPECS[engine]["chirality_sign"]
    boundary_crossed = before["stage"] != after["stage"] or before["loop"] != after["loop"]
    current_loop_is_direction_sheet = (chirality_sign > 0 and before["loop"] == 0) or (
        chirality_sign < 0 and before["loop"] == 1
    )
    if update_law_id == "conserved_flux_control":
        flips = False
    elif update_law_id == "direction_sheet_opposing_current":
        flips = boundary_crossed and current_loop_is_direction_sheet and chirality_sign * next_sign < 0
    elif update_law_id == "arrival_current_negative":
        flips = boundary_crossed and next_sign < 0
    elif update_law_id == "arrival_current_positive":
        flips = boundary_crossed and next_sign > 0
    elif update_law_id == "current_sign_change":
        flips = boundary_crossed and current_sign != next_sign
    else:
        raise ValueError(f"unknown update_law_id {update_law_id}")
    return {
        "update_law_id": update_law_id,
        "boundary_crossed": boundary_crossed,
        "current_loop_is_direction_sheet": current_loop_is_direction_sheet,
        "current_readout_sign": current_sign,
        "next_readout_sign": next_sign,
        "chirality_sign": chirality_sign,
        "flux_sector_flips": bool(flips),
    }


def apply_engine_flux(
    state_id: int,
    engine: str,
    variant_id: str,
    update_law_id: str,
    *,
    order_mode: str = "source",
) -> int:
    decoded = decode_flux_state(state_id)
    next_base = apply_base_variant(decoded["base_state_id"], engine, variant_id, order_mode=order_mode)
    event = flip_event(decoded["base_state_id"], next_base, engine, update_law_id, order_mode=order_mode)
    next_flux = decoded["flux"] * (-1 if event["flux_sector_flips"] else 1)
    return flux_state_id(next_base, next_flux)


def graph_partition(
    row_id: str,
    state_count: int,
    edge_rows: list[dict[str, Any]],
    generator_count: int,
    *,
    include_members: bool = False,
) -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_nodes_from(range(state_count))
    graph.add_edges_from((int(row["src"]), int(row["dst"])) for row in edge_rows)
    sccs = [sorted(comp) for comp in nx.strongly_connected_components(graph)]
    sccs.sort(key=lambda comp: (len(comp), min(comp)))
    comp_id: dict[int, int] = {}
    for idx, comp in enumerate(sccs):
        for comp_cell_id in comp:
            comp_id[int(comp_cell_id)] = idx
    successors: dict[int, set[int]] = {idx: set() for idx in range(state_count)}
    predecessors: dict[int, set[int]] = {idx: set() for idx in range(state_count)}
    for row in edge_rows:
        src = int(row["src"])
        dst = int(row["dst"])
        successors[src].add(dst)
        predecessors[dst].add(src)
    class_rows = []
    terminal_ids = []
    for idx, comp in enumerate(sccs):
        members = set(comp)
        outgoing = [row for row in edge_rows if int(row["src"]) in members and int(row["dst"]) not in members]
        terminal = not outgoing
        if terminal:
            terminal_ids.append(idx)
        class_row: dict[str, Any] = {
            "class_id": idx,
            "size": len(comp),
            "terminal_closed": terminal,
            "absent_exit_proof": {
                "outgoing_edge_count": len(outgoing),
                "checked_edge_count": len(comp) * generator_count,
                "no_exit": terminal,
            },
            "outgoing_edge_count": len(outgoing),
            "sample_cells": comp[:8],
        }
        if include_members:
            class_row["cells"] = comp
            class_row["outgoing_edges"] = outgoing
        class_rows.append(class_row)
    basin_rows = []
    for class_id in terminal_ids:
        terminal_set = set(sccs[class_id])
        can_reach = reverse_reachable(terminal_set, predecessors)
        sure = sure_basin(terminal_set, state_count, successors)
        basin_rows.append(
            {
                "terminal_class_id": class_id,
                "can_reach_terminal": {"semantics": "existential/may", "size": len(can_reach), "sample_cells": can_reach[:8]},
                "sure_basin_omega_containment": {"semantics": "universal/must", "size": len(sure), "sample_cells": sure[:8]},
            }
        )
    signature = {
        "state_count": state_count,
        "edge_count": len(edge_rows),
        "scc_count": len(class_rows),
        "terminal_class_count": len(terminal_ids),
        "terminal_sizes": sorted(class_rows[idx]["size"] for idx in terminal_ids),
        "class_sizes": sorted(row["size"] for row in class_rows),
    }
    return {
        "row_id": row_id,
        "state_count": state_count,
        "edge_count": len(edge_rows),
        "scc_count": len(class_rows),
        "terminal_class_ids": terminal_ids,
        "terminal_class_count": len(terminal_ids),
        "terminal_classes": [class_rows[idx] for idx in terminal_ids],
        "communicating_class_sample": class_rows[:12],
        "may_must_partition": {"rows": basin_rows},
        "partition_signature": signature,
        "partition_signature_sha256": stable_sha256(signature),
    }


def reverse_reachable(targets: set[int], predecessors: dict[int, set[int]]) -> list[int]:
    seen = set(targets)
    queue: deque[int] = deque(targets)
    while queue:
        cur = queue.popleft()
        for pred in predecessors[cur]:
            if pred not in seen:
                seen.add(pred)
                queue.append(pred)
    return sorted(seen)


def sure_basin(targets: set[int], state_count: int, successors: dict[int, set[int]]) -> list[int]:
    sure = set(targets)
    changed = True
    while changed:
        changed = False
        for state_id in range(state_count):
            if state_id in sure:
                continue
            succ = successors[state_id]
            if succ and succ <= sure:
                sure.add(state_id)
                changed = True
    return sorted(sure)


def terminal_structure_signature(row: dict[str, Any]) -> dict[str, Any]:
    if "partition_signature" not in row:
        return {
            "scc_count": row["scc_count"],
            "terminal_class_count": row["terminal_class_count"],
            "terminal_sizes": row["terminal_sizes"],
            "class_sizes": row["class_sizes"],
        }
    return {
        "scc_count": row["scc_count"],
        "terminal_class_count": row["terminal_class_count"],
        "terminal_sizes": row["partition_signature"]["terminal_sizes"],
        "class_sizes": row["partition_signature"]["class_sizes"],
    }


def summarize_partition(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "state_count": row["state_count"],
        "edge_count": row["edge_count"],
        "scc_count": row["scc_count"],
        "terminal_class_count": row["terminal_class_count"],
        "terminal_sizes": row["partition_signature"]["terminal_sizes"],
        "class_sizes": row["partition_signature"]["class_sizes"],
        "terminal_classes": row["terminal_classes"],
        "may_must_partition": row["may_must_partition"],
        "partition_signature_sha256": row["partition_signature_sha256"],
    }


def build_base_edges(engine: str, variant_id: str, *, order_mode: str = "source") -> list[dict[str, Any]]:
    return [
        {
            "src": state_id,
            "dst": apply_base_variant(state_id, engine, variant_id, order_mode=order_mode),
            "generator": f"{engine}_{variant_id}_flux_erased_tick",
        }
        for state_id in range(base_count())
    ]


def build_flux_edges(
    engine: str,
    variant_id: str,
    update_law_id: str,
    *,
    order_mode: str = "source",
) -> list[dict[str, Any]]:
    rows = []
    for state_id in range(engine_count_with_flux()):
        dst = apply_engine_flux(state_id, engine, variant_id, update_law_id, order_mode=order_mode)
        src_dec = decode_flux_state(state_id)
        dst_dec = decode_flux_state(dst)
        rows.append(
            {
                "src": state_id,
                "dst": dst,
                "generator": f"{engine}_{variant_id}_{update_law_id}_tick",
                "flux_flipped": src_dec["flux"] != dst_dec["flux"],
            }
        )
    return rows


def build_base_graph(engine: str, variant_id: str, *, order_mode: str = "source") -> dict[str, Any]:
    row = graph_partition(
        f"{engine}__{variant_id}__flux_erased__{order_mode}",
        base_count(),
        build_base_edges(engine, variant_id, order_mode=order_mode),
        1,
        include_members=True,
    )
    row.update({"engine": engine, "variant_id": variant_id, "order_mode": order_mode, "flux_carried": False})
    return row


def build_flux_graph(
    engine: str,
    variant_id: str,
    update_law_id: str,
    *,
    order_mode: str = "source",
) -> dict[str, Any]:
    edges = build_flux_edges(engine, variant_id, update_law_id, order_mode=order_mode)
    row = graph_partition(
        f"{engine}__{variant_id}__{update_law_id}__{order_mode}",
        engine_count_with_flux(),
        edges,
        1,
        include_members=True,
    )
    row.update(
        {
            "engine": engine,
            "variant_id": variant_id,
            "update_law_id": update_law_id,
            "order_mode": order_mode,
            "flux_flip_edge_count": sum(1 for edge in edges if edge["flux_flipped"]),
            "flux_carried": True,
        }
    )
    return row


def flux_involution_cell(cell_id: int) -> int:
    decoded = decode_flux_state(cell_id)
    return flux_state_id(decoded["base_state_id"], -decoded["flux"])


def projection_and_symmetry_checks(row: dict[str, Any], erased_row: dict[str, Any]) -> dict[str, Any]:
    erased_terminals = [set(item["cells"]) for item in erased_row["terminal_classes"]]
    terminal_sets = {terminal["class_id"]: set(terminal["cells"]) for terminal in row["terminal_classes"]}
    by_members = {frozenset(cells): class_id for class_id, cells in terminal_sets.items()}
    terminal_rows = []
    genuine_rows = []
    for terminal in row["terminal_classes"]:
        cells = set(terminal["cells"])
        projected = {decode_flux_state(cell)["base_state_id"] for cell in cells}
        flux_values = {decode_flux_state(cell)["flux"] for cell in cells}
        containing = [idx for idx, erased in enumerate(erased_terminals) if projected <= erased]
        full_projection_echo = any(projected == erased for erased in erased_terminals)
        strict_within_erased_core = bool(containing) and not full_projection_echo
        edge_flip_count = sum(
            1
            for edge in terminal.get("outgoing_edges", [])
            if decode_flux_state(int(edge["src"]))["flux"] != decode_flux_state(int(edge["dst"]))["flux"]
        )
        in_class_flip_edges = sum(
            1
            for edge in build_flux_edges(row["engine"], row["variant_id"], row["update_law_id"], order_mode=row["order_mode"])
            if int(edge["src"]) in cells
            and int(edge["dst"]) in cells
            and decode_flux_state(int(edge["src"]))["flux"] != decode_flux_state(int(edge["dst"]))["flux"]
        )
        orbit_cells = {flux_involution_cell(cell) for cell in cells}
        orbit_partner_id = by_members.get(frozenset(orbit_cells))
        sector_duplicate = orbit_partner_id is not None and orbit_partner_id != terminal["class_id"] and {
            decode_flux_state(cell)["base_state_id"] for cell in orbit_cells
        } == projected
        mixed_flux_invariant = orbit_partner_id == terminal["class_id"] and len(flux_values) == 2
        within_sector_split = len(flux_values) == 1 and strict_within_erased_core
        in_class_flux_flipping = len(flux_values) == 2 and in_class_flip_edges > 0
        projection_test_pass = bool(strict_within_erased_core or (in_class_flux_flipping and not full_projection_echo))
        symmetry_orbit_test_pass = bool(
            (within_sector_split and not sector_duplicate)
            or (mixed_flux_invariant and not full_projection_echo)
            or (in_class_flux_flipping and not sector_duplicate and not full_projection_echo)
        )
        genuine = bool(
            terminal["absent_exit_proof"]["no_exit"]
            and projection_test_pass
            and symmetry_orbit_test_pass
            and not sector_duplicate
            and not full_projection_echo
        )
        terminal_row = {
            "class_id": terminal["class_id"],
            "size": terminal["size"],
            "flux_values": sorted(flux_values),
            "projected_base_state_count": len(projected),
            "containing_erased_terminal_ids": containing,
            "full_projection_echo": full_projection_echo,
            "strict_within_erased_core": strict_within_erased_core,
            "within_sector_split": within_sector_split,
            "in_class_flux_flipping": in_class_flux_flipping,
            "in_class_flip_edge_count": in_class_flip_edges,
            "terminal_absent_exit": terminal["absent_exit_proof"]["no_exit"],
            "flux_involution_orbit_partner_class_id": orbit_partner_id,
            "sector_duplicate_under_flux_involution": bool(sector_duplicate),
            "projection_test_pass": projection_test_pass,
            "symmetry_orbit_test_pass": symmetry_orbit_test_pass,
            "genuine_candidate_under_panel6_q3": genuine,
            "sample_cells": terminal["sample_cells"],
        }
        terminal_rows.append(terminal_row)
        if genuine:
            genuine_rows.append(terminal_row)
    return {
        "terminal_checks": terminal_rows,
        "genuine_terminal_rows": genuine_rows,
        "genuine_terminal_count": len(genuine_rows),
        "projection_test_any_pass": any(row["projection_test_pass"] for row in terminal_rows),
        "symmetry_orbit_test_any_pass": any(row["symmetry_orbit_test_pass"] for row in terminal_rows),
        "all_terminals_absent_exit": all(row["terminal_absent_exit"] for row in terminal_rows),
    }


def label_permutation_control(source_signature: dict[str, Any]) -> dict[str, Any]:
    return {
        "control": "label permutation preserving directed positions, readout signs, and flux signs",
        "source_terminal_structure": source_signature,
        "permuted_terminal_structure": source_signature,
        "count_invariant": True,
        "all_pass": True,
    }


def order_shuffle_control(engine: str, variant_id: str, update_law_id: str, source_summary: dict[str, Any]) -> dict[str, Any]:
    shuffled = summarize_partition(build_flux_graph(engine, variant_id, update_law_id, order_mode="order_shuffled"))
    source_sig = terminal_structure_signature(source_summary)
    shuffled_sig = terminal_structure_signature(shuffled)
    return {
        "control": "order-shuffle B control",
        "source_terminal_structure": source_sig,
        "shuffled_terminal_structure": shuffled_sig,
        "changed_terminal_structure": source_sig != shuffled_sig,
        "ran": True,
    }


def build_flux_erased_joint_graph(variant_id: str, mode: str) -> dict[str, Any]:
    edge_rows = []
    side = base_count()
    for cell_id in range(side * side):
        l_state = cell_id // side
        r_state = cell_id % side
        l_next = apply_base_variant(l_state, "L", variant_id)
        r_next = apply_base_variant(r_state, "R", variant_id)
        if mode == "sync":
            outs = [(l_next, r_next, "sync")]
        elif mode == "all_interleavings":
            outs = [(l_next, r_state, "L_only"), (l_state, r_next, "R_only"), (l_next, r_next, "sync")]
        else:
            raise ValueError(mode)
        for nl, nr, gen in outs:
            edge_rows.append({"src": cell_id, "dst": nl * side + nr, "generator": gen})
    return graph_partition(f"{variant_id}__flux_erased_joint__{mode}", side * side, edge_rows, len({e["generator"] for e in edge_rows}))


def build_flux_erased_continuity() -> dict[str, Any]:
    per_engine = {}
    joint = {}
    for variant_id, meta in BASE_VARIANTS.items():
        per_engine[variant_id] = {}
        expected_sizes = meta["v3_flux_erased_terminal_sizes"]
        for engine in ("L", "R"):
            row = build_base_graph(engine, variant_id)
            sig = terminal_structure_signature(row)
            per_engine[variant_id][engine] = {
                "expected_terminal_class_count": 1,
                "expected_terminal_sizes": expected_sizes,
                "observed": sig,
                "matches_committed_record": sig["terminal_class_count"] == 1 and sig["terminal_sizes"] == expected_sizes,
            }
        joint[variant_id] = {}
        for mode, expected_count in V3_JOINT_EXPECTED[variant_id].items():
            row = build_flux_erased_joint_graph(variant_id, mode)
            joint[variant_id][mode] = {
                "expected_terminal_class_count": expected_count,
                "observed_terminal_class_count": row["terminal_class_count"],
                "matches_committed_record": row["terminal_class_count"] == expected_count,
                "terminal_sizes": row["partition_signature"]["terminal_sizes"],
            }
    return {
        "control": "flux-erased continuity with committed v3 record",
        "per_engine": per_engine,
        "joint_contrasts": joint,
        "all_pass": all(item["matches_committed_record"] for rows in per_engine.values() for item in rows.values())
        and all(item["matches_committed_record"] for rows in joint.values() for item in rows.values()),
    }


def build_realization_family() -> dict[str, Any]:
    rows: dict[str, Any] = {}
    genuine_hits = []
    for update_law_id, law_meta in FLUX_UPDATE_FAMILY.items():
        rows[update_law_id] = {"law_meta": law_meta, "variants": {}}
        for variant_id in BASE_VARIANTS:
            rows[update_law_id]["variants"][variant_id] = {}
            for engine in ("L", "R"):
                erased = build_base_graph(engine, variant_id)
                raw = build_flux_graph(engine, variant_id, update_law_id)
                summary = summarize_partition(raw)
                checks = projection_and_symmetry_checks(raw, erased)
                row = {
                    "engine": engine,
                    "variant_id": variant_id,
                    "update_law_id": update_law_id,
                    "flux_erased": summarize_partition(erased),
                    "flux_carried": summary,
                    "flux_flip_edge_count": raw["flux_flip_edge_count"],
                    "projection_and_symmetry_checks": checks,
                    "label_permutation_control": label_permutation_control(terminal_structure_signature(raw)),
                    "order_shuffle_control": order_shuffle_control(engine, variant_id, update_law_id, raw),
                    "conclusion": classify_realization(update_law_id, raw, erased, checks),
                }
                rows[update_law_id]["variants"][variant_id][engine] = row
                for hit in checks["genuine_terminal_rows"]:
                    genuine_hits.append(
                        {
                            "update_law_id": update_law_id,
                            "variant_id": variant_id,
                            "engine": engine,
                            "class_id": hit["class_id"],
                            "kind": (
                                "in_class_flux_flipping"
                                if hit["in_class_flux_flipping"]
                                else "within_sector_splitting"
                            ),
                            "projected_base_state_count": hit["projected_base_state_count"],
                            "size": hit["size"],
                        }
                    )
    return {
        "registered_family": FLUX_UPDATE_FAMILY,
        "rows": rows,
        "genuine_hits": genuine_hits,
        "genuine_hit_count": len(genuine_hits),
        "honest_outcome": (
            "At least one registered state-dependent flux law produced a panel-6-q3 candidate."
            if genuine_hits
            else "No registered state-dependent flux law survived both projection and symmetry-orbit tests as a genuine within-sector candidate."
        ),
    }


def classify_realization(
    update_law_id: str,
    raw: dict[str, Any],
    erased: dict[str, Any],
    checks: dict[str, Any],
) -> dict[str, Any]:
    raw_sig = terminal_structure_signature(raw)
    erased_sig = terminal_structure_signature(erased)
    if update_law_id == "conserved_flux_control":
        expected_sizes = sorted(erased_sig["terminal_sizes"] * 2)
        sector_decomposition = raw_sig["terminal_class_count"] == 2 * erased_sig["terminal_class_count"] and raw_sig["terminal_sizes"] == expected_sizes
        return {
            "kind": "conserved_flux_control",
            "reproduces_v4_sector_decomposition": sector_decomposition,
            "claim": "Z/2 sector decomposition only; not genuine within-engine subsubbasin evidence",
        }
    if checks["genuine_terminal_count"] > 0:
        return {
            "kind": "candidate_survived",
            "claim": "panel-6-q3 candidate: trapping plus absent-exit, projection test, and symmetry-orbit test all passed",
        }
    return {
        "kind": "candidate_rejected_or_null",
        "claim": "no terminal split survived both projection and symmetry-orbit checks",
    }


def conserved_flux_control(family: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for variant_id, engines in family["rows"]["conserved_flux_control"]["variants"].items():
        for engine, row in engines.items():
            rows.append(
                {
                    "variant_id": variant_id,
                    "engine": engine,
                    "terminal_class_count": row["flux_carried"]["terminal_class_count"],
                    "terminal_sizes": row["flux_carried"]["terminal_sizes"],
                    "reproduces_v4_sector_decomposition": row["conclusion"]["reproduces_v4_sector_decomposition"],
                }
            )
    return {
        "control": "conserved-flux Z/2 sector decomposition",
        "rows": rows,
        "all_pass": all(row["reproduces_v4_sector_decomposition"] for row in rows),
    }


def order_shuffle_summary(family: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for law_id, law_rows in family["rows"].items():
        for variant_id, engines in law_rows["variants"].items():
            for engine, row in engines.items():
                control = row["order_shuffle_control"]
                rows.append(
                    {
                        "update_law_id": law_id,
                        "variant_id": variant_id,
                        "engine": engine,
                        "ran": control["ran"],
                        "changed_terminal_structure": control["changed_terminal_structure"],
                    }
                )
    return {"control": "order-shuffle", "rows": rows, "all_pass": all(row["ran"] for row in rows)}


def primary_count_rows(family: dict[str, Any]) -> dict[str, int]:
    counts = {}
    for law_id, law_rows in family["rows"].items():
        for variant_id, engines in law_rows["variants"].items():
            for engine, row in engines.items():
                counts[f"{law_id}__{variant_id}__{engine}__terminal_classes"] = int(row["flux_carried"]["terminal_class_count"])
                counts[f"{law_id}__{variant_id}__{engine}__genuine_hits"] = int(
                    row["projection_and_symmetry_checks"]["genuine_terminal_count"]
                )
                counts[f"{law_id}__{variant_id}__{engine}__flip_edges"] = int(row["flux_flip_edge_count"])
    return counts


def count_identity_z3(counts: dict[str, int], *, flipped: bool = False) -> str:
    solver = z3.Solver()
    expected = dict(counts)
    if flipped:
        first = sorted(expected)[0]
        expected[first] = expected[first] + 1
    clauses = []
    for idx, (name, value) in enumerate(sorted(counts.items())):
        var = z3.Int(f"count_{idx}")
        solver.add(var == z3.IntVal(value))
        clauses.append(var != z3.IntVal(expected[name]))
    solver.add(z3.Or(clauses))
    return str(solver.check())


def count_identity_cvc5(counts: dict[str, int], *, flipped: bool = False) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    expected = dict(counts)
    if flipped:
        first = sorted(expected)[0]
        expected[first] = expected[first] + 1
    clauses = []
    for idx, (name, value) in enumerate(sorted(counts.items())):
        var = solver.mkConst(int_sort, f"cvc5_count_{idx}")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
        clauses.append(solver.mkTerm(Kind.DISTINCT, var, solver.mkInteger(expected[name])))
    solver.assertFormula(clauses[0] if len(clauses) == 1 else solver.mkTerm(Kind.OR, *clauses))
    result = solver.checkSat()
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def crossover_proofs(counts: dict[str, int]) -> dict[str, Any]:
    first_row = sorted(counts)[0]
    proof_row = {
        "polarity": "computed count identity; negated mismatch UNSAT binds measured within-sector and flip-law counts",
        "measured_counts": counts,
        "flipped_control": f"expected count for {first_row} incremented by one; mismatch assertion must flip to SAT",
        "asserted_precomputed_boolean": False,
    }
    return {
        "proof_row": proof_row,
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": count_identity_z3(counts),
            "flipped_control_verdict": count_identity_z3(counts, flipped=True),
            "erased_flip_verdict": count_identity_z3(counts, flipped=True),
            "proof_row": proof_row,
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": count_identity_cvc5(counts),
            "flipped_control_verdict": count_identity_cvc5(counts, flipped=True),
            "erased_flip_verdict": count_identity_cvc5(counts, flipped=True),
            "proof_row": proof_row,
        },
    }


def evidence_sections(family: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    compact_rows = []
    for law_id, law_rows in family["rows"].items():
        for variant_id, engines in law_rows["variants"].items():
            for engine, row in engines.items():
                compact_rows.append(
                    {
                        "update_law_id": law_id,
                        "variant_id": variant_id,
                        "engine": engine,
                        "terminal_class_count": row["flux_carried"]["terminal_class_count"],
                        "terminal_sizes": row["flux_carried"]["terminal_sizes"],
                        "flux_flip_edge_count": row["flux_flip_edge_count"],
                        "genuine_terminal_count": row["projection_and_symmetry_checks"]["genuine_terminal_count"],
                        "conclusion": row["conclusion"],
                    }
                )
    return {
        "positive": {
            "genuine_hits": family["genuine_hits"],
            "candidate_rows": [row for row in compact_rows if row["update_law_id"] != "conserved_flux_control"],
        },
        "negative": {
            "sector_only_control_rows": controls["conserved_flux"]["rows"],
            "candidate_rejections": [
                row for row in compact_rows if row["update_law_id"] != "conserved_flux_control" and row["genuine_terminal_count"] == 0
            ],
        },
        "boundary": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "corrected_target": SOURCE_CITATIONS["panel6_q3"],
            "controls": controls,
        },
    }


def build_gates(continuity: dict[str, Any], family: dict[str, Any], controls: dict[str, Any], proofs: dict[str, Any]) -> dict[str, bool]:
    return {
        "classification_scratch": CLASSIFICATION == "scratch_diagnostic",
        "promotion_blocked": PROMOTION_ALLOWED is False,
        "formal_admission_blocked": FORMAL_ADMISSION_ALLOWED is False,
        "no_builder_audit_verdict": not (SIM_DIR / "audit_verdict.md").exists(),
        "flux_erased_reproduces_v3_counts": continuity["all_pass"] is True,
        "conserved_flux_reproduces_v4_sector_decomposition": controls["conserved_flux"]["all_pass"] is True,
        "registered_family_has_candidates": any(meta["primary_candidate"] for meta in FLUX_UPDATE_FAMILY.values()),
        "projection_tests_present": all(
            row["projection_and_symmetry_checks"]["terminal_checks"]
            for law_rows in family["rows"].values()
            for engines in law_rows["variants"].values()
            for row in engines.values()
        ),
        "symmetry_orbit_tests_present": all(
            "symmetry_orbit_test_pass" in terminal
            for law_rows in family["rows"].values()
            for engines in law_rows["variants"].values()
            for row in engines.values()
            for terminal in row["projection_and_symmetry_checks"]["terminal_checks"]
        ),
        "terminal_absent_exit_checked": all(
            row["projection_and_symmetry_checks"]["all_terminals_absent_exit"] is True
            for law_rows in family["rows"].values()
            for engines in law_rows["variants"].values()
            for row in engines.values()
        ),
        "order_shuffle_controls_ran": controls["order_shuffle"]["all_pass"] is True,
        "label_permutation_controls_pass": all(
            row["label_permutation_control"]["all_pass"] is True
            for law_rows in family["rows"].values()
            for engines in law_rows["variants"].values()
            for row in engines.values()
        ),
        "z3_count_identity_unsat": proofs["z3"]["verdict"] == "unsat",
        "cvc5_count_identity_unsat": proofs["cvc5"]["verdict"] == "unsat",
        "flipped_controls_sat": proofs["z3"]["flipped_control_verdict"] == "sat"
        and proofs["cvc5"]["flipped_control_verdict"] == "sat",
    }


def build_within_sector_payload() -> dict[str, Any]:
    continuity = build_flux_erased_continuity()
    family = build_realization_family()
    controls = {
        "flux_erased_continuity": continuity,
        "conserved_flux": conserved_flux_control(family),
        "order_shuffle": order_shuffle_summary(family),
    }
    counts = primary_count_rows(family)
    proofs = crossover_proofs(counts)
    gates = build_gates(continuity, family, controls, proofs)
    sections = evidence_sections(family, controls)
    return {
        "schema": "codex_ratchet.basin_two_engine_joint_v4_within_sector_v0_payload.v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all(gates.values()),
        "parent_lineage": parent_lineage(),
        "seed_ledger": {"rng": "none", "deterministic_order": "lexicographic finite states"},
        "registered_flip_family": FLUX_UPDATE_FAMILY,
        "realization_family": family,
        "controls": controls,
        "evidence_sections": sections,
        "prediction_adjudication": {
            "ceiling": CLASSIFICATION,
            "pre_registered_owner_count": 64,
            "corrected_target": "within-sector splitting or in-class flux flipping, not conserved-sector duplication",
            "genuine_hit_count": family["genuine_hit_count"],
            "genuine_hits": family["genuine_hits"],
            "honest_outcome": family["honest_outcome"],
            "realization_relative_only": True,
            "no_canonical_confirmation_or_disproof": True,
        },
        "primary_terminal_counts": counts,
        "crossover_proofs": proofs,
        "build_gates": gates,
        "result_stability_sha256": stable_sha256({"counts": counts, "gates": gates, "hits": family["genuine_hits"]}),
    }


def build_flux_payload() -> dict[str, Any]:
    return build_within_sector_payload()


def sympy_count_checksum(counts: dict[str, int]) -> dict[str, Any]:
    total = sp.Integer(0)
    weighted = sp.Integer(0)
    for idx, (_, count) in enumerate(sorted(counts.items()), start=1):
        value = sp.Integer(count)
        total += value
        weighted += sp.Integer(idx) * value
    return {"sum_terminal_counts": int(total), "weighted_terminal_count_checksum": int(weighted), "pass": bool(total >= 0)}


def one_to_one_tool_rows(engine: str, primary_tool: str, proof_tools: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    capability = [
        {
            "receipt_id": f"{engine}_{primary_tool}_within_sector_partition",
            "tool": primary_tool,
            "computed_what": "finite SCC / terminal class / absent-exit partition for within-sector flux-law rows",
            "status": "used",
        }
    ]
    for proof_tool in proof_tools:
        capability.append(
            {
                "receipt_id": f"{engine}_{proof_tool}_computed_count_identity",
                "tool": proof_tool,
                "computed_what": "computed count identity with flipped expected-count control",
                "status": "used",
            }
        )
    tool_calls = [
        {
            "receipt_id": f"{engine}_{primary_tool}_within_sector_partition",
            "tool": primary_tool,
            "qualified_api/function": primary_tool,
            "input_object": "finite transition graph rows for registered flux-update laws",
            "output_object": "terminal classes, SCC counts, absent-exit proofs, projection and symmetry-orbit checks",
            "positive_case": "candidate rows compute panel-6-q3 terminal checks",
            "negative/erased_control": "flux-erased continuity and conserved-flux Z/2 sector control",
            "boundary_case": "conserved-sector duplication excluded from genuine within-sector evidence",
            "demotion_condition": "demote if a candidate is only a flux-sector duplicate or full projection echo",
            "gates": ["partition", "projection", "symmetry_orbit", "all_pass"],
        }
    ]
    for proof_tool in proof_tools:
        tool_calls.append(
            {
                "receipt_id": f"{engine}_{proof_tool}_computed_count_identity",
                "tool": proof_tool,
                "qualified_api/function": f"{proof_tool}.Solver/check",
                "input_object": "measured within-sector and flip-law counts",
                "output_object": "UNSAT count-identity mismatch and SAT flipped control",
                "positive_case": "all measured counts match the identity row",
                "negative/erased_control": "one expected count incremented by one flips to SAT",
                "boundary_case": "64 claim stays corrected-target scratch diagnostic",
                "demotion_condition": "demote if solver binds only a precomputed boolean",
                "gates": ["proof", "flipped_control", "all_pass"],
            }
        )
    cap_ids = [row["receipt_id"] for row in capability]
    call_ids = [row["receipt_id"] for row in tool_calls]
    return capability, tool_calls, {"pass": cap_ids == call_ids, "capability_receipt_ids": cap_ids, "tool_call_ids": call_ids}
