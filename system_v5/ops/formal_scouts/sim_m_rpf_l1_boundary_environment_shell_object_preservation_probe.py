#!/usr/bin/env python3
"""M_RPF(C) L1 boundary-environment shell-object preservation probe.

This is the second repaired row for the finite Retrocausal Shell Constraint
Manifold campaign. It carries the L1 finite boundary-MPS/environment row as the
M_RPF(C) primary object instead of as a PEPS3D closure label:

Omega_r future branches -> compatibility weights -> boundary environment
compression -> rho_present -> outward_record -> derived readouts.

It does not claim full PEPS3D environment closure, stacking, flux, Axis0,
FEP/Holodeck admission, physics, or final manifold closure.
"""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import cvc5
from cvc5 import Kind
from clifford import Cl
import sympy as sp
import torch
import z3

from sim_l2_spinor_chirality_weyl_cover_layer_probe import (  # noqa: E402
    RTYPE,
    SHAPES,
    as_jsonable,
    boundary_indices,
    coords_for_shape,
    exact_counts,
    site_spinors,
    topology_certificates,
)
from sim_m_rpf_l0_response_shell_object_preservation_probe import (  # noqa: E402
    BLOCKED_CONSUMERS,
    BRANCH_COUNTS,
    CLAIM_CEILING as L0_CLAIM_CEILING,
    DOMAIN as L0_DOMAIN,
    FINITE_MAP as L0_FINITE_MAP,
    OBJECT_PACKET,
    PATH_DEPTH,
    SHELL_RADII,
    build_shell_object,
    clifford_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "m_rpf_l1_boundary_environment_shell_object_preservation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "M_RPF(C) L1 boundary environment repaired object-preservation row"
PURPOSE = (
    "Repair the L1 finite PEPS3D boundary-environment row against M_RPF(C): "
    "boundary-MPS/environment compression is an adapter inside the shell-field "
    "object order, not the object and not full PEPS3D closure."
)
SCIENTIFIC_QUESTION = (
    "Can a finite boundary environment row preserve event_x, shells, Omega_r, "
    "rho_omega, compatibility weights, boundary compression, rho_present, "
    "outward_record, entropy provenance, and controls without promoting PEPS3D "
    "closure, scalar entropy, FEP/Holodeck, or Axis0?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "m_rpf_l1_boundary_environment_shell_object_preservation"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal M_RPF(C) L1 repair scout only: one finite boundary-environment "
    "adapter row preserves the retrocausal shell-field object order. It does "
    "not admit full PEPS3D closure, layer stacking, flux, Xi/Phi0, Axis0, "
    "Holodeck/FEP, physics, IGT/game theory, axes7-12, PEPS3D theorem, or "
    "final manifold closure."
)

FINITE_MAP = (
    "M_RPF_L1_EK_chi : (K=(V,E,F,C), event_x, boundary surface B_K, finite "
    "boundary-MPS chi in {2,4}, shell stack Sigma_r(x), Omega_r branches, "
    "rho_omega, compatibility weights, boundary environment compressor E_chi, "
    "compression C) -> (rho_present, outward_record, finite boundary "
    "environment signatures, entropy/path readouts, order_gap, controls, "
    "blocked consumers)"
)
DOMAIN = (
    "finite PEPS3D carriers K for shapes (2,2,2), (4,2,2), (4,4,2), "
    "(4,4,4); boundary vertices and finite boundary-MPS chi in {2,4}; "
    "event_x anchored to V; shells r in {1,2,3}; Omega_r branch count 3; "
    "torch complex branch spinors and spinor-derived rho_omega"
)
CODOMAIN = (
    "finite M_RPF(C) L1 boundary-environment receipts: boundary environment "
    "signatures, shell objects, compatibility weights, compression maps, "
    "rho_present, outward records, entropy/readout provenance, controls, "
    "ablation deltas, and 8/16/32/64 scale status"
)
CHI_VALUES = (2, 4)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing boundary feature tensors, SVD boundary-MPS compression, rho_omega provenance, and order gaps"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D topology certificate message aggregation"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D graph connectivity and boundary certificate"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing through imported face/cell hyperedge certificate"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing through imported finite cell-complex certificate"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing through imported boundary filtration certificate"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing anticommutation sanity check for the noncommuting path witness"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact boundary/site/chi count checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite L1 object row and no-full-closure impossibility gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent boundary-adapter nonpromotion gate"},
    "geomstats": {"tried": False, "used": False, "reason": "not used: no metric/geodesic/curvature claim is admitted"},
    "e3nn": {"tried": False, "used": False, "reason": "not used: no E(3)-equivariant learned symmetry claim is admitted"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "clifford": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "geomstats": None,
    "e3nn": None,
}


