#!/usr/bin/env python3
"""Envelope for the G2 forced-vs-installed discriminator."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
OBJECT_ID = "g2_forced_vs_installed_discriminator"
SIM_DIR = ROOT / "system_v6" / "sims" / OBJECT_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{OBJECT_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{OBJECT_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{OBJECT_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{OBJECT_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{OBJECT_ID}_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from standalone Julia, JAX, and PyTorch receipts",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding for requested v6 sim files",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source hashing",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive", "hashlib": "supportive"}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "values": payload["shared_scalars"],
        "derivation_dimensions": payload["derivation_dimensions"],
        "controls": payload["controls"],
        "verdicts": payload["verdicts"],
    }


def max_divergence(engine_values: dict[str, dict[str, float]]) -> tuple[float, str | None]:
    keys = sorted(set.intersection(*(set(values.keys()) for values in engine_values.values())))
    max_seen = 0.0
    max_key = None
    for key in keys:
        rows = [float(values[key]) for values in engine_values.values()]
        diff = max(rows) - min(rows)
        if diff > max_seen:
            max_seen = diff
            max_key = key
    return max_seen, max_key


def all_same(payloads: dict[str, dict[str, Any]], path: list[str], expected: Any | None = None) -> bool:
    values = []
    for payload in payloads.values():
        value: Any = payload
        for key in path:
            value = value[key]
        values.append(value)
    if expected is not None:
        return all(value == expected for value in values)
    return len(set(json.dumps(value, sort_keys=True) for value in values)) == 1


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payloads = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    engine_values = {name: payload["shared_scalars"] for name, payload in payloads.items()}
    divergence_max, divergence_key = max_divergence(engine_values)
    jax_z3 = payloads["jax"]["smt"]["z3"]
    jax_cvc5 = payloads["jax"]["smt"]["cvc5"]
    julia_z3 = payloads["julia"]["smt"]["julia_z3"]

    h_root_pass = all_same(payloads, ["shared_scalars", "H_root_sat"], 1.0)
    m2_root_pass = all_same(payloads, ["shared_scalars", "M2R_root_sat"], 1.0)
    o_dim_14 = all_same(payloads, ["derivation_dimensions", "O", "nullity_dim_der"], 14)
    h_dim_3 = all_same(payloads, ["derivation_dimensions", "H", "nullity_dim_der"], 3)
    m2_dim_3 = all_same(payloads, ["derivation_dimensions", "M2R", "nullity_dim_der"], 3)
    corrupt_changes = all(payload["controls"]["corrupted_octonion_dim_changes"] is True for payload in payloads.values())
    alt_excluded = (
        jax_z3["alternative_3unit_7closure"]["status"]
        == jax_cvc5["alternative_3unit_7closure"]["status"]
        == julia_z3["alternative_3unit_7closure"]["status"]
        == "unsat"
    )
    h_excluded_under_installed = (
        jax_z3["H_7unit_closure"]["status"]
        == jax_cvc5["H_7unit_closure"]["status"]
        == julia_z3["H_7unit_closure"]["status"]
        == "unsat"
    )
    o_installed_sat = (
        jax_z3["O_7unit_closure"]["status"]
        == jax_cvc5["O_7unit_closure"]["status"]
        == julia_z3["O_7unit_closure"]["status"]
        == "sat"
    )
    erased_readmits_h = all(payload["controls"]["erased_closure_readmits_H"] is True for payload in payloads.values())
    forced_by_root = not (h_root_pass and m2_root_pass and h_dim_3 and m2_dim_3 and o_dim_14)
    installed_by_carrier_constraint = bool(o_dim_14 and o_installed_sat and alt_excluded and h_excluded_under_installed)

    controls = {
        "all_engine_legs_passed": all(payload["all_pass"] is True for payload in payloads.values()),
        "same_shared_scalars": divergence_max == 0.0,
        "bare_root_failing_control_fires": forced_by_root is False and h_root_pass and m2_root_pass,
        "erased_constraint_drop_closure_readmits_H": erased_readmits_h,
        "corrupted_octonion_table_changes_dim_der": corrupt_changes,
        "classification_ceiling_held": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False,
    }
    all_pass = bool(
        all(controls.values())
        and forced_by_root is False
        and installed_by_carrier_constraint is True
        and all_same(payloads, ["controls", "forced_commutative_control_unsat"], True)
    )

    sat_table = {
        "bare_root_lane": {
            "H_root_z3": jax_z3["H_bare_root"]["status"],
            "H_root_cvc5": jax_cvc5["H_bare_root"]["status"],
            "H_root_julia_z3": julia_z3["H_bare_root"]["status"],
            "M2R_root_z3": jax_z3["M2R_bare_root"]["status"],
            "M2R_root_cvc5": jax_cvc5["M2R_bare_root"]["status"],
            "M2R_root_julia_z3": julia_z3["M2R_bare_root"]["status"],
        },
        "installed_lane": {
            "O_7unit_closure_z3": jax_z3["O_7unit_closure"]["status"],
            "O_7unit_closure_cvc5": jax_cvc5["O_7unit_closure"]["status"],
            "O_7unit_closure_julia_z3": julia_z3["O_7unit_closure"]["status"],
            "H_7unit_closure_z3": jax_z3["H_7unit_closure"]["status"],
            "H_7unit_closure_cvc5": jax_cvc5["H_7unit_closure"]["status"],
            "H_7unit_closure_julia_z3": julia_z3["H_7unit_closure"]["status"],
            "alternative_3unit_7closure_z3": jax_z3["alternative_3unit_7closure"]["status"],
            "alternative_3unit_7closure_cvc5": jax_cvc5["alternative_3unit_7closure"]["status"],
            "alternative_3unit_7closure_julia_z3": julia_z3["alternative_3unit_7closure"]["status"],
        },
        "controls": {
            "H_erased_closure_z3": jax_z3["H_erased_closure_control"]["status"],
            "H_erased_closure_cvc5": jax_cvc5["H_erased_closure_control"]["status"],
            "H_erased_closure_julia_z3": julia_z3["H_erased_closure_control"]["status"],
            "H_forced_commutative_z3": jax_z3["H_forced_commutative_control"]["status"],
            "H_forced_commutative_cvc5": jax_cvc5["H_forced_commutative_control"]["status"],
            "H_forced_commutative_julia_z3": julia_z3["H_forced_commutative_control"]["status"],
        },
    }

    return {
        "schema_version": "three_engine_sim_result_v1",
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "reads_peer_result": False,
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "object_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "reads_peer_result": False,
        "reads_engine_result_jsons": True,
        "claim_ceiling": "scratch diagnostic only: G2 forced-vs-installed discriminator, no promotion or canonical admission.",
        "all_pass": all_pass,
        "M": {
            "question": "Is G2=Aut(O)=Der(O), dim 14, forced by the bare root constraints or installed by the octonion carrier constraint?",
            "bare_root_constraints": ["finite multiplication table", "nonzero commutator/order-sensitivity witness"],
            "installed_carrier_constraint": "7 anticommuting imaginary units with Fano/Cayley-Dickson closure (Cl(6)/3-qubit-floor family)",
            "candidate_carriers": ["H", "M2R", "O"],
        },
        "derivation_dimensions": {
            engine: payload["derivation_dimensions"] for engine, payload in payloads.items()
        },
        "noncommutation_witnesses": {
            engine: payload["noncommutation_witnesses"] for engine, payload in payloads.items()
        },
        "sat_table": sat_table,
        "decision": {
            "forced_by_root": forced_by_root,
            "installed_by_carrier_constraint": installed_by_carrier_constraint,
            "forced_vs_installed_verdict": "INSTALLED_NOT_FORCED" if (not forced_by_root and installed_by_carrier_constraint) else "UNRESOLVED",
            "evidence_chain_for_forced_by_root_false": [
                "H bare-root SAT in z3/cvc5/Julia-Z3",
                "M2(R) bare-root SAT in z3/cvc5/Julia-Z3",
                "dim Der(H)=3 and dim Der(M2R)=3 in all engines",
                "dim Der(O)=14 in all engines",
                "therefore the bare root admits non-G2 symmetry carriers",
            ],
            "evidence_chain_for_installed_by_carrier_constraint_true": [
                "O seven-unit Fano/Cayley-Dickson closure SAT in z3/cvc5/Julia-Z3",
                "3-unit alternative under seven-unit closure UNSAT in z3/cvc5/Julia-Z3",
                "H under seven-unit closure UNSAT in z3/cvc5/Julia-Z3",
                "dim Der(O)=14 computed by Julia, JAX, and PyTorch derivation linear systems",
            ],
        },
        "negative_control_flip": {
            "erased_constraint_drop_closure": {
                "description": "Dropping the seven-unit closure leaves only the bare finite+noncommutative root and readmits H.",
                "z3": jax_z3["H_erased_closure_control"]["status"],
                "cvc5": jax_cvc5["H_erased_closure_control"]["status"],
                "julia_z3": julia_z3["H_erased_closure_control"]["status"],
                "flips_to_sat": erased_readmits_h,
            },
            "corrupted_octonion_table": {
                "description": "Flip one Fano product e1*e2 coefficient; recompute Der dimension.",
                "dims": {engine: payload["derivation_dimensions"]["O_corrupted"]["nullity_dim_der"] for engine, payload in payloads.items()},
                "changes_away_from_14": corrupt_changes,
            },
            "force_commutativity_control": {
                "description": "Forcing H commutative while retaining the bare noncommutation root is UNSAT.",
                "z3": jax_z3["H_forced_commutative_control"]["status"],
                "cvc5": jax_cvc5["H_forced_commutative_control"]["status"],
                "julia_z3": julia_z3["H_forced_commutative_control"]["status"],
            },
        },
        "engine_result_paths": {
            "julia": str(JULIA_RESULT),
            "jax": str(JAX_RESULT),
            "pytorch": str(PYTORCH_RESULT),
        },
        "engines": {
            "julia": engine_record(payloads["julia"], JULIA_RESULT),
            "jax": engine_record(payloads["jax"], JAX_RESULT),
            "pytorch": engine_record(payloads["pytorch"], PYTORCH_RESULT),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": jax_z3["alternative_3unit_7closure"]["status"],
                "claim": "A 3-imaginary-unit carrier cannot satisfy the installed seven-unit closure constraint; bare-root H/M2R remain SAT.",
                "H_bare_root_verdict": jax_z3["H_bare_root"]["status"],
                "M2R_bare_root_verdict": jax_z3["M2R_bare_root"]["status"],
                "O_7unit_closure_verdict": jax_z3["O_7unit_closure"]["status"],
                "H_7unit_closure_verdict": jax_z3["H_7unit_closure"]["status"],
                "alternative_3unit_7closure_verdict": jax_z3["alternative_3unit_7closure"]["status"],
                "erased_closure_control_verdict": jax_z3["H_erased_closure_control"]["status"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": jax_cvc5["alternative_3unit_7closure"]["status"],
                "claim": "Independent cvc5 check of the same seven-unit exclusion and bare-root SAT controls.",
                "H_bare_root_verdict": jax_cvc5["H_bare_root"]["status"],
                "M2R_bare_root_verdict": jax_cvc5["M2R_bare_root"]["status"],
                "O_7unit_closure_verdict": jax_cvc5["O_7unit_closure"]["status"],
                "H_7unit_closure_verdict": jax_cvc5["H_7unit_closure"]["status"],
                "alternative_3unit_7closure_verdict": jax_cvc5["alternative_3unit_7closure"]["status"],
                "erased_closure_control_verdict": jax_cvc5["H_erased_closure_control"]["status"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia_z3["alternative_3unit_7closure"]["status"],
                "claim": "Julia Z3.jl mirrors the cardinality/closure-side exclusion and bare-root controls.",
                "H_bare_root_verdict": julia_z3["H_bare_root"]["status"],
                "M2R_bare_root_verdict": julia_z3["M2R_bare_root"]["status"],
                "O_7unit_closure_verdict": julia_z3["O_7unit_closure"]["status"],
                "H_7unit_closure_verdict": julia_z3["H_7unit_closure"]["status"],
                "alternative_3unit_7closure_verdict": julia_z3["alternative_3unit_7closure"]["status"],
                "erased_closure_control_verdict": julia_z3["H_erased_closure_control"]["status"],
            },
        },
        "claim_path_tools": ["Z3", "z3", "cvc5"],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": divergence_max,
            "max_divergence_key": divergence_key,
        },
        "controls": controls,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"forced_by_root={str(result['decision']['forced_by_root']).lower()} "
        f"installed={str(result['decision']['installed_by_carrier_constraint']).lower()} "
        f"dims={{H:{result['derivation_dimensions']['julia']['H']['nullity_dim_der']},"
        f"M2R:{result['derivation_dimensions']['julia']['M2R']['nullity_dim_der']},"
        f"O:{result['derivation_dimensions']['julia']['O']['nullity_dim_der']},"
        f"O_corrupted:{result['derivation_dimensions']['julia']['O_corrupted']['nullity_dim_der']}}} "
        f"max_divergence={result['divergence']['max_divergence']} "
        f"validator_target={RESULT_PATH}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
