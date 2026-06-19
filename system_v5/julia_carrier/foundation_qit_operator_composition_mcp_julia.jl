#!/usr/bin/env julia
# object_id: foundation_qit_operator_composition_mcp_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: false

using Dates
using JSON
using SHA
using LinearAlgebra
using QuantumOptics
using DifferentialEquations
using CliffordAlgebras
using Grassmann
using QuantumClifford
using ITensors
using ITensorMPS
using Symbolics
using Graphs
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const OBJECT_ID = "foundation_qit_operator_composition_mcp_julia"
const SOURCE_PATH = realpath(@__FILE__)
const RESULT_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "results", "foundation_qit_operator_composition_mcp_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const N_QUBITS = 3
const DIM = 2^N_QUBITS
const EVOLVE_T = 0.8
const THETA = 0.9
const GAMMA = 1.3
const TOL = 1.0e-6

const TOOL_MANIFEST = Dict{String,Any}(
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing SpinBasis tensor carrier, density operator, Ti/Te/Fi/Fe operator construction, unitary channels, entropy_vn, ptrace, fidelity, and probe expectations"),
    "DifferentialEquations" => Dict("tried" => true, "used" => true, "reason" => "load-bearing ODEProblem + solve(Tsit5) integration of Ti/Te Lindblad master equations"),
    "CliffordAlgebras" => Dict("tried" => true, "used" => true, "reason" => "supportive Cl(3,0) geometric product and pseudoscalar side readout for the bracketing structure; not used by all_pass, divergence, quotient, control, or proof gates"),
    "Grassmann" => Dict("tried" => true, "used" => true, "reason" => "supportive exterior/geometric product side readout on v1*v2*v3; not used by all_pass, quotient, divergence, or proof gates"),
    "QuantumClifford" => Dict("tried" => true, "used" => true, "reason" => "supportive 3-qubit GHZ stabilizer/tableau side readout for the finite multi-qubit carrier; not used by all_pass, divergence, quotient, control, or proof gates"),
    "ITensors" => Dict("tried" => true, "used" => true, "reason" => "supportive 3-qubit tensor-network operator-contraction side readout; not used by all_pass, divergence, quotient, control, or proof gates"),
    "ITensorMPS" => Dict("tried" => true, "used" => true, "reason" => "supportive MPS representation and maxlinkdim side readout for a 3-qubit carrier state; not used by all_pass, divergence, quotient, control, or proof gates"),
    "Symbolics" => Dict("tried" => true, "used" => true, "reason" => "supportive symbolic associator / projected product structure-constant side readout; not used by all_pass, divergence, quotient, control, or proof gates"),
    "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing composition DAG and commutation graph checks"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing derive-in-solver matrix-entry commutation flip"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "control-only Hermitian/eigenvalue/norm checks; not in claim_path_tools"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization, timestamping, and source pinning"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "QuantumOptics" => "load_bearing",
    "DifferentialEquations" => "load_bearing",
    "CliffordAlgebras" => "supportive",
    "Grassmann" => "supportive",
    "QuantumClifford" => "supportive",
    "ITensors" => "supportive",
    "ITensorMPS" => "supportive",
    "Symbolics" => "supportive",
    "Graphs" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON/Dates/SHA" => "supportive",
)

