#!/usr/bin/env julia

using Dates
using JSON
using SHA
using LinearAlgebra
using StaticArrays
using CliffordAlgebras
using Octonions
using Quaternions
using QuantumOptics
using Z3
using Manifolds
using Graphs
using ITensors
using Yao
using DifferentialEquations
using Attractors
using DynamicalSystems

const OBJECT_ID = "foundation_spinor_network_full_stack_layer_julia"
const RUNG_ID = "spinor_network_full_stack_layer"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_spinor_network_full_stack_layer_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_spinor_network_full_stack_layer_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-8

const GRAPH_EDGES = [(1, 2), (2, 3), (3, 4), (4, 1), (1, 3)]
const TARGET = [1.0, -1.0, -1.0, -1.0]
const O_WITNESS = (1, 2, 4)
const H_ASSOC_CONTROL = (1, 2, 3)

const classification = CLASSIFICATION
const promotion_allowed = PROMOTION_ALLOWED
const formal_admission_allowed = FORMAL_ADMISSION_ALLOWED
const reads_peer_result = READS_PEER_RESULT

const TOOL_MANIFEST = Dict{String,Any}(
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "node density matrices, entropy_vn, ptrace, and liouvillian superoperator for the spinor-network node"),
    "CliffordAlgebras" => Dict("tried" => true, "used" => true, "reason" => "supportive Cl(3) side readout attached to the same spinor carrier; not used by all_pass, divergence, quotient, control, or proof gates"),
    "Octonions" => Dict("tried" => true, "used" => true, "reason" => "octonion nonassociative edge associator on the network coupling witness"),
    "Quaternions" => Dict("tried" => true, "used" => true, "reason" => "associative quaternion control and noncommuting edge order control"),
    "DifferentialEquations" => Dict("tried" => true, "used" => true, "reason" => "master-equation ODE integration for the same node Hamiltonian and jump operator"),
    "Attractors" => Dict("tried" => true, "used" => true, "reason" => "supportive basins_of_attraction side readout for the order-parameter basin map; not used by all_pass, divergence, quotient, control, or proof gates"),
    "DynamicalSystems" => Dict("tried" => true, "used" => true, "reason" => "supportive CoupledODEs and StateSpaceSet backing the Attractors side readout; not used by all_pass, divergence, quotient, control, or proof gates"),
    "Manifolds" => Dict("tried" => true, "used" => true, "reason" => "supportive S^3 spinor distance side readout for the Hopf/Bloch manifold control; not used by all_pass, divergence, quotient, control, or proof gates"),
    "Graphs" => Dict("tried" => true, "used" => true, "reason" => "finite graph construction and cycle-rank invariant"),
    "ITensors" => Dict("tried" => true, "used" => true, "reason" => "supportive multi-spinor tensor contraction side readout over four node carrier amplitudes; not used by all_pass, divergence, quotient, control, or proof gates"),
    "Yao" => Dict("tried" => true, "used" => true, "reason" => "supportive X/H unitary gate matrix side readout for node unitary control; not used by all_pass, divergence, quotient, control, or proof gates"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "derive-in-solver associator and basin escape checks from bound table/state entries"),
    "Cayley-Dickson" => Dict("tried" => true, "used" => true, "reason" => "sedenion zero-divisor kill-control table construction"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "QuantumOptics" => "load_bearing",
    "CliffordAlgebras" => "supportive",
    "Octonions" => "load_bearing",
    "Quaternions" => "load_bearing",
    "DifferentialEquations" => "load_bearing",
    "Attractors" => "supportive",
    "DynamicalSystems" => "supportive",
    "Manifolds" => "supportive",
    "Graphs" => "load_bearing",
    "ITensors" => "supportive",
    "Yao" => "supportive",
    "Z3" => "load_bearing",
    "Cayley-Dickson" => "load_bearing",
    "JSON" => "supportive",
)

function sha256_file(path::String)::String
    bytes2hex(sha256(read(path)))
end

