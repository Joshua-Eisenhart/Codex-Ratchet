#!/usr/bin/env julia
# =============================================================================
# nesting_order_pairwise_confluence.jl
#
# Bounded probe for the nested-Hopf noncommutative stacking-order blocker.
# classification = nesting_order_probe_poc ; promotion_allowed = false.
#
# Claim ceiling:
#   Measures pairwise substrate-dressed order differences and depth-3/full-stack
#   confluence classes on a finite density-operator carrier. It does not assert a
#   canonical nesting order, layer completion, manifold admission, bridge, flux,
#   Axis0, FEP, or physics progress. Every total order that remains distinct is
#   only a candidate order.
#
# Genuine source surfaces reused here:
#   - system_v5/julia_carrier/layers/L7_layer_bf.jl
#       Weyl L/R GKSL density-operator channel form.
#   - system_v5/julia_carrier/layers/L10_layer_bf.jl
#       Hopf-driven terrain GKSL channel form and hopf_h0 frame construction.
#   - system_v5/julia_carrier/layers/L11_layer_bf.jl
#       Ti/Te/Fi/Fe density-operator channels and commuting same-axis control.
#   - system_v5/julia_carrier/layers/order_null_killtest.jl
#       dynamic order-gap measurement, explicit noise floor, Z3 flip pattern.
#   - system_v5/julia_carrier/layers/substrate_effect_frame_conjugation.jl
#       substrate frame conjugation Phi_B^A(rho)=U_A Phi_B(U_A' rho U_A) U_A'.
#   - structure frames:
#       s3_hopf, nested_hopf_tori, clifford_rotor, frame_bundle_so3, weyl_lr.
#
# No Bloch-state carrier is used. The carrier is rho in D(C^2), with channels
# rho -> rho and substrate frame conjugation. Pauli matrices appear only as
# operator generators for the quoted channels/frames, matching the existing
# density-operator Julia probes.
# =============================================================================

using LinearAlgebra
using Random
using Statistics
using Printf
import JSON
import Z3

const RESULT_PATH = joinpath(@__DIR__, "nesting_order_pairwise_confluence_results.json")
const SOURCE_LAYER_DIR = joinpath(@__DIR__, "..", "system_v5", "julia_carrier", "layers")
const SEED = 20260602
const N_RHO = 25

