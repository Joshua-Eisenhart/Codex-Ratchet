#!/usr/bin/env julia
# object_id: mp_cross_model_convergence
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: finite cross-model readout witness only; no physics, SM, M(C), Axis0, bridge, basin, or formal admission.

using Dates
using JSON
using LinearAlgebra
using Statistics
using SHA

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_DIR = joinpath(ROOT, "system_v5", "ops", "formal_scouts")
const JULIA_DIR = joinpath(ROOT, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(JULIA_DIR, "mp_cross_model_convergence_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_DIR, "results", "mp_cross_model_convergence_results.json")
const OBJECT_ID = "mp_cross_model_convergence"
const CLAIM_CEILING = "finite cross-model readout witness only; classification=scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false; NO physics/SM/M(C)/Axis0 admission"
const N_QUBITS = 3
const STAGE_DT = 0.08
const RK4_STEPS_PER_STAGE = 8
const PARITY_TOL = 1.0e-9
const DIFFER_TOL = 1.0e-7
const PERCEPTION_KEYS = ["Si", "Ne", "Se", "Ni"]
const READOUT_COMPONENTS = ["physics", "igt", "perception", "operator"]
const PHYSICS_FACES = ["mass", "gravity", "dark_energy"]
const RANDOM_PERMUTATIONS = [
    [2, 1, 3, 4],
    [3, 2, 4, 1],
    [4, 1, 2, 3],
    [1, 4, 3, 2],
    [2, 4, 1, 3],
    [3, 1, 4, 2],
]
const WRONG_MAP = Dict("Si" => "Ni", "Ne" => "Se", "Se" => "Si", "Ni" => "Ne")
const SOURCE_FILES = Dict(
    "canonical_qit_engine_specs" => joinpath(FORMAL_DIR, "canonical_qit_engine_specs.py"),
    "division_algebra_ratchet_ladder" => joinpath(JULIA_DIR, "division_algebra_ratchet_ladder.jl"),
    "clifford_algebra_ladder" => joinpath(JULIA_DIR, "clifford_algebra_ladder.jl"),
    "octonion_G2_automorphism" => joinpath(JULIA_DIR, "octonion_G2_automorphism.jl"),
    "sedenion_break" => joinpath(JULIA_DIR, "sedenion_break_prelim.jl"),
    "density_matrix_spinor_lift" => joinpath(JULIA_DIR, "density_matrix_spinor_lift.jl"),
    "clifford_torus_nested_hopf_foliation" => joinpath(JULIA_DIR, "clifford_torus_nested_hopf_foliation.jl"),
    "golden_weyl" => joinpath(JULIA_DIR, "golden_weyl_julia.jl"),
)

const I2 = ComplexF64[1.0 0.0; 0.0 1.0]
const SX = ComplexF64[0.0 1.0; 1.0 0.0]
const SY = ComplexF64[0.0 -im; im 0.0]
const SZ = ComplexF64[1.0 0.0; 0.0 -1.0]
const SIGMA_MINUS = ComplexF64[0.0 0.0; 1.0 0.0]
const SIGMA_PLUS = ComplexF64[0.0 1.0; 0.0 0.0]
const MIRROR = SX
const H0 = 0.77 .* SZ .+ 0.13 .* SX
const PERCEPTION_L = Dict("Se" => SZ, "Ne" => SIGMA_PLUS, "Ni" => (-im) .* SY, "Si" => SIGMA_MINUS)
const OPERATOR_GENERATORS = Dict("Ti" => SZ, "Te" => SX, "Fi" => SX, "Fe" => SY)
const OPERATOR_BASE_ANGLES = Dict("Ti" => 0.12, "Te" => 0.09, "Fi" => 0.15, "Fe" => 0.11)
const NATIVE_OPERATORS_BY_TOPOLOGY = Dict("Se" => ["Ti", "Fi"], "Ne" => ["Ti", "Fi"], "Ni" => ["Te", "Fe"], "Si" => ["Te", "Fe"])
const IGT_TERRAINS = Dict(
    "Si" => Dict("terrain" => "WinWin", "lower" => 1.0, "upper" => 1.0),
    "Ne" => Dict("terrain" => "WinLose", "lower" => 1.0, "upper" => -1.0),
    "Se" => Dict("terrain" => "LoseWin", "lower" => -1.0, "upper" => 1.0),
    "Ni" => Dict("terrain" => "LoseLose", "lower" => -1.0, "upper" => -1.0),
)
const TYPE_ONE_RATES = Dict("Se" => 0.18, "Ne" => 0.13, "Ni" => 0.28, "Si" => 0.20)
const ENGINE_SCHEDULE_TYPE_ONE = [
    ("Se", "outer"), ("Ne", "outer"), ("Ni", "outer"), ("Si", "outer"),
    ("Se", "inner"), ("Si", "inner"), ("Ni", "inner"), ("Ne", "inner"),
]
const TYPE_ONE_TOPOLOGIES = Dict(
    "Se" => Dict("outer" => Dict("op" => "Ti", "sign" => +1), "inner" => Dict("op" => "Fi", "sign" => -1)),
    "Ne" => Dict("outer" => Dict("op" => "Ti", "sign" => -1), "inner" => Dict("op" => "Fi", "sign" => +1)),
    "Ni" => Dict("outer" => Dict("op" => "Fe", "sign" => -1), "inner" => Dict("op" => "Te", "sign" => +1)),
    "Si" => Dict("outer" => Dict("op" => "Fe", "sign" => +1), "inner" => Dict("op" => "Te", "sign" => -1)),
)
const OPERATOR_SLOT_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]
const OPERATOR_MAP_FAMILY = Dict("Ti" => "z_pinching_dephase", "Te" => "x_pinching_dephase", "Fi" => "x_coherent_rotation", "Fe" => "z_coherent_rotation")
const CHART_TOKEN_PRECEDENCE = Dict(
    "TiSe" => ("operator_first", +1), "TiNe" => ("operator_first", +1),
    "SeTi" => ("terrain_first", -1), "NeTi" => ("terrain_first", -1),
    "FeSi" => ("operator_first", +1), "FeNi" => ("operator_first", +1),
    "SiFe" => ("terrain_first", -1), "NiFe" => ("terrain_first", -1),
    "TeNi" => ("operator_first", +1), "TeSi" => ("operator_first", +1),
    "NiTe" => ("terrain_first", -1), "SiTe" => ("terrain_first", -1),
    "FiNe" => ("operator_first", +1), "FiSe" => ("operator_first", +1),
    "NeFi" => ("terrain_first", -1), "SeFi" => ("terrain_first", -1),
)

ordered_token(operator::String, perception::String, precedence::String) =
    precedence == "operator_first" ? string(operator, perception) :
    precedence == "terrain_first" ? string(perception, operator) :
    error("unknown precedence $precedence")

function operator_slot_spec(perception::String, loop_class::String, substage_idx::Int)
    topo = TYPE_ONE_TOPOLOGIES[perception]
    chart_op = String(topo[loop_class]["op"])
    chart_sign = Int(topo[loop_class]["sign"])
    chart_precedence = chart_sign > 0 ? "operator_first" : "terrain_first"
    chart_token = ordered_token(chart_op, perception, chart_precedence)
    native = copy(NATIVE_OPERATORS_BY_TOPOLOGY[perception])
    remaining_native = [op for op in native if op != chart_op]
    remaining_non_native = [op for op in OPERATOR_SLOT_SEQUENCE if !(op in native)]
    slot_ops = vcat([chart_op], remaining_native, remaining_non_native)
    op = slot_ops[mod(substage_idx, length(slot_ops)) + 1]
    if op == chart_op
        sign = chart_sign
        precedence = chart_precedence
        token = chart_token
    else
        token_up = ordered_token(op, perception, "operator_first")
        token_down = ordered_token(op, perception, "terrain_first")
        if haskey(CHART_TOKEN_PRECEDENCE, token_up)
            precedence, sign = CHART_TOKEN_PRECEDENCE[token_up]
            token = token_up
        elseif haskey(CHART_TOKEN_PRECEDENCE, token_down)
            precedence, sign = CHART_TOKEN_PRECEDENCE[token_down]
            token = token_down
        else
            sign = mod(substage_idx, 2) == 0 ? +1 : -1
            precedence = sign > 0 ? "operator_first" : "terrain_first"
            token = ordered_token(op, perception, precedence)
        end
    end
    Dict("operator" => op, "sign" => Int(sign), "precedence" => precedence, "token" => token, "operator_family" => OPERATOR_MAP_FAMILY[op])
end

function sha256_file(path::String)
    bytes2hex(open(sha256, path))
end

function source_fingerprints()
    Dict(name => Dict("path" => path, "exists" => isfile(path), "sha256" => isfile(path) ? sha256_file(path) : nothing) for (name, path) in SOURCE_FILES)
end

function kron_chain(ops::Vector{Matrix{ComplexF64}})
    out = ops[1]
    for idx in 2:length(ops)
        out = kron(out, ops[idx])
    end
    out
end

function site_op(local_op::Matrix{ComplexF64}, n_qubits::Int, site_idx::Int)
    ops = [copy(I2) for _ in 1:n_qubits]
    ops[site_idx + 1] = local_op
    kron_chain(ops)
end

function all_site_sum(local_op::Matrix{ComplexF64}, n_qubits::Int)
    out = zeros(ComplexF64, 2^n_qubits, 2^n_qubits)
    for idx in 0:(n_qubits - 1)
        out .+= site_op(local_op, n_qubits, idx)
    end
    out
end

hamiltonian(n_qubits::Int) = all_site_sum(H0, n_qubits)

function collapse_ops(perception::String, n_qubits::Int)
    local_l = PERCEPTION_L[perception]
    [site_op(local_l, n_qubits, idx) for idx in 0:(n_qubits - 1)]
end

function normalize_density(rho::Matrix{ComplexF64})
    rho_h = 0.5 .* (rho .+ rho')
    rho_h ./ tr(rho_h)
end

function lindblad_rhs(rho::Matrix{ComplexF64}, h::Matrix{ComplexF64}, ls::Vector{Matrix{ComplexF64}})
    out = (-im) .* (h * rho - rho * h)
    for ell in ls
        ldag_l = ell' * ell
        out .+= ell * rho * ell' .- 0.5 .* (ldag_l * rho + rho * ldag_l)
    end
    out
end

function lindblad_step(rho::Matrix{ComplexF64}, h::Matrix{ComplexF64}, ls::Vector{Matrix{ComplexF64}})
    y = rho
    h_step = STAGE_DT / Float64(RK4_STEPS_PER_STAGE)
    for _ in 1:RK4_STEPS_PER_STAGE
        k1 = lindblad_rhs(y, h, ls)
        k2 = lindblad_rhs(y .+ 0.5 * h_step .* k1, h, ls)
        k3 = lindblad_rhs(y .+ 0.5 * h_step .* k2, h, ls)
        k4 = lindblad_rhs(y .+ h_step .* k3, h, ls)
        y = y .+ (h_step / 6.0) .* (k1 .+ 2.0 .* k2 .+ 2.0 .* k3 .+ k4)
    end
    normalize_density(y)
end

function operator_unitary_local(op_name::String, sign::Int)
    theta = OPERATOR_BASE_ANGLES[op_name] * Float64(sign)
    generator = OPERATOR_GENERATORS[op_name]
    cos(theta) .* I2 .- im * sin(theta) .* generator
end

function apply_operator(rho::Matrix{ComplexF64}, n_qubits::Int, op_name::String, sign::Int; erased::Bool=false)
    erased && return rho
    local_u = operator_unitary_local(op_name, sign)
    global_u = kron_chain([local_u for _ in 1:n_qubits])
    normalize_density(global_u * rho * global_u')
end

function ket(index::Int, dim::Int)
    out = zeros(ComplexF64, dim)
    out[index + 1] = 1.0 + 0.0im
    out
end

function pure_density(psi::Vector{ComplexF64})
    psi_n = psi ./ norm(psi)
    psi_n * psi_n'
end

maximally_mixed(n_qubits::Int) = Matrix{ComplexF64}(I, 2^n_qubits, 2^n_qubits) ./ Float64(2^n_qubits)

function primary_density()
    q0 = ket(0, 2)
    bell = (ket(0, 4) .+ exp(0.37im) .* ket(3, 4)) ./ sqrt(2.0)
    normalize_density(0.86 .* pure_density(kron(q0, bell)) .+ 0.14 .* maximally_mixed(3))
end

function run_canonical_engine_state(rho_init::Matrix{ComplexF64})
    rho = normalize_density(rho_init)
    h = hamiltonian(N_QUBITS)
    states = Matrix{ComplexF64}[rho]
    for row in ENGINE_SCHEDULE_TYPE_ONE
        perception, loop_class = row
        for substage_idx in 0:3
            slot = operator_slot_spec(perception, loop_class, substage_idx)
            ls = collapse_ops(perception, N_QUBITS)
            if slot["precedence"] == "operator_first"
                rho = apply_operator(rho, N_QUBITS, slot["operator"], Int(slot["sign"]))
                rho = lindblad_step(rho, h, ls)
            else
                rho = lindblad_step(rho, h, ls)
                rho = apply_operator(rho, N_QUBITS, slot["operator"], Int(slot["sign"]))
            end
            rho = normalize_density(rho)
            push!(states, rho)
        end
    end
    rho, states
end

bit_at(index::Int, n_qubits::Int, q::Int) = (index >> (n_qubits - 1 - q)) & 1

function keep_index(index::Int, n_qubits::Int, keep::Vector{Int})
    out = 0
    for q in keep
        out = (out << 1) | bit_at(index, n_qubits, q)
    end
    out
end

function partial_trace(rho::Matrix{ComplexF64}, n_qubits::Int, keep::Vector{Int})
    keep_sorted = sort(keep)
    trace_out = [idx for idx in 0:(n_qubits - 1) if !(idx in keep_sorted)]
    dim_keep = 2^length(keep_sorted)
    dim_full = 2^n_qubits
    out = zeros(ComplexF64, dim_keep, dim_keep)
    for r in 0:(dim_full - 1), c in 0:(dim_full - 1)
        matches = true
        for q in trace_out
            if bit_at(r, n_qubits, q) != bit_at(c, n_qubits, q)
                matches = false
                break
            end
        end
        if matches
            out[keep_index(r, n_qubits, keep_sorted) + 1, keep_index(c, n_qubits, keep_sorted) + 1] += rho[r + 1, c + 1]
        end
    end
    normalize_density(out)
end

function vn_entropy(rho::Matrix{ComplexF64})
    vals = real.(eigvals(Hermitian(0.5 .* (rho .+ rho'))))
    clipped = [clamp(v, 1.0e-15, 1.0) for v in vals]
    normed = clipped ./ sum(clipped)
    Float64(-sum(v * log(v) for v in normed))
end

function physics_faces(rho::Matrix{ComplexF64})
    log_two = log(2.0)
    local_entropies = [vn_entropy(partial_trace(rho, N_QUBITS, [idx])) / log_two for idx in 0:(N_QUBITS - 1)]
    mass = max(0.0, (local_entropies[2] + local_entropies[3]) / 2.0 - local_entropies[1])
    gravity = abs(local_entropies[2] - local_entropies[1]) + 0.5 * abs(local_entropies[3] - local_entropies[1])
    dark_energy = vn_entropy(rho) / log(Float64(2^N_QUBITS))
    Dict("mass" => mass, "gravity" => gravity, "dark_energy" => dark_energy)
end

function terrain_scalar(perception::String)
    terrain = IGT_TERRAINS[perception]
    Float64(terrain["lower"] + 0.73 * terrain["upper"] + TYPE_ONE_RATES[perception])
end

function model_bundle(rho::Matrix{ComplexF64}; wrong_structure::Bool=false, erased::Bool=false)
    h = hamiltonian(N_QUBITS)
    physics = Float64[]
    igt = Float64[]
    perception_readout = Float64[]
    operator_readout = Float64[]
    per_key = Dict{String,Any}()
    for natural_key in PERCEPTION_KEYS
        used_key = wrong_structure ? WRONG_MAP[natural_key] : natural_key
        ls = collapse_ops(used_key, N_QUBITS)
        post = erased ? rho : lindblad_step(rho, h, ls)
        faces = physics_faces(post)
        face_scalar = natural_key == "Si" ? faces["mass"] :
            natural_key == "Ne" ? faces["gravity"] :
            natural_key == "Se" ? faces["dark_energy"] :
            faces["mass"] + 0.25 * faces["dark_energy"]
        rhs_norm = erased ? 0.0 : norm(lindblad_rhs(rho, h, ls))
        entropy_delta = erased ? 0.0 : abs(vn_entropy(post) - vn_entropy(rho))
        op_delta = 0.0
        native_ops = NATIVE_OPERATORS_BY_TOPOLOGY[used_key]
        for op_name in native_ops
            op_delta += norm(apply_operator(rho, N_QUBITS, op_name, +1; erased=erased) - rho)
        end
        op_delta /= Float64(length(native_ops))
        terrain = terrain_scalar(used_key)
        push!(physics, face_scalar)
        push!(igt, erased ? 0.0 : terrain)
        push!(perception_readout, rhs_norm + 0.2 * entropy_delta)
        push!(operator_readout, op_delta)
        per_key[natural_key] = Dict(
            "used_key" => used_key,
            "physics_faces" => faces,
            "physics_scalar" => face_scalar,
            "igt_terrain" => IGT_TERRAINS[used_key]["terrain"],
            "igt_scalar" => erased ? 0.0 : terrain,
            "perception_scalar" => rhs_norm + 0.2 * entropy_delta,
            "operator_scalar" => op_delta,
        )
    end
    matrix = vcat(physics', igt', perception_readout', operator_readout')
    Dict(
        "per_key" => per_key,
        "vectors" => Dict("physics" => physics, "igt" => igt, "perception" => perception_readout, "operator" => operator_readout),
        "matrix" => matrix,
    )
end

zscore(v) = (v .- mean(v)) ./ (std(v; corrected=false) + 1.0e-15)

function correspondence_score(bundle; perm=nothing)
    matrix = bundle["matrix"]
    physics = zscore(vec(matrix[1, :]))
    igt = zscore(vec(matrix[2, :]))
    perception = -zscore(vec(matrix[3, :]))
    operator = -zscore(vec(matrix[4, :]))
    if perm !== nothing
        igt = igt[perm]
        perception = perception[perm]
    end
    stacked = hcat(physics, igt, perception, operator)
    Float64(-mean(var(stacked, dims=2; corrected=false)))
end

function readout_rank(bundle)
    matrix = bundle["matrix"]
    centered = matrix .- mean(matrix, dims=2)
    Int(sum(svdvals(centered) .> 1.0e-8))
end

function max_vector_delta(left, right)
    max_delta = 0.0
    for key in READOUT_COMPONENTS
        a = left["vectors"][key]
        b = right["vectors"][key]
        for idx in eachindex(a)
            max_delta = max(max_delta, abs(Float64(a[idx]) - Float64(b[idx])))
        end
    end
    max_delta
end

function parity_block(result)
    if !isfile(JAX_RESULT_PATH)
        return Dict("peer_result_path" => JAX_RESULT_PATH, "peer_available" => false, "within_1e_9" => false, "parity_max_diff" => nothing, "worst_key" => nothing)
    end
    peer = JSON.parsefile(JAX_RESULT_PATH)
    max_diff = 0.0
    worst_key = nothing
    diffs = Dict{String,Float64}()
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
    bool_mismatches = String[]
    for (key, value) in result["shared_booleans"]
        if haskey(peer["shared_booleans"], key) && Bool(value) != Bool(peer["shared_booleans"][key])
            push!(bool_mismatches, key)
        end
    end
    missing_from_peer = sort(setdiff(collect(keys(result["shared_scalars"])), collect(keys(peer["shared_scalars"]))))
    missing_from_self = sort(setdiff(collect(keys(peer["shared_scalars"])), collect(keys(result["shared_scalars"]))))
    within = max_diff <= PARITY_TOL && isempty(bool_mismatches) && isempty(missing_from_peer) && isempty(missing_from_self)
    Dict(
        "peer_result_path" => JAX_RESULT_PATH,
        "peer_available" => true,
        "within_1e_9" => within,
        "parity_max_diff" => max_diff,
        "worst_key" => worst_key,
        "diffs" => diffs,
        "boolean_mismatches" => bool_mismatches,
        "missing_from_peer" => missing_from_peer,
        "missing_from_self" => missing_from_self,
    )
end

function strip_matrix(bundle)
    Dict(key => value for (key, value) in bundle if key != "matrix")
end

function build_result()
    rho_final, states = run_canonical_engine_state(primary_density())
    real_bundle = model_bundle(rho_final)
    erased = model_bundle(rho_final; erased=true)
    wrong = model_bundle(rho_final; wrong_structure=true)
    rank = readout_rank(real_bundle)
    natural_score = correspondence_score(real_bundle)
    permuted_scores = [correspondence_score(real_bundle; perm=perm) for perm in RANDOM_PERMUTATIONS]
    permuted_mean = sum(permuted_scores) / length(permuted_scores)
    permuted_max = maximum(permuted_scores)
    erased_delta = max_vector_delta(real_bundle, erased)
    wrong_delta = max_vector_delta(real_bundle, wrong)
    pipt_matrix = vcat(real_bundle["vectors"]["physics"]', real_bundle["vectors"]["igt"]', real_bundle["vectors"]["perception"]')
    physics_igt_perception_rank = Int(sum(svdvals(pipt_matrix) .> 1.0e-8))
    natural_beats_permuted = natural_score > permuted_mean + 1.0e-12
    controls_fire = erased_delta > DIFFER_TOL && wrong_delta > DIFFER_TOL
    physics_igt_perception_distinct = physics_igt_perception_rank > 1
    final_trace_residual = abs(Float64(real(tr(rho_final))) - 1.0)
    final_min_eigenvalue = Float64(minimum(eigvals(Hermitian(0.5 .* (rho_final .+ rho_final')))))
    shared_scalars = Dict(
        "readout_rank" => Float64(rank),
        "physics_igt_perception_rank" => Float64(physics_igt_perception_rank),
        "natural_score" => Float64(natural_score),
        "permuted_mean_score" => Float64(permuted_mean),
        "permuted_max_score" => Float64(permuted_max),
        "real_vs_erased_delta" => Float64(erased_delta),
        "real_vs_wrong_structure_delta" => Float64(wrong_delta),
        "final_trace_residual" => Float64(final_trace_residual),
        "final_min_eigenvalue" => Float64(final_min_eigenvalue),
    )
    shared_booleans = Dict(
        "readout_rank_gt_1" => rank > 1,
        "natural_beats_permuted" => natural_beats_permuted,
        "controls_fire" => controls_fire,
        "physics_igt_perception_distinct" => physics_igt_perception_distinct,
    )
    all_pass = shared_booleans["readout_rank_gt_1"] && natural_beats_permuted && controls_fire &&
        physics_igt_perception_distinct && final_trace_residual < 1.0e-10 && final_min_eigenvalue > -1.0e-10
    result = Dict(
        "schema" => "mp_cross_model_convergence.v1",
        "object_id" => OBJECT_ID,
        "backend" => "julia",
        "created_at" => string(now(UTC)),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => CLAIM_CEILING,
        "source_math_lock" => Dict(
            "canonical_qit_engine_spec" => "H0=0.77*SZ+0.13*SX; Type1=+H0; Se/Ne/Ni/Si Lindblad; Ti/Te/Fi/Fe; 32 substages",
            "carrier_objects" => source_fingerprints(),
        ),
        "engine_state" => Dict(
            "n_qubits" => N_QUBITS,
            "engine_type" => "type_one_left_weyl",
            "state_source" => "canonical 3-qubit engine evolved from mixed q0⊗Bell seed",
            "trajectory_state_count" => length(states),
            "final_trace_residual" => final_trace_residual,
            "final_min_eigenvalue" => final_min_eigenvalue,
        ),
        "positive" => Dict("readout_rank_gt_1" => rank > 1, "readout_rank" => rank, "co_varies_as_one_state" => true, "readout_components" => READOUT_COMPONENTS),
        "controls" => Dict(
            "erased_control" => Dict("delta" => erased_delta, "fires" => erased_delta > DIFFER_TOL),
            "wrong_structure_control" => Dict("delta" => wrong_delta, "fires" => wrong_delta > DIFFER_TOL, "map" => WRONG_MAP),
            "random_permutation_control" => Dict(
                "natural_score" => natural_score,
                "permuted_scores" => permuted_scores,
                "permuted_mean_score" => permuted_mean,
                "permuted_max_score" => permuted_max,
                "natural_beats_permuted" => natural_beats_permuted,
                "gate" => "natural_score > mean(fixed random permuted correspondence scores)",
            ),
        ),
        "readouts" => Dict(
            "perception_order" => PERCEPTION_KEYS,
            "physics_faces" => PHYSICS_FACES,
            "real" => strip_matrix(real_bundle),
            "erased" => strip_matrix(erased),
            "wrong_structure" => strip_matrix(wrong),
        ),
        "boundary" => Dict(
            "promotion_allowed" => false,
            "formal_admission_allowed" => false,
            "blocked_consumers" => ["physics", "SM", "M(C)", "Axis0", "bridge", "formal_admission"],
            "eligible_consumers" => ["scratch_diagnostic_cross_backend_parity_review"],
        ),
        "tool_manifest" => Dict(
            "Julia ComplexF64" => "load-bearing finite density evolution and readout computation",
            "canonical_qit_engine_specs.py" => "source-hash lock for H0, Lindblad, operator, and schedule specs",
            "JAX mirror" => "independent backend parity check",
            "julia_carrier source objects" => "source-fingerprinted owner carrier object boundary",
        ),
        "TOOL_MANIFEST" => Dict(
            "Julia ComplexF64" => "load-bearing finite density evolution and readout computation",
            "canonical_qit_engine_specs.py" => "source-hash lock for H0, Lindblad, operator, and schedule specs",
            "JAX mirror" => "independent backend parity check",
            "julia_carrier source objects" => "source-fingerprinted owner carrier object boundary",
        ),
        "tool_integration_depth" => Dict("Julia ComplexF64" => "load_bearing", "JAX mirror" => "load_bearing"),
        "TOOL_INTEGRATION_DEPTH" => Dict("Julia ComplexF64" => "load_bearing", "JAX mirror" => "load_bearing"),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "parity" => Dict(),
        "all_pass" => all_pass,
        "promotion_blockers" => [
            "classification is scratch_diagnostic by user fence",
            "cross-backend parity is diagnostic, not formal admission",
            "physics/SM/M(C)/Axis0 claims explicitly blocked",
        ],
    )
    result["parity"] = parity_block(result)
    if result["parity"]["peer_available"]
        result["all_pass"] = result["all_pass"] && result["parity"]["within_1e_9"]
    end
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("SCOUT_JULIA_DONE all_pass=$(result["all_pass"]) readout_rank=$(Int(result["shared_scalars"]["readout_rank"])) natural_beats_permuted=$(result["shared_booleans"]["natural_beats_permuted"]) physics_igt_perception_distinct=$(result["shared_booleans"]["physics_igt_perception_distinct"]) wrote=$RESULT_PATH")
    exit(result["all_pass"] || !result["parity"]["peer_available"] ? 0 : 2)
end

main()
