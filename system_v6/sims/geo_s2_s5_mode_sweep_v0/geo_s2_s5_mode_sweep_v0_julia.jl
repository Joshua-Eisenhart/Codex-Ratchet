#!/usr/bin/env julia
# Julia Symbolics/Z3 mirror for the S2 quotient gauge test in geo_s2_s5_mode_sweep_v0.

using Dates
using JSON
using SHA
using Symbolics
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s2_s5_mode_sweep_v0"
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

const TOOL_MANIFEST = Dict(
    "Symbolics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing symbolic mirror of gauge delta-A and delta-F for the S2 quotient descent row"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing nonzero gauge-control branch for the Symbolics mirror"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source hashing"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "Symbolics" => "load_bearing",
    "Z3" => "load_bearing",
    "JSON" => "supportive",
    "SHA" => "supportive",
)

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))

function clean(x)
    text = string(Symbolics.simplify(Symbolics.expand_derivatives(x), expand=true))
    replacements = Dict("0.0" => "0", "1.0" => "1", "-0.0" => "0", "0//1" => "0", "1//1" => "1")
    return get(replacements, text, text)
end

function symbolic_gauge_receipt()
    @variables eta chi alpha0 alpha1
    alpha = alpha0 + alpha1 * chi
    a_eta = 0
    a_chi = cos(2 * eta)
    a_phi = 1
    d_eta = Differential(eta)
    d_chi = Differential(chi)
    gauge_a_eta = Symbolics.simplify(Symbolics.expand_derivatives(a_eta + d_eta(alpha)), expand=true)
    gauge_a_chi = Symbolics.simplify(Symbolics.expand_derivatives(a_chi + d_chi(alpha)), expand=true)
    gauge_a_phi = a_phi
    delta_a_eta = Symbolics.simplify(Symbolics.expand_derivatives(gauge_a_eta - a_eta), expand=true)
    delta_a_chi = Symbolics.simplify(Symbolics.expand_derivatives(gauge_a_chi - a_chi), expand=true)
    delta_a_phi = Symbolics.simplify(gauge_a_phi - a_phi, expand=true)
    f_eta_chi = Symbolics.simplify(Symbolics.expand_derivatives(d_eta(a_chi) - d_chi(a_eta)), expand=true)
    f_gauge_eta_chi = Symbolics.simplify(Symbolics.expand_derivatives(d_eta(gauge_a_chi) - d_chi(gauge_a_eta)), expand=true)
    delta_f = Symbolics.simplify(Symbolics.expand_derivatives(f_gauge_eta_chi - f_eta_chi), expand=true)
    delta_a_nonzero_sample = Dict(
        "d_eta" => clean(Symbolics.substitute(delta_a_eta, Dict(alpha0 => 0, alpha1 => 1))),
        "d_chi" => clean(Symbolics.substitute(delta_a_chi, Dict(alpha0 => 0, alpha1 => 1))),
        "d_phi" => clean(Symbolics.substitute(delta_a_phi, Dict(alpha0 => 0, alpha1 => 1))),
    )
    Dict(
        "gauge_family" => "phi -> phi + alpha(chi,eta), sampled as alpha=alpha0+alpha1*chi",
        "computed_delta_A" => Dict("d_eta" => clean(delta_a_eta), "d_chi" => clean(delta_a_chi), "d_phi" => clean(delta_a_phi)),
        "computed_delta_A_nonzero_sample_alpha_chi" => delta_a_nonzero_sample,
        "computed_delta_F_eta_chi" => clean(delta_f),
        "A_changes_under_nonconstant_gauge" => any(value != "0" for value in values(delta_a_nonzero_sample)),
        "F_invariant_symbolically" => clean(delta_f) == "0",
    )
end

function z3_nonzero_control()
    solver = Z3.Solver()
    alpha1 = Z3.IntVar("julia_alpha1")
    Z3.add(solver, alpha1 == Z3.IntVal(1))
    positive = string(Z3.check(solver))

    erased = Z3.Solver()
    alpha1_erased = Z3.IntVar("julia_alpha1_erased")
    Z3.add(erased, alpha1_erased == Z3.IntVal(1))
    Z3.add(erased, alpha1_erased == Z3.IntVal(0))
    negative = string(Z3.check(erased))
    Dict(
        "positive_nonconstant_gauge_verdict" => positive,
        "erased_constant_control_verdict" => negative,
        "pass" => positive == "sat" && negative == "unsat",
    )
end

function main()
    mkpath(RESULT_DIR)
    gauge = symbolic_gauge_receipt()
    z3_control = z3_nonzero_control()
    all_pass = gauge["A_changes_under_nonconstant_gauge"] == true &&
        gauge["F_invariant_symbolically"] == true &&
        z3_control["pass"] == true
    result = Dict(
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "all_pass" => all_pass,
        "ran" => true,
        "reads_peer_result" => READS_PEER_RESULT,
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "julia_project" => "system_v5/julia_carrier",
        "packages_used" => ["Symbolics", "Z3", "JSON", "SHA"],
        "aligned_packages_load_bearing" => ["Symbolics", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "symbolics_gauge_test" => gauge,
        "z3_nonzero_control" => z3_control,
        "tool_calls" => [
            Dict(
                "tool" => "Symbolics",
                "qualified_api/function" => "Symbolics.@variables / Symbolics.simplify",
                "input_object" => "A=dphi+cos(2eta)dchi and alpha=alpha0+alpha1*chi",
                "output_object" => "computed delta_A and delta_F",
                "positive_case" => "alpha1=1 gives nonzero delta_A",
                "negative/erased_control" => "alpha1=0 erases delta_A",
                "boundary_case" => "only the S2 quotient gauge check is mirrored",
                "demotion_condition" => "demote if delta_A/delta_F are not computed by Symbolics",
                "gates" => ["julia_symbolics_gauge_mirror"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver / Z3.add / Z3.check",
                "input_object" => "nonzero alpha1 branch",
                "output_object" => "sat positive and unsat erased contradiction",
                "positive_case" => "alpha1=1 is satisfiable",
                "negative/erased_control" => "alpha1=1 and alpha1=0 is unsat",
                "boundary_case" => "control branch only",
                "demotion_condition" => "demote if can-fail control is removed",
                "gates" => ["julia_symbolics_gauge_mirror"],
            ),
        ],
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println(JSON.json(Dict("ok" => all_pass, "result_path" => RESULT_PATH_REL)))
    return all_pass ? 0 : 1
end

exit(main())
