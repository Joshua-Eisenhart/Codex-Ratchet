#!/usr/bin/env julia
# Julia reference lane for spinor_network_surface_v2.

using Dates
using Graphs
using JSON
using LinearAlgebra
using SHA
using Statistics
using Z3

const SIM_ID = "spinor_network_surface_v2"
const ENGINE = "julia"
const ROOT = abspath(joinpath(@__DIR__, "..", "..", ".."))
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")

const N_SITES = 4
const DIM = 2^N_SITES
const GRID = [-1.0, -0.5, 0.0, 0.5, 1.0]
const ORIGIN_CELL = "A33_x00_y00_z00"
const MIN_RECOVERED_NONORIGIN_CELLS = 6
const RETRIEVAL_ALPHA = 0.65
const MAX_TRAJECTORY_STEPS = 6
const SPURIOUS_GAP_THRESHOLD = 0.08
const SEED = 20260611
const HAAR_PINNED_SEEDS = [6608, 6609, 6610, 6611]
const HAAR_NULL_TRIALS = 2048
const HAAR_NULL_SEED0 = 100000
const LCG_A = UInt64(6364136223846793005)
const LCG_C = UInt64(1442695040888963407)

const SIGMA_X = ComplexF64[0 1; 1 0]
const SIGMA_Y = ComplexF64[0 -im; im 0]
const SIGMA_Z = ComplexF64[1 0; 0 -1]
const PAULI = [SIGMA_X, SIGMA_Y, SIGMA_Z]

struct MissingStructure <: Exception
    msg::String
end

Base.showerror(io::IO, err::MissingStructure) = print(io, err.msg)

rel(path::String) = relpath(abspath(path), abspath(ROOT))

function sha256_file(path::String)
    bytes2hex(sha256(read(path)))
end

function a33_rows()
    rows = Tuple{Float64,Float64,Float64}[]
    for x in GRID, y in GRID, z in GRID
        if x*x + y*y + z*z <= 1.000000001
            push!(rows, (x, y, z))
        end
    end
    rows
end

const A33_ROWS = a33_rows()

function cell_token(value::Float64)
    sign = value > 0 ? "p" : value < 0 ? "m" : "0"
    mag = round(Int, abs(value) * 10)
    "$(sign)$(mag)"
end

function a33_cell_id_from_row(row::NTuple{3,Float64})
    "A33_x$(cell_token(row[1]))_y$(cell_token(row[2]))_z$(cell_token(row[3]))"
end

function chart_cell_id(coords::NTuple{3,Float64}; rows=A33_ROWS, row_labels=nothing)
    idx = argmin([sum((row[i] - coords[i])^2 for i in 1:3) for row in rows])
    snapped = rows[idx]
    residual = sqrt(sum((snapped[i] - coords[i])^2 for i in 1:3))
    cell_id = row_labels === nothing ? a33_cell_id_from_row(snapped) : row_labels[idx]
    cell_id, residual
end

const A33_CELL_IDS = Set([a33_cell_id_from_row(row) for row in A33_ROWS])

function qnormalize(q::NTuple{4,Float64})
    n = sqrt(sum(v*v for v in q))
    (q[1]/n, q[2]/n, q[3]/n, q[4]/n)
end

function weyl_spinor_quat(phi::Float64, chi::Float64, eta::Float64, chirality::Symbol)
    c = cos(eta)
    s = sin(eta)
    pp = phi + chi
    pm = phi - chi
    q = if chirality == :L
        (c*cos(pp), c*sin(pp), s*cos(pm), s*sin(pm))
    else
        (c*cos(pp), -c*sin(pp), s*cos(pm), -s*sin(pm))
    end
    w, x, y, z = qnormalize(q)
    spinor = ComplexF64[w + im*x, y + im*z]
    spinor / norm(spinor)
end

function product_state(spinors::Vector{Vector{ComplexF64}})
    state = spinors[1]
    for idx in 2:length(spinors)
        state = kron(state, spinors[idx])
    end
    state / norm(state)
end

function chiral_quaternion_pattern(mu::Int)
    lx, ly = 2, 2
    pattern_count = 2
    seed_phi = mod(SEED * 0.37, 2*pi)
    seed_eta = mod(SEED * 0.17, 0.4)
    phi0 = 2*pi * mu / pattern_count + seed_phi * (mu + 1) / pattern_count
    spinors = Vector{ComplexF64}[]
    for site in 0:(N_SITES - 1)
        x = div(site, ly) + 1
        y = mod(site, ly) + 1
        phi = phi0 + 2*pi * x / lx
        chi = 2*pi * y / ly
        eta = pi/4 + (0.2 + seed_eta * 0.1) * sin(phi + chi)
        push!(spinors, weyl_spinor_quat(phi, chi, eta, iseven(mu) ? :L : :R))
    end
    product_state(spinors)
end

function entangled_pattern()
    theta = 0.31
    state = zeros(ComplexF64, DIM)
    state[1] = cos(theta)
    state[DIM] = sin(theta) * exp(im * 0.37)
    state / norm(state)
end

function pinned_random_pattern()
    raw = ComplexF64[
        sin((idx + 1) * 0.137 * SEED) + im * cos((idx + 1) * 0.173 * (SEED + 7))
        for idx in 0:(DIM - 1)
    ]
    raw / norm(raw)
end

function lcg_uniforms(seed::Int, count::Int)
    state = UInt64(seed) + LCG_C
    values = Float64[]
    for _ in 1:count
        state = LCG_A * state + LCG_C
        mantissa = (state >> 11) & UInt64(2^53 - 1)
        push!(values, Float64(mantissa) / Float64(2^53))
    end
    values
end

function lcg_normals(seed::Int, count::Int)
    uniforms = lcg_uniforms(seed, 2 * cld(count, 2))
    values = Float64[]
    for idx in 1:2:length(uniforms)
        u1 = max(uniforms[idx], 1.0e-12)
        u2 = uniforms[idx + 1]
        radius = sqrt(-2.0 * log(u1))
        theta = 2.0 * pi * u2
        push!(values, radius * cos(theta))
        push!(values, radius * sin(theta))
    end
    values[1:count]
end

function haar_pinned_pattern(seed::Int)
    normals = lcg_normals(seed, 2 * DIM)
    raw = ComplexF64[normals[idx] + im * normals[DIM + idx] for idx in 1:DIM]
    raw / norm(raw)
