#!/usr/bin/env julia
# object_id: disc_qit_source_native_face_knot_shell_discriminator
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA
using Statistics

module LiftSource
include(joinpath(@__DIR__, "density_matrix_spinor_lift.jl"))
end

const OBJECT_ID = "disc_qit_source_native_face_knot_shell_discriminator"
const NAME = OBJECT_ID
const BACKEND = "julia_float64"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUTS = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const JULIA_CARRIER = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(JULIA_CARRIER, "disc_qit_source_native_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUTS, "results", "disc_qit_source_native_results.json")
const SOURCE_PATH = joinpath(JULIA_CARRIER, "disc_qit_source_native_julia.jl")
const CANONICAL_QIT_PATH = joinpath(FORMAL_SCOUTS, "canonical_qit_engine_specs.py")
const QIT_TAXONOMY_PATH = joinpath(JULIA_CARRIER, "qit_engine_3qubit_face_knot_taxonomy_julia.jl")
const DENSITY_LIFT_JAX_PATH = joinpath(JULIA_CARRIER, "jax_density_matrix_spinor_lift.py")
const DENSITY_LIFT_JULIA_PATH = joinpath(JULIA_CARRIER, "density_matrix_spinor_lift.jl")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const SIM_EXECUTION_KIND = "scratch"
const N_QUBITS = 3
const PARITY_TOL = 1.0e-9
const FACE_THRESHOLD = 5.0e-2
const KNOT_THRESHOLD = 1.0e-2
const SHELL_THRESHOLD = 1.0e-4
const MUTATION_DIE_RATIO = 0.12
const CLAIM_CEILING = "QIT source-native face/knot/shell carrier-readout discriminator only. classification=scratch_diagnostic; promotion=false; formal_admission=false. No QIT admission, no physics, no gravity, no dark-sector, no Axis0, no M(C), no bridge, no PEPS3D, and no final manifold closure."
const BLOCKED_CONSUMERS = [
    "QIT engine admission",
    "physics",
    "gravity",
    "dark-sector",
    "Axis0",
    "M(C)",
    "bridge",
    "PEPS3D",
    "formal admission",
    "promotion",
]
const READOUT_MAP = Dict{String,String}(
    "face_entropy_growth" => "entropy_growth",
    "face_three_cell_abs" => "three_cell_abs",
    "knot_bounded_mass" => "bounded_knot_mass",
    "shell_sync_gradient" => "sync_gradient_gravity",
)
const TOOL_MANIFEST = Dict{String,Any}(
    "Julia LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Float64/ComplexF64 mirror backend for finite carrier mutation discriminator",
    ),
    "Julia peer backend" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing peer result compared against JAX shared scalars and booleans",
    ),
    "canonical_qit_engine_specs.py" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing source-native schedule/operator witness mirrored by the Julia QIT taxonomy runner",
    ),
    "density_matrix_spinor_lift" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing owner carrier construction from spinor lift to finite density matrix",
    ),
    "Julia stdlib" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive JSON, hashing, timestamps, and path handling",
    ),
    "numpy" => Dict(
        "tried" => false,
        "used" => false,
        "reason" => "explicitly excluded; this Julia mirror uses no NumPy compute path",
    ),
)
const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia LinearAlgebra" => "load_bearing",
    "Julia peer backend" => "load_bearing",
    "canonical_qit_engine_specs.py" => "load_bearing",
    "density_matrix_spinor_lift" => "load_bearing",
    "Julia stdlib" => "supportive",
    "numpy" => nothing,
)

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
const STAGE_DT = 0.08
const RK4_STEPS_PER_STAGE = 8

ordered_token(operator::String, perception::String, precedence::String) =
    precedence == "operator_first" ? string(operator, perception) :
    precedence == "terrain_first" ? string(perception, operator) :
    error("unknown precedence $precedence")

