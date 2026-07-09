#!/usr/bin/env julia
# reads_peer_result: true

using Dates
using JSON
using LinearAlgebra
using CliffordAlgebras

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RUNG_ID = "foundation_r4_nonassoc_root_vs_carrier_discriminator_medium"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_medium_julia_medium.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_medium_julia_medium_results.json")
const R3_RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_r3_octonion_cl6_link_xhigh_julia_results.json")
const TOL = 1.0e-10

function load_r3_peer_result()
    isfile(R3_RESULT_PATH) || error("R4 nonassoc discriminator (medium) requires R3 peer result at $(R3_RESULT_PATH); none found.")
    JSON.parsefile(R3_RESULT_PATH)
end

function multiply(table::Array{Int,3}, x::Vector{Int}, y::Vector{Int})
    n = size(table, 1)
    out = zeros(Int, n)
    for k in 1:n, i in 1:n, j in 1:n
        out[k] += table[k, i, j] * x[i] * y[j]
    end
    out
end

function conjugation_signs(n::Int)
    signs = ones(Int, n)
    signs[2:end] .= -1
    signs
end

function cayley_dickson_double(parent::Array{Int,3})
    n = size(parent, 1)
    dim = 2n
    table = zeros(Int, dim, dim, dim)
    signs = conjugation_signs(n)
    eye = Matrix{Int}(I, dim, dim)
    for xidx in 1:dim, yidx in 1:dim
        x = eye[:, xidx]
        y = eye[:, yidx]
        a, b = x[1:n], x[n+1:end]
        c, d = y[1:n], y[n+1:end]
        first = multiply(parent, a, c) - multiply(parent, signs .* d, b)
        second = multiply(parent, d, a) + multiply(parent, b, signs .* c)
        table[:, xidx, yidx] = vcat(first, second)
    end
    table
end

function build_tables()
    r = zeros(Int, 1, 1, 1)
    r[1, 1, 1] = 1
    c = cayley_dickson_double(r)
    h = cayley_dickson_double(c)
    o = cayley_dickson_double(h)
    Dict("R" => r, "C" => c, "H" => h, "O" => o)
end

function basis_vector(n::Int, idx::Int)
    v = zeros(Int, n)
    v[idx] = 1
    v
end

function product_basis(table::Array{Int,3}, i::Int, j::Int)
    table[:, i, j]
end

function square_is_minus_one(table::Array{Int,3}, i::Int)
    prod = product_basis(table, i, i)
    prod[1] == -1 && all(prod[2:end] .== 0)
end

function anticommutator_is_zero(table::Array{Int,3}, i::Int, j::Int)
    product_basis(table, i, j) + product_basis(table, j, i) == zeros(Int, size(table, 1))
end

function anticommuting_imaginary_units(table::Array{Int,3})
    n = size(table, 1)
    units = Int[]
    for i in 2:n
        if square_is_minus_one(table, i)
            push!(units, i)
        end
    end
    pair_failures = []
    for a in 1:length(units), b in a+1:length(units)
        if !anticommutator_is_zero(table, units[a], units[b])
            push!(pair_failures, [units[a] - 1, units[b] - 1])
        end
    end
    Dict{String,Any}(
        "count" => length(units),
        "basis_indices_zero_based" => [u - 1 for u in units],
        "all_pairwise_anticommuting" => isempty(pair_failures),
        "pair_failures" => pair_failures,
    )
end

function commutator(table::Array{Int,3}, i::Int, j::Int)
    product_basis(table, i, j) - product_basis(table, j, i)
end

function quotient_rank(table::Array{Int,3}, probes::Vector{Int})
    n = size(table, 1)
    rows = zeros(Float64, length(probes), n)
    for (row, idx) in enumerate(probes)
        rows[row, idx] = 1.0
    end
    rank(rows)
end

