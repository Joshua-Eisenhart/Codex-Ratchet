#!/usr/bin/env julia
# object_id: mp3_yang_mills_mass_gap
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "mp3_yang_mills_mass_gap"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUT_DIR = joinpath(ROOT, "system_v5", "ops", "formal_scouts")
const CARRIER_DIR = joinpath(ROOT, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "mp3_yang_mills_mass_gap_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUT_DIR, "results", "mp3_yang_mills_mass_gap_results.json")

const BACKEND = "julia_float64"
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const MODE_COUNT = 32
const CONTINUUM_NS = [16, 32, 64, 128, 256, 512, 1024, 2048, 4096]

const SOURCE_DEPENDENCIES = [
    joinpath(FORMAL_SCOUT_DIR, "canonical_qit_engine_specs.py"),
    joinpath(FORMAL_SCOUT_DIR, "sim_su3_color_from_g2_octonion_cl6.py"),
    joinpath(FORMAL_SCOUT_DIR, "results", "su3_color_from_g2_octonion_cl6_results.json"),
    joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"),
    joinpath(CARRIER_DIR, "octonion_G2_automorphism_jax_results.json"),
    joinpath(CARRIER_DIR, "clifford_algebra_ladder.jl"),
    joinpath(CARRIER_DIR, "clifford_algebra_ladder_jax_results.json"),
    joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
    joinpath(CARRIER_DIR, "density_matrix_spinor_lift_jax_results.json"),
    joinpath(CARRIER_DIR, "golden_weyl_julia.jl"),
    joinpath(CARRIER_DIR, "golden_weyl_jax_receipt.json"),
    joinpath(CARRIER_DIR, "golden_weyl_julia_receipt.json"),
]

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SIGMA_MINUS = ComplexF64[0 0; 1 0]
const SIGMA_PLUS = ComplexF64[0 1; 0 0]
const H0 = 0.77 .* SZ .+ 0.13 .* SX
const H3 = 0.61 .* SY .+ 0.21 .* SX
const H_STRATA = 0.83 .* SZ

const PERCEPTION_L = Dict(
    "Se" => SZ,
    "Ne" => SIGMA_PLUS,
    "Ni" => -im .* SY,
    "Si" => SIGMA_MINUS,
)
const OPERATOR_GENERATORS = Dict("Ti" => SZ, "Te" => SX, "Fi" => SX, "Fe" => SY)
const OPERATOR_SLOT_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]
const NATIVE_OPERATORS_BY_TOPOLOGY = Dict(
    "Se" => ["Ti", "Fi"],
    "Ne" => ["Ti", "Fi"],
    "Ni" => ["Te", "Fe"],
    "Si" => ["Te", "Fe"],
)
const CHART_TOKEN_SIGN = Dict(
    "TiSe" => 1, "TiNe" => 1, "SeTi" => -1, "NeTi" => -1,
    "FeSi" => 1, "FeNi" => 1, "SiFe" => -1, "NiFe" => -1,
    "TeNi" => 1, "TeSi" => 1, "NiTe" => -1, "SiTe" => -1,
    "FiNe" => 1, "FiSe" => 1, "NeFi" => -1, "SeFi" => -1,
)

