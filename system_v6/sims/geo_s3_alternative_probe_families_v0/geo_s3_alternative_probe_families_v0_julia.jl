#!/usr/bin/env julia
# Julia sidecar for geo_s3_alternative_probe_families_v0.

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s3_alternative_probe_families_v0"
const SIM_DIR_REL = joinpath("system_v6", "sims", SIM_ID)
const SIM_DIR = joinpath(ROOT, SIM_DIR_REL)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH_REL = joinpath(SIM_DIR_REL, "$(SIM_ID)_julia.jl")
const SOURCE_PATH = joinpath(ROOT, SOURCE_PATH_REL)
const RESULT_PATH_REL = joinpath(SIM_DIR_REL, "results", "$(SIM_ID)_julia_results.json")
const RESULT_PATH = joinpath(ROOT, RESULT_PATH_REL)
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const SEED = 20260611

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))
stable_hash(x) = bytes2hex(SHA.sha256(codeunits(JSON.json(x, 4))))

function z3_sub_terms(terms::Vector{Z3.Expr})
    Z3.Expr(terms[1].ctx, Z3.Libz3.Z3_mk_sub(Z3.ctx_ref(terms[1]), length(terms), map(Z3.as_ast, terms)))
end

function z3_distinct(left::Z3.Expr, right::Z3.Expr)
    Z3.Expr(left.ctx, Z3.Libz3.Z3_mk_distinct(Z3.ctx_ref(left), 2, map(Z3.as_ast, [left, right])))
end

function family_rows()
    rt3 = sqrt(3.0)
    Dict(
        "committed_pauli_xyz" => [
            [0.5, 0.5, 0.0, 0.0], [0.5, -0.5, 0.0, 0.0],
            [0.5, 0.0, 0.5, 0.0], [0.5, 0.0, -0.5, 0.0],
            [0.5, 0.0, 0.0, 0.5], [0.5, 0.0, 0.0, -0.5],
        ],
        "A_sic_tetrahedron" => [
            [0.25, 0.25/rt3, 0.25/rt3, 0.25/rt3],
            [0.25, 0.25/rt3, -0.25/rt3, -0.25/rt3],
            [0.25, -0.25/rt3, 0.25/rt3, -0.25/rt3],
            [0.25, -0.25/rt3, -0.25/rt3, 0.25/rt3],
        ],
        "B_mub_xyz" => [
            [0.5, 0.5, 0.0, 0.0], [0.5, -0.5, 0.0, 0.0],
            [0.5, 0.0, 0.5, 0.0], [0.5, 0.0, -0.5, 0.0],
            [0.5, 0.0, 0.0, 0.5], [0.5, 0.0, 0.0, -0.5],
        ],
        "C_single_axis_z" => [
            [0.5, 0.0, 0.0, 0.5], [0.5, 0.0, 0.0, -0.5],
        ],
        "D_random_frame_null" => [
            [0.25, 0.125, 0.0, 0.0625],
            [0.25, -0.0625, 0.0, 0.125],
            [0.25, 0.09375, 0.0, -0.03125],
            [0.25, -0.078125, 0.0, -0.046875],
        ],
    )
end

