#!/usr/bin/env python3
# object_id: foundation_cross_model_readout_matrix_v0_pytorch
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: false

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


RUNG_ID = "cross_model_readout_matrix_v0"
OBJECT_ID = "foundation_cross_model_readout_matrix_v0_pytorch"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_cross_model_readout_matrix_v0_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v0_pytorch_results.json"
CARRIER_SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_three_engine_clifford_spinor_carrier_envelope.py"
CARRIER_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/three_engine_clifford_spinor_carrier_envelope_results.json"
TOL = 1.0e-9

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

BASIS_LABELS = ["uuu", "duu", "udu", "ddu", "uud", "dud", "udd", "ddd"]
LENS_ORDER = ["qit", "igt", "holodeck_runtime", "physics_math"]
LABEL_SHUFFLE_ORDER = ["igt", "physics_math", "qit", "holodeck_runtime"]
SIGNS = torch.tensor(
    [[1.0 if ((idx >> qubit) & 1) == 0 else -1.0 for idx in range(8)] for qubit in range(3)],
    dtype=torch.float64,
)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor substrate for local density/readout computation in float64/complex128",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing jacrev check for same-axis versus cross-axis IGT-readout sensitivity",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source fingerprint",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.func": "load_bearing",
    "json": "supportive",
    "hashlib": "supportive",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return value.detach().cpu().item()
        return value.detach().cpu().tolist()
    return value


def support_vectors() -> list[dict[str, Any]]:
    states: list[dict[str, Any]] = []
    basis = torch.zeros(8, dtype=torch.complex128)
    basis[0] = 1.0 + 0.0j
    states.append(
        {
            "state_id": "basis_uuu",
            "description": "Cl(6) spinor basis density at |uuu>",
            "amplitudes": basis,
        }
    )

    ghz = torch.zeros(8, dtype=torch.complex128)
    ghz[0] = 1 / math.sqrt(2)
    ghz[7] = 1 / math.sqrt(2)
    states.append(
        {
            "state_id": "ghz_phase",
            "description": "two-corner coherent spinor density over |uuu> and |ddd>",
            "amplitudes": ghz,
        }
    )

    w_state = torch.zeros(8, dtype=torch.complex128)
    w_state[1] = 1 / math.sqrt(3)
    w_state[2] = 1 / math.sqrt(3)
    w_state[4] = 1 / math.sqrt(3)
    states.append(
        {
            "state_id": "w_single_down",
            "description": "single-down W spinor density over |duu>, |udu>, |uud>",
            "amplitudes": w_state,
        }
    )

    biased = torch.zeros(8, dtype=torch.complex128)
    biased[0] = math.sqrt(1 / 2)
    biased[3] = math.sqrt(1 / 4)
    biased[5] = 1.0j * math.sqrt(1 / 8)
    biased[6] = math.sqrt(1 / 8)
    states.append(
        {
            "state_id": "biased_phase",
            "description": "asymmetric phase spinor density with rational diagonal support",
            "amplitudes": biased,
        }
    )
    return states


def density_from_vector(vec: torch.Tensor) -> torch.Tensor:
    return torch.outer(vec, torch.conj(vec))


def erased_density() -> torch.Tensor:
    return torch.eye(8, dtype=torch.complex128) / 8.0


def entropy_vn(rho: torch.Tensor) -> float:
    herm = (rho + torch.conj(rho.T)) / 2.0
    vals = torch.real(torch.linalg.eigvalsh(herm))
    vals = torch.clamp(vals, min=0.0, max=1.0)
    safe = torch.clamp(vals, min=1.0e-30, max=1.0)
    entropy = -torch.sum(torch.where(vals > 1.0e-12, vals * torch.log(safe), torch.zeros_like(vals)))
    return float(entropy.detach().cpu().item())


def partial_trace_q0(rho: torch.Tensor) -> torch.Tensor:
    red = torch.zeros((2, 2), dtype=torch.complex128)
    for q0_left in range(2):
        for q0_right in range(2):
            val = torch.zeros((), dtype=torch.complex128)
            for q1 in range(2):
                for q2 in range(2):
                    left = q0_left + 2 * q1 + 4 * q2
                    right = q0_right + 2 * q1 + 4 * q2
                    val = val + rho[left, right]
            red[q0_left, q0_right] = val
    return red


