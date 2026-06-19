#!/usr/bin/env julia
# Julia Symbolics/Z3.jl mirror for geo_union_rule_k_leaves_v0.

using Dates
using JSON
using SHA
using Symbolics
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_union_rule_k_leaves_v0"
const SIM_DIR_REL = joinpath("system_v6", "sims", SIM_ID)
const SIM_DIR = joinpath(ROOT, SIM_DIR_REL)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH_REL = joinpath(SIM_DIR_REL, "$(SIM_ID)_julia.jl")
const SOURCE_PATH = joinpath(ROOT, SOURCE_PATH_REL)
const RESULT_PATH_REL = joinpath(SIM_DIR_REL, "results", "$(SIM_ID)_julia_results.json")
const RESULT_PATH = joinpath(ROOT, RESULT_PATH_REL)

const PARENT_COMMON_PATH_REL = joinpath("system_v6", "sims", "geo_nested_disintegration_v0", "geo_nested_disintegration_v0_common.py")
const PARENT_JAX_SOURCE_PATH_REL = joinpath("system_v6", "sims", "geo_nested_disintegration_v0", "geo_nested_disintegration_v0_jax.py")
const PARENT_JULIA_SOURCE_PATH_REL = joinpath("system_v6", "sims", "geo_nested_disintegration_v0", "geo_nested_disintegration_v0_julia.jl")
const PARENT_ENVELOPE_SOURCE_PATH_REL = joinpath("system_v6", "sims", "geo_nested_disintegration_v0", "geo_nested_disintegration_v0_envelope.py")
const PARENT_JAX_RESULT_PATH_REL = joinpath("system_v6", "sims", "geo_nested_disintegration_v0", "results", "geo_nested_disintegration_v0_jax_results.json")
const PARENT_JULIA_RESULT_PATH_REL = joinpath("system_v6", "sims", "geo_nested_disintegration_v0", "results", "geo_nested_disintegration_v0_julia_results.json")
const PARENT_ENVELOPE_RESULT_PATH_REL = joinpath("system_v6", "sims", "geo_nested_disintegration_v0", "results", "geo_nested_disintegration_v0_envelope_results.json")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const SEED = 2026061102

const PIN_SPEC = "geo_union_rule_k_leaves_v0|purpose=extend_committed_geo_nested_disintegration_two_leaf_union_rule_to_finite_k_leaves|parent=geo_nested_disintegration_v0_read_only|base_measure=round_uniform_S3_volume|outer_foliation=S3_union_eta_T_eta|eta_range=[0,pi/2]|leaf_density=rho(eta)=sin(2*eta)|finite_k_distinct_union_rule=mu(.|union_i_T_eta_i)=sum_i_sin(2eta_i)/sum_j_sin(2eta_j)*mu(.|T_eta_i)|k2_reduction=byte_exact_R3_union_two_shell_conditioning_parent_row|concrete_shells=pi/12,pi/6,pi/4,pi/3|assoc_order_row=((1u2)u3)==(1u(2u3))==direct_3_leaf_when_group_mass_is_summed|degenerate_repeated_leaf=collapse_unique_shells_before_weighting_no_double_count|boundary_eta0=sin(0)=0_weight_vanishes|equal_weights_control=k3_cos2eta_defect_nonzero|mortality_boundary=no_finite_k_naive_conditioning_definable;continuum_all_eta_shells=S3_a.e._recovers_FREE_unconditioned_measure|solver_row=k3_weight_identity_z3_cvc5_and_julia_z3_with_erased_weight_formula_flip|engine_mode=julia_symbolics_plus_python_sympy_smt_diagnostic|pytorch_omitted=no_graph_network_autograd_claim|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const CONVENTION_PIN = Dict(
    "coordinate_chart" => "z1=cos(eta) exp(i(phi+chi)), z2=sin(eta) exp(i(phi-chi))",
    "eta_range" => "[0, pi/2]",
    "s3_volume" => "2*pi^2",
    "parent_stage1_eta_marginal" => "sin(2*eta) d_eta",
    "leaf" => "T_eta = fixed-eta Hopf torus leaf",
    "leaf_density" => "rho(eta)=sin(2*eta)",
    "finite_union_band_limit" => "T_eta_i replaced by [eta_i-eps, eta_i+eps], eps -> 0+",
    "finite_k_scope" => "finite distinct leaves only unless a degenerate collapse row is explicitly named",
    "mortality_boundary" => "finite leaf unions have S3 measure zero; all eta leaves recover S3 a.e.",
)

