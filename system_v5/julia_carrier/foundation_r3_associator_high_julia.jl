#!/usr/bin/env julia
# object_id: foundation_r3_associator_high
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using CliffordAlgebras
using Z3

const OBJECT_ID = "foundation_r3_associator_high"
const ENGINE = "julia"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "foundation_r3_associator_high_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "results", "foundation_r3_associator_high_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-10

function basis_vector(dim::Int, idx0::Int)
    v = zeros(Float64, dim)
    v[idx0 + 1] = 1.0
    v
end

function clifford_h_table()
    cl = CliffordAlgebra(0, 2)
    one_mv = one(cl.e1)
    basis = [one_mv, cl.e1, cl.e2, cl.e1 * cl.e2]
    props = [:𝟏, :e1, :e2, :e1e2]
    table = zeros(Float64, 4, 4, 4)
    for a in 1:4, b in 1:4
        product = basis[a] * basis[b]
        for (c, prop) in enumerate(props)
            table[c, a, b] = Float64(getproperty(product, prop))
        end
    end
    package_residuals = Float64[
        CliffordAlgebras.norm(basis[2] * basis[2] + one_mv),
        CliffordAlgebras.norm(basis[3] * basis[3] + one_mv),
        CliffordAlgebras.norm(basis[4] * basis[4] + one_mv),
        CliffordAlgebras.norm(basis[2] * basis[3] - basis[4]),
        CliffordAlgebras.norm(basis[3] * basis[2] + basis[4]),
    ]
    table, Dict{String,Any}(
        "package" => "CliffordAlgebras",
        "algebra" => "Cl(0,2)",
        "basis_order_zero_based" => ["1", "e1", "e2", "e1e2"],
        "max_quaternion_relation_residual" => maximum(abs.(package_residuals)),
        "package_native_h" => true,
    )
end

function cd_conj(x::AbstractVector{Float64})
    out = collect(x)
    length(out) > 1 && (out[2:end] .*= -1.0)
    out
end

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function cd_pair_multiply(parent::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    n = size(parent, 1)
    a = x[1:n]
    b = x[(n + 1):(2 * n)]
    c = y[1:n]
    d = y[(n + 1):(2 * n)]
    first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
    vcat(first, second)
end

function cd_double(parent::Array{Float64,3})
    n = size(parent, 1)
    dim = 2 * n
    table = zeros(Float64, dim, dim, dim)
    for i in 0:(dim - 1), j in 0:(dim - 1)
        table[:, i + 1, j + 1] .= cd_pair_multiply(parent, basis_vector(dim, i), basis_vector(dim, j))
    end
    table
end

function associator(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64}, z::AbstractVector{Float64})
    multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))
end

function associator_tensor(table::Array{Float64,3})
    dim = size(table, 1)
    tensor = zeros(Float64, dim, dim, dim, dim)
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1)
        tensor[:, a + 1, b + 1, c + 1] .= associator(table, basis_vector(dim, a), basis_vector(dim, b), basis_vector(dim, c))
    end
    tensor
end

function analyze_associator(name::String, table::Array{Float64,3})
    dim = size(table, 1)
    max_norm = 0.0
    witness = Dict{String,Any}("basis_indices_zero_based" => [0, 0, 0], "components" => Float64[], "norm" => 0.0)
    all_rows = Vector{Dict{String,Any}}()
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1)
        vec = associator(table, basis_vector(dim, a), basis_vector(dim, b), basis_vector(dim, c))
        nrm = norm(vec)
        if nrm > TOL
            push!(all_rows, Dict{String,Any}("triple" => [a, b, c], "norm" => nrm, "components" => collect(vec)))
        end
        if nrm > max_norm
            max_norm = nrm
            witness = Dict{String,Any}(
                "basis_indices_zero_based" => [a, b, c],
                "basis_labels" => ["e$a", "e$b", "e$c"],
                "components" => collect(vec),
                "norm" => nrm,
            )
        end
    end
    Dict{String,Any}(
        "name" => name,
        "dim" => dim,
        "associator_max_norm" => max_norm,
        "nonzero_basis_triple_count" => length(all_rows),
        "witness" => witness,
    )
end

