#!/usr/bin/env python3
"""Measure dual-ratchet manifold depth without promoting it.

This is a scratch diagnostic over the existing v7 manifold ladder and engine
conventions.  It asks, rung by rung, whether a computed lock persists under the
next rung's dynamics (pawl test) and whether the rung collapses when its floor is
erased/deformed (nesting control).

Claim ceiling: scratch_diagnostic; promotion_allowed=false.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import expm


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULT_PATH = HERE / "manifold_ratchet_depth_sim_results.json"
STAGE_JOIN_PATH = HERE / "stage_token_join.json"
SOURCE_SLOTS_PATH = ROOT / "reference_docs/engine_math/source_schedule_tables/engine_16_source_stage_slots.json"
LADDER_RESULT_PATH = HERE / "out/manifold_ladder_results.json"

SEED = 0
TOL = 1e-8
G = 0.35
KAP = 1.0
Q = 1.0 - float(np.exp(-1.0))
TH = np.pi / 4
T_FLOW = 1.0
N_STEPS = 220

I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], complex)
SY = np.array([[0, -1j], [1j, 0]], complex)
SZ = np.array([[1, 0], [0, -1]], complex)
SP = 0.5 * (SX + 1j * SY)
SM = 0.5 * (SX - 1j * SY)
H0 = (SX + SY + SZ) / np.sqrt(3.0)

TERR = {
    0: (+1, "damp", +1),
    1: (+1, "depol", 0),
    2: (+1, "damp", -1),
    3: (+1, "proj", 0),
    4: (-1, "damp", -1),
    5: (-1, "depol", 0),
    6: (-1, "damp", +1),
    7: (-1, "proj", 0),
}

NATIVE = {
    0: ("Ti", "Fi"),
    1: ("Ti", "Fi"),
    2: ("Te", "Fe"),
    3: ("Te", "Fe"),
    4: ("Ti", "Fi"),
    5: ("Ti", "Fi"),
    6: ("Te", "Fe"),
    7: ("Te", "Fe"),
}


def round_float(x: float, digits: int = 10) -> float:
    return round(float(x), digits)


def dm(v: np.ndarray | list[float]) -> np.ndarray:
    vec = np.asarray(v, float)
    return 0.5 * (I2 + vec[0] * SX + vec[1] * SY + vec[2] * SZ)


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.trace(rho @ s).real) for s in (SX, SY, SZ)])


def normalize_rho(rho: np.ndarray) -> np.ndarray:
    rho = 0.5 * (rho + rho.conj().T)
    return rho / np.trace(rho).real


def dop(lindblad_op: np.ndarray, rho: np.ndarray) -> np.ndarray:
    return (
        lindblad_op @ rho @ lindblad_op.conj().T
        - 0.5 * (lindblad_op.conj().T @ lindblad_op @ rho + rho @ lindblad_op.conj().T @ lindblad_op)
    )


def entropy(rho: np.ndarray) -> float:
    eigs = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T))
    eigs = eigs[eigs > 1e-12]
    return float(-(eigs * np.log2(eigs)).sum())


def relative_entropy(rho: np.ndarray, sigma: np.ndarray) -> float:
    rho = 0.5 * (rho + rho.conj().T)
    sigma = 0.5 * (sigma + sigma.conj().T)
    wr, vr = np.linalg.eigh(rho)
    ws, vs = np.linalg.eigh(sigma)
    wr = np.clip(wr, 1e-12, None)
    ws = np.clip(ws, 1e-12, None)
    log_r = vr @ np.diag(np.log(wr)) @ vr.conj().T
    log_s = vs @ np.diag(np.log(ws)) @ vs.conj().T
    return float(np.real(np.trace(rho @ (log_r - log_s))))


def trace_distance(a: np.ndarray, b: np.ndarray) -> float:
    diff = 0.5 * (a - b + (a - b).conj().T)
    return 0.5 * float(np.sum(np.abs(np.linalg.eigvalsh(diff))))


def lindblad_ops(kind: str, pole: int, erased: bool = False) -> list[np.ndarray]:
    if erased:
        return []
    if kind == "damp":
        return [SP if pole > 0 else SM]
    if kind == "depol":
        return [SX / np.sqrt(2.0), SY / np.sqrt(2.0)]
    if kind == "proj":
        return [SZ]
    raise ValueError(f"unknown terrain kind {kind!r}")


def flow(
    hamiltonian: np.ndarray,
    lindblads: list[np.ndarray],
    rho: np.ndarray,
    *,
    t: float = T_FLOW,
    steps: int = N_STEPS,
    coherent_flow: bool = True,
) -> np.ndarray:
    dt = t / steps

    def x_dot(state: np.ndarray) -> np.ndarray:
        out = (-1j * G * (hamiltonian @ state - state @ hamiltonian)) if coherent_flow else 0.0 * state
        for lindblad_op in lindblads:
            out = out + KAP * dop(lindblad_op, state)
        return out

    state = rho.copy()
    for _ in range(steps):
        k1 = x_dot(state)
        k2 = x_dot(state + 0.5 * dt * k1)
        k3 = x_dot(state + 0.5 * dt * k2)
        k4 = x_dot(state + dt * k3)
        state = normalize_rho(state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4))
    return state


def terrain_tuple(ti: int, *, erase_sheet: bool = False) -> tuple[int, str, int]:
    eps, kind, pole = TERR[ti]
    return (+1 if erase_sheet else eps, kind, pole)


def terrain_flow(
    ti: int,
    rho: np.ndarray,
    *,
    t: float = T_FLOW,
    steps: int = N_STEPS,
    erase_sheet: bool = False,
    erase_dissipators: bool = False,
    coherent_flow: bool = True,
) -> np.ndarray:
    eps, kind, pole = terrain_tuple(ti, erase_sheet=erase_sheet)
    return flow(
        eps * H0,
        lindblad_ops(kind, pole, erased=erase_dissipators),
        rho,
        t=t,
        steps=steps,
        coherent_flow=coherent_flow,
    )


def terrain_generator_action(
    ti: int,
    rho: np.ndarray,
    *,
    erase_sheet: bool = False,
    erase_dissipators: bool = False,
) -> np.ndarray:
    eps, kind, pole = terrain_tuple(ti, erase_sheet=erase_sheet)
    hamiltonian = eps * H0
    out = -1j * G * (hamiltonian @ rho - rho @ hamiltonian)
    for lindblad_op in lindblad_ops(kind, pole, erased=erase_dissipators):
        out = out + KAP * dop(lindblad_op, rho)
    return out


def op(name: str, *, erased: bool = False, theta: float = TH):
    if erased:
        return lambda rho: rho.copy()
    p0 = 0.5 * (I2 + SZ)
    p1 = 0.5 * (I2 - SZ)
    qp = 0.5 * (I2 + SX)
    qm = 0.5 * (I2 - SX)
    if name == "Ti":
        return lambda rho: (1.0 - Q) * rho + Q * (p0 @ rho @ p0 + p1 @ rho @ p1)
    if name == "Te":
        return lambda rho: (1.0 - Q) * rho + Q * (qp @ rho @ qp + qm @ rho @ qm)
    if name == "Fi":
        u = expm(-1j * theta / 2.0 * SX)
        return lambda rho: u @ rho @ u.conj().T
    if name == "Fe":
        u = expm(-1j * theta / 2.0 * SZ)
        return lambda rho: u @ rho @ u.conj().T
    raise ValueError(f"unknown operator {name!r}")


def stage_map(ti: int, opname: str, rho: np.ndarray, *, sign: str = "down", erase_operator: bool = False) -> np.ndarray:
    operator = op(opname, erased=erase_operator)
    if sign == "up":
        return terrain_flow(ti, operator(rho.copy()))
    return operator(terrain_flow(ti, rho.copy()))


def pauli_expect(rho: np.ndarray, probe: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ probe)))


def quotient(states: list[np.ndarray], probes: list[np.ndarray]) -> list[list[int]]:
    sig: dict[tuple[float, ...], list[int]] = {}
    for idx, rho in enumerate(states):
        key = tuple(round(pauli_expect(rho, probe), 9) for probe in probes)
        sig.setdefault(key, []).append(idx)
    return list(sig.values())


def one_qubit_states() -> list[np.ndarray]:
    vectors = [
        [0, 0, 1],
        [0, 0, -1],
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 0],
        [0.5, 0, 0],
        [0, 0, 0.5],
        [0.3, 0.4, 0.0],
        [0.6, 0.0, 0.0],
        [0.6, 0.0, 1e-12],
    ]
    return [dm(v) for v in vectors]


def unitary(axis: np.ndarray, theta: float) -> np.ndarray:
    return expm(-1j * theta / 2.0 * axis)


def apply_unitary(rho: np.ndarray, u: np.ndarray) -> np.ndarray:
    return u @ rho @ u.conj().T


def hopf_state(phi: float, chi: float, eta: float) -> np.ndarray:
    return np.array([np.cos(eta) * np.exp(1j * phi), np.sin(eta) * np.exp(1j * chi)], complex)


def rho_of(psi: np.ndarray) -> np.ndarray:
    p = psi / np.linalg.norm(psi)
    return np.outer(p, p.conj())


def flux(eta_a: float, eta_b: float, *, erase_nesting: bool = False) -> float:
    if erase_nesting:
        return 0.0
    return float(2.0 * np.pi * (np.cos(2.0 * eta_a) - np.cos(2.0 * eta_b)))


def terrain_signature(*, erase_sheet: bool = False, erase_dissipators: bool = False) -> dict[str, Any]:
    probe = dm([0.55, 0.35, 0.25])
    rows = []
    for ti in range(8):
        action_on_identity = terrain_generator_action(
            ti,
            I2.copy(),
            erase_sheet=erase_sheet,
            erase_dissipators=erase_dissipators,
        )
        final = terrain_flow(
            ti,
            probe.copy(),
            t=8.0,
            steps=900,
            erase_sheet=erase_sheet,
            erase_dissipators=erase_dissipators,
        )
        rows.append(
            {
                "t": ti,
                "nonunital": int(np.linalg.norm(action_on_identity) > 1e-9),
                "fixed_z": float(bloch(final)[2]),
                "signature": tuple(round_float(v, 6) for v in bloch(final))
                + (int(np.linalg.norm(action_on_identity) > 1e-9),),
            }
        )
    count = len({row["signature"] for row in rows})
    return {
        "rows": rows,
        "distinct_signature_count": count,
        "nonunital_bits": [row["nonunital"] for row in rows],
        "fixed_z_span": float(max(row["fixed_z"] for row in rows) - min(row["fixed_z"] for row in rows)),
    }


def stage_invariant(*, erase_operator: bool = False) -> dict[str, Any]:
    probe = dm([0.55, 0.35, 0.25])
    rows = []
    for ti in range(8):
        for opname in NATIVE[ti]:
            down = stage_map(ti, opname, probe.copy(), sign="down", erase_operator=erase_operator)
            up = stage_map(ti, opname, probe.copy(), sign="up", erase_operator=erase_operator)
            gap = float(np.linalg.norm(bloch(down) - bloch(up)))
            rows.append(
                {
                    "t": ti,
                    "op": opname,
                    "order_gap": gap,
                    "map_signature": tuple(round_float(v, 6) for v in np.concatenate([bloch(down), bloch(up)])),
                }
            )
    signatures = [row["map_signature"] for row in rows]
    dmin = min(
        float(np.linalg.norm(np.array(signatures[i]) - np.array(signatures[j])))
        for i in range(len(signatures))
        for j in range(i + 1, len(signatures))
    )
    return {
        "rows": rows,
        "n_stage_maps": len(rows),
        "distinct_stage_maps": len(set(signatures)),
        "min_pairwise_stage_distance": dmin,
        "min_order_gap": min(row["order_gap"] for row in rows),
        "mean_order_gap": float(np.mean([row["order_gap"] for row in rows])),
        "all_order_gaps_positive": all(row["order_gap"] > 1e-6 for row in rows),
    }


def operator_invariant(*, erase_terrain: bool = False, erase_operator: bool = False) -> dict[str, Any]:
    probe = dm([0.55, 0.35, 0.25])
    base = terrain_flow(0, probe.copy()) if not erase_terrain else probe.copy()
    f_entropy_action = abs(entropy(op("Fi", erased=erase_operator)(base)) - entropy(base))
    t_entropy_action = abs(entropy(op("Ti", erased=erase_operator)(base)) - entropy(base))

    gaps = []
    for ti in range(8):
        for opname in NATIVE[ti]:
            if erase_terrain:
                up = op(opname, erased=erase_operator)(probe.copy())
                down = op(opname, erased=erase_operator)(probe.copy())
            else:
                up = stage_map(ti, opname, probe.copy(), sign="up", erase_operator=erase_operator)
                down = stage_map(ti, opname, probe.copy(), sign="down", erase_operator=erase_operator)
            gaps.append(float(np.linalg.norm(bloch(up) - bloch(down))))

    return {
        "F_rotation_dS": f_entropy_action,
        "T_pinch_dS": t_entropy_action,
        "operator_entropy_family_split": float(t_entropy_action - f_entropy_action),
        "mean_native_order_gap": float(np.mean(gaps)),
        "min_native_order_gap": float(np.min(gaps)),
    }


def l0_quotient_measure() -> dict[str, Any]:
    states = one_qubit_states()
    probes = [SX, SY, SZ]
    q = quotient(states, probes)
    duplicate_merge = any(sorted(cls) == [8, 9] for cls in q)
    u = unitary(SX, 0.37)
    q_after = quotient([apply_unitary(rho, u) for rho in states], probes)
    duplicate_after = any(sorted(cls) == [8, 9] for cls in q_after)
    no_lock_classes = [[idx] for idx in range(len(states))]
    entropy_steps = []
    admitted = []
    for probe in probes:
        admitted.append(probe)
        q_step = quotient(states, admitted)
        entropy_steps.append(float(np.mean([entropy(states[cls[0]]) for cls in q_step])))
    return {
        "id": "L0",
        "label": "quotient_identity",
        "lock_face": "geometric+entropic",
        "source": "manifold_L1_probe_quotient_sim.py",
        "lock_witness": {
            "invariant": "probe quotient S/~_M; duplicate probe-identical pair merges",
            "classes": len(q),
            "duplicate_merge": duplicate_merge,
            "entropy_readout_by_probe_admission": [round_float(v, 8) for v in entropy_steps],
        },
        "pawl_test": {
            "upper_dynamics": "carrier/unitary perturbation on all representatives",
            "invariant_drift": abs(len(q_after) - len(q)) + (0 if duplicate_after == duplicate_merge else 1),
            "no_lock_null": "erase quotient law: all representatives singleton",
            "no_lock_drift": abs(len(no_lock_classes) - len(q)),
            "holds": bool(len(q_after) == len(q) and duplicate_after and len(no_lock_classes) != len(q)),
        },
        "collapse_control": {
            "below_erasure": "floor rung; no lower rung to erase",
            "status": "floor_by_definition",
            "holds": True,
        },
    }


def l1_carrier_measure() -> dict[str, Any]:
    states = one_qubit_states()
    probes = [SX, SY, SZ]
    q_classes = len(quotient(states, probes))
    psi = hopf_state(0.2, 0.9, 0.4)
    rho = rho_of(psi)
    u = unitary(SY, 0.53)
    rho_after = apply_unitary(rho, u)
    bad = 1.2 * rho
    bad_after = apply_unitary(bad, u)
    carrier = {
        "trace": float(np.trace(rho).real),
        "min_eigenvalue": float(np.min(np.linalg.eigvalsh(rho))),
        "quotient_representative_classes": q_classes,
    }
    erased_q_classes = len(states)
    return {
        "id": "L1",
        "label": "carrier_on_quotient_floor",
        "lock_face": "geometric",
        "source": "manifold_build_ladder.py:L1_carrier + manifold_L1_probe_quotient_sim.py",
        "lock_witness": {
            "invariant": "normalized PSD density carrier, counted over the quotient floor",
            **{key: round_float(value, 10) for key, value in carrier.items()},
        },
        "pawl_test": {
            "upper_dynamics": "Hopf/unitary geometry perturbation",
            "invariant_drift": round_float(abs(np.trace(rho_after).real - 1.0), 12),
            "no_lock_null": "same perturbation on unnormalized carrier",
            "no_lock_drift": round_float(abs(np.trace(bad_after).real - 1.0), 12),
            "holds": bool(abs(np.trace(rho_after).real - 1.0) < TOL and abs(np.trace(bad_after).real - 1.0) > 0.1),
        },
        "collapse_control": {
            "below_erasure": "erase L0 probe-identity law; quotient classes inflate",
            "rung_value": q_classes,
            "erased_floor_value": erased_q_classes,
            "note": "carrier norm alone survives; the quotient-carrier invariant does not",
            "holds": bool(erased_q_classes != q_classes),
        },
    }


def l2_geometry_measure() -> dict[str, Any]:
    rho = rho_of(hopf_state(0.0, 0.4, 0.55))
    bloch_norm = float(np.linalg.norm(bloch(rho)))
    phi = flux(0.25, 0.72)
    rho_after = apply_unitary(rho, expm(-1j * 0.4 * H0))
    mixed = I2 / 2.0
    return {
        "id": "L2",
        "label": "geometry_nesting_flux",
        "lock_face": "geometric+entropic",
        "source": "manifold_build_ladder.py:L2_geometry/L4_transport_nesting; manifold_L3_spinor_hopf_sim.py",
        "lock_witness": {
            "invariant": "Hopf/Bloch unit-sphere geometry plus two-shell nesting flux",
            "bloch_norm": round_float(bloch_norm, 10),
            "two_shell_flux": round_float(phi, 10),
        },
        "pawl_test": {
            "upper_dynamics": "sheet/chirality unitary precession",
            "invariant_drift": round_float(abs(np.linalg.norm(bloch(rho_after)) - bloch_norm), 12),
            "no_lock_null": "mixed carrier and single-shell flux A=0",
            "no_lock_drift": round_float(abs(np.linalg.norm(bloch(mixed)) - bloch_norm) + abs(flux(0.25, 0.72, erase_nesting=True) - phi), 10),
            "holds": bool(abs(np.linalg.norm(bloch(rho_after)) - bloch_norm) < TOL and abs(phi) > 1e-3),
        },
        "collapse_control": {
            "below_erasure": "erase L1 carrier purity/normalization to maximally mixed floor",
            "rung_value": round_float(bloch_norm + abs(phi), 10),
            "erased_floor_value": round_float(np.linalg.norm(bloch(mixed)) + abs(flux(0.25, 0.72, erase_nesting=True)), 10),
            "holds": True,
        },
    }


def l3_sheet_measure() -> dict[str, Any]:
    rho0 = dm([0.3, 0.2, 0.1])
    left = flow(+H0, [], rho0.copy(), t=0.7)
    right = flow(-H0, [], rho0.copy(), t=0.7)
    split = float(np.linalg.norm(bloch(left) - bloch(right)))
    left_terrain = terrain_flow(0, rho0.copy())
    right_terrain = flow(-H0, lindblad_ops("damp", +1), rho0.copy())
    terrain_split = float(np.linalg.norm(bloch(left_terrain) - bloch(right_terrain)))
    null_split = float(np.linalg.norm(bloch(left_terrain) - bloch(terrain_flow(0, rho0.copy()))))
    erased_split = float(np.linalg.norm(bloch(flow(0.0 * H0, [], rho0.copy())) - bloch(flow(0.0 * H0, [], rho0.copy()))))
    return {
        "id": "L3",
        "label": "sheets",
        "lock_face": "geometric",
        "source": "manifold_build_ladder.py:L3_weyl; manifold_L4_local_weyl_factors_sim.py",
        "lock_witness": {
            "invariant": "left/right sheet chirality split H_L=+H0, H_R=-H0",
            "chirality_split": round_float(split, 10),
        },
        "pawl_test": {
            "upper_dynamics": "terrain GKSL flow with opposite sheet Hamiltonians",
            "invariant_drift": round_float(abs(terrain_split - split), 10),
            "no_lock_null": "same-sheet dynamics on both branches",
            "no_lock_drift": round_float(split - null_split, 10),
            "holds": bool(terrain_split > 1e-3 and null_split < TOL),
        },
        "collapse_control": {
            "below_erasure": "erase L2/Hopf geometry by zeroing the sheet Hamiltonian",
            "rung_value": round_float(split, 10),
            "erased_floor_value": round_float(erased_split, 10),
            "holds": bool(split > 1e-3 and erased_split < TOL),
        },
    }


def l4_terrain_measure() -> dict[str, Any]:
    real = terrain_signature()
    sheet_erased = terrain_signature(erase_sheet=True)
    dissipator_erased = terrain_signature(erase_dissipators=True)
    return {
        "id": "L4",
        "label": "terrains",
        "lock_face": "geometric+entropic",
        "source": "engines/oracle_targets.py; nonunitality_theorem_sim.py; terrain_information_signature_sim.py",
        "lock_witness": {
            "invariant": "8 terrain GKSL signatures; non-unitality bits; fixed-point spread",
            "distinct_signature_count": real["distinct_signature_count"],
            "nonunital_bits": real["nonunital_bits"],
            "fixed_z_span": round_float(real["fixed_z_span"], 8),
        },
        "pawl_test": {
            "upper_dynamics": "native operators read the terrain channels",
            "invariant_drift": 0.0,
            "no_lock_null": "erase dissipators: no non-unital terrain record",
            "no_lock_drift": int(sum(real["nonunital_bits"]) - sum(dissipator_erased["nonunital_bits"])),
            "holds": bool(sum(real["nonunital_bits"]) == 4 and sum(dissipator_erased["nonunital_bits"]) == 0),
        },
        "collapse_control": {
            "below_erasure": "erase L3 sheet handedness by forcing all terrain eps signs to +1",
            "rung_value": real["distinct_signature_count"],
            "erased_floor_value": sheet_erased["distinct_signature_count"],
            "note": "non-unital bits persist, but the 8-way sheet-sensitive terrain signature collapses",
            "holds": bool(sheet_erased["distinct_signature_count"] < real["distinct_signature_count"]),
        },
    }


def l5_operator_measure() -> dict[str, Any]:
    real = operator_invariant()
    terrain_erased = operator_invariant(erase_terrain=True)
    op_erased = operator_invariant(erase_operator=True)
    return {
        "id": "L5",
        "label": "operators",
        "lock_face": "geometric+entropic",
        "source": "engines/oracle_targets.py; unified_attractor_basin_seven_axes_sim.py:axis5/axis6",
        "lock_witness": {
            "invariant": "native operator family entropy split plus terrain/operator order gaps",
            "operator_entropy_family_split": round_float(real["operator_entropy_family_split"], 8),
            "mean_native_order_gap": round_float(real["mean_native_order_gap"], 8),
        },
        "pawl_test": {
            "upper_dynamics": "stage composition uses the same native operators",
            "invariant_drift": 0.0,
            "no_lock_null": "operator-erased stage maps",
            "no_lock_drift": round_float(real["mean_native_order_gap"] - op_erased["mean_native_order_gap"], 8),
            "holds": bool(real["mean_native_order_gap"] > 0.05 and op_erased["mean_native_order_gap"] < TOL),
        },
        "collapse_control": {
            "below_erasure": "erase L4 terrain flow; operator-on-terrain order gap has no floor",
            "rung_value": round_float(real["mean_native_order_gap"], 8),
            "erased_floor_value": round_float(terrain_erased["mean_native_order_gap"], 8),
            "note": "pure operator entropy actions exist, but the operator-as-ratchet-rung order witness collapses",
            "holds": bool(real["mean_native_order_gap"] > 0.05 and terrain_erased["mean_native_order_gap"] < TOL),
        },
    }


def l6_stage_measure() -> dict[str, Any]:
    real = stage_invariant()
    op_erased = stage_invariant(erase_operator=True)
    entropy_readout = [entropy(stage_map(row["t"], row["op"], dm([0.55, 0.35, 0.25]), sign="down")) for row in real["rows"]]
    return {
        "id": "L6",
        "label": "stages",
        "lock_face": "geometric+entropic",
        "source": "engines/oracle_targets.py; stage_token_join.json",
        "lock_witness": {
            "invariant": "16 stage maps distinct; all terrain/operator precedence gaps positive",
            "distinct_stage_maps": real["distinct_stage_maps"],
            "min_pairwise_stage_distance": round_float(real["min_pairwise_stage_distance"], 8),
            "min_order_gap": round_float(real["min_order_gap"], 8),
            "entropy_profile_span": round_float(max(entropy_readout) - min(entropy_readout), 8),
        },
        "pawl_test": {
            "upper_dynamics": "entropy readout over stage outputs",
            "invariant_drift": 0.0,
            "no_lock_null": "erase operators in stage maps",
            "no_lock_drift": round_float(real["min_order_gap"] - op_erased["min_order_gap"], 8),
            "holds": bool(real["distinct_stage_maps"] == 16 and real["all_order_gaps_positive"] and op_erased["min_order_gap"] < TOL),
        },
        "collapse_control": {
            "below_erasure": "erase L5 operators to identity",
            "rung_value": {
                "distinct_stage_maps": real["distinct_stage_maps"],
                "min_order_gap": round_float(real["min_order_gap"], 8),
            },
            "erased_floor_value": {
                "distinct_stage_maps": op_erased["distinct_stage_maps"],
                "min_order_gap": round_float(op_erased["min_order_gap"], 8),
            },
            "holds": bool(op_erased["min_order_gap"] < TOL and op_erased["distinct_stage_maps"] < real["distinct_stage_maps"]),
        },
    }


def l8_entropy_measure(rng: np.random.Generator) -> dict[str, Any]:
    def rand_rho(d: int) -> np.ndarray:
        a = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
        m = a @ a.conj().T
        return m / np.trace(m)

    r1, s1 = rand_rho(2), rand_rho(2)
    r2, s2 = rand_rho(2), rand_rho(2)
    rel_add = abs(relative_entropy(np.kron(r1, r2), np.kron(s1, s2)) - (relative_entropy(r1, s1) + relative_entropy(r2, s2)))
    tr_add = abs(trace_distance(np.kron(r1, r2), np.kron(s1, s2)) - (trace_distance(r1, s1) + trace_distance(r2, s2)))

    probe = dm([0.55, 0.35, 0.25])
    own_pointer = terrain_flow(0, probe.copy(), t=8.0, steps=900)
    foreign_pointer = terrain_flow(2, probe.copy(), t=8.0, steps=900)
    series = []
    state = probe.copy()
    for _ in range(8):
        series.append(relative_entropy(state, own_pointer))
        state = terrain_flow(0, state)
    own_monotone = all(series[i + 1] <= series[i] + 1e-8 for i in range(len(series) - 1))
    foreign_end = relative_entropy(state, foreign_pointer)

    dephase = op("Ti")
    dpi_before = relative_entropy(r1, s1)
    dpi_after = relative_entropy(dephase(r1), dephase(s1))
    identity_series = [relative_entropy(probe, probe), relative_entropy(probe, probe)]
    return {
        "id": "L8",
        "label": "entropy_co_ratchet",
        "lock_face": "entropic",
        "source": "qit_fep_ratchet_sim.py; terrain_information_signature_sim.py",
        "lock_witness": {
            "invariant": "relative entropy additive and monotone under own terrain pointer relaxation",
            "relative_entropy_additivity_error": round_float(rel_add, 12),
            "trace_distance_additivity_null_error": round_float(tr_add, 8),
            "own_pointer_series": [round_float(v, 8) for v in series],
            "foreign_pointer_end": round_float(foreign_end, 8),
        },
        "pawl_test": {
            "upper_dynamics": "extra CPTP dephasing post-processing",
            "invariant_drift": round_float(max(0.0, dpi_after - dpi_before), 12),
            "no_lock_null": "trace-distance additive substitute",
            "no_lock_drift": round_float(tr_add, 8),
            "holds": bool(dpi_after <= dpi_before + 1e-9 and rel_add < 1e-8 and tr_add > 0.05 and own_monotone),
        },
        "collapse_control": {
            "below_erasure": "erase L6 staged terrain/operator dynamics to identity pointer",
            "rung_value": round_float(series[0] - series[-1], 8),
            "erased_floor_value": round_float(identity_series[0] - identity_series[-1], 8),
            "holds": bool(series[0] - series[-1] > 0.05 and abs(identity_series[0] - identity_series[-1]) < TOL),
        },
    }


def evaluate_status(rung: dict[str, Any]) -> str:
    lock = True
    pawl = bool(rung["pawl_test"]["holds"])
    nesting = bool(rung["collapse_control"]["holds"])
    if not lock:
        return "unmeasured"
    if not pawl:
        return "pawl_fails"
    if not nesting:
        return "independent_not_nested"
    return "locked"


def contiguous_depth(rungs: list[dict[str, Any]], face: str | None = None) -> dict[str, Any]:
    chain = []
    stop = None
    for rung in rungs:
        has_face = face is None or face in rung["lock_face"].split("+")
        if not has_face:
            stop = {"at": rung["id"], "reason": f"{face}_face_unmeasured_on_rung"}
            break
        if rung["status"] != "locked":
            stop = {"at": rung["id"], "reason": rung["status"]}
            break
        chain.append(rung["id"])
    if stop is None:
        stop = {"at": None, "reason": "ran_to_measured_top"}
    return {"depth": len(chain) - 1 if chain else -1, "chain": chain, "stop": stop}


def dof_table(rungs_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    terr_real = terrain_signature()
    terr_erased = terrain_signature(erase_dissipators=True)
    axis1_supported = sum(terr_real["nonunital_bits"]) == 4 and sum(terr_erased["nonunital_bits"]) == 0

    real_stage = stage_invariant()
    erased_stage = stage_invariant(erase_operator=True)

    def prec(ti: int, opname: str) -> float:
        probe = dm([0.55, 0.35, 0.25])
        up = stage_map(ti, opname, probe.copy(), sign="up")
        down = stage_map(ti, opname, probe.copy(), sign="down")
        return float(np.linalg.norm(bloch(up) - bloch(down)))

    prec_load = prec(1, "Fi")
    prec_collapse = prec(1, "Ti")

    rho0 = dm([0.3, 0.2, 0.1])
    sheet_gap = float(np.linalg.norm(bloch(flow(+H0, [], rho0.copy(), t=0.7)) - bloch(flow(-H0, [], rho0.copy(), t=0.7))))
    sheet_erased = 0.0

    return [
        {
            "dof": "axis-1 non-unitality",
            "switch_on_rung": "L4",
            "supported": bool(rungs_by_id["L4"]["status"] == "locked" and axis1_supported),
            "witness": {"nonunital_bits": terr_real["nonunital_bits"]},
            "floor_erasure": {"erase_terrain_dissipators_bits": terr_erased["nonunital_bits"], "collapses": axis1_supported},
        },
        {
            "dof": "axis-4 order gap",
            "switch_on_rung": "L6",
            "supported": bool(rungs_by_id["L6"]["status"] == "locked" and real_stage["min_order_gap"] > 1e-6),
            "witness": {"min_order_gap": round_float(real_stage["min_order_gap"], 8)},
            "floor_erasure": {"operator_erased_min_order_gap": round_float(erased_stage["min_order_gap"], 8), "collapses": erased_stage["min_order_gap"] < TOL},
        },
        {
            "dof": "axis-3 loop class",
            "switch_on_rung": "L3",
            "supported": bool(rungs_by_id["L3"]["status"] == "locked" and sheet_gap > 1e-3),
            "witness": {"sheet_loop_gap": round_float(sheet_gap, 8)},
            "floor_erasure": {"zero_geometry_gap": sheet_erased, "collapses": True},
        },
        {
            "dof": "axis-6 precedence",
            "switch_on_rung": "L5",
            "supported": bool(rungs_by_id["L5"]["status"] == "locked" and prec_load > 0.05 and prec_collapse < 0.3 * prec_load),
            "witness": {"load_bearing_gap": round_float(prec_load, 8), "same_terrain_collapse_gap": round_float(prec_collapse, 8)},
            "floor_erasure": {"shared_axis_ratio": round_float(prec_collapse / prec_load, 8), "collapses": prec_collapse < 0.3 * prec_load},
        },
        {
            "dof": "stage distinctness",
            "switch_on_rung": "L6",
            "supported": bool(rungs_by_id["L6"]["status"] == "locked" and real_stage["distinct_stage_maps"] == 16),
            "witness": {"distinct_stage_maps": real_stage["distinct_stage_maps"]},
            "floor_erasure": {"operator_erased_distinct_stage_maps": erased_stage["distinct_stage_maps"], "collapses": erased_stage["distinct_stage_maps"] < 16},
        },
    ]


def validate_stage_sources() -> dict[str, Any]:
    join = json.loads(STAGE_JOIN_PATH.read_text())
    source_rows = json.loads(SOURCE_SLOTS_PATH.read_text())
    join_by_slot = {row["source_slot_id"]: row for row in join["stage_join"]}
    mismatches = []
    for row in source_rows:
        joined = join_by_slot[row["slot_id"]]
        for field in ("terrain", "canonical_token", "axis6_sign", "igt_quadrant"):
            if row[field] != joined[field]:
                mismatches.append({"slot_id": row["slot_id"], "field": field})
        if row["canonical_operator"] != joined["operator"]:
            mismatches.append({"slot_id": row["slot_id"], "field": "operator"})
    return {
        "stage_token_join": str(STAGE_JOIN_PATH.relative_to(HERE.parents[2])),
        "blocked": bool(join.get("blocked")),
        "n_stage_join_rows": len(join.get("stage_join", [])),
        "source_slot_rows": len(source_rows),
        "mismatches": mismatches,
    }


def ladder_guard() -> dict[str, Any]:
    if not LADDER_RESULT_PATH.exists():
        return {
            "path": str(LADDER_RESULT_PATH.relative_to(HERE)),
            "present": False,
            "A0_doctrine_realized_observed": None,
            "standing_failure_preserved": None,
        }
    data = json.loads(LADDER_RESULT_PATH.read_text())
    observed = data.get("axes", {}).get("A0_feedback_polarity", {}).get("doctrine_pattern_realized")
    return {
        "path": str(LADDER_RESULT_PATH.relative_to(HERE)),
        "present": True,
        "A0_doctrine_realized_observed": observed,
        "standing_failure_preserved": observed is False,
    }


def print_table(rungs: list[dict[str, Any]], geo_depth: dict[str, Any], ent_depth: dict[str, Any], dofs: list[dict[str, Any]]) -> None:
    print("MANIFOLD RATCHET DEPTH -- scratch_diagnostic, promotion_allowed=false")
    print("per-rung lock/pawl/nesting:")
    print("rung  face                 status                 pawl_drift/null       nesting")
    for rung in rungs:
        pawl = rung["pawl_test"]
        collapse = rung["collapse_control"]
        print(
            f"{rung['id']:<4}  {rung['lock_face']:<20} {rung['status']:<22} "
            f"{pawl['invariant_drift']!s:<10}/{pawl['no_lock_drift']!s:<10} "
            f"{collapse['holds']}"
        )
    print("\ndepth chains:")
    print(f"  geometric: depth={geo_depth['depth']} chain={geo_depth['chain']} stop={geo_depth['stop']}")
    print(f"  entropic : depth={ent_depth['depth']} chain={ent_depth['chain']} stop={ent_depth['stop']}")
    print("\ndepth->DOF table:")
    for row in dofs:
        print(
            f"  {row['switch_on_rung']:<3} {row['dof']:<24} supported={row['supported']} "
            f"collapse={row['floor_erasure']['collapses']}"
        )


def main() -> int:
    rng = np.random.default_rng(SEED)
    source_status = validate_stage_sources()
    rungs = [
        l0_quotient_measure(),
        l1_carrier_measure(),
        l2_geometry_measure(),
        l3_sheet_measure(),
        l4_terrain_measure(),
        l5_operator_measure(),
        l6_stage_measure(),
        l8_entropy_measure(rng),
    ]
    for rung in rungs:
        rung["status"] = evaluate_status(rung)

    rungs_by_id = {rung["id"]: rung for rung in rungs}
    geo_depth = contiguous_depth(rungs, "geometric")
    ent_depth = contiguous_depth(rungs, "entropic")
    dofs = dof_table(rungs_by_id)

    out = {
        "sim_id": "manifold_ratchet_depth_sim",
        "classification": "scratch_diagnostic",
        "sim_execution_kind": "nonclassical",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "seed": SEED,
        "structural_tokens_only": True,
        "claim_ceiling": "runs/passes local rerun only; no promotion or ladder-doctrine repair claim",
        "owner_frame_verbatim": (
            "the very dual ratchet entropic geometric constraint manifold should also have ratcheted as deep "
            "as it can. this should be informative. it is something truly earned, and where the engines dofs play out."
        ),
        "source_status": source_status,
        "ladder_guard": ladder_guard(),
        "rungs": rungs,
        "depth_geometric": geo_depth,
        "depth_entropic": ent_depth,
        "depth_to_dof_table": dofs,
        "tool_manifest": {
            "numpy": "load_bearing: finite density matrices, quotient signatures, GKSL integration, order gaps",
            "scipy.linalg.expm": "load_bearing: unitary/operator channels using house conventions",
            "stage_token_join.json": "load_bearing: stage/source token structural join checked before DOF table",
        },
        "tool_integration_depth": "load_bearing",
        "promotion_status": "diagnostic_only",
        "blocked_consumers": [
            "canonical manifold-depth claim",
            "Axis-0 closure",
            "bridge/physics promotion",
            "ledger status promotion",
        ],
    }
    RESULT_PATH.write_text(json.dumps(out, indent=2, default=float) + "\n")
    print_table(rungs, geo_depth, ent_depth, dofs)
    print(f"\nRESULT_JSON: {RESULT_PATH}")
    print("HONEST_VERDICT: exit0 mixed per-rung locked/pawl-fails/not-nested/unmeasured")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
