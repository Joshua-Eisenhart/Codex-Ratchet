#!/usr/bin/env python3
"""Canonical Stage 1 F01 finite distinguishability probe.

Finite map:
    R: X x P -> [0, 1]

Quotient:
    x ~ y iff R(x, p) = R(y, p) for every finite probe p in P.

This file is deliberately narrow. It proves one F01 structural claim:
states x_0 and x_1 are distinguished by the full finite probe set, and the
same claim fails under the probe-erased negative control.
"""

import jax

jax.config.update("jax_enable_x64", True)

import json
import pathlib
import sys
import time
from fractions import Fraction
from typing import Any

import jax.numpy as jnp
import sympy as sp
import torch

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OBJECT_ID = "F01_finite_distinguishability"
OUT_PATH = RESULT_DIR / f"{OBJECT_ID}_results.json"

DTYPE = torch.float64
EPS = 0.5
SCALES = (8, 16, 32, 64)
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim-bearing numeric carrier for R(x,p), quotient class counts, controls, and scale ladder.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 parity mirror recomputing response gaps and quotient class counts without NumPy.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via load_bearing_proof.smt_load_bearing; z3 variables are bound to measured real/control observables.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check via load_bearing_proof.smt_load_bearing cvc5_claim_pairs on the same measured observables.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact rational mirror for the measured response gaps and quotient class counts before helper-bound SMT proof.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not used for claim-bearing computation.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not relevant to this finite rational response-map probe.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "numpy": "None",
    "scipy": "None",
}


def response_rows(n: int, *, final_separator: bool) -> list[list[Fraction]]:
    """Build a rational response map with one deliberately removable separator.

    Probes p_0..p_{n-3} distinguish x_2..x_{n-1}. The final probe separates
    x_0 from x_1. Removing that final probe merges only x_0 and x_1.
    """
    rows: list[list[Fraction]] = []
    for x in range(n):
        row: list[Fraction] = []
        for p in range(n):
            if p == n - 1:
                if final_separator:
                    if x == 0:
                        row.append(Fraction(0, 1))
                    elif x == 1:
                        row.append(Fraction(1, 1))
                    else:
                        row.append(Fraction(1, 2))
                else:
                    row.append(Fraction(0, 1))
            elif p < n - 2 and x == p + 2:
                row.append(Fraction(1, 1))
            else:
                row.append(Fraction(0, 1))
        rows.append(row)
    return rows


def probe_erased_rows(n: int) -> list[list[Fraction]]:
    return [[Fraction(0, 1)] for _ in range(n)]


def remove_final_probe(rows: list[list[Fraction]]) -> list[list[Fraction]]:
    return [row[:-1] for row in rows]


def torch_response(rows: list[list[Fraction]]) -> torch.Tensor:
    return torch.tensor([[float(v) for v in row] for row in rows], dtype=DTYPE)


def jax_response(rows: list[list[Fraction]]) -> jax.Array:
    return jnp.array([[float(v) for v in row] for row in rows], dtype=jnp.float64)


def response_gap_torch(response: torch.Tensor, i: int = 0, j: int = 1) -> float:
    return float(torch.max(torch.abs(response[i] - response[j])).item())


def response_gap_jax(response: jax.Array, i: int = 0, j: int = 1) -> float:
    return float(jnp.max(jnp.abs(response[i] - response[j])).item())


def class_count_from_torch(response: torch.Tensor) -> int:
    signatures: list[tuple[float, ...]] = []
    for row in response:
        sig = tuple(round(float(v.item()), 12) for v in row)
        if sig not in signatures:
            signatures.append(sig)
    return len(signatures)


def class_count_from_jax(response: jax.Array) -> int:
    eq = jnp.all(jnp.abs(response[:, None, :] - response[None, :, :]) <= 1.0e-12, axis=2)
    prior = jnp.tril(eq, k=-1)
    representatives = jnp.logical_not(jnp.any(prior, axis=1))
    return int(jnp.sum(representatives).item())