def diag_probs(rho: torch.Tensor) -> list[float]:
    return [float(torch.real(rho[idx, idx]).detach().cpu().item()) for idx in range(8)]


def z_expectations_tensor_from_diag(diag: torch.Tensor) -> torch.Tensor:
    return SIGNS.to(dtype=diag.dtype, device=diag.device) @ diag


def z_expectations_from_diag(diag: list[float]) -> list[float]:
    diag_tensor = torch.tensor(diag, dtype=torch.float64)
    return [float(x.detach().cpu().item()) for x in z_expectations_tensor_from_diag(diag_tensor)]


def pauli_coord(rho: torch.Tensor, qubit: int, pauli: str) -> float:
    total = torch.zeros((), dtype=torch.complex128)
    for rest in range(4):
        lower = rest & ((1 << qubit) - 1)
        upper = rest >> qubit
        idx0 = lower | (0 << qubit) | (upper << (qubit + 1))
        idx1 = lower | (1 << qubit) | (upper << (qubit + 1))
        if pauli == "X":
            total = total + rho[idx0, idx1] + rho[idx1, idx0]
        elif pauli == "Y":
            total = total + (-1.0j * rho[idx0, idx1]) + (1.0j * rho[idx1, idx0])
        else:
            raise ValueError(pauli)
    return float(torch.real(total).detach().cpu().item())


def qit_readout(rho: torch.Tensor) -> dict[str, float]:
    offdiag = rho - torch.diag(torch.diag(rho))
    return {
        "von_neumann_entropy": entropy_vn(rho),
        "coherence_l1": float(torch.sum(torch.abs(offdiag)).detach().cpu().item()),
        "purity": float(torch.real(torch.trace(rho @ rho)).detach().cpu().item()),
        "subsystem_entropy_q0": entropy_vn(partial_trace_q0(rho)),
    }


def igt_readout(rho: torch.Tensor) -> dict[str, Any]:
    z_vals = z_expectations_from_diag(diag_probs(rho))
    asym = [abs(z_vals[0] - z_vals[1]), abs(z_vals[0] - z_vals[2]), abs(z_vals[1] - z_vals[2])]
    return {
        "observable": "win_lose_payoff_asymmetry_only",
        "payoff_definition": "P[i,j]=max(0, z_i-z_j); report abs(P[i,j]-P[j,i]) == abs(z_i-z_j)",
        "z_expectations": z_vals,
        "asymmetry_pairs": {"q0_q1": asym[0], "q0_q2": asym[1], "q1_q2": asym[2]},
        "asymmetry_sum": float(sum(asym)),
    }


def holodeck_signature(diag: list[float]) -> dict[str, Any]:
    acc = 3
    seen: set[int] = set()
    path_sum = 0
    threshold_step = len(diag)
    found_threshold = False
    for idx, value in enumerate(diag):
        bucket = int(round(1000 * value))
        acc = (acc * 5 + bucket + idx) % 97
        seen.add(acc)
        path_sum += (idx + 1) * acc
        if not found_threshold and acc % 11 == 0:
            threshold_step = idx + 1
            found_threshold = True
    return {
        "ordered_basis": BASIS_LABELS,
        "final_accumulator_mod97": acc,
        "unique_runtime_states": len(seen),
        "threshold_step_mod11_zero": threshold_step,
        "weighted_path_sum": path_sum,
        "normalized_signature": [acc / 96, len(seen) / 8, threshold_step / 8, path_sum / (96 * sum(range(1, 9)))],
    }


def physics_readout(rho: torch.Tensor) -> dict[str, float | str]:
    x0 = pauli_coord(rho, 0, "X")
    y0 = pauli_coord(rho, 0, "Y")
    z0 = z_expectations_from_diag(diag_probs(rho))[0]
    grade1_norm = math.sqrt(x0 * x0 + y0 * y0 + z0 * z0)
    return {
        "coordinate_source": "first-qubit Pauli coordinates mirrored as Cl(3,0) grade-1 vector",
        "pauli_x_q0": x0,
        "pauli_y_q0": y0,
        "pauli_z_q0": z0,
        "clifford_grade1_norm": grade1_norm,
        "density_frobenius_norm": math.sqrt(float(torch.real(torch.trace(rho @ rho)).detach().cpu().item())),
    }


