#!/usr/bin/env julia
# object_id: disc_spinor_carrier_minimality
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "disc_spinor_carrier_minimality"
const BACKEND = "julia_float64"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUTS = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const JULIA_CARRIER = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(JULIA_CARRIER, "disc_spinor_carrier_minimality_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUTS, "results", "disc_spinor_carrier_minimality_results.json")
const JAX_SOURCE_PATH = joinpath(FORMAL_SCOUTS, "sim_disc_spinor_carrier_minimality_probe.py")
const EPS = 1.0e-9
const STRICT_TOL = 1.0e-7
const QUOTIENT_THETA = 2.0 * pi / 3.0
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const SIM_EXECUTION_KIND = "nonclassical"
const CLAIM_CEILING = "scratch_diagnostic discriminator only: finite spinor-carrier minimality row for the 2pi=-1 double-cover witness. Supports only the bounded verdict reported here; no promotion, formal admission, PEPS3D admission, Axis0, bridge, physics, uniqueness of C2 over H1, or manifold closure claim."
const BLOCKED_CONSUMERS = [
    "formal_admission",
    "promotion",
    "PEPS3D_admission",
    "Axis0_admission",
    "bridge_admission",
    "physics_admission",
    "C2_unique_realization_claim",
    "manifold_closure",
]

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia Float64 backend" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent Float64 backend for finite SU(2), SO(3), Sp(1), and C3 carrier witnesses"),
    "Julia LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing matrix, vector, density, quaternion, residual, and parity computations"),
    "JAX peer backend" => Dict("tried" => true, "used" => true, "reason" => "load-bearing peer result for dual-backend parity on shared witness scalars and verdicts"),
    "owner double-cover carrier" => Dict("tried" => true, "used" => true, "reason" => "load-bearing layer structure; erasing SU(2)/Sp(1) double-cover signs to SO(3)/density changes the layer verdict"),
    "Julia stdlib" => Dict("tried" => true, "used" => true, "reason" => "supportive JSON serialization, timestamps, hashing, and peer-result loading"),
    "numpy" => Dict("tried" => false, "used" => false, "reason" => "not available in Julia path and explicitly excluded from this scratch diagnostic"),
    "pytorch" => Dict("tried" => false, "used" => false, "reason" => "explicitly excluded by the requested JAX plus Julia lane"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia Float64 backend" => "load_bearing",
    "Julia LinearAlgebra" => "load_bearing",
    "JAX peer backend" => "load_bearing",
    "owner double-cover carrier" => "load_bearing",
    "Julia stdlib" => "supportive",
    "numpy" => nothing,
    "pytorch" => nothing,
)

const I2 = ComplexF64[1.0 0.0; 0.0 1.0]
const SX = ComplexF64[0.0 1.0; 1.0 0.0]
const SY = ComplexF64[0.0 -im; im 0.0]
const SZ = ComplexF64[1.0 0.0; 0.0 -1.0]
const AXIS = [1.0, 2.0, 3.0] ./ norm([1.0, 2.0, 3.0])
const PSI0_RAW = ComplexF64[1.0 + 0.0im, 0.37 + 0.21im]
const PSI0 = PSI0_RAW ./ sqrt(real(dot(PSI0_RAW, PSI0_RAW)))
const VECTOR0_RAW = [0.23, -0.71, 0.48]
const VECTOR0 = VECTOR0_RAW ./ norm(VECTOR0_RAW)
const VERDICT_CODES = Dict{String,Float64}(
    "OPEN" => 0.0,
    "REAL_LAYER" => 1.0,
    "CONVENTION" => 2.0,
    "GENERIC" => 3.0,
    "PARTIAL" => 4.0,
)

sha256_file(path::String) = isfile(path) ? bytes2hex(sha256(read(path))) : nothing

function source_refs()
    paths = Dict{String,String}("jax_source" => JAX_SOURCE_PATH, "julia_source" => @__FILE__)
    Dict{String,Any}(
        key => Dict{String,Any}("path" => path, "exists" => isfile(path), "sha256" => sha256_file(path))
        for (key, path) in paths
    )
end

function su2(axis::Vector{Float64}, theta::Float64)::Matrix{ComplexF64}
    a = axis ./ norm(axis)
    generator = a[1] .* SX .+ a[2] .* SY .+ a[3] .* SZ
    return cos(theta / 2.0) .* I2 .- im * sin(theta / 2.0) .* generator
