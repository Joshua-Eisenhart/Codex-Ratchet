using JSON3
using SHA

function emit(value)
    println(JSON3.write(value))
end

const COMPONENT_ENGINE_ID = "julia_diffeq"
const INTEGRATION_ID = "pysindy_to_julia_rate"
const EXACT_APIS = [
    "DifferentialEquations.ODEProblem",
    "DifferentialEquations.solve",
    "DifferentialEquations.Tsit5",
]

request = JSON3.read(read(stdin, String))
request_schema = String(request["schema"])
request_engine_id = String(request["engine_id"])

try
    @eval using DifferentialEquations
catch err
    emit(Dict(
        "schema" => "constraintbox.external-engine-unavailable.v1",
        "engine_id" => request_engine_id,
        "exact_api" => EXACT_APIS,
        "reason" => "DifferentialEquations import failed: $(sprint(showerror, err))",
        "pid" => getpid(),
    ))
    exit(3)
end

for name in (:ODEProblem, :solve, :Tsit5)
    if !isdefined(DifferentialEquations, name)
        emit(Dict(
            "schema" => "constraintbox.external-engine-unavailable.v1",
            "engine_id" => request_engine_id,
            "exact_api" => EXACT_APIS,
            "reason" => "DifferentialEquations.$(name) is unavailable",
            "pid" => getpid(),
        ))
        exit(3)
    end
end

rhs(u, p, t) = p * u

function solve_terminal(initial, rate, duration)
    problem = DifferentialEquations.ODEProblem(
        rhs,
        initial,
        (0.0, duration),
        rate,
    )
    solution = DifferentialEquations.solve(
        problem,
        DifferentialEquations.Tsit5();
        reltol=1.0e-10,
        abstol=1.0e-12,
        saveat=[duration],
    )
    return Float64(solution.u[end])
end

function runtime_receipt()
    return Dict(
        "julia_version" => string(VERSION),
        "package_version" => string(Base.pkgversion(DifferentialEquations)),
        "active_project" => string(Base.active_project()),
        "load_path" => collect(Base.LOAD_PATH),
    )
end

if request_schema == "constraintbox.external-engine-handoff-input.v1"
    if request_engine_id != INTEGRATION_ID
        error("integration worker input engine_id mismatch")
    end
    artifact_json = String(request["artifact_json"])
    declared_digest = String(request["artifact_sha256"])
    observed_digest = bytes2hex(SHA.sha256(codeunits(artifact_json)))
    if observed_digest != declared_digest
        error("identified-rate artifact digest mismatch")
    end
    artifact = JSON3.read(artifact_json)
    if String(artifact["schema"]) != "external-sim-estate.identified-rate-artifact.v1"
        error("identified-rate artifact schema mismatch")
    end
    if String(artifact["producer_engine_id"]) != "pysindy_identification"
        error("identified-rate artifact producer mismatch")
    end
    rate = Float64(artifact["identified_rate"])
    case = request["case"]
    initial = Float64(case["initial"])
    duration = Float64(case["duration"])
    terminal = solve_terminal(initial, rate, duration)
    emit(Dict(
        "schema" => "constraintbox.external-engine-integration-witness.v1",
        "integration_id" => INTEGRATION_ID,
        "exact_api" => EXACT_APIS,
        "observed" => Dict(
            "terminal" => terminal,
            "consumed_rate" => rate,
            "artifact_sha256" => observed_digest,
        ),
        "runtime" => runtime_receipt(),
        "pid" => getpid(),
    ))
    exit(0)
end

if request_schema != "constraintbox.external-engine-input.v1"
    error("unsupported worker input schema")
end
if request_engine_id != COMPONENT_ENGINE_ID
    error("component worker input engine_id mismatch")
end

case = request["case"]
rate = Float64(case["rate"])
initial = Float64(case["initial"])
duration = Float64(case["duration"])
boundary_rate = Float64(case["boundary_rate"])
boundary_initial = Float64(case["boundary_initial"])
boundary_duration = Float64(case["boundary_duration"])

terminal = solve_terminal(initial, rate, duration)
boundary_terminal = solve_terminal(
    boundary_initial,
    boundary_rate,
    boundary_duration,
)

emit(Dict(
    "schema" => "constraintbox.external-engine-witness.v1",
    "engine_id" => COMPONENT_ENGINE_ID,
    "exact_api" => EXACT_APIS,
    "observed" => Dict(
        "terminal" => terminal,
        "boundary_terminal" => boundary_terminal,
    ),
    "runtime" => runtime_receipt(),
    "pid" => getpid(),
))
