#!/usr/bin/env julia

# carrier_n64_attack.jl
# classification = carrier_n64_poc ; promotion_allowed = false
#
# Narrow attack on the only failed V2 carrier rung:
#   system_v5/julia_carrier/layers/weyl_on_nested_hopf_tori_V2.jl
#
# Scope:
# - Reuse V2 shell etas, seed rotations, N=64 = shell cells, and ITensors-MPS
#   entropy readout.
# - Reproduce the original V2 chain carrier at N=64.
# - Try a nesting-aware shell-contiguous radial alternative that gives each
#   shell boundary explicit eta-bonds across corresponding shell sites.
# - Try a coarser-but-deeper ladder with the same eta band.
# - Decide only this bounded carrier question. This does not promote a layer,
#   manifold, bridge, flux, Axis0, FEP, or physics claim.

using Dates
using ITensors
using ITensorMPS
using JSON
using LinearAlgebra
using Statistics

ITensors.disable_warn_order()

const OBJECT_ID = "carrier_n64_attack"
const CLASSIFICATION = "carrier_n64_poc"
const PROMOTION_ALLOWED = false
const OUT = joinpath(@__DIR__, "carrier_n64_attack_results.json")
const V2_SOURCE = "system_v5/julia_carrier/layers/weyl_on_nested_hopf_tori_V2.jl"
const V2_RESULTS = "system_v5/julia_carrier/layers/weyl_on_nested_hopf_tori_V2_results.json"

const MAXDIM = 256
const CUTOFF = 1.0e-14
const FLOOR = 1.0e-3
const CONTROL_FLOOR = 1.0e-6
const ERROR_BOUND = CUTOFF * 1.0e3

const BASE_SHELL_ETAS = [pi / 10, pi / 6, pi / 5, pi / 4, 0.9, pi / 3, 1.2, 1.35]

function sanitize(x::Float64)
    return isfinite(x) ? x : "non_finite($x)"
end
sanitize(x::AbstractDict) = Dict(string(k) => sanitize(v) for (k, v) in x)
sanitize(x::AbstractVector) = [sanitize(v) for v in x]
sanitize(x) = x

site(k::Int, j::Int, n_s::Int) = (k - 1) * n_s + j

function v2_scaled_etas(K::Int)
    return [BASE_SHELL_ETAS[mod1(k, length(BASE_SHELL_ETAS))] * (1.0 + 0.01 * k) for k in 1:K]
end

function monotone_v2_band_etas(K::Int)
    v2 = v2_scaled_etas(16)
    return collect(range(minimum(v2), maximum(v2), length = K))
end

function shell_seed_rot(eta::Float64, chi::Int)
    theta = (0.3 + 1.2 * (2eta / pi)) + (chi == +1 ? 0.35 : -0.15)
    return ComplexF64[cos(theta / 2) -sin(theta / 2); sin(theta / 2) cos(theta / 2)]
end

function apply_shell_seed_rotations(psi::MPS, s, K::Int, n_s::Int, etas::Vector{Float64})
    half = n_s ÷ 2
    for k in 1:K, j in 1:n_s
        chi = j <= half ? -1 : +1
        rot = shell_seed_rot(etas[k], chi)
        psi = apply(ITensor(rot, prime(s[site(k, j, n_s)]), s[site(k, j, n_s)]), psi;
                    cutoff = CUTOFF, maxdim = MAXDIM)
    end
    return psi
end

function apply_within_shell_torus_phase(psi::MPS, s, K::Int, n_s::Int)
    for k in 1:K, j in 1:(n_s - 1)
        a = site(k, j, n_s)
        b = site(k, j + 1, n_s)
        psi = apply(op("H", s, a), psi; cutoff = CUTOFF, maxdim = MAXDIM)
        psi = apply(op("CNOT", s, a, b), psi; cutoff = CUTOFF, maxdim = MAXDIM)
    end
    return psi
end

function apply_v2_chain_eta_bonds(psi::MPS, s, K::Int, n_s::Int)
    for k in 1:(K - 1)
        ctrl = site(k, n_s, n_s)
        tgt = site(k + 1, 1, n_s)
        psi = apply(op("H", s, ctrl), psi; cutoff = CUTOFF, maxdim = MAXDIM)
        psi = apply(op("CNOT", s, ctrl, tgt), psi; cutoff = CUTOFF, maxdim = MAXDIM)
    end
    return psi
end

function apply_parallel_radial_eta_bonds(psi::MPS, s, K::Int, n_s::Int)
    for k in 1:(K - 1), j in 1:n_s
        ctrl = site(k, j, n_s)
        tgt = site(k + 1, j, n_s)
        psi = apply(op("H", s, ctrl), psi; cutoff = CUTOFF, maxdim = MAXDIM)
        psi = apply(op("CNOT", s, ctrl, tgt), psi; cutoff = CUTOFF, maxdim = MAXDIM)
    end
    return psi
