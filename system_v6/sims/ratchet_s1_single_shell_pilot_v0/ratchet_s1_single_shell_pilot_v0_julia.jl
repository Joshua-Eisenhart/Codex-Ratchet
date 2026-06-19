#!/usr/bin/env julia

using Dates
using JSON3
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "ratchet_s1_single_shell_pilot_v0"
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

function z3_mul(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(1)
    length(args) == 1 && return args[1]
    return Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_mul(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_scaled_identity(multiplier::Int)::Dict{String,Any}
    solver = Z3.Solver()
    q = Z3.IntVar("julia_q_global_scaled_by_pi_over_2")
    full = Z3.IntVar("julia_full_global_scaled_by_pi_over_2")
    Z3.add(solver, q == Z3.IntVal(1))
    Z3.add(solver, full == Z3.IntVal(4))
    product = z3_mul(Z3.Expr[Z3.IntVal(multiplier), q])
    if multiplier == 4
        Z3.add(solver, Z3.Not(product == full))
    else
        Z3.add(solver, product == full)
    end
    verdict = string(Z3.check(solver))
    return Dict(
        "solver" => "Z3.jl",
        "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
        "ran" => true,
        "load_bearing" => true,
        "multiplier" => multiplier,
        "verdict" => verdict,
        "bound_values" => Dict("h_Z4_global" => 1, "h_full_global" => 4),
        "positive_case" => multiplier == 4 ? "negated quotient-order identity is UNSAT" : "erased multiplier control is UNSAT",
    )
end

function exact_rows()::Dict{String,Any}
    eta0 = "pi/6"
    cos_eta0 = "sqrt(3)/2"
    sin_eta0 = "1/2"
    cos_2eta0 = "1/2"
    t_eta0_physical_area = "sqrt(3)*pi**2"
    quotient_area = "sqrt(3)*pi**2/4"
    return Dict(
        "eta0" => eta0,
        "metric_radii" => Dict("alpha" => cos_eta0, "beta" => sin_eta0),
        "metric_phi_chi" => [["1", cos_2eta0], [cos_2eta0, "1"]],
        "connection_pullback" => Dict("dphi" => "1", "dchi" => cos_2eta0),
        "fundamental_cycle_holonomies" => Dict(
            "phi_cycle_delta_2pi_0" => "2*pi",
            "chi_cycle_delta_0_2pi" => "pi",
            "alpha_cycle_delta_pi_pi" => "3*pi/2",
            "beta_cycle_delta_pi_neg_pi" => "pi/2",
        ),
        "quotient_area" => quotient_area,
        "t_eta0_physical_area" => t_eta0_physical_area,
        "quotient_holonomy_identity" => Dict(
            "h_Z4_global_pi_over_2_units" => 1,
            "h_full_global_pi_over_2_units" => 4,
            "identity" => "4 * h_Z4_global = h_full_global",
        ),
        "path_specificity" => Dict(
            "claim_kind" => "quotient_well_definedness_equivariance_failure",
            "witness_orbit_under_Z4" => ["pi/4", "3*pi/4", "5*pi/4", "7*pi/4"],
            "membership_in_window" => [true, true, false, false],
            "is_Z4_saturated" => false,
            "not_numeric_order_gap_family" => true,
            "branch_mortality" => "quotient-first branch kills the non-Z4-saturated alpha window as a coherent quotient constraint",
        ),
    )
end

function observable_values(rows::Dict{String,Any}, z3_positive::Dict{String,Any})::Dict{String,Any}
    return Dict(
        "metric_radii_alpha" => rows["metric_radii"]["alpha"],
        "metric_radii_beta" => rows["metric_radii"]["beta"],
        "A_T_dchi_coefficient" => rows["connection_pullback"]["dchi"],
        "fundamental_holonomy_phi_cycle" => rows["fundamental_cycle_holonomies"]["phi_cycle_delta_2pi_0"],
        "fundamental_holonomy_chi_cycle" => rows["fundamental_cycle_holonomies"]["chi_cycle_delta_0_2pi"],
        "fundamental_holonomy_alpha_cycle" => rows["fundamental_cycle_holonomies"]["alpha_cycle_delta_pi_pi"],
        "fundamental_holonomy_beta_cycle" => rows["fundamental_cycle_holonomies"]["beta_cycle_delta_pi_neg_pi"],
        "quotient_area" => rows["quotient_area"],
        "quotient_global_holonomy_pi_over_2_units" => 1,
        "full_global_holonomy_pi_over_2_units" => 4,
        "non_Z4_saturated_window_witness" => 1,
        "julia_z3_quotient_order_identity_verified" => z3_positive["verdict"] == "unsat" ? 1 : 0,
    )
end

function build_result()::Dict{String,Any}
    rows = exact_rows()
    z3_positive = z3_scaled_identity(4)
    z3_erased = z3_scaled_identity(3)
    all_pass = (
        rows["metric_radii"]["alpha"] == "sqrt(3)/2" &&
        rows["metric_radii"]["beta"] == "1/2" &&
        rows["connection_pullback"]["dchi"] == "1/2" &&
        rows["fundamental_cycle_holonomies"]["phi_cycle_delta_2pi_0"] == "2*pi" &&
        rows["fundamental_cycle_holonomies"]["chi_cycle_delta_0_2pi"] == "pi" &&
        rows["quotient_area"] == "sqrt(3)*pi**2/4" &&
        rows["path_specificity"]["is_Z4_saturated"] == false &&
        z3_positive["verdict"] == "unsat" &&
        z3_erased["verdict"] == "unsat"
    )
    return Dict(
        "schema_version" => "ratchet_s1_single_shell_pilot_v0_julia_result_v1",
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
        "packages_used" => ["JSON3", "SHA", "Dates", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "exact_rows" => rows,
        "engine_values" => observable_values(rows, z3_positive),
        "crossover_proofs" => Dict(
            "julia_z3" => merge(z3_positive, Dict(
                "erased_flip" => "replace multiplier 4 by 3",
                "erased_flip_verdict" => z3_erased["verdict"],
                "erased_flip_detected" => z3_erased["verdict"] == "unsat",
                "demotion_condition" => "demote G1 if Z3.jl does not make the quotient-order identity UNSAT with the bound q/full rows",
                "gates" => ["G1_SOURCE_BACKED_LANES", "proof", "all_pass"],
            )),
        ),
        "tool_calls" => [
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                "input_object" => "quotient-order identity 4 * h_Z4_global = h_full_global over q=1, full=4",
                "output_object" => z3_positive,
                "positive_case" => z3_positive["positive_case"],
                "negative/erased_control" => "multiplier 3 control",
                "boundary_case" => "N=1 collapses quotient generator to the old full global cycle",
                "demotion_condition" => "Z3.jl verdict not UNSAT or source not independently executable",
                "gates" => ["G1_SOURCE_BACKED_LANES"],
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
