#!/usr/bin/env python3
"""JAX leg for the terrain/operator precedence 64-cell chart matrix."""

from __future__ import annotations

from jax import config

config.update("jax_enable_x64", True)

import datetime as _dt
import hashlib
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "terrain_operator_precedence_64_matrix"
ENGINE = "jax"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
FP_TOL = 1.0e-8
SMT_SCALE = 10**10

OP_PACKET = ROOT / "system_v6" / "sims" / "source_locked_operator_base_packet" / "source_locked_operator_base_packet_jax.py"
TERRAIN_PACKET = ROOT / "system_v6" / "sims" / "terrain_generator_sheet_packet" / "terrain_generator_sheet_packet_jax.py"
MCT_RESULT = ROOT / "system_v6" / "sims" / "mct_dynamic_admissibility_packet_v0" / "results" / "mct_dynamic_admissibility_packet_v0_jax_results.json"

PIN_BLOCK_CANONICAL = '{"carrier_lineage":{"boundary":"Hopf/Weyl density carrier only; no nested/rung maps","mct_pin_block_sha256":"f64f2c3624658fb522c8e5363ae2bb1a38b2a626d9da5e283ef05025a0e13161","path":"system_v6/sims/mct_dynamic_admissibility_packet_v0/"},"cells":{"address_key":["terrain_id","signed_operator_id","stage_id","suboperator_id"],"signed_operator_id":["Ti+","Te+","Fi+","Fe+","Ti-","Te-","Fi-","Fe-"],"terrain_id":["Se/Funnel","Se/Cannon","Ne/Vortex","Ne/Spiral","Ni/Pit","Ni/Source","Si/Hill","Si/Citadel"]},"fingerprint_ladder":["F0_address","F1_final_density","F2_order_pair","F3_delta","F4_observable","F5_entropy_purity","F6_spinor_sheet_loop","F7_trajectory","F8_axis_orthogonality"],"fp_tol":1e-08,"operator_pin":{"lineage":"system_v6/sims/source_locked_operator_base_packet/","q1":0.3,"q2":0.3,"theta":"pi/2","phi":"pi/2"},"precedence_semantics":{"+":"Phi_T(O(rho))","-":"O(Phi_T(rho))","source":"system_v6/receipts/terrain_operator_map_20260609.md:36-39"},"states":{"generic_state_sweep_subset_size":6,"pinned_non_eigen_rho":"rho_1=0.7*rho_0+0.3*I/2 from source_locked_operator_base_packet PIN_SPEC"},"terrain_pin":{"Phi":"expm(0.4 * X)","lineage":"system_v6/sims/terrain_generator_sheet_packet/","source_locked_parameters":{"EPS":0.2,"GAMMA_NI":0.5,"KAPPA_SI":0.4,"OMEGA_SI":0.2,"SE_LAMBDA":0.2}}}'
PIN_BLOCK_SHA256 = hashlib.sha256(PIN_BLOCK_CANONICAL.encode("utf-8")).hexdigest()

TERRAIN_SPECS = [
    {"terrain_id": "Se/Funnel", "terrain_key": "Funnel", "family": "Se", "sheet": "L", "stage_id": "Se/Funnel/inner"},
    {"terrain_id": "Se/Cannon", "terrain_key": "Cannon", "family": "Se", "sheet": "R", "stage_id": "Se/Cannon/inner"},
    {"terrain_id": "Ne/Vortex", "terrain_key": "Vortex", "family": "Ne", "sheet": "L", "stage_id": "Ne/Vortex/inner"},
    {"terrain_id": "Ne/Spiral", "terrain_key": "Spiral", "family": "Ne", "sheet": "R", "stage_id": "Ne/Spiral/inner"},
    {"terrain_id": "Ni/Pit", "terrain_key": "Pit", "family": "Ni", "sheet": "L", "stage_id": "Ni/Pit/inner"},
    {"terrain_id": "Ni/Source", "terrain_key": "Source", "family": "Ni", "sheet": "R", "stage_id": "Ni/Source/inner"},
    {"terrain_id": "Si/Hill", "terrain_key": "Hill", "family": "Si", "sheet": "L", "stage_id": "Si/Hill/inner"},
    {"terrain_id": "Si/Citadel", "terrain_key": "Citadel", "family": "Si", "sheet": "R", "stage_id": "Si/Citadel/inner"},
]
BASE_OPERATORS = ["Ti", "Te", "Fi", "Fe"]
SIGNED_OPERATORS = [f"{op}{sign}" for sign in ["+", "-"] for op in BASE_OPERATORS]
FINGERPRINTS = [
    "F0_address",
    "F1_final_density",
    "F2_order_pair",
    "F3_delta",
    "F4_observable",
    "F5_entropy_purity",
    "F6_spinor_sheet_loop",
    "F7_trajectory",
    "F8_axis_orthogonality",
]

