#!/usr/bin/env python3
"""e3nn Gate activation norm micro probe.

Tool-stage scope:
  - one tool: e3nn
  - one API surface: e3nn.nn.Gate on one scalar slot, one gate scalar, and
    one vector irrep
  - one tiny claim: Gate applies scalar activation to 0e scalars and gates
    the 1o vector sector by the activated gate scalar, so the vector norm
    scales while the scalar output remains scalar-slot local.

This is pre-lego tool-lego fit evidence. It does not promote a lego, coupling,
bridge, axis, GStack, QIT, nonclassical carrier, or broad e3nn claim.
"""

from __future__ import annotations

import json
import os
from typing import Any

import torch
from e3nn.nn import Gate
from e3nn.o3 import Irreps


classification = "tool_lego_fit_probe"
NAME = "sim_e3nn_gate_activation_norm_micro"
PROBE_FAMILY = "e3nn_gate_activation_norm_micro"
CONSTRAINT_SET = "tiny_gate_scalar_vs_vector_norm_fixture"
TOLERANCE = 1e-6
DTYPE = torch.float64

_NOT_USED_REASON = (
    "not used: this tool-lego fit probe isolates e3nn.nn.Gate activation "
    "norm behavior on one scalar slot and one vector irrep; proof, topology, "
    "GNN layers, convolution, tool coupling, bridge, axis, GStack, QIT, "
    "nonclassical admission, and lego promotion are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "PyTorch is supportive: tensors carry the finite scalar, gate, "
            "and vector fixtures consumed by e3nn.nn.Gate."
        ),
    },
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": (
            "e3nn is load-bearing: e3nn.nn.Gate supplies the scalar activation "
            "and vector-sector gate behavior that decides every predicate in "
            "this bounded fixture."
        ),
    },
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
TOOL_INTEGRATION_DEPTH["e3nn"] = "load_bearing"

IRREPS_SCALARS = Irreps("1x0e")
IRREPS_GATES = Irreps("1x0e")
IRREPS_GATED = Irreps("1x1o")
IRREPS_OUT = Irreps("1x0e + 1x1o")


def _build_gate() -> Gate:
    gate = Gate(
        IRREPS_SCALARS,
        [torch.tanh],
        IRREPS_GATES,
        [torch.sigmoid],
        IRREPS_GATED,
    )
    return gate.to(dtype=DTYPE)


def _fixture_rows() -> torch.Tensor:
    return torch.tensor(
        [
            [0.25, 0.0, 3.0, 4.0, 0.0],
            [-0.75, 1.5, 1.0, -2.0, 2.0],
        ],
        dtype=DTYPE,
    )


