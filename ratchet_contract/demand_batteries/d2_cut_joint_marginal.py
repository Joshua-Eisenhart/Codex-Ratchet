#!/usr/bin/env python3
"""Executable classical-only battery for D2: cut-conditioned joint/marginal.

Carrier binding: ``read_outcome_z`` is the carrier's one 2-bit joint readout,
with token bit 0 treated as the a-position and token bit 1 as the b-position.
For one root and cut there is consequently one full four-token joint table,
not four independently prepared tables.  The abstract J[c,a,b] index says
which derived single-bit marginal is cross-checked; A and B are calculated
from that same joint table, with no additional probe action.

The carrier declares no native cut primitive.  This battery therefore imposes
cut 0 as identity and cut 1 as the existing native ``perturb_small_rx0``
action, selected because it changes the observed correlated-root joint table.
No carrier mechanics are added.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Mapping

# Running ``python3 path/to/this_file.py`` places this file's directory, not
# the repository root, on sys.path.  Add only that root for the prescribed
# standalone invocation.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ratchet_contract.fuel_sims.candidate_classical_exec import (
    ClassicalRelationalExecCandidate,
)


ROOT_BELL = "root_bell"
ROOT_CUT = "root_00"
CUT_ONE_ACTIONS = ("perturb_small_rx0",)
TOKENS = ("00", "01", "10", "11")
RESULT_PATH = Path(__file__).resolve().parent / "results" / "d2_battery_classical.json"
INDEX_READING = (
    "One read_outcome_z table per (root, cut); J[c,a,b] reuses that full "
    "table while a,b select matched arithmetic marginals derived from it."
)


def _table(outcome) -> dict[str, int]:
    """Render the finite joint outcome as a complete, deterministic table."""
    sparse = dict(outcome.entries)
    return {token: int(sparse.get(token, 0)) for token in TOKENS}


def _joint(candidate: ClassicalRelationalExecCandidate, root: str, cut: int) -> dict[str, int]:
    state = candidate.initial_state(root)
    actions = () if cut == 0 else CUT_ONE_ACTIONS
    for action in actions:
        state, _ack = candidate.step_C(state, action, None)
    _state, outcome = candidate.step_C(state, "read_outcome_z", None)
    return _table(outcome)


def _marginals(joint: Mapping[str, int]) -> tuple[dict[str, int], dict[str, int]]:
    """Return A(bit0) and B(bit1), directly summed from the joint table."""
    a = {"0": joint["00"] + joint["01"], "1": joint["10"] + joint["11"]}
    b = {"0": joint["00"] + joint["10"], "1": joint["01"] + joint["11"]}
    return a, b


def _product_of_marginals(joint: Mapping[str, int]) -> dict[str, int]:
    """Outer product expressed in the joint table's shared total-weight units."""
    a, b = _marginals(joint)
    total = sum(joint.values())
    if total <= 0:
        raise ValueError("read_outcome_z produced an empty table")
    # This carrier's 1000-shot tables make every product here integral; retain
    # exact integer arithmetic rather than introduce float probabilities.
    products = {
        "00": a["0"] * b["0"] // total,
        "01": a["0"] * b["1"] // total,
        "10": a["1"] * b["0"] // total,
        "11": a["1"] * b["1"] // total,
    }
    if any((a[t[0]] * b[t[1]]) % total for t in TOKENS):
        raise ValueError("non-integral product table; this battery requires exact finite counts")
    return products


def _permute_tokens(table: Mapping[str, int]) -> dict[str, int]:
    """Fixed post-read nonlocal token relabeling used only by the control.

    Swapping 01 and 11 makes the cut-0 Bell support {00, 01}, a factorable
    table.  It is intentionally a battery-side scrambled observation, not a
    modification or subclass of the carrier.
    """
    permutation = {"00": "00", "01": "11", "10": "10", "11": "01"}
    out = {token: 0 for token in TOKENS}
    for token, count in table.items():
        out[permutation[token]] += count
    return out


def _edge(name: str, table_a: Mapping[str, int], table_b: Mapping[str, int]) -> dict:
    left = dict(table_a)
    right = dict(table_b)
    return {"name": name, "table_a": left, "table_b": right, "differs": left != right}


def _six_edges(joints: Mapping[tuple[str, int], Mapping[str, int]]) -> list[dict]:
    edges: list[dict] = []
    for a in range(2):
        for b in range(2):
            edges.append(
                _edge(
                    f"cut_change_ab{a}{b}",
                    joints[(ROOT_CUT, 0)],
                    joints[(ROOT_CUT, 1)],
                )
            )
    for cut, a, b in ((0, 0, 0), (1, 1, 1)):
        joint = joints[(ROOT_BELL, cut)]
        edges.append(
            _edge(
                f"joint_vs_marginal_cut{cut}_{ROOT_BELL}_ab{a}{b}",
                joint,
                _product_of_marginals(joint),
            )
        )
    return edges


def build_result() -> dict:
    candidate = ClassicalRelationalExecCandidate()
    joints = {
        (root, cut): _joint(candidate, root, cut)
        for root in (ROOT_BELL, ROOT_CUT)
        for cut in (0, 1)
    }
    edges = _six_edges(joints)

    # Apply the deterministic post-read scramble before deriving control
    # marginals, so its factorability effect is measured on its own reading.
    scrambled_joints = {key: _permute_tokens(value) for key, value in joints.items()}
    control_edges = _six_edges(scrambled_joints)
    flipped = [edge["differs"] for edge in edges] != [edge["differs"] for edge in control_edges]

    digest_source = json.dumps(
        {f"{root}:cut{cut}": joints[(root, cut)] for root in (ROOT_BELL, ROOT_CUT) for cut in (0, 1)},
        sort_keys=True,
        separators=(",", ":"),
    )
    result = {
        "carrier": candidate.name,
        "d2_index_reading": INDEX_READING,
        "cuts_declared": "imposed",
        "declared_primitives_added": list(CUT_ONE_ACTIONS),
        "roots_used": [ROOT_BELL, ROOT_CUT],
        "edges": edges,
        "demand_edges_added": sum(edge["differs"] for edge in edges),
        "tables_digest": "sha256:" + hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:16],
        "negative_control": {
            "scheme": "fixed post-read token permutation swapping 01 and 11 before control marginals are derived",
            "edges": control_edges,
            "negative_control_flipped": flipped,
        },
        "promotion_allowed": False,
        "classification": "tool_lego_fit_probe",
        "claim_ceiling": "fuel for demand-thickening; admits nothing; quantum side blocked on memory-gated carrier",
    }
    if not flipped:
        result["negative_control"]["negative_control_note"] = (
            "BY_CONSTRUCTION: this token relabeling preserved the same six-edge firing pattern."
        )
    return result


def main() -> None:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"carrier={result['carrier']} demand_edges_added={result['demand_edges_added']}/6 "
        f"negative_control_flipped={result['negative_control']['negative_control_flipped']}"
    )


if __name__ == "__main__":
    main()