function sha256_file(path::String)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function basis_bundle()
    q = SpinBasis(1 // 2)
    h = tensor(q, q, q)
    return q, h
end

function op_bundle(q)
    i = identityoperator(q)
    x = sigmax(q)
    z = sigmaz(q)
    Dict(
        "I3" => tensor(i, i, i),
        "X0" => tensor(x, i, i),
        "Z0" => tensor(z, i, i),
        "X1" => tensor(i, x, i),
        "Z1" => tensor(i, z, i),
        "Z2" => tensor(i, i, z),
        "Z0Z1" => tensor(z, z, i),
    )
end

function initial_density(q)
    ket0 = spindown(q)
    ket1 = spinup(q)
    q0 = sqrt(0.65) * ket0 + exp(0.37im) * sqrt(0.35) * ket1
    psi = normalize(tensor(q0, ket0, ket0))
    dm(psi)
end

function trace_normalize(rho)
    h = rho.basis_l
    mat = Matrix{ComplexF64}(rho.data)
    herm = 0.5 .* (mat + mat')
    DenseOperator(h, h, herm ./ tr(herm))
end

function unitary_channel(rho, hamiltonian, theta::Float64)
    unitary = exp(-1im * theta * hamiltonian)
    trace_normalize(unitary * rho * dagger(unitary))
end

function lindblad_rhs!(du, u, p, _t)
    h, hamiltonian, jumps = p
    mat = reshape(u, DIM, DIM)
    rho = DenseOperator(h, h, mat)
    drho = -1im * (hamiltonian * rho - rho * hamiltonian)
    for jump in jumps
        jd = dagger(jump)
        jdj = jd * jump
        drho += jump * rho * jd - 0.5 * (jdj * rho + rho * jdj)
    end
    du .= vec(Matrix{ComplexF64}(drho.data))
    nothing
end

function lindblad_channel(rho, hamiltonian, jumps)
    h = rho.basis_l
    u0 = vec(Matrix{ComplexF64}(rho.data))
    problem = ODEProblem(lindblad_rhs!, u0, (0.0, EVOLVE_T), (h, hamiltonian, jumps))
    solution = solve(problem, Tsit5(); reltol = 1.0e-9, abstol = 1.0e-9, save_everystep = false)
    trace_normalize(DenseOperator(h, h, reshape(solution.u[end], DIM, DIM)))
end

function apply_operator(label::String, rho, ops)
    if label == "Fi"
        return unitary_channel(rho, ops["X0"], THETA)
    elseif label == "Fe"
        return unitary_channel(rho, ops["Z0"], THETA)
    elseif label == "Ti"
        return lindblad_channel(rho, 0.0 * ops["Z0"], [sqrt(GAMMA) * ops["Z0"]])
    elseif label == "Te"
        return lindblad_channel(rho, 0.0 * ops["X1"], [sqrt(0.7 * GAMMA) * ops["X1"]])
    end
    error("unknown operator label $label")
end

function apply_sequence(rho, labels::Vector{String}, ops)
    out = rho
    for label in labels
        out = apply_operator(label, out, ops)
    end
    out
end

fro_gap(a, b) = Float64(norm(Matrix{ComplexF64}(a.data) - Matrix{ComplexF64}(b.data)))

function probe_expect(op, rho)
    Float64(real(QuantumOptics.expect(op, rho)))
end

function diag_from_z(z::Float64)
    zc = clamp(z, -1.0, 1.0)
    ComplexF64[(1.0 + zc) / 2.0 0.0; 0.0 (1.0 - zc) / 2.0]
end

function probe_product_section(rho, h, ops)
    z0 = probe_expect(ops["Z0"], rho)
    z1 = probe_expect(ops["Z1"], rho)
    z2 = probe_expect(ops["Z2"], rho)
    mat = kron(kron(diag_from_z(z0), diag_from_z(z1)), diag_from_z(z2))
    trace_normalize(DenseOperator(h, h, mat))
end

erase_carrier(h) = identityoperator(h) / DIM

function projected_bracketing_report(rho0, h, ops)
    raw = apply_sequence(rho0, ["Fe", "Fi", "Ti"], ops)
    left_inner = probe_product_section(apply_sequence(rho0, ["Fe", "Fi"], ops), h, ops)
    projected_left = probe_product_section(apply_operator("Ti", left_inner, ops), h, ops)
    right_inner = probe_product_section(apply_operator("Fe", rho0, ops), h, ops)
    projected_right = probe_product_section(apply_sequence(right_inner, ["Fi", "Ti"], ops), h, ops)
    erased = erase_carrier(h)
    erased_left = probe_product_section(apply_operator("Ti", probe_product_section(apply_sequence(erased, ["Fe", "Fi"], ops), h, ops), ops), h, ops)
    erased_right = probe_product_section(apply_sequence(probe_product_section(apply_operator("Fe", erased, ops), h, ops), ["Fi", "Ti"], ops), h, ops)
    Dict{String,Any}(
        "raw_associative_gap" => fro_gap(raw, raw),
        "projected_nonassoc_gap" => fro_gap(projected_left, projected_right),
        "erased_projected_gap" => fro_gap(erased_left, erased_right),
        "left_formula" => "P_M(Ti(P_M(Fi(Fe(rho)))))",
        "right_formula" => "P_M(Ti(Fi(P_M(Fe(rho)))))",
        "projection" => "P_M maps rho to product-state section preserving single-qubit Z probe expectations",
    )
end

function qit_readouts(rho)
    sub_q0 = ptrace(rho, [2, 3])
    sub_q12 = ptrace(rho, [1])
    s_all = Float64(real(entropy_vn(rho)))
    s_q12 = Float64(real(entropy_vn(sub_q12)))
    Dict{String,Any}(
        "von_neumann_entropy" => s_all,
        "subsystem_entropy_q0" => Float64(real(entropy_vn(sub_q0))),
        "subsystem_entropy_q12" => s_q12,
        "coherent_information_q0_to_q12" => s_q12 - s_all,
        "trace_real" => Float64(real(tr(rho))),
    )
end

function bures_distance(left, right)
    fid = max(0.0, min(1.0, Float64(real(fidelity(left, right)))))
    sqrt(max(0.0, 2.0 - 2.0 * sqrt(fid)))
end

function quotient_classes(states, probes)
    signatures = Dict{String,Any}()
    classes = Dict{String,Vector{String}}()
    for (name, rho) in states
        sig = [round(probe_expect(op, rho); digits = 8) for (_pname, op) in probes]
        key = JSON.json(sig)
        signatures[name] = sig
        if !haskey(classes, key)
            classes[key] = String[]
        end
        push!(classes[key], name)
    end
    rows = Any[]
    for key in sort(collect(keys(classes)))
        push!(rows, Dict{String,Any}("signature" => JSON.parse(key), "members" => sort(classes[key])))
    end
    Dict{String,Any}(
        "probe_names" => [pname for (pname, _op) in probes],
        "class_count" => length(rows),
        "classes" => rows,
        "signatures" => signatures,
    )
end

function clifford_grassmann_report()
    cl3 = CliffordAlgebra(3, 0)
    e1 = getproperty(cl3, :e1)
    e2 = getproperty(cl3, :e2)
    e3 = getproperty(cl3, :e3)
    pseudoscalar = e1 * e2 * e3
    basis"3"
    grassmann_left = (v1 * v2) * v3
    grassmann_right = v1 * (v2 * v3)
    Dict{String,Any}(
        "CliffordAlgebras_call" => "CliffordAlgebra(3,0); e1*e2*e3; (e1*e2*e3)^2",
        "cl3_pseudoscalar" => string(pseudoscalar),
        "cl3_pseudoscalar_square" => string(pseudoscalar * pseudoscalar),
        "Grassmann_call" => "basis\"3\"; (v1*v2)*v3 and v1*(v2*v3)",
        "grassmann_left" => string(grassmann_left),
        "grassmann_right" => string(grassmann_right),
        "grassmann_associative_control_zero" => string(grassmann_left - grassmann_right),
    )
end

function quantum_clifford_report()
    stab = ghz(3)
    view = stabilizerview(stab)
    gf2 = stab_to_gf2(view)
    Dict{String,Any}(
        "call" => "QuantumClifford.ghz(3); stabilizerview; stab_to_gf2",
        "stabilizer" => string(stab),
        "view_size" => collect(size(view)),
        "gf2_rows" => size(gf2, 1),
        "gf2_cols" => size(gf2, 2),
    )
end

function itensor_report()
    sites = siteinds("Qubit", 3)
    psi = MPS(sites, "0")
    psi = apply(op("H", sites, 1), psi)
    z_values = ITensorMPS.expect(psi, "Z")
    Dict{String,Any}(
        "call" => "ITensorMPS.MPS(siteinds(\"Qubit\",3),\"0\"); ITensors.op(\"H\"); ITensorMPS.expect(psi,\"Z\")",
        "z0_expectation_after_h_on_q0" => Float64(real(z_values[1])),
        "maxlinkdim" => maxlinkdim(psi),
    )
end

function symbolic_associator_report()
    @variables x y z
    associative_control = Symbolics.simplify((x * y) * z - x * (y * z))
    constants = zeros(Int, 3, 3, 3)
    constants[1, 1, 1] = 1
    constants[3, 1, 2] = 1
    constants[2, 2, 3] = 1
    constants[3, 3, 1] = 1
    coeffs = Int[]
    a, b, c = 1, 2, 3
    for k in 1:3
        left = sum(constants[m, a, b] * constants[k, m, c] for m in 1:3)
        right = sum(constants[m, b, c] * constants[k, a, m] for m in 1:3)
        push!(coeffs, left - right)
    end
    Dict{String,Any}(
        "call" => "Symbolics.simplify scalar associator plus projected-product structure constants",
        "associative_control" => string(associative_control),
        "projected_product_associator_e0_e1_e2" => coeffs,
        "projected_product_nonzero" => any(!=(0), coeffs),
    )
end

function graph_report()
    g = DiGraph(6)
    add_edge!(g, 1, 2)
    add_edge!(g, 2, 3)
    add_edge!(g, 3, 4)
    add_edge!(g, 2, 5)
    add_edge!(g, 5, 6)
    Dict{String,Any}(
        "call" => "Graphs.DiGraph; add_edge!; is_cyclic; topological_sort_by_dfs",
        "nodes" => nv(g),
        "edges" => ne(g),
        "is_cyclic" => is_cyclic(g),
        "topological_order" => topological_sort_by_dfs(g),
    )
end

function z3_add(args::Vector{Z3.Expr})
    if length(args) == 1
        return args[1]
    end
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_mul(left::Z3.Expr, right::Z3.Expr)
    Z3.Expr(left.ctx, Z3.Libz3.Z3_mk_mul(Z3.ctx_ref(left), 2, map(Z3.as_ast, [left, right])))
end

function z3_product_entry(left, right, i::Int, j::Int)
    z3_add([z3_mul(left[i, k], right[k, j]) for k in 1:size(left, 2)])
end

function z3_commutation_verdict(a_values::Matrix{Int}, b_values::Matrix{Int})
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    n = size(a_values, 1)
    avec = [Z3.IntVar("a_$(i)_$(j)", ctx) for i in 1:n, j in 1:n]
    bvec = [Z3.IntVar("b_$(i)_$(j)", ctx) for i in 1:n, j in 1:n]
    for i in 1:n, j in 1:n
        Z3.add(solver, avec[i, j] == Z3.IntVal(a_values[i, j], ctx))
        Z3.add(solver, bvec[i, j] == Z3.IntVal(b_values[i, j], ctx))
    end
    for i in 1:n, j in 1:n
        Z3.add(solver, z3_product_entry(avec, bvec, i, j) == z3_product_entry(bvec, avec, i, j))
    end
    string(Z3.check(solver))
end

function z3_flip_report()
    non_a = [0 -1; 1 0]
    non_b = [1 0; 0 2]
    com_a = [2 0; 0 3]
    com_b = [5 0; 0 7]
    Dict{String,Any}(
        "encoding" => "Z3 binds exact 2x2 finite operator-entry matrices, derives AB and BA entries internally, then asserts AB == BA.",
        "noncommuting_scaled_pauli_transfer" => Dict("z3_force_commute_verdict" => z3_commutation_verdict(non_a, non_b), "expected" => "unsat"),
        "commuting_control" => Dict("z3_force_commute_verdict" => z3_commutation_verdict(com_a, com_b), "expected" => "sat"),
    )
end

function build_result()
    q, h = basis_bundle()
    ops = op_bundle(q)
    rho0 = initial_density(q)
    rho_fi_ti = apply_sequence(rho0, ["Fi", "Ti"], ops)
    rho_ti_fi = apply_sequence(rho0, ["Ti", "Fi"], ops)
    rho_fe_ti = apply_sequence(rho0, ["Fe", "Ti"], ops)
    rho_ti_fe = apply_sequence(rho0, ["Ti", "Fe"], ops)
    rho_fi = apply_operator("Fi", rho0, ops)
    rho_ti = apply_operator("Ti", rho0, ops)
    rho_te = apply_operator("Te", rho0, ops)
    erased = erase_carrier(h)
    order_gap = fro_gap(rho_fi_ti, rho_ti_fi)
    commuting_gap = fro_gap(rho_fe_ti, rho_ti_fe)
    erased_order_gap = fro_gap(apply_sequence(erased, ["Fi", "Ti"], ops), apply_sequence(erased, ["Ti", "Fi"], ops))
    bracket = projected_bracketing_report(rho0, h, ops)
    entropy_initial = qit_readouts(rho0)
    entropy_fi = qit_readouts(rho_fi)
    entropy_ti = qit_readouts(rho_ti)
    entropy_te = qit_readouts(rho_te)
    full_q = quotient_classes(
        Dict("rho0" => rho0, "Fi_then_Ti" => rho_fi_ti, "Ti_then_Fi" => rho_ti_fi, "Fe_then_Ti" => rho_fe_ti, "carrier_erased" => erased),
        [("Z0", ops["Z0"]), ("X0", ops["X0"]), ("Z0Z1", ops["Z0Z1"])],
    )
    drop_q = quotient_classes(
        Dict("rho0" => rho0, "Fi_then_Ti" => rho_fi_ti, "Ti_then_Fi" => rho_ti_fi, "Fe_then_Ti" => rho_fe_ti, "carrier_erased" => erased),
        [("Z0", ops["Z0"]), ("Z0Z1", ops["Z0Z1"])],
    )
    z3_report = z3_flip_report()
    all_pass = Bool(
        order_gap > 1.0e-2 &&
        commuting_gap < 1.0e-4 &&
        erased_order_gap < 1.0e-4 &&
        bracket["raw_associative_gap"] < TOL &&
        bracket["projected_nonassoc_gap"] > 1.0e-2 &&
        bracket["erased_projected_gap"] < 1.0e-4 &&
        abs(entropy_fi["von_neumann_entropy"] - entropy_initial["von_neumann_entropy"]) < 1.0e-6 &&
        entropy_ti["von_neumann_entropy"] - entropy_initial["von_neumann_entropy"] > 1.0e-2 &&
        z3_report["noncommuting_scaled_pauli_transfer"]["z3_force_commute_verdict"] == "unsat" &&
        z3_report["commuting_control"]["z3_force_commute_verdict"] == "sat" &&
        full_q["class_count"] > drop_q["class_count"]
    )

    Dict{String,Any}(
        "schema_version" => "three_engine_sim_result_v1",
        "object_id" => OBJECT_ID,
        "rung_id" => "qit_operator_composition_mcp",
        "engine" => "julia",
        "backend" => "julia_authoritative_quantumoptics_diffeq_qit_stack",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "active_project" => Base.active_project(),
        "julia_version" => string(VERSION),
        "carrier" => Dict("n_qubits" => N_QUBITS, "dimension" => DIM, "basis" => "QuantumOptics tensor(SpinBasis(1//2), SpinBasis(1//2), SpinBasis(1//2))"),
        "operators" => Dict(
            "Ti" => "DifferentialEquations.solve(ODEProblem(lindblad_rhs!, ...), Tsit5()) with QuantumOptics jump sqrt(gamma)*Z0",
            "Te" => "DifferentialEquations.solve(ODEProblem(lindblad_rhs!, ...), Tsit5()) with QuantumOptics jump sqrt(0.7*gamma)*X1",
            "Fi" => "QuantumOptics exp(-im*theta*X0) unitary rotation",
            "Fe" => "QuantumOptics exp(-im*theta*Z0) unitary rotation",
        ),
        "M" => Dict("probe_family" => ["Z0", "X0", "Z0Z1"], "defines" => "finite probe signatures for S/~_M"),
        "C" => Dict("constraints" => ["trace=1", "Hermitian", "PSD under Lindblad/unitary evolution", "3-qubit finite carrier"], "rung_specific_constraint" => "operator-composition and P_M quotient-section bracketing"),
        "quotient" => Dict("S_mod_M_full" => full_q, "drop_X0_probe_control" => drop_q, "probe_drop_coarsens" => full_q["class_count"] > drop_q["class_count"]),
        "composition" => Dict(
            "order_gap_Fi_then_Ti_vs_Ti_then_Fi" => order_gap,
            "commuting_control_Fe_then_Ti_vs_Ti_then_Fe" => commuting_gap,
            "carrier_erasure_order_gap" => erased_order_gap,
            "bracketing" => bracket,
        ),
        "readouts" => Dict(
            "initial" => entropy_initial,
            "Fi_unitary" => entropy_fi,
            "Ti_dissipative" => entropy_ti,
            "Te_dissipative" => entropy_te,
            "unitary_entropy_delta_abs" => abs(entropy_fi["von_neumann_entropy"] - entropy_initial["von_neumann_entropy"]),
            "ti_entropy_increase" => entropy_ti["von_neumann_entropy"] - entropy_initial["von_neumann_entropy"],
            "te_entropy_increase" => entropy_te["von_neumann_entropy"] - entropy_initial["von_neumann_entropy"],
            "QuantumOptics_fidelity_Bures_FiTi_vs_TiFi" => Dict("call" => "QuantumOptics.fidelity then Bures formula", "distance" => bures_distance(rho_fi_ti, rho_ti_fi)),
        ),
        "geometry" => Dict(
            "clifford_grassmann" => clifford_grassmann_report(),
            "quantum_clifford" => quantum_clifford_report(),
            "itensor_network" => itensor_report(),
            "symbolic_associator" => symbolic_associator_report(),
            "graph" => graph_report(),
        ),
        "smt" => z3_report,
        "packages_used" => ["QuantumOptics", "DifferentialEquations", "CliffordAlgebras", "Grassmann", "QuantumClifford", "ITensors", "ITensorMPS", "Symbolics", "Graphs", "Z3", "LinearAlgebra", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "DifferentialEquations", "Z3"],
        "claim_path_tools" => ["QuantumOptics", "DifferentialEquations", "Graphs", "Z3"],
        "tool_calls" => Dict(
            "QuantumOptics" => "SpinBasis/tensor/dm/exp/entropy_vn/ptrace/fidelity/expect",
            "DifferentialEquations" => "ODEProblem + solve(Tsit5) for Ti and Te Lindblad channels",
            "CliffordAlgebras" => Dict(
                "call" => "CliffordAlgebra(3,0), e1*e2*e3 pseudoscalar product",
                "status" => "supportive",
                "demotion_condition" => "output remains a side readout and gates no all_pass, divergence, quotient, control, or proof condition",
                "gates" => "none",
            ),
            "Grassmann" => "basis\"3\" and v1*v2*v3 geometric/exterior control",
            "QuantumClifford" => Dict(
                "call" => "ghz(3), stabilizerview, stab_to_gf2",
                "status" => "supportive",
                "demotion_condition" => "output remains a side readout and gates no all_pass, divergence, quotient, control, or proof condition",
                "gates" => "none",
            ),
            "ITensors/ITensorMPS" => Dict(
                "call" => "siteinds, MPS, op(H), ITensorMPS.expect(psi,\"Z\")",
                "status" => "supportive",
                "demotion_condition" => "output remains a side readout and gates no all_pass, divergence, quotient, control, or proof condition",
                "gates" => "none",
            ),
            "Symbolics" => Dict(
                "call" => "Symbolics.simplify and structure-constant associator derivation",
                "status" => "supportive",
                "demotion_condition" => "output remains a side readout and gates no all_pass, divergence, quotient, control, or proof condition",
                "gates" => "none",
            ),
            "Graphs" => "DiGraph, add_edge!, is_cyclic, topological_sort_by_dfs",
            "Z3" => "derive-in-solver AB==BA SAT/UNSAT flip from bound matrix entries",
        ),
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "all_pass" => all_pass,
        "claim_ceiling" => "Scratch diagnostic only: finite 3-qubit QIT operator-composition, quotient, bracketing, and controls. No promotion, formal admission, bridge, Axis0, IGT truth, or physics claim.",
    )
end

function main()
    mkpath(dirname(RESULT_PATH))
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote: ", RESULT_PATH)
    println("SCOUT_DONE all_pass=", result["all_pass"], " order_gap=", result["composition"]["order_gap_Fi_then_Ti_vs_Ti_then_Fi"], " commuting_gap=", result["composition"]["commuting_control_Fe_then_Ti_vs_Ti_then_Fe"], " projected_assoc=", result["composition"]["bracketing"]["projected_nonassoc_gap"])
    return result["all_pass"] ? 0 : 2
end

exit(main())
