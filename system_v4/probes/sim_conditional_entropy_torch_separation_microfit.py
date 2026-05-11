#!/usr/bin/env python3
"""PyTorch conditional-entropy separation microfit.

This bounded tool-lego fit keeps conditional entropy separate from coherent
information on the same fixed two-qubit carriers. It is local tool-lego evidence
only, not a coupling, bridge, QIT, GStack, axis, engine, or nonclassical
admission claim.
"""

from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime

import sympy as sp
import torch
import z3


CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION
divergence_log = (
    "Bounded PyTorch conditional-entropy separation microfit on fixed two-qubit "
    "density matrices. PyTorch is load-bearing for partial traces, eigenvalue "
    "entropy, and sign witnesses; sympy and z3 are supportive finite algebra "
    "checks. This is not a coupling, bridge, QIT, GStack, axis, engine, or "
    "nonclassical admission."
)

LEGO_IDS = ["conditional_entropy"]
PRIMARY_LEGO_IDS = ["conditional_entropy"]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing two-qubit partial traces, eigvalsh entropy, and conditional-entropy sign witnesses",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive symbolic identity Ic(A>B) = -H(A|B) for the same entropy terms",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite Real-arithmetic guard for sign-complement and dimension constraints",
    },
    "numpy": {"tried": False, "used": False, "reason": "not needed; torch carries the numeric entropy path"},
    "qutip": {"tried": False, "used": False, "reason": "not needed for this PyTorch-focused separation row"},
    "qiskit": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "sympy": "supportive",
    "z3": "supportive",
    "numpy": None,
    "qutip": None,
    "qiskit": None,
    "cvc5": None,
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
PARENT_RESULTS = {
    "conditional_entropy": RESULT_DIR / "conditional_entropy_results.json",
    "coherent_information_measure": RESULT_DIR / "coherent_information_measure_results.json",
    "mutual_information_measure": RESULT_DIR / "mutual_information_measure_results.json",
    "reduced_state_object": RESULT_DIR / "reduced_state_object_results.json",
    "pytorch_capability": RESULT_DIR / "pytorch_capability_results.json",
}
REGISTRY_PATH = PROBE_DIR.parents[1] / "system_v5" / "docs" / "17_actual_lego_registry.md"
OUT_PATH = RESULT_DIR / "conditional_entropy_torch_separation_microfit_results.json"
EPS = 1e-10
CDTYPE = torch.complex128


def source_receipts() -> dict[str, object]:
    rows = {}
    for key, path in PARENT_RESULTS.items():
        if not path.exists():
            rows[key] = {"path": str(path), "exists": False, "all_pass": False}
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        rows[key] = {
            "path": str(path),
            "exists": True,
            "all_pass": bool(data.get("all_pass") or data.get("summary", {}).get("all_pass")),
            "classification": data.get("classification"),
        }
    return rows


def dm(psi: torch.Tensor) -> torch.Tensor:
    ket = psi.reshape(-1, 1).to(CDTYPE)
    return ket @ ket.conj().T


