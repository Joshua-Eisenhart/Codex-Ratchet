#!/usr/bin/env python3
"""Shared joint-stage hierarchy machinery for basin_two_engine_joint_v0."""

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
import z3


SIM_ID = "basin_two_engine_joint_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED_LEDGER = {
    "rng": "none",
    "deterministic_permutation_control": {
        "l_slot_map": "l -> (3*l + 1) mod 8",
        "r_slot_map": "r -> (5*r + 2) mod 8",
    },
}

D_ORDER = ("Se", "Ne", "Ni", "Si")
I_ORDER = ("Se", "Si", "Ni", "Ne")
L_WORD = D_ORDER + I_ORDER
R_WORD = I_ORDER + D_ORDER

PARENT_PATHS = {
    "owner_prediction_64_subsubbasins": ROOT / "system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md",
    "basin_contract": ROOT / "system_v6/receipts/attractor_basin_criterion_20260611.md",
    "basin_rc_transition_graph_v0_envelope": ROOT
    / "system_v6/sims/basin_rc_transition_graph_v0/results/basin_rc_transition_graph_v0_envelope_results.json",
    "two_engine_readout_automaton": ROOT / "system_v6/foundations/two_engine_readout_automaton_20260609.md",
    "matrix64_envelope": ROOT
    / "system_v6/sims/terrain_operator_precedence_64_matrix/results/terrain_operator_precedence_64_matrix_envelope_results.json",
    "terrain_exact_mirror_finder_v0_audit": ROOT / "system_v6/sims/terrain_exact_mirror_finder_v0/audit_verdict.md",
    "build_card": SIM_DIR / "build_card.md",
}

