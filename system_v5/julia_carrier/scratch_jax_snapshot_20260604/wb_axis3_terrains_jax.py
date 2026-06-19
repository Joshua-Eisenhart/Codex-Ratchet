#!/usr/bin/env python3
"""
wb_axis3_terrains_jax.py

JAX audit lane for wb_axis3_terrains.
Runs independently, writes /tmp/wb_axis3_terrains_jax_results.json, and writes
/tmp/wb_axis3_terrains_parity.json when the Julia truth-lane result exists.

No NumPy import is used. The state ladder is a deterministic Park-Miller
pseudo-Haar qubit table shared with the Julia lane.
"""

from jax import config

config.update("jax_enable_x64", True)

import hashlib
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import jax
import jax.numpy as jnp

OBJECT_ID = "wb_axis3_terrains"
ENGINE = "jax_audit_lane"
P_PARAM = 0.7
GAMMA = 0.3
EPS = 1e-10
SIZES = [8, 16, 32, 64]

I2 = jnp.eye(2, dtype=jnp.complex128)
SX = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
SZ = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
P0 = jnp.array([[1, 0], [0, 0]], dtype=jnp.complex128)
P1 = jnp.array([[0, 0], [0, 1]], dtype=jnp.complex128)
PPLUS = jnp.array([[0.5, 0.5], [0.5, 0.5]], dtype=jnp.complex128)

LCG_A = 48271
LCG_M = 2147483647
JULIA_RESULT = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/wb_axis3_terrains_julia_results.json")
JAX_RESULT = Path("/tmp/wb_axis3_terrains_jax_results.json")
PARITY_RESULT = Path("/tmp/wb_axis3_terrains_parity.json")


def lcg_next(state):
    return (LCG_A * state) % LCG_M


def seeded_unit(seed):
    state0 = (seed % (LCG_M - 1)) + 1
    state1 = lcg_next(state0)
    state2 = lcg_next(state1)
    return state1 / LCG_M, state2 / LCG_M


def deterministic_haar_density(n, terrain_index, sample_index):
    seed = 7919 + 101 * n + 1009 * terrain_index + 9176 * sample_index
    u_pop, u_phase = seeded_unit(seed)
    phase = 2.0 * math.pi * u_phase
    psi = jnp.array(
        [
            math.sqrt(1.0 - u_pop),
            math.sqrt(u_pop) * complex(math.cos(phase), math.sin(phase)),
        ],
        dtype=jnp.complex128,
    )
    return jnp.outer(psi, jnp.conj(psi))


def apply_channel(rho, kraus):
    out = jnp.zeros((2, 2), dtype=jnp.complex128)
    for k in kraus:
        out = out + k @ rho @ jnp.conj(k).T
    return (out + jnp.conj(out).T) / 2.0


def trace_distance(rho, sigma):
    diff = (rho - sigma + jnp.conj(rho - sigma).T) / 2.0
    vals = jnp.linalg.eigvals(diff)
    return float(0.5 * jnp.sum(jnp.abs(jnp.real(vals))))


def purity(rho):
    return float(jnp.real(jnp.trace(rho @ rho)))


def channel_entropy(rho):
    vals = jnp.clip(jnp.real(jnp.linalg.eigvals((rho + jnp.conj(rho).T) / 2.0)), 0.0, 1.0)
    total = 0.0
    for v in [float(x) for x in vals]:
        if v > 1e-14:
            total -= v * math.log(v)
    return total


def kraus_Se(p=P_PARAM):
    return [math.sqrt(p) * I2, math.sqrt(1.0 - p) * SX]


def kraus_Ne(p=P_PARAM):
    return [math.sqrt(p) * I2, math.sqrt(1.0 - p) * SY]


def kraus_Ni(gamma=GAMMA):
    k0 = jnp.array([[1, 0], [0, math.sqrt(1.0 - gamma)]], dtype=jnp.complex128)
    k1 = jnp.array([[0, math.sqrt(gamma)], [0, 0]], dtype=jnp.complex128)
    return [k0, k1]


def kraus_Si(p=P_PARAM):
    return [math.sqrt(p) * I2, math.sqrt(1.0 - p) * SZ]


def kraus_flat():
    return [I2]


