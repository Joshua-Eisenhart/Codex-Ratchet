#!/usr/bin/env python3
"""Controller envelope for entropy_type_ratchet_v0."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

from entropy_type_ratchet_v0_common import (
    RESULT_DIR,
    ROOT,
    SIM_ID,
    base_leg_payload,
    build_table,
    parent_lineage,
    rel,
    sha256_file,
    stable_hash,
    write_json,
)

sys.path.insert(0, str(ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402

SOURCE = Path(__file__).resolve()
RESULT = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
ENGINES = ["julia", "jax", "pytorch"]


def load_leg(engine: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{SIM_ID}_{engine}_results.json"
    return json.loads(path.read_text(encoding="utf-8"))


def lane_record(leg: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_path": leg["source_path"],
        "result_path": leg["result_path"],
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "package_observables": leg["package_observables"],
        "role_id": leg["role_id"],
        "all_pass": leg["all_pass"],
        "claim_path_tools": leg["claim_path_tools"],
        "tool_calls": leg["tool_calls"],
    }


def max_delta(values: list[float]) -> float:
    return max(values) - min(values)


def build_result() -> dict[str, Any]:
    legs = {engine: load_leg(engine) for engine in ENGINES}
    table = legs["jax"]["type_admissibility_table"]
    local_table = build_table()
    final_type_count = {
        engine: int(legs[engine]["engine_values"]["final_available_type_count"])
        for engine in ENGINES
    }
    rho_entropy = {
        engine: float(legs[engine]["engine_values"]["rho_entropy_nats"])
        for engine in ENGINES
    }
    z3 = legs["jax"]["crossover_proofs"]["z3"]
    cvc5 = legs["jax"]["crossover_proofs"]["cvc5"]
    julia_z3 = legs["julia"]["crossover_proofs"]["julia_z3"]
    controls = legs["jax"]["controls"]
    all_pass = all(
        [
            all(leg["all_pass"] for leg in legs.values()),
            stable_hash(table) == stable_hash(local_table),
            len(table["rows"]) == 9,
            final_type_count == {"julia": 6, "jax": 6, "pytorch": 6},
            max_delta(list(rho_entropy.values())) <= 1.0e-10,
            z3["verdict"] == "unsat",
            cvc5["verdict"] == "unsat",
            julia_z3["verdict"] == "unsat",
            z3["perturbed_availability_entry_verdict"] == "sat",
            cvc5["perturbed_availability_entry_verdict"] == "sat",
            julia_z3["perturbed_availability_entry_verdict"] == "sat",
            all(row["pass"] for row in controls["premature_evaluation"].values()),
            controls["type_confusion"]["pass"],
            controls["order_shuffle"]["pass"],
            controls["degenerate_flag"]["pass"],
        ]
    )
    lanes = {engine: lane_record(legs[engine]) for engine in ENGINES}
    extra_fields = {
        "schema": f"{SIM_ID}_envelope_v1",
        "source_path": rel(SOURCE),
        "source_sha256": sha256_file(SOURCE),
        "result_path": rel(RESULT),
        "all_pass": all_pass,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim": "the admissible entropy/information type set and admissible operator families co-ratchet over the committed sequence",
        "allowed_claims": [
            "per-step type-admissibility table over the named committed sequence",
            "named missing-structure failures for premature evaluations",
            "order-sensitive availability witness for two permuted orders",
            "operator family co-variation witnessed by packet-local applications or named failures",
        ],
        "disallowed_claims": [
            "formal admission",
            "universal entropy scalar",
            "physics or bridge theorem",
            "higher-stage promotion beyond scratch_diagnostic",
        ],
        "type_admissibility_table": table,
        "per_step_type_admissibility_table": table["rows"],
        "availability_sequence": table["availability_sequence"],
        "named_change_steps": table["change_steps"],
        "controls": controls,
        "positive_section": {
            "final_available_types": table["availability_sequence"][-1]["available_types"],
            "operator_co_ratchet_final": table["rows"][-1]["operator_co_ratchet"],
            "rho_entropy_nats": rho_entropy,
        },
        "negative_section": {
            "premature_evaluation": controls["premature_evaluation"],
            "type_confusion": controls["type_confusion"],
            "order_shuffle": controls["order_shuffle"],
        },
        "boundary_section": {
            "degenerate_flag": controls["degenerate_flag"],
            "chart_measure_zero_denominator_boundary": "band-limit convention is required before chart-uniform differential entropy",
        },
        "typed_entropy_discipline": {
            "log_base": "e",
            "labels_carried_from_manifold_entropy_ledger_v0": True,
            "cross_type_sum_without_convention": "rejected",
            "signed_lens_delta_convention": "lens/deep finite quotient deltas remain signed drops; values are not added across entropy types without a declared product convention",
        },
        "operator_co_ratchet": [row["operator_co_ratchet"] for row in table["rows"]],
        "TOOL_INTENT_MATRIX": {
            "julia": legs["julia"]["package_observables"],
            "jax": legs["jax"]["package_observables"],
            "pytorch": legs["pytorch"]["package_observables"],
        },
        "tool_intent": {
            "claim_classes": ["type_admissibility_table", "entropy_type_failures", "operator_co_ratchet"],
            "engine_tool_intent": {
                "julia": legs["julia"]["package_observables"],
                "jax": legs["jax"]["package_observables"],
                "pytorch": legs["pytorch"]["package_observables"],
            },
        },
        "TOOL_MANIFEST": {
            "build_three_engine_envelope": {"used": True, "tried": True, "reason": "load-bearing standard envelope construction"},
            "json": {"used": True, "tried": True, "reason": "supportive deterministic serialization"},
            "hashlib": {"used": True, "tried": True, "reason": "supportive source and table hashes"},
        },
        "TOOL_INTEGRATION_DEPTH": {"build_three_engine_envelope": "load_bearing", "json": "supportive", "hashlib": "supportive"},
        "tool_calls": legs["jax"]["tool_calls"] + legs["julia"]["tool_calls"] + legs["pytorch"]["tool_calls"],
        "validator_expected_commands": [
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/entropy_type_ratchet_v0/entropy_type_ratchet_v0_jax.py",
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/entropy_type_ratchet_v0/entropy_type_ratchet_v0_julia.jl",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/entropy_type_ratchet_v0/entropy_type_ratchet_v0_pytorch.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/entropy_type_ratchet_v0/entropy_type_ratchet_v0_envelope.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/entropy_type_ratchet_v0/validate_entropy_type_ratchet_v0.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/entropy_type_ratchet_v0/results/entropy_type_ratchet_v0_envelope_results.json",
        ],
        "table_hash": stable_hash(table),
    }
    envelope = build_envelope(
        sim_id=SIM_ID,
        lanes=lanes,
        mode="all_three_full_sims",
        claim_path_tools=["QuantumOptics", "Z3", "z3", "cvc5", "sympy", "torch_geometric", "torch.func"],
        crossover_proofs={"z3": z3, "cvc5": cvc5, "julia_z3": julia_z3},
        divergence={
            "julia_authoritative": True,
            "engine_values": {
                "julia": {"final_available_type_count": final_type_count["julia"], "rho_entropy_nats": rho_entropy["julia"]},
                "jax": {"final_available_type_count": final_type_count["jax"], "rho_entropy_nats": rho_entropy["jax"]},
                "pytorch": {"final_available_type_count": final_type_count["pytorch"], "rho_entropy_nats": rho_entropy["pytorch"]},
            },
            "max_divergence": max_delta(list(rho_entropy.values())),
            "observable": "rho_entropy_nats_and_final_type_count",
        },
        parent_lineage=parent_lineage(),
        extra_fields=extra_fields,
    )
    return envelope


def main() -> int:
    payload = build_result()
    write_json(RESULT, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": str(RESULT)}, indent=2))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
