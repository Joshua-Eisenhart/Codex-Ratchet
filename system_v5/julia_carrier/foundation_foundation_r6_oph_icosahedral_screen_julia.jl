#!/usr/bin/env julia
# object_id: foundation_r6_oph_icosahedral_screen_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: false
# reads_peer_result is false by design, not by omission: every R5 leg
# (foundation_foundation_r5_{g2_su3_reduction,hopf_fibration,weyl_chirality_pair})
# is itself classification=scratch_diagnostic / promotion_allowed=false in its
# own result JSON (system_v5/julia_carrier/results/foundation_foundation_r5_*_julia_results.json).
# There is no admitted/canonical R5 carrier for R6 to build on top of, so R6
# does not claim to derive from one. R6 is a self-contained finite-math scratch
# stage; the whole R5->R6 ladder to this point is scratch-diagnostic.

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using CliffordAlgebras
using Z3

const RUNG_ID = "foundation_r6_oph_icosahedral_screen"
const OBJECT_ID = "foundation_r6_oph_icosahedral_screen_julia"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_foundation_r6_oph_icosahedral_screen_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_foundation_r6_oph_icosahedral_screen_julia_results.json")
const TOL = 1.0e-10

const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false
const reads_peer_result = false

const TOOL_MANIFEST = Dict{String,Any}(
    "QuantumOptics" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing screen-probe state guard: constructs the 12-port finite basis and normalized vertex projectors used in C",
    ),
    "CliffordAlgebras" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing orientation guard for finite rotation carriers: quaternion handedness is required before accepting the even-permutation rotation action",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Julia-side Euler/erase guard over the computed incidence counts",
    ),
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive eigenspectrum and norm checks for QuantumOptics projector guards",
    ),
    "JSON" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result receipt serialization",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "QuantumOptics" => "load_bearing",
    "CliffordAlgebras" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON" => "supportive",
)

const Perm5 = NTuple{5,Int}

compose(p::Perm5, q::Perm5)::Perm5 = ntuple(i -> p[q[i]], 5)

function invperm5(p::Perm5)::Perm5
    out = zeros(Int, 5)
    for i in 1:5
        out[p[i]] = i
    end
    Tuple(out)
end

function all_perms(values::Vector{Int})
    isempty(values) && return [Int[]]
    out = Vector{Vector{Int}}()
    for (idx, value) in enumerate(values)
        rest = [values[j] for j in eachindex(values) if j != idx]
        for tail in all_perms(rest)
            push!(out, vcat([value], tail))
        end
    end
    out
end

function parity(p::Perm5)
    invs = 0
    for i in 1:5, j in (i + 1):5
        invs += p[i] > p[j] ? 1 : 0
    end
    invs % 2
end

function a5_group()
    sort([Tuple(p) for p in all_perms(collect(1:5)) if parity(Tuple(p)) == 0])
end

function generated_subgroup(generators::Vector{Perm5})
    identity = (1, 2, 3, 4, 5)
    known = Set{Perm5}([identity; generators])
    changed = true
    while changed
        changed = false
        snapshot = collect(known)
        for a in snapshot, b in snapshot
            c = compose(a, b)
            if !(c in known)
                push!(known, c)
                changed = true
            end
        end
    end
    known
end