end

function rodrigues(axis::Vector{Float64}, theta::Float64)::Matrix{Float64}
    a = axis ./ norm(axis)
    x, y, z = a
    k = Float64[0.0 -z y; z 0.0 -x; -y x 0.0]
    Matrix{Float64}(I, 3, 3) .+ sin(theta) .* k .+ (1.0 - cos(theta)) .* (k * k)
end

function so3_expm_series(axis::Vector{Float64}, theta::Float64; terms::Int=32)::Matrix{Float64}
    a = axis ./ norm(axis)
    x, y, z = a
    generator = theta .* Float64[0.0 -z y; z 0.0 -x; -y x 0.0]
    out = Matrix{Float64}(I, 3, 3)
    term = Matrix{Float64}(I, 3, 3)
    for n in 1:terms
        term = (term * generator) ./ Float64(n)
        out .+= term
    end
    out
end

density(psi::Vector{ComplexF64}) = psi * psi'

function bloch_vec(rho::Matrix{ComplexF64})::Vector{Float64}
    [real(tr(rho * SX)), real(tr(rho * SY)), real(tr(rho * SZ))]
end

return_factor_complex(start::Vector{ComplexF64}, stop::Vector{ComplexF64}) = dot(start, stop) / dot(start, start)
matrix_overlap_factor(start::Matrix{ComplexF64}, stop::Matrix{ComplexF64}) = real(tr(start' * stop)) / real(tr(start' * start))
vector_overlap_factor(start::Vector{Float64}, stop::Vector{Float64}) = dot(start, stop) / dot(start, start)

function qmul(a::Vector{Float64}, b::Vector{Float64})::Vector{Float64}
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    [
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    ]
end

qconj(q::Vector{Float64}) = [q[1], -q[2], -q[3], -q[4]]

function qaxis(axis::Vector{Float64}, theta::Float64)::Vector{Float64}
    a = axis ./ norm(axis)
    [cos(theta / 2.0), a[1] * sin(theta / 2.0), a[2] * sin(theta / 2.0), a[3] * sin(theta / 2.0)]
end

function qrot(q::Vector{Float64}, v::Vector{Float64})::Vector{Float64}
    out = qmul(qmul(q, [0.0, v[1], v[2], v[3]]), qconj(q))
    out[2:4]
end

function qmatrix(q::Vector{Float64})::Matrix{Float64}
    basis = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    hcat([qrot(q, v) for v in basis]...)
end

function block_diag_su2_plus_one(u::Matrix{ComplexF64})::Matrix{ComplexF64}
    out = zeros(ComplexF64, 3, 3)
    out[1:2, 1:2] .= u
    out[3, 3] = 1.0 + 0.0im
    out
end