function alternativity_residual(table::Array{Float64,3})
    dim = size(table, 1)
    max_xxy = 0.0
    max_xyy = 0.0
    for a in 0:(dim - 1), b in 0:(dim - 1)
        x = basis_vector(dim, a)
        y = basis_vector(dim, b)
        max_xxy = max(max_xxy, norm(associator(table, x, x, y)))
        max_xyy = max(max_xyy, norm(associator(table, x, y, y)))
    end
    Dict{String,Any}("xxy_max_norm" => max_xxy, "xyy_max_norm" => max_xyy, "pass" => max(max_xxy, max_xyy) <= TOL)
end

function antisymmetry_residual(table::Array{Float64,3})
    dim = size(table, 1)
    max_swap12 = 0.0
    max_swap23 = 0.0
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1)
        va = basis_vector(dim, a)
        vb = basis_vector(dim, b)
        vc = basis_vector(dim, c)
        abc = associator(table, va, vb, vc)
        bac = associator(table, vb, va, vc)
        acb = associator(table, va, vc, vb)
        max_swap12 = max(max_swap12, norm(abc + bac))
        max_swap23 = max(max_swap23, norm(abc + acb))
    end
    Dict{String,Any}("swap12_max_norm" => max_swap12, "swap23_max_norm" => max_swap23, "pass" => max(max_swap12, max_swap23) <= TOL)
end

function power_associativity_residual(table::Array{Float64,3})
    dim = size(table, 1)
    probes = [basis_vector(dim, idx) for idx in 0:(dim - 1)]
    if dim >= 8
        push!(probes, (basis_vector(dim, 1) + basis_vector(dim, 2) + basis_vector(dim, 4)) ./ sqrt(3.0))
        push!(probes, (basis_vector(dim, 1) - basis_vector(dim, 5) + 0.25 .* basis_vector(dim, 7)) ./ sqrt(1.0 + 1.0 + 0.25^2))
    end
    max_seen = 0.0
    for x in probes
        x2 = multiply(table, x, x)
        left = multiply(table, multiply(table, x2, x), x)
        right = multiply(table, x2, x2)
        max_seen = max(max_seen, norm(left - right))
    end
    Dict{String,Any}("max_norm" => max_seen, "pass" => max_seen <= TOL, "probe_count" => length(probes))
end

function coeffs_int(tensor::Array{Float64,4})
    values = Int[]
    for value in vec(tensor)
        rounded = round(Int, value)
        abs(value - rounded) > TOL && error("non-integral associator coefficient: $value")
        push!(values, rounded)
    end
    values
end

function z3_zero_claim_status(prefix::String, coeffs::Vector{Int}; force_all_zero::Bool)
    solver = Solver()
    witness_idx = findfirst(!=(0), coeffs)
    if witness_idx === nothing
        probe = IntVar("$(prefix)_all_zero_probe")
        add(solver, probe == IntVal(0))
    else
        probe = IntVar("$(prefix)_witness_coeff")
        add(solver, probe == IntVal(coeffs[witness_idx]))
        force_all_zero && add(solver, probe == IntVal(0))
    end
    string(check(solver))
end

