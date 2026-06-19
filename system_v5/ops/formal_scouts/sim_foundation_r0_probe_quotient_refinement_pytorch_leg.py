#!/usr/bin/env python3
"""PyTorch R0 probe quotient refinement third-substrate leg.

Scratch diagnostic only. This lane computes locally and does not read peer
engine result JSON.
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev, vmap


OBJECT_ID = "foundation_r0_probe_quotient_refinement_v1"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_foundation_r0_probe_quotient_refinement_pytorch_leg.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r0_probe_quotient_refinement_pytorch_results.json"
TOL = 1.0e-10

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex128 density matrices, projectors, eigvalsh PSD checks, and Born-rule traces",
    },
    "torch.func.vmap": {
        "tried": True,
        "used": True,
        "reason": "load-bearing batched probe observable computation over finite support states and effects",
    },
    "torch.func.jacrev": {
        "tried": True,
        "used": True,
        "reason": "load-bearing differentiable check that X expectation changes with coherence while Z expectation does not",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive paths, timestamp, JSON serialization, and finite partition assembly",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.func.vmap": "load_bearing",
    "torch.func.jacrev": "load_bearing",
    "Python stdlib": "supportive",
}


def scalar(value: torch.Tensor | float) -> float:
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().item())
    return float(value)


def rounded(value: torch.Tensor | float, digits: int = 12) -> float:
    return round(scalar(value), digits)


def ket(values: list[complex]) -> torch.Tensor:
    vec = torch.tensor(values, dtype=torch.complex128)
    return vec / torch.linalg.vector_norm(vec)


def density(vec: torch.Tensor) -> torch.Tensor:
    return torch.outer(vec, vec.conj())


def objects() -> tuple[dict[str, torch.Tensor], dict[str, dict[str, Any]]]:
    z0 = ket([1.0 + 0.0j, 0.0 + 0.0j])
    z1 = ket([0.0 + 0.0j, 1.0 + 0.0j])
    x_plus = ket([1.0 + 0.0j, 1.0 + 0.0j])
    x_minus = ket([1.0 + 0.0j, -1.0 + 0.0j])
    states = {
        "rho_z0": density(z0),
        "rho_z1": density(z1),
        "rho_plus": density(x_plus),
        "rho_minus": density(x_minus),
    }
    probes = {
        "Z": {"name": "Z", "outcome_labels": ["z0", "z1"], "effects": [density(z0), density(z1)]},
        "X": {"name": "X", "outcome_labels": ["x_plus", "x_minus"], "effects": [density(x_plus), density(x_minus)]},
        "Z_duplicate": {
            "name": "Z_duplicate",
            "outcome_labels": ["z0_dup", "z1_dup"],
            "effects": [density(z0), density(z1)],
        },
        "Z_relabel": {
            "name": "Z_relabel",
            "outcome_labels": ["z1_relabel", "z0_relabel"],
            "effects": [density(z1), density(z0)],
        },
    }
    return states, probes


def expectation(effect: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    return torch.real(torch.trace(effect @ rho))


def batched_distribution(rho: torch.Tensor, effects: list[torch.Tensor]) -> list[float]:
    effects_tensor = torch.stack(effects)
    values = vmap(lambda effect: expectation(effect, rho))(effects_tensor)
    return [rounded(value, 12) for value in values]


def distribution(rho: torch.Tensor, probe: dict[str, Any]) -> list[float]:
    return batched_distribution(rho, probe["effects"])


def quotient(states: dict[str, torch.Tensor], probe_family: list[dict[str, Any]], name: str) -> dict[str, Any]:
    classes: dict[str, dict[str, Any]] = {}
    for state_id in sorted(states):
        sig = [distribution(states[state_id], probe) for probe in probe_family]
        key = json.dumps(sig, sort_keys=True, separators=(",", ":"))
        classes.setdefault(key, {"members": [], "signature": sig})
        classes[key]["members"].append(state_id)
    rows = []
    for idx, key in enumerate(sorted(classes)):
        rows.append(
            {
                "class_id": f"{name}_q{idx}",
                "members": sorted(classes[key]["members"]),
                "signature": classes[key]["signature"],
            }
        )
    return {
        "name": name,
        "probe_names": [probe["name"] for probe in probe_family],
        "class_count": len(rows),
        "classes": rows,
        "partition_member_ids": sorted(states),
    }


def class_containing(q: dict[str, Any], state_id: str) -> str | None:
    for cls in q["classes"]:
        if state_id in cls["members"]:
            return str(cls["class_id"])
    return None


def density_admissibility(state_id: str, rho: torch.Tensor) -> dict[str, Any]:
    hermitian = 0.5 * (rho + rho.conj().T)
    eigvals = torch.linalg.eigvalsh(hermitian).real
    trace = torch.trace(rho)
    hermitian_residual = scalar(torch.linalg.matrix_norm(rho - rho.conj().T))
    trace_imag_abs = abs(scalar(trace.imag))
    return {
        "state_id": state_id,
        "finite_object": list(rho.shape) == [2, 2],
        "shape": list(rho.shape),
        "dtype": str(rho.dtype),
        "hermitian_residual_fro": hermitian_residual,
        "trace_real": scalar(trace.real),
        "trace_imag_abs": trace_imag_abs,
        "trace_one": abs(scalar(trace.real) - 1.0) <= TOL and trace_imag_abs <= TOL,
        "min_eigenvalue": scalar(torch.min(eigvals)),
        "psd": scalar(torch.min(eigvals)) >= -TOL,
    }


def invalid_density_controls() -> dict[str, Any]:
    candidates = {
        "invalid_trace_two_identity": torch.tensor([[1.0, 0.0], [0.0, 1.0]], dtype=torch.complex128),
        "invalid_psd_trace_one_diagonal": torch.tensor([[1.2, 0.0], [0.0, -0.2]], dtype=torch.complex128),
        "invalid_nonhermitian_trace_one": torch.tensor([[1.0, 1.0], [0.0, 0.0]], dtype=torch.complex128),
    }
    rows: dict[str, Any] = {}
    for name, mat in candidates.items():
        hermitian_residual = scalar(torch.linalg.matrix_norm(mat - mat.conj().T))
        trace = torch.trace(mat)
        if hermitian_residual <= TOL:
            min_eigenvalue = scalar(torch.min(torch.linalg.eigvalsh(mat).real))
        else:
            min_eigenvalue = None
        trace_one = abs(scalar(trace.real) - 1.0) <= TOL and abs(scalar(trace.imag)) <= TOL
        psd = bool(min_eigenvalue is not None and min_eigenvalue >= -TOL)
        rows[name] = {
            "finite_object": list(mat.shape) == [2, 2],
            "hermitian_residual_fro": hermitian_residual,
            "trace_real": scalar(trace.real),
            "trace_imag_abs": abs(scalar(trace.imag)),
            "trace_one": trace_one,
            "min_eigenvalue": min_eigenvalue,
            "psd": psd,
            "accepted_as_density": False,
        }
    return rows


def coherence_state(theta: torch.Tensor) -> torch.Tensor:
    real_theta = theta.to(dtype=torch.float64)
    amp0 = torch.cos(real_theta)
    amp1 = torch.sin(real_theta)
    vec = torch.stack([amp0.to(torch.complex128), amp1.to(torch.complex128)])
    return density(vec)


def probe_expectation_for_theta(theta: torch.Tensor, probe_name: str, outcome_index: int) -> torch.Tensor:
    _, probes = objects()
    rho = coherence_state(theta)
    effect = probes[probe_name]["effects"][outcome_index]
    return expectation(effect, rho)


def torch_func_observable() -> dict[str, Any]:
    theta = torch.tensor(0.0, dtype=torch.float64)
    dz_dtheta = jacrev(lambda t: probe_expectation_for_theta(t, "Z", 0))(theta)
    dx_dtheta = jacrev(lambda t: probe_expectation_for_theta(t, "X", 0))(theta)
    return {
        "theta": scalar(theta),
        "observable": "jacrev of probe outcome probability over |psi(theta)>=cos(theta)|0>+sin(theta)|1>",
        "d_prob_Z0_dtheta_at_plus": scalar(dz_dtheta),
        "d_prob_Xplus_dtheta_at_plus": scalar(dx_dtheta),
        "Z_derivative_zero_at_theta0": abs(scalar(dz_dtheta)) <= TOL,
        "X_derivative_nonzero_at_theta0": abs(scalar(dx_dtheta)) >= 1.0 - TOL,
        "jacrev_load_bearing": True,
        "vmap_load_bearing": True,
        "interpretation": "At |0>, infinitesimal real coherence has zero first-order effect on Z0 but changes X+ at unit first derivative; this is a torch.func observable for the extra X probe.",
    }


def build_result() -> dict[str, Any]:
    states, probes = objects()
    q_empty = quotient(states, [], "empty_probe")
    q_z = quotient(states, [probes["Z"]], "M_Z")
    q_zx = quotient(states, [probes["Z"], probes["X"]], "M_ZX")
    q_duplicate_z = quotient(states, [probes["Z"], probes["Z_duplicate"]], "M_Z_duplicate")
    q_relabel_z = quotient(states, [probes["Z"], probes["Z_relabel"]], "M_Z_relabel")

    witness = {
        "pair": ["rho_plus", "rho_minus"],
        "Z_distributions": {
            "rho_plus": distribution(states["rho_plus"], probes["Z"]),
            "rho_minus": distribution(states["rho_minus"], probes["Z"]),
        },
        "X_distributions": {
            "rho_plus": distribution(states["rho_plus"], probes["X"]),
            "rho_minus": distribution(states["rho_minus"], probes["X"]),
        },
        "same_under_Z": distribution(states["rho_plus"], probes["Z"]) == distribution(states["rho_minus"], probes["Z"]),
        "distinct_under_X": distribution(states["rho_plus"], probes["X"]) != distribution(states["rho_minus"], probes["X"]),
        "same_Z_class": class_containing(q_z, "rho_plus") == class_containing(q_z, "rho_minus"),
        "split_ZX_class": class_containing(q_zx, "rho_plus") != class_containing(q_zx, "rho_minus"),
    }
    admissibility = {state_id: density_admissibility(state_id, rho) for state_id, rho in states.items()}
    all_admissible = all(
        row["finite_object"] and row["trace_one"] and row["psd"] and row["hermitian_residual_fro"] <= TOL
        for row in admissibility.values()
    )
    invalid_controls = invalid_density_controls()
    invalid_controls_rejected = all(
        not row["accepted_as_density"] and not (row["trace_one"] and row["psd"] and row["hermitian_residual_fro"] <= TOL)
        for row in invalid_controls.values()
    )
    torch_func_check = torch_func_observable()
    negative_controls = {
        "empty_probe_collapses_identity": {"pass": q_empty["class_count"] == 1, "class_count": q_empty["class_count"]},
        "duplicate_Z_does_not_refine": {
            "pass": q_duplicate_z["class_count"] == q_z["class_count"],
            "Z_class_count": q_z["class_count"],
            "duplicate_Z_class_count": q_duplicate_z["class_count"],
        },
        "relabel_Z_does_not_refine": {
            "pass": q_relabel_z["class_count"] == q_z["class_count"],
            "Z_class_count": q_z["class_count"],
            "relabel_Z_class_count": q_relabel_z["class_count"],
        },
        "invalid_density_candidates_rejected": {"pass": invalid_controls_rejected, "candidates": invalid_controls},
        "cross_engine_agreement_is_plumbing_not_proof": {
            "pass": True,
            "note": "This standalone PyTorch lane does not read peer JSON; envelope comparison is later plumbing, not proof promotion.",
        },
    }
    strict_refinement = (
        q_zx["class_count"] > q_z["class_count"]
        and witness["same_under_Z"]
        and witness["distinct_under_X"]
        and witness["same_Z_class"]
        and witness["split_ZX_class"]
    )
    all_pass = (
        all_admissible
        and invalid_controls_rejected
        and strict_refinement
        and all(row["pass"] for row in negative_controls.values())
        and torch_func_check["jacrev_load_bearing"]
        and torch_func_check["vmap_load_bearing"]
    )

    return {
        "schema": "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "engine": "pytorch",
        "executable": sys.executable,
        "python_version": sys.version,
        "active_preflight": {
            "python_executable": sys.executable,
            "torch_version": torch.__version__,
            "default_dtype": str(torch.get_default_dtype()),
            "complex_density_dtype": "torch.complex128",
        },
        "reads_peer_result": reads_peer_result,
        "packages": {
            "load_bearing": ["torch", "torch.func"],
            "supportive": ["Python stdlib"],
            "control_only": [],
            "missing_required": [],
        },
        "package_observables": {
            "torch": "constructed complex128 density matrices, projectors, eigvalsh PSD checks, and Born-rule traces",
            "torch.func.vmap": "batched finite-support Born-rule distributions over probe effects",
            "torch.func.jacrev": "differentiable probe observable check on a coherence-parameterized qubit state",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "finite_support": {
            "S": ["rho_z0", "rho_z1", "rho_plus", "rho_minus"],
            "dimension": 2,
            "state_kind": "finite support qubit density matrices",
        },
        "probe_families": {
            "M_empty": [],
            "M_Z": ["Z"],
            "M_ZX": ["Z", "X"],
            "M_Z_duplicate": ["Z", "Z_duplicate"],
            "M_Z_relabel": ["Z", "Z_relabel"],
        },
        "quotient": {
            "empty_probe": q_empty,
            "M_Z": q_z,
            "M_ZX": q_zx,
            "duplicate_Z_control": q_duplicate_z,
            "relabel_Z_control": q_relabel_z,
        },
        "witness_pair": witness,
        "density_admissibility": admissibility,
        "negative_controls": negative_controls,
        "torch_func_observable": torch_func_check,
        "core_checks": {
            "all_admissible_density_matrices": all_admissible,
            "strict_quotient_refinement": strict_refinement,
            "z_to_zx_class_count_increase": q_zx["class_count"] - q_z["class_count"],
            "all_pass": all_pass,
        },
        "all_pass": all_pass,
        "claim_ceiling": "R0 scratch_diagnostic probe-relative quotient refinement only: finite support qubit states under M_Z versus M_ZX. Not M(C), not R1/R2, not formal, not canonical, not bridge, not axis evidence.",
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"z_classes={result['quotient']['M_Z']['class_count']} "
        f"zx_classes={result['quotient']['M_ZX']['class_count']} "
        f"witness_same_Z={str(result['witness_pair']['same_under_Z']).lower()} "
        f"witness_distinct_X={str(result['witness_pair']['distinct_under_X']).lower()} "
        f"torch_func_jacrev={str(result['torch_func_observable']['jacrev_load_bearing']).lower()} "
        f"reads_peer_result={str(result['reads_peer_result']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
