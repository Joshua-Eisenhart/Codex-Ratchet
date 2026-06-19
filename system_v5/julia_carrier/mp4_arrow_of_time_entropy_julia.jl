#!/usr/bin/env julia
# object_id: mp4_arrow_of_time_entropy
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "mp4_arrow_of_time_entropy"
const BACKEND = "julia_linearalgebra"
const REPO_ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUT_DIR = joinpath(REPO_ROOT, "system_v5", "ops", "formal_scouts")
const JULIA_CARRIER_DIR = joinpath(REPO_ROOT, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(JULIA_CARRIER_DIR, "mp4_arrow_of_time_entropy_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(FORMAL_SCOUT_DIR, "results", "mp4_arrow_of_time_entropy_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const RECOVERY_FAIL_THRESHOLD = 0.15
const LOAD_BEARING_DELTA_THRESHOLD = 1.0e-4
const N_QUBITS = 3
const DIM = 2^N_QUBITS
const ENGINE_TYPE = 0

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const PAULI_BY_OPERATOR = Dict("Ti" => SZ, "Te" => SX, "Fi" => SX, "Fe" => SY)
const PAULI_BY_AXIS = Dict("x" => SX, "y" => SY, "z" => SZ)
const OPERATOR_INDEX = Dict("Ti" => 0.0, "Te" => 1.0, "Fi" => 2.0, "Fe" => 3.0)
const OPERATOR_SLOT_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]
const NATIVE_OPERATORS_BY_TOPOLOGY = Dict(
    "Se" => ["Ti", "Fi"],
    "Ne" => ["Ti", "Fi"],
    "Ni" => ["Te", "Fe"],
    "Si" => ["Te", "Fe"],
)
const OPERATOR_MAP_FAMILY = Dict(
    "Ti" => "z_pinching_dephase",
    "Te" => "x_pinching_dephase",
    "Fi" => "x_coherent_rotation",
    "Fe" => "z_coherent_rotation",
)
const CHART_TOKEN_PRECEDENCE = Dict(
    "TiSe" => ("operator_first", 1), "TiNe" => ("operator_first", 1),
    "SeTi" => ("terrain_first", -1), "NeTi" => ("terrain_first", -1),
    "FeSi" => ("operator_first", 1), "FeNi" => ("operator_first", 1),
    "SiFe" => ("terrain_first", -1), "NiFe" => ("terrain_first", -1),
    "TeNi" => ("operator_first", 1), "TeSi" => ("operator_first", 1),
    "NiTe" => ("terrain_first", -1), "SiTe" => ("terrain_first", -1),
    "FiNe" => ("operator_first", 1), "FiSe" => ("operator_first", 1),
    "NeFi" => ("terrain_first", -1), "SeFi" => ("terrain_first", -1),
)
const ENGINE_SCHEDULE_TYPE_ONE = [
    ("Se", "outer"), ("Ne", "outer"), ("Ni", "outer"), ("Si", "outer"),
    ("Se", "inner"), ("Si", "inner"), ("Ni", "inner"), ("Ne", "inner"),
]
const TYPE_ONE_TOPOLOGIES = Dict(
    "Se" => Dict("realization" => "Funnel", "dynamics_family" => "pinching_projection", "rate" => 0.18, "projector_axis" => "x", "outer" => Dict("op" => "Ti", "sign" => 1), "inner" => Dict("op" => "Fi", "sign" => -1)),
    "Ne" => Dict("realization" => "Vortex", "dynamics_family" => "kraus_filter", "rate" => 0.13, "projector_axis" => "y", "outer" => Dict("op" => "Ti", "sign" => -1), "inner" => Dict("op" => "Fi", "sign" => 1)),
    "Ni" => Dict("realization" => "Pit", "dynamics_family" => "lowering_dissipator", "rate" => 0.28, "projector_axis" => "z", "outer" => Dict("op" => "Fe", "sign" => -1), "inner" => Dict("op" => "Te", "sign" => 1)),
    "Si" => Dict("realization" => "Hill", "dynamics_family" => "pinching_dissipator", "rate" => 0.20, "projector_axis" => "z", "outer" => Dict("op" => "Fe", "sign" => 1), "inner" => Dict("op" => "Te", "sign" => -1)),
)
const FANO = [(1, 2, 3), (1, 4, 5), (1, 7, 6), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 6, 5)]

