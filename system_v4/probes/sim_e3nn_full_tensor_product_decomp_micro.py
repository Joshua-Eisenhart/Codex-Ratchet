#!/usr/bin/env python3
"""e3nn FullTensorProduct decomposition-count micro probe.

Tool-stage scope only:
  - one tool family: e3nn o3, with torch only as the tensor backend;
  - one API surface: o3.FullTensorProduct.irreps_out on a tiny l=1 x l=1
    O(3) carrier;
  - one bounded claim: e3nn reports the expected 0e, 1e, and 2e output
    channels for the product of two 1x1o vector irreps and rejects nearby
    malformed or widened carrier declarations.

This file is a tool-lego fit probe. It does not promote a lego, coupling,
bridge, axis, GStack, QIT, nonclassical, or target-system claim.
"""

from __future__ import annotations

import json
import os
from typing import Any

from receipt_boundary import apply_default_receipt_boundary

classification = "tool_lego_fit_probe"
NAME = "sim_e3nn_full_tensor_product_decomp_micro"
PROBE_FAMILY = "e3nn_full_tensor_product_decomposition_counts"
CONSTRAINT_SET = "bounded_l1_vector_pair_full_tensor_product_channel_counts"

SURFACE = "e3nn.o3.FullTensorProduct.irreps_out decomposition counts"
CARRIER = "finite two-factor O(3) carrier: 1x1o x 1x1o over one symbolic tensor-product fixture"
COVERED_CHECK = (
    "switched: e3nn_capability_results.json already covers broad 1o x 1o "
    "tensor-product decomposition; this neighbor isolates FullTensorProduct.irreps_out "
    "channel counts as a narrower API surface"
)
LEDGER_LOOPBACK = (
    "tool-depth row e3nn/load_bearing; contributes one candidate toward the "
    "shallow-tool checker threshold >=10 load-bearing e3nn receipts after runner evidence"
)

CLAIM_CEILING = (
    "local tool-lego fit only: e3nn FullTensorProduct.irreps_out reports the "
    "bounded 1x1o x 1x1o -> 1x0e + 1x1e + 1x2e channel-count fixture; "
    "promotion_allowed=false; no QIT, GStack, axis, bridge, nonclassical, "
    "coupling, or target-system claim"
)

_NOT_USED_REASON = (
    "not used: this micro probe isolates one e3nn FullTensorProduct.irreps_out "
    "decomposition-count surface; other tools require separate receipts."
)

TOOL_MANIFEST: dict[str, dict[str, Any]] = {
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "supportive tensor backend required by e3nn; not the decomposition-count surface under test",
    },
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": (
            "load-bearing target: e3nn.o3.FullTensorProduct.irreps_out decides "
            "the bounded l=1 x l=1 decomposition-count predicate"
        ),
    },
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}

TORCH_OK = False
E3NN_OK = False
TORCH_IMPORT_ERROR = None
E3NN_IMPORT_ERROR = None
E3NN_VERSION = None

try:
    import torch  # noqa: F401

    TORCH_OK = True
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
except Exception as exc:  # pragma: no cover - environment receipt path
    TORCH_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
    TOOL_MANIFEST["pytorch"]["reason"] = f"blocked: torch import failed: {TORCH_IMPORT_ERROR}"

try:
    import e3nn
    from e3nn import o3

    E3NN_OK = True
    E3NN_VERSION = getattr(e3nn, "__version__", "unknown")
    TOOL_MANIFEST["e3nn"]["tried"] = True
    TOOL_MANIFEST["e3nn"]["used"] = True
    TOOL_INTEGRATION_DEPTH["e3nn"] = "load_bearing"
except Exception as exc:  # pragma: no cover - environment receipt path
    o3 = None  # type: ignore[assignment]
    E3NN_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
    TOOL_MANIFEST["e3nn"]["reason"] = f"blocked: e3nn import failed: {E3NN_IMPORT_ERROR}"


def _row_admitted(row: dict[str, Any]) -> bool:
    return bool(row.get("passed"))


def _section_admitted(section: dict[str, dict[str, Any]]) -> bool:
    return bool(section) and all(_row_admitted(row) for row in section.values())


def _blocked_section() -> dict[str, dict[str, Any]]:
    return {
        "dependency_gate": {
            "passed": False,
            "status": "blocked",
            "torch_available": TORCH_OK,
            "e3nn_available": E3NN_OK,
            "torch_import_error": TORCH_IMPORT_ERROR,
            "e3nn_import_error": E3NN_IMPORT_ERROR,
            "blocked_reason": (
                "e3nn and torch are both required for this FullTensorProduct "
                "decomposition-count tool-lego fit fixture"
            ),
        }
    }


def _full_tensor_product():
    return o3.FullTensorProduct(o3.Irreps("1x1o"), o3.Irreps("1x1o"))


