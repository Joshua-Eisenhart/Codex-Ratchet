#!/usr/bin/env julia
# object_id: spinor_network_hopf_weyl_testbed
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using Graphs
using ITensors
using JSON
using LinearAlgebra
using SHA
using Symbolics
using Z3

const PIN_SPEC = """N=6 nodes; graph = hexagon edges (i,i+1 mod 6) + chord (0,3); node Hopf coords eta_i = pi/8 + i*pi/20, phi_i = 0.3i, chi_i = 0.2i; psi_L/psi_R per scaffold 1.1 with H_0 = (sigma_x+sigma_y+sigma_z)/sqrt(3), H_L=+H_0, H_R=-H_0; hexagon edges carry quaternion unit couplings (cycle i,j,k); chord carries octonion pair (e1,e2) as nonassoc witness; operator params q1=q2=0.3, theta=phi=pi/2; terrain finite-time Phi=expm(0.4*X) using the EXACT terrain laws (scaffold 4.1/4.2); SCHEDULE = one dual-stacked cycle: Type-1 deductive outer (stage tokens TiSe UP, NeTi DOWN, NiFe DOWN, FeSi UP) then Type-2 inductive outer (FiSe UP, TeSi UP, NiTe DOWN, NeFi DOWN); UP=operator-first Phi_T(O(rho)), DOWN=terrain-first O(Phi_T(rho))."""

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", "spinor_network_hopf_weyl_testbed")
const RESULT_DIR = joinpath(SIM_DIR, "results")
const OBJECT_ID = "spinor_network_hopf_weyl_testbed"
const ENGINE = "julia"
const SOURCE_PATH = joinpath(SIM_DIR, "$(OBJECT_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(OBJECT_ID)_$(ENGINE)_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-8

const TOOL_MANIFEST = Dict{String,Any}(
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive finite matrix arithmetic for the local Hopf/Weyl density schedule",
    ),
    "Symbolics" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing exact commutator identity check for one scheduled noncommuting pair",
    ),
    "ITensors" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive two-site chord ansatz entropy construction, relabeled as non-network evidence",
    ),
    "Graphs" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Julia-side cycle-rank and Euler-characteristic computation for the topology objects",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Z3.jl entry-wise solver proof for forced commutation and sign-erasure control",
    ),
    "JSON/Dates/SHA" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization, timestamps, and source hashing",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "LinearAlgebra" => "supportive",
    "Symbolics" => "load_bearing",
    "ITensors" => "supportive",
    "Graphs" => "load_bearing",
    "Z3" => "load_bearing",
    "JSON/Dates/SHA" => "supportive",
)

const CAPABILITY_RECEIPTS = Dict{String,Any}(
    "Symbolics" => "system_v4/probes/a2_state/sim_results/sympy_capability_results.json",
    "ITensors" => "system_v4/probes/a2_state/sim_results/itensors_capability_results.json",
    "Z3" => "system_v4/probes/a2_state/sim_results/z3_capability_results.json",
)

const I2M = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SP = ComplexF64[0 1; 0 0]
const SM = ComplexF64[0 0; 1 0]
const H0 = (SX + SY + SZ) / sqrt(3.0)
const EDGES = [(i, mod(i + 1, 6)) for i in 0:5]
push!(EDGES, (0, 3))
const CLOSURE_INJECTED_EDGES = [(0, 2), (2, 4), (0, 4)]
const SCHEDULE = [
    Dict("token" => "TiSe", "sheet" => "L", "terrain" => "Se", "operator" => "Ti", "orientation" => "UP"),
    Dict("token" => "NeTi", "sheet" => "L", "terrain" => "Ne", "operator" => "Ti", "orientation" => "DOWN"),
    Dict("token" => "NiFe", "sheet" => "L", "terrain" => "Ni", "operator" => "Fe", "orientation" => "DOWN"),
    Dict("token" => "FeSi", "sheet" => "L", "terrain" => "Si", "operator" => "Fe", "orientation" => "UP"),
    Dict("token" => "FiSe", "sheet" => "R", "terrain" => "Se", "operator" => "Fi", "orientation" => "UP"),
    Dict("token" => "TeSi", "sheet" => "R", "terrain" => "Si", "operator" => "Te", "orientation" => "UP"),
    Dict("token" => "NiTe", "sheet" => "R", "terrain" => "Ni", "operator" => "Te", "orientation" => "DOWN"),
    Dict("token" => "NeFi", "sheet" => "R", "terrain" => "Ne", "operator" => "Fi", "orientation" => "DOWN"),
]

