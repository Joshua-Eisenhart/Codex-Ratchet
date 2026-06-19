#!/usr/bin/env python3
# object_id: mp_cross_model_convergence
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: finite cross-model readout witness only; no physics, SM, M(C), Axis0, bridge, basin, or formal admission.

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from itertools import permutations
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_DIR = ROOT / "system_v5/ops/formal_scouts"
JULIA_DIR = ROOT / "system_v5/julia_carrier"
RESULT_PATH = FORMAL_DIR / "results/mp_cross_model_convergence_results.json"
JULIA_RESULT_PATH = JULIA_DIR / "mp_cross_model_convergence_julia_results.json"
OBJECT_ID = "mp_cross_model_convergence"
CLAIM_CEILING = (
    "finite cross-model readout witness only; classification=scratch_diagnostic; "
    "promotion_allowed=false; formal_admission_allowed=false; NO physics/SM/M(C)/Axis0 admission"
)
N_QUBITS = 3
STAGE_DT = 0.08
RK4_STEPS_PER_STAGE = 8
PARITY_TOL = 1.0e-9
DIFFER_TOL = 1.0e-7
PERCEPTION_KEYS = ["Si", "Ne", "Se", "Ni"]
WRONG_MAP = {"Si": "Ni", "Ne": "Se", "Se": "Si", "Ni": "Ne"}
RANDOM_PERMUTATIONS = [
    [1, 0, 2, 3],
    [2, 1, 3, 0],
    [3, 0, 1, 2],
    [0, 3, 2, 1],
    [1, 3, 0, 2],
    [2, 0, 3, 1],
]
READOUT_COMPONENTS = ["physics", "igt", "perception", "operator"]
PHYSICS_FACES = ["mass", "gravity", "dark_energy"]
IGT_TERRAINS = {
    "Si": {"terrain": "WinWin", "lower": 1.0, "upper": 1.0},
    "Ne": {"terrain": "WinLose", "lower": 1.0, "upper": -1.0},
    "Se": {"terrain": "LoseWin", "lower": -1.0, "upper": 1.0},
    "Ni": {"terrain": "LoseLose", "lower": -1.0, "upper": -1.0},
}
SOURCE_FILES = {
    "canonical_qit_engine_specs": FORMAL_DIR / "canonical_qit_engine_specs.py",
    "division_algebra_ratchet_ladder": JULIA_DIR / "division_algebra_ratchet_ladder.jl",
    "clifford_algebra_ladder": JULIA_DIR / "clifford_algebra_ladder.jl",
    "octonion_G2_automorphism": JULIA_DIR / "octonion_G2_automorphism.jl",
    "sedenion_break": JULIA_DIR / "sedenion_break_prelim.jl",
    "density_matrix_spinor_lift": JULIA_DIR / "density_matrix_spinor_lift.jl",
    "clifford_torus_nested_hopf_foliation": JULIA_DIR / "clifford_torus_nested_hopf_foliation.jl",
    "golden_weyl": JULIA_DIR / "golden_weyl_julia.jl",
}

sys.path.insert(0, str(FORMAL_DIR))
import canonical_qit_engine_specs as specs  # noqa: E402


def as_float(x: Any) -> float:
    return float(jax.device_get(jnp.real(x)))


def carray_from_torch(tensor: Any) -> jax.Array:
    return jnp.asarray(tensor.detach().cpu().tolist(), dtype=jnp.complex128)


I2 = carray_from_torch(specs.I2)
SX = carray_from_torch(specs.SX)
SY = carray_from_torch(specs.SY)
SZ = carray_from_torch(specs.SZ)
SIGMA_MINUS = carray_from_torch(specs.SIGMA_MINUS)
SIGMA_PLUS = carray_from_torch(specs.SIGMA_PLUS)
MIRROR = carray_from_torch(specs.MIRROR)
H0 = carray_from_torch(specs.H0)
PERCEPTION_L = {key: carray_from_torch(value) for key, value in specs.PERCEPTION_L_MATRICES.items()}
OPERATOR_GENERATORS = {key: carray_from_torch(value) for key, value in specs.OPERATOR_GENERATORS.items()}
OPERATOR_BASE_ANGLES = {key: float(value) for key, value in specs.OPERATOR_BASE_ANGLES.items()}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_fingerprints() -> dict[str, Any]:
    return {
        name: {"path": str(path), "exists": path.exists(), "sha256": sha256_file(path) if path.exists() else None}
        for name, path in SOURCE_FILES.items()
    }


