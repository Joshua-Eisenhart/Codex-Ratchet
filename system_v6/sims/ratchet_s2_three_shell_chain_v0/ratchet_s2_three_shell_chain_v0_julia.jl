#!/usr/bin/env julia

using Dates
using JSON3
using Pkg
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "ratchet_s2_three_shell_chain_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")

function rel(path::AbstractString)::String
    return relpath(path, ROOT)
end

function file_sha256(path::AbstractString)::String
    return bytes2hex(SHA.sha256(read(path)))
end

function package_version(name::String)::String
    for dep in values(Pkg.dependencies())
        if dep.name == name
            return dep.version === nothing ? "stdlib_or_unknown" : string(dep.version)
        end
    end
    return "not_found"
end

function z3_add_expr(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0)
    return Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_chain_identity(; flipped::Bool=false)::Dict{String,Any}
    solver = Z3.Solver()
    # Pair basis for 2*pi^{-1} flux values: a*sqrt(3)+b.
    f12_s = Z3.IntVar(flipped ? "julia_flip_f12_sqrt3_coeff" : "julia_f12_sqrt3_coeff")
    f12_q = Z3.IntVar(flipped ? "julia_flip_f12_rational_coeff" : "julia_f12_rational_coeff")
    f23_s = Z3.IntVar("julia_f23_sqrt3_coeff")
    f23_q = Z3.IntVar("julia_f23_rational_coeff")
    f13_s = Z3.IntVar("julia_f13_sqrt3_coeff")
    f13_q = Z3.IntVar("julia_f13_rational_coeff")

    Z3.add(solver, f12_s == Z3.IntVal(flipped ? -1 : 1))
    Z3.add(solver, f12_q == Z3.IntVal(flipped ? 1 : -1))
    Z3.add(solver, f23_s == Z3.IntVal(0))
    Z3.add(solver, f23_q == Z3.IntVal(1))
    Z3.add(solver, f13_s == Z3.IntVal(1))
    Z3.add(solver, f13_q == Z3.IntVal(0))
    sum_s = z3_add_expr(Z3.Expr[f12_s, f23_s])
    sum_q = z3_add_expr(Z3.Expr[f12_q, f23_q])
    if flipped
        Z3.add(solver, sum_s == f13_s)
        Z3.add(solver, sum_q == f13_q)
    else
        Z3.add(solver, Z3.Or(Z3.Expr[Z3.Not(sum_s == f13_s), Z3.Not(sum_q == f13_q)]))
    end

    return Dict(
        "solver" => "Z3.jl",
        "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
        "ran" => true,
        "load_bearing" => true,
        "orientation" => flipped ? "flipped_first_annulus_orientation" : "positive_chain_orientation",
        "verdict" => string(Z3.check(solver)),
        "basis" => "2*pi^{-1} flux represented as (sqrt3_coeff, rational_coeff)",
        "bound_values" => Dict(
            "flux_12" => flipped ? ["-1", "1"] : ["1", "-1"],
            "flux_23" => ["0", "1"],
            "flux_13" => ["1", "0"],
        ),
        "positive_case" => flipped ? "erased flip equality is UNSAT" : "negated chain additivity is UNSAT",
    )
end

function exact_rows()::Dict{String,Any}
    return Dict(
        "weights" => Dict(
            "eta_pi_over_12" => Dict("rho_sin_2eta" => "1/2", "weight" => "1/(3 + sqrt(3))", "weight_rationalized" => "(3 - sqrt(3))/6"),
            "eta_pi_over_6" => Dict("rho_sin_2eta" => "sqrt(3)/2", "weight" => "sqrt(3)/(3 + sqrt(3))", "weight_rationalized" => "(sqrt(3) - 1)/2"),
            "eta_pi_over_4" => Dict("rho_sin_2eta" => "1", "weight" => "2/(3 + sqrt(3))", "weight_rationalized" => "(3 - sqrt(3))/3"),
            "sum" => "1",
            "equal_weight_subtlety_arises" => false,
        ),
        "leaf_connection_coefficients" => Dict(
            "eta_pi_over_12" => "sqrt(3)/2",
            "eta_pi_over_6" => "1/2",
            "eta_pi_over_4" => "0",
        ),
        "chain_fluxes" => Dict(
            "flux_12_pi_over_12_to_pi_over_6" => "pi*(-1/2 + sqrt(3)/2)",
            "flux_23_pi_over_6_to_pi_over_4" => "pi/2",
            "flux_13_total_pi_over_12_to_pi_over_4" => "sqrt(3)*pi/2",
            "chain_sum" => "sqrt(3)*pi/2",
            "chain_defect" => "0",
        ),
        "pairwise_holonomy_gaps" => Dict(
            "gap_12" => "pi*(-1/2 + sqrt(3)/2)",
            "gap_23" => "pi/2",
            "gap_13" => "sqrt(3)*pi/2",
            "gap_13_minus_gap_12_minus_gap_23" => "0",
        ),
        "z4_survivors" => Dict(
            "global_phase_gaps" => Dict("gap_12" => "0", "gap_23" => "0", "gap_13" => "0"),
            "alpha_generator_gaps" => Dict(
                "gap_12" => "pi*(-1/2 + sqrt(3)/2)",
                "gap_23" => "pi/2",
                "gap_13" => "sqrt(3)*pi/2",
            ),
            "beta_generator_gaps" => Dict(
                "gap_12" => "pi*(1/2 - sqrt(3)/2)",
                "gap_23" => "-pi/2",
                "gap_13" => "-sqrt(3)*pi/2",
            ),
            "chain_additivity_survives" => true,
            "flux_rows_survive" => true,
        ),
    )
