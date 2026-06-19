#!/usr/bin/env julia

using Graphs
using JSON
using SHA
using Z3
using Dates

const SIM_ID = "z4_syndrome_record_v0"
const ROOT = normpath(joinpath(abspath(@__DIR__), "..", "..", ".."))
const PACKET = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT = joinpath(PACKET, "results", "$(SIM_ID)_julia_results.json")
const SOURCE = joinpath(PACKET, "$(SIM_ID)_julia.jl")
const LN2 = log(2.0)

function rel(path::AbstractString)
    normalized = normpath(abspath(path))
    prefix = endswith(ROOT, "/") ? ROOT : ROOT * "/"
    return startswith(normalized, prefix) ? normalized[length(prefix)+1:end] : normalized
end

function sha256_file(path::AbstractString)
    return bytes2hex(SHA.sha256(read(path)))
end

function entropy_from_counts(counts::Vector{Int})
    total = sum(counts)
    entropy = 0.0
    for count in counts
        if count > 0
            p = count / total
            entropy -= p * log(p)
        end
    end
    return Dict(
        "entropy_type" => "finite_counting_entropy_nats",
        "log_base" => "e",
        "counts" => counts,
        "entropy_exact" => length(filter(>(0), counts)) == 4 ? "log(4)" : length(filter(>(0), counts)) == 2 ? "log(2)" : "0",
        "entropy_nats" => entropy,
        "entropy_log2_coefficient" => round(Int, entropy / LN2),
        "code_path_id" => "julia_count_distribution_to_shannon_entropy",
    )
end

function counts_from_rows(rows; key)
    counts = Dict{Any,Int}()
    for row in rows
        value = key(row)
        counts[value] = get(counts, value, 0) + 1
    end
    return sort(collect(values(counts)))
end

function build_table()
    base_states = ["z_plus", "z_minus", "x_plus", "x_minus", "y_plus", "y_minus"]
    rows = Vector{Dict{String,Any}}()
    for (orbit_index0, orbit_id) in enumerate(base_states)
        orbit_index = orbit_index0 - 1
        for syndrome in 0:3
            push!(rows, Dict(
                "representative_id" => "$(orbit_id)::phase_$(syndrome)",
                "orbit_id" => orbit_id,
                "orbit_index" => orbit_index,
                "quotient_output" => "orbit::$(orbit_id)",
                "syndrome" => syndrome,
                "syndrome_bits" => string(syndrome, base=2, pad=2),
                "representative_code" => orbit_index * 4 + syndrome,
                "generator" => "alpha += pi/2",
            ))
        end
    end
    return rows
end

function preimage_loss_graph(rows; identity::Bool=false)
    quotient_count = identity ? length(rows) : 6
    representative_count = length(rows)
    graph = Graphs.SimpleDiGraph(quotient_count + representative_count)
    groups = Dict{String,Vector{String}}()
    for (idx, row) in enumerate(rows)
        qnode = identity ? idx : Int(row["orbit_index"]) + 1
        rnode = quotient_count + idx
        Graphs.add_edge!(graph, qnode, rnode)
        key = identity ? row["representative_id"] : row["quotient_output"]
        if !haskey(groups, key)
            groups[key] = String[]
        end
        push!(groups[key], row["representative_id"])
    end
    counts = sort([Graphs.outdegree(graph, node) for node in 1:quotient_count if Graphs.outdegree(graph, node) > 0])
    total = sum(counts)
    loss = sum((count / total) * log(count) for count in counts)
    return Dict(
        "entropy_type" => "finite_counting_entropy_nats",
        "log_base" => "e",
        "preimage_counts" => counts,
        "state_loss_exact" => all(==(4), counts) ? "log(4)" : all(==(1), counts) ? "0" : "computed_mixed",
        "state_loss_without_record_nats" => loss,
        "state_loss_log2_coefficient" => round(Int, loss / LN2),
        "code_path_id" => "Graphs.SimpleDiGraph_outdegree_preimage_counts_to_average_log_fiber_size",
        "graph_receipt" => Dict(
            "nv" => Graphs.nv(graph),
            "ne" => Graphs.ne(graph),
            "quotient_count" => quotient_count,
            "representative_count" => representative_count,
        ),
        "preimage_table" => groups,
    )
end

