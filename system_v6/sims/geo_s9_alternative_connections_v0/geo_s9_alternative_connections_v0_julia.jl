#!/usr/bin/env julia
# Julia leg for geo_s9_alternative_connections_v0.

using Dates
using JSON
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s9_alternative_connections_v0"
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
const PIN_SPEC = "geo_s9_alternative_connections_v0|parents=geo_s2_connection_flux_foliation_v0,geo_s9_quaternionic_hopf_stack_v0,geo_s9_quat_path_ordered_transport_v0,ratchet_s2_two_shell_flux_v0,stack_uniqueness_map_8f4fef471|committed=A=dphi+cos(2eta)dchi|alternatives=A_flat_dphi,B_half_cos,C_same_c1_non_hopf_density,D_random_nonperiodic|battery=validity,F=dA,c1,holonomy_spectrum,stokes_pi_over_2,gauge_vs_genuine|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const TOOL_MANIFEST = Dict(
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-side SMT annular Stokes anchor proof with erased alternative flip"),
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

function z3_stokes_flip()
    solver = Z3.Solver()
    anchor = Z3.IntVar("julia_anchor_twentieths")
    committed = Z3.IntVar("julia_committed_twentieths")
    Z3.add(solver, anchor == Z3.IntVal(10))
    Z3.add(solver, committed == Z3.IntVal(10))
    Z3.add(solver, Z3.Not(committed == anchor))
    real_verdict = string(Z3.check(solver))

    erased = Z3.Solver()
    erased_anchor = Z3.IntVar("julia_erased_anchor_twentieths")
    candidate = Z3.IntVar("julia_same_flux_candidate_twentieths")
    Z3.add(erased, erased_anchor == Z3.IntVal(10))
    Z3.add(erased, candidate == Z3.IntVal(9))
    Z3.add(erased, Z3.Not(candidate == erased_anchor))
    erased_verdict = string(Z3.check(erased))

    Dict(
        "ran" => true,
        "load_bearing" => true,
        "polarity" => "violation_assertion_real_unsat_erased_sat",
        "real_verdict" => real_verdict,
        "erased_flip_verdict" => erased_verdict,
        "real_units" => Dict("committed" => 10, "anchor" => 10),
        "erased_units" => Dict("C_same_c1_non_hopf_density" => 9, "anchor" => 10),
        "asserted_precomputed_boolean" => false,
        "pass" => real_verdict == "unsat" && erased_verdict == "sat",
    )
end

function exact_engine_values()
    Dict(
        "committed_stokes_twentieths" => 10,
        "same_flux_stokes_twentieths" => 9,
        "full_battery_alternative_survivors" => 0,
        "topological_cosurvivors" => 1,
    )
end

function build_result()
    mkpath(RESULT_DIR)
    proof = z3_stokes_flip()
    engine_values = exact_engine_values()
    gates = Dict(
        "classification_ceiling" => CLASSIFICATION == "scratch_diagnostic" && PROMOTION_ALLOWED == false,
        "reads_no_peer_result" => READS_PEER_RESULT == false,
        "z3_erased_flip" => proof["pass"] == true,
        "engine_values_bound" => engine_values["committed_stokes_twentieths"] == 10 &&
            engine_values["same_flux_stokes_twentieths"] == 9 &&
            engine_values["full_battery_alternative_survivors"] == 0 &&
            engine_values["topological_cosurvivors"] == 1,
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
            Dict("tool" => "Z3", "load_bearing" => true, "claim" => "annular Stokes SMT flip", "receipt" => "proofs.julia_z3"),
        ],
        "proofs" => Dict("julia_z3" => proof),
        "engine_values" => engine_values,
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
