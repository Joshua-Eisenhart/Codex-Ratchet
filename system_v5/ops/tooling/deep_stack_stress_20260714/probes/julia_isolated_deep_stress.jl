#!/usr/bin/env julia

"""
Deep operational probe for one Codex Ratchet isolated Julia package.

The same source is run in three deliberately separate projects.  It never
installs packages, never imports a Python bridge, and never reads another
engine's receipt.  A failed operational case is preserved as a red row; exit 2
is reserved for a broken CLI/output harness.

Required arguments:

    --tool-id jl_tensorkit|jl_pepskit|jl_intervalarithmetic
    --out /absolute/or/relative/result.json
    --repo-root /path/to/Codex-Ratchet
"""

import Dates
import Random
import SHA
import TOML

const SOURCE_RELATIVE =
    "system_v5/ops/tooling/deep_stack_stress_20260714/probes/julia_isolated_deep_stress.jl"
const EDGE_ID = "jl_isolated_tensor"
const FORBIDDEN_BRIDGES = Set(["PythonCall", "DLPack", "CondaPkg", "PyCall"])

const TOOL_CONFIG = Dict(
    "jl_tensorkit" => Dict(
        "package" => "TensorKit",
        "family" => "julia_tensor",
        "runtime_id" => "julia_tensorkit",
        "project" => "/Users/joshuaeisenhart/.julia/environments/codex-ratchet-tensorkit-v1.12/Project.toml",
        "imports" => ["TensorKit", "IntervalArithmetic"],
    ),
    "jl_pepskit" => Dict(
        "package" => "PEPSKit",
        "family" => "julia_tensor",
        "runtime_id" => "julia_peps",
        "project" => "/Users/joshuaeisenhart/.julia/environments/codex-ratchet-peps-v1.12/Project.toml",
        "imports" => ["PEPSKit", "TensorKit", "IntervalArithmetic"],
    ),
    "jl_intervalarithmetic" => Dict(
        "package" => "IntervalArithmetic",
        "family" => "certified_bounds",
        "runtime_id" => "julia_attractors",
        "project" => "/Users/joshuaeisenhart/.julia/environments/codex-ratchet-attractors-v1.12/Project.toml",
        "imports" => ["IntervalArithmetic", "StaticArrays"],
    ),
)


function parse_cli(args::Vector{String})
    values = Dict{String,String}()
    known = Set(["--tool-id", "--out", "--repo-root"])
    index = 1
    while index <= length(args)
        raw = args[index]
        key = raw
        value = nothing
        if occursin('=', raw)
            parts = split(raw, '='; limit = 2)
            key, value = parts[1], parts[2]
        else
            key in known || error("unknown argument: $(raw)")
            index == length(args) && error("missing value for $(key)")
            index += 1
            value = args[index]
        end
        key in known || error("unknown argument: $(key)")
        haskey(values, key) && error("duplicate argument: $(key)")
        isempty(value) && error("empty value for $(key)")
        values[key] = value
        index += 1
    end
    for key in known
        haskey(values, key) || error("missing required argument: $(key)")
    end
    haskey(TOOL_CONFIG, values["--tool-id"]) ||
        error("unknown tool id: $(values["--tool-id"])")
    Dict(
        "tool_id" => values["--tool-id"],
        "out" => abspath(values["--out"]),
        "repo_root" => abspath(values["--repo-root"]),
    )
end


const CLI = parse_cli(ARGS)
const TOOL_ID = CLI["tool_id"]
const CONFIG = TOOL_CONFIG[TOOL_ID]
const ACTIVE_PROJECT = something(Base.active_project(), "")
const EXPECTED_PROJECT = CONFIG["project"]
const PROJECT_MATCH =
    !isempty(ACTIVE_PROJECT) && normpath(abspath(ACTIVE_PROJECT)) == normpath(EXPECTED_PROJECT)
const STRICT_LOAD_PATH =
    get(ENV, "JULIA_LOAD_PATH", "") == "@:@stdlib" && Base.LOAD_PATH == ["@", "@stdlib"]
const IMPORT_STATUS = Dict{String,Any}()


function error_record(err, backtrace = nothing)
    Dict(
        "type" => string(typeof(err)),
        "message" => backtrace === nothing ? sprint(showerror, err) : sprint(showerror, err, backtrace),
    )
end


function record_import_success!(name::String, package_module, started::UInt64)
    IMPORT_STATUS[name] = Dict(
        "passed" => true,
        "version" => string(something(Base.pkgversion(package_module), "unknown")),
        "module_path" => something(Base.pathof(package_module), "unknown"),
        "error" => nothing,
        "duration_ms" => round((time_ns() - started) / 1.0e6; digits = 3),
    )
