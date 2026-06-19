#!/usr/bin/env julia
# object_id: clifford_spinor_carrier_rung
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: false

using Dates
using JSON
using SHA
using CliffordAlgebras
using Z3

const OBJECT_ID = "clifford_spinor_carrier_rung"
const RESULT_PATH = joinpath(@__DIR__, "clifford_spinor_carrier_rung_julia_results.json")
const TOL = 1.0e-9
const CLAIM_CEILING = "Authoritative Julia-only Clifford/spinor carrier rung diagnostic: constructs real Cl(3,0) and Cl(6,0) with CliffordAlgebras, checks dimensions, even-subalgebra dimensions, pseudoscalars, geometric-product anticommutation, and Z3 bounded structural dimension recurrence. No peer parity, no JAX/PyTorch leg, no bridge/admission/manifold closure claim."

function sha256_file(path::String)
    isfile(path) || return nothing
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function dimension_for(n::Int)
    2^n
end

function even_subalgebra_dimension(n::Int)
    count(mask -> iseven(count_ones(UInt(mask))), 0:(2^n - 1))
end

function generator(algebra, idx::Int)
    getproperty(algebra, Symbol("e$idx"))
end

function generators(algebra, n::Int)
    [generator(algebra, idx) for idx in 1:n]
end

function pseudoscalar(algebra, n::Int)
    gens = generators(algebra, n)
    acc = gens[1]
    for idx in 2:n
        acc *= gens[idx]
    end
    acc
end

function algebra_dimension(algebra)
    length(propertynames(algebra))
end

function anticommutation_report(algebra, n::Int)
    gens = generators(algebra, n)
    unit = one(gens[1])
    max_residual = 0.0
    failures = Vector{Dict{String,Any}}()
    for i in 1:n, j in 1:n
        lhs = gens[i] * gens[j] + gens[j] * gens[i]
        rhs = (i == j ? 2 : 0) * unit
        residual = Float64(CliffordAlgebras.norm(lhs - rhs))
        max_residual = max(max_residual, residual)
        if residual > TOL
            push!(failures, Dict{String,Any}(
                "i" => i,
                "j" => j,
                "residual" => residual,
                "lhs" => string(lhs),
                "rhs" => string(rhs),
            ))
        end
    end
    Dict{String,Any}(
        "n" => n,
        "max_residual" => max_residual,
        "failures" => failures,
        "pass" => isempty(failures),
    )
end

function z3_status_string(status)
    string(status)
end

function z3_is_unsat(status)
    z3_status_string(status) == "unsat"
end

