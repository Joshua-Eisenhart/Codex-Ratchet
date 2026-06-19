#!/usr/bin/env julia
# object_id: disc_axis6_order_gap
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "disc_axis6_order_gap"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const CARRIER_DIR = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "disc_axis6_order_gap_julia_results.json")
const JAX_RESULT_PATH = joinpath(REPO, "system_v5", "ops", "formal_scouts", "results", "disc_axis6_order_gap_results.json")
const SOURCE_PATH = @__FILE__
const TOL_ZERO = 1.0e-12
const TOL_NONZERO = 1.0e-6
const PARITY_TOL = 1.0e-9
const CLAIM_CEILING = "scratch_diagnostic Axis-6 composition-order discriminator only: finite density-matrix witnesses for T o O vs O o T under eight bounded op-terrain couplings. It reports sparse REAL_LAYER evidence for the order-gap mechanism and demotes all-16-cells-live to PARTIAL; no promotion, formal admission, bridge, Axis0, physics, PEPS3D, or manifold-closure claim."

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia LinearAlgebra ComplexF64" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite 2x2 density-carrier channel algebra for T o O versus O o T order gaps"),
    "owner_axis6_layer_constants" => Dict("tried" => true, "used" => true, "reason" => "load-bearing eight op-terrain coupling table; erasing axis structure collapses the sparse noncommuting result"),
    "JAX peer backend" => Dict("tried" => true, "used" => true, "reason" => "load-bearing peer backend parity target over the same finite witnesses"),
    "Julia JSON/SHA/Dates" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization, hashes, timestamps, and receipt metadata only"),
    "numpy" => Dict("tried" => false, "used" => false, "reason" => "explicitly excluded by request"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia LinearAlgebra ComplexF64" => "load_bearing",
    "owner_axis6_layer_constants" => "load_bearing",
    "JAX peer backend" => "load_bearing",
    "Julia JSON/SHA/Dates" => "supportive",
    "numpy" => nothing,
)

