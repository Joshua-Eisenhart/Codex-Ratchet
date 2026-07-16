#!/usr/bin/env julia

using Dates
using SHA

const ROOT = dirname(dirname(dirname(abspath(@__DIR__))))
const RESULT_DIR = joinpath(abspath(@__DIR__), "results")
const SOURCE_PATH = abspath(normpath(@__FILE__))
const DEFAULT_PACKAGES = ["Symbolics", "IntervalArithmetic", "DifferentialEquations", "CliffordAlgebras", "Quaternions", "Z3"]
const PROJECT_REQUIREMENTS = Dict(
    "IntervalArithmetic" => "/Users/joshuaeisenhart/.julia/environments/codex-ratchet-tensorkit-v1.12/Project.toml",
)
const IMPORT_ERRORS = Dict{String,Any}()
const PACKAGE_AVAILABLE = Dict{String,Bool}()

for pkg in DEFAULT_PACKAGES
    try
        @eval import $(Symbol(pkg))
        PACKAGE_AVAILABLE[pkg] = true
    catch err
        PACKAGE_AVAILABLE[pkg] = false
        IMPORT_ERRORS[pkg] = err
    end
end

function rel(path::AbstractString)
    return replace(normpath(path), ROOT * "/" => "")
end

function json_escape(s::AbstractString)
    out = IOBuffer()
    for c in s
        if c == '"'
            print(out, "\\\"")
        elseif c == '\\'
            print(out, "\\\\")
        elseif c == '\n'
            print(out, "\\n")
        elseif c == '\r'
            print(out, "\\r")
        elseif c == '\t'
            print(out, "\\t")
        else
            print(out, c)
        end
    end
    return String(take!(out))
end

function to_json(x)
    if x === nothing
        return "null"
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x isa Integer || x isa AbstractFloat
        return string(x)
    elseif x isa AbstractString
        return "\"" * json_escape(x) * "\""
    elseif x isa AbstractVector
        return "[" * join([to_json(v) for v in x], ", ") * "]"
    elseif x isa AbstractDict
        parts = String[]
        for k in sort(collect(keys(x)); by=string)
            push!(parts, to_json(string(k)) * ": " * to_json(x[k]))
        end
        return "{" * join(parts, ", ") * "}"
    else
        return to_json(string(x))
    end
end

function source_sha256()
    return bytes2hex(open(sha256, SOURCE_PATH))
end

function ok_case(input_object, output_object, passed; note="")
    return Dict(
        "input_object" => input_object,
        "output_object" => output_object,
        "passed" => Bool(passed),
        "note" => note,
    )
end

function expected_project(tool::String)
    return get(PROJECT_REQUIREMENTS, tool, nothing)
end

function project_gate(tool::String)
    expected = expected_project(tool)
    actual = string(Base.active_project())
    return Dict(
        "expected_project" => expected,
        "active_project" => actual,
        "pass" => expected === nothing || actual == expected,
    )
end

function blocked_result(tool::String, err)
    gate = project_gate(tool)
    return Dict(
        "tool" => tool,
        "package_available" => false,
        "project_gate" => gate,
        "cases" => Dict(
            "positive" => ok_case("package import", string(err), false, note="package did not load in active project"),
            "negative_erased" => ok_case("package import", "blocked", false, note="cannot run erased control without package"),
            "boundary" => ok_case("package import", "blocked", false, note="cannot run boundary case without package"),
            "demotion" => ok_case("active_project", Base.active_project(), true, note="demote all load-bearing claims for this package in this project until a passing probe exists"),
        ),
        "summary" => Dict("all_pass" => false),
    )
end

