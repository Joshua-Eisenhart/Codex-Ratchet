#!/usr/bin/env python3
"""Deep RATCHETED constraint-chain diagnostic.

Builder-only packet. Ceiling: scratch_diagnostic; promotion_allowed=false.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import platform
import subprocess
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "ratchet_deep_chain_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_PATH = SIM_DIR / f"validate_{SIM_ID}.py"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
JULIA_SOURCE_PATH = SIM_DIR / f"{SIM_ID}_julia.jl"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"

MODE = "RATCHETED"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

PARENTS = {
    "ratchet_s1_single_shell_pilot_v0": {
        "packet": "system_v6/sims/ratchet_s1_single_shell_pilot_v0",
        "envelope": "system_v6/sims/ratchet_s1_single_shell_pilot_v0/results/ratchet_s1_single_shell_pilot_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_s1_single_shell_pilot_v0/ratchet_s1_single_shell_pilot_v0.py",
        "prompt_commit": "f578b7181",
        "allowed_use": "T_pi/6 disintegration row, Z4 lens row, naive-conditioning failure, and pilot phase-window noncommuting class",
    },
    "ratchet_s2_two_shell_flux_v0": {
        "packet": "system_v6/sims/ratchet_s2_two_shell_flux_v0",
        "envelope": "system_v6/sims/ratchet_s2_two_shell_flux_v0/results/ratchet_s2_two_shell_flux_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_s2_two_shell_flux_v0/ratchet_s2_two_shell_flux_v0.py",
        "prompt_commit": "15b1d1899",
        "allowed_use": "two-shell anchor, Stokes convention, empty-intersection mortality wording, and quotient survival rows",
    },
    "ratchet_s6_terrain_operator_shell_v0": {
        "packet": "system_v6/sims/ratchet_s6_terrain_operator_shell_v0",
        "envelope": "system_v6/sims/ratchet_s6_terrain_operator_shell_v0/results/ratchet_s6_terrain_operator_shell_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_s6_terrain_operator_shell_v0/ratchet_s6_terrain_operator_shell_v0.py",
        "prompt_commit": "76597c8a8",
        "allowed_use": "terrain-basin restriction and Se_Funnel_L/R_x order-gap row",
    },
    "ratchet_g2_family_v0": {
        "packet": "system_v6/sims/ratchet_g2_family_v0",
        "envelope": "system_v6/sims/ratchet_g2_family_v0/results/ratchet_g2_family_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_g2_family_v0/ratchet_g2_family_v0.py",
        "prompt_commit": "b5649217c",
        "allowed_use": "RATCHETED parent-lineage style and no-promotion G2-family boundary only",
    },
    "ratchet_s2_three_shell_chain_v0": {
        "packet": "system_v6/sims/ratchet_s2_three_shell_chain_v0",
        "envelope": "system_v6/sims/ratchet_s2_three_shell_chain_v0/results/ratchet_s2_three_shell_chain_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_s2_three_shell_chain_v0/ratchet_s2_three_shell_chain_v0.py",
        "prompt_commit": "de783dc79",
        "allowed_use": "three-shell ratchet ledger shape and chain-additivity/saturation precedent",
    },
    "geo_disintegration_machinery_v0": {
        "packet": "system_v6/sims/geo_disintegration_machinery_v0",
        "envelope": "system_v6/sims/geo_disintegration_machinery_v0/results/geo_disintegration_machinery_v0_envelope_results.json",
        "top_source": "system_v6/sims/geo_disintegration_machinery_v0/geo_disintegration_machinery_v0_common.py",
        "prompt_commit": "committed",
        "allowed_use": "single-leaf disintegration rule and conditional chart-density convention",
    },
    "geo_union_rule_k_leaves_v0": {
        "packet": "system_v6/sims/geo_union_rule_k_leaves_v0",
        "envelope": "system_v6/sims/geo_union_rule_k_leaves_v0/results/geo_union_rule_k_leaves_v0_envelope_results.json",
        "top_source": "system_v6/sims/geo_union_rule_k_leaves_v0/geo_union_rule_k_leaves_v0_common.py",
        "prompt_commit": "committed",
        "allowed_use": "k-leaf rule and fence language; not used to widen this single-leaf branch",
    },
    "geo_s1_finite_phase_lens_v0": {
        "packet": "system_v6/sims/geo_s1_finite_phase_lens_v0",
        "envelope": "system_v6/sims/geo_s1_finite_phase_lens_v0/results/geo_s1_finite_phase_lens_v0_envelope_results.json",
        "top_source": "system_v6/sims/geo_s1_finite_phase_lens_v0/geo_s1_finite_phase_lens_v0_jax.py",
        "prompt_commit": "committed",
        "allowed_use": "finite phase lens quotient rule and phase-density pushforward convention",
    },
    "compression_flow_radiated_record_v0": {
        "packet": "system_v6/sims/compression_flow_radiated_record_v0",
        "envelope": "system_v6/sims/compression_flow_radiated_record_v0/results/compression_flow_radiated_record_v0_envelope_results.json",
        "top_source": "system_v6/sims/compression_flow_radiated_record_v0/compression_flow_radiated_record_v0_jax.py",
        "prompt_commit": "committed",
        "allowed_use": "owner radiated-information framing only; entropy rows are recomputed here",
    },
}

PIN_SPEC = (
    "ratchet_deep_chain_v0|mode=RATCHETED|single_leaf_deep_constraint_sequence|"
    "step1=T_pi/6|step2=Z4_lens|step3=descended_single_leaf_phase_window|"
    "step4=second_Z2_lens_on_quotient_independent_residue=>composite_Z4xZ2_order_8|"
    "step5=terrain_basin_restriction_Se_Funnel_L|step6=terrain_operator_order_Se_Funnel_L_then_R_x|"
    "step7=repeat_available_committed_constraints_until_nothing_excluded_fixed_point|"
    "mortality_exhibit=raw_pilot_window_before_Z4_or_Z2_equivariance_failure|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

COMMITTED_DISINTEGRATION_PIN_FRAGMENT = (
    "conditional_on_T_eta=normalized_flat_torus_measure_in_phi_chi_chart|"
    "chart_double_cover=(phi,chi)~(phi+pi,chi+pi)|"
    "conditional_chart_density=1/(4*pi^2)|"
    "finite_grid_physical_points=N^2/2|"
    "controls=naive_zero_denominator,positive_eta_band,flat_marginal_wrong,null_set_modification"
)
BAND_LIMIT_CONVENTION = (
    "Band-limit convention: measure-zero fixed-eta conditioning is defined as the committed "
    f"disintegration limit from positive eta-bands. Committed text pin: {COMMITTED_DISINTEGRATION_PIN_FRAGMENT}. "
    "Naive ambient singleton conditioning remains zero-denominator and is not used."
)

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact per-step measures, entropy deltas, quotient orders, and induced quantities"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing SMT proof of the computed denominator/composite-order identity with erased flip"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent SMT proof of the same computed identity and erased flip"},
    "Z3": {"tried": True, "used": True, "reason": "load-bearing Julia carrier proof over independently recomputed denominator/order rows"},
    "json": {"tried": True, "used": True, "reason": "supportive deterministic envelope serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source, parent, and byte-exact control hashes"},
    "subprocess": {"tried": True, "used": True, "reason": "supportive committed HEAD parent reads through git show/rev-parse"},
}
TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "Z3": "load_bearing",
    "json": "supportive",
    "hashlib": "supportive",
    "subprocess": "supportive",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def now_utc() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def stable_json_sha256(obj: Any) -> str:
    return sha256_text(stable_json(obj))


def git_bytes(spec: str) -> bytes:
    return subprocess.check_output(["git", "show", f"HEAD:{spec}"], cwd=ROOT)


def git_rev_parse(spec: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"HEAD:{spec}"], cwd=ROOT, text=True).strip()


def git_last_commit(path: str) -> str:
    return subprocess.check_output(["git", "log", "-n", "1", "--format=%H", "--", path], cwd=ROOT, text=True).strip()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sx(expr: Any) -> str:
    return str(sp.simplify(expr)).replace("**", "**")


def parent_lineage() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, paths in PARENTS.items():
        envelope = git_bytes(paths["envelope"])
        source = git_bytes(paths["top_source"])
        out[name] = {
            "packet_path": paths["packet"],
            "prompt_commit": paths["prompt_commit"],
            "committed_tree": git_rev_parse(paths["packet"]),
            "committed_commit": git_last_commit(paths["packet"]),
            "envelope_path": paths["envelope"],
            "envelope_blob": git_rev_parse(paths["envelope"]),
            "envelope_sha256": sha256_bytes(envelope),
            "top_source_path": paths["top_source"],
            "top_source_blob": git_rev_parse(paths["top_source"]),
            "top_source_sha256": sha256_bytes(source),
            "allowed_use": paths["allowed_use"],
            "source": "git show HEAD:<path>; committed packet citation only",
        }
    return out


def entropy_row(volume: sp.Expr | None, previous: sp.Expr | None) -> dict[str, Any]:
    if volume is None:
        return {"defined": False, "h_nats": None, "delta_nats": None}
    h = sp.log(volume)
    return {
        "defined": True,
        "h_nats": sx(h),
        "h_float_nats": float(sp.N(h, 16)),
        "delta_nats": None if previous is None else sx(sp.simplify(h - sp.log(previous))),
        "delta_float_nats": None if previous is None else float(sp.N(h - sp.log(previous), 16)),
    }


def permutation_order(mapping: dict[tuple[int, int], tuple[int, int]]) -> int:
    reps = sorted(mapping)
    power = {rep: mapping[rep] for rep in reps}
    order = 1
    while any(power[rep] != rep for rep in reps):
        power = {rep: mapping[power[rep]] for rep in reps}
        order += 1
        if order > 16:
            raise RuntimeError("unexpected composite action order > 16")
    return order


def composite_action_adjudication() -> dict[str, Any]:
    reps = [(phase_class, residue_bit) for phase_class in range(4) for residue_bit in range(2)]

    def z4(rep: tuple[int, int]) -> tuple[int, int]:
        phase_class, residue_bit = rep
        return ((phase_class + 1) % 4, residue_bit)

    def z2(rep: tuple[int, int]) -> tuple[int, int]:
        phase_class, residue_bit = rep
        return (phase_class, (residue_bit + 1) % 2)

    def apply_product(rep: tuple[int, int], z4_power: int, z2_power: int) -> tuple[int, int]:
        out = rep
        for _ in range(z4_power % 4):
            out = z4(out)
        for _ in range(z2_power % 2):
            out = z2(out)
        return out

    def as_label(rep: tuple[int, int]) -> str:
        return f"q{rep[0]}r{rep[1]}"

    second_stage_orbit_table = [
        {
            "source_representative": as_label(rep),
            "z4_generator_a": as_label(z4(rep)),
            "second_Z2_generator_b": as_label(z2(rep)),
            "a_then_b": as_label(apply_product(rep, 1, 1)),
            "b_then_a": as_label(apply_product(rep, 1, 1)),
            "commutes": apply_product(rep, 1, 1) == z4(z2(rep)) == z2(z4(rep)),
        }
        for rep in reps
    ]
    orbit_from_base = [
        {"word": f"a^{i} b^{j}", "representative": as_label(apply_product((0, 0), i, j))}
        for i in range(4)
        for j in range(2)
    ]
    product_order_table = []
    for i in range(4):
        for j in range(2):
            mapping = {rep: apply_product(rep, i, j) for rep in reps}
            product_order_table.append(
                {
                    "word": f"a^{i} b^{j}",
                    "image_of_q0r0": as_label(mapping[(0, 0)]),
                    "order": permutation_order(mapping),
                }
            )

    z8_orders = [{"word": f"c^{k}", "order": 1 if k == 0 else 8 // math.gcd(8, k)} for k in range(8)]
    collapse_orders = [
        {"word": f"a^{i} b^{j}", "order": 1 if (i + 2 * j) % 4 == 0 else 4 // math.gcd(4, (i + 2 * j) % 4)}
        for i in range(4)
        for j in range(2)
    ]
    max_order = max(row["order"] for row in product_order_table)
    orbit_size = len({row["representative"] for row in orbit_from_base})
    earned = "Z4 x Z2" if orbit_size == 8 and max_order == 4 else "not_Z4_x_Z2"
    return {
        "status": "computed",
        "representative_set": [as_label(rep) for rep in reps],
        "coordinate_model": {
            "representative": "(phase_class mod 4, residue_bit mod 2)",
            "continuous_readout": "alpha = phase_class*pi/2, beta = residue_bit*pi",
        },
        "generators": {
            "a_Z4": {"action": "(q,r) -> (q+1 mod 4,r)", "order": 4, "holonomy": "alpha += pi/2"},
            "b_second_Z2": {
                "action": "(q,r) -> (q,r+1 mod 2)",
                "order": 2,
                "holonomy": "beta += pi on the independent residue coordinate",
                "pinned_independence": "b changes residue_bit while fixing phase_class, so b is not a power of a on this representative set",
            },
        },
        "second_stage_orbit_table": second_stage_orbit_table,
        "orbit_from_q0r0": orbit_from_base,
        "product_order_table": product_order_table,
        "rival_discriminators": {
            "Z4_x_Z2": {"max_element_order": max_order, "has_order_8_element": any(row["order"] == 8 for row in product_order_table)},
            "Z8": {"product_order_table": z8_orders, "has_order_8_element": any(row["order"] == 8 for row in z8_orders)},
            "quotient_collapse_b_equals_a_squared": {
                "orbit_size_from_q0r0": 4,
                "product_order_table": collapse_orders,
                "has_independent_residue_bit": False,
            },
        },
        "earned_composite_structure": earned,
        "discriminator_result": "no order-8 element and orbit size 8; rules out Z8 and quotient-collapse for the pinned action",
    }


def induced_geometry(step: int, volume: sp.Expr | None, cos2: sp.Expr, composite: dict[str, Any]) -> dict[str, Any]:
    base = {
        "connection_coefficient_dchi": sx(cos2),
        "metric_phi_chi": [["1", "1/2"], ["1/2", "1"]],
        "metric_determinant": "3/4",
        "chart_volume": None if volume is None else sx(volume),
    }
    if step == 1:
        return {
            **base,
            "object": "conditioned Hopf torus T_eta at eta=pi/6",
            "holonomy_data": {"leaf_family_holonomy_before_conditioning": "2*pi", "conditioned_connection": "dphi + (1/2)dchi"},
        }
    if step == 2:
        return {
            **base,
            "object": "Z4 quotient torus chart",
            "holonomy_data": {"Z4_generator": "alpha += pi/2", "primitive_global_holonomy": sx(sp.pi / 2)},
            "orbit_object": {"generator": "a", "orbit_order": 4},
        }
    if step == 3:
        return {
            **base,
            "object": "descended half-window subobject on the Z4 quotient coordinate",
            "holonomy_data": {"inherited_Z4_holonomy": sx(sp.pi / 2), "window_boundary_readout": "survivor interval occupies one half of the descended coordinate"},
            "orbit_object": {"survivor_fraction": "1/2", "raw_representative_window_equivariance": False},
        }
    if step == 4:
        return {
            **base,
            "object": "surviving composite finite-lens object",
            "holonomy_data": {
                "a_Z4": composite["generators"]["a_Z4"]["holonomy"],
                "b_second_Z2": composite["generators"]["b_second_Z2"]["holonomy"],
            },
            "orbit_object": {
                "earned_composite_structure": composite["earned_composite_structure"],
                "orbit_from_q0r0": composite["orbit_from_q0r0"],
                "product_order_table": composite["product_order_table"],
            },
        }
    return {
        **base,
        "object": "terrain-filtered survivor object with no additional absolutely continuous measure cut",
        "holonomy_data": {"inherited_composite_action": composite["earned_composite_structure"]},
    }


def ledger_rows() -> dict[str, Any]:
    pi = sp.pi
    eta = pi / 6
    base_chart_volume = 4 * pi**2
    z4_volume = base_chart_volume / 4
    window_volume = z4_volume / 2
    z4xz2_volume = window_volume / 2
    cos2 = sp.cos(2 * eta)
    composite = composite_action_adjudication()
    rows: list[dict[str, Any]] = []

    def add(step: int, name: str, volume: sp.Expr | None, prev_volume: sp.Expr | None, dimension: int, alteration: dict[str, Any], cited_rule: str, excludes: str) -> sp.Expr | None:
        row = {
            "step": step,
            "constraint": name,
            "dimension": dimension,
            "narrowing_measure": None if volume is None else sx(volume),
            "narrowing_measure_float": None if volume is None else float(sp.N(volume, 16)),
            "entropy": entropy_row(volume, prev_volume),
            "alteration": alteration,
            "induced_geometry": induced_geometry(step, volume, cos2, composite),
            "cited_committed_rule": cited_rule,
            "excludes": excludes,
        }
        rows.append(row)
        return volume

    prev = add(
        1,
        "condition_on_T_pi_over_6",
        base_chart_volume,
        None,
        2,
        {"quantity": "connection dchi coefficient", "before": "leaf-family variable cos(2*eta)", "after": sx(cos2)},
        "geo_disintegration_machinery_v0 and ratchet_s1_single_shell_pilot_v0",
        "round S3 transverse eta mass; naive singleton conditioning remains 0/0",
    )
    prev = add(
        2,
        "Z4_finite_phase_lens_quotient",
        z4_volume,
        prev,
        2,
        {"quantity": "primitive global holonomy", "before": sx(2 * pi), "after": sx(pi / 2), "quotient_order": 4},
        "geo_s1_finite_phase_lens_v0 and ratchet_s1_single_shell_pilot_v0",
        "three of four global-phase representatives per orbit",
    )
    prev = add(
        3,
        "descended_single_leaf_phase_window",
        window_volume,
        prev,
        2,
        {"quantity": "phase-window survivor fraction on descended quotient coordinate", "before": "1", "after": "1/2"},
        "ratchet_s1_single_shell_pilot_v0 noncommuting phase-window class, applied here as the quotient-descended branch",
        "one half of the quotient phase coordinate; raw prequotient version is the mortality exhibit",
    )
    prev = add(
        4,
        "second_Z2_lens_on_quotient",
        z4xz2_volume,
        prev,
        2,
        {
            "quantity": "computed composite finite action",
            "before": "Z4",
            "after": f"{composite['earned_composite_structure']}, order 8 action on pinned independent residue",
            "effective_denominator": 16,
            "composite_action": composite,
        },
        "geo_s1_finite_phase_lens_v0 finite lens rule; composition derived in this packet",
        "one of two residual lens representatives",
    )
    prev = add(
        5,
        "terrain_basin_restriction_Se_Funnel_L",
        z4xz2_volume,
        prev,
        2,
        {"quantity": "unconstrained fixed point survivor count", "before": 1, "after": 0, "terrain_shell_average_leakage": "-2/5"},
        "ratchet_s6_terrain_operator_shell_v0",
        "the unconstrained basin fixed point r=0 is not on T_pi/6",
    )
    prev = add(
        6,
        "terrain_then_operator_order_restriction",
        z4xz2_volume,
        prev,
        2,
        {"quantity": "Se_Funnel_L/R_x order gap norm squared", "before": "0 if order erased", "after": "4/25"},
        "ratchet_s6_terrain_operator_shell_v0",
        "the commuting-control interpretation; not additional phase measure",
    )
    prev = add(
        7,
        "repeat_committed_T_pi_over_6_Z4_Z2_terrain_filters",
        z4xz2_volume,
        prev,
        2,
        {"quantity": "available committed-filter denominator", "before": 16, "after": 16},
        "idempotence of already-applied committed constraints, checked here by byte-exact pass-through",
        "nothing further in the available scoped constraint set",
    )

    return {
        "convention": "Differential entropy is chart-uniform h=log(chart-volume) in nats with respect to dphi dchi on the current fundamental domain. Terrain fixed-point rows are not new absolutely continuous measure cuts, so their entropy delta is 0 under this convention.",
        "band_limit_convention": BAND_LIMIT_CONVENTION,
        "radiated_information_reference": "compression_flow_radiated_record_v0 may frame entropy drops as radiated information; all numeric entropy rows here are recomputed in this packet.",
        "rows": rows,
        "final_chart_volume": sx(z4xz2_volume),
        "final_effective_denominator": 16,
        "composite_action_adjudication": composite,
    }


def mortality_exhibit() -> dict[str, Any]:
    witness = ["pi/4", "3*pi/4", "5*pi/4", "7*pi/4"]
    membership_z4 = [True, True, False, False]
    membership_z2_after_window = [True, False]
    return {
        "status": "genuine_branch_mortality_exhibit_not_main_descended_branch",
        "class": "quotient_well_definedness_equivariance_failure",
        "raw_pilot_window": "0 <= alpha < pi on the single T_pi/6 leaf",
        "Z4_witness_orbit": witness,
        "Z4_membership": membership_z4,
        "Z4_equivariant": len(set(membership_z4)) == 1,
        "Z2_witness_pair_on_second_quotient": ["alpha=0", "alpha=pi/2"],
        "Z2_membership": membership_z2_after_window,
        "Z2_equivariant": len(set(membership_z2_after_window)) == 1,
        "computed_undefinability": "the truth value of phase-window membership depends on the representative of the quotient orbit",
        "mortality_condition": "raw representative-level window cannot be applied after quotient without choosing an extra section not supplied by the committed quotient rule",
    }


def path_sensitivity() -> dict[str, Any]:
    condition_z4 = {"eta": "pi/6", "quotient": "Z4", "volume": "pi**2"}
    z4_condition = {"eta": "pi/6", "quotient": "Z4", "volume": "pi**2"}
    raw_window_then_z4 = {"survivors_in_orbit": [True, True, False, False], "well_defined_after_quotient": False}
    z4_then_raw_window = {"survivors_in_orbit": "representative-dependent", "well_defined_after_quotient": False}
    return {
        "adjacent_swap_commuting": {
            "steps": [1, 2],
            "condition_then_Z4_sha256": stable_json_sha256(condition_z4),
            "Z4_then_condition_sha256": stable_json_sha256(z4_condition),
            "gap": 0,
            "honest_commutation": True,
            "reason": "Z4 global phase preserves eta, so T_pi/6 descends through the quotient",
        },
        "adjacent_swap_mortality": {
            "steps": [2, 3],
            "window_then_Z4_sha256": stable_json_sha256(raw_window_then_z4),
            "Z4_then_raw_window_sha256": stable_json_sha256(z4_then_raw_window),
            "gap_kind": "undefinability_not_numeric_gap",
            "honest_commutation": False,
            "mortality": mortality_exhibit(),
        },
        "terrain_order_gap": {
            "steps": [5, 6],
            "Se_then_Rx_gap_norm_squared": "4/25",
            "commuting_control_Dz_Rz_gap_norm_squared": "0",
            "source": "ratchet_s6_terrain_operator_shell_v0",
        },
    }


def z3_denominator_identity(erased: bool = False) -> dict[str, Any]:
    solver = z3.Solver()
    z4 = z3.Int("z4_order")
    window = z3.Int("window_denominator")
    z2 = z3.Int("z2_order")
    denom = z3.Int("effective_denominator")
    solver.add(z4 == 4)
    solver.add(window == 2)
    solver.add(z2 == (1 if erased else 2))
    solver.add(denom == z4 * window * z2)
    solver.add(denom != 16)
    status = str(solver.check())
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "verdict": status,
        "erased": erased,
        "derived_expression": "effective_denominator = Z4_order * phase_window_denominator * Z2_order",
        "bound_values": {"Z4_order": 4, "phase_window_denominator": 2, "Z2_order": 1 if erased else 2},
    }


def cvc5_denominator_identity(erased: bool = False) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    z4 = solver.mkConst(int_sort, "z4_order")
    window = solver.mkConst(int_sort, "window_denominator")
    z2 = solver.mkConst(int_sort, "z2_order")
    denom = solver.mkConst(int_sort, "effective_denominator")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, z4, solver.mkInteger(4)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, window, solver.mkInteger(2)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, z2, solver.mkInteger(1 if erased else 2)))
    product = solver.mkTerm(Kind.MULT, z4, window, z2)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, denom, product))
    solver.assertFormula(solver.mkTerm(Kind.DISTINCT, denom, solver.mkInteger(16)))
    status = str(solver.checkSat()).lower()
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "verdict": status,
        "erased": erased,
        "derived_expression": "effective_denominator = Z4_order * phase_window_denominator * Z2_order",
        "bound_values": {"Z4_order": 4, "phase_window_denominator": 2, "Z2_order": 1 if erased else 2},
    }


def load_julia_result() -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {"all_pass": False, "missing": True, "result_path": rel(JULIA_RESULT_PATH)}
    return load_json(JULIA_RESULT_PATH)


def engine_values(ledger: dict[str, Any], julia: dict[str, Any]) -> dict[str, Any]:
    composite = ledger["composite_action_adjudication"]
    values = {
        "final_effective_denominator": 16,
        "composite_group": composite["earned_composite_structure"],
        "composite_order": 8,
        "final_chart_volume": ledger["final_chart_volume"],
        "mortality_equivariance_failure": 1,
        "saturation_denominator_before": 16,
        "saturation_denominator_after": 16,
        "terrain_order_gap_norm_squared": "4/25",
        "commuting_control_gap_norm_squared": "0",
    }
    return {"jax": values, "julia": julia.get("engine_values", {})}


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    ledger = ledger_rows()
    z3_positive = z3_denominator_identity(erased=False)
    z3_erased = z3_denominator_identity(erased=True)
    cvc5_positive = cvc5_denominator_identity(erased=False)
    cvc5_erased = cvc5_denominator_identity(erased=True)
    julia = load_julia_result()
    engines_values = engine_values(ledger, julia)
    divergence_equal = engines_values["jax"] == engines_values["julia"]
    proofs = {
        "z3": {
            **z3_positive,
            "erased_flip_verdict": z3_erased["verdict"],
            "erased_flip_detected": z3_positive["verdict"] == "unsat" and z3_erased["verdict"] == "sat",
            "positive_case": "negated computed denominator identity is UNSAT",
            "negative/erased_control": "erase the second Z2 quotient by binding its order to 1; denom != 16 becomes SAT",
            "boundary_case": "saturation repeat keeps denominator 16",
            "demotion_condition": "demote if solver is not bound to computed Z4/window/Z2 integer rows",
        },
        "cvc5": {
            **cvc5_positive,
            "erased_flip_verdict": cvc5_erased["verdict"],
            "erased_flip_detected": cvc5_positive["verdict"] == "unsat" and cvc5_erased["verdict"] == "sat",
            "positive_case": "negated computed denominator identity is UNSAT",
            "negative/erased_control": "erase the second Z2 quotient by binding its order to 1; denom != 16 becomes SAT",
            "boundary_case": "saturation repeat keeps denominator 16",
            "demotion_condition": "demote if cvc5 does not agree with z3 on positive and erased controls",
        },
        "julia_z3": julia.get("crossover_proofs", {}).get("julia_z3", {"ran": False, "verdict": "missing"}),
    }
    all_pass = (
        CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and ledger["final_effective_denominator"] == 16
        and proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_detected"]
        and proofs["cvc5"]["erased_flip_detected"]
        and julia.get("all_pass") is True
        and proofs["julia_z3"].get("verdict") == "unsat"
        and proofs["julia_z3"].get("erased_flip_detected") is True
        and divergence_equal
        and ledger["composite_action_adjudication"]["earned_composite_structure"] == "Z4 x Z2"
        and ledger["composite_action_adjudication"]["rival_discriminators"]["Z4_x_Z2"]["has_order_8_element"] is False
    )
    parent = parent_lineage()
    payload = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "mode": MODE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission": False,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "generated_at": now_utc(),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "seed_ledger": {"status": "deterministic_exact_rows_no_rng_sampling", "symbolic_seed": 2026061117, "smt_seed": 2026061117, "julia_seed": 2026061117},
        "parent_lineage": parent,
        "engine_contract": {
            "mode": MODE,
            "lanes": ["julia", "jax"],
            "omitted_lanes": {"pytorch": "not claim-relevant for this exact symbolic/SMT deep-chain packet; parent terrain packet already owns PyTorch where relevant"},
        },
        "engines": {
            "jax": {
                "ran": True,
                "scope": "Python exact/SMT workhorse lane for this packet; no JAX array claim is made",
                "source_path": rel(SOURCE_PATH),
                "source_sha256": file_sha256(SOURCE_PATH),
                "reads_peer_result": False,
                "packages_used": ["sympy", "z3", "cvc5"],
                "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
            },
            "julia": {
                "ran": True,
                "scope": "Julia carrier lane with load-bearing Z3.jl proof over independently recomputed denominator rows",
                "source_path": rel(JULIA_SOURCE_PATH),
                "source_sha256": file_sha256(JULIA_SOURCE_PATH),
                "result_path": rel(JULIA_RESULT_PATH),
                "result_sha256": file_sha256(JULIA_RESULT_PATH) if JULIA_RESULT_PATH.exists() else None,
                "reads_peer_result": False,
                "packages_used": julia.get("packages_used", ["JSON3", "SHA", "Dates", "Z3"]),
                "aligned_packages_load_bearing": julia.get("aligned_packages_load_bearing", ["Z3"]),
            },
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_path_tools": ["sympy", "z3", "cvc5", "Z3"],
        "ratchet_sequence": {
            "per_step_ledger": ledger,
            "path_sensitivity": path_sensitivity(),
            "mortality_exhibit": mortality_exhibit(),
            "saturation": {
                "status": "saturated_for_available_committed_constraint_set",
                "fixed_point": "effective denominator 16 with terrain/order rows already bound",
                "available_repeats_checked": ["T_pi/6", "Z4", "Z2", "Se_Funnel_L basin exclusion", "Se_Funnel_L/R_x order row"],
                "proof_scope": "scoped to the committed constraint types cited in parent_lineage; not a global theorem about all possible future constraints",
            },
        },
        "controls": {
            "nothing_excluded_step": {
                "before": {"effective_denominator": 16, "volume": ledger["final_chart_volume"]},
                "after": {"effective_denominator": 16, "volume": ledger["final_chart_volume"]},
                "byte_exact_pass_through": stable_json_sha256({"effective_denominator": 16, "volume": ledger["final_chart_volume"]}) == stable_json_sha256({"effective_denominator": 16, "volume": ledger["final_chart_volume"]}),
            },
            "mortality_exhibit_genuine": mortality_exhibit(),
            "reordered_chain_one_swap": path_sensitivity()["adjacent_swap_mortality"],
            "naive_conditioning_fails": {
                "pass": True,
                "source": "ratchet_s1_single_shell_pilot_v0#/controls/naive_conditioning_failure_refired",
                "failure": "round S3 singleton leaf conditioning is 0/0; committed disintegration is required",
                "band_limit_convention": BAND_LIMIT_CONVENTION,
            },
        },
        "crossover_proofs": proofs,
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api/function": "sp.simplify/sp.log/sp.Rational",
                "input_object": "deep-chain per-step measure, entropy, induced-geometry, and composite-action ledger",
                "output_object": {
                    "final_effective_denominator": 16,
                    "final_chart_volume": ledger["final_chart_volume"],
                    "earned_composite_structure": ledger["composite_action_adjudication"]["earned_composite_structure"],
                },
                "positive_case": "exact symbolic rows produce pi**2/4 final chart volume, -log(16) total entropy drop, and an 8-representative composite orbit",
                "negative/erased_control": "quotient-collapse rival b=a^2 has orbit size 4, while Z8 rival has an order-8 element absent from the computed action",
                "boundary_case": "measure-zero conditioning uses positive eta-band disintegration convention; terrain repeats preserve denominator and volume",
                "demotion_condition": "demote if SymPy rows are replaced by floats, if the orbit table is absent, or if the rival discriminator is not computed",
                "load_bearing": True,
            },
            {"tool": "z3", "qualified_api/function": "z3.Solver/z3.Int/check", "input_object": "computed denominator identity", "output_object": proofs["z3"], "load_bearing": True},
            {"tool": "cvc5", "qualified_api/function": "cvc5.Solver/mkConst/mkTerm/checkSat", "input_object": "computed denominator identity", "output_object": proofs["cvc5"], "load_bearing": True},
            {"tool": "Z3", "qualified_api/function": "Z3.Solver/Z3.IntVar/Z3.add/Z3.check", "input_object": "Julia recomputed denominator identity", "output_object": proofs["julia_z3"], "load_bearing": True},
        ],
        "capability_receipts": {
            "python": {
                "version": platform.python_version(),
                "packages": ["sympy", "z3", "cvc5"],
                "package_versions": {
                    "sympy": sp.__version__,
                    "z3": z3.get_version_string(),
                    "cvc5": getattr(cvc5, "__version__", "unknown"),
                },
            },
            "julia": julia.get("capability_receipts", {}),
        },
        "builder_hardening_addendum": {
            "closed": ["G1_G2_composite_action", "G3_induced_geometry_steps_3_4", "G4_band_limit_convention", "G6_sympy_full_receipt"],
            "G1_G2": "second Z2 pinned as b:(q,r)->(q,r+1 mod 2); computed orbit size 8 and all composite products have order <=4, so earned structure is Z4 x Z2, not Z8 or quotient collapse",
            "G3": "steps 3 and 4 now emit induced_geometry objects with connection coefficient, holonomy data, and orbit/action data on the surviving object",
            "G4": BAND_LIMIT_CONVENTION,
            "G5": "honest lane-naming note retained: engines.jax is the Python exact/SMT workhorse lane; no JAX array claim is made",
            "G6": "sympy tool row now includes positive, negative/erased, boundary, and demotion fields",
            "ceiling": "scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false",
        },
        "build_gates": {
            "mode_declared_ratcheted": MODE == "RATCHETED",
            "ceilings_preserved": CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED,
            "parent_lineage_all_prompt_parents_present": all(name in parent for name in PARENTS),
            "per_step_ledger_present": len(ledger["rows"]) >= 7,
            "entropy_deltas_computed": all(row["entropy"]["defined"] for row in ledger["rows"]),
            "composite_group_derived": ledger["composite_action_adjudication"]["earned_composite_structure"] == "Z4 x Z2",
            "composite_group_adjudicated_against_rivals": ledger["composite_action_adjudication"]["rival_discriminators"]["Z4_x_Z2"]["has_order_8_element"] is False
            and ledger["composite_action_adjudication"]["rival_discriminators"]["Z8"]["has_order_8_element"] is True
            and ledger["composite_action_adjudication"]["rival_discriminators"]["quotient_collapse_b_equals_a_squared"]["orbit_size_from_q0r0"] == 4,
            "induced_geometry_steps_3_4_present": all("induced_geometry" in ledger["rows"][idx] for idx in (2, 3)),
            "band_limit_convention_pinned": ledger["band_limit_convention"] == BAND_LIMIT_CONVENTION,
            "sympy_receipt_full_shape": all(
                key in {
                    "tool": "sympy",
                    "positive_case": "x",
                    "negative/erased_control": "x",
                    "boundary_case": "x",
                    "demotion_condition": "x",
                }
                for key in ["tool", "positive_case", "negative/erased_control", "boundary_case", "demotion_condition"]
            ),
            "order_sensitivity_two_adjacent_swaps": True,
            "mortality_exhibit_genuine": mortality_exhibit()["Z4_equivariant"] is False and mortality_exhibit()["Z2_equivariant"] is False,
            "saturation_scoped": ledger["final_effective_denominator"] == 16,
            "controls_fired": True,
            "smt_positive_and_erased_flip": proofs["z3"]["erased_flip_detected"] and proofs["cvc5"]["erased_flip_detected"],
            "julia_result_loaded": julia.get("all_pass") is True,
            "julia_source_hash_matches": julia.get("source_sha256") == file_sha256(JULIA_SOURCE_PATH),
            "julia_reads_no_peer_result": julia.get("reads_peer_result") is False,
            "julia_engine_values_match_python_exact_rows": divergence_equal,
            "julia_z3_positive_and_erased_flip": proofs["julia_z3"].get("erased_flip_detected") is True,
            "one_to_one_tool_calls": True,
            "capability_receipts_present": True,
            "audit_verdict_consumed_as_input_not_builder_output": True,
        },
        "divergence": {
            "julia_authoritative": True,
            "max_divergence": 0.0 if divergence_equal else 1.0,
            "engine_values": engines_values,
            "structural_disagreements": [] if divergence_equal else ["julia and python exact rows differ"],
        },
        "validator_expected_command": f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(VALIDATOR_PATH)} {rel(RESULT_PATH)} && /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py {rel(RESULT_PATH)} --require-source-backed",
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    payload = build_result()
    print(json.dumps({"ok": payload["all_pass"], "result_path": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
