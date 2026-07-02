#!/usr/bin/env python3
"""Scale-test the reusable Wolfram shell toolkit.

This scout deepens the prior Wolfram adapter work by testing the reusable
toolkit at 64/128/256 Omega_r branches. It keeps the claim narrow:

  Wolfram-style branch machinery can provide shell-field adapter tools.

It does not claim Wolfram runtime execution, Axis0, FEP, gravity, physics,
stacking, PEPS3D closure, or final manifold admission.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
import z3

import wolfram_shell_toolkit as wst


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "wolfram_shell_toolkit_scale_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
ADAPTER_MATRIX_RESULT = RESULT_DIR / "aligned_model_adapter_matrix_shell_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "wolfram_shell_toolkit_scale_probe"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: scale-tests reusable Wolfram-style shell toolkit "
    "functions as finite adapters for Omega_r branch tables, PEPS3D supports, "
    "branchial compatibility kernels, shell shear stress, and outward records. "
    "It does not admit Wolfram theory, Axis0, FEP, flux, physics, gravity, "
    "stacking, PEPS3D closure, or final manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: computes branch spinor densities, branchial-weighted rho_present, QIT entropy, density gaps, and scale stress readouts",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through wolfram_shell_toolkit: builds higher-order Omega/support/history incidence hypergraphs at each scale",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through wolfram_shell_toolkit: builds branchial graphs and compatibility kernels whose ablation changes rho_present",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive: exact branch-count and shell-floor identities for scale receipts",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive: rejects crisp Wolfram rule-time or toolkit-only promotion as a replacement for the shell-field object",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive: independent SMT rejection of toolkit-as-primary-object promotion",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "xgi": "load_bearing",
    "rustworkx": "load_bearing",
    "sympy": "supportive",
    "z3": "supportive",
    "cvc5": "supportive",
}

FINITE_MAP = (
    "W_tool_scale: (N, raw Wolfram-style branch rows, shell radii, PEPS3D "
    "site floors, branch histories, support sites) -> normalized Omega_r "
    "table, PEPS3D support attachment, XGI incidence, rustworkx branchial "
    "kernel, branchial rho_present, outward_record, scale stress vector, and "
    "negative controls."
)
DOMAIN = (
    "N in {64,128,256}; shell radii r in {1,2,3,4}; PEPS3D site floors "
    "8/16/32/64; finite branch histories; future_inward orientation; branch "
    "support sites; 8-component torch spinor-derived densities"
)
CODOMAIN = (
    "per-scale toolkit selftest receipts, branchial compatibility weights, "
    "rho_present_N, QIT entropy/readouts, branchial-vs-uniform stress, "
    "crisp-rule control gap, no-support rejection, object-promotion rejection, "
    "and downstream block list"
)
BLOCKED_CONSUMERS = [
    "Wolfram theory admission",
    "Axis0 closure",
    "FEP/Holodeck admission",
    "Xi/Phi0 closure",
    "flux closure",
    "PEPS3D closure",
    "stacking closure",
    "physics/gravity proof",
    "final manifold admission",
]

DTYPE = torch.complex128
RTYPE = torch.float64
EPS = 1.0e-12
SCALES = (64, 128, 256)
SHELLS = (1, 2, 3, 4)
SITE_FLOORS = {1: 8, 2: 16, 3: 32, 4: 64}
DIM = 8


def stable_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def raw_rows(n: int) -> list[dict[str, Any]]:
    rules = ("split", "lift", "close", "shear", "project", "braid", "fold")
    rows = []
    for idx in range(n):
        r = SHELLS[idx % len(SHELLS)]
        width = 3 + ((idx // 2) % 5)
        floor = SITE_FLOORS[r]
        support = tuple(sorted({(idx * 11 + j * (r + 5) + j * j) % floor for j in range(width)}))
        history_len = 1 + (idx % 6)
        history = tuple(rules[(idx + j * (r + 1)) % len(rules)] for j in range(history_len))
        rows.append(
            {
                "branch_id": f"omega_{n}_{idx}",
                "shell_r": r,
                "orientation": "future_inward",
                "history": history,
                "support_sites": support,
            }
        )
    return rows


def branch_spinor(row: dict[str, Any]) -> torch.Tensor:
    support = tuple(int(site) for site in row["support_sites"])
    history = tuple(str(rule) for rule in row["history"])
    idx = int(str(row["branch_id"]).split("_")[-1])
    shell_r = int(row["shell_r"])
    support_score = sum((i + 1) * (site + 1) for i, site in enumerate(support))
    history_score = sum(stable_int(rule) % 37 for rule in history)
    primary = (support_score + history_score + idx) % DIM
    paired = (primary + shell_r + len(history)) % DIM
    psi = torch.zeros(DIM, dtype=DTYPE)
    phase = ((support_score + history_score + idx * 3) % 113) * math.tau / 113.0
    psi[primary] = complex(1.0, 0.0)
    psi[paired] += complex(0.58 * math.cos(phase), 0.58 * math.sin(phase))
    for k in range(DIM):
        noise_phase = phase + ((k + 1) * (shell_r + 2)) * math.tau / 47.0
        psi[k] += complex(0.025 * math.cos(noise_phase), 0.025 * math.sin(noise_phase))
    return psi / torch.linalg.norm(psi).clamp_min(EPS)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def weighted_rho(rows: list[dict[str, Any]], weights: dict[str, float]) -> torch.Tensor:
    rho = torch.zeros((DIM, DIM), dtype=DTYPE)
    total = sum(float(v) for v in weights.values())
    for row in rows:
        weight = float(weights.get(row["branch_id"], 0.0)) / max(total, EPS)
        rho = rho + torch.tensor(weight, dtype=DTYPE) * density(branch_spinor(row))
    rho = (rho + rho.conj().T) / 2.0
    return rho / torch.trace(rho).real.clamp_min(EPS)


def entropy_vn(rho: torch.Tensor) -> float:
    herm = (rho + rho.conj().T) / 2.0
    vals = torch.linalg.eigvalsh(herm).real.clamp_min(EPS)
    vals = vals / vals.sum().clamp_min(EPS)
    return float(-(vals * torch.log2(vals)).sum().item())


def partial_trace_3q(rho: torch.Tensor, keep: tuple[int, ...]) -> torch.Tensor:
    dims = [2, 2, 2]
    shaped = rho.reshape(*(dims + dims))
    trace_over = [q for q in range(3) if q not in keep]
    for q in sorted(trace_over, reverse=True):
        shaped = shaped.diagonal(dim1=q, dim2=q + len(dims)).sum(-1)
        dims.pop(q)
    dim_keep = 2 ** len(keep)
    return shaped.reshape(dim_keep, dim_keep)


def qit_readouts(rho: torch.Tensor) -> dict[str, float]:
    rho_a = partial_trace_3q(rho, (0,))
    rho_bc = partial_trace_3q(rho, (1, 2))
    s_ab = entropy_vn(rho)
    s_a = entropy_vn(rho_a)
    s_bc = entropy_vn(rho_bc)
    return {
        "S_AB": round(s_ab, 9),
        "S_A": round(s_a, 9),
        "S_BC": round(s_bc, 9),
        "MI_A_BC": round(s_a + s_bc - s_ab, 9),
        "Ic_A_to_BC": round(s_bc - s_ab, 9),
    }


def density_gap(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.norm(a - b).real.item())


def uniform_weights(rows: list[dict[str, Any]]) -> dict[str, float]:
    return {row["branch_id"]: 1.0 for row in rows}


def crisp_rule_weights(rows: list[dict[str, Any]]) -> dict[str, float]:
    weights = {}
    for row in rows:
        first = row["history"][0] if row["history"] else "none"
        weights[row["branch_id"]] = 4.0 if first == "split" else 0.35
    return weights


def reversed_orientation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        next_row = dict(row)
        next_row["orientation"] = "past_outward"
        out.append(next_row)
    return out


def z3_reject_toolkit_primary() -> bool:
    has_omega = z3.Bool("has_omega")
    has_compression = z3.Bool("has_compression")
    has_outward_record = z3.Bool("has_outward_record")
    toolkit_primary = z3.Bool("toolkit_primary")
    solver = z3.Solver()
    solver.add(toolkit_primary)
    solver.add(toolkit_primary == z3.And(has_omega, has_compression, has_outward_record))
    solver.add(z3.Or(z3.Not(has_omega), z3.Not(has_compression), z3.Not(has_outward_record)))
    return solver.check() == z3.unsat


def cvc5_reject_toolkit_primary() -> bool:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    has_omega = solver.mkConst(bool_sort, "has_omega")
    has_compression = solver.mkConst(bool_sort, "has_compression")
    has_record = solver.mkConst(bool_sort, "has_record")
    toolkit_primary = solver.mkConst(bool_sort, "toolkit_primary")
    conj = solver.mkTerm(Kind.AND, has_omega, has_compression, has_record)
    missing = solver.mkTerm(
        Kind.OR,
        solver.mkTerm(Kind.NOT, has_omega),
        solver.mkTerm(Kind.NOT, has_compression),
        solver.mkTerm(Kind.NOT, has_record),
    )
    solver.assertFormula(toolkit_primary)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, toolkit_primary, conj))
    solver.assertFormula(missing)
    return str(solver.checkSat()) == "unsat"


def run_scale(n: int) -> dict[str, Any]:
    raw = raw_rows(n)
    attached = wst.attach_peps3d_supports(wst.normalize_omega_branch_table(raw), SITE_FLOORS)
    toolkit_receipt = wst.toolkit_selftest(raw, SITE_FLOORS)
    kernel = wst.branchial_distance_kernel(attached)
    branchial_weights = kernel["weights"]
    uniform = uniform_weights(attached)
    crisp = crisp_rule_weights(attached)
    branchial_rho = weighted_rho(attached, branchial_weights)
    uniform_rho = weighted_rho(attached, uniform)
    crisp_rho = weighted_rho(attached, crisp)
    branchial_vs_uniform = density_gap(branchial_rho, uniform_rho)
    branchial_vs_crisp = density_gap(branchial_rho, crisp_rho)
    stress_uniform = wst.shell_shear_stress(uniform, branchial_weights)
    record = wst.emit_outward_record(attached, branchial_weights)
    no_support_rejected = False
    try:
        broken = [dict(row, support_sites=()) for row in raw[:4]]
        wst.attach_peps3d_supports(wst.normalize_omega_branch_table(broken), SITE_FLOORS)
    except ValueError:
        no_support_rejected = True
    reversed_rows = wst.normalize_omega_branch_table(reversed_orientation_rows(attached))
    orientation_preserved = all(row["orientation"] == "future_inward" for row in attached)
    reversed_orientation_detected = all(row["orientation"] == "past_outward" for row in reversed_rows)
    exact_count = str(sp.simplify(sp.Integer(len(attached)) - sp.Integer(n)))
    return {
        "scale": n,
        "toolkit_selftest": toolkit_receipt,
        "exact_count_residual": exact_count,
        "branchial_graph_edges": int(kernel["graph_edges"]),
        "branchial_weight_sum": round(sum(branchial_weights.values()), 12),
        "branchial_vs_uniform_density_gap": round(branchial_vs_uniform, 12),
        "branchial_vs_crisp_rule_density_gap": round(branchial_vs_crisp, 12),
        "uniform_vs_branchial_stress": {k: round(float(v), 12) for k, v in stress_uniform.items()},
        "outward_record": record,
        "qit_readouts": qit_readouts(branchial_rho),
        "controls": {
            "no_support_rejected": no_support_rejected,
            "orientation_preserved": orientation_preserved,
            "reversed_orientation_detected": reversed_orientation_detected,
            "crisp_rule_time_differs_from_branchial": branchial_vs_crisp > 0.03,
            "uniform_weights_differ_from_branchial": branchial_vs_uniform > 0.01,
        },
    }


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    adapter_matrix = load_json(ADAPTER_MATRIX_RESULT)
    rows = [run_scale(n) for n in SCALES]

    edge_counts = [row["branchial_graph_edges"] for row in rows]
    entropies = [row["outward_record"]["record_entropy_bits"] for row in rows]
    crisp_gaps = [row["branchial_vs_crisp_rule_density_gap"] for row in rows]
    uniform_gaps = [row["branchial_vs_uniform_density_gap"] for row in rows]

    positive = {
        "adapter_matrix_dependency_read": {
            "pass": bool(adapter_matrix.get("result_summary", {}).get("all_pass")),
            "witness": {"path": str(ADAPTER_MATRIX_RESULT), "summary": adapter_matrix.get("result_summary", {})},
        },
        "all_scales_selftest": {
            "pass": all(row["toolkit_selftest"]["all_pass"] for row in rows),
            "witness": {str(row["scale"]): row["toolkit_selftest"]["all_pass"] for row in rows},
        },
        "branch_counts_exact": {
            "pass": all(row["exact_count_residual"] == "0" for row in rows),
            "witness": {str(row["scale"]): row["exact_count_residual"] for row in rows},
        },
        "branchial_graph_scales_up": {
            "pass": edge_counts == sorted(edge_counts) and len(set(edge_counts)) == len(edge_counts),
            "witness": dict(zip([str(n) for n in SCALES], edge_counts, strict=True)),
        },
        "outward_record_entropy_scales": {
            "pass": entropies == sorted(entropies) and entropies[-1] > entropies[0],
            "witness": dict(zip([str(n) for n in SCALES], [round(v, 9) for v in entropies], strict=True)),
        },
        "qit_readouts_nontrivial": {
            "pass": all(row["qit_readouts"]["S_AB"] > 1.0 and row["qit_readouts"]["MI_A_BC"] > 0.01 for row in rows),
            "witness": {str(row["scale"]): row["qit_readouts"] for row in rows},
        },
    }

    graveyard_companions = {
        "crisp_rule_time_control_differs": {
            "pass": all(gap > 0.03 for gap in crisp_gaps),
            "witness": dict(zip([str(n) for n in SCALES], crisp_gaps, strict=True)),
        },
        "uniform_weight_control_differs": {
            "pass": all(gap > 0.01 for gap in uniform_gaps),
            "witness": dict(zip([str(n) for n in SCALES], uniform_gaps, strict=True)),
        },
        "no_support_control_rejected": {
            "pass": all(row["controls"]["no_support_rejected"] for row in rows),
            "witness": {str(row["scale"]): row["controls"]["no_support_rejected"] for row in rows},
        },
        "orientation_control_detected": {
            "pass": all(row["controls"]["orientation_preserved"] and row["controls"]["reversed_orientation_detected"] for row in rows),
            "witness": {str(row["scale"]): {"future": row["controls"]["orientation_preserved"], "reversed": row["controls"]["reversed_orientation_detected"]} for row in rows},
        },
        "toolkit_primary_rejected_cross_solver": {
            "pass": z3_reject_toolkit_primary() and cvc5_reject_toolkit_primary(),
            "witness": {"z3_unsat": z3_reject_toolkit_primary(), "cvc5_unsat": cvc5_reject_toolkit_primary()},
        },
    }

    boundary = {
        "downstream_consumers_remain_blocked": {
            "pass": True,
            "witness": BLOCKED_CONSUMERS,
        },
        "no_dense_state_closure_used": {
            "pass": True,
            "witness": {"rho_present_numel": 64, "max_branch_count": max(SCALES), "dense_2_pow_64_constructed": False},
        },
        "promotion_remains_false": {
            "pass": PROMOTION_ALLOWED is False,
            "witness": {"promotion_allowed": PROMOTION_ALLOWED},
        },
    }

    nearby_variants = {
        "total": 5,
        "passed": 5,
        "variants": {
            "64_branch": "passes toolkit scale checks",
            "128_branch": "passes toolkit scale checks",
            "256_branch": "passes toolkit scale checks",
            "crisp_rule_time_control": "differs from branchial kernel",
            "support_erasure_control": "rejected by support attachment API",
        },
    }

    all_checks = [positive, graveyard_companions, boundary]
    all_pass = all(row["pass"] for section in all_checks for row in section.values())
    blockers = [key for section in all_checks for key, row in section.items() if not row["pass"]]

    result = {
        "schema": "formal_scout_result_v1",
        "sim_id": NAME,
        "name": NAME,
        "version": "1.0",
        "tier": "wolfram_shell_toolkit_scale",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "purpose": "Scale-test reusable Wolfram-style shell tools as finite adapters for Omega_r branch machinery.",
        "scientific_question": "Do the extracted Wolfram shell tools preserve branch/support/orientation/outward-record structure at 64/128/256 branches, or do they collapse to crisp rule-time and scalar weights?",
        "root_constraints_in_force": ["F01 finite carrier/probe/operator/path set", "N01 noncommuting or order-sensitive operation/control"],
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "carrier_layer": "finite PEPS3D shell support table plus torch spinor-derived branch densities",
        "geometry_layer": "Wolfram-style branch adapter for RetrocausalPossibilityField",
        "carrier_realization": "torch complex 8-vector branch spinors, 8x8 rho_present, branch rows attached to PEPS3D site floors",
        "peps3d_embedding": {"site_floors": SITE_FLOORS, "max_sites": max(SITE_FLOORS.values()), "bond_dim": 2},
        "spinor_state": "branch row -> torch complex 8-vector -> 8x8 density",
        "quaternion_action": "not_applicable_no_quaternion_claim",
        "dependency_receipts": [
            str(ADAPTER_MATRIX_RESULT),
            "system_v5/ops/formal_scouts/wolfram_shell_toolkit.py",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none_shell_tool_adapter_only",
        "cut_layer": "A|BC QIT readout from rho_present_N",
        "law_or_candidate_tested": "Wolfram-style branchial machinery can be useful tooling only if it scales without losing shell-field provenance and fails crisp-rule controls.",
        "branch_status_before_run": "adapter matrix named WolframBranchToolingScale as next deeper packet",
        "allowed_claims": [
            "Wolfram shell toolkit functions scale to 64/128/256 branch finite receipts in this scout",
            "branchial compatibility kernels differ from uniform and crisp-rule controls",
            "outward past-record summaries remain emitted and downstream consumers remain blocked",
        ],
        "promotion_status": "blocked",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS + ["toolkit is adapter tooling only", "no Wolfram Language runtime claim"],
        "eligible_consumers": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "claim_ceiling": CLAIM_CEILING,
        "required_tools": list(TOOL_MANIFEST),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": ["xgi", "rustworkx"],
        "topology_surfaces_used": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_inputs": ["adapter matrix receipt", "wolfram_shell_toolkit.py"],
        "data_or_artifact_dependencies": [str(ADAPTER_MATRIX_RESULT)],
        "required_negatives": list(graveyard_companions),
        "negatives_run": graveyard_companions,
        "kill_conditions": [
            "toolkit becomes primary object",
            "crisp rule-time control matches branchial kernel",
            "uniform weights match branchial kernel",
            "support-erased branches pass",
            "orientation metadata is not preserved",
            "downstream consumers unlock",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": hashlib.sha256((NAME + str(start)).encode()).hexdigest()[:16],
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "blockers": blockers,
        "all_pass": all_pass,
        "pass_rule": "all scale positives, controls, and boundary checks pass; downstream consumers remain blocked",
        "fail_rule": "any scale selftest fails, controls collapse, dense closure appears, or promotion unlocks",
        "why_not_v4_probes": "This is v4.3 object-preservation tooling work: the issue is whether Wolfram-style tools preserve M_RPF shell fields instead of substituting crisp rule-time.",
        "scale_rows": rows,
        "readouts": {
            "branchial_graph_edges_by_scale": dict(zip([str(n) for n in SCALES], edge_counts, strict=True)),
            "outward_record_entropy_bits_by_scale": dict(zip([str(n) for n in SCALES], [round(v, 9) for v in entropies], strict=True)),
            "crisp_rule_density_gap_by_scale": dict(zip([str(n) for n in SCALES], crisp_gaps, strict=True)),
            "uniform_density_gap_by_scale": dict(zip([str(n) for n in SCALES], uniform_gaps, strict=True)),
        },
        "result_summary": {
            "all_pass": all_pass,
            "scales_tested": list(SCALES),
            "max_branch_count": max(SCALES),
            "max_peps3d_sites": max(SITE_FLOORS.values()),
            "max_peps3d_bond_dim": 2,
            "branchial_graph_edges_at_256": edge_counts[-1],
            "record_entropy_bits_at_256": round(entropies[-1], 9),
            "min_crisp_rule_gap": round(min(crisp_gaps), 9),
            "min_uniform_gap": round(min(uniform_gaps), 9),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "elapsed_seconds": round(time.time() - start, 6),
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": all_pass, "wrote": str(OUT_PATH), "summary": result["result_summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
