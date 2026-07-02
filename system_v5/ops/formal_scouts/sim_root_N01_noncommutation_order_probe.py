#!/usr/bin/env python3
import jax
jax.config.update("jax_enable_x64", True)

import json
import pathlib
import sys
import time
from typing import Any

import jax.numpy as jnp
import sympy as sp
import torch
import z3

torch.set_default_dtype(torch.float64)

SCRIPTS_DIR = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "root_N01_noncommutation_order_probe"
OBJECT_ID = "N01_noncommutation_order"
OUT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"

SCALE_RUNGS = (8, 16, 32, 64)
EPS_NUM = 1
EPS_DEN = 1_000_000_000
EPS = EPS_NUM / EPS_DEN
TOL = 1.0e-12
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]


TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": (
            "PRIMARY claim-bearing numeric engine: builds the finite operator "
            "family {A,B}, computes ||[A,B]|| on the real carrier, and "
            "recomputes the order-erased commuting projection control."
        ),
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": (
            "Parity mirror with jax_enable_x64 set before jax.numpy import; "
            "recomputes the same finite commutator-gap observable independently."
        ),
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": (
            "PROOF via load_bearing_proof.smt_load_bearing: binds measured "
            "commutator norms to z3 Reals and requires a real/control verdict flip."
        ),
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": (
            "PROOF via load_bearing_proof.smt_load_bearing cvc5_claim_pairs: "
            "cross-checks the same measured real/control inequality."
        ),
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": (
            "PROOF: exact symbolic commutator construction confirms the nonzero "
            "witness and exact collapse after commuting projection."
        ),
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "control-only by contract; not used in this nonclassical root sim.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "control-only by contract; not used in this finite root sim.",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive only: sys.path helper import, JSON emission, paths, timestamps.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "numpy": None,
    "scipy": None,
    "python_stdlib": "supportive",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if hasattr(value, "tolist") and callable(value.tolist):
        try:
            return as_jsonable(value.tolist())
        except Exception:
            pass
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def torch_operator_family(n: int) -> tuple[torch.Tensor, torch.Tensor]:
    diagonal = torch.arange(n, dtype=torch.float64) / float(n - 1)
    a = torch.diag(diagonal)
    b = torch.zeros((n, n), dtype=torch.float64)
    idx = torch.arange(n - 1)
    b[idx, idx + 1] = 1.0
    return a, b


def jax_operator_family(n: int) -> tuple[jnp.ndarray, jnp.ndarray]:
    diagonal = jnp.arange(n, dtype=jnp.float64) / jnp.float64(n - 1)
    a = jnp.diag(diagonal)
    b = jnp.zeros((n, n), dtype=jnp.float64)
    b = b.at[jnp.arange(n - 1), jnp.arange(1, n)].set(1.0)
    return a, b


def torch_commutator_readout(n: int) -> dict[str, Any]:
    a, b = torch_operator_family(n)
    comm = a @ b - b @ a
    b_projected = torch.diag(torch.diag(b))
    projected_comm = a @ b_projected - b_projected @ a
    simultaneous_control = torch.diag(torch.linspace(1.0, 2.0, n, dtype=torch.float64))
    simultaneous_comm = a @ simultaneous_control - simultaneous_control @ a
    singular_values = torch.linalg.svdvals(comm)

    gap = float(torch.linalg.matrix_norm(comm, ord="fro").item())
    projected_gap = float(torch.linalg.matrix_norm(projected_comm, ord="fro").item())
    simultaneous_gap = float(torch.linalg.matrix_norm(simultaneous_comm, ord="fro").item())
    witness_abs = float(abs(comm[0, 1]).item())

    return {
        "n": n,
        "operator_dimension": n,
        "operator_count": 2,
        "path_count": 2,
        "dense_state_closure_used": False,
        "commutator_frobenius_gap": gap,
        "projected_commuting_subalgebra_gap": projected_gap,
        "simultaneously_diagonalized_control_gap": simultaneous_gap,
        "witness_entry": {"row": 0, "col": 1, "value": float(comm[0, 1].item())},
        "witness_entry_abs": witness_abs,
        "singular_values": [float(item) for item in singular_values.tolist()],
        "min_singular_value": float(torch.min(singular_values).item()),
        "max_singular_value": float(torch.max(singular_values).item()),
        "full_minus_projected_gap": gap - projected_gap,
        "pass": bool(gap >= EPS and witness_abs >= EPS and projected_gap <= TOL and simultaneous_gap <= TOL),
    }


