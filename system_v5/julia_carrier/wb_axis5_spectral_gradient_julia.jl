#!/usr/bin/env julia
# wb_axis5_spectral_gradient_julia.jl
#
# object_id: axis5_spectral_gradient_v1
# promotion_allowed: false
#
# Claim ceiling:
#   Does NOT assert layer-completion, manifold admission, coupling, bridge,
#   flux, or physics. A state that passes is a candidate, not a proven object.
#
# Root constraints:
#   F01: finite carrier/probe/operator/path set
#        8/16/32/64 L/R Weyl spinor density matrices; each carrier is 2x2 complex.
#   N01: noncommuting control domain
#        spectral-then-gradient and gradient-then-spectral are separated by a
#        Frobenius order gap under Ti and Fi.
#
# Finite map:
#   Domain:  (rho_L or rho_R, op_class in {spectral, gradient, commuting_control})
#   Codomain: (von_Neumann_entropy_after, entropy_gain, frobenius_order_gap, axis5_class)
#
# axis5_class:
#   "spectral" if entropy_gain > SPEC_EPS
#   "gradient" if abs(entropy_gain) < GRAD_EPS
#   "commuting_control" for the erased/commuting Ti+Fe control pair
#
# Operator classes:
#   {Ti, Te}: dephasing ops = SPECTRAL; eigenbasis-projective; diagonal readout.
#   {Fi, Fe}: rotation ops = GRADIENT; unitary flow; coherence-preserving readout.
#
# Checks:
#   Positive: Ti and Te entropy gain > SPEC_EPS on the size ladder.
#   Negative/N01: spectral-then-gradient != gradient-then-spectral for Ti and Fi.
#   Boundary/wrong-structure control: Ti and Fe share the z eigenbasis and are
#     indistinguishable under the entropy-gain/order-gap readout.
#
# Blocked downstream consumers:
#   layer-completion, manifold admission, coupling, bridge, Phi0, Xi, Axis0,
#   flux, and physics.
#
# Re-run:
#   julia --project=/Users/joshuaeisenhart/Desktop/Codex\ Ratchet/system_v5/julia_carrier \
#     /Users/joshuaeisenhart/Desktop/Codex\ Ratchet/system_v5/julia_carrier/wb_axis5_spectral_gradient_julia.jl

using LinearAlgebra
using Statistics
using Dates
using SHA

try
    @eval using JSON
catch _
    try
        import Pkg
        Pkg.activate(@__DIR__; io=devnull)
        @eval using JSON
    catch err
        error("JSON unavailable: $err")
    end
end

const OBJECT_ID = "axis5_spectral_gradient_v1"
const PROMOTION_ALLOWED = false
const RESULT_PATH = joinpath(@__DIR__, "wb_axis5_spectral_gradient_julia_results.json")
const RNG_SEED = 20260604
const SIZE_LADDER = [8, 16, 32, 64]

const SPEC_EPS = 1.0e-6
const GRAD_EPS = 1.0e-6
const COMMUTE_EPS = 1.0e-6
const N01_EPS = 1.0e-9
const PARITY_N = 32

const CLAIM_CEILING = "Does NOT assert layer-completion, manifold admission, coupling, bridge, flux, or physics. promotion_allowed=false. A state that passes is a candidate, not a proven object."