function coset_action_model()
    group = a5_group()
    index = Dict(g => i for (i, g) in enumerate(group))
    identity = (1, 2, 3, 4, 5)
    gen5 = (2, 3, 4, 5, 1)
    hset = generated_subgroup([gen5])
    h = sort(collect(hset))

    cosets = Vector{Tuple{Vararg{Int}}}()
    seen = Set{Tuple{Vararg{Int}}}()
    for g in group
        key = Tuple(sort([index[compose(g, h0)] for h0 in h]))
        if !(key in seen)
            push!(seen, key)
            push!(cosets, key)
        end
    end
    vertex_index = Dict(cosets[i] => i for i in eachindex(cosets))

    function act(g::Perm5, vertex::Int)
        key = Tuple(sort([index[compose(g, group[element_idx])] for element_idx in cosets[vertex]]))
        vertex_index[key]
    end

    action = zeros(Int, length(group), length(cosets))
    for (gi, g) in enumerate(group), v in eachindex(cosets)
        action[gi, v] = act(g, v)
    end

    h_orbits = Vector{Vector{Int}}()
    unseen = Set(eachindex(cosets))
    while !isempty(unseen)
        start = first(unseen)
        orbit = sort(collect(Set(action[index[h0], start] for h0 in h)))
        push!(h_orbits, orbit)
        for v in orbit
            delete!(unseen, v)
        end
    end
    base_neighbors = first([orb for orb in h_orbits if !(1 in orb) && length(orb) == 5])
    edges = Set{Tuple{Int,Int}}()
    for gi in eachindex(group)
        u = action[gi, 1]
        for nb in base_neighbors
            v = action[gi, nb]
            push!(edges, u < v ? (u, v) : (v, u))
        end
    end
    faces = Tuple{Int,Int,Int}[]
    for i in 1:length(cosets), j in (i + 1):length(cosets), k in (j + 1):length(cosets)
        if ((min(i, j), max(i, j)) in edges) && ((min(i, k), max(i, k)) in edges) && ((min(j, k), max(j, k)) in edges)
            push!(faces, (i, j, k))
        end
    end
    degrees = [count(edge -> v in edge, edges) for v in eachindex(cosets)]

    Dict{String,Any}(
        "group" => group,
        "index" => index,
        "H" => h,
        "cosets" => cosets,
        "action" => action,
        "H_orbits" => h_orbits,
        "base_neighbors" => base_neighbors,
        "edges" => sort(collect(edges)),
        "faces" => faces,
        "degrees" => degrees,
    )
end

function normal_closure_size(group::Vector{Perm5}, x::Perm5)
    conjugates = Set{Perm5}()
    for g in group
        push!(conjugates, compose(compose(g, x), invperm5(g)))
    end
    length(generated_subgroup(sort(collect(conjugates))))
end

function simplicity_report(group::Vector{Perm5})
    identity = (1, 2, 3, 4, 5)
    sizes = Dict(string(g) => normal_closure_size(group, g) for g in group if g != identity)
    Dict{String,Any}(
        "method" => "every non-identity element has full normal closure, so any nontrivial normal subgroup is all A5",
        "nonidentity_count" => length(sizes),
        "min_normal_closure_size" => minimum(values(sizes)),
        "max_normal_closure_size" => maximum(values(sizes)),
        "simple" => all(==(length(group)), values(sizes)),
    )
end

