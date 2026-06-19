#!/usr/bin/env julia
# object_id: engine_noncollapse_probe
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "engine_noncollapse_probe"
const RESULT_PATH = joinpath(@__DIR__, "engine_noncollapse_probe_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "engine_noncollapse_probe_jax_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const DISTINCT_TOL = 1.0e-5
const DT = 0.002
const STAGE_STEPS = 90
const TERRAIN_STEPS = 360
const PIT_SOURCE_STEPS = 4200

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SM = ComplexF64[0 0; 1 0]
const SP = ComplexF64[0 1; 0 0]
const P_UP = ComplexF64[1 0; 0 0]
const P_DN = ComplexF64[0 0; 0 1]
const N_GENERIC = normalize(Float64[0.37, -0.51, 0.78])
const H0 = N_GENERIC[1] .* SX .+ N_GENERIC[2] .* SY .+ N_GENERIC[3] .* SZ
const HC = 0.63 .* SZ
const EPS_F = 0.17
const EPS_V = 0.08
const EPS_P = 0.05
const GAMMA_F_Z = 0.46
const GAMMA_F_X = 0.19
const GAMMA_P = 2.35
const KAPPA_UP = 0.37
const KAPPA_DN = 0.23
const L_SHARED = [sqrt(GAMMA_F_Z) .* SZ, sqrt(GAMMA_F_X) .* SX]
const L_PIT = sqrt(GAMMA_P) .* SM
const L_SOURCE = sqrt(GAMMA_P) .* SP
const PROJECTORS = [P_UP, P_DN]
const KAPPAS = [KAPPA_UP, KAPPA_DN]

dag(m) = m'
comm(h, rho) = h * rho - rho * h

function bool_scalar(x::Bool)
    x ? 1.0 : 0.0
end

function vec_payload(v)
    [Float64(x) for x in v]
end

function density_from_bloch(r::Vector{Float64})
    0.5 .* (I2 .+ r[1] .* SX .+ r[2] .* SY .+ r[3] .* SZ)
end

function bloch_z(rho)
    Float64(real(tr(rho * SZ)))
end

function project_density(rho)
    rho_h = (rho + dag(rho)) ./ 2.0
    ev = eigen(Hermitian(rho_h))
    vals = max.(ev.values, 0.0)
    total = sum(vals)
    if total <= 1.0e-15
        return I2 ./ 2.0
    end
    rho_p = ev.vectors * Diagonal(vals) * dag(ev.vectors)
    rho_p = (rho_p + dag(rho_p)) ./ 2.0
    rho_p ./ real(tr(rho_p))
end

function dissipator(l, rho)
    ldl = dag(l) * l
    l * rho * dag(l) .- 0.5 .* (ldl * rho + rho * ldl)
end

function sum_dissipators(ls, rho)
    out = zeros(ComplexF64, 2, 2)
    for l in ls
        out .+= dissipator(l, rho)
    end
    out
end

function dephase_generator(rho)
    out = zeros(ComplexF64, 2, 2)
    for idx in eachindex(PROJECTORS)
        p = PROJECTORS[idx]
        kappa = KAPPAS[idx]
        out .+= kappa .* (p * rho * p .- 0.5 .* (p * rho + rho * p))
    end
    out
end

function comm_coeff(engine::String, no_flip_control::Bool)
    if no_flip_control || engine == "type1"
        return -im
    end
    im
end

function terrain_generator(terrain::String, engine::String, rho; no_flip_control::Bool=false)
    c = comm_coeff(engine, no_flip_control)
    if terrain == "Funnel" || terrain == "Cannon"
        return sum_dissipators(L_SHARED, rho) .+ c .* EPS_F .* comm(H0, rho)
    elseif terrain == "Vortex" || terrain == "Spiral"
        return c .* comm(H0, rho) .+ EPS_V .* sum_dissipators(L_SHARED, rho)
    elseif terrain == "Pit" || terrain == "Source"
        l_p = (terrain == "Source" && !no_flip_control) ? L_SOURCE : L_PIT
        return dissipator(l_p, rho) .+ c .* EPS_P .* comm(H0, rho)
    elseif terrain == "Hill" || terrain == "Citadel"
        return c .* comm(HC, rho) .+ dephase_generator(rho)
    end
    error("unknown terrain: $(terrain)")
end

function rk4_step(rho, terrain::String, engine::String; no_flip_control::Bool=false)
    f(x) = terrain_generator(terrain, engine, x; no_flip_control=no_flip_control)
    k1 = f(rho)
    k2 = f(rho .+ 0.5 .* DT .* k1)
    k3 = f(rho .+ 0.5 .* DT .* k2)
    k4 = f(rho .+ DT .* k3)
    project_density(rho .+ (DT / 6.0) .* (k1 .+ 2.0 .* k2 .+ 2.0 .* k3 .+ k4))
end

function integrate_terrain(terrain::String, engine::String, rho0; steps::Int, no_flip_control::Bool=false)
    rho = copy(rho0)
    for _ in 1:steps
        rho = rk4_step(rho, terrain, engine; no_flip_control=no_flip_control)
    end
    rho
end

function trace_distance(a, b)
    vals = eigvals(Hermitian((a - b + dag(a - b)) ./ 2.0))
    0.5 * sum(abs.(vals))
end

function placement_rows(engine::String)
    if engine == "type1"
        return [
            Dict("loop" => "inner", "terrain" => "Funnel", "grammar_label" => "win"),
            Dict("loop" => "inner", "terrain" => "Vortex", "grammar_label" => "lose"),
            Dict("loop" => "inner", "terrain" => "Pit", "grammar_label" => "lose"),
            Dict("loop" => "inner", "terrain" => "Hill", "grammar_label" => "win"),
            Dict("loop" => "outer", "terrain" => "Funnel", "grammar_label" => "LOSE"),
            Dict("loop" => "outer", "terrain" => "Vortex", "grammar_label" => "WIN"),
            Dict("loop" => "outer", "terrain" => "Pit", "grammar_label" => "LOSE"),
            Dict("loop" => "outer", "terrain" => "Hill", "grammar_label" => "WIN"),
        ]
    end
    [
        Dict("loop" => "inner", "terrain" => "Cannon", "grammar_label" => "lose"),
        Dict("loop" => "inner", "terrain" => "Spiral", "grammar_label" => "win"),
        Dict("loop" => "inner", "terrain" => "Source", "grammar_label" => "lose"),
        Dict("loop" => "inner", "terrain" => "Citadel", "grammar_label" => "win"),
        Dict("loop" => "outer", "terrain" => "Cannon", "grammar_label" => "WIN"),
        Dict("loop" => "outer", "terrain" => "Spiral", "grammar_label" => "LOSE"),
        Dict("loop" => "outer", "terrain" => "Source", "grammar_label" => "LOSE"),
        Dict("loop" => "outer", "terrain" => "Citadel", "grammar_label" => "WIN"),
    ]
end

function run_engine(engine::String, rho0; no_flip_control::Bool=false)
    rho = copy(rho0)
    states = [copy(rho)]
    rows = placement_rows(engine)
    for row in rows
        rho = integrate_terrain(row["terrain"], engine, rho; steps=STAGE_STEPS, no_flip_control=no_flip_control)
        push!(states, copy(rho))
    end
    states
end

function trajectory_metrics(a, b)
    distances = [trace_distance(a[idx], b[idx]) for idx in eachindex(a)]
    Dict{String,Any}(
        "max_trace_distance" => Float64(maximum(distances)),
        "terminal_trace_distance" => Float64(distances[end]),
        "per_state_trace_distances" => [Float64(x) for x in distances],
    )
end

function terrain_pairwise(engine::String, rho0)
    terrains = [row["terrain"] for row in placement_rows(engine)[1:4]]
    terminals = Dict(t => integrate_terrain(t, engine, rho0; steps=TERRAIN_STEPS) for t in terrains)
    pair_distances = Dict{String,Any}()
    min_distance = Inf
    for i in 1:length(terrains)-1
        for j in i+1:length(terrains)
            key = "$(terrains[i])__$(terrains[j])"
            dist = trace_distance(terminals[terrains[i]], terminals[terrains[j]])
            pair_distances[key] = Float64(dist)
            min_distance = min(min_distance, dist)
        end
    end
    Dict{String,Any}(
        "terrains" => terrains,
        "pair_distances" => pair_distances,
        "min_pairwise_trace_distance" => Float64(min_distance),
        "all_pairwise_distinct" => min_distance > DISTINCT_TOL,
    )
end

function grammar_balance()
    out = Dict{String,Any}()
    for engine in ["type1", "type2"]
        rows = placement_rows(engine)
        outer = [r["grammar_label"] for r in rows if r["loop"] == "outer"]
        inner = [r["grammar_label"] for r in rows if r["loop"] == "inner"]
        out[engine] = Dict(
            "outer_WIN" => count(==("WIN"), outer),
            "outer_LOSE" => count(==("LOSE"), outer),
            "inner_win" => count(==("win"), inner),
            "inner_lose" => count(==("lose"), inner),
            "balanced" => count(==("WIN"), outer) == 2 &&
                count(==("LOSE"), outer) == 2 &&
                count(==("win"), inner) == 2 &&
                count(==("lose"), inner) == 2,
        )
    end
    out
end

function parity_block(result::Dict{String,Any})
    if !isfile(JAX_REFERENCE_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_REFERENCE_PATH,
            "peer_available" => false,
            "parity_max_diff" => nothing,
            "worst_key" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => false,
            "missing_from_peer" => collect(keys(result["shared_scalars"])),
            "missing_from_self" => String[],
            "diffs" => Dict{String,Any}(),
            "stop_condition_fired" => false,
            "status" => "pending_peer",
        )
    end

    peer = JSON.parsefile(JAX_REFERENCE_PATH)
    self_scalars = result["shared_scalars"]
    peer_scalars = peer["shared_scalars"]
    missing_from_peer = sort(setdiff(collect(keys(self_scalars)), collect(keys(peer_scalars))))
    missing_from_self = sort(setdiff(collect(keys(peer_scalars)), collect(keys(self_scalars))))
    diffs = Dict{String,Any}()
    max_diff = 0.0
    worst_key = ""

    for (key, value) in self_scalars
        if haskey(peer_scalars, key)
            diff = abs(Float64(value) - Float64(peer_scalars[key]))
            diffs[key] = diff
            if diff > max_diff
                max_diff = diff
                worst_key = key
            end
        end
    end

    within = isempty(missing_from_peer) && isempty(missing_from_self) && max_diff < TOL
    strict_divergence = max_diff > STRICT_STOP_TOL
    Dict{String,Any}(
        "peer_result_path" => JAX_REFERENCE_PATH,
        "peer_available" => true,
        "parity_max_diff" => Float64(max_diff),
        "worst_key" => worst_key,
        "within_1e_9" => within,
        "strict_divergence_gt_1e_6" => strict_divergence,
        "missing_from_peer" => missing_from_peer,
        "missing_from_self" => missing_from_self,
        "diffs" => diffs,
        "stop_condition_fired" => strict_divergence,
        "status" => within ? "pass" : "fail_closed",
    )
end

function build_result()
    rho0 = density_from_bloch(Float64[0.23, -0.31, 0.17])
    type1 = run_engine("type1", rho0)
    type2 = run_engine("type2", rho0)
    no_flip_type1 = run_engine("type1", rho0; no_flip_control=true)
    no_flip_type2 = run_engine("type2", rho0; no_flip_control=true)
    flip_metrics = trajectory_metrics(type1, type2)
    no_flip_metrics = trajectory_metrics(no_flip_type1, no_flip_type2)

    type1_terrain = terrain_pairwise("type1", rho0)
    type2_terrain = terrain_pairwise("type2", rho0)
    balances = grammar_balance()

    pit_terminal = integrate_terrain("Pit", "type1", rho0; steps=PIT_SOURCE_STEPS)
    source_terminal = integrate_terrain("Source", "type2", rho0; steps=PIT_SOURCE_STEPS)
    pit_z = bloch_z(pit_terminal)
    source_z = bloch_z(source_terminal)

    verdicts = Dict{String,Any}(
        "engines_distinct_under_flip" => flip_metrics["max_trace_distance"] > DISTINCT_TOL,
        "collapse_under_no_flip_control" => no_flip_metrics["max_trace_distance"] <= TOL,
        "four_terrains_distinct_per_engine" =>
            (type1_terrain["all_pairwise_distinct"]::Bool) && (type2_terrain["all_pairwise_distinct"]::Bool),
        "outcomes_balanced_grammar" =>
            (balances["type1"]["balanced"]::Bool) && (balances["type2"]["balanced"]::Bool),
        "pit_source_opposite_z_flow" => pit_z < -0.5 && source_z > 0.5,
    )
    verdicts["owner_noncollapse_supported"] =
        (verdicts["engines_distinct_under_flip"]::Bool) &&
        (verdicts["collapse_under_no_flip_control"]::Bool) &&
        (verdicts["pit_source_opposite_z_flow"]::Bool)

    shared_scalars = Dict{String,Any}(
        "c1_flip_trajectory_max_trace_distance" => Float64(flip_metrics["max_trace_distance"]),
        "c1_flip_terminal_trace_distance" => Float64(flip_metrics["terminal_trace_distance"]),
        "c1_no_flip_control_max_trace_distance" => Float64(no_flip_metrics["max_trace_distance"]),
        "c1_no_flip_control_terminal_trace_distance" => Float64(no_flip_metrics["terminal_trace_distance"]),
        "c2_type1_min_pairwise_terrain_trace_distance" => Float64(type1_terrain["min_pairwise_trace_distance"]),
        "c2_type2_min_pairwise_terrain_trace_distance" => Float64(type2_terrain["min_pairwise_trace_distance"]),
        "c3_type1_outer_WIN_count" => Float64(balances["type1"]["outer_WIN"]),
        "c3_type1_outer_LOSE_count" => Float64(balances["type1"]["outer_LOSE"]),
        "c3_type1_inner_win_count" => Float64(balances["type1"]["inner_win"]),
        "c3_type1_inner_lose_count" => Float64(balances["type1"]["inner_lose"]),
        "c3_type2_outer_WIN_count" => Float64(balances["type2"]["outer_WIN"]),
        "c3_type2_outer_LOSE_count" => Float64(balances["type2"]["outer_LOSE"]),
        "c3_type2_inner_win_count" => Float64(balances["type2"]["inner_win"]),
        "c3_type2_inner_lose_count" => Float64(balances["type2"]["inner_lose"]),
        "c4_type1_pit_terminal_z" => Float64(pit_z),
        "c4_type2_source_terminal_z" => Float64(source_z),
        "c4_pit_source_z_sum" => Float64(pit_z + source_z),
        "engine_stage_placements_per_engine" => 8.0,
        "engine_total_stage_placements" => 16.0,
        "verdict_engines_distinct_under_flip" => bool_scalar(verdicts["engines_distinct_under_flip"]::Bool),
        "verdict_collapse_under_no_flip_control" => bool_scalar(verdicts["collapse_under_no_flip_control"]::Bool),
        "verdict_four_terrains_distinct_per_engine" => bool_scalar(verdicts["four_terrains_distinct_per_engine"]::Bool),
        "verdict_outcomes_balanced_grammar" => bool_scalar(verdicts["outcomes_balanced_grammar"]::Bool),
        "verdict_pit_source_opposite_z_flow" => bool_scalar(verdicts["pit_source_opposite_z_flow"]::Bool),
        "verdict_owner_noncollapse_supported" => bool_scalar(verdicts["owner_noncollapse_supported"]::Bool),
        "stage_grammar_dynamics_claim_flag" => 0.0,
        "numpy_compute_used_flag" => 0.0,
    )

    tool_manifest = Dict(
        "Julia LinearAlgebra" => Dict(
            "tried" => true,
            "used" => true,
            "role" => "reference_exact_native_linearalgebra",
            "reason" => "load-bearing for native density-matrix Lindblad/RK4 evolution, PSD projection, trace distances, eigenvalue checks, and JSON result scalars",
        ),
        "JAX jax.numpy x64" => Dict(
            "tried" => true,
            "used" => false,
            "role" => "peer_mirror_expected",
            "reason" => "supportive peer parity lane read from its result JSON when present; no JAX compute is used inside Julia",
        ),
    )
    tool_depth = Dict(
        "Julia LinearAlgebra" => "load_bearing",
        "JAX jax.numpy x64" => "supportive",
    )

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia",
        "backend_roles" => Dict(
            "julia" => "reference_exact_native_linearalgebra",
            "jax" => "mirror_stress_jnp_x64_no_numpy",
        ),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "PROMOTION_ALLOWED" => false,
        "FORMAL_ADMISSION_ALLOWED" => false,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "engine_noncollapse_probe",
        "carrier_layer" => "single_qubit_density_matrix_left_right_weyl_engine_diagnostic",
        "geometry_layer" => "owner_terrain_lindblad_generators_on_left_right_weyl_flip",
        "claim_ceiling" => "Scratch diagnostic only: tests owner Type 1/Type 2 engine non-collapse criteria under Weyl-flipped terrain equations; no Axis0, gravity, bridge, win/lose dynamics, promotion, or formal admission claim.",
        "allowed_claims" => [
            "computed scratch verdicts for owner non-collapse criteria C1-C4",
            "no-flip control checks whether distinctness is load-bearing on Weyl sign and Pit/Source operator flip",
            "stage WIN/LOSE and win/lose counts are grammar only",
        ],
        "blocked_consumers" => [
            "Axis0",
            "gravity",
            "bridge",
            "formal_admission",
            "promotion",
            "win_lose_dynamical_claim",
            "canonical_engine_admission",
        ],
        "out_of_scope" => [
            "Axis0",
            "gravity",
            "bridge",
            "formal admission",
            "promotion",
            "win/lose as dynamics",
        ],
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "distinct_tol" => DISTINCT_TOL,
        "dt" => DT,
        "stage_steps" => STAGE_STEPS,
        "terrain_steps" => TERRAIN_STEPS,
        "pit_source_steps" => PIT_SOURCE_STEPS,
        "h0_generic_n" => vec_payload(N_GENERIC),
        "sigma_convention" => Dict(
            "sigma_minus" => "[[0,0],[1,0]], sink toward Pauli-z=-1",
            "sigma_plus" => "[[0,1],[0,0]], source toward Pauli-z=+1",
        ),
        "source_alignment" => Dict(
            "owner_source" => "system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:1249-1306",
            "atlas_source" => "system_v5/READ ONLY Reference Docs/ENGINE_64_SCHEDULE_ATLAS.md:103-116",
            "weyl_sheet_pair_tie_in" => "Uses the same s=+1/s=-1 left/right Weyl sign flip family as weyl_sheet_pair_probe; this is a consistency note only.",
        ),
        "engine_equations" => Dict(
            "type1" => [
                "Funnel: sum_k D_Lk(rho) - i eps_F [H0,rho]",
                "Vortex: -i[H0,rho] + eps_V sum_k D_Lk(rho)",
                "Pit: D_sigma_minus(rho) - i eps_P [H0,rho]",
                "Hill: -i[H_C,rho] + sum_j kappa_j(P_j rho P_j - 0.5{P_j,rho})",
            ],
            "type2" => [
                "Cannon: sum_k D_Lk(rho) + i eps_F [H0,rho]",
                "Spiral: +i[H0,rho] + eps_V sum_k D_Lk(rho)",
                "Source: D_sigma_plus(rho) + i eps_P [H0,rho]",
                "Citadel: +i[H_C,rho] + sum_j kappa_j(P_j rho P_j - 0.5{P_j,rho})",
            ],
        ),
        "placements" => Dict("type1" => placement_rows("type1"), "type2" => placement_rows("type2")),
        "grammar_balance" => balances,
        "trajectory_metrics" => Dict("flip" => flip_metrics, "no_flip_control" => no_flip_metrics),
        "terrain_distinctness" => Dict("type1" => type1_terrain, "type2" => type2_terrain),
        "pit_source_flow" => Dict(
            "type1_pit_terminal_z" => Float64(pit_z),
            "type2_source_terminal_z" => Float64(source_z),
            "opposite_signs" => verdicts["pit_source_opposite_z_flow"],
        ),
        "controls" => Dict(
            "same_sign_no_flip_control" => "Type 2 is evaluated with s=+1/H_R=+H0-equivalent commutator sign and Source mapped to sigma_minus/Pit dynamics; this must collapse trajectories.",
            "win_lose_fence" => "WIN/LOSE and win/lose are counted only as chart grammar, not as a dynamical variable.",
        ),
        "verdicts" => verdicts,
        "shared_scalars" => shared_scalars,
        "tools" => ["Julia LinearAlgebra", "JAX jax.numpy x64"],
        "tool_manifest" => tool_manifest,
        "TOOL_MANIFEST" => tool_manifest,
        "tool_integration_depth" => tool_depth,
        "TOOL_INTEGRATION_DEPTH" => tool_depth,
        "numpy_compute_used" => false,
        "jax_x64_enabled" => nothing,
        "divergence_log" => [
            "Type 1 and Type 2 trajectories are compared from the same rho0 under the Weyl-flipped terrain equations.",
            "The decisive no-flip control removes the Weyl sign flip and maps Source to Pit/sigma_minus dynamics; it must collapse trajectories to zero trace distance.",
            "Pit versus Source is tested as sigma_minus sink z-flow versus sigma_plus source z-flow.",
            "WIN/LOSE and win/lose labels are balanced chart grammar only, not a dynamical distinctness claim.",
        ],
        "honest_caveat" => "scratch_diagnostic is used intentionally; this result is not canonical admission, promotion, Axis0, gravity, bridge, or win/lose dynamical evidence.",
        "plain_sentence" => "The owner's two engines stay distinct under the Weyl-flipped terrain dynamics when C1 and C4 pass; they collapse when the no-flip control sets both engines to s=+1 and maps Source back to Pit/sigma_minus dynamics.",
    )
    result["parity"] = parity_block(result)
    result["all_pass"] =
        !(result["numpy_compute_used"]::Bool) &&
        all(Bool(v) for v in values(verdicts)) &&
        (result["parity"]["within_1e_9"]::Bool)
    result["stop_condition_fired"] =
        !(verdicts["collapse_under_no_flip_control"]::Bool) ||
        (result["parity"]["strict_divergence_gt_1e_6"]::Bool)
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    s = result["shared_scalars"]
    println("engine_noncollapse_probe julia wrote $(RESULT_PATH)")
    println("C1 distinct max_trace_distance=$(s["c1_flip_trajectory_max_trace_distance"]) no_flip_control=$(s["c1_no_flip_control_max_trace_distance"])")
    println("C4 pit_z=$(s["c4_type1_pit_terminal_z"]) source_z=$(s["c4_type2_source_terminal_z"])")
    println("terrain_min_type1=$(s["c2_type1_min_pairwise_terrain_trace_distance"]) terrain_min_type2=$(s["c2_type2_min_pairwise_terrain_trace_distance"])")
    println("parity_max_diff=$(result["parity"]["parity_max_diff"]) numpy_compute_used=$(result["numpy_compute_used"])")
    if result["stop_condition_fired"]
        println("STOP_CONDITION_FIRED engine_noncollapse_probe julia")
        exit(1)
    end
end

main()
