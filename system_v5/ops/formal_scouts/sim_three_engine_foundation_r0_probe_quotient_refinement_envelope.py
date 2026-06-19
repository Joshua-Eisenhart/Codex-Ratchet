#!/usr/bin/env python3
"""Three-engine envelope for R0 probe quotient refinement.

The controller reads peer JSON only after the standalone lanes have produced
their local receipts.
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any


OBJECT_ID = "foundation_r0_probe_quotient_refinement_v1"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_three_engine_foundation_r0_probe_quotient_refinement_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/three_engine_foundation_r0_probe_quotient_refinement_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/foundation_r0_probe_quotient_refinement_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r0_probe_quotient_refinement_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r0_probe_quotient_refinement_pytorch_results.json"

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive controller-envelope readback and comparison after all engine lanes produced local JSON",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding for engine receipts",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "pathlib": "supportive",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compare_field(payloads: dict[str, dict[str, Any]], key: str) -> tuple[bool, dict[str, Any]]:
    values = {engine: payload.get(key) for engine, payload in payloads.items()}
    encoded = {engine: canonical_json(value) for engine, value in values.items()}
    return len(set(encoded.values())) == 1, values


def quotient_summary(payload: dict[str, Any]) -> dict[str, Any]:
    quotient = payload["quotient"]
    return {
        "empty_class_count": quotient["empty_probe"]["class_count"],
        "M_Z_class_count": quotient["M_Z"]["class_count"],
        "M_ZX_class_count": quotient["M_ZX"]["class_count"],
        "duplicate_Z_class_count": quotient["duplicate_Z_control"]["class_count"],
        "relabel_Z_class_count": quotient["relabel_Z_control"]["class_count"],
        "witness_same_Z": payload["witness_pair"]["same_under_Z"],
        "witness_distinct_X": payload["witness_pair"]["distinct_under_X"],
        "witness_same_Z_class": payload["witness_pair"]["same_Z_class"],
        "witness_split_ZX_class": payload["witness_pair"]["split_ZX_class"],
        "strict_refinement": payload["core_checks"]["strict_quotient_refinement"],
        "class_count_increase": payload["core_checks"]["z_to_zx_class_count_increase"],
    }


def engine_record(payload: dict[str, Any], result_path: Path, packages_used: list[str], load_bearing: list[str]) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "result_path": str(result_path),
        "reads_peer_result": payload.get("reads_peer_result"),
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "formal_admission_allowed": payload.get("formal_admission_allowed"),
        "all_pass": payload.get("all_pass"),
        "package_observables": payload.get("package_observables"),
        "quotient_summary": quotient_summary(payload),
    }


def max_summary_divergence(summaries: dict[str, dict[str, Any]]) -> float:
    numeric_keys = [
        "empty_class_count",
        "M_Z_class_count",
        "M_ZX_class_count",
        "duplicate_Z_class_count",
        "relabel_Z_class_count",
        "class_count_increase",
    ]
    max_diff = 0.0
    for key in numeric_keys:
        values = [float(summary[key]) for summary in summaries.values()]
        for idx, left in enumerate(values):
            for right in values[idx + 1 :]:
                max_diff = max(max_diff, abs(left - right))
    return max_diff


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    payloads = {"julia": julia, "jax": jax, "pytorch": pytorch}

    finite_support_match, finite_support_values = compare_field(payloads, "finite_support")
    probe_families_match, probe_family_values = compare_field(payloads, "probe_families")
    quotient_match, quotient_values = compare_field(payloads, "quotient")
    witness_match, witness_values = compare_field(payloads, "witness_pair")
    all_pass_by_engine = {engine: payload.get("all_pass") is True for engine, payload in payloads.items()}
    reads_peer_result_false = {engine: payload.get("reads_peer_result") is False for engine, payload in payloads.items()}
    flags = {
        engine: {
            "classification": payload.get("classification"),
            "promotion_allowed": payload.get("promotion_allowed"),
            "formal_admission_allowed": payload.get("formal_admission_allowed"),
        }
        for engine, payload in payloads.items()
    }
    flag_checks = {
        engine: (
            payload.get("classification") == CLASSIFICATION
            and payload.get("promotion_allowed") is False
            and payload.get("formal_admission_allowed") is False
        )
        for engine, payload in payloads.items()
    }
    summaries = {engine: quotient_summary(payload) for engine, payload in payloads.items()}
    max_divergence = max_summary_divergence(summaries)
    z3_verdict = jax["crossover_proofs"]["z3"]["verdict"]
    cvc5_verdict = jax["crossover_proofs"]["cvc5"]["verdict"]
    z3_details = jax["crossover_proofs"]["z3"]["details"]
    cvc5_details = jax["crossover_proofs"]["cvc5"]["details"]
    core_pass = (
        finite_support_match
        and probe_families_match
        and quotient_match
        and witness_match
        and all(all_pass_by_engine.values())
        and all(reads_peer_result_false.values())
        and all(flag_checks.values())
        and z3_verdict == cvc5_verdict == "unsat"
        and z3_details["duplicate_or_relabel_Z_distinguishes_negation"] == "unsat"
        and cvc5_details["duplicate_or_relabel_Z_distinguishes_negation"] == "unsat"
        and z3_details["invalid_negative_eigenvalue_psd_claim"] == "unsat"
        and cvc5_details["invalid_negative_eigenvalue_psd_claim"] == "unsat"
        and z3_details["invalid_trace_two_trace_one_claim"] == "unsat"
        and cvc5_details["invalid_trace_two_trace_one_claim"] == "unsat"
        and max_divergence == 0.0
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "schema": "codex_ratchet.three_engine_sim_result.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "engine": "envelope_controller",
        "executable": sys.executable,
        "active_preflight": {
            "python_executable": sys.executable,
            "engine_result_paths_exist": {
                "julia": JULIA_RESULT.exists(),
                "jax": JAX_RESULT.exists(),
                "pytorch": PYTORCH_RESULT.exists(),
            },
        },
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": True,
        "reads_peer_result_note": "Envelope/controller reads engine JSON only after all local lanes ran; engine lane reads_peer_result remains false.",
        "all_pass": core_pass,
        "core_pass": core_pass,
        "finite_support_match": finite_support_match,
        "probe_families_match": probe_families_match,
        "quotient_match": quotient_match,
        "witness_match": witness_match,
        "all_pass_by_engine": all_pass_by_engine,
        "reads_peer_result_false_by_engine": reads_peer_result_false,
        "classification_and_admission_flags": flags,
        "classification_and_admission_flags_ok": flag_checks,
        "finite_support_values": finite_support_values,
        "probe_family_values": probe_family_values,
        "quotient_values": quotient_values,
        "witness_values": witness_values,
        "finite_support": julia["finite_support"],
        "probe_families": julia["probe_families"],
        "quotient": julia["quotient"],
        "witness_pair": julia["witness_pair"],
        "negative_controls": {
            engine: payload["negative_controls"] for engine, payload in payloads.items()
        },
        "engine_result_paths": {
            "julia": str(JULIA_RESULT),
            "jax": str(JAX_RESULT),
            "pytorch": str(PYTORCH_RESULT),
        },
        "engines": {
            "julia": engine_record(
                julia,
                JULIA_RESULT,
                packages_used=["QuantumOptics", "LinearAlgebra", "JSON", "Dates"],
                load_bearing=["QuantumOptics"],
            ),
            "jax": engine_record(
                jax,
                JAX_RESULT,
                packages_used=["jax", "jax.numpy", "qutip", "z3", "cvc5"],
                load_bearing=["qutip", "z3", "cvc5"],
            ),
            "pytorch": engine_record(
                pytorch,
                PYTORCH_RESULT,
                packages_used=["torch", "torch.func"],
                load_bearing=["torch.func"],
            ),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_verdict,
                "claim": "Negating the |+>,|-> Z-indistinguishable/X-distinguishable witness is UNSAT.",
                "details": z3_details,
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "claim": "Independent cvc5 encoding of the same finite quotient/admissibility certificates.",
                "details": cvc5_details,
            },
            "julia_exact": {
                "ran": True,
                "load_bearing": True,
                "verdict": "checked",
                "claim": "Julia QuantumOptics/exact finite distributions give the same quotient refinement without reading peer results.",
            },
        },
        "claim_path_tools": ["QuantumOptics", "qutip", "z3", "cvc5", "torch.func", "torch", "jax", "jax.numpy"],
        "control_only_tools": [],
        "packages": {
            "load_bearing": ["QuantumOptics", "qutip", "z3", "cvc5", "torch.func"],
            "supportive": ["LinearAlgebra", "JSON", "Dates", "jax", "jax.numpy", "torch", "Python stdlib"],
            "control_only": [],
            "missing_required": [],
        },
        "package_observables": {
            "QuantumOptics": julia["package_observables"]["QuantumOptics"],
            "qutip": jax["package_observables"]["qutip"],
            "z3": jax["package_observables"]["z3"],
            "cvc5": jax["package_observables"]["cvc5"],
            "torch.func": "vmap batched probe distributions and jacrev differentiable probe observable in the PyTorch lane",
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": summaries,
            "max_divergence": max_divergence,
            "notes": [
                "Agreement is used only as envelope plumbing after independent local lane runs.",
                "The R0 claim path is the finite quotient refinement witness and solver/control checks, not cross-engine parity by itself.",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "R0 scratch_diagnostic probe-relative quotient refinement only: finite support qubit states under M_Z versus M_ZX. Not M(C), not R1/R2, not formal, not canonical, not bridge, not axis evidence.",
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"finite_support_match={str(result['finite_support_match']).lower()} "
        f"probe_families_match={str(result['probe_families_match']).lower()} "
        f"quotient_match={str(result['quotient_match']).lower()} "
        f"witness_match={str(result['witness_match']).lower()} "
        f"max_divergence={result['divergence']['max_divergence']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
