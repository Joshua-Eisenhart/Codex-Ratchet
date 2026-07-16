#!/usr/bin/env julia
# object_id: canon_algebra_artifact_v1
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using JSON3
using LinearAlgebra
using Octonions
using Pkg
using Quaternions
using SHA
using Z3

const ROOT = abspath(joinpath(@__DIR__, "..", ".."))
const SOURCE_PATH = abspath(@__FILE__)
const ARTIFACT_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "artifacts", "algebra_structure_constants_v1.json")
const RESULT_PATH = joinpath(ROOT, "system_v5", "ops", "formal_scouts", "results", "canon_algebra_artifact_v1_results.json")
const TABLE_VERSION = "algebra_structure_constants_v1"
const OBJECT_ID = "canon_algebra_artifact_v1"
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false

const REQUESTED_DEPS = [
    "QuantumOptics",
    "QuantumToolbox",
    "Yao",
    "CliffordAlgebras",
    "Grassmann",
    "QuantumClifford",
    "Octonions",
    "Quaternions",
    "Manifolds",
    "Attractors",
    "DynamicalSystems",
    "ChaosTools",
    "ITensors",
    "ITensorMPS",
    "Symbolics",
    "Z3",
    "Graphs",
    "StaticArrays",
    "DLPack",
    "PythonCall",
    "JSON",
    "JSON3",
    "Dates",
    "SHA",
    "LinearAlgebra",
]

function utc_now()
    Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
end

function sha256_file(path::AbstractString)
    bytes2hex(sha256(read(path)))
end

function sha256_text(text::AbstractString)
    bytes2hex(sha256(Vector{UInt8}(codeunits(text))))
end

function quaternion_basis()
    [
        Quaternion(1, 0, 0, 0),
        Quaternion(0, 1, 0, 0),
        Quaternion(0, 0, 1, 0),
        Quaternion(0, 0, 0, 1),
    ]
end

function octonion_basis()
    [
        Octonion(1, 0, 0, 0, 0, 0, 0, 0),
        Octonion(0, 1, 0, 0, 0, 0, 0, 0),
        Octonion(0, 0, 1, 0, 0, 0, 0, 0),
        Octonion(0, 0, 0, 1, 0, 0, 0, 0),
        Octonion(0, 0, 0, 0, 1, 0, 0, 0),
        Octonion(0, 0, 0, 0, 0, 1, 0, 0),
        Octonion(0, 0, 0, 0, 0, 0, 1, 0),
        Octonion(0, 0, 0, 0, 0, 0, 0, 1),
    ]
end

function components(x, props::Vector{Symbol})
    [Int(getproperty(x, prop)) for prop in props]
end

function table_from_library(basis::Vector, props::Vector{Symbol})
    dim = length(basis)
    table = zeros(Int, dim, dim, dim)
    for i in 1:dim, j in 1:dim
        product = basis[i] * basis[j]
        table[:, i, j] .= components(product, props)
    end
    table
end

function nested_C(table::Array{Int,3})
    dim = size(table, 1)
    [[[table[k, i, j] for j in 1:dim] for i in 1:dim] for k in 1:dim]
end

function zadd(args::Vector{Z3.Expr}, ctx::Z3.Context)
    isempty(args) && return IntVal(0, ctx)
    length(args) == 1 && return args[1]
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_add(Z3.ref(ctx), Cuint(length(args)), map(Z3.as_ast, args)))
end

function zmul(args::Vector{Z3.Expr}, ctx::Z3.Context)
    isempty(args) && return IntVal(1, ctx)
    length(args) == 1 && return args[1]
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_mul(Z3.ref(ctx), Cuint(length(args)), map(Z3.as_ast, args)))
end

function zsub(a::Z3.Expr, b::Z3.Expr, ctx::Z3.Context)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_sub(Z3.ref(ctx), Cuint(2), map(Z3.as_ast, [a, b])))
end

function neq_zero(e::Z3.Expr, ctx::Z3.Context)
    Not(e == IntVal(0, ctx))
end

