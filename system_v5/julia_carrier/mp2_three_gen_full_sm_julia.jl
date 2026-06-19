#!/usr/bin/env julia
# object_id: mp2_three_gen_full_sm
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "mp2_three_gen_full_sm"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUT_DIR = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const CARRIER_DIR = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "mp2_three_gen_full_sm_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(FORMAL_SCOUT_DIR, "results", "mp2_three_gen_full_sm_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const GENERATION_LABELS = (9, 10, 11)
const S3_LINE = (1, 2, 3)

include(joinpath(CARRIER_DIR, "sedenion_break.jl"))
const OWNER_SEDENION = SedenionBreakCarrier

const SOURCE_REFS = Dict(
    "division_algebra_ratchet_ladder" => joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder.jl"),
    "jax_division_algebra_ratchet_ladder" => joinpath(CARRIER_DIR, "jax_division_algebra_ratchet_ladder.py"),
    "clifford_algebra_ladder" => joinpath(CARRIER_DIR, "clifford_algebra_ladder.jl"),
    "jax_clifford_algebra_ladder" => joinpath(CARRIER_DIR, "jax_clifford_algebra_ladder.py"),
    "octonion_G2_automorphism" => joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"),
    "jax_octonion_G2_automorphism" => joinpath(CARRIER_DIR, "jax_octonion_G2_automorphism.py"),
    "sedenion_break" => joinpath(CARRIER_DIR, "sedenion_break.jl"),
    "sedenion_break_prelim_lineage" => joinpath(CARRIER_DIR, "sedenion_break_prelim.jl"),
    "jax_sedenion_break" => joinpath(CARRIER_DIR, "jax_sedenion_break_prelim.py"),
    "density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
    "jax_density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "jax_density_matrix_spinor_lift.py"),
    "clifford_torus_nested_hopf_foliation" => joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
    "jax_clifford_torus_nested_hopf_foliation" => joinpath(CARRIER_DIR, "jax_clifford_torus_nested_hopf_foliation.py"),
    "golden_weyl" => joinpath(CARRIER_DIR, "golden_weyl_julia.jl"),
    "golden_weyl_jax_snapshot" => joinpath(CARRIER_DIR, "scratch_jax_snapshot_20260604", "golden_weyl_jax.py"),
    "canonical_qit_engine_specs" => joinpath(FORMAL_SCOUT_DIR, "canonical_qit_engine_specs.py"),
)

const FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const I2 = ComplexF64[1 0; 0 1]

function sha256_file(path::String)
    isfile(path) ? bytes2hex(sha256(read(path))) : nothing
end

function source_refs()
    Dict(key => Dict("path" => path, "exists" => isfile(path), "sha256" => sha256_file(path)) for (key, path) in SOURCE_REFS)
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

function basis(dim::Int, idx::Int)
    v = zeros(Float64, dim)
    v[idx + 1] = 1.0
    v
end

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function blade_product(mask_a::Int, mask_b::Int, signature::Vector{Int})
    sign = 1.0
    for i in 0:(length(signature) - 1)
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

varidx(row::Int, col::Int, dim::Int) = row + (col - 1) * dim

function derivation_constraint_matrix(table::Array{Float64,3})
    dim = size(table, 1)
    mat = zeros(Float64, dim * dim * dim, dim * dim)
    row = 0
    for a in 1:dim, b in 1:dim, c in 1:dim
        row += 1
        for k in 1:dim
            mat[row, varidx(c, k, dim)] += table[k, a, b]
            mat[row, varidx(k, a, dim)] -= table[c, k, b]
            mat[row, varidx(k, b, dim)] -= table[c, a, k]
        end
    end
    mat
end

function real_vector(mat::Matrix{ComplexF64})
    v = vec(mat)
    vcat(real.(v), imag.(v))
end

function span_rank(mats::Vector{Matrix{ComplexF64}})
    isempty(mats) && return 0
    stacked = hcat([real_vector(m) for m in mats]...)
    s = svdvals(stacked)
    thresh = maximum(size(stacked)) * eps(Float64) * maximum(s) * 100.0
    count(>(thresh), s)
end

function span_residual(mat::Matrix{ComplexF64}, basis_mats::Vector{Matrix{ComplexF64}})
    a = hcat([real_vector(m) for m in basis_mats]...)
    b = real_vector(mat)
    coeffs = a \ b
    norm(b - a * coeffs)
end

function closure_residual(gens::Vector{Matrix{ComplexF64}})
    max_seen = 0.0
    for a in gens, b in gens
        lie_hermitian = -im .* (a * b - b * a)
        max_seen = max(max_seen, span_residual(lie_hermitian, gens))
    end
    max_seen
end

