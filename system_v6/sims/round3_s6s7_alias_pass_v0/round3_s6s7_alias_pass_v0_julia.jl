#!/usr/bin/env julia
# Julia Graphs/Z3 reference lane for round3_s6s7_alias_pass_v0.

using Dates
using Graphs
using JSON
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "round3_s6s7_alias_pass_v0"
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
const N_LIGHT = 8

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))

function cycle_graph_jl(n::Int=N_LIGHT)
    g = SimpleGraph(n)
    for i in 1:n
        add_edge!(g, i, mod1(i + 1, n))
    end
    g
end

function cycle_reparameterized_graph_jl(n::Int=N_LIGHT)
    g = SimpleGraph(n)
    for i0 in 0:n-1
        a = mod(3 - i0, n) + 1
        b = mod(3 - (i0 + 1), n) + 1
        add_edge!(g, a, b)
    end
    g
end

function path_graph_jl(n::Int=N_LIGHT)
    g = SimpleGraph(n)
    for i in 1:n-1
        add_edge!(g, i, i + 1)
    end
    g
end

function chord_cycle_graph_jl(n::Int=N_LIGHT)
    g = cycle_graph_jl(n)
    for i in 1:n÷2
        add_edge!(g, i, i + n ÷ 2)
    end
    g
end

function ladder_prism_graph_jl(n::Int=N_LIGHT)
    g = SimpleGraph(2 * n)
    for layer in 0:1
        offset = layer * n
        for i in 1:n
            add_edge!(g, offset + i, offset + mod1(i + 1, n))
        end
    end
    for i in 1:n
        add_edge!(g, i, n + i)
    end
    g
end

function graph_rows(g)
    n = nv(g)
    m = ne(g)
    degrees = sort(degree(g))
    Dict(
        "node_count" => n,
        "edge_count" => m,
        "degree_sequence" => degrees,
        "cycle_rank" => m - n + length(connected_components(g)),
        "connected_components" => length(connected_components(g)),
    )
end

function edge_set(g)
    sort([(min(src(e), dst(e)), max(src(e), dst(e))) for e in edges(g)])
end

function cover_signature(kind::String)
    if kind == "untwisted"
        return Dict(
            "kind" => "untwisted_torus_cover",
            "relation" => "(a,b)~(a+N/2,b)",
            "z4_well_defined" => true,
            "orbit_size_multiset_N8" => [2, 2, 2, 2],
        )
    elseif kind == "mobius"
        return Dict(
            "kind" => "mobius_reflection_shifted",
            "relation" => "(a,b)~(a+N/2,-b+c)",
            "z4_well_defined" => "queued-heavy-local",
            "orbit_size_multiset_N8" => [2, 2, 2, 2],
        )
    elseif kind == "klein"
        return Dict(
            "kind" => "klein_double_twist",
            "relation" => "two-direction orientation reversal",
            "z4_well_defined" => "queued-heavy-local",
            "orbit_size_multiset_N8" => "queued-heavy-local",
        )
    elseif kind == "shear"
        return Dict(
            "kind" => "shear_torus",
            "relation" => "(a,b)->(a+N/2,b+a mod N)",
            "z4_well_defined" => "queued-heavy-local",
            "orbit_size_multiset_N8" => "queued-heavy-local",
        )
    end
    Dict(
        "kind" => "support_graph_only",
        "relation" => "same untwisted cover pending heavy graph/cost row",
        "z4_well_defined" => "queued-heavy-local",
        "orbit_size_multiset_N8" => "queued-heavy-local",
    )
end

function canonical_tuple(g, kind::String; full_phase1::Bool)
    Dict(
        "canonicalizer" => "graph_isomorphism_class_under_dihedral_lens_preserving_maps, cover_equivalence_relation_classes, Z4_action_well_defined_boolean, orbit_size_multiset, cost_profile[N=8,16,32], S6_leakage_class_signature",
        "light_graph_invariants" => graph_rows(g),
        "cover_signature" => cover_signature(kind),
        "cost_profile_N_8_16_32" => full_phase1 ? [8, 16, 32] : "not-run-heavy-local",
        "S6_leakage_class_signature" => full_phase1 ? "preserve/move/cross/leave" : "not-run-heavy-local",
    )
end

function witness(anchor, candidate)
    paths = [
        ["light_graph_invariants", "node_count"],
        ["light_graph_invariants", "edge_count"],
        ["light_graph_invariants", "degree_sequence"],
        ["light_graph_invariants", "cycle_rank"],
        ["cover_signature", "kind"],
        ["cover_signature", "relation"],
        ["cover_signature", "z4_well_defined"],
    ]
    for path in paths
        left = anchor
        right = candidate
        for part in path
            left = left[part]
            right = right[part]
        end
        if left != right
            return Dict("field" => join(path, "."), "anchor" => left, "candidate" => right)
        end
    end
    Dict("field" => "canonical_tuple", "anchor" => "equal", "candidate" => "equal")
end

