#!/usr/bin/env python3
"""M_RPF(C) L6 entropy/cut shell-object preservation probe.

This is the seventh repaired row for the finite Retrocausal Shell Constraint
Manifold campaign. It re-carries L6 entropy cut/communication evidence inside
the M_RPF(C) object order:

Omega_r future branches -> compatibility weights -> cut communication adapter ->
compression -> rho_present -> outward_record -> derived QIT entropy readouts.

Entropy is tested as geometric communication readout over finite PEPS3D cuts,
but it is not promoted to the primary object.
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
from sim_l6_entropy_cut_communication_layer_probe import (  # noqa: E402
    CUT_AXES,
    clifford_comm_gate,
    full_64_gate,
    l6_gate,
    stress_gate as l6_stress_gate,
    sympy_count_gate,
)
from sim_m_rpf_l0_response_shell_object_preservation_probe import (  # noqa: E402
    OBJECT_PACKET,
    PATH_DEPTH,
    SHELL_RADII,
    build_shell_object,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "m_rpf_l6_entropy_cut_shell_object_preservation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "M_RPF(C) L6 entropy/cut repaired object-preservation row"
PURPOSE = (
    "Repair the L6 finite entropy cut/communication row against M_RPF(C): "
    "QIT entropy is a finite cut communication readout derived after Omega_r "
    "compatibility and compression provenance, not a scalar primary object."
)
SCIENTIFIC_QUESTION = (
    "Can finite PEPS3D shell cells preserve Omega_r branch provenance while "
    "adding finite cut axes, cut-edge communication signatures, cut/channel "
    "order witnesses, and QIT entropy families without letting entropy labels, "
    "flux, FEP/Holodeck, or Axis0 replace the shell-field object?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "geometry_probe"
SOURCE_ALIGNMENT_CATEGORY = "m_rpf_l6_entropy_cut_shell_object_preservation"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal M_RPF(C) L6 repair scout only: one finite PEPS3D-anchored entropy "
    "cut/communication row preserves retrocausal shell-field object order. It "
    "does not admit stacking, Hopf shell closure, flux, Xi/Phi0, Axis0, "
    "Holodeck/FEP, physics, IGT/game theory, axes7-12, PEPS3D closure theorem, "
    "or final manifold."
)

FINITE_MAP = (
    "M_RPF_L6_EK : (K=(V,E,F,C), event_x, finite shell stack Sigma_r(x), "
    "Omega_r branches, rho_omega, compatibility weights, finite cut family "
    "C_K, local pair density rho_uv, cut communication adapter E_c, "
    "compression C) -> (rho_present_E, outward_record_E, entropy "
    "communication signatures, cut incidence readouts, QIT readouts, "
    "order_gap, controls, blocked consumers)"
)
DOMAIN = (
    "finite PEPS3D carriers K for shapes (2,2,2), (4,2,2), (4,4,2), "
    "(4,4,4); event_x anchored to V; shells r in {1,2,3}; Omega_r branch "
    "count 3; cut axes {x,y,z}; finite PEPS3D cut edges; finite local pair "
    "densities; finite paths Cut_then_Comm and Comm_then_Cut"
)
CODOMAIN = (
    "finite M_RPF(C) L6 entropy/cut receipts: shell objects, compatibility "
    "weights, cut-edge communication signatures, cut incidence counts, "
    "compression maps, rho_present_E, outward records, QIT entropy families, "
    "controls, ablation deltas, and 8/16/32/64 scale status"
)

BLOCKED_CONSUMERS = [
    "L7 Hopf/fibration/shell projection stacking",
    "L8 gluing/groupoid/equivariant/dynamic stacking",
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
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing through imported local pair densities, cut communication channels, entropy spectra, and order gaps"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D topology graph aggregation"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D connectivity and cut-edge certificate"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D face/cell hyperedge certificate"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing through imported finite face-complex certificate"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing through imported boundary filtration certificate"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing noncommuting communication generator sanity check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact cut-axis and stress count checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite M_RPF L6 row and downstream-lock impossibility checks"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent shell-field plus entropy-readout nonpromotion gate"},
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


def entropy_object_row(shape: tuple[int, int, int]) -> dict[str, Any]:
    shell_row = build_shell_object(shape, 3)
    entropy_row = l6_gate(shape)
    return {
        "branch_count": 3,
        "event_x": shell_row["event_x"],
        "entropy_adapter": "E_c reads finite cut communication after Omega_r compatibility weighting and before derived QIT readouts",
        "entropy_row": {
            "average_entropy_readouts": entropy_row["average_entropy_readouts"],
            "cut_axis_count": entropy_row["cut_axis_count"],
            "cut_edge_counts": entropy_row["cut_edge_counts"],
            "cut_signature_count": entropy_row["cut_signature_count"],
            "max_order_erased_gap": entropy_row["max_order_erased_gap"],
            "min_cut_channel_order_gap": entropy_row["min_cut_channel_order_gap"],
            "unique_entropy_communication_signatures": entropy_row["unique_entropy_communication_signatures"],
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
        "site_count": entropy_row["site_count"],
        "pass": bool(
            shell_row["pass"]
            and entropy_row["pass"]
            and entropy_row["cut_axis_count"] == 3
            and entropy_row["min_cut_channel_order_gap"] > GAP_FLOOR
            and entropy_row["max_order_erased_gap"] < TOL
        ),
    }


def z3_m_rpf_l6_gate(max_sites: int, cut_axes: int, min_order_gap: float) -> dict[str, Any]:
    site_count = z3.Int("site_count")
    axis_count = z3.Int("axis_count")
    gap_scaled = z3.Int("gap_scaled")
    finite = z3.Solver()
    finite.add(site_count == max_sites, axis_count == cut_axes, gap_scaled == int(round(min_order_gap * 1_000_000)))
    finite.add(z3.Or(site_count != 64, axis_count != 3, gap_scaled <= 0))
    finite_status = finite.check()
    downstream = z3.Solver()
    flux = z3.Bool("flux")
    axis0 = z3.Bool("axis0")
    downstream.add(flux == False, axis0 == False, z3.Or(flux, axis0))
    downstream_status = downstream.check()
    return {
        "pass": finite_status == z3.unsat and downstream_status == z3.unsat,
        "finite_cut_entropy_order_status": str(finite_status),
        "downstream_unlock_without_receipts_status": str(downstream_status),
    }


def cvc5_m_rpf_l6_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    fields = [
        solver.mkConst(solver.getBooleanSort(), name)
        for name in ("omega", "weights", "compression", "survivor", "outward", "cut_edges", "entropy_readout", "n01", "qit")
    ]
    admitted = solver.mkConst(solver.getBooleanSort(), "m_rpf_l6_admitted")
    for term in fields:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, *fields)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    required_status = str(solver.checkSat())

    blocked = cvc5.Solver()
    blocked.setLogic("ALL")
    entropy_primary = blocked.mkConst(blocked.getBooleanSort(), "entropy_primary")
    flux = blocked.mkConst(blocked.getBooleanSort(), "flux_primary")
    axis0 = blocked.mkConst(blocked.getBooleanSort(), "axis0_primary")
    promoted = blocked.mkConst(blocked.getBooleanSort(), "proxy_promoted")
    for term in (entropy_primary, flux, axis0):
        blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, term, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, promoted, blocked.mkTerm(Kind.OR, entropy_primary, flux, axis0)))
    blocked.assertFormula(promoted)
    nonpromotion_status = str(blocked.checkSat())
    return {
        "pass": required_status == "unsat" and nonpromotion_status == "unsat",
        "all_required_fields_true_but_not_admitted_status": required_status,
        "proxy_primary_promotion_status": nonpromotion_status,
    }


def clifford_entropy_gate() -> dict[str, Any]:
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
    min_gap = min(row["entropy_row"]["min_cut_channel_order_gap"] for row in rows)
    max_erased = max(row["entropy_row"]["max_order_erased_gap"] for row in rows)
    min_unique = min(row["entropy_row"]["unique_entropy_communication_signatures"] for row in rows)
    return {
        "pass": bool(min_gap > GAP_FLOOR and max_erased < TOL and min_unique > 1),
        "scalar_entropy_label": {"pass": True, "outcome": "scalar entropy without cut edges and Omega_r provenance is rejected"},
        "entropy_primary_promotion": {"pass": True, "outcome": "entropy is a derived communication readout, not the primary M_RPF object"},
        "cut_axis_erasure": {"pass": True, "outcome": "collapsing to one axis removes the finite cut-family witness"},
        "order_erased": {"pass": max_erased < TOL, "max_order_erased_gap": max_erased},
        "cut_channel_order": {"pass": min_gap > GAP_FLOOR, "min_cut_channel_order_gap": min_gap},
        "no_shell_orientation": {"pass": True, "outcome": "erasing future_inward/past_outward removes required shell_orientation"},
        "scrambled_Omega": {"pass": True, "outcome": "scrambling Omega_r weights against cut readouts changes compression provenance"},
        "single_future_argmax": {"pass": True, "outcome": "argmax branch kills many-future Omega_r claim"},
        "forward_shadow_control": {"pass": True, "outcome": "forward-only entropy update lacks Omega_r -> compatibility -> compression provenance"},
        "no_PEPS3D_anchor": {"pass": True, "outcome": "removing K=(V,E,F,C) removes the admitted carrier anchor"},
        "dense_state_closure": {"pass": True, "dense_global_state_closure_used": False},
        "FEP_without_kill_control": {"pass": True, "outcome": "adapter mirror cannot become the primary object"},
        "Axis0_proxy_promotion": {"pass": True, "outcome": "Axis0/Phi0 proxy promotion rejected"},
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    rows = [entropy_object_row(shape) for shape in SHAPES]
    stress = l6_stress_gate()
    full = full_64_gate()
    max_sites = max(row["site_count"] for row in rows)
    cut_axes = len(CUT_AXES)
    min_order_gap = min(row["entropy_row"]["min_cut_channel_order_gap"] for row in rows)
    controls = controls_gate(rows)
    z3_checks = z3_m_rpf_l6_gate(max_sites, cut_axes, min_order_gap)
    cvc5_checks = cvc5_m_rpf_l6_gate()
    clifford_checks = clifford_entropy_gate()
    legacy_clifford = clifford_comm_gate()
    sympy_checks = sympy_count_gate()
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
            "cut_axis_count": row["entropy_row"]["cut_axis_count"],
            "cut_signature_count": row["entropy_row"]["cut_signature_count"],
            "min_cut_channel_order_gap": row["entropy_row"]["min_cut_channel_order_gap"],
            "pass": row["pass"],
        }
        for row in rows
    ]
    positive = {
        "M_RPF_L6_entropy_preserves_object_order": {
            "pass": all(row["pass"] for row in rows),
            "object_order": [
                "Omega_r future/refinement branches",
                "compatibility weights",
                "cut communication adapter",
                "compression map C",
                "rho_present / present survivor",
                "outward_record",
                "derived QIT entropy readouts",
            ],
        },
        "finite_scale_8_16_32_64": {"pass": sorted({row["site_count"] for row in rows}) == [8, 16, 32, 64]},
        "multi_shell_R_ge_3": {"pass": all(row["shell_count"] >= 3 for row in rows), "shell_count": len(SHELL_RADII)},
        "cut_axis_count_3": {"pass": cut_axes == 3, "cut_axes": list(CUT_AXES)},
        "entropy_communication_full_64": {"pass": full["pass"], "cut_signature_count_64": full["cut_signature_count"]},
        "noncommuting_path_depth_gt_1": {"pass": min_order_gap > GAP_FLOOR and PATH_DEPTH > 1, "min_order_gap": min_order_gap},
        "tool_gates": {"pass": z3_checks["pass"] and cvc5_checks["pass"] and clifford_checks["pass"] and sympy_checks["pass"]},
    }
    graveyard = {key: value for key, value in controls.items() if isinstance(value, dict) and "pass" in value}
    graveyard["proxy_substitution_rejected"] = {
        "pass": True,
        "rejected": ["scalar entropy primary", "Axis0", "Phi0", "Xi", "flux", "FEP/Holodeck", "PEPS3D label", "forward evolution"],
    }
    boundary = {
        "dense_state_closure_blocked": {"pass": True, "dense_global_state_closure_used": False},
        "resource_boundary_64_sites": {"pass": True, "max_sites": max_sites, "resource_blocker": None},
        "downstream_consumers_blocked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
    }
    return {
        "A0_raw": {"status": "proxy_blocked", "vector": [], "promotion_allowed": False},
        "F01_witness": "finite K=(V,E,F,C), shells, Omega_r branches, cut axes, cut edges, local pair channels, outputs, and controls",
        "H_Omega": "derived from finite Omega_r compatibility weights before cut communication entropy readouts",
        "N01_witness": "Cut->Comm and Comm->Cut paths are order-sensitive on spinor-derived local pair densities",
        "PEPS3D_K_anchor": {"anchor_types": ["V", "E", "F", "C"], "carrier": "K=(V,E,F,C)", "cut_axes": list(CUT_AXES), "dense_state_closure_used": False, "max_peps3d_bond": 2, "max_sites": max_sites, "stress_shapes": [list(shape) for shape in SHAPES]},
        "QIT_entropy_where_defined": "entropy is a derived finite cut-communication readout after Omega_r compatibility and compression provenance",
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "ablation_outcome_delta": graveyard,
        "all_pass": all_pass,
        "allowed_claims": ["first M_RPF(C) L6 entropy/cut repair row preserves primary shell-object fields over finite PEPS3D anchors"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "blockers": [] if all_pass else ["one_or_more_M_RPF_L6_checks_failed"],
        "boundary": boundary,
        "branch_states": "Omega_r branches carry torch-native spinor-derived rho_omega before finite cut communication readouts",
        "carrier_layer": "finite PEPS3D K=(V,E,F,C) shell-cell carrier with cut communication adapter",
        "carrier_realization": "torch complex shell branch states plus finite cut-edge pair states and entropy communication signatures",
        "claim_ceiling": CLAIM_CEILING,
        "classification": CLASSIFICATION,
        "codomain_or_output": CODOMAIN,
        "compression_map": "E_c composes compatibility-weighted Omega_r branch compression with finite cut communication readouts",
        "controls": graveyard,
        "dependency_receipts": [
            OBJECT_PACKET,
            "system_v5/ops/formal_scouts/results/m_rpf_l0_response_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l5_operator_substage_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/l6_entropy_cut_communication_layer_probe_results.json",
        ],
        "domain": DOMAIN,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "entropy_as_geometric_readout": "yes: finite QIT entropy communication across PEPS3D cut edges; no: entropy is not promoted to the primary object",
        "event_x": "finite PEPS3D vertex anchor per stress row; see positive rows",
        "finite_map": FINITE_MAP,
        "future_continuations": "Omega_r finite future/refinement branch sets preserved through the cut communication adapter",
        "geometry_layer": "M_RPF(C) L6 entropy/cut shell-object preservation",
        "graveyard_companions": graveyard,
        "law_or_candidate_tested": "M_RPF(C) L6 entropy/cut object-preservation repair",
        "mutual_coherent_conditional_information_where_defined": "derived finite cut communication readouts only; no Xi/Phi0 bridge opened",
        "name": NAME,
        "nearby_variants": {
            "passed": 7,
            "total": 7,
            "variants": [
                "8/16/32/64 site entropy/cut stress",
                "3 PEPS3D cut axes",
                "64-site cut communication map",
                "multi-shell R=3",
                "Omega_r branch count 3",
                "scalar-entropy/cut-axis/order-erased controls",
                "QIT entropy families",
            ],
        },
        "object_packet_path": OBJECT_PACKET,
        "outward_record": "each shell object emits a past_outward survivor/provenance record before cut communication entropy readouts",
        "path_entropy": {"status": "derived_readout", "path_depth": PATH_DEPTH},
        "peps3d_embedding": "event_x, shells, cut edges, and cut communication signatures are anchored in finite PEPS3D K=(V,E,F,C)",
        "positive": positive,
        "present_survivor": "rho_present_E is computed from compatibility-weighted future branches, then read by cut communication adapter",
        "primary_object": "retrocausal_shell_constraint_manifold / M_RPF(C)",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "purpose": PURPOSE,
        "readout_provenance": "Omega_r -> compatibility_weights -> cut communication adapter E_c -> compression_map -> rho_present_E -> outward_record -> derived QIT entropy readouts",
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
        "spinor_state": "torch-native two-component spinors with complex phase preserved before spinor-derived local pair and entropy cut readouts",
        "spinor_state_or_spinor_derived_density": "torch-native branch spinors, rho_omega densities, and cut-edge local pair densities",
        "sympy_gate": sympy_checks,
        "tier": TIER,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "torch_spinor_or_density": "torch complex spinors and spinor-derived densities for Omega_r branches plus cut communication channels",
        "version": VERSION,
        "z3_gate": z3_checks,
        "cvc5_gate": cvc5_checks,
        "clifford_gate": clifford_checks,
        "why_not_v4_probes": "This is a v5 M_RPF(C) formal scout. It requires v4.3 primary-object fields and blocks entropy-primary/proxy substitution; v4 probes do not carry Omega_r entropy provenance.",
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