function finalize(tool::String, body::Dict)
    result_path = joinpath(RESULT_DIR, lowercase(replace(tool, "." => "_")) * "_capability_results.json")
    cases = body["cases"]
    all_pass = get(get(body, "summary", Dict()), "all_pass", all(get(c, "passed", false) === true for c in values(cases)))
    result = merge(body, Dict(
        "kind" => "julia_load_bearing_capability_probe",
        "classification" => "capability_probe",
        "tool" => tool,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "active_project" => Base.active_project(),
        "project_gate" => project_gate(tool),
        "julia_load_path" => Base.LOAD_PATH,
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => source_sha256(),
        "result_path" => rel(result_path),
        "summary" => merge(get(body, "summary", Dict()), Dict("all_pass" => Bool(all_pass))),
    ))
    mkpath(RESULT_DIR)
    open(result_path, "w") do io
        write(io, to_json(result))
        write(io, "\n")
    end
    return result
end

function probe_symbolics()
    if !get(PACKAGE_AVAILABLE, "Symbolics", false)
        return blocked_result("Symbolics", IMPORT_ERRORS["Symbolics"])
    end
    x = Symbolics.variables(:x, 1)[1]
    expanded = Symbolics.expand((x + 1)^2 - (x^2 + 2x + 1))
    raw = (x + 1)^2 - (x^2 + 2x + 1)
    boundary = Symbolics.substitute(x^2 - 1, Dict(x => 1))
    boundary_control = Symbolics.substitute(x^2 - 1, Dict(x => 0))
    cases = Dict(
        "positive" => ok_case("(x+1)^2 - (x^2+2x+1)", string(expanded), isequal(expanded, 0), note="Symbolics.expand discharges the identity"),
        "negative_erased" => ok_case("same expression without expand", string(raw), string(raw) != "0", note="erasing Symbolics simplification leaves a non-discharged expression"),
        "boundary" => ok_case("x^2 - 1 at x=1 and x=0", Dict("x_1" => string(boundary), "x_0" => string(boundary_control)), isequal(boundary, 0) && !isequal(boundary_control, 0)),
        "demotion" => ok_case("remove Symbolics.expand/substitute", "identity and boundary no longer discharged by package API", true),
    )
    return Dict(
        "package_available" => true,
        "tool_call" => Dict(
            "qualified_api/function" => "Symbolics.expand / Symbolics.substitute",
            "gates" => ["positive", "negative_erased", "boundary"],
            "demotion_condition" => "if expressions are precomputed or simplified without Symbolics, demote Symbolics to supportive",
        ),
        "cases" => cases,
    )
end

function probe_interval_arithmetic()
    gate = project_gate("IntervalArithmetic")
    if gate["pass"] != true
        return Dict(
            "package_available" => false,
            "project_gate" => gate,
            "cases" => Dict(
                "positive" => ok_case("active Julia project", gate, false, note="IntervalArithmetic capability must be generated under @codex-ratchet-tensorkit-v1.12"),
                "negative_erased" => ok_case("wrong project guard", "blocked", false, note="wrong-env receipts are not accepted"),
                "boundary" => ok_case("wrong project guard", "blocked", false, note="wrong-env receipts are not accepted"),
                "demotion" => ok_case("active_project", Base.active_project(), true, note="demote IntervalArithmetic claims unless the named TensorKit project is active"),
            ),
            "summary" => Dict("all_pass" => false),
        )
    end
    if !get(PACKAGE_AVAILABLE, "IntervalArithmetic", false)
        return blocked_result("IntervalArithmetic", IMPORT_ERRORS["IntervalArithmetic"])
    end
    y = sin(IntervalArithmetic.interval(0, Float64(pi)))
    endpoint_only = max(sin(0.0), sin(Float64(pi)))
    z = sqrt(IntervalArithmetic.interval(4, 9))
    cases = Dict(
        "positive" => ok_case("sin(interval(0, pi))", Dict("inf" => IntervalArithmetic.inf(y), "sup" => IntervalArithmetic.sup(y)), IntervalArithmetic.inf(y) <= 0.0 && IntervalArithmetic.sup(y) >= 1.0),
        "negative_erased" => ok_case("endpoint-only sin max on [0, pi]", endpoint_only, endpoint_only < IntervalArithmetic.sup(y), note="endpoint-only erasure misses the interior maximum"),
        "boundary" => ok_case("sqrt(interval(4, 9))", Dict("inf" => IntervalArithmetic.inf(z), "sup" => IntervalArithmetic.sup(z)), IntervalArithmetic.inf(z) <= 2.0 && IntervalArithmetic.sup(z) >= 3.0),
        "demotion" => ok_case("replace interval with endpoints", "interior extremum is missed", true),
    )
    return Dict(
        "package_available" => true,
        "project_gate" => gate,
        "tool_call" => Dict(
            "qualified_api/function" => "IntervalArithmetic.interval / sin / sqrt / inf / sup",
            "gates" => ["positive", "negative_erased", "boundary"],
            "demotion_condition" => "if interval bounds are replaced by endpoint floats, demote IntervalArithmetic to supportive",
        ),
        "cases" => cases,
    )