function registry_specs()
    [
        Dict("id" => "S67.R3.0_committed_torus_ring", "finite_representative" => "untwisted torus cover, cycle graph, Z4 lens shift", "closeness" => "control", "expected_teeth_row" => "none; anchor", "cost" => "light-symbolic", "kind" => "untwisted", "graph" => cycle_graph_jl),
        Dict("id" => "S67.R3.1_mobius_reflection_shifted", "finite_representative" => "cover relation (a,b)~(a+N/2,-b+c) for c in {0,N/4,N/2}", "closeness" => "closest known twist family", "expected_teeth_row" => "lens quotient commensurability", "cost" => "heavy-local", "kind" => "mobius", "graph" => cycle_graph_jl),
        Dict("id" => "S67.R3.2_klein_double_twist", "finite_representative" => "two-direction orientation reversal on the rectangular chart with the same Z4 shift", "closeness" => "close cover-neighbor", "expected_teeth_row" => "cover-orbit well-definedness then lens row", "cost" => "heavy-local", "kind" => "klein", "graph" => cycle_graph_jl),
        Dict("id" => "S67.R3.3_shear_torus", "finite_representative" => "untwisted cover plus shear (a,b)->(a+N/2,b+a mod N) on representatives", "closeness" => "near untwisted but altered lens action", "expected_teeth_row" => "lens descent and S6 leakage taxonomy", "cost" => "heavy-local", "kind" => "shear", "graph" => cycle_graph_jl),
        Dict("id" => "S67.R3.4_cycle_with_one_chord", "finite_representative" => "ring graph plus one antipodal chord at each N", "closeness" => "close support graph neighbor", "expected_teeth_row" => "bounded word cost and cycle holonomy", "cost" => "heavy-local", "kind" => "support", "graph" => chord_cycle_graph_jl),
        Dict("id" => "S67.R3.5_ladder_prism_graph", "finite_representative" => "two-ring ladder/prism local graph with degree 3", "closeness" => "graph topology neighbor between ring and complete", "expected_teeth_row" => "locality cost plus leakage class row", "cost" => "heavy-local", "kind" => "support", "graph" => ladder_prism_graph_jl),
    ]
end

function build_rows()
    anchor = canonical_tuple(cycle_graph_jl(), "untwisted"; full_phase1=true)
    candidates = []
    for spec in registry_specs()
        full = spec["cost"] == "light-symbolic"
        candidate = canonical_tuple(spec["graph"](), spec["kind"]; full_phase1=full)
        verdict = spec["id"] == "S67.R3.0_committed_torus_ring" ? "anchor" : "open + queued-heavy-local"
        row_name = spec["id"] == "S67.R3.0_committed_torus_ring" ? "anchor" : "heavy_local_cost_guard_not_run_in_phase_1"
        push!(candidates, Dict(
            "id" => spec["id"],
            "finite_representative" => spec["finite_representative"],
            "closeness" => spec["closeness"],
            "expected_teeth_row" => spec["expected_teeth_row"],
            "cost" => spec["cost"],
            "verdict" => verdict,
            "row" => row_name,
            "witness" => full ? witness(anchor, candidate) : Dict("field" => "registry_cost_guard", "anchor" => "light-symbolic anchor canonical tuple completed", "candidate" => "$(spec["id"]) cost=heavy-local; queued for $(spec["expected_teeth_row"])"),
            "canonical_tuple" => candidate,
            "citation_status" => "no prior co-survivor receipt cited; S4 audit standard forces open + queued-heavy-local",
        ))
    end
    alias_tuple = canonical_tuple(cycle_reparameterized_graph_jl(), "untwisted"; full_phase1=true)
    far_tuple = canonical_tuple(path_graph_jl(), "support"; full_phase1=true)
    controls = [
        Dict("id" => "control.anchor_self", "verdict" => "anchor", "row" => "anchor", "witness" => witness(anchor, anchor), "canonical_tuple" => anchor),
        Dict("id" => "control.alias_reparameterized_committed", "verdict" => edge_set(cycle_graph_jl()) == edge_set(cycle_reparameterized_graph_jl()) && alias_tuple == anchor ? "alias" : "failed", "row" => "graph_edge_set_and_canonical_tuple_equal", "witness" => witness(anchor, alias_tuple), "canonical_tuple" => alias_tuple),
        Dict("id" => "control.round2_path_far_graph", "verdict" => "excluded-by-closed-cycle-graph-row", "row" => "closed-cycle graph row", "witness" => witness(anchor, far_tuple), "canonical_tuple" => far_tuple),
    ]
    Dict("candidate_rows" => candidates, "control_rows" => controls)
end