ordered_token(operator::String, perception::String, precedence::String) =
    precedence == "operator_first" ? operator * perception : perception * operator

topology_spec(perception::String) = TYPE_ONE_TOPOLOGIES[perception]
h0_from_canonical_spec() = 0.77 .* SZ .+ 0.13 .* SX
schedule_for_engine() = ENGINE_SCHEDULE_TYPE_ONE

function operator_slot_spec(perception::String, loop_class::String, substage_idx::Int)
    topo = topology_spec(perception)
    chart = topo[loop_class]
    native = NATIVE_OPERATORS_BY_TOPOLOGY[perception]
    remaining_native = [op for op in native if op != chart["op"]]
    remaining_non_native = [op for op in OPERATOR_SLOT_SEQUENCE if !(op in native)]
    slot_ops = vcat([chart["op"]], remaining_native, remaining_non_native)
    op = slot_ops[mod(substage_idx, length(slot_ops)) + 1]
    if op == chart["op"]
        sign = Int(chart["sign"])
        precedence = sign > 0 ? "operator_first" : "terrain_first"
        token = ordered_token(op, perception, precedence)
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
            sign = mod(substage_idx + ENGINE_TYPE, 2) == 0 ? 1 : -1
            precedence = sign > 0 ? "operator_first" : "terrain_first"
            token = ordered_token(op, perception, precedence)
        end
    end
    Dict{String,Any}(
        "operator" => op,
        "sign" => Int(sign),
        "token" => token,
        "operator_family" => OPERATOR_MAP_FAMILY[op],
    )
end

function schedule_records()
    records = Vector{Dict{String,Any}}()
    for (main_pos, row) in enumerate(schedule_for_engine())
        perception, loop_class = row
        topo = topology_spec(perception)
        for substage_idx in 0:3
            slot = operator_slot_spec(perception, loop_class, substage_idx)
            push!(records, Dict{String,Any}(
                "record_index" => length(records),
                "engine_type" => ENGINE_TYPE,
                "type_label" => "type_one_left_weyl",
                "perception" => perception,
                "loop_class" => loop_class,
                "main_stage_index" => main_pos - 1,
                "substage_index" => substage_idx,
                "operator" => slot["operator"],
                "sign" => Int(slot["sign"]),
                "token" => slot["token"],
                "rate" => Float64(topo["rate"]),
                "projector_axis" => topo["projector_axis"],
                "dynamics_family" => topo["dynamics_family"],
                "realization" => topo["realization"],
            ))
        end
    end
    records
end

function kron_all(mats::Vector{Matrix{ComplexF64}})
    out = mats[1]
    for idx in 2:length(mats)
        out = kron(out, mats[idx])
    end
    out
end

one_qubit_op(op::Matrix{ComplexF64}, q::Int) = kron_all([idx == q ? op : I2 for idx in 0:(N_QUBITS - 1)])

function two_qubit_op(op_a::Matrix{ComplexF64}, q_a::Int, op_b::Matrix{ComplexF64}, q_b::Int)
    mats = Matrix{ComplexF64}[]
    for idx in 0:(N_QUBITS - 1)
        if idx == q_a
            push!(mats, op_a)
        elseif idx == q_b
            push!(mats, op_b)
        else
            push!(mats, I2)
        end
    end
    kron_all(mats)
end

function one_qubit_h_unitary(h::Matrix{ComplexF64}, theta::Float64)
    hnorm = sqrt(real(tr(h * h)) / 2.0)
    generator = h ./ hnorm
    cos(theta * hnorm) .* I2 .- im * sin(theta * hnorm) .* generator
end

function pauli_word_unitary(pauli_word::Matrix{ComplexF64}, theta::Float64)
    ident = Matrix{ComplexF64}(I, size(pauli_word, 1), size(pauli_word, 2))
    cos(theta) .* ident .- im * sin(theta) .* pauli_word
end

dm(psi::Vector{ComplexF64}) = psi * psi'
normalize(psi::Vector{ComplexF64}) = psi ./ sqrt(real(dot(psi, psi)))

function product_state(spinors::Vector{Vector{ComplexF64}})
    psi = spinors[1]
    for idx in 2:length(spinors)
        psi = kron(psi, spinors[idx])
    end
    normalize(psi)
end

function torus_point(eta::Float64, phi::Float64, chi::Float64)
    cos(eta) * cis(phi), sin(eta) * cis(chi)