end


function record_import_failure!(name::String, err, backtrace, started::UInt64)
    IMPORT_STATUS[name] = Dict(
        "passed" => false,
        "version" => nothing,
        "module_path" => nothing,
        "error" => error_record(err, backtrace),
        "duration_ms" => round((time_ns() - started) / 1.0e6; digits = 3),
    )
end


function record_import_skipped!(name::String)
    IMPORT_STATUS[name] = Dict(
        "passed" => false,
        "version" => nothing,
        "module_path" => nothing,
        "error" => Dict(
            "type" => "RuntimeGuardError",
            "message" => "package import skipped because isolated-project or strict-load-path guard failed",
        ),
        "duration_ms" => 0.0,
    )
end


# Literal top-level imports avoid Julia 1.12's world-age warning for dynamically
# created global bindings while still letting each isolated project fail closed.
if !(PROJECT_MATCH && STRICT_LOAD_PATH)
    for package in CONFIG["imports"]
        record_import_skipped!(package)
    end
elseif TOOL_ID == "jl_tensorkit"
    started = time_ns()
    try
        import TensorKit
        record_import_success!("TensorKit", TensorKit, started)
    catch err
        record_import_failure!("TensorKit", err, catch_backtrace(), started)
    end
    started = time_ns()
    try
        import IntervalArithmetic
        record_import_success!("IntervalArithmetic", IntervalArithmetic, started)
    catch err
        record_import_failure!("IntervalArithmetic", err, catch_backtrace(), started)
    end
elseif TOOL_ID == "jl_pepskit"
    started = time_ns()
    try
        import PEPSKit
        record_import_success!("PEPSKit", PEPSKit, started)
    catch err
        record_import_failure!("PEPSKit", err, catch_backtrace(), started)
    end
    started = time_ns()
    try
        import TensorKit
        record_import_success!("TensorKit", TensorKit, started)
    catch err
        record_import_failure!("TensorKit", err, catch_backtrace(), started)
    end
    started = time_ns()
    try
        import IntervalArithmetic
        record_import_success!("IntervalArithmetic", IntervalArithmetic, started)
    catch err
        record_import_failure!("IntervalArithmetic", err, catch_backtrace(), started)
    end
elseif TOOL_ID == "jl_intervalarithmetic"
    started = time_ns()
    try
        import IntervalArithmetic
        record_import_success!("IntervalArithmetic", IntervalArithmetic, started)
    catch err
        record_import_failure!("IntervalArithmetic", err, catch_backtrace(), started)
    end
    started = time_ns()
    try
        import StaticArrays
        record_import_success!("StaticArrays", StaticArrays, started)
    catch err
        record_import_failure!("StaticArrays", err, catch_backtrace(), started)
    end
end


function json_escape(value::AbstractString)
    io = IOBuffer()
    for char in value
        if char == '"'
            write(io, "\\\"")
        elseif char == '\\'
            write(io, "\\\\")
        elseif char == '\b'
            write(io, "\\b")
        elseif char == '\f'
            write(io, "\\f")
        elseif char == '\n'
            write(io, "\\n")
        elseif char == '\r'
            write(io, "\\r")
        elseif char == '\t'
            write(io, "\\t")
        elseif Int(char) < 0x20
            write(io, "\\u", lpad(string(Int(char); base = 16), 4, '0'))
        else
            write(io, char)
        end
    end
    String(take!(io))
end


function emit_json(io::IO, value)
    if value === nothing || value === missing
        write(io, "null")
    elseif value isa Bool
        write(io, value ? "true" : "false")
    elseif value isa Integer
        write(io, string(value))
    elseif value isa AbstractFloat
        isfinite(value) ? write(io, string(value)) : emit_json(io, string(value))
    elseif value isa AbstractString || value isa Symbol || value isa VersionNumber || value isa Dates.TimeType
        write(io, '"', json_escape(string(value)), '"')
    elseif value isa NamedTuple
        emit_json(io, Dict(string(key) => getfield(value, key) for key in keys(value)))
    elseif value isa AbstractDict
        write(io, '{')
        ordered = sort!(collect(keys(value)); by = string)
        for (index, key) in enumerate(ordered)
            index > 1 && write(io, ',')
            emit_json(io, string(key))
            write(io, ':')
            emit_json(io, value[key])
        end
        write(io, '}')
    elseif value isa Tuple || value isa AbstractVector || value isa Set
        write(io, '[')
        for (index, item) in enumerate(value)
            index > 1 && write(io, ',')
            emit_json(io, item)
        end
        write(io, ']')
    elseif value isa Real
        emit_json(io, Float64(value))
    else
        emit_json(io, string(value))
    end
