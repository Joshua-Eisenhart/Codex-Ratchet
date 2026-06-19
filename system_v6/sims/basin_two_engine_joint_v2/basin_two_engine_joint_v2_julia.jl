#!/usr/bin/env julia
# Julia Graphs/Z3 leg for basin_two_engine_joint_v2.

using Dates
using Graphs
using JSON
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "basin_two_engine_joint_v2"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const LOOP_MOD = 2
const STAGE_MOD = 4
const SUBSTAGE_MOD = 4
const PER_ENGINE = LOOP_MOD * STAGE_MOD * SUBSTAGE_MOD
const JOINT_COUNT = PER_ENGINE * PER_ENGINE

const TOOL_MANIFEST = Dict(
    "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing directed graph construction and SCC computation"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing primary no-64 proof with erased flip"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization, timestamping, and hashing"),
)
const TOOL_INTEGRATION_DEPTH = Dict(
    "Graphs" => "load_bearing",
    "Z3" => "load_bearing",
    "JSON/Dates/SHA" => "supportive",
)

function now_z()::String
    Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
end

function rel(path::String)::String
    replace(relpath(path, ROOT), "\\" => "/")
end

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function stable_sha(value)::String
    bytes2hex(sha256(collect(codeunits(JSON.json(value)))))
end

function engine_state_id(loop::Int, stage::Int, substage::Int)::Int
    return ((loop * STAGE_MOD) + stage) * SUBSTAGE_MOD + substage
end

function decode_engine(state_id::Int)
    substage = mod(state_id, SUBSTAGE_MOD)
    rest = div(state_id, SUBSTAGE_MOD)
    stage = mod(rest, STAGE_MOD)
    loop = div(rest, STAGE_MOD)
    return loop, stage, substage
end

function joint_id(l_state::Int, r_state::Int)::Int
    return l_state * PER_ENGINE + r_state
end

function apply_engine_op(state_id::Int, op::String)::Int
    loop, stage, substage = decode_engine(state_id)
    if op == "full_tick"
        substage += 1
        if substage == SUBSTAGE_MOD
            substage = 0
            stage += 1
            if stage == STAGE_MOD
                stage = 0
                loop = mod(loop + 1, LOOP_MOD)
            end
        end
    elseif op == "loop_advance"
        loop = mod(loop + 1, LOOP_MOD)
    elseif op == "stage_progression"
        stage = mod(stage + 1, STAGE_MOD)
    elseif op == "substage_cycling"
        substage = mod(substage + 1, SUBSTAGE_MOD)
    else
        error("unknown op $(op)")
    end
    return engine_state_id(loop, stage, substage)
end

function generator_specs(row_id::String)
    if row_id == "source_sync_full_tick"
        return [("sync_full_tick", "full_tick", "full_tick")]
    elseif row_id == "source_l_only_full_tick"
        return [("L_only_full_tick", "full_tick", "none")]
    elseif row_id == "source_r_only_full_tick"
        return [("R_only_full_tick", "none", "full_tick")]
    elseif row_id == "source_async_lr_union_full_tick"
        return [("L_only_full_tick", "full_tick", "none"), ("R_only_full_tick", "none", "full_tick")]
    elseif row_id == "source_all_interleavings_full_tick"
        return [("L_only_full_tick", "full_tick", "none"), ("R_only_full_tick", "none", "full_tick"), ("sync_full_tick", "full_tick", "full_tick")]
    elseif row_id == "conditioned_sync_loop_advance"
        return [("sync_loop_advance", "loop_advance", "loop_advance")]
    elseif row_id == "conditioned_sync_stage_progression"
        return [("sync_stage_progression", "stage_progression", "stage_progression")]
    elseif row_id == "conditioned_sync_substage_cycling"
        return [("sync_substage_cycling", "substage_cycling", "substage_cycling")]
    elseif row_id == "conditioned_sync_coordinate_generators"
        return [("sync_loop_advance", "loop_advance", "loop_advance"), ("sync_stage_progression", "stage_progression", "stage_progression"), ("sync_substage_cycling", "substage_cycling", "substage_cycling")]
    elseif row_id == "conditioned_async_coordinate_generators"
        return [("L_loop_advance", "loop_advance", "none"), ("R_loop_advance", "none", "loop_advance"), ("L_stage_progression", "stage_progression", "none"), ("R_stage_progression", "none", "stage_progression"), ("L_substage_cycling", "substage_cycling", "none"), ("R_substage_cycling", "none", "substage_cycling")]
    elseif row_id == "control_dissipative_substage_reset"
        return [("reset_both_substages", "reset", "reset")]
    end
    error("unknown row_id $(row_id)")
