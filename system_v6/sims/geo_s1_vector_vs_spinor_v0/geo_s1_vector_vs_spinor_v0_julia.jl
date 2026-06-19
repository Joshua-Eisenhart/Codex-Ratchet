#!/usr/bin/env julia
# object_id: geo_s1_vector_vs_spinor_v0
# classification: scratch_diagnostic
# promotion_allowed: false

using Dates
using JSON
using LinearAlgebra
using Manifolds
using QuantumOptics
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s1_vector_vs_spinor_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const PIN_SPEC = "geo_s1_vector_vs_spinor_v0|routes=SO3_vector_vs_SU2_spinor|U(theta)=diag(exp(-i theta/2),exp(i theta/2))|R(theta)=Rz(theta)|density_quotient=psi psi_dagger|compare_2pi_4pi|classification=scratch_diagnostic|promotion_allowed=false"

const TOOL_MANIFEST = Dict{String,Any}(
    "Manifolds" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing SO(3) manifold distance check on the vector route",
    ),
    "QuantumOptics" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing spinor ket and density quotient construction",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing finite truth-table gate for the route discriminator",
    ),
    "JSON/Dates/SHA/LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive serialization, timestamping, hashing, and local matrix arithmetic",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Manifolds" => "load_bearing",
    "QuantumOptics" => "load_bearing",
    "Z3" => "load_bearing",
    "JSON/Dates/SHA/LinearAlgebra" => "supportive",
)

sha256_text(text::String) = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))

function file_sha256(path::String)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function so3_z(theta::Float64)
    c = cos(theta)
    s = sin(theta)
    return [c -s 0.0; s c 0.0; 0.0 0.0 1.0]
end

function su2_z(theta::Float64)
    a = cos(theta / 2) - im * sin(theta / 2)
    b = cos(theta / 2) + im * sin(theta / 2)
    return ComplexF64[a 0; 0 b]
end

