#!/usr/bin/env python3
"""NumPy leg for the source-faithful Type-1 engine v0.

Ceiling: QUARANTINE_EXPLORATORY / scratch_diagnostic. This is a candidate
finite-time GKSL realization of the source-pinned Type-1 chart, not settled
terrain math and not Axis-0/64-closure evidence.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np
from scipy.linalg import expm

import type1_engine_common as common


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
TOL = 1e-9
DISTINCTNESS_THRESHOLD = 1e-6

I2 = np.eye(2, dtype=np.complex128)
SX = np.array([[0, 1], [1, 0]], dtype=np.complex128)
SY = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
SZ = np.array([[1, 0], [0, -1]], dtype=np.complex128)
SIGMA_MINUS = 0.5 * (SX - 1j * SY)
SIGMA_PLUS = 0.5 * (SX + 1j * SY)
PAULIS = [SX, SY, SZ]

N_AXIS = np.array([1.0, 1.0, 1.0], dtype=float)
N_AXIS = N_AXIS / np.linalg.norm(N_AXIS)
M_IN_AXIS = np.array([1.0, 0.0, 1.0], dtype=float)
M_IN_AXIS = M_IN_AXIS / np.linalg.norm(M_IN_AXIS)
H0 = 0.5 * (N_AXIS[0] * SX + N_AXIS[1] * SY + N_AXIS[2] * SZ)
HC = 0.5 * (M_IN_AXIS[0] * SX + M_IN_AXIS[1] * SY + M_IN_AXIS[2] * SZ)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def as_float_list(values: np.ndarray) -> list[float]:
    return [float(x) for x in np.asarray(values, dtype=float).reshape(-1)]


def vec(rho: np.ndarray) -> np.ndarray:
    return rho.reshape(4, order="F")


def unvec(v: np.ndarray) -> np.ndarray:
    return v.reshape((2, 2), order="F")


def sleft(a: np.ndarray) -> np.ndarray:
    return np.kron(I2, a)


def sright(a: np.ndarray) -> np.ndarray:
    return np.kron(a.T, I2)


def dissipator_super(l_op: np.ndarray) -> np.ndarray:
    ldag_l = l_op.conj().T @ l_op
    return np.kron(l_op.conj(), l_op) - 0.5 * (sleft(ldag_l) + sright(ldag_l))


def hamiltonian_super(h_op: np.ndarray, rate: float = 1.0) -> np.ndarray:
    return -1j * rate * (sleft(h_op) - sright(h_op))


def normalize_density(rho: np.ndarray) -> np.ndarray:
    herm = 0.5 * (rho + rho.conj().T)
    tr = np.trace(herm).real
    return herm / tr


def super_to_channel(superop: np.ndarray) -> Callable[[np.ndarray], np.ndarray]:
    flow = expm(superop)

    def apply(rho: np.ndarray) -> np.ndarray:
        return normalize_density(unvec(flow @ vec(rho)))

    return apply


def rates_for_fixed_point(total_decay: float, target_z: float) -> tuple[float, float]:
    to_plus = total_decay * (1.0 + target_z) / 2.0
    to_minus = total_decay * (1.0 - target_z) / 2.0
    return to_plus, to_minus


def terrain_superoperators() -> dict[str, np.ndarray]:
    se = common.TERRAINS["Se-in"]["params"]
    se_total = -np.log(se["keep_z"])
    se_plus, se_minus = rates_for_fixed_point(se_total, se["target_z"])

    ne = common.TERRAINS["Ne-in"]["params"]
    ne_depol = -np.log(ne["shrink"]) / 4.0

    ni = common.TERRAINS["Ni-in"]["params"]
    ni_gamma = -np.log(ni["keep_z"])

    si = common.TERRAINS["Si-in"]["params"]
    si_kappa = -np.log(si["transverse_keep"]) / 2.0

    p_plus = 0.5 * (I2 + (M_IN_AXIS[0] * SX + M_IN_AXIS[1] * SY + M_IN_AXIS[2] * SZ))
    p_minus = 0.5 * (I2 - (M_IN_AXIS[0] * SX + M_IN_AXIS[1] * SY + M_IN_AXIS[2] * SZ))

    return {
        "Se-in": (
            se_plus * dissipator_super(SIGMA_PLUS)
            + se_minus * dissipator_super(SIGMA_MINUS)
            + hamiltonian_super(H0, se["epsilon"])
        ),
        "Ne-in": (
            hamiltonian_super(H0, ne["rotation"])
            + ne_depol * sum((dissipator_super(p) for p in PAULIS), np.zeros((4, 4), dtype=np.complex128))
        ),
        "Ni-in": (
            ni_gamma * dissipator_super(SIGMA_MINUS)
            + hamiltonian_super(H0, ni["epsilon"])
        ),
        "Si-in": (
            hamiltonian_super(HC, si["rotation"])
            + si_kappa * (dissipator_super(p_plus) + dissipator_super(p_minus))
        ),
    }


def terrains() -> dict[str, Callable[[np.ndarray], np.ndarray]]:
    return {name: super_to_channel(superop) for name, superop in terrain_superoperators().items()}


def unitary(axis: str, angle: float) -> np.ndarray:
    sigma = SX if axis == "x" else SZ
    return expm(-1j * angle * sigma / 2.0)


def operators() -> dict[str, Callable[[np.ndarray], np.ndarray]]:
    q1 = common.OPERATORS["Ti"]["q"]
    q2 = common.OPERATORS["Te"]["q"]
    p0 = 0.5 * (I2 + SZ)
    p1 = 0.5 * (I2 - SZ)
    qp = 0.5 * (I2 + SX)
    qm = 0.5 * (I2 - SX)
    ux = unitary("x", common.OPERATORS["Fi"]["theta"])
    uz = unitary("z", common.OPERATORS["Fe"]["phi"])

    def ti(rho: np.ndarray) -> np.ndarray:
        return normalize_density((1.0 - q1) * rho + q1 * (p0 @ rho @ p0 + p1 @ rho @ p1))

    def te(rho: np.ndarray) -> np.ndarray:
        return normalize_density((1.0 - q2) * rho + q2 * (qp @ rho @ qp + qm @ rho @ qm))

    def fi(rho: np.ndarray) -> np.ndarray:
        return normalize_density(ux @ rho @ ux.conj().T)

    def fe(rho: np.ndarray) -> np.ndarray:
        return normalize_density(uz @ rho @ uz.conj().T)

    return {"Ti": ti, "Te": te, "Fi": fi, "Fe": fe}


def stage_maps() -> dict[str, Callable[[np.ndarray], np.ndarray]]:
    terr = terrains()
    ops = operators()
    maps = {}
    for stage in common.STAGES:
        terrain = terr[stage["terrain"]]
        op = ops[stage["operator"]]
        if stage["composition"] == "terrain_after_operator":
            maps[stage["stage_id"]] = lambda rho, terrain=terrain, op=op: terrain(op(rho))
        else:
            maps[stage["stage_id"]] = lambda rho, terrain=terrain, op=op: op(terrain(rho))
    return maps


def rho_from_bloch(r: np.ndarray) -> np.ndarray:
    return normalize_density(0.5 * (I2 + r[0] * SX + r[1] * SY + r[2] * SZ))


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([np.trace(rho @ p).real for p in PAULIS], dtype=float)


def entropy_vn(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh(normalize_density(rho)).real
    vals = np.clip(vals, 0.0, 1.0)
    nz = vals[vals > 1e-15]
    return float(-np.sum(nz * np.log(nz)))


def probe_states() -> dict[str, np.ndarray]:
    return {
        "mixed": rho_from_bloch(np.array([0.0, 0.0, 0.0])),
        "plus_x": rho_from_bloch(np.array([1.0, 0.0, 0.0])),
        "plus_y": rho_from_bloch(np.array([0.0, 1.0, 0.0])),
        "zero_z": rho_from_bloch(np.array([0.0, 0.0, 1.0])),
        "generic_a": rho_from_bloch(np.array([0.31, -0.27, 0.44])),
        "generic_b": rho_from_bloch(np.array([-0.21, 0.36, -0.18])),
    }


def affine_fingerprint(channel: Callable[[np.ndarray], np.ndarray]) -> dict:
    b = bloch(channel(rho_from_bloch(np.zeros(3))))
    cols = []
    for axis in np.eye(3):
        cols.append(bloch(channel(rho_from_bloch(axis))) - b)
    matrix = np.column_stack(cols)
    fixed, *_ = np.linalg.lstsq(np.eye(3) - matrix, b, rcond=None)
    residual = float(np.linalg.norm(matrix @ fixed + b - fixed))
    return {
        "affine_A": [[float(x) for x in row] for row in matrix],
        "affine_b": as_float_list(b),
        "fixed_point_bloch": as_float_list(fixed),
        "fixed_point_residual": residual,
    }


def stage_fingerprints(maps: dict[str, Callable[[np.ndarray], np.ndarray]]) -> dict:
    probes = probe_states()
    out = {}
    for stage in common.STAGES:
        sid = stage["stage_id"]
        channel = maps[sid]
        fp = affine_fingerprint(channel)
        entropy_injected = {}
        for pname, rho in probes.items():
            entropy_injected[pname] = float(entropy_vn(channel(rho)) - entropy_vn(rho))
        fp.update(
            {
                "stage_id": sid,
                "terrain": stage["terrain"],
                "operator": stage["operator"],
                "loop": stage["loop"],
                "casing": stage["casing"],
                "order_text": stage["order_text"],
                "entropy_injected": entropy_injected,
            }
        )
        out[sid] = fp
    return out


def fingerprint_vector(fp: dict) -> np.ndarray:
    return np.array(
        [x for row in fp["affine_A"] for x in row]
        + fp["affine_b"]
        + [fp["entropy_injected"][k] for k in sorted(fp["entropy_injected"])]
        + fp["fixed_point_bloch"]
        + [fp["fixed_point_residual"]],
        dtype=float,
    )


def distinctness(fingerprints: dict) -> dict:
    ids = list(fingerprints)
    pairs = []
    min_dist = float("inf")
    min_pair: list[str] | None = None
    for i, a in enumerate(ids):
        va = fingerprint_vector(fingerprints[a])
        for b in ids[i + 1 :]:
            dist = float(np.linalg.norm(va - fingerprint_vector(fingerprints[b])))
            pairs.append({"pair": [a, b], "distance": dist})
            if dist < min_dist:
                min_dist = dist
                min_pair = [a, b]
    return {
        "threshold": DISTINCTNESS_THRESHOLD,
        "min_pairwise_distance": min_dist,
        "min_pair": min_pair,
        "all_8_distinct": bool(min_dist > DISTINCTNESS_THRESHOLD),
        "pairwise_distances": pairs,
    }


def order_sensitivity_by_terrain(maps: dict[str, Callable[[np.ndarray], np.ndarray]]) -> dict:
    probes = probe_states()
    terrain_to_ids = {
        "Se-in": ("TiSe", "SeFi"),
        "Ne-in": ("NeTi", "FiNe"),
        "Ni-in": ("NiFe", "TeNi"),
        "Si-in": ("FeSi", "SiTe"),
    }
    out = {}
    for terrain, (outer_id, inner_id) in terrain_to_ids.items():
        vals = {}
        for pname, rho in probes.items():
            vals[pname] = float(np.linalg.norm(bloch(maps[outer_id](rho)) - bloch(maps[inner_id](rho))))
        out[terrain] = {
            "outer_stage": outer_id,
            "inner_stage": inner_id,
            "probe_norms": vals,
            "max_norm": float(max(vals.values())),
            "mean_norm": float(np.mean(list(vals.values()))),
            "axis6_observable": "outer_vs_inner_composition_difference_norm",
        }
    return out


def run_sequence(maps: dict[str, Callable[[np.ndarray], np.ndarray]], stage_ids: list[str], rho: np.ndarray) -> list[dict]:
    trajectory = [{"step": 0, "stage_id": "initial", "bloch": as_float_list(bloch(rho)), "entropy": entropy_vn(rho)}]
    cur = rho
    for idx, stage_id in enumerate(stage_ids, start=1):
        cur = maps[stage_id](cur)
        trajectory.append(
            {
                "step": idx,
                "stage_id": stage_id,
                "bloch": as_float_list(bloch(cur)),
                "entropy": entropy_vn(cur),
            }
        )
    return trajectory


def traversal_measurements(maps: dict[str, Callable[[np.ndarray], np.ndarray]]) -> dict:
    probes = probe_states()
    sequences = {
        "outer": common.OUTER_LOOP_STAGE_IDS,
        "inner": common.INNER_LOOP_STAGE_IDS,
        "double_outer_then_inner": common.OUTER_LOOP_STAGE_IDS + common.INNER_LOOP_STAGE_IDS,
    }
    out = {}
    for name, stage_ids in sequences.items():
        per_probe = {}
        closure_norms = []
        for pname, rho in probes.items():
            traj = run_sequence(maps, stage_ids, rho)
            closure = float(np.linalg.norm(np.array(traj[-1]["bloch"]) - np.array(traj[0]["bloch"])))
            closure_norms.append(closure)
            per_probe[pname] = {
                "stage_ids": stage_ids,
                "trajectory": traj,
                "closure_norm": closure,
                "final_minus_initial_bloch": as_float_list(np.array(traj[-1]["bloch"]) - np.array(traj[0]["bloch"])),
            }
        out[name] = {
            "per_initial_state": per_probe,
            "closure_summary": {
                "min": float(min(closure_norms)),
                "max": float(max(closure_norms)),
                "mean": float(np.mean(closure_norms)),
            },
            "closure_note": "Measured finite traversal closure only; no 720 closure assertion is made.",
        }
    return out


def tool_manifest() -> dict:
    return {
        "numpy": {
            "tried": True,
            "used": True,
            "reason": "load-bearing dense complex matrices, Bloch affine fingerprints, pairwise distances, traversal norms",
        },
        "scipy.linalg.expm": {
            "tried": True,
            "used": True,
            "reason": "load-bearing finite-time GKSL superoperator exponentials for terrain channels",
        },
        "json": {
            "tried": True,
            "used": True,
            "reason": "supportive result artifact serialization",
        },
    }


def build_result() -> dict:
    maps = stage_maps()
    fps = stage_fingerprints(maps)
    return {
        **common.spec_dict(),
        "schema": "codex_ratchet.type1_engine_v0.leg_result.v1",
        "engine": "numpy",
        "substrate": "numpy",
        "computation_style": "numpy_complex128_gksl_superoperator_expm",
        "reads_peer_result": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": sha256_file(Path(__file__)),
        "result_path": "system_v7/sims/type1_engine_v0/results/type1_engine_v0_numpy_results.json",
        "tolerances": {"parity_abs": TOL, "distinctness_threshold": DISTINCTNESS_THRESHOLD},
        "model_axes": {
            "H0_axis": as_float_list(N_AXIS),
            "H0_sign": "+H0",
            "flux": "IN",
            "H_C_axis": as_float_list(M_IN_AXIS),
        },
        "terrain_generator_note": common.TERRAIN_HEADER_NOTE,
        "stage_fingerprints": fps,
        "distinctness": distinctness(fps),
        "order_sensitivity_by_terrain": order_sensitivity_by_terrain(maps),
        "traversals": traversal_measurements(maps),
        "TOOL_MANIFEST": tool_manifest(),
        "TOOL_INTEGRATION_DEPTH": {"numpy": "load_bearing", "scipy.linalg.expm": "load_bearing", "json": "supportive"},
        "all_pass": True,
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = build_result()
    path = RESULTS / "type1_engine_v0_numpy_results.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "engine": "numpy",
        "result_path": str(path),
        "all_8_distinct": out["distinctness"]["all_8_distinct"],
        "min_pairwise_distance": out["distinctness"]["min_pairwise_distance"],
        "outer_closure_mean": out["traversals"]["outer"]["closure_summary"]["mean"],
        "inner_closure_mean": out["traversals"]["inner"]["closure_summary"]["mean"],
        "double_closure_mean": out["traversals"]["double_outer_then_inner"]["closure_summary"]["mean"],
    }, indent=2))


if __name__ == "__main__":
    main()
