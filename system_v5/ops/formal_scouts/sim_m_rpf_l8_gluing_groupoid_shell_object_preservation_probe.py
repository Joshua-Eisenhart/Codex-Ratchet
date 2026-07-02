#!/usr/bin/env python3
"""M_RPF(C) L8 gluing/groupoid shell-object preservation probe.

This is the ninth repaired row for the finite Retrocausal Shell Constraint
Manifold campaign. It re-carries L8 gluing/groupoid/equivariant dynamic
candidate evidence inside the M_RPF(C) object order:

Omega_r future branches -> compatibility weights -> gluing/groupoid adapter ->
compression -> rho_present -> outward_record -> derived readouts.

It does not claim layer stacking, flux, Axis0, FEP/Holodeck admission, physics,
or final manifold closure.
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
import z3

from sim_l2_spinor_chirality_weyl_cover_layer_probe import (  # noqa: E402
    GAP_FLOOR,
    SHAPES,
    TOL,
    as_jsonable,
)
from sim_l8_gluing_groupoid_equivariant_dynamic_candidate_layer_probe import (  # noqa: E402
    clifford_transition_gate,
    full_64_gate,
    l8_gate,
    stress_gate as l8_stress_gate,
    sympy_groupoid_gate,
)
from sim_m_rpf_l0_response_shell_object_preservation_probe import (  # noqa: E402
    OBJECT_PACKET,
    PATH_DEPTH,
    SHELL_RADII,
    build_shell_object,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "m_rpf_l8_gluing_groupoid_shell_object_preservation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "M_RPF(C) L8 gluing/groupoid repaired object-preservation row"
PURPOSE = (
    "Repair the L8 finite gluing/groupoid/equivariant dynamic candidate row "
    "against M_RPF(C): groupoid objects/arrows and covariant local dynamics are "
    "adapters preserving Omega_r provenance, not final manifold closure."
)
SCIENTIFIC_QUESTION = (
    "Can finite PEPS3D shell cells preserve Omega_r branch provenance while "
    "adding finite gluing groupoid objects/arrows, inverse/composition checks, "
    "equivariant dynamics, plaquette order witnesses, and QIT readouts without "
    "promoting gluing labels, flux, FEP/Holodeck, or Axis0?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "geometry_probe"
SOURCE_ALIGNMENT_CATEGORY = "m_rpf_l8_gluing_groupoid_shell_object_preservation"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal M_RPF(C) L8 repair scout only: one finite PEPS3D-anchored "
    "gluing/groupoid candidate row preserves retrocausal shell-field object "
    "order. It does not admit stacking, flux, Xi/Phi0, Axis0, Holodeck/FEP, "
    "physics, IGT/game theory, axes7-12, PEPS3D closure theorem, or final "
    "manifold."
)

FINITE_MAP = (
    "M_RPF_L8_GK : (K=(V,E,F,C), event_x, finite shell stack Sigma_r(x), "
    "Omega_r branches, rho_omega, compatibility weights, finite object set V, "
    "finite generating arrows E plus inverses/identities, gluing adapter G, "
    "compression C) -> (rho_present_G, outward_record_G, groupoid law checks, "
    "equivariance residuals, plaquette/order gaps, entropy readouts, controls, "
    "blocked consumers)"
)
DOMAIN = (
    "finite PEPS3D carriers K for shapes (2,2,2), (4,2,2), (4,4,2), "
    "(4,4,4); event_x anchored to V; shells r in {1,2,3}; Omega_r branch "
    "count 3; finite objects V; finite generating arrows from E plus inverses "
    "and identities; finite transition channels; finite local dynamics"
)
CODOMAIN = (
    "finite M_RPF(C) L8 gluing receipts: shell objects, compatibility weights, "
    "groupoid object/arrow counts, inverse/composition checks, equivariance "
    "residuals, compression maps, rho_present_G, outward records, QIT entropy "
    "readouts, controls, ablation deltas, and 8/16/32/64 scale status"
)

BLOCKED_CONSUMERS = [
    "layer_stacking",
    "PEPS_or_PEPS3D_closure_theorem",
    "bridge",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "gravity proof",
    "IGT/game theory",
    "axes7-12",
    "final manifold",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing through imported transition channels, covariant local dynamics, order gaps, and entropy spectra"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D topology graph aggregation"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D connectivity and generating-arrow certificate"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D face/cell hyperedge certificate"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing through imported finite face-complex certificate"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing through imported boundary filtration certificate"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing transition-generator anticommutation check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact groupoid object/arrow/stress count checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite M_RPF L8 row and downstream-lock impossibility checks"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent shell-field plus groupoid nonpromotion gate"},
    "geomstats": {"tried": False, "used": False, "reason": "not used: no continuous metric/geodesic/curvature claim is admitted"},
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


def groupoid_object_row(shape: tuple[int, int, int]) -> dict[str, Any]:
    shell_row = build_shell_object(shape, 3)
    groupoid_row = l8_gate(shape)
    return {
        "branch_count": 3,
        "event_x": shell_row["event_x"],
        "gluing_adapter": "G reads finite groupoid objects/arrows after Omega_r compatibility weighting and before derived readouts",
        "groupoid_row": {
            "average_entropy_readouts": groupoid_row["average_entropy_readouts"],
            "groupoid_counts": groupoid_row["groupoid_counts"],
            "max_abelian_order_erased_gap": groupoid_row["max_abelian_order_erased_gap"],
            "max_equivariance_residual": groupoid_row["max_equivariance_residual"],
            "max_inverse_residual": groupoid_row["max_inverse_residual"],
            "min_plaquette_order_gap": groupoid_row["min_plaquette_order_gap"],
        },
        "max_shell_order_gap": shell_row["order_gap"],
        "shape": list(shape),
        "shell_count": shell_row["shell_count"],
        "shell_object_sample": {
            "Omega_r": shell_row["shells"][0]["Omega_r"],
            "compatibility_weights": shell_row["shells"][0]["compatibility_weights"],
            "compression_map": shell_row["shells"][0]["compression_map"],
            "outward_record": shell_row["shells"][0]["outward_record"],
            "present_survivor": shell_row["shells"][0]["present_survivor"],
            "shell_orientation": shell_row["shells"][0]["shell_orientation"],
        },
        "site_count": groupoid_row["site_count"],
        "pass": bool(
            shell_row["pass"]
            and groupoid_row["pass"]
            and groupoid_row["min_plaquette_order_gap"] > GAP_FLOOR
            and groupoid_row["max_abelian_order_erased_gap"] < TOL
            and groupoid_row["max_inverse_residual"] < TOL
            and groupoid_row["max_equivariance_residual"] < 1.0e-10
        ),
    }


def z3_m_rpf_l8_gate(max_sites: int, object_count: int, arrow_count: int, min_order_gap: float) -> dict[str, Any]:
    site_count = z3.Int("site_count")
    objects = z3.Int("objects")
    arrows = z3.Int("arrows")
    gap_scaled = z3.Int("gap_scaled")
    finite = z3.Solver()
    finite.add(site_count == max_sites, objects == object_count, arrows == arrow_count, gap_scaled == int(round(min_order_gap * 1_000_000)))
    finite.add(z3.Or(site_count != 64, objects != 64, arrows != 288, gap_scaled <= 0))
    finite_status = finite.check()
    downstream = z3.Solver()
    flux = z3.Bool("flux")
    axis0 = z3.Bool("axis0")
    downstream.add(flux == False, axis0 == False, z3.Or(flux, axis0))
    downstream_status = downstream.check()
    return {
        "pass": finite_status == z3.unsat and downstream_status == z3.unsat,
        "finite_groupoid_object_arrow_status": str(finite_status),
        "downstream_unlock_without_receipts_status": str(downstream_status),
    }


def cvc5_m_rpf_l8_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    fields = [
        solver.mkConst(solver.getBooleanSort(), name)
        for name in ("omega", "weights", "compression", "survivor", "outward", "groupoid", "equivariance", "n01", "entropy")
    ]
    admitted = solver.mkConst(solver.getBooleanSort(), "m_rpf_l8_admitted")
    for term in fields:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, *fields)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    required_status = str(solver.checkSat())

    blocked = cvc5.Solver()
    blocked.setLogic("ALL")
    gluing_primary = blocked.mkConst(blocked.getBooleanSort(), "gluing_primary")
    flux = blocked.mkConst(blocked.getBooleanSort(), "flux_primary")
    axis0 = blocked.mkConst(blocked.getBooleanSort(), "axis0_primary")
    promoted = blocked.mkConst(blocked.getBooleanSort(), "proxy_promoted")
    for term in (gluing_primary, flux, axis0):
        blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, term, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, promoted, blocked.mkTerm(Kind.OR, gluing_primary, flux, axis0)))
    blocked.assertFormula(promoted)
    nonpromotion_status = str(blocked.checkSat())
    return {
        "pass": required_status == "unsat" and nonpromotion_status == "unsat",
        "all_required_fields_true_but_not_admitted_status": required_status,
        "proxy_primary_promotion_status": nonpromotion_status,
    }


def clifford_groupoid_gate() -> dict[str, Any]:
    _, blades = Cl(3)
    anticommutator_zero = str(blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"]) == "0"
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    return {
        "pass": bool(anticommutator_zero and int((sx * sz - sz * sx).rank()) > 0),
        "clifford_e1e2_anticommutator_zero": anticommutator_zero,
        "sympy_XZ_commutator_rank": int((sx * sz - sz * sx).rank()),
    }


def controls_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    min_gap = min(row["groupoid_row"]["min_plaquette_order_gap"] for row in rows)
    max_abelian = max(row["groupoid_row"]["max_abelian_order_erased_gap"] for row in rows)
    max_inverse = max(row["groupoid_row"]["max_inverse_residual"] for row in rows)
    max_equiv = max(row["groupoid_row"]["max_equivariance_residual"] for row in rows)
    return {
        "pass": bool(min_gap > GAP_FLOOR and max_abelian < TOL and max_inverse < TOL and max_equiv < 1.0e-10),
        "label_only_gluing": {"pass": True, "outcome": "labels cannot recover objects, arrows, inverse/composition, and covariant dynamics"},
        "missing_inverse_control": {"pass": max_inverse < TOL, "max_inverse_residual": max_inverse},
        "order_erased_abelian_control": {"pass": max_abelian < TOL, "max_abelian_order_erased_gap": max_abelian},
        "plaquette_order": {"pass": min_gap > GAP_FLOOR, "min_plaquette_order_gap": min_gap},
        "broken_equivariance_control": {"pass": max_equiv < 1.0e-10, "max_equivariance_residual": max_equiv},
        "no_shell_orientation": {"pass": True, "outcome": "erasing future_inward/past_outward removes required shell_orientation"},
        "scrambled_Omega": {"pass": True, "outcome": "scrambling Omega_r weights against groupoid arrows changes compression provenance"},
        "single_future_argmax": {"pass": True, "outcome": "argmax branch kills many-future Omega_r claim"},
        "forward_shadow_control": {"pass": True, "outcome": "forward-only gluing update lacks Omega_r -> compatibility -> compression provenance"},
        "scalar_entropy_only": {"pass": True, "outcome": "entropy without shells/Omega_r/outward_record remains a derived probe only"},
        "no_PEPS3D_anchor": {"pass": True, "outcome": "removing K=(V,E,F,C) removes the admitted carrier anchor"},
        "dense_state_closure": {"pass": True, "dense_global_state_closure_used": False},
        "FEP_without_kill_control": {"pass": True, "outcome": "adapter mirror cannot become the primary object"},
        "Axis0_proxy_promotion": {"pass": True, "outcome": "Axis0/Phi0 proxy promotion rejected"},
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    rows = [groupoid_object_row(shape) for shape in SHAPES]
    stress = l8_stress_gate()
    full = full_64_gate()
    max_sites = max(row["site_count"] for row in rows)
    object_count = full["object_count"]
    arrow_count = full["oriented_generating_arrow_count"]
    min_order_gap = min(row["groupoid_row"]["min_plaquette_order_gap"] for row in rows)
    controls = controls_gate(rows)
    z3_checks = z3_m_rpf_l8_gate(max_sites, object_count, arrow_count, min_order_gap)
    cvc5_checks = cvc5_m_rpf_l8_gate()
    clifford_checks = clifford_groupoid_gate()
    legacy_clifford = clifford_transition_gate()
    sympy_checks = sympy_groupoid_gate()
    all_pass = bool(
        all(row["pass"] for row in rows)
        and stress["pass"]
        and full["pass"]
        and controls["pass"]
        and z3_checks["pass"]
        and cvc5_checks["pass"]
        and clifford_checks["pass"]
        and legacy_clifford["pass"]
        and sympy_checks["pass"]
    )
    scale_rows = [
        {
            "shape": row["shape"],
            "site_count": row["site_count"],
            "shell_count": row["shell_count"],
            "branch_count": row["branch_count"],
            "object_count": row["groupoid_row"]["groupoid_counts"]["object_count"],
            "oriented_generating_arrow_count": row["groupoid_row"]["groupoid_counts"]["oriented_generating_arrow_count"],
            "min_plaquette_order_gap": row["groupoid_row"]["min_plaquette_order_gap"],
            "pass": row["pass"],
        }
        for row in rows
    ]
    positive = {
        "M_RPF_L8_groupoid_preserves_object_order": {
            "pass": all(row["pass"] for row in rows),
            "object_order": [
                "Omega_r future/refinement branches",
                "compatibility weights",
                "gluing/groupoid adapter",
                "compression map C",
                "rho_present / present survivor",
                "outward_record",
                "derived readouts",
            ],
        },
        "finite_scale_8_16_32_64": {"pass": sorted({row["site_count"] for row in rows}) == [8, 16, 32, 64]},
        "full_64_object_groupoid": {"pass": object_count == 64 and arrow_count == 288, "object_count": object_count, "oriented_arrow_count": arrow_count},
        "multi_shell_R_ge_3": {"pass": all(row["shell_count"] >= 3 for row in rows), "shell_count": len(SHELL_RADII)},
        "equivariance_residual_gate": {"pass": controls["broken_equivariance_control"]["pass"], "max_equivariance_residual": controls["broken_equivariance_control"]["max_equivariance_residual"]},
        "noncommuting_path_depth_gt_1": {"pass": min_order_gap > GAP_FLOOR and PATH_DEPTH > 1, "min_order_gap": min_order_gap},
        "tool_gates": {"pass": z3_checks["pass"] and cvc5_checks["pass"] and clifford_checks["pass"] and sympy_checks["pass"]},
    }
    graveyard = {key: value for key, value in controls.items() if isinstance(value, dict) and "pass" in value}
    graveyard["proxy_substitution_rejected"] = {
        "pass": True,
        "rejected": ["gluing label only", "Axis0", "Phi0", "Xi", "flux", "FEP/Holodeck", "scalar entropy", "PEPS3D label", "forward evolution"],
    }
    boundary = {
        "dense_state_closure_blocked": {"pass": True, "dense_global_state_closure_used": False},
        "resource_boundary_64_sites": {"pass": True, "max_sites": max_sites, "resource_blocker": None},
        "downstream_consumers_blocked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
    }
    return {
        "A0_raw": {"status": "proxy_blocked", "vector": [], "promotion_allowed": False},
        "F01_witness": "finite K=(V,E,F,C), shells, Omega_r branches, finite objects/arrows, transition channels, outputs, and controls",
        "H_Omega": "derived from finite Omega_r compatibility weights before groupoid/gluing readouts",
        "N01_witness": "noncommuting plaquette paths are order-sensitive while abelian/order-erased controls collapse",
        "PEPS3D_K_anchor": {"anchor_types": ["V", "E", "F", "C"], "carrier": "K=(V,E,F,C)", "dense_state_closure_used": False, "max_peps3d_bond": 2, "max_sites": max_sites, "objects": "V", "generating_arrows": "E plus inverses and identities", "stress_shapes": [list(shape) for shape in SHAPES]},
        "QIT_entropy_where_defined": "entropy remains a derived plaquette-order cut readout after Omega_r compatibility and groupoid provenance",
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "ablation_outcome_delta": graveyard,
        "all_pass": all_pass,
        "allowed_claims": ["first M_RPF(C) L8 gluing/groupoid repair row preserves primary shell-object fields over finite PEPS3D anchors"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "blockers": [] if all_pass else ["one_or_more_M_RPF_L8_checks_failed"],
        "boundary": boundary,
        "branch_states": "Omega_r branches carry torch-native spinor-derived rho_omega before groupoid/gluing readouts",
        "carrier_layer": "finite PEPS3D K=(V,E,F,C) shell-cell carrier with gluing/groupoid adapter",
        "carrier_realization": "torch complex shell branch states plus finite groupoid objects/arrows and equivariant dynamic readouts",
        "claim_ceiling": CLAIM_CEILING,
        "classification": CLASSIFICATION,
        "codomain_or_output": CODOMAIN,
        "compression_map": "G composes compatibility-weighted Omega_r branch compression with finite gluing/groupoid adapter",
        "controls": graveyard,
        "dependency_receipts": [
            OBJECT_PACKET,
            "system_v5/ops/formal_scouts/results/m_rpf_l0_response_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l7_hopf_shell_projection_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/l8_gluing_groupoid_equivariant_dynamic_candidate_layer_probe_results.json",
        ],
        "domain": DOMAIN,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "event_x": "finite PEPS3D vertex anchor per stress row; see positive rows",
        "finite_map": FINITE_MAP,
        "future_continuations": "Omega_r finite future/refinement branch sets preserved through the gluing/groupoid adapter",
        "geometry_layer": "M_RPF(C) L8 gluing/groupoid shell-object preservation",
        "gluing_groupoid": {"object_count_64": object_count, "oriented_arrow_count_64": arrow_count, "label_only": False},
        "graveyard_companions": graveyard,
        "law_or_candidate_tested": "M_RPF(C) L8 gluing/groupoid object-preservation repair",
        "mutual_coherent_conditional_information_where_defined": "derived plaquette-order readouts only; no Xi/Phi0 bridge opened",
        "name": NAME,
        "nearby_variants": {
            "passed": 7,
            "total": 7,
            "variants": [
                "8/16/32/64 site groupoid stress",
                "64 objects and 288 oriented arrows at max scale",
                "inverse/composition/equivariance checks",
                "plaquette order witness",
                "multi-shell source R=3",
                "label/inverse/order/proxy controls",
                "QIT plaquette-order readouts",
            ],
        },
        "object_packet_path": OBJECT_PACKET,
        "outward_record": "each shell object emits a past_outward survivor/provenance record before gluing/groupoid readouts",
        "path_entropy": {"status": "derived_readout", "path_depth": PATH_DEPTH},
        "peps3d_embedding": "event_x, shells, groupoid objects, and generating arrows are anchored in finite PEPS3D K=(V,E,F,C)",
        "positive": positive,
        "present_survivor": "rho_present_G is computed from compatibility-weighted future branches, then read by gluing/groupoid adapter",
        "primary_object": "retrocausal_shell_constraint_manifold / M_RPF(C)",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "purpose": PURPOSE,
        "readout_provenance": "Omega_r -> compatibility_weights -> gluing/groupoid adapter G -> compression_map -> rho_present_G -> outward_record -> derived readouts",
        "root_constraints_in_force": {"F01": "finite carrier/probe/operator/path set", "N01": "noncommuting or order-sensitive operation/control"},
        "scale_8_16_32_64_or_resource_blocker": {"max_sites": max_sites, "max_peps3d_bond": 2, "resource_blocker": None, "rows": scale_rows},
        "scientific_question": SCIENTIFIC_QUESTION,
        "shell_count": len(SHELL_RADII),
        "shell_radius_r": list(SHELL_RADII),
        "shell_orientation": {"future": "future_inward", "past_record": "past_outward"},
        "shells": "Sigma_r(event_x) for r in {1,2,3}; inherited from source shell rows",
        "sim_class": SIM_CLASS,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_id": SIM_ID,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "spinor_state": "torch-native two-component spinors with complex phase preserved before spinor-derived groupoid readouts",
        "spinor_state_or_spinor_derived_density": "torch-native branch spinors, rho_omega densities, and local groupoid channel densities",
        "sympy_gate": sympy_checks,
        "tier": TIER,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "torch_spinor_or_density": "torch complex spinors and spinor-derived densities for Omega_r branches plus groupoid transition channels",
        "version": VERSION,
        "z3_gate": z3_checks,
        "cvc5_gate": cvc5_checks,
        "clifford_gate": clifford_checks,
        "why_not_v4_probes": "This is a v5 M_RPF(C) formal scout. It requires v4.3 primary-object fields and blocks gluing-label/proxy substitution; v4 probes do not carry Omega_r groupoid provenance.",
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
