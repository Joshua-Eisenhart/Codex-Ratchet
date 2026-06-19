#!/usr/bin/env python3
"""Packet-local validator for geo_disintegration_machinery_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from geo_disintegration_machinery_v0_common import CLASSIFICATION, RESULT_DIR, ROOT, SIM_DIR, SIM_ID, file_sha256

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


RESULT = RESULT_DIR / f"{SIM_ID}_envelope_results.json"


def main() -> int:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(payload["schema_version"] == "three_engine_sim_result_v1", "schema drift")
    require(payload["all_pass"] is True, "all_pass is not true")
    require(payload["classification"] == CLASSIFICATION, "classification drift")
    require(payload["promotion_allowed"] is False, "promotion drift")
    require(payload["formal_admission_allowed"] is False, "formal admission drift")
    require(payload["engine_contract"]["mode"] == "julia_canon_plus_jax_diagnostic", "engine mode drift")
    require(payload["engine_contract"]["pytorch"]["scoped"] is False, "pytorch scope drift")
    require("No graph/network/autograd claim path" in payload["engine_contract"]["pytorch"]["reason"], "pytorch omission reason missing")
    require(all(value is True for value in payload["build_gates"].values()), "one or more build gates failed")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))

    for name, record in payload["engines"].items():
        source = ROOT / record["source_path"]
        require(source.exists(), f"{name} source missing")
        require(file_sha256(source) == record["source_sha256"], f"{name} source hash mismatch")
        require(record["ran"] is True, f"{name} did not run")
        require(record["reads_peer_result"] is False, f"{name} reads peer result")
        require(record["classification"] == CLASSIFICATION, f"{name} classification drift")
        require(record["promotion_allowed"] is False, f"{name} promotion drift")
        require(record["formal_admission_allowed"] is False, f"{name} formal admission drift")
        require(record["tool_calls"], f"{name} missing tool calls")
        require(record["capability_receipts"], f"{name} missing capability receipts")

    receipts = payload["receipts"]
    require(receipts["R1_eta_marginal_area_law"]["normalized_eta_marginal"] == "sin(2*eta)", "eta marginal drift")
    require(receipts["R1_eta_marginal_area_law"]["torus_layer_area_from_chart"] == "2*pi**2*sin(2*eta)", "torus area law drift")
    require(receipts["R1_eta_marginal_area_law"]["s3_volume"] == "2*pi**2", "S3 volume drift")
    require(receipts["R2_symbolic_disintegration_recovery"]["defect"] == "0", "SymPy recovery defect nonzero")
    require(receipts["J1_symbolics_recovery_identity"]["defect"] == "0", "Julia Symbolics recovery defect nonzero")
    require(receipts["C1_naive_singleton_conditioning_fails"]["denominator_mass"] == "0", "naive denominator not zero")
    require(receipts["C1_naive_singleton_conditioning_fails"]["naive_quotient"] == "nan", "naive quotient did not exhibit undefined value")
    require(receipts["C2_positive_eta_band_agrees"]["defect"] == "0", "positive eta-band defect nonzero")
    require(receipts["C3_wrong_flat_marginal_fails"]["computed_nonzero_defect"] == "-1/6", "wrong flat marginal defect drift")
    require(receipts["C4_null_set_disintegration_scope"]["global_integrated_defect"] == "0", "null-set integrated defect nonzero")

    jax_diag = payload["jax_diagnostics"]
    require(abs(jax_diag["s3_volume_exact"] - 19.739208802178716) < 1.0e-12, "S3 volume numeric drift")
    require(jax_diag["abs_diff_vs_committed_geomstats_probe"] < 1.0e-9, "committed geomstats volume mismatch")
    for row in jax_diag["finite_grid_double_cover_rows"]:
        require(row["physical_points"] * 2 == row["chart_points"], f"N={row['N']} double cover count drift")
        require(row["conditional_total_mass_chart"] == 1.0, f"N={row['N']} conditional mass drift")

    proofs = payload["crossover_proofs"]
    for key in ["z3", "cvc5", "julia_z3"]:
        require(proofs[key]["ran"] is True, f"{key} did not run")
        require(proofs[key]["load_bearing"] is True, f"{key} not load-bearing")
        require(proofs[key]["verdict"] == "unsat", f"{key} verdict drift")
        require(proofs[key]["asserted_precomputed_boolean"] is False, f"{key} asserted a precomputed boolean")
        require(proofs[key]["erased_controls_flip"] is True, f"{key} erased controls did not flip")
        require(proofs[key]["raw_values"]["physical_class_count"] == 32, f"{key} physical class count drift")

    summary = payload["summary"]
    require("mode-4 cards may now cite the disintegration rule" in summary["enables"], "enable boundary missing")
    require("no ratchet sim is run here" in summary["does_not_enable"], "non-enable boundary missing")
    require(summary["ceiling"] == CLASSIFICATION, "summary ceiling drift")

    text_suffixes = {".py", ".jl", ".json"}
    text = "".join(
        path.read_text(encoding="utf-8")
        for path in SIM_DIR.rglob("*")
        if path.is_file() and path.suffix in text_suffixes
    )
    banned = "fix" + "ture"
    require(banned not in text.lower(), "banned wording present")

    print(json.dumps({"ok": not errors, "errors": errors, "result_json": str(RESULT.relative_to(ROOT))}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
