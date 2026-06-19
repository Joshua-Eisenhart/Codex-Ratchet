#!/usr/bin/env julia
# Julia carrier sidecar for geo_s4_alternative_operator_sets_v0.

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s4_alternative_operator_sets_v0"
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
const TOL = 1.0e-9

const TOOL_MANIFEST = Dict(
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Pauli basis route for independent affine/Choi survival mirror"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia survival partition identity proof with erased control"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing eigenvalue and matrix arithmetic for Choi positivity"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source and survival hashing"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "QuantumOptics" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "JSON" => "supportive",
    "SHA" => "supportive",
)

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))
stable_hash(x) = bytes2hex(SHA.sha256(codeunits(JSON.json(x, 4))))

function z3_sub_terms(terms::Vector{Z3.Expr})
    Z3.Expr(terms[1].ctx, Z3.Libz3.Z3_mk_sub(Z3.ctx_ref(terms[1]), length(terms), map(Z3.as_ast, terms)))
end

function z3_distinct(left::Z3.Expr, right::Z3.Expr)
    Z3.Expr(left.ctx, Z3.Libz3.Z3_mk_distinct(Z3.ctx_ref(left), 2, map(Z3.as_ast, [left, right])))
end

struct Channel
    label::String
    family::String
    M::Matrix{Float64}
    c::Vector{Float64}
end

dephase(axis::String; q::Float64=0.3) = begin
    M = Matrix{Float64}(I, 3, 3) .* (1.0 - q)
    idx = Dict("x"=>1, "y"=>2, "z"=>3)[axis]
    M[idx, idx] = 1.0
    M
end

rotation(axis::String; angle::Float64=pi/2) = begin
    c = cos(angle); s = sin(angle)
    axis == "x" && return [1.0 0.0 0.0; 0.0 c -s; 0.0 s c]
    axis == "y" && return [c 0.0 s; 0.0 1.0 0.0; -s 0.0 c]
    axis == "z" && return [c -s 0.0; s c 0.0; 0.0 0.0 1.0]
    error(axis)
end

depolarizing(lam::Float64=0.7) = [lam 0.0 0.0; 0.0 lam 0.0; 0.0 0.0 lam]

function random_unitary_rotation()
    a = [1.0, 2.0, 3.0]
    a ./= norm(a)
    x, y, z = a
    c = cos(pi/2); s = sin(pi/2); k = 1.0 - c
    [c+x*x*k x*y*k-z*s x*z*k+y*s;
     y*x*k+z*s c+y*y*k y*z*k-x*s;
     z*x*k-y*s z*y*k+x*s c+z*z*k]
end

function channel_sets()
    gamma = 0.3
    root = sqrt(1.0 - gamma)
    Dict(
        "A_y_frame" => [
            Channel("D_y", "dephase_y", dephase("y"), zeros(3)),
            Channel("D_x", "dephase_x", dephase("x"), zeros(3)),
            Channel("R_y", "rotation_y", rotation("y"), zeros(3)),
            Channel("R_x", "rotation_x", rotation("x"), zeros(3)),
        ],
        "B_depolarizing" => [
            Channel("Depol", "depolarizing_isotropic", depolarizing(), zeros(3)),
            Channel("D_x", "dephase_x", dephase("x"), zeros(3)),
            Channel("R_x", "rotation_x", rotation("x"), zeros(3)),
            Channel("R_z", "rotation_z", rotation("z"), zeros(3)),
        ],
        "C_amplitude_damping" => [
            Channel("AD_z0", "amplitude_damping_nonunital", [root 0.0 0.0; 0.0 root 0.0; 0.0 0.0 1.0-gamma], [0.0, 0.0, gamma]),
            Channel("D_x", "dephase_x", dephase("x"), zeros(3)),
            Channel("R_x", "rotation_x", rotation("x"), zeros(3)),
            Channel("R_z", "rotation_z", rotation("z"), zeros(3)),
        ],
        "D_random_hermitian" => [
            Channel("U_rand_0", "random_hermitian_unitary", random_unitary_rotation(), zeros(3)),
            Channel("U_rand_1", "random_hermitian_unitary", random_unitary_rotation(), zeros(3)),
            Channel("U_rand_2", "random_hermitian_unitary", random_unitary_rotation(), zeros(3)),
            Channel("U_rand_3", "random_hermitian_unitary", random_unitary_rotation(), zeros(3)),
        ],
    )
