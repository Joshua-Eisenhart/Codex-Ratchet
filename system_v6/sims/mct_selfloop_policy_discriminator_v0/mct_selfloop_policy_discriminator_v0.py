#!/usr/bin/env python3
"""Compute both folded self-loop policy branches on the committed G0 graph."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any


SIM_ID = "mct_selfloop_policy_discriminator_v0"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "policy_discriminator_table_only"
EXPECTED_G0_SHA256 = "bd0cd3b551bbb3f323eb596695da8d91429f010780c1c137af4a253bd73438f0"

ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"

SOURCE_PATHS = {
    "s11_owner_decision_row": ROOT / "system_v6/receipts/evening_mining_estate_s11_20260611.json",
    "mct_reconciled_spec": ROOT / "system_v6/receipts/mct_reconciled_spec_20260609.md",
    "g0_committed_envelope": ROOT
    / "system_v6/sims/basin_rc_transition_graph_v0/results/basin_rc_transition_graph_v0_envelope_results.json",
    "mct_dynamic_envelope": ROOT
    / "system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json",
    "mct_dynamic_build_card": ROOT / "system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md",
    "mct_nonassoc_weld_build_card": ROOT / "system_v6/sims/mct_nonassoc_weld_packet_v0/build_card.md",
    "mct_nonassoc_weld_audit": ROOT / "system_v6/sims/mct_nonassoc_weld_packet_v0/audit_verdict.md",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_lock(path: Path, role: str) -> dict[str, Any]:
    return {"role": role, "path": rel(path), "sha256": sha256_file(path)}


def descendants(nodes: list[int], edges: set[tuple[int, int]], start: int) -> set[int]:
    succ: dict[int, set[int]] = {node: set() for node in nodes}
    for src, dst in edges:
        succ.setdefault(src, set()).add(dst)
    seen = {start}
    queue: deque[int] = deque([start])
    while queue:
        cur = queue.popleft()
        for nxt in succ.get(cur, set()):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def sccs(nodes: list[int], edges: set[tuple[int, int]]) -> list[list[int]]:
    succ: dict[int, set[int]] = {node: set() for node in nodes}
    pred: dict[int, set[int]] = {node: set() for node in nodes}
    for src, dst in edges:
        succ.setdefault(src, set()).add(dst)
        pred.setdefault(dst, set()).add(src)
    unassigned = set(nodes)
    comps: list[list[int]] = []
    while unassigned:
        seed = min(unassigned)
        forward = descendants(nodes, edges, seed)
        backward = descendants(nodes, {(b, a) for a, b in edges}, seed)
        comp = sorted(forward & backward)
        comps.append(comp)
        unassigned -= set(comp)
    comps.sort(key=lambda row: (min(row), len(row)))
    return comps


def entropy_nats(counts: dict[str, int]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    value = 0.0
    for count in counts.values():
        if count:
            p = count / total
            value -= p * math.log(p)
    return value


def classify_source_edge(edge: dict[str, Any], comp_by_cell: dict[int, int]) -> str:
    return "folded_self_loop_internal" if comp_by_cell[int(edge["src"])] == comp_by_cell[int(edge["dst"])] else "cross_class_exit"


def folded_branch(
    *,
    policy: str,
    nodes: list[int],
    transported_edges: list[dict[str, Any]],
    comp_by_cell: dict[int, int],
    terminal_original_class_ids: list[int],
) -> dict[str, Any]:
    kept_rows = []
    erased_rows = []
    edge_counter: Counter[tuple[int, int]] = Counter()
    type_counter: Counter[str] = Counter()
    for edge in transported_edges:
        src_class = comp_by_cell[int(edge["src"])]
        dst_class = comp_by_cell[int(edge["dst"])]
        edge_type = "folded_self_loop_internal" if src_class == dst_class else "cross_class_exit"
        type_counter[edge_type] += 1
        folded = {
            "src_class": src_class,
            "dst_class": dst_class,
            "source_src": int(edge["src"]),
            "source_dst": int(edge["dst"]),
            "generator": edge["generator"],
            "edge_type": edge_type,
        }
        if policy == "erase" and src_class == dst_class:
            erased_rows.append(folded)
            continue
        kept_rows.append(folded)
        edge_counter[(src_class, dst_class)] += 1

    relation_edges = set(edge_counter)
    comps = sccs(nodes, relation_edges)
    folded_comp_by_node = {node: idx for idx, comp in enumerate(comps) for node in comp}
    terminal_classes = []
    class_rows = []
    for idx, comp in enumerate(comps):
        comp_set = set(comp)
        outgoing = [(src, dst) for src, dst in relation_edges if src in comp_set and dst not in comp_set]
        terminal = len(outgoing) == 0
        if terminal:
            terminal_classes.append(idx)
        class_rows.append(
            {
                "class_id": idx,
                "folded_nodes": comp,
                "terminal_closed": terminal,
                "absent_exit_proof": {
                    "no_exit": terminal,
                    "outgoing_edge_count": len(outgoing),
                    "outgoing_edges": [{"src_class": s, "dst_class": d} for s, d in sorted(outgoing)],
                },
                "has_explicit_self_loop": any((node, node) in relation_edges for node in comp),
            }
        )

    terminal_nodes = sorted(
        node
        for idx, comp in enumerate(comps)
        if idx in terminal_classes
        for node in comp
    )
    terminal_node_set = set(terminal_nodes)

    may_cells = sorted(node for node in nodes if descendants(nodes, relation_edges, node) & terminal_node_set)

    succ: dict[int, set[int]] = {node: set() for node in nodes}
    for src, dst in relation_edges:
        succ.setdefault(src, set()).add(dst)

    must = set(terminal_node_set)
    changed = True
    while changed:
        changed = False
        for node in nodes:
            if node in must:
                continue
            outs = succ.get(node, set())
            if outs and outs <= must:
                must.add(node)
                changed = True
    must_cells = sorted(must)

    edge_type_counts_after_policy = Counter(row["edge_type"] for row in kept_rows)
    ledger_counts = dict(sorted(type_counter.items()))
    after_counts = dict(sorted(edge_type_counts_after_policy.items()))
    return {
        "policy": policy,
        "folded_node_count": len(nodes),
        "transported_source_edge_count": len(transported_edges),
        "retained_transport_edge_count": len(kept_rows),
        "erased_transport_edge_count": len(erased_rows),
        "relation_edge_count_unique": len(relation_edges),
        "relation_edges_unique": [
            {
                "src_class": src,
                "dst_class": dst,
                "transport_multiplicity": edge_counter[(src, dst)],
                "edge_type": "folded_self_loop_internal" if src == dst else "cross_class_exit",
            }
            for src, dst in sorted(relation_edges)
        ],
        "relation_edge_multiplicity_total": sum(edge_counter.values()),
        "self_loop_relation_edge_count_unique": sum(1 for src, dst in relation_edges if src == dst),
        "self_loop_transport_edge_count": sum(1 for row in kept_rows if row["src_class"] == row["dst_class"]),
        "terminal_structure": {
            "folded_scc_count": len(comps),
            "terminal_class_ids": terminal_classes,
            "terminal_nodes": terminal_nodes,
            "classes": class_rows,
            "original_terminal_class_ids_from_g0": terminal_original_class_ids,
        },
        "may_must_semantics": {
            "can_reach_terminal_may": {
                "semantics": "existential/may",
                "folded_nodes": may_cells,
                "size": len(may_cells),
            },
            "sure_basin_omega_containment_must": {
                "semantics": "universal/must",
                "folded_nodes": must_cells,
                "size": len(must_cells),
                "nonterminal_forced_exit_nodes": sorted(set(must_cells) - terminal_node_set),
            },
        },
        "typed_entropy_ledger": {
            "entropy_object": "H_edge_type_nats over transported source edges classified after quotient pushforward",
            "source_transport_type_counts_before_policy": ledger_counts,
            "retained_type_counts_after_policy": after_counts,
            "H_edge_type_before_policy_nats": round(entropy_nats(ledger_counts), 12),
            "H_edge_type_after_policy_nats": round(entropy_nats(after_counts), 12),
            "record_loss_count_if_erased": len(erased_rows),
        },
        "branch_hash": stable_sha256(
            {
                "policy": policy,
                "relation_edges": sorted(relation_edges),
                "edge_counter": {f"{k[0]}->{k[1]}": v for k, v in sorted(edge_counter.items())},
                "may": may_cells,
                "must": must_cells,
            }
        ),
    }


def downstream_consumer_table(branches: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    erase = branches["erase"]
    retain = branches["retain"]
    return [
        {
            "packet": "mct_dynamic_admissibility_packet_v0",
            "committed_rows_or_fields": [
                "PIN_SPEC.choice_points.self_loop_policy_default",
                "PIN_SPEC_EXTENDED.choice_points.self_loop_policy_default",
                "divergence.comparison.rows sidecar_E3_erase/sidecar_E3_retain",
                "engine per-lane self_loop_policy_provenance rows",
            ],
            "under_erase": "policy value would read erase/owner-selected erase; folded relation edge count uses the erase branch; retained self-loop transport rows require explicit loss ledger",
            "under_retain": "policy value would read retain/owner-selected retain; folded relation edge count uses the retain branch; self-loop transport rows remain relation rows",
            "computed_change": {
                "erase_relation_edge_count_unique": erase["relation_edge_count_unique"],
                "retain_relation_edge_count_unique": retain["relation_edge_count_unique"],
                "erase_must_size": erase["may_must_semantics"]["sure_basin_omega_containment_must"]["size"],
                "retain_must_size": retain["may_must_semantics"]["sure_basin_omega_containment_must"]["size"],
            },
        },
        {
            "packet": "mct_nonassoc_weld_packet_v0",
            "committed_rows_or_fields": [
                "operations.retained_five.folding",
                "audit caveat requesting explicit M(C,t) state fields",
            ],
            "under_erase": "any inherited folded-relation row must show erased self-loop records and a killed-information/record-loss ledger",
            "under_retain": "any inherited folded-relation row may keep quotient self-loop rows as relation records",
            "computed_change": {
                "transport_rows_requiring_ledger_if_erase": erase["erased_transport_edge_count"],
                "transport_rows_retained_as_self_loops_if_retain": retain["self_loop_transport_edge_count"],
            },
        },
        {
            "packet": "basin_rc_transition_graph_v0 consumers of folded G0 quotient",
            "committed_rows_or_fields": [
                "transition_graph.partition_signature",
                "basin_partition.basin_map may/must rows when cited after quotient folding",
                "terminal absent-exit proof rows under folded relation",
            ],
            "under_erase": "terminal closed classes stay the same, but folded nonterminal class has no self-loop and becomes forced-exit under must semantics",
            "under_retain": "terminal closed classes stay the same, but folded nonterminal class has a self-loop and is not forced-exit under must semantics",
            "computed_change": {
                "terminal_nodes_same": erase["terminal_structure"]["terminal_nodes"]
                == retain["terminal_structure"]["terminal_nodes"],
                "erase_nonterminal_forced_exit_nodes": erase["may_must_semantics"]["sure_basin_omega_containment_must"][
                    "nonterminal_forced_exit_nodes"
                ],
                "retain_nonterminal_forced_exit_nodes": retain["may_must_semantics"]["sure_basin_omega_containment_must"][
                    "nonterminal_forced_exit_nodes"
                ],
            },
        },
        {
            "packet": "evening_mining_estate_s11_20260611 owner-decision row",
            "committed_rows_or_fields": [
                "OWNER DECISION 2 - self-loop retention policy for folded relations",
                "proposed_packet",
            ],
            "under_erase": "row can be closed only by owner choice; discriminator supplies erase consequences but not preference",
            "under_retain": "row can be closed only by owner choice; discriminator supplies retain consequences but not preference",
            "computed_change": {
                "branches_differ": True,
                "recommendation_emitted": False,
            },
        },
    ]


def build_markdown(payload: dict[str, Any]) -> str:
    rows = payload["computed_consequences_table"]
    lines = [
        "# mct_selfloop_policy_discriminator_v0 table",
        "",
        "Decision status: owner-gated. This table makes no recommendation.",
        "",
        "| consequence | erase | retain | differs |",
        "|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['consequence']} | {row['erase']} | {row['retain']} | {str(row['differs']).lower()} |"
        )
    lines.extend(
        [
            "",
            "## Downstream Consumer Impact",
            "",
            "| packet | erase consequence | retain consequence |",
            "|---|---|---|",
        ]
    )
    for row in payload["downstream_consumer_impact"]:
        lines.append(f"| `{row['packet']}` | {row['under_erase']} | {row['under_retain']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    g0_path = SOURCE_PATHS["g0_committed_envelope"]
    g0 = load_json(g0_path)
    assert isinstance(g0, dict)
    graph = g0["transition_graph"]
    observed_sha = graph["transition_graph_sha256"]
    if observed_sha != EXPECTED_G0_SHA256:
        raise SystemExit(f"G0 hash mismatch: {observed_sha} != {EXPECTED_G0_SHA256}")

    comp_by_cell = {int(k): int(v) for k, v in graph["component_id_by_cell"].items()}
    folded_nodes = sorted(set(comp_by_cell.values()))
    transported_edges = graph["transition_edges"]
    terminal_original_class_ids = [int(x) for x in graph["terminal_class_ids"]]

    branches = {
        policy: folded_branch(
            policy=policy,
            nodes=folded_nodes,
            transported_edges=transported_edges,
            comp_by_cell=comp_by_cell,
            terminal_original_class_ids=terminal_original_class_ids,
        )
        for policy in ["erase", "retain"]
    }

    consequences = [
        {
            "consequence": "unique folded relation edge count",
            "erase": branches["erase"]["relation_edge_count_unique"],
            "retain": branches["retain"]["relation_edge_count_unique"],
        },
        {
            "consequence": "transported source edge rows retained",
            "erase": branches["erase"]["retained_transport_edge_count"],
            "retain": branches["retain"]["retained_transport_edge_count"],
        },
        {
            "consequence": "transported source edge rows erased/lost from relation",
            "erase": branches["erase"]["erased_transport_edge_count"],
            "retain": branches["retain"]["erased_transport_edge_count"],
        },
        {
            "consequence": "unique self-loop relation edge count",
            "erase": branches["erase"]["self_loop_relation_edge_count_unique"],
            "retain": branches["retain"]["self_loop_relation_edge_count_unique"],
        },
        {
            "consequence": "terminal folded node count",
            "erase": len(branches["erase"]["terminal_structure"]["terminal_nodes"]),
            "retain": len(branches["retain"]["terminal_structure"]["terminal_nodes"]),
        },
        {
            "consequence": "may/existential basin folded node count",
            "erase": branches["erase"]["may_must_semantics"]["can_reach_terminal_may"]["size"],
            "retain": branches["retain"]["may_must_semantics"]["can_reach_terminal_may"]["size"],
        },
        {
            "consequence": "must/universal omega basin folded node count",
            "erase": branches["erase"]["may_must_semantics"]["sure_basin_omega_containment_must"]["size"],
            "retain": branches["retain"]["may_must_semantics"]["sure_basin_omega_containment_must"]["size"],
        },
        {
            "consequence": "H_edge_type_after_policy_nats",
            "erase": branches["erase"]["typed_entropy_ledger"]["H_edge_type_after_policy_nats"],
            "retain": branches["retain"]["typed_entropy_ledger"]["H_edge_type_after_policy_nats"],
        },
    ]
    for row in consequences:
        row["differs"] = row["erase"] != row["retain"]

    payload: dict[str, Any] = {
        "schema_version": "policy_discriminator_table_v0",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "decision_status": "owner_gated",
        "recommendation_emitted": False,
        "allowed_claims": ["computed consequences table for folded self-loop policy branches"],
        "disallowed_claims": [
            "default policy recommendation",
            "owner decision",
            "canonical policy",
            "axis admission",
            "bridge claim",
            "physics claim",
        ],
        "source_locks": {key: source_lock(path, key) for key, path in SOURCE_PATHS.items() if path.exists()},
        "authority_receipts": {
            "owner_decision_2": "both policies mathematically valid; owner chooses default",
            "fable_audit_improvement": "bounded discriminator informs the choice without making it",
            "g0_transition_graph_sha256_expected": EXPECTED_G0_SHA256,
            "g0_transition_graph_sha256_observed": observed_sha,
        },
        "fold_definition": {
            "fold_map": "cell_id -> committed G0 communicating-class/SCC id",
            "source_state_count": graph["state_count"],
            "source_transition_edge_rows": graph["edge_count"],
            "folded_node_count": len(folded_nodes),
            "folded_nodes": folded_nodes,
            "original_partition_signature": graph["partition_signature"],
        },
        "branches": branches,
        "computed_consequences_table": consequences,
        "vacuity_control": {
            "branches_differ_somewhere_computable": any(row["differs"] for row in consequences),
            "differing_consequences": [row["consequence"] for row in consequences if row["differs"]],
        },
        "downstream_consumer_impact": downstream_consumer_table(branches),
        "TOOL_MANIFEST": {
            "python_stdlib": "load source JSON, compute quotient relation, SCCs, may/must fixed point, entropy ledger",
        },
        "TOOL_INTEGRATION_DEPTH": {"python_stdlib": "load_bearing"},
        "claim_path_tools": ["python_stdlib"],
        "result_path": f"system_v6/sims/{SIM_ID}/results/{SIM_ID}_results.json",
    }
    payload["result_sha256_without_self"] = stable_sha256(payload)

    result_path = RESULT_DIR / f"{SIM_ID}_results.json"
    table_path = RESULT_DIR / f"{SIM_ID}_table.md"
    write_json(result_path, payload)
    table_path.write_text(build_markdown(payload), encoding="utf-8")
    print(json.dumps({"ok": True, "result": rel(result_path), "table": rel(table_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
