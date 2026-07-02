#!/usr/bin/env python3
"""Clean-room rebuild 004: Xi -> rho_AB bridge family.

This rebuilds a minimal geometry/history-to-cut-state family from read-only
Axis0/QIT source docs. It does not read contaminated formal receipts and does
not admit final Xi, Phi0, or Axis0.

Tested bridge forms:

* product_control: rho_A tensor rho_B with no cut correlation;
* point_reference: current geometry sample entangled with a fixed reference;
* shell_cut: weighted torus-shell references;
* history_window: current sample entangled with the previous history sample.

The expected clean behavior is modest:

* product controls have zero cut information;
* fiber history is density-stationary and should not create history-window cut
  information;
* lifted-base history traverses density states and should create a nonzero
  history-window cut signal;
* point-reference is fiber-constant but base-varying;
* shell-cut is finite support evidence, not final admission.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "rebuild_004_xi_rho_ab_bridge_family_from_readonly_results.json"

classification = "clean_rebuild_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical_clean_rebuild"
SOURCE_ALIGNMENT_CATEGORY = "xi_rho_ab_bridge_family_readonly_rebuild"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Clean rebuild scout only: tests a minimal Xi -> rho_AB bridge family "
    "against fiber/base and product controls. It does not admit final Xi, "
    "Phi0, Axis0, shell/history unification, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite spinor states, two-qubit cut states, partial traces, entropy, and bridge-family controls",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive clean rebuild receipt serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

DTYPE = torch.float64
CDTYPE = torch.complex128
EPS = 1e-12
TWO_PI = 2.0 * math.pi

I2 = torch.eye(2, dtype=CDTYPE)
I4 = torch.eye(4, dtype=CDTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
XX = torch.kron(SX, SX)
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


def normalize(v: torch.Tensor) -> torch.Tensor:
    return v / torch.clamp(torch.linalg.vector_norm(v), min=EPS)


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return normalize(
        torch.tensor(
            [
                complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
                complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
            ],
            dtype=CDTYPE,
        )
    )


def density(psi: torch.Tensor) -> torch.Tensor:
    rho = torch.outer(psi, torch.conj(psi))
    return (rho + torch.conj(rho).T) / 2.0


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + torch.conj(rho).T) / 2.0).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.sum(vals)
    nz = vals[vals > EPS]
    return float((-torch.sum(nz * torch.log(nz))).item())


def partial_trace_a(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abcb->ac", rho_ab.reshape(2, 2, 2, 2))


def partial_trace_b(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abad->bd", rho_ab.reshape(2, 2, 2, 2))


def cut_readouts(rho_ab: torch.Tensor) -> dict[str, float]:
    rho_a = partial_trace_b(rho_ab)
    rho_b = partial_trace_a(rho_ab)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    s_ab = entropy(rho_ab)
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "conditional_entropy_A_given_B": s_ab - s_b,
        "coherent_information_A_to_B": s_b - s_ab,
        "mutual_information": s_a + s_b - s_ab,
    }


def product_cut(psi_a: torch.Tensor, psi_b: torch.Tensor) -> torch.Tensor:
    return density(torch.kron(psi_a, psi_b))


def entangler(theta: float, generator: torch.Tensor = XX) -> torch.Tensor:
    return math.cos(theta / 2.0) * I4 - 1j * math.sin(theta / 2.0) * generator


def fubini_theta(psi_a: torch.Tensor, psi_b: torch.Tensor, scale: float = 1.10) -> float:
    overlap = torch.abs(torch.dot(torch.conj(psi_a), psi_b)).item()
    overlap = max(0.0, min(1.0, overlap))
    return scale * math.sqrt(max(0.0, 1.0 - overlap * overlap))


def entangled_cut(psi_a: torch.Tensor, psi_b: torch.Tensor, theta: float | None = None) -> torch.Tensor:
    if theta is None:
        theta = fubini_theta(psi_a, psi_b)
    u = entangler(theta)
    psi = u @ torch.kron(psi_a, psi_b)
    return density(normalize(psi))


def path_spinors(path: str, phi0: float, chi0: float, eta: float, steps: int = 24) -> list[torch.Tensor]:
    out = []
    for idx in range(steps):
        u = TWO_PI * idx / steps
        if path == "fiber":
            out.append(spinor(phi0 + u, chi0, eta))
        elif path == "lifted_base":
            out.append(spinor(phi0 - math.cos(2.0 * eta) * u, chi0 + u, eta))
        else:
            raise ValueError(path)
    return out


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values))


def span(values: list[float]) -> float:
    return float(max(values) - min(values))


def xi_product_control(samples: list[torch.Tensor], reference: torch.Tensor) -> list[dict[str, float]]:
    return [cut_readouts(product_cut(sample, reference)) for sample in samples]


def xi_point_reference(samples: list[torch.Tensor], reference: torch.Tensor) -> list[dict[str, float]]:
    return [cut_readouts(entangled_cut(sample, reference)) for sample in samples]


def xi_history_window(samples: list[torch.Tensor]) -> list[dict[str, float]]:
    rows = []
    for idx, sample in enumerate(samples):
        previous = samples[idx - 1]
        rows.append(cut_readouts(entangled_cut(sample, previous)))
    return rows


def xi_shell_cut(samples: list[torch.Tensor], phi0: float, eta: float, shell_size: int = 8) -> list[dict[str, float]]:
    refs = [spinor(phi0, TWO_PI * k / shell_size, eta) for k in range(shell_size)]
    rows = []
    for sample in samples:
        acc = torch.zeros((4, 4), dtype=CDTYPE)
        for ref in refs:
            acc = acc + entangled_cut(sample, ref) / shell_size
        rows.append(cut_readouts((acc + torch.conj(acc).T) / 2.0))
    return rows


def kernel_sanity_gate() -> dict[str, Any]:
    psi_a = spinor(0.10, 0.20, 0.35)
    psi_b = spinor(-0.31, 0.45, 0.66)
    product = cut_readouts(product_cut(psi_a, psi_b))
    bell = density(normalize(torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=CDTYPE)))
    bell_readouts = cut_readouts(bell)
    return {
        "pass": (
            abs(product["mutual_information"]) < 1e-10
            and abs(product["coherent_information_A_to_B"]) < 1e-10
            and abs(bell_readouts["coherent_information_A_to_B"] - math.log(2.0)) < 1e-10
            and abs(bell_readouts["mutual_information"] - 2.0 * math.log(2.0)) < 1e-10
        ),
        "source": "AXIS_0_1_2_QIT_MATH lines 17-23 and 143-147: cut-state entropy kernels require rho_AB",
        "product": product,
        "bell": bell_readouts,
    }


def bridge_family_gate() -> dict[str, Any]:
    phi0, chi0, eta = 0.17, 0.31, 0.44
    reference = spinor(-0.28, 0.79, math.pi / 4.0)
    fiber = path_spinors("fiber", phi0, chi0, eta)
    base = path_spinors("lifted_base", phi0, chi0, eta)
    families = {
        "product_fiber": xi_product_control(fiber, reference),
        "product_base": xi_product_control(base, reference),
        "point_reference_fiber": xi_point_reference(fiber, reference),
        "point_reference_base": xi_point_reference(base, reference),
        "history_window_fiber": xi_history_window(fiber),
        "history_window_base": xi_history_window(base),
        "shell_cut_fiber": xi_shell_cut(fiber, phi0, eta),
        "shell_cut_base": xi_shell_cut(base, phi0, eta),
    }
    summary = {}
    for name, rows in families.items():
        ic_values = [row["coherent_information_A_to_B"] for row in rows]
        mi_values = [row["mutual_information"] for row in rows]
        summary[name] = {
            "mean_Ic": mean(ic_values),
            "span_Ic": span(ic_values),
            "mean_MI": mean(mi_values),
            "span_MI": span(mi_values),
        }
    product_floor = max(abs(summary["product_fiber"]["mean_MI"]), abs(summary["product_base"]["mean_MI"]))
    point_fiber_span = summary["point_reference_fiber"]["span_Ic"]
    point_base_span = summary["point_reference_base"]["span_Ic"]
    history_fiber_mean = abs(summary["history_window_fiber"]["mean_Ic"])
    history_base_mean = summary["history_window_base"]["mean_Ic"]
    shell_finite = summary["shell_cut_fiber"]["mean_MI"] > 0.0 and summary["shell_cut_base"]["mean_MI"] > 0.0
    return {
        "pass": (
            product_floor < 1e-10
            and point_fiber_span < 1e-10
            and point_base_span > 1e-3
            and history_fiber_mean < 1e-10
            and history_base_mean > 1e-4
            and shell_finite
        ),
        "source": "AXIS_0_1_2_QIT_MATH lines 101-120 and 219-223: point, shell, and history bridge families are live but open",
        "summary": summary,
        "product_floor_MI": product_floor,
        "point_reference_base_span_Ic": point_base_span,
        "history_window_base_mean_Ic": history_base_mean,
        "shell_cut_is_finite_support": shell_finite,
    }


def axis0_nonadmission_gate(bridge: dict[str, Any]) -> dict[str, Any]:
    summary = bridge["summary"]
    live_candidates = [
        name
        for name, stats in summary.items()
        if name not in {"product_fiber", "product_base"} and stats["mean_MI"] > 1e-6
    ]
    return {
        "pass": len(live_candidates) >= 4,
        "live_candidate_count": len(live_candidates),
        "live_candidates": live_candidates,
        "admission": "blocked",
        "reason": (
            "Multiple Xi families are live and role-distinct. This rebuild proves "
            "the bridge family can be rerun cleanly, not that one Xi/Phi0 formula "
            "is final."
        ),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    kernel = kernel_sanity_gate()
    bridge = bridge_family_gate()
    nonadmission = axis0_nonadmission_gate(bridge)
    sections = {
        "kernel_sanity_gate": kernel,
        "bridge_family_gate": bridge,
        "axis0_nonadmission_gate": nonadmission,
    }
    all_pass = all(bool(section["pass"]) for section in sections.values())
    result = {
        "schema": "clean_rebuild_result_v1",
        "name": "rebuild_004_xi_rho_ab_bridge_family_from_readonly",
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
        "xi_status": {
            "bridge_family_rebuilt": bool(bridge["pass"]),
            "final_xi_admitted": False,
            "final_phi0_admitted": False,
            "next_required_test": "rebuild QIT-FEP/path-history Axis0 candidate batch against these clean Xi families",
        },
        "source_boundary": {
            "reads_formal_scout_results": False,
            "reads_grok_sim": False,
            "reads_external_audits": False,
            "reads_cross_lane_synthesis_docs": False,
            "primary_reference_docs": [
                "system_v5/READ ONLY Reference Docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md",
                "system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md",
                "system_v5/READ ONLY Reference Docs/QIT_ENGINE_GEOMETRY_ENTROPY_BRIDGE_MASTER_TABLE copy.md",
            ],
        },
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "out": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