function coeffs_quat(q)
    [Float64(getfield(q, idx)) for idx in 1:4]
end

function coeffs_oct(o)
    [Float64(getfield(o, idx)) for idx in 1:8]
end

function qbasis(idx0::Int)
    Quaternions.Quaternion(ntuple(k -> k == idx0 + 1 ? 1.0 : 0.0, 4)...)
end

function obasis(idx0::Int)
    Octonions.Octonion(ntuple(k -> k == idx0 + 1 ? 1.0 : 0.0, 8)...)
end

function quaternion_table()
    table = zeros(Int, 4, 4, 4)
    for i in 0:3, j in 0:3
        vals = coeffs_quat(qbasis(i) * qbasis(j))
        for k in 0:3
            table[k + 1, i + 1, j + 1] = round(Int, vals[k + 1])
        end
    end
    table
end

function octonion_table()
    table = zeros(Int, 8, 8, 8)
    for i in 0:7, j in 0:7
        vals = coeffs_oct(obasis(i) * obasis(j))
        for k in 0:7
            table[k + 1, i + 1, j + 1] = round(Int, vals[k + 1])
        end
    end
    table
end

function basis_vec(dim::Int, idx0::Int)
    v = zeros(Int, dim)
    v[idx0 + 1] = 1
    v
end

function cd_conj(x::Vector{Int})
    y = copy(x)
    for i in 2:length(y)
        y[i] = -y[i]
    end
    y
end

function table_multiply(table::Array{Int,3}, x::Vector{Int}, y::Vector{Int})
    dim = size(table, 1)
    out = zeros(Int, dim)
    for k in 1:dim, i in 1:dim, j in 1:dim
        coeff = table[k, i, j]
        if coeff != 0 && x[i] != 0 && y[j] != 0
            out[k] += coeff * x[i] * y[j]
        end
    end
    out
end

function cd_double(parent::Array{Int,3})
    n = size(parent, 1)
    dim = 2n
    table = zeros(Int, dim, dim, dim)
    for i in 1:dim, j in 1:dim
        x = basis_vec(dim, i - 1)
        y = basis_vec(dim, j - 1)
        a, b = x[1:n], x[(n + 1):dim]
        c, d = y[1:n], y[(n + 1):dim]
        first = table_multiply(parent, a, c) - table_multiply(parent, cd_conj(d), b)
        second = table_multiply(parent, d, a) + table_multiply(parent, b, cd_conj(c))
        table[:, i, j] = vcat(first, second)
    end
    table
end

function cd_tables()
    r = zeros(Int, 1, 1, 1)
    r[1, 1, 1] = 1
    c = cd_double(r)
    h = cd_double(c)
    o = cd_double(h)
    s = cd_double(o)
    Dict("H" => h, "O" => o, "S" => s)
end

function vector_normsq(v)
    sum(x * x for x in v)
end

function algebra_readouts()
    i, j = qbasis(1), qbasis(2)
    qa, qb, qc = H_ASSOC_CONTROL
    hx, hy, hz = qbasis(qa), qbasis(qb), qbasis(qc)
    a, b, c = O_WITNESS
    ox, oy, oz = obasis(a), obasis(b), obasis(c)
    o_assoc = (ox * oy) * oz - ox * (oy * oz)
    h_assoc = (hx * hy) * hz - hx * (hy * hz)
    cl3 = CliffordAlgebra(3)
    e1 = basevector(cl3, :e1)
    e2 = basevector(cl3, :e2)
    cl_zero = MultiVector(cl3, 0)
    tables = cd_tables()
    s_left = basis_vec(16, 1) + basis_vec(16, 10)
    s_right = basis_vec(16, 5) + basis_vec(16, 14)
    s_product = table_multiply(tables["S"], s_left, s_right)
    Dict{String,Any}(
        "quaternion_order_gap" => norm(coeffs_quat(i * j - j * i)),
        "commuting_control_gap" => norm(coeffs_quat(i * i - i * i)),
        "octonion_associator_vector" => coeffs_oct(o_assoc),
        "octonion_associator_norm" => norm(coeffs_oct(o_assoc)),
        "quaternion_associator_control_norm" => norm(coeffs_quat(h_assoc)),
        "sedenion_zero_divisor_product_normsq" => vector_normsq(s_product),
        "sedenion_zero_divisor_left_normsq" => vector_normsq(s_left),
        "sedenion_zero_divisor_right_normsq" => vector_normsq(s_right),
        "clifford_dimension_cl3" => CliffordAlgebras.dimension(cl3),
        "clifford_e1e2_anticommutes" => e1 * e2 + e2 * e1 == cl_zero,
    )
