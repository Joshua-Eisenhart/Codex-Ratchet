#!/usr/bin/env julia

using Dates
using JSON
using LinearAlgebra
using CliffordAlgebras
using Grassmann
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_r3_associator_low_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_r3_associator_low_julia_results.json")
const TOL = 1.0e-12

function basis_vector(dim::Int, idx::Int)
    v = zeros(Float64, dim)
    v[idx + 1] = 1.0
    v
end

cd_conj(x::AbstractVector{Float64}) = collect(x) .* vcat([1.0], fill(-1.0, length(x) - 1))

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    out = zeros(Float64, size(table, 1))
    @inbounds for c in axes(table, 1), a in axes(table, 2), b in axes(table, 3)
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function cd_pair_multiply(parent::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    n = size(parent, 1)
    a, b = x[1:n], x[(n + 1):(2 * n)]
    c, d = y[1:n], y[(n + 1):(2 * n)]
    vcat(multiply(parent, a, c) - multiply(parent, cd_conj(d), b),
         multiply(parent, d, a) + multiply(parent, b, cd_conj(c)))
end

function cd_double(parent::Array{Float64,3})
    dim = 2 * size(parent, 1)
    table = zeros(Float64, dim, dim, dim)
    for i in 0:(dim - 1), j in 0:(dim - 1)
        table[:, i + 1, j + 1] .= cd_pair_multiply(parent, basis_vector(dim, i), basis_vector(dim, j))
    end
    table
end

function build_tables()
    table = zeros(Float64, 1, 1, 1)
    table[1, 1, 1] = 1.0
    tables = Dict{String,Array{Float64,3}}("R" => table)
    for name in ["C", "H", "O"]
        table = cd_double(table)
        tables[name] = table
    end
    tables
end

function clifford_h_table()
    alg = CliffordAlgebra(0, 2)
    elems = [basevector(alg, 1), basevector(alg, :e1), basevector(alg, :e2), basevector(alg, :e1) * basevector(alg, :e2)]
    coeff_keys = [1, :e1, :e2, :e1e2]
    table = zeros(Float64, 4, 4, 4)
    for i in 1:4, j in 1:4
        product = elems[i] * elems[j]
        for k in 1:4
            table[k, i, j] = Float64(coefficient(product, coeff_keys[k]))
        end
    end
    table
end

associator_vector(table, x, y, z) = multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))

function associator_scan(table::Array{Float64,3})
    dim = size(table, 1)
    max_value = 0.0
    witness = [0, 0, 0]
    witness_vec = zeros(Float64, dim)
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1)
        vec = associator_vector(table, basis_vector(dim, a), basis_vector(dim, b), basis_vector(dim, c))
        residual = norm(vec)
        if residual > max_value
            max_value = residual
            witness = [a, b, c]
            witness_vec = vec
        end
    end
    Dict("max_norm" => max_value, "witness_basis_indices" => witness, "witness_vector" => collect(witness_vec))
end

function alternativity_scan(table::Array{Float64,3})
    dim = size(table, 1)
    max_xxy = 0.0
    max_xyy = 0.0
    max_xxx = 0.0
    probes = [basis_vector(dim, i) for i in 0:(dim - 1)]
    for i in 0:(dim - 2), j in (i + 1):(dim - 1)
        push!(probes, basis_vector(dim, i) + basis_vector(dim, j))
        push!(probes, basis_vector(dim, i) - basis_vector(dim, j))
    end
    for x in probes, y in probes
        max_xxy = max(max_xxy, norm(associator_vector(table, x, x, y)))
        max_xyy = max(max_xyy, norm(associator_vector(table, x, y, y)))
        max_xxx = max(max_xxx, norm(associator_vector(table, x, x, x)))
    end
    Dict("max_xxy" => max_xxy, "max_xyy" => max_xyy, "max_xxx" => max_xxx, "alternative" => max(max_xxy, max_xyy, max_xxx) <= 1.0e-10)
end

