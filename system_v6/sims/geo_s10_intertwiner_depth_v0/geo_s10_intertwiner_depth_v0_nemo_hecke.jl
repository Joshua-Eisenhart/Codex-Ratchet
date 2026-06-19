#!/usr/bin/env julia

using Dates
using Hecke
using JSON3
using Nemo
using SHA

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s10_intertwiner_depth_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_nemo_hecke.jl")
const RESULT_PATH = joinpath(SIM_DIR, "results", "$(SIM_ID)_nemo_hecke_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false

function rel(path::AbstractString)
    return relpath(path, ROOT)
end

function sha256_file(path::AbstractString)
    return bytes2hex(open(sha256, path))
end

function matrix_key(matrix_value)
    return join([string(matrix_value[i, j]) for i in 1:2 for j in 1:2], ",")
end

function mat_order(matrix_value, identity_matrix; limit::Int=12)
    acc = identity_matrix
    for order in 1:limit
        acc = acc * matrix_value
        if acc == identity_matrix
            return order
        end
    end
    return 0
end

function gl2_over_gf2_row()
    field = GF(2)
    entries = [field(0), field(1)]
    matrices = []
    singular = []
    for a in entries, b in entries, c in entries, d in entries
        matrix_value = matrix(field, 2, 2, [a, b, c, d])
        if det(matrix_value) != field(0)
            push!(matrices, matrix_value)
        else
            push!(singular, matrix_value)
        end
    end
    identity_matrix = matrix(field, 2, 2, [field(1), field(0), field(0), field(1)])
    cycle = matrix(field, 2, 2, [field(0), field(1), field(1), field(1)])
    transposition = matrix(field, 2, 2, [field(0), field(1), field(1), field(0)])
    inverse_cycle = cycle^2
    return Dict(
        "field" => "GF(2)",
        "all_2x2_count" => 16,
        "gl2_2_order" => length(matrices),
        "singular_count" => length(singular),
        "cycle_matrix" => matrix_key(cycle),
        "cycle_order" => mat_order(cycle, identity_matrix),
        "transposition_matrix" => matrix_key(transposition),
        "transposition_order" => mat_order(transposition, identity_matrix),
        "s3_relation_TCT_equals_C_inverse" => transposition * cycle * transposition == inverse_cycle,
        "determinant_excludes_singular" => all(det(m) == field(0) for m in singular),
        "pass" => length(matrices) == 6 && length(singular) == 10 && cycle^3 == identity_matrix &&
                  transposition^2 == identity_matrix && transposition * cycle * transposition == inverse_cycle
    )
end

function build_payload()
    row = gl2_over_gf2_row()
    payload = Dict(
        "schema_version" => "geo_s10_intertwiner_depth_nemo_hecke_result_v1",
        "sim_id" => SIM_ID,
        "object_id" => SIM_ID,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "packages_used" => ["Nemo", "Hecke", "JSON3", "SHA"],
        "runtime" => Dict(
            "julia_version" => string(VERSION),
            "active_project" => Base.active_project(),
            "required_project" => joinpath(ROOT, "system_v6", "optional", "nemo_hecke", "Project.toml"),
            "load_path" => join(Base.LOAD_PATH, ":")
        ),
        "outer_s3_row" => row,
        "claim_path_tools" => ["Nemo"],
        "TOOL_MANIFEST" => Dict(
            "Nemo" => Dict("tried" => true, "used" => true, "reason" => "load-bearing GF(2) matrix enumeration for GL(2,2) as S3 sanity row"),
            "Hecke" => Dict("tried" => true, "used" => true, "reason" => "supportive optional-project import; not claim-bearing"),
            "julia_stdlib" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization and hashing")
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Nemo" => "load_bearing",
            "Hecke" => "supportive",
            "julia_stdlib" => "supportive"
        ),
        "tool_calls" => [
            Dict(
                "tool" => "Nemo",
                "qualified_api/function" => "Nemo.GF/matrix/det",
                "input_object" => "all 2x2 matrices over GF(2)",
                "output_object" => row,
                "positive_case" => "GL(2,2) order 6 with order-3 and order-2 generators",
                "negative/erased_control" => "determinant-zero matrices excluded; singular count 10",
                "boundary_case" => "finite S3 sanity row only",
                "demotion_condition" => "demote if active project is not system_v6/optional/nemo_hecke or GL(2,2) order drifts",
                "gates" => ["nemo_s3_row", "all_pass"],
                "load_bearing" => true
            )
        ],
        "all_pass" => row["pass"] == true && Base.active_project() == joinpath(ROOT, "system_v6", "optional", "nemo_hecke", "Project.toml")
    )
    return payload
end

function main()
    payload = build_payload()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON3.pretty(io, payload)
        write(io, "\n")
    end
    println(JSON3.write(Dict("ok" => payload["all_pass"], "mode" => "nemo_hecke", "result_path" => rel(RESULT_PATH))))
    return payload["all_pass"] ? 0 : 1
end

exit(main())
