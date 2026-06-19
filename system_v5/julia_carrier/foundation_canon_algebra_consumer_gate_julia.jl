#!/usr/bin/env julia
# object_id: foundation_canon_algebra_consumer_gate_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using SHA
using Z3

const ROOT = abspath(joinpath(@__DIR__, "..", ".."))
const SOURCE_PATH = abspath(@__FILE__)
const RESULT_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "results", "foundation_canon_algebra_consumer_gate_julia_results.json")
const ARTIFACT_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "artifacts", "algebra_structure_constants_v1.json")
const OBJECT_ID = "foundation_canon_algebra_consumer_gate_julia"
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const EXPECTED_PROOF_TAG = "sha256:a9470fc299d39917a791bba0144d3e526866ad217b90fac1a6622b25d2c4652a"
const TOL = 1.0e-12

function utc_now()
    Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
end

sha256_file(path::AbstractString) = bytes2hex(sha256(read(path)))

function algebra_record(artifact, name::String)
    for record in artifact["algebras"]
        if record["algebra"] == name
            return record
        end
    end
    error("missing algebra record: $(name)")
end

function table_from_record(record)
    nested = record["C"]
    dim = length(nested)
    table = zeros(Int, dim, dim, dim)
    for k in 1:dim, i in 1:dim, j in 1:dim
        table[k, i, j] = Int(nested[k][i][j])
    end
    table
end

function basis_vector(dim::Int, idx::Int)
    v = zeros(Int, dim)
    v[idx] = 1
    v
end

function mul(table::Array{Int,3}, x::Vector{Int}, y::Vector{Int})
    dim = size(table, 1)
    out = zeros(Int, dim)
    @inbounds for k in 1:dim, i in 1:dim, j in 1:dim
        out[k] += table[k, i, j] * x[i] * y[j]
    end
    out
end

function associator_vector(table::Array{Int,3}, a::Int, b::Int, c::Int)
    dim = size(table, 1)
    av = basis_vector(dim, a)
    bv = basis_vector(dim, b)
    cv = basis_vector(dim, c)
    mul(table, mul(table, av, bv), cv) - mul(table, av, mul(table, bv, cv))
end

function associator_norm_map(table::Array{Int,3})
    dim = size(table, 1)
    entries = Vector{Dict{String,Any}}()
    nonzero = 0
    max_norm = 0.0
    for a in 1:dim, b in 1:dim, c in 1:dim
        assoc = associator_vector(table, a, b, c)
        norm = sqrt(float(sum(x * x for x in assoc)))
        max_norm = max(max_norm, norm)
        if norm > TOL
            nonzero += 1
        end
        push!(entries, Dict{String,Any}("triple" => [a - 1, b - 1, c - 1], "norm" => norm))
    end
    Dict{String,Any}(
        "entries" => entries,
        "entry_count" => length(entries),
        "nonzero_count_gt_tol" => nonzero,
        "zero_count_le_tol" => length(entries) - nonzero,
        "max_norm" => max_norm,
        "tol" => TOL,
        "implementation" => "Julia native loops over basis triples with mul(table,x,y)",
    )
end

function first_nonzero_triple(map_payload)
    for entry in map_payload["entries"]
        if Float64(entry["norm"]) > TOL
            return Vector{Int}(entry["triple"])
        end
    end
    error("octonion map has no nonzero associator triple")
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

neq_zero(e::Z3.Expr, ctx::Z3.Context) = Not(e == IntVal(0, ctx))

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

function basis_expr(dim::Int, idx::Int, ctx::Z3.Context)
    [i == idx ? IntVal(1, ctx) : IntVal(0, ctx) for i in 1:dim]
end

function z3_mul(C::Array{Z3.Expr,3}, x::Vector{Z3.Expr}, y::Vector{Z3.Expr}, ctx::Z3.Context)
    dim = size(C, 1)
    out = Z3.Expr[]
    for k in 1:dim
        terms = Z3.Expr[]
        for i in 1:dim, j in 1:dim
            push!(terms, zmul([C[k, i, j], x[i], y[j]], ctx))
        end
        push!(out, zadd(terms, ctx))
    end
    out
end

function z3_associator(C::Array{Z3.Expr,3}, a::Int, b::Int, c::Int, ctx::Z3.Context)
    dim = size(C, 1)
    av = basis_expr(dim, a, ctx)
    bv = basis_expr(dim, b, ctx)
    cv = basis_expr(dim, c, ctx)
    left = z3_mul(C, z3_mul(C, av, bv, ctx), cv, ctx)
    right = z3_mul(C, av, z3_mul(C, bv, cv, ctx), ctx)
    [zsub(left[k], right[k], ctx) for k in 1:dim]