end


function write_json(path::String, value)
    normpath(path) == normpath(abspath(@__FILE__)) && error("refusing to overwrite probe source")
    mkpath(dirname(path))
    open(path, "w") do io
        emit_json(io, value)
        write(io, '\n')
    end
end


sha256_file(path::String) = bytes2hex(SHA.sha256(read(path)))
outcome(passed::Bool, observed) = Dict("passed" => passed, "observed" => observed)


function expected_error(expected_type::Type, f::Function)
    try
        f()
        outcome(false, Dict("threw" => false, "expected_type" => string(expected_type)))
    catch err
        outcome(
            err isa expected_type,
            Dict(
                "threw" => true,
                "expected_type" => string(expected_type),
                "observed_type" => string(typeof(err)),
                "message" => sprint(showerror, err),
            ),
        )
    end
end


expected_error(f::Function, expected_type::Type) = expected_error(expected_type, f)


function run_case(
    label::String,
    qualified_api::String,
    input_object,
    expected::String,
    f::Function,
)
    started = time_ns()
    try
        result = f()
        result isa AbstractDict || error("case must return an object")
        haskey(result, "passed") || error("case result lacks passed")
        haskey(result, "observed") || error("case result lacks observed")
        Dict(
            "label" => label,
            "qualified_api" => qualified_api,
            "input_object" => input_object,
            "expected" => expected,
            "passed" => result["passed"] === true,
            "observed" => result["observed"],
            "error" => nothing,
            "duration_ms" => round((time_ns() - started) / 1.0e6; digits = 3),
        )
    catch err
        Dict(
            "label" => label,
            "qualified_api" => qualified_api,
            "input_object" => input_object,
            "expected" => expected,
            "passed" => false,
            "observed" => nothing,
            "error" => error_record(err, catch_backtrace()),
            "duration_ms" => round((time_ns() - started) / 1.0e6; digits = 3),
        )
    end
end


# Julia `do` blocks are passed as the first positional argument.
run_case(f::Function, label::String, qualified_api::String, input_object, expected::String) =
    run_case(label, qualified_api, input_object, expected, f)