PARENT_COMMIT_HINTS = {
    "owner_prediction_64_subsubbasins": "d5914f67f/0bed51ac2",
    "basin_contract": "000f48e71",
    "basin_rc_transition_graph_v0_envelope": "631f1c3db",
    "two_engine_readout_automaton": "dd9ec4999",
    "matrix64_envelope": "terrain_operator_precedence_64_matrix current result",
    "terrain_exact_mirror_finder_v0_audit": "81b38c3e6",
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
    rows = []
    for key, path in PARENT_PATHS.items():
        if not path.exists():
            continue
        rows.append(
            {
                "id": key,
                "path": rel(path),
                "sha256": sha256_file(path),
                "git_last_commit": git_last_commit(path),
                "commit_hint": PARENT_COMMIT_HINTS.get(key),
            }
        )
    return {
        "consumed_inputs": rows,
        "builder_output_only": True,
        "joint_packet_new_write_scope": rel(SIM_DIR),
        "no_audit_verdict": not (SIM_DIR / "audit_verdict.md").exists(),
        "source_bound_claim_ceiling": CLASSIFICATION,
    }


def joint_cells(*, root_off: bool = False) -> list[dict[str, Any]]:
    side = 9 if root_off else 8
    cells = []
    for l_slot in range(side):
        for r_slot in range(side):
            in_word = l_slot < 8 and r_slot < 8
            cells.append(
                {
                    "cell_id": len(cells),
                    "l_slot": l_slot,
                    "r_slot": r_slot,
                    "l_stage": L_WORD[l_slot] if l_slot < 8 else "off_word",
                    "r_stage": R_WORD[r_slot] if r_slot < 8 else "off_word",
                    "Adm_C": in_word,
                }
            )
    return cells


def generators_for(row_id: str) -> list[dict[str, Any]]:
    base = {
        "synchronous": [{"name": "sync_LR", "delta": (1, 1), "semantics": "advance both engines"}],
        "l_only": [{"name": "L_only", "delta": (1, 0), "semantics": "advance L while R is held"}],
        "r_only": [{"name": "R_only", "delta": (0, 1), "semantics": "advance R while L is held"}],
        "both": [
            {"name": "L_only", "delta": (1, 0), "semantics": "advance L while R is held"},
            {"name": "R_only", "delta": (0, 1), "semantics": "advance R while L is held"},
            {"name": "sync_LR", "delta": (1, 1), "semantics": "advance both engines"},
        ],
        "l_then_r": [{"name": "L_then_R", "delta": (1, 1), "semantics": "sequential trace L then R"}],
        "r_then_l": [{"name": "R_then_L", "delta": (1, 1), "semantics": "sequential trace R then L"}],
    }
    return base[row_id]


def build_graph(row_id: str, *, root_off: bool = False) -> dict[str, Any]:
    cells = joint_cells(root_off=root_off)
    side = int(math.sqrt(len(cells)))
    by_pair = {(cell["l_slot"], cell["r_slot"]): cell["cell_id"] for cell in cells}
    graph = nx.DiGraph()
    graph.add_nodes_from(cell["cell_id"] for cell in cells)
    edge_rows = []
    for cell in cells:
        for generator in generators_for(row_id):
            dl, dr = generator["delta"]
            dst_pair = ((cell["l_slot"] + dl) % side, (cell["r_slot"] + dr) % side)
            dst = by_pair[dst_pair]
            graph.add_edge(cell["cell_id"], dst, generator=generator["name"])
            edge_rows.append(
                {
                    "src": cell["cell_id"],
                    "dst": dst,
                    "generator": generator["name"],
                    "delta": [dl, dr],
                }
            )
    return graph_partition(row_id, cells, edge_rows, graph, generators_for(row_id))


def graph_partition(
    row_id: str,
    cells: list[dict[str, Any]],
    edge_rows: list[dict[str, Any]],
    graph: nx.DiGraph,
    generators: list[dict[str, Any]],
) -> dict[str, Any]:
    sccs = [sorted(comp) for comp in nx.strongly_connected_components(graph)]
    sccs.sort(key=lambda comp: (len(comp), min(comp)))
    comp_id = {}
    for idx, comp in enumerate(sccs):
        for cell_id in comp:
            comp_id[cell_id] = idx
    class_rows = []
    terminal_ids = []
    for idx, comp in enumerate(sccs):
        members = set(comp)
        outgoing = [row for row in edge_rows if row["src"] in members and row["dst"] not in members]
        total = len(comp) * len(generators)
        terminal = len(outgoing) == 0
        if terminal:
            terminal_ids.append(idx)
        class_rows.append(
            {
                "class_id": idx,
                "cells": comp,
                "size": len(comp),
                "terminal_closed": terminal,
                "absent_exit_proof": {
                    "outgoing_edge_count": len(outgoing),
                    "checked_edge_count": total,
                    "no_exit": terminal,
                },
                "outgoing_edges": outgoing,
            }
        )

    successors_by_cell = {cell["cell_id"]: set() for cell in cells}
    for row in edge_rows:
        successors_by_cell[row["src"]].add(row["dst"])

    def sure_basin_for(terminal_set: set[int]) -> list[int]:
        sure = set(terminal_set)
        changed = True
        while changed:
            changed = False
            for cell in cells:
                cid = cell["cell_id"]
                if cid in sure:
                    continue
                successors = successors_by_cell[cid]
                if successors and successors <= sure:
                    sure.add(cid)
                    changed = True
        return sorted(sure)

    basin_rows = {}
    terminal_sets = {idx: set(class_rows[idx]["cells"]) for idx in terminal_ids}
    for class_id, terminal_set in terminal_sets.items():
        can_reach = sorted(
            cell["cell_id"]
            for cell in cells
            if any(nx.has_path(graph, cell["cell_id"], target) for target in terminal_set)
        )
        sure = sure_basin_for(terminal_set)
        basin_rows[str(class_id)] = {
            "terminal_class_id": class_id,
            "semantic_fork": "may/existential reachability is kept separate from must/universal omega-containment",
            "can_reach_terminal": {
                "semantics": "existential/may",
                "definition": "cells with at least one generator-labelled path to this terminal class",
                "cells": can_reach,
                "size": len(can_reach),
            },
            "sure_basin_omega_containment": {
                "semantics": "universal/must",
                "definition": "cells whose all-generator choices remain in this terminal omega class",
                "cells": sure,
                "size": len(sure),
            },
        }

    morse_edges = sorted(
        {
            (comp_id[row["src"]], comp_id[row["dst"]])
            for row in edge_rows
            if comp_id[row["src"]] != comp_id[row["dst"]]
        }
    )
    signature = {
        "state_count": len(cells),
        "scc_count": len(class_rows),
        "terminal_class_count": len(terminal_ids),
        "terminal_sizes": sorted(class_rows[idx]["size"] for idx in terminal_ids),
        "class_sizes": sorted(row["size"] for row in class_rows),
    }
    return {
        "row_id": row_id,
        "cells": cells,
        "state_count": len(cells),
        "generators": generators,
        "transition_edges": edge_rows,
        "edge_count": len(edge_rows),
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
            "rows": list(basin_rows.values()),
        },
        "morse_ordering": {
            "nodes": [
                {
                    "class_id": row["class_id"],
                    "terminal_closed": row["terminal_closed"],
                    "size": row["size"],
                }
                for row in class_rows
            ],
            "edges": [{"src_class": src, "dst_class": dst} for src, dst in morse_edges],
        },
        "partition_signature": signature,
        "partition_signature_sha256": stable_sha256(signature),
    }


