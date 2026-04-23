# Stochastic Thermodynamics: Formal Reference

Date: 2026-04-05
Status: Reference doc — the actual framework, not the system's application

---

## What It Is

Thermodynamics extended to individual fluctuating trajectories of mesoscopic
systems far from equilibrium. Defines work, heat, entropy along SINGLE
stochastic trajectories, not just ensemble averages. The second law emerges
as an inequality on averages; individual trajectories can transiently violate it.

Applies to: colloidal particles, molecular motors, single molecules,
biochemical networks — systems where energies are on order of kT.

---

## Fluctuation Theorems

Exact results holding arbitrarily far from equilibrium.

### Jarzynski Equality (1997)

  < exp(-βW) > = exp(-β ΔF)

W = work on system along single trajectory. ΔF = equilibrium free energy
difference. Angle brackets = average over all trajectories from initial
equilibrium.

Meaning: exponential average of nonequilibrium work exactly recovers
equilibrium free energy difference. By Jensen's inequality: <W> ≥ ΔF
(second law as inequality on average). Individual trajectories can have W < ΔF.

### Crooks Fluctuation Theorem (1999)

  P_F(W) / P_R(-W) = exp(β(W - ΔF))

Ratio of forward to reverse work distributions is exponential in dissipated
work. Crossing point P_F = P_R occurs at W = ΔF exactly.

### Detailed Fluctuation Theorem

  P(Σ_tot) / P(-Σ_tot) = exp(Σ_tot / k)

Trajectories producing positive entropy are exponentially more likely than
those producing equal negative entropy. Implies <Σ_tot> ≥ 0 (second law).

---

## Entropy Production Along Trajectories

System entropy along trajectory: s_sys(t) = -k ln p(x(t), t)
This is a fluctuating quantity depending on specific trajectory.

Medium entropy change: Δs_med = Q / T (heat to reservoir)

Total entropy production: Σ_tot = Δs_sys + Δs_med

Average: <Σ_tot> ≥ 0 (second law). Strict inequality for irreversible
processes. Equality only for quasistatic/reversible.

Most fundamental definition: entropy production along a trajectory equals
log-ratio of forward to time-reversed path probabilities:
  Σ_tot[x] = k · ln(P_F[x(t)] / P_R[x̃(t)])

---

## Information and Thermodynamics

### Landauer's Principle (1961)

Erasure of one bit costs at least kT ln 2 heat dissipated.
Experimentally verified (Bérut et al., Nature 2012).

### Szilard Engine (1929)

Single-molecule engine: measure which side particle is on (gain 1 bit),
attach load, extract work W = kT ln 2 via isothermal expansion.
Resolution: erasure of measurement record costs ≥ kT ln 2.

### Sagawa-Ueda Generalized Second Law (2010)

  <W> ≥ ΔF - kT · I

I = mutual information from measurement. Demon can extract extra work up
to kT times information gained. Erasure closes the books.

### Jarzynski with Feedback

  < exp(-βW) > = exp(-βΔF) · < exp(I) >

Information-theoretic extension for Maxwell-demon-type protocols.

---

## Nonequilibrium Steady States (NESS)

Stationary distribution with constant driving, nonzero probability currents,
constant entropy production. Detailed balance broken.

NESS: dp_ss/dt = 0, currents J ≠ 0, σ̇ > 0.

Housekeeping vs excess entropy production (Hatano-Sasa 2001):
  Σ_tot = Σ_hk + Σ_ex
Housekeeping: maintaining NESS. Excess: transitions between steady states.

### Connection to FEP

FEP's NESS is formally a NESS in the stochastic thermodynamics sense.
FEP's "surprise" = -ln p(x) = trajectory-level stochastic entropy s_sys/k.
Both frameworks: systems maintain low-entropy states through continuous
entropy export. FEP adds that biological systems do this by minimizing a
variational bound on surprise.

---

## Key Mathematical Machinery

### Langevin Equation (overdamped)

  γ dx/dt = -∂U/∂x + f(x) + √(2γkT) ξ(t)

γ = friction, U = potential, f = non-conservative force,
ξ(t) = Gaussian white noise.

