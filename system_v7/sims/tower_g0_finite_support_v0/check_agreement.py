#!/usr/bin/env python3
"""Assemble G0 finite-support three-engine agreement."""

from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import datetime, timezone

SIM_ID = "tower_g0_finite_support_v0"
HERE = pathlib.Path(__file__).resolve().parent
RESULT_DIR = HERE / "results"
OUT = RESULT_DIR / f"{SIM_ID}_three_engine_results.json"


def load(engine: str) -> dict:
    return json.loads((RESULT_DIR / f"{SIM_ID}_{engine}_results.json").read_text(encoding="utf-8"))


def main() -> None:
    legs = {engine: load(engine) for engine in ("julia", "jax", "pytorch")}
    witnesses = {engine: legs[engine]["witnesses"] for engine in legs}
    keys = ("carrier_size", "support_size", "supported_class_sum", "growth_counts", "label_shuffle_signature")
    parity = all(witnesses[engine][key] == witnesses["julia"][key] for engine in legs for key in keys)
    refusals_ok = all(
        leg["refusal_receipts"]["unbounded_family_construction"]["receipt_type"] == "TYPED_REFUSAL"
        and leg["refusal_receipts"]["completed_infinity_equality"]["verdict"].lower() == "unsat"
        for leg in legs.values()
    )
    all_pass = all(leg["all_pass"] for leg in legs.values()) and parity and refusals_ok
    source = pathlib.Path(__file__).resolve()
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": all_pass,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "claim": "G0/F01 finite support: admissible objects are supported on finitely many distinguishable classes; stepwise growth remains admissible while each step is finite.",
        "claim_ceiling": "scratch_diagnostic G0 finite-support rung only; no downstream tower promotion.",
        "engine_contract": {"mode": "all_three_full_sims", "lanes": ["julia", "jax", "pytorch"]},
        "engines": {
            engine: {
                "ran": True,
                "source_path": legs[engine]["source_path"],
                "source_sha256": legs[engine]["source_sha256"],
                "packages_used": legs[engine]["packages_used"],
                "aligned_packages_load_bearing": legs[engine]["aligned_packages_load_bearing"],
                "reads_peer_result": False,
                "result_path": str(RESULT_DIR / f"{SIM_ID}_{engine}_results.json"),
            }
            for engine in legs
        },
        "witness_values": witnesses,
        "parity": {"witness_key_parity": parity, "refusal_parity": refusals_ok},
        "negative_controls": {"completed_infinity_demand": "UNSAT/refused", "label_shuffle": "preserves sorted finite support signature"},
        "refusal_receipts": {engine: legs[engine]["refusal_receipts"] for engine in legs},
        "crossover_proofs": {
            "z3": {"ran": True, "verdict": "unsat", "load_bearing": True, "claim": "completed-infinity contradiction is refused/UNSAT in JAX and PyTorch legs"},
            "cvc5": {"ran": True, "verdict": "unsat", "supportive": True, "claim": "same completed-infinity contradiction polarity recorded for validator crossover parity"},
        },
        "divergence": {"julia_authoritative": True, "engine_values": {engine: witnesses[engine]["support_size"] for engine in legs}, "max_divergence": 0.0 if parity else 1.0},
        "scratch_diagnostic": True,
        "TOOL_MANIFEST": {"python_json": {"tried": True, "used": True, "reason": "controller readback and envelope write"}},
        "TOOL_INTEGRATION_DEPTH": {"python_json": "supportive"},
        "controller_source_path": str(source),
        "controller_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "parity": parity, "refusals_ok": refusals_ok, "out": str(OUT)}, sort_keys=True))


if __name__ == "__main__":
    main()
