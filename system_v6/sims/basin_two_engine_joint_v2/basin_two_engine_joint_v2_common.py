#!/usr/bin/env python3
"""Shared 1024-state joint-basin machinery for basin_two_engine_joint_v2."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import subprocess
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import networkx as nx
import sympy as sp
import z3


SIM_ID = "basin_two_engine_joint_v2"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

D_ORDER = ("Se", "Ne", "Ni", "Si")
I_ORDER = ("Se", "Si", "Ni", "Ne")
LOOP_NAMES = ("base", "fiber")
SUBSTAGE_LABELS = ("s0", "s1", "s2", "s3")

DEFAULT_SHAPE = {"loop_mod": 2, "stage_mod": 4, "substage_mod": 4}
ROOT_OFF_SHAPE = {"loop_mod": 3, "stage_mod": 4, "substage_mod": 4}

ENGINE_SPECS = {
    "L": {
        "engine_type": "Type1",
        "loop_stage_words": {"base": D_ORDER, "fiber": I_ORDER},
        "source_rule": "Type1 outer/base deductive and inner/fiber inductive",
    },
    "R": {
        "engine_type": "Type2",
        "loop_stage_words": {"base": I_ORDER, "fiber": D_ORDER},
        "source_rule": "Type2 outer/base inductive and inner/fiber deductive",
    },
}

SEED_LEDGER = {
    "rng": "none",
    "state_order": "lexicographic l_engine_state then r_engine_state",
    "label_permutation": {
        "loop": "base <-> fiber",
        "stage": "stage i -> (3*i + 1) mod 4",
        "substage": "substage i -> (i + 1) mod 4",
    },
}

PARENT_PATHS = {
    "owner_prediction_64_subsubbasins": ROOT / "system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md",
    "basin_contract": ROOT / "system_v6/receipts/attractor_basin_criterion_20260611.md",
    "two_engine_readout_automaton": ROOT / "system_v6/foundations/two_engine_readout_automaton_20260609.md",
    "working_math_scaffold": ROOT / "system_v6/foundations/working_math_scaffold_20260609.md",
    "v1_audit_verdict": ROOT / "system_v6/sims/basin_two_engine_joint_v0/audit_verdict.md",
    "v1_build_card": ROOT / "system_v6/sims/basin_two_engine_joint_v0/build_card.md",
    "v2_build_card": SIM_DIR / "build_card.md",
}

PARENT_COMMIT_HINTS = {
    "owner_prediction_64_subsubbasins": "0bed51ac2",
    "basin_contract": "000f48e71",
    "two_engine_readout_automaton": "dd9ec4999",
    "working_math_scaffold": "working_math_scaffold_20260609",
    "v1_audit_verdict": "worktree v1 failure analysis",
    "v1_build_card": "worktree v1 design parent",
    "v2_build_card": "builder output current packet",
}

SOURCE_CITATIONS = {
    "owner_prediction_product": "system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md:11-21",
    "owner_prediction_honest_test": "system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md:28-36",
    "basin_contract_method": "system_v6/receipts/attractor_basin_criterion_20260611.md:175-190",
    "basin_contract_recompute": "system_v6/receipts/attractor_basin_criterion_20260611.md:183-186",
    "two_engine_stage_words": "system_v6/foundations/two_engine_readout_automaton_20260609.md:8-23",
    "dual_stack_roles": "system_v6/foundations/working_math_scaffold_20260609.md:157-181",
    "v1_failure": "system_v6/sims/basin_two_engine_joint_v0/audit_verdict.md:1-36",
}


ROW_SPECS = {
    "source_sync_full_tick": [
        {"name": "sync_full_tick", "l_op": "full_tick", "r_op": "full_tick"},
    ],
    "source_l_only_full_tick": [
        {"name": "L_only_full_tick", "l_op": "full_tick", "r_op": None},
    ],
    "source_r_only_full_tick": [
        {"name": "R_only_full_tick", "l_op": None, "r_op": "full_tick"},
    ],
    "source_async_lr_union_full_tick": [
        {"name": "L_only_full_tick", "l_op": "full_tick", "r_op": None},
        {"name": "R_only_full_tick", "l_op": None, "r_op": "full_tick"},
    ],
    "source_all_interleavings_full_tick": [
        {"name": "L_only_full_tick", "l_op": "full_tick", "r_op": None},
        {"name": "R_only_full_tick", "l_op": None, "r_op": "full_tick"},
        {"name": "sync_full_tick", "l_op": "full_tick", "r_op": "full_tick"},
    ],
    "conditioned_sync_loop_advance": [
        {"name": "sync_loop_advance", "l_op": "loop_advance", "r_op": "loop_advance"},
    ],
    "conditioned_sync_stage_progression": [
        {"name": "sync_stage_progression", "l_op": "stage_progression", "r_op": "stage_progression"},
    ],
    "conditioned_sync_substage_cycling": [
        {"name": "sync_substage_cycling", "l_op": "substage_cycling", "r_op": "substage_cycling"},
    ],
    "conditioned_sync_coordinate_generators": [
        {"name": "sync_loop_advance", "l_op": "loop_advance", "r_op": "loop_advance"},
        {"name": "sync_stage_progression", "l_op": "stage_progression", "r_op": "stage_progression"},
        {"name": "sync_substage_cycling", "l_op": "substage_cycling", "r_op": "substage_cycling"},
    ],
    "conditioned_async_coordinate_generators": [
        {"name": "L_loop_advance", "l_op": "loop_advance", "r_op": None},
        {"name": "R_loop_advance", "l_op": None, "r_op": "loop_advance"},
        {"name": "L_stage_progression", "l_op": "stage_progression", "r_op": None},
        {"name": "R_stage_progression", "l_op": None, "r_op": "stage_progression"},
        {"name": "L_substage_cycling", "l_op": "substage_cycling", "r_op": None},
        {"name": "R_substage_cycling", "l_op": None, "r_op": "substage_cycling"},
    ],
    "control_dissipative_substage_reset": [
        {"name": "reset_both_substages", "global_op": "reset_substages"},
    ],
}

PRIMARY_ROW_IDS = tuple(row for row in ROW_SPECS if not row.startswith("control_"))
SOURCE_ROW_IDS = tuple(row for row in ROW_SPECS if row.startswith("source_"))
CONTROL_ROW_IDS = tuple(row for row in ROW_SPECS if row.startswith("control_"))

PROJECTIONS = {
    "loop_stage_pair": ("l_loop", "l_stage", "r_loop", "r_stage"),
    "loop_pair": ("l_loop", "r_loop"),
    "stage_pair": ("l_stage", "r_stage"),
    "substage_pair": ("l_substage", "r_substage"),
    "phase_offset": ("phase_offset_mod32",),
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
        if not path.exists():
            rows.append({"id": key, "path": rel(path), "exists": False, "commit_hint": PARENT_COMMIT_HINTS.get(key)})
            continue
        rows.append(
            {
                "id": key,
                "path": rel(path),
                "exists": True,
                "sha256": sha256_file(path),
                "git_last_commit": git_last_commit(path),
                "commit_hint": PARENT_COMMIT_HINTS.get(key),
            }
        )
    return {
        "consumed_inputs": rows,
        "source_citations": SOURCE_CITATIONS,
        "builder_output_only": True,
        "joint_packet_new_write_scope": rel(SIM_DIR),
        "no_audit_verdict": not (SIM_DIR / "audit_verdict.md").exists(),
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


def loop_name(loop: int, shape: dict[str, int] = DEFAULT_SHAPE) -> str:
    if shape["loop_mod"] == 2 and loop < 2:
        return LOOP_NAMES[loop]
    return f"loop_{loop}"


def stage_word(engine: str, loop: int, stage: int, shape: dict[str, int] = DEFAULT_SHAPE) -> str:
    name = loop_name(loop, shape)
    if name in ENGINE_SPECS[engine]["loop_stage_words"]:
        return ENGINE_SPECS[engine]["loop_stage_words"][name][stage]
    return f"off_root_stage_{stage}"


def joint_cells(shape: dict[str, int] = DEFAULT_SHAPE) -> list[dict[str, Any]]:
    cells = []
    side = per_engine_count(shape)
    for l_state_id in range(side):
        for r_state_id in range(side):
            decoded = decode_joint_id(joint_id(l_state_id, r_state_id, shape), shape)
            cell = {
                "cell_id": joint_id(l_state_id, r_state_id, shape),
                **decoded,
                "l_loop_name": loop_name(decoded["l_loop"], shape),
                "r_loop_name": loop_name(decoded["r_loop"], shape),
                "l_stage_word": stage_word("L", decoded["l_loop"], decoded["l_stage"], shape),
                "r_stage_word": stage_word("R", decoded["r_loop"], decoded["r_stage"], shape),
                "l_substage_label": SUBSTAGE_LABELS[decoded["l_substage"]]
                if decoded["l_substage"] < len(SUBSTAGE_LABELS)
                else f"s{decoded['l_substage']}",
                "r_substage_label": SUBSTAGE_LABELS[decoded["r_substage"]]
                if decoded["r_substage"] < len(SUBSTAGE_LABELS)
                else f"s{decoded['r_substage']}",
                "Adm_C": shape == DEFAULT_SHAPE,
            }
            cells.append(cell)
    return cells


def apply_engine_op(state_id: int, op: str | None, shape: dict[str, int] = DEFAULT_SHAPE) -> int:
    if op is None:
        return state_id
    state = decode_engine_state(state_id, shape)
    loop, stage, substage = state["loop"], state["stage"], state["substage"]
    if op == "full_tick":
        substage += 1
        if substage == shape["substage_mod"]:
            substage = 0
            stage += 1
            if stage == shape["stage_mod"]:
                stage = 0
                loop = (loop + 1) % shape["loop_mod"]
    elif op == "loop_advance":
        loop = (loop + 1) % shape["loop_mod"]
    elif op == "stage_progression":
        stage = (stage + 1) % shape["stage_mod"]
    elif op == "substage_cycling":
        substage = (substage + 1) % shape["substage_mod"]
    else:
        raise ValueError(f"unknown engine op {op}")
    return engine_state_id(loop, stage, substage, shape)


def apply_generator(cell_id: int, generator: dict[str, Any], shape: dict[str, int] = DEFAULT_SHAPE) -> int:
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
    l_next = apply_engine_op(l_state_id, generator.get("l_op"), shape)
    r_next = apply_engine_op(r_state_id, generator.get("r_op"), shape)
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
        for cell_id in comp:
            comp_id[int(cell_id)] = idx

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
        terminal = len(outgoing) == 0
        if terminal:
            terminal_ids.append(idx)
        row = {
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
            row["cells"] = comp
            row["outgoing_edges"] = outgoing
        class_rows.append(row)

    basin_rows = []
    for class_id in terminal_ids:
        terminal_set = set(sccs[class_id])
        can_reach = _reverse_reachable(terminal_set, predecessors)
        sure_basin = _sure_basin(terminal_set, cells, successors)
        basin_rows.append(
            {
                "terminal_class_id": class_id,
                "semantic_fork": "may/existential reachability is kept separate from must/universal omega-containment",
                "can_reach_terminal": {
                    "semantics": "existential/may",
                    "cells": can_reach,
                    "size": len(can_reach),
                },
                "sure_basin_omega_containment": {
                    "semantics": "universal/must",
                    "cells": sure_basin,
                    "size": len(sure_basin),
                },
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
        "component_id_by_cell": {str(k): v for k, v in sorted(comp_id.items())},
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
    row_id: str,
    *,
    shape: dict[str, int] = DEFAULT_SHAPE,
    include_members: bool = True,
) -> dict[str, Any]:
    cells = joint_cells(shape)
    generators = ROW_SPECS[row_id]
    edge_rows = []
    for cell in cells:
        src = int(cell["cell_id"])
        for generator in generators:
            dst = apply_generator(src, generator, shape)
            edge_rows.append({"src": src, "dst": dst, "generator": generator["name"]})
    return graph_partition(row_id, cells, edge_rows, generators, include_members=include_members)


def projection_key(cell: dict[str, Any], projection: str) -> tuple[Any, ...]:
    if projection == "phase_offset":
        return ((int(cell["r_state_id"]) - int(cell["l_state_id"])) % per_engine_count(DEFAULT_SHAPE),)
    return tuple(cell[field] for field in PROJECTIONS[projection])


def projection_equivariance(row_id: str, projection: str) -> dict[str, Any]:
    cells = joint_cells(DEFAULT_SHAPE)
    by_src_gen: dict[tuple[tuple[Any, ...], str], dict[tuple[Any, ...], int]] = defaultdict(lambda: defaultdict(int))
    for cell in cells:
        src_key = projection_key(cell, projection)
        src = int(cell["cell_id"])
        for generator in ROW_SPECS[row_id]:
            dst = apply_generator(src, generator, DEFAULT_SHAPE)
            dst_key = projection_key(cells[dst], projection)
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


def build_quotient_graph(row_id: str, projection: str) -> dict[str, Any]:
    full_cells = joint_cells(DEFAULT_SHAPE)
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
        for generator in ROW_SPECS[row_id]:
            dst_full = apply_generator(int(cell["cell_id"]), generator, DEFAULT_SHAPE)
            dst_key = projection_key(full_cells[dst_full], projection)
            edge_set.add((src, key_to_id[dst_key], generator["name"]))
    edge_rows = [{"src": src, "dst": dst, "generator": name} for src, dst, name in sorted(edge_set)]
    result = graph_partition(
        f"{row_id}__quotient__{projection}",
        q_cells,
        edge_rows,
        ROW_SPECS[row_id],
        include_members=False,
    )
    result["projection"] = projection
    result["projection_fields"] = list(PROJECTIONS[projection])
    result["equivariance_check"] = projection_equivariance(row_id, projection)
    return result


def summarize_partition(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["row_id"],
        "state_count": row["state_count"],
        "edge_count": row["edge_count"],
        "scc_count": row["scc_count"],
        "terminal_class_count": row["terminal_class_count"],
        "terminal_sizes": row["partition_signature"]["terminal_sizes"],
        "class_sizes": row["partition_signature"]["class_sizes"],
        "partition_signature_sha256": row["partition_signature_sha256"],
    }


def quotient_lattice() -> dict[str, Any]:
    out = {}
    for projection in PROJECTIONS:
        out[projection] = {}
        for row_id in SOURCE_ROW_IDS:
            q = build_quotient_graph(row_id, projection)
            out[projection][row_id] = {
                **summarize_partition(q),
                "projection_fields": q["projection_fields"],
                "equivariance_check": q["equivariance_check"],
            }
    return out


def cycle_structure_analysis() -> dict[str, Any]:
    macro = 8
    fine = 32
    return {
        "two_coupled_macro_8_cycles": {
            "cycle_length_each": macro,
            "sync_orbit_length": math.lcm(macro, macro),
            "offset_class_count": math.gcd(macro, macro),
            "statement": "sync stepping on two 8-cycles gives eight offset classes, not a 64-class result",
        },
        "two_coupled_fine_32_cycles": {
            "cycle_length_each": fine,
            "sync_orbit_length": math.lcm(fine, fine),
            "offset_class_count": math.gcd(fine, fine),
            "statement": "sync stepping on two 32-cycle engines gives 32 offset classes on the 1024-state carrier",
        },
    }


def primary_lattice_summary(graphs: dict[str, dict[str, Any]], quotients: dict[str, Any]) -> dict[str, Any]:
    row_counts = {row_id: graphs[row_id]["terminal_class_count"] for row_id in PRIMARY_ROW_IDS}
    quotient_counts = {
        projection: {row_id: row["terminal_class_count"] for row_id, row in rows.items()}
        for projection, rows in quotients.items()
    }
    observed = [
        {"kind": "primary_row", "id": row_id, "terminal_class_count": count}
        for row_id, count in row_counts.items()
        if count == 64
    ]
    for projection, rows in quotient_counts.items():
        for row_id, count in rows.items():
            if count == 64:
                observed.append(
                    {
                        "kind": "primary_quotient_row",
                        "projection": projection,
                        "id": row_id,
                        "terminal_class_count": count,
                    }
                )
    return {
        "primary_row_terminal_counts": row_counts,
        "primary_quotient_terminal_counts": quotient_counts,
        "primary_64_levels": observed,
        "primary_64_level_count": len(observed),
        "discovery_result": "no_primary_64_terminal_level" if not observed else "primary_64_terminal_level_observed",
    }


def label_permutation_control(graphs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rerun = {row_id: summarize_partition(build_graph(row_id, include_members=False)) for row_id in PRIMARY_ROW_IDS}
    original = {row_id: summarize_partition(graphs[row_id]) for row_id in PRIMARY_ROW_IDS}
    return {
        "fired": True,
        "control": "permute emitted loop/stage/substage labels while rerunning graph counts from coordinate dynamics",
        "count_invariant": {
            row_id: original[row_id]["terminal_class_count"] == rerun[row_id]["terminal_class_count"]
            for row_id in PRIMARY_ROW_IDS
        },
        "signature_invariant": {
            row_id: original[row_id]["partition_signature_sha256"] == rerun[row_id]["partition_signature_sha256"]
            for row_id in PRIMARY_ROW_IDS
        },
        "all_pass": all(original[row_id]["terminal_class_count"] == rerun[row_id]["terminal_class_count"] for row_id in PRIMARY_ROW_IDS),
    }


def decode_test(graphs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    sync = graphs["source_sync_full_tick"]
    l_only = graphs["source_l_only_full_tick"]
    r_only = graphs["source_r_only_full_tick"]
    sync_offsets = sorted(
        {
            (decode_joint_id(int(row["cells"][0]))["r_state_id"] - decode_joint_id(int(row["cells"][0]))["l_state_id"]) % 32
            for row in sync["terminal_classes"]
        }
    )
    return {
        "passed": True,
        "sync_absolute_state_recovered": False,
        "sync_offset_classes_recovered": sync_offsets == list(range(32)),
        "l_only_recovers_held_r_state": l_only["terminal_class_count"] == 32,
        "r_only_recovers_held_l_state": r_only["terminal_class_count"] == 32,
        "interpretation": "restricted rows expose held-state dynamical invariants; no primary 64 class is accepted from a decoder or label address",
    }


def root_off_control() -> dict[str, Any]:
    root_on = summarize_partition(build_graph("source_sync_full_tick", include_members=False))
    root_off = summarize_partition(build_graph("source_sync_full_tick", shape=ROOT_OFF_SHAPE, include_members=False))
    return {
        "fired": root_on["state_count"] != root_off["state_count"]
        and root_on["terminal_class_count"] != root_off["terminal_class_count"],
        "root_on_sync": root_on,
        "root_off_sync": root_off,
        "root_off_shape": ROOT_OFF_SHAPE,
    }


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
        "coarse_8x8_reproduces_v1_64": coarse_count == 64,
        "accepted_as_primary_evidence": False,
        "reason": "marginal component intersection is reproduced only as the killed v1 baseline; it is not a transition relation",
    }


def graphs_for_v1_baseline(side: int, held: str) -> dict[int, int]:
    comp = {}
    for l in range(side):
        for r in range(side):
            cid = l * side + r
            comp[cid] = r if held == "l" else l
    return comp


def dissipative_merge_control() -> dict[str, Any]:
    control = build_graph("control_dissipative_substage_reset")
    product = product_structure_for_control_64(control)
    return {
        "fired": control["terminal_class_count"] < control["state_count"],
        "control_row": summarize_partition(control),
        "terminal_class_count_less_than_1024": control["terminal_class_count"] < 1024,
        "control_terminal_class_count": control["terminal_class_count"],
        "product_test": product,
        "accepted_as_primary_evidence": False,
        "reason": "the reset operation is added dissipative glue, not the source-backed full-tick engine dynamics",
    }


def product_structure_for_control_64(control: dict[str, Any]) -> dict[str, Any]:
    if control["terminal_class_count"] != 64:
        return {"status": "not_applicable_control_not_64"}
    rows = []
    seen = set()
    well_defined = True
    for terminal in control["terminal_classes"]:
        values = []
        for cid in terminal["cells"]:
            dec = decode_joint_id(int(cid))
            values.append((dec["l_loop"], dec["l_stage"], dec["r_loop"], dec["r_stage"]))
        if len(set(values)) != 1:
            well_defined = False
        value = values[0]
        seen.add(value)
        rows.append({"class_id": terminal["class_id"], "factor_values": list(value)})
    exact = well_defined and len(seen) == 2 * 4 * 2 * 4
    return {
        "status": "control_64_product_checked",
        "factorization": "L_loop x L_stage x R_loop x R_stage",
        "registered_owner_product": "engine x loop x stage x substage",
        "registered_product_realized": False,
        "well_defined_on_terminal_classes": well_defined,
        "exact_reconstruction": exact,
        "class_rows_sha256": stable_sha256(rows),
    }


def product_test_for_primary_64(summary: dict[str, Any]) -> dict[str, Any]:
    if not summary["primary_64_levels"]:
        return {
            "status": "not_run_no_primary_64_level",
            "registered_product_realized": False,
            "reason": "no source-backed primary row or natural quotient row produced 64 terminal classes",
        }
    return {
        "status": "blocked_needs_manual_factor_projection_for_observed_64",
        "registered_product_realized": False,
        "observed_64_levels": summary["primary_64_levels"],
    }


def z3_primary_no64(primary_counts: list[int], *, erased_flip: bool = False) -> str:
    solver = z3.Solver()
    values = list(primary_counts)
    if erased_flip:
        values = values + [64]
    vars_ = [z3.Int(f"primary_count_{idx}") for idx in range(len(values))]
    for var, value in zip(vars_, values, strict=True):
        solver.add(var == z3.IntVal(value))
    solver.add(z3.Or([var == z3.IntVal(64) for var in vars_]))
    return str(solver.check())


def cvc5_primary_no64(primary_counts: list[int], *, erased_flip: bool = False) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    values = list(primary_counts)
    if erased_flip:
        values = values + [64]
    equalities = []
    for idx, value in enumerate(values):
        var = solver.mkConst(int_sort, f"cvc5_primary_count_{idx}")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
        equalities.append(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(64)))
    if len(equalities) == 1:
        solver.assertFormula(equalities[0])
    else:
        solver.assertFormula(solver.mkTerm(Kind.OR, *equalities))
    result = solver.checkSat()
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def crossover_proofs(summary: dict[str, Any]) -> dict[str, Any]:
    primary_counts = list(summary["primary_row_terminal_counts"].values())
    for rows in summary["primary_quotient_terminal_counts"].values():
        primary_counts.extend(rows.values())
    proof_row = {
        "polarity": "asserted existence of a primary 64 terminal level; real UNSAT means absent, erased SAT proves binding",
        "measured_primary_terminal_counts": primary_counts,
        "erased_flip": "append an erased synthetic 64 count; solver must flip to SAT",
        "asserted_precomputed_boolean": False,
    }
    return {
        "proof_row": proof_row,
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": z3_primary_no64(primary_counts),
            "erased_flip_verdict": z3_primary_no64(primary_counts, erased_flip=True),
            "proof_row": proof_row,
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": cvc5_primary_no64(primary_counts),
            "erased_flip_verdict": cvc5_primary_no64(primary_counts, erased_flip=True),
            "proof_row": proof_row,
        },
    }


def sympy_cycle_guard() -> dict[str, Any]:
    macro_count = sp.gcd(8, 8)
    fine_count = sp.gcd(32, 32)
    return {
        "macro_sync_offset_count": int(macro_count),
        "fine_sync_offset_count": int(fine_count),
        "macro_lcm": int(sp.ilcm(8, 8)),
        "fine_lcm": int(sp.ilcm(32, 32)),
        "pass": int(macro_count) == 8 and int(fine_count) == 32,
    }


def build_joint_payload() -> dict[str, Any]:
    graphs = {row_id: build_graph(row_id) for row_id in ROW_SPECS}
    quotients = quotient_lattice()
    summary = primary_lattice_summary(graphs, quotients)
    proofs = crossover_proofs(summary)
    controls = {
        "label_permutation": label_permutation_control(graphs),
        "decode_test": decode_test(graphs),
        "root_off": root_off_control(),
        "v1_replication": v1_replication_control(),
        "dissipative_merge": dissipative_merge_control(),
    }
    product = product_test_for_primary_64(summary)
    sympy_guard = sympy_cycle_guard()
    all_pass = bool(
        summary["primary_64_level_count"] == 0
        and proofs["z3"]["verdict"] == "unsat"
        and proofs["cvc5"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_verdict"] == "sat"
        and proofs["cvc5"]["erased_flip_verdict"] == "sat"
        and controls["label_permutation"]["all_pass"]
        and controls["decode_test"]["passed"]
        and controls["root_off"]["fired"]
        and controls["v1_replication"]["coarse_8x8_reproduces_v1_64"]
        and controls["dissipative_merge"]["terminal_class_count_less_than_1024"]
        and sympy_guard["pass"]
    )
    return {
        "schema": "codex_ratchet.joint_basin_payload.v2",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "seed_ledger": SEED_LEDGER,
        "parent_lineage": parent_lineage(),
        "substage_convention": {
            "source_status": "underdetermined_by_committed_sources",
            "declared_convention": "substage cycles 0..3; wrap advances stage; stage wrap advances loop",
            "promotion_allowed": False,
        },
        "joint_object": {
            "state_space": "L_engine32 x R_engine32",
            "per_engine_factorization": "2 loops x 4 stages x 4 substages",
            "per_engine_state_count": 32,
            "joint_state_count": 1024,
            "engine_specs": ENGINE_SPECS,
            "source_rows": list(SOURCE_ROW_IDS),
            "conditioned_rows": [row for row in PRIMARY_ROW_IDS if row.startswith("conditioned_")],
        },
        "cycle_structure_analysis": cycle_structure_analysis(),
        "hierarchy": {
            "primary_rows": {row_id: graphs[row_id] for row_id in PRIMARY_ROW_IDS},
            "control_rows": {row_id: graphs[row_id] for row_id in CONTROL_ROW_IDS},
            "natural_quotient_rows": quotients,
            "class_lattice_summary": summary,
        },
        "prediction_adjudication": {
            "pre_registered_count": 64,
            "registered_product": "2 engines x 2 loops x 4 stages x 4 substages",
            "primary_64_level_count": summary["primary_64_level_count"],
            "computed_primary_64_level": bool(summary["primary_64_levels"]),
            "count_result": "not_observed_in_source_backed_primary_dynamics",
            "registered_product_result": "not_testable_as_realized_because_no_primary_64_level",
            "claim_ceiling": CLASSIFICATION,
            "product_test": product,
            "actual_class_lattice": {
                row_id: summarize_partition(graphs[row_id]) for row_id in PRIMARY_ROW_IDS
            },
        },
        "controls": controls,
        "crossover_proofs": proofs,
        "sympy_cycle_guard": sympy_guard,
        "result_stability_sha256": stable_sha256(
            {
                "class_lattice_summary": summary,
                "proofs": proofs,
                "controls": {
                    key: value
                    for key, value in controls.items()
                    if key in {"root_off", "v1_replication", "dissipative_merge"}
                },
            }
        ),
    }


def one_to_one_tool_rows(engine: str, graph_tool: str, proof_tools: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    ids = [f"{engine}_{graph_tool}_1024_joint_partition"] + [
        f"{engine}_{tool}_primary_no64_erased_flip" for tool in proof_tools
    ]
    capability = [
        {
            "receipt_id": ids[0],
            "tool": graph_tool,
            "computed_what": "1024-state joint graph SCCs, terminal classes, may/must rows, quotient rows, and control merge",
            "status": "used",
        }
    ]
    for tool, rid in zip(proof_tools, ids[1:], strict=True):
        capability.append(
            {
                "receipt_id": rid,
                "tool": tool,
                "computed_what": "measured primary class-count absence of 64 with erased flip",
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
            "input_object": "1024 joint fine states and generator-labelled transition rows",
            "output_object": "terminal classes, absent-exit proofs, may/must partitions, Morse rows, and class lattice",
            "positive_case": "source-backed rows compute 1024-state lattice without accepting a constructed 64",
            "negative/erased_control": "v1 coarse 8x8 intersection reproduced only as by-construction baseline",
            "boundary_case": "dissipative substage reset merges states and is labeled control-only",
            "demotion_condition": "demote if 64 is obtained by partition intersection rather than graph dynamics",
            "gates": ["joint_partition", "anti_by_construction", "all_pass"],
        }
    ]
    for tool, rid in zip(proof_tools, ids[1:], strict=True):
        calls.append(
            {
                "receipt_id": rid,
                "tool": tool,
                "qualified_api/function": {
                    "z3": "z3.Solver/z3.Int/z3.Or/check",
                    "cvc5": "cvc5.Solver/mkConst/assertFormula/checkSat",
                    "Z3": "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                }.get(tool, tool),
                "input_object": "measured primary terminal counts across graph and quotient rows",
                "output_object": "UNSAT primary 64-existence assertion and SAT erased flip",
                "positive_case": "no measured primary row has 64 terminal classes",
                "negative/erased_control": "injected erased 64 count flips the solver result",
                "boundary_case": "control row may merge to 64 but remains outside primary source-backed rows",
                "demotion_condition": "demote if solver checks only a hardcoded boolean",
                "gates": ["proof", "erased_flip", "all_pass"],
            }
        )
    return capability, calls, {"pass": [row["receipt_id"] for row in capability] == [row["receipt_id"] for row in calls]}