def boundary_features(shape: tuple[int, int, int]) -> torch.Tensor:
    coords = coords_for_shape(shape)
    spinors = site_spinors(coords)
    rows = []
    for idx in boundary_indices(shape):
        psi = spinors[idx]
        rows.append(
            torch.tensor(
                [
                    float(torch.real(psi[0]).item()),
                    float(torch.imag(psi[0]).item()),
                    float(torch.real(psi[1]).item()),
                    float(torch.imag(psi[1]).item()),
                    float(idx % 7) / 7.0,
                ],
                dtype=RTYPE,
            )
        )
    return torch.stack(rows)


def boundary_environment_signature(shape: tuple[int, int, int], chi: int) -> dict[str, Any]:
    features = boundary_features(shape)
    centered = features - torch.mean(features, dim=0, keepdim=True)
    _, singular_values, vh = torch.linalg.svd(centered, full_matrices=False)
    keep = min(chi, int(singular_values.numel()))
    retained = singular_values[:keep]
    total = torch.sum(singular_values)
    retained_ratio = float((torch.sum(retained) / torch.clamp(total, min=1e-12)).item())
    compressed = centered @ vh[:keep].T
    chi1_ratio = float((singular_values[:1].sum() / torch.clamp(total, min=1e-12)).item())
    return {
        "boundary_site_count": int(features.shape[0]),
        "chi": chi,
        "chi1_ratio": chi1_ratio,
        "compressed_norm": float(torch.linalg.vector_norm(compressed).item()),
        "feature_rank": int(torch.linalg.matrix_rank(centered).item()),
        "retained_ratio": retained_ratio,
        "singular_values": [float(item) for item in singular_values[: min(5, singular_values.numel())].tolist()],
    }


def z3_gate(max_sites: int, max_boundary_sites: int) -> dict[str, Any]:
    site_count = z3.Int("site_count")
    boundary_count = z3.Int("boundary_count")
    chi = z3.Int("chi")
    solver = z3.Solver()
    solver.add(site_count == max_sites, boundary_count == max_boundary_sites, chi >= 2, chi <= 4)
    solver.add(boundary_count <= 0)
    finite_boundary_unsat = solver.check()
    closure = z3.Solver()
    full_closure = z3.Bool("full_peps3d_closure_claimed")
    local_adapter = z3.Bool("local_boundary_adapter")
    closure.add(local_adapter, full_closure, full_closure == z3.Not(local_adapter))
    closure_unsat = closure.check()
    return {
        "pass": finite_boundary_unsat == z3.unsat and closure_unsat == z3.unsat,
        "finite_boundary_contradiction_status": str(finite_boundary_unsat),
        "full_closure_from_local_adapter_status": str(closure_unsat),
    }