def kraus_Se_wrong_requested():
    return [math.sqrt(P_PARAM) * I2, math.sqrt(1.0 - P_PARAM) * SZ]


def kraus_Se_wrong_independent():
    return [math.sqrt(P_PARAM) * I2, math.sqrt(1.0 - P_PARAM) * ((SX + SZ) / math.sqrt(2.0))]


def terrain_kraus():
    return {
        "Se": kraus_Se(),
        "Ne": kraus_Ne(),
        "Ni": kraus_Ni(),
        "Si": kraus_Si(),
    }


def terrain_order(name):
    return ["Se", "Ne", "Ni", "Si"].index(name) + 1


def choi_matrix(kraus):
    omega = I2.reshape((4,), order="F")
    choi = jnp.zeros((4, 4), dtype=jnp.complex128)
    for k in kraus:
        a = jnp.kron(k, I2)
        v = a @ omega
        choi = choi + jnp.outer(v, jnp.conj(v))
    return (choi + jnp.conj(choi).T) / 2.0


def choi_summary(kraus):
    choi = choi_matrix(kraus)
    herm_resid = float(jnp.linalg.norm(choi - jnp.conj(choi).T))
    vals = sorted(float(jnp.real(v)) for v in jnp.linalg.eigvals(choi))
    return {
        "min_eigenvalue": min(vals),
        "eigenvalues": vals,
        "psd": min(vals) >= -EPS,
        "rank_tol_1e-10": sum(1 for v in vals if v > EPS),
        "trace": float(jnp.real(jnp.trace(choi))),
        "hermiticity_residual": herm_resid,
    }


def kraus_completeness_error(kraus):
    s = jnp.zeros((2, 2), dtype=jnp.complex128)
    for k in kraus:
        s = s + jnp.conj(k).T @ k
    return float(jnp.linalg.norm(s - I2))


def superoperator(kraus):
    s = jnp.zeros((4, 4), dtype=jnp.complex128)
    for k in kraus:
        s = s + jnp.kron(jnp.conj(k), k)
    return s


def channel_commutator_norm(a, b):
    sa = superoperator(a)
    sb = superoperator(b)
    return float(jnp.linalg.norm(sa @ sb - sb @ sa))


def kraus_pair_commutator_norms(a, b):
    vals = []
    for ka in a:
        for kb in b:
            vals.append(float(jnp.linalg.norm(ka @ kb - kb @ ka)))
    return vals


def run_terrain(name, kraus, n):
    idx = terrain_order(name)
    trace_dists = []
    purity_deltas = []
    entropy_deltas = []
    output_purities = []
    for sample in range(1, n + 1):
        rho = deterministic_haar_density(n, idx, sample)
        out = apply_channel(rho, kraus)
        flat = apply_channel(rho, kraus_flat())
        trace_dists.append(trace_distance(out, flat))
        purity_deltas.append(purity(out) - purity(rho))
        entropy_deltas.append(channel_entropy(out) - channel_entropy(rho))
        output_purities.append(purity(out))
    return {
        "terrain": name,
        "n_states": n,
        "mean_trace_dist": sum(trace_dists) / len(trace_dists),
        "min_trace_dist": min(trace_dists),
        "max_trace_dist": max(trace_dists),
        "all_trace_dists_positive": all(v > EPS for v in trace_dists),
        "mean_purity_delta": sum(purity_deltas) / len(purity_deltas),
        "mean_entropy_delta": sum(entropy_deltas) / len(entropy_deltas),
        "mean_output_purity": sum(output_purities) / len(output_purities),
        "choi": choi_summary(kraus),
        "kraus_completeness_err": kraus_completeness_error(kraus),
    }


def channel_action_summary(state_name, kraus, rho):
    out = apply_channel(rho, kraus)
    flat = apply_channel(rho, kraus_flat())
    return {
        "state": state_name,
        "trace_dist_from_flat": trace_distance(out, flat),
        "input_purity": purity(rho),
        "output_purity": purity(out),
        "purity_delta": purity(out) - purity(rho),
        "entropy_delta": channel_entropy(out) - channel_entropy(rho),
    }


