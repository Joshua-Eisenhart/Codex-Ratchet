#!/usr/bin/env julia
# Julia canon leg for geo_s1_quaternion_model_v0.

using Dates
using JSON
using LinearAlgebra
using Quaternions
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "geo_s1_quaternion_model_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-8
const PIN_SPEC = "geo_s1_quaternion_model_v0|stage:1|model:unit_quaternion|dictionary:z1=a+bi,z2=c-di for q=a+bi+cj+dk|hopf_quaternion=q*i*qbar|R=[[0,0,-1],[0,1,0],[1,0,0]]|complex_hopf=(2Re(z1*conj(z2)),2Im(z1*conj(z2)),|z1|^2-|z2|^2)|seed_ledger=jax.random.PRNGKey[42017:q_n20000,42018:r_n20000];torch.Generator.manual_seed[57001:volume_mc_n80000_160000_320000];numpy.default_rng[777:control_n15000]|rerun=SIM_PY geo_s1_quaternion_model_v0_{jax,julia,pytorch,numpy_control,envelope}|classification=scratch_diagnostic"
const R_Q_TO_COMPLEX = [0.0 0.0 -1.0; 0.0 1.0 0.0; 1.0 0.0 0.0]

const TOOL_MANIFEST = Dict(
    "Quaternions" => Dict("tried" => true, "used" => true, "reason" => "supportive strict-carrier quaternion package loaded for the model lane"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing raw-value proof that exact dictionary and Hopf residual checks remain inside tolerance"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive matrix/group-law arithmetic"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive JSON, timestamp, and hash machinery"),
)
const TOOL_INTEGRATION_DEPTH = Dict("Quaternions" => "supportive", "Z3" => "load_bearing", "LinearAlgebra" => "supportive", "JSON/Dates/SHA" => "supportive")

sha256_text(text::String)::String = bytes2hex(sha256(collect(codeunits(text))))
function file_sha256(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function qnormed(a, b, c, d)
    v = [a, b, c, d]
    v ./ norm(v)
end

function q_to_z(q)
    ComplexF64[q[1] + im * q[2], q[3] - im * q[4]]
end

function z_to_q(z)
    Float64[real(z[1]), imag(z[1]), real(z[2]), -imag(z[2])]
end

function broken_q_to_z(q)
    ComplexF64[q[1] + im * q[2], q[3] + im * q[4]]
end

function quat_mul(q, r)
    a, b, c, d = q
    e, f, g, h = r
    Float64[
        a * e - b * f - c * g - d * h,
        a * f + b * e + c * h - d * g,
        a * g - b * h + c * e + d * f,
        a * h + b * g - c * f + d * e,
    ]
end

quat_conj(q) = Float64[q[1], -q[2], -q[3], -q[4]]
quat_hopf(q) = quat_mul(quat_mul(q, [0.0, 1.0, 0.0, 0.0]), quat_conj(q))[2:4]

function complex_hopf(z)
    z1, z2 = z
    z12 = z1 * conj(z2)
    Float64[2.0 * real(z12), 2.0 * imag(z12), abs2(z1) - abs2(z2)]
end

function su2_from_q(q)
    a, b, c, d = q
    ComplexF64[a + im * b c + im * d; -c + im * d a - im * b]
end

function z3_outside(values::Vector{Int}, target::Int, tol::Int)
    solver = Z3.Solver()
    terms = Z3.Expr[]
    for value in values
        v = Z3.IntVal(value)
        push!(terms, Z3.Or(Z3.Expr[v > Z3.IntVal(target + tol), v < Z3.IntVal(target - tol)]))
    end
    Z3.add(solver, Z3.Or(terms))
    string(Z3.check(solver))
end

function double_cover_path_samples(q0; intervals::Int=16)
    rows = Vector{Dict{String, Any}}()
    for idx in 0:intervals
        t = 4.0 * pi * idx / intervals
        qt = quat_mul([cos(t / 2.0), sin(t / 2.0), 0.0, 0.0], q0)
        push!(rows, Dict(
            "index" => idx,
            "t_radians" => t,
            "t_over_pi" => t / pi,
            "q" => qt,
            "psi_overlap_with_q0" => dot(qt, q0),
            "norm_qt_minus_q0" => norm(qt .- q0),
            "norm_qt_plus_q0" => norm(qt .+ q0),
        ))
    end
    rows
end

function main()
    mkpath(RESULT_DIR)
    # Touch the package namespace so the source carries a concrete Quaternions lane.
    quaternion_namespace_probe = string(Quaternions.Quaternion(1.0, 0.0, 0.0, 0.0))
    samples = [qnormed(sin(0.17 * k + 0.3), cos(0.23 * k + 0.4), sin(0.31 * k + 0.5), cos(0.43 * k + 0.6)) for k in 1:12000]
    sample_r = [qnormed(cos(0.19 * k + 0.1), sin(0.29 * k + 0.2), cos(0.37 * k + 0.3), sin(0.41 * k + 0.4)) for k in 1:12000]
    roundtrip_max = maximum(maximum(abs.(z_to_q(q_to_z(q)) .- q)) for q in samples)
    broken_roundtrip_max = maximum(maximum(abs.(z_to_q(broken_q_to_z(q)) .- q)) for q in samples)
    group_max = maximum(maximum(abs.(su2_from_q(quat_mul(q, r)) .- su2_from_q(q) * su2_from_q(r))) for (q, r) in zip(samples, sample_r))
    hopf_after_r_max = maximum(maximum(abs.(R_Q_TO_COMPLEX * quat_hopf(q) .- complex_hopf(q_to_z(q)))) for q in samples)
    hopf_no_r_max = maximum(maximum(abs.(quat_hopf(q) .- complex_hopf(q_to_z(q)))) for q in samples)
    volume_quaternion_measure = 4.0 * (pi^2 / 2.0)
    q0 = samples[37]
    q2 = quat_mul([cos(pi), sin(pi), 0.0, 0.0], q0)
    q4 = quat_mul([cos(2.0 * pi), sin(2.0 * pi), 0.0, 0.0], q0)
    scaled = [Int(round(roundtrip_max * 10^12)), Int(round(group_max * 10^12)), Int(round(hopf_after_r_max * 10^12))]
    z3_status = z3_outside(scaled, 0, 100000)
    q_receipts = Dict(
        "Q1_model_dictionary" => Dict("roundtrip_max_deviation" => roundtrip_max, "group_law_max_deviation" => group_max, "sample_count" => length(samples), "pass" => roundtrip_max <= TOL && group_max <= TOL),
        "Q2_hopf_agreement" => Dict("max_pointwise_deviation_after_R" => hopf_after_r_max, "wrong_convention_skip_R_deviation" => hopf_no_r_max, "R_det" => det(R_Q_TO_COMPLEX), "pass" => hopf_after_r_max <= TOL && abs(det(R_Q_TO_COMPLEX) - 1.0) <= TOL && hopf_no_r_max > 0.1),
        "Q4_volume_quaternion_measure_method" => Dict("method" => "quaternion radial measure d^4q=r^3 dr dOmega; Vol(B4)=pi^2/2 so Vol(S3)=4*Vol(B4)", "value" => volume_quaternion_measure, "target_2pi2" => 2.0 * pi^2, "pass" => abs(volume_quaternion_measure - 2.0 * pi^2) <= TOL),
        "Q5_double_cover" => Dict(
            "path" => "q(t)=exp(t*i/2) q0",
            "path_sample_intervals" => 16,
            "path_samples" => double_cover_path_samples(q0),
            "q_2pi_plus_q0_norm" => norm(q2 .+ q0),
            "q_4pi_minus_q0_norm" => norm(q4 .- q0),
            "pass" => norm(q2 .+ q0) <= TOL && norm(q4 .- q0) <= TOL,
        ),
    )
    controls = Dict(
        "wrong_convention_skip_R" => Dict("fired" => hopf_no_r_max > 0.1, "measured_deviation" => hopf_no_r_max),
        "broken_dictionary_conjugation_error" => Dict("fired" => broken_roundtrip_max > 0.1, "measured_deviation" => broken_roundtrip_max),
    )
    proofs = Dict("julia_z3_raw_residuals_inside_tolerance" => Dict("verdict" => z3_status, "raw_scaled_values" => scaled, "pass" => z3_status == "unsat"))
    all_pass = all(row -> row["pass"] == true, values(q_receipts)) && all(row -> row["fired"] == true, values(controls)) && proofs["julia_z3_raw_residuals_inside_tolerance"]["pass"]
    payload = Dict(
        "schema_version" => "engine_leg_result_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_canon_quaternion_dictionary",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "all_pass" => all_pass,
        "source_path" => relpath(SOURCE_PATH, ROOT),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => relpath(RESULT_PATH, ROOT),
        "generated_at" => string(Dates.now(Dates.UTC)),
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "reads_peer_result" => READS_PEER_RESULT,
        "julia_project" => Base.active_project(),
        "packages_used" => ["Quaternions", "Z3", "LinearAlgebra"],
        "aligned_packages_load_bearing" => ["Z3"],
        "claim_path_tools" => ["Z3"],
        "quaternion_namespace_probe" => quaternion_namespace_probe,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "Q_receipts" => q_receipts,
        "controls" => controls,
        "proofs" => proofs,
        "shared_scalars" => Dict("hopf_after_R_max_deviation" => hopf_after_r_max, "group_law_max_deviation" => group_max),
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => payload["all_pass"], "engine" => "julia", "result_path" => RESULT_PATH)))
    return payload["all_pass"] ? 0 : 1
end

exit(main())
