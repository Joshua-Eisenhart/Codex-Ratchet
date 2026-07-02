#!/usr/bin/env python3
"""PyTorch mirror for the ER=EPR Hopf-linking log-negativity scout.

Formal scout only. This is a finite QIT receipt for the owner's corrected
object: an A-C EPR link is treated as the ER=EPR connection, and the load-bearing
readout is log-negativity across the A|C cut. The matched unlinked control keeps
the same total count of EPR pairs but routes correlation through B, so A and C
are separable and LN(A:C)=0.

This file is intentionally PyTorch-native: no NumPy import and no tensor.numpy()
escape. It compares its result against the earlier NumPy scout receipt as a
backend mirror, but the local computation is torch complex128 throughout.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
NAME = "erepr_hopf_linking_lognegativity_spinor_network_pytorch_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
COMPARISON_SOURCE_PATH = (
    RESULT_DIR / "erepr_hopf_linking_lognegativity_spinor_network_probe_results.json"
)

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: PyTorch mirror for finite ER=EPR A-C log-negativity "
    "controls. It compares to the earlier NumPy scout receipt, while full Hopf "
    "S3-to-S2 fiber topology, PEPS3D carrier, layer, Axis0, FEP, flux, physics, "
    "gravity, bridge, and final manifold consumers remain locked."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex128 statevectors, reduced density matrices, partial transpose spectra, and QIT entropies",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive result and comparison receipt serialization",
    },
    "python_pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical result path handling",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source hash pinning for freshness",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "python_json": "supportive",
    "python_pathlib": "supportive",
    "hashlib": "supportive",
}

CDTYPE = torch.complex128
RTYPE = torch.float64
LN_MIN = 0.05
SEP_MAX = 1e-9
SCALE_GRID = [
    {"name": "small", "n_reg": 2, "n_blocks": 1},
    {"name": "medium", "n_reg": 2, "n_blocks": 2},
]
BLOCKED_CONSUMERS = [
    "full Hopf S3-to-S2 fiber topology consumer",
    "bond>=8 PEPS3D carrier consumer",
    "layer stacking",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics/gravity",
    "final manifold",
    "official G-structure selection",
]


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        if value.ndim == 0:
            return jsonable(value.item())
        return jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, (torch.dtype, pathlib.Path)):
        return str(value)
    return value


def source_sha256() -> str:
    return hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()


def vn_entropy(rho: torch.Tensor) -> float:
    rho = (rho + rho.conj().T) / 2
    ev = torch.linalg.eigvalsh(rho).real
    ev = torch.clamp(ev, min=0.0)
    total = torch.sum(ev)
    if float(total.item()) <= 1e-15:
        return 0.0
    ev = ev / total
    live = ev[ev > 1e-12]
    if int(live.numel()) == 0:
        return 0.0
    return float((-torch.sum(live * torch.log2(live))).item())


def rdm(psi: torch.Tensor, keep: list[int], n_qubits: int) -> torch.Tensor:
    """Reduced density on keep, preserving keep order for A|C partial transpose."""
    keep = list(keep)
    traced = [i for i in range(n_qubits) if i not in keep]
    tensor = psi.reshape((2,) * n_qubits).permute(*(keep + traced))
    matrix = tensor.reshape(2 ** len(keep), 2 ** len(traced))
    return matrix @ matrix.conj().T


def rdm_dephased(psi: torch.Tensor, keep: list[int], n_qubits: int) -> torch.Tensor:
    """Reduced diagonal density of the fully dephased global state."""
    keep = list(keep)
    traced = [i for i in range(n_qubits) if i not in keep]
    probs = torch.abs(psi) ** 2
    tensor = probs.reshape((2,) * n_qubits).permute(*(keep + traced))
    marginal = tensor.reshape(2 ** len(keep), 2 ** len(traced)).sum(dim=1)
    return torch.diag(marginal).to(CDTYPE)


def entropy_of_state_or_dephased(
    psi: torch.Tensor, keep: list[int], n_qubits: int, dephased: bool
) -> float:
    if len(keep) >= n_qubits:
        if not dephased:
            return 0.0
        probs = torch.abs(psi) ** 2
        live = probs[probs > 1e-12]
        return float((-torch.sum(live * torch.log2(live))).item())
    rho = rdm_dephased(psi, keep, n_qubits) if dephased else rdm(psi, keep, n_qubits)
    return vn_entropy(rho)


def log_negativity_from_rdm(rho: torch.Tensor, d_a: int, d_c: int) -> float:
    partial_transpose = (
        rho.reshape(d_a, d_c, d_a, d_c)
        .permute(0, 3, 2, 1)
        .reshape(d_a * d_c, d_a * d_c)
    )
    hermitian = (partial_transpose + partial_transpose.conj().T) / 2
    ev = torch.linalg.eigvalsh(hermitian).real
    return float(torch.log2(torch.sum(torch.abs(ev))).item())


def log_negativity(
    psi: torch.Tensor,
    region_a: list[int],
    region_c: list[int],
    n_qubits: int,
    dephased: bool = False,
) -> float:
    rho = (
        rdm_dephased(psi, region_a + region_c, n_qubits)
        if dephased
        else rdm(psi, region_a + region_c, n_qubits)
    )
    return log_negativity_from_rdm(rho, 2 ** len(region_a), 2 ** len(region_c))


def conditional_mutual_information(
    psi: torch.Tensor,
    region_a: list[int],
    region_b: list[int],
    region_c: list[int],
    n_qubits: int,
    dephased: bool = False,
) -> float:
    return (
        entropy_of_state_or_dephased(psi, region_a + region_b, n_qubits, dephased)
        + entropy_of_state_or_dephased(psi, region_b + region_c, n_qubits, dephased)
        - entropy_of_state_or_dephased(psi, region_b, n_qubits, dephased)
        - entropy_of_state_or_dephased(psi, region_a + region_b + region_c, n_qubits, dephased)
    )


def mutual_information(
    psi: torch.Tensor,
    region_x: list[int],
    region_y: list[int],
    n_qubits: int,
    dephased: bool = False,
) -> float:
    return (
        entropy_of_state_or_dephased(psi, region_x, n_qubits, dephased)
        + entropy_of_state_or_dephased(psi, region_y, n_qubits, dephased)
        - entropy_of_state_or_dephased(psi, region_x + region_y, n_qubits, dephased)
    )


def tripartite_information(
    psi: torch.Tensor,
    region_a: list[int],
    region_b: list[int],
    region_c: list[int],
    n_qubits: int,
    dephased: bool = False,
) -> float:
    return (
        mutual_information(psi, region_a, region_b, n_qubits, dephased)
        + mutual_information(psi, region_a, region_c, n_qubits, dephased)
        - mutual_information(psi, region_a, region_b + region_c, n_qubits, dephased)
    )


def regions(n_reg: int, base: int = 0) -> tuple[list[int], list[int], list[int]]:
    return (
        [base + i for i in range(0, n_reg)],
        [base + i for i in range(n_reg, 2 * n_reg)],
        [base + i for i in range(2 * n_reg, 3 * n_reg)],
    )


def two_bell(i: int, j: int, k: int, l: int, n_qubits: int) -> torch.Tensor:
    state = torch.zeros((2,) * n_qubits, dtype=CDTYPE)
    for a_bit in (0, 1):
        for b_bit in (0, 1):
            idx = [0] * n_qubits
            idx[i] = a_bit
            idx[j] = a_bit
            idx[k] = b_bit
            idx[l] = b_bit
            state[tuple(idx)] += 1.0
    return state.reshape(-1) / 2.0


def linked_block(n_reg: int) -> torch.Tensor:
    n_qubits = 3 * n_reg
    region_a, region_b, region_c = regions(n_reg)
    return two_bell(region_a[-1], region_c[0], region_a[0], region_b[0], n_qubits)


def trivial_block(n_reg: int) -> torch.Tensor:
    n_qubits = 3 * n_reg
    region_a, region_b, region_c = regions(n_reg)
    return two_bell(region_a[0], region_b[0], region_b[1], region_c[0], n_qubits)


def tensor_product(states: list[torch.Tensor]) -> torch.Tensor:
    out = states[0]
    for state in states[1:]:
        out = torch.kron(out, state)
    return out / torch.linalg.vector_norm(out)


def zero_state(n_qubits: int) -> torch.Tensor:
    state = torch.zeros(2**n_qubits, dtype=CDTYPE)
    state[0] = 1.0
    return state


def local_phase_gauge(psi: torch.Tensor, n_qubits: int, phase_scale: float = 0.031) -> torch.Tensor:
    """Apply a product of local Z phases. Entanglement readouts should not move."""
    idx = torch.arange(psi.numel(), dtype=torch.int64)
    phase = torch.ones(psi.numel(), dtype=CDTYPE)
    for q in range(n_qubits):
        bit = ((idx >> (n_qubits - 1 - q)) & 1).to(torch.bool)
        local = torch.exp(torch.tensor(1j * phase_scale * (q + 1), dtype=CDTYPE))
        phase = torch.where(bit, phase * local, phase)
    return psi * phase


def readout_columns(
    psi: torch.Tensor,
    region_a: list[int],
    region_b: list[int],
    region_c: list[int],
    n_qubits: int,
    dephased: bool = False,
) -> dict[str, float]:
    return {
        "LN_AC": log_negativity(psi, region_a, region_c, n_qubits, dephased),
        "I_ACgivenB_classical_shadow": conditional_mutual_information(
            psi, region_a, region_b, region_c, n_qubits, dephased
        ),
        "I3_classical_shadow": tripartite_information(
            psi, region_a, region_b, region_c, n_qubits, dephased
        ),
    }


def canonical_self_tests() -> dict[str, Any]:
    n_qubits = 6
    region_a, region_b, region_c = [0, 1], [2, 3], [4, 5]
    linked = linked_block(2)
    trivial = trivial_block(2)
    product = zero_state(n_qubits)
    ln_linked = log_negativity(linked, region_a, region_c, n_qubits)
    ln_trivial = log_negativity(trivial, region_a, region_c, n_qubits)
    ln_product = log_negativity(product, region_a, region_c, n_qubits)
    ln_dephased = log_negativity(linked, region_a, region_c, n_qubits, dephased=True)
    ln_phase = log_negativity(local_phase_gauge(linked, n_qubits), region_a, region_c, n_qubits)
    return {
        "LN_linked": ln_linked,
        "LN_trivial": ln_trivial,
        "LN_product": ln_product,
        "LN_dephased": ln_dephased,
        "LN_local_phase_gauge": ln_phase,
        "pass": bool(
            ln_linked > 0.5
            and abs(ln_trivial) < SEP_MAX
            and abs(ln_product) < SEP_MAX
            and abs(ln_dephased) < SEP_MAX
            and abs(ln_phase - ln_linked) < SEP_MAX
        ),
    }


def scale_row(grid: dict[str, Any]) -> dict[str, Any]:
    n_reg = int(grid["n_reg"])
    n_blocks = int(grid["n_blocks"])
    block_qubits = 3 * n_reg
    n_qubits = block_qubits * n_blocks
    linked = tensor_product([linked_block(n_reg)] * n_blocks)
    trivial = tensor_product([trivial_block(n_reg)] * n_blocks)
    product = zero_state(n_qubits)
    phase_linked = local_phase_gauge(linked, n_qubits)

    region_a = [b * block_qubits + i for b in range(n_blocks) for i in range(0, n_reg)]
    region_b = [
        b * block_qubits + i for b in range(n_blocks) for i in range(n_reg, 2 * n_reg)
    ]
    region_c = [
        b * block_qubits + i for b in range(n_blocks) for i in range(2 * n_reg, 3 * n_reg)
    ]

    linked_cols = readout_columns(linked, region_a, region_b, region_c, n_qubits)
    trivial_cols = readout_columns(trivial, region_a, region_b, region_c, n_qubits)
    product_cols = readout_columns(product, region_a, region_b, region_c, n_qubits)
    dephased_cols = readout_columns(
        linked, region_a, region_b, region_c, n_qubits, dephased=True
    )
    phase_cols = readout_columns(phase_linked, region_a, region_b, region_c, n_qubits)

    ent_linked = sum(vn_entropy(rdm(linked, [q], n_qubits)) for q in range(n_qubits))
    ent_trivial = sum(vn_entropy(rdm(trivial, [q], n_qubits)) for q in range(n_qubits))
    self_tests = canonical_self_tests()

    linking_signal = linked_cols["LN_AC"] > LN_MIN
    geometry_kill = abs(trivial_cols["LN_AC"]) < SEP_MAX
    product_kill = abs(product_cols["LN_AC"]) < SEP_MAX
    dephasing_kill = abs(dephased_cols["LN_AC"]) < SEP_MAX
    entanglement_matched = abs(ent_linked - ent_trivial) < 1e-6
    phase_gauge_safe = abs(phase_cols["LN_AC"] - linked_cols["LN_AC"]) < 1e-9
    row_pass = bool(
        linking_signal
        and geometry_kill
        and product_kill
        and dephasing_kill
        and entanglement_matched
        and phase_gauge_safe
        and self_tests["pass"]
    )
    return {
        "pass": row_pass,
        "scale_name": str(grid["name"]),
        "n_qubits": n_qubits,
        "geometry_scale": {"n_reg": n_reg, "n_blocks": n_blocks, "n_qubits": n_qubits},
        "linked": linked_cols,
        "trivial_matched": trivial_cols,
        "product": product_cols,
        "dephased_linked": dephased_cols,
        "local_phase_gauge_linked": phase_cols,
        "total_single_site_entropy_linked": ent_linked,
        "total_single_site_entropy_trivial": ent_trivial,
        "canonical_self_tests": self_tests,
        "root_constraints": {
            "F01_finite": True,
            "N01_nonclassical_control": bool(dephasing_kill and phase_gauge_safe),
            "note": "finite density-matrix readout; signal dies under commuting dephasing and is invariant under local phase gauge",
        },
        "controls": {
            "linked_ac_lognegativity_positive": {
                "pass": bool(linking_signal),
                "LN_AC": linked_cols["LN_AC"],
            },
            "matched_unlinked_chain_geometry_kill": {
                "pass": bool(geometry_kill),
                "LN_AC": trivial_cols["LN_AC"],
                "note": "same two-EPR-pair budget per block, but no direct A-C EPR link",
            },
            "product_information_kill": {
                "pass": bool(product_kill),
                "LN_AC": product_cols["LN_AC"],
            },
            "commuting_dephasing_kills_quantum_signal": {
                "pass": bool(dephasing_kill),
                "LN_AC": dephased_cols["LN_AC"],
            },
            "entanglement_budget_matched": {
                "pass": bool(entanglement_matched),
                "linked": ent_linked,
                "trivial": ent_trivial,
            },
            "local_phase_gauge_invariance": {
                "pass": bool(phase_gauge_safe),
                "linked_LN_AC": linked_cols["LN_AC"],
                "phase_LN_AC": phase_cols["LN_AC"],
            },
            "canonical_state_self_tests": self_tests,
        },
    }


def comparison_receipt(summary: dict[str, Any]) -> dict[str, Any]:
    if not COMPARISON_SOURCE_PATH.exists():
        return {
            "path": str(COMPARISON_SOURCE_PATH),
            "pass": False,
            "errors": ["comparison source result missing"],
        }
    try:
        source = json.loads(COMPARISON_SOURCE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "path": str(COMPARISON_SOURCE_PATH),
            "pass": False,
            "errors": [f"comparison source unreadable: {exc}"],
        }
    other = source.get("summary") or {}
    numeric_keys = [
        "min_linked_LN_AC",
        "max_trivial_LN_AC",
        "max_dephased_LN_AC",
        "max_n_qubits",
    ]
    deltas: dict[str, float] = {}
    errors: list[str] = []
    for key in numeric_keys:
        if key not in other or key not in summary:
            errors.append(f"missing comparison key {key}")
            continue
        deltas[key] = abs(float(summary[key]) - float(other[key]))
    bool_checks = {
        "source_summary_all_pass": bool(other.get("all_pass") is True),
        "source_canonical_self_tests_pass": bool(other.get("canonical_self_tests_pass") is True),
        "pytorch_canonical_self_tests_pass": bool(
            summary.get("canonical_self_tests_pass") is True
        ),
    }
    numeric_pass = all(delta < 1e-9 for delta in deltas.values()) and not errors
    all_pass = bool(numeric_pass and all(bool_checks.values()))
    return {
        "path": str(COMPARISON_SOURCE_PATH),
        "source_schema": source.get("schema"),
        "numeric_deltas": deltas,
        "bool_checks": bool_checks,
        "errors": errors,
        "pass": all_pass,
        "note": "comparison is against the earlier NumPy scout receipt; PyTorch remains the local load-bearing substrate here",
    }


def main() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [scale_row(grid) for grid in SCALE_GRID]
    min_linked = min(row["linked"]["LN_AC"] for row in rows)
    max_trivial = max(abs(row["trivial_matched"]["LN_AC"]) for row in rows)
    max_product = max(abs(row["product"]["LN_AC"]) for row in rows)
    max_dephased = max(abs(row["dephased_linked"]["LN_AC"]) for row in rows)
    max_phase_delta = max(
        abs(row["local_phase_gauge_linked"]["LN_AC"] - row["linked"]["LN_AC"])
        for row in rows
    )
    max_n_qubits = max(row["n_qubits"] for row in rows)
    canonical_ok = all(row["controls"]["canonical_state_self_tests"]["pass"] for row in rows)

    provisional_summary = {
        "all_pass": False,
        "promotion_allowed": PROMOTION_ALLOWED,
        "elapsed_seconds": round(time.time() - started, 6),
        "max_n_qubits": max_n_qubits,
        "min_linked_LN_AC": min_linked,
        "max_trivial_LN_AC": max_trivial,
        "max_product_LN_AC": max_product,
        "max_dephased_LN_AC": max_dephased,
        "max_local_phase_gauge_LN_delta": max_phase_delta,
        "canonical_self_tests_pass": canonical_ok,
    }
    comparison = comparison_receipt(provisional_summary)
    required = {
        "rows_pass": all(row["pass"] for row in rows),
        "linking_lognegativity_pass": min_linked > LN_MIN,
        "geometry_kill_matched_pass": max_trivial < SEP_MAX,
        "info_kill_product_pass": max_product < SEP_MAX,
        "dephasing_pure_qit_pass": max_dephased < SEP_MAX,
        "local_phase_gauge_pass": max_phase_delta < SEP_MAX,
        "entanglement_matched_pass": all(
            row["controls"]["entanglement_budget_matched"]["pass"] for row in rows
        ),
        "canonical_self_tests_pass": canonical_ok,
        "backend_comparison_pass": bool(comparison["pass"]),
    }
    all_pass = bool(all(required.values()))
    summary = {
        **provisional_summary,
        "all_pass": all_pass,
        "elapsed_seconds": round(time.time() - started, 6),
        "scale_grid": [row["geometry_scale"] | {"name": row["scale_name"]} for row in rows],
        "carrier_role": "object_load_bearing_torch_statevector_reduced_density",
    }

    positive = {
        "pytorch_linked_ac_lognegativity_positive": {
            "pass": bool(required["linking_lognegativity_pass"]),
            "min_linked_LN_AC": min_linked,
        },
        "pytorch_backend_comparison_receipt_matches_numpy_scout": comparison,
        "local_phase_gauge_invariance_preserves_lognegativity": {
            "pass": bool(required["local_phase_gauge_pass"]),
            "max_LN_delta": max_phase_delta,
        },
    }
    graveyard_companions = {
        "matched_unlinked_chain_same_entanglement_budget_kills_ac_lognegativity": {
            "pass": bool(required["geometry_kill_matched_pass"]),
            "max_trivial_LN_AC": max_trivial,
        },
        "product_state_kills_ac_lognegativity": {
            "pass": bool(required["info_kill_product_pass"]),
            "max_product_LN_AC": max_product,
        },
        "dephased_commuting_negative_kills_quantum_signal": {
            "pass": bool(required["dephasing_pure_qit_pass"]),
            "max_dephased_LN_AC": max_dephased,
            "note": "dephasing turns the EPR link into a classical/separable diagonal state; log-negativity drops to zero",
        },
        "conditional_mutual_information_kept_as_classical_shadow_column": {
            "pass": True,
            "note": "I(A:C|B) and I3 are reported but are not load-bearing because classical variants exist",
        },
    }
    boundary = {
        "formal_scout_ceiling_blocks_downstream_consumers": {
            "pass": True,
            "promotion_allowed": PROMOTION_ALLOWED,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "torch_native_nonclassical_substrate_no_numpy_escape": {
            "pass": True,
            "sim_execution_kind": SIM_EXECUTION_KIND,
            "load_bearing_tool": "pytorch",
        },
        "not_full_hopf_or_peps3d_consumer": {
            "pass": True,
            "open_next_build": "wire real Hopf fiber/base topology on bond>=8 PEPS3D carrier, then rerun consumer gates",
        },
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "all_pass": all_pass,
        "claim_ceiling": CLAIM_CEILING,
        "source_sha256": source_sha256(),
        "math_object": "finite torch density-matrix readout: log-negativity LN(A:C) over an ER=EPR A-C link in a three-region spinor-network scout",
        "finite_map": "torch statevector -> reduced rho_AC -> partial transpose spectrum -> log2 trace norm",
        "root_constraints_in_force": {
            "F01": "finite qubit carrier, finite A/B/C regions, finite reduced densities",
            "N01": "nonclassical control is enforced by dephasing kill plus local phase gauge invariance; classical/product/matched unlinked controls do not carry the LN(A:C) signal",
        },
        "carrier_role": "object_load_bearing_torch_statevector_reduced_density",
        "carrier_ceiling": "statevector/reduced-density formal scout; PEPS3D and full Hopf-coordinate consumers remain locked",
        "required": required,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(rows),
            "passed": sum(1 for row in rows if row["pass"]),
        },
        "why_not_v4_probes": [
            "The earlier CMI Hopf-linking scout has a classical-shadow readout and no accepted result receipt.",
            "The noncommuting iSWAP over-correction failed its own log-negativity controls.",
            "This PyTorch mirror still does not realize the full Hopf S3-to-S2 fiber/base topology on the bond>=8 PEPS3D carrier.",
        ],
        "blockers": [],
        "rows": rows,
        "backend_comparison_to_numpy_scout": comparison,
        "candidates_kept_separate": [
            "log_negativity(A:C) [load-bearing pure QIT readout]",
            "I(A:C|B) [reported classical-shadow column, not load-bearing]",
            "I3 [reported classical-shadow column, not load-bearing]",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": summary,
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    receipt = main()
    raise SystemExit(0 if receipt["all_pass"] else 1)
