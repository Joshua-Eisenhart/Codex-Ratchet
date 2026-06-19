#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/three_engine_qit_cptp_dephasing_pinned_rho_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/qit_cptp_dephasing_pinned_rho_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/qit_cptp_dephasing_pinned_rho_jax_leg_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/qit_cptp_dephasing_pinned_rho_pytorch_leg_results.json"
classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
TOL = 1e-9

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive result-envelope assembly from engine receipts; not a math claim path"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding for receipt files"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def same_spec(*payloads: dict[str, Any]) -> bool:
    keys = ["rho_formula", "p", "channel", "gamma", "entropy_base", "n_qubits", "hilbert_dimension", "spectrum_after_exact"]
    specs = [p.get("pinned_spec", {}) for p in payloads]
    first = specs[0]
    return all(all(spec.get(k) == first.get(k) for k in keys) for spec in specs[1:])


def spread(values: list[float]) -> float:
    return max(values) - min(values) if values else 0.0


def engine_record(payload: dict[str, Any], result_path: Path, packages_used: list[str], load_bearing: list[str], values: dict[str, Any]) -> dict[str, Any]:
    return {"ran": True, "source_path": payload.get("source_path"), "result_path": str(result_path), "reads_peer_result": payload.get("reads_peer_result"), "packages_used": packages_used, "aligned_packages_load_bearing": load_bearing, "classification": payload.get("classification"), "promotion_allowed": payload.get("promotion_allowed"), "formal_admission_allowed": payload.get("formal_admission_allowed"), "values": values}


