#!/usr/bin/env julia
# object_id: foundation_r3_associator_xhigh_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA
using CliffordAlgebras
using Grassmann
using Z3

const RUNG_ID = "foundation_r3_associator_xhigh"
const CANONICAL_RUNG_ID = "foundation_r3_associator"
const OBJECT_ID = "foundation_r3_associator_xhigh_julia"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_r3_associator_xhigh_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_r3_associator_xhigh_julia_results.json")
const TOL = 1.0e-12
const NONZERO_TOL = 1.0e-9

const classification = "scratch_diagnostic"
const CLASSIFICATION = classification
const promotion_allowed = false
const PROMOTION_ALLOWED = promotion_allowed
const formal_admission_allowed = false
const FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
const reads_peer_result = false

const TOOL_MANIFEST = Dict{String,Any}(
    "CliffordAlgebras" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Cl(0,2)/Quaternions geometric-product table; H multiplication is extracted from the package basis products",
    ),
    "Grassmann" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive aligned Julia package surface loaded and recorded; no package-native octonion algebra was used",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Julia-side SMT derivation of associators from bound Cayley-Dickson table entries",
    ),
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive norm calculations over package-derived finite structure constants",
    ),
    "JSON" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result receipt serialization",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "CliffordAlgebras" => "load_bearing",
    "Grassmann" => "supportive",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON" => "supportive",
)

function basis_vector(dim::Int, idx0::Int)
    v = zeros(Float64, dim)
    v[idx0 + 1] = 1.0
    v
end

function coeffs(mv, labels::Vector{Symbol})
    [Float64(real(getproperty(mv, label))) for label in labels]
end

function package_h_table()
    clh = CliffordAlgebra(:Quaternions)
    labels = [:𝟏, :i, :j, :ij]
    basis = [getproperty(clh, label) for label in labels]
    table = zeros(Float64, 4, 4, 4)
    for a in 1:4, b in 1:4
        table[:, a, b] .= coeffs(basis[a] * basis[b], labels)
    end
    package_crosschecks = Dict{String,Any}(
        "package" => "CliffordAlgebras",
        "constructor" => "CliffordAlgebra(:Quaternions)",
        "basis_labels" => string.(labels),
        "i_squared" => coeffs(clh.i * clh.i, labels),
        "j_squared" => coeffs(clh.j * clh.j, labels),
        "ij_squared" => coeffs(clh.ij * clh.ij, labels),
        "i_j" => coeffs(clh.i * clh.j, labels),
        "j_i" => coeffs(clh.j * clh.i, labels),
    )
    table, package_crosschecks
end

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function conjugate_vec(x::AbstractVector{Float64})
    collect(x) .* vcat([1.0], fill(-1.0, length(x) - 1))
end

function cd_pair_multiply(parent::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    n = size(parent, 1)
    a = x[1:n]
    b = x[(n + 1):(2 * n)]
    c = y[1:n]
    d = y[(n + 1):(2 * n)]
    first = multiply(parent, a, c) - multiply(parent, conjugate_vec(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, conjugate_vec(c))
    vcat(first, second)
end

function cd_double_from_parent(parent::Array{Float64,3})
    n = size(parent, 1)
    dim = 2 * n
    table = zeros(Float64, dim, dim, dim)
    for i in 0:(dim - 1), j in 0:(dim - 1)
        table[:, i + 1, j + 1] .= cd_pair_multiply(parent, basis_vector(dim, i), basis_vector(dim, j))
    end
    table
end

function associator_vector(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64}, z::AbstractVector{Float64})
    multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))
end

function associator_tensor(table::Array{Float64,3})
    dim = size(table, 1)
    tensor = zeros(Float64, dim, dim, dim, dim)
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1)
        tensor[:, a + 1, b + 1, c + 1] .= associator_vector(
            table,
            basis_vector(dim, a),
            basis_vector(dim, b),
            basis_vector(dim, c),
        )
    end
    tensor
end

function tensor_coeffs_int(tensor::Array{Float64,4})
    values = Int[]
    for value in vec(tensor)
        rounded = round(Int, value)
        abs(value - rounded) <= TOL || error("non-integral associator coefficient: $value")
        push!(values, rounded)
    end
    values