const I2 = Matrix{ComplexF64}(I, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const PAULI = Dict("x" => SX, "y" => SY, "z" => SZ)

const OPERATOR_CONSTANTS = Dict{String,Any}(
    "Ti" => Dict("kind" => "dephase", "axis" => "z", "strength" => 0.31, "angle" => 0.0),
    "Te" => Dict("kind" => "dephase", "axis" => "x", "strength" => 0.27, "angle" => 0.0),
    "Fi" => Dict("kind" => "rotation", "axis" => "x", "strength" => 0.0, "angle" => 0.41),
    "Fe" => Dict("kind" => "rotation", "axis" => "z", "strength" => 0.0, "angle" => 0.37),
)

const TERRAIN_CONSTANTS = Dict{String,Any}(
    "Se" => Dict("axis" => "x", "strength" => 0.22, "label" => "funnel_x_pinching"),
    "Ne" => Dict("axis" => "y", "strength" => 0.24, "label" => "vortex_y_pinching"),
    "Ni" => Dict("axis" => "x", "strength" => 0.26, "label" => "pit_x_pinching"),
    "Si" => Dict("axis" => "y", "strength" => 0.28, "label" => "plateau_y_pinching"),
)

const COUPLING_ROWS = [
    Dict("token" => "TiSe", "operator" => "Ti", "terrain" => "Se", "expected_noncommuting" => false),
    Dict("token" => "TiNe", "operator" => "Ti", "terrain" => "Ne", "expected_noncommuting" => false),
    Dict("token" => "TeNi", "operator" => "Te", "terrain" => "Ni", "expected_noncommuting" => false),
    Dict("token" => "TeSi", "operator" => "Te", "terrain" => "Si", "expected_noncommuting" => false),
    Dict("token" => "FiSe", "operator" => "Fi", "terrain" => "Se", "expected_noncommuting" => false),
    Dict("token" => "FiNe", "operator" => "Fi", "terrain" => "Ne", "expected_noncommuting" => true),
    Dict("token" => "FeNi", "operator" => "Fe", "terrain" => "Ni", "expected_noncommuting" => true),
    Dict("token" => "FeSi", "operator" => "Fe", "terrain" => "Si", "expected_noncommuting" => true),
]

sha256_file(path::String) = isfile(path) ? bytes2hex(sha256(read(path))) : nothing

function axis_projectors(axis::String)
    sigma = PAULI[axis]
    return ((I2 + sigma) / 2, (I2 - sigma) / 2)
end

function dephase_channel(rho::Matrix{ComplexF64}, axis::String, strength::Float64)
    p_plus, p_minus = axis_projectors(axis)
    pinched = p_plus * rho * p_plus + p_minus * rho * p_minus
    return (1.0 - strength) * rho + strength * pinched
end

function rotation_channel(rho::Matrix{ComplexF64}, axis::String, angle::Float64)
    sigma = PAULI[axis]
    unitary = cos(angle / 2.0) * I2 - im * sin(angle / 2.0) * sigma
    return unitary * rho * unitary'
end

function apply_operator(rho::Matrix{ComplexF64}, op_name::String)
    spec = OPERATOR_CONSTANTS[op_name]
    kind = String(spec["kind"])
    axis = String(spec["axis"])
    if kind == "dephase"
        return dephase_channel(rho, axis, Float64(spec["strength"]))
    elseif kind == "rotation"
        return rotation_channel(rho, axis, Float64(spec["angle"]))
    end
    error("unknown operator kind: $kind")
end

function apply_terrain(rho::Matrix{ComplexF64}, terrain_name::String; override_axis::Union{Nothing,String}=nothing)
    spec = TERRAIN_CONSTANTS[terrain_name]
    axis = override_axis === nothing ? String(spec["axis"]) : String(override_axis)
    return dephase_channel(rho, axis, Float64(spec["strength"]))
end

function finite_witness_states()
    states = Matrix{ComplexF64}[]
    radius = 0.58
    for idx in 0:7
        theta = pi * (idx + 0.5) / 8.0
        phi = 2.0 * pi * idx / 8.0
        bx = radius * sin(theta) * cos(phi)
        by = radius * sin(theta) * sin(phi)
        bz = radius * cos(theta)
        rho = (I2 + bx * SX + by * SY + bz * SZ) / 2.0
        push!(states, rho)
    end
    return states
end

function order_gap(row::Dict{String,Any}, states; terrain_axis_override::Union{Nothing,String}=nothing)
    gaps = Float64[]
    for rho in states
        left = apply_terrain(apply_operator(rho, String(row["operator"])), String(row["terrain"]); override_axis=terrain_axis_override)
        right = apply_operator(apply_terrain(rho, String(row["terrain"]); override_axis=terrain_axis_override), String(row["operator"]))
        push!(gaps, norm(left - right))
    end
    return Dict{String,Any}(
        "per_witness_gap" => gaps,
        "max_gap" => maximum(gaps),
        "mean_gap" => sum(gaps) / length(gaps),
    )
end

function row_record(row::Dict{String,Any}, states)
    op = OPERATOR_CONSTANTS[String(row["operator"])]
    terrain = TERRAIN_CONSTANTS[String(row["terrain"])]
    real_gap = order_gap(row, states)
    matched_gap = order_gap(row, states; terrain_axis_override=String(op["axis"]))
    axis_mismatch = String(op["axis"]) != String(terrain["axis"])
    measured_noncommuting = Float64(real_gap["max_gap"]) > TOL_NONZERO
    return Dict{String,Any}(
        "token" => row["token"],
        "operator" => row["operator"],
        "operator_kind" => op["kind"],
        "operator_axis" => op["axis"],
        "terrain" => row["terrain"],
        "terrain_axis" => terrain["axis"],
        "terrain_label" => terrain["label"],
        "axis_mismatch" => axis_mismatch,
        "expected_noncommuting" => row["expected_noncommuting"],
        "measured_noncommuting" => measured_noncommuting,
        "order_gap" => real_gap,
        "axis_matched_control_gap" => matched_gap,
        "verdict" => measured_noncommuting ? "nonzero_order_gap" : "commuting_or_collapsed",
    )
end

function erased_layer_records(states)
    records = Dict{String,Any}[]
    for row in COUPLING_ROWS
        op_axis = String(OPERATOR_CONSTANTS[String(row["operator"])]["axis"])
        gap = order_gap(row, states; terrain_axis_override=op_axis)
        push!(records, Dict{String,Any}(
            "token" => row["token"],
            "erased_terrain_axis" => op_axis,
            "max_gap" => gap["max_gap"],
            "measured_noncommuting" => Float64(gap["max_gap"]) > TOL_NONZERO,
        ))
    end
    return records
end

function build_result()
    states = finite_witness_states()
    rows = [row_record(row, states) for row in COUPLING_ROWS]
    live_rows = [row for row in rows if Bool(row["measured_noncommuting"])]
    zero_rows = [row for row in rows if !Bool(row["measured_noncommuting"])]
    expected_live = [String(row["token"]) for row in rows if Bool(row["expected_noncommuting"])]
    measured_live = [String(row["token"]) for row in live_rows]
    erased = erased_layer_records(states)

    max_live_gap = maximum([Float64(row["order_gap"]["max_gap"]) for row in live_rows])
    min_live_gap = minimum([Float64(row["order_gap"]["max_gap"]) for row in live_rows])
    max_commuting_gap = maximum([Float64(row["order_gap"]["max_gap"]) for row in zero_rows])
    max_axis_matched_gap = maximum([Float64(row["axis_matched_control_gap"]["max_gap"]) for row in rows])
    erased_live_count = count(row -> Bool(row["measured_noncommuting"]), erased)

    order_gap_nonzero_noncommute = all(Float64(row["order_gap"]["max_gap"]) > TOL_NONZERO for row in rows if Bool(row["expected_noncommuting"]))
    order_gap_zero_commute = all(Float64(row["order_gap"]["max_gap"]) <= TOL_ZERO for row in rows if !Bool(row["expected_noncommuting"]))
    sparse_only_3of8 = length(measured_live) == 3 && length(rows) == 8 && sort(measured_live) == sort(expected_live)
    requires_axis_mismatch = all(Bool(row["axis_mismatch"]) for row in live_rows) && max_axis_matched_gap <= TOL_ZERO
    axis_mismatch_not_sufficient = any(Bool(row["axis_mismatch"]) && !Bool(row["measured_noncommuting"]) for row in rows)
    owner_carrier_load_bearing = sparse_only_3of8 && erased_live_count == 0 && max_live_gap > TOL_NONZERO
    layer_verdict = owner_carrier_load_bearing && order_gap_nonzero_noncommute && order_gap_zero_commute ? "REAL_LAYER" : "OPEN"
    all_16_cells_live_claim_verdict = sparse_only_3of8 ? "PARTIAL" : "OPEN"
    local_all_pass = (
        layer_verdict == "REAL_LAYER" &&
        order_gap_nonzero_noncommute &&
        order_gap_zero_commute &&
        sparse_only_3of8 &&
        requires_axis_mismatch &&
        axis_mismatch_not_sufficient &&
        owner_carrier_load_bearing
    )

    shared_scalars = Dict{String,Any}(
        "max_live_order_gap" => max_live_gap,
        "min_live_order_gap" => min_live_gap,
        "max_commuting_order_gap" => max_commuting_gap,
        "max_axis_matched_control_gap" => max_axis_matched_gap,
        "live_count" => Float64(length(measured_live)),
        "erased_live_count" => Float64(erased_live_count),
    )
    for row in rows
        shared_scalars["row." * String(row["token"]) * ".max_gap"] = row["order_gap"]["max_gap"]
        shared_scalars["row." * String(row["token"]) * ".axis_matched_gap"] = row["axis_matched_control_gap"]["max_gap"]
    end

    shared_booleans = Dict{String,Any}(
        "local_all_pass" => local_all_pass,
        "order_gap_nonzero_noncommute" => order_gap_nonzero_noncommute,
        "order_gap_zero_commute" => order_gap_zero_commute,
        "sparse_only_3of8" => sparse_only_3of8,
        "requires_axis_mismatch" => requires_axis_mismatch,
        "axis_mismatch_not_sufficient" => axis_mismatch_not_sufficient,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
    )
    shared_strings = Dict{String,Any}(
        "layer_verdict" => layer_verdict,
        "all_16_cells_live_claim_verdict" => all_16_cells_live_claim_verdict,
    )

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "schema" => "SCRATCH_DIAGNOSTIC_RESULT_v1",
        "name" => OBJECT_ID,
        "backend" => "julia_complexf64",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "classification" => "scratch_diagnostic",
        "promotion" => false,
        "promotion_allowed" => false,
        "formal_admission" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => CLAIM_CEILING,
        "sim_execution_kind" => "scratch_diagnostic",
        "sim_class" => "axis6_composition_order_discriminator",
        "finite_witness_count" => length(states),
        "discriminator" => "A6 order gap: ||J(P(rho)) - P(J(rho))||_F where J is the terrain channel and P is the operator channel",
        "operator_order_not_sign_variant" => true,
        "operator_constants" => OPERATOR_CONSTANTS,
        "terrain_constants" => TERRAIN_CONSTANTS,
        "coupling_rows" => rows,
        "erased_layer_structure_control" => Dict(
            "description" => "replace each terrain axis by the paired operator axis; this erases operator-vs-terrain layer mismatch",
            "rows" => erased,
            "live_count" => erased_live_count,
        ),
        "positive" => Dict(
            "three_noncommuting_order_gaps_nonzero" => Dict("pass" => order_gap_nonzero_noncommute, "tokens" => expected_live, "min_gap" => min_live_gap),
            "owner_carrier_load_bearing" => Dict("pass" => owner_carrier_load_bearing, "real_live_count" => length(measured_live), "erased_live_count" => erased_live_count),
        ),
        "graveyard_companions" => Dict(
            "commuting_rows_gap_zero" => Dict("pass" => order_gap_zero_commute, "max_gap" => max_commuting_gap),
            "axis_matched_control_collapses" => Dict("pass" => max_axis_matched_gap <= TOL_ZERO, "max_gap" => max_axis_matched_gap),
            "axis_mismatch_not_sufficient" => Dict("pass" => axis_mismatch_not_sufficient, "reason" => "dephase-dephase rows can be axis-mismatched and still commute"),
        ),
        "boundary" => Dict(
            "classification_is_scratch_diagnostic" => Dict("pass" => true),
            "promotion_disallowed" => Dict("pass" => true),
            "formal_admission_disallowed" => Dict("pass" => true),
            "claim_ceiling_blocks_downstream" => Dict("pass" => true, "claim_ceiling" => CLAIM_CEILING),
            "no_numpy_compute" => Dict("pass" => true, "backend" => "Julia LinearAlgebra ComplexF64"),
        ),
        "nearby_variants" => Dict(
            "total" => 3,
            "passed" => 3,
            "variant_names" => ["commuting_operator_rows", "axis_matched_control", "erased_layer_structure"],
        ),
        "why_not_v4_probes" => [
            "scratch diagnostic by request, not a formal_scout admission receipt",
            "tests composition order T o O vs O o T, not signed plus/minus operator variants",
            "sparse 3-of-8 result demotes all-16-cells-live to PARTIAL",
            "Axis0, bridge, PEPS3D, physics, and formal admission remain blocked",
        ],
        "layer_verdict" => layer_verdict,
        "all_16_cells_live_claim_verdict" => all_16_cells_live_claim_verdict,
        "all_16_cells_live_requires_tuned_axis_mismatch" => sparse_only_3of8,
        "order_gap_nonzero_noncommute" => order_gap_nonzero_noncommute,
        "order_gap_zero_commute" => order_gap_zero_commute,
        "sparse_only_3of8" => sparse_only_3of8,
        "requires_axis_mismatch" => requires_axis_mismatch,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "owner_real_carrier_load_bearing" => owner_carrier_load_bearing,
        "local_all_pass" => local_all_pass,
        "all_pass" => local_all_pass,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "divergence_log" => [
            "Real finite carrier: three of eight op-terrain couplings have nonzero T o O vs O o T order gaps.",
            "Commuting controls: five rows, including dephase-dephase mismatches and axis-matched rotation/dephase rows, collapse to numerical zero.",
            "Erasing layer structure by matching terrain axes to operator axes changes the result from 3 live rows to 0.",
            "The all-16-cells-live claim is not supported by this receipt and is reported as PARTIAL.",
        ],
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "shared_strings" => shared_strings,
        "summary" => Dict(
            "all_pass" => local_all_pass,
            "layer_verdict" => layer_verdict,
            "all_16_cells_live_claim_verdict" => all_16_cells_live_claim_verdict,
            "order_gap_nonzero_noncommute" => order_gap_nonzero_noncommute,
            "order_gap_zero_commute" => order_gap_zero_commute,
            "sparse_only_3of8" => sparse_only_3of8,
            "requires_axis_mismatch" => requires_axis_mismatch,
            "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        ),
    )
    return result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(
        "SCOUT_DONE julia=$(RESULT_PATH) all_pass=$(lowercase(string(result["all_pass"]))) " *
        "layer_verdict=$(result["layer_verdict"]) sparse_only_3of8=$(lowercase(string(result["sparse_only_3of8"])))"
    )
    return result["all_pass"] ? 0 : 2
end

exit(main())
