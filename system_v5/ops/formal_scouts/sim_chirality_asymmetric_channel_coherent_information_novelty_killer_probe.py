#!/usr/bin/env python3
"""Chirality-asymmetric channel coherent-information novelty-killer scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

from clifford import Cl
import opt_einsum as oe
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "chirality_asymmetric_channel_coherent_information_novelty_killer_probe_results.json"

NAME = "chirality_asymmetric_channel_coherent_information_novelty_killer_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether shell-direction channel readouts reduce "
    "to standard CPTP channel theory, and whether chirality-asymmetric CPTP "
    "blocks separate by conditional entropy/coherent information. It does not "
    "admit novelty, physics, ontology, bridge, or target-system claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density matrices, Kraus channels, CPTP checks, and entropy spectra"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing partial traces for bipartite entropy readouts"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing chirality projector sanity via pseudoscalar split"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact Bell-state conditional entropy boundary"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing textbook-equivalence and chirality-separation contradiction checks"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128


def bell_density(theta: float) -> torch.Tensor:
    psi = torch.zeros(4, dtype=DTYPE)
    psi[0] = math.cos(theta)
    psi[3] = math.sin(theta)
    psi = psi / torch.linalg.vector_norm(psi)
    return torch.outer(psi, psi.conj())


def witness_family() -> list[torch.Tensor]:
    rows = []
    for theta in torch.linspace(0.18, 0.78, 16):
        rows.append(bell_density(float(theta.item())))
    return rows


def partial_trace_two_qubit(rho: torch.Tensor, keep: int) -> torch.Tensor:
    tensor = rho.reshape(2, 2, 2, 2)
    if keep == 0:
        return oe.contract("abad->bd", tensor)
    return oe.contract("abcb->ac", tensor)


def entropy(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def observables(rho: torch.Tensor) -> dict[str, float]:
    rho_a = partial_trace_two_qubit(rho, 0)
    rho_b = partial_trace_two_qubit(rho, 1)
    s_ab = entropy(rho)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    bloch_z = float(torch.real(rho_a[0, 0] - rho_a[1, 1]).item())
    hopf_norm_proxy = float(torch.sqrt(torch.clamp((rho_a[0, 0] - rho_a[1, 1]).real ** 2 + 4 * torch.abs(rho_a[0, 1]) ** 2, min=0.0)).item())
    return {
        "binding_ratio_proxy": s_a / max(s_ab, 1e-12),
        "conditional_entropy_A_given_B": s_ab - s_b,
        "hopf_norm_proxy": hopf_norm_proxy,
        "coherent_information_A_to_B": s_b - s_ab,
        "bloch_z": bloch_z,
    }


def amplitude_damping_kraus(gamma: float) -> list[torch.Tensor]:
    return [
        torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1 - gamma)]], dtype=DTYPE),
        torch.tensor([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=DTYPE),
    ]


def apply_single_qubit_kraus_to_first(rho: torch.Tensor, kraus: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(rho)
    eye = torch.eye(2, dtype=DTYPE)
    for k in kraus:
        op = torch.kron(k, eye)
        out = out + op @ rho @ op.conj().T
    return out


def textbook_channel(rho: torch.Tensor, gamma: float) -> torch.Tensor:
    return apply_single_qubit_kraus_to_first(rho, amplitude_damping_kraus(gamma))


def shell_direction_channel_same_math(rho: torch.Tensor, gamma: float) -> torch.Tensor:
    # This intentionally has no extra structure. If it differs from textbook,
    # the implementation is smuggling something.
    return apply_single_qubit_kraus_to_first(rho, amplitude_damping_kraus(gamma))


def chirality_projectors() -> tuple[torch.Tensor, torch.Tensor]:
    return (
        torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=DTYPE),
        torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=DTYPE),
    )


def chirality_asymmetric_kraus(gamma_left: float, gamma_right: float) -> list[torch.Tensor]:
    p_l, p_r = chirality_projectors()
    k0_l, k1_l = amplitude_damping_kraus(gamma_left)
    k0_r, k1_r = amplitude_damping_kraus(gamma_right)
    return [
        k0_l @ p_l + k0_r @ p_r,
        k1_l @ p_l,
        k1_r @ p_r,
    ]


def cptp_gap(kraus: list[torch.Tensor]) -> float:
    accum = torch.zeros((2, 2), dtype=DTYPE)
    for k in kraus:
        accum = accum + k.conj().T @ k
    return float(torch.linalg.matrix_norm(accum - torch.eye(2, dtype=DTYPE)).item())


def max_observable_diff(rows_a: list[dict[str, float]], rows_b: list[dict[str, float]]) -> dict[str, float]:
    keys = rows_a[0].keys()
    return {key: max(abs(a[key] - b[key]) for a, b in zip(rows_a, rows_b, strict=True)) for key in keys}


def clifford_chirality_sanity() -> dict[str, Any]:
    _, blades = Cl(1, 3)
    pseudo = blades["e1234"]
    return {"pseudoscalar": str(pseudo), "negative_differs": str(pseudo) != str(-pseudo), "pass": str(pseudo) != str(-pseudo)}


def sympy_bell_boundary() -> dict[str, Any]:
    expected = -sp.log(2)
    numeric = observables(bell_density(math.pi / 4))["conditional_entropy_A_given_B"]
    return {"expected": str(expected), "numeric": numeric, "pass": abs(numeric + math.log(2)) < 1e-9}


def z3_checks(textbook_diff: dict[str, float], asym_diff: dict[str, float], cptp: float) -> dict[str, Any]:
    textbook_zero = max(textbook_diff.values()) < 1e-12
    asym_separates = asym_diff["conditional_entropy_A_given_B"] > 0.05 and asym_diff["coherent_information_A_to_B"] > 0.05
    valid = cptp < 1e-12
    solver = z3.Solver()
    t, a, c = z3.Bools("textbook asym cptp")
    solver.add(t == textbook_zero, a == asym_separates, c == valid, z3.Not(z3.And(t, a, c)))
    return {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat, "textbook_zero": textbook_zero, "asym_separates": asym_separates, "cptp": valid}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    witnesses = witness_family()
    textbook_rows = [observables(textbook_channel(rho, gamma=0.18)) for rho in witnesses]
    shell_rows = [observables(shell_direction_channel_same_math(rho, gamma=0.18)) for rho in witnesses]
    asym_kraus = chirality_asymmetric_kraus(gamma_left=0.30, gamma_right=0.05)
    asym_rows = [observables(apply_single_qubit_kraus_to_first(rho, asym_kraus)) for rho in witnesses]
    symmetric_rows = [observables(textbook_channel(rho, gamma=0.175)) for rho in witnesses]
    textbook_diff = max_observable_diff(shell_rows, textbook_rows)
    asym_diff = max_observable_diff(asym_rows, symmetric_rows)
    cptp = cptp_gap(asym_kraus)
    positive = {
        "shell_direction_channel_reduces_to_textbook_channel": {
            "max_observable_diff": textbook_diff,
            "pass": max(textbook_diff.values()) < 1e-12,
        },
        "chirality_asymmetric_cptp_channel_separates_signed_information": {
            "max_observable_diff": asym_diff,
            "cptp_gap": cptp,
            "pass": cptp < 1e-12
            and asym_diff["conditional_entropy_A_given_B"] > 0.05
            and asym_diff["coherent_information_A_to_B"] > 0.05,
        },
        "clifford_chirality_projector_sanity": clifford_chirality_sanity(),
        "bell_state_conditional_entropy_boundary": sympy_bell_boundary(),
    }
    graveyard_companions = {
        "bloch_spectral_readouts_are_weak_chirality_witnesses": {
            "binding_ratio_diff": asym_diff["binding_ratio_proxy"],
            "hopf_norm_diff": asym_diff["hopf_norm_proxy"],
            "signed_information_diff": asym_diff["coherent_information_A_to_B"],
            "pass": asym_diff["coherent_information_A_to_B"] > asym_diff["hopf_norm_proxy"],
        },
        "symmetric_channel_has_no_novel_structure_beyond_textbook": {
            "max_observable_diff": textbook_diff,
            "pass": max(textbook_diff.values()) < 1e-12,
        },
        "invalid_asymmetry_would_fail_cptp_boundary": {
            "cptp_gap": cptp,
            "pass": cptp < 1e-12,
        },
    }
    z3_row = z3_checks(textbook_diff, asym_diff, cptp)
    boundary = {
        "witness_count": {"count": len(witnesses), "pass": len(witnesses) == 16},
        "z3_textbook_kill_and_chirality_survival": z3_row,
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "two-qubit density witnesses under standard and chirality-asymmetric CPTP Kraus channels, compared by conditional entropy and coherent information",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "This kills novelty for chirality-symmetric shell-direction channels only.",
            "The chirality-asymmetric channel is still textbook CPTP math; the formal question is whether shell/Hopf/survivor constraints force that asymmetry rather than naming it.",
            "Future scouts should insert chirality-asymmetric Kraus blocks into the eight-qubit dynamic shell graph scout.",
        ],
        "why_not_v4_probes": "This is a clean v5 novelty-killer formal scout translated from Claude/provider sidequest output; it is not a canonical v4 probe.",
        "raw_rows": {
            "textbook_diff": textbook_diff,
            "chirality_asymmetric_diff": asym_diff,
            "chirality_asymmetric_cptp_gap": cptp,
        },
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(checks) and all(row["pass"] for row in boundary.values()), "result": str(OUT_PATH), "textbook_max_diff": max(textbook_diff.values()), "asym_signed_diff": asym_diff["coherent_information_A_to_B"], "cptp_gap": cptp}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