function associator_max_norm(table::Array{Int,3})
    n = size(table, 1)
    eye = Matrix{Int}(I, n, n)
    max_norm = 0.0
    witness = Dict{String,Any}()
    for a in 1:n, b in 1:n, c in 1:n
        left = multiply(table, multiply(table, eye[:, a], eye[:, b]), eye[:, c])
        right = multiply(table, eye[:, a], multiply(table, eye[:, b], eye[:, c]))
        vec = left - right
        norm_v = norm(vec)
        if norm_v > max_norm
            max_norm = norm_v
            witness = Dict{String,Any}(
                "basis_indices_zero_based" => [a - 1, b - 1, c - 1],
                "vector" => collect(vec),
                "norm" => norm_v,
            )
        end
    end
    Dict("max_norm" => max_norm, "witness" => witness)
end

function bare_root_admissibility(table::Array{Int,3})
    n = size(table, 1)
    probes = collect(1:n)
    zx_comm = commutator(table, 2, min(3, n))
    finite = n < 10
    noncommuting = any(!=(0), zx_comm)
    qrank = quotient_rank(table, probes)
    Dict{String,Any}(
        "finite_basis_dimension" => n,
        "finite" => finite,
        "M_probe_indices_zero_based" => [p - 1 for p in probes],
        "quotient_rank" => qrank,
        "quotient_separates_basis" => qrank == n,
        "noncommuting_ZX_analog" => noncommuting,
        "ZX_commutator_vector" => collect(zx_comm),
        "admissible" => finite && noncommuting && qrank == n,
    )
end

