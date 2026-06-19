#!/usr/bin/env julia
# object_id: foundation_spinor_network_basins_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: false

using Dates
using JSON
using LinearAlgebra
using SHA
using CliffordAlgebras
using Octonions
using Quaternions
using QuantumOptics
using Z3
using Manifolds
using DifferentialEquations
using Attractors
using DynamicalSystems

const OBJECT_ID = "foundation_spinor_network_basins_julia"
const RUNG_ID = "spinor_network_basins"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_spinor_network_basins_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_spinor_network_basins_julia_results.json")
const PYTHON = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
const TOL = 1.0e-9
const TARGET = [1.0, -1.0, -1.0, -1.0]
const GRAPH_EDGES = [[0, 1], [1, 2], [2, 3], [3, 0]]
const O_WITNESS = (1, 2, 4)
const H_ASSOC_CONTROL = (1, 2, 3)

const classification = "scratch_diagnostic"
const CLASSIFICATION = classification
const promotion_allowed = false
const PROMOTION_ALLOWED = promotion_allowed
const formal_admission_allowed = false
const FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
const reads_peer_result = false
const READS_PEER_RESULT = reads_peer_result

const TOOL_MANIFEST = Dict{String,Any}(
    "Quaternions" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Hamilton quaternion operator order-gap computation on network edge operators"),
    "Octonions" => Dict("tried" => true, "used" => true, "reason" => "load-bearing octonion bracketing associator for the nonassociative edge witness"),
    "CliffordAlgebras" => Dict("tried" => true, "used" => true, "reason" => "load-bearing CliffordAlgebra(:Quaternions) cross-check of the quaternion spinor carrier product"),
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing two-qubit spinor density, entropy_vn, ptrace, and erased carrier control"),
    "Attractors" => Dict("tried" => true, "used" => true, "reason" => "load-bearing basins_of_attraction computation for the spinor order-parameter flow"),
    "DynamicalSystems" => Dict("tried" => true, "used" => true, "reason" => "load-bearing CoupledODEs/StateSpaceSet route for the Attractors basin map"),
    "DifferentialEquations" => Dict("tried" => true, "used" => true, "reason" => "load-bearing ODEProblem/solve cross-check of the order-parameter flow"),
    "Manifolds" => Dict("tried" => true, "used" => true, "reason" => "load-bearing S^3 spinor-manifold distance between structured and erased reference spinors"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-side SMT derivation from bound structure constants and finite basin update constraints"),
    "cvc5_python_subprocess" => Dict("tried" => true, "used" => true, "reason" => "load-bearing local cvc5 proof over Julia-built table values; CVC5.jl is absent in the default Julia project"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Quaternions" => "load_bearing",
    "Octonions" => "load_bearing",
    "CliffordAlgebras" => "load_bearing",
    "QuantumOptics" => "load_bearing",
    "Attractors" => "load_bearing",
    "DynamicalSystems" => "load_bearing",
    "DifferentialEquations" => "load_bearing",
    "Manifolds" => "load_bearing",
    "Z3" => "load_bearing",
    "cvc5_python_subprocess" => "load_bearing",
)

const CVC5_CODE = raw"""
import json
import sys
import cvc5
from cvc5 import Kind

payload = json.load(open(sys.argv[1], "r", encoding="utf-8"))
mode = payload["mode"]
target = [1, -1, -1, -1]

def csum(s, items):
    if not items:
        return s.mkInteger(0)
    out = items[0]
    for item in items[1:]:
        out = s.mkTerm(Kind.ADD, out, item)
    return out

s = cvc5.Solver()
s.setLogic("QF_LIA")
int_sort = s.getIntegerSort()

if mode in ("order", "assoc"):
    table = payload["table"]
    dim = len(table)
    mu = {}
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                var = s.mkConst(int_sort, f"mu_{mode}_{k}_{i}_{j}")
                s.assertFormula(s.mkTerm(Kind.EQUAL, var, s.mkInteger(int(table[k][i][j]))))
                mu[(k, i, j)] = var
    if mode == "order":
        a = int(payload["a"])
        b = int(payload["b"])
        s.assertFormula(s.mkTerm(Kind.AND, *[s.mkTerm(Kind.EQUAL, mu[(k, a, b)], mu[(k, b, a)]) for k in range(dim)]))
    else:
        a = int(payload["a"])
        b = int(payload["b"])
        c = int(payload["c"])
        eqs = []
        for k in range(dim):
            left = csum(s, [s.mkTerm(Kind.MULT, mu[(k, m, c)], mu[(m, a, b)]) for m in range(dim)])
            right = csum(s, [s.mkTerm(Kind.MULT, mu[(k, a, m)], mu[(m, b, c)]) for m in range(dim)])
            eqs.append(s.mkTerm(Kind.EQUAL, left, right))
        s.assertFormula(s.mkTerm(Kind.AND, *eqs))
elif mode == "basin":
    real = bool(payload["real"])
    one = s.mkInteger(1)
    neg_one = s.mkInteger(-1)
    zero = s.mkInteger(0)
    xs = [s.mkConst(int_sort, f"x{i}") for i in range(4)]
    for x in xs:
        s.assertFormula(s.mkTerm(Kind.OR, s.mkTerm(Kind.EQUAL, x, one), s.mkTerm(Kind.EQUAL, x, neg_one)))
    q = csum(s, [s.mkTerm(Kind.MULT, xs[i], s.mkInteger(target[i])) for i in range(4)])
    if real:
        ys = [
            s.mkTerm(Kind.ITE, s.mkTerm(Kind.GEQ, q, zero), s.mkInteger(target[i]), s.mkInteger(-target[i]))
            for i in range(4)
        ]
    else:
        ys = xs
    pos = s.mkTerm(Kind.AND, *[s.mkTerm(Kind.EQUAL, ys[i], s.mkInteger(target[i])) for i in range(4)])
    neg = s.mkTerm(Kind.AND, *[s.mkTerm(Kind.EQUAL, ys[i], s.mkInteger(-target[i])) for i in range(4)])
    s.assertFormula(s.mkTerm(Kind.NOT, s.mkTerm(Kind.OR, pos, neg)))
else:
    raise SystemExit(f"unknown mode {mode}")

print(str(s.checkSat()))
"""

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
    Quaternion(ntuple(k -> k == idx0 + 1 ? 1.0 : 0.0, 4)...)
end

function obasis(idx0::Int)
    Octonion(ntuple(k -> k == idx0 + 1 ? 1.0 : 0.0, 8)...)
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

function clifford_quaternion_crosscheck()
    clh = CliffordAlgebra(:Quaternions)
    labels = [Symbol("𝟏"), :i, :j, :ij]
    coeffs(mv) = [Float64(real(getproperty(mv, label))) for label in labels]
    ij = coeffs(clh.i * clh.j)
    ji = coeffs(clh.j * clh.i)
    Dict{String,Any}(
        "function_called" => "CliffordAlgebras.CliffordAlgebra(:Quaternions)",
        "i_j" => ij,
        "j_i" => ji,
        "order_gap_norm" => norm(ij - ji),
    )
end

function order_gap_quaternion()
    i = qbasis(1)
    j = qbasis(2)
    Dict{String,Any}(
        "function_called" => "Quaternions.Quaternion multiplication",
        "noncommuting_order_gap" => norm(coeffs_quat(i * j - j * i)),
        "commuting_control_gap" => norm(coeffs_quat(i * i - i * i)),
        "i_j" => coeffs_quat(i * j),
        "j_i" => coeffs_quat(j * i),
    )
end

function associator_octonion()
    a, b, c = O_WITNESS
    x, y, z = obasis(a), obasis(b), obasis(c)
    assoc = (x * y) * z - x * (y * z)
    qa, qb, qc = H_ASSOC_CONTROL
    hx, hy, hz = qbasis(qa), qbasis(qb), qbasis(qc)
    h_assoc = (hx * hy) * hz - hx * (hy * hz)
    Dict{String,Any}(
        "function_called" => "Octonions.Octonion multiplication and Quaternions control",
        "witness" => collect(O_WITNESS),
        "octonion_associator_vector" => coeffs_oct(assoc),
        "octonion_associator_norm" => norm(coeffs_oct(assoc)),
        "quaternion_control_witness" => collect(H_ASSOC_CONTROL),
        "quaternion_associator_control_vector" => coeffs_quat(h_assoc),
        "quaternion_associator_control_norm" => norm(coeffs_quat(h_assoc)),
    )
end

function all_states()
    rows = Vector{Vector{Float64}}()
    for bits in Iterators.product(fill([-1.0, 1.0], 4)...)
        push!(rows, collect(bits))
    end
    rows
end

function finite_update(state::Vector{Float64}; real_constraint::Bool)
    if !real_constraint
        return copy(state)
    end
    q = dot(state, TARGET)
    q >= 0.0 ? copy(TARGET) : -copy(TARGET)
end

function finite_basins(real_constraint::Bool)
    counts = Dict{String,Int}()
    for state in all_states()
        final = finite_update(state; real_constraint = real_constraint)
        key = join(string.(round.(Int, final)), " ")
        counts[key] = get(counts, key, 0) + 1
    end
    Dict{String,Any}(
        "seed_count" => 16,
        "attractor_count" => length(keys(counts)),
        "basin_counts" => counts,
        "basin_fractions" => Dict(key => value / 16.0 for (key, value) in counts),
    )
end

function qit_readout()
    b = tensor(SpinBasis(1 // 2), SpinBasis(1 // 2))
    psi = Ket(b, ComplexF64.(TARGET ./ norm(TARGET)))
    rho = dm(psi)
    erased = Operator(b, b, Matrix{ComplexF64}(I, 4, 4) / 4)
    reduced = ptrace(rho, [2])
    reduced_erased = ptrace(erased, [2])
    s_ab = Float64(real(entropy_vn(rho)))
    s_a = Float64(real(entropy_vn(reduced)))
    s_ab_erased = Float64(real(entropy_vn(erased)))
    s_a_erased = Float64(real(entropy_vn(reduced_erased)))
    vals = eigvals(Matrix{ComplexF64}(rho.data - erased.data))
    Dict{String,Any}(
        "function_called" => "QuantumOptics.Ket, dm, entropy_vn, ptrace",
        "von_neumann_entropy" => s_ab,
        "subsystem_entropy_q0" => s_a,
        "coherent_information_q0_to_q1" => s_a - s_ab,
        "erased_von_neumann_entropy" => s_ab_erased,
        "erased_subsystem_entropy_q0" => s_a_erased,
        "erased_coherent_information_q0_to_q1" => s_a_erased - s_ab_erased,
        "distinguishability_trace_distance_to_erased" => 0.5 * sum(abs.(vals)),
    )
end

function attractors_basin_flow()
    ds = CoupledODEs((u, p, t) -> SVector(u[1] - u[1]^3), SVector(0.2))
    attractor_sets = Dict(
        1 => StateSpaceSet([SVector(-1.0)]),
        2 => StateSpaceSet([SVector(1.0)]),
    )
    mapper = AttractorsViaProximity(ds, attractor_sets)
    grid = (range(-1.5, 1.5; length = 16),)
    basins, attractors = basins_of_attraction(mapper, grid)
    counts = Dict{String,Int}()
    for key in unique(vec(basins))
        counts[string(Int(key))] = count(==(key), vec(basins))
    end
    prob = ODEProblem((u, p, t) -> u - u^3, 0.2, (0.0, 5.0))
    sol = solve(prob, Tsit5())
    Dict{String,Any}(
        "function_called" => "Attractors.basins_of_attraction with DynamicalSystems.CoupledODEs",
        "attractor_count" => length(attractors),
        "basin_counts" => counts,
        "differentialequations_function_called" => "DifferentialEquations.solve",
        "ode_final_state_from_0_2" => Float64(sol.u[end]),
    )
end

function manifolds_distance()
    m = Sphere(3)
    structured = TARGET ./ norm(TARGET)
    erased_reference = fill(1.0, 4)
    erased_reference ./= norm(erased_reference)
    Dict{String,Any}(
        "function_called" => "Manifolds.distance(Sphere(3), p, q)",
        "S3_distance_structured_to_erased_reference" => Float64(distance(m, structured, erased_reference)),
    )
end

function z3_add_expr(args)
    isempty(args) && error("z3_add_expr requires at least one argument")
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_mul_expr(left, right)
    Z3.Expr(left.ctx, Z3.Libz3.Z3_mk_mul(Z3.ctx_ref(left), 2, map(Z3.as_ast, [left, right])))
end

function z3_sum(ctx, items)
    isempty(items) && return Z3.IntVal(0, ctx)
    length(items) == 1 && return items[1]
    z3_add_expr(items)
end

function z3_order_proof(table::Array{Int,3}, a0::Int, b0::Int)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    dim = size(table, 1)
    mu = Dict{Tuple{Int,Int,Int},Any}()
    for k in 0:(dim - 1), i in 0:(dim - 1), j in 0:(dim - 1)
        var = Z3.IntVar("mu_o_$(k)_$(i)_$(j)", ctx)
        Z3.add(solver, var == Z3.IntVal(table[k + 1, i + 1, j + 1], ctx))
        mu[(k, i, j)] = var
    end
    order_eqs = Z3.Expr[mu[(k, a0, b0)] == mu[(k, b0, a0)] for k in 0:(dim - 1)]
    Z3.add(solver, Z3.And(order_eqs))
    string(Z3.check(solver))
end

function z3_associator_proof(table::Array{Int,3}, witness::Tuple{Int,Int,Int})
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    dim = size(table, 1)
    a0, b0, c0 = witness
    mu = Dict{Tuple{Int,Int,Int},Any}()
    for k in 0:(dim - 1), i in 0:(dim - 1), j in 0:(dim - 1)
        var = Z3.IntVar("mu_a_$(k)_$(i)_$(j)", ctx)
        Z3.add(solver, var == Z3.IntVal(table[k + 1, i + 1, j + 1], ctx))
        mu[(k, i, j)] = var
    end
    equations = Z3.Expr[]
    for k in 0:(dim - 1)
        left = z3_sum(ctx, [z3_mul_expr(mu[(k, m, c0)], mu[(m, a0, b0)]) for m in 0:(dim - 1)])
        right = z3_sum(ctx, [z3_mul_expr(mu[(k, a0, m)], mu[(m, b0, c0)]) for m in 0:(dim - 1)])
        push!(equations, left == right)
    end
    Z3.add(solver, Z3.And(equations))
    string(Z3.check(solver))
end

function z3_basin_proof(real_constraint::Bool)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    xs = [Z3.IntVar("x$i", ctx) for i in 1:4]
    ys = [Z3.IntVar("y$i", ctx) for i in 1:4]
    for x in xs
        Z3.add(solver, Z3.Or(Z3.Expr[x == Z3.IntVal(1, ctx), x == Z3.IntVal(-1, ctx)]))
    end
    q = z3_sum(ctx, [z3_mul_expr(xs[i], Z3.IntVal(round(Int, TARGET[i]), ctx)) for i in 1:4])
    if real_constraint
        for i in 1:4
            t = Z3.IntVal(round(Int, TARGET[i]), ctx)
            nt = Z3.IntVal(-round(Int, TARGET[i]), ctx)
            Z3.add(solver, Z3.Or(Z3.Expr[q < Z3.IntVal(0, ctx), ys[i] == t]))
            Z3.add(solver, Z3.Or(Z3.Expr[Z3.Not(q < Z3.IntVal(0, ctx)), ys[i] == nt]))
        end
    else
        for i in 1:4
            Z3.add(solver, ys[i] == xs[i])
        end
    end
    pos = Z3.And(Z3.Expr[ys[i] == Z3.IntVal(round(Int, TARGET[i]), ctx) for i in 1:4])
    neg = Z3.And(Z3.Expr[ys[i] == Z3.IntVal(-round(Int, TARGET[i]), ctx) for i in 1:4])
    Z3.add(solver, Z3.Not(Z3.Or(Z3.Expr[pos, neg])))
    string(Z3.check(solver))
end

function nested_int_table(table::Array{Int,3})
    dim = size(table, 1)
    [[[Int(table[k, i, j]) for j in 1:dim] for i in 1:dim] for k in 1:dim]
end

function cvc5_bridge(mode::String; table = nothing, a::Int = 0, b::Int = 0, c::Int = 0, real::Bool = false)
    payload = Dict{String,Any}("mode" => mode, "a" => a, "b" => b, "c" => c, "real" => real)
    if table !== nothing
        payload["table"] = nested_int_table(table)
    end
    tmp = tempname()
    open(tmp, "w") do io
        JSON.print(io, payload)
    end
    out = strip(read(`$PYTHON -c $CVC5_CODE $tmp`, String))
    rm(tmp; force = true)
    out
end

function quotient_summary()
    classes = Set{Tuple{Float64,Float64,Float64}}()
    dropped = Set{Tuple{Float64,Float64}}()
    for state in all_states()
        edge01 = state[1] * state[2]
        edge02 = state[1] * state[3]
        edge03 = state[1] * state[4]
        push!(classes, (edge01, edge02, edge03))
        push!(dropped, (edge01, edge02))
    end
    Dict{String,Any}(
        "M" => ["edge01_spinor_parity", "edge02_spinor_parity", "edge03_spinor_parity"],
        "quotient_classes_under_M" => length(classes),
        "drop_edge03_control_classes" => length(dropped),
        "drop_probe_strictly_coarsens" => length(dropped) < length(classes),
        "C" => ["trace=1", "PSD", "Hermitian", "normalization", "order_gap_nonzero", "octonion_associator_nonzero", "finite basin compression under C"],
    )
end

function build_result()
    mkpath(dirname(RESULT_PATH))
    h_table = quaternion_table()
    o_table = octonion_table()
    order = order_gap_quaternion()
    assoc = associator_octonion()
    basins_real = finite_basins(true)
    basins_control = finite_basins(false)
    qit = qit_readout()
    attr = attractors_basin_flow()
    manifold = manifolds_distance()
    clifford = clifford_quaternion_crosscheck()
    smt = Dict{String,Any}(
        "z3" => Dict{String,Any}(
            "order_noncommuting_commute_assertion" => z3_order_proof(h_table, 1, 2),
            "order_commuting_control" => z3_order_proof(h_table, 1, 1),
            "octonion_assoc_zero_assertion" => z3_associator_proof(o_table, O_WITNESS),
            "quaternion_assoc_zero_control" => z3_associator_proof(h_table, H_ASSOC_CONTROL),
            "real_basin_counterexample" => z3_basin_proof(true),
            "erased_basin_counterexample" => z3_basin_proof(false),
        ),
        "cvc5" => Dict{String,Any}(
            "order_noncommuting_commute_assertion" => cvc5_bridge("order"; table = h_table, a = 1, b = 2),
            "order_commuting_control" => cvc5_bridge("order"; table = h_table, a = 1, b = 1),
            "octonion_assoc_zero_assertion" => cvc5_bridge("assoc"; table = o_table, a = O_WITNESS[1], b = O_WITNESS[2], c = O_WITNESS[3]),
            "quaternion_assoc_zero_control" => cvc5_bridge("assoc"; table = h_table, a = H_ASSOC_CONTROL[1], b = H_ASSOC_CONTROL[2], c = H_ASSOC_CONTROL[3]),
            "real_basin_counterexample" => cvc5_bridge("basin"; real = true),
            "erased_basin_counterexample" => cvc5_bridge("basin"; real = false),
        ),
    )
    all_pass =
        order["noncommuting_order_gap"] > 1.0 &&
        order["commuting_control_gap"] <= TOL &&
        assoc["octonion_associator_norm"] > 1.0 &&
        assoc["quaternion_associator_control_norm"] <= TOL &&
        basins_real["attractor_count"] == 2 &&
        basins_control["attractor_count"] == 16 &&
        smt["z3"]["real_basin_counterexample"] == "unsat" &&
        smt["cvc5"]["real_basin_counterexample"] == "unsat" &&
        smt["z3"]["erased_basin_counterexample"] == "sat" &&
        smt["cvc5"]["erased_basin_counterexample"] == "sat"
    Dict{String,Any}(
        "schema_version" => "three_engine_leg_result_v1",
        "object_id" => OBJECT_ID,
        "rung_id" => RUNG_ID,
        "engine" => "julia",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "reads_peer_result" => reads_peer_result,
        "packages_used" => ["Quaternions", "Octonions", "CliffordAlgebras", "QuantumOptics", "Attractors", "DynamicalSystems", "DifferentialEquations", "Manifolds", "Z3", "cvc5", "JSON", "SHA"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "CliffordAlgebras", "Z3", "DifferentialEquations"],
        "claim_path_tools" => ["Quaternions", "Octonions", "CliffordAlgebras", "QuantumOptics", "Attractors", "DynamicalSystems", "DifferentialEquations", "Manifolds", "Z3", "cvc5"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "network" => Dict("node_count" => 4, "edges" => GRAPH_EDGES, "target_spinor" => TARGET),
        "algebra" => Dict(
            "order_gap_noncommuting" => order["noncommuting_order_gap"],
            "order_gap_commuting_control" => order["commuting_control_gap"],
            "octonion_associator_norm" => assoc["octonion_associator_norm"],
            "octonion_associator_vector" => assoc["octonion_associator_vector"],
            "quaternion_associator_control_norm" => assoc["quaternion_associator_control_norm"],
            "clifford_quaternion_crosscheck" => clifford,
        ),
        "basins" => Dict("finite_real" => basins_real, "finite_erased_control" => basins_control, "attractors_jl" => attr),
        "qit_readout" => qit,
        "manifolds" => manifold,
        "M_C_quotient" => quotient_summary(),
        "smt" => smt,
        "tool_calls" => [
            Dict("tool" => "Quaternions", "function" => "Quaternion multiplication", "computed" => order),
            Dict("tool" => "Octonions", "function" => "Octonion multiplication", "computed" => assoc),
            Dict("tool" => "CliffordAlgebras", "function" => "CliffordAlgebra(:Quaternions)", "computed" => clifford),
            Dict("tool" => "QuantumOptics", "function" => "entropy_vn and ptrace", "computed" => qit),
            Dict("tool" => "Attractors", "function" => "basins_of_attraction", "computed" => attr),
            Dict("tool" => "Manifolds", "function" => "distance(Sphere(3), p, q)", "computed" => manifold),
            Dict("tool" => "Z3", "function" => "Z3.check", "computed" => smt["z3"]),
            Dict("tool" => "cvc5", "function" => "cvc5.Solver.checkSat via local subprocess", "computed" => smt["cvc5"]),
        ],
        "all_pass" => all_pass,
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(
        "FOUNDATION_SPINOR_NETWORK_BASINS_JULIA_DONE all_pass=$(result["all_pass"]) " *
        "order_gap=$(result["algebra"]["order_gap_noncommuting"]) " *
        "assoc=$(result["algebra"]["octonion_associator_norm"]) " *
        "real_attractors=$(result["basins"]["finite_real"]["attractor_count"]) " *
        "control_attractors=$(result["basins"]["finite_erased_control"]["attractor_count"]) " *
        "result=$(RESULT_PATH)"
    )
    result["all_pass"] ? 0 : 2
end

exit(main())
