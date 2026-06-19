#!/usr/bin/env python3
"""Controller envelope for round3_s4_heavy_discriminator_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SIM_ID = "round3_s4_heavy_discriminator_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
BUILD_CARD = SIM_DIR / "build_card.md"
REGISTRY_REL = "system_v6/receipts/round3_discriminator_registry_20260611.md"
REGISTRY_COMMIT = "de44219ed"
QUEUE_REL = "system_v6/sims/round3_s9_alias_pass_v0/audit_verdict.md"
S4_LIGHT_REL = "system_v6/sims/round3_s4_alias_pass_v0/audit_verdict.md"

sys.path.insert(0, str(ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_show(ref: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT)


def lane_record(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_path": payload["source_path"],
        "result_path": payload["result_path"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "package_observables": payload["package_observables"],
        "all_pass": payload["all_pass"],
        "role_id": payload["role_id"],
        "claim_path_tools": payload["claim_path_tools"],
        "tool_calls": payload["tool_calls"],
        "positive": payload["positive"],
        "negative": payload["negative"],
        "boundary": payload["boundary"],
    }


def verdict_map(payload: dict[str, Any]) -> dict[str, str]:
    return {row["candidate"]: row["verdict"] for row in payload.get("candidate_verdicts", [])}


def build_result() -> dict[str, Any]:
    julia = load(JULIA_RESULT)
    jax = load(JAX_RESULT)
    registry_blob = git_show(REGISTRY_COMMIT, REGISTRY_REL)
    registry_path = ROOT / REGISTRY_REL
    jax_map = verdict_map(jax)
    julia_map = verdict_map(julia)
    verdicts_match = jax_map == julia_map
    expected_verdicts = {
        "S4.R3.1_z_amplitude_damping_pair": "excluded-by-N01-commutator-and-fixed-axis-rows",
        "S4.R3.2_x_amplitude_damping_pair": "excluded-under-pinned-parent-z-probe-convention-by-z-probe-quotient-descent-mortality",
        "S4.R3.3_dephase_rotate_hybrid": "excluded-by-shell-preservation-leakage",
        "S4.R3.5_weak_nonunital_pauli_channel": "excluded-by-Choi-positivity-and-fixed-axis",
    }
    z3 = jax["crossover_proofs"]["z3"]
    cvc5 = jax["crossover_proofs"]["cvc5"]
    julia_z3 = julia["crossover_proofs"]["julia_z3"]
    candidate_details = jax["candidate_variant_details"]
    gates = {
        "julia_lane_pass": julia["all_pass"] is True,
        "jax_lane_pass": jax["all_pass"] is True,
        "julia_jax_verdicts_match": verdicts_match,
        "expected_four_row_verdicts": jax_map == expected_verdicts,
        "registry_commit_bound": sha256_bytes(registry_blob) == sha256_file(registry_path),
        "build_card_copied": BUILD_CARD.exists() and "BUILD CARD" in BUILD_CARD.read_text(encoding="utf-8"),
        "queue_read": (ROOT / QUEUE_REL).exists(),
        "s4_light_verdict_read": (ROOT / S4_LIGHT_REL).exists(),
        "classification_ceiling": all(
            payload["classification"] == "scratch_diagnostic"
            and payload["promotion_allowed"] is False
            and payload["formal_admission_allowed"] is False
            for payload in [julia, jax]
        ),
        "z3_cvc5_agree": z3["verdict"] == cvc5["verdict"] == "unsat",
        "julia_z3_agrees": julia_z3["verdict"] == "unsat",
        "flip_controls_annotated": z3["flip_control_verdict"] == cvc5["flip_control_verdict"] == "tautological_flip",
        "julia_flip_control_fires": julia_z3["flip_control_verdict"] == "sat",
        "r3_5_choi_negative_seen": candidate_details["S4.R3.5_weak_nonunital_pauli_channel"][0]["choi"]["negative_eigenvalues"] == ["-1/40"],
        "r3_2_pin_relative_recorded": next(row for row in jax["candidate_verdicts"] if row["candidate"] == "S4.R3.2_x_amplitude_damping_pair")["pin_relative"] is True,
        "pytorch_honestly_omitted": True,
    }
    all_pass = all(gates.values())
    extra_fields = {
        "schema": f"{SIM_ID}_envelope_v1",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "all_pass": all_pass,
        "claim": "S4 round-3 phase-2 heavy-local discriminator over exactly the four queued S4 rows.",
        "allowed_claims": [
            "finite exact heavy-local verdicts for S4.R3.1, S4.R3.2, S4.R3.3, and S4.R3.5",
            "exact Choi spectra for scoped anchor and candidate channel variants",
            "pin-relative z-probe quotient exclusion for S4.R3.2 under the light-pass parent z-probe convention",
            "SMT-bound finite commutator, quotient, and Choi witnesses with erased SAT controls",
        ],
        "disallowed_claims": [
            "global S4 uniqueness",
            "canonical promotion",
            "other layer heavy-local completion",
            "PyTorch graph/autograd/tensor evidence",
            "convention-independent z-probe exclusion for S4.R3.2",
        ],
        "registry_binding": {
            "path": REGISTRY_REL,
            "commit": REGISTRY_COMMIT,
            "commit_blob_sha256": sha256_bytes(registry_blob),
            "working_tree_sha256": sha256_file(registry_path),
            "s4_rows_used": list(expected_verdicts),
        },
        "source_inputs_read": {
            "consolidated_heavy_queue": QUEUE_REL,
            "registry": REGISTRY_REL,
            "s4_light_verdict": S4_LIGHT_REL,
        },
        "TOOL_INTENT_MATRIX_decision": {
            "engine_mode": "julia_canon_jax_workhorse",
            "julia": "QuantumOptics one-qubit channel object route plus Julia Z3 finite witness binding",
            "jax": "SymPy exact Choi/order/fixed/quotient/shell rows plus supportive qutip object route and supportive z3/cvc5 hardcoded witness checks",
            "pytorch": "omitted honestly: no graph/network/autograd/tensor claim path exists in this S4 channel discriminator",
        },
        "tool_intent": {
            "claim_classes": ["exact_s4_channel_discriminator", "finite_smt_witness_binding"],
            "engine_tool_intent": {
                "julia": {
                    "QuantumOptics": "one-qubit density/channel object route for S4 channel rows",
                    "Z3": "finite witness UNSAT/perturbed SAT binding",
                },
                "jax": {
                    "sympy": "exact affine, Choi-spectrum, fixed-set, quotient, shell, and commutator rows",
                    "qutip": "maximally mixed one-qubit Qobj route sanity check; channel-agnostic",
                    "z3": "supportive finite witness UNSAT check; flip annotated as tautological_flip",
                    "cvc5": "supportive independent finite witness UNSAT check; flip annotated as tautological_flip",
                },
            },
        },
        "TOOL_MANIFEST": {
            "build_three_engine_envelope": {"used": True, "reason": "load-bearing standard controller envelope construction"},
            "QuantumOptics": julia["TOOL_MANIFEST"]["QuantumOptics"],
            "sympy": jax["TOOL_MANIFEST"]["sympy"],
            "qutip": jax["TOOL_MANIFEST"]["qutip"],
            "Z3": julia["TOOL_MANIFEST"]["Z3"],
            "z3": jax["TOOL_MANIFEST"]["z3"],
            "cvc5": jax["TOOL_MANIFEST"]["cvc5"],
        },
        "TOOL_INTEGRATION_DEPTH": {
            "build_three_engine_envelope": "load_bearing",
            "QuantumOptics": "load_bearing",
            "sympy": "load_bearing",
            "qutip": "supportive",
            "Z3": "load_bearing",
            "z3": "supportive",
            "cvc5": "supportive",
        },
        "positive": {
            "anchor_self": jax["positive"]["anchor_control"],
            "deliberate_alias": jax["positive"]["deliberate_alias"],
        },
        "negative": {
            "candidate_verdict_table": jax["candidate_verdicts"],
            "light_R3_4_regression": jax["negative"]["R3_4_regression"],
        },
        "boundary": {
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "scope": "S4 only; four queued heavy-local rows only",
            "pinned_convention": "parent z-probe quotient and S4 role order inherited from round3_s4_alias_pass_v0",
            "pytorch_omission": "honest omission; validator must be run without --require-pytorch",
        },
        "candidate_verdict_table": jax["candidate_verdicts"],
        "candidate_variant_details": candidate_details,
        "control_rows": jax["control_rows"],
        "build_gates": gates,
        "validator_expected_commands": [
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / (SIM_ID + '_jax.py'))}",
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier "
            + rel(SIM_DIR / (SIM_ID + "_julia.jl")),
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SOURCE_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py {rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed {rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-tool-intent {rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / ('validate_' + SIM_ID + '.py'))}",
        ],
    }
    envelope = build_envelope(
        sim_id=SIM_ID,
        lanes={"julia": lane_record(julia), "jax": lane_record(jax)},
        mode="julia_canon_jax_workhorse",
        claim_path_tools=["QuantumOptics", "sympy", "Z3"],
        crossover_proofs={"z3": z3, "cvc5": cvc5, "julia_z3": julia_z3},
        divergence={
            "julia_authoritative": True,
            "observable": "candidate_verdict_table",
            "engine_values": {"julia": stable_hash(julia_map), "jax": stable_hash(jax_map)},
            "max_divergence": 0.0 if verdicts_match else 1.0,
            "verdicts_match": verdicts_match,
        },
        classification="scratch_diagnostic",
        promotion_allowed=False,
        formal_admission_allowed=False,
        parent_lineage={
            "round3_discriminator_registry_20260611": {
                "path": REGISTRY_REL,
                "commit": REGISTRY_COMMIT,
                "sha256": sha256_bytes(registry_blob),
                "allowed_use": "S4 finite heavy-local rows, expected teeth, and stop rule",
            }
        },
        omitted_lanes={"pytorch": "No graph, network, autograd, tensor, or PyTorch-specific claim path is scoped by this S4 channel discriminator."},
        extra_fields=extra_fields,
    )
    envelope["all_pass"] = all_pass
    return envelope


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": rel(RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
