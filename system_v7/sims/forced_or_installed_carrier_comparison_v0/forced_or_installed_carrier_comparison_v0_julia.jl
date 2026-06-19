#!/usr/bin/env julia

using Dates
using JSON
using SHA
using Z3

const SIM_ID = "forced_or_installed_carrier_comparison_v0"
const HERE = @__DIR__
const RESULTS = joinpath(HERE, "results")
const PROBES = ["Z", "X", "Y"]

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

function first_carrier(spec)
    Dict(
        "a" => parse_frac(spec["first_carrier"]["a"]),
        "b" => parse_frac(spec["first_carrier"]["b"]),
        "c" => parse_frac(spec["first_carrier"]["c"]),
    )
end

function psd_margin(carrier)::Rational{Int64}
    a = carrier["a"]
    b = carrier["b"]
    c = carrier["c"]
    a * (1 - a) - b * b - c * c
end

function carrier_json(carrier)
    Dict(
        "a" => frac_text(carrier["a"]),
        "b" => frac_text(carrier["b"]),
        "c" => frac_text(carrier["c"]),
        "psd_margin" => frac_text(psd_margin(carrier)),
    )
end

function readout_frac(carrier, probe::String)::Rational{Int64}
    if probe == "Z"
        return 2 * carrier["a"] - 1
    elseif probe == "X"
        return 2 * carrier["b"]
    elseif probe == "Y"
        return 2 * carrier["c"]
    end
    error("unknown probe $(probe)")
end

function readouts_for(carrier)
    Dict(probe => frac_text(readout_frac(carrier, probe)) for probe in PROBES)
end

function measured_from_fixture(fixture)
    Dict(String(probe) => parse_frac(value) for (probe, value) in fixture["measured"])
end

function fixture_with_name(spec, name::String)
    fixture = deepcopy(spec["fixtures"][name])
    fixture["name"] = name
    fixture
end

function decision_from_status(status::String)::String
    if status == "sat"
        return "installed"
    elseif status == "unsat"
        return "forced"
    end
    return "unknown"
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
    length(args) == 1 && return args[1]
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_add(Z3.ref(ctx), length(args), map(Z3.as_ast, args)))
end

function zsub(ctx, args::Vector{Z3.Expr})
    length(args) == 1 && return args[1]
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_sub(Z3.ref(ctx), length(args), map(Z3.as_ast, args)))
end

function zmul(ctx, args::Vector{Z3.Expr})
    length(args) == 1 && return args[1]
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_mul(Z3.ref(ctx), length(args), map(Z3.as_ast, args)))
end

function zge(ctx, left::Z3.Expr, right::Z3.Expr)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_ge(Z3.ref(ctx), Z3.as_ast(left), Z3.as_ast(right)))
end

function zle(ctx, left::Z3.Expr, right::Z3.Expr)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_le(Z3.ref(ctx), Z3.as_ast(left), Z3.as_ast(right)))
end

function zneq(left::Z3.Expr, right::Z3.Expr)
    Z3.Not(left == right)
end

function zor(ctx, items::Vector{Z3.Expr})
    isempty(items) ? Z3.BoolVal(false, ctx) : Z3.Or(items)
end