function tensorkit_probe()
    positive = run_case(
        "two-state tensor space",
        "TensorKit.ComplexSpace/TensorKit.:⊗/TensorKit.dim/TensorKit.dual",
        Dict("factor_dimensions" => [2, 2]),
        "the tensor product has dimension four and dualization preserves dimension",
    ) do
        left = TensorKit.ComplexSpace(2)
        product = TensorKit.:⊗(left, left)
        observed_dims = Dict(
            "factor" => TensorKit.dim(left),
            "product" => TensorKit.dim(product),
            "dual" => TensorKit.dim(TensorKit.dual(product)),
        )
        outcome(observed_dims == Dict("factor" => 2, "product" => 4, "dual" => 4), observed_dims)
    end

    negative = run_case(
        "erased tensor factor control",
        "TensorKit.ComplexSpace/TensorKit.:⊗/TensorKit.dim",
        Dict("factor_dimensions" => [2, 1], "rejected_impostor_dimension" => 4),
        "replacing one two-state factor by a one-state factor changes the product dimension",
    ) do
        product = TensorKit.:⊗(TensorKit.ComplexSpace(2), TensorKit.ComplexSpace(1))
        dimension = TensorKit.dim(product)
        outcome(dimension == 2 && dimension != 4, Dict("actual_dimension" => dimension, "impostor_rejected" => dimension != 4))
    end

    boundary = run_case(
        "zero-dimensional boundary",
        "TensorKit.ComplexSpace/TensorKit.:⊗/TensorKit.dim",
        Dict("factor_dimensions" => [2, 0]),
        "tensoring with the zero-dimensional boundary yields dimension zero",
    ) do
        product = TensorKit.:⊗(TensorKit.ComplexSpace(2), TensorKit.ComplexSpace(0))
        dimension = TensorKit.dim(product)
        outcome(dimension == 0, Dict("product_dimension" => dimension))
    end

    stress = run_case(
        "twelve-factor tensor-product stress",
        "TensorKit.ComplexSpace/TensorKit.:⊗/TensorKit.dim/TensorKit.dual",
        Dict("factor_count" => 12, "factor_dimension" => 2),
        "the metadata-level 12-factor product and its dual both have dimension 4096",
    ) do
        factors = [TensorKit.ComplexSpace(2) for _ in 1:12]
        product = foldl((left, right) -> TensorKit.:⊗(left, right), factors)
        dimension = TensorKit.dim(product)
        dual_dimension = TensorKit.dim(TensorKit.dual(product))
        outcome(dimension == 4_096 && dual_dimension == 4_096, Dict("dimension" => dimension, "dual_dimension" => dual_dimension))
    end

    adjacent = run_case(
        "TensorKit dimension to interval enclosure edge",
        "TensorKit.dim/IntervalArithmetic.interval/IntervalArithmetic.inf/IntervalArithmetic.sup",
        Dict("tensor_space_dimension" => 2),
        "the TensorKit-derived dimension is preserved as a guaranteed singleton interval",
    ) do
        dimension = TensorKit.dim(TensorKit.ComplexSpace(2))
        enclosure = IntervalArithmetic.interval(Float64(dimension), Float64(dimension))
        lower = IntervalArithmetic.inf(enclosure)
        upper = IntervalArithmetic.sup(enclosure)
        passed = lower == 2.0 && upper == 2.0 && IntervalArithmetic.isguaranteed(enclosure)
        outcome(passed, Dict("lower" => lower, "upper" => upper, "guaranteed" => IntervalArithmetic.isguaranteed(enclosure)))
    end

    demotion = run_case(
        "wrong product-dimension demotion",
        "TensorKit.dim",
        Dict("factor_dimensions" => [2, 2], "claimed_product_dimension" => 3),
        "a package-derived dimension gate rejects the falsified dimension",
    ) do
        actual = TensorKit.dim(TensorKit.:⊗(TensorKit.ComplexSpace(2), TensorKit.ComplexSpace(2)))
        claimed = 3
        outcome(actual != claimed, Dict("actual" => actual, "claimed" => claimed, "demoted" => actual != claimed))
    end

    Dict(
        "qualified_api" => [
            "TensorKit.ComplexSpace",
            "TensorKit.:⊗",
            "TensorKit.dim",
            "TensorKit.dual",
        ],
        "demotion_condition" => "demote if package-derived space dimensions, zero boundary, bounded product scaling, or interval interoperability fail",
        "positive" => positive,
        "negative" => negative,
        "boundary" => boundary,
        "stress" => stress,
        "adjacent" => adjacent,
        "demotion" => demotion,
    )
end


