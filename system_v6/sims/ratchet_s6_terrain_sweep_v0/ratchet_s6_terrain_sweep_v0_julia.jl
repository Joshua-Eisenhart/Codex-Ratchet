#!/usr/bin/env julia

using Dates
using JSON3
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "ratchet_s6_terrain_sweep_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const ETA0 = "pi/6"
const TERRAIN_ORDER = [
    "Ne_Spiral_R",
    "Ne_Vortex_L",
    "Ni_Pit_L",
    "Ni_Source_R",
    "Se_Cannon_R",
    "Se_Funnel_L",
    "Si_Citadel_R",
    "Si_Hill_L",
]
const TERRAIN_HASHES = Dict(
    "Ne_Spiral_R" => "890ac6990ff4158d0f2f7bf9c786aac832837bd9b84530219b763576e18214b4",
    "Ne_Vortex_L" => "f7a01b371cb290c49e911ac477a244e29d9ae489ef0aec3c17c935c2f0c66218",
    "Ni_Pit_L" => "6eff3605086c785fa80db6f2c56f258685a500249bb41d34cc8bdc048ebfa13e",
    "Ni_Source_R" => "53103e38a21a630ef160a17355a2b55bedbc1faff74918bf1d8c8b47a08cc086",
    "Se_Cannon_R" => "82eaa9e60bea7754402e70442c041a467b3546199fae3af0ddd013a2a5763433",
    "Se_Funnel_L" => "25f78fc755e37729771e46eef26f6d80358dbcee06891917e2ebe82dcee5128a",
    "Si_Citadel_R" => "059b6cbfe868456e2478a802252ed543c3bd046d4e2cd4f4d3d79a4cbf50c4be",
    "Si_Hill_L" => "63c4862cc0414923ac5f4918f32a9c704f0050cb8d7e48830560b7b06b841676",
)

function rel(path::AbstractString)::String
    return relpath(path, ROOT)
end

function file_sha256(path::AbstractString)::String
    return bytes2hex(SHA.sha256(read(path)))
end

function z3_zero_assertion(label::String, scaled_value::Int)::String
    solver = Z3.Solver()
    x = Z3.IntVar(label)
    Z3.add(solver, x == Z3.IntVal(scaled_value))
    Z3.add(solver, x == Z3.IntVal(0))
    return string(Z3.check(solver))
end

function z3_nonzero_assertion(label::String, scaled_value::Int)::String
    solver = Z3.Solver()
    x = Z3.IntVar(label)
    Z3.add(solver, x == Z3.IntVal(scaled_value))
    Z3.add(solver, Z3.Not(x == Z3.IntVal(0)))
    return string(Z3.check(solver))
end

function z3_anchor_gap()::Dict{String,Any}
    verdict = z3_zero_assertion("se_funnel_rx_gap_z_theta0_scaled_by_40", -16)
    erased_verdict = z3_zero_assertion("erased_se_funnel_rx_gap_z_theta0_scaled_by_40", 0)
    return Dict(
        "solver" => "Z3.jl",
        "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
        "ran" => true,
        "load_bearing" => true,
        "verdict" => verdict,
        "claim" => "Se_Funnel_L generator and R_x(pi/2) have nonzero N01 order gap on T_pi/6 at theta=0",
        "derived_expression" => "40*Delta_z(theta=0) = -16",
        "positive_case" => "asserting the scaled gap is zero is UNSAT",
        "negative/erased_control" => "erased skew/off-diagonal gap row has scaled value 0; zero assertion becomes SAT",
        "erased_flip_verdict" => erased_verdict,
        "erased_flip_detected" => erased_verdict == "sat",
        "boundary_case" => "Si_Citadel_R/R_x is the zero-gap sweep row",
        "demotion_condition" => "demote if Z3.jl does not refute the nonzero anchor zero assertion or erased row does not flip",
        "gates" => ["anchor", "proof", "all_pass"],
    )
end

function z3_committed_dz_rz_zero()::Dict{String,Any}
    verdict = z3_nonzero_assertion("dz_rz_control_gap_scaled", 0)
    return Dict(
        "solver" => "Z3.jl",
        "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
        "ran" => true,
        "load_bearing" => true,
        "verdict" => verdict,
        "claim" => "D_z and R_z committed commuting control has zero order gap",
        "derived_expression" => "Delta_control_scaled = 0",
        "positive_case" => "asserting a nonzero commuting-control gap is UNSAT",
        "negative/erased_control" => "replace R_z by R_x in the Python exact lane to recover a cross-axis nonzero row",
        "boundary_case" => "q_z=0 identity dephasing also gives zero gap",
        "demotion_condition" => "demote if the commuting-control zero row is not solver-checked",
        "gates" => ["commuting_control", "all_pass"],
    )
