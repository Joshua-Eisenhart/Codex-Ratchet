#!/usr/bin/env python3
"""Shared sweep machinery for basin_generating_set_sweep_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import cvc5
from cvc5 import Kind
import networkx as nx
import sympy as sp
import z3


SIM_ID = "basin_generating_set_sweep_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
PARENT_SIM_DIR = ROOT / "system_v6" / "sims" / "basin_rc_transition_graph_v0"
PARENT_RESULT_PATH = PARENT_SIM_DIR / "results" / "basin_rc_transition_graph_v0_envelope_results.json"
PARENT_COMMON = PARENT_SIM_DIR / "basin_rc_transition_graph_v0_common.py"

if str(PARENT_SIM_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_SIM_DIR))

import basin_rc_transition_graph_v0_common as parent


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED_LEDGER = {"rng": "none", "deterministic_tie_break": "cell_id_ascending"}
BASELINE_NAMES = ["Se_Funnel_L", "Ni_Pit_L", "Ni_Source_R", "Ne_Spiral_R", "D_z", "R_x"]
G1_NAMES = ["R_x", "R_z", "Ne_Spiral_R", "Ne_Vortex_L"]
G5_WORD = ("Ni_Pit_L", "R_x")
EXPECTED_TERMINAL_COUNTS = {"G0": 1, "G1": 3, "G2": 1, "G3L": 3, "G3R": 3, "G4": 1, "G5": 5}

PARENT_PATHS = {
    "basin_rc_transition_graph_v0_envelope": PARENT_RESULT_PATH,
    "basin_rc_transition_graph_v0_common": PARENT_COMMON,
    "basin_contract": ROOT / "system_v6/receipts/attractor_basin_criterion_20260611.md",
    "geo_s5_terrain_flows_v0_envelope": ROOT
    / "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json",
    "geo_s4_operator_stage_v0_envelope": ROOT
    / "system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json",
}
PARENT_COMMIT_HINTS = {
    "basin_rc_transition_graph_v0": "631f1c3db",
    "basin_contract": "000f48e71",
    "s4_s5_generator_inventory": "committed source inventory",
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
        return subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%H", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def parent_lineage() -> dict[str, Any]:
    return {
        "consumed_inputs": [
            {
                "id": key,
                "path": rel(path),
                "sha256": sha256_file(path),
                "commit_hint": PARENT_COMMIT_HINTS.get(key)
                or PARENT_COMMIT_HINTS.get(key.replace("_envelope", ""))
                or PARENT_COMMIT_HINTS.get("s4_s5_generator_inventory"),
                "git_last_commit": git_last_commit(path),
            }
            for key, path in PARENT_PATHS.items()
            if path.exists()
        ],
        "parent_committed_hash_bound": {
            "basin_rc_transition_graph_v0": "631f1c3db",
            "basin_contract": "000f48e71",
            "s4_s5_generator_inventory": "committed",
        },
        "builder_output_only": True,
    }


def load_all_generators(expm_fn: Callable[[list[list[float]], float], list[list[float]]]) -> dict[str, Any]:
    s5 = load_json(PARENT_PATHS["geo_s5_terrain_flows_v0_envelope"])
    s4 = load_json(PARENT_PATHS["geo_s4_operator_stage_v0_envelope"])
    generators: dict[str, dict[str, Any]] = {}
    source_rows: dict[str, Any] = {}
    for name, row in sorted(s5["bloch_generator_table"].items()):
        matrix, offset = parent.affine_from_terrain(row, expm_fn)
        generators[name] = {"name": name, "kind": "S5_terrain_flow", "h": parent.TERRAIN_H, "M": matrix, "c": offset}
        source_rows[name] = {
            "kind": "S5_terrain_flow",
            "source_ref": row.get("source_ref"),
            "family": row.get("family"),
            "symbolic": row.get("symbolic"),
            "pinned_A": row["pinned"]["A"],
            "pinned_b": row["pinned"]["b"],
            "h": parent.TERRAIN_H,
        }
    for name, row in sorted(s4["affine_channel_table"].items()):
        matrix, offset = parent.affine_from_operator(row)
        generators[name] = {"name": name, "kind": "S4_operator_channel", "h": "one_pinned_channel", "M": matrix, "c": offset}
        source_rows[name] = {
            "kind": "S4_operator_channel",
            "basis": row.get("basis"),
            "symbolic": row.get("symbolic"),
            "pinned_M": row["pinned"]["M"],
            "pinned_c": row["pinned"]["c"],
            "h": "one_pinned_channel",
        }
    return {"generators_by_name": generators, "source_rows": source_rows}


def matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def matvec(a: list[list[float]], v: list[float]) -> list[float]:
    return [sum(a[i][j] * v[j] for j in range(3)) for i in range(3)]


def compose_generator(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    matrix = matmul(second["M"], first["M"])
    moved_first_offset = matvec(second["M"], first["c"])
    offset = [moved_first_offset[i] + second["c"][i] for i in range(3)]
    return {
        "name": f"{first['name']}_then_{second['name']}",
        "kind": "composite_two_step_single_move",
        "h": "word_length_2",
        "M": matrix,
        "c": offset,
        "word": [first["name"], second["name"]],
    }


def diagonalized(generator: dict[str, Any]) -> dict[str, Any]:
    out = dict(generator)
    out["name"] = f"{generator['name']}_diagonalized"
    out["kind"] = f"{generator['kind']}_commutative_collapse"
    out["M"] = [[generator["M"][i][j] if i == j else 0.0 for j in range(3)] for i in range(3)]
    return out


def generator_sets(all_rows: dict[str, Any]) -> list[dict[str, Any]]:
    by_name = all_rows["generators_by_name"]
    s5_names = [name for name, row in by_name.items() if row["kind"] == "S5_terrain_flow"]
    s4_names = [name for name, row in by_name.items() if row["kind"] == "S4_operator_channel"]
    left_names = sorted(name for name in s5_names if name.endswith("_L"))
    right_names = sorted(name for name in s5_names if name.endswith("_R"))
    return [
        {
            "set_id": "G0",
            "label": "committed baseline anchor",
            "description": "Committed six-generator baseline re-derived from basin_rc_transition_graph_v0.",
            "generators": [by_name[name] for name in BASELINE_NAMES],
            "conditioned_only": False,
        },
        {
            "set_id": "G1",
            "label": "rotations only",
            "description": "R_x, R_z, Ne_Spiral_R, and Ne_Vortex_L; contraction rows removed.",
            "generators": [by_name[name] for name in G1_NAMES],
            "conditioned_only": False,
        },
        {
            "set_id": "G2",
            "label": "full S5 plus S4 set",
            "description": "All eight terrain flows plus all four operator channels.",
            "generators": [by_name[name] for name in sorted(s5_names) + sorted(s4_names)],
            "conditioned_only": False,
        },
        {
            "set_id": "G3L",
            "label": "L chirality terrain subset",
            "description": "S5 terrain rows whose committed names end in _L.",
            "generators": [by_name[name] for name in left_names],
            "conditioned_only": False,
        },
        {
            "set_id": "G3R",
            "label": "R chirality terrain subset",
            "description": "S5 terrain rows whose committed names end in _R.",
            "generators": [by_name[name] for name in right_names],
            "conditioned_only": False,
        },
        {
            "set_id": "G4",
            "label": "conditioned shell baseline",
            "description": "Baseline generators restricted to conditioned-shell cells; C is tightened before M(C) is recomputed.",
            "generators": [by_name[name] for name in BASELINE_NAMES],
            "conditioned_only": True,
        },
        {
            "set_id": "G5",
            "label": "single composite generator",
            "description": "The noncommuting two-step word Ni_Pit_L then R_x is treated as one move.",
            "generators": [compose_generator(by_name[G5_WORD[0]], by_name[G5_WORD[1]])],
            "conditioned_only": False,
        },
    ]


def cells_for(spec: dict[str, Any], *, root_off: bool = False) -> list[dict[str, Any]]:
    cells = parent.state_cells(root_off=root_off)
    if spec.get("conditioned_only"):
        cells = [cell for cell in cells if cell["conditioned_shell_member"]]
    return cells


def build_graph_for(spec: dict[str, Any], *, root_off: bool = False, generators: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return parent.build_transition_graph(generators or spec["generators"], cells=cells_for(spec, root_off=root_off))


def may_must_sizes(graph: dict[str, Any]) -> tuple[list[int], list[int]]:
    rows = list(graph["basin_map"].values())
    return (
        sorted(row["can_reach_terminal"]["size"] for row in rows),
        sorted(row["sure_basin_omega_containment"]["size"] for row in rows),
    )


def terminal_cells(graph: dict[str, Any]) -> list[list[int]]:
    return [row["cells"] for row in graph["terminal_classes"]]


def fate_for(set_id: str, graph: dict[str, Any]) -> str:
    if set_id == "G0":
        return "anchor"
    if graph["state_count"] < 33 and len(graph["terminal_classes"]) == 1:
        return "shrinks"
    if len(graph["terminal_classes"]) > 1:
        return "SPLITS"
    if len(graph["terminal_classes"]) == 1:
        return "survives"
    return "collapses"


def metastable_rows(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "class_id": row["class_id"],
            "size": row["size"],
            "internal_transition_fraction": row["internal_transition_fraction"],
            "escape_transition_fraction": row["escape_transition_fraction"],
        }
        for row in graph["communicating_classes"]
        if row.get("metastable_almost_invariant")
    ]


def partition_row(spec: dict[str, Any], graph: dict[str, Any], parent_env: dict[str, Any]) -> dict[str, Any]:
    may_sizes, must_sizes = may_must_sizes(graph)
    set_id = spec["set_id"]
    return {
        "set_id": set_id,
        "label": spec["label"],
        "generator_names": [g["name"] for g in spec["generators"]],
        "state_count": graph["state_count"],
        "scc_count": graph["scc_count"],
        "terminal_class_count": len(graph["terminal_classes"]),
        "terminal_class_sizes": sorted(row["size"] for row in graph["terminal_classes"]),
        "terminal_cells": terminal_cells(graph),
        "may_basin_sizes": may_sizes,
        "must_basin_sizes": must_sizes,
        "metastable_classes": metastable_rows(graph),
        "morse_ordering": graph["morse_graph"],
        "partition_signature": graph["partition_signature"],
        "transition_graph_sha256": graph["transition_graph_sha256"],
        "fate": fate_for(set_id, graph),
        "earns_sub_basin_term": len(graph["terminal_classes"]) > 1,
        "baseline_anchor_byte_exact": bool(
            set_id == "G0"
            and graph["partition_signature"] == parent_env["transition_graph"]["partition_signature"]
            and graph["transition_graph_sha256"] == parent_env["transition_graph"]["transition_graph_sha256"]
        )
        if set_id == "G0"
        else None,
    }


def similarity_cluster_contrast(graph: dict[str, Any]) -> dict[str, Any]:
    clusters: dict[str, list[int]] = {"inner": [], "mid": [], "outer": []}
    for cell in graph["cells"]:
        if cell["radius_squared"] <= 0.25:
            clusters["inner"].append(cell["cell_id"])
        elif cell["radius_squared"] <= 0.75:
            clusters["mid"].append(cell["cell_id"])
        else:
            clusters["outer"].append(cell["cell_id"])
    rows = {}
    for name, members in clusters.items():
        member_set = set(members)
        escaping = [row for row in graph["transition_edges"] if row["src"] in member_set and row["dst"] not in member_set]
        rows[name] = {"size": len(members), "closed_under_R_C": len(escaping) == 0, "escaping_edge_count": len(escaping)}
    return {
        "computed": True,
        "fired": any(row["escaping_edge_count"] > 0 for row in rows.values()),
        "basin_language_allowed": False,
        "clusters": rows,
    }


def compare_signatures(base: dict[str, Any], other: dict[str, Any]) -> dict[str, Any]:
    return {
        "partition_changed": base["partition_signature"] != other["partition_signature"],
        "base_signature": base["partition_signature"],
        "variant_signature": other["partition_signature"],
    }


def root_off_contrast(spec: dict[str, Any], graph: dict[str, Any]) -> dict[str, Any]:
    root_graph = build_graph_for(spec, root_off=True)
    return {"computed": True, "fired": graph["partition_signature"] != root_graph["partition_signature"], **compare_signatures(graph, root_graph)}


def g5_commutative_contrast(spec: dict[str, Any], all_rows: dict[str, Any], graph: dict[str, Any]) -> dict[str, Any]:
    by_name = all_rows["generators_by_name"]
    reversed_word = [compose_generator(by_name[G5_WORD[1]], by_name[G5_WORD[0]])]
    diagonal_word = [diagonalized(spec["generators"][0])]
    reversed_graph = build_graph_for(spec, generators=reversed_word)
    diagonal_graph = build_graph_for(spec, generators=diagonal_word)
    return {
        "computed": True,
        "word": list(G5_WORD),
        "reversed_word": list(reversed(G5_WORD)),
        "reversed_partition_changed": graph["partition_signature"] != reversed_graph["partition_signature"],
        "reversed_transition_hash_changed": graph["transition_graph_sha256"] != reversed_graph["transition_graph_sha256"],
        "diagonal_partition_changed": graph["partition_signature"] != diagonal_graph["partition_signature"],
        "reversed_signature": reversed_graph["partition_signature"],
        "diagonal_signature": diagonal_graph["partition_signature"],
    }


def control_rows(specs: list[dict[str, Any]], graphs: dict[str, dict[str, Any]], all_rows: dict[str, Any]) -> dict[str, Any]:
    controls: dict[str, Any] = {}
    for spec in specs:
        set_id = spec["set_id"]
        controls[set_id] = {
            "similarity_cluster_contrast": similarity_cluster_contrast(graphs[set_id]),
            "root_off_contrast": root_off_contrast(spec, graphs[set_id]),
        }
        if set_id == "G5":
            controls[set_id]["commutative_collapse_contrast"] = g5_commutative_contrast(spec, all_rows, graphs[set_id])
    return controls


def partition_identity_inputs(rows: list[dict[str, Any]]) -> list[dict[str, int | str]]:
    return [
        {
            "set_id": row["set_id"],
            "state_count": int(row["state_count"]),
            "scc_count": int(row["scc_count"]),
            "terminal_class_count": int(row["terminal_class_count"]),
            "expected_terminal_class_count": EXPECTED_TERMINAL_COUNTS[row["set_id"]],
        }
        for row in rows
    ]


def z3_partition_identity(rows: list[dict[str, Any]], *, erased_flip: bool = False) -> str:
    solver = z3.Solver()
    terms = []
    for idx, row in enumerate(partition_identity_inputs(rows)):
        actual = z3.Int(f"z3_actual_terminals_{idx}")
        expected = z3.Int(f"z3_expected_terminals_{idx}")
        solver.add(actual == z3.IntVal(int(row["terminal_class_count"])))
        expected_value = int(row["expected_terminal_class_count"])
        if erased_flip and row["set_id"] == "G5":
            expected_value -= 1
        solver.add(expected == z3.IntVal(expected_value))
        terms.append(actual != expected)
    solver.add(z3.Or(terms))
    return str(solver.check())


def cvc5_partition_identity(rows: list[dict[str, Any]], *, erased_flip: bool = False) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    terms = []
    for idx, row in enumerate(partition_identity_inputs(rows)):
        actual = solver.mkConst(int_sort, f"cvc5_actual_terminals_{idx}")
        expected = solver.mkConst(int_sort, f"cvc5_expected_terminals_{idx}")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, actual, solver.mkInteger(int(row["terminal_class_count"]))))
        expected_value = int(row["expected_terminal_class_count"])
        if erased_flip and row["set_id"] == "G5":
            expected_value -= 1
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, expected, solver.mkInteger(expected_value)))
        terms.append(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, actual, expected)))
    solver.assertFormula(terms[0] if len(terms) == 1 else solver.mkTerm(Kind.OR, *terms))
    result = solver.checkSat()
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def proof_bundle(rows: list[dict[str, Any]]) -> dict[str, Any]:
    proof_row = {
        "encoding": "computed terminal-class counts per generating set are bound as QF_LIA constants; assert existence of a count mismatch",
        "erased_flip": "G5 expected terminal count decremented by one",
        "partition_identity_inputs": partition_identity_inputs(rows),
        "asserted_precomputed_boolean": False,
    }
    return {
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": z3_partition_identity(rows),
            "erased_flip_verdict": z3_partition_identity(rows, erased_flip=True),
            "proof_row": proof_row,
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": cvc5_partition_identity(rows),
            "erased_flip_verdict": cvc5_partition_identity(rows, erased_flip=True),
            "proof_row": proof_row,
        },
    }


def source_locks() -> dict[str, Any]:
    return {
        key: {"path": rel(path), "sha256": sha256_file(path), "git_last_commit": git_last_commit(path)}
        for key, path in PARENT_PATHS.items()
        if path.exists()
    }


def build_sweep(expm_fn: Callable[[list[list[float]], float], list[list[float]]]) -> dict[str, Any]:
    all_rows = load_all_generators(expm_fn)
    specs = generator_sets(all_rows)
    parent_env = load_json(PARENT_RESULT_PATH)
    graphs = {spec["set_id"]: build_graph_for(spec) for spec in specs}
    rows = [partition_row(spec, graphs[spec["set_id"]], parent_env) for spec in specs]
    controls = control_rows(specs, graphs, all_rows)
    first_split = next((row["set_id"] for row in rows if row["earns_sub_basin_term"]), None)
    signature_text = "|".join(
        f"{row['set_id']}:{row['state_count']}:{row['terminal_class_count']}:{','.join(str(x) for x in row['terminal_class_sizes'])}:{row['fate']}"
        for row in rows
    )
    return {
        "source_locks": source_locks(),
        "generator_source_rows": all_rows["source_rows"],
        "specs": [
            {
                "set_id": spec["set_id"],
                "label": spec["label"],
                "description": spec["description"],
                "conditioned_only": spec["conditioned_only"],
                "generator_names": [g["name"] for g in spec["generators"]],
            }
            for spec in specs
        ],
        "graphs": graphs,
        "partition_fate_table": rows,
        "controls": controls,
        "crossover_proofs": proof_bundle(rows),
        "sub_basin_answer": {
            "any_second_terminal_class": first_split is not None,
            "first_split_set": first_split,
            "honest_unitary_result_sets": [row["set_id"] for row in rows if not row["earns_sub_basin_term"]],
            "statement": "A second terminal closed communicating class appears in G1, G3L, G3R, and G5; these rows earn the first computed sub-basin structure at the stated scratch ceiling.",
        },
        "engine_dof_reading": {
            "generating_set_is_dof_choice": True,
            "statement": "The same 33-cell carrier yields different basin landscapes as active generator/DoF rows change.",
            "terminal_count_by_set": {row["set_id"]: row["terminal_class_count"] for row in rows},
        },
        "sweep_signature_text": signature_text,
        "sweep_signature_sha256": hashlib.sha256(signature_text.encode("utf-8")).hexdigest(),
    }


def one_to_one_tool_rows(engine: str, graph_tool: str, proof_tools: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    ids = [f"{engine}_{graph_tool}_generating_set_sweep"] + [f"{engine}_{tool}_partition_identity" for tool in proof_tools]
    capability = [
        {
            "receipt_id": ids[0],
            "tool": graph_tool,
            "computed_what": "G0-G5 finite graph partitions, terminal classes, may/must basin sizes, and Morse rows",
            "status": "used",
        }
    ]
    for tool, rid in zip(proof_tools, ids[1:], strict=True):
        capability.append(
            {
                "receipt_id": rid,
                "tool": tool,
                "computed_what": "computed partition identity check with erased terminal-count flip",
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
                "torch_geometric": "torch_geometric.data.Data plus torch.func.vmap",
            }.get(graph_tool, graph_tool),
            "input_object": "finite cells and generator-labelled G0-G5 transition rows",
            "output_object": "partition fate table with terminal classes, may/must basin sizes, metastable rows, and Morse ordering",
            "positive_case": "G0 re-derives the committed one-terminal-class anchor",
            "negative/erased_control": "rotations-only, chirality-only, conditioned, and composite rows recompute different basin landscapes",
            "boundary_case": "G4 uses only the conditioned-shell state set",
            "demotion_condition": "demote if rows are copied rather than recomputed from explicit edges",
            "gates": ["partition_fate_table", "sub_basin_answer", "all_pass"],
        }
    ]
    for tool, rid in zip(proof_tools, ids[1:], strict=True):
        calls.append(
            {
                "receipt_id": rid,
                "tool": tool,
                "qualified_api/function": {
                    "z3": "z3.Solver/z3.Int/check",
                    "cvc5": "cvc5.Solver/mkConst/assertFormula/checkSat",
                    "Z3": "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                }.get(tool, tool),
                "input_object": "computed terminal-class counts for G0-G5",
                "output_object": "UNSAT partition identity proof and SAT erased flip",
                "positive_case": "all computed terminal counts equal expected sweep counts",
                "negative/erased_control": "G5 expected count is decremented",
                "boundary_case": "single-terminal and multi-terminal rows both encoded",
                "demotion_condition": "demote if solver does not bind computed count rows",
                "gates": ["proof", "identity", "all_pass"],
            }
        )
    return capability, calls, {"pass": [row["receipt_id"] for row in capability] == [row["receipt_id"] for row in calls]}


def summarize_sweep(sweep: dict[str, Any]) -> dict[str, Any]:
    return {row["set_id"]: row for row in sweep["partition_fate_table"]}


def all_expected_rows_pass(sweep: dict[str, Any]) -> bool:
    rows = summarize_sweep(sweep)
    return bool(
        rows["G0"]["baseline_anchor_byte_exact"] is True
        and rows["G0"]["terminal_class_count"] == 1
        and rows["G1"]["terminal_class_count"] == 3
        and rows["G2"]["terminal_class_count"] == 1
        and rows["G3L"]["terminal_class_count"] == 3
        and rows["G3R"]["terminal_class_count"] == 3
        and rows["G4"]["state_count"] == 4
        and rows["G4"]["terminal_class_count"] == 1
        and rows["G5"]["terminal_class_count"] == 5
        and sweep["crossover_proofs"]["z3"]["verdict"] == "unsat"
        and sweep["crossover_proofs"]["z3"]["erased_flip_verdict"] == "sat"
        and sweep["crossover_proofs"]["cvc5"]["verdict"] == "unsat"
        and sweep["crossover_proofs"]["cvc5"]["erased_flip_verdict"] == "sat"
    )