def partition_summary(rows: list[list[Fraction]]) -> dict[str, Any]:
    classes: dict[tuple[Fraction, ...], list[int]] = {}
    for x, row in enumerate(rows):
        classes.setdefault(tuple(row), []).append(x)
    ordered = sorted(classes.items(), key=lambda item: item[1][0])
    ids = [-1] * len(rows)
    for class_id, (_, members) in enumerate(ordered):
        for member in members:
            ids[member] = class_id
    return {
        "class_count": len(ordered),
        "class_ids_by_state": ids,
        "classes": [
            {
                "class_id": class_id,
                "members": members,
                "response_signature": [str(v) for v in signature],
            }
            for class_id, (signature, members) in enumerate(ordered)
        ],
    }


def sympy_gap(rows: list[list[Fraction]], i: int = 0, j: int = 1) -> Fraction:
    matrix = sp.Matrix([[sp.Rational(v.numerator, v.denominator) for v in row] for row in rows])
    gaps = [abs(matrix[i, p] - matrix[j, p]) for p in range(matrix.shape[1])]
    return Fraction(max(gaps))


def sympy_class_count(rows: list[list[Fraction]]) -> int:
    signatures = {
        tuple(sp.Rational(v.numerator, v.denominator) for v in row)
        for row in rows
    }
    return len(signatures)


def jax_vs_torch_delta(rows: list[list[Fraction]]) -> float:
    torch_values = torch_response(rows)
    jax_values = jax_response(rows)
    torch_as_jax = jnp.array(torch_values.detach().cpu().tolist(), dtype=jnp.float64)
    return float(jnp.max(jnp.abs(jax_values - torch_as_jax)).item())


def smt_distinguishability_proof(real_gap: float, control_gap: float, claim: str) -> dict[str, Any]:
    return smt_load_bearing(
        claim=claim,
        real_measured={"max_probe_response_gap": real_gap, "eps": EPS},
        control_measured={"max_probe_response_gap": control_gap, "eps": EPS},
        claim_builder=lambda v: v["max_probe_response_gap"] >= v["eps"],
        cvc5_claim_pairs=[("max_probe_response_gap", ">=", "eps")],
    )


def proof_score(proof: dict[str, Any], engine: str) -> float:
    if engine == "z3":
        return float(
            proof.get("real_claim_verdict") == "sat"
            and proof.get("negated_claim_verdict") == "unsat"
            and proof.get("differ") is True
            and proof.get("bound_to_measured") is True
        )
    if engine == "cvc5":
        return float(
            proof.get("cvc5_real_verdict") == "sat"
            and proof.get("cvc5_control_verdict") == "unsat"
            and proof.get("differ") is True
            and proof.get("bound_to_measured") is True
        )
    raise ValueError(f"unknown proof engine: {engine}")


def verdict_sat_score(proof: dict[str, Any], engine: str, side: str) -> float:
    if engine == "z3":
        key = "real_claim_verdict" if side == "real" else "negated_claim_verdict"
    elif engine == "cvc5":
        key = "cvc5_real_verdict" if side == "real" else "cvc5_control_verdict"
    else:
        raise ValueError(f"unknown proof engine: {engine}")
    return float(proof.get(key) == "sat")