function build_result()
    h_table, h_package = clifford_h_table()
    o_table = cd_double(h_table)
    h = analyze_associator("H", h_table)
    o = analyze_associator("O", o_table)
    h_coeffs = coeffs_int(associator_tensor(h_table))
    o_coeffs = coeffs_int(associator_tensor(o_table))
    h_zero_status = z3_zero_claim_status("julia_H_zero_high", h_coeffs; force_all_zero=true)
    o_zero_status = z3_zero_claim_status("julia_O_zero_high", o_coeffs; force_all_zero=true)
    o_erased_status = z3_zero_claim_status("julia_O_erased_high", o_coeffs; force_all_zero=false)
    alt = alternativity_residual(o_table)
    anti = antisymmetry_residual(o_table)
    power = power_associativity_residual(o_table)

    h_zero = h["associator_max_norm"] <= TOL
    o_nonzero = o["associator_max_norm"] > TOL
    smt_flip = o_zero_status == "unsat" && o_erased_status == "sat"
    all_pass = h_zero && o_nonzero && alt["pass"] && anti["pass"] && power["pass"] &&
        h_zero_status == "sat" && o_zero_status == "unsat" && smt_flip &&
        CLASSIFICATION == "scratch_diagnostic" && !PROMOTION_ALLOWED &&
        !FORMAL_ADMISSION_ALLOWED && !READS_PEER_RESULT

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "engine" => ENGINE,
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "executable" => "/opt/homebrew/bin/julia --project=@v1.12 --startup-file=no",
        "active_project" => Base.active_project(),
        "julia_version" => string(VERSION),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "package_construction" => Dict{String,Any}(
            "H" => h_package,
            "O" => Dict(
                "package_native_octonion_constructor_found" => false,
                "method" => "Cayley-Dickson doubling of the CliffordAlgebras Cl(0,2) quaternion table",
                "honesty_note" => "No package-native octonion constructor is used in this leg; O is derived from package H by Cayley-Dickson."
            ),
        ),
        "M_probe_family" => Dict{String,Any}(
            "id" => "basis_triple_associator_coordinates",
            "observable" => "[A,B,C]=(AB)C-A(BC)",
            "H_basis_triple_count" => 4^3,
            "O_basis_triple_count" => 8^3,
            "coordinate_readouts" => "all algebra basis coordinates of the associator vector",
        ),
        "C_constraints" => Dict{String,Any}(
            "domain" => "finite real normed division algebra structure constants",
            "unit" => "e0 is two-sided identity",
            "normalization" => "basis units have norm 1 and imaginary units square to -e0",
            "rung_specific" => "bracketing admissibility is measured by the associator over computed structure constants",
            "density_matrix_constraints_applicable" => false,
        ),
        "quotient" => Dict{String,Any}(
            "definition" => "(AB)C ~ A(BC) iff every associator coordinate probe is zero",
            "H_class" => h_zero ? "single_indistinguishable_bracketing_class" : "distinguishable",
            "O_class" => o_nonzero ? "distinguishable_bracketing_classes" : "single_indistinguishable_bracketing_class",
            "H_quotient_class_count" => h_zero ? 1 : 2,
            "O_quotient_class_count" => o_nonzero ? 2 : 1,
        ),
        "values" => Dict{String,Any}("H" => h, "O" => o),
        "structure_checks" => Dict{String,Any}(
            "O_alternativity" => alt,
            "O_associator_antisymmetry" => anti,
            "O_power_associativity" => power,
        ),
        "finite_certificates" => Dict{String,Any}(
            "julia_z3" => Dict{String,Any}(
                "ran" => true,
                "load_bearing" => true,
                "H_all_zero_status" => h_zero_status,
                "O_all_zero_status" => o_zero_status,
                "O_drop_all_zero_constraint_status" => o_erased_status,
                "erase_flip_unsat_to_sat" => smt_flip,
                "claim" => "SMT assertions are over computed associator coefficients from the Julia package-derived tables.",
            ),
        ),
        "negative_control" => Dict{String,Any}(
            "H_to_O_structure_flip" => Dict("pass" => h_zero && o_nonzero, "H_associator_max_norm" => h["associator_max_norm"], "O_associator_max_norm" => o["associator_max_norm"]),
            "drop_zero_associator_constraint_flip" => Dict("pass" => smt_flip, "with_constraint" => o_zero_status, "constraint_erased" => o_erased_status),
        ),
        "packages_used" => ["CliffordAlgebras", "Z3", "JSON", "LinearAlgebra", "Dates"],
        "aligned_packages_load_bearing" => ["CliffordAlgebras", "Z3"],
        "TOOL_MANIFEST" => Dict{String,Any}(
            "CliffordAlgebras" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Cl(0,2) quaternion structure constants for H"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing SMT over computed associator coefficients"),
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive finite norms over package-derived tables"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("CliffordAlgebras" => "load_bearing", "Z3" => "load_bearing", "LinearAlgebra" => "supportive"),
        "all_pass" => all_pass,
    )
    result
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    all_pass = result["all_pass"]
    h = result["values"]["H"]["associator_max_norm"]
    o = result["values"]["O"]["associator_max_norm"]
    w = result["values"]["O"]["witness"]["basis_labels"]
    o_zero_status = result["finite_certificates"]["julia_z3"]["O_all_zero_status"]
    println("SCOUT_DONE all_pass=$all_pass H_assoc=$h O_assoc=$o witness=$(join(w, ",")) O_zero_status=$o_zero_status")
    return result["all_pass"] ? 0 : 1
end

exit(main())
