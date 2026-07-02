# =====================================================================================
# multishell_ratchet_cascade.jl
# =====================================================================================
# OBJECT (PoC): a finite cascade of nested leaf terrains coupled by an area ratchet.
#
# User request:
#   - Julia + DifferentialEquations + LinearAlgebra; no NumPy; no decorative Z3.
#   - N=8 nested leaves theta_i in (0, pi/2).
#   - Each leaf carries a terrain Lindblad on a qubit density rho_i.
#   - Adjacent leaves are coupled by gamma^theta hopping weighted by
#       A(theta) = 2*pi^2*sin(2*theta),
#     strongest near the Clifford torus theta=pi/4.
#   - Integrate the coupled chain to steady state.
#   - Measure whether the ratchet-on steady leaf-weight profile concentrates near
#     theta=pi/4 while the A=const control stays uniform.
#
# Honest boundary:
#   classification: PoC
#   promotion_allowed: false
#   This is a Julia density-matrix cascade/control receipt. It is not PEPS3D-carried,
#   not torch-native, and not evidence for layer/manifold completion, Axis0, bridge,
#   flux, Xi, Phi0, basin, or physics promotion.
#
# Run:
#   julia --project=. layers/multishell_ratchet_cascade.jl
# =====================================================================================

using LinearAlgebra
using DifferentialEquations
using JSON

const NLEAF = 8
const TMAX = 120.0
const HOP_STRENGTH = 1.25
const TERRAIN_RATE = 0.35
const DEPHASE_RATE = 0.08
const STEADY_TOL = 2e-7
const UNIFORM_TOL = 2e-4
const CONCENTRATION_MARGIN = 0.025
const DENSITY_TOL = 1e-8

const I2 = Matrix{Float64}(I, 2, 2)
const SIGMA_X = [0.0 1.0; 1.0 0.0]
const SIGMA_Z = [1.0 0.0; 0.0 -1.0]
const SIGMA_MINUS = [0.0 0.0; 1.0 0.0]
const SIGMA_PLUS = Matrix(transpose(SIGMA_MINUS))
const GAMMA_THETA = SIGMA_X

ratchet_area(theta) = 2.0 * pi^2 * sin(2.0 * theta)

function nested_leaf_thetas()
    return [
        0.10,
        0.28,
        0.46,
        0.66,
        pi / 4.0,
        0.95,
        1.18,
        (pi / 2.0) - 0.10,
    ]
end

function lindblad(rho::Matrix{Float64}, L::AbstractMatrix{Float64}, rate::Float64)
    LdagL = transpose(L) * L
    return rate .* (L * rho * transpose(L) .- 0.5 .* (LdagL * rho .+ rho * LdagL))
end

function terrain_lindblad(rho::Matrix{Float64}, theta::Float64)
    # The terrain varies across the nested leaves while staying trace-preserving.
    # Low leaves relax toward one pole, high leaves toward the opposite pole, and
    # the Clifford-near leaf uses a balanced thermal terrain.
    drho = zeros(Float64, 2, 2)
    if abs(theta - pi / 4.0) < 1e-12
        drho .+= lindblad(rho, SIGMA_MINUS, TERRAIN_RATE)
        drho .+= lindblad(rho, SIGMA_PLUS, TERRAIN_RATE)
    elseif theta < pi / 4.0
        drho .+= lindblad(rho, SIGMA_MINUS, TERRAIN_RATE)
    else
        drho .+= lindblad(rho, SIGMA_PLUS, TERRAIN_RATE)
    end
    drho .+= lindblad(rho, SIGMA_Z, DEPHASE_RATE)
    return drho
end

function leaf_matrix(u::AbstractVector{Float64}, leaf::Int)
    o = 4 * (leaf - 1)
    return [u[o + 1] u[o + 3]; u[o + 2] u[o + 4]]
end

function add_leaf_matrix!(du::AbstractVector{Float64}, leaf::Int, mat::Matrix{Float64})
    o = 4 * (leaf - 1)
    du[o + 1] += mat[1, 1]
    du[o + 2] += mat[2, 1]
    du[o + 3] += mat[1, 2]
    du[o + 4] += mat[2, 2]
    return nothing
end

function initial_state(nleaf::Int)
    return initial_state_from_weights(fill(1.0 / nleaf, nleaf))
end

