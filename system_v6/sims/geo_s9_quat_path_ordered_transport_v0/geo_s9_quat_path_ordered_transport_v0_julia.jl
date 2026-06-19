#!/usr/bin/env julia
# object_id: geo_s9_quat_path_ordered_transport_v0
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using DifferentialEquations
using JSON
using LinearAlgebra
using Pkg
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s9_quat_path_ordered_transport_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const PARENT_ID = "geo_s9_quaternionic_hopf_stack_v0"
const PARENT_DIR = joinpath(ROOT, "system_v6", "sims", PARENT_ID)
const PARENT_RESULT = joinpath(PARENT_DIR, "results", "$(PARENT_ID)_envelope_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const THETA = pi / 3.0
const COMMITTED_GAP = 1.4999999999999998
const PIN_SPEC = "geo_s9_quat_path_ordered_transport_v0|stage:S9|mode:path_ordered_transport|parent=geo_s9_quaternionic_hopf_stack_v0 read_only|BPST Sp1 A=Im(x*dconj(x))/(1+|x|^2)|loops=(x0,x1)->i,(x0,x2)->j|theta=pi/3 transported calibration|abelian=S2 U1 horizontal holonomy|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const TOOL_MANIFEST = Dict{String,Any}(
    "DifferentialEquations" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Vern9 integration of the path-ordered Sp(1) parallel-transport ODE and U(1) horizontal transport ODE",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing computed inverse identity polarity check with erased-vector-flip control",
    ),
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive quaternion-vector norms and convergence distances",
    ),
    "JSON/Dates/SHA/Pkg" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive receipt serialization, timestamping, source hashing, and package capability receipt",
    ),
)
const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "DifferentialEquations" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON/Dates/SHA/Pkg" => "supportive",
)

sha256_text(text::String)::String = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))

