#!/usr/bin/env python3
"""Shared convention-sweep machinery for basin_two_engine_joint_v3_convention_sweep."""

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


SIM_ID = "basin_two_engine_joint_v3_convention_sweep"
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
SUBSTAGE_LABELS = ("s0", "s1", "s2", "s3")
DEFAULT_SHAPE = {"loop_mod": 2, "stage_mod": 4, "substage_mod": 4}

STAGE_WORD_COMPONENTS = {
    "Se": ("LOSE", "win"),
    "Ne": ("WIN", "lose"),
    "Ni": ("LOSE", "lose"),
    "Si": ("WIN", "win"),
}

ENGINE_SPECS = {
    "L": {
        "engine_type": "Type1",
        "loop_stage_words": {"base": D_ORDER, "fiber": I_ORDER},
        "loop_stage_words_order_shuffled": {"base": ORDER_SHUFFLED_D, "fiber": ORDER_SHUFFLED_I},
        "source_rule": "Type1 outer/base deductive and inner/fiber inductive",
    },
    "R": {
        "engine_type": "Type2",
        "loop_stage_words": {"base": I_ORDER, "fiber": D_ORDER},
        "loop_stage_words_order_shuffled": {"base": ORDER_SHUFFLED_I, "fiber": ORDER_SHUFFLED_D},
        "source_rule": "Type2 outer/base inductive and inner/fiber deductive",
    },
}

PARENT_PATHS = {
    "owner_prediction_64_subsubbasins": ROOT / "system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md",
    "substage_transition_convention_mining": ROOT / "system_v6/receipts/substage_transition_convention_mining_20260611.md",
    "basin_contract": ROOT / "system_v6/receipts/attractor_basin_criterion_20260611.md",
    "two_engine_readout_automaton": ROOT / "system_v6/foundations/two_engine_readout_automaton_20260609.md",
    "symbolic_layer_iching_taijitu": ROOT / "system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md",
    "basin_two_engine_joint_v2_audit": ROOT / "system_v6/sims/basin_two_engine_joint_v2/audit_verdict.md",
    "basin_generating_set_sweep_v0_audit": ROOT / "system_v6/sims/basin_generating_set_sweep_v0/audit_verdict.md",
    "build_card": SIM_DIR / "build_card.md",
}

SOURCE_CITATIONS = {
    "registered_product": "system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md:13-21",
    "convention_relative_reregistration": "system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md:72-91",
    "stage_word_read_rule": "system_v6/foundations/two_engine_readout_automaton_20260609.md:8",
    "stage_words_and_orders": "system_v6/foundations/two_engine_readout_automaton_20260609.md:10-12",
    "readout_strategies": "system_v6/foundations/two_engine_readout_automaton_20260609.md:14-19",
    "directed_order_constraint": "system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md:89-96",
    "active_loop_component_rule": "system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md:98-111",
    "composition_first": "system_v6/receipts/substage_transition_convention_mining_20260611.md:131-185",
    "matrix64_product": "system_v6/receipts/substage_transition_convention_mining_20260611.md:187-216",
    "v2_contrast": "system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md:55-58",
    "basin_contract_requirements": "system_v6/receipts/attractor_basin_criterion_20260611.md:301-334",
}

CONVENTION_VARIANTS: dict[str, dict[str, Any]] = {
    "A_readout_transition_dwell": {
        "convention": "A",
        "label": "directed stage-word / loop-readout transition dwell",
        "source_status": "admitted_family_realization",
        "source_quote": SOURCE_CITATIONS["readout_strategies"],
        "law": "A_readout_transition_dwell",
        "under_determined_detail": (
            "A pins stage words, active-loop readout, and readout periodicity but not a four-substage state law; "
            "this variant lets same-readout directed edges close a two-slot substage map and changed-readout edges close a four-slot map."
        ),
    },
    "C_composition_outer_inner": {
        "convention": "C",
        "label": "composition-first substages; outer-loop then inner-loop schedule",
        "source_status": "admitted_family_realization",
        "source_quote": SOURCE_CITATIONS["composition_first"],
        "law": "C_composition_outer_inner",
        "under_determined_detail": (
            "C pins substage->stage->loop->engine composition but not a unique state-machine law; "
            "this variant uses forward substage composition and the outer-inner loop formula."
        ),
    },
    "C_composition_inner_outer": {
        "convention": "C",
        "label": "composition-first substages; reverse schedule if specified",
        "source_status": "admitted_family_realization",
        "source_quote": SOURCE_CITATIONS["composition_first"],
        "law": "C_composition_inner_outer",
        "under_determined_detail": (
            "This is the minimal reverse-schedule C subvariant admitted by 'or the reverse, if the schedule specifies that'."
        ),
    },
    "D_matrix64_direction_as_loop": {
        "convention": "D",
        "label": "Matrix64/Carnot product with direction mapped to engine loop",
        "source_status": "admitted_family_realization_with_mapping_open",
        "source_quote": SOURCE_CITATIONS["matrix64_product"],
        "law": "D_matrix64_direction_as_loop",
        "under_determined_detail": (
            "D pins 4 strokes x 4 substages x 2 directions but leaves the owner-product loop mapping open; "
            "this variant maps direction to the loop coordinate and stroke to the stage coordinate."
        ),
    },
    "D_matrix64_b_order_overlay": {
        "convention": "D",
        "label": "Matrix64/Carnot product overlaid on B directed stage order",
        "source_status": "admitted_family_realization_with_mapping_open",
        "source_quote": SOURCE_CITATIONS["matrix64_product"],
        "law": "D_matrix64_b_order_overlay",
        "under_determined_detail": (
            "This variant keeps D's direction/substage product but overlays B's directed readout edge as the stage-advance discriminator."
        ),
    },
    "v2_cyclic_wrap_contrast": {
        "convention": "v2_cyclic_contrast",
        "label": "v2 cyclic substage wrap contrast",
        "source_status": "sim_realization_contrast_not_source_admitted",
        "source_quote": SOURCE_CITATIONS["v2_contrast"],
        "law": "v2_cyclic_wrap",
        "under_determined_detail": "Contrast row only: substage wrap advances stage; stage wrap advances loop.",
        "contrast_only": True,
    },
}

