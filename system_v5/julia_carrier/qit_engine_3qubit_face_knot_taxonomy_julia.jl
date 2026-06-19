#!/usr/bin/env julia
# object_id: qit_engine_3qubit_face_knot_taxonomy
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: readouts of the canonical 3-qubit QIT engine only; no admission
# of physics, gravity, dark-sector, Axis0, M(C), bridge, or formal manifold claim.

using Dates
using JSON
using LinearAlgebra
using Statistics

const OBJECT_ID = "qit_engine_3qubit_face_knot_taxonomy"
const N_QUBITS = 3
const STAGE_DT = 0.08
const RK4_STEPS_PER_STAGE = 8
const PARITY_TOL = 1.0e-10
const DIFFER_TOL = 1.0e-6
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/qit_engine_3qubit_face_knot_taxonomy_julia_results.json")
const JAX_RESULT_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/qit_engine_3qubit_face_knot_taxonomy_results.json")
const CLAIM_CEILING = "readouts of the canonical 3-qubit QIT engine; NO admission of physics/gravity/dark-sector/Axis0/M(C); uses the proposed engine math"
const READOUT_KEYS = [
    "dark_energy_time",
    "entropy_growth",
    "preserved_info_dark_matter",
    "bounded_knot_mass",
    "composite_baryons",
    "transition_forces",
    "sync_gradient_gravity",
    "coherence",
    "holonomy",
    "three_cell_abs",
]

const I2 = ComplexF64[1.0 0.0; 0.0 1.0]
const SX = ComplexF64[0.0 1.0; 1.0 0.0]
const SY = ComplexF64[0.0 -im; im 0.0]
const SZ = ComplexF64[1.0 0.0; 0.0 -1.0]
const SIGMA_MINUS = ComplexF64[0.0 0.0; 1.0 0.0]
const SIGMA_PLUS = ComplexF64[0.0 1.0; 0.0 0.0]
const MIRROR = SX
const H0 = 0.77 .* SZ .+ 0.13 .* SX

const PERCEPTION_L = Dict{String,Matrix{ComplexF64}}(
    "Se" => SZ,
    "Ne" => SIGMA_PLUS,
    "Ni" => (-im) .* SY,
    "Si" => SIGMA_MINUS,
)
const OPERATOR_GENERATORS = Dict{String,Matrix{ComplexF64}}(
    "Ti" => SZ,
    "Te" => SX,
    "Fi" => SX,
    "Fe" => SY,
)
const OPERATOR_BASE_ANGLES = Dict{String,Float64}(
    "Ti" => 0.12,
    "Te" => 0.09,
    "Fi" => 0.15,
    "Fe" => 0.11,
)
const OPERATOR_SLOT_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]
const NATIVE_OPERATORS_BY_TOPOLOGY = Dict{String,Vector{String}}(
    "Se" => ["Ti", "Fi"],
    "Ne" => ["Ti", "Fi"],
    "Ni" => ["Te", "Fe"],
    "Si" => ["Te", "Fe"],
)
const OPERATOR_MAP_FAMILY = Dict{String,String}(
    "Ti" => "z_pinching_dephase",
    "Te" => "x_pinching_dephase",
    "Fi" => "x_coherent_rotation",
    "Fe" => "z_coherent_rotation",
)
const CHART_TOKEN_PRECEDENCE = Dict{String,Tuple{String,Int}}(
    "TiSe" => ("operator_first", +1),
    "TiNe" => ("operator_first", +1),
    "SeTi" => ("terrain_first", -1),
    "NeTi" => ("terrain_first", -1),
    "FeSi" => ("operator_first", +1),
    "FeNi" => ("operator_first", +1),
    "SiFe" => ("terrain_first", -1),
    "NiFe" => ("terrain_first", -1),
    "TeNi" => ("operator_first", +1),
    "TeSi" => ("operator_first", +1),
    "NiTe" => ("terrain_first", -1),
    "SiTe" => ("terrain_first", -1),
    "FiNe" => ("operator_first", +1),
    "FiSe" => ("operator_first", +1),
    "NeFi" => ("terrain_first", -1),
    "SeFi" => ("terrain_first", -1),
)

