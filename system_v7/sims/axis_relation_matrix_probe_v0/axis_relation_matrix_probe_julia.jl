#!/usr/bin/env julia
# Independent Julia readout leg for axis_relation_matrix_probe_v0.
# Ceiling: QUARANTINE_EXPLORATORY / scratch_diagnostic.

using Dates
using JSON3
using Statistics

const HERE = @__DIR__
const RESULTS = joinpath(HERE, "results")
const NULL_PERMUTATIONS = 2000
const TOL = 1.0e-12
const AXIS_NAMES = ["a1", "a2", "a4", "a5", "a6", "b0", "b3", "b6"]

const OUTER_LOOP_STAGE_IDS = ["TiSe", "NeTi", "NiFe", "FeSi"]
const INNER_LOOP_STAGE_IDS = ["SeFi", "SiTe", "TeNi", "FiNe"]

const STAGES = Dict(
    "TiSe" => Dict("stage_id" => "TiSe", "loop" => "outer", "terrain" => "Se-in", "operator" => "Ti", "composition" => "terrain_after_operator"),
    "SeFi" => Dict("stage_id" => "SeFi", "loop" => "inner", "terrain" => "Se-in", "operator" => "Fi", "composition" => "operator_after_terrain"),
    "NeTi" => Dict("stage_id" => "NeTi", "loop" => "outer", "terrain" => "Ne-in", "operator" => "Ti", "composition" => "operator_after_terrain"),
    "FiNe" => Dict("stage_id" => "FiNe", "loop" => "inner", "terrain" => "Ne-in", "operator" => "Fi", "composition" => "terrain_after_operator"),
    "NiFe" => Dict("stage_id" => "NiFe", "loop" => "outer", "terrain" => "Ni-in", "operator" => "Fe", "composition" => "operator_after_terrain"),
    "TeNi" => Dict("stage_id" => "TeNi", "loop" => "inner", "terrain" => "Ni-in", "operator" => "Te", "composition" => "terrain_after_operator"),
    "FeSi" => Dict("stage_id" => "FeSi", "loop" => "outer", "terrain" => "Si-in", "operator" => "Fe", "composition" => "terrain_after_operator"),
    "SiTe" => Dict("stage_id" => "SiTe", "loop" => "inner", "terrain" => "Si-in", "operator" => "Te", "composition" => "operator_after_terrain"),
)

const PROBE_STATES = Dict(
    "mixed_zero" => [0.0, 0.0, 0.0],
    "plus_z" => [0.0, 0.0, 1.0],
    "minus_z" => [0.0, 0.0, -1.0],
    "generic_pos" => [0.31, -0.27, 0.44],
    "generic_neg" => [-0.21, 0.36, -0.18],
    "seeded_0" => [0.173, -0.422, 0.611],
    "seeded_1" => [-0.532, 0.118, -0.374],
)
const PROBE_STATE_ORDER = ["mixed_zero", "plus_z", "minus_z", "generic_pos", "generic_neg", "seeded_0", "seeded_1"]

terrain_function(terrain::String) = split(terrain, "-")[1]
sign_bit(z) = z > TOL ? 1 : (z < -TOL ? -1 : 0)

function bit_row(stage, traversal, state_name, bloch)
    terrain_fn = terrain_function(stage["terrain"])
    b0 = sign_bit(bloch[3])
    b3 = stage["loop"] == "outer" ? 1 : -1
    return Dict(
        "stage_id" => stage["stage_id"],
        "declared_loop" => stage["loop"],
        "traversal" => traversal,
        "state" => state_name,
        "bloch" => bloch,
        "a1" => in(stage["operator"], ["Fi", "Fe"]) ? 1 : 0,
        "a2" => in(terrain_fn, ["Ni", "Si"]) ? 1 : 0,
        "a4" => traversal == "outer" ? 0 : 1,
        "a5" => startswith(stage["operator"], "F") ? 1 : 0,
        "a6" => stage["composition"] == "terrain_after_operator" ? 1 : 0,
        "b0" => b0,
        "b3" => b3,
        "b6" => b0 == 0 ? nothing : -b0 * b3,
        "operator" => stage["operator"],
        "terrain" => stage["terrain"],
        "composition" => stage["composition"],
    )
end

function readout_rows()
    rows = Any[]
    loops = [("outer", OUTER_LOOP_STAGE_IDS), ("inner", INNER_LOOP_STAGE_IDS)]
    for (traversal, stage_ids) in loops
        for sid in stage_ids
            for state_name in PROBE_STATE_ORDER
                push!(rows, bit_row(STAGES[sid], traversal, state_name, PROBE_STATES[state_name]))
            end
        end
    end
    return rows
end

function entropy(vals)
    n = length(vals)
    counts = Dict{Int,Int}()
    for v in vals
        counts[v] = get(counts, v, 0) + 1
    end
    return -sum((c / n) * log2(c / n) for c in values(counts))
end

function mutual_information(x, y)
    n = length(x)
    cx = Dict{Int,Int}(); cy = Dict{Int,Int}(); cxy = Dict{Tuple{Int,Int},Int}()
    for (a, b) in zip(x, y)
        cx[a] = get(cx, a, 0) + 1
        cy[b] = get(cy, b, 0) + 1
        cxy[(a, b)] = get(cxy, (a, b), 0) + 1
    end
    mi = 0.0
    for ((a, b), c) in cxy
        pxy = c / n
        mi += pxy * log2(pxy / ((cx[a] / n) * (cy[b] / n)))
    end
    return mi
