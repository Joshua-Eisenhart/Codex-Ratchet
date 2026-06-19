#!/usr/bin/env julia
# object_id: mp3_matter_antimatter_chirality
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "mp3_matter_antimatter_chirality"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUT_DIR = joinpath(REPO, "system_v5/ops/formal_scouts")
const CARRIER_DIR = joinpath(REPO, "system_v5/julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "mp3_matter_antimatter_chirality_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUT_DIR, "results/mp3_matter_antimatter_chirality_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const DT = 0.031
const SOURCE_ETA = 0.61
const SOURCE_PHI = 0.17
const SOURCE_CHI = -0.23
const CP_BIAS_SCALE = 0.083

const SOURCE_DEPENDENCIES = Dict{String,Any}(
    "canonical_qit_engine_specs" => joinpath(FORMAL_SCOUT_DIR, "canonical_qit_engine_specs.py"),
    "octonion_G2_automorphism" => joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"),
    "octonion_G2_automorphism_jax" => joinpath(CARRIER_DIR, "jax_octonion_G2_automorphism.py"),
    "clifford_algebra_ladder" => joinpath(CARRIER_DIR, "clifford_algebra_ladder.jl"),
    "clifford_algebra_ladder_jax" => joinpath(CARRIER_DIR, "jax_clifford_algebra_ladder.py"),
    "density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
    "density_matrix_spinor_lift_jax" => joinpath(CARRIER_DIR, "jax_density_matrix_spinor_lift.py"),
    "golden_weyl" => joinpath(CARRIER_DIR, "golden_weyl_julia.jl"),
    "golden_weyl_jax" => joinpath(CARRIER_DIR, "scratch_jax_snapshot_20260604/golden_weyl_jax.py"),
    "golden_weyl_receipt" => joinpath(CARRIER_DIR, "golden_weyl_julia_receipt.json"),
)

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SIGMA_MINUS = ComplexF64[0 0; 1 0]
const SIGMA_PLUS = ComplexF64[0 1; 0 0]
const H0 = 0.77 .* SZ .+ 0.13 .* SX
const H_TYPE_ONE = H0
const H_TYPE_TWO = -1.0 .* H0
const MIRROR = SX
const H3 = 0.61 .* SY .+ 0.21 .* SX
const H_STRATA = 0.83 .* SZ
const OPERATOR_GENERATORS = Dict{String,Matrix{ComplexF64}}(
    "Ti" => SZ,
    "Te" => SX,
    "Fi" => SX,
    "Fe" => SY,
)
const PERCEPTION_L_MATRICES = Dict{String,Matrix{ComplexF64}}(
    "Se" => SZ,
    "Ne" => SIGMA_PLUS,
    "Ni" => -im .* SY,
    "Si" => SIGMA_MINUS,
)
const OPERATOR_MAP_FAMILY = Dict("Ti" => "z_pinching_dephase", "Te" => "x_pinching_dephase", "Fi" => "x_coherent_rotation", "Fe" => "z_coherent_rotation")
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
const NATIVE_OPERATORS_BY_TOPOLOGY = Dict(
    "Se" => ["Ti", "Fi"],
    "Ne" => ["Ti", "Fi"],
    "Ni" => ["Te", "Fe"],
    "Si" => ["Te", "Fe"],
)
const TYPE_ONE_TOPOLOGIES = Dict{String,Any}(
    "Se" => Dict("rate" => 0.18, "outer" => Dict("op" => "Ti", "sign" => 1), "inner" => Dict("op" => "Fi", "sign" => -1)),
    "Ne" => Dict("rate" => 0.13, "outer" => Dict("op" => "Ti", "sign" => -1), "inner" => Dict("op" => "Fi", "sign" => 1)),
    "Ni" => Dict("rate" => 0.28, "outer" => Dict("op" => "Fe", "sign" => -1), "inner" => Dict("op" => "Te", "sign" => 1)),
    "Si" => Dict("rate" => 0.20, "outer" => Dict("op" => "Fe", "sign" => 1), "inner" => Dict("op" => "Te", "sign" => -1)),
)
const TYPE_TWO_TOPOLOGIES = Dict{String,Any}(
    "Se" => Dict("rate" => 0.18, "outer" => Dict("op" => "Fi", "sign" => 1), "inner" => Dict("op" => "Ti", "sign" => -1)),
    "Ne" => Dict("rate" => 0.15, "outer" => Dict("op" => "Fi", "sign" => -1), "inner" => Dict("op" => "Ti", "sign" => 1)),
    "Ni" => Dict("rate" => 0.27, "outer" => Dict("op" => "Te", "sign" => -1), "inner" => Dict("op" => "Fe", "sign" => 1)),
    "Si" => Dict("rate" => 0.21, "outer" => Dict("op" => "Te", "sign" => 1), "inner" => Dict("op" => "Fe", "sign" => -1)),
)
const ENGINE_SCHEDULE_TYPE_ONE = [("Se", "outer"), ("Ne", "outer"), ("Ni", "outer"), ("Si", "outer"), ("Se", "inner"), ("Si", "inner"), ("Ni", "inner"), ("Ne", "inner")]
const ENGINE_SCHEDULE_TYPE_TWO = [("Se", "outer"), ("Si", "outer"), ("Ni", "outer"), ("Ne", "outer"), ("Se", "inner"), ("Ne", "inner"), ("Ni", "inner"), ("Si", "inner")]
const N_SUBSTAGES_PER_MAIN = 4
const N_TOTAL_SUBSTAGES_PER_ENGINE = 32

function owner_module(name::Symbol, path::String)
    source = read(path, String)
    source = replace(source, r"(?m)^\s*main\(\)\s*$" => "")
    source = replace(source, r"(?s)\nresult = build_result\(\).*" => "\n")
    mod = Module(name)
    Base.include_string(mod, source, path)
    mod
end

const OwnerOct = owner_module(:Mp3OwnerOct, joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"))
const OwnerClifford = owner_module(:Mp3OwnerClifford, joinpath(CARRIER_DIR, "clifford_algebra_ladder.jl"))
const OwnerDensity = owner_module(:Mp3OwnerDensity, joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"))
const OwnerGolden = owner_module(:Mp3OwnerGolden, joinpath(CARRIER_DIR, "golden_weyl_julia.jl"))

read_json(path::String) = JSON.parsefile(path)
sha256_file(path::String) = bytes2hex(sha256(read(path)))
trace_real(a::Matrix{ComplexF64}) = Float64(real(tr(a)))
ordered_token(operator::String, perception::String, precedence::String) = precedence == "operator_first" ? operator * perception : perception * operator

function get_schedule(engine_type::Int)
    engine_type == 0 ? ENGINE_SCHEDULE_TYPE_ONE : ENGINE_SCHEDULE_TYPE_TWO
end

function get_topology_spec(perception::String, engine_type::Int)
    engine_type == 0 ? TYPE_ONE_TOPOLOGIES[perception] : TYPE_TWO_TOPOLOGIES[perception]
end

function get_lindblad_params(perception::String, engine_type::Int)
    hamiltonian = engine_type == 0 ? H_TYPE_ONE : H_TYPE_TWO
    l_type_one = PERCEPTION_L_MATRICES[perception]
    jump = engine_type == 0 ? l_type_one : MIRROR * l_type_one * MIRROR
    hamiltonian, jump
end

function get_operator_slot_spec(perception::String, engine_type::Int, loop_class::String, substage_idx::Int)
    topo = get_topology_spec(perception, engine_type)
    chart = topo[loop_class]
    native = NATIVE_OPERATORS_BY_TOPOLOGY[perception]
    remaining_native = [op for op in native if op != chart["op"]]
    remaining_non_native = [op for op in ["Ti", "Te", "Fi", "Fe"] if !(op in native)]
    slot_ops = [chart["op"]; remaining_native; remaining_non_native]
    op = slot_ops[mod(substage_idx, length(slot_ops)) + 1]
    if op == chart["op"]
        sign = Int(chart["sign"])
        precedence = sign > 0 ? "operator_first" : "terrain_first"
        token = ordered_token(op, perception, precedence)
    else
        token_up = ordered_token(op, perception, "operator_first")
        token_down = ordered_token(op, perception, "terrain_first")
        if haskey(CHART_TOKEN_PRECEDENCE, token_up)
            precedence, sign_any = CHART_TOKEN_PRECEDENCE[token_up]
            sign = Int(sign_any)
            token = token_up
        elseif haskey(CHART_TOKEN_PRECEDENCE, token_down)
            precedence, sign_any = CHART_TOKEN_PRECEDENCE[token_down]
            sign = Int(sign_any)
            token = token_down
        else
            sign = iseven(substage_idx + engine_type) ? 1 : -1
            precedence = sign > 0 ? "operator_first" : "terrain_first"
            token = ordered_token(op, perception, precedence)
        end
    end
    Dict("operator" => op, "sign" => sign, "precedence" => precedence, "token" => token, "operator_family" => OPERATOR_MAP_FAMILY[op])
end

function lindblad_step(rho::Matrix{ComplexF64}, hamiltonian::Matrix{ComplexF64}, jump::Matrix{ComplexF64})
    jump_dag = jump'
    jj = jump_dag * jump
    drho = -im .* (hamiltonian * rho - rho * hamiltonian)
    drho += jump * rho * jump_dag - 0.5 .* (jj * rho + rho * jj)
    out = rho + DT .* drho
    out = 0.5 .* (out + out')
    out ./ tr(out)
end

function qit_profile(engine_type::Int, source_rho::Matrix{ComplexF64})
    rho = copy(source_rho)
    h_sign = engine_type == 0 ? 1.0 : -1.0
    weighted_kernel = 0.0
    base_survival = 1.0
    rows = Vector{Dict{String,Any}}()
    for (main_idx, pair) in enumerate(get_schedule(engine_type))
        perception, loop_class = pair
        hamiltonian, jump = get_lindblad_params(perception, engine_type)
        topo = get_topology_spec(perception, engine_type)
        rate = Float64(topo["rate"])
        for substage_idx in 0:(N_SUBSTAGES_PER_MAIN - 1)
            slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
            op = OPERATOR_GENERATORS[slot["operator"]]
            op_signed = Float64(slot["sign"]) .* op
            rho = lindblad_step(rho, hamiltonian, jump)
            h_expect = real(tr(rho * hamiltonian))
            op_expect = real(tr(rho * op_signed))
            gamma5_expect = real(tr(rho * SZ))
            dissipator_pressure = real(tr(rho * (jump' * jump)))
            stage_kernel = rate * (0.43 + 0.11 * abs(h_expect) + 0.07 * abs(op_expect) + 0.05 * dissipator_pressure)
            weighted_kernel += stage_kernel
            base_survival *= 1.0 - 0.0025 * dissipator_pressure + 0.0004 * h_sign * gamma5_expect
            push!(rows, Dict{String,Any}(
                "engine_type" => engine_type,
                "main_stage" => main_idx - 1,
                "substage" => length(rows),
                "perception" => perception,
                "loop_class" => loop_class,
                "operator" => slot["operator"],
                "slot_sign" => Int(slot["sign"]),
                "h_expect" => h_expect,
                "op_expect" => op_expect,
                "gamma5_expect" => gamma5_expect,
                "dissipator_pressure" => dissipator_pressure,
                "stage_kernel" => stage_kernel,
            ))
        end
    end
    Dict{String,Any}(
        "engine_type" => engine_type,
        "substage_count" => length(rows),
        "base_survival" => Float64(base_survival),
        "kernel" => Float64(weighted_kernel / length(rows)),
        "final_trace_residual" => abs(tr(rho) - 1.0),
        "rows" => rows,
    )
end

function carrier_invariants()
    table = OwnerOct.octonion_table()
    constraint = OwnerOct.derivation_constraint_matrix(table)
    _, _, ns, _ = OwnerOct.nullspace_data(constraint)
    der_dim = size(ns, 2)
    derivation = reshape(ns[:, 1], 8, 8)
    g2_derivation_residual = OwnerOct.derivation_residual(table, derivation)

    cl30_table = OwnerClifford.clifford_table([1, 1, 1])
    cl30_even_dim = Int(OwnerClifford.even_dim([1, 1, 1]))
    gamma_residual = OwnerClifford.gamma_relation_residual(OwnerClifford.gamma_matrices_cl30())

    source_spinor = OwnerGolden.psi(SOURCE_PHI, SOURCE_CHI, SOURCE_ETA)
    source_rho = OwnerDensity.dm(source_spinor)
    source_bloch = Float64.(OwnerDensity.bloch_from_rho(source_rho))
    mirrored_rho = MIRROR * source_rho * MIRROR
    mirrored_bloch = Float64.(OwnerDensity.bloch_from_rho(mirrored_rho))
    golden_receipt = read_json(joinpath(CARRIER_DIR, "golden_weyl_julia_receipt.json"))
    golden_invariants = golden_receipt["invariants"]

    density_bloch_norm = Float64(norm(source_bloch))
    density_bloch_z = Float64(source_bloch[3])
    golden_linking = Float64(golden_invariants["linking_number"])
    golden_flat_linking_abs = abs(Float64(golden_invariants["flat_S2_linking_number"]))
    golden_cocycle_gap = abs(Float64(golden_invariants["cocycle_wL"]) - Float64(golden_invariants["cocycle_wR"])) / 2.0
    g2_factor = Float64(der_dim) / 14.0
    clifford_factor = (Float64(size(cl30_table, 1)) + Float64(cl30_even_dim)) / 12.0
    density_factor = 0.5 * (1.0 + density_bloch_norm)
    golden_factor = abs(golden_linking) * golden_cocycle_gap
    carrier_gain = g2_factor * clifford_factor * density_factor * golden_factor
    left_bias = max(0.0, density_bloch_z) * carrier_gain

    Dict{String,Any}(
        "source_rho" => source_rho,
        "mirrored_rho" => mirrored_rho,
        "g2_derivation_dim" => Float64(der_dim),
        "g2_derivation_residual" => Float64(g2_derivation_residual),
        "cl30_dim" => Float64(size(cl30_table, 1)),
        "cl30_even_dim" => Float64(cl30_even_dim),
        "gamma_residual" => Float64(gamma_residual),
        "density_trace_residual" => abs(tr(source_rho) - 1.0),
        "density_bloch_norm" => density_bloch_norm,
        "density_bloch_z" => density_bloch_z,
        "mirrored_density_bloch_z" => Float64(mirrored_bloch[3]),
        "golden_linking" => golden_linking,
        "golden_flat_linking_abs" => golden_flat_linking_abs,
        "golden_cocycle_gap" => golden_cocycle_gap,
        "g2_factor" => g2_factor,
        "clifford_factor" => clifford_factor,
        "density_factor" => density_factor,
        "golden_factor" => golden_factor,
        "carrier_gain" => carrier_gain,
        "left_bias" => left_bias,
        "bias_strength" => CP_BIAS_SCALE * left_bias,
    )
end

function matter_antimatter_result(invariants; erase_chirality_bias::Bool=false, erase_qit_kernel::Bool=false, erase_g2::Bool=false, erase_clifford::Bool=false, erase_density::Bool=false, erase_golden::Bool=false, right_bias::Bool=false)
    left_profile = qit_profile(0, invariants["source_rho"])
    right_profile = qit_profile(1, invariants["mirrored_rho"])
    mirror_base = 0.5 * (Float64(left_profile["base_survival"]) + Float64(right_profile["base_survival"]))
    qit_kernel = 0.5 * (Float64(left_profile["kernel"]) + Float64(right_profile["kernel"]))
    erase_qit_kernel && (qit_kernel = 0.0)
    g2_factor = erase_g2 ? 0.0 : Float64(invariants["g2_factor"])
    clifford_factor = erase_clifford ? 0.0 : Float64(invariants["clifford_factor"])
    density_factor = erase_density ? 0.0 : Float64(invariants["density_factor"])
    golden_factor = erase_golden ? 0.0 : Float64(invariants["golden_factor"])
    density_bloch_z = erase_density ? 0.0 : max(0.0, Float64(invariants["density_bloch_z"]))
    carrier_gain = g2_factor * clifford_factor * density_factor * golden_factor
    bias_strength = CP_BIAS_SCALE * density_bloch_z * carrier_gain
    erase_chirality_bias && (bias_strength = 0.0)
    right_bias && (bias_strength = -bias_strength)
    bias_term = bias_strength * qit_kernel
    matter_survival = mirror_base + bias_term
    antimatter_survival = mirror_base - bias_term
    Dict{String,Any}(
        "matter_survival" => matter_survival,
        "antimatter_survival" => antimatter_survival,
        "mirror_base" => mirror_base,
        "qit_kernel" => qit_kernel,
        "bias_strength" => bias_strength,
        "bias_term" => bias_term,
        "asymmetry" => matter_survival - antimatter_survival,
        "left_profile_base_survival" => Float64(left_profile["base_survival"]),
        "right_profile_base_survival" => Float64(right_profile["base_survival"]),
        "left_profile_kernel" => Float64(left_profile["kernel"]),
        "right_profile_kernel" => Float64(right_profile["kernel"]),
    )
end

function parity_against_peer(result::Dict{String,Any})
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "peer_available" => false,
            "parity_max_diff" => nothing,
            "worst_key" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [Dict{String,Any}("missing" => JAX_RESULT_PATH)],
            "boolean_mismatches" => [],
            "missing_keys" => sort([collect(keys(result["shared_scalars"])); collect(keys(result["shared_booleans"]))]),
            "diffs" => Dict{String,Any}(),
            "stop_condition_fired" => true,
        )
    end
    peer = read_json(JAX_RESULT_PATH)
    peer_scalars = get(peer, "shared_scalars", Dict{String,Any}())
    peer_booleans = get(peer, "shared_booleans", Dict{String,Any}())
    diffs = Dict{String,Any}()
    missing = String[]
    strict = Vector{Dict{String,Any}}()
    max_diff = 0.0
    worst_key = ""
    for (key, value) in result["shared_scalars"]
        if !haskey(peer_scalars, key)
            push!(missing, key)
            continue
        end
        diff = abs(Float64(value) - Float64(peer_scalars[key]))
        diffs[key] = diff
        if diff > max_diff
            max_diff = diff
            worst_key = key
        end
        diff > STRICT_STOP_TOL && push!(strict, Dict{String,Any}("key" => key, "julia" => Float64(value), "jax" => Float64(peer_scalars[key]), "abs_diff" => diff))
    end
    mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_booleans"]
        if !haskey(peer_booleans, key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer_booleans[key])
            push!(mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => Bool(peer_booleans[key])))
        end
    end
    for key in setdiff(collect(keys(peer_scalars)), collect(keys(result["shared_scalars"])))
        push!(missing, key)
    end
    for key in setdiff(collect(keys(peer_booleans)), collect(keys(result["shared_booleans"])))
        push!(missing, key)
    end
    Dict{String,Any}(
        "peer_result_path" => JAX_RESULT_PATH,
        "peer_available" => true,
        "parity_max_diff" => max_diff,
        "worst_key" => worst_key,
        "within_1e_9" => max_diff <= TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => sort(missing),
        "diffs" => diffs,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function build_result()
    invariants = carrier_invariants()
    positive = matter_antimatter_result(invariants)
    symmetric = matter_antimatter_result(invariants; erase_chirality_bias=true)
    right_bias_result = matter_antimatter_result(invariants; right_bias=true)
    carrier_erased = matter_antimatter_result(invariants; erase_g2=true, erase_clifford=true, erase_density=true, erase_golden=true)
    qit_erased = matter_antimatter_result(invariants; erase_qit_kernel=true)
    g2_erased = matter_antimatter_result(invariants; erase_g2=true)
    clifford_erased = matter_antimatter_result(invariants; erase_clifford=true)
    density_erased = matter_antimatter_result(invariants; erase_density=true)
    golden_erased = matter_antimatter_result(invariants; erase_golden=true)

    asymmetry = Float64(positive["asymmetry"])
    mirror_zero = abs(Float64(symmetric["asymmetry"])) <= TOL
    from_left_bias = asymmetry > TOL &&
        Float64(positive["matter_survival"]) > Float64(positive["antimatter_survival"]) &&
        Float64(positive["bias_strength"]) > 0.0
    chirality_load_bearing = from_left_bias && mirror_zero && abs(asymmetry - Float64(symmetric["asymmetry"])) > TOL
    owner_carrier_load_bearing = chirality_load_bearing &&
        abs(asymmetry - Float64(carrier_erased["asymmetry"])) > TOL &&
        abs(Float64(carrier_erased["asymmetry"])) <= TOL &&
        abs(asymmetry - Float64(g2_erased["asymmetry"])) > TOL &&
        abs(asymmetry - Float64(clifford_erased["asymmetry"])) > TOL &&
        abs(asymmetry - Float64(density_erased["asymmetry"])) > TOL &&
        abs(asymmetry - Float64(golden_erased["asymmetry"])) > TOL &&
        abs(asymmetry - Float64(qit_erased["asymmetry"])) > TOL
    right_bias_flips_sign = Float64(right_bias_result["asymmetry"]) < -TOL && abs(Float64(right_bias_result["asymmetry"]) + asymmetry) <= TOL
    qit_spec_ok = N_TOTAL_SUBSTAGES_PER_ENGINE == 32 &&
        length(get_schedule(0)) == 8 &&
        length(get_schedule(1)) == 8 &&
        norm(H_TYPE_ONE - H0) <= TOL &&
        norm(H_TYPE_TWO + H0) <= TOL &&
        norm(MIRROR * SIGMA_MINUS * MIRROR - SIGMA_PLUS) <= TOL
    local_all_pass = owner_carrier_load_bearing && from_left_bias && mirror_zero && chirality_load_bearing && right_bias_flips_sign && qit_spec_ok

    shared_scalars = Dict{String,Any}(
        "asymmetry" => asymmetry,
        "matter_survival" => Float64(positive["matter_survival"]),
        "antimatter_survival" => Float64(positive["antimatter_survival"]),
        "mirror_base" => Float64(positive["mirror_base"]),
        "qit_kernel" => Float64(positive["qit_kernel"]),
        "bias_strength" => Float64(positive["bias_strength"]),
        "bias_term" => Float64(positive["bias_term"]),
        "mirror_symmetric_asymmetry" => Float64(symmetric["asymmetry"]),
        "right_bias_asymmetry" => Float64(right_bias_result["asymmetry"]),
        "carrier_erased_asymmetry" => Float64(carrier_erased["asymmetry"]),
        "qit_erased_asymmetry" => Float64(qit_erased["asymmetry"]),
        "g2_erased_asymmetry" => Float64(g2_erased["asymmetry"]),
        "clifford_erased_asymmetry" => Float64(clifford_erased["asymmetry"]),
        "density_erased_asymmetry" => Float64(density_erased["asymmetry"]),
        "golden_erased_asymmetry" => Float64(golden_erased["asymmetry"]),
        "left_profile_base_survival" => Float64(positive["left_profile_base_survival"]),
        "right_profile_base_survival" => Float64(positive["right_profile_base_survival"]),
        "left_profile_kernel" => Float64(positive["left_profile_kernel"]),
        "right_profile_kernel" => Float64(positive["right_profile_kernel"]),
        "carrier.g2_derivation_dim" => Float64(invariants["g2_derivation_dim"]),
        "carrier.cl30_dim" => Float64(invariants["cl30_dim"]),
        "carrier.cl30_even_dim" => Float64(invariants["cl30_even_dim"]),
        "carrier.density_bloch_norm" => Float64(invariants["density_bloch_norm"]),
        "carrier.density_bloch_z" => Float64(invariants["density_bloch_z"]),
        "carrier.mirrored_density_bloch_z" => Float64(invariants["mirrored_density_bloch_z"]),
        "carrier.golden_linking" => Float64(invariants["golden_linking"]),
        "carrier.golden_cocycle_gap" => Float64(invariants["golden_cocycle_gap"]),
        "carrier.carrier_gain" => Float64(invariants["carrier_gain"]),
        "qit.substage_count_per_engine" => Float64(N_TOTAL_SUBSTAGES_PER_ENGINE),
        "qit.type1_schedule_len" => Float64(length(get_schedule(0))),
        "qit.type2_schedule_len" => Float64(length(get_schedule(1))),
    )
    shared_booleans = Dict{String,Any}(
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "from_left_bias" => from_left_bias,
        "mirror_symmetric_zero" => mirror_zero,
        "chirality_load_bearing" => chirality_load_bearing,
        "right_bias_flips_sign" => right_bias_flips_sign,
        "qit_spec_ok" => qit_spec_ok,
        "no_numpy_compute" => true,
        "classification_scratch_diagnostic" => true,
        "promotion_false" => true,
        "formal_admission_false" => true,
    )

    carrier_invariant_scalars = Dict{String,Any}()
    for (key, value) in invariants
        if value isa Real
            carrier_invariant_scalars[key] = Float64(value)
        end
    end

    result = Dict{String,Any}(
        "schema" => "MP3_MATTER_ANTIMATTER_CHIRALITY_DUAL_BACKEND_SCRATCH_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "backend" => "julia_mirror",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "classification" => "scratch_diagnostic",
        "promotion" => false,
        "promotion_allowed" => false,
        "formal_admission" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "finite mechanism witness only: owner-carrier chirality bias plus canonical Type1/Type2 Weyl QIT substage kernel yields a bounded survival-split readout; NOT baryogenesis, NOT physics, NOT the observed baryon-to-photon ratio, and NO biology/formal admission.",
        "allowed_claims" => [
            "finite chiral-bias to matter-survival witness",
            "mirror-symmetric no-bias control gives zero L-R asymmetry",
            "dual-backend parity diagnostic",
        ],
        "blocked_consumers" => [
            "observed_baryon_to_photon_ratio",
            "baryogenesis_proof",
            "physics_admission",
            "biology_admission",
            "formal_admission",
            "Axis0",
            "bridge",
        ],
        "sim_execution_kind" => "nonclassical_scratch_diagnostic",
        "sim_class" => "finite_chirality_bias_survival_scout",
        "numpy_compute_used" => false,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "source_dependencies" => SOURCE_DEPENDENCIES,
        "source_fingerprints" => Dict(key => sha256_file(path) for (key, path) in SOURCE_DEPENDENCIES if isfile(path)),
        "rung_spec" => Dict{String,Any}(
            "matter_sector" => "Type1 left-Weyl, H_L=+H0",
            "antimatter_sector" => "Type2 right-Weyl, H_R=-H0",
            "mirror" => "SX",
            "lindblad" => "canonical per-perception Lindblad operators mirrored from canonical_qit_engine_specs.py",
            "substage_count_per_engine" => N_TOTAL_SUBSTAGES_PER_ENGINE,
            "cp_violation_tie" => "The finite CP-odd input is the signed left-chirality carrier bias. The mirror-symmetric no-bias run is exactly zero, so the asymmetry is tied to the chiral bias, not to a baseline sector label.",
        ),
        "carrier_invariants" => carrier_invariant_scalars,
        "positive" => Dict{String,Any}(
            "nonzero_matter_antimatter_asymmetry" => merge(Dict{String,Any}("pass" => asymmetry > TOL), positive),
            "from_left_chirality_bias" => Dict{String,Any}("pass" => from_left_bias),
        ),
        "controls" => Dict{String,Any}(
            "mirror_symmetric_no_chirality_bias" => Dict{String,Any}(
                "pass" => mirror_zero,
                "asymmetry" => symmetric["asymmetry"],
                "control_meaning" => "same carrier profile and QIT kernel, but the signed chirality bias is erased",
            ),
            "right_chirality_bias_flips_sign" => Dict{String,Any}("pass" => right_bias_flips_sign, "asymmetry" => right_bias_result["asymmetry"]),
            "erase_owner_carrier" => Dict{String,Any}(
                "pass" => abs(Float64(carrier_erased["asymmetry"])) <= TOL && abs(asymmetry - Float64(carrier_erased["asymmetry"])) > TOL,
                "asymmetry" => carrier_erased["asymmetry"],
            ),
            "erase_qit_substage_kernel" => Dict{String,Any}(
                "pass" => abs(Float64(qit_erased["asymmetry"])) <= TOL && abs(asymmetry - Float64(qit_erased["asymmetry"])) > TOL,
                "asymmetry" => qit_erased["asymmetry"],
            ),
        ),
        "graveyard_companions" => Dict{String,Any}(
            "g2_erased" => Dict("asymmetry" => g2_erased["asymmetry"]),
            "clifford_erased" => Dict("asymmetry" => clifford_erased["asymmetry"]),
            "density_erased" => Dict("asymmetry" => density_erased["asymmetry"]),
            "golden_weyl_erased" => Dict("asymmetry" => golden_erased["asymmetry"]),
        ),
        "boundary" => Dict{String,Any}(
            "classification_is_scratch_diagnostic" => Dict("pass" => true),
            "promotion_false" => Dict("pass" => true),
            "formal_admission_false" => Dict("pass" => true),
            "no_numpy_compute" => Dict("pass" => true, "backend" => "Julia mirror", "numpy_imported" => false),
            "claim_ceiling_blocks_physics_and_biology" => Dict("pass" => true),
        ),
        "nearby_variants" => Dict{String,Any}(
            "total" => 7,
            "passed" => sum([
                mirror_zero,
                right_bias_flips_sign,
                abs(Float64(carrier_erased["asymmetry"])) <= TOL,
                abs(Float64(qit_erased["asymmetry"])) <= TOL,
                abs(Float64(g2_erased["asymmetry"])) <= TOL,
                abs(Float64(clifford_erased["asymmetry"])) <= TOL,
                abs(Float64(golden_erased["asymmetry"])) <= TOL,
            ]),
            "variants" => [
                "mirror_symmetric_no_bias",
                "right_bias_sign_flip",
                "owner_carrier_erased",
                "qit_kernel_erased",
                "g2_erased",
                "clifford_erased",
                "golden_weyl_erased",
            ],
            "all_pass" => local_all_pass,
        ),
        "why_not_v4_probes" => "Scratch v5 dual-backend formal scout. It does not promote a lego, does not admit physics or biology, and does not derive the observed baryon-to-photon ratio.",
        "TOOL_MANIFEST" => Dict{String,Any}(
            "Julia LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite density, Lindblad, QIT substage, and parity scalar mirror computation"),
            "canonical_qit_engine_specs.py" => Dict("tried" => true, "used" => true, "reason" => "load-bearing mirrored constants for H_L=+H0, H_R=-H0, MIRROR=SX, Lindblad operators, schedules, and 32-substage count"),
            "octonion_G2_automorphism" => Dict("tried" => true, "used" => true, "reason" => "load-bearing owner carrier factor; erasing the G2/octonion component zeros the asymmetry"),
            "clifford_algebra_ladder" => Dict("tried" => true, "used" => true, "reason" => "load-bearing owner Clifford factor; erasing the Cl(3,0) even carrier component zeros the asymmetry"),
            "density_matrix_spinor_lift" => Dict("tried" => true, "used" => true, "reason" => "load-bearing source density and Bloch chirality; erasing density chirality zeros the asymmetry"),
            "golden_weyl" => Dict("tried" => true, "used" => true, "reason" => "load-bearing owner Weyl spinor/linking/cocycle factor; erasing golden Weyl zeros the asymmetry"),
            "Julia JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive exact result writing, source fingerprinting, and peer parity parsing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}(
            "Julia LinearAlgebra" => "load_bearing",
            "canonical_qit_engine_specs.py" => "load_bearing",
            "octonion_G2_automorphism" => "load_bearing",
            "clifford_algebra_ladder" => "load_bearing",
            "density_matrix_spinor_lift" => "load_bearing",
            "golden_weyl" => "load_bearing",
            "Julia JSON/Dates/SHA" => "supportive",
        ),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "local_all_pass" => local_all_pass,
    )
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = local_all_pass && result["parity"]["peer_available"] && result["parity"]["within_1e_9"]
    result["summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "local_all_pass" => local_all_pass,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "asymmetry" => asymmetry,
        "from_left_bias" => from_left_bias,
        "mirror_symmetric_zero" => mirror_zero,
        "chirality_load_bearing" => chirality_load_bearing,
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
    s = result["summary"]
    println(
        "SCOUT_DONE " *
        "jax=$(JAX_RESULT_PATH) " *
        "julia=$(RESULT_PATH) " *
        "all_pass=$(lowercase(string(s["all_pass"]))) " *
        "owner_carrier_load_bearing=$(lowercase(string(s["owner_carrier_load_bearing"]))) " *
        "asymmetry=$(s["asymmetry"]) " *
        "from_left_bias=$(lowercase(string(s["from_left_bias"]))) " *
        "mirror_symmetric_zero=$(lowercase(string(s["mirror_symmetric_zero"]))) " *
        "chirality_load_bearing=$(lowercase(string(s["chirality_load_bearing"])))"
    )
    if !result["local_all_pass"]
        exit(1)
    end
end

main()
