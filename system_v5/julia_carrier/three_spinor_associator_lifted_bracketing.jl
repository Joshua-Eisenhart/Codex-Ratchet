#!/usr/bin/env julia
# object_id: three_spinor_associator_lifted_bracketing
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "three_spinor_associator_lifted_bracketing"
const RESULT_PATH = joinpath(@__DIR__, "three_spinor_associator_lifted_bracketing_julia_results.json")
const JAX_SOURCE_PATH = joinpath(@__DIR__, "..", "ops", "formal_scouts", "sim_three_spinor_associator_lifted_bracketing_probe.py")
const JAX_RESULT_PATH = joinpath(@__DIR__, "..", "ops", "formal_scouts", "results", "three_spinor_associator_lifted_bracketing_probe_results.json")
const TOL = 1.0e-9

const FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

function octonion_table()
    table = fill((0.0, 0), 8, 8)
    table[1, 1] = (1.0, 1)
    for i in 2:8
        table[1, i] = (1.0, i)
        table[i, 1] = (1.0, i)
        table[i, i] = (-1.0, 1)
    end
    for (a0, b0, c0) in FANO
        a, b, c = a0 + 1, b0 + 1, c0 + 1
        for (i, j, k) in [(a, b, c), (b, c, a), (c, a, b)]
            table[i, j] = (1.0, k)
        end
        for (i, j, k) in [(b, a, c), (c, b, a), (a, c, b)]
            table[i, j] = (-1.0, k)
        end
    end
    table
end

const TABLE = octonion_table()

function basis(idx0::Int)
    v = zeros(Float64, 8)
    v[idx0 + 1] = 1.0
    v
end

function oct_mul(a::AbstractVector{Float64}, b::AbstractVector{Float64})
    out = zeros(Float64, 8)
    @inbounds for i in 1:8
        for j in 1:8
            sign, k = TABLE[i, j]
            out[k] += sign * a[i] * b[j]
        end
    end
    out
end

function normalize_spinor(psi::Vector{ComplexF64})
    psi ./ norm(psi)
end

function seed_three_qubit_spinor()
    real = [1.0, -2.0, 3.0, 5.0, -7.0, 11.0, -13.0, 17.0]
    imag = [19.0, -23.0, 29.0, -31.0, 37.0, -41.0, 43.0, -47.0]
    normalize_spinor(ComplexF64.(real, imag))
end

function spinor_to_oct_pair(psi::Vector{ComplexF64})
    real.(psi), imag.(psi)
end

function oct_pair_to_spinor(pair)
    a, b = pair
    normalize_spinor(ComplexF64.(a, b))
end

function right_action_pair(pair, q::AbstractVector{Float64})
    a, b = pair
    (oct_mul(a, q), oct_mul(b, q))
end

function bracket_products(x, y, z)
    (oct_mul(oct_mul(x, y), z), oct_mul(x, oct_mul(y, z)))
end

function density(psi::Vector{ComplexF64})
    psi * psi'
end

function spinor_bracket_witness(psi::Vector{ComplexF64}, x, y, z)
    pair = spinor_to_oct_pair(psi)
    left_q, right_q = bracket_products(x, y, z)
    left = oct_pair_to_spinor(right_action_pair(pair, left_q))
    right = oct_pair_to_spinor(right_action_pair(pair, right_q))
    delta = left - right
    rho_left = density(left)
    rho_right = density(right)
    Dict{String,Any}(
        "product_gap" => norm(left_q - right_q),
        "spinor_gap" => norm(delta),
        "basis_probe_max_abs" => maximum(abs.(delta)),
        "optimal_unit_probe_abs" => norm(delta),
        "density_gap_fro" => norm(rho_left - rho_right),
        "left_product" => collect(left_q),
        "right_product" => collect(right_q),
    )
end

function right_mult_matrix(q::AbstractVector{Float64})
    hcat([oct_mul(basis(i), q) for i in 0:7]...)
end

function raw_matrix_associativity_gap(x, y, z)
    rx = right_mult_matrix(x)
    ry = right_mult_matrix(y)
    rz = right_mult_matrix(z)
    norm((rz * ry) * rx - rz * (ry * rx))
end

function density_phase_erasure_control(psi::Vector{ComplexF64})
    minus = -psi
    rho = density(psi)
    rho_minus = density(minus)
    spinor_gap = norm(psi - minus)
    density_gap = norm(rho - rho_minus)
    Dict{String,Any}(
        "spinor_sign_gap" => spinor_gap,
        "density_sign_gap" => density_gap,
        "pass" => spinor_gap > 1.0 && density_gap < TOL,
    )
end

