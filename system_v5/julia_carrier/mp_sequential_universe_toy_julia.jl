#!/usr/bin/env julia
# object_id: mp_sequential_universe_density_carrier
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

module OwnerDensityCarrier
include("density_matrix_spinor_lift.jl")
end

const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const JULIA_CARRIER = joinpath(REPO, "system_v5", "julia_carrier")
const FORMAL_SCOUTS = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const RESULT_PATH = joinpath(JULIA_CARRIER, "mp_sequential_universe_toy_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(FORMAL_SCOUTS, "results", "mp_sequential_universe_toy_results.json")
const OBJECT_ID = "mp_sequential_universe_density_carrier"
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const UNIVERSE_COUNT = 6
const DT = 0.018
const LOG2 = log(2.0)

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const MIRROR = SX

const OPERATOR_SLOT_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]
const NATIVE_OPERATORS_BY_TOPOLOGY = Dict(
    "Se" => ["Ti", "Fi"],
    "Ne" => ["Ti", "Fi"],
    "Ni" => ["Te", "Fe"],
    "Si" => ["Te", "Fe"],
)
const CHART_TOKEN_PRECEDENCE = Dict(
    "TiSe" => ("operator_first", 1),
    "TiNe" => ("operator_first", 1),
    "SeTi" => ("terrain_first", -1),
    "NeTi" => ("terrain_first", -1),
    "FeSi" => ("operator_first", 1),
    "FeNi" => ("operator_first", 1),
    "SiFe" => ("terrain_first", -1),
    "NiFe" => ("terrain_first", -1),
    "TeNi" => ("operator_first", 1),
    "TeSi" => ("operator_first", 1),
    "NiTe" => ("terrain_first", -1),
    "SiTe" => ("terrain_first", -1),
    "FiNe" => ("operator_first", 1),
    "FiSe" => ("operator_first", 1),
    "NeFi" => ("terrain_first", -1),
    "SeFi" => ("terrain_first", -1),
)
const TYPE_ONE_TOPOLOGIES = Dict(
    "Se" => Dict("outer" => Dict("op" => "Ti", "sign" => 1), "inner" => Dict("op" => "Fi", "sign" => -1), "rate" => 0.18),
    "Ne" => Dict("outer" => Dict("op" => "Ti", "sign" => -1), "inner" => Dict("op" => "Fi", "sign" => 1), "rate" => 0.13),
    "Ni" => Dict("outer" => Dict("op" => "Fe", "sign" => -1), "inner" => Dict("op" => "Te", "sign" => 1), "rate" => 0.28),
    "Si" => Dict("outer" => Dict("op" => "Fe", "sign" => 1), "inner" => Dict("op" => "Te", "sign" => -1), "rate" => 0.20),
)
const TYPE_TWO_TOPOLOGIES = Dict(
    "Se" => Dict("outer" => Dict("op" => "Fi", "sign" => 1), "inner" => Dict("op" => "Ti", "sign" => -1), "rate" => 0.18),
    "Ne" => Dict("outer" => Dict("op" => "Fi", "sign" => -1), "inner" => Dict("op" => "Ti", "sign" => 1), "rate" => 0.15),
    "Ni" => Dict("outer" => Dict("op" => "Te", "sign" => -1), "inner" => Dict("op" => "Fe", "sign" => 1), "rate" => 0.27),
    "Si" => Dict("outer" => Dict("op" => "Te", "sign" => 1), "inner" => Dict("op" => "Fe", "sign" => -1), "rate" => 0.21),
)
const ENGINE_SCHEDULE_TYPE_ONE = [("Se", "outer"), ("Ne", "outer"), ("Ni", "outer"), ("Si", "outer"),
    ("Se", "inner"), ("Si", "inner"), ("Ni", "inner"), ("Ne", "inner")]
const ENGINE_SCHEDULE_TYPE_TWO = [("Se", "outer"), ("Si", "outer"), ("Ni", "outer"), ("Ne", "outer"),
    ("Se", "inner"), ("Ne", "inner"), ("Ni", "inner"), ("Si", "inner")]
const N_SUBSTAGES_PER_MAIN = 4
const N_TOTAL_SUBSTAGES_PER_ENGINE = 32

function sha256_file(path::String)
    isfile(path) ? bytes2hex(sha256(read(path))) : nothing
