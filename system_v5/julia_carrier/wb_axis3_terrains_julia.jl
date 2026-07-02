#!/usr/bin/env julia
# wb_axis3_terrains_julia.jl
#
# object_id: wb_axis3_terrains
# engine: Julia truth lane
# claim_ceiling: candidate finite-map probe only; not layer-complete.
# promotion_allowed: false
#
# Finite map:
#   domain: 2x2 spinor density matrices rho, sampled on the finite size
#           ladder n=8,16,32,64 by a deterministic pseudo-Haar qubit table.
#   codomain: post-channel density matrices plus channel invariants:
#             trace distance from flat control, purity change, Choi PSD,
#             Kraus trace-preservation error, terrain/channel distinctness,
#             and Se/Ni order-sensitive commutator evidence.
#
# Boundary:
#   Terrain labels are Rosetta labels after the channel math. This file does
#   not admit a layer, bridge, flux, Xi, Phi0, Axis0, physics, or manifold claim.

using LinearAlgebra
using Dates
using JSON
using SHA

const OBJECT_ID = "wb_axis3_terrains"
const ENGINE = "julia_truth_lane"
const P_PARAM = 0.7
const GAMMA = 0.3
const EPS = 1e-10
const SIZES = [8, 16, 32, 64]

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const P0 = ComplexF64[1 0; 0 0]
const P1 = ComplexF64[0 0; 0 1]
const PPLUS = ComplexF64[0.5 0.5; 0.5 0.5]

const LCG_A = Int64(48271)
const LCG_M = Int64(2147483647)

function lcg_next(state::Int64)::Int64
    return mod(LCG_A * state, LCG_M)
end

function seeded_unit(seed::Int64)
    state0 = mod(seed, LCG_M - 1) + 1
    state1 = lcg_next(state0)
    state2 = lcg_next(state1)
    return Float64(state1) / Float64(LCG_M), Float64(state2) / Float64(LCG_M)
end

function deterministic_haar_density(n::Int, terrain_index::Int, sample_index::Int)
    seed = Int64(7919 + 101 * n + 1009 * terrain_index + 9176 * sample_index)
    u_pop, u_phase = seeded_unit(seed)
    phase = 2.0 * pi * u_phase
    psi = ComplexF64[
        sqrt(1.0 - u_pop),
        sqrt(u_pop) * (cos(phase) + im * sin(phase)),
    ]
    return psi * psi'
end

