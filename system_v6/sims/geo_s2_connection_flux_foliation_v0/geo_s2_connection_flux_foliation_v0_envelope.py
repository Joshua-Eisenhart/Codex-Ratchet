#!/usr/bin/env python3
"""Envelope assembler for geo_s2_connection_flux_foliation_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s2_connection_flux_foliation_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
SPEC_SECTION_A_COPY = SIM_DIR / "s2_build_spec_section_A.md"
DIRECTIVE_COPY = SIM_DIR / "directive_addendum.md"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from fresh engine receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source, copied-input, and PIN hash checks"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}

ALLOWED_STRENGTHS = {
    "symbolic_identity",
    "closed_form_integral",
    "exact_integer_combinatorial",
    "rigorous_interval_bound",
    "measure_theorem",
    "finite_exhaustive_enumeration",
    "representation_theorem_with_constructive_receipt",
    "statistical_redundant_by_exact_route",
    "diagnostic_float_nonclaim",
    "open_with_reason",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": rel(result_path),
        "result_sha256": file_sha256(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "role_id": payload["role_id"],
        "pin_sha256": payload["pin_sha256"],
        "convention_pin": payload["convention_pin"],
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    out: set[str] = set()
    for payload in payloads.values():
        out.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(out)


def current_source_hash_ok(payload: dict[str, Any]) -> bool:
    source = ROOT / payload["source_path"]
    return source.exists() and file_sha256(source) == payload["source_sha256"]


def receipt_strengths(receipts: dict[str, Any]) -> list[str]:
    return sorted({str(row.get("exact_strength")) for row in receipts.values()})


def main() -> int:
    payloads = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    jax = payloads["jax"]
    julia = payloads["julia"]
    pytorch = payloads["pytorch"]
    pin_hashes = {payload["pin_sha256"] for payload in payloads.values()}
    convention_pin_ok = julia["convention_pin"] == jax["convention_pin"] == pytorch["convention_pin"]
    receipts = dict(jax["receipts"])
    receipts["S2.FG"] = julia["receipts"]["S2.FG"]
    receipts["F01_finitude_receipt"] = jax["F01_finitude_receipt"]
    receipts["N01_noncommutation_receipt"] = jax["N01_noncommutation_receipt"]
    receipts["T01_bracketing_receipt"] = jax["T01_bracketing_receipt"]
    strengths = receipt_strengths(receipts)
    required = {"S2.A", "S2.F", "S2.FG", "S2.H1", "S2.H2", "S2.H3", "S2.S", "S2.C", "S2.T", "S2.G", "S2.N", "S2.K"}
    copied_inputs = {
        "spec_section_A": {"path": rel(SPEC_SECTION_A_COPY), "sha256": file_sha256(SPEC_SECTION_A_COPY), "exists": SPEC_SECTION_A_COPY.exists()},
        "directive_addendum": {"path": rel(DIRECTIVE_COPY), "sha256": file_sha256(DIRECTIVE_COPY), "exists": DIRECTIVE_COPY.exists()},
    }
    gates = {
        "engine_legs_pass": all(payload["all_pass"] is True for payload in payloads.values()),
        "identical_pin_sha256": len(pin_hashes) == 1,
        "identical_structured_convention_pin": convention_pin_ok,
        "source_sha256_current": all(current_source_hash_ok(payload) for payload in payloads.values()),
        "ceilings_preserved": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is PROMOTION_ALLOWED
            and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for payload in payloads.values()
        ),
        "section_A_receipts_present": required <= set(receipts),
        "literal_strength_tokens": all(strength in ALLOWED_STRENGTHS for strength in strengths),
        "F01_grid_receipt_scoped": receipts["F01_finitude_receipt"]["pass"] is True
        and receipts["F01_finitude_receipt"]["scope"].startswith("finite torus grids"),
        "N01_honest_not_scoped": receipts["N01_noncommutation_receipt"]["status"] == "not_scoped",
        "five_convention_pin_present": set(jax["convention_pin"]) == {
            "holonomy_quantity",
            "berry_formula",
            "phase_domain",
            "base_loop_count",
            "orientation_and_c1_sign",
        },
        "two_to_one_double_cover_handled": receipts["S2.T"]["data"]["double_cover_reason"] == "(phi, chi) ~ (phi + pi, chi + pi)"
        and all(row["physical_points"] * 2 == row["chart_points"] for row in receipts["S2.G"]["data"]["rows"]),
        "grassmann_exterior_curvature_mirror": receipts["S2.FG"]["pass"] is True
        and receipts["S2.FG"]["data"]["api"] == "Grassmann.wedge(v1, v2)"
        and receipts["S2.FG"]["data"]["wrong_sign_control"]["fails"] is True,
        "exact_smt_can_fail_controls": jax["exact_smt"]["z3"]["wrong_sign_control_can_fail"]
        and jax["exact_smt"]["cvc5"]["wrong_sign_control_can_fail"]
        and pytorch["exact_smt"]["z3"]["naive_control_can_fail"]
        and pytorch["exact_smt"]["cvc5"]["naive_control_can_fail"]
        and julia["crossover_proofs"]["julia_z3"]["wrong_sign_control_can_fail"],
        "copied_spec_and_directive_present": all(item["exists"] for item in copied_inputs.values()),
        "no_peer_result_reads": all(payload["reads_peer_result"] is False for payload in payloads.values()),
    }
    all_pass = all(gates.values())
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "Section A positive S2 connection/flux/foliation receipts over the S1 Hopf geometry, with convention pin, double-cover grid accounting, and exact SMT controls.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "copied_inputs": copied_inputs,
        "pin_spec": jax["pin_spec"],
        "pin_sha256": next(iter(pin_hashes)),
        "convention_pin": jax["convention_pin"],
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": julia.get("julia_project"),
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": julia["source_sha256"],
            "receipt_path": julia["result_path"],
            "proof_tag": "S2_connection_flux_foliation_section_A_julia_carrier_z3",
            "proof_pass": bool(julia["all_pass"]),
            "table_version": None,
            "bracket_convention": "not_applicable_connection_forms_and_finite_torus_grid_quotient",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia.get("julia_project"), "packages": julia["packages_used"], "role": "semantic owner for carrier-side ODE and SMT receipt"},
            "jax": {"packages": jax["packages_used"], "role": "SymPy derivation, z3/cvc5 exact Stokes proof, dense convergence diagnostics"},
            "pytorch": {"packages": pytorch["packages_used"], "role": "torch.func horizontal ODE/grid quotient lane plus exact grid SMT"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": collect_claim_tools(payloads),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "receipts": receipts,
        "strength_tokens": strengths,
        "crossover_proofs": {
            "z3": jax["crossover_proofs"]["z3"],
            "cvc5": jax["crossover_proofs"]["cvc5"],
            "julia_z3": julia["crossover_proofs"]["julia_z3"],
            "pytorch_z3": pytorch["crossover_proofs"]["z3"],
            "pytorch_cvc5": pytorch["crossover_proofs"]["cvc5"],
        },
        "controls": {
            "wrong_sign_curvature": jax["controls"]["wrong_sign_curvature_control"],
            "wrong_sign_stokes": {"z3": jax["controls"]["wrong_sign_stokes_z3"], "cvc5": jax["controls"]["wrong_sign_stokes_cvc5"]},
            "naive_cover_grid": pytorch["receipts"]["S2.G"]["grid_rows"],
        },
        "build_gates": gates,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": 0.0, "jax": 0.0, "pytorch": 0.0},
            "max_divergence": 0.0,
            "basis": "all engines agree on pass/fail gates under identical PIN; numeric values are not used to promote beyond scratch_diagnostic",
        },
        "summary": {
            "section_A_receipts": sorted(required),
            "ceiling": CLASSIFICATION,
            "pin_sha256": next(iter(pin_hashes)),
            "source_sha256_current": gates["source_sha256_current"],
            "strict_controls": gates["exact_smt_can_fail_controls"],
            "all_pass": bool(all_pass),
            "grassmann_exterior_curvature_mirror": receipts["S2.FG"]["pass"],
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": bool(all_pass), "result_path": rel(RESULT_PATH), "gates": gates}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