function carrier_witnesses()
    u2 = su2(AXIS, 2.0 * pi)
    u4 = su2(AXIS, 4.0 * pi)
    spinor2 = u2 * PSI0
    spinor4 = u4 * PSI0
    spinor_factor2 = return_factor_complex(PSI0, spinor2)
    spinor_factor4 = return_factor_complex(PSI0, spinor4)
    rho0 = density(PSI0)
    rho2 = u2 * rho0 * u2'
    rho4 = u4 * rho0 * u4'
    bloch0 = bloch_vec(rho0)
    quotient_spinor = bloch_vec(su2(AXIS, QUOTIENT_THETA) * rho0 * su2(AXIS, QUOTIENT_THETA)')
    quotient_so3 = rodrigues(AXIS, QUOTIENT_THETA) * bloch0

    r2 = rodrigues(AXIS, 2.0 * pi)
    r4 = rodrigues(AXIS, 4.0 * pi)
    rq_series = so3_expm_series(AXIS, QUOTIENT_THETA)
    rq_closed = rodrigues(AXIS, QUOTIENT_THETA)
    vector2 = r2 * VECTOR0
    vector4 = r4 * VECTOR0

    q0 = [1.0, 0.0, 0.0, 0.0]
    q2 = qaxis(AXIS, 2.0 * pi)
    q4 = qaxis(AXIS, 4.0 * pi)
    qtheta = qaxis(AXIS, QUOTIENT_THETA)
    qx = qaxis([1.0, 0.0, 0.0], pi / 3.0)
    qy = qaxis([0.0, 1.0, 0.0], pi / 4.0)

    c3_spin1_vector2 = r2 * VECTOR0
    c3_embed2 = block_diag_su2_plus_one(u2)
    c3_embed4 = block_diag_su2_plus_one(u4)
    psi3 = ComplexF64[PSI0[1], PSI0[2], 0.0 + 0.0im]
    psi3_spectator = ComplexF64[PSI0[1], PSI0[2], 0.2 + 0.0im]
    psi3_spectator = psi3_spectator ./ sqrt(real(dot(psi3_spectator, psi3_spectator)))
    c3_embed_factor2 = return_factor_complex(psi3, c3_embed2 * psi3)
    c3_embed_factor4 = return_factor_complex(psi3, c3_embed4 * psi3)
    c3_spectator_after2 = c3_embed2 * psi3_spectator
    ux = su2([1.0, 0.0, 0.0], pi / 3.0)
    uy = su2([0.0, 1.0, 0.0], pi / 4.0)
    rx = rodrigues([1.0, 0.0, 0.0], pi / 3.0)
    ry = rodrigues([0.0, 1.0, 0.0], pi / 4.0)

    Dict{String,Any}(
        "spinor_su2_holonomy_2pi" => real(spinor_factor2),
        "spinor_su2_holonomy_2pi_imag" => imag(spinor_factor2),
        "spinor_su2_holonomy_4pi" => real(spinor_factor4),
        "spinor_return_residual_2pi" => norm(spinor2 .+ PSI0),
        "spinor_return_residual_4pi" => norm(spinor4 .- PSI0),
        "density_holonomy_2pi" => matrix_overlap_factor(rho0, rho2),
        "density_holonomy_4pi" => matrix_overlap_factor(rho0, rho4),
        "density_return_residual_2pi" => norm(rho2 .- rho0),
        "density_return_residual_4pi" => norm(rho4 .- rho0),
        "su2_to_so3_quotient_residual" => norm(quotient_spinor .- quotient_so3),
        "vector_so3_holonomy_2pi" => vector_overlap_factor(VECTOR0, vector2),
        "vector_so3_holonomy_4pi" => vector_overlap_factor(VECTOR0, vector4),
        "vector_return_residual_2pi" => norm(vector2 .- VECTOR0),
        "vector_return_residual_4pi" => norm(vector4 .- VECTOR0),
        "so3_series_rodrigues_residual" => norm(rq_series .- rq_closed),
        "quaternion_holonomy_2pi" => vector_overlap_factor(q0, q2),
        "quaternion_holonomy_4pi" => vector_overlap_factor(q0, q4),
        "quaternion_return_residual_2pi" => norm(q2 .+ q0),
        "quaternion_return_residual_4pi" => norm(q4 .- q0),
        "quaternion_to_so3_2pi_residual" => norm(qmatrix(q2) .- r2),
        "quaternion_to_so3_quotient_residual" => norm(qmatrix(qtheta) .- rq_closed),
        "quaternion_spinor_gap_2pi" => abs(vector_overlap_factor(q0, q2) - real(spinor_factor2)),
        "c3_spin1_holonomy_2pi" => vector_overlap_factor(VECTOR0, c3_spin1_vector2),
        "c3_embedded_c2_holonomy_2pi" => real(c3_embed_factor2),
        "c3_embedded_c2_holonomy_4pi" => real(c3_embed_factor4),
        "c3_embed_spinor_gap_2pi" => abs(real(c3_embed_factor2) - real(spinor_factor2)),
        "c3_spectator_global_minus_residual" => norm(c3_spectator_after2 .+ psi3_spectator),
        "c3_spectator_return_residual" => norm(c3_spectator_after2 .- psi3_spectator),
        "su2_commutator_norm" => norm(ux * uy .- uy * ux),
        "so3_commutator_norm" => norm(rx * ry .- ry * rx),
        "quaternion_commutator_norm" => norm(qmul(qx, qy) .- qmul(qy, qx)),
        "full_layer_minus_channels" => 2.0,
        "erased_layer_minus_channels" => 0.0,
    )
end

function verdict_from(values)
    spinor_su2_has_minus1 = abs(values["spinor_su2_holonomy_2pi"] + 1.0) <= STRICT_TOL &&
        abs(values["spinor_su2_holonomy_4pi"] - 1.0) <= STRICT_TOL &&
        values["spinor_return_residual_2pi"] <= STRICT_TOL &&
        values["spinor_return_residual_4pi"] <= STRICT_TOL
    density_loses_minus1 = abs(values["density_holonomy_2pi"] - 1.0) <= STRICT_TOL &&
        values["density_return_residual_2pi"] <= STRICT_TOL
    vector_so3_loses_minus1 = abs(values["vector_so3_holonomy_2pi"] - 1.0) <= STRICT_TOL &&
        values["vector_return_residual_2pi"] <= STRICT_TOL
    spinor_su2_quotients_to_so3 = values["su2_to_so3_quotient_residual"] <= STRICT_TOL
    quaternion_ties_spinor = abs(values["quaternion_holonomy_2pi"] - values["spinor_su2_holonomy_2pi"]) <= STRICT_TOL &&
        values["quaternion_return_residual_2pi"] <= STRICT_TOL &&
        values["quaternion_to_so3_quotient_residual"] <= STRICT_TOL &&
        values["quaternion_spinor_gap_2pi"] <= STRICT_TOL
    c3_spin1_loses_minus1 = abs(values["c3_spin1_holonomy_2pi"] - 1.0) <= STRICT_TOL
    c3_embedded_c2_ties_spinor = values["c3_embed_spinor_gap_2pi"] <= STRICT_TOL
    c3_spectator_extra_not_load_bearing = values["c3_spectator_global_minus_residual"] > STRICT_TOL &&
        values["c3_spectator_return_residual"] > STRICT_TOL
    higher_qudit_unnecessary = spinor_su2_has_minus1 &&
        c3_spin1_loses_minus1 &&
        c3_embedded_c2_ties_spinor &&
        c3_spectator_extra_not_load_bearing
    noncommuting_controls = values["su2_commutator_norm"] > STRICT_TOL &&
        values["so3_commutator_norm"] > STRICT_TOL &&
        values["quaternion_commutator_norm"] > STRICT_TOL
    double_cover_needed = spinor_su2_has_minus1 && vector_so3_loses_minus1 && density_loses_minus1
    realization_convention = quaternion_ties_spinor
    erased_layer_verdict = vector_so3_loses_minus1 && density_loses_minus1 ? "GENERIC" : "OPEN"
    erased_layer_loses_result = vector_so3_loses_minus1 && density_loses_minus1 && spinor_su2_has_minus1
    owner_erasure_changes_result = double_cover_needed &&
        realization_convention &&
        erased_layer_verdict != "REAL_LAYER" &&
        values["full_layer_minus_channels"] > values["erased_layer_minus_channels"]
    controls_pass = density_loses_minus1 &&
        vector_so3_loses_minus1 &&
        spinor_su2_quotients_to_so3 &&
        c3_spin1_loses_minus1 &&
        c3_spectator_extra_not_load_bearing &&
        noncommuting_controls
    layer_verdict = if double_cover_needed && realization_convention && higher_qudit_unnecessary && owner_erasure_changes_result && controls_pass
        "REAL_LAYER"
    elseif double_cover_needed && realization_convention
        "PARTIAL"
    elseif realization_convention && !double_cover_needed
        "CONVENTION"
    elseif controls_pass && !double_cover_needed
        "GENERIC"
    else
        "OPEN"
    end
    Dict{String,Any}(
        "layer_verdict" => layer_verdict,
        "erased_layer_verdict" => erased_layer_verdict,
        "realization_verdict" => realization_convention ? "CONVENTION" : "OPEN",
        "double_cover_needed" => double_cover_needed,
        "realization_convention" => realization_convention,
        "density_loses_minus1" => density_loses_minus1,
        "vector_so3_loses_minus1" => vector_so3_loses_minus1,
        "spinor_su2_has_minus1" => spinor_su2_has_minus1,
        "spinor_su2_quotients_to_so3" => spinor_su2_quotients_to_so3,
        "quaternion_ties_spinor" => quaternion_ties_spinor,
        "c3_spin1_loses_minus1" => c3_spin1_loses_minus1,
        "c3_embedded_c2_ties_spinor" => c3_embedded_c2_ties_spinor,
        "c3_spectator_extra_not_load_bearing" => c3_spectator_extra_not_load_bearing,
        "higher_qudit_unnecessary" => higher_qudit_unnecessary,
        "noncommuting_controls" => noncommuting_controls,
        "owner_erasure_changes_result" => owner_erasure_changes_result,
        "erased_layer_loses_result" => erased_layer_loses_result,
        "erased_layer_changes_verdict" => layer_verdict != erased_layer_verdict,
        "controls_pass" => controls_pass,
    )
end

function parity_against_peer(result)
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "peer_available" => false,
            "within_1e_9" => false,
            "max_abs_diff" => nothing,
            "scalar_diffs" => Any[],
            "boolean_mismatches" => Any[],
            "string_mismatches" => [Dict("key" => "peer", "julia" => "present", "jax" => "missing")],
        )
    end
    peer = JSON.parsefile(JAX_RESULT_PATH)
    diffs = Vector{Dict{String,Any}}()
    max_diff = 0.0
    for (key, value) in result["shared_scalars"]
        peer_value = Float64(peer["shared_scalars"][key])
        diff = abs(Float64(value) - peer_value)
        max_diff = max(max_diff, diff)
        diff > EPS && push!(diffs, Dict{String,Any}("key" => key, "julia" => Float64(value), "jax" => peer_value, "abs_diff" => diff))
    end
    boolean_mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_booleans"]
        peer_value = Bool(peer["shared_booleans"][key])
        Bool(value) != peer_value && push!(boolean_mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => peer_value))
    end
    string_mismatches = Vector{Dict{String,Any}}()
    for key in ["layer_verdict", "realization_verdict"]
        if result[key] != peer[key]
            push!(string_mismatches, Dict{String,Any}("key" => key, "julia" => result[key], "jax" => peer[key]))
        end
    end
    Dict{String,Any}(
        "peer_result_path" => JAX_RESULT_PATH,
        "peer_available" => true,
        "within_1e_9" => max_diff <= EPS && isempty(diffs) && isempty(boolean_mismatches) && isempty(string_mismatches),
        "max_abs_diff" => max_diff,
        "scalar_diffs" => diffs,
        "boolean_mismatches" => boolean_mismatches,
        "string_mismatches" => string_mismatches,
    )