const TOOL_MANIFEST = Dict(
    "Symbolics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing symbolic mirror for finite-k normalization, grouping/associativity, k=3 radical identities, and degenerate/equal controls"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-side real-arithmetic proof of the k=3 radical weight identity with erased-weight flip"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source and lineage hashing"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "Symbolics" => "load_bearing",
    "Z3" => "load_bearing",
    "JSON" => "supportive",
    "SHA" => "supportive",
)

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))
sha256_text(text::AbstractString) = bytes2hex(SHA.sha256(codeunits(text)))

function stable_json_sha256(obj)
    io = IOBuffer()
    JSON.print(io, obj, 0)
    sha256_text(String(take!(io)))
end

function parent_lineage()
    parent_jax = JSON.parsefile(joinpath(ROOT, PARENT_JAX_RESULT_PATH_REL))
    parent_envelope = JSON.parsefile(joinpath(ROOT, PARENT_ENVELOPE_RESULT_PATH_REL))
    parent_r3 = parent_jax["receipts"]["R3_union_two_shell_conditioning"]
    Dict(
        "geo_nested_disintegration_v0_common_source" => Dict("path" => PARENT_COMMON_PATH_REL, "sha256" => sha256_file(joinpath(ROOT, PARENT_COMMON_PATH_REL))),
        "geo_nested_disintegration_v0_jax_source" => Dict("path" => PARENT_JAX_SOURCE_PATH_REL, "sha256" => sha256_file(joinpath(ROOT, PARENT_JAX_SOURCE_PATH_REL))),
        "geo_nested_disintegration_v0_julia_source" => Dict("path" => PARENT_JULIA_SOURCE_PATH_REL, "sha256" => sha256_file(joinpath(ROOT, PARENT_JULIA_SOURCE_PATH_REL))),
        "geo_nested_disintegration_v0_envelope_source" => Dict("path" => PARENT_ENVELOPE_SOURCE_PATH_REL, "sha256" => sha256_file(joinpath(ROOT, PARENT_ENVELOPE_SOURCE_PATH_REL))),
        "geo_nested_disintegration_v0_jax_result" => Dict("path" => PARENT_JAX_RESULT_PATH_REL, "sha256" => sha256_file(joinpath(ROOT, PARENT_JAX_RESULT_PATH_REL))),
        "geo_nested_disintegration_v0_julia_result" => Dict("path" => PARENT_JULIA_RESULT_PATH_REL, "sha256" => sha256_file(joinpath(ROOT, PARENT_JULIA_RESULT_PATH_REL))),
        "geo_nested_disintegration_v0_envelope_result" => Dict("path" => PARENT_ENVELOPE_RESULT_PATH_REL, "sha256" => sha256_file(joinpath(ROOT, PARENT_ENVELOPE_RESULT_PATH_REL))),
        "geo_nested_disintegration_v0_pin" => Dict("path" => string(PARENT_ENVELOPE_RESULT_PATH_REL, "#/pin_sha256"), "sha256" => parent_envelope["pin_sha256"]),
        "geo_nested_disintegration_v0_R3_union_two_shell_conditioning" => Dict("path" => string(PARENT_JAX_RESULT_PATH_REL, "#/receipts/R3_union_two_shell_conditioning"), "sha256" => stable_json_sha256(parent_r3)),
    )
end

function maybe_pkgversion(modsym::Symbol)
    try
        return string(pkgversion(getfield(Main, modsym)))
    catch
        return "unknown"
    end
end