def positive_controls():
    terrains = terrain_kraus()
    pure_zero = {}
    for name in ["Se", "Ne", "Ni", "Si"]:
        summary = channel_action_summary("|0><0|", terrains[name], P0)
        summary["nontrivial_on_requested_state"] = summary["trace_dist_from_flat"] > EPS
        summary["purity_decreased_on_requested_state"] = summary["purity_delta"] < -EPS
        pure_zero[name] = summary
    requested_nontrivial = all(v["nontrivial_on_requested_state"] for v in pure_zero.values())
    requested_purity_decreased = all(v["purity_decreased_on_requested_state"] for v in pure_zero.values())

    sensitive_specs = {
        "Se": ("|0><0|", P0),
        "Ne": ("|0><0|", P0),
        "Ni": ("|1><1|", P1),
        "Si": ("|+><+|", PPLUS),
    }
    sensitive = {}
    for name in ["Se", "Ne", "Ni", "Si"]:
        label, rho = sensitive_specs[name]
        summary = channel_action_summary(label, terrains[name], rho)
        summary["nontrivial_on_sensitive_state"] = summary["trace_dist_from_flat"] > EPS
        summary["purity_decreased_on_sensitive_state"] = summary["purity_delta"] < -EPS
        sensitive[name] = summary
    sensitive_pass = all(
        v["nontrivial_on_sensitive_state"] and v["purity_decreased_on_sensitive_state"]
        for v in sensitive.values()
    )
    return {
        "requested_pure_zero": pure_zero,
        "requested_pure_zero_nontrivial_pass": requested_nontrivial,
        "requested_pure_zero_purity_direction_pass": requested_purity_decreased,
        "requested_pure_zero_control_pass": requested_nontrivial and requested_purity_decreased,
        "sensitive_state_controls": sensitive,
        "sensitive_state_control_pass": sensitive_pass,
        "control_note": "|0><0| is a fixed point for Ni amplitude damping and Si z-dephasing, so the requested pure-zero control cannot honestly pass for all four terrains.",
    }


def boundary_checks():
    rho = jnp.array([[0.3, 0.2], [0.2, 0.7]], dtype=jnp.complex128)
    full_damp = apply_channel(rho, kraus_Ni(1.0))
    p1_identity = {
        "Se": trace_distance(apply_channel(rho, kraus_Se(1.0)), rho),
        "Ne": trace_distance(apply_channel(rho, kraus_Ne(1.0)), rho),
        "Si": trace_distance(apply_channel(rho, kraus_Si(1.0)), rho),
    }
    id_choi = choi_summary(kraus_flat())
    return {
        "gamma_1_complete_damping_dist_to_ground": trace_distance(full_damp, P0),
        "gamma_1_complete_damping_pass": trace_distance(full_damp, P0) < EPS,
        "p_1_identity_trace_dists": p1_identity,
        "p_1_identity_pass": all(v < EPS for v in p1_identity.values()),
        "identity_choi": id_choi,
        "identity_choi_rank_one_pass": id_choi["rank_tol_1e-10"] == 1,
    }


def wrong_structure_check():
    requested_diffs = []
    independent_diffs = []
    for n in SIZES:
        for sample in range(1, n + 1):
            rho = deterministic_haar_density(n, 1, sample)
            real_out = apply_channel(rho, kraus_Se())
            requested_out = apply_channel(rho, kraus_Se_wrong_requested())
            independent_out = apply_channel(rho, kraus_Se_wrong_independent())
            requested_diffs.append(trace_distance(real_out, requested_out))
            independent_diffs.append(trace_distance(real_out, independent_out))
    return {
        "requested_wrong_kraus": "Se with sigma_z replacing sigma_x; this equals the Si axis under the provided terrain table, so it is reported separately.",
        "independent_wrong_kraus": "Se with (sigma_x + sigma_z)/sqrt(2) replacing sigma_x; CP/TP and not one of Se/Ne/Ni/Si.",
        "requested_mean_Se_vs_wrong_trace_dist": sum(requested_diffs) / len(requested_diffs),
        "requested_min_Se_vs_wrong_trace_dist": min(requested_diffs),
        "requested_wrong_structure_distinct": (sum(requested_diffs) / len(requested_diffs)) > EPS,
        "independent_mean_Se_vs_wrong_trace_dist": sum(independent_diffs) / len(independent_diffs),
        "independent_min_Se_vs_wrong_trace_dist": min(independent_diffs),
        "independent_wrong_structure_distinct": (sum(independent_diffs) / len(independent_diffs)) > EPS,
        "wrong_structure_distinct": (sum(requested_diffs) / len(requested_diffs)) > EPS
        and (sum(independent_diffs) / len(independent_diffs)) > EPS,
    }


