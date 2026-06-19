using Dates
using LinearAlgebra
using Random
using Printf
using SHA

const OBJECT_ID = "c3_chirality_constraint_candidate_v1"
const RESULT_PATH = joinpath(@__DIR__, "c3_chirality_constraint_candidate_results.json")
const TOL = 1.0e-9

struct JObject
    fields::Vector{Pair{String, Any}}
end

jobj(pairs::Pair...) = JObject(Pair{String, Any}[string(pair.first) => pair.second for pair in pairs])

function json_escape(s::AbstractString)::String
    io = IOBuffer()
    for c in s
        if c == '"'
            print(io, "\\\"")
        elseif c == '\\'
            print(io, "\\\\")
        elseif c == '\n'
            print(io, "\\n")
        elseif c == '\r'
            print(io, "\\r")
        elseif c == '\t'
            print(io, "\\t")
        elseif Int(c) < 0x20
            print(io, @sprintf("\\u%04x", Int(c)))
        else
            print(io, c)
        end
    end
    return String(take!(io))
end

function json_value(x, indent::Int=0)::String
    pad = " "^indent
    nextpad = " "^(indent + 2)
    if x isa JObject
        isempty(x.fields) && return "{}"
        parts = String[]
        for pair in x.fields
            push!(parts, nextpad * "\"" * json_escape(pair.first) * "\": " *
                         json_value(pair.second, indent + 2))
        end
        return "{\n" * join(parts, ",\n") * "\n" * pad * "}"
    elseif x isa AbstractString
        return "\"" * json_escape(x) * "\""
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x === nothing
        return "null"
    elseif x isa Integer
        return string(x)
    elseif x isa AbstractFloat
        isfinite(x) || error("Non-finite float cannot be serialized to JSON")
        return @sprintf("%.12g", x)
    elseif x isa AbstractVector
        isempty(x) && return "[]"
        parts = [nextpad * json_value(v, indent + 2) for v in x]
        return "[\n" * join(parts, ",\n") * "\n" * pad * "]"
    else
        error("Unsupported JSON value of type $(typeof(x))")
    end
end

function write_json(path::AbstractString, root::JObject)
    open(path, "w") do io
        write(io, json_value(root))
        write(io, "\n")
    end
end

sha256_file(path::AbstractString) = bytes2hex(sha256(read(path)))

struct Carrier
    name::String
    dim::Int
    description::String
end

struct Probe
    name::String
    matrix::Matrix{ComplexF64}
    role::String
end

const I2 = ComplexF64[1 0; 0 1]
const X = ComplexF64[0 1; 1 0]
const Y = ComplexF64[0 -im; im 0]
const Z = ComplexF64[1 0; 0 -1]

kron3(a, b, c) = kron(kron(a, b), c)

matrix_finite(m::AbstractMatrix) = all(isfinite, real.(m)) && all(isfinite, imag.(m))
eye(n::Int) = Matrix{ComplexF64}(I, n, n)
commutator(a::AbstractMatrix, b::AbstractMatrix) = a * b - b * a

function check_f01(carrier::Carrier, probes::Vector{Probe})
    finite_dim = carrier.dim > 0
    nonempty_probe_family = !isempty(probes)
    finite_shapes = all(size(p.matrix) == (carrier.dim, carrier.dim) for p in probes)
    finite_entries = all(matrix_finite(p.matrix) for p in probes)
    return finite_dim && nonempty_probe_family && finite_shapes && finite_entries,
           finite_dim, nonempty_probe_family, finite_shapes, finite_entries
end

function check_n01(probes::Vector{Probe}; tol::Float64=TOL)
    best_norm = 0.0
    best_pair = ["none", "none"]
    for i in eachindex(probes)
        for j in (i + 1):length(probes)
            value = norm(commutator(probes[i].matrix, probes[j].matrix))
            if value > best_norm
                best_norm = value
                best_pair = [probes[i].name, probes[j].name]
            end
        end
    end
    return best_norm > tol, best_norm, best_pair
end