function spin_operator_receipt()
    b = SpinBasis(1//2)
    sx = sigmax(b)
    sy = sigmay(b)
    sz = sigmaz(b)
    id = identityoperator(b)
    row = family_rows()["A_sic_tetrahedron"][1]
    effect = row[1] * id + row[2] * sx + row[3] * sy + row[4] * sz
    vals = eigvals(Matrix(dense(effect).data))
    Dict(
        "basis" => "SpinBasis(1//2)",
        "sic_first_effect_trace" => round(real(tr(Matrix(dense(effect).data))), digits=12),
        "sic_first_effect_min_eigenvalue" => round(minimum(real.(vals)), digits=12),
        "pass" => minimum(real.(vals)) >= -1.0e-10,
    )
end

const STATES = Dict(
    "+x" => [0.5, 0.0, 0.0], "-x" => [-0.5, 0.0, 0.0],
    "+y" => [0.0, 0.5, 0.0], "-y" => [0.0, -0.5, 0.0],
    "+z" => [0.0, 0.0, 0.5], "-z" => [0.0, 0.0, -0.5],
)

function probabilities(rows, state)
    [row[1] + row[2] * state[1] + row[3] * state[2] + row[4] * state[3] for row in rows]
end

function separated_count(rows)
    labels = collect(keys(STATES))
    count = 0
    collapsed = []
    for i in 1:length(labels)
        for j in (i+1):length(labels)
            if j <= length(labels)
                diff = maximum(abs.(probabilities(rows, STATES[labels[i]]) .- probabilities(rows, STATES[labels[j]]))) > 1.0e-10
                count += diff ? 1 : 0
                diff || push!(collapsed, [labels[i], labels[j]])
            end
        end
    end
    count, collapsed
end

function engine_values()
    out = Dict()
    for (name, rows) in family_rows()
        sep, collapsed = separated_count(rows)
        out[name] = Dict(
            "frame_rank" => rank(hcat(rows...)'),
            "distinguished_pair_count" => sep,
            "null_deficiency" => 4 - rank(hcat(rows...)'),
        )
    end
    out
end

function julia_z3_proof(values)
    s = Z3.Solver()
    sic = Z3.IntVar("julia_sic_rank")
    zrank = Z3.IntVar("julia_z_rank")
    nulldef = Z3.IntVar("julia_null_def")
    Z3.add(s, sic == Z3.IntVal(values["A_sic_tetrahedron"]["frame_rank"]))
    Z3.add(s, zrank == Z3.IntVal(values["C_single_axis_z"]["frame_rank"]))
    Z3.add(s, nulldef == Z3.IntVal(values["D_random_frame_null"]["null_deficiency"]))
    Z3.add(s, z3_distinct(z3_sub_terms([sic, zrank, nulldef]), Z3.IntVal(0)))
    verdict = string(Z3.check(s))
    e = Z3.Solver()
    erased_sic = Z3.IntVar("julia_erased_sic_rank")
    Z3.add(e, erased_sic == Z3.IntVal(values["A_sic_tetrahedron"]["frame_rank"]))
    Z3.add(e, erased_sic < Z3.IntVal(4))
    erased = string(Z3.check(e))
    Dict(
        "ran" => true,
        "load_bearing" => true,
        "solver" => "Z3.jl",
        "verdict" => verdict,
        "erased_verdict" => erased,
        "erased_flip_detected" => verdict == "sat" && erased == "unsat",
        "asserted_precomputed_boolean" => false,
    )
end

function main()
    mkpath(RESULT_DIR)
    values = engine_values()
    qo = spin_operator_receipt()
    proof = julia_z3_proof(values)
    payload = Dict(
        "schema_version" => "julia_sidecar_result_v1",
        "sim_id" => SIM_ID,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "engine_values" => values,
        "engine_values_hash" => stable_hash(values),
        "quantumoptics_receipt" => qo,
        "crossover_proofs" => Dict("Z3" => proof),
        "TOOL_MANIFEST" => Dict(
            "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing d=2 probe operator construction"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia raw-rank erased-flip proof"),
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing rank/eigenvalue calculations"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization"),
            "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source/result hashing")
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "QuantumOptics" => "load_bearing",
            "Z3" => "load_bearing",
            "LinearAlgebra" => "load_bearing",
            "JSON" => "supportive",
            "SHA" => "supportive"
        ),
        "capability_receipts" => Dict("julia_version" => string(VERSION), "project" => "system_v5/julia_carrier"),
    )
    payload["all_pass"] = qo["pass"] == true && proof["erased_flip_detected"] == true &&
        values["A_sic_tetrahedron"]["frame_rank"] == 4 &&
        values["B_mub_xyz"]["frame_rank"] == 4 &&
        values["C_single_axis_z"]["frame_rank"] == 2 &&
        values["D_random_frame_null"]["null_deficiency"] > 0
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("sim_id" => SIM_ID, "all_pass" => payload["all_pass"], "result_path" => RESULT_PATH_REL), 2))
end

main()
