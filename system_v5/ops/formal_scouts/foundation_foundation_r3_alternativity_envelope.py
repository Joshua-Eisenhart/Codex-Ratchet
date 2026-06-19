#!/usr/bin/env python3
"""Composite envelope for foundation_r3_alternativity.

The envelope reads completed engine receipts only after the independent legs
have run. It does not recompute the leg claims or promote this scratch rung.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r3_alternativity"
OBJECT_ID = "foundation_foundation_r3_alternativity_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r3_alternativity_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_alternativity_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r3_alternativity_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_alternativity_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_alternativity_pytorch_results.json"
TOL = 1.0e-9

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from completed engine receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], *, result_path: Path, values: dict[str, Any]) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "values": values,
    }


def summary_values(payload: dict[str, Any]) -> dict[str, Any]:
    s = payload["summary"]
    return {
        "O_alternative": bool(s["O_alternative"]),
        "S_alternative": bool(s["S_alternative"]),
        "O_antisymmetry_max_norm": float(s["O_antisymmetry_max_norm"]),
        "S_antisymmetry_max_norm": float(s["S_antisymmetry_max_norm"]),
        "S_witness_pair": s["S_witness_pair"],
        "S_witness_basis_indices": s["S_witness_basis_indices"],
        "S_witness_vector": s["S_witness_vector"],
    }


def max_divergence(values: dict[str, dict[str, Any]]) -> float:
    keys = ["O_antisymmetry_max_norm", "S_antisymmetry_max_norm"]
    diffs = []
    for key in keys:
        rows = [float(row[key]) for row in values.values() if key in row]
        if rows:
            diffs.append(max(rows) - min(rows))
    return max(diffs) if diffs else 0.0


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    julia_values = summary_values(julia)
    jax_values = summary_values(jax)
    pytorch_values = {
        **summary_values(pytorch),
        "jacrev_alpha_0": float(pytorch["summary"]["jacrev_alpha_0"]),
        "jacrev_alpha_1": float(pytorch["summary"]["jacrev_alpha_1"]),
        "energy_alpha_0": float(pytorch["summary"]["energy_alpha_0"]),
        "energy_alpha_1": float(pytorch["summary"]["energy_alpha_1"]),
    }
    engine_values = {"julia": julia_values, "jax": jax_values, "pytorch": pytorch_values}
    div = max_divergence(engine_values)
    same_witness = julia_values["S_witness_pair"] == jax_values["S_witness_pair"] == pytorch_values["S_witness_pair"] and julia_values["S_witness_basis_indices"] == jax_values["S_witness_basis_indices"] == pytorch_values["S_witness_basis_indices"]
    z3_verdict = jax["crossover_proofs"]["z3"]["verdict"]
    cvc5_verdict = jax["crossover_proofs"]["cvc5"]["verdict"]
    negative = {
        "O_alternative_to_S_nonalternative_flip": bool(julia["negative_control_flip"]["O_alternative_to_S_nonalternative_flip"] and jax["negative_control_flip"]["O_alternative_to_S_nonalternative_flip"] and pytorch["negative_control_flip"]["O_alternative_to_S_nonalternative_flip"]),
        "drop_M_coarsens_quotient": bool(julia["negative_control_flip"]["drop_M_coarsens_quotient"] and jax["negative_control_flip"]["drop_M_coarsens_quotient"] and pytorch["negative_control_flip"]["drop_M_coarsens_quotient"]),
        "z3_O_unsat_to_erased_sat": bool(jax["negative_control_flip"]["z3_O_antisymmetry_violation_unsat_to_erased_sat"]),
        "cvc5_O_unsat_to_erased_sat": bool(jax["negative_control_flip"]["cvc5_O_antisymmetry_violation_unsat_to_erased_sat"]),
        "S_smt_sat_control": bool(jax["negative_control_flip"]["z3_S_antisymmetry_violation_sat"] and jax["negative_control_flip"]["cvc5_S_antisymmetry_violation_sat"]),
        "force_commutativity_changes_commutator_control": bool(julia["negative_control_flip"]["force_commutativity_changes_commutator_control"]),
        "torch_jacrev_sensitivity": bool(pytorch["negative_control_flip"]["torch_func_jacrev_independent_sensitivity"]),
    }
    fences_ok = all(
        payload["classification"] == "scratch_diagnostic"
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        and payload["reads_peer_result"] is False
        for payload in (julia, jax, pytorch)
    )
    all_pass = bool(
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and pytorch["all_pass"] is True
        and z3_verdict == cvc5_verdict == "unsat"
        and div <= TOL
        and same_witness
        and all(negative.values())
        and fences_ok
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "controller_reads_engine_results_after_lanes": True,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "Scratch foundation R3 alternativity rung only: O alternative/power-associative versus S power-associative/flexible but non-alternative. No promotion or formal admission.",
        "all_pass": all_pass,
        "M": {
            "name": "associator_antisymmetry_probe",
            "explicit_probe_family": ["[A,B,C]+[B,A,C]", "[A,B,C]+[C,B,A]", "[A,B,C]+[A,C,B]", "[A,A,B]", "[B,A,A]"],
            "finite_probe_domain": {"O_basis_triples": 8**3, "S_basis_triples": 16**3},
            "witness_probe": {"algebra": "S", "swap_pair": julia_values["S_witness_pair"], "basis_triple": julia_values["S_witness_basis_indices"], "antisymmetry_defect_vector": julia_values["S_witness_vector"]},
        },
        "C": {
            "trace_equals_one": "Each finite basis probe e_i is admissible as rank-one projector e_i*e_i' with trace 1.",
            "psd": "Those probe projectors are PSD.",
            "hermiticity": "Those projectors are real Hermitian; table coefficients are real integers.",
            "normalization": "Basis probes are unit vectors under the Euclidean Gram matrix.",
            "rung_specific_constraint": "Cayley-Dickson structure constants: Julia H from CliffordAlgebras; O=CD(H); S=CD(O).",
        },
        "S_mod_M": {
            "definition": "Equivalence classes under finite probe-indistinguishability: alternative versus non_alternative.",
            "O_class": "alternative",
            "S_class": "non_alternative",
            "with_M_classes": 2,
            "drop_M_classes": 1,
        },
        "alternativity_values": {
            "O_alternative": julia_values["O_alternative"],
            "S_alternative": julia_values["S_alternative"],
            "O_antisymmetry_max_norm": julia_values["O_antisymmetry_max_norm"],
            "S_antisymmetry_max_norm": julia_values["S_antisymmetry_max_norm"],
            "S_witness_pair": julia_values["S_witness_pair"],
            "S_witness_basis_indices": julia_values["S_witness_basis_indices"],
            "S_witness_vector": julia_values["S_witness_vector"],
            "O_power_associative_basis": julia["summary"]["O_power_associative_basis"],
            "S_power_associative_basis": julia["summary"]["S_power_associative_basis"],
            "S_flexible_basis": julia["summary"]["S_flexible_basis"],
        },
        "negative_control_flip": negative,
        "engines": {
            "julia": engine_record(julia, result_path=JULIA_RESULT, values=julia_values),
            "jax": engine_record(jax, result_path=JAX_RESULT, values=jax_values),
            "pytorch": engine_record(pytorch, result_path=PYTORCH_RESULT, values=pytorch_values),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_verdict,
                "negative_control_verdict": jax["crossover_proofs"]["z3"]["negative_control_verdict"],
                "erase_flip_verdict": jax["crossover_proofs"]["z3"]["erase_flip_verdict"],
                "claim": "Given computed O structure constants, antisymmetry violation is UNSAT; given computed S table, violation is SAT; erasing O bindings flips to SAT.",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "negative_control_verdict": jax["crossover_proofs"]["cvc5"]["negative_control_verdict"],
                "erase_flip_verdict": jax["crossover_proofs"]["cvc5"]["erase_flip_verdict"],
                "claim": "cvc5 agrees with z3 over the same computed antisymmetry-defect coefficients.",
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["julia_z3"]["O_swap12"]["antisymmetry_violation_exists_status"],
                "negative_control_verdict": julia["julia_z3"]["S_swap12"]["antisymmetry_violation_exists_status"],
            },
        },
        "claim_path_tools": ["CliffordAlgebras", "Z3", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": ["json", "pathlib", "LinearAlgebra"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": div,
            "same_witness": same_witness,
            "notes": [
                "Julia is authoritative for the Cayley-Dickson ladder seeded by CliffordAlgebras H.",
                "JAX supplies dual SMT over computed antisymmetry-defect coefficients.",
                "PyTorch supplies a torch.func.jacrev sensitivity check, not exact algebra authority.",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R3_ALTERNATIVITY_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"O_alt={result['alternativity_values']['O_alternative']} "
        f"S_alt={result['alternativity_values']['S_alternative']} "
        f"S_witness={result['alternativity_values']['S_witness_basis_indices']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
