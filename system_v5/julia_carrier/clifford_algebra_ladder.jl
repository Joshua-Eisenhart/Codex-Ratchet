#!/usr/bin/env julia
# object_id: clifford_algebra_ladder
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: Finite Clifford/quaternion carrier diagnostic only. No basin,
# admission, engine, Axis0, bridge, gravity, or manifold-closure claim.

using Dates
using JSON
using LinearAlgebra
using CliffordAlgebras

const OBJECT_ID = "clifford_algebra_ladder"
const RESULT_PATH = joinpath(@__DIR__, "clifford_algebra_ladder_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "clifford_algebra_ladder_jax_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6

function setprod!(table::Array{Float64,3}, a::Int, b::Int, c::Int, s::Float64)
    table[c + 1, a + 1, b + 1] = s
end

function add_identity!(table::Array{Float64,3}, dim::Int)
    for a in 0:(dim - 1)
        setprod!(table, 0, a, a, 1.0)
        setprod!(table, a, 0, a, 1.0)
    end
end

function complex_table()
    table = zeros(Float64, 2, 2, 2)
    add_identity!(table, 2)
    setprod!(table, 1, 1, 0, -1.0)
    table
end

function quaternion_table()
    table = zeros(Float64, 4, 4, 4)
    add_identity!(table, 4)
    for a in 1:3
        setprod!(table, a, a, 0, -1.0)
    end
    for (i, j, k) in [(1, 2, 3)]
        for (a, b, c, s) in [
            (i, j, k, 1.0), (j, k, i, 1.0), (k, i, j, 1.0),
            (j, i, k, -1.0), (k, j, i, -1.0), (i, k, j, -1.0),
        ]
            setprod!(table, a, b, c, s)
        end
    end
    table
end

function blade_product(mask_a::Int, mask_b::Int, signature::Vector{Int})
    sign = 1.0
    n = length(signature)
    for i in 0:(n - 1)
        if ((mask_a >> i) & 1) == 1
            for j in 0:(i - 1)
                if ((mask_b >> j) & 1) == 1
                    sign *= -1.0
                end
            end
            if ((mask_b >> i) & 1) == 1
                sign *= Float64(signature[i + 1])
            end
        end
    end
    sign, xor(mask_a, mask_b)
end

function clifford_table(signature::Vector{Int})
    dim = 2^length(signature)
    table = zeros(Float64, dim, dim, dim)
    for a in 0:(dim - 1), b in 0:(dim - 1)
        sign, c = blade_product(a, b, signature)
        setprod!(table, a, b, c, sign)
    end
    table
end

function basis(dim::Int, idx::Int; scale::Float64=1.0)
    v = zeros(Float64, dim)
    v[idx + 1] = scale
    v
end

function mv_mul(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function table_residual(table::Array{Float64,3}, subbasis::Vector{Vector{Float64}}, target::Array{Float64,3})
    max_resid = 0.0
    dim = size(table, 1)
    for a in 1:length(subbasis), b in 1:length(subbasis)
        product = mv_mul(table, subbasis[a], subbasis[b])
        expected = zeros(Float64, dim)
        for c in 1:length(subbasis)
            expected .+= target[c, a, b] .* subbasis[c]
        end
        max_resid = max(max_resid, norm(product - expected))
    end
    max_resid
end

function even_dim(signature::Vector{Int})
    n = length(signature)
    count(mask -> iseven(count_ones(UInt(mask))), 0:(2^n - 1))
end

function gamma_matrices_cl30()
    sx = ComplexF64[0 1; 1 0]
    sy = ComplexF64[0 -im; im 0]
    sz = ComplexF64[1 0; 0 -1]
    [sx, sy, sz]
end

function gamma_relation_residual(gammas::Vector{Matrix{ComplexF64}})
    ident = Matrix{ComplexF64}(I, 2, 2)
    max_resid = 0.0
    for i in 1:3, j in 1:3
        target = (i == j) ? 2.0 .* ident : zeros(ComplexF64, 2, 2)
        max_resid = max(max_resid, opnorm(gammas[i] * gammas[j] + gammas[j] * gammas[i] - target))
    end
    max_resid
end

function package_cl30_even_crosscheck()
    cl3 = CliffordAlgebra(3, 0)
    e12 = cl3.e1 * cl3.e2
    e23 = cl3.e2 * cl3.e3
    e31 = cl3.e3 * cl3.e1
    i = -e12
    j = -e23
    k = -e31
    one_mv = one(i)
    residuals = [
        Float64(CliffordAlgebras.norm(i * i + one_mv)),
        Float64(CliffordAlgebras.norm(j * j + one_mv)),
        Float64(CliffordAlgebras.norm(k * k + one_mv)),
        Float64(CliffordAlgebras.norm(i * j - k)),
        Float64(CliffordAlgebras.norm(j * k - i)),
        Float64(CliffordAlgebras.norm(k * i - j)),
    ]
    raw_orientation_residual = Float64(CliffordAlgebras.norm(e12 * e23 - e31))
    Dict{String,Any}(
        "package" => "CliffordAlgebras",
        "algebra" => "Cl(3,0)",
        "oriented_basis" => "i=-e12, j=-e23, k=-e31",
        "max_oriented_h_residual" => maximum(residuals),
        "raw_e12_e23_minus_e31_residual" => raw_orientation_residual,
        "e12_e23_equals_negative_e31" => e12 * e23 == -e31,
        "pass" => maximum(residuals) < TOL && e12 * e23 == -e31,
    )
end

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
    table_cl01 = clifford_table([-1])
    table_cl02 = clifford_table([-1, -1])
    table_cl20 = clifford_table([1, 1])
    table_cl30 = clifford_table([1, 1, 1])

    cl01_basis = [basis(2, 0), basis(2, 1)]
    cl02_basis = [basis(4, 0), basis(4, 1), basis(4, 2), basis(4, 3)]
    cl20_basis = [basis(4, 0), basis(4, 1), basis(4, 2), basis(4, 3)]
    cl30_even_oriented = [basis(8, 0), basis(8, Int(0b011), scale=-1.0), basis(8, Int(0b110), scale=-1.0), basis(8, Int(0b101))]
    cl30_even_raw_named = [basis(8, 0), basis(8, Int(0b011)), basis(8, Int(0b110)), basis(8, Int(0b101), scale=-1.0)]

    c_table = complex_table()
    h_table = quaternion_table()

    cl01_complex_resid = table_residual(table_cl01, cl01_basis, c_table)
    cl02_h_resid = table_residual(table_cl02, cl02_basis, h_table)
    cl20_wrong_h_resid = table_residual(table_cl20, cl20_basis, h_table)
    cl30_even_h_resid = table_residual(table_cl30, cl30_even_oriented, h_table)
    cl30_even_raw_h_resid = table_residual(table_cl30, cl30_even_raw_named, h_table)
    gamma_resid = gamma_relation_residual(gamma_matrices_cl30())
    package_check = package_cl30_even_crosscheck()

    dimension_rows = Dict{String,Any}(
        "Cl(0,1)" => Dict("n" => 1, "dim" => size(table_cl01, 1), "expected" => 2),
        "Cl(0,2)" => Dict("n" => 2, "dim" => size(table_cl02, 1), "expected" => 4),
        "Cl(3,0)" => Dict("n" => 3, "dim" => size(table_cl30, 1), "expected" => 8, "even_dim" => even_dim([1, 1, 1]), "expected_even_dim" => 4),
    )
    dim_max_resid = maximum(abs(Float64(row["dim"] - row["expected"])) for row in values(dimension_rows))
    even_dim_resid = abs(Float64(dimension_rows["Cl(3,0)"]["even_dim"] - dimension_rows["Cl(3,0)"]["expected_even_dim"]))

    verdicts = Dict{String,Any}(
        "cl01_is_C" => cl01_complex_resid < TOL && size(table_cl01, 1) == 2,
        "cl02_is_H" => cl02_h_resid < TOL && size(table_cl02, 1) == 4,
        "cl30_even_is_H" => cl30_even_h_resid < TOL && even_dim([1, 1, 1]) == 4,
        "clifford_even_3_is_H" => cl30_even_h_resid < TOL,
        "gamma_relations_hold" => gamma_resid < TOL,
        "dimension_pattern_holds" => dim_max_resid < TOL && even_dim_resid < TOL,
    )
    controls = Dict{String,Any}(
        "wrong_signature_cl20_not_H" => cl20_wrong_h_resid > 1.0,
        "raw_cl30_bivector_orientation_not_standard_H" => cl30_even_raw_h_resid > 1.0,
        "oriented_cl30_bivectors_match_H" => cl30_even_h_resid < TOL,
    )
    controls["control_miswired"] = !(controls["wrong_signature_cl20_not_H"] &&
                                     controls["raw_cl30_bivector_orientation_not_standard_H"] &&
                                     controls["oriented_cl30_bivectors_match_H"])
    all_verdicts = all(Bool(v) for v in values(verdicts))

    shared_scalars = Dict{String,Any}(
        "cl01.dim" => size(table_cl01, 1),
        "cl02.dim" => size(table_cl02, 1),
        "cl30.dim" => size(table_cl30, 1),
        "cl30.even_dim" => even_dim([1, 1, 1]),
        "cl01_complex_table_residual" => cl01_complex_resid,
        "cl02_quaternion_table_residual" => cl02_h_resid,
        "cl30_even_quaternion_table_residual" => cl30_even_h_resid,
        "cl30_even_raw_quaternion_table_residual" => cl30_even_raw_h_resid,
        "wrong_signature_cl20_quaternion_table_residual" => cl20_wrong_h_resid,
        "gamma_cl30_anticommutator_max_residual" => gamma_resid,
        "dimension_max_residual" => dim_max_resid,
        "even_dimension_residual" => even_dim_resid,
    )
    shared_booleans = Dict{String,Any}()
    for (key, value) in verdicts
        shared_booleans["verdict.$key"] = value
    end
    for (key, value) in controls
        isa(value, Bool) && (shared_booleans["control.$key"] = value)
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
        "claim_ceiling" => "Finite Clifford/quaternion carrier diagnostic only; no basin, admission, engine, Axis0, bridge, gravity, or manifold-closure claim.",
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "carrier_probe",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "question" => "Do the low real Clifford rungs compute C/H identities, and does Cl^0(3,0) compute the quaternion spinor-neighborhood carrier?",
        "basis_convention" => Dict{String,Any}(
            "Cl(p,q)" => "p positive generators square +1, q negative generators square -1",
            "Cl(0,2)_H_basis" => "1,e1,e2,e12 maps to 1,i,j,k",
            "Cl(3,0)_even_H_basis" => "1,-e12,-e23,-e31 maps to 1,i,j,k; raw e12,e23,e31 has the opposite handed product and is recorded as a control",
        ),
        "dimension_rows" => dimension_rows,
        "gamma_representation" => "Pauli matrices sigma_x, sigma_y, sigma_z over C^2; {gamma_i,gamma_j}=2 delta_ij I",
        "bott_period_8_reference_data" => Dict{String,Any}(
            "status" => "reference_data_only_not_a_verdict",
            "low_cases" => Dict("Cl(0,1)" => "C", "Cl(0,2)" => "H", "Cl^0(3,0)" => "H"),
        ),
        "tool_manifest" => Dict{String,Any}(
            "Julia" => "load_bearing explicit finite Clifford blade multiplication and table checks",
            "LinearAlgebra" => "load_bearing norms, operator norms, gamma relation residuals",
            "CliffordAlgebras" => "load_bearing Julia-only independent Cl(3,0) even-bivector cross-check",
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
        "julia_cliffordalgebras_crosscheck" => package_check,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "plain_sentence" => "The computed low Clifford rungs match C and H, and the oriented even bivectors of Cl(3,0) match the quaternion table; this is a scratch carrier diagnostic only.",
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["stop_condition_fired"] = controls["control_miswired"] || !all_verdicts || !Bool(package_check["pass"]) || result["parity"]["stop_condition_fired"]
    result
end

function print_summary(result::Dict{String,Any})
    s = result["shared_scalars"]
    println("clifford_algebra_ladder - Julia full sim")
    println("classification: ", result["classification"], " | promotion_allowed: ", result["promotion_allowed"], " | formal_admission_allowed: ", result["formal_admission_allowed"])
    println("cl01_is_C=", result["verdicts"]["cl01_is_C"],
        " residual=", s["cl01_complex_table_residual"], " dim=", s["cl01.dim"])
    println("cl02_is_H=", result["verdicts"]["cl02_is_H"],
        " residual=", s["cl02_quaternion_table_residual"], " dim=", s["cl02.dim"])
    println("clifford_even_3_is_H=", result["verdicts"]["clifford_even_3_is_H"],
        " residual=", s["cl30_even_quaternion_table_residual"],
        " raw_orientation_residual=", s["cl30_even_raw_quaternion_table_residual"])
    println("gamma_relations_hold=", result["verdicts"]["gamma_relations_hold"],
        " gamma_residual=", s["gamma_cl30_anticommutator_max_residual"])
    println("wrong_signature_control_ok=", result["controls"]["wrong_signature_cl20_not_H"],
        " wrong_signature_residual=", s["wrong_signature_cl20_quaternion_table_residual"])
    println("controls=", JSON.json(result["controls"]))
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
    println("STOP: clifford_algebra_ladder control/verdict/parity stop condition fired.")
    exit(2)
end
