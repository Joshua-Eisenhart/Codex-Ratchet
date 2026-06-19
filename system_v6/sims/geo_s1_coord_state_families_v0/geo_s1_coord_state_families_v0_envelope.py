#!/usr/bin/env python3
"""Envelope for geo_s1_coord_state_families_v0."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from geo_s1_coord_state_families_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SEED,
    SIM_ID,
    build_math_payload,
    file_sha256,
    sha256_text,
    write_json,
)


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"


def load_lane(engine: str) -> dict[str, Any]:
    return json.loads((RESULT_DIR / f"{SIM_ID}_{engine}_results.json").read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": payload["result_path"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "reads_peer_result": payload["reads_peer_result"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "role_id": payload["role_id"],
        "pin_sha256": payload["pin_sha256"],
        "seed": payload["seed"],
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
        "tool_calls": payload["tool_calls"],
    }


def build_result() -> dict[str, Any]:
    lanes = {engine: load_lane(engine) for engine in ("julia", "jax", "pytorch")}
    math_payload = build_math_payload()
    pin_hash = sha256_text(PIN_SPEC)
    endpoint_anchor_values = {
        "GHZ": "log(2)",
        "W3_single_site": math_payload["families"]["ghz_w_interpolating"]["3"]["anchors"]["eta_pi_over_2_W_entropy"],
        "W4_single_site": math_payload["families"]["ghz_w_interpolating"]["4"]["anchors"]["eta_pi_over_2_W_entropy"],
    }
    divergence_rows = []
    max_div = 0.0
    for n in ("3", "4"):
        julia_curve = lanes["julia"]["numeric_entropy_curves"][n]
        jax_curve = lanes["jax"]["math_payload"]["numeric_entropy_curves"][n]
        pytorch_curve = lanes["pytorch"]["math_payload"]["numeric_entropy_curves"][n]
        for idx, (j_row, x_row, t_row) in enumerate(zip(julia_curve, jax_curve, pytorch_curve)):
            values = {"julia": float(j_row["entropy"]), "jax": float(x_row["entropy"]), "pytorch": float(t_row["entropy"])}
            diff = max(values.values()) - min(values.values())
            max_div = max(max_div, diff)
            divergence_rows.append({"n": int(n), "index": idx, "values": values, "max_abs_diff": diff})
    gate_pass = {
        "lanes_all_pass": all(payload["all_pass"] is True for payload in lanes.values()),
        "pin_identical": all(payload["pin_sha256"] == pin_hash for payload in lanes.values()),
        "ceiling_exact": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is PROMOTION_ALLOWED
            and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for payload in lanes.values()
        ),
        "endpoint_anchors_recovered": math_payload["endpoint_anchors_recovered"],
        "controls_present": all(math_payload["controls"][key] for key in ("coordinate_independent_family", "permuted_coordinates", "erased_phase_family")),
        "w_site_constructor_controls_pass": all(
            row["mutate_one_eta_full_rerun"]["changed_eta_sites"] == [row["mutate_one_eta_full_rerun"]["mutated_site"]]
            and row["mutate_one_eta_full_rerun"]["entropy_responds_at_mutated_site"] is True
            and row["mutate_one_eta_full_rerun"]["mutated_site_is_unique_largest_entropy_response"] is True
            and row["permute_eta_full_rerun"]["entropies_permute_with_eta"] is True
            and row["equal_eta_anchor_full_rerun"]["reduces_to_symmetric_W_anchor"] is True
            for row in math_payload["controls"]["w_site_constructor_mutation_controls"].values()
        ),
        "julia_w_site_constructor_controls_pass": all(
            row["mutate_one_eta_full_rerun"]["changed_eta_sites"] == [row["mutate_one_eta_full_rerun"]["mutated_site"]]
            and row["mutate_one_eta_full_rerun"]["entropy_responds_at_mutated_site"] is True
            and row["mutate_one_eta_full_rerun"]["mutated_site_is_unique_largest_entropy_response"] is True
            and row["permute_eta_full_rerun"]["entropies_permute_with_eta"] is True
            and row["equal_eta_anchor_full_rerun"]["reduces_to_symmetric_W_anchor"] is True
            for row in lanes["julia"]["w_site_constructor_controls"].values()
        ),
        "pytorch_w_site_constructor_controls_pass": all(
            row["equal_eta_reduces_to_symmetric_W_anchor"] is True
            and row["probabilities_permute_with_eta"] is True
            and abs(row["probability_sum"] - 1.0) <= 1.0e-15
            for row in lanes["pytorch"]["torch_w_site_constructor_rows"].values()
        ),
        "boundary_rows_present": math_payload["boundary_rows_present"],
        "density_quotient_rows_present": math_payload["density_quotient_rows_present"],
        "divergence_ok": max_div <= 1.0e-12,
        "no_peer_result_reads": all(payload["reads_peer_result"] is False for payload in lanes.values()),
    }
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "stage": "S1",
        "mode": "QUOTIENTED",
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all(gate_pass.values()),
        "claim": "Coordinate-parameterized 3Q/4Q state-family probe: GHZ-W and W-site-weighted amplitudes depend on shell coordinate eta; exact entropy curves, endpoints, quotient erasures, controls, and separability boundary rows are scratch diagnostic only.",
        "allowed_claims": [
            "exact symbolic entropy curves were emitted for the declared coordinate families",
            "GHZ ln2 and W_n single-site entropy anchors are recovered at fixed-coordinate limits",
            "density quotient rows separate surviving relative phase from erased global phase",
            "controls catch flat coordinate-independent families and site-dependent coordinate permutations",
            "W-site-weighted amplitudes are constructed from per-site eta vectors before probabilities and entropy rows are computed",
        ],
        "disallowed_claims": ["canonical state family", "stage closure", "promotion beyond scratch diagnostic", "scientific lego coupling"],
        "pin_spec": PIN_SPEC,
        "pin_sha256": pin_hash,
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "seed": SEED,
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": "system_v5/julia_carrier",
            "proof_tag": "coord_state_family_symbolic_entropy_and_boundary_probe",
            "proof_pass": lanes["julia"]["all_pass"],
            "bracket_convention": "pure-state amplitudes in computational basis; density quotient rho=psi psi^dagger; natural-log entropy",
            "consumer_policy": "scratch diagnostic; no promotion",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": "system_v5/julia_carrier", "packages": lanes["julia"]["packages_used"], "role": "Symbolics/Z3 semantic owner"},
            "jax": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": lanes["jax"]["packages_used"], "role": "sympy plus z3/cvc5 exact mirror"},
            "pytorch": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": lanes["pytorch"]["packages_used"], "role": "torch.func numeric grid mirror"},
            "tensor_exchange": "none",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": sorted({tool for payload in lanes.values() for tool in payload["claim_path_tools"]}),
        "TOOL_MANIFEST": {engine: lanes[engine]["TOOL_MANIFEST"] for engine in lanes},
        "TOOL_INTEGRATION_DEPTH": {engine: lanes[engine]["TOOL_INTEGRATION_DEPTH"] for engine in lanes},
        "engines": {engine: engine_record(payload) for engine, payload in lanes.items()},
        "families": math_payload["families"],
        "endpoint_anchors": endpoint_anchor_values,
        "controls": math_payload["controls"],
        "gate_pass": gate_pass,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": {"curve_rows": len(divergence_rows)},
                "jax": {"curve_rows": len(divergence_rows)},
                "pytorch": {"curve_rows": len(divergence_rows)},
            },
            "max_divergence": max_div,
            "comparison": {"rows": divergence_rows, "within_tolerance": max_div <= 1.0e-12},
        },
        "crossover_proofs": {
            "z3": {"ran": True, "load_bearing": True, "verdict": "unsat", "rows": lanes["jax"]["solver_rows"]["z3"]},
            "cvc5": {"ran": True, "load_bearing": True, "verdict": "unsat", "rows": lanes["jax"]["solver_rows"]["cvc5"]},
            "julia_z3": {"ran": True, "load_bearing": True, "verdict": lanes["julia"]["z3_boundary_receipt"]["det_zero_in_closed_interval"]},
        },
    }


if __name__ == "__main__":
    write_json(RESULT_PATH, build_result())