function nonzero_vector(v::Vector{Z3.Expr}, ctx::Z3.Context)
    Or([neq_zero(e, ctx) for e in v])
end

function solver_with_bound_C(table::Array{Int,3}, prefix::String)
    dim = size(table, 1)
    ctx = Context()
    solver = Solver(ctx)
    C = Array{Z3.Expr,3}(undef, dim, dim, dim)
    for k in 1:dim, i in 1:dim, j in 1:dim
        C[k, i, j] = IntVar("$(prefix)_C_$(k - 1)_$(i - 1)_$(j - 1)", ctx)
        add(solver, C[k, i, j] == IntVal(table[k, i, j], ctx))
    end
    ctx, solver, C
end

function basis_product(C::Array{Z3.Expr,3}, i::Int, j::Int)
    [C[k, i, j] for k in 1:size(C, 1)]
end

function product_right_basis(C::Array{Z3.Expr,3}, x::Vector{Z3.Expr}, j::Int, ctx::Z3.Context)
    dim = size(C, 1)
    [zadd([zmul([C[k, i, j], x[i]], ctx) for i in 1:dim], ctx) for k in 1:dim]
end

function product_left_basis(C::Array{Z3.Expr,3}, i::Int, y::Vector{Z3.Expr}, ctx::Z3.Context)
    dim = size(C, 1)
    [zadd([zmul([C[k, i, j], y[j]], ctx) for j in 1:dim], ctx) for k in 1:dim]
end

function associator_basis(C::Array{Z3.Expr,3}, a::Int, b::Int, c::Int, ctx::Z3.Context)
    ab = basis_product(C, a, b)
    bc = basis_product(C, b, c)
    left = product_right_basis(C, ab, c, ctx)
    right = product_left_basis(C, a, bc, ctx)
    [zsub(left[k], right[k], ctx) for k in 1:size(C, 1)]
end

function concrete_mul(table::Array{Int,3}, x::Vector{Int}, y::Vector{Int})
    dim = size(table, 1)
    out = zeros(Int, dim)
    for k in 1:dim, i in 1:dim, j in 1:dim
        out[k] += table[k, i, j] * x[i] * y[j]
    end
    out
end

function concrete_basis(dim::Int, idx::Int)
    v = zeros(Int, dim)
    v[idx] = 1
    v
end

function concrete_assoc(table::Array{Int,3}, a::Int, b::Int, c::Int)
    dim = size(table, 1)
    ea = concrete_basis(dim, a)
    eb = concrete_basis(dim, b)
    ec = concrete_basis(dim, c)
    concrete_mul(table, concrete_mul(table, ea, eb), ec) - concrete_mul(table, ea, concrete_mul(table, eb, ec))
end

function closure_proof(table::Array{Int,3}, prefix::String)
    ctx, solver, _C = solver_with_bound_C(table, prefix)
    Dict{String,Any}(
        "status" => string(check(solver)),
        "structural" => true,
        "dim" => size(table, 1),
        "shape" => collect(size(table)),
        "basis_product_count" => size(table, 1)^2,
        "bound_structure_constant_count" => length(table),
        "meaning" => "mul(a,b)[k]=sum_ij C[k,i,j]*a[i]*b[j] returns exactly dim coordinates in the declared basis",
    )
end

function find_noncomm_witness(table::Array{Int,3}, prefix::String, labels::Vector{String})
    dim = size(table, 1)
    for i in 1:dim, j in 1:dim
        i == j && continue
        ctx, solver, C = solver_with_bound_C(table, "$(prefix)_witness_$(i)_$(j)")
        add(solver, Or([neq_zero(zsub(C[k, i, j], C[k, j, i], ctx), ctx) for k in 1:dim]))
        if string(check(solver)) == "sat"
            return Dict{String,Any}(
                "basis_indices_zero_based" => [i - 1, j - 1],
                "basis_labels" => [labels[i], labels[j]],
                "ij_minus_ji" => [table[k, i, j] - table[k, j, i] for k in 1:dim],
            )
        end
    end
    nothing
end

