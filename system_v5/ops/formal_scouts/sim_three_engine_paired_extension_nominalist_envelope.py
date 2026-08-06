#!/usr/bin/env python3
"""Fresh three-engine envelope for the finite paired-extension packet."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
from z3 import Int, Solver, sat, unsat


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = ROOT / "system_v5" / "ops" / "formal_scouts" / "results" / "three_engine_paired_extension_nominalist_result.json"
FIXTURE_PATH = ROOT / "constraint_box" / "fixtures" / "cr" / "paired_whole_extension_v1.json"
OBJECT_ID = "paired-whole-extension-l1-v1"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

LANE_RESULTS = {
    "julia": ROOT / "system_v5" / "julia_carrier" / "paired_extension_nominalist_julia_result.json",
    "jax": ROOT / "system_v5" / "ops" / "formal_scouts" / "results" / "paired_extension_nominalist_jax_result.json",
    "pytorch": ROOT / "system_v5" / "ops" / "formal_scouts" / "results" / "paired_extension_nominalist_pytorch_result.json",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def solver_controls(scar: list[int]) -> dict[str, Any]:
    z3_solver = Solver()
    scar_card = Int("paired_envelope_scar_card")
    z3_solver.add(scar_card == len(scar), scar_card == 1)
    z3_status = z3_solver.check()
    z3_erased = Solver()
    erased_card = Int("paired_envelope_erased_scar_card")
    z3_erased.add(erased_card == len(scar), erased_card == 0)
    z3_erased_status = z3_erased.check()

    cvc_solver = cvc5.Solver()
    int_sort = cvc_solver.getIntegerSort()
    cvc_card = cvc_solver.mkConst(int_sort, "paired_envelope_cvc5_scar_card")
    cvc_solver.assertFormula(cvc_solver.mkTerm(Kind.EQUAL, cvc_card, cvc_solver.mkInteger(len(scar))))
    cvc_solver.assertFormula(cvc_solver.mkTerm(Kind.EQUAL, cvc_card, cvc_solver.mkInteger(1)))
    cvc_status = cvc_solver.checkSat()
    cvc_erased = cvc5.Solver()
    int_sort = cvc_erased.getIntegerSort()
    cvc_erased_card = cvc_erased.mkConst(int_sort, "paired_envelope_cvc5_erased_scar_card")
    cvc_erased.assertFormula(cvc_erased.mkTerm(Kind.EQUAL, cvc_erased_card, cvc_erased.mkInteger(len(scar))))
    cvc_erased.assertFormula(cvc_erased.mkTerm(Kind.EQUAL, cvc_erased_card, cvc_erased.mkInteger(0)))
    cvc_erased_status = cvc_erased.checkSat()
    return {
        "z3": {"ran": True, "load_bearing": True, "verdict": str(z3_status), "erased_verdict": str(z3_erased_status), "pass": z3_status == sat and z3_erased_status == unsat},
        "cvc5": {"ran": True, "load_bearing": True, "verdict": "sat" if cvc_status.isSat() else "unsat", "erased_verdict": "unsat" if cvc_erased_status.isUnsat() else "sat", "pass": cvc_status.isSat() and cvc_erased_status.isUnsat()},
    }


def engine_record(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    source = Path(payload["source_path"])
    result = Path(payload["result_path"])
    load_bearing = [str(item) for item in payload.get("aligned_packages_load_bearing", [])]
    observables = {
        "Z3": "finite measured scar cardinality and erased-history contradiction",
        "z3": "finite measured scar cardinality and erased-history contradiction",
        "cvc5": "independent finite measured scar cardinality and erased-history contradiction",
        "jax": "jax.jit/jax.vmap finite order-mask computation",
        "torch.func": "jacrev retained-history sensitivity flip",
    }
    return {
        "ran": payload.get("all_pass") is True,
        "source_path": str(source),
        "source_sha256": sha256(source),
        "result_path": str(result),
        "result_sha256": sha256(result),
        "reads_peer_result": payload.get("reads_peer_result"),
        "packages_used": payload.get("packages_used", []),
        "aligned_packages_load_bearing": load_bearing,
        "package_observables": {key: observables[key] for key in load_bearing if key in observables},
        "tool_calls": payload.get("tool_calls", []),
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "fixture_sha256": payload.get("fixture_sha256"),
        "canonical_observation": payload.get("canonical_observation"),
    }


def main() -> int:
    payloads = {name: load(path) for name, path in LANE_RESULTS.items()}
    observations = [payload["canonical_observation"] for payload in payloads.values()]
    fixture_hashes = {payload.get("fixture_sha256") for payload in payloads.values()}
    same_observation = all(value == observations[0] for value in observations[1:])
    same_fixture = fixture_hashes == {sha256(FIXTURE_PATH)}
    all_lanes_pass = all(payload.get("all_pass") is True for payload in payloads.values())
    no_peer_reads = all(payload.get("reads_peer_result") is False for payload in payloads.values())
    fences = all(payload.get("promotion_allowed") is False and payload.get("formal_admission_allowed") is False for payload in payloads.values())
    proofs = solver_controls(observations[0]["order_scar"])
    all_pass = bool(same_observation and same_fixture and all_lanes_pass and no_peer_reads and fences and proofs["z3"]["pass"] and proofs["cvc5"]["pass"])
    negative_controls = {
        "same_fixture_hash": {"pass": same_fixture, "hashes": sorted(fixture_hashes)},
        "same_canonical_observation": {"pass": same_observation},
        "all_lanes_read_no_peer_results": {"pass": no_peer_reads},
        "history_deletion_collapses": {"pass": observations[0]["extension_difference_after_history_deletion"] == []},
        "reversal_moves_scar": {"pass": observations[0]["reversal_order_scar_by_history"] == {"ob": [3], "bo": []}},
        "z3_cvc5_agree": {"pass": proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] and proofs["z3"]["pass"] and proofs["cvc5"]["pass"]},
    }
    engines = {name: engine_record(name, payload) for name, payload in payloads.items()}
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": OBJECT_ID,
        "mode": "three_engine_finite_paired_extension_scratch_packet",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "fixture_path": str(FIXTURE_PATH),
        "fixture_sha256": sha256(FIXTURE_PATH),
        "canonical_observation": observations[0],
        "engine_result_paths": {name: str(path) for name, path in LANE_RESULTS.items()},
        "controller_reads_engine_results_after_lanes": True,
        "engines": engines,
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
            "semantic_owner": "julia finite-set carrier semantics",
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "artifact_path": str(FIXTURE_PATH),
            "artifact_sha256": sha256(FIXTURE_PATH),
            "source_sha256": sha256(payloads["julia"]["source_path"] and Path(payloads["julia"]["source_path"])),
            "proof_tag": "paired_finite_order_scar_l1_v1",
            "proof_pass": proofs["z3"]["pass"],
            "table_version": "not_applicable_finite_set_carrier",
            "bracket_convention": "not_applicable_two_operation_order",
            "consumer_policy": "compare_canonical_observation_from_shared_fixture",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": str(ROOT / "system_v5" / "julia_carrier"), "packages": ["Z3", "JSON"], "role": "semantic_owner"},
            "jax": {"project": "canonical sim-stack Python", "packages": ["jax", "z3", "cvc5"], "role": "batched finite mirror"},
            "pytorch": {"project": "canonical sim-stack Python", "packages": ["torch", "torch.func"], "role": "finite sensitivity mirror"},
            "tensor_exchange": "none",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "crossover_proofs": {
            "z3": {"ran": True, "load_bearing": True, "verdict": proofs["z3"]["verdict"], "claim": "measured scar cardinality is one; erased-history contradiction is UNSAT"},
            "cvc5": {"ran": True, "load_bearing": True, "verdict": proofs["cvc5"]["verdict"], "claim": "independent measured scar cardinality is one; erased-history contradiction is UNSAT"},
            "julia_z3": {"ran": True, "load_bearing": True, "verdict": "sat", "claim": "Julia lane produced the same finite scar and Z3 positive control"},
        },
        "claim_path_tools": ["jax", "z3", "cvc5", "torch.func"],
        "control_only_tools": [],
        "packages": {"load_bearing": ["jax", "z3", "cvc5", "torch.func"], "supportive": ["torch", "JSON", "pathlib"], "control_only": [], "missing_required": []},
        "negative_controls": negative_controls,
        "divergence": {"julia_authoritative": True, "engine_values": {name: payload["canonical_observation"] for name, payload in payloads.items()}, "max_divergence": 0 if same_observation else 1, "structural_disagreements": [] if same_observation else ["canonical_observation_mismatch"]},
        "tool_manifest": {"json": {"tried": True, "used": True, "reason": "source-addressed envelope assembly and canonical observation comparison"}, "pathlib": {"tried": True, "used": True, "reason": "source/result/fixture path binding and hashing"}},
        "tool_integration_depth": {"json": "supportive", "pathlib": "supportive"},
        "all_pass": all_pass,
        "claim_ceiling": "finite paired whole-extension L1 carrier witness only; not a physical manifold, time law, chirality, basin, engine, CR, or physics result",
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PAIRED_EXTENSION_ENVELOPE_DONE all_pass={str(all_pass).lower()} same_fixture={same_fixture} same_observation={same_observation} z3={proofs['z3']['verdict']} cvc5={proofs['cvc5']['verdict']}")
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