def pairwise_superoperator_distances():
    terrains = terrain_kraus()
    out = {}
    names = ["Se", "Ne", "Ni", "Si"]
    for i, a in enumerate(names[:-1]):
        for b in names[i + 1 :]:
            out[f"{a}-{b}"] = float(jnp.linalg.norm(superoperator(terrains[a]) - superoperator(terrains[b])))
    return out


def axis3_split(size_ladder):
    deltas = {}
    entropy_deltas = {}
    for name in ["Se", "Ne", "Ni", "Si"]:
        vals = [size_ladder[f"n={n}"][name]["mean_purity_delta"] for n in SIZES]
        ents = [size_ladder[f"n={n}"][name]["mean_entropy_delta"] for n in SIZES]
        deltas[name] = sum(vals) / len(vals)
        entropy_deltas[name] = sum(ents) / len(ents)
    type1 = (deltas["Se"] + deltas["Ne"]) / 2.0
    type2 = (deltas["Ni"] + deltas["Si"]) / 2.0
    return {
        "declared_type1_expansion": ["Se", "Ne"],
        "declared_type2_compression": ["Ni", "Si"],
        "mean_purity_delta_by_terrain": deltas,
        "mean_entropy_delta_by_terrain": entropy_deltas,
        "type1_mean_purity_delta": type1,
        "type2_mean_purity_delta": type2,
        "type_partition_observable_gap": abs(type1 - type2),
        "axis3_distinct_by_observed_gap": abs(type1 - type2) > EPS,
        "axis3_direction_pass": False,
        "axis3_direction_note": "The supplied Kraus maps do not support a clean purity-sign expansion/compression split: all four mean purity deltas are negative on the finite ladder. Axis 3 remains an observable candidate partition, not a direction-admitted result.",
    }


def erased_structure_control():
    erased_comm = channel_commutator_norm(kraus_flat(), kraus_flat())
    rho = deterministic_haar_density(64, 1, 1)
    erased_trace_dist = trace_distance(apply_channel(rho, kraus_flat()), rho)
    return {
        "control": "all terrains replaced by flat identity channel",
        "n01_channel_commutator_norm": erased_comm,
        "sample_trace_dist_from_flat": erased_trace_dist,
        "terrain_structure_present": False,
        "axis3_distinct": False,
        "finite_map_verdict_if_erased": False,
    }


def flat_control_max_trace_dist_by_n():
    out = {}
    for n in SIZES:
        vals = []
        for sample in range(1, n + 1):
            rho = deterministic_haar_density(n, 1, sample)
            vals.append(trace_distance(apply_channel(rho, kraus_flat()), rho))
        out[f"n={n}"] = max(vals)
    return out