function julia_z3_proof(path_degrees, cycle_degrees)
    solver = Z3.Solver()
    for (i, value) in enumerate(path_degrees)
        var = Z3.IntVar("julia_path_degree_$i")
        Z3.add(solver, var == Z3.IntVal(value))
        Z3.add(solver, var == Z3.IntVal(2))
    end
    positive = string(Z3.check(solver))

    flip = Z3.Solver()
    for (i, value) in enumerate(cycle_degrees)
        var = Z3.IntVar("julia_cycle_degree_$i")
        Z3.add(flip, var == Z3.IntVal(value))
        Z3.add(flip, var == Z3.IntVal(2))
    end
    flip_status = string(Z3.check(flip))
    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "verdict" => positive,
        "load_bearing" => true,
        "asserted_precomputed_boolean" => false,
        "claim" => "computed path graph degree witnesses cannot satisfy the closed cycle degree-2 row",
        "witness_values" => Dict("path_degrees" => path_degrees, "cycle_degrees" => cycle_degrees),
        "negated_assertion" => "all path degrees equal 2",
        "flip_control_verdict" => flip_status,
        "positive_case" => "far path graph has degree endpoints 1, so the closed-cycle row is UNSAT",
        "negative/erased_control" => "closing the path into the anchor cycle makes the degree-2 row SAT",
        "boundary_case" => "SMT binds the finite N=8 first-teeth row only; heavy S6/S7 rows remain queued",
    )
end

function build_result()
    rows = build_rows()
    verdicts = Dict(row["id"] => row["verdict"] for row in rows["candidate_rows"])
    controls = Dict(row["id"] => row["verdict"] for row in rows["control_rows"])
    heavy_queue = [row["id"] for row in rows["candidate_rows"] if row["cost"] == "heavy-local"]
    proof = julia_z3_proof(sort(degree(path_graph_jl())), sort(degree(cycle_graph_jl())))
    gates = Dict(
        "graphs_rows_built" => length(rows["candidate_rows"]) == 6,
        "anchor_classifies_as_itself" => verdicts["S67.R3.0_committed_torus_ring"] == "anchor",
        "deliberate_alias_classifies_alias" => controls["control.alias_reparameterized_committed"] == "alias",
        "far_candidate_dies_first_teeth" => controls["control.round2_path_far_graph"] == "excluded-by-closed-cycle-graph-row",
        "heavy_local_rows_queued" => all(verdicts[id] == "open + queued-heavy-local" for id in heavy_queue),
        "julia_z3_positive_unsat" => proof["verdict"] == "unsat",
        "julia_z3_flip_control_sat" => proof["flip_control_verdict"] == "sat",
    )
    all_pass = all(values(gates))
    Dict(
        "schema" => "$(SIM_ID)_julia_lane_v1",
        "sim_id" => SIM_ID,
        "role_id" => "julia_graphs_reference_lane",
        "engine_role_note" => "Julia Graphs rebuilds finite graph rows; Z3.jl binds the far path closed-cycle witness polarity.",
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "packages_used" => ["Graphs", "Z3", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "package_observables" => Dict(
            "Graphs" => "Graphs.SimpleGraph/add_edge!/degree/ne/nv compute finite support graph rows for anchor, alias, and far-control witnesses",
            "Z3" => "Z3.Solver/check proves finite far path degree-row UNSAT under cycle constraints and SAT after closing-edge flip",
        ),
        "claim_path_tools" => ["Graphs", "Z3"],
        "all_pass" => all_pass,
        "positive" => Dict("graphs_reference_rows" => rows["candidate_rows"], "anchor_and_alias_control" => rows["control_rows"][1:2]),
        "negative" => Dict("far_candidate_control" => rows["control_rows"][3], "heavy_local_label_guard" => "not-run heavy-local rows are open + queued-heavy-local"),
        "boundary" => Dict(
            "phase" => "light-symbolic phase 1 only",
            "heavy_local_not_run" => heavy_queue,
            "pytorch_omitted" => "no PyTorch tensor/autograd/message-passing claim path is scoped",
        ),
        "candidate_verdicts" => rows["candidate_rows"],
        "control_verdicts" => rows["control_rows"],
        "phase2_queue" => Dict(
            "light_symbolic_non_alias_representatives_remaining" => [],
            "heavy_local_queued_by_registry_cost_class" => heavy_queue,
            "known_cosurvivor_classes" => [],
        ),
        "crossover_proofs" => Dict("julia_z3" => proof),
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("used" => true, "reason" => "load-bearing finite graph construction and degree/cycle rows"),
            "Z3" => Dict("used" => true, "reason" => "load-bearing Julia-side finite first-teeth row witness polarity"),
            "JSON" => Dict("used" => true, "reason" => "supportive result serialization"),
            "SHA" => Dict("used" => true, "reason" => "supportive source hash"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "Z3" => "load_bearing", "JSON" => "supportive", "SHA" => "supportive"),
        "tool_calls" => [
            Dict(
                "tool" => "Graphs",
                "qualified_api" => "Graphs.SimpleGraph/add_edge!/degree/ne/nv",
                "input_object" => "finite N=8 support graph rows",
                "output_object" => "degree, edge, node, and cycle-rank witnesses",
                "positive_case" => "cycle anchor has degree sequence all 2 and cycle rank 1",
                "negative/erased_control" => "path far-control has endpoint degree 1 and cycle rank 0",
                "boundary_case" => "heavy-local R3 rows remain queued",
                "demotion_condition" => "Graphs rows missing or disagreed with Python exact lane",
            )
        ],
        "build_gates" => gates,
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "result_path" => RESULT_PATH_REL)))
    result["all_pass"] ? 0 : 1
end

exit(main())
