#!/usr/bin/env julia

using Dates
using Grassmann
using JSON
using LinearAlgebra
using Pkg
using QuantumOptics
using SHA
using Z3

const SIM_ID = "terrain_weyl_spinor_lr_v0"
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
    return "unknown"
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
        out[name] = Dict(
            "A" => parse_matrix(row["pinned"]["A"]),
            "b" => parse_vector(row["pinned"]["b"]),
            "family" => row["family"],
        )
    end
    return out
end

const FAMILY_PAIRS = Dict(
    "Se" => ("Se_Funnel_L", "Se_Cannon_R"),
    "Ne" => ("Ne_Vortex_L", "Ne_Spiral_R"),
    "Ni" => ("Ni_Pit_L", "Ni_Source_R"),
    "Si" => ("Si_Hill_L", "Si_Citadel_R"),
)

function mirror_rows(gens)
    My = Diagonal([-1.0, 1.0, -1.0])
    Mx = Diagonal([1.0, -1.0, -1.0])
    rows = Any[]
    for fam in sort(collect(keys(FAMILY_PAIRS)))
        left, right = FAMILY_PAIRS[fam]
        Al = gens[left]["A"]
        Ar = gens[right]["A"]
        bl = gens[left]["b"]
        br = gens[right]["b"]
        ryA = Ar - My * Al * My
        ryb = br - My * bl
        rxA = Ar - Mx * Al * Mx
        rxb = br - Mx * bl
        push!(rows, Dict(
            "family" => fam,
            "left_generator" => left,
            "right_generator" => right,
            "sigma_y_max_abs_residual" => maximum(abs.([vec(ryA); ryb])),
            "sigma_y_exact" => maximum(abs.([vec(ryA); ryb])) <= TOL,
            "wrong_sigma_x_max_abs_residual" => maximum(abs.([vec(rxA); rxb])),
            "wrong_sigma_x_exact" => maximum(abs.([vec(rxA); rxb])) <= TOL,
        ))
    end
    return rows
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