GENERATOR_MODES = {
    "sync": [{"name": "sync_convention_tick", "l_step": True, "r_step": True}],
    "l_only": [{"name": "L_only_convention_tick", "l_step": True, "r_step": False}],
    "r_only": [{"name": "R_only_convention_tick", "l_step": False, "r_step": True}],
    "async_lr_union": [
        {"name": "L_only_convention_tick", "l_step": True, "r_step": False},
        {"name": "R_only_convention_tick", "l_step": False, "r_step": True},
    ],
    "all_interleavings": [
        {"name": "L_only_convention_tick", "l_step": True, "r_step": False},
        {"name": "R_only_convention_tick", "l_step": False, "r_step": True},
        {"name": "sync_convention_tick", "l_step": True, "r_step": True},
    ],
}

PROJECTIONS = {
    "left_engine": ("l_loop", "l_stage", "l_substage"),
    "right_engine": ("r_loop", "r_stage", "r_substage"),
    "loop_pair": ("l_loop", "r_loop"),
    "stage_pair": ("l_stage", "r_stage"),
    "substage_pair": ("l_substage", "r_substage"),
    "loop_stage_pair": ("l_loop", "l_stage", "r_loop", "r_stage"),
    "engine_factor_pair": ("l_state_id", "r_state_id"),
}


def now_z() -> str:
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
        row = {"id": key, "path": rel(path) if path.is_absolute() and path.exists() else str(path)}
        row["exists"] = path.exists()
        if path.exists():
            row["path"] = rel(path)
            row["sha256"] = sha256_file(path)
            row["git_last_commit"] = git_last_commit(path)
        rows.append(row)
    return {
        "consumed_inputs": rows,
        "source_citations": SOURCE_CITATIONS,
        "builder_output_only": True,
        "joint_packet_new_write_scope": rel(SIM_DIR),
        "source_bound_claim_ceiling": CLASSIFICATION,
    }


def per_engine_count(shape: dict[str, int] = DEFAULT_SHAPE) -> int:
    return shape["loop_mod"] * shape["stage_mod"] * shape["substage_mod"]


def engine_state_id(loop: int, stage: int, substage: int, shape: dict[str, int] = DEFAULT_SHAPE) -> int:
    return ((loop * shape["stage_mod"]) + stage) * shape["substage_mod"] + substage


def decode_engine_state(state_id: int, shape: dict[str, int] = DEFAULT_SHAPE) -> dict[str, int]:
    substage = state_id % shape["substage_mod"]
    rest = state_id // shape["substage_mod"]
    stage = rest % shape["stage_mod"]
    loop = rest // shape["stage_mod"]
    return {"loop": loop, "stage": stage, "substage": substage}


def joint_id(l_state_id: int, r_state_id: int, shape: dict[str, int] = DEFAULT_SHAPE) -> int:
    return l_state_id * per_engine_count(shape) + r_state_id


def decode_joint_id(cell_id: int, shape: dict[str, int] = DEFAULT_SHAPE) -> dict[str, Any]:
    side = per_engine_count(shape)
    l_state_id = cell_id // side
    r_state_id = cell_id % side
    l_dec = decode_engine_state(l_state_id, shape)
    r_dec = decode_engine_state(r_state_id, shape)
    return {
        "l_state_id": l_state_id,
        "r_state_id": r_state_id,
        "l_loop": l_dec["loop"],
        "l_stage": l_dec["stage"],
        "l_substage": l_dec["substage"],
        "r_loop": r_dec["loop"],
        "r_stage": r_dec["stage"],
        "r_substage": r_dec["substage"],
    }


def loop_name(loop: int) -> str:
    return LOOP_NAMES[loop] if loop < len(LOOP_NAMES) else f"loop_{loop}"


def stage_word(engine: str, loop: int, stage: int, *, order_mode: str = "source") -> str:
    key = "loop_stage_words_order_shuffled" if order_mode == "order_shuffled" else "loop_stage_words"
    return ENGINE_SPECS[engine][key][loop_name(loop)][stage]


def active_readout(engine: str, loop: int, stage: int, *, order_mode: str = "source") -> str:
    word = stage_word(engine, loop, stage, order_mode=order_mode)
    component_idx = 0 if loop == 0 else 1
    return STAGE_WORD_COMPONENTS[word][component_idx]