function pepskit_probe()
    positive = run_case(
        "PEPS and CTMRG environment construction",
        "PEPSKit.InfinitePEPS/PEPSKit.CTMRGEnv/TensorKit.ComplexSpace",
        Dict("physical_dimension" => 2, "bond_dimension" => 2, "environment_dimension" => 4),
        "real TensorKit spaces construct a one-site InfinitePEPS and CTMRGEnv",
    ) do
        Random.seed!(20_260_714)
        state = PEPSKit.InfinitePEPS(TensorKit.ComplexSpace(2), TensorKit.ComplexSpace(2))
        environment = PEPSKit.CTMRGEnv(state, TensorKit.ComplexSpace(4))
        passed = state isa PEPSKit.InfinitePEPS && environment isa PEPSKit.CTMRGEnv && size(state) == (1, 1)
        outcome(passed, Dict("state_type" => string(typeof(state)), "environment_type" => string(typeof(environment)), "lattice_size" => collect(size(state))))
    end

    negative = run_case(
        "primitive-integer space rejection",
        "PEPSKit.InfinitePEPS",
        Dict("physical_space" => 2, "bond_space" => 2),
        "the public constructor rejects primitive integers in place of TensorKit spaces",
    ) do
        expected_error(MethodError) do
            PEPSKit.InfinitePEPS(2, 2)
        end
    end

    boundary = run_case(
        "unit-dimension PEPS boundary",
        "PEPSKit.InfinitePEPS/PEPSKit.CTMRGEnv/TensorKit.ComplexSpace",
        Dict("physical_dimension" => 1, "bond_dimension" => 1, "environment_dimension" => 1),
        "the one-dimensional product-state boundary constructs without a hidden minimum bond dimension",
    ) do
        Random.seed!(20_260_715)
        state = PEPSKit.InfinitePEPS(TensorKit.ComplexSpace(1), TensorKit.ComplexSpace(1))
        environment = PEPSKit.CTMRGEnv(state, TensorKit.ComplexSpace(1))
        passed = state isa PEPSKit.InfinitePEPS && environment isa PEPSKit.CTMRGEnv && size(state) == (1, 1)
        outcome(passed, Dict("state_type" => string(typeof(state)), "environment_type" => string(typeof(environment)), "lattice_size" => collect(size(state))))
    end

    stress = run_case(
        "mixed-dimension constructor stress",
        "PEPSKit.InfinitePEPS/PEPSKit.CTMRGEnv/TensorKit.ComplexSpace",
        Dict("construction_count" => 24, "physical_dimensions" => [1, 2, 3], "bond_dimensions" => [1, 2], "environment_dimensions" => [1, 2, 3, 4]),
        "24 bounded mixed-dimension PEPS/environment pairs retain valid public types and lattice shape",
    ) do
        Random.seed!(20_260_716)
        count = 24
        valid = true
        for index in 1:count
            physical = TensorKit.ComplexSpace(1 + index % 3)
            bond = TensorKit.ComplexSpace(1 + index % 2)
            state = PEPSKit.InfinitePEPS(physical, bond)
            environment = PEPSKit.CTMRGEnv(state, TensorKit.ComplexSpace(1 + index % 4))
            valid &= state isa PEPSKit.InfinitePEPS
            valid &= environment isa PEPSKit.CTMRGEnv
            valid &= size(state) == (1, 1)
        end
        outcome(valid, Dict("construction_count" => count, "all_types_and_shapes_valid" => valid))
    end

    adjacent = run_case(
        "PEPSKit-TensorKit-IntervalArithmetic compatibility edge",
        "PEPSKit.CTMRGEnv/TensorKit.dim/IntervalArithmetic.interval",
        Dict("environment_dimension" => 4),
        "the same TensorKit environment space constructs CTMRGEnv and supplies a guaranteed interval control",
    ) do
        Random.seed!(20_260_717)
        state = PEPSKit.InfinitePEPS(TensorKit.ComplexSpace(2), TensorKit.ComplexSpace(2))
        environment_space = TensorKit.ComplexSpace(4)
        environment = PEPSKit.CTMRGEnv(state, environment_space)
        dimension = TensorKit.dim(environment_space)
        enclosure = IntervalArithmetic.interval(Float64(dimension), Float64(dimension))
        passed = environment isa PEPSKit.CTMRGEnv && IntervalArithmetic.inf(enclosure) == 4.0 && IntervalArithmetic.sup(enclosure) == 4.0 && IntervalArithmetic.isguaranteed(enclosure)
        outcome(passed, Dict("environment_type" => string(typeof(environment)), "dimension_lower" => IntervalArithmetic.inf(enclosure), "dimension_upper" => IntervalArithmetic.sup(enclosure)))
    end

    demotion = run_case(
        "invalid-space demotion",
        "PEPSKit.InfinitePEPS",
        Dict("physical_space" => "primitive Int", "bond_space" => "primitive Int"),
        "a MethodError prevents an import-only or wrong-space constructor from being reported operational",
    ) do
        result = expected_error(MethodError) do
            PEPSKit.InfinitePEPS(2, 2)
        end
        outcome(result["passed"] === true, merge(result["observed"], Dict("demoted" => result["passed"] === true)))
    end

    Dict(
        "qualified_api" => [
            "PEPSKit.InfinitePEPS",
            "PEPSKit.CTMRGEnv",
            "TensorKit.ComplexSpace",
        ],
        "demotion_condition" => "demote if wrong-space calls are accepted, unit boundaries fail, mixed-dimension constructors drift, or TensorKit/interval compatibility breaks",
        "positive" => positive,
        "negative" => negative,
        "boundary" => boundary,
        "stress" => stress,
        "adjacent" => adjacent,
        "demotion" => demotion,
    )
end


