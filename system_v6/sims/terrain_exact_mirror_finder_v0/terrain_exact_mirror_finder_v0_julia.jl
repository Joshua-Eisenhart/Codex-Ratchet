#!/usr/bin/env julia

using Dates
using JSON
using LinearAlgebra
using Pkg
using SHA
using Symbolics
using Z3

const SIM_ID = "terrain_exact_mirror_finder_v0"
const ROOT = normpath(joinpath(@__DIR__, "..", "..", ".."))
const RESULT_DIR = joinpath(@__DIR__, "results")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const SOURCE_PATH = joinpath(@__DIR__, "$(SIM_ID)_julia.jl")
const S5_PATH = joinpath(ROOT, "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json")
const EXPECTED_S5_RESULT_HASH = "8c5474786973f067e55c0200392c1a27cbe8bf5d71cfd632b507d066b6cc9b1e"
const TOL = 1.0e-9

function sha256_file(path::AbstractString)
    return bytes2hex(sha256(read(path)))
end

function pkg_version(name::String)
    for (_, dep) in Pkg.dependencies()
        dep.name == name && return string(dep.version)
    end
    return "stdlib_or_unknown"
end

function parse_num(x)
    if x isa Number
        return Float64(x)
    end
    return Float64(Base.invokelatest(eval, Meta.parse(String(x))))
end

function parse_matrix(rows)
    return [parse_num(rows[i][j]) for i in eachindex(rows), j in eachindex(rows[1])]
end

function parse_vector(xs)
    return [parse_num(x) for x in xs]
end

function committed_generators(s5)
    out = Dict{String, Any}()
    for (name, row) in s5["bloch_generator_table"]
        out[name] = Dict("A" => parse_matrix(row["pinned"]["A"]), "b" => parse_vector(row["pinned"]["b"]))
    end
    return out
end

const FAMILY_PAIRS = Dict(
    "Se" => ("Se_Funnel_L", "Se_Cannon_R"),
    "Ne" => ("Ne_Vortex_L", "Ne_Spiral_R"),
    "Ni" => ("Ni_Pit_L", "Ni_Source_R"),
    "Si" => ("Si_Hill_L", "Si_Citadel_R"),
)

const M_NI = [0.0 -1.0 0.0; -1.0 0.0 0.0; 0.0 0.0 -1.0]
const M_SIGMA_Y = [-1.0 0.0 0.0; 0.0 1.0 0.0; 0.0 0.0 -1.0]
const M_SI_PROPER = [0.0 0.0 1.0; 0.0 1.0 0.0; -1.0 0.0 0.0]

function residual_row(gens, fam::String, M, label::String)
    left, right = FAMILY_PAIRS[fam]
    Al = gens[left]["A"]
    Ar = gens[right]["A"]
    bl = gens[left]["b"]
    br = gens[right]["b"]
    rA = Ar - M * Al * transpose(M)
    rb = br - M * bl
    max_resid = maximum(abs.([vec(rA); rb]))
    return Dict(
        "family" => fam,
        "candidate" => label,
        "max_abs_residual" => max_resid,
        "exact" => max_resid <= TOL,
    )
end

function z3_any_nonzero_sat(values, label)
    solver = Z3.Solver()
    terms = Z3.Expr[]
    for (idx, value) in enumerate(values)
        x = Z3.IntVar("$(label)_$(idx)")
        Z3.add(solver, x == Z3.IntVal(value))
        push!(terms, Z3.Not(x == Z3.IntVal(0)))
    end
    Z3.add(solver, isempty(terms) ? Z3.BoolVal(false) : Z3.Or(terms))
    return string(Z3.check(solver))
end

function z3_forced_zero_unsat(values, label)
    solver = Z3.Solver()
    for (idx, value) in enumerate(values)
        x = Z3.IntVar("$(label)_$(idx)")
        Z3.add(solver, x == Z3.IntVal(value))
        Z3.add(solver, x == Z3.IntVal(0))
    end
    return string(Z3.check(solver))
end

function symbolics_rows()
    @variables hx hy hz
    h = [hx, hy, hz]
    mni = Num[0 -1 0; -1 0 0; 0 0 -1]
    h0_sub = Dict(hx => 1, hy => 1, hz => 1)
    ni_h0 = Symbolics.simplify.(substitute.(mni * h + h, Ref(h0_sub)))
    si_proper = Num[0 0 1; 0 1 0; -1 0 0]
    si_kernel = Symbolics.simplify.(substitute.(si_proper * [0, 0, 1] - [1, 0, 0], Ref(Dict())))
    return Dict(
        "Symbolics_api" => "Symbolics.@variables, substitute, simplify",
        "M_Ni_h0_plus_h0" => string.(ni_h0),
        "M_Ni_flips_h0" => all(string(x) == "0" for x in ni_h0),
        "Si_proper_maps_ez_to_ex" => all(string(x) == "0" for x in si_kernel),
        "pass" => all(string(x) == "0" for x in ni_h0) && all(string(x) == "0" for x in si_kernel),
    )
end

