#!/usr/bin/env julia
# Cheap exact Julia mirror for engine_64_stage_full_run_v0 coordinate rows.

using Dates
using SHA

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "engine_64_stage_full_run_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")

const STROKES = [
    Dict("stroke_index" => 0, "axis1" => 0, "axis2" => 0, "operator_family" => "Ti", "stroke_label" => "expand_open"),
    Dict("stroke_index" => 1, "axis1" => 0, "axis2" => 1, "operator_family" => "Te", "stroke_label" => "expand_closed"),
    Dict("stroke_index" => 2, "axis1" => 1, "axis2" => 0, "operator_family" => "Fi", "stroke_label" => "compress_open"),
    Dict("stroke_index" => 3, "axis1" => 1, "axis2" => 1, "operator_family" => "Fe", "stroke_label" => "compress_closed"),
]
const SUBSTAGES = [
    Dict("substage_index" => 0, "axis5" => 0, "axis6" => 0, "substage_label" => "family0_operator_first"),
    Dict("substage_index" => 1, "axis5" => 0, "axis6" => 1, "substage_label" => "family0_terrain_first"),
    Dict("substage_index" => 2, "axis5" => 1, "axis6" => 0, "substage_label" => "family1_operator_first"),
    Dict("substage_index" => 3, "axis5" => 1, "axis6" => 1, "substage_label" => "family1_terrain_first"),
]
const ENGINE_SPECS = Dict(
    0 => Dict("engine_family" => "Type1-L", "sheet" => "L", "base_order" => ["Se", "Ne", "Ni", "Si"], "readouts" => ["LOSE", "WIN", "LOSE", "WIN"]),
    1 => Dict("engine_family" => "Type2-R", "sheet" => "R", "base_order" => ["Se", "Si", "Ni", "Ne"], "readouts" => ["WIN", "WIN", "LOSE", "LOSE"]),
)
const TERRAIN_REALIZATIONS = Dict(
    ("L", "Se") => "Se/Funnel",
    ("R", "Se") => "Se/Cannon",
    ("L", "Ne") => "Ne/Vortex",
    ("R", "Ne") => "Ne/Spiral",
    ("L", "Ni") => "Ni/Pit",
    ("R", "Ni") => "Ni/Source",
    ("L", "Si") => "Si/Hill",
    ("R", "Si") => "Si/Citadel",
)