def scale_rung(n: int) -> dict[str, Any]:
    full_rows = response_rows(n, final_separator=True)
    separator_removed_rows = remove_final_probe(full_rows)
    probe_erased = probe_erased_rows(n)

    full_torch = torch_response(full_rows)
    separator_removed_torch = torch_response(separator_removed_rows)
    probe_erased_torch = torch_response(probe_erased)

    full_jax = jax_response(full_rows)
    separator_removed_jax = jax_response(separator_removed_rows)
    probe_erased_jax = jax_response(probe_erased)

    torch_full_classes = class_count_from_torch(full_torch)
    torch_separator_removed_classes = class_count_from_torch(separator_removed_torch)
    torch_probe_erased_classes = class_count_from_torch(probe_erased_torch)
    torch_real_gap = response_gap_torch(full_torch)
    torch_separator_removed_gap = response_gap_torch(separator_removed_torch)
    torch_probe_erased_gap = response_gap_torch(probe_erased_torch)

    jax_full_classes = class_count_from_jax(full_jax)
    jax_separator_removed_classes = class_count_from_jax(separator_removed_jax)
    jax_probe_erased_classes = class_count_from_jax(probe_erased_jax)
    jax_real_gap = response_gap_jax(full_jax)
    jax_separator_removed_gap = response_gap_jax(separator_removed_jax)
    jax_probe_erased_gap = response_gap_jax(probe_erased_jax)

    pass_rung = (
        torch_full_classes == n
        and torch_separator_removed_classes == n - 1
        and torch_probe_erased_classes == 1
        and jax_full_classes == torch_full_classes
        and jax_separator_removed_classes == torch_separator_removed_classes
        and jax_probe_erased_classes == torch_probe_erased_classes
        and abs(torch_real_gap - 1.0) <= 1.0e-12
        and abs(torch_separator_removed_gap) <= 1.0e-12
        and abs(torch_probe_erased_gap) <= 1.0e-12
        and abs(jax_real_gap - torch_real_gap) <= 1.0e-12
        and abs(jax_separator_removed_gap - torch_separator_removed_gap) <= 1.0e-12
        and abs(jax_probe_erased_gap - torch_probe_erased_gap) <= 1.0e-12
        and jax_vs_torch_delta(full_rows) <= 1.0e-12
    )

    return {
        "sites_or_qubits": n,
        "state_count": n,
        "probe_count": n,
        "operator_count": n,
        "path_count": n,
        "dense_state_closure_used": False,
        "torch_full_class_count": torch_full_classes,
        "torch_separator_removed_class_count": torch_separator_removed_classes,
        "torch_probe_erased_class_count": torch_probe_erased_classes,
        "torch_real_gap_x0_x1": torch_real_gap,
        "torch_separator_removed_gap_x0_x1": torch_separator_removed_gap,
        "torch_probe_erased_gap_x0_x1": torch_probe_erased_gap,
        "jax_full_class_count": jax_full_classes,
        "jax_separator_removed_class_count": jax_separator_removed_classes,
        "jax_probe_erased_class_count": jax_probe_erased_classes,
        "jax_real_gap_x0_x1": jax_real_gap,
        "jax_separator_removed_gap_x0_x1": jax_separator_removed_gap,
        "jax_probe_erased_gap_x0_x1": jax_probe_erased_gap,
        "jax_vs_pytorch_delta": jax_vs_torch_delta(full_rows),
        "partition": partition_summary(full_rows),
        "separator_removed_partition": partition_summary(separator_removed_rows),
        "probe_erased_partition": partition_summary(probe_erased),
        "pass": bool(pass_rung),
    }


def build_proofs(top: dict[str, Any]) -> dict[str, Any]:
    full_rows = response_rows(64, final_separator=True)
    separator_removed_rows = remove_final_probe(full_rows)
    probe_erased_control_rows = probe_erased_rows(64)

    real_gap = float(top["torch_real_gap_x0_x1"])
    control_gap = float(top["torch_probe_erased_gap_x0_x1"])
    separator_removed_gap = float(top["torch_separator_removed_gap_x0_x1"])
    sympy_full_gap = sympy_gap(full_rows)
    sympy_separator_removed_gap = sympy_gap(separator_removed_rows)
    sympy_probe_erased_gap = sympy_gap(probe_erased_control_rows)
    sympy_full_classes = sympy_class_count(full_rows)
    sympy_separator_removed_classes = sympy_class_count(separator_removed_rows)
    sympy_probe_erased_classes = sympy_class_count(probe_erased_control_rows)
    primary = smt_distinguishability_proof(
        real_gap,
        control_gap,
        "states_x0_x1_distinguished_by_full_probe_set_max_gap_ge_eps",
    )
    separator_removed = smt_distinguishability_proof(
        real_gap,
        separator_removed_gap,
        "states_x0_x1_distinguishability_lost_after_separator_probe_removed",
    )
    return {
        "distinguishing_gap_smt_load_bearing": primary,
        "separator_removed_negative_smt_recompute": separator_removed,
        "sympy_exact_observables": {
            "tool": "sympy",
            "full_max_gap_x0_x1": str(sympy_full_gap),
            "separator_removed_max_gap_x0_x1": str(sympy_separator_removed_gap),
            "probe_erased_max_gap_x0_x1": str(sympy_probe_erased_gap),
            "full_class_count": sympy_full_classes,
            "separator_removed_class_count": sympy_separator_removed_classes,
            "probe_erased_class_count": sympy_probe_erased_classes,
            "claim_threshold_eps": str(EPS),
            "full_claim_holds": bool(float(sympy_full_gap) >= EPS),
            "separator_removed_claim_holds": bool(float(sympy_separator_removed_gap) >= EPS),
            "probe_erased_claim_holds": bool(float(sympy_probe_erased_gap) >= EPS),
            "bound_to_measured": True,
            "pass": bool(
                float(sympy_full_gap) >= EPS
                and float(sympy_separator_removed_gap) < EPS
                and float(sympy_probe_erased_gap) < EPS
                and sympy_full_classes == 64
                and sympy_separator_removed_classes == 63
                and sympy_probe_erased_classes == 1
            ),
        },
    }


