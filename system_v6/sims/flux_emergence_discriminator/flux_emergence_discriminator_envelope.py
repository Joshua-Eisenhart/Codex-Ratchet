#!/usr/bin/env python3
"""Envelope for the flux emergence discriminator."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "flux_emergence_discriminator"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOL = 5.0e-6

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from independent Julia/JAX/PyTorch receipts",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding for the v6 packet files",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source hashing",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive", "hashlib": "supportive"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "standard_labels": payload["standard_labels"],
        "max_errors": payload["max_errors"],
    }


def compare_shared_scalars(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    key_sets = {engine: set(payload["shared_scalars"].keys()) for engine, payload in payloads.items()}
    common = sorted(set.intersection(*key_sets.values()))
    same_sets = all(keys == key_sets["julia"] for keys in key_sets.values())
    union = set.union(*key_sets.values())
    rows = []
    max_divergence = 0.0
    max_key = None
    for key in common:
        values = {engine: float(payload["shared_scalars"][key]) for engine, payload in payloads.items()}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_divergence:
            max_divergence = diff
            max_key = key
    return {
        "same_named_observable_sets": same_sets,
        "common_observable_count": len(common),
        "missing_by_engine": {engine: sorted(union - keys) for engine, keys in key_sets.items()},
        "rows": rows,
        "max_divergence": max_divergence,
        "max_divergence_key": max_key,
        "within_tolerance": same_sets and max_divergence <= TOL,
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def report_tables(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    julia = payloads["julia"]
    jax = payloads["jax"]
    return {
        "h_k_table": [
            {
                "k": row["shell"],
                "eta": row["eta"],
                "h_transport": row["accumulated_phase"],
                "h_mod_2pi": row["accumulated_phase_mod_2pi"],
                "closed_form_target": row["closed_form_target"],
                "mod_error": row["mod_error"],
            }
            for row in julia["shell_holonomy"]
        ],
        "Phi_pairs": [
            {
                "pair": row["pair"],
                "transport": row["transport_h_difference"],
                "quadrature_stokes_oriented": row["quadrature_stokes_oriented"],
                "closed_form_target": row["closed_form_target"],
                "transport_vs_quadrature_error": row["transport_vs_quadrature_error"],
            }
            for row in julia["inter_shell_flux"]
        ],
        "chern": julia["chern"],
        "ablations": julia["ablations"],
        "co_variation": julia["ratchet_coupling"],
        "smt_verdicts": {
            "z3": jax["smt"]["z3"]["verdict"],
            "cvc5": jax["smt"]["cvc5"]["verdict"],
            "julia_z3": julia["smt"]["julia_z3"]["verdict"],
            "single_shell": {
                "z3": jax["smt"]["z3"]["single_shell_verdict"],
                "cvc5": jax["smt"]["cvc5"]["single_shell_verdict"],
                "julia_z3": julia["smt"]["julia_z3"]["single_shell_verdict"],
            },
        },
    }


def build_result() -> dict[str, Any]:
    payloads = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    comparison = compare_shared_scalars(payloads)
    report = report_tables(payloads)
    jax_z3 = payloads["jax"]["smt"]["z3"]
    jax_cvc5 = payloads["jax"]["smt"]["cvc5"]
    julia_z3 = payloads["julia"]["smt"]["julia_z3"]
    controls = {
        "legs_all_pass": all(payload["all_pass"] is True for payload in payloads.values()),
        "classification_ceiling_held": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is False
            and payload["formal_admission_allowed"] is False
            for payload in payloads.values()
        ),
        "shared_scalars_within_tolerance": comparison["within_tolerance"],
        "all_engines_no_peer_reads": all(payload["reads_peer_result"] is False for payload in payloads.values()),
        "holonomy_errors_bounded": all(payload["max_errors"]["holonomy_mod_error"] <= TOL for payload in payloads.values()),
        "flux_stokes_errors_bounded": all(
            payload["max_errors"]["transport_vs_quadrature_flux_error"] <= TOL for payload in payloads.values()
        ),
        "chern_abs_errors_bounded": all(payload["max_errors"]["chern_abs_error"] <= TOL for payload in payloads.values()),
        "bare_spinor_kills_flux": all(payload["ablations"]["bare_spinor"]["pass"] is True for payload in payloads.values()),
        "single_shell_separates_h_from_flux": all(payload["ablations"]["single_shell"]["pass"] is True for payload in payloads.values()),
        "ratchet_scramble_changes_flux_not_chern": all(
            payload["ablations"]["ratchet_scramble"]["sign_pattern_changed"] is True
            and payload["ablations"]["ratchet_scramble"]["topology_indifferent_to_order"] is True
            for payload in payloads.values()
        ),
        "smt_additivity_unsat": jax_z3["verdict"] == jax_cvc5["verdict"] == julia_z3["verdict"] == "unsat",
        "smt_single_shell_unsat": jax_z3["single_shell_verdict"]
        == jax_cvc5["single_shell_verdict"]
        == julia_z3["single_shell_verdict"]
        == "unsat",
        "candidate_correlation_positive": all(
            payload["ratchet_coupling"]["correlation_across_3_rungs"] > 0.0 for payload in payloads.values()
        ),
        "no_numpy_claim_path": "numpy" not in collect_claim_tools(payloads),
    }
    all_pass = bool(all(controls.values()))
    return {
        "schema_version": "three_engine_sim_result_v1",
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "reads_peer_result": False,
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "object_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "all_pass": all_pass,
        "claim_ceiling": "scratch_diagnostic only; promotion_allowed=false; flux remains a CANDIDATE FAMILY per weyl-flux.md. This tests the curvature member's emergence conditions and does not select a family winner or close any axis/bridge.",
        "pin_spec": payloads["julia"]["pin_spec"],
        "standard_labels": {
            "pin": "eta shells, loop grammar, and curvature member fixed",
            "like_for_like": True,
            "no_numpy_claim_path": True,
            "capability_backed": True,
        },
        "engines": {
            "julia": engine_record(payloads["julia"], JULIA_RESULT),
            "jax": engine_record(payloads["jax"], JAX_RESULT),
            "pytorch": engine_record(payloads["pytorch"], PYTORCH_RESULT),
        },
        "report": report,
        "shell_holonomy_by_engine": {engine: payload["shell_holonomy"] for engine, payload in payloads.items()},
        "inter_shell_flux_by_engine": {engine: payload["inter_shell_flux"] for engine, payload in payloads.items()},
        "chern_by_engine": {engine: payload["chern"] for engine, payload in payloads.items()},
        "ablations_by_engine": {engine: payload["ablations"] for engine, payload in payloads.items()},
        "ratchet_coupling_by_engine": {engine: payload["ratchet_coupling"] for engine, payload in payloads.items()},
        "smt_by_engine": {engine: payload["smt"] for engine, payload in payloads.items()},
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": jax_z3["verdict"],
                "single_shell_verdict": jax_z3["single_shell_verdict"],
                "bound_scaled_cos_values": jax_z3["bound_scaled_cos_values"],
                "scale": jax_z3["scale"],
                "derived_expression": jax_z3["derived_expression"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": jax_cvc5["verdict"],
                "single_shell_verdict": jax_cvc5["single_shell_verdict"],
                "bound_scaled_cos_values": jax_cvc5["bound_scaled_cos_values"],
                "scale": jax_cvc5["scale"],
                "derived_expression": jax_cvc5["derived_expression"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia_z3["verdict"],
                "single_shell_verdict": julia_z3["single_shell_verdict"],
                "bound_scaled_cos_values": julia_z3["bound_scaled_cos_values"],
                "scale": julia_z3["scale"],
                "derived_expression": julia_z3["derived_expression"],
            },
        },
        "claim_path_tools": collect_claim_tools(payloads),
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {engine: payload["shared_scalars"] for engine, payload in payloads.items()},
            "comparison": comparison,
            "max_divergence": comparison["max_divergence"],
            "max_divergence_key": comparison["max_divergence_key"],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "controls": controls,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "envelope": str(RESULT_PATH),
                "all_pass": result["all_pass"],
                "max_divergence": result["divergence"]["max_divergence"],
                "max_divergence_key": result["divergence"]["max_divergence_key"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