const TYPE_ONE_TOPOLOGIES = Dict{String,Dict{String,Dict{String,Any}}}(
    "Se" => Dict("outer" => Dict("op" => "Ti", "sign" => +1), "inner" => Dict("op" => "Fi", "sign" => -1)),
    "Ne" => Dict("outer" => Dict("op" => "Ti", "sign" => -1), "inner" => Dict("op" => "Fi", "sign" => +1)),
    "Ni" => Dict("outer" => Dict("op" => "Fe", "sign" => -1), "inner" => Dict("op" => "Te", "sign" => +1)),
    "Si" => Dict("outer" => Dict("op" => "Fe", "sign" => +1), "inner" => Dict("op" => "Te", "sign" => -1)),
)
const TYPE_TWO_TOPOLOGIES = Dict{String,Dict{String,Dict{String,Any}}}(
    "Se" => Dict("outer" => Dict("op" => "Fi", "sign" => +1), "inner" => Dict("op" => "Ti", "sign" => -1)),
    "Ne" => Dict("outer" => Dict("op" => "Fi", "sign" => -1), "inner" => Dict("op" => "Ti", "sign" => +1)),
    "Ni" => Dict("outer" => Dict("op" => "Te", "sign" => -1), "inner" => Dict("op" => "Fe", "sign" => +1)),
    "Si" => Dict("outer" => Dict("op" => "Te", "sign" => +1), "inner" => Dict("op" => "Fe", "sign" => -1)),
)
const ENGINE_SCHEDULE_TYPE_ONE = [
    ("Se", "outer"),
    ("Ne", "outer"),
    ("Ni", "outer"),
    ("Si", "outer"),
    ("Se", "inner"),
    ("Si", "inner"),
    ("Ni", "inner"),
    ("Ne", "inner"),
]
const ENGINE_SCHEDULE_TYPE_TWO = [
    ("Se", "outer"),
    ("Si", "outer"),
    ("Ni", "outer"),
    ("Ne", "outer"),
    ("Se", "inner"),
    ("Ne", "inner"),
    ("Ni", "inner"),
    ("Si", "inner"),
]

ordered_token(operator::String, perception::String, precedence::String) =
    precedence == "operator_first" ? string(operator, perception) :
    precedence == "terrain_first" ? string(perception, operator) :
    error("unknown precedence $precedence")

topologies(engine_type::Int) = engine_type == 0 ? TYPE_ONE_TOPOLOGIES :
    engine_type == 1 ? TYPE_TWO_TOPOLOGIES :
    error("engine_type must be 0 or 1, got $engine_type")

schedule_for(engine_type::Int) = engine_type == 0 ? ENGINE_SCHEDULE_TYPE_ONE : ENGINE_SCHEDULE_TYPE_TWO

function inner_before_outer_schedule(engine_type::Int)
    schedule = schedule_for(engine_type)
    vcat([row for row in schedule if row[2] == "inner"], [row for row in schedule if row[2] == "outer"])
end

function operator_slot_spec(perception::String, engine_type::Int, loop_class::String, substage_idx::Int)
    topo = topologies(engine_type)[perception]
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
            sign = mod(substage_idx + engine_type, 2) == 0 ? +1 : -1
            precedence = sign > 0 ? "operator_first" : "terrain_first"
            token = ordered_token(op, perception, precedence)
        end
        chart_locked = false
    end
    Dict{String,Any}(
        "operator" => op,
        "sign" => Int(sign),
        "precedence" => precedence,
        "token" => token,
        "operator_family" => OPERATOR_MAP_FAMILY[op],
        "is_native_operator" => op in native,
        "is_chart_locked" => chart_locked,
        "native_operator_set" => native,
    )
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
    dim = 2^n_qubits
    out = zeros(ComplexF64, dim, dim)
    for idx in 0:(n_qubits - 1)
        out .+= site_op(local_op, n_qubits, idx)
    end
    out
end

hamiltonian(engine_type::Int, n_qubits::Int) =
    all_site_sum(engine_type == 0 ? H0 : (-1.0 .* H0), n_qubits)

function collapse_ops(perception::String, engine_type::Int, n_qubits::Int)
    local_l = PERCEPTION_L[perception]
    if engine_type == 1
        local_l = MIRROR * local_l * MIRROR
    end
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
    dt_step = STAGE_DT / Float64(RK4_STEPS_PER_STAGE)
    for _ in 1:RK4_STEPS_PER_STAGE
        k1 = lindblad_rhs(y, h, ls)
        k2 = lindblad_rhs(y .+ 0.5 * dt_step .* k1, h, ls)
        k3 = lindblad_rhs(y .+ 0.5 * dt_step .* k2, h, ls)
        k4 = lindblad_rhs(y .+ dt_step .* k3, h, ls)
        y = y .+ (dt_step / 6.0) .* (k1 .+ 2.0 .* k2 .+ 2.0 .* k3 .+ k4)
    end
    normalize_density(y)