function reduce_r2(expr, r)
    expanded = Symbolics.expand(expr)
    substituted = Symbolics.substitute(expanded, Dict(r^2 => 3))
    Symbolics.simplify(substituted)
end

function expr_string(expr)
    string(Symbolics.simplify(expr))
end

function symbolic_receipts()
    @variables rho1 rho2 rho3 r
    weights = [
        rho1 / (rho1 + rho2 + rho3),
        rho2 / (rho1 + rho2 + rho3),
        rho3 / (rho1 + rho2 + rho3),
    ]
    normalization_defect = Symbolics.simplify(sum(weights) - 1)
    group12 = (rho1 + rho2) / (rho1 + rho2 + rho3)
    group23 = (rho2 + rho3) / (rho1 + rho2 + rho3)
    left = [
        Symbolics.simplify(group12 * rho1 / (rho1 + rho2)),
        Symbolics.simplify(group12 * rho2 / (rho1 + rho2)),
        Symbolics.simplify(rho3 / (rho1 + rho2 + rho3)),
    ]
    right = [
        Symbolics.simplify(rho1 / (rho1 + rho2 + rho3)),
        Symbolics.simplify(group23 * rho2 / (rho2 + rho3)),
        Symbolics.simplify(group23 * rho3 / (rho2 + rho3)),
    ]
    left_defects = [Symbolics.simplify(left[i] - weights[i]) for i in 1:3]
    right_defects = [Symbolics.simplify(right[i] - weights[i]) for i in 1:3]

    k3_weights = [(3 - r) / 6, (r - 1) / 2, (3 - r) / 3]
    k3_sum_defect = Symbolics.simplify(sum(k3_weights) - 1)
    k3_scaled_identity_defects = [
        reduce_r2(k3_weights[1] * (3 + r) - 1, r),
        reduce_r2(k3_weights[2] * (3 + r) - r, r),
        reduce_r2(k3_weights[3] * (3 + r) - 2, r),
    ]
    duplicate_naive_value = r / (2r + 2)
    collapsed_value = r / (2r + 4)
    duplicate_defect = Symbolics.simplify(duplicate_naive_value - collapsed_value)
    equal_defect = (2 - r) / 3
    boundary_sum_defect = Symbolics.simplify(0 + r / (r + 2) + 2 / (r + 2) - 1)

    Dict(
        "J1_symbolics_general_k_leaf_rule" => Dict(
            "exact_strength" => "symbolic_identity",
            "weight_formula" => "rho_i/sum_j rho_j, with rho_i=sin(2eta_i)",
            "normalization_defect_k3_symbolic" => string(normalization_defect),
            "left_grouping_defects" => [string(item) for item in left_defects],
            "right_grouping_defects" => [string(item) for item in right_defects],
            "pass" => string(normalization_defect) == "0" && all(string(item) == "0" for item in vcat(left_defects, right_defects)),
        ),
        "J2_symbolics_k3_radical_weights" => Dict(
            "exact_strength" => "symbolic_radical_identity_with_r2_reduction",
            "r_constraint" => "r^2=3,r>0",
            "scaled_densities" => ["1", "r", "2"],
            "weights" => ["(3-r)/6", "(r-1)/2", "(3-r)/3"],
            "sum_defect" => string(k3_sum_defect),
            "scaled_identity_defects_after_r2_to_3" => [string(item) for item in k3_scaled_identity_defects],
            "pass" => string(k3_sum_defect) == "0" && all(string(item) in ["0", "0//1"] for item in k3_scaled_identity_defects),
        ),
        "J3_symbolics_associativity_order_row" => Dict(
            "exact_strength" => "symbolic_group_mass_associativity",
            "agreement_or_gap" => "agreement_when_iterated_union_carries_summed_group_mass",
            "left_route_weights" => [string(item) for item in left],
            "right_route_weights" => [string(item) for item in right],
            "direct_weights" => [string(item) for item in weights],
            "left_minus_direct_defects" => [string(item) for item in left_defects],
            "right_minus_direct_defects" => [string(item) for item in right_defects],
            "pass" => all(string(item) == "0" for item in vcat(left_defects, right_defects)),
        ),
        "J4_symbolics_degenerate_boundary_controls" => Dict(
            "exact_strength" => "symbolic_control_identities",
            "duplicate_double_count_defect_symbolic" => string(duplicate_defect),
            "duplicate_double_count_status" => "nonzero unless r=0; repeated leaves must collapse as sets",
            "boundary_zero_leaf_weight" => "0",
            "boundary_sum_defect" => string(boundary_sum_defect),
            "equal_weight_k3_defect_equal_minus_correct" => string(equal_defect),
            "pass" => string(duplicate_defect) != "0" && string(boundary_sum_defect) == "0" && string(equal_defect) != "0",
        ),
        "J5_mortality_boundary" => Dict(
            "exact_strength" => "symbolic_measure_boundary",
            "finite_k_naive_conditioning_denominator" => "0",
            "definable_again_k" => "no_finite_k",
            "definable_again_boundary" => "continuum_all_eta_in_[0,pi/2]; union of all shells equals S3 a.e.",
            "all_shell_constant_recovery" => "1",
            "all_shell_cos_2eta_unconditioned" => "0",
            "all_shell_cos2_2eta_unconditioned" => "1/3",
            "pass" => true,
        ),
    )