def scalar_profile(readouts: dict[str, Any]) -> dict[str, float]:
    qit = readouts["qit"]
    igt = readouts["igt"]
    hol = readouts["holodeck_runtime"]
    phy = readouts["physics_math"]
    return {
        "qit": qit["von_neumann_entropy"] + qit["coherence_l1"] + qit["purity"] + qit["subsystem_entropy_q0"],
        "igt": igt["asymmetry_sum"],
        "holodeck_runtime": sum(hol["normalized_signature"]),
        "physics_math": abs(float(phy["pauli_x_q0"]))
        + abs(float(phy["pauli_y_q0"]))
        + abs(float(phy["pauli_z_q0"]))
        + float(phy["clifford_grade1_norm"]),
    }


def matrix_from_profiles(profiles: list[dict[str, float]], order: list[str]) -> list[list[float]]:
    return [[profile[lens] for lens in order] for profile in profiles]


def matrix_l1_delta(left: list[list[float]], right: list[list[float]]) -> float:
    return sum(abs(left[row][col] - right[row][col]) for row in range(len(left)) for col in range(len(left[row])))


def column_std_sum(matrix: list[list[float]]) -> float:
    rows = len(matrix)
    cols = len(matrix[0])
    total = 0.0
    for col in range(cols):
        vals = [matrix[row][col] for row in range(rows)]
        mean_val = sum(vals) / rows
        total += math.sqrt(sum((v - mean_val) ** 2 for v in vals) / rows)
    return total


def rounded_signature(profile: dict[str, float]) -> list[float]:
    return [round(profile[lens], 9) for lens in LENS_ORDER]


def class_count(profiles: list[dict[str, float]]) -> int:
    return len({json.dumps(rounded_signature(profile)) for profile in profiles})


def constraints_for_density(rho: torch.Tensor) -> dict[str, Any]:
    herm = (rho + torch.conj(rho.T)) / 2.0
    eigs = torch.real(torch.linalg.eigvalsh(herm))
    return {
        "trace_eq_1": abs(float(torch.real(torch.trace(rho)).detach().cpu().item()) - 1.0) <= TOL,
        "psd": float(torch.min(eigs).detach().cpu().item()) >= -TOL,
        "hermitian": float(torch.linalg.norm(rho - torch.conj(rho.T)).detach().cpu().item()) <= TOL,
        "normalization": abs(float(torch.real(torch.trace(rho)).detach().cpu().item()) - 1.0) <= TOL,
        "min_eigenvalue": float(torch.min(eigs).detach().cpu().item()),
    }