end

function apply_generator(cell_id::Int, spec)
    _, l_op, r_op = spec
    l_state = div(cell_id, PER_ENGINE)
    r_state = mod(cell_id, PER_ENGINE)
    if l_op == "reset" && r_op == "reset"
        l_loop, l_stage, _ = decode_engine(l_state)
        r_loop, r_stage, _ = decode_engine(r_state)
        return joint_id(engine_state_id(l_loop, l_stage, 0), engine_state_id(r_loop, r_stage, 0))
    end
    l_next = l_op == "none" ? l_state : apply_engine_op(l_state, l_op)
    r_next = r_op == "none" ? r_state : apply_engine_op(r_state, r_op)
    return joint_id(l_next, r_next)
end

function build_graph(row_id::String)
    specs = generator_specs(row_id)
    g = Graphs.SimpleDiGraph(JOINT_COUNT)
    edges = Any[]
    for src in 0:(JOINT_COUNT - 1)
        for spec in specs
            name, _, _ = spec
            dst = apply_generator(src, spec)
            Graphs.add_edge!(g, src + 1, dst + 1)
            push!(edges, Dict("src" => src, "dst" => dst, "generator" => name))
        end
    end
    comps_1 = Graphs.strongly_connected_components(g)
    comps = [sort([Int(v) - 1 for v in comp]) for comp in comps_1]
    sort!(comps, by = comp -> (length(comp), minimum(comp)))
    comp_id = Dict{Int, Int}()
    for (idx0, comp) in enumerate(comps)
        for cid in comp
            comp_id[cid] = idx0 - 1
        end
    end
    class_rows = Any[]
    terminal_ids = Int[]
    for (idx0, comp) in enumerate(comps)
        class_id = idx0 - 1
        comp_set = Set(comp)
        outgoing = Any[row for row in edges if (row["src"] in comp_set) && !(row["dst"] in comp_set)]
        terminal = isempty(outgoing)
        if terminal
            push!(terminal_ids, class_id)
        end
        push!(class_rows, Dict(
            "class_id" => class_id,
            "size" => length(comp),
            "terminal_closed" => terminal,
            "absent_exit_proof" => Dict("outgoing_edge_count" => length(outgoing), "checked_edge_count" => length(comp) * length(specs), "no_exit" => terminal),
        ))
    end
    signature = Dict(
        "state_count" => JOINT_COUNT,
        "edge_count" => length(edges),
        "scc_count" => length(class_rows),
        "terminal_class_count" => length(terminal_ids),
        "terminal_sizes" => sort([class_rows[id + 1]["size"] for id in terminal_ids]),
        "class_sizes" => sort([row["size"] for row in class_rows]),
    )
    Dict(
        "row_id" => row_id,
        "state_count" => JOINT_COUNT,
        "edge_count" => length(edges),
        "scc_count" => length(class_rows),
        "terminal_class_count" => length(terminal_ids),
        "terminal_class_ids" => terminal_ids,
        "terminal_classes" => [class_rows[id + 1] for id in terminal_ids],
        "partition_signature" => signature,
        "partition_signature_sha256" => stable_sha(signature),
    )
end

function z3_primary_no64(counts::Vector{Int}; erased_flip::Bool=false)::String
    values = copy(counts)
    if erased_flip
        push!(values, 64)
    end
    solver = Z3.Solver()
    clauses = Z3.Expr[]
    for (idx, value) in enumerate(values)
        count_var = Z3.IntVar("julia_primary_count_$(idx)")
        Z3.add(solver, count_var == Z3.IntVal(value))
        push!(clauses, count_var == Z3.IntVal(64))
    end
    Z3.add(solver, Z3.Or(clauses))
    return string(Z3.check(solver))
end

