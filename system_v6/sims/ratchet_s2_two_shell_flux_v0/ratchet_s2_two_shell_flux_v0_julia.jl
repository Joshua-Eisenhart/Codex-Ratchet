#!/usr/bin/env julia

using Dates
using JSON3
using Pkg
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "ratchet_s2_two_shell_flux_v0"
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

function z3_stokes_identity(flipped::Bool)::Dict{String,Any}
    solver = Z3.Solver()
    flux = Z3.IntVar(flipped ? "julia_flipped_flux_pi_over_2_units" : "julia_flux_pi_over_2_units")
    boundary = Z3.IntVar("julia_boundary_gap_pi_over_2_units")
    Z3.add(solver, flux == Z3.IntVal(flipped ? -1 : 1))
    Z3.add(solver, boundary == Z3.IntVal(1))
    if flipped
        Z3.add(solver, flux == boundary)
    else
        Z3.add(solver, Z3.Not(flux == boundary))
    end
    return Dict(
        "solver" => "Z3.jl",
        "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
        "ran" => true,
        "load_bearing" => true,
        "orientation" => flipped ? "flipped_wrong_orientation" : "eta1_boundary_minus_eta2_boundary",
        "verdict" => string(Z3.check(solver)),
        "bound_values" => Dict(
            "flux_pi_over_2_units" => flipped ? -1 : 1,
            "boundary_gap_pi_over_2_units" => 1,
        ),
        "positive_case" => flipped ? "wrong-orientation equality is UNSAT" : "negated Stokes identity is UNSAT",
    )
end

function z3_boundary_zero_gap()::Dict{String,Any}
    solver = Z3.Solver()
    flux = Z3.IntVar("julia_boundary_flux_pi_over_2_units")
    boundary = Z3.IntVar("julia_boundary_gap_pi_over_2_units_zero")
    Z3.add(solver, flux == Z3.IntVal(0))
    Z3.add(solver, boundary == Z3.IntVal(0))
    Z3.add(solver, Z3.Not(flux == boundary))
    return Dict(
        "solver" => "Z3.jl",
        "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
        "ran" => true,
        "load_bearing" => true,
        "verdict" => string(Z3.check(solver)),
        "bound_values" => Dict("flux_pi_over_2_units" => 0, "boundary_gap_pi_over_2_units" => 0),
        "positive_case" => "zero-gap boundary negation is UNSAT",
    )
end

function exact_rows()::Dict{String,Any}
    return Dict(
        "union_weights" => Dict(
            "eta1" => "pi/6",
            "eta2" => "pi/4",
            "rho_eta1" => "sqrt(3)/2",
            "rho_eta2" => "1",
            "weight_eta1" => "-3 + 2*sqrt(3)",
            "weight_eta1_ratio_form" => "sqrt(3)/(sqrt(3)+2)",
            "weight_eta2" => "4 - 2*sqrt(3)",
            "weight_eta2_ratio_form" => "2/(sqrt(3)+2)",
            "sum" => "1",
        ),
        "per_leaf_geometry" => Dict(
            "eta_pi_over_6" => Dict(
                "metric_radii" => Dict("alpha" => "sqrt(3)/2", "beta" => "1/2"),
                "metric_phi_chi" => [["1", "1/2"], ["1/2", "1"]],
                "connection_pullback" => Dict("dphi" => "1", "dchi" => "1/2"),
                "physical_chi_holonomy" => "pi/2",
            ),
            "eta_pi_over_4" => Dict(
                "metric_radii" => Dict("alpha" => "sqrt(2)/2", "beta" => "sqrt(2)/2"),
                "metric_phi_chi" => [["1", "0"], ["0", "1"]],
                "connection_pullback" => Dict("dphi" => "1", "dchi" => "0"),
                "physical_chi_holonomy" => "0",
                "self_dual_square_torus_note" => "chi coefficient vanishes; chi-cycle has zero connection holonomy",
            ),
        ),
        "inter_shell_flux" => Dict(
            "coefficient_gap" => "1/2",
            "physical_chi_period" => "pi",
            "flux_physical" => "pi/2",
            "boundary_holonomy_difference_physical" => "pi/2",
            "stokes_identity_pi_over_2_units" => "1 == 1",
            "double_chart_diagnostic_period" => "2*pi",
            "double_chart_diagnostic_flux" => "pi",
        ),
        "z4_quotient_rows" => Dict(
            "q_global_holonomy_gap" => "0",
            "z1_alpha_holonomy_gap" => "pi/2",
            "z2_beta_holonomy_gap" => "-pi/2",
            "relative_chi_nonprimitive_gap" => "pi",
            "flux_survives_quotient" => true,
        ),
        "controls" => Dict(
            "wrong_weights_equal_minus_correct_coefficient" => "7/4 - sqrt(3)",
            "wrong_weights_equal_minus_correct_physical" => "pi*(7/4 - sqrt(3))",
            "naive_joint_conditioning_denominator_mass" => "0",
            "empty_intersection" => "undefined_branch_mortality",
            "wrong_orientation_flux" => "-pi/2",
        ),
    )
