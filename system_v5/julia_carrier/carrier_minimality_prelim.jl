#!/usr/bin/env julia
# object_id: carrier_minimality_prelim
# classification: scratch_diagnostic
# promotion_allowed: false
# claim_ceiling: PRELIM finite-map falsifier only. This does not claim basin,
# admission, proof, engine forcing, bridge, Axis0, or manifold closure.

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "carrier_minimality_prelim"
const RESULT_PATH = joinpath(@__DIR__, "carrier_minimality_prelim_julia_results.json")
const GUIDE_PATH = "/Users/joshuaeisenhart/wiki/projects/codex-ratchet/qit-igt-engine-valid-results-and-running-guide-2026-06-05.md"
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

normalize_vec(v::Vector{Float64}) = v ./ norm(v)
const AXIS = normalize_vec([1.0, 1.0, 1.0])
const QUOTIENT_THETA = 2.0 * pi / 3.0

function su2(axis::Vector{Float64}, theta::Float64)::Matrix{ComplexF64}
    generator = axis[1] .* SX .+ axis[2] .* SY .+ axis[3] .* SZ
    return cos(theta / 2.0) .* I2 .- im * sin(theta / 2.0) .* generator
end

function rodrigues(axis::Vector{Float64}, theta::Float64)::Matrix{Float64}
    x, y, z = axis
    K = Float64[
        0.0 -z y
        z 0.0 -x
        -y x 0.0
    ]
    return Matrix{Float64}(I, 3, 3) .+ sin(theta) .* K .+ (1.0 - cos(theta)) .* (K * K)
end

function so3_expm_series(axis::Vector{Float64}, theta::Float64; terms::Int=32)::Matrix{Float64}
    x, y, z = axis
    A = theta .* Float64[
        0.0 -z y
        z 0.0 -x
        -y x 0.0
    ]
    out = Matrix{Float64}(I, 3, 3)
    term = Matrix{Float64}(I, 3, 3)
    for n in 1:terms
        term = (term * A) ./ Float64(n)
        out .+= term
    end
    return out
end

dm(psi::Vector{ComplexF64}) = psi * psi'

function bloch_vec(rho::Matrix{ComplexF64})::Vector{Float64}
    return [real(tr(rho * SX)), real(tr(rho * SY)), real(tr(rho * SZ))]
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

function qrot(q::Vector{Float64}, v::Vector{Float64})::Vector{Float64}
    out = qmul(qmul(q, [0.0, v[1], v[2], v[3]]), qconj(q))
    return out[2:4]
end

function qaxis(axis::Vector{Float64}, theta::Float64)::Vector{Float64}
    return [
        cos(theta / 2.0),
        axis[1] * sin(theta / 2.0),
        axis[2] * sin(theta / 2.0),
        axis[3] * sin(theta / 2.0),
    ]
end

function qmatrix(q::Vector{Float64})::Matrix{Float64}
    basis = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    cols = [qrot(q, b) for b in basis]
    return hcat(cols...)
end

maxabs(x) = maximum(abs.(x))
approx_equal(a::Float64, b::Float64; tol::Float64=TOL) = abs(a - b) <= tol

function return_factor_complex(start::Vector{ComplexF64}, stop::Vector{ComplexF64})::ComplexF64
    return dot(start, stop) / dot(start, start)
end

function matrix_overlap_factor(start::Matrix{ComplexF64}, stop::Matrix{ComplexF64})::Float64
    return real(tr(start' * stop)) / real(tr(start' * start))
end

function vector_overlap_factor(start::Vector{Float64}, stop::Vector{Float64})::Float64
    return dot(start, stop) / dot(start, start)
end

function spinor_carrier()
    psi0 = ComplexF64[1.0 + 0im, 0.37 + 0.21im]
    psi0 = psi0 ./ sqrt(real(dot(psi0, psi0)))
    psi2 = su2(AXIS, 2.0 * pi) * psi0
    psi4 = su2(AXIS, 4.0 * pi) * psi0
    f2 = return_factor_complex(psi0, psi2)
    f4 = return_factor_complex(psi0, psi4)

    Uq = su2(AXIS, QUOTIENT_THETA)
    rq = bloch_vec(dm(Uq * psi0))
    rtarget = rodrigues(AXIS, QUOTIENT_THETA) * bloch_vec(dm(psi0))

    Ux = su2([1.0, 0.0, 0.0], pi / 3.0)
    Uy = su2([0.0, 1.0, 0.0], pi / 4.0)

    return Dict{String,Any}(
        "status" => "computed",
        "holonomy_2pi" => real(f2),
        "holonomy_2pi_imag" => imag(f2),
        "holonomy_4pi" => real(f4),
        "holonomy_4pi_imag" => imag(f4),
        "return_residual_2pi" => norm(psi2 .- f2 .* psi0),
        "return_residual_4pi" => norm(psi4 .- f4 .* psi0),
        "quotient_residual" => maxabs(rq .- rtarget),
        "quotient_target" => "Bloch r=Tr(rho sigma), compared with SO(3) Rodrigues rotation",
        "n01_commutator_norm" => norm(Ux * Uy - Uy * Ux),
        "presumption_ledger" => Dict{String,Any}(
            "field" => "C",
            "form_metric_type" => "Hermitian",
            "carrier_real_dim" => 4,
            "unit_state_real_dim" => 3,
            "quotient_real_dim" => 2,
            "group" => "SU(2)",
            "simply_connected" => true,
        ),
    )