end

function z3_fixed_nonzero(table::Array{Int,3}, prefix::String, triple0::Vector{Int})
    ctx, solver, C = solver_with_bound_C(table, prefix)
    assoc = z3_associator(C, triple0[1] + 1, triple0[2] + 1, triple0[3] + 1, ctx)
    add(solver, Or([neq_zero(e, ctx) for e in assoc]))
    Dict{String,Any}(
        "solver" => "Z3.jl",
        "verdict" => string(check(solver)),
        "derive_in_solver" => true,
        "bound_structure_constant_count" => length(table),
        "triple_indices_zero_based" => triple0,
        "asserted_shape" => "exists k: associator(C,e_a,e_b,e_c)[k] != 0",
    )
end

function z3_no_basis_associator(table::Array{Int,3}, prefix::String)
    dim = size(table, 1)
    ctx, solver, C = solver_with_bound_C(table, prefix)
    terms = Z3.Expr[]
    for a in 1:dim, b in 1:dim, c in 1:dim
        append!(terms, [neq_zero(e, ctx) for e in z3_associator(C, a, b, c, ctx)])
    end
    add(solver, Or(terms))
    Dict{String,Any}(
        "solver" => "Z3.jl",
        "verdict" => string(check(solver)),
        "derive_in_solver" => true,
        "basis_triples_checked" => dim^3,
        "bound_structure_constant_count" => length(table),
        "asserted_shape" => "exists basis triple and k: associator(C,e_a,e_b,e_c)[k] != 0",
    )
end

function tool_call(tool::String, api_surface::String, input_object, output_object, positive_case, negative_control, boundary_case, demotion_condition)
    Dict{String,Any}(
        "tool" => tool,
        "api_surface" => api_surface,
        "input_object" => input_object,
        "output_object" => output_object,
        "positive_case" => positive_case,
        "negative_control" => negative_control,
        "boundary_case" => boundary_case,
        "demotion_condition" => demotion_condition,
    )
end