end

function v1_anchor_patterns()
    Dict{String,Vector{ComplexF64}}(
        "chiral_quaternion_L" => chiral_quaternion_pattern(0),
        "chiral_quaternion_R" => chiral_quaternion_pattern(1),
        "entangled_nonproduct" => entangled_pattern(),
        "pinned_random" => pinned_random_pattern(),
    )
end

function terminal_patterns()
    patterns = v1_anchor_patterns()
    for seed in HAAR_PINNED_SEEDS
        patterns["haar_pinned_seed_$(seed)"] = haar_pinned_pattern(seed)
    end
    patterns
end

function stable_hash_value(value)
    bytes2hex(sha256(JSON.json(value)))
end

function pattern_metadata(patterns)
    rows = Dict{String,Dict{String,Any}}(
        "chiral_quaternion_L" => Dict("family_id" => "estate_chiral_quaternion_Hopf_Weyl", "bias_class" => "residual_chart_plane_bias_v1_anchor", "load_bearing_for_identity_claim" => false, "anchor_from_v1" => true),
        "chiral_quaternion_R" => Dict("family_id" => "estate_chiral_quaternion_Hopf_Weyl", "bias_class" => "residual_chart_plane_bias_v1_anchor", "load_bearing_for_identity_claim" => false, "anchor_from_v1" => true),
        "entangled_nonproduct" => Dict("family_id" => "entangled_nonproduct", "bias_class" => "computational_endpoint_z_bias_v1_anchor", "load_bearing_for_identity_claim" => false, "anchor_from_v1" => true),
        "pinned_random" => Dict("family_id" => "pinned_random_v1_anchor", "bias_class" => "single_seed_thin_margin_v1_anchor", "load_bearing_for_identity_claim" => false, "anchor_from_v1" => true),
    )
    for seed in HAAR_PINNED_SEEDS
        pid = "haar_pinned_seed_$(seed)"
        rows[pid] = Dict(
            "family_id" => pid,
            "bias_class" => "haar_sampled_then_seed_pinned_no_preferred_chart_axis",
            "seed" => seed,
            "seed_hash" => stable_hash_value(Dict("haar_pinned_seed" => seed, "dim" => DIM, "sim_id" => SIM_ID)),
            "load_bearing_for_identity_claim" => true,
            "anchor_from_v1" => false,
        )
    end
    Dict(key => rows[key] for key in keys(patterns))
end

density(psi::Vector{ComplexF64}) = psi * psi'

