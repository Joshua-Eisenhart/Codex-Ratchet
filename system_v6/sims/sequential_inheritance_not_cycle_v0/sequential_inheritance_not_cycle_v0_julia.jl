#!/usr/bin/env julia

using Dates
using Graphs
using JSON
using SHA
using Z3

const SIM_ID = "sequential_inheritance_not_cycle_v0"
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

function stable_hash(value)
    return bytes2hex(SHA.sha256(JSON.json(value)))
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
        "entropy_nats" => entropy,
        "entropy_log2_coefficient" => round(Int, entropy / LN2),
        "code_path_id" => "julia_distribution_counts_to_shannon_entropy",
    )
end

function parent_rows()
    orbits = [
        ("z_plus", "axis_z", 0),
        ("z_minus", "axis_z", 1),
        ("x_plus", "axis_x", 0),
        ("x_minus", "axis_x", 1),
        ("y_plus", "axis_y", 0),
        ("y_minus", "axis_y", 1),
    ]
    phases = [(0, "1"), (1, "i"), (2, "-1"), (3, "-i")]
    rows = Vector{Dict{String,Any}}()
    for (orbit_index0, orbit) in enumerate(orbits)
        orbit_index = orbit_index0 - 1
        orbit_id, family, bit = orbit
        for (syndrome, phase) in phases
            push!(rows, Dict(
                "parent_representative_id" => "$(orbit_id)::phase_$(syndrome)",
                "orbit_id" => orbit_id,
                "orbit_index" => orbit_index,
                "quotient_output" => "orbit::$(orbit_id)",
                "terminal_family" => family,
                "terminal_bit" => bit,
                "terminal_structure_id" => "$(family)::bit_$(bit)::z4_$(syndrome)",
                "syndrome" => syndrome,
                "syndrome_bits" => string(syndrome, base=2, pad=2),
                "global_phase" => phase,
                "phase_quarter" => syndrome,
                "record_object_standard" => "packet_local_z4_syndrome_distribution",
                "generator" => "alpha += pi/2",
                "orbit_order" => 4,
            ))
        end
    end
    return rows
end

function record_object(rows)
    syndrome_counts = Dict{Int,Int}()
    orbit_support = Dict{String,Vector{Int}}()
    for row in rows
        syndrome = Int(row["syndrome"])
        syndrome_counts[syndrome] = get(syndrome_counts, syndrome, 0) + 1
        orbit_id = String(row["orbit_id"])
        if !haskey(orbit_support, orbit_id)
            orbit_support[orbit_id] = Int[]
        end
        push!(orbit_support[orbit_id], syndrome)
    end
    return Dict(
        "standard" => "z4_syndrome_record_v0_packet_local_convention",
        "semantic_role" => "record_of_parent_terminal_structure",
        "record_is_not_loss_assignment" => true,
        "syndrome_distribution" => Dict(string(k) => syndrome_counts[k] for k in sort(collect(keys(syndrome_counts)))),
        "syndrome_entropy" => entropy_from_counts([syndrome_counts[k] for k in sort(collect(keys(syndrome_counts)))]),
        "orbit_syndrome_support" => Dict(k => sort(v) for (k, v) in orbit_support),
        "source_convention_commit" => "bd7a54080",
    )
end

function assigned_syndrome(row, regime::String)
    parent = Int(row["syndrome"])
    orbit_index = Int(row["orbit_index"])
    if regime == "inheritance"
        return parent
    elseif regime == "cycle_null"
        return mod(parent + 1, 4)
    elseif regime == "random_null"
        return mod(3 * orbit_index + 1, 4)
    end
    error("unknown regime $(regime)")
end

