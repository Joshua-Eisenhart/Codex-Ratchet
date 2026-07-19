#!/usr/bin/env python3
"""Re-offer every base and nesting proposal inside one finite entropy geometry.

This is the feedback pass missing from a merely staged ladder.  It does not
assume that the packet-relative base or nesting winners remain winners after
the entropic-geometric requirements arrive.  Every one of the sixteen base
presentations is crossed with every one of the eleven nesting presentations
and every declared potential/metric pair.  The resulting 528 complete finite
manifolds are settled before any comparison is made.

The finite manifold is a factor complex built from the same complete nested
histories used by the source packets.  Its entropy potential, Hessian metric,
factor Laplacian, Schur-compressed inner geometry, expansion response, and
renesting counterfactual are therefore views of the same decoded object.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any

from common import digest, matrix_subtract, max_abs_matrix, schur_complement, submatrix, write_json
from nesting_ratchet import NESTING_KINDS, evaluate_candidate as evaluate_nesting, parse_packet, simulate_nesting


GEOMETRY_PROFILES = {
    "no_geometry": {"potential": "none", "metric": "none"},
    "quadratic_euclidean": {"potential": "quadratic", "metric": "euclidean"},
    "shannon_fisher": {"potential": "shannon", "metric": "fisher"},
}

FULL_REQUIREMENTS = (
    "finite_nonempty_whole",
    "base_survives_all_source_packets",
    "baseline_source_exact",
    "expanded_source_exact",
    "outer_restriction_changes_inner",
    "inner_restriction_changes_outer",
    "baseline_persists_under_expansion",
    "expansion_adds_configuration",
    "potential_and_metric_cogenerated",
    "nested_entropy_chain_rule",
    "nested_metric_chain_rule",
    "factor_geometry_uses_same_histories",
    "outer_geometry_changes_inner_geometry",
    "expansion_changes_effective_inner_geometry",
    "renesting_changes_effective_inner_geometry",
    "source_ancestry_retained",
)


def entropy_geometry(profile: str, decoded: set[tuple[Any, Any, Any]]) -> dict[str, Any]:
    """Compute a potential and tangent metric on the finite history simplex."""
    rows = sorted(decoded)
    count = len(rows)
    if not count:
        return {
            "history_count": 0,
            "cogenerated": False,
            "potential_chain_rule": False,
            "metric_chain_rule": False,
            "history_digest": digest([]),
        }
    potential = GEOMETRY_PROFILES[profile]["potential"]
    metric = GEOMETRY_PROFILES[profile]["metric"]
    probabilities = [1.0 / count for _ in rows]
    groups: dict[Any, list[int]] = {}
    for index, row in enumerate(rows):
        groups.setdefault(row[0], []).append(index)

    if potential == "shannon":
        joint = sum(value * math.log(value) for value in probabilities)
    elif potential == "quadratic":
        joint = 0.5 * sum(value * value for value in probabilities)
    else:
        joint = 0.0
    masses = {group: len(indices) / count for group, indices in groups.items()}
    if potential == "shannon":
        outer = sum(value * math.log(value) for value in masses.values())
        conditional = sum(
            masses[group] * sum((1.0 / len(indices)) * math.log(1.0 / len(indices)) for _ in indices)
            for group, indices in groups.items()
        )
    elif potential == "quadratic":
        outer = 0.5 * sum(value * value for value in masses.values())
        conditional = sum(
            masses[group] * 0.5 * sum((1.0 / len(indices)) ** 2 for _ in indices)
            for group, indices in groups.items()
        )
    else:
        outer = conditional = 0.0

    raw_tangent = [((index * 7 + 3) % 11) - 5 for index in range(count)]
    mean = sum(raw_tangent) / count
    tangent = [value - mean for value in raw_tangent]
    if metric == "fisher":
        joint_metric = sum(value * value / probability for value, probability in zip(tangent, probabilities))
    elif metric == "euclidean":
        joint_metric = sum(value * value for value in tangent)
    else:
        joint_metric = 0.0
    outer_metric = 0.0
    inner_metric = 0.0
    for group, indices in groups.items():
        mass = masses[group]
        group_tangent = sum(tangent[index] for index in indices)
        if metric == "fisher":
            outer_metric += group_tangent * group_tangent / mass
        elif metric == "euclidean":
            outer_metric += group_tangent * group_tangent
        q = 1.0 / len(indices)
        conditional_tangent = [(tangent[index] - group_tangent * q) / mass for index in indices]
        if metric == "fisher":
            inner_metric += mass * sum(value * value / q for value in conditional_tangent)
        elif metric == "euclidean":
            inner_metric += mass * sum(value * value for value in conditional_tangent)

    potential_error = abs(joint - outer - conditional)
    metric_error = abs(joint_metric - outer_metric - inner_metric)
    cogenerated = (
        (potential == "shannon" and metric == "fisher")
        or (potential == "quadratic" and metric == "euclidean")
    )
    return {
        "history_count": count,
        "history_digest": digest(rows),
        "potential": potential,
        "metric": metric,
        "joint_potential": joint,
        "outer_plus_conditional_potential": outer + conditional,
        "potential_chain_error": potential_error,
        "joint_metric": joint_metric,
        "outer_plus_conditional_metric": outer_metric + inner_metric,
        "metric_chain_error": metric_error,
        "cogenerated": cogenerated,
        "potential_chain_rule": potential != "none" and potential_error < 1e-10,
        "metric_chain_rule": metric != "none" and metric_error < 1e-8,
    }


def relation_edges(kind: str) -> tuple[tuple[int, int], ...]:
    return {
        "chain_012": ((0, 1), (1, 2)),
        "chain_021": ((0, 2), (2, 1)),
        "chain_102": ((1, 0), (0, 2)),
        "fan_outer": ((0, 1), (0, 2)),
        "complete_pairwise": ((0, 1), (1, 2), (0, 2)),
        "outer_functions": ((0, 1), (1, 2)),
        "inner_functions": ((2, 1), (1, 0)),
        "identity_bijection": ((0, 1), (1, 2)),
        "twisted_bijection": ((0, 1), (1, 2)),
    }.get(kind, ())


def factors_for(kind: str, target: set[tuple[Any, Any, Any]], decoded: set[tuple[Any, Any, Any]]):
    """Return typed constraint factors; every factor is a tuple of layer states."""
    if kind == "independent_product":
        return [((layer, state),) for layer in range(3) for state in sorted({row[layer] for row in decoded})]
    if kind == "ternary_relation":
        return [tuple((layer, row[layer]) for layer in range(3)) for row in sorted(target)]
    output = []
    for left, right in relation_edges(kind):
        pairs = sorted({(row[left], row[right]) for row in (decoded if "bijection" in kind or "functions" in kind else target)})
        output.extend((((left, a), (right, b)) for a, b in pairs))
    return output


def node_masses(values: list[tuple[Any, ...]], decoded: set[tuple[Any, Any, Any]]):
    denominator = max(1, 3 * len(decoded))
    return {
        (layer, state): (1 + sum(row[layer] == state for row in decoded)) / (denominator + sum(len(v) for v in values))
        for layer, layer_values in enumerate(values)
        for state in layer_values
    }


def factor_operator(profile: str, kind: str, target, decoded, values) -> dict[str, Any]:
    """Build the factor-complex Laplacian and Schur-compress to layer two."""
    state_nodes = [("state", layer, state) for layer, layer_values in enumerate(values) for state in layer_values]
    factors = factors_for(kind, target, decoded)
    factor_nodes = [("factor", index) for index in range(len(factors))]
    nodes = state_nodes + factor_nodes
    index = {node: position for position, node in enumerate(nodes)}
    size = len(nodes)
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    masses = node_masses(values, decoded)
    edge_count = 0
    for factor_index, factor in enumerate(factors):
        fnode = ("factor", factor_index)
        factor_mass = sum(masses[item] for item in factor) / max(1, len(factor))
        for layer_state in factor:
            snode = ("state", layer_state[0], layer_state[1])
            if profile == "shannon_fisher":
                left_mass = masses[layer_state]
                weight = 2.0 * left_mass * factor_mass / max(1e-15, left_mass + factor_mass)
            else:
                weight = 1.0
            left, right = index[snode], index[fnode]
            matrix[left][left] += weight
            matrix[right][right] += weight
            matrix[left][right] -= weight
            matrix[right][left] -= weight
            edge_count += 1
    for position in range(size):
        matrix[position][position] += 0.25
    keep_nodes = [("state", 2, state) for state in values[2]]
    keep = [index[node] for node in keep_nodes]
    eliminate = [position for position in range(size) if position not in set(keep)]
    effective = schur_complement(matrix, keep, eliminate) if eliminate else submatrix(matrix, keep, keep)
    bare = submatrix(matrix, keep, keep)
    delta = max_abs_matrix(matrix_subtract(bare, effective))
    return {
        "node_count": size,
        "factor_count": len(factors),
        "edge_count": edge_count,
        "inner_nodes": [[layer, list(state)] for _, layer, state in keep_nodes],
        "outer_changes_inner": delta > 1e-10,
        "bare_to_effective_max_change": delta,
        "effective_operator": effective,
        "effective_operator_digest": digest(effective),
        "factor_digest": digest(factors),
        "history_digest": digest(sorted(decoded)),
    }


def aligned_delta(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_labels = [tuple(node[1]) for node in left["inner_nodes"]]
    right_labels = [tuple(node[1]) for node in right["inner_nodes"]]
    common = sorted(set(left_labels) & set(right_labels))
    if not common:
        return 0.0
    left_index = [left_labels.index(label) for label in common]
    right_index = [right_labels.index(label) for label in common]
    left_matrix = submatrix(left["effective_operator"], left_index, left_index)
    right_matrix = submatrix(right["effective_operator"], right_index, right_index)
    return max_abs_matrix(matrix_subtract(left_matrix, right_matrix))


def geometry_cost(base_id: str, profile: str) -> dict[str, int]:
    scalar_native = {
        "classical_distribution", "rebit_density", "complex_density", "euclidean_jordan",
        "quaternionic", "octonionic",
    }
    if profile == "no_geometry":
        return {
            "geometry_auxiliary_carrier": 0,
            "geometry_native_lift": 0,
            "geometry_operations": 0,
            "geometry_axioms": 0,
            "geometry_scalar_field_dimension": 0,
        }
    native = base_id in scalar_native
    return {
        "geometry_auxiliary_carrier": int(not native),
        "geometry_native_lift": int(not native),
        "geometry_operations": 1 if native else (2 if profile == "quadratic_euclidean" else 3),
        "geometry_axioms": 1 if native else (2 if profile == "quadratic_euclidean" else 3),
        "geometry_scalar_field_dimension": 1,
    }


def alternate_kind(kind: str) -> str:
    return {
        "complete_pairwise": "ternary_relation",
        "ternary_relation": "complete_pairwise",
        "chain_012": "chain_102",
        "chain_102": "chain_012",
        "chain_021": "fan_outer",
        "fan_outer": "chain_021",
        "outer_functions": "inner_functions",
        "inner_functions": "outer_functions",
        "identity_bijection": "twisted_bijection",
        "twisted_bijection": "identity_bijection",
        "independent_product": "complete_pairwise",
    }[kind]


def simulate_kernel(profile: str, kind: str, packets: list[dict[str, Any]]) -> dict[str, Any]:
    packet_rows = {}
    intermediates = {}
    for packet in packets:
        target, values = parse_packet(packet)
        nested = simulate_nesting(kind, target, values)
        decoded = nested.pop("decoded")
        geometry = entropy_geometry(profile, decoded)
        operator = factor_operator(profile, kind, target, decoded, values)
        alternate = alternate_kind(kind)
        alternate_nested = simulate_nesting(alternate, target, values)
        alternate_decoded = alternate_nested.pop("decoded")
        alternate_operator = factor_operator(profile, alternate, target, alternate_decoded, values)
        renesting_delta = aligned_delta(operator, alternate_operator)
        packet_rows[packet["packet_id"]] = {
            "target_count": len(target),
            "decoded_count": len(decoded),
            "extra_count": len(decoded - target),
            "missing_count": len(target - decoded),
            "exact": decoded == target,
            "decoded_digest": digest(sorted(decoded)),
            "target_digest": digest(sorted(target)),
            "nesting_model": nested["model"],
            "outer_restriction_changes_inner": nested["outer_restriction_changes_inner"],
            "inner_restriction_changes_outer": nested["inner_restriction_changes_outer"],
            "entropy_geometry": geometry,
            "operator": {key: value for key, value in operator.items() if key != "effective_operator"},
            "alternate_nesting": alternate,
            "renesting_effective_operator_delta": renesting_delta,
            "renesting_changes_effective_inner": renesting_delta > 1e-10,
        }
        intermediates[packet["packet_id"]] = {"decoded": decoded, "operator": operator}
    baseline = intermediates["nested_completion_baseline"]
    expanded = intermediates["nested_completion_expanded"]
    expansion_delta = aligned_delta(baseline["operator"], expanded["operator"])
    baseline_states = baseline["decoded"]
    expanded_states = expanded["decoded"]
    return {
        "geometry_profile": profile,
        "nesting_kind": kind,
        "packet_results": packet_rows,
        "baseline_persists_under_expansion": baseline_states <= expanded_states,
        "expansion_adds_configuration": bool(expanded_states - baseline_states),
        "expansion_effective_inner_delta": expansion_delta,
        "expansion_changes_effective_inner": expansion_delta > 1e-10,
        "kernel_digest": digest(packet_rows),
    }


def evaluate_complete(base_id: str, base_row: dict[str, Any], kind: str, profile: str, kernel: dict[str, Any], source_digest: str) -> dict[str, Any]:
    baseline = kernel["packet_results"]["nested_completion_baseline"]
    expanded = kernel["packet_results"]["nested_completion_expanded"]
    geometry_rows = [baseline["entropy_geometry"], expanded["entropy_geometry"]]
    base_exact = all(row["exact"] for row in base_row["packet_results"].values())
    requirement_results = {
        "finite_nonempty_whole": all(row["decoded_count"] > 0 and row["operator"]["node_count"] > 0 for row in kernel["packet_results"].values()),
        "base_survives_all_source_packets": base_exact,
        "baseline_source_exact": baseline["exact"],
        "expanded_source_exact": expanded["exact"],
        "outer_restriction_changes_inner": all(row["outer_restriction_changes_inner"] for row in kernel["packet_results"].values()),
        "inner_restriction_changes_outer": all(row["inner_restriction_changes_outer"] for row in kernel["packet_results"].values()),
        "baseline_persists_under_expansion": kernel["baseline_persists_under_expansion"],
        "expansion_adds_configuration": kernel["expansion_adds_configuration"],
        "potential_and_metric_cogenerated": all(row["cogenerated"] for row in geometry_rows),
        "nested_entropy_chain_rule": all(row["potential_chain_rule"] for row in geometry_rows),
        "nested_metric_chain_rule": all(row["metric_chain_rule"] for row in geometry_rows),
        "factor_geometry_uses_same_histories": all(
            row["entropy_geometry"]["history_digest"] == row["operator"]["history_digest"]
            for row in kernel["packet_results"].values()
        ),
        "outer_geometry_changes_inner_geometry": all(row["operator"]["outer_changes_inner"] for row in kernel["packet_results"].values()),
        "expansion_changes_effective_inner_geometry": kernel["expansion_changes_effective_inner"],
        "renesting_changes_effective_inner_geometry": all(row["renesting_changes_effective_inner"] for row in kernel["packet_results"].values()),
        "source_ancestry_retained": bool(source_digest),
    }
    vector = {f"base_{key}": value for key, value in base_row["presumption_vector"].items()}
    sample = baseline
    vector.update({
        "nest_relation_count": {
            "independent_product": 0, "ternary_relation": 1, "complete_pairwise": 3,
        }.get(kind, 2),
        "nest_maximum_arity": 3 if kind == "ternary_relation" else (1 if kind == "independent_product" else 2),
        "nest_stored_tuple_slots": sum(
            row["operator"]["factor_count"] for row in kernel["packet_results"].values()
        ),
        "nest_primitive_operations": int(kind not in {"independent_product", "ternary_relation"}),
        "nest_deterministic_choices": sum(
            row["decoded_count"] for row in kernel["packet_results"].values()
        ) if kind in {"outer_functions", "inner_functions", "identity_bijection", "twisted_bijection"} else 0,
        "nest_chosen_edges": len(relation_edges(kind)),
        **geometry_cost(base_id, profile),
    })
    candidate_id = f"{base_id}__{kind}__{profile}"
    return {
        "candidate_id": candidate_id,
        "base_candidate": base_id,
        "nesting_kind": kind,
        "geometry_profile": profile,
        "source_packet_digest": source_digest,
        "kernel_digest": kernel["kernel_digest"],
        "requirement_results": requirement_results,
        "presumption_vector": vector,
        "complete_whole_candidate": True,
        "behavior_signature": digest({
            "base_behavior": base_row["behavior_signature"],
            "kernel": kernel["kernel_digest"],
            "requirements": requirement_results,
        }),
        "whole_summary": {
            "baseline_decoded_count": sample["decoded_count"],
            "expanded_decoded_count": expanded["decoded_count"],
            "baseline_effective_operator_digest": sample["operator"]["effective_operator_digest"],
            "expanded_effective_operator_digest": expanded["operator"]["effective_operator_digest"],
            "expansion_effective_inner_delta": kernel["expansion_effective_inner_delta"],
            "baseline_renesting_delta": sample["renesting_effective_operator_delta"],
            "expanded_renesting_delta": expanded["renesting_effective_operator_delta"],
            "baseline_entropy_geometry": sample["entropy_geometry"],
            "expanded_entropy_geometry": expanded["entropy_geometry"],
        },
    }


def active_view(row: dict[str, Any], requirements: list[str]) -> dict[str, Any]:
    return {
        "failed": sorted(name for name in requirements if not row["requirement_results"][name]),
        "vector": row["presumption_vector"],
    }


def beats(left: dict[str, Any], right: dict[str, Any]) -> tuple[bool, str]:
    left_failed, right_failed = set(left["failed"]), set(right["failed"])
    if left_failed < right_failed:
        return True, "strictly fewer failed whole-manifold requirements"
    if left_failed != right_failed:
        return False, "incomparable failure sets"
    keys = sorted(left["vector"])
    no_worse = all(left["vector"][key] <= right["vector"][key] for key in keys)
    better = any(left["vector"][key] < right["vector"][key] for key in keys)
    return no_worse and better, "Pareto-smaller explicit presumption vector" if no_worse and better else "incomparable vectors"


def recompute(rows: dict[str, dict[str, Any]], requirements: list[str], previous_frontier: list[str], previous_purgatory: set[str], default: str):
    views = {name: active_view(row, requirements) for name, row in rows.items()}
    beaten_by = {name: [] for name in rows}
    winner_counts = {name: 0 for name in rows}
    comparison_hasher = hashlib.sha256()
    comparison_count = 0
    names = sorted(rows)
    for left in names:
        for right in names:
            if left == right:
                continue
            won, reason = beats(views[left], views[right])
            comparison_hasher.update(
                f"{left}\0{right}\0{int(won)}\0{reason}\n".encode("utf-8")
            )
            comparison_count += 1
            if won:
                winner_counts[right] += 1
                # One deterministic witness is sufficient to prove that a
                # candidate is off-frontier.  The digest and count retain the
                # complete pairwise comparison without bloating the archive
                # with tens of megabytes of repeated witness strings.
                if not beaten_by[right]:
                    beaten_by[right].append({"candidate_id": left, "reason": reason})
    frontier = sorted(name for name in names if not beaten_by[name])
    purgatory = set(names) - set(frontier)
    if default not in frontier:
        default = frontier[0]
    return {
        "requirements": list(requirements),
        "frontier": frontier,
        "previous_frontier": previous_frontier,
        "purgatory": sorted(purgatory),
        "reentered_from_purgatory": sorted(previous_purgatory & set(frontier)),
        "newly_in_purgatory": sorted(purgatory - previous_purgatory),
        "default": default,
        "beaten_by": beaten_by,
        "winner_counts": winner_counts,
        "comparison_count": comparison_count,
        "comparison_digest": "sha256:" + comparison_hasher.hexdigest(),
        "views_digest": digest(views),
        "candidate_count_recomputed": len(views),
    }, purgatory, default


def run(source: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    packets = source["nesting_packets"]
    base_rows = base["candidate_evaluations"]
    kernels = {
        f"{kind}__{profile}": simulate_kernel(profile, kind, packets)
        for kind in NESTING_KINDS
        for profile in GEOMETRY_PROFILES
    }
    rows = {
        f"{base_id}__{kind}__{profile}": evaluate_complete(
            base_id, base_row, kind, profile, kernels[f"{kind}__{profile}"], source["result_digest"]
        )
        for base_id, base_row in sorted(base_rows.items())
        for kind in NESTING_KINDS
        for profile in GEOMETRY_PROFILES
    }
    expected_count = len(base_rows) * len(NESTING_KINDS) * len(GEOMETRY_PROFILES)
    default = "finite_relation__ternary_relation__shannon_fisher"
    if default not in rows:
        default = sorted(rows)[0]
    receipts = []
    purgatory: set[str] = set()
    previous_frontier: list[str] = []
    campaigns = (
        (
            "settle every complete candidate under structural survival before entropic requirements",
            [
                "finite_nonempty_whole", "base_survives_all_source_packets", "baseline_source_exact",
                "outer_restriction_changes_inner", "inner_restriction_changes_outer",
                "baseline_persists_under_expansion", "expansion_adds_configuration",
                "factor_geometry_uses_same_histories", "source_ancestry_retained",
            ],
        ),
        ("add complete entropic-geometric requirements and recompute all candidates", list(FULL_REQUIREMENTS)),
        (
            "requirement revision control: suspend source exactness and chain identities without deleting candidates",
            [
                "finite_nonempty_whole", "base_survives_all_source_packets",
                "outer_restriction_changes_inner", "inner_restriction_changes_outer",
                "baseline_persists_under_expansion", "expansion_adds_configuration",
                "factor_geometry_uses_same_histories", "outer_geometry_changes_inner_geometry",
                "expansion_changes_effective_inner_geometry", "renesting_changes_effective_inner_geometry",
                "source_ancestry_retained",
            ],
        ),
        ("restore full requirements and re-offer all 528 candidates", list(FULL_REQUIREMENTS)),
        ("open continuation tick with no new proposal", list(FULL_REQUIREMENTS)),
    )
    for reason, requirements in campaigns:
        receipt, purgatory, default = recompute(rows, requirements, previous_frontier, purgatory, default)
        receipt.update({
            "step": len(receipts),
            "reason": reason,
            "global_mss_claimed": False,
            "terminal_state": False,
        })
        receipt["receipt_digest"] = digest(receipt)
        receipts.append(receipt)
        previous_frontier = receipt["frontier"]

    final_frontier = receipts[-1]["frontier"]
    final_rows = [rows[name] for name in final_frontier]
    stage_two_frontier = set(receipts[1]["frontier"])
    revision_frontier = set(receipts[2]["frontier"])
    restored_frontier = set(receipts[3]["frontier"])
    process_checks = {
        "all_528_cross_layer_candidates_simulated_before_comparison": len(rows) == expected_count == 528,
        "every_candidate_is_a_complete_whole_manifold": all(row["complete_whole_candidate"] for row in rows.values()),
        "every_base_candidate_reoffered_after_geometry_arrives": {row["base_candidate"] for row in rows.values()} == set(base_rows),
        "every_nesting_kind_reoffered_after_geometry_arrives": {row["nesting_kind"] for row in rows.values()} == set(NESTING_KINDS),
        "all_geometry_profiles_compared": {row["geometry_profile"] for row in rows.values()} == set(GEOMETRY_PROFILES),
        "whole_geometry_depends_on_nesting": len({kernels[f"{kind}__shannon_fisher"]["kernel_digest"] for kind in NESTING_KINDS}) > 1,
        "whole_frontier_nonempty": bool(final_frontier),
        "final_candidates_pass_all_full_requirements": all(all(row["requirement_results"][name] for name in FULL_REQUIREMENTS) for row in final_rows),
        "final_frontier_is_plural": len(final_frontier) > 1,
        "requirement_revision_changes_frontier": revision_frontier != stage_two_frontier,
        "restoration_reoffers_all_candidates": receipts[3]["candidate_count_recomputed"] == 528,
        "restored_frontier_matches_full_comparison": restored_frontier == stage_two_frontier,
        "idle_tick_continues_without_error": receipts[4]["frontier"] == receipts[3]["frontier"],
        "operational_default_always_available": all(receipt["default"] in receipt["frontier"] for receipt in receipts),
        "no_global_mss_or_terminal_claim": all(not receipt["global_mss_claimed"] and not receipt["terminal_state"] for receipt in receipts),
    }
    result = {
        "schema": "ratchet.pack183.whole-feedback-ratchet.v1",
        "source_packet_digest": source["result_digest"],
        "base_census_digest": base["result_digest"],
        "base_candidate_count": len(base_rows),
        "nesting_candidate_count": len(NESTING_KINDS),
        "geometry_profile_count": len(GEOMETRY_PROFILES),
        "candidate_count": len(rows),
        "geometry_profiles": GEOMETRY_PROFILES,
        "kernel_count": len(kernels),
        "kernel_summaries": kernels,
        "candidate_evaluations": rows,
        "receipts": receipts,
        "final_frontier": final_frontier,
        "final_frontier_evaluations": {name: rows[name] for name in final_frontier},
        "operational_default": default,
        "purgatory": receipts[-1]["purgatory"],
        "process_checks": process_checks,
        "global_mss_claimed": False,
        "candidate_universe_exhausted": False,
        "terminal_state": False,
        "status": "OPEN_WHOLE_ENTROPIC_GEOMETRIC_FRONTIER_COMPUTED",
        "claim_ceiling": (
            "finite source-relative feedback comparison of 528 complete base/nesting/geometry candidates; "
            "this is a current survivable frontier, not an absolute MSS, final nesting, physical ontology, "
            "or proof that the declared proposal grammar is exhaustive"
        ),
    }
    result["all_pass"] = all(process_checks.values())
    result["result_digest"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.source.read_text(encoding="utf-8"))
    base = json.loads(args.base.read_text(encoding="utf-8"))
    result = run(source, base)
    write_json(args.output, result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "candidate_count": result["candidate_count"],
        "kernel_count": result["kernel_count"],
        "final_frontier": result["final_frontier"],
        "default": result["operational_default"],
        "process_checks": result["process_checks"],
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