### Fokker-Planck (probability level)

  ∂p/∂t = -∂J/∂x

J = probability current. Equilibrium: J=0. NESS: ∂J/∂x=0 but J≠0.

### Master Equation (discrete states)

  dp_i/dt = Σ_j [k_ij p_j - k_ji p_i]

Local detailed balance relates rates to energetics.

### Path Integral

  P[x(t)] ∝ exp(-A[x(t)])

A = Onsager-Machlup action.

---

## Thermodynamic Uncertainty Relations (TUR)

### Barato-Seifert (2015)

For any current J in a NESS:

  Var(J) / <J>² ≥ 2k / <Σ̇> · (1/τ)

Or: ε² · <Σ_tot>/k ≥ 2 where ε² = Var(J)/<J>²

Meaning: to measure/transmit a current with high precision, you must pay
thermodynamic cost (high entropy production). Fundamental trade-off between
precision and dissipation. Cannot have precise molecular clock, motor, or
sensor without dissipating energy.

Extensions: finite-time TUR (Horowitz-Gingrich 2020), multidimensional,
quantum, empirical (infer dissipation from precision measurements).

---

## Applications to Biology

### Molecular Motors
Kinesin, myosin, F1-ATPase. TUR constrains stepping precision.
Fluctuation theorems verified experimentally (Liphardt 2002, Collin 2005).

### Cellular Information Processing
Cost of sensing: chemotaxis accuracy bounded by dissipation.
Kinetic proofreading (Hopfield 1974): error rates below equilibrium limits
cost energy. ~kT ln(10) per decade of error reduction.

### Biochemical Networks
Gene regulatory networks as nonequilibrium information processors.
Circadian clocks, cell cycle: precision requires dissipation (TUR).

### Biological Systems as Maxwell Demons
Use information to maintain low-entropy states. Stochastic thermodynamics
provides exact accounting for the thermodynamic cost.

---

## Information Geometry Connection

### Fisher Information Metric

  g_ij = ∫ p(x;θ) [∂ln p/∂θ_i][∂ln p/∂θ_j] dx

Riemannian geometry on statistical manifolds. When θ = thermodynamic
control parameters, connects to thermodynamics.

### Thermodynamic Length (Crooks 2007)

  L = ∫ dt √(dλ/dt · g(λ) · dλ/dt)

Excess work bounded: <W_diss> ≥ L²/τ. Optimal protocol traverses at
constant thermodynamic speed. Geodesic in thermodynamic metric.

### Optimal Protocols

  dλ/dt ∝ [g(λ)]^{-1/2}

Move slowly where friction is high, quickly where low.

### Deeper Connections
- Thermodynamic cost of inference: Fisher info bounds precision (Cramér-Rao),
  TUR bounds precision by dissipation → cost of statistical inference
- Wasserstein distance / optimal transport: geometric lower bounds on
  dissipation (Dechant-Sasa 2019, Nakazato-Ito 2021)
- Thermodynamic speed limits: how fast a system can transition, bounded
  by entropy production and Fisher information

---

## Key People

| Person | Contribution |
|---|---|
| Udo Seifert | Unified framework (2005, 2012 review), trajectory entropy, TUR |
| Christopher Jarzynski | Jarzynski equality (1997) |
| Gavin Crooks | Crooks fluctuation theorem (1999), thermodynamic length |
| Massimiliano Esposito | Multipartite systems, information engines |
| Christian Van den Broeck | Efficiency at max power, TUR extensions |
| Juan Parrondo | Parrondo's paradox, information-thermodynamics |
| Takahiro Sagawa | Information-thermodynamics, generalized second law |
| Masahito Ueda | Feedback control thermodynamics |
| Andre Barato | TUR with Seifert |
| Ken Sekimoto | Stochastic energetics (1998) |

---

## Sources

Seifert (2012) Rep. Prog. Phys. 75, 126001. Jarzynski (2011) Annu. Rev.
Condens. Matter Phys. Crooks (1999, 2007). Esposito & Van den Broeck (2010)
PRL. Barato & Seifert (2015) PRL. Sagawa & Ueda (2010) PRL. Bérut et al.
(2012) Nature (Landauer verification). Liphardt et al. (2002) Science.