function regime_summary(rows, regime::String)
    daughter = Vector{Dict{String,Any}}()
    for row in rows
        ds = assigned_syndrome(row, regime)
        daughter_terminal = "$(row["terminal_family"])::bit_$(row["terminal_bit"])::z4_$(ds)"
        matches = daughter_terminal == row["terminal_structure_id"]
        push!(daughter, Dict(
            "regime" => regime,
            "parent_representative_id" => row["parent_representative_id"],
            "daughter_initial_constraint" => Dict(
                "orbit_id" => row["orbit_id"],
                "terminal_family" => row["terminal_family"],
                "terminal_bit" => row["terminal_bit"],
                "record_syndrome" => ds,
                "initializer_source" => regime,
            ),
            "parent_terminal_structure_id" => row["terminal_structure_id"],
            "daughter_terminal_structure_id" => daughter_terminal,
            "parent_syndrome" => row["syndrome"],
            "daughter_syndrome" => ds,
            "record_alignment" => ds == row["syndrome"] ? 1 : 0,
            "terminal_structure_match" => matches,
            "stability_score" => matches ? 1.0 : 0.0,
            "structure_row_hash" => stable_hash(Dict(
                "family" => row["terminal_family"],
                "bit" => row["terminal_bit"],
                "parent_z4" => row["syndrome"],
                "daughter_z4" => ds,
            )),
        ))
    end
    syndrome_counts = Dict{Int,Int}()
    for row in daughter
        syndrome_counts[Int(row["daughter_syndrome"])] = get(syndrome_counts, Int(row["daughter_syndrome"]), 0) + 1
    end
    match_count = count(row -> row["terminal_structure_match"] == true, daughter)
    structures = Set([row["daughter_terminal_structure_id"] for row in daughter])
    return Dict(
        "regime" => regime,
        "row_count" => length(daughter),
        "daughter_rows" => daughter,
        "record_alignment_count" => sum(row["record_alignment"] for row in daughter),
        "terminal_structure_match_count" => match_count,
        "terminal_structure_mismatch_count" => length(daughter) - match_count,
        "mean_stability_score" => match_count / length(daughter),
        "stability_score_sum" => Float64(match_count),
        "unique_daughter_terminal_structures" => length(structures),
        "daughter_syndrome_distribution" => Dict(string(k) => syndrome_counts[k] for k in sort(collect(keys(syndrome_counts)))),
        "daughter_record_entropy" => entropy_from_counts([syndrome_counts[k] for k in sort(collect(keys(syndrome_counts)))]),
        "structure_signature_hash" => stable_hash([row["daughter_terminal_structure_id"] for row in daughter]),
    )
end

function graph_receipt(rows, regimes)
    graph = Graphs.SimpleDiGraph(3 * length(rows))
    for idx in 1:length(rows)
        Graphs.add_edge!(graph, idx, length(rows) + idx)
        Graphs.add_edge!(graph, length(rows) + idx, 2 * length(rows) + idx)
    end
    return Dict(
        "graph_type" => "Graphs.SimpleDiGraph",
        "node_count" => Graphs.nv(graph),
        "edge_count" => Graphs.ne(graph),
        "parent_record_bridge_count" => sum(Graphs.outdegree(graph, idx) for idx in 1:length(rows)),
        "regime_match_counts" => Dict(name => regimes[name]["terminal_structure_match_count"] for name in keys(regimes)),
    )
end

function z3_proofs(regimes)
    inherited = regimes["inheritance"]["terminal_structure_match_count"]
    cycle = regimes["cycle_null"]["terminal_structure_match_count"]
    random = regimes["random_null"]["terminal_structure_match_count"]

    function prove(kind::String)
        solver = Z3.Solver()
        inh = Z3.IntVar("inheritance_match_count")
        cyc = Z3.IntVar("cycle_match_count")
        rnd = Z3.IntVar("random_match_count")
        Z3.add(solver, inh == Z3.IntVal(inherited))
        Z3.add(solver, cyc == Z3.IntVal(cycle))
        Z3.add(solver, rnd == Z3.IntVal(random))
        if kind == "inheritance_gt_controls"
            Z3.add(solver, Z3.Not(Z3.And([inh > cyc, inh > rnd])))
        elseif kind == "cycle_random_distinct"
            Z3.add(solver, cyc == rnd)
        end
        return Dict(
            "solver" => "Z3.jl",
            "ran" => true,
            "load_bearing" => true,
            "verdict" => string(Z3.check(solver)),
            "polarity" => kind,
            "bound_values" => Dict(
                "inheritance_match_count" => inherited,
                "cycle_match_count" => cycle,
                "random_match_count" => random,
            ),
        )
    end

    return Dict(
        "inheritance_gt_controls" => prove("inheritance_gt_controls"),
        "cycle_random_distinct" => prove("cycle_random_distinct"),
    )