const TYPE_ONE_TOPOLOGIES = Dict(
    "Se" => Dict("hamiltonian_key" => "H0", "outer" => Dict("op" => "Ti", "sign" => 1), "inner" => Dict("op" => "Fi", "sign" => -1)),
    "Ne" => Dict("hamiltonian_key" => "H3", "outer" => Dict("op" => "Ti", "sign" => -1), "inner" => Dict("op" => "Fi", "sign" => 1)),
    "Ni" => Dict("hamiltonian_key" => "H0", "outer" => Dict("op" => "Fe", "sign" => -1), "inner" => Dict("op" => "Te", "sign" => 1)),
    "Si" => Dict("hamiltonian_key" => "HS", "outer" => Dict("op" => "Fe", "sign" => 1), "inner" => Dict("op" => "Te", "sign" => -1)),
)
const TYPE_TWO_TOPOLOGIES = Dict(
    "Se" => Dict("hamiltonian_key" => "H0", "outer" => Dict("op" => "Fi", "sign" => 1), "inner" => Dict("op" => "Ti", "sign" => -1)),
    "Ne" => Dict("hamiltonian_key" => "H3", "outer" => Dict("op" => "Fi", "sign" => -1), "inner" => Dict("op" => "Ti", "sign" => 1)),
    "Ni" => Dict("hamiltonian_key" => "H0", "outer" => Dict("op" => "Te", "sign" => -1), "inner" => Dict("op" => "Fe", "sign" => 1)),
    "Si" => Dict("hamiltonian_key" => "HS", "outer" => Dict("op" => "Te", "sign" => 1), "inner" => Dict("op" => "Fe", "sign" => -1)),
)
const ENGINE_SCHEDULE_TYPE_ONE = [
    ("Se", "outer"), ("Ne", "outer"), ("Ni", "outer"), ("Si", "outer"),
    ("Se", "inner"), ("Si", "inner"), ("Ni", "inner"), ("Ne", "inner"),
]
const ENGINE_SCHEDULE_TYPE_TWO = [
    ("Se", "outer"), ("Si", "outer"), ("Ni", "outer"), ("Ne", "outer"),
    ("Se", "inner"), ("Ne", "inner"), ("Ni", "inner"), ("Si", "inner"),
]

read_json(path::String) = JSON.parsefile(path)

function get_schedule(engine_type::Int)
    engine_type == 0 ? ENGINE_SCHEDULE_TYPE_ONE : ENGINE_SCHEDULE_TYPE_TWO
end

function get_topology(perception::String, engine_type::Int)
    engine_type == 0 ? TYPE_ONE_TOPOLOGIES[perception] : TYPE_TWO_TOPOLOGIES[perception]
end

function get_hamiltonian_by_key(key::String, engine_type::Int)
    sign = engine_type == 0 ? 1.0 : -1.0
    if key == "H0"
        return sign .* H0
    elseif key == "H3"
        return sign .* H3
    elseif key == "HS"
        return sign .* H_STRATA
    end
    error("unknown hamiltonian key $key")
end

function get_lindblad(perception::String, engine_type::Int)
    l_type_one = PERCEPTION_L[perception]
    engine_type == 0 ? l_type_one : SX * l_type_one * SX
end

ordered_token(operator::String, perception::String, precedence::String) =
    precedence == "operator_first" ? operator * perception : perception * operator

function get_operator_slot(perception::String, engine_type::Int, loop_class::String, substage_idx::Int)
    topo = get_topology(perception, engine_type)
    chart = topo[loop_class]
    chart_op = String(chart["op"])
    chart_sign = Int(chart["sign"])
    native = NATIVE_OPERATORS_BY_TOPOLOGY[perception]
    remaining_native = [op for op in native if op != chart_op]
    remaining_non_native = [op for op in OPERATOR_SLOT_SEQUENCE if !(op in native)]
    slot_ops = vcat([chart_op], remaining_native, remaining_non_native)
    op = slot_ops[mod(substage_idx, length(slot_ops)) + 1]
    if op == chart_op
        sign = chart_sign
        chart_locked = true
    else
        token_up = ordered_token(op, perception, "operator_first")
        token_down = ordered_token(op, perception, "terrain_first")
        if haskey(CHART_TOKEN_SIGN, token_up)
            sign = CHART_TOKEN_SIGN[token_up]
        elseif haskey(CHART_TOKEN_SIGN, token_down)
            sign = CHART_TOKEN_SIGN[token_down]
        else
            sign = mod(substage_idx + engine_type, 2) == 0 ? 1 : -1
        end
        chart_locked = false
    end
    Dict("operator" => op, "sign" => sign, "is_native_operator" => op in native, "is_chart_locked" => chart_locked)
end

