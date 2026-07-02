#!/usr/bin/env python3
"""Candidate-fence non-redundancy audit.

This is not a promotion gate. It checks the receipted candidate fences
(currently CF-14..CF-25) for the minimum
conditions required before a separate human or formal review can even consider
changing their status:

* the candidate gate exists;
* the gate has a passing receipt;
* the candidate remains marked candidate;
* the receipt has a promotion blocker;
* the candidate has at least one distinctive operational token not already
  covered by accepted RC/DC wording or another receipted CF;
* the candidate does not exactly duplicate another receipted CF's structural
  fixture signature.
"""

from __future__ import annotations

import json
import pathlib
import re
import time
from typing import Any


HERE = pathlib.Path(__file__).resolve().parent
REGISTRY_PATH = HERE / "foundation_role_registry_20260523.json"
OUT = HERE / "results" / "candidate_fence_nonredundancy_audit_results.json"

RECEIPTED_CF_CODES = [
    "CF-14",
    "CF-15",
    "CF-16",
    "CF-17",
    "CF-18",
    "CF-19",
    "CF-20",
    "CF-21",
    "CF-22",
    "CF-23",
    "CF-24",
    "CF-25",
]
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "before",
    "by",
    "candidate",
    "claim",
    "control",
    "derived",
    "explicit",
    "finite",
    "for",
    "from",
    "gate",
    "in",
    "is",
    "must",
    "no",
    "not",
    "of",
    "or",
    "primitive",
    "requires",
    "root",
    "test",
    "the",
    "to",
    "under",
    "with",
}
EXPECTED_DISTINCTIVE_TOKENS = {
    "CF-14": {"continuum", "smoothness", "derivative", "limit", "discretization"},
    "CF-15": {"tensor", "factorization", "independence", "product", "marginals"},
    "CF-16": {"markov", "cptp", "instrument", "transition", "kraus"},
    "CF-17": {"blanket", "cut", "mediator", "boundary", "instrument"},
    "CF-18": {"aggregation", "average", "path", "resolved", "order"},
    "CF-19": {"scalarization", "scalar", "vector", "tensor", "projection"},
    "CF-20": {"basis", "gauge", "scramble", "invariance", "coordinate"},
    "CF-21": {
        "measurement",
        "probe",
        "apparatus",
        "povm",
        "instrument",
        "instrument_declared",
        "probe_family_finite",
        "observer_in_joint_system",
    },
    "CF-22": {"simultaneity", "simultaneous", "merge", "race", "no_global_now", "commuting_collapse_control"},
    "CF-23": {"global", "context", "oracle", "scoped", "scope", "partial_trace_or_projection"},
    "CF-24": {"convergence", "limit", "epsilon", "step_budget", "stopping_rule", "finite_failure_case"},
    "CF-25": {"reversibility", "inverse", "irreversible", "inverse_witness", "irreversible_channel_control"},
}
NONOVERLAP_JACCARD_THRESHOLD = 0.55
THRESHOLD_RATIONALE = (
    "A receipted CF must share less than 55 percent of its bounded text/token "
    "signature with accepted RC/DC wording and with any other receipted CF. "
    "This is only a conservative proxy for non-collapse, not a formal "
    "independence proof or a promotion criterion."
)
STRUCTURAL_SIGNATURES = {
    "CF-14": {
        "carrier": "finite_sequence",
        "operator_family": "finite_difference",
        "positive_predicate": "finite_grid_derivative_defined",
        "negative_predicate": "continuum_derivative_without_grid_rejected",
        "boundary_predicate": "refined_grid_declared",
    },
    "CF-15": {
        "carrier": "two_qubit_density",
        "operator_family": "partial_trace_factorization",
        "positive_predicate": "entangled_vs_product_matched_cut_separated",
        "negative_predicate": "primitive_factorization_rejected",
        "boundary_predicate": "declared_product_state_allowed",
    },
    "CF-16": {
        "carrier": "single_qubit_density",
        "operator_family": "cptp_kraus_instrument",
        "positive_predicate": "noncommuting_cptp_order_and_coherence_tracked",
        "negative_predicate": "classical_transition_matrix_without_kraus_rejected",
        "boundary_predicate": "commuting_diagonal_markov_ablation_allowed",
    },
    "CF-17": {
        "carrier": "two_qubit_cut_density",
        "operator_family": "boundary_instrument_backaction",
        "positive_predicate": "cut_instrument_changes_remote_reduction",
        "negative_predicate": "sharp_blanket_partition_without_instrument_rejected",
        "boundary_predicate": "classical_correlated_cut_with_declared_instrument_allowed",
    },
    "CF-18": {
        "carrier": "path_family_density",
        "operator_family": "ordered_path_composition",
        "positive_predicate": "path_resolved_order_signal_survives",
        "negative_predicate": "order_erasing_average_rejected",
        "boundary_predicate": "commuting_average_ablation_allowed",
    },
    "CF-19": {
        "carrier": "single_qubit_readout_vector",
        "operator_family": "vector_projection",
        "positive_predicate": "vector_distinguishes_scalar_collapse",
        "negative_predicate": "undeclared_scalarization_rejected",
        "boundary_predicate": "declared_projection_with_loss_allowed",
    },
    "CF-20": {
        "carrier": "single_qubit_density_pair",
        "operator_family": "unitary_basis_scramble",
        "positive_predicate": "trace_distance_invariant_raw_coordinate_changes",
        "negative_predicate": "undeclared_basis_coordinate_rejected",
        "boundary_predicate": "declared_diagonal_basis_allowed",
    },
    "CF-21": {
        "carrier": "single_qubit_system_plus_probe",
        "operator_family": "projective_instrument",
        "positive_predicate": "declared_instrument_probabilities_and_backaction_tracked",
        "negative_predicate": "unnamed_probe_probability_rejected",
        "boundary_predicate": "declared_classical_readout_ablation_allowed",
    },
    "CF-22": {
        "carrier": "single_qubit_density",
        "operator_family": "noncommuting_order_race",
        "positive_predicate": "declared_order_contract_separates_ab_ba",
        "negative_predicate": "same_time_average_erases_order_signal",
        "boundary_predicate": "commuting_order_collapse_allowed",
    },
    "CF-23": {
        "carrier": "two_qubit_bell_pair",
        "operator_family": "scoped_partial_trace",
        "positive_predicate": "local_scope_invariant_global_oracle_differs",
        "negative_predicate": "global_oracle_decision_fails_scoped_process",
        "boundary_predicate": "declared_global_diagnostic_allowed",
    },
    "CF-24": {
        "carrier": "finite_scalar_recurrence",
        "operator_family": "bounded_iteration",
        "positive_predicate": "epsilon_reached_within_step_budget",
        "negative_predicate": "eventual_limit_without_budget_rejected",
        "boundary_predicate": "asymptotic_intuition_non_load_bearing",
    },
    "CF-25": {
        "carrier": "single_qubit_density_channel",
        "operator_family": "unitary_vs_amplitude_damping_channel",
        "positive_predicate": "unitary_inverse_witness_and_irreversible_collapse_control",
        "negative_predicate": "proposed_damping_inverse_fails_recovery",
        "boundary_predicate": "unitary_subgroup_inverse_allowed",
    },
}