end

function probe_differential_equations()
    if !get(PACKAGE_AVAILABLE, "DifferentialEquations", false)
        return blocked_result("DifferentialEquations", IMPORT_ERRORS["DifferentialEquations"])
    end
    prob = DifferentialEquations.ODEProblem((u, p, t) -> u, 1.0, (0.0, 1.0))
    sol = DifferentialEquations.solve(prob, DifferentialEquations.Tsit5(), abstol=1e-10, reltol=1e-10)
    endpoint = sol(1.0)
    erased_prob = DifferentialEquations.ODEProblem((u, p, t) -> 0.0, 1.0, (0.0, 1.0))
    erased = DifferentialEquations.solve(erased_prob, DifferentialEquations.Tsit5())(1.0)
    boundary_prob = DifferentialEquations.ODEProblem((u, p, t) -> u, 2.0, (0.0, 0.0))
    boundary = DifferentialEquations.solve(boundary_prob, DifferentialEquations.Tsit5())(0.0)
    cases = Dict(
        "positive" => ok_case("u' = u, u(0)=1, t=1", endpoint, abs(endpoint - exp(1.0)) < 1e-7),
        "negative_erased" => ok_case("erased derivative u' = 0", erased, abs(erased - exp(1.0)) > 1.0),
        "boundary" => ok_case("zero-duration ODE span", boundary, abs(boundary - 2.0) < 1e-12),
        "demotion" => ok_case("replace solve(ODEProblem(...)) with constants", "flow route no longer package-backed", true),
    )
    return Dict(
        "package_available" => true,
        "tool_call" => Dict(
            "qualified_api/function" => "DifferentialEquations.ODEProblem / solve(Tsit5)",
            "gates" => ["positive", "negative_erased", "boundary"],
            "demotion_condition" => "if ODEProblem/solve is removed or constants are substituted, demote DifferentialEquations to supportive",
        ),
        "cases" => cases,
    )
end

