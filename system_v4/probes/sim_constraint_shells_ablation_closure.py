#!/usr/bin/env python3
"""Finite constraint-shell ablation closure packet.

This packet follows the older constraint-shell binding crosscheck without
relabeling it. It asks a narrower closure question: do the L4 sub-projections
and L6 entropy monotone have separable, finite, ablation-detectable roles on
the same local state set?

It is lego-stage evidence only. It does not admit QIT, GStack, axes, bridge, or
nonclassical claims.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import torch
from z3 import Int, Solver, unsat

from receipt_boundary import apply_default_receipt_boundary


SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
sys.path.insert(0, str(SCRIPT_DIR))
import sim_constraint_shells_binding_crosscheck as shell_parent  # noqa: E402

PARENT_RESULT = "constraint_shells_binding_crosscheck_results.json"
EPS = 1e-5

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing finite arrays, ablation summaries, and threshold checks"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density-matrix shell projections and displacement measures"},
    "z3": {"tried": True, "used": True, "reason": "supportive integer fence for finite ablation coverage only"},
    "sympy": {"tried": False, "used": False, "reason": "not needed; no symbolic derivation in this closure packet"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed; parent receipt carries geodesic support"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed; z3 covers the small integer fence"},
    "pyg": {"tried": False, "used": False, "reason": "not needed; no graph message passing"},
    "qutip": {"tried": False, "used": False, "reason": "not needed; direct finite torch density matrices"},
    "qiskit": {"tried": False, "used": False, "reason": "not needed; no circuit backend"},
    "clifford": {"tried": False, "used": False, "reason": "not needed; no geometric algebra action"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed; no topology"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed; no cell-complex layer"},
    "xgi": {"tried": False, "used": False, "reason": "not needed; no hypergraph layer"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed; no graph algorithms"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": "load_bearing",
    "z3": "supportive",
    "sympy": None,
    "geomstats": None,
    "cvc5": None,
    "pyg": None,
    "qutip": None,
    "qiskit": None,
    "clifford": None,
    "gudhi": None,
    "toponetx": None,
    "xgi": None,
    "rustworkx": None,
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parent_receipt() -> dict:
    path = RESULTS_DIR / PARENT_RESULT
    payload = read_json(path) if path.exists() else {}
    return {
        "name": PARENT_RESULT,
        "path": str(path),
        "exists": path.exists(),
        "classification": payload.get("classification"),
        "all_pass": bool(payload.get("all_pass") or payload.get("summary", {}).get("all_pass")),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
        "scope_note": payload.get("summary", {}).get("scope_note"),
    }


def l4_sequence(rho: torch.Tensor, channel_names: list[str]) -> torch.Tensor:
    state = rho
    for name in channel_names:
        if name == "depolarizing":
            state = shell_parent.apply_depolarizing(state, p=0.1)
        elif name == "amplitude_damping":
            state = shell_parent.apply_amplitude_damping(state, gamma=0.1)
        elif name == "z_dephasing":
            state = shell_parent.apply_z_dephasing(state, p=0.1)
        else:
            raise ValueError(f"unknown channel {name}")
        tr = torch.real(torch.trace(state))
        state = state / (tr + 1e-12)
    return state


def distance(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(shell_parent.frobenius_distance_torch(a, b).item())


def evaluate_states() -> list[dict]:
    channels = ["depolarizing", "amplitude_damping", "z_dephasing"]
    rows = []
    for label, rho_np in shell_parent.make_test_states().items():
        rho = torch.tensor(rho_np, dtype=torch.complex64)
        full_l4, l4_steps = shell_parent.project_L4_substeps(rho)
        l6 = shell_parent.project_entropy_monotone(rho)
        ablations = {}
        for channel in channels:
            kept = [name for name in channels if name != channel]
            ablated = l4_sequence(rho, kept)
            ablations[f"without_{channel}"] = {
                "kept_channels": kept,
                "endpoint_delta_from_full_l4": distance(full_l4, ablated),
                "endpoint_displacement_from_input": distance(rho, ablated),
            }
        reversed_l4 = l4_sequence(rho, list(reversed(channels)))
        identity_l4 = l4_sequence(rho, [])
        rows.append(
            {
                "label": label,
                "l4_substep_displacements": [float(step["displacement"]) for step in l4_steps],
                "l4_path_length": float(sum(step["displacement"] for step in l4_steps)),
                "l4_endpoint_displacement": distance(rho, full_l4),
                "l6_displacement": distance(rho, l6),
                "l4_ablations": ablations,
                "reversed_l4_endpoint_delta": distance(full_l4, reversed_l4),
                "identity_l4_displacement": distance(rho, identity_l4),
            }
        )
    return rows


def z3_ablation_coverage_fence(required_count: int, observed_count: int) -> dict:
    required = Int("required_ablation_roles")
    observed = Int("observed_ablation_roles")
    solver = Solver()
    solver.add(required == required_count, observed == observed_count)
    solver.add(observed < required)
    status = solver.check()
    return {
        "required_ablation_roles": required_count,
        "observed_ablation_roles": observed_count,
        "missing_role_contradiction": str(status),
        "pass": status == unsat,
        "scope": "integer coverage fence for the finite three-channel L4 ablation only",
    }


def main() -> int:
    classification = "classical_baseline"
    promotion_allowed = False
    parent = parent_receipt()
    rows = evaluate_states()
    channel_names = ["depolarizing", "amplitude_damping", "z_dephasing"]
    max_ablation_delta = {
        name: max(row["l4_ablations"][f"without_{name}"]["endpoint_delta_from_full_l4"] for row in rows)
        for name in channel_names
    }
    active_l6 = [row["label"] for row in rows if row["l6_displacement"] > 1e-3]
    inactive_l6 = [row["label"] for row in rows if row["l6_displacement"] <= 1e-3]
    max_reverse_delta = max(row["reversed_l4_endpoint_delta"] for row in rows)
    max_identity_l4 = max(row["identity_l4_displacement"] for row in rows)
    path_minus_endpoint = [row["l4_path_length"] - row["l4_endpoint_displacement"] for row in rows]

    positive = {
        "parent_receipt_exists_and_passes": {"parent": parent, "pass": parent["exists"] and parent["all_pass"]},
        "all_l4_channels_have_detectable_ablation_role": {
            "max_ablation_delta_by_removed_channel": max_ablation_delta,
            "pass": all(value > EPS for value in max_ablation_delta.values()),
        },
        "l4_path_length_bounds_endpoint_displacement": {
            "min_path_minus_endpoint": float(min(path_minus_endpoint)),
            "pass": all(value >= -1e-7 for value in path_minus_endpoint),
        },
        "l6_selectively_activates_on_entropy_decrease_states": {
            "active_l6_labels": active_l6,
            "inactive_l6_labels": inactive_l6,
            "pass": bool(active_l6) and bool(inactive_l6) and len(active_l6) < len(rows),
        },
    }
    negative = {
        "identity_l4_control_has_no_displacement": {
            "max_identity_l4_displacement": max_identity_l4,
            "pass": max_identity_l4 <= 2e-7,
        },
        "reversed_l4_order_changes_endpoint": {
            "max_reversed_endpoint_delta": max_reverse_delta,
            "pass": max_reverse_delta > EPS,
        },
        "single_shell_story_rejected": {
            "l4_active_count": sum(1 for row in rows if row["l4_endpoint_displacement"] > 1e-3),
            "l6_active_count": len(active_l6),
            "pass": sum(1 for row in rows if row["l4_endpoint_displacement"] > 1e-3) != len(active_l6),
        },
        "z3_ablation_coverage_fence": z3_ablation_coverage_fence(
            required_count=3,
            observed_count=sum(1 for value in max_ablation_delta.values() if value > EPS),
        ),
    }
    closure_checks = {
        "parent_receipt": positive["parent_receipt_exists_and_passes"]["pass"],
        "l4_channel_ablation": positive["all_l4_channels_have_detectable_ablation_role"]["pass"],
        "l4_path_geometry": positive["l4_path_length_bounds_endpoint_displacement"]["pass"],
        "l6_selectivity": positive["l6_selectively_activates_on_entropy_decrease_states"]["pass"],
        "identity_control": negative["identity_l4_control_has_no_displacement"]["pass"],
        "order_control": negative["reversed_l4_order_changes_endpoint"]["pass"],
        "single_shell_rejection": negative["single_shell_story_rejected"]["pass"],
    }
    boundary = {
        "finite_local_state_set_only": {"state_count": len(rows), "pass": len(rows) == 7},
        "parent_read_confirms_old_receipt_stays_supporting": {
            "parent_classification": parent["classification"],
            "pass": parent["classification"] == "supporting",
        },
        "closure_candidate_defined_by_finite_checks": {
            "definition": (
                "closure_candidate means the finite parent receipt passes, all three L4 sub-projection "
                "ablations are detectable, L4 path/order controls pass, L6 activation is selective, "
                "and the single-shell explanation is rejected on this local state set."
            ),
            "checks": closure_checks,
            "pass": all(closure_checks.values()),
        },
        "not_admission_gate": {
            "classification": classification,
            "promotion_allowed": promotion_allowed,
            "pass": classification in {"classical_baseline", "supporting"} and promotion_allowed is False,
        },
        "no_qit_gstack_axis_bridge_or_nonclassical_promotion": {
            "promotion_allowed": promotion_allowed,
            "blocked_until": "shell/constraint coupling audit and stage-gate admission",
            "pass": promotion_allowed is False,
        },
    }
    all_pass = all(item["pass"] for group in (positive, negative, boundary) for item in group.values())
    result = {
        "name": "constraint_shells_ablation_closure",
        "classification": classification,
        "classification_note": "Finite constraint-shell ablation closure candidate; lego-stage evidence only.",
        "generated_at": datetime.now(UTC).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "parents": [parent],
        "finite_state_rows": rows,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "closure_candidate": all_pass,
            "promotion_allowed": promotion_allowed,
            "active_l6_count": len(active_l6),
            "max_reversed_l4_endpoint_delta": max_reverse_delta,
            "scope_note": "Ablation separates L4 channel roles and L6 activation on the finite local shell state set only.",
        },
        "all_pass": all_pass,
        "divergence_log": (
            "This packet rejects a single-shell explanation: L4 sub-projection ablations, L4 order reversal, "
            "and L6 entropy activation produce separable finite effects."
        ),
    }
    result = apply_default_receipt_boundary(
        result,
        source_name="sim_constraint_shells_ablation_closure",
        target="Use as bounded constraint-shell closure-candidate evidence before shell/constraint assembly.",
    )
    result["promotion_condition"] = "Requires downstream shell/constraint coupling audit and explicit stage-gate admission."
    result["blocked_until"] = "shell/constraint coupling audit and stage-gate admission"

    out_path = RESULTS_DIR / "constraint_shells_ablation_closure_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
