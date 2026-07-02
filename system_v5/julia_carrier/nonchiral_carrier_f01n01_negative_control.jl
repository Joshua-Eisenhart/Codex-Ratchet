using Dates
using LinearAlgebra
using Random
using Printf

const OBJECT_ID = "nonchiral_carrier_f01n01_v1"
const RESULT_PATH = "/tmp/cfc_chirality_results.json"
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
        if isempty(x.fields)
            return "{}"
        end
        parts = String[]
        for pair in x.fields
            push!(parts, nextpad * "\"" * json_escape(pair.first) * "\": " *
                         json_value(pair.second, indent + 2))
        end
        return "{\n" * join(parts, ",\n") * "\n" * pad * "}"
    elseif x isa AbstractDict
        fields = Pair{String, Any}[string(k) => v for (k, v) in x]
        return json_value(JObject(fields), indent)
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
        if isempty(x)
            return "[]"
        end
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

const I2 = ComplexF64[1 0; 0 1]
const X = ComplexF64[0 1; 1 0]
const Y = ComplexF64[0 -im; im 0]
const Z = ComplexF64[1 0; 0 -1]

kron3(a, b, c) = kron(kron(a, b), c)

struct Carrier
    name::String
    dim::Int
    hamiltonian::Matrix{ComplexF64}
    probe::Matrix{ComplexF64}
    probe_name::String
    gamma5::Union{Nothing, Matrix{ComplexF64}}
    left_right_split::Bool
    sign_structure::Bool
    chirality_labels::Union{Nothing, Vector{Int}}
    description::String
end

matrix_finite(m::AbstractMatrix) = all(isfinite, real.(m)) && all(isfinite, imag.(m))

function check_f01(dim::Int, ops::Vector{Matrix{ComplexF64}})
    finite_dim = dim > 0
    finite_ops = all(size(op) == (dim, dim) for op in ops)
    finite_entries = all(matrix_finite(op) for op in ops)
    return finite_dim && finite_ops && finite_entries, finite_dim, finite_ops, finite_entries
end

commutator(a::AbstractMatrix, b::AbstractMatrix) = a * b - b * a
commutator_norm(a::AbstractMatrix, b::AbstractMatrix) = norm(commutator(a, b))

function check_n01(ops::Vector{Matrix{ComplexF64}}, names::Vector{String}; tol::Float64=TOL)
    best_norm = 0.0
    best_pair = ["none", "none"]
    for i in eachindex(ops)
        for j in (i + 1):length(ops)
            value = commutator_norm(ops[i], ops[j])
            if value > best_norm
                best_norm = value
                best_pair = [names[i], names[j]]
            end
        end
    end
    return best_norm > tol, best_norm, best_pair
end