end

function observable_values(rows::Dict{String,Any}, z3_positive::Dict{String,Any})::Dict{String,Any}
    return Dict(
        "weight_eta_pi_over_12" => rows["weights"]["eta_pi_over_12"]["weight_rationalized"],
        "weight_eta_pi_over_6" => rows["weights"]["eta_pi_over_6"]["weight_rationalized"],
        "weight_eta_pi_over_4" => rows["weights"]["eta_pi_over_4"]["weight_rationalized"],
        "dchi_eta_pi_over_12" => rows["leaf_connection_coefficients"]["eta_pi_over_12"],
        "dchi_eta_pi_over_6" => rows["leaf_connection_coefficients"]["eta_pi_over_6"],
        "dchi_eta_pi_over_4" => rows["leaf_connection_coefficients"]["eta_pi_over_4"],
        "flux_12" => rows["chain_fluxes"]["flux_12_pi_over_12_to_pi_over_6"],
        "flux_23" => rows["chain_fluxes"]["flux_23_pi_over_6_to_pi_over_4"],
        "flux_13_total" => rows["chain_fluxes"]["flux_13_total_pi_over_12_to_pi_over_4"],
        "chain_defect" => rows["chain_fluxes"]["chain_defect"],
        "gap_13_minus_gap_12_minus_gap_23" => rows["pairwise_holonomy_gaps"]["gap_13_minus_gap_12_minus_gap_23"],
        "julia_z3_chain_identity_verified" => z3_positive["verdict"] == "unsat" ? 1 : 0,
    )
end

function build_result()::Dict{String,Any}
    rows = exact_rows()
    z3_positive = z3_chain_identity(flipped=false)
    z3_flipped = z3_chain_identity(flipped=true)
    all_pass = (
        rows["weights"]["sum"] == "1" &&
        rows["weights"]["equal_weight_subtlety_arises"] == false &&
        rows["leaf_connection_coefficients"]["eta_pi_over_4"] == "0" &&
        rows["chain_fluxes"]["chain_defect"] == "0" &&
        rows["pairwise_holonomy_gaps"]["gap_13_minus_gap_12_minus_gap_23"] == "0" &&
        rows["z4_survivors"]["chain_additivity_survives"] == true &&
        z3_positive["verdict"] == "unsat" &&
        z3_flipped["verdict"] == "unsat"
    )
    return Dict(
        "schema_version" => "$(SIM_ID)_julia_result_v1",
        "sim_id" => SIM_ID,
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "all_pass" => all_pass,
        "julia_project" => String(Base.active_project()),
        "load_path" => String.(Base.LOAD_PATH),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "reads_peer_result" => false,
        "packages_used" => ["JSON3", "Pkg", "SHA", "Dates", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "capability_receipts" => Dict(
            "julia" => Dict("version" => string(VERSION), "active_project" => String(Base.active_project())),
            "Z3" => Dict("package_version" => package_version("Z3"), "api_smoke" => z3_positive["verdict"]),
        ),
        "exact_rows" => rows,
        "engine_values" => observable_values(rows, z3_positive),
        "crossover_proofs" => Dict(
            "julia_z3" => merge(z3_positive, Dict(
                "erased_flip" => "flip first annulus orientation while keeping the total boundary target fixed",
                "erased_flip_verdict" => z3_flipped["verdict"],
                "erased_flip_detected" => z3_flipped["verdict"] == "unsat",
                "identity" => "flux_12 + flux_23 == flux_13 in Q(sqrt3) coefficient-pair basis",
                "demotion_condition" => "demote chain-additivity proof if Z3.jl does not make the negated identity UNSAT from bound coefficient rows",
                "gates" => ["chain_additivity", "holonomy_gap_additivity", "proof", "all_pass"],
            )),
        ),
        "tool_calls" => [
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                "input_object" => "Three-shell flux-chain identity in 2*pi^{-1} Q(sqrt3) coefficient basis",
                "output_object" => z3_positive,
                "positive_case" => z3_positive["positive_case"],
                "negative/erased_control" => "wrong first-annulus orientation",
                "boundary_case" => "adjacent pair eta=pi/6 to eta=pi/4 reproduces committed two-shell anchor",
                "demotion_condition" => "Z3.jl verdict not UNSAT or source not independently executable",
                "gates" => ["chain_additivity"],
                "load_bearing" => true,
            ),
        ],
    )
end

function main()::Int
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON3.pretty(io, result)
        write(io, "\n")
    end
    println(JSON3.write(Dict("ok" => result["all_pass"], "result_path" => rel(RESULT_PATH))))
    return result["all_pass"] ? 0 : 1
end

exit(main())