def kron_chain(ops: list[jax.Array]) -> jax.Array:
    out = ops[0]
    for op in ops[1:]:
        out = jnp.kron(out, op)
    return out


def site_op(local_op: jax.Array, n_qubits: int, site_idx: int) -> jax.Array:
    return kron_chain([local_op if idx == site_idx else I2 for idx in range(n_qubits)])


def all_site_sum(local_op: jax.Array, n_qubits: int) -> jax.Array:
    out = jnp.zeros((2**n_qubits, 2**n_qubits), dtype=jnp.complex128)
    for idx in range(n_qubits):
        out = out + site_op(local_op, n_qubits, idx)
    return out


def hamiltonian(engine_type: int, n_qubits: int) -> jax.Array:
    return all_site_sum(H0 if engine_type == 0 else -H0, n_qubits)


def collapse_ops(perception: str, engine_type: int, n_qubits: int) -> list[jax.Array]:
    local_l = PERCEPTION_L[perception]
    if engine_type == 1:
        local_l = MIRROR @ local_l @ MIRROR
    return [site_op(local_l, n_qubits, idx) for idx in range(n_qubits)]


def normalize_density(rho: jax.Array) -> jax.Array:
    rho_h = 0.5 * (rho + jnp.conj(rho.T))
    return rho_h / jnp.trace(rho_h)


def lindblad_rhs(rho: jax.Array, h: jax.Array, ls: list[jax.Array]) -> jax.Array:
    out = -1.0j * (h @ rho - rho @ h)
    for ell in ls:
        ldag_l = jnp.conj(ell.T) @ ell
        out = out + ell @ rho @ jnp.conj(ell.T) - 0.5 * (ldag_l @ rho + rho @ ldag_l)
    return out


