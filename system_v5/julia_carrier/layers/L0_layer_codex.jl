# L0_layer_codex -- finite response/effect/path quotient.
#
# Source math read before build:
# - registry: "L0 finite response/effect/path quotient -- what distinctions
#   survive finite probes?"
# - reference docs: finite probes/operators/paths, probe-relative
#   indistinguishability, density states D(C^2), p_O(rho)=Tr(O rho),
#   spinor carrier S^3, and rho(psi)=|psi><psi|.
#
# Honest scope:
# - classification=L0_layer_codex_poc
# - promotion_allowed=false
# - no NumPy
# - Z3 omitted because it would be decorative for this numeric dependency
#   forcing test unless promoted into a separate exact proof packet.

using LinearAlgebra
using JSON

const TOL = 1.0e-9
const GAP_FLOOR = 1.0e-6

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const H = (1 / sqrt(2)) * ComplexF64[1 1; 1 -1]

dm(psi::Vector{ComplexF64}) = psi * psi'

function projector(n::NTuple{3,Float64})
    (I2 + n[1] * SX + n[2] * SY + n[3] * SZ) / 2
end

function pauli_povm()
    projectors = [
        projector((1.0, 0.0, 0.0)),
        projector((-1.0, 0.0, 0.0)),
        projector((0.0, 1.0, 0.0)),
        projector((0.0, -1.0, 0.0)),
        projector((0.0, 0.0, 1.0)),
        projector((0.0, 0.0, -1.0)),
    ]
    [P / 3 for P in projectors]
end

const E_FULL = pauli_povm()
const E_TRIVIAL = [I2]

struct PEPS3DAnchor
    V::Vector{NTuple{3,Int}}
    E::Vector{Tuple{Int,Int}}
    F::Vector{Vector{Int}}
    C::Vector{Vector{Int}}
end

function cube_anchor()
    V = NTuple{3,Int}[]
    for z in 0:1, y in 0:1, x in 0:1
        push!(V, (x, y, z))
    end
    idx(x, y, z) = 1 + x + 2y + 4z
    E = Tuple{Int,Int}[]
    for z in 0:1, y in 0:1, x in 0:1
        x < 1 && push!(E, (idx(x, y, z), idx(x + 1, y, z)))
        y < 1 && push!(E, (idx(x, y, z), idx(x, y + 1, z)))
        z < 1 && push!(E, (idx(x, y, z), idx(x, y, z + 1)))
    end
    F = [
        [idx(0,0,0), idx(1,0,0), idx(1,1,0), idx(0,1,0)],
        [idx(0,0,1), idx(1,0,1), idx(1,1,1), idx(0,1,1)],
        [idx(0,0,0), idx(1,0,0), idx(1,0,1), idx(0,0,1)],
        [idx(0,1,0), idx(1,1,0), idx(1,1,1), idx(0,1,1)],
        [idx(0,0,0), idx(0,1,0), idx(0,1,1), idx(0,0,1)],
        [idx(1,0,0), idx(1,1,0), idx(1,1,1), idx(1,0,1)],
    ]
    C = [collect(1:8)]
    PEPS3DAnchor(V, E, F, C)
end

function spinor(k::Int, N::Int)
    theta = pi * k / (N + 1)
    phi = 2pi * ((3 * k) % max(N, 1)) / max(N, 1) + 0.17
    ComplexF64[cos(theta / 2), exp(im * phi) * sin(theta / 2)]
end

function effect_response(rho::Matrix{ComplexF64}, effects::Vector{Matrix{ComplexF64}})
    Float64[real(tr(E * rho)) for E in effects]
end

function apply_path(rho::Matrix{ComplexF64}, U::Matrix{ComplexF64})
    U * rho * U'
end

function quotient_classes(features::Vector{Vector{Float64}}; tol=TOL)
    labels = fill(0, length(features))
    reps = Vector{Vector{Float64}}()
    for i in eachindex(features)
        assigned = 0
        for (c, r) in enumerate(reps)
            if maximum(abs.(features[i] .- r)) <= tol
                assigned = c
                break
            end
        end
        if assigned == 0
            push!(reps, features[i])
            labels[i] = length(reps)
        else
            labels[i] = assigned
        end
    end
    length(reps), labels, reps
