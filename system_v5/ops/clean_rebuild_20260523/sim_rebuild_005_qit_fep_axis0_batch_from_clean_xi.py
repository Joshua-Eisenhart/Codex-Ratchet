#!/usr/bin/env python3
"""Clean-room rebuild 005: QIT-FEP/Axis0 batch over clean Xi states.

This script consumes only the clean rebuild_004 source functions, not any
formal_scout result receipt. It tests a finite Kraus-history QIT-FEP readout
batch over clean Xi candidate states and keeps final Axis0 blocked.
"""

from __future__ import annotations

import itertools
import json
import math
import pathlib
import time
from typing import Any

import torch

from sim_rebuild_004_xi_rho_ab_bridge_family_from_readonly import (
    CDTYPE,
    EPS,
    I2,
    SX,
    SZ,
    cut_readouts,
    entangled_cut,
    entropy,
    partial_trace_a,
    path_spinors,
    product_cut,
    spinor,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "rebuild_005_qit_fep_axis0_batch_from_clean_xi_results.json"

classification = "clean_rebuild_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical_clean_rebuild"
SOURCE_ALIGNMENT_CATEGORY = "qit_fep_axis0_batch_from_clean_xi"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Clean rebuild scout only: runs finite Kraus-history QIT-FEP readouts over "
    "clean Xi bridge states. It does not admit final Axis0, Xi, Phi0, Markov "
    "blanket ontology, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite Kraus histories, two-qubit postselected cut states, entropy, and candidate readouts",
    },
    "clean_rebuild_004_source": {
        "tried": True,
        "used": True,
        "reason": "supportive reuse of clean-room Xi bridge constructors without reading result receipts",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive clean rebuild receipt serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result paths"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "clean_rebuild_004_source": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

I4 = torch.eye(4, dtype=CDTYPE)
ZZ = torch.kron(SZ, SZ)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def hermitize(mat: torch.Tensor) -> torch.Tensor:
    return (mat + torch.conj(mat).T) / 2.0


def normalize_state(rho: torch.Tensor) -> torch.Tensor:
    return hermitize(rho / torch.real(torch.trace(rho)))


def unitary(axis: torch.Tensor, theta: float) -> torch.Tensor:
    return math.cos(theta / 2.0) * I2 - 1j * math.sin(theta / 2.0) * axis


def dephase(axis: torch.Tensor, q: float) -> list[torch.Tensor]:
    return [math.sqrt(1.0 - q) * I2, math.sqrt(q) * axis]


def instrument_registry() -> list[list[torch.Tensor]]:
    return [
        [unitary(SZ, 0.33)],
        dephase(SX, 0.12),
        dephase(SZ, 0.07),
    ]


def enumerate_paths(instruments: list[list[torch.Tensor]]) -> list[torch.Tensor]:
    paths = []
    for choices in itertools.product(*instruments):
        k = I2.clone()
        for step in choices:
            k = step @ k
        paths.append(k)
    return paths


def psd_sqrt(mat: torch.Tensor) -> torch.Tensor:
    vals, vecs = torch.linalg.eigh(hermitize(mat))
    vals = torch.clamp(vals.real, min=0.0)
    return vecs @ torch.diag(torch.sqrt(vals)).to(CDTYPE) @ torch.conj(vecs).T


def qit_path_readout(rho_ab: torch.Tensor) -> dict[str, Any]:
    effect = hermitize(0.5 * I2 + 0.22 * SZ + 0.11 * SX)
    sqrt_e = psd_sqrt(effect)
    sqrt_e_ab = torch.kron(sqrt_e, I2)
    effect_ab = torch.kron(effect, I2)
    tau = torch.zeros((4, 4), dtype=CDTYPE)
    z_path = 0.0
    paths = enumerate_paths(instrument_registry())
    for k_a in paths:
        k_ab = torch.kron(k_a, I2)
        evolved = k_ab @ rho_ab @ torch.conj(k_ab).T
        z_path += float(torch.real(torch.trace(effect_ab @ evolved)).item())
        tau = tau + sqrt_e_ab @ evolved @ torch.conj(sqrt_e_ab).T
    posterior = normalize_state(tau)
    readouts = cut_readouts(posterior)
    log_z = math.log(max(z_path, EPS))
    return {
        "path_count": len(paths),
        "z_path": z_path,
        "log_z": log_z,
        "posterior_trace_gap": abs(torch.real(torch.trace(posterior)).item() - 1.0),
        "posterior_min_eig": float(torch.min(torch.linalg.eigvalsh(hermitize(posterior)).real).item()),
        "I_c": readouts["coherent_information_A_to_B"],
        "MI": readouts["mutual_information"],
        "S_A_given_B": readouts["conditional_entropy_A_given_B"],
        "Phi_logZ_plus_Ic": log_z + readouts["coherent_information_A_to_B"],
        "Phi_logZ_plus_MI": log_z + readouts["mutual_information"],
    }


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values))


def span(values: list[float]) -> float:
    return float(max(values) - min(values))


def shell_cut_state(sample: torch.Tensor, phi0: float, eta: float, shell_size: int = 8) -> torch.Tensor:
    acc = torch.zeros((4, 4), dtype=CDTYPE)
    for k in range(shell_size):
        ref = spinor(phi0, 2.0 * math.pi * k / shell_size, eta)
        acc = acc + entangled_cut(sample, ref) / shell_size
    return normalize_state(acc)