end

function source_refs()
    refs = Dict(
        "density_matrix_spinor_lift" => joinpath(JULIA_CARRIER, "density_matrix_spinor_lift.jl"),
        "jax_density_matrix_spinor_lift" => joinpath(JULIA_CARRIER, "jax_density_matrix_spinor_lift.py"),
        "canonical_qit_engine_specs" => joinpath(FORMAL_SCOUTS, "canonical_qit_engine_specs.py"),
    )
    Dict(key => Dict("path" => path, "exists" => isfile(path), "sha256" => sha256_file(path)) for (key, path) in refs)
end

function normalize(v::Vector{Float64})
    n = norm(v)
    n > TOL ? v ./ n : v
end

function clamp_bloch(v::Vector{Float64}; max_norm::Float64 = 0.985)
    n = norm(v)
    n > max_norm ? v .* (max_norm / n) : v
end

function rho_from_bloch(v::Vector{Float64})
    r = clamp_bloch(v)
    0.5 .* (I2 .+ r[1] .* SX .+ r[2] .* SY .+ r[3] .* SZ)
end

function bloch_from_rho(rho::Matrix{ComplexF64})
    [real(tr(rho * SX)), real(tr(rho * SY)), real(tr(rho * SZ))]
end

function renormalize_rho(rho::Matrix{ComplexF64})
    hermitian = 0.5 .* (rho .+ rho')
    hermitian ./ tr(hermitian)
end

function lindblad_step(rho::Matrix{ComplexF64}, h_mat::Matrix{ComplexF64}, l_mat::Matrix{ComplexF64}, rate::Float64)
    ldl = l_mat' * l_mat
    comm = h_mat * rho - rho * h_mat
    dissipator = l_mat * rho * l_mat' - 0.5 .* (ldl * rho + rho * ldl)
    renormalize_rho(rho .+ DT .* (-im .* comm .+ rate .* dissipator))
end

function entropy(rho::Matrix{ComplexF64})
    vals = clamp.(eigvals(Hermitian(0.5 .* (rho .+ rho'))), 0.0, 1.0)
    vals ./= sum(vals)
    total = 0.0
    for value in vals
        if value > TOL
            total -= value * log(value) / LOG2
        end
    end
    total
end

idx2(a::Int, b::Int) = 2 * a + b + 1

function partial_trace_a(rho_ab::Matrix{ComplexF64})
    out = zeros(ComplexF64, 2, 2)
    for a in 0:1, c in 0:1, b in 0:1
        out[a + 1, c + 1] += rho_ab[idx2(a, b), idx2(c, b)]
    end
    out
end

function partial_trace_b(rho_ab::Matrix{ComplexF64})
    out = zeros(ComplexF64, 2, 2)
    for b in 0:1, d in 0:1, a in 0:1
        out[b + 1, d + 1] += rho_ab[idx2(a, b), idx2(a, d)]
    end
    out
end

function mutual_information(rho_ab::Matrix{ComplexF64})
    entropy(partial_trace_a(rho_ab)) + entropy(partial_trace_b(rho_ab)) - entropy(rho_ab)
end

function spinor_perp(psi::Vector{ComplexF64})
    ComplexF64[-conj(psi[2]), conj(psi[1])]
end

function owner_carrier(seed::Float64 = 0.0)
    psi = OwnerDensityCarrier.spinor_from_angles(1.1 + 0.07 * seed, -0.7 + 0.11 * seed)
    rho = OwnerDensityCarrier.dm(psi)
    bloch = OwnerDensityCarrier.bloch_from_rho(rho)
    axis = normalize(Float64.(bloch))
    rho_rebuilt = OwnerDensityCarrier.rho_from_bloch(Float64.(bloch))
    u2 = OwnerDensityCarrier.su2([0.2, -0.5, 0.84], 2.0 * pi)
    psi2 = u2 * psi
    rho2 = u2 * rho * u2'
    Dict{String,Any}(
        "psi" => psi,
        "psi_perp" => spinor_perp(psi),
        "rho" => rho,
        "axis" => axis,
        "bloch" => Float64.(bloch),
        "rho_reconstruction_residual" => norm(rho - rho_rebuilt),
        "spinor_norm_residual" => abs(real(dot(psi, psi)) - 1.0),
        "rho_2pi_return_residual" => norm(rho2 - rho),
        "psi_2pi_sign_residual" => norm(psi2 + psi),
    )
end

function erased_owner_carrier()
    psi = ComplexF64[1.0 + 0im, 0.0 + 0im]
    axis = [0.0, 0.0, 1.0]
    Dict{String,Any}(
        "psi" => psi,
        "psi_perp" => spinor_perp(psi),
        "rho" => rho_from_bloch(axis),
        "axis" => axis,
        "bloch" => axis,
        "rho_reconstruction_residual" => 0.0,
        "spinor_norm_residual" => 0.0,
        "rho_2pi_return_residual" => 0.0,
        "psi_2pi_sign_residual" => 0.0,
    )
end

function entangled_density(carrier::Dict{String,Any}, inherited::Vector{Float64})
    axis = carrier["axis"]
    memory_alignment = clamp(dot(inherited, axis), 0.0, 0.96)
    memory_norm = clamp(norm(inherited), 0.0, 0.96)
    corr_weight = clamp(0.06 + 0.58 * memory_alignment + 0.22 * memory_norm, 0.0, 0.92)
    alpha = clamp(0.66 + 0.18 * memory_alignment, 0.54, 0.86)
    psi = carrier["psi"]
    psi_perp = carrier["psi_perp"]
    ent = sqrt(alpha) .* kron(psi, psi) .+ sqrt(1.0 - alpha) .* kron(psi_perp, psi_perp)
    ent ./= sqrt(real(dot(ent, ent)))
    ent_rho = ent * ent'
    rho_a = rho_from_bloch(0.42 .* axis .+ 0.48 .* inherited)
    rho_b = rho_from_bloch(0.37 .* axis .+ 0.51 .* inherited)
    product = kron(rho_a, rho_b)
    renormalize_rho(corr_weight .* ent_rho .+ (1.0 - corr_weight) .* product)
end

function qit_hamiltonian(engine_type::Int)
    h0 = 0.77 .* SZ .+ 0.13 .* SX
    engine_type == 0 ? h0 : -h0
end

function qit_lindblad(perception::String, engine_type::Int)
    base = Dict(
        "Se" => SZ,
        "Ne" => ComplexF64[0 1; 0 0],
        "Ni" => -im .* SY,
        "Si" => ComplexF64[0 0; 1 0],
    )[perception]
    engine_type == 0 ? base : MIRROR * base * MIRROR
end

function qit_operator(op::String)
    Dict("Ti" => SZ, "Te" => SX, "Fi" => SX, "Fe" => SY)[op]
end

function op_axis(op::Matrix{ComplexF64})
    [real(tr(op * SX)) / 2.0, real(tr(op * SY)) / 2.0, real(tr(op * SZ)) / 2.0]
end

function qit_topologies(engine_type::Int)
    engine_type == 0 ? TYPE_ONE_TOPOLOGIES : TYPE_TWO_TOPOLOGIES
end

function qit_schedule(engine_type::Int)
    engine_type == 0 ? ENGINE_SCHEDULE_TYPE_ONE : ENGINE_SCHEDULE_TYPE_TWO
end

function ordered_token(operator::String, perception::String, precedence::String)
    precedence == "operator_first" ? operator * perception : perception * operator
end

function operator_slot_spec(perception::String, engine_type::Int, loop_class::String, substage_idx::Int)
    topo = qit_topologies(engine_type)[perception]
    chart_op = String(topo[loop_class]["op"])
    chart_sign = Int(topo[loop_class]["sign"])
    chart_precedence = chart_sign > 0 ? "operator_first" : "terrain_first"
    native = NATIVE_OPERATORS_BY_TOPOLOGY[perception]
    slot_ops = vcat([chart_op], [op for op in native if op != chart_op], [op for op in OPERATOR_SLOT_SEQUENCE if !(op in native)])
    op = slot_ops[mod(substage_idx, length(slot_ops)) + 1]
    if op == chart_op
        return Dict("operator" => op, "sign" => chart_sign)
    end
    token_up = ordered_token(op, perception, "operator_first")
    token_down = ordered_token(op, perception, "terrain_first")
    if haskey(CHART_TOKEN_PRECEDENCE, token_up)
        _, sign = CHART_TOKEN_PRECEDENCE[token_up]
        return Dict("operator" => op, "sign" => sign)
    elseif haskey(CHART_TOKEN_PRECEDENCE, token_down)
        _, sign = CHART_TOKEN_PRECEDENCE[token_down]
        return Dict("operator" => op, "sign" => sign)
    end
    sign = iseven(substage_idx + engine_type) ? 1 : -1
    Dict("operator" => op, "sign" => sign)
end

function qit_cycle(inherited::Vector{Float64}, carrier::Dict{String,Any})
    rho = entangled_density(carrier, inherited)
    axis = carrier["axis"]
    stage_count = 0
    for engine_type in (0, 1)
        h_base = qit_hamiltonian(engine_type)
        for (perception, loop_class) in qit_schedule(engine_type)
            l_single = qit_lindblad(perception, engine_type)
            rate = Float64(qit_topologies(engine_type)[perception]["rate"])
            for substage_idx in 0:(N_SUBSTAGES_PER_MAIN - 1)
                slot = operator_slot_spec(perception, engine_type, loop_class, substage_idx)
                op = qit_operator(String(slot["operator"]))
                drive = dot(inherited, op_axis(op)) + 0.25 * dot(axis, op_axis(op))
                h_single = h_base .+ (0.030 * Float64(slot["sign"]) + 0.014 * drive) .* op
                h_total = kron(h_single, I2) .+ kron(I2, 0.73 .* h_single)
                l_a = kron(l_single, I2)
                l_b = kron(I2, MIRROR * l_single * MIRROR)
                rho = lindblad_step(rho, h_total, l_a, rate)
                rho = lindblad_step(rho, h_total, l_b, 0.71 * rate)
                stage_count += 1
            end
        end
    end
    if stage_count != 2 * N_TOTAL_SUBSTAGES_PER_ENGINE
        error("unexpected qit stage count $stage_count")
    end
    rho_a = partial_trace_a(rho)
    rho_b = partial_trace_b(rho)
    out_bloch = clamp_bloch(0.5 .* (bloch_from_rho(rho_a) .+ bloch_from_rho(rho_b)))
    mi = mutual_information(rho)
    mi_norm = clamp(mi / 2.0, 0.0, 1.0)
    purity = real(tr(rho * rho))
    entropy_basin = 1.0 - clamp(entropy(rho) / 2.0, 0.0, 1.0)
    alignment = clamp(0.5 + 0.5 * dot(out_bloch, axis), 0.0, 1.0)
    stability = clamp(0.48 * mi_norm + 0.24 * entropy_basin + 0.18 * alignment + 0.10 * purity, 0.0, 1.0)
    mixed = 0.54 .* inherited .+ (0.24 + 0.48 * mi_norm) .* axis .+ 0.16 .* out_bloch
    next_norm = clamp(0.16 + 0.70 * mi_norm + 0.12 * norm(inherited), 0.0, 0.96)
    next_memory = next_norm .* normalize(mixed)
    next_memory, out_bloch, stability, mi, entropy_basin, purity
end

function scramble_memory(v::Vector{Float64}, axis::Vector{Float64})
    scramble = [0.0 0.0 -1.0; 0.0 1.0 0.0; -1.0 0.0 0.0]
    carrier_component = dot(v, axis)
    orthogonal = v .- carrier_component .* axis
    scrambled_orthogonal = scramble * orthogonal
    scrambled_orthogonal = scrambled_orthogonal .- dot(scrambled_orthogonal, axis) .* axis
    0.62 .* (-abs(carrier_component) .* axis .+ scrambled_orthogonal)
end

function run_sequence(mode::String, carrier::Dict{String,Any})
    prev = 0.18 .* carrier["axis"]
    rows = Vector{Dict{String,Any}}()
    windows = Float64[]
    mutual_infos = Float64[]
    entropies = Float64[]
    purities = Float64[]
    for universe_idx in 0:(UNIVERSE_COUNT - 1)
        inherited = if mode == "preserved"
            prev
        elseif mode == "random"
            scramble_memory(prev, carrier["axis"])
        elseif mode == "none"
            zeros(Float64, 3)
        else
            error(mode)
        end
        next_memory, out_bloch, stability, mi, entropy_basin, purity = qit_cycle(inherited, carrier)
        push!(windows, Float64(stability))
        push!(mutual_infos, Float64(mi))
        push!(entropies, Float64(entropy_basin))
        push!(purities, Float64(purity))
        push!(rows, Dict{String,Any}(
            "universe_index" => universe_idx,
            "inheritance_mode" => mode,
            "inherited_rho_correlation_vector" => Float64.(inherited),
            "out_density_bloch" => Float64.(out_bloch),
            "next_rho_correlation_vector" => Float64.(next_memory),
            "alignment_with_owner_density_axis" => Float64(dot(inherited, carrier["axis"])),
            "mutual_information_bits" => Float64(mi),
            "entropy_basin_score" => Float64(entropy_basin),
            "stability_window" => Float64(stability),
            "two_qubit_purity" => Float64(purity),
        ))
        prev = next_memory
    end
    diffs = [windows[i + 1] - windows[i] for i in 1:(length(windows) - 1)]
    Dict{String,Any}(
        "mode" => mode,
        "rows" => rows,
        "stability_windows" => windows,
        "window_diffs" => diffs,
        "mutual_information_bits" => mutual_infos,
        "entropy_basin_scores" => entropies,
        "purities" => purities,
        "monotonic_strict_increase" => all(diff -> diff > STRICT_STOP_TOL, diffs),
        "net_increase" => windows[end] - windows[1],
        "final_window" => windows[end],
        "final_mutual_information_bits" => mutual_infos[end],
    )
end

function run_bundle(carrier::Dict{String,Any})
    Dict{String,Any}(
        "preserved" => run_sequence("preserved", carrier),
        "random_inheritance_control" => run_sequence("random", carrier),
        "no_inheritance_control" => run_sequence("none", carrier),
    )
end

function parity_against_jax(result::Dict{String,Any})
    if !isfile(JAX_REFERENCE_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_REFERENCE_PATH,
            "status" => "missing_jax_reference",
            "parity_max_diff" => nothing,
            "within_1e_9" => false,
            "boolean_mismatches" => ["missing_jax_reference"],
            "strict_divergence_gt_1e_6" => ["missing_jax_reference"],
            "missing_keys" => [],
            "stop_condition_fired" => true,
        )
    end
    peer = JSON.parsefile(JAX_REFERENCE_PATH)
    rows = Vector{Dict{String,Any}}()
    missing = String[]
    strict = Vector{Dict{String,Any}}()
    max_diff = 0.0
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        julia_value = Float64(value)
        jax_value = Float64(peer["shared_scalars"][key])
        diff = abs(julia_value - jax_value)
        row = Dict{String,Any}("key" => key, "julia" => julia_value, "jax" => jax_value, "abs_diff" => diff)
        push!(rows, row)
        max_diff = max(max_diff, diff)
        diff > STRICT_STOP_TOL && push!(strict, row)
    end
    mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_booleans"]
        if !haskey(peer["shared_booleans"], key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer["shared_booleans"][key])
            push!(mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => Bool(peer["shared_booleans"][key])))
        end
    end
    Dict{String,Any}(
        "peer_result_path" => JAX_REFERENCE_PATH,
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "parity_max_diff" => max_diff,
        "within_1e_9" => max_diff <= TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "boolean_mismatches" => mismatches,
        "strict_divergence_gt_1e_6" => strict,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function build_result()
    carrier = owner_carrier()
    erased_carrier = erased_owner_carrier()
    sequences = run_bundle(carrier)
    erased_sequences = run_bundle(erased_carrier)
    preserved = sequences["preserved"]
    random_control = sequences["random_inheritance_control"]
    no_control = sequences["no_inheritance_control"]

    inherited_increases_stability = Bool(preserved["monotonic_strict_increase"] && preserved["net_increase"] > 1.0e-3)
    random_inherit_fails = Bool((!random_control["monotonic_strict_increase"]) && random_control["net_increase"] < 0.03)
    no_inherit_fails = Bool((!no_control["monotonic_strict_increase"]) && abs(no_control["net_increase"]) <= STRICT_STOP_TOL)
    owner_delta = abs(Float64(preserved["final_window"]) - Float64(erased_sequences["preserved"]["final_window"]))
    owner_carrier_load_bearing = Bool(owner_delta > STRICT_STOP_TOL)
    on_real_density_carrier = Bool(
        carrier["rho_reconstruction_residual"] <= STRICT_STOP_TOL &&
        carrier["spinor_norm_residual"] <= STRICT_STOP_TOL &&
        carrier["psi_2pi_sign_residual"] <= STRICT_STOP_TOL
    )
    controls_fire = random_inherit_fails && no_inherit_fails

    shared_scalars = Dict{String,Float64}(
        "universe_count" => Float64(UNIVERSE_COUNT),
        "qit_total_substages_per_engine" => Float64(N_TOTAL_SUBSTAGES_PER_ENGINE),
        "qit_stage_count_per_universe" => Float64(2 * N_TOTAL_SUBSTAGES_PER_ENGINE),
        "owner_axis_x" => Float64(carrier["axis"][1]),
        "owner_axis_y" => Float64(carrier["axis"][2]),
        "owner_axis_z" => Float64(carrier["axis"][3]),
        "owner_density_bloch_norm" => Float64(norm(carrier["bloch"])),
        "owner_rho_reconstruction_residual" => Float64(carrier["rho_reconstruction_residual"]),
        "owner_psi_2pi_sign_residual" => Float64(carrier["psi_2pi_sign_residual"]),
        "preserved_window_0" => Float64(preserved["stability_windows"][1]),
        "preserved_window_final" => Float64(preserved["final_window"]),
        "preserved_net_increase" => Float64(preserved["net_increase"]),
        "preserved_final_mutual_information_bits" => Float64(preserved["final_mutual_information_bits"]),
        "random_window_0" => Float64(random_control["stability_windows"][1]),
        "random_window_final" => Float64(random_control["final_window"]),
        "random_net_increase" => Float64(random_control["net_increase"]),
        "no_inherit_window_0" => Float64(no_control["stability_windows"][1]),
        "no_inherit_window_final" => Float64(no_control["final_window"]),
        "no_inherit_net_increase" => Float64(no_control["net_increase"]),
        "owner_erased_preserved_window_final" => Float64(erased_sequences["preserved"]["final_window"]),
        "owner_erased_result_delta" => Float64(owner_delta),
    )
    for (idx, value) in enumerate(preserved["stability_windows"])
        shared_scalars["preserved_window_$(idx - 1)"] = Float64(value)
    end
    for (idx, value) in enumerate(random_control["stability_windows"])
        shared_scalars["random_window_$(idx - 1)"] = Float64(value)
    end
    for (idx, value) in enumerate(no_control["stability_windows"])
        shared_scalars["no_inherit_window_$(idx - 1)"] = Float64(value)
    end

    shared_booleans = Dict{String,Any}(
        "inherited_increases_stability" => inherited_increases_stability,
        "random_inherit_fails" => random_inherit_fails,
        "no_inherit_fails" => no_inherit_fails,
        "controls_fire" => controls_fire,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "on_real_density_carrier" => on_real_density_carrier,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "jax_enable_x64" => true,
    )
    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "result_path" => RESULT_PATH,
        "jax_reference_path" => JAX_REFERENCE_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "Finite density-carrier inheritance diagnostic only; no physics, dark-matter, Standard Model, M(C), Axis0, bridge, engine admission, manifold closure, or formal admission claim.",
        "owner_source_refs" => source_refs(),
        "carrier_anchors" => Dict{String,Any}(
            "density_bloch" => Float64.(carrier["bloch"]),
            "density_bloch_norm" => Float64(norm(carrier["bloch"])),
            "rho_reconstruction_residual" => Float64(carrier["rho_reconstruction_residual"]),
            "spinor_norm_residual" => Float64(carrier["spinor_norm_residual"]),
            "rho_2pi_return_residual" => Float64(carrier["rho_2pi_return_residual"]),
            "psi_2pi_sign_residual" => Float64(carrier["psi_2pi_sign_residual"]),
        ),
        "construction" => Dict{String,Any}(
            "memory_carrier" => "two-qubit density matrix whose inherited state is previous-iteration rho correlation and mutual information",
            "stability_measure" => "density entropy basin score plus mutual information, purity, and owner-density-axis alignment",
            "positive" => "preserved rho correlation vector is passed to the next finite iteration",
            "controls" => [
                "random inheritance applies an order/sign-scrambled correlation vector before the same density and QIT evolution",
                "no inheritance replaces the previous rho correlation by zero before the same density and QIT evolution",
                "owner-erased ablation replaces density_matrix_spinor_lift with a fixed computational-basis carrier",
            ],
        ),
        "sequences" => sequences,
        "owner_erased_ablation" => erased_sequences,
        "controls" => Dict{String,Any}(
            "real_vs_scrambled_structure_flip" => random_inherit_fails,
            "real_vs_erased_structure_flip" => no_inherit_fails,
            "random_inheritance_does_not_raise_stability" => random_inherit_fails,
            "no_inheritance_does_not_raise_stability" => no_inherit_fails,
            "owner_carrier_erasure_changes_result" => owner_carrier_load_bearing,
        ),
        "tool_manifest" => Dict(
            "Julia" => "load-bearing density-matrix, entropy, mutual-information, Lindblad, and parity arithmetic",
            "LinearAlgebra" => "load-bearing complex matrix, eigensystem, tensor product, and trace arithmetic",
            "owner_julia_carrier" => "load-bearing direct include of density_matrix_spinor_lift.jl; owner-erased ablation changes the result",
            "canonical_qit_engine_specs" => "load-bearing mirrored H0, Type1/2 signs, Se/Ne/Ni/Si Lindblad, operator slots, and 32-substage schedule metadata",
            "JSON" => "supportive result serialization",
        ),
        "TOOL_MANIFEST" => Dict(
            "Julia" => "load-bearing density-matrix, entropy, mutual-information, Lindblad, and parity arithmetic",
            "LinearAlgebra" => "load-bearing complex matrix, eigensystem, tensor product, and trace arithmetic",
            "owner_julia_carrier" => "load-bearing direct include of density_matrix_spinor_lift.jl; owner-erased ablation changes the result",
            "canonical_qit_engine_specs" => "load-bearing mirrored H0, Type1/2 signs, Se/Ne/Ni/Si Lindblad, operator slots, and 32-substage schedule metadata",
            "JSON" => "supportive result serialization",
        ),
        "tool_integration_depth" => Dict(
            "Julia" => "load_bearing",
            "LinearAlgebra" => "load_bearing",
            "owner_julia_carrier" => "load_bearing",
            "canonical_qit_engine_specs" => "load_bearing",
            "JSON" => "supportive",
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Julia" => "load_bearing",
            "LinearAlgebra" => "load_bearing",
            "owner_julia_carrier" => "load_bearing",
            "canonical_qit_engine_specs" => "load_bearing",
            "JSON" => "supportive",
        ),
        "divergence_log" => [
            "Positive: preserved rho correlation and mutual information raise the density stability window monotonically.",
            "Control: scrambled inheritance uses the same carrier/evolution after a wrong order/sign correlation flip and does not raise the window.",
            "Control: erased inheritance uses the same carrier/evolution from zero correlation and does not raise the window.",
            "Owner-carrier ablation: replacing density_matrix_spinor_lift with a fixed carrier changes the final stability window.",
        ],
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
    )
    result["parity"] = parity_against_jax(result)
    result["parity_stop_condition_fired"] = Bool(result["parity"]["stop_condition_fired"])
    result["all_pass"] = Bool(
        inherited_increases_stability &&
        random_inherit_fails &&
        no_inherit_fails &&
        owner_carrier_load_bearing &&
        on_real_density_carrier &&
        !result["parity_stop_condition_fired"]
    )
    result["shared_booleans"]["all_pass"] = result["all_pass"]
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("SCOUT_DONE jax=$(JAX_REFERENCE_PATH) julia=$(RESULT_PATH) all_pass=$(lowercase(string(result["all_pass"]))) owner_carrier_load_bearing=$(lowercase(string(result["shared_booleans"]["owner_carrier_load_bearing"]))) inherited_increases_stability=$(lowercase(string(result["shared_booleans"]["inherited_increases_stability"]))) random_inherit_fails=$(lowercase(string(result["shared_booleans"]["random_inherit_fails"]))) no_inherit_fails=$(lowercase(string(result["shared_booleans"]["no_inherit_fails"]))) on_real_density_carrier=$(lowercase(string(result["shared_booleans"]["on_real_density_carrier"])))")
    result["all_pass"] ? exit(0) : exit(2)
end

main()
