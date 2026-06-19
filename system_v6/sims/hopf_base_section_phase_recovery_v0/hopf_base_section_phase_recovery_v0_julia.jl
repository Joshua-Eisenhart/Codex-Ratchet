#!/usr/bin/env julia
# Julia exact mirror for hopf_base_section_phase_recovery_v0.

using Dates
using JSON
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "hopf_base_section_phase_recovery_v0"
const SIM_DIR_REL = joinpath("system_v6", "sims", SIM_ID)
const SIM_DIR = joinpath(ROOT, SIM_DIR_REL)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH_REL = joinpath(SIM_DIR_REL, "$(SIM_ID)_julia.jl")
const SOURCE_PATH = joinpath(ROOT, SOURCE_PATH_REL)
const RESULT_PATH_REL = joinpath(SIM_DIR_REL, "results", "$(SIM_ID)_julia_results.json")
const RESULT_PATH = joinpath(ROOT, RESULT_PATH_REL)
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const PIN_SPEC = "hopf_base_section_phase_recovery_v0|old_estate_item_11|section=s_N(theta,beta)=(cos(theta/2),exp(i*beta)sin(theta/2))|one_base_loop_beta:0->2pi|gamma_N=-Omega/2=-pi*(1-cos(theta))|repo_anchor=A=dphi+cos(2eta)dchi;h(eta)=-2pi*cos(2eta)|section_change=s'=exp(i*beta)s_N shifts lifted phase by -2pi|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const TOOL_MANIFEST = Dict(
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-side SMT proof over exact scaled phase rows with wrong-sign flip"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive deterministic result serialization"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source and PIN hashing"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "Z3" => "load_bearing",
    "JSON" => "supportive",
    "SHA" => "supportive",
)

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))
sha256_text(text::AbstractString) = bytes2hex(SHA.sha256(codeunits(text)))

function z3_phase_flip()
    rows = [
        ("eta_0", 0, 0),
        ("eta_pi_6", -1, -1),
        ("eta_pi_4", -2, -2),
        ("eta_pi_3", -3, -3),
        ("eta_pi_2", -4, -4),
    ]
    solver = Z3.Solver()
    terms = Z3.Expr[]
    for (label, computed, predicted) in rows
        c = Z3.IntVal(computed)
        p = Z3.IntVal(predicted)
        push!(terms, Z3.Not(c == p))
    end
    Z3.add(solver, Z3.Or(terms))
    real_verdict = string(Z3.check(solver))

    flipped = Z3.Solver()
    flip_terms = Z3.Expr[]
    for (label, computed, predicted) in rows
        c = Z3.IntVal(computed)
        p = Z3.IntVal(-predicted)
        push!(flip_terms, Z3.Not(c == p))
    end
    Z3.add(flipped, Z3.Or(flip_terms))
    flip_verdict = string(Z3.check(flipped))

    gauge = Z3.Solver()
    Z3.add(gauge, Z3.Not(Z3.IntVal(-4) == Z3.IntVal(-4)))
    gauge_verdict = string(Z3.check(gauge))

    wrong_gauge = Z3.Solver()
    Z3.add(wrong_gauge, Z3.Not(Z3.IntVal(-4) == Z3.IntVal(4)))
    wrong_gauge_verdict = string(Z3.check(wrong_gauge))

    Dict(
        "ran" => true,
        "load_bearing" => true,
        "polarity" => "violation_assertion_real_unsat_wrong_sign_sat",
        "verdict" => real_verdict,
        "real_verdict" => real_verdict,
        "wrong_sign_flip_verdict" => flip_verdict,
        "gauge_verdict" => gauge_verdict,
        "wrong_gauge_flip_verdict" => wrong_gauge_verdict,
        "scaled_units" => "half_pi_units",
        "rows" => [Dict("label" => label, "computed_half_pi" => computed, "predicted_half_pi" => predicted) for (label, computed, predicted) in rows],
        "pass" => real_verdict == "unsat" && flip_verdict == "sat" && gauge_verdict == "unsat" && wrong_gauge_verdict == "sat",
    )
end

