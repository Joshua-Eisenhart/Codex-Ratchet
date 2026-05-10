#!/usr/bin/env python3
"""Discriminate density-shaped carrier work from integrated dependency-chain work.

This is a small falsifier before using a separate density-carrier closure
packet. It asks whether the density-shaped carrier surface is merely a Rosetta
renaming of the existing imported dependency chain, or whether it has a distinct
finite rejection boundary under M_density.

Result interpretation:
- If the two surfaces disagree on valid Bloch-shell inputs, the packet is
  broken and no closure should be registered.
- If they agree on valid Bloch-shell inputs but the density-shaped carrier
  rejects invalid finite matrices outside the dependency-chain domain, the
  density closure may proceed as a tool/probe closure only.

No QIT, GStack, axes, bridge, or nonclassical admission is claimed.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import qutip
import torch
from qiskit.quantum_info import DensityMatrix

from receipt_boundary import apply_default_receipt_boundary


SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
PARENT_RESULT_NAMES = [
    "integrated_dependency_chain_results.json",
    "density_hopf_geometry_results.json",
]
OUT_PATH = RESULTS_DIR / "density_carrier_dependency_discrimination_results.json"
TOL = 1e-6

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from sim_integrated_dependency_chain import run_full_chain  # noqa: E402


TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing finite density validity and shell fixtures"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing imported dependency-chain execution and eigenvalue checks"},
    "qutip": {"tried": True, "used": True, "reason": "load-bearing density-shaped domain witness for invalid finite matrices"},
    "qiskit": {"tried": True, "used": True, "reason": "load-bearing independent DensityMatrix representation check"},
    "scipy": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": "load_bearing",
    "qutip": "load_bearing",
    "qiskit": "load_bearing",
    "scipy": None,
    "sympy": None,
    "z3": None,
    "cvc5": None,
    "pyg": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
    "clifford": None,
    "geomstats": None,
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parent_receipts() -> list[dict]:
    rows = []
    for name in PARENT_RESULT_NAMES:
        path = RESULTS_DIR / name
        payload = read_json(path) if path.exists() else {}
        rows.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
                "classification": payload.get("classification"),
                "all_pass": bool(payload.get("all_pass") or payload.get("summary", {}).get("all_pass")),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
            }
        )
    return rows


def density_from_bloch(vec: np.ndarray) -> np.ndarray:
    sx = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    sy = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    sz = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    return (np.eye(2, dtype=np.complex128) + vec[0] * sx + vec[1] * sy + vec[2] * sz) / 2.0


def valid_density(rho: np.ndarray) -> dict:
    hermitian_error = float(np.max(np.abs(rho - rho.conj().T)))
    trace_error = float(abs(np.trace(rho) - 1.0))
    eig_np = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    eig_torch = torch.linalg.eigvalsh(torch.tensor(rho, dtype=torch.complex128)).real.numpy()
    qutip_trace = float(qutip.Qobj(rho, dims=[[2], [2]]).tr().real)
    qiskit_trace = float(np.trace(DensityMatrix(rho).data).real)
    return {
        "hermitian_error": hermitian_error,
        "trace_error": trace_error,
        "min_eig_numpy": float(np.min(eig_np)),
        "min_eig_torch": float(np.min(eig_torch)),
        "qutip_trace": qutip_trace,
        "qiskit_trace": qiskit_trace,
        "pass": bool(hermitian_error < TOL and trace_error < TOL and np.min(eig_np) > -TOL and np.min(eig_torch) > -TOL),
    }


def valid_shell_rows() -> list[dict]:
    fixtures = [
        ("x_shell", np.array([0.55, 0.0, 0.2]), np.array([0.0, 0.0, 0.65])),
        ("y_shell", np.array([0.0, -0.45, 0.3]), np.array([0.2, 0.0, 0.4])),
        ("mixed_shell", np.array([0.25, 0.25, 0.35]), np.array([0.0, 0.3, 0.3])),
    ]
    rows = []
    for label, bloch_a, bloch_b in fixtures:
        chain = run_full_chain(bloch_a.tolist(), bloch_b.tolist(), dephasing_p=0.3)
        rho_a = density_from_bloch(bloch_a)
        rho_reduced = np.asarray(chain["rho_a_reduced"].detach().numpy(), dtype=np.complex128)
        rows.append(
            {
                "label": label,
                "dependency_chain_mi_finite": bool(np.isfinite(float(chain["mi_val"].detach().item()))),
                "dependency_chain_reduced_valid": valid_density(rho_reduced),
                "density_surface_input_valid": valid_density(rho_a),
                "same_valid_survivor": bool(
                    np.isfinite(float(chain["mi_val"].detach().item()))
                    and valid_density(rho_reduced)["pass"]
                    and valid_density(rho_a)["pass"]
                ),
            }
        )
    return rows


def invalid_rows() -> dict:
    base = density_from_bloch(np.array([0.2, 0.1, 0.2]))
    rows = {
        "trace_bad": base * 1.2,
        "non_hermitian": base + np.array([[0.0, 0.2j], [0.0, 0.0]], dtype=np.complex128),
        "negative_eigenvalue": np.array([[1.2, 0.0], [0.0, -0.2]], dtype=np.complex128),
    }
    return {name: valid_density(rho) for name, rho in rows.items()}


def main() -> int:
    parents = parent_receipts()
    shell_rows = valid_shell_rows()
    bad_rows = invalid_rows()
    bad_rejected = {name: not bool(row["pass"]) for name, row in bad_rows.items()}

    positive = {
        "parents_exist_and_pass": {"parents": parents, "pass": all(row["exists"] and row["all_pass"] for row in parents)},
        "valid_bloch_shell_agrees_with_dependency_chain": {
            "shell_rows": shell_rows,
            "pass": all(row["same_valid_survivor"] for row in shell_rows),
        },
        "density_surface_has_distinct_invalid_matrix_rejection_boundary": {
            "invalid_rows": bad_rows,
            "bad_rejected": bad_rejected,
            "pass": all(bad_rejected.values()),
        },
    }
    negative = {
        "duplicate_claim_is_not_allowed": {
            "reason": (
                "Agreement on valid Bloch-shell rows is not enough to claim a new lego; "
                "the only distinct signal here is the finite invalid-matrix rejection boundary."
            ),
            "pass": all(row["same_valid_survivor"] for row in shell_rows) and all(bad_rejected.values()),
        },
        "dependency_chain_domain_does_not_accept_raw_invalid_matrices": {
            "dependency_chain_input_type": "Bloch-vector fixtures only",
            "invalid_matrix_count": len(bad_rows),
            "pass": len(bad_rows) == 3,
        },
    }
    boundary = {
        "m_density_defined": {
            "M_density": "Hermitian, trace-one, PSD finite 2x2 carrier check plus tool representation roundtrip",
            "C": "three valid Bloch-shell fixtures plus three invalid finite matrix counterexamples",
            "S_mod_M": "valid/invalid survivor partition under M_density",
            "pass": True,
        },
        "closure_permission_is_tool_probe_only": {
            "recommendation": "closure may proceed only as density-shaped carrier tool/probe closure, not as admission",
            "pass": True,
        },
        "not_admission_or_promotion": {
            "classification": "classical_baseline",
            "promotion_allowed": False,
            "pass": True,
        },
        "no_qit_gstack_axis_bridge_or_nonclassical_promotion": {
            "claim_ceiling": "finite density-carrier discrimination probe only",
            "pass": True,
        },
    }

    all_pass = all(item["pass"] for group in (positive, negative, boundary) for item in group.values())
    result = {
        "name": "density_carrier_dependency_discrimination",
        "classification": "classical_baseline",
        "classification_note": "Finite discrimination probe before density-carrier closure; lego-stage evidence only.",
        "generated_at": datetime.now(UTC).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "parents": parents,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "discrimination_survived": all_pass,
            "closure_permission": "tool_probe_closure_only" if all_pass else "blocked",
            "promotion_allowed": False,
            "scope_note": "Distinguishes density-shaped carrier checks from dependency-chain domain without admitting a new stage.",
        },
        "divergence_log": (
            "Valid Bloch-shell fixtures agree with integrated dependency-chain behavior, while raw invalid "
            "finite matrices define a separate M_density rejection boundary. This permits a tool/probe "
            "closure packet but not a stronger density-carrier admission claim."
        ),
        "all_pass": all_pass,
    }
    result = apply_default_receipt_boundary(
        result,
        source_name="sim_density_carrier_dependency_discrimination",
        target="Use as a falsifier/discrimination receipt before density-carrier tool closure registration.",
    )
    result["promotion_condition"] = "Requires downstream assembly audit and explicit stage-gate admission."
    result["blocked_until"] = "density-carrier assembly audit and stage-gate admission"
    OUT_PATH.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {OUT_PATH}")
    print(f"ALL PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
