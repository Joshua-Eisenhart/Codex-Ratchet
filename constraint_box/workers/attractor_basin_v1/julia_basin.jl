#!/usr/bin/env julia
# Independent Julia reference-basin worker for the fixed controller challenge.
# It deliberately consumes no peer result, bridge, CSV, pickle, or NumPy input.

using Attractors
using SHA

const DSB = Attractors.DynamicalSystemsBase
const NOMINAL_H = 0.2
const WRONG_SIGN_H = -0.2
const STEPS = 80
const GRID_X = collect(-1.5:0.1:1.5)
const GRID_Y = collect(-0.5:0.1:0.5)
const BASIN_EPSILON = 0.05
const HORIZON_LIMIT = 10.0
const DEFAULT_OUTPUT_DIR = normpath(joinpath(
    @__DIR__, "..", "..", "outputs", "cb_attractor_basin_three_engine_20260801", "julia",
))

sha256_string(value::AbstractString) = bytes2hex(SHA.sha256(codeunits(value)))
sha256_file(path::AbstractString) = isfile(path) ? bytes2hex(SHA.sha256(read(path))) : nothing
matrix_hash(matrix) = sha256_string(join(string.(vec(matrix)), ","))
x_derivative(h::Float64, x::Float64) = 1.0 - h * (3.0 * x^2 - 1.0)

function resolve_output_dir()
    cli_output_dir = nothing
    if isempty(ARGS)
        # Use the source-relative default below.
    elseif length(ARGS) == 2 && ARGS[1] == "--output-dir"
        isempty(strip(ARGS[2])) && error("--output-dir cannot be empty")
        cli_output_dir = ARGS[2]
    else
        error("usage: julia_basin.jl [--output-dir <directory>]")
    end

    env_output_dir = strip(get(ENV, "CB_BASIN_OUTPUT_DIR", ""))
    !isnothing(cli_output_dir) && !isempty(env_output_dir) && error(
        "set either --output-dir or CB_BASIN_OUTPUT_DIR, not both",
    )
    requested_dir = !isnothing(cli_output_dir) ? cli_output_dir : (
        isempty(env_output_dir) ? DEFAULT_OUTPUT_DIR : env_output_dir
    )
    return normpath(abspath(requested_dir))
end

function json_escape(value::AbstractString)
    return replace(
        String(value),
        "\\" => "\\\\",
        "\"" => "\\\"",
        "\n" => "\\n",
        "\r" => "\\r",
        "\t" => "\\t",
    )
end

function json_value(value)
    if value === nothing
        return "null"
    elseif value isa Bool
        return value ? "true" : "false"
    elseif value isa Integer
        return string(value)
    elseif value isa AbstractFloat
        isfinite(value) || error("receipt does not encode non-finite floats")
        return repr(value)
    elseif value isa AbstractString
        return "\"$(json_escape(value))\""
    elseif value isa Symbol
        return json_value(string(value))
    elseif value isa AbstractDict
        ordered_keys = sort!(collect(keys(value)); by = string)
        entries = [json_value(string(key)) * ":" * json_value(value[key]) for key in ordered_keys]
        return "{" * join(entries, ",") * "}"
    elseif value isa Tuple || value isa AbstractArray
        return "[" * join((json_value(item) for item in value), ",") * "]"
    else
        error("unsupported receipt value type: $(typeof(value))")
    end
end

function constrained_map(h::Float64)
    # F_h(x, y) = (x - h * (x^3 - x), 0.5 * y)
    return (u, p, n) -> Attractors.SVector(
        u[1] - h * (u[1]^3 - u[1]),
        0.5 * u[2],
    )
end

function new_system(h::Float64)
    return DSB.DeterministicIteratedMap(
        constrained_map(h),
        Attractors.SVector(GRID_X[1], GRID_Y[1]),
    )
end

function candidate_attractors(; erase_positive::Bool = false)
    negative = Attractors.StateSpaceSet([Attractors.SVector(-1.0, 0.0)])
    positive = Attractors.StateSpaceSet([Attractors.SVector(1.0, 0.0)])
    return erase_positive ? Dict(1 => negative) : Dict(1 => negative, 2 => positive)
end

function run_actual_basin(h::Float64; erase_positive::Bool = false)
    ds = new_system(h)
    candidates = candidate_attractors(; erase_positive)
    mapper = Attractors.AttractorsViaProximity(
        ds,
        candidates;
        ε = BASIN_EPSILON,
        Δt = 1,
        Ttr = 0,
        consecutive_lost_steps = STEPS,
        horizon_limit = HORIZON_LIMIT,
        stop_at_Δt = true,
    )
    basins, discovered = Attractors.basins_of_attraction(mapper, (GRID_X, GRID_Y))
    return (
        basins = copy(basins),
        discovered = discovered,
        candidate_keys = sort!(collect(keys(candidates))),
        ds_type = string(typeof(ds)),
        mapper_type = string(typeof(mapper)),
    )