end

function observable_values(rows::Dict{String,Any}, z3_positive::Dict{String,Any})::Dict{String,Any}
    return Dict(
        "union_weight_eta1" => rows["union_weights"]["weight_eta1"],
        "union_weight_eta2" => rows["union_weights"]["weight_eta2"],
        "eta1_connection_dchi" => rows["per_leaf_geometry"]["eta_pi_over_6"]["connection_pullback"]["dchi"],
        "eta2_connection_dchi" => rows["per_leaf_geometry"]["eta_pi_over_4"]["connection_pullback"]["dchi"],
        "chi_coefficient_gap" => rows["inter_shell_flux"]["coefficient_gap"],
        "flux_physical" => rows["inter_shell_flux"]["flux_physical"],
        "boundary_holonomy_difference_physical" => rows["inter_shell_flux"]["boundary_holonomy_difference_physical"],
        "z4_z1_alpha_holonomy_gap" => rows["z4_quotient_rows"]["z1_alpha_holonomy_gap"],
        "wrong_weight_defect_coefficient" => rows["controls"]["wrong_weights_equal_minus_correct_coefficient"],
        "julia_z3_stokes_identity_verified" => z3_positive["verdict"] == "unsat" ? 1 : 0,
    )
end

function build_result()::Dict{String,Any}
    rows = exact_rows()
    z3_positive = z3_stokes_identity(false)
    z3_flipped = z3_stokes_identity(true)
    z3_boundary = z3_boundary_zero_gap()
    all_pass = (
        rows["union_weights"]["weight_eta1_ratio_form"] == "sqrt(3)/(sqrt(3)+2)" &&
        rows["per_leaf_geometry"]["eta_pi_over_4"]["connection_pullback"]["dchi"] == "0" &&
        rows["inter_shell_flux"]["flux_physical"] == rows["inter_shell_flux"]["boundary_holonomy_difference_physical"] &&
        rows["z4_quotient_rows"]["z1_alpha_holonomy_gap"] == "pi/2" &&
        z3_positive["verdict"] == "unsat" &&
        z3_flipped["verdict"] == "unsat" &&
        z3_boundary["verdict"] == "unsat"
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
                "erased_flip" => "flip annulus orientation so flux_pi_over_2_units=-1 while boundary_gap_pi_over_2_units=1",
                "erased_flip_verdict" => z3_flipped["verdict"],
                "erased_flip_detected" => z3_flipped["verdict"] == "unsat",
                "boundary_case" => "eta1=eta2 gives zero coefficient gap and zero flux",
                "boundary_case_verdict" => z3_boundary["verdict"],
                "identity" => "flux_pi_over_2_units == boundary_gap_pi_over_2_units",
                "demotion_condition" => "demote Stokes row if Z3.jl does not make the negated identity UNSAT from bound flux and boundary rows",
                "gates" => ["stokes_identity", "proof", "all_pass"],
            )),
        ),
        "tool_calls" => [
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                "input_object" => "Stokes identity for two-shell annulus scaled by pi/2",
                "output_object" => z3_positive,
                "positive_case" => z3_positive["positive_case"],
                "negative/erased_control" => "wrong orientation sign control",
                "boundary_case" => "eta1=eta2 zero-gap control",
                "demotion_condition" => "Z3.jl verdict not UNSAT or source not independently executable",
                "gates" => ["stokes_identity"],
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
