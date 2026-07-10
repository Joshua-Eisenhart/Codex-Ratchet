#!/usr/bin/env julia

using Dates
using JSON3
using LinearAlgebra
using Pkg
using QuantumToolbox
using Random
using SHA

const HERE = @__DIR__
const REPO_ROOT = normpath(joinpath(HERE, "..", "..", ".."))
const SPEC_PATH = joinpath(HERE, "spec.json")
const RESULT_PATH = joinpath(HERE, "results", "coratchet_basin_depth_multiview_v0_julia_results.json")
const CANONICAL_SOURCE_PATH = joinpath(REPO_ROOT, "system_v5", "ops", "formal_scouts", "canonical_qit_engine_specs.py")
const CARRIER_PROJECT = joinpath(REPO_ROOT, "system_v5", "julia_carrier", "Project.toml")

const EXPECTED_SPEC_SHA256 = "f370aeb1366f30857c89d5ab9c94af54aea6f40fb8db6309776a5c0fa79dacb7"
const EXPECTED_CANONICAL_SOURCE_SHA256 = "0b8df7def1c274cf118995663abd9ec95886197d1dfb01de4519c19ca9351f83"
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const EPS = 1.0e-13
const FIXED_TOL = 1.0e-9
const CONTRACTION_TOL = 1.0e-8
const CONVERGENCE_TOL = 1.0e-8
const MONOTONIC_TOL = 1.0e-9
const COVARIANCE_TOL = 1.0e-9
const TYPE_DIFFERENCE_TOL = 1.0e-6

const I2 = Matrix{ComplexF64}(I, 2, 2)
const I4 = Matrix{ComplexF64}(I, 4, 4)
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SIGMA_MINUS = ComplexF64[0 0; 1 0]
const SIGMA_PLUS = ComplexF64[0 1; 0 0]
const H0 = 0.77 .* SZ .+ 0.13 .* SX
const PAULI_BASIS_TRANSFORMS = Dict("I" => I2, "X" => SX, "Y" => SY, "Z" => SZ)

const TERRAIN_COLLAPSE_TYPE1 = Dict(
    "Se" => SZ,
    "Ne" => SIGMA_PLUS,
    "Ni" => -im .* SY,
    "Si" => SIGMA_MINUS,
)

const TERRAIN_RATES = Dict(
    "Type1_left" => Dict("Se" => 0.18, "Ne" => 0.13, "Ni" => 0.28, "Si" => 0.20),
    "Type2_right" => Dict("Se" => 0.18, "Ne" => 0.15, "Ni" => 0.27, "Si" => 0.21),
)

struct StageDef
    token::String
    terrain::String
    operator::String
    precedence::String
end

const STAGE_DEFS = [
    StageDef("TiSe", "Se", "Ti", "operator_first"),
    StageDef("SeTi", "Se", "Ti", "terrain_first"),
    StageDef("FiSe", "Se", "Fi", "operator_first"),
    StageDef("SeFi", "Se", "Fi", "terrain_first"),
    StageDef("TiNe", "Ne", "Ti", "operator_first"),
    StageDef("NeTi", "Ne", "Ti", "terrain_first"),
    StageDef("FiNe", "Ne", "Fi", "operator_first"),
    StageDef("NeFi", "Ne", "Fi", "terrain_first"),
    StageDef("TeNi", "Ni", "Te", "operator_first"),
    StageDef("NiTe", "Ni", "Te", "terrain_first"),
    StageDef("FeNi", "Ni", "Fe", "operator_first"),
    StageDef("NiFe", "Ni", "Fe", "terrain_first"),
    StageDef("TeSi", "Si", "Te", "operator_first"),
    StageDef("SiTe", "Si", "Te", "terrain_first"),
    StageDef("FeSi", "Si", "Fe", "operator_first"),
    StageDef("SiFe", "Si", "Fe", "terrain_first"),
]

const FUNCTION_CALL_COUNTS = Dict(
    "QuantumToolbox.liouvillian" => 0,
    "QuantumToolbox.steadystate" => 0,
    "LinearAlgebra.exp" => 0,
    "LinearAlgebra.eigen" => 0,
    "LinearAlgebra.svdvals" => 0,
)

struct CycleAnalysis
    spectrum::Vector{ComplexF64}
    fixed_state::Matrix{ComplexF64}
    fixed_residual::Float64
    fixed_multiplicity::Int
    fixed_min_eigenvalue::Float64
    subdominant_modulus::Float64
    contraction_gap::Float64
    horizon_rows::Vector{Dict{String,Any}}
    trace_distance_profile::Vector{Float64}
    max_relative_entropy_increase::Float64
    observed_epsilon_depth::Union{Nothing,Int}
    spectral_predicted_depth::Union{Nothing,Int}
    depth_factor::Union{Nothing,Float64}
end

function count_call!(name::String)
    FUNCTION_CALL_COUNTS[name] = get(FUNCTION_CALL_COUNTS, name, 0) + 1
end

function sha256_file(path::String)::String
    open(path, "r") do io
        bytes2hex(SHA.sha256(io))
    end
end

function utc_now_string()::String
    Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ")
end

clean_float(x::Real) = abs(Float64(x)) < 1.0e-15 ? 0.0 : Float64(x)
complex_json(z::Complex) = Dict("re" => clean_float(real(z)), "im" => clean_float(imag(z)))
complex_matrix_json(a::AbstractMatrix) = [[complex_json(a[i, j]) for j in axes(a, 2)] for i in axes(a, 1)]

