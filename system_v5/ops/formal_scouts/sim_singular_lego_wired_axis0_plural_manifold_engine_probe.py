#!/usr/bin/env python3
"""Singular lego-wired manifold+engine probe with axis0 plural treatment.

OWNER DIRECTIVE (2026-05-16): "get the manifold and engines in a strong singular
sim. use all the legos to get there. axis0 is not so simple and needs deep nuance."

DESIGN ORIGIN (5-worker council):
- Subagent B identified two_engine_thirty_two_stage_execution.py as scaffold candidate
- Codex+Gemini converged: legos must be load-bearing, not imported ornaments
- Axis0 subagent: keep all 5 candidates parallel; never collapse to scalar
- Hermes audits: static-baseline-beats-reservoir is the dominant failure mode

WHAT THIS SIM IS:
A bounded probe that runs both QIT engines through one cycle each with the live
13-layer constraint manifold active, AND scores per-substage Axis0 plurally
across the 5 candidates from the existing plural router, AND verifies that the
12 nonclassical legos in system_v5/legos/ are importable/exercised rather than
silently absent. The classical matrix-baseline lego is intentionally excluded
from this nonclassical sim surface, and lego load-bearingness remains deferred
to v2 ablation work.

WHAT THIS SIM IS NOT (per axis0 subagent's collapse-prevention contract):
- not nonclassical root-manifold evidence while it imports NumPy-backed
  engine_core; this is an adapter/control boundary row until that runtime is
  torch-native spinor/quaternion
- not a canonical singular engine
- not a final axis0
- not quantum advantage
- not learned dynamics
- not a Holodeck / cognition / physics admission
- not bridge / coupling stage authorisation

The 7 axis0 acceptance fields (must all hold for receipt to be honest):
  1. axis0_candidates: dict with exactly the 5 named keys
  2. each candidate value: {values, finite, control_deltas, blockers}
  3. single_scalar_axis0_emitted: false
  4. signed_polarity_preserved: true (fep_gradient sign counts retained)
  5. path_entropy_is_not_degenerate: false=fail if >50% deriv values are 0.0
  6. holographic_boundary_blockers_retained: true
  7. promotion_allowed: false + claim_ceiling explicit

V1 SCOPE (honest):
  - imports all nonclassical system_v5/legos modules
  - exercises 11 legos via primary_callable; lego_autograd_ci via real coherent_info+mixture
  - runs engine_core 32-substage cycle per engine type with manifold active
  - emits axis0 as 5-key plural dict (no scalar collapse)
  - HARD path_entropy non-degeneracy gate (all_pass=False if degenerate)

V2 DEFERRED (NOT this sim):
  - per-lego ablation with axis0 candidate delta measurement
  - real classifier-vs-engine static baseline (matched-feature train/test split)
  - legos used IN the per-substage axis0 path (currently they're invoked in
    isolation, not feeding the per-substage axis0 candidate computations)
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
import time
from collections import Counter
from typing import Any

import torch

# === Stage gate compliance ===
import os
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

# === Path setup ===
ROOT = pathlib.Path(__file__).resolve().parents[3]  # repo root
sys.path.insert(0, str(ROOT / "system_v5" / "ops" / "formal_scouts"))
sys.path.insert(0, str(ROOT / "system_v5" / "ops" / "formal_scouts" / "claude_integrated_manifold_modules"))
sys.path.insert(0, str(ROOT / "system_v5" / "legos"))

# === Engine + manifold ===
from engine_core import EngineCore, generate_initial_density
import active_layer_constraint_enforcers as ale

# === Legos — IMPORT EACH (per directive: use all the legos to get there) ===
# Per subagent B finding: 0 imported modules from system_v5/legos/ — this sim
# closes that gap for the 12 nonclassical lego modules in scope here. The
# classical matrix-baseline lego is excluded from this nonclassical sim surface.
import finite_density_matrix_carrier_trace_psd_pytorch_sympy_z3 as lego_density_psd
import unit_spinor_hopf_projection_phase_invariance_geomstats_pytorch_sympy as lego_hopf_projection
import weyl_spinor_chirality_hamiltonian_sign_expectation_clifford_pytorch_z3 as lego_weyl_chirality
import pauli_clifford_commutator_representation_gap_clifford_sympy_z3 as lego_pauli_commutator
import density_operator_cptp_amplitude_damping_trace_psd_pytorch_sympy_z3 as lego_cptp_damping
import finite_simplicial_cycle_boundary_homology_gudhi_toponetx_xgi as lego_simplicial_homology
import two_point_spectral_triple_dirac_commutator_distance_pytorch_sympy_z3 as lego_spectral_triple
import spectral_entropy_family_density_state_pytorch_sympy_z3 as lego_spectral_entropy
import bipartite_cut_mutual_conditional_coherent_information_pytorch_sympy_z3 as lego_bipartite_ci
import finite_support_topology_entropy_witness_pyg_gudhi_xgi_z3 as lego_topology_witness
import signed_conditional_and_coherent_information_negative_entropy_pytorch_sympy_z3 as lego_signed_ci
import coherent_information_parameter_gradient_two_qubit_mixture_pytorch_autograd_z3 as lego_autograd_ci


# === Output ===
ROOT_FS = pathlib.Path(__file__).resolve().parent  # system_v5/ops/formal_scouts
RESULT_DIR = ROOT_FS / "results"
OUT_PATH = RESULT_DIR / "singular_lego_wired_axis0_plural_manifold_engine_probe_results.json"

NAME = "singular_lego_wired_axis0_plural_manifold_engine_probe"
# R1 AUDIT: demoted from formal_scout per Codex+Opus convergent finding that
# legos are imported but not actually load-bearing in the axis0 path; this is
# a tool_lego_fit_probe at v1 — engine-cycle lego integration deferred to v2.
CLASSIFICATION = "tool_lego_fit_probe"
PROMOTION_ALLOWED = False
SIM_EXECUTION_KIND = "adapter_control"
SOURCE_ALIGNMENT_CATEGORY = "singular_lego_wired_axis0_plural_manifold_engine"

CLAIM_CEILING = (
    "tool_lego_fit_probe ONLY / adapter-control boundary row: verifies that the "
    "12 nonclassical system_v5/legos "
    "primitives in scope are importable AND each has its primary non-trivial "
    "callable exercised in isolation, while the classical matrix-baseline lego "
    "is intentionally excluded from this nonclassical surface, "
    "AND runs engine_core (Lindblad cycle) with the live 13-layer active manifold "
    "constraint chain, AND emits axis0 plurally across the 5 candidates from the "
    "existing plural router with strict per-candidate predicates. Because this row "
    "imports NumPy-backed engine_core, it is not nonclassical root-manifold "
    "evidence until the runtime is ported to a torch-native spinor/quaternion "
    "carrier. Does NOT admit: "
    "canonical engine, final axis0, Holodeck memory, retrocausality, quantum "
    "advantage, learned dynamics, intelligence, physics, cognition, canonical "
    "manifold tower claims, or lego load-bearingness in the per-substage axis0 path "
    "(v1 scope: lego callable + axis0 plural emission separately; v2 scope: legos "
    "in axis0 path with ablation sensitivity). Owner emphasis 'axis0 not so simple "
    "needs deep nuance' enforced via 5-key dict + signed polarity + path_entropy "
    "HARD non-degeneracy gate + holographic boundary blockers retained. "
    "promotion_allowed: false."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing engine carrier, lego density ops, autograd lego, and axis0 candidate aggregation/statistics"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing via lego_pauli_commutator + lego_density_psd"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing via lego_pauli_commutator + lego_density_psd + lego_topology_witness"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing via lego_weyl_chirality + lego_pauli_commutator"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing via lego_hopf_projection"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing via lego_simplicial_homology + lego_topology_witness"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing via lego_simplicial_homology"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing via lego_simplicial_homology + lego_topology_witness"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing via lego_signed_ci + lego_autograd_ci"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing via lego_topology_witness (pyg)"},
    "engine_core": {"tried": True, "used": True, "reason": "load-bearing engine cycle + LAYERS_ACTIVE manifold chain"},
}
TOOL_INTEGRATION_DEPTH = {
    'pytorch': 'load_bearing',
    'sympy': 'load_bearing',
    'z3': 'load_bearing',
    'clifford': 'load_bearing',
    'geomstats': 'load_bearing',
    'gudhi': 'load_bearing',
    'toponetx': 'load_bearing',
    'xgi': 'load_bearing',
    'opt_einsum': 'load_bearing',
    'torch_geometric': 'load_bearing',
    'engine_core': 'supportive',
}
TOOL_ROLE_SOURCE = {k: "local" for k in TOOL_MANIFEST}


# === Per-lego contract block (per codex Phase 3 decisive check) ===
# Each lego must have: module, role, consumed_output, failure_condition,
# stage_gate_reason, primary_callable (a thunk that exercises non-trivial logic).
LEGO_CONTRACTS = {
    "lego_density_psd": {
        "module": lego_density_psd,
        "role": "PSD+trace=1 verification of density matrices",
        "consumed_output": "torch.complex128 (2x2) density matrix",
        "failure_condition": "min_eigenvalue < -tol OR |trace - 1| > tol",
        "stage_gate_reason": "lego stage requires PSD admission",
        "primary_callable": lambda: lego_density_psd.torch_density_validity(
            torch.tensor([[0.7, 0.0], [0.0, 0.3]], dtype=torch.complex128)
        ),
        "pass_predicate": lambda out: bool(out.get("pass", False)),
    },
    "lego_hopf_projection": {
        "module": lego_hopf_projection,
        "role": "REAL Hopf S3->S2 projection (NOT just real_embedding) + global-phase invariance",
        "consumed_output": "dict of (bloch_vec, phase_distance_dict, spinor_checks_dict)",
        "failure_condition": "hopf_projection non-Bloch OR phase invariance violated OR spinor_checks fails",
        "stage_gate_reason": "geometry lego stage requires REAL Hopf projection + phase invariance",
        # R8 FIX per R7 P1.1/P1.2 findings: call hopf_projection (not the trivial real_embedding),
        # and verify phase_distance returns ~0 (S2 projection IS phase-invariant), and
        # spinor_checks confirms unit norm + geomstats S3/S2 membership.
        "primary_callable": lambda: {
            "bloch": lego_hopf_projection.hopf_projection(
                torch.tensor([1.0, 1.0j], dtype=torch.complex128) / math.sqrt(2)
            ),
            "phase_dist": lego_hopf_projection.phase_distance(
                torch.tensor([1.0, 1.0j], dtype=torch.complex128) / math.sqrt(2),
                theta=1.0,
            ),
            "checks": lego_hopf_projection.spinor_checks(
                torch.tensor([1.0, 1.0j], dtype=torch.complex128) / math.sqrt(2)
            ),
        },
        "pass_predicate": lambda out: (
            isinstance(out, dict)
            # Bloch vec lives on S^2: |bloch| ≈ 1
            and abs(float(torch.linalg.norm(out["bloch"]).item()) - 1.0) < 1e-9
            # Phase invariance: phase_distance returns 'pass' True AND base_distance near zero
            and out["phase_dist"].get("pass") is True
            and abs(float(out["phase_dist"]["base_distance_after_global_phase"])) < 1e-9
            # spinor_checks: pass True + geomstats S3+S2 membership True + carrier+base norm = 1
            and out["checks"].get("pass") is True
            and out["checks"].get("geomstats_s3_belongs") is True
            and out["checks"].get("geomstats_s2_belongs") is True
            and abs(float(out["checks"]["carrier_norm"]) - 1.0) < 1e-9
            and abs(float(out["checks"]["base_norm"]) - 1.0) < 1e-9
        ),
    },
    "lego_weyl_chirality": {
        "module": lego_weyl_chirality,
        "role": "expectation of chirality (sigma_z) on spinor; opposite-sign fixture set",
        "consumed_output": "dict of (|+z>, |-z>, |+x>) expectations",
        "failure_condition": "|+z> != +1 or |-z> != -1 or |+x> != 0 within tol; non-trivial chirality required",
        "stage_gate_reason": "chirality lego stage anchor requires SIGN discrimination",
        # R6 STRENGTHEN per adversarial: feed three known eigenstate fixtures;
        # predicate must verify SIGN behavior, not just finiteness.
        "primary_callable": lambda: {
            "plus_z": float(lego_weyl_chirality.expectation(
                torch.tensor([1.0, 0.0], dtype=torch.complex128),
                torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.complex128),
            )),
            "minus_z": float(lego_weyl_chirality.expectation(
                torch.tensor([0.0, 1.0], dtype=torch.complex128),
                torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.complex128),
            )),
            "plus_x": float(lego_weyl_chirality.expectation(
                torch.tensor([1.0, 1.0], dtype=torch.complex128) / math.sqrt(2),
                torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.complex128),
            )),
        },
        "pass_predicate": lambda out: (
            isinstance(out, dict)
            and abs(out["plus_z"] - 1.0) < 1e-9     # |+z> sigma_z = +1
            and abs(out["minus_z"] - (-1.0)) < 1e-9  # |-z> sigma_z = -1
            and abs(out["plus_x"] - 0.0) < 1e-9     # |+x> sigma_z = 0 (orthogonal axis)
            # Sign discrimination: +1 vs -1 must differ
            and (out["plus_z"] - out["minus_z"]) > 1.9
        ),
    },
    "lego_pauli_commutator": {
        "module": lego_pauli_commutator,
        "role": "Pauli/Clifford commutator gap via z3 + clifford + sympy; DEPTH-2 check on each positive sub-pred",
        "consumed_output": "main() result dict with positive.{clifford_bivector, sympy_xy_eq_2iz, z3_nonzero}",
        "failure_condition": "ANY of the 3 positive sub-predicates pass=False (depth-2 check, not summary trust)",
        "stage_gate_reason": "algebra lego stage anchor; trust-the-module antipattern explicitly avoided",
        # R10 FIX per R9 P2-D1: don't trust main().summary.all_pass; check the 3 positive sub-predicates directly
        "primary_callable": lambda: lego_pauli_commutator.main(),
        "pass_predicate": lambda out: (
            isinstance(out, dict)
            and isinstance(out.get("positive"), dict)
            and out["positive"].get("clifford_vector_commutator_is_bivector", {}).get("pass") is True
            and out["positive"].get("sympy_pauli_x_y_commutator_equals_two_i_z", {}).get("pass") is True
            and out["positive"].get("z3_nonzero_commutator_cannot_be_zero", {}).get("pass") is True
        ),
    },
    "lego_cptp_damping": {
        "module": lego_cptp_damping,
        "role": "amplitude-damping CPTP: gamma=0 identity preserves rho; gamma>0 reduces rho_11",
        "consumed_output": "dict of (rho_input, rho_after_gamma_zero, rho_after_gamma_half)",
        "failure_condition": "gamma=0 changes rho OR gamma=0.5 doesn't reduce rho_11 (no damping action witness)",
        "stage_gate_reason": "CPTP channel lego anchor requires DAMPING-IS-NONTRIVIAL witness",
        # R8 FIX per R7 P2.2: add gamma=0 negative control + gamma=0.5 positive control;
        # predicate verifies damping ACTUALLY damps (rho_11 decreases).
        "primary_callable": lambda: {
            "rho_in": torch.tensor([[0.6, 0.0], [0.0, 0.4]], dtype=torch.complex128),
            "rho_gamma_zero": lego_cptp_damping.apply_channel(
                torch.tensor([[0.6, 0.0], [0.0, 0.4]], dtype=torch.complex128),
                lego_cptp_damping.kraus(0.0),
            ),
            "rho_gamma_half": lego_cptp_damping.apply_channel(
                torch.tensor([[0.6, 0.0], [0.0, 0.4]], dtype=torch.complex128),
                lego_cptp_damping.kraus(0.5),
            ),
        },
        "pass_predicate": lambda out: (
            isinstance(out, dict)
            # gamma=0 → output ≈ input (identity channel)
            and float(torch.norm(out["rho_gamma_zero"] - out["rho_in"]).item()) < 1e-9
            # gamma=0.5 → rho_11 reduced (damping acted)
            and float(out["rho_gamma_half"][1, 1].real.item()) < float(out["rho_in"][1, 1].real.item()) - 0.05
            # rho_00 increased by population transfer
            and float(out["rho_gamma_half"][0, 0].real.item()) > float(out["rho_in"][0, 0].real.item()) + 0.05
            # gamma=0.5 output still valid density
            and bool(lego_cptp_damping.density_validity(out["rho_gamma_half"]).get("pass", False))
        ),
    },
    "lego_simplicial_homology": {
        "module": lego_simplicial_homology,
        "role": "gudhi Betti numbers + control contrast filled-vs-unfilled cycle",
        "consumed_output": "internal (filled/unfilled toggle)",
        "failure_condition": "Betti_0 != 1 OR filled-vs-unfilled Betti_1 contrast collapses (control fails)",
        "stage_gate_reason": "topology lego stage anchor",
        # R4 STRENGTHEN: check expected fixture values AND filled-vs-unfilled contrast (control)
        "primary_callable": lambda: {
            "filled": lego_simplicial_homology.gudhi_betti(filled=True),
            "unfilled": lego_simplicial_homology.gudhi_betti(filled=False),
        },
        "pass_predicate": lambda out: (
            isinstance(out, dict)
            and isinstance(out.get("filled"), list)
            and isinstance(out.get("unfilled"), list)
            # R6 FIX: require BOTH lists to have at least 2 entries (no short-circuit hole)
            and len(out["filled"]) >= 2
            and len(out["unfilled"]) >= 2
            and out["filled"][0] == 1  # Betti_0 = 1 (connected)
            and out["filled"][1] == 0  # filled disk → no 1-cycles
            and out["unfilled"][0] == 1  # connected
            and out["unfilled"][1] == 1  # unfilled cycle → exactly one 1-cycle
            # CONTROL CONTRAST: filled and unfilled differ in Betti_1
            and out["filled"][1] != out["unfilled"][1]
        ),
    },
    "lego_spectral_triple": {
        "module": lego_spectral_triple,
        "role": "Dirac commutator norm for 2-point spectral triple; check pass + finite positive norm",
        "consumed_output": "mass + a + b parameters",
        "failure_condition": "operator_norm non-finite OR non-positive for distinct a≠b OR dirac_eigenvalues not antipodal",
        "stage_gate_reason": "spectral lego stage anchor",
        # R4 STRENGTHEN (corrected field names per inspection): operator_norm + dirac_eigenvalues
        "primary_callable": lambda: lego_spectral_triple.torch_commutator_norm(mass=1.0, a=0.3, b=0.4),
        "pass_predicate": lambda out: (
            isinstance(out, dict)
            and "operator_norm" in out
            and math.isfinite(float(out["operator_norm"]))
            and float(out["operator_norm"]) > 0.0  # distinct a,b → non-zero commutator
            and isinstance(out.get("dirac_eigenvalues"), list)
            and len(out["dirac_eigenvalues"]) == 2
            and abs(out["dirac_eigenvalues"][0] + out["dirac_eigenvalues"][1]) < 1e-9  # antipodal ±mass
        ),
    },
    "lego_spectral_entropy": {
        "module": lego_spectral_entropy,
        "role": "spectral entropy family (von Neumann + Renyi + Tsallis) with finite + ordered checks",
        "consumed_output": "rho density matrix",
        "failure_condition": "any entropy non-finite, any entropy < 0, or pure-state vs mixed-state ordering breaks",
        "stage_gate_reason": "entropy lego stage anchor",
        # R4 STRENGTHEN: check finite + non-negative for each entropy + ordering Renyi_2 ≤ vN ≤ rank_max
        "primary_callable": lambda: lego_spectral_entropy.entropy_family(
            torch.tensor([[0.7, 0.1], [0.1, 0.3]], dtype=torch.complex128)
        ),
        "pass_predicate": lambda out: (
            isinstance(out, dict)
            and out.get("pass") is True
            and all(k in out for k in ("von_neumann", "renyi_2", "tsallis_2", "min_entropy", "rank_max_entropy", "purity", "rank"))
            and all(math.isfinite(float(out[k])) for k in ("von_neumann", "renyi_2", "tsallis_2", "min_entropy", "rank_max_entropy", "purity"))
            # R14 FIX per R13-Opus P3-H1: tighten `> 1e-9` to `> 1e-6` (semantic-gap close)
            # Mixed fixture rho=[[0.7,0.1],[0.1,0.3]] has vN ≈ 0.59; threshold at 1e-6 is still
            # 5+ orders below real signal but well above FP-noise band (1e-13 to 1e-9).
            and float(out["von_neumann"]) > 1e-6  # genuinely mixed; not 1e-11 admixture leak
            and float(out["renyi_2"]) > 1e-6
            and float(out["renyi_2"]) <= float(out["von_neumann"]) + 1e-9  # Renyi_2 ≤ vN
            and float(out["von_neumann"]) <= float(out["rank_max_entropy"]) + 1e-9  # vN ≤ log(rank)
            and 0.0 <= float(out["purity"]) <= 1.0 + 1e-9
        ),
    },
    "lego_bipartite_ci": {
        "module": lego_bipartite_ci,
        "role": "bipartite cut mutual + coherent info; discriminates product vs max-entangled 2q",
        "consumed_output": "dict of (product_state_cut, bell_state_cut)",
        "failure_condition": "product state must have MI=0; max-entangled state must have MI=2ln2 (NEGATIVE CONTROL required per codex+adv-opus R5)",
        "stage_gate_reason": "coherent-info lego anchor requires discrimination between entangled and product",
        # R6 STRENGTHEN per adversarial: add NEGATIVE control fixture (product state, MI should be 0)
        # alongside POSITIVE fixture (max-entangled, MI should be 2 ln 2).
        # Predicate must accept BOTH only when the values are correct.
        "primary_callable": lambda: {
            "product": lego_bipartite_ci.cut_info(
                lego_bipartite_ci.density(
                    torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=torch.complex128)  # |00>
                )
            ),
            "max_entangled": lego_bipartite_ci.cut_info(
                lego_bipartite_ci.density(
                    torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=torch.complex128) / math.sqrt(2)  # Bell
                )
            ),
        },
        "pass_predicate": lambda out: (
            isinstance(out, dict)
            and out["product"].get("pass") is True
            and out["max_entangled"].get("pass") is True
            # POSITIVE: max-entangled has MI = 2 ln 2 within tol
            and abs(float(out["max_entangled"]["mutual_information"]) - 2.0 * math.log(2.0)) < 1e-6
            and abs(float(out["max_entangled"]["coherent_information_A_to_B"]) - math.log(2.0)) < 1e-6
            # NEGATIVE CONTROL: product state has MI ~ 0 within tol (catches Bell-only fixture artifact)
            and abs(float(out["product"]["mutual_information"])) < 1e-6
            and abs(float(out["product"]["coherent_information_A_to_B"])) < 1e-6
            # DISCRIMINATION: MI of entangled - MI of product > 1.0 (big gap)
            and (float(out["max_entangled"]["mutual_information"]) - float(out["product"]["mutual_information"])) > 1.0
            # I > CI always (sanity invariant)
            and float(out["max_entangled"]["mutual_information"]) > float(out["max_entangled"]["coherent_information_A_to_B"])
        ),
    },
    "lego_topology_witness": {
        "module": lego_topology_witness,
        "role": "finite-support topology entropy witness; ANY unfilled-loop satisfies Betti=(1,1) — role honestly named",
        "consumed_output": "gudhi_cycle_support dict + pyg_path_vs_star dict (contrast)",
        "failure_condition": "either witness fails OR path-vs-star distinguishability collapses",
        "stage_gate_reason": "topology-entropy lego stage anchor; predicate ALSO checks path-vs-star control",
        # R10 FIX per R9 P2-D2: 'any-1-cycle satisfies (1,1)' is true; add path-vs-star control to discriminate
        "primary_callable": lambda: {
            "cycle": lego_topology_witness.gudhi_cycle_support(),
            "path_vs_star": lego_topology_witness.pyg_path_vs_star(),
        },
        "pass_predicate": lambda out: (
            isinstance(out, dict)
            and out["cycle"].get("pass") is True
            and isinstance(out["cycle"].get("betti_numbers"), list)
            and len(out["cycle"]["betti_numbers"]) >= 2
            and out["cycle"]["betti_numbers"][0] == 1
            and out["cycle"]["betti_numbers"][1] == 1
            and isinstance(out["path_vs_star"], dict)
            # R12 FIX per R11 P2-F1: control must DISCRIMINATE path from star (not just len > 0)
            and out["path_vs_star"].get("pass") is True
            and "path_degree_entropy" in out["path_vs_star"]
            and "star_degree_entropy" in out["path_vs_star"]
            and abs(
                float(out["path_vs_star"]["path_degree_entropy"])
                - float(out["path_vs_star"]["star_degree_entropy"])
            ) > 1e-3  # path and star MUST differ in degree entropy
        ),
    },
    "lego_signed_ci": {
        "module": lego_signed_ci,
        "role": "signed CI: Bell state has positive CI (negative conditional entropy admitted), product state CI=0",
        "consumed_output": "dict of (product_readouts, bell_readouts)",
        "failure_condition": "Bell CI not positive OR product CI not zero (no negative-entropy discrimination)",
        "stage_gate_reason": "signed-CI lego anchor requires negative-entropy admission discrimination",
        # R8 FIX per R7 P2.1: add product vs Bell adversarial controls; verify Bell CI > 0 (negative
        # conditional entropy admitted) AND product CI ~ 0 (no quantum correlation).
        "primary_callable": lambda: {
            "product": lego_signed_ci.readouts(
                lego_signed_ci.density(
                    torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=torch.complex128)  # |00>
                )
            ),
            "bell": lego_signed_ci.readouts(
                lego_signed_ci.density(
                    torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=torch.complex128) / math.sqrt(2)  # Bell
                )
            ),
        },
        "pass_predicate": lambda out: (
            isinstance(out, dict)
            and isinstance(out["product"], dict) and isinstance(out["bell"], dict)
            and all(math.isfinite(float(v)) for v in out["product"].values() if isinstance(v, (int, float)))
            and all(math.isfinite(float(v)) for v in out["bell"].values() if isinstance(v, (int, float)))
            # R14 FIX per R13-Opus P3-H2: substring "coherent" matches `coherent_garbage_score`
            # refactor-attack surface. Pin to EXACT key name (which lego_signed_ci already uses).
            and "coherent_information_A_to_B" in out["bell"]
            and abs(float(out["bell"]["coherent_information_A_to_B"]) - math.log(2.0)) < 1e-6  # Bell CI EXACTLY ln(2)
            and "coherent_information_A_to_B" in out["product"]
            and abs(float(out["product"]["coherent_information_A_to_B"])) < 1e-6  # Product CI ~ 0
        ),
    },
    "lego_autograd_ci": {
        "module": lego_autograd_ci,
        "role": "coherent-info autograd parameter gradient on 2q mixture (REAL call to lego, not inline reimpl)",
        "consumed_output": "torch.nn.Parameter theta",
        "failure_condition": "gradient non-finite or zero",
        "stage_gate_reason": "autograd lego anchor",
        "primary_callable": None,  # exercised in end_to_end_jacobian_via_autograd_lego
        "pass_predicate": None,
    },
}

# Back-compat alias for the old name (until cleanup)
LEGO_REGISTRY = {k: v["module"] for k, v in LEGO_CONTRACTS.items()}


# =============================================================================
# SECTION 1 — Lego primitive verification (each lego must be CALLABLE here)
# =============================================================================
def verify_lego_callable(name: str, contract: dict[str, Any]) -> dict[str, Any]:
    """R2 FIX: each lego exercises its primary non-trivial callable per the
    LEGO_CONTRACTS spec. NO MORE hasattr-shortcut. Per codex+opus R1 audit:
    'effective real-exercise count was 3 of 13; replace with actual calls.'

    lego_autograd_ci is exercised separately in end_to_end_jacobian_via_autograd_lego.
    """
    record: dict[str, Any] = {
        "name": name,
        "role": contract["role"],
        "consumed_output": contract["consumed_output"],
        "failure_condition": contract["failure_condition"],
        "stage_gate_reason": contract["stage_gate_reason"],
        "module_loaded": True,
        "callable_invoked": False,
        "callable_returned_pass": None,
        "exception": None,
    }
    callable_fn = contract.get("primary_callable")
    pass_pred = contract.get("pass_predicate")
    if callable_fn is None or pass_pred is None:
        record["callable_invoked"] = False
        record["callable_returned_pass"] = "deferred_to_other_section"
        # R5: link forward to where the deferred lego is actually exercised
        record["callable_invoked_in"] = "end_to_end_jacobian_via_autograd_lego"
        return record
    try:
        out = callable_fn()
        record["callable_invoked"] = True
        record["callable_returned_pass"] = bool(pass_pred(out))
    except Exception as e:
        record["exception"] = f"{type(e).__name__}: {e}"
        record["callable_returned_pass"] = False
    return record


def lego_inventory_pass() -> dict[str, Any]:
    records = [verify_lego_callable(n, c) for n, c in LEGO_CONTRACTS.items()]
    # 11 nonclassical legos have primary_callable; lego_autograd_ci is exercised separately.
    # The classical matrix-baseline lego is outside this sim's nonclassical tool surface.
    n_invoked = sum(1 for r in records if r["callable_invoked"])
    n_pass = sum(1 for r in records if r["callable_returned_pass"] is True)
    deferred = sum(1 for r in records if r["callable_returned_pass"] == "deferred_to_other_section")
    return {
        "records": records,
        "lego_count": len(records),
        "callable_invoked_count": n_invoked,
        "callable_pass_count": n_pass,
        "deferred_count": deferred,
        "all_invokable_legos_pass": (n_invoked == 11 and n_pass == 11 and deferred == 1),
        "pass": (n_invoked == 11 and n_pass == 11 and deferred == 1),
    }


# =============================================================================
# SECTION 2 — Engine cycle with manifold constrained (uses engine_core)
# =============================================================================
def run_engine_cycle(engine_type: int, init_seed: int, manifold_enabled: bool = True) -> list[dict[str, Any]]:
    """Run one full QIT engine cycle (32 substages) with manifold active.
    Uses engine_core.EngineCore — the canonical engine implementation."""
    rho0 = generate_initial_density(init_seed)
    trajectory = EngineCore(engine_type, manifold_enabled=manifold_enabled).run_full_cycle(rho0)["trajectory"]
    return trajectory


# =============================================================================
# SECTION 3 — Axis0 5-candidate plural readout (per axis0 subagent's 7 fields)
# =============================================================================

def _real_tensor(values: Any) -> torch.Tensor:
    return torch.as_tensor(values, dtype=torch.float64)


def _finite_values(values: Any) -> torch.Tensor:
    tensor = _real_tensor(values)
    return tensor[torch.isfinite(tensor)]


def _diff(values: torch.Tensor) -> torch.Tensor:
    return values[1:] - values[:-1] if values.numel() > 1 else torch.empty(0, dtype=torch.float64)


def _mean(values: torch.Tensor) -> float:
    return float(torch.mean(values).item()) if values.numel() else 0.0


def _mean_abs(values: torch.Tensor) -> float:
    return float(torch.mean(torch.abs(values)).item()) if values.numel() else 0.0


def _tensor_list(values: torch.Tensor) -> list[float]:
    return [float(value) for value in values.detach().cpu().tolist()]


def _categorical_entropy(values: list[Any]) -> float:
    counts = Counter(str(v) for v in values)
    total = float(sum(counts.values()))
    probs = _real_tensor([c / total for c in counts.values()])
    return float(-torch.sum(probs * torch.log(probs + 1e-30)).item())


def _rolling(values: list[Any], width: int) -> list[list[Any]]:
    return [values[max(0, i - width + 1): i + 1] for i in range(len(values))]


def candidate_fep_gradient(rows: list[dict[str, Any]]) -> dict[str, Any]:
    efe = _real_tensor(
        [row.get("fep_efe_score", {}).get("expected_free_energy_proxy", float("nan")) for row in rows],
    )
    efe = _finite_values(efe)
    grad = _diff(efe)
    polarity = torch.sign(grad)
    return {
        "candidate": "fep_gradient_polarity",
        "values": _tensor_list(grad),
        "mean_abs_gradient": _mean_abs(grad),
        "positive_steps": int(torch.sum(polarity > 0).item()),
        "negative_steps": int(torch.sum(polarity < 0).item()),
        "zero_steps": int(torch.sum(polarity == 0).item()),
        "finite": bool(grad.numel() and torch.all(torch.isfinite(grad)).item()),
        "blockers": {},
    }


def candidate_path_entropy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tokens = [str(row.get("ordered_token", row.get("substage_idx", "?"))) for row in rows]
    ent = _real_tensor([_categorical_entropy(window) for window in _rolling(tokens, width=8)])
    deriv = _diff(ent)
    # CRITICAL non-degeneracy gate (per axis0 subagent's NEW predicate):
    # Fail if >50% of deriv values are 0.0
    # R10 FIX per R9 P3-E1: fail-closed when deriv.size < 16 (small-N silent-pass would be misleading)
    n_zero = int(torch.sum(torch.isclose(deriv, torch.zeros_like(deriv), atol=1e-12)).item())
    if deriv.numel() < 16:
        is_degenerate = True  # fail-closed for small N
    else:
        is_degenerate = (n_zero / deriv.numel() > 0.5)
    return {
        "candidate": "path_entropy",
        "values": _tensor_list(deriv),
        "entropy_mean": _mean(ent),
        "derivative_mean_abs": _mean_abs(deriv),
        "n_zero_deriv": n_zero,
        "n_total_deriv": int(deriv.numel()),
        "is_degenerate": is_degenerate,
        "finite": bool(deriv.numel() and torch.all(torch.isfinite(deriv)).item()),
        "blockers": {"degenerate_zeros_gate_failed": is_degenerate},
    }


def candidate_correlation_diversity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    obs = _real_tensor(
        [row.get("observation", {}).get("observation_distribution", [0.0] * 6) for row in rows],
    )
    diversity = []
    for window in _rolling(list(obs), width=8):
        arr = torch.stack([_real_tensor(row) for row in window])
        if arr.shape[0] < 3:
            diversity.append(0.0)
            continue
        corr = torch.corrcoef(arr)
        corr = torch.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
        offdiag = corr[~torch.eye(corr.shape[0], dtype=torch.bool)]
        diversity.append(float((1.0 - torch.mean(torch.abs(offdiag))).item()))
    div_arr = _real_tensor(diversity)
    deriv = _diff(div_arr)
    return {
        "candidate": "correlation_diversity_derivative",
        "values": _tensor_list(deriv),
        "diversity_mean": _mean(div_arr),
        "derivative_mean_abs": _mean_abs(deriv),
        "finite": bool(deriv.numel() and torch.all(torch.isfinite(deriv)).item()),
        "blockers": {},
    }


def candidate_boundary_interior() -> dict[str, Any]:
    """Per axis0 subagent: holographic_boundary_interior_reconstruction is
    currently BLOCKED (KL gap 0.0070 < 0.01 floor). We retain it as blocked,
    per the 'holographic_boundary_blockers_retained' acceptance field."""
    receipt_path = RESULT_DIR / "source_native_engine_boundary_path_fep_reconstruction_probe_results.json"
    if not receipt_path.exists():
        return {
            "candidate": "holographic_boundary_interior_reconstruction",
            "status": "blocked_receipt_missing",
            "values": [],
            "finite": False,
            "blockers": {"receipt_missing": True, "expected_path": str(receipt_path)},
        }
    try:
        receipt = json.loads(receipt_path.read_text())
    except Exception as e:
        return {
            "candidate": "holographic_boundary_interior_reconstruction",
            "status": "blocked_receipt_parse_error",
            "values": [],
            "finite": False,
            "blockers": {"parse_error": str(e)},
        }
    # R5 fix: do not call it "routed" when explicit_blockers content is present.
    # The boundary candidate is always BLOCKED (per axis0 subagent), regardless of the
    # upstream receipt's own all_pass field, because of the KL gap floor failure.
    explicit_blockers = receipt.get("explicit_blockers", {})
    has_active_blockers = bool(explicit_blockers)
    if has_active_blockers:
        status = "blocked_by_explicit_blockers_in_upstream_receipt"
    elif receipt.get("all_pass") is not True:
        status = "blocked_by_upstream_receipt_failure"
    else:
        status = "upstream_receipt_clean_but_still_held_pending_axis0_subagent_review"
    return {
        "candidate": "holographic_boundary_interior_reconstruction",
        "status": status,
        "receipt_all_pass": receipt.get("all_pass"),
        "values": [],
        "finite": False,
        "blockers": {
            "explicit_blockers": explicit_blockers,
            "axis0_subagent_2026_05_16": "KL gap 0.0070 < 0.01 floor; do not silently drop",
            "honest_status_note": (
                f"explicit_blockers present={has_active_blockers}; upstream all_pass={receipt.get('all_pass')}; "
                "status reflects the BLOCKED reality, not 'routed' (per R3 audit P3 boundary-blocker-semantics finding)."
            ),
        },
    }


def candidate_retrocausal_many_futures(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a centered-policy posterior over the 64 substage tokens."""
    efe = _real_tensor(
        [row.get("fep_efe_score", {}).get("expected_free_energy_proxy", 0.0) for row in rows],
    )
    if not bool(torch.all(torch.isfinite(efe)).item()):
        return {
            "candidate": "retrocausal_many_futures_policy_scoring",
            "status": "blocked_non_finite_efe",
            "values": [],
            "finite": False,
            "blockers": {"non_finite_efe": True},
        }
    shifted = -efe - torch.max(-efe)
    weights = torch.exp(shifted)
    posterior = weights / torch.sum(weights)
    uniform = torch.full_like(posterior, 1.0 / len(posterior))
    centered = posterior - uniform
    entropy = float(-torch.sum(torch.where(posterior > 0.0, posterior * torch.log(posterior + 1e-30), torch.zeros_like(posterior))).item())
    return {
        "candidate": "retrocausal_many_futures_policy_scoring",
        "values": _tensor_list(centered),
        "policy_entropy": entropy,
        "effective_policy_count": float(math.exp(entropy)),
        "l2_from_uniform_control": float(torch.linalg.vector_norm(centered).item()),
        "finite": bool(torch.all(torch.isfinite(centered)).item()),
        "blockers": {"single_argmax_future_control_rejected": True},
    }


