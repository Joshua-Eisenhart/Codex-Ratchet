#!/usr/bin/env python3
"""Helper-built envelope for root_randomness_entropy_discriminator_v0."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

from root_randomness_entropy_discriminator_v0_common import (
    CLAIM_CEILING,
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SIM_DIR,
    SIM_ID,
    SOURCE_ROWS,
    controls_readout,
    discriminator_table,
    engine_values,
    finite_carrier,
    rel,
    root_readout,
    sha256_file,
    stable_sha256,
    write_json,
)


SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
LEG_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
}
HELPER_PATH = ROOT / "scripts" / "build_three_engine_envelope.py"

spec = importlib.util.spec_from_file_location("build_three_engine_envelope", HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(helper)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_lane(leg: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "source_path": leg["source_path"],
        "result_path": rel(result_path),
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "package_observables": leg["package_observables"],
        "tool_calls": leg.get("tool_calls", []),
        "TOOL_MANIFEST": leg.get("TOOL_MANIFEST", {}),
        "TOOL_INTEGRATION_DEPTH": leg.get("TOOL_INTEGRATION_DEPTH", {}),
    }


def close_float(left: float, right: float) -> bool:
    return abs(float(left) - float(right)) <= 1.0e-10


def build_result() -> dict[str, Any]:
    legs = {name: load_json(path) for name, path in LEG_PATHS.items()}
    root = root_readout()
    controls = controls_readout()
    jax = legs["jax"]
    proofs = {
        "z3": jax["crossover_proofs"]["z3"],
        "cvc5": jax["crossover_proofs"]["cvc5"],
        "julia_z3": legs["julia"]["crossover_proofs"]["julia_z3"],
    }
    values = {engine: leg["engine_values"] for engine, leg in legs.items()}
    engine_match = (
        values["julia"]["outcome_support_count"] == values["jax"]["outcome_support_count"] == values["pytorch"]["outcome_support_count"]
        and close_float(values["julia"]["counting_entropy_bits"], values["jax"]["counting_entropy_bits"])
        and close_float(values["jax"]["counting_entropy_bits"], values["pytorch"]["counting_entropy_bits"])
        and close_float(values["julia"]["label_structured_mi_bits"], values["jax"]["label_structured_mi_bits"])
        and close_float(values["jax"]["label_structured_mi_bits"], values["pytorch"]["label_structured_mi_bits"])
    )
    gates = {
        "build_card_copied": (SIM_DIR / "build_card.md").is_file(),
        "no_builder_audit_verdict": not (SIM_DIR / "audit_verdict.md").exists(),
        "classification_scratch": all(leg["classification"] == CLASSIFICATION for leg in legs.values()),
        "promotion_blocked": all(leg["promotion_allowed"] is False for leg in legs.values()),
        "formal_admission_blocked": all(leg["formal_admission_allowed"] is False for leg in legs.values()),
        "all_legs_passed": all(leg["all_pass"] is True for leg in legs.values()),
        "engine_rows_match": engine_match,
        "smt_binds_computed_rows": all(
            proofs[name]["verdict"] == "unsat"
            and proofs[name]["perturbed_control_verdict"] == "sat"
            and proofs[name].get("asserted_precomputed_boolean") is False
            and bool(proofs[name].get("raw_bound_values"))
            for name in proofs
        ),
        "controls_nonvacuous": controls["label_structured_control"]["label_rows_distinguish"] is True
        and controls["label_shuffle_control"]["root_rows_invariant"] is True
        and controls["label_shuffle_control"]["label_dependent_rows_changed"] is True
        and controls["geometry_first_control"]["root_rows_differ_from_randomness_first"] is True
        and controls["bit_identical_guard"]["label_structured_not_bit_identical_to_shuffle"] is True
        and controls["bit_identical_guard"]["geometry_not_bit_identical_to_baseline"] is True,
        "density_diagonal_proxy_honest": root["density_matrix"]["density_kind"] == "classical_diagonal_vn_proxy"
        and root["density_matrix"]["trace_one"] is True
        and root["density_matrix"]["psd"] is True
        and root["density_matrix"]["hermitian"] is True,
        "source_quote_to_fence_consumed": set(SOURCE_ROWS) == {"R01", "R02", "R03", "R04", "R05"},
        "safe_order_predecessor_deferred_not_claimed": True,
    }
    all_pass = all(gates.values())
    result_path_rel = rel(RESULT_PATH)
    extra_fields = {
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": result_path_rel,
        "claim_ceiling": CLAIM_CEILING,
        "envelope_built_with_helper": True,
        "build_helper_path": rel(HELPER_PATH),
        "no_builder_audit_verdict": gates["no_builder_audit_verdict"],
        "builder_gates": gates,
        "safe_order": {
            "authority_commit": "35ed8142cace61a2e9837e9f0f13d2607cb90942",
            "receipt": "system_v6/receipts/physics_model_primary_deepread_20260612.md",
            "item": 2,
            "packet": SIM_ID,
            "shared_fence": "source quote -> finite witness -> control -> claim ceiling",
            "source_quote_to_fence_lint_v0": "not_run_deferred; not implied complete",
        },
        "source_rows": SOURCE_ROWS,
        "finite_carrier": finite_carrier(),
        "root_randomness_first": root,
        "controls": controls,
        "discriminator_table": discriminator_table(result_path_rel),
        "discriminator_verdict": "nontrivial_finite_root_layer_separation" if all_pass else "inconclusive_no_teeth",
        "claim_summary": (
            "This scratch diagnostic computes a finite root-layer discriminator: entropy rows are derived from a pinned "
            "random ensemble before labels or geometry, label shuffle preserves root rows while changing label-dependent "
            "readouts, and geometry-first order changes the finite readout table."
        ),
        "allowed_claims": [
            "finite pinned-ensemble entropy ladder computed",
            "label-shuffle root-row invariance computed",
            "label-structured and geometry-first controls nonvacuous on this carrier",
            "root-layer discriminator only",
        ],
        "disallowed_claims": [
            "physics admission",
            "ontology conclusion",
            "cosmology conclusion",
            "spacetime claim",
            "dark matter or dark energy claim",
            "vacuum-energy inference",
            "quantum vN physical claim from diagonal count density",
            "downstream packet completion",
        ],
        "positive_negative_boundary_sections": {
            "positive": ["finite entropy ladder", "label-shuffle root invariance", "geometry-first order sensitivity"],
            "negative": ["label-only cosmetic shuffle as evidence", "geometry metadata without readout change"],
            "boundary": ["diagonal count density only", "SMT binds count/order flags only"],
        },
        "TOOL_INTENT_MATRIX": {
            "julia": {"mode": "Graphs order-control plus Julia Z3 finite flag proof", "load_bearing": ["Graphs", "Z3"]},
            "jax": {"mode": "x64 probability vector plus sympy/z3/cvc5 finite proof", "load_bearing": ["sympy", "z3", "cvc5"]},
            "pytorch": {"mode": "torch.func boundary derivative plus sympy/z3/cvc5 finite proof", "load_bearing": ["torch.func", "sympy", "z3", "cvc5"]},
        },
        "TOOL_MANIFEST": {engine: leg.get("TOOL_MANIFEST", {}) for engine, leg in legs.items()},
        "TOOL_INTEGRATION_DEPTH": {engine: leg.get("TOOL_INTEGRATION_DEPTH", {}) for engine, leg in legs.items()},
        "tool_calls": {engine: leg.get("tool_calls", []) for engine, leg in legs.items()},
        "tool_intent": {
            "claim_classes": ["finite_root_layer_discriminator", "computed_controls", "smt_count_order_flags"],
            "engine_tool_intent": {
                "julia": {
                    "Graphs": "Graphs.has_path finite order-control witness for geometry-first mutation",
                    "Z3": "Z3.check binds computed finite discriminator flags with erased-control SAT",
                },
                "jax": {
                    "sympy": "exact entropy expression over pinned finite probabilities",
                    "z3": "z3.Solver binds computed finite discriminator flags",
                    "cvc5": "cvc5.Solver independently binds computed finite discriminator flags",
                },
                "pytorch": {
                    "torch.func": "jacrev checks normalized diagonal entropy boundary derivative",
                    "sympy": "exact entropy expression over pinned finite probabilities",
                    "z3": "z3.Solver binds computed finite discriminator flags",
                    "cvc5": "cvc5.Solver independently binds computed finite discriminator flags",
                },
            },
        },
        "validator_commands": [
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / (SIM_ID + '_jax.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / (SIM_ID + '_pytorch.py'))}",
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier "
            f"{rel(SIM_DIR / (SIM_ID + '_julia.jl'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / (SIM_ID + '_envelope.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / ('validate_' + SIM_ID + '.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch {result_path_rel}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest {rel(SIM_DIR / 'tests')}",
        ],
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "divergence_details": {
            "engine_values": values,
            "engine_match": engine_match,
            "comparison_hash": hashlib.sha256(json.dumps(values, sort_keys=True).encode("utf-8")).hexdigest(),
        },
    }
    envelope = helper.build_envelope(
        sim_id=SIM_ID,
        lanes={engine: engine_lane(leg, LEG_PATHS[engine]) for engine, leg in legs.items()},
        mode="three_engine_finite_root_layer_discriminator",
        claim_path_tools=["Graphs", "Z3", "sympy", "z3", "cvc5", "torch.func"],
        crossover_proofs=proofs,
        divergence={
            "julia_authoritative": True,
            "engine_values": {engine: values[engine]["outcome_support_count"] for engine in values},
            "max_divergence": 0 if engine_match else 1,
            "comparison": "finite support/count rows and entropy readouts agree within tolerance",
        },
        classification=CLASSIFICATION,
        promotion_allowed=PROMOTION_ALLOWED,
        formal_admission_allowed=FORMAL_ADMISSION_ALLOWED,
        parent_lineage={
            "physics_primary_deepread": "35ed8142c",
            "safe_order_item": "2",
        },
        extra_fields=extra_fields,
    )
    return envelope


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_result()
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": rel(RESULT_PATH)}, indent=2))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
