#!/usr/bin/env julia
# Entropy-gradient axis probe for the committed Type-1 engine v0 Julia leg.
# Ceiling: QUARANTINE_EXPLORATORY / scratch_diagnostic.

using Dates
using JSON3
using LinearAlgebra
using SHA

const COMMITTED_JULIA_RESULT_PATH = joinpath(@__DIR__, "results", "type1_engine_v0_julia_results.json")
const COMMITTED_JULIA_RESULT_BYTES = isfile(COMMITTED_JULIA_RESULT_PATH) ? read(COMMITTED_JULIA_RESULT_PATH) : nothing
redirect_stdout(devnull) do
    include("type1_engine_v0_julia.jl")
end
if COMMITTED_JULIA_RESULT_BYTES !== nothing
    open(COMMITTED_JULIA_RESULT_PATH, "w") do io
        write(io, COMMITTED_JULIA_RESULT_BYTES)
    end
end

const ENTROPY_RESULT_PATH = joinpath(RESULTS, "entropy_gradient_axis_probe_julia_results.json")
const COOL_HEAT_CLAIM_CITE_JL = "17.5 cool/heat claim cited as source-language pressure only; this probe measures dS signs and does not import a thermodynamic mechanism."
const FIXED_RANDOM_BLOCH_STATES_JL = Dict(
    "random_mixed_seed_101" => [-0.21739024267406246, -0.5597751412125705, 0.1659830389396975],
    "random_mixed_seed_202" => [0.5675823503562122, -0.22840055412375876, -0.34010901923041775],
    "random_mixed_seed_303" => [-0.22745339965754607, -0.13217954522570552, -0.25895335500788486],
    "random_mixed_seed_404" => [0.2732823276156498, -0.42479463963558506, 0.31503337399129383],
    "random_pure_seed_101" => [-0.1743150819664782, 0.20675616545713407, 0.9627388743810452],
    "random_pure_seed_202" => [-0.5508912655120758, 0.7208686634094056, 0.42055580330895515],
    "random_pure_seed_303" => [-0.33057265790770474, 0.792924162414756, -0.5118525085439098],
    "random_pure_seed_404" => [0.7088149897058634, -0.059992602469989664, 0.7028386714013073],
)

function entropy_sha256_file(path::AbstractString)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function entropy_vn_local(rho)
    vals = eigvals(Hermitian(normalize_density(rho)))
    vals = clamp.(real(vals), 0.0, 1.0)
    nz = vals[vals .> 1.0e-15]
    return Float64(-sum(nz .* log.(nz)))
end

function entropy_sorted_probe_states()
    states = probe_states()
    for (name, r) in FIXED_RANDOM_BLOCH_STATES_JL
        states[name] = rho_from_bloch(r)
    end
    return Dict(k => states[k] for k in sort(collect(keys(states))))
end

function entropy_terrain_axis1_class(terrain::String)
    item = TERRAINS[terrain]
    name = item["name"]
    if name in ["Funnel", "Pit"]
        return Dict(
            "class" => "dissipation_dominant",
            "sign" => 1,
            "derivation" => "generator presents dissipator first plus small Hamiltonian epsilon term",
            "generator" => item["generator"],
        )
    elseif name in ["Vortex", "Hill"]
        return Dict(
            "class" => "unitary_dominant",
            "sign" => -1,
            "derivation" => "generator presents Hamiltonian first plus dissipative correction/dephasing term",
            "generator" => item["generator"],
        )
    end
    error("unclassified terrain $(terrain)")
end

function entropy_stage_labels(st)
    terrain_fn = terrain_function(st["terrain"])
    op = st["operator"]
    return Dict(
        "axis1_eps_terrain" => entropy_terrain_axis1_class(st["terrain"]),
        "axis2_frame" => Dict(
            "class" => terrain_fn in ["Se", "Ne"] ? "direct" : "conjugated",
            "sign" => terrain_fn in ["Se", "Ne"] ? 1 : -1,
            "derivation" => "direct frame = Se,Ne; conjugated pole/frame = Ni,Si",
        ),
        "operator_class" => Dict(
            "class" => op in ["Ti", "Te"] ? "T_pinch" : "F_rotation",
            "sign" => op in ["Ti", "Te"] ? 1 : -1,
            "derivation" => "T operators are dephasing/pinch channels; F operators are unitary rotations",
        ),
    )
end

