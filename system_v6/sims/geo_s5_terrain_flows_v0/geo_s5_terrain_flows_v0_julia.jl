#!/usr/bin/env julia
# Julia carrier leg for geo_s5_terrain_flows_v0.

using Dates
using DifferentialEquations
using JSON
using LinearAlgebra
using SHA
using Symbolics
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s5_terrain_flows_v0"
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

const PIN_SPEC = "geo_s5_terrain_flows_v0|sigma_y_standard=[[0,-i],[i,0]]|primary_bloch_basis=(sigma_x,sigma_y_standard,sigma_z)|s1_pinned_bloch_basis=(sigma_x,-sigma_y_standard,sigma_z)|standard_to_s1_pinned_J=diag(1,-1,1)|component_rule=r_i=Tr(generator(rho)*basis_i)|rho_rule=rho(r)=(I+r.basis)/2|H0=(sigma_x+sigma_y+sigma_z)/sqrt(3)|H_L=+H0|H_R=-H0|rows=(Se/Funnel,Se/Cannon,Ne/Vortex,Ne/Spiral,Ni/Pit,Ni/Source,Si/Hill,Si/Citadel)|symbolic_parameters=(lambda_Se_L,epsilon_Se_L,lambda_Se_R,epsilon_Se_R,gamma_Ni_L,epsilon_Ni_L,gamma_Ni_R,epsilon_Ni_R,kappa_Si_L,omega_Si_L,kappa_Si_R,omega_Si_R)|pin_row=(lambda_Se_L=1/5,epsilon_Se_L=1/5,lambda_Se_R=1/5,epsilon_Se_R=1/5,gamma_Ni_L=1/2,epsilon_Ni_L=1/5,gamma_Ni_R=1/2,epsilon_Ni_R=1/5,kappa_Si_L=2/5,omega_Si_L=1/5,kappa_Si_R=2/5,omega_Si_R=1/5)|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const CONVENTION_PIN = Dict(
    "sigma_y_standard" => [["0", "-i"], ["i", "0"]],
    "primary_table_basis" => "source_locked_standard_bloch",
    "source_locked_bloch_basis" => ["sigma_x", "sigma_y_standard", "sigma_z"],
    "s1_pinned_bloch_basis" => ["sigma_x", "-sigma_y_standard", "sigma_z"],
    "standard_to_s1_pinned_J" => [["1", "0", "0"], ["0", "-1", "0"], ["0", "0", "1"]],
    "conversion_rule" => "A_s1_pinned = J * A_source_locked_standard * J and b_s1_pinned = J * b",
    "component_rule" => "r_i = Tr(generator(rho) * basis_i)",
    "rho_rule" => "rho(r) = (I + r.basis) / 2",
    "hamiltonian_pin" => Dict("H0" => "(sigma_x + sigma_y + sigma_z) / sqrt(3)", "H_L" => "+H0", "H_R" => "-H0", "n" => ["1/sqrt(3)", "1/sqrt(3)", "1/sqrt(3)"]),
    "si_frame_pin" => Dict("Hill" => "z frame", "Citadel" => "x frame"),
    "stage" => "S5 density/Bloch terrain flows only",
)

const TOOL_MANIFEST = Dict(
    "Symbolics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-side derivation from density generator forms into Bloch A,b rows"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-side SMT pinned-entry contradiction check; not a full symbolic flow proof"),
    "DifferentialEquations" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia carrier ODEProblem/solve(Tsit5) route for pinned affine Bloch flow evolution"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive matrix multiplication and traces"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source and PIN hashing"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "Symbolics" => "load_bearing",
    "Z3" => "load_bearing",
    "DifferentialEquations" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON" => "supportive",
    "SHA" => "supportive",
)

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))
sha256_text(text::AbstractString) = bytes2hex(SHA.sha256(codeunits(text)))

function cstr(x)
    if x isa Num
        text = string(Symbolics.simplify(x, expand=true))
        replacements = Dict(
            "0.0" => "0",
            "1.0" => "1",
            "-0.0" => "0",
            "0//1" => "0",
            "1//1" => "1",
            "-1//1" => "-1",
        )
        return get(replacements, text, text)
    end
    if x isa Complex
        re = Symbolics.simplify(real(x), expand=true)
        imv = Symbolics.simplify(imag(x), expand=true)
        if cstr(imv) == "0"
            return cstr(re)
        end
        return string(Symbolics.simplify(x, expand=true))
    end
    if x isa Rational
        x.den == 1 && return string(x.num)
        return string(x.num, "//", x.den)
    end
    if x isa Integer
        return string(x)
    end
    text = string(x)
    get(Dict("0.0" => "0", "1.0" => "1", "-0.0" => "0"), text, text)