function intervalarithmetic_probe()
    positive = run_case(
        "guaranteed sine enclosure",
        "IntervalArithmetic.interval/IntervalArithmetic.sin/IntervalArithmetic.inf/IntervalArithmetic.sup/IntervalArithmetic.isguaranteed",
        Dict("domain" => [0.0, 1.0]),
        "sin([0,1]) encloses both endpoint values with the guaranteed flag set",
    ) do
        domain = IntervalArithmetic.interval(0.0, 1.0)
        enclosure = IntervalArithmetic.sin(domain)
        lower = IntervalArithmetic.inf(enclosure)
        upper = IntervalArithmetic.sup(enclosure)
        passed = lower <= sin(0.0) && upper >= sin(1.0) && IntervalArithmetic.isguaranteed(enclosure)
        outcome(passed, Dict("lower" => lower, "upper" => upper, "guaranteed" => IntervalArithmetic.isguaranteed(enclosure)))
    end

    negative = run_case(
        "endpoint-only square enclosure rejection",
        "IntervalArithmetic.interval/IntervalArithmetic.issubset_interval/Base.:^",
        Dict("domain" => [-1.0, 1.0], "impostor_enclosure" => [1.0, 1.0]),
        "the endpoint-only singleton fails to enclose the true square interval containing zero",
    ) do
        actual = IntervalArithmetic.interval(-1.0, 1.0)^2
        impostor = IntervalArithmetic.interval(1.0, 1.0)
        impostor_covers_actual = IntervalArithmetic.issubset_interval(actual, impostor)
        passed = !impostor_covers_actual && IntervalArithmetic.inf(actual) <= 0.0 && IntervalArithmetic.sup(actual) >= 1.0
        outcome(passed, Dict("actual_lower" => IntervalArithmetic.inf(actual), "actual_upper" => IntervalArithmetic.sup(actual), "impostor_covers_actual" => impostor_covers_actual))
    end

    boundary = run_case(
        "singleton interval boundary",
        "IntervalArithmetic.interval/IntervalArithmetic.inf/IntervalArithmetic.sup",
        Dict("domain" => [2.0, 2.0]),
        "a singleton interval has identical lower and upper bounds and remains guaranteed",
    ) do
        singleton = IntervalArithmetic.interval(2.0, 2.0)
        lower = IntervalArithmetic.inf(singleton)
        upper = IntervalArithmetic.sup(singleton)
        outcome(lower == 2.0 && upper == 2.0 && IntervalArithmetic.isguaranteed(singleton), Dict("lower" => lower, "upper" => upper, "width" => upper - lower, "guaranteed" => IntervalArithmetic.isguaranteed(singleton)))
    end

    stress = run_case(
        "4096 certified square enclosures",
        "IntervalArithmetic.interval/IntervalArithmetic.inf/IntervalArithmetic.sup/IntervalArithmetic.isguaranteed/Base.:^",
        Dict("interval_count" => 4_096, "domain" => [0.0, 1.0]),
        "every bounded subinterval square encloses both endpoint squares and remains guaranteed",
    ) do
        count = 4_096
        valid = true
        maximum_width = 0.0
        for index in 0:(count - 1)
            lower_input = index / count
            upper_input = (index + 1) / count
            enclosure = IntervalArithmetic.interval(lower_input, upper_input)^2
            lower = IntervalArithmetic.inf(enclosure)
            upper = IntervalArithmetic.sup(enclosure)
            valid &= lower <= lower_input^2
            valid &= upper >= upper_input^2
            valid &= IntervalArithmetic.isguaranteed(enclosure)
            maximum_width = max(maximum_width, upper - lower)
        end
        outcome(valid, Dict("interval_count" => count, "all_certified" => valid, "maximum_output_width" => maximum_width))
    end

    adjacent = run_case(
        "StaticArrays vector of certified coordinates",
        "StaticArrays.SVector/IntervalArithmetic.interval/Base.abs2/IntervalArithmetic.inf/IntervalArithmetic.sup",
        Dict("coordinate_intervals" => [[0.0, 0.5], [0.0, 0.5]]),
        "fixed-size interval coordinates yield a norm-square enclosure containing [0,0.5]",
    ) do
        vector = StaticArrays.SVector(
            IntervalArithmetic.interval(0.0, 0.5),
            IntervalArithmetic.interval(0.0, 0.5),
        )
        enclosure = sum(abs2, vector)
        lower = IntervalArithmetic.inf(enclosure)
        upper = IntervalArithmetic.sup(enclosure)
        passed = lower <= 0.0 && upper >= 0.5 && IntervalArithmetic.isguaranteed(enclosure)
        outcome(passed, Dict("vector_type" => string(typeof(vector)), "norm_square_lower" => lower, "norm_square_upper" => upper, "guaranteed" => IntervalArithmetic.isguaranteed(enclosure)))
    end

    demotion = run_case(
        "non-enclosing recovery demotion",
        "IntervalArithmetic.issubset_interval",
        Dict("true_enclosure" => [0.0, 1.0], "claimed_enclosure" => [1.0, 1.0]),
        "a claimed bound that omits zero is rejected by interval inclusion",
    ) do
        true_enclosure = IntervalArithmetic.interval(-1.0, 1.0)^2
        claimed_enclosure = IntervalArithmetic.interval(1.0, 1.0)
        rejected = !IntervalArithmetic.issubset_interval(true_enclosure, claimed_enclosure)
        outcome(rejected, Dict("rejected" => rejected, "actual_lower" => IntervalArithmetic.inf(true_enclosure), "actual_upper" => IntervalArithmetic.sup(true_enclosure)))
    end

    Dict(
        "qualified_api" => [
            "IntervalArithmetic.interval",
            "IntervalArithmetic.sin",
            "IntervalArithmetic.inf",
            "IntervalArithmetic.sup",
            "IntervalArithmetic.isguaranteed",
            "IntervalArithmetic.issubset_interval",
        ],
        "demotion_condition" => "demote if an invalid enclosure is accepted, singleton boundaries drift, certified stress loses guarantees, or StaticArrays interoperability fails",
        "positive" => positive,
        "negative" => negative,
        "boundary" => boundary,
        "stress" => stress,
        "adjacent" => adjacent,
        "demotion" => demotion,
    )