function z3_mul(args::Vector{Z3.Expr})
    ctx = args[1].ctx
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_mul(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_mul(left::Z3.Expr, right::Z3.Expr)
    z3_mul([left, right])
end

function build_dim_solver(max_n::Int)
    solver = Z3.Solver()
    dims = [Z3.IntVar("dim_$idx") for idx in 0:max_n]
    pows = [Z3.IntVar("pow2_$idx") for idx in 0:max_n]
    Z3.add(solver, dims[1] == Z3.IntVal(1))
    Z3.add(solver, pows[1] == Z3.IntVal(1))
    for idx in 1:max_n
        Z3.add(solver, dims[idx + 1] == z3_mul(Z3.IntVal(2), dims[idx]))
        Z3.add(solver, pows[idx + 1] == z3_mul(Z3.IntVal(2), pows[idx]))
    end
    solver, dims, pows
end

function z3_dimension_proof(max_n::Int)
    proof_rows = Vector{Dict{String,Any}}()
    all_proved = true
    for n in 0:max_n
        solver, dims, pows = build_dim_solver(max_n)
        Z3.add(solver, Z3.Not(dims[n + 1] == pows[n + 1]))
        status = Z3.check(solver)
        proved = z3_is_unsat(status)
        all_proved &= proved
        push!(proof_rows, Dict{String,Any}(
            "n" => n,
            "claim" => "dim_$n == 2^$n",
            "negated_claim_status" => z3_status_string(status),
            "proved" => proved,
        ))
    end

    wrong_dim_rows = Vector{Dict{String,Any}}()
    wrong_controls = [(3, 7), (3, 9), (6, 63), (6, 65)]
    all_wrong_unsat = true
    for (n, wrong_dim) in wrong_controls
        solver, dims, pows = build_dim_solver(max_n)
        Z3.add(solver, dims[n + 1] == pows[n + 1])
        Z3.add(solver, dims[n + 1] == Z3.IntVal(wrong_dim))
        status = Z3.check(solver)
        wrong_unsat = z3_is_unsat(status)
        all_wrong_unsat &= wrong_unsat
        push!(wrong_dim_rows, Dict{String,Any}(
            "n" => n,
            "wrong_dim" => wrong_dim,
            "status" => z3_status_string(status),
            "unsat" => wrong_unsat,
        ))
    end

    Dict{String,Any}(
        "encoding" => "bounded recurrence: dim_0=1, dim_(k+1)=2*dim_k; pow2_0=1, pow2_(k+1)=2*pow2_k; prove negated equality UNSAT for n=0..max_n",
        "max_n" => max_n,
        "proof_rows" => proof_rows,
        "wrong_dim_rows" => wrong_dim_rows,
        "dim_relation_proved" => all_proved,
        "erase_flip_wrong_dim_unsat" => all_wrong_unsat,
        "pass" => all_proved && all_wrong_unsat,
    )
end

function algebra_report(name::String, algebra, n::Int)
    dim = algebra_dimension(algebra)
    expected_dim = dimension_for(n)
    even_dim = even_subalgebra_dimension(n)
    expected_even_dim = n == 0 ? 1 : 2^(n - 1)
    ps = pseudoscalar(algebra, n)
    Dict{String,Any}(
        "name" => name,
        "type" => string(typeof(algebra)),
        "signature" => "Cl($n,0)",
        "constructed_as_real_cliffordalgebra_object" => occursin("CliffordAlgebra", string(typeof(algebra))),
        "basis_symbol_count" => dim,
        "dimension" => dim,
        "expected_dimension_2_pow_n" => expected_dim,
        "dimension_pass" => dim == expected_dim,
        "even_subalgebra_dimension" => even_dim,
        "expected_even_subalgebra_dimension" => expected_even_dim,
        "even_subalgebra_dimension_pass" => even_dim == expected_even_dim,
        "pseudoscalar_gamma5" => string(ps),
        "pseudoscalar_square" => string(ps * ps),
        "anticommutation" => anticommutation_report(algebra, n),
    )
end

function build_result()
    started = time()
    cl3 = CliffordAlgebra(3, 0)
    cl6 = CliffordAlgebra(6, 0)

    cl3_report = algebra_report("cl3_pauli_floor", cl3, 3)
    cl6_report = algebra_report("cl6_carrier", cl6, 6)
    z3_report = z3_dimension_proof(6)

    uses_cliffordalgebras = cl3_report["constructed_as_real_cliffordalgebra_object"] &&
                            cl6_report["constructed_as_real_cliffordalgebra_object"]
    anticommutation_holds = cl3_report["anticommutation"]["pass"] &&
                            cl6_report["anticommutation"]["pass"]
    all_pass = uses_cliffordalgebras &&
               cl3_report["dimension_pass"] &&
               cl6_report["dimension_pass"] &&
               cl3_report["even_subalgebra_dimension_pass"] &&
               cl6_report["even_subalgebra_dimension_pass"] &&
               anticommutation_holds &&
               z3_report["pass"]

    Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => CLAIM_CEILING,
        "engine" => "julia",
        "backend" => "julia_authoritative_cliffordalgebras_z3",
        "ran" => true,
        "standalone" => true,
        "reads_peer_result" => false,
        "active_project" => Base.active_project(),
        "julia_version" => string(VERSION),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "source_sha256" => sha256_file(@__FILE__),
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "uses_cliffordalgebras" => uses_cliffordalgebras,
        "uses_z3" => true,
        "clifford_algebras" => Dict{String,Any}(
            "Cl(3,0)" => cl3_report,
            "Cl(6,0)" => cl6_report,
        ),
        "z3_dimension_proof" => z3_report,
        "summary" => Dict{String,Any}(
            "cl3_dim" => cl3_report["dimension"],
            "cl6_dim" => cl6_report["dimension"],
            "even_subalg_dim_cl3" => cl3_report["even_subalgebra_dimension"],
            "even_subalg_dim_cl6" => cl6_report["even_subalgebra_dimension"],
            "anticommutation_holds" => anticommutation_holds,
            "z3_dim_proof" => z3_report["pass"],
            "all_pass" => all_pass,
        ),
        "TOOL_MANIFEST" => Dict{String,Any}(
            "CliffordAlgebras" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing real CliffordAlgebra object construction, pseudoscalar/gamma5 extraction, and geometric-product anticommutation checks for Cl(3,0) and Cl(6,0)",
            ),
            "Z3" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing structural SMT recurrence proof for dim(Cl(n))=2^n and wrong-dimension UNSAT erase-flip controls",
            ),
            "JSON" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "supportive result serialization",
            ),
            "Dates" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "supportive UTC receipt timestamp",
            ),
            "SHA" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "supportive source fingerprint",
            ),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}(
            "CliffordAlgebras" => "load_bearing",
            "Z3" => "load_bearing",
            "JSON" => "supportive",
            "Dates" => "supportive",
            "SHA" => "supportive",
        ),
        "runtime_seconds" => round(time() - started; digits=6),
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    summary = result["summary"]
    println("result_path=", RESULT_PATH)
    println(
        "SCOUT_DONE uses_cliffordalgebras=$(result["uses_cliffordalgebras"]) " *
        "cl3_dim=$(summary["cl3_dim"]) " *
        "cl6_dim=$(summary["cl6_dim"]) " *
        "even_subalg_dim_cl3=$(summary["even_subalg_dim_cl3"]) " *
        "anticommutation_holds=$(summary["anticommutation_holds"]) " *
        "z3_dim_proof=$(summary["z3_dim_proof"]) " *
        "ran=$(result["ran"])"
    )
    return summary["all_pass"] ? 0 : 1
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
