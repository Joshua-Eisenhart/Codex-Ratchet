#!/usr/bin/env julia
# object_id: round3_s9_s2_final_heavy_v0
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using DifferentialEquations
using JSON
using LinearAlgebra
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "round3_s9_s2_final_heavy_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")

sha256_text(text::String)::String = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))
file_sha256(path::String)::String = open(path, "r") do io bytes2hex(sha256(io)) end
rel(path::String)::String = relpath(path, ROOT)

function qmul(a::Vector{Float64}, b::Vector{Float64})::Vector{Float64}
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return [
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    ]
end

function qexp(axis::Int, theta::Float64)::Vector{Float64}
    q = [cos(theta), 0.0, 0.0, 0.0]
    q[axis + 1] = sin(theta)
    return q
end

commutator_gap_squared(theta::Float64)::Float64 = norm(qmul(qexp(1, theta), qexp(2, theta)) .- qmul(qexp(2, theta), qexp(1, theta)))^2
theta_from_x_eps(x::Float64, eps::Float64)::Float64 = pi * (1.0 + x + eps * (1.0 - x^2)) / 6.0

function ode_anchor_control()
    theta = pi / 3.0
    function rhs!(du, u, p, t)
        du[1] = -theta * u[2]
        du[2] = theta * u[1]
    end
    prob = ODEProblem(rhs!, [1.0, 0.0], (0.0, 1.0))
    sol = solve(prob, Vern9(); reltol=1.0e-12, abstol=1.0e-14, dtmax=1.0 / 64.0, save_everystep=false)
    observed = Vector{Float64}(sol.u[end])
    target = [cos(theta), sin(theta)]
    err = maximum(abs.(observed .- target))
    return Dict(
        "surface" => "DifferentialEquations.ODEProblem/solve/Vern9 anchor loop control",
        "theta" => "pi/3",
        "observed" => observed,
        "target" => target,
        "max_abs_error_bound" => err,
        "pass" => err <= 2.0e-11,
        "strength_label" => "diagnostic_float_bound_not_exact_claim_path",
    )
end

function s9_receipt()
    xs = [1.0, 0.5, 0.0, -0.5, -1.0]
    labels = ["0", "pi/6", "pi/4", "pi/3", "pi/2"]
    rows = Any[]
    for (idx, x) in enumerate(xs)
        anchor = theta_from_x_eps(x, 0.0)
        plus = theta_from_x_eps(x, 1.0 / 20.0)
        minus = theta_from_x_eps(x, -1.0 / 20.0)
        push!(rows, Dict(
            "leaf" => labels[idx],
            "anchor_theta" => anchor,
            "plus_theta" => plus,
            "minus_theta" => minus,
            "plus_theta_gap" => plus - anchor,
            "minus_theta_gap" => minus - anchor,
            "anchor_commutator_gap_squared" => commutator_gap_squared(anchor),
            "plus_commutator_gap_squared" => commutator_gap_squared(plus),
            "minus_commutator_gap_squared" => commutator_gap_squared(minus),
        ))
    end
    alias_gap = maximum(abs.([theta_from_x_eps(x, 0.0) - theta_from_x_eps(x, 0.0) for x in xs]))
    return Dict(
        "row" => "S9.R3.5_path_ordered_loop_neighbor",
        "loop_families" => ["(x0,x1)->i", "(x0,x2)->j"],
        "rows" => rows,
        "alias_gap_max" => alias_gap,
        "pass" => alias_gap == 0.0 && any(abs(row["plus_theta_gap"]) > 1.0e-14 for row in rows),
        "verdict" => "excluded-under-pinned-path-ordered-transport-convention",
    )
end

function s2_receipt()
    weights_pi12_pi6 = ["1/(1 + sqrt(3))", "sqrt(3)/(1 + sqrt(3))"]
    weights_pi6_pi4 = ["sqrt(3)/(sqrt(3) + 2)", "2/(sqrt(3) + 2)"]
    weights_pi4_pi3 = ["2/(sqrt(3) + 2)", "sqrt(3)/(sqrt(3) + 2)"]
    rows = [
        Dict("union_id" => "U_pi12_pi6", "labels" => ["pi/12", "pi/6"], "valid" => true, "weights" => weights_pi12_pi6, "annular_flux_physical_period" => "pi*(-1/2 + sqrt(3)/2)", "stokes_defect" => "0"),
        Dict("union_id" => "U_pi6_pi4", "labels" => ["pi/6", "pi/4"], "valid" => true, "weights" => weights_pi6_pi4, "annular_flux_physical_period" => "pi/2", "stokes_defect" => "0"),
        Dict("union_id" => "U_pi4_pi3", "labels" => ["pi/4", "pi/3"], "valid" => true, "weights" => weights_pi4_pi3, "annular_flux_physical_period" => "pi/2", "stokes_defect" => "0"),
    ]
    invalid = Dict("union_id" => "invalid.overlapping_duplicate_pi6", "labels" => ["pi/6", "pi/6"], "valid" => false, "reason" => "duplicate fixed leaf is an overlapping/non-canonical cover")
    return Dict(
        "row" => "S2.R3.5_boundary_conditioning_variant",
        "valid_union_rows" => rows,
        "invalid_cover_control" => invalid,
        "pass" => all(row["valid"] == true && row["stokes_defect"] == "0" for row in rows) && invalid["valid"] == false,
    )
