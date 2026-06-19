#!/usr/bin/env python3
"""Three-engine envelope for nesting_consistency_family_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "nesting_consistency_family_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
PIN_SPEC = (
    "nesting_consistency_family_v0|family_not_canonical|"
    "embedding_variants=first-sites,last-sites,interleaved-jw-order|"
    "trace_variants=Tr_last,Tr_first,Tr_middle|n=2,3,4|"
    "states=GHZ,W,product_plus,linear_cluster|"
    "arrow_order_hybrids=trace_phase_quotient|quotient_chain=S7_CP3_in_S15_CP7|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from independently generated lane receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source hashing and PIN checks"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}
ALLOWED_ARROW_TYPES = {
    "tensor",
    "algebra extension",
    "quotient",
    "principal-bundle / fibration",
    "subset/submanifold",
    "filtration",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload.get("all_pass") is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path.relative_to(ROOT)),
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
        "shared_scalars": payload.get("shared_scalars", {}),
        "blind_diff_pass": payload.get("blind_diff", {}).get("pass"),
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def gate(condition: bool, name: str, details: Any) -> dict[str, Any]:
    return {"pass": bool(condition), "gate": name, "details": details}


def arrow_types_in(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        if "arrow_type" in value:
            raw = value["arrow_type"]
            if isinstance(raw, list):
                found.extend(str(item) for item in raw)
            else:
                found.append(str(raw))
        for child in value.values():
            found.extend(arrow_types_in(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(arrow_types_in(child))
    return found


def divergence(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {engine: payload["shared_scalars"] for engine, payload in payloads.items()}
    keys = sorted(set().union(*(set(v) for v in values.values())))
    rows = []
    max_divergence = 0
    for key in keys:
        row_values = {engine: values[engine].get(key) for engine in values}
        exact_match = len(set(row_values.values())) == 1
        rows.append({"key": key, "values": row_values, "exact_match": exact_match})
        if not exact_match:
            max_divergence = 1
    return {
        "julia_authoritative": True,
        "engine_values": values,
        "max_divergence": max_divergence,
        "comparison": {"rows": rows, "exact_match": max_divergence == 0},
        "meaning": "exact string/scalar family comparison, not floating tolerance",
    }


def build_result() -> dict[str, Any]:
    payloads = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    div = divergence(payloads)
    pin_hashes = {payload["pin_sha256"] for payload in payloads.values()}
    source_hashes_present = all(payload.get("source_sha256") and len(payload["source_sha256"]) == 64 for payload in payloads.values())
    ceilings_exact = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is PROMOTION_ALLOWED
        and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
        for payload in payloads.values()
    )
    blind_hashes = {payload["blind_diff"]["blind_sha256"] for payload in payloads.values()}
    blind_checks = {engine: payload["blind_diff"]["checks"] for engine, payload in payloads.items()}
    arrow_types = {engine: sorted(set(arrow_types_in(payload["receipts"]))) for engine, payload in payloads.items()}
    arrow_types_allowed = all(set(types) <= ALLOWED_ARROW_TYPES and {"tensor", "algebra extension", "quotient"}.issubset(set(types)) for types in arrow_types.values())
    jax_proofs = payloads["jax"]["proofs"]
    pytorch_proofs = payloads["pytorch"]["proofs"]
    julia_proof = payloads["julia"]["proofs"]["julia_z3"]
    raw_smt_ok = (
        jax_proofs["z3"]["ghz_pure_nesting_forced_equality"] == "unsat"
        and jax_proofs["z3"]["w4_weight_negation"] == "unsat"
        and jax_proofs["z3"]["can_fail_wrong_weight_control"] == "sat"
        and jax_proofs["cvc5"]["ghz_pure_nesting_forced_equality"] == "unsat"
        and jax_proofs["cvc5"]["w4_weight_negation"] == "unsat"
        and jax_proofs["cvc5"]["can_fail_wrong_weight_control"] == "sat"
        and pytorch_proofs["z3"]["ghz_pure_nesting_forced_equality"] == "unsat"
        and pytorch_proofs["cvc5"]["w4_weight_negation"] == "unsat"
        and julia_proof["ghz_pure_nesting_forced_equality"] == "unsat"
        and julia_proof["w4_weight_negation"] == "unsat"
        and julia_proof["can_fail_wrong_weight_control"] == "sat"
    )
    shared = payloads["jax"]["shared_scalars"]
    no_promotion = shared["promoted_variant"] == "None" and all(payload["controls"]["no_variant_promoted"] is True for payload in payloads.values())
    gates = {
        "legs_exit_0_by_receipt": gate(all(payload["all_pass"] is True for payload in payloads.values()), "legs_exit_0_by_receipt", {k: v["all_pass"] for k, v in payloads.items()}),
        "pin_identical": gate(len(pin_hashes) == 1 and next(iter(pin_hashes)) == sha256_text(PIN_SPEC), "pin_identical", sorted(pin_hashes)),
        "source_sha256_present": gate(source_hashes_present, "source_sha256_present", {k: v["source_sha256"] for k, v in payloads.items()}),
        "ceiling_exact": gate(ceilings_exact, "ceiling_exact", {k: v["classification"] for k, v in payloads.items()}),
        "blind_diff_all_pass": gate(all(payload["blind_diff"]["pass"] is True for payload in payloads.values()) and len(blind_hashes) == 1, "blind_diff_all_pass", blind_checks),
        "arrow_types_named_allowed": gate(arrow_types_allowed, "arrow_types_named_allowed", arrow_types),
        "raw_value_smt_tripwires": gate(raw_smt_ok, "raw_value_smt_tripwires", {"julia": julia_proof, "jax": jax_proofs, "pytorch": pytorch_proofs}),
        "divergence_zero": gate(div["max_divergence"] == 0, "divergence_zero", div),
        "no_variant_promoted": gate(no_promotion, "no_variant_promoted", {k: v["shared_scalars"]["promoted_variant"] for k, v in payloads.items()}),
    }
    all_pass = all(item["pass"] for item in gates.values())
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "The inter-rung/inter-stage nesting relations are computed as a family of nesting maps with embedding, trace, arrow-order, and quotient-chain variants compared; no variant is promoted.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": payloads["julia"]["source_sha256"],
            "receipt_path": payloads["julia"]["result_path"],
            "proof_tag": "nesting_family_cliffordalgebras_z3_raw_value",
            "proof_pass": payloads["julia"]["all_pass"],
            "table_version": SIM_ID,
            "bracket_convention": "Hermitian Pauli Jordan-Wigner generators; Gamma_m=(-i)^m product gamma_1..gamma_2m",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": payloads["julia"].get("julia_project"), "packages": payloads["julia"]["packages_used"], "role": "CliffordAlgebras/Z3 semantic receipt"},
            "jax": {"packages": payloads["jax"]["packages_used"], "role": "SymPy plus z3/cvc5 exact SMT lane with JAX x64 marker"},
            "pytorch": {"packages": payloads["pytorch"]["packages_used"], "role": "torch.func exact tensor gate plus SymPy/z3/cvc5 lane"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": collect_claim_tools(payloads),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {
            "julia": engine_record(payloads["julia"], JULIA_RESULT),
            "jax": engine_record(payloads["jax"], JAX_RESULT),
            "pytorch": engine_record(payloads["pytorch"], PYTORCH_RESULT),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "julia_ghz": julia_proof["ghz_pure_nesting_forced_equality"],
                    "jax_ghz": jax_proofs["z3"]["ghz_pure_nesting_forced_equality"],
                    "pytorch_ghz": pytorch_proofs["z3"]["ghz_pure_nesting_forced_equality"],
                    "w_weight": jax_proofs["z3"]["w4_weight_negation"],
                    "can_fail": jax_proofs["z3"]["can_fail_wrong_weight_control"],
                },
            },
            "cvc5": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "jax_ghz": jax_proofs["cvc5"]["ghz_pure_nesting_forced_equality"],
                    "pytorch_ghz": pytorch_proofs["cvc5"]["ghz_pure_nesting_forced_equality"],
                    "w_weight": jax_proofs["cvc5"]["w4_weight_negation"],
                    "can_fail": jax_proofs["cvc5"]["can_fail_wrong_weight_control"],
                },
            },
            "julia_z3": {
                "ran": True,
                "verdict": julia_proof["ghz_pure_nesting_forced_equality"],
                "load_bearing": True,
                "control": julia_proof["can_fail_wrong_weight_control"],
            },
        },
        "family_comparison": payloads["jax"]["receipts"]["F5_family_comparison"],
        "blind_diff": {"hashes": sorted(blind_hashes), "checks": blind_checks},
        "build_gates": gates,
        "divergence": div,
        "engine_result_paths": {engine: payload["result_path"] for engine, payload in payloads.items()},
        "claim_boundary": {
            "ceiling": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "not_claimed": "no canonical nesting variant, no rung promotion, no bridge/axis-level claim",
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "engine": "envelope", "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