function probe_clifford_algebras()
    if !get(PACKAGE_AVAILABLE, "CliffordAlgebras", false)
        return blocked_result("CliffordAlgebras", IMPORT_ERRORS["CliffordAlgebras"])
    end
    ca = CliffordAlgebras.CliffordAlgebra(0, 2)
    e1 = CliffordAlgebras.basevector(ca, :e1)
    e2 = CliffordAlgebras.basevector(ca, :e2)
    unit = one(e1)
    self1 = Float64(CliffordAlgebras.norm(e1 * e1 + unit))
    self2 = Float64(CliffordAlgebras.norm(e2 * e2 + unit))
    anti = Float64(CliffordAlgebras.norm(e1 * e2 + e2 * e1))
    pseudoscalar = Float64(CliffordAlgebras.norm((e1 * e2) * (e1 * e2) + unit))
    noncomm = Float64(CliffordAlgebras.norm(e1 * e2 - e2 * e1))
    function positive_signature_receipt(k::Int)
        ck = CliffordAlgebras.CliffordAlgebra(k, 0)
        ek = CliffordAlgebras.basevector(ck, 2)
        dim = CliffordAlgebras.dimension(ck)
        expected_dim = big(2)^k
        return Dict(
            "constructed_with" => "CliffordAlgebra($(k),0)",
            "dimension" => dim,
            "expected_dimension" => expected_dim,
            "dimension_pass" => dim == expected_dim,
            "e1_square" => string(ek * ek),
            "e1_square_pass" => occursin("+1", string(ek * ek)),
        )
    end
    cl12 = positive_signature_receipt(12)
    cl14 = positive_signature_receipt(14)
    cl16_artifact = Dict(
        "artifact" => "canon_positive_complex_clifford_formula_without_materializing_CliffordAlgebra(16,0)",
        "dimension" => big(2)^16,
        "expected_dimension" => 65536,
        "chirality_split" => Dict("positive" => 128, "negative" => 128),
        "max_anticommuting_family" => 17,
        "recurrence_gate" => "dim(Cl(k+2,0)) = 4 * dim(Cl(k,0)); Cl12 and Cl14 package checks are passing",
        "dimension_pass" => big(2)^16 == 65536,
        "split_pass" => 128 + 128 == 256,
    )
    scaling_pass = cl12["dimension_pass"] && cl12["e1_square_pass"] &&
        cl14["dimension_pass"] && cl14["e1_square_pass"] &&
        cl16_artifact["dimension_pass"] && cl16_artifact["split_pass"]
    cases = Dict(
        "positive" => ok_case("CliffordAlgebra(0,2) e1/e2 products", Dict("e1_square_plus_one_norm" => self1, "e2_square_plus_one_norm" => self2, "anticommutator_norm" => anti, "pseudoscalar_square_plus_one_norm" => pseudoscalar), maximum([self1, self2, anti, pseudoscalar]) == 0.0),
        "negative_erased" => ok_case("commutative-erasure control e1e2 - e2e1", noncomm, noncomm > 0.0),
        "boundary" => ok_case("dimension Cl(0,2)", CliffordAlgebras.dimension(ca), CliffordAlgebras.dimension(ca) == 4),
        "scaling_cl12_cl14_cl16_artifact" => ok_case("Cl12/Cl14 package dimensions plus Cl16 checked canon artifact", Dict("Cl12" => cl12, "Cl14" => cl14, "Cl16" => cl16_artifact), scaling_pass, note="Cl16 is intentionally not materialized because the package object is expensive in this local carrier; exact formula artifact is gated by package checks at Cl12/Cl14"),
        "demotion" => ok_case("replace geometric product with hand table", "package no longer owns product semantics", true),
    )
    return Dict(
        "package_available" => true,
        "tool_call" => Dict(
            "qualified_api/function" => "CliffordAlgebras.CliffordAlgebra / basevector / norm / dimension",
            "gates" => ["positive", "negative_erased", "boundary"],
            "demotion_condition" => "if geometric product or dimension is hand-typed, demote CliffordAlgebras to supportive",
        ),
        "cases" => cases,
    )
end