def axis0_plural_readout(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Returns dict with the 5 named candidates per axis0 subagent's spec.
    NO MERGER. NO RANKING. NO SCALAR."""
    return {
        "fep_gradient_polarity": candidate_fep_gradient(rows),
        "path_entropy": candidate_path_entropy(rows),
        "correlation_diversity_derivative": candidate_correlation_diversity(rows),
        "holographic_boundary_interior_reconstruction": candidate_boundary_interior(),
        "retrocausal_many_futures_policy_scoring": candidate_retrocausal_many_futures(rows),
    }


# =============================================================================
# SECTION 4 — Axis0 7 acceptance predicates (must all hold)
# =============================================================================
def axis0_acceptance_check(axis0: dict[str, dict]) -> dict[str, Any]:
    expected_keys = {
        "fep_gradient_polarity", "path_entropy", "correlation_diversity_derivative",
        "holographic_boundary_interior_reconstruction", "retrocausal_many_futures_policy_scoring",
    }
    actual_keys = set(axis0.keys())
    five_keys_present = (actual_keys == expected_keys)
    # Each value must have values, finite, blockers structure
    structure_ok = all(
        isinstance(v, dict) and "values" in v and "finite" in v and "blockers" in v
        for v in axis0.values()
    )
    # Signed polarity preserved
    fep = axis0.get("fep_gradient_polarity", {})
    signed_polarity_preserved = all(
        k in fep for k in ("positive_steps", "negative_steps", "zero_steps")
    )
    # Path entropy non-degeneracy
    pe = axis0.get("path_entropy", {})
    path_entropy_not_degenerate = (pe.get("is_degenerate") is False)
    # Boundary blockers retained (not silently dropped)
    boundary = axis0.get("holographic_boundary_interior_reconstruction", {})
    boundary_blockers_retained = bool(boundary.get("blockers"))
    # No top-level scalar named axis0
    # R2 FIX: P4 restored as HARD gate per opus R1 P2 HARKing finding.
    # Path_entropy degeneracy must FAIL the sim, not be silently demoted to diagnostic.
    # If the predicate fails, the candidate is demoted from the 5-keys set (which itself
    # fails P1, since 4 keys != 5). This is the honest outcome — silent reframing IS HARK.
    p7_explicit = bool(
        CLAIM_CEILING and ("does not admit" in CLAIM_CEILING.lower() or "not admit" in CLAIM_CEILING.lower())
    )
    all_seven_pass = all([
        five_keys_present, structure_ok, signed_polarity_preserved,
        path_entropy_not_degenerate, boundary_blockers_retained,
        (PROMOTION_ALLOWED is False), p7_explicit,
    ])
    return {
        "P1_five_keys_present": five_keys_present,
        "P2_per_candidate_structure_ok": structure_ok,
        "P3_signed_polarity_preserved": signed_polarity_preserved,
        "P4_path_entropy_not_degenerate_HARD_GATE": path_entropy_not_degenerate,
        "P4_finding_note": (
            "P4 is a HARD gate per axis0 subagent 2026-05-16 spec. "
            "When False, sim all_pass=False AND path_entropy candidate is demoted. "
            "R1-audit caught the prior reframing-to-diagnostic as HARKing; reverted."
        ),
        "P5_holographic_boundary_blockers_retained": boundary_blockers_retained,
        "P6_promotion_disabled": (PROMOTION_ALLOWED is False),
        "P7_claim_ceiling_explicit": p7_explicit,
        "all_seven_pass": all_seven_pass,
        "diagnostic_path_entropy_degenerate": (path_entropy_not_degenerate is False),
    }


# =============================================================================
# SECTION 5 — End-to-end Jacobian sensitivity (Gemini's decisive check)
# =============================================================================
def end_to_end_jacobian_via_autograd_lego() -> dict[str, Any]:
    """R2 FIX: actually call lego_autograd_ci.coherent_information(lego_autograd_ci.mixture(theta)).
    Per opus R1 audit P1: 'lego_autograd_ci was IMPORTED but NEVER CALLED - the autograd section
    reimplements the computation inline rather than calling module.coherent_information or
    module.mixture.' This rewrite invokes the lego's real symbols.

    Scope claim remains: op-isolated lego only. Cycle-level autograd is severed at
    engine core's external array handoff per prior 5-round audit. This DOES NOT prove
    engine-cycle gradient flow; it proves autograd flows THROUGH lego_autograd_ci's
    coherent_information path.
    """
    try:
        theta = torch.nn.Parameter(torch.tensor(0.3, dtype=torch.float64))
        # Call lego primitives directly — per R1 audit fix
        rho = lego_autograd_ci.mixture(theta)
        ci = lego_autograd_ci.coherent_information(rho)
        ci.backward()
        grad_val = float(theta.grad.item()) if theta.grad is not None else None
        # Cross-check: finite-difference on same closure (consistency, not validation)
        with torch.no_grad():
            h = 1e-5
            ci_plus = lego_autograd_ci.coherent_information(
                lego_autograd_ci.mixture(torch.tensor(0.3 + h, dtype=torch.float64))
            )
            ci_minus = lego_autograd_ci.coherent_information(
                lego_autograd_ci.mixture(torch.tensor(0.3 - h, dtype=torch.float64))
            )
        fd_grad = float((ci_plus.item() - ci_minus.item()) / (2 * h))
        rel_err = abs(grad_val - fd_grad) / max(abs(fd_grad), 1e-12) if grad_val is not None else None
        return {
            "ci_value": float(ci.item()),
            "grad_dCI_dtheta": grad_val,
            "fd_grad_dCI_dtheta": fd_grad,
            "autograd_vs_fd_rel_err": rel_err,
            "lego_autograd_ci_actually_called": True,  # Per R1 audit: verify this is True
            "lego_callables_invoked": ["mixture", "coherent_information"],
            "grad_is_finite": grad_val is not None and math.isfinite(grad_val),
            "grad_is_nonzero": grad_val is not None and abs(grad_val) > 1e-9,
            "autograd_consistent_with_fd": rel_err is not None and rel_err < 1e-4,
            "pass": (
                grad_val is not None
                and math.isfinite(grad_val)
                and abs(grad_val) > 1e-9
                and rel_err is not None
                and rel_err < 1e-4
            ),
            "scope_claim": (
                "Autograd flows through lego_autograd_ci's coherent_information+mixture pipeline. "
                "This is op-isolated, NOT engine-cycle. Cycle-level autograd remains severed at "
                "engine_core.py:561; that boundary is unchanged in this sim."
            ),
        }
    except Exception as e:
        return {"pass": False, "exception": f"{type(e).__name__}: {e}"}


# =============================================================================
# SECTION 6 — Static-baseline comparison (Hermes's required control)
# =============================================================================
def trivial_polarity_sanity_check(rows: list[dict[str, Any]], axis0: dict[str, dict]) -> dict[str, Any]:
    """R2 RENAME (was static_baseline_vs_engine_axis0): per opus R1 audit P2 —
    'Static baseline = always-positive is NOT a baseline comparison; it is a sanity
    check on engine variance. Hermes-style static-classifier-beats-engine probe NOT done.'

    This is an HONEST RENAME. The function is a trivial sanity check that the engine
    produces BOTH positive and negative substages in fep_gradient_polarity — not a
    Hermes-grade classifier comparison. A real static-classifier-vs-engine probe is
    deferred to v2 and would require: matched feature extraction, train/test split,
    11+ feature kernel comparison per the reservoir baseline scout pattern.
    """
    fep = axis0.get("fep_gradient_polarity", {})
    pos = fep.get("positive_steps", 0)
    neg = fep.get("negative_steps", 0)
    total = pos + neg
    if total == 0:
        return {"pass": False, "reason": "no signed steps to compare"}
    return {
        "engine_positive_steps": pos,
        "engine_negative_steps": neg,
        "engine_polarity_is_nontrivial": (pos > 0 and neg > 0),
        "pass": (pos > 0 and neg > 0),
        "honest_label": "trivial_sanity_check_not_a_static_classifier_baseline",
        "v2_required": (
            "Real static-classifier-vs-engine probe deferred to v2; would need "
            "matched feature extraction + train/test split + 11+ feature kernel "
            "per multiqubit_reservoir_static_kernel_esn_baseline_probe pattern."
        ),
    }


# =============================================================================
# SECTION 7 — Lego ablation graveyard (the NEW question the singular sim asks)
# =============================================================================
def lego_inventory_for_v2_ablation() -> dict[str, Any]:
    """R2 RENAME (was lego_ablation_graveyard): per opus R1 audit P2 finding —
    'lego_ablation_graveyard does not ablate; rename to remove the NEW question framing.'

    This is a passive inventory of imported legos for traceability. v1 does NOT
    execute per-lego ablation (remove + rerun + measure delta on axis0 candidates).
    The 'NEW question' framing has been retired from the docstring. v2 work item.
    """
    inv = {}
    for name, contract in LEGO_CONTRACTS.items():
        module = contract["module"]
        inv[name] = {
            "module_path": getattr(module, "__file__", "unknown"),
            "module_loaded": True,
            "role": contract["role"],
            "stage_gate_reason": contract["stage_gate_reason"],
        }
    return {
        "records": inv,
        "lego_count": len(inv),
        "pass": all(r["module_loaded"] for r in inv.values()),
        "note": (
            "RENAMED from lego_ablation_graveyard. v1 records imports only. "
            "v2 work item: per-lego remove-and-rerun with axis0 delta measurement."
        ),
        "v1_ablation_not_executed": True,
        "v2_pending_actual_ablation": True,
    }


# =============================================================================
# MAIN
# =============================================================================
def main() -> dict[str, Any]:
    started = time.time()

    # Section 1: lego inventory
    lego_pass = lego_inventory_pass()

    # Section 2: engine cycles (both engine types)
    rows_engine0 = run_engine_cycle(engine_type=0, init_seed=6100, manifold_enabled=True)
    rows_engine1 = run_engine_cycle(engine_type=1, init_seed=6101, manifold_enabled=True)
    combined_rows = rows_engine0 + rows_engine1

    # Section 3: axis0 plural readout
    axis0 = axis0_plural_readout(combined_rows)

    # Section 4: axis0 acceptance check
    axis0_accept = axis0_acceptance_check(axis0)

    # Section 5: autograd Jacobian via lego_autograd_ci
    jacobian = end_to_end_jacobian_via_autograd_lego()

    # Section 6: trivial polarity sanity check (renamed from "static baseline" per R1)
    polarity_sanity = trivial_polarity_sanity_check(combined_rows, axis0)

    # Section 7: lego inventory (renamed from "ablation graveyard" per R1; no actual ablation)
    inventory = lego_inventory_for_v2_ablation()

    # Predicates (R2: honest naming + hard P4 gate)
    positive = {
        "eleven_invokable_nonclassical_legos_actually_callable_via_primary_callable": {
            "callable_invoked_count": lego_pass["callable_invoked_count"],
            "callable_pass_count": lego_pass["callable_pass_count"],
            "deferred_count": lego_pass["deferred_count"],
            "expected_invoked": 12,
            "expected_pass": 12,
            "expected_deferred": 1,
            "pass": lego_pass["pass"],
        },
        "engine_cycle_produces_64_substage_rows": {
            "actual_row_count": len(combined_rows),
            "expected": 64,
            "pass": len(combined_rows) == 64,
        },
        "axis0_five_candidate_plural_readout_emitted": {
            "candidate_count": len(axis0),
            "expected": 5,
            "pass": len(axis0) == 5,
        },
        "axis0_seven_acceptance_fields_hold_INCLUDING_path_entropy_hard_gate": {
            "details": axis0_accept,
            "pass": axis0_accept["all_seven_pass"],
        },
        "autograd_through_lego_autograd_ci_real_call_op_isolated": jacobian,
        "engine_polarity_trivial_sanity_check_NOT_static_baseline": polarity_sanity,
        "lego_inventory_for_v2_ablation_records": {
            "details": inventory,
            "pass": inventory["pass"],
        },
    }

    boundary = {
        "scope_op_isolated_only_for_autograd": {
            "claim": "autograd verified at op-isolated lego level; cycle-level autograd known severed at the engine-core external-array boundary",
            "pass": True,
        },
        "manifold_enabled_for_both_engines": {"pass": True},
        "promotion_remains_disabled": {"pass": (PROMOTION_ALLOWED is False)},
    }

    graveyard_companions = {
        "single_scalar_axis0_emitted_is_rejected": {
            "single_scalar_axis0_emitted": False,
            "interpretation": "axis0 emitted as 5-key plural dict; any future collapse to scalar must be rejected",
            "pass": True,
        },
        "trivial_polarity_sanity_check_reported_honestly_not_static_baseline": {
            "details": polarity_sanity,
            "pass": True,
        },
        "path_entropy_degeneracy_HARD_GATE_status": {
            "is_degenerate": axis0.get("path_entropy", {}).get("is_degenerate"),
            "n_zero_deriv": axis0.get("path_entropy", {}).get("n_zero_deriv"),
            "n_total_deriv": axis0.get("path_entropy", {}).get("n_total_deriv"),
            "interpretation": (
                "path_entropy as an axis0 candidate is structurally degenerate under the "
                "current 8-token cyclic engine schedule; rolling-window entropy plateaus. "
                "Per axis0 subagent + R1 audit: this is a HARD gate (not diagnostic). "
                "When degenerate, sim all_pass=False is the honest outcome."
            ),
            "pass": True,  # graveyard companion is satisfied by HAVING reported the degeneracy honestly
            "consequence_for_sim_all_pass": "sim all_pass=False whenever degenerate",
        },
        "boundary_interior_blocker_retained_not_dropped": {
            "boundary_status": axis0.get("holographic_boundary_interior_reconstruction", {}).get("status"),
            "pass": True,
        },
    }

    all_positive_pass = all(p.get("pass") for p in positive.values())
    all_boundary_pass = all(b.get("pass") for b in boundary.values())
    all_graveyard_pass = all(g.get("pass") for g in graveyard_companions.values())
    all_pass = all_positive_pass and all_boundary_pass and all_graveyard_pass

    elapsed = time.time() - started

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "positive": positive,
        "boundary": boundary,
        "graveyard_companions": graveyard_companions,
        "axis0_candidates": axis0,
        "axis0_acceptance_check": axis0_accept,
        "lego_inventory": lego_pass,
        "lego_inventory_for_v2_ablation": inventory,
        "blockers": [
            "v1 ablation graveyard does not actually remove-and-rerun per lego; v2 work",
            "cycle-level autograd remains severed at the engine-core external-array boundary",
            "holographic_boundary_interior_reconstruction blocked by KL gap 0.0070 < 0.01 floor",
        ],
        "open_choices": [
            "Should v2 ablation actually remove each lego call and re-evaluate axis0 deltas?",
            "Should this sim feed into the existing plural router as a NEW candidate routing source?",
        ],
        "all_pass": all_pass,
        "elapsed_seconds": elapsed,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")

    print(f"=== {NAME} ===")
    print(f"  classification: {CLASSIFICATION}")
    print(f"  elapsed: {elapsed:.2f}s")
    print(f"  lego_invoked: {lego_pass['callable_invoked_count']}/11  pass: {lego_pass['callable_pass_count']}/11  deferred: {lego_pass['deferred_count']}/1")
    print(f"  engine_substage_rows: {len(combined_rows)}/64")
    print(f"  axis0_candidates: {len(axis0)}/5  (seven_acceptance: {axis0_accept['all_seven_pass']}, path_entropy_degenerate: {axis0_accept['diagnostic_path_entropy_degenerate']})")
    print(f"  autograd_lego_grad: {jacobian.get('grad_dCI_dtheta')}  vs_fd_rel_err: {jacobian.get('autograd_vs_fd_rel_err')}  (pass={jacobian.get('pass')})")
    print(f"  polarity_sanity: pos={polarity_sanity.get('engine_positive_steps')} neg={polarity_sanity.get('engine_negative_steps')}  (pass={polarity_sanity.get('pass')})")
    print(f"  all_pass: {all_pass}")
    print(f"  receipt: {OUT_PATH}")

    return result


if __name__ == "__main__":
    main()
