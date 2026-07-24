#!/usr/bin/env python3
"""Convert flip-battery measurements into a Lev sim-witness TRACE fixture.

Generated, never hand-authored, so the fixture cannot drift from the run that
produced it. Lane statuses stay 'non_authoritative_input' and no lane carries a
verdict — the scorer decides.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "results" / "flip_harness_v0.json"
OUT = HERE / "fixtures" / "flip_evidence.trace.json"
SUBJECT = "codex-ratchet:system_v8/harness_patch/flip_harness.py"


def fnv1a32(data: bytes) -> str:
    h = 0x811C9DC5
    for b in data:
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"


def facts_for(entry: dict) -> list[dict]:
    return [
        {"name": "label", "value": entry["label"]},
        {"name": "flip_rate", "value": entry["test_2_perturb"]["flip_rate"]},
        {"name": "n_perturbations", "value": entry["test_2_perturb"]["n_perturbations"]},
        {"name": "erase_flips", "value": entry["test_1_erase"]["erase_flips"]},
        {"name": "smt_real", "value": entry["test_1_erase"]["real"]},
        {"name": "smt_erased", "value": entry["test_1_erase"]["erased"]},
        {"name": "unsat_core_size", "value": entry["test_3_core"]["unsat_core_size"]},
        {"name": "n_pinned", "value": entry["test_3_core"]["n_pinned"]},
        {"name": "core_is_subset", "value": entry["test_3_core"]["core_is_subset"]},
    ]


def lane(lane_id: str, entry: dict, generation: int) -> dict:
    facts = facts_for(entry)
    body = json.dumps({"lane": lane_id, "facts": facts}, sort_keys=True,
                      separators=(",", ":")).encode()
    return {
        "schema": "lev.sim_witness.provider_evidence.v1",
        "lane_id": lane_id,
        # allowed status: NOT one of evaluated/pass/fail/not_evaluated
        "status": "non_authoritative_input",
        "subject_ref": SUBJECT,
        "generation": generation,
        "content_address": f"sim-witness:fnv1a32:{fnv1a32(body)}",
        "refs": [{"kind": "codex_ratchet_result_json", "ref": str(SRC)}],
        "facts": facts,
    }


def main() -> int:
    src = json.loads(SRC.read_text())
    results = src["results"]
    real = next(r for r in results if not r["label"].startswith("NEGATIVE"))
    ctrl = next(r for r in results if r["label"].startswith("NEGATIVE"))

    trace = {
        "schema": "lev.claimgate_flip_battery.trace.v1",
        "subject_ref": SUBJECT,
        "observable_name": "flip_rate",
        "tolerance": 0,
        "claim_under_test": src["claim_under_test"],
        "llm_tokens_spent": src["llm_tokens_spent"],
        "provider_evidence": [
            # JAX batches the perturbation instances; z3 decides each one.
            lane("sim.jax", real, 1),
            lane("proof.smt", real, 1),
            lane("proof.smt", ctrl, 2),
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(trace, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(HERE.parent.parent.parent)} "
          f"({len(trace['provider_evidence'])} lanes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