end

function main()
    rows = parent_rows()
    regimes = Dict(
        "inheritance" => regime_summary(rows, "inheritance"),
        "cycle_null" => regime_summary(rows, "cycle_null"),
        "random_null" => regime_summary(rows, "random_null"),
    )
    signatures = Dict(name => regimes[name]["structure_signature_hash"] for name in keys(regimes))
    discriminator = Dict(
        "all_regime_signatures_distinct" => length(Set(values(signatures))) == 3,
        "inheritance_gt_cycle_stability" => regimes["inheritance"]["mean_stability_score"] > regimes["cycle_null"]["mean_stability_score"],
        "inheritance_gt_random_stability" => regimes["inheritance"]["mean_stability_score"] > regimes["random_null"]["mean_stability_score"],
        "cycle_null_distinct_from_random_null" => signatures["cycle_null"] != signatures["random_null"],
    )
    discriminator["reported_if_no_teeth"] = !(discriminator["all_regime_signatures_distinct"] &&
        discriminator["inheritance_gt_cycle_stability"] &&
        discriminator["inheritance_gt_random_stability"])

    fixture = Dict(
        "parent_terminal_table" => rows,
        "record_object" => record_object(rows),
        "regimes" => regimes,
        "discriminator" => discriminator,
        "regime_signature_hashes" => signatures,
    )
    graph = graph_receipt(rows, regimes)
    proofs = z3_proofs(regimes)
    all_pass = (
        length(rows) == 24 &&
        fixture["record_object"]["syndrome_entropy"]["entropy_log2_coefficient"] == 2 &&
        regimes["inheritance"]["terminal_structure_match_count"] == 24 &&
        regimes["cycle_null"]["terminal_structure_match_count"] == 0 &&
        regimes["random_null"]["terminal_structure_match_count"] == 6 &&
        discriminator["all_regime_signatures_distinct"] == true &&
        discriminator["reported_if_no_teeth"] == false &&
        graph["parent_record_bridge_count"] == 24 &&
        proofs["inheritance_gt_controls"]["verdict"] == "unsat" &&
        proofs["cycle_random_distinct"]["verdict"] == "unsat"
    )

    payload = Dict(
        "schema_version" => "$(SIM_ID)_julia_leg_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_graphs_z3_reference_lane",
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
            "Graphs" => "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.outdegree parent-record-daughter support graph",
            "Z3" => "Z3.Solver/Z3.add/Z3.check over computed daughter match counts",
        ),
        "claim_path_tools" => ["Graphs", "Z3"],
        "fixture" => fixture,
        "julia_graph_receipt" => graph,
        "crossover_proofs" => Dict("julia_z3" => proofs),
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("used" => true, "reason" => "load-bearing finite inheritance support graph"),
            "Z3" => Dict("used" => true, "reason" => "load-bearing inequality/collapse proof over computed counts"),
            "JSON" => Dict("used" => true, "reason" => "structured result serialization"),
            "SHA" => Dict("used" => true, "reason" => "supportive hashing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "Z3" => "load_bearing", "JSON" => "supportive", "SHA" => "supportive"),
        "tool_calls" => [
            Dict(
                "tool" => "Graphs",
                "qualified_api/function" => "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.outdegree",
                "input_object" => "parent terminal rows plus record bridge edges",
                "output_object" => "finite parent->record->daughter graph receipt",
                "positive_case" => "24 parent rows bridge to record nodes",
                "negative/erased_control" => "cycle and random nulls do not align with parent syndrome records",
                "boundary_case" => "finite 72-node graph",
                "demotion_condition" => "demote if graph route is replaced by literal bridge count",
                "gates" => ["julia_graph_receipt", "all_pass"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.add/Z3.check",
                "input_object" => "computed regime match counts",
                "output_object" => "UNSAT collapse attempts",
                "positive_case" => "inheritance match count exceeds both null controls",
                "negative/erased_control" => "cycle-null and random-null are lower and distinct",
                "boundary_case" => "finite 24-row table",
                "demotion_condition" => "demote if solver does not bind computed counts",
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