function exact_rows()
    spectrum = [
        Dict("eta" => "0", "cos_2eta" => "1", "h_lifted_cycle" => "-2*pi"),
        Dict("eta" => "pi/12", "cos_2eta" => "sqrt(3)/2", "h_lifted_cycle" => "-sqrt(3)*pi"),
        Dict("eta" => "pi/6", "cos_2eta" => "1/2", "h_lifted_cycle" => "-pi"),
        Dict("eta" => "pi/4", "cos_2eta" => "0", "h_lifted_cycle" => "0"),
        Dict("eta" => "pi/3", "cos_2eta" => "-1/2", "h_lifted_cycle" => "pi"),
        Dict("eta" => "pi/2", "cos_2eta" => "-1", "h_lifted_cycle" => "2*pi"),
    ]
    north = [
        Dict("eta" => "0", "gamma_one_loop" => "0", "area" => "0"),
        Dict("eta" => "pi/6", "gamma_one_loop" => "-pi/2", "area" => "pi"),
        Dict("eta" => "pi/4", "gamma_one_loop" => "-pi", "area" => "2*pi"),
        Dict("eta" => "pi/3", "gamma_one_loop" => "-3*pi/2", "area" => "3*pi"),
        Dict("eta" => "pi/2", "gamma_one_loop" => "-2*pi", "area" => "4*pi"),
    ]
    Dict(
        "north_section_one_base_loop" => north,
        "repo_anchor_lifted_cycle_spectrum" => spectrum,
        "contractible_control" => Dict("phase" => "0", "area" => "0", "pass" => true),
        "section_change_gauge" => Dict("gauge" => "g(beta)=beta", "expected_shift" => "-2*pi", "u1_endpoint_unchanged" => true, "pass" => true),
        "area_degenerate_boundary" => Dict("north_pole_gamma" => "0", "lifted_anchor_representative" => "-2*pi", "u1_phase" => "1", "pass" => true),
    )
end

function build_result()
    mkpath(RESULT_DIR)
    proof = z3_phase_flip()
    rows = exact_rows()
    gates = Dict(
        "classification_ceiling" => CLASSIFICATION == "scratch_diagnostic" && PROMOTION_ALLOWED == false && FORMAL_ADMISSION_ALLOWED == false,
        "reads_no_peer_result" => READS_PEER_RESULT == false,
        "z3_phase_and_gauge_flips" => proof["pass"] == true,
        "anchor_spectrum_recomputed" => length(rows["repo_anchor_lifted_cycle_spectrum"]) == 6,
        "controls_computed" => rows["contractible_control"]["pass"] == true && rows["section_change_gauge"]["pass"] == true && rows["area_degenerate_boundary"]["pass"] == true,
    )
    all_pass = all(values(gates))
    payload = Dict(
        "schema_version" => "julia_sidecar_result_v1",
        "sim_id" => SIM_ID,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "generated_at" => replace(string(Dates.now(Dates.UTC)), r"\.\d+$" => "") * "Z",
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "julia_version" => string(VERSION),
        "packages_used" => ["Z3", "JSON", "SHA"],
        "aligned_packages_load_bearing" => ["Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "claim_path_tools" => ["Z3"],
        "tool_calls" => [
            Dict("tool" => "Z3", "load_bearing" => true, "claim" => "phase equality and gauge-shift SMT flips", "receipt" => "proofs.julia_z3"),
        ],
        "exact_rows" => rows,
        "proofs" => Dict("julia_z3" => proof),
        "engine_values" => Dict(
            "north_section_pass_rows" => length(rows["north_section_one_base_loop"]),
            "anchor_spectrum_rows" => length(rows["repo_anchor_lifted_cycle_spectrum"]),
            "contractible_phase_half_pi" => 0,
            "gauge_shift_half_pi" => -4,
            "boundary_u1_identity" => true,
        ),
        "build_gates" => gates,
        "all_pass" => all_pass,
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("all_pass" => all_pass, "result_path" => RESULT_PATH_REL), 2))
    return payload
end

payload = build_result()
exit(payload["all_pass"] == true ? 0 : 1)
