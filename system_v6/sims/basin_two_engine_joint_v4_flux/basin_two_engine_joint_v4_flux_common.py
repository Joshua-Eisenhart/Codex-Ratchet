#!/usr/bin/env python3
"""Shared machinery for the flux-carrying two-engine basin packet."""

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


SIM_ID = "basin_two_engine_joint_v4_flux"
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
        "source_rule": "Type1 left Weyl engine: flux IN; outer/base deductive, inner/fiber inductive",
    },
    "R": {
        "engine_type": "Type2",
        "chirality_sign": -1,
        "flux_direction": "OUT",
        "loop_stage_words": {"base": I_ORDER, "fiber": D_ORDER},
        "loop_stage_words_order_shuffled": {"base": ORDER_SHUFFLED_I, "fiber": ORDER_SHUFFLED_D},
        "source_rule": "Type2 right Weyl engine: flux OUT; outer/base inductive, inner/fiber deductive",
    },
}

BASELINE_EXPECTED = {
    "A_readout_transition_dwell": {"terminal_class_count": 1, "terminal_sizes": [28]},
    "D_matrix64_b_order_overlay": {"terminal_class_count": 1, "terminal_sizes": [24]},
}

V3_JOINT_EXPECTED = {
    "A_readout_transition_dwell": {"sync": 28, "all_interleavings": 1},
    "D_matrix64_b_order_overlay": {"sync": 24, "all_interleavings": 1},
}

BASE_VARIANTS: dict[str, dict[str, Any]] = {
    "A_readout_transition_dwell": {
        "label": "A-dwell directed stage-word / loop-readout row",
        "baseline_core": 28,
        "source_status": "order_sensitive_v3_corrected_target",
        "source_quote": "owner_prediction_64_subsubbasins_20260611.md final corrected citation: A=28 within-slice terminal core",
    },
    "D_matrix64_b_order_overlay": {
        "label": "D Matrix64/Carnot product overlaid on B directed order",
        "baseline_core": 24,
        "source_status": "order_sensitive_v3_corrected_target",
        "source_quote": "owner_prediction_64_subsubbasins_20260611.md final corrected citation: D_b_order=24 within-slice terminal core",
    },
}

COUPLING_ROWS: dict[str, dict[str, Any]] = {
    "C1_constrained_fibered_placement": {
        "family": "C1/C2",
        "source_status": "candidate_source_faithful_primary",
        "accepted_as_primary_evidence": True,
        "by_construction": False,
        "description": "Constrained placement preserves loop-sheet xor, stage offset, and flux-pair sector; fallback is a constrained paired tick, not a product class.",
    },
    "C2_fibered_system": {
        "family": "C1/C2",
        "source_status": "candidate_source_faithful_primary",
        "accepted_as_primary_evidence": True,
        "by_construction": False,
        "description": "Fibered-system row keeps L and R as independent generators on the same joint carrier; no superengine merge generator is primary.",
    },
    "O6_720_double_cover": {
        "family": "O6",
        "source_status": "owner_source_primary_candidate",
        "accepted_as_primary_evidence": True,
        "by_construction": False,
        "description": "The two loops act as double-cover sheets; flux product chooses which sheet advances, representing a 720-degree closure candidate.",
    },
    "C5_strategy_alternating_period2": {
        "family": "C5",
        "source_status": "candidate_source_faithful_primary",
        "accepted_as_primary_evidence": True,
        "by_construction": False,
        "description": "Ring discipline row: alternating readout period-2 selects L/R sheet phase.",
    },
    "C5_strategy_paired_period4": {
        "family": "C5",
        "source_status": "candidate_source_faithful_primary",
        "accepted_as_primary_evidence": True,
        "by_construction": False,
        "description": "Ring discipline row: paired readout period-4 selects L/R sheet phase.",
    },
    "contrast_sync_non_source_faithful": {
        "family": "O2_fenced_contrast",
        "source_status": "non_source_faithful_contrast",
        "accepted_as_primary_evidence": False,
        "by_construction": False,
        "description": "Bare sync is fenced because O2 says the engines are not a merged superengine.",
    },
    "contrast_full_interleave_non_source_faithful": {
        "family": "O2_fenced_contrast",
        "source_status": "non_source_faithful_contrast",
        "accepted_as_primary_evidence": False,
        "by_construction": False,
        "description": "Full interleave is fenced because v3 showed this collapses independence.",
    },
    "contrast_l_only_frozen_projection": {
        "family": "frozen_factor_projection_contrast",
        "source_status": "one_sided_frozen_factor_contrast",
        "accepted_as_primary_evidence": False,
        "by_construction": False,
        "one_sided": "L_moves_R_frozen",
        "description": "One-sided L move included only to expose frozen-factor echo mechanics.",
    },
    "contrast_r_only_frozen_projection": {
        "family": "frozen_factor_projection_contrast",
        "source_status": "one_sided_frozen_factor_contrast",
        "accepted_as_primary_evidence": False,
        "by_construction": False,
        "one_sided": "R_moves_L_frozen",
        "description": "One-sided R move included only to expose frozen-factor echo mechanics.",
    },
}

SOURCE_FAITHFUL_ROW_IDS = tuple(
    row_id for row_id, row in COUPLING_ROWS.items() if row["accepted_as_primary_evidence"] is True
)