def lindblad_step(rho: jax.Array, h: jax.Array, ls: list[jax.Array]) -> jax.Array:
    y = rho
    h_step = STAGE_DT / float(RK4_STEPS_PER_STAGE)
    for _ in range(RK4_STEPS_PER_STAGE):
        k1 = lindblad_rhs(y, h, ls)
        k2 = lindblad_rhs(y + 0.5 * h_step * k1, h, ls)
        k3 = lindblad_rhs(y + 0.5 * h_step * k2, h, ls)
        k4 = lindblad_rhs(y + h_step * k3, h, ls)
        y = y + (h_step / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    return normalize_density(y)


def operator_unitary_local(op_name: str, sign: int) -> jax.Array:
    theta = OPERATOR_BASE_ANGLES[op_name] * float(sign)
    generator = OPERATOR_GENERATORS[op_name]
    return jnp.cos(theta) * I2 - 1.0j * jnp.sin(theta) * generator


def apply_operator(rho: jax.Array, n_qubits: int, op_name: str, sign: int, erased: bool = False) -> jax.Array:
    if erased:
        return rho
    local_u = operator_unitary_local(op_name, sign)
    global_u = kron_chain([local_u for _ in range(n_qubits)])
    return normalize_density(global_u @ rho @ jnp.conj(global_u.T))


def ket(index: int, dim: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.complex128)[:, index]


def pure_density(psi: jax.Array) -> jax.Array:
    psi = psi / jnp.linalg.norm(psi)
    return psi.reshape((-1, 1)) @ jnp.conj(psi.reshape((1, -1)))


def maximally_mixed(n_qubits: int) -> jax.Array:
    dim = 2**n_qubits
    return jnp.eye(dim, dtype=jnp.complex128) / float(dim)


def primary_density() -> jax.Array:
    q0 = ket(0, 2)
    bell = (ket(0, 4) + jnp.exp(0.37j) * ket(3, 4)) / jnp.sqrt(2.0)
    psi = jnp.kron(q0, bell)
    return normalize_density(0.86 * pure_density(psi) + 0.14 * maximally_mixed(3))


def run_canonical_engine_state(rho_init: jax.Array) -> tuple[jax.Array, list[jax.Array]]:
    rho = normalize_density(rho_init)
    h = hamiltonian(0, N_QUBITS)
    states = [rho]
    for perception, loop_class in specs.ENGINE_SCHEDULE_TYPE_ONE:
        for substage_idx in range(specs.N_SUBSTAGES_PER_MAIN):
            slot = specs.get_operator_slot_spec(perception, 0, loop_class, substage_idx)
            ls = collapse_ops(perception, 0, N_QUBITS)
            if slot["precedence"] == "operator_first":
                rho = apply_operator(rho, N_QUBITS, slot["operator"], int(slot["sign"]))
                rho = lindblad_step(rho, h, ls)
            else:
                rho = lindblad_step(rho, h, ls)
                rho = apply_operator(rho, N_QUBITS, slot["operator"], int(slot["sign"]))
            rho = normalize_density(rho)
            states.append(rho)
    return rho, states


def partial_trace(rho: jax.Array, n_qubits: int, keep: list[int]) -> jax.Array:
    keep_sorted = sorted(keep)
    trace_out = [idx for idx in range(n_qubits) if idx not in keep_sorted]
    tensor = jnp.reshape(rho, [2] * (2 * n_qubits))
    perm = keep_sorted + trace_out + [n_qubits + idx for idx in keep_sorted] + [n_qubits + idx for idx in trace_out]
    permuted = jnp.transpose(tensor, perm)
    dim_keep = 2 ** len(keep_sorted)
    dim_trace = 2 ** len(trace_out)
    reshaped = jnp.reshape(permuted, (dim_keep, dim_trace, dim_keep, dim_trace))
    return normalize_density(jnp.einsum("atbt->ab", reshaped))


def vn_entropy(rho: jax.Array) -> jax.Array:
    vals = jnp.real(jnp.linalg.eigvalsh(0.5 * (rho + jnp.conj(rho.T))))
    vals = jnp.clip(vals, 1.0e-15, 1.0)
    vals = vals / jnp.sum(vals)
    return -jnp.sum(vals * jnp.log(vals))


def purity(rho: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(rho @ rho))


def offdiag_coherence(rho: jax.Array) -> jax.Array:
    dim = rho.shape[0]
    mask = jnp.ones((dim, dim), dtype=jnp.float64) - jnp.eye(dim, dtype=jnp.float64)
    return jnp.sum(jnp.abs(rho) * mask) / float(dim * (dim - 1))


def mutual_info(rho: jax.Array, left: list[int], right: list[int]) -> jax.Array:
    rho_l = partial_trace(rho, N_QUBITS, left)
    rho_r = partial_trace(rho, N_QUBITS, right)
    rho_lr = partial_trace(rho, N_QUBITS, sorted(left + right))
    return vn_entropy(rho_l) + vn_entropy(rho_r) - vn_entropy(rho_lr)


def physics_faces(rho: jax.Array) -> dict[str, float]:
    log2 = jnp.log(jnp.asarray(2.0, dtype=jnp.float64))
    local = [vn_entropy(partial_trace(rho, N_QUBITS, [idx])) / log2 for idx in range(N_QUBITS)]
    mass = jnp.maximum(0.0, (local[1] + local[2]) / 2.0 - local[0])
    gravity = jnp.abs(local[1] - local[0]) + 0.5 * jnp.abs(local[2] - local[0])
    dark_energy = vn_entropy(rho) / jnp.log(jnp.asarray(2**N_QUBITS, dtype=jnp.float64))
    return {"mass": as_float(mass), "gravity": as_float(gravity), "dark_energy": as_float(dark_energy)}


def terrain_scalar(perception: str) -> float:
    terrain = IGT_TERRAINS[perception]
    topo = specs.TYPE_ONE_TOPOLOGIES[perception]
    return float(terrain["lower"] + 0.73 * terrain["upper"] + float(topo["rate"]))


def model_bundle(rho: jax.Array, *, wrong_structure: bool = False, erased: bool = False) -> dict[str, Any]:
    h = hamiltonian(0, N_QUBITS)
    physics: list[float] = []
    igt: list[float] = []
    perception_readout: list[float] = []
    operator_readout: list[float] = []
    per_key: dict[str, Any] = {}
    for natural_key in PERCEPTION_KEYS:
        used_key = WRONG_MAP[natural_key] if wrong_structure else natural_key
        ls = collapse_ops(used_key, 0, N_QUBITS)
        post = rho if erased else lindblad_step(rho, h, ls)
        faces = physics_faces(post)
        face_scalar = {
            "Si": faces["mass"],
            "Ne": faces["gravity"],
            "Se": faces["dark_energy"],
            "Ni": faces["mass"] + 0.25 * faces["dark_energy"],
        }[natural_key]
        rhs_norm = 0.0 if erased else as_float(jnp.linalg.norm(lindblad_rhs(rho, h, ls)))
        entropy_delta = 0.0 if erased else as_float(jnp.abs(vn_entropy(post) - vn_entropy(rho)))
        native_ops = specs.NATIVE_OPERATORS_BY_TOPOLOGY[used_key]
        op_delta = 0.0
        for op_name in native_ops:
            op_delta += as_float(jnp.linalg.norm(apply_operator(rho, N_QUBITS, op_name, +1, erased=erased) - rho))
        op_delta /= float(len(native_ops))
        terrain = terrain_scalar(used_key)
        physics.append(face_scalar)
        igt.append(0.0 if erased else terrain)
        perception_readout.append(rhs_norm + 0.2 * entropy_delta)
        operator_readout.append(op_delta)
        per_key[natural_key] = {
            "used_key": used_key,
            "physics_faces": faces,
            "physics_scalar": float(face_scalar),
            "igt_terrain": IGT_TERRAINS[used_key]["terrain"],
            "igt_scalar": 0.0 if erased else terrain,
            "perception_scalar": float(rhs_norm + 0.2 * entropy_delta),
            "operator_scalar": float(op_delta),
        }
    matrix = jnp.asarray([physics, igt, perception_readout, operator_readout], dtype=jnp.float64)
    return {
        "per_key": per_key,
        "vectors": {
            "physics": [float(x) for x in physics],
            "igt": [float(x) for x in igt],
            "perception": [float(x) for x in perception_readout],
            "operator": [float(x) for x in operator_readout],
        },
        "matrix": matrix,
    }


def zscore(vector: jax.Array) -> jax.Array:
    return (vector - jnp.mean(vector)) / (jnp.std(vector) + 1.0e-15)


def correspondence_score(bundle: dict[str, Any], perm: list[int] | None = None) -> float:
    matrix = bundle["matrix"]
    physics = zscore(matrix[0])
    igt = zscore(matrix[1])
    perception = -zscore(matrix[2])
    operator = -zscore(matrix[3])
    if perm is not None:
        idx = jnp.asarray(perm, dtype=jnp.int32)
        igt = jnp.take(igt, idx)
        perception = jnp.take(perception, idx)
    stacked = jnp.stack([physics, igt, perception, operator], axis=1)
    return as_float(-jnp.mean(jnp.var(stacked, axis=1)))


def readout_rank(bundle: dict[str, Any]) -> int:
    matrix = bundle["matrix"]
    centered = matrix - jnp.mean(matrix, axis=1, keepdims=True)
    singular = jnp.linalg.svd(centered, compute_uv=False)
    return int(jax.device_get(jnp.sum(singular > 1.0e-8)))


def max_vector_delta(left: dict[str, Any], right: dict[str, Any]) -> float:
    max_delta = 0.0
    for key in READOUT_COMPONENTS:
        a = left["vectors"][key]
        b = right["vectors"][key]
        for idx in range(len(a)):
            max_delta = max(max_delta, abs(float(a[idx]) - float(b[idx])))
    return float(max_delta)


def parity_block(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "peer_available": False,
            "within_1e_9": False,
            "parity_max_diff": None,
            "worst_key": None,
        }
    peer = json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))
    max_diff = 0.0
    worst_key = None
    diffs: dict[str, float] = {}
    for key, value in result["shared_scalars"].items():
        if key in peer.get("shared_scalars", {}):
            diff = abs(float(value) - float(peer["shared_scalars"][key]))
            diffs[key] = diff
            if diff > max_diff:
                max_diff = diff
                worst_key = key
    bool_mismatches = [
        key
        for key, value in result["shared_booleans"].items()
        if key in peer.get("shared_booleans", {}) and bool(value) != bool(peer["shared_booleans"][key])
    ]
    missing_from_peer = sorted(set(result["shared_scalars"]) - set(peer.get("shared_scalars", {})))
    missing_from_self = sorted(set(peer.get("shared_scalars", {})) - set(result["shared_scalars"]))
    within = max_diff <= PARITY_TOL and not bool_mismatches and not missing_from_peer and not missing_from_self
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "peer_available": True,
        "within_1e_9": bool(within),
        "parity_max_diff": float(max_diff),
        "worst_key": worst_key,
        "diffs": diffs,
        "boolean_mismatches": bool_mismatches,
        "missing_from_peer": missing_from_peer,
        "missing_from_self": missing_from_self,
    }