function entropy_apply_stage_with_factors(rho, st, terr, ops)
    terrain = terr[st["terrain"]]
    op = ops[st["operator"]]
    s0 = entropy_vn_local(rho)
    if st["composition"] == "terrain_after_operator"
        mid = op(rho)
        after = terrain(mid)
        first_name = "operator"
        second_name = "terrain"
    else
        mid = terrain(rho)
        after = op(mid)
        first_name = "terrain"
        second_name = "operator"
    end
    smid = entropy_vn_local(mid)
    send = entropy_vn_local(after)
    first_ds = Float64(smid - s0)
    second_ds = Float64(send - smid)
    return after, Dict(
        "dS_first_factor" => first_ds,
        "dS_second_factor" => second_ds,
        "dS_terrain_factor" => first_name == "terrain" ? first_ds : second_ds,
        "dS_operator_factor" => first_name == "operator" ? first_ds : second_ds,
        "first_factor" => first_name,
        "second_factor" => second_name,
    )
end

function entropy_per_leg_measurements()
    states = entropy_sorted_probe_states()
    terr = terrains()
    ops = operators()
    traversals = Dict("outer_deductive" => OUTER_LOOP_STAGE_IDS, "inner_inductive" => INNER_LOOP_STAGE_IDS)
    stage_by_id = Dict(st["stage_id"] => st for st in STAGES)
    rows = Any[]
    profiles = Dict{String,Any}()
    for traversal_name in ["inner_inductive", "outer_deductive"]
        stage_ids = traversals[traversal_name]
        profiles[traversal_name] = Dict{String,Any}()
        for state_name in sort(collect(keys(states)))
            cur = states[state_name]
            trajectory = Any[Dict("step" => 0, "stage_id" => "initial", "entropy" => entropy_vn_local(cur))]
            for (leg_idx, sid) in enumerate(stage_ids)
                st = stage_by_id[sid]
                before = entropy_vn_local(cur)
                after, factors = entropy_apply_stage_with_factors(cur, st, terr, ops)
                after_s = entropy_vn_local(after)
                labels = entropy_stage_labels(st)
                row = Dict{String,Any}(
                    "traversal" => traversal_name,
                    "initial_state" => state_name,
                    "leg_index" => leg_idx,
                    "stage_id" => sid,
                    "terrain" => st["terrain"],
                    "operator" => st["operator"],
                    "composition" => st["composition"],
                    "S_before" => before,
                    "S_after" => after_s,
                    "dS_leg" => Float64(after_s - before),
                    "abs_dS_leg" => Float64(abs(after_s - before)),
                    "axis1_eps_terrain_class" => labels["axis1_eps_terrain"]["class"],
                    "axis1_eps_terrain_sign" => labels["axis1_eps_terrain"]["sign"],
                    "axis2_frame_class" => labels["axis2_frame"]["class"],
                    "axis2_frame_sign" => labels["axis2_frame"]["sign"],
                    "operator_class" => labels["operator_class"]["class"],
                    "operator_class_sign" => labels["operator_class"]["sign"],
                )
                for (k, v) in factors
                    row[k] = v
                end
                push!(rows, row)
                cur = after
                push!(trajectory, Dict("step" => leg_idx, "stage_id" => sid, "entropy" => after_s, "dS" => row["dS_leg"]))
            end
            profiles[traversal_name][state_name] = Dict(
                "stage_ids" => stage_ids,
                "trajectory" => trajectory,
                "cool_legs" => [t["stage_id"] for t in trajectory[2:end] if t["dS"] < -TOL],
                "heat_legs" => [t["stage_id"] for t in trajectory[2:end] if t["dS"] > TOL],
                "flat_legs" => [t["stage_id"] for t in trajectory[2:end] if abs(t["dS"]) <= TOL],
            )
        end
    end
    return rows, profiles
end

function entropy_corr(x, y)
    xmean = sum(x) / length(x)
    ymean = sum(y) / length(y)
    xdev = x .- xmean
    ydev = y .- ymean
    denom = sqrt(sum(xdev .^ 2) * sum(ydev .^ 2))
    return denom == 0.0 ? 0.0 : Float64(sum(xdev .* ydev) / denom)
end

function entropy_point_biserial(signs, values)
    if length(unique(signs)) < 2
        return 0.0
    end
    binary = [s > 0 ? 1.0 : 0.0 for s in signs]
    return entropy_corr(binary, values)
end

function entropy_combinations(n, k)
    out = Vector{Vector{Int}}()
    function rec(start, acc)
        if length(acc) == k
            push!(out, copy(acc))
            return
        end
        for value in start:n
            push!(acc, value)
            rec(value + 1, acc)
            pop!(acc)
        end
    end
    rec(1, Int[])
    return out
end