function read_and_validate_spec()
    spec_hash = sha256_file(SPEC_PATH)
    spec_hash == EXPECTED_SPEC_SHA256 || error("preregistered spec hash drift: expected $EXPECTED_SPEC_SHA256, got $spec_hash")
    source_hash = sha256_file(CANONICAL_SOURCE_PATH)
    source_hash == EXPECTED_CANONICAL_SOURCE_SHA256 || error(
        "canonical source hash drift: expected $EXPECTED_CANONICAL_SOURCE_SHA256, got $source_hash",
    )

    spec = JSON3.read(read(SPEC_PATH, String))
    String(spec["schema"]) == "codex_ratchet.sim_spec.v1" || error("unexpected spec schema")
    String(spec["sim_id"]) == "coratchet_basin_depth_multiview_v0" || error("unexpected sim_id")
    String(spec["classification"]) == CLASSIFICATION || error("classification ceiling drift")
    Bool(spec["promotion_allowed"]) == PROMOTION_ALLOWED || error("promotion ceiling drift")
    Bool(spec["formal_admission_allowed"]) == FORMAL_ADMISSION_ALLOWED || error("formal-admission ceiling drift")

    expected_slots = [stage.token for stage in STAGE_DEFS]
    registered_slots = String.(collect(spec["ordered_source_slots"]))
    registered_slots == expected_slots || error("ordered_source_slots drift from the preregistered 16-slot cycle")
    spec, spec_hash, source_hash
end

function normalize_density(rho::AbstractMatrix{<:Complex})::Matrix{ComplexF64}
    out = ComplexF64.(0.5 .* (rho .+ rho'))
    trace_value = real(tr(out))
    abs(trace_value) > EPS || error("density trace collapsed")
    out ./= trace_value
    count_call!("LinearAlgebra.eigen")
    decomposition = eigen(Hermitian(out))
    minimum(real.(decomposition.values)) >= -1.0e-9 || error("channel produced a non-positive density matrix")
    values = max.(real.(decomposition.values), 0.0)
    out = decomposition.vectors * Diagonal(values) * decomposition.vectors'
    ComplexF64.(out ./ real(tr(out)))
end

function density_from_bloch(r::AbstractVector{<:Real})::Matrix{ComplexF64}
    0.5 .* (I2 .+ Float64(r[1]) .* SX .+ Float64(r[2]) .* SY .+ Float64(r[3]) .* SZ)
end

function bloch_vector(rho::Matrix{ComplexF64})::Vector{Float64}
    Float64[real(tr(rho * sigma)) for sigma in (SX, SY, SZ)]
end

function bloch_affine_readout(superoperator::Matrix{ComplexF64})
    center_output = normalize_density(reshape(superoperator * vec(0.5 .* I2), 2, 2))
    offset = bloch_vector(center_output)
    columns = Vector{Float64}[]
    for axis in ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0])
        output = normalize_density(reshape(superoperator * vec(density_from_bloch(axis)), 2, 2))
        push!(columns, bloch_vector(output) .- offset)
    end
    linear = hcat(columns...)
    count_call!("LinearAlgebra.svdvals")
    singular_values = Float64.(svdvals(linear))
    Dict{String,Any}(
        "linear_matrix" => [clean_float.(linear[row, :]) for row in axes(linear, 1)],
        "offset" => clean_float.(offset),
        "singular_values" => clean_float.(singular_values),
        "trace_distance_contraction_coefficient" => clean_float(maximum(singular_values)),
    )
end

function initial_density_columns(count::Int)::Matrix{ComplexF64}
    count >= 7 || error("initial_state_count must be at least 7")
    columns = Matrix{ComplexF64}(undef, 4, count)
    seed_vectors = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0], [-1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0], [0.0, -1.0, 0.0],
        [0.0, 0.0, 1.0], [0.0, 0.0, -1.0],
    ]
    for (index, vector) in enumerate(seed_vectors)
        columns[:, index] = vec(density_from_bloch(vector))
    end
    remaining = count - length(seed_vectors)
    for offset in 1:remaining
        u = mod(offset * 0.7548776662466927, 1.0)
        v = mod(offset * 0.5698402909980532, 1.0)
        z = 2.0 * u - 1.0
        phi = 2.0 * pi * v
        radius = (offset / remaining)^(1.0 / 3.0)
        radial = sqrt(max(0.0, 1.0 - z^2))
        bloch = radius .* [radial * cos(phi), radial * sin(phi), z]
        columns[:, length(seed_vectors) + offset] = vec(density_from_bloch(bloch))
    end
    columns
end

function qt_liouvillian_matrix(H::Matrix{ComplexF64}, collapse_ops::Vector{Matrix{ComplexF64}})
    hamiltonian = Qobj(H)
    count_call!("QuantumToolbox.liouvillian")
    generator = isempty(collapse_ops) ?
        QuantumToolbox.liouvillian(hamiltonian) :
        QuantumToolbox.liouvillian(hamiltonian, Qobj.(collapse_ops))
    Matrix{ComplexF64}(generator.data)
end

function qt_terrain_steadystate_receipt(H::Matrix{ComplexF64}, collapse_op::Matrix{ComplexF64})
    count_call!("QuantumToolbox.steadystate")
    state = QuantumToolbox.steadystate(Qobj(H), [Qobj(collapse_op)])
    rho = normalize_density(Matrix{ComplexF64}(state.data))
    generator = qt_liouvillian_matrix(H, [collapse_op])
    Dict{String,Any}(
        "trace" => clean_float(real(tr(rho))),
        "minimum_eigenvalue" => clean_float(minimum(real.(eigvals(Hermitian(rho))))),
        "generator_residual_frobenius" => clean_float(norm(generator * vec(rho))),
    )
end

function finite_lindblad_channel(
    H::Matrix{ComplexF64},
    collapse_op::Matrix{ComplexF64},
    duration::Float64,
)::Matrix{ComplexF64}
    generator = qt_liouvillian_matrix(H, [collapse_op])
    count_call!("LinearAlgebra.exp")
    ComplexF64.(exp(duration .* generator))
end

function unitary_lindblad_channel(H::Matrix{ComplexF64}, duration::Float64)::Matrix{ComplexF64}
    generator = qt_liouvillian_matrix(H, Matrix{ComplexF64}[])
    count_call!("LinearAlgebra.exp")
    ComplexF64.(exp(duration .* generator))
end

function pinching_channel(axis::Matrix{ComplexF64}, strength::Float64)::Matrix{ComplexF64}
    0.0 <= strength <= 1.0 || error("pinching strength outside [0,1]")
    p_plus = 0.5 .* (I2 .+ axis)
    p_minus = 0.5 .* (I2 .- axis)
    (1.0 - strength) .* I4 .+ strength .* (
        kron(conj(p_plus), p_plus) .+ kron(conj(p_minus), p_minus)
    )