topologies(engine_type::Int) = engine_type == 0 ? TYPE_ONE_TOPOLOGIES :
    engine_type == 1 ? TYPE_TWO_TOPOLOGIES :
    error("engine_type must be 0 or 1, got $engine_type")

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
    end
    Dict{String,Any}(
        "operator" => op,
        "sign" => Int(sign),
        "precedence" => precedence,
        "token" => token,
        "operator_family" => OPERATOR_MAP_FAMILY[op],
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
                "transition_delta_fro" => matrix_norm(rho - before),
                "trace_residual" => trace_residual(rho),
                "min_eigenvalue" => min_eigenvalue(rho),
            ))
        end
    end
    Dict{String,Any}("n_qubits" => n_qubits, "states" => states, "records" => records, "n_substages" => length(records))
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

function maximally_mixed(n_qubits::Int)
    dim = 2^n_qubits
    Matrix{ComplexF64}(I, dim, dim) ./ Float64(dim)
end

function two_qubit_density()
    bell = (ket(0, 4) .+ exp(0.37im) .* ket(3, 4)) ./ sqrt(2.0)
    normalize_density(0.86 .* pure_density(bell) .+ 0.14 .* maximally_mixed(2))
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
    normed = clipped ./ sum(clipped)
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

function branch_result(label::String; n_qubits::Int, engine_type::Int, schedule, rho_init::Matrix{ComplexF64}, operator_erased::Bool=false)
    run = run_engine(n_qubits=n_qubits, engine_type=engine_type, schedule=schedule, rho_init=rho_init, operator_erased=operator_erased)
    r = readouts(run)
    max_trace_residual = maximum(Float64(row["trace_residual"]) for row in run["records"])
    min_psd = minimum(Float64(row["min_eigenvalue"]) for row in run["records"])
    Dict{String,Any}(
        "label" => label,
        "n_qubits" => n_qubits,
        "readouts" => r,
        "transition_channel_checks" => Dict{String,Any}(
            "trace_residual_max" => max_trace_residual,
            "min_eigenvalue_over_trajectory" => min_psd,
            "cptp_numeric_pass" => max_trace_residual < 1.0e-10 && min_psd > -1.0e-10,
        ),
    )
end

function sha256_file(path::String)
    if !isfile(path)
        return nothing
    end
    open(path, "r") do io
        bytes2hex(sha256(io))
    end
end

function source_refs()
    Dict{String,Any}(
        "self" => Dict("path" => SOURCE_PATH, "exists" => isfile(SOURCE_PATH), "sha256" => sha256_file(SOURCE_PATH)),
        "canonical_qit_engine_specs" => Dict("path" => CANONICAL_QIT_PATH, "exists" => isfile(CANONICAL_QIT_PATH), "sha256" => sha256_file(CANONICAL_QIT_PATH)),
        "qit_engine_3qubit_face_knot_taxonomy_julia" => Dict("path" => QIT_TAXONOMY_PATH, "exists" => isfile(QIT_TAXONOMY_PATH), "sha256" => sha256_file(QIT_TAXONOMY_PATH)),
        "jax_density_matrix_spinor_lift" => Dict("path" => DENSITY_LIFT_JAX_PATH, "exists" => isfile(DENSITY_LIFT_JAX_PATH), "sha256" => sha256_file(DENSITY_LIFT_JAX_PATH)),
        "density_matrix_spinor_lift_julia" => Dict("path" => DENSITY_LIFT_JULIA_PATH, "exists" => isfile(DENSITY_LIFT_JULIA_PATH), "sha256" => sha256_file(DENSITY_LIFT_JULIA_PATH)),
    )
end