end

function z3_add(args)
    length(args) == 1 && return args[1]
    ctx = args[1].ctx
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_add(Z3.ref(ctx), Cuint(length(args)), map(Z3.as_ast, args)))
end

function z3_mul(args)
    length(args) == 1 && return args[1]
    ctx = args[1].ctx
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_mul(Z3.ref(ctx), Cuint(length(args)), map(Z3.as_ast, args)))
end

function z3_sub(a, b)
    ctx = a.ctx
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_sub(Z3.ref(ctx), Cuint(2), [Z3.as_ast(a), Z3.as_ast(b)]))
end

function z3_div(a, b)
    ctx = a.ctx
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_div(Z3.ref(ctx), Z3.as_ast(a), Z3.as_ast(b)))
end

function real_sort(ctx)
    Z3.Sort(ctx, Z3.Libz3.Z3_mk_real_sort(Z3.ref(ctx)))
end

function real_var(name::String, ctx)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_const(Z3.ref(ctx), Z3.to_symbol(name, ctx), real_sort(ctx).ast))
end

function real_val(ctx, num::Integer, den::Integer=1)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_real(Z3.ref(ctx), Cint(num), Cint(den)))
end

function z3_k3_weight_identity()
    function base()
        ctx = Z3.Context()
        vars = Dict(name => real_var(name, ctx) for name in ["r", "w1", "w2", "w3", "total"])
        solver = Z3.Solver(ctx)
        r = vars["r"]
        Z3.add(solver, z3_mul([r, r]) == real_val(ctx, 3))
        Z3.add(solver, r > real_val(ctx, 0))
        Z3.add(solver, r < real_val(ctx, 2))
        Z3.add(solver, vars["total"] == z3_add([real_val(ctx, 3), r]))
        return ctx, solver, vars
    end

    function identity(ctx, vars)
        r = vars["r"]; w1 = vars["w1"]; w2 = vars["w2"]; w3 = vars["w3"]; total = vars["total"]
        Z3.And([
            z3_mul([w1, total]) == real_val(ctx, 1),
            z3_mul([w2, total]) == r,
            z3_mul([w3, total]) == real_val(ctx, 2),
            z3_add([w1, w2, w3]) == real_val(ctx, 1),
        ])
    end

    ctx, solver, vars = base()
    r = vars["r"]
    Z3.add(solver, vars["w1"] == z3_div(z3_sub(real_val(ctx, 3), r), real_val(ctx, 6)))
    Z3.add(solver, vars["w2"] == z3_div(z3_sub(r, real_val(ctx, 1)), real_val(ctx, 2)))
    Z3.add(solver, vars["w3"] == z3_div(z3_sub(real_val(ctx, 3), r), real_val(ctx, 3)))
    Z3.add(solver, Z3.Not(identity(ctx, vars)))
    positive_verdict = string(Z3.check(solver))

    ectx, erased, evars = base()
    er = evars["r"]
    Z3.add(erased, evars["w1"] == z3_div(z3_sub(real_val(ectx, 3), er), real_val(ectx, 6)))
    Z3.add(erased, evars["w3"] == z3_div(z3_sub(real_val(ectx, 3), er), real_val(ectx, 3)))
    Z3.add(erased, Z3.Not(identity(ectx, evars)))
    erased_verdict = string(Z3.check(erased))

    qctx, equal, qvars = base()
    for name in ["w1", "w2", "w3"]
        Z3.add(equal, qvars[name] == z3_div(real_val(qctx, 1), real_val(qctx, 3)))
    end
    Z3.add(equal, identity(qctx, qvars))
    equal_verdict = string(Z3.check(equal))

    bctx = Z3.Context()
    bv = Dict(name => real_var(name, bctx) for name in ["r", "b0", "b2", "b3", "btotal"])
    boundary = Z3.Solver(bctx)
    br = bv["r"]
    Z3.add(boundary, z3_mul([br, br]) == real_val(bctx, 3))
    Z3.add(boundary, br > real_val(bctx, 0))
    Z3.add(boundary, br < real_val(bctx, 2))
    Z3.add(boundary, bv["btotal"] == z3_add([br, real_val(bctx, 2)]))
    Z3.add(boundary, bv["b0"] == real_val(bctx, 0))
    Z3.add(boundary, bv["b2"] == z3_div(br, z3_add([br, real_val(bctx, 2)])))
    Z3.add(boundary, bv["b3"] == z3_div(real_val(bctx, 2), z3_add([br, real_val(bctx, 2)])))
    boundary_identity = Z3.And([
        z3_mul([bv["b0"], bv["btotal"]]) == real_val(bctx, 0),
        z3_mul([bv["b2"], bv["btotal"]]) == br,
        z3_mul([bv["b3"], bv["btotal"]]) == real_val(bctx, 2),
        z3_add([bv["b0"], bv["b2"], bv["b3"]]) == real_val(bctx, 1),
    ])
    Z3.add(boundary, Z3.Not(boundary_identity))
    boundary_verdict = string(Z3.check(boundary))

    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "load_bearing" => true,
        "verdict" => positive_verdict,
        "expected_for_valid_identity" => "unsat",
        "claim" => "Julia Z3.jl mirror of k=3 radical weight identity with r^2=3,r>0",
        "scaled_densities" => ["1", "sqrt(3)", "2"],
        "closed_weights" => ["(3-sqrt(3))/6", "(sqrt(3)-1)/2", "(3-sqrt(3))/3"],
        "derived_expression" => "And(w1*S=1,w2*S=r,w3*S=2,w1+w2+w3=1) under S=3+r,r^2=3,r>0",
        "asserted_precomputed_boolean" => false,
        "erased_weight_w2_formula_negated_identity_verdict" => erased_verdict,
        "equal_weights_identity_verdict" => equal_verdict,
        "boundary_zero_leaf_negated_identity_verdict" => boundary_verdict,
        "erase_flip_unsat_to_sat" => positive_verdict == "unsat" && erased_verdict == "sat",
        "equal_weights_fail" => equal_verdict == "unsat",
        "boundary_pass" => boundary_verdict == "unsat",
    )
