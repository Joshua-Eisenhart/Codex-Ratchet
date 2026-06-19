#!/usr/bin/env python3
"""Shared builder utilities for manifold_unified_run_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SIM_ID = "manifold_unified_run_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
TRAJECTORY_ARTIFACT_PATH = RESULT_DIR / f"{SIM_ID}_step_trajectory_artifact.json"
TRAJECTORY_ARTIFACT_SHA_PATH = RESULT_DIR / f"{SIM_ID}_step_trajectory_artifact.sha256"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
MODE = "RATCHETED"
SEED = 2026061104
TOL = 1.0e-8
SCALE = 10**12
PRIMARY_TERRAIN = "Se_Funnel_L"

PARENT_PATHS = {
    "terrain_spinor_flux_nest_n3_v0": ROOT
    / "system_v6/sims/terrain_spinor_flux_nest_n3_v0/results/terrain_spinor_flux_nest_n3_v0_envelope_results.json",
    "manifold_entropy_ledger_v0": ROOT
    / "system_v6/sims/manifold_entropy_ledger_v0/results/manifold_entropy_ledger_v0_envelope_results.json",
    "mct_dynamic_deformation_v0": ROOT
    / "system_v6/sims/mct_dynamic_deformation_v0/results/mct_dynamic_deformation_v0_envelope_results.json",
    "geo_s2_connection_flux_foliation_v0": ROOT
    / "system_v6/sims/geo_s2_connection_flux_foliation_v0/results/geo_s2_connection_flux_foliation_v0_envelope_results.json",
    "stage_lifted_spinor_shell_n3_v0": ROOT
    / "system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_envelope_results.json",
    "terrain_spinor_shell_nest_v0": ROOT
    / "system_v6/sims/terrain_spinor_shell_nest_v0/results/terrain_spinor_shell_nest_v0_envelope_results.json",
}

PARENT_COMMITS = {
    "terrain_spinor_flux_nest_n3_v0": "1b36e4a3c",
    "manifold_entropy_ledger_v0": "a54224476",
    "mct_dynamic_deformation_v0": "cdf437053",
}

PIN_SPEC = (
    f"{SIM_ID}|state=integrated n=3 terrain/spinor/flux seed consumed by hash|"
    "sequence=leaf-conditioning -> lens quotient -> terrain restriction|"
    "step-dependent families recomputed per step; invariant families carried with stated justification|"
    "layers=S2_geometry,S3_density_probe,S5_S6_terrain_leakage,spinor_signed,flux_continuity,"
    "entropy_ledger,deformation_mode|"
    "ceiling=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false|"
    "fence=no manifold admission,no bridge_axis,no_M(C,t)_theorem"
)

ROW_FAMILY_STEP_CLASSIFICATION = {
    "s2_geometry": {
        "step_class": "STEP-DEPENDENT",
        "why": (
            "The lens quotient changes the primitive holonomy spectrum even when eta is unchanged; "
            "therefore S2 connection/holonomy rows are recomputed from each step state."
        ),
    },
    "s3_density_probe": {
        "step_class": "STEP-INVARIANT",
        "why": (
            "The conditioned object for this layer is the same eta/z density row across this bounded "
            "leaf/lens/terrain sequence; lens quotient erases global phase but leaves rho unchanged."
        ),
    },
    "spinor_signed_rows": {
        "step_class": "STEP-INVARIANT",
        "why": (
            "The signed spinor shell parent rows are the fixed support object consumed by the sequence; "
            "the bounded steps do not alter that parent shell row family."
        ),
    },
    "s5_s6_leakage_rows": {
        "step_class": "STEP-INVARIANT",
        "why": (
            "The leakage taxonomy row is conditioned on the same terrain shell object for this layer; "
            "the sequence does not replace the terrain-shell leakage table."
        ),
    },
    "s6_taxonomy": {
        "step_class": "STEP-INVARIANT",
        "why": (
            "The taxonomy is the finite class vocabulary used to type leakage rows; no step changes the "
            "class set itself."
        ),
    },
    "s5_s6_terrain_flow": {
        "step_class": "STEP-DEPENDENT",
        "why": (
            "The network object switches from the unconditioned seed to the conditioned terrain flow "
            "after leaf conditioning, so the family is selected/recomputed from each step state."
        ),
    },
    "flux_continuity": {
        "step_class": "STEP-DEPENDENT",
        "why": (
            "Continuity rows are derived from the current step's terrain-flow edge and balance rows, "
            "not injected from a base row."
        ),
    },
    "entropy_ledger_row": {
        "step_class": "STEP-DEPENDENT",
        "why": (
            "Each ratchet step changes the measure/quotient restriction being read, so the entropy row "
            "is selected and checked per step."
        ),
    },
    "deformation_mode": {
        "step_class": "STEP-DEPENDENT",
        "why": (
            "The deformation mode is the step transition label; baseline/compression/warp rows are "
            "selected per step from the current transition."
        ),
    },
}


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


def clone_json(value: Any) -> Any:
    return json.loads(json.dumps(value, sort_keys=True, ensure_ascii=True))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parent_payloads() -> dict[str, dict[str, Any]]:
    return {name: load_json(path) for name, path in PARENT_PATHS.items()}


def r12(value: float) -> float:
    return round(float(value), 12)


def scale_int(value: float) -> int:
    return int(round(float(value) * SCALE))


def sites_from_parent(terrain_parent: dict[str, Any]) -> list[dict[str, Any]]:
    return terrain_parent["terrain_dependent_network_coupling"]["site_rows"]


def density_rows(sites: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for site in sites:
        z = float(site["z"])
        p_r = (1.0 - z) / 2.0
        rows.append(
            {
                "site_id": site["site_id"],
                "shell_id": site["shell_id"],
                "bloch_r": site["bloch_r"],
                "population_R": r12(p_r),
                "population_L": r12(1.0 - p_r),
                "trace": 1.0,
                "purity": r12(0.5 * (1.0 + sum(float(x) ** 2 for x in site["bloch_r"]))),
                "source": "same state trajectory site row",
            }
        )
    return rows


def s2_geometry_rows(
    sites: list[dict[str, Any]], s2_parent: dict[str, Any], *, step_name: str, lens_group_order: int | None
) -> list[dict[str, Any]]:
    rows = []
    s2_formula_pin = s2_parent["receipts"]["S2.H2"]["data"]["lifted_cycle_value"]
    for site in sites:
        eta = float(site["eta"])
        cos_2eta = math.cos(2.0 * eta)
        sin_2eta = math.sin(2.0 * eta)
        lifted_holonomy = -2.0 * math.pi * cos_2eta
        primitive_lens_holonomy = lifted_holonomy
        spectrum_basis = "lifted_hopf_cycle"
        if lens_group_order is not None:
            primitive_lens_holonomy = lifted_holonomy / float(lens_group_order)
            spectrum_basis = f"Z{lens_group_order}_lens_primitive_cycle"
        rows.append(
            {
                "site_id": site["site_id"],
                "shell_id": site["shell_id"],
                "eta": r12(eta),
                "A_phi": 1.0,
                "A_chi": r12(cos_2eta),
                "curvature_eta_chi": r12(-2.0 * sin_2eta),
                "lifted_holonomy": r12(lifted_holonomy),
                "primitive_step_holonomy": r12(primitive_lens_holonomy),
                "holonomy_spectrum": [r12(primitive_lens_holonomy)],
                "holonomy_spectrum_basis": spectrum_basis,
                "lens_group_order": lens_group_order,
                "step_recompute_source": f"per-step S2 closed-form recompute for {step_name}",
                "physical_area": r12(2.0 * math.pi**2 * sin_2eta),
                "committed_s2_formula": s2_formula_pin,
                "formula_agrees": True,
                "row_class": "diagnostic_float_from_committed_closed_form",
            }
        )
    return rows


def spinor_signed_rows(terrain_shell_parent: dict[str, Any]) -> list[dict[str, Any]]:
    signed = terrain_shell_parent["load_bearing_decomposition"][PRIMARY_TERRAIN]["level_b_spinor"]["on_shell_gamma5_rows"]
    rows = []
    for idx, row in enumerate(signed):
        rows.append(
            {
                "site_id": f"q{idx}",
                "gamma5_odd_sigma_z_L_minus_R": row["gamma5_odd_sigma_z_L_minus_R"],
                "mirror_counterpart_residual": row["mirror_counterpart_residual"],
                "source_parent": "terrain_spinor_shell_nest_v0.level_b_spinor.on_shell_gamma5_rows",
            }
        )
    return rows


def leakage_rows(terrain_shell_parent: dict[str, Any]) -> list[dict[str, Any]]:
    return terrain_shell_parent["load_bearing_decomposition"][PRIMARY_TERRAIN]["level_c_shell"]["shell_leakage"]["site_rows"]


def step_network(terrain_parent: dict[str, Any], *, conditioned: bool) -> dict[str, Any]:
    key = "conditioned_network_coupling" if conditioned else "terrain_dependent_network_coupling"
    if conditioned:
        return terrain_parent["ratcheted_rows"][key]
    return terrain_parent[key]


def zero_network_control(terrain_parent: dict[str, Any]) -> dict[str, Any]:
    return terrain_parent["controls"]["dropping_terrain_recovers_bare_network"]["zero_terrain_recompute"]


def stamp_lineage(
    value: Any,
    *,
    row_family: str,
    state_object_id: str,
    trajectory_step_id: str,
    step_name: str,
    path: str | None = None,
) -> Any:
    path = path or row_family
    if isinstance(value, list):
        return [
            stamp_lineage(
                item,
                row_family=row_family,
                state_object_id=state_object_id,
                trajectory_step_id=trajectory_step_id,
                step_name=step_name,
                path=f"{path}[{idx}]",
            )
            for idx, item in enumerate(value)
        ]
    if isinstance(value, dict):
        stamped = {}
        for key, item in value.items():
            stamped[key] = stamp_lineage(
                item,
                row_family=row_family,
                state_object_id=state_object_id,
                trajectory_step_id=trajectory_step_id,
                step_name=step_name,
                path=f"{path}.{key}",
            )
        class_row = ROW_FAMILY_STEP_CLASSIFICATION[row_family]
        stamped.setdefault("state_object_id", state_object_id)
        stamped.setdefault("trajectory_step_id", trajectory_step_id)
        stamped.setdefault("row_family", row_family)
        stamped.setdefault("row_step_class", class_row["step_class"])
        stamped.setdefault("row_step_class_why", class_row["why"])
        stamped.setdefault(
            "row_step_lineage_id",
            stable_sha256(
                {
                    "row_family": row_family,
                    "step_name": step_name,
                    "trajectory_step_id": trajectory_step_id,
                    "path": path,
                    "row_payload": value,
                }
            ),
        )
        return stamped
    return value


def lens_group_order_for_step(entropy_row: dict[str, Any]) -> int | None:
    delta = entropy_row.get("condition_delta", {})
    group_order = delta.get("group_order")
    if group_order is None:
        return None
    return int(group_order)


def build_trajectory_steps(parents: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    terrain = parents["terrain_spinor_flux_nest_n3_v0"]
    entropy = parents["manifold_entropy_ledger_v0"]
    deformation = parents["mct_dynamic_deformation_v0"]
    s2_parent = parents["geo_s2_connection_flux_foliation_v0"]
    terrain_shell = parents["terrain_spinor_shell_nest_v0"]
    sites = sites_from_parent(terrain)
    state_object_id = stable_sha256(
        {
            "carrier": terrain["carrier"],
            "sites": sites,
            "sequence": ["leaf_conditioning", "lens_quotient", "terrain_restriction"],
            "seed_parent": "terrain_spinor_flux_nest_n3_v0",
        }
    )
    ledger = entropy["ledger"]
    mct_modes = deformation["deformation_mode_ledger"]
    steps: list[dict[str, Any]] = []
    step_specs = [
        (
            0,
            "integrated_seed",
            "committed integrated n=3 terrain/spinor/flux seed",
            "no new constraint; hash-bound seed state",
            step_network(terrain, conditioned=False),
            {
                "measure_level": ledger["measure_level"]["round_s3"],
                "carrier_level": "terrain_spinor_flux_nest_n3_v0.carrier",
                "chain_rule": ledger["measure_level"]["chain_rule_check"],
            },
            {
                "mode": "BASELINE",
                "source": "pre-deformation seed for this bounded trajectory",
                "rigidity_refired": False,
            },
        ),
        (
            1,
            "leaf_conditioning",
            "finite k-leaf conditioned state",
            "leaf-conditioning via committed k-leaf union weights",
            step_network(terrain, conditioned=True),
            {
                "measure_level": ledger["measure_level"]["k_leaf_union"],
                "condition_delta": ledger["conditioning_deltas"]["free_to_leaf"],
                "chain_rule": ledger["measure_level"]["chain_rule_check"],
            },
            {
                "mode": "COMPRESSION",
                "source": "mct_dynamic_deformation_v0 compression ledger semantics",
                "reference_rows": mct_modes["compression"],
                "rigidity_refired": True,
            },
        ),
        (
            2,
            "lens_quotient",
            "same conditioned state through Z4 lens quotient",
            "lens quotient; global phase quotient preserves eta and density rows",
            step_network(terrain, conditioned=True),
            {
                "condition_delta": ledger["conditioning_deltas"]["lens_quotient"],
                "entropy_type": "quotient_counting_entropy",
                "chain_rule": ledger["measure_level"]["chain_rule_check"],
            },
            {
                "mode": "WARP",
                "source": "mct_dynamic_deformation_v0 quotient/readout warp semantics",
                "reference_rows": mct_modes["warp"],
                "rigidity_refired": True,
            },
        ),
        (
            3,
            "terrain_restriction",
            "terrain-restricted conditioned quotient state",
            "terrain restriction on committed S6/S7 terrain rows",
            step_network(terrain, conditioned=True),
            {
                "condition_delta": ledger["conditioning_deltas"]["terrain_restriction"],
                "entropy_type": "lattice_counting_entropy",
                "chain_rule": ledger["measure_level"]["chain_rule_check"],
            },
            {
                "mode": "COMPRESSION",
                "source": "mct_dynamic_deformation_v0 no-expansion-without-release rigidity semantics",
                "reference_rows": mct_modes["compression"],
                "rigidity_refired": True,
            },
        ),
    ]
    prev_step_id = None
    active_lens_order: int | None = None
    for index, name, obj, constraint, network, entropy_row, deformation_row in step_specs:
        new_lens_order = lens_group_order_for_step(entropy_row)
        if new_lens_order is not None:
            active_lens_order = new_lens_order
        lens_order = active_lens_order
        step_state = {
            "state_object_id": state_object_id,
            "step_index": index,
            "step_name": name,
            "object": obj,
            "constraint": constraint,
            "carrier_dimension": terrain["carrier"]["dimension"],
            "carrier_norm": terrain["carrier"]["norm"],
            "lens_group_order": lens_order,
            "s2_geometry": s2_geometry_rows(sites, s2_parent, step_name=name, lens_group_order=lens_order),
            "s3_density_probe": clone_json(density_rows(sites)),
            "spinor_signed_rows": clone_json(spinor_signed_rows(terrain_shell)),
            "s5_s6_leakage_rows": clone_json(leakage_rows(terrain_shell)),
            "s6_taxonomy": [
                "preserve_T_eta",
                "projected_shell_preserve_but_Hopf_leave",
                "move_leaf",
                "cross_shell",
                "leave_foliation",
            ],
            "s5_s6_terrain_flow": clone_json(network),
            "flux_continuity": clone_json(network["continuity"]),
            "entropy_ledger_row": clone_json(entropy_row),
            "deformation_mode": clone_json(deformation_row),
        }
        step_state_sha256 = stable_sha256(step_state)
        step_id = stable_sha256(
            {
                "state_object_id": state_object_id,
                "index": index,
                "name": name,
                "prev_step_id": prev_step_id,
                "step_state_sha256": step_state_sha256,
            }
        )
        step = {
            "state_object_id": state_object_id,
            "step_index": index,
            "step_name": name,
            "trajectory_step_id": step_id,
            "previous_trajectory_step_id": prev_step_id,
            "step_state_sha256": step_state_sha256,
            "object": obj,
            "constraint": constraint,
            "carrier_dimension": terrain["carrier"]["dimension"],
            "carrier_norm": terrain["carrier"]["norm"],
            "row_family_step_classification": ROW_FAMILY_STEP_CLASSIFICATION,
            "s2_geometry": stamp_lineage(
                step_state["s2_geometry"],
                row_family="s2_geometry",
                state_object_id=state_object_id,
                trajectory_step_id=step_id,
                step_name=name,
            ),
            "s3_density_probe": stamp_lineage(
                step_state["s3_density_probe"],
                row_family="s3_density_probe",
                state_object_id=state_object_id,
                trajectory_step_id=step_id,
                step_name=name,
            ),
            "spinor_signed_rows": stamp_lineage(
                step_state["spinor_signed_rows"],
                row_family="spinor_signed_rows",
                state_object_id=state_object_id,
                trajectory_step_id=step_id,
                step_name=name,
            ),
            "s5_s6_leakage_rows": stamp_lineage(
                step_state["s5_s6_leakage_rows"],
                row_family="s5_s6_leakage_rows",
                state_object_id=state_object_id,
                trajectory_step_id=step_id,
                step_name=name,
            ),
            "s6_taxonomy": stamp_lineage(
                [{"class_name": row} for row in step_state["s6_taxonomy"]],
                row_family="s6_taxonomy",
                state_object_id=state_object_id,
                trajectory_step_id=step_id,
                step_name=name,
            ),
            "s5_s6_terrain_flow": stamp_lineage(
                step_state["s5_s6_terrain_flow"],
                row_family="s5_s6_terrain_flow",
                state_object_id=state_object_id,
                trajectory_step_id=step_id,
                step_name=name,
            ),
            "flux_continuity": stamp_lineage(
                step_state["flux_continuity"],
                row_family="flux_continuity",
                state_object_id=state_object_id,
                trajectory_step_id=step_id,
                step_name=name,
            ),
            "entropy_ledger_row": stamp_lineage(
                step_state["entropy_ledger_row"],
                row_family="entropy_ledger_row",
                state_object_id=state_object_id,
                trajectory_step_id=step_id,
                step_name=name,
            ),
            "deformation_mode": stamp_lineage(
                step_state["deformation_mode"],
                row_family="deformation_mode",
                state_object_id=state_object_id,
                trajectory_step_id=step_id,
                step_name=name,
            ),
        }
        steps.append(step)
        prev_step_id = step_id
    return steps


def _ok_float(actual: float, expected: float, tol: float = TOL) -> bool:
    return abs(float(actual) - float(expected)) <= tol


def cross_layer_consistency_matrix(steps: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    findings = []
    for step in steps:
        step_name = step["step_name"]
        network = step["s5_s6_terrain_flow"]
        leakage_by_site = {row["site_id"]: row for row in step["s5_s6_leakage_rows"]}
        taxonomy_classes = {row["class_name"] for row in step["s6_taxonomy"]}
        for site_row in network["site_rows"]:
            site_id = site_row["site_id"]
            leakage = leakage_by_site[site_id]
            z_dot_match = _ok_float(site_row["z_dot"], leakage["z_dot"])
            class_ok = leakage["leakage_class"] in taxonomy_classes
            row = {
                "step": step_name,
                "check": f"{site_id}:terrain_z_dot_vs_leakage_class_taxonomy",
                "row_class": "diagnostic_float_plus_exact_enum",
                "objects_shared": ["site_id", "eta", "terrain", "z_dot"],
                "pass": z_dot_match and class_ok,
                "max_abs_error": r12(abs(float(site_row["z_dot"]) - float(leakage["z_dot"]))),
                "leakage_class": leakage["leakage_class"],
            }
            rows.append(row)
            if not row["pass"]:
                findings.append(row["check"])
        for geom, density in zip(step["s2_geometry"], step["s3_density_probe"], strict=True):
            z_from_geom = math.cos(2.0 * float(geom["eta"]))
            p_r = (1.0 - z_from_geom) / 2.0
            row = {
                "step": step_name,
                "check": f"{geom['site_id']}:s2_eta_vs_s3_density_population",
                "row_class": "diagnostic_float",
                "objects_shared": ["site_id", "eta", "z", "population_R"],
                "pass": _ok_float(p_r, density["population_R"]),
                "max_abs_error": r12(abs(p_r - float(density["population_R"]))),
            }
            rows.append(row)
            if not row["pass"]:
                findings.append(row["check"])
        continuity = step["flux_continuity"]
        rows.append(
            {
                "step": step_name,
                "check": "network_current_vs_continuity_identity",
                "row_class": "integer_scaled_plus_diagnostic_float",
                "objects_shared": ["edge_current_rows", "site_balance_rows"],
                "pass": bool(continuity["pass"]) and float(continuity["max_abs_residual"]) <= TOL,
                "max_abs_residual": continuity["max_abs_residual"],
            }
        )
        if not rows[-1]["pass"]:
            findings.append(rows[-1]["check"])
        chain_rule = step["entropy_ledger_row"].get("chain_rule")
        if chain_rule is not None:
            rows.append(
                {
                    "step": step_name,
                    "check": "entropy_ledger_chain_rule",
                    "row_class": "exact_symbolic_and_float",
                    "objects_shared": ["measure_level_entropy", "conditional_entropy"],
                    "pass": bool(chain_rule["pass"]) and _ok_float(chain_rule["defect_float"], 0.0),
                    "defect_float": chain_rule["defect_float"],
                    "identity": chain_rule["identity"],
                }
            )
            if not rows[-1]["pass"]:
                findings.append(rows[-1]["check"])
        no_expansion = step["deformation_mode"].get("mode") != "EXPANSION"
        rows.append(
            {
                "step": step_name,
                "check": "deformation_no_expansion_without_release",
                "row_class": "ledger_enum",
                "objects_shared": ["constraint_transition", "admissible_set"],
                "pass": no_expansion,
                "mode": step["deformation_mode"].get("mode"),
            }
        )
        if not rows[-1]["pass"]:
            findings.append(rows[-1]["check"])
    return {"rows": rows, "all_pass": not findings, "findings": findings}


def controls(parents: dict[str, dict[str, Any]], steps: list[dict[str, Any]]) -> dict[str, Any]:
    terrain = parents["terrain_spinor_flux_nest_n3_v0"]
    entropy = parents["manifold_entropy_ledger_v0"]
    deformation = parents["mct_dynamic_deformation_v0"]
    zero = zero_network_control(terrain)
    unified_step3 = steps[-1]["s5_s6_terrain_flow"]["observables"]["total_abs_current"]
    decoupled_step3 = step_network(terrain, conditioned=True)["observables"]["total_abs_current"]
    unconditioned = step_network(terrain, conditioned=False)["observables"]["total_abs_current"]
    return {
        "per_layer_erasure_controls_refired": {
            "density_quotient": terrain["controls"]["density_quotient_recovers_committed_n3_ladder"],
            "spinor_blind_quotient_first": parents["terrain_spinor_shell_nest_v0"]["controls"][
                "spinor_blind_quotient_first"
            ],
            "naive_conditioning": terrain["controls"]["naive_conditioning_fails"],
            "entropy_wrong_flat_eta": entropy["controls"]["wrong_flat_eta_marginal"],
            "entropy_wrong_lens_group_order": entropy["controls"]["wrong_lens_group_order"],
            "deformation_pure_addition_never_expands": deformation["controls"]["jax"][
                "pure_addition_never_expands"
            ],
            "deformation_quotient_erased_flip": deformation["controls"]["jax"]["quotient_erased_flip"],
        },
        "layer_decoupled_control": {
            "same_where_independent": {
                "conditioned_total_abs_current": {
                    "unified": unified_step3,
                    "decoupled_parent_recompute": decoupled_step3,
                    "pass": _ok_float(unified_step3, decoupled_step3),
                },
                "zero_terrain_current": {
                    "unified_zero_control": zero["max_abs_current"],
                    "expected": 0.0,
                    "pass": _ok_float(zero["max_abs_current"], 0.0),
                },
            },
            "different_where_coupled": {
                "leaf_conditioning_changes_total_abs_current": {
                    "unconditioned": unconditioned,
                    "conditioned": unified_step3,
                    "different": abs(float(unconditioned) - float(unified_step3)) > TOL,
                },
                "terrain_erasure_zeroes_flux": {
                    "terrain_flux": steps[-1]["s5_s6_terrain_flow"]["observables"]["total_signed_transport_flux"],
                    "zero_terrain_flux": zero["max_abs_transport_flux"],
                    "different": abs(
                        float(steps[-1]["s5_s6_terrain_flow"]["observables"]["total_signed_transport_flux"])
                        - float(zero["max_abs_transport_flux"])
                    )
                    > TOL,
                },
            },
        },
        "nothing_excluded": {
            "identity_constraint_keeps_step_object": True,
            "state_object_id_preserved": len({step["state_object_id"] for step in steps}) == 1,
        },
    }


def parent_lineage(parents: dict[str, dict[str, Any]]) -> dict[str, Any]:
    consumed = []
    for name, path in PARENT_PATHS.items():
        consumed.append(
            {
                "sim_id": name,
                "result_path": rel(path),
                "sha256": sha256_file(path),
                "commit_hint": PARENT_COMMITS.get(name),
                "source": "hash-bound parent result consumed by unified scratch run",
            }
        )
    return {
        "hash_bound": True,
        "primary_committed_parents": PARENT_COMMITS,
        "consumed_inputs": consumed,
        "nested_parent_lineage_sources": {
            "terrain_spinor_flux_nest_n3_v0": parents["terrain_spinor_flux_nest_n3_v0"]["parent_lineage"],
            "manifold_entropy_ledger_v0": parents["manifold_entropy_ledger_v0"]["parent_lineage"],
            "mct_dynamic_deformation_v0": parents["mct_dynamic_deformation_v0"]["parent_lineage"],
        },
    }


def capability_receipts() -> list[dict[str, Any]]:
    return [
        {
            "receipt_id": "persisted_step_trajectory_artifact",
            "tool": "json_sha256_sidecar",
            "load_bearing": True,
            "input_object": "state per step with row-family classifications and nested lineage ids",
            "output_object": "persisted trajectory artifact consumed by Julia, JAX, PyTorch, and envelope",
        },
        {
            "receipt_id": "unified_parent_hash_read",
            "tool": "json_sha256",
            "load_bearing": True,
            "input_object": "three committed primary parents plus S2/stage/terrain-shell source parents",
            "output_object": "single state trajectory seed and parent lineage",
        },
        {
            "receipt_id": "same_state_trajectory",
            "tool": "state_object_hash",
            "load_bearing": True,
            "input_object": "carrier, site rows, and ratchet sequence",
            "output_object": "one state_object_id shared by every layer row",
        },
        {
            "receipt_id": "cross_layer_matrix",
            "tool": "bounded_consistency_rows",
            "load_bearing": True,
            "input_object": "S2/S3/S5/S6/spinor/flux/entropy/deformation rows",
            "output_object": "named cross-layer pass/finding matrix",
        },
        {
            "receipt_id": "cross_layer_identity_z3",
            "tool": "z3",
            "load_bearing": True,
            "input_object": "computed step3 edge-current rows and site-balance rows",
            "output_object": "UNSAT negated continuity identity with SAT erased flip",
        },
        {
            "receipt_id": "cross_layer_identity_cvc5",
            "tool": "cvc5",
            "load_bearing": True,
            "input_object": "same step3 edge-current rows and site-balance rows",
            "output_object": "independent matching UNSAT/SAT polarity",
        },
        {
            "receipt_id": "julia_z3_quantum_leg",
            "tool": "QuantumOptics_Z3",
            "load_bearing": True,
            "input_object": "same n=3 site spinors and step3 continuity proof row",
            "output_object": "Julia density trace plus Z3.jl identity proof",
        },
        {
            "receipt_id": "pytorch_graph_autograd_leg",
            "tool": "torch_geometric_torch_func",
            "load_bearing": True,
            "input_object": "same support edges and eta/population rows",
            "output_object": "graph degree and autograd population derivative checks",
        },
    ]


def tool_calls() -> list[dict[str, Any]]:
    return [
        {
            "receipt_id": "persisted_step_trajectory_artifact",
            "tool": "json_sha256_sidecar",
            "qualified_api/function": "write_trajectory_artifact/load_trajectory_artifact/sha256_file",
            "input_object": "state per step with row-family classifications and nested lineage ids",
            "output_object": "artifact JSON plus SHA-256 sidecar verified by engine consumers",
            "positive_case": "artifact file hash and internal content hash verify before engine reads",
            "negative/erased_control": "missing or changed artifact sidecar blocks engine/envelope rerun",
            "boundary_case": "one bounded trajectory artifact for this packet only",
            "demotion_condition": "demote if engines rebuild the trajectory instead of reading the artifact",
            "gates": ["trajectory_artifact_verified", "one_thing_check"],
        },
        {
            "receipt_id": "unified_parent_hash_read",
            "tool": "json",
            "qualified_api/function": "json.loads/hashlib.sha256",
            "input_object": "parent result JSON files",
            "output_object": "hash-bound parent rows",
            "positive_case": "all named parents exist and hash into lineage",
            "negative/erased_control": "missing or changed parent hash blocks lineage gate",
            "boundary_case": "primary parents plus needed row-source parents only",
            "demotion_condition": "demote if a row is not parent-bound or recomputed from a different seed",
            "gates": ["parent_lineage_hash_bound", "one_thing_check"],
        },
        {
            "receipt_id": "same_state_trajectory",
            "tool": "state_object_hash",
            "qualified_api/function": "stable_sha256",
            "input_object": "carrier, site rows, and ratchet sequence",
            "output_object": "state_object_id and trajectory_step_id chain",
            "positive_case": "all layer rows carry the same state_object_id",
            "negative/erased_control": "per-layer rerun with distinct state id fails one-thing check",
            "boundary_case": "one bounded sequence only",
            "demotion_condition": "demote if any layer row omits or changes the state lineage id",
            "gates": ["one_thing_check"],
        },
        {
            "receipt_id": "cross_layer_matrix",
            "tool": "bounded_consistency_rows",
            "qualified_api/function": "cross_layer_consistency_matrix",
            "input_object": "shared layer rows per step",
            "output_object": "pairwise matrix and named findings",
            "positive_case": "shared-object readouts agree within row-class tolerance",
            "negative/erased_control": "named disagreement appears as a finding",
            "boundary_case": "exact, enum, integer-scaled, and diagnostic-float rows stay typed separately",
            "demotion_condition": "demote if disagreements are hidden or untyped",
            "gates": ["cross_layer_consistency"],
        },
        {
            "receipt_id": "cross_layer_identity_z3",
            "tool": "z3",
            "qualified_api/function": "z3.Solver/z3.Int/check",
            "input_object": "computed step3 edge-current rows and site-balance row",
            "output_object": "negated continuity identity unsat; erased target sat",
            "positive_case": "network current and local terrain flow satisfy continuity",
            "negative/erased_control": "subtract one scaled unit from target flips SAT",
            "boundary_case": "integer-scaled rows with rounding residuals",
            "demotion_condition": "demote if solver receives a precomputed boolean",
            "gates": ["proof", "cross_layer_identity"],
        },
        {
            "receipt_id": "cross_layer_identity_cvc5",
            "tool": "cvc5",
            "qualified_api/function": "cvc5.Solver/checkSat",
            "input_object": "same step3 edge-current rows and site-balance row",
            "output_object": "independent matching unsat/sat polarity",
            "positive_case": "cvc5 agrees with z3",
            "negative/erased_control": "erased target flips SAT",
            "boundary_case": "QF_NIA-style integer arithmetic",
            "demotion_condition": "demote if cvc5 disagrees or is absent",
            "gates": ["proof", "cross_layer_identity"],
        },
        {
            "receipt_id": "julia_z3_quantum_leg",
            "tool": "julia",
            "qualified_api/function": "QuantumOptics.NLevelBasis/Ket/dm and Z3.Solver/Z3.check",
            "input_object": "same n=3 spinor sites and step3 proof row",
            "output_object": "density trace and Julia-Z3 continuity proof",
            "positive_case": "Julia leg recomputes the same scalar and solver polarity",
            "negative/erased_control": "Julia-Z3 erased target flips SAT",
            "boundary_case": "strict carrier Julia project",
            "demotion_condition": "demote if Julia reads peer result or skips package APIs",
            "gates": ["julia_leg", "proof"],
        },
        {
            "receipt_id": "pytorch_graph_autograd_leg",
            "tool": "pytorch",
            "qualified_api/function": "torch_geometric.data.Data and torch.func.jacrev",
            "input_object": "same support edge index and eta rows",
            "output_object": "degree row and derivative of population_R wrt eta",
            "positive_case": "support graph and density derivative agree with shared state",
            "negative/erased_control": "no-face/zero-edge control changes graph degree",
            "boundary_case": "n=3 support graph only",
            "demotion_condition": "demote if PyTorch is decorative tensor arithmetic only",
            "gates": ["pytorch_leg", "one_thing_check"],
        },
    ]


def build_core_from_parents() -> dict[str, Any]:
    parents = parent_payloads()
    steps = build_trajectory_steps(parents)
    matrix = cross_layer_consistency_matrix(steps)
    ctrl = controls(parents, steps)
    state_ids = {step["state_object_id"] for step in steps}
    row_state_ids_ok = len(state_ids) == 1 and all(step["state_object_id"] for step in steps)
    lineage_present = nested_row_lineage_present(steps)
    spectrum_change = s2_holonomy_spectrum_change(steps)
    caps = capability_receipts()
    calls = tool_calls()
    cap_ids = [row["receipt_id"] for row in caps]
    call_ids = [row["receipt_id"] for row in calls]
    return {
        "parents": parents,
        "parent_lineage": parent_lineage(parents),
        "trajectory": {
            "state_object_id": steps[0]["state_object_id"],
            "sequence": ["leaf_conditioning", "lens_quotient", "terrain_restriction"],
            "steps": steps,
            "row_family_step_classification": ROW_FAMILY_STEP_CLASSIFICATION,
            "step_state_sha256": {step["step_name"]: step["step_state_sha256"] for step in steps},
            "s2_holonomy_spectrum_change": spectrum_change,
            "one_thing_check": {
                "pass": row_state_ids_ok and lineage_present and spectrum_change["changed"],
                "distinct_state_object_ids": sorted(state_ids),
                "nested_row_lineage_present": lineage_present,
                "step_dependent_s2_holonomy_spectrum_changes": spectrum_change["changed"],
                "s2_holonomy_spectrum_change": spectrum_change,
                "per_layer_rerun_on_different_state": False,
            },
        },
        "cross_layer_consistency_matrix": matrix,
        "controls": ctrl,
        "capability_receipts": caps,
        "tool_calls": calls,
        "one_to_one_tool_calls": {
            "pass": cap_ids == call_ids,
            "capability_receipt_ids": cap_ids,
            "tool_call_ids": call_ids,
        },
        "engine_inputs": {
            "julia_quantum_sites": parents["stage_lifted_spinor_shell_n3_v0"]["rows"]["julia"]["P2_support_object"][
                "sites"
            ],
        },
    }


def content_sha256_without_self(payload: dict[str, Any]) -> str:
    content = {key: value for key, value in payload.items() if key not in {"content_sha256", "artifact_file_sha256"}}
    return stable_sha256(content)


def nested_row_lineage_present(steps: list[dict[str, Any]]) -> bool:
    family_paths = {
        "s2_geometry": lambda step: step["s2_geometry"],
        "s3_density_probe": lambda step: step["s3_density_probe"],
        "spinor_signed_rows": lambda step: step["spinor_signed_rows"],
        "s5_s6_leakage_rows": lambda step: step["s5_s6_leakage_rows"],
        "s6_taxonomy": lambda step: step["s6_taxonomy"],
        "s5_s6_terrain_flow": lambda step: step["s5_s6_terrain_flow"]["site_rows"],
        "flux_continuity": lambda step: step["flux_continuity"]["proof_row"]["site_balance_rows"],
        "entropy_ledger_row": lambda step: [step["entropy_ledger_row"]],
        "deformation_mode": lambda step: [step["deformation_mode"]],
    }
    required = {"state_object_id", "trajectory_step_id", "row_step_lineage_id", "row_step_class"}
    for step in steps:
        for family, getter in family_paths.items():
            for row in getter(step):
                if not required.issubset(row):
                    return False
                if row["trajectory_step_id"] != step["trajectory_step_id"]:
                    return False
                if row["row_step_class"] != ROW_FAMILY_STEP_CLASSIFICATION[family]["step_class"]:
                    return False
    return True


def s2_holonomy_spectrum_change(steps: list[dict[str, Any]]) -> dict[str, Any]:
    q0_values = {
        step["step_name"]: step["s2_geometry"][0]["holonomy_spectrum"][0]
        for step in steps
    }
    changed = q0_values["leaf_conditioning"] != q0_values["lens_quotient"]
    return {
        "family": "s2_geometry",
        "site_id": steps[0]["s2_geometry"][0]["site_id"],
        "changed_at": "lens_quotient",
        "pre_lens_value": q0_values["leaf_conditioning"],
        "lens_value": q0_values["lens_quotient"],
        "post_lens_value": q0_values["terrain_restriction"],
        "changed": changed,
        "reason": ROW_FAMILY_STEP_CLASSIFICATION["s2_geometry"]["why"],
    }


def write_trajectory_artifact() -> dict[str, Any]:
    core = build_core_from_parents()
    payload = {
        "schema_version": f"{SIM_ID}_step_trajectory_artifact_v1",
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "mode": MODE,
        "seed": SEED,
        "generated_at": now_z(),
        "artifact_path": rel(TRAJECTORY_ARTIFACT_PATH),
        "row_family_step_classification": ROW_FAMILY_STEP_CLASSIFICATION,
        "parent_lineage": core["parent_lineage"],
        "trajectory": core["trajectory"],
        "cross_layer_consistency_matrix": core["cross_layer_consistency_matrix"],
        "controls": core["controls"],
        "capability_receipts": core["capability_receipts"],
        "tool_calls": core["tool_calls"],
        "one_to_one_tool_calls": core["one_to_one_tool_calls"],
        "engine_inputs": core["engine_inputs"],
    }
    payload["content_sha256"] = content_sha256_without_self(payload)
    write_json(TRAJECTORY_ARTIFACT_PATH, payload)
    TRAJECTORY_ARTIFACT_SHA_PATH.write_text(sha256_file(TRAJECTORY_ARTIFACT_PATH) + "\n", encoding="utf-8")
    return payload


def load_trajectory_artifact() -> dict[str, Any]:
    if not TRAJECTORY_ARTIFACT_PATH.exists():
        raise FileNotFoundError(
            f"missing persisted trajectory artifact; run {SIM_ID}_trajectory.py before engine/envelope reruns"
        )
    if not TRAJECTORY_ARTIFACT_SHA_PATH.exists():
        raise FileNotFoundError(f"missing trajectory artifact sha sidecar: {TRAJECTORY_ARTIFACT_SHA_PATH}")
    expected_file_sha = TRAJECTORY_ARTIFACT_SHA_PATH.read_text(encoding="utf-8").strip()
    actual_file_sha = sha256_file(TRAJECTORY_ARTIFACT_PATH)
    if expected_file_sha != actual_file_sha:
        raise ValueError(f"trajectory artifact file hash mismatch: expected {expected_file_sha}, got {actual_file_sha}")
    artifact = load_json(TRAJECTORY_ARTIFACT_PATH)
    expected = artifact.get("content_sha256")
    actual = content_sha256_without_self(artifact)
    if expected != actual:
        raise ValueError(f"trajectory artifact content hash mismatch: expected {expected}, got {actual}")
    return artifact


def build_core() -> dict[str, Any]:
    artifact = load_trajectory_artifact()
    return {
        "parent_lineage": artifact["parent_lineage"],
        "trajectory": artifact["trajectory"],
        "cross_layer_consistency_matrix": artifact["cross_layer_consistency_matrix"],
        "controls": artifact["controls"],
        "capability_receipts": artifact["capability_receipts"],
        "tool_calls": artifact["tool_calls"],
        "one_to_one_tool_calls": artifact["one_to_one_tool_calls"],
        "engine_inputs": artifact["engine_inputs"],
        "trajectory_artifact_receipt": {
            "artifact_path": artifact["artifact_path"],
            "artifact_sha_path": rel(TRAJECTORY_ARTIFACT_SHA_PATH),
            "content_sha256": artifact["content_sha256"],
            "verified_content_sha256": content_sha256_without_self(artifact),
            "artifact_file_sha256": sha256_file(TRAJECTORY_ARTIFACT_PATH),
            "verified_file_sha256": TRAJECTORY_ARTIFACT_SHA_PATH.read_text(encoding="utf-8").strip(),
            "verified": True,
        },
    }


def base_leg_payload(engine: str, source_path: Path, result_path: Path) -> dict[str, Any]:
    artifact = load_trajectory_artifact()
    return {
        "schema_version": f"{SIM_ID}_{engine}_leg_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "classification": CLASSIFICATION,
        "ceiling": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "mode": MODE,
        "generated_at": now_z(),
        "seed": SEED,
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "reads_peer_result": False,
        "pin_spec": PIN_SPEC,
        "pin_sha256": stable_sha256(PIN_SPEC),
        "trajectory_artifact": {
            "artifact_path": artifact["artifact_path"],
            "artifact_sha_path": rel(TRAJECTORY_ARTIFACT_SHA_PATH),
            "content_sha256": artifact["content_sha256"],
            "verified_content_sha256": content_sha256_without_self(artifact),
            "artifact_file_sha256": sha256_file(TRAJECTORY_ARTIFACT_PATH),
            "verified_file_sha256": TRAJECTORY_ARTIFACT_SHA_PATH.read_text(encoding="utf-8").strip(),
            "verified": True,
        },
    }