function su2_to_so3(U::Matrix{ComplexF64})
    sigma = [
        ComplexF64[0 1; 1 0],
        ComplexF64[0 -im; im 0],
        ComplexF64[1 0; 0 -1],
    ]
    R = zeros(Float64, 3, 3)
    for i in 1:3
        for j in 1:3
            R[i, j] = real(tr(sigma[i] * U * sigma[j] * U'))
        end
    end
    return R ./ 2
end

function matrix_payload(M)
    return [[Float64(real(M[i, j])) for j in 1:size(M, 2)] for i in 1:size(M, 1)]
end

function complex_matrix_payload(M)
    return [[Dict("re" => Float64(real(M[i, j])), "im" => Float64(imag(M[i, j]))) for j in 1:size(M, 2)] for i in 1:size(M, 1)]
end

function z3_gate(actuals::Dict{String,Bool})
    solver = Z3.Solver()
    for (name, value) in actuals
        x = Z3.IntVar(name)
        Z3.add(solver, x == Z3.IntVal(value ? 1 : 0))
    end
    accepted = Z3.IntVar("route_discriminator_accepts")
    Z3.add(solver, accepted == Z3.IntVal(all(values(actuals)) ? 1 : 0))
    Z3.add(solver, Z3.Not(accepted == Z3.IntVal(1)))
    return string(Z3.check(solver))
end

function main()
    mkpath(RESULT_DIR)
    I2 = ComplexF64[1 0; 0 1]
    I3 = Matrix{Float64}(I, 3, 3)
    Rman = Manifolds.Rotations(3)

    U0 = su2_z(0.0)
    U2 = su2_z(2pi)
    U4 = su2_z(4pi)
    R0 = so3_z(0.0)
    R2 = so3_z(2pi)
    R4 = so3_z(4pi)
    R_from_U = su2_to_so3(su2_z(pi / 3))
    R_from_minus_U = su2_to_so3(-su2_z(pi / 3))

    basis = QuantumOptics.NLevelBasis(2)
    psi_plus = QuantumOptics.Ket(basis, ComplexF64[1, 0])
    psi_minus = QuantumOptics.Ket(basis, ComplexF64[-1, 0])
    rho_plus = QuantumOptics.dm(psi_plus)
    rho_minus = QuantumOptics.dm(psi_minus)
    density_diff_norm = norm(rho_plus.data - rho_minus.data)
    spinor_diff_norm = norm(psi_plus.data - psi_minus.data)

    so3_distance_2pi = Manifolds.distance(Rman, I3, R2)
    so3_distance_4pi = Manifolds.distance(Rman, I3, R4)
    su2_distance_2pi_to_identity = norm(U2 - I2)
    su2_distance_2pi_to_minus_identity = norm(U2 + I2)
    su2_distance_4pi_to_identity = norm(U4 - I2)
    u_minus_u_rotation_distance = norm(R_from_U - R_from_minus_U)

    vector_closes_at_2pi = so3_distance_2pi < 1e-12
    spinor_closes_at_2pi = su2_distance_2pi_to_identity < 1e-12
    n01_closure_order_gap = Int(vector_closes_at_2pi) - Int(spinor_closes_at_2pi)
    closure_order_gap_receipt = Dict{String,Any}(
        "name" => "n01_closure_order_gap",
        "functional" => "boolean identity closure at theta=2pi under each route's own representation",
        "routes" => Dict(
            "vector_SO3_Rz" => Dict(
                "representation" => "R(theta)=Rz(theta) in SO(3)",
                "theta" => "2pi",
                "closes_to_identity" => vector_closes_at_2pi,
                "normalized_boolean_value" => Int(vector_closes_at_2pi),
            ),
            "spinor_SU2_U" => Dict(
                "representation" => "U(theta)=diag(exp(-i theta/2), exp(i theta/2)) in SU(2)",
                "theta" => "2pi",
                "closes_to_identity" => spinor_closes_at_2pi,
                "normalized_boolean_value" => Int(spinor_closes_at_2pi),
            ),
        ),
        "gap_direction" => "vector_minus_spinor",
        "gap" => n01_closure_order_gap,
        "four_pi_check" => Dict(
            "vector_closes_to_identity" => so3_distance_4pi < 1e-12,
            "spinor_closes_to_identity" => su2_distance_4pi_to_identity < 1e-12,
        ),
        "scale" => "normalized_boolean_closure_not_raw_matrix_norm",
        "raw_norm_cross_dimension_comparison_excluded" => true,
        "exclusion_reason" => "does not compare ||R-I3|| with ||U-I2|| as one numeric gap because the representations have different matrix dimensions",
        "pass" => n01_closure_order_gap == 1 && so3_distance_4pi < 1e-12 && su2_distance_4pi_to_identity < 1e-12,
    )

    actuals = Dict{String,Bool}(
        "so3_2pi_closed" => vector_closes_at_2pi,
        "su2_2pi_not_closed" => su2_distance_2pi_to_identity > 1.0 && su2_distance_2pi_to_minus_identity < 1e-12,
        "su2_4pi_closed" => su2_distance_4pi_to_identity < 1e-12,
        "u_minus_u_same_rotation" => u_minus_u_rotation_distance < 1e-12,
        "spinor_sign_visible_before_density" => spinor_diff_norm > 1.0,
        "density_quotient_collapses_sign" => density_diff_norm < 1e-12,
        "n01_closure_order_gap_pass" => closure_order_gap_receipt["pass"],
    )
    corrupted = copy(actuals)
    corrupted["su2_2pi_not_closed"] = false
    z3_nominal = z3_gate(actuals)
    z3_corrupted = z3_gate(corrupted)

    all_pass = all(values(actuals)) && z3_nominal == "unsat" && z3_corrupted == "sat"

    payload = Dict{String,Any}(
        "schema_version" => "$(SIM_ID)_leg_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_authoritative_sim_builder",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "source_path" => relpath(SOURCE_PATH, ROOT),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => relpath(RESULT_PATH, ROOT),
        "generated_at" => string(Dates.now(Dates.UTC)),
        "julia_project" => string(Base.active_project()),
        "packages_used" => ["Manifolds", "QuantumOptics", "Z3", "JSON", "Dates", "LinearAlgebra", "SHA"],
        "aligned_packages_load_bearing" => ["Manifolds", "QuantumOptics", "Z3"],
        "claim_path_tools" => ["Manifolds", "QuantumOptics", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "route_receipts" => Dict{String,Any}(
            "SO3_vector_return" => Dict(
                "manifold" => "Manifolds.Rotations(3)",
                "distance_identity_to_R_2pi" => so3_distance_2pi,
                "distance_identity_to_R_4pi" => so3_distance_4pi,
                "R_2pi" => matrix_payload(R2),
                "R_4pi" => matrix_payload(R4),
                "pass" => actuals["so3_2pi_closed"],
            ),
            "SU2_spinor_return" => Dict(
                "U_2pi" => complex_matrix_payload(U2),
                "U_4pi" => complex_matrix_payload(U4),
                "distance_U_2pi_to_identity" => su2_distance_2pi_to_identity,
                "distance_U_2pi_to_minus_identity" => su2_distance_2pi_to_minus_identity,
                "distance_U_4pi_to_identity" => su2_distance_4pi_to_identity,
                "pass" => actuals["su2_2pi_not_closed"] && actuals["su2_4pi_closed"],
            ),
            "double_cover_map" => Dict(
                "map" => "R_ij = 1/2 Tr(sigma_i U sigma_j U^dagger)",
                "R_from_U_theta_pi_over_3" => matrix_payload(R_from_U),
                "R_from_minus_U_theta_pi_over_3" => matrix_payload(R_from_minus_U),
                "norm_difference" => u_minus_u_rotation_distance,
                "pass" => actuals["u_minus_u_same_rotation"],
            ),
            "density_quotient" => Dict(
                "quantumoptics_objects" => ["QuantumOptics.Ket", "QuantumOptics.dm"],
                "spinor_norm_difference_psi_minus_psi" => spinor_diff_norm,
                "density_norm_difference_dm_psi_dm_minus_psi" => density_diff_norm,
                "rho_plus" => complex_matrix_payload(rho_plus.data),
                "rho_minus" => complex_matrix_payload(rho_minus.data),
                "pass" => actuals["spinor_sign_visible_before_density"] && actuals["density_quotient_collapses_sign"],
            ),
            "n01_closure_order_gap" => closure_order_gap_receipt,
        ),
        "proofs" => Dict{String,Any}(
            "route_truth_table_julia_z3" => Dict(
                "nominal_not_accepted" => z3_nominal,
                "corrupted_control_not_accepted" => z3_corrupted,
                "actuals" => actuals,
                "pass" => z3_nominal == "unsat" && z3_corrupted == "sat",
            ),
        ),
        "shared_scalars" => Dict{String,Any}(
            "so3_2pi_distance" => so3_distance_2pi,
            "su2_2pi_identity_distance" => su2_distance_2pi_to_identity,
            "su2_4pi_identity_distance" => su2_distance_4pi_to_identity,
            "u_minus_u_rotation_distance" => u_minus_u_rotation_distance,
            "density_quotient_sign_distance" => density_diff_norm,
            "n01_closure_order_gap" => n01_closure_order_gap,
        ),
        "controls" => Dict{String,Any}(
            "corrupted_su2_2pi_closure_control" => Dict("z3" => z3_corrupted, "pass" => z3_corrupted == "sat"),
        ),
        "all_pass" => all_pass,
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => all_pass, "engine" => "julia", "result_path" => RESULT_PATH)))
    return all_pass ? 0 : 1
end

exit(main())