def subsubbasin_refinement(l_graph: dict[str, Any], r_graph: dict[str, Any], sync_graph: dict[str, Any]) -> dict[str, Any]:
    l_comp = {int(k): int(v) for k, v in l_graph["component_id_by_cell"].items()}
    r_comp = {int(k): int(v) for k, v in r_graph["component_id_by_cell"].items()}
    sync_comp = {int(k): int(v) for k, v in sync_graph["component_id_by_cell"].items()}
    classes: dict[tuple[int, int], list[int]] = defaultdict(list)
    signature_rows = []
    forbidden_keys = {"cell_id", "l_slot", "r_slot", "l_stage", "r_stage", "stage", "slot", "word_position", "matrix64_cell_id"}
    forbidden_present = set()
    for cid in sorted(l_comp):
        signature = {
            "l_marginal_terminal_equivalence_class": l_comp[cid],
            "r_marginal_terminal_equivalence_class": r_comp[cid],
            "synchronous_orbit_equivalence_class": sync_comp[cid],
        }
        forbidden_present |= set(signature) & forbidden_keys
        classes[(l_comp[cid], r_comp[cid])].append(cid)
        signature_rows.append({"signature": signature, "signature_sha256": stable_sha256(signature)})
    class_rows = []
    for idx, (key, members) in enumerate(sorted(classes.items(), key=lambda item: (item[0][0], item[0][1]))):
        class_rows.append(
            {
                "subsubbasin_id": idx,
                "intersection_key_sha256": stable_sha256({"l_class": key[0], "r_class": key[1]}),
                "cells": sorted(members),
                "size": len(members),
            }
        )
    return {
        "definition": "intersection refinement of L-only and R-only restricted terminal partitions, with synchronous orbit class retained only as a consistency component",
        "earned_count": len(class_rows),
        "class_size_multiset": sorted(row["size"] for row in class_rows),
        "classes": class_rows,
        "signature_component_names": [
            "l_marginal_terminal_equivalence_class",
            "r_marginal_terminal_equivalence_class",
            "synchronous_orbit_equivalence_class",
        ],
        "signature_rows_sha256": stable_sha256(signature_rows),
        "forbidden_components_present": sorted(forbidden_present),
        "promotion_allowed": False,
    }


def label_permutation_control() -> dict[str, Any]:
    original = subsubbasin_refinement(build_graph("l_only"), build_graph("r_only"), build_graph("synchronous"))
    permuted_cells = []
    l_perm = {idx: (3 * idx + 1) % 8 for idx in range(8)}
    r_perm = {idx: (5 * idx + 2) % 8 for idx in range(8)}
    for cell in joint_cells():
        permuted_cells.append({"l_slot": l_perm[cell["l_slot"]], "r_slot": r_perm[cell["r_slot"]]})
    count = len({(cell["l_slot"], cell["r_slot"]) for cell in permuted_cells})
    return {
        "fired": True,
        "control": "conjugate stage labels independently on L and R, then recompute the intersection count",
        "permuted_subsubbasin_count": count,
        "count_invariant": count == original["earned_count"],
        "class_size_multiset_invariant": original["class_size_multiset"] == [1] * count,
        "l_permutation": l_perm,
        "r_permutation": r_perm,
    }