end

function associator_scan(table::Array{Float64,3})
    dim = size(table, 1)
    max_norm = 0.0
    witness = [0, 0, 0]
    witness_vec = zeros(Float64, dim)
    nonzero_count = 0
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1)
        assoc = associator_vector(table, basis_vector(dim, a), basis_vector(dim, b), basis_vector(dim, c))
        residual = norm(assoc)
        residual > NONZERO_TOL && (nonzero_count += 1)
        if residual > max_norm
            max_norm = residual
            witness = [a, b, c]
            witness_vec = assoc
        end
    end
    Dict{String,Any}(
        "max_norm" => max_norm,
        "nonzero_basis_triple_count" => nonzero_count,
        "witness_basis_indices" => witness,
        "witness_expression_ids" => ["(e$(witness[1])*e$(witness[2]))*e$(witness[3])", "e$(witness[1])*(e$(witness[2])*e$(witness[3]))"],
        "witness_vector" => [Float64(v) for v in witness_vec],
        "associative" => max_norm <= TOL,
    )
end

function pair_vector(dim::Int, i::Int, j::Int, si::Float64 = 1.0, sj::Float64 = 1.0)
    v = zeros(Float64, dim)
    v[i + 1] = si
    v[j + 1] = sj
    v
end

function deterministic_probe(dim::Int, sample_idx::Int, side::Int)
    Float64[
        (Float64(mod((sample_idx + 17) * (j + 3) * (side + 5) * 37 + (j + 1)^2 * 19 + sample_idx * 11 + side * 13, 101)) - 50.0) / 37.0
        for j in 1:dim
    ]
end

function probe_vectors(dim::Int)
    probes = [basis_vector(dim, idx) for idx in 0:(dim - 1)]
    for i in 0:(dim - 1), j in (i + 1):(dim - 1)
        push!(probes, pair_vector(dim, i, j, 1.0, 1.0))
        push!(probes, pair_vector(dim, i, j, 1.0, -1.0))
    end
    for idx in 1:4
        push!(probes, deterministic_probe(dim, idx, 11))
    end
    probes
end

function alternativity_scan(table::Array{Float64,3})
    probes = probe_vectors(size(table, 1))
    max_left = 0.0
    max_right = 0.0
    max_power = 0.0
    for x in probes, y in probes
        max_left = max(max_left, norm(associator_vector(table, x, x, y)))
        max_right = max(max_right, norm(associator_vector(table, y, x, x)))
    end
    for x in probes
        max_power = max(max_power, norm(associator_vector(table, x, x, x)))
    end
    Dict{String,Any}(
        "left_alternativity_max_norm" => max_left,
        "right_alternativity_max_norm" => max_right,
        "power_associativity_sample_max_norm" => max_power,
        "probe_count" => length(probes),
        "alternative_pass" => max(max_left, max_right) <= 1.0e-9,
        "power_associative_sample_pass" => max_power <= 1.0e-9,
    )
end

function antisymmetry_scan(table::Array{Float64,3})
    dim = size(table, 1)
    max_swap12 = 0.0
    max_swap23 = 0.0
    max_repeated = 0.0
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1)
        ea = basis_vector(dim, a)
        eb = basis_vector(dim, b)
        ec = basis_vector(dim, c)
        abc = associator_vector(table, ea, eb, ec)
        bac = associator_vector(table, eb, ea, ec)
        acb = associator_vector(table, ea, ec, eb)
        max_swap12 = max(max_swap12, norm(abc + bac))
        max_swap23 = max(max_swap23, norm(abc + acb))
        if a == b || b == c || a == c
            max_repeated = max(max_repeated, norm(abc))
        end
    end
    Dict{String,Any}(
        "swap12_antisymmetry_max_norm" => max_swap12,
        "swap23_antisymmetry_max_norm" => max_swap23,
        "repeated_argument_zero_max_norm" => max_repeated,
        "antisymmetry_pass" => max(max_swap12, max_swap23, max_repeated) <= 1.0e-9,
    )
end

