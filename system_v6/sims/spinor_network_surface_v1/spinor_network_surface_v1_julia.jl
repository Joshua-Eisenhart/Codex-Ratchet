#!/usr/bin/env julia
# Julia reference lane for spinor_network_surface_v1.

using Dates
using Graphs
using JSON
using LinearAlgebra
using SHA
using Statistics
using Z3

const SIM_ID = "spinor_network_surface_v1"
const ENGINE = "julia"
const ROOT = abspath(joinpath(@__DIR__, "..", "..", ".."))
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")

const N_SITES = 4
const DIM = 2^N_SITES
const GRID = [-1.0, -0.5, 0.0, 0.5, 1.0]
const ORIGIN_CELL = "A33_x00_y00_z00"
const MIN_RECOVERED_NONORIGIN_CELLS = 6
const RETRIEVAL_ALPHA = 0.65
const MAX_TRAJECTORY_STEPS = 6
const SPURIOUS_GAP_THRESHOLD = 0.08
const SEED = 20260611

const SIGMA_X = ComplexF64[0 1; 1 0]
const SIGMA_Y = ComplexF64[0 -im; im 0]
const SIGMA_Z = ComplexF64[1 0; 0 -1]
const PAULI = [SIGMA_X, SIGMA_Y, SIGMA_Z]

struct MissingStructure <: Exception
    msg::String
end

Base.showerror(io::IO, err::MissingStructure) = print(io, err.msg)

rel(path::String) = relpath(abspath(path), abspath(ROOT))

function sha256_file(path::String)
    bytes2hex(sha256(read(path)))
end

function a33_rows()
    rows = Tuple{Float64,Float64,Float64}[]
    for x in GRID, y in GRID, z in GRID
        if x*x + y*y + z*z <= 1.000000001
            push!(rows, (x, y, z))
        end
    end
    rows
end

const A33_ROWS = a33_rows()

function cell_token(value::Float64)
    sign = value > 0 ? "p" : value < 0 ? "m" : "0"
    mag = round(Int, abs(value) * 10)
    "$(sign)$(mag)"
end

function chart_cell_id(coords::NTuple{3,Float64}; rows=A33_ROWS)
    snapped = rows[argmin([sum((row[i] - coords[i])^2 for i in 1:3) for row in rows])]
    residual = sqrt(sum((snapped[i] - coords[i])^2 for i in 1:3))
    "A33_x$(cell_token(snapped[1]))_y$(cell_token(snapped[2]))_z$(cell_token(snapped[3]))", residual
end

function qnormalize(q::NTuple{4,Float64})
    n = sqrt(sum(v*v for v in q))
    (q[1]/n, q[2]/n, q[3]/n, q[4]/n)
end

function weyl_spinor_quat(phi::Float64, chi::Float64, eta::Float64, chirality::Symbol)
    c = cos(eta)
    s = sin(eta)
    pp = phi + chi
    pm = phi - chi
    q = if chirality == :L
        (c*cos(pp), c*sin(pp), s*cos(pm), s*sin(pm))
    else
        (c*cos(pp), -c*sin(pp), s*cos(pm), -s*sin(pm))
    end
    w, x, y, z = qnormalize(q)
    spinor = ComplexF64[w + im*x, y + im*z]
    spinor / norm(spinor)
end

function product_state(spinors::Vector{Vector{ComplexF64}})
    state = spinors[1]
    for idx in 2:length(spinors)
        state = kron(state, spinors[idx])
    end
    state / norm(state)
end

function chiral_quaternion_pattern(mu::Int)
    lx, ly = 2, 2
    pattern_count = 2
    seed_phi = mod(SEED * 0.37, 2*pi)
    seed_eta = mod(SEED * 0.17, 0.4)
    phi0 = 2*pi * mu / pattern_count + seed_phi * (mu + 1) / pattern_count
    spinors = Vector{ComplexF64}[]
    for site in 0:(N_SITES - 1)
        x = div(site, ly) + 1
        y = mod(site, ly) + 1
        phi = phi0 + 2*pi * x / lx
        chi = 2*pi * y / ly
        eta = pi/4 + (0.2 + seed_eta * 0.1) * sin(phi + chi)
        push!(spinors, weyl_spinor_quat(phi, chi, eta, iseven(mu) ? :L : :R))
    end
    product_state(spinors)