end

function exact_terminal_sign_partition(h::Float64)
    ds = new_system(h)
    labels = Matrix{Int32}(undef, length(GRID_X), length(GRID_Y))
    min_abs_nonboundary_terminal_x = Inf
    all_finite = true

    for (x_index, x0) in enumerate(GRID_X), (y_index, y0) in enumerate(GRID_Y)
        DSB.reinit!(ds, Attractors.SVector(x0, y0))
        for _ in 1:STEPS
            DSB.step!(ds)
        end
        terminal = DSB.current_state(ds)
        all_finite &= all(isfinite, terminal)
        if x0 == 0.0
            labels[x_index, y_index] = -1
        else
            min_abs_nonboundary_terminal_x = min(min_abs_nonboundary_terminal_x, abs(terminal[1]))
            labels[x_index, y_index] = terminal[1] < 0.0 ? 1 : 2
        end
    end

    return (
        labels = labels,
        min_abs_nonboundary_terminal_x = min_abs_nonboundary_terminal_x,
        all_finite = all_finite,
    )
end

function terminal_state_after_80_steps(h::Float64, x0::Float64, y0::Float64)
    ds = new_system(h)
    DSB.reinit!(ds, Attractors.SVector(x0, y0))
    for _ in 1:STEPS
        DSB.step!(ds)
    end
    return collect(DSB.current_state(ds))
end

function label_counts(labels)
    return Dict(
        string(Int(label)) => count(==(label), labels)
        for label in sort!(collect(unique(vec(labels))))
    )
end

function grid_description()
    return Dict(
        "x" => Dict("start" => -1.5, "step" => 0.1, "stop" => 1.5, "count" => length(GRID_X)),
        "y" => Dict("start" => -0.5, "step" => 0.1, "stop" => 0.5, "count" => length(GRID_Y)),
        "shape" => [length(GRID_X), length(GRID_Y)],
        "grid_point_count" => length(GRID_X) * length(GRID_Y),
        "boundary_rule" => "boundary iff initial x is exactly 0.0",
    )
end