function reconstruction(rows; shift::Int=0)
    failures = 0
    recovered_sample = Int[]
    for row in rows
        recovered = Int(row["orbit_index"]) * 4 + mod(Int(row["syndrome"]) + shift, 4)
        push!(recovered_sample, recovered)
        if recovered != Int(row["representative_code"])
            failures += 1
        end
    end
    return Dict(
        "syndrome_shift" => shift,
        "checked_count" => length(rows),
        "failure_count" => failures,
        "failure_rate" => failures / length(rows),
        "bit_exact_roundtrip" => failures == 0,
        "recovered_code_sample" => recovered_sample[1:min(end, 8)],
    )
end

function quotient_alone(rows)
    counts = Dict{String,Int}()
    for row in rows
        counts[row["quotient_output"]] = get(counts, row["quotient_output"], 0) + 1
    end
    ambiguity = maximum(values(counts))
    return Dict(
        "computed_ambiguity" => ambiguity,
        "unique_reconstruction_possible" => ambiguity == 1,
        "reconstruction_fails" => ambiguity > 1,
        "ambiguities" => sort(collect(values(counts))),
    )
end

function stable_hash(row)
    return bytes2hex(SHA.sha256(JSON.json(row)))
end

function conservation_rows(rows)
    full_loss = preimage_loss_graph(rows)
    full_record = entropy_from_counts(counts_from_rows(rows; key=row -> row["syndrome"]))
    erased_record = entropy_from_counts(counts_from_rows(rows; key=_row -> "erased"))
    partial_record = entropy_from_counts(counts_from_rows(rows; key=row -> div(Int(row["syndrome"]), 2)))
    trivial_loss = preimage_loss_graph(rows; identity=true)
    trivial_record = entropy_from_counts(counts_from_rows(rows; key=_row -> "trivial"))

    function row(name, loss, record)
        defect = loss["state_loss_without_record_nats"] - record["entropy_nats"]
        out = Dict(
            "regime" => name,
            "state_loss_without_record_nats" => loss["state_loss_without_record_nats"],
            "record_retained_nats" => record["entropy_nats"],
            "computed_defect_nats" => defect,
            "state_loss_log2_coefficient" => loss["state_loss_log2_coefficient"],
            "record_log2_coefficient" => record["entropy_log2_coefficient"],
            "defect_log2_coefficient" => round(Int, defect / LN2),
            "typed_entropy_label" => "finite_counting_entropy_nats",
            "loss_code_path_id" => loss["code_path_id"],
            "record_code_path_id" => record["code_path_id"],
            "different_code_paths" => loss["code_path_id"] != record["code_path_id"],
        )
        out["row_hash"] = stable_hash(Dict("regime" => name, "loss" => out["state_loss_log2_coefficient"], "record" => out["record_log2_coefficient"], "defect" => out["defect_log2_coefficient"]))
        return out
    end

    return Dict(
        "positive" => row("full_record", full_loss, full_record),
        "negative_erased_record" => row("erased_record", full_loss, erased_record),
        "negative_partial_record" => row("partial_record_one_bit", full_loss, partial_record),
        "boundary_trivial_quotient" => row("trivial_quotient", trivial_loss, trivial_record),
        "source_rows" => Dict(
            "full_loss" => full_loss,
            "full_record" => full_record,
            "erased_record" => erased_record,
            "partial_record" => partial_record,
            "trivial_loss" => trivial_loss,
            "trivial_record" => trivial_record,
        ),
    )
end

function z3_add(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0)
    return Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_prove(row)
    solver = Z3.Solver()
    loss = Z3.IntVar("loss")
    record = Z3.IntVar("record")
    Z3.add(solver, loss == Z3.IntVal(row["state_loss_log2_coefficient"]))
    Z3.add(solver, record == Z3.IntVal(row["record_log2_coefficient"]))
    Z3.add(solver, Z3.Not(loss == record))
    return Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "load_bearing" => true,
        "verdict" => string(Z3.check(solver)),
        "bound_values" => Dict(
            "loss_log2_coefficient" => row["state_loss_log2_coefficient"],
            "record_log2_coefficient" => row["record_log2_coefficient"],
            "defect_log2_coefficient" => row["defect_log2_coefficient"],
        ),
    )
end

