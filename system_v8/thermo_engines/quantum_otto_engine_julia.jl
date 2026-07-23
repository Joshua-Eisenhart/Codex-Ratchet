# Authoritative Julia leg for quantum_otto_engine -- QuantumOptics.jl.
# Carries the two isentropic strokes (time-dependent, non-commuting
# H(t) = (B(t)/2) sigma_z + (eps_max/2) sin(pi t/tau) sigma_x) via
# timeevolution.master_dynamic (no jump operators) at tight tolerance.
# Isochoric strokes use the same complete-thermalization idealization as the
# main sim (analytic Gibbs populations, hbar = k_B = 1). Emits one JSON line.
using QuantumOptics
using JSON

const b = SpinBasis(1//2)
const sz = sigmaz(b)
const sx = sigmax(b)
const P_up = projector(spinup(b))    # excited state, E = +B/2
const P_dn = projector(spindown(b))  # ground state,  E = -B/2

const B_HOT = 2.0; const B_COLD = 1.0
const T_HOT = 2.0; const T_COLD = 0.5
const EPS_MAX = 0.8
const TAU_IDEAL = 200.0
const TAU_FRICTION = 1.0

gibbs_excited_pop(B, T) = 1.0 / (1.0 + exp(B / T))

function stroke(p_exc_in, B_start, B_end, tau, eps_max)
    rho0 = p_exc_in * P_up + (1.0 - p_exc_in) * P_dn
    function f(t, rho)
        B = B_start + (B_end - B_start) * (t / tau)
        H = 0.5 * B * sz + 0.5 * eps_max * sin(pi * t / tau) * sx
        return H, [], []
    end
    _, rhot = timeevolution.master_dynamic([0.0, tau], rho0, f;
                                           reltol=1e-10, abstol=1e-12)
    rho_out = rhot[end]
    return real(expect(P_up, rho_out)), abs(rho_out.data[1, 2])
end

function cycle(tau, eps_max, p1, p3)
    p2, off2 = stroke(p1, B_HOT, B_COLD, tau, eps_max)
    p4, off4 = stroke(p3, B_COLD, B_HOT, tau, eps_max)
    q_in = B_HOT * (p1 - p4)
    q_out = B_COLD * (p2 - p3)
    w_net = q_in - q_out
    return Dict("p2" => p2, "p4" => p4, "off2" => off2, "off4" => off4,
                "q_in" => q_in, "q_out" => q_out, "w_net" => w_net,
                "eta" => w_net / q_in)
end

p1 = gibbs_excited_pop(B_HOT, T_HOT)
p3 = gibbs_excited_pop(B_COLD, T_COLD)
ideal = cycle(TAU_IDEAL, 0.0, p1, p3)
friction = cycle(TAU_FRICTION, EPS_MAX, p1, p3)

out = Dict(
    "engine" => "julia:QuantumOptics",
    "p1_excited_pop_hot_gibbs" => p1,
    "p3_excited_pop_cold_gibbs" => p3,
    "eta_ideal" => ideal["eta"],
    "w_net_ideal" => ideal["w_net"],
    "q_in_ideal" => ideal["q_in"],
    "q_out_ideal" => ideal["q_out"],
    "eta_friction" => friction["eta"],
    "w_net_friction" => friction["w_net"],
    "q_in_friction" => friction["q_in"],
    "q_out_friction" => friction["q_out"],
    "offdiag_friction_max" => max(friction["off2"], friction["off4"]),
)
println(JSON.json(out))