end

function build_carrier(s, K::Int, n_s::Int, etas::Vector{Float64}; mode::Symbol, topology::Symbol)
    psi = MPS(s, "0")
    mode === :product && return psi

    psi = apply_shell_seed_rotations(psi, s, K, n_s, etas)

    if topology === :v2_chain
        psi = apply_within_shell_torus_phase(psi, s, K, n_s)
        mode === :nested && (psi = apply_v2_chain_eta_bonds(psi, s, K, n_s))
    elseif topology === :radial_parallel
        mode === :nested && (psi = apply_parallel_radial_eta_bonds(psi, s, K, n_s))
        psi = apply_within_shell_torus_phase(psi, s, K, n_s)
    else
        error("unknown topology: $topology")
    end

    normalize!(psi)
    return psi
end

function cut_entropy(psi_in::MPS, b::Int)
    psi = copy(psi_in)
    orthogonalize!(psi, b)
    U, S, V = b == 1 ? svd(psi[b], (siteind(psi, b),)) :
                       svd(psi[b], (linkind(psi, b - 1), siteind(psi, b)))
    entropy = 0.0
    for n in 1:dim(S, 1)
        p = real(S[n, n]^2)
        p > 1.0e-14 && (entropy -= p * log2(p))
    end
    return entropy
end

function linear_fit(xs::Vector{Float64}, ys::Vector{Float64})
    length(xs) < 2 && return Dict("available" => false, "reason" => "not_enough_points")
    X = hcat(xs, ones(length(xs)))
    coef = X \ ys
    yhat = X * coef
    ss_res = sum((ys .- yhat) .^ 2)
    ss_tot = sum((ys .- mean(ys)) .^ 2)
    r2 = ss_tot < 1.0e-18 ? 0.0 : 1.0 - ss_res / ss_tot
    return Dict("available" => true, "slope" => coef[1], "intercept" => coef[2], "r2" => r2)
end

function decay_law(entropies::Vector{Float64})
    xs = Float64[]
    ys = Float64[]
    for (i, e) in enumerate(entropies)
        if e > 0.0
            push!(xs, Float64(i))
            push!(ys, log(e))
        end
    end
    fit_all = linear_fit(xs, ys)

    tail_start = max(1, length(entropies) - 7)
    tx = Float64[]
    ty = Float64[]
    for i in tail_start:length(entropies)
        e = entropies[i]
        if e > 0.0
            push!(tx, Float64(i))
            push!(ty, log(e))
        end
    end
    fit_tail = linear_fit(tx, ty)
    return Dict("log_entropy_vs_boundary_all" => fit_all,
                "log_entropy_vs_boundary_tail" => fit_tail)
end