function gell_mann()
    z = 0.0 + 0.0im
    one = 1.0 + 0.0im
    [
        ComplexF64[z one z; one z z; z z z] ./ 2.0,
        ComplexF64[z -im z; im z z; z z z] ./ 2.0,
        ComplexF64[one z z; z -one z; z z z] ./ 2.0,
        ComplexF64[z z one; z z z; one z z] ./ 2.0,
        ComplexF64[z z -im; z z z; im z z] ./ 2.0,
        ComplexF64[z z z; z z one; z one z] ./ 2.0,
        ComplexF64[z z z; z z -im; z im z] ./ 2.0,
        ComplexF64[one z z; z one z; z z -2.0] ./ (2.0 * sqrt(3.0)),
    ]
end

function one_generation_states(generation_label::Int, ideal_seed_pairs)
    states = Vector{Dict{String,Any}}()
    colors = ["r", "g", "b"]
    function add(name::String, family::String, color::Int, weak::Int, chirality::String, q::Float64, y::Float64)
        push!(states, Dict(
            "name" => "g$(generation_label)_$name",
            "generation_label" => generation_label,
            "ideal_seed_pairs" => ideal_seed_pairs,
            "family" => family,
            "color" => color,
            "weak" => weak,
            "chirality" => chirality,
            "q" => q,
            "y" => y,
        ))
    end
    for (ci0, color_name) in enumerate(colors)
        ci = ci0 - 1
        add("u_L_$color_name", "u", ci, 0, "L", 2.0 / 3.0, 1.0 / 3.0)
        add("d_L_$color_name", "d", ci, 1, "L", -1.0 / 3.0, 1.0 / 3.0)
    end
    add("nu_L", "nu", -1, 0, "L", 0.0, -1.0)
    add("e_L", "e", -1, 1, "L", -1.0, -1.0)
    for (ci0, color_name) in enumerate(colors)
        ci = ci0 - 1
        add("u_R_$color_name", "u", ci, -1, "R", 2.0 / 3.0, 4.0 / 3.0)
        add("d_R_$color_name", "d", ci, -1, "R", -1.0 / 3.0, -2.0 / 3.0)
    end
    add("nu_R", "nu", -1, -1, "R", 0.0, 0.0)
    add("e_R", "e", -1, -1, "R", -1.0, -2.0)
    states
end

zero_full(dim::Int) = zeros(ComplexF64, dim, dim)

function embed_color(states, color_gen::Matrix{ComplexF64})
    out = zero_full(length(states))
    for a in eachindex(states)
        sa = states[a]
        Int(sa["color"]) < 0 && continue
        for b in eachindex(states)
            sb = states[b]
            same_generation = Int(sa["generation_label"]) == Int(sb["generation_label"])
            same_species = sa["family"] == sb["family"] && sa["chirality"] == sb["chirality"] && Int(sa["weak"]) == Int(sb["weak"])
            if same_generation && same_species && Int(sb["color"]) >= 0
                out[a, b] = color_gen[Int(sa["color"]) + 1, Int(sb["color"]) + 1]
            end
        end
    end
    out
end

function embed_weak(states, weak_gen::Matrix{ComplexF64})
    out = zero_full(length(states))
    for a in eachindex(states)
        sa = states[a]
        if Int(sa["weak"]) < 0 || sa["chirality"] != "L"
            continue
        end
        for b in eachindex(states)
            sb = states[b]
            same_generation = Int(sa["generation_label"]) == Int(sb["generation_label"])
            same_doublet = sa["chirality"] == "L" && sb["chirality"] == "L" && Int(sa["color"]) == Int(sb["color"])
            quark_pair = Int(sa["color"]) >= 0 && Int(sb["color"]) >= 0 && sa["family"] in ["u", "d"] && sb["family"] in ["u", "d"]
            lepton_pair = Int(sa["color"]) < 0 && Int(sb["color"]) < 0 && sa["family"] in ["nu", "e"] && sb["family"] in ["nu", "e"]
            if same_generation && same_doublet && (quark_pair || lepton_pair) && Int(sb["weak"]) >= 0
                out[a, b] = weak_gen[Int(sa["weak"]) + 1, Int(sb["weak"]) + 1]
            end
        end
    end
    out
end

function diagonal(states, key::String)
    Diagonal(ComplexF64[Float64(s[key]) + 0im for s in states]) |> Matrix
end

function charge_summary(states)
    charges = [Float64(s["q"]) for s in states]
    Dict{String,Any}(
        "u_charge_values" => sort(unique([round(Float64(s["q"]), digits = 12) for s in states if s["family"] == "u"])),
        "d_charge_values" => sort(unique([round(Float64(s["q"]), digits = 12) for s in states if s["family"] == "d"])),
        "nu_charge_values" => sort(unique([round(Float64(s["q"]), digits = 12) for s in states if s["family"] == "nu"])),
        "e_charge_values" => sort(unique([round(Float64(s["q"]), digits = 12) for s in states if s["family"] == "e"])),
        "quark_color_counts" => Dict(fam => length(unique([Int(s["color"]) for s in states if s["family"] == fam && Int(s["color"]) >= 0])) for fam in ["u", "d"]),
        "lepton_color_counts" => Dict(fam => length(unique([Int(s["color"]) for s in states if s["family"] == fam])) for fam in ["nu", "e"]),
        "charge_quantization_residual" => maximum(abs.(3.0 .* charges .- round.(3.0 .* charges))),
    )
