#!/usr/bin/env julia
# object_id: qit_cptp_dephasing_pinned_rho_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using QuantumOptics

const OBJECT_ID = "qit_cptp_dephasing_pinned_rho_julia"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "qit_cptp_dephasing_pinned_rho_julia_results.json")
const SOURCE_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "qit_cptp_dephasing_pinned_rho_julia.jl")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const P = 0.3
const GAMMA = 0.4
const DIM = 8
const TOL = 1e-10

function computational_kets(b::SpinBasis)
    zero = spindown(b); one = spinup(b)
    [tensor(bits...) for bits in Iterators.product((zero, one), (zero, one), (zero, one))]
end

function ghz_state(b::SpinBasis)
    zero = spindown(b); one = spinup(b)
    (tensor(zero, zero, zero) + tensor(one, one, one)) / sqrt(2.0)
end

function rho_pinned(p::Float64, h)
    psi = ghz_state(h.bases[1])
    (1.0 - p) * dm(psi) + p * identityoperator(h) / DIM
end

function dephase(rho, gamma::Float64, h)
    pinched = zero(rho)
    for ket in computational_kets(h.bases[1])
        proj = dm(ket)
        pinched += proj * rho * proj
    end
    (1.0 - gamma) * rho + gamma * pinched
end

function analytic_spectrum_after(p::Float64, gamma::Float64)
    a = (1.0 - p) / 2.0 + p / 8.0
    b = (1.0 - gamma) * (1.0 - p) / 2.0
    low = p / 8.0
    sort(vcat([low for _ in 1:6], [a - b, a + b]))
end

function entropy_from(vals)
    -sum(v * log(v) for v in vals if v > 0)
end

function matrix_checks(rho, expected)
    data = dense(rho).data
    eigs = sort(real.(eigvals(Hermitian(data))))
    Dict{String,Any}(
        "trace_real" => Float64(real(tr(rho))),
        "trace_imag_abs" => Float64(abs(imag(tr(rho)))),
        "hermitian_residual_fro" => Float64(norm(data - data')),
        "min_eigenvalue" => Float64(minimum(eigs)),
        "max_eigenvalue" => Float64(maximum(eigs)),
        "spectrum" => [Float64(v) for v in eigs],
        "expected_spectrum" => [Float64(v) for v in expected],
        "spectrum_max_abs_residual" => Float64(maximum(abs.(eigs .- expected))),
        "psd_with_tol" => Bool(minimum(eigs) >= -TOL)
    )
end

function main()
    b = SpinBasis(1//2); h = tensor(b, b, b)
    rho0 = rho_pinned(P, h)
    rho1 = dephase(rho0, GAMMA, h)
    expected = analytic_spectrum_after(P, GAMMA)
    entropy_before = Float64(real(entropy_vn(rho0)))
    entropy_after = Float64(real(entropy_vn(rho1)))
    analytic_after = entropy_from(expected)
    checks = matrix_checks(rho1, expected)
    all_pass = Bool(
        checks["psd_with_tol"] && abs(checks["trace_real"] - 1.0) <= TOL &&
        checks["trace_imag_abs"] <= TOL && checks["hermitian_residual_fro"] <= TOL &&
        checks["spectrum_max_abs_residual"] <= TOL && abs(entropy_after - analytic_after) <= TOL &&
        entropy_after >= entropy_before - TOL && READS_PEER_RESULT == false
    )
    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia_quantumoptics",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "julia_version" => string(VERSION),
        "active_project" => Base.active_project(),
        "reads_peer_result" => READS_PEER_RESULT,
        "pinned_spec" => Dict("rho_formula" => "rho(p)=(1-p)|GHZ><GHZ|+pI/8", "p" => P, "channel" => "computational_basis_dephasing", "gamma" => GAMMA, "entropy_base" => "natural_log", "n_qubits" => 3, "hilbert_dimension" => DIM, "spectrum_after_exact" => "{239/400, 71/400, 15/400 x 6}"),
        "values" => Dict("vn_entropy_before" => entropy_before, "vn_entropy_after" => entropy_after, "analytic_entropy_after" => analytic_after, "entropy_change" => entropy_after - entropy_before, "spectrum_high" => 239/400, "spectrum_mid" => 71/400, "spectrum_low" => 15/400),
        "density_checks" => checks,
        "all_pass" => all_pass,
        "TOOL_MANIFEST" => Dict("QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing density construction, computational-basis projectors, dephasing channel, and entropy_vn"), "Julia LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive eigenspectrum residual check"), "Julia JSON/Dates stdlib path support" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization")),
        "TOOL_INTEGRATION_DEPTH" => Dict("QuantumOptics" => "load_bearing", "Julia LinearAlgebra" => "supportive", "Julia JSON/Dates stdlib path support" => "supportive"),
        "claim_ceiling" => "Julia leg for one pinned CPTP dephasing scratch scout over rho(p); no peer reads, no promotion, no formal admission."
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2); write(io, "\n")
    end
    println("wrote ", RESULT_PATH)
    println("SCOUT_DONE all_pass=", all_pass, " entropy_after=", entropy_after, " entropy_change=", entropy_after - entropy_before, " reads_peer_result=", READS_PEER_RESULT)
    return all_pass ? 0 : 2
end

exit(main())