function noncomm_proof(table::Array{Int,3}, prefix::String, labels::Vector{String})
    dim = size(table, 1)
    ctx, solver, C = solver_with_bound_C(table, prefix)
    terms = Z3.Expr[]
    for i in 1:dim, j in 1:dim
        i == j && continue
        append!(terms, [neq_zero(zsub(C[k, i, j], C[k, j, i], ctx), ctx) for k in 1:dim])
    end
    add(solver, Or(terms))
    status = string(check(solver))
    Dict{String,Any}(
        "exists_basis_witness_status" => status,
        "witness" => status == "sat" ? find_noncomm_witness(table, prefix, labels) : nothing,
    )
end

function find_associator_witness(table::Array{Int,3}, prefix::String, labels::Vector{String})
    dim = size(table, 1)
    for a in 1:dim, b in 1:dim, c in 1:dim
        ctx, solver, C = solver_with_bound_C(table, "$(prefix)_assoc_witness_$(a)_$(b)_$(c)")
        add(solver, nonzero_vector(associator_basis(C, a, b, c, ctx), ctx))
        if string(check(solver)) == "sat"
            return Dict{String,Any}(
                "basis_indices_zero_based" => [a - 1, b - 1, c - 1],
                "basis_labels" => [labels[a], labels[b], labels[c]],
                "associator_components" => concrete_assoc(table, a, b, c),
            )
        end
    end
    nothing
end

function associator_existence_proof(table::Array{Int,3}, prefix::String, labels::Vector{String})
    dim = size(table, 1)
    ctx, solver, C = solver_with_bound_C(table, prefix)
    terms = Z3.Expr[]
    for a in 1:dim, b in 1:dim, c in 1:dim
        append!(terms, [neq_zero(e, ctx) for e in associator_basis(C, a, b, c, ctx)])
    end
    add(solver, Or(terms))
    status = string(check(solver))
    Dict{String,Any}(
        "exists_nonzero_basis_associator_status" => status,
        "basis_triples_checked" => dim^3,
        "witness" => status == "sat" ? find_associator_witness(table, prefix, labels) : nothing,
    )
end

function associator_cache(C::Array{Z3.Expr,3}, ctx::Z3.Context)
    dim = size(C, 1)
    cache = Dict{Tuple{Int,Int,Int},Vector{Z3.Expr}}()
    for a in 1:dim, b in 1:dim, c in 1:dim
        cache[(a, b, c)] = associator_basis(C, a, b, c, ctx)
    end
    cache
end

function coefficient_vector(cache::Dict{Tuple{Int,Int,Int},Vector{Z3.Expr}}, keys::Vector{Tuple{Int,Int,Int}}, ctx::Z3.Context)
    dim = length(cache[first(keys)])
    [zadd([cache[key][k] for key in keys], ctx) for k in 1:dim]
end

function alternative_law_proof(table::Array{Int,3}, prefix::String, law::String)
    dim = size(table, 1)
    ctx, solver, C = solver_with_bound_C(table, prefix)
    cache = associator_cache(C, ctx)
    terms = Z3.Expr[]
    for a in 1:dim, b in a:dim, c in 1:dim
        keys = if law == "left"
            a == b ? [(a, a, c)] : [(a, b, c), (b, a, c)]
        elseif law == "right"
            a == b ? [(c, a, a)] : [(c, a, b), (c, b, a)]
        elseif law == "flexible"
            a == b ? [(a, c, a)] : [(a, c, b), (b, c, a)]
        else
            error("unknown alternative/flexible law: $law")
        end
        append!(terms, [neq_zero(e, ctx) for e in coefficient_vector(cache, keys, ctx)])
    end
    add(solver, Or(terms))
    Dict{String,Any}(
        "violation_status" => string(check(solver)),
        "coefficient_rows_checked" => div(dim * (dim + 1), 2) * dim,
        "basis_component_coefficients_checked" => div(dim * (dim + 1), 2) * dim * dim,
        "method" => "Z3 checks finite coefficient rows of the multilinear associator polynomial derived from bound C[k,i,j]",
    )
end