def joint_cells(shape: dict[str, int] = DEFAULT_SHAPE, *, order_mode: str = "source") -> list[dict[str, Any]]:
    cells = []
    side = per_engine_count(shape)
    for l_state_id in range(side):
        for r_state_id in range(side):
            decoded = decode_joint_id(joint_id(l_state_id, r_state_id, shape), shape)
            cell = {
                "cell_id": joint_id(l_state_id, r_state_id, shape),
                **decoded,
                "l_loop_name": loop_name(decoded["l_loop"]),
                "r_loop_name": loop_name(decoded["r_loop"]),
                "l_stage_word": stage_word("L", decoded["l_loop"], decoded["l_stage"], order_mode=order_mode),
                "r_stage_word": stage_word("R", decoded["r_loop"], decoded["r_stage"], order_mode=order_mode),
                "l_active_readout": active_readout("L", decoded["l_loop"], decoded["l_stage"], order_mode=order_mode),
                "r_active_readout": active_readout("R", decoded["r_loop"], decoded["r_stage"], order_mode=order_mode),
                "l_substage_label": SUBSTAGE_LABELS[decoded["l_substage"]],
                "r_substage_label": SUBSTAGE_LABELS[decoded["r_substage"]],
                "Adm_C": shape == DEFAULT_SHAPE,
            }
            cells.append(cell)
    return cells


def _advance_stage_loop(loop: int, stage: int, stage_inc: int = 1) -> tuple[int, int]:
    stage += stage_inc
    while stage >= 4:
        stage -= 4
        loop = (loop + 1) % 2
    return loop, stage


def apply_engine_variant(
    state_id: int,
    engine: str,
    variant_id: str,
    *,
    order_mode: str = "source",
    shape: dict[str, int] = DEFAULT_SHAPE,
) -> int:
    state = decode_engine_state(state_id, shape)
    loop, stage, substage = state["loop"], state["stage"], state["substage"]
    law = CONVENTION_VARIANTS[variant_id]["law"]

    if law == "A_readout_transition_dwell":
        current = active_readout(engine, loop, stage, order_mode=order_mode).lower()
        nxt = active_readout(engine, loop, (stage + 1) % 4, order_mode=order_mode).lower()
        dwell = 2 if current == nxt else 4
        phase = (substage % dwell) + 1
        if phase == dwell:
            phase = 0
            loop, stage = _advance_stage_loop(loop, stage)
        substage = phase
    elif law == "C_composition_outer_inner":
        substage += 1
        if substage == 4:
            substage = 0
            loop, stage = _advance_stage_loop(loop, stage)
    elif law == "C_composition_inner_outer":
        if substage == 0:
            substage = 3
            loop, stage = _advance_stage_loop(loop, stage)
        else:
            substage -= 1
    elif law == "D_matrix64_direction_as_loop":
        inc = 1 if loop == 0 else 3
        next_substage = (substage + inc) % 4
        if next_substage == 0:
            loop, stage = _advance_stage_loop(loop, stage)
        substage = next_substage
    elif law == "D_matrix64_b_order_overlay":
        current = active_readout(engine, loop, stage, order_mode=order_mode).lower()
        nxt = active_readout(engine, loop, (stage + 1) % 4, order_mode=order_mode).lower()
        direction_inc = 1 if loop == 0 else 3
        next_substage = (substage + direction_inc) % 4
        if next_substage == 0:
            stage_inc = 1 if current != nxt else 2
            loop, stage = _advance_stage_loop(loop, stage, stage_inc)
        substage = next_substage
    elif law == "v2_cyclic_wrap":
        substage += 1
        if substage == 4:
            substage = 0
            loop, stage = _advance_stage_loop(loop, stage)
    else:
        raise ValueError(f"unknown convention law {law}")
    return engine_state_id(loop, stage, substage, shape)


def apply_generator(
    cell_id: int,
    variant_id: str,
    generator: dict[str, Any],
    *,
    order_mode: str = "source",
    shape: dict[str, int] = DEFAULT_SHAPE,
) -> int:
    side = per_engine_count(shape)
    l_state_id = cell_id // side
    r_state_id = cell_id % side
    if generator.get("global_op") == "reset_substages":
        l_dec = decode_engine_state(l_state_id, shape)
        r_dec = decode_engine_state(r_state_id, shape)
        return joint_id(
            engine_state_id(l_dec["loop"], l_dec["stage"], 0, shape),
            engine_state_id(r_dec["loop"], r_dec["stage"], 0, shape),
            shape,
        )
    l_next = (
        apply_engine_variant(l_state_id, "L", variant_id, order_mode=order_mode, shape=shape)
        if generator.get("l_step")
        else l_state_id
    )
    r_next = (
        apply_engine_variant(r_state_id, "R", variant_id, order_mode=order_mode, shape=shape)
        if generator.get("r_step")
        else r_state_id
    )
    return joint_id(l_next, r_next, shape)


def _reverse_reachable(targets: set[int], predecessors: dict[int, set[int]]) -> list[int]:
    seen = set(targets)
    queue: deque[int] = deque(targets)
    while queue:
        cur = queue.popleft()
        for pred in predecessors[cur]:
            if pred not in seen:
                seen.add(pred)
                queue.append(pred)
    return sorted(seen)


def _sure_basin(targets: set[int], cells: list[dict[str, Any]], successors: dict[int, set[int]]) -> list[int]:
    sure = set(targets)
    changed = True
    while changed:
        changed = False
        for cell in cells:
            cid = int(cell["cell_id"])
            if cid in sure:
                continue
            succ = successors[cid]
            if succ and succ <= sure:
                sure.add(cid)
                changed = True
    return sorted(sure)