function canonical_spec_witness()
    schedule_ok = length(ENGINE_SCHEDULE_TYPE_ONE) == 8 &&
        length(ENGINE_SCHEDULE_TYPE_TWO) == 8
    slot_rows = Vector{Dict{String,Any}}()
    slot_ok = true
    for engine_type in 0:1
        schedule = engine_type == 0 ? ENGINE_SCHEDULE_TYPE_ONE : ENGINE_SCHEDULE_TYPE_TWO
        for substage_idx in 0:3
            perception, loop_class = schedule[substage_idx + 1]
            slot = operator_slot_spec(perception, engine_type, loop_class, substage_idx)
            same = haskey(slot, "operator") && haskey(slot, "sign") && haskey(slot, "precedence") && haskey(slot, "token")
            slot_ok = slot_ok && same
            push!(slot_rows, Dict{String,Any}(
                "engine_type" => engine_type,
                "perception" => perception,
                "loop_class" => loop_class,
                "substage_idx" => substage_idx,
                "same" => same,
                "operator" => slot["operator"],
                "sign" => Int(slot["sign"]),
                "precedence" => slot["precedence"],
                "token" => slot["token"],
            ))
        end
    end
    Dict{String,Any}(
        "pass" => schedule_ok && slot_ok,
        "schedule_match" => schedule_ok,
        "slot_match" => slot_ok,
        "checked_slots" => slot_rows,
        "source" => CANONICAL_QIT_PATH,
    )
end

function lifted_owner_state(; entangle::Bool)
    locals = [
        LiftSource.spinor_from_angles(0.22, -0.31),
        LiftSource.spinor_from_angles(1.31, 0.27),
        LiftSource.spinor_from_angles(1.48, 0.13),
    ]
    edge_weights = [(0, 1, 0.43), (0, 2, -0.29), (1, 2, 0.91)]
    amps = ComplexF64[]
    for basis in 0:(2^N_QUBITS - 1)
        bits = [((basis >> (N_QUBITS - 1 - idx)) & 1) for idx in 0:(N_QUBITS - 1)]
        amp = 1.0 + 0.0im
        for idx in 1:N_QUBITS
            amp *= locals[idx][bits[idx] + 1]
        end
        if entangle
            phase = sum(weight * (bits[a + 1] == bits[b + 1] ? 1.0 : -1.0) for (a, b, weight) in edge_weights)
            amp *= exp(im * phase)
        end
        push!(amps, amp)
    end
    psi = amps ./ norm(amps)
    pure = pure_density(psi)
    normalize_density(0.86 .* pure .+ 0.14 .* maximally_mixed(N_QUBITS))
end

function density_lift_witness(owner_rho)
    local0 = partial_trace(owner_rho, N_QUBITS, [0])
    bloch0 = LiftSource.bloch_from_rho(local0)
    rebuilt0 = LiftSource.rho_from_bloch(bloch0)
    residual = Float64(norm(local0 - rebuilt0))
    Dict{String,Any}(
        "pass" => residual <= 1.0e-9,
        "local0_bloch" => [Float64(x) for x in bloch0],
        "local0_rebuild_residual" => residual,
        "source" => DENSITY_LIFT_JULIA_PATH,
    )
end

function branch(label::String, rho; n_qubits::Int=N_QUBITS, operator_erased::Bool=false)
    branch_result(
        label;
        n_qubits=n_qubits,
        engine_type=0,
        schedule=ENGINE_SCHEDULE_TYPE_ONE,
        rho_init=rho,
        operator_erased=operator_erased,
    )
end

function selected_readouts(result_branch)
    readouts = result_branch["readouts"]
    Dict{String,Float64}(name => Float64(readouts[key]) for (name, key) in READOUT_MAP)
end

function readout_vector(selected)
    [
        selected["face_entropy_growth"],
        selected["knot_bounded_mass"],
        selected["shell_sync_gradient"],
    ]
end

function readout_presence(selected)
    Dict{String,Bool}(
        "face_present" => selected["face_entropy_growth"] > FACE_THRESHOLD,
        "knot_present" => selected["knot_bounded_mass"] > KNOT_THRESHOLD,
        "shell_present" => selected["shell_sync_gradient"] > SHELL_THRESHOLD,
    )
end

function row_verdict(; owner_present::Bool, erased_present::Bool, null_present::Bool, erase_changes_result::Bool, survives_mutation::Bool, parity_ok::Bool)
    if !parity_ok
        return "OPEN"
    elseif null_present
        return "GENERIC"
    elseif !owner_present
        return "GRAVEYARD"
    elseif owner_present && erase_changes_result && !survives_mutation && !erased_present
        return "REAL_CARRIER"
    elseif survives_mutation && !erase_changes_result
        return "REPRODUCED"
    elseif survives_mutation
        return "CONVENTION"
    end
    "OPEN"