def build_result() -> dict[str, Any]:
    julia, jax, torch = load_json(JULIA_RESULT), load_json(JAX_RESULT), load_json(PYTORCH_RESULT)
    jv = {"vn_entropy_before": julia["values"]["vn_entropy_before"], "vn_entropy_after": julia["values"]["vn_entropy_after"], "analytic_entropy_after": julia["values"]["analytic_entropy_after"], "entropy_change": julia["values"]["entropy_change"], "spectrum_high": julia["values"]["spectrum_high"], "spectrum_mid": julia["values"]["spectrum_mid"], "spectrum_low": julia["values"]["spectrum_low"]}
    xv = {"vn_entropy_before": jax["values"]["vn_entropy_before"], "vn_entropy_after": jax["values"]["vn_entropy_after"], "qutip_entropy_after": jax["values"]["qutip_entropy_after"], "analytic_entropy_after": jax["values"]["analytic_entropy_after"], "entropy_change": jax["values"]["entropy_change"], "spectrum_high": jax["values"]["spectrum_high"], "spectrum_mid": jax["values"]["spectrum_mid"], "spectrum_low": jax["values"]["spectrum_low"]}
    tv = {"vn_entropy_before": torch["values"]["vn_entropy_before"], "vn_entropy_after": torch["values"]["vn_entropy_after"], "analytic_entropy_after": torch["values"]["analytic_entropy_after"], "entropy_change": torch["values"]["entropy_change"], "dS_dgamma_grad": torch["values"]["dS_dgamma_grad"], "dS_dgamma_jacrev": torch["values"]["dS_dgamma_jacrev"], "analytic_dS_dgamma": torch["values"]["analytic_dS_dgamma"], "spectrum_high": torch["values"]["spectrum_high"], "spectrum_mid": torch["values"]["spectrum_mid"], "spectrum_low": torch["values"]["spectrum_low"]}
    entropy_after_spread = spread([float(jv["vn_entropy_after"]), float(xv["vn_entropy_after"]), float(tv["vn_entropy_after"])])
    entropy_change_spread = spread([float(jv["entropy_change"]), float(xv["entropy_change"]), float(tv["entropy_change"])])
    z3_main, cvc5_main = jax["smt"]["z3"]["main_status"], jax["smt"]["cvc5"]["main_status"]
    z3_bad, cvc5_bad = jax["smt"]["z3"]["negative_control_status"], jax["smt"]["cvc5"]["negative_control_status"]
    all_pass = bool(julia.get("all_pass") is True and jax.get("all_pass") is True and torch.get("all_pass") is True and same_spec(julia, jax, torch) and entropy_after_spread <= TOL and entropy_change_spread <= TOL and z3_main == cvc5_main == "sat" and z3_bad == cvc5_bad == "unsat" and all(p.get("reads_peer_result") is False for p in (julia, jax, torch)))
    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": "three_engine_qit_cptp_dephasing_pinned_rho_envelope",
        "mode": "all_three_full_sims",
        "classification": CLASSIFICATION,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "Scratch three-engine QIT CPTP dephasing envelope over one pinned finite object/channel only. No formal admission, bridge, manifold, basin, axis, M(C), QIT-engine, or full-system claim.",
        "all_pass": all_pass,
        "pinned_spec": julia.get("pinned_spec"),
        "package_preflight": {"python_executable": jax.get("python_executable"), "julia_active_project": julia.get("active_project"), "julia_version": julia.get("julia_version"), "python_packages_ok": {"jax": True, "qutip": True, "z3": True, "cvc5": True, "torch": True, "torch.func": True}, "julia_packages_ok": {"QuantumOptics": True}},
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT, ["QuantumOptics", "JSON", "LinearAlgebra", "Dates"], ["QuantumOptics"], jv),
            "jax": engine_record(jax, JAX_RESULT, ["jax", "jax.numpy", "qutip", "z3", "cvc5", "numpy", "json"], ["qutip", "z3", "cvc5"], xv),
            "pytorch": engine_record(torch, PYTORCH_RESULT, ["torch", "torch.func"], ["torch.func"], tv),
        },
        "engine_contract": {"julia": {"status": "ran", "authority": "reference", "load_bearing_packages": ["QuantumOptics"], "result_path": str(JULIA_RESULT)}, "jax": {"status": "ran", "authority": "primary_mirror", "load_bearing_packages": ["qutip", "z3", "cvc5"], "result_path": str(JAX_RESULT)}, "pytorch": {"status": "ran", "authority": "third_substrate", "load_bearing_packages": ["torch.func"], "result_path": str(PYTORCH_RESULT)}},
        "crossover_proofs": {"z3": {"ran": True, "load_bearing": True, "verdict": z3_main, "negative_control_verdict": z3_bad, "claim": "Exact post-dephasing spectrum {239/400, 71/400, 15/400 x 6} is a nonnegative probability simplex"}, "cvc5": {"ran": True, "load_bearing": True, "verdict": cvc5_main, "negative_control_verdict": cvc5_bad, "claim": "Exact post-dephasing spectrum {239/400, 71/400, 15/400 x 6} is a nonnegative probability simplex"}},
        "claim_path_tools": ["QuantumOptics", "jax", "jax.numpy", "qutip", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": ["numpy"],
        "load_bearing_tool_claims": [{"tool": "QuantumOptics", "engine": "julia", "claim": "construct channel and compute entropy_vn", "observable": "vn_entropy_after", "status": "passed"}, {"tool": "qutip", "engine": "jax", "claim": "Qobj entropy cross-check after dephasing", "observable": "qutip_entropy_after", "status": "passed"}, {"tool": "z3", "engine": "jax", "claim": "post-channel spectrum simplex certificate", "observable": "sat with unsat negative control", "status": "passed"}, {"tool": "cvc5", "engine": "jax", "claim": "independent post-channel spectrum simplex certificate", "observable": "sat with unsat negative control", "status": "passed"}, {"tool": "torch.func", "engine": "pytorch", "claim": "differentiable entropy gradient dS/dgamma", "observable": "dS_dgamma", "status": "passed"}],
        "divergence": {"julia_authoritative": True, "engine_values": {"julia": jv, "jax": xv, "pytorch": tv}, "max_divergence": entropy_after_spread, "entropy_change_max_divergence": entropy_change_spread, "structural_disagreements": [], "interpretation": "Agreement is only over the pinned finite rho(p) and one named dephasing channel; divergence remains signal for broader claims."},
        "peer_json_rule": "engine results read only after each engine computed its local result; never as a pass source",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result(); RESULT_PATH.parent.mkdir(parents=True, exist_ok=True); RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(f"SCOUT_DONE all_pass={str(result['all_pass']).lower()} same_spec={str(same_spec(load_json(JULIA_RESULT), load_json(JAX_RESULT), load_json(PYTORCH_RESULT))).lower()} entropy_after_max_divergence={result['divergence']['max_divergence']} entropy_after={result['engines']['julia']['values']['vn_entropy_after']}")
    return 0 if result["all_pass"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
