from __future__ import annotations

from generate_facts import generate
from oracle import Instance, enumerate_candidates, evaluate, normalize_labels


def base_payload(
    *,
    tolerance_edges: list[list[int]],
    demand: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "schema": "codex_ratchet.tolerance_to_equivalence_v1.instance.v1",
        "instance_id": "test",
        "seed": 0,
        "n": 4,
        "tolerance_edges": tolerance_edges,
        "current_labels": [0, 0, 0, 0],
        "demand": demand,
    }


def relation_pairs(labels: list[int]) -> set[tuple[int, int]]:
    return {
        (left, right)
        for left in range(len(labels) - 1)
        for right in range(left + 1, len(labels))
        if labels[left] == labels[right]
    }


def permute_payload(
    payload: dict[str, object], permutation: list[int]
) -> dict[str, object]:
    inverse = {old: new for new, old in enumerate(permutation)}
    current = payload["current_labels"]
    assert isinstance(current, list)
    return {
        **payload,
        "instance_id": "permuted",
        "tolerance_edges": [
            [inverse[left], inverse[right]]
            for left, right in payload["tolerance_edges"]
        ],
        "current_labels": [current[old] for old in permutation],
        "demand": [
            {
                **row,
                "pair": [
                    inverse[row["pair"][0]],
                    inverse[row["pair"][1]],
                ],
            }
            for row in payload["demand"]
        ],
    }


def test_candidate_enumeration_is_complete_at_bell_four_boundary() -> None:
    payload = base_payload(tolerance_edges=[], demand=[])
    instance = Instance.from_payload(payload)
    assert len(enumerate_candidates(instance)) == 15
    result = evaluate(payload)
    assert result["decision"] == "HOLD_NONPOSITIVE"


def test_unique_pareto_front_commits_without_expected_decision_input() -> None:
    payload = base_payload(
        tolerance_edges=[[0, 1], [2, 3]],
        demand=[{"pair": [1, 2], "weight": 1}],
    )
    result = evaluate(payload)
    assert result["candidate_count"] == 2
    assert result["admissible_count"] == 1
    assert result["decision"] == "COMMIT"
    assert result["selected"]["labels"] == [0, 0, 1, 1]


def test_plural_symmetric_front_holds() -> None:
    payload = base_payload(
        tolerance_edges=[],
        demand=[{"pair": [0, 1], "weight": 1}],
    )
    result = evaluate(payload)
    assert result["decision"] == "HOLD_MSS_AMBIGUOUS"
    assert len(result["pareto_front"]) >= 2
    assert result["selected"] is None


def test_simultaneous_label_permutation_is_equivariant() -> None:
    payload = base_payload(
        tolerance_edges=[[0, 1], [2, 3]],
        demand=[{"pair": [1, 2], "weight": 1}],
    )
    permutation = [2, 0, 3, 1]
    original = evaluate(payload)
    permuted = evaluate(permute_payload(payload, permutation))
    assert original["decision"] == permuted["decision"] == "COMMIT"
    original_pairs = relation_pairs(original["selected"]["labels"])
    inverse = {old: new for new, old in enumerate(permutation)}
    expected_pairs = {
        tuple(sorted((inverse[left], inverse[right])))
        for left, right in original_pairs
    }
    assert relation_pairs(permuted["selected"]["labels"]) == expected_pairs


def test_fact_generator_contains_no_oracle_answer_fields() -> None:
    payload = generate(17, 6)
    forbidden = {
        "expected",
        "expected_decision",
        "decision",
        "target_rung",
        "preferred_proposal",
        "proposal",
    }
    assert forbidden.isdisjoint(payload)
    Instance.from_payload(payload)