function main()
    mkpath(dirname(RESULT_PATH))
    artifact = JSON.parsefile(ARTIFACT_PATH)
    artifact_sha = sha256_file(ARTIFACT_PATH)
    artifact_source_path = String(artifact["source_path"])
    artifact_source_sha = isfile(artifact_source_path) ? sha256_file(artifact_source_path) : "missing"

    oct_record = algebra_record(artifact, "octonion")
    quat_record = algebra_record(artifact, "quaternion")
    oct_table = table_from_record(oct_record)
    quat_table = table_from_record(quat_record)
    oct_map = associator_norm_map(oct_table)
    quat_map = associator_norm_map(quat_table)
    sampled_nonzero_triple = first_nonzero_triple(oct_map)
    oct_z3 = z3_fixed_nonzero(oct_table, "julia_octonion_sampled_nonzero", sampled_nonzero_triple)
    quat_z3 = z3_no_basis_associator(quat_table, "julia_quaternion_all_basis")

    source_checks = Dict{String,Any}(
        "artifact_path" => ARTIFACT_PATH,
        "artifact_sha256" => artifact_sha,
        "artifact_source_path" => artifact_source_path,
        "artifact_source_sha256_expected" => artifact["source_sha256"],
        "artifact_source_sha256_current" => artifact_source_sha,
        "artifact_source_sha256_matches" => artifact_source_sha == artifact["source_sha256"],
        "proof_tag" => artifact["proof_tag"],
        "proof_tag_matches_expected" => artifact["proof_tag"] == EXPECTED_PROOF_TAG,
        "proof_pass" => artifact["proof_pass"],
        "table_version" => artifact["table_version"],
        "bracket_convention" => artifact["bracket_convention"],
    )
    all_pass =
        source_checks["artifact_source_sha256_matches"] == true &&
        source_checks["proof_tag_matches_expected"] == true &&
        source_checks["proof_pass"] == true &&
        source_checks["bracket_convention"] == "left" &&
        oct_map["entry_count"] == 512 &&
        oct_map["nonzero_count_gt_tol"] > 0 &&
        quat_map["entry_count"] == 64 &&
        quat_map["nonzero_count_gt_tol"] == 0 &&
        oct_z3["verdict"] == "sat" &&
        quat_z3["verdict"] == "unsat"

    canon_runtime = Dict{String,Any}(
        "semantic_owner" => "julia",
        "artifact_path" => ARTIFACT_PATH,
        "artifact_sha256" => artifact_sha,
        "source_sha256" => artifact["source_sha256"],
        "receipt_path" => joinpath(ROOT, "system_v5", "ops", "formal_scouts", "results", "canon_algebra_artifact_v1_results.json"),
        "proof_tag" => artifact["proof_tag"],
        "proof_pass" => artifact["proof_pass"],
        "table_version" => artifact["table_version"],
        "bracket_convention" => artifact["bracket_convention"],
        "consumer_policy" => "compute_from_exported_C_tensor_with_fixed_parenthesization",
    )
    tool_calls = [
        tool_call(
            "JSON",
            "JSON.parsefile(ARTIFACT_PATH)",
            Dict("source_path" => ARTIFACT_PATH),
            Dict("table_version" => artifact["table_version"], "proof_tag" => artifact["proof_tag"], "algebras" => ["quaternion", "octonion"]),
            "Loaded the Julia-owned canon table from the versioned JSON artifact.",
            "Demotes if any engine reads peer result JSON or recomputes C instead of loading this artifact.",
            "Quaternion and octonion records both carry bracket_convention=left.",
            "Demote if source_sha256/proof_tag/proof_pass/bracket_convention does not match.",
        ),
        tool_call(
            "Julia",
            "mul(table,x,y): out[k] += C[k,i,j] * x[i] * y[j]",
            Dict("algebra" => "octonion", "basis_triples" => "all 8^3 triples"),
            Dict("entry_count" => oct_map["entry_count"], "nonzero_count_gt_tol" => oct_map["nonzero_count_gt_tol"], "max_norm" => oct_map["max_norm"]),
            "Julia authoritative leg computes the full 512-entry octonion associator-norm map.",
            "Demotes if JAX/PyTorch disagree; Julia is the arbiter, not a peer echo.",
            Dict("algebra" => "quaternion", "entry_count" => quat_map["entry_count"], "nonzero_count_gt_tol" => quat_map["nonzero_count_gt_tol"]),
            "Demote if multiplication order is rewritten or quaternion associativity is not all-zero.",
        ),
        tool_call(
            "Z3",
            "Solver + bound IntVar C[k,i,j] + check()",
            Dict("octonion_sampled_nonzero_triple" => sampled_nonzero_triple, "quaternion_scope" => "all basis triples"),
            Dict("octonion_nonzero" => oct_z3, "quaternion_nonzero_exists" => quat_z3),
            "Z3 derives octonion nonzero associator from bound C entries.",
            "No precomputed associator literal is asserted.",
            "Z3 derives no nonzero quaternion basis associator exists.",
            "Demote if solver receives a precomputed associator scalar instead of bound C algebra.",
        ),
    ]

    result = Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "schema_version" => "codex_ratchet.engine_leg_result.v1",
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "generated_at" => utc_now(),
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "julia_project" => Base.active_project(),
        "julia_version" => string(VERSION),
        "packages_used" => ["JSON", "SHA", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "claim_path_tools" => ["JSON", "Julia", "Z3"],
        "control_only_tools" => [],
        "source_checks" => source_checks,
        "canon_runtime" => canon_runtime,
        "associator_norm_maps" => Dict(
            "octonion_basis_triples" => oct_map,
            "quaternion_basis_triples" => quat_map,
        ),
        "sampled_nonzero_triple" => sampled_nonzero_triple,
        "proofs" => Dict(
            "z3" => Dict(
                "octonion_sampled_nonzero_assoc" => oct_z3,
                "quaternion_associator_nonzero_exists" => quat_z3,
            ),
        ),
        "tool_calls" => tool_calls,
        "TOOL_MANIFEST" => Dict(
            "Julia" => Dict("tried" => true, "used" => true, "reason" => "load-bearing authoritative local exhaustive associator map computation"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing derive-in-solver SAT/UNSAT controls from bound C"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive canon artifact intake"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Julia" => "load_bearing",
            "Z3" => "load_bearing",
            "JSON" => "supportive",
        ),
        "all_pass" => all_pass,
        "GAINED" => ["Julia authority leg consumed the canon JSON table and computed the full octonion/quaternion basis associator maps."],
        "NOT_GAINED" => ["No promotion; no independent rebuild of the canon table; no bridge or axis claim."],
        "CONTROLS" => ["quaternion all-basis associator map is zero", "Z3 derives octonion SAT and quaternion UNSAT from bound C"],
        "CEILING" => "classification=scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false",
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end

    println(JSON.json(Dict("ok" => all_pass, "result_path" => RESULT_PATH, "source_sha256" => result["source_sha256"])))
    return all_pass ? 0 : 1
end

if abspath(PROGRAM_FILE) == SOURCE_PATH
    exit(main())
end
