#!/usr/bin/env python3
"""Envelope assembler for geo_s7_discrete_refinement_v0."""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

from geo_s7_discrete_refinement_v0_core import (
    CLASSIFICATION,
    CONVENTION_PIN,
    CURVE_DIR,
    FORMAL_ADMISSION_ALLOWED,
    JULIA_PROJECT,
    LINEAGE_CITATIONS,
    N_VALUES,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SIM_DIR,
    SIM_ID,
    build_s7_payload,
    curve_hashes,
    file_sha256,
    rel,
    sha256_text,
    source_bundle_sha256,
    stable_json_sha256,
)

SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
INTERVAL_RESULT = RESULT_DIR / f"{SIM_ID}_interval_results.json"
SPEC_COPY = SIM_DIR / "s7_build_spec_20260610.md"
DIRECTIVE_COPY = SIM_DIR / "directive_addendum.md"

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from fresh engine receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source, result, bundle, and PIN hash checks"},
    "csv": {"tried": True, "used": True, "reason": "output-artifact export only; never a proof surface"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "csv": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def export_curves(payload: dict[str, Any]) -> dict[str, Any]:
    CURVE_DIR.mkdir(parents=True, exist_ok=True)
    exports = {
        "area": {
            "path": CURVE_DIR / "area_curve.csv",
            "rows": payload["area_curve"]["rows"],
            "columns": ["eta_label", "eta", "N", "area_estimate", "area_target", "abs_error", "rel_error", "rate_between_N_doublings"],
        },
        "holonomy": {
            "path": CURVE_DIR / "holonomy_curve.csv",
            "rows": payload["holonomy_curve"]["rows"],
            "columns": [
                "eta_label",
                "eta",
                "N",
                "primary_estimator",
                "holonomy_estimate",
                "target_h",
                "abs_error",
                "rel_error",
                "rate_between_N_doublings",
                "round_trip_residual",
                "central_secant_estimate",
                "central_secant_abs_error",
                "estimator_abs_diff",
                "blind_table_comparison_estimator",
            ],
        },
        "flux_stokes": {
            "path": CURVE_DIR / "flux_stokes_curve.csv",
            "rows": payload["flux_stokes_curve"]["rows"],
            "columns": [
                "pair_label",
                "eta_i_label",
                "eta_j_label",
                "N",
                "flux_estimate",
                "target_Phi_ij",
                "abs_error",
                "rel_error",
                "rate_between_N_doublings",
                "stokes_residual",
                "stokes_abs_residual",
            ],
        },
    }
    out = {}
    for name, spec in exports.items():
        write_csv(spec["path"], spec["rows"], spec["columns"])
        out[name] = {
            "path": rel(spec["path"]),
            "sha256": file_sha256(spec["path"]),
            "row_count": len(spec["rows"]),
            "evidence_role": "output_artifact_only",
            "proof_surface": "interval_error_certificates",
        }
    return out


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "source_hash_current": file_sha256(ROOT / payload["source_path"]) == payload["source_sha256"],
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
        "TOOL_MANIFEST": payload["TOOL_MANIFEST"],
        "TOOL_INTEGRATION_DEPTH": payload["TOOL_INTEGRATION_DEPTH"],
        "tool_calls": payload.get("tool_calls", []),
    }


def find_curve_row(rows: list[dict[str, Any]], **selector: Any) -> dict[str, Any]:
    for row in rows:
        if all(row.get(key) == value for key, value in selector.items()):
            return row
    raise KeyError(selector)