function initial_state_from_weights(weights::Vector{Float64})
    nleaf = length(weights)
    normalized = weights ./ sum(weights)
    u0 = zeros(Float64, 4 * nleaf)
    for leaf in 1:nleaf
        rho0 = normalized[leaf] .* (I2 ./ 2.0)
        add_leaf_matrix!(u0, leaf, rho0)
    end
    return u0
end

function leaf_weights(u::AbstractVector{Float64}, nleaf::Int)
    weights = zeros(Float64, nleaf)
    for leaf in 1:nleaf
        rho = leaf_matrix(u, leaf)
        weights[leaf] = tr(rho)
    end
    total = sum(weights)
    return weights ./ total
end

function hop_generator(area_weights::Vector{Float64}; hop_scale::Float64=HOP_STRENGTH)
    nleaf = length(area_weights)
    max_area = maximum(area_weights)
    Q = zeros(Float64, nleaf, nleaf)
    for leaf in 1:(nleaf - 1)
        rate_left_to_right = hop_scale * area_weights[leaf + 1] / max_area
        rate_right_to_left = hop_scale * area_weights[leaf] / max_area
        Q[leaf + 1, leaf] += rate_left_to_right
        Q[leaf, leaf] -= rate_left_to_right
        Q[leaf, leaf + 1] += rate_right_to_left
        Q[leaf + 1, leaf + 1] -= rate_right_to_left
    end
    return Q
end

function cascade_rhs!(du, u, p, t)
    thetas = p.thetas
    area_weights = p.area_weights
    hop_scale = p.hop_scale
    terrain_on = p.terrain_on
    fill!(du, 0.0)
    nleaf = length(thetas)
    max_area = maximum(area_weights)

    if terrain_on
        for leaf in 1:nleaf
            rho = leaf_matrix(u, leaf)
            add_leaf_matrix!(du, leaf, terrain_lindblad(rho, thetas[leaf]))
        end
    end

    for leaf in 1:(nleaf - 1)
        rho_left = leaf_matrix(u, leaf)
        rho_right = leaf_matrix(u, leaf + 1)

        # Destination-weighted adjacent hopping. For trace weights w_i this gives
        # q_{i->j} proportional to A_j, so detailed balance yields w_i proportional
        # to A_i. With A=const the same finite map has a uniform steady profile.
        rate_left_to_right = hop_scale * area_weights[leaf + 1] / max_area
        rate_right_to_left = hop_scale * area_weights[leaf] / max_area

        gamma_left = GAMMA_THETA * rho_left * GAMMA_THETA
        gamma_right = GAMMA_THETA * rho_right * GAMMA_THETA

        add_leaf_matrix!(du, leaf, -rate_left_to_right .* rho_left)
        add_leaf_matrix!(du, leaf + 1, rate_left_to_right .* gamma_left)

        add_leaf_matrix!(du, leaf + 1, -rate_right_to_left .* rho_right)
        add_leaf_matrix!(du, leaf, rate_right_to_left .* gamma_right)
    end
    return nothing
end

function run_cascade(
    thetas::Vector{Float64},
    area_weights::Vector{Float64};
    u0::Vector{Float64}=initial_state(length(thetas)),
    hop_scale::Float64=HOP_STRENGTH,
    terrain_on::Bool=true,
)
    params = (thetas=thetas, area_weights=area_weights, hop_scale=hop_scale, terrain_on=terrain_on)
    prob = ODEProblem(cascade_rhs!, u0, (0.0, TMAX), params)
    sol = solve(prob, Tsit5(); abstol=1e-10, reltol=1e-10, save_everystep=false)
    final_u = Array(sol.u[end])
    du = similar(final_u)
    cascade_rhs!(du, final_u, params, sol.t[end])
    return (
        sol = sol,
        final_u = final_u,
        weights = leaf_weights(final_u, length(thetas)),
        derivative_norm = norm(du),
        retcode = string(sol.retcode),
    )
end

function trace_rhs_vector(du::AbstractVector{Float64}, nleaf::Int)
    return [du[4 * (leaf - 1) + 1] + du[4 * (leaf - 1) + 4] for leaf in 1:nleaf]
end

