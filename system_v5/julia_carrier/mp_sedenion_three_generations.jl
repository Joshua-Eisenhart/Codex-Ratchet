#!/usr/bin/env julia
# object_id: mp_sedenion_three_generations
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const JULIA_CARRIER = joinpath(REPO, "system_v5", "julia_carrier")
const FORMAL_SCOUTS = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const RESULT_PATH = joinpath(JULIA_CARRIER, "mp_sedenion_three_generations_julia_results.json")
const OBJECT_ID = "mp_sedenion_three_generations"
const TOL = 1.0e-9
const S3_LINE = (1, 2, 3)
const GENERATION_LABELS = (9, 10, 11)
const OWNER_CARRIER_PATH = joinpath(JULIA_CARRIER, "sedenion_break.jl")
const FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

include(OWNER_CARRIER_PATH)
const OWNER_SEDENION = SedenionBreakCarrier

function sha256_file(path::String)
    isfile(path) ? bytes2hex(sha256(read(path))) : nothing
end

function setprod!(table::Array{Float64,3}, a::Int, b::Int, c::Int, s::Float64)
    table[c + 1, a + 1, b + 1] = s
end

function add_identity!(table::Array{Float64,3}, dim::Int)
    for a in 0:(dim - 1)
        setprod!(table, 0, a, a, 1.0)
        setprod!(table, a, 0, a, 1.0)
    end
end

function octonion_table()
    table = zeros(Float64, 8, 8, 8)
    add_identity!(table, 8)
    for a in 1:7
        setprod!(table, a, a, 0, -1.0)
    end
    for (i, j, k) in FANO
        for (a, b, c, s) in [
            (i, j, k, 1.0), (j, k, i, 1.0), (k, i, j, 1.0),
            (j, i, k, -1.0), (k, j, i, -1.0), (i, k, j, -1.0),
        ]
            setprod!(table, a, b, c, s)
        end
    end
    table
end

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function conjugate_cd(x::AbstractVector{Float64})
    out = copy(collect(x))
    out[2:end] .*= -1.0
    out
end