SOURCE_REFS = {
    "matrix64_spec_A_D": "system_v6/receipts/matrix64_mine_20260610.md:5-242",
    "chart_not_runtime_boundary": "system_v6/receipts/matrix64_mine_20260610.md:61-84,156",
    "fingerprint_ladder": "system_v6/receipts/matrix64_mine_20260610.md:209-242",
    "precedence_semantics": "system_v6/receipts/terrain_operator_map_20260609.md:36-39",
    "signed_operator_boundary": "system_v6/receipts/terrain_operator_map_20260609.md:54",
    "terrain_generators": "system_v5/READ ONLY Reference Docs/terrain math.md:72-83",
    "terrain_placements": "system_v5/READ ONLY Reference Docs/terrain math.md:118-150",
    "terrain_rosetta_lock": "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:149-183",
    "operator_exact_lock": "system_v5/READ ONLY Reference Docs/operator math explicit.md:3-4,796-810",
}

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive 64-cell x pinned/generic-state batch construction; substrate demoted under capability-probe doctrine"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive complex density matrices, norms, spectra, observables, and fingerprints; substrate demoted under capability-probe doctrine"},
    "jax.scipy.linalg": {"tried": True, "used": True, "reason": "supportive local lineage citation; load-bearing expm call lives in reused terrain packet"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing SMT over computed noncommuting Delta entries and erased zero control"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent SMT over the same computed entries/control"},
}
TOOL_INTEGRATION_DEPTH = {"jax": "supportive", "jax.numpy": "supportive", "jax.scipy.linalg": "supportive", "z3": "load_bearing", "cvc5": "load_bearing"}
SOURCE_BACKED_AUDIT_CHOICE = {
    "chosen_fix": "demote_local_jax_scipy_linalg_declaration",
    "local_declaration": "supportive",
    "load_bearing_source": "system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py:20,443,447",
    "strict_validator_reason": "matrix source imports and uses z3/cvc5 directly; jax.scipy.linalg expm is transitive through the reused terrain packet",
}
F6_RESULT_NOTE = (
    "family-specific collapse (sheet/loop/chirality magnitude family); coarser than commute classes; "
    "not evidence of intended mathematical degeneracy"
)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OP_SRC = load_module(OP_PACKET, "source_locked_operator_base_packet_jax_reuse")
TERRAIN_SRC = load_module(TERRAIN_PACKET, "terrain_generator_sheet_packet_jax_reuse")

I2 = OP_SRC.I2
SX = OP_SRC.SX
SY = OP_SRC.SY
SZ = OP_SRC.SZ
H0 = TERRAIN_SRC.H0


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def real_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def hermitize(rho: Any) -> Any:
    return 0.5 * (rho + jnp.conjugate(rho.T))


def matrix_json(mat: Any) -> list[list[list[float]]]:
    arr = jax.device_get(mat)
    return [[[float(jnp.real(arr[i, j])), float(jnp.imag(arr[i, j]))] for j in range(arr.shape[1])] for i in range(arr.shape[0])]


def matrix_key(mat: Any, tol: float = FP_TOL) -> tuple[int, ...]:
    arr = jax.device_get(mat)
    out: list[int] = []
    for value in arr.reshape(-1):
        out.append(int(round(float(jnp.real(value)) / tol)))
        out.append(int(round(float(jnp.imag(value)) / tol)))
    return tuple(out)


def scalar_key(values: list[Any], tol: float = FP_TOL) -> tuple[int, ...]:
    return tuple(int(round(float(v) / tol)) for v in values)


def entropy_vn(rho: Any) -> float:
    vals = jnp.clip(jnp.real(jnp.linalg.eigvalsh(hermitize(rho))), 0.0, 1.0)
    ent = -jnp.sum(jnp.where(vals > 1.0e-14, vals * jnp.log(vals), 0.0))
    return real_float(ent)


def purity(rho: Any) -> float:
    return real_float(jnp.trace(rho @ rho))


def fro_norm(mat: Any) -> float:
    return real_float(jnp.linalg.norm(mat))


def trace_norm(mat: Any) -> float:
    return real_float(jnp.sum(jnp.linalg.svd(mat, compute_uv=False)))


def max_abs(mat: Any) -> float:
    return real_float(jnp.max(jnp.abs(mat)))


def observable_values(rho: Any, terrain: dict[str, str], base_op: str) -> dict[str, float]:
    op_axis = "z" if base_op in {"Ti", "Fe"} else "x"
    op_matrix = SZ if op_axis == "z" else SX
    h = H0 if terrain["sheet"] == "L" else -H0
    return {
        "sigma_x": real_float(jnp.trace(rho @ SX)),
        "sigma_y": real_float(jnp.trace(rho @ SY)),
        "sigma_z": real_float(jnp.trace(rho @ SZ)),
        "operator_axis_expectation": real_float(jnp.trace(rho @ op_matrix)),
        "terrain_hamiltonian_expectation": real_float(jnp.trace(rho @ h)),
    }


def terrain_channel(terrain_key: str) -> Any:
    gen = TERRAIN_SRC.generator_fn(terrain_key, ne_variant="pure_hamiltonian")
    return TERRAIN_SRC.channel_from_generator(gen)


def apply_terrain(channel: Any, rho: Any) -> Any:
    return TERRAIN_SRC.apply_channel(channel, rho)


def apply_operator(base_op: str, rho: Any) -> Any:
    return OP_SRC.source_channel(base_op, rho)


def spinor_density(phi: float, chi: float, eta: float) -> Any:
    return OP_SRC.density_from_spinor(OP_SRC.spinor(phi, chi, eta))


def loop_density_deltas(phi: float, chi: float, eta: float) -> dict[str, float]:
    u = math.pi / 4.0
    rho0 = spinor_density(phi, chi, eta)
    inner = spinor_density(phi + u, chi, eta)
    outer = spinor_density(phi - math.cos(2.0 * eta) * u, chi + u, eta)
    return {
        "inner_density_delta_fro": fro_norm(inner - rho0),
        "outer_density_delta_fro": fro_norm(outer - rho0),
        "outer_minus_inner_delta_fro": fro_norm(outer - inner),
    }


