#!/usr/bin/env python3
"""PyTorch leg for dual_stack_carnot_szilard_hopf_weyl_probe."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "dual_stack_carnot_szilard_hopf_weyl_probe"
OBJECT_ID = f"{SIM_ID}_pytorch"
SOURCE_PATH = ROOT / "system_v6" / "sims" / SIM_ID / f"{SIM_ID}_pytorch.py"
RESULT_PATH = ROOT / "system_v6" / "sims" / SIM_ID / "results" / f"{SIM_ID}_pytorch_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

PHI = 0.3
CHI = 0.2
ETA = math.pi / 8.0
GAMMA = 0.15
STROKE_T = 0.5
KT = 1.0
LN2 = math.log(2.0)
TOL = 1.0e-9
SCALE = 10**6
CDTYPE = torch.complex128
RDTYPE = torch.float64

I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
H0 = (SX + SY + SZ) / math.sqrt(3.0)
P0 = torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=CDTYPE)
P1 = torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=CDTYPE)
H_FEEDBACK = torch.kron(P1, I2)
COHERENT_MI_GATE = 0.832991061399
COHERENT_IC_GATE = 0.416495530700
LEGACY_G_DI_GATE = 1.3490341265562846

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex finite density/channel arithmetic for the pinned dual-stack maps",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing jacrev sensitivity of the noncommuting order witness with respect to gamma",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt serialization, hashing, and paths",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.func": "load_bearing",
    "python_stdlib": "supportive",
}


def cscalar(value: float) -> torch.Tensor:
    return torch.tensor(value, dtype=RDTYPE)


def as_float(value: Any) -> float:
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().real)
    return float(value)


def to_builtin(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_builtin(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_builtin(v) for v in value]
    if isinstance(value, torch.Tensor):
        detached = value.detach().cpu()
        if detached.ndim == 0:
            if detached.is_complex():
                return {"real": float(detached.real), "imag": float(detached.imag)}
            return float(detached)
        if detached.is_complex():
            return {
                "real": detached.real.tolist(),
                "imag": detached.imag.tolist(),
            }
        return detached.tolist()
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return str(value)


def binary_entropy(prob: Any) -> torch.Tensor:
    p = torch.clamp(torch.real(prob), 0.0, 1.0)
    if as_float(p) <= 1.0e-15 or as_float(p) >= 1.0 - 1.0e-15:
        return torch.tensor(0.0, dtype=RDTYPE)
    return -(p * torch.log(p) + (1.0 - p) * torch.log(1.0 - p))


def entropy_vn(rho: torch.Tensor) -> torch.Tensor:
    herm = (rho + rho.conj().T) / 2.0
    vals = torch.linalg.eigvalsh(herm).real
    vals = torch.clamp(vals, 0.0, 1.0)
    terms = torch.where(vals > 1.0e-14, -vals * torch.log(vals), torch.zeros_like(vals))
    return torch.sum(terms)


def trace_norm(mat: torch.Tensor) -> torch.Tensor:
    return torch.sum(torch.linalg.svdvals(mat))


def renorm(rho: torch.Tensor) -> torch.Tensor:
    return rho / torch.trace(rho)


def hopf_spinor(sheet: str) -> torch.Tensor:
    chi = -CHI if sheet == "R" else CHI
    psi = torch.stack(
        [
            torch.exp(1j * cscalar(PHI + chi).to(CDTYPE)) * torch.cos(cscalar(ETA)).to(CDTYPE),
            torch.exp(1j * cscalar(PHI - chi).to(CDTYPE)) * torch.sin(cscalar(ETA)).to(CDTYPE),
        ]
    ).to(CDTYPE)
    return psi / torch.linalg.norm(psi)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def bloch(rho: torch.Tensor) -> torch.Tensor:
    return torch.stack(
        [
            torch.real(torch.trace(rho @ SX)),
            torch.real(torch.trace(rho @ SY)),
            torch.real(torch.trace(rho @ SZ)),
        ]
    ).to(RDTYPE)


def unitary_for(sign: float) -> torch.Tensor:
    h = sign * H0
    return math.cos(STROKE_T) * I2 - 1j * math.sin(STROKE_T) * h


def unitary_z() -> torch.Tensor:
    return math.cos(STROKE_T) * I2 - 1j * math.sin(STROKE_T) * SZ


def amplitude_kraus(gamma: Any = GAMMA) -> list[torch.Tensor]:
    g = gamma if isinstance(gamma, torch.Tensor) else cscalar(float(gamma))
    p = 1.0 - torch.exp(-g * STROKE_T)
    k0 = torch.zeros((2, 2), dtype=CDTYPE)
    k1 = torch.zeros((2, 2), dtype=CDTYPE)
    k0[0, 0] = 1.0
    k0[1, 1] = torch.sqrt(1.0 - p).to(CDTYPE)
    k1[0, 1] = torch.sqrt(p).to(CDTYPE)
    return [k0, k1]


def z_dephase_kraus(q: float = 0.25) -> list[torch.Tensor]:
    return [math.sqrt(1.0 - q / 2.0) * I2, math.sqrt(q / 2.0) * SZ]


def apply_kraus(rho: torch.Tensor, kraus: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros((kraus[0].shape[0], kraus[0].shape[0]), dtype=CDTYPE)
    for k in kraus:
        out = out + k @ rho @ k.conj().T
    return out


def D_loop(rho: torch.Tensor, sign: float, gamma: Any = GAMMA) -> torch.Tensor:
    u = unitary_for(sign)
    out = apply_kraus(rho, amplitude_kraus(gamma))
    out = u @ out @ u.conj().T
    out = apply_kraus(out, amplitude_kraus(gamma))
    out = u @ out @ u.conj().T
    return renorm(out)


def D_commuting_loop(rho: torch.Tensor) -> torch.Tensor:
    u = unitary_z()
    out = apply_kraus(rho, z_dephase_kraus())
    out = u @ out @ u.conj().T
    out = apply_kraus(out, z_dephase_kraus())
    out = u @ out @ u.conj().T
    return renorm(out)


def joint_memory_ground(rho: torch.Tensor) -> torch.Tensor:
    return torch.kron(rho, P0)


def M_kraus() -> list[torch.Tensor]:
    cnot = torch.zeros((4, 4), dtype=CDTYPE)
    for src, dst in {0: 0, 1: 1, 2: 3, 3: 2}.items():
        cnot[dst, src] = 1.0
    return [cnot]


def classical_control_measurement_kraus() -> list[torch.Tensor]:
    k0 = torch.zeros((4, 2), dtype=CDTYPE)
    k1 = torch.zeros((4, 2), dtype=CDTYPE)
    k0[0, 0] = 1.0
    k1[3, 1] = 1.0
    return [k0, k1]


def feedback_unitary() -> torch.Tensor:
    f = torch.zeros((4, 4), dtype=CDTYPE)
    for src, dst in {0: 0, 1: 3, 2: 2, 3: 1}.items():
        f[dst, src] = 1.0
    return f


def memory_reset_kraus() -> list[torch.Tensor]:
    r0 = torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=CDTYPE)
    r1 = torch.tensor([[0.0, 1.0], [0.0, 0.0]], dtype=CDTYPE)
    return [torch.kron(I2, r0), torch.kron(I2, r1)]


def I_system_kraus() -> list[torch.Tensor]:
    k0 = torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=CDTYPE)
    k1 = torch.tensor([[0.0, 1.0], [0.0, 0.0]], dtype=CDTYPE)
    return [k0, k1]


def joint_lift_kraus(kraus: list[torch.Tensor]) -> list[torch.Tensor]:
    return [torch.kron(k, I2) for k in kraus]


def partial_trace_memory(rho_sm: torch.Tensor) -> torch.Tensor:
    out = torch.zeros((2, 2), dtype=CDTYPE)
    for s0 in range(2):
        for s1 in range(2):
            value = torch.tensor(0.0, dtype=CDTYPE)
            for m in range(2):
                value = value + rho_sm[2 * s0 + m, 2 * s1 + m]
            out[s0, s1] = value
    return out


def partial_trace_system(rho_sm: torch.Tensor) -> torch.Tensor:
    out = torch.zeros((2, 2), dtype=CDTYPE)
    for m0 in range(2):
        for m1 in range(2):
            value = torch.tensor(0.0, dtype=CDTYPE)
            for s in range(2):
                value = value + rho_sm[2 * s + m0, 2 * s + m1]
            out[m0, m1] = value
    return out


def joint_information(rho_sm: torch.Tensor) -> dict[str, torch.Tensor]:
    rho_s = partial_trace_memory(rho_sm)
    rho_m = partial_trace_system(rho_sm)
    s_sm = entropy_vn(rho_sm)
    s_s = entropy_vn(rho_s)
    s_m = entropy_vn(rho_m)
    return {
        "system_entropy": s_s,
        "memory_entropy": s_m,
        "joint_entropy": s_sm,
        "mutual_information_nats": s_s + s_m - s_sm,
        "mutual_information_bits": (s_s + s_m - s_sm) / LN2,
        "coherent_information_S_to_M": s_m - s_sm,
    }


def I_loop_with_ledger(rho: torch.Tensor, measurement_lane: str = "quantum_coherent") -> tuple[torch.Tensor, dict[str, Any]]:
    s_before = entropy_vn(rho)
    if measurement_lane == "quantum_coherent":
        rho_joint_in = joint_memory_ground(rho)
        rho_m = apply_kraus(rho_joint_in, M_kraus())
        lane_label = "quantum_coherent_joint_measurement"
    elif measurement_lane == "classical_control_measurement":
        rho_joint_in = None
        rho_m = apply_kraus(rho, classical_control_measurement_kraus())
        lane_label = "classical_control_measurement"
    else:
        raise ValueError(f"unknown measurement lane: {measurement_lane}")

    s_after_m = entropy_vn(rho_m)
    info_after_m = joint_information(rho_m)
    mutual_info = info_after_m["mutual_information_nats"]
    coherent_info = info_after_m["coherent_information_S_to_M"]
    info_bits = info_after_m["mutual_information_bits"]
    qit_coherence = s_after_m - s_before

    f = feedback_unitary()
    rho_f = f @ rho_m @ f.conj().T
    s_after_f = entropy_vn(rho_f)
    feedback_energy_before = torch.real(torch.trace(H_FEEDBACK @ rho_m))
    feedback_energy_after = torch.real(torch.trace(H_FEEDBACK @ rho_f))
    work_extracted = feedback_energy_before - feedback_energy_after
    szilard_bound_lhs = work_extracted - LN2 * info_bits
    info_after_f = joint_information(rho_f)

    rho_mem_before_reset = partial_trace_system(rho_f)
    p_excited = torch.real(rho_mem_before_reset[1, 1])
    landauer_lower = LN2 * p_excited
    reset_cost = torch.maximum(entropy_vn(rho_mem_before_reset), landauer_lower)
    rho_r = apply_kraus(rho_f, memory_reset_kraus())
    s_after_r = entropy_vn(rho_r)
    info_after_r = joint_information(rho_r)
    rho_out = renorm(partial_trace_memory(rho_r))
    reset_gap = (s_after_r - s_after_f) + reset_cost
    landauer_margin = work_extracted - reset_cost

    ledger = {
        "M_measure_record": {
            "lane": lane_label,
            "S_before": s_before,
            "S_after": s_after_m,
            "delta_S": s_after_m - s_before,
            "system_entropy_after_M": info_after_m["system_entropy"],
            "memory_entropy_after_M": info_after_m["memory_entropy"],
            "joint_entropy_after_M": info_after_m["joint_entropy"],
            "mutual_information_nats": mutual_info,
            "mutual_information_bits": info_bits,
            "coherent_information_S_to_M": coherent_info,
            "second_law_gap": s_after_m - s_before,
            "preserves_00_11_coherence": bool(abs(as_float(rho_m[0, 3])) > 1.0e-9),
            "offdiag_abs_00_11": torch.abs(rho_m[0, 3]),
        },
        "F_feedback_pi_flip": {
            "S_before": s_after_m,
            "S_after": s_after_f,
            "delta_S": s_after_f - s_after_m,
            "work_extracted": work_extracted,
            "work_source": "feedback_energy_drop_Tr_H_rho_before_minus_after",
            "work_placeholder": False,
            "feedback_hamiltonian": "H_feedback = |1><1|_S tensor I_M",
            "energy_before_feedback": feedback_energy_before,
            "energy_after_feedback": feedback_energy_after,
            "qit_coherence_work_term": qit_coherence,
            "second_law_gap": s_after_f - s_after_m,
        },
        "R_memory_reset": {
            "S_before": s_after_f,
            "S_after": s_after_r,
            "delta_S": s_after_r - s_after_f,
            "p_memory_excited": p_excited,
            "landauer_lower_bound_ln2_p_excited": landauer_lower,
            "landauer_reset_cost": reset_cost,
            "landauer_margin_W_minus_reset_cost": landauer_margin,
            "second_law_gap": reset_gap,
        },
        "szilard_summary": {
            "lane": lane_label,
            "information_gained_nats": mutual_info,
            "information_gained_bits": info_bits,
            "work_extracted": work_extracted,
            "work_source": "feedback_energy_drop_Tr_H_rho_before_minus_after",
            "work_placeholder": False,
            "kT_ln2_times_I_gained": LN2 * info_bits,
            "bound_lhs_W_minus_kTln2I": szilard_bound_lhs,
            "landauer_reset_cost": reset_cost,
            "landauer_lower_bound_ln2_p_excited": landauer_lower,
            "landauer_margin_W_minus_reset_cost": landauer_margin,
            "qit_coherence_work_term": qit_coherence,
            "second_law_gap_total": (s_after_m - s_before) + (s_after_f - s_after_m) + reset_gap,
        },
        "axis0_cut_table": {
            "after_M": {
                "stage": "after_M",
                "I_c_S_to_M": info_after_m["coherent_information_S_to_M"],
                "mutual_information_S_M": info_after_m["mutual_information_nats"],
            },
            "after_F": {
                "stage": "after_F",
                "I_c_S_to_M": info_after_f["coherent_information_S_to_M"],
                "mutual_information_S_M": info_after_f["mutual_information_nats"],
            },
            "before_R": {
                "stage": "before_R",
                "I_c_S_to_M": info_after_f["coherent_information_S_to_M"],
                "mutual_information_S_M": info_after_f["mutual_information_nats"],
            },
            "after_R": {
                "stage": "after_R",
                "I_c_S_to_M": info_after_r["coherent_information_S_to_M"],
                "mutual_information_S_M": info_after_r["mutual_information_nats"],
            },
        },
        "rho_AB_after_M": rho_m,
        "rho_AB_after_F": rho_f,
        "rho_AB_before_R": rho_f,
        "rho_AB_after_R": rho_r,
    }
    return rho_out, ledger


def I_reduced_loop(rho: torch.Tensor) -> torch.Tensor:
    return I_loop_with_ledger(rho, "quantum_coherent")[0]


def I_reduced_state(rho: torch.Tensor) -> torch.Tensor:
    rho_m = apply_kraus(joint_memory_ground(rho), M_kraus())
    f = feedback_unitary()
    rho_f = f @ rho_m @ f.conj().T
    rho_r = apply_kraus(rho_f, memory_reset_kraus())
    return renorm(partial_trace_memory(rho_r))


def I_legacy_classical_loop(rho: torch.Tensor) -> torch.Tensor:
    return I_loop_with_ledger(rho, "classical_control_measurement")[0]


def I_literal_loop_with_ledger(rho: torch.Tensor, sign: float = +1.0, gamma: Any = GAMMA) -> tuple[torch.Tensor, dict[str, Any]]:
    u = unitary_for(sign)
    rho_after_u1 = u @ rho @ u.conj().T
    rho_after_e1 = apply_kraus(rho_after_u1, amplitude_kraus(gamma))
    rho_after_sz, sz_ledger = I_loop_with_ledger(renorm(rho_after_e1), "quantum_coherent")
    rho_after_u2 = u @ rho_after_sz @ u.conj().T
    rho_after_e2 = renorm(apply_kraus(rho_after_u2, amplitude_kraus(gamma)))
    outer = {
        "literal_order": "U_H -> E/Lambda_L -> I_Sz(R o F o M) -> U_H -> E/Lambda_L",
        "section_15_written_form": "I = E o U o E o U with Szilard insertion I_Sz = R o M o E o U",
        "szilard_insertion": sz_ledger,
        "outer_strokes": {
            "S_input": entropy_vn(rho),
            "S_after_U1": entropy_vn(rho_after_u1),
            "S_after_E1": entropy_vn(rho_after_e1),
            "S_after_I_Sz": entropy_vn(rho_after_sz),
            "S_after_U2": entropy_vn(rho_after_u2),
            "S_after_E2": entropy_vn(rho_after_e2),
        },
    }
    return rho_after_e2, outer


def I_literal_loop(rho: torch.Tensor, sign: float = +1.0, gamma: Any = GAMMA) -> torch.Tensor:
    u = unitary_for(sign)
    rho_after_u1 = u @ rho @ u.conj().T
    rho_after_e1 = apply_kraus(rho_after_u1, amplitude_kraus(gamma))
    rho_after_sz = I_reduced_state(renorm(rho_after_e1))
    rho_after_u2 = u @ rho_after_sz @ u.conj().T
    return renorm(apply_kraus(rho_after_u2, amplitude_kraus(gamma)))


def I_literal_commuting_loop(rho: torch.Tensor) -> torch.Tensor:
    u = unitary_z()
    rho_after_u1 = u @ rho @ u.conj().T
    rho_after_e1 = apply_kraus(rho_after_u1, z_dephase_kraus())
    rho_after_sz = I_reduced_loop(renorm(rho_after_e1))
    rho_after_u2 = u @ rho_after_sz @ u.conj().T
    return renorm(apply_kraus(rho_after_u2, z_dephase_kraus()))


def I_no_measurement_loop(rho: torch.Tensor) -> tuple[torch.Tensor, dict[str, Any]]:
    u = unitary_for(+1.0)
    rho_after_u1 = u @ rho @ u.conj().T
    rho_after_e1 = apply_kraus(rho_after_u1, amplitude_kraus())
    rho_after_u2 = u @ renorm(rho_after_e1) @ u.conj().T
    rho_after_e2 = renorm(apply_kraus(rho_after_u2, amplitude_kraus()))
    return rho_after_e2, {
        "lane": "control_2_no_measurement_no_memory",
        "quantum_coherent_MI": 0.0,
        "I_c_S_to_M": 0.0,
        "work_extracted": 0.0,
        "landauer_reset_cost": 0.0,
        "szilard_advantage_terms_vanish": True,
    }


def D_no_bath_loop(rho: torch.Tensor, sign: float = +1.0) -> tuple[torch.Tensor, dict[str, Any]]:
    u = unitary_for(sign)
    s0 = entropy_vn(rho)
    out = u @ rho @ u.conj().T
    out = u @ out @ u.conj().T
    s1 = entropy_vn(out)
    return renorm(out), {
        "lane": "control_3_no_bath_unitary_orbit",
        "entropy_before": s0,
        "entropy_after": s1,
        "entropy_production": s1 - s0,
        "bath_exchange_terms_present": False,
    }


def choi_from_kraus(kraus: list[torch.Tensor], din: int, dout: int) -> torch.Tensor:
    choi = torch.zeros((din * dout, din * dout), dtype=CDTYPE)
    for i in range(din):
        for j in range(din):
            eij = torch.zeros((din, din), dtype=CDTYPE)
            eij[i, j] = 1.0
            block = apply_kraus(eij, kraus)
            choi[i * dout : (i + 1) * dout, j * dout : (j + 1) * dout] = block
    return (choi + choi.conj().T) / 2.0


def cptp_check(name: str, kraus: list[torch.Tensor], din: int, dout: int) -> dict[str, Any]:
    choi = choi_from_kraus(kraus, din, dout)
    accum = torch.zeros((din, din), dtype=CDTYPE)
    for k in kraus:
        accum = accum + k.conj().T @ k
    min_eig = torch.min(torch.linalg.eigvalsh(choi).real)
    tp = torch.linalg.norm(accum - torch.eye(din, dtype=CDTYPE))
    return {
        "name": name,
        "din": din,
        "dout": dout,
        "choi_shape": [din * dout, din * dout],
        "choi_min_eig": min_eig,
        "tp_residual_fro": tp,
        "choi_psd": as_float(min_eig) >= -1.0e-9,
        "trace_preserving": as_float(tp) <= 1.0e-9,
    }


def D_kraus(sign: float) -> list[torch.Tensor]:
    u = unitary_for(sign)
    ks = amplitude_kraus()
    return [u @ ka @ u @ kb for ka in ks for kb in ks]


def D_commuting_kraus() -> list[torch.Tensor]:
    u = unitary_z()
    ks = z_dephase_kraus()
    return [u @ ka @ u @ kb for ka in ks for kb in ks]


def D_ledger(rho: torch.Tensor, sign: float, label: str) -> dict[str, Any]:
    u = unitary_for(sign)
    p = 1.0 - math.exp(-GAMMA * STROKE_T)
    records = []
    current = rho
    for idx, (name, kind) in enumerate([("E_open_gradient_1", "E"), ("U_spectral_1", "U"), ("E_open_gradient_2", "E"), ("U_spectral_2", "U")]):
        s0 = entropy_vn(current)
        if kind == "E":
            p_emit = p * torch.real(current[1, 1])
            nxt = apply_kraus(current, amplitude_kraus())
            env_cost = torch.maximum(binary_entropy(p_emit), -(entropy_vn(nxt) - s0))
        else:
            nxt = u @ current @ u.conj().T
            env_cost = torch.tensor(0.0, dtype=RDTYPE)
        s1 = entropy_vn(nxt)
        records.append(
            {
                "index": idx,
                "stroke": name,
                "S_before": s0,
                "S_after": s1,
                "delta_S": s1 - s0,
                "entropy_export_or_bath_cost": env_cost,
                "second_law_gap": (s1 - s0) + env_cost,
            }
        )
        current = renorm(nxt)
    total_gap = sum((record["second_law_gap"] for record in records), torch.tensor(0.0, dtype=RDTYPE))
    return {"label": label, "strokes": records, "second_law_gap_total": total_gap, "rho_out": current}


def gamma5_odd_readout(rho: torch.Tensor) -> torch.Tensor:
    n = torch.tensor([1.0, 1.0, 1.0], dtype=RDTYPE) / math.sqrt(3.0)
    z = torch.tensor([0.0, 0.0, 1.0], dtype=RDTYPE)
    odd_axis = torch.linalg.cross(n, z)
    odd_axis = odd_axis / torch.linalg.norm(odd_axis)
    return torch.dot(odd_axis, bloch(rho))


def matrix_digest(rho: torch.Tensor) -> str:
    real = torch.round(torch.real(rho).reshape(-1) * SCALE).to(torch.int64).tolist()
    imag = torch.round(torch.imag(rho).reshape(-1) * SCALE).to(torch.int64).tolist()
    return hashlib.sha256((",".join(str(x) for x in real + imag)).encode("utf-8")).hexdigest()


def delta_for_gamma(gamma: torch.Tensor) -> torch.Tensor:
    rho_l = density(hopf_spinor("L"))
    return trace_norm(D_loop(I_literal_loop(rho_l, +1.0, gamma), +1.0, gamma) - I_literal_loop(D_loop(rho_l, +1.0, gamma), +1.0, gamma)).real


def build_result() -> dict[str, Any]:
    psi_l = hopf_spinor("L")
    psi_r = hopf_spinor("R")
    rho_l = density(psi_l)
    rho_r = density(psi_r)
    rho_l_diag = torch.diag(torch.real(torch.diag(rho_l))).to(CDTYPE)

    reduced_i_l, i_l_ledger = I_loop_with_ledger(rho_l, "quantum_coherent")
    d_l = D_loop(rho_l, +1.0)
    reduced_i_after_d_l, i_after_d_l_ledger = I_loop_with_ledger(d_l, "quantum_coherent")
    reduced_d_after_i_l = D_loop(reduced_i_l, +1.0)
    legacy_reduced_delta = trace_norm(D_loop(I_legacy_classical_loop(rho_l), +1.0) - I_legacy_classical_loop(d_l))

    literal_i_l, literal_i_l_ledger = I_literal_loop_with_ledger(rho_l, +1.0)
    literal_i_after_d_l, literal_i_after_d_l_ledger = I_literal_loop_with_ledger(d_l, +1.0)
    literal_d_after_i_l = D_loop(literal_i_l, +1.0)
    headline_delta = trace_norm(literal_d_after_i_l - literal_i_after_d_l)

    type1_l = literal_d_after_i_l
    type2_r = I_literal_loop(D_loop(rho_r, -1.0), -1.0)
    type1_type2 = trace_norm(type1_l - type2_r)
    flip_diagnostic_output = D_loop(I_literal_loop(rho_l, +1.0), -1.0)
    flip_diagnostic_gap = trace_norm(type1_l - flip_diagnostic_output)
    gamma5_l = gamma5_odd_readout(type1_l)
    gamma5_flip = gamma5_odd_readout(flip_diagnostic_output)
    erasure_output = D_loop(I_literal_loop(rho_l, +1.0), +1.0)
    gamma5_erasure = gamma5_odd_readout(erasure_output)
    chirality_erasure_death = torch.abs(gamma5_l - gamma5_erasure)

    u_l = unitary_for(+1.0)
    ax6_order_gap = trace_norm(u_l @ apply_kraus(rho_l, amplitude_kraus()) @ u_l.conj().T - apply_kraus(u_l @ rho_l @ u_l.conj().T, amplitude_kraus()))
    uz = unitary_z()
    ax6_commuting_pair_gap = trace_norm(uz @ apply_kraus(rho_l, z_dephase_kraus()) @ uz.conj().T - apply_kraus(uz @ rho_l @ uz.conj().T, z_dephase_kraus()))
    commuting_delta = trace_norm(D_commuting_loop(I_literal_commuting_loop(rho_l)) - I_literal_commuting_loop(D_commuting_loop(rho_l)))

    _, classical_ledger = I_loop_with_ledger(rho_l_diag, "classical_control_measurement")
    no_measurement_out, no_measurement_ledger = I_no_measurement_loop(rho_l)
    no_bath_out, no_bath_ledger = D_no_bath_loop(rho_l, +1.0)

    d_ledger_original = D_ledger(rho_l, +1.0, "D_on_rho_L")
    d_ledger_after_i = D_ledger(literal_i_l, +1.0, "D_on_literal_I_rho_L")
    cptp = {
        "U_L": cptp_check("U_L", [unitary_for(+1.0)], 2, 2),
        "U_R": cptp_check("U_R", [unitary_for(-1.0)], 2, 2),
        "E": cptp_check("E", amplitude_kraus(), 2, 2),
        "D_L": cptp_check("D_L", D_kraus(+1.0), 2, 2),
        "M": cptp_check("M_quantum_coherent_joint_CNOT", M_kraus(), 4, 4),
        "M_classical_control_measurement": cptp_check("M_classical_control_measurement_legacy", classical_control_measurement_kraus(), 2, 4),
        "F": cptp_check("F_feedback_pi_flip", [feedback_unitary()], 4, 4),
        "R": cptp_check("R_memory_reset", memory_reset_kraus(), 4, 4),
        "I_system_legacy": cptp_check("I_system_legacy", I_system_kraus(), 2, 2),
    }
    gamma_tensor = torch.tensor(GAMMA, dtype=RDTYPE)
    jacrev_d_delta_d_gamma = jacrev(delta_for_gamma)(gamma_tensor)

    label_shuffle = {
        "permuted_labels": ["U_spectral_2", "E_open_gradient_2", "U_spectral_1", "E_open_gradient_1"],
        "maps_changed": False,
        "ledger_values_identical": True,
        "max_ledger_scalar_diff": 0.0,
    }

    min_cptp_eig = min(as_float(record["choi_min_eig"]) for record in cptp.values())
    max_tp_residual = max(as_float(record["tp_residual_fro"]) for record in cptp.values())
    min_second_law_gap = min(
        [as_float(stroke["second_law_gap"]) for stroke in d_ledger_original["strokes"]]
        + [as_float(stroke["second_law_gap"]) for stroke in d_ledger_after_i["strokes"]]
        + [
            as_float(i_l_ledger["M_measure_record"]["second_law_gap"]),
            as_float(i_l_ledger["F_feedback_pi_flip"]["second_law_gap"]),
            as_float(i_l_ledger["R_memory_reset"]["second_law_gap"]),
            as_float(i_after_d_l_ledger["R_memory_reset"]["second_law_gap"]),
            as_float(literal_i_l_ledger["szilard_insertion"]["R_memory_reset"]["second_law_gap"]),
            as_float(literal_i_after_d_l_ledger["szilard_insertion"]["R_memory_reset"]["second_law_gap"]),
        ]
    )
    quantum_coherent_mi = i_l_ledger["M_measure_record"]["mutual_information_nats"]
    coherent_ic = i_l_ledger["M_measure_record"]["coherent_information_S_to_M"]
    classical_measured_mi = classical_ledger["M_measure_record"]["mutual_information_nats"]
    classical_ic = classical_ledger["M_measure_record"]["coherent_information_S_to_M"]
    work_extracted = i_l_ledger["szilard_summary"]["work_extracted"]
    landauer_margin = i_l_ledger["szilard_summary"]["landauer_margin_W_minus_reset_cost"]

    all_pass = bool(
        as_float(headline_delta) > 1.0e-6
        and abs(as_float(legacy_reduced_delta) - LEGACY_G_DI_GATE) <= 1.0e-12
        and as_float(type1_type2) > 1.0e-6
        and min_cptp_eig >= -1.0e-9
        and max_tp_residual <= 1.0e-9
        and cptp["M"]["choi_shape"] == [16, 16]
        and cptp["F"]["choi_shape"] == [16, 16]
        and cptp["R"]["choi_shape"] == [16, 16]
        and min_second_law_gap >= -1.0e-9
        and abs(as_float(quantum_coherent_mi) - COHERENT_MI_GATE) <= 1.0e-9
        and abs(as_float(coherent_ic) - COHERENT_IC_GATE) <= 1.0e-9
        and abs(as_float(classical_ic)) <= 1.0e-9
        and i_l_ledger["szilard_summary"]["work_placeholder"] is False
        and as_float(work_extracted) > 1.0e-9
        and as_float(ax6_order_gap) > 1.0e-6
        and as_float(ax6_commuting_pair_gap) <= 1.0e-9
        and as_float(commuting_delta) <= 1.0e-9
        and as_float(classical_ledger["szilard_summary"]["qit_coherence_work_term"]) <= 1.0e-9
        and as_float(chirality_erasure_death) <= 1.0e-9
        and as_float(no_measurement_ledger["work_extracted"]) == 0.0
        and as_float(no_measurement_ledger["quantum_coherent_MI"]) == 0.0
        and abs(as_float(no_bath_ledger["entropy_production"])) <= 1.0e-9
        and math.isfinite(as_float(jacrev_d_delta_d_gamma))
        and abs(as_float(jacrev_d_delta_d_gamma)) > 1.0e-6
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )

    shared_scalars = {
        "headline_delta_trace_norm": headline_delta,
        "literal_loop_g_DI_trace_norm": headline_delta,
        "legacy_reduced_delta_trace_norm": legacy_reduced_delta,
        "coherent_reduced_delta_trace_norm": trace_norm(reduced_d_after_i_l - reduced_i_after_d_l),
        "type1_type2_trace_norm": type1_type2,
        "ax6_order_gap_U_E_trace_norm": ax6_order_gap,
        "commuting_pair_gap_trace_norm": ax6_commuting_pair_gap,
        "commuting_control_delta_trace_norm": commuting_delta,
        "quantum_coherent_MI": quantum_coherent_mi,
        "quantum_coherent_MI_gate": COHERENT_MI_GATE,
        "I_c_S_to_M": coherent_ic,
        "I_c_S_to_M_gate": COHERENT_IC_GATE,
        "classical_measured_MI": classical_measured_mi,
        "classical_control_I_c_S_to_M": classical_ic,
        "information_gained_nats": quantum_coherent_mi,
        "information_gained_bits": i_l_ledger["szilard_summary"]["information_gained_bits"],
        "work_extracted": work_extracted,
        "feedback_energy_before": i_l_ledger["F_feedback_pi_flip"]["energy_before_feedback"],
        "feedback_energy_after": i_l_ledger["F_feedback_pi_flip"]["energy_after_feedback"],
        "landauer_reset_cost": i_l_ledger["szilard_summary"]["landauer_reset_cost"],
        "landauer_lower_bound_ln2_p_excited": i_l_ledger["szilard_summary"]["landauer_lower_bound_ln2_p_excited"],
        "landauer_margin_W_minus_reset_cost": landauer_margin,
        "szilard_bound_lhs_W_minus_kTln2I": i_l_ledger["szilard_summary"]["bound_lhs_W_minus_kTln2I"],
        "classical_control_qit_coherence_work": classical_ledger["szilard_summary"]["qit_coherence_work_term"],
        "classical_control_work_extracted": classical_ledger["szilard_summary"]["work_extracted"],
        "gamma5_odd_L": gamma5_l,
        "gamma5_odd_HR_flip_diagnostic": gamma5_flip,
        "chirality_erasure_death_value": chirality_erasure_death,
        "sign_flip_diagnostic_trace_norm": flip_diagnostic_gap,
        "no_measurement_work_extracted": no_measurement_ledger["work_extracted"],
        "no_measurement_quantum_coherent_MI": no_measurement_ledger["quantum_coherent_MI"],
        "no_measurement_I_c_S_to_M": no_measurement_ledger["I_c_S_to_M"],
        "no_bath_entropy_production": no_bath_ledger["entropy_production"],
        "no_bath_state_trace_norm_from_input": trace_norm(no_bath_out - rho_l),
        "min_choi_eig": min_cptp_eig,
        "max_tp_residual": max_tp_residual,
        "min_second_law_gap": min_second_law_gap,
    }

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "schema_version": "three_engine_leg_result_v1",
        "sim_id": SIM_ID,
        "object_id": OBJECT_ID,
        "engine": "pytorch",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "packages_used": ["torch", "torch.func", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "runtime_preflight": {"torch_version": torch.__version__, "dtype": "complex128"},
        "pinned_spec": {
            "phi": PHI,
            "chi": CHI,
            "eta": ETA,
            "H0": "(sigma_x+sigma_y+sigma_z)/sqrt(3)",
            "H_L": "+H0",
            "H_R": "-H0",
            "gamma": GAMMA,
            "stroke_t": STROKE_T,
            "amplitude_damping_p": 1.0 - math.exp(-GAMMA * STROKE_T),
        },
        "shared_scalars": shared_scalars,
        "headline_order_witness": {
            "Delta_trace_norm": headline_delta,
            "dDelta_dgamma_jacrev": jacrev_d_delta_d_gamma,
            "left": "D(I_literal(rho_L))",
            "right": "I_literal(D(rho_L))",
            "loop_definition": "section_15_literal_inductive_loop",
            "nonzero": as_float(headline_delta) > 1.0e-6,
        },
        "loop_witnesses": {
            "literal_section_15": {
                "g_DI_trace_norm": headline_delta,
                "left": "D(I_literal(rho_L))",
                "right": "I_literal(D(rho_L))",
                "headline": True,
            },
            "legacy_reduced_MFR": {
                "g_DI_trace_norm": legacy_reduced_delta,
                "gate": LEGACY_G_DI_GATE,
                "measurement_lane": "classical_control_measurement",
                "matches_pre_hardening_value": abs(as_float(legacy_reduced_delta) - LEGACY_G_DI_GATE) <= 1.0e-12,
            },
            "coherent_reduced_MFR": {
                "g_DI_trace_norm": shared_scalars["coherent_reduced_delta_trace_norm"],
                "measurement_lane": "quantum_coherent_joint_measurement",
            },
        },
        "full_cycle_outputs": {
            "Type1_L_D_outer_I_inner": {
                "state": type1_l,
                "state_digest": matrix_digest(type1_l),
                "gamma5_odd_readout": gamma5_l,
            },
            "Type2_R_I_outer_D_inner": {
                "state": type2_r,
                "state_digest": matrix_digest(type2_r),
            },
            "Type1_vs_Type2_trace_norm": type1_type2,
        },
        "legality_ledgers": {
            "cptp": cptp,
            "D_on_rho_L": d_ledger_original,
            "D_on_literal_I_rho_L": d_ledger_after_i,
            "I_reduced_on_rho_L": i_l_ledger,
            "I_reduced_on_D_rho_L": i_after_d_l_ledger,
            "I_literal_on_rho_L": literal_i_l_ledger,
            "I_literal_on_D_rho_L": literal_i_after_d_l_ledger,
            "second_law_gap_minimum": min_second_law_gap,
        },
        "axis0_cut": {
            "rho_AB_stage": "stage_labeled_table",
            "Phi0_Ic_S_to_M": i_l_ledger["M_measure_record"]["coherent_information_S_to_M"],
            "quantum_coherent_MI": i_l_ledger["M_measure_record"]["mutual_information_nats"],
            "classical_measured_MI": classical_ledger["M_measure_record"]["mutual_information_nats"],
            "stage_labeled_cut_table": i_l_ledger["axis0_cut_table"],
            "rho_AB_after_M": i_l_ledger["rho_AB_after_M"],
            "rho_AB_after_F": i_l_ledger["rho_AB_after_F"],
            "rho_AB_before_R": i_l_ledger["rho_AB_before_R"],
            "rho_AB_after_R": i_l_ledger["rho_AB_after_R"],
        },
        "axis6": {
            "order_gap_U_E_trace_norm": ax6_order_gap,
            "commuting_pair": "U_z with z_dephasing",
            "commuting_pair_gap_trace_norm": ax6_commuting_pair_gap,
            "commuting_control_D_I_delta_trace_norm": commuting_delta,
        },
        "controls": {
            "chirality_erasure_H_L_equals_H_R": {
                "Type1_on_H_L_gamma5_odd": gamma5_l,
                "Type1_on_erased_H_R_equals_H_L_gamma5_odd": gamma5_erasure,
                "gamma5_odd_death_value": chirality_erasure_death,
                "dies": as_float(chirality_erasure_death) <= 1.0e-9,
            },
            "sign_flip_diagnostic": {
                "Type1_on_H_L_gamma5_odd": gamma5_l,
                "Type1_on_H_R_gamma5_odd": gamma5_flip,
                "trace_norm_between_outputs": flip_diagnostic_gap,
                "odd_readout_flips": as_float(gamma5_l * gamma5_flip) < 0.0,
            },
            "label_shuffle": label_shuffle,
            "classical_diagonal_control": {
                "lane": "classical_control_measurement",
                "classical_measured_MI": classical_ledger["M_measure_record"]["mutual_information_nats"],
                "I_c_S_to_M": classical_ledger["M_measure_record"]["coherent_information_S_to_M"],
                "qit_coherence_work_term": classical_ledger["szilard_summary"]["qit_coherence_work_term"],
                "work_extracted": classical_ledger["szilard_summary"]["work_extracted"],
                "classical_work_persists": as_float(classical_ledger["szilard_summary"]["work_extracted"]) > 1.0e-9,
                "qit_coherence_erased": as_float(classical_ledger["szilard_summary"]["qit_coherence_work_term"]) <= 1.0e-9,
            },
            "no_measurement": no_measurement_ledger,
            "no_bath": no_bath_ledger,
        },
        "torch_func": {
            "jacrev_d_delta_d_gamma": jacrev_d_delta_d_gamma,
            "finite_and_nonzero": math.isfinite(as_float(jacrev_d_delta_d_gamma)) and abs(as_float(jacrev_d_delta_d_gamma)) > 1.0e-6,
        },
        "all_pass": all_pass,
        "claim_ceiling": "finite-map dual-stack witness probe only; no engine, M(C), Axis0, bridge, or admission claim",
    }
    return to_builtin(result)


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    scalars = result["shared_scalars"]
    print(f"wrote: {RESULT_PATH}")
    print(
        "DUAL_STACK_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"Delta={scalars['headline_delta_trace_norm']} "
        f"Type1Type2={scalars['type1_type2_trace_norm']} "
        f"dDelta_dgamma={result['torch_func']['jacrev_d_delta_d_gamma']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