def _split_input(row_batch: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    scalar = row_batch[:, 0:1]
    gate_scalar = row_batch[:, 1:2]
    vector = row_batch[:, 2:5]
    return scalar, gate_scalar, vector


def _split_output(row_batch: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    scalar = row_batch[:, 0:1]
    vector = row_batch[:, 1:4]
    return scalar, vector


def _max_abs(tensor: torch.Tensor) -> float:
    if tensor.numel() == 0:
        return 0.0
    return float(tensor.abs().max())


def _norms(tensor: torch.Tensor) -> torch.Tensor:
    return torch.linalg.norm(tensor, dim=-1, keepdim=True)


def _flatten_sections(*sections: dict[str, Any]) -> list[dict[str, Any]]:
    flat = []
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "passed" in value:
                flat.append(value)
    return flat


def run_positive_tests() -> dict[str, Any]:
    gate = _build_gate()
    x = _fixture_rows()
    scalar, gate_scalar, vector = _split_input(x)
    out_scalar, out_vector = _split_output(gate(x))

    expected_scalar = torch.tanh(scalar)
    expected_vector = torch.sigmoid(gate_scalar) * vector
    expected_norm = torch.sigmoid(gate_scalar).abs() * _norms(vector)

    scalar_error = _max_abs(out_scalar - expected_scalar)
    vector_error = _max_abs(out_vector - expected_vector)
    norm_error = _max_abs(_norms(out_vector) - expected_norm)

    return {
        "scalar_slot_uses_scalar_activation": {
            "passed": scalar_error < TOLERANCE,
            "max_abs_error": scalar_error,
            "expected_activation": "torch.tanh on the 0e scalar slot",
            "carrier_slice": "input[:, 0:1] -> output[:, 0:1]",
        },
        "vector_sector_norm_scales_by_gate_scalar": {
            "passed": vector_error < TOLERANCE and norm_error < TOLERANCE,
            "max_abs_vector_error": vector_error,
            "max_abs_norm_error": norm_error,
            "expected_gate": "torch.sigmoid(input[:, 1:2]) multiplies the 1x1o vector sector",
            "carrier_slice": "input[:, 2:5] -> output[:, 1:4]",
        },
        "declared_gate_dimensions_match_fixture": {
            "passed": gate.irreps_in.dim == 5
            and gate.irreps_out.dim == 4
            and gate.irreps_in == Irreps("2x0e + 1x1o")
            and gate.irreps_out == IRREPS_OUT,
            "input_irreps": str(gate.irreps_in),
            "output_irreps": str(gate.irreps_out),
            "expected_input_dim": 5,
            "expected_output_dim": 4,
        },
    }


def run_negative_tests() -> dict[str, Any]:
    gate = _build_gate()
    x = _fixture_rows()
    scalar, gate_scalar, vector = _split_input(x)
    out_scalar, out_vector = _split_output(gate(x))

    scalar_as_gated_vector = torch.sigmoid(gate_scalar) * scalar
    scalar_gate_error = _max_abs(out_scalar - scalar_as_gated_vector)

    altered_vector = vector * torch.tensor([[10.0, 10.0, 10.0], [0.1, 0.1, 0.1]], dtype=DTYPE)
    altered_x = torch.cat([scalar, gate_scalar, altered_vector], dim=-1)
    altered_out_scalar, _ = _split_output(gate(altered_x))
    scalar_vector_dependence_error = _max_abs(altered_out_scalar - out_scalar)

    malformed_rejected = False
    error_type = None
    error_message = None
    try:
        gate(torch.ones(1, gate.irreps_in.dim + 1, dtype=DTYPE))
    except Exception as exc:
        malformed_rejected = True
        error_type = type(exc).__name__
        error_message = str(exc)

    return {
        "scalar_slot_is_excluded_from_vector_norm_gate_rule": {
            "passed": scalar_gate_error > 0.05,
            "excluded_reading": "scalar output equals sigmoid(gate_scalar) times scalar input",
            "observed_disagreement": scalar_gate_error,
            "exclusion_note": (
                "The scalar slot is admitted through its scalar activation, "
                "not through the vector-sector norm gate rule."
            ),
        },
        "vector_norm_change_does_not_change_scalar_output": {
            "passed": scalar_vector_dependence_error < TOLERANCE,
            "max_abs_scalar_change": scalar_vector_dependence_error,
            "exclusion_note": (
                "The 0e scalar output must not read the norm of the gated "
                "1o vector sector in this one-row carrier."
            ),
        },
        "wrong_input_width_is_rejected": {
            "passed": malformed_rejected,
            "bad_input_width": gate.irreps_in.dim + 1,
            "expected_input_width": gate.irreps_in.dim,
            "error_type": error_type,
            "error_message": error_message,
            "exclusion_note": "The declared Gate carrier width must not silently widen.",
        },
    }


def run_boundary_tests() -> dict[str, Any]:
    gate = _build_gate()

    zero_vector = torch.tensor([[0.5, 3.0, 0.0, 0.0, 0.0]], dtype=DTYPE)
    zero_out_scalar, zero_out_vector = _split_output(gate(zero_vector))
    zero_vector_norm = float(_norms(zero_out_vector).item())

    zero_gate = torch.tensor([[0.5, 0.0, 2.0, 0.0, 0.0]], dtype=DTYPE)
    _, zero_gate_out_vector = _split_output(gate(zero_gate))
    zero_gate_expected_norm = float((torch.sigmoid(zero_gate[:, 1:2]) * _norms(zero_gate[:, 2:5])).item())
    zero_gate_norm_error = abs(float(_norms(zero_gate_out_vector).item()) - zero_gate_expected_norm)

    empty = torch.empty(0, gate.irreps_in.dim, dtype=DTYPE)
    empty_out = gate(empty)

    return {
        "zero_vector_has_zero_gated_vector_norm": {
            "passed": zero_vector_norm < TOLERANCE
            and abs(float(zero_out_scalar.item()) - float(torch.tanh(zero_vector[:, 0:1]).item())) < TOLERANCE,
            "output_vector_norm": zero_vector_norm,
            "scalar_output": float(zero_out_scalar.item()),
            "boundary_note": "A zero 1o vector remains zero after Gate even when the gate scalar is nonzero.",
        },
        "zero_gate_scalar_halves_vector_norm_under_sigmoid": {
            "passed": zero_gate_norm_error < TOLERANCE,
            "observed_output_norm": float(_norms(zero_gate_out_vector).item()),
            "expected_output_norm": zero_gate_expected_norm,
            "boundary_note": "Gate scalar zero maps through sigmoid to 0.5 in this bounded fixture.",
        },
        "zero_batch_preserves_declared_output_width": {
            "passed": tuple(empty_out.shape) == (0, gate.irreps_out.dim),
            "observed_shape": list(empty_out.shape),
            "expected_shape": [0, gate.irreps_out.dim],
            "boundary_note": "An empty finite batch preserves the declared Gate output width.",
        },
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    flat_tests = _flatten_sections(positive, negative, boundary)
    all_pass = all(test.get("passed") for test in flat_tests)

    results = {
        "name": NAME,
        "probe_family": PROBE_FAMILY,
        "constraint_set": CONSTRAINT_SET,
        "classification": classification,
        "tool_function_surface": "e3nn.nn.Gate scalar activation and vector norm gating",
        "tool_function_scope": "tool_lego_fit_probe_only",
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "finite_map": (
            "Gate: R^5 carrier with [0e scalar, 0e gate scalar, 1o vector] "
            "to R^4 output with [activated 0e scalar, gated 1o vector]"
        ),
        "domain": "finite two-row e3nn Gate input tensor with one scalar slot, one gate scalar, and one 1x1o vector sector",
        "codomain_or_output": "finite two-row tensor with one activated scalar and one gated vector sector",
        "carrier": "finite one-row/two-row scalar-plus-vector e3nn Gate carrier: 1x0e scalar, 1x0e gate, 1x1o vector",
        "carrier_topology": "finite tensor fixture only; no graph, cell complex, bridge, axis, GStack, QIT, or nonclassical carrier",
        "one_variable": "Only e3nn.nn.Gate scalar-vs-vector activation norm behavior is under test; carrier size, activations, irreps, and tolerances are pinned.",
        "ledger_loopback": {
            "tool_depth_row": "e3nn load-bearing micro receipts",
            "threshold": "shallow-tool checker threshold is >=10 load-bearing receipts for e3nn",
            "receipt_role_if_run": "one additional load-bearing e3nn tool-lego fit receipt for Gate activation norm behavior",
        },
        "surviving_alternatives": [
            "Other e3nn nonlinearities and Gate layouts remain separate surfaces.",
            "This receipt does not decide learned networks, convolutions, coupling, bridge, axis, GStack, QIT, or broad e3nn behavior.",
        ],
        "claim_ceiling": (
            "local tool-lego fit only: e3nn.nn.Gate fits one tiny scalar-vs-vector "
            "activation norm fixture; promotion_allowed=false; no QIT, GStack, "
            "axis, bridge, nonclassical, coupling, or scientific lego promotion claim"
        ),
        "next_lego_target": "minimal scalar-gated vector fixture before any downstream equivariant operator-family use",
        "promotion_allowed": False,
        "promotion_condition": (
            "No promotion from this authored packet. A later admitted lego row "
            "must name this exact receipt, declare the active stage gate, and "
            "pass strict runner admission."
        ),
        "blocked_until": (
            "blocked from lego, coupling, bridge, axis, GStack, QIT, "
            "nonclassical, and broad e3nn claims until a later runner result "
            "and queue row reconcile this exact surface"
        ),
        "demotion_condition": (
            "Demote this surface if e3nn/torch imports fail, Gate dimensions "
            "do not match the declared carrier, scalar activation diverges "
            "from tanh on the scalar slot, vector-sector norm does not scale "
            "by sigmoid of the gate scalar, wrong-width input is accepted, or "
            "the result is cited outside the stated claim ceiling."
        ),
        "out_of_scope": [
            "no result JSON written during authoring-only closeout",
            "no sim execution in this packet",
            "no registry or doc status edit",
            "no lego promotion",
            "no tool-tool coupling",
            "no bridge claim",
            "no axis claim",
            "no GStack claim",
            "no QIT claim",
            "no nonclassical admission",
            "no proof of the whole e3nn library",
        ],
        "criteria_checked": [
            "e3nn.nn.Gate declares the pinned scalar-plus-vector carrier dimensions",
            "scalar slot output follows scalar activation only",
            "1x1o vector output norm scales by the activated gate scalar",
            "scalar slot is excluded from the vector norm gate rule",
            "wrong input width is rejected",
            "zero-vector, zero-gate, and zero-batch boundaries preserve the declared semantics",
        ],
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
            "all_pass": all_pass,
            "classification": classification,
            "promotion_allowed": False,
            "promotion_note": "promotion_allowed=false; this is an authorable tool-lego fit probe only",
        },
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} admitted")

    if not all_pass:
        raise SystemExit(1)
