#!/usr/bin/env julia
# object_id: spinor_network_force_transition_channel_taxonomy
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/spinor_network_force_transition_channel_taxonomy_julia_results.json")
const JAX_RESULT_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/spinor_network_force_transition_channel_taxonomy_results.json")
const OBJECT_ID = "spinor_network_force_transition_channel_taxonomy"
const N = 5
const DIM = 2^N
const TOL = 1.0e-10
const RANK_TOL = 1.0e-8
const PURITY_THRESHOLD = 0.85
const LN2 = log(2.0)
const EDGES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4)]
const REST_EDGES = [(2, 3), (3, 4)]
const LOCAL_SUBSETS = Any[(0,), (1,), (2,), (3,), (4,), (0, 1), (1, 2), (2, 3), (3, 4), (0, 4)]
const DELTA_KEYS = [
    "expansion_dark_energy_time",
    "preserved_info_dark_matter",
    "bounded_knot_matter_mass",
    "composite_knot_baryons_hadrons",
    "transition_forces",
    "synchronization_gradient_gravity",
]
const FORCE_KEYS = [
    "electromagnetic_phase_coupling",
    "strong_binding_confinement",
    "weak_decay_topology_change",
    "gravity_sync_flattening",
]
const CHANNEL_ORDER = ["identity_control"; FORCE_KEYS]

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SZ = ComplexF64[1 0; 0 -1]

bit_at(index::Int, node::Int) = (index >> (N - 1 - node)) & 1

function normalize(psi::Vector{ComplexF64})
    psi ./ norm(psi)
end

function graph_phase_value(index::Int, phase::Real, edges)
    total = 0.0
    for (left, right) in edges
        total += bit_at(index, left) * bit_at(index, right)
    end
    cis(Float64(phase) * total)
end

function graph_state(phase::Real)
    normalize(ComplexF64[graph_phase_value(index, phase, EDGES) for index in 0:(DIM - 1)])
end

function single_knot_state()
    psi = zeros(ComplexF64, DIM)
    for index in 0:(DIM - 1)
        if bit_at(index, 0) == 0
            psi[index + 1] = graph_phase_value(index, pi, EDGES)
        end
    end
    normalize(psi)
end

density(psi::Vector{ComplexF64}) = psi * psi'

function packed_bits(index::Int, keep)
    out = 0
    for node in keep
        out = (out << 1) | bit_at(index, node)
    end
    out
end

function traced_nodes(keep)
    [node for node in 0:(N - 1) if !(node in keep)]
end

function same_trace_bits(left::Int, right::Int, traced)
    for node in traced
        bit_at(left, node) == bit_at(right, node) || return false
    end
    true
end

function reduced_density(rho::Matrix{ComplexF64}, keep)
    traced = traced_nodes(keep)
    dim_a = 2^length(keep)
    out = zeros(ComplexF64, dim_a, dim_a)
    for left in 0:(DIM - 1)
        for right in 0:(DIM - 1)
            if same_trace_bits(left, right, traced)
                out[packed_bits(left, keep) + 1, packed_bits(right, keep) + 1] += rho[left + 1, right + 1]
            end
        end
    end
    out
end

function entropy_probs(values)
    total = 0.0
    for value in values
        p = max(real(value), 0.0)
        if p > 1.0e-15
            total -= p * log(p)
        end
    end
    total
end