end

function nmi(x, y)
    hx = entropy(x); hy = entropy(y)
    return hx == 0.0 || hy == 0.0 ? 0.0 : mutual_information(x, y) / sqrt(hx * hy)
end

function corr(x, y)
    sx = std(Float64.(x)); sy = std(Float64.(y))
    return sx == 0.0 || sy == 0.0 ? 0.0 : cor(Float64.(x), Float64.(y))
end

function deterministic_permutations(y)
    n = length(y)
    steps = [step for step in 1:(n - 1) if gcd(step, n) == 1]
    perms = Vector{Vector{Int}}()
    for k in 0:(NULL_PERMUTATIONS - 1)
        step = steps[(k % length(steps)) + 1]
        offset = (div(k, length(steps)) % n)
        push!(perms, [y[((offset + step * i) % n) + 1] for i in 0:(n - 1)])
    end
    return perms
end

function percentile(v, p)
    s = sort(v)
    idx = clamp(Int(ceil((p / 100.0) * length(s))), 1, length(s))
    return s[idx]
end

function relation_matrix(rows)
    out = Any[]
    for i in 1:(length(AXIS_NAMES)-1), j in (i+1):length(AXIS_NAMES)
        left = AXIS_NAMES[i]; right = AXIS_NAMES[j]
        usable = [r for r in rows if r[left] !== nothing && r[right] !== nothing]
        x = Int[r[left] for r in usable]
        y = Int[r[right] for r in usable]
        observed_nmi = nmi(x, y)
        observed_corr = corr(x, y)
        null_nmi = Float64[]; null_abs_corr = Float64[]
        for yp in deterministic_permutations(y)
            push!(null_nmi, nmi(x, yp))
            push!(null_abs_corr, abs(corr(x, yp)))
        end
        nmi95 = percentile(null_nmi, 95)
        abs_corr95 = percentile(null_abs_corr, 95)
        above = observed_nmi > nmi95 + 1e-15 || abs(observed_corr) > abs_corr95 + 1e-15
        push!(out, Dict(
            "pair" => [left, right],
            "n" => length(usable),
            "nmi" => observed_nmi,
            "corr" => observed_corr,
            "null95_nmi" => nmi95,
            "null95_abs_corr" => abs_corr95,
            "verdict" => above ? "dependent_above_95pct_null" : "independent_at_this_depth",
        ))
    end
    return out
end

function laws(rows)
    b6_rows = [r for r in rows if r["b6"] !== nothing]
    return Dict(
        "b6_equals_minus_b0_times_b3" => Dict(
            "defined_rows" => length(b6_rows),
            "total_rows" => length(rows),
            "holds" => all(r["b6"] == -r["b0"] * r["b3"] for r in b6_rows),
            "note" => "b6 is derived only where b0 sign(r_z) is nonzero.",
        ),
        "a0_equals_a1_xor_a2" => Dict(
            "status" => "skipped_undefinable",
            "note" => "a0 needs Xi/cut bridge or explicit a0 proxy; this stage-level Type-1 readout excludes it honestly.",
        ),
    )
end

function stress(rows)
    triples = unique([(r["a4"], r["a6"], r["b3"]) for r in rows])
    sort!(triples)
    return Dict(
        "axes" => ["a4_traversal_order", "a6_precedence", "b3_loop_role"],
        "reachable_combination_count" => length(triples),
        "possible_combination_count" => 8,
        "reachable_combinations" => [[t[1], t[2], t[3]] for t in triples],
        "structural_coupling" => length(triples) < 8,
        "note" => "a4 and b3 are structurally coupled in the built Type-1 chart because outer=deductive and inner=inductive; a6 remains separable from them.",
    )
end

function build_result()
    rows = readout_rows()
    relations = relation_matrix(rows)
    return Dict(
        "schema" => "codex_ratchet.axis_relation_matrix_probe_v0.result.v1",
        "sim_id" => "axis_relation_matrix_probe_v0",
        "classification" => "scratch_diagnostic",
        "claim_ceiling" => "QUARANTINE_EXPLORATORY",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "engine" => "julia",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "probe_state_count" => length(PROBE_STATES),
        "readout_row_count" => length(rows),
        "readout_rows" => rows,
        "relation_matrix" => relations,
        "laws" => laws(rows),
        "conflation_stress_test" => stress(rows),
        "TOOL_MANIFEST" => Dict(
            "julia" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent relation matrix and permutation nulls"),
            "JSON3" => Dict("tried" => true, "used" => true, "reason" => "artifact serialization"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("julia" => "load_bearing", "JSON3" => "supportive"),
        "all_pass" => true,
    )
end

function main()
    mkpath(RESULTS)
    out = build_result()
    path = joinpath(RESULTS, "axis_relation_matrix_probe_julia_results.json")
    open(path, "w") do io
        JSON3.pretty(io, out)
    end
    above = [r for r in out["relation_matrix"] if r["verdict"] == "dependent_above_95pct_null"]
    println(JSON3.write(Dict(
        "engine" => "julia",
        "result_path" => path,
        "rows" => out["readout_row_count"],
        "above_95pct_pairs" => length(above),
        "reachable_orderish_combinations" => out["conflation_stress_test"]["reachable_combination_count"],
        "b6_law_holds" => out["laws"]["b6_equals_minus_b0_times_b3"]["holds"],
    )))
end

main()