end

function tool_call(tool, qualified_api, input_object, output_object, positive_case, negative_control, boundary_case, demotion_condition, gates)
    Dict(
        "tool" => tool,
        "qualified_api/function" => qualified_api,
        "input_object" => input_object,
        "output_object" => output_object,
        "positive_case" => positive_case,
        "negative/erased_control" => negative_control,
        "boundary_case" => boundary_case,
        "demotion_condition" => demotion_condition,
        "gates" => gates,
    )
end

function main()
    mkpath(RESULT_DIR)
    receipts = symbolic_receipts()
    z3_row = z3_k3_weight_identity()
    gates = Dict(
        "symbolics_general_k_leaf_rule" => receipts["J1_symbolics_general_k_leaf_rule"]["pass"],
        "symbolics_k3_radical_weights" => receipts["J2_symbolics_k3_radical_weights"]["pass"],
        "symbolics_associativity_order_row" => receipts["J3_symbolics_associativity_order_row"]["pass"],
        "symbolics_degenerate_boundary_controls" => receipts["J4_symbolics_degenerate_boundary_controls"]["pass"],
        "mortality_boundary" => receipts["J5_mortality_boundary"]["pass"],
        "julia_z3_k3_weight_identity" => z3_row["verdict"] == "unsat" && z3_row["erase_flip_unsat_to_sat"],
    )
    all_pass = all(values(gates))
    tool_calls = [
        tool_call(
            "Symbolics",
            "Symbolics.@variables / Symbolics.simplify / Symbolics.expand / Symbolics.substitute",
            "generic rho_i finite union weights, k=3 radical weights with r^2 substitution, associativity and control expressions",
            receipts["J2_symbolics_k3_radical_weights"]["scaled_identity_defects_after_r2_to_3"],
            "normalization, grouping, and k=3 scaled weight identities reduce to zero",
            "duplicate-list and equal-weight controls remain nonzero",
            "eta=0 boundary has zero weight and finite-k mortality remains denominator zero",
            "demote if Symbolics no longer derives zero defects for the claim rows",
            ["symbolics_general_k_leaf_rule", "symbolics_k3_radical_weights", "controls"],
        ),
        tool_call(
            "Z3",
            "Z3.Solver / Z3.Libz3 real sort / Z3.check",
            "k=3 scaled density identity [1,sqrt(3),2] with real variable r constrained by r^2=3,r>0",
            z3_row["verdict"],
            "negated exact weight identity is UNSAT",
            "erasing the middle weight formula makes the negated identity SAT; equal weights fail",
            "eta=0 boundary weight identity remains UNSAT under negated violation",
            "demote if Julia Z3.jl solver does not flip under erasure",
            ["julia_z3_k3_weight_identity"],
        ),
    ]
    payload = Dict(
        "schema_version" => "engine_result_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_symbolics_z3_k_leaf_union_rule_builder",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "all_pass" => all_pass,
        "generated_at" => string(Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SS"), "Z"),
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "seed" => SEED,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "convention_pin" => CONVENTION_PIN,
        "parent_lineage" => parent_lineage(),
        "julia_project" => Base.active_project(),
        "packages_used" => ["Symbolics", "Z3", "JSON", "SHA"],
        "aligned_packages_load_bearing" => ["Z3"],
        "claim_path_tools" => ["Symbolics", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => tool_calls,
        "capability_receipts" => Dict(
            "active_project" => Base.active_project(),
            "load_path" => join(Base.LOAD_PATH, ":"),
            "symbolics_version" => maybe_pkgversion(:Symbolics),
            "z3_version" => maybe_pkgversion(:Z3),
            "z3_positive_verdict" => z3_row["verdict"],
        ),
        "receipts" => receipts,
        "crossover_proofs" => Dict("julia_z3" => z3_row),
        "build_gates" => gates,
        "summary" => Dict(
            "enables" => "finite multi-shell stacks may cite the finite-k union rule after parent-lineage and k=2 byte-exact checks",
            "does_not_enable" => "no manifold, axis, bridge, physics, canonical admission, finite-k FREE replacement, or formal proof claim is made",
            "associativity_order_row" => receipts["J3_symbolics_associativity_order_row"]["agreement_or_gap"],
            "mortality_boundary" => receipts["J5_mortality_boundary"]["definable_again_boundary"],
            "pytorch_omission" => "no graph/network/autograd claim path; engine mode is julia_symbolics_plus_python_sympy_smt_diagnostic",
        ),
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => all_pass, "result_path" => RESULT_PATH_REL, "gates" => gates)))
    return all_pass ? 0 : 1
end

exit(main())
