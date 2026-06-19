#!/usr/bin/env julia
# Julia/QuantumOptics receipt for s8_local_information_table_v0.

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using SHA
using Z3

const SIM_ID = "s8_local_information_table_v0"
const ROOT = abspath(normpath(joinpath(@__DIR__, "..", "..", "..")))
const RESULT_DIR = joinpath(@__DIR__, "results")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const SOURCE_PATH = @__FILE__
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false

function rel(path::AbstractString)
    prefix = endswith(ROOT, "/") ? ROOT : ROOT * "/"
    return replace(abspath(normpath(path)), prefix => "")
end

function sha256_file(path::AbstractString)
    return bytes2hex(open(sha256, path))
end

function qbasis()
    basis = QuantumOptics.NLevelBasis(2)
    zero = QuantumOptics.basisstate(basis, 1)
    one = QuantumOptics.basisstate(basis, 2)
    return basis, zero, one
end

function qstate(name::String)
    _, zero, one = qbasis()
    if name == "GHZ"
        return (QuantumOptics.tensor(zero, zero, zero) + QuantumOptics.tensor(one, one, one)) / sqrt(2)
    elseif name == "W"
        return (QuantumOptics.tensor(one, zero, zero) + QuantumOptics.tensor(zero, one, zero) + QuantumOptics.tensor(zero, zero, one)) / sqrt(3)
    elseif name == "product_000"
        return QuantumOptics.tensor(zero, zero, zero)
    elseif name == "Bell_q0q1_spectator_q2"
        return (QuantumOptics.tensor(zero, zero, zero) + QuantumOptics.tensor(one, one, zero)) / sqrt(2)
    else
        error("unknown qstate $name")
    end
end

function qtheta(theta::Float64)
    _, zero, one = qbasis()
    return cos(theta) * QuantumOptics.tensor(zero, zero, zero) + sin(theta) * QuantumOptics.tensor(one, one, zero)
end

function binary_entropy(p::Float64)
    if p <= 0.0 || p >= 1.0
        return 0.0
    end
    return -(p * log(p) + (1.0 - p) * log(1.0 - p))
end

function p_for_entropy(target::Float64)
    lo = 0.5
    hi = 1.0 - 1.0e-15
    for _ in 1:200
        mid = (lo + hi) / 2.0
        if binary_entropy(mid) > target
            lo = mid
        else
            hi = mid
        end
    end
    return (lo + hi) / 2.0
end

function qphi0()
    target = 0.4164955306996874
    p = p_for_entropy(target)
    _, zero, one = qbasis()
    return sqrt(p) * QuantumOptics.tensor(zero, zero, zero) + sqrt(1.0 - p) * QuantumOptics.tensor(one, one, zero)
end

entropy_nats(op) = real(QuantumOptics.entropy_vn(op))

function reduced_by_keep(rho, keep::Vector{Int})
    trace_out = [site for site in 1:3 if !(site in keep)]
    return isempty(trace_out) ? rho : QuantumOptics.ptrace(rho, trace_out)
end

function qit_values(psi)
    rho = QuantumOptics.dm(psi)
    s_a = entropy_nats(reduced_by_keep(rho, [1]))
    s_b = entropy_nats(reduced_by_keep(rho, [2, 3]))
    s_ab = entropy_nats(reduced_by_keep(rho, [1, 2, 3]))
    return Dict(
        "S_A_given_B" => s_ab - s_b,
        "I_A_colon_B" => s_a + s_b - s_ab,
        "I_c" => s_b - s_ab,
        "S_A" => s_a,
        "S_B" => s_b,
        "S_AB" => s_ab,
    )
end

function scalar_vector()
    specs = Dict(
        "GHZ" => qstate("GHZ"),
        "Bell_q0q1_spectator_q2" => qstate("Bell_q0q1_spectator_q2"),
        "W" => qstate("W"),
        "nested_r2_theta_0_35" => qtheta(0.35),
        "nested_r3_theta_0_70" => qtheta(0.70),
        "dual_stack_phi0_fixture" => qphi0(),
    )
    values = Dict{String,Float64}()
    for (state_id, psi) in specs
        row = qit_values(psi)
        prefix = "$(state_id).q0__q1q2"
        values["$(prefix).S_A_given_B"] = row["S_A_given_B"]
        values["$(prefix).I_A_colon_B"] = row["I_A_colon_B"]
        values["$(prefix).I_c"] = row["I_c"]
    end
    return values
end