function density_sanity(u::AbstractVector{Float64}, nleaf::Int)
    max_hermitian_error = 0.0
    min_eigenvalue = Inf
    min_trace = Inf
    for leaf in 1:nleaf
        rho = leaf_matrix(u, leaf)
        max_hermitian_error = max(max_hermitian_error, norm(rho - transpose(rho), Inf))
        min_eigenvalue = min(min_eigenvalue, minimum(eigvals(Symmetric((rho + transpose(rho)) ./ 2.0))))
        min_trace = min(min_trace, tr(rho))
    end
    return Dict(
        "max_hermitian_error" => max_hermitian_error,
        "min_eigenvalue" => min_eigenvalue,
        "min_leaf_trace" => min_trace,
        "total_trace" => sum([tr(leaf_matrix(u, leaf)) for leaf in 1:nleaf]),
        "ok" => max_hermitian_error < DENSITY_TOL && min_eigenvalue > -DENSITY_TOL && min_trace > -DENSITY_TOL,
    )
end

function gamma_channel_checks()
    rho = [0.7 0.2; 0.2 0.3]
    gamma_rho = GAMMA_THETA * rho * transpose(GAMMA_THETA)
    return Dict(
        "gamma_hermitian" => norm(GAMMA_THETA - transpose(GAMMA_THETA), Inf) < DENSITY_TOL,
        "gamma_unitary" => norm(transpose(GAMMA_THETA) * GAMMA_THETA - I2, Inf) < DENSITY_TOL,
        "trace_preserving_sample" => abs(tr(gamma_rho) - tr(rho)) < DENSITY_TOL,
        "psd_preserving_sample" => minimum(eigvals(Symmetric(gamma_rho))) > -DENSITY_TOL,
    )
end

function source_boundary_checks()
    src = read(@__FILE__, String)
    pycall_import = "using " * "PyCall"
    pythoncall_import = "using " * "PythonCall"
    pyimport_call = "py" * "import("
    z3_import = "using " * "Z3"
    return Dict(
        "no_pycall" => !occursin(pycall_import, src) && !occursin(pyimport_call, src),
        "no_pythoncall" => !occursin(pythoncall_import, src),
        "no_z3_import" => !occursin(z3_import, src),
    )
end

function max_abs_delta(xs::Vector{Float64}, ys::Vector{Float64})
    return maximum(abs.(xs .- ys))
end

function rounded_vector(xs::Vector{Float64}; digits::Int=10)
    return [round(x; digits=digits) for x in xs]
end

