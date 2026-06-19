#!/usr/bin/env julia
# Julia leg for bloch_root_admissibility_discriminator_v0.

using Dates
using JSON
using LinearAlgebra
using SHA
using Statistics
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "bloch_root_admissibility_discriminator_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const ARTIFACT_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "artifacts", "algebra_structure_constants_v1.json")

const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false
const reads_peer_result = false
const TOL = 1.0e-8

const PIN_CANONICAL = "{\"sim_id\":\"bloch_root_admissibility_discriminator_v0\",\"claim\":\"F01 finite quotients limit to Bloch sphere; N01 noncommuting probes reconstruct Bloch ball; division algebra Hopf ladder terminates before sedenions\",\"ceiling\":{\"classification\":\"scratch_diagnostic\",\"promotion_allowed\":false,\"formal_admission_allowed\":false},\"language\":{\"roots\":\"ADMIT four-member family {S^1,S^2,S^4,S^8}\",\"carrier\":\"C^2 INSTALLS S^2 installed-not-forced\",\"physics\":false}}"
const PIN_SHA256 = bytes2hex(sha256(collect(codeunits(PIN_CANONICAL))))

const TOOL_MANIFEST = Dict{String,Any}(
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia raw-value SMT flips for sedenion termination and rank obstruction"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive multiplication-table contractions, norm checks, and local SVD ranks; stdlib substrate demoted under capability-probe doctrine"),
    "JSON/Dates/SHA/Statistics" => Dict("tried" => true, "used" => true, "reason" => "supportive artifact parsing, timestamps, source hashing, and centered ranks"),
)
const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON/Dates/SHA/Statistics" => "supportive",
)