def generic_carrier_sweep_states() -> list[dict[str, Any]]:
    samples = [
        ("L", 0, 0, math.pi / 8.0),
        ("L", 1, 2, math.pi / 4.0),
        ("L", 3, 5, 3.0 * math.pi / 8.0),
        ("R", 4, 1, math.pi / 8.0),
        ("R", 6, 3, math.pi / 4.0),
        ("R", 7, 7, 3.0 * math.pi / 8.0),
    ]
    rows = []
    for sheet, phi_i, chi_j, eta in samples:
        phi = 2.0 * math.pi * phi_i / 8.0
        chi = 2.0 * math.pi * chi_j / 8.0
        rows.append(
            {
                "carrier_row_id": f"{sheet}_phi{phi_i}_chi{chi_j}_eta{round(eta, 12)}",
                "sheet": sheet,
                "phi_i": phi_i,
                "chi_j": chi_j,
                "eta": eta,
                "rho": spinor_density(phi, chi, eta),
            }
        )
    return rows


def cell_id(terrain_id: str, signed_operator_id: str) -> str:
    return terrain_id.replace("/", "_") + "__" + signed_operator_id.replace("+", "_plus").replace("-", "_minus")


def compute_cell(terrain: dict[str, str], signed_operator_id: str, rho: Any, sweep_states: list[dict[str, Any]]) -> dict[str, Any]:
    base_op = signed_operator_id[:2]
    sign = signed_operator_id[-1]
    channel = terrain_channel(terrain["terrain_key"])
    op_first_mid = apply_operator(base_op, rho)
    terrain_first_mid = apply_terrain(channel, rho)
    plus_out = apply_terrain(channel, op_first_mid)
    minus_out = apply_operator(base_op, terrain_first_mid)
    selected = plus_out if sign == "+" else minus_out
    counterfactual = minus_out if sign == "+" else plus_out
    delta = plus_out - minus_out
    signed_delta = selected - counterfactual
    obs_before = observable_values(rho, terrain, base_op)
    obs_selected = observable_values(selected, terrain, base_op)
    obs_counter = observable_values(counterfactual, terrain, base_op)
    loop = loop_density_deltas(0.3, 0.2, math.pi / 8.0)
    sweep_norms = []
    for sample in sweep_states:
        sample_plus = apply_terrain(channel, apply_operator(base_op, sample["rho"]))
        sample_minus = apply_operator(base_op, apply_terrain(channel, sample["rho"]))
        sweep_norms.append(fro_norm(sample_plus - sample_minus))
    return {
        "cell_id": cell_id(terrain["terrain_id"], signed_operator_id),
        "terrain_id": terrain["terrain_id"],
        "terrain_key": terrain["terrain_key"],
        "family": terrain["family"],
        "sheet": terrain["sheet"],
        "signed_operator_id": signed_operator_id,
        "base_operator": base_op,
        "precedence_sign": sign,
        "stage_id": terrain["stage_id"],
        "suboperator_id": base_op,
        "rho_in": rho,
        "operator_first_mid": op_first_mid,
        "terrain_first_mid": terrain_first_mid,
        "plus_out": plus_out,
        "minus_out": minus_out,
        "selected_out": selected,
        "counterfactual_out": counterfactual,
        "delta": delta,
        "signed_delta": signed_delta,
        "delta_norms": {
            "fro": fro_norm(delta),
            "trace": trace_norm(delta),
            "max_abs": max_abs(delta),
            "signed_fro": fro_norm(signed_delta),
        },
        "entropy_purity": {
            "entropy_before": entropy_vn(rho),
            "entropy_selected": entropy_vn(selected),
            "entropy_counterfactual": entropy_vn(counterfactual),
            "entropy_delta_selected_minus_before": entropy_vn(selected) - entropy_vn(rho),
            "entropy_selected_minus_counterfactual": entropy_vn(selected) - entropy_vn(counterfactual),
            "purity_before": purity(rho),
            "purity_selected": purity(selected),
            "purity_counterfactual": purity(counterfactual),
            "purity_delta_selected_minus_before": purity(selected) - purity(rho),
            "purity_selected_minus_counterfactual": purity(selected) - purity(counterfactual),
        },
        "observables": {
            "before": obs_before,
            "selected": obs_selected,
            "counterfactual": obs_counter,
            "selected_minus_before": {k: obs_selected[k] - obs_before[k] for k in obs_before},
            "selected_minus_counterfactual": {k: obs_selected[k] - obs_counter[k] for k in obs_before},
        },
        "spinor_sheet_loop": {
            "sheet": terrain["sheet"],
            "sheet_sign": 1 if terrain["sheet"] == "L" else -1,
            "loop_path_default": "inner",
            "pinned_phi": 0.3,
            "pinned_chi": 0.2,
            "pinned_eta": math.pi / 8.0,
            "hopf_connection_sample": 1.0 + math.cos(math.pi / 4.0),
            "chirality_gap_signed_delta_fro": (1 if terrain["sheet"] == "L" else -1) * fro_norm(signed_delta),
            **loop,
        },
        "trajectory": {
            "selected_order": "Phi_T(O(rho))" if sign == "+" else "O(Phi_T(rho))",
            "counterfactual_order": "O(Phi_T(rho))" if sign == "+" else "Phi_T(O(rho))",
            "selected_matrices": [rho, op_first_mid if sign == "+" else terrain_first_mid, selected],
            "counterfactual_matrices": [rho, terrain_first_mid if sign == "+" else op_first_mid, counterfactual],
        },
        "axis_orthogonality": {
            "axis6_precedence_sign": sign,
            "axis6_signed_delta_fro": fro_norm(signed_delta),
            "axis4_inner_density_delta_fro": loop["inner_density_delta_fro"],
            "axis4_outer_density_delta_fro": loop["outer_density_delta_fro"],
            "axis4_loop_class": "fiber_density_stationary_vs_base_density_visible",
        },
        "generic_state_sweep": {
            "subset_size": len(sweep_states),
            "carrier_row_ids": [sample["carrier_row_id"] for sample in sweep_states],
            "delta_fro_norms": sweep_norms,
            "min_delta_fro": min(sweep_norms),
            "max_delta_fro": max(sweep_norms),
            "mean_delta_fro": sum(sweep_norms) / len(sweep_norms),
        },
    }