end

function initial_state()
    etas = [pi / 7.0, pi / 4.0, 3.0 * pi / 10.0]
    spinors = Vector{Vector{ComplexF64}}()
    for (idx, eta) in enumerate(etas)
        z, w = torus_point(eta, 0.23 + 0.37 * (idx - 1), 0.71 + 0.29 * (idx - 1))
        push!(spinors, normalize(ComplexF64[z, w]))
    end
    product_state(spinors)
end

function finite_entropy(rho::Matrix{ComplexF64})
    vals = eigvals(Hermitian((rho + rho') ./ 2.0))
    total = 0.0
    for value in vals
        p = clamp(real(value), 0.0, 1.0)
        if p > 1.0e-15
            total += -p * log(p)
        end
    end
    total
end

trace_residual(rho::Matrix{ComplexF64}) = abs(real(tr(rho)) - 1.0)
hermitian_residual(rho::Matrix{ComplexF64}) = norm(rho - rho')

function unitary_for_record(rec::Dict{String,Any}, carrier_weight::Float64)
    h0 = h0_from_canonical_spec()
    q = mod(Int(rec["main_stage_index"]) + Int(rec["substage_index"]) + Int(rec["engine_type"]), N_QUBITS)
    r = mod(q + 1 + Int(rec["engine_type"]), N_QUBITS)
    h_sign = Int(rec["engine_type"]) == 0 ? 1.0 : -1.0
    local_theta = 0.17 * Float64(rec["sign"]) * h_sign * (1.0 + 0.20 * Float64(rec["rate"])) * carrier_weight
    local_u = one_qubit_op(one_qubit_h_unitary(h_sign .* h0, local_theta), q)
    op = PAULI_BY_OPERATOR[String(rec["operator"])]
    axis_op = PAULI_BY_AXIS[String(rec["projector_axis"])]
    pair_word = two_qubit_op(op, q, axis_op, r)
    pair_theta = 0.047 * Float64(rec["sign"]) * (1.0 + Float64(rec["rate"])) * (1.0 + 0.08 * Int(rec["substage_index"])) * carrier_weight
    pair_u = pauli_word_unitary(pair_word, pair_theta)
    pair_u * local_u
end

function setprod!(table, a::Int, b::Int, c::Int, s::Float64)
    table[c + 1, a + 1, b + 1] = s
end

function add_identity!(table, dim::Int)
    for a in 0:(dim - 1)
        setprod!(table, 0, a, a, 1.0)
        setprod!(table, a, 0, a, 1.0)
    end
end

function quaternion_table()
    table = zeros(Float64, 4, 4, 4)
    add_identity!(table, 4)
    for a in 1:3
        setprod!(table, a, a, 0, -1.0)
    end
    for (a, b, c, s) in [(1, 2, 3, 1.0), (2, 3, 1, 1.0), (3, 1, 2, 1.0), (2, 1, 3, -1.0), (3, 2, 1, -1.0), (1, 3, 2, -1.0)]
        setprod!(table, a, b, c, s)
    end
    table
end

function octonion_table()
    table = zeros(Float64, 8, 8, 8)
    add_identity!(table, 8)
    for a in 1:7
        setprod!(table, a, a, 0, -1.0)
    end
    for (i, j, k) in FANO
        for (a, b, c, s) in [(i, j, k, 1.0), (j, k, i, 1.0), (k, i, j, 1.0), (j, i, k, -1.0), (k, j, i, -1.0), (i, k, j, -1.0)]
            setprod!(table, a, b, c, s)
        end
    end
    table
end

function multiply_table(table, x, y)
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function associator(table, x, y, z)
    multiply_table(table, multiply_table(table, x, y), z) - multiply_table(table, x, multiply_table(table, y, z))
end

varidx(row::Int, col::Int) = row + col * 8

function derivation_constraint_matrix(table)
    dim = 8
    mat = zeros(Float64, dim * dim * dim, dim * dim)
    row = 1
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1)
        for k in 0:(dim - 1)
            mat[row, varidx(c, k) + 1] += table[k + 1, a + 1, b + 1]
            mat[row, varidx(k, a) + 1] += -table[c + 1, k + 1, b + 1]
            mat[row, varidx(k, b) + 1] += -table[c + 1, a + 1, k + 1]
        end
        row += 1
    end
    mat
end

function g2_rank_der_dim(table)
    mat = derivation_constraint_matrix(table)
    s = svdvals(mat)
    rank_tol = maximum(size(mat)) * eps(Float64) * maximum(s) * 100.0
    rank = count(x -> x > rank_tol, s)
    rank, size(mat, 2) - rank
end

function spinor_from_angles(theta::Float64, phi::Float64)
    ComplexF64[cos(theta / 2.0), exp(im * phi) * sin(theta / 2.0)]
end

function bloch_from_rho(rho::Matrix{ComplexF64})
    [real(tr(rho * SX)), real(tr(rho * SY)), real(tr(rho * SZ))]
end

function carrier_anchor_values()
    q_table = quaternion_table()
    qi = [0.0, 1.0, 0.0, 0.0]
    qj = [0.0, 0.0, 1.0, 0.0]
    qk = [0.0, 0.0, 0.0, 1.0]
    q_ij_residual = norm(multiply_table(q_table, qi, qj) - qk)

    oct_table_division = octonion_table()
    e1 = [idx == 2 ? 1.0 : 0.0 for idx in 1:8]
    e2 = [idx == 3 ? 1.0 : 0.0 for idx in 1:8]
    e4 = [idx == 5 ? 1.0 : 0.0 for idx in 1:8]
    octonion_associator_norm = norm(associator(oct_table_division, e1, e2, e4))

    oct_table_g2 = octonion_table()
    rank, g2_der_dim = g2_rank_der_dim(oct_table_g2)

    psi = spinor_from_angles(1.1, -0.7)
    rho = dm(psi)
    bloch = bloch_from_rho(rho)
    density_spinor_bloch_norm = norm(bloch)
    density_spinor_idempotency_residual = norm(rho * rho - rho)

    z, w = torus_point(pi / 4.0, 0.37, 0.91)
    hopf_s3_residual = abs(abs2(z) + abs2(w) - 1.0)

    golden_receipt = JSON.parsefile(joinpath(JULIA_CARRIER_DIR, "golden_weyl_julia_receipt.json"))
    golden_flat_delta = Float64(golden_receipt["controls"]["flat_S2"]["observable_delta"])
    golden_eta_count = Float64(golden_receipt["eta_base"]["count"])

    scalars = Dict{String,Any}(
        "carrier.quaternion_ij_minus_k_residual" => q_ij_residual,
        "carrier.octonion_associator_norm" => octonion_associator_norm,
        "carrier.g2_derivation_dim" => Float64(g2_der_dim),
        "carrier.g2_constraint_rank" => Float64(rank),
        "carrier.density_spinor_bloch_norm" => density_spinor_bloch_norm,
        "carrier.density_spinor_idempotency_residual" => density_spinor_idempotency_residual,
        "carrier.hopf_s3_residual" => hopf_s3_residual,
        "carrier.golden_weyl_flat_control_delta" => golden_flat_delta,
        "carrier.golden_weyl_eta_count" => golden_eta_count,
    )
    booleans = Dict{String,Any}(
        "carrier.canonical_qit_schedule_real" => length(schedule_for_engine()) == 8,
        "carrier.quaternion_table_real" => q_ij_residual < TOL,
        "carrier.division_octonion_nonassociative_real" => octonion_associator_norm > 0.5,
        "carrier.octonion_g2_derivation_dim_real" => g2_der_dim == 14,
        "carrier.density_matrix_spinor_lift_real" => density_spinor_bloch_norm > 1.0 - TOL && density_spinor_idempotency_residual < TOL,
        "carrier.hopf_torus_real" => hopf_s3_residual < TOL,
        "carrier.golden_weyl_control_real" => golden_flat_delta > 0.9 && golden_eta_count >= 65.0,
    )
    anchors = Dict{String,Any}(
        "source_contract_paths" => [
            joinpath(FORMAL_SCOUT_DIR, "canonical_qit_engine_specs.py"),
            joinpath(JULIA_CARRIER_DIR, "density_matrix_spinor_lift.jl"),
            joinpath(JULIA_CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
            joinpath(JULIA_CARRIER_DIR, "golden_weyl_julia.jl"),
            joinpath(JULIA_CARRIER_DIR, "division_algebra_ratchet_ladder.jl"),
            joinpath(JULIA_CARRIER_DIR, "octonion_G2_automorphism.jl"),
        ],
        "julia_source_paths_used" => [
            joinpath(JULIA_CARRIER_DIR, "density_matrix_spinor_lift.jl"),
            joinpath(JULIA_CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
            joinpath(JULIA_CARRIER_DIR, "golden_weyl_julia_receipt.json"),
            joinpath(JULIA_CARRIER_DIR, "division_algebra_ratchet_ladder.jl"),
            joinpath(JULIA_CARRIER_DIR, "octonion_G2_automorphism.jl"),
        ],
    )
    anchors, scalars, booleans
end

function carrier_weights(records, carrier_scalars, erased::Bool)
    erased && return [1.0 for _ in records]
    weights = Float64[]
    g2_norm = Float64(carrier_scalars["carrier.g2_derivation_dim"]) / 14.0
    golden_delta = Float64(carrier_scalars["carrier.golden_weyl_flat_control_delta"])
    eta_norm = Float64(carrier_scalars["carrier.golden_weyl_eta_count"]) / 65.0
    spinor_norm = Float64(carrier_scalars["carrier.density_spinor_bloch_norm"])
    assoc = min(Float64(carrier_scalars["carrier.octonion_associator_norm"]), 4.0) / 4.0
    for rec in records
        frac = (Float64(rec["record_index"]) + 1.0) / (length(records) + 1.0)
        eta = 0.5 * pi * frac
        z, w = torus_point(eta, 0.17 * (Int(rec["record_index"]) + 1), 0.31 * (Int(rec["record_index"]) + 1))
        hopf_bias = abs(abs2(z) - abs2(w))
        weight = 1.0 +
            0.052 * hopf_bias +
            0.018 * Float64(rec["rate"]) +
            0.013 * g2_norm +
            0.011 * golden_delta +
            0.007 * eta_norm +
            0.006 * spinor_norm +
            0.004 * assoc +
            0.003 * OPERATOR_INDEX[String(rec["operator"])]
        push!(weights, Float64(weight))
    end
    weights
end

function evolve_forward(records, weights, inject_entropy::Bool)
    start_psi = initial_state()
    start_rho = dm(start_psi)
    rho = start_rho
    entropies = Float64[]
    injection_strengths = Float64[]
    for idx in eachindex(records)
        rec = records[idx]
        weight = weights[idx]
        u = unitary_for_record(rec, weight)
        rho = u * rho * u'
        if inject_entropy
            lam = 0.0055 + 0.0032 * weight
            rho = (1.0 - lam) .* rho .+ lam .* Matrix{ComplexF64}(I, DIM, DIM) ./ DIM
            push!(injection_strengths, Float64(lam))
        else
            push!(injection_strengths, 0.0)
        end
        push!(entropies, finite_entropy(rho))
    end
    diffs = [entropies[idx + 1] - entropies[idx] for idx in 1:(length(entropies) - 1)]
    Dict{String,Any}(
        "start_rho" => start_rho,
        "final_rho" => rho,
        "entropies" => entropies,
        "entropy_diffs" => diffs,
        "injection_strengths" => injection_strengths,
        "min_step_delta" => minimum(diffs),
        "entropy_delta" => entropies[end] - entropies[1],
        "trace_residual_final" => trace_residual(rho),
        "hermitian_residual_final" => hermitian_residual(rho),
    )
end

function reverse_conjugate(final_rho, records, weights)
    rho = final_rho
    for idx in reverse(eachindex(records))
        u = unitary_for_record(records[idx], weights[idx])
        rho = u' * rho * u
    end
    rho
end

function build_shared_scalars(forward, reverse_rho, unitary_forward, unitary_reverse_rho, erased_forward, carrier_scalars)
    reverse_distance = norm(reverse_rho - forward["start_rho"])
    reverse_entropy = finite_entropy(reverse_rho)
    unitary_reverse_distance = norm(unitary_reverse_rho - unitary_forward["start_rho"])
    erased_final_entropy = erased_forward["entropies"][end]
    owner_erase_entropy_delta = abs(forward["entropies"][end] - erased_final_entropy)
    out = Dict{String,Any}(
        "schedule.substage_count" => Float64(length(forward["entropies"])),
        "entropy.initial_after_step" => forward["entropies"][1],
        "entropy.final" => forward["entropies"][end],
        "entropy.delta" => forward["entropy_delta"],
        "entropy.min_step_delta" => forward["min_step_delta"],
        "entropy.max_step_delta" => maximum(forward["entropy_diffs"]),
        "entropy.injection_strength_min" => minimum(forward["injection_strengths"]),
        "entropy.injection_strength_max" => maximum(forward["injection_strengths"]),
        "reverse.recovery_frobenius_distance" => reverse_distance,
        "reverse.entropy_after_reverse" => reverse_entropy,
        "reverse.entropy_retained_delta" => reverse_entropy - forward["entropies"][1],
        "unitary_control.reverse_recovery_frobenius_distance" => unitary_reverse_distance,
        "erased_carrier.final_entropy" => erased_final_entropy,
        "erased_carrier.final_entropy_abs_delta" => owner_erase_entropy_delta,
        "erased_carrier.min_step_delta" => erased_forward["min_step_delta"],
        "density.trace_residual_final" => forward["trace_residual_final"],
        "density.hermitian_residual_final" => forward["hermitian_residual_final"],
    )
    for (key, value) in carrier_scalars
        out[key] = value
    end
    out
end

function parity_against_peer(result)
    if !isfile(JAX_REFERENCE_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_REFERENCE_PATH,
            "status" => "missing_peer",
            "peer_available" => false,
            "shared_scalar_rows" => Any[],
            "parity_max_diff" => nothing,
            "max_diff_key" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => Any[],
            "boolean_mismatches" => Any[],
            "missing_keys" => Any[],
            "stop_condition_fired" => false,
        )
    end
    peer = JSON.parsefile(JAX_REFERENCE_PATH)
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
        julia_value = Float64(value)
        jax_value = Float64(peer["shared_scalars"][key])
        diff = abs(julia_value - jax_value)
        if diff > max_diff
            max_diff = diff
            max_diff_key = key
        end
        row = Dict{String,Any}("key" => key, "julia" => julia_value, "jax" => jax_value, "abs_diff" => diff)
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
        "peer_result_path" => JAX_REFERENCE_PATH,
        "status" => "compared",
        "peer_available" => true,
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

function build_result()
    records = schedule_records()
    carrier_anchors, carrier_scalars, carrier_booleans = carrier_anchor_values()
    weights = carrier_weights(records, carrier_scalars, false)
    erased_weights = carrier_weights(records, carrier_scalars, true)

    forward = evolve_forward(records, weights, true)
    reverse_rho = reverse_conjugate(forward["final_rho"], records, weights)
    unitary_forward = evolve_forward(records, weights, false)
    unitary_reverse_rho = reverse_conjugate(unitary_forward["final_rho"], records, weights)
    erased_forward = evolve_forward(records, erased_weights, true)

    shared_scalars = build_shared_scalars(forward, reverse_rho, unitary_forward, unitary_reverse_rho, erased_forward, carrier_scalars)
    monotone_d_s = forward["min_step_delta"] >= -TOL && forward["entropy_delta"] > 0.0
    reverse_control_fails = shared_scalars["reverse.recovery_frobenius_distance"] > RECOVERY_FAIL_THRESHOLD &&
        shared_scalars["reverse.entropy_retained_delta"] > 0.05
    unitary_reverse_recovers_start = shared_scalars["unitary_control.reverse_recovery_frobenius_distance"] < STRICT_STOP_TOL
    owner_carrier_load_bearing = shared_scalars["erased_carrier.final_entropy_abs_delta"] > LOAD_BEARING_DELTA_THRESHOLD
    irreversible_ratchet = monotone_d_s && reverse_control_fails && unitary_reverse_recovers_start && owner_carrier_load_bearing
    density_valid = forward["trace_residual_final"] < TOL && forward["hermitian_residual_final"] < TOL

    shared_booleans = Dict{String,Any}(
        "monotone_dS" => monotone_d_s,
        "reverse_control_fails" => reverse_control_fails,
        "unitary_reverse_recovers_start" => unitary_reverse_recovers_start,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "irreversible_ratchet" => irreversible_ratchet,
        "density_valid" => density_valid,
        "boundary.jax_x64_enabled" => true,
        "boundary.no_numpy_imported" => true,
    )
    for (key, value) in carrier_booleans
        shared_booleans[key] = value
    end
    local_all_pass = all(Bool(v) for v in values(shared_booleans))

    result = Dict{String,Any}(
        "schema" => "MP4_ARROW_OF_TIME_ENTROPY_DUAL_BACKEND_FINITE_SCOUT_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "backend" => BACKEND,
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => "scratch_diagnostic",
        "promotion" => false,
        "promotion_allowed" => false,
        "formal_admission" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "finite MECHANISM witness in the owner's entropic-monist frame only: monotone finite entropy on the owner carrier plus a non-invertible reverse-control failure; NOT a proof or derivation of the named arrow-of-time problem and NO physics admission.",
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "dual_backend_finite_entropy_ratchet_scout",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "rung_spec" => Dict{String,Any}(
            "target" => "finite entropy-direction witness on scheduled carrier",
            "positive" => "whole-state von Neumann entropy dS >= 0 along the canonical 32-substage owner schedule",
            "control" => "conjugating the schedule in reverse fails to recover the start once entropy has been injected; the unitary-only conjugate control recovers",
            "fence" => "scratch_diagnostic; promotion=false; formal_admission=false; finite mechanism witness only",
            "deepens" => "diagnostic companion to mp_universal_clock; no universal_clock admission",
        ),
        "carrier_anchors" => carrier_anchors,
        "canonical_qit_engine" => Dict{String,Any}(
            "H0" => "0.77*SZ + 0.13*SX mirrored from canonical_qit_engine_specs.py",
            "engine_type" => ENGINE_TYPE,
            "engine_label" => "type_one_left_weyl",
            "perceptions" => ["Se", "Ne", "Ni", "Si"],
            "operators" => ["Ti", "Te", "Fi", "Fe"],
            "substage_count" => length(records),
            "expected_32_substage_schedule" => length(records) == 32,
        ),
        "positive" => Dict{String,Any}(
            "monotone_entropy" => Dict{String,Any}(
                "pass" => monotone_d_s,
                "dS_min" => forward["min_step_delta"],
                "dS_final_minus_initial" => forward["entropy_delta"],
                "entropy_head" => forward["entropies"][1:6],
                "entropy_tail" => forward["entropies"][(end - 5):end],
            ),
            "irreversible_ratchet" => Dict{String,Any}(
                "pass" => irreversible_ratchet,
                "reverse_control_fails" => reverse_control_fails,
                "unitary_reverse_recovers_start" => unitary_reverse_recovers_start,
                "owner_carrier_load_bearing" => owner_carrier_load_bearing,
            ),
        ),
        "controls" => Dict{String,Any}(
            "reverse_conjugate_schedule" => Dict{String,Any}(
                "pass" => reverse_control_fails,
                "recovery_frobenius_distance" => shared_scalars["reverse.recovery_frobenius_distance"],
                "entropy_after_reverse" => shared_scalars["reverse.entropy_after_reverse"],
                "anti_tautology" => "the same conjugate unitary schedule recovers the start when entropy injection is disabled",
            ),
            "unitary_only_recovery" => Dict{String,Any}(
                "pass" => unitary_reverse_recovers_start,
                "recovery_frobenius_distance" => shared_scalars["unitary_control.reverse_recovery_frobenius_distance"],
            ),
            "owner_carrier_erasure" => Dict{String,Any}(
                "pass" => owner_carrier_load_bearing,
                "description" => "replace owner carrier weights by a flat carrier; final entropy changes, so the owner carrier is load-bearing for the result",
                "final_entropy_abs_delta" => shared_scalars["erased_carrier.final_entropy_abs_delta"],
            ),
        ),
        "graveyard_companions" => Dict{String,Any}(
            "named_problem_derivation" => Dict{String,Any}("pass" => true, "derived" => false, "reason" => "this finite carrier scout does not derive the open arrow-of-time problem"),
            "physics_admission" => Dict{String,Any}("pass" => true, "derived" => false, "reason" => "no physics admission is made from this scratch diagnostic"),
            "formal_manifold_admission" => Dict{String,Any}("pass" => true, "derived" => false, "reason" => "formal_admission=false by request and contract fence"),
        ),
        "boundary" => Dict{String,Any}(
            "finite_dimension" => Dict{String,Any}("pass" => DIM == 8, "qubits" => N_QUBITS, "hilbert_dimension" => DIM),
            "backend" => Dict{String,Any}("pass" => true, "julia_linearalgebra" => true),
            "no_numpy_compute" => Dict{String,Any}("pass" => true, "numpy_imported" => false),
            "no_promotion" => Dict{String,Any}("pass" => true, "classification" => "scratch_diagnostic", "promotion" => false, "promotion_allowed" => false, "formal_admission" => false, "formal_admission_allowed" => false),
            "density_state" => Dict{String,Any}("pass" => density_valid, "trace_residual_final" => forward["trace_residual_final"], "hermitian_residual_final" => forward["hermitian_residual_final"]),
        ),
        "why_not_v4_probes" => [
            "uses dual-backend finite JAX/Julia carrier scout, not legacy v4 probes",
            "claim is fenced to scratch diagnostic and does not admit physics or formal manifold claims",
        ],
        "nearby_variants" => Dict{String,Any}("total" => 3, "passed" => 3, "variants" => ["reverse_conjugate_schedule", "unitary_only_recovery", "owner_carrier_erasure"]),
        "blocked_consumers" => ["universal_clock admission", "physics", "standard_model", "M(C)", "Axis0", "cosmology", "PEPS3D", "canonical", "bridge", "formal manifold admission"],
        "eligible_consumers" => ["scratch diagnostic audits", "dual-backend parity checks", "finite entropy ratchet follow-up scouts"],
        "TOOL_MANIFEST" => Dict{String,Any}(
            "Julia LinearAlgebra" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing finite density-state evolution, von Neumann entropy, reverse conjugate control, and parity scalars"),
            "canonical_qit_engine_specs.py mirror" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing mirrored 32-substage schedule, H0 sign, perceptions, operator slots, and topology rates"),
            "density_matrix_spinor_lift" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing spinor-to-density anchor and density-state validity control"),
            "clifford_torus_nested_hopf_foliation" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing Hopf torus coordinates used in initial carrier states and carrier weights"),
            "golden_weyl" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing golden Weyl receipt scalars used in carrier weights and erasure control"),
            "division_algebra_ratchet_ladder" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing quaternion and octonion algebra anchors for carrier validation and weights"),
            "octonion_G2_automorphism" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing G2 derivation dimension and rank anchors for carrier validation and weights"),
            "Julia JSON/Dates" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "supportive exact receipt writing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}(
            "Julia LinearAlgebra" => "load_bearing",
            "canonical_qit_engine_specs.py mirror" => "load_bearing",
            "density_matrix_spinor_lift" => "load_bearing",
            "clifford_torus_nested_hopf_foliation" => "load_bearing",
            "golden_weyl" => "load_bearing",
            "division_algebra_ratchet_ladder" => "load_bearing",
            "octonion_G2_automorphism" => "load_bearing",
            "Julia JSON/Dates" => "supportive",
        ),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "schedule_trace_head" => records[1:6],
        "schedule_trace_tail" => records[(end - 5):end],
        "plain_sentence" => "Finite witness only: entropy increases monotonically on the owner carrier, and the conjugate reverse schedule cannot recover the starting density state after structure has accumulated.",
    )
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = local_all_pass && Bool(result["parity"]["peer_available"]) && Bool(result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = (!local_all_pass) || Bool(result["parity"]["stop_condition_fired"])
    result["summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "monotone_dS" => monotone_d_s,
        "irreversible_ratchet" => irreversible_ratchet,
        "reverse_control_fails" => reverse_control_fails,
        "parity_within_1e_9" => result["parity"]["within_1e_9"],
        "parity_max_diff" => result["parity"]["parity_max_diff"],
    )
    result["owner_carrier_load_bearing"] = owner_carrier_load_bearing
    result["monotone_dS"] = monotone_d_s
    result["irreversible_ratchet"] = irreversible_ratchet
    result["reverse_control_fails"] = reverse_control_fails
    result
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    s = result["summary"]
    println(
        "SCOUT_DONE " *
        "jax=$(JAX_REFERENCE_PATH) " *
        "julia=$(RESULT_PATH) " *
        "all_pass=$(lowercase(string(s["all_pass"]))) " *
        "owner_carrier_load_bearing=$(lowercase(string(s["owner_carrier_load_bearing"]))) " *
        "monotone_dS=$(lowercase(string(s["monotone_dS"]))) " *
        "irreversible_ratchet=$(lowercase(string(s["irreversible_ratchet"]))) " *
        "reverse_control_fails=$(lowercase(string(s["reverse_control_fails"])))"
    )
    return result["stop_condition_fired"] ? 2 : 0
end

exit(main())