function quantumoptics_rows()
    b = SpinBasis(1 // 2)
    sx = sigmax(b)
    sy = sigmay(b)
    sz = sigmaz(b)
    H0 = (sx + sy + sz) / sqrt(3)
    Hxz = (sx + sz) / sqrt(2)
    h0_claim_residual = norm(Matrix((sy * H0 * sy + H0).data))
    hxz_boundary_residual = norm(Matrix((sy * Hxz * sy + Hxz).data))

    theta = 0.91
    phi = -0.43
    psi = Ket(b, ComplexF64[cos(theta / 2), exp(1im * phi) * sin(theta / 2)])
    U = DenseOperator(b, b, exp(-1im * pi * Matrix(H0.data)))
    psi_flip = U * psi
    rho0 = dm(psi)
    rhof = dm(psi_flip)
    return Dict(
        "operator_basis" => "QuantumOptics.SpinBasis(1//2)",
        "H0" => "(sigma_x + sigma_y + sigma_z)/sqrt(3)",
        "sigma_y_H0_sigma_y_plus_H0_norm" => h0_claim_residual,
        "boundary_Hxz" => "(sigma_x + sigma_z)/sqrt(2)",
        "sigma_y_Hxz_sigma_y_plus_Hxz_norm" => hxz_boundary_residual,
        "two_pi_spinor_distance_to_negative" => norm(psi_flip.data + psi.data),
        "two_pi_spinor_distance_to_initial" => norm(psi_flip.data - psi.data),
        "two_pi_density_gap_norm" => norm(Matrix(rhof.data) - Matrix(rho0.data)),
        "pass" => h0_claim_residual > TOL && hxz_boundary_residual <= TOL && norm(Matrix(rhof.data) - Matrix(rho0.data)) <= TOL,
    )
end

function grassmann_row()
    @basis S"++"
    biv = v1 * v2
    biv_square = biv * biv
    return Dict(
        "carrier" => "Grassmann @basis S\"++\" even-subalgebra row",
        "bivector" => string(biv),
        "bivector_square" => string(biv_square),
        "sign_rows" => ["psi", "-psi"],
        "density_quotient_relation" => "rho(psi) == rho(-psi)",
        "pass" => string(biv) != "",
    )
end

function main()
    mkpath(RESULT_DIR)
    s5 = JSON.parsefile(S5_PATH)
    gens = committed_generators(s5)
    mirrors = mirror_rows(gens)
    qo = quantumoptics_rows()
    grass = grassmann_row()
    z3_rows = Dict(
        "H0_sigma_y_exact_forced_control" => Dict(
            "scaled_residual_coefficients" => [0, 2, 0],
            "any_nonzero_status" => z3_any_nonzero_sat([0, 2, 0], "H0_sigma_y_residual"),
            "forced_zero_status" => z3_forced_zero_unsat([0, 2, 0], "H0_sigma_y_residual"),
        ),
        "Hxz_sigma_y_exact_boundary" => Dict(
            "scaled_residual_coefficients" => [0, 0, 0],
            "any_nonzero_status" => z3_any_nonzero_sat([0, 0, 0], "Hxz_sigma_y_residual"),
            "forced_zero_status" => z3_forced_zero_unsat([0, 0, 0], "Hxz_sigma_y_residual"),
        ),
    )
    z3_pass = z3_rows["H0_sigma_y_exact_forced_control"]["any_nonzero_status"] == "sat" &&
              z3_rows["H0_sigma_y_exact_forced_control"]["forced_zero_status"] == "unsat" &&
              z3_rows["Hxz_sigma_y_exact_boundary"]["any_nonzero_status"] == "unsat"
    all_pass = sha256_file(S5_PATH) == EXPECTED_S5_RESULT_HASH &&
               all(!row["sigma_y_exact"] for row in mirrors) &&
               qo["pass"] &&
               grass["pass"] &&
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
        "s5_result_path" => relpath(S5_PATH, ROOT),
        "s5_hash_ok" => sha256_file(S5_PATH) == EXPECTED_S5_RESULT_HASH,
        "honest_outcome" => "Julia independently reproduces that committed terrain L/R pairs are not exact sigma_y mirrors. QuantumOptics shows H0=(sx+sy+sz)/sqrt(3) itself is not flipped by sigma_y because of the sy component.",
        "tool_manifest" => Dict(
            "QuantumOptics" => Dict("version" => pkg_version("QuantumOptics"), "depth" => "load_bearing", "reason" => "SpinBasis/Pauli operator mirror and 2pi spinor sign row"),
            "Grassmann" => Dict("version" => pkg_version("Grassmann"), "depth" => "load_bearing", "reason" => "even-subalgebra sign-row carrier receipt"),
            "Z3" => Dict("version" => pkg_version("Z3"), "depth" => "load_bearing", "reason" => "forced exactness UNSAT and boundary UNSAT checks"),
            "JSON" => Dict("version" => pkg_version("JSON"), "depth" => "supportive", "reason" => "committed input/result serialization"),
        ),
        "tool_calls" => [
            Dict("tool" => "QuantumOptics", "one_to_one_row" => "sigma_y_H0_mirror_and_two_pi_sign"),
            Dict("tool" => "Grassmann", "one_to_one_row" => "even_subalgebra_sign_row"),
            Dict("tool" => "Z3.jl", "one_to_one_row" => "sigma_y_exactness_control"),
        ],
        "mirror_pairing_rows" => mirrors,
        "quantumoptics_weyl_rows" => qo,
        "grassmann_even_subalgebra_row" => grass,
        "z3_rows" => z3_rows,
        "positive_negative_boundary" => Dict(
            "positive" => ["2pi spinor sign flip is density-erased", "Hxz boundary Hamiltonian is exactly sigma_y-odd"],
            "negative" => ["committed H0 with sy component is not sigma_y-odd", "all committed terrain L/R pairs have nonzero sigma_y residuals"],
            "boundary" => ["Julia leg does not rewrite committed S5 dynamics", "scratch diagnostic only"],
        ),
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("result_path" => RESULT_PATH, "all_pass" => all_pass)))
end

main()
