#!/usr/bin/env python3
"""ENTANGLEMENT PAWL v0 — bounded three-qubit resource-retention search.

This file is deliberately a finite diagnostic.  It keeps the prior
three-qubit nested-cut object literal: rho_ABC is evolved by an RK4 GKSL
integrator, S(A|B) is recomputed from rho only for q0|q12 and q01|q2, and
I(A>B) is exactly -S(A|B).  The imported nested-manifold drive affects the
trajectory *only* by selecting Hamiltonian and Lindblad-generator
coefficients.  It is never an argument of an entropy, coherent-information,
or observable-panel function.

PREREGISTERED PASS CRITERIA (fixed in this header before the sweep):

  R1  The no-pawl source-schedule baseline has no longest negative run above
      three end-of-tick samples on either declared cut (the prior receipt has
      cut1 negative at ticks 0,1,2 and cut2 at tick 0 only).
  R2  The local-only product control has S(A|B) >= -1e-10 and I(A>B) <= 1e-9
      on both cuts at every tick.
  R3  Every tested pawl configuration, with the entangling Hamiltonian removed,
      leaves the declared diagonal classical mixture nonnegative on both cuts.
  R4  A candidate sustains only if one fixed cut has at least
      SUSTAINED_TICKS=10 consecutive samples S(A|B) < -1e-6.  The result also
      records the fraction negative, minimum, and longest run for both cuts.
  R5  Drive-to-dI correlations are post-hoc reports.  The fixed-seed shuffled
      drive rerun must reduce |r|, unless both values are below 0.20; an honest
      non-collapse remains a failure rather than a tuning target.
  R6  QuTiP independently recomputes both conditional entropies from saved
      selected-candidate density states at predeclared ticks 5, 15, and 25;
      its maximum absolute discrepancy must be <= 1e-10.
  R7  The density stays trace-one, Hermitian, and positive within numerical
      tolerance.  The chamber-wall candidate additionally cannot pass if its
      dissipative gate was trivially off on every tick.

Candidate sweep families (all are executed across every stage schedule):
  1. a collective, commuting-jump retention stroke in the XY commutant;
  2. duty-cycle drive pumping of the XY generator;
  3. spectral chamber-wall dissipation gating; and
  4. non-postselected weak stabilizer measurement plus local feedback.

The source vocabulary, timing, GKSL form, and drive series are imported from
system_v8/nested_manifold/manifold_one.py.  For stability on high-drive and
zero-dissipation rows, this runner exponentiates that finite GKSL Liouvillian
instead of treating eight RK4 substeps as a positivity certificate.  The fixed observable panel is
called from manifold_unified_v2 on rho_q0q1 without modification.  Result
ceiling: scratch_diagnostic; promotion_allowed=false; no admission, canonical,
hardware, fault-tolerance, or scientific claim.  The default output refuses
reuse.  No files are deleted, moved, staged, or committed.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import psutil
import torch

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from system_v8.nested_manifold import manifold_one as mf
from system_v8.unified import manifold_unified_v2 as unified_v2


SIM_INTERPRETER = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
OUT_DEFAULT = Path(__file__).resolve().parent / "results" / "pawl_v0"
TICKS = mf.N_TICKS
SUSTAINED_TICKS = 10
NEGATIVE_EPS = 1e-6
PHYSICAL_EPS = 1e-8
MIN_FREE_GIB = 2.0  # Bounded 8x8 sweep: absolute capacity is the relevant guard.
DISSIPATION_SCALE = 0.20  # inherited calibrated scale from the prior ladder.
J_COUPLE = 2.0  # inherited calibrated entangling strength; mf.J_XY=0.35 failed.
SHUFFLE_SEED = 20260719
SPOT_TICKS = (5, 15, 25)
RETENTION_FRACTION = 0.35
FEEDBACK_ANGLE = 0.15
CDTYPE = torch.complex128
RDTYPE = torch.float64

# Imported rather than numerically retyped.  These objects are embedded below.
I2 = torch.tensor(mf.I2, dtype=CDTYPE)
SX = torch.tensor(mf.SX, dtype=CDTYPE)
SY = torch.tensor(mf.SY, dtype=CDTYPE)
SZ = torch.tensor(mf.SZ, dtype=CDTYPE)
SM = torch.tensor(mf.SM, dtype=CDTYPE)
I8 = torch.eye(8, dtype=CDTYPE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def as_json(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return as_json(value.detach().cpu().tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): as_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_json(item) for item in value]
    return value


def kron3(a: torch.Tensor, b: torch.Tensor, c: torch.Tensor) -> torch.Tensor:
    return torch.kron(torch.kron(a, b), c)


def embed1(op: torch.Tensor, position: int) -> torch.Tensor:
    mats = [I2, I2, I2]
    mats[position] = op
    return kron3(*mats)


def embed2(op_left: torch.Tensor, op_right: torch.Tensor, left: int, right: int) -> torch.Tensor:
    if left >= right:
        raise ValueError("two-qubit embedding requires left < right")
    mats = [I2, I2, I2]
    mats[left] = op_left
    mats[right] = op_right
    return kron3(*mats)


def local_hamiltonian() -> torch.Tensor:
    h1 = 0.5 * mf.OMEGA * (math.sin(mf.ALPHA) * SX + math.cos(mf.ALPHA) * SZ)
    return sum((embed1(h1, qubit) for qubit in range(3)), torch.zeros((8, 8), dtype=CDTYPE))


def xy_coupling_operator() -> torch.Tensor:
    """The 01 plus 12 XY chain; its scale is supplied by a generator only."""
    return (
        embed2(SX, SX, 0, 1) + embed2(SY, SY, 0, 1)
        + embed2(SX, SX, 1, 2) + embed2(SY, SY, 1, 2)
    )


H_LOCAL = local_hamiltonian()
H_XY = xy_coupling_operator()
Z_TOTAL = embed1(SZ, 0) + embed1(SZ, 1) + embed1(SZ, 2)
STABILIZER_ZZ = embed2(SZ, SZ, 0, 1)
FEEDBACK_X2 = embed1(SX, 2)


def bank_jumps_3q(stage: int, gamma: float) -> list[torch.Tensor]:
    """Imported manifold stage *types* re-embedded as three-qubit local jumps."""
    if gamma <= 0.0:
        return []
    if stage == 0:  # G1 depolarizing
        return [math.sqrt(gamma / 4.0) * embed1(op, qubit) for qubit in range(3) for op in (SX, SY, SZ)]
    if stage == 1:  # G7 pinching GKSL limit
        return [math.sqrt(gamma) * embed1(SZ, qubit) for qubit in range(3)]
    return [math.sqrt(gamma) * embed1(SM, qubit) for qubit in range(3)]  # G3 damping


def normalise_hermitian(rho: torch.Tensor) -> torch.Tensor:
    rho = 0.5 * (rho + rho.mH)
    trace = torch.trace(rho)
    if abs(complex(trace.item())) < 1e-14:
        raise RuntimeError("GKSL evolution returned an effectively zero-trace state")
    return rho / trace


def gksl_liouvillian(hamiltonian: torch.Tensor, jumps: list[torch.Tensor]) -> torch.Tensor:
    """Column-vectorized exact finite form of manifold_one.gksl_rhs."""
    dimension = hamiltonian.shape[0]
    identity = torch.eye(dimension, dtype=CDTYPE)
    generator = -1j * (torch.kron(identity, hamiltonian) - torch.kron(hamiltonian.T.contiguous(), identity))
    for jump in jumps:
        jump_dag_jump = jump.mH @ jump
        generator = generator + (
            torch.kron(jump.conj(), jump)
            - 0.5 * torch.kron(identity, jump_dag_jump)
            - 0.5 * torch.kron(jump_dag_jump.T.contiguous(), identity)
        )
    return generator


def evolve_gksl(rho: torch.Tensor, hamiltonian: torch.Tensor, jumps: list[torch.Tensor], duration: float) -> torch.Tensor:
    """Exact CPTP step for the source GKSL RHS; avoids false negative eigenvalues."""
    generator = gksl_liouvillian(hamiltonian, jumps)
    propagator = torch.matrix_exp(duration * generator)
    vec_f = rho.T.reshape(-1)
    output = (propagator @ vec_f).reshape(rho.shape).T
    return normalise_hermitian(output)


def ptrace_out0(rho: torch.Tensor) -> torch.Tensor:
    tensor = rho.reshape(2, 2, 2, 2, 2, 2)
    return torch.einsum("ijkilm->jklm", tensor).reshape(4, 4)


def ptrace_out2(rho: torch.Tensor) -> torch.Tensor:
    tensor = rho.reshape(2, 2, 2, 2, 2, 2)
    return torch.einsum("ijklmk->ijlm", tensor).reshape(4, 4)


def ptrace_keep2(rho: torch.Tensor) -> torch.Tensor:
    tensor = rho.reshape(2, 2, 2, 2, 2, 2)
    return torch.einsum("ijkijl->kl", tensor).reshape(2, 2)


def vn_entropy_bits(rho: torch.Tensor) -> float:
    values = torch.linalg.eigvalsh(0.5 * (rho + rho.mH)).real
    values = values[values > 1e-14]
    if values.numel() == 0:
        return 0.0
    return float(-(values * torch.log2(values)).sum())


def cut_readouts(rho: torch.Tensor) -> dict[str, float]:
    """State-only resource panel.  Drive is intentionally not an argument."""
    s_abc = vn_entropy_bits(rho)
    s_bc = vn_entropy_bits(ptrace_out0(rho))
    s_c = vn_entropy_bits(ptrace_keep2(rho))
    sab1, sab2 = s_abc - s_bc, s_abc - s_c
    return {
        "S_ABC_bits": s_abc,
        "S_BC_bits": s_bc,
        "S_C_bits": s_c,
        "cut1_SAB": sab1,
        "cut1_I": -sab1,
        "cut2_SAB": sab2,
        "cut2_I": -sab2,
    }


def density_health(rho: torch.Tensor) -> dict[str, float | bool]:
    hermiticity = float(torch.max(torch.abs(rho - rho.mH)))
    trace_error = abs(complex(torch.trace(rho).item()) - 1.0)
    minimum_eigenvalue = float(torch.min(torch.linalg.eigvalsh(0.5 * (rho + rho.mH)).real))
    return {
        "trace_error": float(trace_error),
        "hermiticity_error": hermiticity,
        "min_eigenvalue": minimum_eigenvalue,
        "physical": bool(trace_error <= PHYSICAL_EPS and hermiticity <= PHYSICAL_EPS and minimum_eigenvalue >= -PHYSICAL_EPS),
    }


def min_adjacent_eigenvalue_gap(rho_ab: torch.Tensor) -> float:
    values = torch.sort(torch.linalg.eigvalsh(0.5 * (rho_ab + rho_ab.mH)).real).values
    return float(torch.min(values[1:] - values[:-1]))


def initial_product_state() -> torch.Tensor:
    # The same pure Bloch direction used by the prior 3q ladder control.
    bloch = torch.tensor([0.5, 0.3, -0.4], dtype=RDTYPE)
    bloch = bloch / torch.linalg.norm(bloch)
    rho1 = 0.5 * (I2 + bloch[0] * SX + bloch[1] * SY + bloch[2] * SZ)
    return kron3(rho1, rho1, rho1)


def initial_classical_mixture() -> torch.Tensor:
    ket000 = torch.zeros(8, dtype=CDTYPE)
    ket111 = torch.zeros(8, dtype=CDTYPE)
    ket000[0], ket111[7] = 1.0, 1.0
    return 0.5 * (torch.outer(ket000, ket000.conj()) + torch.outer(ket111, ket111.conj()))


def imported_drive_series() -> tuple[list[float], list[float]]:
    """The packet-growth drive is generated by mf.tick, not re-derived here."""
    state = mf.ManifoldState()
    capacities, generator_gammas = [], []
    for tick in range(TICKS):
        row = mf.tick(state, tick)
        capacities.append(float(row["dC"]))
        generator_gammas.append(float(row["gamma"]))
    return capacities, generator_gammas


def stage_schedules() -> dict[str, list[int]]:
    return {
        "source_012": [tick // 10 for tick in range(TICKS)],
        "interleaved_012": [tick % 3 for tick in range(TICKS)],
        "dephase_first_102": [1 if tick < 10 else (0 if tick < 20 else 2) for tick in range(TICKS)],
    }


def candidate_specs() -> dict[str, list[dict[str, Any]]]:
    schedules = stage_schedules()
    specs: dict[str, list[dict[str, Any]]] = {name: [] for name in ("dfs_commutant", "drive_duty", "chamber_wall", "weak_feedback")}
    for schedule_name in schedules:
        for rate in (0.15, 0.45, 0.90):
            specs["dfs_commutant"].append({"kind": "dfs_commutant", "schedule": schedule_name, "retention_rate": rate})
        for duty in (0.25, 0.50, 0.75, 1.00):
            specs["drive_duty"].append({"kind": "drive_duty", "schedule": schedule_name, "duty_cycle": duty})
        for threshold in (0.0, 0.002, 0.01, 0.03, 0.08):
            specs["chamber_wall"].append({"kind": "chamber_wall", "schedule": schedule_name, "gap_threshold": threshold})
        for interval in (2, 3):
            for strength in (0.10, 0.30):
                specs["weak_feedback"].append({"kind": "weak_feedback", "schedule": schedule_name, "measurement_interval": interval, "measurement_strength": strength})
    return specs


def generator_from_drive(
    *,
    tick: int,
    source_gamma: float,
    stage: int,
    config: dict[str, Any],
    entangling: bool,
    max_source_gamma: float,
    pre_stroke_gap: float,
) -> tuple[torch.Tensor, list[torch.Tensor], dict[str, Any]]:
    """The only place source_gamma/drive reaches the dynamics is H or Ls."""
    coupling_scale = 1.0
    if config["kind"] == "drive_duty":
        active_ticks = max(1, round(4 * float(config["duty_cycle"])))
        duty_open = (tick % 4) < active_ticks
        normalized_drive = source_gamma / max_source_gamma if max_source_gamma > 0.0 else 0.0
        coupling_scale = 1.0 + (2.0 * normalized_drive if duty_open else 0.0)
    hamiltonian = H_LOCAL + (J_COUPLE * coupling_scale * H_XY if entangling else torch.zeros((8, 8), dtype=CDTYPE))
    dissipative_enabled = True
    if config["kind"] == "chamber_wall":
        dissipative_enabled = not (pre_stroke_gap < float(config["gap_threshold"]))
        if bool(config.get("force_dissipation_off", False)):
            dissipative_enabled = False
    local_rate = source_gamma * DISSIPATION_SCALE if dissipative_enabled else 0.0
    jumps = bank_jumps_3q(stage, local_rate)
    return hamiltonian, jumps, {
        "source_gamma": source_gamma,
        "stage": stage,
        "coupling_scale": coupling_scale if entangling else 0.0,
        "dissipative_enabled": dissipative_enabled,
        "local_jump_rate": local_rate,
        "pre_stroke_rho_q01_min_gap": pre_stroke_gap,
    }


def weak_measurement_feedback(rho: torch.Tensor, strength: float) -> tuple[torch.Tensor, dict[str, float | bool]]:
    """Non-postselected two-outcome parity measurement and declared local feedback."""
    if not 0.0 < strength < 1.0:
        raise ValueError("weak-measurement strength must lie strictly between zero and one")
    p_plus, p_minus = 0.5 * (I8 + STABILIZER_ZZ), 0.5 * (I8 - STABILIZER_ZZ)
    m_plus = math.sqrt((1.0 + strength) / 2.0) * p_plus + math.sqrt((1.0 - strength) / 2.0) * p_minus
    m_minus = math.sqrt((1.0 - strength) / 2.0) * p_plus + math.sqrt((1.0 + strength) / 2.0) * p_minus
    u_plus = I8
    u_minus = torch.matrix_exp(-1j * FEEDBACK_ANGLE * FEEDBACK_X2)
    plus_branch = u_plus @ m_plus @ rho @ m_plus.mH @ u_plus.mH
    minus_branch = u_minus @ m_minus @ rho @ m_minus.mH @ u_minus.mH
    output = normalise_hermitian(plus_branch + minus_branch)
    completeness = torch.linalg.norm(m_plus.mH @ m_plus + m_minus.mH @ m_minus - I8)
    return output, {
        "measurement_applied": True,
        "p_plus": float(torch.trace(plus_branch).real),
        "p_minus": float(torch.trace(minus_branch).real),
        "kraus_completeness_frobenius": float(completeness),
        "postselection_used": False,
    }


def apply_retention_stroke(rho: torch.Tensor, tick: int, config: dict[str, Any]) -> tuple[torch.Tensor, dict[str, Any]]:
    kind = config["kind"]
    if kind == "dfs_commutant":
        rate = float(config["retention_rate"])
        jump = math.sqrt(rate) * Z_TOTAL
        output = evolve_gksl(rho, torch.zeros((8, 8), dtype=CDTYPE), [jump], mf.TICK_DT * RETENTION_FRACTION)
        commutator = torch.linalg.norm(Z_TOTAL @ H_XY - H_XY @ Z_TOTAL)
        return output, {
            "stroke": "collective_Z_total_commutant_jump",
            "retention_rate": rate,
            "commutator_frobenius": float(commutator),
            "duration": mf.TICK_DT * RETENTION_FRACTION,
        }
    if kind == "weak_feedback" and tick % int(config["measurement_interval"]) == 0:
        output, record = weak_measurement_feedback(rho, float(config["measurement_strength"]))
        return output, {"stroke": "weak_Z0Z1_measurement_local_X2_feedback", **record}
    if kind == "weak_feedback":
        return rho, {"stroke": "weak_feedback_not_scheduled", "measurement_applied": False, "postselection_used": False}
    return rho, {"stroke": "none"}


def run_variant(
    *,
    config: dict[str, Any],
    applied_gammas: list[float],
    entangling: bool,
    initial_kind: str,
    keep_snapshots: bool = False,
) -> dict[str, Any]:
    if len(applied_gammas) != TICKS:
        raise ValueError("one imported or shuffled source gamma is required for each tick")
    if initial_kind == "product":
        rho = initial_product_state()
    elif initial_kind == "classical_mixture":
        rho = initial_classical_mixture()
    else:
        raise ValueError(f"unsupported initial kind: {initial_kind}")
    schedule = stage_schedules()[str(config["schedule"])]
    rows, snapshots = [], []
    initial_readouts = cut_readouts(rho)
    max_source_gamma = max(applied_gammas)
    for tick, source_gamma in enumerate(applied_gammas):
        rho_q01_before = ptrace_out2(rho)
        gap = min_adjacent_eigenvalue_gap(rho_q01_before)
        hamiltonian, jumps, generator_record = generator_from_drive(
            tick=tick,
            source_gamma=source_gamma,
            stage=schedule[tick],
            config=config,
            entangling=entangling,
            max_source_gamma=max_source_gamma,
            pre_stroke_gap=gap,
        )
        rho = evolve_gksl(rho, hamiltonian, jumps, mf.TICK_DT)
        rho, stroke_record = apply_retention_stroke(rho, tick, config)
        cut = cut_readouts(rho)
        # Exact unified-v2 panel, applied to the named q0q1 reduced state.
        fixed_panel = unified_v2.fixed_quantum_observables(ptrace_out2(rho))
        health = density_health(rho)
        rows.append({
            "tick": tick,
            "generator": generator_record,
            "retention_stroke": stroke_record,
            "cuts": cut,
            "fixed_observable_panel_rho_q01": fixed_panel,
            "density_health": health,
        })
        if keep_snapshots:
            snapshots.append(rho.clone())
    return {
        "config": dict(config),
        "initial_kind": initial_kind,
        "entangling_hamiltonian_enabled": entangling,
        "applied_gammas": list(applied_gammas),
        "initial_cuts": initial_readouts,
        "rows": rows,
        "snapshots": snapshots,
    }


def longest_true_run(mask: list[bool]) -> int:
    longest = current = 0
    for value in mask:
        current = current + 1 if value else 0
        longest = max(longest, current)
    return longest


def pearson(left: list[float], right: list[float]) -> float:
    a, b = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    if a.std() < 1e-15 or b.std() < 1e-15:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def metrics_for_run(run: dict[str, Any], *, include_panel_series: bool = False) -> dict[str, Any]:
    rows = run["rows"]
    cuts: dict[str, dict[str, Any]] = {}
    for cut in ("cut1", "cut2"):
        sab = [float(row["cuts"][f"{cut}_SAB"]) for row in rows]
        coherent = [float(row["cuts"][f"{cut}_I"]) for row in rows]
        negative = [value < -NEGATIVE_EPS for value in sab]
        cuts[cut] = {
            "negative_fraction": sum(negative) / len(negative),
            "min_SAB": min(sab),
            "minimum_tick": sab.index(min(sab)),
            "sustained_run_length": longest_true_run(negative),
            "SAB_series": sab,
            "I_series": coherent,
        }
    selected_cut = max(("cut1", "cut2"), key=lambda cut: (cuts[cut]["sustained_run_length"], cuts[cut]["negative_fraction"], -cuts[cut]["min_SAB"]))
    initial_i = float(run["initial_cuts"][f"{selected_cut}_I"])
    i_increments = np.diff([initial_i] + cuts[selected_cut]["I_series"]).tolist()
    panels = {key: [float(row["fixed_observable_panel_rho_q01"][key]) for row in rows] for key in rows[0]["fixed_observable_panel_rho_q01"]}
    gated = [not bool(row["generator"]["dissipative_enabled"]) for row in rows]
    measurements = [bool(row["retention_stroke"].get("measurement_applied", False)) for row in rows]
    health_rows = [row["density_health"] for row in rows]
    output: dict[str, Any] = {
        "per_nested_cut": cuts,
        "selected_cut": selected_cut,
        "selected_drive_I_correlation": pearson(run["applied_gammas"], i_increments),
        "physicality": {
            "all_ticks_physical": all(bool(row["physical"]) for row in health_rows),
            "max_trace_error": max(float(row["trace_error"]) for row in health_rows),
            "max_hermiticity_error": max(float(row["hermiticity_error"]) for row in health_rows),
            "min_eigenvalue": min(float(row["min_eigenvalue"]) for row in health_rows),
        },
        "generator_and_stroke_counts": {
            "dissipation_gated_off_ticks": sum(gated),
            "measurement_feedback_ticks": sum(measurements),
        },
        "fixed_observable_panel_names": list(panels),
        "fixed_observable_panel_final": {key: values[-1] for key, values in panels.items()},
    }
    if include_panel_series:
        output["fixed_observable_panel_series"] = panels
        output["tick_chain"] = rows
    return output


def compact_metric(metric: dict[str, Any]) -> dict[str, Any]:
    return {
        "per_nested_cut": {
            cut: {
                "negative_fraction": value["negative_fraction"],
                "min_SAB": value["min_SAB"],
                "minimum_tick": value["minimum_tick"],
                "sustained_run_length": value["sustained_run_length"],
            }
            for cut, value in metric["per_nested_cut"].items()
        },
        "selected_cut": metric["selected_cut"],
        "selected_drive_I_correlation": metric["selected_drive_I_correlation"],
        "physicality": metric["physicality"],
        "generator_and_stroke_counts": metric["generator_and_stroke_counts"],
        "fixed_observable_panel_final": metric["fixed_observable_panel_final"],
    }


def select_best(runs: list[tuple[dict[str, Any], dict[str, Any]]]) -> tuple[dict[str, Any], dict[str, Any]]:
    def score(item: tuple[dict[str, Any], dict[str, Any]]) -> tuple[float, float, float]:
        metric = item[1]
        cut = metric["selected_cut"]
        row = metric["per_nested_cut"][cut]
        return (float(row["sustained_run_length"]), float(row["negative_fraction"]), -float(row["min_SAB"]))
    return max(runs, key=score)


def qutip_referee(run: dict[str, Any]) -> dict[str, Any]:
    import qutip

    snapshots = run["snapshots"]
    if len(snapshots) != TICKS:
        raise ValueError("QuTiP referee requires every saved selected-candidate snapshot")
    rows: dict[str, Any] = {}
    maximum = 0.0
    for tick in SPOT_TICKS:
        rho = snapshots[tick].detach().cpu().numpy()
        q = qutip.Qobj(rho, dims=[[2, 2, 2], [2, 2, 2]])
        s_abc = qutip.entropy_vn(q, base=2)
        sab1 = s_abc - qutip.entropy_vn(q.ptrace([1, 2]), base=2)
        sab2 = s_abc - qutip.entropy_vn(q.ptrace([2]), base=2)
        local1 = float(run["rows"][tick]["cuts"]["cut1_SAB"])
        local2 = float(run["rows"][tick]["cuts"]["cut2_SAB"])
        diff1, diff2 = abs(sab1 - local1), abs(sab2 - local2)
        maximum = max(maximum, diff1, diff2)
        rows[str(tick)] = {
            "qutip_cut1_SAB": float(sab1), "local_cut1_SAB": local1, "abs_diff_cut1": float(diff1),
            "qutip_cut2_SAB": float(sab2), "local_cut2_SAB": local2, "abs_diff_cut2": float(diff2),
        }
    return {"spot_ticks": list(SPOT_TICKS), "rows": rows, "max_abs_diff": maximum, "agreement": bool(maximum <= 1e-10), "qutip_version": qutip.__version__}


def shuffled_summary(
    *,
    selected_run: dict[str, Any],
    selected_metric: dict[str, Any],
    selected_config: dict[str, Any],
    source_gammas: list[float],
) -> tuple[dict[str, Any], dict[str, Any]]:
    rng = np.random.default_rng(SHUFFLE_SEED)
    permutation = [int(index) for index in rng.permutation(TICKS)]
    shuffled_gammas = [source_gammas[index] for index in permutation]
    shuffled_run = run_variant(config=selected_config, applied_gammas=shuffled_gammas, entangling=True, initial_kind="product")
    shuffled_metric = metrics_for_run(shuffled_run)
    unshuffled_r = float(selected_metric["selected_drive_I_correlation"])
    selected_cut = str(selected_metric["selected_cut"])
    shuffled_i = shuffled_metric["per_nested_cut"][selected_cut]["I_series"]
    shuffled_initial = float(shuffled_run["initial_cuts"][f"{selected_cut}_I"])
    shuffled_d_i = np.diff([shuffled_initial] + shuffled_i).tolist()
    original_order_r_on_shuffled = pearson(source_gammas, shuffled_d_i)
    both_small = abs(unshuffled_r) < 0.20 and abs(original_order_r_on_shuffled) < 0.20
    return {
        "shuffle_seed": SHUFFLE_SEED,
        "permutation": permutation,
        "unshuffled_drive_I_correlation": unshuffled_r,
        "shuffled_run_vs_original_drive_correlation": original_order_r_on_shuffled,
        "shuffled_run_vs_its_applied_drive_correlation": shuffled_metric["selected_drive_I_correlation"],
        "both_below_0_20": both_small,
        "collapses_or_both_small": bool(abs(original_order_r_on_shuffled) < abs(unshuffled_r) or both_small),
    }, compact_metric(shuffled_metric)


def static_drive_audit() -> dict[str, Any]:
    cut_source = inspect.getsource(cut_readouts)
    panel_source = inspect.getsource(unified_v2.fixed_quantum_observables)
    generator_source = inspect.getsource(generator_from_drive)
    cut_names = {node.id for node in ast.walk(ast.parse(cut_source)) if isinstance(node, ast.Name)}
    panel_names = {node.id for node in ast.walk(ast.parse(panel_source)) if isinstance(node, ast.Name)}
    return {
        "cut_readouts_parameters": list(inspect.signature(cut_readouts).parameters),
        "fixed_panel_parameters": list(inspect.signature(unified_v2.fixed_quantum_observables).parameters),
        "cut_readouts_mentions_drive_identifier": "drive" in cut_names,
        "fixed_panel_mentions_drive_identifier": "drive" in panel_names,
        "generator_mentions_source_gamma": "source_gamma" in generator_source,
        "drive_path": "imported mf.tick gamma -> generator_from_drive Hamiltonian/jump coefficients -> GKSL state -> state-only entropy and fixed panel",
        "passes": bool(
            list(inspect.signature(cut_readouts).parameters) == ["rho"]
            and list(inspect.signature(unified_v2.fixed_quantum_observables).parameters) == ["rho"]
            and "drive" not in cut_names
            and "drive" not in panel_names
            and "source_gamma" in generator_source
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the preregistered Entanglement Pawl v0 sweep.")
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT, help="Refuse-to-reuse output directory (default: canonical pawl_v0 result).")
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise SystemExit(f"refusing to reuse output directory: {out}")
    if TICKS <= max(SPOT_TICKS):
        raise SystemExit("source tick count does not cover preregistered QuTiP spot ticks")

    memory = psutil.virtual_memory()
    free_percent = 100.0 * memory.available / memory.total
    free_gib = memory.available / (1024 ** 3)
    if free_gib < MIN_FREE_GIB:
        raise SystemExit(f"refusing bounded torch sweep: free memory {free_gib:.2f} GiB < {MIN_FREE_GIB:.2f} GiB")
    out.mkdir(parents=True)

    source_dC, source_gammas = imported_drive_series()
    no_pawl_config = {"kind": "none", "schedule": "source_012"}
    baseline_run = run_variant(config=no_pawl_config, applied_gammas=source_gammas, entangling=True, initial_kind="product")
    baseline_metric = metrics_for_run(baseline_run, include_panel_series=True)
    product_run = run_variant(config=no_pawl_config, applied_gammas=source_gammas, entangling=False, initial_kind="product")
    product_metric = metrics_for_run(product_run, include_panel_series=True)

    candidate_receipts: dict[str, Any] = {}
    all_classical_safe = True
    all_candidate_physical = True
    for candidate_name, specs in candidate_specs().items():
        primary_rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
        classical_rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for config in specs:
            primary = run_variant(config=config, applied_gammas=source_gammas, entangling=True, initial_kind="product")
            primary_metric = metrics_for_run(primary)
            primary_rows.append((config, primary_metric))
            classical = run_variant(config=config, applied_gammas=source_gammas, entangling=False, initial_kind="classical_mixture")
            classical_metric = metrics_for_run(classical)
            classical_rows.append((config, classical_metric))
        selected_config, selected_first_metric = select_best(primary_rows)
        # Rerun only the frozen selected setting with snapshots, shuffle, and QuTiP.
        selected_run = run_variant(config=selected_config, applied_gammas=source_gammas, entangling=True, initial_kind="product", keep_snapshots=True)
        selected_metric = metrics_for_run(selected_run, include_panel_series=True)
        if compact_metric(selected_metric) != compact_metric(selected_first_metric):
            raise RuntimeError("deterministic rerun mismatch before referee")
        shuffle, shuffled_metric = shuffled_summary(
            selected_run=selected_run,
            selected_metric=selected_metric,
            selected_config=selected_config,
            source_gammas=source_gammas,
        )
        referee = qutip_referee(selected_run)
        selected_cut = selected_metric["selected_cut"]
        selected_run_length = int(selected_metric["per_nested_cut"][selected_cut]["sustained_run_length"])
        all_classical_nonnegative = all(
            all(metric["per_nested_cut"][cut]["min_SAB"] >= -1e-10 for cut in ("cut1", "cut2"))
            for _, metric in classical_rows
        )
        all_variants_physical = all(metric["physicality"]["all_ticks_physical"] for _, metric in primary_rows + classical_rows)
        chamber_nontrivial = True
        always_off_metric: dict[str, Any] | None = None
        if candidate_name == "chamber_wall":
            gated = selected_metric["generator_and_stroke_counts"]["dissipation_gated_off_ticks"]
            chamber_nontrivial = bool(0 < gated < TICKS)
            always_off_config = {**selected_config, "force_dissipation_off": True}
            always_off_run = run_variant(config=always_off_config, applied_gammas=source_gammas, entangling=True, initial_kind="product")
            always_off_metric = compact_metric(metrics_for_run(always_off_run))
        sustained = selected_run_length >= SUSTAINED_TICKS
        candidate_pass = bool(
            sustained
            and all_classical_nonnegative
            and all_variants_physical
            and shuffle["collapses_or_both_small"]
            and referee["agreement"]
            and chamber_nontrivial
        )
        all_classical_safe = all_classical_safe and all_classical_nonnegative
        all_candidate_physical = all_candidate_physical and all_variants_physical
        candidate_receipts[candidate_name] = {
            "description": {
                "dfs_commutant": "Collective Z0+Z1+Z2 GKSL stroke; its commutator with the full adjacent-pair XY chain is recorded.",
                "drive_duty": "Drive-controlled duty-cycle sweep changes only the XY Hamiltonian coefficient.",
                "chamber_wall": "Pre-stroke rho_q01 eigenvalue-gap threshold gates local dissipative jumps off; an always-off comparison prevents a trivial gate result.",
                "weak_feedback": "Periodic non-postselected weak Z0Z1 parity measurement plus declared local X2 feedback.",
            }[candidate_name],
            "sweep_count": len(specs),
            "sweep_rows": [{"config": config, "metrics": compact_metric(metric)} for config, metric in primary_rows],
            "classical_mixture_control_rows": [{"config": config, "metrics": compact_metric(metric)} for config, metric in classical_rows],
            "all_classical_mixture_runs_nonnegative": all_classical_nonnegative,
            "all_sweep_runs_physical": all_variants_physical,
            "selected_config": selected_config,
            "selected_metrics": selected_metric,
            "shuffled_drive_control": {**shuffle, "shuffled_metrics": shuffled_metric},
            "qutip_referee": referee,
            "chamber_nontrivial_gate": chamber_nontrivial if candidate_name == "chamber_wall" else None,
            "always_dissipation_off_comparison": always_off_metric,
            "sustained_resource_found": sustained,
            "candidate_pass": candidate_pass,
        }

    baseline_max_run = max(int(baseline_metric["per_nested_cut"][cut]["sustained_run_length"]) for cut in ("cut1", "cut2"))
    product_nonnegative = all(product_metric["per_nested_cut"][cut]["min_SAB"] >= -1e-10 for cut in ("cut1", "cut2"))
    product_no_resource = all(max(product_metric["per_nested_cut"][cut]["I_series"]) <= 1e-9 for cut in ("cut1", "cut2"))
    any_candidate_pass = any(bool(item["candidate_pass"]) for item in candidate_receipts.values())
    integrity_checks = {
        "R1_no_pawl_resource_lost_by_third_end_of_tick_sample": baseline_max_run <= 3,
        "R2_product_control_nonnegative": product_nonnegative,
        "R2_product_control_no_coherent_information_gain": product_no_resource,
        "R3_all_pawl_classical_mixtures_nonnegative": all_classical_safe,
        "R6_selected_candidate_qutip_agreement": all(bool(item["qutip_referee"]["agreement"]) for item in candidate_receipts.values()),
        "R7_all_sweep_states_physical": all_candidate_physical and bool(baseline_metric["physicality"]["all_ticks_physical"]) and bool(product_metric["physicality"]["all_ticks_physical"]),
        "drive_readout_separation": static_drive_audit()["passes"],
    }
    resource_status = "sustained_by_at_least_one_candidate" if any_candidate_pass else "no_candidate_sustained_under_preregistered_gates"
    receipt = {
        "schema": "ratchet.v8.entanglement-pawl.v0",
        "name": "entanglement_pawl_v0",
        "generated_at": iso_now(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "one finite three-qubit retention sweep; no official, canonical, scientific, admission, hardware, fault-tolerance, or promotion claim.",
        "runtime": {
            "interpreter": SIM_INTERPRETER,
            "resolved_interpreter": sys.executable,
            "torch": torch.__version__,
            "memory_free_percent_before_run": free_percent,
            "memory_free_gib_before_run": free_gib,
            "minimum_free_gib_guard": MIN_FREE_GIB,
        },
        "source_provenance": {
            "manifold_one": {"path": "system_v8/nested_manifold/manifold_one.py", "sha256": sha256(REPO / "system_v8/nested_manifold/manifold_one.py")},
            "prior_entanglement_ladder_receipt": "system_v8/entanglement_gradient/results/coherent_information_ladder_v0/receipt.json",
            "unified_v2": {"path": "system_v8/unified/manifold_unified_v2.py", "sha256": sha256(REPO / "system_v8/unified/manifold_unified_v2.py")},
            "object_card": "system_v8/entanglement_pawl/pawl_v0_v43_card.json",
        },
        "register": "three qubits rho_ABC (8x8); nested cuts q0|q12 and q01|q2; fixed panel evaluated on rho_q01",
        "parameters": {
            "ticks": TICKS,
            "tick_dt_imported_from_manifold_one": mf.TICK_DT,
            "source_rk4_substeps": mf.NSUB,
            "integrator": "exact matrix exponential of the imported finite GKSL RHS",
            "declared_J_COUPLE": J_COUPLE,
            "imported_mf_J_XY": mf.J_XY,
            "declared_dissipation_scale": DISSIPATION_SCALE,
            "negative_epsilon": NEGATIVE_EPS,
            "sustained_ticks": SUSTAINED_TICKS,
            "stage_schedules": stage_schedules(),
            "candidate_sweep_grid": candidate_specs(),
            "source_packet_capacity_drive_dC": source_dC,
            "source_generator_gamma": source_gammas,
        },
        "tool_manifest": {
            "torch": {"tried": True, "used": True, "reason": "Primary complex128 density evolution, state entropies, controls, and sweep selection."},
            "nested_manifold.manifold_one": {"tried": True, "used": True, "reason": "Load-bearing source for finite GKSL semantics, timing, Pauli vocabulary, stages, and drive generation."},
            "unified_v2.fixed_quantum_observables": {"tried": True, "used": True, "reason": "Exact fixed observable panel called on rho_q01 every tick."},
            "qutip": {"tried": True, "used": True, "reason": "Independent entropy/partial-trace spot referee on three selected trajectories."},
        },
        "tool_integration_depth": {"torch": "load_bearing", "nested_manifold.manifold_one": "load_bearing", "unified_v2.fixed_quantum_observables": "load_bearing", "qutip": "supportive"},
        "preregistered_pass_criteria": {
            "R1": "No-pawl longest negative run is at most three end-of-tick samples.",
            "R2": "Local-only product stays nonnegative and has no coherent-information gain.",
            "R3": "Every candidate pawl-on-classical-mixture run stays nonnegative.",
            "R4": "One cut needs at least ten consecutive S(A|B)<-1e-6 samples.",
            "R5": "Shuffle reduces absolute drive-dI correlation or both correlations are below 0.20.",
            "R6": "QuTiP agrees at ticks 5,15,25 to 1e-10.",
            "R7": "All states are physical; chamber wall cannot pass with its gate always off.",
        },
        "drive_audit": static_drive_audit(),
        "controls": {
            "no_pawl_baseline": baseline_metric,
            "product_state_local_only": product_metric,
        },
        "candidates": candidate_receipts,
        "checks": integrity_checks,
        "resource_status": resource_status,
        "negative_finding": not any_candidate_pass,
        "all_pass": bool(all(integrity_checks.values()) and any_candidate_pass),
        "receipt_valid": bool(all(integrity_checks.values())),
        "findings": [
            "A non-sustaining result is retained as a boundary receipt; all candidate sweep rows remain present.",
            "Drive enters only in generator_from_drive and is absent from cut_readouts and the unified-v2 fixed panel by static audit.",
            "The chamber-wall gate is judged nontrivial only when it is off on at least one but fewer than all ticks; always-off comparison is retained.",
            "Weak measurement feedback is nonselective: both Kraus branches enter the state, and postselection is false by construction.",
        ],
    }
    receipt_path = out / "receipt.json"
    receipt_path.write_text(json.dumps(as_json(receipt), indent=2, allow_nan=False) + "\n")
    print(json.dumps({
        "receipt": str(receipt_path),
        "receipt_valid": receipt["receipt_valid"],
        "resource_status": resource_status,
        "all_pass": receipt["all_pass"],
        "candidate_passes": {name: item["candidate_pass"] for name, item in candidate_receipts.items()},
    }, indent=2))
    return 0 if receipt["receipt_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