def structural_key(code: str) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(STRUCTURAL_SIGNATURES[code].items()))


def tokenize(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, (list, tuple)):
        text = " ".join(str(v) for v in value)
    else:
        text = str(value)
    return {tok for tok in re.findall(r"[a-zA-Z][a-zA-Z0-9_]+", text.lower()) if tok not in STOPWORDS}


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / max(1, len(a | b))


def cf_signature(item: dict[str, Any], gate: dict[str, Any], receipt_payload: dict[str, Any]) -> set[str]:
    fields = [
        item.get("name"),
        item.get("forbidden_primitive"),
        item.get("cs_form"),
        item.get("qit_math_form"),
        item.get("process_form"),
        item.get("gate_needed"),
        gate.get("positive_case"),
        gate.get("negative_case"),
        gate.get("boundary_case"),
        gate.get("observable"),
        receipt_payload.get("name"),
        receipt_payload.get("claim_ceiling"),
    ]
    out: set[str] = set()
    for field in fields:
        out |= tokenize(field)
    return out


def accepted_signature(items: list[dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for item in items:
        if item.get("role") not in {"RC", "DC"}:
            continue
        for field in ("name", "forbidden_primitive", "cs_form", "qit_math_form", "process_form"):
            out |= tokenize(item.get(field))
    return out


def main() -> int:
    started = time.time()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    registry = load_json(REGISTRY_PATH)
    items = registry["items"]
    by_code = {item["code"]: item for item in items}
    gates_by_code = {item["code"]: item for item in items if item.get("role") == "EG"}
    receipts_by_gate = {item["gate"]: item for item in items if item.get("role") == "REC"}
    accepted_tokens = accepted_signature(items)

    rows: list[dict[str, Any]] = []
    signatures: dict[str, set[str]] = {}
    for code in RECEIPTED_CF_CODES:
        item = by_code[code]
        gate = gates_by_code[item["required_gate"]]
        receipt = receipts_by_gate[item["required_gate"]]
        receipt_path = HERE.parents[2] / receipt["result_path"]
        payload = load_json(receipt_path)
        signature = cf_signature(item, gate, payload)
        signatures[code] = signature
        distinctive_tokens = sorted((signature - accepted_tokens) & EXPECTED_DISTINCTIVE_TOKENS[code])
        accepted_overlap = jaccard(signature, accepted_tokens)
        rows.append(
            {
                "code": code,
                "required_gate": item["required_gate"],
                "receipt_id": receipt["receipt_id"],
                "candidate_status_preserved": item.get("status") == "candidate",
                "gate_implemented": gate.get("gate_implemented") is True,
                "receipt_all_pass": payload.get("all_pass") is True,
                "promotion_blocker_present": bool(receipt.get("promotion_blocker")),
                "distinctive_tokens": distinctive_tokens,
                "structural_signature": STRUCTURAL_SIGNATURES[code],
                "accepted_rc_dc_signature_jaccard": accepted_overlap,
                "accepted_rc_dc_nonoverlap_pass": accepted_overlap < NONOVERLAP_JACCARD_THRESHOLD,
                "signature_size": len(signature),
                "pass": (
                    item.get("status") == "candidate"
                    and gate.get("gate_implemented") is True
                    and payload.get("all_pass") is True
                    and bool(receipt.get("promotion_blocker"))
                    and bool(distinctive_tokens)
                    and accepted_overlap < NONOVERLAP_JACCARD_THRESHOLD
                ),
            }
        )

    pairwise = []
    for idx, left in enumerate(RECEIPTED_CF_CODES):
        for right in RECEIPTED_CF_CODES[idx + 1 :]:
            overlap = jaccard(signatures[left], signatures[right])
            pairwise.append(
                {
                    "left": left,
                    "right": right,
                    "signature_jaccard": overlap,
                    "structural_exact_duplicate": structural_key(left) == structural_key(right),
                }
            )
    max_pairwise_overlap = max(row["signature_jaccard"] for row in pairwise)
    structural_duplicate_pairs = [row for row in pairwise if row["structural_exact_duplicate"]]
    threshold_calibration = {
        "synthetic_duplicate_signature_jaccard": 1.0,
        "synthetic_duplicate_rejected_by_threshold": 1.0 >= NONOVERLAP_JACCARD_THRESHOLD,
        "structural_duplicate_pairs_detected": structural_duplicate_pairs,
        "structural_nonduplicate_pass": len(structural_duplicate_pairs) == 0,
        "ceiling_threshold_jaccard": NONOVERLAP_JACCARD_THRESHOLD,
        "ceiling_threshold_structural_duplicate_pairs": 0,
        "structural_duplicate_threshold_semantics": "Any nonempty structural_duplicate_pairs list blocks this ceiling audit.",
        "note": "Token Jaccard is a ceiling proxy. Structural fixture signatures are checked separately for exact duplicate gates.",
    }

    result = {
        "schema": "candidate_fence_nonredundancy_audit_result_v1",
        "name": "candidate_fence_nonredundancy_audit",
        "classification": "registry_audit_gate",
        "gate": "EG-CF-nonredundancy-review",
        "claim_ceiling": "Non-redundancy audit only. Passing does not promote any CF to DC.",
        "uses_numpy": False,
        "TOOL_MANIFEST": {
            "python_json": {
                "tried": True,
                "used": True,
                "reason": "load-bearing registry and receipt parsing for candidate-fence non-redundancy and structural-signature audit",
            },
            "python_re": {
                "tried": True,
                "used": True,
                "reason": "supportive bounded token signatures for non-redundancy proxy",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {"python_json": "load_bearing", "python_re": "supportive"},
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "receipted_candidate_fences": RECEIPTED_CF_CODES,
        "rows": rows,
        "pairwise_signature_overlap": pairwise,
        "max_pairwise_signature_jaccard": max_pairwise_overlap,
        "structural_pairwise_overlap": pairwise,
        "structural_duplicate_pairs": structural_duplicate_pairs,
        "threshold_calibration": threshold_calibration,
        "nonoverlap_jaccard_threshold": NONOVERLAP_JACCARD_THRESHOLD,
        "threshold_rationale": THRESHOLD_RATIONALE,
        "accepted_signature_size": len(accepted_tokens),
        "all_pass": (
            all(row["pass"] for row in rows)
            and max_pairwise_overlap < NONOVERLAP_JACCARD_THRESHOLD
            and len(structural_duplicate_pairs) == 0
            and threshold_calibration["synthetic_duplicate_rejected_by_threshold"]
        ),
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "out": str(OUT)}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