function carrier_variant(label::String, topology::Symbol, K::Int, n_s::Int, etas::Vector{Float64})
    N = K * n_s
    inter = [k * n_s for k in 1:(K - 1)]
    t0 = time()
    s = siteinds("Qubit", N)

    psi_nested = build_carrier(s, K, n_s, etas; mode = :nested, topology = topology)
    psi_flat = build_carrier(s, K, n_s, etas; mode = :flat, topology = topology)
    psi_product = build_carrier(s, K, n_s, etas; mode = :product, topology = topology)

    ent_nested = [cut_entropy(psi_nested, b) for b in inter]
    ent_flat = [cut_entropy(psi_flat, b) for b in inter]
    ent_product = [cut_entropy(psi_product, b) for b in inter]

    maxbond_nested = maxlinkdim(psi_nested)
    maxbond_flat = maxlinkdim(psi_flat)
    maxbond_product = maxlinkdim(psi_product)
    cap_clear = max(maxbond_nested, maxbond_flat, maxbond_product) < MAXDIM

    deepest_idx = argmin(ent_nested)
    deepest_entropy = ent_nested[deepest_idx]
    max_control = max(maximum(abs.(ent_flat)), maximum(abs.(ent_product)))
    controls_at_floor = max_control < CONTROL_FLOOR
    equal_truncation = true
    discarded_weight_nested = cap_clear ? 0.0 : "unknown_cap_hit"
    discarded_weight_flat = cap_clear ? 0.0 : "unknown_cap_hit"
    discarded_weight_product = cap_clear ? 0.0 : "unknown_cap_hit"
    error_bounded = cap_clear && deepest_entropy > ERROR_BOUND
    reliable = equal_truncation && controls_at_floor && error_bounded
    reaches_floor = reliable && deepest_entropy > FLOOR

    left_neighbor = deepest_idx > 1 ? ent_nested[deepest_idx - 1] : nothing
    right_neighbor = deepest_idx < length(ent_nested) ? ent_nested[deepest_idx + 1] : nothing
    local_node = deepest_entropy <= FLOOR &&
                 ((left_neighbor isa Float64 && left_neighbor > FLOOR) ||
                  (right_neighbor isa Float64 && right_neighbor > FLOOR))

    return Dict(
        "label" => label,
        "N" => N,
        "K" => K,
        "n_s" => n_s,
        "topology" => string(topology),
        "eta_ladder" => etas,
        "inter_shell_cuts" => inter,
        "ent_nested" => ent_nested,
        "ent_flat_control" => ent_flat,
        "ent_product_control" => ent_product,
        "min_inter_shell_entropy" => deepest_entropy,
        "max_inter_shell_entropy" => maximum(ent_nested),
        "deepest_cut_index" => deepest_idx,
        "deepest_cut_site" => inter[deepest_idx],
        "deepest_shell_pair" => [deepest_idx, deepest_idx + 1],
        "deepest_eta_pair" => [etas[deepest_idx], etas[deepest_idx + 1]],
        "deepest_left_neighbor_entropy" => left_neighbor,
        "deepest_right_neighbor_entropy" => right_neighbor,
        "deep_min_is_local_node_not_monotone_tail" => local_node,
        "max_flat_abs_control" => maximum(abs.(ent_flat)),
        "max_product_abs_control" => maximum(abs.(ent_product)),
        "max_control_abs" => max_control,
        "controls_at_floor" => controls_at_floor,
        "maxbond_nested" => maxbond_nested,
        "maxbond_flat_control" => maxbond_flat,
        "maxbond_product_control" => maxbond_product,
        "maxdim_cap" => MAXDIM,
        "cutoff" => CUTOFF,
        "equal_maxdim_cutoff_genuine_and_control" => equal_truncation,
        "discarded_weight_nested" => discarded_weight_nested,
        "discarded_weight_flat_control" => discarded_weight_flat,
        "discarded_weight_product_control" => discarded_weight_product,
        "discarded_weight_log_note" => cap_clear ?
            "maxlinkdim stayed below maxdim for genuine and controls; no cap truncation observed, logged discarded weight 0.0" :
            "maxlinkdim reached cap; discarded weight unavailable and carrier is not accepted as error-bounded",
        "cap_clear_no_observed_truncation" => cap_clear,
        "error_bound_floor" => ERROR_BOUND,
        "error_bounded_effect_gt_error" => error_bounded,
        "reliable_error_bounded_carrier" => reliable,
        "pre_registered_floor" => FLOOR,
        "n64_floor_pass" => reaches_floor,
        "decay_law" => decay_law(ent_nested),
        "wall_seconds" => round(time() - t0; digits = 3),
    )
end

println("carrier_n64_attack: classification=$CLASSIFICATION promotion_allowed=false")
println("source geometry: $V2_SOURCE")
println("maxdim=$MAXDIM cutoff=$CUTOFF floor=$FLOOR")

v2_etas = v2_scaled_etas(16)
variants = Dict{String,Any}()

println("[1/3] reproducing V2 N=64 chain carrier")
variants["v2_chain_reproduction"] =
    carrier_variant("v2_chain_reproduction", :v2_chain, 16, 4, v2_etas)

println("[2/3] running nesting-aware radial eta-bond carrier")
variants["radial_parallel_eta_bonds"] =
    carrier_variant("radial_parallel_eta_bonds", :radial_parallel, 16, 4, v2_etas)

println("[3/3] running coarser-but-deeper chain carrier")
variants["coarser_deeper_shell_ladder"] =
    carrier_variant("coarser_deeper_shell_ladder", :v2_chain, 32, 2, monotone_v2_band_etas(32))

reliable = [v for v in values(variants) if get(v, "reliable_error_bounded_carrier", false)]
reached = [v["label"] for v in reliable if get(v, "n64_floor_pass", false)]
decayed = [v["label"] for v in reliable if !get(v, "n64_floor_pass", false)]

verdict = if !isempty(reached)
    "n64_reached"
elseif !isempty(reliable) && length(decayed) == length(reliable)
    "n64_physical_decay"
else
    "mixed"
end

reading = if verdict == "n64_reached"
    "At least one reliable error-bounded alternative carrier keeps the N=64 deepest inter-shell cut above the pre-registered 1e-3 floor. The V2 N=64 miss is therefore carrier/topology-sensitive, not evidence that the nested geometry is physically weakly entangled at depth."
elseif verdict == "n64_physical_decay"
    "Every reliable error-bounded carrier tested keeps the deepest N=64 inter-shell cut below the 1e-3 floor. In this bounded attack, the decay reads as physical weak deep-nesting entanglement rather than an MPS carrier artifact."
else
    "The reliable carriers did not give a clean single reading; treat N=64 as mixed and do not promote."
end