def product_state(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return dm(torch.kron(a.to(CDTYPE), b.to(CDTYPE)))


def partial_trace_A(rho_ab: torch.Tensor) -> torch.Tensor:
    # Computes Tr_A[rho_AB] = rho_B; indices are (A, B, A', B').
    return torch.einsum("abac->bc", rho_ab.reshape(2, 2, 2, 2))


def partial_trace_B(rho_ab: torch.Tensor) -> torch.Tensor:
    # Computes Tr_B[rho_AB] = rho_A; indices are (A, B, A', B').
    return torch.einsum("abcb->ac", rho_ab.reshape(2, 2, 2, 2))


def entropy_vn(rho: torch.Tensor) -> torch.Tensor:
    herm = 0.5 * (rho + rho.conj().T)
    eigs = torch.linalg.eigvalsh(herm).real.clamp_min(0.0)
    positive = eigs[eigs > 1e-14]
    if positive.numel() == 0:
        return torch.tensor(0.0, dtype=torch.float64)
    return -torch.sum(positive * torch.log2(positive))


def conditional_entropy_A_given_B(rho_ab: torch.Tensor) -> torch.Tensor:
    return entropy_vn(rho_ab) - entropy_vn(partial_trace_A(rho_ab))


def coherent_information_A_to_B(rho_ab: torch.Tensor) -> torch.Tensor:
    return entropy_vn(partial_trace_A(rho_ab)) - entropy_vn(rho_ab)


def mutual_information(rho_ab: torch.Tensor) -> torch.Tensor:
    return entropy_vn(partial_trace_A(rho_ab)) + entropy_vn(partial_trace_B(rho_ab)) - entropy_vn(rho_ab)


def states() -> dict[str, torch.Tensor]:
    zero = torch.tensor([1.0, 0.0], dtype=CDTYPE)
    one = torch.tensor([0.0, 1.0], dtype=CDTYPE)
    plus = (zero + one) / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    bell_vec = (torch.kron(zero, zero) + torch.kron(one, one)) / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    bell = dm(bell_vec)
    classical = 0.5 * product_state(zero, zero) + 0.5 * product_state(one, one)
    werner_low = 0.2 * bell + 0.8 * torch.eye(4, dtype=CDTYPE) / 4.0
    werner_high = 0.8 * bell + 0.2 * torch.eye(4, dtype=CDTYPE) / 4.0
    return {
        "product_00": product_state(zero, zero),
        "product_0_plus": product_state(zero, plus),
        "classical_00_11_mix": classical,
        "bell_phi_plus": bell,
        "werner_low_0p2": werner_low,
        "werner_high_0p8": werner_high,
    }


def torch_entropy_rows() -> dict[str, object]:
    rows = {}
    for name, rho in states().items():
        h_a_given_b = float(conditional_entropy_A_given_B(rho).item())
        ic_a_to_b = float(coherent_information_A_to_B(rho).item())
        mi = float(mutual_information(rho).item())
        rows[name] = {
            "H_A_given_B": h_a_given_b,
            "Ic_A_to_B": ic_a_to_b,
            "mutual_information": mi,
            "sign_complement_gap": abs(h_a_given_b + ic_a_to_b),
            "pass": abs(h_a_given_b + ic_a_to_b) < EPS and mi >= -EPS,
        }
    return {"rows": rows, "pass": all(row["pass"] for row in rows.values())}


def sign_and_separation_checks(rows: dict[str, object]) -> dict[str, object]:
    product = rows["product_00"]["H_A_given_B"]
    classical = rows["classical_00_11_mix"]["H_A_given_B"]
    bell = rows["bell_phi_plus"]["H_A_given_B"]
    werner_low = rows["werner_low_0p2"]["H_A_given_B"]
    werner_high = rows["werner_high_0p8"]["H_A_given_B"]
    checks = {
        "pure_product_zero": {"value": product, "pass": abs(product) < EPS},
        "classical_mixture_nonnegative": {"value": classical, "pass": classical >= -EPS},
        "bell_negative_conditional_entropy": {"value": bell, "pass": bell < -1.0 + EPS},
        "werner_order_has_threshold_pressure": {
            "low": werner_low,
            "high": werner_high,
            "pass": werner_high < werner_low - EPS,
        },
        "conditional_entropy_not_mutual_information": {
            "bell_H_A_given_B": bell,
            "bell_MI": rows["bell_phi_plus"]["mutual_information"],
            "pass": abs(bell - rows["bell_phi_plus"]["mutual_information"]) > 1.0,
        },
    }
    return {"rows": checks, "pass": all(row["pass"] for row in checks.values())}


def sympy_identity_check() -> dict[str, object]:
    s_ab, s_b = sp.symbols("S_AB S_B", real=True)
    h_a_given_b = s_ab - s_b
    ic_a_to_b = s_b - s_ab
    return {
        "H_A_given_B": str(h_a_given_b),
        "Ic_A_to_B": str(ic_a_to_b),
        "H_plus_Ic": str(sp.simplify(h_a_given_b + ic_a_to_b)),
        "pass": bool(sp.simplify(h_a_given_b + ic_a_to_b) == 0),
    }


def z3_guard_checks() -> dict[str, object]:
    s_ab, s_b, h, ic = z3.Reals("S_AB S_B H_A_given_B Ic_A_to_B")
    finite_identity = z3.Solver()
    finite_identity.add(s_ab >= 0, s_b >= 0, h == s_ab - s_b, ic == s_b - s_ab)
    finite_identity.add(h + ic != 0)

    negative_conditional_positive_ic = z3.Solver()
    negative_conditional_positive_ic.add(h < 0, ic == -h, ic <= 0)

    da, db, dim = z3.Ints("da db dim")
    dim_guard = z3.Solver()
    dim_guard.add(da == 2, db == 2, dim == 4, da * db == dim)
    wrong_dim = z3.Solver()
    wrong_dim.add(da == 2, db == 2, dim == 3, da * db == dim)
    return {
        "identity_violation_unsat": {
            "z3_result": str(finite_identity.check()),
            "pass": finite_identity.check() == z3.unsat,
        },
        "negative_H_requires_positive_Ic_under_identity": {
            "z3_result": str(negative_conditional_positive_ic.check()),
            "pass": negative_conditional_positive_ic.check() == z3.unsat,
        },
        "valid_2x2_joint_dim": {"z3_result": str(dim_guard.check()), "pass": dim_guard.check() == z3.sat},
        "reject_wrong_joint_dim": {"z3_result": str(wrong_dim.check()), "pass": wrong_dim.check() == z3.unsat},
    }


def boundary_checks() -> dict[str, object]:
    registry_text = REGISTRY_PATH.read_text(encoding="utf-8") if REGISTRY_PATH.exists() else ""
    rows = {
        "primary_lego_registered": {
            "primary_lego_ids": PRIMARY_LEGO_IDS,
            "registry_path": str(REGISTRY_PATH),
            "boundary_note": "Registry presence is not promotion; this row remains tool-lego fit evidence only.",
            "pass": PRIMARY_LEGO_IDS == ["conditional_entropy"] and "conditional_entropy" in registry_text,
        },
        "no_neighbor_lego_credit": {"lego_ids": LEGO_IDS, "pass": LEGO_IDS == ["conditional_entropy"]},
        "classification_is_tool_lego_fit_probe": {"classification": CLASSIFICATION, "pass": CLASSIFICATION == "tool_lego_fit_probe"},
    }
    return {"rows": rows, "pass": all(row["pass"] for row in rows.values())}


def main() -> None:
    receipts = source_receipts()
    prerequisite = {
        "source_receipts": receipts,
        "all_available_and_passing": all(row["exists"] and row["all_pass"] for row in receipts.values()),
        "note": "Prerequisite receipts must exist and pass; their canonical status is not promoted.",
    }
    torch_rows = torch_entropy_rows()
    positive = {
        "torch_conditional_entropy_rows": torch_rows,
        "sign_and_separation_checks": sign_and_separation_checks(torch_rows["rows"]),
    }
    negative = {
        "z3_guard_checks": {
            **z3_guard_checks(),
        }
    }
    negative["z3_guard_checks"]["pass"] = all(row["pass"] for row in negative["z3_guard_checks"].values())
    boundary = {
        "sympy_identity_check": sympy_identity_check(),
        "scope_and_promotion_boundary": boundary_checks(),
    }
    evidence_all_pass = all(row["pass"] for group in (positive, negative, boundary) for row in group.values())
    all_pass = bool(prerequisite["all_available_and_passing"] and evidence_all_pass)
    result = {
        "name": "conditional_entropy_torch_separation_microfit",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "tool_lego_fit_probe",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {key: str(path) for key, path in PARENT_RESULTS.items()},
        "prerequisite": prerequisite,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": all_pass,
        "summary": {
            "all_pass": all_pass,
            "load_bearing_tools": ["pytorch"],
            "supportive_tools": ["sympy", "z3"],
            "claim_ceiling": "local conditional-entropy tool-lego fit only",
            "promotion_allowed": False,
        },
        "claim_ceiling": "local conditional-entropy tool-lego fit only; no coupling, bridge, QIT, GStack, axis, engine, or nonclassical admission",
        "promotion_condition": "Requires separate coupling/coexistence/topology/operator receipts and explicit stage-gate approval.",
        "blocked_until": "downstream coupling evidence exists and stage gate admits it",
        "demotion_condition": "Demote if parent receipts disappear, torch entropy witnesses fail, or the result is used as bridge/QIT/axis proof.",
        "out_of_scope": ["QIT engine admission", "GStack admission", "axis promotion", "nonclassical proof", "channel capacity claim"],
        "timestamp": datetime.now(UTC).isoformat(),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(OUT_PATH)


if __name__ == "__main__":
    main()