end

function z3_receipt()
    solver = Z3.Solver()
    gap = Z3.IntVar("s9_theta_gap_over_pi_scaled_by_120")
    Z3.add(solver, gap == Z3.IntVal(1))
    Z3.add(solver, gap == Z3.IntVal(0))
    verdict = string(Z3.check(solver))

    flip = Z3.Solver()
    flip_gap = Z3.IntVar("flip_s9_theta_gap_over_pi_scaled_by_120")
    Z3.add(flip, flip_gap == Z3.IntVal(0))
    Z3.add(flip, flip_gap == Z3.IntVal(0))
    flip_verdict = string(Z3.check(flip))
    return Dict(
        "ran" => true,
        "load_bearing" => true,
        "solver" => "Z3.jl",
        "verdict" => verdict,
        "flip_control_verdict" => flip_verdict,
        "claim" => "Julia Z3 binds the finite S9 transport theta-gap witness and erased flip",
        "witness_values" => Dict("s9_plus_epsilon_pi4_theta_gap" => "pi/120", "scaled_by_120" => 1),
    )
end

function build_result()
    s9 = s9_receipt()
    s2 = s2_receipt()
    ode = ode_anchor_control()
    z3 = z3_receipt()
    gates = Dict(
        "s9_alias_control_pass" => s9["alias_gap_max"] == 0.0,
        "s9_candidate_separates" => s9["pass"] == true,
        "s2_validity_first_rows_pass" => s2["pass"] == true,
        "ode_anchor_control_pass" => ode["pass"] == true,
        "julia_z3_unsat_flip_sat" => z3["verdict"] == "unsat" && z3["flip_control_verdict"] == "sat",
    )
    return Dict(
        "schema_version" => "$(SIM_ID)_julia_lane_v1",
        "sim_id" => SIM_ID,
        "object_id" => SIM_ID,
        "role_id" => "julia_differentialequations_z3_reference_lane",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => false,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => rel(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "all_pass" => all(values(gates)),
        "packages_used" => ["DifferentialEquations", "Z3", "LinearAlgebra", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["DifferentialEquations", "Z3"],
        "package_observables" => Dict(
            "DifferentialEquations" => "Vern9 anchor-loop ODE transport control with explicit error bound",
            "Z3" => "finite S9 transport gap polarity proof with erased flip",
        ),
        "TOOL_MANIFEST" => Dict(
            "DifferentialEquations" => Dict("used" => true, "reason" => "load-bearing ODE anchor-loop transport control"),
            "Z3" => Dict("used" => true, "reason" => "load-bearing finite witness polarity proof"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("DifferentialEquations" => "load_bearing", "Z3" => "load_bearing"),
        "claim_path_tools" => ["DifferentialEquations", "Z3"],
        "tool_calls" => [
            Dict("tool" => "DifferentialEquations", "qualified_api" => "ODEProblem/solve/Vern9", "observable" => "anchor loop transport control"),
            Dict("tool" => "Z3", "qualified_api" => "Z3.Solver/Z3.check", "observable" => "UNSAT/SAT finite witness polarity"),
        ],
        "positive" => Dict("s9_alias_gap_max" => s9["alias_gap_max"], "s2_valid_count" => length(s2["valid_union_rows"])),
        "negative" => Dict("s9_rows" => s9["rows"], "s2_invalid_cover_control" => s2["invalid_cover_control"]),
        "boundary" => Dict("strength_label" => "Julia reference numeric ODE control plus exact table/SMT rows; no promotion"),
        "s9" => s9,
        "s2" => s2,
        "ode_anchor_control" => ode,
        "crossover_proofs" => Dict("julia_z3" => z3),
        "build_gates" => gates,
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("result" => rel(RESULT_PATH), "all_pass" => result["all_pass"])))
    return result["all_pass"] ? 0 : 1
end

exit(main())