scorecard = Dict(
    "verdict" => verdict,
    "reached_variants" => reached,
    "decayed_variants" => decayed,
    "n_reliable" => length(reliable),
    "best_min_inter_shell_entropy" => maximum([v["min_inter_shell_entropy"] for v in reliable]),
    "best_variant" => isempty(reliable) ? "none" :
        reliable[argmax([v["min_inter_shell_entropy"] for v in reliable])]["label"],
    "floor" => FLOOR,
    "reading" => reading,
)

result = Dict(
    "object_id" => OBJECT_ID,
    "sim_id" => OBJECT_ID,
    "name" => "N=64 carrier attack for V2 Weyl-on-nested-Hopf-tori carrier rung",
    "classification" => CLASSIFICATION,
    "promotion_allowed" => PROMOTION_ALLOWED,
    "generated_at" => string(Dates.now()),
    "source_geometry_reused" => Dict(
        "v2_source" => V2_SOURCE,
        "v2_results" => V2_RESULTS,
        "shell_etas_base" => BASE_SHELL_ETAS,
        "shell_seed_rot" => "theta=(0.3 + 1.2*(2eta/pi)) + chirality offset; same as V2",
        "v2_failed_number" => 0.00029669630197314435,
    ),
    "finite_map" => "N=64 finite shell-carrier graph and matched controls -> inter-shell Schmidt entropy spectrum, min-cut floor decision, discarded-weight/error-bound receipt.",
    "domain" => "Finite ITensors Qubit MPS carriers at N=64: V2 16x4 shell chain, radial 16x4 shell-contiguous eta-bond carrier, and coarser 32x2 shell ladder over the V2 eta band.",
    "codomain_or_output" => "Per-variant inter-shell entropy arrays, deepest cut, controls, max bond, discarded-weight log, reliable/error-bounded flag, and n64 verdict.",
    "root_constraints_in_force" => [
        "F01 finite carrier/probe/operator/path set: finite shell sites, finite H/CNOT/seed rotations, finite inter-shell cuts",
        "N01 order-sensitive operation/control: inter-shell eta-bond placement changes the finite contraction path and is compared against flat/product controls",
    ],
    "carrier_realization" => "Julia ITensors/ITensorMPS finite MPS; no CTMRG, no dense full-state closure, no NumPy.",
    "peps3d_embedding" => "not_admitted: this is a carrier attack on V2's exact MPS rung, not a PEPS3D manifold admission.",
    "spinor_state" => "V2 spinor-derived per-shell seed rotations reused; MPS qubit carrier read by Schmidt cuts.",
    "quaternion_action" => "not_applicable in this N=64 carrier attack; Hopf-shell eta geometry is reused but no quaternion claim is made.",
    "dependency_receipts" => [V2_SOURCE, V2_RESULTS],
    "downstream_blocks" => [
        "layer_completion",
        "manifold_admission",
        "stacking_readiness",
        "flux",
        "Xi",
        "Phi0",
        "Axis0",
        "FEP",
        "physics_gravity",
    ],
    "allowed_claims" => "Only the bounded N=64 carrier-artifact-vs-physical-decay verdict for this probe.",
    "promotion_blockers" => [
        "not PEPS3D-carried from first admitted finite step",
        "not a full layer or manifold admission packet",
        "alternative carrier changes eta-bond topology and must not be silently substituted into V2 claims",
    ],
    "tool_manifest" => Dict(
        "ITensors/ITensorMPS" => "load_bearing: builds finite MPS carriers and gives Schmidt cuts/max link dimensions",
        "LinearAlgebra" => "load_bearing: SVD-backed entropy readout through ITensors and small linear fits",
        "Statistics" => "supportive: log-entropy fit diagnostics",
        "JSON" => "supportive: durable result artifact",
    ),
    "tool_integration_depth" => Dict(
        "ITensors/ITensorMPS" => "load_bearing",
        "LinearAlgebra" => "load_bearing",
        "Statistics" => "supportive",
        "JSON" => "supportive",
    ),
    "classification_summary" => scorecard,
    "variants" => variants,
    "status_ladder" => "exists < runs < passes local rerun < canonical by process",
)

open(OUT, "w") do io
    JSON.print(io, sanitize(result), 2)
    write(io, "\n")
end

println("verdict=$verdict")
println("best_variant=", scorecard["best_variant"], " best_min=", scorecard["best_min_inter_shell_entropy"])
for key in sort(collect(keys(variants)))
    v = variants[key]
    println("  ", rpad(v["label"], 30),
            " min=", round(v["min_inter_shell_entropy"]; sigdigits = 6),
            " reliable=", v["reliable_error_bounded_carrier"],
            " floor_pass=", v["n64_floor_pass"],
            " maxbond=", v["maxbond_nested"])
end
println("wrote: $OUT")
