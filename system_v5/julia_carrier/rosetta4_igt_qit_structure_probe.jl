#!/usr/bin/env julia
# object_id: rosetta4_igt_qit_structure_probe
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "rosetta4_igt_qit_structure_probe"
const RESULT_PATH = joinpath(@__DIR__, "rosetta4_igt_qit_structure_probe_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "rosetta4_igt_qit_structure_probe_jax_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const SCORE_TOL = 1.0e-12
const DT = 0.002
const TERRAIN_STEPS = 360

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SM = ComplexF64[0 0; 1 0]
const P_UP = ComplexF64[1 0; 0 0]
const P_DN = ComplexF64[0 0; 0 1]
const N_GENERIC = normalize(Float64[0.37, -0.51, 0.78])
const H0 = N_GENERIC[1] .* SX .+ N_GENERIC[2] .* SY .+ N_GENERIC[3] .* SZ
const HC = 0.63 .* SZ
const EPS_F = 0.17
const EPS_V = 0.08
const EPS_P = 0.05
const GAMMA_F_Z = 0.46
const GAMMA_F_X = 0.19
const GAMMA_P = 2.35
const KAPPA_UP = 0.37
const KAPPA_DN = 0.23
const L_SHARED = [sqrt(GAMMA_F_Z) .* SZ, sqrt(GAMMA_F_X) .* SX]
const L_PIT = sqrt(GAMMA_P) .* SM
const PROJECTORS = [P_UP, P_DN]
const KAPPAS = [KAPPA_UP, KAPPA_DN]
const R0 = Float64[0.23, -0.31, 0.17]

const IGT_ORDER = ["Se", "Ne", "Ni", "Si"]
const QIT_ORDER = ["Funnel", "Vortex", "Pit", "Hill"]
const IGT_CW_CYCLE = ["Se", "Si", "Ni", "Ne"]
const CANONICAL_QIT_FOR_IGT = ["Vortex", "Funnel", "Pit", "Hill"]
const GRAMMAR_FEATURE_LABELS = [
    "first_slot_sign",
    "second_slot_sign",
    "cw_cycle_cos",
    "cw_cycle_sin",
    "hamming_class_centered",
]
const DYNAMICS_FEATURE_LABELS = [
    "terminal_z",
    "purity_delta",
    "dissipative_minus_unitary_mean",
    "fixed_point_type_code",
    "terminal_generator_norm",
]

dag(m) = m'
comm(h, rho) = h * rho - rho * h
bool_scalar(x::Bool) = x ? 1.0 : 0.0

function vec_payload(v)
    [Float64(x) for x in v]
end

function sign_scalar(x::Float64; tol::Float64=TOL)
    if x > tol
        return 1.0
    elseif x < -tol
        return -1.0
    end
    0.0
end

function permutations(v::Vector{Int})
    if length(v) <= 1
        return [copy(v)]
    end
    out = Vector{Vector{Int}}()
    for idx in eachindex(v)
        head = v[idx]
        rest = [v[j] for j in eachindex(v) if j != idx]
        for tail in permutations(rest)
            push!(out, vcat([head], tail))
        end
    end
    out
end

function grammar_label(igt_name::String)
    if igt_name == "Se"
        return ["Lose", "WIN"]
    elseif igt_name == "Ne"
        return ["Win", "LOSE"]
    elseif igt_name == "Ni"
        return ["Lose", "LOSE"]
    elseif igt_name == "Si"
        return ["Win", "WIN"]
    end
    error("unknown IGT terrain: $(igt_name)")
end

function qit_source_given_grammar(terrain::String)
    if terrain == "Funnel"
        return ["Win", "LOSE"]
    elseif terrain == "Vortex"
        return ["Lose", "WIN"]
    elseif terrain == "Pit"
        return ["Lose", "LOSE"]
    elseif terrain == "Hill"
        return ["Win", "WIN"]
    end
    error("unknown QIT terrain: $(terrain)")
end

function first_slot_sign(label::Vector{String})
    label[1] == "Win" ? 1.0 : -1.0
end

function second_slot_sign(label::Vector{String})
    label[2] == "WIN" ? 1.0 : -1.0
end

function hamming_from_winwin(label::Vector{String})
    (label[1] == "Win" ? 0.0 : 1.0) + (label[2] == "WIN" ? 0.0 : 1.0)
end

function build_grammar_features()
    out = Dict{String,Any}()
    cycle_index = Dict(IGT_CW_CYCLE[idx] => idx - 1 for idx in eachindex(IGT_CW_CYCLE))
    for terrain in IGT_ORDER
        label = grammar_label(terrain)
        pos = Float64(cycle_index[terrain])
        theta = 2.0 * pi * pos / 4.0
        features = Float64[
            first_slot_sign(label),
            second_slot_sign(label),
            cos(theta),
            sin(theta),
            hamming_from_winwin(label) - 1.0,
        ]
        out[terrain] = Dict{String,Any}(
            "terrain" => terrain,
            "grammar_label" => label,
            "source_given_assignment" => "$(terrain)=" * label[1] * label[2],
            "cw_cycle" => IGT_CW_CYCLE,
            "cw_cycle_position_zero_based" => pos,
            "hamming_from_WinWIN" => hamming_from_winwin(label),
            "feature_labels" => GRAMMAR_FEATURE_LABELS,
            "feature_vector" => vec_payload(features),
        )
    end
    out
end

function density_from_bloch(r::Vector{Float64})
    0.5 .* (I2 .+ r[1] .* SX .+ r[2] .* SY .+ r[3] .* SZ)
end

function bloch_vector(rho)
    Float64[
        real(tr(rho * SX)),
        real(tr(rho * SY)),
        real(tr(rho * SZ)),
    ]
end

function purity(rho)
    Float64(real(tr(rho * rho)))
end

function project_density(rho)
    rho_h = (rho + dag(rho)) ./ 2.0
    ev = eigen(Hermitian(rho_h))
    vals = max.(ev.values, 0.0)
    total = sum(vals)
    if total <= 1.0e-15
        return I2 ./ 2.0
    end
    rho_p = ev.vectors * Diagonal(vals) * dag(ev.vectors)
    rho_p = (rho_p + dag(rho_p)) ./ 2.0
    rho_p ./ real(tr(rho_p))
end

function dissipator(l, rho)
    ldl = dag(l) * l
    l * rho * dag(l) .- 0.5 .* (ldl * rho + rho * ldl)
end

function sum_dissipators(ls, rho)
    out = zeros(ComplexF64, 2, 2)
    for l in ls
        out .+= dissipator(l, rho)
    end
    out
end

function dephase_generator(rho)
    out = zeros(ComplexF64, 2, 2)
    for idx in eachindex(PROJECTORS)
        p = PROJECTORS[idx]
        kappa = KAPPAS[idx]
        out .+= kappa .* (p * rho * p .- 0.5 .* (p * rho + rho * p))
    end
    out
end

function terrain_generator_parts(terrain::String, rho)
    if terrain == "Funnel"
        dissipative = sum_dissipators(L_SHARED, rho)
        unitary = -im .* EPS_F .* comm(H0, rho)
        return unitary, dissipative
    elseif terrain == "Vortex"
        unitary = -im .* comm(H0, rho)
        dissipative = EPS_V .* sum_dissipators(L_SHARED, rho)
        return unitary, dissipative
    elseif terrain == "Pit"
        dissipative = dissipator(L_PIT, rho)
        unitary = -im .* EPS_P .* comm(H0, rho)
        return unitary, dissipative
    elseif terrain == "Hill"
        unitary = -im .* comm(HC, rho)
        dissipative = dephase_generator(rho)
        return unitary, dissipative
    end
    error("unknown Type-1 terrain: $(terrain)")
end

function terrain_generator(terrain::String, rho)
    unitary, dissipative = terrain_generator_parts(terrain, rho)
    unitary .+ dissipative
end

function rk4_step(rho, terrain::String)
    f(x) = terrain_generator(terrain, x)
    k1 = f(rho)
    k2 = f(rho .+ 0.5 .* DT .* k1)
    k3 = f(rho .+ 0.5 .* DT .* k2)
    k4 = f(rho .+ DT .* k3)
    project_density(rho .+ (DT / 6.0) .* (k1 .+ 2.0 .* k2 .+ 2.0 .* k3 .+ k4))
end

function fixed_point_readout(terminal_z::Float64, dissipative_fraction::Float64)
    if abs(terminal_z) > 0.5
        return terminal_z > 0.0 ? (1.0, "positive_z_attractor") : (-1.0, "negative_z_attractor")
    elseif dissipative_fraction < 0.5
        return 0.5, "unitary_dominant_nonfixed_orbit"
    end
    0.0, "dissipative_dephasing_or_mixed"
end

function integrate_signature(terrain::String)
    rho = density_from_bloch(R0)
    initial_purity = purity(rho)
    dissipative_fraction_sum = 0.0
    dissipative_minus_unitary_sum = 0.0
    speed_sum = 0.0
    for _ in 1:TERRAIN_STEPS
        unitary, dissipative = terrain_generator_parts(terrain, rho)
        unorm = norm(unitary)
        dnorm = norm(dissipative)
        denom = unorm + dnorm + 1.0e-15
        dissipative_fraction_sum += dnorm / denom
        dissipative_minus_unitary_sum += (dnorm - unorm) / denom
        speed_sum += norm(unitary .+ dissipative)
        rho = rk4_step(rho, terrain)
    end
    terminal_purity = purity(rho)
    terminal_bloch = bloch_vector(rho)
    terminal_z = terminal_bloch[3]
    terminal_generator_norm = norm(terrain_generator(terrain, rho))
    dissipative_fraction_mean = dissipative_fraction_sum / TERRAIN_STEPS
    dissipative_minus_unitary_mean = dissipative_minus_unitary_sum / TERRAIN_STEPS
    fixed_code, fixed_type = fixed_point_readout(terminal_z, dissipative_fraction_mean)
    features = Float64[
        terminal_z,
        terminal_purity - initial_purity,
        dissipative_minus_unitary_mean,
        fixed_code,
        terminal_generator_norm,
    ]
    Dict{String,Any}(
        "terrain" => terrain,
        "feature_labels" => DYNAMICS_FEATURE_LABELS,
        "feature_vector" => vec_payload(features),
        "terminal_bloch" => vec_payload(terminal_bloch),
        "terminal_z" => Float64(terminal_z),
        "terminal_z_sign" => sign_scalar(terminal_z),
        "initial_purity" => Float64(initial_purity),
        "terminal_purity" => Float64(terminal_purity),
        "purity_delta" => Float64(terminal_purity - initial_purity),
        "purity_trend_sign" => sign_scalar(terminal_purity - initial_purity),
        "dissipative_fraction_mean" => Float64(dissipative_fraction_mean),
        "unitary_fraction_mean" => Float64(1.0 - dissipative_fraction_mean),
        "dissipative_minus_unitary_mean" => Float64(dissipative_minus_unitary_mean),
        "dissipative_minus_unitary_sign" => sign_scalar(dissipative_minus_unitary_mean),
        "mean_generator_norm" => Float64(speed_sum / TERRAIN_STEPS),
        "terminal_generator_norm" => Float64(terminal_generator_norm),
        "fixed_point_type_code" => Float64(fixed_code),
        "fixed_point_type" => fixed_type,
    )
end

function build_dynamics_features()
    Dict{String,Any}(terrain => integrate_signature(terrain) for terrain in QIT_ORDER)
end

function feature_matrix(features::Dict{String,Any}, order::Vector{String})
    rows = Vector{Vector{Float64}}()
    for name in order
        push!(rows, [Float64(x) for x in features[name]["feature_vector"]])
    end
    rows
end

function standardize_rows(rows::Vector{Vector{Float64}})
    n = length(rows)
    p = length(rows[1])
    means = Float64[]
    stds = Float64[]
    for col in 1:p
        vals = [rows[row][col] for row in 1:n]
        m = sum(vals) / n
        s = sqrt(sum((x - m)^2 for x in vals) / n)
        push!(means, m)
        push!(stds, s)
    end
    out = Vector{Vector{Float64}}()
    for row in 1:n
        zrow = Float64[]
        for col in 1:p
            if stds[col] <= 1.0e-15
                push!(zrow, 0.0)
            else
                push!(zrow, (rows[row][col] - means[col]) / stds[col])
            end
        end
        push!(out, zrow)
    end
    out, means, stds
end

function euclidean(a::Vector{Float64}, b::Vector{Float64})
    sqrt(sum((a[idx] - b[idx])^2 for idx in eachindex(a)))
end

function pairwise_distances(rows::Vector{Vector{Float64}})
    out = Float64[]
    pairs = Vector{Vector{Int}}()
    for i in 1:length(rows)-1
        for j in i+1:length(rows)
            push!(out, euclidean(rows[i], rows[j]))
            push!(pairs, [i, j])
        end
    end
    out, pairs
end

function pearson(a::Vector{Float64}, b::Vector{Float64})
    n = length(a)
    ma = sum(a) / n
    mb = sum(b) / n
    da = [x - ma for x in a]
    db = [x - mb for x in b]
    denom = sqrt(sum(x^2 for x in da) * sum(x^2 for x in db))
    if denom <= 1.0e-15
        return 0.0
    end
    sum(da[idx] * db[idx] for idx in 1:n) / denom
end

function permutation_labels(perm::Vector{Int})
    [QIT_ORDER[idx] for idx in perm]
end

function score_permutations(grammar_features, dynamics_features)
    grammar_rows = feature_matrix(grammar_features, IGT_ORDER)
    dynamics_rows = feature_matrix(dynamics_features, QIT_ORDER)
    grammar_z, grammar_means, grammar_stds = standardize_rows(grammar_rows)
    dynamics_z, dynamics_means, dynamics_stds = standardize_rows(dynamics_rows)
    grammar_distances, pair_indices = pairwise_distances(grammar_z)
    perms = permutations(collect(1:4))
    canonical_perm = [findfirst(==(terrain), QIT_ORDER) for terrain in CANONICAL_QIT_FOR_IGT]

    rows = Vector{Dict{String,Any}}()
    scores = Float64[]
    canonical_score = NaN
    for perm in perms
        permuted_rows = [dynamics_z[idx] for idx in perm]
        qit_distances, _ = pairwise_distances(permuted_rows)
        score = pearson(grammar_distances, qit_distances)
        push!(scores, score)
        is_canonical = perm == canonical_perm
        if is_canonical
            canonical_score = score
        end
        push!(rows, Dict{String,Any}(
            "permutation_1_based" => perm,
            "igt_order" => IGT_ORDER,
            "qit_order_for_igt_order" => permutation_labels(perm),
            "score" => Float64(score),
            "is_canonical_source_given" => is_canonical,
        ))
    end

    score_mean = sum(scores) / length(scores)
    score_std = sqrt(sum((x - score_mean)^2 for x in scores) / length(scores))
    z = score_std <= 1.0e-15 ? 0.0 : (canonical_score - score_mean) / score_std
    max_score = maximum(scores)
    n_ge = count(x -> x >= canonical_score - SCORE_TOL, scores)
    n_max = count(x -> x >= max_score - SCORE_TOL, scores)
    canonical_is_unique_max = canonical_score >= max_score - SCORE_TOL && n_max == 1
    exact_p_ge = n_ge / length(scores)
    significant = canonical_score > score_mean && exact_p_ge <= 0.05 && z > 0.0
    shared = canonical_is_unique_max && significant
    trivial = !shared || n_ge > 1

    Dict{String,Any}(
        "score_method" => "Pearson correlation between the six pairwise Euclidean distances of backend-local z-scored feature vectors; no per-dimension semantic crosswalk is fit.",
        "igt_order" => IGT_ORDER,
        "qit_base_order" => QIT_ORDER,
        "canonical_qit_order_for_igt_order" => CANONICAL_QIT_FOR_IGT,
        "canonical_permutation_1_based" => canonical_perm,
        "grammar_pair_indices_igt_order_1_based" => pair_indices,
        "grammar_pairwise_distances_zscored" => vec_payload(grammar_distances),
        "grammar_feature_means" => vec_payload(grammar_means),
        "grammar_feature_stds" => vec_payload(grammar_stds),
        "dynamics_feature_means" => vec_payload(dynamics_means),
        "dynamics_feature_stds" => vec_payload(dynamics_stds),
        "rows" => rows,
        "scores" => vec_payload(scores),
        "score_mean" => Float64(score_mean),
        "score_std" => Float64(score_std),
        "max_score" => Float64(max_score),
        "canonical_bijection_score" => Float64(canonical_score),
        "canonical_gap_above_null_mean" => Float64(canonical_score - score_mean),
        "canonical_z_above_null" => Float64(z),
        "n_permutations_ge_canonical" => n_ge,
        "canonical_exact_p_ge" => Float64(exact_p_ge),
        "canonical_is_unique_max" => canonical_is_unique_max,
        "canonical_significant_above_null" => significant,
        "shared_structure_invariant" => shared,
        "rosetta4_is_trivial" => trivial,
        "exactly_24_bijections_scored" => length(rows) == 24,
    )
end

function flatten_feature_scalars!(shared_scalars, prefix::String, features, order::Vector{String})
    for name in order
        vector = features[name]["feature_vector"]
        labels = features[name]["feature_labels"]
        for idx in eachindex(vector)
            shared_scalars["$(prefix)_$(name)_feature_$(idx)_$(labels[idx])"] = Float64(vector[idx])
        end
    end
end

function parity_block(result::Dict{String,Any})
    if !isfile(JAX_REFERENCE_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_REFERENCE_PATH,
            "peer_available" => false,
            "parity_max_diff" => nothing,
            "worst_key" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => false,
            "missing_from_peer" => collect(keys(result["shared_scalars"])),
            "missing_from_self" => String[],
            "diffs" => Dict{String,Any}(),
            "status" => "pending_peer",
        )
    end
    peer = JSON.parsefile(JAX_REFERENCE_PATH)
    self_scalars = result["shared_scalars"]
    peer_scalars = peer["shared_scalars"]
    missing_from_peer = sort(collect(setdiff(Set(keys(self_scalars)), Set(keys(peer_scalars)))))
    missing_from_self = sort(collect(setdiff(Set(keys(peer_scalars)), Set(keys(self_scalars)))))
    diffs = Dict{String,Any}()
    max_diff = 0.0
    worst_key = ""
    for key in sort(collect(intersect(Set(keys(self_scalars)), Set(keys(peer_scalars)))))
        diff = abs(Float64(self_scalars[key]) - Float64(peer_scalars[key]))
        diffs[key] = diff
        if diff > max_diff
            max_diff = diff
            worst_key = key
        end
    end
    within = isempty(missing_from_peer) && isempty(missing_from_self) && max_diff < TOL
    strict_divergence = !isempty(missing_from_peer) || !isempty(missing_from_self) || max_diff > STRICT_STOP_TOL
    Dict{String,Any}(
        "peer_result_path" => JAX_REFERENCE_PATH,
        "peer_available" => true,
        "parity_max_diff" => Float64(max_diff),
        "worst_key" => worst_key,
        "within_1e_9" => within,
        "strict_divergence_gt_1e_6" => strict_divergence,
        "missing_from_peer" => missing_from_peer,
        "missing_from_self" => missing_from_self,
        "diffs" => diffs,
        "status" => within ? "pass" : "fail_closed",
    )
end

function build_result()
    grammar_features = build_grammar_features()
    dynamics_features = build_dynamics_features()
    rosetta = score_permutations(grammar_features, dynamics_features)
    verdicts = Dict{String,Any}(
        "exactly_24_bijections_scored" => rosetta["exactly_24_bijections_scored"],
        "canonical_bijection_score" => rosetta["canonical_bijection_score"],
        "n_permutations_ge_canonical" => rosetta["n_permutations_ge_canonical"],
        "canonical_is_unique_max" => rosetta["canonical_is_unique_max"],
        "canonical_z_above_null" => rosetta["canonical_z_above_null"],
        "shared_structure_invariant" => rosetta["shared_structure_invariant"],
        "rosetta4_is_trivial" => rosetta["rosetta4_is_trivial"],
    )

    shared_scalars = Dict{String,Any}(
        "exactly_24_bijections_scored_flag" => bool_scalar(verdicts["exactly_24_bijections_scored"]::Bool),
        "canonical_bijection_score" => Float64(verdicts["canonical_bijection_score"]),
        "n_permutations_ge_canonical" => Float64(verdicts["n_permutations_ge_canonical"]),
        "canonical_is_unique_max_flag" => bool_scalar(verdicts["canonical_is_unique_max"]::Bool),
        "canonical_z_above_null" => Float64(verdicts["canonical_z_above_null"]),
        "canonical_gap_above_null_mean" => Float64(rosetta["canonical_gap_above_null_mean"]),
        "canonical_exact_p_ge" => Float64(rosetta["canonical_exact_p_ge"]),
        "shared_structure_invariant_flag" => bool_scalar(verdicts["shared_structure_invariant"]::Bool),
        "rosetta4_is_trivial_flag" => bool_scalar(verdicts["rosetta4_is_trivial"]::Bool),
        "permutation_score_mean" => Float64(rosetta["score_mean"]),
        "permutation_score_std" => Float64(rosetta["score_std"]),
        "permutation_max_score" => Float64(rosetta["max_score"]),
        "numpy_compute_used_flag" => 0.0,
        "promotion_allowed_flag" => 0.0,
    )
    flatten_feature_scalars!(shared_scalars, "igt", grammar_features, IGT_ORDER)
    flatten_feature_scalars!(shared_scalars, "qit", dynamics_features, QIT_ORDER)

    tool_manifest = Dict(
        "Julia LinearAlgebra" => Dict(
            "tried" => true,
            "used" => true,
            "role" => "reference_native_linearalgebra",
            "reason" => "load-bearing for Type-1 terrain Lindblad/RK4 density-matrix dynamics, PSD projection, feature extraction, and exhaustive 24-bijection scoring",
        ),
        "JAX jax.numpy x64" => Dict(
            "tried" => true,
            "used" => false,
            "role" => "peer_mirror_expected",
            "reason" => "supportive peer parity lane read from its result JSON when present; no JAX compute is used inside Julia",
        ),
        "Python stdlib itertools/json" => Dict(
            "tried" => true,
            "used" => false,
            "role" => "peer_mirror_expected",
            "reason" => "supportive mirror lane only; Julia uses native recursion and JSON.jl",
        ),
    )
    tool_depth = Dict(
        "Julia LinearAlgebra" => "load_bearing",
        "JAX jax.numpy x64" => "supportive",
        "Python stdlib itertools/json" => "supportive",
    )

    result = Dict{String,Any}(
        "sim_id" => OBJECT_ID,
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "version" => "1.0.0",
        "backend" => "julia",
        "backend_roles" => Dict(
            "julia" => "reference_native_linearalgebra_no_pycall_no_numpy",
            "jax" => "mirror_stress_jnp_x64_no_numpy",
        ),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "PROMOTION_ALLOWED" => false,
        "FORMAL_ADMISSION_ALLOWED" => false,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "dual_backend_rosetta4_structure_probe",
        "carrier_layer" => "igt_two_ring_grammar_and_single_qubit_type1_density_matrix_terrain_dynamics",
        "geometry_layer" => "four_element_structure_alignment_null",
        "claim_ceiling" => "Scratch diagnostic only: tests whether a source-given IGT win/lose grammar assignment uniquely aligns with independently integrated Type-1 QIT terrain dynamics; no admission or promotion claim.",
        "allowed_claims" => [
            "IGT grammar features are computed from the two-slot win/lose x WIN/LOSE grammar and the source-given Se/Ne/Ni/Si cycle only",
            "QIT dynamics features are computed from integrated Type-1 terrain equations only, without win/lose labels",
            "Rosetta scoring exhausts all 24 IGT-to-QIT bijections and reports whether the source-given canonical bijection is uniquely best",
            "A trivial/uninformative result is an accepted diagnostic outcome when random permutations tie or beat the canonical bijection",
        ],
        "blocked_consumers" => [
            "formal_admission",
            "QIT_engine_admission",
            "Axis0",
            "bridge",
            "canonical_engine_evidence",
            "promotion",
        ],
        "out_of_scope" => [
            "admission claim",
            "philosophy claim",
            "QIT terrain labels derived from win/lose during dynamics extraction",
            "feature tuning to force uniqueness",
        ],
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "score_tol" => SCORE_TOL,
        "dt" => DT,
        "terrain_steps" => TERRAIN_STEPS,
        "h0_generic_n" => vec_payload(N_GENERIC),
        "initial_bloch" => vec_payload(R0),
        "anti_circularity" => Dict(
            "genealogy_rule" => "Sim both sides independently; do not derive either feature family from the other; exhaust the permutation null.",
            "igt_feature_source" => "2-ring win/lose combinatorics only: source-given Se=LoseWin, Ne=WinLose, Ni=LoseLose, Si=WinWin plus CW cycle Se->Si->Ni->Ne.",
            "qit_feature_source" => "Type-1 Funnel/Vortex/Pit/Hill terrain equations only: integrated rho dynamics, terminal Bloch readouts, purity trend, generator norm split, and fixed-point readout.",
            "canonical_assignment_status" => "SOURCE-GIVEN, not fit. Existing Type-1 placement grammar gives Funnel=WinLose, Vortex=LoseWin, Pit=LoseLose, Hill=WinWin; therefore canonical IGT order [Se,Ne,Ni,Si] maps to [Vortex,Funnel,Pit,Hill]. This assignment is used only to pick the canonical permutation after features are computed.",
        ),
        "engine_equations_type1" => Dict(
            "Funnel" => "sum_k D_Lk(rho) - i eps_F [H0,rho]",
            "Vortex" => "-i[H0,rho] + eps_V sum_k D_Lk(rho)",
            "Pit" => "D_sigma_minus(rho) - i eps_P [H0,rho]",
            "Hill" => "-i[H_C,rho] + sum_j kappa_j(P_j rho P_j - 0.5{P_j,rho})",
        ),
        "grammar_feature_labels" => GRAMMAR_FEATURE_LABELS,
        "dynamics_feature_labels" => DYNAMICS_FEATURE_LABELS,
        "grammar_features" => grammar_features,
        "dynamics_features" => dynamics_features,
        "rosetta4_test" => rosetta,
        "verdicts" => verdicts,
        "shared_scalars" => shared_scalars,
        "tools" => ["Julia LinearAlgebra", "JAX jax.numpy x64", "Python stdlib itertools/json"],
        "tool_manifest" => tool_manifest,
        "TOOL_MANIFEST" => tool_manifest,
        "tool_integration_depth" => tool_depth,
        "TOOL_INTEGRATION_DEPTH" => tool_depth,
        "numpy_compute_used" => false,
        "jax_x64_enabled" => nothing,
        "divergence_log" => [
            "IGT side did not read or integrate QIT dynamics.",
            "QIT side did not use win/lose labels to compute terrain signatures.",
            "All 24 bijections are scored; the decisive control is n_permutations_ge_canonical.",
            "shared_structure_invariant is true only if the source-given canonical bijection is the unique maximum and the exact permutation p-value is <= 0.05.",
            "rosetta4_is_trivial is true when the canonical bijection is tied/beaten or otherwise not significant against the exhaustive permutation null.",
        ],
    )
    result["parity"] = parity_block(result)
    result["all_pass"] =
        !(result["numpy_compute_used"]::Bool) &&
        (verdicts["exactly_24_bijections_scored"]::Bool) &&
        (result["parity"]["within_1e_9"]::Bool)
    result["stop_condition_fired"] = result["parity"]["strict_divergence_gt_1e_6"]::Bool
    result["plain_sentence"] =
        (verdicts["shared_structure_invariant"]::Bool) ?
        "The source-given IGT win/lose grammar uniquely aligns with the independent QIT terrain dynamics under this four-element permutation-null test." :
        "The source-given IGT win/lose grammar does not uniquely align with the independent QIT terrain dynamics under this four-element permutation-null test; the result is trivial/uninformative."
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    s = result["shared_scalars"]
    println("rosetta4_igt_qit_structure_probe julia wrote $(RESULT_PATH)")
    println("canonical_score=$(s["canonical_bijection_score"]) n_ge=$(s["n_permutations_ge_canonical"])/24 unique=$(result["verdicts"]["canonical_is_unique_max"]) z=$(s["canonical_z_above_null"])")
    println("shared_structure_invariant=$(result["verdicts"]["shared_structure_invariant"]) rosetta4_is_trivial=$(result["verdicts"]["rosetta4_is_trivial"])")
    println("parity_max_diff=$(result["parity"]["parity_max_diff"]) numpy_compute_used=$(result["numpy_compute_used"])")
    if result["stop_condition_fired"]
        println("STOP_CONDITION_FIRED rosetta4_igt_qit_structure_probe julia")
        exit(1)
    end
end

main()
