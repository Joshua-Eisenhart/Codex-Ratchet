# Julia leg for carnot_engine — independent recompute, no echo.
#
# Recomputes the classical Carnot cycle headline scalars (eta, W_net, Qh, Qc)
# by trapezoid integration in Julia, and grounds the isothermal-stroke premise
# (working substance held at the bath's thermal populations) with QuantumOptics:
# a detailed-balance master-equation relaxation (timeevolution.master) whose
# populations must approach the closed-form Gibbs values at BOTH bath
# temperatures. Emits ONE JSON line on stdout for the controller.
using QuantumOptics
using JSON

const R = 8.314462618  # J / (mol K)
const N_MOL = 1.0
const GAMMA_GAS = 5.0 / 3.0
const GRID_N = 200_000
const TH = 400.0
const TC = 300.0
const V1 = 1.0e-3
const RATIO = 2.5

trapz(P, V) = 0.5 * sum((P[2:end] .+ P[1:end-1]) .* (V[2:end] .- V[1:end-1]))

function isothermal_work(T, Va, Vb)
    V = collect(range(Va, Vb; length=GRID_N))
    P = N_MOL * R * T ./ V
    return trapz(P, V)
end

function adiabatic_work(Vstart, Tstart, Vend)
    Pstart = N_MOL * R * Tstart / Vstart
    V = collect(range(Vstart, Vend; length=GRID_N))
    P = Pstart .* (Vstart ./ V) .^ GAMMA_GAS
    return trapz(P, V)
end

# --- classical Carnot cycle under the closure condition ---------------------
ratio_pow = (TH / TC)^(1.0 / (GAMMA_GAS - 1.0))
V2 = V1 * RATIO
V3 = V2 * ratio_pow
V4 = V1 * ratio_pow
W12 = isothermal_work(TH, V1, V2)
W23 = adiabatic_work(V2, TH, V3)
W34 = isothermal_work(TC, V3, V4)
W41 = adiabatic_work(V4, TC, V1)
Qh = W12
Qc = -W34
W_net = W12 + W23 + W34 + W41
eta = W_net / Qh
eta_analytic = 1.0 - TC / TH
W_net_analytic = N_MOL * R * (TH - TC) * log(RATIO)

# Degenerate control Th=Tc: a closed isothermal round trip admits zero net work.
W_degen = isothermal_work(350.0, V1, V2) + isothermal_work(350.0, V2, V1)

# --- thermal-contact premise via QuantumOptics master equation --------------
# Two-level probe, splitting DELTA (kelvin units, k_B = 1), detailed-balance
# jump rates gamma_up/gamma_down = exp(-DELTA/T); populations must relax to
# the Gibbs values along the closed-form exponential.
const DELTA = 150.0
const G_DOWN = 0.1
const T_RELAX = 200.0

function relax_divergences(Tbath)
    b = SpinBasis(1 // 2)
    g_up = G_DOWN * exp(-DELTA / Tbath)
    gam = G_DOWN + g_up
    p_ss = g_up / gam  # = 1/(1+exp(DELTA/T)) — the Gibbs excited population
    H = 0.5 * DELTA * sigmaz(b)
    J = [sigmam(b), sigmap(b)]
    rates = [G_DOWN, g_up]
    rho0 = 0.5 * dm(spinup(b)) + 0.5 * dm(spindown(b))
    tspan = collect(range(0.0, T_RELAX; length=21))
    tout, rhot = timeevolution.master(tspan, rho0, H, J;
                                      rates=rates, reltol=1e-10, abstol=1e-12)
    proj_up = dm(spinup(b))
    p_up = [real(expect(proj_up, r)) for r in rhot]
    closed_form = p_ss .+ (0.5 - p_ss) .* exp.(-gam .* tout)
    div_closed_form = maximum(abs.(p_up .- closed_form))
    p_gibbs = 1.0 / (1.0 + exp(DELTA / Tbath))
    div_gibbs_final = abs(p_up[end] - p_gibbs)
    return div_closed_form, div_gibbs_final
end

div_cf_th, div_gibbs_th = relax_divergences(TH)
div_cf_tc, div_gibbs_tc = relax_divergences(TC)
thermal_contact_ok = max(div_cf_th, div_cf_tc, div_gibbs_th, div_gibbs_tc) < 1e-6

out = Dict(
    "engine" => "julia:QuantumOptics+trapezoid",
    "eta_numeric" => eta,
    "eta_analytic" => eta_analytic,
    "W_net_J" => W_net,
    "W_net_analytic_J" => W_net_analytic,
    "Qh_J" => Qh,
    "Qc_J" => Qc,
    "carnot_ratio_residual" => abs(Qc / Qh - TC / TH),
    "degenerate_W_net_J" => W_degen,
    "gibbs_closed_form_div_Th" => div_cf_th,
    "gibbs_closed_form_div_Tc" => div_cf_tc,
    "gibbs_final_div_Th" => div_gibbs_th,
    "gibbs_final_div_Tc" => div_gibbs_tc,
    "thermal_contact_ok" => thermal_contact_ok,
)
println(JSON.json(out))