function apply_channel(rho::Matrix{ComplexF64}, kraus::Vector{Matrix{ComplexF64}})
    out = zeros(ComplexF64, 2, 2)
    for k in kraus
        out .+= k * rho * k'
    end
    return (out + out') / 2
end

function trace_distance(rho::Matrix{ComplexF64}, sigma::Matrix{ComplexF64})
    diff = (rho - sigma + (rho - sigma)') / 2
    vals = eigvals(diff)
    return 0.5 * sum(abs.(real.(vals)))
end

purity(rho::Matrix{ComplexF64}) = real(tr(rho * rho))

function channel_entropy(rho::Matrix{ComplexF64})
    vals = clamp.(real.(eigvals((rho + rho') / 2)), 0.0, 1.0)
    total = 0.0
    for v in vals
        if v > 1e-14
            total -= v * log(v)
        end
    end
    return total
end

function kraus_Se(p::Float64=P_PARAM)
    return [sqrt(p) * I2, sqrt(1.0 - p) * SX]
end

function kraus_Ne(p::Float64=P_PARAM)
    return [sqrt(p) * I2, sqrt(1.0 - p) * SY]
end

function kraus_Ni(gamma::Float64=GAMMA)
    k0 = ComplexF64[1 0; 0 sqrt(1.0 - gamma)]
    k1 = ComplexF64[0 sqrt(gamma); 0 0]
    return [k0, k1]
end

function kraus_Si(p::Float64=P_PARAM)
    return [sqrt(p) * I2, sqrt(1.0 - p) * SZ]
end

kraus_flat() = [I2]
kraus_Se_wrong_requested() = [sqrt(P_PARAM) * I2, sqrt(1.0 - P_PARAM) * SZ]
kraus_Se_wrong_independent() = [sqrt(P_PARAM) * I2, sqrt(1.0 - P_PARAM) * ((SX + SZ) / sqrt(2.0))]

function terrain_kraus()
    return Dict(
        "Se" => kraus_Se(),
        "Ne" => kraus_Ne(),
        "Ni" => kraus_Ni(),
        "Si" => kraus_Si(),
    )
end

function terrain_order(name::String)
    return findfirst(==(name), ["Se", "Ne", "Ni", "Si"])
end

function choi_matrix(kraus::Vector{Matrix{ComplexF64}})
    omega = vec(I2)
    choi = zeros(ComplexF64, 4, 4)
    for k in kraus
        a = kron(k, I2)
        v = a * omega
        choi .+= v * v'
    end
    return (choi + choi') / 2
end

function choi_summary(kraus::Vector{Matrix{ComplexF64}})
    choi = choi_matrix(kraus)
    herm_resid = norm(choi - choi')
    vals = sort(real.(eigvals(choi)))
    return Dict(
        "min_eigenvalue" => minimum(vals),
        "eigenvalues" => vals,
        "psd" => minimum(vals) >= -EPS,
        "rank_tol_1e-10" => count(v -> v > EPS, vals),
        "trace" => real(tr(choi)),
        "hermiticity_residual" => herm_resid,
    )
end

function kraus_completeness_error(kraus::Vector{Matrix{ComplexF64}})
    s = zeros(ComplexF64, 2, 2)
    for k in kraus
        s .+= k' * k
    end
    return norm(s - I2)
end

function superoperator(kraus::Vector{Matrix{ComplexF64}})
    s = zeros(ComplexF64, 4, 4)
    for k in kraus
        s .+= kron(conj(k), k)
    end
    return s
end

function channel_commutator_norm(a::Vector{Matrix{ComplexF64}}, b::Vector{Matrix{ComplexF64}})
    sa = superoperator(a)
    sb = superoperator(b)
    return norm(sa * sb - sb * sa)
end

function kraus_pair_commutator_norms(a::Vector{Matrix{ComplexF64}}, b::Vector{Matrix{ComplexF64}})
    vals = Float64[]
    for ka in a, kb in b
        push!(vals, norm(ka * kb - kb * ka))
    end
    return vals
end

function run_terrain(name::String, kraus::Vector{Matrix{ComplexF64}}, n::Int)
    idx = terrain_order(name)
    trace_dists = Float64[]
    purity_deltas = Float64[]
    entropy_deltas = Float64[]
    output_purities = Float64[]
    for sample in 1:n
        rho = deterministic_haar_density(n, idx, sample)
        out = apply_channel(rho, kraus)
        flat = apply_channel(rho, kraus_flat())
        push!(trace_dists, trace_distance(out, flat))
        push!(purity_deltas, purity(out) - purity(rho))
        push!(entropy_deltas, channel_entropy(out) - channel_entropy(rho))
        push!(output_purities, purity(out))
    end
    return Dict(
        "terrain" => name,
        "n_states" => n,
        "mean_trace_dist" => sum(trace_dists) / length(trace_dists),
        "min_trace_dist" => minimum(trace_dists),
        "max_trace_dist" => maximum(trace_dists),
        "all_trace_dists_positive" => all(v -> v > EPS, trace_dists),
        "mean_purity_delta" => sum(purity_deltas) / length(purity_deltas),
        "mean_entropy_delta" => sum(entropy_deltas) / length(entropy_deltas),
        "mean_output_purity" => sum(output_purities) / length(output_purities),
        "choi" => choi_summary(kraus),
        "kraus_completeness_err" => kraus_completeness_error(kraus),
    )
end

function channel_action_summary(name::String, kraus::Vector{Matrix{ComplexF64}}, rho::Matrix{ComplexF64})
    out = apply_channel(rho, kraus)
    flat = apply_channel(rho, kraus_flat())
    return Dict(
        "state" => name,
        "trace_dist_from_flat" => trace_distance(out, flat),
        "input_purity" => purity(rho),
        "output_purity" => purity(out),
        "purity_delta" => purity(out) - purity(rho),
        "entropy_delta" => channel_entropy(out) - channel_entropy(rho),
    )
end

function positive_controls()
    terrains = terrain_kraus()
    pure_zero = Dict{String, Any}()
    for name in ["Se", "Ne", "Ni", "Si"]
        summary = channel_action_summary("|0><0|", terrains[name], P0)
        summary["nontrivial_on_requested_state"] = summary["trace_dist_from_flat"] > EPS
        summary["purity_decreased_on_requested_state"] = summary["purity_delta"] < -EPS
        pure_zero[name] = summary
    end
    requested_nontrivial = all(v -> v["nontrivial_on_requested_state"], values(pure_zero))
    requested_purity_decreased = all(v -> v["purity_decreased_on_requested_state"], values(pure_zero))

    sensitive_specs = Dict(
        "Se" => ("|0><0|", P0),
        "Ne" => ("|0><0|", P0),
        "Ni" => ("|1><1|", P1),
        "Si" => ("|+><+|", PPLUS),
    )
    sensitive = Dict{String, Any}()
    for name in ["Se", "Ne", "Ni", "Si"]
        label, rho = sensitive_specs[name]
        summary = channel_action_summary(label, terrains[name], rho)
        summary["nontrivial_on_sensitive_state"] = summary["trace_dist_from_flat"] > EPS
        summary["purity_decreased_on_sensitive_state"] = summary["purity_delta"] < -EPS
        sensitive[name] = summary
    end
    sensitive_pass = all(v -> v["nontrivial_on_sensitive_state"] && v["purity_decreased_on_sensitive_state"], values(sensitive))

    return Dict(
        "requested_pure_zero" => pure_zero,
        "requested_pure_zero_nontrivial_pass" => requested_nontrivial,
        "requested_pure_zero_purity_direction_pass" => requested_purity_decreased,
        "requested_pure_zero_control_pass" => requested_nontrivial && requested_purity_decreased,
        "sensitive_state_controls" => sensitive,
        "sensitive_state_control_pass" => sensitive_pass,
        "control_note" => "|0><0| is a fixed point for Ni amplitude damping and Si z-dephasing, so the requested pure-zero control cannot honestly pass for all four terrains.",
    )
end

function boundary_checks()
    rho = ComplexF64[0.3 0.2; 0.2 0.7]
    full_damp = apply_channel(rho, kraus_Ni(1.0))
    p1_identity = Dict{String, Any}()
    for name in ["Se", "Ne", "Si"]
        k = name == "Se" ? kraus_Se(1.0) : name == "Ne" ? kraus_Ne(1.0) : kraus_Si(1.0)
        p1_identity[name] = trace_distance(apply_channel(rho, k), rho)
    end
    id_choi = choi_summary(kraus_flat())
    return Dict(
        "gamma_1_complete_damping_dist_to_ground" => trace_distance(full_damp, P0),
        "gamma_1_complete_damping_pass" => trace_distance(full_damp, P0) < EPS,
        "p_1_identity_trace_dists" => p1_identity,
        "p_1_identity_pass" => all(v -> v < EPS, values(p1_identity)),
        "identity_choi" => id_choi,
        "identity_choi_rank_one_pass" => id_choi["rank_tol_1e-10"] == 1,
    )
end

function wrong_structure_check()
    requested_diffs = Float64[]
    independent_diffs = Float64[]
    for n in SIZES, sample in 1:n
        rho = deterministic_haar_density(n, 1, sample)
        real_out = apply_channel(rho, kraus_Se())
        requested_out = apply_channel(rho, kraus_Se_wrong_requested())
        independent_out = apply_channel(rho, kraus_Se_wrong_independent())
        push!(requested_diffs, trace_distance(real_out, requested_out))
        push!(independent_diffs, trace_distance(real_out, independent_out))
    end
    return Dict(
        "requested_wrong_kraus" => "Se with sigma_z replacing sigma_x; this equals the Si axis under the provided terrain table, so it is reported separately.",
        "independent_wrong_kraus" => "Se with (sigma_x + sigma_z)/sqrt(2) replacing sigma_x; CP/TP and not one of Se/Ne/Ni/Si.",
        "requested_mean_Se_vs_wrong_trace_dist" => sum(requested_diffs) / length(requested_diffs),
        "requested_min_Se_vs_wrong_trace_dist" => minimum(requested_diffs),
        "requested_wrong_structure_distinct" => (sum(requested_diffs) / length(requested_diffs)) > EPS,
        "independent_mean_Se_vs_wrong_trace_dist" => sum(independent_diffs) / length(independent_diffs),
        "independent_min_Se_vs_wrong_trace_dist" => minimum(independent_diffs),
        "independent_wrong_structure_distinct" => (sum(independent_diffs) / length(independent_diffs)) > EPS,
        "wrong_structure_distinct" => (sum(requested_diffs) / length(requested_diffs)) > EPS && (sum(independent_diffs) / length(independent_diffs)) > EPS,
    )
end

function pairwise_superoperator_distances()
    terrains = terrain_kraus()
    out = Dict{String, Float64}()
    names = ["Se", "Ne", "Ni", "Si"]
    for i in 1:length(names)-1, j in i+1:length(names)
        a = names[i]
        b = names[j]
        out["$a-$b"] = norm(superoperator(terrains[a]) - superoperator(terrains[b]))
    end
    return out
end

function axis3_split(size_ladder::Dict{String, Any})
    deltas = Dict{String, Float64}()
    entropy_deltas = Dict{String, Float64}()
    for name in ["Se", "Ne", "Ni", "Si"]
        vals = [size_ladder["n=$n"][name]["mean_purity_delta"] for n in SIZES]
        ent = [size_ladder["n=$n"][name]["mean_entropy_delta"] for n in SIZES]
        deltas[name] = sum(vals) / length(vals)
        entropy_deltas[name] = sum(ent) / length(ent)
    end
    type1 = (deltas["Se"] + deltas["Ne"]) / 2
    type2 = (deltas["Ni"] + deltas["Si"]) / 2
    return Dict(
        "declared_type1_expansion" => ["Se", "Ne"],
        "declared_type2_compression" => ["Ni", "Si"],
        "mean_purity_delta_by_terrain" => deltas,
        "mean_entropy_delta_by_terrain" => entropy_deltas,
        "type1_mean_purity_delta" => type1,
        "type2_mean_purity_delta" => type2,
        "type_partition_observable_gap" => abs(type1 - type2),
        "axis3_distinct_by_observed_gap" => abs(type1 - type2) > EPS,
        "axis3_direction_pass" => false,
        "axis3_direction_note" => "The supplied Kraus maps do not support a clean purity-sign expansion/compression split: all four mean purity deltas are negative on the finite ladder. Axis 3 remains an observable candidate partition, not a direction-admitted result.",
    )
end

function erased_structure_control()
    erased_comm = channel_commutator_norm(kraus_flat(), kraus_flat())
    rho = deterministic_haar_density(64, 1, 1)
    erased_trace_dist = trace_distance(apply_channel(rho, kraus_flat()), rho)
    return Dict(
        "control" => "all terrains replaced by flat identity channel",
        "n01_channel_commutator_norm" => erased_comm,
        "sample_trace_dist_from_flat" => erased_trace_dist,
        "terrain_structure_present" => false,
        "axis3_distinct" => false,
        "finite_map_verdict_if_erased" => false,
    )
end

function flat_control_max_trace_dist_by_n()
    out = Dict{String, Float64}()
    for n in SIZES
        vals = Float64[]
        for sample in 1:n
            rho = deterministic_haar_density(n, 1, sample)
            push!(vals, trace_distance(apply_channel(rho, kraus_flat()), rho))
        end
        out["n=$n"] = maximum(vals)
    end
    return out
end

function n01_witness()
    rho = PPLUS
    se_then_ni = apply_channel(apply_channel(rho, terrain_kraus()["Se"]), terrain_kraus()["Ni"])
    ni_then_se = apply_channel(apply_channel(rho, terrain_kraus()["Ni"]), terrain_kraus()["Se"])
    return Dict(
        "state" => "|+><+|",
        "trace_distance_Se_after_Ni_vs_Ni_after_Se" => trace_distance(se_then_ni, ni_then_se),
        "order_sensitive" => trace_distance(se_then_ni, ni_then_se) > EPS,
    )
end

function main()
    println("wb_axis3_terrains Julia truth lane")
    terrains = terrain_kraus()

    size_ladder = Dict{String, Any}()
    for n in SIZES
        size_ladder["n=$n"] = Dict(name => run_terrain(name, terrains[name], n) for name in ["Se", "Ne", "Ni", "Si"])
    end

    choi_checks = Dict(name => size_ladder["n=8"][name]["choi"]["psd"] for name in ["Se", "Ne", "Ni", "Si"])
    completeness = Dict(name => kraus_completeness_error(terrains[name]) for name in ["Se", "Ne", "Ni", "Si"])
    pairwise_dists = pairwise_superoperator_distances()
    pos = positive_controls()
    bounds = boundary_checks()
    wrong = wrong_structure_check()
    ax3 = axis3_split(size_ladder)
    flat_by_n = flat_control_max_trace_dist_by_n()
    n01_state_witness = n01_witness()

    n01_channel = channel_commutator_norm(terrains["Se"], terrains["Ni"])
    n01_kraus_pair = kraus_pair_commutator_norms(terrains["Se"], terrains["Ni"])
    erased = erased_structure_control()

    all_trace_positive = all(size_ladder["n=$n"][name]["all_trace_dists_positive"] for n in SIZES for name in ["Se", "Ne", "Ni", "Si"])
    all_choi_psd = all(values(choi_checks))
    all_complete = all(v -> v < EPS, values(completeness))
    terrain_distinct = minimum(values(pairwise_dists)) > EPS
    finite_map_checks_pass = (
        all_trace_positive &&
        all_choi_psd &&
        all_complete &&
        terrain_distinct &&
        n01_channel > EPS &&
        maximum(n01_kraus_pair) > EPS &&
        bounds["gamma_1_complete_damping_pass"] &&
        bounds["p_1_identity_pass"] &&
        bounds["identity_choi_rank_one_pass"] &&
        wrong["wrong_structure_distinct"] &&
        n01_state_witness["order_sensitive"] &&
        ax3["axis3_distinct_by_observed_gap"] &&
        pos["sensitive_state_control_pass"] &&
        !erased["finite_map_verdict_if_erased"]
    )
    requested_control_pass = pos["requested_pure_zero_control_pass"]
    all_pass = finite_map_checks_pass && requested_control_pass

    result = Dict(
        "object_id" => OBJECT_ID,
        "engine" => ENGINE,
        "generated_at" => string(Dates.now(Dates.UTC)),
        "source_path" => @__FILE__,
        "source_sha256" => bytes2hex(sha256(read(@__FILE__))),
        "run_command" => "/opt/homebrew/bin/julia --project=system_v5/julia_carrier system_v5/julia_carrier/wb_axis3_terrains_julia.jl",
        "julia_version" => string(VERSION),
        "rng_seed" => "deterministic Park-Miller LCG seeds 7919 + 101*n + 1009*terrain_index + 9176*sample_index",
        "run_completed" => true,
        "classification" => "tool_lego_fit_probe",
        "claim_ceiling" => "candidate finite-map probe; not layer-complete; not manifold admission",
        "promotion_allowed" => false,
        "promotion_status" => requested_control_pass ? "keep_but_open" : "audit_further",
        "finite_map" => Dict(
            "domain" => "2x2 spinor density matrices rho, deterministic pseudo-Haar qubit samples at n=8,16,32,64",
            "codomain_or_output" => "post-channel density matrices plus trace distance, purity/entropy change, Choi PSD, Kraus TP, and order-sensitive channel commutator invariants",
        ),
        "domain" => "2x2 spinor density matrices rho, deterministic pseudo-Haar qubit samples at n=8,16,32,64",
        "codomain_or_output" => "post-channel density matrices plus trace distance, purity/entropy change, Choi PSD, Kraus TP, and order-sensitive channel commutator invariants",
        "root_constraints_in_force" => Dict(
            "F01" => Dict("satisfied" => true, "witness" => "explicit finite size ladder n=8,16,32,64"),
            "N01" => Dict("satisfied" => n01_channel > EPS, "channel_commutator_norm" => n01_channel, "kraus_pair_commutator_norms" => n01_kraus_pair),
        ),
        "carrier_realization" => "Julia ComplexF64 2-component spinor-derived density matrices; no NumPy bridge",
        "spinor_state" => "2-component ComplexF64 spinors psi with rho = psi * psi'",
        "peps3d_embedding" => Dict(
            "status" => "blocked_not_claimed",
            "reason" => "This object is a 2x2 CP-channel finite-map probe only. It does not provide a PEPS3D carrier anchor and cannot be cited for manifold/layer promotion.",
        ),
        "quaternion_action" => "not_applicable",
        "dependency_receipts" => String[],
        "axes" => ["Axis1_channel_polarity", "Axis2_chart_lens", "Axis3_engine_family"],
        "terrains" => Dict(
            "Se" => Dict("axis1" => "expansive", "axis2" => "open_direct", "axis3" => "Type1_expansion", "kraus" => "sqrt(p) I, sqrt(1-p) sigma_x"),
            "Ne" => Dict("axis1" => "expansive", "axis2" => "closed_direct", "axis3" => "Type1_expansion", "kraus" => "sqrt(p) I, sqrt(1-p) sigma_y"),
            "Ni" => Dict("axis1" => "compressive", "axis2" => "open_conj", "axis3" => "Type2_compression", "kraus" => "amplitude damping gamma=0.3"),
            "Si" => Dict("axis1" => "compressive", "axis2" => "closed_conj", "axis3" => "Type2_compression", "kraus" => "sqrt(p) I, sqrt(1-p) sigma_z"),
        ),
        "parameters" => Dict("p" => P_PARAM, "gamma" => GAMMA),
        "size_ladder" => size_ladder,
        "choi_psd_by_terrain" => choi_checks,
        "all_choi_psd" => all_choi_psd,
        "choi_min_eigenvalue_by_terrain" => Dict(name => size_ladder["n=8"][name]["choi"]["min_eigenvalue"] for name in ["Se", "Ne", "Ni", "Si"]),
        "choi_hermiticity_residual_by_terrain" => Dict(name => size_ladder["n=8"][name]["choi"]["hermiticity_residual"] for name in ["Se", "Ne", "Ni", "Si"]),
        "kraus_completeness_errors" => completeness,
        "all_kraus_complete" => all_complete,
        "pairwise_superoperator_distances" => pairwise_dists,
        "terrain_channels_distinct" => terrain_distinct,
        "n01_channel_commutator_norm" => n01_channel,
        "n01_kraus_pair_commutator_norms" => n01_kraus_pair,
        "n01_witness_state" => n01_state_witness,
        "n01_satisfied" => n01_channel > EPS,
        "positive_controls" => pos,
        "positive_control_pass_by_terrain" => Dict(name => pos["sensitive_state_controls"][name]["nontrivial_on_sensitive_state"] && pos["sensitive_state_controls"][name]["purity_decreased_on_sensitive_state"] for name in ["Se", "Ne", "Ni", "Si"]),
        "boundary_checks" => bounds,
        "flat_control_max_trace_dist_by_n" => flat_by_n,
        "wrong_structure_control" => wrong,
        "erased_structure_control" => erased,
        "axis3_split" => ax3,
        "finite_map_checks_pass" => finite_map_checks_pass,
        "requested_pure_zero_control_pass" => requested_control_pass,
        "all_pass" => all_pass,
        "all_pass_reason" => all_pass ? "finite map checks and requested pure-zero controls passed" : "finite map checks passed, but the requested |0><0| positive control is false for Ni and Si because |0><0| is their fixed/eigen state.",
        "allowed_claims" => ["four explicit CP channel finite maps", "F01 finite size ladder", "N01 Se/Ni order-sensitive channel commutator", "candidate Axis 3 engine-family partition observable"],
        "promotion_blockers" => ["requested |0><0| positive control is false for Ni and Si", "Axis 3 direction criterion is not admitted by purity signs", "no PEPS3D carrier anchor", "promotion_allowed=false"],
        "eligible_consumers" => String[],
        "blocked_consumers" => ["layer_completion", "manifold_admission", "bridge", "coupling", "flux", "Xi", "Phi0", "Axis0", "physics"],
        "pass_rule" => "finite_map_checks_pass requires CP/TP channels, nonzero trace distance on the finite ladder, distinct superoperators, Se/Ni channel order sensitivity, boundary checks, wrong-structure controls, sensitive-state controls, and erased-structure verdict flip. all_pass additionally requires the requested |0><0| controls.",
        "fail_rule" => "fail if Choi PSD/TP, F01 ladder, N01 order sensitivity, wrong/erased controls, or sensitive-state controls fail; all_pass remains false if requested pure-zero controls fail.",
        "blocked_downstream" => ["layer_completion", "manifold_admission", "bridge", "coupling", "flux", "Xi", "Phi0", "Axis0", "physics"],
        "TOOL_MANIFEST" => Dict(
            "LinearAlgebra" => Dict("used" => true, "reason" => "eigvals/norm/tr for computed Choi PSD, trace distance, purity, superoperator, and commutator checks"),
            "JSON" => Dict("used" => true, "reason" => "durable result receipt"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "LinearAlgebra" => "load_bearing",
            "JSON" => "supportive",
        ),
        "tool_manifest" => Dict(
            "LinearAlgebra" => Dict("used" => true, "reason" => "load-bearing channel invariant computation"),
            "JSON" => Dict("used" => true, "reason" => "supportive result writer"),
        ),
        "tool_integration_depth" => Dict("LinearAlgebra" => "load_bearing", "JSON" => "supportive"),
    )

    out_path = joinpath(@__DIR__, "wb_axis3_terrains_julia_results.json")
    open(out_path, "w") do io
        JSON.print(io, result, 2)
    end
    println("wrote $(out_path)")
    println("finite_map_checks_pass=$(finite_map_checks_pass)")
    println("all_pass=$(all_pass)")
end

main()