end

function rotation_channel(axis::Matrix{ComplexF64}, angle::Float64)::Matrix{ComplexF64}
    unitary = cos(angle / 2.0) .* I2 .- im * sin(angle / 2.0) .* axis
    ComplexF64.(kron(conj(unitary), unitary))
end

function operator_maps(spec, factor::Float64=1.0)
    params = spec["parameter_grid"]
    q_ti = clamp(factor * Float64(params["dephase_strengths"]["Ti"]), 0.0, 1.0)
    q_te = clamp(factor * Float64(params["dephase_strengths"]["Te"]), 0.0, 1.0)
    theta = factor * Float64(params["operator_angles"]["Fi"])
    phi = factor * Float64(params["operator_angles"]["Fe"])
    Dict(
        "Ti" => pinching_channel(SZ, q_ti),
        "Te" => pinching_channel(SX, q_te),
        "Fi" => rotation_channel(SX, theta),
        "Fe" => rotation_channel(SZ, phi),
    )
end

function engine_hamiltonian(engine::String)::Matrix{ComplexF64}
    engine == "Type1_left" && return ComplexF64.(H0)
    engine == "Type2_right" && return ComplexF64.(-H0)
    error("unknown engine type $engine")
end

function engine_collapse(engine::String, terrain::String)::Matrix{ComplexF64}
    base = TERRAIN_COLLAPSE_TYPE1[terrain]
    engine == "Type1_left" && return ComplexF64.(base)
    engine == "Type2_right" && return ComplexF64.(SX * base * SX)
    error("unknown engine type $engine")
end

function compose_cycle(stages::Vector{Matrix{ComplexF64}}, order::Vector{Int}=collect(eachindex(stages)))
    cycle = copy(I4)
    for index in order
        cycle = stages[index] * cycle
    end
    ComplexF64.(cycle)
end

function build_native_cycle(spec, engine::String; factor::Float64=1.0, steady_receipts::Bool=true)
    params = spec["parameter_grid"]
    duration = factor * Float64(params["lindblad_duration"])
    H = engine_hamiltonian(engine)
    terrains = Dict{String,Matrix{ComplexF64}}()
    steady = Dict{String,Any}()
    for terrain in ("Se", "Ne", "Ni", "Si")
        rate = factor * TERRAIN_RATES[engine][terrain]
        collapse = sqrt(rate) .* engine_collapse(engine, terrain)
        terrains[terrain] = finite_lindblad_channel(H, collapse, duration)
        if steady_receipts
            steady[terrain] = qt_terrain_steadystate_receipt(H, collapse)
        end
    end
    operators = operator_maps(spec, factor)
    stages = Matrix{ComplexF64}[]
    for stage in STAGE_DEFS
        terrain = terrains[stage.terrain]
        operator = operators[stage.operator]
        push!(stages, stage.precedence == "operator_first" ? terrain * operator : operator * terrain)
    end
    (
        stages = stages,
        cycle = compose_cycle(stages),
        terrain_steadystate_receipts = steady,
        effective_parameters = Dict(
            "global_multiplier" => factor,
            "lindblad_duration" => duration,
            "terrain_rates" => Dict(key => factor * value for (key, value) in TERRAIN_RATES[engine]),
            "dephase_strengths" => Dict(
                "Ti" => clamp(factor * Float64(params["dephase_strengths"]["Ti"]), 0.0, 1.0),
                "Te" => clamp(factor * Float64(params["dephase_strengths"]["Te"]), 0.0, 1.0),
            ),
            "operator_angles" => Dict(
                "Fi" => factor * Float64(params["operator_angles"]["Fi"]),
                "Fe" => factor * Float64(params["operator_angles"]["Fe"]),
            ),
        ),
    )
end