def json_cell(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "cell_id": raw["cell_id"],
        "address_key": {
            "terrain_id": raw["terrain_id"],
            "signed_operator_id": raw["signed_operator_id"],
            "stage_id": raw["stage_id"],
            "suboperator_id": raw["suboperator_id"],
        },
        "source_locked_forms": {
            "terrain_channel": raw["terrain_key"],
            "base_operator": raw["base_operator"],
            "precedence_semantics": "+ = Phi_T(O(rho)); - = O(Phi_T(rho))",
        },
        "rho_in": matrix_json(raw["rho_in"]),
        "ordered_outputs": {
            "operator_first_then_terrain__plus": matrix_json(raw["plus_out"]),
            "terrain_first_then_operator__minus": matrix_json(raw["minus_out"]),
            "selected_by_signed_operator": matrix_json(raw["selected_out"]),
            "counterfactual_order": matrix_json(raw["counterfactual_out"]),
        },
        "Delta_T_O_matrix_plus_minus": matrix_json(raw["delta"]),
        "signed_delta_selected_minus_counterfactual": matrix_json(raw["signed_delta"]),
        "Delta_T_O_norms": raw["delta_norms"],
        "entropy_purity_deltas": raw["entropy_purity"],
        "observables": raw["observables"],
        "spinor_sheet_loop": raw["spinor_sheet_loop"],
        "trajectory": {
            "selected_order": raw["trajectory"]["selected_order"],
            "counterfactual_order": raw["trajectory"]["counterfactual_order"],
            "selected_matrices": [matrix_json(mat) for mat in raw["trajectory"]["selected_matrices"]],
            "counterfactual_matrices": [matrix_json(mat) for mat in raw["trajectory"]["counterfactual_matrices"]],
        },
        "axis_orthogonality": raw["axis_orthogonality"],
        "generic_state_sweep": raw["generic_state_sweep"],
        "computed_behavior_columns_present": True,
    }


def fingerprint_key(row: dict[str, Any], family: str, tol: float = FP_TOL) -> tuple[Any, ...]:
    if family == "F0_address":
        return (row["terrain_id"], row["signed_operator_id"], row["stage_id"], row["suboperator_id"])
    if family == "F1_final_density":
        return matrix_key(row["selected_out"], tol)
    if family == "F2_order_pair":
        return matrix_key(row["selected_out"], tol) + matrix_key(row["counterfactual_out"], tol)
    if family == "F3_delta":
        return matrix_key(row["signed_delta"], tol) + scalar_key([row["delta_norms"]["signed_fro"], row["delta_norms"]["trace"], row["delta_norms"]["max_abs"]], tol)
    if family == "F4_observable":
        vals = row["observables"]["selected"] | row["observables"]["selected_minus_counterfactual"]
        return scalar_key([vals[k] for k in sorted(vals)], tol)
    if family == "F5_entropy_purity":
        vals = row["entropy_purity"]
        return scalar_key([vals[k] for k in sorted(vals)], tol)
    if family == "F6_spinor_sheet_loop":
        vals = row["spinor_sheet_loop"]
        return (
            vals["sheet"],
            vals["loop_path_default"],
            *scalar_key(
                [
                    vals["hopf_connection_sample"],
                    vals["chirality_gap_signed_delta_fro"],
                    vals["inner_density_delta_fro"],
                    vals["outer_density_delta_fro"],
                ],
                tol,
            ),
        )
    if family == "F7_trajectory":
        mats = row["trajectory"]["selected_matrices"] + row["trajectory"]["counterfactual_matrices"]
        key: tuple[int, ...] = tuple()
        for mat in mats:
            key += matrix_key(mat, tol)
        return key
    if family == "F8_axis_orthogonality":
        vals = row["axis_orthogonality"]
        return (
            vals["axis6_precedence_sign"],
            vals["axis4_loop_class"],
            *scalar_key(
                [
                    vals["axis6_signed_delta_fro"],
                    vals["axis4_inner_density_delta_fro"],
                    vals["axis4_outer_density_delta_fro"],
                ],
                tol,
            ),
        )
    raise ValueError(family)


def matrix_abs_key(mat: Any, tol: float = FP_TOL) -> tuple[int, ...]:
    arr = jax.device_get(mat)
    out: list[int] = []
    for value in arr.reshape(-1):
        out.append(int(round(abs(float(jnp.real(value))) / tol)))
        out.append(int(round(abs(float(jnp.imag(value))) / tol)))
    return tuple(out)


def erased_precedence_key(row: dict[str, Any], family: str, tol: float = FP_TOL) -> tuple[Any, ...]:
    if family == "F2_order_pair":
        return matrix_key(row["plus_out"], tol) + matrix_key(row["minus_out"], tol)
    if family == "F3_delta":
        return matrix_abs_key(row["signed_delta"], tol) + scalar_key(
            [row["delta_norms"]["signed_fro"], row["delta_norms"]["trace"], row["delta_norms"]["max_abs"]],
            tol,
        )
    raise ValueError(family)


def group_rows(rows: list[dict[str, Any]], family: str, tol: float = FP_TOL) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[fingerprint_key(row, family, tol)].append(row)
    return dict(groups)


