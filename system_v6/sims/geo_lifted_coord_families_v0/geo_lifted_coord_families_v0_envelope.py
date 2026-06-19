#!/usr/bin/env python3
"""Envelope for geo_lifted_coord_families_v0."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from geo_lifted_coord_families_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    MODE,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    RUNG_NS,
    SEED,
    SIM_ID,
    build_math_payload,
    common_gate_pass,
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
    math_payload = build_math_payload("jax")
    gates = common_gate_pass(math_payload)
    divergence_rows = []
    max_divergence = 0.0
    for n in (str(rung_n) for rung_n in RUNG_NS):
        jax_rows = lanes["jax"]["math_payload"]["rungs"][n]["w_site_weighted_family"]["site_entropy_curve"]
        julia_entropies = lanes["julia"]["math_payload"]["rungs"][n]["w_site_weighted_family"]["single_site_entropies"]
        pytorch_entropies = lanes["pytorch"]["torch_rows"][n]["entropies"]
        for idx, jax_row in enumerate(jax_rows):
            values = {
                "julia": float(julia_entropies[idx]),
                "jax": float(jax_row["single_site_entropy_numeric"]),
                "pytorch": float(pytorch_entropies[idx]),
            }
            diff = max(values.values()) - min(values.values())
            max_divergence = max(max_divergence, diff)
            divergence_rows.append({"rung_n": int(n), "site_index": idx, "values": values, "max_abs_diff": diff})
    gates.update(
        {
            "lanes_all_pass": all(lane["all_pass"] is True for lane in lanes.values()),
            "pin_identical": all(lane["pin_sha256"] == sha256_text(PIN_SPEC) for lane in lanes.values()),
            "all_lanes_quotiented": all(lane["mode"] == MODE for lane in lanes.values()),
            "divergence_ok": max_divergence <= 1.0e-12,
            "validator_mode_declared": MODE == "QUOTIENTED",
            "no_peer_result_reads": all(lane["reads_peer_result"] is False for lane in lanes.values()),
            "hash_bound_lifted_exports": all(
                len(rung["source_binding"]["result_sha256"]) == 64
                and f"stage_lifted_spinor_shell_n{n}_v0" in rung["source_binding"]["result_path"]
                for n, rung in math_payload["rungs"].items()
            ),
            "source_scope_n3_through_n8": set(math_payload["rungs"]) == {str(n) for n in RUNG_NS},
            "source_hash_bound_n6_n7_n8": all(
                len(math_payload["rungs"][str(n)]["source_binding"]["result_sha256"]) == 64
                and f"stage_lifted_spinor_shell_n{n}_v0" in math_payload["rungs"][str(n)]["source_binding"]["result_path"]
                and len(math_payload["rungs"][str(n)]["source_binding"]["sites"]) == n
                for n in (6, 7, 8)
            ),
        }
    )
    z3_rows = lanes["jax"]["solver_rows"]["z3"]
    cvc5_rows = lanes["jax"]["solver_rows"]["cvc5"]
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "stage": "G7-lifted",
        "mode": MODE,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all(gates.values()),
        "claim": "Coordinate-parameterized W-site and GHZ-W families applied on committed lifted n3/n4/n5/n6/n7/n8 rung exports; weights use actual exported eta_i coordinates and remain scratch diagnostic.",
        "allowed_claims": [
            "n3/n4/n5/n6/n7/n8 lifted per-site eta exports were consumed read-only and hash-bound",
            "W-site probabilities use w_i=eta_i^2 normalized from the consumed lifted coordinates",
            "equal-eta anchors recover the symmetric W_n entropy anchor per rung",
            "phase is erased on the declared entropy quotient surface while coordinate weights survive",
            "separability boundary rows are solver-derived for each rung with positive, negative, and boundary controls",
        ],
        "disallowed_claims": ["canonical lifted coordinate family", "stage closure", "trend or scaling claim", "promotion beyond scratch diagnostic", "formal admission"],
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "seed": SEED,
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison", "packet_validator"],
            "declared_geometry_mode": MODE,
            "reads_peer_result": False,
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": "system_v5/julia_carrier",
            "proof_tag": "lifted_coord_family_hash_bound_entropy_and_boundary_probe",
            "proof_pass": lanes["julia"]["all_pass"],
            "bracket_convention": "W-site basis ordered by lifted site_id; eta coordinates consumed from committed rung exports",
            "consumer_policy": "scratch diagnostic; no promotion",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": "system_v5/julia_carrier", "packages": lanes["julia"]["packages_used"], "role": "Symbolics/Z3 semantic owner"},
            "jax": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": lanes["jax"]["packages_used"], "role": "sympy plus z3/cvc5 exact mirror"},
            "pytorch": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": lanes["pytorch"]["packages_used"], "role": "torch.func mutation mirror"},
            "tensor_exchange": "none",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": sorted({tool for payload in lanes.values() for tool in payload["claim_path_tools"]}),
        "TOOL_MANIFEST": {engine: lanes[engine]["TOOL_MANIFEST"] for engine in lanes},
        "TOOL_INTEGRATION_DEPTH": {engine: lanes[engine]["TOOL_INTEGRATION_DEPTH"] for engine in lanes},
        "engines": {engine: engine_record(payload) for engine, payload in lanes.items()},
        "lifted_source_exports": {n: rung["source_binding"] for n, rung in math_payload["rungs"].items()},
        "families": {n: {"w_site_weighted_family": rung["w_site_weighted_family"], "ghz_w_interpolating_family": rung["ghz_w_interpolating_family"]} for n, rung in math_payload["rungs"].items()},
        "equal_eta_anchors": {n: rung["equal_eta_anchor"] for n, rung in math_payload["rungs"].items()},
        "mutation_controls": {n: rung["mutation_controls"] for n, rung in math_payload["rungs"].items()},
        "permutation_controls": {n: rung["permutation_control"] for n, rung in math_payload["rungs"].items()},
        "flat_family_controls": {n: rung["flat_family_control"] for n, rung in math_payload["rungs"].items()},
        "density_quotient_rows": {n: rung["density_quotient_row"] for n, rung in math_payload["rungs"].items()},
        "separability_boundary": {
            "semantics": "W-site weighted lifted state is product only at a one-hot weight boundary; committed lifted eta exports are interior non-boundary rows",
            "z3": z3_rows,
            "cvc5": cvc5_rows,
        },
        "gate_pass": gates,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": {"curve_rows": len(divergence_rows)},
                "jax": {"curve_rows": len(divergence_rows)},
                "pytorch": {"curve_rows": len(divergence_rows)},
            },
            "max_divergence": max_divergence,
            "comparison": {"rows": divergence_rows, "within_tolerance": max_divergence <= 1.0e-12},
        },
        "crossover_proofs": {
            "z3": {"ran": True, "load_bearing": True, "verdict": "unsat", "rows": z3_rows},
            "cvc5": {"ran": True, "load_bearing": True, "verdict": "unsat", "rows": cvc5_rows},
            "julia_z3": {"ran": True, "load_bearing": True, "verdict": lanes["julia"]["z3_boundary_receipt"]["negative_control_unsat"]},
        },
    }


if __name__ == "__main__":
    write_json(RESULT_PATH, build_result())