def compute_rows(*, erased: bool = False, reversed_order: bool = False) -> tuple[list[dict[str, Any]], list[dict[str, float]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    profiles: list[dict[str, float]] = []
    constraints: list[dict[str, Any]] = []
    for state in support_vectors():
        rho = erased_density() if erased else density_from_vector(state["amplitudes"])
        diag = diag_probs(rho)
        if reversed_order:
            diag = list(reversed(diag))
        readouts = {
            "qit": qit_readout(rho),
            "igt": igt_readout(rho),
            "holodeck_runtime": holodeck_signature(diag),
            "physics_math": physics_readout(rho),
        }
        profile = scalar_profile(readouts)
        constraint = constraints_for_density(rho)
        rows.append(
            {
                "state_id": state["state_id"],
                "support_index_labels": BASIS_LABELS,
                "amplitudes": "maximally_mixed_density_no_spinor_amplitudes"
                if erased
                else [
                    {"real": float(torch.real(v).detach().cpu().item()), "imag": float(torch.imag(v).detach().cpu().item())}
                    for v in state["amplitudes"]
                ],
                "readouts": readouts,
                "scalar_profile": profile,
                "constraints": constraint,
            }
        )
        profiles.append(profile)
        constraints.append(constraint)
    return rows, profiles, constraints


def param_density(theta: torch.Tensor) -> torch.Tensor:
    vec = torch.zeros(8, dtype=torch.complex128)
    c = torch.cos(theta).to(dtype=torch.float64)
    s = torch.sin(theta).to(dtype=torch.float64)
    vec[0] = c.to(dtype=torch.complex128)
    vec[3] = (s / math.sqrt(2)).to(dtype=torch.complex128)
    vec[5] = (1.0j * s / 2).to(dtype=torch.complex128)
    vec[6] = (s / 2).to(dtype=torch.complex128)
    return density_from_vector(vec)


def z_expectations_torch(rho: torch.Tensor) -> torch.Tensor:
    diag = torch.real(torch.diagonal(rho))
    return z_expectations_tensor_from_diag(diag)


def same_axis_igt(theta: torch.Tensor) -> torch.Tensor:
    z_vals = z_expectations_torch(param_density(theta))
    return z_vals[0] - z_vals[1]


def cross_axis_igt(theta: torch.Tensor) -> torch.Tensor:
    z_vals = z_expectations_torch(param_density(theta))
    return z_vals[2] - z_vals[0]


def jacrev_sensitivity_check() -> dict[str, Any]:
    theta = torch.tensor(0.41, dtype=torch.float64)
    same_value = same_axis_igt(theta)
    cross_value = cross_axis_igt(theta)
    same_grad = jacrev(same_axis_igt)(theta)
    cross_grad = jacrev(cross_axis_igt)(theta)
    return {
        "readout_map": "IGT lens q-Z payoff asymmetry",
        "parameterized_state": "cos(theta)|uuu> + sin(theta)/sqrt(2)|ddu> + i*sin(theta)/2|dud> + sin(theta)/2|udd>",
        "theta": float(theta.detach().cpu().item()),
        "same_axis_value_q0_minus_q1": float(same_value.detach().cpu().item()),
        "cross_axis_value_q2_minus_q0": float(cross_value.detach().cpu().item()),
        "same_axis_jacrev": float(same_grad.detach().cpu().item()),
        "cross_axis_jacrev": float(cross_grad.detach().cpu().item()),
        "cross_vs_same_gradient_flip": abs(float(cross_grad.detach().cpu().item())) > 1.0e-8
        and abs(float(same_grad.detach().cpu().item())) <= 1.0e-10,
    }


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(torch.float64)
    rows, profiles, constraints = compute_rows()
    erased_rows, erased_profiles, _ = compute_rows(erased=True)
    reversed_rows, reversed_profiles, _ = compute_rows(reversed_order=True)

    matrix = matrix_from_profiles(profiles, LENS_ORDER)
    shuffled_matrix = matrix_from_profiles(profiles, LABEL_SHUFFLE_ORDER)
    erased_matrix = matrix_from_profiles(erased_profiles, LENS_ORDER)
    reversed_matrix = matrix_from_profiles(reversed_profiles, LENS_ORDER)
    igt_erased_profiles = [{**profile, "igt": 0.0} for profile in profiles]
    igt_erased_matrix = matrix_from_profiles(igt_erased_profiles, LENS_ORDER)

    label_delta = matrix_l1_delta(matrix, shuffled_matrix)
    real_structure = column_std_sum(matrix)
    erased_structure = column_std_sum(erased_matrix)
    map_before = column_std_sum([[row[1]] for row in matrix])
    map_after = column_std_sum([[row[1]] for row in igt_erased_matrix])
    order_delta = matrix_l1_delta(matrix, reversed_matrix)
    full_classes = class_count(profiles)
    erased_classes = class_count(erased_profiles)
    jacrev_check = jacrev_sensitivity_check()

    all_constraints_ok = all(c["trace_eq_1"] and c["psd"] and c["hermitian"] and c["normalization"] for c in constraints)
    controls_ok = (
        label_delta > TOL
        and real_structure > TOL
        and erased_structure <= TOL
        and map_before > TOL
        and map_after <= TOL
        and order_delta > TOL
        and full_classes > erased_classes
        and jacrev_check["cross_vs_same_gradient_flip"]
    )

    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "engine": "pytorch",
        "backend": "pytorch_torch_func_readout_matrix",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "ran": True,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "carrier_source_pin": {
            "source_path": str(CARRIER_SOURCE_PATH),
            "result_path": str(CARRIER_RESULT_PATH),
            "read_only": True,
            "rebuilt": False,
        },
        "torch_version": torch.__version__,
        "torch_dtype": str(torch.get_default_dtype()),
        "claim_ceiling": "Scratch diagnostic cross-model readout matrix only: four readout lenses over one fixed Clifford-spinor support S. No identity, canon, bridge, IGT truth, physics truth, Axis0, or formal admission claim.",
        "packages_used": ["torch", "torch.func", "json", "hashlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "package_table": TOOL_MANIFEST,
        "M": {
            "explicit_finite_probe_family": [
                "QIT: von Neumann entropy, l1 coherence, purity, first-qubit subsystem entropy",
                "IGT lens only: abs(P[i,j]-P[j,i]) over qubit-Z payoff probes derived from carrier density",
                "Holodeck/runtime: ordered diagonal trajectory accumulator/reachability signature",
                "Physics/math: first-qubit Pauli coordinate grade-vector mirror",
            ],
            "matrix_shape": [len(rows), len(LENS_ORDER)],
            "lens_order": LENS_ORDER,
        },
        "C": {
            "trace_eq_1": all(c["trace_eq_1"] for c in constraints),
            "psd": all(c["psd"] for c in constraints),
            "hermitian": all(c["hermitian"] for c in constraints),
            "normalization": all(c["normalization"] for c in constraints),
            "rung_specific_constraint": "All four readout maps consume the same fixed support S of four Cl(6)-spinor density states; no readout consumes another readout and no lens identity is asserted.",
        },
        "S_mod_M": {
            "S": [row["state_id"] for row in rows],
            "equivalence_relation": "s ~_M t iff every scalarized readout probe in the four-lens matrix agrees after rounding to 1e-9",
            "full_probe_class_count": full_classes,
            "carrier_erased_class_count": erased_classes,
            "full_signatures": [rounded_signature(profile) for profile in profiles],
            "carrier_erased_signatures": [rounded_signature(profile) for profile in erased_profiles],
        },
        "readout_rows": rows,
        "control_rows": {
            "carrier_erasure_rows": erased_rows,
            "order_reversal_rows": reversed_rows,
        },
        "controls": {
            "label_shuffle": {
                "falsifies": "Rosetta-style relabeling where all lenses carry the same chart",
                "original_lens_order": LENS_ORDER,
                "shuffled_lens_order": LABEL_SHUFFLE_ORDER,
                "matrix_l1_delta": label_delta,
                "flips": label_delta > TOL,
            },
            "carrier_erasure": {
                "falsifies": "carrier-agnostic decorative readouts",
                "real_structure_norm": real_structure,
                "erased_structure_norm": erased_structure,
                "structure_drop": real_structure - erased_structure,
                "full_class_count": full_classes,
                "erased_class_count": erased_classes,
                "flips": real_structure > TOL and erased_structure <= TOL and full_classes > erased_classes,
            },
            "readout_map_erasure": {
                "falsifies": "a readout column that remains structured after replacing A_i with a constant map",
                "erased_lens": "igt",
                "column_structure_before": map_before,
                "column_structure_after": map_after,
                "flips": map_before > TOL and map_after <= TOL,
            },
            "order_composition_reversal": {
                "falsifies": "runtime readout ignoring its ordered carrier composition",
                "basis_order": BASIS_LABELS,
                "reversed_basis_order": list(reversed(BASIS_LABELS)),
                "matrix_l1_delta": order_delta,
                "flips": order_delta > TOL,
            },
        },
        "torch_func_jacrev": jacrev_check,
        "summary": {
            "support_size": len(rows),
            "lens_count": len(LENS_ORDER),
            "full_probe_class_count": full_classes,
            "carrier_erased_class_count": erased_classes,
            "label_shuffle_delta": label_delta,
            "real_structure_norm": real_structure,
            "erased_structure_norm": erased_structure,
            "readout_map_erasure_before": map_before,
            "readout_map_erasure_after": map_after,
            "order_reversal_delta": order_delta,
            "same_axis_jacrev": jacrev_check["same_axis_jacrev"],
            "cross_axis_jacrev": jacrev_check["cross_axis_jacrev"],
            "all_constraints_ok": all_constraints_ok,
        },
        "all_pass": all_constraints_ok and controls_ok,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = to_jsonable(build_result())
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = result["summary"]
    print(f"wrote: {RESULT_PATH}")
    print(
        "CROSS_MODEL_READOUT_MATRIX_V0_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"classes={summary['full_probe_class_count']}->{summary['carrier_erased_class_count']} "
        f"label_delta={summary['label_shuffle_delta']} "
        f"erased_structure={summary['erased_structure_norm']} "
        f"same_jac={summary['same_axis_jacrev']} "
        f"cross_jac={summary['cross_axis_jacrev']} "
        f"order_delta={summary['order_reversal_delta']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