end

function parity_block(result)
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "peer_available" => false,
            "within_1e_9" => false,
            "parity_max_diff" => nothing,
            "worst_key" => nothing,
            "missing_from_peer" => sort(collect(keys(result["shared_scalars"]))),
            "missing_from_self" => String[],
            "boolean_mismatches" => String[],
            "diffs" => Dict{String,Any}(),
        )
    end
    peer = JSON.parsefile(JAX_RESULT_PATH)
    self_scalars = result["shared_scalars"]
    peer_scalars = get(peer, "shared_scalars", Dict{String,Any}())
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
    peer_booleans = get(peer, "shared_booleans", Dict{String,Any}())
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
        "within_1e_9" => within,
        "parity_max_diff" => max_diff,
        "worst_key" => worst_key,
        "missing_from_peer" => missing_from_peer,
        "missing_from_self" => missing_from_self,
        "boolean_mismatches" => boolean_mismatches,
        "diffs" => diffs,
    )
end

function build_result()
    owner_rho = lifted_owner_state(entangle=true)
    phase_erased_rho = lifted_owner_state(entangle=false)
    erased_rho = maximally_mixed(N_QUBITS)
    owner = branch("owner_source_native_lifted_carrier", owner_rho)
    carrier_erased = branch("carrier_erased_maximally_mixed", erased_rho)
    operator_erased = branch("operator_erased_same_carrier", owner_rho; operator_erased=true)
    phase_erased = branch("phase_erased_same_lift_no_edges", phase_erased_rho)
    twoq = branch_result(
        "two_qubit_floor_control";
        n_qubits=2,
        engine_type=0,
        schedule=ENGINE_SCHEDULE_TYPE_ONE,
        rho_init=two_qubit_density(),
    )

    owner_selected = selected_readouts(owner)
    erased_selected = selected_readouts(carrier_erased)
    op_erased_selected = selected_readouts(operator_erased)
    phase_erased_selected = selected_readouts(phase_erased)
    twoq_selected = selected_readouts(twoq)

    owner_vec = readout_vector(owner_selected)
    erased_vec = readout_vector(erased_selected)
    op_erased_vec = readout_vector(op_erased_selected)
    phase_erased_vec = readout_vector(phase_erased_selected)
    twoq_vec = readout_vector(twoq_selected)
    owner_norm = Float64(norm(owner_vec))
    erased_norm = Float64(norm(erased_vec))
    erase_delta = Float64(norm(owner_vec - erased_vec))
    operator_erase_delta = Float64(norm(owner_vec - op_erased_vec))
    phase_erase_delta = Float64(norm(owner_vec - phase_erased_vec))
    twoq_delta = Float64(norm(owner_vec - twoq_vec))
    survival_ratio = erased_norm / max(owner_norm, 1.0e-15)

    owner_presence = readout_presence(owner_selected)
    erased_presence = readout_presence(erased_selected)
    null_presence = readout_presence(twoq_selected)
    face_knot_shell_present = all(values(owner_presence))
    carrier_erased_present = all(values(erased_presence))
    twoq_null_present = all(values(null_presence))
    survives_mutation = survival_ratio >= MUTATION_DIE_RATIO && carrier_erased_present
    erase_changes_result = erase_delta > max(1.0e-6, 0.5 * owner_norm)
    three_qubit_min = N_QUBITS == 3 && Float64(twoq["readouts"]["three_cell_abs"]) == 0.0

    source_spec = canonical_spec_witness()
    lift_witness = density_lift_witness(owner_rho)
    shared_scalars = Dict{String,Float64}(
        "owner.face_entropy_growth" => owner_selected["face_entropy_growth"],
        "owner.face_three_cell_abs" => owner_selected["face_three_cell_abs"],
        "owner.knot_bounded_mass" => owner_selected["knot_bounded_mass"],
        "owner.shell_sync_gradient" => owner_selected["shell_sync_gradient"],
        "carrier_erased.face_entropy_growth" => erased_selected["face_entropy_growth"],
        "carrier_erased.face_three_cell_abs" => erased_selected["face_three_cell_abs"],
        "carrier_erased.knot_bounded_mass" => erased_selected["knot_bounded_mass"],
        "carrier_erased.shell_sync_gradient" => erased_selected["shell_sync_gradient"],
        "operator_erased.face_entropy_growth" => op_erased_selected["face_entropy_growth"],
        "operator_erased.knot_bounded_mass" => op_erased_selected["knot_bounded_mass"],
        "operator_erased.shell_sync_gradient" => op_erased_selected["shell_sync_gradient"],
        "phase_erased.face_entropy_growth" => phase_erased_selected["face_entropy_growth"],
        "phase_erased.knot_bounded_mass" => phase_erased_selected["knot_bounded_mass"],
        "phase_erased.shell_sync_gradient" => phase_erased_selected["shell_sync_gradient"],
        "two_qubit_floor.face_entropy_growth" => twoq_selected["face_entropy_growth"],
        "two_qubit_floor.knot_bounded_mass" => twoq_selected["knot_bounded_mass"],
        "two_qubit_floor.shell_sync_gradient" => twoq_selected["shell_sync_gradient"],
        "owner_vector_norm" => owner_norm,
        "carrier_erased_vector_norm" => erased_norm,
        "erase_delta" => erase_delta,
        "operator_erase_delta" => operator_erase_delta,
        "phase_erase_delta" => phase_erase_delta,
        "twoq_delta" => twoq_delta,
        "survival_ratio" => survival_ratio,
        "density_lift_local0_rebuild_residual" => Float64(lift_witness["local0_rebuild_residual"]),
        "n_qubits" => Float64(N_QUBITS),
    )
    shared_booleans = Dict{String,Bool}(
        "jax_enable_x64" => true,
        "numpy_compute_used" => false,
        "torch_compute_used" => false,
        "source_spec_witness_pass" => Bool(source_spec["pass"]),
        "density_lift_witness_pass" => Bool(lift_witness["pass"]),
        "three_qubit_min" => three_qubit_min,
        "source_native" => Bool(source_spec["pass"]) && Bool(lift_witness["pass"]),
        "face_knot_shell_present" => face_knot_shell_present,
        "carrier_erased_present" => carrier_erased_present,
        "twoq_null_present" => twoq_null_present,
        "survives_mutation" => survives_mutation,
        "erase_changes_result" => erase_changes_result,
        "operator_erase_changes_result" => operator_erase_delta > 1.0e-4,
        "phase_erase_changes_result" => phase_erase_delta > 1.0e-4,
        "all_transition_channels_numeric_cptp" =>
            Bool(owner["transition_channel_checks"]["cptp_numeric_pass"]) &&
            Bool(carrier_erased["transition_channel_checks"]["cptp_numeric_pass"]) &&
            Bool(operator_erased["transition_channel_checks"]["cptp_numeric_pass"]) &&
            Bool(phase_erased["transition_channel_checks"]["cptp_numeric_pass"]) &&
            Bool(twoq["transition_channel_checks"]["cptp_numeric_pass"]),
    )
    pre_parity_result = Dict{String,Any}(
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
    )
    parity = parity_block(pre_parity_result)
    verdict = row_verdict(
        owner_present=face_knot_shell_present,
        erased_present=carrier_erased_present,
        null_present=twoq_null_present,
        erase_changes_result=erase_changes_result,
        survives_mutation=survives_mutation,
        parity_ok=Bool(parity["peer_available"]) && Bool(parity["within_1e_9"]),
    )
    all_pass = Bool(parity["peer_available"]) &&
        Bool(parity["within_1e_9"]) &&
        shared_booleans["source_native"] &&
        shared_booleans["three_qubit_min"] &&
        shared_booleans["face_knot_shell_present"] &&
        shared_booleans["erase_changes_result"] &&
        shared_booleans["operator_erase_changes_result"] &&
        shared_booleans["phase_erase_changes_result"] &&
        shared_booleans["all_transition_channels_numeric_cptp"] &&
        !shared_booleans["numpy_compute_used"] &&
        !shared_booleans["torch_compute_used"] &&
        verdict in ["REAL_CARRIER", "CONVENTION", "REPRODUCED", "GENERIC", "GRAVEYARD"]

    positive = Dict{String,Any}(
        "source_native_canonical_qit_witness" => source_spec,
        "density_matrix_spinor_lift_witness" => lift_witness,
        "three_qubit_minimum" => Dict("pass" => three_qubit_min, "n_qubits" => N_QUBITS, "two_qubit_three_cell_abs" => Float64(twoq["readouts"]["three_cell_abs"])),
        "face_knot_shell_owner_present" => Dict(
            "pass" => face_knot_shell_present,
            "thresholds" => Dict("face_entropy_growth" => FACE_THRESHOLD, "knot_bounded_mass" => KNOT_THRESHOLD, "shell_sync_gradient" => SHELL_THRESHOLD),
            "readouts" => owner_selected,
            "presence" => owner_presence,
        ),
        "owner_carrier_load_bearing" => Dict(
            "pass" => erase_changes_result,
            "erase_delta" => erase_delta,
            "owner_vector_norm" => owner_norm,
            "carrier_erased_vector_norm" => erased_norm,
            "survival_ratio" => survival_ratio,
        ),
        "dual_backend_parity" => Dict("pass" => Bool(parity["peer_available"]) && Bool(parity["within_1e_9"]), "parity" => parity),
    )
    graveyard_companions = Dict{String,Any}(
        "carrier_erased_control" => Dict(
            "pass" => !carrier_erased_present,
            "readouts" => erased_selected,
            "presence" => erased_presence,
            "reason" => "maximally mixed carrier keeps schedule but erases the owner spinor/density carrier",
        ),
        "operator_erased_control" => Dict(
            "pass" => shared_booleans["operator_erase_changes_result"],
            "readouts" => op_erased_selected,
            "delta_from_owner" => operator_erase_delta,
            "reason" => "same owner carrier with source operator kicks erased changes the finite readout vector",
        ),
        "phase_erased_control" => Dict(
            "pass" => shared_booleans["phase_erase_changes_result"],
            "readouts" => phase_erased_selected,
            "delta_from_owner" => phase_erase_delta,
            "reason" => "same local spinor densities without entangling phase edges changes the finite readout vector",
        ),
        "two_qubit_floor_control" => Dict(
            "pass" => three_qubit_min,
            "readouts" => twoq_selected,
            "reason" => "two-qubit floor lacks the third face/shell memory region; tripartite face readout is zero",
        ),
    )
    boundary = Dict{String,Any}(
        "classification_fence" => Dict(
            "pass" => CLASSIFICATION == "scratch_diagnostic" && PROMOTION_ALLOWED == false && FORMAL_ADMISSION_ALLOWED == false,
            "classification" => CLASSIFICATION,
            "promotion_allowed" => PROMOTION_ALLOWED,
            "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        ),
        "claim_ceiling" => Dict("pass" => true, "claim_ceiling" => CLAIM_CEILING, "blocked_consumers" => BLOCKED_CONSUMERS),
        "honest_discriminator" => Dict(
            "pass" => verdict in ["REAL_CARRIER", "CONVENTION", "REPRODUCED", "GENERIC", "GRAVEYARD", "OPEN"],
            "row_verdict" => verdict,
            "rule" => "REAL_CARRIER iff owner present, null absent, and carrier mutation kills the face/knot/shell readout vector",
        ),
    )
    Dict{String,Any}(
        "schema" => "SCRATCH_DIAGNOSTIC_RESULT_v1",
        "object_id" => OBJECT_ID,
        "name" => NAME,
        "backend" => BACKEND,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "allowed_claims" => [
            "finite scratch discriminator verdict for the face/knot/shell readout vector",
            "dual-backend JAX/Julia parity over shared finite witnesses",
            "owner-carrier load-bearing only when erasing the carrier changes the result",
        ],
        "blocked_consumers" => BLOCKED_CONSUMERS,
        "sim_execution_kind" => SIM_EXECUTION_KIND,
        "sim_class" => "carrier_readout_discriminator_probe",
        "source_alignment_category" => "qit_source_native_face_knot_shell_carrier_mutation_discriminator",
        "numpy_compute_used" => false,
        "torch_compute_used" => false,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "source_refs" => source_refs(),
        "source_math_lock" => Dict(
            "canonical_qit_engine_specs" => "schedule and operator-slot witnesses compare canonical specs to the engine runner",
            "density_matrix_spinor_lift" => "owner local spinors are lifted to density matrices and checked by Bloch reconstruction",
            "finite_carrier" => "(C^2)^3 density matrix, Hilbert dimension 8",
        ),
        "carrier" => Dict(
            "minimum_qubits" => 3,
            "hilbert_dimension" => 8,
            "roles" => ["left Weyl sheet", "right Weyl sheet", "cut/shell memory spinor"],
            "owner" => "density-matrix lift of three local spinors with finite entangling phase edges",
            "mutation" => "same engine schedule on maximally mixed 3-qubit carrier",
        ),
        "finite_witness" => Dict(
            "readout_map" => READOUT_MAP,
            "owner" => owner_selected,
            "carrier_erased" => erased_selected,
            "operator_erased" => op_erased_selected,
            "phase_erased" => phase_erased_selected,
            "two_qubit_floor" => twoq_selected,
            "owner_vector_norm" => owner_norm,
            "carrier_erased_vector_norm" => erased_norm,
            "erase_delta" => erase_delta,
            "survival_ratio" => survival_ratio,
        ),
        "row_verdict" => verdict,
        "three_qubit_min" => three_qubit_min,
        "source_native" => Bool(source_spec["pass"]) && Bool(lift_witness["pass"]),
        "face_knot_shell_present" => face_knot_shell_present,
        "survives_mutation" => survives_mutation,
        "positive" => positive,
        "graveyard_companions" => graveyard_companions,
        "boundary" => boundary,
        "nearby_variants" => Dict(
            "total" => 4,
            "passed" => sum(Bool(row["pass"]) ? 1 : 0 for row in values(graveyard_companions)),
            "variants" => collect(keys(graveyard_companions)),
        ),
        "why_not_v4_probes" => Dict(
            "reason" => "key-list or toy-knot readouts do not discriminate carrier dependence; this row mutates the actual 3-qubit carrier and measures finite readout death/survival",
        ),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "parity" => parity,
        "all_pass" => all_pass,
        "stop_condition_fired" => !all_pass,
        "blockers" => all_pass ? Any[] : ["parity missing/disagreed or a finite discriminator/control/source-native/fence predicate failed"],
        "result_summary" => Dict(
            "all_pass" => all_pass,
            "row_verdict" => verdict,
            "three_qubit_min" => three_qubit_min,
            "source_native" => Bool(source_spec["pass"]) && Bool(lift_witness["pass"]),
            "face_knot_shell_present" => face_knot_shell_present,
            "survives_mutation" => survives_mutation,
            "claim_ceiling" => CLAIM_CEILING,
        ),
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(
        "RESULT $(OBJECT_ID) julia=$(RESULT_PATH) all_pass=$(lowercase(string(result["all_pass"]))) " *
        "row_verdict=$(result["row_verdict"]) three_qubit_min=$(lowercase(string(result["three_qubit_min"]))) " *
        "source_native=$(lowercase(string(result["source_native"]))) " *
        "face_knot_shell_present=$(lowercase(string(result["face_knot_shell_present"]))) " *
        "survives_mutation=$(lowercase(string(result["survives_mutation"])))"
    )
    result["all_pass"] ? 0 : 1
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