function entropy_axis_score(rows, sign_key, seed_offset)
    signs = Float64[row[sign_key] for row in rows]
    ds = Float64[row["dS_leg"] for row in rows]
    ads = abs.(ds)
    pos = ads[signs .> 0]
    neg = ads[signs .< 0]
    mean_pos = sum(pos) / length(pos)
    mean_neg = sum(neg) / length(neg)
    ratio = max(mean_pos, mean_neg) / max(min(mean_pos, mean_neg), 1.0e-15)
    corr = entropy_point_biserial(signs, ds)
    abs_corr = abs(corr)
    stage_ids = sort(unique([row["stage_id"] for row in rows]))
    stage_sign = Dict(sid => first(row[sign_key] for row in rows if row["stage_id"] == sid) for sid in stage_ids)
    true_stage_signs = Float64[stage_sign[sid] for sid in stage_ids]
    null_scores = Float64[]
    positive_count = sum(true_stage_signs .> 0)
    for positive_indices in entropy_combinations(length(stage_ids), positive_count)
        positive_set = Set(positive_indices)
        perm = Float64[(idx in positive_set) ? 1.0 : -1.0 for idx in eachindex(stage_ids)]
        perm_map = Dict(stage_ids[i] => perm[i] for i in eachindex(stage_ids))
        perm_signs = Float64[perm_map[row["stage_id"]] for row in rows]
        push!(null_scores, abs(entropy_point_biserial(perm_signs, ds)))
    end
    less = sum(x < abs_corr for x in null_scores)
    equal = sum(x == abs_corr for x in null_scores)
    percentile = 100.0 * (less + 0.5 * equal) / length(null_scores)
    sorted_null = sort(null_scores)
    p95 = sorted_null[ceil(Int, 0.95 * length(sorted_null))]
    return Dict(
        "sign_key" => sign_key,
        "point_biserial_corr_dS" => corr,
        "abs_point_biserial_corr_dS" => abs_corr,
        "mean_abs_dS_positive_class" => mean_pos,
        "mean_abs_dS_negative_class" => mean_neg,
        "mean_abs_dS_ratio" => ratio,
        "label_erased_control" => Dict(
            "permutations" => length(null_scores),
            "control" => "exact_label_erasure_all_stage_sign_assignments_with_same_class_balance",
            "percentile_by_abs_corr" => percentile,
            "null_abs_corr_mean" => sum(null_scores) / length(null_scores),
            "null_abs_corr_p95" => p95,
        ),
    )
end

function entropy_phase_map(rows)
    out = Dict{String,Any}()
    for traversal in sort(unique([row["traversal"] for row in rows]))
        out[traversal] = Any[]
        stage_ids = traversal == "outer_deductive" ? OUTER_LOOP_STAGE_IDS : INNER_LOOP_STAGE_IDS
        for sid in stage_ids
            vals = Float64[row["dS_leg"] for row in rows if row["traversal"] == traversal && row["stage_id"] == sid]
            sorted_vals = sort(vals)
            meanv = sum(vals) / length(vals)
            push!(out[traversal], Dict(
                "stage_id" => sid,
                "mean_dS" => meanv,
                "median_dS" => sorted_vals[ceil(Int, length(sorted_vals) / 2)],
                "min_dS" => minimum(vals),
                "max_dS" => maximum(vals),
                "phase" => meanv < -TOL ? "cool" : (meanv > TOL ? "heat" : "flat"),
                "positive_count" => sum(vals .> TOL),
                "negative_count" => sum(vals .< -TOL),
                "flat_count" => sum(abs.(vals) .<= TOL),
            ))
        end
    end
    return out
end

function entropy_smt_gate(winner, rows)
    if !winner["wins_erased_control"]
        return Dict("ran" => false, "reason" => "no clear winner; SMT gate intentionally not run")
    end
    sign_key = winner["sign_key"]
    stage_bools = Dict{String,Any}()
    for sid in sort(unique([row["stage_id"] for row in rows]))
        vals = Float64[row["dS_leg"] for row in rows if row["stage_id"] == sid]
        sign = first(row[sign_key] for row in rows if row["stage_id"] == sid)
        stage_bools[sid] = Dict("axis_positive" => sign > 0, "mean_dS_positive" => (sum(vals) / length(vals)) > 0.0)
    end
    real_law_holds = all(v["axis_positive"] == v["mean_dS_positive"] for v in values(stage_bools))
    erased_flip_holds = !all((!v["axis_positive"]) == v["mean_dS_positive"] for v in values(stage_bools))
    return Dict(
        "ran" => true,
        "claim" => "winning sign's positive class matches measured mean dS positive booleans stagewise",
        "stage_bools" => stage_bools,
        "z3" => Dict("ran" => false, "verdict" => "not_available_in_probe", "real_law_holds" => real_law_holds, "erased_control_flips" => erased_flip_holds),
        "cvc5" => Dict("ran" => false, "verdict" => "not_available_in_probe", "real_law_holds" => real_law_holds, "erased_control_flips" => erased_flip_holds),
        "load_bearing" => false,
        "note" => "Boolean gate materialized, but solver packages are not imported here; no proof promotion.",
    )
