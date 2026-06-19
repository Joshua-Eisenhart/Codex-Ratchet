#!/usr/bin/env python3
"""Three-engine envelope for geo_s6_stacked_flows_hopf_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s6_stacked_flows_hopf_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
SPEC = ROOT / "system_v6/receipts/s6_build_spec_20260610.md"
SPEC_COPY = SIM_DIR / "s6_build_spec_20260610.md"
DIRECTIVE_COPY = SIM_DIR / "directive_addendum.md"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

PIN_SPEC = (
    "geo_s6_stacked_flows_hopf_v0|mode=RESTRICTED_STACKED|"
    "arrow_types=(foliation,dynamical_flow,quotient_projection,covering_group_quotient,undefined_without_lift)|"
    "shell_coordinate=z=cos(2*eta)|r_eta=(sin(2*eta)cos(2*chi),sin(2*eta)sin(2*chi),cos(2*eta))|"
    "eta_rows=(pi/12,pi/6,pi/4,pi/3,5*pi/12)|chi0=pi/7|loop_period=2*pi_lifted_chart_cycle|"
    "leakage=dz_dt=e_z^T(A*r_eta+b)_from_S5_exported_A_b|"
    "Phi_D=U_E_U_E|Phi_I=E_U_E_U|U=Ne_Vortex_L_flow_t1|E=Si_Hill_L_flow_t1|carrier=density_bloch|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from fresh engine receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source, result, copied-input, and PIN hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}
REQUIRED_RECEIPTS = {
    "P1_prior_reuse_lineage",
    "P2_arrow_typing_and_mode",
    "P3_z_dot_from_exported_A_b",
    "P4_shell_classification",
    "P5_leakage_integrals_are_flux",
    "P6_A_F_h_action_status",
    "P7_sixteen_placements_computed",
    "P8_matrix64_reuse_not_rebuild",
    "P9_loop_order_gap",
    "P10_round_trip_gates",
    "P11_consistency_gates",
    "P12_executed_mutation_controls",
    "P13_cross_engine_fatality",
    "P14_claim_ceiling",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def current_source_hash_ok(payload: dict[str, Any]) -> bool:
    source = ROOT / payload["source_path"]
    return source.exists() and file_sha256(source) == payload["source_sha256"]


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
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
        "tool_calls": payload.get("tool_calls", []),
        "claim_path_tools": payload.get("claim_path_tools", []),
    }


def copied_input_records() -> dict[str, Any]:
    return {
        "s6_build_spec": {
            "source_path": rel(SPEC),
            "copy_path": rel(SPEC_COPY),
            "source_sha256": file_sha256(SPEC),
            "copy_sha256": file_sha256(SPEC_COPY),
            "exists": SPEC_COPY.exists(),
            "matches_source": SPEC_COPY.exists() and file_sha256(SPEC_COPY) == file_sha256(SPEC),
        },
        "directive_addendum": {
            "copy_path": rel(DIRECTIVE_COPY),
            "copy_sha256": file_sha256(DIRECTIVE_COPY),
            "exists": DIRECTIVE_COPY.exists(),
            "source": "user directive plus s6_build_spec directive rules; no separate /tmp S6 directive file was present",
        },
    }


def cross_engine_consistency(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    signatures = {engine: payload["cross_engine_signature"] for engine, payload in payloads.items()}
    canonical = signatures["jax"]
    row_reports = {}
    for row_id in sorted(canonical["leakage_rows"]):
        row_reports[row_id] = {
            "julia": signatures["julia"]["leakage_rows"][row_id],
            "jax": signatures["jax"]["leakage_rows"][row_id],
            "pytorch": signatures["pytorch"]["leakage_rows"][row_id],
            "pass": signatures["julia"]["leakage_rows"][row_id] == signatures["jax"]["leakage_rows"][row_id] == signatures["pytorch"]["leakage_rows"][row_id],
        }
    loop_values = {engine: sig["loop_order_g_DI_scaled_1e9"] for engine, sig in signatures.items()}
    counts = {
        engine: {"placement_count": sig["placement_count"], "matrix64_overlay_count": sig["matrix64_overlay_count"]}
        for engine, sig in signatures.items()
    }
    return {
        "method": "fatal exact signature comparison over scaled leakage integrals, classes, placement count, Matrix64 overlay count, and g_DI",
        "row_reports": row_reports,
        "loop_order_g_DI_scaled_1e9": loop_values,
        "counts": counts,
        "all_pass": all(row["pass"] for row in row_reports.values())
        and len(set(loop_values.values())) == 1
        and all(c["placement_count"] == 16 and c["matrix64_overlay_count"] == 64 for c in counts.values()),
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def build_result() -> dict[str, Any]:
    payloads = {"julia": load_json(JULIA_RESULT), "jax": load_json(JAX_RESULT), "pytorch": load_json(PYTORCH_RESULT)}
    jax = payloads["jax"]
    copied = copied_input_records()
    pin_hash = sha256_text(PIN_SPEC)
    pin_hashes = {payload["pin_sha256"] for payload in payloads.values()}
    cross_engine = cross_engine_consistency(payloads)
    receipts = dict(jax["receipts"])
    receipts["P13_cross_engine_fatality"] = {
        "pass": cross_engine["all_pass"] is True,
        "exact_strength": "cross_engine_signature",
        "data": {"method": cross_engine["method"], "loop_order_g_DI_scaled_1e9": cross_engine["loop_order_g_DI_scaled_1e9"]},
    }
    build_gates = {
        "engine_legs_pass": all(payload["all_pass"] is True for payload in payloads.values()),
        "identical_pin_sha256": len(pin_hashes) == 1 and pin_hashes == {pin_hash},
        "source_sha256_current": all(current_source_hash_ok(payload) for payload in payloads.values()),
        "no_peer_result_reads": all(payload["reads_peer_result"] is False for payload in payloads.values()),
        "ceilings_preserved": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is PROMOTION_ALLOWED
            and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for payload in payloads.values()
        ),
        "copied_spec_and_directive_present": copied["s6_build_spec"]["matches_source"] is True and copied["directive_addendum"]["exists"] is True,
        "required_positive_receipts_present": REQUIRED_RECEIPTS <= set(receipts),
        "required_positive_receipts_pass": all(receipts[key]["pass"] is True for key in REQUIRED_RECEIPTS),
        "cross_engine_signature_fatality": cross_engine["all_pass"] is True,
        "shell_rows_eight": len(jax["shell_leakage_rows"]) == 8,
        "placement_rows_sixteen": len(jax["placement_rows"]) == 16,
        "matrix64_overlay_rows_64": len(jax["matrix64_overlay_rows"]) == 64,
        "negative_controls_executed": jax["negative_controls"]["all_executed_can_fail"] is True,
        "loop_order_gap_positive": jax["loop_order_gap"]["max_g_DI_scaled_1e9"] > 0,
        "julia_flow_solver_route": payloads["julia"]["loop_order_gap"]["flow_solver_route"]["pass"] is True,
        "jax_loop_flow_solver_route": jax["loop_order_gap"]["flow_solver_route"]["pass"] is True,
        "jax_shell_flow_solver_route": all(
            eta_row["flow_solver_route"]["pass"] is True for row in jax["shell_leakage_rows"].values() for eta_row in row["eta_rows"]
        ),
        "commuting_control_zero": jax["loop_order_gap"]["controls"]["commuting_erased_control"]["pass"] is True,
        "noncommuting_control_positive": jax["loop_order_gap"]["controls"]["noncommuting_control"]["pass"] is True,
        "claim_path_no_control_only_tools": set(collect_claim_tools(payloads)).isdisjoint({"numpy", "scipy", "mpmath"}),
    }
    all_pass = all(build_gates.values())
    engines = {engine: engine_record(payload, {"julia": JULIA_RESULT, "jax": JAX_RESULT, "pytorch": PYTORCH_RESULT}[engine]) for engine, payload in payloads.items()}
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim": "S6 restricted/stacked Hopf-shell leakage, placement, Matrix64 overlay, and Phi_D/Phi_I loop-order gap packet from exported S5 A,b",
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "pin_spec": PIN_SPEC,
        "pin_sha256": pin_hash,
        "convention_pin": jax["convention_pin"],
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "copied_inputs": copied,
        "source_lineage": jax["source_lineage"],
        "genericity_check": jax["genericity_check"],
        "blind_expected_comparison": jax["blind_expected_comparison"],
        "round_trip_report": jax["round_trip_report"],
        "engines": engines,
        "claim_path_tools": collect_claim_tools(payloads),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "canon_runtime": {
            "semantic_owner": "julia_for_carrier_signature; S5 exported A,b remains imported prior evidence",
            "s5_result_path": rel(S5_RESULT := ROOT / "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json"),
            "s5_result_sha256": file_sha256(S5_RESULT),
            "consumer_policy": "compute dz/dt from imported exported A,b with fixed shell coordinate and no S5 table rebuild",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": payloads["julia"].get("julia_project"), "packages": payloads["julia"]["packages_used"], "role": "carrier_signature_mirror"},
            "jax": {"packages": payloads["jax"]["packages_used"], "role": "rich_symbolic_builder"},
            "pytorch": {"packages": payloads["pytorch"]["packages_used"], "role": "tensor_mirror"},
            "tensor_exchange": "none; engines share source receipts, not peer result tensors",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "shell_leakage_rows": jax["shell_leakage_rows"],
        "terrain_summary": jax["terrain_summary"],
        "terrain_action_rows": jax["terrain_action_rows"],
        "placement_rows": jax["placement_rows"],
        "matrix64_overlay_rows": jax["matrix64_overlay_rows"],
        "loop_order_gap": jax["loop_order_gap"],
        "flow_solver_routes": {
            "julia_loop": payloads["julia"]["loop_order_gap"]["flow_solver_route"],
            "jax_loop": jax["loop_order_gap"]["flow_solver_route"],
            "jax_shell_eta_rows_all_pass": all(
                eta_row["flow_solver_route"]["pass"] is True for row in jax["shell_leakage_rows"].values() for eta_row in row["eta_rows"]
            ),
            "matrix_exponential_role": "exact constant-flow special-case parity check; not the primary flow-evolution claim path",
        },
        "negative_controls": jax["negative_controls"],
        "positive_ledger": {key: {"pass": receipts[key]["pass"], "exact_strength": receipts[key]["exact_strength"]} for key in sorted(REQUIRED_RECEIPTS)},
        "receipts": receipts,
        "cross_engine_consistency": cross_engine,
        "crossover_proofs": {
            "z3": jax["crossover_proofs"]["z3"],
            "cvc5": jax["crossover_proofs"]["cvc5"],
            "julia_z3": payloads["julia"]["crossover_proofs"]["julia_z3"],
            "pytorch_z3": payloads["pytorch"]["crossover_proofs"]["z3"],
            "pytorch_cvc5": payloads["pytorch"]["crossover_proofs"]["cvc5"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                engine: {
                    "loop_order_g_DI_scaled_1e9": payload["cross_engine_signature"]["loop_order_g_DI_scaled_1e9"],
                    "leakage_signature_sha256": sha256_text(json.dumps(payload["cross_engine_signature"]["leakage_rows"], sort_keys=True)),
                }
                for engine, payload in payloads.items()
            },
            "max_divergence": 0 if cross_engine["all_pass"] else 1,
            "comparison": "exact signature match required; disagreement is fatal",
        },
        "build_gates": build_gates,
        "strength_tokens": jax["strength_tokens"],
        "self_check_notice": "Builder self-checks are not audit evidence; this envelope is a build receipt only.",
        "all_pass": all_pass,
    }


def main() -> int:
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result_path": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