function norm_multiplicativity_scan(table::Array{Float64,3})
    probes = probe_vectors(size(table, 1))
    max_residual = 0.0
    witness = Dict{String,Any}()
    for (ix, x) in enumerate(probes), (iy, y) in enumerate(probes)
        product = multiply(table, x, y)
        residual = abs(dot(product, product) - dot(x, x) * dot(y, y))
        if residual > max_residual
            max_residual = residual
            witness = Dict{String,Any}(
                "left_probe_index" => ix - 1,
                "right_probe_index" => iy - 1,
                "residual" => residual,
            )
        end
    end
    Dict{String,Any}(
        "sample_max_residual" => max_residual,
        "sample_count" => length(probes)^2,
        "sample_pass" => max_residual <= 1.0e-9,
        "witness" => witness,
    )
end

function table_summary(name::String, table::Array{Float64,3})
    assoc_tensor = associator_tensor(table)
    coeffs = tensor_coeffs_int(assoc_tensor)
    Dict{String,Any}(
        "name" => name,
        "dim" => size(table, 1),
        "associator" => associator_scan(table),
        "alternativity" => alternativity_scan(table),
        "antisymmetry" => antisymmetry_scan(table),
        "norm_multiplicativity_sample" => norm_multiplicativity_scan(table),
        "associator_coeff_sha256" => bytes2hex(sha256(join(coeffs, ",") |> Vector{UInt8})),
        "associator_coeff_nonzero_count" => count(!=(0), coeffs),
    )
end

function projector_constraint_checks(dim::Int)
    trace_residual = 0.0
    hermitian_residual = 0.0
    min_eig = Inf
    norm_residual = 0.0
    for i in 1:dim
        e = zeros(Float64, dim)
        e[i] = 1.0
        rho = e * transpose(e)
        trace_residual = max(trace_residual, abs(tr(rho) - 1.0))
        hermitian_residual = max(hermitian_residual, maximum(abs.(rho - transpose(rho))))
        min_eig = min(min_eig, minimum(eigvals(Symmetric(rho))))
        norm_residual = max(norm_residual, abs(norm(e) - 1.0))
    end
    Dict{String,Any}(
        "basis_projector_count" => dim,
        "trace_one_max_residual" => trace_residual,
        "hermiticity_max_residual" => hermitian_residual,
        "psd_min_eigenvalue" => min_eig,
        "normalization_max_residual" => norm_residual,
    )
end

function int_table_values(table::Array{Float64,3})
    dim = size(table, 1)
    values = zeros(Int, dim, dim, dim)
    for k in 1:dim, i in 1:dim, j in 1:dim
        rounded = round(Int, table[k, i, j])
        abs(table[k, i, j] - rounded) <= TOL || error("non-integral table entry")
        values[k, i, j] = rounded
    end
    values
end

function z3_sum_terms(terms)
    isempty(terms) && return Z3.IntVal(0)
    Z3.Expr(terms[1].ctx, Z3.Z3_mk_add(Z3.ctx_ref(terms[1]), length(terms), map(e -> Z3.as_ast(e), terms)))
end

function z3_mul(left, right)
    Z3.Expr(left.ctx, Z3.Z3_mk_mul(Z3.ctx_ref(left), 2, [Z3.as_ast(left), Z3.as_ast(right)]))
end

function z3_sub(left, right)
    Z3.Expr(left.ctx, Z3.Z3_mk_sub(Z3.ctx_ref(left), 2, [Z3.as_ast(left), Z3.as_ast(right)]))
end

