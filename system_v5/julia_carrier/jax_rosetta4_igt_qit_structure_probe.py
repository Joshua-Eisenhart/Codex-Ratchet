import jax; jax.config.update("jax_enable_x64", True)

import datetime as _dt
import json
import re
from itertools import permutations
from pathlib import Path
from typing import Any

import jax.numpy as jnp


OBJECT_ID = "rosetta4_igt_qit_structure_probe"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "rosetta4_igt_qit_structure_probe_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "rosetta4_igt_qit_structure_probe_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
SCORE_TOL = 1.0e-12
DT = 0.002
TERRAIN_STEPS = 360

I2 = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=jnp.complex128)
SX = jnp.array([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SY = jnp.array([[0.0 + 0.0j, -1.0j], [1.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SZ = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=jnp.complex128)
SM = jnp.array([[0.0 + 0.0j, 0.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
P_UP = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
P_DN = jnp.array([[0.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=jnp.complex128)
N_GENERIC = jnp.array([0.37, -0.51, 0.78], dtype=jnp.float64)
N_GENERIC = N_GENERIC / jnp.linalg.norm(N_GENERIC)
H0 = N_GENERIC[0] * SX + N_GENERIC[1] * SY + N_GENERIC[2] * SZ
HC = 0.63 * SZ
EPS_F = 0.17
EPS_V = 0.08
EPS_P = 0.05
GAMMA_F_Z = 0.46
GAMMA_F_X = 0.19
GAMMA_P = 2.35
KAPPA_UP = 0.37
KAPPA_DN = 0.23
L_SHARED = [jnp.sqrt(GAMMA_F_Z) * SZ, jnp.sqrt(GAMMA_F_X) * SX]
L_PIT = jnp.sqrt(GAMMA_P) * SM
PROJECTORS = [P_UP, P_DN]
KAPPAS = [KAPPA_UP, KAPPA_DN]
R0 = jnp.array([0.23, -0.31, 0.17], dtype=jnp.float64)

IGT_ORDER = ["Se", "Ne", "Ni", "Si"]
QIT_ORDER = ["Funnel", "Vortex", "Pit", "Hill"]
IGT_CW_CYCLE = ["Se", "Si", "Ni", "Ne"]
CANONICAL_QIT_FOR_IGT = ["Vortex", "Funnel", "Pit", "Hill"]
GRAMMAR_FEATURE_LABELS = [
    "first_slot_sign",
    "second_slot_sign",
    "cw_cycle_cos",
    "cw_cycle_sin",
    "hamming_class_centered",
]
DYNAMICS_FEATURE_LABELS = [
    "terminal_z",
    "purity_delta",
    "dissipative_minus_unitary_mean",
    "fixed_point_type_code",
    "terminal_generator_norm",
]


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def bool_scalar(value: bool) -> float:
    return 1.0 if value else 0.0


def vec_payload(v: Any) -> list[float]:
    if isinstance(v, list):
        return [float(x) for x in v]
    return [py_float(v[i]) for i in range(int(v.shape[0]))]


def sign_scalar(x: float, *, tol: float = TOL) -> float:
    if x > tol:
        return 1.0
    if x < -tol:
        return -1.0
    return 0.0


def jax_x64_enabled() -> bool:
    try:
        return bool(jax.config.jax_enable_x64)
    except AttributeError:
        return bool(jax.config.read("jax_enable_x64"))


def source_numpy_markers() -> dict[str, bool]:
    text = Path(__file__).read_text(encoding="utf-8")
    return {
        "import_numpy_present": ("import " + "numpy") in text or ("from " + "numpy") in text,
        "np_dot_present": re.search(r"(?<![A-Za-z0-9_])np\.", text) is not None,
        "numpy_method_bridge_present": ("." + "numpy()") in text,
    }


def grammar_label(igt_name: str) -> list[str]:
    if igt_name == "Se":
        return ["Lose", "WIN"]
    if igt_name == "Ne":
        return ["Win", "LOSE"]
    if igt_name == "Ni":
        return ["Lose", "LOSE"]
    if igt_name == "Si":
        return ["Win", "WIN"]
    raise ValueError(f"unknown IGT terrain: {igt_name}")


def first_slot_sign(label: list[str]) -> float:
    return 1.0 if label[0] == "Win" else -1.0


def second_slot_sign(label: list[str]) -> float:
    return 1.0 if label[1] == "WIN" else -1.0


def hamming_from_winwin(label: list[str]) -> float:
    return (0.0 if label[0] == "Win" else 1.0) + (0.0 if label[1] == "WIN" else 1.0)


def build_grammar_features() -> dict[str, Any]:
    out: dict[str, Any] = {}
    cycle_index = {name: idx for idx, name in enumerate(IGT_CW_CYCLE)}
    for terrain in IGT_ORDER:
        label = grammar_label(terrain)
        pos = float(cycle_index[terrain])
        theta = 2.0 * jnp.pi * pos / 4.0
        features = [
            first_slot_sign(label),
            second_slot_sign(label),
            py_float(jnp.cos(theta)),
            py_float(jnp.sin(theta)),
            hamming_from_winwin(label) - 1.0,
        ]
        out[terrain] = {
            "terrain": terrain,
            "grammar_label": label,
            "source_given_assignment": f"{terrain}={label[0]}{label[1]}",
            "cw_cycle": IGT_CW_CYCLE,
            "cw_cycle_position_zero_based": pos,
            "hamming_from_WinWIN": hamming_from_winwin(label),
            "feature_labels": GRAMMAR_FEATURE_LABELS,
            "feature_vector": vec_payload(features),
        }
    return out


def dag(m: jax.Array) -> jax.Array:
    return jnp.conj(m.T)


def comm(h: jax.Array, rho: jax.Array) -> jax.Array:
    return h @ rho - rho @ h


def density_from_bloch(r: jax.Array) -> jax.Array:
    return 0.5 * (I2 + r[0] * SX + r[1] * SY + r[2] * SZ)


def bloch_vector(rho: jax.Array) -> jax.Array:
    return jnp.array(
        [
            jnp.real(jnp.trace(rho @ SX)),
            jnp.real(jnp.trace(rho @ SY)),
            jnp.real(jnp.trace(rho @ SZ)),
        ],
        dtype=jnp.float64,
    )


def purity(rho: jax.Array) -> float:
    return py_float(jnp.real(jnp.trace(rho @ rho)))


def project_density(rho: jax.Array) -> jax.Array:
    rho_h = (rho + dag(rho)) / 2.0
    vals, vecs = jnp.linalg.eigh(rho_h)
    vals = jnp.maximum(jnp.real(vals), 0.0)
    total = py_float(jnp.sum(vals))
    if total <= 1.0e-15:
        return I2 / 2.0
    rho_p = vecs @ jnp.diag(vals.astype(jnp.complex128)) @ dag(vecs)
    rho_p = (rho_p + dag(rho_p)) / 2.0
    return rho_p / jnp.real(jnp.trace(rho_p))


def dissipator(l: jax.Array, rho: jax.Array) -> jax.Array:
    ldl = dag(l) @ l
    return l @ rho @ dag(l) - 0.5 * (ldl @ rho + rho @ ldl)


def sum_dissipators(ls: list[jax.Array], rho: jax.Array) -> jax.Array:
    out = jnp.zeros((2, 2), dtype=jnp.complex128)
    for l in ls:
        out = out + dissipator(l, rho)
    return out


def dephase_generator(rho: jax.Array) -> jax.Array:
    out = jnp.zeros((2, 2), dtype=jnp.complex128)
    for p, kappa in zip(PROJECTORS, KAPPAS, strict=True):
        out = out + kappa * (p @ rho @ p - 0.5 * (p @ rho + rho @ p))
    return out


def terrain_generator_parts(terrain: str, rho: jax.Array) -> tuple[jax.Array, jax.Array]:
    if terrain == "Funnel":
        dissipative = sum_dissipators(L_SHARED, rho)
        unitary = -1.0j * EPS_F * comm(H0, rho)
        return unitary, dissipative
    if terrain == "Vortex":
        unitary = -1.0j * comm(H0, rho)
        dissipative = EPS_V * sum_dissipators(L_SHARED, rho)
        return unitary, dissipative
    if terrain == "Pit":
        dissipative = dissipator(L_PIT, rho)
        unitary = -1.0j * EPS_P * comm(H0, rho)
        return unitary, dissipative
    if terrain == "Hill":
        unitary = -1.0j * comm(HC, rho)
        dissipative = dephase_generator(rho)
        return unitary, dissipative
    raise ValueError(f"unknown Type-1 terrain: {terrain}")


def terrain_generator(terrain: str, rho: jax.Array) -> jax.Array:
    unitary, dissipative = terrain_generator_parts(terrain, rho)
    return unitary + dissipative


def rk4_step(rho: jax.Array, terrain: str) -> jax.Array:
    def f(x: jax.Array) -> jax.Array:
        return terrain_generator(terrain, x)

    k1 = f(rho)
    k2 = f(rho + 0.5 * DT * k1)
    k3 = f(rho + 0.5 * DT * k2)
    k4 = f(rho + DT * k3)
    return project_density(rho + (DT / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4))


def fixed_point_readout(terminal_z: float, dissipative_fraction: float) -> tuple[float, str]:
    if abs(terminal_z) > 0.5:
        return (1.0, "positive_z_attractor") if terminal_z > 0.0 else (-1.0, "negative_z_attractor")
    if dissipative_fraction < 0.5:
        return 0.5, "unitary_dominant_nonfixed_orbit"
    return 0.0, "dissipative_dephasing_or_mixed"


def integrate_signature(terrain: str) -> dict[str, Any]:
    rho = density_from_bloch(R0)
    initial_purity = purity(rho)
    dissipative_fraction_sum = 0.0
    dissipative_minus_unitary_sum = 0.0
    speed_sum = 0.0
    for _ in range(TERRAIN_STEPS):
        unitary, dissipative = terrain_generator_parts(terrain, rho)
        unorm = py_float(jnp.linalg.norm(unitary))
        dnorm = py_float(jnp.linalg.norm(dissipative))
        denom = unorm + dnorm + 1.0e-15
        dissipative_fraction_sum += dnorm / denom
        dissipative_minus_unitary_sum += (dnorm - unorm) / denom
        speed_sum += py_float(jnp.linalg.norm(unitary + dissipative))
        rho = rk4_step(rho, terrain)
    terminal_purity = purity(rho)
    terminal_bloch = bloch_vector(rho)
    terminal_z = py_float(terminal_bloch[2])
    terminal_generator_norm = py_float(jnp.linalg.norm(terrain_generator(terrain, rho)))
    dissipative_fraction_mean = dissipative_fraction_sum / TERRAIN_STEPS
    dissipative_minus_unitary_mean = dissipative_minus_unitary_sum / TERRAIN_STEPS
    fixed_code, fixed_type = fixed_point_readout(terminal_z, dissipative_fraction_mean)
    features = [
        terminal_z,
        terminal_purity - initial_purity,
        dissipative_minus_unitary_mean,
        fixed_code,
        terminal_generator_norm,
    ]
    return {
        "terrain": terrain,
        "feature_labels": DYNAMICS_FEATURE_LABELS,
        "feature_vector": vec_payload(features),
        "terminal_bloch": vec_payload(terminal_bloch),
        "terminal_z": float(terminal_z),
        "terminal_z_sign": sign_scalar(terminal_z),
        "initial_purity": float(initial_purity),
        "terminal_purity": float(terminal_purity),
        "purity_delta": float(terminal_purity - initial_purity),
        "purity_trend_sign": sign_scalar(terminal_purity - initial_purity),
        "dissipative_fraction_mean": float(dissipative_fraction_mean),
        "unitary_fraction_mean": float(1.0 - dissipative_fraction_mean),
        "dissipative_minus_unitary_mean": float(dissipative_minus_unitary_mean),
        "dissipative_minus_unitary_sign": sign_scalar(dissipative_minus_unitary_mean),
        "mean_generator_norm": float(speed_sum / TERRAIN_STEPS),
        "terminal_generator_norm": float(terminal_generator_norm),
        "fixed_point_type_code": float(fixed_code),
        "fixed_point_type": fixed_type,
    }


def build_dynamics_features() -> dict[str, Any]:
    return {terrain: integrate_signature(terrain) for terrain in QIT_ORDER}


def feature_matrix(features: dict[str, Any], order: list[str]) -> list[list[float]]:
    return [[float(x) for x in features[name]["feature_vector"]] for name in order]


def standardize_rows(rows: list[list[float]]) -> tuple[list[list[float]], list[float], list[float]]:
    arr = jnp.array(rows, dtype=jnp.float64)
    means = jnp.mean(arr, axis=0)
    centered = arr - means
    stds = jnp.sqrt(jnp.mean(centered * centered, axis=0))
    safe_stds = jnp.where(stds <= 1.0e-15, 1.0, stds)
    z = centered / safe_stds
    z = jnp.where(stds <= 1.0e-15, 0.0, z)
    out = [[py_float(z[row, col]) for col in range(int(z.shape[1]))] for row in range(int(z.shape[0]))]
    return out, vec_payload(means), vec_payload(stds)


def euclidean(a: list[float], b: list[float]) -> float:
    av = jnp.array(a, dtype=jnp.float64)
    bv = jnp.array(b, dtype=jnp.float64)
    return py_float(jnp.linalg.norm(av - bv))


def pairwise_distances(rows: list[list[float]]) -> tuple[list[float], list[list[int]]]:
    out: list[float] = []
    pairs: list[list[int]] = []
    for i in range(len(rows) - 1):
        for j in range(i + 1, len(rows)):
            out.append(euclidean(rows[i], rows[j]))
            pairs.append([i + 1, j + 1])
    return out, pairs


def pearson(a: list[float], b: list[float]) -> float:
    av = jnp.array(a, dtype=jnp.float64)
    bv = jnp.array(b, dtype=jnp.float64)
    da = av - jnp.mean(av)
    db = bv - jnp.mean(bv)
    denom = jnp.sqrt(jnp.sum(da * da) * jnp.sum(db * db))
    if py_float(denom) <= 1.0e-15:
        return 0.0
    return py_float(jnp.sum(da * db) / denom)


def permutation_labels(perm: list[int]) -> list[str]:
    return [QIT_ORDER[idx] for idx in perm]


def score_permutations(grammar_features: dict[str, Any], dynamics_features: dict[str, Any]) -> dict[str, Any]:
    grammar_rows = feature_matrix(grammar_features, IGT_ORDER)
    dynamics_rows = feature_matrix(dynamics_features, QIT_ORDER)
    grammar_z, grammar_means, grammar_stds = standardize_rows(grammar_rows)
    dynamics_z, dynamics_means, dynamics_stds = standardize_rows(dynamics_rows)
    grammar_distances, pair_indices = pairwise_distances(grammar_z)
    perms = [list(p) for p in permutations(range(4))]
    canonical_perm = [QIT_ORDER.index(terrain) for terrain in CANONICAL_QIT_FOR_IGT]
    rows: list[dict[str, Any]] = []
    scores: list[float] = []
    canonical_score = float("nan")
    for perm in perms:
        permuted_rows = [dynamics_z[idx] for idx in perm]
        qit_distances, _ = pairwise_distances(permuted_rows)
        score = pearson(grammar_distances, qit_distances)
        scores.append(float(score))
        is_canonical = perm == canonical_perm
        if is_canonical:
            canonical_score = float(score)
        rows.append(
            {
                "permutation_1_based": [idx + 1 for idx in perm],
                "igt_order": IGT_ORDER,
                "qit_order_for_igt_order": permutation_labels(perm),
                "score": float(score),
                "is_canonical_source_given": is_canonical,
            }
        )
    score_arr = jnp.array(scores, dtype=jnp.float64)
    score_mean = py_float(jnp.mean(score_arr))
    score_std = py_float(jnp.sqrt(jnp.mean((score_arr - score_mean) * (score_arr - score_mean))))
    z = 0.0 if score_std <= 1.0e-15 else (canonical_score - score_mean) / score_std
    max_score = py_float(jnp.max(score_arr))
    n_ge = int(jax.device_get(jnp.sum(score_arr >= canonical_score - SCORE_TOL)))
    n_max = int(jax.device_get(jnp.sum(score_arr >= max_score - SCORE_TOL)))
    canonical_is_unique_max = canonical_score >= max_score - SCORE_TOL and n_max == 1
    exact_p_ge = py_float(jnp.array(n_ge, dtype=jnp.float64) / jnp.array(len(scores), dtype=jnp.float64))
    significant = canonical_score > score_mean and exact_p_ge <= 0.05 and z > 0.0
    shared = canonical_is_unique_max and significant
    trivial = (not shared) or n_ge > 1
    return {
        "score_method": "Pearson correlation between the six pairwise Euclidean distances of backend-local z-scored feature vectors; no per-dimension semantic crosswalk is fit.",
        "igt_order": IGT_ORDER,
        "qit_base_order": QIT_ORDER,
        "canonical_qit_order_for_igt_order": CANONICAL_QIT_FOR_IGT,
        "canonical_permutation_1_based": [idx + 1 for idx in canonical_perm],
        "grammar_pair_indices_igt_order_1_based": pair_indices,
        "grammar_pairwise_distances_zscored": vec_payload(grammar_distances),
        "grammar_feature_means": vec_payload(grammar_means),
        "grammar_feature_stds": vec_payload(grammar_stds),
        "dynamics_feature_means": vec_payload(dynamics_means),
        "dynamics_feature_stds": vec_payload(dynamics_stds),
        "rows": rows,
        "scores": vec_payload(scores),
        "score_mean": float(score_mean),
        "score_std": float(score_std),
        "max_score": float(max_score),
        "canonical_bijection_score": float(canonical_score),
        "canonical_gap_above_null_mean": float(canonical_score - score_mean),
        "canonical_z_above_null": float(z),
        "n_permutations_ge_canonical": n_ge,
        "canonical_exact_p_ge": float(exact_p_ge),
        "canonical_is_unique_max": canonical_is_unique_max,
        "canonical_significant_above_null": significant,
        "shared_structure_invariant": shared,
        "rosetta4_is_trivial": trivial,
        "exactly_24_bijections_scored": len(rows) == 24,
    }


def flatten_feature_scalars(shared_scalars: dict[str, float], prefix: str, features: dict[str, Any], order: list[str]) -> None:
    for name in order:
        vector = features[name]["feature_vector"]
        labels = features[name]["feature_labels"]
        for idx, value in enumerate(vector, start=1):
            shared_scalars[f"{prefix}_{name}_feature_{idx}_{labels[idx - 1]}"] = float(value)


def parity_block(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_REFERENCE_PATH.exists():
        return {
            "peer_result_path": str(JULIA_REFERENCE_PATH),
            "peer_available": False,
            "parity_max_diff": None,
            "worst_key": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": False,
            "missing_from_peer": sorted(result["shared_scalars"].keys()),
            "missing_from_self": [],
            "diffs": {},
            "status": "pending_peer",
        }
    peer = json.loads(JULIA_REFERENCE_PATH.read_text(encoding="utf-8"))
    self_scalars = result["shared_scalars"]
    peer_scalars = peer["shared_scalars"]
    missing_from_peer = sorted(set(self_scalars) - set(peer_scalars))
    missing_from_self = sorted(set(peer_scalars) - set(self_scalars))
    diffs: dict[str, float] = {}
    max_diff = 0.0
    worst_key = ""
    for key in sorted(set(self_scalars) & set(peer_scalars)):
        diff = abs(float(self_scalars[key]) - float(peer_scalars[key]))
        diffs[key] = diff
        if diff > max_diff:
            max_diff = diff
            worst_key = key
    within = not missing_from_peer and not missing_from_self and max_diff < TOL
    strict_divergence = bool(missing_from_peer or missing_from_self or max_diff > STRICT_STOP_TOL)
    return {
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "peer_available": True,
        "parity_max_diff": float(max_diff),
        "worst_key": worst_key,
        "within_1e_9": within,
        "strict_divergence_gt_1e_6": strict_divergence,
        "missing_from_peer": missing_from_peer,
        "missing_from_self": missing_from_self,
        "diffs": diffs,
        "status": "pass" if within else "fail_closed",
    }


def build_result() -> dict[str, Any]:
    grammar_features = build_grammar_features()
    dynamics_features = build_dynamics_features()
    rosetta = score_permutations(grammar_features, dynamics_features)
    verdicts = {
        "exactly_24_bijections_scored": rosetta["exactly_24_bijections_scored"],
        "canonical_bijection_score": rosetta["canonical_bijection_score"],
        "n_permutations_ge_canonical": rosetta["n_permutations_ge_canonical"],
        "canonical_is_unique_max": rosetta["canonical_is_unique_max"],
        "canonical_z_above_null": rosetta["canonical_z_above_null"],
        "shared_structure_invariant": rosetta["shared_structure_invariant"],
        "rosetta4_is_trivial": rosetta["rosetta4_is_trivial"],
    }
    shared_scalars: dict[str, float] = {
        "exactly_24_bijections_scored_flag": bool_scalar(bool(verdicts["exactly_24_bijections_scored"])),
        "canonical_bijection_score": float(verdicts["canonical_bijection_score"]),
        "n_permutations_ge_canonical": float(verdicts["n_permutations_ge_canonical"]),
        "canonical_is_unique_max_flag": bool_scalar(bool(verdicts["canonical_is_unique_max"])),
        "canonical_z_above_null": float(verdicts["canonical_z_above_null"]),
        "canonical_gap_above_null_mean": float(rosetta["canonical_gap_above_null_mean"]),
        "canonical_exact_p_ge": float(rosetta["canonical_exact_p_ge"]),
        "shared_structure_invariant_flag": bool_scalar(bool(verdicts["shared_structure_invariant"])),
        "rosetta4_is_trivial_flag": bool_scalar(bool(verdicts["rosetta4_is_trivial"])),
        "permutation_score_mean": float(rosetta["score_mean"]),
        "permutation_score_std": float(rosetta["score_std"]),
        "permutation_max_score": float(rosetta["max_score"]),
        "numpy_compute_used_flag": 0.0,
        "promotion_allowed_flag": 0.0,
    }
    flatten_feature_scalars(shared_scalars, "igt", grammar_features, IGT_ORDER)
    flatten_feature_scalars(shared_scalars, "qit", dynamics_features, QIT_ORDER)

    tool_manifest = {
        "JAX jax.numpy x64": {
            "tried": True,
            "used": True,
            "role": "mirror_stress_jnp_x64_no_numpy",
            "reason": "load-bearing for jax.numpy x64 Type-1 terrain Lindblad/RK4 density-matrix dynamics, PSD projection, feature extraction, and exhaustive 24-bijection scoring",
        },
        "Julia LinearAlgebra": {
            "tried": True,
            "used": False,
            "role": "peer_reference_expected",
            "reason": "supportive peer parity lane read from its result JSON when present; no Julia compute is used inside JAX",
        },
        "Python stdlib itertools/json": {
            "tried": True,
            "used": True,
            "role": "local_iteration_and_json_support",
            "reason": "supportive only for exact 24-permutation enumeration and JSON writing; numerical compute stays in jax.numpy x64",
        },
    }
    tool_depth = {
        "JAX jax.numpy x64": "load_bearing",
        "Julia LinearAlgebra": "supportive",
        "Python stdlib itertools/json": "supportive",
    }
    source_markers = source_numpy_markers()

    result: dict[str, Any] = {
        "sim_id": OBJECT_ID,
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "version": "1.0.0",
        "backend": "jax",
        "backend_roles": {
            "julia": "reference_native_linearalgebra_no_pycall_no_numpy",
            "jax": "mirror_stress_jnp_x64_no_numpy",
        },
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "PROMOTION_ALLOWED": False,
        "FORMAL_ADMISSION_ALLOWED": False,
        "sim_execution_kind": "nonclassical",
        "sim_class": "dual_backend_rosetta4_structure_probe",
        "carrier_layer": "igt_two_ring_grammar_and_single_qubit_type1_density_matrix_terrain_dynamics",
        "geometry_layer": "four_element_structure_alignment_null",
        "claim_ceiling": "Scratch diagnostic only: tests whether a source-given IGT win/lose grammar assignment uniquely aligns with independently integrated Type-1 QIT terrain dynamics; no admission or promotion claim.",
        "allowed_claims": [
            "IGT grammar features are computed from the two-slot win/lose x WIN/LOSE grammar and the source-given Se/Ne/Ni/Si cycle only",
            "QIT dynamics features are computed from integrated Type-1 terrain equations only, without win/lose labels",
            "Rosetta scoring exhausts all 24 IGT-to-QIT bijections and reports whether the source-given canonical bijection is uniquely best",
            "A trivial/uninformative result is an accepted diagnostic outcome when random permutations tie or beat the canonical bijection",
        ],
        "blocked_consumers": [
            "formal_admission",
            "QIT_engine_admission",
            "Axis0",
            "bridge",
            "canonical_engine_evidence",
            "promotion",
        ],
        "out_of_scope": [
            "admission claim",
            "philosophy claim",
            "QIT terrain labels derived from win/lose during dynamics extraction",
            "feature tuning to force uniqueness",
        ],
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__)),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "score_tol": SCORE_TOL,
        "dt": DT,
        "terrain_steps": TERRAIN_STEPS,
        "h0_generic_n": vec_payload(N_GENERIC),
        "initial_bloch": vec_payload(R0),
        "anti_circularity": {
            "genealogy_rule": "Sim both sides independently; do not derive either feature family from the other; exhaust the permutation null.",
            "igt_feature_source": "2-ring win/lose combinatorics only: source-given Se=LoseWin, Ne=WinLose, Ni=LoseLose, Si=WinWin plus CW cycle Se->Si->Ni->Ne.",
            "qit_feature_source": "Type-1 Funnel/Vortex/Pit/Hill terrain equations only: integrated rho dynamics, terminal Bloch readouts, purity trend, generator norm split, and fixed-point readout.",
            "canonical_assignment_status": "SOURCE-GIVEN, not fit. Existing Type-1 placement grammar gives Funnel=WinLose, Vortex=LoseWin, Pit=LoseLose, Hill=WinWin; therefore canonical IGT order [Se,Ne,Ni,Si] maps to [Vortex,Funnel,Pit,Hill]. This assignment is used only to pick the canonical permutation after features are computed.",
        },
        "engine_equations_type1": {
            "Funnel": "sum_k D_Lk(rho) - i eps_F [H0,rho]",
            "Vortex": "-i[H0,rho] + eps_V sum_k D_Lk(rho)",
            "Pit": "D_sigma_minus(rho) - i eps_P [H0,rho]",
            "Hill": "-i[H_C,rho] + sum_j kappa_j(P_j rho P_j - 0.5{P_j,rho})",
        },
        "grammar_feature_labels": GRAMMAR_FEATURE_LABELS,
        "dynamics_feature_labels": DYNAMICS_FEATURE_LABELS,
        "grammar_features": grammar_features,
        "dynamics_features": dynamics_features,
        "rosetta4_test": rosetta,
        "verdicts": verdicts,
        "shared_scalars": shared_scalars,
        "tools": ["JAX jax.numpy x64", "Julia LinearAlgebra", "Python stdlib itertools/json"],
        "tool_manifest": tool_manifest,
        "TOOL_MANIFEST": tool_manifest,
        "tool_integration_depth": tool_depth,
        "TOOL_INTEGRATION_DEPTH": tool_depth,
        "numpy_compute_used": False,
        "source_numpy_markers": source_markers,
        "jax_x64_enabled": jax_x64_enabled(),
        "divergence_log": [
            "IGT side did not read or integrate QIT dynamics.",
            "QIT side did not use win/lose labels to compute terrain signatures.",
            "All 24 bijections are scored; the decisive control is n_permutations_ge_canonical.",
            "shared_structure_invariant is true only if the source-given canonical bijection is the unique maximum and the exact permutation p-value is <= 0.05.",
            "rosetta4_is_trivial is true when the canonical bijection is tied/beaten or otherwise not significant against the exhaustive permutation null.",
        ],
    }
    result["parity"] = parity_block(result)
    result["all_pass"] = (
        bool(result["jax_x64_enabled"])
        and not bool(result["numpy_compute_used"])
        and not any(source_markers.values())
        and bool(verdicts["exactly_24_bijections_scored"])
        and bool(result["parity"]["within_1e_9"])
    )
    result["stop_condition_fired"] = bool(result["parity"]["strict_divergence_gt_1e_6"])
    result["plain_sentence"] = (
        "The source-given IGT win/lose grammar uniquely aligns with the independent QIT terrain dynamics under this four-element permutation-null test."
        if bool(verdicts["shared_structure_invariant"])
        else "The source-given IGT win/lose grammar does not uniquely align with the independent QIT terrain dynamics under this four-element permutation-null test; the result is trivial/uninformative."
    )
    return result


def main() -> None:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["shared_scalars"]
    print(f"rosetta4_igt_qit_structure_probe jax wrote {RESULT_PATH}")
    print(
        "canonical_score={score} n_ge={nge}/24 unique={unique} z={z}".format(
            score=s["canonical_bijection_score"],
            nge=s["n_permutations_ge_canonical"],
            unique=result["verdicts"]["canonical_is_unique_max"],
            z=s["canonical_z_above_null"],
        )
    )
    print(
        "shared_structure_invariant={shared} rosetta4_is_trivial={trivial}".format(
            shared=result["verdicts"]["shared_structure_invariant"],
            trivial=result["verdicts"]["rosetta4_is_trivial"],
        )
    )
    print(
        "parity_max_diff={diff} numpy_compute_used={numpy_used} jax_x64_enabled={x64}".format(
            diff=result["parity"]["parity_max_diff"],
            numpy_used=result["numpy_compute_used"],
            x64=result["jax_x64_enabled"],
        )
    )
    if result["stop_condition_fired"]:
        print("STOP_CONDITION_FIRED rosetta4_igt_qit_structure_probe jax")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