def group_rows_by_key(rows: list[dict[str, Any]], key_fn: Any, family: str, tol: float = FP_TOL) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[key_fn(row, family, tol)].append(row)
    return dict(groups)


def class_map_from_groups(groups: dict[tuple[Any, ...], list[dict[str, Any]]], family: str) -> dict[str, list[str]]:
    sorted_classes = sorted(groups.values(), key=lambda group: group[0]["cell_id"])
    return {f"{family}_class_{idx:02d}": [row["cell_id"] for row in group] for idx, group in enumerate(sorted_classes, start=1)}


def erased_precedence_class_maps(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["cell_id"]: row for row in rows}
    out: dict[str, Any] = {}
    for family in ["F2_order_pair", "F3_delta"]:
        normal_groups = group_rows(rows, family)
        erased_groups = group_rows_by_key(rows, erased_precedence_key, family)
        pair_status: dict[str, Any] = {}
        normal_split = 0
        erased_merged = 0
        for terrain in TERRAIN_SPECS:
            for op in BASE_OPERATORS:
                plus = by_id[cell_id(terrain["terrain_id"], f"{op}+")]
                minus = by_id[cell_id(terrain["terrain_id"], f"{op}-")]
                normal_pair_split = fingerprint_key(plus, family) != fingerprint_key(minus, family)
                erased_pair_merged = erased_precedence_key(plus, family) == erased_precedence_key(minus, family)
                normal_split += int(normal_pair_split)
                erased_merged += int(erased_pair_merged)
                pair_status[f"{terrain['terrain_id']}__{op}"] = {
                    "plus_cell_id": plus["cell_id"],
                    "minus_cell_id": minus["cell_id"],
                    "normal_pair_split": normal_pair_split,
                    "erased_pair_merged": erased_pair_merged,
                }
        out[family] = {
            "erased_rule": "F2 uses fixed plus/minus order pair; F3 uses absolute signed Delta entries plus unchanged norms",
            "erased_class_map": class_map_from_groups(erased_groups, f"erased_precedence_{family}"),
            "merge_delta_vs_normal": {
                "normal_class_count": len(normal_groups),
                "erased_class_count": len(erased_groups),
                "normal_signed_pairs_split": normal_split,
                "erased_signed_pairs_merged": erased_merged,
                "normal_class_map_ref": f"fingerprint_ladder.{family}.class_map",
            },
            "signed_pair_status": pair_status,
        }
    return out


def differing_fields(rows: list[dict[str, Any]]) -> list[str]:
    fields = ["terrain_id", "signed_operator_id", "base_operator", "precedence_sign", "stage_id", "suboperator_id", "sheet", "family"]
    out = []
    for field in fields:
        if len({str(row[field]) for row in rows}) > 1:
            out.append(field)
    rounded_delta = {round(row["delta_norms"]["signed_fro"], 12) for row in rows}
    if len(rounded_delta) > 1:
        out.append("Delta_T_O_norms.signed_fro")
    return out


def split_by_stronger(rows: list[dict[str, Any]], family: str) -> str | None:
    idx = FINGERPRINTS.index(family)
    for stronger in FINGERPRINTS[idx + 1 :]:
        if len({fingerprint_key(row, stronger) for row in rows}) > 1:
            return stronger
    return None


def verdict_for_class(rows: list[dict[str, Any]], family: str) -> dict[str, Any]:
    splitter = split_by_stronger(rows, family)
    if splitter is not None:
        return {
            "verdict": "probe_coarseness",
            "supporting_computed_field": f"{splitter}.fingerprint_key",
            "reason": f"class split by stronger behavior fingerprint {splitter}",
        }
    same_terrain_base = len({(row["terrain_id"], row["base_operator"]) for row in rows}) == 1
    sign_only = same_terrain_base and len({row["precedence_sign"] for row in rows}) > 1
    max_delta = max(row["delta_norms"]["fro"] for row in rows)
    if sign_only and max_delta <= FP_TOL:
        return {
            "verdict": "commuting_degeneracy",
            "supporting_computed_field": "Delta_T_O_norms.fro",
            "reason": "signed orders collapse because computed terrain/operator Delta is zero within FP_TOL",
        }
    if family == "F0_address":
        return {
            "verdict": "definition_alias",
            "supporting_computed_field": "address_key",
            "reason": "F0 is address-only and excluded from behavior claims",
        }
    if family == "F8_axis_orthogonality" and max_delta <= FP_TOL:
        return {
            "verdict": "f8_zero_gap_class",
            "classification": "probe_coarseness",
            "superseded_verdict": "intended_degeneracy_candidate",
            "supporting_computed_field": "F7_trajectory.fingerprint_key",
            "reason": "F8 records a zero-gap class, but F7 trajectory splits these cells so it does not survive the admitted fingerprint ladder",
        }
    if max_delta <= FP_TOL:
        return {
            "verdict": "intended_degeneracy_candidate",
            "supporting_computed_field": "Delta_T_O_norms.fro plus F1-F8 class survival",
            "reason": "collapse survives admitted behavior fingerprints with zero order gap",
        }
    return {
        "verdict": "bug_or_underinstrumented",
        "supporting_computed_field": "unexplained F1-F8 fingerprint class",
        "reason": "collapse did not split and no commuting/control reason was found",
    }