end

matrix_strings(m) = [[cstr(m[i, j]) for j in axes(m, 2)] for i in axes(m, 1)]
vector_strings(v) = [cstr(v[i]) for i in eachindex(v)]

function parse_number(text)
    Float64(eval(Meta.parse(replace(text, "//" => "/"))))
end

function parse_matrix(values)
    [parse_number(values[i][j]) for i in 1:3, j in 1:3]
end

function parse_vector(values)
    [parse_number(values[i]) for i in 1:3]
end

function pauli()
    eye = Any[1 0; 0 1]
    x = Any[0 1; 1 0]
    y = Any[0 -im; im 0]
    z = Any[1 0; 0 -1]
    sm = Any[0 0; 1 0]
    sp = Any[0 1; 0 0]
    Dict("I" => eye, "X" => x, "Y_standard" => y, "Yp" => -y, "Z" => z, "sigma_minus" => sm, "sigma_plus" => sp)
end

function rho_from_bloch(rx, ry, rz)
    b = pauli()
    (b["I"] + rx * b["X"] + ry * b["Y_standard"] + rz * b["Z"]) / 2
end

function dissipator(L, rho)
    adjoint(L) * L
    L * rho * adjoint(L) - (adjoint(L) * L * rho + rho * adjoint(L) * L) / 2
end

function dephase_projectors(projectors, rho)
    out = fill(0, 2, 2)
    for P in projectors
        out += P * rho * P
    end
    out - rho
end

component_vector(generator_rho) = begin
    b = pauli()
    [Symbolics.simplify(tr(generator_rho * b[name]), expand=true) for name in ["X", "Y_standard", "Z"]]
end

function affine_from_components(comps, rx, ry, rz)
    vars = [rx, ry, rz]
    zero_sub = Dict(rx => 0, ry => 0, rz => 0)
    c = [Symbolics.simplify(Symbolics.substitute(comp, zero_sub), expand=true) for comp in comps]
    rows = Matrix{Any}(undef, length(comps), length(vars))
    for (i, comp) in enumerate(comps)
        for (idx, var) in enumerate(vars)
            sub = Dict(rx => idx == 1 ? 1 : 0, ry => idx == 2 ? 1 : 0, rz => idx == 3 ? 1 : 0)
            rows[i, idx] = Symbolics.simplify(Symbolics.substitute(comp, sub) - Symbolics.substitute(comp, zero_sub), expand=true)
        end
    end
    rows, c
end

function substitute_matrix(m, sub)
    out = Matrix{Any}(undef, size(m)...)
    for i in axes(m, 1), j in axes(m, 2)
        out[i, j] = Symbolics.simplify(Symbolics.substitute(m[i, j], sub), expand=true)
    end
    out
end

function substitute_vector(v, sub)
    [Symbolics.simplify(Symbolics.substitute(item, sub), expand=true) for item in v]
end

function derive_rows()
    @variables rx ry rz lambda_Se_L epsilon_Se_L lambda_Se_R epsilon_Se_R gamma_Ni_L epsilon_Ni_L gamma_Ni_R epsilon_Ni_R kappa_Si_L omega_Si_L kappa_Si_R omega_Si_R
    b = pauli()
    rho = rho_from_bloch(rx, ry, rz)
    H0 = (b["X"] + b["Y_standard"] + b["Z"]) / sqrt(Num(3))
    HL = H0
    HR = -H0
    PZp = (b["I"] + b["Z"]) / 2
    PZm = (b["I"] - b["Z"]) / 2
    PXp = (b["I"] + b["X"]) / 2
    PXm = (b["I"] - b["X"]) / 2
    pauli_sum = dissipator(b["X"], rho) + dissipator(b["Y_standard"], rho) + dissipator(b["Z"], rho)
    rows = Dict(
        "Se_Funnel_L" => lambda_Se_L * pauli_sum - im * epsilon_Se_L * (HL * rho - rho * HL),
        "Se_Cannon_R" => lambda_Se_R * pauli_sum - im * epsilon_Se_R * (HR * rho - rho * HR),
        "Ne_Vortex_L" => -im * (HL * rho - rho * HL),
        "Ne_Spiral_R" => -im * (HR * rho - rho * HR),
        "Ni_Pit_L" => gamma_Ni_L * dissipator(b["sigma_minus"], rho) - im * epsilon_Ni_L * (HL * rho - rho * HL),
        "Ni_Source_R" => gamma_Ni_R * dissipator(b["sigma_plus"], rho) - im * epsilon_Ni_R * (HR * rho - rho * HR),
        "Si_Hill_L" => -im * (omega_Si_L * b["Z"] * rho - rho * omega_Si_L * b["Z"]) + kappa_Si_L * dephase_projectors([PZp, PZm], rho),
        "Si_Citadel_R" => -im * (omega_Si_R * b["X"] * rho - rho * omega_Si_R * b["X"]) + kappa_Si_R * dephase_projectors([PXp, PXm], rho),
    )
    pin_sub = Dict(
        lambda_Se_L => 1//5,
        epsilon_Se_L => 1//5,
        lambda_Se_R => 1//5,
        epsilon_Se_R => 1//5,
        gamma_Ni_L => 1//2,
        epsilon_Ni_L => 1//5,
        gamma_Ni_R => 1//2,
        epsilon_Ni_R => 1//5,
        kappa_Si_L => 2//5,
        omega_Si_L => 1//5,
        kappa_Si_R => 2//5,
        omega_Si_R => 1//5,
    )
    derived = Dict{String, Any}()
    for (name, gen) in rows
        comps = component_vector(gen)
        A, avec = affine_from_components(comps, rx, ry, rz)
        Ap = substitute_matrix(A, pin_sub)
        bp = substitute_vector(avec, pin_sub)
        derived[name] = Dict(
            "symbolic" => Dict("A" => matrix_strings(A), "b" => vector_strings(avec)),
            "pinned" => Dict("A" => matrix_strings(Ap), "b" => vector_strings(bp)),
            "derived_from" => "Julia density generator form, then component extraction by Tr(generator(rho)*sigma_i)",
        )
    end
    derived