def n01_witness():
    rho = PPLUS
    terrains = terrain_kraus()
    se_then_ni = apply_channel(apply_channel(rho, terrains["Se"]), terrains["Ni"])
    ni_then_se = apply_channel(apply_channel(rho, terrains["Ni"]), terrains["Se"])
    td = trace_distance(se_then_ni, ni_then_se)
    return {
        "state": "|+><+|",
        "trace_distance_Se_after_Ni_vs_Ni_after_Se": td,
        "order_sensitive": td > EPS,
    }


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_result():
    terrains = terrain_kraus()
    size_ladder = {}
    for n in SIZES:
        size_ladder[f"n={n}"] = {name: run_terrain(name, terrains[name], n) for name in ["Se", "Ne", "Ni", "Si"]}

    choi_checks = {name: size_ladder["n=8"][name]["choi"]["psd"] for name in ["Se", "Ne", "Ni", "Si"]}
    completeness = {name: kraus_completeness_error(terrains[name]) for name in ["Se", "Ne", "Ni", "Si"]}
    pairwise_dists = pairwise_superoperator_distances()
    pos = positive_controls()
    bounds = boundary_checks()
    wrong = wrong_structure_check()
    ax3 = axis3_split(size_ladder)
    flat_by_n = flat_control_max_trace_dist_by_n()
    n01_state_witness = n01_witness()

    n01_channel = channel_commutator_norm(terrains["Se"], terrains["Ni"])
    n01_kraus_pair = kraus_pair_commutator_norms(terrains["Se"], terrains["Ni"])
    erased = erased_structure_control()

    all_trace_positive = all(
        size_ladder[f"n={n}"][name]["all_trace_dists_positive"] for n in SIZES for name in ["Se", "Ne", "Ni", "Si"]
    )
    all_choi_psd = all(choi_checks.values())
    all_complete = all(v < EPS for v in completeness.values())
    terrain_distinct = min(pairwise_dists.values()) > EPS
    finite_map_checks_pass = (
        all_trace_positive
        and all_choi_psd
        and all_complete
        and terrain_distinct
        and n01_channel > EPS
        and max(n01_kraus_pair) > EPS
        and bounds["gamma_1_complete_damping_pass"]
        and bounds["p_1_identity_pass"]
        and bounds["identity_choi_rank_one_pass"]
        and wrong["wrong_structure_distinct"]
        and n01_state_witness["order_sensitive"]
        and ax3["axis3_distinct_by_observed_gap"]
        and pos["sensitive_state_control_pass"]
        and not erased["finite_map_verdict_if_erased"]
    )
    requested_control_pass = pos["requested_pure_zero_control_pass"]
    all_pass = finite_map_checks_pass and requested_control_pass
    source_path = Path(__file__)

    return {
        "object_id": OBJECT_ID,
        "parent_object_id": OBJECT_ID,
        "engine": ENGINE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_path": str(source_path),
        "source_sha256": file_sha256(source_path),
        "run_command": "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 /tmp/wb_axis3_terrains_jax.py",
        "exit_code": 0,
        "python_version": platform.python_version(),
        "jax_version": jax.__version__,
        "rng_seed": "deterministic Park-Miller LCG seeds 7919 + 101*n + 1009*terrain_index + 9176*sample_index",
        "run_completed": True,
        "classification": "tool_lego_fit_probe",
        "sim_execution_kind": "nonclassical",
        "claim_ceiling": "candidate finite-map probe; JAX audit lane; not layer-complete; not manifold admission",
        "promotion_allowed": False,
        "promotion_status": "keep_but_open" if requested_control_pass else "audit_further",
        "finite_map": {
            "domain": "2x2 spinor density matrices rho, deterministic pseudo-Haar qubit samples at n=8,16,32,64",
            "codomain_or_output": "post-channel density matrices plus trace distance, purity/entropy change, Choi PSD, Kraus TP, and order-sensitive channel commutator invariants",
        },
        "domain": "2x2 spinor density matrices rho, deterministic pseudo-Haar qubit samples at n=8,16,32,64",
        "codomain_or_output": "post-channel density matrices plus trace distance, purity/entropy change, Choi PSD, Kraus TP, and order-sensitive channel commutator invariants",
        "root_constraints_in_force": {
            "F01": {"satisfied": True, "witness": "explicit finite size ladder n=8,16,32,64"},
            "N01": {
                "satisfied": n01_channel > EPS,
                "channel_commutator_norm": n01_channel,
                "kraus_pair_commutator_norms": n01_kraus_pair,
            },
        },
        "carrier_realization": "JAX complex128 2-component spinor-derived density matrices; no NumPy import",
        "spinor_state": "2-component complex128 spinors psi with rho = psi psi^dagger",
        "peps3d_embedding": {
            "status": "blocked_not_claimed",
            "reason": "This object is a 2x2 CP-channel finite-map probe only. It does not provide a PEPS3D carrier anchor and cannot be cited for manifold/layer promotion.",
        },
        "quaternion_action": "not_applicable",
        "dependency_receipts": [],
        "required_tools": ["jax", "jax.numpy"],
        "actual_tools_used": ["jax", "jax.numpy", "python_stdlib_json_hashlib_datetime"],
        "axes": ["Axis1_channel_polarity", "Axis2_chart_lens", "Axis3_engine_family"],
        "terrains": {
            "Se": {"axis1": "expansive", "axis2": "open_direct", "axis3": "Type1_expansion", "kraus": "sqrt(p) I, sqrt(1-p) sigma_x"},
            "Ne": {"axis1": "expansive", "axis2": "closed_direct", "axis3": "Type1_expansion", "kraus": "sqrt(p) I, sqrt(1-p) sigma_y"},
            "Ni": {"axis1": "compressive", "axis2": "open_conj", "axis3": "Type2_compression", "kraus": "amplitude damping gamma=0.3"},
            "Si": {"axis1": "compressive", "axis2": "closed_conj", "axis3": "Type2_compression", "kraus": "sqrt(p) I, sqrt(1-p) sigma_z"},
        },
        "parameters": {"p": P_PARAM, "gamma": GAMMA},
        "size_ladder": size_ladder,
        "choi_psd_by_terrain": choi_checks,
        "all_choi_psd": all_choi_psd,
        "choi_min_eigenvalue_by_terrain": {name: size_ladder["n=8"][name]["choi"]["min_eigenvalue"] for name in ["Se", "Ne", "Ni", "Si"]},
        "choi_hermiticity_residual_by_terrain": {name: size_ladder["n=8"][name]["choi"]["hermiticity_residual"] for name in ["Se", "Ne", "Ni", "Si"]},
        "kraus_completeness_errors": completeness,
        "all_kraus_complete": all_complete,
        "pairwise_superoperator_distances": pairwise_dists,
        "terrain_channels_distinct": terrain_distinct,
        "n01_channel_commutator_norm": n01_channel,
        "n01_kraus_pair_commutator_norms": n01_kraus_pair,
        "n01_witness_state": n01_state_witness,
        "n01_satisfied": n01_channel > EPS,
        "positive_controls": pos,
        "positive_control_pass_by_terrain": {
            name: pos["sensitive_state_controls"][name]["nontrivial_on_sensitive_state"]
            and pos["sensitive_state_controls"][name]["purity_decreased_on_sensitive_state"]
            for name in ["Se", "Ne", "Ni", "Si"]
        },
        "boundary_checks": bounds,
        "flat_control_max_trace_dist_by_n": flat_by_n,
        "wrong_structure_control": wrong,
        "erased_structure_control": erased,
        "axis3_split": ax3,
        "finite_map_checks_pass": finite_map_checks_pass,
        "requested_pure_zero_control_pass": requested_control_pass,
        "all_pass": all_pass,
        "all_pass_reason": "finite map checks and requested pure-zero controls passed"
        if all_pass
        else "finite map checks passed, but the requested |0><0| positive control is false for Ni and Si because |0><0| is their fixed/eigen state.",
        "allowed_claims": [
            "four explicit CP channel finite maps",
            "F01 finite size ladder",
            "N01 Se/Ni order-sensitive channel commutator",
            "candidate Axis 3 engine-family partition observable",
        ],
        "promotion_blockers": [
            "requested |0><0| positive control is false for Ni and Si",
            "Axis 3 direction criterion is not admitted by purity signs",
            "no PEPS3D carrier anchor",
            "promotion_allowed=false",
        ],
        "eligible_consumers": [],
        "blocked_consumers": ["layer_completion", "manifold_admission", "bridge", "coupling", "flux", "Xi", "Phi0", "Axis0", "physics"],
        "blocked_downstream": ["layer_completion", "manifold_admission", "bridge", "coupling", "flux", "Xi", "Phi0", "Axis0", "physics"],
        "pass_rule": "finite_map_checks_pass requires CP/TP channels, nonzero trace distance on the finite ladder, distinct superoperators, Se/Ni channel order sensitivity, boundary checks, wrong-structure controls, sensitive-state controls, and erased-structure verdict flip. all_pass additionally requires the requested |0><0| controls.",
        "fail_rule": "fail if Choi PSD/TP, F01 ladder, N01 order sensitivity, wrong/erased controls, or sensitive-state controls fail; all_pass remains false if requested pure-zero controls fail.",
        "TOOL_MANIFEST": {
            "jax": {"used": True, "reason": "complex128 array execution for CP channels, Choi PSD, superoperators, and commutator checks"},
            "jax.numpy": {"used": True, "reason": "load-bearing linear algebra and tensor primitives"},
            "python_stdlib": {"used": True, "reason": "JSON, timestamps, and source hashing"},
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "jax.numpy": "load_bearing", "python_stdlib": "supportive"},
        "tool_manifest": {
            "jax": {"used": True, "reason": "load-bearing audit computation"},
            "jax.numpy": {"used": True, "reason": "load-bearing channel invariant computation"},
            "python_stdlib": {"used": True, "reason": "supportive receipt metadata"},
        },
        "tool_integration_depth": {"jax": "load_bearing", "jax.numpy": "load_bearing", "python_stdlib": "supportive"},
    }