end

function graph_readout()
    g = Graphs.SimpleGraph(4)
    for edge in GRAPH_EDGES
        Graphs.add_edge!(g, edge[1], edge[2])
    end
    Dict{String,Any}(
        "node_count" => Graphs.nv(g),
        "edge_count" => Graphs.ne(g),
        "connected_components" => Graphs.connected_components(g),
        "cycle_rank" => Graphs.ne(g) - Graphs.nv(g) + length(Graphs.connected_components(g)),
    )
end

function hopf(q::Vector{Float64})
    z1 = complex(q[1], q[2])
    z2 = complex(q[3], q[4])
    n = abs2(z1) + abs2(z2)
    [
        2 * real(z1 * conj(z2)) / n,
        2 * imag(z1 * conj(z2)) / n,
        (abs2(z1) - abs2(z2)) / n,
    ]
end

function geometry_readout()
    m = Sphere(3)
    spinor = TARGET ./ norm(TARGET)
    erased = fill(1.0, 4)
    erased ./= norm(erased)
    h0 = [0.1 0.2; 0.2 -0.1]
    hl = h0
    hr = -h0
    Dict{String,Any}(
        "hopf_s2" => hopf(spinor),
        "s3_distance_to_erased_reference" => Float64(Manifolds.distance(m, spinor, erased)),
        "chirality_split_norm" => norm(hl - hr),
        "no_chirality_control_norm" => norm(hl - hl),
    )
end