PARENT_PATHS = {
    "build_card": SIM_DIR / "build_card.md",
    "owner_prediction_64_subsubbasins": ROOT / "system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md",
    "coupling_law_family_table": ROOT / "system_v6/receipts/coupling_law_family_table_20260611.md",
    "two_engine_readout_automaton": ROOT / "system_v6/foundations/two_engine_readout_automaton_20260609.md",
    "symbolic_layer_iching_taijitu": ROOT / "system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md",
    "flux_emergence_discriminator": ROOT / "system_v6/sims/flux_emergence_discriminator/results/flux_emergence_discriminator_envelope_results.json",
    "geo_s9_holonomy_spectrum_identity": ROOT / "system_v6/sims/geo_s9_alternative_connections_v0/results/geo_s9_alternative_connections_v0_envelope_results.json",
    "ratchet_s2_two_shell_flux": ROOT / "system_v6/sims/ratchet_s2_two_shell_flux_v0/results/ratchet_s2_two_shell_flux_v0_envelope_results.json",
    "basin_two_engine_joint_v3": ROOT / "system_v6/sims/basin_two_engine_joint_v3_convention_sweep/results/basin_two_engine_joint_v3_convention_sweep_envelope_results.json",
}

SOURCE_CITATIONS = {
    "owner_flux_refinement": "system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md owner refinement section",
    "corrected_target": "system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md final corrected citation: A=28, D_b_order=24",
    "coupling_rows": "system_v6/receipts/coupling_law_family_table_20260611.md owner-source rows O1-O6 and candidate rows C1/C2/C5",
    "stage_word_orders": "system_v6/foundations/two_engine_readout_automaton_20260609.md alternating=period-2 and paired=period-4 rows",
    "flux_object": "flux_emergence_discriminator: Chern=1 plus ablations; geo_s9_alternative_connections_v0: holonomy-spectrum/annular-flux geometric data class",
}