function entropy_rho(rho::Matrix{ComplexF64})
    entropy_probs(eigvals(Hermitian((rho + rho') / 2)))
end

function normalized_entropy(rho::Matrix{ComplexF64}, dim::Int)
    dim <= 1 && return 0.0
    entropy_rho(rho) / log(Float64(dim))
end

purity(rho::Matrix{ComplexF64}) = real(tr(rho * rho))
purity_score(rho::Matrix{ComplexF64}) = clamp((purity(rho) - PURITY_THRESHOLD) / (1.0 - PURITY_THRESHOLD), 0.0, 1.0)

function neighbors(subset)
    selected = Set(subset)
    out = Set{Int}()
    for (left, right) in EDGES
        if left in selected && !(right in selected)
            push!(out, right)
        end
        if right in selected && !(left in selected)
            push!(out, left)
        end
    end
    sort(collect(out))
end

function edge_mutual_information(rho::Matrix{ComplexF64}, left::Int, right::Int)
    rho_l = reduced_density(rho, (left,))
    rho_r = reduced_density(rho, (right,))
    rho_lr = reduced_density(rho, (left, right))
    entropy_rho(rho_l) + entropy_rho(rho_r) - entropy_rho(rho_lr)
end

function one_site_operator(op::Matrix{ComplexF64}, node::Int)
    result = reshape(ComplexF64[1], 1, 1)
    for idx in 0:(N - 1)
        result = kron(result, idx == node ? op : I2)
    end
    result
end

function controlled_phase(edge::Tuple{Int,Int}, angle::Float64)
    left, right = edge
    out = zeros(ComplexF64, DIM, DIM)
    for index in 0:(DIM - 1)
        out[index + 1, index + 1] = cis(angle * bit_at(index, left) * bit_at(index, right))
    end
    out
end

function amplitude_damping_kraus(node::Int, gamma::Float64)
    k0 = ComplexF64[1 0; 0 sqrt(1 - gamma)]
    k1 = ComplexF64[0 sqrt(gamma); 0 0]
    (one_site_operator(k0, node), one_site_operator(k1, node))
end

function trace_distance(left::Matrix{ComplexF64}, right::Matrix{ComplexF64})
    diff = (left - right + (left - right)') / 2
    0.5 * sum(abs.(eigvals(Hermitian(diff))))
end

function transition_readout(rho::Matrix{ComplexF64})
    ux0 = one_site_operator(SX, 0)
    uz1 = one_site_operator(SZ, 1)
    ucp = controlled_phase((0, 1), pi / 3)
    k0, k1 = amplitude_damping_kraus(0, 0.23)
    channels = Dict{String,Matrix{ComplexF64}}(
        "local_x_node0" => ux0 * rho * ux0',
        "local_z_node1" => uz1 * rho * uz1',
        "controlled_phase_edge01" => ucp * rho * ucp',
        "damping_node0" => k0 * rho * k0' + k1 * rho * k1',
    )
    distances = Dict(key => trace_distance(rho, value) for (key, value) in channels)
    residual = norm(k0' * k0 + k1' * k1 - Matrix{ComplexF64}(I, DIM, DIM))
    (sum(values(distances)) / length(distances), Dict{String,Any}("channel_trace_distances" => distances, "max_cptp_residual" => residual))
end

function knot_scores(rho::Matrix{ComplexF64})
    values = Float64[]
    for subset in LOCAL_SUBSETS
        push!(values, purity_score(reduced_density(rho, subset)) / length(subset))
    end
    (maximum(values), Dict{String,Any}())
end

function composite_score(rho::Matrix{ComplexF64})
    values = Float64[]
    for (left, right) in EDGES
        rho_pair = reduced_density(rho, (left, right))
        mi_norm = clamp(edge_mutual_information(rho, left, right) / (2 * LN2), 0.0, 1.0)
        push!(values, purity_score(rho_pair) * mi_norm)
    end
    (maximum(values), Dict{String,Any}())
end

function gravity_score(rho::Matrix{ComplexF64})
    values = Float64[]
    for subset in LOCAL_SUBSETS
        rho_a = reduced_density(rho, subset)
        knot = purity_score(rho_a) / length(subset)
        local_s = normalized_entropy(rho_a, 2^length(subset))
        nbrs = neighbors(subset)
        neighbor_s = isempty(nbrs) ? 0.0 : sum(normalized_entropy(reduced_density(rho, (node,)), 2) for node in nbrs) / length(nbrs)
        push!(values, knot * max(0.0, neighbor_s - local_s))
    end
    (maximum(values), Dict{String,Any}())
end

function density_readouts(rho::Matrix{ComplexF64})
    diagonal = real.(diag(rho))
    expansion = entropy_probs(diagonal) / log(Float64(DIM))
    edge_mis = [edge_mutual_information(rho, left, right) / (2 * LN2) for (left, right) in EDGES]
    matter, _ = knot_scores(rho)
    composite, _ = composite_score(rho)
    gravity, _ = gravity_score(rho)
    transition, transition_detail = transition_readout(rho)
    readouts = Dict{String,Any}(
        "expansion_dark_energy_time" => expansion,
        "preserved_info_dark_matter" => sum(edge_mis) / length(edge_mis),
        "bounded_knot_matter_mass" => matter,
        "composite_knot_baryons_hadrons" => composite,
        "transition_forces" => transition,
        "synchronization_gradient_gravity" => gravity,
    )
    details = Dict{String,Any}(
        "transition" => transition_detail,
        "trace" => real(tr(rho)),
        "min_eigenvalue" => minimum(eigvals(Hermitian((rho + rho') / 2))),
    )
    (readouts, details)
end

function bell_edge_density()
    vec = ComplexF64[1 / sqrt(2), 0, 0, 1 / sqrt(2)]
    vec * vec'
end

function replace_leading_subsystem(rho::Matrix{ComplexF64}, replacement::Matrix{ComplexF64}, n_replace::Int)
    rest = reduced_density(rho, Tuple(n_replace:(N - 1)))
    kron(replacement, rest)
end

identity_channel(rho::Matrix{ComplexF64}) = rho

function electromagnetic_phase_channel(rho::Matrix{ComplexF64})
    unitary = controlled_phase((0, 1), pi / 5)
    unitary * rho * unitary'
end

strong_binding_channel(rho::Matrix{ComplexF64}) = replace_leading_subsystem(rho, bell_edge_density(), 2)
weak_decay_channel(rho::Matrix{ComplexF64}) = replace_leading_subsystem(rho, I2 / 2, 1)

function gravity_sync_channel(rho::Matrix{ComplexF64})
    flat = density(graph_state(pi))
    0.65 * rho + 0.35 * flat
end

function selected_input_states()
    single = density(single_knot_state())
    Dict{String,Matrix{ComplexF64}}(
        "identity_control" => single,
        "electromagnetic_phase_coupling" => density(graph_state(pi / 2)),
        "strong_binding_confinement" => single,
        "weak_decay_topology_change" => single,
        "gravity_sync_flattening" => single,
    )
end

function apply_channel(name::String, rho::Matrix{ComplexF64})
    name == "identity_control" && return identity_channel(rho)
    name == "electromagnetic_phase_coupling" && return electromagnetic_phase_channel(rho)
    name == "strong_binding_confinement" && return strong_binding_channel(rho)
    name == "weak_decay_topology_change" && return weak_decay_channel(rho)
    name == "gravity_sync_flattening" && return gravity_sync_channel(rho)
    error("unknown channel $name")
end

function channel_record(name::String, input_rho::Matrix{ComplexF64})
    output_rho = apply_channel(name, input_rho)
    before, _ = density_readouts(input_rho)
    after, after_details = density_readouts(output_rho)
    delta = Dict(key => after[key] - before[key] for key in DELTA_KEYS)
    trace_value = real(tr(output_rho))
    min_eig = minimum(eigvals(Hermitian((output_rho + output_rho') / 2)))
    Dict{String,Any}(
        "input_readouts" => before,
        "output_readouts" => after,
        "delta" => delta,
        "trace_distance" => trace_distance(input_rho, output_rho),
        "output_trace" => trace_value,
        "output_min_eigenvalue" => min_eig,
        "output_details" => after_details,
        "density_valid" => abs(trace_value - 1.0) <= TOL && min_eig >= -1.0e-9,
    )
end

function response_matrix(records)
    matrix = zeros(Float64, length(FORCE_KEYS), length(DELTA_KEYS))
    for (i, channel) in enumerate(FORCE_KEYS)
        for (j, key) in enumerate(DELTA_KEYS)
            matrix[i, j] = Float64(records[channel]["delta"][key])
        end
    end
    matrix
end

function parity_block(result)
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}("peer_result_path" => JAX_RESULT_PATH, "peer_available" => false, "parity_max_diff" => nothing, "worst_key" => nothing, "within_1e_10" => false, "diffs" => Dict{String,Any}())
    end
    peer = JSON.parsefile(JAX_RESULT_PATH)
    diffs = Dict{String,Any}()
    max_diff = 0.0
    worst_key = ""
    for (key, value) in result["shared_scalars"]
        if haskey(peer["shared_scalars"], key)
            diff = abs(Float64(value) - Float64(peer["shared_scalars"][key]))
            diffs[key] = diff
            if diff > max_diff
                max_diff = diff
                worst_key = key
            end
        end
    end
    Dict{String,Any}("peer_result_path" => JAX_RESULT_PATH, "peer_available" => true, "parity_max_diff" => max_diff, "worst_key" => worst_key, "within_1e_10" => max_diff <= TOL, "diffs" => diffs)
end

function main()
    inputs = selected_input_states()
    records = Dict(name => channel_record(name, inputs[name]) for name in CHANNEL_ORDER)
    matrix = response_matrix(records)
    singular_values = svdvals(matrix)
    channel_response_rank = count(value -> value > RANK_TOL, singular_values)

    identity_zero = all(abs(records["identity_control"]["delta"][key]) <= TOL for key in DELTA_KEYS)
    em = records["electromagnetic_phase_coupling"]
    strong = records["strong_binding_confinement"]
    weak = records["weak_decay_topology_change"]
    sync = records["gravity_sync_flattening"]
    em_phase_selective = em["trace_distance"] > 0.05 &&
        abs(em["delta"]["expansion_dark_energy_time"]) <= TOL &&
        abs(em["delta"]["bounded_knot_matter_mass"]) <= TOL &&
        abs(em["delta"]["synchronization_gradient_gravity"]) <= TOL &&
        abs(em["delta"]["preserved_info_dark_matter"]) > 1.0e-3
    strong_binding_selective = strong["delta"]["composite_knot_baryons_hadrons"] > 0.9 &&
        strong["delta"]["preserved_info_dark_matter"] > 0.05 &&
        strong["delta"]["bounded_knot_matter_mass"] < -0.25
    weak_decay_selective = weak["delta"]["bounded_knot_matter_mass"] < -0.9 &&
        weak["delta"]["synchronization_gradient_gravity"] < -0.9 &&
        abs(weak["delta"]["composite_knot_baryons_hadrons"]) <= TOL
    sync_flatten_selective = sync["delta"]["synchronization_gradient_gravity"] < -0.9 &&
        sync["delta"]["expansion_dark_energy_time"] > 0.05 &&
        sync["delta"]["preserved_info_dark_matter"] < -0.05
    density_valid = all(records[name]["density_valid"] for name in CHANNEL_ORDER)
    distinct_channels = channel_response_rank >= 3

    positive = Dict{String,Any}(
        "same_finite_carrier_distinct_transition_channels" => Dict{String,Any}("pass" => distinct_channels, "channel_response_rank" => channel_response_rank, "singular_values" => singular_values),
        "identity_channel_zero_delta_control" => Dict{String,Any}("pass" => identity_zero, "delta" => records["identity_control"]["delta"]),
        "electromagnetic_phase_channel_selective" => Dict{String,Any}("pass" => em_phase_selective, "record" => em),
        "strong_binding_channel_selective" => Dict{String,Any}("pass" => strong_binding_selective, "record" => strong),
        "weak_decay_channel_selective" => Dict{String,Any}("pass" => weak_decay_selective, "record" => weak),
        "gravity_sync_flattening_channel_selective" => Dict{String,Any}("pass" => sync_flatten_selective, "record" => sync),
        "finite_density_validity_controls" => Dict{String,Any}("pass" => density_valid),
    )
    graveyard_companions = Dict{String,Any}(
        "anti_force_admission_fence" => Dict{String,Any}("pass" => true, "promotion_allowed" => false, "formal_admission_allowed" => false),
        "anti_single_force_scalar_control" => Dict{String,Any}("pass" => distinct_channels, "minimum_rank_required" => 3, "rank" => channel_response_rank),
        "identity_channel_must_not_move_faces" => Dict{String,Any}("pass" => identity_zero),
    )
    boundary = Dict{String,Any}(
        "finite_spinor_network_boundary" => Dict{String,Any}("pass" => true, "n_spinor_nodes" => N, "hilbert_dimension" => DIM),
        "julia_mirror_no_numpy_compute" => Dict{String,Any}("pass" => true, "numpy_compute_used" => false),
    )
    shared_scalars = Dict{String,Any}(
        "channel_response_rank" => Float64(channel_response_rank),
        "identity_zero" => identity_zero ? 1.0 : 0.0,
        "em_phase_selective" => em_phase_selective ? 1.0 : 0.0,
        "strong_binding_selective" => strong_binding_selective ? 1.0 : 0.0,
        "weak_decay_selective" => weak_decay_selective ? 1.0 : 0.0,
        "sync_flatten_selective" => sync_flatten_selective ? 1.0 : 0.0,
        "density_valid" => density_valid ? 1.0 : 0.0,
    )
    for (idx, value) in enumerate(singular_values)
        shared_scalars["channel_singular_value_$(idx - 1)"] = Float64(value)
    end
    for channel_name in CHANNEL_ORDER
        shared_scalars["$(channel_name).trace_distance"] = Float64(records[channel_name]["trace_distance"])
        for key in DELTA_KEYS
            shared_scalars["$(channel_name).delta.$(key)"] = Float64(records[channel_name]["delta"][key])
        end
    end

    result = Dict{String,Any}(
        "schema" => "FINITE_SPINOR_NETWORK_FORCE_TRANSITION_CHANNEL_TAXONOMY_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "backend" => "julia",
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "finite force/transition-channel taxonomy only; no force, particle, gravity, Axis0, physics, M(C), PEPS3D, or bridge admission",
        "carrier" => Dict{String,Any}("primitive" => "finite spinor-network state psi; channels operate on spinor-derived density readouts", "nodes" => N, "edges" => [collect(edge) for edge in EDGES], "hilbert_dimension" => DIM),
        "records" => records,
        "positive" => positive,
        "graveyard_companions" => graveyard_companions,
        "boundary" => boundary,
        "shared_scalars" => shared_scalars,
        "blocked_consumers" => ["force admission", "particle admission", "gravity admission", "Standard Model claim", "Axis0", "physics", "M(C)", "PEPS3D", "bridge", "final manifold closure"],
        "eligible_consumers" => ["scratch diagnostic audits", "transition taxonomy follow-up scouts", "dual-backend parity checks"],
        "TOOL_MANIFEST" => Dict{String,Any}(
            "Julia LinearAlgebra" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing finite channel action, density/readout deltas, rank controls, and parity scalars"),
            "Julia JSON/Dates" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "supportive receipt writing to the exact Julia result path"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}("Julia LinearAlgebra" => "load_bearing", "Julia JSON/Dates" => "supportive"),
    )
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_block(result)
    local_all_pass = all(row["pass"] for row in values(positive)) &&
        all(row["pass"] for row in values(graveyard_companions)) &&
        all(row["pass"] for row in values(boundary))
    result["all_pass"] = local_all_pass && result["parity"]["peer_available"] && result["parity"]["within_1e_10"]
    result["summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "local_all_pass" => local_all_pass,
        "channel_response_rank" => channel_response_rank,
        "identity_zero" => identity_zero,
        "em_phase_selective" => em_phase_selective,
        "strong_binding_selective" => strong_binding_selective,
        "weak_decay_selective" => weak_decay_selective,
        "sync_flatten_selective" => sync_flatten_selective,
        "parity_within_1e_10" => result["parity"]["within_1e_10"],
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(result["summary"], 2))
    if !local_all_pass
        exit(1)
    end
    if result["parity"]["peer_available"] && !result["parity"]["within_1e_10"]
        exit(1)
    end
end

main()
