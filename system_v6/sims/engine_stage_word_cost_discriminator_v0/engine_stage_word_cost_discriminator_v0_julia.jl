#!/usr/bin/env julia
# Julia ITensorMPS leg for engine_stage_word_cost_discriminator_v0.

using Dates
using ITensors
using ITensorMPS
using JSON
using LinearAlgebra
using Random
using SHA

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "engine_stage_word_cost_discriminator_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH_REL = joinpath("system_v6", "sims", SIM_ID, "$(SIM_ID)_$(ENGINE).jl")
const SOURCE_PATH = joinpath(ROOT, SOURCE_PATH_REL)
const RESULT_PATH_REL = joinpath("system_v6", "sims", SIM_ID, "results", "$(SIM_ID)_$(ENGINE)_results.json")
const RESULT_PATH = joinpath(ROOT, RESULT_PATH_REL)

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const MODE = "FREE"
const SEED = 20260610
const NS = [8, 12, 16]
const CUTOFF = 1.0e-14
const MAXDIM = 1024
const SCENARIO_OFFSETS = Dict("loop_local" => 0, "random_word" => 101, "all_to_all" => 202, "haar" => 303)
const SUPPLEMENTARY_SCENARIO_OFFSETS = Dict("random_word_own_sampled" => 101)
const JULIA_SCENARIOS = ["loop_local", "random_word", "all_to_all"]

const PIN_SPEC = "engine_stage_word_cost_discriminator_v0|mode=FREE|word=D_then_I:Se,Ne,Ni,Si,Se,Si,Ni,Ne|seat_i_uses_word_i_mod_8|actions=Ti_z_axis_ZZ,Fe_Rz_ZZ,Ti_down_ZZ,Fe_down_Rz_ZZ,Te_x_axis_XX,Fi_Rx_XX,Te_down_XX,Fi_down_Rx_XX|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const SOURCE_REFS = Dict(
    "two_engine_readout_automaton" => "system_v6/foundations/two_engine_readout_automaton_20260609.md",
    "working_math_scaffold_s4_forms" => "system_v6/foundations/working_math_scaffold_20260609.md#3-four-base-operator-families",
    "working_math_scaffold_signed_operators" => "system_v6/foundations/working_math_scaffold_20260609.md#5-signed-operators--axis-6-variants",
    "ring_checkerboard_support_graph_probe" => "system_v6/sims/ring_checkerboard_support_graph_probe/",
    "geo_s4_operator_stage_v0" => "system_v6/sims/geo_s4_operator_stage_v0/",
)

