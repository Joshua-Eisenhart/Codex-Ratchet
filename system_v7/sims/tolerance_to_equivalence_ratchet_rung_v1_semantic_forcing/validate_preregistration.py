#!/usr/bin/env python3
"""Fail-closed structural and semantic preregistration validator."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from generate_facts import generate
from oracle import Instance, evaluate


HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> list[str]:
    errors: list[str] = []
    spec = json.loads((HERE / "spec.json").read_text(encoding="utf-8"))
    mutations = json.loads((HERE / "mutations.json").read_text(encoding="utf-8"))
    for key in (
        "promotion_allowed",
        "formal_admission_allowed",
        "official_launch_allowed",
        "llm_verdict_allowed",
    ):
        if spec.get(key) is not False:
            errors.append(f"{key} must remain false")
    gates = spec.get("code_gates")
    if not isinstance(gates, list) or len(gates) != 13:
        errors.append("P0-P12 gate vector must contain exactly 13 entries")
    elif [str(row).split()[0] for row in gates] != [f"P{i}" for i in range(13)]:
        errors.append("P0-P12 gate labels are not ordered and complete")
    for relative in spec.get("builder_paths", []):
        if (HERE / relative).exists():
            errors.append(f"builder path must be absent at preregistration: {relative}")
    generator_path = HERE / "generate_facts.py"
    tree = ast.parse(generator_path.read_text(encoding="utf-8"))
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    if any(name == "oracle" or name.endswith(".oracle") for name in imported):
        errors.append("fact generator imports the decision oracle")
    forbidden_keys = {
        "expected",
        "expected_decision",
        "decision",
        "target_rung",
        "preferred_proposal",
        "proposal",
    }
    for seed, n in ((1, 4), (7, 6), (19, 8)):
        payload = generate(seed, n)
        if forbidden_keys & set(payload):
            errors.append(f"fact generator leaked answer fields for seed={seed}")
        try:
            Instance.from_payload(payload)
        except ValueError as error:
            errors.append(f"generated instance invalid for seed={seed}: {error}")
    unique = {
        "n": 4,
        "tolerance_edges": [[0, 1], [2, 3]],
        "current_labels": [0, 0, 0, 0],
        "demand": [{"pair": [1, 2], "weight": 1}],
    }
    plural = {
        "n": 4,
        "tolerance_edges": [],
        "current_labels": [0, 0, 0, 0],
        "demand": [{"pair": [0, 1], "weight": 1}],
    }
    flat = {
        "n": 4,
        "tolerance_edges": [[0, 1], [2, 3]],
        "current_labels": [0, 0, 1, 1],
        "demand": [{"pair": [1, 2], "weight": 1}],
    }
    expected = (
        (evaluate(unique)["decision"], "COMMIT"),
        (evaluate(plural)["decision"], "HOLD_MSS_AMBIGUOUS"),
        (evaluate(flat)["decision"], "HOLD_NONPOSITIVE"),
    )
    for observed, wanted in expected:
        if observed != wanted:
            errors.append(f"oracle semantic vector mismatch: {observed} != {wanted}")
    required_mutations = mutations.get("required_mutations")
    if (
        mutations.get("coherent_regeneration_required") is not True
        or mutations.get("envelope_only_mutation_insufficient") is not True
        or not isinstance(required_mutations, list)
        or len(required_mutations) < 12
    ):
        errors.append("semantic mutation contract is incomplete")
    return errors


def main() -> int:
    errors = validate()
    receipt = {
        "schema": "codex_ratchet.tolerance_to_equivalence_v1.preregistration_validation.v1",
        "ok": not errors,
        "errors": errors,
        "spec_sha256": sha256(HERE / "spec.json"),
        "generator_sha256": sha256(HERE / "generate_facts.py"),
        "oracle_sha256": sha256(HERE / "oracle.py"),
        "mutations_sha256": sha256(HERE / "mutations.json"),
        "builder_paths_absent": all(
            not (HERE / path).exists()
            for path in json.loads((HERE / "spec.json").read_text())["builder_paths"]
        ),
        "claim_ceiling": "preregistration and reference oracle only; no engine builders or tooth",
    }
    print(json.dumps(receipt, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