def julia_summary_comparison(julia: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    native = julia["engine_native_checks"]
    area_row = find_curve_row(payload["area_curve"]["rows"], eta_label="pi/4", N=64)
    h_i = find_curve_row(payload["holonomy_curve"]["rows"], eta_label="pi/6", N=64)
    h_j = find_curve_row(payload["holonomy_curve"]["rows"], eta_label="pi/4", N=64)
    flux = find_curve_row(payload["flux_stokes_curve"]["rows"], pair_label="pi/6->pi/4", N=64)
    rows = [
        {
            "name": "area_pi_over_4_N64",
            "julia": native["area_pi_over_4_N64"]["estimate"],
            "envelope": area_row["area_estimate"],
            "abs_diff": abs(native["area_pi_over_4_N64"]["estimate"] - area_row["area_estimate"]),
            "tolerance": 1.0e-10,
        },
        {
            "name": "holonomy_pi_over_6_N64",
            "julia": native["holonomy_pi_over_6_N64"]["estimate"],
            "envelope": h_i["holonomy_estimate"],
            "abs_diff": abs(native["holonomy_pi_over_6_N64"]["estimate"] - h_i["holonomy_estimate"]),
            "tolerance": 1.0e-10,
        },
        {
            "name": "holonomy_pi_over_4_N64",
            "julia": native["holonomy_pi_over_4_N64"]["estimate"],
            "envelope": h_j["holonomy_estimate"],
            "abs_diff": abs(native["holonomy_pi_over_4_N64"]["estimate"] - h_j["holonomy_estimate"]),
            "tolerance": 1.0e-10,
        },
        {
            "name": "flux_pi_over_6_to_pi_over_4_N64",
            "julia": native["flux_pi_over_6_to_pi_over_4_N64"]["estimate"],
            "envelope": flux["flux_estimate"],
            "abs_diff": abs(native["flux_pi_over_6_to_pi_over_4_N64"]["estimate"] - flux["flux_estimate"]),
            "tolerance": 1.0e-10,
        },
        {
            "name": "stokes_pi_over_6_to_pi_over_4_N64",
            "julia": native["stokes_pi_over_6_to_pi_over_4_N64"]["residual"],
            "envelope": flux["stokes_residual"],
            "abs_diff": abs(native["stokes_pi_over_6_to_pi_over_4_N64"]["residual"] - flux["stokes_residual"]),
            "tolerance": 1.0e-10,
        },
    ]
    return {"rows": rows, "pass": all(row["abs_diff"] <= row["tolerance"] for row in rows)}


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    out: set[str] = set()
    for payload in payloads.values():
        out.update(str(item) for item in payload.get("claim_path_tools", []))
    return sorted(out)


def independent_fatality_receipt(
    engines: dict[str, dict[str, Any]],
    payload_hashes: dict[str, str],
    julia_compare: dict[str, Any],
) -> dict[str, Any]:
    jax = engines["jax"]
    pytorch = engines["pytorch"]
    julia = engines["julia"]
    jax_z3 = jax["crossover_proofs"]["z3"]
    jax_cvc5 = jax["crossover_proofs"]["cvc5"]
    torch_z3 = pytorch["crossover_proofs"]["z3"]
    torch_cvc5 = pytorch["crossover_proofs"]["cvc5"]
    julia_z3 = julia["crossover_proofs"]["julia_z3"]
    jax_loop = jax["engine_native_checks"]["transported_loop"]
    torch_loop = pytorch["engine_native_checks"]["transported_loop"]
    julia_grid_n64 = next(row for row in julia["engine_native_checks"]["grid_rows"] if row["N"] == 64)
    proof_signature = {
        "jax_z3": {
            "verdict": jax_z3["verdict"],
            "raw": jax_z3["bound_raw_values"],
            "control": jax_z3["naive_cover_control_verdict"],
        },
        "jax_cvc5": {
            "verdict": jax_cvc5["verdict"],
            "raw": jax_cvc5["bound_raw_values"],
            "control": jax_cvc5["naive_cover_control_verdict"],
        },
        "pytorch_z3": {
            "verdict": torch_z3["verdict"],
            "raw": torch_z3["bound_raw_values"],
            "control": torch_z3["naive_cover_control_verdict"],
        },
        "pytorch_cvc5": {
            "verdict": torch_cvc5["verdict"],
            "raw": torch_cvc5["bound_raw_values"],
            "control": torch_cvc5["naive_cover_control_verdict"],
        },
        "julia_z3": {
            "verdict": julia_z3["verdict"],
            "raw": julia_z3["bound_raw_values"],
            "control": julia_z3["naive_cover_control_verdict"],
        },
    }
    target_raw = {"N": 64, "kappa_mismatch_count": 0, "physical_point_count": 2048}
    proof_signature_pass = all(
        row["verdict"] == "unsat" and row["raw"] == target_raw and row["control"] == "unsat"
        for row in proof_signature.values()
    )
    transported_loop_pass = (
        jax_loop["pass"] is True
        and torch_loop["pass"] is True
        and jax_loop["N"] == torch_loop["N"] == 64
        and jax_loop["primary_estimator"] == torch_loop["primary_estimator"] == "wilson_overlap_product"
        and max(abs(a - b) for a, b in zip(jax_loop["holonomy_estimates"], torch_loop["holonomy_estimates"], strict=True)) <= 1.0e-12
    )
    negative_control_hash_pass = (
        jax["curve_hashes"]["negative_controls"]
        == pytorch["curve_hashes"]["negative_controls"]
        == payload_hashes["negative_controls"]
    )
    curve_hash_pass = all(
        jax["curve_hashes"][key] == pytorch["curve_hashes"][key] == payload_hashes[key]
        for key in ["area", "holonomy", "flux_stokes", "parity_cover", "presentations"]
    )
    julia_cover_pass = (
        julia_grid_n64["physical_point_count"] == 2048
        and julia_grid_n64["expected_physical_point_count"] == 2048
        and julia_grid_n64["two_times_physical_equals_chart"] is True
        and julia_grid_n64["parity_class_invariant_under_cover"] is True
        and julia_compare["pass"] is True
    )
    checks = {
        "proof_signature_pass": proof_signature_pass,
        "curve_hash_pass": curve_hash_pass,
        "negative_control_hash_pass": negative_control_hash_pass,
        "transported_loop_pass": transported_loop_pass,
        "julia_cover_pass": julia_cover_pass,
        "no_peer_reads": all(engine["reads_peer_result"] is False for engine in engines.values()),
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "proof_signature": proof_signature,
        "curve_hashes": {
            "jax": jax["curve_hashes"],
            "pytorch": pytorch["curve_hashes"],
            "payload": payload_hashes,
        },
        "transported_loop_max_abs_diff": max(
            abs(a - b) for a, b in zip(jax_loop["holonomy_estimates"], torch_loop["holonomy_estimates"], strict=True)
        ),
        "julia_grid_N64": julia_grid_n64,
    }


def remediated_positive_receipts(receipts: dict[str, Any], interval_cert: dict[str, Any]) -> dict[str, Any]:
    out = json.loads(json.dumps(receipts))
    replacements = {
        "P5_area_curve": ("area", "Area convergence is certified by IntervalArithmetic bounds; CSV rows are artifacts only."),
        "P6_holonomy_curve": ("holonomy", "Holonomy convergence is certified by IntervalArithmetic bounds; CSV rows are artifacts only."),
        "P7_flux_curve": ("flux", "Flux convergence is certified by IntervalArithmetic bounds; CSV rows are artifacts only."),
        "P8_discrete_stokes": ("stokes", "Stokes residual convergence is certified by IntervalArithmetic bounds; CSV rows are artifacts only."),
    }
    for key, (family, route) in replacements.items():
        summary = interval_cert["certificates"][family]["summary"]
        out[key] = {
            "pass": summary["pass"] is True,
            "exact_strength": "rigorous_interval_bound",
            "route": route,
            "interval_certificate_summary": summary,
            "interval_certificate_result": rel(INTERVAL_RESULT),
            "csv_curve_role": "output_artifact_only",
        }
    out["P9_rate_ledger"] = {
        "pass": all(interval_cert["certificates"][family]["summary"]["pass"] is True for family in ["area", "holonomy", "flux", "stokes"]),
        "exact_strength": "rigorous_interval_bound",
        "route": "IntervalArithmetic summaries certify finite row bounds, N64 threshold clearance, and N8-to-N64 refinement improvement for area/holonomy/flux/Stokes.",
        "interval_certificate_result": rel(INTERVAL_RESULT),
        "csv_curve_role": "output_artifact_only",
    }
    return out


def evidence_route_table(interval_cert: dict[str, Any], topology_cert: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "route": "quotient_grid_tables",
            "claim_rows": ["P2_even_N_cover_quotient", "P3_parity_cover_compatibility"],
            "claim_carrier": "exact integer quotient/class tables",
            "proof_surface": "z3/cvc5/Z3.jl exact integer checks plus emitted tables",
            "artifact_only": [],
            "status": "pass",
        },
        {
            "route": "topology_mesh_certificate",
            "claim_rows": ["P4_three_presentation_row_locations"],
            "claim_carrier": "N>=8 quotient triangulation",
            "proof_surface": "TopoNetX SimplicialComplex incidence plus GUDHI SimplexTree betti readout",
            "artifact_only": ["N=2/N=4 degenerate mesh controls"],
            "status": "pass" if topology_cert["pass"] is True else "fail",
            "claim_N_values": topology_cert["claim_N_values"],
        },
        {
            "route": "interval_error_certificates",
            "claim_rows": ["P5_area_curve", "P6_holonomy_curve", "P7_flux_curve", "P8_discrete_stokes", "P9_rate_ledger"],
            "claim_carrier": "IntervalArithmetic.jl interval-valued propagation",
            "proof_surface": rel(INTERVAL_RESULT),
            "artifact_only": [rel(CURVE_DIR / "area_curve.csv"), rel(CURVE_DIR / "holonomy_curve.csv"), rel(CURVE_DIR / "flux_stokes_curve.csv")],
            "status": "pass" if interval_cert["all_pass"] is True else "fail",
            "summaries": {family: interval_cert["certificates"][family]["summary"] for family in ["area", "holonomy", "flux", "stokes"]},
        },
        {
            "route": "claim_ceiling",
            "claim_rows": ["P12_claim_ceiling"],
            "claim_carrier": "literal classification and promotion fields",
            "proof_surface": "source/result field equality checks",
            "artifact_only": [],
            "status": "pass",
        },
    ]


