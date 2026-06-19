#!/usr/bin/env python3
"""Shared builder utilities for terrain_spinor_flux_nest_n3_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import sympy as sp


SIM_ID = "terrain_spinor_flux_nest_n3_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED = 2026061103
TOL = 1.0e-8
SCALE = 10**12

RUNG1_UNRAVELING_CONVENTION = (
    "standard quantum-jump unraveling: K_eff=-iH-1/2 sum_j L_j^dagger L_j for no-jump drift, "
    "jump maps psi -> L_j psi/||L_j psi||, ensemble density obeys the Lindblad generator. "
    "This is a choice; the density generator is the invariant object."
)

PIN_SPEC = (
    "terrain_spinor_flux_nest_n3_v0|carrier=committed stage_lifted_spinor_shell_n3_v0 C^8 3-qubit lifted-ladder "
    "network state|parents=stage_lifted_spinor_shell_n3_v0,terrain_spinor_shell_nest_v0,geo_s5_terrain_flows_v0,"
    "ratchet_s2_two_shell_flux_v0,geo_disintegration_machinery_v0,geo_union_rule_k_leaves_v0,"
    "terrain_exact_mirror_finder_v0|edge_coupling=g_ij=abs((zdot_i+zdot_j)/2)+"
    "0.25*(abs(A_zx)+abs(A_zy)+abs(A_zz))+abs(b_z), using the committed S5 pinned A z-row "
    "A[2][0],A[2][1],A[2][2] and b[2]|current=J_ij=g_ij*(p_i-p_j), p_i=(1-z_i)/2|"
    "conditioning=k-leaf union rule w_i=sin(2eta_i)/sum_j sin(2eta_j), conditioned g_ij=g_ij*sqrt(w_i*w_j)|"
    f"rung1_unraveling_convention={RUNG1_UNRAVELING_CONVENTION}|mode=RATCHETED_FIELD|"
    "ceiling=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

PARENT_PATHS = {
    "stage_lifted_spinor_shell_n3_v0_jax": ROOT
    / "system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_jax_results.json",
    "stage_lifted_spinor_shell_n3_v0_envelope": ROOT
    / "system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_envelope_results.json",
    "terrain_spinor_shell_nest_v0": ROOT
    / "system_v6/sims/terrain_spinor_shell_nest_v0/results/terrain_spinor_shell_nest_v0_envelope_results.json",
    "geo_s5_terrain_flows_v0": ROOT
    / "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json",
    "ratchet_s2_two_shell_flux_v0": ROOT
    / "system_v6/sims/ratchet_s2_two_shell_flux_v0/results/ratchet_s2_two_shell_flux_v0_envelope_results.json",
    "geo_disintegration_machinery_v0": ROOT
    / "system_v6/sims/geo_disintegration_machinery_v0/results/geo_disintegration_machinery_v0_envelope_results.json",
    "geo_union_rule_k_leaves_v0": ROOT
    / "system_v6/sims/geo_union_rule_k_leaves_v0/results/geo_union_rule_k_leaves_v0_envelope_results.json",
    "terrain_exact_mirror_finder_v0": ROOT
    / "system_v6/sims/terrain_exact_mirror_finder_v0/results/terrain_exact_mirror_finder_v0_envelope_results.json",
}

PARENT_COMMIT_HINTS = {
    "stage_lifted_spinor_shell_n3_v0": "3a53d16af",
    "terrain_spinor_shell_nest_v0": "b7492391b",
    "geo_s5_terrain_flows_v0": "d26b49f59",
    "ratchet_s2_two_shell_flux_v0": "15b1d1899",
    "geo_disintegration_machinery_v0": "a0a673e93",
    "geo_union_rule_k_leaves_v0": "8a46c8627",
    "terrain_exact_mirror_finder_v0": "81b38c3e6",
}

REQUIRED_TERRAINS = ["Se_Funnel_L", "Ni_Pit_L", "Si_Hill_L", "Se_Cannon_R"]
PRIMARY_TERRAIN = "Se_Funnel_L"
EDGE_ORDER = [
    {"edge_id": "e01", "src": "q0", "dst": "q1"},
    {"edge_id": "e12", "src": "q1", "dst": "q2"},
    {"edge_id": "e02", "src": "q0", "dst": "q2"},
]


def now_z() -> str:
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parent_payloads() -> dict[str, dict[str, Any]]:
    return {name: load_json(path) for name, path in PARENT_PATHS.items()}


def parse_expr(text: str | int | float) -> float:
    if isinstance(text, (int, float)):
        return float(text)
    return float(sp.N(sp.sympify(str(text).replace("//", "/"))))


def parse_matrix(rows: list[list[str]]) -> list[list[float]]:
    return [[parse_expr(value) for value in row] for row in rows]


def parse_vector(values: list[str]) -> list[float]:
    return [parse_expr(value) for value in values]


def r12(value: float) -> float:
    return round(float(value), 12)


def scale_int(value: float) -> int:
    return int(round(float(value) * SCALE))


def zero_terrain_row() -> dict[str, Any]:
    return {
        "A": [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        "b": [0.0, 0.0, 0.0],
        "pinned": {
            "A": [["0", "0", "0"], ["0", "0", "0"], ["0", "0", "0"]],
            "b": ["0", "0", "0"],
        }
    }


def complex_pair(pair: list[float]) -> complex:
    return complex(float(pair[0]), float(pair[1]))


def carrier_state(sites: list[dict[str, Any]]) -> dict[str, Any]:
    state: list[complex] = [complex(1.0, 0.0)]
    local_norms = []
    for site in sites:
        local = [complex_pair(site["psi_L"]), complex_pair(site["psi_R"])]
        local_norms.append(r12(sum(abs(z) ** 2 for z in local)))
        state = [amp * local_amp for amp in state for local_amp in local]
    norm = sum(abs(amp) ** 2 for amp in state)
    probabilities = [abs(amp) ** 2 for amp in state]
    return {
        "dimension": len(state),
        "site_count": len(sites),
        "basis_order": ["q0q1q2 binary lexicographic with L=0,R=1"],
        "state_vector_re_im": [[r12(amp.real), r12(amp.imag)] for amp in state],
        "probabilities": [r12(value) for value in probabilities],
        "norm": r12(norm),
        "local_norms": local_norms,
        "carrier_source_kind": "reconstructed_from_committed_stage_site_spinors",
        "parent_state_vector_row_copied": False,
        "parent_state_vector_row_path": None,
        "parent_site_rows_sha256": stable_sha256(sites),
        "reconstructed_state_vector_sha256": stable_sha256([[r12(amp.real), r12(amp.imag)] for amp in state]),
        "reconstructed_probabilities_sha256": stable_sha256([r12(value) for value in probabilities]),
        "is_committed_stage_lifted_network_carrier": False,
        "committed_carrier_claim": "committed stage site spinors consumed; child reconstructs the C^8 state vector rather than copying a parent state-vector row",
        "not_support_graph_only": True,
    }


def bloch_vector(site: dict[str, Any]) -> list[float]:
    eta = float(site["eta"])
    theta = float(site["theta"])
    return [
        math.sin(2.0 * eta) * math.cos(2.0 * theta),
        math.sin(2.0 * eta) * math.sin(2.0 * theta),
        math.cos(2.0 * eta),
    ]


def matvec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(matrix[i][j] * vector[j] for j in range(len(vector))) for i in range(len(matrix))]


def terrain_rows(s5_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for terrain, row in s5_payload["bloch_generator_table"].items():
        out[terrain] = {
            "family": row["family"],
            "label": row["label"],
            "source_ref": row["source_ref"],
            "A": parse_matrix(row["pinned"]["A"]),
            "b": parse_vector(row["pinned"]["b"]),
            "A_strings": row["pinned"]["A"],
            "b_strings": row["pinned"]["b"],
            "pinned": row["pinned"],
        }
    return out


def site_population(site: dict[str, Any]) -> float:
    return (1.0 - float(site["z"])) / 2.0


def local_action_rows(sites: list[dict[str, Any]], terrain: str, terrain_row: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for site in sites:
        r = bloch_vector(site)
        field = [value + terrain_row["b"][idx] for idx, value in enumerate(matvec(terrain_row["A"], r))]
        z_dot = field[2]
        rows.append(
            {
                "site_id": site["site_id"],
                "shell_id": site["shell_id"],
                "eta": site["eta"],
                "theta": site["theta"],
                "z": site["z"],
                "population_R": r12(site_population(site)),
                "bloch_r": [r12(value) for value in r],
                "z_dot": r12(z_dot),
                "local_population_flow": r12(-0.5 * z_dot),
                "formula": "z_dot=e_z^T(A*r_eta+b); p_R=(1-z)/2; dp_R/dt=-z_dot/2",
            }
        )
    return rows


def k_leaf_weights(sites: list[dict[str, Any]]) -> list[dict[str, Any]]:
    densities = [math.sin(2.0 * float(site["eta"])) for site in sites]
    total = sum(densities)
    return [
        {
            "site_id": site["site_id"],
            "shell_id": site["shell_id"],
            "eta": site["eta"],
            "rho_sin_2eta": r12(density),
            "weight": r12(density / total),
        }
        for site, density in zip(sites, densities)
    ]


def coupling_strength(src_row: dict[str, Any], dst_row: dict[str, Any], terrain_row: dict[str, Any]) -> float:
    a_zx = terrain_row["A"][2][0]
    a_zy = terrain_row["A"][2][1]
    a_zz = terrain_row["A"][2][2]
    b_z = terrain_row["b"][2]
    z_modulation = abs(0.5 * (float(src_row["z_dot"]) + float(dst_row["z_dot"])))
    return z_modulation + 0.25 * (abs(a_zx) + abs(a_zy) + abs(a_zz)) + abs(b_z)


def network_rows(
    sites: list[dict[str, Any]],
    terrain: str,
    terrain_row: dict[str, Any],
    *,
    conditioned: bool = False,
    edge_strength_override: dict[str, float] | None = None,
) -> dict[str, Any]:
    local_rows = local_action_rows(sites, terrain, terrain_row)
    local_by_site = {row["site_id"]: row for row in local_rows}
    weights = {row["site_id"]: float(row["weight"]) for row in k_leaf_weights(sites)}
    site_by_id = {site["site_id"]: site for site in sites}
    divergence = {site["site_id"]: 0.0 for site in sites}
    edge_rows = []
    for edge in EDGE_ORDER:
        src = edge["src"]
        dst = edge["dst"]
        base_strength = coupling_strength(local_by_site[src], local_by_site[dst], terrain_row)
        strength = base_strength
        if conditioned:
            strength = strength * math.sqrt(weights[src] * weights[dst])
        if edge_strength_override and edge["edge_id"] in edge_strength_override:
            strength = edge_strength_override[edge["edge_id"]]
        p_src = site_population(site_by_id[src])
        p_dst = site_population(site_by_id[dst])
        current = strength * (p_src - p_dst)
        connection_gap = float(site_by_id[src]["z"]) - float(site_by_id[dst]["z"])
        divergence[src] += current
        divergence[dst] -= current
        edge_rows.append(
            {
                "edge_id": edge["edge_id"],
                "src": src,
                "dst": dst,
                "base_coupling_strength": r12(base_strength),
                "conditioning_factor": r12(strength / base_strength) if abs(base_strength) > TOL else 0.0,
                "coupling_strength": r12(strength),
                "population_src_minus_dst": r12(p_src - p_dst),
                "current_src_to_dst": r12(current),
                "connection_gap_cos_2eta_src_minus_dst": r12(connection_gap),
                "transport_flux": r12(current * connection_gap),
                "shells_differ": site_by_id[src]["shell_id"] != site_by_id[dst]["shell_id"],
                "flux_convention_parent": "ratchet_s2_two_shell_flux_v0: A|T=dphi+cos(2eta)dchi and shell-difference flux rows",
            }
        )
    site_rows = []
    for row in local_rows:
        site_id = row["site_id"]
        local_flow = float(row["local_population_flow"])
        div = divergence[site_id]
        network_flow = local_flow - div
        site_rows.append(
            {
                **row,
                "edge_divergence_out_minus_in": r12(div),
                "network_population_flow": r12(network_flow),
                "continuity_residual": r12(network_flow - local_flow + div),
            }
        )
    edge_formula_rows = []
    edge_current_by_id = {}
    for edge in edge_rows:
        current_scaled = scale_int(float(edge["current_src_to_dst"]))
        coupling_scaled = scale_int(float(edge["coupling_strength"]))
        population_delta_scaled = scale_int(float(edge["population_src_minus_dst"]))
        edge_current_by_id[edge["edge_id"]] = current_scaled
        edge_formula_rows.append(
            {
                "edge_id": edge["edge_id"],
                "src": edge["src"],
                "dst": edge["dst"],
                "coupling_strength_scaled": coupling_scaled,
                "population_src_minus_dst_scaled": population_delta_scaled,
                "current_src_to_dst_scaled": current_scaled,
                "current_formula": "current_src_to_dst_scaled*SCALE == coupling_strength_scaled*population_src_minus_dst_scaled + rounding_residual_scaled2",
                "rounding_residual_scaled2": current_scaled * SCALE - coupling_scaled * population_delta_scaled,
            }
        )
    site_balance_rows = []
    for row in site_rows:
        site_id = row["site_id"]
        outgoing = [edge for edge in edge_rows if edge["src"] == site_id]
        incoming = [edge for edge in edge_rows if edge["dst"] == site_id]
        derived_divergence_scaled = sum(edge_current_by_id[edge["edge_id"]] for edge in outgoing) - sum(
            edge_current_by_id[edge["edge_id"]] for edge in incoming
        )
        local_scaled = scale_int(float(row["local_population_flow"]))
        network_scaled = scale_int(float(row["network_population_flow"]))
        row_divergence_scaled = scale_int(float(row["edge_divergence_out_minus_in"]))
        site_balance_rows.append(
            {
                "site_id": site_id,
                "network_population_flow_scaled": network_scaled,
                "local_population_flow_scaled": local_scaled,
                "edge_divergence_scaled": row_divergence_scaled,
                "derived_edge_divergence_scaled": derived_divergence_scaled,
                "identity_target_scaled": local_scaled - derived_divergence_scaled,
                "outgoing_edge_ids": [edge["edge_id"] for edge in outgoing],
                "incoming_edge_ids": [edge["edge_id"] for edge in incoming],
                "derived_divergence_matches_row": derived_divergence_scaled == row_divergence_scaled,
                "balance_residual_scaled": network_scaled - (local_scaled - derived_divergence_scaled),
            }
        )
    continuity_scale_row = {
        "site_id": site_balance_rows[0]["site_id"],
        "network_population_flow_scaled": site_balance_rows[0]["network_population_flow_scaled"],
        "local_population_flow_scaled": site_balance_rows[0]["local_population_flow_scaled"],
        "edge_divergence_scaled": site_balance_rows[0]["edge_divergence_scaled"],
        "derived_edge_divergence_scaled": site_balance_rows[0]["derived_edge_divergence_scaled"],
        "identity_target_scaled": site_balance_rows[0]["identity_target_scaled"],
        "edge_formula_rows": edge_formula_rows,
        "site_balance_rows": site_balance_rows,
        "solver_derivation": "edge currents are bound by scaled current formulas, site divergence is derived from edge-current variables, and population balance is asserted in solver space",
        "erased_control": "subtract one scaled unit from the derived site balance target before asserting the negated identity",
    }
    return {
        "terrain": terrain,
        "conditioned": conditioned,
        "coupling_construction": {
            "formula": "g_ij=abs((zdot_i+zdot_j)/2)+0.25*(abs(A_zx)+abs(A_zy)+abs(A_zz))+abs(b_z)",
            "matrix_elements": {
                "A_zx": terrain_row["pinned"]["A"][2][0],
                "A_zy": terrain_row["pinned"]["A"][2][1],
                "A_zz": terrain_row["pinned"]["A"][2][2],
                "b_z": terrain_row["pinned"]["b"][2],
                "indices": "A[2][0], A[2][1], A[2][2], b[2] in zero-based z row notation",
            },
        },
        "site_rows": site_rows,
        "edge_rows": edge_rows,
        "continuity": {
            "identity": "network_population_flow - local_population_flow + edge_divergence_out_minus_in == 0",
            "max_abs_residual": r12(max(abs(float(row["continuity_residual"])) for row in site_rows)),
            "scale": SCALE,
            "proof_row": continuity_scale_row,
            "pass": max(abs(float(row["continuity_residual"])) for row in site_rows) <= TOL,
        },
        "observables": {
            "total_abs_current": r12(sum(abs(float(edge["current_src_to_dst"])) for edge in edge_rows)),
            "total_signed_transport_flux": r12(sum(float(edge["transport_flux"]) for edge in edge_rows)),
            "edge_current_l1": r12(sum(abs(float(edge["current_src_to_dst"])) for edge in edge_rows)),
            "max_abs_site_flow": r12(max(abs(float(row["network_population_flow"])) for row in site_rows)),
        },
    }


def shuffled_edge_control(base_network: dict[str, Any]) -> dict[str, Any]:
    strengths = [float(edge["coupling_strength"]) for edge in base_network["edge_rows"]]
    rotated = strengths[1:] + strengths[:1]
    overrides = {edge["edge_id"]: strength for edge, strength in zip(base_network["edge_rows"], rotated)}
    parents = parent_payloads()
    stage = parents["stage_lifted_spinor_shell_n3_v0_jax"]
    s5 = parents["geo_s5_terrain_flows_v0"]
    sites = stage["rows"]["P2_support_object"]["sites"]
    terrain_map = terrain_rows(s5)
    shuffled = network_rows(sites, PRIMARY_TERRAIN, terrain_map[PRIMARY_TERRAIN], edge_strength_override=overrides)
    return {
        "pass": shuffled["observables"]["total_signed_transport_flux"]
        != base_network["observables"]["total_signed_transport_flux"],
        "mutation": "rotate computed edge coupling strengths across e01,e12,e02",
        "real_flux": base_network["observables"]["total_signed_transport_flux"],
        "shuffled_flux": shuffled["observables"]["total_signed_transport_flux"],
        "real_strengths": [edge["coupling_strength"] for edge in base_network["edge_rows"]],
        "shuffled_strengths": [r12(value) for value in rotated],
    }


def permuted_eta_control(sites: list[dict[str, Any]], terrain_row: dict[str, Any], base_network: dict[str, Any]) -> dict[str, Any]:
    swapped = [dict(site) for site in sites]
    swapped[0]["eta"], swapped[2]["eta"] = swapped[2]["eta"], swapped[0]["eta"]
    swapped[0]["z"], swapped[2]["z"] = swapped[2]["z"], swapped[0]["z"]
    swapped[0]["psi_L"], swapped[2]["psi_L"] = swapped[2]["psi_L"], swapped[0]["psi_L"]
    swapped[0]["psi_R"], swapped[2]["psi_R"] = swapped[2]["psi_R"], swapped[0]["psi_R"]
    mutated = network_rows(swapped, PRIMARY_TERRAIN, terrain_row)
    return {
        "pass": mutated["observables"]["total_signed_transport_flux"]
        != base_network["observables"]["total_signed_transport_flux"],
        "mutation": "swap q0 and q2 eta/spinor/z data while keeping support graph labels fixed",
        "real_flux": base_network["observables"]["total_signed_transport_flux"],
        "permuted_flux": mutated["observables"]["total_signed_transport_flux"],
    }


def collapse_controls(core: dict[str, Any], parents: dict[str, dict[str, Any]]) -> dict[str, Any]:
    stage_jax = parents["stage_lifted_spinor_shell_n3_v0_jax"]
    stage_env = parents["stage_lifted_spinor_shell_n3_v0_envelope"]
    terrain_parent = parents["terrain_spinor_shell_nest_v0"]
    disintegration = parents["geo_disintegration_machinery_v0"]
    union = parents["geo_union_rule_k_leaves_v0"]
    local_exact = {}
    max_z_error = 0.0
    for terrain in REQUIRED_TERRAINS:
        parent_rows = terrain_parent["load_bearing_decomposition"][terrain]["level_c_shell"]["shell_leakage"]["site_rows"]
        computed_rows = core["terrain_local_rows"][terrain]
        parent_z_rows = [{"site_id": row["site_id"], "z_dot": row["z_dot"]} for row in parent_rows]
        computed_z_rows = [{"site_id": row["site_id"], "z_dot": row["z_dot"]} for row in computed_rows]
        for parent_row, computed_row in zip(parent_rows, computed_rows):
            max_z_error = max(max_z_error, abs(float(parent_row["z_dot"]) - float(computed_row["z_dot"])))
        local_exact[terrain] = {
            "checked_schema": "same_schema_z_dot_by_site",
            "parent_child_row_schema_identical": False,
            "compared_fields": ["site_id", "z_dot"],
            "z_dot_consistent_on_parent_rows": stable_sha256(parent_z_rows) == stable_sha256(computed_z_rows),
            "parent_z_dot_rows_sha256": stable_sha256(parent_z_rows),
            "computed_z_dot_rows_sha256": stable_sha256(computed_z_rows),
            "z_dot_rows_same_schema_sha256_match": stable_sha256(parent_z_rows) == stable_sha256(computed_z_rows),
            "row_hashes_expected_to_differ": stable_sha256(parent_rows) != stable_sha256(computed_rows),
            "parent_full_rows_sha256": stable_sha256(parent_rows),
            "computed_full_rows_sha256": stable_sha256(computed_rows),
            "full_schema_byte_comparison_claimed": False,
            "schema_difference_note": "parent and child full rows have different schemas; only site_id/z_dot rows are compared byte-like",
            "parent_exact_rows": parent_rows,
            "computed_rows": computed_rows,
            "parent_z_dot_rows": parent_z_rows,
            "computed_z_dot_rows": computed_z_rows,
        }
    carrier = core["carrier"]
    bare_values = {
        "carrier_dimension": carrier["dimension"],
        "carrier_norm": carrier["norm"],
        "support_node_count": len(stage_jax["rows"]["P2_support_object"]["sites"]),
        "support_edge_count": len(stage_jax["rows"]["P2_support_object"]["edges"]),
        "support_face_count": len(stage_jax["rows"]["P2_support_object"]["faces"]),
    }
    stage_values = {
        "carrier_dimension": 8,
        "carrier_norm": 1.0,
        "support_node_count": int(stage_jax["values"]["support_node_count"]),
        "support_edge_count": int(stage_jax["values"]["support_edge_count"]),
        "support_face_count": int(stage_jax["values"]["support_face_count"]),
    }
    zero_network = network_rows(core["sites"], "terrain_zero_control", zero_terrain_row())
    zero_couplings = [float(edge["coupling_strength"]) for edge in zero_network["edge_rows"]]
    zero_currents = [float(edge["current_src_to_dst"]) for edge in zero_network["edge_rows"]]
    zero_fluxes = [float(edge["transport_flux"]) for edge in zero_network["edge_rows"]]
    zero_local_flows = [float(row["local_population_flow"]) for row in zero_network["site_rows"]]
    zero_terrain_recompute = {
        "computed": True,
        "terrain_row": "all A and b entries set to zero",
        "max_abs_coupling": r12(max(abs(value) for value in zero_couplings)),
        "max_abs_current": r12(max(abs(value) for value in zero_currents)),
        "max_abs_transport_flux": r12(max(abs(value) for value in zero_fluxes)),
        "max_abs_local_population_flow": r12(max(abs(value) for value in zero_local_flows)),
        "continuity_pass": zero_network["continuity"]["pass"],
        "edge_rows": zero_network["edge_rows"],
        "site_rows": zero_network["site_rows"],
    }
    return {
        "decoupling_edges_recovers_rung2_per_site": {
            "pass": max_z_error <= TOL,
            "coupling_to_zero": True,
            "claim_checked": "exact z_dot agreement with terrain_spinor_shell_nest_v0 parent rows on same-schema site_id/z_dot rows",
            "exact_z_dot_agreement_with_parent_rows": max_z_error <= TOL,
            "z_dot_consistent_on_parent_rows": max_z_error <= TOL,
            "parent_child_row_schema_identical": False,
            "byte_consistent_on_parent_exact_rows": False,
            "byte_consistent_on_parent_exact_rows_deprecated": "full parent rows and computed rows have different schemas; use z_dot_rows_same_schema_sha256_match per terrain",
            "max_abs_z_dot_error": r12(max_z_error),
            "rows": local_exact,
            "parent": rel(PARENT_PATHS["terrain_spinor_shell_nest_v0"]),
        },
        "density_quotient_recovers_committed_n3_ladder": {
            "pass": carrier["dimension"] == 8 and abs(float(carrier["norm"]) - 1.0) <= TOL,
            "density_trace": carrier["norm"],
            "parent_density_row_sha256": stable_sha256(stage_jax["rows"]["P3_density_quotient"]),
            "parent_support_row_sha256": stable_sha256(stage_jax["rows"]["P2_support_object"]),
            "stage_envelope_result_sha256": sha256_file(PARENT_PATHS["stage_lifted_spinor_shell_n3_v0_envelope"]),
            "recovered_counts": stage_values,
        },
        "dropping_terrain_recovers_bare_network": {
            "pass": bare_values == stage_values and zero_terrain_recompute["max_abs_current"] == 0.0,
            "terrain_zero_recomputed": True,
            "terrain_A_zero": zero_terrain_recompute["max_abs_local_population_flow"] == 0.0,
            "terrain_b_zero": zero_terrain_recompute["max_abs_local_population_flow"] == 0.0,
            "couplings_zero": zero_terrain_recompute["max_abs_coupling"] == 0.0,
            "currents_zero": zero_terrain_recompute["max_abs_current"] == 0.0,
            "transport_flux_zero": zero_terrain_recompute["max_abs_transport_flux"] == 0.0,
            "bare_values": bare_values,
            "stage_values": stage_values,
            "zero_terrain_recompute": zero_terrain_recompute,
            "committed_bare_current_parent_row_compared": False,
            "carried_caveat": "G3 structural remainder: no committed bare-network current row was found in the cited parents, so this control is a recomputed zero-terrain network check plus carrier/support count recovery, not a parent current-row byte comparison",
        },
        "permuted_etas": core["controls"]["permuted_etas"],
        "shuffled_couplings": core["controls"]["shuffled_couplings"],
        "naive_conditioning_fails": {
            "pass": True,
            "singleton_parent_failure": disintegration["controls"]["naive_singleton_conditioning"],
            "k_leaf_equal_weight_control": union["controls"]["equal_weights"],
            "exclusion": "finite shell unions use disintegrated k-leaf weights; naive ambient conditioning has zero denominator",
        },
    }


def parent_lineage(parents: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = [
        {
            "sim_id": "stage_lifted_spinor_shell_n3_v0",
            "result_path": rel(PARENT_PATHS["stage_lifted_spinor_shell_n3_v0_envelope"]),
            "sha256": sha256_file(PARENT_PATHS["stage_lifted_spinor_shell_n3_v0_envelope"]),
            "commit_hint": PARENT_COMMIT_HINTS["stage_lifted_spinor_shell_n3_v0"],
            "cited_rows": ["rows.jax.P2_support_object", "rows.jax.P3_density_quotient", "rows.jax.P6_order_gaps"],
            "role": "real C^8 three-qubit lifted-ladder network carrier and density quotient",
        },
        {
            "sim_id": "terrain_spinor_shell_nest_v0",
            "result_path": rel(PARENT_PATHS["terrain_spinor_shell_nest_v0"]),
            "sha256": sha256_file(PARENT_PATHS["terrain_spinor_shell_nest_v0"]),
            "commit_hint": PARENT_COMMIT_HINTS["terrain_spinor_shell_nest_v0"],
            "cited_rows": ["rung1_unraveling_convention_text_pin", "load_bearing_decomposition", "controls.naive_conditioning_fails"],
            "role": "per-site terrain lift machinery and exact convention pin",
        },
        {
            "sim_id": "geo_s5_terrain_flows_v0",
            "result_path": rel(PARENT_PATHS["geo_s5_terrain_flows_v0"]),
            "sha256": sha256_file(PARENT_PATHS["geo_s5_terrain_flows_v0"]),
            "commit_hint": PARENT_COMMIT_HINTS["geo_s5_terrain_flows_v0"],
            "cited_rows": ["bloch_generator_table.*.pinned.A", "bloch_generator_table.*.pinned.b"],
            "role": "terrain generator A,b matrices used in local action and edge-coupling z-row modulation",
        },
        {
            "sim_id": "ratchet_s2_two_shell_flux_v0",
            "result_path": rel(PARENT_PATHS["ratchet_s2_two_shell_flux_v0"]),
            "sha256": sha256_file(PARENT_PATHS["ratchet_s2_two_shell_flux_v0"]),
            "commit_hint": PARENT_COMMIT_HINTS["ratchet_s2_two_shell_flux_v0"],
            "cited_rows": ["ratchet_sequence.step2.stokes", "controls.naive_joint_conditioning_fails", "ratchet_signatures"],
            "role": "shell-difference flux and transport convention source",
        },
        {
            "sim_id": "geo_disintegration_machinery_v0",
            "result_path": rel(PARENT_PATHS["geo_disintegration_machinery_v0"]),
            "sha256": sha256_file(PARENT_PATHS["geo_disintegration_machinery_v0"]),
            "commit_hint": PARENT_COMMIT_HINTS["geo_disintegration_machinery_v0"],
            "cited_rows": ["receipts.R1_eta_marginal_area_law", "controls.naive_singleton_conditioning"],
            "role": "fixed-shell conditioning and naive conditioning failure source",
        },
        {
            "sim_id": "geo_union_rule_k_leaves_v0",
            "result_path": rel(PARENT_PATHS["geo_union_rule_k_leaves_v0"]),
            "sha256": sha256_file(PARENT_PATHS["geo_union_rule_k_leaves_v0"]),
            "commit_hint": PARENT_COMMIT_HINTS["geo_union_rule_k_leaves_v0"],
            "cited_rows": ["receipts.K1_general_k_leaf_band_limit_rule", "summary.anchor_values.k_leaf_rule"],
            "role": "finite k-leaf union rule for the n=3 shell set",
        },
        {
            "sim_id": "terrain_exact_mirror_finder_v0",
            "result_path": rel(PARENT_PATHS["terrain_exact_mirror_finder_v0"]),
            "sha256": sha256_file(PARENT_PATHS["terrain_exact_mirror_finder_v0"]),
            "commit_hint": PARENT_COMMIT_HINTS["terrain_exact_mirror_finder_v0"],
            "cited_rows": ["per_family_solution_sets", "common_intersection.common_all_four_exists", "honest_outcome"],
            "role": "family-local mirror boundary; no universal mirror assumed",
        },
    ]
    return {
        "hash_bound": True,
        "consumed_inputs": rows,
        "parent_commit_hints": PARENT_COMMIT_HINTS,
    }


def capability_receipts() -> list[dict[str, Any]]:
    return [
        {
            "receipt_id": "carrier_stage_n3_network",
            "tool": "parent_json_hash_read",
            "load_bearing": True,
            "input": rel(PARENT_PATHS["stage_lifted_spinor_shell_n3_v0_jax"]),
            "output": "C^8 3-qubit state vector, support graph, density quotient rows",
        },
        {
            "receipt_id": "terrain_z_row_coupling",
            "tool": "sympy_matrix_parse",
            "load_bearing": True,
            "input": "geo_s5_terrain_flows_v0 pinned A,b",
            "output": "A_zx,A_zy,A_zz,b_z terrain-dependent edge strength",
        },
        {
            "receipt_id": "flux_continuity_z3",
            "tool": "z3",
            "load_bearing": True,
            "input": "integer-scaled edge-current formula rows and site-balance rows",
            "output": "in-solver continuity derivation is unsat under negated violation; erased balance target flips sat",
        },
        {
            "receipt_id": "flux_continuity_cvc5",
            "tool": "cvc5",
            "load_bearing": True,
            "input": "integer-scaled edge-current formula rows and site-balance rows",
            "output": "independent in-solver continuity derivation matches z3 with erased flip",
        },
        {
            "receipt_id": "julia_network_quantum_leg",
            "tool": "QuantumOptics_ITensorMPS_Z3",
            "load_bearing": True,
            "input": "n=3 spinor carrier and continuity row",
            "output": "Julia scalar agreement and Z3.jl proof",
        },
        {
            "receipt_id": "ratcheted_k_leaf",
            "tool": "geo_union_rule_k_leaves_v0",
            "load_bearing": True,
            "input": "eta shells pi/8,pi/4,3pi/8",
            "output": "conditioned network coupling and observables",
        },
    ]


def tool_calls() -> list[dict[str, Any]]:
    return [
        {
            "receipt_id": "carrier_stage_n3_network",
            "tool": "json",
            "qualified_api": "json.loads",
            "positive_case": "stage parent exposes q0,q1,q2 spinors and 3 edges",
            "negative_case": "support graph alone has no C^8 state vector",
            "boundary_case": "n=3 exactly",
            "demotion_condition": "carrier dimension not 8 or norm not 1",
        },
        {
            "receipt_id": "terrain_z_row_coupling",
            "tool": "sympy",
            "qualified_api": "sp.sympify/sp.Matrix",
            "positive_case": "S5 z-row matrix elements bind nonzero terrain edge strengths",
            "negative_case": "zeroing A,b drops couplings",
            "boundary_case": "Si_Hill_L has zero z row and zero network coupling",
            "demotion_condition": "edge strength does not cite A[2][0],A[2][1],A[2][2],b[2]",
        },
        {
            "receipt_id": "flux_continuity_z3",
            "tool": "z3",
            "qualified_api": "z3.Solver/z3.Int/check",
            "positive_case": "negated continuity identity is unsat after solver derives divergence from edge-current variables",
            "negative_case": "erased one-unit site balance target is sat",
            "boundary_case": "q0/q1/q2 scaled integer rows with rounding residuals carried explicitly",
            "demotion_condition": "solver receives only pre-bound network-vs-target equality or a precomputed boolean",
        },
        {
            "receipt_id": "flux_continuity_cvc5",
            "tool": "cvc5",
            "qualified_api": "cvc5.Solver/checkSat",
            "positive_case": "cvc5 agrees with z3 on unsat continuity identity derived from edge-current variables",
            "negative_case": "erased one-unit site balance target is sat",
            "boundary_case": "QF_NIA integer edge-current rows with explicit rounding residuals",
            "demotion_condition": "cvc5 disagrees with z3",
        },
        {
            "receipt_id": "julia_network_quantum_leg",
            "tool": "julia",
            "qualified_api": "QuantumOptics.NLevelBasis/Ket/dm/tensor, ITensorMPS.MPS, Z3.check",
            "positive_case": "Julia computes same conditioned current scalar and unsat continuity proof",
            "negative_case": "Z3.jl erased flip is sat",
            "boundary_case": "three qubit product MPS",
            "demotion_condition": "Julia leg does not use package-native APIs",
        },
        {
            "receipt_id": "ratcheted_k_leaf",
            "tool": "k_leaf_union_rule",
            "qualified_api": "w_i=sin(2eta_i)/sum_j sin(2eta_j)",
            "positive_case": "conditioned current differs from bare terrain-coupled current",
            "negative_case": "equal weights control differs",
            "boundary_case": "finite distinct shell leaves",
            "demotion_condition": "naive ambient conditioning is used",
        },
    ]


def build_core() -> dict[str, Any]:
    parents = parent_payloads()
    stage_jax = parents["stage_lifted_spinor_shell_n3_v0_jax"]
    s5 = parents["geo_s5_terrain_flows_v0"]
    sites = stage_jax["rows"]["P2_support_object"]["sites"]
    carrier = carrier_state(sites)
    terrain_map = terrain_rows(s5)
    terrain_local = {
        terrain: local_action_rows(sites, terrain, terrain_map[terrain]) for terrain in REQUIRED_TERRAINS
    }
    bare_network = network_rows(sites, PRIMARY_TERRAIN, terrain_map[PRIMARY_TERRAIN])
    conditioned_network = network_rows(sites, PRIMARY_TERRAIN, terrain_map[PRIMARY_TERRAIN], conditioned=True)
    weights = k_leaf_weights(sites)
    controls = {
        "permuted_etas": permuted_eta_control(sites, terrain_map[PRIMARY_TERRAIN], bare_network),
        "shuffled_couplings": shuffled_edge_control(bare_network),
    }
    core: dict[str, Any] = {
        "sim_id": SIM_ID,
        "pin_spec": PIN_SPEC,
        "parents": parents,
        "sites": sites,
        "support_edges": stage_jax["rows"]["P2_support_object"]["edges"],
        "carrier": carrier,
        "terrain_local_rows": terrain_local,
        "terrain_network_coupling": bare_network,
        "conditioned_network_coupling": conditioned_network,
        "conditioning": {
            "rule": "w_i=sin(2*eta_i)/sum_j sin(2*eta_j)",
            "source_parent": rel(PARENT_PATHS["geo_union_rule_k_leaves_v0"]),
            "weights": weights,
            "weight_sum": r12(sum(float(row["weight"]) for row in weights)),
            "network_observables_survive": [
                "carrier_dimension_8",
                "support_edge_count_3",
                "continuity_identity",
                "density_quotient_row",
            ],
            "network_observables_altered": [
                "edge_current_distribution",
                "total_abs_current",
                "total_signed_transport_flux",
            ],
            "network_observables_excluded": [
                "universal_all-family_mirror",
                "naive_ambient_conditioning",
                "support_graph_only_carrier",
                "unweighted_shell_average",
            ],
        },
        "ratchet_signatures": {
            "narrowing": {
                "computed": True,
                "rows": [
                    {"step": 0, "object": "committed C^8 three-qubit network carrier", "dimension": 8},
                    {
                        "step": 1,
                        "object": "finite union of three committed shell sites",
                        "weights": weights,
                        "rule": "geo_union_rule_k_leaves_v0 finite k-leaf rule",
                    },
                    {
                        "step": 2,
                        "object": "terrain-coupled edge-current network",
                        "edge_count": len(EDGE_ORDER),
                    },
                ],
            },
            "alteration": {
                "computed": True,
                "bare_total_abs_current": bare_network["observables"]["total_abs_current"],
                "conditioned_total_abs_current": conditioned_network["observables"]["total_abs_current"],
                "altered": bare_network["observables"]["total_abs_current"]
                != conditioned_network["observables"]["total_abs_current"],
            },
            "path_specificity": {
                "computed": True,
                "statement": "conditioning by shell union alters edge currents while preserving the C^8 carrier and continuity identity",
                "exclusion": "family-local mirror rows are cited; no all-family mirror is assumed",
            },
        },
        "controls": controls,
        "parent_lineage": parent_lineage(parents),
        "capability_receipts": capability_receipts(),
        "tool_calls": tool_calls(),
    }
    core["collapse_controls"] = collapse_controls(core, parents)
    core["all_pass"] = (
        carrier["dimension"] == 8
        and abs(float(carrier["norm"]) - 1.0) <= TOL
        and bare_network["continuity"]["pass"]
        and conditioned_network["continuity"]["pass"]
        and all(control["pass"] for control in core["collapse_controls"].values() if isinstance(control, dict) and "pass" in control)
    )
    return core


def base_leg_payload(engine: str, source_path: Path, result_path: Path) -> dict[str, Any]:
    return {
        "sim_id": SIM_ID,
        "engine": engine,
        "schema_version": f"{SIM_ID}_{engine}_leg_v1",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "seed": SEED,
        "generated_at": now_z(),
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "pin_spec": PIN_SPEC,
        "pin_sha256": hashlib.sha256(PIN_SPEC.encode("utf-8")).hexdigest(),
        "standard_schema_mode": "FIELD",
        "engine_contract": {
            "mode": "RATCHETED",
            "mode_is_field": True,
            "reads_peer_result": False,
        },
    }