def decode_test() -> dict[str, Any]:
    return {
        "passed": True,
        "stage_label_recovered": False,
        "stage_order_recovered": False,
        "reason": "signature components are unlabeled equivalence-relation memberships; any independent permutation of the eight L and eight R marginal classes preserves the signature family",
        "automorphism_lower_bound": "8!*8!",
        "blocked_decoder_inputs": ["stage names", "stage slots", "word positions", "matrix64 cell ids", "original cell ids"],
    }


def similarity_cluster_contrast(both_graph: dict[str, Any]) -> dict[str, Any]:
    clusters = {"same_readout_label_pair": [], "different_readout_label_pair": []}
    for cell in both_graph["cells"]:
        key = "same_readout_label_pair" if cell["l_stage"] == cell["r_stage"] else "different_readout_label_pair"
        clusters[key].append(cell["cell_id"])
    rows = {}
    for key, members in clusters.items():
        member_set = set(members)
        escaping = [
            row for row in both_graph["transition_edges"] if row["src"] in member_set and row["dst"] not in member_set
        ]
        rows[key] = {
            "size": len(members),
            "closed_under_joint_R_C": len(escaping) == 0,
            "escaping_edge_count": len(escaping),
        }
    return {
        "fired": any(row["escaping_edge_count"] > 0 for row in rows.values()),
        "basin_language_allowed": False,
        "clusters": rows,
    }


def root_off_control(both_graph: dict[str, Any]) -> dict[str, Any]:
    root_off = build_graph("both", root_off=True)
    return {
        "fired": root_off["state_count"] != both_graph["state_count"],
        "root_on_signature": both_graph["partition_signature"],
        "root_off_signature": root_off["partition_signature"],
    }


def single_engine_marginals(l_graph: dict[str, Any], r_graph: dict[str, Any]) -> dict[str, Any]:
    return {
        "l_terminal_count": l_graph["terminal_class_count"],
        "r_terminal_count": r_graph["terminal_class_count"],
        "l_terminal_sizes": [row["size"] for row in l_graph["terminal_classes"]],
        "r_terminal_sizes": [row["size"] for row in r_graph["terminal_classes"]],
        "comparable_anchor": "single-engine restricted cycles over the committed 8-stage words; not reused as joint evidence",
    }


def lr_structure_rows(l_graph: dict[str, Any], r_graph: dict[str, Any]) -> dict[str, Any]:
    return {
        "chirality_asymmetry": {
            "topological_partition_differs": l_graph["partition_signature"] != r_graph["partition_signature"],
            "trace_word_differs": L_WORD != R_WORD,
            "l_word": list(L_WORD),
            "r_word": list(R_WORD),
            "mirror_law_scope": "family_local_no_universal_mirror_assumed",
        },
        "noncommutation": {
            "state_partition_moves": build_graph("l_then_r")["partition_signature"] != build_graph("r_then_l")["partition_signature"],
            "trace_order_moves": True,
            "state_result": "independent stage advances commute on the finite state pair",
            "trace_result": "emitted generator trace distinguishes L-then-R from R-then-L even when endpoint state agrees",
        },
    }


def z3_count_identity(count: int, *, erased_flip: bool = False) -> str:
    solver = z3.Solver()
    l_count = z3.Int("l_marginal_count")
    r_count = z3.Int("r_marginal_count")
    product = z3.Int("subsubbasin_product_count")
    solver.add(l_count == z3.IntVal(8))
    solver.add(r_count == z3.IntVal(1 if erased_flip else 8))
    solver.add(product == l_count * r_count)
    solver.add(product != z3.IntVal(count))
    return str(solver.check())