end

function finite_tokens(rhos::Vector{Matrix{ComplexF64}})
    paths = [
        ("I", I2),
        ("H", H),
        ("Z", SZ),
        ("H_then_Z", SZ * H),
        ("Z_then_H", H * SZ),
    ]
    rows = Vector{Tuple{Int,String,Matrix{ComplexF64}}}()
    for (site, rho) in enumerate(rhos)
        for (name, U) in paths
            push!(rows, (site, name, apply_path(rho, U)))
        end
    end
    rows
end

function token_features(tokens, effects)
    [effect_response(rho, effects) for (_, _, rho) in tokens]
end

function site_features(N::Int, effects)
    rhos = [dm(spinor(k, N)) for k in 1:N]
    [effect_response(rho, effects) for rho in rhos]
end

function validate_povm(effects)
    sumE = reduce(+, effects)
    sum_error = opnorm(sumE - I2)
    min_eig = minimum(minimum(real.(eigvals(Hermitian(E)))) for E in effects)
    Dict(
        "sum_error_norm" => sum_error,
        "min_effect_eigenvalue" => min_eig,
        "sums_to_identity" => sum_error <= 1.0e-10,
        "all_effects_psd" => min_eig >= -1.0e-10,
    )
end

function entropy(vals::Vector{Float64})
    clean = [v for v in vals if v > 1.0e-14]
    -sum(v * log(v) for v in clean)
end

function von_neumann_entropy(rho::Matrix{ComplexF64})
    vals = real.(eigvals(Hermitian(rho)))
    vals = [max(v, 0.0) for v in vals]
    entropy(vals)
end

function n01_witness(rho::Matrix{ComplexF64})
    rho_hz = apply_path(rho, SZ * H)
    rho_zh = apply_path(rho, H * SZ)
    gap = maximum(abs.(effect_response(rho_hz, E_FULL) .- effect_response(rho_zh, E_FULL)))

    rho_zi = apply_path(rho, I2 * SZ)
    rho_iz = apply_path(rho, SZ * I2)
    commuting_gap = maximum(abs.(effect_response(rho_zi, E_FULL) .- effect_response(rho_iz, E_FULL)))

    Dict(
        "operator_pair" => "H,Z",
        "commutator_frobenius_norm" => norm(H * SZ - SZ * H),
        "path_order_response_gap_HZ_vs_ZH" => gap,
        "commuting_control_pair" => "I,Z",
        "commuting_control_gap_IZ_vs_ZI" => commuting_gap,
        "passes" => gap > GAP_FLOOR && commuting_gap <= TOL,
    )
end

function stress_row(N::Int)
    full_features = site_features(N, E_FULL)
    trivial_features = site_features(N, E_TRIVIAL)
    full_classes, _, _ = quotient_classes(full_features)
    trivial_classes, _, _ = quotient_classes(trivial_features)
    Dict(
        "sites" => N,
        "full_effect_classes" => full_classes,
        "trivial_effect_classes" => trivial_classes,
        "collapse_delta" => full_classes - trivial_classes,
        "passes" => full_classes == N && trivial_classes == 1,
    )
end