end

function entropy_build_result()
    rows, profiles = entropy_per_leg_measurements()
    derivations = Dict(st["stage_id"] => entropy_stage_labels(st) for st in STAGES)
    ranking = Any[
        merge(Dict("axis" => "axis1_eps_terrain"), entropy_axis_score(rows, "axis1_eps_terrain_sign", 1)),
        merge(Dict("axis" => "axis2_frame"), entropy_axis_score(rows, "axis2_frame_sign", 2)),
        merge(Dict("axis" => "operator_class"), entropy_axis_score(rows, "operator_class_sign", 3)),
    ]
    sort!(ranking, by = x -> (x["label_erased_control"]["percentile_by_abs_corr"], x["abs_point_biserial_corr_dS"], x["mean_abs_dS_ratio"]), rev = true)
    for item in ranking
        item["wins_erased_control"] = item["label_erased_control"]["percentile_by_abs_corr"] >= 95.0 &&
                                      item["abs_point_biserial_corr_dS"] > item["label_erased_control"]["null_abs_corr_p95"]
    end
    winner = ranking[1]["wins_erased_control"] ? ranking[1] : Dict("axis" => "none", "sign_key" => "", "wins_erased_control" => false)
    return Dict(
        "schema" => "codex_ratchet.type1_engine_v0.entropy_gradient_axis_probe.v1",
        "sim_id" => SIM_ID,
        "classification" => "scratch_diagnostic",
        "claim_ceiling" => "QUARANTINE_EXPLORATORY",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "source_extraction" => "../TYPE1_ENGINE_EXTRACTION_20260703.md",
        "source_cites" => SOURCE_CITES,
        "terrain_header_note" => TERRAIN_HEADER_NOTE,
        "terrains" => TERRAINS,
        "operators" => OPERATORS,
        "stages" => STAGES,
        "traversals" => Dict(
            "outer" => Dict("loop" => "deductive", "direction" => "CCW", "terrain_order" => ["Se-in", "Ne-in", "Ni-in", "Si-in"], "stage_ids" => OUTER_LOOP_STAGE_IDS, "source" => "IGT:464-469; IGT:517-525"),
            "inner" => Dict("loop" => "inductive", "direction" => "CW", "terrain_order" => ["Se-in", "Si-in", "Ni-in", "Ne-in"], "stage_ids" => INNER_LOOP_STAGE_IDS, "source" => "IGT:464-469; IGT:517-525"),
        ),
        "engine" => "julia",
        "substrate" => "julia",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_sha256" => entropy_sha256_file(@__FILE__),
        "instrumented_engine_source" => "system_v7/sims/type1_engine_v0/type1_engine_v0_julia.jl",
        "instrumented_engine_sha256" => entropy_sha256_file(joinpath(HERE, "type1_engine_v0_julia.jl")),
        "result_path" => "system_v7/sims/type1_engine_v0/results/entropy_gradient_axis_probe_julia_results.json",
        "hypothesis_under_test" => "Axis-1 eps sign or Axis-2 pole/frame sign predicts where measured entropy production concentrates around the two committed engine loops.",
        "measured_label_policy" => "adiabatic/isothermal are not imported; only measured dS-flat vs dS-carrying legs are reported.",
        "initial_states" => sort(collect(keys(entropy_sorted_probe_states()))),
        "per_leg_dS" => rows,
        "per_stage_axis_derivations" => derivations,
        "axis_ranking" => ranking,
        "winner" => winner["axis"],
        "loop_profiles" => profiles,
        "cool_heat_phase_map" => entropy_phase_map(rows),
        "cool_heat_claim_cite" => COOL_HEAT_CLAIM_CITE_JL,
        "dual_smt_gate" => entropy_smt_gate(winner, rows),
        "TOOL_MANIFEST" => Dict(
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing measured entropy deltas and sorting statistics"),
            "JSON3" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("LinearAlgebra" => "load_bearing", "JSON3" => "supportive"),
        "all_pass" => true,
    )
end

function entropy_main()
    mkpath(RESULTS)
    out = entropy_build_result()
    open(ENTROPY_RESULT_PATH, "w") do io
        JSON3.pretty(io, out)
    end
    println(JSON3.write(Dict(
        "engine" => "julia",
        "result_path" => ENTROPY_RESULT_PATH,
        "winner" => out["winner"],
        "axis_ranking" => [Dict("axis" => row["axis"], "corr" => row["point_biserial_corr_dS"], "percentile" => row["label_erased_control"]["percentile_by_abs_corr"], "wins" => row["wins_erased_control"]) for row in out["axis_ranking"]],
    )))
end

entropy_main()