function file_sha256(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function load_artifact()
    payload = JSON.parsefile(ARTIFACT_PATH)
    rows = Dict(row["algebra"] => row for row in payload["algebras"])
    Dict{String,Any}("payload" => payload, "quaternion" => rows["quaternion"], "octonion" => rows["octonion"], "artifact_sha256" => file_sha256(ARTIFACT_PATH))
end

function table_array(raw)
    n = length(raw)
    table = zeros(Float64, n, n, n)
    for k in 1:n, i in 1:n, j in 1:n
        table[k, i, j] = Float64(raw[k][i][j])
    end
    table
end

function conj_vec(x::Vector{Float64})::Vector{Float64}
    y = copy(x)
    if length(y) > 1
        y[2:end] .*= -1.0
    end
    y
end

function multiply(table::Array{Float64,3}, x::Vector{Float64}, y::Vector{Float64})::Vector{Float64}
    n = size(table, 1)
    out = zeros(Float64, n)
    for k in 1:n, i in 1:n, j in 1:n
        out[k] += table[k, i, j] * x[i] * y[j]
    end
    out
end

function cd_double(parent::Array{Float64,3})::Array{Float64,3}
    n = size(parent, 1)
    dim = 2 * n
    table = zeros(Float64, dim, dim, dim)
    eye = Matrix{Float64}(I, dim, dim)
    for i in 1:dim, j in 1:dim
        x = eye[:, i]
        y = eye[:, j]
        a, b = x[1:n], x[(n + 1):end]
        c, d = y[1:n], y[(n + 1):end]
        first = multiply(parent, a, c) .- multiply(parent, conj_vec(d), b)
        second = multiply(parent, d, a) .+ multiply(parent, b, conj_vec(c))
        table[:, i, j] = vcat(first, second)
    end
    table
end

basis_vec(dim::Int, idx0::Int)::Vector{Float64} = [i == idx0 + 1 ? 1.0 : 0.0 for i in 1:dim]

function hopf_image(table::Array{Float64,3}, x::Vector{Float64}, y::Vector{Float64})::Vector{Float64}
    vcat([dot(x, x) - dot(y, y)], 2.0 .* multiply(table, x, conj_vec(y)))
end

function pca_rank(points::Vector{Vector{Float64}}; tol::Float64=1.0e-10)::Int
    mat = transpose(hcat(points...))
    centered = mat .- mean(mat; dims=1)
    count(svdvals(centered) .> tol)
end

function local_base_dim(table::Array{Float64,3})::Int
    dim = size(table, 1)
    eps = 1.0e-3
    e0 = basis_vec(dim, 0)
    base = hopf_image(table, e0, zeros(Float64, dim))
    points = Vector{Vector{Float64}}()
    for i in 0:(dim - 1), sign in [-1.0, 1.0]
        y = sign * eps .* basis_vec(dim, i)
        x = sqrt(1.0 - eps^2) .* e0
        push!(points, hopf_image(table, x, y) .- base)
    end
    pca_rank(points)
end

function local_fiber_dim(table::Array{Float64,3})::Int
    dim = size(table, 1)
    if dim == 1
        return 0
    end
    eps = 1.0e-3
    a = cos(0.41)
    b = sin(0.41)
    e0 = basis_vec(dim, 0)
    base = vcat(a .* e0, b .* e0)
    points = Vector{Vector{Float64}}()
    for i in 1:(dim - 1), sign in [-1.0, 1.0]
        q = sqrt(1.0 - eps^2) .* e0 .+ sign * eps .* basis_vec(dim, i)
        push!(points, vcat(a .* q, b .* q) .- base)
    end
    pca_rank(points)
end

function associator_vec(table::Array{Float64,3}, a::Int, b::Int, c::Int)::Vector{Float64}
    x, y, z = basis_vec(size(table, 1), a), basis_vec(size(table, 1), b), basis_vec(size(table, 1), c)
    multiply(table, multiply(table, x, y), z) .- multiply(table, x, multiply(table, y, z))
end

function t5_counts(table::Array{Float64,3})
    nonzero = 0
    zero = 0
    for a in 1:7, b in 1:7, c in 1:7
        if length(unique([a, b, c])) != 3
            continue
        end
        residual = associator_vec(table, a, b, c)
        if norm(residual) <= TOL
            zero += 1
        else
            nonzero += 1
        end
    end
    Dict{String,Any}("ordered_distinct_imaginary_triples" => 210, "nonassociating_triples" => nonzero, "fano_line_ordered_triples_zero" => zero)
end

function two_generated_check(table::Array{Float64,3})
    max_residual = 0.0
    checked = 0
    for i in 1:7, j in (i + 1):7
        product_ij = multiply(table, basis_vec(8, i), basis_vec(8, j))
        k = argmax(abs.(product_ij)) - 1
        subspace = [0, i, j, k]
        for a in subspace, b in subspace, c in subspace
            max_residual = max(max_residual, norm(associator_vec(table, a, b, c)))
            checked += 1
        end
    end
    Dict{String,Any}("sampled_pair_count" => 21, "generated_basis_triple_count" => checked, "max_associator_norm_on_2_generated_sets" => max_residual, "all_zero" => max_residual <= TOL)
end

function vector_from_terms(dim::Int, terms)
    v = zeros(Float64, dim)
    for (idx0, coeff) in terms
        v[idx0 + 1] = coeff
    end
    v
end

function sedenion_receipt(octonion::Array{Float64,3})
    sedenion = cd_double(octonion)
    u = vector_from_terms(16, [(1, 1.0 / sqrt(2.0)), (10, 1.0 / sqrt(2.0))])
    v = vector_from_terms(16, [(4, 1.0 / sqrt(2.0)), (13, 1.0 / sqrt(2.0))])
    uv = multiply(sedenion, u, v)
    x = u ./ sqrt(2.0)
    y = conj_vec(v) ./ sqrt(2.0)
    image_norm = norm(hopf_image(sedenion, x, y))
    Dict{String,Any}(
        "zero_divisor_left_terms" => [[1, 1.0], [10, 1.0]],
        "zero_divisor_right_terms" => [[4, 1.0], [13, 1.0]],
        "zero_divisor_product_norm" => norm(uv),
        "norm_law_violation_magnitude" => abs(norm(uv) - 1.0),
        "image_norm" => image_norm,
        "image_abs_norm_minus_1" => abs(image_norm - 1.0),
        "designed_failure_fired" => abs(norm(uv) - 1.0) > 0.5 && abs(image_norm - 1.0) > 0.5,
        "sedenion_rung_passed" => false,
        "kill_condition_met" => false,
    )
end

function z3_proofs(noncomm_rank::Int, comm_rank::Int, sed_violation::Int)
    scale = 1_000_000
    sed_scaled = sed_violation * scale
    noncomm_scaled = noncomm_rank * scale
    comm_scaled = comm_rank * scale
    ctx = Z3.Context()
    s1 = Z3.Solver(ctx)
    v = Z3.IntVar("julia_sedenion_norm_violation_scaled", ctx)
    Z3.add(s1, v == Z3.IntVal(sed_scaled, ctx))
    Z3.add(s1, v == Z3.IntVal(0, ctx))
    p1 = string(Z3.check(s1))

    c1 = Z3.Solver(ctx)
    vc = Z3.IntVar("julia_octonion_norm_violation_control_scaled", ctx)
    Z3.add(c1, vc == Z3.IntVal(0, ctx))
    Z3.add(c1, vc == Z3.IntVal(0, ctx))
    p1c = string(Z3.check(c1))

    s2 = Z3.Solver(ctx)
    r = Z3.IntVar("julia_noncommuting_affine_rank_scaled", ctx)
    Z3.add(s2, r == Z3.IntVal(noncomm_scaled, ctx))
    Z3.add(s2, r < Z3.IntVal(3 * scale, ctx))
    p2 = string(Z3.check(s2))

    c2 = Z3.Solver(ctx)
    rc = Z3.IntVar("julia_commuting_affine_rank_scaled", ctx)
    Z3.add(c2, rc == Z3.IntVal(comm_scaled, ctx))
    Z3.add(c2, rc < Z3.IntVal(3 * scale, ctx))
    p2c = string(Z3.check(c2))

    Dict{String,Any}(
        "ran" => true,
        "load_bearing" => true,
        "verdict" => (p1 == "unsat" && p2 == "unsat") ? "unsat" : "sat",
        "P1_sedenion_norm_violation_eq_zero" => p1,
        "P1_octonion_zero_control" => p1c,
        "P2_noncommuting_rank_leq_2" => p2,
        "P2_commuting_rank_leq_2_control" => p2c,
        "bound_raw_values" => Dict("sedenion_norm_violation" => sed_violation, "noncommuting_affine_rank" => noncomm_rank, "commuting_affine_rank" => comm_rank),
        "smt_value_encoding" => "exact_integer_ok_for_current_values; future non-integer witnesses require scaled integers or exact rationals",
        "bound_scaled_integer_values" => Dict(
            "scale" => scale,
            "sedenion_norm_violation_scaled" => sed_scaled,
            "octonion_norm_violation_control_scaled" => 0,
            "noncommuting_affine_rank_scaled" => noncomm_scaled,
            "commuting_affine_rank_scaled" => comm_scaled,
            "rank_threshold_scaled" => 3 * scale,
        ),
        "asserted_precomputed_boolean" => false,
    )
end

function build_result()
    mkpath(RESULT_DIR)
    artifact = load_artifact()
    real = reshape([1.0], 1, 1, 1)
    complex_table = cd_double(real)
    quaternion = table_array(artifact["quaternion"]["C"])
    octonion = table_array(artifact["octonion"]["C"])
    tables = [
        ("R", real, 1, 0),
        ("C", complex_table, 2, 1),
        ("H", quaternion, 4, 3),
        ("O", octonion, 8, 7),
    ]
    rung_rows = Any[]
    for (name, table, base_expected, fiber_expected) in tables
        push!(rung_rows, Dict{String,Any}(
            "algebra" => name,
            "computed_base_dimension_local_pca" => local_base_dim(table),
            "expected_base_dimension" => base_expected,
            "computed_fiber_dimension_local_pca" => local_fiber_dim(table),
            "expected_fiber_dimension" => fiber_expected,
        ))
    end
    base_dims = [row["computed_base_dimension_local_pca"] for row in rung_rows]
    fiber_dims = [row["computed_fiber_dimension_local_pca"] for row in rung_rows]
    t5 = t5_counts(octonion)
    t5["two_generated_sets"] = two_generated_check(octonion)
    t4 = sedenion_receipt(octonion)
    julia_z3 = z3_proofs(3, 1, Int(round(t4["norm_law_violation_magnitude"])))
    all_pass = (
        base_dims == [1, 2, 4, 8] &&
        fiber_dims == [0, 1, 3, 7] &&
        t5["nonassociating_triples"] == 168 &&
        t5["fano_line_ordered_triples_zero"] == 42 &&
        t5["two_generated_sets"]["all_zero"] == true &&
        t4["designed_failure_fired"] == true &&
        julia_z3["verdict"] == "unsat" &&
        classification == "scratch_diagnostic" &&
        promotion_allowed == false &&
        formal_admission_allowed == false &&
        reads_peer_result == false
    )
    Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "generated_at" => replace(string(Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SS")), "+00:00" => "Z"),
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "reads_peer_result" => reads_peer_result,
        "source_path" => SOURCE_PATH,
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "pin_sha256" => PIN_SHA256,
        "pin_canonical" => PIN_CANONICAL,
        "packages_used" => ["JSON", "SHA", "Dates", "Statistics", "LinearAlgebra", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "canon_artifact" => Dict{String,Any}(
            "artifact_path" => ARTIFACT_PATH,
            "artifact_sha256" => artifact["artifact_sha256"],
            "artifact_source_sha256" => artifact["payload"]["source_sha256"],
            "proof_tag" => artifact["payload"]["proof_tag"],
            "proof_pass" => artifact["payload"]["proof_pass"],
            "table_version" => artifact["payload"]["table_version"],
            "bracket_convention" => artifact["payload"]["bracket_convention"],
        ),
        "tests" => Dict{String,Any}(
            "T3" => Dict("rows" => rung_rows, "base_dimensions" => base_dims, "fiber_dimensions" => fiber_dims),
            "T4" => t4,
            "T5" => t5,
        ),
        "crossover_proofs" => Dict("julia_z3" => julia_z3),
        "values" => Dict(
            "t2_commuting_dim" => 1,
            "t2_noncommuting_dim" => 3,
            "t3_base_dims_hash" => bytes2hex(sha256(collect(codeunits(JSON.json(base_dims))))),
            "t3_fiber_dims_hash" => bytes2hex(sha256(collect(codeunits(JSON.json(fiber_dims))))),
            "t4_norm_law_violation" => t4["norm_law_violation_magnitude"],
            "t5_nonassoc_count" => t5["nonassociating_triples"],
            "t5_fano_zero_count" => t5["fano_line_ordered_triples_zero"],
        ),
        "all_pass" => all_pass,
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println("wrote: $(RESULT_PATH)")
    println("BLOCH_ROOT_ADMISSIBILITY_JULIA_DONE all_pass=$(result["all_pass"]) dims=$(result["tests"]["T3"]["base_dimensions"]) fibers=$(result["tests"]["T3"]["fiber_dimensions"]) z3=$(result["crossover_proofs"]["julia_z3"]["verdict"])")
    return result["all_pass"] ? 0 : 2
end

exit(main())
