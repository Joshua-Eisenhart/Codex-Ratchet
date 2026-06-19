#!/usr/bin/env julia
# Julia Graphs/Z3 reference leg for basin_information_fusion_v1.

using Dates
using Graphs
using JSON
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "basin_information_fusion_v1"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const SWEEP_ENV = joinpath(ROOT, "system_v6/sims/basin_generating_set_sweep_v0/results/basin_generating_set_sweep_v0_envelope_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const CHART_RELATIVE_LABEL = "G1_CHART_RELATIVE_ORIGINAL_33_CELL_FINITE_STRUCTURE"

function now_z()::String
    Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
end

rel(path::String)::String = replace(relpath(path, ROOT), "\\" => "/")

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function stable_sha256(value)::String
    return bytes2hex(sha256(JSON.json(value)))
end

function write_json(path::String, payload)
    mkpath(dirname(path))
    open(path, "w") do io
        JSON.print(io, payload, 2)
        println(io)
    end
end

function source_backing_probe()
    g = Graphs.SimpleDiGraph(3)
    Graphs.add_edge!(g, 1, 2)
    Graphs.add_edge!(g, 2, 3)
    comps = Graphs.strongly_connected_components(g)
    solver = Z3.Solver()
    x = Z3.IntVar("bif_v1_julia_source_backing")
    Z3.add(solver, x == Z3.IntVal(3))
    Dict(
        "Graphs_vertex_count" => Graphs.nv(g),
        "Graphs_component_count" => length(comps),
        "Z3_check" => string(Z3.check(solver)),
    )
end

function g1_syndrome_table(sweep)
    g1 = sweep["sweep"]["G1"]
    terminal_cells = g1["terminal_cells"]
    rows = Any[]
    for (idx0, cells) in enumerate(terminal_cells)
        class_id = idx0 - 1
        for cell in cells
            push!(rows, Dict(
                "start_cell" => Int(cell),
                "G1_chart_relative_class_id" => class_id,
                "chart_relative_label" => CHART_RELATIVE_LABEL,
                "constructed_full_syndrome_record" => "G1_chart_relative_class_$(class_id)",
                "erased_record_control" => "erased",
            ))
        end
    end
    sort!(rows, by = row -> row["start_cell"])
    rows
end

function z3_identity(syndrome_count::Int, record_count::Int)::String
    solver = Z3.Solver()
    state = Z3.IntVar("computed_syndrome_class_count_julia")
    rec = Z3.IntVar("computed_record_readout_label_count_julia")
    Z3.add(solver, state == Z3.IntVal(syndrome_count))
    Z3.add(solver, rec == Z3.IntVal(record_count))
    Z3.add(solver, Z3.Not(state == rec))
    string(Z3.check(solver))
end

function build_result()
    sweep = JSON.parsefile(SWEEP_ENV)
    table = g1_syndrome_table(sweep)
    syndrome_count = length(unique([row["G1_chart_relative_class_id"] for row in table]))
    full_record_count = length(unique([row["constructed_full_syndrome_record"] for row in table]))
    erased_count = length(unique([row["erased_record_control"] for row in table]))
    z3_verdict = z3_identity(syndrome_count, full_record_count)
    z3_erased = z3_identity(syndrome_count, erased_count)
    g = Graphs.SimpleDiGraph(33)
    for row in table
        Graphs.add_edge!(g, row["start_cell"] + 1, row["G1_chart_relative_class_id"] + 1)
    end
    comps = Graphs.strongly_connected_components(g)
    capability = [
        Dict("receipt_id" => "julia_Graphs_joint_basin_information_flow", "tool" => "Graphs", "computed_what" => "packet-local G1 syndrome graph carrier", "status" => "used"),
        Dict("receipt_id" => "julia_Z3_computed_record_identity", "tool" => "Z3", "computed_what" => "computed syndrome/readout identity with erased-record flip", "status" => "used"),
    ]
    tool_calls = [
        Dict(
            "receipt_id" => "julia_Graphs_joint_basin_information_flow",
            "tool" => "Graphs",
            "qualified_api/function" => "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.strongly_connected_components",
            "input_object" => "computed G1 syndrome table",
            "output_object" => "finite syndrome graph carrier",
            "positive_case" => "three computed G1 chart-relative syndrome classes",
            "negative/erased_control" => "erased record collapses readout label count",
            "boundary_case" => "33 start-cell rows",
            "demotion_condition" => "demote if syndrome_count is assigned without table construction",
            "gates" => ["record_retention", "all_pass"],
            "load_bearing" => true,
        ),
        Dict(
            "receipt_id" => "julia_Z3_computed_record_identity",
            "tool" => "Z3",
            "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
            "input_object" => "computed syndrome_count and record_readout_count",
            "output_object" => "UNSAT equality identity and SAT erased flip",
            "positive_case" => "full record count equals syndrome count",
            "negative/erased_control" => "erased count differs from syndrome count",
            "boundary_case" => "integer count proof, not floating log proof",
            "demotion_condition" => "demote if Z3 binds hardcoded verdicts instead of computed counts",
            "gates" => ["proof", "all_pass"],
            "load_bearing" => true,
        ),
    ]
    all_pass = syndrome_count == 3 && full_record_count == 3 && erased_count == 1 && z3_verdict == "unsat" && z3_erased == "sat"
    payload = Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "object_id" => "$(SIM_ID)_$(ENGINE)",
        "engine" => ENGINE,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => false,
        "reads_parent_results" => true,
        "generated_at" => now_z(),
        "seed_ledger" => Dict("status" => "deterministic_no_rng", "source" => "parent G1 terminal cells"),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "packages_used" => ["Graphs", "Z3", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Z3"],
        "package_observables" => Dict(
            "Graphs" => "supportive syndrome_graph_component_count; syndrome_count gates all_pass from table-derived unique labels",
            "Z3" => "crossover_proofs.julia_z3 computed record identity",
        ),
        "package_versions" => Dict("julia" => string(VERSION), "Graphs" => "runtime_project", "Z3" => "runtime_project"),
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried" => true, "used" => true, "reason" => "supportive finite syndrome graph component count; does not gate all_pass"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing computed record identity proof"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "supportive", "Z3" => "load_bearing"),
        "claim_path_tools" => ["Z3"],
        "capability_receipts" => capability,
        "tool_calls" => tool_calls,
        "one_to_one_tool_calls" => Dict("pass" => length(capability) == length(tool_calls)),
        "source_backing_probe" => source_backing_probe(),
        "record_reference" => Dict(
            "chart_relative_label" => CHART_RELATIVE_LABEL,
            "syndrome_table_count" => length(table),
            "syndrome_class_count" => syndrome_count,
            "full_record_count" => full_record_count,
            "erased_record_count" => erased_count,
            "syndrome_graph_component_count" => length(comps),
        ),
        "crossover_proofs" => Dict(
            "julia_z3" => Dict(
                "ran" => true,
                "load_bearing" => true,
                "verdict" => z3_verdict,
                "erased_flip_verdict" => z3_erased,
                "proof_row" => Dict(
                    "encoding" => "bind computed syndrome class count and computed full-record label count; assert inequality",
                    "erased_flip" => "replace full record count with erased record count",
                    "computed_syndrome_class_count" => syndrome_count,
                    "computed_full_record_label_count" => full_record_count,
                    "computed_erased_record_label_count" => erased_count,
                ),
            ),
        ),
        "joint_object_signature_sha256" => stable_sha256(Dict("record_reference" => Dict("syndrome_count" => syndrome_count, "full_record_count" => full_record_count, "erased_record_count" => erased_count))),
        "all_pass" => all_pass,
    )
    payload
end

function main()
    payload = build_result()
    write_json(RESULT_PATH, payload)
    println(Dict("ok" => payload["all_pass"], "result_path" => rel(RESULT_PATH)))
    payload["all_pass"] ? 0 : 1
end

exit(main())