const I2 = Matrix{ComplexF64}(I, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SZ = ComplexF64[1 0; 0 -1]
const H = (SX + SZ) / sqrt(2.0)

rotation(pauli::Matrix{ComplexF64}, angle::Float64)::Matrix{ComplexF64} =
    cos(angle / 2.0) * I2 - im * sin(angle / 2.0) * pauli

const FI = rotation(SX, pi / 2.0)
const FE = rotation(SZ, pi / 2.0)

function unitary_apply(U::Matrix{ComplexF64}, rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    return U * rho * U'
end

function z_dephase(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    return ComplexF64[rho[1, 1] 0; 0 rho[2, 2]]
end

function x_dephase(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    rho_x = H * rho * H'
    return H' * ComplexF64[rho_x[1, 1] 0; 0 rho_x[2, 2]] * H
end

function von_neumann_entropy(rho::Matrix{ComplexF64})::Float64
    clean = Hermitian((rho + rho') / 2.0)
    total = 0.0
    for lambda in eigvals(clean)
        if lambda > 1.0e-14
            total -= lambda * log(lambda)
        end
    end
    return total
end

function density_valid(rho::Matrix{ComplexF64})::Bool
    trace_ok = abs(tr(rho) - 1.0) < 1.0e-10
    hermitian_ok = norm(rho - rho') < 1.0e-10
    eigen_ok = all(lambda >= -1.0e-10 for lambda in eigvals(Hermitian((rho + rho') / 2.0)))
    return trace_ok && hermitian_ok && eigen_ok
end

function seeded_fraction(seed::Int, n::Int, idx::Int, stride::Int, modulus::Int, offset::Int)::Float64
    raw = mod(mod(seed, modulus) + stride * n + offset * idx, modulus)
    return (Float64(raw) + 0.5) / Float64(modulus)
end

function seeded_angles(seed::Int, n::Int, idx::Int)
    theta_frac = seeded_fraction(seed, n, idx, 37, 997, 53)
    phi_frac = seeded_fraction(seed, n, idx, 101, 991, 67)
    chi_frac = seeded_fraction(seed, n, idx, 131, 983, 71)
    theta = pi * (0.11 + 0.78 * theta_frac)
    phi = 2.0 * pi * phi_frac
    chi = 2.0 * pi * chi_frac
    return theta, phi, chi
end

function weyl_density(seed::Int, n::Int, idx::Int, sheet_sign::Float64)::Matrix{ComplexF64}
    theta, phi, chi = seeded_angles(seed, n, idx)
    psi = ComplexF64[
        cis(phi + sheet_sign * chi) * cos(theta / 2.0),
        cis(phi - sheet_sign * chi) * sin(theta / 2.0),
    ]
    psi ./= norm(psi)
    return psi * psi'
end

chirality_for_index(idx::Int)::String = isodd(idx) ? "L" : "R"
sheet_sign_for_index(idx::Int)::Float64 = isodd(idx) ? 1.0 : -1.0

function ensemble(seed::Int, n::Int)
    return [
        weyl_density(seed, n, idx, sheet_sign_for_index(idx))
        for idx in 1:n
    ]
end

function axis5_class(op_class::String, entropy_gain::Float64)::String
    if op_class == "commuting_control"
        return "commuting_control"
    elseif entropy_gain > SPEC_EPS
        return "spectral"
    elseif abs(entropy_gain) < GRAD_EPS
        return "gradient"
    end
    return "excluded"
end

function order_readouts(rho::Matrix{ComplexF64})
    spectral_then_gradient = unitary_apply(FI, z_dephase(rho))
    gradient_then_spectral = z_dephase(unitary_apply(FI, rho))
    n01_gap = norm(spectral_then_gradient - gradient_then_spectral)

    control_spectral_then_gradient = unitary_apply(FE, z_dephase(rho))
    control_gradient_then_spectral = z_dephase(unitary_apply(FE, rho))
    control_gap = norm(control_spectral_then_gradient - control_gradient_then_spectral)

    s0 = von_neumann_entropy(rho)
    control_gain_a = von_neumann_entropy(control_spectral_then_gradient) - s0
    control_gain_b = von_neumann_entropy(control_gradient_then_spectral) - s0
    control_entropy_gain_gap = abs(control_gain_a - control_gain_b)

    return Dict(
        "n01_spectral_then_gradient_gap" => n01_gap,
        "n01_pass" => n01_gap > N01_EPS,
        "commuting_control_order_gap" => control_gap,
        "commuting_control_entropy_gain_gap" => control_entropy_gain_gap,
        "commuting_control_pass" => control_gap < COMMUTE_EPS && control_entropy_gain_gap < COMMUTE_EPS,
    )
end

function analyze_state(seed::Int, n::Int, idx::Int, rho::Matrix{ComplexF64})
    s0 = von_neumann_entropy(rho)

    rho_ti = z_dephase(rho)
    rho_te = x_dephase(rho)
    rho_fi = unitary_apply(FI, rho)
    rho_fe = unitary_apply(FE, rho)

    s_ti = von_neumann_entropy(rho_ti)
    s_te = von_neumann_entropy(rho_te)
    s_fi = von_neumann_entropy(rho_fi)
    s_fe = von_neumann_entropy(rho_fe)

    gain_ti = s_ti - s0
    gain_te = s_te - s0
    gain_fi = s_fi - s0
    gain_fe = s_fe - s0

    order = order_readouts(rho)

    theta, phi, chi = seeded_angles(seed, n, idx)

    return Dict(
        "state_index" => idx,
        "chirality" => chirality_for_index(idx),
        "seed_angles" => Dict("theta" => theta, "phi" => phi, "chi" => chi),
        "s0" => s0,
        "ops" => Dict(
            "Ti" => Dict(
                "op_class" => "spectral",
                "von_Neumann_entropy_after" => s_ti,
                "entropy_gain" => gain_ti,
                "frobenius_order_gap" => order["n01_spectral_then_gradient_gap"],
                "axis5_class" => axis5_class("spectral", gain_ti),
            ),
            "Te" => Dict(
                "op_class" => "spectral",
                "von_Neumann_entropy_after" => s_te,
                "entropy_gain" => gain_te,
                "frobenius_order_gap" => nothing,
                "axis5_class" => axis5_class("spectral", gain_te),
            ),
            "Fi" => Dict(
                "op_class" => "gradient",
                "von_Neumann_entropy_after" => s_fi,
                "entropy_gain" => gain_fi,
                "frobenius_order_gap" => order["n01_spectral_then_gradient_gap"],
                "axis5_class" => axis5_class("gradient", gain_fi),
            ),
            "Fe" => Dict(
                "op_class" => "gradient",
                "von_Neumann_entropy_after" => s_fe,
                "entropy_gain" => gain_fe,
                "frobenius_order_gap" => order["commuting_control_order_gap"],
                "axis5_class" => axis5_class("gradient", gain_fe),
            ),
            "Ti_Fe_commuting_control" => Dict(
                "op_class" => "commuting_control",
                "von_Neumann_entropy_after" => von_neumann_entropy(unitary_apply(FE, z_dephase(rho))),
                "entropy_gain" => von_neumann_entropy(unitary_apply(FE, z_dephase(rho))) - s0,
                "frobenius_order_gap" => order["commuting_control_order_gap"],
                "entropy_gain_gap" => order["commuting_control_entropy_gain_gap"],
                "axis5_class" => "commuting_control",
            ),
        ),
        "gain_spectral_Ti" => gain_ti,
        "gain_spectral_Te" => gain_te,
        "gain_gradient_Fi" => gain_fi,
        "gain_gradient_Fe" => gain_fe,
        "n01" => Dict(
            "spectral_then_gradient" => "Fi(Ti(rho))",
            "gradient_then_spectral" => "Ti(Fi(rho))",
            "frobenius_order_gap" => order["n01_spectral_then_gradient_gap"],
            "pass" => order["n01_pass"],
        ),
        "wrong_structure_control" => Dict(
            "control" => "erased/commuting Ti+Fe pair",
            "spectral_then_gradient" => "Fe(Ti(rho))",
            "gradient_then_spectral" => "Ti(Fe(rho))",
            "frobenius_order_gap" => order["commuting_control_order_gap"],
            "entropy_gain_gap" => order["commuting_control_entropy_gain_gap"],
            "indistinguishable" => order["commuting_control_pass"],
        ),
        "rho_valid" => density_valid(rho),
        "post_rho_valid" => Dict(
            "Ti" => density_valid(rho_ti),
            "Te" => density_valid(rho_te),
            "Fi" => density_valid(rho_fi),
            "Fe" => density_valid(rho_fe),
        ),
    )
end

function run_at_size(n::Int)
    states = ensemble(RNG_SEED, n)
    rows = Dict{String,Any}[]
    for (idx, rho) in enumerate(states)
        push!(rows, analyze_state(RNG_SEED, n, idx, rho))
    end

    gains_ti = [row["gain_spectral_Ti"] for row in rows]
    gains_te = [row["gain_spectral_Te"] for row in rows]
    gains_fi = [row["gain_gradient_Fi"] for row in rows]
    gains_fe = [row["gain_gradient_Fe"] for row in rows]
    n01_gaps = [row["n01"]["frobenius_order_gap"] for row in rows]
    control_gaps = [row["wrong_structure_control"]["frobenius_order_gap"] for row in rows]
    control_entropy_gaps = [row["wrong_structure_control"]["entropy_gain_gap"] for row in rows]

    spectral_ok = all(gain > SPEC_EPS for gain in gains_ti) &&
                  all(gain > SPEC_EPS for gain in gains_te)
    gradient_ok = all(abs(gain) < GRAD_EPS for gain in gains_fi) &&
                  all(abs(gain) < GRAD_EPS for gain in gains_fe)
    n01_ok = all(gap > N01_EPS for gap in n01_gaps)
    control_ok = all(gap < COMMUTE_EPS for gap in control_gaps) &&
                 all(gap < COMMUTE_EPS for gap in control_entropy_gaps)
    valid_ok = all(row["rho_valid"] && all(values(row["post_rho_valid"])) for row in rows)

    return Dict(
        "N" => n,
        "mean_gain_spectral_Ti" => mean(gains_ti),
        "mean_gain_spectral_Te" => mean(gains_te),
        "mean_gain_gradient_Fi" => mean(gains_fi),
        "mean_gain_gradient_Fe" => mean(gains_fe),
        "min_gain_spectral_Ti" => minimum(gains_ti),
        "min_gain_spectral_Te" => minimum(gains_te),
        "max_abs_gain_gradient_Fi" => maximum(abs.(gains_fi)),
        "max_abs_gain_gradient_Fe" => maximum(abs.(gains_fe)),
        "max_n01_frobenius_order_gap" => maximum(n01_gaps),
        "min_n01_frobenius_order_gap" => minimum(n01_gaps),
        "max_commuting_control_order_gap" => maximum(control_gaps),
        "max_commuting_control_entropy_gain_gap" => maximum(control_entropy_gaps),
        "spectral_entropy_gain_positive" => spectral_ok,
        "gradient_entropy_gain_near_zero" => gradient_ok,
        "n01_noncommuting_control_survived" => n01_ok,
        "wrong_structure_control_indistinguishable" => control_ok,
        "rho_valid" => valid_ok,
        "state_results" => rows,
        "all_pass" => spectral_ok && gradient_ok && n01_ok && control_ok && valid_ok,
    )
end

function result_payload()
    t0 = now()
    size_rows = Dict{String,Any}[run_at_size(n) for n in SIZE_LADDER]
    parity_ref = size_rows[findfirst(row -> row["N"] == PARITY_N, size_rows)]

    all_spectral = all(row["spectral_entropy_gain_positive"] for row in size_rows)
    all_gradient = all(row["gradient_entropy_gain_near_zero"] for row in size_rows)
    all_n01 = all(row["n01_noncommuting_control_survived"] for row in size_rows)
    all_control = all(row["wrong_structure_control_indistinguishable"] for row in size_rows)
    all_valid = all(row["rho_valid"] for row in size_rows)
    all_pass = all_spectral && all_gradient && all_n01 && all_control && all_valid

    return Dict(
        "object_id" => OBJECT_ID,
        "classification" => "tool_lego_fit_probe",
        "classification_note" => "candidate finite-map probe only; not canonical by process; promotion_allowed=false",
        "claim_ceiling" => CLAIM_CEILING,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "generated_at" => string(t0),
        "source_path" => @__FILE__,
        "source_sha256" => bytes2hex(sha256(read(@__FILE__))),
        "execution_command" => "julia --project=system_v5/julia_carrier --startup-file=no system_v5/julia_carrier/wb_axis5_spectral_gradient_julia.jl",
        "rng_seed" => RNG_SEED,
        "seed_protocol" => "deterministic arithmetic state table shared by Julia and JAX",
        "size_ladder" => SIZE_LADDER,
        "size_ladder_results" => size_rows,
        "ladder_results" => size_rows,
        "thresholds" => Dict(
            "SPEC_EPS" => SPEC_EPS,
            "GRAD_EPS" => GRAD_EPS,
            "COMMUTE_EPS" => COMMUTE_EPS,
            "N01_EPS" => N01_EPS,
        ),
        "parity_reference" => Dict(
            "N" => PARITY_N,
            "rng_seed" => RNG_SEED,
            "seed_protocol" => "deterministic arithmetic state table shared by Julia and JAX",
            "julia_spectral_entropy_gain" => parity_ref["mean_gain_spectral_Ti"],
            "julia_gradient_entropy_gain" => parity_ref["mean_gain_gradient_Fi"],
            "mean_gain_spectral_Ti" => parity_ref["mean_gain_spectral_Ti"],
            "mean_gain_gradient_Fi" => parity_ref["mean_gain_gradient_Fi"],
        ),
        "finite_map" => Dict(
            "domain" => "(rho_L or rho_R, op_class in {spectral, gradient, commuting_control})",
            "codomain_or_output" => "(von_Neumann_entropy_after, entropy_gain, frobenius_order_gap, axis5_class)",
            "axis5_class" => Dict(
                "spectral" => "entropy_gain > SPEC_EPS",
                "gradient" => "abs(entropy_gain) < GRAD_EPS",
                "commuting_control" => "erased/commuting Ti+Fe control pair",
            ),
        ),
        "root_constraints_in_force" => Dict(
            "F01" => "finite carrier: 8/16/32/64 L/R Weyl spinor density matrices, each 2x2 complex",
            "N01" => "Ti and Fi are order-sensitive under Frobenius readout",
        ),
        "positive_check" => Dict(
            "spectral_ops" => ["Ti", "Te"],
            "verdict" => all_spectral,
        ),
        "negative_check" => Dict(
            "name" => "N01 spectral-then-gradient != gradient-then-spectral",
            "verdict" => all_n01,
        ),
        "boundary_check" => Dict(
            "name" => "wrong-structure erased/commuting Ti+Fe pair",
            "verdict" => all_control,
        ),
        "all_spectral_raise_entropy" => all_spectral,
        "all_gradient_preserve_entropy" => all_gradient,
        "all_n01_noncommutativity" => all_n01,
        "all_commuting_control_ok" => all_control,
        "all_rho_valid" => all_valid,
        "monotone_split_survived" => all_spectral && all_gradient,
        "all_pass" => all_pass,
        "TOOL_MANIFEST" => Dict(
            "entropy_monotone_check" => Dict(
                "used" => true,
                "reason" => "load_bearing: von Neumann entropy gain decides the spectral/gradient readout; removal changes the verdict",
            ),
            "LinearAlgebra" => Dict(
                "used" => true,
                "reason" => "load_bearing: Hermitian eigenspectrum and Frobenius norms are used by the entropy and order-gap checks",
            ),
            "JSON" => Dict(
                "used" => true,
                "reason" => "supportive: result artifact emission",
            ),
            "SHA" => Dict(
                "used" => true,
                "reason" => "supportive: source hash for stale-receipt audit",
            ),
        ),
        "tool_manifest" => Dict(
            "entropy_monotone_check" => "load_bearing: removal changes the verdict",
            "LinearAlgebra" => "load_bearing",
            "JSON" => "supportive",
            "SHA" => "supportive",
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "entropy_monotone_check" => "load_bearing",
            "LinearAlgebra" => "load_bearing",
            "JSON" => "supportive",
            "SHA" => "supportive",
        ),
        "tool_integration_depth" => Dict(
            "entropy_monotone_check" => "load_bearing",
            "LinearAlgebra" => "load_bearing",
            "JSON" => "supportive",
            "SHA" => "supportive",
        ),
        "eligible_consumers" => ["JAX parity audit lane for this object_id"],
        "blocked_consumers" => ["layer-completion", "manifold admission", "coupling", "bridge", "Phi0", "Xi", "Axis0", "flux", "physics"],
        "promotion_blockers" => ["claim ceiling is candidate-only", "promotion_allowed=false", "no downstream bridge/coupling/layer admission packet"],
    )
end

function main()
    payload = result_payload()
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end

    println("=== AXIS-5 SPECTRAL/GRADIENT JULIA CARRIER ===")
    println("object_id: $OBJECT_ID")
    println("promotion_allowed: $PROMOTION_ALLOWED")
    println("result_path: $RESULT_PATH")
    println("all_pass: $(payload["all_pass"])")
    println("spectral_entropy_gain_positive: $(payload["all_spectral_raise_entropy"])")
    println("gradient_entropy_gain_near_zero: $(payload["all_gradient_preserve_entropy"])")
    println("n01_noncommuting_control_survived: $(payload["all_n01_noncommutativity"])")
    println("wrong_structure_control_indistinguishable: $(payload["all_commuting_control_ok"])")
    return payload["all_pass"]
end

ok = main()
exit(ok ? 0 : 1)