# ----------------------------- 2x2 density carrier ---------------------------
const I2 = Matrix{ComplexF64}(I, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SP = ComplexF64[0 1; 0 0]   # sigma_+ / source jump
const SM = ComplexF64[0 0; 1 0]   # sigma_- / sink jump
const P0 = (I2 + SZ) / 2
const P1 = (I2 - SZ) / 2
const QP = (I2 + SX) / 2
const QM = (I2 - SX) / 2

trace_norm(M) = sum(svdvals(M))
hs_norm(M) = sqrt(real(tr(M' * M)))

function reproject_density(rho)
    h = (rho + rho') / 2
    vals, vecs = eigen(Hermitian(h))
    vals = max.(real.(vals), 0.0)
    s = sum(vals)
    s < 1e-14 && return Matrix{ComplexF64}(I2 / 2)
    out = vecs * Diagonal(ComplexF64.(vals ./ s)) * vecs'
    return (out + out') / 2
end

function rand_rho(rng)
    psi = ComplexF64[randn(rng) + im * randn(rng), randn(rng) + im * randn(rng)]
    psi /= norm(psi)
    pure = psi * psi'
    p = 0.2 + 0.6 * rand(rng)
    rho = p * pure + (1 - p) * (I2 / 2)
    reproject_density(rho)
end

function make_rhos(rng, n)
    fixed = Matrix{ComplexF64}[
        I2 / 2,
        reproject_density(ComplexF64[0.62 0.30+0.18im; 0.30-0.18im 0.38]),
        reproject_density(ComplexF64[0.72 0.08-0.22im; 0.08+0.22im 0.28]),
    ]
    vcat([rand_rho(rng) for _ in 1:n], fixed)
end

function density_health(rho)
    h = (rho + rho') / 2
    vals = real.(eigvals(Hermitian(h)))
    Dict(
        "trace_error" => abs(real(tr(h)) - 1.0),
        "hermitian_error" => norm(rho - rho'),
        "min_eigenvalue" => minimum(vals),
    )
end

# ---------------------- genuine channel formulas, copied not invented --------
# L11_layer_bf.jl intrinsic channels.
phi_ti(rho, q) = (1 - q) * rho + q * (P0 * rho * P0 + P1 * rho * P1)
phi_te(rho, q) = (1 - q) * rho + q * (QP * rho * QP + QM * rho * QM)
ux(theta) = ComplexF64[cos(theta/2) (-im*sin(theta/2)); (-im*sin(theta/2)) cos(theta/2)]
uz(phi) = ComplexF64[cis(-phi/2) 0; 0 cis(phi/2)]
phi_fi(rho, theta) = ux(theta) * rho * ux(theta)'
phi_fe(rho, phi) = uz(phi) * rho * uz(phi)'

# L7/L10_layer_bf.jl GKSL form.
dissipator(L, rho) = L * rho * L' - 0.5 * ((L' * L) * rho + rho * (L' * L))
commutator_flow(H, rho) = -im * (H * rho - rho * H)

function gksl_step_evolve(rho0, H, L; gamma=1.0, eps=1.0, T=4.0, steps=240)
    dt = T / steps
    rho = rho0
    for _ in 1:steps
        rho = rho + dt * (gamma * dissipator(L, rho) + eps * commutator_flow(H, rho))
        rho = reproject_density(rho)
    end
    rho
end

# L10_layer_bf.jl Hopf site / Hamiltonian form.
function hopf_spinor(phi::Float64, chi::Float64, eta::Float64)
    psi = ComplexF64[exp(im * (phi + chi)) * cos(eta),
                     exp(im * (phi - chi)) * sin(eta)]
    psi / norm(psi)
end

function hopf_h0(phi::Float64, chi::Float64, eta::Float64)
    psi = hopf_spinor(phi, chi, eta)
    n = [real(psi' * (p * psi)) for p in (SX, SY, SZ)]
    nn = norm(n)
    nhat = nn < 1e-12 ? [0.0, 0.0, 1.0] : n ./ nn
    nhat[1] * SX + nhat[2] * SY + nhat[3] * SZ
end

# ----------------------------- genuine frames --------------------------------
# substrate_effect_frame_conjugation.jl / G_hopf_fibration.jl.
function su2_frame(z1::ComplexF64, z2::ComplexF64)
    n = sqrt(abs2(z1) + abs2(z2))
    z1 /= n
    z2 /= n
    ComplexF64[z1 (-conj(z2)); z2 conj(z1)]
end

hopf_frame(theta, phi) =
    su2_frame(ComplexF64(cos(theta / 2)), ComplexF64(sin(theta / 2) * exp(im * phi)))

# G_nested_hopf_tori.jl / nested_hopf_tori_spinor_network.jl leaf.
leaf_frame(theta, a, b) =
    su2_frame(ComplexF64(cos(theta) * exp(im * a)),
              ComplexF64(sin(theta) * exp(im * b)))

# clifford_rotor_spinor_network_entanglement.jl / substrate_effect_frame_conjugation.jl.
function clifford_rotor(angle::Float64, n::Vector{Float64})
    nh = n / norm(n)
    B = nh[1] * SX + nh[2] * SY + nh[3] * SZ
    exp(-im * angle / 2 * B)
end

# frame_bundle_so3_spinor_network.jl SU(2) double cover frame.
function so3_su2(n::Vector{Float64}, angle::Float64)
    nh = n / norm(n)
    cos(angle / 2) * I2 - im * sin(angle / 2) * (nh[1] * SX + nh[2] * SY + nh[3] * SZ)
end

# ----------------------------- layer model -----------------------------------
struct GenuineLayer
    name::String
    source::String
    frame::Matrix{ComplexF64}
    channel::Function
end

dressed_channel(chan, substrate_frame, rho) =
    substrate_frame * chan(substrate_frame' * rho * substrate_frame) * substrate_frame'

function build_layers()
    q = 0.65
    ang = 0.9
    phi0, chi0, eta0 = 2pi * 0.21, 2pi * 0.13, pi / 4
    H0 = hopf_h0(phi0, chi0, eta0)

    U_weyl = exp(-im * 0.45 * H0)                    # Weyl L/R H0 rotor frame.
    U_hopf = hopf_frame(pi / 3, 0.7)                 # S3 Hopf representative frame.
    U_leaf = leaf_frame(pi / 4, 0.6, 1.9)            # nested-Hopf-tori leaf.
    U_cliff = clifford_rotor(0.9, [0.2, 0.7, 0.5])   # Clifford rotor.
    U_so3 = so3_su2([0.3, 0.5, 0.8], 1.1)            # frame-bundle SO(3) spin cover.

    GenuineLayer[
        GenuineLayer(
            "weyl_lr_gksl",
            "L7_layer_bf.jl Weyl L/R GKSL; weyl_lr_spinor_network_entanglement.jl H_L=+H0/H_R=-H0",
            U_weyl,
            rho -> gksl_step_evolve(rho, +H0, SM),
        ),
        GenuineLayer(
            "s3_hopf_terrain",
            "G_hopf_fibration.jl Hopf frame; L10_layer_bf.jl Ni R-sheet Hopf-driven terrain GKSL",
            U_hopf,
            rho -> gksl_step_evolve(rho, -H0, SP),
        ),
        GenuineLayer(
            "nested_hopf_tori_cell",
            "G_nested_hopf_tori.jl leaf frame; L11_layer_bf.jl Te/Fi x-axis local cell channel",
            U_leaf,
            rho -> phi_fi(phi_te(rho, q), ang),
        ),
        GenuineLayer(
            "clifford_rotor",
            "clifford_rotor_spinor_network_entanglement.jl SU(2)~Cl(3,0) even rotor",
            U_cliff,
            rho -> U_cliff * rho * U_cliff',
        ),
        GenuineLayer(
            "frame_bundle_so3",
            "frame_bundle_so3_spinor_network.jl SO(3) frame via SU(2) double cover",
            U_so3,
            rho -> U_so3 * rho * U_so3',
        ),
    ]
end

# ----------------------------- metrics ---------------------------------------
function pairwise_order_stats(A::GenuineLayer, B::GenuineLayer, rhos)
    vals = Float64[]
    for rho in rhos
        a_on_b = dressed_channel(A.channel, B.frame, rho)
        b_on_a = dressed_channel(B.channel, A.frame, rho)
        push!(vals, trace_norm(reproject_density(a_on_b) - reproject_density(b_on_a)))
    end
    Dict(
        "mean" => mean(vals),
        "max" => maximum(vals),
        "min" => minimum(vals),
        "std" => length(vals) > 1 ? std(vals) : 0.0,
        "range" => maximum(vals) - minimum(vals),
        "per_input" => vals,
    )
end

function stack_apply(order::Vector{Int}, layers::Vector{GenuineLayer}, rho)
    # order is top -> bottom. Bottom acts bare; each upper layer is run on the
    # frame supplied by the layer directly below it.
    out = layers[order[end]].channel(rho)
    out = reproject_density(out)
    for pos in (length(order)-1):-1:1
        top = layers[order[pos]]
        substrate = layers[order[pos+1]]
        out = dressed_channel(top.channel, substrate.frame, out)
        out = reproject_density(out)
    end
    out
end

function outputs_for_order(order, layers, rhos)
    [stack_apply(order, layers, rho) for rho in rhos]
end

function order_output_gap(out_a, out_b)
    maximum(trace_norm(out_a[k] - out_b[k]) for k in eachindex(out_a))
end

function permutations_vec(v::Vector{Int})
    length(v) == 1 && return [copy(v)]
    out = Vector{Vector{Int}}()
    for i in eachindex(v)
        rest = [v[j] for j in eachindex(v) if j != i]
        for p in permutations_vec(rest)
            push!(out, vcat([v[i]], p))
        end
    end
    out
end

function cluster_orders(orders, outputs, threshold)
    clusters = Vector{Vector{Int}}()
    reps = Int[]
    for i in eachindex(orders)
        placed = false
        for (ci, rep) in enumerate(reps)
            if order_output_gap(outputs[i], outputs[rep]) <= threshold
                push!(clusters[ci], i)
                placed = true
                break
            end
        end
        if !placed
            push!(reps, i)
            push!(clusters, [i])
        end
    end
    clusters
end

function format_order(order, labels)
    join([labels[i] for i in order], " -> ")
end

# ----------------------------- controls --------------------------------------
function flat_substrate_control(layers, rhos)
    vals = Float64[]
    for layer in layers, rho in rhos
        push!(vals, trace_norm(dressed_channel(layer.channel, I2, rho) - layer.channel(rho)))
    end
    Dict("max" => maximum(vals), "mean" => mean(vals), "per_check" => vals)
end

function commuting_pair_control(rhos)
    q = 0.65
    ang = 0.9
    vals = Float64[]
    for rho in rhos
        ab = phi_ti(phi_fe(rho, ang), q)
        ba = phi_fe(phi_ti(rho, q), ang)
        push!(vals, trace_norm(ab - ba))
    end
    Dict(
        "pair" => "L11 same-axis z-pinch Ti and z-rotation Fe",
        "source" => "L11_layer_bf.jl same-axis commuting control",
        "max" => maximum(vals),
        "mean" => mean(vals),
        "per_input" => vals,
    )
end

function z3_order_obstruction(measured_gap::Float64; scale=1_000_000_000)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    gap = Z3.IntVar("gap", ctx)
    erased_or_commuting = Z3.BoolVar("erased_or_commuting", ctx)
    Z3.add(solver, Z3.Or([Z3.Not(erased_or_commuting), gap == Z3.IntVal(0, ctx)]))
    Z3.add(solver, erased_or_commuting == Z3.BoolVal(true, ctx))
    m = round(Int, scale * abs(measured_gap))
    Z3.add(solver, gap == Z3.IntVal(m, ctx))
    string(Z3.check(solver))
end

function frame_diagnostics(U)
    Dict(
        "unitary_error" => norm(U' * U - I2),
        "det_abs" => abs(det(U)),
        "distance_from_identity_hs" => hs_norm(U - I2),
    )
end

function main()
    rng = MersenneTwister(SEED)
    rhos = make_rhos(rng, N_RHO)
    layers = build_layers()
    labels = [l.name for l in layers]
    n = length(layers)

    # Explicit floor. The trace norm of a density difference is O(1); each stack
    # uses a small fixed number of 2x2 matmul/channel operations.
    noise_floor = eps(Float64) * 1.0 * 8.0 * 128.0
    classification_floor = max(1.0e-8, 100_000.0 * noise_floor)

    pair_stats = Dict{String,Any}()
    pair_matrix = zeros(Float64, n, n)
    range_matrix = zeros(Float64, n, n)
    for i in 1:n, j in 1:n
        if i == j
            pair_stats["$(labels[i])__on__$(labels[j])"] = Dict(
                "mean" => 0.0, "max" => 0.0, "min" => 0.0, "std" => 0.0,
                "range" => 0.0, "per_input" => zeros(Float64, length(rhos)),
            )
        else
            st = pairwise_order_stats(layers[i], layers[j], rhos)
            pair_stats["$(labels[i])__on__$(labels[j])"] = st
            pair_matrix[i, j] = st["max"]
            range_matrix[i, j] = st["range"]
        end
    end

    commuting_pairs = String[]
    order_mattering_pairs = String[]
    input_dependent_pairs = String[]
    for i in 1:n-1, j in i+1:n
        gap = pair_matrix[i, j]
        rngap = range_matrix[i, j]
        pair_label = "$(labels[i]) <-> $(labels[j])"
        if gap <= classification_floor
            push!(commuting_pairs, pair_label)
        else
            push!(order_mattering_pairs, pair_label)
            rngap > classification_floor && push!(input_dependent_pairs, pair_label)
        end
    end

    flat_control = flat_substrate_control(layers, rhos)
    commute_control = commuting_pair_control(rhos)

    # Depth-3 confluence over every 3-layer subset.
    triple_reports = Vector{Dict{String,Any}}()
    for a in 1:n-2, b in a+1:n-1, c in b+1:n
        subset = [a, b, c]
        orders = permutations_vec(subset)
        outs = [outputs_for_order(o, layers, rhos) for o in orders]
        dm = zeros(Float64, length(orders), length(orders))
        for i in eachindex(orders), j in eachindex(orders)
            dm[i, j] = i == j ? 0.0 : order_output_gap(outs[i], outs[j])
        end
        clusters = cluster_orders(orders, outs, classification_floor)
        push!(triple_reports, Dict(
            "layers" => [labels[i] for i in subset],
            "n_orderings" => length(orders),
            "max_terminal_gap" => maximum(dm),
            "confluent" => maximum(dm) <= classification_floor,
            "n_survivor_classes" => length(clusters),
            "survivor_clusters" => [
                Dict(
                    "size" => length(cluster),
                    "orders" => [format_order(orders[idx], labels) for idx in cluster],
                ) for cluster in clusters
            ],
            "distance_matrix_order_labels" => [format_order(o, labels) for o in orders],
            "distance_matrix_max_trace_norm" => dm,
        ))
    end

    # Full 5-layer stack order classes.
    full_orders = permutations_vec(collect(1:n))
    full_outputs = [outputs_for_order(o, layers, rhos) for o in full_orders]
    full_clusters = cluster_orders(full_orders, full_outputs, classification_floor)
    full_max_gap = 0.0
    for i in eachindex(full_orders), j in i+1:length(full_orders)
        full_max_gap = max(full_max_gap, order_output_gap(full_outputs[i], full_outputs[j]))
    end

    health_records = Dict{String,Any}()
    invalid_orders = String[]
    for (idx, order) in enumerate(full_orders)
        max_trace_err = 0.0
        max_herm_err = 0.0
        min_eval = Inf
        for rho in full_outputs[idx]
            h = density_health(rho)
            max_trace_err = max(max_trace_err, h["trace_error"])
            max_herm_err = max(max_herm_err, h["hermitian_error"])
            min_eval = min(min_eval, h["min_eigenvalue"])
        end
        ok = max_trace_err < 1e-8 && max_herm_err < 1e-8 && min_eval > -1e-8
        label = format_order(order, labels)
        health_records[label] = Dict(
            "density_valid" => ok,
            "max_trace_error" => max_trace_err,
            "max_hermitian_error" => max_herm_err,
            "min_eigenvalue" => min_eval,
        )
        ok || push!(invalid_orders, label)
    end

    full_cluster_payload = [
        Dict(
            "class_id" => k,
            "size" => length(cluster),
            "orders" => [format_order(full_orders[idx], labels) for idx in cluster[1:min(end, 12)]],
            "orders_omitted" => max(length(cluster) - 12, 0),
        ) for (k, cluster) in enumerate(full_clusters)
    ]

    admissibility_verdict =
        !isempty(invalid_orders) ? "some_orders_excluded_by_invalid_density_no_unique_order" :
        length(full_clusters) == 1 ? "all_orders_confluent_single_survivor_class" :
        length(full_clusters) == length(full_orders) ? "all_orders_distinct_no_unique_admissible_order" :
        "small_admissible_output_classes_no_unique_canonical_order"

    max_pair_gap = maximum(pair_matrix)
    z3_real = z3_order_obstruction(max_pair_gap)
    z3_erased = z3_order_obstruction(0.0)

    anti_tautology = Dict(
        "flat_identity_substrate_no_effect" => flat_control,
        "commuting_pair_control_confluent" => commute_control,
        "noise_floor" => Dict(
            "value" => noise_floor,
            "classification_floor" => classification_floor,
            "definition" => "eps(Float64) * trace_scale(1) * depth(8) * safety(128); classification floor=max(1e-8,100000*noise_floor)",
        ),
        "input_dependence" => Dict(
            "order_mattering_pairs" => order_mattering_pairs,
            "input_dependent_pairs" => input_dependent_pairs,
            "all_order_mattering_pairs_input_dependent" => length(input_dependent_pairs) == length(order_mattering_pairs),
            "range_matrix" => range_matrix,
        ),
        "z3_verdict_flip" => Dict(
            "law" => "erased_or_commuting => measured_gap == 0",
            "measured_real_gap" => max_pair_gap,
            "real_verdict_expected_unsat" => z3_real,
            "erased_gap" => 0.0,
            "erased_verdict_expected_sat" => z3_erased,
            "flips" => (z3_real == "unsat" && z3_erased == "sat"),
        ),
    )

    R = Dict{String,Any}(
        "object_id" => "nesting_order_pairwise_confluence",
        "sim_id" => "nesting_order_pairwise_confluence",
        "name" => "Nested-Hopf noncommutative stacking-order pairwise/depth-3 confluence probe",
        "version" => "1.0",
        "classification" => "nesting_order_probe_poc",
        "promotion_allowed" => false,
        "script" => "layers/nesting_order_pairwise_confluence.jl",
        "result_path" => "layers/nesting_order_pairwise_confluence_results.json",
        "seed" => SEED,
        "n_rho" => length(rhos),
        "non_numpy" => true,
        "bloch_free" => true,
        "sim_execution_kind" => "nonclassical_poc",
        "sim_class" => "geometry_order_probe",
        "finite_map" => "For layer pair (A,B): rho |-> A-on-B = U_B Phi_A(U_B' rho U_B) U_B' and B-on-A = U_A Phi_B(U_A' rho U_A) U_A'; compare ||A-on-B - B-on-A||_1 over finite density probes. For stack order top->bottom, bottom acts bare and each upper channel is substrate-dressed by the frame directly below.",
        "domain" => "finite set of density operators rho in D(C^2); five genuine layer frames/channels {weyl_lr_gksl,s3_hopf_terrain,nested_hopf_tori_cell,clifford_rotor,frame_bundle_so3}",
        "codomain_or_output" => "pairwise order-difference matrix, depth-3 terminal confluence clusters, full-stack survivor classes, controls, Z3 verdict flip",
        "carrier_layer" => "density operators rho in D(C^2); SU(2) substrate frames from genuine Hopf/nested/Clifford/SO3/Weyl sources; no PEPS promotion claimed",
        "carrier_realization" => "Julia ComplexF64 2x2 density operators and CPTP channels; no NumPy; no Bloch-state readout",
        "peps3d_embedding" => "not_admitted_in_this_probe; finite density-operator/frame-conjugation scout only, downstream PEPS3D consumers blocked",
        "spinor_state" => "SU(2) frames built from genuine 2-spinors / spin double-cover frames; density probes include spinor-derived pure states mixed with I/2",
        "quaternion_action" => "SU(2) unit frames can be read as unit-quaternion actions; no stronger quaternion invariant is claimed",
        "dependency_receipts" => [
            joinpath(SOURCE_LAYER_DIR, "L7_layer_bf.jl"),
            joinpath(SOURCE_LAYER_DIR, "L10_layer_bf.jl"),
            joinpath(SOURCE_LAYER_DIR, "L11_layer_bf.jl"),
            joinpath(SOURCE_LAYER_DIR, "order_null_killtest.jl"),
            joinpath(SOURCE_LAYER_DIR, "substrate_effect_frame_conjugation.jl"),
            joinpath(SOURCE_LAYER_DIR, "substrate_effect_matched_band.jl"),
            joinpath(SOURCE_LAYER_DIR, "s3_hopf_spinor_network_entanglement.jl"),
            joinpath(SOURCE_LAYER_DIR, "nested_hopf_tori_spinor_network.jl"),
            joinpath(SOURCE_LAYER_DIR, "clifford_rotor_spinor_network_entanglement.jl"),
            joinpath(SOURCE_LAYER_DIR, "frame_bundle_so3_spinor_network.jl"),
            joinpath(SOURCE_LAYER_DIR, "weyl_lr_spinor_network_entanglement.jl"),
        ],
        "allowed_claims" => "Measures finite order structure and candidate survivor classes only.",
        "claim_ceiling" => "Does NOT assert the canonical nesting order; does NOT admit flux, twistor/d>=4 tie, unified manifold, bridge, Axis0, FEP, or physics. A surviving order/class is a candidate only.",
        "promotion_blockers" => [
            "no PEPS3D carrier admission in this scout",
            "no full-layer/G-structure/manifold evidence packet",
            "full-stack survivor class is observational, not canonical",
            "downstream consumers flux/Xi/Phi0/Axis0/bridge/physics blocked",
        ],
        "blocked_consumers" => ["flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "physics", "unified_manifold", "twistor_d_ge_4_tie"],
        "required_tools" => ["Julia LinearAlgebra", "JSON", "Z3"],
        "actual_tools_used" => ["LinearAlgebra", "Random", "Statistics", "JSON", "Z3"],
        "tool_manifest" => Dict(
            "LinearAlgebra" => "load-bearing density/operator norms, eigenspectrum health, matrix exponentials, SU(2) frames",
            "JSON" => "result emission",
            "Z3" => "load-bearing verdict flip for nonzero order gap vs erased/commuting law",
            "Random" => "finite randomized spinor-derived density probes",
            "Statistics" => "input-dependence range/std summaries",
        ),
        "tool_integration_depth" => Dict(
            "LinearAlgebra" => "load_bearing",
            "Z3" => "load_bearing",
            "JSON" => "supportive",
            "Random" => "supportive",
            "Statistics" => "supportive",
        ),
        "layer_labels" => labels,
        "layer_sources" => Dict(l.name => l.source for l in layers),
        "frame_diagnostics" => Dict(l.name => frame_diagnostics(l.frame) for l in layers),
        "pairwise_order_difference_matrix_max_trace_norm" => pair_matrix,
        "pairwise_order_difference_matrix_input_range" => range_matrix,
        "pairwise_order_stats" => pair_stats,
        "commuting_pairs_under_floor" => commuting_pairs,
        "order_mattering_pairs" => order_mattering_pairs,
        "depth3_confluence" => triple_reports,
        "full_stack_ordering" => Dict(
            "n_layers" => n,
            "n_total_orders" => length(full_orders),
            "n_survivor_classes" => length(full_clusters),
            "max_inter_order_gap" => full_max_gap,
            "survivor_classes" => full_cluster_payload,
            "invalid_density_orders_excluded" => invalid_orders,
            "orders_survive_as_candidates" => isempty(invalid_orders) ? length(full_orders) : length(full_orders) - length(invalid_orders),
        ),
        "admissibility" => Dict(
            "verdict" => admissibility_verdict,
            "unique_admissible_order_found" => false,
            "excluded_orders_by_inconsistency" => invalid_orders,
            "excluded_claims" => [
                "canonical_nesting_order",
                "stacking_readiness",
                "flux_unlock",
                "unified_manifold_admission",
            ],
            "surviving_candidate_classes" => length(full_clusters),
            "surviving_candidate_orders" => isempty(invalid_orders) ? length(full_orders) : length(full_orders) - length(invalid_orders),
        ),
        "anti_tautology" => anti_tautology,
        "promotion_status" => "diagnostic_only",
        "eligible_consumers" => ["next bounded nesting-order scout only"],
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, R, 2)
        write(io, "\n")
    end

    println("="^88)
    println("nesting_order_pairwise_confluence :: classification=nesting_order_probe_poc")
    println("promotion_allowed=false")
    println("claim_ceiling: measures finite order structure only; no canonical order / flux / bridge / manifold admission")
    println("result_path: $(RESULT_PATH)")
    println("="^88)
    println("layers: ", join(labels, ", "))
    @printf("noise_floor=%.3e classification_floor=%.3e\n", noise_floor, classification_floor)
    println()

    println("PAIRWISE ORDER-DIFFERENCE MATRIX max ||A-on-B - B-on-A||_1")
    print(rpad("", 28))
    for label in labels
        print(rpad(label[1:min(end, 20)], 24))
    end
    println()
    for i in 1:n
        print(rpad(labels[i][1:min(end, 26)], 28))
        for j in 1:n
            @printf("%-24.6e", pair_matrix[i, j])
        end
        println()
    end
    println()
    println("commuting pairs under floor: ", isempty(commuting_pairs) ? "none" : join(commuting_pairs, "; "))
    println("order-mattering pairs: ", isempty(order_mattering_pairs) ? "none" : join(order_mattering_pairs, "; "))
    println("input-dependent order-mattering pairs: ", isempty(input_dependent_pairs) ? "none" : join(input_dependent_pairs, "; "))
    println()

    println("DEPTH-3 CONFLUENCE")
    for trp in triple_reports
        @printf("  %-78s classes=%d max_gap=%.6e confluent=%s\n",
                join(trp["layers"], " | "),
                trp["n_survivor_classes"],
                trp["max_terminal_gap"],
                trp["confluent"])
    end
    println()

    println("FULL-STACK ADMISSIBILITY")
    println("  verdict: ", admissibility_verdict)
    println("  total_orders: ", length(full_orders))
    println("  survivor_classes: ", length(full_clusters))
    @printf("  max_inter_order_gap: %.6e\n", full_max_gap)
    println("  invalid_density_orders_excluded: ", length(invalid_orders))
    println("  unique_admissible_order_found: false")
    println()

    println("ANTI-TAUTOLOGY")
    @printf("  flat_identity_substrate_max=%.6e\n", flat_control["max"])
    @printf("  commuting_control_max=%.6e (%s)\n", commute_control["max"], commute_control["pair"])
    println("  all_order_mattering_pairs_input_dependent=", anti_tautology["input_dependence"]["all_order_mattering_pairs_input_dependent"])
    println("  z3 real_gap verdict=", z3_real, " ; erased verdict=", z3_erased, " ; flips=", anti_tautology["z3_verdict_flip"]["flips"])
    println("="^88)

    return R
end

main()
