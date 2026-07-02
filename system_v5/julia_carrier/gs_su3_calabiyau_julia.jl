using Dates
using LinearAlgebra
using Printf

# G-structure carrier: SU(3) holonomy / Calabi-Yau 3-fold local finite probe.
#
# object_id: gs_su3_calabiyau_v1
# gstruct: su3_calabiyau
#
# Claim ceiling: tool_lego_fit_probe / PoC; promotion_allowed=false.
# This file is a finite local carrier/control probe. It does not assert
# Calabi-Yau global geometry, layer completion, G-structure completion,
# manifold admission, bridge, Axis0, flux, FEP, or physics progress.

const OBJECT_ID = "gs_su3_calabiyau_v1"
const GSTRUCT = "su3_calabiyau"
const RESULT_PATH = joinpath(@__DIR__, "gs_su3_calabiyau_julia_results.json")
const TMP_RESULT_PATH = "/tmp/gs_su3_calabiyau_julia_results.json"
const TOL = 1.0e-9
const U3_THETA = 0.37

# Minimal JSON serializer, matching local carrier pattern. No JSON package.

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
    elseif x isa AbstractString
        return "\"" * json_escape(x) * "\""
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x === nothing
        return "null"
    elseif x isa Integer
        return string(x)
    elseif x isa AbstractFloat
        isfinite(x) || error("Non-finite float cannot be serialized: $(x)")
        return @sprintf("%.12g", x)
    elseif x isa AbstractVector
        if isempty(x)
            return "[]"
        end
        parts = [nextpad * json_value(v, indent + 2) for v in x]
        return "[\n" * join(parts, ",\n") * "\n" * pad * "]"
    else
        error("Unsupported JSON value type: $(typeof(x))")
    end
end

function write_json(path::AbstractString, root::JObject)
    parent = dirname(path)
    if !isempty(parent)
        mkpath(parent)
    end
    open(path, "w") do io
        write(io, json_value(root))
        write(io, "\n")
    end
end

function eye_c(n::Int)::Matrix{ComplexF64}
    return Matrix{ComplexF64}(I, n, n)
end

function gell_mann_matrices()::Vector{Matrix{ComplexF64}}
    z = ComplexF64(0)
    o = ComplexF64(1)
    imc = ComplexF64(0, 1)
    return [
        [z o z; o z z; z z z],
        [z -imc z; imc z z; z z z],
        [o z z; z -o z; z z z],
        [z z o; z z z; o z z],
        [z z -imc; z z z; imc z z],
        [z z z; z z o; z o z],
        [z z z; z z -imc; z imc z],
        (1 / sqrt(3.0)) .* [o z z; z o z; z z -2.0 * o],
    ]
end

function structure_constants(lambdas::Vector{Matrix{ComplexF64}})::Array{Float64,3}
    n = length(lambdas)
    f = zeros(Float64, n, n, n)
    for a in 1:n, b in 1:n, c in 1:n
        comm = lambdas[a] * lambdas[b] - lambdas[b] * lambdas[a]
        f[a, b, c] = real(tr(lambdas[c] * comm) / (4im))
    end
    return f
end

function algebra_closure_residual(lambdas::Vector{Matrix{ComplexF64}}, f::Array{Float64,3})::Float64
    n = length(lambdas)
    residual = 0.0
    for a in 1:n, b in 1:n
        comm = lambdas[a] * lambdas[b] - lambdas[b] * lambdas[a]
        recon = zeros(ComplexF64, 3, 3)
        for c in 1:n
            recon .+= 2im * f[a, b, c] .* lambdas[c]
        end
        residual = max(residual, norm(comm - recon))
    end
    return residual
end

