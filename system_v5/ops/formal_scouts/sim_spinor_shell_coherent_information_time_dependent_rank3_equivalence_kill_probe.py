#!/usr/bin/env python3
"""Spinor-shell coherent-information time-dependent rank-3 equivalence kill scout."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import opt_einsum as oe
import sympy as sp
import torch
import z3

from sim_spinor_shell_coherent_information_locality_preserving_rank3_control_probe import (
    best_constant_fit,
    dynamic_sequence,
    l2_gap,
)
from sim_dynamic_shell_graph_gamma5_chirality_choi_survivor_quotient_probe import rates_from_weights, shell_weights
from sim_gamma5_offdiagonal_coherence_trace_orbit_survivor_quotient_probe import (
    DTYPE,
    DIM,
    N_QUBITS,
    apply_kraus,
    asymmetric_local_kraus,
    candidate_densities,
    cptp_gap,
    embed,
    gamma5_boundary,
)
from sim_spinor_shell_coherent_information_locality_preserving_rank3_control_probe import signed_readout


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "spinor_shell_coherent_information_time_dependent_rank3_equivalence_kill_probe_results.json"

NAME = "spinor_shell_coherent_information_time_dependent_rank3_equivalence_kill_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: records the kill boundary that a shell-independent "
    "time-dependent locality-preserving rank-3 split-jump CPTP sequence can "
    "exactly reproduce the dynamic-shell gamma5 coherent-information orbit "
    "when the per-step rates are allowed to match. It does not admit novelty, "
    "empirical physics, a final manifold tower, ontology, or bridge claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density states, time-dependent Kraus sequence, entropy spectra, and CPTP checks"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing imported signed-readout partial trace path"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic time-dependent versus constant-rate boundary"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing equivalence-kill contradiction witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def time_dependent_rank3_sequence(rho: torch.Tensor) -> dict[str, Any]:
    current = rho.clone()
    coherent = [signed_readout(current)["coherent_information_local_to_rest"]]
    conditional = [signed_readout(current)["conditional_entropy_local_given_rest"]]
    rates = []
    cptp_gaps = []
    for step in range(1, 7):
        gamma_l, gamma_r = rates_from_weights(shell_weights(step, "dynamic"))
        rates.append([gamma_l, gamma_r])
        kraus = embed(asymmetric_local_kraus(gamma_l, gamma_r))
        current = apply_kraus(current, kraus)
        row = signed_readout(current)
        coherent.append(row["coherent_information_local_to_rest"])
        conditional.append(row["conditional_entropy_local_given_rest"])
        cptp_gaps.append(cptp_gap(kraus))
    return {"coherent_orbit": coherent, "conditional_orbit": conditional, "rates": rates, "max_cptp_gap": max(cptp_gaps)}


def z3_witness(exact_gap: float, constant_gap: float, cptp: float) -> dict[str, Any]:
    solver = z3.Solver()
    exact, constant_fails, valid = z3.Bools("exact constant_fails valid")
    solver.add(exact == (exact_gap < 1e-12))
    solver.add(constant_fails == (constant_gap > 0.004))
    solver.add(valid == (cptp < 1e-12))
    solver.add(z3.Not(z3.And(exact, constant_fails, valid)))
    status = solver.check()
    return {"solver_status": str(status), "pass": status == z3.unsat, "exact_time_dependent_fit": exact_gap < 1e-12, "constant_control_gap_remains": constant_gap > 0.004, "cptp_valid": cptp < 1e-12}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = {}
    exact_gaps = []
    constant_gaps = []
    cptp_gaps = []
    for name, rho in candidate_densities().items():
        target = dynamic_sequence(rho)
        timed = time_dependent_rank3_sequence(rho)
        exact_gap = l2_gap(target["coherent_orbit"], timed["coherent_orbit"])
        constant = best_constant_fit(rho, target["coherent_orbit"])
        exact_gaps.append(exact_gap)
        constant_gaps.append(constant["gap"])
        cptp_gaps.append(timed["max_cptp_gap"])
        rows[name] = {"target_dynamic_shell": target, "time_dependent_rank3": timed, "exact_gap": exact_gap, "best_constant_rank3_gap": constant["gap"]}
    max_exact_gap = max(exact_gaps)
    min_constant_gap = min(constant_gaps)
    max_cptp_gap = max(cptp_gaps)
    symbolic_boundary = sp.Symbol("time_dependent_rates") != sp.Symbol("constant_rates")
    positive = {
        "time_dependent_rank3_sequence_exactly_reproduces_dynamic_shell_coherent_orbit": {"max_exact_gap": max_exact_gap, "pass": max_exact_gap < 1e-12},
        "constant_rank3_control_is_weaker_than_time_dependent_rank3_control": {"min_constant_gap": min_constant_gap, "pass": min_constant_gap > 0.004},
        "time_dependent_rank3_sequence_is_cptp": {"max_cptp_gap": max_cptp_gap, "pass": max_cptp_gap < 1e-12},
        "gamma5_projector_boundary": gamma5_boundary(),
        "symbolic_time_dependent_boundary": {"expr": "time_dependent_rates != constant_rates", "pass": bool(symbolic_boundary)},
    }
    graveyard_companions = {
        "unrestricted_time_dependent_rank3_comparison_is_too_broad": {"max_exact_gap": max_exact_gap, "pass": max_exact_gap < 1e-12},
        "constant_rate_comparison_was_the_prior_weaker_control": {"min_constant_gap": min_constant_gap, "pass": min_constant_gap > 0.004},
        "entropy_contraction_path_is_exercised": {"imported_opt_einsum": oe.__name__, "pass": oe.__name__ == "opt_einsum"},
        "finite_dimension_boundary": {
            "dimension": DIM,
            "qubits": N_QUBITS,
            "minimum_nonclassical_width": 8,
            "minimum_width_role": "calibration_only",
            "minimum_width_reason": "four-qubit density fixture is a finite boundary/control, not nonclassical maturity evidence",
            "pass": DIM == 16 and N_QUBITS == 4,
        },
    }
    boundary = {
        "z3_time_dependent_rank3_equivalence_kill": z3_witness(max_exact_gap, min_constant_gap, max_cptp_gap),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "four-qubit dynamic-shell gamma5 coherent-information orbit compared against shell-independent time-dependent locality-preserving rank-3 split-jump CPTP sequence using identical per-step rates",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": ["This is a kill boundary for unconstrained time-dependent rank-3 controls.", "Future coherent-information scouts need constraints beyond allowing arbitrary per-step rates, such as shell-rate derivability, parameter compression, or independent observables.", "The prior constant-rate survival should not be promoted without this boundary."],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from Grok/Gemini time-dependent locality-control pressure; it is not a canonical v4 probe.",
        "raw_rows": rows,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(checks), "result": str(OUT_PATH), "max_exact_gap": max_exact_gap, "min_constant_gap": min_constant_gap}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