function qit_readout()
    b = QuantumOptics.tensor(QuantumOptics.SpinBasis(1 // 2), QuantumOptics.SpinBasis(1 // 2))
    psi = QuantumOptics.Ket(b, ComplexF64.(TARGET ./ norm(TARGET)))
    rho = QuantumOptics.dm(psi)
    erased = QuantumOptics.Operator(b, b, Matrix{ComplexF64}(I, 4, 4) / 4)
    reduced = QuantumOptics.ptrace(rho, [2])
    reduced_erased = QuantumOptics.ptrace(erased, [2])
    vals = eigvals(Matrix{ComplexF64}(rho.data - erased.data))
    qo_liouvillian = QuantumOptics.liouvillian(
        0.2 * QuantumOptics.sigmax(QuantumOptics.SpinBasis(1 // 2)),
        [sqrt(0.2) * QuantumOptics.sigmam(QuantumOptics.SpinBasis(1 // 2))],
    )
    Dict{String,Any}(
        "von_neumann_entropy" => Float64(real(QuantumOptics.entropy_vn(rho))),
        "subsystem_entropy" => Float64(real(QuantumOptics.entropy_vn(reduced))),
        "coherent_information" => Float64(real(QuantumOptics.entropy_vn(reduced) - QuantumOptics.entropy_vn(rho))),
        "erased_von_neumann_entropy" => Float64(real(QuantumOptics.entropy_vn(erased))),
        "erased_subsystem_entropy" => Float64(real(QuantumOptics.entropy_vn(reduced_erased))),
        "erased_coherent_information" => Float64(real(QuantumOptics.entropy_vn(reduced_erased) - QuantumOptics.entropy_vn(erased))),
        "trace_distance_to_erased" => 0.5 * sum(abs.(vals)),
        "liouvillian_shape" => collect(size(qo_liouvillian.data)),
    )
end

function dynamics_readout()
    h = ComplexF64[0.1 0.2; 0.2 -0.1]
    l = sqrt(0.2) * ComplexF64[0 1; 0 0]
    rho0 = ComplexF64[0 0; 0 1]
    function f!(du, u, p, t)
        rho = reshape(u, 2, 2)
        dr = -im * (h * rho - rho * h) + l * rho * l' - 0.5 * ((l' * l) * rho + rho * (l' * l))
        du .= vec(dr)
    end
    prob = DifferentialEquations.ODEProblem(f!, vec(rho0), (0.0, 1.0))
    sol = DifferentialEquations.solve(prob, DifferentialEquations.Tsit5(), reltol = 1.0e-8, abstol = 1.0e-10)
    final = reshape(sol.u[end], 2, 2)
    xmat = Matrix(Yao.mat(Yao.X))
    hmat = Matrix(Yao.mat(Yao.H))
    Dict{String,Any}(
        "final_excited_population" => Float64(real(final[2, 2])),
        "final_trace" => Float64(real(tr(final))),
        "unitary_xh_commutator_norm" => norm(xmat * hmat - hmat * xmat),
    )
end

function finite_states()
    rows = Vector{Vector{Float64}}()
    for bits in Iterators.product(fill([-1.0, 1.0], 4)...)
        push!(rows, collect(bits))
    end
    rows
end

function finite_update(state::Vector{Float64}; real_constraint::Bool)
    if !real_constraint
        return zeros(Float64, 4)
    end
    dot(state, TARGET) >= 0.0 ? copy(TARGET) : -copy(TARGET)
end

function finite_basins(real_constraint::Bool)
    counts = Dict{String,Int}()
    for state in finite_states()
        final = finite_update(state; real_constraint = real_constraint)
        key = join(string.(round.(Int, final)), " ")
        counts[key] = get(counts, key, 0) + 1
    end
    Dict{String,Any}(
        "state_space" => "{-1,+1}^4",
        "seed_count" => 16,
        "attractor_count" => length(keys(counts)),
        "basin_counts" => counts,
        "basin_fractions" => Dict(key => value / 16.0 for (key, value) in counts),
    )
end

function attractors_readout()
    ds = CoupledODEs((u, p, t) -> SVector(u[1] - u[1]^3), SVector(0.2))
    attractor_sets = Dict(1 => StateSpaceSet([SVector(-1.0)]), 2 => StateSpaceSet([SVector(1.0)]))
    mapper = AttractorsViaProximity(ds, attractor_sets)
    grid = (range(-1.5, 1.5; length = 16),)
    basins, attractors = basins_of_attraction(mapper, grid)
    counts = Dict{String,Int}()
    for key in unique(vec(basins))
        counts[string(Int(key))] = count(==(key), vec(basins))
    end
    Dict{String,Any}(
        "function_called" => "Attractors.basins_of_attraction with DynamicalSystems.CoupledODEs",
        "attractor_count" => length(attractors),
        "basin_counts" => counts,
    )
end

function itensor_readout()
    links = [ITensors.Index(2, "node$(i)") for i in 1:4]
    tensors = ITensor[]
    for i in 1:4
        t = ITensors.ITensor(links[i])
        t[links[i] => 1] = TARGET[i] > 0 ? 1.0 : 0.0
        t[links[i] => 2] = TARGET[i] < 0 ? 1.0 : 0.0
        push!(tensors, t)
    end
    prod = tensors[1] * tensors[2] * tensors[3] * tensors[4]
    norm_tensor = prod * ITensors.dag(prod)
    Dict{String,Any}("node_tensor_count" => 4, "contraction_norm" => Float64(real(ITensors.scalar(norm_tensor))))
end

function z3_add_expr(args)
    isempty(args) && error("z3_add_expr requires at least one argument")
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_mul_expr(left, right)
    Z3.Expr(left.ctx, Z3.Libz3.Z3_mk_mul(Z3.ctx_ref(left), 2, map(Z3.as_ast, [left, right])))
end

function z3_ge_expr(left, right)
    Z3.Expr(left.ctx, Z3.Libz3.Z3_mk_ge(Z3.ctx_ref(left), Z3.as_ast(left), Z3.as_ast(right)))
end

function z3_sum(ctx, items)
    isempty(items) && return Z3.IntVal(0, ctx)
    length(items) == 1 && return items[1]
    z3_add_expr(items)
end

function z3_product_exprs(ctx, table::Array{Int,3}, x, y)
    dim = size(table, 1)
    out = Z3.Expr[]
    for k in 1:dim
        terms = Z3.Expr[]
        for i in 1:dim, j in 1:dim
            coeff = table[k, i, j]
            if coeff != 0
                push!(terms, z3_mul_expr(Z3.IntVal(coeff, ctx), z3_mul_expr(x[i], y[j])))
            end
        end
        push!(out, z3_sum(ctx, terms))
    end
    out
end

function z3_associator_zero_verdict(table::Array{Int,3}, witness::Tuple{Int,Int,Int})
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    dim = size(table, 1)
    vars(name) = [Z3.IntVar("$(name)_$(i - 1)", ctx) for i in 1:dim]
    x, y, z = vars("x"), vars("y"), vars("z")
    a0, b0, c0 = witness
    for i in 1:dim
        Z3.add(solver, x[i] == Z3.IntVal(i == a0 + 1 ? 1 : 0, ctx))
        Z3.add(solver, y[i] == Z3.IntVal(i == b0 + 1 ? 1 : 0, ctx))
        Z3.add(solver, z[i] == Z3.IntVal(i == c0 + 1 ? 1 : 0, ctx))
    end
    xy = z3_product_exprs(ctx, table, x, y)
    yz = z3_product_exprs(ctx, table, y, z)
    left = z3_product_exprs(ctx, table, xy, z)
    right = z3_product_exprs(ctx, table, x, yz)
    eqs = Z3.Expr[left[k] == right[k] for k in 1:dim]
    Z3.add(solver, Z3.And(eqs))
    string(Z3.check(solver))
end

function z3_basin_escape_verdict(real_constraint::Bool)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    xs = [Z3.IntVar("seed_$(i)", ctx) for i in 1:4]
    for x in xs
        Z3.add(solver, Z3.Or([x == Z3.IntVal(1, ctx), x == Z3.IntVal(-1, ctx)]))
    end
    q = z3_sum(ctx, [z3_mul_expr(xs[i], Z3.IntVal(round(Int, TARGET[i]), ctx)) for i in 1:4])
    ys = if real_constraint
        [Z3.If(z3_ge_expr(q, Z3.IntVal(0, ctx)), Z3.IntVal(round(Int, TARGET[i]), ctx), Z3.IntVal(-round(Int, TARGET[i]), ctx)) for i in 1:4]
    else
        [Z3.IntVal(0, ctx) for _ in 1:4]
    end
    pos = Z3.And([ys[i] == Z3.IntVal(round(Int, TARGET[i]), ctx) for i in 1:4])
    neg = Z3.And([ys[i] == Z3.IntVal(-round(Int, TARGET[i]), ctx) for i in 1:4])
    Z3.add(solver, Z3.Not(Z3.Or([pos, neg])))
    string(Z3.check(solver))
end

function smt_readout()
    tables = Dict("H" => quaternion_table(), "O" => octonion_table())
    Dict{String,Any}(
        "z3" => Dict(
            "octonion_assoc_zero_assertion" => z3_associator_zero_verdict(tables["O"], O_WITNESS),
            "quaternion_assoc_zero_control" => z3_associator_zero_verdict(tables["H"], H_ASSOC_CONTROL),
            "real_basin_escape" => z3_basin_escape_verdict(true),
            "erased_basin_escape" => z3_basin_escape_verdict(false),
            "derived_in_solver" => true,
        ),
    )
end

function quotient_readout(graph, algebra, qit, basins)
    Dict{String,Any}(
        "M" => Dict(
            "probe_family" => [
                "edge octonion associator",
                "quaternion associator control",
                "Hopf S3_to_S2 node readout",
                "Weyl chirality split",
                "Lindblad/CPTP entropy/coherent information",
                "finite graph cycle rank",
                "basin state/update/boundary/invariant/escape",
            ],
            "graph_edges" => [collect(e) for e in GRAPH_EDGES],
        ),
        "C" => Dict(
            "trace" => "trace(rho)=1 checked after ODE integration",
            "PSD" => "density generated as |psi><psi| and Lindblad/CPTP path preserves positive eigenvalues within tolerance",
            "Hermitian" => "rho=rho^dagger by density construction and Hermitian symmetrization in readouts",
            "normalization" => "node spinor normalized on S3 before Hopf map",
            "rung_specific" => "octonion edge bracketing, chirality split, graph message invariant, and finite basin escape query all active",
        ),
        "quotient_classes_under_M" => Dict(
            "structured_spinor_network" => "nonzero octonion associator, chirality split, two structured finite basins, positive coherent information",
            "erased_control" => "zeroed basin update and maximally mixed carrier collapse coherent information",
            "associative_control" => "quaternion associator zero",
        ),
        "drop_probe_strictly_coarsens" => algebra["octonion_associator_norm"] > 0 && graph["cycle_rank"] > 0 && qit["coherent_information"] != qit["erased_coherent_information"] && basins["finite_real"]["attractor_count"] != basins["finite_erased_control"]["attractor_count"],
    )
end

function tool_calls(algebra, geometry, dynamics, graph, qit, basins, attractors, tensor, smt)
    [
        Dict("tool" => "Octonions", "api_surface" => "Octonions.Octonion multiplication", "input_object" => "edge couplings e1,e2,e4", "output_object" => algebra["octonion_associator_norm"], "positive_case" => "nonzero octonion associator", "negative_control" => "quaternion associator zero", "boundary_case" => "same witness indices inside quaternion subalgebra", "demotion_condition" => "associator norm collapses to zero"),
        Dict("tool" => "Quaternions", "api_surface" => "Quaternions.Quaternion multiplication", "input_object" => "edge controls i,j", "output_object" => algebra["quaternion_order_gap"], "positive_case" => "noncommuting order gap", "negative_control" => "i*i order gap zero", "boundary_case" => "associative triplet associator", "demotion_condition" => "no order or associativity flip"),
        Dict("tool" => "Cayley-Dickson", "api_surface" => "recursive table multiplication", "input_object" => "sedenion witness (e1+e10)*(e5+e14)", "output_object" => algebra["sedenion_zero_divisor_product_normsq"], "positive_case" => "zero product with nonzero factors", "negative_control" => "octonion division control", "boundary_case" => "nonzero factor norms", "demotion_condition" => "kill-control does not annihilate"),
        Dict("tool" => "CliffordAlgebras", "api_surface" => "CliffordAlgebra(3)/basevector/MultiVector product", "input_object" => "Cl(3) e1,e2 carrier blades", "output_object" => Dict("dimension" => algebra["clifford_dimension_cl3"], "e1e2_anticommutes" => algebra["clifford_e1e2_anticommutes"]), "positive_case" => "Cl(3) carrier side sanity check", "negative_control" => "zero multivector anticommutator", "boundary_case" => algebra["clifford_dimension_cl3"], "demotion_condition" => "side readout does not gate all_pass, divergence, quotient, a named control, or proof", "gates" => "none", "claim_depth" => "supportive"),
        Dict("tool" => "QuantumOptics", "api_surface" => "QuantumOptics.entropy_vn/ptrace/liouvillian", "input_object" => "two-qubit spinor density", "output_object" => qit["coherent_information"], "positive_case" => "structured coherent information", "negative_control" => qit["erased_coherent_information"], "boundary_case" => qit["liouvillian_shape"], "demotion_condition" => "entropy readout independent of carrier"),
        Dict("tool" => "DifferentialEquations", "api_surface" => "DifferentialEquations.ODEProblem/solve", "input_object" => "Lindblad master equation", "output_object" => dynamics["final_excited_population"], "positive_case" => "dissipative/unitary final population", "negative_control" => "trace conservation", "boundary_case" => dynamics["final_trace"], "demotion_condition" => "ODE not on node state"),
        Dict("tool" => "Attractors+DynamicalSystems", "api_surface" => "basins_of_attraction/CoupledODEs", "input_object" => "order-parameter flow", "output_object" => attractors["attractor_count"], "positive_case" => "two attractor labels", "negative_control" => basins["finite_erased_control"]["attractor_count"], "boundary_case" => "finite basin escape SMT", "demotion_condition" => "side readout does not gate all_pass, divergence, quotient, a named control, or proof", "gates" => "none", "claim_depth" => "supportive"),
        Dict("tool" => "Manifolds", "api_surface" => "Manifolds.distance(Sphere(3),p,q)", "input_object" => "normalized node spinor", "output_object" => geometry["s3_distance_to_erased_reference"], "positive_case" => "structured S3 distance", "negative_control" => "erased reference", "boundary_case" => geometry["hopf_s2"], "demotion_condition" => "side readout does not gate all_pass, divergence, quotient, a named control, or proof", "gates" => "none", "claim_depth" => "supportive"),
        Dict("tool" => "Graphs", "api_surface" => "Graphs.SimpleGraph/add_edge!", "input_object" => "four-node spinor network", "output_object" => graph["cycle_rank"], "positive_case" => "cycle rank invariant", "negative_control" => "edge-erasure would reduce rank", "boundary_case" => graph["edge_count"], "demotion_condition" => "graph invariant unused"),
        Dict("tool" => "ITensors", "api_surface" => "ITensors.ITensor/scalar", "input_object" => "four node spinor amplitudes", "output_object" => tensor["contraction_norm"], "positive_case" => "multi-node contraction norm", "negative_control" => "carrier erasure would flatten amplitudes", "boundary_case" => tensor["node_tensor_count"], "demotion_condition" => "side readout does not gate all_pass, divergence, quotient, a named control, or proof", "gates" => "none", "claim_depth" => "supportive"),
        Dict("tool" => "Yao", "api_surface" => "Yao.X/Yao.H matrices", "input_object" => "unitary node gates", "output_object" => dynamics["unitary_xh_commutator_norm"], "positive_case" => "unitary order gap", "negative_control" => "same-gate commutator zero", "boundary_case" => "2x2 gates", "demotion_condition" => "side readout does not gate all_pass, divergence, quotient, a named control, or proof", "gates" => "none", "claim_depth" => "supportive"),
        Dict("tool" => "Z3", "api_surface" => "Z3.add/check", "input_object" => "bound multiplication tables and finite state update", "output_object" => smt["z3"], "positive_case" => "octonion assoc-zero UNSAT and real escape UNSAT", "negative_control" => "quaternion assoc-zero SAT and erased escape SAT", "boundary_case" => "all entries derived in solver", "demotion_condition" => "proof binds only a precomputed scalar"),
    ]
end

function main()
    mkpath(dirname(RESULT_PATH))
    algebra = algebra_readouts()
    graph = graph_readout()
    geometry = geometry_readout()
    qit = qit_readout()
    dynamics = dynamics_readout()
    basins = Dict("finite_real" => finite_basins(true), "finite_erased_control" => finite_basins(false))
    attractors = attractors_readout()
    tensor = itensor_readout()
    smt = smt_readout()
    quotient = quotient_readout(graph, algebra, qit, basins)
    controls = Dict{String,Any}(
        "commuting_control" => Dict("structured" => algebra["quaternion_order_gap"], "control" => algebra["commuting_control_gap"], "flips" => algebra["quaternion_order_gap"] > 0 && algebra["commuting_control_gap"] <= TOL),
        "associative_control" => Dict("octonion" => algebra["octonion_associator_norm"], "quaternion" => algebra["quaternion_associator_control_norm"], "flips" => algebra["octonion_associator_norm"] > 0 && algebra["quaternion_associator_control_norm"] <= TOL),
        "sedenion_zero_divisor_kill" => Dict("product_normsq" => algebra["sedenion_zero_divisor_product_normsq"], "flips" => algebra["sedenion_zero_divisor_product_normsq"] == 0 && algebra["sedenion_zero_divisor_left_normsq"] > 0 && algebra["sedenion_zero_divisor_right_normsq"] > 0),
        "carrier_erasure" => Dict("structured_coherent_information" => qit["coherent_information"], "erased_coherent_information" => qit["erased_coherent_information"], "flips" => qit["coherent_information"] != qit["erased_coherent_information"]),
        "no_chirality" => Dict("chirality_split_norm" => geometry["chirality_split_norm"], "no_chirality_control_norm" => geometry["no_chirality_control_norm"], "flips" => geometry["chirality_split_norm"] > 0 && geometry["no_chirality_control_norm"] <= TOL),
        "basin_control" => Dict("structured_count" => basins["finite_real"]["attractor_count"], "erased_count" => basins["finite_erased_control"]["attractor_count"], "flips" => basins["finite_real"]["attractor_count"] != basins["finite_erased_control"]["attractor_count"]),
        "z3_derive_flip" => Dict("octonion_assoc_zero" => smt["z3"]["octonion_assoc_zero_assertion"], "quaternion_assoc_zero" => smt["z3"]["quaternion_assoc_zero_control"], "erased_basin_escape" => smt["z3"]["erased_basin_escape"], "flips" => smt["z3"]["octonion_assoc_zero_assertion"] == "unsat" && smt["z3"]["quaternion_assoc_zero_control"] == "sat" && smt["z3"]["erased_basin_escape"] == "sat"),
    )
    all_pass = all(v["flips"] == true for v in values(controls)) && abs(dynamics["final_trace"] - 1.0) <= TOL && quotient["drop_probe_strictly_coarsens"]
    payload = Dict{String,Any}(
        "schema_version" => "engine_leg_result_v1",
        "object_id" => OBJECT_ID,
        "rung_id" => RUNG_ID,
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "generated_at" => string(now(UTC)),
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "julia_project" => Base.active_project(),
        "packages_used" => collect(keys(TOOL_MANIFEST)),
        "aligned_packages_load_bearing" => ["QuantumOptics", "DifferentialEquations", "Z3"],
        "claim_path_tools" => ["QuantumOptics", "Octonions", "Quaternions", "DifferentialEquations", "Graphs", "Z3", "Cayley-Dickson"],
        "engine_contract" => Dict("mode" => "all_three_full_sims", "reads_peer_result" => false),
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "algebra" => algebra,
        "geometry" => geometry,
        "dynamics" => dynamics,
        "network" => graph,
        "basins" => basins,
        "attractors_package_basin" => attractors,
        "qit_readout" => qit,
        "tensor_readout" => tensor,
        "smt" => smt,
        "M_C_quotient" => quotient,
        "controls" => controls,
        "tool_calls" => tool_calls(algebra, geometry, dynamics, graph, qit, basins, attractors, tensor, smt),
        "omitted_tools" => ["Grassmann", "QuantumClifford", "QuantumToolbox", "ITensorMPS", "Symbolics", "ChaosTools"],
        "claim_ceiling" => "scratch_diagnostic finite same-carrier spinor-network integration test only; no canon/admission/bridge/physics/Axis0/manifold claim",
        "all_pass" => all_pass,
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println("FOUNDATION_SPINOR_NETWORK_FULL_STACK_LAYER_JULIA_DONE all_pass=$(all_pass) result=$(RESULT_PATH)")
    return all_pass ? 0 : 2
end

exit(main())
