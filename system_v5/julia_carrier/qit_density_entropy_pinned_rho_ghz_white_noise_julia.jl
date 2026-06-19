#!/usr/bin/env julia
# object_id: qit_density_entropy_pinned_rho_ghz_white_noise_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using QuantumOptics

const OBJECT_ID = "qit_density_entropy_pinned_rho_ghz_white_noise_julia"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "qit_density_entropy_pinned_rho_ghz_white_noise_julia_results.json")
const SOURCE_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "qit_density_entropy_pinned_rho_ghz_white_noise_julia.jl")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const N_QUBITS = 3
const DIM = 2^N_QUBITS
const WHITE_NOISE_P = 0.3
const TOL = 1.0e-10

function ghz_state(b::SpinBasis)
    zero = spindown(b)
    one = spinup(b)
    return (tensor(zero, zero, zero) + tensor(one, one, one)) / sqrt(2.0)
end

function pinned_density(p::Float64, h)
    # Pinned shared observable for the three-engine packet:
    # rho(p) = (1-p)|GHZ><GHZ| + p * I/8, p=0.3, no dephasing.
    psi = ghz_state(h.bases[1])
    rho_pure = dm(psi)
    rho_maxmix = identityoperator(h) / DIM
    return (1.0 - p) * rho_pure + p * rho_maxmix
end

function analytic_spectrum(p::Float64)
    high = 1.0 - 7.0 * p / 8.0
    low = p / 8.0
    return vcat([low for _ in 1:7], [high])
end

function analytic_entropy(p::Float64)
    vals = analytic_spectrum(p)
    return -sum(v * log(v) for v in vals if v > 0)
end

function matrix_checks(rho)
    data = dense(rho).data
    eigs = sort(real.(eigvals(Hermitian(data))))
    expected = sort(analytic_spectrum(WHITE_NOISE_P))
    entropy_value = Float64(real(entropy_vn(rho)))
    entropy_expected = analytic_entropy(WHITE_NOISE_P)
    return Dict{String,Any}(
        "trace_real" => Float64(real(tr(rho))),
        "trace_imag_abs" => Float64(abs(imag(tr(rho)))),
        "hermitian_residual_fro" => Float64(norm(data - data')),
        "min_eigenvalue" => Float64(minimum(eigs)),
        "max_eigenvalue" => Float64(maximum(eigs)),
        "spectrum" => [Float64(v) for v in eigs],
        "expected_spectrum" => [Float64(v) for v in expected],
        "spectrum_max_abs_residual" => Float64(maximum(abs.(eigs .- expected))),
        "entropy_residual_vs_analytic" => Float64(abs(entropy_value - entropy_expected)),
        "psd_with_tol" => Bool(minimum(eigs) >= -TOL),
    )
end

function main()
    b = SpinBasis(1//2)
    h = tensor(b, b, b)
    rho = pinned_density(WHITE_NOISE_P, h)
    checks = matrix_checks(rho)
    vn_entropy = Float64(real(entropy_vn(rho)))
    analytic = analytic_entropy(WHITE_NOISE_P)
    all_pass = Bool(
        checks["psd_with_tol"] &&
        abs(checks["trace_real"] - 1.0) <= TOL &&
        checks["trace_imag_abs"] <= TOL &&
        checks["hermitian_residual_fro"] <= TOL &&
        checks["spectrum_max_abs_residual"] <= TOL &&
        checks["entropy_residual_vs_analytic"] <= TOL &&
        CLASSIFICATION == "scratch_diagnostic" &&
        PROMOTION_ALLOWED == false &&
        FORMAL_ADMISSION_ALLOWED == false &&
        READS_PEER_RESULT == false
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
        "peer_result_path" => nothing,
        "pinned_spec" => Dict{String,Any}(
            "name" => "GHZ white-noise density, no dephasing",
            "formula" => "rho(p) = (1-p)|GHZ><GHZ| + p*I/8",
            "p" => WHITE_NOISE_P,
            "n_qubits" => N_QUBITS,
            "hilbert_dimension" => DIM,
            "basis_order" => "QuantumOptics tensor(SpinBasis(1//2), SpinBasis(1//2), SpinBasis(1//2)); entropy is spectrum-invariant",
            "entropy_base" => "natural_log",
            "dephasing_included" => false,
        ),
        "values" => Dict{String,Any}(
            "vn_entropy" => vn_entropy,
            "analytic_entropy" => analytic,
            "entropy_residual_vs_analytic" => abs(vn_entropy - analytic),
            "spectrum_high" => 1.0 - 7.0 * WHITE_NOISE_P / 8.0,
            "spectrum_low" => WHITE_NOISE_P / 8.0,
            "entropy_upper_log8" => log(Float64(DIM)),
            "entropy_in_bounds_0_to_log8" => Bool(-TOL <= vn_entropy <= log(Float64(DIM)) + TOL),
        ),
        "checks" => Dict{String,Any}(
            "ran_standalone" => true,
            "uses_quantumoptics" => true,
            "quantumoptics_load_bearing" => true,
            "rho_checks" => checks,
            "all_pass" => all_pass,
        ),
        "all_pass" => all_pass,
        "tools" => ["QuantumOptics", "Julia LinearAlgebra", "Julia stdlib JSON/Dates"],
        "TOOL_MANIFEST" => Dict{String,Any}(
            "QuantumOptics" => Dict(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing SpinBasis tensor Hilbert space, GHZ ket, density operator, identity operator, and entropy_vn calculation for the pinned rho(p)"
            ),
            "Julia LinearAlgebra" => Dict(
                "tried" => true,
                "used" => true,
                "reason" => "supportive Hermitian eigenspectrum and residual checks against the pinned analytic spectrum"
            ),
            "Julia JSON/Dates stdlib path support" => Dict(
                "tried" => true,
                "used" => true,
                "reason" => "supportive result serialization and timestamping"
            ),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}(
            "QuantumOptics" => "load_bearing",
            "Julia LinearAlgebra" => "supportive",
            "Julia JSON/Dates stdlib path support" => "supportive",
        ),
        "claim_ceiling" => "Julia leg for one pinned QIT density/entropy scratch scout: rho(p)=(1-p)|GHZ><GHZ|+pI/8 at p=0.3, natural-log entropy. No peer reads, no promotion, no formal admission.",
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote ", RESULT_PATH)
    println("SCOUT_DONE all_pass=", all_pass, " vn_entropy=", vn_entropy, " p=", WHITE_NOISE_P, " reads_peer_result=", READS_PEER_RESULT)
    return all_pass ? 0 : 2
end

exit(main())