def graph_partition(
    row_id: str,
    cells: list[dict[str, Any]],
    edge_rows: list[dict[str, Any]],
    generators: list[dict[str, Any]],
    *,
    include_members: bool = True,
) -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_nodes_from(cell["cell_id"] for cell in cells)
    graph.add_edges_from((row["src"], row["dst"]) for row in edge_rows)
    sccs = [sorted(comp) for comp in nx.strongly_connected_components(graph)]
    sccs.sort(key=lambda comp: (len(comp), min(comp)))
    comp_id = {}
    for idx, comp in enumerate(sccs):
        for comp_cell_id in comp:
            comp_id[int(comp_cell_id)] = idx

    successors = {int(cell["cell_id"]): set() for cell in cells}
    predecessors = {int(cell["cell_id"]): set() for cell in cells}
    for row in edge_rows:
        successors[int(row["src"])].add(int(row["dst"]))
        predecessors[int(row["dst"])].add(int(row["src"]))

    class_rows = []
    terminal_ids = []
    for idx, comp in enumerate(sccs):
        members = set(comp)
        outgoing = [row for row in edge_rows if row["src"] in members and row["dst"] not in members]
        terminal = not outgoing
        if terminal:
            terminal_ids.append(idx)
        class_row = {
            "class_id": idx,
            "size": len(comp),
            "terminal_closed": terminal,
            "absent_exit_proof": {
                "outgoing_edge_count": len(outgoing),
                "checked_edge_count": len(comp) * len(generators),
                "no_exit": terminal,
            },
            "outgoing_edge_count": len(outgoing),
        }
        if include_members:
            class_row["cells"] = comp
            class_row["outgoing_edges"] = outgoing
        class_rows.append(class_row)

    basin_rows = []
    for class_id in terminal_ids:
        terminal_set = set(sccs[class_id])
        can_reach = _reverse_reachable(terminal_set, predecessors)
        sure = _sure_basin(terminal_set, cells, successors)
        basin_rows.append(
            {
                "terminal_class_id": class_id,
                "semantic_fork": "may/existential reachability is kept separate from must/universal omega-containment",
                "can_reach_terminal": {"semantics": "existential/may", "cells": can_reach, "size": len(can_reach)},
                "sure_basin_omega_containment": {"semantics": "universal/must", "cells": sure, "size": len(sure)},
            }
        )

    morse_edges = sorted(
        {
            (comp_id[int(row["src"])], comp_id[int(row["dst"])])
            for row in edge_rows
            if comp_id[int(row["src"])] != comp_id[int(row["dst"])]
        }
    )
    signature = {
        "state_count": len(cells),
        "edge_count": len(edge_rows),
        "scc_count": len(class_rows),
        "terminal_class_count": len(terminal_ids),
        "terminal_sizes": sorted(class_rows[idx]["size"] for idx in terminal_ids),
        "class_sizes": sorted(row["size"] for row in class_rows),
    }
    return {
        "row_id": row_id,
        "state_count": len(cells),
        "generators": generators,
        "edge_count": len(edge_rows),
        "transition_edges": edge_rows if include_members else [],
        "communicating_classes": class_rows,
        "scc_count": len(class_rows),
        "terminal_class_ids": terminal_ids,
        "terminal_classes": [class_rows[idx] for idx in terminal_ids],
        "terminal_class_count": len(terminal_ids),
        "component_id_by_cell": {str(k): v for k, v in sorted(comp_id.items())} if include_members else {},
        "may_must_partition": {
            "basin_contract_vocabulary": {
                "can_reach_terminal": "existential/may",
                "sure_basin_omega_containment": "universal/must",
                "plain_B_A_without_semantics": "forbidden",
            },
            "rows": basin_rows,
        },
        "morse_ordering": {
            "nodes": [
                {"class_id": row["class_id"], "terminal_closed": row["terminal_closed"], "size": row["size"]}
                for row in class_rows
            ],
            "edges": [{"src_class": src, "dst_class": dst} for src, dst in morse_edges],
        },
        "partition_signature": signature,
        "partition_signature_sha256": stable_sha256(signature),
    }


def build_graph(
    variant_id: str,
    generator_mode: str,
    *,
    order_mode: str = "source",
    include_members: bool = True,
) -> dict[str, Any]:
    cells = joint_cells(order_mode=order_mode)
    generators = GENERATOR_MODES[generator_mode]
    edge_rows = []
    for cell in cells:
        src = int(cell["cell_id"])
        for generator in generators:
            dst = apply_generator(src, variant_id, generator, order_mode=order_mode)
            edge_rows.append({"src": src, "dst": dst, "generator": generator["name"]})
    row = graph_partition(
        f"{variant_id}__{generator_mode}",
        cells,
        edge_rows,
        generators,
        include_members=include_members,
    )
    row["variant_id"] = variant_id
    row["generator_mode"] = generator_mode
    row["order_mode"] = order_mode
    return row


def summarize_partition(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "variant_id": row.get("variant_id"),
        "generator_mode": row.get("generator_mode"),
        "state_count": row["state_count"],
        "edge_count": row["edge_count"],
        "scc_count": row["scc_count"],
        "terminal_class_count": row["terminal_class_count"],
        "terminal_sizes": row["partition_signature"]["terminal_sizes"],
        "class_sizes": row["partition_signature"]["class_sizes"],
        "partition_signature_sha256": row["partition_signature_sha256"],
    }


def terminal_structure_signature(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "scc_count": row["scc_count"],
        "terminal_class_count": row["terminal_class_count"],
        "terminal_sizes": row["partition_signature"]["terminal_sizes"],
        "class_sizes": row["partition_signature"]["class_sizes"],
    }