function file_sha256(path::String)
    isfile(path) || return nothing
    bytes2hex(sha256(read(path)))
end

function main()
    started = time()
    psi = seed_three_qubit_spinor()
    oct_x, oct_y, oct_z = basis(1), basis(2), basis(4)
    h_x, h_y, h_z = basis(1), basis(2), basis(3)
    alt_x, alt_y, alt_z = basis(1), basis(1), basis(4)

    oct_witness = spinor_bracket_witness(psi, oct_x, oct_y, oct_z)
    h_control = spinor_bracket_witness(psi, h_x, h_y, h_z)
    alt_control = spinor_bracket_witness(psi, alt_x, alt_y, alt_z)
    matrix_gap = raw_matrix_associativity_gap(oct_x, oct_y, oct_z)
    phase_control = density_phase_erasure_control(psi)

    shared_scalars = Dict{String,Any}(
        "three_qubit_complex_dim" => length(psi),
        "three_qubit_real_dim" => 2 * length(psi),
        "two_qubit_real_dim" => 8,
        "octonion_pair_real_dim" => 16,
        "octonion_product_gap" => oct_witness["product_gap"],
        "octonion_spinor_gap" => oct_witness["spinor_gap"],
        "octonion_basis_probe_max_abs" => oct_witness["basis_probe_max_abs"],
        "octonion_optimal_unit_probe_abs" => oct_witness["optimal_unit_probe_abs"],
        "octonion_density_gap_fro" => oct_witness["density_gap_fro"],
        "h_control_spinor_gap" => h_control["spinor_gap"],
        "h_control_product_gap" => h_control["product_gap"],
        "alt_control_spinor_gap" => alt_control["spinor_gap"],
        "alt_control_product_gap" => alt_control["product_gap"],
        "raw_matrix_assoc_gap" => matrix_gap,
        "density_sign_spinor_gap" => phase_control["spinor_sign_gap"],
        "density_sign_density_gap" => phase_control["density_sign_gap"],
    )
    shared_booleans = Dict{String,Any}(
        "three_qubit_minimum_for_octonion_pair" => 2 * length(psi) == 16,
        "two_qubit_insufficient_for_octonion_pair" => 8 < 16,
        "octonion_bracketing_lifted_spinor_visible" => oct_witness["spinor_gap"] > TOL && oct_witness["basis_probe_max_abs"] > TOL,
        "density_quotient_erases_octonion_bracketing_witness" => oct_witness["density_gap_fro"] < TOL && oct_witness["spinor_gap"] > TOL,
        "quaternion_subalgebra_collapses" => h_control["spinor_gap"] < TOL && h_control["product_gap"] < TOL,
        "octonion_alternativity_repeated_input_collapses" => alt_control["spinor_gap"] < TOL && alt_control["product_gap"] < TOL,
        "raw_matrix_composition_associative_control" => matrix_gap < TOL,
        "density_sign_erasure_control" => phase_control["pass"],
    )
    result = Dict{String,Any}(
        "schema" => "three_spinor_associator_lifted_bracketing_julia_v1",
        "object_id" => OBJECT_ID,
        "backend" => "julia",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "elapsed_seconds" => time() - started,
        "source_path" => @__FILE__,
        "source_sha256" => file_sha256(@__FILE__),
        "peer_source_path" => JAX_SOURCE_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "peer_metadata" => Dict{String,Any}(
            "backend" => "jax",
            "source_path" => JAX_SOURCE_PATH,
            "source_sha256" => file_sha256(JAX_SOURCE_PATH),
            "result_path" => JAX_RESULT_PATH,
            "result_sha256" => file_sha256(JAX_RESULT_PATH),
        ),
        "claim_ceiling" => "Julia mirror only for the formal scout; no final M(C), PEPS3D admission, Axis0, physics, engine, or bridge promotion.",
        "root_constraints" => Dict(
            "F01" => "finite 3-site spinor cell, finite basis probes, finite operation triples",
            "N01" => "bracketing/order is a measured finite operation readout; associativity is not assumed globally",
        ),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "witnesses" => Dict(
            "octonion" => oct_witness,
            "quaternion_control" => h_control,
            "alternativity_control" => alt_control,
            "density_phase_erasure_control" => phase_control,
        ),
        "all_pass" => all(Bool(v) for v in values(shared_booleans)),
        "result_path" => RESULT_PATH,
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println(JSON.json(Dict(
        "all_pass" => result["all_pass"],
        "octonion_spinor_gap" => shared_scalars["octonion_spinor_gap"],
        "octonion_density_gap_fro" => shared_scalars["octonion_density_gap_fro"],
        "result_path" => RESULT_PATH,
    )))
end

main()
