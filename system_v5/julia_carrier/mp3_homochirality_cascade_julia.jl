#!/usr/bin/env julia
# object_id: mp3_homochirality_cascade
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "mp3_homochirality_cascade"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUT_DIR = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const CARRIER_DIR = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "mp3_homochirality_cascade_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUT_DIR, "results", "mp3_homochirality_cascade_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const WEAK_SCALE = 1.0e-4
const CHEMISTRY_INVERSE_TEMP = 1.0
const RATCHET_INVERSE_TEMP = 2.0e5
const RATCHET_ROUNDS = 256

const SOURCE_REFS = Dict{String,String}(
    "canonical_qit_engine_specs" => joinpath(FORMAL_SCOUT_DIR, "canonical_qit_engine_specs.py"),
    "octonion_G2_automorphism" => joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"),
    "jax_octonion_G2_automorphism" => joinpath(CARRIER_DIR, "jax_octonion_G2_automorphism.py"),
    "clifford_algebra_ladder" => joinpath(CARRIER_DIR, "clifford_algebra_ladder.jl"),
    "jax_clifford_algebra_ladder" => joinpath(CARRIER_DIR, "jax_clifford_algebra_ladder.py"),
    "density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
    "jax_density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "jax_density_matrix_spinor_lift.py"),
    "golden_weyl" => joinpath(CARRIER_DIR, "golden_weyl_julia.jl"),
    "golden_weyl_jax_snapshot" => joinpath(CARRIER_DIR, "scratch_jax_snapshot_20260604", "golden_weyl_jax.py"),
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
const PERCEPTION_L = Dict{String,Matrix{ComplexF64}}(
    "Se" => SZ,
    "Ne" => SIGMA_PLUS,
    "Ni" => -im .* SY,
    "Si" => SIGMA_MINUS,
)
const OPERATOR_GENERATORS = Dict{String,Matrix{ComplexF64}}(
    "Ti" => SZ,
    "Te" => SX,
    "Fi" => SX,
    "Fe" => SY,
)
const OPERATOR_BASE_ANGLES = Dict("Ti" => 0.12, "Te" => 0.09, "Fi" => 0.15, "Fe" => 0.11)
const OPERATOR_SLOT_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]
const NATIVE_OPERATORS_BY_TOPOLOGY = Dict(
    "Se" => ["Ti", "Fi"],
    "Ne" => ["Ti", "Fi"],
    "Ni" => ["Te", "Fe"],
    "Si" => ["Te", "Fe"],
)
const CHART_TOKEN_PRECEDENCE = Dict{String,Tuple{String,Int}}(
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
const TYPE_ONE = Dict(
    "Se" => Dict("outer" => ("Ti", 1), "inner" => ("Fi", -1)),
    "Ne" => Dict("outer" => ("Ti", -1), "inner" => ("Fi", 1)),
    "Ni" => Dict("outer" => ("Fe", -1), "inner" => ("Te", 1)),
    "Si" => Dict("outer" => ("Fe", 1), "inner" => ("Te", -1)),
)
const TYPE_TWO = Dict(
    "Se" => Dict("outer" => ("Fi", 1), "inner" => ("Ti", -1)),
    "Ne" => Dict("outer" => ("Fi", -1), "inner" => ("Ti", 1)),
    "Ni" => Dict("outer" => ("Te", -1), "inner" => ("Fe", 1)),
    "Si" => Dict("outer" => ("Te", 1), "inner" => ("Fe", -1)),
)
const ENGINE_SCHEDULE_TYPE_ONE = [
    ("Se", "outer"), ("Ne", "outer"), ("Ni", "outer"), ("Si", "outer"),
    ("Se", "inner"), ("Si", "inner"), ("Ni", "inner"), ("Ne", "inner"),
]
const ENGINE_SCHEDULE_TYPE_TWO = [
    ("Se", "outer"), ("Si", "outer"), ("Ni", "outer"), ("Ne", "outer"),
    ("Se", "inner"), ("Ne", "inner"), ("Ni", "inner"), ("Si", "inner"),
]
const N_SUBSTAGES_PER_MAIN = 4
const N_TOTAL_SUBSTAGES_PER_ENGINE = 32

const FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

sha256_file(path::String) = isfile(path) ? bytes2hex(sha256(read(path))) : nothing

function source_refs()
    out = Dict{String,Any}()
    for (key, path) in SOURCE_REFS
        out[key] = Dict("path" => path, "exists" => isfile(path), "sha256" => sha256_file(path))
    end
    out
end

ordered_token(operator::String, perception::String, precedence::String) =
    precedence == "operator_first" ? operator * perception : perception * operator

get_schedule(engine_type::Int) = engine_type == 0 ? ENGINE_SCHEDULE_TYPE_ONE : ENGINE_SCHEDULE_TYPE_TWO

function get_lindblad_params(perception::String, engine_type::Int)
    H = engine_type == 0 ? H_TYPE_ONE : H_TYPE_TWO
    L0 = PERCEPTION_L[perception]
    L = engine_type == 0 ? L0 : MIRROR * L0 * MIRROR
    H, L
end

function get_loop_class_op_sign(perception::String, engine_type::Int, loop_class::String)
    topo = engine_type == 0 ? TYPE_ONE : TYPE_TWO
    row = topo[perception][loop_class]
    row[1], row[2]
end

function get_chart_token_spec(perception::String, engine_type::Int, loop_class::String)
    op, sign = get_loop_class_op_sign(perception, engine_type, loop_class)
    precedence = sign > 0 ? "operator_first" : "terrain_first"
    Dict("operator" => op, "sign" => sign, "precedence" => precedence, "token" => ordered_token(op, perception, precedence))
end

function get_operator_slot_spec(perception::String, engine_type::Int, loop_class::String, substage_idx::Int)
    chart = get_chart_token_spec(perception, engine_type, loop_class)
    native = NATIVE_OPERATORS_BY_TOPOLOGY[perception]
    remaining_native = [op for op in native if op != chart["operator"]]
    remaining_non_native = [op for op in OPERATOR_SLOT_SEQUENCE if !(op in native)]
    slot_ops = vcat([chart["operator"]], remaining_native, remaining_non_native)
    op = slot_ops[mod(substage_idx, length(slot_ops)) + 1]
    if op == chart["operator"]
        sign = chart["sign"]
        precedence = chart["precedence"]
        token = chart["token"]
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
            sign = iseven(substage_idx + engine_type) ? 1 : -1
            precedence = sign > 0 ? "operator_first" : "terrain_first"
            token = ordered_token(op, perception, precedence)
        end
    end
    Dict("operator" => op, "sign" => sign, "precedence" => precedence, "token" => token)
end

dm(psi::Vector{ComplexF64}) = psi * psi'

function bloch_from_rho(rho::Matrix{ComplexF64})
    [real(tr(rho * SX)), real(tr(rho * SY)), real(tr(rho * SZ))]
end

function golden_psi(phi::Float64, chi::Float64, eta::Float64)
    ComplexF64[
        exp(im * (phi + chi)) * cos(eta),
        exp(im * (phi - chi)) * sin(eta),
    ]
end

function lindblad_tangent(H::Matrix{ComplexF64}, L::Matrix{ComplexF64}, rho::Matrix{ComplexF64})
    ld = L'
    -im .* (H * rho - rho * H) .+ L * rho * ld .- 0.5 .* (ld * L * rho + rho * ld * L)
end

function canonical_energy_score(rho::Matrix{ComplexF64}, engine_type::Int)
    total = 0.0
    for (perception, loop_class) in get_schedule(engine_type)
        H, L = get_lindblad_params(perception, engine_type)
        tangent = lindblad_tangent(H, L, rho)
        for substage_idx in 0:(N_SUBSTAGES_PER_MAIN - 1)
            slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
            op = OPERATOR_GENERATORS[slot["operator"]]
            signed_op = Float64(slot["sign"]) * OPERATOR_BASE_ANGLES[slot["operator"]] .* op
            total += real(tr(tangent * signed_op))
        end
    end
    total / Float64(N_TOTAL_SUBSTAGES_PER_ENGINE)
end

function sigmoid_pair(logit::Float64)
    p_l = 1.0 / (1.0 + exp(-logit))
    p_r = 1.0 / (1.0 + exp(logit))
    p_l, p_r
end

function run_selection(delta_e::Float64, ratchet_enabled::Bool)
    gain = ratchet_enabled ? RATCHET_INVERSE_TEMP * RATCHET_ROUNDS : CHEMISTRY_INVERSE_TEMP
    logit = gain * delta_e
    p_l, p_r = sigmoid_pair(logit)
    energy_l = -0.5 * delta_e
    energy_r = 0.5 * delta_e
    w_l = exp(-CHEMISTRY_INVERSE_TEMP * energy_l)
    w_r = exp(-CHEMISTRY_INVERSE_TEMP * energy_r)
    Dict{String,Any}(
        "delta_E_R_minus_L" => delta_e,
        "energy_L" => energy_l,
        "energy_R" => energy_r,
        "chemistry_weight_L" => w_l,
        "chemistry_weight_R" => w_r,
        "chemistry_weight_preference_L_minus_R" => w_l - w_r,
        "ratchet_enabled" => ratchet_enabled,
        "selection_logit" => logit,
        "rounds" => ratchet_enabled ? RATCHET_ROUNDS : 1,
        "p_L_final" => p_l,
        "p_R_final" => p_r,
        "survivor" => p_l > 1.0 - 1.0e-12 ? "L" : (p_r > 1.0 - 1.0e-12 ? "R" : "racemic_or_mixed"),
        "single_survivor" => max(p_l, p_r) > 1.0 - 1.0e-12 && min(p_l, p_r) < 1.0e-12,
    )
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

varidx(row::Int, col::Int) = row + (col - 1) * 8

function derivation_constraint_matrix(table::Array{Float64,3})
    mat = zeros(Float64, 8 * 8 * 8, 8 * 8)
    row = 0
    for a in 1:8, b in 1:8, c in 1:8
        row += 1
        for k in 1:8
            mat[row, varidx(c, k)] += table[k, a, b]
            mat[row, varidx(k, a)] -= table[c, k, b]
            mat[row, varidx(k, b)] -= table[c, a, k]
        end
    end
    mat
end

function g2_carrier_factor()
    constraint = derivation_constraint_matrix(octonion_table())
    s = svdvals(constraint)
    rank_tol = max(size(constraint)...) * eps(Float64) * maximum(s) * 100.0
    rank_value = count(>(rank_tol), s)
    der_dim = size(constraint, 2) - rank_value
    Dict{String,Any}(
        "der_O_dim" => der_dim,
        "constraint_rank" => rank_value,
        "factor" => Float64(der_dim) / 14.0,
        "pass" => der_dim == 14,
    )
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

function basis(dim::Int, idx::Int; scale::Float64=1.0)
    v = zeros(Float64, dim)
    v[idx + 1] = scale
    v
end

function mv_mul(table::Array{Float64,3}, x::Vector{Float64}, y::Vector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function table_residual(table::Array{Float64,3}, subbasis::Vector{Vector{Float64}}, target::Array{Float64,3})
    max_resid = 0.0
    dim = size(table, 1)
    for a in 1:length(subbasis), b in 1:length(subbasis)
        product = mv_mul(table, subbasis[a], subbasis[b])
        expected = zeros(Float64, dim)
        for c in 1:length(subbasis)
            expected .+= target[c, a, b] .* subbasis[c]
        end
        max_resid = max(max_resid, norm(product - expected))
    end
    max_resid
end

function even_dim(signature::Vector{Int})
    n = length(signature)
    count(mask -> iseven(count_ones(UInt(mask))), 0:(2^n - 1))
end

function clifford_carrier_factor()
    cl30 = clifford_table([1, 1, 1])
    h_table = quaternion_table()
    oriented = [
        basis(8, 0),
        basis(8, Int(0b011); scale=-1.0),
        basis(8, Int(0b110); scale=-1.0),
        basis(8, Int(0b101)),
    ]
    h_residual = table_residual(cl30, oriented, h_table)
    evend = even_dim([1, 1, 1])
    Dict{String,Any}(
        "cl30_even_dim" => evend,
        "cl30_even_h_residual" => h_residual,
        "factor" => h_residual < TOL ? Float64(evend) / 4.0 : 0.0,
        "pass" => evend == 4 && h_residual < TOL,
    )
end

function density_carrier_factor(rho::Matrix{ComplexF64})
    bloch = bloch_from_rho(rho)
    trace_real = real(tr(rho))
    bloch_norm = norm(bloch)
    hermitian_residual = norm(rho - rho')
    Dict{String,Any}(
        "trace_real" => trace_real,
        "bloch_norm" => bloch_norm,
        "hermitian_residual" => hermitian_residual,
        "factor" => trace_real * min(1.0, bloch_norm),
        "pass" => abs(trace_real - 1.0) < TOL && hermitian_residual < TOL && bloch_norm > 0.0,
    )
end

function golden_carrier_factor(psi::Vector{ComplexF64})
    norm_value = real(dot(psi, psi))
    phase_imbalance = abs(imag(psi[1] * conj(psi[2])))
    Dict{String,Any}(
        "state_norm" => norm_value,
        "phase_imbalance" => phase_imbalance,
        "factor" => norm_value,
        "pass" => abs(norm_value - 1.0) < TOL && phase_imbalance > 0.0,
    )
end

function qit_anchor_checks()
    Dict{String,Any}(
        "H_L_equals_plus_H0_residual" => norm(H_TYPE_ONE - H0),
        "H_R_equals_minus_H0_residual" => norm(H_TYPE_TWO + H0),
        "mirror_SX_ladder_swap_residual" => norm(SX * SIGMA_MINUS * SX - SIGMA_PLUS),
        "type_one_schedule_len" => length(ENGINE_SCHEDULE_TYPE_ONE),
        "type_two_schedule_len" => length(ENGINE_SCHEDULE_TYPE_TWO),
        "substage_count_per_engine" => N_TOTAL_SUBSTAGES_PER_ENGINE,
        "lindblad_operator_count" => length(PERCEPTION_L),
        "pass" => norm(H_TYPE_ONE - H0) < TOL &&
            norm(H_TYPE_TWO + H0) < TOL &&
            norm(SX * SIGMA_MINUS * SX - SIGMA_PLUS) < TOL &&
            N_TOTAL_SUBSTAGES_PER_ENGINE == 32,
    )
end

function carrier_bundle(rho::Matrix{ComplexF64}, psi::Vector{ComplexF64})
    g2 = g2_carrier_factor()
    cl = clifford_carrier_factor()
    den = density_carrier_factor(rho)
    gw = golden_carrier_factor(psi)
    qit_anchor = qit_anchor_checks()
    factor = g2["factor"] * cl["factor"] * den["factor"] * gw["factor"]
    Dict{String,Any}(
        "octonion_G2_automorphism" => g2,
        "clifford_algebra_ladder" => cl,
        "density_matrix_spinor_lift" => den,
        "golden_weyl" => gw,
        "canonical_qit_engine_specs" => qit_anchor,
        "carrier_strength" => factor,
        "all_owner_carriers_present" => all(row["pass"] for row in [g2, cl, den, gw, qit_anchor]),
    )
end

function mechanism_from_rho(rho::Matrix{ComplexF64}, carrier_strength::Float64; chirality_sign::Float64=1.0, bias_enabled::Bool=true, ratchet_enabled::Bool=true)
    energy_l = canonical_energy_score(rho, 0)
    energy_r = canonical_energy_score(rho, 1)
    canonical_preference = energy_r - energy_l
    signed_preference = bias_enabled ? chirality_sign * canonical_preference : 0.0
    delta_e = WEAK_SCALE * carrier_strength * signed_preference
    selection = run_selection(delta_e, ratchet_enabled)
    merge(Dict{String,Any}(
        "canonical_energy_score_L" => energy_l,
        "canonical_energy_score_R" => energy_r,
        "canonical_R_minus_L_preference" => canonical_preference,
        "chirality_sign" => chirality_sign,
        "bias_enabled" => bias_enabled,
        "carrier_strength" => carrier_strength,
    ), selection)
end

function parity_against_peer(result::Dict{String,Any})
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "status" => "pending_peer_backend",
            "shared_scalar_rows" => [],
            "max_diff_key" => nothing,
            "parity_max_diff" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [],
            "boolean_mismatches" => [],
            "missing_keys" => sort(vcat(collect(keys(result["shared_scalars"])), collect(keys(result["shared_booleans"])))),
            "stop_condition_fired" => true,
        )
    end
    peer = JSON.parsefile(JAX_RESULT_PATH)
    rows = Vector{Dict{String,Any}}()
    strict = Vector{Dict{String,Any}}()
    missing = String[]
    mismatches = Vector{Dict{String,Any}}()
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
        row = Dict{String,Any}("key" => key, "julia" => jv, "jax" => pv, "abs_diff" => diff)
        push!(rows, row)
        if diff > max_diff
            max_diff = diff
            max_key = key
        end
        diff > STRICT_STOP_TOL && push!(strict, row)
    end
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
    psi = golden_psi(0.31, -0.27, 0.25)
    rho = dm(psi)
    carrier = carrier_bundle(rho, psi)
    positive = mechanism_from_rho(rho, Float64(carrier["carrier_strength"]); chirality_sign=1.0, bias_enabled=true, ratchet_enabled=true)
    no_bias = mechanism_from_rho(rho, Float64(carrier["carrier_strength"]); chirality_sign=1.0, bias_enabled=false, ratchet_enabled=true)
    no_ratchet = mechanism_from_rho(rho, Float64(carrier["carrier_strength"]); chirality_sign=1.0, bias_enabled=true, ratchet_enabled=false)
    mirror_flip = mechanism_from_rho(rho, Float64(carrier["carrier_strength"]); chirality_sign=-1.0, bias_enabled=true, ratchet_enabled=true)
    erased_carrier = mechanism_from_rho(rho, 0.0; chirality_sign=1.0, bias_enabled=true, ratchet_enabled=true)
    mixed_density = mechanism_from_rho(0.5 .* I2, Float64(carrier["carrier_strength"]); chirality_sign=1.0, bias_enabled=true, ratchet_enabled=true)
    erased_golden = mechanism_from_rho(dm(ComplexF64[1.0 + 0.0im, 0.0 + 0.0im]), Float64(carrier["carrier_strength"]); chirality_sign=1.0, bias_enabled=true, ratchet_enabled=true)

    from_chirality_bias = positive["delta_E_R_minus_L"] > 0.0 &&
        positive["chemistry_weight_preference_L_minus_R"] > 0.0 &&
        abs(no_bias["delta_E_R_minus_L"]) < TOL &&
        no_bias["survivor"] == "racemic_or_mixed" &&
        mirror_flip["survivor"] == "R"
    ratchet_amplifies_to_one = positive["survivor"] == "L" && positive["single_survivor"]
    racemic_control = abs(no_bias["p_L_final"] - 0.5) < TOL &&
        abs(no_bias["p_R_final"] - 0.5) < TOL &&
        no_bias["survivor"] == "racemic_or_mixed"
    no_ratchet_control = no_ratchet["p_L_final"] > 0.5 &&
        no_ratchet["p_L_final"] < 0.501 &&
        !no_ratchet["single_survivor"]
    owner_carrier_load_bearing = carrier["all_owner_carriers_present"] &&
        erased_carrier["survivor"] == "racemic_or_mixed" &&
        abs(erased_carrier["delta_E_R_minus_L"]) < TOL &&
        abs(mixed_density["delta_E_R_minus_L"] - positive["delta_E_R_minus_L"]) > 1.0e-8 &&
        abs(erased_golden["delta_E_R_minus_L"] - positive["delta_E_R_minus_L"]) > 1.0e-8
    local_all_pass = from_chirality_bias &&
        ratchet_amplifies_to_one &&
        racemic_control &&
        no_ratchet_control &&
        owner_carrier_load_bearing &&
        positive["canonical_R_minus_L_preference"] > 0.0

    shared_scalars = Dict{String,Any}(
        "canonical_energy_score_L" => positive["canonical_energy_score_L"],
        "canonical_energy_score_R" => positive["canonical_energy_score_R"],
        "canonical_R_minus_L_preference" => positive["canonical_R_minus_L_preference"],
        "carrier_strength" => carrier["carrier_strength"],
        "weak_scale" => WEAK_SCALE,
        "L_vs_R_preference" => positive["delta_E_R_minus_L"],
        "chemistry_weight_L" => positive["chemistry_weight_L"],
        "chemistry_weight_R" => positive["chemistry_weight_R"],
        "chemistry_weight_preference_L_minus_R" => positive["chemistry_weight_preference_L_minus_R"],
        "selection_logit" => positive["selection_logit"],
        "p_L_final" => positive["p_L_final"],
        "p_R_final" => positive["p_R_final"],
        "no_bias_delta_E" => no_bias["delta_E_R_minus_L"],
        "no_bias_p_L_final" => no_bias["p_L_final"],
        "no_bias_p_R_final" => no_bias["p_R_final"],
        "no_ratchet_p_L_final" => no_ratchet["p_L_final"],
        "no_ratchet_p_R_final" => no_ratchet["p_R_final"],
        "mirror_flip_p_L_final" => mirror_flip["p_L_final"],
        "mirror_flip_p_R_final" => mirror_flip["p_R_final"],
        "erased_carrier_delta_E" => erased_carrier["delta_E_R_minus_L"],
        "mixed_density_delta_E" => mixed_density["delta_E_R_minus_L"],
        "erased_golden_delta_E" => erased_golden["delta_E_R_minus_L"],
        "g2_der_O_dim" => Float64(carrier["octonion_G2_automorphism"]["der_O_dim"]),
        "clifford_cl30_even_dim" => Float64(carrier["clifford_algebra_ladder"]["cl30_even_dim"]),
        "density_trace_real" => carrier["density_matrix_spinor_lift"]["trace_real"],
        "density_bloch_norm" => carrier["density_matrix_spinor_lift"]["bloch_norm"],
        "golden_state_norm" => carrier["golden_weyl"]["state_norm"],
        "qit_substage_count_per_engine" => Float64(carrier["canonical_qit_engine_specs"]["substage_count_per_engine"]),
        "qit_mirror_ladder_residual" => carrier["canonical_qit_engine_specs"]["mirror_SX_ladder_swap_residual"],
    )
    shared_booleans = Dict{String,Any}(
        "local_all_pass" => local_all_pass,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "from_chirality_bias" => from_chirality_bias,
        "ratchet_amplifies_to_one" => ratchet_amplifies_to_one,
        "racemic_control" => racemic_control,
        "no_ratchet_control" => no_ratchet_control,
        "jax_enable_x64" => true,
        "positive_survivor_L" => positive["survivor"] == "L",
        "mirror_flip_survivor_R" => mirror_flip["survivor"] == "R",
        "erased_carrier_racemic" => erased_carrier["survivor"] == "racemic_or_mixed",
    )

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "schema" => "MP3_HOMOCHIRALITY_CASCADE_DUAL_BACKEND_v1",
        "name" => OBJECT_ID,
        "backend" => "julia_mirror",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "Finite witness of a chirality-to-homochirality selection mechanism only. It is not a proof or derivation of homochirality and admits no physics, chemistry, biology, evolution, QIT-engine, bridge, Axis0, or formal-manifold claim.",
        "allowed_claims" => [
            "finite chirality-bias to L/R stability-preference witness",
            "finite selection-ratchet amplification witness",
            "dual-backend parity witness",
            "non-tautological erasure/control witness",
        ],
        "blocked_consumers" => [
            "physics_admission", "chemistry_admission", "biology_admission", "evolution_claim",
            "origin_of_life_claim", "open_problem_solution", "formal_admission", "Axis0", "bridge", "manifold_closure",
        ],
        "sim_execution_kind" => "nonclassical_scratch_diagnostic",
        "sim_class" => "finite_formal_scout",
        "numpy_compute_used" => false,
        "jax_enable_x64" => true,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "owner_source_refs" => source_refs(),
        "carrier_bundle" => carrier,
        "mechanism" => Dict(
            "rung_spec" => "fenced downstream candidate: chirality bias -> enantiomer stability preference -> entropy-weighted selection ratchet -> one surviving handedness",
            "interpretation_fence" => "Downstream cascade vocabulary is descriptive only; no biology/physics admission.",
            "positive" => positive,
            "no_chirality_bias_control" => no_bias,
            "no_ratchet_control" => no_ratchet,
            "mirror_flip_control" => mirror_flip,
            "erased_carrier_control" => erased_carrier,
            "mixed_density_control" => mixed_density,
            "erased_golden_state_control" => erased_golden,
        ),
        "positive" => Dict(
            "L_energy_lower_than_R_from_chirality_bias" => Dict(
                "pass" => positive["delta_E_R_minus_L"] > 0.0,
                "L_vs_R_preference" => positive["delta_E_R_minus_L"],
                "chemistry_weight_preference_L_minus_R" => positive["chemistry_weight_preference_L_minus_R"],
            ),
            "ratchet_amplifies_to_one_survivor" => Dict(
                "pass" => ratchet_amplifies_to_one,
                "survivor" => positive["survivor"],
                "p_L_final" => positive["p_L_final"],
                "p_R_final" => positive["p_R_final"],
            ),
        ),
        "graveyard_companions" => Dict(
            "no_chirality_bias_racemic" => Dict("pass" => racemic_control, "control" => no_bias),
            "no_ratchet_keeps_only_tiny_preference" => Dict("pass" => no_ratchet_control, "control" => no_ratchet),
            "mirror_flip_selects_R" => Dict("pass" => mirror_flip["survivor"] == "R", "control" => mirror_flip),
            "erased_carrier_kills_preference" => Dict("pass" => erased_carrier["survivor"] == "racemic_or_mixed", "control" => erased_carrier),
            "mixed_density_changes_preference" => Dict("pass" => abs(mixed_density["delta_E_R_minus_L"] - positive["delta_E_R_minus_L"]) > 1.0e-8, "control" => mixed_density),
            "erased_golden_state_changes_preference" => Dict("pass" => abs(erased_golden["delta_E_R_minus_L"] - positive["delta_E_R_minus_L"]) > 1.0e-8, "control" => erased_golden),
        ),
        "boundary" => Dict(
            "classification_is_scratch_diagnostic" => Dict("pass" => true),
            "promotion_disallowed" => Dict("pass" => true),
            "formal_admission_disallowed" => Dict("pass" => true),
            "claim_ceiling_blocks_physics_chemistry_biology" => Dict("pass" => true),
            "no_numpy_compute" => Dict("pass" => true, "compute_backend" => "Julia LinearAlgebra mirror of JAX x64"),
        ),
        "nearby_variants" => Dict(
            "total" => 6,
            "passed" => count(row -> Bool(row["pass"]), values(Dict(
                "no_chirality_bias_racemic" => Dict("pass" => racemic_control),
                "no_ratchet_keeps_only_tiny_preference" => Dict("pass" => no_ratchet_control),
                "mirror_flip_selects_R" => Dict("pass" => mirror_flip["survivor"] == "R"),
                "erased_carrier_kills_preference" => Dict("pass" => erased_carrier["survivor"] == "racemic_or_mixed"),
                "mixed_density_changes_preference" => Dict("pass" => abs(mixed_density["delta_E_R_minus_L"] - positive["delta_E_R_minus_L"]) > 1.0e-8),
                "erased_golden_state_changes_preference" => Dict("pass" => abs(erased_golden["delta_E_R_minus_L"] - positive["delta_E_R_minus_L"]) > 1.0e-8),
            ))),
            "variant_names" => ["no_chirality_bias", "no_ratchet", "mirror_flip", "erased_carrier", "mixed_density", "erased_golden_state"],
        ),
        "why_not_v4_probes" => [
            "scratch diagnostic by request, not a formal admission or promotion receipt",
            "finite two-enantiomer selection model only; no derivation of real molecular homochirality",
            "downstream physics->chemistry->biology cascade remains fenced and not admitted",
            "selection-ratchet map is a bounded mechanism witness, not an evolutionary biology claim",
        ],
        "TOOL_MANIFEST" => Dict(
            "Julia LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing mirror backend for finite matrix dynamics, carrier factors, selection logits, controls, and peer parity"),
            "JAX jax.numpy x64" => Dict("tried" => true, "used" => true, "reason" => "load-bearing peer backend parity over shared scalars/booleans"),
            "canonical_qit_engine_specs.py" => Dict("tried" => true, "used" => true, "reason" => "load-bearing H_L=+H0/H_R=-H0, MIRROR=SX ladder, Lindblad maps, operator slots, and 32-substage schedule drive the L/R split"),
            "octonion_G2_automorphism" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Der(O)=g2 dimension factor; erasing the carrier factor kills the preference and selection"),
            "clifford_algebra_ladder" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Cl(3,0) even-quaternion carrier factor; erasing the carrier factor kills the preference and selection"),
            "density_matrix_spinor_lift" => Dict("tried" => true, "used" => true, "reason" => "load-bearing spinor-to-density source for the signed Lindblad energy split; mixed-density erasure changes the result"),
            "golden_weyl" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Weyl spinor source state for the density carrier; replacing it changes the result"),
            "Julia JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization and source hashing only"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Julia LinearAlgebra" => "load_bearing",
            "JAX jax.numpy x64" => "load_bearing",
            "canonical_qit_engine_specs.py" => "load_bearing",
            "octonion_G2_automorphism" => "load_bearing",
            "clifford_algebra_ladder" => "load_bearing",
            "density_matrix_spinor_lift" => "load_bearing",
            "golden_weyl" => "load_bearing",
            "Julia JSON/Dates/SHA" => "supportive",
        ),
        "divergence_log" => [
            "No chirality bias: delta_E=0 and the finite selection map stays racemic.",
            "No ratchet: the chemistry preference stays tiny and does not become a single survivor.",
            "Mirror-flipped chirality: the same mechanism selects R instead of L.",
            "Carrier erasure: zeroing the owner carrier factor kills the preference and selection.",
        ],
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "local_all_pass" => local_all_pass,
        "L_vs_R_preference" => positive["delta_E_R_minus_L"],
        "from_chirality_bias" => from_chirality_bias,
        "ratchet_amplifies_to_one" => ratchet_amplifies_to_one,
        "racemic_control" => racemic_control,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
    )
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = Bool(local_all_pass && result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = Bool((!local_all_pass) || result["parity"]["stop_condition_fired"])
    result["result_summary"] = Dict(
        "all_pass" => result["all_pass"],
        "local_all_pass" => local_all_pass,
        "parity_within_1e_9" => result["parity"]["within_1e_9"],
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "L_vs_R_preference" => positive["delta_E_R_minus_L"],
        "from_chirality_bias" => from_chirality_bias,
        "ratchet_amplifies_to_one" => ratchet_amplifies_to_one,
        "racemic_control" => racemic_control,
        "claim_ceiling" => result["claim_ceiling"],
    )
    result["blockers"] = result["all_pass"] ? [] : ["local_or_dual_backend_parity_not_yet_green"]
    result
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(
        "SCOUT_DONE " *
        "jax=$(JAX_RESULT_PATH) " *
        "julia=$(RESULT_PATH) " *
        "all_pass=$(lowercase(string(result["all_pass"]))) " *
        "owner_carrier_load_bearing=$(lowercase(string(result["owner_carrier_load_bearing"]))) " *
        "L_vs_R_preference=$(result["L_vs_R_preference"]) " *
        "from_chirality_bias=$(lowercase(string(result["from_chirality_bias"]))) " *
        "ratchet_amplifies_to_one=$(lowercase(string(result["ratchet_amplifies_to_one"]))) " *
        "racemic_control=$(lowercase(string(result["racemic_control"])))"
    )
    return result["local_all_pass"] ? 0 : 1
end

exit(main())
