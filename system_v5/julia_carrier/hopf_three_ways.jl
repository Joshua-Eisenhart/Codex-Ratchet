#!/usr/bin/env julia
# object_id: hopf_three_ways
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: Finite S3->S2 Hopf convention check only. No basin,
# admission, engine, Axis0, bridge, gravity, or manifold-closure claim.

using Dates
using JSON
using LinearAlgebra
using CliffordAlgebras

const OBJECT_ID = "hopf_three_ways"
const RESULT_PATH = joinpath(@__DIR__, "hopf_three_ways_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "hopf_three_ways_jax_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const SAMPLE_COUNT = 96

const CL = CliffordAlgebra(:Cl3)
const E23 = CL.e2 * CL.e3
const E31 = CL.e3 * CL.e1
const E12 = CL.e1 * CL.e2

function probe_vector(dim::Int, sample_idx::Int, side::Int)
    [((Float64(mod((sample_idx + 17) * (j + 3) * (side + 5) * 37 +
                   (j + 1)^2 * 19 + sample_idx * 11 + side * 13, 101)) - 50.0) / 37.0) for j in 1:dim]
end

function unit_quaternion_samples()
    samples = Vector{Vector{Float64}}()
    append!(samples, [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ])
    for sample_idx in 1:SAMPLE_COUNT
        v = probe_vector(4, sample_idx, 11)
        push!(samples, v ./ norm(v))
    end
    samples
end

function qmul(x::AbstractVector{Float64}, y::AbstractVector{Float64})
    a, b, c, d = x
    e, f, g, h = y
    [
        a * e - b * f - c * g - d * h,
        a * f + b * e + c * h - d * g,
        a * g - b * h + c * e + d * f,
        a * h + b * g - c * f + d * e,
    ]
end

qconj(q::AbstractVector{Float64}) = [q[1], -q[2], -q[3], -q[4]]

function quaternion_hopf(q::AbstractVector{Float64})
    raw = qmul(qmul(q, [0.0, 1.0, 0.0, 0.0]), qconj(q))
    i_coeff = raw[2]
    j_coeff = raw[3]
    k_coeff = raw[4]
    [-k_coeff, j_coeff, i_coeff]
end

function spinor_bloch(q::AbstractVector{Float64})
    a, b, c, d = q
    z = complex(a, b)
    w = complex(c, d)
    psi = [conj(z), w]
    sigma_x = ComplexF64[0 1; 1 0]
    sigma_y = ComplexF64[0 -im; im 0]
    sigma_z = ComplexF64[1 0; 0 -1]
    [
        real(dot(psi, sigma_x * psi)),
        real(dot(psi, sigma_y * psi)),
        real(dot(psi, sigma_z * psi)),
    ]
end

function complex_hopf(q::AbstractVector{Float64})
    a, b, c, d = q
    z = complex(a, b)
    w = complex(c, d)
    zw = z * w
    [2.0 * real(zw), 2.0 * imag(zw), abs2(z) - abs2(w)]
end

function clifford_hopf(q::AbstractVector{Float64})
    a, b, c, d = q
    R = a * CL.𝟏 - b * E23 - c * E31 - d * E12
    B = R * E23 * reverse(R)
    i_coeff = real(B.e2e3)
    j_coeff = real(B.e3e1)
    k_coeff = real(B.e1e2)
    [-k_coeff, j_coeff, i_coeff]
end

function right_phase(q::AbstractVector{Float64}, theta::Float64)
    qmul(q, [cos(theta), sin(theta), 0.0, 0.0])
end

function spinor_pair(q::AbstractVector{Float64})
    a, b, c, d = q
    z = complex(a, b)
    w = complex(c, d)
    [conj(z), w]
end

linf(x::AbstractVector, y::AbstractVector) = maximum(abs.(x .- y))

function parity_against_peer(result::Dict{String,Any}, peer_path::String)
    if !isfile(peer_path)
        return Dict{String,Any}(
            "peer_result_path" => peer_path,
            "status" => "pending_peer_backend",
            "shared_scalar_rows" => [],
            "max_diff_key" => nothing,
            "parity_max_diff" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [Dict{String,Any}("missing" => peer_path)],
            "boolean_mismatches" => [],
            "missing_keys" => [],
            "stop_condition_fired" => true,
        )
    end
    peer = JSON.parsefile(peer_path)
    rows = Vector{Dict{String,Any}}()
    max_diff = 0.0
    max_diff_key = nothing
    strict = Vector{Dict{String,Any}}()
    missing = String[]
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        jv = Float64(value)
        pv = Float64(peer["shared_scalars"][key])
        diff = abs(jv - pv)
        if diff > max_diff
            max_diff = diff
            max_diff_key = key
        end
        row = Dict{String,Any}("key" => key, "julia" => jv, "jax" => pv, "abs_diff" => diff)
        push!(rows, row)
        diff > STRICT_STOP_TOL && push!(strict, row)
    end
    mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_booleans"]
        if !haskey(peer["shared_booleans"], key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer["shared_booleans"][key])
            push!(mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => Bool(peer["shared_booleans"][key])))
        end
    end
    Dict{String,Any}(
        "peer_result_path" => peer_path,
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "max_diff_key" => max_diff_key,
        "parity_max_diff" => max_diff,
        "within_1e_9" => max_diff < TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function build_result()
    samples = unit_quaternion_samples()
    max_input_unit_norm_error = 0.0
    quaternion_s2_norm_max_error = 0.0
    spinor_s2_norm_max_error = 0.0
    complex_s2_norm_max_error = 0.0
    clifford_s2_norm_max_error = 0.0
    quat_spinor_max_linf = 0.0
    quat_complex_max_linf = 0.0
    spinor_complex_max_linf = 0.0
    clifford_quat_max_linf = 0.0
    fiber_invariance_max_linf = 0.0
    right_phase_global_phase_max_linf = 0.0

    thetas = collect(range(0.0, 2pi, length = 13))[1:end-1]
    for q in samples
        hq = quaternion_hopf(q)
        hs = spinor_bloch(q)
        hc = complex_hopf(q)
        hcl = clifford_hopf(q)
        max_input_unit_norm_error = max(max_input_unit_norm_error, abs(norm(q) - 1.0))
        quaternion_s2_norm_max_error = max(quaternion_s2_norm_max_error, abs(norm(hq) - 1.0))
        spinor_s2_norm_max_error = max(spinor_s2_norm_max_error, abs(norm(hs) - 1.0))
        complex_s2_norm_max_error = max(complex_s2_norm_max_error, abs(norm(hc) - 1.0))
        clifford_s2_norm_max_error = max(clifford_s2_norm_max_error, abs(norm(hcl) - 1.0))
        quat_spinor_max_linf = max(quat_spinor_max_linf, linf(hq, hs))
        quat_complex_max_linf = max(quat_complex_max_linf, linf(hq, hc))
        spinor_complex_max_linf = max(spinor_complex_max_linf, linf(hs, hc))
        clifford_quat_max_linf = max(clifford_quat_max_linf, linf(hcl, hq))
        psi = spinor_pair(q)
        for theta in thetas
            qp = right_phase(q, theta)
            fiber_invariance_max_linf = max(fiber_invariance_max_linf, linf(quaternion_hopf(qp), hq))
            psi_phase = spinor_pair(qp)
            right_phase_global_phase_max_linf = max(right_phase_global_phase_max_linf,
                maximum(abs.(psi_phase .- exp(-im * theta) .* psi)))
        end
    end

    nonunit_q = 1.7 .* samples[end]
    nonunit_output_norm = norm(quaternion_hopf(nonunit_q))
    nonunit_s2_norm_error = abs(nonunit_output_norm - 1.0)
    max_pairwise_disagreement = maximum([quat_spinor_max_linf, quat_complex_max_linf, spinor_complex_max_linf])

    verdicts = Dict{String,Any}(
        "hopf_three_ways_agree" => max_pairwise_disagreement < TOL,
        "fiber_invariant" => fiber_invariance_max_linf < TOL,
        "clifford_rotor_agrees" => clifford_quat_max_linf < TOL,
        "nonunit_control_pass" => nonunit_s2_norm_error > 0.5,
    )
    controls = Dict{String,Any}(
        "unit_inputs_control_ok" => max_input_unit_norm_error < TOL,
        "nonunit_quaternion_off_s2_control_ok" => verdicts["nonunit_control_pass"],
        "control_miswired" => !(max_input_unit_norm_error < TOL && verdicts["nonunit_control_pass"]),
    )
    shared_scalars = Dict{String,Any}(
        "max_input_unit_norm_error" => max_input_unit_norm_error,
        "quaternion_s2_norm_max_error" => quaternion_s2_norm_max_error,
        "spinor_s2_norm_max_error" => spinor_s2_norm_max_error,
        "complex_s2_norm_max_error" => complex_s2_norm_max_error,
        "clifford_s2_norm_max_error" => clifford_s2_norm_max_error,
        "quat_spinor_max_linf" => quat_spinor_max_linf,
        "quat_complex_max_linf" => quat_complex_max_linf,
        "spinor_complex_max_linf" => spinor_complex_max_linf,
        "clifford_quat_max_linf" => clifford_quat_max_linf,
        "max_pairwise_disagreement" => max_pairwise_disagreement,
        "fiber_invariance_max_linf" => fiber_invariance_max_linf,
        "right_phase_global_phase_max_linf" => right_phase_global_phase_max_linf,
        "nonunit_output_norm" => nonunit_output_norm,
        "nonunit_s2_norm_error" => nonunit_s2_norm_error,
    )
    shared_booleans = Dict{String,Any}()
    for (key, value) in verdicts
        shared_booleans["verdict.$key"] = value
    end
    for (key, value) in controls
        shared_booleans["control.$key"] = value
    end

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia_full_sim",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "Finite S3->S2 Hopf convention check only; no basin, admission, engine, Axis0, bridge, gravity, or manifold-closure claim.",
        "sim_execution_kind" => "classical",
        "sim_class" => "hopf_geometry_convention_probe",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "sample_count" => length(samples),
        "convention" => Dict{String,Any}(
            "quaternion" => "q=a+b*i+c*j+d*k; compute q*i*qbar = I*i + J*j + K*k, then compare S2 coordinates as (-K,J,I)",
            "spinor" => "z=a+b*i, w=c+d*i, psi_R=(conj(z),w)",
            "complex_hopf" => "(2*Re(z*w), 2*Im(z*w), |z|^2-|w|^2)",
            "right_fiber_action" => "q -> q*exp(i*theta), equivalent to z->z*exp(i*theta), w->w*exp(-i*theta), psi_R->exp(-i*theta)*psi_R",
        ),
        "tool_manifest" => Dict{String,Any}(
            "Julia" => "load_bearing quaternion, spinor, and complex Hopf computations",
            "LinearAlgebra" => "load_bearing S2 norms, disagreements, and fiber residuals",
            "CliffordAlgebras" => "load_bearing independent Cl(3) even-rotor sandwich check for q*i*qbar",
            "JSON" => "supportive result serialization",
        ),
        "tool_integration_depth" => Dict{String,Any}(
            "Julia" => "load_bearing",
            "LinearAlgebra" => "load_bearing",
            "CliffordAlgebras" => "load_bearing",
            "JSON" => "supportive",
        ),
        "verdicts" => verdicts,
        "controls" => controls,
        "numbers" => shared_scalars,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "plain_sentence" => "The three Hopf maps agree after fixing one S2 coordinate convention: unit quaternions, the paired spinor, and the complex formula are the same finite S3->S2 object with an S1 fiber.",
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["stop_condition_fired"] = controls["control_miswired"] ||
        !verdicts["hopf_three_ways_agree"] ||
        !verdicts["fiber_invariant"] ||
        !verdicts["clifford_rotor_agrees"] ||
        result["parity"]["stop_condition_fired"]
    result
end

function print_summary(result::Dict{String,Any})
    n = result["numbers"]
    println("hopf_three_ways - Julia full sim")
    println("hopf_three_ways_agree=", result["verdicts"]["hopf_three_ways_agree"],
        " max_pairwise_disagreement=", n["max_pairwise_disagreement"])
    println("fiber_invariant=", result["verdicts"]["fiber_invariant"],
        " fiber_invariance_max_linf=", n["fiber_invariance_max_linf"])
    println("clifford_rotor_agrees=", result["verdicts"]["clifford_rotor_agrees"],
        " clifford_quat_max_linf=", n["clifford_quat_max_linf"])
    println("nonunit_control_pass=", result["verdicts"]["nonunit_control_pass"],
        " nonunit_output_norm=", n["nonunit_output_norm"],
        " nonunit_s2_norm_error=", n["nonunit_s2_norm_error"])
    println("parity_status=", result["parity"]["status"],
        " parity_max_diff=", result["parity"]["parity_max_diff"],
        " within_1e-9=", result["parity"]["within_1e_9"])
    println(result["plain_sentence"])
    println("wrote: ", result["result_path"])
end

result = build_result()
open(RESULT_PATH, "w") do io
    JSON.print(io, result, 2)
    write(io, "\n")
end
print_summary(result)

if result["stop_condition_fired"]
    println("STOP: hopf_three_ways control/verdict/parity condition failed.")
    exit(2)
end