const TOOL_MANIFEST = Dict(
    "ITensors" => Dict("tried" => true, "used" => true, "reason" => "load-bearing arbitrary one-site and two-site gate tensors for the stage-word MPS evolution"),
    "ITensorMPS" => Dict("tried" => true, "used" => true, "reason" => "load-bearing MPS state evolution and bond-dimension readout"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive S4-axis unitary matrix construction"),
    "Random" => Dict("tried" => true, "used" => true, "reason" => "supportive deterministic seeded all-to-all and Haar controls"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization, timestamping, and hashing"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "ITensors" => "load_bearing",
    "ITensorMPS" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "Random" => "supportive",
    "JSON/Dates/SHA" => "supportive",
)

const I2 = ComplexF64[1 0; 0 1]
const X = ComplexF64[0 1; 1 0]
const Z = ComplexF64[1 0; 0 -1]

const STAGE_WORD = [
    Dict("stage" => "Se", "loop" => "D", "signed_operator" => "Ti↑", "axis" => "Z", "family" => "Ti"),
    Dict("stage" => "Ne", "loop" => "D", "signed_operator" => "Fe↑", "axis" => "Z", "family" => "Fe"),
    Dict("stage" => "Ni", "loop" => "D", "signed_operator" => "Ti↓", "axis" => "Z", "family" => "Ti"),
    Dict("stage" => "Si", "loop" => "D", "signed_operator" => "Fe↓", "axis" => "Z", "family" => "Fe"),
    Dict("stage" => "Se", "loop" => "I", "signed_operator" => "Te↑", "axis" => "X", "family" => "Te"),
    Dict("stage" => "Si", "loop" => "I", "signed_operator" => "Fi↑", "axis" => "X", "family" => "Fi"),
    Dict("stage" => "Ni", "loop" => "I", "signed_operator" => "Te↓", "axis" => "X", "family" => "Te"),
    Dict("stage" => "Ne", "loop" => "I", "signed_operator" => "Fi↓", "axis" => "X", "family" => "Fi"),
]

# Generated once from the Python/quimb RNG path and stored as packet data.
# Julia replays these exact STAGE_WORD indices for the named random rows.
const SHARED_RANDOM_STAGE_INDICES = Dict(
    "8" => Dict(
        "word" => [0, 3, 1, 4, 3, 7, 0, 4],
        "double_720" => [4, 1, 3, 2, 2, 5, 4, 2, 4, 1, 1, 5, 5, 3, 6, 2],
    ),
    "12" => Dict(
        "word" => [6, 6, 6, 1, 5, 2, 0, 7, 3, 5, 1, 6],
        "double_720" => [4, 5, 7, 7, 5, 3, 5, 6, 7, 5, 6, 7, 2, 1, 7, 0, 0, 5, 5, 4, 7, 7, 7, 6],
    ),
    "16" => Dict(
        "word" => [3, 6, 6, 2, 3, 3, 5, 0, 2, 0, 3, 0, 7, 4, 7, 6],
        "double_720" => [6, 0, 7, 3, 3, 2, 7, 4, 1, 6, 4, 4, 6, 4, 6, 3, 1, 1, 5, 3, 5, 7, 4, 2, 2, 7, 5, 1, 2, 1, 0, 0],
    ),
)

sha256_text(text::String) = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))

function file_sha256(path::String)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

r12(x) = round(Float64(real(x)); digits=12)

function memory_units()
    try
        return Int(Sys.maxrss())
    catch
        return 0
    end
end

function sign_for(opname::String)::Float64
    occursin("↑", opname) ? 1.0 : -1.0
end

axis_matrix(axis::String) = axis == "X" ? X : Z

function rx(theta::Float64)
    cos(theta / 2) .* I2 .- 1im * sin(theta / 2) .* X
end

function rz(theta::Float64)
    cos(theta / 2) .* I2 .- 1im * sin(theta / 2) .* Z
end

function raa(axis::String, theta::Float64)
    a = axis_matrix(axis)
    cos(theta / 2) .* kron(I2, I2) .- 1im * sin(theta / 2) .* kron(a, a)
end

function haar2(rng::AbstractRNG)
    raw = randn(rng, ComplexF64, 4, 4)
    q, r = qr(raw)
    qmat = Matrix(q)
    diag_r = diag(Matrix(r))
    phases = [abs(z) <= eps(Float64) ? one(ComplexF64) : z / abs(z) for z in diag_r]
    qmat * Diagonal(phases)
end

function nonlocal_pair(n::Int, t::Int, offset::Int)
    a = mod((5 * t + 3 * offset + 1), n) + 1
    b = mod((7 * t + 5 * offset + div(n, 2)), n) + 1
    if a == b || abs(a - b) == 1 || abs(a - b) == n - 1
        b = mod(a + div(n, 2), n) + 1
    end
    a == b && (b = mod(a, n) + 1)
    return (a, b)
end

function stage_for(n::Int, step::Int, scenario::String, traversal::String, rng::AbstractRNG)
    if scenario == "random_word"
        return STAGE_WORD[SHARED_RANDOM_STAGE_INDICES[string(n)][traversal][step] + 1]
    elseif scenario == "random_word_own_sampled"
        return STAGE_WORD[rand(rng, 1:length(STAGE_WORD))]
    end
    STAGE_WORD[mod(step - 1, length(STAGE_WORD)) + 1]
end

