#!/usr/bin/env python3
"""Coherent envelope mutations must all be rejected by the independent validator."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable


SIM_DIR = Path(__file__).resolve().parent
ENVELOPE = SIM_DIR / "results" / "controller_envelope.json"
RESULT = SIM_DIR / "results" / "mutation_tests.json"
VALIDATOR = SIM_DIR / "validate_controller_envelope.py"


def mutate_source(payload: dict[str, Any]) -> None:
    payload["engines"]["jax"]["payload"]["source_sha256"] = "0" * 64


def mutate_proof(payload: dict[str, Any]) -> None:
    payload["engines"]["proof"]["payload"]["z3"]["queries"]["endpoint_negation_under_transitivity"] = "sat"


def mutate_drive(payload: dict[str, Any]) -> None:
    payload["drive"]["drive"] = 0


def mutate_decision(payload: dict[str, Any]) -> None:
    payload["decision"] = "HOLD"


def mutate_llm(payload: dict[str, Any]) -> None:
    payload["llm_verdict_used"] = True


def main() -> int:
    baseline = json.loads(ENVELOPE.read_text(encoding="utf-8"))
    cases: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        ("source_hash", mutate_source),
        ("proof_verdict", mutate_proof),
        ("drive", mutate_drive),
        ("decision", mutate_decision),
        ("llm_gate", mutate_llm),
    ]
    records = []
    with tempfile.TemporaryDirectory(prefix="ratchet-rung-mutations-") as temp:
        temp_dir = Path(temp)
        for name, mutation in cases:
            payload = copy.deepcopy(baseline)
            mutation(payload)
            path = temp_dir / f"{name}.json"
            path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-B", str(VALIDATOR), "--envelope", str(path)],
                cwd=SIM_DIR.parents[2],
                text=True,
                capture_output=True,
                check=False,
            )
            records.append(
                {
                    "case": name,
                    "validator_returncode": proc.returncode,
                    "rejected": proc.returncode != 0,
                    "stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest(),
                    "stderr": proc.stderr,
                }
            )
    all_pass = all(record["rejected"] for record in records)
    result = {
        "schema": "codex_ratchet.tolerance_to_equivalence.mutation_tests.v1",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve().relative_to(SIM_DIR.parents[2])),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "baseline_envelope_sha256": hashlib.sha256(ENVELOPE.read_bytes()).hexdigest(),
        "case_count": len(records),
        "cases": records,
        "all_pass": all_pass,
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"TOLERANCE_RUNG_MUTATIONS_DONE all_pass={str(all_pass).lower()} rejected={sum(r['rejected'] for r in records)}/{len(records)}")
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