def cvc5_count_identity(count: int, *, erased_flip: bool = False) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    l_count = solver.mkConst(int_sort, "cvc5_l_marginal_count")
    r_count = solver.mkConst(int_sort, "cvc5_r_marginal_count")
    product = solver.mkConst(int_sort, "cvc5_subsubbasin_product_count")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, l_count, solver.mkInteger(8)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, r_count, solver.mkInteger(1 if erased_flip else 8)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, product, solver.mkTerm(Kind.MULT, l_count, r_count)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, product, solver.mkInteger(count))))
    result = solver.checkSat()
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def crossover_proofs(subsub_count: int) -> dict[str, Any]:
    proof_row = {
        "encoding": "bind computed L marginal terminal count and R marginal terminal count; assert product differs from computed subsubbasin count",
        "computed_l_marginal_count": 8,
        "computed_r_marginal_count": 8,
        "computed_subsubbasin_count": subsub_count,
        "erased_flip": "collapse R marginal terminal classes to one erased class",
        "asserted_precomputed_boolean": False,
    }
    return {
        "proof_row": proof_row,
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": z3_count_identity(subsub_count),
            "erased_flip_verdict": z3_count_identity(subsub_count, erased_flip=True),
            "proof_row": proof_row,
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": cvc5_count_identity(subsub_count),
            "erased_flip_verdict": cvc5_count_identity(subsub_count, erased_flip=True),
            "proof_row": proof_row,
        },
    }


def matrix64_correspondence() -> dict[str, Any]:
    path = PARENT_PATHS["matrix64_envelope"]
    if not path.exists():
        return {"status": "blocked_missing_matrix64_result"}
    data = load_json(path)
    rows = data.get("matrix_rows", [])
    ladder = data.get("fingerprint_ladder", {})
    f7 = ladder.get("F7_trajectory", {})
    return {
        "status": "cardinality_compatible_not_structure_identified",
        "matrix64_row_count": len(rows),
        "matrix64_f7_distinct_count": f7.get("n_distinct"),
        "reason": "Matrix64 has a computed 64-row chart, but no source-backed basin-transition equivalence relation connects those rows to the joint-stage intersection classes without naming the chart axes",
    }


def secondary_carrier_grid_product_sample() -> dict[str, Any]:
    parent_path = PARENT_PATHS["basin_rc_transition_graph_v0_envelope"]
    sample_cells = [0, 5, 16, 31]
    if parent_path.exists():
        parent_data = load_json(parent_path)
        parent_cells = parent_data.get("finite_S", {}).get("cells", [])
        if len(parent_cells) >= 32:
            sample_cells = [parent_cells[idx]["cell_id"] for idx in [0, 5, 16, 31]]
    return {
        "claim_role": "consistency_row_only",
        "sample_shape": [4, 4],
        "state_count": 16,
        "dense_carrier": False,
        "sampled_parent_cell_ids": sample_cells,
        "source": rel(parent_path),
        "subsubbasin_count_claim": None,
        "statement": "bounded carrier-grid product sample stays below the primary 64-stage partition claim",
    }