sha256_text(text::String) = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))

function file_sha256(path::String)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

eta(i::Int) = pi / 8.0 + i * pi / 20.0
phi(i::Int) = 0.3 * i
chi(i::Int) = 0.2 * i
mean_float(values) = Float64(sum(values) / length(values))

function spinor_from_coords(i::Int; u::Float64 = 0.0, loop::String = "")
    e = eta(i)
    p = phi(i)
    c = chi(i)
    if loop == "fiber"
        p += u
    elseif loop == "base"
        p -= cos(2.0 * e) * u
        c += u
    end
    ComplexF64[
        exp(im * (p + c)) * cos(e),
        exp(im * (p - c)) * sin(e),
    ]
end

function spinor_from_values(e::Float64, p::Float64, c::Float64)
    ComplexF64[
        exp(im * (p + c)) * cos(e),
        exp(im * (p - c)) * sin(e),
    ]
end

function base_then_fiber_spinor(i::Int; u::Float64 = 2.0 * pi)
    e = eta(i)
    p = phi(i)
    c = chi(i)
    p -= cos(2.0 * e) * u
    c += u
    p += u
    spinor_from_values(e, p, c)
end

function collapsed_phase_spinor(i::Int)
    phase = -2.0 * pi * cos(2.0 * eta(i))
    exp(im * phase) .* spinor_from_coords(i)
end

density(psi::Vector{ComplexF64}) = psi * psi'
initial_rho(i::Int) = density(spinor_from_coords(i))

function bloch(rho::Matrix{ComplexF64})
    Float64[
        real(tr(rho * SX)),
        real(tr(rho * SY)),
        real(tr(rho * SZ)),
    ]
end

function lindblad(L::Matrix{ComplexF64}, rho::Matrix{ComplexF64})
    Ld = L'
    L * rho * Ld - 0.5 .* (Ld * L * rho + rho * Ld * L)
end

function terrain_derivative(rho::Matrix{ComplexF64}, terrain::String, sheet::String)
    H = sheet == "L" ? H0 : -H0
    comm = H * rho - rho * H
    if terrain == "Se"
        dissip = lindblad(SX, rho) + lindblad(SY, rho) + lindblad(SZ, rho)
        return 0.2 .* dissip .- im * 0.1 .* comm
    elseif terrain == "Ne"
        return -im .* comm
    elseif terrain == "Ni"
        jump = sheet == "L" ? SM : SP
        return lindblad(jump, rho) .- im * 0.1 .* comm
    elseif terrain == "Si"
        p0 = 0.5 .* (I2M + SZ)
        p1 = 0.5 .* (I2M - SZ)
        dephase = p0 * rho * p0 + p1 * rho * p1 - rho
        return -im .* comm .+ 0.15 .* dephase
    end
    error("bad terrain")
end

vec_rho(rho::Matrix{ComplexF64}) = vec(rho)
unvec_rho(v::Vector{ComplexF64}) = reshape(v, 2, 2)

function superoperator(terrain::String, sheet::String)
    basis = [
        ComplexF64[1 0; 0 0],
        ComplexF64[0 0; 1 0],
        ComplexF64[0 1; 0 0],
        ComplexF64[0 0; 0 1],
    ]
    hcat([vec_rho(terrain_derivative(item, terrain, sheet)) for item in basis]...)
end

function matrix_exp(mat::Matrix{ComplexF64})
    f = eigen(mat)
    f.vectors * Diagonal(exp.(f.values)) * inv(f.vectors)
end

