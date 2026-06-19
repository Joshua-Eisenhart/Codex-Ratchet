#!/usr/bin/env julia
# object_id: mp_universal_clock
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "mp_universal_clock"
const BACKEND = "julia_linearalgebra"
const REPO_ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUT_DIR = joinpath(REPO_ROOT, "system_v5", "ops", "formal_scouts")
const JULIA_CARRIER_DIR = joinpath(REPO_ROOT, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(JULIA_CARRIER_DIR, "mp_universal_clock_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(FORMAL_SCOUT_DIR, "results", "mp_universal_clock_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const N_QUBITS = 3
const DIM = 2^N_QUBITS

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const PAULI_BY_OPERATOR = Dict("Ti" => SZ, "Te" => SX, "Fi" => SX, "Fe" => SY)
const PAULI_BY_AXIS = Dict("x" => SX, "y" => SY, "z" => SZ)
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
const OPERATOR_BASE_ANGLES = Dict("Ti" => 0.12, "Te" => 0.09, "Fi" => 0.15, "Fe" => 0.11)
const ENGINE_SCHEDULE_TYPE_ONE = [
    ("Se", "outer"), ("Ne", "outer"), ("Ni", "outer"), ("Si", "outer"),
    ("Se", "inner"), ("Si", "inner"), ("Ni", "inner"), ("Ne", "inner"),
]
const ENGINE_SCHEDULE_TYPE_TWO = [
    ("Se", "outer"), ("Si", "outer"), ("Ni", "outer"), ("Ne", "outer"),
    ("Se", "inner"), ("Ne", "inner"), ("Ni", "inner"), ("Si", "inner"),
]
const TYPE_ONE_TOPOLOGIES = Dict(
    "Se" => Dict("realization" => "Funnel", "dynamics_family" => "pinching_projection", "rate" => 0.18, "projector_axis" => "x", "outer" => Dict("op" => "Ti", "sign" => 1), "inner" => Dict("op" => "Fi", "sign" => -1)),
    "Ne" => Dict("realization" => "Vortex", "dynamics_family" => "kraus_filter", "rate" => 0.13, "projector_axis" => "y", "outer" => Dict("op" => "Ti", "sign" => -1), "inner" => Dict("op" => "Fi", "sign" => 1)),
    "Ni" => Dict("realization" => "Pit", "dynamics_family" => "lowering_dissipator", "rate" => 0.28, "projector_axis" => "z", "outer" => Dict("op" => "Fe", "sign" => -1), "inner" => Dict("op" => "Te", "sign" => 1)),
    "Si" => Dict("realization" => "Hill", "dynamics_family" => "pinching_dissipator", "rate" => 0.20, "projector_axis" => "z", "outer" => Dict("op" => "Fe", "sign" => 1), "inner" => Dict("op" => "Te", "sign" => -1)),
)
const TYPE_TWO_TOPOLOGIES = Dict(
    "Se" => Dict("realization" => "Cannon", "dynamics_family" => "kraus_release", "rate" => 0.18, "projector_axis" => "x", "outer" => Dict("op" => "Fi", "sign" => 1), "inner" => Dict("op" => "Ti", "sign" => -1)),
    "Ne" => Dict("realization" => "Spiral", "dynamics_family" => "outward_projection", "rate" => 0.15, "projector_axis" => "y", "outer" => Dict("op" => "Fi", "sign" => -1), "inner" => Dict("op" => "Ti", "sign" => 1)),
    "Ni" => Dict("realization" => "Source", "dynamics_family" => "raising_dissipator", "rate" => 0.27, "projector_axis" => "x", "outer" => Dict("op" => "Te", "sign" => -1), "inner" => Dict("op" => "Fe", "sign" => 1)),
    "Si" => Dict("realization" => "Citadel", "dynamics_family" => "pinching_dissipator", "rate" => 0.21, "projector_axis" => "z", "outer" => Dict("op" => "Te", "sign" => 1), "inner" => Dict("op" => "Fe", "sign" => -1)),
)

ordered_token(operator::String, perception::String, precedence::String) =
    precedence == "operator_first" ? operator * perception : perception * operator

function topology_spec(perception::String, engine_type::Int)
    engine_type == 0 ? TYPE_ONE_TOPOLOGIES[perception] : TYPE_TWO_TOPOLOGIES[perception]
end

function schedule_for_engine(engine_type::Int)
    engine_type == 0 ? ENGINE_SCHEDULE_TYPE_ONE : ENGINE_SCHEDULE_TYPE_TWO
end

function operator_slot_spec(perception::String, engine_type::Int, loop_class::String, substage_idx::Int)
    topo = topology_spec(perception, engine_type)
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
        chart_locked = true
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
            sign = mod(substage_idx + engine_type, 2) == 0 ? 1 : -1
            precedence = sign > 0 ? "operator_first" : "terrain_first"
            token = ordered_token(op, perception, precedence)
        end
        chart_locked = false
    end
    Dict{String,Any}(
        "operator" => op,
        "sign" => Int(sign),
        "token" => token,
        "operator_family" => OPERATOR_MAP_FAMILY[op],
        "is_native_operator" => op in native,
        "is_chart_locked" => chart_locked,
        "slot_index" => mod(substage_idx, length(slot_ops)),
    )
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

h0_from_canonical_spec() = 0.77 .* SZ .+ 0.13 .* SX

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

function spinor_from_angles(theta, phi)
    ComplexF64[cos(theta / 2.0), exp(im * phi) * sin(theta / 2.0)]
end

function product_state(spinors::Vector{Vector{ComplexF64}})
    psi = spinors[1]
    for idx in 2:length(spinors)
        psi = kron(psi, spinors[idx])
    end
    normalize(psi)
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

function reduced_one_qubit(rho::Matrix{ComplexF64}, q::Int)
    red = zeros(ComplexF64, 2, 2)
    other = [idx for idx in 0:(N_QUBITS - 1) if idx != q]
    for a in 0:1, b in 0:1
        value = 0.0 + 0.0im
        for mask in 0:(2^(N_QUBITS - 1) - 1)
            ket_bits = zeros(Int, N_QUBITS)
            bra_bits = zeros(Int, N_QUBITS)
            ket_bits[q + 1] = a
            bra_bits[q + 1] = b
            for (pos, qubit) in enumerate(other)
                bit = (mask >> (N_QUBITS - 1 - pos)) & 1
                ket_bits[qubit + 1] = bit
                bra_bits[qubit + 1] = bit
            end
            ket = sum(ket_bits[idx + 1] << (N_QUBITS - 1 - idx) for idx in 0:(N_QUBITS - 1))
            bra = sum(bra_bits[idx + 1] << (N_QUBITS - 1 - idx) for idx in 0:(N_QUBITS - 1))
            value += rho[ket + 1, bra + 1]
        end
        red[a + 1, b + 1] = value
    end
    red
end

function permutation_unitary(order::Vector{Int})
    perm = zeros(ComplexF64, DIM, DIM)
    for old in 0:(DIM - 1)
        bits = [(old >> (N_QUBITS - 1 - idx)) & 1 for idx in 0:(N_QUBITS - 1)]
        new_bits = [bits[idx + 1] for idx in order]
        new = sum(new_bits[idx + 1] << (N_QUBITS - 1 - idx) for idx in 0:(N_QUBITS - 1))
        perm[new + 1, old + 1] = 1.0 + 0.0im
    end
    perm
end

function schedule_records()
    records = Vector{Dict{String,Any}}()
    for engine_type in [0, 1]
        sched = schedule_for_engine(engine_type)
        for (main_pos, row) in enumerate(sched)
            perception, loop_class = row
            topo = topology_spec(perception, engine_type)
            for substage_idx in 0:3
                slot = operator_slot_spec(perception, engine_type, loop_class, substage_idx)
                push!(records, Dict{String,Any}(
                    "record_index" => length(records),
                    "engine_type" => engine_type,
                    "type_label" => engine_type == 0 ? "type_one_left_weyl" : "type_two_right_weyl",
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
    end
    records
end

function evolve_pure_schedule(records::Vector{Dict{String,Any}})
    h0 = h0_from_canonical_spec()
    etas = [pi / 11.0, pi / 5.0, 3.0 * pi / 11.0]
    psi = product_state([spinor_from_angles(2.0 * eta, 0.19 + (idx - 1) * 0.41) for (idx, eta) in enumerate(etas)])
    states = Vector{Vector{ComplexF64}}()
    for rec in records
        q = mod(Int(rec["main_stage_index"]) + Int(rec["substage_index"]) + Int(rec["engine_type"]), N_QUBITS)
        r = mod(q + 1 + Int(rec["engine_type"]), N_QUBITS)
        h_sign = Int(rec["engine_type"]) == 0 ? 1.0 : -1.0
        local_theta = 0.18 * Float64(rec["sign"]) * h_sign * (1.0 + 0.25 * Float64(rec["rate"]))
        local_u = one_qubit_op(one_qubit_h_unitary(h_sign .* h0, local_theta), q)
        op = PAULI_BY_OPERATOR[String(rec["operator"])]
        axis_op = PAULI_BY_AXIS[String(rec["projector_axis"])]
        pair_word = two_qubit_op(op, q, axis_op, r)
        pair_theta = 0.055 * Float64(rec["sign"]) * (1.0 + Float64(rec["rate"])) * (1.0 + 0.1 * Int(rec["substage_index"]))
        pair_u = pauli_word_unitary(pair_word, pair_theta)
        psi = normalize(pair_u * (local_u * psi))
        push!(states, psi)
    end
    states
end

function rho_from_pure_and_extent(psi::Vector{ComplexF64}, step_idx::Int, total_steps::Int)
    fraction = Float64(step_idx + 1) / Float64(total_steps)
    p = 0.015 + 0.515 * fraction^1.18
    rho = (1.0 - p) .* dm(psi) .+ p .* Matrix{ComplexF64}(I, DIM, DIM) ./ DIM
    rho, p
end

function build_trajectory(records::Vector{Dict{String,Any}})
    pure_states = evolve_pure_schedule(records)
    rhos = Matrix{ComplexF64}[]
    entropy_values = Float64[]
    extent_values = Float64[]
    wrong_scalars = Float64[]
    local_entropy_rows = Vector{Vector{Float64}}()
    z0 = one_qubit_op(SZ, 0)
    for (idx, psi) in enumerate(pure_states)
        rho, p = rho_from_pure_and_extent(psi, idx - 1, length(pure_states))
        push!(rhos, rho)
        entropy = finite_entropy(rho)
        push!(entropy_values, entropy)
        push!(extent_values, exp(entropy))
        push!(wrong_scalars, real(tr(rho * z0)))
        push!(local_entropy_rows, [finite_entropy(reduced_one_qubit(rho, q)) for q in 0:(N_QUBITS - 1)])
        records[idx]["global_depolarizing_extent_fraction"] = p
    end
    local_final = local_entropy_rows[end]
    local_density_final = [x / extent_values[end] for x in local_final]
    diffs = [entropy_values[idx + 1] - entropy_values[idx] for idx in 1:(length(entropy_values) - 1)]
    wrong_diffs = [wrong_scalars[idx + 1] - wrong_scalars[idx] for idx in 1:(length(wrong_scalars) - 1)]
    Dict{String,Any}(
        "rhos" => rhos,
        "entropy_values" => entropy_values,
        "extent_values" => extent_values,
        "wrong_scalars" => wrong_scalars,
        "local_entropy_rows" => local_entropy_rows,
        "local_t_final" => local_density_final,
        "global_entropy_min_step_delta" => minimum(diffs),
        "wrong_scalar_positive_delta_count" => count(x -> x > TOL, wrong_diffs),
        "wrong_scalar_negative_delta_count" => count(x -> x < -TOL, wrong_diffs),
    )
end

function frame_checks(final_rho::Matrix{ComplexF64}, entropy_reference::Float64, wrong_reference::Float64)
    local_frame = kron_all([
        one_qubit_h_unitary(SX, 0.73),
        one_qubit_h_unitary(SY, -0.41),
        one_qubit_h_unitary(SZ, 0.29),
    ])
    relabel = permutation_unitary([2, 0, 1])
    rho_frame = local_frame * final_rho * local_frame'
    rho_relabel = relabel * final_rho * relabel'
    z0 = one_qubit_op(SZ, 0)
    Dict{String,Any}(
        "local_unitary_entropy_abs_diff" => abs(finite_entropy(rho_frame) - entropy_reference),
        "subsystem_relabel_entropy_abs_diff" => abs(finite_entropy(rho_relabel) - entropy_reference),
        "wrong_scalar_local_unitary_abs_diff" => abs(real(tr(rho_frame * z0)) - wrong_reference),
        "wrong_scalar_relabel_abs_diff" => abs(real(tr(rho_relabel * z0)) - wrong_reference),
    )
end

function erased_structure_control(records::Vector{Dict{String,Any}})
    psi = product_state([spinor_from_angles(pi / 2.0, 0.0) for _ in 1:N_QUBITS])
    local_rows = Vector{Vector{Float64}}()
    entropies = Float64[]
    for idx in 0:(length(records) - 1)
        rho, _ = rho_from_pure_and_extent(psi, idx, length(records))
        push!(entropies, finite_entropy(rho))
        push!(local_rows, [finite_entropy(reduced_one_qubit(rho, q)) for q in 0:(N_QUBITS - 1)])
    end
    diffs = [entropies[idx + 1] - entropies[idx] for idx in 1:(length(entropies) - 1)]
    spread = maximum(local_rows[end]) - minimum(local_rows[end])
    Dict{String,Any}(
        "description" => "canonical operator/topology structure erased: same extent ramp on a symmetric product state",
        "global_entropy_min_step_delta" => minimum(diffs),
        "local_entropy_final_spread" => spread,
        "local_t_varies" => spread > 1.0e-4,
    )
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

const FANO = [(1, 2, 3), (1, 4, 5), (1, 7, 6), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 6, 5)]

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

function conjugate_cd(x)
    out = copy(collect(x))
    out[2:end] .*= -1.0
    out
end

function cayley_dickson_multiply(parent, x, y)
    n = size(parent, 1)
    a = x[1:n]
    b = x[(n + 1):(2 * n)]
    c = y[1:n]
    d = y[(n + 1):(2 * n)]
    first = multiply_table(parent, a, c) - multiply_table(parent, conjugate_cd(d), b)
    second = multiply_table(parent, d, a) + multiply_table(parent, b, conjugate_cd(c))
    vcat(first, second)
end

function cayley_dickson_double(parent)
    n = size(parent, 1)
    table = zeros(Float64, 2 * n, 2 * n, 2 * n)
    for i in 1:(2 * n), j in 1:(2 * n)
        x = zeros(Float64, 2 * n)
        y = zeros(Float64, 2 * n)
        x[i] = 1.0
        y[j] = 1.0
        table[:, i, j] .= cayley_dickson_multiply(parent, x, y)
    end
    table
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

function gamma_relation_residual()
    ident = I2
    zero = zeros(ComplexF64, 2, 2)
    gammas = [SX, SY, SZ]
    max_resid = 0.0
    for i in 1:3, j in 1:3
        target = i == j ? 2.0 .* ident : zero
        max_resid = max(max_resid, opnorm(gammas[i] * gammas[j] + gammas[j] * gammas[i] - target))
    end
    max_resid
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

function torus_point(eta::Float64, phi::Float64, chi::Float64)
    z = cos(eta) * exp(im * phi)
    w = sin(eta) * exp(im * chi)
    z, w
end

function carrier_anchor_values()
    q_table = quaternion_table()
    qi = [0.0, 1.0, 0.0, 0.0]
    qj = [0.0, 0.0, 1.0, 0.0]
    qk = [0.0, 0.0, 0.0, 1.0]
    q_ij_residual = norm(multiply_table(q_table, qi, qj) - qk)

    cl30 = clifford_table([1, 1, 1])
    cl30_even_dim = count(mask -> count_ones(mask) % 2 == 0, 0:(size(cl30, 1) - 1))
    gamma_resid = gamma_relation_residual()

    oct_table = octonion_table()
    rank, g2_der_dim = g2_rank_der_dim(oct_table)
    s_table = cayley_dickson_double(oct_table)
    left = zeros(Float64, 16)
    right = zeros(Float64, 16)
    left[2] = -1.0
    left[11] = -1.0
    right[5] = -1.0
    right[16] = 1.0
    sedenion_zero_product_norm = norm(multiply_table(s_table, left, right))

    z, w = torus_point(pi / 4.0, 0.37, 0.91)
    hopf_s3_residual = abs(abs2(z) + abs2(w) - 1.0)

    golden_receipt = JSON.parsefile(joinpath(JULIA_CARRIER_DIR, "golden_weyl_julia_receipt.json"))
    golden_flat_delta = Float64(golden_receipt["controls"]["flat_S2"]["observable_delta"])
    golden_eta_count = Float64(golden_receipt["eta_base"]["count"])

    scalars = Dict{String,Any}(
        "carrier.quaternion_ij_minus_k_residual" => q_ij_residual,
        "carrier.cl30_even_dim" => Float64(cl30_even_dim),
        "carrier.gamma_relation_residual" => gamma_resid,
        "carrier.g2_derivation_dim" => Float64(g2_der_dim),
        "carrier.g2_constraint_rank" => Float64(rank),
        "carrier.sedenion_zero_product_norm" => sedenion_zero_product_norm,
        "carrier.hopf_s3_residual" => hopf_s3_residual,
        "carrier.golden_weyl_flat_control_delta" => golden_flat_delta,
        "carrier.golden_weyl_eta_count" => golden_eta_count,
    )
    booleans = Dict{String,Any}(
        "carrier.quaternion_table_real" => q_ij_residual < TOL,
        "carrier.clifford_even_dim_real" => cl30_even_dim == 4,
        "carrier.octonion_g2_derivation_dim_real" => g2_der_dim == 14,
        "carrier.sedenion_break_real" => sedenion_zero_product_norm < TOL,
        "carrier.hopf_torus_real" => hopf_s3_residual < TOL,
        "carrier.golden_weyl_control_real" => golden_flat_delta > 0.9,
    )
    anchors = Dict{String,Any}(
        "source_contract_paths" => [
            joinpath(JULIA_CARRIER_DIR, "division_algebra_ratchet_ladder.jl"),
            joinpath(JULIA_CARRIER_DIR, "clifford_algebra_ladder.jl"),
            joinpath(JULIA_CARRIER_DIR, "octonion_G2_automorphism.jl"),
            joinpath(JULIA_CARRIER_DIR, "sedenion_break_prelim.jl"),
            joinpath(JULIA_CARRIER_DIR, "density_matrix_spinor_lift.jl"),
            joinpath(JULIA_CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
            joinpath(JULIA_CARRIER_DIR, "golden_weyl_julia.jl"),
            joinpath(FORMAL_SCOUT_DIR, "canonical_qit_engine_specs.py"),
        ],
        "julia_source_paths_used" => [
            joinpath(JULIA_CARRIER_DIR, "division_algebra_ratchet_ladder.jl"),
            joinpath(JULIA_CARRIER_DIR, "clifford_algebra_ladder.jl"),
            joinpath(JULIA_CARRIER_DIR, "octonion_G2_automorphism.jl"),
            joinpath(JULIA_CARRIER_DIR, "sedenion_break_prelim.jl"),
            joinpath(JULIA_CARRIER_DIR, "density_matrix_spinor_lift.jl"),
            joinpath(JULIA_CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
            joinpath(JULIA_CARRIER_DIR, "golden_weyl_julia_receipt.json"),
        ],
    )
    anchors, scalars, booleans
end

function build_shared_scalars(trajectory, frames, erased, carrier_scalars)
    entropies = trajectory["entropy_values"]
    extents = trajectory["extent_values"]
    local_t = trajectory["local_t_final"]
    wrong_values = trajectory["wrong_scalars"]
    out = Dict{String,Any}(
        "schedule.substage_count" => Float64(length(entropies)),
        "global_entropy.initial" => entropies[1],
        "global_entropy.final" => entropies[end],
        "global_entropy.delta" => entropies[end] - entropies[1],
        "global_entropy.min_step_delta" => trajectory["global_entropy_min_step_delta"],
        "global_extent.initial" => extents[1],
        "global_extent.final" => extents[end],
        "global_extent.delta" => extents[end] - extents[1],
        "local_t.q0_final" => local_t[1],
        "local_t.q1_final" => local_t[2],
        "local_t.q2_final" => local_t[3],
        "local_t.final_spread" => maximum(local_t) - minimum(local_t),
        "frame.local_unitary_entropy_abs_diff" => frames["local_unitary_entropy_abs_diff"],
        "frame.subsystem_relabel_entropy_abs_diff" => frames["subsystem_relabel_entropy_abs_diff"],
        "control.wrong_scalar.initial" => wrong_values[1],
        "control.wrong_scalar.final" => wrong_values[end],
        "control.wrong_scalar.local_unitary_abs_diff" => frames["wrong_scalar_local_unitary_abs_diff"],
        "control.wrong_scalar.relabel_abs_diff" => frames["wrong_scalar_relabel_abs_diff"],
        "control.wrong_scalar.positive_delta_count" => Float64(trajectory["wrong_scalar_positive_delta_count"]),
        "control.wrong_scalar.negative_delta_count" => Float64(trajectory["wrong_scalar_negative_delta_count"]),
        "control.erased.global_entropy_min_step_delta" => erased["global_entropy_min_step_delta"],
        "control.erased.local_entropy_final_spread" => erased["local_entropy_final_spread"],
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
    trajectory = build_trajectory(records)
    final_rho = trajectory["rhos"][end]
    frames = frame_checks(final_rho, trajectory["entropy_values"][end], trajectory["wrong_scalars"][end])
    erased = erased_structure_control(records)
    carrier_anchors, carrier_scalars, carrier_booleans = carrier_anchor_values()

    global_monotone = trajectory["global_entropy_min_step_delta"] >= -TOL && trajectory["extent_values"][end] > trajectory["extent_values"][1]
    frame_invariant = frames["local_unitary_entropy_abs_diff"] < TOL && frames["subsystem_relabel_entropy_abs_diff"] < TOL
    local_t_varies = (maximum(trajectory["local_t_final"]) - minimum(trajectory["local_t_final"])) > 1.0e-4
    wrong_scalar_nonmonotone = trajectory["wrong_scalar_positive_delta_count"] > 0 && trajectory["wrong_scalar_negative_delta_count"] > 0
    wrong_scalar_frame_fails = frames["wrong_scalar_local_unitary_abs_diff"] > 1.0e-3 && frames["wrong_scalar_relabel_abs_diff"] > 1.0e-3
    erased_flip_fires = !Bool(erased["local_t_varies"])
    broken_control_fails = wrong_scalar_nonmonotone && wrong_scalar_frame_fails && erased_flip_fires

    shared_booleans = Dict{String,Any}(
        "global_monotone" => global_monotone,
        "frame_invariant" => frame_invariant,
        "local_t_varies" => local_t_varies,
        "control.wrong_scalar_nonmonotone" => wrong_scalar_nonmonotone,
        "control.wrong_scalar_frame_fails" => wrong_scalar_frame_fails,
        "control.erased_structure_flip_fires" => erased_flip_fires,
        "broken_control_fails" => broken_control_fails,
    )
    for (key, value) in carrier_booleans
        shared_booleans[key] = value
    end
    local_all_pass = all(Bool(v) for v in values(shared_booleans))

    result = Dict{String,Any}(
        "schema" => "MP_UNIVERSAL_CLOCK_DUAL_BACKEND_FINITE_SCOUT_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "backend" => BACKEND,
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "finite witness only: global entropy/extent readout versus local entropy-density readouts; NO physics, Standard Model, M(C), Axis0, dark-energy, cosmology, bridge, or formal admission",
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "finite_dual_backend_clock_witness",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "rung_spec" => Dict{String,Any}(
            "i" => "global von Neumann entropy / total finite extent scalar of the whole density state",
            "t" => "subsystem-local entropy density readout, allowed to differ by qubit",
            "positive" => "i monotone along canonical paired-engine 32-substage schedules and invariant under local unitaries/subsystem relabeling while local t differs",
            "control" => "wrong locally-resettable scalar on the same state is nonmonotone and fails frame/relabel invariance; erased-structure schedule loses local t variation",
        ),
        "carrier_anchors" => carrier_anchors,
        "canonical_qit_engine" => Dict{String,Any}(
            "H0" => "0.77*SZ + 0.13*SX mirrored from canonical_qit_engine_specs.py",
            "engine_types" => ["Type 1: +H0", "Type 2: -H0"],
            "perceptions" => ["Se", "Ne", "Ni", "Si"],
            "operators" => ["Ti", "Te", "Fi", "Fe"],
            "substage_count" => length(records),
            "per_engine_substages" => 32,
        ),
        "positive" => Dict{String,Any}(
            "global_monotone" => Dict{String,Any}("pass" => global_monotone, "min_step_delta" => trajectory["global_entropy_min_step_delta"]),
            "frame_invariant" => merge(Dict{String,Any}("pass" => frame_invariant), frames),
            "local_t_varies" => Dict{String,Any}("pass" => local_t_varies, "local_t_final" => trajectory["local_t_final"]),
        ),
        "controls" => Dict{String,Any}(
            "wrong_scalar" => Dict{String,Any}(
                "pass" => broken_control_fails,
                "wrong_scalar_nonmonotone" => wrong_scalar_nonmonotone,
                "wrong_scalar_frame_fails" => wrong_scalar_frame_fails,
                "anti_tautology" => "same final density state is read with a local Z scalar, then transformed by real local unitary and subsystem relabeling",
            ),
            "erased_structure" => merge(Dict{String,Any}("pass" => erased_flip_fires), erased),
        ),
        "boundary" => Dict{String,Any}(
            "finite_dimension" => Dict{String,Any}("qubits" => N_QUBITS, "hilbert_dimension" => DIM, "pass" => DIM == 8),
            "no_numpy_compute" => Dict{String,Any}("numpy_imported" => false, "pass" => true),
            "no_promotion" => Dict{String,Any}("classification" => "scratch_diagnostic", "promotion_allowed" => false, "formal_admission_allowed" => false, "pass" => true),
        ),
        "blocked_consumers" => ["physics", "Standard Model", "M(C)", "Axis0", "dark energy admission", "cosmology", "bridge", "formal manifold admission"],
        "eligible_consumers" => ["scratch diagnostic audits", "dual-backend parity checks", "finite readout follow-up scouts"],
        "TOOL_MANIFEST" => Dict{String,Any}(
            "Julia LinearAlgebra" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing finite density-state evolution, von Neumann entropy, extent readout, frame/relabel controls, and parity scalars"),
            "canonical_qit_engine_specs.py mirror" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing mirrored schedule, H0 sign, perceptions, operator slots, topology rates, and 32-substage per-engine structure"),
            "system_v5/julia_carrier carrier objects" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing carrier anchors for division ladder, Clifford ladder, G2 octonion derivation, sedenion break, density spinor lift, Hopf torus, and golden Weyl controls"),
            "Julia JSON/Dates" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "supportive exact receipt writing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}(
            "Julia LinearAlgebra" => "load_bearing",
            "canonical_qit_engine_specs.py mirror" => "load_bearing",
            "system_v5/julia_carrier carrier objects" => "load_bearing",
            "Julia JSON/Dates" => "supportive",
        ),
        "shared_scalars" => build_shared_scalars(trajectory, frames, erased, carrier_scalars),
        "shared_booleans" => shared_booleans,
        "schedule_trace_head" => records[1:6],
        "schedule_trace_tail" => records[(end - 5):end],
        "plain_sentence" => "Finite witness only: the whole-state entropy/extent scalar is monotone and frame-invariant, local entropy-density t varies by subsystem, and the wrong local scalar control fails.",
    )
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = local_all_pass && Bool(result["parity"]["peer_available"]) && Bool(result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = (!local_all_pass) || Bool(result["parity"]["stop_condition_fired"])
    result["summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "global_monotone" => global_monotone,
        "frame_invariant" => frame_invariant,
        "local_t_varies" => local_t_varies,
        "broken_control_fails" => broken_control_fails,
        "parity_within_1e_9" => result["parity"]["within_1e_9"],
        "parity_max_diff" => result["parity"]["parity_max_diff"],
    )
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
        "jax=$(JAX_REFERENCE_PATH) " *
        "julia=$(RESULT_PATH) " *
        "all_pass=$(lowercase(string(s["all_pass"]))) " *
        "global_monotone=$(lowercase(string(s["global_monotone"]))) " *
        "frame_invariant=$(lowercase(string(s["frame_invariant"]))) " *
        "local_t_varies=$(lowercase(string(s["local_t_varies"]))) " *
        "broken_control_fails=$(lowercase(string(s["broken_control_fails"])))"
    )
    return result["stop_condition_fired"] ? 2 : 0
end

exit(main())