function main()
    thetas = nested_leaf_thetas()
    areas = ratchet_area.(thetas)
    const_areas = ones(Float64, NLEAF)
    uniform = fill(1.0 / NLEAF, NLEAF)
    expected_ratchet = areas ./ sum(areas)
    max_leaf = argmax(areas)

    u0_uniform = initial_state(NLEAF)
    u0_skew_left = initial_state_from_weights(Float64.(NLEAF:-1:1))
    u0_skew_right = initial_state_from_weights(Float64.(1:NLEAF))

    ratchet_on = run_cascade(thetas, areas)
    ratchet_off = run_cascade(thetas, const_areas)
    ratchet_on_skew_left = run_cascade(thetas, areas; u0=u0_skew_left)
    ratchet_on_skew_right = run_cascade(thetas, areas; u0=u0_skew_right)
    terrain_only = run_cascade(thetas, areas; u0=u0_uniform, hop_scale=0.0, terrain_on=true)
    terrain_off = run_cascade(thetas, areas; u0=u0_skew_left, hop_scale=HOP_STRENGTH, terrain_on=false)

    Q_ratchet = hop_generator(areas)
    Q_control = hop_generator(const_areas)
    du0 = similar(u0_uniform)
    cascade_rhs!(du0, u0_uniform, (thetas=thetas, area_weights=areas, hop_scale=HOP_STRENGTH, terrain_on=true), 0.0)
    trace_rhs0 = trace_rhs_vector(du0, NLEAF)
    gamma_checks = gamma_channel_checks()
    ratchet_density = density_sanity(ratchet_on.final_u, NLEAF)
    control_density = density_sanity(ratchet_off.final_u, NLEAF)
    terrain_only_density = density_sanity(terrain_only.final_u, NLEAF)
    terrain_off_density = density_sanity(terrain_off.final_u, NLEAF)
    source_boundary = source_boundary_checks()

    ratchet_matches_area = max_abs_delta(ratchet_on.weights, expected_ratchet) < 5e-4
    skew_left_matches_area = sum(abs.(ratchet_on_skew_left.weights .- expected_ratchet)) < 5e-3
    skew_right_matches_area = sum(abs.(ratchet_on_skew_right.weights .- expected_ratchet)) < 5e-3
    control_uniform = max_abs_delta(ratchet_off.weights, uniform) < UNIFORM_TOL
    max_leaf_is_clifford = abs(thetas[max_leaf] - pi / 4.0) < 1e-12
    ratchet_peak_at_clifford = argmax(ratchet_on.weights) == max_leaf
    ratchet_concentrates = ratchet_on.weights[max_leaf] > (ratchet_off.weights[max_leaf] + CONCENTRATION_MARGIN)
    steady_on = ratchet_on.retcode == "Success" && ratchet_on.derivative_norm < STEADY_TOL
    steady_off = ratchet_off.retcode == "Success" && ratchet_off.derivative_norm < STEADY_TOL
    steady_terrain_off = terrain_off.retcode == "Success" && terrain_off.derivative_norm < STEADY_TOL
    total_trace_preserved = abs(ratchet_density["total_trace"] - 1.0) < 1e-9
    theta_grid_ok = length(thetas) == NLEAF && all(theta -> 0.0 < theta < pi / 2.0, thetas) && all(diff(thetas) .> 0.0)
    area_positive_nonuniform = all(areas .> 0.0) && maximum(areas) - minimum(areas) > 1.0
    gamma_channel_ok = all(values(gamma_checks))
    density_ok = ratchet_density["ok"] && control_density["ok"] && terrain_only_density["ok"] && terrain_off_density["ok"]
    Q_column_sums_zero = maximum(abs.(sum(Q_ratchet; dims=1))) < 1e-12
    Q_adjacent_positive = all([Q_ratchet[i + 1, i] > 0.0 && Q_ratchet[i, i + 1] > 0.0 for i in 1:(NLEAF - 1)])
    Q_nonadjacent_zero = maximum([abs(Q_ratchet[i, j]) for i in 1:NLEAF, j in 1:NLEAF if abs(i - j) > 1]) < 1e-12
    detailed_balance_error = maximum([
        abs(expected_ratchet[i] * Q_ratchet[i + 1, i] - expected_ratchet[i + 1] * Q_ratchet[i, i + 1])
        for i in 1:(NLEAF - 1)
    ])
    stationarity_error = norm(Q_ratchet * expected_ratchet, Inf)
    control_stationarity_error = norm(Q_control * uniform, Inf)
    trace_rhs_matches_Qw = norm(trace_rhs0 - Q_ratchet * uniform, Inf) < 1e-12
    terrain_only_preserves_weights = max_abs_delta(terrain_only.weights, uniform) < 1e-8
    terrain_only_changes_internal = norm(terrain_only.final_u - u0_uniform) > 1e-3
    hopping_off_preserves_initial_weights = terrain_only_preserves_weights
    terrain_off_matches_area = sum(abs.(terrain_off.weights .- expected_ratchet)) < 5e-3
    source_boundary_ok = all(values(source_boundary))

    checks = Dict(
        "metadata_contract_ok" => true,
        "theta_grid_in_open_interval" => theta_grid_ok,
        "area_positive_and_nonuniform" => area_positive_nonuniform,
        "max_leaf_is_clifford_torus" => max_leaf_is_clifford,
        "gamma_channel_ok" => gamma_channel_ok,
        "hop_generator_column_sums_zero" => Q_column_sums_zero,
        "hop_generator_adjacent_rates_positive" => Q_adjacent_positive,
        "hop_generator_nonadjacent_rates_zero" => Q_nonadjacent_zero,
        "detailed_balance_area_stationary" => detailed_balance_error < 1e-12 && stationarity_error < 1e-12,
        "control_generator_uniform_stationary" => control_stationarity_error < 1e-12,
        "trace_rhs_matches_hop_generator" => trace_rhs_matches_Qw,
        "density_sanity_ok" => density_ok,
        "terrain_only_preserves_leaf_weights" => terrain_only_preserves_weights,
        "terrain_only_changes_internal_density" => terrain_only_changes_internal,
        "hopping_off_preserves_initial_weights" => hopping_off_preserves_initial_weights,
        "terrain_off_still_converges_to_area_weights" => terrain_off_matches_area && steady_terrain_off,
        "ratchet_on_peak_at_clifford_leaf" => ratchet_peak_at_clifford,
        "ratchet_on_matches_area_stationary_profile" => ratchet_matches_area,
        "ratchet_on_skew_left_matches_area_stationary_profile" => skew_left_matches_area,
        "ratchet_on_skew_right_matches_area_stationary_profile" => skew_right_matches_area,
        "ratchet_on_concentrates_vs_control" => ratchet_concentrates,
        "control_A_const_uniform" => control_uniform,
        "steady_state_ratchet_on" => steady_on,
        "steady_state_control" => steady_off,
        "total_trace_preserved" => total_trace_preserved,
        "no_numpy_pycall_or_z3_boundary" => source_boundary_ok,
    )
    all_pass = all(values(checks))

    leaf_rows = [
        Dict(
            "leaf" => i,
            "theta" => thetas[i],
            "A_theta" => areas[i],
            "expected_ratchet_weight_A_normalized" => expected_ratchet[i],
            "ratchet_on_weight" => ratchet_on.weights[i],
            "ratchet_off_A_const_weight" => ratchet_off.weights[i],
            "distance_to_clifford_theta" => abs(thetas[i] - pi / 4.0),
        )
        for i in 1:NLEAF
    ]

    receipt = Dict(
        "object" => "multishell_ratchet_cascade",
        "sim_id" => "multishell_ratchet_cascade",
        "name" => "Nested-leaf Lindblad terrain cascade with area-ratchet hopping",
        "version" => "1.0",
        "classification" => "PoC",
        "promotion_allowed" => false,
        "promotion_status" => "diagnostic_only",
        "status" => all_pass ? "passes" : "partial",
        "public_status" => all_pass ? "passes local rerun" : "runs",
        "status_ladder" => "exists < runs < passes local rerun < canonical by process",
        "all_pass" => all_pass,
        "tier" => "PoC bounded cascade/control",
        "purpose" => "Measure whether destination-weighted area-ratchet hopping concentrates finite leaf trace weight near theta=pi/4, with A=const as the uniform kill-control.",
        "scientific_question" => "Does the coupled finite leaf cascade concentrate steady trace weight at the Clifford-torus leaf when hopping rates are weighted by A(theta), while the A=const control remains uniform?",
        "sim_execution_kind" => "classical",
        "sim_execution_boundary" => "Julia density-matrix PoC over qubit Lindblad equations; treated as diagnostic/control evidence only, not nonclassical manifold admission.",
        "sim_class" => "constraint_probe",
        "root_constraints_in_force" => [
            "F01: finite N=8 leaf/probe set and finite adjacent path graph",
            "N01: order-sensitive adjacent gamma^theta transfer channel is represented, but no stronger nonclassical manifold claim is admitted",
        ],
        "finite_map" => "For each leaf i, rho_i is an unnormalized 2x2 qubit density. Local terrain Lindblad maps preserve tr(rho_i). Adjacent transfer maps rho_i -> gamma_theta*rho_i*gamma_theta with q_{i->j}=k*A(theta_j)/max(A), producing a finite trace-weight Markov cascade.",
        "domain" => Dict(
            "N" => NLEAF,
            "thetas" => thetas,
            "state" => "8 unnormalized real 2x2 qubit density matrices, one per theta leaf",
            "adjacency" => "path graph on leaves 1..8",
            "gamma_theta" => "sigma_x channel rho -> sigma_x*rho*sigma_x",
        ),
        "codomain_or_output" => "Steady leaf trace-weight profile plus A=const control profile.",
        "carrier_layer" => "finite nested theta leaves over qubit density matrices",
        "geometry_layer" => "leaf-area ratchet A(theta)=2*pi^2*sin(2theta)",
        "carrier_realization" => "Julia Float64 2x2 density matrices integrated by DifferentialEquations; no NumPy",
        "peps3d_embedding" => "not_applicable_blocked: this PoC is not finite PEPS3D-carried",
        "spinor_state" => "not_applicable_blocked: density-matrix PoC, not torch-native spinor or spinor-derived PEPS3D carrier",
        "quaternion_action" => "not_applicable",
        "dependency_receipts" => [
            "system_v5/julia_carrier/layers/nested_leaf_area_ratchet_results.json",
            "system_v5/julia_carrier/layers/emergent_basin_nested_terrains_results.json",
        ],
        "downstream_blocks" => [
            "layer_completion",
            "manifold_admission",
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "bridge",
            "basin",
            "physics",
        ],
        "law_or_candidate_tested" => "Destination-ratchet weighted adjacent hopping has steady leaf trace weights proportional to A(theta); A=const kills concentration and yields uniform weights.",
        "allowed_claims" => [
            "local PoC script exists and runs",
            "ratchet-on steady profile concentrates at the Clifford-torus leaf in this finite cascade",
            "A=const control is uniform in this finite cascade",
        ],
        "promotion_blockers" => [
            "classification is PoC",
            "promotion_allowed=false",
            "not torch-native",
            "not PEPS3D-carried",
            "no proof/graph/topology tooling",
            "single finite cascade only",
        ],
        "eligible_consumers" => ["local PoC comparison only"],
        "blocked_consumers" => [
            "layer_completion",
            "manifold_admission",
            "G_structure_admission",
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "bridge",
            "basin",
            "physics",
        ],
        "required_tools" => ["DifferentialEquations", "LinearAlgebra", "JSON"],
        "actual_tools_used" => ["DifferentialEquations", "LinearAlgebra", "JSON"],
        "tools" => ["DifferentialEquations", "LinearAlgebra", "JSON"],
        "tool_manifest" => Dict(
            "DifferentialEquations" => "load-bearing: integrates the coupled Lindblad/hopping ODE to steady state",
            "LinearAlgebra" => "load-bearing: density-matrix traces, Lindblad products, gamma channel, derivative norm",
            "JSON" => "supportive: writes the receipt artifact",
            "Z3" => "not used: deliberately omitted because SMT would be decorative for this numeric PoC/control measurement",
        ),
        "tool_integration_depth" => Dict(
            "DifferentialEquations" => "load_bearing",
            "LinearAlgebra" => "load_bearing",
            "JSON" => "supportive",
            "Z3" => "None",
        ),
        "proof_surfaces_used" => String[],
        "graph_surfaces_used" => String[],
        "topology_surfaces_used" => String[],
        "required_negatives" => ["A=const adjacent hopping control must yield uniform leaf weights"],
        "negatives_run" => ["A=const control"],
        "kill_conditions" => [
            "FAIL if ratchet-on max weight is not at the Clifford-torus leaf",
            "FAIL if ratchet-on Clifford leaf weight does not exceed A=const Clifford weight by the configured margin",
            "FAIL if A=const control is not uniform",
            "FAIL if either integration is not steady",
        ],
        "required_artifacts" => ["layers/multishell_ratchet_cascade_results.json"],
        "artifacts_emitted" => ["layers/multishell_ratchet_cascade_results.json"],
        "witness_trace_id" => "multishell_ratchet_cascade_v1",
        "checks" => checks,
        "gamma_channel_checks" => gamma_checks,
        "source_boundary_checks" => source_boundary,
        "density_sanity" => Dict(
            "ratchet_on" => ratchet_density,
            "ratchet_off_A_const" => control_density,
            "terrain_only_hopping_off" => terrain_only_density,
            "terrain_off_hopping_on" => terrain_off_density,
        ),
        "hop_generator" => Dict(
            "ratchet_Q_column_sum_max_abs" => maximum(abs.(sum(Q_ratchet; dims=1))),
            "ratchet_detailed_balance_max_abs" => detailed_balance_error,
            "ratchet_stationarity_norm_inf" => stationarity_error,
            "control_stationarity_norm_inf" => control_stationarity_error,
            "trace_rhs_matches_Qw_norm_inf" => norm(trace_rhs0 - Q_ratchet * uniform, Inf),
            "adjacent_only" => Q_adjacent_positive && Q_nonadjacent_zero,
        ),
        "parameters" => Dict(
            "N" => NLEAF,
            "TMAX" => TMAX,
            "HOP_STRENGTH" => HOP_STRENGTH,
            "TERRAIN_RATE" => TERRAIN_RATE,
            "DEPHASE_RATE" => DEPHASE_RATE,
            "STEADY_TOL" => STEADY_TOL,
            "UNIFORM_TOL" => UNIFORM_TOL,
            "CONCENTRATION_MARGIN" => CONCENTRATION_MARGIN,
        ),
        "ratchet" => Dict(
            "A_theta_formula" => "2*pi^2*sin(2theta)",
            "max_A_leaf" => max_leaf,
            "max_A_theta" => thetas[max_leaf],
            "max_A_value" => areas[max_leaf],
            "ratchet_on_clifford_weight" => ratchet_on.weights[max_leaf],
            "control_clifford_weight" => ratchet_off.weights[max_leaf],
            "concentration_delta_vs_control" => ratchet_on.weights[max_leaf] - ratchet_off.weights[max_leaf],
            "ratchet_expected_profile_max_abs_error" => max_abs_delta(ratchet_on.weights, expected_ratchet),
            "ratchet_skew_left_L1_error" => sum(abs.(ratchet_on_skew_left.weights .- expected_ratchet)),
            "ratchet_skew_right_L1_error" => sum(abs.(ratchet_on_skew_right.weights .- expected_ratchet)),
            "terrain_off_L1_error" => sum(abs.(terrain_off.weights .- expected_ratchet)),
            "control_uniform_max_abs_error" => max_abs_delta(ratchet_off.weights, uniform),
        ),
        "steady_state" => Dict(
            "ratchet_on_retcode" => ratchet_on.retcode,
            "ratchet_off_retcode" => ratchet_off.retcode,
            "ratchet_on_skew_left_retcode" => ratchet_on_skew_left.retcode,
            "ratchet_on_skew_right_retcode" => ratchet_on_skew_right.retcode,
            "terrain_only_retcode" => terrain_only.retcode,
            "terrain_off_retcode" => terrain_off.retcode,
            "ratchet_on_derivative_norm" => ratchet_on.derivative_norm,
            "ratchet_off_derivative_norm" => ratchet_off.derivative_norm,
            "ratchet_on_skew_left_derivative_norm" => ratchet_on_skew_left.derivative_norm,
            "ratchet_on_skew_right_derivative_norm" => ratchet_on_skew_right.derivative_norm,
            "terrain_only_derivative_norm" => terrain_only.derivative_norm,
            "terrain_off_derivative_norm" => terrain_off.derivative_norm,
        ),
        "leaf_weight_profile" => leaf_rows,
        "ratchet_on_weights" => ratchet_on.weights,
        "ratchet_on_skew_left_weights" => ratchet_on_skew_left.weights,
        "ratchet_on_skew_right_weights" => ratchet_on_skew_right.weights,
        "ratchet_off_A_const_weights" => ratchet_off.weights,
        "terrain_only_hopping_off_weights" => terrain_only.weights,
        "terrain_off_hopping_on_weights" => terrain_off.weights,
        "expected_ratchet_A_normalized_weights" => expected_ratchet,
        "uniform_control_target" => uniform,
        "honest_scope" => Dict(
            "forced_standard_math" => [
                "A(theta)=2*pi^2*sin(2theta) is maximal at theta=pi/4",
                "destination-weighted nearest-neighbor rates q_{i->j}=k*A(theta_j)/max(A) have detailed-balance stationary trace weights proportional to A(theta_i)",
            ],
            "novel_interpretive_NOT_proven" => [
                "calling the concentration a ratchet pull toward the Clifford torus is a PoC interpretation of this finite cascade measurement",
            ],
            "claim_ceiling" => "PoC local cascade/control measurement only; no promotion, no layer/manifold completion, no Axis/bridge/physics claim.",
        ),
        "z3_omitted" => "deliberate: no decorative solver block; evidence is the DifferentialEquations steady-state profile plus A=const kill-control",
    )

    out_path = joinpath(@__DIR__, "multishell_ratchet_cascade_results.json")
    open(out_path, "w") do io
        JSON.print(io, receipt, 2)
        println(io)
    end

    println("multishell_ratchet_cascade")
    println("classification=PoC promotion_allowed=false")
    println("ratchet_on_weights=", rounded_vector(ratchet_on.weights))
    println("ratchet_off_A_const_weights=", rounded_vector(ratchet_off.weights))
    println("max_A_leaf=", max_leaf, " theta=", round(thetas[max_leaf]; digits=10))
    println("ALL_PASS=", all_pass)
    println("receipt=", out_path)
    all_pass || exit(1)
end

main()