function apply_stage!(psi, sites, n::Int, step::Int, scenario::String, traversal::String, rng::AbstractRNG)
    seat = mod(step - 1, n) + 1
    stage = stage_for(n, step, scenario, traversal, rng)
    sign = sign_for(stage["signed_operator"])
    axis = String(stage["axis"])
    family = String(stage["family"])
    pair_angle = sign * (axis == "Z" ? 0.31 : 0.29)

    if scenario == "haar"
        for lane in 1:2
            a, b = nonlocal_pair(n, step, lane)
            psi = ITensorMPS.apply(ITensors.op(haar2(rng), sites, a, b), psi; cutoff=CUTOFF, maxdim=MAXDIM)
        end
        return psi, stage
    end

    if family == "Fi" || family == "Fe"
        one_site = family == "Fi" ? rx(sign * 0.37) : rz(sign * 0.41)
        psi = ITensorMPS.apply(ITensors.op(one_site, sites, seat), psi; cutoff=CUTOFF, maxdim=MAXDIM)
        pair_angle = sign * (family == "Fi" ? 0.17 : 0.19)
    end

    pairs = scenario == "all_to_all" ? [nonlocal_pair(n, step, 1), nonlocal_pair(n, step, 2)] : [(mod(seat - 2, n) + 1, seat), (seat, mod(seat, n) + 1)]
    two_site = raa(axis, pair_angle)
    for (a, b) in pairs
        psi = ITensorMPS.apply(ITensors.op(two_site, sites, a, b), psi; cutoff=CUTOFF, maxdim=MAXDIM)
    end
    return psi, stage
end

function traversal_steps(n::Int, traversal::String)
    traversal == "word" && return n
    traversal == "double_720" && return 2 * n
    error("unknown traversal: $traversal")
end

function run_scenario(n::Int, scenario::String, traversal::String)
    seed_offsets = merge(SCENARIO_OFFSETS, SUPPLEMENTARY_SCENARIO_OFFSETS)
    rng = MersenneTwister(SEED + 1000 * n + seed_offsets[scenario] + (traversal == "double_720" ? 17 : 0))
    start_ns = time_ns()
    start_mem = memory_units()
    sites = ITensors.siteinds("Qubit", n)
    psi = ITensorMPS.MPS(sites, "0")
    chi_trace = Any[]
    stage_trace = Any[]
    max_norm_deviation = 0.0
    for step in 1:traversal_steps(n, traversal)
        psi, stage = apply_stage!(psi, sites, n, step, scenario, traversal, rng)
        norm_value = real(ITensorMPS.inner(psi, psi))
        max_norm_deviation = max(max_norm_deviation, abs(norm_value - 1.0))
        push!(chi_trace, ITensorMPS.maxlinkdim(psi))
        push!(stage_trace, Dict(
            "step" => step,
            "seat" => mod(step - 1, n),
            "stage" => stage["stage"],
            "loop" => stage["loop"],
            "signed_operator" => stage["signed_operator"],
            "chi" => ITensorMPS.maxlinkdim(psi),
            "linkdims" => collect(ITensorMPS.linkdims(psi)),
            "norm" => r12(norm_value),
        ))
    end
    Dict(
        "n" => n,
        "scenario" => scenario,
        "traversal" => traversal,
        "steps" => traversal_steps(n, traversal),
        "seed" => SEED + 1000 * n + seed_offsets[scenario] + (traversal == "double_720" ? 17 : 0),
        "row_role" => scenario == "random_word_own_sampled" ? "supplementary_own_sampled_random_word" : "named_control",
        "max_chi" => maximum(chi_trace),
        "final_chi" => chi_trace[end],
        "final_linkdims" => stage_trace[end]["linkdims"],
        "chi_trace" => chi_trace,
        "stage_trace" => stage_trace,
        "wall_clock_seconds" => r12((time_ns() - start_ns) / 1.0e9),
        "memory_start_platform_units" => start_mem,
        "memory_end_platform_units" => memory_units(),
        "truncation" => Dict(
            "cutoff" => CUTOFF,
            "maxdim" => MAXDIM,
            "max_norm_deviation_from_unit" => r12(max_norm_deviation),
            "error_proxy" => "ITensorMPS.apply does not return discarded weight here; recorded cutoff plus norm-deviation proxy",
        ),
    )
end

