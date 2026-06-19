#!/usr/bin/env julia

using JSON
using LinearAlgebra
using QuantumOptics
using SHA
using Z3

const SIM_ID = "manifold_information_throughput_v0"
const ROOT = normpath(joinpath(abspath(@__DIR__), "..", "..", ".."))
const RESULT = joinpath(ROOT, "system_v6", "sims", SIM_ID, "results", "$(SIM_ID)_julia_results.json")
const SOURCE = joinpath(ROOT, "system_v6", "sims", SIM_ID, "$(SIM_ID)_julia.jl")

function rel(path::AbstractString)
    normalized = normpath(abspath(path))
    prefix = endswith(ROOT, "/") ? ROOT : ROOT * "/"
    return startswith(normalized, prefix) ? normalized[length(prefix)+1:end] : normalized
end

function sha256_file(path::AbstractString)
    return bytes2hex(SHA.sha256(read(path)))
end

function entropy_from_bloch(r::Vector{Float64})
    radius = min(1.0, max(0.0, norm(r)))
    p = (1.0 + radius) / 2.0
    if p <= 0.0 || p >= 1.0
        return 0.0
    end
    return -p * log(p) - (1.0 - p) * log(1.0 - p)
end

function density_matrix_from_bloch(r::Vector{Float64})
    sx = ComplexF64[0 1; 1 0]
    sy = ComplexF64[0 -im; im 0]
    sz = ComplexF64[1 0; 0 -1]
    return (Matrix{ComplexF64}(I, 2, 2) + r[1] * sx + r[2] * sy + r[3] * sz) / 2
end

