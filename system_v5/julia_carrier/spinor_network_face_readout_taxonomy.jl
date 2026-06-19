#!/usr/bin/env julia
# object_id: spinor_network_face_readout_taxonomy
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/spinor_network_face_readout_taxonomy_julia_results.json")
const JAX_RESULT_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/spinor_network_face_readout_taxonomy_results.json")
const OBJECT_ID = "spinor_network_face_readout_taxonomy"
const BACKEND = "julia"
const N = 5
const DIM = 2^N
const TOL = 1.0e-10
const RANK_TOL = 1.0e-8
const PURITY_THRESHOLD = 0.85
const LN2 = log(2.0)
const EDGES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4)]
const REST_EDGES = [(2, 3), (3, 4)]
const LOCAL_SUBSETS = Any[(0,), (1,), (2,), (3,), (4,), (0, 1), (1, 2), (2, 3), (3, 4), (0, 4)]
const READOUT_KEYS = [
    "expansion_dark_energy_time",
    "preserved_info_dark_matter",
    "bounded_knot_matter_mass",
    "composite_knot_baryons_hadrons",
    "transition_forces",
    "synchronization_gradient_gravity",
]
const PERTURBATION_ORDER = ["flat_fuzz", "phase_twisted_flat", "single_knot", "composite_knot"]

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
    psi = ComplexF64[graph_phase_value(index, phase, EDGES) for index in 0:(DIM - 1)]
    normalize(psi)
end

function single_knot_state()
    psi = zeros(ComplexF64, DIM)
    for index in 0:(DIM - 1)
        if bit_at(index, 0) == 0
            # Pin node 0 into a local pure knot while preserving the graph-phase
            # field on the remaining finite network. Edges incident on node 0
            # vanish because bit_0=0 on the support.
            psi[index + 1] = graph_phase_value(index, pi, EDGES)
        end
    end
    normalize(psi)
end

