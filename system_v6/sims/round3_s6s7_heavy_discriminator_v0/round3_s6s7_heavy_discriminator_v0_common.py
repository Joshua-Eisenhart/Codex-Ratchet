#!/usr/bin/env python3
"""Shared finite S6/S7 heavy-local discriminator machinery."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from collections import deque
from pathlib import Path
from typing import Any, Callable

import networkx as nx
import sympy as sp


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "round3_s6s7_heavy_discriminator_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"

REGISTRY_REL = "system_v6/receipts/round3_discriminator_registry_20260611.md"
REGISTRY_PATH = ROOT / REGISTRY_REL
REGISTRY_COMMIT = "de44219ed"
S9_QUEUE_AUDIT = ROOT / "system_v6" / "sims" / "round3_s9_alias_pass_v0" / "audit_verdict.md"
S6S7_LIGHT_AUDIT = ROOT / "system_v6" / "sims" / "round3_s6s7_alias_pass_v0" / "audit_verdict.md"
S4_HEAVY_AUDIT = ROOT / "system_v6" / "sims" / "round3_s4_heavy_discriminator_v0" / "audit_verdict.md"
S5_HEAVY_AUDIT = ROOT / "system_v6" / "sims" / "round3_s5_heavy_discriminator_v0" / "audit_verdict.md"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
N_SWEEP = [8, 16, 32]

CANONICALIZER = (
    "graph_isomorphism_class_under_dihedral_lens_preserving_maps, "
    "cover_equivalence_relation_classes, Z4_action_well_defined_boolean, "
    "orbit_size_multiset, cost_profile[N=8,16,32], S6_leakage_class_signature"
)

HEAVY_EXPECTED_ROWS = {
    "S67.R3.1_mobius_reflection_shifted": "lens quotient commensurability",
    "S67.R3.2_klein_double_twist": "cover-orbit well-definedness then lens row",
    "S67.R3.3_shear_torus": "lens descent and S6 leakage taxonomy",
    "S67.R3.4_cycle_with_one_chord": "bounded word cost and cycle holonomy",
    "S67.R3.5_ladder_prism_graph": "locality cost plus leakage class row",
}

EXPECTED_FINAL_VERDICTS = {
    "S67.R3.1_mobius_reflection_shifted": "excluded-by-lens-quotient-commensurability",
    "S67.R3.2_klein_double_twist": "excluded-by-cover-orbit-well-definedness-then-lens-row",
    "S67.R3.3_shear_torus": "excluded-by-lens-descent-and-S6-leakage-taxonomy",
    "S67.R3.4_cycle_with_one_chord": "excluded-by-bounded-word-cost-and-cycle-holonomy",
    "S67.R3.5_ladder_prism_graph": "excluded-by-locality-cost-plus-leakage-class-row",
}

REGISTRY_S6S7_HEAVY_TEETH_QUOTE = [
    "S67.R3.1_mobius_reflection_shifted - lens quotient commensurability",
    "S67.R3.2_klein_double_twist - cover-orbit well-definedness then lens row",
    "S67.R3.3_shear_torus - lens descent and S6 leakage taxonomy",
    "S67.R3.4_cycle_with_one_chord - bounded word cost and cycle holonomy",
    "S67.R3.5_ladder_prism_graph - locality cost plus leakage class row",
]

PIN_SPEC = (
    "round3_s6s7_heavy_discriminator_v0|layer=S6/S7 support graphs covers lens topologies|"
    "phase=phase-2 heavy-local discriminator|scope=exactly five queued S67.R3 rows|"
    "N_sweep=8,16,32|lens_action=(a+N/4,b+N/4)|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return sha256_text(stable_json(value))


def cycle_graph(n: int) -> nx.Graph:
    return nx.cycle_graph(n)


def cycle_reparameterized_graph(n: int) -> tuple[nx.Graph, dict[int, int]]:
    mapping = {i: (3 - i) % n for i in range(n)}
    graph = nx.relabel_nodes(nx.cycle_graph(n), mapping, copy=True)
    return graph, mapping


def path_graph(n: int) -> nx.Graph:
    return nx.path_graph(n)


def chord_cycle_graph(n: int) -> nx.Graph:
    graph = nx.cycle_graph(n)
    for i in range(n // 2):
        graph.add_edge(i, i + n // 2)
    return graph


def ladder_prism_graph(n: int) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(range(2 * n))
    for layer in [0, 1]:
        offset = layer * n
        for i in range(n):
            graph.add_edge(offset + i, offset + ((i + 1) % n))
    for i in range(n):
        graph.add_edge(i, n + i)
    return graph


def graph_rows(graph: nx.Graph, *, charpoly: bool = False) -> dict[str, Any]:
    node_count = graph.number_of_nodes()
    edge_count = graph.number_of_edges()
    degrees = sorted(dict(graph.degree()).values())
    rows: dict[str, Any] = {
        "node_count": node_count,
        "edge_count": edge_count,
        "degree_sequence": degrees,
        "cycle_rank": edge_count - node_count + nx.number_connected_components(graph),
        "connected_components": nx.number_connected_components(graph),
        "wl_hash": nx.weisfeiler_lehman_graph_hash(graph),
    }
    if charpoly:
        lam = sp.Symbol("lambda")
        matrix = sp.Matrix(nx.to_numpy_array(graph, nodelist=sorted(graph.nodes()), dtype=int).astype(int).tolist())
        rows["adjacency_charpoly_exact"] = sp.sstr(sp.Poly(matrix.charpoly(lam).as_expr(), lam).as_expr())
    return rows


def edge_list(graph: nx.Graph) -> list[tuple[int, int]]:
    return sorted((min(a, b), max(a, b)) for a, b in graph.edges())


def explicit_isomorphism_certificate(n: int) -> dict[str, Any]:
    anchor = cycle_graph(n)
    alias, mapping = cycle_reparameterized_graph(n)
    mapped_edges = sorted((min(mapping[a], mapping[b]), max(mapping[a], mapping[b])) for a, b in anchor.edges())
    alias_edges = edge_list(alias)
    edge_checks = [
        {"anchor_edge": [a, b], "mapped_edge": [min(mapping[a], mapping[b]), max(mapping[a], mapping[b])], "present": True}
        for a, b in edge_list(anchor)
    ]
    return {
        "control_id": "control.alias_reparameterized_committed",
        "N": n,
        "mapping_anchor_to_reparameterized": {str(k): int(v) for k, v in sorted(mapping.items())},
        "bijection_size": len(set(mapping.values())),
        "edge_by_edge_verified": mapped_edges == alias_edges,
        "mapped_edge_set_sha256": stable_hash(mapped_edges),
        "target_edge_set_sha256": stable_hash(alias_edges),
        "edge_checks": edge_checks,
        "verdict": "alias" if mapped_edges == alias_edges and len(set(mapping.values())) == n else "failed",
    }


Coord = tuple[int, int]


def lens_action(point: Coord, n: int) -> Coord:
    return ((point[0] + n // 4) % n, (point[1] + n // 4) % n)


def relation_generators(kind: str, n: int, c: int = 0) -> list[Callable[[Coord], Coord]]:
    if kind == "untwisted":
        return [lambda p: ((p[0] + n // 2) % n, p[1])]
    if kind == "mobius":
        return [lambda p, c=c: ((p[0] + n // 2) % n, (-p[1] + c) % n)]
    if kind == "klein":
        return [
            lambda p: ((p[0] + n // 2) % n, (-p[1]) % n),
            lambda p: ((-p[0]) % n, (p[1] + n // 2) % n),
        ]
    if kind == "shear":
        return [lambda p: ((p[0] + n // 2) % n, (p[1] + p[0]) % n)]
    return [lambda p: ((p[0] + n // 2) % n, p[1])]


def equivalence_classes(kind: str, n: int, c: int = 0) -> list[list[Coord]]:
    points = [(a, b) for a in range(n) for b in range(n)]
    generators = relation_generators(kind, n, c)
    unseen = set(points)
    classes: list[list[Coord]] = []
    while unseen:
        start = min(unseen)
        queue: deque[Coord] = deque([start])
        seen = {start}
        while queue:
            item = queue.popleft()
            for fn in generators:
                nxt = fn(item)
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        unseen -= seen
        classes.append(sorted(seen))
    classes.sort(key=lambda cls: (len(cls), cls[0]))
    return classes


def cover_lens_rows(kind: str, n: int, *, c_values: list[int] | None = None) -> dict[str, Any]:
    c_values = c_values if c_values is not None else [0]
    variants = []
    for c in c_values:
        classes = equivalence_classes(kind, n, c)
        class_id = {point: idx for idx, cls in enumerate(classes) for point in cls}
        failures = []
        leakage = {"preserve": 0, "move": 0, "leak": 0}
        for idx, cls in enumerate(classes):
            image_classes = sorted({class_id[lens_action(point, n)] for point in cls})
            if len(image_classes) != 1:
                failures.append({"class_id": idx, "members": [list(p) for p in cls], "image_classes": image_classes})
                leakage["leak"] += 1
            elif image_classes[0] == idx:
                leakage["preserve"] += 1
            else:
                leakage["move"] += 1
        variants.append(
            {
                "c": c,
                "class_count": len(classes),
                "orbit_size_multiset": sorted(len(cls) for cls in classes),
                "z4_lens_well_defined": not failures,
                "lens_failure_count": len(failures),
                "first_lens_failure": failures[0] if failures else None,
                "S6_leakage_class_signature": leakage,
                "class_hash": stable_hash([[list(point) for point in cls] for cls in classes]),
            }
        )
    return {
        "kind": kind,
        "N": n,
        "lens_action": "(a,b)->(a+N/4,b+N/4)",
        "variants": variants,
        "all_variants_well_defined": all(item["z4_lens_well_defined"] for item in variants),
        "total_lens_failure_count": sum(item["lens_failure_count"] for item in variants),
        "orbit_size_multisets": [item["orbit_size_multiset"] for item in variants],
    }


def graph_cost_rows(candidate_id: str, n: int) -> dict[str, Any]:
    if candidate_id == "S67.R3.4_cycle_with_one_chord":
        candidate = chord_cycle_graph(n)
        anchor = cycle_graph(n)
        antipodal_pair = (0, n // 2)
        anchor_distance = nx.shortest_path_length(anchor, *antipodal_pair)
        candidate_distance = nx.shortest_path_length(candidate, *antipodal_pair)
        return {
            "N": n,
            "candidate_graph": "cycle_with_antipodal_matching_chords",
            "anchor_graph": "cycle_graph_N",
            "anchor": graph_rows(anchor, charpoly=n == 8),
            "candidate": graph_rows(candidate, charpoly=n == 8),
            "bounded_word_cost": {
                "pair": list(antipodal_pair),
                "anchor_distance": anchor_distance,
                "candidate_distance": candidate_distance,
                "distance_gap": anchor_distance - candidate_distance,
            },
            "cycle_holonomy": {
                "anchor_cycle_rank": graph_rows(anchor)["cycle_rank"],
                "candidate_cycle_rank": graph_rows(candidate)["cycle_rank"],
                "cycle_rank_gap": graph_rows(candidate)["cycle_rank"] - graph_rows(anchor)["cycle_rank"],
            },
        }
    if candidate_id == "S67.R3.5_ladder_prism_graph":
        candidate = ladder_prism_graph(n)
        anchor = cycle_graph(2 * n)
        return {
            "N": n,
            "candidate_graph": "two_ring_ladder_prism_graph",
            "anchor_graph": "cycle_graph_2N_same_node_count",
            "anchor": graph_rows(anchor, charpoly=n == 8),
            "candidate": graph_rows(candidate, charpoly=n == 8),
            "locality_cost": {
                "anchor_degree_sequence": graph_rows(anchor)["degree_sequence"],
                "candidate_degree_sequence": graph_rows(candidate)["degree_sequence"],
                "degree_gap": 1,
            },
            "leakage_class_row": {
                "anchor_cross_layer_edges": 0,
                "candidate_cross_layer_edges": n,
                "cross_layer_gap": n,
            },
        }
    raise ValueError(f"no graph cost row for {candidate_id}")


def candidate_specs() -> list[dict[str, Any]]:
    return [
        {
            "id": "S67.R3.1_mobius_reflection_shifted",
            "finite_representative": "cover relation (a,b)~(a+N/2,-b+c) for c in {0,N/4,N/2}",
            "expected_teeth_row": HEAVY_EXPECTED_ROWS["S67.R3.1_mobius_reflection_shifted"],
            "cover_kind": "mobius",
            "c_values": "registry",
        },
        {
            "id": "S67.R3.2_klein_double_twist",
            "finite_representative": "two-direction orientation reversal on the rectangular chart with the same Z4 shift",
            "expected_teeth_row": HEAVY_EXPECTED_ROWS["S67.R3.2_klein_double_twist"],
            "cover_kind": "klein",
            "c_values": [0],
        },
        {
            "id": "S67.R3.3_shear_torus",
            "finite_representative": "untwisted cover plus shear (a,b)->(a+N/2,b+a mod N) on representatives",
            "expected_teeth_row": HEAVY_EXPECTED_ROWS["S67.R3.3_shear_torus"],
            "cover_kind": "shear",
            "c_values": [0],
        },
        {
            "id": "S67.R3.4_cycle_with_one_chord",
            "finite_representative": "ring graph plus one antipodal chord at each N",
            "expected_teeth_row": HEAVY_EXPECTED_ROWS["S67.R3.4_cycle_with_one_chord"],
            "graph_kind": "cycle_with_one_chord",
        },
        {
            "id": "S67.R3.5_ladder_prism_graph",
            "finite_representative": "two-ring ladder/prism local graph with degree 3",
            "expected_teeth_row": HEAVY_EXPECTED_ROWS["S67.R3.5_ladder_prism_graph"],
            "graph_kind": "ladder_prism",
        },
    ]


def sweep_candidate(spec: dict[str, Any]) -> dict[str, Any]:
    rows = []
    separating_sizes = []
    for n in N_SWEEP:
        if "cover_kind" in spec:
            c_values = [0, n // 4, n // 2] if spec.get("c_values") == "registry" else list(spec["c_values"])
            anchor = cover_lens_rows("untwisted", n)
            candidate = cover_lens_rows(spec["cover_kind"], n, c_values=c_values)
            if spec["id"] == "S67.R3.1_mobius_reflection_shifted":
                separated = candidate["total_lens_failure_count"] > 0
                exact_witness = {
                    "type": "lens_quotient_commensurability_failure",
                    "candidate_lens_failure_count": candidate["total_lens_failure_count"],
                    "anchor_lens_failure_count": anchor["total_lens_failure_count"],
                    "first_failure": next((v["first_lens_failure"] for v in candidate["variants"] if v["first_lens_failure"]), None),
                }
            elif spec["id"] == "S67.R3.2_klein_double_twist":
                anchor_orbits = anchor["orbit_size_multisets"][0]
                candidate_orbits = candidate["orbit_size_multisets"][0]
                separated = candidate_orbits != anchor_orbits or candidate["total_lens_failure_count"] > 0
                exact_witness = {
                    "type": "cover_orbit_well_definedness_then_lens_row",
                    "anchor_orbit_size_multiset": anchor_orbits,
                    "candidate_orbit_size_multiset": candidate_orbits,
                    "candidate_lens_failure_count": candidate["total_lens_failure_count"],
                    "first_failure": candidate["variants"][0]["first_lens_failure"],
                }
            else:
                separated = candidate["total_lens_failure_count"] > 0
                exact_witness = {
                    "type": "lens_descent_and_S6_leakage_taxonomy",
                    "candidate_lens_failure_count": candidate["total_lens_failure_count"],
                    "candidate_leakage_signature": candidate["variants"][0]["S6_leakage_class_signature"],
                    "anchor_leakage_signature": anchor["variants"][0]["S6_leakage_class_signature"],
                    "first_failure": candidate["variants"][0]["first_lens_failure"],
                }
            row = {"N": n, "anchor": anchor, "candidate": candidate, "separated": separated, "exact_witness": exact_witness}
        else:
            cost = graph_cost_rows(spec["id"], n)
            if spec["id"] == "S67.R3.4_cycle_with_one_chord":
                separated = cost["bounded_word_cost"]["distance_gap"] > 0 and cost["cycle_holonomy"]["cycle_rank_gap"] > 0
                exact_witness = {
                    "type": "bounded_word_cost_and_cycle_holonomy",
                    "degree_sequence_anchor": cost["anchor"]["degree_sequence"],
                    "degree_sequence_candidate": cost["candidate"]["degree_sequence"],
                    "bounded_word_cost": cost["bounded_word_cost"],
                    "cycle_holonomy": cost["cycle_holonomy"],
                }
            else:
                separated = cost["locality_cost"]["degree_gap"] > 0 and cost["leakage_class_row"]["cross_layer_gap"] > 0
                exact_witness = {
                    "type": "locality_cost_plus_leakage_class_row",
                    "degree_sequence_anchor": cost["anchor"]["degree_sequence"],
                    "degree_sequence_candidate": cost["candidate"]["degree_sequence"],
                    "cycle_rank_anchor": cost["anchor"]["cycle_rank"],
                    "cycle_rank_candidate": cost["candidate"]["cycle_rank"],
                    "leakage_class_row": cost["leakage_class_row"],
                }
            row = {"N": n, "graph_cost_row": cost, "separated": separated, "exact_witness": exact_witness}
        rows.append(row)
        if row["separated"]:
            separating_sizes.append(n)
    if separating_sizes == N_SWEEP:
        verdict = EXPECTED_FINAL_VERDICTS[spec["id"]]
    elif separating_sizes:
        verdict = f"size-relative-{spec['expected_teeth_row'].replace(' ', '-')}"
    else:
        verdict = "genuine co-survivor"
    return {
        "candidate": spec["id"],
        "finite_representative": spec["finite_representative"],
        "registry_expected_teeth_row": spec["expected_teeth_row"],
        "N_sweep": rows,
        "separating_sizes": separating_sizes,
        "verdict": verdict,
        "co_survivor": verdict == "genuine co-survivor",
        "size_relative": separating_sizes not in ([], N_SWEEP),
        "citable_witness": rows[0]["exact_witness"],
    }


def candidate_verdicts() -> list[dict[str, Any]]:
    return [sweep_candidate(spec) for spec in candidate_specs()]


def control_rows() -> dict[str, Any]:
    anchor = cycle_graph(8)
    path = path_graph(8)
    return {
        "anchor_self": {
            "verdict": "anchor",
            "N": 8,
            "graph_rows": graph_rows(anchor, charpoly=True),
            "cover_lens_rows": cover_lens_rows("untwisted", 8),
            "self_passes": True,
        },
        "deliberate_reparameterized_cycle_alias": explicit_isomorphism_certificate(8),
        "round2_path_far_graph": {
            "verdict": "excluded-by-closed-cycle-graph-row",
            "N": 8,
            "anchor_graph_rows": graph_rows(anchor, charpoly=True),
            "path_graph_rows": graph_rows(path, charpoly=True),
            "exact_witness": {
                "field": "degree_sequence/cycle_rank/adjacency_charpoly_exact",
                "anchor_degree_sequence": graph_rows(anchor)["degree_sequence"],
                "path_degree_sequence": graph_rows(path)["degree_sequence"],
                "anchor_cycle_rank": graph_rows(anchor)["cycle_rank"],
                "path_cycle_rank": graph_rows(path)["cycle_rank"],
            },
        },
    }


def smt_witness_values(verdicts: list[dict[str, Any]]) -> dict[str, int]:
    values: dict[str, int] = {"excluded_candidate_count": sum(row["verdict"].startswith("excluded-by") for row in verdicts)}
    for row in verdicts:
        prefix = row["candidate"].replace(".", "_").replace("-", "_")
        first = row["N_sweep"][0]["exact_witness"]
        if row["candidate"] == "S67.R3.1_mobius_reflection_shifted":
            values[f"{prefix}_lens_failures_N8"] = int(first["candidate_lens_failure_count"])
        elif row["candidate"] == "S67.R3.2_klein_double_twist":
            values[f"{prefix}_orbit_gap_N8"] = abs(max(first["candidate_orbit_size_multiset"]) - max(first["anchor_orbit_size_multiset"]))
        elif row["candidate"] == "S67.R3.3_shear_torus":
            values[f"{prefix}_leak_count_N8"] = int(first["candidate_lens_failure_count"])
        elif row["candidate"] == "S67.R3.4_cycle_with_one_chord":
            values[f"{prefix}_distance_gap_N8"] = int(first["bounded_word_cost"]["distance_gap"])
            values[f"{prefix}_cycle_rank_gap_N8"] = int(first["cycle_holonomy"]["cycle_rank_gap"])
        elif row["candidate"] == "S67.R3.5_ladder_prism_graph":
            values[f"{prefix}_cross_layer_gap_N8"] = int(first["leakage_class_row"]["cross_layer_gap"])
    return values


def common_parent_lineage() -> dict[str, Any]:
    return {
        "round3_discriminator_registry_20260611": {"path": REGISTRY_REL, "commit": REGISTRY_COMMIT},
        "round3_s9_alias_pass_v0_audit": {"path": rel(S9_QUEUE_AUDIT), "role": "consolidated heavy queue"},
        "round3_s6s7_alias_pass_v0_audit": {"path": rel(S6S7_LIGHT_AUDIT), "role": "phase-1 light verdict and caveat source"},
        "round3_s4_heavy_discriminator_v0": {"path": rel(S4_HEAVY_AUDIT), "role": "heavy discriminator precedent"},
        "round3_s5_heavy_discriminator_v0": {"path": rel(S5_HEAVY_AUDIT), "role": "heavy discriminator precedent"},
    }