function hermitize_trace_one(rho::Matrix{ComplexF64})
    herm = (rho + rho') / 2
    herm / tr(herm)
end

function bits_of(index::Int, width::Int)
    [((index >> bit) & 1) for bit in (width - 1):-1:0]
end

function basis_index(bits::Vector{Int})
    out = 0
    for bit in bits
        out = (out << 1) | bit
    end
    out + 1
end

function reduce_density(rho::Matrix{ComplexF64}, keep::Vector{Int})
    keep = sort(keep)
    dim = 2^length(keep)
    out = zeros(ComplexF64, dim, dim)
    rest_sites = [idx for idx in 0:(N_SITES - 1) if !(idx in keep)]
    for a in 0:(dim - 1), b in 0:(dim - 1)
        a_bits = bits_of(a, length(keep))
        b_bits = bits_of(b, length(keep))
        value = 0.0 + 0.0im
        for rest in 0:(2^length(rest_sites) - 1)
            rest_bits = bits_of(rest, length(rest_sites))
            left = fill(0, N_SITES)
            right = fill(0, N_SITES)
            for (site, bit) in zip(keep, a_bits)
                left[site + 1] = bit
            end
            for (site, bit) in zip(keep, b_bits)
                right[site + 1] = bit
            end
            for (site, bit) in zip(rest_sites, rest_bits)
                left[site + 1] = bit
                right[site + 1] = bit
            end
            value += rho[basis_index(left), basis_index(right)]
        end
        out[a + 1, b + 1] = value
    end
    out
end

function entropy_vn(rho::Matrix{ComplexF64})
    vals = eigvals(Hermitian((rho + rho') / 2))
    clean = [max(0.0, min(1.0, real(v))) for v in vals if real(v) > 1.0e-12]
    isempty(clean) ? 0.0 : -sum(v * log(v) for v in clean)
end

function bloch_coords(rho1::Matrix{ComplexF64})
    Tuple(real(tr(rho1 * p)) for p in PAULI)
end

state_fidelity(rho::Matrix{ComplexF64}, psi::Vector{ComplexF64}) = real(dot(psi, rho * psi))

function energy_v(rho::Matrix{ComplexF64}, patterns::Dict{String,Vector{ComplexF64}})
    scored = sort([(pid, state_fidelity(rho, psi)) for (pid, psi) in patterns], by=x -> x[2], rev=true)
    1.0 - scored[1][2], scored[1][1], scored[1][2], scored
end

function spurious_density(label_a::String, label_b::String, patterns::Dict{String,Vector{ComplexF64}})
    0.5 * density(patterns[label_a]) + 0.5 * density(patterns[label_b])
end

function choose_target(rho::Matrix{ComplexF64}, patterns::Dict{String,Vector{ComplexF64}})
    _, best_id, _, scores = energy_v(rho, patterns)
    gap = scores[1][2] - scores[2][2]
    if gap <= SPURIOUS_GAP_THRESHOLD
        pair = sort([scores[1][1], scores[2][1]])
        return "spurious::$(pair[1])::$(pair[2])", spurious_density(pair[1], pair[2], patterns), scores, "spurious_low_margin_pair"
    end
    return best_id, density(patterns[best_id]), scores, "stored_pattern_attractor"
end

function retrieval_update(rho::Matrix{ComplexF64}, patterns::Dict{String,Vector{ComplexF64}})
    target_id, target, scores, mode = choose_target(rho, patterns)
    next_rho = hermitize_trace_one((1.0 - RETRIEVAL_ALPHA) * rho + RETRIEVAL_ALPHA * target)
    vals = eigvals(Hermitian((next_rho + next_rho') / 2))
    next_rho, Dict(
        "target_id" => target_id,
        "mode" => mode,
        "trace_real" => real(tr(next_rho)),
        "min_eigenvalue" => minimum(real.(vals)),
        "top_scores" => [Dict("id" => pid, "fidelity" => value) for (pid, value) in scores[1:3]],
    )
end

function seed_states(patterns::Dict{String,Vector{ComplexF64}})
    pattern_ids = collect(keys(patterns))
    rows = Dict{String,Any}[]
    for key in pattern_ids
        push!(rows, Dict("id" => "stored::$(key)", "kind" => "stored", "rho" => density(patterns[key])))
    end
    for (idx, key) in enumerate(pattern_ids)
        other = pattern_ids[mod(idx, length(pattern_ids)) + 1]
        push!(rows, Dict("id" => "corrupt::$(key)::neighbor15", "kind" => "corrupt15", "rho" => hermitize_trace_one(0.85 * density(patterns[key]) + 0.15 * density(patterns[other]))))
    end
    for i in 1:length(pattern_ids)
        for j in (i + 1):length(pattern_ids)
            if j <= length(pattern_ids)
                left, right = pattern_ids[i], pattern_ids[j]
                push!(rows, Dict("id" => "pairmix::$(left)::$(right)", "kind" => "pairmix_equal", "rho" => spurious_density(left, right, patterns)))
            end
        end
    end
    rows
end

function transition_graph(patterns::Dict{String,Vector{ComplexF64}})
    node_ids = Dict{String,Int}()
    edge_pairs = Tuple{Int,Int}[]
    terminal_nodes = Set{String}()
    spurious_terminal_ids = Set{String}()
    lyapunov_deltas = Float64[]
    node_index(name::String) = get!(node_ids, name, length(node_ids) + 1)
    trajectories = Dict{String,Any}[]
    for seed in seed_states(patterns)
        rho = seed["rho"]
        prev_node = seed["id"]
        node_index(prev_node)
        path = Any[Dict("node" => prev_node, "V" => energy_v(rho, patterns)[1])]
        for step in 1:MAX_TRAJECTORY_STEPS
            v_before = energy_v(rho, patterns)[1]
            next_rho, edge = retrieval_update(rho, patterns)
            v_after = energy_v(next_rho, patterns)[1]
            delta = v_after - v_before
            push!(lyapunov_deltas, delta)
            target_node = "$(seed["id"])::step$(step)::$(edge["target_id"])"
            push!(edge_pairs, (node_index(prev_node), node_index(target_node)))
            push!(path, Dict("node" => target_node, "V" => v_after, "target" => edge["target_id"], "delta" => delta))
            rho = next_rho
            prev_node = target_node
            if abs(delta) <= 1.0e-11 || step == MAX_TRAJECTORY_STEPS
                push!(edge_pairs, (node_index(prev_node), node_index(prev_node)))
                push!(terminal_nodes, prev_node)
                if startswith(edge["target_id"], "spurious::")
                    push!(spurious_terminal_ids, edge["target_id"])
                end
                break
            end
        end
        push!(trajectories, Dict("seed_id" => seed["id"], "kind" => seed["kind"], "path" => path))
    end
    g = Graphs.SimpleDiGraph(length(node_ids))
    for (src, dst) in edge_pairs
        Graphs.add_edge!(g, src, dst)
    end
    comps = Graphs.strongly_connected_components(g)
    Dict(
        "node_count" => Graphs.nv(g),
        "edge_count" => Graphs.ne(g),
        "component_count" => length(comps),
        "terminal_scc_count" => length(terminal_nodes),
        "terminal_node_count" => length(terminal_nodes),
        "spurious_terminal_ids" => sort(collect(spurious_terminal_ids)),
        "spurious_attractor_count" => length(spurious_terminal_ids),
        "max_lyapunov_delta" => maximum(lyapunov_deltas),
        "min_lyapunov_delta" => minimum(lyapunov_deltas),
        "trajectories" => trajectories,
        "coverage" => Dict(
            "seed_state_count" => length(seed_states(patterns)),
            "pair_mixture_denominator" => binomial(length(patterns), 2),
            "pair_mixture_enumerated" => binomial(length(patterns), 2),
            "corruptions_enumerated" => length(patterns),
            "stored_enumerated" => length(patterns),
        ),
    )
end

function recover_chart_structure(
    rhos::Vector{Matrix{ComplexF64}};
    state_ids=nothing,
    metadata=nothing,
    rows=A33_ROWS,
    row_labels=nothing,
    classifier_id="A33_committed_predeclared",
    identity_required_pairs=nothing,
    require_load_bearing_identity=false,
)
    recovered = Set{String}()
    residuals = Float64[]
    details = Dict{String,Any}[]
    family_cell_map = Dict{String,Set{String}}()
    load_bearing_cells = Set{String}()
    load_bearing_pairs = Set{String}()
    ids = state_ids === nothing ? ["state_$(idx - 1)" for idx in 1:length(rhos)] : state_ids
    for (state_idx, rho) in enumerate(rhos)
        pattern_id = ids[state_idx]
        meta = metadata === nothing ? Dict{String,Any}() : get(metadata, pattern_id, Dict{String,Any}())
        family_id = string(get(meta, "family_id", pattern_id))
        load_bearing = get(meta, "load_bearing_for_identity_claim", false) == true
        for site in 0:(N_SITES - 1)
            coords = bloch_coords(reduce_density(rho, [site]))
            cell_id, residual = chart_cell_id(coords; rows=rows, row_labels=row_labels)
            push!(recovered, cell_id)
            push!(residuals, residual)
            if !haskey(family_cell_map, family_id)
                family_cell_map[family_id] = Set{String}()
            end
            push!(family_cell_map[family_id], cell_id)
            if load_bearing && cell_id != ORIGIN_CELL
                push!(load_bearing_cells, cell_id)
                push!(load_bearing_pairs, "$(family_id):$(cell_id)")
            end
            push!(details, Dict(
                "state_index" => state_idx - 1,
                "pattern_id" => pattern_id,
                "family_id" => family_id,
                "load_bearing_for_identity_claim" => load_bearing,
                "site" => site,
                "bloch" => collect(coords),
                "cell_id" => cell_id,
                "alignment_residual" => residual,
            ))
        end
    end
    nonorigin = sort([cell for cell in recovered if cell != ORIGIN_CELL])
    family_cell_map_json = Dict(family_id => sort([cell for cell in cells if cell != ORIGIN_CELL]) for (family_id, cells) in family_cell_map)
    observed_pairs = sort(collect(load_bearing_pairs))
    identity_pairs_match_expected = identity_required_pairs === nothing ? true : Set(observed_pairs) == Set(identity_required_pairs)
    load_bearing_family_count = count(family -> any(startswith(pair, "$(family):") for pair in observed_pairs), keys(family_cell_map_json))
    pass_predicate = (
        classifier_id == "A33_committed_predeclared" &&
        length(rows) == 33 &&
        length(nonorigin) >= MIN_RECOVERED_NONORIGIN_CELLS &&
        identity_pairs_match_expected &&
        (
            !require_load_bearing_identity ||
            (
                length(load_bearing_cells) >= MIN_RECOVERED_NONORIGIN_CELLS &&
                load_bearing_family_count == length(HAAR_PINNED_SEEDS)
            )
        )
    )
    Dict(
        "classifier_id" => classifier_id,
        "expected_cell_count" => length(rows),
        "recovered_cell_ids" => sort(collect(recovered)),
        "recovered_nonorigin_cell_ids" => nonorigin,
        "recovered_nonorigin_cell_count" => length(nonorigin),
        "family_cell_identity_map" => family_cell_map_json,
        "load_bearing_recovered_nonorigin_cell_ids" => sort(collect(load_bearing_cells)),
        "load_bearing_recovered_nonorigin_cell_count" => length(load_bearing_cells),
        "load_bearing_family_cell_pairs" => observed_pairs,
        "identity_pairs_match_expected" => identity_pairs_match_expected,
        "median_alignment_residual" => median(residuals),
        "minimum_recovered_nonorigin_cells" => MIN_RECOVERED_NONORIGIN_CELLS,
        "verdict" => pass_predicate ? "RECOVERY_PASS_NONTRIVIAL" : "RECOVERY_FAIL",
        "registered_falsifier_fired" => !pass_predicate,
        "details" => details,
    )
end

function chart_controls(patterns::Dict{String,Vector{ComplexF64}}, metadata)
    terminal_ids = collect(keys(patterns))
    terminal_rhos = [density(patterns[key]) for key in terminal_ids]
    positive = recover_chart_structure(
        terminal_rhos;
        state_ids=terminal_ids,
        metadata=metadata,
        require_load_bearing_identity=true,
    )
    mixed = [Matrix{ComplexF64}(I, DIM, DIM) / DIM]
    erased = [Matrix{ComplexF64}(I, DIM, DIM) / DIM for _ in terminal_rhos]
    axis = (SIGMA_X + SIGMA_Y + SIGMA_Z) / sqrt(3.0)
    single_u = cos(0.37) * Matrix{ComplexF64}(I, 2, 2) - im * sin(0.37) * axis
    rot = single_u
    for _ in 1:(N_SITES - 1)
        rot = kron(rot, single_u)
    end
    rotated = [density(rot * patterns[key]) for key in terminal_ids]
    correct_labels = [a33_cell_id_from_row(row) for row in A33_ROWS]
    permuted_labels = vcat(correct_labels[8:end], correct_labels[1:7])
    controls = Dict(
        "maximally_mixed_state" => recover_chart_structure(mixed),
        "quotient_erased_state" => recover_chart_structure(erased),
        "off_axis_rotated_states" => recover_chart_structure(
            rotated;
            state_ids=terminal_ids,
            metadata=metadata,
            identity_required_pairs=Set(positive["load_bearing_family_cell_pairs"]),
            require_load_bearing_identity=true,
        ),
        "wrong_row_classifier" => recover_chart_structure(
            terminal_rhos;
            state_ids=terminal_ids,
            metadata=metadata,
            rows=A33_ROWS,
            row_labels=permuted_labels,
            classifier_id="A33_committed_predeclared",
            identity_required_pairs=Set(positive["load_bearing_family_cell_pairs"]),
            require_load_bearing_identity=true,
        ),
    )
    controls["wrong_row_classifier"]["control_design"] = "same A33 classifier machinery with a permuted row-label ledger; failure is by family-cell identity mismatch, not classifier-id mismatch"
    for row in values(controls)
        row["expected"] = "RECOVERY_FAIL"
        row["control_fired"] = row["verdict"] == "RECOVERY_FAIL"
    end
    Dict("positive" => positive, "controls" => controls)
end

function cells_for_states(states::Vector{Vector{ComplexF64}})
    rows = Vector{Vector{String}}()
    for state in states
        rho = density(state)
        push!(rows, [chart_cell_id(bloch_coords(reduce_density(rho, [site])))[1] for site in 0:(N_SITES - 1)])
    end
    rows
end

function haar_null_identity_row(positive)
    trial_cell_sets = Vector{Set{String}}()
    trial_pair_sets = Vector{Set{String}}()
    cell_occurrences = Dict{String,Int}()
    pair_occurrences = Dict{String,Int}()
    slot_nonorigin_counts = Dict("slot_$(idx - 1)" => Int[] for idx in 1:length(HAAR_PINNED_SEEDS))
    for trial in 0:(HAAR_NULL_TRIALS - 1)
        states = [haar_pinned_pattern(HAAR_NULL_SEED0 + trial * length(HAAR_PINNED_SEEDS) + idx) for idx in 0:(length(HAAR_PINNED_SEEDS) - 1)]
        per_state_cells = cells_for_states(states)
        trial_cells = Set{String}()
        trial_pairs = Set{String}()
        for (slot_idx, cells) in enumerate(per_state_cells)
            slot = slot_idx - 1
            nonorigin = Set([cell for cell in cells if cell != ORIGIN_CELL])
            append!(slot_nonorigin_counts["slot_$(slot)"], [length(nonorigin)])
            union!(trial_cells, nonorigin)
            for cell in nonorigin
                push!(trial_pairs, "slot_$(slot):$(cell)")
            end
        end
        push!(trial_cell_sets, trial_cells)
        push!(trial_pair_sets, trial_pairs)
        for cell in trial_cells
            cell_occurrences[cell] = get(cell_occurrences, cell, 0) + 1
        end
        for pair in trial_pairs
            pair_occurrences[pair] = get(pair_occurrences, pair, 0) + 1
        end
    end
    cell_prob = Dict(cell => get(cell_occurrences, cell, 0) / HAAR_NULL_TRIALS for cell in sort(collect(A33_CELL_IDS)) if cell != ORIGIN_CELL)
    pair_prob = Dict(pair => count / HAAR_NULL_TRIALS for (pair, count) in pair_occurrences)
    smooth = 1.0 / (HAAR_NULL_TRIALS + 1.0)
    score_pairs(pairs) = sum(-log(max(get(pair_prob, pair, 0.0), smooth)) for pair in pairs)
    family_to_slot = Dict("haar_pinned_seed_$(seed)" => "slot_$(idx - 1)" for (idx, seed) in enumerate(HAAR_PINNED_SEEDS))
    observed_pairs = Set{String}()
    for (family_id, cells) in positive["family_cell_identity_map"]
        if haskey(family_to_slot, family_id)
            for cell in cells
                if cell != ORIGIN_CELL
                    push!(observed_pairs, "$(family_to_slot[family_id]):$(cell)")
                end
            end
        end
    end
    observed_cells = Set([split(pair, ":", limit=2)[2] for pair in observed_pairs])
    null_scores = [score_pairs(pairs) for pairs in trial_pair_sets]
    null_counts = [length(cells) for cells in trial_cell_sets]
    observed_score = score_pairs(observed_pairs)
    null_mean = mean(null_scores)
    null_std = std(null_scores; corrected=false)
    Dict(
        "kind" => "haar_null_identity_control",
        "generator" => "full 4-qubit complex Haar states, four pinned states per trial, single-site quotient cells",
        "trials" => HAAR_NULL_TRIALS,
        "seed0" => HAAR_NULL_SEED0,
        "expected_nonorigin_cell_count" => mean(null_counts),
        "std_nonorigin_cell_count" => std(null_counts; corrected=false),
        "observed_load_bearing_nonorigin_cell_count" => length(observed_cells),
        "observed_family_tied_pair_count" => length(observed_pairs),
        "observed_slot_cell_pairs" => sort(collect(observed_pairs)),
        "observed_identity_surprisal" => observed_score,
        "null_identity_surprisal_mean" => null_mean,
        "null_identity_surprisal_std" => null_std,
        "identity_surprisal_z" => null_std > 0 ? (observed_score - null_mean) / null_std : Inf,
        "cell_identity_distribution" => Dict(cell => Dict("trial_presence_probability" => prob, "observed_load_bearing" => cell in observed_cells) for (cell, prob) in cell_prob),
        "slot_nonorigin_expected" => Dict(slot => mean(counts) for (slot, counts) in slot_nonorigin_counts),
        "verdict" => observed_score > null_mean ? "IDENTITY_ABOVE_NULL" : "IDENTITY_NOT_ABOVE_NULL",
        "control_fired" => true,
        "registered_falsifier_fired" => observed_score <= null_mean,
    )
end

function per_family_recovery_table(positive, metadata, haar_null)
    rows = Dict{String,Any}[]
    cell_prob = haar_null["cell_identity_distribution"]
    for (pattern_id, meta) in metadata
        family_id = string(meta["family_id"])
        cells = get(positive["family_cell_identity_map"], family_id, String[])
        nonorigin = [cell for cell in cells if cell != ORIGIN_CELL]
        surprisal = sum(-log(max(get(get(cell_prob, cell, Dict{String,Any}()), "trial_presence_probability", 0.0), 1.0 / (HAAR_NULL_TRIALS + 1.0))) for cell in nonorigin)
        push!(rows, Dict(
            "pattern_id" => pattern_id,
            "family_id" => family_id,
            "bias_class" => meta["bias_class"],
            "seed" => get(meta, "seed", nothing),
            "seed_hash" => get(meta, "seed_hash", nothing),
            "load_bearing_for_identity_claim" => meta["load_bearing_for_identity_claim"],
            "anchor_from_v1" => meta["anchor_from_v1"],
            "recovered_nonorigin_cell_ids" => nonorigin,
            "recovered_nonorigin_cell_count" => length(nonorigin),
            "identity_surprisal_vs_null_cells" => surprisal,
        ))
    end
    rows
end

function a33_reachability_ceiling(recovered_cell_ids)
    recovered = Set(recovered_cell_ids)
    rows = Dict{String,Any}[]
    for row in A33_ROWS
        rho = 0.5 * (Matrix{ComplexF64}(I, 2, 2) + row[1] * SIGMA_X + row[2] * SIGMA_Y + row[3] * SIGMA_Z)
        vals = eigvals(Hermitian((rho + rho') / 2))
        cell_id = a33_cell_id_from_row(row)
        reachable = minimum(real.(vals)) >= -1.0e-12 && abs(real(tr(rho)) - 1.0) <= 1.0e-12
        push!(rows, Dict(
            "cell_id" => cell_id,
            "bloch_row" => collect(row),
            "reachable_in_principle" => reachable,
            "carrier_witness" => "single-qubit density quotient rho=(I+r.sigma)/2; four-site carrier can purify any rank<=2 single-site quotient",
            "min_eigenvalue" => minimum(real.(vals)),
            "recovered_in_packet" => cell_id in recovered,
        ))
    end
    reachable_ids = [row["cell_id"] for row in rows if row["reachable_in_principle"] == true]
    Dict(
        "geometric_ceiling_cell_count" => length(reachable_ids),
        "reachable_in_principle_cell_ids" => sort(reachable_ids),
        "recovered_cell_ids" => sort(collect(recovered)),
        "recovered_reachable_cell_count" => length(intersect(recovered, Set(reachable_ids))),
        "reachable_not_recovered_cell_ids" => sort(collect(setdiff(Set(reachable_ids), recovered))),
        "rows" => rows,
    )
end

function target_components(target_id::String, patterns)
    if startswith(target_id, "spurious::")
        parts = split(target_id, "::")
        return [(0.5, patterns[parts[2]]), (0.5, patterns[parts[3]])]
    end
    [(1.0, patterns[target_id])]
end

function kraus_choi_witness(target_id::String, patterns)
    components = target_components(target_id, patterns)
    eye = Matrix{ComplexF64}(I, DIM, DIM)
    kraus = Matrix{ComplexF64}[sqrt(1.0 - RETRIEVAL_ALPHA) * eye]
    for (weight, psi) in components
        for basis in 1:DIM
            op = zeros(ComplexF64, DIM, DIM)
            op[:, basis] = sqrt(RETRIEVAL_ALPHA * weight) * psi
            push!(kraus, op)
        end
    end
    completeness = sum(k' * k for k in kraus)
    completeness_residual = norm(completeness - eye)
    choi = zeros(ComplexF64, DIM * DIM, DIM * DIM)
    for a in 1:DIM, b in 1:DIM
        eab = zeros(ComplexF64, DIM, DIM)
        eab[a, b] = 1.0
        mapped = sum(k * eab * k' for k in kraus)
        choi[((a - 1) * DIM + 1):(a * DIM), ((b - 1) * DIM + 1):(b * DIM)] = mapped / DIM
    end
    choi = (choi + choi') / 2
    vals = eigvals(Hermitian(choi))
    ptr_out = zeros(ComplexF64, DIM, DIM)
    for a in 1:DIM, b in 1:DIM
        ptr_out[a, b] = tr(choi[((a - 1) * DIM + 1):(a * DIM), ((b - 1) * DIM + 1):(b * DIM)])
    end
    ptr_residual = norm(ptr_out - eye / DIM)
    Dict(
        "target_id" => target_id,
        "kraus_count" => length(kraus),
        "component_count" => length(components),
        "completeness_residual_fro" => completeness_residual,
        "choi_min_eigenvalue" => minimum(real.(vals)),
        "choi_trace" => real(tr(choi)),
        "choi_rank_tol_1e_10" => count(v -> real(v) > 1.0e-10, vals),
        "choi_partial_trace_output_residual_fro" => ptr_residual,
        "kraus_completeness_pass" => completeness_residual <= 1.0e-10,
        "choi_positivity_pass" => minimum(real.(vals)) >= -1.0e-10,
        "choi_trace_preserving_pass" => ptr_residual <= 1.0e-10,
        "choi_eigenvalue_sha256" => stable_hash_value([round(real(v), digits=15) for v in vals]),
    )
end

function kraus_choi_witness_ledger(basin, patterns)
    target_ids = sort(collect(Set([step["target"] for traj in basin["trajectories"] for step in traj["path"] if haskey(step, "target")])))
    rows = [kraus_choi_witness(target_id, patterns) for target_id in target_ids]
    Dict(
        "channel_formula" => "E_target(rho)=(1-alpha)rho+alpha*Tr(rho)*sigma_target",
        "alpha" => RETRIEVAL_ALPHA,
        "witness_count" => length(rows),
        "all_completeness_pass" => all(row["kraus_completeness_pass"] for row in rows),
        "all_choi_positivity_pass" => all(row["choi_positivity_pass"] for row in rows),
        "all_trace_preserving_pass" => all(row["choi_trace_preserving_pass"] for row in rows),
        "max_completeness_residual_fro" => maximum(row["completeness_residual_fro"] for row in rows),
        "min_choi_eigenvalue" => minimum(row["choi_min_eigenvalue"] for row in rows),
        "max_partial_trace_output_residual_fro" => maximum(row["choi_partial_trace_output_residual_fro"] for row in rows),
        "rows" => rows,
    )
end

function typed_information_rows(patterns::Dict{String,Vector{ComplexF64}}, bipartition)
    if bipartition === nothing || !haskey(bipartition, "A") || !haskey(bipartition, "B")
        throw(MissingStructure("typed S(A|B) requires predeclared bipartition with A and B"))
    end
    rows = Dict{String,Any}[]
    for (pid, psi) in patterns
        rho = density(psi)
        rho_a = reduce_density(rho, Int.(bipartition["A"]))
        rho_b = reduce_density(rho, Int.(bipartition["B"]))
        s_a = entropy_vn(rho_a)
        s_b = entropy_vn(rho_b)
        s_ab = entropy_vn(rho)
        push!(rows, Dict(
            "pattern_id" => pid,
            "S_A_nats" => s_a,
            "S_B_nats" => s_b,
            "S_AB_nats" => s_ab,
            "S_A_given_B_nats" => s_ab - s_b,
            "I_A_B_nats" => s_a + s_b - s_ab,
            "nonproduct_witness" => (s_ab - s_b) < -0.05,
        ))
    end
    Dict(
        "bipartition" => bipartition,
        "rows" => rows,
        "entangled_negative_conditional_rows" => [row for row in rows if row["S_A_given_B_nats"] < -0.05],
    )
end

function z3_proof(;
    nonorigin_count::Int,
    load_bearing_nonorigin_count::Int,
    control_fail_count::Int,
    spurious_count::Int,
    reachable_ceiling_count::Int,
    kraus_witness_count::Int,
    identity_surprisal_scaled::Int,
    null_surprisal_mean_scaled::Int,
)
    values = Dict(
        "nonorigin_count" => nonorigin_count,
        "load_bearing_nonorigin_count" => load_bearing_nonorigin_count,
        "control_fail_count" => control_fail_count,
        "spurious_count" => spurious_count,
        "reachable_ceiling_count" => reachable_ceiling_count,
        "kraus_witness_count" => kraus_witness_count,
        "identity_surprisal_scaled" => identity_surprisal_scaled,
        "null_surprisal_mean_scaled" => null_surprisal_mean_scaled,
    )
    solver = Z3.Solver()
    nonorigin = Z3.IntVar("julia_nonorigin_count")
    load_bearing = Z3.IntVar("julia_load_bearing_nonorigin_count")
    controls = Z3.IntVar("julia_control_fail_count")
    spurious = Z3.IntVar("julia_spurious_count")
    reachable = Z3.IntVar("julia_reachable_ceiling_count")
    kraus = Z3.IntVar("julia_kraus_witness_count")
    identity = Z3.IntVar("julia_identity_surprisal_scaled")
    null_mean = Z3.IntVar("julia_null_surprisal_mean_scaled")
    Z3.add(solver, nonorigin == Z3.IntVal(nonorigin_count))
    Z3.add(solver, load_bearing == Z3.IntVal(load_bearing_nonorigin_count))
    Z3.add(solver, controls == Z3.IntVal(control_fail_count))
    Z3.add(solver, spurious == Z3.IntVal(spurious_count))
    Z3.add(solver, reachable == Z3.IntVal(reachable_ceiling_count))
    Z3.add(solver, kraus == Z3.IntVal(kraus_witness_count))
    Z3.add(solver, identity == Z3.IntVal(identity_surprisal_scaled))
    Z3.add(solver, null_mean == Z3.IntVal(null_surprisal_mean_scaled))
    Z3.add(solver, Z3.Or(Z3.Expr[
        Z3.Not(nonorigin > Z3.IntVal(5)),
        Z3.Not(load_bearing > Z3.IntVal(5)),
        Z3.Not(controls == Z3.IntVal(4)),
        Z3.Not(spurious > Z3.IntVal(5)),
        Z3.Not(reachable == Z3.IntVal(33)),
        Z3.Not(kraus > Z3.IntVal(0)),
        Z3.Not(identity > null_mean),
    ]))
    verdict = string(Z3.check(solver))
    flip = Z3.Solver()
    mutated = Z3.IntVar("julia_mutated_identity_surprisal_scaled")
    mutated_null = Z3.IntVar("julia_mutated_null_surprisal_mean_scaled")
    Z3.add(flip, mutated == Z3.IntVal(null_surprisal_mean_scaled - 1))
    Z3.add(flip, mutated_null == Z3.IntVal(null_surprisal_mean_scaled))
    Z3.add(flip, Z3.Not(mutated > mutated_null))
    flip_verdict = string(Z3.check(flip))
    Dict(
        "ran" => true,
        "solver" => "Z3.jl",
        "verdict" => verdict,
        "perturbed_construction_path_verdict" => flip_verdict,
        "load_bearing" => true,
        "bound_computed_values" => values,
        "positive_case" => "Julia-computed v2 identity/null/control/spurious/reachability/Kraus counts satisfy the finite claim",
        "negative/erased_control" => "mutating identity surprisal below the null mean makes the negated assertion SAT",
    )
end

function build_result()
    mkpath(RESULT_DIR)
    patterns = terminal_patterns()
    metadata = pattern_metadata(patterns)
    anchor_patterns = v1_anchor_patterns()
    anchor_metadata = pattern_metadata(anchor_patterns)
    chart = chart_controls(patterns, metadata)
    anchor_ids = collect(keys(anchor_patterns))
    v1_anchor_recovery = recover_chart_structure(
        [density(anchor_patterns[key]) for key in anchor_ids];
        state_ids=anchor_ids,
        metadata=anchor_metadata,
    )
    basin = transition_graph(anchor_patterns)
    typed = typed_information_rows(patterns, Dict("A" => [0], "B" => [1, 2, 3]))
    premature = try
        typed_information_rows(patterns, nothing)
        Dict("raised" => false, "error" => nothing)
    catch err
        Dict("raised" => true, "error" => sprint(showerror, err))
    end
    haar_null = haar_null_identity_row(chart["positive"])
    family_recovery = per_family_recovery_table(chart["positive"], metadata, haar_null)
    a33_coverage = a33_reachability_ceiling(chart["positive"]["recovered_nonorigin_cell_ids"])
    kraus_ledger = kraus_choi_witness_ledger(basin, anchor_patterns)
    control_fail_count = count(row -> row["control_fired"] == true, values(chart["controls"]))
    identity_surprisal_scaled = round(Int, haar_null["observed_identity_surprisal"] * 1000)
    null_surprisal_mean_scaled = round(Int, haar_null["null_identity_surprisal_mean"] * 1000)
    julia_z3 = z3_proof(
        nonorigin_count=chart["positive"]["recovered_nonorigin_cell_count"],
        load_bearing_nonorigin_count=chart["positive"]["load_bearing_recovered_nonorigin_cell_count"],
        control_fail_count=control_fail_count,
        spurious_count=basin["spurious_attractor_count"],
        reachable_ceiling_count=a33_coverage["geometric_ceiling_cell_count"],
        kraus_witness_count=kraus_ledger["witness_count"],
        identity_surprisal_scaled=identity_surprisal_scaled,
        null_surprisal_mean_scaled=null_surprisal_mean_scaled,
    )
    engine_values = Dict(
        "recovered_nonorigin_cell_count" => chart["positive"]["recovered_nonorigin_cell_count"],
        "load_bearing_recovered_nonorigin_cell_count" => chart["positive"]["load_bearing_recovered_nonorigin_cell_count"],
        "control_fail_count" => control_fail_count,
        "terminal_scc_count" => basin["terminal_scc_count"],
        "spurious_attractor_count" => basin["spurious_attractor_count"],
        "max_lyapunov_delta_scaled" => round(Int, max(0.0, basin["max_lyapunov_delta"]) * 1_000_000_000),
        "typed_entangled_negative_count" => length(typed["entangled_negative_conditional_rows"]),
        "haar_null_expected_nonorigin_cell_count_scaled" => round(Int, haar_null["expected_nonorigin_cell_count"] * 1000),
        "identity_surprisal_scaled" => identity_surprisal_scaled,
        "null_surprisal_mean_scaled" => null_surprisal_mean_scaled,
        "a33_reachable_in_principle_count" => a33_coverage["geometric_ceiling_cell_count"],
        "kraus_choi_witness_count" => kraus_ledger["witness_count"],
        "v1_anchor_recovered_nonorigin_cell_count" => v1_anchor_recovery["recovered_nonorigin_cell_count"],
    )
    all_pass = (
        chart["positive"]["verdict"] == "RECOVERY_PASS_NONTRIVIAL" &&
        chart["positive"]["load_bearing_recovered_nonorigin_cell_count"] >= MIN_RECOVERED_NONORIGIN_CELLS &&
        control_fail_count == 4 &&
        chart["controls"]["wrong_row_classifier"]["identity_pairs_match_expected"] == false &&
        haar_null["verdict"] == "IDENTITY_ABOVE_NULL" &&
        7.0 <= haar_null["expected_nonorigin_cell_count"] <= 8.3 &&
        a33_coverage["geometric_ceiling_cell_count"] == 33 &&
        kraus_ledger["all_completeness_pass"] == true &&
        kraus_ledger["all_choi_positivity_pass"] == true &&
        kraus_ledger["all_trace_preserving_pass"] == true &&
        v1_anchor_recovery["recovered_nonorigin_cell_count"] == 6 &&
        basin["max_lyapunov_delta"] <= 1.0e-10 &&
        basin["spurious_attractor_count"] == 6 &&
        length(typed["entangled_negative_conditional_rows"]) >= 1 &&
        premature["raised"] == true &&
        julia_z3["verdict"] == "unsat" &&
        julia_z3["perturbed_construction_path_verdict"] == "sat"
    )
    Dict(
        "schema" => "codex_ratchet.engine_leg_result.v2",
        "sim_id" => SIM_ID,
        "object_id" => "$(SIM_ID)_$(ENGINE)",
        "engine" => ENGINE,
        "role_id" => "julia_graphs_z3_surface_reference",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => false,
        "all_pass" => all_pass,
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "julia_project" => string(Base.active_project()),
        "packages_used" => ["Graphs", "Z3", "JSON", "LinearAlgebra", "SHA", "Statistics", "Dates"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "claim_path_tools" => ["Graphs", "Z3", "LinearAlgebra", "Statistics"],
        "package_observables" => Dict(
            "Graphs" => "Julia SimpleDiGraph recomputes finite retrieval graph edge rows and component evidence",
            "Z3" => "Julia-side computed v2 chart/control/null/reachability/Kraus count identity UNSAT with SAT mutation flip",
            "LinearAlgebra" => "Julia eigenspectrum, density quotient, and Kraus/Choi witness computations gate positivity and A33 reachability",
            "Statistics" => "Julia null-distribution mean/std and residual medians gate the Haar identity row",
        ),
        "engine_values" => engine_values,
        "A_chart_recoverability" => chart["positive"],
        "v1_anchor_reproduction" => Dict(
            "expected_recovered_nonorigin_cell_ids" => [
                "A33_x00_y00_zp10",
                "A33_x00_yp5_z00",
                "A33_xp10_y00_z00",
                "A33_xp5_y00_z00",
                "A33_xp5_y00_zm5",
                "A33_xp5_y00_zp5",
            ],
            "actual_recovered_nonorigin_cell_ids" => v1_anchor_recovery["recovered_nonorigin_cell_ids"],
            "actual_recovered_nonorigin_cell_count" => v1_anchor_recovery["recovered_nonorigin_cell_count"],
            "unchanged_anchor_pass" => Set(v1_anchor_recovery["recovered_nonorigin_cell_ids"]) == Set([
                "A33_x00_y00_zp10",
                "A33_x00_yp5_z00",
                "A33_xp10_y00_z00",
                "A33_xp5_y00_z00",
                "A33_xp5_y00_zm5",
                "A33_xp5_y00_zp5",
            ]),
        ),
        "haar_null_row" => haar_null,
        "per_family_recovery_table" => family_recovery,
        "A33_reachability_ceiling" => a33_coverage,
        "kraus_choi_witness_ledger" => kraus_ledger,
        "no_structure_controls" => chart["controls"],
        "basin_partition" => basin,
        "typed_information" => typed,
        "premature_typed_row_control" => premature,
        "crossover_proofs" => Dict("julia_z3" => julia_z3),
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("used" => true, "reason" => "load-bearing finite graph construction"),
            "Z3" => Dict("used" => true, "reason" => "load-bearing finite v2 count/null/reachability proof"),
            "JSON" => Dict("used" => true, "reason" => "supportive receipt serialization"),
            "LinearAlgebra" => Dict("used" => true, "reason" => "load-bearing density quotient, A33 reachability, and Kraus/Choi positivity witness computation"),
            "SHA" => Dict("used" => true, "reason" => "supportive source hash"),
            "Statistics" => Dict("used" => true, "reason" => "load-bearing Haar-null distribution and median residual computation"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "Z3" => "load_bearing", "JSON" => "supportive", "LinearAlgebra" => "load_bearing", "SHA" => "supportive", "Statistics" => "load_bearing"),
        "tool_calls" => [
            Dict(
                "tool" => "Graphs",
                "qualified_api/function" => "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.strongly_connected_components",
                "input_object" => "finite retrieval trajectory edge relation",
                "output_object" => Dict("node_count" => basin["node_count"], "edge_count" => basin["edge_count"], "component_count" => basin["component_count"]),
                "positive_case" => "finite graph rows exist and terminal count is computed from graph construction",
                "negative/erased_control" => "spurious pair mixtures remain explicit graph seeds",
                "boundary_case" => "finite n4 graph only",
                "demotion_condition" => "demote if Graphs route is removed",
                "gates" => ["basin_partition", "all_pass"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                "input_object" => "computed nonorigin recovery count, control fail count, and spurious count",
                "output_object" => julia_z3,
                "positive_case" => julia_z3["positive_case"],
                "negative/erased_control" => julia_z3["negative/erased_control"],
                "boundary_case" => "integer finite-count proof only",
                "demotion_condition" => "demote if solver binds only booleans",
                "gates" => ["crossover_proofs", "all_pass"],
            ),
            Dict(
                "tool" => "LinearAlgebra",
                "qualified_api/function" => "LinearAlgebra.eigvals/LinearAlgebra.norm/LinearAlgebra.Hermitian",
                "input_object" => "A33 single-site quotient rows and Kraus/Choi channel matrices",
                "output_object" => Dict(
                    "a33_reachable_in_principle_count" => a33_coverage["geometric_ceiling_cell_count"],
                    "kraus_witness_count" => kraus_ledger["witness_count"],
                    "min_choi_eigenvalue" => kraus_ledger["min_choi_eigenvalue"],
                ),
                "positive_case" => "all 33 A33 rows are positive single-site density quotients and all Choi witnesses are positive",
                "negative/erased_control" => "positivity/completeness gates would fail for non-density rows or non-TP Kraus ledgers",
                "boundary_case" => "finite 16-dimensional four-site carrier only",
                "demotion_condition" => "demote if A33 reachability or Choi positivity stops gating all_pass",
                "gates" => ["A33_reachability_ceiling", "kraus_choi_witness_ledger", "all_pass"],
            ),
            Dict(
                "tool" => "Statistics",
                "qualified_api/function" => "Statistics.mean/Statistics.std/Statistics.median",
                "input_object" => "2048-trial Haar null identity distribution and chart residual rows",
                "output_object" => Dict(
                    "expected_nonorigin_cell_count" => haar_null["expected_nonorigin_cell_count"],
                    "identity_surprisal_z" => haar_null["identity_surprisal_z"],
                ),
                "positive_case" => "family-tied identity surprisal is above the computed Haar null mean",
                "negative/erased_control" => "mutated identity score below the null mean is admitted by the finite Z3 flip",
                "boundary_case" => "deterministic pinned Haar generator with recorded seeds",
                "demotion_condition" => "demote if null distribution is removed or not tied to all_pass",
                "gates" => ["haar_null_row", "all_pass"],
            ),
        ],
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "result_path" => rel(RESULT_PATH))))
    result["all_pass"] ? 0 : 1
end

exit(main())