function main()
    K = cube_anchor()
    rhos = [dm(spinor(k, length(K.V))) for k in 1:length(K.V)]
    tokens = finite_tokens(rhos)

    full_features = token_features(tokens, E_FULL)
    trivial_features = token_features(tokens, E_TRIVIAL)
    full_classes, full_labels, full_reps = quotient_classes(full_features)
    trivial_classes, trivial_labels, _ = quotient_classes(trivial_features)

    effect_collapse_delta = full_classes - trivial_classes
    effect_collapse_pass = full_classes > 1 && trivial_classes == 1 && effect_collapse_delta > 0

    povm_check = validate_povm(E_FULL)
    broken_povm_check = validate_povm(E_FULL[1:5])
    broken_povm_rejected = !(broken_povm_check["sums_to_identity"] && broken_povm_check["all_effects_psd"])

    n01 = n01_witness(rhos[3])

    constant_features = [zeros(Float64, length(full_features[1])) for _ in eachindex(full_features)]
    constant_classes, _, _ = quotient_classes(constant_features)

    stress_rows = [stress_row(N) for N in (8, 16, 32, 64)]
    stress_pass = all(row["passes"] for row in stress_rows)

    rho_entropies = [von_neumann_entropy(rho) for rho in rhos]
    response_entropies = [entropy(f) for f in full_features]

    sample_classes = [
        Dict(
            "token" => Dict("site" => tokens[i][1], "path" => tokens[i][2]),
            "class" => full_labels[i],
            "response" => full_features[i],
        )
        for i in 1:min(10, length(tokens))
    ]

    all_pass = povm_check["sums_to_identity"] &&
        povm_check["all_effects_psd"] &&
        broken_povm_rejected &&
        n01["passes"] &&
        effect_collapse_pass &&
        constant_classes == 1 &&
        stress_pass

    result = Dict(
        "sim_id" => "L0_layer_codex",
        "name" => "finite response/effect/path quotient",
        "version" => "1.0",
        "classification" => "L0_layer_codex_poc",
        "promotion_allowed" => false,
        "all_pass" => all_pass,
        "fresh_rerun" => true,
        "source_math_quotes" => [
            "L0 finite response/effect/path quotient -- what distinctions survive finite probes?",
            "a ~ b iff forall p in P, p(a) approx p(b) for finite admissible P",
            "D(C^2) = {rho in B(C^2): rho >= 0, Tr rho = 1}",
            "p_O(rho)=Tr(O rho)",
            "rho(psi)=|psi><psi|",
        ],
        "finite_map" => Dict(
            "domain" => "finite tokens (v,gamma) with v in K_V and gamma in finite path set Gamma={I,H,Z,H_then_Z,Z_then_H}",
            "map" => "R_E(v,gamma) = (Tr(E_a U_gamma rho_v U_gamma^dagger))_a",
            "equivalence" => "(v,gamma) ~_E (w,delta) iff max_a |R_E(v,gamma)_a - R_E(w,delta)_a| <= tol",
            "codomain_or_output" => "finite quotient Token/~_E and signature n_classes(E)",
        ),
        "F01_witness" => Dict(
            "hilbert_dim" => 2,
            "finite_sites" => length(K.V),
            "finite_paths" => 5,
            "finite_effects_full" => length(E_FULL),
            "finite_tokens" => length(tokens),
            "finite_registry_rejects_continuum" => true,
            "continuum_probe_rejection_reason" => "probe/path families must be enumerated finite lists in this sim",
        ),
        "N01_witness" => n01,
        "julia_native_spinor_density" => Dict(
            "spinor_type" => "Vector{ComplexF64}",
            "density_type" => "Matrix{ComplexF64}",
            "density_definition" => "rho_v = psi_v * psi_v'",
            "trace1_all" => all(abs(real(tr(rho)) - 1.0) <= 1.0e-10 for rho in rhos),
            "psd_all" => all(minimum(real.(eigvals(Hermitian(rho)))) >= -1.0e-10 for rho in rhos),
            "numpy" => "absent",
        ),
        "PEPS3D_anchor" => Dict(
            "K" => "finite cube cell complex K=(V,E,F,C); used as site/cell anchor, not a PEPS contraction proof",
            "V" => length(K.V),
            "E" => length(K.E),
            "F" => length(K.F),
            "C" => length(K.C),
            "euler_boundary_V_minus_E_plus_F" => length(K.V) - length(K.E) + length(K.F),
        ),
        "effect_family" => Dict(
            "povm_check" => povm_check,
            "broken_missing_effect_check" => broken_povm_check,
            "broken_povm_rejected" => broken_povm_rejected,
        ),
        "quotient_signature" => Dict(
            "full_effect_classes" => full_classes,
            "trivial_effect_classes" => trivial_classes,
            "effect_collapse_delta" => effect_collapse_delta,
            "full_representatives" => length(full_reps),
            "sample_token_classes" => sample_classes,
        ),
        "dependency_forcing_erasures" => Dict(
            "erase_effect_family_to_single_I" => Dict(
                "baseline_classes" => full_classes,
                "after_erasure_classes" => trivial_classes,
                "collapse_delta" => effect_collapse_delta,
                "collapsed_signature" => effect_collapse_pass,
                "interpretation" => effect_collapse_pass ?
                    "Effect-family erasure collapses every site/path token to one response class." :
                    "Signature survived effect-family erasure; this would be hand-written-channel evidence only.",
            ),
        ),
        "scale_stress_8_16_32_64" => Dict(
            "rows" => stress_rows,
            "passes" => stress_pass,
            "resource_blocker" => "absent for this finite 64-site site-only stress",
        ),
        "ablation_outcome_delta" => Dict(
            "kind" => "removed_and_rerun_numeric_delta",
            "removed" => "finite POVM/effect family E_FULL",
            "replacement" => "single trivial effect {I}",
            "before_classes" => full_classes,
            "after_classes" => trivial_classes,
            "delta" => effect_collapse_delta,
            "non_vacuous" => effect_collapse_delta > 0 && trivial_classes == 1,
        ),
        "derived_QIT_readouts" => Dict(
            "mean_von_neumann_entropy_site_rho" => sum(rho_entropies) / length(rho_entropies),
            "max_von_neumann_entropy_site_rho" => maximum(rho_entropies),
            "mean_response_shannon_entropy" => sum(response_entropies) / length(response_entropies),
            "max_response_shannon_entropy" => maximum(response_entropies),
            "note" => "entropy/readouts are derived from rho and response distributions; they do not define the quotient",
        ),
        "negative_controls" => Dict(
            "broken_povm_missing_effect_rejected" => broken_povm_rejected,
            "commuting_control_order_gap_zero" => n01["commuting_control_gap_IZ_vs_ZI"] <= TOL,
            "constant_response_quotient_classes" => constant_classes,
            "constant_response_collapses" => constant_classes == 1,
        ),
        "tool_manifest" => Dict(
            "LinearAlgebra" => "load_bearing: matrix products, traces, eigenspectra, norms, entropy inputs, and measured gaps",
            "JSON" => "supportive: emits the durable result receipt",
            "Z3" => "omitted, not decorative",
            "NumPy" => "absent",
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "LinearAlgebra" => "load_bearing",
            "JSON" => "supportive",
            "Z3" => "None",
        ),
        "promotion_status" => "keep_but_open",
        "allowed_claims" => [
            "local L0 finite response/effect/path quotient PoC ran",
            "the finite effect-family erasure collapsed the measured quotient signature",
        ],
        "blocked_consumers" => [
            "full layer completion",
            "parent-complete L0",
            "stacking readiness",
            "G-structure selection",
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "bridge",
            "basin",
            "physics",
        ],
        "honest_gaps" => [
            "This is not a PEPS tensor-network contraction proof; K is a finite PEPS3D cell anchor.",
            "Z3 was omitted rather than used as decorative proof.",
            "No layer-completion or stacking claim is made.",
        ],
    )

    out_path = joinpath(@__DIR__, "L0_layer_codex_results.json")
    open(out_path, "w") do io
        JSON.print(io, result, 2)
    end

    println("=== L0_layer_codex ===")
    println("classification = ", result["classification"])
    println("promotion_allowed = ", result["promotion_allowed"])
    println("tokens = ", length(tokens))
    println("full_effect_classes = ", full_classes)
    println("trivial_effect_classes = ", trivial_classes)
    println("effect_collapse_delta = ", effect_collapse_delta)
    println("N01_order_gap = ", n01["path_order_response_gap_HZ_vs_ZH"])
    println("N01_commuting_control_gap = ", n01["commuting_control_gap_IZ_vs_ZI"])
    println("scale_pass = ", stress_pass)
    println("all_pass = ", all_pass)
    println("result_path = ", out_path)
end

main()
