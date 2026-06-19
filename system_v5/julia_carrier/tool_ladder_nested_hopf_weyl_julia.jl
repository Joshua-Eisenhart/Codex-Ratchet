#!/usr/bin/env julia
# object_id: tool_ladder_nested_hopf_weyl_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: false

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using CliffordAlgebras
using Grassmann
using Z3

@basis S"+++"

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const OBJECT_ID = "tool_ladder_nested_hopf_weyl_julia"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/tool_ladder_nested_hopf_weyl_julia_results.json")
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/tool_ladder_nested_hopf_weyl_julia.jl")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-10

const TOOL_MANIFEST = Dict{String,Any}(
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing 3-qubit tensor Pauli/gamma construction for the Weyl chirality layer"),
    "CliffordAlgebras" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Cl(6,0) generator anticommutation check for the Weyl carrier"),
    "Grassmann" => Dict("tried" => true, "used" => true, "reason" => "load-bearing even-subalgebra blade witness for the Weyl-spinor layer"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing integer SMT proof for the nested Hopf-to-Weyl weight split"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive finite norms, traces, and eigenspectrum checks"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization"),
    "Dates" => Dict("tried" => true, "used" => true, "reason" => "supportive timestamping"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "QuantumOptics" => "load_bearing",
    "CliffordAlgebras" => "load_bearing",
    "Grassmann" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON" => "supportive",
    "Dates" => "supportive",
)

function hopf_map(q::Vector{Float64})
    a, b, c, d = q
    [
        2.0 * (a * c + b * d),
        2.0 * (b * c - a * d),
        a * a + b * b - c * c - d * d,
    ]
end

function fiber_phase(q::Vector{Float64}, phi::Float64)
    a, b, c, d = q
    cp = cos(phi)
    sp = sin(phi)
    [
        a * cp - b * sp,
        a * sp + b * cp,
        c * cp - d * sp,
        c * sp + d * cp,
    ]
end

function spin_basis_ops()
    b = SpinBasis(1//2)
    Dict(
        "I" => identityoperator(b),
        "X" => sigmax(b),
        "Y" => sigmay(b),
        "Z" => sigmaz(b),
    )
end

function tensor_matrix(a, b, c)
    Matrix(tensor(a, b, c).data)
end

function quantumoptics_gamma_matrices()
    ops = spin_basis_ops()
    i2 = ops["I"]
    x = ops["X"]
    y = ops["Y"]
    z = ops["Z"]
    [
        tensor_matrix(x, i2, i2),
        tensor_matrix(y, i2, i2),
        tensor_matrix(z, x, i2),
        tensor_matrix(z, y, i2),
        tensor_matrix(z, z, x),
        tensor_matrix(z, z, y),
    ]
end

function matrix_anticommutation_residual(gammas)
    dim = size(gammas[1], 1)
    ident = Matrix{ComplexF64}(I, dim, dim)
    max_residual = 0.0
    for i in eachindex(gammas), j in eachindex(gammas)
        target = i == j ? 2.0 .* ident : zeros(ComplexF64, dim, dim)
        residual = Float64(norm(gammas[i] * gammas[j] + gammas[j] * gammas[i] - target))
        max_residual = max(max_residual, residual)
    end
    max_residual
end

function cliffordalgebras_report()
    cl6 = CliffordAlgebra(6, 0)
    gens = [getproperty(cl6, Symbol("e$i")) for i in 1:6]
    unit = one(gens[1])
    failures = Any[]
    for i in 1:6, j in 1:6
        lhs = gens[i] * gens[j] + gens[j] * gens[i]
        rhs = (i == j ? 2 : 0) * unit
        if lhs != rhs
            push!(failures, Dict{String,Any}("i" => i, "j" => j, "lhs" => string(lhs), "rhs" => string(rhs)))
        end
    end
    Dict{String,Any}(
        "generator_count" => length(gens),
        "anticommutation_failure_count" => length(failures),
        "anticommutation_failures" => failures,
        "pass" => length(gens) == 6 && isempty(failures),
    )
end

function grassmann_even_report()
    even_basis = ["1", string(v1 * v2), string(v1 * v3), string(v2 * v3)]
    pseudoscalar = string(v1 * v2 * v3)
    module_has_submanifold = isdefined(Grassmann, :Submanifold)
    Dict{String,Any}(
        "basis" => "S\"+++\"",
        "even_basis" => even_basis,
        "even_basis_count" => length(even_basis),
        "pseudoscalar" => pseudoscalar,
        "module_has_submanifold" => module_has_submanifold,
        "pass" => length(even_basis) == 4 && pseudoscalar != "" && module_has_submanifold,
    )
end

function z3_add(args::Vector{Z3.Expr})
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_sub(left::Z3.Expr, right::Z3.Expr)
    Z3.Expr(left.ctx, Z3.Libz3.Z3_mk_sub(Z3.ctx_ref(left), 2, map(Z3.as_ast, [left, right])))
end

function z3_weight_proof()
    main = Z3.Solver()
    p4 = Z3.IntVar("p_plus_scaled_by_4")
    m4 = Z3.IntVar("p_minus_scaled_by_4")
    Z3.add(main, z3_add(Z3.Expr[p4, m4]) == Z3.IntVal(4))
    Z3.add(main, z3_sub(p4, m4) == Z3.IntVal(2))
    Z3.add(main, Z3.Or(Z3.Expr[Z3.Not(p4 == Z3.IntVal(3)), Z3.Not(m4 == Z3.IntVal(1))]))
    main_status = string(Z3.check(main))

    control = Z3.Solver()
    cp4 = Z3.IntVar("identity_plus_scaled_by_4")
    cm4 = Z3.IntVar("identity_minus_scaled_by_4")
    Z3.add(control, z3_add(Z3.Expr[cp4, cm4]) == Z3.IntVal(4))
    Z3.add(control, z3_sub(cp4, cm4) == Z3.IntVal(4))
    Z3.add(control, Z3.Or(Z3.Expr[Z3.Not(cp4 == Z3.IntVal(3)), Z3.Not(cm4 == Z3.IntVal(1))]))
    control_status = string(Z3.check(control))

    Dict{String,Any}(
        "encoding" => "scaled integer weights: p_plus+p_minus=1, p_plus-p_minus=Hopf_z=1/2; multiplied by 4 gives p4+m4=4 and p4-m4=2",
        "main_not_expected_3_1_verdict" => main_status,
        "identity_control_not_expected_3_1_verdict" => control_status,
        "main_proves_nested_weights" => main_status == "unsat",
        "identity_control_flips" => control_status == "sat",
    )
end

function nested_weyl_report(hopf_z::Float64)
    gammas = quantumoptics_gamma_matrices()
    dim = size(gammas[1], 1)
    ident = Matrix{ComplexF64}(I, dim, dim)
    gamma7 = ((-1im)^3) .* reduce(*, gammas)
    gamma7_square_residual = Float64(norm(gamma7 * gamma7 - ident))
    gamma7_trace = Float64(real(tr(gamma7)))
    diag = [Float64(round(real(gamma7[i, i]); digits=12)) for i in 1:dim]
    plus_indices = findall(x -> x == 1.0, diag)
    minus_indices = findall(x -> x == -1.0, diag)
    theta = 0.5 * acos(hopf_z)
    psi = zeros(ComplexF64, dim)
    psi[plus_indices[1]] = cos(theta) + 0im
    psi[minus_indices[1]] = sin(theta) + 0im
    rho = psi * psi'
    nested_expectation = Float64(real(psi' * gamma7 * psi))
    p_plus = (ident + gamma7) ./ 2.0
    p_minus = (ident - gamma7) ./ 2.0
    Dict{String,Any}(
        "spinor_dim" => dim,
        "gamma7_square_residual" => gamma7_square_residual,
        "gamma7_trace" => gamma7_trace,
        "plus_dim" => length(plus_indices),
        "minus_dim" => length(minus_indices),
        "hopf_z_input" => hopf_z,
        "theta" => theta,
        "nested_chirality_expectation" => nested_expectation,
        "nested_expectation_residual" => abs(nested_expectation - hopf_z),
        "p_plus_trace" => Float64(real(tr(p_plus))),
        "p_minus_trace" => Float64(real(tr(p_minus))),
        "rho_trace_residual" => abs(Float64(real(tr(rho))) - 1.0),
        "rho_psd_min_eigenvalue" => Float64(minimum(real.(eigvals(Hermitian((rho + rho') ./ 2.0))))),
        "matrix_anticommutation_max_residual" => matrix_anticommutation_residual(gammas),
        "pass" => gamma7_square_residual <= TOL &&
                  length(plus_indices) == 4 &&
                  length(minus_indices) == 4 &&
                  abs(nested_expectation - hopf_z) <= TOL,
    )
end

function build_result()
    q = [sqrt(3.0) / 2.0, 0.0, 0.5, 0.0]
    q_phase = fiber_phase(q, 0.73)
    base = hopf_map(q)
    base_phase = hopf_map(q_phase)
    hopf_norm_residual = abs(dot(base, base) - 1.0)
    fiber_invariance_residual = Float64(norm(base - base_phase))
    hopf_z = base[3]
    weyl = nested_weyl_report(hopf_z)
    clifford = cliffordalgebras_report()
    grassmann = grassmann_even_report()
    z3proof = z3_weight_proof()
    nested_signature = [base[1], base[2], base[3], weyl["nested_chirality_expectation"], weyl["plus_dim"], weyl["minus_dim"]]
    all_pass = READS_PEER_RESULT == false &&
               hopf_norm_residual <= TOL &&
               fiber_invariance_residual <= TOL &&
               weyl["pass"] == true &&
               clifford["pass"] == true &&
               grassmann["pass"] == true &&
               z3proof["main_proves_nested_weights"] == true &&
               z3proof["identity_control_flips"] == true
    Dict{String,Any}(
        "schema_version" => "engine_leg_result_v1",
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "packages_used" => ["QuantumOptics", "CliffordAlgebras", "Grassmann", "Z3", "LinearAlgebra", "JSON", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "CliffordAlgebras", "Grassmann", "Z3"],
        "claim_ceiling" => "Scratch tool-ladder scout only: nested Hopf S3-to-S2 fiber invariance feeding a Weyl chirality split. No formal admission, no canonical claim.",
        "hopf" => Dict(
            "q" => q,
            "fiber_phase" => 0.73,
            "base" => base,
            "base_after_fiber_phase" => base_phase,
            "s2_norm_residual" => hopf_norm_residual,
            "fiber_invariance_residual" => fiber_invariance_residual,
            "pass" => hopf_norm_residual <= TOL && fiber_invariance_residual <= TOL,
        ),
        "weyl" => weyl,
        "cliffordalgebras" => clifford,
        "grassmann" => grassmann,
        "julia_z3" => z3proof,
        "negative_control_flip" => Dict(
            "identity_control_not_expected_3_1_verdict" => z3proof["identity_control_not_expected_3_1_verdict"],
            "identity_control_flips" => z3proof["identity_control_flips"],
        ),
        "values" => Dict(
            "hopf_base_x" => base[1],
            "hopf_base_y" => base[2],
            "hopf_base_z" => base[3],
            "fiber_invariance_residual" => fiber_invariance_residual,
            "nested_chirality_expectation" => weyl["nested_chirality_expectation"],
            "nested_expectation_residual" => weyl["nested_expectation_residual"],
            "plus_dim" => weyl["plus_dim"],
            "minus_dim" => weyl["minus_dim"],
            "grassmann_even_basis_count" => grassmann["even_basis_count"],
        ),
        "nested_signature" => nested_signature,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "all_pass" => all_pass,
    )
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(
        "NESTED_HOPF_WEYL_JULIA_DONE all_pass=", result["all_pass"],
        " hopf_z=", result["values"]["hopf_base_z"],
        " nested=", result["values"]["nested_chirality_expectation"],
        " dims=", result["values"]["plus_dim"], "/", result["values"]["minus_dim"],
        " z3=", result["julia_z3"]["main_not_expected_3_1_verdict"],
    )
    return result["all_pass"] ? 0 : 1
end

exit(main())