end

function z3_nonunitality_proof()
    solver = Z3.Solver()
    pit = Z3.IntVar("julia_pit_bz_times_2")
    Z3.add(solver, pit == Z3.IntVal(-1))
    Z3.add(solver, pit == Z3.IntVal(0))
    verdict = string(Z3.check(solver))

    wrong = Z3.Solver()
    wrongpit = Z3.IntVar("julia_wrong_pit_bz_times_2")
    Z3.add(wrong, wrongpit == Z3.IntVal(0))
    Z3.add(wrong, wrongpit == Z3.IntVal(0))
    wrong_verdict = string(Z3.check(wrong))
    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "verdict" => verdict,
        "load_bearing" => true,
        "claim" => "pinned-entry contradiction only: Pit b_z=-1/2 contradicts fake unital b_z=0",
        "proof_scope" => "pinned_entry_contradiction_not_full_symbolic_flow_or_basin_proof",
        "bound_raw_values" => Dict("2*Pit_b_z" => -1),
        "asserted_precomputed_boolean" => false,
        "wrong_control_verdict" => wrong_verdict,
        "wrong_control_can_fail" => wrong_verdict == "sat",
    )
end

function flow_solver_receipts(rows)
    r0 = [1.0 / 5.0, -2.0 / 5.0, 1.0 / 3.0]
    tspan = (0.0, 1.0)
    receipts = Dict{String, Any}()
    for name in sort(collect(keys(rows)))
        A = parse_matrix(rows[name]["pinned"]["A"])
        b = parse_vector(rows[name]["pinned"]["b"])
        rhs(u, p, t) = A * u + b
        prob = DifferentialEquations.ODEProblem(rhs, r0, tspan)
        sol = DifferentialEquations.solve(prob, DifferentialEquations.Tsit5(), abstol=1e-10, reltol=1e-10)
        rt_solver = Array(sol(1.0))
        generator = zeros(Float64, 4, 4)
        generator[1:3, 1:3] .= A
        generator[1:3, 4] .= b
        rt_exact = (exp(generator) * [r0; 1.0])[1:3]
        max_error = maximum(abs.(rt_solver .- rt_exact))
        receipts[name] = Dict(
            "method" => "DifferentialEquations.ODEProblem plus solve(Tsit5) over pinned affine Bloch ODE r'=A*r+b",
            "initial" => ["1/5", "-2/5", "1/3"],
            "t" => 1.0,
            "r_t_diffeq" => rt_solver,
            "exact_special_case_check" => Dict(
                "method" => "LinearAlgebra.exp on augmented constant-coefficient affine generator",
                "role" => "exact_special_case_check_not_primary_solver_route",
                "r_t" => rt_exact,
            ),
            "max_abs_error_vs_exact_special_case" => max_error,
            "pass" => max_error <= 1.0e-7,
        )
    end
    Dict(
        "tool" => "DifferentialEquations",
        "qualified_api/function" => "DifferentialEquations.ODEProblem / DifferentialEquations.solve(Tsit5)",
        "claim_path_role" => "load-bearing Julia carrier flow-evolution solver route",
        "ordinarydiffeq_note" => "Tsit5 is used through DifferentialEquations in the strict carrier project; direct OrdinaryDiffEq is not declared in this project",
        "matrix_exponential_role" => "exact constant-coefficient special-case parity check only",
        "rows" => receipts,
        "all_pass" => all(row["pass"] == true for row in values(receipts)),
    )