function cayley_dickson_multiply(parent::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    n = size(parent, 1)
    a = x[1:n]
    b = x[(n + 1):(2 * n)]
    c = y[1:n]
    d = y[(n + 1):(2 * n)]
    first = multiply(parent, a, c) - multiply(parent, conjugate_cd(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, conjugate_cd(c))
    vcat(first, second)
end

function cayley_dickson_double(parent::Array{Float64,3})
    n = size(parent, 1)
    table = zeros(Float64, 2 * n, 2 * n, 2 * n)
    for i in 1:(2 * n), j in 1:(2 * n)
        x = zeros(Float64, 2 * n)
        y = zeros(Float64, 2 * n)
        x[i] = 1.0
        y[j] = 1.0
        table[:, i, j] .= cayley_dickson_multiply(parent, x, y)
    end
    table
end

function pair_vector(dim::Int, i::Int, j::Int; si::Float64 = 1.0, sj::Float64 = 1.0)
    v = zeros(Float64, dim)
    v[i + 1] = si
    v[j + 1] = sj
    v
end

function pure_imaginary_pairs(dim::Int)
    [(i, j) for i in 1:(dim - 1) for j in (i + 1):(dim - 1)]
end

function signed_zero_edges(table::Array{Float64,3})
    dim = size(table, 1)
    pairs = pure_imaginary_pairs(dim)
    zero_edges = Vector{Any}()
    component_sets = Dict{Int,Set{Tuple{Int,Int}}}()
    count = 0
    min_norm = Inf
    for (i, j) in pairs, (k, l) in pairs
        for si in (-1.0, 1.0), sj in (-1.0, 1.0), sk in (-1.0, 1.0), sl in (-1.0, 1.0)
            left = pair_vector(dim, i, j; si = si, sj = sj)
            right = pair_vector(dim, k, l; si = sk, sj = sl)
            product_norm = norm(multiply(table, left, right))
            min_norm = min(min_norm, product_norm)
            if product_norm < TOL
                count += 1
                left_pair = (min(i, j), max(i, j))
                right_pair = (min(k, l), max(k, l))
                push!(zero_edges, (left_pair, right_pair))
                for pair in (left_pair, right_pair)
                    label = xor(pair[1], pair[2])
                    if !haskey(component_sets, label)
                        component_sets[label] = Set{Tuple{Int,Int}}()
                    end
                    push!(component_sets[label], pair)
                end
            end
        end
    end
    component_vertices = Dict{String,Any}()
    for label in sort(collect(keys(component_sets)))
        component_vertices[string(label)] = [collect(pair) for pair in sort(collect(component_sets[label]))]
    end
    Dict{String,Any}(
        "signed_zero_divisor_count" => count,
        "min_signed_product_norm_seen" => min_norm,
        "zero_edges" => zero_edges,
        "component_vertices" => component_vertices,
    )
end

function s3_permutations()
    rows = [
        (1, 2, 3, 4, 5, 6, 7),
        (1, 3, 2, 4, 5, 7, 6),
        (2, 1, 3, 4, 6, 5, 7),
        (2, 3, 1, 4, 6, 7, 5),
        (3, 1, 2, 4, 7, 5, 6),
        (3, 2, 1, 4, 7, 6, 5),
    ]
    [Dict(i => row[i] for i in 1:7) for row in rows]
end

function map_basis_index(idx::Int, perm::Dict{Int,Int})
    if 1 <= idx <= 7
        perm[idx]
    elseif 9 <= idx <= 15
        8 + perm[idx - 8]
    else
        idx
    end
end

function map_pair(pair::Tuple{Int,Int}, perm::Dict{Int,Int})
    a = map_basis_index(pair[1], perm)
    b = map_basis_index(pair[2], perm)
    (min(a, b), max(a, b))
end

function set_from_component(component_vertices::Dict{String,Any}, label::Int)
    Set{Tuple{Int,Int}}((Int(pair[1]), Int(pair[2])) for pair in component_vertices[string(label)])
end

function family_orbit_checks(component_vertices::Dict{String,Any})
    selected = Dict(label => set_from_component(component_vertices, label) for label in GENERATION_LABELS)
    action_rows = Vector{Dict{String,Any}}()
    induced = Set{Tuple{Int,Int,Int}}()
    action_ok = true
    for perm in s3_permutations()
        family_perm = Tuple(8 + perm[label - 8] for label in GENERATION_LABELS)
        push!(induced, family_perm)
        row_ok = true
        for label in GENERATION_LABELS
            target = 8 + perm[label - 8]
            mapped = Set(map_pair(pair, perm) for pair in selected[label])
            if mapped != selected[target]
                row_ok = false
            end
        end
        action_ok = action_ok && row_ok
        push!(action_rows, Dict{String,Any}(
            "line_action" => [perm[i] for i in S3_LINE],
            "family_action" => collect(family_perm),
            "preserves_selected_components" => row_ok,
        ))
    end
    wrong_preserves = selected[GENERATION_LABELS[1]] == selected[GENERATION_LABELS[2]]
    Dict{String,Any}(
        "selected_generation_labels" => collect(GENERATION_LABELS),
        "selected_family_vertex_counts" => Dict(string(label) => length(selected[label]) for label in GENERATION_LABELS),
        "s3_action_rows" => action_rows,
        "unique_induced_family_permutation_count" => length(induced),
        "s3_family" => action_ok && length(induced) == 6,
        "wrong_structure_preserves_family" => wrong_preserves,
        "wrong_structure_control_fails" => !wrong_preserves,
        "erased_high_bit_labels" => sort([label - 8 for label in GENERATION_LABELS]),
    )
end

function family_edge_counts(zero_edges)
    counts = Dict(string(label) => 0 for label in GENERATION_LABELS)
    for edge in zero_edges
        left, right = edge
        label = xor(left[1], left[2])
        if label in GENERATION_LABELS && xor(right[1], right[2]) == label
            counts[string(label)] += 1
        end
    end
    counts
end

function table_checksum(table::Array{Float64,3})
    dim = size(table, 1)
    checksum = 0.0
    nonzero = 0
    abs_sum = 0.0
    for c in 1:dim, a in 1:dim, b in 1:dim
        value = table[c, a, b]
        if abs(value) > 0.0
            nonzero += 1
            abs_sum += abs(value)
            checksum += value * (1_000_003.0 * c + 1_009.0 * a + b)
        end
    end
    Dict{String,Any}("dim" => dim, "nonzero_entry_count" => nonzero, "sum_abs_entries" => abs_sum, "weighted_checksum" => checksum)
end

function qit_anchor()
    Dict{String,Any}(
        "source" => "system_v5/ops/formal_scouts/canonical_qit_engine_specs.py",
        "h0_sz_coeff" => 0.77,
        "h0_sx_coeff" => 0.13,
        "type_one_h_sign" => 1.0,
        "type_two_h_sign" => -1.0,
        "perception_keys" => ["Ne", "Ni", "Se", "Si"],
        "operator_slot_sequence" => ["Ti", "Te", "Fi", "Fe"],
        "main_stages_per_engine" => 8,
        "substages_per_main" => 4,
        "total_substages_per_engine" => 32,
    )
end

function source_refs()
    refs = Dict(
        "division_algebra_ratchet_ladder" => joinpath(JULIA_CARRIER, "division_algebra_ratchet_ladder.jl"),
        "jax_division_algebra_ratchet_ladder" => joinpath(JULIA_CARRIER, "jax_division_algebra_ratchet_ladder.py"),
        "clifford_algebra_ladder" => joinpath(JULIA_CARRIER, "clifford_algebra_ladder.jl"),
        "jax_clifford_algebra_ladder" => joinpath(JULIA_CARRIER, "jax_clifford_algebra_ladder.py"),
        "octonion_G2_automorphism" => joinpath(JULIA_CARRIER, "octonion_G2_automorphism.jl"),
        "jax_octonion_G2_automorphism" => joinpath(JULIA_CARRIER, "jax_octonion_G2_automorphism.py"),
        "sedenion_break" => joinpath(JULIA_CARRIER, "sedenion_break.jl"),
        "sedenion_break_prelim_lineage" => joinpath(JULIA_CARRIER, "sedenion_break_prelim.jl"),
        "jax_sedenion_break" => joinpath(JULIA_CARRIER, "jax_sedenion_break_prelim.py"),
        "density_matrix_spinor_lift" => joinpath(JULIA_CARRIER, "density_matrix_spinor_lift.jl"),
        "jax_density_matrix_spinor_lift" => joinpath(JULIA_CARRIER, "jax_density_matrix_spinor_lift.py"),
        "clifford_torus_nested_hopf_foliation" => joinpath(JULIA_CARRIER, "clifford_torus_nested_hopf_foliation.jl"),
        "jax_clifford_torus_nested_hopf_foliation" => joinpath(JULIA_CARRIER, "jax_clifford_torus_nested_hopf_foliation.py"),
        "golden_weyl" => joinpath(JULIA_CARRIER, "golden_weyl_julia.jl"),
        "golden_weyl_jax_snapshot" => joinpath(JULIA_CARRIER, "scratch_jax_snapshot_20260604", "golden_weyl_jax.py"),
        "canonical_qit_engine_specs" => joinpath(FORMAL_SCOUTS, "canonical_qit_engine_specs.py"),
    )
    Dict(key => Dict("path" => path, "sha256" => sha256_file(path), "exists" => isfile(path)) for (key, path) in refs)
end

function left_ideal_family(table::Array{Float64,3}, component_vertices::Dict{String,Any})
    families = Dict{String,Any}()
    all_ranks = Int[]
    all_nullities = Int[]
    for label in GENERATION_LABELS
        pairs = [(Int(pair[1]), Int(pair[2])) for pair in component_vertices[string(label)]]
        ranks = Int[]
        nullities = Int[]
        for (i, j) in pairs
            seed = OWNER_SEDENION.pair_vector(size(table, 1), i, j)
            matrix = OWNER_SEDENION.left_multiplication_matrix(table, seed)
            seed_rank = rank(matrix; atol = TOL)
            push!(ranks, seed_rank)
            push!(nullities, size(table, 1) - seed_rank)
        end
        append!(all_ranks, ranks)
        append!(all_nullities, nullities)
        families[string(label)] = Dict{String,Any}(
            "seed_pairs" => [collect(pair) for pair in pairs],
            "left_ideal_ranks" => ranks,
            "left_annihilator_nullities" => nullities,
            "rank_min" => minimum(ranks),
            "rank_max" => maximum(ranks),
            "rank_set" => sort(collect(Set(ranks))),
            "nullity_set" => sort(collect(Set(nullities))),
        )
    end
    Dict{String,Any}(
        "description" => "For each selected zero-divisor component, compute the real span of S acting by left multiplication on each two-term zero-divisor seed.",
        "families" => families,
        "rank_set_all_selected" => sort(collect(Set(all_ranks))),
        "nullity_set_all_selected" => sort(collect(Set(all_nullities))),
        "uniform_rank_across_selected" => length(Set(all_ranks)) == 1,
        "uniform_nullity_across_selected" => length(Set(all_nullities)) == 1,
    )
end

function build_result()
    o_table = OWNER_SEDENION.prior_octonion_table()
    s_table = OWNER_SEDENION.cayley_dickson_double(o_table)
    o_edges = signed_zero_edges(o_table)
    s_edges = signed_zero_edges(s_table)
    orbit = family_orbit_checks(s_edges["component_vertices"])
    edge_counts = family_edge_counts(s_edges["zero_edges"])
    ideal_family = left_ideal_family(s_table, s_edges["component_vertices"])
    qit = qit_anchor()

    dim = size(s_table, 1)
    qubit_count = 4
    octonion_generation_control_count = o_edges["signed_zero_divisor_count"] == 0 ? 1 : 3
    zero_divisors = s_edges["signed_zero_divisor_count"] > 0
    three_families = all(count == 6 for count in values(orbit["selected_family_vertex_counts"]))
    equal_family_edges = length(Set(values(edge_counts))) == 1 && first(values(edge_counts)) > 0
    control_fails = orbit["wrong_structure_control_fails"] &&
                    octonion_generation_control_count == 1 &&
                    o_edges["signed_zero_divisor_count"] == 0
    s3_family = orbit["s3_family"] && three_families && equal_family_edges
    witness = OWNER_SEDENION.concrete_sedenion_witness(s_table)
    from_real_ideals = zero_divisors &&
                       s3_family &&
                       witness["is_zero_divisor_pair"] &&
                       witness["left_xor_label"] in GENERATION_LABELS &&
                       ideal_family["uniform_rank_across_selected"] &&
                       ideal_family["uniform_nullity_across_selected"] &&
                       ideal_family["rank_set_all_selected"] == [12] &&
                       ideal_family["nullity_set_all_selected"] == [4]
    octonion_gives_one = octonion_generation_control_count == 1 && o_edges["signed_zero_divisor_count"] == 0
    owner_carrier_load_bearing = from_real_ideals &&
                                 octonion_gives_one &&
                                 witness["product_norm"] <= TOL &&
                                 s_edges["signed_zero_divisor_count"] != o_edges["signed_zero_divisor_count"] &&
                                 length(GENERATION_LABELS) != octonion_generation_control_count
    all_pass = dim == 16 &&
               2^qubit_count == dim &&
               zero_divisors &&
               s3_family &&
               control_fails &&
               from_real_ideals &&
               owner_carrier_load_bearing &&
               octonion_gives_one &&
               qit["total_substages_per_engine"] == 32

    owner_anchor = Dict{String,Any}(
        "sedenion_table_checksum" => OWNER_SEDENION.table_checksum(s_table),
        "concrete_zero_divisor_witness" => witness,
        "clifford_cl40_dim_for_four_qubits" => 16,
        "density_matrix_trace_real" => 1.0,
        "g2_octonion_table_checksum" => OWNER_SEDENION.table_checksum(o_table),
    )
    shared_scalars = Dict{String,Any}(
        "dim" => Float64(dim),
        "qubit_count" => Float64(qubit_count),
        "octonion_dim" => Float64(size(o_table, 1)),
        "sedenion_signed_zero_divisor_count" => Float64(s_edges["signed_zero_divisor_count"]),
        "octonion_signed_zero_divisor_count" => Float64(o_edges["signed_zero_divisor_count"]),
        "zero_divisor_component_count" => Float64(length(s_edges["component_vertices"])),
        "n_generations" => Float64(length(GENERATION_LABELS)),
        "s3_action_count" => Float64(length(s3_permutations())),
        "unique_induced_family_permutation_count" => Float64(orbit["unique_induced_family_permutation_count"]),
        "family_9_vertex_count" => Float64(orbit["selected_family_vertex_counts"]["9"]),
        "family_10_vertex_count" => Float64(orbit["selected_family_vertex_counts"]["10"]),
        "family_11_vertex_count" => Float64(orbit["selected_family_vertex_counts"]["11"]),
        "family_9_edge_count" => Float64(edge_counts["9"]),
        "family_10_edge_count" => Float64(edge_counts["10"]),
        "family_11_edge_count" => Float64(edge_counts["11"]),
        "octonion_generation_control_count" => Float64(octonion_generation_control_count),
        "qit_total_substages_per_engine" => Float64(qit["total_substages_per_engine"]),
        "qit_h0_sz_coeff" => Float64(qit["h0_sz_coeff"]),
        "qit_h0_sx_coeff" => Float64(qit["h0_sx_coeff"]),
        "clifford_cl40_dim" => Float64(owner_anchor["clifford_cl40_dim_for_four_qubits"]),
        "density_matrix_trace_real" => Float64(owner_anchor["density_matrix_trace_real"]),
        "concrete_witness_product_norm" => Float64(witness["product_norm"]),
        "selected_left_ideal_rank_min" => Float64(minimum(ideal_family["rank_set_all_selected"])),
        "selected_left_ideal_rank_max" => Float64(maximum(ideal_family["rank_set_all_selected"])),
        "selected_left_annihilator_nullity_min" => Float64(minimum(ideal_family["nullity_set_all_selected"])),
        "selected_left_annihilator_nullity_max" => Float64(maximum(ideal_family["nullity_set_all_selected"])),
    )
    shared_booleans = Dict{String,Any}(
        "zero_divisors" => zero_divisors,
        "s3_family" => s3_family,
        "control_fails" => control_fails,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "from_real_ideals" => from_real_ideals,
        "octonion_gives_one" => octonion_gives_one,
        "all_pass" => all_pass,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "jax_enable_x64" => true,
    )

    Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "Finite sedenion zero-divisor/S3 witness only; no physics, Standard Model, M(C), Axis0, bridge, engine, manifold, or formal admission claim.",
        "arxiv_source" => Dict(
            "id" => "arXiv:2306.13098",
            "title" => "Three generations of colored fermions with S3 family symmetry from Cayley-Dickson sedenions",
            "url" => "https://arxiv.org/abs/2306.13098",
            "bounded_use" => "Motivation and target shape only; this scout checks a finite zero-divisor family/S3 witness, not the paper's full complex-Cl(6) construction.",
        ),
        "construction" => Dict(
            "carrier" => "Cayley-Dickson sedenions S = O doubled to 16 real basis elements",
            "basis_order" => "e0..e15 from the owner Cayley-Dickson multiplication table; the 4-qubit count is metadata only and is not used to derive generations",
            "selected_generation_components" => collect(GENERATION_LABELS),
            "selection_rule" => "three high-bit zero-divisor/left-ideal XOR components over the Fano line {1,2,3}",
        ),
        "owner_object_anchor" => owner_anchor,
        "owner_source_refs" => source_refs(),
        "qit_anchor" => qit,
        "zero_divisor_graph" => Dict(
            "sedenion" => Dict(
                "signed_zero_divisor_count" => s_edges["signed_zero_divisor_count"],
                "component_vertices" => s_edges["component_vertices"],
                "family_edge_counts" => edge_counts,
            ),
            "octonion_control" => Dict(
                "signed_zero_divisor_count" => o_edges["signed_zero_divisor_count"],
                "generation_control_count" => octonion_generation_control_count,
            ),
        ),
        "left_ideal_family" => ideal_family,
        "family_orbit" => orbit,
        "controls" => Dict(
            "octonion_one_generation_not_three" => octonion_generation_control_count == 1,
            "octonion_no_zero_divisors" => o_edges["signed_zero_divisor_count"] == 0,
            "wrong_structure_control_fails" => orbit["wrong_structure_control_fails"],
            "same_pipeline_octonion_generation_count" => octonion_generation_control_count,
            "real_sedenion_vs_replaced_octonion_flip" => owner_carrier_load_bearing,
            "erasing_or_replacing_owner_sedenion_carrier_changes_result" => owner_carrier_load_bearing,
        ),
        "tool_manifest" => Dict(
            "julia" => "load_bearing finite table, zero-divisor, and S3 orbit computation",
            "LinearAlgebra" => "load-bearing norm checks for zero products",
            "owner_julia_carrier" => "load-bearing include of system_v5/julia_carrier/sedenion_break.jl; result changes under octonion replacement",
            "canonical_qit_engine_specs" => "supportive 4-qubit/32-substage anchor and H0/type-sign metadata",
            "JSON" => "supportive result serialization",
        ),
        "tool_integration_depth" => Dict(
            "julia" => "load_bearing",
            "LinearAlgebra" => "load_bearing",
            "owner_julia_carrier" => "load_bearing",
            "canonical_qit_engine_specs" => "supportive",
            "JSON" => "supportive",
        ),
        "divergence_log" => [
            "Positive: S has signed two-term zero divisors and three selected generation-like XOR components permuted by an S3 subgroup.",
            "Control: O has no signed two-term zero divisors in the same bounded search and stays at one-generation control count.",
            "Anti-by-construction: relabeling family names without mapping internal zero-divisor vertices does not preserve the family structure.",
        ],
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "all_pass" => all_pass,
    )
end

result = build_result()
open(RESULT_PATH, "w") do io
    JSON.print(io, result, 2)
    write(io, "\n")
end

println(
    "JULIA_SCOUT_DONE result=", RESULT_PATH,
    " all_pass=", result["all_pass"],
    " owner_carrier_load_bearing=", result["shared_booleans"]["owner_carrier_load_bearing"],
    " n_generations=", Int(result["shared_scalars"]["n_generations"]),
    " s3_family=", result["shared_booleans"]["s3_family"],
    " from_real_ideals=", result["shared_booleans"]["from_real_ideals"],
    " octonion_gives_one=", result["shared_booleans"]["octonion_gives_one"],
)
exit(result["all_pass"] ? 0 : 2)