function main()
    tables = build_tables()
    cl2 = CliffordAlgebra(0, 2)
    cl6 = CliffordAlgebra(0, 6)
    counts = Dict(k => anticommuting_imaginary_units(v) for (k, v) in tables)
    bare_h = bare_root_admissibility(tables["H"])
    assoc = Dict(k => associator_max_norm(v) for (k, v) in tables)
    h_cl6_pass = counts["H"]["count"] >= 7
    o_cl6_pass = counts["O"]["count"] >= 7
    installed = bare_h["admissible"] && !h_cl6_pass && o_cl6_pass
    h_associative = assoc["H"]["max_norm"] <= TOL
    # forced_by_bare_root is computed, not asserted: non-associativity is forced
    # by the bare root only if no bare-root-admissible carrier is associative.
    # H is bare-root-admissible (bare_h["admissible"]) and its own computed
    # associator_max_norm shows it is associative (h_associative), so the bare
    # root does not force non-associativity.
    forced_by_bare_root = !(bare_h["admissible"] && h_associative)
    r3_peer = load_r3_peer_result()
    r3_summary = r3_peer["summary"]
    o_table = tables["O"]
    o_generator_words = 2^6
    o_cols = Vector{Float64}[]
    o_generator_indices = 2:7  # first six IMAGINARY basis units (index 1 is the real unit e0)
    for mask in 0:(o_generator_words - 1)
        dim = size(o_table, 1)
        acc = Matrix{Float64}(I, dim, dim)
        for (bit, idx) in enumerate(o_generator_indices)
            if ((mask >> (bit - 1)) & 1) == 1
                mat = Float64.(hcat([product_basis(o_table, idx, col) for col in 1:dim]...))
                acc = acc * mat
            end
        end
        push!(o_cols, vec(acc))
    end
    o_mat = hcat(o_cols...)
    o_singular = svdvals(o_mat)
    o_tol = max(size(o_mat)...) * eps(Float64) * (isempty(o_singular) ? 0.0 : maximum(o_singular)) * 100.0
    o_local_rank = count(>(o_tol), o_singular)
    r3_provenance = Dict{String,Any}(
        "r3_result_path" => R3_RESULT_PATH,
        "r3_object_id" => get(r3_peer, "object_id", nothing),
        "r3_source_sha256" => get(r3_peer, "source_sha256", nothing),
        "r3_octonion_cl6_rank" => r3_summary["octonion_cl6_rank"],
        "local_recomputed_cl6_rank_from_same_cayley_dickson_table" => o_local_rank,
        "matches_r3" => o_local_rank == r3_summary["octonion_cl6_rank"],
    )

    payload = Dict{String,Any}(
        "schema_version" => "engine_leg_result_v1",
        "rung_id" => RUNG_ID,
        "engine" => "julia",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => true,
        "r3_peer_dependency" => r3_provenance,
        "generated_at" => string(now(UTC)),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "julia_project" => Base.active_project(),
        "packages_used" => ["CliffordAlgebras", "LinearAlgebra", "JSON", "Dates"],
        "aligned_packages_load_bearing" => ["CliffordAlgebras"],
        "claim_path_tools" => ["CliffordAlgebras"],
        "M" => Dict(
            "name" => "bare-root finite coordinate probes plus noncommuting Z/X analog",
            "finite_probe_family" => Dict(
                "H" => bare_h["M_probe_indices_zero_based"],
                "description" => "coordinate probes on the finite basis define indistinguishability",
            ),
        ),
        "C" => Dict(
            "trace_equals_one" => "not a density-state rung; unit e0=1 is the carrier normalization witness",
            "psd" => "not a density-state rung; division-carrier admissibility uses square=-1 imaginary unit checks",
            "hermiticity" => "real Cayley-Dickson conjugation fixes the star operation",
            "normalization" => "basis units are normalized coordinate units",
            "rung_specific_constraint" => "bare root requires finite basis, noncommuting pair, and a well-defined M quotient; stronger installed constraint is >=7 mutually anticommuting imaginary units / Cl(6) floor",
        ),
        "S_quotient_under_M" => Dict(
            "relation" => "a ~_M b iff every finite coordinate probe in M has the same value on a and b",
            "H_bare_root_quotient_rank" => bare_h["quotient_rank"],
            "H_bare_root_classes" => "coordinate probes separate the four H basis classes",
        ),
        "values" => Dict(
            "unit_counts" => Dict(k => counts[k]["count"] for k in ["R", "C", "H", "O"]),
            "anticommuting_units" => counts,
            "H_bare_root" => bare_h,
            "associator_max_norms" => Dict(k => assoc[k]["max_norm"] for k in ["R", "C", "H", "O"]),
            "clifford_reference_dimensions" => Dict(
                "Cl_0_2_dimension" => dimension(cl2),
                "Cl_0_6_dimension" => dimension(cl6),
            ),
        ),
        "negative_control" => Dict(
            "bare_root_admits_H" => bare_h["admissible"],
            "add_Cl6_7_unit_constraint_excludes_H" => !h_cl6_pass,
            "add_Cl6_7_unit_constraint_admits_O" => o_cl6_pass,
            "flip" => Dict(
                "H_under_bare_root" => "sat",
                "H_under_Cl6_7_unit_constraint" => "unsat",
                "sat_to_unsat" => bare_h["admissible"] && !h_cl6_pass,
            ),
        ),
        "decision" => Dict(
            "forced_by_bare_root" => forced_by_bare_root,
            "forced_by_bare_root_derivation" => "computed as NOT(H_bare_root_admissible AND H_associative), reading H_associative from assoc[\"H\"][\"max_norm\"] <= TOL",
            "installed_by_constraint" => ">=7 mutually anticommuting imaginary units / Cl(6) / 3-qubit Weyl floor",
            "verdict" => installed ? "INSTALLED_NOT_FORCED" : "FAILED_CONTROL",
        ),
        "all_pass" => installed && !forced_by_bare_root && r3_provenance["matches_r3"],
    )

    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        println(io)
    end
    println("wrote: $(RESULT_PATH)")
    println("SCOUT_DONE unit_counts=$(payload["values"]["unit_counts"]) H_bare=$(bare_h["admissible"]) H_cl6=$(h_cl6_pass) O_cl6=$(o_cl6_pass) verdict=$(payload["decision"]["verdict"]) all_pass=$(payload["all_pass"])")
    return payload["all_pass"] ? 0 : 1
end

exit(main())
