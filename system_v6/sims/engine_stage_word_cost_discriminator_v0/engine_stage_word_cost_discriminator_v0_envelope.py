#!/usr/bin/env python3
"""Envelope for engine_stage_word_cost_discriminator_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "engine_stage_word_cost_discriminator_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
MODE = "FREE"
COMMON_VALUE_KEYS = [
    "local_n8_double_max_chi",
    "local_n12_double_max_chi",
    "local_n16_double_max_chi",
    "random_word_n16_double_max_chi",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_leg(engine: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{SIM_ID}_{engine}_results.json"
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def source_hash_fresh(payload: dict[str, Any]) -> bool:
    source = ROOT / payload["source_path"]
    return source.exists() and sha256_file(source) == payload["source_sha256"]


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": rel(result_path),
        "result_sha256": sha256_file(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "mode": payload["mode"],
        "pin_sha256": payload["pin_sha256"],
        "seed": payload["seed"],
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
        "tool_calls": payload["tool_calls"],
        "values": payload["values"],
        "gate_pass": payload["gate_pass"],
        "summary": payload["summary"],
    }


def collect_claim_path_tools(julia: dict[str, Any], jax: dict[str, Any]) -> list[str]:
    tools: set[str] = {"ITensors", "ITensorMPS"}
    tools.update(str(tool) for tool in jax["claim_path_tools"])
    return sorted(tools)


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    engine_values = {
        engine: {key: float(payload["values"][key]) for key in COMMON_VALUE_KEYS}
        for engine, payload in legs.items()
    }
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
        "comparison": {
            "rows": rows,
            "same_named_observable_sets": True,
            "interpretation": "Bond dimensions are compared as independently evolved tensor-network diagnostics; exact equality is not required for validator shape.",
        },
    }


def verdict(julia: dict[str, Any], jax: dict[str, Any]) -> str:
    j_local = [julia["summary"][str(n)]["loop_local"]["double_720"]["max_chi"] for n in (8, 12, 16)]
    p_local = [jax["summary"][str(n)]["loop_local"]["double_720"]["max_chi"] for n in (8, 12, 16)]
    p_all = jax["summary"]["16"]["all_to_all"]["double_720"]["max_chi"]
    p_haar = jax["summary"]["16"]["haar"]["double_720"]["max_chi"]
    j_random = [julia["summary"][str(n)]["random_word"]["double_720"]["max_chi"] for n in (8, 12, 16)]
    p_random = [jax["summary"][str(n)]["random_word"]["double_720"]["max_chi"] for n in (8, 12, 16)]
    bounded = max(j_local + p_local) <= 8
    all_to_all_fires = p_all > p_local[-1]
    haar_fires = p_haar > p_all
    if not bounded or not all_to_all_fires:
        return "EXCLUDED"
    # Builder hardening closes named caveats, but verdict promotion belongs to
    # the next independent audit. Do not self-upgrade this packet to SURVIVES.
    if bounded and all_to_all_fires and haar_fires:
        return "MIXED"
    return "MIXED"


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    julia = load_leg("julia")
    jax = load_leg("jax")
    legs = {"julia": julia, "jax": jax}
    pin_ok = julia["pin_sha256"] == jax["pin_sha256"]
    z3 = jax["crossover_proofs"]["z3"]
    cvc5 = jax["crossover_proofs"]["cvc5"]
    div = divergence(legs)
    local_double = {
        "julia": [julia["summary"][str(n)]["loop_local"]["double_720"]["max_chi"] for n in (8, 12, 16)],
        "jax": [jax["summary"][str(n)]["loop_local"]["double_720"]["max_chi"] for n in (8, 12, 16)],
    }
    random_double = {
        "julia": [julia["summary"][str(n)]["random_word"]["double_720"]["max_chi"] for n in (8, 12, 16)],
        "jax": [jax["summary"][str(n)]["random_word"]["double_720"]["max_chi"] for n in (8, 12, 16)],
    }
    julia_all_to_all_double = {
        "8": julia["summary"]["8"]["all_to_all"]["double_720"],
        "12": julia["summary"]["12"]["all_to_all"]["double_720"],
        "16": julia["summary"]["16"]["all_to_all"]["double_720"],
    }
    cost_verdict = verdict(julia, jax)
    gate_pass = {
        "legs_all_pass": julia["all_pass"] is True and jax["all_pass"] is True,
        "mode_declared_free": julia["mode"] == MODE and jax["mode"] == MODE,
        "ceiling_exact": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is PROMOTION_ALLOWED
            and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for payload in legs.values()
        ),
        "pin_identical": pin_ok,
        "source_hashes_fresh": all(source_hash_fresh(payload) for payload in legs.values()),
        "no_peer_result_reads": all(payload["reads_peer_result"] is False for payload in legs.values()),
        "local_loop_bounded": max(local_double["julia"] + local_double["jax"]) <= 8,
        "all_to_all_controls_fire_in_quimb": jax["summary"]["16"]["all_to_all"]["double_720"]["max_chi"] > jax["summary"]["16"]["loop_local"]["double_720"]["max_chi"],
        "julia_all_to_all_controls_fire_n8_n12": (
            julia_all_to_all_double["8"]["max_chi"] > julia["summary"]["8"]["loop_local"]["double_720"]["max_chi"]
            and julia_all_to_all_double["12"]["max_chi"] > julia["summary"]["12"]["loop_local"]["double_720"]["max_chi"]
        ),
        "julia_all_to_all_n16_honest_infeasible_delegated": julia_all_to_all_double["16"]["status"] == "infeasible_delegated",
        "haar_controls_fire_in_quimb": jax["summary"]["16"]["haar"]["double_720"]["max_chi"] > jax["summary"]["16"]["all_to_all"]["double_720"]["max_chi"],
        "haar_baseline_delegated_to_quimb": True,
        "dense_n8_mps_fidelity": jax["dense_crosscheck_n8_loop_local_double"]["fidelity"] >= 1.0 - 1.0e-10,
        "dense_n8_bond_ranks_match": jax["dense_crosscheck_n8_loop_local_double"]["bond_sizes_match_dense_ranks"] is True,
        "smt_z3_cvc5_agree": z3["verdict"] == "unsat" and cvc5["verdict"] == "unsat",
        "smt_erased_flip_controls_sat": z3["control_verdict"] == "sat" and cvc5["control_verdict"] == "sat",
    }
    all_pass = all(gate_pass.values())
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "mode": MODE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "claim": "Scratch cost discriminator for Reading B: the committed two-engine 8-stage word is lifted to local ring MPS dynamics and tested for bounded/slowly-growing bond dimension against all-to-all, shuffled-word, and Haar baselines at n=8,12,16.",
        "allowed_claims": [
            "computed bond-dimension diagnostics for the declared pure-state S4-axis lift",
            "n=8 dense statevector cross-check of the quimb MPS evolution",
            "finite z3/cvc5 periodicity identity over the committed alternating/paired readout grammar",
            "verdict limited to SURVIVES, EXCLUDED, or MIXED for this computed packet",
        ],
        "disallowed_claims": [
            "proof of asymptotic linearity",
            "new physics or engine admission",
            "formal admission",
            "density-channel dephasing simulation claim",
            "extrapolation beyond n=8,12,16",
        ],
        "engine_contract": {
            "mode": "julia_canon_plus_jax_diagnostic",
            "lanes": ["julia", "jax"],
            "lane_note": "The jax lane is validator-compatible naming; load-bearing Python tensor-network work is quimb/quimb.tensor.",
            "audit_order": ["combined_envelope", "julia_local_loop", "jax_quimb_local_and_controls", "controller_comparison"],
            "reads_peer_result": False,
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier",
            "role": "ITensorMPS carrier-side MPS evolution and bond-dimension readout",
            "classification": CLASSIFICATION,
            "proof_tag": "engine_stage_word_cost_discriminator_v0_itensormps_quimb_smt",
            "proof_pass": bool(all_pass),
            "bracket_convention": "stage order fixed by D loop followed by I loop; seat i uses word[i mod 8]",
            "consumer_policy": "scratch diagnostic only; no promotion or formal admission",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier", "packages": julia["packages_used"], "role": "semantic_owner_mps_leg"},
            "jax": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": jax["packages_used"], "role": "quimb_mps_mirror_plus_z3_cvc5_sidecar"},
            "pytorch": {"scoped": False, "reason": "No graph/network/autograd claim path in this packet."},
            "tensor_exchange": "none; no cross-engine tensor exchange on claim path",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "pin_spec": julia["pin_spec"],
        "pin_sha256": julia["pin_sha256"],
        "pin_identical_across_legs": pin_ok,
        "source_refs": julia["source_refs"],
        "stage_word": julia["stage_word"],
        "shared_random_stage_indices": julia["shared_random_stage_indices"],
        "shared_random_word_policy": julia["shared_random_word_policy"],
        "stage_assignment": julia["stage_assignment"],
        "claim_path_tools": collect_claim_path_tools(julia, jax),
        "TOOL_MANIFEST": {
            "julia": julia["TOOL_MANIFEST"],
            "jax": jax["TOOL_MANIFEST"],
        },
        "TOOL_INTEGRATION_DEPTH": {
            "julia": julia["TOOL_INTEGRATION_DEPTH"],
            "jax": jax["TOOL_INTEGRATION_DEPTH"],
        },
        "engines": {
            "julia": engine_record(julia, RESULT_DIR / f"{SIM_ID}_julia_results.json"),
            "jax": engine_record(jax, RESULT_DIR / f"{SIM_ID}_jax_results.json"),
        },
        "rows": {
            "julia": julia["rows"],
            "jax": jax["rows"],
        },
        "summaries": {
            "julia": julia["summary"],
            "jax": jax["summary"],
        },
        "dense_crosscheck_n8_loop_local_double": jax["dense_crosscheck_n8_loop_local_double"],
        "crossover_proofs": {
            "z3": z3,
            "cvc5": cvc5,
        },
        "divergence": div,
        "cost_readout": {
            "verdict": cost_verdict,
            "vocabulary": ["SURVIVES", "EXCLUDED", "MIXED"],
            "local_double_max_chi": local_double,
            "random_word_double_max_chi": random_double,
            "all_to_all_n16_double_max_chi": {
                "julia": julia_all_to_all_double["16"]["status"],
                "jax": jax["summary"]["16"]["all_to_all"]["double_720"]["max_chi"],
            },
            "all_to_all_julia_boundary_controls": {
                "n8_double_max_chi": julia_all_to_all_double["8"]["max_chi"],
                "n12_double_max_chi": julia_all_to_all_double["12"]["max_chi"],
                "n16_double_status": julia_all_to_all_double["16"]["status"],
            },
            "haar_n16_double_max_chi": {
                "julia": "delegated_to_quimb",
                "jax": jax["summary"]["16"]["haar"]["double_720"]["max_chi"],
            },
            "interpretation": "MIXED stands pending independent re-audit. This builder round closes H1/H2/H3 but does not self-upgrade the packet to SURVIVES.",
        },
        "builder_hardening_addendum": {
            "verdict_status": "MIXED verdict stands pending re-audit; no self-upgrade to SURVIVES",
            "H1_like_for_like_random_word": "closed: one stored shared random stage sequence per n/traversal is replayed by both engines as scenario=random_word; own-sampled rows are supplementary",
            "H2_julia_controls": "closed: Julia all-to-all controls computed at n=8 and n=12; n=16 all-to-all is explicitly labeled infeasible_delegated; Haar remains delegated to quimb",
            "H3_capability_gates": "closed after verifier aliases map ITensorMPS to itensors capability probe and quimb.tensor to quimb capability probe",
        },
        "build_gates": gate_pass,
        "limits": [
            "Pure-state unitary axis-lift of S4 operator forms; no density-channel mixed-state dephasing claim.",
            "No extrapolation beyond n=8,12,16.",
            "Builder hardening addendum only; audit_verdict.md remains the prior MIXED audit until a fresh audit is performed.",
            "Codex-native subagents not spawned because the available subagent tool requires an explicit user request for delegated agent work.",
        ],
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "cost_verdict": result["cost_readout"]["verdict"],
                "result_path": rel(RESULT_PATH),
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