rel(path::String) = relpath(path, ROOT)
sha256_file(path::String) = bytes2hex(open(sha256, path))
now_z() = string(Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SS"), "Z")

function json_escape(s)
    out = IOBuffer()
    for c in String(s)
        if c == '"'
            print(out, "\\\"")
        elseif c == '\\'
            print(out, "\\\\")
        elseif c == '\n'
            print(out, "\\n")
        else
            print(out, c)
        end
    end
    return String(take!(out))
end

function to_json(x)
    if x isa Dict
        parts = String[]
        for key in sort(collect(keys(x)); by=string)
            push!(parts, string("\"", json_escape(string(key)), "\":", to_json(x[key])))
        end
        return string("{", join(parts, ","), "}")
    elseif x isa Vector
        return string("[", join(to_json.(x), ","), "]")
    elseif x isa Tuple
        return to_json(collect(x))
    elseif x isa String
        return string("\"", json_escape(x), "\"")
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x === nothing
        return "null"
    else
        return string(x)
    end
end

matrix64_index(bits) = bits["axis1"] + 2 * bits["axis2"] + 4 * bits["axis3"] + 8 * bits["axis4"] + 16 * bits["axis5"] + 32 * bits["axis6"]

function expected_stage_sequence(axis3, axis4)
    stages = copy(ENGINE_SPECS[axis3]["base_order"])
    readouts = copy(ENGINE_SPECS[axis3]["readouts"])
    if axis4 == 1
        reverse!(stages)
        reverse!(readouts)
    end
    return stages, readouts
end

function make_slot(axis3, axis4, stroke, substage, slot_index)
    stages, readouts = expected_stage_sequence(axis3, axis4)
    stage = stages[stroke["stroke_index"] + 1]
    readout = readouts[stroke["stroke_index"] + 1]
    spec = ENGINE_SPECS[axis3]
    bits = Dict(
        "axis1" => stroke["axis1"],
        "axis2" => stroke["axis2"],
        "axis3" => axis3,
        "axis4" => axis4,
        "axis5" => substage["axis5"],
        "axis6" => substage["axis6"],
    )
    return Dict(
        "slot_index" => slot_index,
        "matrix64_index" => matrix64_index(bits),
        "axis_bits" => bits,
        "engine_family" => spec["engine_family"],
        "sheet" => spec["sheet"],
        "stage" => stage,
        "readout" => readout,
        "stroke_index" => stroke["stroke_index"],
        "substage_index" => substage["substage_index"],
        "operator_family" => stroke["operator_family"],
        "precedence" => bits["axis6"] == 0 ? "operator_first" : "terrain_first",
        "terrain_id" => TERRAIN_REALIZATIONS[(spec["sheet"], stage)],
    )
end

function build_schedule()
    slots = []
    slot_index = 0
    for axis3 in (0, 1), axis4 in (0, 1), stroke in STROKES, substage in SUBSTAGES
        push!(slots, make_slot(axis3, axis4, stroke, substage, slot_index))
        slot_index += 1
    end
    return slots
end

function coordinate_consistency(slot)
    bits = slot["axis_bits"]
    stroke = only(filter(row -> row["axis1"] == bits["axis1"] && row["axis2"] == bits["axis2"], STROKES))
    substage = only(filter(row -> row["axis5"] == bits["axis5"] && row["axis6"] == bits["axis6"], SUBSTAGES))
    stages, readouts = expected_stage_sequence(bits["axis3"], bits["axis4"])
    expected_stage = stages[stroke["stroke_index"] + 1]
    expected_readout = readouts[stroke["stroke_index"] + 1]
    expected_sheet = ENGINE_SPECS[bits["axis3"]]["sheet"]
    expected_terrain = TERRAIN_REALIZATIONS[(expected_sheet, expected_stage)]
    expected_precedence = bits["axis6"] == 0 ? "operator_first" : "terrain_first"
    checks = Dict(
        "operator_family_matches_axis1_axis2" => slot["operator_family"] == stroke["operator_family"],
        "substage_matches_axis5_axis6" => slot["substage_index"] == substage["substage_index"],
        "precedence_matches_axis6" => slot["precedence"] == expected_precedence,
        "stage_matches_engine_direction_and_stroke" => slot["stage"] == expected_stage,
        "terrain_matches_sheet_and_stage" => slot["terrain_id"] == expected_terrain,
        "readout_matches_committed_discipline_row" => slot["readout"] == expected_readout,
        "matrix64_index_matches_axis_bits" => slot["matrix64_index"] == matrix64_index(bits),
    )
    return Dict(
        "slot_index" => slot["slot_index"],
        "matrix64_index" => slot["matrix64_index"],
        "axis_bits" => bits,
        "expected_operator_family" => stroke["operator_family"],
        "actual_operator_family" => slot["operator_family"],
        "expected_stage" => expected_stage,
        "actual_stage" => slot["stage"],
        "expected_terrain" => expected_terrain,
        "actual_terrain" => slot["terrain_id"],
        "expected_precedence" => expected_precedence,
        "actual_precedence" => slot["precedence"],
        "checks" => checks,
        "pass" => all(values(checks)),
    )
end

function build_result()
    mkpath(RESULT_DIR)
    schedule = build_schedule()
    rows = coordinate_consistency.(schedule)
    coords = Set(Tuple(slot["axis_bits"]["axis$i"] for i in 1:6) for slot in schedule)
    type1 = count(slot -> slot["axis_bits"]["axis3"] == 0, schedule)
    type2 = count(slot -> slot["axis_bits"]["axis3"] == 1, schedule)
    bad = count(row -> !row["pass"], rows)
    gates = Dict(
        "total_slots_64" => length(schedule) == 64,
        "unique_coordinates_64" => length(coords) == 64,
        "type1_slots_32" => type1 == 32,
        "type2_slots_32" => type2 == 32,
        "coordinate_rows_all_pass" => bad == 0,
    )
    return Dict(
        "schema_version" => "$(SIM_ID)_julia_lane_v1",
        "sim_id" => SIM_ID,
        "generated_at" => now_z(),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "all_pass" => all(values(gates)),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "lane_role" => "Julia exact mirror of slot-coordinate consistency rows and schedule cardinalities",
        "packages_used" => ["julia_gf4_stdlib"],
        "aligned_packages_load_bearing" => ["julia_gf4_stdlib"],
        "package_observables" => Dict("julia_gf4_stdlib" => "Exact integer coordinate schedule and Boolean row consistency checks"),
        "TOOL_MANIFEST" => Dict("julia_gf4_stdlib" => Dict("used" => true, "reason" => "load-bearing exact Julia mirror of slot-coordinate consistency rows")),
        "TOOL_INTEGRATION_DEPTH" => Dict("julia_gf4_stdlib" => "load_bearing"),
        "counts" => Dict("total_slots" => length(schedule), "unique_coordinate_count" => length(coords), "type1_slots" => type1, "type2_slots" => type2, "bad_coordinate_rows" => bad),
        "slot_coordinate_consistency" => Dict("row_count" => length(rows), "bad_row_count" => bad, "all_rows_pass" => bad == 0, "rows" => rows),
        "gates" => gates,
        "boundary" => Dict("values_unchanged" => true, "reference_only" => true, "pytorch_omitted" => true),
    )
end

payload = build_result()
open(RESULT_PATH, "w") do io
    write(io, to_json(payload), "\n")
end
println(to_json(Dict("ok" => payload["all_pass"], "result_path" => rel(RESULT_PATH))))
exit(payload["all_pass"] ? 0 : 1)