function channel_physicality(superoperator::Matrix{ComplexF64})
    choi = zeros(ComplexF64, 4, 4)
    for i in 1:2, j in 1:2
        basis = zeros(ComplexF64, 2, 2)
        basis[i, j] = 1.0
        output = reshape(superoperator * vec(basis), 2, 2)
        for a in 1:2, b in 1:2
            choi[(i - 1) * 2 + a, (j - 1) * 2 + b] = output[a, b]
        end
    end
    trace_row = vec(I2)'
    Dict{String,Any}(
        "trace_preservation_residual" => clean_float(norm(trace_row * superoperator - trace_row)),
        "choi_minimum_eigenvalue" => clean_float(minimum(real.(eigvals(Hermitian(0.5 .* (choi .+ choi')))))),
    )
end

function fixed_point_data(cycle::Matrix{ComplexF64})
    count_call!("LinearAlgebra.eigen")
    decomposition = eigen(cycle)
    fixed_index = argmin(abs.(decomposition.values .- 1.0))
    candidate = reshape(decomposition.vectors[:, fixed_index], 2, 2)
    abs(tr(candidate)) > EPS || error("fixed eigenoperator has zero trace")
    rho = normalize_density(candidate ./ tr(candidate))
    values = ComplexF64.(decomposition.values)
    moduli = sort(abs.(values); rev=true)
    subdominant = length(moduli) >= 2 ? Float64(moduli[2]) : 0.0
    (
        spectrum = values,
        fixed_state = rho,
        fixed_residual = Float64(norm(cycle * vec(rho) - vec(rho))),
        fixed_multiplicity = count(abs.(values .- 1.0) .<= FIXED_TOL),
        fixed_min_eigenvalue = Float64(minimum(real.(eigvals(Hermitian(rho))))),
        subdominant_modulus = subdominant,
        contraction_gap = Float64(1.0 - subdominant),
    )
end

function trace_distance(a::Matrix{ComplexF64}, b::Matrix{ComplexF64})::Float64
    count_call!("LinearAlgebra.svdvals")
    Float64(0.5 * sum(svdvals(a .- b)))
end

function log_density(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    decomposition = eigen(Hermitian(rho))
    minimum(real.(decomposition.values)) > 0.0 || error("log_density requires full rank")
    decomposition.vectors * Diagonal(log.(real.(decomposition.values))) * decomposition.vectors'
end

function relative_entropy(rho::Matrix{ComplexF64}, log_sigma::Matrix{ComplexF64})::Float64
    decomposition = eigen(Hermitian(rho))
    values = max.(real.(decomposition.values), 0.0)
    self_term = sum(value > EPS ? value * log(value) : 0.0 for value in values)
    cross_term = real(tr(rho * log_sigma))
    Float64(max(0.0, self_term - cross_term))
end

function bures_distance(rho::Matrix{ComplexF64}, sigma::Matrix{ComplexF64})::Float64
    det_rho = max(0.0, real(det(rho)))
    det_sigma = max(0.0, real(det(sigma)))
    fidelity_squared = clamp(real(tr(rho * sigma)) + 2.0 * sqrt(det_rho * det_sigma), 0.0, 1.0)
    root_fidelity = sqrt(fidelity_squared)
    Float64(sqrt(max(0.0, 2.0 - 2.0 * root_fidelity)))
end

function spectral_depth(subdominant::Float64, epsilon::Float64)
    subdominant <= EPS && return 1
    subdominant >= 1.0 && return nothing
    max(1, ceil(Int, log(epsilon) / log(subdominant)))
end

function trajectory_analysis(
    cycle::Matrix{ComplexF64},
    fixed_state::Matrix{ComplexF64},
    initial_columns::Matrix{ComplexF64},
    horizons::Vector{Int},
)
    maximum_horizon = maximum(horizons)
    state_columns = copy(initial_columns)
    log_fixed = log_density(fixed_state)
    previous_relative = [
        relative_entropy(normalize_density(reshape(state_columns[:, index], 2, 2)), log_fixed)
        for index in axes(state_columns, 2)
    ]
    trace_profile = zeros(Float64, maximum_horizon)
    max_relative_increase = -Inf
    rows = Dict{String,Any}[]
    observed_depth = nothing

    for time in 1:maximum_horizon
        state_columns = cycle * state_columns
        maximum_trace = 0.0
        maximum_relative = 0.0
        maximum_bures = 0.0
        is_horizon = time in horizons
        for index in axes(state_columns, 2)
            rho = normalize_density(reshape(state_columns[:, index], 2, 2))
            state_columns[:, index] = vec(rho)
            distance = trace_distance(rho, fixed_state)
            maximum_trace = max(maximum_trace, distance)
            relative = relative_entropy(rho, log_fixed)
            max_relative_increase = max(max_relative_increase, relative - previous_relative[index])
            previous_relative[index] = relative
            if is_horizon
                maximum_relative = max(maximum_relative, relative)
                maximum_bures = max(maximum_bures, bures_distance(rho, fixed_state))
            end
        end
        trace_profile[time] = maximum_trace
        if observed_depth === nothing && maximum_trace < CONVERGENCE_TOL
            observed_depth = time
        end
        if is_horizon
            push!(rows, Dict(
                "horizon_cycles" => time,
                "maximum_trace_distance" => clean_float(maximum_trace),
                "maximum_relative_entropy_nats" => clean_float(maximum_relative),
                "maximum_bures_distance" => clean_float(maximum_bures),
            ))
        end
    end
    rows, trace_profile, max_relative_increase, observed_depth
end

function analyze_cycle(
    cycle::Matrix{ComplexF64},
    initial_columns::Matrix{ComplexF64},
    horizons::Vector{Int},
)::CycleAnalysis
    fixed = fixed_point_data(cycle)
    rows, profile, max_increase, observed = trajectory_analysis(
        cycle,
        fixed.fixed_state,
        initial_columns,
        horizons,
    )
    predicted = spectral_depth(fixed.subdominant_modulus, CONVERGENCE_TOL)
    factor = if observed === nothing || predicted === nothing
        nothing
    else
        max(observed, predicted) / max(1.0, min(observed, predicted))
    end
    CycleAnalysis(
        fixed.spectrum,
        fixed.fixed_state,
        fixed.fixed_residual,
        fixed.fixed_multiplicity,
        fixed.fixed_min_eigenvalue,
        fixed.subdominant_modulus,
        fixed.contraction_gap,
        rows,
        profile,
        max_increase,
        observed,
        predicted,
        factor,
    )
end

function analysis_tests(analysis::CycleAnalysis)
    final_distance = analysis.horizon_rows[end]["maximum_trace_distance"]
    Dict{String,Bool}(
        "T1_unique_full_rank_fixed_point" => analysis.fixed_multiplicity == 1 && analysis.fixed_min_eigenvalue > 1.0e-9,
        "T2_strict_transverse_contraction" => analysis.subdominant_modulus < 1.0 - CONTRACTION_TOL,
        "T3_global_sampled_convergence" => final_distance < CONVERGENCE_TOL,
        "T4_relative_entropy_pawl" => analysis.max_relative_entropy_increase <= MONOTONIC_TOL,
        "T5_depth_matches_spectral_prediction" => analysis.depth_factor !== nothing && analysis.depth_factor <= 4.0,
    )
end

function analysis_json(analysis::CycleAnalysis)
    Dict{String,Any}(
        "liouville_spectrum" => complex_json.(analysis.spectrum),
        "fixed_state" => complex_matrix_json(analysis.fixed_state),
        "fixed_point_residual" => clean_float(analysis.fixed_residual),
        "fixed_point_multiplicity" => analysis.fixed_multiplicity,
        "fixed_state_minimum_eigenvalue" => clean_float(analysis.fixed_min_eigenvalue),
        "subdominant_eigenvalue_modulus" => clean_float(analysis.subdominant_modulus),
        "contraction_gap" => clean_float(analysis.contraction_gap),
        "sampled_horizon_readouts" => analysis.horizon_rows,
        "maximum_trace_distance_profile_by_cycle" => clean_float.(analysis.trace_distance_profile),
        "maximum_relative_entropy_increase" => clean_float(analysis.max_relative_entropy_increase),
        "observed_epsilon_depth" => analysis.observed_epsilon_depth,
        "spectral_predicted_depth" => analysis.spectral_predicted_depth,
        "observed_to_predicted_depth_factor" => analysis.depth_factor,
        "tests" => analysis_tests(analysis),
    )
end

function stage_receipts(stages::Vector{Matrix{ComplexF64}})
    [
        Dict{String,Any}(
            "slot" => index,
            "token" => definition.token,
            "terrain" => definition.terrain,
            "operator" => definition.operator,
            "axis6_token_precedence" => definition.precedence == "operator_first" ? "up" : "down",
            "axis6_action_side" => "closure-only",
            "operator_closure_type" => definition.operator in ("Ti", "Te") ? "dephasing" : "unitary",
            "terrain_closure_type" => "finite_time_lindblad_cptp",
            "native_formula" => definition.precedence == "operator_first" ?
                "T_$(definition.terrain) o $(definition.operator)" :
                "$(definition.operator) o T_$(definition.terrain)",
            "physicality" => channel_physicality(stages[index]),
        )
        for (index, definition) in enumerate(STAGE_DEFS)
    ]
end

function quick_schedule_metrics(cycle::Matrix{ComplexF64}, nominal_fixed::Matrix{ComplexF64})
    fixed = fixed_point_data(cycle)
    Dict{String,Any}(
        "fixed_point_multiplicity" => fixed.fixed_multiplicity,
        "subdominant_eigenvalue_modulus" => clean_float(fixed.subdominant_modulus),
        "contraction_gap" => clean_float(fixed.contraction_gap),
        "fixed_point_trace_distance_from_native" => clean_float(trace_distance(fixed.fixed_state, nominal_fixed)),
        "cycle_physicality" => channel_physicality(cycle),
    )
end

function schedule_atlas(stages::Vector{Matrix{ComplexF64}}, nominal_fixed::Matrix{ComplexF64}, engine::String)
    controls = Dict{String,Any}[]
    orders = Pair{String,Vector{Int}}[]
    push!(orders, "native" => collect(1:16))
    push!(orders, "reverse" => collect(16:-1:1))
    for shift in 1:15
        push!(orders, "cyclic_shift_$shift" => [mod1(index + shift, 16) for index in 1:16])
    end
    rng = MersenneTwister(engine == "Type1_left" ? 0xC0A7_1001 : 0xC0A7_2002)
    for permutation_index in 1:16
        push!(orders, "seeded_permutation_$permutation_index" => shuffle(rng, collect(1:16)))
    end
    for (name, order) in orders
        cycle = compose_cycle(stages, order)
        push!(controls, Dict(
            "control" => name,
            "slot_order" => order,
            "token_order" => [STAGE_DEFS[index].token for index in order],
            "metrics" => quick_schedule_metrics(cycle, nominal_fixed),
        ))
    end
    Dict(
        "interpretation" => "atlas_only_no_pass_assigned",
        "controls" => controls,
    )
end

function eigen_multiset_error(left::Vector{ComplexF64}, right::Vector{ComplexF64})::Float64
    length(left) == 4 && length(right) == 4 || error("eigen_multiset_error expects four eigenvalues")
    best = Inf
    for a in 1:4, b in 1:4, c in 1:4, d in 1:4
        length(Set((a, b, c, d))) == 4 || continue
        best = min(best, maximum(abs.([left[1] - right[a], left[2] - right[b], left[3] - right[c], left[4] - right[d]])))
    end
    Float64(best)
end

function horizon_metric_error(left::Vector{Dict{String,Any}}, right::Vector{Dict{String,Any}}, key::String)
    maximum(abs(Float64(a[key]) - Float64(b[key])) for (a, b) in zip(left, right))
end

function basis_covariance_controls(
    stages::Vector{Matrix{ComplexF64}},
    nominal::CycleAnalysis,
    initial_columns::Matrix{ComplexF64},
    horizons::Vector{Int},
)
    rows = Dict{String,Any}[]
    for basis_name in ("I", "X", "Y", "Z")
        unitary = PAULI_BASIS_TRANSFORMS[basis_name]
        conjugation = kron(conj(unitary), unitary)
        transformed_stages = [conjugation * stage * conjugation' for stage in stages]
        transformed_cycle = compose_cycle(transformed_stages)
        transformed_initial = conjugation * initial_columns
        transformed = analyze_cycle(transformed_cycle, transformed_initial, horizons)
        expected_fixed = normalize_density(reshape(conjugation * vec(nominal.fixed_state), 2, 2))
        errors = Dict{String,Any}(
            "spectrum_multiset" => clean_float(eigen_multiset_error(nominal.spectrum, transformed.spectrum)),
            "fixed_state_trace_distance" => clean_float(trace_distance(expected_fixed, transformed.fixed_state)),
            "trace_distance_trajectory" => clean_float(maximum(abs.(nominal.trace_distance_profile .- transformed.trace_distance_profile))),
            "relative_entropy_horizons" => clean_float(horizon_metric_error(
                nominal.horizon_rows, transformed.horizon_rows, "maximum_relative_entropy_nats",
            )),
            "bures_horizons" => clean_float(horizon_metric_error(
                nominal.horizon_rows, transformed.horizon_rows, "maximum_bures_distance",
            )),
        )
        passed = maximum(Float64.(collect(values(errors)))) <= COVARIANCE_TOL
        push!(rows, Dict("basis_transform" => basis_name, "errors" => errors, "passed" => passed))
    end
    Dict(
        "transforms" => rows,
        "passed" => all(Bool(row["passed"]) for row in rows),
        "tolerance" => COVARIANCE_TOL,
    )
end

function random_unit_vector(rng::AbstractRNG)::Vector{Float64}
    vector = randn(rng, 3)
    vector ./ norm(vector)
end

function axis_matrix(axis::Vector{Float64})::Matrix{ComplexF64}
    ComplexF64.(axis[1] .* SX .+ axis[2] .* SY .+ axis[3] .* SZ)
end

function random_su2(rng::AbstractRNG)::Matrix{ComplexF64}
    axis = axis_matrix(random_unit_vector(rng))
    angle = 2.0 * pi * rand(rng)
    ComplexF64.(cos(angle / 2.0) .* I2 .- im * sin(angle / 2.0) .* axis)
end

function random_matched_cycle(spec, engine::String, rng::AbstractRNG)
    params = spec["parameter_grid"]
    duration = Float64(params["lindblad_duration"])
    base_hamiltonian = engine_hamiltonian(engine)
    terrains = Dict{String,Matrix{ComplexF64}}()
    for terrain in ("Se", "Ne", "Ni", "Si")
        h_unitary = random_su2(rng)
        l_unitary = random_su2(rng)
        random_hamiltonian = h_unitary * base_hamiltonian * h_unitary'
        canonical_collapse = sqrt(TERRAIN_RATES[engine][terrain]) .* engine_collapse(engine, terrain)
        random_collapse = l_unitary * canonical_collapse * l_unitary'
        terrains[terrain] = finite_lindblad_channel(random_hamiltonian, random_collapse, duration)
    end
    operators = Dict(
        "Ti" => pinching_channel(axis_matrix(random_unit_vector(rng)), Float64(params["dephase_strengths"]["Ti"])),
        "Te" => pinching_channel(axis_matrix(random_unit_vector(rng)), Float64(params["dephase_strengths"]["Te"])),
        "Fi" => rotation_channel(axis_matrix(random_unit_vector(rng)), Float64(params["operator_angles"]["Fi"])),
        "Fe" => rotation_channel(axis_matrix(random_unit_vector(rng)), Float64(params["operator_angles"]["Fe"])),
    )
    stages = [
        definition.precedence == "operator_first" ?
            terrains[definition.terrain] * operators[definition.operator] :
            operators[definition.operator] * terrains[definition.terrain]
        for definition in STAGE_DEFS
    ]
    compose_cycle(stages)
end

function nearest_rank_percentile(values::Vector{Float64}, percentile::Float64)::Float64
    ordered = sort(values)
    ordered[clamp(ceil(Int, percentile * length(ordered)), 1, length(ordered))]
end

function genericity_controls(spec, engine::String, native_gap::Float64, count::Int)
    rng = MersenneTwister(engine == "Type1_left" ? 0xB451_1001 : 0xB451_2002)
    gaps = Float64[]
    for _ in 1:count
        fixed = fixed_point_data(random_matched_cycle(spec, engine, rng))
        push!(gaps, fixed.contraction_gap)
    end
    percentile_95 = nearest_rank_percentile(gaps, 0.95)
    Dict{String,Any}(
        "control_family" => "matched_random_primitive_cptp_cycles",
        "matching_rule" => "same 16 precedence slots, terrain durations/rates, Hamiltonian norm, collapse-operator norms, operator families, dephase strengths, and rotation angles; axes are independently Haar-style SU(2) rotated",
        "count" => count,
        "contraction_gaps" => clean_float.(gaps),
        "percentile_95" => clean_float(percentile_95),
        "native_contraction_gap" => clean_float(native_gap),
        "passed" => native_gap > percentile_95,
    )
end

function erased_dissipation_control(spec, engine::String)
    duration = Float64(spec["parameter_grid"]["lindblad_duration"])
    terrain = unitary_lindblad_channel(engine_hamiltonian(engine), duration)
    operators = operator_maps(spec)
    stages = Matrix{ComplexF64}[]
    for definition in STAGE_DEFS
        operator = definition.operator in ("Ti", "Te") ? I4 : operators[definition.operator]
        push!(stages, definition.precedence == "operator_first" ? terrain * operator : operator * terrain)
    end
    cycle = compose_cycle(stages)
    count_call!("LinearAlgebra.eigen")
    values = ComplexF64.(eigen(cycle).values)
    fixed_multiplicity = count(abs.(values .- 1.0) .<= FIXED_TOL)
    moduli = sort(abs.(values); rev=true)
    subdominant_modulus = length(moduli) >= 2 ? Float64(moduli[2]) : 0.0
    passed = subdominant_modulus >= 1.0 - CONTRACTION_TOL || fixed_multiplicity != 1
    Dict{String,Any}(
        "erasure_rule" => "remove all Lindblad collapse operators and replace Ti/Te dissipative pinching maps by identity; retain only Hamiltonian, Fi, and Fe unitary channels",
        "fixed_point_multiplicity" => fixed_multiplicity,
        "subdominant_eigenvalue_modulus" => clean_float(subdominant_modulus),
        "strict_attraction_destroyed" => passed,
        "passed" => passed,
    )
end

function commuting_fixed_manifold_control(spec, engine::String)
    params = spec["parameter_grid"]
    duration = Float64(params["lindblad_duration"])
    terrains = Dict{String,Matrix{ComplexF64}}()
    for terrain in ("Se", "Ne", "Ni", "Si")
        collapse = sqrt(TERRAIN_RATES[engine][terrain]) .* SZ
        terrains[terrain] = finite_lindblad_channel(zeros(ComplexF64, 2, 2), collapse, duration)
    end
    shared_operator = pinching_channel(
        SZ,
        max(Float64(params["dephase_strengths"]["Ti"]), Float64(params["dephase_strengths"]["Te"])),
    )
    stages = [
        definition.precedence == "operator_first" ?
            terrains[definition.terrain] * shared_operator :
            shared_operator * terrains[definition.terrain]
        for definition in STAGE_DEFS
    ]
    fixed = fixed_point_data(compose_cycle(stages))
    passed = fixed.fixed_multiplicity >= 2
    Dict{String,Any}(
        "control_rule" => "all terrain and operator maps are z-axis dephasing channels with zero Hamiltonian",
        "fixed_point_multiplicity" => fixed.fixed_multiplicity,
        "subdominant_eigenvalue_modulus" => clean_float(fixed.subdominant_modulus),
        "nonunique_fixed_manifold_retained" => passed,
        "passed" => passed,
    )
end

function parameter_robustness(
    spec,
    engine::String,
    nominal::CycleAnalysis,
    initial_columns::Matrix{ComplexF64},
    horizons::Vector{Int},
)
    rows = Dict{String,Any}[]
    multipliers = Float64.(collect(spec["parameter_grid"]["perturbation_multipliers"]))
    for multiplier in multipliers
        if multiplier == 1.0
            analysis = nominal
            effective = build_native_cycle(spec, engine; factor=1.0, steady_receipts=false).effective_parameters
        else
            build = build_native_cycle(spec, engine; factor=multiplier, steady_receipts=false)
            analysis = analyze_cycle(build.cycle, initial_columns, horizons)
            effective = build.effective_parameters
        end
        tests = analysis_tests(analysis)
        t1_t4 = all(tests[key] for key in (
            "T1_unique_full_rank_fixed_point",
            "T2_strict_transverse_contraction",
            "T3_global_sampled_convergence",
            "T4_relative_entropy_pawl",
        ))
        drift = trace_distance(analysis.fixed_state, nominal.fixed_state)
        push!(rows, Dict(
            "multiplier" => multiplier,
            "effective_parameters" => effective,
            "T1_T4_passed" => t1_t4,
            "fixed_point_trace_distance_from_nominal" => clean_float(drift),
            "fixed_point_drift_below_0_2" => drift < 0.2,
            "analysis" => analysis_json(analysis),
        ))
    end
    passed = all(Bool(row["T1_T4_passed"]) && Bool(row["fixed_point_drift_below_0_2"]) for row in rows)
    Dict(
        "multiplier_rule" => "the registered global multiplier scales Lindblad duration, terrain rates, dephase strengths, and coherent operator angles; H0 matrix entries remain source-locked",
        "rows" => rows,
        "passed" => passed,
    )
end

function type_difference(type1::CycleAnalysis, type2::CycleAnalysis)
    fixed_distance = trace_distance(type1.fixed_state, type2.fixed_state)
    profile_difference = maximum(abs.(type1.trace_distance_profile .- type2.trace_distance_profile))
    passed = fixed_distance > TYPE_DIFFERENCE_TOL || profile_difference > TYPE_DIFFERENCE_TOL
    Dict{String,Any}(
        "fixed_point_trace_distance" => clean_float(fixed_distance),
        "maximum_depth_profile_difference" => clean_float(profile_difference),
        "threshold" => TYPE_DIFFERENCE_TOL,
        "passed" => passed,
    )
end

function package_receipts()
    dependencies = Pkg.dependencies()
    packages = Dict{String,Any}()
    for package_name in ("QuantumToolbox", "JSON3")
        matching = [info for info in values(dependencies) if info.name == package_name]
        packages[package_name] = isempty(matching) ? nothing : string(first(matching).version)
    end
    Dict{String,Any}(
        "julia_version" => string(VERSION),
        "active_project" => Base.active_project(),
        "expected_project" => CARRIER_PROJECT,
        "active_project_matches_expected" => normpath(something(Base.active_project(), "")) == normpath(CARRIER_PROJECT),
        "package_versions" => packages,
        "function_receipts" => [
            Dict(
                "function" => name,
                "call_count" => count,
                "role" => name == "QuantumToolbox.liouvillian" ?
                    "load_bearing construction of finite-time terrain Lindblad generators" :
                    name == "QuantumToolbox.steadystate" ?
                    "load_bearing independent steady-state receipt for each nominal terrain generator" :
                    "load_bearing finite-dimensional channel analysis",
            )
            for (name, count) in sort(collect(FUNCTION_CALL_COUNTS); by=first)
        ],
    )
end

function tool_manifest()
    Dict{String,Any}(
        "QuantumToolbox" => Dict(
            "tried" => true,
            "used" => true,
            "reason" => "load-bearing liouvillian construction and terrain steadystate receipts",
        ),
        "LinearAlgebra" => Dict(
            "tried" => true,
            "used" => true,
            "reason" => "load-bearing exponentials, spectra, fixed points, singular values, density distances, and matrix functions",
        ),
        "JSON3" => Dict(
            "tried" => true,
            "used" => true,
            "reason" => "supportive independent preregistered spec parsing and result serialization",
        ),
        "SHA" => Dict(
            "tried" => true,
            "used" => true,
            "reason" => "supportive fail-closed preregistration and committed-semantics provenance hashes",
        ),
    )
end

function tool_integration_depth()
    Dict(
        "QuantumToolbox" => "load_bearing",
        "LinearAlgebra" => "load_bearing",
        "JSON3" => "supportive",
        "SHA" => "supportive",
    )
end

function strict_verdict(engine_tests::Dict{String,Any}, type_control::Dict{String,Any})
    nominal_t1_t4 = all(
        all(Bool(engine_tests[engine]["nominal_tests"]["T$index"]) for index in 1:4)
        for engine in keys(engine_tests)
    )
    nominal_t1_t7 = all(
        all(Bool(engine_tests[engine]["nominal_tests"]["T$index"]) for index in 1:7)
        for engine in keys(engine_tests)
    )
    t9_all = all(Bool(engine_tests[engine]["nominal_tests"]["T9"]) for engine in keys(engine_tests))
    controls_all = all(
        Bool(engine_tests[engine]["nominal_tests"]["T10"]) && Bool(engine_tests[engine]["nominal_tests"]["T11"])
        for engine in keys(engine_tests)
    )
    t12 = Bool(type_control["passed"])
    if !nominal_t1_t4
        "NO_REAL_ATTRACTOR_BASIN_IN_THIS_MAP"
    elseif nominal_t1_t7 && t9_all && controls_all && t12
        "REAL_DISTINCTIVE_INSTALLED_BASINS"
    elseif nominal_t1_t7 && !t9_all && controls_all && t12
        "REAL_BUT_GENERIC_INSTALLED_BASINS"
    else
        "LOCAL_OR_FRAGILE_INSTALLED_BASIN_ONLY"
    end
end

function main()
    spec, spec_hash, source_hash = read_and_validate_spec()
    params = spec["parameter_grid"]
    horizons = Int.(collect(params["horizons"]))
    initial_count = Int(params["initial_state_count"])
    random_control_count = Int(params["random_control_count"])
    initial_columns = initial_density_columns(initial_count)

    engine_results = Dict{String,Any}()
    engine_analyses = Dict{String,CycleAnalysis}()
    engine_tests = Dict{String,Any}()

    for engine in String.(collect(params["engine_types"]))
        build = build_native_cycle(spec, engine; steady_receipts=true)
        nominal = analyze_cycle(build.cycle, initial_columns, horizons)
        engine_analyses[engine] = nominal
        tests = analysis_tests(nominal)
        robustness = parameter_robustness(spec, engine, nominal, initial_columns, horizons)
        covariance = basis_covariance_controls(build.stages, nominal, initial_columns, horizons)
        schedules = schedule_atlas(build.stages, nominal.fixed_state, engine)
        genericity = genericity_controls(spec, engine, nominal.contraction_gap, random_control_count)
        erased = erased_dissipation_control(spec, engine)
        commuting = commuting_fixed_manifold_control(spec, engine)

        nominal_tests = Dict{String,Bool}(
            "T1" => tests["T1_unique_full_rank_fixed_point"],
            "T2" => tests["T2_strict_transverse_contraction"],
            "T3" => tests["T3_global_sampled_convergence"],
            "T4" => tests["T4_relative_entropy_pawl"],
            "T5" => tests["T5_depth_matches_spectral_prediction"],
            "T6" => Bool(robustness["passed"]),
            "T7" => Bool(covariance["passed"]),
            "T9" => Bool(genericity["passed"]),
            "T10" => Bool(erased["passed"]),
            "T11" => Bool(commuting["passed"]),
        )
        engine_tests[engine] = Dict("nominal_tests" => nominal_tests)
        engine_results[engine] = Dict{String,Any}(
            "semantic_definition" => Dict(
                "hamiltonian" => engine == "Type1_left" ? "+H0" : "-H0",
                "H0" => complex_matrix_json(H0),
                "collapse_mirror_rule" => engine == "Type1_left" ? "L_type1" : "SX * L_type1 * SX",
                "terrain_rates" => TERRAIN_RATES[engine],
                "axis6_rule" => "composition_precedence_only",
            ),
            "effective_parameters" => build.effective_parameters,
            "terrain_steadystate_receipts" => build.terrain_steadystate_receipts,
            "stage_receipts" => stage_receipts(build.stages),
            "cycle_physicality" => channel_physicality(build.cycle),
            "bloch_ball_affine_readout" => bloch_affine_readout(build.cycle),
            "nominal_analysis" => analysis_json(nominal),
            "parameter_robustness" => robustness,
            "basis_covariance" => covariance,
            "schedule_sensitivity_atlas" => schedules,
            "genericity_kill_control" => genericity,
            "unitary_no_attraction_control" => erased,
            "commuting_fixed_manifold_control" => commuting,
            "nominal_tests" => nominal_tests,
        )
    end

    type_control = type_difference(engine_analyses["Type1_left"], engine_analyses["Type2_right"])
    for engine in keys(engine_tests)
        engine_tests[engine]["nominal_tests"]["T12"] = Bool(type_control["passed"])
    end
    verdict = strict_verdict(engine_tests, type_control)
    manifest = tool_manifest()
    integration_depth = tool_integration_depth()

    result = Dict{String,Any}(
        "schema" => "codex_ratchet.sim_result.v1",
        "sim_id" => String(spec["sim_id"]),
        "engine" => "julia",
        "semantic_role" => "julia_canon_arbitration",
        "result_path" => relpath(RESULT_PATH, REPO_ROOT),
        "reads_peer_result" => false,
        "generated_at" => utc_now_string(),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => String(spec["claim_ceiling"]),
        "blocked_consumers" => String.(collect(spec["blocked_consumers"])),
        "verdict" => verdict,
        "verdict_scope" => "installed finite CPTP cycles only; no derivation, canonicity, Axis0, perception, object, ontology, mesh, business, or physics promotion",
        "input_provenance" => Dict(
            "spec_path" => relpath(SPEC_PATH, REPO_ROOT),
            "canonical_semantics_ref" => "HEAD:system_v5/ops/formal_scouts/canonical_qit_engine_specs.py",
            "canonical_source_path" => relpath(CANONICAL_SOURCE_PATH, REPO_ROOT),
            "peer_result_files_read" => String[],
            "independent_spec_read" => true,
        ),
        "hashes" => Dict(
            "spec_sha256" => spec_hash,
            "canonical_semantics_sha256" => source_hash,
            "run_julia_sha256" => sha256_file(abspath(@__FILE__)),
        ),
        "carrier" => Dict(
            "state_space" => "2x2 density matrices on the closed Bloch ball",
            "vectorization" => "Julia column-major vec",
            "full_cycle" => "16 registered stage maps applied left-to-right in ordered_source_slots order",
            "initial_state_sampling" => "origin, six Pauli poles, then deterministic low-discrepancy interior Bloch-ball points",
            "initial_state_count" => initial_count,
        ),
        "ordered_source_slots" => [stage.token for stage in STAGE_DEFS],
        "engine_results" => engine_results,
        "type_difference_control" => type_control,
        "test_summary" => Dict(
            "T1_T7_T9_T12" => Dict(engine => engine_tests[engine]["nominal_tests"] for engine in keys(engine_tests)),
            "T8_schedule_sensitivity" => "reported_as_atlas_no_pass_assigned",
        ),
        "TOOL_MANIFEST" => manifest,
        "TOOL_INTEGRATION_DEPTH" => integration_depth,
        "tool_manifest" => manifest,
        "tool_integration_depth" => integration_depth,
        "divergence_log" => [
            "No JAX, PyTorch, controller, or peer result artifact is read; this file is an independent Julia semantic arbitration lane.",
            "QuantumToolbox parity is diagnostic rather than formal proof; the result remains scratch_diagnostic regardless of verdict.",
        ],
        "environment" => package_receipts(),
    )

    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON3.pretty(io, result)
        write(io, "\n")
    end
    println(JSON3.write(Dict(
        "sim_id" => String(spec["sim_id"]),
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "verdict" => verdict,
        "result_path" => RESULT_PATH,
    )))
end

main()