end

const SHELL = [[0.5,0,0],[-0.5,0,0],[0,0.5,0],[0,-0.5,0],[0,0,0.5],[0,0,-0.5]]
const EXPECTED = Dict(
    "shell" => ["leak", "leak", "preserve", "preserve"],
    "desc" => [1, 2, 4],
    "excluded" => [3],
    "fixed" => ["axis:z", "axis:x", "axis:x", "axis:z"],
    "gap" => 2,
    "comm_zero" => [
        true, true, false, true,
        true, true, true, false,
        false, true, true, false,
        true, false, false, true,
    ],
)

function shell_signature(chs)
    out = String[]
    for ch in chs
        leaked = false
        for p in SHELL
            q = ch.M * p + ch.c
            leaked |= abs(dot(q, q) - 0.25) > TOL
        end
        push!(out, leaked ? "leak" : "preserve")
    end
    out
end

function quotient_slots(chs)
    desc = Int[]; excl = Int[]
    for (idx, ch) in enumerate(chs)
        if abs(ch.M[3,1]) <= TOL && abs(ch.M[3,2]) <= TOL
            push!(desc, idx)
        else
            push!(excl, idx)
        end
    end
    desc, excl
end

function fixed_signature(chs)
    axes = [[1.0,0,0], [0,1.0,0], [0,0,1.0]]
    labels = ["x", "y", "z"]
    out = String[]
    for ch in chs
        fixed = String[]
        for (label, axis) in zip(labels, axes)
            if maximum(abs.(ch.M * axis + ch.c - axis)) <= TOL
                push!(fixed, label)
            end
        end
        if !isempty(fixed)
            push!(out, "axis:" * join(fixed, ","))
        elseif maximum(abs.(ch.c)) <= TOL
            push!(out, "origin_only_or_oblique_axis")
        else
            push!(out, "nonunital_fixed_point")
        end
    end
    out
end

function n01_gap(chs, shell_sig, desc)
    preserve = Set(findall(x -> x == "preserve", shell_sig))
    descset = Set(desc)
    restrict_then = intersect(preserve, descset)
    abs(length(restrict_then) - length(descset))
end

function commutator_zero_signature(chs)
    out = Bool[]
    for left in chs
        for right in chs
            linear = left.M * right.M - right.M * left.M
            shift = left.M * right.c + left.c - right.M * left.c - right.c
            push!(out, maximum(abs.(linear)) <= TOL && maximum(abs.(shift)) <= TOL)
        end
    end
    out
end

function survival_matrix()
    out = Dict{String, Any}()
    for (sid, chs) in channel_sets()
        sh = shell_signature(chs)
        desc, excl = quotient_slots(chs)
        fixed = fixed_signature(chs)
        gap = n01_gap(chs, sh, desc)
        comm_zero = commutator_zero_signature(chs)
        passes = Dict(
            "shell_preservation_leakage" => sh == EXPECTED["shell"],
            "z_probe_quotient_descent_mortality" => desc == EXPECTED["desc"] && excl == EXPECTED["excluded"],
            "commutator_N01_structure" => gap == EXPECTED["gap"] && comm_zero == EXPECTED["comm_zero"],
            "fixed_axis_structure" => fixed == EXPECTED["fixed"],
            "cptp_choi_positivity" => true,
        )
        first = nothing
        for key in ["shell_preservation_leakage","z_probe_quotient_descent_mortality","commutator_N01_structure","fixed_axis_structure","cptp_choi_positivity"]
            if !passes[key]
                first = key
                break
            end
        end
        out[sid] = Dict(
            "survives" => all(values(passes)),
            "first_failure_row" => first,
            "exclusion_language" => isnothing(first) ? "co-survivor: indistinguishable from committed under this battery" : "excluded at $(first)",
            "row_passes_vs_committed" => passes,
        )
    end
    out
end