function build_receipt(output_dir::AbstractString)
    source_path = abspath(@__FILE__)
    active_project = Base.active_project()
    manifest_path = joinpath(dirname(active_project), "Manifest.toml")
    output_file = joinpath(output_dir, "julia_basin_receipt.json")
    dsb_module = Attractors.DynamicalSystemsBase
    staticarrays_module = parentmodule(Attractors.SVector)

    nominal = run_actual_basin(NOMINAL_H)
    terminal = exact_terminal_sign_partition(NOMINAL_H)
    wrong = run_actual_basin(WRONG_SIGN_H)
    erased = run_actual_basin(NOMINAL_H; erase_positive = true)
    replay = run_actual_basin(NOMINAL_H)

    boundary_x_indices = findall(==(0.0), GRID_X)
    length(boundary_x_indices) == 1 || error("controller grid does not expose exactly one x=0 boundary row")
    boundary_x_index = only(boundary_x_indices)
    boundary_labels = vec(nominal.basins[boundary_x_index, :])
    nonboundary_attractors = [
        nominal.basins[x_index, y_index]
        for x_index in eachindex(GRID_X), y_index in eachindex(GRID_Y)
        if x_index != boundary_x_index
    ]

    nominal_counts = label_counts(nominal.basins)
    terminal_counts = Dict(
        "negative" => count(==(Int32(1)), terminal.labels),
        "positive" => count(==(Int32(2)), terminal.labels),
        "boundary" => count(==(Int32(-1)), terminal.labels),
    )
    nominal_terminal_mismatch_count = count(nominal.basins .!= terminal.labels)
    wrong_changed_cell_count = count(nominal.basins .!= wrong.basins)
    nominal_fixed_point_abs_derivative = abs(x_derivative(NOMINAL_H, 1.0))
    wrong_fixed_point_abs_derivative = abs(x_derivative(WRONG_SIGN_H, 1.0))
    nominal_origin_abs_derivative = abs(x_derivative(NOMINAL_H, 0.0))
    wrong_origin_abs_derivative = abs(x_derivative(WRONG_SIGN_H, 0.0))
    fake_severed_partition = fill(Int32(0), size(nominal.basins))
    fake_partition_rejected = fake_severed_partition != nominal.basins

    positive_observed =
        length(nominal.discovered) == 2 &&
        nominal_counts == Dict("-1" => 11, "1" => 165, "2" => 165) &&
        terminal_counts == Dict("negative" => 165, "positive" => 165, "boundary" => 11) &&
        nominal_terminal_mismatch_count == 0 &&
        terminal.all_finite
    wrong_observed =
        wrong_changed_cell_count > 0 &&
        count(==(-1), wrong.basins) > count(==(-1), nominal.basins) &&
        nominal_fixed_point_abs_derivative < 1.0 &&
        wrong_fixed_point_abs_derivative > 1.0 &&
        nominal_origin_abs_derivative > 1.0 &&
        wrong_origin_abs_derivative < 1.0
    erased_observed = !(2 in erased.candidate_keys) && !any(==(2), erased.basins)
    boundary_observed =
        all(==(-1), boundary_labels) &&
        all(label -> label == 1 || label == 2, nonboundary_attractors)
    replay_observed = nominal.basins == replay.basins && nominal.discovered == replay.discovered
    severance_observed = fake_partition_rejected

    receipt = Dict{String, Any}(
        "schema_version" => "cb_attractor_basin_three_engine.julia.v1",
        "role_id" => "julia_authoritative_sim_builder",
        "worker_status" => "raw_execution_complete",
        "claim_ceiling" => "scratch_diagnostic: deterministic finite-grid Julia basin calculation only; not canonical/formal/scientific admission",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "scientific_admission_allowed" => false,
        "builder_statement" => "This builder recorded raw execution and controls only; it did not audit, certify, admit, or promote the result.",
        "source" => Dict(
            "path" => source_path,
            "sha256" => sha256_file(source_path),
        ),
        "runtime" => Dict(
            "julia_version" => string(VERSION),
            "julia_executable" => first(Base.julia_cmd().exec),
            "active_project" => active_project,
            "active_project_sha256" => sha256_file(active_project),
            "manifest_path" => manifest_path,
            "manifest_sha256" => sha256_file(manifest_path),
            "load_path" => copy(Base.LOAD_PATH),
            "runtime_descriptor_sha256" => sha256_string(join([
                string(VERSION),
                active_project,
                string(Base.pkgversion(Attractors)),
                string(Base.pkgversion(dsb_module)),
            ], "|")),
        ),
        "packages" => Dict(
            "Attractors" => Dict(
                "version" => string(Base.pkgversion(Attractors)),
                "root" => Base.pkgdir(Attractors),
            ),
            "DynamicalSystemsBase" => Dict(
                "version" => string(Base.pkgversion(dsb_module)),
                "root" => Base.pkgdir(dsb_module),
                "accessed_as" => "Attractors.DynamicalSystemsBase",
            ),
            "StaticArraysCore" => Dict(
                "version" => string(Base.pkgversion(staticarrays_module)),
                "accessed_as" => "Attractors.SVector",
            ),
        ),
        "fixed_challenge" => Dict(
            "equation" => "F_h(x,y)=(x-h*(x^3-x),0.5*y)",
            "nominal_h" => NOMINAL_H,
            "wrong_sign_h" => WRONG_SIGN_H,
            "steps" => STEPS,
            "float_type" => "Float64",
            "stable_attractor_candidates" => [[-1.0, 0.0], [1.0, 0.0]],
            "unstable_separatrix" => [0.0, 0.0],
            "grid" => grid_description(),
        ),
        "actual_apis" => [
            "Attractors.DynamicalSystemsBase.DeterministicIteratedMap",
            "Attractors.DynamicalSystemsBase.reinit!",
            "Attractors.DynamicalSystemsBase.step!",
            "Attractors.DynamicalSystemsBase.current_state",
            "Attractors.StateSpaceSet",
            "Attractors.AttractorsViaProximity",
            "Attractors.basins_of_attraction",
        ],
        "function_level_evidence" => [
            Dict(
                "function" => "run_actual_basin",
                "actual_call" => "Attractors.AttractorsViaProximity followed by Attractors.basins_of_attraction",
                "nominal_system_type" => nominal.ds_type,
                "nominal_mapper_type" => nominal.mapper_type,
                "nominal_partition_sha256" => matrix_hash(nominal.basins),
            ),
            Dict(
                "function" => "exact_terminal_sign_partition",
                "actual_call" => "DynamicalSystemsBase.reinit! and step! for exactly 80 steps per grid point",
                "terminal_sign_partition_sha256" => matrix_hash(terminal.labels),
            ),
        ],
        "measurements" => Dict(
            "nominal_attractor_keys" => nominal.candidate_keys,
            "nominal_returned_attractor_count" => length(nominal.discovered),
            "nominal_basin_label_counts" => nominal_counts,
            "nominal_basin_partition_sha256" => matrix_hash(nominal.basins),
            "terminal_sign_label_counts" => terminal_counts,
            "terminal_sign_partition_sha256" => matrix_hash(terminal.labels),
            "nominal_terminal_mismatch_count" => nominal_terminal_mismatch_count,
            "minimum_abs_terminal_x_nonboundary" => terminal.min_abs_nonboundary_terminal_x,
            "terminal_states_after_80_steps" => Dict(
                "negative_corner" => terminal_state_after_80_steps(NOMINAL_H, -1.5, -0.5),
                "boundary" => terminal_state_after_80_steps(NOMINAL_H, 0.0, 0.0),
                "positive_corner" => terminal_state_after_80_steps(NOMINAL_H, 1.5, 0.5),
            ),
        ),
        "controls" => Dict(
            "positive" => Dict(
                "observed" => positive_observed,
                "real_attractors_partition_sha256" => matrix_hash(nominal.basins),
                "exact_80_step_terminal_partition_sha256" => matrix_hash(terminal.labels),
                "mismatch_count" => nominal_terminal_mismatch_count,
            ),
            "wrong_sign" => Dict(
                "observed" => wrong_observed,
                "h" => WRONG_SIGN_H,
                "real_attractors_partition_sha256" => matrix_hash(wrong.basins),
                "label_counts" => label_counts(wrong.basins),
                "changed_cell_count_vs_nominal" => wrong_changed_cell_count,
                "abs_x_derivative" => Dict(
                    "nominal_at_plus_minus_one" => nominal_fixed_point_abs_derivative,
                    "wrong_sign_at_plus_minus_one" => wrong_fixed_point_abs_derivative,
                    "nominal_at_origin" => nominal_origin_abs_derivative,
                    "wrong_sign_at_origin" => wrong_origin_abs_derivative,
                ),
            ),
            "erased_positive_attractor" => Dict(
                "observed" => erased_observed,
                "candidate_keys" => erased.candidate_keys,
                "real_attractors_partition_sha256" => matrix_hash(erased.basins),
                "label_counts" => label_counts(erased.basins),
            ),
            "boundary" => Dict(
                "observed" => boundary_observed,
                "exact_x_zero_row_index" => boundary_x_index,
                "x_zero_grid_point_count" => length(GRID_Y),
                "actual_boundary_labels" => collect(Int.(boundary_labels)),
                "rule" => "only exact initial x=0.0 is classified as boundary",
            ),
            "replay" => Dict(
                "observed" => replay_observed,
                "first_partition_sha256" => matrix_hash(nominal.basins),
                "replay_partition_sha256" => matrix_hash(replay.basins),
            ),
            "severance" => Dict(
                "observed" => severance_observed,
                "fabricated_all_zero_partition_sha256" => matrix_hash(fake_severed_partition),
                "fabricated_partition_rejected_against_actual_attractors_output" => fake_partition_rejected,
                "reads_peer_result" => false,
                "peer_result_paths" => String[],
                "foreign_runtime_inputs" => String[],
                "direct_imports" => ["Attractors", "SHA"],
                "nonpeer_file_reads" => [source_path, active_project, manifest_path],
            ),
        ),
        "receipt_types" => Dict(
            "numeric_values" => "JSON numbers",
            "control_flags" => "JSON booleans",
            "partition_hashes" => "sha256 hex strings",
            "receipt_encoding" => "standalone JSON serializer in source; no external data codec input",
        ),
        "execution" => Dict(
            "recommended_command" => "<julia> --startup-file=no --project=<julia-project> workers/attractor_basin_v1/julia_basin.jl --output-dir <directory>",
            "output_dir" => output_dir,
            "output_file" => output_file,
            "output_dir_resolution" => "--output-dir, otherwise CB_BASIN_OUTPUT_DIR, otherwise source-relative default",
            "reads_peer_result" => false,
            "cross_engine_result_comparison" => false,
        ),
    )

    return receipt, Dict(
        "positive" => positive_observed,
        "wrong_sign" => wrong_observed,
        "erased_positive_attractor" => erased_observed,
        "boundary" => boundary_observed,
        "replay" => replay_observed,
        "severance" => severance_observed,
    )
end

function main()
    output_dir = resolve_output_dir()
    output_file = joinpath(output_dir, "julia_basin_receipt.json")
    receipt, raw_controls = build_receipt(output_dir)
    mkpath(output_dir)
    open(output_file, "w") do io
        write(io, json_value(receipt))
        write(io, "\n")
    end
    println("JULIA_BASIN_RECEIPT=", output_file)
    println("JULIA_BASIN_RAW_CONTROLS=", json_value(raw_controls))
    all(values(raw_controls)) || error("one or more raw controls was not observed; receipt written for external review")
end

main()
