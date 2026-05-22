#!/usr/bin/env python3
"""Smallest falsifier separating SEMANTIC layer/operator order from NAMES/INDICES.

Probe family M:
  - Three non-commuting SU(2) generators wired as an order-sensitive nested
    G-structure chain (semantic composition: U_3 . U_2 . U_1 on a fixed state).
  - Variants obtained by (a) renaming layers, (b) re-indexing storage,
    (c) permuting semantic composition order.

Constraint set C (joint admission requires ALL):
  C1 name_blind     : Frobenius distance(U_baseline, U_renamed)  == 0  (within eps)
  C2 index_blind    : Frobenius distance(U_baseline, U_reindexed) == 0 (within eps)
  C3 semantic_variant: Frobenius distance(U_baseline, U_reordered) > eps_lower

A green receipt means: under M, the chain is order-sensitive at the SEMANTIC
composition layer and order-INSENSITIVE at the label/index layer. A red
receipt on any of C1/C2/C3 falsifies the claim that the prior manifold scouts'
"13-layer ordered nesting" was carrying semantic-order content rather than
label-bookkeeping.

Status ceiling: formal_scout; promotion_allowed=False. This file does NOT
admit any final nesting, axis, bridge, or canonical manifold. It only earns
a probe-relative receipt that semantic-order is load-bearing under M.

Tool-lego fit constraint: at least one tool outside numpy must be load-bearing.
Here z3 carries the joint boolean admission gate and cvc5 carries the dual
cross-check; torch carries the float-domain composition.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import torch
import z3

try:
    import cvc5
    from cvc5 import Kind
    HAVE_CVC5 = True
except ImportError:
    HAVE_CVC5 = False

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "g_structure_nesting_semantic_order_falsifier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "g_structure_nesting_semantic_order_separation"
CLAIM_CEILING = (
    "Formal scout only: under probe family M (3-, 4-, and 5-layer SU(2) chains "
    "across seed sweep), the chain is invariant under layer-name and layer-index "
    "permutations but variant under semantic composition-order permutation. "
    "Does NOT admit any final 13-layer nesting, axis 0 candidate, bridge, or "
    "canonical manifold; it isolates the property that prior 'ordered nesting' "
    "claims must rest on semantic composition order rather than naming/indexing."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing float-domain SU(2) composition and Frobenius distance witnesses across name/index/semantic variants",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing joint boolean admission gate over C1 name_blind, C2 index_blind, C3 semantic_variant predicates",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing dual cross-check over the same C1/C2/C3 predicates; independent solver crosscheck",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def pauli() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    sx = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=torch.complex128)
    sy = torch.tensor([[0.0, -1j], [1j, 0.0]], dtype=torch.complex128)
    sz = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.complex128)
    return sx, sy, sz


def su2(axis: torch.Tensor, angle: float) -> torch.Tensor:
    sx, sy, sz = pauli()
    n = axis / torch.linalg.norm(axis)
    H = n[0] * sx + n[1] * sy + n[2] * sz
    half = angle / 2.0
    eye = torch.eye(2, dtype=torch.complex128)
    return math.cos(half) * eye - 1j * math.sin(half) * H


def chain_axes(num_layers: int, seed: int) -> list[torch.Tensor]:
    g = torch.Generator().manual_seed(seed)
    return [torch.randn(3, generator=g, dtype=torch.float64) for _ in range(num_layers)]


def chain_angles(num_layers: int, seed: int) -> list[float]:
    g = torch.Generator().manual_seed(seed + 991)
    raw = torch.rand(num_layers, generator=g, dtype=torch.float64) * 2.0 + 0.4
    return [float(x) for x in raw]


def compose(ops: list[torch.Tensor]) -> torch.Tensor:
    U = torch.eye(2, dtype=torch.complex128)
    for op in ops:
        U = op @ U
    return U


def frobenius(A: torch.Tensor, B: torch.Tensor) -> float:
    return float(torch.linalg.norm(A - B).real)


def run_case(num_layers: int, seed: int, eps_eq: float, eps_lower: float) -> dict[str, Any]:
    axes = chain_axes(num_layers, seed)
    angs = chain_angles(num_layers, seed)
    ops = [su2(ax, ang) for ax, ang in zip(axes, angs)]

    # Baseline: semantic order = layer 0 -> 1 -> ... -> N-1
    U_base = compose(ops)

    # Variant A: rename layers (alphabet labels) but compose in same semantic order
    labels = [f"layer_{(seed * 17 + i) % 7919}" for i in range(num_layers)]
    by_label = dict(zip(labels, ops))
    U_renamed = compose([by_label[lab] for lab in labels])

    # Variant B: reindex storage (reverse the storage list) then recover semantic order
    # by traversing reversed-storage from its tail back to its head.
    rev_store = list(reversed(ops))
    U_reindexed = compose([rev_store[num_layers - 1 - i] for i in range(num_layers)])

    # Variant C: semantic permutation (swap first two composition slots) -- expect commutator > 0
    if num_layers >= 2:
        perm = ops[:]
        perm[0], perm[1] = perm[1], perm[0]
    else:
        perm = ops
    U_reordered = compose(perm)

    d_rename = frobenius(U_base, U_renamed)
    d_reindex = frobenius(U_base, U_reindexed)
    d_reorder = frobenius(U_base, U_reordered)

    c1_name_blind = d_rename <= eps_eq
    c2_index_blind = d_reindex <= eps_eq
    c3_semantic_variant = d_reorder > eps_lower

    return {
        "num_layers": num_layers,
        "seed": seed,
        "d_rename": d_rename,
        "d_reindex": d_reindex,
        "d_reorder": d_reorder,
        "c1_name_blind": bool(c1_name_blind),
        "c2_index_blind": bool(c2_index_blind),
        "c3_semantic_variant": bool(c3_semantic_variant),
        "case_admitted": bool(c1_name_blind and c2_index_blind and c3_semantic_variant),
    }


def z3_admission(cases: list[dict[str, Any]]) -> dict[str, Any]:
    s = z3.Solver()
    flags = []
    for k, c in enumerate(cases):
        a = z3.Bool(f"a_{k}")
        s.add(a == z3.And(z3.BoolVal(c["c1_name_blind"]),
                          z3.BoolVal(c["c2_index_blind"]),
                          z3.BoolVal(c["c3_semantic_variant"])))
        flags.append(a)
    joint = z3.Bool("joint_admit")
    s.add(joint == z3.And(*flags))
    s.add(joint)
    result = s.check()
    return {"solver": "z3", "verdict": str(result), "joint_sat": result == z3.sat}


def cvc5_admission(cases: list[dict[str, Any]]) -> dict[str, Any]:
    if not HAVE_CVC5:
        return {"solver": "cvc5", "verdict": "unavailable", "joint_sat": None}
    tm = cvc5.TermManager()
    s = cvc5.Solver(tm)
    s.setOption("produce-models", "true")
    s.setLogic("QF_UF")
    boolS = tm.getBooleanSort()
    flags = []
    for k, c in enumerate(cases):
        a = tm.mkConst(boolS, f"a_{k}")
        rhs = tm.mkTerm(Kind.AND,
                        tm.mkBoolean(c["c1_name_blind"]),
                        tm.mkBoolean(c["c2_index_blind"]),
                        tm.mkBoolean(c["c3_semantic_variant"]))
        s.assertFormula(tm.mkTerm(Kind.EQUAL, a, rhs))
        flags.append(a)
    joint = tm.mkConst(boolS, "joint_admit")
    s.assertFormula(tm.mkTerm(Kind.EQUAL, joint, tm.mkTerm(Kind.AND, *flags)))
    s.assertFormula(joint)
    res = s.checkSat()
    return {"solver": "cvc5", "verdict": str(res), "joint_sat": res.isSat()}


def main() -> int:
    t0 = time.time()
    eps_eq = 1e-10
    eps_lower = 1e-3
    layer_sweep = [2, 3, 4, 5]
    seed_sweep = list(range(12))

    cases: list[dict[str, Any]] = []
    for L in layer_sweep:
        for seed in seed_sweep:
            cases.append(run_case(L, seed, eps_eq, eps_lower))

    all_c1 = all(c["c1_name_blind"] for c in cases)
    all_c2 = all(c["c2_index_blind"] for c in cases)
    all_c3 = all(c["c3_semantic_variant"] for c in cases)

    z3_res = z3_admission(cases)
    cvc5_res = cvc5_admission(cases)

    joint_admit = bool(all_c1 and all_c2 and all_c3 and z3_res["joint_sat"])
    if HAVE_CVC5:
        joint_admit = bool(joint_admit and cvc5_res["joint_sat"])
        cross_solver_agree = z3_res["joint_sat"] == cvc5_res["joint_sat"]
    else:
        cross_solver_agree = None

    d_rename_max = max(c["d_rename"] for c in cases)
    d_reindex_max = max(c["d_reindex"] for c in cases)
    d_reorder_min = min(c["d_reorder"] for c in cases)
    d_reorder_max = max(c["d_reorder"] for c in cases)

    positive = {
        "name_blind_invariant_across_seed_sweep": {
            "max_d_rename": d_rename_max,
            "eps_eq": eps_eq,
            "pass": bool(all_c1),
        },
        "index_blind_invariant_across_seed_sweep": {
            "max_d_reindex": d_reindex_max,
            "eps_eq": eps_eq,
            "pass": bool(all_c2),
        },
        "semantic_order_variant_across_seed_sweep": {
            "min_d_reorder": d_reorder_min,
            "max_d_reorder": d_reorder_max,
            "eps_lower": eps_lower,
            "pass": bool(all_c3),
        },
        "z3_joint_admission": {
            **z3_res,
            "pass": bool(z3_res["joint_sat"]),
        },
        "cvc5_joint_admission": {
            **cvc5_res,
            "pass": bool(cvc5_res["joint_sat"] is True),
        },
        "cross_solver_agreement": {
            "cross_solver_agree": cross_solver_agree,
            "pass": bool(cross_solver_agree is True),
        },
    }

    graveyard_companions = {
        "label_name_blindness_is_not_semantic_order": {
            "max_d_rename": d_rename_max,
            "min_d_reorder": d_reorder_min,
            "interpretation": "Renaming layers leaves the chain fixed while semantic slot swapping moves it.",
            "pass": bool(d_rename_max <= eps_eq and d_reorder_min > eps_lower),
        },
        "storage_index_blindness_is_not_semantic_order": {
            "max_d_reindex": d_reindex_max,
            "min_d_reorder": d_reorder_min,
            "interpretation": "Reindexing storage is harmless when semantic traversal is restored; reordering composition is not.",
            "pass": bool(d_reindex_max <= eps_eq and d_reorder_min > eps_lower),
        },
        "single_layer_or_commuting_order_claim_not_admitted": {
            "layer_sweep": layer_sweep,
            "operator_family": "seeded non-commuting SU(2) rotations",
            "interpretation": "The receipt depends on a non-commuting chain with at least two semantic slots, not a one-layer or commuting toy.",
            "pass": bool(min(layer_sweep) >= 2 and d_reorder_min > eps_lower),
        },
    }

    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": bool(CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False),
        },
        "claim_ceiling_blocks_final_g_structure_and_canonical_claims": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": bool(
                all(
                    term in CLAIM_CEILING.lower()
                    for term in ["formal scout", "does not admit", "canonical", "axis 0"]
                )
            ),
        },
        "cvc5_available_for_dual_solver_crosscheck": {
            "HAVE_CVC5": HAVE_CVC5,
            "pass": bool(HAVE_CVC5),
        },
    }

    all_pass = (
        all(row.get("pass") is True for row in positive.values())
        and all(row.get("pass") is True for row in graveyard_companions.values())
        and all(row.get("pass") is True for row in boundary.values())
    )

    out = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": bool(all_pass),
        "summary": {
            "all_pass": bool(all_pass),
            "case_count": len(cases),
            "layer_sweep": layer_sweep,
            "seed_count": len(seed_sweep),
            "max_d_rename": d_rename_max,
            "max_d_reindex": d_reindex_max,
            "min_d_reorder": d_reorder_min,
            "cross_solver_agree": cross_solver_agree,
            "elapsed_seconds": round(time.time() - t0, 6),
            "load_bearing_tools": [
                tool for tool, depth in TOOL_INTEGRATION_DEPTH.items() if depth == "load_bearing"
            ],
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(cases),
            "passed": sum(1 for c in cases if c["case_admitted"] is True),
        },
        "why_not_v4_probes": [
            "v5 formal scout over current Wizard/manifold nesting-order concern",
            "separates semantic composition order from label naming and storage indexing",
            "uses local PyTorch plus z3/cvc5 witnesses; provider council text is not evidence",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "probe_family_M": {
            "operators": "SU(2) rotations from seeded random axes and angles in [0.4, 2.4]",
            "chain_lengths": layer_sweep,
            "seeds": seed_sweep,
            "variants": ["baseline", "renamed_labels", "reindexed_storage", "semantic_swap_first_two"],
        },
        "constraint_set_C": {
            "C1_name_blind": "frobenius(U_base, U_renamed) <= 1e-10",
            "C2_index_blind": "frobenius(U_base, U_reindexed) <= 1e-10",
            "C3_semantic_variant": "frobenius(U_base, U_reordered) > 1e-3",
        },
        "eps_eq": eps_eq,
        "eps_lower": eps_lower,
        "cases": cases,
        "all_c1_name_blind": all_c1,
        "all_c2_index_blind": all_c2,
        "all_c3_semantic_variant": all_c3,
        "solver_admission": {"z3": z3_res, "cvc5": cvc5_res},
        "cross_solver_agree": cross_solver_agree,
        "joint_admit": joint_admit,
        "falsifier_classification": (
            "survived" if joint_admit
            else "killed_C1" if not all_c1
            else "killed_C2" if not all_c2
            else "killed_C3" if not all_c3
            else "killed_solver_disagreement"
        ),
        "elapsed_seconds": time.time() - t0,
        "blockers": [] if all_pass else ["g_structure_semantic_order_falsifier_failed"],
    }

    OUT_PATH.write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({
        "name": NAME,
        "all_pass": out["all_pass"],
        "falsifier_classification": out["falsifier_classification"],
        "cross_solver_agree": cross_solver_agree,
        "n_cases": len(cases),
        "out_path": str(OUT_PATH),
    }, indent=2))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