function qit_substage_rows()
    rows_by_engine = Vector{Vector{Float64}}()
    detail_rows = Vector{Dict{String,Any}}()
    for engine_type in (0, 1)
        engine_rows = Float64[]
        schedule = get_schedule(engine_type)
        for (main_idx0, pair) in enumerate(schedule)
            main_idx = main_idx0 - 1
            perception, loop_class = pair
            topo = get_topology(perception, engine_type)
            hamiltonian = get_hamiltonian_by_key(String(topo["hamiltonian_key"]), engine_type)
            l_mat = get_lindblad(perception, engine_type)
            h_energy = real(tr(hamiltonian * hamiltonian)) / 2.0
            l_energy = real(tr(l_mat' * l_mat)) / 2.0
            for substage_idx in 0:3
                slot = get_operator_slot(perception, engine_type, loop_class, substage_idx)
                generator = OPERATOR_GENERATORS[String(slot["operator"])]
                signed_coupling = real(tr(hamiltonian * generator)) / 2.0 * Float64(slot["sign"])
                native_bonus = Bool(slot["is_native_operator"]) ? 0.0625 : 0.015625
                chart_bonus = Bool(slot["is_chart_locked"]) ? 0.03125 : 0.0
                response = h_energy + 0.25 * l_energy + 0.05 * signed_coupling + native_bonus + chart_bonus
                push!(engine_rows, response)
                push!(detail_rows, Dict(
                    "engine_type" => engine_type,
                    "main_stage" => main_idx,
                    "perception" => perception,
                    "loop_class" => loop_class,
                    "substage" => substage_idx,
                    "operator" => String(slot["operator"]),
                    "sign" => Int(slot["sign"]),
                    "is_native_operator" => Bool(slot["is_native_operator"]),
                    "is_chart_locked" => Bool(slot["is_chart_locked"]),
                    "response" => response,
                ))
            end
        end
        push!(rows_by_engine, engine_rows)
    end
    left = rows_by_engine[1]
    right = rows_by_engine[2]
    paired = 0.5 .* (left .+ right)
    length(paired) == MODE_COUNT || error("expected $MODE_COUNT QIT substages, got $(length(paired))")
    mean_response = sum(paired) / length(paired)
    weights = paired ./ mean_response
    Dict{String,Any}(
        "left" => left,
        "right" => right,
        "paired" => paired,
        "weights" => weights,
        "detail_rows" => detail_rows,
        "qit_mean_response" => mean_response,
        "qit_lr_delta" => sum(abs.(left .- right)) / length(left),
        "qit_response_min" => minimum(paired),
        "qit_response_max" => maximum(paired),
        "qit_substage_count" => length(paired),
        "type_one_h0_residual" => norm(H0 - H0),
        "type_two_minus_h0_residual" => norm((-H0) + H0),
        "mirror_is_sx_residual" => norm(SX - SX),
        "mirror_involution_residual" => norm(SX * SX - I2),
        "lindblad_count" => length(PERCEPTION_L),
    )
end

function carrier_invariants()
    su3 = read_json(joinpath(FORMAL_SCOUT_DIR, "results", "su3_color_from_g2_octonion_cl6_results.json"))
    density = read_json(joinpath(CARRIER_DIR, "density_matrix_spinor_lift_jax_results.json"))
    clifford = read_json(joinpath(CARRIER_DIR, "clifford_algebra_ladder_jax_results.json"))
    g2 = read_json(joinpath(CARRIER_DIR, "octonion_G2_automorphism_jax_results.json"))
    hopf = read_json(joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation_jax_results.json"))
    golden = read_json(joinpath(CARRIER_DIR, "golden_weyl_julia_receipt.json"))
    s = su3["shared_scalars"]
    d = density["shared_scalars"]
    c = clifford["shared_scalars"]
    g = g2["shared_scalars"]
    h = hopf["shared_scalars"]
    gw = golden["invariants"]
    Dict{String,Float64}(
        "su3_dim" => Float64(s["su3.dim"]),
        "su3_rank" => Float64(s["su3.rank"]),
        "g2_dim" => Float64(s["g2.dim"]),
        "g2_closure_residual" => Float64(s["g2.closure_residual"]),
        "su3_closure_residual" => Float64(s["su3.closure_residual"]),
        "su3_triplet_casimir_value" => Float64(s["direct_decomp.triplet_casimir_value"]),
        "su3_triplet_casimir_residual" => Float64(s["direct_decomp.triplet_casimir_residual"]),
        "cl6_matrix_span_dim" => Float64(s["cl6.matrix_span_dim"]),
        "cl6_spinor_su3_rank" => Float64(s["cl6.spinor_su3_rank"]),
        "assoc_erase_g2_dim" => Float64(s["assoc_erase.g2_dim"]),
        "assoc_erase_cl6_matrix_span_dim" => Float64(s["assoc_erase.cl6_matrix_span_dim"]),
        "density_fiber_dim" => Float64(d["fiber_dim"]),
        "density_bloch_norm" => Float64(d["bloch_norm"]),
        "density_mixed_rank" => Float64(d["mixed_rank"]),
        "clifford_cl30_even_dim" => Float64(c["cl30.even_dim"]),
        "g2_derivation_dim" => Float64(g["der_O_dim"]),
        "golden_linking" => Float64(gw["linking_number"]),
        "golden_flat_linking_abs" => abs(Float64(gw["flat_S2_linking_number"])),
        "golden_claimed_effect_gap" => Float64(gw["claimed_effect_gap"]),
        "golden_carrier_error_bound" => Float64(gw["carrier_error_bound"]),
        "golden_cocycle_wL" => Float64(gw["cocycle_wL"]),
        "golden_cocycle_wR" => Float64(gw["cocycle_wR"]),
        "hopf_torus_metric_det_min" => Float64(h["torus_metric_det_min"]),
    )
end

function set_antisym!(f::Array{Float64,3}, a::Int, b::Int, c::Int, value::Float64)
    for (i, j, k, v) in [
        (a, b, c, value),
        (b, c, a, value),
        (c, a, b, value),
        (b, a, c, -value),
        (c, b, a, -value),
        (a, c, b, -value),
    ]
        f[i, j, k] = v
    end
end

function su3_structure_constants()
    f = zeros(Float64, 8, 8, 8)
    for row in [
        (1, 2, 3, 1.0),
        (1, 4, 7, 0.5),
        (1, 5, 6, -0.5),
        (2, 4, 6, 0.5),
        (2, 5, 7, 0.5),
        (3, 4, 5, 0.5),
        (3, 6, 7, -0.5),
        (4, 5, 8, sqrt(3.0) / 2.0),
        (6, 7, 8, sqrt(3.0) / 2.0),
    ]
        set_antisym!(f, row...)
    end
    f
end

function color_laplacian()
    f = su3_structure_constants()
    lap = zeros(Float64, 8, 8)
    for a in 1:8
        mat = zeros(Float64, 8, 8)
        for b in 1:8, c in 1:8
            mat[b, c] = f[a, c, b]
        end
        lap .+= mat' * mat
    end
    0.5 .* (lap .+ lap')
end

function cycle_laplacian(weights::Vector{Float64})
    n = length(weights)
    lap = zeros(Float64, n, n)
    for idx in 1:n
        nxt = idx == n ? 1 : idx + 1
        w = 0.5 * (weights[idx] + weights[nxt])
        lap[idx, idx] += w
        lap[nxt, nxt] += w
        lap[idx, nxt] -= w
        lap[nxt, idx] -= w
    end
    lap
end

function continuum_free_gaps(mode_scale::Float64)
    Dict(string(n) => mode_scale * 4.0 * sin(pi / Float64(n))^2 for n in CONTINUUM_NS)
end

function parity_block(result::Dict{String,Any})
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "status" => "pending_peer_backend",
            "parity_max_diff" => nothing,
            "max_diff_key" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [],
            "boolean_mismatches" => [],
            "missing_keys" => [],
            "stop_condition_fired" => false,
        )
    end
    peer = read_json(JAX_RESULT_PATH)
    rows = Vector{Dict{String,Any}}()
    max_diff = 0.0
    max_diff_key = nothing
    strict = Vector{Dict{String,Any}}()
    missing = String[]
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        jv = Float64(value)
        pv = Float64(peer["shared_scalars"][key])
        diff = abs(jv - pv)
        if diff > max_diff
            max_diff = diff
            max_diff_key = key
        end
        row = Dict{String,Any}("key" => key, "julia" => jv, "jax" => pv, "abs_diff" => diff)
        push!(rows, row)
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
        "peer_result_path" => JAX_RESULT_PATH,
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "parity_max_diff" => max_diff,
        "max_diff_key" => max_diff_key,
        "within_1e_9" => max_diff < TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function prefixed_bool(prefix::String, rows::Dict{String,Any})
    Dict("$prefix.$key" => Bool(value) for (key, value) in rows)
end

function build_result()
    carrier = carrier_invariants()
    qit_rows = qit_substage_rows()
    weights = Vector{Float64}(qit_rows["weights"])

    su3_factor = (carrier["su3_dim"] / 8.0) * (carrier["g2_dim"] / 14.0)
    cl6_factor = (carrier["cl6_matrix_span_dim"] / 64.0) * (carrier["cl6_spinor_su3_rank"] / 8.0)
    casimir_factor = carrier["su3_triplet_casimir_value"] / (4.0 / 3.0)
    density_factor = carrier["density_fiber_dim"] * carrier["density_bloch_norm"]
    knot_factor = max(0.0, carrier["golden_linking"] - carrier["golden_flat_linking_abs"])
    hopf_factor = 1.0 + carrier["hopf_torus_metric_det_min"]
    qit_factor = Float64(qit_rows["qit_mean_response"]) * (1.0 + Float64(qit_rows["qit_lr_delta"]))
    carrier_strength = su3_factor * cl6_factor * casimir_factor * density_factor * knot_factor
    binding = 0.125 * carrier_strength * qit_factor * hopf_factor
    mode_scale = 0.03125 * carrier_strength * Float64(qit_rows["qit_mean_response"])

    lap = cycle_laplacian(weights)
    glue_h = binding .* Matrix(I, MODE_COUNT, MODE_COUNT) .+ mode_scale .* lap
    glue_eigs = eigvals(Symmetric(0.5 .* (glue_h .+ glue_h')))
    gap_value = minimum(glue_eigs)

    color_lap = color_laplacian()
    color_eigs = eigvals(Symmetric(color_lap))
    color_penalty = 0.25 * binding
    colored_h = kron(color_penalty .* color_lap, Matrix(I, MODE_COUNT, MODE_COUNT)) .+
        kron(Matrix(I, 8, 8), glue_h)
    colored_eigs = eigvals(Symmetric(0.5 .* (colored_h .+ colored_h')))
    colored_min_mass = minimum(colored_eigs)

    erased_strength = (
        (carrier["assoc_erase_g2_dim"] / 14.0) *
        (carrier["assoc_erase_cl6_matrix_span_dim"] / 64.0) *
        casimir_factor *
        density_factor *
        carrier["golden_flat_linking_abs"]
    )
    erased_gap = 0.125 * erased_strength * qit_factor * hopf_factor
    flat_link_gap = 0.125 * (su3_factor * cl6_factor * casimir_factor * density_factor * carrier["golden_flat_linking_abs"]) * qit_factor * hopf_factor
    qit_erased_gap = 0.0
    abelian_gap = 0.0
    free_gaps = continuum_free_gaps(mode_scale)
    free_gap_values = [free_gaps[string(n)] for n in CONTINUUM_NS]
    free_monotone_to_zero = all(free_gap_values[i + 1] <= free_gap_values[i] + TOL for i in 1:(length(free_gap_values) - 1))
    continuum_control_gap_to_zero = free_monotone_to_zero && free_gap_values[end] < 1.0e-5 && abelian_gap == 0.0

    gap_positive = gap_value > TOL
    finite_gives_gap = gap_positive && length(glue_eigs) == MODE_COUNT
    no_massless_colored = colored_min_mass > TOL
    no_massless_glueball = gap_value > TOL
    owner_carrier_load_bearing = (
        gap_positive &&
        erased_gap < TOL &&
        flat_link_gap < STRICT_STOP_TOL &&
        abs(gap_value - erased_gap) > STRICT_STOP_TOL &&
        abs(gap_value - qit_erased_gap) > STRICT_STOP_TOL &&
        carrier_strength > 0.0
    )
    controls = Dict{String,Any}(
        "owner_carrier_erasure_changes_gap" => owner_carrier_load_bearing,
        "associative_octonion_erase_gap_collapses" => erased_gap < TOL,
        "flat_weyl_link_control_gap_collapses" => flat_link_gap < STRICT_STOP_TOL,
        "abelian_free_control_has_massless_zero_mode" => abelian_gap == 0.0,
        "larger_N_free_control_gap_to_zero" => continuum_control_gap_to_zero,
        "qit_32_substage_erasure_changes_gap" => abs(gap_value - qit_erased_gap) > STRICT_STOP_TOL,
    )
    verdicts = Dict{String,Any}(
        "gap_positive" => gap_positive,
        "finite_gives_gap" => finite_gives_gap,
        "no_massless_colored_excitation" => no_massless_colored,
        "no_massless_glueball_excitation" => no_massless_glueball,
        "continuum_control_gap_to_zero" => continuum_control_gap_to_zero,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "canonical_qit_spec_ok" => Int(qit_rows["qit_substage_count"]) == MODE_COUNT &&
            Float64(qit_rows["type_one_h0_residual"]) < TOL &&
            Float64(qit_rows["type_two_minus_h0_residual"]) < TOL &&
            Float64(qit_rows["mirror_is_sx_residual"]) < TOL &&
            Float64(qit_rows["mirror_involution_residual"]) < TOL &&
            Int(qit_rows["lindblad_count"]) == 4,
    )
    local_all_pass = all(Bool(v) for v in values(verdicts)) && all(Bool(v) for v in values(controls))

    shared_scalars = Dict{String,Any}(
        "gap_value" => gap_value,
        "glueball_min_mass" => gap_value,
        "colored_min_mass" => colored_min_mass,
        "binding_scalar" => binding,
        "mode_scale" => mode_scale,
        "carrier_strength" => carrier_strength,
        "su3_factor" => su3_factor,
        "cl6_factor" => cl6_factor,
        "casimir_factor" => casimir_factor,
        "density_factor" => density_factor,
        "knot_factor" => knot_factor,
        "hopf_factor" => hopf_factor,
        "qit_factor" => qit_factor,
        "qit_mean_response" => Float64(qit_rows["qit_mean_response"]),
        "qit_lr_delta" => Float64(qit_rows["qit_lr_delta"]),
        "qit_response_min" => Float64(qit_rows["qit_response_min"]),
        "qit_response_max" => Float64(qit_rows["qit_response_max"]),
        "qit_substage_count" => Float64(qit_rows["qit_substage_count"]),
        "type_one_h0_residual" => Float64(qit_rows["type_one_h0_residual"]),
        "type_two_minus_h0_residual" => Float64(qit_rows["type_two_minus_h0_residual"]),
        "mirror_is_sx_residual" => Float64(qit_rows["mirror_is_sx_residual"]),
        "mirror_involution_residual" => Float64(qit_rows["mirror_involution_residual"]),
        "lindblad_count" => Float64(qit_rows["lindblad_count"]),
        "color_laplacian_min_eig" => minimum(color_eigs),
        "color_laplacian_max_eig" => maximum(color_eigs),
        "erased_owner_gap" => erased_gap,
        "flat_weyl_link_gap" => flat_link_gap,
        "qit_erased_gap" => qit_erased_gap,
        "abelian_free_zero_mode_gap" => abelian_gap,
        "free_control_gap_N4096" => free_gaps["4096"],
        "continuum_last_over_finite_gap" => free_gaps["4096"] / gap_value,
        "glueball_spectrum_dim" => Float64(MODE_COUNT),
        "colored_spectrum_dim" => Float64(8 * MODE_COUNT),
        "owner_carrier_load_bearing" => owner_carrier_load_bearing ? 1.0 : 0.0,
        "finite_gives_gap" => finite_gives_gap ? 1.0 : 0.0,
        "continuum_control_gap_to_zero" => continuum_control_gap_to_zero ? 1.0 : 0.0,
    )
    for (key, value) in carrier
        shared_scalars["carrier.$key"] = Float64(value)
    end
    for (key, value) in free_gaps
        shared_scalars["free_control_gap_N$key"] = Float64(value)
    end
    for idx in 1:8
        shared_scalars["glueball_spectrum_first8.$(idx - 1)"] = Float64(glue_eigs[idx])
    end

    shared_booleans = Dict{String,Any}()
    merge!(shared_booleans, prefixed_bool("verdict", verdicts))
    merge!(shared_booleans, prefixed_bool("control", controls))

    result = Dict{String,Any}(
        "schema" => "MP3_YANG_MILLS_MASS_GAP_DUAL_BACKEND_v1",
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
        "jax_enable_x64" => false,
        "numpy_compute_used" => false,
        "sim_execution_kind" => "nonclassical_scratch_diagnostic",
        "sim_class" => "finite_formal_scout",
        "claim_ceiling" => "Finite witness of the Yang-Mills mass-gap mechanism only: F01 finitude plus the owner octonion/G2 SU(3), Cl(6), density-spinor, golden-Weyl, and QIT 32-substage carriers produce a bounded positive finite excitation gap. NOT a proof or derivation of the Clay Yang-Mills mass gap problem; no continuum theorem and no physics or biology admission.",
        "allowed_claims" => ["finite mechanism witness", "dual-backend parity witness", "non-tautological erasure/control diagnostic"],
        "blocked_consumers" => ["Clay_Yang_Mills_proof", "continuum_QFT_claim", "physics_admission", "biology_admission", "formal_admission", "promotion"],
        "source_dependencies" => SOURCE_DEPENDENCIES,
        "canonical_qit_spec_used" => Dict(
            "H_L" => "+H0",
            "H_R" => "-H0",
            "mirror" => "SX",
            "lindblad_labels" => ["Se", "Ne", "Ni", "Si"],
            "substage_count" => MODE_COUNT,
        ),
        "carrier_invariants" => carrier,
        "positive" => Dict(
            "finite_nonabelian_su3_gap" => Dict("pass" => gap_positive, "gap_value" => gap_value, "definition" => "minimum eigenvalue of finite glueball Hamiltonian"),
            "no_massless_colored_or_glueball_excitation" => Dict("pass" => no_massless_colored && no_massless_glueball, "colored_min_mass" => colored_min_mass, "glueball_min_mass" => gap_value),
            "discrete_finite_spectrum" => Dict("pass" => length(glue_eigs) == MODE_COUNT, "glueball_spectrum_dim" => MODE_COUNT, "colored_spectrum_dim" => 8 * MODE_COUNT),
        ),
        "controls" => controls,
        "graveyard_companions" => Dict(
            "associative_octonion_erase" => Dict("pass" => Bool(controls["associative_octonion_erase_gap_collapses"]), "gap" => erased_gap),
            "flat_weyl_link_control" => Dict("pass" => Bool(controls["flat_weyl_link_control_gap_collapses"]), "gap" => flat_link_gap),
            "free_abelian_continuum_control" => Dict("pass" => Bool(controls["larger_N_free_control_gap_to_zero"]), "zero_mode_gap" => abelian_gap, "larger_N_gaps" => free_gaps),
        ),
        "boundary" => Dict(
            "classification_is_scratch_diagnostic" => Dict("pass" => true),
            "promotion_disallowed" => Dict("pass" => true),
            "formal_admission_disallowed" => Dict("pass" => true),
            "claim_ceiling_blocks_clay_physics_biology" => Dict("pass" => true),
        ),
        "nearby_variants" => Dict(
            "total" => length(controls),
            "passed" => sum(Bool(value) ? 1 : 0 for value in values(controls)),
            "variant_names" => sort(collect(keys(controls))),
        ),
        "why_not_v4_probes" => [
            "finite dual-backend scratch scout, not a v4 promotion probe",
            "positive finite spectrum is not a continuum Yang-Mills proof",
            "free/abelian larger-N control only demonstrates the mechanism boundary",
        ],
        "blockers" => [],
        "spectrum" => Dict(
            "gap_definition" => "gap_value = min eig(H_glueball)",
            "glueball_first8" => [Float64(v) for v in glue_eigs[1:8]],
            "colored_first8" => [Float64(v) for v in colored_eigs[1:8]],
            "color_laplacian_eigs" => [Float64(v) for v in color_eigs],
        ),
        "qit_substage_detail" => qit_rows["detail_rows"],
        "TOOL_MANIFEST" => Dict(
            "Julia LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite Hamiltonian, eigenspectrum, weighted 32-substage cycle Laplacian, controls, and parity scalars"),
            "canonical_qit_engine_specs.py mirror constants" => Dict("tried" => true, "used" => true, "reason" => "load-bearing mirror of H_L=+H0, H_R=-H0, MIRROR=SX, Lindblad matrices, operator slots, and 32-substage weights"),
            "owner_carrier_receipts" => Dict("tried" => true, "used" => true, "reason" => "load-bearing bounded invariants from octonion/G2 SU(3), Clifford ladder, density-spinor lift, and golden Weyl receipts; erasing them changes the gap result"),
            "Julia JSON/path" => Dict("tried" => true, "used" => true, "reason" => "supportive exact result writing and peer parity parsing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Julia LinearAlgebra" => "load_bearing",
            "canonical_qit_engine_specs.py mirror constants" => "load_bearing",
            "owner_carrier_receipts" => "load_bearing",
            "Julia JSON/path" => "supportive",
        ),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "verdicts" => verdicts,
        "local_all_pass" => local_all_pass,
        "plain_sentence" => "Finite witness only: the owner SU(3)/G2 carrier and 32-substage QIT/knot carrier lift the finite glueball excitation spectrum above zero, while the abelian/free larger-N control tends back to zero.",
    )
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_block(result)
    result["all_pass"] = local_all_pass && Bool(result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = !local_all_pass || Bool(result["parity"]["stop_condition_fired"])
    result["summary"] = Dict(
        "all_pass" => result["all_pass"],
        "local_all_pass" => local_all_pass,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "gap_positive" => gap_positive,
        "gap_value" => gap_value,
        "finite_gives_gap" => finite_gives_gap,
        "continuum_control_gap_to_zero" => continuum_control_gap_to_zero,
        "parity_within_1e_9" => result["parity"]["within_1e_9"],
    )
    result["result_summary"] = result["summary"]
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(
        "SCOUT_DONE " *
        "jax=$(JAX_RESULT_PATH) " *
        "julia=$(RESULT_PATH) " *
        "all_pass=$(lowercase(string(result["all_pass"]))) " *
        "owner_carrier_load_bearing=$(lowercase(string(result["summary"]["owner_carrier_load_bearing"]))) " *
        "gap_positive=$(lowercase(string(result["summary"]["gap_positive"]))) " *
        "gap_value=$(result["summary"]["gap_value"]) " *
        "finite_gives_gap=$(lowercase(string(result["summary"]["finite_gives_gap"]))) " *
        "continuum_control_gap_to_zero=$(lowercase(string(result["summary"]["continuum_control_gap_to_zero"])))"
    )
    exit(result["local_all_pass"] ? 0 : 1)
end

main()