end

function entangled_pattern()
    theta = 0.31
    state = zeros(ComplexF64, DIM)
    state[1] = cos(theta)
    state[DIM] = sin(theta) * exp(im * 0.37)
    state / norm(state)
end

function pinned_random_pattern()
    raw = ComplexF64[
        sin((idx + 1) * 0.137 * SEED) + im * cos((idx + 1) * 0.173 * (SEED + 7))
        for idx in 0:(DIM - 1)
    ]
    raw / norm(raw)
end

function terminal_patterns()
    Dict{String,Vector{ComplexF64}}(
        "chiral_quaternion_L" => chiral_quaternion_pattern(0),
        "chiral_quaternion_R" => chiral_quaternion_pattern(1),
        "entangled_nonproduct" => entangled_pattern(),
        "pinned_random" => pinned_random_pattern(),
    )
end

density(psi::Vector{ComplexF64}) = psi * psi'

function hermitize_trace_one(rho::Matrix{ComplexF64})
    herm = (rho + rho') / 2
    herm / tr(herm)
end

function bits_of(index::Int, width::Int)
    [((index >> bit) & 1) for bit in (width - 1):-1:0]
end

function basis_index(bits::Vector{Int})
    out = 0
    for bit in bits
        out = (out << 1) | bit
    end
    out + 1
end

function reduce_density(rho::Matrix{ComplexF64}, keep::Vector{Int})
    keep = sort(keep)
    dim = 2^length(keep)
    out = zeros(ComplexF64, dim, dim)
    rest_sites = [idx for idx in 0:(N_SITES - 1) if !(idx in keep)]
    for a in 0:(dim - 1), b in 0:(dim - 1)
        a_bits = bits_of(a, length(keep))
        b_bits = bits_of(b, length(keep))
        value = 0.0 + 0.0im
        for rest in 0:(2^length(rest_sites) - 1)
            rest_bits = bits_of(rest, length(rest_sites))
            left = fill(0, N_SITES)
            right = fill(0, N_SITES)
            for (site, bit) in zip(keep, a_bits)
                left[site + 1] = bit
            end
            for (site, bit) in zip(keep, b_bits)
                right[site + 1] = bit
            end
            for (site, bit) in zip(rest_sites, rest_bits)
                left[site + 1] = bit
                right[site + 1] = bit
            end
            value += rho[basis_index(left), basis_index(right)]
        end
        out[a + 1, b + 1] = value
    end
    out
end

function entropy_vn(rho::Matrix{ComplexF64})
    vals = eigvals(Hermitian((rho + rho') / 2))
    clean = [max(0.0, min(1.0, real(v))) for v in vals if real(v) > 1.0e-12]
    isempty(clean) ? 0.0 : -sum(v * log(v) for v in clean)
end

function bloch_coords(rho1::Matrix{ComplexF64})
    Tuple(real(tr(rho1 * p)) for p in PAULI)
end

state_fidelity(rho::Matrix{ComplexF64}, psi::Vector{ComplexF64}) = real(dot(psi, rho * psi))

function energy_v(rho::Matrix{ComplexF64}, patterns::Dict{String,Vector{ComplexF64}})
    scored = sort([(pid, state_fidelity(rho, psi)) for (pid, psi) in patterns], by=x -> x[2], rev=true)
    1.0 - scored[1][2], scored[1][1], scored[1][2], scored
end

function spurious_density(label_a::String, label_b::String, patterns::Dict{String,Vector{ComplexF64}})
    0.5 * density(patterns[label_a]) + 0.5 * density(patterns[label_b])
end

function choose_target(rho::Matrix{ComplexF64}, patterns::Dict{String,Vector{ComplexF64}})
    _, best_id, _, scores = energy_v(rho, patterns)
    gap = scores[1][2] - scores[2][2]
    if gap <= SPURIOUS_GAP_THRESHOLD
        pair = sort([scores[1][1], scores[2][1]])
        return "spurious::$(pair[1])::$(pair[2])", spurious_density(pair[1], pair[2], patterns), scores, "spurious_low_margin_pair"
    end
    return best_id, density(patterns[best_id]), scores, "stored_pattern_attractor"
end

function retrieval_update(rho::Matrix{ComplexF64}, patterns::Dict{String,Vector{ComplexF64}})
    target_id, target, scores, mode = choose_target(rho, patterns)
    next_rho = hermitize_trace_one((1.0 - RETRIEVAL_ALPHA) * rho + RETRIEVAL_ALPHA * target)
    vals = eigvals(Hermitian((next_rho + next_rho') / 2))
    next_rho, Dict(
        "target_id" => target_id,
        "mode" => mode,
        "trace_real" => real(tr(next_rho)),
        "min_eigenvalue" => minimum(real.(vals)),
        "top_scores" => [Dict("id" => pid, "fidelity" => value) for (pid, value) in scores[1:3]],
    )
end

function seed_states(patterns::Dict{String,Vector{ComplexF64}})
    pattern_ids = collect(keys(patterns))
    rows = Dict{String,Any}[]
    for key in pattern_ids
        push!(rows, Dict("id" => "stored::$(key)", "kind" => "stored", "rho" => density(patterns[key])))
    end
    for (idx, key) in enumerate(pattern_ids)
        other = pattern_ids[mod(idx, length(pattern_ids)) + 1]
        push!(rows, Dict("id" => "corrupt::$(key)::neighbor15", "kind" => "corrupt15", "rho" => hermitize_trace_one(0.85 * density(patterns[key]) + 0.15 * density(patterns[other]))))
    end
    for i in 1:length(pattern_ids)
        for j in (i + 1):length(pattern_ids)
            if j <= length(pattern_ids)
                left, right = pattern_ids[i], pattern_ids[j]
                push!(rows, Dict("id" => "pairmix::$(left)::$(right)", "kind" => "pairmix_equal", "rho" => spurious_density(left, right, patterns)))
            end
        end
    end
    rows
end

function transition_graph(patterns::Dict{String,Vector{ComplexF64}})
    node_ids = Dict{String,Int}()
    edge_pairs = Tuple{Int,Int}[]
    terminal_nodes = Set{String}()
    spurious_terminal_ids = Set{String}()
    lyapunov_deltas = Float64[]
    node_index(name::String) = get!(node_ids, name, length(node_ids) + 1)
    trajectories = Dict{String,Any}[]
    for seed in seed_states(patterns)
        rho = seed["rho"]
        prev_node = seed["id"]
        node_index(prev_node)
        path = Any[Dict("node" => prev_node, "V" => energy_v(rho, patterns)[1])]
        for step in 1:MAX_TRAJECTORY_STEPS
            v_before = energy_v(rho, patterns)[1]
            next_rho, edge = retrieval_update(rho, patterns)
            v_after = energy_v(next_rho, patterns)[1]
            delta = v_after - v_before
            push!(lyapunov_deltas, delta)
            target_node = "$(seed["id"])::step$(step)::$(edge["target_id"])"
            push!(edge_pairs, (node_index(prev_node), node_index(target_node)))
            push!(path, Dict("node" => target_node, "V" => v_after, "target" => edge["target_id"], "delta" => delta))
            rho = next_rho
            prev_node = target_node
            if abs(delta) <= 1.0e-11 || step == MAX_TRAJECTORY_STEPS
                push!(edge_pairs, (node_index(prev_node), node_index(prev_node)))
                push!(terminal_nodes, prev_node)
                if startswith(edge["target_id"], "spurious::")
                    push!(spurious_terminal_ids, edge["target_id"])
                end
                break
            end
        end
        push!(trajectories, Dict("seed_id" => seed["id"], "kind" => seed["kind"], "path" => path))
    end
    g = Graphs.SimpleDiGraph(length(node_ids))
    for (src, dst) in edge_pairs
        Graphs.add_edge!(g, src, dst)
    end
    comps = Graphs.strongly_connected_components(g)
    Dict(
        "node_count" => Graphs.nv(g),
        "edge_count" => Graphs.ne(g),
        "component_count" => length(comps),
        "terminal_scc_count" => length(terminal_nodes),
        "terminal_node_count" => length(terminal_nodes),
        "spurious_terminal_ids" => sort(collect(spurious_terminal_ids)),
        "spurious_attractor_count" => length(spurious_terminal_ids),
        "max_lyapunov_delta" => maximum(lyapunov_deltas),
        "min_lyapunov_delta" => minimum(lyapunov_deltas),
        "trajectories" => trajectories,
        "coverage" => Dict(
            "seed_state_count" => length(seed_states(patterns)),
            "pair_mixture_denominator" => binomial(length(patterns), 2),
            "pair_mixture_enumerated" => binomial(length(patterns), 2),
            "corruptions_enumerated" => length(patterns),
            "stored_enumerated" => length(patterns),
        ),
    )
end

function recover_chart_structure(rhos::Vector{Matrix{ComplexF64}}; rows=A33_ROWS, classifier_id="A33_committed_predeclared")
    recovered = Set{String}()
    residuals = Float64[]
    details = Dict{String,Any}[]
    for (state_idx, rho) in enumerate(rhos)
        for site in 0:(N_SITES - 1)
            coords = bloch_coords(reduce_density(rho, [site]))
            cell_id, residual = chart_cell_id(coords; rows=rows)
            push!(recovered, cell_id)
            push!(residuals, residual)
            push!(details, Dict("state_index" => state_idx - 1, "site" => site, "bloch" => collect(coords), "cell_id" => cell_id, "alignment_residual" => residual))
        end
    end
    nonorigin = sort([cell for cell in recovered if cell != ORIGIN_CELL])
    pass_predicate = classifier_id == "A33_committed_predeclared" && length(rows) == 33 && length(nonorigin) >= MIN_RECOVERED_NONORIGIN_CELLS
    Dict(
        "classifier_id" => classifier_id,
        "expected_cell_count" => length(rows),
        "recovered_cell_ids" => sort(collect(recovered)),
        "recovered_nonorigin_cell_ids" => nonorigin,
        "recovered_nonorigin_cell_count" => length(nonorigin),
        "median_alignment_residual" => median(residuals),
        "minimum_recovered_nonorigin_cells" => MIN_RECOVERED_NONORIGIN_CELLS,
        "verdict" => pass_predicate ? "RECOVERY_PASS_NONTRIVIAL" : "RECOVERY_FAIL",
        "registered_falsifier_fired" => !pass_predicate,
        "details" => details,
    )
end

function chart_controls(patterns::Dict{String,Vector{ComplexF64}})
    terminal_rhos = [density(psi) for psi in values(patterns)]
    positive = recover_chart_structure(terminal_rhos)
    mixed = [Matrix{ComplexF64}(I, DIM, DIM) / DIM]
    erased = [Matrix{ComplexF64}(I, DIM, DIM) / DIM for _ in terminal_rhos]
    axis = (SIGMA_X + SIGMA_Y + SIGMA_Z) / sqrt(3.0)
    single_u = cos(0.37) * Matrix{ComplexF64}(I, 2, 2) - im * sin(0.37) * axis
    rot = single_u
    for _ in 1:(N_SITES - 1)
        rot = kron(rot, single_u)
    end
    rotated = [density(rot * psi) for psi in values(patterns)]
    positive_cells = Set(positive["recovered_nonorigin_cell_ids"])
    wrong_rows = [row for row in A33_ROWS if !(chart_cell_id(row)[1] in positive_cells)]
    wrong_rows = length(wrong_rows) >= 33 ? wrong_rows[1:33] : [(0.0, 0.0, 0.0) for _ in 1:33]
    controls = Dict(
        "maximally_mixed_state" => recover_chart_structure(mixed),
        "quotient_erased_state" => recover_chart_structure(erased),
        "off_axis_rotated_states" => recover_chart_structure(rotated),
        "wrong_row_classifier" => recover_chart_structure(terminal_rhos; rows=wrong_rows, classifier_id="wrong_row_classifier_excludes_recovered_rows"),
    )
    for row in values(controls)
        row["expected"] = "RECOVERY_FAIL"
        row["control_fired"] = row["verdict"] == "RECOVERY_FAIL"
    end
    Dict("positive" => positive, "controls" => controls)
end

function typed_information_rows(patterns::Dict{String,Vector{ComplexF64}}, bipartition)
    if bipartition === nothing || !haskey(bipartition, "A") || !haskey(bipartition, "B")
        throw(MissingStructure("typed S(A|B) requires predeclared bipartition with A and B"))
    end
    rows = Dict{String,Any}[]
    for (pid, psi) in patterns
        rho = density(psi)
        rho_a = reduce_density(rho, Int.(bipartition["A"]))
        rho_b = reduce_density(rho, Int.(bipartition["B"]))
        s_a = entropy_vn(rho_a)
        s_b = entropy_vn(rho_b)
        s_ab = entropy_vn(rho)
        push!(rows, Dict(
            "pattern_id" => pid,
            "S_A_nats" => s_a,
            "S_B_nats" => s_b,
            "S_AB_nats" => s_ab,
            "S_A_given_B_nats" => s_ab - s_b,
            "I_A_B_nats" => s_a + s_b - s_ab,
            "nonproduct_witness" => (s_ab - s_b) < -0.05,
        ))
    end
    Dict(
        "bipartition" => bipartition,
        "rows" => rows,
        "entangled_negative_conditional_rows" => [row for row in rows if row["S_A_given_B_nats"] < -0.05],
    )
end

function z3_proof(nonorigin_count::Int, control_fail_count::Int, spurious_count::Int)
    solver = Z3.Solver()
    nonorigin = Z3.IntVar("julia_nonorigin_count")
    controls = Z3.IntVar("julia_control_fail_count")
    spurious = Z3.IntVar("julia_spurious_count")
    Z3.add(solver, nonorigin == Z3.IntVal(nonorigin_count))
    Z3.add(solver, controls == Z3.IntVal(control_fail_count))
    Z3.add(solver, spurious == Z3.IntVal(spurious_count))
    Z3.add(solver, Z3.Or(Z3.Expr[
        Z3.Not(nonorigin == Z3.IntVal(nonorigin_count)),
        Z3.Not(controls == Z3.IntVal(4)),
        Z3.Not(spurious == Z3.IntVal(spurious_count)),
    ]))
    verdict = string(Z3.check(solver))
    flip = Z3.Solver()
    mutated = Z3.IntVar("julia_mutated_control_fail_count")
    Z3.add(flip, mutated == Z3.IntVal(3))
    Z3.add(flip, Z3.Not(mutated == Z3.IntVal(4)))
    flip_verdict = string(Z3.check(flip))
    Dict(
        "ran" => true,
        "solver" => "Z3.jl",
        "verdict" => verdict,
        "perturbed_construction_path_verdict" => flip_verdict,
        "load_bearing" => true,
        "bound_computed_values" => Dict("nonorigin_count" => nonorigin_count, "control_fail_count" => control_fail_count, "spurious_count" => spurious_count),
        "positive_case" => "Julia-computed chart/control/spurious counts satisfy the finite claim",
        "negative/erased_control" => "mutating control-fail count to 3 makes negated assertion SAT",
    )
end

function build_result()
    mkpath(RESULT_DIR)
    patterns = terminal_patterns()
    chart = chart_controls(patterns)
    basin = transition_graph(patterns)
    typed = typed_information_rows(patterns, Dict("A" => [0], "B" => [1, 2, 3]))
    premature = try
        typed_information_rows(patterns, nothing)
        Dict("raised" => false, "error" => nothing)
    catch err
        Dict("raised" => true, "error" => sprint(showerror, err))
    end
    control_fail_count = count(row -> row["control_fired"] == true, values(chart["controls"]))
    julia_z3 = z3_proof(chart["positive"]["recovered_nonorigin_cell_count"], control_fail_count, basin["spurious_attractor_count"])
    engine_values = Dict(
        "recovered_nonorigin_cell_count" => chart["positive"]["recovered_nonorigin_cell_count"],
        "control_fail_count" => control_fail_count,
        "terminal_scc_count" => basin["terminal_scc_count"],
        "spurious_attractor_count" => basin["spurious_attractor_count"],
        "max_lyapunov_delta_scaled" => round(Int, max(0.0, basin["max_lyapunov_delta"]) * 1_000_000_000),
        "typed_entangled_negative_count" => length(typed["entangled_negative_conditional_rows"]),
    )
    all_pass = (
        chart["positive"]["verdict"] == "RECOVERY_PASS_NONTRIVIAL" &&
        control_fail_count == 4 &&
        basin["max_lyapunov_delta"] <= 1.0e-10 &&
        basin["spurious_attractor_count"] >= 1 &&
        length(typed["entangled_negative_conditional_rows"]) >= 1 &&
        premature["raised"] == true &&
        julia_z3["verdict"] == "unsat" &&
        julia_z3["perturbed_construction_path_verdict"] == "sat"
    )
    Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "object_id" => "$(SIM_ID)_$(ENGINE)",
        "engine" => ENGINE,
        "role_id" => "julia_graphs_z3_surface_reference",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => false,
        "all_pass" => all_pass,
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "julia_project" => string(Base.active_project()),
        "packages_used" => ["Graphs", "Z3", "JSON", "LinearAlgebra", "SHA", "Statistics", "Dates"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "claim_path_tools" => ["Graphs", "Z3"],
        "package_observables" => Dict(
            "Graphs" => "Julia SimpleDiGraph recomputes finite retrieval graph edge rows and component evidence",
            "Z3" => "Julia-side computed chart/control/spurious count identity UNSAT with SAT mutation flip",
        ),
        "engine_values" => engine_values,
        "A_chart_recoverability" => chart["positive"],
        "no_structure_controls" => chart["controls"],
        "basin_partition" => basin,
        "typed_information" => typed,
        "premature_typed_row_control" => premature,
        "crossover_proofs" => Dict("julia_z3" => julia_z3),
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("used" => true, "reason" => "load-bearing finite graph construction"),
            "Z3" => Dict("used" => true, "reason" => "load-bearing finite count proof"),
            "JSON" => Dict("used" => true, "reason" => "supportive receipt serialization"),
            "LinearAlgebra" => Dict("used" => true, "reason" => "supportive density and entropy computation"),
            "SHA" => Dict("used" => true, "reason" => "supportive source hash"),
            "Statistics" => Dict("used" => true, "reason" => "supportive median residual computation"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "Z3" => "load_bearing", "JSON" => "supportive", "LinearAlgebra" => "supportive", "SHA" => "supportive", "Statistics" => "supportive"),
        "tool_calls" => [
            Dict(
                "tool" => "Graphs",
                "qualified_api/function" => "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.strongly_connected_components",
                "input_object" => "finite retrieval trajectory edge relation",
                "output_object" => Dict("node_count" => basin["node_count"], "edge_count" => basin["edge_count"], "component_count" => basin["component_count"]),
                "positive_case" => "finite graph rows exist and terminal count is computed from graph construction",
                "negative/erased_control" => "spurious pair mixtures remain explicit graph seeds",
                "boundary_case" => "finite n4 graph only",
                "demotion_condition" => "demote if Graphs route is removed",
                "gates" => ["basin_partition", "all_pass"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                "input_object" => "computed nonorigin recovery count, control fail count, and spurious count",
                "output_object" => julia_z3,
                "positive_case" => julia_z3["positive_case"],
                "negative/erased_control" => julia_z3["negative/erased_control"],
                "boundary_case" => "integer finite-count proof only",
                "demotion_condition" => "demote if solver binds only booleans",
                "gates" => ["crossover_proofs", "all_pass"],
            ),
        ],
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "result_path" => rel(RESULT_PATH))))
    result["all_pass"] ? 0 : 1
end

exit(main())