function build_result()
    primary_rows = [
        "source_sync_full_tick",
        "source_l_only_full_tick",
        "source_r_only_full_tick",
        "source_async_lr_union_full_tick",
        "source_all_interleavings_full_tick",
        "conditioned_sync_loop_advance",
        "conditioned_sync_stage_progression",
        "conditioned_sync_substage_cycling",
        "conditioned_sync_coordinate_generators",
        "conditioned_async_coordinate_generators",
    ]
    graphs = Dict(row => build_graph(row) for row in vcat(primary_rows, ["control_dissipative_substage_reset"]))
    counts = [graphs[row]["terminal_class_count"] for row in primary_rows]
    z3_verdict = z3_primary_no64(counts)
    z3_erased = z3_primary_no64(counts; erased_flip=true)
    capability = [
        Dict("receipt_id" => "julia_Graphs_1024_joint_partition", "tool" => "Graphs", "computed_what" => "1024-state joint graph SCCs and terminal class counts", "status" => "used"),
        Dict("receipt_id" => "julia_Z3_primary_no64_erased_flip", "tool" => "Z3", "computed_what" => "measured primary class-count absence of 64 with erased flip", "status" => "used"),
    ]
    tool_calls = [
        Dict(
            "receipt_id" => "julia_Graphs_1024_joint_partition",
            "tool" => "Graphs",
            "qualified_api/function" => "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.strongly_connected_components",
            "input_object" => "1024 joint fine states and generator-labelled transition rows",
            "output_object" => "terminal classes and class lattice counts",
            "positive_case" => "source-backed rows compute a 1024-state lattice",
            "negative/erased_control" => "dissipative reset merges states and is marked control-only",
            "boundary_case" => "sync full tick gives 32 offset classes",
            "demotion_condition" => "demote if 64 is obtained by partition intersection",
            "gates" => ["joint_partition", "anti_by_construction", "all_pass"],
        ),
        Dict(
            "receipt_id" => "julia_Z3_primary_no64_erased_flip",
            "tool" => "Z3",
            "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
            "input_object" => "measured primary terminal counts",
            "output_object" => "UNSAT primary 64-existence assertion and SAT erased flip",
            "positive_case" => "no primary row has 64 terminal classes",
            "negative/erased_control" => "injected erased 64 count flips to SAT",
            "boundary_case" => "control row may merge to 64 but is not primary",
            "demotion_condition" => "demote if solver checks only a hardcoded boolean",
            "gates" => ["proof", "erased_flip", "all_pass"],
        ),
    ]
    all_pass = (
        graphs["source_sync_full_tick"]["terminal_class_count"] == 32 &&
        graphs["source_l_only_full_tick"]["terminal_class_count"] == 32 &&
        graphs["source_r_only_full_tick"]["terminal_class_count"] == 32 &&
        graphs["source_async_lr_union_full_tick"]["terminal_class_count"] == 1 &&
        graphs["control_dissipative_substage_reset"]["terminal_class_count"] == 64 &&
        !(64 in counts) &&
        z3_verdict == "unsat" &&
        z3_erased == "sat"
    )
    Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "object_id" => "$(SIM_ID)_$(ENGINE)",
        "engine" => ENGINE,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => false,
        "generated_at" => now_z(),
        "seed_ledger" => Dict("rng" => "none", "deterministic_graph_order" => "l_state_then_r_state"),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "julia_project" => joinpath(ROOT, "system_v5", "julia_carrier", "Project.toml"),
        "packages_used" => ["Graphs", "Z3", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "package_versions" => Dict("julia" => string(VERSION), "Graphs" => string(pkgversion(Graphs)), "Z3" => string(pkgversion(Z3))),
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "capability_receipts" => capability,
        "tool_calls" => tool_calls,
        "one_to_one_tool_calls" => Dict("pass" => [row["receipt_id"] for row in capability] == [row["receipt_id"] for row in tool_calls]),
        "joint_graphs" => graphs,
        "primary_terminal_counts" => Dict(row => graphs[row]["terminal_class_count"] for row in primary_rows),
        "primary_64_level_count" => count(==(64), counts),
        "control_terminal_class_count" => graphs["control_dissipative_substage_reset"]["terminal_class_count"],
        "crossover_proofs" => Dict(
            "julia_z3" => Dict(
                "ran" => true,
                "load_bearing" => true,
                "verdict" => z3_verdict,
                "erased_flip_verdict" => z3_erased,
                "proof_row" => Dict(
                    "measured_primary_terminal_counts" => counts,
                    "erased_flip" => "append erased synthetic 64 count",
                    "asserted_precomputed_boolean" => false,
                ),
            ),
        ),
        "joint_signature_sha256" => stable_sha(Dict("primary_terminal_counts" => counts, "control_terminal_count" => graphs["control_dissipative_substage_reset"]["terminal_class_count"])),
        "all_pass" => all_pass,
    )
end

function main()
    mkpath(RESULT_DIR)
    payload = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => payload["all_pass"], "result_path" => rel(RESULT_PATH))))
    return payload["all_pass"] ? 0 : 1
end

exit(main())