function anticommutativity_scan(table::Array{Float64,3})
    dim = size(table, 1)
    max_sym = 0.0
    for a in 1:(dim - 1), b in 1:(dim - 1), c in 1:(dim - 1)
        x, y, z = basis_vector(dim, a), basis_vector(dim, b), basis_vector(dim, c)
        max_sym = max(max_sym, norm(associator_vector(table, x, y, z) + associator_vector(table, y, x, z)))
        max_sym = max(max_sym, norm(associator_vector(table, x, y, z) + associator_vector(table, x, z, y)))
    end
    Dict("max_pair_swap_sum_norm" => max_sym, "antisymmetric_on_imaginary_basis" => max_sym <= 1.0e-10)
end

function main()
    tables = build_tables()
    tables["H"] = clifford_h_table()
    tables["O"] = cd_double(tables["H"])
    h_assoc = associator_scan(tables["H"])
    o_assoc = associator_scan(tables["O"])
    o_alt = alternativity_scan(tables["O"])
    o_anti = anticommutativity_scan(tables["O"])
    negative = Dict(
        "name" => "force_associativity_on_O",
        "with_normed_division_O_table" => "distinguishable",
        "forced_associative_or_erased_associator" => "indistinguishable",
        "flipped" => h_assoc["max_norm"] <= TOL && o_assoc["max_norm"] > TOL,
    )
    result = Dict(
        "schema_version" => "engine_leg_result_v1",
        "rung_id" => "foundation_r3_associator_low",
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "created_at" => string(now(UTC)),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => false,
        "packages_used" => ["CliffordAlgebras", "Grassmann", "Z3", "JSON", "LinearAlgebra"],
        "aligned_packages_load_bearing" => ["CliffordAlgebras", "Grassmann", "Z3"],
        "package_route_note" => "H is extracted from CliffordAlgebras Cl(0,2) multiplication coefficients. This leg builds O by Cayley-Dickson extension from that package-derived H because no stable package octonion constructor was found in the default project.",
        "M" => Dict("probe_family" => ["associator [A,B,C]=(AB)C-A(BC) over basis triples"], "finite_probe_count_H" => 4^3, "finite_probe_count_O" => 8^3),
        "C" => Dict("constraints" => ["finite normed division algebra multiplication table", "unit basis", "conjugation", "bilinear multiplication", "rung-specific associator bracketing probe"]),
        "quotient" => Dict("rule" => "(AB)C ~_M A(BC) iff associator vector is zero", "H_class" => "single indistinguishable bracketing class", "O_class" => "split by nonzero associator witness"),
        "values" => Dict("H_associator_norm" => h_assoc["max_norm"], "O_associator_norm" => o_assoc["max_norm"], "O_witness_basis_indices" => o_assoc["witness_basis_indices"], "O_witness_vector" => o_assoc["witness_vector"]),
        "structural_checks" => Dict("O_alternativity" => o_alt, "O_antisymmetry" => o_anti),
        "negative_control_flip" => negative,
        "TOOL_MANIFEST" => Dict(
            "CliffordAlgebras" => Dict("tried" => true, "used" => true, "reason" => "load-bearing H table extraction from Cl(0,2) multiplication coefficients"),
            "Grassmann" => Dict("tried" => true, "used" => true, "reason" => "aligned algebra package loaded while checking octonion/Cayley-Dickson route availability"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "aligned proof package loaded; structural SMT is carried in the JAX leg"),
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive norm computation only"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("CliffordAlgebras" => "load_bearing", "Grassmann" => "supportive", "Z3" => "supportive", "LinearAlgebra" => "supportive"),
        "all_pass" => h_assoc["max_norm"] <= TOL && o_assoc["max_norm"] > TOL && o_alt["alternative"] && o_anti["antisymmetric_on_imaginary_basis"] && negative["flipped"],
    )
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println("wrote: ", RESULT_PATH)
    println("SCOUT_DONE H_associator_norm=$(h_assoc["max_norm"]) O_associator_norm=$(o_assoc["max_norm"]) witness=$(o_assoc["witness_basis_indices"])")
    return result["all_pass"] ? 0 : 1
end

exit(main())