function readout_expr(ctx, probe::String, a::Z3.Expr, b::Z3.Expr, c::Z3.Expr)
    two = real_val(ctx, 2 // 1)
    one = real_val(ctx, 1 // 1)
    if probe == "Z"
        return zsub(ctx, Z3.Expr[zmul(ctx, Z3.Expr[two, a]), one])
    elseif probe == "X"
        return zmul(ctx, Z3.Expr[two, b])
    elseif probe == "Y"
        return zmul(ctx, Z3.Expr[two, c])
    end
    error("unknown probe $(probe)")
end

function first_reproduces_measured(carrier, measured)::Bool
    all(readout_frac(carrier, probe) == value for (probe, value) in measured)
end

function decide(
    fixture,
    c1;
    include_reproduce::Bool=true,
    include_non_isomorphism::Bool=true,
    require_readout_mismatch::Bool=false,
    variable_prefix::String="julia_c2",
)
    include_reproduce && require_readout_mismatch && error("include_reproduce and require_readout_mismatch conflict")
    measured = measured_from_fixture(fixture)
    probes = [String(p) for p in fixture["probe_set"]]
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    a = real_var(ctx, "$(variable_prefix)_a")
    b = real_var(ctx, "$(variable_prefix)_b")
    c = real_var(ctx, "$(variable_prefix)_c")
    zero = real_val(ctx, 0 // 1)
    one = real_val(ctx, 1 // 1)

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

    if include_reproduce
        for probe in probes
            Z3.add(solver, readout_expr(ctx, probe, a, b, c) == real_val(ctx, measured[probe]))
        end
    end

    if require_readout_mismatch
        Z3.add(
            solver,
            zor(ctx, Z3.Expr[zneq(readout_expr(ctx, probe, a, b, c), real_val(ctx, measured[probe])) for probe in probes]),
        )
    end

    if include_non_isomorphism
        Z3.add(
            solver,
            zor(
                ctx,
                Z3.Expr[
                    zneq(a, real_val(ctx, c1["a"])),
                    zneq(b, real_val(ctx, c1["b"])),
                    zneq(c, real_val(ctx, c1["c"])),
                ],
            ),
        )
    end

    status = lowercase(string(Z3.check(solver)))
    witness = status == "sat" ? string(Z3.model(solver)) : nothing
    Dict{String,Any}(
        "solver" => "Z3.jl",
        "solver_logic" => "QF_NRA",
        "solver_status" => status,
        "verdict" => decision_from_status(status),
        "verdict_source" => "string(Z3.check(solver))",
        "fixture" => fixture["name"],
        "carrier_type" => "qubit_density_2x2_real_coordinates",
        "readout_definition" => Dict(
            "Z" => "Tr(sigma_z rho)=2a-1",
            "X" => "Tr(sigma_x rho)=2b",
            "Y" => "declared sigma_y-orientation readout=2c",
        ),
        "first_carrier" => carrier_json(c1),
        "first_carrier_readouts" => readouts_for(c1),
        "measured_probe_table" => Dict(probe => frac_text(value) for (probe, value) in measured),
        "probe_set" => probes,
        "second_carrier_variables" => Dict(
            "a" => "$(variable_prefix)_a:Real",
            "b" => "$(variable_prefix)_b:Real",
            "c" => "$(variable_prefix)_c:Real",
        ),
        "constraints" => Dict(
            "carrier_psd" => "0 <= a <= 1 and a*(1-a)-b^2-c^2 >= 0",
            "reproduce_table" => include_reproduce,
            "reproduce_binding" => include_reproduce ? "readout_k(C2) == measured_k for every active probe" : "omitted",
            "non_isomorphism" => include_non_isomorphism,
            "require_readout_mismatch" => require_readout_mismatch,
        ),
        "non_isomorphism_predicate" => "coordinate inequality: (a,b,c) for C2 differs from C1; no gauge quotient is applied in v0",
        "first_carrier_reproduces_measured" => first_reproduces_measured(c1, measured),
        "witness_model_string" => witness,
    )
end

function run_all_decisions(spec, c1)
    installed = fixture_with_name(spec, "installed_incomplete")
    forced = fixture_with_name(spec, "forced_complete")
    installed_scrambled = fixture_with_name(spec, "installed_incomplete_scrambled")
    forced_scrambled = fixture_with_name(spec, "forced_complete_scrambled")
    invalid_z = fixture_with_name(spec, "invalid_measured_z")
    Dict{String,Any}(
        "installed_incomplete" => Dict(
            "julia_z3" => decide(installed, c1; variable_prefix="julia_installed_c2"),
        ),
        "forced_complete" => Dict(
            "julia_z3" => decide(forced, c1; variable_prefix="julia_forced_c2"),
        ),
        "load_bearing_controls" => Dict(
            "installed_reproduce_off" => Dict(
                "julia_z3" => decide(
                    installed,
                    c1;
                    include_reproduce=false,
                    variable_prefix="julia_installed_no_reproduce_c2",
                ),
            ),
            "installed_reproduce_off_mismatch" => Dict(
                "julia_z3" => decide(
                    installed,
                    c1;
                    include_reproduce=false,
                    require_readout_mismatch=true,
                    variable_prefix="julia_installed_no_reproduce_mismatch_c2",
                ),
            ),
            "forced_reproduce_off" => Dict(
                "julia_z3" => decide(
                    forced,
                    c1;
                    include_reproduce=false,
                    variable_prefix="julia_forced_no_reproduce_c2",
                ),
            ),
            "forced_reproduce_off_mismatch" => Dict(
                "julia_z3" => decide(
                    forced,
                    c1;
                    include_reproduce=false,
                    require_readout_mismatch=true,
                    variable_prefix="julia_forced_no_reproduce_mismatch_c2",
                ),
            ),
            "installed_without_non_isomorphism" => Dict(
                "julia_z3" => decide(installed, c1; include_non_isomorphism=false, variable_prefix="julia_installed_no_noniso_c2"),
            ),
            "forced_without_non_isomorphism" => Dict(
                "julia_z3" => decide(forced, c1; include_non_isomorphism=false, variable_prefix="julia_forced_no_noniso_c2"),
            ),
            "installed_scrambled_values" => Dict(
                "julia_z3" => decide(installed_scrambled, c1; variable_prefix="julia_installed_scrambled_c2"),
            ),
            "forced_scrambled_values" => Dict(
                "julia_z3" => decide(forced_scrambled, c1; variable_prefix="julia_forced_scrambled_c2"),
            ),
            "invalid_measured_z_reproduce_on" => Dict(
                "julia_z3" => decide(invalid_z, c1; variable_prefix="julia_invalid_z_c2"),
            ),
            "invalid_measured_z_reproduce_off" => Dict(
                "julia_z3" => decide(
                    invalid_z,
                    c1;
                    include_reproduce=false,
                    variable_prefix="julia_invalid_z_no_reproduce_c2",
                ),
            ),
            "invalid_measured_z_reproduce_off_mismatch" => Dict(
                "julia_z3" => decide(
                    invalid_z,
                    c1;
                    include_reproduce=false,
                    require_readout_mismatch=true,
                    variable_prefix="julia_invalid_z_no_reproduce_mismatch_c2",
                ),
            ),
        ),
    )
end

function headline_checks(decisions)
    controls = decisions["load_bearing_controls"]
    installed_status = decisions["installed_incomplete"]["julia_z3"]["solver_status"]
    forced_status = decisions["forced_complete"]["julia_z3"]["solver_status"]
    unknowns = String[]
    for (name, section) in decisions
        if name == "load_bearing_controls"
            for (control_name, control) in section
                status = control["julia_z3"]["solver_status"]
                status == "unknown" && push!(unknowns, control_name)
            end
        else
            status = section["julia_z3"]["solver_status"]
            status == "unknown" && push!(unknowns, name)
        end
    end
    reproduce = Dict(
        "installed_on" => installed_status,
        "installed_off" => controls["installed_reproduce_off"]["julia_z3"]["solver_status"],
        "installed_off_mismatch" => controls["installed_reproduce_off_mismatch"]["julia_z3"]["solver_status"],
        "forced_on" => forced_status,
        "forced_off" => controls["forced_reproduce_off"]["julia_z3"]["solver_status"],
        "forced_off_mismatch" => controls["forced_reproduce_off_mismatch"]["julia_z3"]["solver_status"],
        "forced_status_differs" => forced_status != controls["forced_reproduce_off"]["julia_z3"]["solver_status"],
        "invalid_on" => controls["invalid_measured_z_reproduce_on"]["julia_z3"]["solver_status"],
        "invalid_off" => controls["invalid_measured_z_reproduce_off"]["julia_z3"]["solver_status"],
        "invalid_off_mismatch" => controls["invalid_measured_z_reproduce_off_mismatch"]["julia_z3"]["solver_status"],
        "invalid_status_differs" => controls["invalid_measured_z_reproduce_on"]["julia_z3"]["solver_status"] != controls["invalid_measured_z_reproduce_off"]["julia_z3"]["solver_status"],
    )
    Dict(
        "installed_fixture_sat" => installed_status == "sat",
        "forced_fixture_unsat" => forced_status == "unsat",
        "no_unknown_headline" => isempty(unknowns),
        "unknowns" => unknowns,
        "noniso_off_is_sat" =>
            controls["installed_without_non_isomorphism"]["julia_z3"]["solver_status"] == "sat" &&
            controls["forced_without_non_isomorphism"]["julia_z3"]["solver_status"] == "sat",
        "reproduce_on_off_differs" => reproduce["forced_status_differs"] && reproduce["invalid_status_differs"],
        "scramble_changes_forced_verdict" => controls["forced_scrambled_values"]["julia_z3"]["solver_status"] == "sat",
        "scramble_keeps_installed_sat_with_different_table" => controls["installed_scrambled_values"]["julia_z3"]["solver_status"] == "sat",
        "reproduce_on_off" => Dict("julia_z3" => reproduce),
    )
end

function main()
    mkpath(RESULTS)
    spec = JSON.parsefile(joinpath(HERE, "spec.json"))
    c1 = first_carrier(spec)
    fixture_results = run_all_decisions(spec, c1)
    checks = headline_checks(fixture_results)
    all_pass =
        checks["installed_fixture_sat"] &&
        checks["forced_fixture_unsat"] &&
        checks["no_unknown_headline"] &&
        checks["noniso_off_is_sat"] &&
        checks["reproduce_on_off_differs"] &&
        checks["scramble_changes_forced_verdict"] &&
        checks["scramble_keeps_installed_sat_with_different_table"]

    result = Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia_z3jl_qf_nra",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => false,
        "written_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "source_sha256" => sha256_file(@__FILE__),
        "spec_sha256" => sha256_file(joinpath(HERE, "spec.json")),
        "julia_project" => Base.active_project(),
        "carrier_type" => spec["carrier_type"],
        "readout_definition" => spec["readout_definition"],
        "first_carrier" => carrier_json(c1),
        "first_carrier_readouts" => readouts_for(c1),
        "fixture_results" => fixture_results,
        "headline_checks" => checks,
        "same_decide_code" => "decide in forced_or_installed_carrier_comparison_v0_julia.jl with local real-sort wrappers",
        "non_isomorphism_predicate" => spec["non_isomorphism_predicate"],
        "TOOL_MANIFEST" => Dict(
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive spec/result JSON handling"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Z3.jl QF_NRA second-density-carrier existence search"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("JSON" => "supportive", "Z3" => "load_bearing"),
        "packages_used" => ["JSON", "SHA", "Dates", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "package_observables" => Dict(
            "Z3" => "Z3.jl QF_NRA installed SAT and forced UNSAT checks plus reproduce/non-isomorphism/scramble controls",
            "JSON" => "spec/result JSON handling only",
        ),
        "tool_calls" => [
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.Libz3 real-sort constructors/Z3.check/Z3.model",
                "input_object" => "free C2 density coordinates a,b,c with PSD, reproduce, and non-isomorphism constraints",
                "output_object" => "SAT installed model and UNSAT complete-table coordinate-uniqueness result",
                "positive_case" => "Z/X incomplete table admits a coordinate-distinct C2",
                "negative/erased_control" => "Z/X/Y complete table rejects coordinate-distinct C2; reproduce-off mismatch controls are SAT",
                "boundary_case" => "scrambled complete table is SAT, so forced is value-coupled",
                "demotion_condition" => "demote if Z3.check is bypassed or C2 variables are not free",
                "gates" => ["proof", "all_pass"],
            ),
        ],
        "claim_path_tools" => ["Z3"],
        "all_pass" => all_pass,
        "criteria_checked" => [
            "installed_incomplete Z3.jl SAT",
            "forced_complete Z3.jl UNSAT",
            "no headline solver returned unknown",
            "reproduce ON/OFF controls differ for forced and invalid measured tables",
            "scrambled complete table flips to SAT",
        ],
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
                "installed" => Dict("julia_z3" => fixture_results["installed_incomplete"]["julia_z3"]["verdict"]),
                "forced" => Dict("julia_z3" => fixture_results["forced_complete"]["julia_z3"]["verdict"]),
                "reproduce_on_off" => checks["reproduce_on_off"],
                "julia_installed_C2" => fixture_results["installed_incomplete"]["julia_z3"]["witness_model_string"],
            ),
            2,
        ),
    )
    result["all_pass"] || exit(1)
end

main()