function direct_dep_versions()
    deps = Pkg.dependencies()
    by_name = Dict{String,Any}()
    for (_uuid, info) in deps
        if getproperty(info, :is_direct_dep)
            version = getproperty(info, :version)
            by_name[getproperty(info, :name)] = isnothing(version) ? "stdlib" : string(version)
        end
    end
    by_name
end

function build_algebra_record(name::String, table::Array{Int,3}, labels::Vector{String}, proof_tag::String)
    Dict{String,Any}(
        "algebra" => name,
        "dim" => size(table, 1),
        "table_version" => TABLE_VERSION,
        "C" => nested_C(table),
        "basis_labels" => labels,
        "bracket_convention" => "left",
        "proof_tag" => proof_tag,
        "shape" => collect(size(table)),
    )
end

function main()
    mkpath(dirname(ARTIFACT_PATH))
    mkpath(dirname(RESULT_PATH))

    q_labels = ["1", "i", "j", "k"]
    o_labels = ["1", "e1", "e2", "e3", "e4", "e5", "e6", "e7"]
    q_table = table_from_library(quaternion_basis(), [:s, :v1, :v2, :v3])
    o_table = table_from_library(octonion_basis(), [:s, :v1, :v2, :v3, :v4, :v5, :v6, :v7])

    q_closure = closure_proof(q_table, "q_closure")
    o_closure = closure_proof(o_table, "o_closure")
    q_noncomm = noncomm_proof(q_table, "q_noncomm", q_labels)
    o_noncomm = noncomm_proof(o_table, "o_noncomm", o_labels)
    q_assoc = associator_existence_proof(q_table, "q_assoc_exists", q_labels)
    o_assoc = associator_existence_proof(o_table, "o_assoc_exists", o_labels)
    o_left_alt = alternative_law_proof(o_table, "o_left_alt", "left")
    o_right_alt = alternative_law_proof(o_table, "o_right_alt", "right")
    o_flexible = alternative_law_proof(o_table, "o_flexible", "flexible")

    z3_verdicts = Dict{String,Any}(
        "quaternion_closure" => q_closure,
        "octonion_closure" => o_closure,
        "quaternion_noncommutativity" => q_noncomm,
        "octonion_noncommutativity" => o_noncomm,
        "quaternion_associative_no_nonzero_basis_associator" => q_assoc,
        "octonion_nonassociative_has_basis_associator" => o_assoc,
        "octonion_left_alternative_violation" => o_left_alt,
        "octonion_right_alternative_violation" => o_right_alt,
        "octonion_flexible_violation" => o_flexible,
    )

    proof_pass =
        q_closure["status"] == "sat" &&
        o_closure["status"] == "sat" &&
        q_noncomm["exists_basis_witness_status"] == "sat" &&
        o_noncomm["exists_basis_witness_status"] == "sat" &&
        q_assoc["exists_nonzero_basis_associator_status"] == "unsat" &&
        o_assoc["exists_nonzero_basis_associator_status"] == "sat" &&
        o_left_alt["violation_status"] == "unsat" &&
        o_right_alt["violation_status"] == "unsat" &&
        o_flexible["violation_status"] == "unsat"

    proof_tag_payload = join([
        "table_version=$(TABLE_VERSION)",
        "q_noncomm=$(q_noncomm["exists_basis_witness_status"])",
        "o_noncomm=$(o_noncomm["exists_basis_witness_status"])",
        "q_assoc_exists=$(q_assoc["exists_nonzero_basis_associator_status"])",
        "o_assoc_exists=$(o_assoc["exists_nonzero_basis_associator_status"])",
        "o_left_alt_violation=$(o_left_alt["violation_status"])",
        "o_right_alt_violation=$(o_right_alt["violation_status"])",
        "o_flexible_violation=$(o_flexible["violation_status"])",
    ], "\n")
    proof_tag = "sha256:" * sha256_text(proof_tag_payload)

    artifact = Dict{String,Any}(
        "schema_version" => "algebra_structure_constants_v1",
        "created_at" => utc_now(),
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "table_version" => TABLE_VERSION,
        "bracket_convention" => "left",
        "proof_tag" => proof_tag,
        "proof_pass" => proof_pass,
        "table_derivation" => Dict{String,Any}(
            "quaternion" => "Quaternions.jl basis products read from Quaternion(s,v1,v2,v3)",
            "octonion" => "Octonions.jl basis products read from Octonion(s,v1,v2,v3,v4,v5,v6,v7)",
        ),
        "algebras" => [
            build_algebra_record("quaternion", q_table, q_labels, proof_tag),
            build_algebra_record("octonion", o_table, o_labels, proof_tag),
        ],
        "z3_verdicts" => z3_verdicts,
    )
    open(ARTIFACT_PATH, "w") do io
        JSON.print(io, artifact, 2)
        println(io)
    end

    dep_versions = direct_dep_versions()
    pinned = [
        Dict{String,Any}("name" => dep, "version" => get(dep_versions, dep, "missing_from_active_project"))
        for dep in REQUESTED_DEPS
        if haskey(dep_versions, dep)
    ]
    dropped = [dep for dep in REQUESTED_DEPS if !haskey(dep_versions, dep)]

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "created_at" => utc_now(),
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "artifact_path" => ARTIFACT_PATH,
        "artifact_sha256" => sha256_file(ARTIFACT_PATH),
        "artifact_proof_tag" => proof_tag,
        "active_project" => Base.active_project(),
        "julia_version" => string(VERSION),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "proof_pass" => proof_pass,
        "table_shapes" => Dict{String,Any}(
            "quaternion" => collect(size(q_table)),
            "octonion" => collect(size(o_table)),
        ),
        "z3_verdicts" => z3_verdicts,
        "deps" => Dict{String,Any}(
            "requested" => REQUESTED_DEPS,
            "pinned" => pinned,
            "dropped" => dropped,
            "excluded_by_request" => ["Basins", "CVC5", "Lux"],
        ),
        "TOOL_MANIFEST" => Dict{String,Any}(
            "Quaternions" => Dict("tried" => true, "used" => true, "reason" => "load-bearing source for quaternion basis multiplication table"),
            "Octonions" => Dict("tried" => true, "used" => true, "reason" => "load-bearing source for Fano-plane octonion basis multiplication table"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite SMT proof over bound structure constants C[k,i,j]"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive artifact/result serialization"),
            "JSON3" => Dict("tried" => true, "used" => true, "reason" => "supportive project-pinned JSON dependency recorded for downstream consumers"),
            "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source, artifact, and proof-tag hashing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}(
            "Quaternions" => "load_bearing",
            "Octonions" => "load_bearing",
            "Z3" => "load_bearing",
            "JSON" => "supportive",
            "JSON3" => "supportive",
            "SHA" => "supportive",
            "LinearAlgebra" => "None",
        ),
        "divergence_log" => [
            "not_applicable: this receipt is a Julia-owned canon artifact plus Z3 proof, not a classical-baseline comparison",
        ],
        "claim_ceiling" => "scratch_diagnostic only; promotion_allowed=false; formal_admission_allowed=false",
        "GAINED" => [
            "repo-local Julia Project.toml and Manifest.toml for the carrier lane",
            "versioned quaternion and octonion structure-constant artifact derived from Quaternions.jl and Octonions.jl",
            "Z3.jl proof obligations over bound C[k,i,j] variables, including octonion SAT nonassociativity and quaternion UNSAT associator search",
        ],
        "NOT_GAINED" => [
            "no three-engine envelope",
            "no JAX/PyTorch consumer implementation",
            "no formal admission or canonical promotion beyond this pinned data artifact receipt",
        ],
        "CEILING" => "classification=scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false",
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end

    println(JSON.json(Dict(
        "ok" => proof_pass,
        "artifact_path" => ARTIFACT_PATH,
        "result_path" => RESULT_PATH,
        "proof_tag" => proof_tag,
    )))
    return proof_pass ? 0 : 1
end

if abspath(PROGRAM_FILE) == SOURCE_PATH
    exit(main())
end