def build_tool_ablations(top: dict[str, Any], proofs: dict[str, Any]) -> dict[str, Any]:
    separator_removed = proofs["separator_removed_negative_smt_recompute"]
    sympy_observable = proofs["sympy_exact_observables"]
    full_classes = float(top["torch_full_class_count"])
    removed_classes = float(top["torch_separator_removed_class_count"])

    return {
        "separating_probe_structure_class_count": tool_ablation(
            "equiv_classes_with_full_probe_set_vs_final_probe_removed",
            baseline_value=full_classes,
            ablated_value=removed_classes,
            tool="torch",
        ),
        "jax_parity_class_count": tool_ablation(
            "jax_equiv_classes_with_full_probe_set_vs_final_probe_removed",
            baseline_value=float(top["jax_full_class_count"]),
            ablated_value=float(top["jax_separator_removed_class_count"]),
            tool="jax",
        ),
        "z3_distinguishability_flip": tool_ablation(
            "z3_helper_flip_score_full_probe_vs_separator_removed",
            baseline_value=verdict_sat_score(separator_removed, "z3", "real"),
            ablated_value=verdict_sat_score(separator_removed, "z3", "control"),
            tool="z3",
        ),
        "cvc5_distinguishability_flip": tool_ablation(
            "cvc5_helper_flip_score_full_probe_vs_separator_removed",
            baseline_value=verdict_sat_score(separator_removed, "cvc5", "real"),
            ablated_value=verdict_sat_score(separator_removed, "cvc5", "control"),
            tool="cvc5",
        ),
        "sympy_exact_gap": tool_ablation(
            "sympy_exact_max_gap_full_probe_vs_separator_removed",
            baseline_value=float(Fraction(sympy_observable["full_max_gap_x0_x1"])),
            ablated_value=float(Fraction(sympy_observable["separator_removed_max_gap_x0_x1"])),
            tool="sympy",
        ),
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(exist_ok=True)

    scale_rows = {n: scale_rung(n) for n in SCALES}
    top = scale_rows[64]
    proofs = build_proofs(top)
    ablations = build_tool_ablations(top, proofs)

    full_rows_64 = response_rows(64, final_separator=True)
    separator_removed_rows_64 = remove_final_probe(full_rows_64)
    probe_erased_rows_64 = probe_erased_rows(64)

    sympy_full_gap = sympy_gap(full_rows_64)
    sympy_separator_removed_gap = sympy_gap(separator_removed_rows_64)
    sympy_probe_erased_gap = sympy_gap(probe_erased_rows_64)
    sympy_full_classes = sympy_class_count(full_rows_64)
    sympy_separator_removed_classes = sympy_class_count(separator_removed_rows_64)
    sympy_probe_erased_classes = sympy_class_count(probe_erased_rows_64)

    scale_pass = all(row["pass"] for row in scale_rows.values())
    proof_pass = (
        proofs["distinguishing_gap_smt_load_bearing"]["real_claim_verdict"] == "sat"
        and proofs["distinguishing_gap_smt_load_bearing"]["negated_claim_verdict"] == "unsat"
        and proofs["distinguishing_gap_smt_load_bearing"]["differ"] is True
        and proofs["distinguishing_gap_smt_load_bearing"]["bound_to_measured"] is True
        and proofs["separator_removed_negative_smt_recompute"]["real_claim_verdict"] == "sat"
        and proofs["separator_removed_negative_smt_recompute"]["negated_claim_verdict"] == "unsat"
        and proofs["separator_removed_negative_smt_recompute"]["differ"] is True
        and proofs["separator_removed_negative_smt_recompute"]["bound_to_measured"] is True
        and sympy_full_gap == Fraction(1, 1)
        and sympy_separator_removed_gap == Fraction(0, 1)
        and sympy_probe_erased_gap == Fraction(0, 1)
    )
    ablation_pass = all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > 1.0e-12
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= 1.0e-12
        for row in ablations.values()
    )
    all_pass = bool(scale_pass and proof_pass and ablation_pass)

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(DTYPE),
        "response_shape_at_64": [64, 64],
        "class_count_full_probe_set": top["torch_full_class_count"],
        "class_count_separator_removed": top["torch_separator_removed_class_count"],
        "class_count_probe_erased": top["torch_probe_erased_class_count"],
        "max_gap_x0_x1_full_probe_set": top["torch_real_gap_x0_x1"],
        "max_gap_x0_x1_separator_removed": top["torch_separator_removed_gap_x0_x1"],
        "max_gap_x0_x1_probe_erased": top["torch_probe_erased_gap_x0_x1"],
        "claim": "max_p |R(x_0,p)-R(x_1,p)| >= eps",
        "eps": EPS,
        "pass": bool(top["pass"]),
    }

    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "class_count_full_probe_set": top["jax_full_class_count"],
        "class_count_separator_removed": top["jax_separator_removed_class_count"],
        "class_count_probe_erased": top["jax_probe_erased_class_count"],
        "max_gap_x0_x1_full_probe_set": top["jax_real_gap_x0_x1"],
        "max_gap_x0_x1_separator_removed": top["jax_separator_removed_gap_x0_x1"],
        "max_gap_x0_x1_probe_erased": top["jax_probe_erased_gap_x0_x1"],
        "pass": bool(
            top["jax_full_class_count"] == top["torch_full_class_count"]
            and top["jax_separator_removed_class_count"] == top["torch_separator_removed_class_count"]
            and top["jax_probe_erased_class_count"] == top["torch_probe_erased_class_count"]
            and abs(top["jax_real_gap_x0_x1"] - top["torch_real_gap_x0_x1"]) <= 1.0e-12
        ),
    }

    controls = {
        "probe_erased": {
            "description": "single constant probe R(x,p0)=0 for all states x",
            "negative_control_type": "probe-erased constant carrier",
            "class_count": top["torch_probe_erased_class_count"],
            "max_gap_x0_x1": top["torch_probe_erased_gap_x0_x1"],
            "distinguishing_claim_holds": False,
            "pass": bool(top["torch_probe_erased_class_count"] == 1 and top["torch_probe_erased_gap_x0_x1"] == 0.0),
        },
        "separator_removed": {
            "description": "remove the final probe p_{n-1} and recompute quotient classes",
            "negative_control_type": "separating-probe ablated carrier",
            "class_count": top["torch_separator_removed_class_count"],
            "max_gap_x0_x1": top["torch_separator_removed_gap_x0_x1"],
            "distinguishing_claim_holds": False,
            "pass": bool(
                top["torch_separator_removed_class_count"] == top["torch_full_class_count"] - 1
                and top["torch_separator_removed_gap_x0_x1"] == 0.0
            ),
        },
    }

    return {
        "sim_id": "sim_root_F01_finite_distinguishability_probe",
        "name": "sim_root_F01_finite_distinguishability_probe",
        "version": "2.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "object_id": OBJECT_ID,
        "finite_map": {
            "domain": "finite X x P with |X|=|P| in {8,16,32,64}; X={x_0,...,x_{n-1}}, P={p_0,...,p_{n-1}}",
            "codomain_or_output": "[0,1] response tensor R plus quotient X/~ where x~y iff all probe responses match",
            "definition": "R(x,p) is rational; p_{n-1} separates x_0 and x_1; p_0..p_{n-3} distinguish x_2..x_{n-1}",
        },
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite states X, finite probes/effects P, response R(x,p) in [0,1], quotient by equal response vectors",
            },
            "N01": {
                "status": "referenced_not_active",
                "statement": "noncommuting/order-sensitive operation/control root is not claimed by this one-root F01 packet",
            },
        },
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "canonical STAGE 1",
        "sim_execution_kind": "nonclassical",
        "sim_class": "constraint_probe",
        "carrier_layer": "finite response-map carrier",
        "carrier_realization": "torch float64 tensor from exact rational rows; no dense state closure and no NumPy bridge",
        "peps3d_embedding": "not_admitted_by_this_F01-only packet; downstream PEPS3D/manifold consumers remain blocked",
        "spinor_state": "not_applicable_to_this_F01-only finite response-map packet",
        "quaternion_action": "not_applicable",
        "dependency_receipts": ["root_stage_packet_no_lower_dependency"],
        "allowed_claims": [
            "F01 finite distinguishability for this response-map family",
            "x_0 and x_1 are distinguished by the full probe set and not distinguished after probe erasure",
            "quotient class count recomputes as n, n-1, and 1 for full, separator-removed, and probe-erased carriers",
        ],
        "promotion_blockers": [
            "N01 is not active in this packet",
            "no spinor/PEPS3D manifold carrier is admitted here",
            "no Xi/Phi0/Axis0/flux/FEP/gravity consumer is unlocked",
        ],
        "eligible_consumers": ["future bounded Stage-1 F01/N01 cross-check packets only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": float(max(row["jax_vs_pytorch_delta"] for row in scale_rows.values())),
        "proof_results": proofs,
        "controls": controls,
        "tool_ablations": ablations,
        "sympy_exact_result": {
            "full_max_gap_x0_x1": str(sympy_full_gap),
            "separator_removed_max_gap_x0_x1": str(sympy_separator_removed_gap),
            "probe_erased_max_gap_x0_x1": str(sympy_probe_erased_gap),
            "full_class_count": sympy_full_classes,
            "separator_removed_class_count": sympy_separator_removed_classes,
            "probe_erased_class_count": sympy_probe_erased_classes,
            "pass": bool(
                sympy_full_gap == Fraction(1, 1)
                and sympy_separator_removed_gap == Fraction(0, 1)
                and sympy_probe_erased_gap == Fraction(0, 1)
                and sympy_full_classes == 64
                and sympy_separator_removed_classes == 63
                and sympy_probe_erased_classes == 1
            ),
        },
        "scale_ladder": {
            "rungs": {
                str(n): {
                    "sites_or_qubits": row["sites_or_qubits"],
                    "state_count": row["state_count"],
                    "probe_count": row["probe_count"],
                    "operator_count": row["operator_count"],
                    "path_count": row["path_count"],
                    "dense_state_closure_used": row["dense_state_closure_used"],
                    "torch_full_class_count": row["torch_full_class_count"],
                    "torch_separator_removed_class_count": row["torch_separator_removed_class_count"],
                    "torch_probe_erased_class_count": row["torch_probe_erased_class_count"],
                    "jax_full_class_count": row["jax_full_class_count"],
                    "jax_separator_removed_class_count": row["jax_separator_removed_class_count"],
                    "jax_probe_erased_class_count": row["jax_probe_erased_class_count"],
                    "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
                    "pass": row["pass"],
                }
                for n, row in scale_rows.items()
            },
            "pass": bool(scale_pass),
        },
        "scale_details": scale_rows,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "pass_rule": "helper-bound SMT proof flips on real full carrier and fails on probe-erased control; separator removal recomputes quotient class count; all scale rungs pass without dense closure",
        "fail_rule": "fail on missing helper proof flip, missing baseline/ablated recompute fields, JAX mismatch, live probe-erased control, dense closure, or downstream consumer promotion",
        "all_pass": all_pass,
        "required_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