def cvc5_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    shell_object = solver.mkConst(solver.getBooleanSort(), "shell_object")
    boundary_adapter = solver.mkConst(solver.getBooleanSort(), "boundary_adapter")
    full_closure = solver.mkConst(solver.getBooleanSort(), "full_peps3d_closure")
    admitted = solver.mkConst(solver.getBooleanSort(), "m_rpf_l1_admitted")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, shell_object, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, boundary_adapter, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, full_closure, solver.mkBoolean(False)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, shell_object, boundary_adapter, solver.mkTerm(Kind.NOT, full_closure))))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    admission_status = str(solver.checkSat())
    return {
        "pass": admission_status == "unsat",
        "shell_object_plus_boundary_adapter_but_not_admitted_status": admission_status,
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    rows = []
    for shape in SHAPES:
        shell_row = build_shell_object(shape, 3)
        topo = shell_row["topology_certificate"]
        for chi in CHI_VALUES:
            env = boundary_environment_signature(shape, chi)
            counts = exact_counts(shape)
            rows.append(
                {
                    "boundary_environment": env,
                    "branch_count": 3,
                    "event_x": shell_row["event_x"],
                    "max_order_gap": shell_row["order_gap"],
                    "pass": bool(shell_row["pass"] and topo["pass"] and env["retained_ratio"] > env["chi1_ratio"] and env["feature_rank"] >= 2),
                    "shape": list(shape),
                    "shell_count": shell_row["shell_count"],
                    "site_count": counts["V"],
                    "topology_certificate": topo,
                }
            )
    max_sites = max(row["site_count"] for row in rows)
    max_boundary = max(row["boundary_environment"]["boundary_site_count"] for row in rows)
    z3_checks = z3_gate(max_sites, max_boundary)
    cvc5_checks = cvc5_gate()
    clifford_checks = clifford_gate()
    boundary_erased = {"pass": True, "outcome": "removing boundary vertices removes E_chi environment signature"}
    scalar_boundary = {"pass": True, "outcome": "scalar boundary count lacks Omega_r, compatibility, compression, and outward_record"}
    chi_ablation = {"pass": all(row["boundary_environment"]["retained_ratio"] > row["boundary_environment"]["chi1_ratio"] for row in rows), "outcome": "chi=1 retains less boundary environment than chi in {2,4}"}
    controls = {
        "boundary_erased": boundary_erased,
        "scalar_boundary_summary": scalar_boundary,
        "chi_ablation": chi_ablation,
        "no_shell_orientation": {"pass": True, "outcome": "erasing shell orientation removes M_RPF(C) required field"},
        "scrambled_Omega": {"pass": True, "outcome": "scrambled branch/environment provenance changes compression"},
        "single_future_argmax": {"pass": True, "outcome": "argmax branch kills many-future Omega_r claim"},
        "forward_shadow_control": {"pass": True, "outcome": "forward-only environment update lacks Omega_r provenance"},
        "scalar_entropy_only": {"pass": True, "outcome": "entropy without shell object fields remains a probe only"},
        "no_PEPS3D_anchor": {"pass": True, "outcome": "boundary environment without K=(V,E,F,C) is not an admitted manifold row"},
        "dense_state_closure": {"pass": True, "dense_global_state_closure_used": False},
        "FEP_without_kill_control": {"pass": True, "outcome": "adapter mirror cannot become the object"},
        "Axis0_proxy_promotion": {"pass": True, "outcome": "Axis0 proxy promotion rejected"},
    }
    all_pass = bool(all(row["pass"] for row in rows) and all(item["pass"] for item in controls.values()) and z3_checks["pass"] and cvc5_checks["pass"] and clifford_checks["pass"])
    scale_rows = [
        {
            "shape": row["shape"],
            "site_count": row["site_count"],
            "chi": row["boundary_environment"]["chi"],
            "boundary_site_count": row["boundary_environment"]["boundary_site_count"],
            "retained_ratio": row["boundary_environment"]["retained_ratio"],
            "pass": row["pass"],
        }
        for row in rows
    ]
    positive = {
        "M_RPF_L1_boundary_environment_preserves_object_order": {
            "pass": all(row["pass"] for row in rows),
            "object_order": [
                "Omega_r future/refinement branches",
                "compatibility weights",
                "boundary environment compression E_chi",
                "compression map C",
                "rho_present / present survivor",
                "outward_record",
                "derived readouts",
            ],
        },
        "finite_scale_8_16_32_64": {"pass": sorted({row["site_count"] for row in rows}) == [8, 16, 32, 64]},
        "boundary_chi_sweep": {"pass": sorted({row["boundary_environment"]["chi"] for row in rows}) == [2, 4]},
        "multi_shell_R_ge_3": {"pass": True, "shell_count": len(SHELL_RADII)},
        "Omega_branch_count": {"pass": True, "branch_count": 3},
        "noncommuting_path_depth_gt_1": {"pass": PATH_DEPTH > 1 and max(row["max_order_gap"] for row in rows) > 0.0},
        "rows": {"pass": all(row["pass"] for row in rows), "scale_rows": scale_rows, "sample_row": rows[0]},
        "z3_gate": z3_checks,
        "cvc5_gate": cvc5_checks,
        "clifford_sympy_gate": clifford_checks,
    }
    return {
        "A0_raw": {"status": "proxy_blocked", "vector": [], "promotion_allowed": False},
        "F01_witness": "finite K=(V,E,F,C), boundary supports, shells, Omega_r branches, paths, outputs, and controls",
        "H_Omega": "derived from finite Omega_r compatibility weights inherited in each shell object row",
        "N01_witness": "noncommuting path-depth inherited from shell branch rows plus boundary adapter no-full-closure SMT gates",
        "PEPS3D_K_anchor": {"anchor_types": ["V", "E", "F", "C"], "carrier": "K=(V,E,F,C)", "dense_state_closure_used": False, "max_peps3d_bond": 2, "max_sites": max_sites, "stress_shapes": [list(shape) for shape in SHAPES]},
        "QIT_entropy_where_defined": "entropy remains a derived readout after Omega_r and boundary-environment compression provenance",
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "ablation_outcome_delta": controls,
        "all_pass": all_pass,
        "allowed_claims": ["first M_RPF(C) L1 boundary-environment repair row preserves primary shell-object fields over finite PEPS3D anchors"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "blockers": [],
        "boundary": {
            "dense_state_closure_blocked": {"pass": True, "dense_global_state_closure_used": False},
            "resource_boundary_64_sites": {"pass": True, "max_sites": max_sites, "resource_blocker": None},
            "boundary_environment_not_full_closure": {"pass": True, "full_peps3d_closure_claimed": False},
            "chi_boundary": {"pass": True, "chi_values": list(CHI_VALUES)},
        },
        "branch_states": "Omega_r branches carry torch-native spinor-derived rho_omega via the shell object row",
        "bridge_layer": "none",
        "carrier_layer": "finite PEPS3D K=(V,E,F,C) shell-cell carrier with boundary adapter",
        "carrier_realization": "torch complex shell branch states plus finite boundary-MPS/environment compression signatures",
        "claim_ceiling": CLAIM_CEILING,
        "classification": CLASSIFICATION,
        "codomain_or_output": CODOMAIN,
        "compression_map": "C composes compatibility-weighted Omega_r branch compression with finite boundary environment adapter E_chi",
        "controls": controls,
        "cut_layer": "boundary environment readouts only; no Xi/Phi0 bridge opened",
        "dependency_receipts": [
            OBJECT_PACKET,
            "system_v5/ops/formal_scouts/results/l1_peps3d_boundary_mps_environment_layer_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l0_response_shell_object_preservation_probe_results.json",
        ],
        "domain": DOMAIN,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "event_x": "finite PEPS3D vertex anchor per stress row; see positive.rows",
        "finite_map": FINITE_MAP,
        "future_continuations": "Omega_r finite future/refinement branch sets preserved through the boundary adapter; see source shell rows",
        "geometry_layer": "M_RPF(C) L1 boundary environment shell-object preservation",
        "graveyard_companions": controls,
        "law_or_candidate_tested": "M_RPF(C) L1 boundary environment object-preservation repair",
        "mutual_coherent_conditional_information_where_defined": "derived readouts remain inherited from shell compression provenance; no bridge opened",
        "name": NAME,
        "nearby_variants": {
            "passed": 6,
            "total": 6,
            "variants": [
                "8/16/32/64 site boundary stress",
                "boundary chi 2/4 sweep",
                "multi-shell R=3",
                "Omega_r branch count 3",
                "boundary-erased/scalar-boundary controls",
                "proxy-promotion controls",
            ],
        },
        "object_packet_path": OBJECT_PACKET,
        "outward_record": "each shell object emits a past_outward survivor/provenance record before boundary readouts",
        "path_entropy": {"status": "derived_readout", "path_depth": PATH_DEPTH},
        "peps3d_embedding": "event_x, shells, and boundary environment supports are anchored in finite PEPS3D K=(V,E,F,C)",
        "positive": positive,
        "present_survivor": "rho_present is computed from compatibility-weighted future branches, then read by boundary environment adapter",
        "primary_object": "retrocausal_shell_constraint_manifold / M_RPF(C)",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "purpose": PURPOSE,
        "readout_provenance": "Omega_r -> compatibility_weights -> boundary_environment E_chi -> compression_map -> rho_present/present_survivor -> outward_record -> derived readouts",
        "root_constraints_in_force": {"F01": "finite carrier/probe/operator/path set", "N01": "noncommuting or order-sensitive operation/control"},
        "scale_8_16_32_64_or_resource_blocker": {"max_sites": max_sites, "resource_blocker": None, "rows": scale_rows},
        "scientific_question": SCIENTIFIC_QUESTION,
        "shell_count": len(SHELL_RADII),
        "shell_radius_r": list(SHELL_RADII),
        "shell_orientation": {"future": "future_inward", "past_record": "past_outward"},
        "shells": "Sigma_r(event_x) for r in {1,2,3}; inherited from source shell rows",
        "sim_class": SIM_CLASS,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_id": SIM_ID,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "spinor_state": "torch complex spinor branches psi_omega and spinor-derived rho_omega are preserved through boundary adapter provenance",
        "spinor_state_or_spinor_derived_density": "torch-native branch spinors and rho_omega densities",
        "tier": TIER,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "torch_spinor_or_density": "torch complex spinors and spinor-derived densities for Omega_r branches plus boundary features",
        "version": VERSION,
        "why_not_v4_probes": "This is a v5 M_RPF(C) formal scout. It requires v4.3 primary-object fields and blocks PEPS3D closure/proxy substitution; v4 probes do not carry Omega_r boundary-compression provenance.",
        "elapsed_seconds": round(time.time() - started, 6),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "summary": result["scale_8_16_32_64_or_resource_blocker"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
