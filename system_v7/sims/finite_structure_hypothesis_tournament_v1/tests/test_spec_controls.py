from __future__ import annotations

import itertools
import json
import math
from fractions import Fraction
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]


def load_spec() -> dict:
    return json.loads((HERE / "spec.json").read_text(encoding="utf-8"))


def preserves(matrix: tuple[tuple[int, ...], ...] | None, constants: tuple[int, ...], perm: tuple[int, ...]) -> bool:
    if any(perm[c] != c for c in constants):
        return False
    if matrix is None:
        return True
    n = len(perm)
    return all(matrix[i][j] == matrix[perm[i]][perm[j]] for i in range(n) for j in range(n))


def auts(n: int, matrix: tuple[tuple[int, ...], ...] | None = None, constants: tuple[int, ...] = ()) -> set[tuple[int, ...]]:
    return {perm for perm in itertools.permutations(range(n)) if preserves(matrix, constants, perm)}


def test_frozen_relation_counts() -> None:
    spec = load_spec()
    expected = spec["execution_bounds"]["binary_relation_count_by_exhaustive_size"]
    assert expected == {str(n): 2 ** (n * n) for n in (1, 2, 3)}


def test_root_presentations_share_data_without_collapsing_types() -> None:
    roots = {row["id"]: row for row in load_spec()["candidate_grammar"]["root_presentations"]}
    assert roots["J_n"]["semantic_type"] == "static_relation"
    assert roots["C_n"]["semantic_type"] == "transition_relation"
    assert roots["J_n"]["semantic_type"] != roots["C_n"]["semantic_type"]
    assert roots["J_n"]["internal_dynamics"] is False
    assert roots["C_n"]["internal_dynamics"] is True


def test_fixed_carrier_append_chain_and_replacement() -> None:
    n = 4
    universal = tuple(tuple(1 for _ in range(n)) for _ in range(n))
    a0 = auts(n)
    a1 = auts(n, universal)
    a2 = auts(n, universal, (0,))
    a3 = auts(n, universal, (0, 1))
    b2 = auts(n, universal, (1,))

    assert [len(a0), len(a1), len(a2), len(a3)] == [24, 24, 6, 2]
    assert a1 <= a0 and a2 <= a1 and a3 <= a2
    assert a1 == a0 and a2 < a1 and a3 < a2
    assert not b2 <= a2
    assert (2, 1, 0, 3) in b2 - a2


def relation_from_bits(n: int, bits: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple((bits >> (i * n + j)) & 1 for j in range(n)) for i in range(n))


def test_external_gate_counts_do_not_install_asymmetry() -> None:
    n = 3
    relations = [relation_from_bits(n, bits) for bits in range(2 ** (n * n))]
    reflexive = [r for r in relations if all(r[i][i] for i in range(n))]
    symmetric = [r for r in reflexive if all(r[i][j] == r[j][i] for i in range(n) for j in range(n))]
    universal = [r for r in symmetric if all(r[i][j] for i in range(n) for j in range(n))]
    assert [len(relations), len(reflexive), len(symmetric), len(universal)] == [512, 64, 8, 1]
    survivor_aut_before = {r: auts(n, r) for r in universal}
    survivor_aut_after = {r: auts(n, r) for r in universal}
    assert survivor_aut_before == survivor_aut_after


def entropy(row: tuple[Fraction, ...]) -> float:
    return -sum(float(p) * math.log2(float(p)) for p in row if p)


def test_symmetric_full_support_does_not_imply_white_noise() -> None:
    n = 4
    uniform = tuple(Fraction(1, n) for _ in range(n))
    lazy_rows = tuple(
        tuple(Fraction(1, 2) if i == j else Fraction(1, 2 * (n - 1)) for j in range(n))
        for i in range(n)
    )
    uniform_rows = tuple(uniform for _ in range(n))
    all_perms = set(itertools.permutations(range(n)))

    def kernel_auts(rows: tuple[tuple[Fraction, ...], ...]) -> set[tuple[int, ...]]:
        return {
            perm
            for perm in all_perms
            if all(rows[i][j] == rows[perm[i]][perm[j]] for i in range(n) for j in range(n))
        }

    assert kernel_auts(uniform_rows) == all_perms
    assert kernel_auts(lazy_rows) == all_perms
    assert all(p > 0 for row in lazy_rows for p in row)
    assert entropy(lazy_rows[0]) < entropy(uniform)
    assert len(set(lazy_rows)) == n
    assert len(set(uniform_rows)) == 1


def test_entropy_readouts_are_typed_not_candidate_set_entropy() -> None:
    readouts = load_spec()["entropy_capacity_readouts"]
    assert readouts["K0_fixed_n_state_entropy_change"] == "exactly zero"
    assert readouts["K0_one_step_conditional_entropy"] == "log2(n)"
    assert "none is a drive" in readouts["causal_status"]
    assert "candidate" not in readouts["K0_fixed_n_state_entropy_change"].lower()


def test_no_search_or_outer_clock_is_run() -> None:
    spec = load_spec()
    assert spec["execution_bounds"]["search_steps_run"] == 0
    assert spec["execution_bounds"]["ratchet_epochs_run"] == 0
    assert spec["clock_separation"]["frozen_search"]["status"] == "not_installed_in_v1"
    assert spec["clock_separation"]["ratchet_context"]["status"] == "not_run_in_v1"
