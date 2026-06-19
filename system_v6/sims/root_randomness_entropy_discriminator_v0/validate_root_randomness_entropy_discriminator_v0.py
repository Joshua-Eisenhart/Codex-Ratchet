#!/usr/bin/env python3
"""Packet-local validator for root_randomness_entropy_discriminator_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "root_randomness_entropy_discriminator_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, errors: list[str], name: str) -> dict[str, Any]:
    require(errors, isinstance(value, dict), f"{name} must be an object")
    return value if isinstance(value, dict) else {}


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == SIM_ID, "sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", "classification must stay scratch_diagnostic")
    require(errors, payload.get("claim_ceiling") == "root_layer_discriminator_only", "claim ceiling mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    require(errors, payload.get("envelope_built_with_helper") is True, "helper envelope gate missing")
    require(errors, payload.get("build_helper_path") == "scripts/build_three_engine_envelope.py", "helper path mismatch")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))

    rows = as_dict(payload.get("source_rows"), errors, "source_rows")
    require(errors, set(rows) == {"R01", "R02", "R03", "R04", "R05"}, "source rows mismatch")
    for row_id, row in rows.items():
        require(errors, row.get("packet") == SIM_ID, f"{row_id} packet mismatch")
        quotes = row.get("quotes")
        require(errors, isinstance(quotes, list) and bool(quotes), f"{row_id} quotes missing")
        if isinstance(quotes, list):
            for quote in quotes:
                require(errors, bool(quote.get("quote")), f"{row_id} quote text missing")
                require(errors, bool(quote.get("source_path")), f"{row_id} source path missing")
                require(errors, isinstance(quote.get("source_line"), int), f"{row_id} source line missing")

    table = payload.get("discriminator_table")
    require(errors, isinstance(table, list) and len(table) == 5, "expected five discriminator rows")
    if isinstance(table, list):
        for row in table:
            require(errors, row.get("source_quote"), "table source_quote missing")
            require(errors, row.get("source_path"), "table source_path missing")
            require(errors, isinstance(row.get("source_line"), int), "table source_line missing")
            require(errors, row.get("tiny_observable"), "table tiny_observable missing")
            require(errors, row.get("negative_control"), "table negative_control missing")
            require(errors, row.get("fresh_receipt") == payload.get("result_path"), "table fresh receipt mismatch")
            require(errors, row.get("claim_ceiling") == "root_layer_discriminator_only", "table claim ceiling mismatch")

    root = as_dict(payload.get("root_randomness_first"), errors, "root_randomness_first")
    density = as_dict(root.get("density_matrix"), errors, "density_matrix")
    require(errors, density.get("density_kind") == "classical_diagonal_vn_proxy", "density kind must be diagonal proxy")
    require(errors, density.get("trace_one") is True, "density trace-one check failed")
    require(errors, density.get("psd") is True, "density PSD check failed")
    require(errors, density.get("hermitian") is True, "density Hermitian check failed")
    require(errors, density.get("physical_claim") == "none; finite diagonal count density only", "density physical boundary missing")
    require(errors, root.get("entropy_is_first_derived_structure") is True, "root entropy first gate failed")

    controls = as_dict(payload.get("controls"), errors, "controls")
    label_structured = as_dict(controls.get("label_structured_control"), errors, "label_structured_control")
    label_shuffle = as_dict(controls.get("label_shuffle_control"), errors, "label_shuffle_control")
    geometry = as_dict(controls.get("geometry_first_control"), errors, "geometry_first_control")
    bit_guard = as_dict(controls.get("bit_identical_guard"), errors, "bit_identical_guard")
    require(errors, label_structured.get("same_ensemble_counts") is True, "label structured must use same ensemble counts")
    require(errors, label_structured.get("label_rows_distinguish") is True, "label structured control has no teeth")
    require(errors, label_structured.get("root_rows_alone_do_not_read_label_meaning") is True, "root rows must not smuggle labels")
    require(errors, label_structured.get("root_randomness_first_has_teeth") is True, "root discriminator verdict must have teeth")
    require(errors, label_shuffle.get("root_rows_invariant") is True, "label shuffle must preserve root rows")
    require(errors, label_shuffle.get("label_dependent_rows_changed") is True, "label shuffle must change label-dependent rows")
    require(errors, label_shuffle.get("nominalism_row_computed") is True, "nominalism row not computed")
    require(errors, geometry.get("order_changed") is True, "geometry order must change")
    require(errors, geometry.get("root_rows_differ_from_randomness_first") is True, "geometry-first readout must differ")
    require(errors, geometry.get("n01_style_order_test") == "survived", "N01-style root order test must survive")
    require(errors, bit_guard.get("label_structured_not_bit_identical_to_shuffle") is True, "label structured/shuffle controls bit-identical")
    require(errors, bit_guard.get("geometry_not_bit_identical_to_baseline") is True, "geometry control bit-identical to baseline")

    proofs = as_dict(payload.get("crossover_proofs"), errors, "crossover_proofs")
    for name in ["z3", "cvc5", "julia_z3"]:
        proof = as_dict(proofs.get(name), errors, f"crossover_proofs.{name}")
        require(errors, proof.get("verdict") == "unsat", f"{name} negated identity must be UNSAT")
        require(errors, proof.get("perturbed_control_verdict") == "sat", f"{name} perturbed control must be SAT")
        require(errors, proof.get("asserted_precomputed_boolean") is False, f"{name} must not assert a precomputed boolean")
        require(errors, bool(proof.get("raw_bound_values")), f"{name} raw bound values missing")

    gates = as_dict(payload.get("builder_gates"), errors, "builder_gates")
    for key, value in gates.items():
        require(errors, value is True, f"builder gate failed: {key}")

    summary = str(payload.get("claim_summary", "")).lower()
    banned = ["proves", "forces", "confirms physics", "ontology", "spacetime", "dark matter", "dark energy", "cosmology"]
    for word in banned:
        require(errors, word not in summary, f"claim_summary contains overclaim term: {word}")
    disallowed = payload.get("disallowed_claims")
    require(errors, isinstance(disallowed, list) and "physics admission" in disallowed, "disallowed claims must list physics admission")
    require(errors, payload.get("safe_order", {}).get("source_quote_to_fence_lint_v0") == "not_run_deferred; not implied complete", "safe-order predecessor boundary missing")

    errors.extend(f"three_engine_shape: {err}" for err in validate_three_engine(payload, require_pytorch=True))
    return errors


def main() -> int:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    errors = validate_payload(payload)
    result = {"ok": not errors, "errors": errors, "result_json": str(RESULT.relative_to(ROOT))}
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