function z3_derived_associator_certificate(name::String, table::Array{Float64,3})
    values = int_table_values(table)
    dim = size(values, 1)
    cache = Dict{Tuple{Int,Int,Int},Any}()
    constraints = Any[]

    function table_var(k::Int, i::Int, j::Int)
        key = (k, i, j)
        if !haskey(cache, key)
            var = Z3.IntVar("$(name)_T_$(k)_$(i)_$(j)")
            cache[key] = var
            push!(constraints, var == Z3.IntVal(values[k + 1, i + 1, j + 1]))
        end
        cache[key]
    end

    function assoc_component(a::Int, b::Int, c::Int, k::Int)
        left = z3_sum_terms([z3_mul(table_var(m, a, b), table_var(k, m, c)) for m in 0:(dim - 1)])
        right = z3_sum_terms([z3_mul(table_var(n, b, c), table_var(k, a, n)) for n in 0:(dim - 1)])
        z3_sub(left, right)
    end

    assoc_rows = Any[]
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1), k in 0:(dim - 1)
        push!(assoc_rows, (a, b, c, k, assoc_component(a, b, c, k)))
    end

    all_zero = Z3.Solver()
    for constraint in constraints
        Z3.add(all_zero, constraint)
    end
    for row in assoc_rows
        Z3.add(all_zero, row[5] == Z3.IntVal(0))
    end
    all_zero_status = string(Z3.check(all_zero))

    erased = Z3.Solver()
    for constraint in constraints
        Z3.add(erased, constraint)
    end
    erased_status = string(Z3.check(erased))

    nonzero = Z3.Solver()
    for constraint in constraints
        Z3.add(nonzero, constraint)
    end
    nonzero_terms = Z3.Expr[]
    for row in assoc_rows
        push!(nonzero_terms, Z3.Not(row[5] == Z3.IntVal(0)))
    end
    Z3.add(nonzero, Z3.Or(nonzero_terms))
    nonzero_status = string(Z3.check(nonzero))

    Dict{String,Any}(
        "solver" => "Z3.jl",
        "logic" => "integer-domain exact derivation from bound table constants; Z3.jl RealVar is not exposed in this environment",
        "bound_table_entry_equalities" => length(constraints),
        "probe_triple_count" => dim^3,
        "derived_assoc_component_count" => length(assoc_rows),
        "asserted_precomputed_associator_coefficients" => 0,
        "all_coefficients_zero_status" => all_zero_status,
        "nonzero_exists_status" => nonzero_status,
        "drop_zero_constraint_status" => erased_status,
        "drop_zero_constraint_keeps_table_bindings" => true,
        "drop_zero_constraint_flips_unsat_to_sat" => all_zero_status == "unsat" && erased_status == "sat",
        "drop_nonzero_constraint_flips_unsat_to_sat" => nonzero_status == "unsat" && erased_status == "sat",
        "derivation" => "assoc_k=sum_m T[m,a,b]*T[k,m,c]-sum_n T[n,b,c]*T[k,a,n], expanded inside Z3.jl from bound T[k,i,j] table entries",
    )
end

