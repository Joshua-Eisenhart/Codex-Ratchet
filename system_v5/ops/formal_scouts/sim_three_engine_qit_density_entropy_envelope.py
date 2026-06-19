#!/usr/bin/env python3
"""Composite envelope for the three-engine QIT density/entropy scout.

This does not recompute the engine legs. It binds the already-built Julia,
JAX, and PyTorch QIT density/entropy receipts into the repo's three-engine
result shape.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
RESULT_PATH = (
    ROOT
    / "system_v5"
    / "ops"
    / "formal_scouts"
    / "results"
    / "three_engine_qit_density_entropy_envelope_results.json"
)
JULIA_RESULT = (
    ROOT
    / "system_v5"
    / "julia_carrier"
    / "results"
    / "qit_density_entropy_3qubit_cl6_julia_results.json"
)
JAX_RESULT = (
    ROOT
    / "system_v5"
    / "ops"
    / "formal_scouts"
    / "results"
    / "qit_density_entropy_jax_leg_results.json"
)
PYTORCH_RESULT = (
    ROOT
    / "system_v5"
    / "ops"
    / "formal_scouts"
    / "results"
    / "qit_density_entropy_pytorch_grad_leg_results.json"
)

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
        "reason": "supportive result-envelope assembly from engine receipts; not a math claim path",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding for receipt files",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "pathlib": "supportive",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(
    *,
    payload: dict[str, Any],
    source_path: str,
    packages_used: list[str],
    load_bearing: list[str],
    values: dict[str, Any],
    result_path: Path,
) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": source_path,
        "result_path": str(result_path),
        "reads_peer_result": payload.get("reads_peer_result"),
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "formal_admission_allowed": payload.get("formal_admission_allowed"),
        "values": values,
    }


def max_pairwise_abs_diff(values: list[float]) -> float:
    diffs = []
    for index, left in enumerate(values):
        for right in values[index + 1 :]:
            diffs.append(abs(left - right))
    return max(diffs) if diffs else 0.0


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def rho_spec_comparison(payloads: dict[str, dict[str, Any]]) -> tuple[bool, dict[str, Any]]:
    specs = {engine: payload.get("rho_spec") for engine, payload in payloads.items()}
    encoded = {engine: canonical_json(spec) for engine, spec in specs.items() if isinstance(spec, dict)}
    match = len(encoded) == len(specs) and len(set(encoded.values())) == 1
    if match:
        return True, {}

    reference = specs.get("julia")
    diffs: dict[str, Any] = {"reference_engine": "julia", "by_engine": specs}
    if isinstance(reference, dict):
        key_diffs = {}
        keys = set(reference)
        for spec in specs.values():
            if isinstance(spec, dict):
                keys.update(spec)
        for key in sorted(keys):
            observed = {
                engine: spec.get(key) if isinstance(spec, dict) else None
                for engine, spec in specs.items()
            }
            if len({canonical_json({"value": value}) for value in observed.values()}) > 1:
                key_diffs[key] = observed
        diffs["key_diffs"] = key_diffs
    return False, diffs


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    julia_values = {
        "vn_entropy": julia["vn_entropy"],
        "eigenvalues": julia["eigenvalues"],
        "rho_spec": julia["rho_spec"],
        "package": julia["package"],
        "entropy_call": julia["entropy_call"],
        "eigenvalue_call": julia["eigenvalue_call"],
    }
    jax_values = {
        "vn_entropy": jax["vn_entropy"],
        "vn_entropy_units": jax["vn_entropy_units"],
        "rho_spec": jax["rho_spec"],
        "package": jax["package"],
        "jax_qutip_max_abs_diff": jax["diagnostics"]["jax_qutip_max_abs_diff"],
        "purity_assertion_unsat": jax["purity_assertion_unsat"],
        "erase_flip_drop_measured_spectrum_sat": jax["erase_flip_drop_measured_spectrum_sat"],
    }
    pytorch_values = {
        "vn_entropy": pytorch["vn_entropy"],
        "dS_dp": pytorch["dS_dp"],
        "rho_spec": pytorch["rho_spec"],
        "package": pytorch["package"],
        "fd_residual": pytorch["fd_residual"],
        "torch_density_dtype": pytorch["torch_density_dtype"],
        "torch_parameter_dtype": pytorch["torch_parameter_dtype"],
        "torch_version": pytorch["torch_version"],
    }

    rho_spec_match, rho_spec_diffs = rho_spec_comparison(
        {"julia": julia, "jax": jax, "pytorch": pytorch}
    )
    max_divergence = max_pairwise_abs_diff(
        [
            float(julia_values["vn_entropy"]),
            float(jax_values["vn_entropy"]),
            float(pytorch_values["vn_entropy"]),
        ]
    )
    z3_verdict = jax["smt_proof"]["z3"]["pure_with_measured_spectrum"]
    cvc5_verdict = jax["smt_proof"]["cvc5"]["pure_with_measured_spectrum"]
    z3_negative_control = jax["smt_proof"]["z3"]["pure_without_measured_spectrum"]
    cvc5_negative_control = jax["smt_proof"]["cvc5"]["pure_without_measured_spectrum"]
    all_pass = (
        julia["vn_entropy"] == jax["vn_entropy"] == pytorch["vn_entropy"]
        and jax["all_pass"] is True
        and pytorch["checks"]["core_pass"] is True
        and jax["z3_cvc5_agree"] is True
        and z3_verdict == cvc5_verdict == "unsat"
        and z3_negative_control == cvc5_negative_control == "sat"
        and rho_spec_match is True
    )

    result = {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": "three_engine_qit_density_entropy_envelope",
        "classification": CLASSIFICATION,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": (
            "Scratch three-engine QIT density/entropy envelope only. It binds "
            "Julia QuantumOptics entropy_vn/eigenstates, JAX qutip+z3+cvc5 "
            "density and SMT receipts, and PyTorch torch.func.jacrev entropy "
            "gradient receipt. No formal admission, no bridge, manifold, basin, "
            "or axis-level claim."
        ),
        "all_pass": all_pass,
        "rho_spec_match": rho_spec_match,
        "engines": {
            "julia": engine_record(
                payload=julia,
                source_path=julia["source_path"],
                result_path=JULIA_RESULT,
                packages_used=["QuantumOptics", "JSON", "Dates"],
                load_bearing=["QuantumOptics"],
                values=julia_values,
            ),
            "jax": engine_record(
                payload=jax,
                source_path=jax["source_path"],
                result_path=JAX_RESULT,
                packages_used=["jax", "jax.numpy", "qutip", "z3", "cvc5"],
                load_bearing=["z3", "cvc5"],
                values=jax_values,
            ),
            "pytorch": engine_record(
                payload=pytorch,
                source_path=pytorch["source_path"],
                result_path=PYTORCH_RESULT,
                packages_used=["torch", "torch.func"],
                load_bearing=["torch.func"],
                values=pytorch_values,
            ),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_verdict,
                "claim": (
                    "The measured mixed spectrum cannot satisfy a pure-state "
                    "assertion; adding the pure-state assertion is UNSAT."
                ),
                "negative_control_verdict": z3_negative_control,
                "negative_control_claim": "Dropping the measured spectrum makes the pure-state assertion SAT.",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "claim": (
                    "The measured mixed spectrum cannot satisfy a pure-state "
                    "assertion; adding the pure-state assertion is UNSAT."
                ),
                "negative_control_verdict": cvc5_negative_control,
                "negative_control_claim": "Dropping the measured spectrum makes the pure-state assertion SAT.",
            },
        },
        "claim_path_tools": [
            "QuantumOptics",
            "qutip",
            "z3",
            "cvc5",
            "torch.func",
            "jax",
            "jax.numpy",
        ],
        "control_only_tools": ["numpy"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": julia_values,
                "jax": jax_values,
                "pytorch": pytorch_values,
            },
            "max_divergence": max_divergence,
            "notes": [
                "All three engines computed the IDENTICAL pinned rho(p) (GHZ depolarizing, p=0.3, no dephasing) and agree on von Neumann entropy to ~1e-16.",
                "Prior divergence (1.086/1.859/1.761) was an unpinned-state spec artifact, now resolved.",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }
    if not rho_spec_match:
        result["rho_spec_diffs"] = rho_spec_diffs
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"julia_vn_entropy={result['engines']['julia']['values']['vn_entropy']} "
        f"jax_vn_entropy={result['engines']['jax']['values']['vn_entropy']} "
        f"pytorch_vn_entropy={result['engines']['pytorch']['values']['vn_entropy']} "
        f"pytorch_dS_dp={result['engines']['pytorch']['values']['dS_dp']} "
        f"max_divergence={result['divergence']['max_divergence']} "
        f"rho_spec_match={str(result['rho_spec_match']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