def copied_inputs() -> dict[str, Any]:
    return {
        "spec": {"path": rel(SPEC_COPY), "sha256": file_sha256(SPEC_COPY), "exists": SPEC_COPY.exists()},
        "directive": {"path": rel(DIRECTIVE_COPY), "sha256": file_sha256(DIRECTIVE_COPY), "exists": DIRECTIVE_COPY.exists()},
    }


def build_result() -> dict[str, Any]:
    payload = build_s7_payload()
    curve_artifacts = export_curves(payload)
    payload_hashes = curve_hashes(payload)
    engines = {"julia": load_json(JULIA_RESULT), "jax": load_json(JAX_RESULT), "pytorch": load_json(PYTORCH_RESULT)}
    interval_cert = load_json(INTERVAL_RESULT)
    topology_cert = engines["jax"]["engine_native_checks"]["topology_mesh_certificate"]
    positive_receipts = remediated_positive_receipts(payload["positive_receipts"], interval_cert)
    pin_hashes = {engine["pin_sha256"] for engine in engines.values()}
    jax_py_hash_match = engines["jax"].get("curve_hashes") == engines["pytorch"].get("curve_hashes") == payload_hashes
    julia_compare = julia_summary_comparison(engines["julia"], payload)
    fatality = independent_fatality_receipt(engines, payload_hashes, julia_compare)
    proofs = {
        "z3": engines["jax"]["crossover_proofs"]["z3"],
        "cvc5": engines["jax"]["crossover_proofs"]["cvc5"],
        "julia_z3": engines["julia"]["crossover_proofs"]["julia_z3"],
        "pytorch_z3": engines["pytorch"]["crossover_proofs"]["z3"],
        "pytorch_cvc5": engines["pytorch"]["crossover_proofs"]["cvc5"],
    }
    source_paths = [
        SIM_DIR / f"{SIM_ID}_core.py",
        SIM_DIR / f"{SIM_ID}_julia.jl",
        SIM_DIR / f"{SIM_ID}_jax.py",
        SIM_DIR / f"{SIM_ID}_pytorch.py",
        SOURCE_PATH,
        SIM_DIR / f"{SIM_ID}_interval.jl",
        SIM_DIR / f"{SIM_ID}_exact_strength_validator.py",
    ]
    existing_source_paths = [path for path in source_paths if path.exists()]
    source_bundle = source_bundle_sha256(existing_source_paths)
    engine_records = {
        "julia": engine_record(engines["julia"], JULIA_RESULT),
        "jax": engine_record(engines["jax"], JAX_RESULT),
        "pytorch": engine_record(engines["pytorch"], PYTORCH_RESULT),
    }
    gates = {
        "engine_legs_pass": all(engine["all_pass"] is True for engine in engines.values()),
        "identical_pin_sha256": len(pin_hashes) == 1 and next(iter(pin_hashes)) == sha256_text(PIN_SPEC),
        "source_sha256_current": all(record["source_hash_current"] for record in engine_records.values()),
        "no_peer_result_reads": all(engine["reads_peer_result"] is False for engine in engines.values()),
        "ceilings_preserved": all(
            engine["classification"] == CLASSIFICATION
            and engine["promotion_allowed"] is PROMOTION_ALLOWED
            and engine["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for engine in engines.values()
        ),
        "positive_receipts_pass": all(row["pass"] is True for row in payload["positive_receipts"].values()),
        "remediated_positive_receipts_pass": all(row["pass"] is True for row in positive_receipts.values()),
        "interval_error_certificates_pass": interval_cert["all_pass"] is True,
        "topology_mesh_tool_certificate": topology_cert["pass"] is True,
        "negative_controls_executed": all(item.get("executed") is True for item in payload["negative_controls"].values()),
        "jax_pytorch_curve_hashes_match_payload": jax_py_hash_match,
        "julia_native_summary_matches_payload": julia_compare["pass"],
        "cross_engine_fatality": fatality["pass"],
        "copied_spec_and_directive_present": all(item["exists"] for item in copied_inputs().values()),
        "crossover_proofs_agree_unsat": proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] == proofs["julia_z3"]["verdict"] == "unsat",
    }
    all_pass = all(gates.values())
    divergence_rows = julia_compare["rows"]
    max_divergence = max(row["abs_diff"] for row in divergence_rows)
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "S7 finite Hopf-torus grid refinement: 2:1 quotient grids, parity-cover receipts, three-presentation row locations, and discrete area/holonomy/flux/Stokes convergence curves.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "source_bundle_sha256": source_bundle,
        "result_path": rel(RESULT_PATH),
        "copied_inputs": copied_inputs(),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "convention_pin": CONVENTION_PIN,
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": engines["julia"].get("julia_project", JULIA_PROJECT),
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": engines["julia"]["source_sha256"],
            "receipt_path": engines["julia"]["result_path"],
            "proof_tag": "geo_s7_discrete_refinement_v0_julia_z3_cover_parity",
            "proof_pass": proofs["julia_z3"]["verdict"] == "unsat",
            "table_version": None,
            "bracket_convention": "not_applicable_finite_hopf_torus_discretization",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": engines["julia"].get("julia_project", JULIA_PROJECT), "packages": engines["julia"]["packages_used"], "role": "carrier-side exact cover/parity proof plus compact geometry summary"},
            "julia_interval": {
                "project": interval_cert["julia_project"],
                "packages": interval_cert["packages_used"],
                "role": "isolated IntervalArithmetic convergence/error certificate lane; not strict-carrier evidence",
                "capability_receipt": interval_cert["capability_receipt"],
            },
            "jax": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": engines["jax"]["packages_used"], "role": "batched transported-loop and exact z3/cvc5 proof lane"},
            "pytorch": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": engines["pytorch"]["packages_used"], "role": "torch.func transported-loop and exact proof lane"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": sorted(set(collect_claim_tools(engines)) | {str(item) for item in interval_cert.get("claim_path_tools", [])}),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": engine_records,
        "lineage_citations": LINEAGE_CITATIONS,
        "positive_receipts": positive_receipts,
        "evidence_route_table": evidence_route_table(interval_cert, topology_cert),
        "parity_cover": payload["parity_cover"],
        "presentations": payload["presentations"],
        "topology_mesh_certificate": topology_cert,
        "interval_error_certificates": interval_cert,
        "area_curve": payload["area_curve"],
        "holonomy_curve": payload["holonomy_curve"],
        "flux_stokes_curve": payload["flux_stokes_curve"],
        "rate_ledger": payload["rate_ledger"],
        "exact_support_rows": payload["exact_support_rows"],
        "negative_controls": payload["negative_controls"],
        "cross_engine_fatality_receipt": fatality,
        "curve_hashes": payload_hashes,
        "curve_artifacts": curve_artifacts,
        "crossover_proofs": proofs,
        "build_gates": gates,
        "julia_summary_comparison": julia_compare,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": {row["name"]: row["julia"] for row in divergence_rows},
                "jax": {"curve_hashes": payload_hashes},
                "pytorch": {"curve_hashes": engines["pytorch"].get("curve_hashes")},
            },
            "max_divergence": max_divergence,
            "within_tolerance": max_divergence <= 1.0e-10 and jax_py_hash_match,
            "rows": divergence_rows,
        },
        "summary": {
            "N_values": N_VALUES,
            "eta_count": 7,
            "strip_pair_count": 8,
            "ceiling": CLASSIFICATION,
            "all_pass": bool(all_pass),
            "self_check_is_not_audit_evidence": True,
        },
    }
    return result


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH), "gates": result["build_gates"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