function random_hermitian(n::Int, seed::Int)
    rng = MersenneTwister(seed)
    a = randn(rng, n, n) .+ im .* randn(rng, n, n)
    return Matrix{ComplexF64}((a + a') / 2)
end

function chirality_report(carrier::Carrier; tol::Float64=TOL)
    gamma_present = carrier.gamma5 !== nothing
    gamma_hermitian = false
    gamma_involution = false
    gamma_plus_count = 0
    gamma_minus_count = 0
    gamma_mixed_pm = false
    if gamma_present
        gamma = carrier.gamma5
        gamma_hermitian = norm(gamma - gamma') <= tol
        gamma_involution = norm(gamma * gamma - Matrix{ComplexF64}(I, carrier.dim, carrier.dim)) <= tol
        if gamma_hermitian
            vals = eigvals(Hermitian((gamma + gamma') / 2))
            gamma_plus_count = count(abs(v - 1.0) <= 1.0e-7 for v in vals)
            gamma_minus_count = count(abs(v + 1.0) <= 1.0e-7 for v in vals)
            gamma_mixed_pm = gamma_plus_count > 0 &&
                             gamma_minus_count > 0 &&
                             gamma_plus_count + gamma_minus_count == carrier.dim
        end
    end

    label_count = carrier.chirality_labels === nothing ? 0 : length(unique(carrier.chirality_labels))
    labels_split = label_count > 1
    z2_grading = gamma_present && gamma_hermitian && gamma_involution && gamma_mixed_pm
    chiral = z2_grading || (labels_split && carrier.left_right_split) || carrier.sign_structure
    structurally_nonchiral = !chiral &&
                             !gamma_present &&
                             !carrier.left_right_split &&
                             !carrier.sign_structure &&
                             !labels_split

    basis = if z2_grading
        "valid_gamma5_z2_grading_operator_present"
    elseif carrier.sign_structure
        "left_right_sign_structure_present"
    elseif labels_split && carrier.left_right_split
        "left_right_label_split_present"
    elseif structurally_nonchiral
        "no_gamma5_no_z2_grading_no_left_right_split_no_sign_structure"
    else
        "no_valid_chirality_structure_detected"
    end

    return jobj(
        "chiral" => chiral,
        "basis" => basis,
        "gamma5_present" => gamma_present,
        "gamma5_hermitian" => gamma_hermitian,
        "gamma5_involution" => gamma_involution,
        "gamma5_plus_count" => gamma_plus_count,
        "gamma5_minus_count" => gamma_minus_count,
        "z2_grading" => z2_grading,
        "left_right_split" => carrier.left_right_split,
        "sign_structure" => carrier.sign_structure,
        "chirality_label_classes" => label_count,
        "labels_split" => labels_split,
        "structurally_nonchiral" => structurally_nonchiral
    ), chiral, structurally_nonchiral
end

function operator_list(carrier::Carrier)
    ops = Matrix{ComplexF64}[carrier.hamiltonian, carrier.probe]
    names = ["H", carrier.probe_name]
    if carrier.gamma5 !== nothing
        push!(ops, carrier.gamma5)
        push!(names, "gamma5")
    end
    return ops, names
end

function carrier_result(carrier::Carrier, control_verdict::String)
    ops, names = operator_list(carrier)
    f01, finite_dim, finite_ops, finite_entries = check_f01(carrier.dim, ops)
    n01, c_norm, witness_pair = check_n01(ops, names)
    chirality, chiral, structurally_nonchiral = chirality_report(carrier)
    verdict = if f01 && n01 && !chiral
        "admitted nonchiral"
    elseif f01 && n01 && chiral
        control_verdict
    elseif !f01
        "excluded by F01"
    elseif !n01
        "excluded by N01"
    else
        "open"
    end

    return jobj(
        "dim" => carrier.dim,
        "f01" => f01,
        "n01" => n01,
        "chiral" => chiral,
        "commutator_norm" => c_norm,
        "commutator_witness_pair" => witness_pair,
        "verdict" => verdict,
        "description" => carrier.description,
        "f01_detail" => jobj(
            "finite_dim" => finite_dim,
            "finite_operator_shapes" => finite_ops,
            "finite_numeric_entries" => finite_entries
        ),
        "chirality_structural_check" => chirality,
        "structurally_nonchiral" => structurally_nonchiral
    ), f01, n01, chiral, c_norm
end

function density_matrix_check(n::Int, seed::Int)
    rng = MersenneTwister(seed)
    a = randn(rng, n, n) .+ im .* randn(rng, n, n)
    rho = a * a'
    rho ./= real(tr(rho))
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
        "f01" => f01,
        "density_matrix_shape" => [size(rho, 1), size(rho, 2)],
        "finite_entries" => finite_entries,
        "hermitian_error" => hermitian_error,
        "trace_error" => trace_error,
        "min_eigenvalue" => min_eval,
        "positive_semidefinite" => min_eval >= -1.0e-8,
        "verdict" => f01 ? "finite density carrier confirmed" : "F01 density check failed"
    ), f01
end

function build_carriers()
    qubit_h = ComplexF64[0 1; 1 0] + im * ComplexF64[0 -1; 1 0]
    qubit = Carrier(
        "qubit_dim2",
        2,
        qubit_h,
        Z,
        "Z_dephasing_probe",
        nothing,
        false,
        false,
        nothing,
        "single qubit with H = X + i*real_antisymmetric = X + Y and Z dephasing probe; no gamma5 field"
    )

    qutrit_h = random_hermitian(3, 314159)
    qutrit_dephase = ComplexF64[1 0 0; 0 0 0; 0 0 -1]
    qutrit = Carrier(
        "qutrit_dim3",
        3,
        qutrit_h,
        qutrit_dephase,
        "qutrit_dephasing_lindblad",
        nothing,
        false,
        false,
        nothing,
        "fixed-seed random Hermitian qutrit Hamiltonian with diagonal dephasing Lindblad; no Z2 grading"
    )

    four_h = 0.7 * kron(X, I2) + 0.4 * kron(Z, X) + 0.3 * kron(Y, Z)
    four_probe = kron(Z, I2) + 0.2 * kron(I2, Z)
    four = Carrier(
        "fourbody_dim4",
        4,
        Matrix{ComplexF64}(four_h),
        Matrix{ComplexF64}(four_probe),
        "two_qubit_dephasing_probe",
        nothing,
        false,
        false,
        fill(1, 4),
        "two-qubit carrier with generic Hermitian interactions; all optional chirality labels same and no split operator"
    )

    eight_h = 0.8 * kron3(X, I2, Z) +
              0.5 * kron3(Z, X, I2) +
              0.35 * kron3(Y, Z, X) +
              0.25 * kron3(X, X, X)
    eight_probe = kron3(Z, I2, I2) + 0.7 * kron3(I2, Z, I2) + 0.4 * kron3(I2, I2, Z)
    eight = Carrier(
        "eightbody_dim8",
        8,
        Matrix{ComplexF64}(eight_h),
        Matrix{ComplexF64}(eight_probe),
        "three_qubit_diagonal_probe",
        nothing,
        false,
        false,
        nothing,
        "three-qubit finite carrier with generic noncommuting interaction algebra and no orientation or handedness structure"
    )

    gamma5_dim4 = Diagonal(ComplexF64[1, 1, -1, -1]) |> Matrix{ComplexF64}
    chiral_h = kron(X, I2)
    chiral_probe = 2.0 * kron(Z, X) + 0.25 * kron(I2, Z)
    chiral = Carrier(
        "chiral_control_dim4",
        4,
        Matrix{ComplexF64}(chiral_h),
        Matrix{ComplexF64}(chiral_probe),
        "independent_noncommuting_probe",
        gamma5_dim4,
        true,
        true,
        [1, 1, -1, -1],
        "4-level control with explicit gamma5 = diag(+1,+1,-1,-1), left/right split, sign structure, and an independent N01 witness probe"
    )

    return qubit, qutrit, four, eight, chiral, gamma5_dim4
end

function dim1_boundary()
    a = ComplexF64[2 + 3im;;]
    b = ComplexF64[-5 + 0.25im;;]
    f01, finite_dim, finite_ops, finite_entries = check_f01(1, Matrix{ComplexF64}[a, b])
    n01, c_norm, witness_pair = check_n01(Matrix{ComplexF64}[a, b], ["scalar_A", "scalar_B"])
    return jobj(
        "dim" => 1,
        "f01" => f01,
        "n01" => n01,
        "commutator_norm" => c_norm,
        "commutator_witness_pair" => witness_pair,
        "f01_detail" => jobj(
            "finite_dim" => finite_dim,
            "finite_operator_shapes" => finite_ops,
            "finite_numeric_entries" => finite_entries
        ),
        "reason" => "1x1 operators reduce to scalar multiplication, so the computed commutator is zero for the sampled pair and N01 has no witness in dim=1",
        "verdict" => "dim=1 excluded by N01"
    )
end

function wrong_structure_control(base::Carrier, gamma5_dim4::Matrix{ComplexF64})
    _, base_chiral, _ = chirality_report(base)
    altered = Carrier(
        "fourbody_dim4_with_added_gamma5",
        base.dim,
        base.hamiltonian,
        base.probe,
        base.probe_name,
        gamma5_dim4,
        base.left_right_split,
        base.sign_structure,
        [1, 1, -1, -1],
        "same two-qubit carrier, but with a valid gamma5 Z2 grading injected as wrong-structure control"
    )
    altered_report, altered_chiral, _ = chirality_report(altered)
    ops, names = operator_list(altered)
    n01, c_norm, witness_pair = check_n01(ops, names)
    f01, _, _, _ = check_f01(altered.dim, ops)
    return jobj(
        "base_carrier" => base.name,
        "base_chiral" => base_chiral,
        "after_adding_gamma5_chiral" => altered_chiral,
        "classification_changed" => base_chiral != altered_chiral,
        "added_gamma5_f01" => f01,
        "added_gamma5_n01" => n01,
        "added_gamma5_commutator_norm" => c_norm,
        "added_gamma5_commutator_witness_pair" => witness_pair,
        "added_gamma5_structural_check" => altered_report,
        "verdict" => (base_chiral != altered_chiral ?
                      "adding a valid gamma5 changes structural chirality classification" :
                      "wrong-structure control failed to change classification")
    )
end

function main()
    qubit, qutrit, four, eight, chiral, gamma5_dim4 = build_carriers()

    qubit_res, qubit_f01, qubit_n01, qubit_chiral, _ = carrier_result(qubit, "admitted chiral (control)")
    qutrit_res, qutrit_f01, qutrit_n01, qutrit_chiral, _ = carrier_result(qutrit, "admitted chiral (control)")
    four_res, four_f01, four_n01, four_chiral, _ = carrier_result(four, "admitted chiral (control)")
    eight_res, eight_f01, eight_n01, eight_chiral, _ = carrier_result(eight, "admitted chiral (control)")
    chiral_res, chiral_f01, chiral_n01, chiral_chiral, _ = carrier_result(chiral, "admitted chiral (control)")

    size8, size8_f01 = density_matrix_check(8, 8008)
    size16, size16_f01 = density_matrix_check(16, 8016)
    size32, size32_f01 = density_matrix_check(32, 8032)
    size64, size64_f01 = density_matrix_check(64, 8064)

    nonchiral_pass = all([
        qubit_f01 && qubit_n01 && !qubit_chiral,
        qutrit_f01 && qutrit_n01 && !qutrit_chiral,
        four_f01 && four_n01 && !four_chiral,
        eight_f01 && eight_n01 && !eight_chiral
    ])
    chiral_control_pass = chiral_f01 && chiral_n01 && chiral_chiral
    forced_or_chosen = if nonchiral_pass && chiral_control_pass
        "chosen_principle"
    elseif !nonchiral_pass && chiral_control_pass
        "forced_by_F01_N01"
    else
        "open"
    end

    caveat = if forced_or_chosen == "chosen_principle"
        "This finite negative control only checks F01 finite dimension and N01 existence of a noncommuting operator pair. It shows chirality is not forced by those constraints alone; it does not admit geometry, Weyl physics, PEPS3D manifold structure, coupling, bridge, flux, or physics."
    elseif forced_or_chosen == "forced_by_F01_N01"
        "Nonchiral carriers failed under the implemented checks while the chiral control passed; this would need independent proof before any stronger claim."
    else
        "The implemented finite checks did not cleanly separate forced versus chosen; inspect carrier-level failures before drawing a conclusion."
    end

    conclusion = if forced_or_chosen == "chosen_principle"
        "Non-chiral carriers satisfy F01+N01. Chiral carriers also satisfy F01+N01. Chirality is admitted but not forced."
    elseif forced_or_chosen == "forced_by_F01_N01"
        "The checked non-chiral carriers did not satisfy F01+N01 while the chiral control did. This would make chirality look forced in this finite test, pending proof."
    else
        "The finite carrier checks are inconclusive; chirality remains open under this test."
    end

    root = jobj(
        "object_id" => OBJECT_ID,
        "claim_ceiling" => "Finite-carrier negative control only: no layer-completion, manifold admission, coupling, bridge, flux, Axis0, gravity, or physics claims.",
        "promotion_allowed" => false,
        "classification" => "diagnostic_only_negative_control",
        "generated_at" => string(now(UTC)),
        "root_constraints" => jobj(
            "F01" => "finite-dimensional Hilbert carrier and finite operator/probe set with finite numeric entries",
            "N01" => "there exists at least one numerically nonzero commutator among the carrier operators"
        ),
        "forced_or_chosen" => forced_or_chosen,
        "honest_caveat" => caveat,
        "carriers" => jobj(
            "qubit_dim2" => qubit_res,
            "qutrit_dim3" => qutrit_res,
            "fourbody_dim4" => four_res,
            "eightbody_dim8" => eight_res,
            "chiral_control_dim4" => chiral_res
        ),
        "size_ladder" => jobj(
            "N8" => size8,
            "N16" => size16,
            "N32" => size32,
            "N64" => size64
        ),
        "boundary_checks" => jobj(
            "dim1_excluded" => dim1_boundary()
        ),
        "structural_controls" => jobj(
            "wrong_structure_added_gamma5" => wrong_structure_control(four, gamma5_dim4)
        ),
        "positive_check" => jobj(
            "all_nonchiral_carriers_f01_n01_pass" => nonchiral_pass,
            "chiral_control_f01_n01_pass" => chiral_control_pass,
            "density_size_ladder_f01_pass" => all([size8_f01, size16_f01, size32_f01, size64_f01])
        ),
        "tool_manifest" => jobj(
            "julia_stdlib_LinearAlgebra" => "load-bearing for numerical commutator norms, Hermitian checks, eigenvalue checks, and density matrix checks",
            "julia_stdlib_Random" => "load-bearing fixed-seed qutrit Hamiltonian and density matrix ladder",
            "julia_stdlib_Dates" => "supportive timestamp only",
            "julia_stdlib_Printf" => "supportive JSON float/escape formatting only"
        ),
        "tool_integration_depth" => jobj(
            "LinearAlgebra" => "load_bearing",
            "Random" => "load_bearing",
            "Dates" => "supportive",
            "Printf" => "supportive"
        ),
        "conclusion" => conclusion
    )

    write_json(RESULT_PATH, root)
    println("wrote ", RESULT_PATH)
    println(conclusion)
end

main()
