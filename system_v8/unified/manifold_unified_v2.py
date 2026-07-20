#!/usr/bin/env python3
"""UNIFIED SIM v2: narrow repair of the v1 tainted evidence paths.

This runner deliberately imports v1's source-composed 64-microstep adaptor and
drop-one ablation functions unchanged.  V2 changes only the invalid coupling,
belief, Julia-referee, and layer-receipt paths identified in AUDIT_VERDICT.md.
It remains a non-promoting scratch diagnostic and records failing controls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from system_v8.nested_manifold import manifold_one as manifold
from system_v8.unified import manifold_unified_v1 as v1

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "manifold_unified_v2"
SIM_INTERPRETER = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
TICKS_DEFAULT = 30
K2_SHUFFLE_SEED = 20260720
K2_SIGNAL_FLOOR = 0.20
K2_SHUFFLE_RATIO = 0.50
DTYPE = v1.DTYPE
RD = v1.RD
I4 = v1.I4

SOURCE_FILES = [
    REPO / "system_v7/constraint_core/MODEL_LAYER_LEDGER.md",
    REPO / "system_v8/nested_manifold/manifold_one.py",
    REPO / "system_v8/nested_manifold/stage64_constraint_tournament.py",
    REPO / "system_v8/unified/manifold_unified_v1.py",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def serial(value: Any) -> Any:
    return v1.serial(value)


def vn_entropy_bits(rho: torch.Tensor) -> float:
    herm = 0.5 * (rho + rho.mH)
    values = torch.clamp(torch.linalg.eigvalsh(herm).real, min=1e-15)
    return float(-torch.sum(values * torch.log2(values)))


def purity(rho: torch.Tensor) -> float:
    return float(torch.trace(rho @ rho).real)


def fixed_quantum_observables(rho: torch.Tensor) -> dict[str, float]:
    """Fixed panel; its definition contains neither drive nor any drive-off run."""
    z_left, z_right, xx, yy = v1.pauli_readout(rho)
    return {
        "purity": purity(rho),
        "von_neumann_entropy_bits": vn_entropy_bits(rho),
        "bloch_z_left": z_left,
        "bloch_z_right": z_right,
        "pauli_xx": xx,
        "pauli_yy": yy,
    }


def nested_cut_readouts(rho: torch.Tensor) -> dict[str, float]:
    """L08 cut panel with a distinct, literal cut-balance label."""
    r = rho.reshape(2, 2, 2, 2)
    # rho[a,i,b,j] has left indices a,b and right indices i,j.
    left = torch.einsum("aibi->ab", r)
    right = torch.einsum("aiaj->ij", r)
    sl, sr, sj = vn_entropy_bits(left), vn_entropy_bits(right), vn_entropy_bits(rho)
    pt = rho.reshape(2, 2, 2, 2).permute(0, 3, 2, 1).reshape(4, 4)
    negativity = float(torch.sum(torch.clamp(-torch.linalg.eigvalsh(0.5 * (pt + pt.mH)).real, min=0.0)))
    return {
        "S_L_bits": sl,
        "S_R_bits": sr,
        "S_LR_bits": sj,
        "mutual_information_bits": sl + sr - sj,
        "negativity": negativity,
        "symmetric_cut_balance_bits": 0.5 * (sl + sr - 2.0 * sj),
    }


def corr(a: list[float], b: list[float]) -> float:
    x, y = torch.tensor(a, dtype=RD), torch.tensor(b, dtype=RD)
    if float(torch.std(x)) < 1e-14 or float(torch.std(y)) < 1e-14:
        return 0.0
    return float(torch.corrcoef(torch.stack((x, y)))[0, 1])


def drive_sequence(ticks: int) -> tuple[list[list[int]], list[float], list[float]]:
    counts = [1, 1, 1, 0, 0]
    rows, drives, quotients = [], [], []
    for tick in range(ticks):
        counts, drive, quotient = v1.packet_drive(counts, tick)
        rows.append(counts[:])
        drives.append(drive)
        quotients.append(quotient)
    return rows, drives, quotients


def hidden_world_bit(counts: list[int]) -> tuple[int, list[int]]:
    """The target is a packet/world bit only, never a quantum readout function."""
    bits = [int(count) & 1 for count in counts]
    target = (bits[0] ^ bits[2] ^ bits[4])
    return target, bits


def fast_slow_world_episode(
    rho: torch.Tensor,
    *,
    counts: list[int],
    frozen: bool = False,
    unmask: bool = False,
    target_override: int | None = None,
) -> dict[str, Any]:
    """View-only belief update against a target fixed from hidden packet bits."""
    sx = torch.tensor(v1.stage64.SX, dtype=DTYPE)
    sz = torch.tensor(v1.stage64.SZ, dtype=DTYPE)
    rotations = [I4, torch.matrix_exp(-0.17j * torch.kron(sz, v1.I2)), torch.matrix_exp(-0.23j * torch.kron(v1.I2, sx))]
    target, world_bits = hidden_world_bit(counts)
    if target_override is not None:
        target = target_override
    candidates = torch.arange(2, dtype=RD)
    posterior = torch.ones(2, dtype=RD) / 2.0
    views = []
    for view_index, unitary in enumerate(rotations):
        rho_fast = unitary @ rho @ unitary.mH
        readout = v1.pauli_readout(rho_fast)
        evidence = 0.0 if frozen else 0.5 * (readout[0] + readout[1])
        expected = torch.cos((candidates + view_index) * math.pi)
        likelihood = torch.exp(-((expected - evidence) ** 2) / 0.18)
        if unmask:
            # Deliberate positive leak sentinel, kept out of the baseline/frozen paths.
            likelihood = likelihood * torch.exp(-0.8 * (candidates - target) ** 2)
        posterior = posterior * likelihood
        posterior = posterior / torch.sum(posterior)
        views.append({"view": view_index, "pauli": readout, "posterior": [float(x) for x in posterior]})
    prediction = int(torch.argmax(posterior).item())
    feature_hash = hashlib.sha256(json.dumps(serial({"views": views, "posterior": posterior}), sort_keys=True).encode()).hexdigest()
    return {
        "target": target,
        "world_packet_bits": world_bits,
        "prediction": prediction,
        "correct": prediction == target,
        "views": views,
        "m_slow": [float(x) for x in posterior],
        "feature_hash": feature_hash,
    }


def rho_complex_pairs(rho: torch.Tensor) -> list[list[list[float]]]:
    return [[[float(value.real), float(value.imag)] for value in row] for row in rho.detach().cpu().tolist()]


def complex_matrix_pairs(matrix: torch.Tensor) -> list[list[list[float]]]:
    return rho_complex_pairs(matrix)


def run_primary(
    ticks: int,
    *,
    applied_drives: list[float],
    flatten: bool = False,
    scramble: bool = False,
    frozen_senses: bool = False,
    ablate_microsteps: bool = False,
) -> dict[str, Any]:
    """One full nested run.  Only applied_drives changes in the shuffled K2 control."""
    packet_counts, world_drives, quotients = drive_sequence(ticks)
    if len(applied_drives) != ticks:
        raise ValueError("applied drive sequence must have one value per tick")
    rho = torch.tensor(manifold.ManifoldState().rho_LR, dtype=DTYPE)
    rho_initial = rho.clone()
    _, outer_np, _ = manifold.build_outer_schur()
    outer = torch.tensor(outer_np, dtype=DTYPE)
    rows, all_deltas, beliefs, julia_trajectory = [], [], [], []
    for tick, (counts, world_drive, quotient, applied_drive) in enumerate(zip(packet_counts, world_drives, quotients, applied_drives)):
        rho_before = rho.clone()
        carrier_health = v1.density_health(rho_before)
        # This is exactly the dynamic v1 quantity that the Julia lane recomputes.
        p1_left = float(torch.real(rho_before.reshape(2, 2, 2, 2).diagonal(dim1=1, dim2=3).sum((0, 1))[1]))
        eta2 = 0.3 + 0.4 * min(max(p1_left, 0.0), 1.0)
        h1 = float(manifold.loop_holonomy(manifold.chi_loop(manifold.ETA1)))
        h2 = float(manifold.loop_holonomy(manifold.chi_loop(eta2)))
        flux = h1 - h2
        plus, minus, kappa = v1.source_stages(applied_drive, flux)
        if scramble:
            plus, minus = list(reversed(plus)), list(reversed(minus))
        matrices, ids = v1.micro_ops(plus, minus)  # v1 path retained unchanged.
        if ablate_microsteps:
            l6_rho, deltas = v1.microstep_ablations(rho_before, matrices, ids)  # v1 path retained unchanged.
            all_deltas.extend([{**item, "tick": tick} for item in deltas])
        else:
            l6_rho, deltas = v1.apply_ops(rho_before, matrices), []
        if flatten:
            rho = l6_rho
            outer_info = {"flattened": True}
        else:
            rho, outer_info = v1.normalize_outer(v1.unvec_f(outer @ v1.vec_f(l6_rho)))
        observables = fixed_quantum_observables(rho)
        belief = fast_slow_world_episode(rho, counts=counts, frozen=frozen_senses)
        beliefs.append(belief)
        julia_trajectory.append({"tick": tick, "rho_before": rho_complex_pairs(rho_before)})
        rows.append({
            "tick": tick,
            "L00_packet": {"counts": counts, "world_capacity_drive": world_drive, "quotient_entropy": quotient},
            "L01_carrier": {"health": carrier_health},
            "L02_flux": {"eta1": manifold.ETA1, "eta2": eta2, "holonomy_eta1": h1, "holonomy_eta2": h2, "flux": flux},
            "L03_weyl": {"W_plus_stage_count": len(plus), "W_minus_stage_count": len(minus)},
            "L04_terrain": {"W_plus": [stage["family"] for stage in plus], "W_minus": [stage["family"] for stage in minus]},
            "L05_operators": {"W_plus": plus, "W_minus": minus, "scrambled_order": scramble},
            "L06_microsteps": {"adaptor": "four_step_repeated_lie_trotter_adaptor", "count": len(ids), "ids": ids, "drop_one_deltas": deltas, "terminal_health": v1.density_health(l6_rho)},
            "L07_axis_readout": {"fixed_observables": observables},
            "L08_nesting": {"L_eff_source": "manifold.build_outer_schur", "flattened": flatten, "outer_corrections": outer_info, "cuts": nested_cut_readouts(rho)},
            "L09_k2": {"world_drive": world_drive, "applied_drive": applied_drive, "kappa": kappa, "observables": observables},
            "L13_learning_proxy": belief,
        })
    return {
        "rows": rows,
        "rho": rho,
        "rho_initial": rho_initial,
        "deltas": all_deltas,
        "beliefs": beliefs,
        "world_drives": world_drives,
        "applied_drives": applied_drives,
        "julia_trajectory": julia_trajectory,
    }


def observable_correlations(run: dict[str, Any]) -> dict[str, float]:
    panel = list(run["rows"][0]["L09_k2"]["observables"])
    return {
        key: corr(run["applied_drives"], [row["L09_k2"]["observables"][key] for row in run["rows"]])
        for key in panel
    }


def k2_summary(baseline: dict[str, Any], shuffled: dict[str, Any], permutation: list[int]) -> dict[str, Any]:
    base_corr = observable_correlations(baseline)
    shuffled_corr = observable_correlations(shuffled)
    aggregate = math.sqrt(sum(value * value for value in base_corr.values()) / len(base_corr))
    shuffled_aggregate = math.sqrt(sum(value * value for value in shuffled_corr.values()) / len(shuffled_corr))
    collapse = aggregate >= K2_SIGNAL_FLOOR and shuffled_aggregate < K2_SHUFFLE_RATIO * aggregate
    if aggregate < K2_SIGNAL_FLOOR:
        status = "negative_low_independent_correlation"
    elif not collapse:
        status = "negative_shuffled_drive_did_not_collapse_correlation"
    else:
        status = "survived_shuffled_drive_control"
    return {
        "status": status,
        "reference_protocol": {
            "initial_state": "manifold.ManifoldState().rho_LR",
            "measurement_time": "end_of_tick_after_live_outer_or_flattened_step",
            "fixed_panel": list(base_corr),
            "no_drive_off_distance": True,
        },
        "baseline_correlations": base_corr,
        "shuffled_correlations": shuffled_corr,
        "baseline_rms_correlation": aggregate,
        "shuffled_rms_correlation": shuffled_aggregate,
        "shuffle_seed": K2_SHUFFLE_SEED,
        "shuffle_permutation": permutation,
        "signal_floor": K2_SIGNAL_FLOOR,
        "required_shuffled_ratio": K2_SHUFFLE_RATIO,
        "shuffle_collapses": collapse,
    }


def apply_superop(superop: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    result = v1.unvec_f(superop @ v1.vec_f(rho))
    return v1.normalize_outer(result)[0]


def macro_channel(stage: dict[str, Any]) -> torch.Tensor:
    matrices = [torch.matrix_exp(v1.MICRO_DT * v1.local_generator(stage, role)) for role in ("D", "H", "D", "H")]
    out = torch.eye(16, dtype=DTYPE)
    for matrix in matrices:
        out = matrix @ out
    return out


def stage_set_for_layer_metrics(reference_row: dict[str, Any]) -> list[dict[str, Any]]:
    return reference_row["L05_operators"]["W_plus"] + reference_row["L05_operators"]["W_minus"]


def terrain_receipt(stages: list[dict[str, Any]]) -> dict[str, Any]:
    """Eight family×sheet GKSL generator rows with computed fixed-point witnesses."""
    representatives = sorted((stage for stage in stages if stage["f"] == 1), key=lambda stage: (stage["family"], stage["sheet"]))
    if len(representatives) != 8:
        raise RuntimeError("L04 requires one f=+1 representative for every family×sheet terrain")
    entries, generators, fixed_points = [], [], []
    for stage in representatives:
        dissipator_super = v1.local_generator(stage, "D")
        hamiltonian_super = v1.local_generator(stage, "H")
        generator = dissipator_super + hamiltonian_super
        local_hamiltonian = stage["source_h_sign"] * stage["omega"] * torch.tensor(v1.stage64.SIG[stage["b"]], dtype=DTYPE)
        local_jump = math.sqrt(stage["gamma"]) * torch.tensor(v1.stage64.JUMP[stage["a"]], dtype=DTYPE)
        if stage["sheet"] == "L":
            hamiltonian = torch.kron(local_hamiltonian, v1.I2)
            lindblad_jump = torch.kron(local_jump, v1.I2)
        else:
            hamiltonian = torch.kron(v1.I2, local_hamiltonian)
            lindblad_jump = torch.kron(v1.I2, local_jump)
        fixed = apply_superop(torch.matrix_exp(80.0 * generator), I4 / 4.0)
        residual = float(torch.linalg.norm(generator @ v1.vec_f(fixed)))
        generators.append(generator)
        fixed_points.append(fixed)
        entries.append({
            "terrain": f"{stage['family']}|{stage['sheet']}",
            "representative_field": stage["f"],
            "dissipator_axis": stage["a"],
            "hamiltonian_axis": stage["b"],
            "hamiltonian_omega": stage["omega"],
            "dissipator_gamma": stage["gamma"],
            "hamiltonian_matrix": complex_matrix_pairs(hamiltonian),
            "lindblad_jump_matrix": complex_matrix_pairs(lindblad_jump),
            "hamiltonian_superoperator_frobenius_norm": float(torch.linalg.norm(hamiltonian_super)),
            "dissipator_superoperator_frobenius_norm": float(torch.linalg.norm(dissipator_super)),
            "gksl_generator_frobenius_norm": float(torch.linalg.norm(generator)),
            "fixed_point_pauli": v1.pauli_readout(fixed),
            "fixed_point_purity": purity(fixed),
            "fixed_point_entropy_bits": vn_entropy_bits(fixed),
            "fixed_point_residual_norm": residual,
            "fixed_point_health": v1.density_health(fixed),
        })
    generator_distances = [float(torch.linalg.norm(generators[i] - generators[j])) for i in range(8) for j in range(i + 1, 8)]
    fixed_distances = [v1.trace_distance(fixed_points[i], fixed_points[j]) for i in range(8) for j in range(i + 1, 8)]
    return {
        "terrain_count": len(entries),
        "terrains": entries,
        "min_pairwise_generator_distance": min(generator_distances),
        "min_pairwise_fixed_point_trace_distance": min(fixed_distances),
        "max_fixed_point_residual_norm": max(item["fixed_point_residual_norm"] for item in entries),
        "local_all_pass": all(item["fixed_point_health"]["physical"] for item in entries),
    }


def stage_fingerprint(stage: dict[str, Any], rho_probe: torch.Tensor) -> dict[str, Any]:
    d = torch.matrix_exp(v1.MICRO_DT * v1.local_generator(stage, "D"))
    h = torch.matrix_exp(v1.MICRO_DT * v1.local_generator(stage, "H"))
    rho_d = apply_superop(d, rho_probe)
    rho_h = apply_superop(h, rho_probe)
    rho_dh = apply_superop(h @ d, rho_probe)
    rho_hd = apply_superop(d @ h, rho_probe)
    rho_dhdh = apply_superop(h @ d @ h @ d, rho_probe)
    rho_hdhd = apply_superop(d @ h @ d @ h, rho_probe)
    initial = torch.tensor(v1.pauli_readout(rho_probe)[:3], dtype=RD)
    d_vec = torch.tensor(v1.pauli_readout(rho_d)[:3], dtype=RD)
    h_vec = torch.tensor(v1.pauli_readout(rho_h)[:3], dtype=RD)
    dh_vec = torch.tensor(v1.pauli_readout(rho_dh)[:3], dtype=RD)
    values = [
        float(torch.dot(d_vec - initial, torch.linalg.cross(h_vec - initial, dh_vec - initial))),
        vn_entropy_bits(rho_d) - vn_entropy_bits(rho_probe),
        v1.pauli_readout(rho_dhdh)[3],
        float(torch.linalg.norm(torch.tensor(v1.pauli_readout(rho_dhdh), dtype=RD) - torch.tensor(v1.pauli_readout(rho_probe), dtype=RD))),
        v1.trace_distance(rho_dhdh, rho_hdhd),
        vn_entropy_bits(rho_h) - vn_entropy_bits(rho_d),
        v1.trace_distance(rho_dh, rho_hd),
    ]
    return {
        "stage": stage["id"],
        "coordinates": {
            "axis0_drive_polarity_signed_volume": values[0],
            "axis1_dissipative_entropy_delta_bits": values[1],
            "axis2_fixed_frame_phase_yy": values[2],
            "axis3_trajectory_motion_l2": values[3],
            "axis4_four_step_loop_order_gap": values[4],
            "axis5_kernel_entropy_split_bits": values[5],
            "axis6_precedence_gap": values[6],
        },
        "vector": values,
    }


def l07_fingerprint(stages: list[dict[str, Any]]) -> dict[str, Any]:
    # Fixed, asymmetric two-sheet probe: a symmetric input would collapse the
    # otherwise distinct left/right stage actions before the seven DOFs are read.
    sx = torch.tensor(v1.stage64.SX, dtype=DTYPE)
    sy = torch.tensor(v1.stage64.SY, dtype=DTYPE)
    sz = torch.tensor(v1.stage64.SZ, dtype=DTYPE)
    left = 0.5 * (v1.I2 + 0.45 * sx + 0.15 * sy - 0.25 * sz)
    right = 0.5 * (v1.I2 - 0.20 * sx + 0.25 * sy + 0.35 * sz)
    rho_probe = torch.kron(left, right)
    fingerprints = [stage_fingerprint(stage, rho_probe) for stage in stages]
    vectors = [torch.tensor(item["vector"], dtype=RD) for item in fingerprints]
    distances = [float(torch.linalg.norm(vectors[i] - vectors[j])) for i in range(len(vectors)) for j in range(i + 1, len(vectors))]
    collisions = [
        [fingerprints[i]["stage"], fingerprints[j]["stage"]]
        for i in range(len(vectors)) for j in range(i + 1, len(vectors))
        if float(torch.linalg.norm(vectors[i] - vectors[j])) <= 1e-10
    ]
    return {
        "fixed_probe": "fixed asymmetric product state: left=(0.45,0.15,-0.25), right=(-0.20,0.25,0.35)",
        "coordinate_count": 7,
        "stage_count": len(fingerprints),
        "fingerprints": fingerprints,
        "unique_count": len(fingerprints) - len(collisions),
        "min_pairwise_distance": min(distances),
        "collision_pairs": collisions,
        "local_all_pass": len(fingerprints) == 16 and not collisions,
    }


def choi_from_superop(superop: torch.Tensor) -> torch.Tensor:
    dim = 4
    choi = torch.zeros((dim * dim, dim * dim), dtype=DTYPE)
    for i in range(dim):
        for j in range(dim):
            basis = torch.zeros((dim, dim), dtype=DTYPE)
            basis[i, j] = 1.0
            output = v1.unvec_f(superop @ v1.vec_f(basis))
            choi[i * dim:(i + 1) * dim, j * dim:(j + 1) * dim] = output
    return 0.5 * (choi + choi.mH)


def information_channels(stages: list[dict[str, Any]]) -> tuple[dict[str, Any], list[torch.Tensor]]:
    rho_probe = torch.tensor(manifold.ManifoldState().rho_LR, dtype=DTYPE)
    records, choi_states, channels = [], [], []
    for stage in stages:
        channel = macro_channel(stage)
        channels.append(channel)
        choi = choi_from_superop(channel)
        normalized_choi = choi / 4.0
        output = sum((normalized_choi[i * 4:(i + 1) * 4, i * 4:(i + 1) * 4] for i in range(4)), torch.zeros((4, 4), dtype=DTYPE))
        output, _ = v1.normalize_outer(output)
        evolved = apply_superop(channel, rho_probe)
        coherent_information = vn_entropy_bits(output) - vn_entropy_bits(normalized_choi)
        choi_states.append(choi)
        records.append({
            "stage": stage["id"],
            "coherent_information_bits": coherent_information,
            "entropy_injection_bits": vn_entropy_bits(evolved) - vn_entropy_bits(rho_probe),
            "choi_min_eigenvalue": float(torch.min(torch.linalg.eigvalsh(choi).real)),
            "channel_output_purity": purity(evolved),
        })
    distances = [float(torch.linalg.norm(choi_states[i] - choi_states[j])) for i in range(len(choi_states)) for j in range(i + 1, len(choi_states))]
    entropy_injections = [item["entropy_injection_bits"] for item in records]
    return {
        "channel_count": len(records),
        "stages": records,
        "min_pairwise_choi_frobenius_distance": min(distances),
        "entropy_injection_range_bits": [min(entropy_injections), max(entropy_injections)],
        "max_coherent_information_bits": max(item["coherent_information_bits"] for item in records),
        "local_all_pass": len(records) == 16 and min(distances) > 1e-10,
    }, channels


def memory_trajectory_substitute(channels: list[torch.Tensor], stages: list[dict[str, Any]], baseline: dict[str, Any]) -> dict[str, Any]:
    zero = torch.zeros((4, 4), dtype=DTYPE)
    one = torch.zeros((4, 4), dtype=DTYPE)
    zero[0, 0] = 1.0
    one[3, 3] = 1.0
    candidates = []
    for stage, channel in zip(stages, channels):
        z, o = zero.clone(), one.clone()
        for _ in range(8):
            z, o = apply_superop(channel, z), apply_superop(channel, o)
        candidates.append((v1.trace_distance(z, o), stage["id"]))
    retention_margin, store_stage = max(candidates)
    return {
        "status": "substituted",
        "substitution_reason": "v2 measures finite state-carrying trajectory retention, not the ledger's projective-Si memory-cell construction.",
        "write_states": ["|00><00|", "|11><11|"],
        "hold_count": 8,
        "best_retention_margin_trace_distance": retention_margin,
        "best_available_store_stage": store_stage,
        "trajectory_tick_count": len(baseline["rows"]),
        "initial_to_terminal_trace_distance": v1.trace_distance(baseline["rho_initial"], baseline["rho"]),
        "local_all_pass": False,
    }


def belief_summary(baseline: dict[str, Any], frozen: dict[str, Any]) -> dict[str, Any]:
    targets = [int(item["target"]) for item in baseline["beliefs"]]
    predictions = [int(item["prediction"]) for item in baseline["beliefs"]]
    frozen_predictions = [int(item["prediction"]) for item in frozen["beliefs"]]
    chance = 0.5
    majority = max(targets.count(0), targets.count(1)) / len(targets)
    accuracy = sum(prediction == target for prediction, target in zip(predictions, targets)) / len(targets)
    frozen_accuracy = sum(prediction == target for prediction, target in zip(frozen_predictions, targets)) / len(targets)
    baseline_beats_majority = accuracy > majority
    frozen_loses_to_majority = frozen_accuracy <= majority
    return {
        "status": "substituted",
        "substitution_reason": "This is a hidden-world prediction measurement, not a stationary free-energy learning or action loop.",
        "target_source": "packet/world parity bits only; excluded from baseline and frozen view likelihoods",
        "target_counts": {"0": targets.count(0), "1": targets.count(1)},
        "baseline": {
            "accuracy": accuracy,
            "chance_accuracy": chance,
            "majority_accuracy": majority,
            "delta_vs_chance": accuracy - chance,
            "delta_vs_majority": accuracy - majority,
        },
        "frozen_senses": {
            "accuracy": frozen_accuracy,
            "chance_accuracy": chance,
            "majority_accuracy": majority,
            "delta_vs_chance": frozen_accuracy - chance,
            "delta_vs_majority": frozen_accuracy - majority,
        },
        "baseline_beats_majority": baseline_beats_majority,
        "frozen_loses_to_same_majority_baseline": frozen_loses_to_majority,
        "frozen_senses_control_flips": baseline_beats_majority and frozen_loses_to_majority,
        "local_all_pass": baseline_beats_majority and frozen_loses_to_majority,
    }


JULIA_REFEREE = r'''using JSON3
using LinearAlgebra

function spinor(eta, phi, chi)
    ComplexF64[exp(im * phi) * cos(eta), exp(im * chi) * sin(eta)]
end

function loop_holonomy_from_links(eta, phi0, n_loop)
    points = [spinor(eta, phi0, 2 * pi * k / n_loop) for k in 0:(n_loop - 1)]
    sum(angle(dot(points[k], points[k == n_loop ? 1 : k + 1])) for k in 1:n_loop)
end

payload = JSON3.read(read(ARGS[1], String))
protocol = payload["protocol"]
eta1 = Float64(protocol["eta1"])
phi0 = Float64(protocol["phi0"])
n_loop = Int(protocol["n_loop"])
rows = Any[]
for item in payload["ticks"]
    encoded = item["rho_before"]
    rho = Matrix{ComplexF64}(undef, 4, 4)
    for i in 1:4, j in 1:4
        rho[i, j] = ComplexF64(Float64(encoded[i][j][1]), Float64(encoded[i][j][2]))
    end
    # Literal equivalent of v1's reshape(...).diagonal(...).sum(...)[1].
    p1_left = real(sum(rho[2 * a + 2, 2 * c + 2] for a in 0:1, c in 0:1))
    eta2 = 0.3 + 0.4 * clamp(p1_left, 0.0, 1.0)
    h1 = loop_holonomy_from_links(eta1, phi0, n_loop)
    h2 = loop_holonomy_from_links(eta2, phi0, n_loop)
    push!(rows, Dict("tick" => Int(item["tick"]), "eta2" => eta2,
                     "holonomy_eta1" => h1, "holonomy_eta2" => h2,
                     "flux" => h1 - h2))
end
println(JSON3.write(Dict("ticks" => rows)))
'''


def run_julia_referee(baseline: dict[str, Any], artifact_dir: Path) -> dict[str, Any]:
    input_path = artifact_dir / "julia_holonomy_trajectory.json"
    script_path = artifact_dir / "julia_holonomy_referee.jl"
    input_payload = {
        "protocol": {"eta1": manifold.ETA1, "phi0": 0.3, "n_loop": manifold.N_LOOP},
        "ticks": baseline["julia_trajectory"],
    }
    input_path.write_text(json.dumps(serial(input_payload), indent=2, allow_nan=False) + "\n")
    script_path.write_text(JULIA_REFEREE)
    def artifact_reference(path: Path) -> str:
        try:
            return str(path.relative_to(REPO))
        except ValueError:
            return str(path)
    command = ["/opt/homebrew/bin/julia", "--startup-file=no", "--project=" + str(REPO / "system_v5/julia_carrier"), str(script_path), str(input_path)]
    completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=120)
    try:
        payload = json.loads(completed.stdout)
        rows = payload["ticks"]
        comparisons = []
        for py_row, julia_row in zip(baseline["rows"], rows):
            if py_row["tick"] != julia_row["tick"]:
                raise ValueError("Julia trajectory ticks are not contiguous/aligned")
            comparisons.append(abs(py_row["L02_flux"]["flux"] - float(julia_row["flux"])))
        max_difference = max(comparisons) if comparisons else math.inf
        matches = completed.returncode == 0 and len(rows) == len(baseline["rows"]) and max_difference < 1e-10
        return {
            "ran": completed.returncode == 0,
            "trajectory_input": artifact_reference(input_path),
            "referee_script": artifact_reference(script_path),
            "tick_count": len(rows),
            "per_tick": rows,
            "max_abs_difference": max_difference,
            "matches_dynamical_holonomy": matches,
            "stderr": completed.stderr[-2000:],
        }
    except Exception as exc:
        return {
            "ran": False,
            "trajectory_input": artifact_reference(input_path),
            "referee_script": artifact_reference(script_path),
            "error": f"{type(exc).__name__}: {exc}",
            "stdout": completed.stdout[-2000:],
            "stderr": completed.stderr[-2000:],
            "matches_dynamical_holonomy": False,
        }


def layer_receipt(index: int, unified: dict[str, Any], status: str, computed: dict[str, Any], reason: str | None = None) -> dict[str, Any]:
    receipt = {
        "name": f"manifold_unified_v2_layer_{index:02d}",
        "schema": "ratchet.v8.unified.manifold_unified_v2.layer.v2",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "generated_at": unified["generated_at"],
        "layer_status": status,
        "computed": computed,
        "all_pass": bool(computed.get("local_all_pass", False)) if status == "executed" else False,
        "claim_ceiling": "bounded v2 source-composed scratch layer only",
    }
    if reason is not None:
        receipt["reason"] = reason
    return receipt


def write_receipts(unified: dict[str, Any], layer_data: dict[int, tuple[str, dict[str, Any], str | None]], *, refresh: bool) -> None:
    (OUT / "receipt.json").write_text(json.dumps(serial(unified), indent=2, allow_nan=False) + "\n")
    for index in range(18):
        status, computed, reason = layer_data[index]
        folder = OUT / "layers" / f"L{index:02d}"
        folder.mkdir(parents=True, exist_ok=refresh)
        (folder / "receipt.json").write_text(json.dumps(serial(layer_receipt(index, unified, status, computed, reason)), indent=2, allow_nan=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticks", type=int, default=TICKS_DEFAULT)
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--refresh", action="store_true", help="replace only v2-generated result files after a corrected rerun")
    args = parser.parse_args()
    if args.ticks < 30:
        raise SystemExit("unified v2 requires at least 30 ticks")

    free_memory = v1.senses_source.memory_free_percent()
    if free_memory <= 25:
        raise SystemExit(f"memory gate failed: free={free_memory}% <= 25%")
    _, base_drives, _ = drive_sequence(args.ticks)
    permutation = list(range(args.ticks))
    random.Random(K2_SHUFFLE_SEED).shuffle(permutation)
    shuffled_drives = [base_drives[index] for index in permutation]

    baseline = run_primary(args.ticks, applied_drives=base_drives, ablate_microsteps=True)
    shuffled = run_primary(args.ticks, applied_drives=shuffled_drives)
    flattened = run_primary(args.ticks, applied_drives=base_drives, flatten=True)
    scrambled = run_primary(args.ticks, applied_drives=base_drives, scramble=True)
    frozen = run_primary(args.ticks, applied_drives=base_drives, frozen_senses=True)

    k2 = k2_summary(baseline, shuffled, permutation)
    l04 = terrain_receipt(stage_set_for_layer_metrics(baseline["rows"][0]))
    l07 = l07_fingerprint(stage_set_for_layer_metrics(baseline["rows"][0]))
    l11, channels = information_channels(stage_set_for_layer_metrics(baseline["rows"][0]))
    l12 = memory_trajectory_substitute(channels, stage_set_for_layer_metrics(baseline["rows"][0]), baseline)
    l13 = belief_summary(baseline, frozen)
    endpoint_flat = v1.trace_distance(baseline["rho"], flattened["rho"])
    endpoint_scramble = v1.trace_distance(baseline["rho"], scrambled["rho"])

    if args.no_write:
        with tempfile.TemporaryDirectory(prefix="manifold_unified_v2_") as temp:
            referee = run_julia_referee(baseline, Path(temp))
    else:
        OUT.mkdir(parents=True, exist_ok=args.refresh)
        referee = run_julia_referee(baseline, OUT)

    all_deltas = baseline["deltas"]
    checks = {
        "tick_count_at_least_30": len(baseline["rows"]) >= 30,
        "l6_64_microsteps_each_tick": all(row["L06_microsteps"]["count"] == 64 and len(row["L06_microsteps"]["drop_one_deltas"]) == 64 for row in baseline["rows"]),
        "l6_all_drop_one_measurable": all(item["measurable"] for item in all_deltas),
        "flattened_nesting_flips": endpoint_flat > v1.DELTA_THRESHOLD,
        "scrambled_stage_order_flips": endpoint_scramble > v1.DELTA_THRESHOLD,
        "k2_shuffled_drive_collapses_independent_observables": bool(k2["shuffle_collapses"]),
        "belief_beats_chance_and_majority": bool(l13["baseline_beats_majority"]),
        "frozen_senses_flips_against_same_majority_baseline": bool(l13["frozen_senses_control_flips"]),
        "l04_fixed_points_physical": bool(l04["local_all_pass"]),
        "l07_16_stage_7dof_noncollapse": bool(l07["local_all_pass"]),
        "l11_16_information_channels_distinct": bool(l11["local_all_pass"]),
        "julia_dynamical_holonomy_agreement": bool(referee.get("matches_dynamical_holonomy")),
    }
    leak_base = fast_slow_world_episode(baseline["rho"], counts=baseline["rows"][-1]["L00_packet"]["counts"])
    leak_flip = fast_slow_world_episode(baseline["rho"], counts=baseline["rows"][-1]["L00_packet"]["counts"], target_override=1 - leak_base["target"])
    leak_positive = fast_slow_world_episode(baseline["rho"], counts=baseline["rows"][-1]["L00_packet"]["counts"], unmask=True)
    checks["belief_target_flip_does_not_change_features"] = leak_base["feature_hash"] == leak_flip["feature_hash"]
    checks["belief_positive_leak_sentinel_changes_features"] = leak_base["feature_hash"] != leak_positive["feature_hash"]

    l08 = {
        "baseline_terminal_cuts": baseline["rows"][-1]["L08_nesting"]["cuts"],
        "flattened_terminal_cuts": flattened["rows"][-1]["L08_nesting"]["cuts"],
        "endpoint_trace_distance_from_flattened": endpoint_flat,
        "local_all_pass": endpoint_flat > v1.DELTA_THRESHOLD,
    }
    l09 = {**k2, "local_all_pass": bool(k2["shuffle_collapses"])}
    layer_data: dict[int, tuple[str, dict[str, Any], str | None]] = {
        0: ("executed", {"tick_count": len(baseline["rows"]), "drive_min": min(base_drives), "drive_max": max(base_drives), "local_all_pass": True}, None),
        1: ("executed", {"terminal_health": v1.density_health(baseline["rho"]), "local_all_pass": v1.density_health(baseline["rho"])["physical"]}, None),
        2: ("executed", {"terminal_flux": baseline["rows"][-1]["L02_flux"]["flux"], "flux_min": min(row["L02_flux"]["flux"] for row in baseline["rows"]), "flux_max": max(row["L02_flux"]["flux"] for row in baseline["rows"]), "local_all_pass": True}, None),
        3: ("executed", {"W_plus_stage_count": 8, "W_minus_stage_count": 8, "local_all_pass": True}, None),
        4: ("executed", l04, None),
        5: ("executed", {"macro_stage_count": 16, "source_selected_operator_axes": sorted({f"{stage['a']}|{stage['b']}" for stage in stage_set_for_layer_metrics(baseline["rows"][0])}), "local_all_pass": True}, None),
        6: ("executed", {"drop_one_count": len(all_deltas), "min_delta_trace": min(item["delta_trace"] for item in all_deltas), "max_delta_trace": max(item["delta_trace"] for item in all_deltas), "local_all_pass": all(item["measurable"] for item in all_deltas)}, None),
        7: ("executed", l07, None),
        8: ("executed", l08, None),
        9: ("executed", l09, None),
        10: ("not_executed", {}, "The ledger's aligned multi-substrate engine computation was not run; the Julia trajectory referee is not substituted for it."),
        11: ("executed", l11, None),
        12: ("substituted", l12, l12["substitution_reason"]),
        13: ("substituted", l13, l13["substitution_reason"]),
        14: ("not_executed", {"executed_operations": 0}, "No L14 computation is in the v2 repair scope."),
        15: ("not_executed", {"executed_operations": 0}, "No L15 computation is in the v2 repair scope."),
        16: ("not_executed", {"executed_operations": 0}, "No L16 computation is in the v2 repair scope."),
        17: ("not_executed", {"executed_operations": 0}, "No L17 computation is in the v2 repair scope."),
    }
    unified = {
        "name": "manifold_unified_v2",
        "schema": "ratchet.v8.unified.manifold_unified_v2.v2",
        "generated_at": iso_now(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "accepted_status_label": "passes local rerun" if all(checks.values()) else "runs_with_honest_negative_or_open_control",
        "claim_ceiling": "finite source-composed scratch diagnostic; no official, canonical, scientific, admission, or promotion claim.",
        "runtime": {"interpreter": SIM_INTERPRETER, "resolved_interpreter": sys.executable, "torch": torch.__version__, "memory_free_percent": free_memory},
        "composition_provenance": {str(path.relative_to(REPO)): sha(path) for path in SOURCE_FILES},
        "v1_preserved_path": {"micro_ops": "imported unchanged", "microstep_ablations": "imported unchanged", "drop_one_count": len(all_deltas)},
        "tool_manifest": {
            "pytorch": {"tried": True, "used": True, "reason": "Primary density evolution, controls, channel calculations, and drop-one ablations."},
            "julia": {"tried": True, "used": bool(referee.get("ran")), "reason": "Independent link-by-link recomputation of exported dynamical holonomy trajectories."},
        },
        "tool_integration_depth": {"pytorch": "load_bearing", "julia": "supportive"},
        "checks": checks,
        "all_pass": bool(all(checks.values())),
        "tick_chain": baseline["rows"],
        "controls": {
            "shuffled_drive": l09,
            "flattened_nesting": {"endpoint_trace_distance": endpoint_flat},
            "scrambled_stage_order": {"endpoint_trace_distance": endpoint_scramble},
            "frozen_senses": l13["frozen_senses"],
        },
        "layer_computations": {f"L{index:02d}": data[1] for index, data in layer_data.items()},
        "l6_drop_one_summary": {"count": len(all_deltas), "min_delta_trace": min(item["delta_trace"] for item in all_deltas), "max_delta_trace": max(item["delta_trace"] for item in all_deltas), "all_measurable": all(item["measurable"] for item in all_deltas)},
        "belief_leak_checks": {"target_flip_same_hash": leak_base["feature_hash"] == leak_flip["feature_hash"], "positive_unmask_changes_hash": leak_base["feature_hash"] != leak_positive["feature_hash"]},
        "referee_spot_checks": {"julia_dynamical_holonomy": referee},
        "findings": [
            "K2 uses only correlations between the applied packet-drive sequence and a predeclared fixed panel of evolving-state observables.",
            "The belief target is derived only from packet/world bits and is scored against chance and the majority-class baseline.",
            "L10 remains not_executed; L12 and L13 state their substituted, incomplete ledger coverage explicitly.",
        ],
    }
    if not args.no_write:
        write_receipts(unified, layer_data, refresh=args.refresh)
    print(json.dumps(serial({"out": OUT, "all_pass": unified["all_pass"], "checks": checks, "k2": {"status": k2["status"], "baseline_rms_correlation": k2["baseline_rms_correlation"], "shuffled_rms_correlation": k2["shuffled_rms_correlation"]}, "belief": l13, "julia": referee, "wrote": not args.no_write}), indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
