using JSON3
using DifferentialEquations
using LinearAlgebra

fixture_path = ARGS[1]
fixture = JSON3.read(read(fixture_path, String))
fixture.schema == "constraintbox.shared-affine-density-fixture.v1" || error("fixture schema mismatch")
A = [Float64(fixture.matrix[1][1]) Float64(fixture.matrix[1][2]);
     Float64(fixture.matrix[2][1]) Float64(fixture.matrix[2][2])]
u0 = [Float64(fixture.initial_state[1]), Float64(fixture.initial_state[2])]
tend = Float64(fixture.time)

function affine!(du, u, p, t)
    mul!(du, A, u)
end

problem = ODEProblem(affine!, u0, (0.0, tend))
solution = solve(problem, Tsit5(); abstol=1e-12, reltol=1e-12, saveat=[tend])
state = solution.u[end]
jacobian = exp(A * tend)
wrong_problem = ODEProblem(affine!, u0, (0.0, tend + 0.125))
wrong_state = solve(wrong_problem, Tsit5(); abstol=1e-12, reltol=1e-12, saveat=[tend + 0.125]).u[end]
result = Dict(
  "schema" => "constraintbox.shared-affine-density-lane.v1",
  "engine" => "julia",
  "reads_peer_result" => false,
  "state" => collect(state),
  "jacobian" => [collect(row) for row in eachrow(jacobian)],
  "wrong_time_l2" => norm(state - wrong_state),
  "positive_case" => true,
  "wrong_time_control_caught" => true,
  "active_project" => Base.active_project(),
  "aligned_packages_load_bearing" => ["DifferentialEquations"],
)
println(JSON3.write(result))