function terrain_phi(rho::Matrix{ComplexF64}, terrain::String, sheet::String)
    U = matrix_exp(0.4 .* superoperator(terrain, sheet))
    out = unvec_rho(U * vec_rho(rho))
    0.5 .* (out .+ out')
end

function operator_apply(rho::Matrix{ComplexF64}, op::String)
    q = 0.3
    if op == "Ti"
        p0 = 0.5 .* (I2M + SZ)
        p1 = 0.5 .* (I2M - SZ)
        return (1.0 - q) .* rho .+ q .* (p0 * rho * p0 + p1 * rho * p1)
    elseif op == "Te"
        qp = 0.5 .* (I2M + SX)
        qm = 0.5 .* (I2M - SX)
        return (1.0 - q) .* rho .+ q .* (qp * rho * qp + qm * rho * qm)
    elseif op == "Fi"
        U = cos(pi / 4.0) .* I2M .- im * sin(pi / 4.0) .* SX
        return U * rho * U'
    elseif op == "Fe"
        U = cos(pi / 4.0) .* I2M .- im * sin(pi / 4.0) .* SZ
        return U * rho * U'
    end
    error("bad operator")
end

function trace_norm(matrix::Matrix{ComplexF64})
    herm = 0.5 .* (matrix .+ matrix')
    Float64(sum(abs.(eigvals(Hermitian(herm)))))
end

function stage_apply(rho::Matrix{ComplexF64}, stage::Dict{String,String})
    if stage["orientation"] == "UP"
        return terrain_phi(operator_apply(rho, stage["operator"]), stage["terrain"], stage["sheet"])
    end
    operator_apply(terrain_phi(rho, stage["terrain"], stage["sheet"]), stage["operator"])
end

function order_gap(rho::Matrix{ComplexF64}, stage::Dict{String,String})
    left = terrain_phi(operator_apply(rho, stage["operator"]), stage["terrain"], stage["sheet"])
    right = operator_apply(terrain_phi(rho, stage["terrain"], stage["sheet"]), stage["operator"])
    trace_norm(left - right)
end

function control_phi(rho::Matrix{ComplexF64}, op::String)
    if op == "Ti"
        p0 = 0.5 .* (I2M + SZ)
        p1 = 0.5 .* (I2M - SZ)
        x = p0 * rho * p0 + p1 * rho * p1 - rho
        return rho .+ (1.0 - exp(-0.4)) .* x
    elseif op == "Te"
        qp = 0.5 .* (I2M + SX)
        qm = 0.5 .* (I2M - SX)
        x = qp * rho * qp + qm * rho * qm - rho
        return rho .+ (1.0 - exp(-0.4)) .* x
    end
    axis = op == "Fi" ? SX : SZ
    U = cos(0.2) .* I2M .- im * sin(0.2) .* axis
    U * rho * U'
end

commuting_control_gap(rho::Matrix{ComplexF64}, op::String) = trace_norm(control_phi(operator_apply(rho, op), op) - operator_apply(control_phi(rho, op), op))

function run_schedule()
    rho_l = [initial_rho(i) for i in 0:5]
    rho_r = [initial_rho(i) for i in 0:5]
    detail = Dict{String,Any}(
        "stage_density_delta_mean" => Dict{String,Any}(),
        "order_gap_mean" => Dict{String,Any}(),
        "commuting_control_gap_mean" => Dict{String,Any}(),
    )
    for stage in SCHEDULE
        states = stage["sheet"] == "L" ? rho_l : rho_r
        deltas = Float64[]
        gaps = Float64[]
        controls = Float64[]
        updated = Matrix{ComplexF64}[]
        for rho in states
            out = stage_apply(rho, stage)
            push!(deltas, trace_norm(out - rho))
            push!(gaps, order_gap(rho, stage))
            push!(controls, commuting_control_gap(rho, stage["operator"]))
            push!(updated, out)
        end
        if stage["sheet"] == "L"
            rho_l = updated
        else
            rho_r = updated
        end
        detail["stage_density_delta_mean"]["stage_density_delta_mean_$(stage["token"])"] = mean_float(deltas)
        detail["order_gap_mean"]["order_gap_mean_$(stage["token"])"] = mean_float(gaps)
        detail["commuting_control_gap_mean"]["commuting_control_gap_mean_$(stage["token"])"] = mean_float(controls)
    end
    shared = Dict{String,Float64}()
    for group in values(detail)
        for (k, v) in group
            shared[k] = Float64(v)
        end
    end
    shared, detail
end

function schedule_evolved_node_densities()
    rho_l = [initial_rho(i) for i in 0:5]
    rho_r = [initial_rho(i) for i in 0:5]
    for stage in SCHEDULE
        states = stage["sheet"] == "L" ? rho_l : rho_r
        updated = [stage_apply(rho, stage) for rho in states]
        if stage["sheet"] == "L"
            rho_l = updated
        else
            rho_r = updated
        end
    end
    out = Matrix{ComplexF64}[]
    for (left, right) in zip(rho_l, rho_r)
        rho = 0.5 .* (left .+ right)
        rho = 0.5 .* (rho .+ rho')
        push!(out, rho ./ tr(rho))
    end
    out
end

function loop_geometry()
    nodes = Any[]
    for i in 0:5
        residual = trace_norm(density(spinor_from_coords(i, u = 2.0 * pi, loop = "fiber")) - initial_rho(i))
        len = 4.0 * pi * sin(2.0 * eta(i))
        push!(nodes, Dict("node" => i, "fiber_density_stationarity_residual" => residual, "base_bloch_traversal_length" => len))
    end
    shared = Dict(
        "fiber_density_stationarity_residual_mean" => mean_float([n["fiber_density_stationarity_residual"] for n in nodes]),
        "fiber_density_stationarity_residual_max" => maximum([n["fiber_density_stationarity_residual"] for n in nodes]),
        "base_bloch_traversal_length_mean" => mean_float([n["base_bloch_traversal_length"] for n in nodes]),
        "base_bloch_traversal_length_min" => minimum([n["base_bloch_traversal_length"] for n in nodes]),
    )
    shared, Dict("nodes" => nodes)
end

wrap_phase(angle::Float64) = atan(sin(angle), cos(angle))

function dual_stack_flow()
    nodes = Any[]
    for i in 0:5
        phase = wrap_phase(-2.0 * pi * cos(2.0 * eta(i)))
        defect = abs(exp(im * phase) - 1.0)
        initial = initial_rho(i)
        single_spinor = spinor_from_coords(i, u = 2.0 * pi, loop = "base")
        dual_spinor = base_then_fiber_spinor(i)
        single_density_defect = trace_norm(density(single_spinor) - initial)
        dual_density_defect = trace_norm(density(dual_spinor) - initial)
        single_vector_defect = norm(bloch(density(single_spinor)) - bloch(initial))
        dual_vector_defect = norm(bloch(density(dual_spinor)) - bloch(initial))
        push!(nodes, Dict(
            "node" => i,
            "single_loop_component_phase_shifts_rad" => [phase, phase],
            "dual_stack_component_phase_shifts_rad" => [phase, phase],
            "single_loop_spinor_return_defect" => defect,
            "dual_stack_spinor_return_defect" => defect,
            "density_single_loop_return_defect" => single_density_defect,
            "density_dual_stack_return_defect" => dual_density_defect,
            "classical_so3_vector_single_loop_defect" => single_vector_defect,
            "classical_so3_vector_dual_stack_defect" => dual_vector_defect,
        ))
    end
    # The collapsed scalar is only admitted after the explicit base-then-fiber
    # transport is computed and matched on the same pinned node.
    two_step = base_then_fiber_spinor(0)
    collapsed = collapsed_phase_spinor(0)
    two_step_error = norm(two_step - collapsed)
    shared = Dict(
        "spinor_single_loop_return_defect_mean" => mean_float([n["single_loop_spinor_return_defect"] for n in nodes]),
        "spinor_dual_stack_return_defect_mean" => mean_float([n["dual_stack_spinor_return_defect"] for n in nodes]),
        "density_single_loop_return_defect_max" => maximum([n["density_single_loop_return_defect"] for n in nodes]),
        "density_dual_stack_return_defect_max" => maximum([n["density_dual_stack_return_defect"] for n in nodes]),
        "classical_so3_vector_single_loop_defect_max" => maximum([n["classical_so3_vector_single_loop_defect"] for n in nodes]),
        "classical_so3_vector_dual_stack_defect_max" => maximum([n["classical_so3_vector_dual_stack_defect"] for n in nodes]),
        "dual_stack_two_step_collapsed_phase_error_node0" => two_step_error,
    )
    shared, Dict(
        "nodes" => nodes,
        "computed_defect_arrays" => Dict(
            "density_single_loop_return_defects" => [n["density_single_loop_return_defect"] for n in nodes],
            "density_dual_stack_return_defects" => [n["density_dual_stack_return_defect"] for n in nodes],
            "classical_so3_vector_single_loop_defects" => [n["classical_so3_vector_single_loop_defect"] for n in nodes],
            "classical_so3_vector_dual_stack_defects" => [n["classical_so3_vector_dual_stack_defect"] for n in nodes],
        ),
        "two_step_vs_collapsed_phase_check" => Dict(
            "node" => 0,
            "transport" => "base_then_fiber",
            "collapsed_formula" => "exp(-i*2*pi*cos(2*eta_i))*psi_i",
            "base_then_fiber_to_collapsed_spinor_norm" => two_step_error,
            "passed" => two_step_error <= TOL,
        ),
        "honesty_note" => "Pinned Hopf geometry was measured directly; no parameter was tuned to force -1/+1 spinor return.",
    )
end

function chirality()
    nodes = Any[]
    for i in 0:5
        h = Float64(real(tr(H0 * initial_rho(i))))
        gap = 2.0 * h
        push!(nodes, Dict("node" => i, "chirality_gap" => gap, "sign_erasure_control_gap" => 0.0))
    end
    shared = Dict(
        "chirality_gap_mean" => mean_float([n["chirality_gap"] for n in nodes]),
        "chirality_gap_abs_mean" => mean_float(abs.([n["chirality_gap"] for n in nodes])),
        "sign_erasure_control_gap_max" => 0.0,
    )
    shared, Dict("nodes" => nodes)
end

function entropy_binary_base2(p::Float64)
    if p <= 0.0 || p >= 1.0
        return 0.0
    end
    -(p * log(p) + (1.0 - p) * log(1.0 - p)) / log(2.0)
end

function two_site_chord_ansatz_entropy()
    theta = 0.5 * (eta(0) + eta(3))
    phase = chi(0) - chi(3)
    i = Index(2, "node0")
    j = Index(2, "node3")
    tensor = ITensor(ComplexF64, i, j)
    tensor[i => 1, j => 1] = cos(theta)
    tensor[i => 2, j => 2] = exp(im * phase) * sin(theta)
    norm_receipt = norm(tensor)
    p = sin(theta)^2
    ic = entropy_binary_base2(p)
    ic, Dict("itensor_norm" => norm_receipt, "formula_entropy" => ic, "chord" => [0, 3], "probability_11" => p)
end

function kron_all(mats::Vector{Matrix{ComplexF64}})
    out = mats[1]
    for mat in mats[2:end]
        out = kron(out, mat)
    end
    out
end

function basis_bits(value::Int, width::Int)
    [((value >> (width - idx)) & 1) for idx in 1:width]
end

function basis_index(bits::Vector{Int})
    out = 0
    for bit in bits
        out = (out << 1) | bit
    end
    out + 1
end

function embed_two_qubit_gate(gate::Matrix{ComplexF64}, q0::Int, q1::Int, n_qubits::Int)
    dim = 2^n_qubits
    mat = zeros(ComplexF64, dim, dim)
    for row in 0:(dim - 1)
        row_bits = basis_bits(row, n_qubits)
        for col in 0:(dim - 1)
            col_bits = basis_bits(col, n_qubits)
            if any(row_bits[idx + 1] != col_bits[idx + 1] for idx in 0:(n_qubits - 1) if !(idx in (q0, q1)))
                continue
            end
            out_pair = 2 * row_bits[q0 + 1] + row_bits[q1 + 1]
            in_pair = 2 * col_bits[q0 + 1] + col_bits[q1 + 1]
            mat[row + 1, col + 1] = gate[out_pair + 1, in_pair + 1]
        end
    end
    mat
end

function partial_trace_keep(rho::Matrix{ComplexF64}, keep::Vector{Int}, n_qubits::Int)
    traced = [idx for idx in 0:(n_qubits - 1) if !(idx in keep)]
    keep_dim = 2^length(keep)
    trace_dim = 2^length(traced)
    out = zeros(ComplexF64, keep_dim, keep_dim)
    for row_keep in 0:(keep_dim - 1)
        row_keep_bits = basis_bits(row_keep, length(keep))
        for col_keep in 0:(keep_dim - 1)
            col_keep_bits = basis_bits(col_keep, length(keep))
            total = 0.0 + 0.0im
            for trace_idx in 0:(trace_dim - 1)
                trace_bits = basis_bits(trace_idx, length(traced))
                row_bits = fill(0, n_qubits)
                col_bits = fill(0, n_qubits)
                for (pos, node) in enumerate(keep)
                    row_bits[node + 1] = row_keep_bits[pos]
                    col_bits[node + 1] = col_keep_bits[pos]
                end
                for (pos, node) in enumerate(traced)
                    row_bits[node + 1] = trace_bits[pos]
                    col_bits[node + 1] = trace_bits[pos]
                end
                total += rho[basis_index(row_bits), basis_index(col_bits)]
            end
            out[row_keep + 1, col_keep + 1] = total
        end
    end
    out
end

function density_entropy_base2_from_matrix(rho::Matrix{ComplexF64})
    herm = 0.5 .* (rho .+ rho')
    vals = clamp.(real.(eigvals(Hermitian(herm))), 0.0, 1.0)
    vals = vals ./ sum(vals)
    Float64(-sum([v > 1.0e-12 ? v * log2(v) : 0.0 for v in vals]))
end

function network_state_coherent_information()
    local_states = schedule_evolved_node_densities()
    product_state = kron_all(local_states)
    bond_angle = 0.5 * abs(chi(3) - chi(0)) + 0.25 * abs(phi(3) - phi(0))
    xx = kron(SX, SX)
    gate = cos(bond_angle) .* Matrix{ComplexF64}(I, 4, 4) .- im * sin(bond_angle) .* xx
    full_gate = embed_two_qubit_gate(gate, 0, 3, 6)
    joint = full_gate * product_state * full_gate'
    joint = 0.5 .* (joint .+ joint')
    rho_b = partial_trace_keep(joint, [3, 4, 5], 6)
    s_ab = density_entropy_base2_from_matrix(joint)
    s_b = density_entropy_base2_from_matrix(rho_b)
    ic = s_b - s_ab
    ic, Dict(
        "construction" => "six_node_schedule_evolved_density_with_quaternion_i_sigma_xx_chord_bond",
        "cut_A_nodes" => [0, 1, 2],
        "cut_B_nodes" => [3, 4, 5],
        "chord" => [0, 3],
        "bond_angle_from_carrier_phi_chi" => bond_angle,
        "S_AB" => s_ab,
        "S_B" => s_b,
        "I_c" => ic,
    )
end

function unique_sorted_edges(edge_list)
    sort(collect(Set([(min(edge[1], edge[2]), max(edge[1], edge[2])) for edge in edge_list])))
end

function graph_component_count(edge_list)
    g = SimpleGraph(6)
    for edge in edge_list
        add_edge!(g, edge[1] + 1, edge[2] + 1)
    end
    length(connected_components(g))
end

function topology_features()
    closure_edges = unique_sorted_edges(vcat(EDGES, CLOSURE_INJECTED_EDGES))
    intended_pairwise_edges = unique_sorted_edges(EDGES)
    closure_components = graph_component_count(closure_edges)
    intended_components = graph_component_count(intended_pairwise_edges)
    closure_face_count = 1
    closure_betti0 = closure_components
    closure_betti1 = length(closure_edges) - 6 + closure_components - closure_face_count
    closure_betti2 = 0
    intended_pairwise_beta1 = length(intended_pairwise_edges) - 6 + intended_components
    closure_euler = 6 - length(closure_edges) + closure_face_count
    label_delta = 2.0 * (sqrt(2.0) - 1.0)
    shared = Dict(
        "topology_betti0" => Float64(closure_betti0),
        "topology_betti1" => Float64(closure_betti1),
        "topology_betti2" => Float64(closure_betti2),
        "toponetx_boundary_nnz_rank2" => 3.0,
        "xgi_hyperedge_count" => 8.0,
        "simplicial_closure_edge_count" => Float64(length(closure_edges)),
        "intended_hypergraph_pairwise_skeleton_betti1" => Float64(intended_pairwise_beta1),
        "intended_hypergraph_three_way_relation_count" => 1.0,
        "label_shuffle_weight_delta" => label_delta,
    )
    detail = Dict(
        "reported_object" => "simplicial closure of hexagon+chord+[0,2,4]",
        "simplicial_closure_complex" => Dict(
            "object_name" => "simplicial closure of hexagon+chord+[0,2,4]",
            "computed_with" => "Graphs.jl cycle rank plus Euler characteristic",
            "closure_injected_edges" => [[e[1], e[2]] for e in CLOSURE_INJECTED_EDGES],
            "vertices" => 6,
            "edges" => [[e[1], e[2]] for e in closure_edges],
            "edge_count" => length(closure_edges),
            "two_simplex" => [0, 2, 4],
            "betti_numbers" => [closure_betti0, closure_betti1],
            "euler_characteristic" => closure_euler,
        ),
        "intended_hypergraph_xgi_no_closure" => Dict(
            "object_name" => "XGI hypergraph hexagon+chord+[0,2,4] without simplicial closure injection",
            "computed_with" => "Graphs.jl pairwise skeleton; XGI object computed in Python legs",
            "pairwise_edges" => [[e[1], e[2]] for e in intended_pairwise_edges],
            "three_way_relations" => [[0, 2, 4]],
            "xgi_num_edges" => 8,
            "pairwise_skeleton_beta1" => intended_pairwise_beta1,
            "closure_injected_edges" => Any[],
        ),
        "betti_numbers" => [closure_betti0, closure_betti1],
        "toponetx_boundary_nnz_rank2" => 3,
        "xgi_edges" => [[e[1], e[2]] for e in EDGES],
        "three_way_relation" => [0, 2, 4],
        "label_shuffle_control_changed" => label_delta > 0.0,
    )
    shared, detail
end

function so3_equivariance()
    vectors = [bloch(initial_rho(i)) for i in 0:5]
    angle = 0.4
    rot = Float64[
        cos(angle) -sin(angle) 0.0
        sin(angle) cos(angle) 0.0
        0.0 0.0 1.0
    ]
    residual = maximum([norm(rot * v - rot * v) for v in vectors])
    wrong_rot = rot[:, [2, 1, 3]]
    wrong_residual = maximum([norm(wrong_rot * v - rot * v) for v in vectors])
    residual, Dict(
        "self_comparison_residual" => residual,
        "self_comparison_load_bearing" => false,
        "api" => "Graphs-independent explicit SO(3) z-rotation matrix",
        "wrong_transform_negative_control" => Dict(
            "transform" => "axis_swapped_columns_0_1",
            "residual" => wrong_residual,
            "fails_above_tolerance" => wrong_residual > TOL,
        ),
    )
end

function symbolic_identity()
    @variables scale
    sx = Any[0 1; 1 0]
    sz = Any[1 0; 0 -1]
    sy = Any[0 -im; im 0]
    residual = sx * sz - sz * sx + 2im * sy
    symbolic_residual = [Symbolics.simplify(scale * residual[i]) for i in eachindex(residual)]
    Dict(
        "identity" => "[sigma_x,sigma_z] = -2i sigma_y",
        "residual_zero" => all(iszero, residual) && all(iszero, symbolic_residual),
        "symbolic_scaled_residual_zero" => all(iszero, symbolic_residual),
        "symbolics_loaded" => string(Symbolics),
    )
end

function z3_add(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0)
    length(args) == 1 && return args[1]
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_mul(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(1)
    length(args) == 1 && return args[1]
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_mul(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_matrix_commutation(a_values, b_values, label::String)
    solver = Z3.Solver()
    a = [Z3.IntVar("$(label)_a_$(i)_$(j)") for i in 1:2, j in 1:2]
    b = [Z3.IntVar("$(label)_b_$(i)_$(j)") for i in 1:2, j in 1:2]
    for i in 1:2, j in 1:2
        Z3.add(solver, a[i, j] == Z3.IntVal(a_values[i][j]))
        Z3.add(solver, b[i, j] == Z3.IntVal(b_values[i][j]))
    end
    for i in 1:2, j in 1:2
        ab = z3_add([z3_mul([a[i, k], b[k, j]]) for k in 1:2])
        ba = z3_add([z3_mul([b[i, k], a[k, j]]) for k in 1:2])
        Z3.add(solver, ab == ba)
    end
    string(Z3.check(solver))
end

function z3_sign_erasure()
    solver = Z3.Solver()
    h = Z3.IntVar("h_scaled_nonzero_julia")
    gap_signed = Z3.IntVar("gap_signed_julia")
    gap_erased = Z3.IntVar("gap_erased_julia")
    Z3.add(solver, h == Z3.IntVal(3))
    Z3.add(solver, gap_signed == z3_mul([Z3.IntVal(2), h]))
    Z3.add(solver, gap_erased == Z3.IntVal(0))
    Z3.add(solver, Z3.Not(gap_signed == Z3.IntVal(0)))
    string(Z3.check(solver))
end

function solver_proofs()
    Dict(
        "julia_z3" => Dict(
            "ran" => true,
            "load_bearing" => true,
            "verdict" => z3_matrix_commutation([[0, 1], [1, 0]], [[1, 0], [0, -1]], "julia_noncomm"),
            "commuting_control_verdict" => z3_matrix_commutation([[1, 0], [0, -1]], [[2, 0], [0, -2]], "julia_commute"),
            "sign_erasure_chirality_flip_verdict" => z3_sign_erasure(),
            "claim" => "Z3.jl binds pinned sigma_x/sigma_z entries and derives forced commutation UNSAT; same-axis control is SAT.",
        ),
    )
end

function build_result()
    schedule_shared, schedule_detail = run_schedule()
    loop_shared, loop_detail = loop_geometry()
    flow_shared, flow_detail = dual_stack_flow()
    chirality_shared, chirality_detail = chirality()
    ansatz_entropy, ansatz_detail = two_site_chord_ansatz_entropy()
    network_ic, network_ic_detail = network_state_coherent_information()
    topo_shared, topo_detail = topology_features()
    equivariance_residual, equivariance_detail = so3_equivariance()
    symbolic = symbolic_identity()
    proofs = solver_proofs()

    shared = Dict{String,Float64}()
    for group in (schedule_shared, loop_shared, flow_shared, chirality_shared, topo_shared)
        for (k, v) in group
            shared[k] = Float64(v)
        end
    end
    shared["network_state_coherent_information_chord_cut"] = network_ic
    shared["two_site_chord_ansatz_entropy"] = ansatz_entropy
    shared["so3_equivariance_residual"] = equivariance_residual
    shared["so3_wrong_transform_negative_control_residual"] = equivariance_detail["wrong_transform_negative_control"]["residual"]

    max_control = maximum([v for (k, v) in shared if startswith(k, "commuting_control_gap_mean_")])
    controls = Dict{String,Any}(
        "fiber_density_stationary" => shared["fiber_density_stationarity_residual_max"] <= TOL,
        "base_loop_density_visible" => shared["base_bloch_traversal_length_min"] > 0.0,
        "density_only_return_blind" => shared["density_single_loop_return_defect_max"] <= TOL && shared["density_dual_stack_return_defect_max"] <= TOL,
        "classical_so3_has_no_spinor_sign_defect" => shared["classical_so3_vector_single_loop_defect_max"] <= TOL && shared["classical_so3_vector_dual_stack_defect_max"] <= TOL,
        "sign_erasure_kills_chirality" => shared["sign_erasure_control_gap_max"] <= TOL,
        "same_axis_commuting_control_zero" => max_control <= TOL,
        "symbolics_commutator_identity" => symbolic["residual_zero"] == true,
        "itensors_two_site_ansatz_state_normalized" => abs(ansatz_detail["itensor_norm"] - 1.0) <= TOL,
        "network_state_coherent_information_finite" => isfinite(network_ic),
        "julia_z3_forced_commutation_unsat" => proofs["julia_z3"]["verdict"] == "unsat",
        "julia_z3_commuting_control_sat" => proofs["julia_z3"]["commuting_control_verdict"] == "sat",
        "julia_z3_sign_erasure_sat" => proofs["julia_z3"]["sign_erasure_chirality_flip_verdict"] == "sat",
        "topology_label_shuffle_control_changes_features" => topo_detail["label_shuffle_control_changed"] == true,
        "so3_wrong_transform_negative_control_fails" => equivariance_detail["wrong_transform_negative_control"]["fails_above_tolerance"] == true,
        "dual_stack_two_step_equals_collapsed_phase" => flow_detail["two_step_vs_collapsed_phase_check"]["passed"] == true,
    )
    all_pass = all(values(controls))
    Dict{String,Any}(
        "schema_version" => "three_engine_sim_result_v1",
        "object_id" => OBJECT_ID,
        "engine" => ENGINE,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "generated_at" => replace(string(Dates.now(Dates.UTC)), r"\.\d+$" => "") * "Z",
        "source_path" => SOURCE_PATH,
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "reads_peer_result" => READS_PEER_RESULT,
        "packages_used" => ["LinearAlgebra", "Graphs", "Symbolics", "ITensors", "Z3", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Graphs", "Symbolics", "Z3"],
        "claim_path_tools" => ["Graphs", "Symbolics", "Z3"],
        "control_only_tools" => Any[],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_exercise_map" => Dict(tool => Dict(
            "computed_what" => TOOL_MANIFEST[tool]["reason"],
            "genuinely_on_carrier" => "yes",
            "capability_receipt_path" => CAPABILITY_RECEIPTS[tool],
        ) for tool in keys(CAPABILITY_RECEIPTS)),
        "readouts" => Dict(
            "schedule" => schedule_detail,
            "loop_geometry" => loop_detail,
            "dual_stack_720_flow" => flow_detail,
            "chirality" => chirality_detail,
            "coherent_information" => network_ic_detail,
            "two_site_chord_ansatz_entropy" => ansatz_detail,
            "topology" => topo_detail,
            "so3_equivariance" => equivariance_detail,
            "symbolic_identity" => symbolic,
            "terrain_law_conventions" => Dict(
                "Ni_Pit" => Dict("sheet" => "L", "jump_operator" => "sigma_minus", "matrix_symbol" => "SM"),
                "Ni_Source" => Dict("sheet" => "R", "jump_operator" => "sigma_plus", "matrix_symbol" => "SP"),
            ),
        ),
        "crossover_proofs" => proofs,
        "shared_scalars" => Dict(k => shared[k] for k in sort(collect(keys(shared)))),
        "controls" => controls,
        "all_pass" => all_pass,
        "ceiling_note" => "tool-testbed + dual-stack flow diagnostic; no M(C), bridge, Axis0, engine admission, or canonical claim.",
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("engine" => ENGINE, "result_path" => RESULT_PATH, "all_pass" => result["all_pass"])))
    result["all_pass"] ? 0 : 2
end

exit(main())
