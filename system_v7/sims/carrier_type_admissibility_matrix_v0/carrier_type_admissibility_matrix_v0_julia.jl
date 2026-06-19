#!/usr/bin/env julia

using Dates
using JSON
using SHA
using Z3

const SIM_ID = "carrier_type_admissibility_matrix_v0"
const HERE = @__DIR__
const RESULTS = joinpath(HERE, "results")
const CARRIER_TYPES = ["quotient", "classical_noncontextual", "real_rebit", "complex_rho"]
const ASSIGNMENTS = [(z, x, y) for z in (0, 1) for x in (0, 1) for y in (0, 1)]

function sha256_file(path::AbstractString)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function parse_frac(value)::Rational{Int64}
    s = strip(string(value))
    if occursin("/", s)
        parts = split(s, "/")
        return parse(Int64, parts[1]) // parse(Int64, parts[2])
    end
    return parse(Int64, s) // 1
end

function frac_text(value::Rational)::String
    denominator(value) == 1 ? string(numerator(value)) : "$(numerator(value))/$(denominator(value))"
end

function measured_from_fixture(fixture)
    Dict(String(probe) => parse_frac(value) for (probe, value) in fixture["measured"])
end

function fixture_with_name(spec, group::String, name::String)
    fixture = deepcopy(spec[group][name])
    fixture["name"] = name
    fixture["group"] = group
    fixture
end

function ordered_names(spec, group::String)
    order_key = endswith(group, "s") ? "$(group[1:end-1])_order" : "$(group)_order"
    haskey(spec, order_key) ? [String(name) for name in spec[order_key]] : sort([String(name) for name in keys(spec[group])])
end

function real_sort(ctx)
    Z3.Sort(ctx, Z3.Libz3.Z3_mk_real_sort(Z3.ref(ctx)))
end

function real_var(ctx, name::String)
    Z3.Const(name, real_sort(ctx))
end

function real_val(ctx, value::Rational)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_real_int64(Z3.ref(ctx), Int64(numerator(value)), Int64(denominator(value))))
end

function zadd(ctx, args::Vector{Z3.Expr})
    isempty(args) && return real_val(ctx, 0 // 1)
    length(args) == 1 && return args[1]
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_add(Z3.ref(ctx), length(args), map(Z3.as_ast, args)))
end

function zsub(ctx, args::Vector{Z3.Expr})
    length(args) == 1 && return args[1]
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_sub(Z3.ref(ctx), length(args), map(Z3.as_ast, args)))
end

function zmul(ctx, args::Vector{Z3.Expr})
    isempty(args) && return real_val(ctx, 1 // 1)
    length(args) == 1 && return args[1]
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_mul(Z3.ref(ctx), length(args), map(Z3.as_ast, args)))
end

function zge(ctx, left::Z3.Expr, right::Z3.Expr)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_ge(Z3.ref(ctx), Z3.as_ast(left), Z3.as_ast(right)))
end

function zle(ctx, left::Z3.Expr, right::Z3.Expr)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_le(Z3.ref(ctx), Z3.as_ast(left), Z3.as_ast(right)))
end

function classical_readout(ctx, probe::String, weights::Dict{Tuple{Int64,Int64,Int64},Z3.Expr})
    if probe == "Z"
        return zadd(ctx, Z3.Expr[w for ((z, _x, _y), w) in weights if z == 1])
    elseif probe == "X"
        return zadd(ctx, Z3.Expr[w for ((_z, x, _y), w) in weights if x == 1])
    elseif probe == "Y"
        return zadd(ctx, Z3.Expr[w for ((_z, _x, y), w) in weights if y == 1])
    elseif probe == "ZX" || probe == "XZ"
        return zadd(ctx, Z3.Expr[w for ((z, x, _y), w) in weights if z == 1 && x == 1])
    end
    error("unknown probe $(probe)")
end