def jax_commutator_readout(n: int) -> dict[str, Any]:
    a, b = jax_operator_family(n)
    comm = a @ b - b @ a
    b_projected = jnp.diag(jnp.diag(b))
    projected_comm = a @ b_projected - b_projected @ a
    simultaneous_control = jnp.diag(jnp.linspace(1.0, 2.0, n, dtype=jnp.float64))
    simultaneous_comm = a @ simultaneous_control - simultaneous_control @ a

    gap = float(jnp.linalg.norm(comm, ord="fro"))
    projected_gap = float(jnp.linalg.norm(projected_comm, ord="fro"))
    simultaneous_gap = float(jnp.linalg.norm(simultaneous_comm, ord="fro"))
    witness_abs = float(jnp.abs(comm[0, 1]))

    return {
        "n": n,
        "operator_dimension": n,
        "operator_count": 2,
        "path_count": 2,
        "dense_state_closure_used": False,
        "commutator_frobenius_gap": gap,
        "projected_commuting_subalgebra_gap": projected_gap,
        "simultaneously_diagonalized_control_gap": simultaneous_gap,
        "witness_entry_abs": witness_abs,
        "full_minus_projected_gap": gap - projected_gap,
        "pass": bool(gap >= EPS and witness_abs >= EPS and projected_gap <= TOL and simultaneous_gap <= TOL),
    }


def sympy_exact_readout(n: int) -> dict[str, Any]:
    diag_entries = [sp.Rational(i, n - 1) for i in range(n)]
    a = sp.diag(*diag_entries)
    b = sp.zeros(n, n)
    for i in range(n - 1):
        b[i, i + 1] = sp.Integer(1)
    comm = a * b - b * a
    b_projected = sp.diag(*[b[i, i] for i in range(n)])
    projected_comm = a * b_projected - b_projected * a
    frob_sq = sp.simplify(sum(comm[i, j] ** 2 for i in range(n) for j in range(n)))
    projected_frob_sq = sp.simplify(sum(projected_comm[i, j] ** 2 for i in range(n) for j in range(n)))
    witness = sp.simplify(comm[0, 1])
    return {
        "n": n,
        "operator_dimension": n,
        "exact_witness_entry": str(witness),
        "exact_commutator_frobenius_square": str(frob_sq),
        "exact_projected_frobenius_square": str(projected_frob_sq),
        "commutator_frobenius_gap": float(sp.sqrt(frob_sq)),
        "projected_commuting_subalgebra_gap": float(sp.sqrt(projected_frob_sq)),
        "original_commutator_nonzero": bool(witness != 0 and frob_sq > 0),
        "projected_commutator_zero": bool(projected_comm == sp.zeros(n, n)),
        "pass": bool(witness != 0 and frob_sq > 0 and projected_comm == sp.zeros(n, n)),
    }


def load_bearing_commutator_proof(real_gap: float, control_gap: float) -> dict[str, Any]:
    return smt_load_bearing(
        "||[A,B]||_F >= eps",
        real_measured={"commutator_norm": real_gap},
        control_measured={"commutator_norm": control_gap},
        claim_builder=lambda v: v["commutator_norm"] >= z3.Q(EPS_NUM, EPS_DEN),
        cvc5_claim_pairs=[("commutator_norm", ">=", EPS)],
    )


def proof_flip_score(proof: dict[str, Any], engine: str) -> float:
    if engine == "z3":
        return float(
            proof.get("real_claim_verdict") == "sat"
            and proof.get("negated_claim_verdict") == "unsat"
            and proof.get("differ") is True
            and proof.get("bound_to_measured") is True
        )
    if engine == "cvc5":
        return float(
            proof.get("cvc5_real_verdict") == "sat"
            and proof.get("cvc5_control_verdict") == "unsat"
            and proof.get("differ") is True
            and proof.get("bound_to_measured") is True
        )
    raise ValueError(f"unknown proof engine: {engine}")