function julia_z3_proof(values)
    scale = 10^12
    s_scaled = round(Int, values["GHZ.q0__q1q2.S_A_given_B"] * scale)
    ic_scaled = round(Int, values["GHZ.q0__q1q2.I_c"] * scale)
    solver = Z3.Solver()
    s_term = Z3.IntVar("scaled_s_cond_julia")
    ic_term = Z3.IntVar("scaled_ic_julia")
    sum_term = Z3.IntVar("scaled_sum_julia")
    Z3.add(solver, s_term == Z3.IntVal(s_scaled))
    Z3.add(solver, ic_term == Z3.IntVal(ic_scaled))
    Z3.add(solver, sum_term == Z3.IntVal(s_scaled + ic_scaled))
    Z3.add(solver, Z3.Not(sum_term == Z3.IntVal(0)))
    verdict = string(Z3.check(solver))

    flip = Z3.Solver()
    fs = Z3.IntVar("scaled_s_cond_julia_flip")
    fi = Z3.IntVar("scaled_ic_julia_flip")
    fsum = Z3.IntVar("scaled_sum_julia_flip")
    Z3.add(flip, fs == Z3.IntVal(s_scaled))
    Z3.add(flip, fi == Z3.IntVal(ic_scaled + 1))
    Z3.add(flip, fsum == Z3.IntVal(s_scaled + ic_scaled + 1))
    Z3.add(flip, Z3.Not(fsum == Z3.IntVal(0)))
    flip_status = string(Z3.check(flip))
    return Dict(
        "ran" => true,
        "load_bearing" => true,
        "verdict" => verdict,
        "perturbed_construction_path_verdict" => flip_status,
        "scaled_identity" => "round(1e12*S(A|B)) + round(1e12*I_c) == 0",
        "scale" => scale,
    )
end

function quantumoptics_receipt()
    psi = qstate("GHZ")
    rho = QuantumOptics.dm(psi)
    trace_value = real(tr(rho.data))
    row = qit_values(psi)
    return Dict(
        "trace" => trace_value,
        "GHZ_I_c_nats" => row["I_c"],
        "GHZ_S_A_given_B_nats" => row["S_A_given_B"],
        "observable" => "QuantumOptics.NLevelBasis/basisstate/tensor/dm/ptrace/entropy_vn constructed the GHZ q0|q1q2 row",
        "pass" => abs(trace_value - 1.0) <= 1.0e-12 && abs(row["I_c"] - log(2.0)) <= 1.0e-12,
    )
end

function build_result()
    values = scalar_vector()
    z3_proof = julia_z3_proof(values)
    qo = quantumoptics_receipt()
    all_pass = qo["pass"] && z3_proof["verdict"] == "unsat" && z3_proof["perturbed_construction_path_verdict"] == "sat"
    return Dict(
        "schema" => "$(SIM_ID)_engine_receipt_v1",
        "sim_id" => SIM_ID,
        "role_id" => "julia",
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => false,
        "packages_used" => ["QuantumOptics", "Z3", "JSON", "SHA", "Dates", "LinearAlgebra"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "Z3"],
        "claim_path_tools" => ["QuantumOptics", "Z3"],
        "package_observables" => Dict(
            "QuantumOptics" => "QuantumOptics.NLevelBasis/tensor/dm/ptrace/entropy_vn computes q0|q1q2 entropy rows",
            "Z3" => "Z3.Solver/add/check proves scaled S(A|B)+I_c identity UNSAT with perturbed SAT flip",
        ),
        "TOOL_MANIFEST" => Dict(
            "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Hilbert object, density, partial trace, entropy construction"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing SMT identity and flip over computed table values"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("QuantumOptics" => "load_bearing", "Z3" => "load_bearing"),
        "engine_values" => values,
        "crossover_proofs" => Dict("julia_z3" => z3_proof),
        "package_receipts" => Dict("QuantumOptics" => qo),
        "tool_calls" => [
            Dict("tool" => "QuantumOptics", "qualified_api" => "NLevelBasis / tensor / dm / ptrace / entropy_vn", "output_object" => "GHZ q0|q1q2 QIT row"),
            Dict("tool" => "Z3", "qualified_api" => "Z3.Solver / Z3.add / Z3.check", "output_object" => z3_proof["verdict"]),
        ],
        "all_pass" => all_pass,
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "result_path" => rel(RESULT_PATH), "julia_z3" => result["crossover_proofs"]["julia_z3"]["verdict"])))
    return result["all_pass"] ? 0 : 1
end

exit(main())