end


function package_probe()
    TOOL_ID == "jl_tensorkit" && return tensorkit_probe()
    TOOL_ID == "jl_pepskit" && return pepskit_probe()
    TOOL_ID == "jl_intervalarithmetic" && return intervalarithmetic_probe()
    error("unreachable tool id: $(TOOL_ID)")
end


function runtime_binding()
    project_data = isfile(ACTIVE_PROJECT) ? TOML.parsefile(ACTIVE_PROJECT) : Dict{String,Any}()
    direct_deps = sort!(collect(keys(get(project_data, "deps", Dict{String,Any}()))))
    forbidden_present = sort!(collect(intersect(Set(direct_deps), FORBIDDEN_BRIDGES)))
    manifest_path = isempty(ACTIVE_PROJECT) ? "" : joinpath(dirname(ACTIVE_PROJECT), "Manifest.toml")
    imports_pass = all(get(IMPORT_STATUS[name], "passed", false) === true for name in CONFIG["imports"])
    guard_pass = PROJECT_MATCH && STRICT_LOAD_PATH && isempty(forbidden_present) && imports_pass
    Dict(
        "runtime_id" => CONFIG["runtime_id"],
        "executable" => joinpath(Sys.BINDIR, "julia"),
        "runtime_version" => string(VERSION),
        "active_project" => ACTIVE_PROJECT,
        "expected_project" => EXPECTED_PROJECT,
        "project_match" => PROJECT_MATCH,
        "load_path" => copy(Base.LOAD_PATH),
        "julia_load_path_env" => get(ENV, "JULIA_LOAD_PATH", nothing),
        "strict_load_path" => STRICT_LOAD_PATH,
        "environment_policy" => "exact isolated Julia project; strict @:@stdlib load path; no installation; no Python bridge",
        "install_allowed" => false,
        "direct_dependencies" => direct_deps,
        "forbidden_bridge_dependencies" => forbidden_present,
        "project_sha256" => isfile(ACTIVE_PROJECT) ? sha256_file(ACTIVE_PROJECT) : nothing,
        "manifest_path" => manifest_path,
        "manifest_sha256" => isfile(manifest_path) ? sha256_file(manifest_path) : nothing,
        "imports" => IMPORT_STATUS,
        "passed" => guard_pass,
    )
end


function representative_sim(repo_root::String)
    source = normpath(abspath(@__FILE__))
    expected_source = normpath(abspath(joinpath(repo_root, SOURCE_RELATIVE)))
    passed = isdir(repo_root) && source == expected_source
    Dict(
        "passed" => passed,
        "source_path" => SOURCE_RELATIVE,
        "kind" => "new_bounded_integration_fixture",
        "reads_peer_result" => false,
        "standalone" => true,
        "observed" => Dict(
            "resolved_source" => source,
            "expected_source" => expected_source,
            "source_identity_match" => source == expected_source,
        ),
    )
end


function make_tool_call(row::Dict{String,Any})
    cases = Dict(name => row[name]["observed"] for name in ["positive", "negative", "boundary", "stress"])
    Dict(
        "tool" => CONFIG["package"],
        "qualified_api" => join(row["qualified_api"], "; "),
        "probe_function" => "package_probe/$(TOOL_ID)",
        "executed" => true,
        "load_bearing" => true,
        "raw_probe_recorded" => true,
        "input_object" => Dict(
            "positive" => row["positive"]["input_object"],
            "negative" => row["negative"]["input_object"],
            "boundary" => row["boundary"]["input_object"],
            "stress" => row["stress"]["input_object"],
        ),
        "output_object" => cases,
        "case_bindings" => Dict(
            name => Dict(
                "passed" => row[name]["passed"],
                "qualified_api" => row[name]["qualified_api"],
                "duration_ms" => row[name]["duration_ms"],
            )
            for name in ["positive", "negative", "boundary", "stress"]
        ),
        "positive_case" => row["positive"]["expected"],
        "negative_control" => row["negative"]["expected"],
        "boundary_case" => row["boundary"]["expected"],
        "stress_case" => row["stress"]["expected"],
        "demotion_condition" => row["demotion_condition"],
        "gates" => [
            "cases.positive.passed",
            "cases.negative.passed",
            "cases.boundary.passed",
            "cases.stress.passed",
            "demotion.passed",
            "adjacent_integrations[0].passed",
            "verdict.operational_pass",
        ],
    )