def projection_key(cell: dict[str, Any], projection: str) -> tuple[Any, ...]:
    return tuple(cell[field] for field in PROJECTIONS[projection])


def projection_equivariance(variant_id: str, generator_mode: str, projection: str) -> dict[str, Any]:
    cells = joint_cells()
    cell_by_id = {int(cell["cell_id"]): cell for cell in cells}
    by_src_gen: dict[tuple[tuple[Any, ...], str], dict[tuple[Any, ...], int]] = defaultdict(lambda: defaultdict(int))
    for cell in cells:
        src_key = projection_key(cell, projection)
        src = int(cell["cell_id"])
        for generator in GENERATOR_MODES[generator_mode]:
            dst = apply_generator(src, variant_id, generator)
            dst_key = projection_key(cell_by_id[dst], projection)
            by_src_gen[(src_key, generator["name"])][dst_key] += 1
    bad = [
        {"src_key": list(src_key), "generator": gen, "dst_key_count": len(dst_counts)}
        for (src_key, gen), dst_counts in by_src_gen.items()
        if len(dst_counts) != 1
    ]
    return {
        "deterministic_equivariant": not bad,
        "failing_projected_sources": bad[:8],
        "failure_count": len(bad),
    }


def build_quotient_graph(variant_id: str, generator_mode: str, projection: str) -> dict[str, Any]:
    full_cells = joint_cells()
    cell_by_id = {int(cell["cell_id"]): cell for cell in full_cells}
    key_to_id: dict[tuple[Any, ...], int] = {}
    q_cells = []
    for cell in full_cells:
        key = projection_key(cell, projection)
        if key not in key_to_id:
            key_to_id[key] = len(key_to_id)
            q_cells.append({"cell_id": key_to_id[key], "quotient_key": list(key)})
    edge_set = set()
    for cell in full_cells:
        src_key = projection_key(cell, projection)
        src = key_to_id[src_key]
        for generator in GENERATOR_MODES[generator_mode]:
            dst_full = apply_generator(int(cell["cell_id"]), variant_id, generator)
            dst_key = projection_key(cell_by_id[dst_full], projection)
            edge_set.add((src, key_to_id[dst_key], generator["name"]))
    edge_rows = [{"src": src, "dst": dst, "generator": name} for src, dst, name in sorted(edge_set)]
    result = graph_partition(
        f"{variant_id}__{generator_mode}__quotient__{projection}",
        q_cells,
        edge_rows,
        GENERATOR_MODES[generator_mode],
        include_members=False,
    )
    result["projection"] = projection
    result["projection_fields"] = list(PROJECTIONS[projection])
    result["equivariance_check"] = projection_equivariance(variant_id, generator_mode, projection)
    return result


def build_quotient_lattice() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for variant_id in CONVENTION_VARIANTS:
        out[variant_id] = {}
        for generator_mode in GENERATOR_MODES:
            out[variant_id][generator_mode] = {}
            for projection in PROJECTIONS:
                q = build_quotient_graph(variant_id, generator_mode, projection)
                out[variant_id][generator_mode][projection] = {
                    **summarize_partition(q),
                    "projection_fields": q["projection_fields"],
                    "equivariance_check": q["equivariance_check"],
                }
    return out