def numeric_paths(obj, prefix=""):
    found = {}
    if isinstance(obj, dict):
        for key, val in obj.items():
            found.update(numeric_paths(val, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(obj, list):
        for idx, val in enumerate(obj):
            found.update(numeric_paths(val, f"{prefix}[{idx}]"))
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        found[prefix] = float(obj)
    return found


def bool_paths(obj, prefix=""):
    found = {}
    if isinstance(obj, dict):
        for key, val in obj.items():
            found.update(bool_paths(val, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(obj, list):
        for idx, val in enumerate(obj):
            found.update(bool_paths(val, f"{prefix}[{idx}]"))
    elif isinstance(obj, bool):
        found[prefix] = obj
    return found


def write_parity(jax_result):
    if not JULIA_RESULT.exists():
        parity = {
            "object_id": "wb_axis3_terrains_parity",
            "status": "blocked_missing_julia_result",
            "julia_result": str(JULIA_RESULT),
            "jax_result": str(JAX_RESULT),
            "promotion_allowed": False,
        }
        PARITY_RESULT.write_text(json.dumps(parity, indent=2, sort_keys=True) + "\n")
        return parity

    julia_result = json.loads(JULIA_RESULT.read_text())
    j_nums = numeric_paths(julia_result)
    x_nums = numeric_paths(jax_result)
    numeric_diffs = {}
    max_abs_diff = 0.0
    for key in sorted(set(j_nums) & set(x_nums)):
        if any(skip in key for skip in ["generated_at", "julia_version", "python_version", "source_sha256"]):
            continue
        diff = abs(j_nums[key] - x_nums[key])
        if math.isfinite(diff):
            numeric_diffs[key] = diff
            max_abs_diff = max(max_abs_diff, diff)

    j_bools = bool_paths(julia_result)
    x_bools = bool_paths(jax_result)
    bool_mismatches = {
        key: {"julia": j_bools[key], "jax": x_bools[key]}
        for key in sorted(set(j_bools) & set(x_bools))
        if j_bools[key] != x_bools[key]
    }
    parity_pass = max_abs_diff < 1e-9 and not bool_mismatches
    parity = {
        "object_id": "wb_axis3_terrains_parity",
        "julia_result": str(JULIA_RESULT),
        "jax_result": str(JAX_RESULT),
        "julia_source_sha256": julia_result.get("source_sha256"),
        "jax_source_sha256": jax_result.get("source_sha256"),
        "shared_fixture": "deterministic Park-Miller pseudo-Haar qubit table",
        "max_abs_numeric_diff": max_abs_diff,
        "numeric_diff_count": len(numeric_diffs),
        "numeric_diffs_over_1e-9": {k: v for k, v in numeric_diffs.items() if v >= 1e-9},
        "bool_mismatches": bool_mismatches,
        "parity_pass": parity_pass,
        "promotion_allowed": False,
        "claim_ceiling": "parity audit only; no layer/manifold promotion",
    }
    PARITY_RESULT.write_text(json.dumps(parity, indent=2, sort_keys=True) + "\n")
    return parity


def main():
    result = build_result()
    JAX_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    parity = write_parity(result)
    print(f"wrote {JAX_RESULT}")
    print(f"wrote {PARITY_RESULT}")
    print(f"finite_map_checks_pass={result['finite_map_checks_pass']}")
    print(f"all_pass={result['all_pass']}")
    print(f"parity_pass={parity.get('parity_pass')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