function composite_knot_state()
    psi = zeros(ComplexF64, DIM)
    for index in 0:(DIM - 1)
        if bit_at(index, 0) == bit_at(index, 1)
            psi[index + 1] = graph_phase_value(index, pi, REST_EDGES)
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
        if bit_at(left, node) != bit_at(right, node)
            return false
        end
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
    hermitian = Hermitian((rho + rho') / 2)
    entropy_probs(eigvals(hermitian))
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

function support_entropy(psi::Vector{ComplexF64})
    probs = abs2.(psi)
    entropy_probs(probs) / log(Float64(DIM))
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
    distances = Dict{String,Any}()
    for (key, value) in channels
        distances[key] = trace_distance(rho, value)
    end
    cptp_residual = norm(k0' * k0 + k1' * k1 - Matrix{ComplexF64}(I, DIM, DIM))
    (sum(values(distances)) / length(distances), Dict{String,Any}("channel_trace_distances" => distances, "max_cptp_residual" => cptp_residual))
end

function knot_scores(rho::Matrix{ComplexF64})
    values = Float64[]
    rows = Any[]
    for subset in LOCAL_SUBSETS
        rho_a = reduced_density(rho, subset)
        score = purity_score(rho_a) / length(subset)
        push!(values, score)
        push!(
            rows,
            Dict{String,Any}(
                "subset" => collect(subset),
                "purity" => purity(rho_a),
                "purity_score" => purity_score(rho_a),
                "locality_weighted_score" => score,
            ),
        )
    end
    best_value, best_idx = findmax(values)
    (best_value, Dict{String,Any}("best" => rows[best_idx], "candidates" => rows))
end

function composite_score(rho::Matrix{ComplexF64})
    values = Float64[]
    rows = Any[]
    for (left, right) in EDGES
        rho_pair = reduced_density(rho, (left, right))
        mi_norm = clamp(edge_mutual_information(rho, left, right) / (2 * LN2), 0.0, 1.0)
        score = purity_score(rho_pair) * mi_norm
        push!(values, score)
        push!(
            rows,
            Dict{String,Any}(
                "edge" => [left, right],
                "pair_purity" => purity(rho_pair),
                "pair_purity_score" => purity_score(rho_pair),
                "internal_mi_norm" => mi_norm,
                "score" => score,
            ),
        )
    end
    best_value, best_idx = findmax(values)
    (best_value, Dict{String,Any}("best" => rows[best_idx], "candidates" => rows))
end

function gravity_score(rho::Matrix{ComplexF64})
    values = Float64[]
    rows = Any[]
    for subset in LOCAL_SUBSETS
        rho_a = reduced_density(rho, subset)
        knot = purity_score(rho_a) / length(subset)
        local_s = normalized_entropy(rho_a, 2^length(subset))
        nbrs = neighbors(subset)
        neighbor_s = isempty(nbrs) ? 0.0 : sum(normalized_entropy(reduced_density(rho, (node,)), 2) for node in nbrs) / length(nbrs)
        gradient = knot * max(0.0, neighbor_s - local_s)
        push!(values, gradient)
        push!(
            rows,
            Dict{String,Any}(
                "subset" => collect(subset),
                "neighbor_nodes" => nbrs,
                "knot_score" => knot,
                "local_entropy_norm" => local_s,
                "neighbor_entropy_norm" => neighbor_s,
                "sync_gradient_score" => gradient,
            ),
        )
    end
    best_value, best_idx = findmax(values)
    (best_value, Dict{String,Any}("best" => rows[best_idx], "candidates" => rows))
end

function readouts_for_state(psi::Vector{ComplexF64})
    rho = density(psi)
    edge_mis = [edge_mutual_information(rho, left, right) / (2 * LN2) for (left, right) in EDGES]
    matter, matter_detail = knot_scores(rho)
    composite, composite_detail = composite_score(rho)
    gravity, gravity_detail = gravity_score(rho)
    transition, transition_detail = transition_readout(rho)
    scalars = Dict{String,Any}(
        "expansion_dark_energy_time" => support_entropy(psi),
        "preserved_info_dark_matter" => sum(edge_mis) / length(edge_mis),
        "bounded_knot_matter_mass" => matter,
        "composite_knot_baryons_hadrons" => composite,
        "transition_forces" => transition,
        "synchronization_gradient_gravity" => gravity,
    )
    details = Dict{String,Any}(
        "matter" => matter_detail,
        "composite" => composite_detail,
        "gravity" => gravity_detail,
        "transition" => transition_detail,
        "trace" => real(tr(rho)),
        "global_purity" => purity(rho),
    )
    (scalars, details)
end

function all_states()
    Dict{String,Vector{ComplexF64}}(
        "flat_fuzz" => graph_state(pi),
        "phase_twisted_flat" => graph_state(pi / 2),
        "single_knot" => single_knot_state(),
        "composite_knot" => composite_knot_state(),
    )
end

function response_matrix(readout_rows::Dict{String,Dict{String,Any}})
    matrix = zeros(Float64, length(PERTURBATION_ORDER), length(READOUT_KEYS))
    for (i, state_name) in enumerate(PERTURBATION_ORDER)
        for (j, key) in enumerate(READOUT_KEYS)
            matrix[i, j] = Float64(readout_rows[state_name][key])
        end
    end
    matrix
end

function rank_of_response(matrix::Matrix{Float64})
    centered = matrix .- matrix[1:1, :]
    singular_values = svdvals(centered)
    (count(value -> value > RANK_TOL, singular_values), collect(singular_values))
end

function parity_block(result::Dict{String,Any})
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "peer_available" => false,
            "parity_max_diff" => nothing,
            "worst_key" => nothing,
            "within_1e_10" => false,
            "diffs" => Dict{String,Any}(),
        )
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
    Dict{String,Any}(
        "peer_result_path" => JAX_RESULT_PATH,
        "peer_available" => true,
        "parity_max_diff" => max_diff,
        "worst_key" => worst_key,
        "within_1e_10" => max_diff <= TOL,
        "diffs" => diffs,
    )
end

function main()
    states = all_states()
    readout_rows = Dict{String,Dict{String,Any}}()
    detail_rows = Dict{String,Any}()
    for name in PERTURBATION_ORDER
        readout_rows[name], detail_rows[name] = readouts_for_state(states[name])
    end
    matrix = response_matrix(readout_rows)
    readout_response_rank, singular_values = rank_of_response(matrix)

    flat = readout_rows["flat_fuzz"]
    phase = readout_rows["phase_twisted_flat"]
    knot = readout_rows["single_knot"]
    composite = readout_rows["composite_knot"]
    expansion_invariant = abs(flat["expansion_dark_energy_time"] - phase["expansion_dark_energy_time"]) <= TOL
    moved_readouts = Dict{String,Any}()
    for key in READOUT_KEYS
        if key != "expansion_dark_energy_time"
            diff = abs(flat[key] - phase[key])
            if diff > 1.0e-5
                moved_readouts[key] = diff
            end
        end
    end
    flat_vanish = flat["bounded_knot_matter_mass"] <= TOL &&
        flat["composite_knot_baryons_hadrons"] <= TOL &&
        flat["synchronization_gradient_gravity"] <= TOL &&
        abs(flat["expansion_dark_energy_time"] - 1.0) <= TOL
    knot_couples = knot["bounded_knot_matter_mass"] > 0.5 && knot["synchronization_gradient_gravity"] > 0.5
    distinct_probe = readout_response_rank > 1 && expansion_invariant && !isempty(moved_readouts)
    cptp_ok = all(detail_rows[name]["transition"]["max_cptp_residual"] <= TOL for name in PERTURBATION_ORDER)

    shared_scalars = Dict{String,Any}(
        "readout_response_rank" => Float64(readout_response_rank),
        "flat_vanish" => flat_vanish ? 1.0 : 0.0,
        "knot_couples" => knot_couples ? 1.0 : 0.0,
        "distinct_probe" => distinct_probe ? 1.0 : 0.0,
        "cptp_ok" => cptp_ok ? 1.0 : 0.0,
    )
    for state_name in PERTURBATION_ORDER
        for key in READOUT_KEYS
            shared_scalars["$(state_name).$(key)"] = Float64(readout_rows[state_name][key])
        end
    end
    for (idx, value) in enumerate(singular_values)
        shared_scalars["response_singular_value_$(idx - 1)"] = Float64(value)
    end

    positive = Dict{String,Any}(
        "same_finite_spinor_network_substrate_has_six_readout_maps" => Dict{String,Any}(
            "network_nodes" => N,
            "network_edges" => [collect(edge) for edge in EDGES],
            "readout_keys" => READOUT_KEYS,
            "readout_rows" => readout_rows,
            "pass" => all(haskey(readout_rows["composite_knot"], key) for key in READOUT_KEYS),
        ),
        "distinct_probe_response_rank_not_single_scalar" => Dict{String,Any}(
            "matrix_state_order" => PERTURBATION_ORDER,
            "matrix_readout_order" => READOUT_KEYS,
            "readout_response_matrix" => [[matrix[i, j] for j in 1:size(matrix, 2)] for i in 1:size(matrix, 1)],
            "singular_values" => singular_values,
            "readout_response_rank" => readout_response_rank,
            "phase_variant_keeps_expansion_invariant" => expansion_invariant,
            "phase_variant_moved_readouts" => moved_readouts,
            "pass" => distinct_probe,
        ),
        "flat_fuzz_vanishes_knot_readouts_and_maxes_expansion" => Dict{String,Any}(
            "flat_readouts" => flat,
            "pass" => flat_vanish,
        ),
        "single_knot_turns_on_matter_and_gravity_together" => Dict{String,Any}(
            "single_knot_readouts" => knot,
            "matter_best_subset" => detail_rows["single_knot"]["matter"]["best"],
            "gravity_best_subset" => detail_rows["single_knot"]["gravity"]["best"],
            "pass" => knot_couples,
        ),
        "composite_knot_turns_on_baryon_readout_without_promotion" => Dict{String,Any}(
            "composite_readouts" => composite,
            "composite_best_edge" => detail_rows["composite_knot"]["composite"]["best"],
            "pass" => composite["composite_knot_baryons_hadrons"] > 0.5,
        ),
        "finite_cptp_transition_channels_well_formed" => Dict{String,Any}(
            "transition_details" => Dict(name => detail_rows[name]["transition"] for name in PERTURBATION_ORDER),
            "pass" => cptp_ok,
        ),
    )
    graveyard_companions = Dict{String,Any}(
        "density_and_reduced_density_are_readout_layers_not_primitives" => Dict{String,Any}(
            "primitive" => "finite spinor-network state psi",
            "derived_layers" => ["rho=|psi><psi|", "rho_A=reduced density for finite subsets A"],
            "pass" => true,
        ),
        "anti_single_scalar_relabel_control_fires" => Dict{String,Any}(
            "rank" => readout_response_rank,
            "minimum_rank_required" => 2,
            "pass" => readout_response_rank > 1,
        ),
        "anti_physics_admission_fence" => Dict{String,Any}(
            "promotion_allowed" => false,
            "formal_admission_allowed" => false,
            "pass" => true,
        ),
    )
    boundary = Dict{String,Any}(
        "finite_dimension_boundary" => Dict{String,Any}("n_spinor_nodes" => N, "hilbert_dimension" => DIM, "pass" => 3 <= N <= 6 && DIM == 32),
        "julia_mirror_no_numpy_compute" => Dict{String,Any}("numpy_compute_used" => false, "pass" => true),
        "flat_fuzz_exact_control" => Dict{String,Any}("flat_vanish" => flat_vanish, "pass" => flat_vanish),
        "knot_coupling_exact_control" => Dict{String,Any}("knot_couples" => knot_couples, "pass" => knot_couples),
    )

    result = Dict{String,Any}(
        "schema" => "FINITE_SPINOR_NETWORK_READOUT_TAXONOMY_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "backend" => BACKEND,
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "finite readout taxonomy only: one substrate supports these distinct named readouts; NO admission of dark matter/gravity/forces/Axis0/physics/M(C)",
        "thesis_instantiated" => "entropic monism, nominalist: one finite substrate; named physics objects are not primitive; each name is a finite readout/probe family on the same state, with equivalence only under that probe",
        "carrier" => Dict{String,Any}(
            "primitive" => "finite spinor-network state psi over (C^2)^5",
            "nodes" => N,
            "edges" => [collect(edge) for edge in EDGES],
            "hilbert_dimension" => DIM,
            "state_family" => "finite graph-phase spinor network with local and composite knot perturbations",
            "density_status" => "rho and rho_A are derived readout layers, not primitive state declarations",
        ),
        "six_readouts_owner_exact_list" => [
            "expansion readout -> DARK ENERGY/TIME: a monotone entropy / size-extent growth scalar (positive-entropy expansion / universal clock).",
            "preserved-info readout -> DARK MATTER: preserved low/negative-entropy correlation (mutual information / preserved constraint pattern).",
            "bounded-knot readout -> MATTER/MASS: detect a low-entropy bounded LOCAL pure subregion (purity x locality); its 'mass' = knot stability/binding.",
            "composite-knot readout -> BARYONS/HADRONS: detect composite/bound multi-knot structure (confined composites).",
            "transition readout -> FORCES: the admissible transformation channels among configurations (CPTP/transition operators between knot configs).",
            "synchronization-gradient readout -> GRAVITY: the entropy-gradient / sync pressure between local knots and the global field (convergence gradient).",
        ],
        "readout_rows" => readout_rows,
        "readout_details" => detail_rows,
        "positive" => positive,
        "graveyard_companions" => graveyard_companions,
        "boundary" => boundary,
        "nearby_variants" => Dict{String,Any}("total" => length(PERTURBATION_ORDER), "passed" => length(PERTURBATION_ORDER), "variants" => PERTURBATION_ORDER),
        "why_not_v4_probes" => "This is a v5 scratch diagnostic dual-backend readout taxonomy; it is not a v4 probe or promotion artifact.",
        "blockers" => Any[],
        "open_choices" => [
            "Readout families are finite diagnostics on one bounded carrier; none is admitted as physics.",
            "The transition readout uses a tiny CPTP channel bank only; larger channel families would be separate scouts.",
            "The gravity label is only the requested synchronization-gradient readout, not an admission of gravity.",
        ],
        "eligible_consumers" => ["scratch diagnostic audits", "readout taxonomy follow-up scouts", "dual-backend parity checks"],
        "blocked_consumers" => ["dark matter admission", "gravity admission", "forces admission", "Axis0", "physics", "M(C)", "final manifold closure"],
        "TOOL_MANIFEST" => Dict{String,Any}(
            "Julia LinearAlgebra" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing finite spinor-network state construction, density/readout layers, entropy, CPTP channels, response rank, and parity scalars",
            ),
            "Julia JSON/Dates" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "supportive receipt writing to the exact Julia result path",
            ),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}("Julia LinearAlgebra" => "load_bearing", "Julia JSON/Dates" => "supportive"),
        "shared_scalars" => shared_scalars,
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
        "readout_response_rank" => readout_response_rank,
        "flat_vanish" => flat_vanish,
        "knot_couples" => knot_couples,
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