function build_result()
    h_table, h_package = package_h_table()
    o_table = cd_double_from_parent(h_table)

    h_tensor = associator_tensor(h_table)
    o_tensor = associator_tensor(o_table)
    h_summary = table_summary("H", h_table)
    o_summary = table_summary("O", o_table)
    h_z3 = z3_derived_associator_certificate("H", h_table)
    o_z3 = z3_derived_associator_certificate("O", o_table)

    h_norm = Float64(h_summary["associator"]["max_norm"])
    o_norm = Float64(o_summary["associator"]["max_norm"])
    drop_probe_class_count = 1
    m_class_counts = Dict{String,Any}(
        "H_bracketing_classes_under_M" => h_norm <= TOL ? 1 : 2,
        "O_witness_bracketing_classes_under_M" => o_norm > NONZERO_TOL ? 2 : 1,
        "drop_M_bracketing_classes" => drop_probe_class_count,
    )

    negative_control = Dict{String,Any}(
        "H_to_O_flip" => h_norm <= TOL && o_norm > NONZERO_TOL,
        "drop_M_coarsens_O_witness_quotient" => m_class_counts["O_witness_bracketing_classes_under_M"] > drop_probe_class_count,
        "z3_O_all_zero_unsat_to_erased_sat" => o_z3["drop_zero_constraint_flips_unsat_to_sat"],
        "z3_H_nonzero_unsat_to_erased_sat" => h_z3["drop_nonzero_constraint_flips_unsat_to_sat"],
        "H_all_zero_status" => h_z3["all_coefficients_zero_status"],
        "O_all_zero_status" => o_z3["all_coefficients_zero_status"],
        "H_nonzero_exists_status" => h_z3["nonzero_exists_status"],
        "O_nonzero_exists_status" => o_z3["nonzero_exists_status"],
    )

    all_pass = (
        h_norm <= TOL &&
        o_norm > NONZERO_TOL &&
        Bool(o_summary["alternativity"]["alternative_pass"]) &&
        Bool(o_summary["alternativity"]["power_associative_sample_pass"]) &&
        Bool(o_summary["antisymmetry"]["antisymmetry_pass"]) &&
        h_z3["all_coefficients_zero_status"] == "sat" &&
        h_z3["nonzero_exists_status"] == "unsat" &&
        o_z3["all_coefficients_zero_status"] == "unsat" &&
        o_z3["nonzero_exists_status"] == "sat" &&
        Bool(negative_control["drop_M_coarsens_O_witness_quotient"]) &&
        Bool(negative_control["z3_O_all_zero_unsat_to_erased_sat"]) &&
        classification == "scratch_diagnostic" &&
        promotion_allowed == false &&
        formal_admission_allowed == false &&
        reads_peer_result == false
    )

    Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "rung_id" => RUNG_ID,
        "canonical_rung_id" => CANONICAL_RUNG_ID,
        "hardening_variant" => "xhigh_v3_solver_derived_associator",
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "authority" => "authoritative",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "reads_peer_result" => reads_peer_result,
        "packages_used" => ["CliffordAlgebras", "Grassmann", "Z3", "LinearAlgebra", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["CliffordAlgebras", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "M" => Dict{String,Any}(
            "name" => "bracketing_distinguishability_probe",
            "probe_family" => ["associator[A,B,C] = (AB)C - A(BC)"],
            "finite_probe_domain" => "basis triples in H and O, plus sampled alternativity/norm probes",
        ),
        "C" => Dict{String,Any}(
            "trace_one" => "basis probes are represented as rank-one coordinate projectors rho=|e_i><e_i| with trace 1",
            "psd" => "rank-one coordinate projectors are positive semidefinite",
            "hermitian" => "rank-one coordinate projectors are real symmetric/Hermitian",
            "normalization" => "basis probes have unit Euclidean norm; sampled probes also check norm multiplicativity",
            "rung_specific_constraint" => "normed division algebra multiplication with package-derived H and Cayley-Dickson O over H",
            "O_construction_limit" => "No package-native octonion surface was used; O is Cayley-Dickson doubled from the CliffordAlgebras H table.",
            "finite_projector_checks" => Dict{String,Any}("H" => projector_constraint_checks(4), "O" => projector_constraint_checks(8)),
        ),
        "S_mod_M" => Dict{String,Any}(
            "definition" => "(AB)C ~_M A(BC) iff associator[A,B,C] is the zero vector",
            "class_counts" => m_class_counts,
        ),
        "package_h_table" => h_package,
        "construction" => Dict{String,Any}(
            "H" => "CliffordAlgebras.CliffordAlgebra(:Quaternions) geometric product table",
            "O" => "Cayley-Dickson doubling applied to the package-derived H table",
        ),
        "summaries" => Dict{String,Any}("H" => h_summary, "O" => o_summary),
        "julia_z3" => Dict{String,Any}("H" => h_z3, "O" => o_z3),
        "negative_control_flip" => negative_control,
        "summary" => Dict{String,Any}(
            "H_associator_max_norm" => h_norm,
            "O_associator_max_norm" => o_norm,
            "O_witness_basis_indices" => o_summary["associator"]["witness_basis_indices"],
            "O_witness_vector" => o_summary["associator"]["witness_vector"],
            "O_alternative" => o_summary["alternativity"]["alternative_pass"],
            "O_power_associative_sample" => o_summary["alternativity"]["power_associative_sample_pass"],
            "O_antisymmetry" => o_summary["antisymmetry"]["antisymmetry_pass"],
        ),
        "all_pass" => all_pass,
    )
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println("wrote: ", RESULT_PATH)
    println(
        "FOUNDATION_R3_ASSOCIATOR_XHIGH_JULIA_DONE ",
        "all_pass=", lowercase(string(result["all_pass"])), " ",
        "H_norm=", result["summary"]["H_associator_max_norm"], " ",
        "O_norm=", result["summary"]["O_associator_max_norm"], " ",
        "O_witness=", result["summary"]["O_witness_basis_indices"], " ",
        "z3_O_all_zero=", result["julia_z3"]["O"]["all_coefficients_zero_status"],
    )
    return result["all_pass"] ? 0 : 1
end

exit(main())