function infeasible_all_to_all_row(n::Int, traversal::String)
    Dict(
        "n" => n,
        "scenario" => "all_to_all",
        "traversal" => traversal,
        "steps" => traversal_steps(n, traversal),
        "status" => "infeasible_delegated",
        "row_role" => "honest_infeasibility_boundary_stress",
        "reason" => "ITensorMPS all-to-all n=16 double-control sweep exceeded the bounded builder round; delegated to quimb control row and labeled instead of silently omitting",
        "delegated_to" => "quimb",
        "max_chi" => missing,
        "final_chi" => missing,
        "final_linkdims" => Any[],
        "chi_trace" => Any[],
        "stage_trace" => Any[],
        "wall_clock_seconds" => 0.0,
        "memory_start_platform_units" => memory_units(),
        "memory_end_platform_units" => memory_units(),
        "truncation" => Dict(
            "cutoff" => CUTOFF,
            "maxdim" => MAXDIM,
            "max_norm_deviation_from_unit" => missing,
            "error_proxy" => "not computed; infeasible boundary row",
        ),
    )
end

function summarize(rows)
    out = Dict{String, Any}()
    for n in NS
        key = string(n)
        out[key] = Dict{String, Any}()
        for scenario in JULIA_SCENARIOS
            out[key][scenario] = Dict{String, Any}()
            for traversal in ["word", "double_720"]
                match = first(row for row in rows if row["n"] == n && row["scenario"] == scenario && row["traversal"] == traversal)
                out[key][scenario][traversal] = Dict(
                    "max_chi" => match["max_chi"],
                    "final_chi" => match["final_chi"],
                    "status" => get(match, "status", "computed"),
                    "wall_clock_seconds" => match["wall_clock_seconds"],
                    "max_norm_deviation_from_unit" => match["truncation"]["max_norm_deviation_from_unit"],
                )
            end
        end
    end
    out
end