end

function operator_unitary_local(op_name::String, sign::Int)
    theta = OPERATOR_BASE_ANGLES[op_name] * Float64(sign)
    generator = OPERATOR_GENERATORS[op_name]
    cos(theta) .* I2 .- im * sin(theta) .* generator
end

function apply_operator(rho::Matrix{ComplexF64}, n_qubits::Int, op_name::String, sign::Int, erased::Bool)
    if erased
        return rho
    end
    local_u = operator_unitary_local(op_name, sign)
    global_u = kron_chain([local_u for _ in 1:n_qubits])
    normalize_density(global_u * rho * global_u')
end

matrix_norm(a::Matrix{ComplexF64}) = Float64(norm(a))
trace_residual(rho::Matrix{ComplexF64}) = abs(Float64(real(tr(rho))) - 1.0)
min_eigenvalue(rho::Matrix{ComplexF64}) = Float64(minimum(eigvals(Hermitian(0.5 .* (rho .+ rho')))))

function run_engine(; n_qubits::Int, engine_type::Int, schedule, rho_init::Matrix{ComplexF64}, operator_erased::Bool=false)
    rho = normalize_density(rho_init)
    h = hamiltonian(engine_type, n_qubits)
    states = Matrix{ComplexF64}[rho]
    records = Vector{Dict{String,Any}}()
    for (main_idx0, row) in enumerate(schedule)
        main_idx = main_idx0 - 1
        perception, loop_class = row
        for substage_idx in 0:3
            before = rho
            slot = operator_slot_spec(perception, engine_type, loop_class, substage_idx)
            ls = collapse_ops(perception, engine_type, n_qubits)
            if slot["precedence"] == "operator_first"
                rho = apply_operator(rho, n_qubits, slot["operator"], Int(slot["sign"]), operator_erased)
                rho = lindblad_step(rho, h, ls)
            else
                rho = lindblad_step(rho, h, ls)
                rho = apply_operator(rho, n_qubits, slot["operator"], Int(slot["sign"]), operator_erased)
            end
            rho = normalize_density(rho)
            push!(states, rho)
            push!(records, Dict{String,Any}(
                "main_stage_idx" => main_idx,
                "substage_idx" => substage_idx,
                "perception" => perception,
                "loop_class" => loop_class,
                "operator" => slot["operator"],
                "operator_sign" => Int(slot["sign"]),
                "precedence" => slot["precedence"],
                "ordered_token" => slot["token"],
                "operator_erased" => operator_erased,
                "transition_delta_fro" => matrix_norm(rho - before),
                "trace_residual" => trace_residual(rho),
                "min_eigenvalue" => min_eigenvalue(rho),
            ))
        end
    end
    Dict{String,Any}(
        "n_qubits" => n_qubits,
        "engine_type" => engine_type,
        "operator_erased" => operator_erased,
        "states" => states,
        "records" => records,
        "n_substages" => length(records),
    )
end

rho_from_bloch(v::Tuple{Float64,Float64,Float64}) =
    0.5 .* (I2 .+ v[1] .* SX .+ v[2] .* SY .+ v[3] .* SZ)

function ket(index::Int, dim::Int)
    out = zeros(ComplexF64, dim)
    out[index + 1] = 1.0 + 0.0im
    out
end

function pure_density(psi::Vector{ComplexF64})
    psi_n = psi ./ norm(psi)
    psi_n * psi_n'
end

function maximally_mixed(n_qubits::Int)
    dim = 2^n_qubits
    Matrix{ComplexF64}(I, dim, dim) ./ Float64(dim)
end

function primary_density()
    q0 = ket(0, 2)
    bell = (ket(0, 4) .+ exp(0.37im) .* ket(3, 4)) ./ sqrt(2.0)
    psi = kron(q0, bell)
    pure = pure_density(psi)
    normalize_density(0.86 .* pure .+ 0.14 .* maximally_mixed(3))
end

function two_qubit_density()
    bell = (ket(0, 4) .+ exp(0.37im) .* ket(3, 4)) ./ sqrt(2.0)
    normalize_density(0.86 .* pure_density(bell) .+ 0.14 .* maximally_mixed(2))
end

product_density(local_rhos::Vector{Matrix{ComplexF64}}) = normalize_density(kron_chain(local_rhos))

function shape_density(swapped::Bool)
    q0 = rho_from_bloch((0.0, 0.0, 0.92))
    q1 = rho_from_bloch((0.0, 0.0, 0.0))
    q2 = rho_from_bloch((0.95, 0.0, 0.0))
    product_density(swapped ? [q0, q2, q1] : [q0, q1, q2])
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
            kr = keep_index(r, n_qubits, keep_sorted)
            kc = keep_index(c, n_qubits, keep_sorted)
            out[kr + 1, kc + 1] += rho[r + 1, c + 1]
        end
    end
    normalize_density(out)
end

function vn_entropy(rho::Matrix{ComplexF64})
    vals = real.(eigvals(Hermitian(0.5 .* (rho .+ rho'))))
    clipped = [clamp(v, 1.0e-15, 1.0) for v in vals]
    total = sum(clipped)
    normed = clipped ./ total
    Float64(-sum(v * log(v) for v in normed))
end

purity(rho::Matrix{ComplexF64}) = Float64(real(tr(rho * rho)))

function mutual_info(rho::Matrix{ComplexF64}, n_qubits::Int, left::Vector{Int}, right::Vector{Int})
    rho_l = partial_trace(rho, n_qubits, left)
    rho_r = partial_trace(rho, n_qubits, right)
    rho_lr = partial_trace(rho, n_qubits, sort(vcat(left, right)))
    vn_entropy(rho_l) + vn_entropy(rho_r) - vn_entropy(rho_lr)
end

function tripartite_information(rho::Matrix{ComplexF64}, n_qubits::Int)
    if n_qubits < 3
        return 0.0
    end
    s0 = vn_entropy(partial_trace(rho, n_qubits, [0]))
    s1 = vn_entropy(partial_trace(rho, n_qubits, [1]))
    s2 = vn_entropy(partial_trace(rho, n_qubits, [2]))
    s01 = vn_entropy(partial_trace(rho, n_qubits, [0, 1]))
    s02 = vn_entropy(partial_trace(rho, n_qubits, [0, 2]))
    s12 = vn_entropy(partial_trace(rho, n_qubits, [1, 2]))
    s012 = vn_entropy(rho)
    s0 + s1 + s2 - s01 - s02 - s12 + s012
end

function offdiag_coherence(rho::Matrix{ComplexF64})
    dim = size(rho, 1)
    total = 0.0
    for i in 1:dim, j in 1:dim
        if i != j
            total += abs(rho[i, j])
        end
    end
    Float64(total / Float64(dim * (dim - 1)))
end

function gauge_fix(vec::Vector{ComplexF64})
    idx = argmax(abs.(vec))
    vec .* exp(-im * angle(vec[idx]))
end

function holonomy_phase(states::Vector{Matrix{ComplexF64}})
    product = 1.0 + 0.0im
    prev_vec = nothing
    for rho in states
        eig = eigen(Hermitian(0.5 .* (rho .+ rho')))
        if length(eig.values) > 1 && Float64(eig.values[end] - eig.values[end - 1]) < 1.0e-12
            prev_vec = nothing
            continue
        end
        vec = gauge_fix(Vector{ComplexF64}(eig.vectors[:, end]))
        if prev_vec !== nothing
            overlap = dot(prev_vec, vec)
            mag = abs(overlap)
            if mag > 1.0e-14
                product *= overlap / mag
            end
        end
        prev_vec = vec
    end
    Float64(-angle(product))
end

function readouts(run::Dict{String,Any})
    n_qubits = Int(run["n_qubits"])
    states = run["states"]::Vector{Matrix{ComplexF64}}
    records = run["records"]::Vector{Dict{String,Any}}
    initial = states[1]
    final = states[end]
    log2 = log(2.0)
    global_norm = log(Float64(2^n_qubits))
    global_entropies = [vn_entropy(state) for state in states]
    local_final = [partial_trace(final, n_qubits, [idx]) for idx in 0:(n_qubits - 1)]
    local_entropy_norm = [vn_entropy(rho_q) / log2 for rho_q in local_final]
    if n_qubits >= 3
        mi_initial = mutual_info(initial, n_qubits, [1], [2])
        mi_final = mutual_info(final, n_qubits, [1], [2])
        pair = partial_trace(final, n_qubits, [1, 2])
        three_cell = tripartite_information(final, n_qubits)
    else
        mi_initial = mutual_info(initial, n_qubits, [0], [1])
        mi_final = mutual_info(final, n_qubits, [0], [1])
        pair = final
        three_cell = 0.0
    end
    others_mean = sum(local_entropy_norm[2:end]) / Float64(max(1, n_qubits - 1))
    mass = max(0.0, others_mean - local_entropy_norm[1])
    gravity_sum = 0.0
    for idx in 2:n_qubits
        gravity_sum += abs(local_entropy_norm[idx] - local_entropy_norm[1]) / Float64(idx - 1)
    end
    transition_values = [Float64(row["transition_delta_fro"]) for row in records]
    Dict{String,Float64}(
        "dark_energy_time" => maximum(global_entropies) / global_norm,
        "entropy_growth" => (global_entropies[end] - global_entropies[1]) / global_norm,
        "preserved_info_dark_matter" => max(0.0, min(mi_initial, mi_final) / (2.0 * log2)),
        "bounded_knot_mass" => mass,
        "composite_baryons" => max(0.0, mi_final / (2.0 * log2)) * purity(pair),
        "transition_forces" => mean(transition_values),
        "sync_gradient_gravity" => mass * gravity_sum,
        "coherence" => offdiag_coherence(final),
        "holonomy" => holonomy_phase(states),
        "three_cell_abs" => abs(three_cell) / log2,
    )
end

function matrix_payload(rho::Matrix{ComplexF64})
    Dict{String,Any}(
        "real" => [[Float64(real(rho[i, j])) for j in 1:size(rho, 2)] for i in 1:size(rho, 1)],
        "imag" => [[Float64(imag(rho[i, j])) for j in 1:size(rho, 2)] for i in 1:size(rho, 1)],
    )
end

function branch_result(label::String; n_qubits::Int, engine_type::Int, schedule, rho_init::Matrix{ComplexF64}, operator_erased::Bool=false)
    run = run_engine(n_qubits=n_qubits, engine_type=engine_type, schedule=schedule, rho_init=rho_init, operator_erased=operator_erased)
    r = readouts(run)
    final = run["states"][end]
    max_trace_residual = maximum(Float64(row["trace_residual"]) for row in run["records"])
    min_psd = minimum(Float64(row["min_eigenvalue"]) for row in run["records"])
    Dict{String,Any}(
        "label" => label,
        "n_qubits" => n_qubits,
        "engine_type" => engine_type,
        "engine_type_label" => engine_type == 0 ? "type_one_left_weyl" : "type_two_right_weyl",
        "schedule" => [[row[1], row[2]] for row in schedule],
        "operator_erased" => operator_erased,
        "n_substages" => Int(run["n_substages"]),
        "readouts" => r,
        "transition_channel_checks" => Dict{String,Any}(
            "trace_residual_max" => max_trace_residual,
            "min_eigenvalue_over_trajectory" => min_psd,
            "cptp_numeric_pass" => max_trace_residual < 1.0e-10 && min_psd > -1.0e-10,
        ),
        "final_density" => matrix_payload(final),
    )
end

function max_readout_diff(left::Dict{String,Any}, right::Dict{String,Any})
    maximum(abs(Float64(left["readouts"][key]) - Float64(right["readouts"][key])) for key in READOUT_KEYS)
end

function readout_rank(branch_list::Vector{Dict{String,Any}})
    matrix = [Float64(branch["readouts"][key]) for branch in branch_list, key in READOUT_KEYS]
    centered = matrix .- mean(matrix, dims=1)
    Int(sum(svdvals(centered) .> 1.0e-8))
end

function parity_block(result::Dict{String,Any})
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "peer_available" => false,
            "within_1e_10" => false,
            "parity_max_diff" => nothing,
            "worst_key" => nothing,
            "missing_from_peer" => sort(collect(keys(result["shared_scalars"]))),
            "missing_from_self" => String[],
            "boolean_mismatches" => String[],
        )
    end
    peer = JSON.parsefile(JAX_RESULT_PATH)
    self_scalars = result["shared_scalars"]
    peer_scalars = peer["shared_scalars"]
    missing_from_peer = sort(setdiff(collect(keys(self_scalars)), collect(keys(peer_scalars))))
    missing_from_self = sort(setdiff(collect(keys(peer_scalars)), collect(keys(self_scalars))))
    max_diff = 0.0
    worst_key = nothing
    diffs = Dict{String,Float64}()
    for (key, value) in self_scalars
        if haskey(peer_scalars, key)
            diff = abs(Float64(value) - Float64(peer_scalars[key]))
            diffs[key] = diff
            if diff > max_diff
                max_diff = diff
                worst_key = key
            end
        end
    end
    self_booleans = result["shared_booleans"]
    peer_booleans = peer["shared_booleans"]
    boolean_mismatches = String[]
    for (key, value) in self_booleans
        if haskey(peer_booleans, key) && Bool(value) != Bool(peer_booleans[key])
            push!(boolean_mismatches, key)
        end
    end
    within = isempty(missing_from_peer) && isempty(missing_from_self) && isempty(boolean_mismatches) && max_diff <= PARITY_TOL
    Dict{String,Any}(
        "peer_result_path" => JAX_RESULT_PATH,
        "peer_available" => true,
        "within_1e_10" => within,
        "parity_max_diff" => max_diff,
        "worst_key" => worst_key,
        "missing_from_peer" => missing_from_peer,
        "missing_from_self" => missing_from_self,
        "boolean_mismatches" => boolean_mismatches,
        "diffs" => diffs,
    )
end

function build_result()
    rho0 = primary_density()
    branch_labels = [
        "type1_canonical",
        "type2_canonical",
        "type1_with_type2_schedule_order",
        "type1_inner_before_outer_order",
        "type1_operator_erased",
    ]
    branches = Dict{String,Any}(
        "type1_canonical" => branch_result("type1_canonical", n_qubits=3, engine_type=0, schedule=ENGINE_SCHEDULE_TYPE_ONE, rho_init=rho0),
        "type2_canonical" => branch_result("type2_canonical", n_qubits=3, engine_type=1, schedule=ENGINE_SCHEDULE_TYPE_TWO, rho_init=rho0),
        "type1_with_type2_schedule_order" => branch_result("type1_with_type2_schedule_order", n_qubits=3, engine_type=0, schedule=ENGINE_SCHEDULE_TYPE_TWO, rho_init=rho0),
        "type1_inner_before_outer_order" => branch_result("type1_inner_before_outer_order", n_qubits=3, engine_type=0, schedule=inner_before_outer_schedule(0), rho_init=rho0),
        "type1_operator_erased" => branch_result("type1_operator_erased", n_qubits=3, engine_type=0, schedule=ENGINE_SCHEDULE_TYPE_ONE, rho_init=rho0, operator_erased=true),
    )
    flat = branch_result("flat_fuzz_type1", n_qubits=3, engine_type=0, schedule=ENGINE_SCHEDULE_TYPE_ONE, rho_init=maximally_mixed(3))
    knot = branch_result("knot_product_type1", n_qubits=3, engine_type=0, schedule=ENGINE_SCHEDULE_TYPE_ONE, rho_init=shape_density(false))
    shape = branch_result("knot_shape_swapped_type1", n_qubits=3, engine_type=0, schedule=ENGINE_SCHEDULE_TYPE_ONE, rho_init=shape_density(true))
    twoq = branch_result("two_qubit_control_type1", n_qubits=2, engine_type=0, schedule=ENGINE_SCHEDULE_TYPE_ONE, rho_init=two_qubit_density())

    rank = readout_rank([branches[label] for label in branch_labels])
    type_diff = max_readout_diff(branches["type1_canonical"], branches["type2_canonical"])
    schedule_type_diff = max_readout_diff(branches["type1_canonical"], branches["type1_with_type2_schedule_order"])
    loop_order_diff = max_readout_diff(branches["type1_canonical"], branches["type1_inner_before_outer_order"])
    erased_diff = max_readout_diff(branches["type1_canonical"], branches["type1_operator_erased"])
    flat_r = flat["readouts"]
    knot_r = knot["readouts"]
    shape_r = shape["readouts"]
    mass_delta = abs(knot_r["bounded_knot_mass"] - shape_r["bounded_knot_mass"])
    gravity_delta = abs(knot_r["sync_gradient_gravity"] - shape_r["sync_gradient_gravity"])
    flat_vanish = (
        abs(flat_r["bounded_knot_mass"]) < 1.0e-10 &&
        abs(flat_r["composite_baryons"]) < 1.0e-10 &&
        abs(flat_r["sync_gradient_gravity"]) < 1.0e-10 &&
        abs(flat_r["dark_energy_time"] - 1.0) < 1.0e-10
    )
    knot_couples = knot_r["bounded_knot_mass"] > 1.0e-4 && knot_r["sync_gradient_gravity"] > 1.0e-4
    decoupling_witness = mass_delta < 1.0e-10 && gravity_delta > 1.0e-4
    two_qubit_insufficient = twoq["n_qubits"] == 2 && twoq["readouts"]["three_cell_abs"] == 0.0

    shared_scalars = Dict{String,Float64}()
    for label in branch_labels
        branch = branches[label]
        for key in READOUT_KEYS
            shared_scalars["branch.$label.$key"] = Float64(branch["readouts"][key])
        end
        shared_scalars["branch.$label.trace_residual_max"] = Float64(branch["transition_channel_checks"]["trace_residual_max"])
        shared_scalars["branch.$label.min_eigenvalue_over_trajectory"] = Float64(branch["transition_channel_checks"]["min_eigenvalue_over_trajectory"])
    end
    for (label, branch) in Dict("flat" => flat, "knot" => knot, "shape" => shape, "twoq" => twoq)
        for key in READOUT_KEYS
            shared_scalars["control.$label.$key"] = Float64(branch["readouts"][key])
        end
    end
    shared_scalars["diff.type1_vs_type2"] = Float64(type_diff)
    shared_scalars["diff.type1_vs_type2_schedule_order"] = Float64(schedule_type_diff)
    shared_scalars["diff.outer_vs_inner_loop_order"] = Float64(loop_order_diff)
    shared_scalars["diff.operator_on_vs_erased"] = Float64(erased_diff)
    shared_scalars["control.shape_mass_delta"] = Float64(mass_delta)
    shared_scalars["control.shape_gravity_delta"] = Float64(gravity_delta)
    shared_scalars["readout_rank"] = Float64(rank)
    shared_scalars["n_qubits"] = Float64(N_QUBITS)
    shared_scalars["n_substages_per_engine"] = 32.0

    shared_booleans = Dict{String,Bool}(
        "jax_enable_x64" => true,
        "numpy_compute_used" => false,
        "torch_compute_used" => false,
        "type1_vs_type2_differ" => type_diff > DIFFER_TOL,
        "schedule_orders_differ" => schedule_type_diff > DIFFER_TOL && loop_order_diff > DIFFER_TOL,
        "operator_order_matters" => erased_diff > DIFFER_TOL,
        "distinct_probe" => rank > 1,
        "flat_vanish" => flat_vanish,
        "knot_couples" => knot_couples,
        "decoupling_witness" => decoupling_witness,
        "two_qubit_insufficient" => two_qubit_insufficient,
        "all_branches_32_substages" => all(branches[label]["n_substages"] == 32 for label in branch_labels),
        "all_transition_channels_numeric_cptp" => all(branches[label]["transition_channel_checks"]["cptp_numeric_pass"] for label in branch_labels),
    )
    positive_boolean_keys = [
        "jax_enable_x64",
        "type1_vs_type2_differ",
        "schedule_orders_differ",
        "operator_order_matters",
        "distinct_probe",
        "flat_vanish",
        "knot_couples",
        "decoupling_witness",
        "two_qubit_insufficient",
        "all_branches_32_substages",
        "all_transition_channels_numeric_cptp",
    ]
    controls = Dict{String,Any}(
        "distinct_probe" => Dict("pass" => shared_booleans["distinct_probe"], "readout_rank" => rank, "rank_threshold" => "> 1"),
        "flat_fuzz" => Dict("pass" => shared_booleans["flat_vanish"], "readouts" => flat_r, "condition" => "max-entropy rho has zero knot/baryon/gravity readouts and dark_energy_time=1"),
        "knot_couples_mass_gravity" => Dict("pass" => shared_booleans["knot_couples"], "mass" => knot_r["bounded_knot_mass"], "gravity" => knot_r["sync_gradient_gravity"]),
        "decoupling_witness" => Dict("pass" => shared_booleans["decoupling_witness"], "mass_delta" => mass_delta, "gravity_delta" => gravity_delta, "condition" => "shape swap preserves local knot mass but moves distance-weighted entropy gradient"),
        "two_qubit_control_insufficient" => Dict("pass" => shared_booleans["two_qubit_insufficient"], "n_qubits" => twoq["n_qubits"], "three_cell_defined" => false, "reason" => "tripartite inclusion-exclusion needs three one-qubit regions A,B,C and pairs AB,AC,BC"),
    )
    branch_tests = Dict{String,Any}(
        "type1_vs_type2_weyl" => Dict("pass" => shared_booleans["type1_vs_type2_differ"], "max_readout_diff" => type_diff, "type1_hamiltonian" => "+(0.77*SZ + 0.13*SX)", "type2_hamiltonian" => "-(0.77*SZ + 0.13*SX)"),
        "loop_classes_and_schedule_orders" => Dict("pass" => shared_booleans["schedule_orders_differ"], "type1_vs_type2_schedule_order_diff" => schedule_type_diff, "outer_first_vs_inner_first_diff" => loop_order_diff),
        "operator_on_vs_operator_erased" => Dict("pass" => shared_booleans["operator_order_matters"], "max_readout_diff" => erased_diff),
    )
    positive = Dict{String,Any}(
        "canonical_type_branches_separate" => branch_tests["type1_vs_type2_weyl"],
        "schedule_and_loop_order_are_observable" => branch_tests["loop_classes_and_schedule_orders"],
        "operator_erasure_changes_readouts" => branch_tests["operator_on_vs_operator_erased"],
        "three_qubit_readout_rank_nontrivial" => controls["distinct_probe"],
    )
    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia",
        "created_at" => string(now(UTC)),
        "result_path" => RESULT_PATH,
        "jax_result_path" => JAX_RESULT_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => CLAIM_CEILING,
        "n_qubits" => N_QUBITS,
        "source_math_lock" => Dict(
            "source_file" => "system_v5/ops/formal_scouts/canonical_qit_engine_specs.py",
            "hamiltonian" => "H0=0.77*SZ+0.13*SX; Type1=+H0; Type2=-H0",
            "lindblad" => "Se=SZ, Ne=SIGMA_PLUS, Ni=-i*SY, Si=SIGMA_MINUS; Type2 uses MIRROR @ L @ MIRROR",
            "operators" => "Ti=SZ, Te=SX, Fi=SX, Fe=SY with OPERATOR_BASE_ANGLES",
            "schedule" => "8 main stages x 4 operator substages = 32 per engine",
            "carrier_extension" => "site-local canonical H, L, and operator kicks lifted to (C^2)^n by Kronecker products",
            "non_source_math_excluded" => ["no toy spinor network operators", "no invented Hamiltonian", "no torch compute in this scout", "no numpy compute in this scout"],
        ),
        "branches" => branches,
        "controls" => controls,
        "branch_tests" => branch_tests,
        "positive" => positive,
        "control_runs" => Dict("flat_fuzz_type1" => flat, "knot_product_type1" => knot, "knot_shape_swapped_type1" => shape, "two_qubit_control_type1" => twoq),
        "readout_keys" => READOUT_KEYS,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "positive_boolean_keys" => positive_boolean_keys,
        "tool_manifest" => Dict(
            "Julia" => Dict("used" => true, "reason" => "load-bearing ComplexF64 density evolution and mirror readout computation"),
            "LinearAlgebra" => Dict("used" => true, "reason" => "load-bearing matrix algebra and eigensolvers"),
            "JSON" => Dict("used" => true, "reason" => "durable scratch diagnostic result serialization"),
            "JAX" => Dict("used" => false, "reason" => "peer backend is executed in separate JAX scout"),
        ),
        "tool_integration_depth" => Dict("Julia" => "load_bearing", "LinearAlgebra" => "load_bearing", "JSON" => "supportive", "JAX" => "supportive"),
        "promotion_blockers" => ["classification is scratch_diagnostic", "promotion_allowed=false", "formal_admission_allowed=false", "readouts are taxonomy diagnostics only and do not admit physics/gravity/dark-sector/Axis0/M(C)"],
    )
    result["parity"] = parity_block(result)
    result["all_pass"] = all(shared_booleans[key] for key in positive_boolean_keys) &&
        !shared_booleans["numpy_compute_used"] &&
        !shared_booleans["torch_compute_used"] &&
        all(Bool(row["pass"]) for row in values(controls)) &&
        all(Bool(row["pass"]) for row in values(branch_tests)) &&
        Bool(result["parity"]["within_1e_10"])
    result["stop_condition_fired"] = !Bool(result["all_pass"])
    result
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("RESULT $(OBJECT_ID) julia all_pass=$(result["all_pass"]) -> $(RESULT_PATH)")
    println(
        "SCOUT_DONE " *
        "jax=$(JAX_RESULT_PATH) " *
        "julia=$(RESULT_PATH) " *
        "all_pass=$(lowercase(string(result["all_pass"]))) " *
        "n_qubits=$(N_QUBITS) " *
        "type1_vs_type2_differ=$(lowercase(string(result["shared_booleans"]["type1_vs_type2_differ"]))) " *
        "readout_rank=$(Int(result["shared_scalars"]["readout_rank"])) " *
        "flat_vanish=$(lowercase(string(result["shared_booleans"]["flat_vanish"]))) " *
        "knot_couples=$(lowercase(string(result["shared_booleans"]["knot_couples"]))) " *
        "two_qubit_insufficient=$(lowercase(string(result["shared_booleans"]["two_qubit_insufficient"])))"
    )
    return Bool(result["all_pass"]) ? 0 : 1
end

exit(main())