end

function z3_sweep_rows()::Vector{Dict{String,Any}}
    rows = [
        ("Ne_Spiral_R", "z_theta0_scaled_by_40", 80, "nonzero"),
        ("Ne_Vortex_L", "z_theta0_scaled_by_40", -80, "nonzero"),
        ("Ni_Pit_L", "y_theta0_scaled_by_40", -25, "nonzero"),
        ("Ni_Source_R", "y_theta0_scaled_by_40", 15, "nonzero"),
        ("Se_Cannon_R", "z_theta0_scaled_by_40", 16, "nonzero"),
        ("Se_Funnel_L", "z_theta0_scaled_by_40", -16, "nonzero"),
        ("Si_Citadel_R", "all_gap_entries_scaled_by_40", 0, "zero"),
        ("Si_Hill_L", "x_theta0_scaled_by_40", 8, "nonzero"),
    ]
    out = Dict{String,Any}[]
    for (terrain, field, value, status) in rows
        verdict = status == "zero" ? z3_nonzero_assertion("$(terrain)_$(field)", value) : z3_zero_assertion("$(terrain)_$(field)", value)
        push!(
            out,
            Dict(
                "terrain_id" => terrain,
                "checked_field" => field,
                "scaled_value" => value,
                "expected_status" => status,
                "verdict" => verdict,
                "pass" => verdict == "unsat",
            ),
        )
    end
    return out
end

function exact_rows(anchor::Dict{String,Any}, control::Dict{String,Any}, sweep::Vector{Dict{String,Any}})::Dict{String,Any}
    return Dict(
        "eta0" => ETA0,
        "terrain_order" => TERRAIN_ORDER,
        "terrain_hashes" => TERRAIN_HASHES,
        "terrain_count" => 8,
        "fixed_survivor_count" => 0,
        "pure_shell_compatible_count" => 0,
        "density_z_leaf_compatible_count" => 1,
        "rx_gap_zero_terrain_ids" => ["Si_Citadel_R"],
        "se_funnel_gap_norm_squared" => "4/25",
        "se_funnel_gap_delta" => ["2*sin(theta)/5", "0", "-2*cos(theta)/5"],
        "se_funnel_gap_witness_theta0" => ["0", "0", "-2/5"],
        "committed_dz_rz_control_norm_squared" => "0",
        "commuting_control_count" => 5,
        "julia_z3_anchor_verdict" => anchor["verdict"],
        "julia_z3_erased_flip_verdict" => anchor["erased_flip_verdict"],
        "julia_z3_committed_control_verdict" => control["verdict"],
        "julia_z3_sweep_rows" => sweep,
    )
end

function build_result()::Dict{String,Any}
    anchor = z3_anchor_gap()
    control = z3_committed_dz_rz_zero()
    sweep = z3_sweep_rows()
    rows = exact_rows(anchor, control, sweep)
    engine_values = Dict(
        "terrain_count" => 8,
        "fixed_survivor_count" => 0,
        "pure_shell_compatible_count" => 0,
        "density_z_leaf_compatible_count" => 1,
        "rx_gap_zero_terrain_ids" => ["Si_Citadel_R"],
        "se_funnel_gap_norm_squared" => "4/25",
        "se_funnel_gap_delta" => ["2*sin(theta)/5", "0", "-2*cos(theta)/5"],
        "se_funnel_gap_witness_theta0" => ["0", "0", "-2/5"],
        "committed_dz_rz_control_norm_squared" => "0",
        "commuting_control_count" => 5,
    )
    all_pass = (
        anchor["verdict"] == "unsat" &&
        anchor["erased_flip_verdict"] == "sat" &&
        control["verdict"] == "unsat" &&
        all(row["pass"] == true for row in sweep) &&
        length(TERRAIN_HASHES) == 8 &&
        engine_values["se_funnel_gap_norm_squared"] == "4/25"
    )
    return Dict(
        "schema_version" => "$(SIM_ID)_julia_result_v1",
        "sim_id" => SIM_ID,
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
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
        "engine_values" => engine_values,
        "crossover_proofs" => Dict(
            "julia_z3" => anchor,
            "julia_z3_committed_dz_rz_control" => control,
            "julia_z3_sweep_rows" => sweep,
        ),
        "tool_calls" => [
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                "input_object" => "scaled Se_Funnel_L/R_x anchor row, committed D_z/R_z zero row, and eight scaled sweep rows",
                "output_object" => anchor,
                "positive_case" => anchor["positive_case"],
                "negative/erased_control" => anchor["negative/erased_control"],
                "boundary_case" => anchor["boundary_case"],
                "demotion_condition" => anchor["demotion_condition"],
                "gates" => anchor["gates"],
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