def _counts_by_l_and_parity(irreps: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for mul, ir in irreps:
        parity = "e" if int(ir.p) == 1 else "o"
        key = f"{ir.l}{parity}"
        counts[key] = counts.get(key, 0) + int(mul)
    return counts


def run_positive_tests() -> dict[str, dict[str, Any]]:
    if not (TORCH_OK and E3NN_OK):
        return _blocked_section()

    input_irreps = o3.Irreps("1x1o")
    full_tp = _full_tensor_product()
    output_irreps = full_tp.irreps_out.simplify()
    observed_counts = _counts_by_l_and_parity(output_irreps)
    expected_counts = {"0e": 1, "1e": 1, "2e": 1}

    return {
        "l1_pair_decomposition_counts_are_admitted": {
            "passed": observed_counts == expected_counts,
            "input_irreps": [str(input_irreps), str(input_irreps)],
            "observed_irreps_out": str(output_irreps),
            "observed_counts": observed_counts,
            "expected_counts": expected_counts,
            "admission_note": (
                "The finite l=1 vector-pair carrier is admitted only for the "
                "declared 0e, 1e, and 2e channel-count readout."
            ),
        },
        "declared_output_dimension_matches_channel_counts": {
            "passed": output_irreps.dim == 9,
            "observed_dim": output_irreps.dim,
            "expected_dim": 1 + 3 + 5,
            "dimension_terms": {"0e": 1, "1e": 3, "2e": 5},
        },
        "full_tensor_product_names_the_expected_output_carrier": {
            "passed": str(output_irreps) == "1x0e+1x1e+1x2e",
            "observed_irreps_out": str(output_irreps),
            "expected_irreps_out": "1x0e+1x1e+1x2e",
        },
    }


def run_negative_tests() -> dict[str, dict[str, Any]]:
    if not (TORCH_OK and E3NN_OK):
        return _blocked_section()

    malformed_rejected = False
    malformed_error = None
    try:
        o3.Irreps("not_an_irrep")
    except Exception as exc:
        malformed_rejected = True
        malformed_error = f"{type(exc).__name__}: {exc}"

    scalar_pair_out = o3.FullTensorProduct(o3.Irreps("1x0e"), o3.Irreps("1x0e")).irreps_out.simplify()
    scalar_pair_counts = _counts_by_l_and_parity(scalar_pair_out)

    widened_pair_out = o3.FullTensorProduct(o3.Irreps("2x1o"), o3.Irreps("1x1o")).irreps_out.simplify()
    widened_counts = _counts_by_l_and_parity(widened_pair_out)

    return {
        "malformed_irrep_string_is_excluded": {
            "passed": malformed_rejected,
            "error": malformed_error,
            "exclusion_note": "Malformed carrier declarations must be excluded before decomposition counts are read.",
        },
        "scalar_pair_is_excluded_from_l1_vector_pair_counts": {
            "passed": scalar_pair_counts != {"0e": 1, "1e": 1, "2e": 1},
            "observed_irreps_out": str(scalar_pair_out),
            "observed_counts": scalar_pair_counts,
            "excluded_from": "1x1o x 1x1o channel-count fixture",
        },
        "widened_multiplicity_is_excluded_from_single_pair_counts": {
            "passed": widened_counts != {"0e": 1, "1e": 1, "2e": 1},
            "observed_irreps_out": str(widened_pair_out),
            "observed_counts": widened_counts,
            "excluded_from": "single-multiplicity l=1 vector-pair fixture",
        },
    }


def run_boundary_tests() -> dict[str, dict[str, Any]]:
    if not (TORCH_OK and E3NN_OK):
        return _blocked_section()

    even_vector_out = o3.FullTensorProduct(o3.Irreps("1x1e"), o3.Irreps("1x1e")).irreps_out.simplify()
    odd_even_out = o3.FullTensorProduct(o3.Irreps("1x1o"), o3.Irreps("1x1e")).irreps_out.simplify()
    scalar_vector_out = o3.FullTensorProduct(o3.Irreps("1x0e"), o3.Irreps("1x1o")).irreps_out.simplify()

    return {
        "even_vector_pair_has_same_l_counts_with_even_parity": {
            "passed": _counts_by_l_and_parity(even_vector_out) == {"0e": 1, "1e": 1, "2e": 1},
            "observed_irreps_out": str(even_vector_out),
            "boundary_note": "Parity changes are explicit carrier choices, not promotion evidence.",
        },
        "odd_even_vector_pair_marks_odd_output_parity": {
            "passed": _counts_by_l_and_parity(odd_even_out) == {"0o": 1, "1o": 1, "2o": 1},
            "observed_irreps_out": str(odd_even_out),
            "boundary_note": "Mixed parity remains distinguishable at the irreps_out boundary.",
        },
        "scalar_vector_pair_stays_single_l1_channel": {
            "passed": _counts_by_l_and_parity(scalar_vector_out) == {"1o": 1},
            "observed_irreps_out": str(scalar_vector_out),
            "boundary_note": "A scalar-vector boundary fixture does not admit the three-channel l=1 pair readout.",
        },
    }


def build_result() -> dict[str, Any]:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _section_admitted(positive),
        "negative_all_pass": _section_admitted(negative),
        "boundary_all_pass": _section_admitted(boundary),
        "torch_available": TORCH_OK,
        "e3nn_available": E3NN_OK,
        "e3nn_version": E3NN_VERSION,
        "promotion_allowed": False,
        "surface": SURFACE,
        "covered_check": COVERED_CHECK,
        "ledger_loopback": LEDGER_LOOPBACK,
    }
    summary["all_pass"] = bool(
        TORCH_OK
        and E3NN_OK
        and summary["positive_all_pass"]
        and summary["negative_all_pass"]
        and summary["boundary_all_pass"]
    )

    result = {
        "name": NAME,
        "probe_family": PROBE_FAMILY,
        "constraint_set": CONSTRAINT_SET,
        "classification": classification,
        "status": "admitted" if summary["all_pass"] else "blocked",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "surface": SURFACE,
        "carrier": CARRIER,
        "one_variable": "only the e3nn FullTensorProduct.irreps_out channel-count behavior is uncertain",
        "covered_check": COVERED_CHECK,
        "ledger_loopback": LEDGER_LOOPBACK,
        "operation_sequence": [
            "construct o3.Irreps('1x1o') twice as the finite carrier",
            "construct o3.FullTensorProduct(1x1o, 1x1o)",
            "read irreps_out and count l/parity channels",
            "run malformed-irrep, scalar-pair, widened-multiplicity, parity, and scalar-vector controls",
        ],
        "carrier_topology": {
            "carrier": CARRIER,
            "topology": "finite one-row representation fixture; no graph, cell complex, manifold, bridge, or axis topology",
            "irreps": {"input_1": "1x1o", "input_2": "1x1o", "output": "1x0e+1x1e+1x2e"},
        },
        "observable": "counts of l/parity channels in e3nn FullTensorProduct.irreps_out",
        "pass_fail_predicate": (
            "admitted iff imports are available, irreps_out for 1x1o x 1x1o "
            "has counts {'0e': 1, '1e': 1, '2e': 1}, output dim is 9, "
            "malformed and adjacent carrier controls are excluded, and boundary "
            "parity fixtures remain distinguishable"
        ),
        "graveyards": [
            "malformed irrep declaration admitted as a carrier",
            "scalar-pair fixture reported as the l=1 vector-pair channel set",
            "widened multiplicity collapsed into the single-pair count",
            "mixed parity hidden by the decomposition-count readout",
            "any promotion beyond local tool-lego fit",
        ],
        "baselines": {
            "manual_l_count": "1 x 1 has l channels 0, 1, and 2 with one multiplicity each",
            "manual_dimension_count": "0e + 1e + 2e has dimension 1 + 3 + 5 = 9",
            "scalar_vector_boundary": "0e x 1o remains a single l=1 channel",
        },
        "alternative_formulations": [
            "o3.TensorProduct with explicit instructions for the same output irreps",
            "o3.FullyConnectedTensorProduct output-width fixture",
            "Irreps.D_from_matrix equivariance check for the returned output carrier",
        ],
        "exact_tool_function_needs": [
            "e3nn.o3.Irreps",
            "e3nn.o3.FullTensorProduct",
            "FullTensorProduct.irreps_out",
            "torch import only as e3nn backend",
        ],
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "surviving_alternatives": [
            "Other e3nn tensor-product API surfaces remain separate receipts.",
            "This receipt does not decide any downstream lego, coupling, QIT, GStack, axis, bridge, or nonclassical surface.",
        ],
        "next_lego_target": "minimal finite SO(3) representation-channel-count fixture before operator-family geometry claims",
        "promotion_condition": (
            "No promotion from this receipt. A later admitted lego row must name "
            "this exact function receipt, declare the stage gate, and pass strict runner admission."
        ),
        "blocked_until": (
            "blocked from QIT, GStack, axis, bridge, nonclassical, coupling, or "
            "target-system claims until separate downstream receipts and stage-gate admission exist"
        ),
        "demotion_condition": (
            "Demote e3nn for this surface if FullTensorProduct.irreps_out reports "
            "different l/parity counts for 1x1o x 1x1o, if malformed carriers are "
            "admitted, or if adjacent scalar/multiplicity/parity controls are not excluded."
        ),
        "out_of_scope": [
            "no lego promotion",
            "no tool-tool coupling",
            "no bridge claim",
            "no axis claim",
            "no GStack claim",
            "no QIT claim",
            "no nonclassical admission",
            "no target-system admission",
            "no proof of the whole e3nn library",
        ],
        "blocked_reason": None
        if summary["all_pass"]
        else "blocked because e3nn/torch imports or bounded channel-count predicates did not all admit",
    }
    return apply_default_receipt_boundary(
        result,
        source_name=NAME,
        target=result["next_lego_target"],
    )


if __name__ == "__main__":
    results = build_result()
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: all_pass={results['all_pass']}")
    if not results["all_pass"]:
        raise SystemExit(1)