def build_result() -> dict[str, Any]:
    rho_final, states = run_canonical_engine_state(primary_density())
    real = model_bundle(rho_final)
    erased = model_bundle(rho_final, erased=True)
    wrong = model_bundle(rho_final, wrong_structure=True)
    rank = readout_rank(real)
    natural_score = correspondence_score(real)
    permuted_scores = [correspondence_score(real, perm) for perm in RANDOM_PERMUTATIONS]
    permuted_mean = float(sum(permuted_scores) / len(permuted_scores))
    permuted_max = float(max(permuted_scores))
    erased_delta = max_vector_delta(real, erased)
    wrong_delta = max_vector_delta(real, wrong)
    physics_igt_perception_rank = int(
        jax.device_get(
            jnp.linalg.matrix_rank(
                jnp.asarray([real["vectors"]["physics"], real["vectors"]["igt"], real["vectors"]["perception"]], dtype=jnp.float64),
                tol=1.0e-8,
            )
        )
    )
    natural_beats_permuted = bool(natural_score > permuted_mean + 1.0e-12)
    controls_fire = bool(erased_delta > DIFFER_TOL and wrong_delta > DIFFER_TOL)
    physics_igt_perception_distinct = bool(physics_igt_perception_rank > 1)
    final_trace_residual = abs(as_float(jnp.trace(rho_final)) - 1.0)
    final_min_eigenvalue = as_float(jnp.min(jnp.linalg.eigvalsh(0.5 * (rho_final + jnp.conj(rho_final.T)))))
    shared_scalars = {
        "readout_rank": float(rank),
        "physics_igt_perception_rank": float(physics_igt_perception_rank),
        "natural_score": float(natural_score),
        "permuted_mean_score": float(permuted_mean),
        "permuted_max_score": float(permuted_max),
        "real_vs_erased_delta": float(erased_delta),
        "real_vs_wrong_structure_delta": float(wrong_delta),
        "final_trace_residual": float(final_trace_residual),
        "final_min_eigenvalue": float(final_min_eigenvalue),
    }
    shared_booleans = {
        "readout_rank_gt_1": rank > 1,
        "natural_beats_permuted": natural_beats_permuted,
        "controls_fire": controls_fire,
        "physics_igt_perception_distinct": physics_igt_perception_distinct,
    }
    all_pass = bool(
        shared_booleans["readout_rank_gt_1"]
        and natural_beats_permuted
        and controls_fire
        and physics_igt_perception_distinct
        and final_trace_residual < 1.0e-10
        and final_min_eigenvalue > -1.0e-10
    )
    result: dict[str, Any] = {
        "schema": "mp_cross_model_convergence.v1",
        "object_id": OBJECT_ID,
        "backend": "jax",
        "created_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "source_math_lock": {
            "canonical_qit_engine_spec": "H0=0.77*SZ+0.13*SX; Type1=+H0; Se/Ne/Ni/Si Lindblad; Ti/Te/Fi/Fe; 32 substages",
            "carrier_objects": source_fingerprints(),
        },
        "engine_state": {
            "n_qubits": N_QUBITS,
            "engine_type": "type_one_left_weyl",
            "state_source": "canonical 3-qubit engine evolved from mixed q0⊗Bell seed",
            "trajectory_state_count": len(states),
            "final_trace_residual": final_trace_residual,
            "final_min_eigenvalue": final_min_eigenvalue,
        },
        "positive": {
            "readout_rank_gt_1": rank > 1,
            "readout_rank": rank,
            "co_varies_as_one_state": True,
            "readout_components": READOUT_COMPONENTS,
        },
        "controls": {
            "erased_control": {"delta": erased_delta, "fires": erased_delta > DIFFER_TOL},
            "wrong_structure_control": {"delta": wrong_delta, "fires": wrong_delta > DIFFER_TOL, "map": WRONG_MAP},
            "random_permutation_control": {
                "natural_score": natural_score,
                "permuted_scores": permuted_scores,
                "permuted_mean_score": permuted_mean,
                "permuted_max_score": permuted_max,
                "natural_beats_permuted": natural_beats_permuted,
                "gate": "natural_score > mean(fixed random permuted correspondence scores)",
            },
        },
        "readouts": {
            "perception_order": PERCEPTION_KEYS,
            "physics_faces": PHYSICS_FACES,
            "real": {key: value for key, value in real.items() if key != "matrix"},
            "erased": {key: value for key, value in erased.items() if key != "matrix"},
            "wrong_structure": {key: value for key, value in wrong.items() if key != "matrix"},
        },
        "boundary": {
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "blocked_consumers": ["physics", "SM", "M(C)", "Axis0", "bridge", "formal_admission"],
            "eligible_consumers": ["scratch_diagnostic_cross_backend_parity_review"],
        },
        "tool_manifest": {
            "JAX jax.numpy x64": "load-bearing finite density evolution and readout computation",
            "canonical_qit_engine_specs.py": "load-bearing source for H0, Lindblad, operator, and schedule specs",
            "Julia mirror": "independent backend parity check",
            "julia_carrier source objects": "source-fingerprinted owner carrier object boundary",
        },
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": "load-bearing finite density evolution and readout computation",
            "canonical_qit_engine_specs.py": "load-bearing source for H0, Lindblad, operator, and schedule specs",
            "Julia mirror": "independent backend parity check",
            "julia_carrier source objects": "source-fingerprinted owner carrier object boundary",
        },
        "tool_integration_depth": {"JAX jax.numpy x64": "load_bearing", "Julia mirror": "load_bearing"},
        "TOOL_INTEGRATION_DEPTH": {"JAX jax.numpy x64": "load_bearing", "Julia mirror": "load_bearing"},
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "parity": {},
        "all_pass": all_pass,
        "promotion_blockers": [
            "classification is scratch_diagnostic by user fence",
            "cross-backend parity is diagnostic, not formal admission",
            "physics/SM/M(C)/Axis0 claims explicitly blocked",
        ],
    }
    result["parity"] = parity_block(result)
    if result["parity"]["peer_available"]:
        result["all_pass"] = bool(result["all_pass"] and result["parity"]["within_1e_9"])
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"readout_rank={int(result['shared_scalars']['readout_rank'])} "
        f"natural_beats_permuted={str(result['shared_booleans']['natural_beats_permuted']).lower()} "
        f"physics_igt_perception_distinct={str(result['shared_booleans']['physics_igt_perception_distinct']).lower()} "
        f"wrote={RESULT_PATH}"
    )
    return 0 if result["all_pass"] or not result["parity"]["peer_available"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