function qo_entropy_guard()
    basis = QuantumOptics.SpinBasis(1//2)
    psi = QuantumOptics.basisstate(basis, 1)
    rho = QuantumOptics.dm(psi)
    return real(QuantumOptics.entropy_vn(rho))
end

function six_state_holevo(M::Matrix{Float64}, c::Vector{Float64})
    ensemble = [
        [1.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, -1.0, 0.0],
        [0.0, 0.0, 1.0],
        [0.0, 0.0, -1.0],
    ]
    outputs = [M * collect(r) + c for r in ensemble]
    avg = sum(outputs) / length(outputs)
    # QuantumOptics entropy is used as the load-bearing state entropy route.
    basis = QuantumOptics.SpinBasis(1//2)
    mean_entropy = 0.0
    for out in outputs
        op = QuantumOptics.DenseOperator(basis, density_matrix_from_bloch(out))
        mean_entropy += real(QuantumOptics.entropy_vn(op))
    end
    mean_entropy /= length(outputs)
    avg_entropy = real(QuantumOptics.entropy_vn(QuantumOptics.DenseOperator(basis, density_matrix_from_bloch(avg))))
    holevo = avg_entropy - mean_entropy
    return Dict(
        "avg_entropy_nats" => avg_entropy,
        "mean_output_entropy_nats" => mean_entropy,
        "holevo_nats" => holevo,
        "information_killed_from_identity_nats" => log(2) - holevo,
    )
end

function z3_add(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0)
    return Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_sub(args::Vector{Z3.Expr})
    return Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_sub(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function julia_z3_conservation()
    solver = Z3.Solver()
    before = Z3.IntVar("before")
    after = Z3.IntVar("after")
    record = Z3.IntVar("record")
    Z3.add(solver, after == z3_sub(Z3.Expr[before, Z3.IntVal(2)]))
    Z3.add(solver, record == Z3.IntVal(2))
    Z3.add(solver, Z3.Not(before == z3_add(Z3.Expr[after, record])))
    status = string(Z3.check(solver))

    erased = Z3.Solver()
    eb = Z3.IntVar("erased_before")
    ea = Z3.IntVar("erased_after")
    er = Z3.IntVar("erased_record")
    Z3.add(erased, ea == z3_sub(Z3.Expr[eb, Z3.IntVal(2)]))
    Z3.add(erased, er == Z3.IntVal(0))
    Z3.add(erased, Z3.Not(eb == z3_add(Z3.Expr[ea, er])))
    erased_status = string(Z3.check(erased))
    return Dict(
        "ran" => true,
        "load_bearing" => true,
        "solver" => "Z3.jl",
        "verdict" => status,
        "erased_record_control_verdict" => erased_status,
        "erased_flip_unsat_to_sat" => status == "unsat" && erased_status == "sat",
    )
end

function main()
    Dz = [0.7 0.0 0.0; 0.0 0.7 0.0; 0.0 0.0 1.0]
    Dx = [1.0 0.0 0.0; 0.0 0.7 0.0; 0.0 0.0 0.7]
    Rx = [1.0 0.0 0.0; 0.0 0.0 -1.0; 0.0 1.0 0.0]
    Rz = [0.0 -1.0 0.0; 1.0 0.0 0.0; 0.0 0.0 1.0]
    zero = [0.0, 0.0, 0.0]
    rows = Dict(
        "D_z" => six_state_holevo(Dz, zero),
        "D_x" => six_state_holevo(Dx, zero),
        "R_x" => six_state_holevo(Rx, zero),
        "R_z" => six_state_holevo(Rz, zero),
    )
    z3_row = julia_z3_conservation()
    pure_guard_entropy = qo_entropy_guard()
    all_pass = (
        abs(rows["R_x"]["information_killed_from_identity_nats"]) < 1e-10 &&
        abs(rows["R_z"]["information_killed_from_identity_nats"]) < 1e-10 &&
        rows["D_z"]["information_killed_from_identity_nats"] > 0 &&
        rows["D_x"]["information_killed_from_identity_nats"] > 0 &&
        abs(pure_guard_entropy) < 1e-12 &&
        z3_row["erased_flip_unsat_to_sat"]
    )
    payload = Dict(
        "schema_version" => "$(SIM_ID)_julia_leg_v1",
        "sim_id" => SIM_ID,
        "object_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_quantumoptics_information_throughput_leg",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "source_path" => rel(SOURCE),
        "source_sha256" => sha256_file(SOURCE),
        "result_path" => rel(RESULT),
        "julia_project" => Base.active_project(),
        "reads_peer_result" => false,
        "log_base" => "e",
        "packages_used" => ["QuantumOptics", "Z3", "LinearAlgebra", "JSON", "SHA"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "Z3"],
        "s4_six_state_rows" => rows,
        "quantumoptics_guard" => Dict(
            "api" => "QuantumOptics.SpinBasis / QuantumOptics.dm / QuantumOptics.entropy_vn / QuantumOptics.DenseOperator",
            "pure_state_entropy_nats" => pure_guard_entropy,
        ),
        "crossover_proofs" => Dict("julia_z3" => z3_row),
        "capability_receipts" => Dict(
            "active_project" => Base.active_project(),
            "QuantumOptics.SpinBasis" => "loaded_and_used",
            "Z3.Solver" => "loaded_and_checked",
        ),
        "TOOL_MANIFEST" => Dict(
            "QuantumOptics" => Dict("used" => true, "reason" => "load-bearing entropy_vn on qubit density operators for pinned S4 throughput rows"),
            "Z3" => Dict("used" => true, "reason" => "load-bearing finite quotient conservation identity control"),
            "JSON" => Dict("used" => true, "reason" => "structured result write"),
            "LinearAlgebra" => Dict("used" => true, "reason" => "supportive matrix arithmetic"),
            "SHA" => Dict("used" => true, "reason" => "supportive source hashing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("QuantumOptics" => "load_bearing", "Z3" => "load_bearing", "JSON" => "supportive", "LinearAlgebra" => "supportive", "SHA" => "supportive"),
        "claim_path_tools" => ["QuantumOptics", "Z3"],
        "tool_calls" => [
            Dict(
                "tool" => "QuantumOptics",
                "qualified_api/function" => "QuantumOptics.SpinBasis/QuantumOptics.DenseOperator/QuantumOptics.dm/QuantumOptics.entropy_vn",
                "input_object" => "pinned qubit density operators from Bloch six-state ensemble",
                "output_object" => "Holevo throughput and information killed for D_z, D_x, R_x, R_z",
                "positive_case" => "unitary rows kill zero and dephasing rows kill positive off-axis information",
                "negative/erased_control" => "pure-state entropy guard is zero",
                "boundary_case" => "one-qubit SpinBasis(1//2)",
                "demotion_condition" => "demote if entropy_vn route is replaced by literals only",
                "gates" => ["s4_six_state_rows", "all_pass"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.add/Z3.check",
                "input_object" => "integer coefficients of log(2) for before/after/record",
                "output_object" => "unsat conservation identity and sat erased-record control",
                "positive_case" => "before = after + record is forced",
                "negative/erased_control" => "record=0 makes conservation violation satisfiable",
                "boundary_case" => "Z4 coefficient 2",
                "demotion_condition" => "demote if solver binds a precomputed boolean",
                "gates" => ["julia_z3_conservation", "all_pass"],
            ),
        ],
        "all_pass" => all_pass,
    )
    mkpath(dirname(RESULT))
    open(RESULT, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => payload["all_pass"], "result_path" => rel(RESULT))))
    return payload["all_pass"] ? 0 : 1
end

exit(main())
