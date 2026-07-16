#!/usr/bin/env python3
"""Deterministic QICS battery for associative qubit relative-entropy controls.

The channel constants and 16 stage anchors are copied from the read-only
``system_v7/constraint_core/engines/targets.json`` contract.  This module never
imports from or writes to ``constraint_core``.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np
import qics


HERE = Path(__file__).resolve().parent
PHYS_LIB_RECEIPT = HERE / "physlib_dpi_axiom_check.txt"
QICS_CHECKOUT = Path("/Users/joshuaeisenhart/GitHub/qics")
EXPECTED_PYTHON = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
TARGETS_SOURCE = Path(
    "/Users/joshuaeisenhart/Codex-Ratchet/system_v7/constraint_core/engines/targets.json"
)
ORACLE_TARGETS_SOURCE = TARGETS_SOURCE.with_name("oracle_targets.py")
EXPECTED_TARGETS_SHA256 = "1d74d038881b528e67e7ac21d9feef09e26c942ebc0e8f3bbcbca1e78ebbe69e"
EXPECTED_ORACLE_TARGETS_SHA256 = "e97247034d7da3a2ebbd27bda01d348e76da6c7cd605144219a3f297524dcdfb"

SCHEMA = "codex_ratchet.qics_physlib_entropy_controls_result.v0"
SIM_ID = "qics_physlib_entropy_controls_v0"
SEED = 0
CEILING = (
    "associative-entropy controls only; no exceptional/Jordan DPI inference licensed."
)

G = 0.35
KAP = 1.0
Q = 0.6321205588285577
TH = 0.7853981633974483
T_FLOW = 1.0
N_STEPS = 400
PROBE = (0.55, 0.35, 0.25)

TERRAINS = {
    0: (+1, "damp", +1),
    1: (+1, "depol", 0),
    2: (+1, "damp", -1),
    3: (+1, "proj", 0),
    4: (-1, "damp", -1),
    5: (-1, "depol", 0),
    6: (-1, "damp", +1),
    7: (-1, "proj", 0),
}
NATIVE_OPERATORS = {
    0: ("Ti", "Fi"),
    1: ("Ti", "Fi"),
    2: ("Te", "Fe"),
    3: ("Te", "Fe"),
    4: ("Ti", "Fi"),
    5: ("Ti", "Fi"),
    6: ("Te", "Fe"),
    7: ("Te", "Fe"),
}

# Copied verbatim from targets.json. Runtime reads of constraint_core are forbidden.
COPIED_STAGE_TARGETS = [
    {"t": 0, "op": "Ti", "bloch_down": [0.15118960892700745, 0.07002569850719088, 0.6791130756528434]},
    {"t": 0, "op": "Fi", "bloch_down": [0.41097596659811375, -0.3456079795016491, 0.6148029424715078]},
    {"t": 1, "op": "Ti", "bloch_down": [0.059039922818789586, 0.06725922805015336, 0.028167953846973792]},
    {"t": 1, "op": "Fi", "bloch_down": [0.16048714935194022, 0.10936225452286993, 0.14919775687755948]},
    {"t": 2, "op": "Te", "bloch_down": [0.1373510004316365, 0.14664622699949717, -0.1939527705396904]},
    {"t": 2, "op": "Fe", "bloch_down": [-0.18474916418899956, 0.37899281180493266, -0.5272182917373271]},
    {"t": 3, "op": "Te", "bloch_down": [0.09388638147908362, 0.014636145755844801, 0.07939900185774496]},
    {"t": 3, "op": "Fe", "bloch_down": [0.038255334181288146, 0.0945200598285661, 0.2158288639476943]},
    {"t": 4, "op": "Ti", "bloch_down": [0.1650965568941112, -0.0013336928831351187, -0.45644778533692776]},
    {"t": 4, "op": "Fi", "bloch_down": [0.44877897054641747, 0.32019381248763157, -0.3253208360510147]},
    {"t": 5, "op": "Ti", "bloch_down": [0.07888509666153286, 0.027040580734766582, 0.06254531330809343]},
    {"t": 5, "op": "Fi", "bloch_down": [0.21443192479128004, 0.007748904568425502, 0.09620133491160582]},
    {"t": 6, "op": "Te", "bloch_down": [0.24050278025885186, 0.09932730676074347, 0.27586675310938674]},
    {"t": 6, "op": "Fe", "bloch_down": [-0.020857410481312233, 0.3609797041118167, 0.7498835820532438]},
    {"t": 7, "op": "Te", "bloch_down": [0.04583238857325542, 0.02524318707089651, 0.10344091134042799]},
    {"t": 7, "op": "Fe", "bloch_down": [-0.01611192873565701, 0.0809287142519084, 0.28118154961592845]},
]

TOLERANCES = {
    "contract_bloch_abs": 1e-6,
    "choi_psd_abs": 1e-9,
    "trace_preserving_abs": 1e-9,
    "state_abs": 1e-9,
    "state_positive_floor": 1e-12,
    "qics_fixed_input_abs": 1e-8,
    "qics_spectral_abs": 1e-8,
    "dpi_slack": 1e-9,
    "false_dpi_violation_min": 1e-6,
}
SOLVER_OPTIONS = {
    "max_iter": 200,
    "max_time": 120,
    "tol_gap": 1e-10,
    "tol_feas": 1e-10,
    "tol_infeas": 1e-12,
    "tol_ip": 1e-13,
    "verbose": 0,
}

I2 = np.eye(2, dtype=np.complex128)
SX = np.array([[0, 1], [1, 0]], dtype=np.complex128)
SY = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
SZ = np.array([[1, 0], [0, -1]], dtype=np.complex128)
SP = 0.5 * (SX + 1j * SY)
SM = 0.5 * (SX - 1j * SY)

MatrixMap = Callable[[np.ndarray], np.ndarray]

TOOL_MANIFEST = {
    "qics": {
        "function": "qics.cones.QuantRelEntr fixed-input epigraph minimization",
        "reason": "Every accepted DPI margin and the false-map violation use QICS values; a missing or bad solve fails the battery.",
    },
    "numpy": {
        "function": "float64 RK4, Choi eigenspectra, state diagnostics, and spectral Umegaki comparator",
        "reason": "Reconstructs the copied channel contract and supplies a computation independent of the QICS cone value.",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "qics": "supportive_independent_cross_check",  # demoted per fresh audit 2026-07-11: stub test showed agreement-gating, not divergence-gating
    "numpy": "supportive_independent_comparator",
}


def stable_float(value: Any) -> float:
    real = float(np.real(value))
    if not math.isfinite(real):
        raise ValueError(f"non-finite numeric value: {value!r}")
    return float(f"{real:.15g}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(checkout: Path, *args: str) -> str:
    return subprocess.check_output(
        ["/usr/bin/git", "-C", str(checkout), *args], text=True
    ).strip()


def dissipator(operator: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    product = operator.conj().T @ operator
    return (
        operator @ matrix @ operator.conj().T
        - 0.5 * (product @ matrix + matrix @ product)
    )


def terrain_generator(index: int) -> MatrixMap:
    epsilon, kind, pole = TERRAINS[index]
    hamiltonian = epsilon * (SX + SY + SZ) / np.sqrt(3.0)

    def generator(matrix: np.ndarray) -> np.ndarray:
        value = -1j * G * (hamiltonian @ matrix - matrix @ hamiltonian)
        if kind == "damp":
            value = value + KAP * dissipator(SP if pole > 0 else SM, matrix)
        elif kind == "depol":
            value = value + 0.5 * KAP * (
                dissipator(SX, matrix) + dissipator(SY, matrix)
            )
        elif kind == "proj":
            value = value + KAP * dissipator(SZ, matrix)
        else:
            raise ValueError(f"unknown terrain kind: {kind}")
        return np.asarray(value, dtype=np.complex128)

    return generator


def rk4_flow(
    generator: MatrixMap,
    matrix: np.ndarray,
    *,
    time: float = T_FLOW,
    steps: int = N_STEPS,
) -> np.ndarray:
    """Apply the linear RK4 approximation without nonlinear renormalization."""
    value = np.asarray(matrix, dtype=np.complex128).copy()
    dt = time / steps
    for _ in range(steps):
        k1 = generator(value)
        k2 = generator(value + 0.5 * dt * k1)
        k3 = generator(value + 0.5 * dt * k2)
        k4 = generator(value + dt * k3)
        value = value + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    return np.asarray(value, dtype=np.complex128)


def operator_channel(name: str) -> MatrixMap:
    p0 = 0.5 * (I2 + SZ)
    p1 = 0.5 * (I2 - SZ)
    px = 0.5 * (I2 + SX)
    mx = 0.5 * (I2 - SX)
    if name == "Ti":
        return lambda matrix: (1.0 - Q) * matrix + Q * (
            p0 @ matrix @ p0 + p1 @ matrix @ p1
        )
    if name == "Te":
        return lambda matrix: (1.0 - Q) * matrix + Q * (
            px @ matrix @ px + mx @ matrix @ mx
        )
    if name == "Fi":
        unitary = np.cos(TH / 2.0) * I2 - 1j * np.sin(TH / 2.0) * SX
        return lambda matrix: unitary @ matrix @ unitary.conj().T
    if name == "Fe":
        unitary = np.cos(TH / 2.0) * I2 - 1j * np.sin(TH / 2.0) * SZ
        return lambda matrix: unitary @ matrix @ unitary.conj().T
    raise ValueError(f"unknown operator channel: {name}")


def bloch_expansion(scale: float) -> MatrixMap:
    def apply(matrix: np.ndarray) -> np.ndarray:
        trace = np.trace(matrix)
        return scale * matrix + (1.0 - scale) * trace * I2 / 2.0

    return apply


def bloch_state(vector: np.ndarray | tuple[float, float, float]) -> np.ndarray:
    x, y, z = np.asarray(vector, dtype=np.float64)
    return np.asarray(0.5 * (I2 + x * SX + y * SY + z * SZ), dtype=np.complex128)


def bloch_vector(matrix: np.ndarray) -> np.ndarray:
    return np.asarray(
        [np.trace(matrix @ pauli).real for pauli in (SX, SY, SZ)],
        dtype=np.float64,
    )


def compose(after: MatrixMap, before: MatrixMap) -> MatrixMap:
    return lambda matrix: after(before(matrix))


def build_channels() -> list[dict[str, Any]]:
    flows: dict[int, MatrixMap] = {
        index: (
            lambda matrix, generator=terrain_generator(index): rk4_flow(
                generator, matrix
            )
        )
        for index in range(8)
    }
    operators = {name: operator_channel(name) for name in ("Ti", "Te", "Fi", "Fe")}
    channels: list[dict[str, Any]] = []
    for index in range(8):
        channels.append(
            {
                "id": f"terrain_flow_t{index}",
                "family": "terrain_flow",
                "terrain": index,
                "operator": None,
                "apply": flows[index],
            }
        )
    for name in ("Ti", "Te", "Fi", "Fe"):
        representative_terrain = 0 if name in {"Ti", "Fi"} else 2
        channels.append(
            {
                "id": f"operator_{name}",
                "family": "operator",
                "terrain": representative_terrain,
                "operator": name,
                "apply": operators[name],
            }
        )
    for target in COPIED_STAGE_TARGETS:
        index = int(target["t"])
        name = str(target["op"])
        channels.append(
            {
                "id": f"stage_t{index}_{name}_down",
                "family": "composed_stage",
                "terrain": index,
                "operator": name,
                "apply": compose(operators[name], flows[index]),
            }
        )
    if len(channels) != 28:
        raise AssertionError(f"expected 28 channels, built {len(channels)}")
    return channels


def expected_channel_ids() -> list[str]:
    ids = [f"terrain_flow_t{index}" for index in range(8)]
    ids.extend(f"operator_{name}" for name in ("Ti", "Te", "Fi", "Fe"))
    ids.extend(
        f"stage_t{target['t']}_{target['op']}_down"
        for target in COPIED_STAGE_TARGETS
    )
    return ids


def fixed_point_like_states() -> dict[int, np.ndarray]:
    probe = bloch_state(PROBE)
    return {
        index: rk4_flow(
            terrain_generator(index), probe, time=8.0, steps=1600
        )
        for index in range(8)
    }


def random_full_rank_state(rng: np.random.Generator) -> np.ndarray:
    raw = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
    matrix = raw @ raw.conj().T + 0.25 * I2
    return np.asarray(matrix / np.trace(matrix).real, dtype=np.complex128)


def state_pairs(
    terrain_index: int,
    fixed_states: dict[int, np.ndarray],
    random_pairs: list[tuple[np.ndarray, np.ndarray]],
) -> list[dict[str, Any]]:
    probe = bloch_state(PROBE)
    pairs = [
        {"id": "probe_vs_maximally_mixed", "rho": probe, "sigma": I2 / 2.0},
        {
            "id": f"probe_vs_terrain_t{terrain_index}_fixed_point_like",
            "rho": probe,
            "sigma": fixed_states[terrain_index],
        },
    ]
    pairs.extend(
        {"id": f"seed0_random_full_rank_{index}", "rho": rho, "sigma": sigma}
        for index, (rho, sigma) in enumerate(random_pairs)
    )
    return pairs


def state_diagnostics(matrix: np.ndarray) -> dict[str, Any]:
    eigenvalues = np.linalg.eigvalsh((matrix + matrix.conj().T) / 2.0)
    return {
        "hermitian_residual": stable_float(np.max(np.abs(matrix - matrix.conj().T))),
        "trace_one_residual": stable_float(abs(np.trace(matrix) - 1.0)),
        "minimum_eigenvalue": stable_float(np.min(eigenvalues)),
        "maximum_eigenvalue": stable_float(np.max(eigenvalues)),
    }


def state_is_full_rank(matrix: np.ndarray) -> bool:
    diagnostics = state_diagnostics(matrix)
    return bool(
        diagnostics["hermitian_residual"] <= TOLERANCES["state_abs"]
        and diagnostics["trace_one_residual"] <= TOLERANCES["state_abs"]
        and diagnostics["minimum_eigenvalue"] > TOLERANCES["state_positive_floor"]
    )


def choi_certificate(apply_map: MatrixMap) -> dict[str, Any]:
    choi = np.zeros((4, 4), dtype=np.complex128)
    trace_out = np.zeros((2, 2), dtype=np.complex128)
    for i in range(2):
        for j in range(2):
            matrix_unit = np.zeros((2, 2), dtype=np.complex128)
            matrix_unit[i, j] = 1.0
            mapped = np.asarray(apply_map(matrix_unit), dtype=np.complex128)
            choi[2 * i : 2 * (i + 1), 2 * j : 2 * (j + 1)] = mapped
            trace_out[i, j] = np.trace(mapped)
    hermitian_residual = float(np.max(np.abs(choi - choi.conj().T)))
    hermitian_choi = (choi + choi.conj().T) / 2.0
    minimum_eigenvalue = float(np.min(np.linalg.eigvalsh(hermitian_choi)))
    tp_residual = float(np.max(np.abs(trace_out - I2)))
    cp_pass = bool(
        hermitian_residual <= TOLERANCES["choi_psd_abs"]
        and minimum_eigenvalue >= -TOLERANCES["choi_psd_abs"]
    )
    tp_pass = bool(tp_residual <= TOLERANCES["trace_preserving_abs"])
    return {
        "choi_hermitian_residual": stable_float(hermitian_residual),
        "minimum_choi_eigenvalue": stable_float(minimum_eigenvalue),
        "trace_preserving_residual": stable_float(tp_residual),
        "complete_positivity_pass": cp_pass,
        "trace_preservation_pass": tp_pass,
        "accepted_as_cptp": bool(cp_pass and tp_pass),
    }


def spectral_umegaki(rho: np.ndarray, sigma: np.ndarray) -> float:
    rho_values, rho_vectors = np.linalg.eigh(rho)
    sigma_values, sigma_vectors = np.linalg.eigh(sigma)
    if np.min(rho_values) <= 0.0 or np.min(sigma_values) <= 0.0:
        raise ValueError("spectral Umegaki comparator requires full-rank states")
    log_rho = (rho_vectors * np.log(rho_values)) @ rho_vectors.conj().T
    log_sigma = (sigma_vectors * np.log(sigma_values)) @ sigma_vectors.conj().T
    return stable_float(np.trace(rho @ (log_rho - log_sigma)).real)


def qics_quant_rel_entr(rho: np.ndarray, sigma: np.ndarray) -> dict[str, Any]:
    cone = qics.cones.QuantRelEntr(2, iscomplex=True)
    variable_dimension = 17
    objective = np.zeros((variable_dimension, 1), dtype=np.float64)
    objective[0, 0] = 1.0
    constraints = np.zeros((variable_dimension - 1, variable_dimension), dtype=np.float64)
    constraints[:, 1:] = np.eye(variable_dimension - 1, dtype=np.float64)
    fixed_values = np.vstack(
        [qics.vectorize.mat_to_vec(rho), qics.vectorize.mat_to_vec(sigma)]
    )
    model = qics.Model(c=objective, A=constraints, b=fixed_values, cones=[cone])
    info = qics.Solver(model, **SOLVER_OPTIONS).solve()
    solved_rho = np.asarray(info["s_opt"][0][1])
    solved_sigma = np.asarray(info["s_opt"][0][2])
    fixed_residual = max(
        float(np.max(np.abs(solved_rho - rho))),
        float(np.max(np.abs(solved_sigma - sigma))),
    )
    solver_pass = bool(
        str(info["sol_status"]) in {"optimal", "near_optimal"}
        and str(info["exit_status"]) in {"solved", "slow_progress"}
    )
    return {
        "value": stable_float(info["p_obj"]),
        "solver_status": str(info["sol_status"]),
        "exit_status": str(info["exit_status"]),
        "iterations": int(info["num_iter"]),
        "optimality_gap": stable_float(info["opt_gap"]),
        "primal_feasibility": stable_float(info["p_feas"]),
        "dual_feasibility": stable_float(info["d_feas"]),
        "fixed_input_max_abs_residual": stable_float(fixed_residual),
        "solver_pass": solver_pass,
    }


def relative_entropy_pair(rho: np.ndarray, sigma: np.ndarray) -> dict[str, Any]:
    if not state_is_full_rank(rho) or not state_is_full_rank(sigma):
        raise ValueError("QICS input pair is not full-rank density data")
    spectral = spectral_umegaki(rho, sigma)
    qics_result = qics_quant_rel_entr(rho, sigma)
    error = abs(qics_result["value"] - spectral)
    return {
        "qics": qics_result,
        "spectral_umegaki": spectral,
        "qics_spectral_abs_error": stable_float(error),
        "fixed_input_pass": bool(
            qics_result["fixed_input_max_abs_residual"]
            <= TOLERANCES["qics_fixed_input_abs"]
        ),
        "agreement_pass": bool(error <= TOLERANCES["qics_spectral_abs"]),
    }


def copied_contract_anchor_results(
    channels: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {channel["id"]: channel for channel in channels}
    probe = bloch_state(PROBE)
    results = []
    for target in COPIED_STAGE_TARGETS:
        channel_id = f"stage_t{target['t']}_{target['op']}_down"
        observed = bloch_vector(by_id[channel_id]["apply"](probe))
        expected = np.asarray(target["bloch_down"], dtype=np.float64)
        residual = float(np.max(np.abs(observed - expected)))
        results.append(
            {
                "channel_id": channel_id,
                "observed_bloch_down": [stable_float(item) for item in observed],
                "copied_target_bloch_down": [stable_float(item) for item in expected],
                "max_abs_residual": stable_float(residual),
                "pass": bool(residual <= TOLERANCES["contract_bloch_abs"]),
            }
        )
    return results


def evaluate_false_variant() -> dict[str, Any]:
    apply_map = bloch_expansion(1.5)
    certificate = choi_certificate(apply_map)
    rho = bloch_state((0.0, 0.0, 0.50))
    sigma = bloch_state((0.0, 0.0, -0.40))
    mapped_rho = apply_map(rho)
    mapped_sigma = apply_map(sigma)
    input_case = relative_entropy_pair(rho, sigma)
    output_case = relative_entropy_pair(mapped_rho, mapped_sigma)
    qics_violation = output_case["qics"]["value"] - input_case["qics"]["value"]
    spectral_violation = (
        output_case["spectral_umegaki"] - input_case["spectral_umegaki"]
    )
    negative_choi_detected = bool(certificate["minimum_choi_eigenvalue"] < -1e-9)
    qics_dpi_violation_detected = bool(
        qics_violation > TOLERANCES["false_dpi_violation_min"]
    )
    spectral_dpi_violation_detected = bool(
        spectral_violation > TOLERANCES["false_dpi_violation_min"]
    )
    instrument_detected = bool(
        negative_choi_detected
        and qics_dpi_violation_detected
        and spectral_dpi_violation_detected
        and input_case["agreement_pass"]
        and output_case["agreement_pass"]
        and input_case["fixed_input_pass"]
        and output_case["fixed_input_pass"]
        and input_case["qics"]["solver_pass"]
        and output_case["qics"]["solver_pass"]
    )
    result = {
        "id": "bloch_expansion_c_1p5_non_cp",
        "scale": 1.5,
        "outputs_are_full_rank_states": bool(
            state_is_full_rank(mapped_rho) and state_is_full_rank(mapped_sigma)
        ),
        "input_rho": state_diagnostics(rho),
        "input_sigma": state_diagnostics(sigma),
        "output_rho": state_diagnostics(mapped_rho),
        "output_sigma": state_diagnostics(mapped_sigma),
        "certificate": certificate,
        "input_case": input_case,
        "output_case": output_case,
        "qics_dpi_violation": stable_float(qics_violation),
        "spectral_dpi_violation": stable_float(spectral_violation),
        "negative_choi_detected": negative_choi_detected,
        "qics_dpi_violation_detected": qics_dpi_violation_detected,
        "spectral_dpi_violation_detected": spectral_dpi_violation_detected,
        "instrument_detected_false_variant": instrument_detected,
        "abort_rule": "If Choi negativity or a DPI violation above 1e-6 is absent, the instrument is broken and exits nonzero.",
    }
    if not instrument_detected:
        raise RuntimeError(
            "INSTRUMENT BROKEN: the c=1.5 false variant did not trigger both "
            f"Choi negativity and DPI expansion: {result}"
        )
    return result


def environment_receipt() -> dict[str, Any]:
    imported_qics = Path(qics.__file__).resolve()
    checks = {
        "requested_python_exact": Path(sys.executable).resolve()
        == EXPECTED_PYTHON.resolve(),
        "qics_version_1p1p3": qics.__version__ == "1.1.3",
        "qics_import_from_requested_checkout": imported_qics.is_relative_to(
            QICS_CHECKOUT.resolve()
        ),
        "physlib_green_receipt_present": PHYS_LIB_RECEIPT.is_file(),
    }
    return {
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "qics_version": qics.__version__,
        "qics_module": str(imported_qics),
        "qics_git_commit": git_output(QICS_CHECKOUT, "rev-parse", "HEAD"),
        "qics_git_status_porcelain": git_output(QICS_CHECKOUT, "status", "--porcelain"),
        "numpy_version": np.__version__,
        "scipy_version": importlib.metadata.version("scipy"),
        "physlib_receipt": str(PHYS_LIB_RECEIPT),
        "physlib_receipt_sha256": sha256_file(PHYS_LIB_RECEIPT),
        "physlib_rerun": False,
    }


def source_hashes() -> dict[str, str]:
    return {
        "card.md": sha256_file(HERE / "card.md"),
        "physlib_dpi_axiom_check.txt": sha256_file(PHYS_LIB_RECEIPT),
        "qics_battery.py": sha256_file(HERE / "qics_battery.py"),
        "run_all.sh": sha256_file(HERE / "run_all.sh"),
    }


def dependency_hashes() -> dict[str, Any]:
    qics_files = [
        "qics/cones/entropy/quantrelentr.py",
        "qics/model.py",
        "qics/solver.py",
        "qics/vectorize.py",
    ]
    resolved_python = EXPECTED_PYTHON.resolve()
    return {
        "algorithm": "sha256",
        "copied_contract_snapshots": {
            str(TARGETS_SOURCE): EXPECTED_TARGETS_SHA256,
            str(ORACLE_TARGETS_SOURCE): EXPECTED_ORACLE_TARGETS_SHA256,
        },
        "qics_sources": {
            name: sha256_file(QICS_CHECKOUT / name) for name in qics_files
        },
        "python_executable_resolved": {
            "path": str(resolved_python),
            "sha256": sha256_file(resolved_python),
        },
    }


def build_result() -> dict[str, Any]:
    environment = environment_receipt()
    if not environment["all_checks_pass"]:
        raise RuntimeError(f"environment gate failed: {environment['checks']}")

    channels = build_channels()
    anchor_results = copied_contract_anchor_results(channels)
    if not all(item["pass"] for item in anchor_results):
        raise RuntimeError(f"copied 16-stage contract anchor failed: {anchor_results}")

    fixed_states = fixed_point_like_states()
    rng = np.random.default_rng(SEED)
    random_pairs = [
        (random_full_rank_state(rng), random_full_rank_state(rng))
        for _ in range(4)
    ]
    channel_results = []
    all_qics_margins: list[float] = []
    all_spectral_margins: list[float] = []
    all_qics_errors: list[float] = []
    all_fixed_input_residuals: list[float] = []
    qics_solves = 0

    for channel in channels:
        apply_map = channel["apply"]
        certificate = choi_certificate(apply_map)
        pair_results = []
        for pair in state_pairs(channel["terrain"], fixed_states, random_pairs):
            rho = pair["rho"]
            sigma = pair["sigma"]
            mapped_rho = apply_map(rho)
            mapped_sigma = apply_map(sigma)
            input_case = relative_entropy_pair(rho, sigma)
            output_case = relative_entropy_pair(mapped_rho, mapped_sigma)
            qics_solves += 2
            qics_margin = input_case["qics"]["value"] - output_case["qics"]["value"]
            spectral_margin = (
                input_case["spectral_umegaki"] - output_case["spectral_umegaki"]
            )
            all_qics_margins.append(qics_margin)
            all_spectral_margins.append(spectral_margin)
            all_qics_errors.extend(
                [
                    input_case["qics_spectral_abs_error"],
                    output_case["qics_spectral_abs_error"],
                ]
            )
            all_fixed_input_residuals.extend(
                [
                    input_case["qics"]["fixed_input_max_abs_residual"],
                    output_case["qics"]["fixed_input_max_abs_residual"],
                ]
            )
            pair_pass = bool(
                input_case["qics"]["solver_pass"]
                and output_case["qics"]["solver_pass"]
                and input_case["agreement_pass"]
                and output_case["agreement_pass"]
                and input_case["fixed_input_pass"]
                and output_case["fixed_input_pass"]
                and qics_margin >= -TOLERANCES["dpi_slack"]
                and spectral_margin >= -TOLERANCES["dpi_slack"]
                and state_is_full_rank(mapped_rho)
                and state_is_full_rank(mapped_sigma)
            )
            pair_results.append(
                {
                    "pair_id": pair["id"],
                    "input_rho": state_diagnostics(rho),
                    "input_sigma": state_diagnostics(sigma),
                    "output_rho": state_diagnostics(mapped_rho),
                    "output_sigma": state_diagnostics(mapped_sigma),
                    "input_relative_entropy": input_case,
                    "output_relative_entropy": output_case,
                    "qics_dpi_margin": stable_float(qics_margin),
                    "spectral_dpi_margin": stable_float(spectral_margin),
                    "qics_dpi_pass": bool(qics_margin >= -TOLERANCES["dpi_slack"]),
                    "spectral_dpi_pass": bool(
                        spectral_margin >= -TOLERANCES["dpi_slack"]
                    ),
                    "case_pass": pair_pass,
                }
            )
        channel_pass = bool(
            certificate["accepted_as_cptp"]
            and len(pair_results) == 6
            and all(item["case_pass"] for item in pair_results)
        )
        channel_results.append(
            {
                "channel_id": channel["id"],
                "family": channel["family"],
                "terrain": channel["terrain"],
                "operator": channel["operator"],
                "choi_certificate": certificate,
                "pairs": pair_results,
                "channel_pass": channel_pass,
            }
        )

    false_variant = evaluate_false_variant()
    qics_solves += 2
    tests = {
        "environment": environment["all_checks_pass"],
        "copied_contract_anchor_16_of_16": len(anchor_results) == 16
        and all(item["pass"] for item in anchor_results),
        "accepted_channel_count_28": len(channel_results) == 28,
        "all_accepted_channels_cptp": all(
            item["choi_certificate"]["accepted_as_cptp"]
            for item in channel_results
        ),
        "all_seeded_pairs_full_rank": all(
            pair["input_rho"]["minimum_eigenvalue"]
            > TOLERANCES["state_positive_floor"]
            and pair["input_sigma"]["minimum_eigenvalue"]
            > TOLERANCES["state_positive_floor"]
            and pair["output_rho"]["minimum_eigenvalue"]
            > TOLERANCES["state_positive_floor"]
            and pair["output_sigma"]["minimum_eigenvalue"]
            > TOLERANCES["state_positive_floor"]
            for channel in channel_results
            for pair in channel["pairs"]
        ),
        "all_qics_solver_runs": all(
            pair["input_relative_entropy"]["qics"]["solver_pass"]
            and pair["output_relative_entropy"]["qics"]["solver_pass"]
            for channel in channel_results
            for pair in channel["pairs"]
        ),
        "qics_spectral_agreement_at_most_1e_8": max(all_qics_errors)
        <= TOLERANCES["qics_spectral_abs"],
        "qics_fixed_input_residual_at_most_1e_8": max(all_fixed_input_residuals)
        <= TOLERANCES["qics_fixed_input_abs"],
        "all_qics_dpi_margins": min(all_qics_margins)
        >= -TOLERANCES["dpi_slack"],
        "all_spectral_dpi_margins": min(all_spectral_margins)
        >= -TOLERANCES["dpi_slack"],
        "all_channel_cases_pass": all(item["channel_pass"] for item in channel_results),
        "false_variant_negative_choi_detected": false_variant[
            "negative_choi_detected"
        ],
        "false_variant_qics_dpi_violation_gt_1e_6": false_variant[
            "qics_dpi_violation_detected"
        ],
        "false_variant_spectral_dpi_violation_gt_1e_6": false_variant[
            "spectral_dpi_violation_detected"
        ],
        "false_variant_joint_detection": false_variant[
            "instrument_detected_false_variant"
        ],
        "physlib_receipt_preserved_without_rerun": PHYS_LIB_RECEIPT.is_file()
        and not environment["physlib_rerun"],
        "claim_ceiling_bounded": CEILING
        == "associative-entropy controls only; no exceptional/Jordan DPI inference licensed.",
    }
    all_pass = bool(all(tests.values()))
    if not all_pass:
        raise RuntimeError(f"battery tests failed: {tests}")

    result = {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "name": "QICS and existing-Physlib associative entropy control battery",
        "version": "0.1.0",
        "tier": "tool_stage_control",
        "classification": "scratch_diagnostic",
        "sim_execution_kind": "classical",
        "sim_class": "tool_function_control_battery",
        "producer_status_label": "runs",
        "promotion_status": "diagnostic_only",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "CEILING": CEILING,
        "claim_ceiling": CEILING,
        "allowed_claims": [
            "finite associative matrix relative-entropy control evidence for the named channels and seed"
        ],
        "blocked_consumers": [
            "exceptional_or_Jordan_DPI_inference",
            "bridge_or_axis_admission",
            "canonical_scientific_promotion",
            "constraint_core_mutation",
        ],
        "command": (
            "PYTHONPATH=/Users/joshuaeisenhart/GitHub/qics "
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
            "-B qics_battery.py --output <append-only-result-path>"
        ),
        "runner_identity": {
            "script": "qics_battery.py",
            "interpreter": str(EXPECTED_PYTHON),
            "seed": SEED,
            "result_write_mode": "exclusive_create_with_version_suffix",
        },
        "root_constraints_in_force": [
            "finite seeded carrier and channel family",
            "separate structural and numeric falsifiers",
        ],
        "carrier_layer": "finite 2x2 complex matrix algebra",
        "geometry_layer": "none",
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": (
            "Umegaki relative-entropy DPI for 28 reconstructed qubit CPTP maps, "
            "with one non-CP expansion kill control"
        ),
        "branch_status_before_run": "control_only",
        "promotion_blockers": [
            "scratch_diagnostic classification",
            "associative matrices only",
            "no exceptional or Jordan carrier statement",
        ],
        "required_tools": ["qics==1.1.3", "numpy", "scipy as QICS dependency"],
        "actual_tools_used": ["qics", "numpy", "scipy as QICS dependency"],
        "proof_surfaces_used": [
            "existing physlib_dpi_axiom_check.txt receipt only; Lean was not invoked"
        ],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "environment": environment,
        "source_hashes": source_hashes(),
        "dependency_hashes": dependency_hashes(),
        "contract_source": {
            "path": str(TARGETS_SOURCE),
            "runtime_read": False,
            "copy_policy": "model constants and 16 bloch_down targets copied into qics_battery.py",
            "targets_json_expected_sha256": EXPECTED_TARGETS_SHA256,
            "oracle_targets_py_expected_sha256": EXPECTED_ORACLE_TARGETS_SHA256,
            "model_constants": {
                "G": G,
                "KAP": KAP,
                "Q": Q,
                "TH": TH,
                "T_FLOW": T_FLOW,
                "N_STEPS": N_STEPS,
                "PROBE": list(PROBE),
            },
        },
        "tolerances": TOLERANCES,
        "solver_options": SOLVER_OPTIONS,
        "required_inputs": [
            "copied targets.json constants and stage anchors",
            "seed zero deterministic full-rank state pairs",
            "existing Physlib GREEN receipt",
        ],
        "data_or_artifact_dependencies": [
            str(QICS_CHECKOUT),
            str(PHYS_LIB_RECEIPT),
        ],
        "required_negatives": [
            "Bloch expansion c=1.5 has negative Choi eigenvalue",
            "same expansion violates QICS DPI by more than 1e-6",
        ],
        "negatives_run": ["bloch_expansion_c_1p5_non_cp"],
        "kill_conditions": [
            "any copied stage anchor exceeds 1e-6",
            "any accepted channel fails CP or TP",
            "any accepted QICS DPI margin is below -1e-9",
            "any QICS/spectral value disagreement exceeds 1e-8",
            "the false map lacks either negative Choi eigenvalue or DPI violation above 1e-6",
            "an existing result would be overwritten",
        ],
        "contract_anchor_results": anchor_results,
        "channels": channel_results,
        "false_variant": false_variant,
        "metrics": {
            "channels_total": len(channel_results),
            "terrain_flows": sum(
                item["family"] == "terrain_flow" for item in channel_results
            ),
            "operator_channels": sum(
                item["family"] == "operator" for item in channel_results
            ),
            "composed_stages": sum(
                item["family"] == "composed_stage" for item in channel_results
            ),
            "state_pairs_per_channel": 6,
            "accepted_dpi_cases": len(all_qics_margins),
            "qics_solves": qics_solves,
            "minimum_qics_dpi_margin": stable_float(min(all_qics_margins)),
            "maximum_qics_dpi_margin": stable_float(max(all_qics_margins)),
            "minimum_spectral_dpi_margin": stable_float(
                min(all_spectral_margins)
            ),
            "maximum_spectral_dpi_margin": stable_float(
                max(all_spectral_margins)
            ),
            "maximum_qics_spectral_abs_error": stable_float(max(all_qics_errors)),
            "maximum_qics_fixed_input_abs_residual": stable_float(
                max(all_fixed_input_residuals)
            ),
            "maximum_contract_anchor_abs_residual": stable_float(
                max(item["max_abs_residual"] for item in anchor_results)
            ),
        },
        "tests": tests,
        "test_count": len(tests),
        "tests_passed": sum(bool(value) for value in tests.values()),
        "all_pass": all_pass,
        "all_tests_pass": all_pass,
        "required_artifacts": [
            "qics_battery.py",
            "run_all.sh",
            "append-only result JSON family",
            "unchanged physlib_dpi_axiom_check.txt",
        ],
        "artifacts_emitted": ["append-only result JSON"],
        "witness_trace_id": "qics_physlib_entropy_controls_v0_seed0",
        "result_summary": "28 accepted channels and 168 seeded DPI cases passed; the non-CP false map triggered both structural and numeric detections.",
        "pass_rule": "All contract, CPTP, QICS, comparator, DPI, false-control, environment, and ceiling tests are true.",
        "fail_rule": "Any false-control miss or accepted-channel failure aborts before a result is written.",
        "eligible_consumers": ["local_associative_entropy_control_audit"],
        "divergence_log": [
            "QICS cone values are checked against a separately implemented spectral Umegaki formula for every input and output.",
            "The copied standard-probe stage targets independently bind the local channel reconstruction to the read-only repository contract.",
            "The deliberately non-CP expansion is excluded from accepted evidence and must exhibit both Choi negativity and entropy expansion.",
        ],
    }
    return result


def versioned_output_path(requested: Path) -> Path:
    path = requested if requested.is_absolute() else HERE / requested
    path = path.resolve()
    if path.parent != HERE:
        raise ValueError("result output must stay inside the lane directory")
    if not path.exists():
        return path
    for version in range(1, 10000):
        candidate = path.with_name(f"{path.stem}.v{version:03d}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"no append-only version slot available for {path.name}")


def write_result_exclusive(requested: Path, result: dict[str, Any]) -> Path:
    output = versioned_output_path(requested)
    payload = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with output.open("x", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    return output


def validate_result_payload(payload: dict[str, Any]) -> dict[str, Any]:
    def diagnostics_valid(diagnostics: Any) -> bool:
        return bool(
            isinstance(diagnostics, dict)
            and isinstance(diagnostics.get("hermitian_residual"), (int, float))
            and diagnostics["hermitian_residual"] <= TOLERANCES["state_abs"]
            and isinstance(diagnostics.get("trace_one_residual"), (int, float))
            and diagnostics["trace_one_residual"] <= TOLERANCES["state_abs"]
            and isinstance(diagnostics.get("minimum_eigenvalue"), (int, float))
            and diagnostics["minimum_eigenvalue"]
            > TOLERANCES["state_positive_floor"]
            and isinstance(diagnostics.get("maximum_eigenvalue"), (int, float))
            and diagnostics["maximum_eigenvalue"] < 1.0 + TOLERANCES["state_abs"]
        )

    def relative_case_valid(case: Any) -> bool:
        if not isinstance(case, dict) or not isinstance(case.get("qics"), dict):
            return False
        qics_case = case["qics"]
        value = qics_case.get("value")
        spectral = case.get("spectral_umegaki")
        residual = qics_case.get("fixed_input_max_abs_residual")
        recorded_error = case.get("qics_spectral_abs_error")
        if not all(
            isinstance(item, (int, float))
            for item in (value, spectral, residual, recorded_error)
        ):
            return False
        computed_error = stable_float(abs(value - spectral))
        return bool(
            qics_case.get("solver_status") in {"optimal", "near_optimal"}
            and qics_case.get("exit_status") in {"solved", "slow_progress"}
            and qics_case.get("solver_pass") is True
            and residual <= TOLERANCES["qics_fixed_input_abs"]
            and case.get("fixed_input_pass") is True
            and computed_error == recorded_error
            and computed_error <= TOLERANCES["qics_spectral_abs"]
            and case.get("agreement_pass") is True
        )

    def accepted_pair_valid(pair: Any) -> bool:
        if not isinstance(pair, dict):
            return False
        input_case = pair.get("input_relative_entropy")
        output_case = pair.get("output_relative_entropy")
        if not relative_case_valid(input_case) or not relative_case_valid(output_case):
            return False
        qics_margin = stable_float(
            input_case["qics"]["value"] - output_case["qics"]["value"]
        )
        spectral_margin = stable_float(
            input_case["spectral_umegaki"] - output_case["spectral_umegaki"]
        )
        return bool(
            all(
                diagnostics_valid(pair.get(field))
                for field in ("input_rho", "input_sigma", "output_rho", "output_sigma")
            )
            and pair.get("qics_dpi_margin") == qics_margin
            and pair.get("spectral_dpi_margin") == spectral_margin
            and qics_margin >= -TOLERANCES["dpi_slack"]
            and spectral_margin >= -TOLERANCES["dpi_slack"]
            and pair.get("qics_dpi_pass") is True
            and pair.get("spectral_dpi_pass") is True
            and pair.get("case_pass") is True
        )

    anchors = payload.get("contract_anchor_results")
    channels = payload.get("channels")
    anchors = anchors if isinstance(anchors, list) else []
    channels = channels if isinstance(channels, list) else []
    channel_ids = [item.get("channel_id") for item in channels if isinstance(item, dict)]
    pairs = [
        pair
        for channel in channels
        if isinstance(channel, dict) and isinstance(channel.get("pairs"), list)
        for pair in channel["pairs"]
        if isinstance(pair, dict)
    ]
    qics_margins = [pair.get("qics_dpi_margin") for pair in pairs]
    spectral_margins = [pair.get("spectral_dpi_margin") for pair in pairs]
    qics_errors = [
        case.get("qics_spectral_abs_error")
        for pair in pairs
        for case in (
            pair.get("input_relative_entropy"),
            pair.get("output_relative_entropy"),
        )
        if isinstance(case, dict)
    ]
    fixed_residuals = [
        case.get("qics", {}).get("fixed_input_max_abs_residual")
        for pair in pairs
        for case in (
            pair.get("input_relative_entropy"),
            pair.get("output_relative_entropy"),
        )
        if isinstance(case, dict) and isinstance(case.get("qics"), dict)
    ]
    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
    tests = payload.get("tests") if isinstance(payload.get("tests"), dict) else {}
    false_variant = (
        payload.get("false_variant")
        if isinstance(payload.get("false_variant"), dict)
        else {}
    )
    certificate = (
        false_variant.get("certificate")
        if isinstance(false_variant.get("certificate"), dict)
        else {}
    )
    local_hashes = payload.get("source_hashes")
    local_hashes = local_hashes if isinstance(local_hashes, dict) else {}
    expected_local_files = {
        "card.md": HERE / "card.md",
        "physlib_dpi_axiom_check.txt": PHYS_LIB_RECEIPT,
        "qics_battery.py": HERE / "qics_battery.py",
        "run_all.sh": HERE / "run_all.sh",
    }
    dependency_receipt = payload.get("dependency_hashes")
    dependency_receipt = (
        dependency_receipt if isinstance(dependency_receipt, dict) else {}
    )
    current_dependencies = dependency_hashes()
    tool_manifest = payload.get("tool_manifest")
    tool_manifest = tool_manifest if isinstance(tool_manifest, dict) else {}

    evidence_shapes_valid = bool(
        len(anchors) == 16
        and all(
            isinstance(item, dict)
            and item.get("pass") is True
            and isinstance(item.get("max_abs_residual"), (int, float))
            and item["max_abs_residual"] <= TOLERANCES["contract_bloch_abs"]
            for item in anchors
        )
        and len(channels) == 28
        and channel_ids == expected_channel_ids()
        and len(set(channel_ids)) == 28
        and all(
            isinstance(channel.get("choi_certificate"), dict)
            and channel["choi_certificate"].get("accepted_as_cptp") is True
            and channel["choi_certificate"].get("minimum_choi_eigenvalue", -math.inf)
            >= -TOLERANCES["choi_psd_abs"]
            and channel["choi_certificate"].get("trace_preserving_residual", math.inf)
            <= TOLERANCES["trace_preserving_abs"]
            and isinstance(channel.get("pairs"), list)
            and len(channel["pairs"]) == 6
            and channel.get("channel_pass") is True
            and all(
                accepted_pair_valid(pair)
                for pair in channel["pairs"]
            )
            for channel in channels
            if isinstance(channel, dict)
        )
        and len(pairs) == 168
    )

    aggregate_evidence_valid = bool(
        len(qics_margins) == 168
        and all(isinstance(value, (int, float)) for value in qics_margins)
        and len(spectral_margins) == 168
        and all(isinstance(value, (int, float)) for value in spectral_margins)
        and len(qics_errors) == 336
        and all(isinstance(value, (int, float)) for value in qics_errors)
        and len(fixed_residuals) == 336
        and all(isinstance(value, (int, float)) for value in fixed_residuals)
        and min(qics_margins) >= -TOLERANCES["dpi_slack"]
        and min(spectral_margins) >= -TOLERANCES["dpi_slack"]
        and max(qics_errors) <= TOLERANCES["qics_spectral_abs"]
        and max(fixed_residuals) <= TOLERANCES["qics_fixed_input_abs"]
        and metrics.get("accepted_dpi_cases") == len(pairs)
        and metrics.get("minimum_qics_dpi_margin") == stable_float(min(qics_margins))
        and metrics.get("maximum_qics_spectral_abs_error")
        == stable_float(max(qics_errors))
        and metrics.get("maximum_qics_fixed_input_abs_residual")
        == stable_float(max(fixed_residuals))
    )

    false_input = false_variant.get("input_case")
    false_output = false_variant.get("output_case")
    false_qics_violation = (
        stable_float(false_output["qics"]["value"] - false_input["qics"]["value"])
        if relative_case_valid(false_input) and relative_case_valid(false_output)
        else None
    )
    false_spectral_violation = (
        stable_float(
            false_output["spectral_umegaki"] - false_input["spectral_umegaki"]
        )
        if relative_case_valid(false_input) and relative_case_valid(false_output)
        else None
    )
    false_nested_evidence_valid = bool(
        all(
            diagnostics_valid(false_variant.get(field))
            for field in ("input_rho", "input_sigma", "output_rho", "output_sigma")
        )
        and false_variant.get("outputs_are_full_rank_states") is True
        and false_qics_violation is not None
        and false_spectral_violation is not None
        and false_variant.get("qics_dpi_violation") == false_qics_violation
        and false_variant.get("spectral_dpi_violation") == false_spectral_violation
        and false_qics_violation > TOLERANCES["false_dpi_violation_min"]
        and false_spectral_violation > TOLERANCES["false_dpi_violation_min"]
    )

    checks = {
        "schema": payload.get("schema") == SCHEMA,
        "sim_id": payload.get("sim_id") == SIM_ID,
        "classification": payload.get("classification") == "scratch_diagnostic",
        "ceiling": payload.get("CEILING") == CEILING,
        "all_pass": payload.get("all_pass") is True,
        "all_tests_pass": payload.get("all_tests_pass") is True,
        "nested_evidence_shapes": evidence_shapes_valid,
        "nested_aggregates": aggregate_evidence_valid,
        "channel_count": metrics.get("channels_total") == 28,
        "stage_count": metrics.get("composed_stages") == 16,
        "case_count": metrics.get("accepted_dpi_cases") == 168,
        "test_ledger": bool(
            tests
            and all(value is True for value in tests.values())
            and payload.get("tests_passed") == payload.get("test_count") == len(tests)
        ),
        "false_negative_choi": false_variant.get("negative_choi_detected") is True
        and isinstance(certificate.get("minimum_choi_eigenvalue"), (int, float))
        and certificate["minimum_choi_eigenvalue"] < -1e-9
        and certificate.get("complete_positivity_pass") is False
        and certificate.get("trace_preservation_pass") is True
        and certificate.get("accepted_as_cptp") is False
        and isinstance(certificate.get("trace_preserving_residual"), (int, float))
        and certificate["trace_preserving_residual"]
        <= TOLERANCES["trace_preserving_abs"],
        "false_qics_violation": false_variant.get("qics_dpi_violation_detected")
        is True
        and isinstance(false_variant.get("qics_dpi_violation"), (int, float))
        and false_variant["qics_dpi_violation"]
        > TOLERANCES["false_dpi_violation_min"],
        "false_joint_detection": false_variant.get(
            "instrument_detected_false_variant"
        )
        is True
        and false_nested_evidence_valid,
        "physlib_not_rerun": payload.get("environment", {}).get("physlib_rerun")
        is False,
        "qics_tool_depth_honest": payload.get("tool_integration_depth", {}).get("qics")
        == "supportive_independent_cross_check",  # audit 2026-07-11: agreement-gated, demoted from load_bearing
        "promotion_blocked": payload.get("promotion_allowed") is False
        and payload.get("formal_admission_allowed") is False,
        "local_source_hashes": set(local_hashes) == set(expected_local_files)
        and all(
            local_hashes.get(name) == sha256_file(path)
            for name, path in expected_local_files.items()
        ),
        "dependency_hashes": dependency_receipt == current_dependencies,
        "copied_contract_hashes": payload.get("contract_source", {}).get(
            "targets_json_expected_sha256"
        )
        == EXPECTED_TARGETS_SHA256
        and payload.get("contract_source", {}).get(
            "oracle_targets_py_expected_sha256"
        )
        == EXPECTED_ORACLE_TARGETS_SHA256,
        "tool_manifest_reasons": bool(tool_manifest)
        and all(
            isinstance(item, dict)
            and isinstance(item.get("reason"), str)
            and bool(item["reason"].strip())
            for item in tool_manifest.values()
        ),
    }
    return {"checks": checks, "all_pass": all(checks.values())}


def validate_result(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return validate_result_payload(payload)


def print_summary(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    metrics = payload["metrics"]
    false_variant = payload["false_variant"]
    print("DPI margins summary")
    print(f"  channels: {metrics['channels_total']} (8 flows + 4 operators + 16 stages)")
    print(f"  accepted seeded cases: {metrics['accepted_dpi_cases']}")
    print(f"  minimum QICS DPI margin: {metrics['minimum_qics_dpi_margin']:.12g}")
    print(f"  maximum QICS DPI margin: {metrics['maximum_qics_dpi_margin']:.12g}")
    print(f"  minimum spectral DPI margin: {metrics['minimum_spectral_dpi_margin']:.12g}")
    print(
        "  maximum QICS/spectral absolute error: "
        f"{metrics['maximum_qics_spectral_abs_error']:.12g}"
    )
    print("false-variant detection evidence")
    print(
        "  minimum Choi eigenvalue: "
        f"{false_variant['certificate']['minimum_choi_eigenvalue']:.12g}"
    )
    print(f"  QICS DPI violation: {false_variant['qics_dpi_violation']:.12g}")
    print(
        "  spectral DPI violation: "
        f"{false_variant['spectral_dpi_violation']:.12g}"
    )
    print(
        "  joint detection: "
        f"{str(false_variant['instrument_detected_false_variant']).upper()}"
    )


def self_test() -> dict[str, bool]:
    channels = build_channels()
    false_certificate = choi_certificate(bloch_expansion(1.5))
    tests = {
        "copied_stage_target_count": len(COPIED_STAGE_TARGETS) == 16,
        "channel_count": len(channels) == 28,
        "channel_ids_unique": len({item["id"] for item in channels}) == 28,
        "false_map_trace_preserving": false_certificate["trace_preservation_pass"],
        "false_map_not_cp": not false_certificate["complete_positivity_pass"],
        "false_map_negative_choi": false_certificate["minimum_choi_eigenvalue"]
        < -1e-9,
        "ceiling_exact": CEILING
        == "associative-entropy controls only; no exceptional/Jordan DPI inference licensed.",
        "physlib_receipt_present": PHYS_LIB_RECEIPT.is_file(),
    }
    return tests


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--validate", type=Path)
    mode.add_argument("--summary", type=Path)
    mode.add_argument("--compare", nargs=2, type=Path, metavar=("FIRST", "SECOND"))
    parser.add_argument("--output", type=Path, default=HERE / "result.json")
    args = parser.parse_args()

    if args.self_test:
        tests = self_test()
        print(json.dumps({"tests": tests, "all_pass": all(tests.values())}, sort_keys=True))
        return 0 if all(tests.values()) else 1
    if args.validate:
        verdict = validate_result(args.validate)
        print(json.dumps(verdict, sort_keys=True))
        return 0 if verdict["all_pass"] else 1
    if args.summary:
        print_summary(args.summary)
        return 0
    if args.compare:
        first, second = args.compare
        identical = first.read_bytes() == second.read_bytes()
        print(
            json.dumps(
                {
                    "first": str(first),
                    "second": str(second),
                    "byte_identical": identical,
                    "sha256": sha256_file(first),
                },
                sort_keys=True,
            )
        )
        return 0 if identical else 1

    result = build_result()
    output = write_result_exclusive(args.output, result)
    print(str(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