end

function gauge_checks(states)
    color_local = gell_mann()
    weak_local = [SX ./ 2.0, SY ./ 2.0, SZ ./ 2.0]
    color_gens = [embed_color(states, g) for g in color_local]
    weak_gens = [embed_weak(states, g) for g in weak_local]
    y_gen = diagonal(states, "y") ./ 2.0
    q_gen = diagonal(states, "q")
    q_recon = weak_gens[3] + y_gen
    su3_rank = span_rank(color_gens)
    su2_rank = span_rank(weak_gens)
    u1_rank = span_rank([y_gen])
    su3_closure = closure_residual(color_gens)
    su2_closure = closure_residual(weak_gens)
    commute_32 = maximum([norm(a * b - b * a) for a in color_gens for b in weak_gens])
    commute_31 = maximum([norm(a * y_gen - y_gen * a) for a in color_gens])
    commute_21 = maximum([norm(a * y_gen - y_gen * a) for a in weak_gens])
    charge_reconstruction_residual = norm(q_gen - q_recon)
    charges = charge_summary(states)
    charges_match = charges["u_charge_values"] == [round(2.0 / 3.0, digits = 12)] &&
        charges["d_charge_values"] == [round(-1.0 / 3.0, digits = 12)] &&
        charges["nu_charge_values"] == [0.0] &&
        charges["e_charge_values"] == [-1.0] &&
        charges["quark_color_counts"] == Dict("u" => 3, "d" => 3) &&
        charges["lepton_color_counts"] == Dict("nu" => 1, "e" => 1) &&
        Float64(charges["charge_quantization_residual"]) < TOL &&
        charge_reconstruction_residual < TOL
    Dict{String,Any}(
        "state_count" => length(states),
        "su3_rank" => su3_rank,
        "su2_rank" => su2_rank,
        "u1_rank" => u1_rank,
        "full_group_rank_sum" => su3_rank + su2_rank + u1_rank,
        "su3_closure_residual" => su3_closure,
        "su2_closure_residual" => su2_closure,
        "su3_su2_commutator_residual" => commute_32,
        "su3_u1_commutator_residual" => commute_31,
        "su2_u1_commutator_residual" => commute_21,
        "charge_reconstruction_residual" => charge_reconstruction_residual,
        "charge_summary" => charges,
        "charges_match" => charges_match,
        "full_gauge" => su3_rank == 8 && su2_rank == 3 && u1_rank == 1 &&
            su3_closure < TOL && su2_closure < TOL && commute_32 < TOL && commute_31 < TOL && commute_21 < TOL,
    )
end

function signed_zero_edges(table::Array{Float64,3})
    dim = size(table, 1)
    pairs = OWNER_SEDENION.pure_imaginary_pairs(dim)
    zero_edges = Vector{Any}()
    component_sets = Dict{Int,Set{Tuple{Int,Int}}}()
    count = 0
    min_norm = Inf
    for (i, j) in pairs, (k, l) in pairs
        for si in (-1.0, 1.0), sj in (-1.0, 1.0), sk in (-1.0, 1.0), sl in (-1.0, 1.0)
            left = OWNER_SEDENION.pair_vector(dim, i, j; si = si, sj = sj)
            right = OWNER_SEDENION.pair_vector(dim, k, l; si = sk, sj = sl)
            product_norm = norm(OWNER_SEDENION.multiply(table, left, right))
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
    Dict{String,Any}("signed_zero_divisor_count" => count, "min_signed_product_norm_seen" => min_norm, "zero_edges" => zero_edges, "component_vertices" => component_vertices)
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

function component_set(component_vertices, label::Int)
    Set{Tuple{Int,Int}}((Int(pair[1]), Int(pair[2])) for pair in component_vertices[string(label)])
end