end


function main()
    started = time_ns()
    source_path = normpath(abspath(@__FILE__))
    runtime = runtime_binding()
    probe = package_probe()
    representative = representative_sim(CLI["repo_root"])

    case_names = ["positive", "negative", "boundary", "stress"]
    cases = Dict(name => probe[name] for name in case_names)
    adjacent = merge(
        copy(probe["adjacent"]),
        Dict("edge_id" => EDGE_ID, "case_id" => "julia_isolated_tensor_chain"),
    )
    demotion = merge(
        copy(probe["demotion"]),
        Dict("method" => "real public-API falsification control"),
    )

    import_pass = get(IMPORT_STATUS[CONFIG["package"]], "passed", false) === true
    operational_pass =
        runtime["passed"] === true &&
        import_pass &&
        all(cases[name]["passed"] === true for name in case_names) &&
        demotion["passed"] === true &&
        adjacent["passed"] === true &&
        representative["passed"] === true

    row = Dict{String,Any}(
        "tool_id" => TOOL_ID,
        "package" => CONFIG["package"],
        "bucket" => "current_isolated",
        "family" => CONFIG["family"],
        "runtime_id" => CONFIG["runtime_id"],
        "role" => "function_level_receipt",
        "qualified_api" => probe["qualified_api"],
        "import_status" => IMPORT_STATUS[CONFIG["package"]],
        "positive" => probe["positive"],
        "negative" => probe["negative"],
        "boundary" => probe["boundary"],
        "stress" => probe["stress"],
        "cases" => cases,
        "demotion_condition" => probe["demotion_condition"],
        "demotion" => demotion,
        "adjacent_integration_edge" => adjacent,
        "adjacent_integrations" => [adjacent],
        "integration_edge_ids" => [EDGE_ID],
        "representative_sim" => representative,
        "operational_pass" => operational_pass,
        "verdict" => Dict(
            "operational_pass" => operational_pass,
            "operational_status" => operational_pass ? "passed" : "red",
        ),
    )
    row["tool_calls"] = [make_tool_call(row)]

    receipt = Dict(
        "schema" => "codex_ratchet_julia_isolated_deep_stress_v1",
        "generated_at" => string(Dates.now(Dates.UTC)) * "Z",
        "classification" => "integration_diagnostic",
        "promotion_allowed" => false,
        "scientific_claim_proven" => false,
        "release_eligible" => false,
        "claude_bridge_used" => false,
        "reads_peer_result" => false,
        "install_attempted" => false,
        "receipt_semantics" => "isolated-package operational diagnostic only; a valid red row is preserved and proves no Ratchet, QIT, or downstream scientific claim",
        "tool_id" => TOOL_ID,
        "runtime_binding" => runtime,
        "source_binding" => Dict(
            "source_path" => SOURCE_RELATIVE,
            "source_sha256" => sha256_file(source_path),
            "repo_root" => CLI["repo_root"],
        ),
        "summary" => Dict(
            "row_count" => 1,
            "operational_pass_count" => operational_pass ? 1 : 0,
            "operational_red_count" => operational_pass ? 0 : 1,
            "all_operational_pass" => operational_pass,
            "trustworthy_receipt_written_even_if_red" => true,
            "duration_ms" => round((time_ns() - started) / 1.0e6; digits = 3),
        ),
        "rows" => [row],
    )

    write_json(CLI["out"], receipt)
    println("receipt=$(CLI["out"])")
    println("tool=$(TOOL_ID) runtime=$(CONFIG["runtime_id"]) operational_pass=$(operational_pass)")
    println("active_project=$(ACTIVE_PROJECT)")
    println("load_path=$(join(Base.LOAD_PATH, ':'))")
    return 0
end


exit_code = try
    main()
catch err
    println(stderr, "HARNESS FAILURE: ", sprint(showerror, err, catch_backtrace()))
    2
end
exit(exit_code)
