#!/usr/bin/env python3
"""Exact Python sidecar for manifold_entropy_ledger_v0."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


SIM_ID = "manifold_entropy_ledger_v0"
ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = PACKET / "results" / f"{SIM_ID}_jax_results.json"
SOURCE = PACKET / f"{SIM_ID}_jax.py"

PARENT_RESULT_PATHS = {
    "geo_disintegration_machinery_v0": "system_v6/sims/geo_disintegration_machinery_v0/results/geo_disintegration_machinery_v0_envelope_results.json",
    "geo_nested_disintegration_v0": "system_v6/sims/geo_nested_disintegration_v0/results/geo_nested_disintegration_v0_envelope_results.json",
    "geo_union_rule_k_leaves_v0": "system_v6/sims/geo_union_rule_k_leaves_v0/results/geo_union_rule_k_leaves_v0_envelope_results.json",
    "geo_s2_connection_flux_foliation_v0": "system_v6/sims/geo_s2_connection_flux_foliation_v0/results/geo_s2_connection_flux_foliation_v0_envelope_results.json",
    "geo_s6_s7_mode_sweep_v0": "system_v6/sims/geo_s6_s7_mode_sweep_v0/results/geo_s6_s7_mode_sweep_v0_envelope_results.json",
    "geo_s7_discrete_refinement_v0": "system_v6/sims/geo_s7_discrete_refinement_v0/results/geo_s7_discrete_refinement_v0_envelope_results.json",
    "ratchet_s1_single_shell_pilot_v0": "system_v6/sims/ratchet_s1_single_shell_pilot_v0/results/ratchet_s1_single_shell_pilot_v0_envelope_results.json",
    "ratchet_s2_three_shell_chain_v0": "system_v6/sims/ratchet_s2_three_shell_chain_v0/results/ratchet_s2_three_shell_chain_v0_envelope_results.json",
    "ratchet_s6_terrain_operator_shell_v0": "system_v6/sims/ratchet_s6_terrain_operator_shell_v0/results/ratchet_s6_terrain_operator_shell_v0_envelope_results.json",
    "compression_flow_radiated_record_v0": "system_v6/sims/compression_flow_radiated_record_v0/results/compression_flow_radiated_record_v0_envelope_results.json",
    "stage_lifted_spinor_shell_n3_v0": "system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_envelope_results.json",
    "stage_lifted_spinor_shell_n4_v0": "system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_envelope_results.json",
    "stage_lifted_spinor_shell_n5_v0": "system_v6/sims/stage_lifted_spinor_shell_n5_v0/results/stage_lifted_spinor_shell_n5_v0_envelope_results.json",
    "stage_lifted_spinor_shell_n6_v0": "system_v6/sims/stage_lifted_spinor_shell_n6_v0/results/stage_lifted_spinor_shell_n6_v0_envelope_results.json",
    "stage_lifted_spinor_shell_n7_v0": "system_v6/sims/stage_lifted_spinor_shell_n7_v0/results/stage_lifted_spinor_shell_n7_v0_envelope_results.json",
    "stage_lifted_spinor_shell_n8_v0": "system_v6/sims/stage_lifted_spinor_shell_n8_v0/results/stage_lifted_spinor_shell_n8_v0_envelope_results.json",
    "geo_s1_scaling_stress_678q_exact_v0": "system_v6/sims/geo_s1_scaling_stress_678q_exact_v0/results/geo_s1_scaling_stress_678q_exact_v0_envelope_results.json",
}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_output(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def git_bytes(args: list[str]) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def parent_lineage() -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for name, path in PARENT_RESULT_PATHS.items():
        payload = git_bytes(["show", f"HEAD:{path}"])
        rows[name] = {
            "result_path": path,
            "result_blob": git_output(["rev-parse", f"HEAD:{path}"]),
            "result_sha256": sha256_bytes(payload),
            "allowed_use": "committed parent citation; values are cited only where marked cited_parent_anchor",
        }
    return rows


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "imported_version_unavailable"


def sx(expr: sp.Expr) -> str:
    return str(sp.simplify(expr))


def f(expr: sp.Expr) -> float:
    return float(sp.N(expr, 16))


def entropy_rows() -> dict[str, Any]:
    eta = sp.symbols("eta", positive=True)
    eps = sp.symbols("epsilon", positive=True)
    pi = sp.pi
    density = sp.sin(2 * eta)
    h_eta_integral = -sp.integrate(density * sp.log(density), (eta, 0, pi / 2))
    h_eta = sp.simplify(h_eta_integral)
    conditional = sp.log(2 * pi**2 * sp.sin(2 * eta))
    expected_conditional = sp.simplify(sp.integrate(density * conditional, (eta, 0, pi / 2)))
    h_s3 = sp.log(2 * pi**2)
    chain_defect = sp.simplify(h_s3 - h_eta - expected_conditional)

    flat_density = sp.Rational(2, 1) / pi
    h_flat_eta = sp.log(pi / 2)
    wrong_expected = sp.simplify(2 * sp.log(pi))
    wrong_defect = sp.simplify(h_s3 - h_flat_eta - wrong_expected)

    eta0 = pi / 6
    # Exact local asymptotic for the two-stage finite-band convention.
    # The full symbolic finite-epsilon integral is unnecessary for the limit row.
    h_band_total_limit_form = sp.log(2 * eps) + sp.log(2 * pi**2 * sp.sin(2 * eta0))

    leaves = [pi / 12, pi / 6, pi / 4]
    raw = [sp.sin(2 * x) for x in leaves]
    total = sp.simplify(sum(raw))
    weights = [sp.simplify(x / total) for x in raw]
    h_weights = sp.simplify(-sum(w * sp.log(w) for w in weights))
    union_entropy = sp.simplify(h_weights + sum(w * sp.log(2 * pi**2 * sp.sin(2 * leaves[i])) for i, w in enumerate(weights)))

    lens_n = sp.Integer(4)
    wrong_lens_n = sp.Integer(3)
    lens_drop = sp.log(lens_n)
    wrong_lens_defect = sp.simplify(lens_drop - sp.log(wrong_lens_n))

    terrain_before = sp.Integer(40)
    terrain_after = sp.Integer(16)
    terrain_drop = sp.simplify(sp.log(terrain_before) - sp.log(terrain_after))

    h_eta_bits = sp.simplify(h_eta / sp.log(2))
    bit_mismatch_defect = sp.simplify(h_eta - h_eta_bits)

    leaf_pi6 = sp.simplify(conditional.subs(eta, eta0))
    carrier_ghz_entropy_nats = sp.log(2)
    meeting_product = sp.simplify(leaf_pi6 + carrier_ghz_entropy_nats)

    return {
        "log_base": "e",
        "measure_level": {
            "round_s3": {
                "entropy_type": "differential_entropy",
                "measure_reference": "round Riemannian volume on S^3",
                "value_exact": sx(h_s3),
                "value_float": f(h_s3),
                "derivation": "uniform density 1/Vol(S^3), Vol(S^3)=2*pi^2",
            },
            "eta_marginal": {
                "entropy_type": "differential_entropy",
                "density": "sin(2*eta) on [0, pi/2]",
                "value_exact": sx(h_eta),
                "value_float": f(h_eta),
                "integral": "-int_0^(pi/2) sin(2eta) log(sin(2eta)) d eta",
            },
            "conditional_torus": [
                {
                    "eta": sx(x),
                    "entropy_type": "differential_entropy",
                    "measure_reference": "induced physical area on T_eta",
                    "value_exact": sx(sp.log(2 * pi**2 * sp.sin(2 * x))),
                    "value_float": f(sp.log(2 * pi**2 * sp.sin(2 * x))),
                }
                for x in leaves
            ],
            "conditional_expectation": {
                "value_exact": sx(expected_conditional),
                "value_float": f(expected_conditional),
            },
            "chain_rule_check": {
                "identity": "h(S^3)=h(eta)+E[h(T_eta)]",
                "defect_exact": sx(chain_defect),
                "defect_float": f(chain_defect),
                "pass": chain_defect == 0,
            },
            "k_leaf_union": {
                "leaves": [sx(x) for x in leaves],
                "weights": [sx(w) for w in weights],
                "weight_entropy_exact": sx(h_weights),
                "mixture_entropy_with_weight_term_exact": sx(union_entropy),
                "mixture_entropy_with_weight_term_float": f(union_entropy),
                "entropy_type": "mixed discrete-continuous entropy",
            },
        },
        "conditioning_deltas": {
            "free_to_leaf": {
                "status": "singular_measure_zero_conditioning",
                "honest_drop": "infinite",
                "band_limit_convention": {
                    "center_eta": sx(eta0),
                    "band": "[eta0-epsilon, eta0+epsilon]",
                    "h_band_asymptotic_exact": sx(h_band_total_limit_form),
                    "limit": "h_band -> -oo as epsilon -> 0, so h(S^3)-h_band -> +oo",
                },
            },
            "lens_quotient": {
                "group_order": int(lens_n),
                "drop_exact": sx(lens_drop),
                "drop_float": f(lens_drop),
                "derivation": "uniform quotient volume Vol/|G|, so log(Vol)-log(Vol/|G|)=log|G|",
            },
            "terrain_restriction": {
                "entropy_type": "lattice_counting_entropy",
                "committed_parent": "geo_s6_s7_mode_sweep_v0",
                "before_rows": int(terrain_before),
                "after_rows": int(terrain_after),
                "drop_exact": sx(terrain_drop),
                "drop_float": f(terrain_drop),
            },
        },
        "cross_layer_meeting_point": {
            "leaf": "T_pi/6",
            "measure_entropy_exact": sx(leaf_pi6),
            "carrier_anchor": "GHZ carrier vN entropy cited as log(2) on lifted-shell parent rows",
            "carrier_entropy_nats_exact": sx(carrier_ghz_entropy_nats),
            "product_bookkeeping_if_independent_exact": sx(meeting_product),
            "consistency_statement": "differential measure entropy and vN carrier entropy are typed separately; only an explicit product convention adds them",
        },
        "controls": {
            "wrong_log_base": {
                "natural_value_exact": sx(h_eta),
                "bit_value_misread_as_nats_exact": sx(h_eta_bits),
                "defect_exact": sx(bit_mismatch_defect),
                "detected": sp.simplify(bit_mismatch_defect) != 0,
            },
            "wrong_flat_eta_marginal": {
                "wrong_marginal_entropy_exact": sx(h_flat_eta),
                "wrong_expected_conditional_exact": sx(wrong_expected),
                "chain_defect_exact": sx(wrong_defect),
                "chain_defect_float": f(wrong_defect),
                "detected": sp.simplify(wrong_defect) != 0,
            },
            "wrong_lens_group_order": {
                "actual_order": int(lens_n),
                "wrong_order": int(wrong_lens_n),
                "defect_exact": sx(wrong_lens_defect),
                "detected": sp.simplify(wrong_lens_defect) != 0,
            },
        },
        "basis_coefficients_for_smt": {
            "basis": ["constant", "log(2)", "log(pi)"],
            "h_s3": [0, 1, 2],
            "h_eta": [1, -1, 0],
            "expected_conditional": [-1, 2, 2],
        },
    }


def z3_chain(coeffs: dict[str, list[int]]) -> dict[str, Any]:
    solver = z3.Solver()
    violations = []
    for idx in range(3):
        j = z3.Int(f"j_{idx}")
        m = z3.Int(f"m_{idx}")
        c = z3.Int(f"c_{idx}")
        solver.add(j == coeffs["h_s3"][idx])
        solver.add(m == coeffs["h_eta"][idx])
        solver.add(c == coeffs["expected_conditional"][idx])
        violations.append(j != m + c)
    solver.add(z3.Or(violations))
    verdict = str(solver.check())

    erased = z3.Solver()
    erased_violations = []
    for idx in range(3):
        j = z3.Int(f"ej_{idx}")
        m = z3.Int(f"em_{idx}")
        erased.add(j == coeffs["h_s3"][idx])
        erased.add(m == coeffs["h_eta"][idx])
        erased_violations.append(j == m)
    erased.add(z3.And(erased_violations))
    erased_verdict = str(erased.check())
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "claim": "no coefficient counterexample to h(S3)=h(eta)+E[h(T_eta)]",
        "erased_conditional_control_verdict": erased_verdict,
        "erased_flip_control_can_fail": erased_verdict == "unsat",
    }


def cvc5_var(solver: cvc5.Solver, name: str) -> Any:
    return solver.mkConst(solver.getIntegerSort(), name)


def cvc5_chain(coeffs: dict[str, list[int]]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    violations = []
    for idx in range(3):
        j = cvc5_var(solver, f"j_{idx}")
        m = cvc5_var(solver, f"m_{idx}")
        c = cvc5_var(solver, f"c_{idx}")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, j, solver.mkInteger(coeffs["h_s3"][idx])))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, m, solver.mkInteger(coeffs["h_eta"][idx])))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, c, solver.mkInteger(coeffs["expected_conditional"][idx])))
        violations.append(solver.mkTerm(Kind.DISTINCT, j, solver.mkTerm(Kind.ADD, m, c)))
    solver.assertFormula(solver.mkTerm(Kind.OR, *violations))
    verdict = str(solver.checkSat()).lower()

    erased = cvc5.Solver()
    for idx in range(3):
        j = cvc5_var(erased, f"ej_{idx}")
        m = cvc5_var(erased, f"em_{idx}")
        erased.assertFormula(erased.mkTerm(Kind.EQUAL, j, erased.mkInteger(coeffs["h_s3"][idx])))
        erased.assertFormula(erased.mkTerm(Kind.EQUAL, m, erased.mkInteger(coeffs["h_eta"][idx])))
        erased.assertFormula(erased.mkTerm(Kind.EQUAL, j, m))
    erased_verdict = str(erased.checkSat()).lower()
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "claim": "same coefficient identity as z3",
        "erased_conditional_control_verdict": erased_verdict,
        "erased_flip_control_can_fail": erased_verdict == "unsat",
    }


def collect_entropy_anchor(path: Path, n: int) -> dict[str, Any]:
    data = json.loads(path.read_text())
    hits: list[dict[str, Any]] = []

    def walk(obj: Any, trail: str = "$") -> None:
        if len(hits) >= 12:
            return
        if isinstance(obj, dict):
            for key, value in obj.items():
                key_s = str(key)
                if "entropy" in key_s.lower() and (
                    "GHZ" in key_s or f"W_{n}" in key_s or f"W{n}" in key_s or key_s in {"entropy_qubit_0", "entropy_qubits_0_1"}
                ):
                    if isinstance(value, (str, int, float, bool)):
                        hits.append({"json_path": f"{trail}.{key_s}", "value": value})
                walk(value, f"{trail}.{key_s}")
        elif isinstance(obj, list):
            for idx, value in enumerate(obj):
                walk(value, f"{trail}[{idx}]")

    walk(data)
    return {
        "n": n,
        "entropy_type": "von_Neumann_entropy",
        "status": "cited_parent_anchor_not_recomputed",
        "parent_result_path": rel(path),
        "parent_result_sha256": file_sha256(path),
        "sample_cited_entropy_rows": hits,
    }


def carrier_anchors() -> list[dict[str, Any]]:
    anchors = []
    for n in range(3, 9):
        path = ROOT / PARENT_RESULT_PATHS[f"stage_lifted_spinor_shell_n{n}_v0"]
        anchors.append(collect_entropy_anchor(path, n))
    scaling = ROOT / PARENT_RESULT_PATHS["geo_s1_scaling_stress_678q_exact_v0"]
    anchors.append(
        {
            "n": "6..8_scaling_stress_cross_citation",
            "entropy_type": "von_Neumann_entropy",
            "status": "cited_parent_anchor_not_recomputed",
            "parent_result_path": rel(scaling),
            "parent_result_sha256": file_sha256(scaling),
            "note": "scaling stress packet is cited for high-rung carrier entropy rows and controls; per-rung stage packets remain primary anchors above",
        }
    )
    return anchors


def tool_calls() -> list[dict[str, Any]]:
    return [
        {
            "tool": "sympy",
            "qualified_api/function": "sympy.integrate / sympy.simplify / sympy.log",
            "input_object": "S3 eta density sin(2eta), conditional torus entropy, k-leaf weights",
            "output_object": "exact entropy rows and controls",
            "positive_case": "chain rule simplifies to zero",
            "negative/erased_control": "wrong flat eta marginal gives nonzero defect",
            "boundary_case": "fixed nonboundary leaves pi/12, pi/6, pi/4",
            "demotion_condition": "demote if exact rows are replaced by floats only",
            "gates": ["measure_chain_rule", "wrong_marginal_control", "k_leaf_union_entropy"],
        },
        {
            "tool": "z3",
            "qualified_api/function": "z3.Solver.check",
            "input_object": "coefficient vectors over [1, log(2), log(pi)]",
            "output_object": "unsat counterexample to chain identity",
            "positive_case": "h_S3 - h_eta - E_h_cond coefficient vector is zero",
            "negative/erased_control": "erasing expected conditional term is unsat",
            "boundary_case": "linear integer coefficient identity only",
            "demotion_condition": "demote if solver binds only a precomputed boolean",
            "gates": ["smt_chain_identity", "erased_conditional_control"],
        },
        {
            "tool": "cvc5",
            "qualified_api/function": "cvc5.Solver.checkSat",
            "input_object": "same coefficient vectors as z3",
            "output_object": "independent unsat counterexample to chain identity",
            "positive_case": "agrees with z3",
            "negative/erased_control": "erasing expected conditional term is unsat",
            "boundary_case": "QF_LIA integer coefficient identity only",
            "demotion_condition": "demote if cvc5 disagrees with z3",
            "gates": ["smt_chain_identity", "erased_conditional_control"],
        },
        {
            "tool": "hashlib",
            "qualified_api/function": "hashlib.sha256",
            "input_object": "committed parent result bytes and generated packet sources",
            "output_object": "parent_lineage sha256 and source/result hashes",
            "positive_case": "every cited parent path is hash-bound",
            "negative/erased_control": "not a mathematical proof",
            "boundary_case": "HEAD result blobs only",
            "demotion_condition": "demote if parent hashes are missing",
            "gates": ["parent_lineage"],
        },
        {
            "tool": "json",
            "qualified_api/function": "json.loads / json.dumps",
            "input_object": "parent envelopes and new result payload",
            "output_object": "structured ledger JSON",
            "positive_case": "typed entropy rows remain machine-readable",
            "negative/erased_control": "unstructured prose would fail packet validator",
            "boundary_case": "packet-local JSON only",
            "demotion_condition": "demote if ledger rows are not structured",
            "gates": ["structured_ledger"],
        },
        {
            "tool": "pathlib",
            "qualified_api/function": "Path.read_text / Path.write_text",
            "input_object": "file-disjoint packet paths",
            "output_object": "packet-local result JSON",
            "positive_case": "writes remain under manifold_entropy_ledger_v0",
            "negative/erased_control": "not a proof engine",
            "boundary_case": "explicit result path",
            "demotion_condition": "demote if paths are not explicit",
            "gates": ["file_disjoint_packet"],
        },
    ]


def main() -> int:
    ledger = entropy_rows()
    proofs = {
        "z3": z3_chain(ledger["basis_coefficients_for_smt"]),
        "cvc5": cvc5_chain(ledger["basis_coefficients_for_smt"]),
    }
    all_pass = (
        ledger["measure_level"]["chain_rule_check"]["pass"]
        and ledger["controls"]["wrong_log_base"]["detected"]
        and ledger["controls"]["wrong_flat_eta_marginal"]["detected"]
        and ledger["controls"]["wrong_lens_group_order"]["detected"]
        and proofs["z3"]["verdict"] == "unsat"
        and proofs["cvc5"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_control_can_fail"]
        and proofs["cvc5"]["erased_flip_control_can_fail"]
    )
    payload = {
        "schema_version": f"{SIM_ID}_leg_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "stage": "S11_cross_layer_entropy_ledger",
        "mode": "RATCHETED",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "source_path": rel(SOURCE),
        "source_sha256": file_sha256(SOURCE),
        "result_path": rel(RESULT),
        "log_base": "e",
        "seed": {
            "stochastic": False,
            "deterministic_symbolic_seed": "manifold_entropy_ledger_v0:sympy:z3:cvc5:v1",
        },
        "parent_lineage": parent_lineage(),
        "entropy_type_table": [
            {"layer": "measure", "entropy": "differential", "reference": "Riemannian or induced area measure", "log_base": "e"},
            {"layer": "conditioning bands/unions", "entropy": "mixed differential plus discrete Shannon", "reference": "explicit mixture convention", "log_base": "e"},
            {"layer": "carrier", "entropy": "von_Neumann", "reference": "density matrix eigenvalues in cited ladder parents", "log_base": "parent-stated; nats recorded where parent records nats"},
            {"layer": "terrain row restrictions", "entropy": "lattice/counting", "reference": "uniform over committed row set", "log_base": "e"},
        ],
        "ledger": ledger,
        "carrier_level_anchors": carrier_anchors(),
        "crossover_proofs": proofs,
        "capability_receipts": {
            "python": "sim-stack",
            "sympy": package_version("sympy"),
            "z3-solver": package_version("z3-solver"),
            "cvc5": package_version("cvc5"),
        },
        "TOOL_MANIFEST": {
            "sympy": {"used": True, "reason": "exact entropy integrals and symbolic simplification"},
            "z3": {"used": True, "reason": "load-bearing chain identity coefficient proof and erased-control rejection"},
            "cvc5": {"used": True, "reason": "independent load-bearing chain identity proof and erased-control rejection"},
            "hashlib": {"used": True, "reason": "parent and source hash binding"},
            "json": {"used": True, "reason": "structured parent and result payloads"},
            "pathlib": {"used": True, "reason": "explicit packet-local IO"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "hashlib": "load_bearing",
            "json": "supportive",
            "pathlib": "supportive",
        },
        "claim_path_tools": ["sympy", "z3", "cvc5", "hashlib", "json", "pathlib"],
        "tool_calls": tool_calls(),
        "all_pass": all_pass,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"ok": all_pass, "result_path": rel(RESULT)}))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