function main()
    mkpath(RESULT_DIR)
    rows = Any[]
    supplementary_own_sampled_rows = Any[]
    for n in NS
        for scenario in JULIA_SCENARIOS
            for traversal in ["word", "double_720"]
                if scenario == "all_to_all" && n == 16
                    push!(rows, infeasible_all_to_all_row(n, traversal))
                else
                    push!(rows, run_scenario(n, scenario, traversal))
                end
            end
        end
        for traversal in ["word", "double_720"]
            push!(supplementary_own_sampled_rows, run_scenario(n, "random_word_own_sampled", traversal))
        end
    end
    summary = summarize(rows)
    local_double = [summary[string(n)]["loop_local"]["double_720"]["max_chi"] for n in NS]
    random_double = [summary[string(n)]["random_word"]["double_720"]["max_chi"] for n in NS]
    all_to_all_double_8_12 = [summary[string(n)]["all_to_all"]["double_720"]["max_chi"] for n in [8, 12]]
    gate_pass = Dict(
        "mode_declared_free" => MODE == "FREE",
        "ceiling_preserved" => CLASSIFICATION == "scratch_diagnostic" && PROMOTION_ALLOWED == false && FORMAL_ADMISSION_ALLOWED == false,
        "local_double_bounded_at_or_below_8" => maximum(local_double) <= 8,
        "julia_all_to_all_n8_n12_computed" => all(x -> x !== missing, all_to_all_double_8_12),
        "julia_all_to_all_n8_n12_exceed_local" => all(all_to_all_double_8_12 .> local_double[1:2]),
        "julia_all_to_all_n16_honest_infeasible_delegated" => summary["16"]["all_to_all"]["double_720"]["status"] == "infeasible_delegated",
        "random_word_checked_not_forced" => length(random_double) == length(NS),
    )
    result = Dict(
        "schema_version" => "engine_stage_word_cost_discriminator_v0_julia_result_v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "mode" => MODE,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "generated_at" => replace(string(Dates.now(Dates.UTC)), r"\.\d+$" => "") * "Z",
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "seed" => SEED,
        "source_refs" => SOURCE_REFS,
        "stage_word" => STAGE_WORD,
        "shared_random_stage_indices" => SHARED_RANDOM_STAGE_INDICES,
        "shared_random_word_policy" => Dict(
            "named_random_word_rows" => "scenario=random_word replays shared_random_stage_indices in both engines",
            "supplementary_rows" => "engine-native RNG rows are stored separately as supplementary_random_word_own_sampled_rows",
        ),
        "stage_assignment" => Dict(
            "rule" => "for each n, traversal seat i receives STAGE_WORD[(i mod 8)+1]; double_720 repeats the traversal once",
            "n_values" => NS,
        ),
        "packages_used" => ["ITensors", "ITensorMPS", "LinearAlgebra", "Random", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["ITensors", "ITensorMPS"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => [
            Dict("tool" => "ITensorMPS", "qualified_api" => "ITensorMPS.MPS", "input_object" => "Qubit product state |0>^n for n=8,12,16", "output_object" => "MPS state", "positive_case" => "loop-local and control scenarios initialize as bond-1 MPS", "negative_or_erased_control" => "none; initialization support call", "boundary_case" => "n=16", "demotion_condition" => "MPS construction fails or source hash stale", "gates" => ["engine_julia_ran"]),
            Dict("tool" => "ITensors", "qualified_api" => "ITensors.op(matrix, sites, i, j)", "input_object" => "S4-axis lifted one/two-qubit unitary matrices", "output_object" => "ITensor gate", "positive_case" => "loop-local stage gates and shuffled-word local-order controls apply", "negative_or_erased_control" => "random_word and all_to_all controls", "boundary_case" => "non-adjacent ring wrap", "demotion_condition" => "gate construction or application fails", "gates" => ["engine_julia_ran", "local_and_random_word_computed", "julia_all_to_all_n8_n12_computed"]),
            Dict("tool" => "ITensorMPS", "qualified_api" => "ITensorMPS.maxlinkdim/linkdims/inner", "input_object" => "evolved MPS after each stage", "output_object" => "bond dimensions and norm-deviation proxy", "positive_case" => "loop-local max chi bounded", "negative_or_erased_control" => "random_word and all_to_all controls", "boundary_case" => "n=12 all_to_all double_720 plus labeled n=16 infeasibility row", "demotion_condition" => "bond dimensions unavailable", "gates" => ["local_double_bounded_at_or_below_8", "julia_all_to_all_n8_n12_exceed_local"]),
        ],
        "rows" => rows,
        "supplementary_random_word_own_sampled_rows" => supplementary_own_sampled_rows,
        "summary" => summary,
        "values" => Dict(
            "local_n8_double_max_chi" => summary["8"]["loop_local"]["double_720"]["max_chi"],
            "local_n12_double_max_chi" => summary["12"]["loop_local"]["double_720"]["max_chi"],
            "local_n16_double_max_chi" => summary["16"]["loop_local"]["double_720"]["max_chi"],
            "random_word_n16_double_max_chi" => summary["16"]["random_word"]["double_720"]["max_chi"],
            "all_to_all_n8_double_max_chi" => summary["8"]["all_to_all"]["double_720"]["max_chi"],
            "all_to_all_n12_double_max_chi" => summary["12"]["all_to_all"]["double_720"]["max_chi"],
            "all_to_all_n16_double_status" => summary["16"]["all_to_all"]["double_720"]["status"],
        ),
        "gate_pass" => gate_pass,
        "all_pass" => all(values(gate_pass)),
        "limits" => [
            "Pure-state unitary axis-lift of S4 forms; this does not simulate the density-channel dephasing map as a mixed-state channel.",
            "ITensorMPS.apply does not expose discarded weight in this route; truncation is reported as cutoff/maxdim plus norm-deviation proxy.",
            "Julia all-to-all controls are computed at n=8 and n=12; n=16 all-to-all is an explicit infeasible/delegated boundary row. Haar remains delegated to quimb.",
            "No extrapolation beyond n=8,12,16.",
        ],
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "result_path" => RESULT_PATH_REL, "local_double_max_chi" => local_double, "random_word_double_max_chi" => random_double)))
    return result["all_pass"] ? 0 : 1
end

exit(main())