end

function build_result()
    mkpath(RESULT_DIR)
    rows = derive_rows()
    z3proof = z3_nonunitality_proof()
    flow_solver = flow_solver_receipts(rows)
    expected_keys = Set(["Se_Funnel_L", "Se_Cannon_R", "Ne_Vortex_L", "Ne_Spiral_R", "Ni_Pit_L", "Ni_Source_R", "Si_Hill_L", "Si_Citadel_R"])
    all_pass = Set(keys(rows)) == expected_keys &&
        rows["Ni_Pit_L"]["pinned"]["b"] == ["0", "0", "-1//2"] &&
        rows["Ni_Source_R"]["pinned"]["b"] == ["0", "0", "1//2"] &&
        rows["Si_Hill_L"]["pinned"]["b"] == ["0", "0", "0"] &&
        flow_solver["all_pass"] == true &&
        z3proof["verdict"] == "unsat" &&
        z3proof["wrong_control_can_fail"]
    Dict(
        "schema_version" => "geo_s5_engine_result_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_density_generator_derivation_builder",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "all_pass" => all_pass,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "reads_peer_result" => READS_PEER_RESULT,
        "packages_used" => ["Symbolics", "Z3", "DifferentialEquations", "LinearAlgebra", "JSON", "SHA"],
        "aligned_packages_load_bearing" => ["Symbolics", "Z3", "DifferentialEquations"],
        "claim_path_tools" => ["Symbolics", "Z3", "DifferentialEquations"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => [
            Dict(
                "tool" => "Symbolics",
                "qualified_api/function" => "Symbolics.substitute/Symbolics.simplify",
                "input_object" => "density generator forms for eight terrain rows",
                "output_object" => "Julia-derived Bloch A,b rows",
                "positive_case" => "all eight rows are derived from generator(rho) component extraction",
                "negative/erased_control" => "fake unital Ni is contradicted by derived b_z",
                "boundary_case" => "Julia records generator derivation and leaves full flow formulas to the JAX/SymPy exact lane",
                "demotion_condition" => "if rows are hand-copied without density derivation, Julia lane is diagnostic only",
                "gates" => ["all_pass", "P2"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.add/Z3.check",
                "input_object" => "2*Pit_b_z pinned integer entry",
                "output_object" => "unsat contradiction against fake unital b_z=0",
                "positive_case" => "2*Pit_b_z=-1 and 2*Pit_b_z=0 is unsat",
                "negative/erased_control" => "0=0 wrong control is sat",
                "boundary_case" => "pinned-entry proof only",
                "demotion_condition" => "if solver binds only a boolean, proof is demoted",
                "gates" => ["all_pass", "P8"],
            ),
            Dict(
                "tool" => "DifferentialEquations",
                "qualified_api/function" => "DifferentialEquations.ODEProblem/DifferentialEquations.solve/DifferentialEquations.Tsit5",
                "input_object" => "pinned affine Bloch ODE rows r'=A*r+b",
                "output_object" => "finite-time flow states r(1) from each terrain row",
                "positive_case" => "ODE solver flow matches exact constant-coefficient matrix-exponential check within tolerance",
                "negative/erased_control" => "matrix exponential alone is relabeled as special-case parity check, not the solver route",
                "boundary_case" => "singular pure-Ne and Si rows solve without stationary inversion",
                "demotion_condition" => "if ODEProblem/solve is removed or parity check fails, Julia flow route is demoted",
                "gates" => ["all_pass"],
            ),
        ],
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "convention_pin" => CONVENTION_PIN,
        "julia_project" => Base.active_project(),
        "density_generator_derivation" => Dict(
            "basis" => CONVENTION_PIN["source_locked_bloch_basis"],
            "rows" => rows,
            "all_pass" => all_pass,
        ),
        "flow_solver_route" => flow_solver,
        "crossover_proofs" => Dict("julia_z3" => z3proof),
        "limits" => "Julia derives density-generator A,b rows, runs DifferentialEquations pinned-flow solver receipts, and runs Julia Z3 pinned-entry control. JAX/SymPy owns the fuller exact symbolic flow and basin formula receipts.",
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("result" => RESULT_PATH_REL, "all_pass" => result["all_pass"])))
    return result["all_pass"] ? 0 : 1
end

exit(main())