def bridge_states(mode: str, path: str, steps: int = 18) -> list[torch.Tensor]:
    phi0, chi0, eta = 0.17, 0.31, 0.44
    samples = path_spinors(path, phi0, chi0, eta, steps=steps)
    reference = spinor(-0.28, 0.79, math.pi / 4.0)
    states = []
    for idx, sample in enumerate(samples):
        if mode == "product":
            states.append(product_cut(sample, reference))
        elif mode == "point_reference":
            states.append(entangled_cut(sample, reference))
        elif mode == "history_window":
            states.append(entangled_cut(sample, samples[idx - 1]))
        elif mode == "shell_cut":
            states.append(shell_cut_state(sample, phi0, eta))
        else:
            raise ValueError(mode)
    return states


def summarize_mode(mode: str, path: str) -> dict[str, Any]:
    rows = [qit_path_readout(state) for state in bridge_states(mode, path)]
    keys = ["log_z", "I_c", "MI", "S_A_given_B", "Phi_logZ_plus_Ic", "Phi_logZ_plus_MI"]
    return {
        "mode": mode,
        "path": path,
        "path_count": rows[0]["path_count"],
        "posterior_trace_gap_max": max(row["posterior_trace_gap"] for row in rows),
        "posterior_min_eig_min": min(row["posterior_min_eig"] for row in rows),
        "means": {key: mean([row[key] for row in rows]) for key in keys},
        "spans": {key: span([row[key] for row in rows]) for key in keys},
    }


def implementation_gate() -> dict[str, Any]:
    rho = bridge_states("point_reference", "lifted_base", steps=3)[1]
    readout = qit_path_readout(rho)
    return {
        "pass": readout["path_count"] == 4 and readout["z_path"] > 0.0 and readout["posterior_trace_gap"] < 1e-12,
        "path_count": readout["path_count"],
        "z_path": readout["z_path"],
        "posterior_trace_gap": readout["posterior_trace_gap"],
        "posterior_min_eig": readout["posterior_min_eig"],
    }


def candidate_batch_gate() -> dict[str, Any]:
    summaries = {}
    for mode in ("product", "point_reference", "history_window", "shell_cut"):
        for path in ("fiber", "lifted_base"):
            summaries[f"{mode}_{path}"] = summarize_mode(mode, path)

    product_mi_floor = max(abs(summaries["product_fiber"]["means"]["MI"]), abs(summaries["product_lifted_base"]["means"]["MI"]))
    history_fiber_mi = summaries["history_window_fiber"]["means"]["MI"]
    history_base_mi = summaries["history_window_lifted_base"]["means"]["MI"]
    point_fiber_ic_span = summaries["point_reference_fiber"]["spans"]["I_c"]
    point_base_ic_span = summaries["point_reference_lifted_base"]["spans"]["I_c"]
    shell_mi = min(summaries["shell_cut_fiber"]["means"]["MI"], summaries["shell_cut_lifted_base"]["means"]["MI"])

    return {
        "pass": (
            product_mi_floor < 1e-10
            and abs(history_fiber_mi) < 1e-10
            and history_base_mi > 1e-2
            and point_fiber_ic_span < 1e-10
            and point_base_ic_span > 1e-2
            and shell_mi > 1e-2
        ),
        "source": "Axis0/QIT readouts are tested only after Xi constructs rho_AB; product, point, shell, and history forms stay role-distinct",
        "summaries": summaries,
        "product_mi_floor": product_mi_floor,
        "history_window_base_mean_MI": history_base_mi,
        "point_reference_base_span_Ic": point_base_ic_span,
        "shell_min_mean_MI": shell_mi,
    }


def nonadmission_gate(batch: dict[str, Any]) -> dict[str, Any]:
    summaries = batch["summaries"]
    candidate_keys = ["log_z", "I_c", "MI", "Phi_logZ_plus_Ic", "Phi_logZ_plus_MI"]
    rankings = {}
    for key in candidate_keys:
        ranking = sorted(
            ((name, summary["means"][key]) for name, summary in summaries.items()),
            key=lambda item: item[1],
            reverse=True,
        )
        rankings[key] = ranking[:3]
    top_modes = {key: rankings[key][0][0] for key in candidate_keys}
    unique_top_modes = sorted(set(top_modes.values()))
    return {
        "pass": len(unique_top_modes) >= 2,
        "admission": "blocked",
        "top_modes_by_candidate": top_modes,
        "unique_top_modes": unique_top_modes,
        "rankings_top3": rankings,
        "reason": "Different allowed readouts select different top bridge/path modes, so this batch does not justify one final Axis0/Phi0 scalar.",
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    implementation = implementation_gate()
    batch = candidate_batch_gate()
    nonadmission = nonadmission_gate(batch)
    sections = {
        "implementation_gate": implementation,
        "candidate_batch_gate": batch,
        "nonadmission_gate": nonadmission,
    }
    all_pass = all(bool(section["pass"]) for section in sections.values())
    result = {
        "schema": "clean_rebuild_result_v1",
        "name": "rebuild_005_qit_fep_axis0_batch_from_clean_xi",
        "classification": classification,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "sections": sections,
        "axis0_status": {
            "candidate_batch_rebuilt": bool(batch["pass"]),
            "final_axis0_admitted": False,
            "final_phi0_admitted": False,
            "next_required_test": "run matched-control ensemble over the clean batch before any formal_scout regeneration",
        },
        "source_boundary": {
            "reads_formal_scout_results": False,
            "reads_grok_sim": False,
            "reads_external_audits": False,
            "reads_cross_lane_synthesis_docs": False,
            "reads_clean_rebuild_source": ["sim_rebuild_004_xi_rho_ab_bridge_family_from_readonly.py"],
            "reads_clean_rebuild_results": False,
        },
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "out": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

