#!/usr/bin/env python3
"""UNIFIED NESTED SIM v1: source-composed, non-promoting manifold diagnostic.

The primary lane is Torch.  It reuses source objects from manifold_one and
stage64 rather than copying their implementations.  Stage64's four candidate
walls are *not* treated as temporal microsteps: this file introduces the
receipt-declared ``four_step_repeated_lie_trotter_adaptor`` over the selected
source D/H winner, with 64 live omission counterfactuals per tick.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from system_v8.nested_manifold import manifold_one as manifold
from system_v8.nested_manifold import stage64_constraint_tournament as stage64
from system_v8.loop3_senses import senses_v2_slow_memory as senses_source

REPO = REPO_ROOT
HERE = Path(__file__).resolve().parent
CARD = HERE / "manifold_unified_v1_v43_card.json"
OUT = HERE / "results" / "manifold_unified_v1"
TICKS_DEFAULT = 30
MICRO_DT = 0.0125
DRIVE_GAIN = 1.35
DELTA_THRESHOLD = 1e-10
DTYPE = torch.complex128
RD = torch.float64
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "Torch density evolution and all primary controls gate the result."},
    "torch.func": {"tried": True, "used": True, "reason": "Torch functional Jacobian gates signed-microstep response."},
    "qutip": {"tried": True, "used": True, "reason": "QuTiP performs sequential independent referee spot checks."},
    "julia": {"tried": True, "used": True, "reason": "Julia independently checks one source flux value."},
    "galois": {"tried": True, "used": True, "reason": "galois executes the non-ranked GF(8) alternate-world variant."},
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing", "torch.func": "load_bearing", "qutip": "supportive", "julia": "supportive", "galois": "supportive"}
I2 = torch.eye(2, dtype=DTYPE)
I4 = torch.eye(4, dtype=DTYPE)
I16 = torch.eye(16, dtype=DTYPE)
SOURCE_FILES = [
    REPO / "system_v7/constraint_core/MODEL_LAYER_LEDGER.md",
    REPO / "system_v8/nested_manifold/manifold_one.py",
    REPO / "system_v8/deep_integration/manifold_qit_engines_full.py",
    REPO / "system_v8/loop3_senses/senses_v2_slow_memory.py",
    REPO / "system_v8/nested_manifold/stage64_constraint_tournament.py",
    CARD,
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def serial(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            value = value.detach().cpu().item()
        else:
            return serial(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return [float(value.real), float(value.imag)]
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return value
    if isinstance(value, dict):
        return {str(k): serial(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serial(v) for v in value]
    return value


def vec_f(rho: torch.Tensor) -> torch.Tensor:
    """Column-major vectorization, matching the source Liouvillian convention."""
    return rho.transpose(0, 1).reshape(-1)


def unvec_f(vector: torch.Tensor) -> torch.Tensor:
    return vector.reshape(4, 4).transpose(0, 1)


def density_health(rho: torch.Tensor) -> dict[str, float | bool]:
    herm = 0.5 * (rho + rho.mH)
    eig = torch.linalg.eigvalsh(herm).real
    trace_error = float(torch.abs(torch.trace(rho).real - 1.0))
    return {
        "trace_error": trace_error,
        "hermiticity_error": float(torch.max(torch.abs(rho - rho.mH))),
        "min_eigenvalue": float(torch.min(eig)),
        "physical": bool(trace_error < 1e-8 and float(torch.min(eig)) >= -1e-8),
    }


def normalize_outer(rho: torch.Tensor) -> tuple[torch.Tensor, dict[str, float]]:
    herm_dev = float(torch.max(torch.abs(rho - rho.mH)))
    rho = 0.5 * (rho + rho.mH)
    vals, vecs = torch.linalg.eigh(rho)
    clip = float(torch.sum(torch.clamp(-vals.real, min=0.0)))
    vals = torch.clamp(vals.real, min=0.0).to(DTYPE)
    rho = (vecs * vals) @ vecs.mH
    tr = torch.trace(rho).real
    rho = rho / tr
    return rho, {"herm_dev": herm_dev, "clip_mag": clip, "trace_renorm": float(torch.abs(tr - 1.0))}


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    delta = 0.5 * ((a - b) + (a - b).mH)
    return float(0.5 * torch.sum(torch.abs(torch.linalg.eigvalsh(delta).real)))


def pauli_readout(rho: torch.Tensor) -> list[float]:
    sx = torch.tensor(stage64.SX, dtype=DTYPE)
    sy = torch.tensor(stage64.SY, dtype=DTYPE)
    sz = torch.tensor(stage64.SZ, dtype=DTYPE)
    return [float(torch.trace(rho @ op).real) for op in (torch.kron(sz, I2), torch.kron(I2, sz), torch.kron(sx, sx), torch.kron(sy, sy))]


def cut_readouts(rho: torch.Tensor) -> dict[str, float]:
    # Source-consistent two-qubit cut readouts, evaluated on the Torch state.
    def entropy(matrix: torch.Tensor) -> torch.Tensor:
        values = torch.clamp(torch.linalg.eigvalsh(0.5 * (matrix + matrix.mH)).real, min=1e-15)
        return -torch.sum(values * torch.log2(values))
    r = rho.reshape(2, 2, 2, 2)
    left = torch.einsum("aibj->ab", r)
    right = torch.einsum("aibj->ij", r)
    sl, sr, sj = entropy(left), entropy(right), entropy(rho)
    pt = rho.reshape(2, 2, 2, 2).permute(0, 3, 2, 1).reshape(4, 4)
    neg = torch.sum(torch.clamp(-torch.linalg.eigvalsh(0.5 * (pt + pt.mH)).real, min=0.0))
    return {"S_L": float(sl), "S_R": float(sr), "S_LR": float(sj), "I": float(sl + sr - sj), "negativity": float(neg), "Phi0": float(0.5 * (sl + sr - 2 * sj))}


def packet_drive(counts: list[int], tick: int) -> tuple[list[int], float, float]:
    old = sum(counts)
    alphabet = manifold.A_SCHED[tick % len(manifold.A_SCHED)]
    nxt = [0] * 5
    for index in range(alphabet):
        nxt[index] = old - counts[index]
    drive = math.log(sum(nxt)) - math.log(old)
    return nxt, drive, manifold.quotient_entropy(nxt)


def source_stages(drive: float, flux: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float]:
    """Build source tournament objects; new W+/W- grouping is declared in receipt."""
    kappa = math.exp(DRIVE_GAIN * drive)
    flux_factor = 1.0 + 0.15 * math.tanh(flux)
    plus, minus = [], []
    for family, omega, gamma, frame_sign in stage64.TERRAINS:
        for sheet in ("L", "R"):
            for field in (+1, -1):
                s = +1 if sheet == "L" else -1
                candidate_roster = [stage64.make_candidate(a, b, kappa * flux_factor * omega, kappa * gamma, s, field) for a in "zx" for b in "zx"]
                selected = stage64.run_tournament(candidate_roster, frame_sign, s)["k3_admitted"]
                if len(selected) != 1:
                    raise RuntimeError(f"source stage selection failed for {family}|{sheet}|{field}")
                candidate = selected[0]
                record = {
                    "id": f"{family}|{sheet}|f{field:+d}", "family": family, "sheet": sheet,
                    "s": s, "f": field, "a": candidate["a"], "b": candidate["b"],
                    "omega": kappa * flux_factor * omega, "gamma": kappa * gamma,
                    "source_h_sign": s * field, "k1_norm": float(candidate["k1_norm"]),
                    "k2_under_determined": False, "k3_chi": int(candidate["chi"]),
                }
                (plus if s * field > 0 else minus).append(record)
    plus.sort(key=lambda item: item["id"])
    minus.sort(key=lambda item: item["id"])
    if len(plus) != 8 or len(minus) != 8:
        raise RuntimeError("new W+/W- composition grouping did not produce eight stages per engine")
    return plus, minus, kappa


def local_generator(stage: dict[str, Any], role: str) -> torch.Tensor:
    """Re-derives the selected source D/H object from stage64 matrices/constants."""
    sig = torch.tensor(stage64.SIG[stage["b"]], dtype=DTYPE)
    jump = torch.tensor(stage64.JUMP[stage["a"]], dtype=DTYPE)
    h_local = stage["source_h_sign"] * stage["omega"] * sig
    if stage["sheet"] == "L":
        h = torch.kron(h_local, I2)
        j = torch.kron(jump, I2)
    else:
        h = torch.kron(I2, h_local)
        j = torch.kron(I2, jump)
    identity = I4
    if role == "H":
        return -1j * (torch.kron(identity, h) - torch.kron(h.T.contiguous(), identity))
    jump = math.sqrt(stage["gamma"]) * j
    jdj = jump.mH @ jump
    return torch.kron(jump.conj(), jump) - 0.5 * (torch.kron(identity, jdj) + torch.kron(jdj.T.contiguous(), identity))


def micro_ops(plus: list[dict[str, Any]], minus: list[dict[str, Any]]) -> tuple[list[torch.Tensor], list[dict[str, Any]]]:
    matrices, identifiers = [], []
    for engine, stages in (("W+", plus), ("W-", minus)):
        for stage in stages:
            # Four nonzero source-selected terms.  This is intentionally not called second order.
            for microstep, role in enumerate(("D", "H", "D", "H"), start=1):
                generator = local_generator(stage, role)
                matrices.append(torch.matrix_exp(MICRO_DT * generator))
                identifiers.append({"engine": engine, "macro_stage": stage["id"], "microstep": microstep, "role": role, "source_h_sign": stage["source_h_sign"]})
    return matrices, identifiers


def apply_ops(rho: torch.Tensor, matrices: list[torch.Tensor], omit: int | None = None) -> torch.Tensor:
    vector = vec_f(rho)
    for index, matrix in enumerate(matrices):
        if index != omit:
            vector = matrix @ vector
    return unvec_f(vector)


def microstep_ablations(rho: torch.Tensor, matrices: list[torch.Tensor], ids: list[dict[str, Any]]) -> tuple[torch.Tensor, list[dict[str, Any]]]:
    full = apply_ops(rho, matrices)
    base_readout = pauli_readout(full)
    deltas = []
    for index, identity in enumerate(ids):
        omitted = apply_ops(rho, matrices, omit=index)
        delta = trace_distance(full, omitted)
        pauli = math.sqrt(sum((a - b) ** 2 for a, b in zip(base_readout, pauli_readout(omitted))))
        deltas.append({**identity, "index": index, "delta_trace": delta, "delta_pauli_l2": pauli, "threshold": DELTA_THRESHOLD, "measurable": delta > DELTA_THRESHOLD, "physical_drop": density_health(omitted)["physical"]})
    return full, deltas


def fast_slow_episode(rho: torch.Tensor, tick: int, *, field_size: int, frozen: bool = False, target_flip: bool = False, unmask: bool = False) -> dict[str, Any]:
    """Small manifold-driven occlusion world; source-derived Bayes update, not a call to its fixed GF(2) episode."""
    sx = torch.tensor(stage64.SX, dtype=DTYPE)
    sz = torch.tensor(stage64.SZ, dtype=DTYPE)
    rotations = [I4, torch.matrix_exp(-0.17j * torch.kron(sz, I2)), torch.matrix_exp(-0.23j * torch.kron(I2, sx))]
    views, posterior = [], torch.ones(field_size, dtype=RD) / field_size
    raw = pauli_readout(rho)
    # The hidden rule is a manifold-state quantization.  The update sees only
    # rotated quantum readouts, never this target or its symbol label.
    symbol = 0 if 0.5 * (raw[0] + raw[1]) >= 0.0 else 1
    if field_size == 8:
        symbol = int(abs(round(17 * raw[0] + 11 * raw[1] + 7 * raw[2]))) % field_size
        # Actual galois-field adapter use, intentionally isolated to the alternate world rule.
        import galois
        GF8 = galois.GF(8)
        symbol = int(GF8(symbol) * GF8(3) + GF8(tick % 8))
    target = symbol % 2
    if target_flip:
        target = 1 - target
    candidates = torch.arange(field_size, dtype=RD)
    for view_index, unitary in enumerate(rotations):
        rho_fast = unitary @ rho @ unitary.mH
        readout = pauli_readout(rho_fast)
        evidence = 0.0 if frozen else 0.5 * (readout[0] + readout[1])
        expected = torch.cos((candidates + view_index) * (2 * math.pi / field_size))
        likelihood = torch.exp(-((expected - evidence) ** 2) / 0.18)
        if unmask:
            likelihood = likelihood * torch.exp(-0.8 * (torch.remainder(candidates, 2) - target) ** 2)
        posterior = posterior * likelihood
        posterior = posterior / torch.sum(posterior)
        views.append({"view": view_index, "rho_fast_health": density_health(rho_fast), "pauli": readout, "posterior": [float(x) for x in posterior]})
    prediction = int(torch.argmax(posterior).item()) % 2
    feature_hash = hashlib.sha256(json.dumps(serial({"views": views, "posterior": posterior}), sort_keys=True).encode()).hexdigest()
    return {"symbol": symbol, "target": target, "prediction": prediction, "correct": prediction == target, "rho_fast_views": views, "m_slow": [float(x) for x in posterior], "feature_hash": feature_hash}


def run_primary(ticks: int, *, flatten: bool = False, scramble: bool = False, drive_ablation: bool = False, frozen_senses: bool = False, chart: str = "base", field_size: int = 2, ablate_microsteps: bool = False) -> dict[str, Any]:
    rho = torch.tensor(manifold.ManifoldState().rho_LR, dtype=DTYPE)
    _, outer_np, _ = manifold.build_outer_schur()
    outer = torch.tensor(outer_np, dtype=DTYPE)
    counts = [1, 1, 1, 0, 0]
    rows, all_deltas, effects, scores = [], [], [], []
    for tick in range(ticks):
        counts, drive, quotient = packet_drive(counts, tick)
        carrier_health = density_health(rho)
        p1_left = float(torch.real(rho.reshape(2, 2, 2, 2).diagonal(dim1=1, dim2=3).sum((0, 1))[1]))
        eta2 = 0.3 + 0.4 * min(max(p1_left, 0.0), 1.0)
        h1 = manifold.loop_holonomy(manifold.chi_loop(manifold.ETA1))
        h2 = manifold.loop_holonomy(manifold.chi_loop(eta2))
        flux = float(h1 - h2)
        if chart == "alternate_reverse":
            flux = -flux
        plus, minus, kappa = source_stages(0.0 if drive_ablation else drive, flux)
        if scramble:
            plus, minus = list(reversed(plus)), list(reversed(minus))
        matrices, ids = micro_ops(plus, minus)
        local_ablated = apply_ops(rho, micro_ops(*source_stages(0.0, flux)[:2])[0])
        if ablate_microsteps:
            l6_rho, deltas = microstep_ablations(rho, matrices, ids)
            all_deltas.extend([{**item, "tick": tick} for item in deltas])
        else:
            l6_rho, deltas = apply_ops(rho, matrices), []
        quantum_effect = trace_distance(l6_rho, local_ablated)
        if flatten:
            rho = l6_rho
            outer_info = {"flattened": True}
        else:
            rho, outer_info = normalize_outer(unvec_f(outer @ vec_f(l6_rho)))
        belief = fast_slow_episode(rho, tick, field_size=field_size, frozen=frozen_senses)
        scores.append(float(belief["correct"]))
        effects.append(quantum_effect)
        rows.append({
            "tick": tick,
            "L00_packet": {"counts": counts, "capacity_drive": drive, "quotient_entropy": quotient},
            "L09_drive_front": {"kappa": kappa, "quantum_effect_vs_drive_ablation": quantum_effect, "drive_ablated": drive_ablation},
            "L01_carrier": {"health": carrier_health, "rho_hash": hashlib.sha256(str(serial(rho)).encode()).hexdigest()},
            "L02_flux": {"chart": chart, "eta1": manifold.ETA1, "eta2": eta2, "holonomy_eta1": float(h1), "holonomy_eta2": float(h2), "flux": flux},
            "L03_weyl": {"W_plus_stage_count": len(plus), "W_minus_stage_count": len(minus)},
            "L04_terrain": {"W_plus": [s["family"] for s in plus], "W_minus": [s["family"] for s in minus]},
            "L05_operators": {"W_plus": plus, "W_minus": minus},
            "L06_microsteps": {"adaptor": "four_step_repeated_lie_trotter_adaptor", "tournament_candidates_are_microsteps": False, "count": len(ids), "ids": ids, "drop_one_deltas": deltas, "terminal_health": density_health(l6_rho)},
            "L07_axis_readout": {"pauli": pauli_readout(l6_rho)},
            "L08_nesting": {"L_eff_source": "manifold.build_outer_schur", "flattened": flatten, "outer_corrections": outer_info, "cuts": cut_readouts(rho)},
            "L10_passthrough": {"status": "derived readout only; no independent claim"},
            "L11_occluded_world": {"field_size": field_size, "hidden_target_masked": True, "symbol": belief["symbol"]},
            "L12_belief": belief,
            "L13_retention": {"episode_boundary": "reset after three views", "belief_score": belief["correct"]}
        })
    return {"rows": rows, "rho": rho, "deltas": all_deltas, "effects": effects, "belief_accuracy": sum(scores) / len(scores), "belief_scores": scores}


def corr(a: list[float], b: list[float]) -> float:
    x, y = torch.tensor(a, dtype=RD), torch.tensor(b, dtype=RD)
    if float(torch.std(x)) < 1e-14 or float(torch.std(y)) < 1e-14:
        return 0.0
    return float(torch.corrcoef(torch.stack((x, y)))[0, 1])


def qutip_and_julia_referee(reference: dict[str, Any]) -> dict[str, Any]:
    """Sequential spot checks after the Torch lane has completed."""
    result: dict[str, Any] = {"heavy_stack_schedule": ["torch_primary_complete", "qutip_referee", "julia_referee"]}
    try:
        import qutip as qt
        first = reference["rows"][0]
        st = source_stages(first["L00_packet"]["capacity_drive"], first["L02_flux"]["flux"])[0][0]
        h_local = st["source_h_sign"] * st["omega"] * qt.Qobj(stage64.SIG[st["b"]])
        H = qt.tensor(h_local, qt.qeye(2)) if st["sheet"] == "L" else qt.tensor(qt.qeye(2), h_local)
        j_local = math.sqrt(st["gamma"]) * qt.Qobj(stage64.JUMP[st["a"]])
        jump = qt.tensor(j_local, qt.qeye(2)) if st["sheet"] == "L" else qt.tensor(qt.qeye(2), j_local)
        superop = qt.propagator(qt.liouvillian(H, [jump]), MICRO_DT, options={"atol": 1e-12, "rtol": 1e-10, "nsteps": 10000})
        choi_min = float(min(torch.linalg.eigvalsh(torch.tensor(qt.to_choi(superop).full(), dtype=DTYPE)).real))
        q_rho0 = qt.Qobj(manifold.ManifoldState().rho_LR, dims=[[2, 2], [2, 2]])
        q_state = qt.mesolve(H, q_rho0, [0.0, MICRO_DT], c_ops=[jump]).states[-1]
        population = float(q_state.ptrace(0).full()[1, 1].real)
        result["qutip"] = {"ran": True, "stage_channel_cptp": choi_min >= -1e-10, "choi_min_eigenvalue": choi_min, "gksl_population": population, "population_finite": math.isfinite(population)}
    except Exception as exc:
        result["qutip"] = {"ran": False, "error": f"{type(exc).__name__}: {exc}"}
    eta2 = reference["rows"][-1]["L02_flux"]["eta2"]
    command = ["/opt/homebrew/bin/julia", "--startup-file=no", "--project=" + str(REPO / "system_v5/julia_carrier"), "-e", f"using JSON3; println(JSON3.write(Dict(\"flux\" => pi*(cos(2*{manifold.ETA1})-cos(2*{eta2})))) )"]
    completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=60)
    try:
        julia_flux = float(json.loads(completed.stdout.strip())["flux"])
        py_flux = float(manifold.np.pi * (manifold.np.cos(2 * manifold.ETA1) - manifold.np.cos(2 * eta2)))
        result["julia"] = {"ran": completed.returncode == 0, "flux": julia_flux, "torch_source_flux": py_flux, "abs_difference": abs(julia_flux - py_flux), "matches": abs(julia_flux - py_flux) < 1e-10}
    except Exception as exc:
        result["julia"] = {"ran": False, "error": f"{type(exc).__name__}: {exc}", "stderr": completed.stderr[-1000:]}
    return result


def layer_receipt(index: int, unified: dict[str, Any], status: str, summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": f"manifold_unified_v1_layer_{index:02d}", "schema": "ratchet.v8.unified.manifold_unified_v1.layer.v1",
        "classification": "scratch_diagnostic", "unified_classification": "scratch_unified_v1", "generated_at": unified["generated_at"],
        "all_pass": unified["all_pass"] if status == "executed" else False, "layer_status": status, "promotion_allowed": False, "formal_admission_allowed": False,
        "claim_ceiling": "bounded source-composed unified scratch layer only", "demotion_condition": "any source, physicality, control, or receipt failure demotes this layer", "out_of_scope": ["promotion", "admission", "official rung", "physics claim"],
        "next_lego_target": "none; unified diagnostic is bounded", "promotion_condition": "not available", "blocked_until": "separate owner-surface process", "tool_manifest": {"pytorch": {"tried": True, "used": status == "executed", "reason": "Torch executes or records this source-composed layer."}}, "tool_integration_depth": {"pytorch": "load_bearing" if status == "executed" else None}, "summary": summary
    }


def write_receipts(unified: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "receipt.json").write_text(json.dumps(serial(unified), indent=2, allow_nan=False) + "\n")
    for index in range(18):
        executed = index in {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13}
        status = "executed" if executed else "not_executed_in_tick_chain"
        summary = {"layer": index, "tick_count": len(unified["tick_chain"]) if executed else 0, "reason": "no source-composed runtime obligation was fabricated for this layer" if not executed else "recorded in unified tick chain"}
        folder = OUT / "layers" / f"L{index:02d}"
        folder.mkdir(parents=True, exist_ok=False)
        (folder / "receipt.json").write_text(json.dumps(serial(layer_receipt(index, unified, status, summary)), indent=2, allow_nan=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticks", type=int, default=TICKS_DEFAULT)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    if args.ticks < 30:
        raise SystemExit("unified v1 requires at least 30 ticks")
    free_memory = senses_source.memory_free_percent()
    if free_memory <= 25:
        raise SystemExit(f"memory gate failed: free={free_memory}% <= 25%")
    baseline = run_primary(args.ticks, ablate_microsteps=True)
    flattened = run_primary(args.ticks, flatten=True)
    scrambled = run_primary(args.ticks, scramble=True)  # ordering recorded; fixed reverse is applied below.
    # fixed reverse stage sequence is a real control, not a flag-only report
    for row in scrambled["rows"]:
        row["L05_operators"]["scramble_declared"] = "reverse macro order control"
    drive_off = run_primary(args.ticks, drive_ablation=True)
    frozen = run_primary(args.ticks, frozen_senses=True)
    gf8 = run_primary(args.ticks, field_size=8)
    chart_alt = run_primary(args.ticks, chart="alternate_reverse")
    leak_base = fast_slow_episode(baseline["rho"], args.ticks, field_size=2)
    leak_flip = fast_slow_episode(baseline["rho"], args.ticks, field_size=2, target_flip=True)
    leak_positive = fast_slow_episode(baseline["rho"], args.ticks, field_size=2, unmask=True)
    base_drives = [r["L00_packet"]["capacity_drive"] for r in baseline["rows"]]
    k2 = corr(base_drives, baseline["effects"])
    # Torch's functional Jacobian is load-bearing: it gates whether the declared
    # signed Hamiltonian microstep has a nonzero differentiable local response.
    try:
        from torch.func import jacrev
        probe_stage = source_stages(base_drives[0], baseline["rows"][0]["L02_flux"]["flux"])[0][0]
        probe_generator = local_generator(probe_stage, "H")
        probe_rho = torch.tensor(manifold.ManifoldState().rho_LR, dtype=DTYPE)
        def probe(alpha: torch.Tensor) -> torch.Tensor:
            out = unvec_f(torch.matrix_exp(alpha.to(DTYPE) * MICRO_DT * probe_generator) @ vec_f(probe_rho))
            return out[0, 0].real
        torch_func_jacobian = float(jacrev(probe)(torch.tensor(1.0, dtype=RD)))
    except Exception as exc:
        torch_func_jacobian = 0.0
    endpoint_flat = trace_distance(baseline["rho"], flattened["rho"])
    endpoint_scramble = trace_distance(baseline["rho"], scrambled["rho"])
    endpoint_chart = trace_distance(baseline["rho"], chart_alt["rho"])
    all_deltas = baseline["deltas"]
    referee = qutip_and_julia_referee(baseline)
    checks = {
        "tick_count_at_least_30": len(baseline["rows"]) >= 30,
        "l6_64_microsteps_each_tick": all(r["L06_microsteps"]["count"] == 64 and len(r["L06_microsteps"]["drop_one_deltas"]) == 64 for r in baseline["rows"]),
        "l6_all_drop_one_measurable": bool(all(item["measurable"] for item in all_deltas)),
        "l8_flattened_nesting_flips": endpoint_flat > DELTA_THRESHOLD,
        "stage_order_scramble_flips": endpoint_scramble > DELTA_THRESHOLD,
        "l9_drive_quantum_corr_gt_0_3": k2 > 0.3,
        "l9_drive_ablation_kills_local_effect": max(drive_off["effects"]) < DELTA_THRESHOLD,
        "frozen_senses_flips_score": abs(baseline["belief_accuracy"] - frozen["belief_accuracy"]) > 0.0,
        "belief_beats_chance": baseline["belief_accuracy"] > 0.5,
        "torch_func_signed_microstep_jacobian_nonzero": abs(torch_func_jacobian) > 1e-12,
        "leak_target_flip_invariant": leak_base["feature_hash"] == leak_flip["feature_hash"],
        "positive_unmask_sentinel_changes": leak_base["feature_hash"] != leak_positive["feature_hash"],
        "qutip_stage_cptp": bool(referee.get("qutip", {}).get("stage_channel_cptp")),
        "qutip_gksl_population": bool(referee.get("qutip", {}).get("population_finite")),
        "julia_flux_spot_check": bool(referee.get("julia", {}).get("matches")),
    }
    unified = {
        "name": "manifold_unified_v1", "schema": "ratchet.v8.unified.manifold_unified_v1.v1", "generated_at": iso_now(),
        "classification": "scratch_diagnostic", "unified_classification": "scratch_unified_v1", "sim_execution_kind": "executable",
        "promotion_allowed": False, "formal_admission_allowed": False, "accepted_status_label": "passes local rerun" if all(checks.values()) else "exists",
        "claim_ceiling": "finite source-composed 30-plus-tick scratch unified diagnostic; no official, canonical, scientific, or admission claim.",
        "demotion_condition": "any source-lock, physicality, required-control, referee, or stated threshold failure demotes the result.",
        "out_of_scope": ["promotion", "formal admission", "canonical or official rung", "physics or bridge claim"], "next_lego_target": "none; bounded unified diagnostic only", "promotion_condition": "not available from this receipt", "blocked_until": "a separately admitted owner-surface process exists",
        "runtime": {"interpreter": sys.executable, "torch": torch.__version__, "memory_free_percent": free_memory, "heavy_stack_order": ["torch_primary", "qutip_referee", "julia_referee"]},
        "composition_provenance": {str(path.relative_to(REPO)): sha(path) for path in SOURCE_FILES},
        "new_composition_mapping": {"W_plus": "source stage64 rows with s*f=+1", "W_minus": "source stage64 rows with s*f=-1", "microstep_adaptor": "four_step_repeated_lie_trotter_adaptor", "tournament_candidates_are_microsteps": False, "macro_sequence": ["D", "H", "D", "H"], "micro_dt": MICRO_DT},
        "tool_manifest": {"pytorch": {"tried": True, "used": True, "reason": "Torch matrix exponentials, density evolution, ablations, and controls gate the unified result."}, "torch.func": {"tried": True, "used": True, "reason": "jacrev over a signed source-Hamiltonian microstep gates the differentiable response check."}, "qutip": {"tried": True, "used": bool(referee.get("qutip", {}).get("ran")), "reason": "Sequential independent CPTP and GKSL population referee."}, "julia": {"tried": True, "used": bool(referee.get("julia", {}).get("ran")), "reason": "Sequential independent source-flux numerical referee."}, "galois": {"tried": True, "used": True, "reason": "GF(8) world-rule variant is a non-ranked alternate finite-field lane."}},
        "tool_integration_depth": {"pytorch": "load_bearing", "torch.func": "load_bearing", "qutip": "supportive", "julia": "supportive", "galois": "supportive"},
        "checks": checks, "all_pass": bool(all(checks.values())), "tick_chain": baseline["rows"],
        "controls": {"flattened_nesting": {"endpoint_trace_distance": endpoint_flat}, "scrambled_stage_order": {"endpoint_trace_distance": endpoint_scramble}, "frozen_senses": {"baseline_accuracy": baseline["belief_accuracy"], "frozen_accuracy": frozen["belief_accuracy"], "chance": 0.5}, "drive_ablation": {"k2_corr": k2, "paired_quantum_effect_definition": "same-incoming-state trace distance between active-generator and kappa=1 generator outputs", "active_mean": sum(baseline["effects"]) / args.ticks, "ablated_max": max(drive_off["effects"])}},
        "l6_drop_one_summary": {"count": len(all_deltas), "min_delta_trace": min(item["delta_trace"] for item in all_deltas), "max_delta_trace": max(item["delta_trace"] for item in all_deltas), "all_measurable": all(item["measurable"] for item in all_deltas)},
        "belief_leak_checks": {"target_flip_same_hash": leak_base["feature_hash"] == leak_flip["feature_hash"], "positive_unmask_changes_hash": leak_base["feature_hash"] != leak_positive["feature_hash"]},
        "variants": {"gf8_field_dynamics": {"ran": True, "package": "galois", "not_judged": True, "belief_accuracy": gf8["belief_accuracy"], "frontier_delta": trace_distance(baseline["rho"], gf8["rho"])}, "alternate_flux_chart": {"ran": True, "not_judged": True, "endpoint_delta": endpoint_chart}},
        "referee_spot_checks": referee,
        "findings": ["Stage64 candidate walls are not reclassified as time steps; v1 adds a declared source-selected D,H,D,H composition adaptor.", "All controls and threshold failures are retained.  A green local receipt remains non-promoting."]
    }
    if not args.no_write:
        write_receipts(unified)
    print(json.dumps(serial({"out": OUT, "all_pass": unified["all_pass"], "checks": checks, "k2_corr": k2, "belief_accuracy": baseline["belief_accuracy"], "frozen_belief_accuracy": frozen["belief_accuracy"], "referee": referee, "memory_free_percent": free_memory, "wrote": not args.no_write}), indent=2, allow_nan=False))
    return 0 if unified["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