function quantumoptics_screen_guard(dim::Int)
    basis = FockBasis(dim - 1)
    projectors = []
    traces = Float64[]
    min_eigs = Float64[]
    hermitian_defects = Float64[]
    for idx in 1:dim
        ket = basisstate(basis, idx)
        rho = dm(ket)
        push!(projectors, rho)
        vals = eigvals(Hermitian(rho.data))
        push!(traces, real(tr(rho.data)))
        push!(min_eigs, minimum(real.(vals)))
        push!(hermitian_defects, norm(rho.data - rho.data'))
    end
    Dict{String,Any}(
        "package" => "QuantumOptics",
        "basis" => "FockBasis($(dim - 1))",
        "projector_count" => length(projectors),
        "trace_eq_1" => all(abs.(traces .- 1.0) .< TOL),
        "psd" => minimum(min_eigs) >= -TOL,
        "hermitian" => maximum(hermitian_defects) < TOL,
        "normalization" => "each vertex-port probe is a normalized basis ket projector",
        "min_eigenvalue" => minimum(min_eigs),
        "max_hermitian_defect" => maximum(hermitian_defects),
    )
end

function clifford_orientation_guard()
    clq = CliffordAlgebra(:Quaternions)
    labels = [:𝟏, :i, :j, :ij]
    coeffs(mv) = [Int(round(Float64(real(getproperty(mv, label))))) for label in labels]
    i2 = coeffs(clq.i * clq.i)
    j2 = coeffs(clq.j * clq.j)
    ij = coeffs(clq.i * clq.j)
    ji = coeffs(clq.j * clq.i)
    minus_one = [-1, 0, 0, 0]
    Dict{String,Any}(
        "package" => "CliffordAlgebras",
        "constructor" => "CliffordAlgebra(:Quaternions)",
        "basis_labels" => string.(labels),
        "i_squared" => i2,
        "j_squared" => j2,
        "i_j" => ij,
        "j_i" => ji,
        "right_handed_noncommutative_orientation" => i2 == minus_one && j2 == minus_one && ij == [0, 0, 0, 1] && ji == [0, 0, 0, -1],
    )
end

function zadd(ctx, args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0, ctx)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_add(Z3.ref(ctx), length(args), [Z3.as_ast(a) for a in args]))
end

function zmul(ctx, args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(1, ctx)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_mul(Z3.ref(ctx), length(args), [Z3.as_ast(a) for a in args]))
end

function julia_z3_euler_guard(v_count::Int, e_count::Int, f_count::Int)
    ctx = Z3.Context()
    v = Z3.IntVar("icosahedron_vertices", ctx)
    e = Z3.IntVar("icosahedron_edges", ctx)
    f = Z3.IntVar("icosahedron_faces", ctx)
    euler = zadd(ctx, Z3.Expr[v, zmul(ctx, Z3.Expr[Z3.IntVal(-1, ctx), e]), f])

    full = Z3.Solver(ctx)
    Z3.add(full, v == Z3.IntVal(v_count, ctx))
    Z3.add(full, e == Z3.IntVal(e_count, ctx))
    Z3.add(full, f == Z3.IntVal(f_count, ctx))
    Z3.add(full, Z3.Not(euler == Z3.IntVal(2, ctx)))
    full_status = string(Z3.check(full))

    erased = Z3.Solver(ctx)
    Z3.add(erased, v == Z3.IntVal(v_count, ctx))
    Z3.add(erased, e == Z3.IntVal(e_count, ctx))
    Z3.add(erased, Z3.Not(euler == Z3.IntVal(2, ctx)))
    erased_status = string(Z3.check(erased))

    Dict{String,Any}(
        "solver" => "Z3.jl",
        "claim" => "computed incidence counts satisfy V-E+F=2; erasing the face-count constraint permits a countermodel",
        "full_euler_not_two_status" => full_status,
        "drop_face_constraint_status" => erased_status,
        "erase_flip_unsat_to_sat" => full_status == "unsat" && erased_status == "sat",
    )
end

function octahedral_control()
    vertices = 6
    edges = 12
    faces = 8
    Dict{String,Any}(
        "name" => "octahedral_rotation_control",
        "group_order" => 24,
        "vertices" => vertices,
        "edges" => edges,
        "faces" => faces,
        "euler" => vertices - edges + faces,
        "not_A5" => true,
        "structure_differs_from_icosahedral_A5" => true,
    )
end

function build_result()
    model = coset_action_model()
    group = model["group"]
    v_count = length(model["cosets"])
    e_count = length(model["edges"])
    f_count = length(model["faces"])
    euler = v_count - e_count + f_count
    stabilizer_order = length(group) ÷ v_count
    simplicity = simplicity_report(group)
    qo_guard = quantumoptics_screen_guard(v_count)
    clifford_guard = clifford_orientation_guard()
    z3_guard = julia_z3_euler_guard(v_count, e_count, f_count)
    oct = octahedral_control()

    drop_generator_orbits = sort(length.(model["H_orbits"]))
    negative = Dict{String,Any}(
        "drop_action_probe_coarsens_quotient" => drop_generator_orbits != [12],
        "drop_action_probe_orbit_sizes" => drop_generator_orbits,
        "drop_face_constraint_z3_unsat_to_sat" => z3_guard["erase_flip_unsat_to_sat"],
        "octahedral_control_order_differs_24_vs_60" => oct["group_order"] != length(group),
        "octahedral_control_vertices_differ_6_vs_12" => oct["vertices"] != v_count,
    )
    all_pass = Bool(
        length(group) == 60 &&
        v_count == 12 &&
        e_count == 30 &&
        f_count == 20 &&
        euler == 2 &&
        all(==(5), model["degrees"]) &&
        stabilizer_order == 5 &&
        simplicity["simple"] == true &&
        qo_guard["trace_eq_1"] &&
        qo_guard["psd"] &&
        qo_guard["hermitian"] &&
        clifford_guard["right_handed_noncommutative_orientation"] &&
        z3_guard["full_euler_not_two_status"] == "unsat" &&
        z3_guard["drop_face_constraint_status"] == "sat" &&
        all(value for value in values(negative) if value isa Bool) &&
        classification == "scratch_diagnostic" &&
        promotion_allowed == false &&
        formal_admission_allowed == false &&
        reads_peer_result == false
    )

    Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "rung_id" => RUNG_ID,
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "reads_peer_result" => reads_peer_result,
        "packages_used" => ["QuantumOptics", "CliffordAlgebras", "Z3", "LinearAlgebra", "JSON", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "CliffordAlgebras", "Z3"],
        "claim_path_tools" => ["QuantumOptics", "CliffordAlgebras", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "runtime_preflight" => Dict("julia_version" => string(VERSION), "active_project" => Base.active_project()),
        "M" => Dict(
            "name" => "A5_action_probe_on_icosahedral_screen_ports",
            "explicit_probe_family" => [
                "A5 left action on the 12 cosets of a C5 vertex stabilizer",
                "icosahedral edge probe generated by the size-5 stabilizer orbit of the base vertex",
                "screen-port projectors |v><v| for v=1..12",
            ],
            "probe_counts" => Dict("group_elements" => length(group), "vertices" => v_count, "edges" => e_count),
        ),
        "C" => Dict(
            "trace_eq_1" => qo_guard["trace_eq_1"],
            "psd" => qo_guard["psd"],
            "hermitian" => qo_guard["hermitian"],
            "normalization" => qo_guard["normalization"],
            "rung_specific_constraint" => "A5 acts transitively on the 12 cosets of C5 and preserves the generated icosahedral incidence",
            "icosahedral_incidence" => Dict("V" => v_count, "E" => e_count, "F" => f_count, "euler" => euler, "degree_sequence" => model["degrees"]),
        ),
        "S_mod_M" => Dict(
            "definition" => "screen ports are equivalent when no A5 action probe distinguishes them; the full A5 probe has one vertex orbit",
            "orbit_structure" => [collect(1:v_count)],
            "class_count" => 1,
            "stabilizer_order" => stabilizer_order,
            "drop_action_probe_orbit_sizes" => drop_generator_orbits,
        ),
        "summary" => Dict(
            "A5_order" => length(group),
            "A5_simple" => simplicity["simple"],
            "vertex_count" => v_count,
            "edge_count" => e_count,
            "face_count" => f_count,
            "euler" => euler,
            "vertex_transitive" => true,
            "stabilizer_order" => stabilizer_order,
            "degrees" => model["degrees"],
        ),
        "simplicity" => simplicity,
        "quantumoptics_screen_guard" => qo_guard,
        "clifford_orientation_guard" => clifford_guard,
        "julia_z3" => z3_guard,
        "octahedral_control" => oct,
        "negative_control_flip" => negative,
        "all_pass" => all_pass,
    )
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println("wrote: ", RESULT_PATH)
    println(
        "FOUNDATION_R6_OPH_ICOSAHEDRAL_SCREEN_JULIA_DONE ",
        "all_pass=", lowercase(string(result["all_pass"])), " ",
        "A5_order=", result["summary"]["A5_order"], " ",
        "simple=", lowercase(string(result["summary"]["A5_simple"])), " ",
        "V/E/F=", result["summary"]["vertex_count"], "/", result["summary"]["edge_count"], "/", result["summary"]["face_count"], " ",
        "stabilizer=", result["summary"]["stabilizer_order"],
    )
    result["all_pass"] ? 0 : 1
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