function scalar_multiple_error(a::AbstractMatrix, b::AbstractMatrix)
    denom = sum(abs2, b)
    denom <= TOL && return Inf, 0.0 + 0.0im
    alpha = sum(conj.(vec(b)) .* vec(a)) / denom
    scale = max(norm(a), TOL)
    return norm(a - alpha * b) / scale, alpha
end

function scalar_identity_error(a::AbstractMatrix)
    n = size(a, 1)
    ident = eye(n)
    err, alpha = scalar_multiple_error(a, ident)
    return err, alpha
end

function gamma_candidate_report(probe::Probe, dim::Int; tol::Float64=TOL)
    g = probe.matrix
    hermitian = norm(g - g') <= tol
    involution = norm(g * g - eye(dim)) <= tol
    plus_count = 0
    minus_count = 0
    spectrum_pm_only = false
    balanced = false

    if hermitian
        vals = eigvals(Hermitian((g + g') / 2))
        plus_count = count(abs(real(v) - 1.0) <= 1.0e-7 for v in vals)
        minus_count = count(abs(real(v) + 1.0) <= 1.0e-7 for v in vals)
        spectrum_pm_only = plus_count + minus_count == dim
        balanced = spectrum_pm_only && plus_count == minus_count && plus_count > 0
    end

    valid = hermitian && involution && balanced
    return jobj(
        "probe_name" => probe.name,
        "role" => probe.role,
        "hermitian" => hermitian,
        "involution" => involution,
        "plus_count" => plus_count,
        "minus_count" => minus_count,
        "spectrum_pm_only" => spectrum_pm_only,
        "balanced_spectrum" => balanced,
        "valid_z2_grading" => valid
    ), valid
end

function sector_delta_report(gamma_probe::Probe, obs_probe::Probe; tol::Float64=TOL)
    g = gamma_probe.matrix
    o = obs_probe.matrix
    n = size(g, 1)
    p_plus = (eye(n) + g) / 2
    p_minus = (eye(n) - g) / 2
    rank_plus = real(tr(p_plus))
    rank_minus = real(tr(p_minus))
    rho_plus = p_plus / rank_plus
    rho_minus = p_minus / rank_minus

    obs_hermitian = norm(o - o') <= tol
    gamma_err, gamma_alpha = scalar_multiple_error(o, g)
    ident_err, ident_alpha = scalar_identity_error(o)
    not_gamma_multiple = gamma_err > 1.0e-8
    not_identity_multiple = ident_err > 1.0e-8
    exp_plus = real(tr(rho_plus * o))
    exp_minus = real(tr(rho_minus * o))
    delta = abs(exp_plus - exp_minus)
    signs_opposed = exp_plus * exp_minus < 0
    distinguishes = obs_hermitian && not_gamma_multiple && not_identity_multiple && delta > tol

    return jobj(
        "observable" => obs_probe.name,
        "role" => obs_probe.role,
        "hermitian" => obs_hermitian,
        "not_scalar_multiple_of_gamma" => not_gamma_multiple,
        "gamma_multiple_relative_error" => gamma_err,
        "gamma_multiple_alpha_abs" => abs(gamma_alpha),
        "not_scalar_identity" => not_identity_multiple,
        "identity_multiple_relative_error" => ident_err,
        "identity_multiple_alpha_abs" => abs(ident_alpha),
        "sector_expectation_plus" => exp_plus,
        "sector_expectation_minus" => exp_minus,
        "sector_expectation_delta" => delta,
        "sector_expectations_opposed_sign" => signs_opposed,
        "distinguishes_z2_sectors" => distinguishes
    ), distinguishes, delta
end

observable_witness_role(probe::Probe) = probe.role == "observable" || probe.role == "hamiltonian"

function c3_test(carrier::Carrier, probes::Vector{Probe}; tol::Float64=TOL)
    gamma_reports = JObject[]
    valid_gamma_indices = Int[]
    for (idx, probe) in enumerate(probes)
        report, valid = gamma_candidate_report(probe, carrier.dim; tol=tol)
        push!(gamma_reports, report)
        valid && push!(valid_gamma_indices, idx)
    end

    best_witness = nothing
    best_delta = -1.0
    observable_reports = JObject[]

    for gamma_idx in valid_gamma_indices
        gamma_probe = probes[gamma_idx]
        for (obs_idx, obs_probe) in enumerate(probes)
            obs_idx == gamma_idx && continue
            observable_witness_role(obs_probe) || continue
            report, distinguishes, delta = sector_delta_report(gamma_probe, obs_probe; tol=tol)
            push!(observable_reports, report)
            if distinguishes && delta > best_delta
                best_delta = delta
                best_witness = jobj(
                    "gamma_probe" => gamma_probe.name,
                    "observable_probe" => obs_probe.name,
                    "sector_expectation_delta" => delta
                )
            end
        end
    end

    admitted = best_witness !== nothing
    reason = if admitted
        "valid_z2_grading_and_sector_distinguishing_probe_observed"
    elseif isempty(valid_gamma_indices)
        "no_valid_balanced_hermitian_involution_in_probe_family"
    else
        "valid_z2_grading_seen_but_no_nontrivial_sector_distinguishing_observable"
    end

    return jobj(
        "admitted_C3" => admitted,
        "verdict" => admitted ? "admitted_C3" : "excluded_C3",
        "reason" => reason,
        "valid_gamma_count" => length(valid_gamma_indices),
        "gamma_candidates" => gamma_reports,
        "observable_checks" => observable_reports,
        "witness" => best_witness
    ), admitted
end

function finite_map_result(carrier::Carrier, probes::Vector{Probe})
    f01, finite_dim, nonempty_probe_family, finite_shapes, finite_entries = check_f01(carrier, probes)
    n01, c_norm, witness_pair = check_n01(probes)
    c3, admitted_c3 = c3_test(carrier, probes)
    verdict = if !f01
        "excluded"
    elseif !n01
        "excluded"
    elseif admitted_c3
        "admitted"
    else
        "excluded"
    end
    return jobj(
        "carrier" => carrier.name,
        "dim" => carrier.dim,
        "description" => carrier.description,
        "finite_map" => "(carrier, probe_family) -> {admitted_C3, excluded_C3}",
        "codomain_value" => verdict,
        "f01" => f01,
        "n01" => n01,
        "c3" => c3,
        "commutator_norm" => c_norm,
        "commutator_witness_pair" => witness_pair,
        "f01_detail" => jobj(
            "finite_dim" => finite_dim,
            "nonempty_probe_family" => nonempty_probe_family,
            "finite_operator_shapes" => finite_shapes,
            "finite_numeric_entries" => finite_entries
        ),
        "probe_names" => [p.name for p in probes],
        "probe_roles" => [p.role for p in probes]
    ), f01, n01, admitted_c3, verdict
end

function density_matrix(n::Int, seed::Int)
    rng = MersenneTwister(seed)
    a = randn(rng, n, n) .+ im .* randn(rng, n, n)
    rho = a * a'
    rho ./= real(tr(rho))
    return Matrix{ComplexF64}(rho)
end

function density_f01_report(rho::Matrix{ComplexF64})
    n = size(rho, 1)
    hermitian_error = norm(rho - rho')
    trace_error = abs(real(tr(rho)) - 1.0)
    min_eval = minimum(eigvals(Hermitian((rho + rho') / 2)))
    finite_entries = matrix_finite(rho)
    f01 = size(rho) == (n, n) &&
          finite_entries &&
          hermitian_error <= 1.0e-8 &&
          trace_error <= 1.0e-8 &&
          min_eval >= -1.0e-8
    return jobj(
        "N" => n,
        "density_f01" => f01,
        "density_matrix_shape" => [size(rho, 1), size(rho, 2)],
        "finite_entries" => finite_entries,
        "hermitian_error" => hermitian_error,
        "trace_error" => trace_error,
        "min_eigenvalue" => min_eval,
        "positive_semidefinite" => min_eval >= -1.0e-8
    ), f01
end

function diag_matrix(values::Vector{Float64})
    return Matrix{ComplexF64}(Diagonal(ComplexF64.(values)))
end

function blockdiag2(a::Matrix{ComplexF64}, b::Matrix{ComplexF64})
    m = size(a, 1)
    n = size(b, 1)
    z_ab = zeros(ComplexF64, m, n)
    z_ba = zeros(ComplexF64, n, m)
    return [a z_ab; z_ba b]
end

function shift_hermitian(n::Int)
    m = zeros(ComplexF64, n, n)
    for i in 1:(n - 1)
        m[i, i + 1] = 1.0
        m[i + 1, i] = 1.0
    end
    return m
end

function z2_gamma(n::Int)
    @assert iseven(n)
    k = n ÷ 2
    return diag_matrix(vcat(fill(1.0, k), fill(-1.0, k)))
end

function sector_observable(n::Int)
    @assert iseven(n)
    k = n ÷ 2
    weights = [1.0 + i / (10.0 * k) for i in 1:k]
    return diag_matrix(vcat(weights, -weights))
end

function same_sector_observable(n::Int)
    @assert iseven(n)
    k = n ÷ 2
    weights = [1.0 + i / (10.0 * k) for i in 1:k]
    return diag_matrix(vcat(weights, weights))
end

function nonchiral_dim4()
    h = 0.7 * kron(X, I2) + 0.4 * kron(Z, X) + 0.3 * kron(Y, Z)
    p = kron(Z, I2) + 0.2 * kron(I2, Z)
    carrier = Carrier(
        "nonchiral_dim4",
        4,
        "two-qubit finite carrier with noncommuting probes and no admitted Z2 grading probe"
    )
    probes = Probe[
        Probe("H_nonchiral_dim4", Matrix{ComplexF64}(h), "hamiltonian"),
        Probe("two_qubit_dephasing_probe", Matrix{ComplexF64}(p), "observable")
    ]
    return carrier, probes
end

function nonchiral_dim8()
    h = 0.8 * kron3(X, I2, Z) +
        0.5 * kron3(Z, X, I2) +
        0.35 * kron3(Y, Z, X) +
        0.25 * kron3(X, X, X)
    p = kron3(Z, I2, I2) + 0.7 * kron3(I2, Z, I2) + 0.4 * kron3(I2, I2, Z)
    carrier = Carrier(
        "nonchiral_dim8",
        8,
        "three-qubit finite carrier with noncommuting probes and no admitted Z2 grading probe"
    )
    probes = Probe[
        Probe("H_nonchiral_dim8", Matrix{ComplexF64}(h), "hamiltonian"),
        Probe("three_qubit_diagonal_probe", Matrix{ComplexF64}(p), "observable")
    ]
    return carrier, probes
end

function chiral_control_dim4()
    h0 = diag_matrix([1.25, 0.75])
    h = blockdiag2(h0, -h0)
    gamma = z2_gamma(4)
    mixing = kron(I2, X) + 0.15 * kron(X, Z)
    carrier = Carrier(
        "chiral_control_dim4",
        4,
        "4-level control with gamma5 = diag(+1,+1,-1,-1) and opposite-sign sector observable"
    )
    probes = Probe[
        Probe("H_opposite_sign_sector_observable", h, "observable"),
        Probe("gamma5_z2_grading", gamma, "z2_grading"),
        Probe("independent_noncommuting_probe", Matrix{ComplexF64}(mixing), "observable")
    ]
    return carrier, probes
end

function erased_sector_control_dim4()
    h0 = diag_matrix([1.25, 0.75])
    h_erased = blockdiag2(h0, h0)
    gamma = z2_gamma(4)
    mixing = kron(I2, X) + 0.15 * kron(X, Z)
    carrier = Carrier(
        "chiral_control_sector_marker_erased_dim4",
        4,
        "structurally distinct 4-level control with balanced gamma5 retained but sector readout erased"
    )
    probes = Probe[
        Probe("H_same_sign_sector_observable", h_erased, "observable"),
        Probe("gamma5_z2_grading", gamma, "z2_grading"),
        Probe("independent_noncommuting_probe", Matrix{ComplexF64}(mixing), "observable")
    ]
    return carrier, probes
end

function erased_gamma_control_dim4()
    h0 = diag_matrix([1.25, 0.75])
    h_erased = blockdiag2(h0, h0)
    mixing = kron(I2, X) + 0.15 * kron(X, Z)
    carrier = Carrier(
        "chiral_control_gamma_erased_dim4",
        4,
        "structurally distinct 4-level control with no admitted Z2 grading probe"
    )
    probes = Probe[
        Probe("H_same_sign_sector_observable", h_erased, "observable"),
        Probe("independent_noncommuting_probe", Matrix{ComplexF64}(mixing), "observable")
    ]
    return carrier, probes
end

function density_ladder_case(n::Int, seed::Int)
    rho = density_matrix(n, seed)
    density_report, density_f01 = density_f01_report(rho)
    carrier = Carrier(
        "density_chiral_ladder_N$(n)",
        n,
        "finite density carrier with explicit balanced Z2 grading probe and sector-distinguishing observable"
    )
    probes = Probe[
        Probe("rho_trace_probe", rho, "density_carrier"),
        Probe("gamma_z2_grading_N$(n)", z2_gamma(n), "z2_grading"),
        Probe("sector_observable_N$(n)", sector_observable(n), "observable"),
        Probe("shift_noncommuting_probe_N$(n)", shift_hermitian(n), "observable")
    ]
    result, f01, n01, admitted_c3, verdict = finite_map_result(carrier, probes)

    erased_carrier = Carrier(
        "density_erased_ladder_N$(n)",
        n,
        "finite density carrier with balanced Z2 grading probe and sector readout erased"
    )
    erased_probes = Probe[
        Probe("rho_trace_probe", rho, "density_carrier"),
        Probe("gamma_z2_grading_N$(n)", z2_gamma(n), "z2_grading"),
        Probe("same_sector_observable_N$(n)", same_sector_observable(n), "observable"),
        Probe("shift_noncommuting_probe_N$(n)", shift_hermitian(n), "observable")
    ]
    erased_result, erased_f01, erased_n01, erased_admitted_c3, erased_verdict =
        finite_map_result(erased_carrier, erased_probes)

    return jobj(
        "density_check" => density_report,
        "c3_positive_density_carrier" => result,
        "c3_erased_density_control" => erased_result,
        "density_f01" => density_f01,
        "positive_f01_n01_c3" => f01 && n01 && admitted_c3 && verdict == "admitted",
        "erased_control_excluded" => erased_f01 && erased_n01 && !erased_admitted_c3 && erased_verdict == "excluded"
    ), density_f01 && f01 && n01 && admitted_c3 && erased_f01 && erased_n01 && !erased_admitted_c3
end

function structural_difference_report(chiral_probes::Vector{Probe}, erased_probes::Vector{Probe})
    chiral_h = chiral_probes[1].matrix
    erased_h = erased_probes[1].matrix
    err, alpha = scalar_multiple_error(erased_h, chiral_h)
    return jobj(
        "compared_probe" => "sector_observable",
        "not_scalar_multiple" => err > 1.0e-8,
        "relative_error_to_best_scalar_multiple" => err,
        "best_scalar_alpha_abs" => abs(alpha),
        "chiral_sector_trace" => real(tr(chiral_h)),
        "erased_sector_trace" => real(tr(erased_h))
    ), err > 1.0e-8
end

function main()
    n4, n4_probes = nonchiral_dim4()
    n8, n8_probes = nonchiral_dim8()
    chiral, chiral_probes = chiral_control_dim4()
    erased_sector, erased_sector_probes = erased_sector_control_dim4()
    erased_gamma, erased_gamma_probes = erased_gamma_control_dim4()

    n4_result, n4_f01, n4_n01, n4_c3, n4_verdict = finite_map_result(n4, n4_probes)
    n8_result, n8_f01, n8_n01, n8_c3, n8_verdict = finite_map_result(n8, n8_probes)
    chiral_result, chiral_f01, chiral_n01, chiral_c3, chiral_verdict =
        finite_map_result(chiral, chiral_probes)
    erased_sector_result, erased_sector_f01, erased_sector_n01, erased_sector_c3, erased_sector_verdict =
        finite_map_result(erased_sector, erased_sector_probes)
    erased_gamma_result, erased_gamma_f01, erased_gamma_n01, erased_gamma_c3, erased_gamma_verdict =
        finite_map_result(erased_gamma, erased_gamma_probes)

    structural_diff, not_scalar_multiple = structural_difference_report(chiral_probes, erased_sector_probes)

    ladder8, ladder8_pass = density_ladder_case(8, 9008)
    ladder16, ladder16_pass = density_ladder_case(16, 9016)
    ladder32, ladder32_pass = density_ladder_case(32, 9032)
    ladder64, ladder64_pass = density_ladder_case(64, 9064)

    negative_pass = n4_f01 && n4_n01 && !n4_c3 && n4_verdict == "excluded" &&
                    n8_f01 && n8_n01 && !n8_c3 && n8_verdict == "excluded"
    positive_pass = chiral_f01 && chiral_n01 && chiral_c3 && chiral_verdict == "admitted"
    wrong_structure_pass = erased_sector_f01 && erased_sector_n01 && !erased_sector_c3 &&
                           erased_sector_verdict == "excluded" &&
                           erased_gamma_f01 && erased_gamma_n01 && !erased_gamma_c3 &&
                           erased_gamma_verdict == "excluded" &&
                           not_scalar_multiple
    size_ladder_pass = all([ladder8_pass, ladder16_pass, ladder32_pass, ladder64_pass])
    load_bearing_flip = positive_pass && wrong_structure_pass
    all_pass = negative_pass && positive_pass && wrong_structure_pass && size_ladder_pass

    root = jobj(
        "object_id" => OBJECT_ID,
        "generated_at" => string(now(UTC)),
        "classification" => "diagnostic_only_candidate_c3",
        "source_path" => abspath(@__FILE__),
        "result_path" => RESULT_PATH,
        "source_sha256" => sha256_file(abspath(@__FILE__)),
        "julia_version" => string(VERSION),
        "promotion_allowed" => false,
        "claim_ceiling" => "Candidate C3 probe only. Does not assert layer-completion, manifold admission, coupling, bridge, flux, Axis0, or physics.",
        "candidate_c3_name" => "C3_Z2_sector_probe_distinguishability",
        "candidate_c3" => "C3_Z2_sector_probe_distinguishability: admitted_C3 iff the finite probe family contains a balanced Hermitian involution Gamma and a nontrivial Hermitian observable O, not Gamma or a scalar identity, with Tr(P_plus O)/rank(P_plus) != Tr(P_minus O)/rank(P_minus).",
        "candidate_c3_definition" => "C3_Z2_sector_probe_distinguishability: admitted_C3 iff the finite probe family contains a balanced Hermitian involution Gamma and a nontrivial Hermitian observable O, not Gamma or a scalar identity, with Tr(P_plus O)/rank(P_plus) != Tr(P_minus O)/rank(P_minus).",
        "nominalist_frame" => jobj(
            "identity" => "probe-relative: a~b iff all admissible probes agree",
            "root_axiom" => "a = a iff a ~ b",
            "chirality_status" => "chosen principle added as C3; F01+N01 alone still admits the nonchiral controls"
        ),
        "finite_map" => jobj(
            "rule" => "(carrier, probe_family) -> {admitted_C3, excluded_C3}",
            "input" => ["finite carrier", "finite probe family"],
            "output" => ["admitted_C3", "excluded_C3"],
            "admitted_condition" => "F01 and N01 survive, a valid balanced Gamma is present, and a nontrivial probe separates the normalized Gamma sectors",
            "excluded_condition" => "F01 or N01 fails, or the finite probe family has no valid balanced Gamma-sector distinguishing witness"
        ),
        "domain" => ["nonchiral_dim4", "nonchiral_dim8"],
        "codomain_or_output" => ["admitted_C3", "excluded_C3"],
        "root_constraints_in_force" => jobj(
            "F01" => "finite carrier and finite probe/operator family with finite entries",
            "N01" => "at least one nonzero commutator exists in the finite probe/operator family",
            "C3" => "balanced Z2 sector probe distinguishability"
        ),
        "carrier_realization" => "Julia-native finite ComplexF64 matrices and finite density matrices; no NumPy or dense-state closure claim beyond this diagnostic object.",
        "peps3d_embedding" => "blocked_not_part_of_this_candidate_probe",
        "spinor_state" => "finite gamma5-style Z2 sector object only; no full spinor-network carrier admission claimed",
        "quaternion_action" => "not_applicable",
        "dependency_receipts" => [
            "system_v5/julia_carrier/nonchiral_carrier_f01n01_negative_control_results.json",
            "system_v5/julia_carrier/branch_prune_dirac_gamma5_chirality_object_results.json"
        ],
        "downstream_blocks" => ["layer_completion", "manifold_admission", "coupling", "bridge", "flux", "Axis0", "physics"],
        "carrier_results" => jobj(
            "nonchiral_dim4" => n4_result,
            "nonchiral_dim8" => n8_result,
            "chiral_control_dim4" => chiral_result,
            "wrong_structure_sector_marker_erased_dim4" => erased_sector_result,
            "wrong_structure_gamma_erased_dim4" => erased_gamma_result
        ),
        "domain_checks" => jobj(
            "nonchiral_dim4" => jobj(
                "f01" => n4_f01,
                "n01" => n4_n01,
                "excluded_c3" => !n4_c3 && n4_verdict == "excluded"
            ),
            "nonchiral_dim8" => jobj(
                "f01" => n8_f01,
                "n01" => n8_n01,
                "excluded_c3" => !n8_c3 && n8_verdict == "excluded"
            )
        ),
        "positive_check" => jobj(
            "chiral_control_dim4_survives_f01_n01_c3" => positive_pass,
            "verdict" => chiral_verdict
        ),
        "negative_check" => jobj(
            "nonchiral_dim4_excluded_c3" => n4_f01 && n4_n01 && !n4_c3 && n4_verdict == "excluded",
            "nonchiral_dim8_excluded_c3" => n8_f01 && n8_n01 && !n8_c3 && n8_verdict == "excluded"
        ),
        "wrong_structure_control" => jobj(
            "structural_difference" => structural_diff,
            "distinguishing_element_removed" => true,
            "is_scalar_multiple_of_positive" => !not_scalar_multiple,
            "chiral_control_verdict" => chiral_verdict,
            "sector_marker_erased_verdict" => erased_sector_verdict,
            "gamma_erased_verdict" => erased_gamma_verdict,
            "verdict_changed" => chiral_verdict != erased_sector_verdict,
            "passes" => wrong_structure_pass
        ),
        "size_ladder" => jobj(
            "N8" => ladder8,
            "N16" => ladder16,
            "N32" => ladder32,
            "N64" => ladder64
        ),
        "checks" => jobj(
            "positive_chiral_control_survives_F01_N01_C3" => positive_pass,
            "negative_nonchiral_dim4_dim8_excluded_under_C3_while_F01_N01_survive" => negative_pass,
            "wrong_structure_erasure_changes_verdict" => wrong_structure_pass,
            "size_ladder_N8_N16_N32_N64_pass" => size_ladder_pass
        ),
        "load_bearing_flip" => load_bearing_flip,
        "load_bearing_flip_explanation" => "The chiral control is admitted with a valid Gamma and sector-distinguishing observable; the structurally distinct erased controls keep F01+N01 but are excluded_C3 after the distinguishing element is absent or sector-equal.",
        "decorative_if_no_flip" => !load_bearing_flip,
        "tool_manifest" => jobj(
            "julia_stdlib_LinearAlgebra" => "load-bearing for commutator norms, Hermitian/involution checks, eigenspace counts, sector projectors, traces, and density PSD checks",
            "julia_stdlib_Random" => "load-bearing fixed-seed density carrier ladder",
            "julia_stdlib_Dates" => "supportive timestamp only",
            "julia_stdlib_Printf" => "supportive JSON float and string formatting",
            "julia_stdlib_SHA" => "supportive source-hash receipt guard"
        ),
        "tool_integration_depth" => jobj(
            "LinearAlgebra" => "load_bearing",
            "Random" => "load_bearing",
            "Dates" => "supportive",
            "Printf" => "supportive",
            "SHA" => "supportive"
        ),
        "all_pass" => all_pass
    )

    write_json(RESULT_PATH, root)
    println("wrote ", RESULT_PATH)
    println("all_pass=", all_pass)
    exit(all_pass ? 0 : 1)
end

main()
