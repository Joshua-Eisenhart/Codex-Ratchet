using JSON3
using DifferentialEquations

const INPUT_SCHEMA = "constraintbox.multiengine-worker-input.v1"

function require_keys(value, expected::Set{String}, label::String)
    value isa JSON3.Object || error(label * " must be an object")
    Set(String.(keys(value))) == expected || error(label * " keys mismatch")
end

function solve_terminal(growth::Float64, initial::Float64, t_final::Float64)
    function exponential_rhs!(du, u, p, t)
        du[1] = p * u[1]
    end
    problem = DifferentialEquations.ODEProblem(
        exponential_rhs!,
        [initial],
        (0.0, t_final),
        growth,
    )
    solution = DifferentialEquations.solve(
        problem,
        DifferentialEquations.Tsit5();
        abstol = 1.0e-12,
        reltol = 1.0e-12,
        save_everystep = false,
    )
    return solution.u[end][1]
end

function solve_severed(initial::Float64, t_final::Float64)
    function zero_rhs!(du, u, p, t)
        du[1] = 0.0
    end
    problem = DifferentialEquations.ODEProblem(
        zero_rhs!,
        [initial],
        (0.0, t_final),
        nothing,
    )
    solution = DifferentialEquations.solve(
        problem,
        DifferentialEquations.Tsit5();
        abstol = 1.0e-12,
        reltol = 1.0e-12,
        save_everystep = false,
    )
    return solution.u[end][1]
end

function main()
    source = JSON3.read(read(stdin, String))
    require_keys(
        source,
        Set(["schema", "lane", "binding", "challenge", "input_origin"]),
        "worker input",
    )
    String(source["schema"]) == INPUT_SCHEMA || error("worker input schema mismatch")
    String(source["lane"]) == "julia_diffeq" || error("worker lane mismatch")
    String(source["input_origin"]) == "controller-derived" || error("worker origin mismatch")
    binding = source["binding"]
    challenge = source["challenge"]
    require_keys(
        challenge,
        Set([
            "growth",
            "initial",
            "t_final",
            "boundary_initial",
            "wrong_offset",
        ]),
        "Julia challenge",
    )
    growth = Float64(challenge["growth"])
    initial = Float64(challenge["initial"])
    t_final = Float64(challenge["t_final"])
    boundary_initial = Float64(challenge["boundary_initial"])
    terminal = solve_terminal(growth, initial, t_final)
    boundary_terminal = solve_terminal(growth, boundary_initial, t_final)
    severed_terminal = solve_severed(initial, t_final)
    witness = Dict(
        "schema" => "constraintbox.multiengine-julia-witness.v1",
        "lane" => "julia_diffeq",
        "exact_apis" => [
            "DifferentialEquations.ODEProblem",
            "DifferentialEquations.solve",
            "DifferentialEquations.Tsit5",
        ],
        "binding" => binding,
        "input_origin" => "controller-derived",
        "reads_peer_output" => false,
        "pid" => getpid(),
        "runtime" => Dict(
            "julia_version" => string(VERSION),
            "active_project" => string(Base.active_project()),
            "load_path" => join(Base.LOAD_PATH, ":"),
            "diffeq_version" => string(Base.pkgversion(DifferentialEquations)),
        ),
        "observed" => Dict(
            "terminal" => terminal,
            "boundary_terminal" => boundary_terminal,
            "wrong_terminal" => terminal + Float64(challenge["wrong_offset"]),
            "severed_terminal" => severed_terminal,
        ),
    )
    JSON3.write(stdout, witness)
    write(stdout, '\n')
end

main()