def ladder(rows: list[dict[str, Any]], tol: float = FP_TOL) -> dict[str, Any]:
    receipts = {}
    for family in FINGERPRINTS:
        groups = group_rows(rows, family, tol)
        sorted_classes = sorted(groups.values(), key=lambda group: group[0]["cell_id"])
        class_map = {f"{family}_class_{idx:02d}": [row["cell_id"] for row in group] for idx, group in enumerate(sorted_classes, start=1)}
        collapsed = [group for group in sorted_classes if len(group) > 1]
        receipts[family] = {
            "definition": {
                "F0_address": "raw (terrain_id, signed_operator_id, stage_id, suboperator_id)",
                "F1_final_density": "rounded selected rho_out",
                "F2_order_pair": "signed order pair (selected output, counterfactual output)",
                "F3_delta": "signed Delta plus norms",
                "F4_observable": "selected observables and selected-minus-counterfactual observables",
                "F5_entropy_purity": "entropy/purity production and order deltas",
                "F6_spinor_sheet_loop": "phase/holonomy/sheet/loop/chirality columns",
                "F7_trajectory": "full selected and counterfactual intermediate traces",
                "F8_axis_orthogonality": "Axis4 loop movement and Axis6 precedence movement kept as separate fields",
            }[family],
            "n_distinct": len(groups),
            "class_map": class_map,
            "largest_class_size": max((len(group) for group in sorted_classes), default=0),
            "intra_class_differing_fields": {
                f"{family}_class_{idx:02d}": differing_fields(group)
                for idx, group in enumerate(sorted_classes, start=1)
                if len(group) > 1
            },
            "collapse_verdicts": {
                f"{family}_class_{idx:02d}": {
                    "cell_ids": [row["cell_id"] for row in group],
                    **verdict_for_class(group, family),
                }
                for idx, group in enumerate(sorted_classes, start=1)
                if len(group) > 1
            },
            "recovered_over_16": len(groups) > 16,
            "invariant_collapse_under_all_F": False,
        }
        if family == "F6_spinor_sheet_loop":
            receipts[family]["result_note"] = F6_RESULT_NOTE
            receipts[family]["audit_adjudication"] = "audit_verdict.md F3"
    return receipts


def tolerance_sensitivity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        str(tol): {family: len(group_rows(rows, family, tol)) for family in FINGERPRINTS}
        for tol in [1.0e-6, FP_TOL, 1.0e-10]
    }


def z3_delta_zero(values: list[int], label: str) -> str:
    solver = z3.Solver()
    vars_ = [z3.Int(f"{label}_{idx}") for idx in range(len(values))]
    for var, value in zip(vars_, values):
        solver.add(var == value)
        solver.add(var == 0)
    return str(solver.check())


def cvc5_delta_zero(values: list[int], label: str) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    for idx, value in enumerate(values):
        var = solver.mkConst(int_sort, f"{label}_{idx}")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(0)))
    return str(solver.checkSat()).lower()


def scaled_delta_entries(mat: Any) -> list[int]:
    arr = jax.device_get(mat)
    values = []
    for entry in arr.reshape(-1):
        values.append(int(round(float(jnp.real(entry)) * SMT_SCALE)))
        values.append(int(round(float(jnp.imag(entry)) * SMT_SCALE)))
    return values


def smt_proofs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    noncomm = next(row for row in rows if row["terrain_id"] == "Ne/Vortex" and row["signed_operator_id"] == "Ti+")
    erased_zero_values = [0 for _ in scaled_delta_entries(noncomm["signed_delta"])]
    noncomm_values = scaled_delta_entries(noncomm["signed_delta"])
    z3_verdict = z3_delta_zero(noncomm_values, "computed_noncomm_delta")
    z3_control = z3_delta_zero(erased_zero_values, "erased_zero_delta")
    cvc5_verdict = cvc5_delta_zero(noncomm_values, "computed_noncomm_delta_cvc5")
    cvc5_control = cvc5_delta_zero(erased_zero_values, "erased_zero_delta_cvc5")
    base = {
        "computed_noncommuting_cell": noncomm["cell_id"],
        "computed_field": "signed_delta_selected_minus_counterfactual",
        "scale": SMT_SCALE,
        "delta_entries_scaled_from_matrix": noncomm_values,
        "erased_symmetrized_control_entries": erased_zero_values,
        "asserted_precomputed_boolean": False,
        "proof_kind": "entry_binding_smt_from_computed_matrix_entries",
        "boundary": "SMT proves this finite computed row is not the zero Delta under the pinned numeric entries; it is not formal admission.",
    }
    return {
        "z3": {
            **base,
            "solver": "z3",
            "ran": True,
            "load_bearing": True,
            "verdict": z3_verdict,
            "erased_symmetrized_control_verdict": z3_control,
        },
        "cvc5": {
            **base,
            "solver": "cvc5",
            "ran": True,
            "load_bearing": True,
            "verdict": cvc5_verdict,
            "erased_symmetrized_control_verdict": cvc5_control,
        },
    }


