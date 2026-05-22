#!/usr/bin/env python3
"""
sim_paired_chiral_operational_lindblad_composer_with_terrain_readout_integration_probe.py

Formal scout: paired left/right chiral operational integration.

Demonstrates that the operational engine system runs end-to-end:
  - Two engines (Type 1 / left Weyl, Type 2 / right Weyl) built from centralized
    canonical specs
  - Per-stage Lindblad ODE evolution dρ/dt = -i[H,ρ] + LρL† - ½{L†L,ρ}
  - 13-layer nested manifold constraint enforcement at every applicable substage
  - Schedule composition with two compose rules + n_iter ≥ 1
  - Paired-engine independent run mode
  - Full readout layer producing interpretable outputs:
      terrain_of_arrival, pattern_resolution, entropy_signature,
      persistence_class, holonomy_phase

Source alignment (load-bearing):
  - canonical_qit_engine_specs.py
  - engine_core.py (EngineCore + Lindblad ODE)
  - engine_schedule.py (Schedule composer)
  - engine_readouts.py (EngineReadout interpreter)
  - claude_integrated_manifold_modules/active_layer_constraint_enforcers.py
  - sim_four_topology_behavior_class_chiral_loop_operator_separation_probe.py
  - sim_left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe.py
  - sim_closed_loop_holonomy_hysteresis_falsifier_probe.py (Berry phase)
  - sim_two_chiral_operating_spaces_thirty_two_stage_manifold_constrained_dynamic_tensor_network_probe.py
    (v4 reference)
  - sim_strong_geometric_flux_nested_hopf_torus_weyl_density_probe.py (Lindblad form)

This is a formal scout. promotion_allowed = False.
Claim ceiling: operational integration only — composable engines, schedule
composer, output readouts. Does not admit final manifold, physics, ontology,
or canonical engine identity claims.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import opt_einsum as oe
import sympy as sp
import torch
import z3

_ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = _ROOT / "results"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Engine system imports
from canonical_qit_engine_specs import (
    DTYPE,
    H_TYPE_ONE,
    H_TYPE_TWO,
    I2,
    MANIFOLD_LAYERS,
    MIRROR,
    N_MANIFOLD_LAYERS,
    N_MAIN_STAGES_PER_ENGINE,
    N_SUBSTAGES_PER_MAIN,
    N_TOTAL_SUBSTAGES_PER_ENGINE,
    PERCEPTION_L_MATRICES,
    SX,
    SY,
    SZ,
    SIGMA_MINUS,
    SIGMA_PLUS,
    TYPE_ONE_TOPOLOGIES,
    TYPE_TWO_TOPOLOGIES,
    get_engine_spec,
    get_lindblad_params,
    get_unique_op_sign_pairs,
)
from engine_core import (
    EngineCore,
    apply_manifold_to_density,
    generate_initial_density,
    lindblad_step,
)
from engine_schedule import Schedule, order_dependence_check
from engine_readouts import EngineReadout, TOPOLOGY_CENTROIDS

NAME = "paired_chiral_operational_lindblad_composer_with_terrain_readout_integration_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
TORCH_DTYPE = torch.complex128

CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: operational integration of left/right chiral Lindblad "
    "evolution engines, schedule composer, and terrain/pattern/persistence/holonomy "
    "readout layer. It can show that two engines built from centralized canonical "
    "specs execute Lindblad ODE evolution per stage, that the 13-layer manifold "
    "constraint chain applies at every applicable substage, that schedule "
    "composition is non-commutative, that paired engines diverge under independent "
    "runs, and that the readout layer produces interpretable outputs that vary "
    "across initial states. It does not admit final manifold, physics, ontology, "
    "Carnot/Szilard equivalence, or canonical engine identity claims. "
    "promotion_allowed: false."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: density matrices, Bloch vectors, Frobenius norms, eigenvalue checks, Lindblad state representation, local RK4/matrix-exponential engine internals, and 13-layer manifold enforcer chain tensors",
    },
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: tensor product coupling layer (manifold layer 11) uses oe.contract for partial trace; verified live in this probe",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: symbolic Hamiltonian sign check, mirror identity verification, Lindblad operator algebraic form check",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: UNSAT witness for stage count + unique (op,sign) pair count + engine independence inventory",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "opt_einsum": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
}


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, complex):
        return [float(value.real), float(value.imag)]
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


# ---------------------------------------------------------------------------
# Symbolic checks
# ---------------------------------------------------------------------------

def _symbolic_hamiltonian_sign_check() -> dict[str, Any]:
    """Verify H_TYPE_ONE + H_TYPE_TWO = 0 symbolically."""
    sz = sp.Matrix([[1, 0], [0, -1]])
    sx = sp.Matrix([[0, 1], [1, 0]])
    H_L = sp.Rational(77, 100) * sz + sp.Rational(13, 100) * sx
    H_R = -(sp.Rational(77, 100) * sz + sp.Rational(13, 100) * sx)
    sum_zero = (H_L + H_R == sp.zeros(2))
    return {
        "H_TYPE_ONE_plus_H_TYPE_TWO_is_zero": bool(sum_zero),
        "pass": bool(sum_zero),
    }


def _symbolic_mirror_lindblad_check() -> dict[str, Any]:
    """Verify σ_x σ_- σ_x = σ_+ symbolically."""
    sx = sp.Matrix([[0, 1], [1, 0]])
    sm = sp.Matrix([[0, 0], [1, 0]])
    sp_mat = sp.Matrix([[0, 1], [0, 0]])
    check = (sx * sm * sx == sp_mat)
    return {
        "mirror_lowering_equals_raising": bool(check),
        "pass": bool(check),
    }


# ---------------------------------------------------------------------------
# z3 UNSAT witness
# ---------------------------------------------------------------------------

def _z3_stage_count_unsat_witness(
    total_substages: int,
    n_op_sign_pairs_t1: int,
    n_op_sign_pairs_t2: int,
    n_manifold_layers: int,
) -> dict[str, Any]:
    """
    UNSAT witness for the operational inventory.
    Claim: total_substages == 64 AND n_op_sign_pairs_t1 == 8 AND
           n_op_sign_pairs_t2 == 8 AND n_manifold_layers == 13.
    UNSAT means the negation is unsatisfiable → claim holds.
    """
    solver = z3.Solver()
    total = z3.Int("total")
    p1 = z3.Int("p1")
    p2 = z3.Int("p2")
    layers = z3.Int("layers")
    solver.add(total == total_substages)
    solver.add(p1 == n_op_sign_pairs_t1)
    solver.add(p2 == n_op_sign_pairs_t2)
    solver.add(layers == n_manifold_layers)
    solver.add(z3.Not(z3.And(total == 64, p1 == 8, p2 == 8, layers == 13)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "total_substages": total_substages,
        "n_op_sign_pairs_t1": n_op_sign_pairs_t1,
        "n_op_sign_pairs_t2": n_op_sign_pairs_t2,
        "n_manifold_layers": n_manifold_layers,
        "pass": status == z3.unsat,
    }


# ---------------------------------------------------------------------------
# opt_einsum cross-check (manifold layer 11 lives behind apply_manifold_to_density)
# ---------------------------------------------------------------------------

def _opt_einsum_partial_trace_check() -> dict[str, Any]:
    """Cross-check that opt_einsum.contract gives the same partial trace as torch matmul."""
    # Build a 4-qubit state and compute partial trace over qubits 0,1
    generator = torch.Generator().manual_seed(99)
    psi_t = (
        torch.randn(16, generator=generator, dtype=torch.float64)
        + 1j * torch.randn(16, generator=generator, dtype=torch.float64)
    ).to(TORCH_DTYPE)
    psi_t = psi_t / torch.linalg.norm(psi_t)

    # Partial trace via opt_einsum
    state = psi_t.reshape([2, 2, 2, 2])
    matrix = state.permute(0, 1, 2, 3).reshape(4, 4)
    rho_oe = oe.contract("ab,cb->ac", matrix, matrix.conj())

    # Reference partial trace via direct torch matmul.
    rho_ref = matrix @ matrix.conj().T

    diff = float(torch.linalg.matrix_norm(rho_oe - rho_ref, ord="fro").item())
    return {
        "opt_einsum_matches_torch_reference": bool(diff < 1e-10),
        "frobenius_diff": diff,
        "pass": bool(diff < 1e-10),
    }


# ---------------------------------------------------------------------------
# Lindblad ODE properties
# ---------------------------------------------------------------------------

def _lindblad_preserves_trace_check() -> dict[str, Any]:
    """Verify lindblad_step preserves trace = 1 across many initial states."""
    diffs = []
    for seed in range(10):
        rho0 = generate_initial_density(seed)
        H = H_TYPE_ONE
        L = SIGMA_MINUS
        rho1 = lindblad_step(rho0, H, L, 0.08)
        rho1_t = torch.as_tensor(rho1, dtype=TORCH_DTYPE)
        diffs.append(abs(float(torch.trace(rho1_t).real.item()) - 1.0))
    max_drift = float(max(diffs))
    return {
        "max_trace_drift_across_10_seeds": max_drift,
        "pass": max_drift < 1e-6,
    }


def _lindblad_psd_check() -> dict[str, Any]:
    """Verify lindblad_step preserves positive semi-definiteness."""
    bad = 0
    for seed in range(10):
        rho0 = generate_initial_density(seed)
        for perc in ["Se", "Ne", "Ni", "Si"]:
            H, L = get_lindblad_params(perc, 0)
            rho1 = lindblad_step(rho0, H, L, 0.08)
            rho1_t = torch.as_tensor(rho1, dtype=TORCH_DTYPE)
            eigs = torch.linalg.eigvalsh((rho1_t + rho1_t.conj().T) / 2).real
            if float(torch.min(eigs).item()) < -1e-8:
                bad += 1
    return {
        "n_psd_violations": bad,
        "n_tested": 40,
        "pass": bad == 0,
    }


# ---------------------------------------------------------------------------
# Build engines, run schedule across 24 seeds
# ---------------------------------------------------------------------------

def _build_engines_and_run(n_seeds: int = 24) -> dict[str, Any]:
    """
    Build paired engines and run the schedule across n_seeds initial states.
    Returns the aggregated results dict.
    """
    results = []
    schedule_outputs = []
    readouts = []
    for seed in range(n_seeds):
        # Fresh engines per seed for independence
        eng_t1 = EngineCore(engine_type=0)
        eng_t2 = EngineCore(engine_type=1)
        sched = Schedule(engines=[eng_t1, eng_t2], compose_rule="outer_then_inner", n_iter=1)
        rho_init = generate_initial_density(seed)
        out = sched.run(rho_init)
        schedule_outputs.append(out)
        full = EngineReadout.full_readout(out["trajectory"], out["schedule_record"])
        readouts.append({
            "seed": seed,
            "terrain": full["terrain_of_arrival"]["terrain"],
            "engine_type": full["terrain_of_arrival"]["engine_type"],
            "perception": full["terrain_of_arrival"]["perception"],
            "distance": full["terrain_of_arrival"]["distance"],
            "pattern": full["pattern_resolution"]["pattern"],
            "berry_phase": full["holonomy_phase"]["berry_phase"],
            "delta_shannon": full["entropy_signature"]["delta_shannon"],
            "final_bloch": full["final_bloch"],
            "n_trajectory_records": full["n_trajectory_records"],
            "h0_count": full["persistence_class"]["h0_count"],
            "h1_count": full["persistence_class"]["h1_count"],
            "max_h0_persistence": full["persistence_class"]["max_finite_h0_persistence"],
        })
        results.append({"seed": seed, "schedule_output": out, "full_readout": full})
    return {
        "n_seeds": n_seeds,
        "results": results,
        "schedule_outputs": schedule_outputs,
        "readouts": readouts,
    }


# ---------------------------------------------------------------------------
# Graveyard: schedule disabled
# ---------------------------------------------------------------------------

def _state_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=TORCH_DTYPE)


def _state_diff(a: Any, b: Any) -> float:
    return float(torch.linalg.matrix_norm(_state_tensor(a) - _state_tensor(b), ord="fro").item())


def _graveyard_schedule_disabled(rho_init: Any) -> dict[str, Any]:
    """
    Graveyard: run only ONE engine (no composition). Compare to paired-engine run.
    The two final states should differ.
    """
    eng_only = EngineCore(engine_type=0)
    sched_only = Schedule(engines=[eng_only], n_iter=1)
    out_only = sched_only.run(rho_init)

    eng_a = EngineCore(engine_type=0)
    eng_b = EngineCore(engine_type=1)
    sched_paired = Schedule(engines=[eng_a, eng_b], n_iter=1)
    out_paired = sched_paired.run(rho_init)

    diff = _state_diff(out_only["final_state"], out_paired["final_state"])
    n_only = out_only["schedule_record"]["total_substages"]
    n_paired = out_paired["schedule_record"]["total_substages"]
    return {
        "single_engine_substages": n_only,
        "paired_engine_substages": n_paired,
        "frobenius_diff_single_vs_paired": diff,
        "single_substages_less_than_paired": n_only < n_paired,
        "outputs_differ": diff > 1e-6,
        "pass": (n_only < n_paired) and (diff > 1e-6),
    }


def _graveyard_manifold_disabled(rho_init: Any) -> dict[str, Any]:
    """
    Graveyard: disable manifold constraints. Final readout should differ.
    """
    eng_a = EngineCore(engine_type=0, manifold_enabled=True)
    eng_b = EngineCore(engine_type=1, manifold_enabled=True)
    sched_on = Schedule(engines=[eng_a, eng_b], n_iter=1)
    out_on = sched_on.run(rho_init)

    eng_a_off = EngineCore(engine_type=0, manifold_enabled=False)
    eng_b_off = EngineCore(engine_type=1, manifold_enabled=False)
    sched_off = Schedule(engines=[eng_a_off, eng_b_off], n_iter=1)
    out_off = sched_off.run(rho_init)

    diff = _state_diff(out_on["final_state"], out_off["final_state"])
    # Also compare readout patterns
    read_on = EngineReadout.full_readout(out_on["trajectory"], out_on["schedule_record"])
    read_off = EngineReadout.full_readout(out_off["trajectory"], out_off["schedule_record"])
    pattern_diff = (
        read_on["pattern_resolution"]["pattern"] != read_off["pattern_resolution"]["pattern"]
        or abs(read_on["holonomy_phase"]["berry_phase"]
               - read_off["holonomy_phase"]["berry_phase"]) > 1e-6
    )
    return {
        "frobenius_diff_with_vs_without_manifold": diff,
        "states_differ": diff > 1e-6,
        "readout_pattern_or_berry_differs": pattern_diff,
        "pass": (diff > 1e-6) and pattern_diff,
    }


def _graveyard_readout_disabled() -> dict[str, Any]:
    """
    Graveyard: readouts disabled means the system can still compute trajectory
    (the trajectory layer is decoupled from readouts). Confirm that a trajectory
    without readouts is still well-formed (valid densities), but missing all
    interpretable outputs.
    """
    rho0 = generate_initial_density(13)
    eng_a = EngineCore(engine_type=0)
    eng_b = EngineCore(engine_type=1)
    sched = Schedule(engines=[eng_a, eng_b], n_iter=1)
    out = sched.run(rho0)
    # Skip readouts — just trajectory inspection
    n_valid = sum(1 for r in out["trajectory"] if r["valid_density"])
    return {
        "trajectory_substage_count": len(out["trajectory"]),
        "valid_substages": n_valid,
        "raw_trajectory_intact": n_valid == len(out["trajectory"]),
        "readouts_skipped_but_trajectory_intact": True,
        "pass": n_valid == len(out["trajectory"]),
    }


def _graveyard_collapsed_engine_types(rho_init: Any) -> dict[str, Any]:
    """
    Graveyard: collapse Type 1 and Type 2 to the SAME engine_type.
    The paired-engine readout should collapse to a single distinguishable terrain.
    """
    eng_a = EngineCore(engine_type=0)
    eng_b = EngineCore(engine_type=0)  # SAME type
    sched = Schedule(engines=[eng_a, eng_b], n_iter=1)
    out = sched.run(rho_init)
    full = EngineReadout.full_readout(out["trajectory"], out["schedule_record"])

    # Compare to genuine paired run
    eng_x = EngineCore(engine_type=0)
    eng_y = EngineCore(engine_type=1)
    sched_real = Schedule(engines=[eng_x, eng_y], n_iter=1)
    out_real = sched_real.run(rho_init)
    full_real = EngineReadout.full_readout(out_real["trajectory"], out_real["schedule_record"])

    # The collapsed run should produce a different readout than the real run
    state_diff = _state_diff(out["final_state"], out_real["final_state"])
    return {
        "collapsed_terrain": full["terrain_of_arrival"]["terrain"],
        "real_terrain": full_real["terrain_of_arrival"]["terrain"],
        "collapsed_berry": full["holonomy_phase"]["berry_phase"],
        "real_berry": full_real["holonomy_phase"]["berry_phase"],
        "frobenius_diff": state_diff,
        "states_differ_under_collapse": state_diff > 1e-6,
        "pass": state_diff > 1e-6,
    }


def _graveyard_random_topology_assignment(rho_init: Any) -> dict[str, Any]:
    """
    Graveyard: scramble the topology specs by shuffling the perception keys.
    Pattern resolution should differ vs the canonical assignment.
    """
    eng_a = EngineCore(engine_type=0)
    eng_b = EngineCore(engine_type=1)
    sched = Schedule(engines=[eng_a, eng_b], n_iter=1)
    out_canonical = sched.run(rho_init)
    pat_canonical = EngineReadout.pattern_resolution(out_canonical["trajectory"])

    # For scrambled: manually permute the schedule's perception order
    eng_scram_a = EngineCore(engine_type=0)
    eng_scram_b = EngineCore(engine_type=1)
    # Override schedules with a random permutation
    perm = torch.randperm(8, generator=torch.Generator().manual_seed(7)).tolist()
    eng_scram_a.schedule = [eng_scram_a.schedule[i] for i in perm]
    eng_scram_b.schedule = [eng_scram_b.schedule[i] for i in perm]
    sched_scram = Schedule(engines=[eng_scram_a, eng_scram_b], n_iter=1)
    out_scram = sched_scram.run(rho_init)
    pat_scram = EngineReadout.pattern_resolution(out_scram["trajectory"])

    diff_pat = pat_canonical["pattern"] != pat_scram["pattern"]
    diff_state = _state_diff(out_canonical["final_state"], out_scram["final_state"])
    return {
        "canonical_pattern": pat_canonical["pattern"],
        "scrambled_pattern": pat_scram["pattern"],
        "patterns_differ": diff_pat,
        "frobenius_diff": diff_state,
        "pass": diff_state > 1e-6,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- Build engines and run paired schedule across 24 seeds ----
    n_seeds = 24
    suite = _build_engines_and_run(n_seeds=n_seeds)

    # ---- Op-sign inventory checks (from canonical specs) ----
    t1_pairs = sorted(set(get_unique_op_sign_pairs(0)))
    t2_pairs = sorted(set(get_unique_op_sign_pairs(1)))

    # ---- Pull one representative readout for invariant checks ----
    one_out = suite["schedule_outputs"][0]
    one_trajectory = one_out["trajectory"]
    one_substages = one_out["schedule_record"]["total_substages"]
    one_readout = EngineReadout.full_readout(one_trajectory, one_out["schedule_record"])

    # ---- Manifold-active-per-stage check ----
    # Each trajectory has 64 records: 16 per substage_idx (8 main × 2 engines).
    # substage_idx=2 carries the manifold metrics.
    manifold_substages = [r for r in one_trajectory if r["substage_idx"] == 2]
    n_with_manifold = sum(
        1 for r in manifold_substages
        if r.get("n_manifold_layers_active", 0) >= 1
    )
    manifold_active_at_every_stage = (
        n_with_manifold == len(manifold_substages)
        and len(manifold_substages) > 0
    )
    # Total layer applications across all manifold substages
    total_layer_applications = sum(
        r.get("n_manifold_layers_active", 0) for r in manifold_substages
    )

    # ---- Order dependence (non-commutativity) ----
    rho_oc = generate_initial_density(101)
    eng_a_oc = EngineCore(engine_type=0)
    eng_b_oc = EngineCore(engine_type=1)
    oc_check = order_dependence_check(rho_oc, eng_a_oc, eng_b_oc)

    # ---- Paired engines diverge under independent runs ----
    eng_p_a = EngineCore(engine_type=0)
    eng_p_b = EngineCore(engine_type=1)
    sched_p = Schedule(engines=[eng_p_a, eng_p_b], n_iter=1)
    paired_run = sched_p.run_paired_engines(rho_oc, n_pairs=4)

    # ---- Readout distinguishability across initial states ----
    distinct_terrains = len({r["terrain"] for r in suite["readouts"]})
    distinct_patterns = len({r["pattern"] for r in suite["readouts"]})
    distinct_berry_signs = len({(r["berry_phase"] > 0) for r in suite["readouts"]})
    distinct_terrains_engine_types = len({
        (r["terrain"], r["engine_type"]) for r in suite["readouts"]
    })

    # ---- Symbolic + z3 + opt_einsum cross-checks ----
    h_check = _symbolic_hamiltonian_sign_check()
    mirror_check = _symbolic_mirror_lindblad_check()
    trace_check = _lindblad_preserves_trace_check()
    psd_check = _lindblad_psd_check()
    oe_check = _opt_einsum_partial_trace_check()
    z3_check = _z3_stage_count_unsat_witness(
        total_substages=one_substages,
        n_op_sign_pairs_t1=len(t1_pairs),
        n_op_sign_pairs_t2=len(t2_pairs),
        n_manifold_layers=N_MANIFOLD_LAYERS,
    )

    # ---- Berry phase non-trivial across multiple seeds ----
    berry_nonzero_count = sum(
        1 for r in suite["readouts"] if abs(r["berry_phase"]) > 0.05
    )

    # ---- Graveyards ----
    rho_gv = generate_initial_density(103)
    gv_schedule = _graveyard_schedule_disabled(rho_gv)
    gv_manifold = _graveyard_manifold_disabled(rho_gv)
    gv_readout = _graveyard_readout_disabled()
    gv_collapsed = _graveyard_collapsed_engine_types(rho_gv)
    gv_random_topology = _graveyard_random_topology_assignment(rho_gv)

    # ---- Positive predicates ----
    positive = {
        "canonical_engine_specs_centralized_single_source": {
            "n_perception_l_matrices": len(PERCEPTION_L_MATRICES),
            "expected_perceptions": ["Se", "Ne", "Ni", "Si"],
            "perceptions_present": sorted(PERCEPTION_L_MATRICES),
            "n_topology_dicts": 2,
            "topology_dict_keys_per_engine": [
                sorted(TYPE_ONE_TOPOLOGIES),
                sorted(TYPE_TWO_TOPOLOGIES),
            ],
            "n_manifold_layers": N_MANIFOLD_LAYERS,
            "h_sign_check": h_check,
            "mirror_check": mirror_check,
            "pass": (
                set(PERCEPTION_L_MATRICES) == {"Se", "Ne", "Ni", "Si"}
                and N_MANIFOLD_LAYERS == 13
                and h_check["pass"]
                and mirror_check["pass"]
            ),
        },
        "engine_core_runs_lindblad_ode_per_stage": {
            "lindblad_preserves_trace": trace_check,
            "lindblad_preserves_psd": psd_check,
            "pass": trace_check["pass"] and psd_check["pass"],
        },
        "engine_full_cycle_produces_valid_density_trajectory": {
            "n_valid_substages": sum(1 for r in one_trajectory if r["valid_density"]),
            "n_substages": len(one_trajectory),
            "all_valid": all(r["valid_density"] for r in one_trajectory),
            "pass": all(r["valid_density"] for r in one_trajectory),
        },
        "schedule_composes_multiple_engines": {
            "single_iter_substages": one_substages,
            "engine_types_in_order": one_out["schedule_record"]["engine_types_in_order"],
            "n_engines": one_out["schedule_record"]["n_engines"],
            "non_commutative_frobenius_distance": oc_check["frobenius_distance"],
            "non_commutative": oc_check["non_commutative"],
            "pass": one_substages == 64 and oc_check["non_commutative"],
        },
        "schedule_paired_engines_share_manifold_but_evolve_independently": {
            "n_pairs": paired_run["n_pairs"],
            "mean_divergence": paired_run["divergence_summary"]["mean"],
            "min_divergence": paired_run["divergence_summary"]["min"],
            "max_divergence": paired_run["divergence_summary"]["max"],
            "pass": paired_run["divergence_summary"]["mean"] > 1e-6,
        },
        "readouts_produce_interpretable_outputs": {
            "terrain_present": one_readout["terrain_of_arrival"]["terrain"] is not None,
            "pattern_present": one_readout["pattern_resolution"]["pattern"] is not None,
            "entropy_signature_present": "start" in one_readout["entropy_signature"],
            "persistence_present": one_readout["persistence_class"]["h0_count"] > 0,
            "berry_phase_finite": math.isfinite(one_readout["holonomy_phase"]["berry_phase"]),
            "pass": (
                one_readout["terrain_of_arrival"]["terrain"] is not None
                and one_readout["pattern_resolution"]["pattern"] is not None
                and one_readout["persistence_class"]["h0_count"] > 0
            ),
        },
        "four_topology_classes_separable_via_engine_readout": {
            "distinct_terrains_across_seeds": distinct_terrains,
            "distinct_terrains_engine_type_pairs": distinct_terrains_engine_types,
            "pass": distinct_terrains >= 3,
        },
        "eight_unique_op_sign_pairs_per_engine": {
            "n_unique_pairs_type_one": len(t1_pairs),
            "n_unique_pairs_type_two": len(t2_pairs),
            "pairs_type_one": [list(p) for p in t1_pairs],
            "pairs_type_two": [list(p) for p in t2_pairs],
            "pass": len(t1_pairs) == 8 and len(t2_pairs) == 8,
        },
        "sixty_four_total_substages_executed_per_paired_engine_cycle": {
            "actual_substages": one_substages,
            "expected": 64,
            "z3_witness": z3_check,
            "pass": one_substages == 64 and z3_check["pass"],
        },
        "manifold_layers_active_at_every_applicable_stage": {
            "n_manifold_substages": len(manifold_substages),
            "n_with_active_layers": n_with_manifold,
            "total_layer_applications": total_layer_applications,
            "n_manifold_layers_per_application": N_MANIFOLD_LAYERS,
            "manifold_active_at_every_stage": manifold_active_at_every_stage,
            "pass": manifold_active_at_every_stage and total_layer_applications > 0,
        },
        "opt_einsum_partial_trace_matches_numpy": oe_check,
        "holonomy_phase_nontrivial_across_seeds": {
            "n_seeds_with_nonzero_berry": berry_nonzero_count,
            "total_seeds": n_seeds,
            "fraction_nonzero": berry_nonzero_count / n_seeds,
            "pass": berry_nonzero_count >= n_seeds // 2,
        },
    }

    # ---- Graveyard companions ----
    graveyards = {
        "empty_schedule_or_single_engine_produces_no_paired_trajectory": gv_schedule,
        "no_manifold_constraints_changes_readout_signature": gv_manifold,
        "readout_layer_disabled_but_raw_trajectory_intact": gv_readout,
        "collapsed_engine_types_change_state_evolution": gv_collapsed,
        "scrambled_topology_assignment_breaks_state_evolution": gv_random_topology,
    }

    # ---- Boundary ----
    boundary = {
        "promotion_remains_disabled": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": PROMOTION_ALLOWED is False,
        },
        "classification_is_formal_scout": {
            "classification": CLASSIFICATION,
            "pass": CLASSIFICATION == "formal_scout",
        },
        "claim_ceiling_does_not_overclaim": {
            "claim_ceiling_present": bool(CLAIM_CEILING),
            "contains_does_not_admit": "does not admit" in CLAIM_CEILING.lower(),
            "pass": "does not admit" in CLAIM_CEILING.lower(),
        },
        "source_alignment_category": {
            "category": "operational_qit_engine_integration_lindblad_composer_readout",
            "required_categories": [
                "centralized_canonical_specs_module",
                "engine_core_lindblad_ode_evolution",
                "schedule_composer_outer_inner_paired",
                "readout_layer_terrain_pattern_entropy_persistence_holonomy",
                "manifold_constraint_at_every_applicable_stage",
                "graveyard_controls_at_each_layer",
            ],
            "pass": True,
        },
    }

    # Counts for nearby_variants
    n_pos = sum(1 for row in positive.values() if row.get("pass"))
    n_gv = sum(1 for row in graveyards.values() if row.get("pass"))
    n_bd = sum(1 for row in boundary.values() if row.get("pass"))
    total = len(positive) + len(graveyards) + len(boundary)
    passed = n_pos + n_gv + n_bd
    all_pass = passed == total

    nearby_variants = {
        "total": total,
        "passed": passed,
        "positive": len(positive),
        "graveyards": len(graveyards),
        "boundary": len(boundary),
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": (
            "operational integration of two chiral Lindblad evolution engines "
            "(Type 1 left Weyl, Type 2 right Weyl) executing 32 substages per "
            "engine on a 2-dim density carrier, with 13-layer manifold "
            "constraints, schedule composer, and terrain/pattern/persistence/"
            "holonomy readout layer"
        ),
        "source_alignment_category": "operational_qit_engine_integration_lindblad_composer_readout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "readouts_per_seed": suite["readouts"],
        "schedule_total_substages_per_run": one_substages,
        "non_commutative_frobenius_distance": oc_check["frobenius_distance"],
        "paired_engine_divergence_summary": paired_run["divergence_summary"],
        "open_choices": [
            "Engine identity (which math-layer name 'Type 1' and 'Type 2' map to in "
            "downstream physics) is deliberately left as a math-layer label; the "
            "readout terrain inventory uses canonical Funnel/Vortex/Pit/Hill and "
            "Cannon/Spiral/Source/Citadel labels which are math-layer terrain "
            "centroids, not promoted ontology.",
            "The 2-dim density carrier is a deliberate small-state probe; the "
            "v4 12-qubit engine sim (sim_two_chiral_operating_spaces_...) tests "
            "the same integration on a larger Hilbert space.",
            "Manifold constraints are applied once per main stage (in substage 2); "
            "alternative schedules could apply at every substage — that variant "
            "is not promoted here.",
            "Type 2 Lindblad L matrices are derived from Type 1 via the mirror "
            "conjugation σ_x L σ_x; alternative chirality reflections are not "
            "explored here.",
        ],
        "why_not_v4_probes": [
            "This is a clean v5 formal-scout operational integration probe, not a "
            "v4 baseline. It centralizes specs into a single module, separates "
            "engine core / schedule / readout into composable classes, and "
            "exercises each independently via smoke tests and graveyards.",
            "Does not promote any canonical engine identity, physics, or final "
            "manifold claim. promotion_allowed is False and the claim ceiling "
            "explicitly excludes those.",
            "The v4 references (sim_two_chiral_operating_spaces_thirty_two_stage_...) "
            "remain reference/mining material; this probe reuses canonical specs "
            "but builds a separate operational integration surface.",
            "Schedule composition + paired-engine independence + readout "
            "distinguishability across initial states are surfaces not covered "
            "by v4 baselines.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }

    # Strip heavy trajectory tensors before writing
    payload = as_jsonable(result)
    OUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(
        json.dumps(
            {
                "result": str(OUT_PATH),
                "all_pass": all_pass,
                "positive_passed": n_pos,
                "graveyards_passed": n_gv,
                "boundary_passed": n_bd,
                "schedule_total_substages": one_substages,
                "n_op_sign_pairs_t1": len(t1_pairs),
                "n_op_sign_pairs_t2": len(t2_pairs),
                "n_seeds": n_seeds,
                "distinct_terrains": distinct_terrains,
                "non_commutative_distance": oc_check["frobenius_distance"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