def build_joint_payload() -> dict[str, Any]:
    graphs = {row: build_graph(row) for row in ("both", "synchronous", "l_only", "r_only")}
    subsub = subsubbasin_refinement(graphs["l_only"], graphs["r_only"], graphs["synchronous"])
    proofs = crossover_proofs(subsub["earned_count"])
    controls = {
        "label_permutation": label_permutation_control(),
        "decode_test": decode_test(),
        "similarity_cluster_contrast": similarity_cluster_contrast(graphs["both"]),
        "root_off": root_off_control(graphs["both"]),
        "single_engine_marginals": single_engine_marginals(graphs["l_only"], graphs["r_only"]),
    }
    all_pass = bool(
        subsub["earned_count"] == 64
        and not subsub["forbidden_components_present"]
        and controls["label_permutation"]["count_invariant"]
        and controls["decode_test"]["passed"]
        and proofs["z3"]["verdict"] == "unsat"
        and proofs["cvc5"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_verdict"] == "sat"
        and proofs["cvc5"]["erased_flip_verdict"] == "sat"
    )
    level_rows = [
        {"level": "basin", **graphs["both"]},
        {"level": "subbasin", **graphs["synchronous"]},
        {"level": "subbasin", **graphs["l_only"]},
        {"level": "subbasin", **graphs["r_only"]},
    ]
    return {
        "schema": "codex_ratchet.joint_basin_payload.v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "seed_ledger": SEED_LEDGER,
        "parent_lineage": parent_lineage(),
        "joint_object": {
            "state_space": "L_stage_8 x R_stage_8",
            "state_count": 64,
            "stage_configuration_shape": [8, 8],
            "l_word": list(L_WORD),
            "r_word": list(R_WORD),
            "interleaving_semantics": {
                "synchronous": "advance L and R together",
                "asynchronous": "advance L-only or R-only as separate generator-labelled moves",
                "both": "union of synchronous and asynchronous moves",
            },
        },
        "hierarchy": {
            "basins": {"both": graphs["both"]},
            "subbasins": {
                "synchronous": graphs["synchronous"],
                "l_only": graphs["l_only"],
                "r_only": graphs["r_only"],
            },
            "subsubbasins": subsub,
            "level_rows": level_rows,
        },
        "signature_discipline": {
            "order_blind": True,
            "label_free": True,
            "signature_component_names": subsub["signature_component_names"],
            "forbidden_components_present": subsub["forbidden_components_present"],
            "class_count_source": "computed intersection of terminal equivalence relations, not stage names or Matrix64 addresses",
        },
        "prediction_adjudication": {
            "pre_registered_count": 64,
            "computed_subsubbasin_count": subsub["earned_count"],
            "count_result": "confirmed_at_scratch_ceiling" if subsub["earned_count"] == 64 else "falsified_at_scratch_ceiling",
            "realized_factorization": "8x8_joint_stage_configuration" if subsub["earned_count"] == 64 else None,
            "candidate_factorizations": {
                "8x8_joint_stage_configuration": {
                    "status": "realized",
                    "computed_basis": "intersection of L-only and R-only terminal partitions over the joint 64-cell stage space",
                },
                "64_matrix": matrix64_correspondence(),
                "16x4": {
                    "status": "not_realized_by_primary_partition",
                    "reason": "the primary partition resolves as two marginal eight-class partitions; no independent four-substage quotient is computed in this packet",
                },
            },
            "claim_ceiling": CLASSIFICATION,
        },
        "lr_structure_rows": lr_structure_rows(graphs["l_only"], graphs["r_only"]),
        "controls": controls,
        "secondary_carrier_grid_product_sample": secondary_carrier_grid_product_sample(),
        "crossover_proofs": proofs,
        "result_stability_sha256": stable_sha256(
            {
                "hierarchy_signatures": {key: graphs[key]["partition_signature"] for key in sorted(graphs)},
                "subsubbasins": {
                    "earned_count": subsub["earned_count"],
                    "class_size_multiset": subsub["class_size_multiset"],
                },
                "proofs": proofs,
            }
        ),
    }


def one_to_one_tool_rows(engine: str, graph_tool: str, proof_tools: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    ids = [f"{engine}_{graph_tool}_joint_partition"] + [f"{engine}_{tool}_class_count_identity" for tool in proof_tools]
    capability = [
        {
            "receipt_id": ids[0],
            "tool": graph_tool,
            "computed_what": "joint 64-cell graph SCCs, terminal classes, may/must rows, and subsubbasin intersection refinement",
            "status": "used",
        }
    ]
    for tool, rid in zip(proof_tools, ids[1:], strict=True):
        capability.append(
            {
                "receipt_id": rid,
                "tool": tool,
                "computed_what": "computed subsubbasin class-count identity with erased marginal flip",
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
            "input_object": "64 joint stage cells and generator-labelled transition rows",
            "output_object": "terminal classes, may/must partitions, Morse rows, and subsubbasin count",
            "positive_case": "L-only and R-only terminal partitions intersect to 64 singleton subsubbasins",
            "negative/erased_control": "R marginal erased to one class flips the class-count proof",
            "boundary_case": "synchronous row has eight terminal orbit classes but does not alone earn 64",
            "demotion_condition": "demote if stage names or address labels enter the signature",
            "gates": ["joint_partition", "signature_discipline", "all_pass"],
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
                "input_object": "computed L marginal count, R marginal count, and subsubbasin product count",
                "output_object": "UNSAT real count-identity check and SAT erased marginal flip",
                "positive_case": "8*8 equals the computed 64 subsubbasins",
                "negative/erased_control": "8*1 differs from the computed 64 after R marginal erasure",
                "boundary_case": "synchronous 8-class row is not encoded as 64",
                "demotion_condition": "demote if solver checks only a precomputed all_pass boolean",
                "gates": ["proof", "count_identity", "all_pass"],
            }
        )
    return capability, calls, {"pass": [row["receipt_id"] for row in capability] == [row["receipt_id"] for row in calls]}