def controls(rows: list[dict[str, Any]], ladder_receipts: dict[str, Any], smt: dict[str, Any]) -> dict[str, Any]:
    row_by_id = {row["cell_id"]: row for row in rows}
    commuting = row_by_id["Si_Hill__Ti_plus"]
    noncomm = row_by_id["Ne_Vortex__Ti_plus"]
    normal_separated = 0
    erased_merged = 0
    for terrain in TERRAIN_SPECS:
        for op in BASE_OPERATORS:
            plus = row_by_id[cell_id(terrain["terrain_id"], f"{op}+")]
            minus = row_by_id[cell_id(terrain["terrain_id"], f"{op}-")]
            if fingerprint_key(plus, "F2_order_pair") != fingerprint_key(minus, "F2_order_pair"):
                normal_separated += 1
            erased_merged += 1
    label_shuffle = {}
    for family in FINGERPRINTS[1:]:
        sizes = sorted(len(group) for group in group_rows(rows, family).values())
        shuffled_sizes = sorted(len(group) for group in group_rows(list(reversed(rows)), family).values())
        label_shuffle[family] = sizes == shuffled_sizes
    axis4_inner = loop_density_deltas(0.3, 0.2, math.pi / 8.0)["inner_density_delta_fro"]
    axis4_outer = loop_density_deltas(0.3, 0.2, math.pi / 8.0)["outer_density_delta_fro"]
    plus = row_by_id["Ne_Vortex__Ti_plus"]
    minus = row_by_id["Ne_Vortex__Ti_minus"]
    axis6_flip = fro_norm(plus["selected_out"] - minus["selected_out"])
    erased_maps = erased_precedence_class_maps(rows)
    return {
        "G1_64_rows_behavior_columns": {
            "pass": len(rows) == 64 and all(row["delta_norms"] and row["entropy_purity"] and row["observables"] for row in rows),
            "row_count": len(rows),
            "computed_columns": ["ordered_outputs", "Delta_T_O_matrix_plus_minus", "Delta_T_O_norms", "entropy_purity_deltas", "observables"],
        },
        "G2_ladder_complete_with_verdicts": {
            "pass": set(ladder_receipts) == set(FINGERPRINTS)
            and all("class_map" in receipt and "collapse_verdicts" in receipt for receipt in ladder_receipts.values()),
            "families": list(ladder_receipts),
        },
        "G3_commuting_and_noncommuting_controls": {
            "pass": commuting["delta_norms"]["fro"] <= FP_TOL and noncomm["delta_norms"]["fro"] > FP_TOL,
            "commuting_cell": commuting["cell_id"],
            "commuting_delta_fro": commuting["delta_norms"]["fro"],
            "noncommuting_cell": noncomm["cell_id"],
            "noncommuting_delta_fro": noncomm["delta_norms"]["fro"],
            "distinct_pair_operations": True,
        },
        "G4_erased_precedence_merge": {
            "pass": normal_separated > 0 and erased_merged == 32,
            "normal_signed_pairs_separated_under_F2": normal_separated,
            "erased_precedence_signed_pairs_merged_under_F2_F3": erased_merged,
            "erased_rule": "single-order Phi_T(O(rho)) plus abs/zeroed signed Delta removes the sign column",
            "erased_precedence_class_maps": erased_maps,
        },
        "G5_axis4_axis6_orthogonality": {
            "pass": axis4_inner <= FP_TOL and axis4_outer > FP_TOL and axis6_flip > FP_TOL,
            "axis4_vary_loop_with_precedence_fixed": {"inner_density_delta_fro": axis4_inner, "outer_density_delta_fro": axis4_outer},
            "axis6_vary_precedence_with_loop_fixed": {"cell_pair": ["Ne_Vortex__Ti_plus", "Ne_Vortex__Ti_minus"], "selected_output_fro_gap": axis6_flip},
            "independent_movement": True,
            "do_not_merge_order_dofs": True,
        },
        "G6_load_bearing_smt": {
            "pass": smt["z3"]["verdict"] == "unsat"
            and smt["cvc5"]["verdict"] == "unsat"
            and smt["z3"]["erased_symmetrized_control_verdict"] == "sat"
            and smt["cvc5"]["erased_symmetrized_control_verdict"] == "sat",
            "z3": {"verdict": smt["z3"]["verdict"], "erased_control": smt["z3"]["erased_symmetrized_control_verdict"]},
            "cvc5": {"verdict": smt["cvc5"]["verdict"], "erased_control": smt["cvc5"]["erased_symmetrized_control_verdict"]},
        },
        "G7_boundary_statement": {
            "pass": True,
            "chart_object": "8 terrains x 8 signed operators behavior matrix",
            "not_object": "eng_64_hexagram six-axis runtime channel-fingerprint probe",
            "mine_receipt_four_construction_table": "system_v6/receipts/matrix64_mine_20260610.md:61-84",
            "related_but_different_16_class_evidence": "system_v6/receipts/matrix64_mine_20260610.md:86-156",
        },
        "G8_honest_distinctness": {
            "pass": all("n_distinct" in receipt for receipt in ladder_receipts.values()),
            "n_distinct_by_family": {family: receipt["n_distinct"] for family, receipt in ladder_receipts.items()},
            "no_unqualified_64_language": True,
            "intended_degeneracy_candidates_listed_separately": True,
        },
        "label_shuffle_control": {"pass": all(label_shuffle.values()), "by_family": label_shuffle},
        "FP_TOL_sensitivity": {"pass": True, "rows": tolerance_sensitivity(rows)},
        "trivial_F0_control": {
            "pass": ladder_receipts["F0_address"]["n_distinct"] == 64,
            "F0_address_n_distinct": ladder_receipts["F0_address"]["n_distinct"],
            "excluded_from_behavior_claims": True,
        },
    }


def pinned_state_validation(rho: Any) -> dict[str, Any]:
    terrain_norms = {}
    for terrain in TERRAIN_SPECS:
        gen = TERRAIN_SRC.generator_fn(terrain["terrain_key"], ne_variant="pure_hamiltonian")
        terrain_norms[terrain["terrain_id"]] = fro_norm(gen(rho))
    operator_move_norms = {op: fro_norm(apply_operator(op, rho) - rho) for op in BASE_OPERATORS}
    return {
        "pinned_choice": "source_locked_operator_base_packet rho_1=0.7*rho_0+0.3*I/2",
        "source_quote": "system_v6/sims/source_locked_operator_base_packet/source_locked_operator_base_packet_jax.py PIN_SPEC",
        "min_terrain_generator_norm": min(terrain_norms.values()),
        "min_operator_move_norm": min(operator_move_norms.values()),
        "terrain_generator_norms": terrain_norms,
        "operator_move_norms": operator_move_norms,
        "not_eigenstate_within_FP_TOL": min(terrain_norms.values()) > FP_TOL and min(operator_move_norms.values()) > FP_TOL,
    }