function main()
    rows = build_table()
    regimes = conservation_rows(rows)
    proofs = Dict(
        "full_record" => z3_prove(regimes["positive"]),
        "erased_record_control" => z3_prove(regimes["negative_erased_record"]),
        "partial_record_control" => z3_prove(regimes["negative_partial_record"]),
        "trivial_quotient_boundary" => z3_prove(regimes["boundary_trivial_quotient"]),
    )
    controls = Dict(
        "erased_record" => regimes["negative_erased_record"],
        "partial_record_one_bit" => regimes["negative_partial_record"],
        "shuffled_syndrome" => reconstruction(rows; shift=1),
        "trivial_quotient" => regimes["boundary_trivial_quotient"],
    )
    hashes = Set([
        regimes["positive"]["row_hash"],
        regimes["negative_erased_record"]["row_hash"],
        regimes["negative_partial_record"]["row_hash"],
        regimes["boundary_trivial_quotient"]["row_hash"],
    ])
    all_pass = (
        length(rows) == 24 &&
        regimes["positive"]["different_code_paths"] == true &&
        regimes["positive"]["defect_log2_coefficient"] == 0 &&
        regimes["negative_erased_record"]["defect_log2_coefficient"] == 2 &&
        regimes["negative_partial_record"]["defect_log2_coefficient"] == 1 &&
        regimes["boundary_trivial_quotient"]["state_loss_log2_coefficient"] == 0 &&
        reconstruction(rows)["bit_exact_roundtrip"] == true &&
        quotient_alone(rows)["computed_ambiguity"] == 4 &&
        controls["shuffled_syndrome"]["failure_rate"] == 1.0 &&
        length(hashes) == 4 &&
        proofs["full_record"]["verdict"] == "unsat" &&
        proofs["erased_record_control"]["verdict"] == "sat" &&
        proofs["partial_record_control"]["verdict"] == "sat"
    )
    payload = Dict(
        "schema_version" => "$(SIM_ID)_julia_leg_v1",
        "sim_id" => SIM_ID,
        "object_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_graphs_z3_z4_syndrome_record_leg",
        "generated_at" => string(Dates.now(Dates.UTC)),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "source_path" => rel(SOURCE),
        "source_sha256" => sha256_file(SOURCE),
        "result_path" => rel(RESULT),
        "julia_project" => Base.active_project(),
        "reads_peer_result" => false,
        "packages_used" => ["Graphs", "Z3", "JSON", "SHA"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "package_observables" => Dict(
            "Graphs" => "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.outdegree quotient preimage counts",
            "Z3" => "Z3.Solver/Z3.add/Z3.check over computed log2 coefficients",
        ),
        "claim_path_tools" => ["Graphs", "Z3"],
        "syndrome_table" => rows,
        "regimes" => regimes,
        "controls" => controls,
        "reconstruction" => Dict("with_quotient_and_syndrome" => reconstruction(rows), "quotient_alone" => quotient_alone(rows)),
        "crossover_proofs" => Dict("julia_z3" => proofs),
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("used" => true, "reason" => "load-bearing quotient-to-representative graph preimage counts"),
            "Z3" => Dict("used" => true, "reason" => "load-bearing SMT control over computed coefficients"),
            "JSON" => Dict("used" => true, "reason" => "structured result serialization"),
            "SHA" => Dict("used" => true, "reason" => "supportive source hashing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "Z3" => "load_bearing", "JSON" => "supportive", "SHA" => "supportive"),
        "tool_calls" => [
            Dict(
                "tool" => "Graphs",
                "qualified_api/function" => "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.outdegree",
                "input_object" => "Z4 quotient output to representative incidence table",
                "output_object" => "preimage counts for state_loss_without_record",
                "positive_case" => "all six quotient classes have four representatives",
                "negative/erased_control" => "same loss paired with erased or partial syndrome record",
                "boundary_case" => "identity quotient has preimage counts all one",
                "demotion_condition" => "demote if graph route is replaced by literal counts",
                "gates" => ["state_loss_without_record", "all_pass"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.add/Z3.check",
                "input_object" => "computed log2 coefficients",
                "output_object" => "UNSAT full conservation and SAT erased/partial controls",
                "positive_case" => "full record closes ln4 loss",
                "negative/erased_control" => "erased and partial records do not close the zero-defect equation",
                "boundary_case" => "trivial quotient has zero loss",
                "demotion_condition" => "demote if solver does not bind computed rows",
                "gates" => ["crossover_proofs", "all_pass"],
            ),
        ],
        "all_pass" => all_pass,
    )
    mkpath(dirname(RESULT))
    open(RESULT, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => all_pass, "result_path" => rel(RESULT))))
    return all_pass ? 0 : 1
end

exit(main())