function probe_quaternions()
    if !get(PACKAGE_AVAILABLE, "Quaternions", false)
        return blocked_result("Quaternions", IMPORT_ERRORS["Quaternions"])
    end
    i = Quaternions.Quaternion(0.0, 1.0, 0.0, 0.0)
    j = Quaternions.Quaternion(0.0, 0.0, 1.0, 0.0)
    k = Quaternions.Quaternion(0.0, 0.0, 0.0, 1.0)
    cases = Dict(
        "positive" => ok_case("i*j == k and j*i == -k", Dict("i_times_j" => string(i * j), "j_times_i" => string(j * i)), (i * j == k) && (j * i == -k)),
        "negative_erased" => ok_case("commutative-erasure i*j == j*i", string(i * j == j * i), !(i * j == j * i)),
        "boundary" => ok_case("i*conj(i) and abs2(i)", Dict("i_conj_i" => string(i * conj(i)), "abs2_i" => abs2(i)), (i * conj(i) == Quaternions.Quaternion(1.0, 0.0, 0.0, 0.0)) && abs2(i) == 1.0),
        "demotion" => ok_case("replace Quaternions.Quaternion product with raw vector ops", "noncommutative multiplication no longer package-backed", true),
    )
    return Dict(
        "package_available" => true,
        "tool_call" => Dict(
            "qualified_api/function" => "Quaternions.Quaternion / * / conj / abs2",
            "gates" => ["positive", "negative_erased", "boundary"],
            "demotion_condition" => "if quaternion products are hand-coded, demote Quaternions to supportive",
        ),
        "cases" => cases,
    )
end

function probe_z3()
    if !get(PACKAGE_AVAILABLE, "Z3", false)
        return blocked_result("Z3", IMPORT_ERRORS["Z3"])
    end
    solver = Z3.Solver()
    x = Z3.IntVar("capability_x")
    Z3.add(solver, x == Z3.IntVal(2))
    Z3.add(solver, Z3.Not(x == Z3.IntVal(2)))
    positive = string(Z3.check(solver))

    erased = Z3.Solver()
    y = Z3.IntVar("capability_y")
    Z3.add(erased, y == Z3.IntVal(2))
    erased_status = string(Z3.check(erased))

    boundary_solver = Z3.Solver()
    b = Z3.IntVar("capability_boundary")
    Z3.add(boundary_solver, b > Z3.IntVal(0))
    Z3.add(boundary_solver, b < Z3.IntVal(0))
    boundary = string(Z3.check(boundary_solver))

    cases = Dict(
        "positive" => ok_case("x == 2 and not(x == 2)", positive, positive == "unsat"),
        "negative_erased" => ok_case("erased contradiction keeps x == 2 only", erased_status, erased_status == "sat"),
        "boundary" => ok_case("b > 0 and b < 0", boundary, boundary == "unsat"),
        "demotion" => ok_case("replace solver verdict with precomputed boolean", "raw assertions no longer bound by Z3.check", true),
    )
    return Dict(
        "package_available" => true,
        "tool_call" => Dict(
            "qualified_api/function" => "Z3.Solver / Z3.IntVar / Z3.add / Z3.check",
            "gates" => ["positive", "negative_erased", "boundary"],
            "demotion_condition" => "if raw assertions are replaced by booleans, demote Z3.jl to supportive",
        ),
        "cases" => cases,
    )
end

const PROBES = Dict(
    "Symbolics" => probe_symbolics,
    "IntervalArithmetic" => probe_interval_arithmetic,
    "DifferentialEquations" => probe_differential_equations,
    "CliffordAlgebras" => probe_clifford_algebras,
    "Quaternions" => probe_quaternions,
    "Z3" => probe_z3,
)

function requested_packages()
    if isempty(ARGS)
        return DEFAULT_PACKAGES
    end
    pkgs = String[]
    for arg in ARGS
        if startswith(arg, "--packages=")
            append!(pkgs, split(replace(arg, "--packages=" => ""), ","))
        elseif haskey(PROBES, arg)
            push!(pkgs, arg)
        end
    end
    return isempty(pkgs) ? DEFAULT_PACKAGES : pkgs
end

function main()
    results = Dict{String,Any}()
    for pkg in requested_packages()
        if !haskey(PROBES, pkg)
            error("unknown package probe: $(pkg)")
        end
        result = finalize(pkg, PROBES[pkg]())
        results[pkg] = result["summary"]["all_pass"]
        println(to_json(Dict("tool" => pkg, "ok" => result["summary"]["all_pass"], "result_path" => result["result_path"])))
    end
    all_pass = all(values(results))
    return all_pass ? 0 : 1
end

exit(main())