function real_readout(ctx, probe::String, a::Z3.Expr, b::Z3.Expr)
    half = real_val(ctx, 1 // 2)
    quarter = real_val(ctx, 1 // 4)
    if probe == "Z"
        return a
    elseif probe == "X"
        return zadd(ctx, Z3.Expr[half, b])
    elseif probe == "Y"
        return half
    elseif probe == "ZX"
        return zmul(ctx, Z3.Expr[half, a])
    elseif probe == "XZ"
        return zadd(ctx, Z3.Expr[quarter, zmul(ctx, Z3.Expr[half, b])])
    end
    error("unknown probe $(probe)")
end

function complex_readout(ctx, probe::String, a::Z3.Expr, b::Z3.Expr, c::Z3.Expr)
    if probe == "Y"
        return zadd(ctx, Z3.Expr[real_val(ctx, 1 // 2), c])
    end
    real_readout(ctx, probe, a, b)
end

function status_admission(status::String)::String
    status == "sat" && return "admitted"
    status == "unsat" && return "excluded"
    "unknown"
end

function sorted_var_decls(vars::Dict{String,Z3.Expr})
    Dict(name => "$(name):Real" for name in sort(collect(keys(vars))))
end

function witness_model_string(status::String, solver)
    status == "sat" ? string(Z3.model(solver)) : nothing
end

function decide(fixture, carrier_type::String; include_reproduce::Bool=true)
    measured = measured_from_fixture(fixture)
    probes = [String(p) for p in fixture["probes"]]
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    prefix = "julia_$(fixture["name"])_$(carrier_type)"
    readouts = Dict{String,Z3.Expr}()
    variables = Dict{String,Z3.Expr}()
    validity = String[]
    zero = real_val(ctx, 0 // 1)
    one = real_val(ctx, 1 // 1)

    if carrier_type == "quotient"
        for probe in probes
            var = real_var(ctx, "$(prefix)_$(probe)")
            variables["q_$(probe)"] = var
            Z3.add(solver, zge(ctx, var, zero))
            Z3.add(solver, zle(ctx, var, one))
            readouts[probe] = var
        end
        push!(validity, "0 <= q_probe <= 1 for each measured probe")
    elseif carrier_type == "classical_noncontextual"
        weights = Dict{Tuple{Int64,Int64,Int64},Z3.Expr}()
        for assignment in ASSIGNMENTS
            z, x, y = assignment
            weight = real_var(ctx, "$(prefix)_w_$(z)$(x)$(y)")
            weights[assignment] = weight
            variables["w_z$(z)x$(x)y$(y)"] = weight
            Z3.add(solver, zge(ctx, weight, zero))
        end
        Z3.add(solver, zadd(ctx, collect(values(weights))) == one)
        for probe in probes
            readouts[probe] = classical_readout(ctx, probe, weights)
        end
        push!(validity, "weights over deterministic Z/X/Y assignments are nonnegative and sum to 1")
        push!(validity, "ZX and XZ are the same non-disturbing joint event")
    elseif carrier_type == "real_rebit"
        a = real_var(ctx, "$(prefix)_a")
        b = real_var(ctx, "$(prefix)_b")
        variables["a"] = a
        variables["b"] = b
        Z3.add(solver, zge(ctx, a, zero))
        Z3.add(solver, zle(ctx, a, one))
        Z3.add(
            solver,
            zge(
                ctx,
                zsub(ctx, Z3.Expr[zmul(ctx, Z3.Expr[a, zsub(ctx, Z3.Expr[one, a])]), zmul(ctx, Z3.Expr[b, b])]),
                zero,
            ),
        )
        for probe in probes
            readouts[probe] = real_readout(ctx, probe, a, b)
        end
        push!(validity, "rho_R=[[a,b],[b,1-a]], 0 <= a <= 1, a*(1-a)-b^2 >= 0")
    elseif carrier_type == "complex_rho"
        a = real_var(ctx, "$(prefix)_a")
        b = real_var(ctx, "$(prefix)_b")
        c = real_var(ctx, "$(prefix)_c")
        variables["a"] = a
        variables["b"] = b
        variables["c"] = c
        Z3.add(solver, zge(ctx, a, zero))
        Z3.add(solver, zle(ctx, a, one))
        Z3.add(
            solver,
            zge(
                ctx,
                zsub(
                    ctx,
                    Z3.Expr[
                        zmul(ctx, Z3.Expr[a, zsub(ctx, Z3.Expr[one, a])]),
                        zadd(ctx, Z3.Expr[zmul(ctx, Z3.Expr[b, b]), zmul(ctx, Z3.Expr[c, c])]),
                    ],
                ),
                zero,
            ),
        )
        for probe in probes
            readouts[probe] = complex_readout(ctx, probe, a, b, c)
        end
        push!(validity, "rho=[[a,b-i*c],[b+i*c,1-a]], 0 <= a <= 1, a*(1-a)-b^2-c^2 >= 0")
    else
        error("unknown carrier type $(carrier_type)")
    end

    if include_reproduce
        for probe in probes
            Z3.add(solver, readouts[probe] == real_val(ctx, measured[probe]))
        end
    end

    status = lowercase(string(Z3.check(solver)))
    Dict{String,Any}(
        "solver" => "Z3.jl",
        "solver_logic" => "QF_NRA",
        "solver_status" => status,
        "carrier_type" => carrier_type,
        "fixture" => fixture["name"],
        "admission" => status_admission(status),
        "verdict_source" => "string(Z3.check(solver))",
        "probes" => probes,
        "measured" => Dict(probe => frac_text(value) for (probe, value) in measured),
        "include_reproduce" => include_reproduce,
        "readout_binding" => include_reproduce ? "readout_T(C, probe) == measured_probe for every listed probe" : "omitted",
        "validity_constraints" => validity,
        "free_variables" => sorted_var_decls(variables),
        "witness_model_string" => witness_model_string(status, solver),
    )
end

function solve_fixture(fixture; include_reproduce::Bool=true)
    by_type = Dict{String,Any}()
    for carrier_type in CARRIER_TYPES
        by_type[carrier_type] = decide(fixture, carrier_type; include_reproduce=include_reproduce)
    end
    allowed = [carrier_type for carrier_type in CARRIER_TYPES if by_type[carrier_type]["solver_status"] == "sat"]
    excluded = [carrier_type for carrier_type in CARRIER_TYPES if by_type[carrier_type]["solver_status"] == "unsat"]
    unknown = [carrier_type for carrier_type in CARRIER_TYPES if !(by_type[carrier_type]["solver_status"] in ["sat", "unsat"])]
    Dict{String,Any}(
        "solver" => "julia_z3",
        "fixture" => fixture["name"],
        "include_reproduce" => include_reproduce,
        "allowed_set" => allowed,
        "excluded_set" => excluded,
        "unknown_set" => unknown,
        "fixture_verdict" => length(allowed) >= 2 ? "installed" : length(allowed) == 1 ? "single_allowed_by_panel" : "none_allowed",
        "by_type" => by_type,
    )
end

function solve_group(spec, group::String; include_reproduce::Bool=true)
    Dict{String,Any}(
        name => solve_fixture(fixture_with_name(spec, group, name); include_reproduce=include_reproduce)
        for name in ordered_names(spec, group)
    )
end

function first_reproduce_diff_for_type(spec, headline, controls, carrier_type::String)
    for (group_name, on_group, off_group) in [
        ("headline_fixtures", headline["julia_z3"], headline["julia_z3_reproduce_off"]),
        ("load_bearing_controls", controls["julia_z3"], controls["julia_z3_reproduce_off"]),
    ]
        for fixture_name in ordered_names(spec, group_name)
            on_status = on_group[fixture_name]["by_type"][carrier_type]["solver_status"]
            off_status = off_group[fixture_name]["by_type"][carrier_type]["solver_status"]
            if on_status != off_status
                return Dict(
                    "fixture" => fixture_name,
                    "fixture_group" => group_name,
                    "on" => on_status,
                    "off" => off_status,
                    "differs" => true,
                )
            end
        end
    end
    Dict("fixture" => nothing, "on" => nothing, "off" => nothing, "differs" => false)
end

function set_vectors_vary(rows, key::String)::Bool
    seen = Set{String}()
    for row in values(rows)
        push!(seen, join(row[key], ","))
    end
    length(seen) > 1
end

function summarize_checks(spec, headline, controls)
    no_unknown = true
    for section in [headline["julia_z3"], controls["julia_z3"]]
        for row in values(section)
            !isempty(row["unknown_set"]) && (no_unknown = false)
        end
    end
    reproduce_by_type = Dict(carrier_type => first_reproduce_diff_for_type(spec, headline, controls, carrier_type) for carrier_type in CARRIER_TYPES)
    reproduce_all = all(reproduce_by_type[carrier_type]["differs"] for carrier_type in CARRIER_TYPES)
    original = spec["scramble_pair"]["original"]
    scrambled = spec["scramble_pair"]["scrambled"]
    scramble_changes = headline["julia_z3"][original]["allowed_set"] != headline["julia_z3"][scrambled]["allowed_set"]
    expected_ok = Dict{String,Bool}()
    for (name, fixture) in spec["headline_fixtures"]
        row = headline["julia_z3"][name]
        allowed = Set(row["allowed_set"])
        excluded = Set(row["excluded_set"])
        allowed_contains = Set(get(fixture, "expected_allowed_contains", []))
        excluded_contains = Set(get(fixture, "expected_excluded_contains", get(fixture, "expected_excluded", [])))
        expected_ok[name] = issubset(allowed_contains, allowed) && issubset(excluded_contains, excluded)
    end
    multiplicity = length(headline["julia_z3"]["marginal_multiplicity"]["allowed_set"]) >= 2
    exclusion = any(!isempty(row["excluded_set"]) && !isempty(row["allowed_set"]) for row in values(headline["julia_z3"]))
    allowed_varies = set_vectors_vary(headline["julia_z3"], "allowed_set")
    excluded_varies = set_vectors_vary(headline["julia_z3"], "excluded_set")
    all_pass =
        no_unknown &&
        multiplicity &&
        exclusion &&
        reproduce_all &&
        scramble_changes &&
        allowed_varies &&
        excluded_varies &&
        all(values(expected_ok))
    Dict{String,Any}(
        "no_unknown_headline_or_controls" => no_unknown,
        "multiplicity_fixture_admits_at_least_two_types" => multiplicity,
        "has_genuine_exclusion_fixture" => exclusion,
        "reproduce_on_off_by_type" => reproduce_by_type,
        "reproduce_on_off_all_types_differ" => reproduce_all,
        "scramble_changes_allowed_set" => scramble_changes,
        "allowed_set_varies_across_matrix" => allowed_varies,
        "excluded_set_varies_across_matrix" => excluded_varies,
        "expected_fixture_sets_present" => expected_ok,
        "all_pass" => all_pass,
    )
end

function subset_fixture(fixture, name::String, probes::Vector{String})
    Dict{String,Any}(
        "name" => name,
        "group" => "order_gap_clean_isolation",
        "role" => "ISOLATION_CHECK",
        "probes" => probes,
        "measured" => Dict(probe => fixture["measured"][probe] for probe in probes),
    )
end

function order_gap_clean_isolation(spec)
    fixture = fixture_with_name(spec, "headline_fixtures", "order_gap_clean")
    classical_base = decide(subset_fixture(fixture, "order_gap_clean_ZX_marginals", ["Z", "X"]), "classical_noncontextual")
    classical_zx = decide(subset_fixture(fixture, "order_gap_clean_ZX_branch", ["Z", "X", "ZX"]), "classical_noncontextual")
    classical_xz = decide(subset_fixture(fixture, "order_gap_clean_XZ_branch", ["Z", "X", "XZ"]), "classical_noncontextual")
    classical_joint = decide(fixture, "classical_noncontextual")
    complex_joint = decide(fixture, "complex_rho")
    passed =
        classical_base["solver_status"] == "sat" &&
        classical_zx["solver_status"] == "sat" &&
        classical_xz["solver_status"] == "sat" &&
        classical_joint["solver_status"] == "unsat" &&
        complex_joint["solver_status"] == "sat"
    Dict{String,Any}(
        "solver" => "julia_z3",
        "fixture" => "order_gap_clean",
        "expected_clean_values" => Dict(
            "Z" => "1/2",
            "X" => "3/4",
            "ZX" => "1/4",
            "XZ" => "3/8",
            "complex_rho_witness" => Dict("a" => "1/2", "b" => "1/4"),
        ),
        "classical_noncontextual" => Dict(
            "marginals_Z_X" => classical_base["solver_status"],
            "branch_Z_X_ZX" => classical_zx["solver_status"],
            "branch_Z_X_XZ" => classical_xz["solver_status"],
            "joint_Z_X_ZX_XZ" => classical_joint["solver_status"],
            "exclusion_mechanism" => "one non-disturbing classical joint J cannot equal both ZX=1/4 and XZ=3/8",
        ),
        "complex_rho" => Dict(
            "joint_Z_X_ZX_XZ" => complex_joint["solver_status"],
            "witness_model_string" => complex_joint["witness_model_string"],
        ),
        "passed" => passed,
    )
end

function main()
    mkpath(RESULTS)
    spec = JSON.parsefile(joinpath(HERE, "spec.json"))
    headline = Dict{String,Any}(
        "julia_z3" => solve_group(spec, "headline_fixtures"),
        "julia_z3_reproduce_off" => solve_group(spec, "headline_fixtures"; include_reproduce=false),
    )
    controls = Dict{String,Any}(
        "julia_z3" => solve_group(spec, "load_bearing_controls"),
        "julia_z3_reproduce_off" => solve_group(spec, "load_bearing_controls"; include_reproduce=false),
    )
    checks = summarize_checks(spec, headline, controls)
    isolation = order_gap_clean_isolation(spec)
    checks["order_gap_clean_isolation_pass"] = isolation["passed"]
    result = Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia_z3",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => false,
        "written_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "source_sha256" => sha256_file(@__FILE__),
        "spec_sha256" => sha256_file(joinpath(HERE, "spec.json")),
        "julia_project" => Base.active_project(),
        "carrier_types" => CARRIER_TYPES,
        "carrier_type_non_isomorphism" => spec["carrier_type_non_isomorphism"],
        "readout_definitions" => spec["readout_definitions"],
        "headline_matrix" => headline,
        "load_bearing_controls" => controls,
        "headline_checks" => checks,
        "multiplicity_witness" => Dict(
            "fixture" => spec["multiplicity_witness_fixture"],
            "classical_noncontextual" => headline["julia_z3"][spec["multiplicity_witness_fixture"]]["by_type"]["classical_noncontextual"]["witness_model_string"],
            "complex_rho" => headline["julia_z3"][spec["multiplicity_witness_fixture"]]["by_type"]["complex_rho"]["witness_model_string"],
        ),
        "TOOL_MANIFEST" => Dict(
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive read/write of spec and receipt JSON"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Z3.jl existence search over free carrier variables for each type and fixture"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("JSON" => "supportive", "Z3" => "load_bearing"),
        "packages_used" => ["JSON", "SHA", "Dates", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "package_observables" => Dict(
            "Z3" => "SAT/UNSAT allowed-set matrix and reproduce controls over free carrier variables",
            "JSON" => "spec/result JSON handling only",
        ),
        "tool_calls" => [
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.Const/Z3.add/Z3.check/Z3.model",
                "input_object" => "per-type free variables and readout equalities for each finite probe-table fixture",
                "output_object" => "allowed/excluded carrier-type matrix",
                "positive_case" => "marginal_multiplicity admits multiple non-isomorphic carrier categories",
                "negative/erased_control" => "order_gap_clean excludes classical_noncontextual through the non-disturbing joint; invalid_probability flips reproduce ON/OFF",
                "boundary_case" => "scrambled_order_gap changes the allowed set",
                "demotion_condition" => "demote if Z3.jl returns unknown or reproduce ON/OFF does not differ for every carrier type",
                "gates" => ["proof", "all_pass"],
            ),
        ],
        "claim_path_tools" => ["Z3"],
        "order_gap_clean_isolation" => isolation,
        "all_pass" => checks["all_pass"] && isolation["passed"],
        "claim_ceiling" => spec["claim_ceiling"],
        "surviving_alternatives" => spec["surviving_alternatives"],
    )
    out_path = joinpath(RESULTS, "$(SIM_ID)_julia_results.json")
    open(out_path, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(
        JSON.json(
            Dict(
                "ok" => result["all_pass"],
                "result_path" => out_path,
                "headline_allowed_sets" => Dict(name => row["allowed_set"] for (name, row) in headline["julia_z3"]),
                "headline_excluded_sets" => Dict(name => row["excluded_set"] for (name, row) in headline["julia_z3"]),
                "reproduce_on_off_by_type" => checks["reproduce_on_off_by_type"],
                "order_gap_clean_isolation" => isolation,
                "scramble_changes_allowed_set" => checks["scramble_changes_allowed_set"],
            ),
            2,
        ),
    )
    result["all_pass"] || exit(1)
end

main()
