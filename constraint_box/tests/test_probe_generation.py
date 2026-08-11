from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from constraintbox.probe_generation import finite_problem_strategy, generate_receipt, mutate_one_field
from constraintbox.constraints import FiniteConstraintProblem
from constraintbox.probe_generation import flow_policy_strategy


def test_finite_problem_strategy_produces_real_cb_inputs() -> None:
    for _ in range(8):
        spec = finite_problem_strategy().example()
        problem = FiniteConstraintProblem.from_spec(spec)
        assert problem.state_count >= 1


def test_flow_policy_strategy_and_mutations_are_one_field() -> None:
    policy = flow_policy_strategy().example()
    for field, mutant in mutate_one_field(policy):
        changed = [name for name in policy.__dataclass_fields__ if getattr(policy, name) != getattr(mutant, name)]
        assert changed == ["transitions" if field.startswith("transitions[") else field]


def test_receipt_is_stable_and_contains_negative_pairs() -> None:
    first = json.dumps(generate_receipt(), sort_keys=True, separators=(",", ":")).encode()
    second = json.dumps(generate_receipt(), sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(first).hexdigest() == hashlib.sha256(second).hexdigest()
    receipt = json.loads(first)
    assert receipt["families"]["cb:sympy-exact-gate"]["boundary_pairs"]
    assert receipt["families"]["mini_levos.construction"]["boundary_pairs"]


def test_cli_receipt_has_no_wall_clock_and_is_replayable(tmp_path: Path) -> None:
    output = tmp_path / "receipt.json"
    cmd = [
        "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
        "-m",
        "constraintbox.probe_generation",
        "--write-receipt",
        str(output),
    ]
    subprocess.run(cmd, check=True)
    first = output.read_bytes()
    subprocess.run(cmd, check=True)
    second = output.read_bytes()
    assert hashlib.sha256(first).hexdigest() == hashlib.sha256(second).hexdigest()
    assert b"created_at" not in first