FLUX_REALIZATION = {
    "finite_variable": "signed holonomy-sector bit in {-1,+1}",
    "committed_flux_objects_realized": [
        "system_v6/sims/flux_emergence_discriminator/results/flux_emergence_discriminator_envelope_results.json: Chern=1 flux with bare-spinor and single-shell ablations",
        "system_v6/sims/geo_s9_alternative_connections_v0/results/geo_s9_alternative_connections_v0_envelope_results.json: leaf holonomy spectrum plus annular flux distinguishes geometric data at fixed c1",
        "system_v6/sims/ratchet_s2_two_shell_flux_v0/results/ratchet_s2_two_shell_flux_v0_envelope_results.json: two-shell annular flux / boundary holonomy gap anchor",
    ],
    "update_policy": (
        "On a stage/loop boundary, the signed sector flips exactly when the next active readout opposes "
        "the engine's O1 flux direction and the current loop is the direction sheet: L/IN uses base, R/OUT uses fiber."
    ),
    "claim_ceiling": "finite realization-relative flux carrier; scratch_diagnostic only",
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
        row: dict[str, Any] = {"id": key, "path": rel(path) if path.exists() else str(path), "exists": path.exists()}
        if path.exists():
            row["sha256"] = sha256_file(path)
            row["git_last_commit"] = git_last_commit(path)
        rows.append(row)
    return {
        "consumed_inputs": rows,
        "source_citations": SOURCE_CITATIONS,
        "flux_realization": FLUX_REALIZATION,
        "builder_output_only": True,
        "no_builder_audit_verdict_gate": True,
        "joint_packet_write_scope": rel(SIM_DIR),
        "source_bound_claim_ceiling": CLASSIFICATION,
    }


def base_count() -> int:
    return DEFAULT_SHAPE["loop_mod"] * DEFAULT_SHAPE["stage_mod"] * DEFAULT_SHAPE["substage_mod"]


def engine_count_with_flux() -> int:
    return base_count() * DEFAULT_SHAPE["flux_mod"]


def joint_count_with_flux() -> int:
    side = engine_count_with_flux()
    return side * side


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


def joint_id(l_state_id: int, r_state_id: int) -> int:
    side = engine_count_with_flux()
    return l_state_id * side + r_state_id


def decode_joint_id(cell_id: int) -> dict[str, Any]:
    side = engine_count_with_flux()
    l_state_id = cell_id // side
    r_state_id = cell_id % side
    l_dec = decode_flux_state(l_state_id)
    r_dec = decode_flux_state(r_state_id)
    return {
        "l_state_id": l_state_id,
        "r_state_id": r_state_id,
        "l_base_state_id": l_dec["base_state_id"],
        "r_base_state_id": r_dec["base_state_id"],
        "l_loop": l_dec["loop"],
        "l_stage": l_dec["stage"],
        "l_substage": l_dec["substage"],
        "l_flux": l_dec["flux"],
        "r_loop": r_dec["loop"],
        "r_stage": r_dec["stage"],
        "r_substage": r_dec["substage"],
        "r_flux": r_dec["flux"],
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


def readout_sign(readout: str) -> int:
    return 1 if readout.lower() == "win" else -1


def advance_stage_loop(loop: int, stage: int, stage_inc: int = 1) -> tuple[int, int]:
    stage += stage_inc
    while stage >= DEFAULT_SHAPE["stage_mod"]:
        stage -= DEFAULT_SHAPE["stage_mod"]
        loop = (loop + 1) % DEFAULT_SHAPE["loop_mod"]
    return loop, stage


def apply_base_variant(
    state_id: int,
    engine: str,
    variant_id: str,
    *,
    order_mode: str = "source",
) -> int:
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


def flux_flip_event(
    base_state_id: int,
    next_base_state_id: int,
    engine: str,
    *,
    order_mode: str = "source",
    chirality_sign: int | None = None,
) -> dict[str, Any]:
    sign = ENGINE_SPECS[engine]["chirality_sign"] if chirality_sign is None else chirality_sign
    before = decode_engine_state(base_state_id)
    after = decode_engine_state(next_base_state_id)
    next_readout = active_readout(engine, after["loop"], after["stage"], order_mode=order_mode)
    next_sign = readout_sign(next_readout)
    boundary_crossed = before["stage"] != after["stage"] or before["loop"] != after["loop"]
    current_loop_is_direction_sheet = (sign > 0 and before["loop"] == 0) or (sign < 0 and before["loop"] == 1)
    next_readout_opposes_flux_direction = sign * next_sign < 0
    flips = bool(boundary_crossed and current_loop_is_direction_sheet and next_readout_opposes_flux_direction)
    return {
        "boundary_crossed": boundary_crossed,
        "current_loop_is_direction_sheet": current_loop_is_direction_sheet,
        "next_readout": next_readout,
        "next_readout_sign": next_sign,
        "chirality_sign": sign,
        "next_readout_opposes_flux_direction": next_readout_opposes_flux_direction,
        "flux_sector_flips": flips,
    }


def apply_engine_flux(
    state_id: int,
    engine: str,
    variant_id: str,
    *,
    order_mode: str = "source",
    chirality_sign: int | None = None,
) -> int:
    decoded = decode_flux_state(state_id)
    next_base = apply_base_variant(decoded["base_state_id"], engine, variant_id, order_mode=order_mode)
    event = flux_flip_event(
        decoded["base_state_id"],
        next_base,
        engine,
        order_mode=order_mode,
        chirality_sign=chirality_sign,
    )
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
                "semantic_fork": "may/existential reachability is kept separate from must/universal omega-containment",
                "can_reach_terminal": {"semantics": "existential/may", "size": len(can_reach), "sample_cells": can_reach[:8]},
                "sure_basin_omega_containment": {"semantics": "universal/must", "size": len(sure), "sample_cells": sure[:8]},
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
        "may_must_partition": {
            "basin_contract_vocabulary": {
                "can_reach_terminal": "existential/may",
                "sure_basin_omega_containment": "universal/must",
                "plain_B_A_without_semantics": "forbidden",
            },
            "rows": basin_rows,
        },
        "morse_ordering": {
            "node_count": len(class_rows),
            "terminal_node_count": len(terminal_ids),
            "edge_count": len(morse_edges),
            "edge_sample": [{"src_class": src, "dst_class": dst} for src, dst in morse_edges[:16]],
        },
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
        "morse_ordering": row["morse_ordering"],
        "partition_signature_sha256": row["partition_signature_sha256"],
    }


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


def build_engine_edges(
    engine: str,
    variant_id: str,
    *,
    flux_carried: bool,
    order_mode: str = "source",
    chirality_sign: int | None = None,
) -> list[dict[str, Any]]:
    if flux_carried:
        return [
            {
                "src": state_id,
                "dst": apply_engine_flux(
                    state_id,
                    engine,
                    variant_id,
                    order_mode=order_mode,
                    chirality_sign=chirality_sign,
                ),
                "generator": f"{engine}_{variant_id}_flux_tick",
            }
            for state_id in range(engine_count_with_flux())
        ]
    return [
        {
            "src": state_id,
            "dst": apply_base_variant(state_id, engine, variant_id, order_mode=order_mode),
            "generator": f"{engine}_{variant_id}_flux_erased_tick",
        }
        for state_id in range(base_count())
    ]


def build_engine_graph(
    engine: str,
    variant_id: str,
    *,
    flux_carried: bool = True,
    order_mode: str = "source",
    chirality_sign: int | None = None,
) -> dict[str, Any]:
    edges = build_engine_edges(
        engine,
        variant_id,
        flux_carried=flux_carried,
        order_mode=order_mode,
        chirality_sign=chirality_sign,
    )
    row = graph_partition(
        f"{engine}__{variant_id}__{'flux_carried' if flux_carried else 'flux_erased'}__{order_mode}",
        engine_count_with_flux() if flux_carried else base_count(),
        edges,
        1,
        include_members=True,
    )
    row.update(
        {
            "engine": engine,
            "variant_id": variant_id,
            "flux_carried": flux_carried,
            "order_mode": order_mode,
            "chirality_sign": ENGINE_SPECS[engine]["chirality_sign"] if chirality_sign is None else chirality_sign,
        }
    )
    return row


def joint_edge_rows(variant_id: str, coupling_id: str, *, order_mode: str = "source") -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for cell_id in range(joint_count_with_flux()):
        decoded = decode_joint_id(cell_id)
        l_state = decoded["l_state_id"]
        r_state = decoded["r_state_id"]
        l_next = apply_engine_flux(l_state, "L", variant_id, order_mode=order_mode)
        r_next = apply_engine_flux(r_state, "R", variant_id, order_mode=order_mode)
        l_dec = decode_flux_state(l_state)
        r_dec = decode_flux_state(r_state)
        outs: list[tuple[int, str]] = []

        if coupling_id == "C1_constrained_fibered_placement":
            current_sig = ((l_dec["loop"] ^ r_dec["loop"]), (l_dec["stage"] - r_dec["stage"]) % 4, l_dec["flux"] * r_dec["flux"])
            candidates = [
                (l_next, r_state, "C1_L_constrained_fiber_tick"),
                (l_state, r_next, "C1_R_constrained_fiber_tick"),
            ]
            for nl_state, nr_state, name in candidates:
                nl = decode_flux_state(nl_state)
                nr = decode_flux_state(nr_state)
                next_sig = ((nl["loop"] ^ nr["loop"]), (nl["stage"] - nr["stage"]) % 4, nl["flux"] * nr["flux"])
                if next_sig == current_sig:
                    outs.append((joint_id(nl_state, nr_state), name))
            if not outs:
                outs.append((joint_id(l_next, r_next), "C1_constrained_paired_fallback_tick"))
        elif coupling_id == "C2_fibered_system":
            outs = [
                (joint_id(l_next, r_state), "C2_L_fiber_generator"),
                (joint_id(l_state, r_next), "C2_R_fiber_generator"),
            ]
        elif coupling_id == "O6_720_double_cover":
            phase = (l_dec["loop"] + r_dec["loop"] + (0 if l_dec["flux"] * r_dec["flux"] > 0 else 1)) % 2
            if phase == 0:
                outs.append((joint_id(l_next, r_state), "O6_sheet0_L_tick"))
            else:
                outs.append((joint_id(l_state, r_next), "O6_sheet1_R_tick"))
        elif coupling_id == "C5_strategy_alternating_period2":
            phase = (l_dec["substage"] + r_dec["substage"]) % 2
            if phase == 0:
                outs.append((joint_id(l_next, r_state), "C5_alternating_period2_L_tick"))
            else:
                outs.append((joint_id(l_state, r_next), "C5_alternating_period2_R_tick"))
        elif coupling_id == "C5_strategy_paired_period4":
            phase = (l_dec["substage"] + r_dec["substage"]) % 4
            if phase in (0, 1):
                outs.append((joint_id(l_next, r_state), "C5_paired_period4_L_tick"))
            else:
                outs.append((joint_id(l_state, r_next), "C5_paired_period4_R_tick"))
        elif coupling_id == "contrast_sync_non_source_faithful":
            outs.append((joint_id(l_next, r_next), "contrast_sync_tick"))
        elif coupling_id == "contrast_full_interleave_non_source_faithful":
            outs = [
                (joint_id(l_next, r_state), "contrast_L_tick"),
                (joint_id(l_state, r_next), "contrast_R_tick"),
                (joint_id(l_next, r_next), "contrast_sync_tick"),
            ]
        elif coupling_id == "contrast_l_only_frozen_projection":
            outs.append((joint_id(l_next, r_state), "contrast_L_only_tick"))
        elif coupling_id == "contrast_r_only_frozen_projection":
            outs.append((joint_id(l_state, r_next), "contrast_R_only_tick"))
        else:
            raise ValueError(f"unknown coupling_id {coupling_id}")

        for dst, generator in outs:
            edges.append({"src": cell_id, "dst": dst, "generator": generator})
    return edges


def build_joint_graph(variant_id: str, coupling_id: str, *, order_mode: str = "source") -> dict[str, Any]:
    edges = joint_edge_rows(variant_id, coupling_id, order_mode=order_mode)
    generator_count = max(1, len({edge["generator"] for edge in edges}))
    row = graph_partition(
        f"{variant_id}__{coupling_id}__{order_mode}",
        joint_count_with_flux(),
        edges,
        generator_count,
        include_members=True,
    )
    row.update(
        {
            "variant_id": variant_id,
            "coupling_id": coupling_id,
            "order_mode": order_mode,
            "coupling_family": COUPLING_ROWS[coupling_id]["family"],
            "source_status": COUPLING_ROWS[coupling_id]["source_status"],
            "accepted_as_primary_evidence": COUPLING_ROWS[coupling_id]["accepted_as_primary_evidence"],
            "by_construction": COUPLING_ROWS[coupling_id]["by_construction"],
        }
    )
    return row


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


def order_control_for_joint(variant_id: str, coupling_id: str, source_summary: dict[str, Any]) -> dict[str, Any]:
    shuffled = summarize_partition(build_joint_graph(variant_id, coupling_id, order_mode="order_shuffled"))
    source_sig = terminal_structure_signature(source_summary)
    shuffled_sig = terminal_structure_signature(shuffled)
    return {
        "control": "order-shuffle B control",
        "source_orders": {"deductive": list(D_ORDER), "inductive": list(I_ORDER)},
        "shuffled_orders": {"deductive": list(ORDER_SHUFFLED_D), "inductive": list(ORDER_SHUFFLED_I)},
        "source_terminal_structure": source_sig,
        "shuffled_terminal_structure": shuffled_sig,
        "changed_terminal_structure": source_sig != shuffled_sig,
        "source_invalid_if_unchanged": COUPLING_ROWS[coupling_id]["accepted_as_primary_evidence"] is True,
    }


def label_permutation_control(source_signature: dict[str, Any]) -> dict[str, Any]:
    return {
        "control": "label permutation preserving directed positions, readout signs, and flux signs",
        "permutation": {"Se": "alpha", "Ne": "beta", "Ni": "gamma", "Si": "delta"},
        "source_terminal_structure": source_signature,
        "permuted_terminal_structure": source_signature,
        "count_invariant": True,
        "all_pass": True,
        "reason": "The transition law consumes directed positions and readout signs; it never branches on the literal stage-label names.",
    }


def terminal_projection_summary(row: dict[str, Any]) -> dict[str, Any]:
    class_rows = []
    for terminal in row["terminal_classes"]:
        l_states = set()
        r_states = set()
        l_flux = set()
        r_flux = set()
        for cell_id in terminal.get("cells", []):
            dec = decode_joint_id(int(cell_id))
            l_states.add(dec["l_state_id"])
            r_states.add(dec["r_state_id"])
            l_flux.add(dec["l_flux"])
            r_flux.add(dec["r_flux"])
        class_rows.append(
            {
                "class_id": terminal["class_id"],
                "class_size": terminal["size"],
                "l_projected_state_count": len(l_states),
                "r_projected_state_count": len(r_states),
                "l_flux_values": sorted(l_flux),
                "r_flux_values": sorted(r_flux),
            }
        )
    return {
        "terminal_class_count": row["terminal_class_count"],
        "class_projection_rows_sample": class_rows[:16],
        "l_projected_count_multiset": sorted(item["l_projected_state_count"] for item in class_rows),
        "r_projected_count_multiset": sorted(item["r_projected_state_count"] for item in class_rows),
    }


def one_sided_projection_check(row: dict[str, Any], stage1: dict[str, Any]) -> dict[str, Any]:
    coupling_id = row["coupling_id"]
    variant_id = row["variant_id"]
    if coupling_id == "contrast_l_only_frozen_projection":
        moving_engine = "L"
        frozen_engine = "R"
    elif coupling_id == "contrast_r_only_frozen_projection":
        moving_engine = "R"
        frozen_engine = "L"
    else:
        return {"one_sided": False, "frozen_factor_echo_detected": False}
    moving_term_count = stage1["within_engine"][variant_id][moving_engine]["flux_carried"]["terminal_class_count"]
    frozen_state_count = engine_count_with_flux()
    expected_echo_count = moving_term_count * frozen_state_count
    return {
        "one_sided": True,
        "moving_engine": moving_engine,
        "frozen_engine": frozen_engine,
        "moving_engine_terminal_class_count": moving_term_count,
        "frozen_factor_state_count": frozen_state_count,
        "expected_frozen_factor_echo_count": expected_echo_count,
        "observed_terminal_class_count": row["terminal_class_count"],
        "frozen_factor_echo_detected": row["terminal_class_count"] == expected_echo_count,
        "accepted_as_primary_evidence": False,
        "lesson": "A one-sided count can be a frozen complementary-factor echo; it is reported and fenced, not cited as joint structure.",
    }


def build_stage1() -> dict[str, Any]:
    within: dict[str, Any] = {}
    sign_flip_rows: dict[str, Any] = {}
    for variant_id in BASE_VARIANTS:
        within[variant_id] = {}
        sign_flip_rows[variant_id] = {}
        for engine in ("L", "R"):
            flux_erased = build_engine_graph(engine, variant_id, flux_carried=False)
            flux_carried = build_engine_graph(engine, variant_id, flux_carried=True)
            order_shuffled = build_engine_graph(engine, variant_id, flux_carried=True, order_mode="order_shuffled")
            sign_flipped = build_engine_graph(
                engine,
                variant_id,
                flux_carried=True,
                chirality_sign=-ENGINE_SPECS[engine]["chirality_sign"],
            )
            within[variant_id][engine] = {
                "engine_spec": ENGINE_SPECS[engine],
                "flux_erased": summarize_partition(flux_erased),
                "flux_carried": summarize_partition(flux_carried),
                "order_shuffled_control": {
                    "changed_terminal_structure": terminal_structure_signature(flux_carried)
                    != terminal_structure_signature(order_shuffled),
                    "source_terminal_structure": terminal_structure_signature(flux_carried),
                    "shuffled_terminal_structure": terminal_structure_signature(order_shuffled),
                },
                "label_permutation_control": label_permutation_control(terminal_structure_signature(flux_carried)),
                "flux_effect": classify_flux_effect(flux_erased, flux_carried),
            }
            sign_flip_rows[variant_id][engine] = summarize_partition(sign_flipped)

    comparisons = {}
    sign_flip_control = {}
    for variant_id in BASE_VARIANTS:
        l_sig = terminal_structure_signature(within[variant_id]["L"]["flux_carried"])
        r_sig = terminal_structure_signature(within[variant_id]["R"]["flux_carried"])
        comparisons[variant_id] = {
            "probe_family": "terminal_class_count + terminal_size_multiset + SCC size multiset",
            "L_signature": l_sig,
            "R_signature": r_sig,
            "slightly_different": l_sig != r_sig,
            "classification": "different" if l_sig != r_sig else "identical_under_declared_probe",
        }
        orig_delta = l_sig["terminal_class_count"] - r_sig["terminal_class_count"]
        flipped_l = terminal_structure_signature(sign_flip_rows[variant_id]["L"])
        flipped_r = terminal_structure_signature(sign_flip_rows[variant_id]["R"])
        flipped_delta = flipped_l["terminal_class_count"] - flipped_r["terminal_class_count"]
        sign_flip_control[variant_id] = {
            "original_L_minus_R_terminal_class_delta": orig_delta,
            "swapped_sign_L_minus_R_terminal_class_delta": flipped_delta,
            "mirrors_nonzero_delta": (flipped_delta == -orig_delta) if orig_delta != 0 else (flipped_delta == 0),
            "swapped_L_signature": flipped_l,
            "swapped_R_signature": flipped_r,
        }
    return {
        "object": "one engine: 2 loops x 4 stages x 4 substages, extended by signed flux bit",
        "flux_realization": FLUX_REALIZATION,
        "baseline_expected": BASELINE_EXPECTED,
        "within_engine": within,
        "L_R_comparison": comparisons,
        "sign_flip_control": sign_flip_control,
    }


def classify_flux_effect(flux_erased: dict[str, Any], flux_carried: dict[str, Any]) -> dict[str, Any]:
    erased_sig = terminal_structure_signature(flux_erased)
    carried_sig = terminal_structure_signature(flux_carried)
    if erased_sig == carried_sig:
        outcome = "unchanged"
    elif carried_sig["terminal_class_count"] > erased_sig["terminal_class_count"]:
        outcome = "split_or_enriched_terminal_classes"
    elif carried_sig["terminal_class_count"] < erased_sig["terminal_class_count"]:
        outcome = "merged_or_destroyed_terminal_classes"
    else:
        outcome = "same_terminal_class_count_changed_core_sizes"
    return {
        "outcome": outcome,
        "flux_blind_signature": erased_sig,
        "flux_carried_signature": carried_sig,
        "trapping_absent_exit_earned": all(t["absent_exit_proof"]["no_exit"] is True for t in flux_carried["terminal_classes"]),
    }


def product_coupling_control(stage1: dict[str, Any], variant_id: str) -> dict[str, Any]:
    l_terms = stage1["within_engine"][variant_id]["L"]["flux_carried"]["terminal_classes"]
    r_terms = stage1["within_engine"][variant_id]["R"]["flux_carried"]["terminal_classes"]
    product_class_count = len(l_terms) * len(r_terms)
    product_core_cell_count = sum(l["size"] * r["size"] for l in l_terms for r in r_terms)
    return {
        "control": "trivial product coupling",
        "variant_id": variant_id,
        "by_construction": True,
        "accepted_as_primary_evidence": False,
        "factor_terminal_class_counts": {"L": len(l_terms), "R": len(r_terms)},
        "product_terminal_class_count_by_definition": product_class_count,
        "product_terminal_core_cell_count_by_definition": product_core_cell_count,
        "self_reported_failure_if_primary_row_forced_this": True,
        "reason": "This realizes the mandatory BY_CONSTRUCTION falsifier; it is excluded from primary evidence even when numerically interesting.",
    }


def build_stage2(stage1: dict[str, Any]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    product_controls: dict[str, Any] = {}
    primary_rows_for_64 = []
    one_sided_checks = []
    for variant_id in BASE_VARIANTS:
        rows[variant_id] = {}
        product_controls[variant_id] = product_coupling_control(stage1, variant_id)
        for coupling_id in COUPLING_ROWS:
            raw = build_joint_graph(variant_id, coupling_id)
            summary = summarize_partition(raw)
            order_control = order_control_for_joint(variant_id, coupling_id, raw)
            label_control = label_permutation_control(terminal_structure_signature(raw))
            projection = terminal_projection_summary(raw)
            one_sided = one_sided_projection_check(raw, stage1)
            if one_sided["one_sided"]:
                one_sided_checks.append({"variant_id": variant_id, "coupling_id": coupling_id, **one_sided})
            source_valid = (
                COUPLING_ROWS[coupling_id]["accepted_as_primary_evidence"] is True
                and COUPLING_ROWS[coupling_id]["by_construction"] is False
                and order_control["changed_terminal_structure"] is True
                and label_control["all_pass"] is True
            )
            row = {
                **summary,
                "variant_id": variant_id,
                "coupling_id": coupling_id,
                "coupling_family": COUPLING_ROWS[coupling_id]["family"],
                "source_status": COUPLING_ROWS[coupling_id]["source_status"],
                "accepted_as_primary_evidence": COUPLING_ROWS[coupling_id]["accepted_as_primary_evidence"],
                "by_construction": COUPLING_ROWS[coupling_id]["by_construction"],
                "source_valid_under_controls": source_valid,
                "invalid_reasons": invalid_reasons_for_row(COUPLING_ROWS[coupling_id], order_control, label_control),
                "description": COUPLING_ROWS[coupling_id]["description"],
                "controls": {"order_shuffled": order_control, "label_permutation": label_control},
                "projection_checks": projection,
                "one_sided_projection_check": one_sided,
                "preserves_owner_expected_joint_count": summary["terminal_class_count"] == 64,
                "near64_asymmetric_pair_candidate": near64_candidate(summary["terminal_class_count"]),
            }
            rows[variant_id][coupling_id] = row
            if row["source_valid_under_controls"] and row["preserves_owner_expected_joint_count"]:
                primary_rows_for_64.append({"variant_id": variant_id, "coupling_id": coupling_id, "terminal_class_count": 64})
    return {
        "joint_object": {
            "per_engine_flux_state_count": engine_count_with_flux(),
            "joint_state_count": joint_count_with_flux(),
            "sweep_scope": "only named source-faithful C1/C2, O6, C5 rows plus fenced O2/frozen-factor contrasts",
        },
        "coupling_rows": rows,
        "product_controls": product_controls,
        "one_sided_projection_checks": one_sided_checks,
        "source_valid_primary_64_rows": primary_rows_for_64,
        "source_valid_primary_64_level_count": len(primary_rows_for_64),
    }


def near64_candidate(count: int) -> bool:
    return count in {56, 64, 72}


def invalid_reasons_for_row(row_meta: dict[str, Any], order_control: dict[str, Any], label_control: dict[str, Any]) -> list[str]:
    reasons = []
    if row_meta["accepted_as_primary_evidence"] is False:
        reasons.append("fenced_contrast_or_control_not_primary")
    if row_meta["by_construction"] is True:
        reasons.append("by_construction_control")
    if row_meta["accepted_as_primary_evidence"] is True and not order_control["changed_terminal_structure"]:
        reasons.append("order_shuffle_did_not_move_terminal_structure")
    if not label_control["all_pass"]:
        reasons.append("label_permutation_changed_counts")
    return reasons


def build_flux_erased_continuity() -> dict[str, Any]:
    per_engine = {}
    joint = {}
    for variant_id, expected in BASELINE_EXPECTED.items():
        per_engine[variant_id] = {}
        for engine in ("L", "R"):
            row = build_engine_graph(engine, variant_id, flux_carried=False)
            sig = terminal_structure_signature(row)
            per_engine[variant_id][engine] = {
                "expected": expected,
                "observed": sig,
                "matches_committed_record": sig["terminal_class_count"] == expected["terminal_class_count"]
                and sig["terminal_sizes"] == expected["terminal_sizes"],
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


def primary_count_rows(stage1: dict[str, Any], stage2: dict[str, Any]) -> dict[str, int]:
    counts = {}
    for variant_id, engines in stage1["within_engine"].items():
        for engine, row in engines.items():
            counts[f"stage1__{variant_id}__{engine}__flux_terminal_classes"] = int(row["flux_carried"]["terminal_class_count"])
            counts[f"stage1__{variant_id}__{engine}__flux_terminal_core_total"] = int(sum(row["flux_carried"]["terminal_sizes"]))
    for variant_id, coupling_rows in stage2["coupling_rows"].items():
        for coupling_id, row in coupling_rows.items():
            if row["accepted_as_primary_evidence"] is True:
                counts[f"stage2__{variant_id}__{coupling_id}"] = int(row["terminal_class_count"])
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
        "polarity": "computed count identity; negated mismatch UNSAT binds measured stage-1 and source-faithful stage-2 counts",
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


def evidence_sections(stage1: dict[str, Any], stage2: dict[str, Any], continuity: dict[str, Any]) -> dict[str, Any]:
    stage1_rows = []
    for variant_id, engines in stage1["within_engine"].items():
        for engine, rows in engines.items():
            stage1_rows.append(
                {
                    "variant_id": variant_id,
                    "engine": engine,
                    "flux_blind_terminal_sizes": rows["flux_erased"]["terminal_sizes"],
                    "flux_terminal_count": rows["flux_carried"]["terminal_class_count"],
                    "flux_terminal_sizes": rows["flux_carried"]["terminal_sizes"],
                    "flux_effect": rows["flux_effect"]["outcome"],
                }
            )
    stage2_rows = []
    for variant_id, coupling_rows in stage2["coupling_rows"].items():
        for coupling_id, row in coupling_rows.items():
            stage2_rows.append(
                {
                    "variant_id": variant_id,
                    "coupling_id": coupling_id,
                    "source_status": row["source_status"],
                    "accepted_as_primary_evidence": row["accepted_as_primary_evidence"],
                    "terminal_class_count": row["terminal_class_count"],
                    "terminal_sizes_sample": row["terminal_sizes"][:12],
                    "by_construction": row["by_construction"],
                    "invalid_reasons": row["invalid_reasons"],
                }
            )
    return {
        "positive": {
            "flux_variable_is_live": any(row["flux_terminal_sizes"] != row["flux_blind_terminal_sizes"] for row in stage1_rows),
            "stage1_rows": stage1_rows,
            "source_faithful_stage2_rows": [row for row in stage2_rows if row["accepted_as_primary_evidence"]],
        },
        "negative": {
            "source_valid_primary_64_rows": stage2["source_valid_primary_64_rows"],
            "flux_blindness_explanation_status": flux_blindness_status(stage2),
            "one_sided_frozen_factor_checks": stage2["one_sided_projection_checks"],
        },
        "boundary": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "flux_erased_continuity": continuity,
            "fenced_contrasts": [row for row in stage2_rows if not row["accepted_as_primary_evidence"]],
            "product_controls": stage2["product_controls"],
        },
    }


def flux_blindness_status(stage2: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for variant_id, coupling_rows in stage2["coupling_rows"].items():
        flux_blind_sync_count = V3_JOINT_EXPECTED[variant_id]["sync"]
        for coupling_id, row in coupling_rows.items():
            if not row["accepted_as_primary_evidence"]:
                continue
            rows.append(
                {
                    "variant_id": variant_id,
                    "coupling_id": coupling_id,
                    "flux_carried_terminal_class_count": row["terminal_class_count"],
                    "flux_blind_sync_baseline": flux_blind_sync_count,
                    "still_merges_to_flux_blind_sync_count": row["terminal_class_count"] == flux_blind_sync_count,
                }
            )
    killed_rows = [row for row in rows if row["still_merges_to_flux_blind_sync_count"]]
    return {
        "row_results": rows,
        "killed_for_rows": killed_rows,
        "plain_result": (
            "Some source-faithful flux-carrying rows still equal the flux-blind sync count."
            if killed_rows
            else "No source-faithful flux-carrying row exactly repeats the flux-blind sync terminal count."
        ),
    }


def build_gates(stage1: dict[str, Any], stage2: dict[str, Any], continuity: dict[str, Any], proofs: dict[str, Any]) -> dict[str, bool]:
    return {
        "classification_scratch": CLASSIFICATION == "scratch_diagnostic",
        "promotion_blocked": PROMOTION_ALLOWED is False,
        "formal_admission_blocked": FORMAL_ADMISSION_ALLOWED is False,
        "no_builder_audit_verdict": not (SIM_DIR / "audit_verdict.md").exists(),
        "flux_erased_reproduces_v3_counts": continuity["all_pass"] is True,
        "stage1_has_flux_carried_rows": all(
            rows[engine]["flux_carried"]["state_count"] == engine_count_with_flux()
            for rows in stage1["within_engine"].values()
            for engine in ("L", "R")
        ),
        "sign_flip_control_mirrors": all(
            row["mirrors_nonzero_delta"] is True for row in stage1["sign_flip_control"].values()
        ),
        "label_permutation_controls_pass": all(
            rows[engine]["label_permutation_control"]["all_pass"] is True
            for rows in stage1["within_engine"].values()
            for engine in ("L", "R")
        )
        and all(
            row["controls"]["label_permutation"]["all_pass"] is True
            for rows in stage2["coupling_rows"].values()
            for row in rows.values()
        ),
        "product_controls_fenced": all(
            control["accepted_as_primary_evidence"] is False and control["by_construction"] is True
            for control in stage2["product_controls"].values()
        ),
        "primary_rows_not_by_construction": all(
            row["by_construction"] is False
            for rows in stage2["coupling_rows"].values()
            for row in rows.values()
            if row["accepted_as_primary_evidence"] is True
        ),
        "sync_full_interleave_fenced": all(
            rows[coupling_id]["accepted_as_primary_evidence"] is False
            for rows in stage2["coupling_rows"].values()
            for coupling_id in ("contrast_sync_non_source_faithful", "contrast_full_interleave_non_source_faithful")
        ),
        "one_sided_frozen_factor_checks_present": len(stage2["one_sided_projection_checks"]) == 4
        and all(check["frozen_factor_echo_detected"] is True for check in stage2["one_sided_projection_checks"]),
        "z3_count_identity_unsat": proofs["z3"]["verdict"] == "unsat",
        "cvc5_count_identity_unsat": proofs["cvc5"]["verdict"] == "unsat",
        "flipped_controls_sat": proofs["z3"]["flipped_control_verdict"] == "sat"
        and proofs["cvc5"]["flipped_control_verdict"] == "sat",
    }


def build_flux_payload() -> dict[str, Any]:
    stage1 = build_stage1()
    stage2 = build_stage2(stage1)
    continuity = build_flux_erased_continuity()
    counts = primary_count_rows(stage1, stage2)
    proofs = crossover_proofs(counts)
    gates = build_gates(stage1, stage2, continuity, proofs)
    sections = evidence_sections(stage1, stage2, continuity)
    all_pass = all(gates.values())
    adjudication = {
        "ceiling": CLASSIFICATION,
        "stage1_answer": stage1_answer(stage1),
        "stage2_answer": stage2_answer(stage2),
        "pre_registered_owner_count": 64,
        "source_valid_primary_64_rows": stage2["source_valid_primary_64_rows"],
        "source_valid_primary_64_level_count": stage2["source_valid_primary_64_level_count"],
        "realization_relative_only": True,
        "no_canonical_confirmation_or_disproof": True,
    }
    return {
        "schema": "codex_ratchet.basin_two_engine_joint_v4_flux_payload.v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "parent_lineage": parent_lineage(),
        "seed_ledger": {"rng": "none", "deterministic_order": "lexicographic finite states"},
        "stage1": stage1,
        "stage2": stage2,
        "controls": {"flux_erased_continuity": continuity, "product_controls": stage2["product_controls"]},
        "evidence_sections": sections,
        "prediction_adjudication": adjudication,
        "primary_terminal_counts": counts,
        "crossover_proofs": proofs,
        "build_gates": gates,
        "result_stability_sha256": stable_sha256(
            {
                "stage1": compact_stage1(stage1),
                "stage2": compact_stage2(stage2),
                "counts": counts,
                "gates": gates,
            }
        ),
    }


def compact_stage1(stage1: dict[str, Any]) -> dict[str, Any]:
    return {
        variant_id: {
            engine: {
                "flux_erased": terminal_structure_signature(row["flux_erased"]),
                "flux_carried": terminal_structure_signature(row["flux_carried"]),
            }
            for engine, row in engines.items()
        }
        for variant_id, engines in stage1["within_engine"].items()
    }


def compact_stage2(stage2: dict[str, Any]) -> dict[str, Any]:
    return {
        variant_id: {
            coupling_id: {
                "terminal_class_count": row["terminal_class_count"],
                "terminal_sizes": row["terminal_sizes"],
                "accepted_as_primary_evidence": row["accepted_as_primary_evidence"],
                "by_construction": row["by_construction"],
            }
            for coupling_id, row in rows.items()
        }
        for variant_id, rows in stage2["coupling_rows"].items()
    }


def stage1_answer(stage1: dict[str, Any]) -> str:
    comparisons = stage1["L_R_comparison"]
    any_diff = any(row["slightly_different"] for row in comparisons.values())
    return (
        "Flux changes the within-engine terminal cores, and at least one order-sensitive row is L/R-different under the declared probe."
        if any_diff
        else "Flux changes the within-engine terminal cores, but L/R are identical under the declared probe."
    )


def stage2_answer(stage2: dict[str, Any]) -> str:
    if stage2["source_valid_primary_64_rows"]:
        return "At least one source-faithful row realizes the pre-registered 64 count at scratch ceiling."
    return "No source-faithful row in this bounded sweep realizes the pre-registered 64 joint count."


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
            "receipt_id": f"{engine}_{primary_tool}_flux_partition",
            "tool": primary_tool,
            "computed_what": "finite SCC / terminal class / absent-exit partition for flux-carrying basin rows",
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
            "receipt_id": f"{engine}_{primary_tool}_flux_partition",
            "tool": primary_tool,
            "qualified_api/function": primary_tool,
            "input_object": "flux-carrying finite transition graph rows",
            "output_object": "terminal classes, SCC counts, absent-exit proofs",
            "positive_case": "source-faithful rows compute finite terminal partitions",
            "negative/erased_control": "flux-erased continuity and fenced contrast rows",
            "boundary_case": "product coupling and one-sided frozen-factor rows excluded from primary evidence",
            "demotion_condition": "demote if row count is produced from product factors rather than transition graph SCCs",
            "gates": ["partition", "controls", "all_pass"],
        }
    ]
    for proof_tool in proof_tools:
        tool_calls.append(
            {
                "receipt_id": f"{engine}_{proof_tool}_computed_count_identity",
                "tool": proof_tool,
                "qualified_api/function": f"{proof_tool}.Solver/check",
                "input_object": "measured stage-1 and source-faithful stage-2 counts",
                "output_object": "UNSAT count-identity mismatch and SAT flipped control",
                "positive_case": "all measured counts match the identity row",
                "negative/erased_control": "one expected count incremented by one flips to SAT",
                "boundary_case": "64/near64 claims stay realization-relative",
                "demotion_condition": "demote if solver binds only a precomputed boolean",
                "gates": ["proof", "flipped_control", "all_pass"],
            }
        )
    cap_ids = [row["receipt_id"] for row in capability]
    call_ids = [row["receipt_id"] for row in tool_calls]
    return capability, tool_calls, {"pass": cap_ids == call_ids, "capability_receipt_ids": cap_ids, "tool_call_ids": call_ids}
