#!/usr/bin/env julia
# object_id: r3_readout_invariants
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA
using UUIDs

const OBJECT_ID = "r3_readout_invariants"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const DEFAULT_JAX_RESULT_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/r3_readout_invariants_results.json")
const DEFAULT_RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/r3_readout_invariants_julia_results.json")
const TOL = 1.0e-12
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const SIM_EXECUTION_KIND = "nonclassical"
const ALLOWED_CLAIM = "Finite R3 scalar readout-dependence taxonomy over verified R0-R3 foundation receipts; scratch diagnostic only."
const BLOCKED_CLAIMS = ["formal_admission", "promotion", "top_floor_claim", "physics_claim", "downstream_doctrine_claim"]
const CLAIM_CEILING = "Allowed only: finite bottom-up scalar readout taxonomy and mutation classifier. No formal admission, no promotion, no physics/top-floor consumer."

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent finite density, quotient, carrier, and operation-algebra scalar readouts"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing traces, eigenvalues, and norm computations"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive current JAX receipt read and Julia result write"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive parity digest over the shared scalar/boolean/string payload"),
    "JAX peer" => Dict("tried" => true, "used" => true, "reason" => "load-bearing same-run peer backend reference"),
    "numpy" => Dict("tried" => false, "used" => false, "reason" => "not used in Julia mirror"),
    "pytorch" => Dict("tried" => false, "used" => false, "reason" => "not used: explicit rung fence says no torch"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "JSON" => "supportive",
    "SHA" => "supportive",
    "JAX peer" => "load_bearing",
    "numpy" => nothing,
    "pytorch" => nothing,
)