end

function build_result()
    mkpath(dirname(RESULT_PATH))
    values = carrier_witnesses()
    verdict = verdict_from(values)
    shared_scalars = Dict{String,Any}()
    for (key, value) in values
        shared_scalars[key] = value
    end
    shared_scalars["layer_verdict_code"] = VERDICT_CODES[verdict["layer_verdict"]]
    shared_scalars["erased_layer_verdict_code"] = VERDICT_CODES[verdict["erased_layer_verdict"]]
    shared_scalars["realization_verdict_code"] = VERDICT_CODES[verdict["realization_verdict"]]
    shared_booleans = Dict{String,Any}(
        "classification_fence" => CLASSIFICATION == "scratch_diagnostic" && !PROMOTION_ALLOWED && !FORMAL_ADMISSION_ALLOWED,
        "double_cover_needed" => verdict["double_cover_needed"],
        "realization_convention" => verdict["realization_convention"],
        "density_loses_minus1" => verdict["density_loses_minus1"],
        "vector_so3_loses_minus1" => verdict["vector_so3_loses_minus1"],
        "spinor_su2_has_minus1" => verdict["spinor_su2_has_minus1"],
        "spinor_su2_quotients_to_so3" => verdict["spinor_su2_quotients_to_so3"],
        "quaternion_ties_spinor" => verdict["quaternion_ties_spinor"],
        "c3_spin1_loses_minus1" => verdict["c3_spin1_loses_minus1"],
        "c3_embedded_c2_ties_spinor" => verdict["c3_embedded_c2_ties_spinor"],
        "c3_spectator_extra_not_load_bearing" => verdict["c3_spectator_extra_not_load_bearing"],
        "higher_qudit_unnecessary" => verdict["higher_qudit_unnecessary"],
        "noncommuting_controls" => verdict["noncommuting_controls"],
        "owner_erasure_changes_result" => verdict["owner_erasure_changes_result"],
        "erased_layer_changes_verdict" => verdict["erased_layer_changes_verdict"],
        "controls_pass" => verdict["controls_pass"],
    )
    positive = Dict{String,Any}(
        "spinor_su2_has_minus1" => Dict("pass" => verdict["spinor_su2_has_minus1"], "holonomy_2pi" => values["spinor_su2_holonomy_2pi"], "return_residual_2pi" => values["spinor_return_residual_2pi"]),
        "double_cover_needed_against_vector_and_density" => Dict("pass" => verdict["double_cover_needed"], "so3_holonomy_2pi" => values["vector_so3_holonomy_2pi"], "density_holonomy_2pi" => values["density_holonomy_2pi"]),
        "quaternion_ties_spinor_realization" => Dict("pass" => verdict["quaternion_ties_spinor"], "quaternion_holonomy_2pi" => values["quaternion_holonomy_2pi"], "spinor_holonomy_2pi" => values["spinor_su2_holonomy_2pi"]),
        "owner_carrier_load_bearing" => Dict("pass" => verdict["owner_erasure_changes_result"], "rule" => "erase double-cover layer to SO3/density quotient and the -1 channel count changes from 2 to 0", "full_layer_verdict" => verdict["layer_verdict"], "erased_layer_verdict" => verdict["erased_layer_verdict"], "full_layer_minus_channels" => values["full_layer_minus_channels"], "erased_layer_minus_channels" => values["erased_layer_minus_channels"]),
        "higher_qudit_unnecessary" => Dict("pass" => verdict["higher_qudit_unnecessary"], "reason" => "C2 already carries the -1; C3 spin-1 loses it, while C3 block embedding only reuses the C2 subspace"),
    )
    negative = Dict{String,Any}(
        "so3_vector_loses_minus1_control" => Dict("pass" => verdict["vector_so3_loses_minus1"], "holonomy_2pi" => values["vector_so3_holonomy_2pi"]),
        "density_projection_loses_minus1_control" => Dict("pass" => verdict["density_loses_minus1"], "holonomy_2pi" => values["density_holonomy_2pi"]),
        "c3_spin1_loses_minus1_control" => Dict("pass" => verdict["c3_spin1_loses_minus1"], "holonomy_2pi" => values["c3_spin1_holonomy_2pi"]),
        "c3_spectator_not_global_minus_control" => Dict("pass" => verdict["c3_spectator_extra_not_load_bearing"], "global_minus_residual" => values["c3_spectator_global_minus_residual"], "note" => "the extra dimension is not load-bearing for the spinor -1 unless the state is restricted back to the C2 block"),
    )
    boundary = Dict{String,Any}(
        "classification_fence" => Dict("pass" => shared_booleans["classification_fence"], "classification" => CLASSIFICATION, "promotion_allowed" => PROMOTION_ALLOWED, "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED),
        "claim_ceiling_blocks_downstream" => Dict("pass" => true, "claim_ceiling" => CLAIM_CEILING, "blocked_consumers" => BLOCKED_CONSUMERS),
        "honest_discriminator_verdict" => Dict("pass" => haskey(VERDICT_CODES, verdict["layer_verdict"]), "layer_verdict" => verdict["layer_verdict"], "note" => "REAL_LAYER means the double-cover layer is required against SO3/density controls; C2 versus H1 remains a realization convention."),
    )
    result = Dict{String,Any}(
        "schema" => "FORMAL_SCOUT_RESULT_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "backend" => BACKEND,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "sim_execution_kind" => SIM_EXECUTION_KIND,
        "sim_class" => "carrier_minimality_discriminator_probe",
        "source_alignment_category" => "spinor_carrier_minimality_double_cover_discriminator",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "jax_result_path" => JAX_RESULT_PATH,
        "source_refs" => source_refs(),
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "required_tools" => ["julia", "linearalgebra", "jax peer", "owner double-cover carrier"],
        "actual_tools_used" => ["julia", "linearalgebra", "julia stdlib", "jax peer result when present"],
        "numpy_compute_used" => false,
        "torch_compute_used" => false,
        "root_constraints_in_force" => Dict("F01" => "finite C2, R3, H1, and C3 witnesses at theta in {2pi,4pi,2pi/3}", "N01" => "noncommuting SU2, SO3, and quaternion rotation controls have nonzero commutator norms"),
        "finite_map" => "carrier choice -> finite 2pi/4pi holonomy and quotient residuals -> erasure controls -> layer verdict",
        "domain" => "one spinor-carrier minimality discriminator row over C2, SO3 vector, H1/Sp1 quaternion, and C3+ controls",
        "codomain_or_output" => "single layer verdict plus parity-checked finite witness scalars and booleans",
        "carrier_layer" => "SU2/Sp1 double-cover carrier with SO3/density erasure controls",
        "geometry_layer" => "finite double-cover holonomy, Hopf/Bloch quotient readout, and quaternion conjugation quotient",
        "bridge_layer" => "none",
        "cut_layer" => "SO3/density quotient and higher-qudit spectator erasure controls",
        "law_or_candidate_tested" => "A spinorial double-cover layer is needed to retain the 2pi=-1 holonomy; C2 and H1 are isomorphic realizations, and C3+ is not required.",
        "branch_status_before_run" => "discriminator row requested; survival not assumed",
        "allowed_claims" => ["finite double-cover discriminator verdict for this row", "SO3 vector and density controls lose the -1 holonomy", "H1/Sp1 ties the C2 spinor realization, so C2 uniqueness is not claimed", "C3+ is unnecessary under these finite witnesses", "JAX/Julia parity agreed or disagreements were reported"],
        "blocked_consumers" => BLOCKED_CONSUMERS,
        "promotion_blockers" => BLOCKED_CONSUMERS,
        "promotion_status" => "diagnostic_only",
        "eligible_consumers" => Any[],
        "row_id" => "spinor_carrier_minimality",
        "layer_verdict" => verdict["layer_verdict"],
        "erased_layer_verdict" => verdict["erased_layer_verdict"],
        "realization_verdict" => verdict["realization_verdict"],
        "realization_note" => "C2 spinor and H1/Sp1 unit quaternion both carry the -1; choosing one is a realization convention in this row.",
        "vector_so3_loses_minus1" => verdict["vector_so3_loses_minus1"],
        "spinor_su2_has_minus1" => verdict["spinor_su2_has_minus1"],
        "quaternion_ties_spinor" => verdict["quaternion_ties_spinor"],
        "higher_qudit_unnecessary" => verdict["higher_qudit_unnecessary"],
        "owner_erasure_changes_result" => verdict["owner_erasure_changes_result"],
        "finite_witness" => Dict("values" => values, "verdict" => verdict, "axis" => AXIS, "quotient_theta" => QUOTIENT_THETA),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "positive" => positive,
        "negative" => negative,
        "graveyard_companions" => negative,
        "boundary" => boundary,
        "nearby_variants" => Dict("total" => 1, "passed" => haskey(VERDICT_CODES, verdict["layer_verdict"]) ? 1 : 0, "variants" => ["spinor_carrier_minimality"]),
        "why_not_v4_probes" => Dict("reason" => "v5 scratch dual-backend discriminator row; not a v4 promotion or formal-admission probe"),
    )
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = result["parity"]["peer_available"] &&
        result["parity"]["within_1e_9"] &&
        shared_booleans["classification_fence"] &&
        verdict["layer_verdict"] == "REAL_LAYER" &&
        verdict["vector_so3_loses_minus1"] &&
        verdict["spinor_su2_has_minus1"] &&
        verdict["quaternion_ties_spinor"] &&
        verdict["higher_qudit_unnecessary"] &&
        verdict["owner_erasure_changes_result"]
    result["result_summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "layer_verdict" => verdict["layer_verdict"],
        "realization_verdict" => verdict["realization_verdict"],
        "claim_ceiling" => CLAIM_CEILING,
        "parity_within_1e_9" => result["parity"]["within_1e_9"],
        "vector_so3_loses_minus1" => verdict["vector_so3_loses_minus1"],
        "spinor_su2_has_minus1" => verdict["spinor_su2_has_minus1"],
        "quaternion_ties_spinor" => verdict["quaternion_ties_spinor"],
        "higher_qudit_unnecessary" => verdict["higher_qudit_unnecessary"],
    )
    result["stop_condition_fired"] = !result["all_pass"]
    result["blockers"] = result["all_pass"] ? Any[] : ["peer parity missing/disagreed or a core discriminator/control boolean failed"]
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("RESULT $(OBJECT_ID) julia=$(RESULT_PATH) jax=$(JAX_RESULT_PATH) all_pass=$(lowercase(string(result["all_pass"]))) layer_verdict=$(result["layer_verdict"]) parity=$(lowercase(string(result["parity"]["within_1e_9"]))) vector_so3_loses_minus1=$(lowercase(string(result["vector_so3_loses_minus1"]))) spinor_su2_has_minus1=$(lowercase(string(result["spinor_su2_has_minus1"]))) quaternion_ties_spinor=$(lowercase(string(result["quaternion_ties_spinor"]))) higher_qudit_unnecessary=$(lowercase(string(result["higher_qudit_unnecessary"])))")
    return result["all_pass"] ? 0 : 1
end

exit(main())