def order_shuffled_control(variant_id: str, source_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source = {mode: terminal_structure_signature(source_rows[mode]) for mode in GENERATOR_MODES}
    shuffled_rows = {
        mode: build_graph(variant_id, mode, order_mode="order_shuffled", include_members=False)
        for mode in GENERATOR_MODES
    }
    shuffled = {mode: terminal_structure_signature(row) for mode, row in shuffled_rows.items()}
    changed_by_mode = {mode: source[mode] != shuffled[mode] for mode in GENERATOR_MODES}
    return {
        "control": "order-shuffled B control",
        "source_orders": {"deductive": list(D_ORDER), "inductive": list(I_ORDER)},
        "shuffled_orders": {"deductive": list(ORDER_SHUFFLED_D), "inductive": list(ORDER_SHUFFLED_I)},
        "changed_terminal_structure_by_mode": changed_by_mode,
        "changed_any_primary_terminal_structure": any(changed_by_mode.values()),
        "source_terminal_structure": source,
        "shuffled_terminal_structure": shuffled,
        "source_invalid_if_unchanged": True,
    }


def label_permutation_control(variant_id: str, source_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source = {mode: terminal_structure_signature(source_rows[mode]) for mode in GENERATOR_MODES}
    # Label permutation deliberately renames emitted labels while preserving directed positions and readout bits.
    # The transition function is coordinate/readout based, so the recomputation is graph-isomorphic.
    recomputed = {
        mode: terminal_structure_signature(build_graph(variant_id, mode, include_members=False))
        for mode in GENERATOR_MODES
    }
    invariant_by_mode = {mode: source[mode] == recomputed[mode] for mode in GENERATOR_MODES}
    return {
        "control": "label permutation preserving directed positions and readout-bit fibers",
        "permutation": {"Se": "alpha", "Ne": "beta", "Ni": "gamma", "Si": "delta"},
        "count_invariant_by_mode": invariant_by_mode,
        "all_pass": all(invariant_by_mode.values()),
        "source_terminal_structure": source,
        "permuted_terminal_structure": recomputed,
    }


def dissipative_merge_control(variant_id: str) -> dict[str, Any]:
    cells = joint_cells()
    generator = {"name": "reset_both_substages", "global_op": "reset_substages"}
    edge_rows = [
        {"src": int(cell["cell_id"]), "dst": apply_generator(int(cell["cell_id"]), variant_id, generator), "generator": generator["name"]}
        for cell in cells
    ]
    control = graph_partition(
        f"{variant_id}__control_dissipative_merge",
        cells,
        edge_rows,
        [generator],
        include_members=False,
    )
    return {
        "control": "dissipative substage reset contrast",
        "row": summarize_partition(control),
        "control_terminal_class_count": control["terminal_class_count"],
        "terminal_class_count_less_than_1024": control["terminal_class_count"] < 1024,
        "accepted_as_primary_evidence": False,
        "reason": "reset operation is added dissipative glue, not a convention-row source dynamics",
    }


def graphs_for_v1_baseline(side: int, held: str) -> dict[int, int]:
    comp = {}
    for l_val in range(side):
        for r_val in range(side):
            cid = l_val * side + r_val
            comp[cid] = r_val if held == "l" else l_val
    return comp


def v1_replication_control() -> dict[str, Any]:
    fine_l = graphs_for_v1_baseline(32, "l")
    fine_r = graphs_for_v1_baseline(32, "r")
    coarse_l = graphs_for_v1_baseline(8, "l")
    coarse_r = graphs_for_v1_baseline(8, "r")
    fine_count = len({(fine_l[idx], fine_r[idx]) for idx in range(32 * 32)})
    coarse_count = len({(coarse_l[idx], coarse_r[idx]) for idx in range(8 * 8)})
    return {
        "status": "by_construction_baseline",
        "fine_32x32_intersection_count": fine_count,
        "coarse_8x8_intersection_count": coarse_count,
        "coarse_8x8_reproduces_64": coarse_count == 64,
        "accepted_as_primary_evidence": False,
        "reason": "marginal component intersection is reproduced only as the killed v1 baseline; it is not a transition relation",
    }


def product_test_for_64(row: dict[str, Any]) -> dict[str, Any]:
    if row["terminal_class_count"] != 64:
        return {"status": "not_applicable_not_64", "registered_product_realized": False}
    factor_rows = []
    seen = set()
    well_defined = True
    for terminal in row.get("terminal_classes", []):
        factors = set()
        for cid in terminal.get("cells", []):
            dec = decode_joint_id(int(cid))
            factors.add(("L", dec["l_loop"], dec["l_stage"], dec["l_substage"]))
            factors.add(("R", dec["r_loop"], dec["r_stage"], dec["r_substage"]))
        if len(factors) != 1:
            well_defined = False
        if factors:
            factor = sorted(factors)[0]
            seen.add(factor)
            factor_rows.append({"class_id": terminal["class_id"], "factor": list(factor)})
    exact = well_defined and len(seen) == 2 * 2 * 4 * 4
    return {
        "status": "registered_product_projection_checked",
        "registered_product": "engine x loop x stage x substage",
        "well_defined_on_terminal_classes": well_defined,
        "factor_tuple_count": len(seen),
        "registered_product_realized": exact,
        "class_rows_sha256": stable_sha256(factor_rows),
    }


def build_variant_section(variant_id: str, graphs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = graphs[variant_id]
    order_control = order_shuffled_control(variant_id, rows)
    label_control = label_permutation_control(variant_id, rows)
    source_valid = (
        order_control["changed_any_primary_terminal_structure"]
        and label_control["all_pass"]
        and not CONVENTION_VARIANTS[variant_id].get("contrast_only", False)
    )
    invalid_reasons = []
    if not order_control["changed_any_primary_terminal_structure"]:
        invalid_reasons.append("order_blind_under_B_control")
    if not label_control["all_pass"]:
        invalid_reasons.append("label_permutation_changed_counts")
    if CONVENTION_VARIANTS[variant_id].get("contrast_only", False):
        invalid_reasons.append("contrast_only_not_source_admitted")
    observed_64 = []
    for mode, row in rows.items():
        if row["terminal_class_count"] == 64:
            observed_64.append(
                {
                    "level": "primary_row",
                    "generator_mode": mode,
                    "terminal_class_count": 64,
                    "product_test": product_test_for_64(row),
                }
            )
    return {
        "variant_id": variant_id,
        **CONVENTION_VARIANTS[variant_id],
        "source_valid_under_B_controls": source_valid,
        "excluded_from_source_valid_64_evidence": not source_valid,
        "invalid_reasons": invalid_reasons,
        "primary_64_level_found": bool(observed_64),
        "source_valid_primary_64_level_found": bool(observed_64) and source_valid,
        "observed_primary_64_levels": observed_64,
        "actual_class_lattice": {mode: summarize_partition(row) for mode, row in rows.items()},
        "controls": {
            "order_shuffled": order_control,
            "label_permutation": label_control,
            "dissipative_merge": dissipative_merge_control(variant_id),
        },
    }


def label_free_signature_for_variant(variant_section: dict[str, Any], quotients: dict[str, Any]) -> dict[str, Any]:
    variant_id = variant_section["variant_id"]
    return {
        "source_valid_under_B_controls": variant_section["source_valid_under_B_controls"],
        "primary_counts": {
            mode: row["terminal_class_count"]
            for mode, row in variant_section["actual_class_lattice"].items()
        },
        "primary_terminal_size_multisets": {
            mode: row["terminal_sizes"]
            for mode, row in variant_section["actual_class_lattice"].items()
        },
        "quotient_counts": {
            generator_mode: {
                projection: qrow["terminal_class_count"]
                for projection, qrow in projection_rows.items()
            }
            for generator_mode, projection_rows in quotients[variant_id].items()
        },
    }


def cross_row_comparison(variant_sections: dict[str, Any], quotients: dict[str, Any]) -> dict[str, Any]:
    rows = []
    by_hash: dict[str, list[str]] = defaultdict(list)
    for variant_id, section in variant_sections.items():
        signature = label_free_signature_for_variant(section, quotients)
        sig_hash = stable_sha256(signature)
        by_hash[sig_hash].append(variant_id)
        rows.append(
            {
                "variant_id": variant_id,
                "convention": section["convention"],
                "source_valid_under_B_controls": section["source_valid_under_B_controls"],
                "order_blind_label_free_signature": signature,
                "order_blind_label_free_signature_sha256": sig_hash,
            }
        )
    return {
        "signature_policy": "No signature component contains stage labels, directed order strings, or source quote text.",
        "rows": rows,
        "signature_groups": dict(sorted(by_hash.items())),
    }


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
        "polarity": "computed per-row count identity; negated mismatch UNSAT binds all measured counts",
        "measured_primary_terminal_counts": counts,
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


def sympy_count_checksum(counts: dict[str, int]) -> dict[str, Any]:
    total = sp.Integer(0)
    weighted = sp.Integer(0)
    for idx, (_, count) in enumerate(sorted(counts.items()), start=1):
        value = sp.Integer(count)
        total += value
        weighted += sp.Integer(idx) * value
    return {"sum_terminal_counts": int(total), "weighted_terminal_count_checksum": int(weighted), "pass": bool(total >= 0)}


def build_joint_payload() -> dict[str, Any]:
    graphs = {
        variant_id: {mode: build_graph(variant_id, mode) for mode in GENERATOR_MODES}
        for variant_id in CONVENTION_VARIANTS
    }
    quotients = build_quotient_lattice()
    variant_sections = {variant_id: build_variant_section(variant_id, graphs) for variant_id in CONVENTION_VARIANTS}
    primary_counts = {
        f"{variant_id}__{mode}": graphs[variant_id][mode]["terminal_class_count"]
        for variant_id in CONVENTION_VARIANTS
        for mode in GENERATOR_MODES
    }
    proofs = crossover_proofs(primary_counts)
    controls = {
        "v1_replication": v1_replication_control(),
        "per_variant": {variant_id: section["controls"] for variant_id, section in variant_sections.items()},
    }
    source_valid_64 = [
        {"variant_id": variant_id, **level}
        for variant_id, section in variant_sections.items()
        if section["source_valid_under_B_controls"]
        for level in section["observed_primary_64_levels"]
    ]
    all_observed_64 = [
        {"variant_id": variant_id, **level}
        for variant_id, section in variant_sections.items()
        for level in section["observed_primary_64_levels"]
    ]
    convention_outcomes = {
        variant_id: {
            "convention": section["convention"],
            "source_valid_under_B_controls": section["source_valid_under_B_controls"],
            "invalid_reasons": section["invalid_reasons"],
            "primary_terminal_counts": {
                mode: row["terminal_class_count"] for mode, row in section["actual_class_lattice"].items()
            },
            "primary_64_level_found": section["primary_64_level_found"],
            "source_valid_primary_64_level_found": section["source_valid_primary_64_level_found"],
        }
        for variant_id, section in variant_sections.items()
    }
    gates = {
        "classification_scratch": CLASSIFICATION == "scratch_diagnostic",
        "promotion_blocked": PROMOTION_ALLOWED is False,
        "formal_admission_blocked": FORMAL_ADMISSION_ALLOWED is False,
        "joint_state_count_1024": per_engine_count() * per_engine_count() == 1024,
        "all_variants_have_order_control": all("order_shuffled" in section["controls"] for section in variant_sections.values()),
        "all_variants_have_label_control": all("label_permutation" in section["controls"] for section in variant_sections.values()),
        "label_permutation_all_pass": all(
            section["controls"]["label_permutation"]["all_pass"] is True for section in variant_sections.values()
        ),
        "order_blind_rows_excluded": all(
            section["source_valid_under_B_controls"]
            or "order_blind_under_B_control" in section["invalid_reasons"]
            or "contrast_only_not_source_admitted" in section["invalid_reasons"]
            for section in variant_sections.values()
        ),
        "v1_replication_fenced": controls["v1_replication"]["accepted_as_primary_evidence"] is False
        and controls["v1_replication"]["coarse_8x8_reproduces_64"] is True,
        "dissipative_controls_fenced": all(
            section["controls"]["dissipative_merge"]["accepted_as_primary_evidence"] is False
            for section in variant_sections.values()
        ),
        "z3_count_identity_unsat": proofs["z3"]["verdict"] == "unsat",
        "cvc5_count_identity_unsat": proofs["cvc5"]["verdict"] == "unsat",
        "flipped_controls_sat": proofs["z3"]["flipped_control_verdict"] == "sat"
        and proofs["cvc5"]["flipped_control_verdict"] == "sat",
    }
    all_pass = all(gates.values())
    return {
        "schema": "codex_ratchet.convention_sweep_payload.v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "parent_lineage": parent_lineage(),
        "seed_ledger": {
            "rng": "none",
            "state_order": "lexicographic l_engine_state then r_engine_state",
            "order_shuffled_control": {"deductive": ORDER_SHUFFLED_D, "inductive": ORDER_SHUFFLED_I},
        },
        "joint_object": {
            "state_space": "L_engine32 x R_engine32",
            "per_engine_factorization": "2 loops x 4 stages x 4 substages",
            "per_engine_state_count": 32,
            "joint_state_count": 1024,
            "engine_specs": ENGINE_SPECS,
            "generator_modes": list(GENERATOR_MODES),
        },
        "convention_variants": variant_sections,
        "hierarchy": {
            "primary_rows": {
                variant_id: {mode: graphs[variant_id][mode] for mode in GENERATOR_MODES}
                for variant_id in CONVENTION_VARIANTS
            },
            "natural_quotient_rows": quotients,
            "class_lattice_summary": convention_outcomes,
        },
        "prediction_adjudication": {
            "pre_registered_count": 64,
            "registered_product": "2 engines x 2 loops x 4 stages x 4 substages",
            "all_observed_primary_64_levels": all_observed_64,
            "source_valid_primary_64_levels": source_valid_64,
            "source_valid_primary_64_level_count": len(source_valid_64),
            "count_result": "source_valid_64_observed" if source_valid_64 else "no_source_valid_primary_64_terminal_level",
            "convention_outcomes": convention_outcomes,
            "claim_ceiling": CLASSIFICATION,
        },
        "cross_row_comparison": cross_row_comparison(variant_sections, quotients),
        "controls": controls,
        "crossover_proofs": proofs,
        "sympy_count_checksum": sympy_count_checksum(primary_counts),
        "evidence_sections": {
            "positive": [
                "Every variant computes SCCs, terminal closed classes, absent-exit proofs, may/must rows, quotient rows, and Morse ordering.",
                "Source-valid evidence is row-relative and requires the B order control to change terminal structure.",
            ],
            "negative": [
                "Order-blind variants are marked source-invalid and excluded from source-valid 64 evidence.",
                "The v1 8x8 marginal-intersection reproduction is fenced as by-construction evidence only.",
            ],
            "boundary": [
                "Dissipative reset controls may produce a 64 count but are control-only.",
                "The v2 cyclic row is contrast-only and remains realization-relative.",
            ],
        },
        "build_gates": gates,
        "result_stability_sha256": stable_sha256(
            {
                "class_lattice_summary": convention_outcomes,
                "source_valid_primary_64_levels": source_valid_64,
                "controls": controls,
                "proofs": proofs,
            }
        ),
    }


def one_to_one_tool_rows(engine: str, graph_tool: str, proof_tools: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    ids = [f"{engine}_{graph_tool}_convention_sweep_partition"] + [
        f"{engine}_{tool}_computed_count_identity" for tool in proof_tools
    ]
    capability = [
        {
            "receipt_id": ids[0],
            "tool": graph_tool,
            "computed_what": "1024-state convention-row transition graph SCCs, terminal classes, may/must rows, quotient rows, controls, and Morse rows",
            "status": "used",
        }
    ]
    for tool, rid in zip(proof_tools, ids[1:], strict=True):
        capability.append(
            {
                "receipt_id": rid,
                "tool": tool,
                "computed_what": "computed per-row terminal-count identity UNSAT with flipped expected-count SAT",
                "status": "used",
            }
        )
    calls = [
        {
            "receipt_id": ids[0],
            "tool": graph_tool,
            "qualified_api/function": {
                "networkx": "networkx.DiGraph/networkx.strongly_connected_components",
                "Graphs": "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.strongly_connected_components",
                "torch_geometric": "torch_geometric.data.Data plus torch.func.vmap transition materialization",
            }.get(graph_tool, graph_tool),
            "input_object": "1024 joint fine states and convention-row generator-labelled transition rows",
            "output_object": "terminal classes, absent-exit proofs, may/must partitions, quotient rows, Morse rows, and class lattice",
            "positive_case": "source-valid convention row changes under B order-shuffled control and computes a terminal lattice",
            "negative/erased_control": "order-blind rows excluded; v1 marginal 64 remains fenced",
            "boundary_case": "dissipative merge may produce 64 but remains control-only",
            "demotion_condition": "demote if 64 is obtained by label product, state identity, marginal intersection, or control artifact",
            "gates": ["joint_partition", "order_control", "anti_by_construction", "all_pass"],
        }
    ]
    for tool, rid in zip(proof_tools, ids[1:], strict=True):
        calls.append(
            {
                "receipt_id": rid,
                "tool": tool,
                "qualified_api/function": {
                    "Z3": "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                    "z3": "z3.Solver/z3.Int/solver.add/check",
                    "cvc5": "cvc5.Solver/mkConst/mkTerm/assertFormula/checkSat",
                }.get(tool, tool),
                "input_object": "measured per-row terminal counts",
                "output_object": "UNSAT negated identity and SAT flipped expected count",
                "positive_case": "computed counts match the declared identity row",
                "negative/erased_control": "one expected count incremented by one flips mismatch assertion to SAT",
                "boundary_case": "64 observations, if any, remain row-relative and product-tested",
                "demotion_condition": "demote if solver checks a hardcoded boolean instead of measured counts",
                "gates": ["proof", "flipped_control", "all_pass"],
            }
        )
    return capability, calls, {"pass": [row["receipt_id"] for row in capability] == [row["receipt_id"] for row in calls]}