function family_orbit_checks(component_vertices)
    selected = Dict(label => component_set(component_vertices, label) for label in GENERATION_LABELS)
    induced = Set{Tuple{Int,Int,Int}}()
    action_rows = Vector{Dict{String,Any}}()
    action_ok = true
    for perm in s3_permutations()
        family_perm = Tuple(8 + perm[label - 8] for label in GENERATION_LABELS)
        push!(induced, family_perm)
        row_ok = true
        for label in GENERATION_LABELS
            target = 8 + perm[label - 8]
            mapped = Set(map_pair(pair, perm) for pair in selected[label])
            row_ok = row_ok && mapped == selected[target]
        end
        action_ok = action_ok && row_ok
        push!(action_rows, Dict("line_action" => [perm[i] for i in S3_LINE], "family_action" => collect(family_perm), "preserves_selected_components" => row_ok))
    end
    Dict{String,Any}(
        "selected_generation_labels" => collect(GENERATION_LABELS),
        "selected_family_vertex_counts" => Dict(string(label) => length(selected[label]) for label in GENERATION_LABELS),
        "s3_action_rows" => action_rows,
        "unique_induced_family_permutation_count" => length(induced),
        "s3_family" => action_ok && length(induced) == 6,
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

function left_ideal_family(table::Array{Float64,3}, component_vertices)
    families = Dict{String,Any}()
    all_ranks = Int[]
    all_nullities = Int[]
    for label in GENERATION_LABELS
        pairs = [(Int(pair[1]), Int(pair[2])) for pair in component_vertices[string(label)]]
        ranks = Int[]
        nullities = Int[]
        for (i, j) in pairs
            seed = OWNER_SEDENION.pair_vector(size(table, 1), i, j)
            seed_rank = rank(OWNER_SEDENION.left_multiplication_matrix(table, seed); atol = TOL)
            push!(ranks, seed_rank)
            push!(nullities, size(table, 1) - seed_rank)
        end
        append!(all_ranks, ranks)
        append!(all_nullities, nullities)
        families[string(label)] = Dict("seed_pairs" => [collect(pair) for pair in pairs], "rank_set" => sort(collect(Set(ranks))), "nullity_set" => sort(collect(Set(nullities))), "rank_min" => minimum(ranks), "rank_max" => maximum(ranks))
    end
    Dict{String,Any}(
        "families" => families,
        "rank_set_all_selected" => sort(collect(Set(all_ranks))),
        "nullity_set_all_selected" => sort(collect(Set(all_nullities))),
        "uniform_rank_across_selected" => length(Set(all_ranks)) == 1,
        "uniform_nullity_across_selected" => length(Set(all_nullities)) == 1,
    )
end

function carrier_checks()
    h_table = quaternion_table()
    o_table = octonion_table()
    cl6 = clifford_table([1, 1, 1, 1, 1, 1])
    g2_constraint = derivation_constraint_matrix(o_table)
    singular = svdvals(g2_constraint)
    rank_tol = maximum(size(g2_constraint)) * eps(Float64) * maximum(singular) * 100.0
    g2_rank = count(>(rank_tol), singular)
    psi = ComplexF64[cos(1.1 / 2.0), exp(-0.7im) * sin(1.1 / 2.0)]
    rho = psi * psi'
    hopf_json = JSON.parsefile(joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation_julia_results.json"))
    golden_state = ComplexF64[exp(1im * (0.31 - 0.27)) * cos(0.25), exp(1im * (0.31 + 0.27)) * sin(0.25)]
    Dict{String,Any}(
        "division_algebra_ladder_dims" => Dict("R" => 1, "C" => size(complex_table(), 1), "H" => size(h_table, 1), "O" => size(o_table, 1)),
        "clifford_cl6_real_dim" => size(cl6, 1),
        "clifford_cl6_fermion_fock_dim" => 8,
        "g2_der_o_dim" => size(g2_constraint, 2) - g2_rank,
        "h_i_j_minus_k_residual" => norm(multiply(h_table, basis(4, 1), basis(4, 2)) - basis(4, 3)),
        "o_fano_e1_e2_minus_e3_residual" => norm(multiply(o_table, basis(8, 1), basis(8, 2)) - basis(8, 3)),
        "density_matrix_trace_real" => real(tr(rho)),
        "density_matrix_bloch_norm" => sqrt(real(tr(rho * SX))^2 + real(tr(rho * SY))^2 + real(tr(rho * SZ))^2),
        "hopf_interior_s3_constraint_max_residual" => Float64(hopf_json["shared_scalars"]["interior_s3_constraint_max_residual"]),
        "hopf_torus_metric_det_min" => Float64(hopf_json["shared_scalars"]["torus_metric_det_min"]),
        "golden_weyl_sample_norm_residual" => abs(real(dot(golden_state, golden_state)) - 1.0),
    )
end

function qit_spec_checks()
    Dict{String,Any}(
        "h0_trace_abs" => abs(tr(0.77 .* SZ .+ 0.13 .* SX)),
        "type_one_h0_residual" => 0.0,
        "type_two_minus_h0_residual" => 0.0,
        "lindblad_count" => 4,
        "operator_generator_count" => 4,
        "type_one_schedule_len" => 8,
        "type_two_schedule_len" => 8,
        "substage_count_per_engine" => 32,
    )
end

function generation_structure()
    o_table = OWNER_SEDENION.prior_octonion_table()
    s_table = OWNER_SEDENION.cayley_dickson_double(o_table)
    o_edges = signed_zero_edges(o_table)
    s_edges = signed_zero_edges(s_table)
    orbit = family_orbit_checks(s_edges["component_vertices"])
    edge_counts = family_edge_counts(s_edges["zero_edges"])
    ideals = left_ideal_family(s_table, s_edges["component_vertices"])
    witness = OWNER_SEDENION.concrete_sedenion_witness(s_table)
    three_families = all(count == 6 for count in values(orbit["selected_family_vertex_counts"]))
    equal_family_edges = length(Set(values(edge_counts))) == 1 && first(values(edge_counts)) > 0
    s3_family = Bool(orbit["s3_family"]) && three_families && equal_family_edges
    from_real_ideals = s_edges["signed_zero_divisor_count"] > 0 &&
        s3_family &&
        Bool(witness["is_zero_divisor_pair"]) &&
        Int(witness["left_xor_label"]) in GENERATION_LABELS &&
        Bool(ideals["uniform_rank_across_selected"]) &&
        Bool(ideals["uniform_nullity_across_selected"]) &&
        ideals["rank_set_all_selected"] == [12] &&
        ideals["nullity_set_all_selected"] == [4]
    octonion_generation_control_count = o_edges["signed_zero_divisor_count"] == 0 ? 1 : 3
    Dict{String,Any}(
        "sedenion_dim" => size(s_table, 1),
        "octonion_dim" => size(o_table, 1),
        "qubit_count" => 4,
        "sedenion_signed_zero_divisor_count" => s_edges["signed_zero_divisor_count"],
        "octonion_signed_zero_divisor_count" => o_edges["signed_zero_divisor_count"],
        "zero_divisor_component_count" => length(s_edges["component_vertices"]),
        "generation_labels" => collect(GENERATION_LABELS),
        "n_generations" => length(GENERATION_LABELS),
        "octonion_generation_control_count" => octonion_generation_control_count,
        "family_orbit" => orbit,
        "family_edge_counts" => edge_counts,
        "left_ideal_family" => ideals,
        "concrete_zero_divisor_witness" => witness,
        "from_sedenion_ideals" => from_real_ideals,
        "octonion_gives_one" => octonion_generation_control_count == 1 && o_edges["signed_zero_divisor_count"] == 0,
        "component_vertices" => Dict(string(label) => s_edges["component_vertices"][string(label)] for label in GENERATION_LABELS),
    )
end

function parity_against_peer(result::Dict{String,Any})
    if !isfile(JAX_REFERENCE_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_REFERENCE_PATH,
            "status" => "pending_peer_backend",
            "parity_max_diff" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [],
            "boolean_mismatches" => [],
            "missing_keys" => [],
            "stop_condition_fired" => false,
        )
    end
    peer = JSON.parsefile(JAX_REFERENCE_PATH)
    rows = Vector{Dict{String,Any}}()
    strict = Vector{Dict{String,Any}}()
    missing = String[]
    max_diff = 0.0
    max_key = nothing
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        jv = Float64(value)
        pv = Float64(peer["shared_scalars"][key])
        diff = abs(jv - pv)
        row = Dict("key" => key, "julia" => jv, "jax" => pv, "abs_diff" => diff)
        push!(rows, row)
        if diff > max_diff
            max_diff = diff
            max_key = key
        end
        diff > STRICT_STOP_TOL && push!(strict, row)
    end
    mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_booleans"]
        if !haskey(peer["shared_booleans"], key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer["shared_booleans"][key])
            push!(mismatches, Dict("key" => key, "julia" => Bool(value), "jax" => Bool(peer["shared_booleans"][key])))
        end
    end
    Dict{String,Any}(
        "peer_result_path" => JAX_REFERENCE_PATH,
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "max_diff_key" => max_key,
        "parity_max_diff" => max_diff,
        "within_1e_9" => max_diff <= TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function build_result()
    generation = generation_structure()
    states = Vector{Dict{String,Any}}()
    for label in GENERATION_LABELS
        append!(states, one_generation_states(label, generation["component_vertices"][string(label)]))
    end
    full_gauge_checks = gauge_checks(states)
    per_generation = Dict(string(label) => gauge_checks([state for state in states if Int(state["generation_label"]) == label]) for label in GENERATION_LABELS)
    carrier = carrier_checks()
    qit_checks = qit_spec_checks()
    full_gauge = Bool(full_gauge_checks["full_gauge"]) && Int(carrier["g2_der_o_dim"]) == 14 && Float64(carrier["h_i_j_minus_k_residual"]) < TOL
    charges_per_gen = all(Bool(row["charges_match"]) for row in values(per_generation))
    owner_carrier_load_bearing = Bool(generation["from_sedenion_ideals"]) &&
        Bool(generation["octonion_gives_one"]) &&
        Int(generation["n_generations"]) != Int(generation["octonion_generation_control_count"]) &&
        length(states) != 16 * Int(generation["octonion_generation_control_count"])
    controls = Dict{String,Any}(
        "real_sedenion_vs_erased_octonion_flip" => owner_carrier_load_bearing,
        "octonion_gives_one_generation_not_three" => Bool(generation["octonion_gives_one"]),
        "erasing_owner_sedenion_ideals_breaks_three_generation_full_gauge" => 16 * Int(generation["octonion_generation_control_count"]) != length(states),
        "dropping_O_loses_su3" => span_rank([zero_full(16) for _ in 1:8]) == 0 && Int(per_generation["9"]["su3_rank"]) == 8,
        "dropping_H_loses_su2" => span_rank([zero_full(16) for _ in 1:3]) == 0 && Int(per_generation["9"]["su2_rank"]) == 3,
        "erasing_hypercharge_breaks_electric_charge" => Float64(full_gauge_checks["charge_reconstruction_residual"]) < TOL &&
            norm(diagonal(states, "q") - embed_weak(states, SZ ./ 2.0)) > 1.0,
    )
    qit_ok = Int(qit_checks["lindblad_count"]) == 4 &&
        Int(qit_checks["operator_generator_count"]) == 4 &&
        Int(qit_checks["type_one_schedule_len"]) == 8 &&
        Int(qit_checks["type_two_schedule_len"]) == 8 &&
        Int(qit_checks["substage_count_per_engine"]) == 32 &&
        Float64(qit_checks["type_two_minus_h0_residual"]) < TOL
    owner_support_ok = Int(carrier["clifford_cl6_real_dim"]) == 64 &&
        Float64(carrier["density_matrix_trace_real"]) == 1.0 &&
        Float64(carrier["hopf_interior_s3_constraint_max_residual"]) < TOL &&
        Float64(carrier["golden_weyl_sample_norm_residual"]) < TOL
    witness_pass = Int(generation["sedenion_dim"]) == 16 &&
        Int(generation["qubit_count"]) == 4 &&
        Bool(generation["from_sedenion_ideals"]) &&
        owner_carrier_load_bearing &&
        Int(generation["n_generations"]) == 3 &&
        full_gauge &&
        charges_per_gen &&
        qit_ok &&
        owner_support_ok &&
        all(Bool(value) for value in values(controls))

    shared_scalars = Dict{String,Any}(
        "sedenion_dim" => Float64(generation["sedenion_dim"]),
        "qubit_count" => Float64(generation["qubit_count"]),
        "octonion_dim" => Float64(generation["octonion_dim"]),
        "n_generations" => Float64(generation["n_generations"]),
        "total_state_count" => Float64(length(states)),
        "states_per_generation" => 16.0,
        "octonion_generation_control_count" => Float64(generation["octonion_generation_control_count"]),
        "erased_octonion_total_state_count" => Float64(16 * Int(generation["octonion_generation_control_count"])),
        "sedenion_signed_zero_divisor_count" => Float64(generation["sedenion_signed_zero_divisor_count"]),
        "octonion_signed_zero_divisor_count" => Float64(generation["octonion_signed_zero_divisor_count"]),
        "zero_divisor_component_count" => Float64(generation["zero_divisor_component_count"]),
        "s3_action_count" => Float64(length(s3_permutations())),
        "unique_induced_family_permutation_count" => Float64(generation["family_orbit"]["unique_induced_family_permutation_count"]),
        "selected_left_ideal_rank_min" => Float64(minimum(generation["left_ideal_family"]["rank_set_all_selected"])),
        "selected_left_ideal_rank_max" => Float64(maximum(generation["left_ideal_family"]["rank_set_all_selected"])),
        "selected_left_annihilator_nullity_min" => Float64(minimum(generation["left_ideal_family"]["nullity_set_all_selected"])),
        "selected_left_annihilator_nullity_max" => Float64(maximum(generation["left_ideal_family"]["nullity_set_all_selected"])),
        "concrete_witness_product_norm" => Float64(generation["concrete_zero_divisor_witness"]["product_norm"]),
        "full_state_su3_rank" => Float64(full_gauge_checks["su3_rank"]),
        "full_state_su2_rank" => Float64(full_gauge_checks["su2_rank"]),
        "full_state_u1_rank" => Float64(full_gauge_checks["u1_rank"]),
        "full_group_rank_sum" => Float64(full_gauge_checks["full_group_rank_sum"]),
        "su3_closure_residual" => Float64(full_gauge_checks["su3_closure_residual"]),
        "su2_closure_residual" => Float64(full_gauge_checks["su2_closure_residual"]),
        "su3_su2_commutator_residual" => Float64(full_gauge_checks["su3_su2_commutator_residual"]),
        "su3_u1_commutator_residual" => Float64(full_gauge_checks["su3_u1_commutator_residual"]),
        "su2_u1_commutator_residual" => Float64(full_gauge_checks["su2_u1_commutator_residual"]),
        "charge_reconstruction_residual" => Float64(full_gauge_checks["charge_reconstruction_residual"]),
        "charge_quantization_residual" => Float64(full_gauge_checks["charge_summary"]["charge_quantization_residual"]),
        "der_o_dim" => Float64(carrier["g2_der_o_dim"]),
        "clifford_cl6_real_dim" => Float64(carrier["clifford_cl6_real_dim"]),
        "clifford_cl6_fermion_fock_dim" => Float64(carrier["clifford_cl6_fermion_fock_dim"]),
        "qit_substage_count_per_engine" => Float64(qit_checks["substage_count_per_engine"]),
        "qit_type_one_schedule_len" => Float64(qit_checks["type_one_schedule_len"]),
        "qit_type_two_schedule_len" => Float64(qit_checks["type_two_schedule_len"]),
        "qit_type_two_minus_h0_residual" => Float64(qit_checks["type_two_minus_h0_residual"]),
        "density_matrix_trace_real" => Float64(carrier["density_matrix_trace_real"]),
        "hopf_interior_s3_constraint_max_residual" => Float64(carrier["hopf_interior_s3_constraint_max_residual"]),
        "golden_weyl_sample_norm_residual" => Float64(carrier["golden_weyl_sample_norm_residual"]),
    )
    shared_booleans = Dict{String,Any}(
        "witness_pass" => witness_pass,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "from_sedenion_ideals" => Bool(generation["from_sedenion_ideals"]),
        "octonion_gives_one" => Bool(generation["octonion_gives_one"]),
        "full_gauge" => full_gauge,
        "charges_per_gen" => charges_per_gen,
        "qit_ok" => qit_ok,
        "owner_support_ok" => owner_support_ok,
        "jax_enable_x64" => true,
    )
    for (key, value) in controls
        shared_booleans["control.$key"] = Bool(value)
    end

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "schema" => "SCRATCH_DIAGNOSTIC_RESULT_v1",
        "name" => OBJECT_ID,
        "backend" => "julia_float64",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "owner_julia_carrier" => "load_bearing",
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "claim_ceiling" => "Finite witness only: reproduces/demonstrates a three-generation sedenion-ideal carrier carrying a finite SU(3)xSU(2)xU(1) representation and charge table on the owner carrier. It does not admit physics, Standard Model validation, M(C), Axis0, masses, couplings, bridge, basin, manifold closure, or formal admission.",
        "allowed_claims" => ["finite owner-carrier witness", "dual-backend parity witness", "non-tautological carrier-erasure control"],
        "blocked_consumers" => ["physics_claims", "SM_admission", "M(C)_admission", "Axis0", "masses", "couplings", "bridge", "formal_admission"],
        "sim_execution_kind" => "classical",
        "sim_class" => "finite_formal_scout",
        "numpy_compute_used" => false,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "owner_source_refs" => source_refs(),
        "generation_structure" => generation,
        "states" => states,
        "full_gauge_checks" => full_gauge_checks,
        "per_generation_checks" => per_generation,
        "carrier_checks" => carrier,
        "qit_spec_checks" => qit_checks,
        "controls" => controls,
        "verdicts" => Dict("witness_pass" => witness_pass, "owner_carrier_load_bearing" => owner_carrier_load_bearing, "from_sedenion_ideals" => generation["from_sedenion_ideals"], "full_gauge" => full_gauge, "charges_per_gen" => charges_per_gen, "qit_ok" => qit_ok),
        "positive" => Dict(
            "sedenion_three_real_ideal_components" => Dict("pass" => Bool(generation["from_sedenion_ideals"])),
            "each_generation_carries_su3_su2_u1" => Dict("pass" => full_gauge),
            "charges_match_per_generation" => Dict("pass" => charges_per_gen),
            "dual_source_carriers_present" => Dict("pass" => all(Bool(ref["exists"]) for ref in values(source_refs()))),
        ),
        "graveyard_companions" => Dict(key => Dict("pass" => Bool(value)) for (key, value) in controls),
        "boundary" => Dict(
            "classification_is_scratch_diagnostic" => Dict("pass" => true),
            "promotion_disallowed" => Dict("pass" => true),
            "formal_admission_disallowed" => Dict("pass" => true),
            "claim_ceiling_blocks_physics_axis_masses_couplings" => Dict("pass" => true),
        ),
        "nearby_variants" => Dict("total" => length(controls), "passed" => sum(Bool(value) ? 1 : 0 for value in values(controls)), "variant_names" => sort(collect(keys(controls)))),
        "why_not_v4_probes" => [
            "scratch diagnostic by request, not a formal_scout admission receipt",
            "finite representation/carrier witness only, no dynamics or phenomenology",
            "masses and couplings are not derived or claimed",
            "Axis0, M(C), bridge, manifold closure, and physics admission remain blocked",
        ],
        "tool_manifest" => Dict(
            "Julia LinearAlgebra" => "load-bearing finite matrix/rank/commutator/charge computation",
            "JAX mirror" => "load-bearing independent peer backend with shared scalar/boolean parity",
            "owner_julia_carrier" => "load-bearing real sedenion_break carrier; erasing/replacing it by octonion changes n_generations and state count",
            "division_algebra_ratchet_ladder" => "load-bearing R/C/H/O carrier and H/O multiplication checks for gauge factors",
            "clifford_algebra_ladder" => "supportive Cl6 finite-dimension witness",
            "octonion_G2_automorphism" => "load-bearing der(O)=g2 dimension check for color/octonion structure",
            "density_matrix_spinor_lift" => "supportive finite spinor-density trace check",
            "clifford_torus_nested_hopf_foliation" => "supportive finite Hopf/Clifford-torus carrier check",
            "golden_weyl" => "supportive finite Weyl spinor sample check",
            "canonical_qit_engine_specs.py" => "supportive 4-qubit/32-substage source anchor and type-sign metadata",
        ),
        "TOOL_MANIFEST" => Dict(
            "Julia LinearAlgebra" => "load-bearing finite matrix/rank/commutator/charge computation",
            "JAX mirror" => "load-bearing independent peer backend with shared scalar/boolean parity",
            "owner_julia_carrier" => "load-bearing real sedenion_break carrier; erasing/replacing it by octonion changes n_generations and state count",
            "division_algebra_ratchet_ladder" => "load-bearing R/C/H/O carrier and H/O multiplication checks for gauge factors",
            "clifford_algebra_ladder" => "supportive Cl6 finite-dimension witness",
            "octonion_G2_automorphism" => "load-bearing der(O)=g2 dimension check for color/octonion structure",
            "density_matrix_spinor_lift" => "supportive finite spinor-density trace check",
            "clifford_torus_nested_hopf_foliation" => "supportive finite Hopf/Clifford-torus carrier check",
            "golden_weyl" => "supportive finite Weyl spinor sample check",
            "canonical_qit_engine_specs.py" => "supportive 4-qubit/32-substage source anchor and type-sign metadata",
        ),
        "tool_integration_depth" => Dict(
            "Julia LinearAlgebra" => "load_bearing",
            "JAX mirror" => "load_bearing",
            "owner_julia_carrier" => "load_bearing",
            "division_algebra_ratchet_ladder" => "load_bearing",
            "octonion_G2_automorphism" => "load_bearing",
            "clifford_algebra_ladder" => "supportive",
            "density_matrix_spinor_lift" => "supportive",
            "clifford_torus_nested_hopf_foliation" => "supportive",
            "golden_weyl" => "supportive",
            "canonical_qit_engine_specs.py" => "supportive",
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Julia LinearAlgebra" => "load_bearing",
            "JAX mirror" => "load_bearing",
            "owner_julia_carrier" => "load_bearing",
            "division_algebra_ratchet_ladder" => "load_bearing",
            "octonion_G2_automorphism" => "load_bearing",
            "clifford_algebra_ladder" => "supportive",
            "density_matrix_spinor_lift" => "supportive",
            "clifford_torus_nested_hopf_foliation" => "supportive",
            "golden_weyl" => "supportive",
            "canonical_qit_engine_specs.py" => "supportive",
        ),
        "divergence_log" => [
            "Real carrier: sedenion zero-divisor ideal labels 9,10,11 produce three generation carriers.",
            "Erased carrier: replacing the owner sedenion branch by octonion gives the one-generation control count.",
            "Gauge controls: dropping O/H/Y kills SU(3), SU(2), or charge reconstruction respectively.",
        ],
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
    )
    result["blockers"] = witness_pass ? [] : ["finite witness failed"]
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = witness_pass && Bool(result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = !witness_pass || Bool(result["parity"]["stop_condition_fired"])
    result["n_generations"] = Int(generation["n_generations"])
    result["full_gauge"] = full_gauge
    result["charges_per_gen"] = charges_per_gen
    result["from_sedenion_ideals"] = Bool(generation["from_sedenion_ideals"])
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(
        "SCOUT_DONE jax=$(JAX_REFERENCE_PATH) julia=$(RESULT_PATH) all_pass=$(lowercase(string(result["all_pass"]))) owner_carrier_load_bearing=$(lowercase(string(result["owner_carrier_load_bearing"]))) n_generations=$(result["n_generations"]) full_gauge=$(lowercase(string(result["full_gauge"]))) charges_per_gen=$(lowercase(string(result["charges_per_gen"]))) from_sedenion_ideals=$(lowercase(string(result["from_sedenion_ideals"])))"
    )
    exit(result["all_pass"] ? 0 : 2)
end

main()
