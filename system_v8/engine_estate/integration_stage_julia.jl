# Integration handoff — stage 3 (Julia, authoritative). Loads ONLY the Julia stack.
#
# Reads the jax-exported sweep result and runs the authoritative GKSL check:
# for each node i, integrate the single-qubit amplitude-damping master equation
#     drho/dt = gamma* D[sigma-] rho ,   rho0_i = diag(e_i, 1 - e_i)
# with tight solver tolerances to time T, then
#   (a) gate the integrated excited population against the analytic law
#       e_i * exp(-gamma* T)  == q_star_i from the jax handoff, and
#   (b) compute the chained manifold quantity
#       S_master = sum_i S_vN(rho_i(T))   (nats, von Neumann via QuantumOptics).

using JSON3, LinearAlgebra, Printf
using QuantumOptics

const HERE = @__DIR__
const OUTDIR = get(ENV, "ENGINE_ESTATE_INTEGRATION_DIR", joinpath(HERE, "results", "integration"))
const IN  = joinpath(OUTDIR, "handoff_jax.json")
const OUT = joinpath(
    OUTDIR,
    "handoff_julia.json",
)

up = JSON3.read(read(IN, String))
e  = Float64.(up.excitation_profile)
qs = Float64.(up.q_star)
T  = Float64(up.T)
gamma = Float64(up.gamma_star)
n  = length(e)

b = SpinBasis(1//2)
Pe = dm(spinup(b))                       # excited-state projector
H  = 0.0 * sigmaz(b)                     # pure dissipative sheet
J  = [sqrt(gamma) * sigmam(b)]
tspan = [0.0, T]

pops = zeros(n)
ents = zeros(n)
for i in 1:n
    rho0 = e[i] * dm(spinup(b)) + (1 - e[i]) * dm(spindown(b))
    _, rhot = timeevolution.master(tspan, rho0, H, J;
                                   reltol=1e-12, abstol=1e-14)
    rhoT = rhot[end]
    pops[i] = real(expect(Pe, rhoT))
    ents[i] = real(entropy_vn(rhoT))
end

S_master = sum(ents)
pop_dev = maximum(abs.(pops .- qs))      # integrated vs analytic-law handoff
S_jax_dev = abs(S_master - Float64(up.S_at_gamma_star))

@printf("[julia stage] gamma*=%.6f T=%.3f\n", gamma, T)
@printf("[julia stage] max|pop_master - q_star| = %.3e\n", pop_dev)
@printf("[julia stage] S_master = %.12f  |S_master - S_jax| = %.3e\n",
        S_master, S_jax_dev)

result = Dict(
    "stage" => "julia",
    "packet_id" => String(up.packet_id),
    "p0_digest" => String(up.p0_digest),
    "gamma_star" => gamma,
    "T" => T,
    "pops_master" => pops,
    "entropies_master" => ents,
    "S_master" => S_master,
    "max_pop_dev_vs_analytic" => pop_dev,
    "S_dev_vs_jax" => S_jax_dev,
    "gksl_law_check_pass" => pop_dev < 1e-9,
    "solver" => "QuantumOptics timeevolution.master reltol=1e-12 abstol=1e-14",
    "julia_version" => string(VERSION),
)
open(OUT, "w") do f
    JSON3.pretty(f, result)
end
println("[julia stage] wrote ", OUT)