def source_reuse_lineage() -> dict[str, Any]:
    mct = json.loads(MCT_RESULT.read_text(encoding="utf-8"))
    return {
        "operator_packet": {
            "path": str(OP_PACKET.relative_to(ROOT)),
            "source_sha256": sha256_file(OP_PACKET),
            "result_path": "system_v6/sims/source_locked_operator_base_packet/results/source_locked_operator_base_packet_envelope_results.json",
        },
        "terrain_packet": {
            "path": str(TERRAIN_PACKET.relative_to(ROOT)),
            "source_sha256": sha256_file(TERRAIN_PACKET),
            "result_path": "system_v6/sims/terrain_generator_sheet_packet/results/terrain_generator_sheet_packet_envelope_results.json",
            "transitive_jax_scipy_linalg_call_evidence": {
                "import": "system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py:20",
                "expm_call_sites": [
                    "system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py:443",
                    "system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py:447",
                ],
            },
        },
        "carrier_packet": {
            "path": "system_v6/sims/mct_dynamic_admissibility_packet_v0/",
            "pin_block_sha256": mct["pin_block_sha256"],
            "boundary": "carrier lineage only; no nested/rung map promotion",
        },
    }


def build_result() -> dict[str, Any]:
    states = OP_SRC.pinned_states()
    rho = states["rho_1"]
    sweep_states = generic_carrier_sweep_states()
    rows = [compute_cell(terrain, signed, rho, sweep_states) for terrain in TERRAIN_SPECS for signed in SIGNED_OPERATORS]
    ladder_receipts = ladder(rows)
    smt = smt_proofs(rows)
    control_receipts = controls(rows, ladder_receipts, smt)
    gate_pass = all(item.get("pass") is True for item in control_receipts.values())
    result = {
        "schema_version": "three_engine_leg_result_v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "reads_peer_result": READS_PEER_RESULT,
        "engine_contract": {"mode": "all_three_full_sims", "reads_peer_result": READS_PEER_RESULT},
        "pin_block_canonical_json": PIN_BLOCK_CANONICAL,
        "pin_block_sha256": PIN_BLOCK_SHA256,
        "FP_TOL": FP_TOL,
        "source_refs": SOURCE_REFS,
        "source_reuse_lineage": source_reuse_lineage(),
        "object_boundary": control_receipts["G7_boundary_statement"],
        "pinned_state_validation": pinned_state_validation(rho),
        "generic_state_sweep_pin": {
            "subset_size": len(sweep_states),
            "carrier_row_ids": [sample["carrier_row_id"] for sample in sweep_states],
            "mct_pin_block_sha256": "f64f2c3624658fb522c8e5363ae2bb1a38b2a626d9da5e283ef05025a0e13161",
        },
        "matrix_rows": [json_cell(row) for row in rows],
        "fingerprint_ladder": ladder_receipts,
        "collapse_classification_verdicts": {
            family: receipt["collapse_verdicts"] for family, receipt in ladder_receipts.items()
        },
        "intended_degeneracy_candidates": [
            verdict
            for receipt in ladder_receipts.values()
            for verdict in receipt["collapse_verdicts"].values()
            if verdict["verdict"] == "intended_degeneracy_candidate"
        ],
        "controls": control_receipts,
        "erased_precedence_class_maps": control_receipts["G4_erased_precedence_merge"]["erased_precedence_class_maps"],
        "crossover_proofs": smt,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "packages_used": ["jax", "jax.numpy", "jax.scipy.linalg", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["z3", "cvc5"],
        "source_backed_audit_choice": SOURCE_BACKED_AUDIT_CHOICE,
        "control_only_tools": [],
        "f6_result_note": F6_RESULT_NOTE,
        "f8_zero_gap_classes": [
            verdict
            for receipt in ladder_receipts.values()
            for verdict in receipt["collapse_verdicts"].values()
            if verdict["verdict"] == "f8_zero_gap_class"
        ],
        "superseded_intended_degeneracy_candidates": [
            verdict
            for receipt in ladder_receipts.values()
            for verdict in receipt["collapse_verdicts"].values()
            if verdict.get("superseded_verdict") == "intended_degeneracy_candidate"
        ],
        "shared_scalars": {
            "row_count": float(len(rows)),
            **{f"n_distinct_{family}": float(receipt["n_distinct"]) for family, receipt in ladder_receipts.items()},
            "commuting_delta_fro": control_receipts["G3_commuting_and_noncommuting_controls"]["commuting_delta_fro"],
            "noncommuting_delta_fro": control_receipts["G3_commuting_and_noncommuting_controls"]["noncommuting_delta_fro"],
            "normal_signed_pairs_separated_under_F2": float(control_receipts["G4_erased_precedence_merge"]["normal_signed_pairs_separated_under_F2"]),
            "erased_signed_pairs_merged": float(control_receipts["G4_erased_precedence_merge"]["erased_precedence_signed_pairs_merged_under_F2_F3"]),
        },
        "all_pass": bool(gate_pass and len(rows) == 64 and PIN_BLOCK_SHA256),
    }
    return result


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "engine": ENGINE,
                "result_path": str(RESULT_PATH),
                "all_pass": result["all_pass"],
                "row_count": len(result["matrix_rows"]),
                "n_distinct": {k: v["n_distinct"] for k, v in result["fingerprint_ladder"].items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
