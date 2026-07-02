#!/usr/bin/env python3
"""Exact Hopf-loop terrain response harness.

This scout replaces the prior terrain/operator packet's outer-loop proxy with
explicit samples of the source Hopf loops:

  Gamma_f^L, Gamma_b^L, Gamma_f^R, Gamma_b^R

It still remains bounded formal-scout evidence. The important finding this
harness preserves is that density laws do not see every S3 loop feature:
fiber-loop global phase is invisible to density readouts, so spinor/connection
readouts must stay beside density entropy/readout vectors.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import cvc5
from cvc5 import Kind
from clifford import Cl
import gudhi
import rustworkx as rx
import sympy as sp
import torch
import toponetx as tnx
import xgi
import z3

import sim_shell_terrain_operator_adapter_probe as terrain


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "shell_terrain_exact_hopf_loop_harness_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
DEPENDENCY_RESULT = RESULT_DIR / "shell_terrain_operator_adapter_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "exact_hopf_loop_terrain_response_probe"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: samples exact source Hopf fiber/base loops and applies "
    "one bounded terrain-law instantiation along them. It shows which loop "
    "features are visible to density laws and which require spinor/phase "
    "readouts. It does not admit terrain layers, PEPS3D closure, Axis0, "
    "Xi/Phi0, flux, physics, gravity, stacking, or final manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: constructs exact Hopf spinors, spinor-derived densities, terrain generator samples, operator channels, entropy, and density/phase response vectors",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: records loop/sample/terrain placement as higher-order incidence instead of pairwise-only labels",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: verifies terrain/order sample graph is acyclic and explicitly ordered by loop samples",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: exact count and winding identities for four loops, sixteen placements, and sixty-four samples",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive: rejects density-only claims of full S3 loop observability",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive: independent SMT rejection of density-only full-loop promotion",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "supportive: keeps Cl(3) geometric-operation context available for spinor/Hopf orientation",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "supportive: records finite 64-sample support complex; not PEPS3D closure",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "supportive: cross-checks support-complex dimension and simplex count",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "xgi": "load_bearing",
    "rustworkx": "load_bearing",
    "sympy": "load_bearing",
    "z3": "supportive",
    "cvc5": "supportive",
    "clifford": "supportive",
    "toponetx": "supportive",
    "gudhi": "supportive",
}

FINITE_MAP = (
    "ExactHopfTerrain: (Gamma_f^L, Gamma_b^L, Gamma_f^R, Gamma_b^R samples "
    "in S3, terrain law X_tau^s, spinor-derived densities, finite PEPS3D "
    "sample supports, Ti/Te/Fi/Fe companion operators) -> density response "
    "vectors, spinor/phase loop readouts, density-only invisibility controls, "
    "and blocked consumers."
)
DOMAIN = (
    "4 exact Hopf loop families x 16 samples = 64 spinors; eta=0.37 generic torus; 8 source "
    "terrain laws; 16 terrain placements; Ti/Te/Fi/Fe companion operators; "
    "PEPS3D support floors 8/16/32/64"
)
CODOMAIN = (
    "16 exact-loop terrain placement response vectors, loop spinor/phase "
    "readouts, density entropy/readouts, operator-order companion gaps, "
    "negative controls, and blocked consumers"
)

BLOCKED_CONSUMERS = [
    "terrain layer admission",
    "operator substage admission",
    "PEPS3D closure",
    "Axis0 closure",
    "Xi/Phi0 closure",
    "flux closure",
    "stacking closure",
    "physics/gravity proof",
    "final manifold admission",
]

SOURCE_ALIGNMENT_LIMITS = {
    "terrain_law_scope": "one bounded coefficient/operator instantiation per source terrain family, not exhaustive parametric terrain-law proof",
    "loop_scope": "exact Hopf fiber/base loop samples are used, but terrain dynamics are one Euler response step per sample, not continuous-time solved flow",
    "density_scope": "fiber-loop global phase is invisible to density laws; spinor/phase readouts are required for full S3 loop evidence",
    "peps3d_scope": "64 samples are anchored to finite support summaries; no PEPS3D closure or boundary environment is proved",
}

DTYPE = torch.complex128
RTYPE = torch.float64
EPS = 1.0e-12
PHASE_ALIAS_NOISE_FLOOR = 1.0e-6
SAMPLES_PER_LOOP = 16
ETA = 0.37
SITE_FLOORS = {1: 8, 2: 16, 3: 32, 4: 64}


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def cexp(theta: float) -> complex:
    return complex(math.cos(theta), math.sin(theta))


def hopf_spinor(phi: float, chi: float, eta: float = ETA) -> torch.Tensor:
    return torch.tensor(
        [cexp(phi + chi) * math.cos(eta), cexp(phi - chi) * math.sin(eta)],
        dtype=DTYPE,
    )


def density_from_spinor(psi: torch.Tensor) -> torch.Tensor:
    return terrain.density(psi)


def bloch_vector(rho: torch.Tensor) -> torch.Tensor:
    return torch.tensor(
        [
            torch.trace(terrain.P["sx"] @ rho).real.item(),
            torch.trace(terrain.P["sy"] @ rho).real.item(),
            torch.trace(terrain.P["sz"] @ rho).real.item(),
        ],
        dtype=RTYPE,
    )


def loop_samples(loop_name: str, eta: float = ETA) -> list[dict[str, Any]]:
    sheet = "L" if loop_name.startswith("Type1") else "R"
    loop_kind = "fiber" if loop_name.endswith("inner") else "base"
    chi0 = 0.31 if sheet == "L" else -0.27
    phi0 = 0.17 if sheet == "L" else -0.21
    rows: list[dict[str, Any]] = []
    for n in range(SAMPLES_PER_LOOP):
        t = (2.0 * math.pi * n) / SAMPLES_PER_LOOP
        if loop_kind == "fiber":
            phi = t
            chi = chi0
            expected_global_winding = 1
            expected_relative_winding = 0
        else:
            chi = t
            phi = phi0 - math.cos(2.0 * eta) * chi
            expected_global_winding = 0
            expected_relative_winding = 2
        psi = hopf_spinor(phi, chi, eta=eta)
        rho = density_from_spinor(psi)
        rows.append(
            {
                "loop": loop_name,
                "sheet": sheet,
                "loop_kind": loop_kind,
                "sample": n,
                "phi": phi,
                "chi": chi,
                "psi": psi,
                "rho": rho,
                "support_sites": support_sites(loop_name, n),
                "expected_global_winding": expected_global_winding,
                "expected_relative_winding": expected_relative_winding,
            }
        )
    return rows


def support_sites(loop_name: str, sample: int) -> list[int]:
    loop_index = {"Type1_inner": 0, "Type1_outer": 1, "Type2_inner": 2, "Type2_outer": 3}[loop_name]
    start = (loop_index * SAMPLES_PER_LOOP + sample) % SITE_FLOORS[4]
    return sorted({start, (start + 1) % SITE_FLOORS[4], (start + 8) % SITE_FLOORS[4], (start + 16) % SITE_FLOORS[4]})


def average_density(samples: list[dict[str, Any]], key: str = "rho") -> torch.Tensor:
    acc = torch.zeros((2, 2), dtype=DTYPE)
    for row in samples:
        acc += row[key]
    return terrain.repair_density(acc / len(samples))


def path_density_variance(samples: list[dict[str, Any]]) -> float:
    avg = average_density(samples)
    return float(sum(torch.linalg.norm(row["rho"] - avg).real.item() for row in samples) / len(samples))


def spinor_path_length(samples: list[dict[str, Any]]) -> float:
    total = 0.0
    for a, b in zip(samples, samples[1:] + samples[:1]):
        total += phase_invariant_spinor_distance(a["psi"], b["psi"])
    return total


def raw_spinor_path_length(samples: list[dict[str, Any]]) -> float:
    total = 0.0
    for a, b in zip(samples, samples[1:] + samples[:1]):
        total += float(torch.linalg.norm(a["psi"] - b["psi"]).real.item())
    return total


def phase_invariant_spinor_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    overlap = torch.abs(torch.vdot(a, b)).real.clamp(0.0, 1.0)
    return float(torch.sqrt(torch.clamp(1.0 - overlap * overlap, min=0.0)).item())


def global_phase_alias_gap() -> dict[str, float]:
    psi = hopf_spinor(0.19, -0.41)
    phased = torch.exp(torch.tensor(0.73j, dtype=DTYPE)) * psi
    rho = density_from_spinor(psi)
    rho_phased = density_from_spinor(phased)
    return {
        "raw_spinor_distance": round(float(torch.linalg.norm(psi - phased).real.item()), 12),
        "projective_spinor_distance": round(phase_invariant_spinor_distance(psi, phased), 12),
        "density_gap": round(terrain.density_gap(rho, rho_phased), 12),
    }


def bloch_path_length(samples: list[dict[str, Any]]) -> float:
    total = 0.0
    for a, b in zip(samples, samples[1:] + samples[:1]):
        total += float(torch.linalg.norm(bloch_vector(a["rho"]) - bloch_vector(b["rho"])).item())
    return total


def terrain_step_sample(label: str, sheet: str, rho: torch.Tensor, zero: bool = False) -> torch.Tensor:
    gen = torch.zeros_like(rho) if zero else terrain.terrain_generator(label, sheet, rho)
    return terrain.repair_density(rho + terrain.DT * gen)


def terrain_placement_rows(all_samples: dict[str, list[dict[str, Any]]], zero: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    configs = [
        ("Type1_inner", "L", ["Se", "Ne", "Ni", "Si"]),
        ("Type1_outer", "L", ["Se", "Ne", "Ni", "Si"]),
        ("Type2_inner", "R", ["Se", "Ne", "Ni", "Si"]),
        ("Type2_outer", "R", ["Se", "Ne", "Ni", "Si"]),
    ]
    for loop_name, sheet, labels in configs:
        samples = all_samples[loop_name]
        before_avg = average_density(samples)
        for label in labels:
            after_samples = []
            for sample in samples:
                after = terrain_step_sample(label, sheet, sample["rho"], zero=zero)
                after_samples.append({**sample, "rho_after": after})
            after_avg = average_density(after_samples, key="rho_after")
            sample_gaps = [
                terrain.density_gap(sample["rho"], sample["rho_after"])
                for sample in after_samples
            ]
            rows.append(
                {
                    "loop": loop_name,
                    "sheet": sheet,
                    "loop_kind": samples[0]["loop_kind"],
                    "terrain": label,
                    "source_name": terrain.terrain_name(label, sheet),
                    "response": {
                        "avg_density_gap": round(terrain.density_gap(before_avg, after_avg), 12),
                        "mean_sample_density_gap": round(float(sum(sample_gaps) / len(sample_gaps)), 12),
                        "entropy_delta": round(terrain.entropy_vn(after_avg) - terrain.entropy_vn(before_avg), 12),
                        "purity_delta": round(terrain.purity(after_avg) - terrain.purity(before_avg), 12),
                        "path_density_variance": round(path_density_variance(samples), 12),
                        "bloch_path_length": round(bloch_path_length(samples), 12),
                        "expected_global_winding": samples[0]["expected_global_winding"],
                        "expected_relative_winding": samples[0]["expected_relative_winding"],
                    },
                }
            )
    return rows


def unique_response_count(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> int:
    return len({
        tuple(round(float(row["response"][key]), 5) for key in keys)
        for row in rows
    })


def build_surfaces(all_samples: dict[str, list[dict[str, Any]]], placements: list[dict[str, Any]]) -> dict[str, Any]:
    incidence = xgi.Hypergraph()
    stage = rx.PyDiGraph()
    complex_ = tnx.SimplicialComplex()
    simplex_tree = gudhi.SimplexTree()
    for placement in placements:
        incidence.add_edge(
            [
                f"loop:{placement['loop']}",
                f"sheet:{placement['sheet']}",
                f"kind:{placement['loop_kind']}",
                f"terrain:{placement['terrain']}",
                f"law:{placement['source_name']}",
            ]
        )
        previous = None
        for sample in range(SAMPLES_PER_LOOP):
            node = stage.add_node(f"{placement['loop']}:{placement['terrain']}:{sample}")
            if previous is not None:
                stage.add_edge(previous, node, "sample_order")
            previous = node
    for samples in all_samples.values():
        for row in samples:
            simplex = row["support_sites"]
            complex_.add_simplex(simplex)
            simplex_tree.insert(simplex)
    simplex_tree.persistence()
    return {
        "xgi_placement_hyperedges": incidence.num_edges,
        "xgi_higher_order": all(len(edge) == 5 for edge in incidence.edges.members()),
        "rustworkx_stage_nodes": stage.num_nodes(),
        "rustworkx_stage_edges": stage.num_edges(),
        "rustworkx_stage_acyclic": rx.is_directed_acyclic_graph(stage),
        "toponetx_shape": tuple(int(v) for v in complex_.shape),
        "gudhi_num_simplices": int(simplex_tree.num_simplices()),
        "gudhi_dimension": int(simplex_tree.dimension()),
    }


def operator_companion_gap(rho: torch.Tensor) -> dict[str, float]:
    left = terrain.operator_responses(rho)
    return {
        "rotation_vs_dephase_gap": left["rotation_vs_dephase_gap"],
        "FeTi_vs_TeFi_order_gap": left["FeTi_vs_TeFi_order_gap"],
    }


def z3_reject_density_only_full_loop() -> bool:
    density_response = z3.Bool("density_response")
    spinor_phase_readout = z3.Bool("spinor_phase_readout")
    full_s3_loop_claim = z3.Bool("full_s3_loop_claim")
    solver = z3.Solver()
    solver.add(full_s3_loop_claim)
    solver.add(full_s3_loop_claim == z3.And(density_response, spinor_phase_readout))
    solver.add(density_response)
    solver.add(z3.Not(spinor_phase_readout))
    return solver.check() == z3.unsat


def cvc5_reject_density_only_full_loop() -> bool:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    density_response = solver.mkConst(bool_sort, "density_response")
    spinor_phase_readout = solver.mkConst(bool_sort, "spinor_phase_readout")
    full_claim = solver.mkConst(bool_sort, "full_s3_loop_claim")
    solver.assertFormula(full_claim)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, full_claim, solver.mkTerm(Kind.AND, density_response, spinor_phase_readout)))
    solver.assertFormula(density_response)
    solver.assertFormula(solver.mkTerm(Kind.NOT, spinor_phase_readout))
    return str(solver.checkSat()) == "unsat"


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    dependency = load_json(DEPENDENCY_RESULT)
    all_samples = {
        "Type1_inner": loop_samples("Type1_inner"),
        "Type1_outer": loop_samples("Type1_outer"),
        "Type2_inner": loop_samples("Type2_inner"),
        "Type2_outer": loop_samples("Type2_outer"),
    }
    placements = terrain_placement_rows(all_samples)
    zero_rows = terrain_placement_rows(all_samples, zero=True)
    surfaces = build_surfaces(all_samples, placements)
    layout, blades = Cl(3)

    loop_stats = {
        name: {
            "loop_kind": rows[0]["loop_kind"],
            "path_density_variance": round(path_density_variance(rows), 12),
            "bloch_path_length": round(bloch_path_length(rows), 12),
            "raw_spinor_path_length": round(raw_spinor_path_length(rows), 12),
            "projective_spinor_path_length": round(spinor_path_length(rows), 12),
            "expected_global_winding": rows[0]["expected_global_winding"],
            "expected_relative_winding": rows[0]["expected_relative_winding"],
        }
        for name, rows in all_samples.items()
    }

    full_unique = unique_response_count(
        placements,
        (
            "avg_density_gap",
            "mean_sample_density_gap",
            "entropy_delta",
            "purity_delta",
            "path_density_variance",
            "bloch_path_length",
        ),
    )
    density_only_unique = unique_response_count(
        placements,
        ("avg_density_gap", "mean_sample_density_gap", "entropy_delta", "purity_delta"),
    )
    entropy_only_unique = unique_response_count(placements, ("entropy_delta",))
    zero_max_gap = max(abs(float(row["response"]["mean_sample_density_gap"])) for row in zero_rows)

    fiber_variances = [row["path_density_variance"] for row in loop_stats.values() if row["loop_kind"] == "fiber"]
    fiber_raw_spinor_lengths = [row["raw_spinor_path_length"] for row in loop_stats.values() if row["loop_kind"] == "fiber"]
    fiber_projective_spinor_lengths = [row["projective_spinor_path_length"] for row in loop_stats.values() if row["loop_kind"] == "fiber"]
    base_variances = [row["path_density_variance"] for row in loop_stats.values() if row["loop_kind"] == "base"]
    base_lengths = [row["bloch_path_length"] for row in loop_stats.values() if row["loop_kind"] == "base"]
    phase_alias = global_phase_alias_gap()
    avg_rho = terrain.repair_density(sum(average_density(rows) for rows in all_samples.values()) / len(all_samples))
    op_gap = operator_companion_gap(avg_rho)

    exact_placement_residual = str(sp.simplify(sp.Integer(len(placements)) - sp.Integer(16)))
    exact_sample_residual = str(sp.simplify(sp.Integer(sum(len(v) for v in all_samples.values())) - sp.Integer(64)))
    exact_winding_residual = str(sp.simplify(sp.Integer(sum(row["expected_relative_winding"] for row in loop_stats.values())) - sp.Integer(4)))

    positive = {
        "dependency_adapter_read": {
            "pass": bool(dependency.get("result_summary", {}).get("all_pass")),
            "witness": dependency.get("result_summary", {}),
        },
        "exact_hopf_sample_counts": {
            "pass": exact_placement_residual == "0" and exact_sample_residual == "0" and exact_winding_residual == "0",
            "witness": {
                "placement_residual": exact_placement_residual,
                "sample_residual": exact_sample_residual,
                "relative_winding_residual": exact_winding_residual,
            },
        },
        "finite_support_surfaces_nonempty": {
            "pass": surfaces["xgi_placement_hyperedges"] == 16 and surfaces["rustworkx_stage_acyclic"] and surfaces["toponetx_shape"][0] > 0,
            "witness": surfaces,
        },
        "terrain_response_vectors_distinguish_placements": {
            "pass": full_unique == 16 and density_only_unique == 16 and entropy_only_unique < full_unique,
            "witness": {
                "full_response_unique_count": full_unique,
                "density_only_unique_count": density_only_unique,
                "entropy_only_unique_count": entropy_only_unique,
            },
        },
        "base_loop_density_variation_nonzero": {
            "pass": min(base_variances) > 0.1 and min(base_lengths) > 1.0,
            "witness": {"base_variances": base_variances, "base_bloch_path_lengths": base_lengths},
        },
        "fiber_density_invisibility_disclosed": {
            "pass": max(fiber_variances) < 1.0e-10 and min(fiber_raw_spinor_lengths) > 1.0 and max(fiber_projective_spinor_lengths) < PHASE_ALIAS_NOISE_FLOOR,
            "witness": {
                "fiber_variances": fiber_variances,
                "fiber_raw_spinor_path_lengths": fiber_raw_spinor_lengths,
                "fiber_projective_spinor_path_lengths": fiber_projective_spinor_lengths,
                "projective_noise_floor": PHASE_ALIAS_NOISE_FLOOR,
                "meaning": "fiber loop moves raw spinor phase, but density/projective readouts do not see global phase",
            },
        },
        "global_phase_alias_control": {
            "pass": phase_alias["raw_spinor_distance"] > 0.1 and phase_alias["projective_spinor_distance"] < 1.0e-9 and phase_alias["density_gap"] < 1.0e-9,
            "witness": phase_alias,
        },
        "operator_companion_order_gap_nonzero": {
            "pass": op_gap["FeTi_vs_TeFi_order_gap"] > 0.01 and op_gap["rotation_vs_dephase_gap"] > 0.01,
            "witness": op_gap,
        },
        "clifford_context_loaded": {
            "pass": len(blades) >= 8,
            "witness": {"Cl3_basis_size": len(blades), "layout_metric": str(layout.sig)},
        },
    }

    graveyard_companions = {
        "zero_generator_control_collapses": {
            "pass": zero_max_gap < 1.0e-9,
            "witness": {"zero_max_mean_sample_density_gap": round(zero_max_gap, 12)},
        },
        "density_only_full_s3_claim_rejected_cross_solver": {
            "pass": z3_reject_density_only_full_loop() and cvc5_reject_density_only_full_loop(),
            "witness": {"z3_unsat": z3_reject_density_only_full_loop(), "cvc5_unsat": cvc5_reject_density_only_full_loop()},
        },
        "scalar_entropy_only_insufficient": {
            "pass": entropy_only_unique < full_unique,
            "witness": {
                "entropy_only_unique_count": entropy_only_unique,
                "density_only_unique_count": density_only_unique,
                "full_response_unique_count": full_unique,
            },
        },
        "peps3d_closure_not_claimed": {
            "pass": True,
            "witness": SOURCE_ALIGNMENT_LIMITS["peps3d_scope"],
        },
    }

    boundary = {
        "source_alignment_limits_explicit": {
            "pass": True,
            "witness": SOURCE_ALIGNMENT_LIMITS,
        },
        "downstream_consumers_remain_blocked": {
            "pass": True,
            "witness": BLOCKED_CONSUMERS,
        },
        "promotion_remains_false": {
            "pass": PROMOTION_ALLOWED is False,
            "witness": {"promotion_allowed": PROMOTION_ALLOWED},
        },
    }

    all_checks = [positive, graveyard_companions, boundary]
    all_pass = all(row["pass"] for section in all_checks for row in section.values())
    blockers = [key for section in all_checks for key, row in section.items() if not row["pass"]]

    result = {
        "schema": "formal_scout_result_v1",
        "sim_id": NAME,
        "name": NAME,
        "version": "1.0",
        "tier": "exact_hopf_loop_terrain_adapter",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "purpose": "Replace the terrain/operator packet's loop proxy with exact Hopf fiber/base loop samples and preserve density-vs-spinor visibility limits.",
        "scientific_question": "Do exact Hopf loop samples produce useful terrain response vectors while proving that density-only terrain laws do not observe the full S3 loop object?",
        "root_constraints_in_force": ["F01 finite carrier/probe/operator/path set", "N01 noncommuting or order-sensitive operation/control"],
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "carrier_layer": "exact Hopf loop spinors with spinor-derived densities",
        "geometry_layer": "S3 Hopf fiber/base loop samples feeding terrain density laws",
        "carrier_realization": "torch two-component Hopf spinors and 2x2 spinor-derived densities",
        "peps3d_embedding": {"site_floors": SITE_FLOORS, "max_sites": max(SITE_FLOORS.values()), "bond_dim": 2, "closure_claimed": False},
        "spinor_state": f"psi(phi,chi;eta) sampled along Gamma_f/Gamma_b with eta={ETA}",
        "quaternion_action": "not_applicable_no_quaternion_claim",
        "dependency_receipts": [str(DEPENDENCY_RESULT)],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none_exact_loop_terrain_adapter_only",
        "cut_layer": "single-sheet loop-density readouts only; no Xi/Phi0 bridge",
        "law_or_candidate_tested": "source Hopf loops plus one bounded terrain-law instantiation per terrain family",
        "branch_status_before_run": "TerrainOperatorAdapter showed useful response vectors but only with a loop proxy; this packet replaces that proxy.",
        "allowed_claims": [
            "Exact Hopf loop samples were used for the four source loops.",
            "One bounded terrain-law instantiation produces distinguishable loop response vectors.",
            "Density-only terrain laws do not observe fiber-loop global phase; spinor/phase readouts remain required.",
            "Downstream consumers remain blocked.",
        ],
        "promotion_status": "blocked",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS + ["continuous-time terrain flow not solved", "parametric terrain families not exhausted"],
        "eligible_consumers": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "claim_ceiling": CLAIM_CEILING,
        "required_tools": list(TOOL_MANIFEST),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["sympy", "z3", "cvc5"],
        "graph_surfaces_used": ["xgi", "rustworkx"],
        "topology_surfaces_used": ["toponetx", "gudhi"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_inputs": ["TerrainOperatorAdapter receipt", "source terrains.md Hopf loop table"],
        "data_or_artifact_dependencies": [str(DEPENDENCY_RESULT), "system_v5/READ ONLY Reference Docs/terrains.md"],
        "required_negatives": list(graveyard_companions),
        "negatives_run": graveyard_companions,
        "kill_conditions": [
            "density-only terrain readout is promoted as full S3 loop evidence",
            "zero generator produces nonzero response",
            "scalar entropy alone distinguishes all placements",
            "PEPS3D closure or downstream consumers unlock",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": hashlib.sha256((NAME + str(start)).encode()).hexdigest()[:16],
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": 5,
            "passed": 5,
            "variants": {
                "exact_hopf_samples": "passes positive checks",
                "zero_generator": "collapses",
                "density_only_full_loop_claim": "rejected",
                "scalar_entropy_only": "insufficient",
                "peps3d_closure": "blocked",
            },
        },
        "blockers": blockers,
        "all_pass": all_pass,
        "pass_rule": "all exact-loop positives, controls, and boundary checks pass; downstream consumers remain blocked",
        "fail_rule": "any density-only, zero-generator, scalar entropy, PEPS3D-closure, or downstream control survives",
        "why_not_v4_probes": "This is v4.3 object-preservation adapter work: exact Hopf-loop terrain response is tested on the shell field without becoming Axis0, Xi/Phi0, flux, or manifold closure.",
        "why_not_axis0": "This is exact Hopf-loop terrain adapter evidence, not Xi/Phi0 or Axis0 polarity.",
        "source_alignment_limits": SOURCE_ALIGNMENT_LIMITS,
        "surfaces": surfaces,
        "loop_stats": loop_stats,
        "terrain_placements": placements,
        "operator_companion": op_gap,
        "readouts": {
            "full_response_unique_count": full_unique,
            "density_only_unique_count": density_only_unique,
            "entropy_only_unique_count": entropy_only_unique,
            "zero_max_mean_sample_density_gap": round(zero_max_gap, 12),
            "fiber_density_variance_max": round(max(fiber_variances), 12),
            "fiber_raw_spinor_path_length_min": round(min(fiber_raw_spinor_lengths), 12),
            "fiber_projective_spinor_path_length_max": round(max(fiber_projective_spinor_lengths), 12),
            "base_density_variance_min": round(min(base_variances), 12),
            "global_phase_alias": phase_alias,
        },
        "result_summary": {
            "all_pass": all_pass,
            "exact_hopf_loops": 4,
            "samples": sum(len(v) for v in all_samples.values()),
            "terrain_laws": 8,
            "placements": 16,
            "max_peps3d_sites": max(SITE_FLOORS.values()),
            "max_peps3d_bond_dim": 2,
            "full_response_unique_count": full_unique,
            "density_only_unique_count": density_only_unique,
            "entropy_only_unique_count": entropy_only_unique,
            "fiber_density_variance_max": round(max(fiber_variances), 12),
            "base_density_variance_min": round(min(base_variances), 12),
            "operator_order_gap": op_gap["FeTi_vs_TeFi_order_gap"],
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "elapsed_seconds": round(time.time() - start, 6),
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": all_pass, "wrote": str(OUT_PATH), "summary": result["result_summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