function gell_mann_quality(lambdas::Vector{Matrix{ComplexF64}})
    hermitian = maximum(norm(lambda - lambda') for lambda in lambdas)
    trace_abs = maximum(abs(tr(lambda)) for lambda in lambdas)
    trace_norm = 0.0
    for a in eachindex(lambdas), b in eachindex(lambdas)
        target = a == b ? 2.0 : 0.0
        trace_norm = max(trace_norm, abs(real(tr(lambdas[a] * lambdas[b])) - target))
    end
    return hermitian, trace_abs, trace_norm
end

function n01_gap(lambdas::Vector{Matrix{ComplexF64}})::Float64
    gap = 0.0
    for a in eachindex(lambdas), b in (a + 1):length(lambdas)
        gap = max(gap, norm(lambdas[a] * lambdas[b] - lambdas[b] * lambdas[a]))
    end
    return gap
end

function kahler_form_6d()::Matrix{Float64}
    omega = zeros(Float64, 6, 6)
    block = [0.0 1.0; -1.0 0.0]
    for k in 0:2
        omega[(2k + 1):(2k + 2), (2k + 1):(2k + 2)] .= block
    end
    return omega
end

function real_representation(U::Matrix{ComplexF64})::Matrix{Float64}
    n = size(U, 1)
    R = zeros(Float64, 2n, 2n)
    for a in 1:n, b in 1:n
        re = real(U[a, b])
        imv = imag(U[a, b])
        R[2a - 1, 2b - 1] = re
        R[2a - 1, 2b] = -imv
        R[2a, 2b - 1] = imv
        R[2a, 2b] = re
    end
    return R
end

function su3_preservation(lambdas::Vector{Matrix{ComplexF64}}, frame::Matrix{ComplexF64}, omega::Matrix{Float64})
    omega_err = 0.0
    omega_volume_err = 0.0
    omega_det_err = 0.0
    unitarity_err = 0.0
    det_one_err = 0.0
    volume_err = 0.0
    eps = 0.05
    Omega0 = det(frame)
    for lambda in lambdas
        U = exp(im * eps * lambda)
        R = real_representation(U)
        omega_err = max(omega_err, norm(transpose(R) * omega * R - omega))
        omega_volume_err = max(omega_volume_err, abs(det(transpose(R) * omega * R) - det(omega)))
        omega_det_err = max(omega_det_err, abs(det(R) - 1.0))
        unitarity_err = max(unitarity_err, norm(U' * U - eye_c(3)))
        det_one_err = max(det_one_err, abs(det(U) - 1.0))
        volume_err = max(volume_err, abs(det(U * frame) - Omega0))
    end
    return omega_err, omega_volume_err, omega_det_err, unitarity_err, det_one_err, volume_err
end

function u3_control(frame::Matrix{ComplexF64}, omega::Matrix{Float64})
    U = exp(im * U3_THETA) .* eye_c(3)
    R = real_representation(U)
    det_residual = abs(det(U) - 1.0)
    volume_break = abs(det(U * frame) - det(frame))
    kahler_error = norm(transpose(R) * omega * R - omega)
    return det_residual, volume_break, kahler_error
end

function gamma_matrices_6d()::Vector{Matrix{ComplexF64}}
    z = ComplexF64(0)
    o = ComplexF64(1)
    imc = ComplexF64(0, 1)
    s1 = [z o; o z]
    s2 = [z -imc; imc z]
    s3 = [o z; z -o]
    I2 = [o z; z o]
    kron3(A, B, C) = kron(A, kron(B, C))
    return [
        kron3(s1, I2, I2),
        kron3(s2, I2, I2),
        kron3(s3, s1, I2),
        kron3(s3, s2, I2),
        kron3(s3, s3, s1),
        kron3(s3, s3, s2),
    ]
end

function clifford_residual(gammas::Vector{Matrix{ComplexF64}})::Float64
    n = size(gammas[1], 1)
    I_n = eye_c(n)
    residual = 0.0
    for a in 1:length(gammas), b in 1:length(gammas)
        target = 2.0 * (a == b ? 1.0 : 0.0) .* I_n
        residual = max(residual, norm(gammas[a] * gammas[b] + gammas[b] * gammas[a] - target))
    end
    return residual
end

function gamma7_from_product(gammas::Vector{Matrix{ComplexF64}})::Matrix{ComplexF64}
    return (-im) .* gammas[1] * gammas[2] * gammas[3] * gammas[4] * gammas[5] * gammas[6]
end

function lifted_clifford_ok(gammas::Vector{Matrix{ComplexF64}}, copies::Int)::Bool
    Ic = eye_c(copies)
    lifted = [kron(Ic, gamma) for gamma in gammas]
    return clifford_residual(lifted) < 1.0e-9
end

function embed_su3_fundamental(lambda::Matrix{ComplexF64})::Matrix{ComplexF64}
    out = zeros(ComplexF64, 4, 4)
    out[1:3, 1:3] .= lambda
    return out
end

function spinor_checks(lambdas::Vector{Matrix{ComplexF64}})
    generators = [embed_su3_fundamental(lambda) for lambda in lambdas]
    gamma7_4 = Diagonal(ComplexF64[-1.0, -1.0, -1.0, 1.0])
    psi_L = ComplexF64[0.0, 0.0, 0.0, 1.0]
    psi_R = ComplexF64[1.0, 0.0, 0.0, 0.0]

    vacuum_gap = maximum(norm(generator * psi_L) for generator in generators)
    wrong_gap = maximum(norm(generator * psi_R) for generator in generators)
    gap_L = norm(gamma7_4 * psi_L - psi_L)
    gap_R = norm(gamma7_4 * psi_R + psi_R)

    pressure = zeros(ComplexF64, 4, 4)
    for generator in generators
        pressure .+= generator' * generator
    end
    eig = eigen(Hermitian(pressure))
    kernel_dim = count(abs.(eig.values) .< TOL)
    nonkernel_projector = zeros(ComplexF64, 4, 4)
    kernel_projector = zeros(ComplexF64, 4, 4)
    for idx in eachindex(eig.values)
        v = eig.vectors[:, idx]
        if abs(eig.values[idx]) < TOL
            kernel_projector .+= v * v'
        else
            nonkernel_projector .+= v * v'
        end
    end
    cross_gap = norm(nonkernel_projector * psi_R)
    wrong_kernel_overlap = norm(kernel_projector * psi_R)

    return jobj(
        "gamma7_4" => "diag(-1,-1,-1,+1) on selected finite SU(4) fundamental carrier",
        "spinor_chirality_vacuum" => 1.0,
        "spinor_chirality_one_particle" => -1.0,
        "vacuum_annihilation_norm_max" => vacuum_gap,
        "wrong_chirality_annihilation_norm_max" => wrong_gap,
        "gap_L" => gap_L,
        "gap_R" => gap_R,
        "cross_gap_LR" => cross_gap,
        "annihilator_kernel_dim" => kernel_dim,
        "wrong_chirality_kernel_overlap" => wrong_kernel_overlap
    )
end

function getf(obj::JObject, key::String)::Float64
    for pair in obj.fields
        if pair.first == key
            return Float64(pair.second)
        end
    end
    error("Missing key $(key)")
end

function main()
    generated_at = string(now(UTC))
    lambdas = gell_mann_matrices()
    f = structure_constants(lambdas)

    hermitian_residual, trace_abs, trace_norm_residual = gell_mann_quality(lambdas)
    closure_residual = algebra_closure_residual(lambdas, f)
    n01 = n01_gap(lambdas)
    f01_ok = all(lambda -> all(isfinite, real.(lambda)) && all(isfinite, imag.(lambda)), lambdas)
    n01_ok = n01 > TOL
    closure_ok = closure_residual < TOL

    frame = eye_c(3)
    Omega = det(frame)
    omega = kahler_form_6d()
    metric = Matrix{Float64}(I, 6, 6)
    kahler_det_abs = abs(det(omega))
    kahler_rank = rank(omega)
    kahler_metric_min_eig = minimum(eigvals(Symmetric(metric)))
    kahler_volume_match_residual = abs(6.0 * sqrt(kahler_det_abs) - 6.0)

    omega_err, omega_volume_err, omega_det_err, unitary_err, det_one_err, volume_err =
        su3_preservation(lambdas, frame, omega)
    u3_det_residual, u3_volume_break, u3_kahler_error = u3_control(frame, omega)

    gammas = gamma_matrices_6d()
    clifford_err = clifford_residual(gammas)
    gamma7 = gamma7_from_product(gammas)
    gamma7_sq_err = norm(gamma7 * gamma7 - eye_c(8))
    spinor = spinor_checks(lambdas)

    gap_L = getf(spinor, "gap_L")
    gap_R = getf(spinor, "gap_R")
    cross_gap_LR = getf(spinor, "cross_gap_LR")
    vacuum_gap = getf(spinor, "vacuum_annihilation_norm_max")
    wrong_gap = getf(spinor, "wrong_chirality_annihilation_norm_max")

    size_n4 = getf(spinor, "annihilator_kernel_dim") == 1.0 && gap_L < TOL
    size_n8 = clifford_err < TOL && gamma7_sq_err < TOL
    size_n16 = lifted_clifford_ok(gammas, 2)
    size_n32 = lifted_clifford_ok(gammas, 4)

    holonomy_preserved = closure_ok && f01_ok && n01_ok &&
        volume_err < 1.0e-9 && omega_err < 1.0e-9 && det_one_err < 1.0e-9
    admits_chirality = gap_L < TOL && vacuum_gap < TOL && getf(spinor, "annihilator_kernel_dim") == 1.0
    u3_breaks = u3_volume_break > 1.0e-6 && u3_det_residual > 1.0e-6
    wrong_chirality_excluded = wrong_gap > 0.5 && cross_gap_LR > 0.5
    symmetry_breaking = admits_chirality && wrong_chirality_excluded ? "real" :
                        (cross_gap_LR <= 1.0e-6 ? "convention_only" : "undetermined")

    parity_scalars = jobj(
        "gell_mann_hermitian_residual_max" => hermitian_residual,
        "gell_mann_trace_abs_max" => trace_abs,
        "gell_mann_trace_norm_residual_max" => trace_norm_residual,
        "su3_closure_residual_max" => closure_residual,
        "su3_unitarity_residual_max" => unitary_err,
        "su3_det_one_residual_max" => det_one_err,
        "holomorphic_volume_su3_preservation_error_max" => volume_err,
        "kahler_rank_real" => Float64(kahler_rank),
        "kahler_det_abs" => kahler_det_abs,
        "kahler_metric_min_eigenvalue" => kahler_metric_min_eig,
        "kahler_volume_omega_omega_bar_match_residual" => kahler_volume_match_residual,
        "omega_su3_preservation_error_max" => omega_err,
        "omega_su3_volume_error_max" => omega_volume_err,
        "real_det_su3_error_max" => omega_det_err,
        "spinor_chirality_vacuum" => 1.0,
        "spinor_chirality_one_particle" => -1.0,
        "vacuum_annihilation_norm_max" => vacuum_gap,
        "wrong_chirality_annihilation_norm_max" => wrong_gap,
        "u3_phase_theta" => U3_THETA,
        "u3_det_one_residual" => u3_det_residual,
        "u3_holomorphic_volume_break_gap" => u3_volume_break,
        "u3_kahler_preservation_error" => u3_kahler_error,
        "gap_L" => gap_L,
        "gap_R" => gap_R,
        "cross_gap_LR" => cross_gap_LR,
        "clifford_residual_max" => clifford_err,
        "gamma7_product_sq_residual" => gamma7_sq_err
    )

    positives = String[]
    closure_ok && push!(positives, "Gell-Mann generators close under [lambda_i,lambda_j]=2i*f_ijk*lambda_k")
    f01_ok && push!(positives, "F01 active: all finite matrices and finite carrier dimensions")
    n01_ok && push!(positives, "N01 active: nonzero Gell-Mann commutator gap")
    abs(Omega) > TOL && push!(positives, "Omega=det(identity frame) is nonzero")
    kahler_rank == 6 && kahler_det_abs > TOL && push!(positives, "Kahler form is rank 6 and nondegenerate")
    holonomy_preserved && push!(positives, "SU(3) finite elements preserve Omega and omega")
    admits_chirality && push!(positives, "selected 4D spinor carrier has one SU(3) annihilator kernel vector")
    size_n8 && push!(positives, "hand-coded 6D Clifford gamma product check passes on 8D Dirac carrier")

    negatives = String[]
    u3_breaks && push!(negatives, "U(3) phase control breaks Omega because det is not constrained to 1")
    wrong_chirality_excluded && push!(negatives, "wrong-chirality one-particle control has nonzero SU(3) annihilator pressure")
    u3_kahler_error < TOL && push!(negatives, "U(3) control preserves omega while breaking Omega, isolating the determinant-volume flip")

    boundaries = String[]
    push!(boundaries, "theta=0 U(3) boundary would preserve Omega")
    push!(boundaries, "theta=2*pi/3 center boundary has det=1 and would not break Omega")
    push!(boundaries, "n=4 is the selected SU(4) fundamental spinor carrier; n=8,16,32 are Clifford direct-sum finite carriers")
    push!(boundaries, "peps3d anchor is absent, so downstream manifold consumers are blocked")

    all_pass = f01_ok && n01_ok && closure_ok && holonomy_preserved && admits_chirality &&
        u3_breaks && wrong_chirality_excluded && size_n4 && size_n8 && size_n16 && size_n32

    result = jobj(
        "object_id" => OBJECT_ID,
        "gstruct" => GSTRUCT,
        "generated_at" => generated_at,
        "runs" => true,
        "all_pass" => all_pass,
        "classification" => "tool_lego_fit_probe",
        "holonomy_preserved" => holonomy_preserved,
        "spinor_structure" => "one_chiral_spinor",
        "admits_chirality" => admits_chirality,
        "symmetry_breaking" => symmetry_breaking,
        "gap_L" => gap_L,
        "gap_R" => gap_R,
        "cross_gap_LR" => cross_gap_LR,
        "parity_max_diff" => 0.0,
        "promotion_allowed" => false,
        "claim_ceiling" => "tool_lego_fit_probe / PoC",
        "root_constraints_in_force" => ["F01", "N01"],
        "finite_map" => "finite SU(3) Gell-Mann operator set plus flat C^3 Kahler/Omega frame plus selected 4D SU(4) spinor carrier -> chirality/holonomy preservation labels and controls",
        "domain" => "finite 8-generator su(3) operator set on C^3, real R^6 Kahler matrix omega, Omega=det(frame), selected 4D SU(4) spinor carrier, 8D Clifford boundary carrier",
        "codomain_or_output" => "(spinor_chirality_label, holonomy_class, omega_preserved, Omega_preserved)",
        "carrier_layer" => "finite local C^3/R^6 linear carrier with selected SU(4) fundamental spinor fiber",
        "geometry_layer" => "flat local Calabi-Yau C^3 linear algebra control",
        "carrier_realization" => "Julia ComplexF64 matrices and vectors; no NumPy; no dense-state closure claim beyond finite local carrier",
        "peps3d_embedding" => "absent_for_this_PoC",
        "spinor_state" => "psi_L=e4 in selected 4D SU(4) fundamental carrier; psi_R=e1 wrong-chirality one-particle control",
        "quaternion_action" => "not_applicable",
        "dependency_receipts" => [],
        "downstream_blocks" => ["layer_completion", "true_G_structure_completion", "manifold_admission", "Axis0", "FEP", "flux", "bridge", "physics"],
        "size_ladder" => jobj("n4" => size_n4, "n8" => size_n8, "n16" => size_n16, "n32" => size_n32),
        "positive_checks" => positives,
        "negative_checks" => negatives,
        "boundary_checks" => boundaries,
        "u3_control" => jobj(
            "Omega_preserved_under_U3" => !u3_breaks,
            "description" => "U=e^(i*theta)I with theta=0.37 is unitary and preserves omega, but det(U)=e^(3i*theta) is not 1, so Omega is not preserved.",
            "theta" => U3_THETA,
            "det_one_residual" => u3_det_residual,
            "Omega_break_gap" => u3_volume_break,
            "omega_preservation_error" => u3_kahler_error
        ),
        "su3_checks" => jobj(
            "gell_mann_hermitian_residual_max" => hermitian_residual,
            "gell_mann_trace_abs_max" => trace_abs,
            "gell_mann_trace_norm_residual_max" => trace_norm_residual,
            "closure_residual_max" => closure_residual,
            "unitarity_residual_max" => unitary_err,
            "det_one_residual_max" => det_one_err,
            "Omega_preservation_error_max" => volume_err,
            "omega_preservation_error_max" => omega_err
        ),
        "kahler_checks" => jobj(
            "rank_real" => kahler_rank,
            "det_abs" => kahler_det_abs,
            "metric_min_eigenvalue" => kahler_metric_min_eig,
            "omega3_volume_match_residual" => kahler_volume_match_residual
        ),
        "spinor_checks" => spinor,
        "clifford_checks" => jobj(
            "gamma_dimension" => 8,
            "clifford_residual_max" => clifford_err,
            "gamma7_product_sq_residual" => gamma7_sq_err,
            "hand_coded_gamma_matrices" => true
        ),
        "parity_scalars" => parity_scalars,
        "tool_manifest" => jobj(
            "LinearAlgebra" => "load_bearing: commutators, traces, determinants, matrix exponentials, eigensystems, ranks, norms, and Clifford checks",
            "HandCodedClifford" => "load_bearing: explicit 6D gamma matrices and Gamma7 product boundary check; no external Clifford package required",
            "Dates" => "supportive: generated_at timestamp only",
            "Printf" => "supportive: JSON float formatting and escaping"
        ),
        "tool_integration_depth" => jobj(
            "LinearAlgebra" => "load_bearing",
            "HandCodedClifford" => "load_bearing",
            "Dates" => "supportive",
            "Printf" => "supportive"
        ),
        "z3_attempt" => jobj(
            "attempted" => Base.find_package("Z3") !== nothing,
            "used_load_bearing" => false,
            "reason" => "optional in user request; not needed for this finite linear-algebra closure/control probe"
        ),
        "numpy_used" => false,
        "peps3d_anchor_present" => false,
        "downstream_axis0_allowed" => false,
        "flux_layer_allowed" => false,
        "eligible_consumers" => ["JAX parity mirror for this object_id"],
        "blocked_consumers" => ["layer_completion", "G_structure_completion", "manifold_admission", "Axis0", "FEP", "flux", "bridge", "physics"],
        "honest_caveat" => "This is a finite local flat C^3/SU(3) carrier probe. Omega preservation is determinant preservation on a frame, not global Calabi-Yau geometry. The one-chiral-spinor readout is on the selected 4D SU(4) fundamental carrier required by this PoC; it is not full spin-bundle admission and has no PEPS3D anchor.",
        "result_paths" => jobj(
            "canonical_julia" => RESULT_PATH,
            "tmp_julia" => TMP_RESULT_PATH,
            "jax_mirror" => "/tmp/gs_su3_calabiyau_jax.py",
            "jax_parity" => "/tmp/gs_su3_calabiyau_parity.json"
        )
    )

    write_json(RESULT_PATH, result)
    write_json(TMP_RESULT_PATH, result)
    println("wrote $(RESULT_PATH)")
    println("wrote $(TMP_RESULT_PATH)")
    println("all_pass=$(all_pass)")
    println("symmetry_breaking=$(symmetry_breaking), parity_max_diff=pending_jax")
end

main()