def build_ablation(
    observable: str,
    baseline_value: float,
    ablated_value: float,
    tool: str,
    *,
    ablation_kind: str,
    removal_semantics: str,
) -> dict[str, Any]:
    row = tool_ablation(observable, baseline_value=baseline_value, ablated_value=ablated_value, tool=tool)
    row["pass"] = bool(abs(row["outcome_delta"]) >= EPS and float(ablated_value) <= TOL)
    row["baseline_recomputed"] = True
    row["ablated_recomputed"] = True
    row["ablation_kind"] = ablation_kind
    row["removal_semantics"] = removal_semantics
    return row


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()

    torch_rungs = {str(n): torch_commutator_readout(n) for n in SCALE_RUNGS}
    jax_rungs = {str(n): jax_commutator_readout(n) for n in SCALE_RUNGS}
    sympy_rungs = {str(n): sympy_exact_readout(n) for n in SCALE_RUNGS}
    smt_rungs = {
        str(n): load_bearing_commutator_proof(
            torch_rungs[str(n)]["commutator_frobenius_gap"],
            torch_rungs[str(n)]["projected_commuting_subalgebra_gap"],
        )
        for n in SCALE_RUNGS
    }
    smt_decoupled_rungs = {
        str(n): load_bearing_commutator_proof(
            torch_rungs[str(n)]["commutator_frobenius_gap"],
            torch_rungs[str(n)]["commutator_frobenius_gap"],
        )
        for n in SCALE_RUNGS
    }

    max_jax_delta = max(
        abs(torch_rungs[str(n)]["commutator_frobenius_gap"] - jax_rungs[str(n)]["commutator_frobenius_gap"])
        for n in SCALE_RUNGS
    )
    min_torch_gap = min(torch_rungs[str(n)]["commutator_frobenius_gap"] for n in SCALE_RUNGS)
    max_torch_control_gap = max(torch_rungs[str(n)]["projected_commuting_subalgebra_gap"] for n in SCALE_RUNGS)
    min_jax_gap = min(jax_rungs[str(n)]["commutator_frobenius_gap"] for n in SCALE_RUNGS)
    max_jax_control_gap = max(jax_rungs[str(n)]["projected_commuting_subalgebra_gap"] for n in SCALE_RUNGS)
    min_sympy_gap = min(sympy_rungs[str(n)]["commutator_frobenius_gap"] for n in SCALE_RUNGS)
    max_sympy_control_gap = max(sympy_rungs[str(n)]["projected_commuting_subalgebra_gap"] for n in SCALE_RUNGS)
    smt_load_bearing_pass = all(
        row["real_claim_verdict"] == "sat"
        and row["negated_claim_verdict"] == "unsat"
        and row["differ"]
        and row["bound_to_measured"]
        and row.get("cvc5_real_verdict") == "sat"
        and row.get("cvc5_control_verdict") == "unsat"
        for row in smt_rungs.values()
    )
    sympy_pass = all(row["pass"] for row in sympy_rungs.values())

    tool_ablations = {
        "torch": build_ablation(
            "torch_commutator_frobenius_gap_with_shift_vs_shift_removed_projection",
            min_torch_gap,
            max_torch_control_gap,
            "torch",
            ablation_kind="torch_noncommuting_shift_removed",
            removal_semantics=(
                "recompute the torch commutator after removing only the noncommuting "
                "off-diagonal shift structure by projecting B into A's diagonal basis"
            ),
        ),
        "jax": build_ablation(
            "jax_commutator_frobenius_gap_with_shift_vs_shift_removed_projection",
            min_jax_gap,
            max_jax_control_gap,
            "jax",
            ablation_kind="jax_noncommuting_shift_removed",
            removal_semantics=(
                "recompute the JAX x64 parity commutator after removing only the "
                "noncommuting off-diagonal shift structure by projecting B into A's diagonal basis"
            ),
        ),
        "z3": build_ablation(
            "z3_commutator_order_flip_score_engine_present_vs_decoupled",
            min(proof_flip_score(row, "z3") for row in smt_rungs.values()),
            max(proof_flip_score(row, "z3") for row in smt_decoupled_rungs.values()),
            "z3",
            ablation_kind="z3_engine_flip_score_removed",
            removal_semantics=(
                "z3 is removed by decoupling the proof flip: the same measured "
                "real commutator value is fed as the control value, so z3 cannot "
                "produce a real/control verdict flip"
            ),
        ),
        "cvc5": build_ablation(
            "cvc5_commutator_order_flip_score_engine_present_vs_decoupled",
            min(proof_flip_score(row, "cvc5") for row in smt_rungs.values()),
            max(proof_flip_score(row, "cvc5") for row in smt_decoupled_rungs.values()),
            "cvc5",
            ablation_kind="cvc5_engine_flip_score_removed",
            removal_semantics=(
                "cvc5 is removed by decoupling its cross-check flip: the same measured "
                "real commutator value is fed as the control value, so cvc5 cannot "
                "produce a real/control verdict flip"
            ),
        ),
        "sympy": build_ablation(
            "sympy_exact_commutator_frobenius_gap_with_symbolic_step_removed",
            min_sympy_gap,
            max_sympy_control_gap,
            "sympy",
            ablation_kind="sympy_exact_commutator_step_removed",
            removal_semantics=(
                "recompute the exact rational commutator after removing only the "
                "symbolic noncommuting shift step by projecting B into A's diagonal basis"
            ),
        ),
    }

    scale_rungs = {
        str(n): {
            "n": n,
            "operator_dimension": n,
            "operator_count": 2,
            "path_count": 2,
            "dense_state_closure_used": False,
            "torch_commutator_frobenius_gap": torch_rungs[str(n)]["commutator_frobenius_gap"],
            "jax_commutator_frobenius_gap": jax_rungs[str(n)]["commutator_frobenius_gap"],
            "jax_vs_pytorch_delta": abs(
                torch_rungs[str(n)]["commutator_frobenius_gap"] - jax_rungs[str(n)]["commutator_frobenius_gap"]
            ),
            "projected_commuting_subalgebra_gap": torch_rungs[str(n)]["projected_commuting_subalgebra_gap"],
            "smt_load_bearing_differ": smt_rungs[str(n)]["differ"],
            "pass": bool(
                torch_rungs[str(n)]["pass"]
                and jax_rungs[str(n)]["pass"]
                and sympy_rungs[str(n)]["pass"]
                and smt_rungs[str(n)]["differ"]
                and smt_rungs[str(n)]["real_claim_verdict"] == "sat"
                and smt_rungs[str(n)]["negated_claim_verdict"] == "unsat"
                and smt_rungs[str(n)].get("cvc5_real_verdict") == "sat"
                and smt_rungs[str(n)].get("cvc5_control_verdict") == "unsat"
            ),
        }
        for n in SCALE_RUNGS
    }

    all_scale_pass = all(row["pass"] for row in scale_rungs.values())
    all_ablations_pass = all(row["pass"] for row in tool_ablations.values())
    required_pass = bool(
        all_scale_pass
        and all_ablations_pass
        and smt_load_bearing_pass
        and sympy_pass
        and max_jax_delta <= TOL
        and min_torch_gap >= EPS
        and max_torch_control_gap <= TOL
    )

    result = {
        "schema": "PER_SIM_CONTRACT_ROOT_STAGE1_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "object_id": OBJECT_ID,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "tier": "canonical_stage_1_root_constraint",
        "purpose": "Build one root-constraint N01 noncommutation/order lego with non-fabricated helper proofs.",
        "scientific_question": "Does a finite operator family {A,B} carry order-sensitive noncommutation that collapses under order-erased commuting projection?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "constraint_probe",
        "finite_map": {
            "domain": "finite ordered operator pairs (A,B) over dimensions n in {8,16,32,64}",
            "codomain_or_output": "numeric commutator norm ||A@B - B@A||_F and its order-erased commuting-projection control",
        },
        "domain": "finite ordered operator pairs (A,B) over dimensions n in {8,16,32,64}",
        "codomain_or_output": "commutator norm ||A@B - B@A||_F plus negative-control collapse",
        "root_constraints": {
            "F01": {
                "role": "active_finite_carrier",
                "description": "finite operator/probe/path set: two n-by-n operators at each bounded rung",
            },
            "N01": {
                "role": "active_noncommutation_order",
                "description": "A@B and B@A differ on the real family; order-erased commuting projection kills the gap",
            },
        },
        "root_constraints_in_force": ["F01_finite_operator_family", "N01_noncommutation_order"],
        "law_or_candidate_tested": "||[A,B]||_F >= eps for a finite diagonal/shift operator family",
        "carrier_layer": "root_finite_operator_family_no_manifold_claim",
        "geometry_layer": "not_applicable_root_constraint_only",
        "carrier_realization": "torch.float64 finite matrices; no dense state closure",
        "peps3d_embedding": "blocked_not_claimed_for_this_root_constraint_sim",
        "spinor_state": "not_applicable_no_spinor_manifold_claim",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [],
        "torch_primary_result": {
            "engine": "torch",
            "dtype": "torch.float64",
            "claim": "real carrier has commutator norm above eps while commuting projection control collapses",
            "eps": EPS,
            "rungs": torch_rungs,
            "min_commutator_frobenius_gap": min_torch_gap,
            "max_projected_commuting_subalgebra_gap": max_torch_control_gap,
            "pass": all(row["pass"] for row in torch_rungs.values()),
        },
        "jax_mirror_result": {
            "engine": "jax",
            "x64_enabled": bool(jax.config.read("jax_enable_x64")),
            "claim": "JAX parity mirror recomputes the same finite commutator gaps",
            "rungs": jax_rungs,
            "min_commutator_frobenius_gap": min_jax_gap,
            "max_projected_commuting_subalgebra_gap": max_jax_control_gap,
            "pass": all(row["pass"] for row in jax_rungs.values()),
        },
        "jax_vs_pytorch_delta": max_jax_delta,
        "proof_results": {
            "smt_load_bearing_commutator_norm": {
                "helper": "load_bearing_proof.smt_load_bearing",
                "claim": "||[A,B]||_F >= eps",
                "rungs": smt_rungs,
                "pass": smt_load_bearing_pass,
            },
            "sympy_exact_commutator": {
                "engine": "sympy",
                "claim": "exact symbolic [A,B] witness is nonzero and projected control is zero",
                "rungs": sympy_rungs,
                "pass": sympy_pass,
            },
        },
        "controls": {
            "order_erased_projected_commuting_subalgebra": {
                "description": "replace B by its diagonal projection in A's eigenbasis and recompute the commutator",
                "rungs": {
                    str(n): {
                        "torch_gap_after_control": torch_rungs[str(n)]["projected_commuting_subalgebra_gap"],
                        "jax_gap_after_control": jax_rungs[str(n)]["projected_commuting_subalgebra_gap"],
                        "sympy_gap_after_control": sympy_rungs[str(n)]["projected_commuting_subalgebra_gap"],
                        "kills_constraint": bool(torch_rungs[str(n)]["projected_commuting_subalgebra_gap"] <= TOL),
                    }
                    for n in SCALE_RUNGS
                },
                "max_gap_after_control": max_torch_control_gap,
                "pass": bool(max_torch_control_gap <= TOL),
            },
            "simultaneously_diagonalized_commuting_family": {
                "description": "replace B with a diagonal operator in the same basis as A and recompute the commutator",
                "max_gap_after_control": max(
                    torch_rungs[str(n)]["simultaneously_diagonalized_control_gap"] for n in SCALE_RUNGS
                ),
                "pass": bool(
                    max(torch_rungs[str(n)]["simultaneously_diagonalized_control_gap"] for n in SCALE_RUNGS)
                    <= TOL
                ),
            },
        },
        "tool_ablations": tool_ablations,
        "scale_ladder": {
            "rungs": scale_rungs,
            "scale_axis": "operator_dimension",
            "dense_state_closure_used": False,
            "pass": all_scale_pass,
        },
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "eligible_consumers": [],
        "allowed_claims": [
            "N01 finite operator noncommutation/order witness only",
            "canonical stage-1 root-constraint lego evidence only",
        ],
        "promotion_blockers": [
            "does not test Xi",
            "does not test Phi0",
            "does not test Axis0",
            "does not test flux",
            "does not test FEP",
            "does not test gravity",
            "does not establish PEPS3D manifold admission",
        ],
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["load_bearing_proof.smt_load_bearing", "sympy_exact_commutator"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_negatives": ["order_erased_projected_commuting_subalgebra", "simultaneously_diagonalized_commuting_family"],
        "negatives_run": ["order_erased_projected_commuting_subalgebra", "simultaneously_diagonalized_commuting_family"],
        "kill_conditions": ["helper verdict does not flip", "projected commuting control has nonzero commutator gap"],
        "required_artifacts": ["result_json", "scale_ladder", "proof_results", "controls", "tool_ablations"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "pass_rule": "all rungs pass torch/JAX/sympy, helper SMT differs real vs control, and helper ablations have nonzero recomputed deltas",
        "fail_rule": "any non-flipping helper proof, zero ablation delta, dense closure, or missing control fails the sim",
        "promotion_status": "keep_but_open",
        "classification": "lego",
        "promotion_allowed": False,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "result_summary": {
            "required_pass": required_pass,
            "min_torch_commutator_gap": min_torch_gap,
            "max_projected_control_gap": max_torch_control_gap,
            "max_jax_vs_pytorch_delta": max_jax_delta,
            "smt_load_bearing_pass": smt_load_bearing_pass,
            "sympy_exact_pass": sympy_pass,
            "all_ablations_pass": all_ablations_pass,
        },
        "required_pass": required_pass,
        "all_pass": required_pass,
    }

    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result_path": str(OUT_PATH.relative_to(ROOT)), "required_pass": required_pass}, indent=2))
    return 0 if required_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