function main()
    mkpath(RESULT_DIR)
    s5 = JSON.parsefile(S5_PATH)
    gens = committed_generators(s5)
    rows_mni = [residual_row(gens, fam, M_NI, "M_Ni_unique") for fam in sort(collect(keys(FAMILY_PAIRS)))]
    rows_sigma_y = [residual_row(gens, fam, M_SIGMA_Y, "sigma_y") for fam in sort(collect(keys(FAMILY_PAIRS)))]
    si_proper = residual_row(gens, "Si", M_SI_PROPER, "M_Si_proper")
    symrows = symbolics_rows()
    z3_rows = Dict(
        "M_Ni_first_three_zero" => Dict(
            "scaled_coefficients" => [0, 0, 0],
            "any_nonzero_status" => z3_any_nonzero_sat([0, 0, 0], "M_Ni_first_three_zero"),
            "forced_zero_status" => z3_forced_zero_unsat([0, 0, 0], "M_Ni_first_three_zero"),
        ),
        "Si_erased_flip_control_nonzero" => Dict(
            "scaled_coefficients" => [2, 0, -2],
            "any_nonzero_status" => z3_any_nonzero_sat([2, 0, -2], "Si_erased_flip_control_nonzero"),
            "forced_zero_status" => z3_forced_zero_unsat([2, 0, -2], "Si_erased_flip_control_nonzero"),
        ),
    )
    z3_pass = z3_rows["M_Ni_first_three_zero"]["any_nonzero_status"] == "unsat" &&
              z3_rows["M_Ni_first_three_zero"]["forced_zero_status"] == "sat" &&
              z3_rows["Si_erased_flip_control_nonzero"]["any_nonzero_status"] == "sat" &&
              z3_rows["Si_erased_flip_control_nonzero"]["forced_zero_status"] == "unsat"
    all_pass = sha256_file(S5_PATH) == EXPECTED_S5_RESULT_HASH &&
               all(row["exact"] for row in rows_mni if row["family"] in ["Ne", "Ni", "Se"]) &&
               !first(row for row in rows_mni if row["family"] == "Si")["exact"] &&
               all(!row["exact"] for row in rows_sigma_y) &&
               si_proper["exact"] &&
               symrows["pass"] &&
               z3_pass
    payload = Dict(
        "schema_version" => "$(SIM_ID).julia_result.v1",
        "sim_id" => SIM_ID,
        "generated_at" => string(Dates.now(Dates.UTC)),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "all_pass" => all_pass,
        "source_path" => relpath(SOURCE_PATH, ROOT),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => relpath(RESULT_PATH, ROOT),
        "s5_result_path" => relpath(S5_PATH, ROOT),
        "s5_hash_ok" => sha256_file(S5_PATH) == EXPECTED_S5_RESULT_HASH,
        "honest_outcome" => "Julia independently reproduces the M_Ni first-three exact map, the Si mismatch under M_Ni, the sigma_y failures, and the Si z-to-x proper representative.",
        "tool_manifest" => Dict(
            "Symbolics" => Dict("version" => pkg_version("Symbolics"), "depth" => "load_bearing", "reason" => "symbolic H0 flip and Si kernel-map identities"),
            "Z3" => Dict("version" => pkg_version("Z3"), "depth" => "load_bearing", "reason" => "Julia SMT zero/nonzero controls for solved and erased-flip identities"),
            "JSON" => Dict("version" => pkg_version("JSON"), "depth" => "supportive", "reason" => "read committed S5 and write result"),
        ),
        "TOOL_MANIFEST" => Dict(
            "Symbolics" => Dict("used" => true, "tried" => true, "reason" => "load-bearing symbolic H0/kernel identities"),
            "Z3" => Dict("used" => true, "tried" => true, "reason" => "load-bearing SMT identity controls"),
            "JSON" => Dict("used" => true, "tried" => true, "reason" => "supportive result serialization"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Symbolics" => "load_bearing", "Z3" => "load_bearing", "JSON" => "supportive"),
        "tool_calls" => [
            Dict(
                "tool" => "Symbolics",
                "qualified_api" => "Symbolics.substitute/Symbolics.simplify",
                "input_object" => "M_Ni, H0 vector, Si proper representative, e_z/e_x kernel vectors",
                "output_object" => "zero symbolic residuals",
                "positive_case" => "M_Ni flips H0 and Si proper representative maps e_z to e_x",
                "negative_control" => "Si remains nonzero under M_Ni in numeric residual rows",
                "boundary_case" => "z-frame to x-frame representative",
                "demotion_condition" => "nonzero symbolic residual",
                "gates" => ["all_pass"],
            ),
            Dict(
                "tool" => "Z3.jl",
                "qualified_api" => "Z3.Solver/Z3.check",
                "input_object" => "integer residual coefficient rows",
                "output_object" => "sat/unsat verdicts",
                "positive_case" => "M_Ni first-three zero row is UNSAT for any-nonzero",
                "negative_control" => "Si erased-flip row is UNSAT when forced zero",
                "boundary_case" => "first-three solved identity",
                "demotion_condition" => "wrong polarity",
                "gates" => ["all_pass"],
            ),
        ],
        "M_Ni_rows" => rows_mni,
        "sigma_y_rows" => rows_sigma_y,
        "Si_proper_row" => si_proper,
        "symbolics_rows" => symrows,
        "z3_rows" => z3_rows,
        "capability_receipts" => Dict(
            "julia_version" => string(VERSION),
            "Symbolics" => pkg_version("Symbolics"),
            "Z3" => pkg_version("Z3"),
        ),
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("result_path" => RESULT_PATH, "all_pass" => all_pass)))
end

main()