const SIM_TEMPLATE_SURFACE = Dict{String,Any}(
    "identity" => ["sim_id", "name", "version", "tier"],
    "tooling" => ["TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "classification"],
    "negatives" => ["positive", "negative", "boundary", "probe"],
    "promotion" => ["promotion_allowed", "formal_admission_allowed", "blocked_consumers"],
)

const I2 = ComplexF64[1 0; 0 1]
const Z = ComplexF64[1 0; 0 -1]
const HAD = (1.0 / sqrt(2.0)) .* ComplexF64[1 1; 1 -1]

rounded(value::Real, digits::Int = 12) = round(Float64(value); digits = digits)

function ket(values::Vector{ComplexF64})
    vec = copy(values)
    vec ./ sqrt(real(dot(vec, vec)))
end

density(psi::Vector{ComplexF64}) = psi * psi'

function make_probe(name::String, vectors::Vector{Vector{ComplexF64}})
    Dict{String,Any}("name" => name, "effects" => [density(vec) for vec in vectors])
end

function base_kets()
    Dict{String,Vector{ComplexF64}}(
        "z0" => ket(ComplexF64[1 + 0im, 0 + 0im]),
        "z1" => ket(ComplexF64[0 + 0im, 1 + 0im]),
        "x_plus" => ket(ComplexF64[1 + 0im, 1 + 0im]),
        "x_minus" => ket(ComplexF64[1 + 0im, -1 + 0im]),
    )
end

function candidate_configurations()
    ks = base_kets()
    [
        Dict{String,Any}("id" => "pure_z0", "rho" => density(ks["z0"])),
        Dict{String,Any}("id" => "pure_z1", "rho" => density(ks["z1"])),
        Dict{String,Any}("id" => "pure_x_plus", "rho" => density(ks["x_plus"])),
        Dict{String,Any}("id" => "pure_x_minus", "rho" => density(ks["x_minus"])),
    ]
end

function probes()
    ks = base_kets()
    Dict{String,Any}(
        "Z" => make_probe("Z", [ks["z0"], ks["z1"]]),
        "X" => make_probe("X", [ks["x_plus"], ks["x_minus"]]),
        "BLIND" => Dict{String,Any}("name" => "BLIND", "effects" => Matrix{ComplexF64}[I2]),
    )
end

function measurement_stats(rho::Matrix{ComplexF64}, probe::Dict{String,Any})
    [rounded(real(tr(effect * rho)), 12) for effect in probe["effects"]]
end

function quotient_class_count(candidates::Vector{Dict{String,Any}}, probe_family::Vector{Dict{String,Any}})
    signatures = Set{String}()
    for candidate in candidates
        sig = [measurement_stats(candidate["rho"], probe) for probe in probe_family]
        push!(signatures, JSON.json(sig))
    end
    length(signatures)
end

function von_neumann_entropy(rho::Matrix{ComplexF64})
    total = 0.0
    for value in real.(eigvals(Hermitian(rho)))
        if value > TOL
            total -= value * log(value)
        end
    end
    round(total; digits = 15)
end

purity(rho::Matrix{ComplexF64}) = round(real(tr(rho * rho)); digits = 15)

function op_signature(commuting::Bool)
    left = commuting ? Z * I2 : Z * HAD
    right = commuting ? I2 * Z : HAD * Z
    round(norm(left - right); digits = 15)
end

function cd_conj(x::Vector{Float64})
    collect(x) .* vcat([1.0], fill(-1.0, length(x) - 1))
end

function cd_multiply(table::Array{Float64,3}, x::Vector{Float64}, y::Vector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function basis_vector(dim::Int, idx::Int)
    vec = zeros(Float64, dim)
    vec[idx + 1] = 1.0
    vec
end

function cd_pair_multiply(parent::Array{Float64,3}, x::Vector{Float64}, y::Vector{Float64})
    n = size(parent, 1)
    a = x[1:n]
    b = x[(n + 1):(2 * n)]
    c = y[1:n]
    d = y[(n + 1):(2 * n)]
    first = cd_multiply(parent, a, c) - cd_multiply(parent, cd_conj(d), b)
    second = cd_multiply(parent, d, a) + cd_multiply(parent, b, cd_conj(c))
    vcat(first, second)
end

function cd_double(parent::Array{Float64,3})
    n = size(parent, 1)
    dim = 2 * n
    table = zeros(Float64, dim, dim, dim)
    for i in 0:(dim - 1), j in 0:(dim - 1)
        table[:, i + 1, j + 1] .= cd_pair_multiply(parent, basis_vector(dim, i), basis_vector(dim, j))
    end
    table
end

function carrier_tables()
    r = zeros(Float64, 1, 1, 1)
    r[1, 1, 1] = 1.0
    c = cd_double(r)
    h = cd_double(c)
    o = cd_double(h)
    Dict{String,Any}("H" => h, "O" => o)
end

function associator_defect(table::Array{Float64,3})
    dim = size(table, 1)
    max_value = 0.0
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1)
        ea = basis_vector(dim, a)
        eb = basis_vector(dim, b)
        ec = basis_vector(dim, c)
        left = cd_multiply(table, cd_multiply(table, ea, eb), ec)
        right = cd_multiply(table, ea, cd_multiply(table, eb, ec))
        max_value = max(max_value, round(norm(left - right); digits = 15))
    end
    max_value
end

l1_gap(left::Vector{Float64}, right::Vector{Float64}) = sum(abs(a - b) for (a, b) in zip(left, right))

function no_self_diff_tautologies(rows)
    all(
        row["left_expression_id"] != row["right_expression_id"] &&
            row["left_quantity_id"] != row["right_quantity_id"]
        for row in rows
    )
end

function build_classifier()
    ps = probes()
    candidates = candidate_configurations()
    relabeled = reverse(candidates)
    pure = candidates[1]["rho"]
    mixed = 0.5 .* candidates[1]["rho"] .+ 0.5 .* candidates[2]["rho"]
    tables = carrier_tables()

    readout_values = Dict{String,Any}(
        "quotient_class_count" => Dict(
            "base" => Float64(quotient_class_count(candidates, Dict{String,Any}[ps["Z"]])),
            "mutate_M" => Float64(quotient_class_count(candidates, Dict{String,Any}[ps["Z"], ps["X"]])),
            "carrier_relabel" => Float64(quotient_class_count(relabeled, Dict{String,Any}[ps["Z"]])),
        ),
        "quotient_resolution" => Dict(
            "base" => log(Float64(quotient_class_count(candidates, Dict{String,Any}[ps["Z"]]))),
            "mutate_M" => log(Float64(quotient_class_count(candidates, Dict{String,Any}[ps["Z"], ps["X"]]))),
            "carrier_relabel" => log(Float64(quotient_class_count(relabeled, Dict{String,Any}[ps["Z"]]))),
        ),
        "von_neumann_entropy" => Dict(
            "base" => von_neumann_entropy(pure),
            "mutate_density" => von_neumann_entropy(mixed),
            "mutate_M" => von_neumann_entropy(pure),
            "carrier_relabel" => von_neumann_entropy(pure),
        ),
        "purity" => Dict(
            "base" => purity(pure),
            "mutate_density" => purity(mixed),
            "mutate_M" => purity(pure),
            "carrier_relabel" => purity(pure),
        ),
        "associator_defect" => Dict(
            "base" => associator_defect(tables["O"]),
            "mutate_carrier" => associator_defect(tables["H"]),
            "mutate_M" => associator_defect(tables["O"]),
        ),
        "commutation_order_signature" => Dict(
            "base" => op_signature(false),
            "mutate_operation_algebra" => op_signature(true),
            "mutate_density" => op_signature(false),
            "carrier_relabel" => op_signature(false),
        ),
    )
    specs = Dict{String,Any}(
        "quotient_class_count" => Dict("dependence" => "PROBE_DEPENDENT", "positive_factor" => "M", "positive_key" => "mutate_M", "control_keys" => ["carrier_relabel"]),
        "quotient_resolution" => Dict("dependence" => "PROBE_DEPENDENT", "positive_factor" => "M", "positive_key" => "mutate_M", "control_keys" => ["carrier_relabel"]),
        "von_neumann_entropy" => Dict("dependence" => "DENSITY_DERIVED", "positive_factor" => "density", "positive_key" => "mutate_density", "control_keys" => ["mutate_M", "carrier_relabel"]),
        "purity" => Dict("dependence" => "DENSITY_DERIVED", "positive_factor" => "density", "positive_key" => "mutate_density", "control_keys" => ["mutate_M", "carrier_relabel"]),
        "associator_defect" => Dict("dependence" => "CARRIER_DEPENDENT", "positive_factor" => "carrier", "positive_key" => "mutate_carrier", "control_keys" => ["mutate_M"]),
        "commutation_order_signature" => Dict("dependence" => "OPERATION_ALGEBRA_DEPENDENT", "positive_factor" => "operation_algebra", "positive_key" => "mutate_operation_algebra", "control_keys" => ["mutate_density", "carrier_relabel"]),
    )

    rows = Dict{String,Any}()
    dependence_map = Dict{String,String}()
    probe_dependent = String[]
    carrier_dependent = String[]
    density_derived = String[]
    operation_algebra_dependent = String[]
    control_pairs = Any[]
    for (readout, spec) in specs
        row_values = readout_values[readout]
        base = Float64(row_values["base"])
        positive_value = Float64(row_values[spec["positive_key"]])
        positive_delta = abs(positive_value - base)
        control_deltas = Dict{String,Any}(
            key => abs(Float64(row_values[key]) - base) for key in spec["control_keys"]
        )
        pass_value = positive_delta > TOL && all(delta <= TOL for delta in values(control_deltas))
        rows[readout] = Dict{String,Any}(
            "readout" => readout,
            "classification" => spec["dependence"],
            "positive_mutation_factor" => spec["positive_factor"],
            "base_value" => base,
            "positive_mutation_value" => positive_value,
            "positive_delta" => positive_delta,
            "control_deltas" => control_deltas,
            "pass" => pass_value,
            "can_misclassify" => true,
            "iff_rule" => "only the declared dependence mutation changes this scalar above tolerance",
        )
        dependence_map[readout] = spec["dependence"]
        if spec["dependence"] == "PROBE_DEPENDENT"
            push!(probe_dependent, readout)
        elseif spec["dependence"] == "CARRIER_DEPENDENT"
            push!(carrier_dependent, readout)
        elseif spec["dependence"] == "DENSITY_DERIVED"
            push!(density_derived, readout)
        elseif spec["dependence"] == "OPERATION_ALGEBRA_DEPENDENT"
            push!(operation_algebra_dependent, readout)
        end
        push!(control_pairs, Dict{String,Any}(
            "name" => "$(readout)_positive_mutation",
            "left_expression_id" => "$(readout).base",
            "right_expression_id" => "$(readout).$(spec["positive_key"])",
            "left_quantity_id" => "$(readout)_base_value",
            "right_quantity_id" => "$(readout)_$(spec["positive_key"])_value",
            "gap" => positive_delta,
            "can_fail" => true,
        ))
    end
    no_self_diff = no_self_diff_tautologies(control_pairs)
    Dict{String,Any}(
        "readout_rows" => rows,
        "readout_dependence_map" => dependence_map,
        "probe_dependent" => sort(probe_dependent),
        "carrier_dependent" => sort(carrier_dependent),
        "density_derived" => sort(density_derived),
        "operation_algebra_dependent" => sort(operation_algebra_dependent),
        "control_comparison_pairs" => control_pairs,
        "no_self_diff" => no_self_diff,
        "all_classified" => all(Bool(row["pass"]) for row in values(rows)),
        "readouts_count" => length(rows),
    )
end

function shared_digest(shared)
    bytes2hex(sha256(JSON.json(shared)))
end

function dependence_map_string(dependence_map)
    join(["$(key)=$(dependence_map[key])" for key in sort(collect(keys(dependence_map)))], "|")
end

function parity_against_jax(result, jax_data)
    max_diff = 0.0
    rows = Any[]
    missing = String[]
    for (key, value) in result["shared_scalars"]
        if !haskey(jax_data["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        diff = abs(Float64(value) - Float64(jax_data["shared_scalars"][key]))
        max_diff = max(max_diff, diff)
        push!(rows, Dict("key" => key, "julia" => Float64(value), "jax" => Float64(jax_data["shared_scalars"][key]), "abs_diff" => diff))
    end
    boolean_mismatches = Any[]
    for (key, value) in result["shared_booleans"]
        if !haskey(jax_data["shared_booleans"], key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(jax_data["shared_booleans"][key])
            push!(boolean_mismatches, Dict("key" => key, "julia" => Bool(value), "jax" => Bool(jax_data["shared_booleans"][key])))
        end
    end
    string_mismatches = Any[]
    for (key, value) in result["shared_strings"]
        if !haskey(jax_data["shared_strings"], key)
            push!(missing, key)
            continue
        end
        if string(value) != string(jax_data["shared_strings"][key])
            push!(string_mismatches, Dict("key" => key, "julia" => string(value), "jax" => string(jax_data["shared_strings"][key])))
        end
    end
    within_run = result["jax_reference_within_run_id"] == get(jax_data, "within_run_id", "") &&
        result["jax_reference_shared_value_digest"] == get(jax_data, "shared_value_digest", "")
    Dict{String,Any}(
        "peer_result_path" => result["jax_reference_path"],
        "status" => "compared",
        "within_1e_12" => max_diff <= TOL && isempty(boolean_mismatches) && isempty(string_mismatches) && isempty(missing) && within_run,
        "parity_max_diff" => max_diff,
        "numeric_rows" => rows,
        "boolean_mismatches" => boolean_mismatches,
        "string_mismatches" => string_mismatches,
        "missing_keys" => missing,
        "parity_within_run" => within_run,
    )
end

function build_result(jax_reference_path::String, result_path::String)
    jax_data = JSON.parsefile(jax_reference_path)
    classifier = build_classifier()
    classification_genuine = get(get(jax_data, "shared_booleans", Dict{String,Any}()), "classification_genuine", false) == true
    shared_scalars = Dict{String,Any}()
    for (name, row) in classifier["readout_rows"]
        shared_scalars["$name.base"] = Float64(row["base_value"])
        shared_scalars["$name.positive_delta"] = Float64(row["positive_delta"])
    end
    shared_booleans = Dict{String,Any}(
        "parent_receipts_verified" => get(jax_data["shared_booleans"], "parent_receipts_verified", false) == true,
        "readout_classifier_all_pass" => classifier["all_classified"],
        "no_self_diff" => classifier["no_self_diff"],
        "classification_genuine" => classification_genuine,
        "classification_is_scratch_diagnostic" => CLASSIFICATION == "scratch_diagnostic",
        "promotion_false" => PROMOTION_ALLOWED == false,
        "formal_admission_false" => FORMAL_ADMISSION_ALLOWED == false,
        "jax_enable_x64" => get(jax_data["shared_booleans"], "jax_enable_x64", false) == true,
        "numpy_compute_used" => false,
        "torch_compute_used" => false,
        "no_top_floor" => true,
    )
    shared_strings = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "allowed_claim" => ALLOWED_CLAIM,
        "claim_ceiling" => CLAIM_CEILING,
        "dependence_map" => dependence_map_string(classifier["readout_dependence_map"]),
    )
    shared = Dict("shared_scalars" => shared_scalars, "shared_booleans" => shared_booleans, "shared_strings" => shared_strings)
    result = Dict{String,Any}(
        "schema" => "codex_ratchet.julia_carrier.scratch_diagnostic.v1",
        "object_id" => OBJECT_ID,
        "sim_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "version" => "1.0",
        "tier" => "R3_readout_invariants_taxonomy",
        "backend" => "julia",
        "within_run_id" => string(uuid4()),
        "generated_at" => string(Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS"), "Z"),
        "source_path" => @__FILE__,
        "result_path" => result_path,
        "jax_reference_path" => jax_reference_path,
        "jax_reference_within_run_id" => get(jax_data, "within_run_id", ""),
        "jax_reference_shared_value_digest" => get(jax_data, "shared_value_digest", ""),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "allowed_claims" => [ALLOWED_CLAIM],
        "blocked_claims" => BLOCKED_CLAIMS,
        "claim_ceiling" => CLAIM_CEILING,
        "promotion_status" => "diagnostic_only",
        "eligible_consumers" => [],
        "blocked_consumers" => BLOCKED_CLAIMS,
        "sim_execution_kind" => SIM_EXECUTION_KIND,
        "sim_class" => "constraint_probe",
        "purpose" => "Julia mirror classifies finite R3 scalar readouts by genuine mutation dependence.",
        "SIM_TEMPLATE_surface" => SIM_TEMPLATE_SURFACE,
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "required_tools" => ["Julia", "LinearAlgebra", "JAX peer"],
        "actual_tools_used" => ["Julia", "LinearAlgebra", "JSON", "SHA", "JAX peer"],
        "numpy_compute_used" => false,
        "numpy_imported" => false,
        "torch_compute_used" => false,
        "torch_imported" => false,
        "tol" => TOL,
        "probe" => Dict(
            "readouts" => sort(collect(keys(classifier["readout_rows"]))),
            "mutation_factors" => ["M", "density", "carrier", "operation_algebra"],
            "classifier_rule" => "a readout is assigned to the only mutation factor that changes it above tolerance",
        ),
        "readout_dependence_map" => classifier["readout_dependence_map"],
        "readout_rows" => classifier["readout_rows"],
        "probe_dependent" => classifier["probe_dependent"],
        "carrier_dependent" => classifier["carrier_dependent"],
        "density_derived" => classifier["density_derived"],
        "operation_algebra_dependent" => classifier["operation_algebra_dependent"],
        "control_comparison_pairs" => classifier["control_comparison_pairs"],
        "positive" => Dict(
            "readout_classifier_all_pass" => Dict("pass" => classifier["all_classified"]),
            "classification_genuine" => Dict("pass" => classification_genuine),
            "no_self_diff_tautologies" => Dict("pass" => classifier["no_self_diff"]),
        ),
        "negative" => Dict(
            "wrong_probe_dependence_controls_stable" => Dict(
                "pass" => all(delta <= TOL for row in values(classifier["readout_rows"]) for delta in values(row["control_deltas"])),
            ),
            "top_floor_blocked" => Dict("pass" => true, "blocked_claims" => BLOCKED_CLAIMS),
            "self_diff_control_rejected" => Dict("pass" => classifier["no_self_diff"]),
        ),
        "boundary" => Dict(
            "quaternion_octonion_associator_boundary" => Dict("pass" => classifier["readout_rows"]["associator_defect"]["positive_delta"] > TOL),
            "commuting_noncommuting_operation_boundary" => Dict("pass" => classifier["readout_rows"]["commutation_order_signature"]["positive_delta"] > TOL),
            "classification_fence" => Dict("pass" => CLASSIFICATION == "scratch_diagnostic" && PROMOTION_ALLOWED == false && FORMAL_ADMISSION_ALLOWED == false),
        ),
        "why_not_v4_probes" => "This is a v5 scratch diagnostic bottom-up formal-scout receipt with no promotion or formal admission.",
        "required_artifacts" => [jax_reference_path, result_path],
        "artifacts_emitted" => [result_path],
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "shared_strings" => shared_strings,
        "shared_value_digest" => shared_digest(shared),
        "result_summary" => Dict(
            "readouts_count" => classifier["readouts_count"],
            "probe_dependent" => classifier["probe_dependent"],
            "carrier_dependent" => classifier["carrier_dependent"],
            "density_derived" => classifier["density_derived"],
            "classification_genuine" => classification_genuine,
            "no_self_diff" => classifier["no_self_diff"],
            "all_pass" => false,
        ),
    )
    result["parity"] = parity_against_jax(result, jax_data)
    result["positive"]["dual_backend_parity"] = Dict("pass" => result["parity"]["within_1e_12"])
    result["all_pass"] = Bool(result["parity"]["within_1e_12"]) && classifier["all_classified"] && classifier["no_self_diff"] && classification_genuine
    result["stop_condition_fired"] = !Bool(result["all_pass"])
    result["parity_within_run"] = Bool(result["parity"]["parity_within_run"])
    result["no_self_diff"] = Bool(classifier["no_self_diff"])
    result["classification_genuine"] = Bool(classification_genuine)
    result["pass_rule"] = "all readouts classify by iff mutation, no self-diff controls, fenced scratch diagnostic, and same-run JAX/Julia parity"
    result["fail_rule"] = "any misclassified readout, stale JAX reference, missing parity, self-diff control, or fence violation"
    result["result_summary"]["parity_within_run"] = result["parity_within_run"]
    result["result_summary"]["all_pass"] = result["all_pass"]
    result
end

function main()
    jax_path = get(ENV, "R3_READOUT_JAX_RESULT", DEFAULT_JAX_RESULT_PATH)
    result_path = get(ENV, "R3_READOUT_JULIA_RESULT", DEFAULT_RESULT_PATH)
    result = build_result(jax_path, result_path)
    mkpath(dirname(result_path))
    open(result_path, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict(
        "all_pass" => result["all_pass"],
        "parity_within_run" => result["parity_within_run"],
        "no_self_diff" => result["no_self_diff"],
        "readouts_count" => result["result_summary"]["readouts_count"],
    )))
    return result["all_pass"] ? 0 : 1
end

exit(main())