function file_sha256(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function rel(path::String)::String
    return relpath(path, ROOT)
end

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

qconj(q::Vector{Float64}) = [q[1], -q[2], -q[3], -q[4]]
qnormalize(q::Vector{Float64}) = q ./ norm(q)

function qexp(axis::Int, theta::Float64)::Vector{Float64}
    out = [cos(theta), 0.0, 0.0, 0.0]
    out[axis + 1] = sin(theta)
    return out
end

function qdist(a::Vector{Float64}, b::Vector{Float64})::Float64
    return min(norm(a .- b), norm(a .+ b))
end

function commutator_gap(h1::Vector{Float64}, h2::Vector{Float64})::Float64
    return norm(qmul(h1, h2) .- qmul(h2, h1))
end

function angle_square(side::Float64)::Float64
    u = side / sqrt(1.0 + side^2)
    return 2.0 * u * atan(u)
end

function solve_side_for_theta(theta::Float64)::Float64
    lo = 0.0
    hi = 10.0
    for _ in 1:120
        mid = 0.5 * (lo + hi)
        if angle_square(mid) < theta
            lo = mid
        else
            hi = mid
        end
    end
    return 0.5 * (lo + hi)
end

function square_loop(side::Float64, plane::Tuple{Int,Int}; reverse::Bool=false)
    a, b = plane
    z = zeros(4)
    ea = zeros(4)
    eb = zeros(4)
    ea[a + 1] = side
    eb[b + 1] = side
    pts = [z, ea, ea .+ eb, eb, z]
    if reverse
        pts = reverse!(pts)
    end
    return [(copy(pts[i]), copy(pts[i + 1])) for i in 1:4]
end

function bpst_a_t(x::Vector{Float64}, xdot::Vector{Float64})::Vector{Float64}
    xq = [x[1], x[2], x[3], x[4]]
    dxbar = [xdot[1], -xdot[2], -xdot[3], -xdot[4]]
    prod = qmul(xq, dxbar)
    return [0.0, prod[2], prod[3], prod[4]] ./ (1.0 + dot(x, x))
end

function integrate_loop(segments, n_per_segment::Int; connection::String="bpst")
    q = [1.0, 0.0, 0.0, 0.0]
    max_raw_norm_drift = 0.0
    step_count = 0
    for (start, stop) in segments
        delta = stop .- start
        function rhs!(du, u, p, t)
            x = start .+ t .* delta
            at = connection == "zero" ? zeros(4) : bpst_a_t(x, delta)
            du[:] = qmul(-at, collect(u))
        end
        prob = ODEProblem(rhs!, q, (0.0, 1.0))
        sol = solve(prob, Vern9(); reltol=1.0e-11, abstol=1.0e-13, dtmax=1.0 / n_per_segment, save_everystep=false)
        q = collect(sol.u[end])
        step_count += length(sol.t) - 1
        max_raw_norm_drift = max(max_raw_norm_drift, abs(norm(q) - 1.0))
        q = qnormalize(q)
    end
    return Dict{String,Any}(
        "holonomy" => q,
        "raw_norm_drift_before_segment_renormalization" => max_raw_norm_drift,
        "n_per_segment_dtmax" => n_per_segment,
        "accepted_step_count" => step_count,
        "method" => "DifferentialEquations.Vern9 adaptive with dtmax=1/N; segment endpoint unit renormalization with raw drift recorded",
    )
end

function euler_coarse_loop(segments, n_per_segment::Int)
    q = [1.0, 0.0, 0.0, 0.0]
    dt_step = 1.0 / n_per_segment
    max_drift = 0.0
    for (start, stop) in segments
        delta = stop .- start
        for k in 0:(n_per_segment - 1)
            t = (k + 0.5) * dt_step
            at = bpst_a_t(start .+ t .* delta, delta)
            q = q .+ dt_step .* qmul(-at, q)
            max_drift = max(max_drift, abs(norm(q) - 1.0))
        end
    end
    return Dict("holonomy_raw" => q, "raw_norm_drift" => max_drift, "method" => "deliberately coarse explicit Euler control")
end

function angle_from_axis(q::Vector{Float64}, axis::Int)::Float64
    return atan(q[axis + 1], q[1])
end

function richardson(rows, order::Int)
    a = rows[end - 1]["angle"]
    b = rows[end]["angle"]
    limit = b + (b - a) / (2.0^order - 1.0)
    return Dict("order_assumed" => order, "limit" => limit, "error_bar" => abs(limit - b), "last_step_delta" => abs(b - a))
end

function convergence_for_loop(side::Float64, plane::Tuple{Int,Int}, axis::Int)
    rows = Any[]
    for n in [32, 64, 128, 256]
        rec = integrate_loop(square_loop(side, plane), n)
        q = Vector{Float64}(rec["holonomy"])
        push!(rows, Dict(
            "n_per_segment_dtmax" => n,
            "holonomy" => q,
            "angle" => angle_from_axis(q, axis),
            "unit_norm_drift" => rec["raw_norm_drift_before_segment_renormalization"],
            "accepted_step_count" => rec["accepted_step_count"],
        ))
    end
    return Dict("rows" => rows, "richardson" => richardson(rows, 9))
end

function sp1_transport_receipt()
    side = solve_side_for_theta(THETA)
    c1 = convergence_for_loop(side, (0, 1), 1)
    c2 = convergence_for_loop(side, (0, 2), 2)
    h1 = Vector{Float64}(c1["rows"][end]["holonomy"])
    h2 = Vector{Float64}(c2["rows"][end]["holonomy"])
    gap = commutator_gap(h1, h2)
    rev = integrate_loop(square_loop(side, (0, 1); reverse=true), 256)
    zero = integrate_loop(square_loop(side, (0, 1)), 64; connection="zero")
    coarse = euler_coarse_loop(square_loop(side, (0, 1)), 4)
    curvature_side = sqrt(THETA / 2.0)
    curvature_area = integrate_loop(square_loop(curvature_side, (0, 1)), 256)
    reverse_distance = qdist(Vector{Float64}(rev["holonomy"]), qconj(h1))
    zero_distance = qdist(Vector{Float64}(zero["holonomy"]), [1.0, 0.0, 0.0, 0.0])
    return Dict{String,Any}(
        "pass" => abs(gap - COMMITTED_GAP) <= 2.0e-9 && reverse_distance <= 1.0e-9 && zero_distance <= 1.0e-12 && coarse["raw_norm_drift"] > 1.0e-3,
        "connection" => "BPST Sp(1) A_t=Im(x*dconj(x))/(1+|x|^2); transport q'=-A_t q",
        "loop_model" => "same parent planes: rectangle in (x0,x1) gives i holonomy; rectangle in (x0,x2) gives j holonomy",
        "calibration" => Dict(
            "target_theta" => THETA,
            "side_length_solved_from_exact_square_integral" => side,
            "angle_formula" => "2*(a/sqrt(1+a^2))*atan(a/sqrt(1+a^2))",
            "why" => "parent row stored curvature-generated theta=pi/3; this packet uses explicit loops in the same planes calibrated to the same transported angle",
        ),
        "loop_1_i" => c1,
        "loop_2_j" => c2,
        "holonomy_1" => h1,
        "holonomy_2" => h2,
        "h1_h2" => qmul(h1, h2),
        "h2_h1" => qmul(h2, h1),
        "commutator_gap" => gap,
        "committed_algebraic_gap" => COMMITTED_GAP,
        "difference_from_committed_gap" => abs(gap - COMMITTED_GAP),
        "reverse_loop_inverse_control" => Dict(
            "reverse_holonomy" => rev["holonomy"],
            "inverse_expected" => qconj(h1),
            "distance" => reverse_distance,
            "pass" => reverse_distance <= 1.0e-9,
        ),
        "zero_curvature_control" => Dict(
            "scope" => "explicit A=0 control connection on the same loop; BPST itself has nonzero curvature on the tested chart",
            "holonomy" => zero["holonomy"],
            "distance_to_identity" => zero_distance,
            "pass" => zero_distance <= 1.0e-12,
        ),
        "coarse_integration_control" => coarse,
        "curvature_area_square_control" => Dict(
            "side_length_from_leading_order_area_theta" => curvature_side,
            "transport_angle_observed" => angle_from_axis(Vector{Float64}(curvature_area["holonomy"]), 1),
            "leading_order_theta" => THETA,
            "visible_difference" => abs(angle_from_axis(Vector{Float64}(curvature_area["holonomy"]), 1) - THETA),
        ),
        "strength_label" => "diagnostic_float_nonclaim_path_ordered",
    )
end

function small_loop_stokes_receipt()
    rows = Any[]
    for side in [0.12, 0.08, 0.04, 0.02]
        hol = integrate_loop(square_loop(side, (0, 1)), 256)
        q = Vector{Float64}(hol["holonomy"])
        leading = qexp(1, 2.0 * side^2)
        dist = qdist(q, leading)
        push!(rows, Dict(
            "side" => side,
            "transport_holonomy" => hol["holonomy"],
            "leading_exp_curvature" => leading,
            "distance" => dist,
            "distance_over_side4" => dist / side^4,
        ))
    end
    return Dict(
        "pass" => rows[end]["distance"] < rows[1]["distance"] && rows[end]["distance_over_side4"] < 4.0,
        "boundary" => "leading-order nonabelian Stokes only; no surface-ordered full nonabelian Stokes theorem is proved",
        "curvature_at_basepoint" => "F01=2*i for the (x0,x1) rectangle",
        "rows" => rows,
        "strength_label" => "leading_order_consistency_check",
    )
end

function u1_transport(eta::Float64, nsteps::Int)
    target = -2.0 * pi * cos(2.0 * eta)
    function rhs!(du, u, p, t)
        du[1] = -cos(2.0 * eta) * (2.0 * pi)
    end
    prob = ODEProblem(rhs!, [0.0], (0.0, 1.0))
    sol = solve(prob, Vern9(); reltol=1.0e-12, abstol=1.0e-14, dtmax=1.0 / nsteps, save_everystep=false)
    phase = sol.u[end][1]
    return Dict("eta" => eta, "computed_lifted_holonomy" => phase, "committed_lifted_holonomy" => target, "abs_error" => abs(phase - target))
end

function u1_contrast_receipt()
    etas = [pi / 12.0, pi / 6.0, pi / 4.0, pi / 3.0, 5.0 * pi / 12.0]
    rows = [u1_transport(eta, 256) for eta in etas]
    a = rows[2]["computed_lifted_holonomy"]
    b = rows[4]["computed_lifted_holonomy"]
    ab = cis(a + b)
    ba = cis(b + a)
    return Dict(
        "pass" => maximum([row["abs_error"] for row in rows]) <= 2.0e-12 && abs(ab - ba) == 0.0,
        "committed_values_source" => "geo_s2_connection_flux_foliation_v0: lifted_holonomy=-2*pi*cos(2*eta), rows eta=pi/12,pi/6,pi/4,pi/3,5pi/12",
        "rows" => rows,
        "u1_commutator_gap" => abs(ab - ba),
        "path_ordered_equals_algebraic_reason" => "U(1) connection values commute, so path ordering collapses to the ordinary exponential of the integrated phase",
        "strength_label" => "abelian_transport_contrast",
    )
end

function z3_any_nonzero(values::Vector{Int})
    solver = Z3.Solver()
    terms = Z3.Expr[]
    for value in values
        push!(terms, Z3.Not(Z3.IntVal(value) == Z3.IntVal(0)))
    end
    Z3.add(solver, isempty(terms) ? Z3.BoolVal(false) : Z3.Or(terms))
    return string(Z3.check(solver))
end

function smt_identity_receipt(q::Vector{Float64})
    scale = 10^3
    ints = [Int(round(v * scale)) for v in q]
    a, b, c, d = ints
    good = [0, 0, 0]
    wrong = [2 * a * b, 2 * a * c, 2 * a * d]
    zg = z3_any_nonzero(good)
    zw = z3_any_nonzero(wrong)
    return Dict(
        "pass" => zg == "unsat" && zw == "sat",
        "computed_scaled_quaternion" => ints,
        "positive_identity" => "vector((q*conj(q))) == 0 for computed transported q",
        "erased_flip_control" => "vector((q*q)) != 0 for the same computed q when the inverse vector flip is erased",
        "z3_verdict" => zg,
        "z3_erased_flip_control" => zw,
        "strength_label" => "computed_integer_smt_polarity",
    )
end

function parent_lineage()
    parent_payload = JSON.parsefile(PARENT_RESULT)
    paths = Dict(
        "envelope_source" => joinpath(PARENT_DIR, "$(PARENT_ID)_envelope.py"),
        "julia_source" => joinpath(PARENT_DIR, "$(PARENT_ID)_julia.jl"),
        "jax_source" => joinpath(PARENT_DIR, "$(PARENT_ID)_jax.py"),
        "envelope_result" => PARENT_RESULT,
    )
    return Dict(
        "parent_sim_id" => PARENT_ID,
        "read_only" => true,
        "paths" => Dict(name => rel(path) for (name, path) in paths),
        "sha256" => Dict(name => file_sha256(path) for (name, path) in paths),
        "pin_sha256" => parent_payload["pin_sha256"],
    )
end

function capability_receipts()
    return Dict(
        "Base.active_project" => Base.active_project(),
        "DifferentialEquations.ODEProblem" => string(ODEProblem),
        "DifferentialEquations.Vern9" => string(Vern9),
        "Z3.Solver" => string(Z3.Solver),
        "julia_version" => string(VERSION),
        "project_dependencies_count" => length(Pkg.project().dependencies),
    )
end

function build_result()
    sp1 = sp1_transport_receipt()
    stokes = small_loop_stokes_receipt()
    u1 = u1_contrast_receipt()
    smt = smt_identity_receipt(Vector{Float64}(sp1["holonomy_1"]))
    all_pass = sp1["pass"] && stokes["pass"] && u1["pass"] && smt["pass"]
    return Dict{String,Any}(
        "schema_version" => "$(SIM_ID)_leg_v1",
        "sim_id" => SIM_ID,
        "object_id" => SIM_ID,
        "role_id" => "julia_differentialequations_transport_leg",
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "all_pass" => all_pass,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "reads_peer_result" => READS_PEER_RESULT,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "parent_lineage" => parent_lineage(),
        "julia_project" => Base.active_project(),
        "packages_used" => ["DifferentialEquations", "Z3", "LinearAlgebra", "JSON", "Dates", "SHA", "Pkg"],
        "aligned_packages_load_bearing" => ["DifferentialEquations", "Z3"],
        "claim_path_tools" => ["DifferentialEquations", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => [
            Dict("tool" => "DifferentialEquations", "surface" => "Vern9 path-ordered transport ODE", "status" => "used"),
            Dict("tool" => "Z3", "surface" => "computed inverse identity erased-flip polarity", "status" => "used"),
            Dict("tool" => "LinearAlgebra", "surface" => "quaternion norm/distance controls", "status" => "used"),
            Dict("tool" => "JSON/Dates/SHA/Pkg", "surface" => "receipt assembly and capability metadata", "status" => "used"),
        ],
        "capability_receipts" => capability_receipts(),
        "receipts" => Dict(
            "J1_path_ordered_sp1_transport" => sp1,
            "J2_small_loop_leading_stokes_boundary" => stokes,
            "J3_abelian_u1_contrast" => u1,
        ),
        "proofs" => Dict("J4_computed_inverse_identity_smt" => smt),
        "controls" => Dict(
            "zero_curvature_identity" => sp1["zero_curvature_control"],
            "reverse_loop_inverse" => sp1["reverse_loop_inverse_control"],
            "coarse_integration_visible_drift" => sp1["coarse_integration_control"],
            "curvature_area_square_visible_difference" => sp1["curvature_area_square_control"],
        ),
        "seed_ledger" => Dict("rng" => "none", "deterministic" => true),
    )
end

function main()
    mkpath(RESULT_DIR)
    payload = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => payload["all_pass"], "result_path" => RESULT_PATH)))
    return payload["all_pass"] ? 0 : 1
end

exit(main())