end

function density_carrier()
    psi0 = ComplexF64[1.0 + 0im, 0.37 + 0.21im]
    psi0 = psi0 ./ sqrt(real(dot(psi0, psi0)))
    rho0 = dm(psi0)
    rho2 = su2(AXIS, 2.0 * pi) * rho0 * su2(AXIS, 2.0 * pi)'
    rho4 = su2(AXIS, 4.0 * pi) * rho0 * su2(AXIS, 4.0 * pi)'

    Uq = su2(AXIS, QUOTIENT_THETA)
    rq = bloch_vec(Uq * rho0 * Uq')
    rtarget = rodrigues(AXIS, QUOTIENT_THETA) * bloch_vec(rho0)

    Rx = rodrigues([1.0, 0.0, 0.0], pi / 3.0)
    Ry = rodrigues([0.0, 1.0, 0.0], pi / 4.0)

    return Dict{String,Any}(
        "status" => "computed",
        "holonomy_2pi" => matrix_overlap_factor(rho0, rho2),
        "holonomy_4pi" => matrix_overlap_factor(rho0, rho4),
        "return_residual_2pi" => norm(rho2 .- rho0),
        "return_residual_4pi" => norm(rho4 .- rho0),
        "quotient_residual" => maxabs(rq .- rtarget),
        "quotient_target" => "Bloch r=Tr(rho sigma), compared with SO(3) Rodrigues rotation",
        "n01_commutator_norm" => norm(Rx * Ry - Ry * Rx),
        "presumption_ledger" => Dict{String,Any}(
            "field" => "C",
            "form_metric_type" => "Hermitian trace-one positive density form",
            "carrier_real_dim" => 3,
            "tested_pure_orbit_real_dim" => 2,
            "group" => "SO(3) adjoint readout of SU(2) action",
            "simply_connected" => false,
        ),
    )
end

function real_vector_carrier()
    v0 = normalize_vec([0.23, -0.71, 0.48])
    R2 = rodrigues(AXIS, 2.0 * pi)
    R4 = rodrigues(AXIS, 4.0 * pi)
    Rq = so3_expm_series(AXIS, QUOTIENT_THETA)

    Rx = rodrigues([1.0, 0.0, 0.0], pi / 3.0)
    Ry = rodrigues([0.0, 1.0, 0.0], pi / 4.0)

    return Dict{String,Any}(
        "status" => "computed",
        "holonomy_2pi" => vector_overlap_factor(v0, R2 * v0),
        "holonomy_4pi" => vector_overlap_factor(v0, R4 * v0),
        "return_residual_2pi" => norm(R2 * v0 .- v0),
        "return_residual_4pi" => norm(R4 * v0 .- v0),
        "quotient_residual" => maxabs(Rq .- rodrigues(AXIS, QUOTIENT_THETA)),
        "quotient_target" => "SO(3) matrix exponential series compared with closed-form Rodrigues rotation",
        "n01_commutator_norm" => norm(Rx * Ry - Ry * Rx),
        "presumption_ledger" => Dict{String,Any}(
            "field" => "R",
            "form_metric_type" => "Euclidean symmetric",
            "carrier_real_dim" => 3,
            "group" => "SO(3)",
            "simply_connected" => false,
        ),
    )
end

function quaternion_carrier()
    q0 = [1.0, 0.0, 0.0, 0.0]
    q2 = qaxis(AXIS, 2.0 * pi)
    q4 = qaxis(AXIS, 4.0 * pi)
    qtarget = qaxis(AXIS, QUOTIENT_THETA)
    Rq = qmatrix(qtarget)
    Rtarget = rodrigues(AXIS, QUOTIENT_THETA)

    qx = qaxis([1.0, 0.0, 0.0], pi / 3.0)
    qy = qaxis([0.0, 1.0, 0.0], pi / 4.0)

    return Dict{String,Any}(
        "status" => "computed",
        "holonomy_2pi" => vector_overlap_factor(q0, q2),
        "holonomy_4pi" => vector_overlap_factor(q0, q4),
        "return_residual_2pi" => norm(q2 .- (-1.0 .* q0)),
        "return_residual_4pi" => norm(q4 .- q0),
        "quotient_residual" => maxabs(Rq .- Rtarget),
        "quotient_target" => "quaternion conjugation q v q*, compared with SO(3) Rodrigues rotation",
        "n01_commutator_norm" => norm(qmul(qx, qy) .- qmul(qy, qx)),
        "presumption_ledger" => Dict{String,Any}(
            "field" => "H",
            "form_metric_type" => "quaternionic norm",
            "carrier_real_dim" => 4,
            "unit_state_real_dim" => 3,
            "quotient_real_dim" => 3,
            "group" => "Sp(1)",
            "simply_connected" => true,
        ),
    )
end

function finite_subgroup_2t_carrier()
    # 2T element a=(1+i+j+k)/2 is a 120-degree SO(3) rotation around (1,1,1).
    # Its cube is -1 and sixth power is +1, exposing the inherited double cover.
    q0 = [1.0, 0.0, 0.0, 0.0]
    a = [0.5, 0.5, 0.5, 0.5]
    a2 = qmul(a, a)
    a3 = qmul(a2, a)
    a6 = qmul(a3, a3)
    Rq = qmatrix(a)
    Rtarget = rodrigues(AXIS, QUOTIENT_THETA)
    qi = [0.0, 1.0, 0.0, 0.0]
    qj = [0.0, 0.0, 1.0, 0.0]

    return Dict{String,Any}(
        "status" => "computed_optional",
        "holonomy_2pi" => vector_overlap_factor(q0, a3),
        "holonomy_4pi" => vector_overlap_factor(q0, a6),
        "return_residual_2pi" => norm(a3 .- (-1.0 .* q0)),
        "return_residual_4pi" => norm(a6 .- q0),
        "quotient_residual" => maxabs(Rq .- Rtarget),
        "quotient_target" => "2T generator projected by quaternion conjugation to tetrahedral SO(3) rotation",
        "n01_commutator_norm" => norm(qmul(qi, qj) .- qmul(qj, qi)),
        "presumption_ledger" => Dict{String,Any}(
            "field" => "H finite subset",
            "form_metric_type" => "restricted quaternionic norm",
            "carrier_real_dim" => 0,
            "carrier_cardinality" => 24,
            "group" => "2T binary tetrahedral subgroup of SU(2)",
            "simply_connected" => false,
            "note" => "discrete finite group; not path-connected",
        ),
    )
end

function compute_verdicts(carriers::Dict{String,Any})
    spinor = carriers["spinor_C2"]
    density = carriers["density_C2"]
    realv = carriers["real_vector_SO3"]
    quat = carriers["quaternion_Sp1"]

    rho_invisible = approx_equal(density["holonomy_2pi"], 1.0) &&
                    approx_equal(spinor["holonomy_2pi"], -1.0)
    quaternion_ties = approx_equal(quat["holonomy_2pi"], spinor["holonomy_2pi"]) &&
                      quat["quotient_residual"] < TOL
    real_vector_loses = approx_equal(realv["holonomy_2pi"], 1.0)
    spinor_uniquely_minimal = rho_invisible && real_vector_loses && !quaternion_ties

    return Dict{String,Any}(
        "rho_invisible" => Dict{String,Any}(
            "value" => rho_invisible,
            "numbers" => Dict{String,Any}(
                "density_C2.holonomy_2pi" => density["holonomy_2pi"],
                "spinor_C2.holonomy_2pi" => spinor["holonomy_2pi"],
            ),
        ),
        "quaternion_ties" => Dict{String,Any}(
            "value" => quaternion_ties,
            "numbers" => Dict{String,Any}(
                "quaternion_Sp1.holonomy_2pi" => quat["holonomy_2pi"],
                "spinor_C2.holonomy_2pi" => spinor["holonomy_2pi"],
                "quaternion_Sp1.quotient_residual" => quat["quotient_residual"],
                "tol" => TOL,
            ),
        ),
        "real_vector_loses" => Dict{String,Any}(
            "value" => real_vector_loses,
            "numbers" => Dict{String,Any}(
                "real_vector_SO3.holonomy_2pi" => realv["holonomy_2pi"],
            ),
        ),
        "spinor_uniquely_minimal" => Dict{String,Any}(
            "value" => spinor_uniquely_minimal,
            "numbers" => Dict{String,Any}(
                "quaternion_ties" => quaternion_ties,
            ),
        ),
    )
end

function build_result()
    carriers = Dict{String,Any}(
        "spinor_C2" => spinor_carrier(),
        "density_C2" => density_carrier(),
        "real_vector_SO3" => real_vector_carrier(),
        "quaternion_Sp1" => quaternion_carrier(),
        "finite_subgroup_2T" => finite_subgroup_2t_carrier(),
    )
    verdicts = compute_verdicts(carriers)
    density_bad = approx_equal(carriers["density_C2"]["holonomy_2pi"], -1.0)
    real_bad = approx_equal(carriers["real_vector_SO3"]["holonomy_2pi"], -1.0)
    stop_fired = density_bad || real_bad
    sentence = verdicts["quaternion_ties"]["value"] ?
        "At scratch_diagnostic ceiling, the spinor preference TIES the quaternion carrier; the unique-spinor claim is falsified down to psi-level surplus." :
        "At scratch_diagnostic ceiling, the spinor preference SURVIVES this quaternion comparison."
    shared_scalar_keys = [
        "holonomy_2pi",
        "holonomy_4pi",
        "return_residual_2pi",
        "return_residual_4pi",
        "quotient_residual",
        "n01_commutator_norm",
    ]
    shared_scalars = Dict{String,Any}()
    shared_booleans = Dict{String,Any}()
    for (carrier_name, carrier) in carriers
        for scalar_key in shared_scalar_keys
            shared_scalars["$carrier_name.$scalar_key"] = carrier[scalar_key]
        end
    end
    for (key, value) in verdicts
        shared_booleans["verdict.$key"] = value["value"]
    end
    shared_booleans["control.density_C2_shows_minus_sign"] = density_bad
    shared_booleans["control.real_vector_SO3_shows_minus_sign"] = real_bad
    shared_booleans["control.negative_control_miswired"] = stop_fired

    return Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia_reference",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "guide_reference" => Dict{String,Any}(
            "path" => GUIDE_PATH,
            "line_start" => 879,
            "line_end" => 929,
            "box" => "spinor-vector visibility fence and falsifier",
        ),
        "question" => "Under F01 finite + N01 noncommutation, does C2 spinor uniquely beat density/Bloch, real-vector SO(3), and quaternion Sp(1) carriers?",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "PRELIM finite-map falsifier only; no basin/admission/proof/engine-forcing claim",
        "root_constraints" => Dict{String,Any}(
            "F01" => "finite carrier representation and finite sampled map theta in {0,2pi,4pi} plus quotient test theta",
            "N01" => "noncommuting action witness recorded as n01_commutator_norm for each carrier",
        ),
        "axis" => AXIS,
        "quotient_theta" => QUOTIENT_THETA,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "shared_scalar_keys" => shared_scalar_keys,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "carriers" => carriers,
        "verdicts" => verdicts,
        "negative_control_status" => Dict{String,Any}(
            "density_C2_shows_minus_sign" => density_bad,
            "real_vector_SO3_shows_minus_sign" => real_bad,
            "negative_control_miswired" => stop_fired,
        ),
        "stop_condition_fired" => stop_fired,
        "plain_sentence" => sentence,
    )
end

function print_summary(result::Dict{String,Any})
    println("Carrier minimality prelim — Julia reference")
    println("classification: ", result["classification"], " | promotion_allowed: ", result["promotion_allowed"])
    for name in ["spinor_C2", "density_C2", "real_vector_SO3", "quaternion_Sp1", "finite_subgroup_2T"]
        c = result["carriers"][name]
        ledger = c["presumption_ledger"]
        println(name, ": holonomy_2pi=", c["holonomy_2pi"],
            " holonomy_4pi=", c["holonomy_4pi"],
            " quotient_residual=", c["quotient_residual"],
            " ledger(field=", ledger["field"],
            ", form=", ledger["form_metric_type"],
            ", real_dim=", ledger["carrier_real_dim"],
            ", group=", ledger["group"],
            ", simply_connected=", ledger["simply_connected"], ")")
    end
    for key in ["rho_invisible", "quaternion_ties", "real_vector_loses", "spinor_uniquely_minimal"]
        v = result["verdicts"][key]
        println(key, "=", v["value"], " numbers=", JSON.json(v["numbers"]))
    end
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
    println("STOP: negative control showed the lifted -1 sign; test is miswired.")
    exit(2)
end
