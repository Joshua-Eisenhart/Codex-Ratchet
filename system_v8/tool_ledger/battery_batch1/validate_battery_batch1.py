#!/usr/bin/env python3
"""Fail-closed structural validator for the batch-1 tool integration receipt."""
from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
TOOLS = {
    "pykoopman": "pykoopman",
    "pydmd": "pydmd",
    "dynamiqs": "dynamiqs",
    "qutip_jax": "qutip_jax",
    "numpyro": "numpyro",
    "mctx": "mctx",
    "kingdon": "kingdon",
    "clifford": "clifford",
    "cvxpy": "cvxpy",
    "jax_verify": "jax_verify",
    "torchdiffeq": "torchdiffeq",
    "xgi": "xgi",
    "maude": "maude",
    "hypothesis": "hypothesis",
    "umap_learn": "umap_learn",
    "optuna": "optuna",
}
STATES = {"INTEGRATED", "BLOCKED", "PRUNED"}


def main() -> int:
    failures: list[str] = []
    summaries: dict[str, str] = {}
    for tool, stem in TOOLS.items():
        source = HERE / f"test_{tool}.py"
        result_path = HERE / "results" / f"{stem}.json"
        if not source.is_file():
            failures.append(f"missing test file: {source.name}")
            continue
        if not result_path.is_file():
            failures.append(f"missing result: {result_path.name}")
            continue
        try:
            result = json.loads(result_path.read_text())
        except Exception as exc:
            failures.append(f"invalid JSON {result_path.name}: {exc}")
            continue
        verdict = result.get("verdict")
        if verdict not in STATES:
            failures.append(f"{tool}: invalid verdict {verdict!r}")
        if result.get("promotion_allowed") is not False:
            failures.append(f"{tool}: promotion_allowed must be false")
        if not result.get("real_object"):
            failures.append(f"{tool}: missing real_object provenance")
        if verdict == "INTEGRATED" and result.get("computed_number") is None:
            failures.append(f"{tool}: integrated result lacks computed_number")
        if verdict == "BLOCKED" and not result.get("exact_error"):
            failures.append(f"{tool}: blocked result lacks exact_error")
        if verdict == "PRUNED" and not result.get("limitation"):
            failures.append(f"{tool}: pruned result lacks limitation")
        summaries[tool] = str(verdict)
    receipt = HERE / "receipt.json"
    if receipt.is_file():
        payload = json.loads(receipt.read_text())
        for tool, verdict in summaries.items():
            if payload.get("tools", {}).get(tool, {}).get("verdict") != verdict:
                failures.append(f"receipt verdict mismatch: {tool}")
    else:
        failures.append("missing consolidated receipt.json")
    output = {"all_pass": not failures, "checks": summaries, "failures": failures}
    print(json.dumps(output, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
