#!/usr/bin/env python3
"""Packet-local validator for geo_s2_connection_flux_foliation_v0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s2_connection_flux_foliation_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
SPEC = ROOT / "system_v6" / "receipts" / "s2_build_spec_20260610.md"
SPEC_COPY = SIM_DIR / "s2_build_spec_section_A.md"
DIRECTIVE = Path("/tmp/claude_s1_qubit_ladder_corrected_message_20260610.md")
DIRECTIVE_COPY = SIM_DIR / "directive_addendum.md"

ALLOWED_STRENGTHS = {
    "symbolic_identity",
    "closed_form_integral",
    "exact_integer_combinatorial",
    "rigorous_interval_bound",
    "measure_theorem",
    "finite_exhaustive_enumeration",
    "representation_theorem_with_constructive_receipt",
    "statistical_redundant_by_exact_route",
    "diagnostic_float_nonclaim",
    "open_with_reason",
}

REQUIRED_RECEIPTS = {"S2.A", "S2.F", "S2.H1", "S2.H2", "S2.H3", "S2.S", "S2.C", "S2.T", "S2.G", "S2.N", "S2.K"}
PIN_FIELDS = {"holonomy_quantity", "berry_formula", "phase_domain", "base_loop_count", "orientation_and_c1_sign"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section_a_text() -> str:
    lines = []
    in_section = False
    for line in SPEC.read_text(encoding="utf-8").splitlines():
        if line.startswith("## A. Positive S2 packet spec"):
            in_section = True
        elif line.startswith("## B. Negative-model specs"):
            break
        if in_section:
            lines.append(line)
    return "\n".join(lines) + "\n"


def main() -> int:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    receipts = payload["receipts"]
    gates = payload["build_gates"]
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(payload["schema_version"] == "three_engine_sim_result_v1", "schema drift")
    require(payload["all_pass"] is True, "envelope all_pass is not true")
    require(payload["classification"] == "scratch_diagnostic", "classification drift")
    require(payload["promotion_allowed"] is False, "promotion_allowed drift")
    require(payload["formal_admission_allowed"] is False, "formal_admission_allowed drift")
    require(all(value is True for value in gates.values()), "one or more envelope gates failed")
    require(REQUIRED_RECEIPTS <= set(receipts), "missing Section A receipt")

    require(set(payload["convention_pin"]) == PIN_FIELDS, "convention pin does not have exactly the five required fields")
    require(len({record["pin_sha256"] for record in payload["engines"].values()}) == 1, "engine PIN hashes differ")
    require(all(record["convention_pin"] == payload["convention_pin"] for record in payload["engines"].values()), "engine convention pins differ")

    for name, record in payload["engines"].items():
        source = ROOT / record["source_path"]
        require(source.exists(), f"{name} source missing")
        require(sha256(source) == record["source_sha256"], f"{name} source hash mismatch")
        require(record["reads_peer_result"] is False, f"{name} reads peer result")
        require(record["ran"] is True, f"{name} did not run")
        require(record["aligned_packages_load_bearing"], f"{name} has no aligned load-bearing package")

    require(SPEC_COPY.exists(), "Section A copy missing")
    require(SPEC_COPY.read_text(encoding="utf-8") == section_a_text(), "Section A copy differs from committed spec section")
    require(DIRECTIVE_COPY.exists(), "directive copy missing")
    if DIRECTIVE.exists():
        require(sha256(DIRECTIVE_COPY) == sha256(DIRECTIVE), "directive copy differs from /tmp directive")

    for rid, row in receipts.items():
        strength = row.get("exact_strength")
        require(strength in ALLOWED_STRENGTHS, f"{rid} has non-literal strength {strength!r}")
        if rid.startswith("S2."):
            require(row.get("convention_pin") == payload["convention_pin"], f"{rid} missing identical convention pin")

    s2a = receipts["S2.A"]
    require(s2a["pass"] is True, "S2.A failed")
    require("differentiates" in s2a["route"], "S2.A route does not state derivation")
    jax_source = (ROOT / payload["engines"]["jax"]["source_path"]).read_text(encoding="utf-8")
    require("sp.diff" in jax_source and "sp.conjugate" in jax_source and "-sp.I" in jax_source, "JAX source does not derive A from spinor differential")

    s2f = receipts["S2.F"]
    require(s2f["data"]["curvature_eta_chi"] == "-2*sin(2*eta)", "S2.F curvature sign/value drift")
    require(s2f["data"]["wrong_sign_control"]["fails"] is True, "S2.F wrong-sign control does not fail")

    s2h1 = receipts["S2.H1"]
    require(s2h1["exact_strength"] == "diagnostic_float_nonclaim", "S2.H1 strength must stay diagnostic_float_nonclaim")
    require(s2h1["data"]["nonzero_rhs_rows_strictly_shrink"] is True, "S2.H1 nonzero rows do not shrink")
    require("closed form compared only after solve" in s2h1["data"]["method"], "S2.H1 does not state solve-before-compare route")

    s2c = receipts["S2.C"]["data"]
    require(s2c["chart_integral"] == "-4*pi", "S2.C chart integral drift")
    require(s2c["physical_base_integral"] == "-2*pi", "S2.C physical integral drift")
    require(s2c["reported_c1"] == "1", "S2.C c1 drift")

    s2t = receipts["S2.T"]["data"]
    require(s2t["chart_area"] == "4*pi**2*sin(2*eta)", "S2.T chart area drift")
    require(s2t["physical_area"] == "2*pi**2*sin(2*eta)", "S2.T physical area drift")
    require(s2t["double_cover_reason"] == "(phi, chi) ~ (phi + pi, chi + pi)", "S2.T double-cover reason missing")

    for row in receipts["S2.G"]["data"]["rows"]:
        require(row["N"] % 2 == 0, "S2.G odd N row present")
        require(row["physical_points"] * 2 == row["chart_points"], f"S2.G N={row['N']} double-cover count fails")
        require(row["naive_control_fails"] is True, f"S2.G N={row['N']} naive control did not fail")

    s2i = receipts["S2.I"]
    require(s2i["exact_strength"] == "rigorous_interval_bound", "S2.I interval strength drift")
    require("no float-tail boxing" in s2i["method"], "S2.I interval route is not marked as genuine endpoint enclosure")
    require(s2i["pass"] is True, "S2.I interval receipt failed")

    require(receipts["S2.K"]["data"]["eta"] == "pi/4", "S2.K eta drift")
    require(receipts["S2.K"]["data"]["physical_area"] == "2*pi**2", "S2.K area drift")
    require(receipts["S2.K"]["data"]["lifted_holonomy"] == "0", "S2.K holonomy drift")

    f01 = receipts["F01_finitude_receipt"]
    require(f01["pass"] is True and f01["exact_strength"] == "exact_integer_combinatorial", "F01 grid finitude receipt invalid")
    n01 = receipts["N01_noncommutation_receipt"]
    require(n01["status"] == "not_scoped" and n01["pass"] is True, "N01 not-scoped boundary invalid")

    proofs = payload["crossover_proofs"]
    for key in ["z3", "cvc5", "julia_z3", "pytorch_z3", "pytorch_cvc5"]:
        require(proofs[key]["verdict"] == "unsat", f"{key} proof verdict drift")
        require(proofs[key]["load_bearing"] is True, f"{key} proof not load-bearing")
    require(proofs["z3"]["asserted_precomputed_boolean"] is False, "z3 proof binds boolean")
    require(proofs["cvc5"]["asserted_precomputed_boolean"] is False, "cvc5 proof binds boolean")
    require(proofs["pytorch_z3"]["asserted_precomputed_boolean"] is False, "pytorch z3 proof binds boolean")
    require(payload["build_gates"]["exact_smt_can_fail_controls"] is True, "can-fail SMT controls gate false")
    require(payload["build_gates"]["two_to_one_double_cover_handled"] is True, "2:1 double-cover gate false")

    print(json.dumps({"ok": not errors, "errors": errors, "result_json": str(RESULT.relative_to(ROOT))}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
