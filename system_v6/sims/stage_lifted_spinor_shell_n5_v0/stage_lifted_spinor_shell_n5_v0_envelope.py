#!/usr/bin/env python3
"""Three-engine envelope for stage_lifted_spinor_shell_n5_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "stage_lifted_spinor_shell_n5_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
REQUIRED_ROWS = {f"P{i}" for i in range(1, 13)}
COMMON_VALUE_KEYS = [
    "support_node_count",
    "support_edge_count",
    "support_face_count",
    "GHZ_A_B_I",
    "GHZ_A_B_conditional",
    "order_gap_TO",
    "bracketing_path_gap",
    "matrix_associator_norm",
    "aggregate_leakage",
    "ghz_non_nesting_distance",
]
PIN_SPEC = (
    "stage_lifted_spinor_shell_n5_v0|n=5-only|shell_nested_hopf_torus_support|"
    "arrow_types=tensor,algebra extension,quotient,principal-bundle / fibration,subset/submanifold|"
    "GHZ partial trace is non-nesting mixture|z=cos(2 eta)|classification=scratch_diagnostic|"
    "promotion_allowed=false|formal_admission_allowed=false"
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_leg(engine: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{SIM_ID}_{engine}_results.json"
    return json.loads(path.read_text(encoding="utf-8"))


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
        "tool_calls": payload.get("tool_calls", []),
        "acceptance": payload["acceptance"],
        "values": payload["values"],
    }


def source_hash_fresh(payload: dict[str, Any]) -> bool:
    source_path = ROOT / payload["source_path"]
    return source_path.exists() and sha256_file(source_path) == payload["source_sha256"]


def result_hashes(legs: dict[str, dict[str, Any]]) -> dict[str, str]:
    hashes = {}
    for engine, payload in legs.items():
        hashes[engine] = sha256_file(ROOT / payload["result_path"])
    return hashes


def collect_claim_path_tools(legs: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in legs.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def row_ids(payload: dict[str, Any]) -> set[str]:
    return {key.split("_", 1)[0] for key in payload.get("rows", {}) if key.startswith("P")}


def controls_fired(payload: dict[str, Any]) -> bool:
    return all(isinstance(control, dict) and control.get("fired") is True for control in payload.get("controls", {}).values())


def mutation_controls_rerun(payload: dict[str, Any]) -> bool:
    support_controls = payload.get("rows", {}).get("P2_support_object", {}).get("controls", {})
    scoped = ["global_shell_only", "no_face", "duplicate_eta", "collapsed_shell"]
    return all(
        isinstance(support_controls.get(name), dict)
        and support_controls[name].get("fired") is True
        and support_controls[name].get("rerun_under_mutation") is True
        and support_controls[name].get("gate_passed_after_mutation") is False
        and bool(support_controls[name].get("failing_values"))
        for name in scoped
    )


def s5_s6_lineage_pass(payload: dict[str, Any]) -> bool:
    lineage = payload.get("rows", {}).get("P8_shell_leakage", {}).get("s5_s6_generator_lineage", {})
    taxonomy = set(lineage.get("s6_class_taxonomy", []))
    rows = lineage.get("rows", {})
    return (
        lineage.get("pass") is True
        and lineage.get("current_z_cos_2eta_mirror_retained") is True
        and set(
            [
                "preserve_T_eta",
                "projected_shell_preserve_but_Hopf_leave",
                "move_leaf",
                "cross_shell",
                "leave_foliation",
            ]
        )
        <= taxonomy
        and len(rows) == 8
        and all(row.get("derived_from_exported_A_b") is True and row.get("site_rows") for row in rows.values())
    )


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    engine_values = {engine: {key: float(payload["values"][key]) for key in COMMON_VALUE_KEYS} for engine, payload in legs.items()}
    rows = []
    max_div = 0.0
    max_key = None
    for key in COMMON_VALUE_KEYS:
        values = {engine: engine_values[engine][key] for engine in legs}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_div:
            max_div = diff
            max_key = key
    return {
        "julia_authoritative": True,
        "engine_values": engine_values,
        "max_divergence": max_div,
        "max_divergence_key": max_key,
        "comparison": {"rows": rows, "within_tolerance": max_div <= 1.0e-8, "same_named_observable_sets": True},
    }


def build_result() -> dict[str, Any]:
    legs = {engine: load_leg(engine) for engine in ("julia", "jax", "pytorch")}
    pin_hashes = {payload["pin_sha256"] for payload in legs.values()}
    pin_specs = {payload["pin_spec"] for payload in legs.values()}
    seeds = {payload["seed"] for payload in legs.values()}
    expected_pin = sha256_text(PIN_SPEC)
    div = divergence(legs)
    jax_z3 = legs["jax"]["crossover_proofs"]["z3"]
    jax_cvc5 = legs["jax"]["crossover_proofs"]["cvc5"]
    gate_pass = {
        "legs_all_pass": all(payload["all_pass"] is True for payload in legs.values()),
        "pin_identical": len(pin_hashes) == 1 and len(pin_specs) == 1 and next(iter(pin_hashes)) == expected_pin,
        "seeds_declared_identical": len(seeds) == 1,
        "source_hashes_fresh": all(source_hash_fresh(payload) for payload in legs.values()),
        "ceiling_exact": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is PROMOTION_ALLOWED
            and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for payload in legs.values()
        ),
        "no_peer_result_reads": all(payload["reads_peer_result"] is False for payload in legs.values()),
        "required_rows_present": all(REQUIRED_ROWS <= row_ids(payload) for payload in legs.values()),
        "required_acceptance_pass": all(all(payload["acceptance"].values()) for payload in legs.values()),
        "negative_controls_fired": all(controls_fired(payload) for payload in legs.values()),
        "mutation_controls_rerun_with_failing_values": all(mutation_controls_rerun(payload) for payload in legs.values()),
        "s5_s6_generator_lineage": all(s5_s6_lineage_pass(payload) for payload in legs.values()),
        "smt_z3_cvc5_agree": jax_z3["verdict"] == "unsat" and jax_cvc5["verdict"] == "unsat" and jax_z3["control_verdict"] == "sat" and jax_cvc5["control_verdict"] == "sat",
        "julia_z3_mirror": legs["julia"]["crossover_proofs"]["julia_z3"]["verdict"] == "unsat" and legs["julia"]["crossover_proofs"]["julia_z3"]["control_verdict"] == "sat",
        "pytorch_z3_cvc5_mirror": legs["pytorch"]["crossover_proofs"]["z3"]["verdict"] == "unsat" and legs["pytorch"]["crossover_proofs"]["cvc5"]["verdict"] == "unsat",
        "divergence_ok": div["comparison"]["within_tolerance"],
        "ghz_non_nesting_bound": all(payload["rows"]["blind_tripwires"]["GHZ_non_nesting"]["GHZ_non_nesting_binding"] is True for payload in legs.values()),
    }
    all_pass = all(gate_pass.values())
    claim_path_tools = collect_claim_path_tools(legs)
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "claim": "n=5 lifted-ladder rung: a five-site spinor network is placed on explicit nested-Hopf-torus shell support and the requested density, path, entropy, order, bracketing, leakage, topology, nesting, Cl(10), and negative-control rows are recomputed under scratch-only ceiling.",
        "allowed_claims": [
            "scratch diagnostic n=5 lifted-shell packet exists and runs",
            "three engines agree on the named finite scalar rows under the declared PIN",
            "executed controls catch shell-label-only, density-only, no-face, collapsed-shell, wrong-coordinate, GHZ-nesting, W-nesting, separable, and permutation-control errors",
        ],
        "disallowed_claims": [
            "stage closure",
            "canonical geometry",
            "bridge or axis admission",
            "trend across n=5..8",
            "promotion beyond scratch diagnostic",
        ],
        "pin_spec": PIN_SPEC,
        "pin_sha256": expected_pin,
        "pin_identical_across_legs": gate_pass["pin_identical"],
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "engine_result_sha256": result_hashes(legs),
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
            "reads_peer_result": False,
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": legs["julia"].get("julia_project"),
            "role": "Julia strict-carrier leg owns the carrier/QIT/geometric package receipt; envelope only compares bounded emitted rows",
            "classification": CLASSIFICATION,
            "proof_tag": "stage_lifted_spinor_shell_n5_v0_density_erasure_and_lifted_support",
            "proof_pass": gate_pass["julia_z3_mirror"],
            "bracket_convention": "ordinary 32x32 matrix multiplication is associative; lifted path grouping sensitivity is a separate network action row; raw-object bracketing SMT remains the separate geo_bracketing_smt_lifted_v0 packet",
            "consumer_policy": "no promotion; later packets/audits required for trend or formal claims",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": legs["julia"].get("julia_project"), "packages": legs["julia"]["packages_used"], "role": "semantic_owner"},
            "jax": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": legs["jax"]["packages_used"], "role": "topology/qutip/quimb/diffrax/jaxopt/z3/cvc5 workhorse"},
            "pytorch": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": legs["pytorch"]["packages_used"], "role": "tensor graph geometry autograd mirror"},
            "tensor_exchange": "none; no cross-engine tensor exchange on claim path",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": claim_path_tools,
        "TOOL_MANIFEST": {
            engine: legs[engine]["TOOL_MANIFEST"] for engine in legs
        },
        "TOOL_INTEGRATION_DEPTH": {
            engine: legs[engine]["TOOL_INTEGRATION_DEPTH"] for engine in legs
        },
        "engines": {engine: engine_record(payload) for engine, payload in legs.items()},
        "rows": {engine: legs[engine]["rows"] for engine in legs},
        "controls": {engine: legs[engine]["controls"] for engine in legs},
        "gate_pass": gate_pass,
        "crossover_proofs": {
            "z3": jax_z3,
            "cvc5": jax_cvc5,
            "julia_z3": legs["julia"]["crossover_proofs"]["julia_z3"],
            "pytorch_z3": legs["pytorch"]["crossover_proofs"]["z3"],
            "pytorch_cvc5": legs["pytorch"]["crossover_proofs"]["cvc5"],
        },
        "divergence": div,
        "source_refs": {
            "spec": "system_v6/receipts/lifted_ladder_spec_20260610.md",
            "blind_tripwires": "/tmp/nesting_blind_expected_20260610.md",
            "density_doctrine": "system_v6/receipts/density_matrix_as_quotient_doctrine_20260610.md",
            "s6_spec": "system_v6/receipts/s6_build_spec_20260610.md",
            "s5_exported_A_b": "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json",
            "s6_committed_packet": "system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json",
            "s8_s9": "system_v6/receipts/s8_s9_adjudication_20260610.md",
        },
    }


def main() -> int:
    result = build_result()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(f"{SIM_ID}_ENVELOPE_DONE all_pass={str(result['all_pass']).lower()} max_divergence={result['divergence']['max_divergence']}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
