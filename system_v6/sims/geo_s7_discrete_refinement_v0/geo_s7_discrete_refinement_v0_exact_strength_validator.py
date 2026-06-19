#!/usr/bin/env python3
"""Packet-local validator for geo_s7_discrete_refinement_v0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s7_discrete_refinement_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
SPEC = ROOT / "system_v6" / "receipts" / "s7_build_spec_20260610.md"
SPEC_COPY = SIM_DIR / "s7_build_spec_20260610.md"
DIRECTIVE_COPY = SIM_DIR / "directive_addendum.md"
INTERVAL_RESULT = SIM_DIR / "results" / f"{SIM_ID}_interval_results.json"

REQUIRED_POSITIVES = {f"P{i}_{suffix}" for i, suffix in [
    (1, "prior_reuse_lineage"),
    (2, "even_N_cover_quotient"),
    (3, "parity_cover_compatibility"),
    (4, "three_presentation_row_locations"),
    (5, "area_curve"),
    (6, "holonomy_curve"),
    (7, "flux_curve"),
    (8, "discrete_stokes"),
    (9, "rate_ledger"),
    (10, "negative_controls_execute"),
    (11, "cross_engine_fatality"),
    (12, "claim_ceiling"),
]}
REQUIRED_N = [2, 4, 8, 16, 32, 64]
PIN_FIELDS = {"holonomy_quantity", "berry_formula", "phase_domain", "base_loop_count", "orientation_and_c1_sign"}
NEGATIVE_CONTROL_COUNT = 17


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(payload["schema_version"] == "three_engine_sim_result_v1", "schema_version drift")
    require(payload["all_pass"] is True, "envelope all_pass is not true")
    require(payload["classification"] == "scratch_diagnostic", "classification drift")
    require(payload["promotion_allowed"] is False, "promotion_allowed drift")
    require(payload["formal_admission_allowed"] is False, "formal_admission_allowed drift")
    require(all(value is True for value in payload["build_gates"].values()), "one or more build gate failed")
    require(payload["build_gates"].get("interval_error_certificates_pass") is True, "interval certificate gate failed")
    require(payload["build_gates"].get("topology_mesh_tool_certificate") is True, "topology mesh gate failed")
    require(payload["build_gates"].get("remediated_positive_receipts_pass") is True, "remediated positive receipts gate failed")
    require(set(payload["convention_pin"]) == PIN_FIELDS, "S2 five-part convention pin missing/drifted")

    require(SPEC_COPY.exists(), "spec copy missing")
    require(SPEC_COPY.read_text(encoding="utf-8") == SPEC.read_text(encoding="utf-8"), "spec copy differs from receipt spec")
    require(DIRECTIVE_COPY.exists(), "directive copy missing")
    require("BUILDER lane for the S7 positive packet" in DIRECTIVE_COPY.read_text(encoding="utf-8"), "directive copy missing user directive")

    require(REQUIRED_POSITIVES <= set(payload["positive_receipts"]), "missing positive receipt")
    for name in REQUIRED_POSITIVES:
        require(payload["positive_receipts"][name]["pass"] is True, f"{name} did not pass")
    for name in ["P5_area_curve", "P6_holonomy_curve", "P7_flux_curve", "P8_discrete_stokes", "P9_rate_ledger"]:
        row = payload["positive_receipts"][name]
        require(row["exact_strength"] == "rigorous_interval_bound", f"{name} not interval-certified")
        require(row["csv_curve_role"] == "output_artifact_only", f"{name} still treats CSV as proof")

    routes = {row["route"]: row for row in payload.get("evidence_route_table", [])}
    require(routes.get("topology_mesh_certificate", {}).get("status") == "pass", "route table topology route not pass")
    require(routes.get("interval_error_certificates", {}).get("status") == "pass", "route table interval route not pass")
    require(INTERVAL_RESULT.exists(), "interval result missing")
    interval_payload = json.loads(INTERVAL_RESULT.read_text(encoding="utf-8"))
    require(interval_payload["all_pass"] is True, "interval result all_pass false")
    require(interval_payload["TOOL_INTEGRATION_DEPTH"]["IntervalArithmetic"] == "load_bearing", "IntervalArithmetic not load-bearing in interval result")
    require(interval_payload["capability_receipt"] == "system_v6/probes/julia/results/intervalarithmetic_capability_results.json", "IntervalArithmetic capability receipt drift")
    for family in ["area", "holonomy", "flux", "stokes"]:
        summary = interval_payload["certificates"][family]["summary"]
        require(summary["pass"] is True, f"{family} interval summary failed")
        require(summary["N64_below_threshold"] is True, f"{family} interval N64 threshold failed")
        require(summary["refinement_improves_from_N8_to_N64"] is True, f"{family} interval refinement did not improve")

    pins = {record["pin_sha256"] for record in payload["engines"].values()}
    require(len(pins) == 1 and next(iter(pins)) == payload["pin_sha256"], "engine PIN hashes differ")
    for name, record in payload["engines"].items():
        source = ROOT / record["source_path"]
        require(source.exists(), f"{name} source missing")
        require(sha256(source) == record["source_sha256"], f"{name} source_sha256 mismatch")
        require(record["ran"] is True, f"{name} did not run")
        require(record["reads_peer_result"] is False, f"{name} reads peer result")
        require(record["classification"] == "scratch_diagnostic", f"{name} classification drift")
        require(record["promotion_allowed"] is False, f"{name} promotion drift")
        require(record["formal_admission_allowed"] is False, f"{name} formal admission drift")
        require(record["aligned_packages_load_bearing"], f"{name} missing load-bearing packages")

    parity_rows = payload["parity_cover"]["rows"]
    require([row["N"] for row in parity_rows] == REQUIRED_N, "parity rows not exact N ladder")
    for row in parity_rows:
        n = row["N"]
        require(row["chart_point_count"] == n * n, f"N={n} chart count wrong")
        require(row["physical_point_count"] == n * n // 2, f"N={n} physical count wrong")
        require(row["every_class_size_2"] is True, f"N={n} class size not 2")
        require(row["parity_class_invariant_under_cover"] is True, f"N={n} parity cover invariant failed")
        require(row["cover_compatible_adjacency_orientation_check"]["pass"] is True, f"N={n} cover orientation check failed")

    require(len(payload["area_curve"]["rows"]) == 7 * 6, "area curve row count drift")
    require(len(payload["holonomy_curve"]["rows"]) == 7 * 6, "holonomy curve row count drift")
    require(len(payload["flux_stokes_curve"]["rows"]) == 9 * 6, "flux/Stokes curve row count drift")
    require(any(row["eta_label"] == "pi/4" and row["N"] == 64 and abs(row["target_h"]) < 1.0e-12 for row in payload["holonomy_curve"]["rows"]), "pi/4 holonomy zero-target row missing")
    require(all(row["round_trip_pass"] is True for row in payload["holonomy_curve"]["rows"]), "round-trip holonomy gate failed")
    require(payload["holonomy_curve"]["primary_estimator"] == "wilson_overlap_product", "holonomy primary estimator is not Wilson/overlap")
    require(payload["holonomy_curve"]["blind_table_comparison_estimator"] == "wilson_overlap_product", "blind table estimator is not Wilson/overlap")
    require(len(payload["holonomy_curve"]["central_secant_rows"]) == 7 * 6, "central-secant comparison row count drift")
    require(len(payload["holonomy_curve"]["estimator_comparison_rows"]) == 7 * 6, "estimator diff row count drift")
    require(any(row["pair_label"] == "pi/6->5*pi/12" for row in payload["flux_stokes_curve"]["rows"]), "pi/6->5pi/12 wider flux strip missing")
    require(any(row["pair_label"] == "pi/8->3*pi/8" for row in payload["flux_stokes_curve"]["rows"]), "pi/8->3pi/8 wider flux strip missing")
    require(payload["exact_support_rows"]["area_exact_by_constant_density"]["excluded_from_convergence_rate_claims"] is True, "exact area rows not excluded")
    require(payload["exact_support_rows"]["holonomy_closed_form_edge_sum"]["excluded_from_convergence_rate_claims"] is True, "exact holonomy rows not excluded")

    topo = payload["topology_mesh_certificate"]
    require(topo["pass"] is True, "topology mesh certificate did not pass")
    require(topo["claim_N_values"] == [8, 16, 32, 64], "topology claim N values drift")
    for row in topo["rows"]:
        if row["N"] in [8, 16, 32, 64]:
            require(row["certificate_role"] == "claim_path", f"N={row['N']} topology row not claim path")
            require(row["pass"] is True, f"N={row['N']} topology row failed")
            require(row["toponetx_dim"] == 2, f"N={row['N']} TopoNetX dim drift")
            require(row["gudhi_betti_numbers"][:2] == [1, 2], f"N={row['N']} GUDHI betti drift")
        else:
            require(row["certificate_role"] == "degenerate_refinement_control_only", f"N={row['N']} degenerate topology row mislabeled")

    controls = payload["negative_controls"]
    require(len(controls) == NEGATIVE_CONTROL_COUNT, "negative control count drift")
    require(all(row.get("executed") is True for row in controls.values()), "not all negative controls executed")
    require(controls["odd_N_attempted_cover"]["status"] == "blocked_unsupported_odd_N_cover", "odd-N control did not block")
    cover = controls["naive_cover_count_N2_physical_points"]
    require(cover["discrete_area_ratio_exact"]["reduced"] == "2/1", "discrete area cover ratio is not exact 2/1")
    require(cover["discrete_flux_ratio_exact"]["reduced"] == "2/1", "discrete flux cover ratio is not exact 2/1")
    require(cover["discrete_area_naive_over_cover_corrected_ratio"] == 2.0, "discrete area cover factor is not 2")
    require(cover["discrete_flux_naive_over_cover_corrected_ratio"] == 2.0, "discrete flux cover factor is not 2")
    require(cover["continuum_target_comparison"]["label"] == "separate_discrete_vs_continuum_row_not_cover_factor", "continuum comparison is not separately labeled")
    require(controls["cross_engine_copy"]["reads_peer_result"] is True and controls["cross_engine_copy"]["independence_gate_pass"] is False, "cross-engine copy control did not fail")
    require(controls["ceiling_creep"]["claim_ceiling_gate_pass"] is False, "ceiling creep control did not fail")

    for name, artifact in payload["curve_artifacts"].items():
        path = ROOT / artifact["path"]
        require(path.exists(), f"{name} CSV artifact missing")
        require(sha256(path) == artifact["sha256"], f"{name} CSV artifact hash mismatch")
        require(artifact["row_count"] > 0, f"{name} CSV has no rows")
        require(artifact["evidence_role"] == "output_artifact_only", f"{name} CSV is not artifact-only")
        require(artifact["proof_surface"] == "interval_error_certificates", f"{name} CSV proof surface mismatch")

    proofs = payload["crossover_proofs"]
    for key in ["z3", "cvc5", "julia_z3", "pytorch_z3", "pytorch_cvc5"]:
        require(proofs[key]["ran"] is True, f"{key} did not run")
        require(proofs[key]["load_bearing"] is True, f"{key} is not load-bearing")
        require(proofs[key]["verdict"] == "unsat", f"{key} verdict drift")
        require(proofs[key]["asserted_precomputed_boolean"] is False, f"{key} binds a precomputed boolean")
    require(payload["divergence"]["within_tolerance"] is True, "divergence gate not within tolerance")
    require(payload["summary"]["self_check_is_not_audit_evidence"] is True, "self-check boundary missing")

    print(json.dumps({"ok": not errors, "errors": errors, "result_json": str(RESULT.relative_to(ROOT))}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