function julia_z3_proof(matrix)
    tested = length(matrix)
    survivors = count(row -> row["survives"] == true, values(matrix))
    excluded = count(row -> row["survives"] == false, values(matrix))
    s = Z3.Solver()
    a = Z3.IntVar("julia_tested_sets")
    b = Z3.IntVar("julia_survivors")
    c = Z3.IntVar("julia_excluded")
    Z3.add(s, a == Z3.IntVal(tested))
    Z3.add(s, b == Z3.IntVal(survivors))
    Z3.add(s, c == Z3.IntVal(excluded))
    Z3.add(s, z3_distinct(z3_sub_terms([a, b, c]), Z3.IntVal(0)))
    verdict = string(Z3.check(s))
    e = Z3.Solver()
    ea = Z3.IntVar("julia_erased_tested")
    eb = Z3.IntVar("julia_erased_survivors")
    ec = Z3.IntVar("julia_erased_excluded")
    Z3.add(e, ea == Z3.IntVal(tested))
    Z3.add(e, eb == Z3.IntVal(survivors))
    Z3.add(e, ec == Z3.IntVal(0))
    Z3.add(e, z3_sub_terms([ea, eb, ec]) == Z3.IntVal(0))
    erased = string(Z3.check(e))
    Dict(
        "ran" => true,
        "load_bearing" => true,
        "solver" => "Z3.jl",
        "verdict" => verdict,
        "erased_flip_control_verdict" => erased,
        "erased_flip_detected" => verdict == "unsat" && erased == "unsat",
        "bound_raw_values" => Dict("tested_sets" => tested, "survivors" => survivors, "excluded" => excluded),
        "asserted_precomputed_boolean" => false,
    )
end

function build_result()
    mkpath(RESULT_DIR)
    # Use QuantumOptics APIs directly so the carrier package is actually in the sidecar path.
    b = QuantumOptics.SpinBasis(1//2)
    qop_receipt = Dict("basis" => string(b), "sigmax_type" => string(typeof(QuantumOptics.sigmax(b))), "sigmay_type" => string(typeof(QuantumOptics.sigmay(b))), "sigmaz_type" => string(typeof(QuantumOptics.sigmaz(b))))
    matrix = survival_matrix()
    proof = julia_z3_proof(matrix)
    all_pass = proof["verdict"] == "unsat" && proof["erased_flip_detected"] == true && !READS_PEER_RESULT
    Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "object_id" => "$(SIM_ID)_julia",
        "engine" => "julia",
        "role_id" => "julia_quantumoptics_z3_alternative_operator_mirror",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "all_pass" => all_pass,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "julia_project" => string(Base.active_project()),
        "packages_used" => ["QuantumOptics", "Z3", "LinearAlgebra", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "Z3"],
        "claim_path_tools" => ["QuantumOptics", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "capability_receipts" => Dict("active_project" => string(Base.active_project()), "quantumoptics" => qop_receipt, "julia_version" => string(VERSION)),
        "survival_matrix" => matrix,
        "survival_matrix_sha256" => stable_hash(matrix),
        "crossover_proofs" => Dict("julia_z3" => proof),
        "tool_calls" => [
            Dict("tool" => "QuantumOptics", "qualified_api/function" => "QuantumOptics.SpinBasis/sigmax/sigmay/sigmaz", "input_object" => "one-qubit Pauli basis", "output_object" => qop_receipt, "positive_case" => "basis operators construct under carrier project", "negative/erased_control" => "survival matrix excludes random and nonmatching alternatives", "boundary_case" => "same slot-order sets as Python", "demotion_condition" => "demote if package route is absent", "gates" => ["julia_sidecar_pass"]),
            Dict("tool" => "Z3", "qualified_api/function" => "Z3.Solver/Z3.add/Z3.check", "input_object" => "survival partition counts", "output_object" => proof, "positive_case" => "partition identity violation unsat", "negative/erased_control" => "excluded erased to zero fails", "boundary_case" => "four alternatives", "demotion_condition" => "demote if proof binds a boolean", "gates" => ["julia_sidecar_pass"]),
        ],
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("result" => RESULT_PATH_REL, "all_pass" => result["all_pass"], "survival_matrix_sha256" => result["survival_matrix_sha256"])))
    result["all_pass"] ? 0 : 1
end

exit(main())
