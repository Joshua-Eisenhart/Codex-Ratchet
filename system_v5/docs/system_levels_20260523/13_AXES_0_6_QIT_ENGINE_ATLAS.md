# Axes 0-6, QIT Engines, Flux, And Axis0 Atlas

Date: 2026-05-23

Status: working atlas. Source-grounded where cited, sim-checkable where
equations are explicit, and formal-scout-only where receipts exist. This file is
not a canonical admission of Axis0, flux, Xi, final physics, or engine ontology.

2026-05-23 quarantine note: any "current scout", "current fixture", "current
R5 boundary", pass, or fresh-rerun wording in this atlas is a stale receipt
anchor from the contaminated expansion window. Treat those passages as rerun
targets only until clean independent receipts exist.

## 0. Why This Atlas Exists

The system needs one place where the axes are not only labels.

The useful reading is:

```text
F01 + N01
  -> admissible constraint manifold
  -> finite QIT carrier
  -> Hopf/Weyl engine geometry
  -> terrain generator laws
  -> judging operator channels
  -> ordered token grammar
  -> engine charts
  -> open flux current families
  -> open Xi bridge
  -> open Axis0 kernel Phi_0
```

The bad reading is:

```text
Jung labels are the math.
Thermodynamic metaphors are the math.
Axis0 is already solved.
Flux is Axis3.
A6 up/down is automatically a physical channel.
```

This atlas keeps the layers separate.

## 1. Claim Ceiling

This file may say:

```text
the current source-backed axis equations are these
this equation is testable
this sim should check this equation
this candidate is open
this label is only a correlation layer
```

This file may not say:

```text
Axis0 is solved
Xi is solved
flux is admitted
engine type is fully derived
the physics model is final
the I-Ching/Jung/IGT labels alone admit QIT, game-theory, or physics truth
```

Status in one sentence:

```text
This atlas is a proposed/source-aligned working specification with local math
fixtures, not an admission packet.
```

## 2. Source Ladder

The constraint manifold starts from root admissibility, not from Jung, IGT, or
token names. IGT then matters as the source-backed stage grammar that maps the
axes into engine patterns; it is not the root substrate.

```text
1. F01_FINITUDE and N01_NONCOMMUTATION
2. admissible set C
3. admissible manifold M(C)
4. axis slices A_i : M(C) -> V_i
5. finite QIT carrier H = C^2, density space D(C^2)
6. spinor carrier S^3
7. Hopf projection S^3 -> S^2
8. Hopf tori T_eta
9. fiber/base loop laws
10. left/right Weyl sheets
11. engine runtime manifold
12. open bridge Xi : geometry/history -> rho_AB
13. open Phi_0(rho_AB) Axis0 kernel
```

Primary source paths:

```text
system_v5/READ ONLY Reference Docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md
system_v5/READ ONLY Reference Docs/JUNGIAN_FUNCTIONS_AND_IGT_EXPLICIT_MATH_GEOMETRY_MAP copy.md
system_v5/READ ONLY Reference Docs/terrain math.md
system_v5/READ ONLY Reference Docs/Weyl Flux.md
system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md
system_v5/ops/AXIS3_ENGINE_FLUX_PLACEMENT_EXPLORATORY_AUDIT_20260522.md
```

## 3. Root Constraints

### F01: Finitude

At root, no completed infinity is admissible.

Operationally:

```text
dim(H) < infinity
rho in D(H)
operator registry finite
path registry finite
probe family finite
receipt finite
claim scope finite
```

Rejected as primitive:

```text
continuous state space
infinite bath
unbounded path integral
unbounded hidden state family
unbounded witness
```

Smoothness, continuum geometry, field equations, or path integrals may appear
only after finite replacement, approximation, or limiting discipline has been
made explicit.

### N01: Noncommutation

At root, operator order is meaningful.

```text
AB != BA in general
A rho != rho A in general
[A, rho] != 0 in general
```

This is not "time" yet. It is algebraic order before temporal order.

Enforcement pattern:

```text
positive case: AB(rho) differs from BA(rho)
graveyard control: commuting A,B gives AB(rho) = BA(rho)
receipt: finite norm/readout gap above tolerance
```

## 4. Carrier Geometry

The current concrete carrier is a single finite qubit carrier, with later cuts
and networks built from tensor products of finite carriers.

Density state:

```text
rho = 1/2 (I + r_x sigma_x + r_y sigma_y + r_z sigma_z)
r in R^3, ||r|| <= 1
```

Hamiltonian:

```text
H_0 = n_x sigma_x + n_y sigma_y + n_z sigma_z
```

Spinor chart:

```text
psi_s(phi, chi; eta)
  = [
      exp(i(phi + chi)) cos eta,
      exp(i(phi - chi)) sin eta
    ]^T

s in {left, right}
eta in [0, pi/2]
phi, chi in [0, 2pi)
```

Density:

```text
rho(psi) = psi psi^dagger
```

Bloch image under the standard Pauli-y convention:

```text
r(phi, chi; eta)
  = (
      sin(2 eta) cos(2 chi),
     -sin(2 eta) sin(2 chi),
      cos(2 eta)
    )
```

Important correction:

```text
Some source text writes the y component with a plus sign.
The standard Pauli-y convention gives the minus sign.
Fixture:
  phi = 0
  chi = pi/4
  eta = pi/4
  rho = [[1/2, i/2], [-i/2, 1/2]]
  Tr(rho sigma_y) = -1
```

This should stay marked as a sim-caught source transcription correction until a
line-by-line source reconciliation is complete.

Hopf connection:

```text
A_Hopf = -i psi^dagger d psi
       = d phi + cos(2 eta) d chi
```

Fiber loop:

```text
gamma_f^s(u) = psi_s(phi_0 + u, chi_0; eta_0)
rho_f^s(u) = rho_f^s(0)
```

Lifted-base loop:

```text
gamma_b^s(u)
  = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)

A_Hopf(dot gamma_b^s) = 0
rho_b^s(u) changes with u
```

Weyl sheet realization:

```text
H_left  = +H_0
H_right = -H_0

rho_left  = psi_left psi_left^dagger
rho_right = psi_right psi_right^dagger

dot rho_left  = -i[H_left, rho_left]
dot rho_right = -i[H_right, rho_right]
```

In Bloch form:

```text
dot r_left  = +2 n x r_left
dot r_right = -2 n x r_right
```

The sheet sign is a Hamiltonian sign flip, not a metaphor.

## 5. Axis0: Entropy Drive And Cut-State Polarity

Status: active and open.

Axis0 is not one of the six structural lines. It is the drive or polarity seat
that cuts through them. The current atlas has two levels:

```text
chart-level Axis0 seat: Hopf torus latitude eta
bridge-level Axis0 candidate: Phi_0(rho_AB) after Xi is built
```

These must not be collapsed.

### 5.1 Chart-Level Seat

Hopf torus latitude:

```text
eta in [0, pi/2]
T_eta subset S^3
```

Orbit-averaged density:

```text
rho_bar(eta)
  = (1/(2pi)) int_0^(2pi) rho(chi, eta) d chi
  = diag(cos^2 eta, sin^2 eta)
```

Orbit entropy:

```text
S(rho_bar(eta))
  = -cos^2(eta) log(cos^2(eta))
    -sin^2(eta) log(sin^2(eta))
```

Derivative:

```text
dS/deta = -sin(2 eta) log(tan^2 eta)
```

Consequences:

```text
eta = 0 or pi/2 -> S = 0
eta = pi/4      -> S = log 2, Clifford torus maximum
```

Chart polarity bit:

```text
b_0 = sign(cos(2 eta)) = sign(r_z)
```

Current terrain partition:

```text
A0+ = {Ne, Ni}
A0- = {Se, Si}
```

The words "upper", "lower", "white", "black", "N", or "S" are chart aliases.
The enforceable object is the sign of `cos(2 eta)` or the sign of an admitted
cut-state functional.

### 5.2 Bridge-Level Axis0 Candidates

The bridge is open:

```text
Xi : geometry/history -> rho_AB
```

Once a finite cut state exists:

```text
rho_AB in D(H_A tensor H_B)
rho_A = Tr_B(rho_AB)
rho_B = Tr_A(rho_AB)
```

Candidate readouts:

```text
conditional entropy:
  S(A|B) = S(rho_AB) - S(rho_B)

coherent information:
  I_c(A -> B) = S(rho_B) - S(rho_AB) = -S(A|B)

mutual information:
  I(A:B) = S(rho_A) + S(rho_B) - S(rho_AB)

weighted shell cut:
  Phi_shell = sum_r w_r I_c(A_r -> B_r)
```

Best-tested-so-far simple signed candidate family, still unadmitted:

```text
Phi_candidate_Ic(rho_AB) = I_c(A -> B)
```

But this is not admitted as final. Prior static cut readouts have failed or
become nonrobust under matched controls. The next better surface is the
engine/Holodeck process cut, not only a static bipartite cut.

### 5.3 QIT-FEP Axis0 Candidate Space

Finite Kraus history:

```text
h = (a_1, ..., a_T)
K_h = K_T,a_T ... K_1,a_1
```

Finite path evidence:

```text
Z_path =
  sum_h Tr[
    (E_A tensor I_B)
    (K_h tensor I_B)
    rho_AB
    (K_h^dagger tensor I_B)
  ]
```

Unnormalized posterior:

```text
tau_AB =
  sum_h
    (sqrt(E_A) tensor I_B)
    (K_h tensor I_B)
    rho_AB
    (K_h^dagger tensor I_B)
    (sqrt(E_A) tensor I_B)
```

Normalized posterior:

```text
rho_AB|E = tau_AB / Tr(tau_AB)
```

Quantum variational free energy:

```text
F_Q(sigma_AB)
  = D(sigma_AB || tau_AB / Z_path) - log Z_path
```

Candidate family:

```text
Phi_1 = log Z_path
Phi_2 = I_c(A -> B)
Phi_3 = I(A:B)
Phi_4 = log Z_path + alpha I_c(A -> B)
Phi_5 = log Z_path + alpha I(A:B)
Phi_6 = -S(A|B)
Phi_7 = log-negativity
Phi_8 = smooth H_min/H_max term
Phi_9 = Renyi divergence term
```

Admission rule:

```text
No Axis0 candidate is canon until it beats matched controls, stress controls,
gauge controls, amplitude/spectrum scrambling, and process-history controls on
the same engine/Holodeck rows.
```

## 6. Axis1: Derived Terrain Branch Split

Status: active, derived, not primitive.

Partition:

```text
A1_open_or_isothermal  = {Se, Ni}
A1_closed_or_adiabatic = {Ne, Si}
```

QIT-explicit reading:

```text
open/isothermal  -> dissipator-dominant generator
closed/adiabatic -> Hamiltonian-dominant generator
```

Generator sketches:

```text
open:
  L = sum_k D[L_k] + epsilon (-i[H, .])

closed:
  L = -i[H, .] + epsilon sum_k D[M_k]
```

Distinguishing tests:

```text
open: generator eigenvalues have negative real parts
closed: generator is imaginary-axis dominated, up to epsilon correction
open: pure-state purity usually decays or relaxes
closed: pure unitary preserves purity and spectrum
```

Axis1 derivation:

```text
A1 = f(A0, A2)
```

One consistent parity convention:

```text
b_1 = -b_0 b_2
```

The important fact is not the sign convention alone. It is that the terrain
square is overconstrained by A0 and A2; A1 is not a freely chosen root bit.

Terrain square:

```text
                 A2 direct/expansion       A2 conjugated/compression
A1 open          Se = A0-                  Ni = A0+
A1 closed        Ne = A0+                  Si = A0-
```

Common failure:

```text
A0+ intersect direct = Ne, not Se.
```

## 7. Axis2: Direct Vs Conjugated Frame

Status: active, locked.

Partition:

```text
A2 direct/expansion       = {Se, Ne}
A2 conjugated/compression = {Ni, Si}
```

Direct frame:

```text
rho_tilde = rho
dot rho = L(rho)
```

Conjugated frame:

```text
rho_tilde = V_s^dagger rho V_s
V_s(u) = exp(-i H_s u)
K = i V_s^dagger dot V_s

dot rho_tilde =
  V_s^dagger L(V_s rho_tilde V_s^dagger) V_s
  - i[-K, rho_tilde]
```

Weyl sheet realization:

```text
H_left  = +H_0
H_right = -H_0
```

Native operator assignment:

```text
direct frame       -> Se, Ne -> Ti, Fi
conjugated frame   -> Ni, Si -> Te, Fe
```

This is the structural reason each major runtime pair contains one direct-frame
native operator and one conjugated-frame native operator.

## 8. Axis3: Fiber Vs Lifted-Base Path Class

Status: active, locked at geometry level.

Axis3 is not flux and not chirality. The source-level geometry anchor is
fiber/base.

Fiber path:

```text
gamma_f^s(u) = psi_s(phi_0 + u, chi_0; eta_0)
rho_f^s(u) = rho_f^s(0)
Y_in psi_s = partial_phi psi_s
```

Lifted-base path:

```text
gamma_b^s(u) =
  psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)

rho_b^s(u) = |gamma_b^s(u)><gamma_b^s(u)|
Y_out psi_s = (-cos(2 eta) partial_phi + partial_chi) psi_s
A_Hopf(dot gamma_b^s) = 0
```

Chart-relative inner/outer:

```text
Engine type 1: inner = fiber, outer = lifted base
Engine type 2: inner = lifted base, outer = fiber
```

Critical qualifier:

```text
The A6 rule b_6 = -b_0 b_3 uses chart-role A3 (inner/outer), not raw
geometric fiber/base. Under raw fiber/base, the parity flips between engine
types.
```

This qualifier should travel with every A3/A6 runtime row.

## 9. Axis4: Loop-Order Family

Status: active, engine-level or runtime-family-level, not a primitive root.

Composition convention:

```text
(A o B)(rho) = A(B(rho))
rightmost map acts first
```

Order families:

```text
Phi_deductive = U o E o U o E
Phi_inductive = E o U o E o U
```

where:

```text
U = unitary / rotation branch = {Fi, Fe}
E = non-unitary / dephasing branch = {Ti, Te}
```

Runtime correlation:

```text
deductive -> FeTi family
inductive -> TeFi family
```

Two label layers must stay visible:

```text
Jung pair-order layer: TiFe vs FeTi
IGT/runtime layer:    FeTi vs TeFi
```

Witness:

```text
Delta_4(rho) = Phi_deductive(rho) - Phi_inductive(rho)
||Delta_4||_P = max_{rho in finite probes P} ||Delta_4(rho)||_F
```

Falsifier:

```text
If Phi_deductive(rho) = Phi_inductive(rho) for every admissible rho and every
active readout, A4 has no runtime content for that row.
```

## 10. Axis5: Operator Family

Status: active, locked.

Partition:

```text
dephasing / pinching = {Ti, Te}
rotation / unitary   = {Fi, Fe}
```

### Ti: z-basis dephasing

```text
P_0 = 1/2(I + sigma_z)
P_1 = 1/2(I - sigma_z)

Ti_q(rho) =
  (1 - q_1) rho + q_1(P_0 rho P_0 + P_1 rho P_1)

L_Ti(rho) =
  (kappa_1/2)(sigma_z rho sigma_z - rho)
```

Bloch action:

```text
(x, y, z) -> ((1 - q_1)x, (1 - q_1)y, z)
```

Fixed algebra:

```text
Fix(Ti) = span{I, sigma_z}
```

Lyapunov contraction:

```text
D_z(rho) = (x^2 + y^2)/2
D_z(Ti_t rho) = exp(-2 kappa_1 t) D_z(rho)
```

### Te: x-basis dephasing

```text
Q_+ = 1/2(I + sigma_x)
Q_- = 1/2(I - sigma_x)

Te_q(rho) =
  (1 - q_2) rho + q_2(Q_+ rho Q_+ + Q_- rho Q_-)

L_Te(rho) =
  (kappa_2/2)(sigma_x rho sigma_x - rho)
```

Bloch action:

```text
(x, y, z) -> (x, (1 - q_2)y, (1 - q_2)z)
```

Fixed algebra:

```text
Fix(Te) = span{I, sigma_x}
```

Lyapunov contraction:

```text
D_x(rho) = (y^2 + z^2)/2
D_x(Te_t rho) = exp(-2 kappa_2 t) D_x(rho)
```

### Fi: x-axis Hamiltonian rotation

```text
U_x(theta) = exp(-i theta sigma_x/2)
Fi_theta(rho) = U_x(theta) rho U_x(theta)^dagger

L_Fi(rho) = -i[(omega_3/2) sigma_x, rho]
```

Bloch action:

```text
x' = x
y' = y cos theta - z sin theta
z' = y sin theta + z cos theta
```

### Fe: z-axis Hamiltonian rotation

```text
U_z(phi) = exp(-i phi sigma_z/2)
Fe_phi(rho) = U_z(phi) rho U_z(phi)^dagger

L_Fe(rho) = -i[(omega_4/2) sigma_z, rho]
```

Bloch action:

```text
x' = x cos phi - y sin phi
y' = x sin phi + y cos phi
z' = z
```

### Operator Class Properties

| Property | Dephasing `{Ti, Te}` | Rotation `{Fi, Fe}` |
| --- | --- | --- |
| Channel class | unital pinching CPTP semigroup | inner automorphism |
| Generator | self-adjoint negative on transverse subspace | skew-adjoint Hamiltonian derivation |
| Spectrum of rho | not preserved | preserved |
| Entropy | non-decreasing for qubit unital dephasing | preserved |
| Purity | decreases or stays fixed | preserved |
| Reversibility | irreversible semigroup | reversible group |
| Fixed algebra | non-trivial | only spectral invariants |

Correction:

```text
"All Lindbladians increase entropy" is false.
Amplitude damping at zero temperature can decrease entropy by pulling a mixed
state toward a pure ground state.
```

Any role word such as "gradient", "ascent", "descent", "projector", or
"filter" must name the functional being changed.

## 11. Axis6: Precedence And Algebraic Action Side

Status: active, derived, two-layer audit required.

Derivation rule:

```text
b_6 = -b_0 b_3
```

Qualifier:

```text
b_3 here means chart inner/outer, not raw fiber/base.
```

Token precedence:

```text
up   = operator written first
down = terrain written first
```

Up tokens:

```text
TiSe, TiNe, FeSi, FeNi, TeNi, TeSi, FiNe, FiSe
```

Down tokens:

```text
SeTi, NeTi, SiFe, NiFe, NiTe, SiTe, NeFi, SeFi
```

QIT primitive actions:

```text
L_A(rho) = A rho
R_A(rho) = rho A
[A, rho] = L_A(rho) - R_A(rho)
```

For:

```text
A = a . sigma
rho = 1/2(I + r . sigma)
```

Commutator and gap:

```text
[A, rho] = i(a x r) . sigma
gap_A(rho) = ||A rho - rho A||_F = sqrt(2) ||a x r||
```

Specific fixtures:

```text
gap_sigma_x(rho) = sqrt(2) sqrt(y^2 + z^2)
gap_sigma_z(rho) = sqrt(2) sqrt(x^2 + y^2)
```

These match the transverse components collapsed by Te and Ti.

Liouville convention:

```text
vec(A rho B) = (B^T tensor A) vec(rho)
L_A ~ I tensor A
R_A ~ A^T tensor I
ad_H = L_H - R_H
-i[H, rho] = -i(L_H - R_H) vec(rho)
```

Physical closure taxonomy:

| Closure | Formula | Status |
| --- | --- | --- |
| commutator | `-i(A rho - rho A)` | Hermiticity/trace preserving generator iff `A = A^dagger` |
| anti-commutator | `-1/2(M rho + rho M)` | not trace preserving alone |
| Kraus sandwich | `sum_j K_j rho K_j^dagger` | CPTP iff `sum_j K_j^dagger K_j = I` |
| GKSL semigroup | `sum_j D[L_j](rho) + Hamiltonian` | Markovian CPTP |
| unitary adjoint | `U rho U^dagger` | reversible CPTP |

A runtime row claiming A6 is load-bearing must record:

```text
axis6_token_precedence in {operator_first, terrain_first}
axis6_action_side in {left, right, both}
closure_type in {commutator, Kraus, GKSL, unitary_adjoint, other}
C_up(rho) != C_down(rho) for at least one finite fixture and readout
```

## 12. Token Grammar

The 16 ordered tokens come from:

```text
4 topologies x 2 operator families x 2 precedence signs
```

Table:

| Topology | dephasing up | dephasing down | rotation up | rotation down |
| --- | --- | --- | --- | --- |
| Se | TiSe | SeTi | FiSe | SeFi |
| Ne | TiNe | NeTi | FiNe | NeFi |
| Ni | TeNi | NiTe | FeNi | NiFe |
| Si | TeSi | SiTe | FeSi | SiFe |

Projection identity:

```text
A1 x A2 -> 4 topologies
A5      -> 2 operator families
A6      -> 2 precedence signs
4 x 2 x 2 = 16 ordered tokens
```

Therefore:

```text
A1 x A2 x A5 x A6 identifies each ordered token uniquely.
```

But:

```text
A3 x A4 x A5 x A6 gives only 8 paired signatures.
```

Each such signature contains two tokens. So `(A3, A4, A5, A6)` is too coarse to
identify a token.

## 13. IGT Charts And Engine Strategy Grammar

Status: generative stage-grammar layer for engine patterns. Not root math and
not a substitute for QIT enforcement.

IGT is stronger than a decorative label overlay: it maps every axis into the
engine-stage grammar and is where the Type1/Type2 engine pattern is generated.
The constraint is that its patterns become admissible only after translation
into finite channels, density states, path histories, and readouts.

Governing split:

```text
IGT     = stage grammar: WIN/LOSE/win/lose, same-sign vs mixed, outer/inner, first/second asymmetry
Jung    = operator grammar: ordered pair tokens and operator-pair names
I Ching = 64-schedule index scaffold
QIT     = load-bearing channel, density, entropy, and path math
```

Do not let the IGT chart redefine operator formulas, QIT closure, or axis
admission.

### 13.1 IGT Quadrant Lock

Source-backed quadrant table:

```text
admission_status = not_admitted_source_aligned_stage_grammar_only
This table records current IGT chart grammar. It is not QIT substrate and does
not promote final IGT, psychology, game theory, Axis0, Xi, flux, or physics.
Each row still needs finite channel/path/readout receipts before it can carry
runtime evidence.
```

| Topology | IGT quadrant | T-strategy | F-strategy | T1 major | T1 minor | T2 major | T2 minor |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ne | WinLose | NeTi | FiNe | NeTi -> WIN | FiNe -> lose | NeFi -> LOSE | TiNe -> win |
| Si | WinWin | SiTe | FeSi | FeSi -> WIN | SiTe -> win | TeSi -> WIN | SiFe -> win |
| Se | LoseWin | TiSe | SeFi | TiSe -> LOSE | SeFi -> win | FiSe -> WIN | SeTi -> lose |
| Ni | LoseLose | TeNi | NiFe | NiFe -> LOSE | TeNi -> lose | NiTe -> LOSE | FeNi -> lose |

Interpretation:

```text
uppercase WIN/LOSE = major/outer-stage result marker
lowercase win/lose = minor/inner-stage result marker
T-strategy and F-strategy are IGT chart grammar, not independent QIT operators
```

This table is important because it records how the Type1/Type2 engine rows
surface as IGT stage grammar without letting IGT become the substrate.

### 13.2 Axis Correlation Layer

| Axis | Jung layer | IGT layer | I-Ching scaffold |
| --- | --- | --- | --- |
| A0 | Ni/Ne vs Si/Se | WinLose/LoseLose vs LoseWin/WinWin | drive through 64-slot space, not a structural line |
| A1 | Se/Ni vs Ne/Si | LoseWin/LoseLose vs WinLose/WinWin | line 5 |
| A2 | Se/Ne vs Si/Ni | LoseWin/WinLose vs WinWin/LoseLose | line 6 |
| A3 | inner vs outer token set | inner vs outer token set | line 3 |
| A4 | TiFe vs FeTi pair-order layer | FeTi vs TeFi runtime loop-family layer | line 4 |
| A5 | FeFi vs TiTe | rotation-class vs dephasing-class tokens | line 2 |
| A6 | judging-first vs perceiving-first | up vs down ordered tokens | line 1 |

Two warnings:

```text
A3's chart layer says inner/outer, but the geometry anchor is fiber/base.
A4 has two label layers: Jung pair-order and IGT/runtime loop-family.
```

### 13.3 IGT Is Generative But Not QIT Substrate

IGT charts are useful because they generate the engine pattern surface:

```text
generating the Type1/Type2 engine stage pattern
mapping all axes into one strategy grammar
stage grammar
engine-row sanity checks
outer/inner result polarity
same-sign vs mixed quadrant tracking
64-schedule indexing
human-facing chart continuity
finite game-theory simulations
```

That is stronger than "decorative correlation." The guardrail is narrower:
IGT supplies stage grammar, symmetry, quadrant structure, and strategy sets.
QIT supplies the admissible carrier, channels, entropies, path histories,
controls, and proofs.

IGT charts are not allowed to directly:

```text
define a density state
define a CPTP channel
close Xi
admit Axis0
admit flux
replace A3 fiber/base geometry
replace A6 left/right action-side checks
```

### 13.4 IGT As A Finite Game-Theory Candidate

The new game-theory reading is admissible as a scout target if it follows the
constraint discipline:

```text
character = finite Type1 or Type2 engine
strategy set per character = 8 source-backed engine strategies
strategy = finite CPTP channel/readout row
payoff = named finite QIT functional, not primitive utility
interaction = noncommuting finite composition, with commuting controls
```

Type1 strategy set:

```text
TiSe, SeFi, NeTi, FiNe, NiFe, TeNi, FeSi, SiTe
```

Type2 strategy set:

```text
FiSe, SeTi, TeSi, SiFe, NiTe, FeNi, NeFi, TiNe
```

The union is the 16-token registry. The current strategy-registry scout is:

```text
system_v5/ops/formal_scouts/sim_igt_engine_game_theory_strategy_probe.py
```

It tests:

```text
Type1 has 8 strategies
Type2 has 8 strategies
the union covers 16 ordered tokens
characters can instantiate either engine type
the Type1-vs-Type2 payoff matrix is finite and nonconstant
payoff uses a named QIT readout, not primitive utility
noncommuting order gaps contribute to the game readout
commuting/identity control collapses order-gap content
```

This does not admit final IGT game theory. It opens the correct sim lane.

The first population/Holodeck game scout is:

```text
system_v5/ops/formal_scouts/sim_igt_engine_population_holodeck_game_probe.py
```

It tests:

```text
six finite Type1/Type2 characters
8 strategies per character
strategy weights derived from named QIT readouts
finite Holodeck world-memory density update
adaptive strategy readout differs from uniform evaluation
memory-erasure and commuting/identity controls collapse the intended content
```

This is the first runnable IGT-as-game-theory lane. It still does not admit
final game theory, Axis0, Xi, flux, psychology, cognition, economics, or
physics.

### 13.5 QIT Versions Of Classical Extrema Policies

The classical policy names become exact finite operators over a named QIT
readout matrix `M`.

```text
maximax(M) = argmax_i max_j M_ij
maximin(M) = argmax_i min_j M_ij
minimax(M) = argmin_i max_j M_ij
minimin(M) = argmin_i min_j M_ij
```

The operator is exact; the meaning depends on the readout. If `M` is a reward
or affordance matrix, the max policies behave like reward-seeking policies. If
`M` is an exposure, disturbance, entropy-production, or commitment matrix, the
min policies become powerful preservation policies.

The important IGT correction:

```text
minimin is not "weak utility" by default.
minimin over exposure = lowest low-bound commitment / disturbance selector.
```

The current extrema-policy scout is:

```text
system_v5/ops/formal_scouts/sim_igt_qit_game_extrema_policy_probe.py
```

It tests:

```text
the four extrema policies as exact finite matrix selectors
payoff matrix = target overlap + order-gap contribution - entropy cost
exposure matrix = disturbance + entropy cost - order-gap content
constant-matrix control collapses policy content
minimin over exposure preserves nonzero order-gap and future optionality
```

In the current fixture, minimin over exposure selects `NeTi`, and the payoff
maximax selector also selects `NeTi`. That is useful evidence for the owner
reading: minimin can align low exposure with strong QIT payoff. It is not final
admission; it is a formal scout result for this readout fixture.

The current science-method/Holodeck coupling scout is:

```text
system_v5/ops/formal_scouts/sim_holodeck_science_method_igt_qit_fep_probe.py
```

It tests:

```text
observe/hypothesize/predict/experiment/update/falsify/replicate
finite hypothesis bank over target effects
IGT minimin-over-exposure as a low-exposure experiment policy prefix
Holodeck QIT-FEP posterior update
wrong-hypothesis falsification
three-fixture replication grid
commuting-order control collapse
scalar entropy rejection
```

Current boundary from that scout:

```text
science-method loop = executable as a formal scout
minimin exposure token = NeTi in the current fixture
wrong-memory stress = did NOT prove memory-specific load-bearing
final Holodeck / science method / IGT / Axis0 / Xi / flux / physics = not admitted
```

The R5 multiseed follow-through scout is:

```text
system_v5/ops/formal_scouts/sim_holodeck_science_method_multiseed_policy_grid_probe.py
```

It tests:

```text
12 bounded world-memory seeds
16 ordered token rows
24 policy rows including extrema selectors and all-token grid rows
memory-erased / product-memory / wrong-memory / shuffled-memory controls
constant policy matrix degeneracy
commuting-order collapse
scalar entropy rejection
```

Current R5 boundary:

```text
Holodeck truth-selection loop survives the grid.
All 16 tokens select H_true_target.
Therefore IGT policy specificity is not admitted by this scout.

minimin(exposure) = NeTi
payoff maximax = NeTi
Therefore minimin is not unique in this fixture.

Memory controls still select H_true_target.
Therefore memory-specific truth selection is not admitted.

Live entangled memory beats controls only on active-update margin:
  delta over best control ~= 0.01033
So memory remains a candidate active-margin contributor, not a proven truth
selection requirement.
```

## 14. Terrain Laws

The terrain layer is generator/vector-field math, not token grammar.

GKSL dissipator:

```text
D[L](rho) = L rho L^dagger - 1/2(L^dagger L rho + rho L^dagger L)
```

### 14.1 Se: Funnel / Cannon

Generator:

```text
X_Se,s(rho) =
  lambda_Se,s sum_{j=x,y,z} D[sigma_j](rho)
  - i epsilon_Se,s [H_s, rho]
```

QIT class:

```text
Pauli-isotropic depolarizing semigroup with sheet-Hamiltonian perturbation.
```

Bloch dynamics in pure dissipator limit:

```text
dot r = -4 lambda r
fixed point: r -> 0, rho -> I/2
```

### 14.2 Ne: Vortex / Spiral

Generator:

```text
X_Ne,s(rho) =
  -i[H_s, rho] + epsilon_Ne,s sum_k D[M_k](rho)
```

QIT class:

```text
Hamiltonian inner automorphism with weak dissipator perturbation.
```

Bloch dynamics in pure Hamiltonian limit:

```text
dot r = +/- 2 n x r
||r|| preserved
S(rho) preserved
```

### 14.3 Ni: Pit / Source

Source convention:

```text
sigma_- = [[0, 0], [1, 0]]   fixed point z = -1
sigma_+ = [[0, 1], [0, 0]]   fixed point z = +1
```

Generators:

```text
X_Ni,left(rho) =
  gamma_Ni,left D[sigma_-](rho) - i epsilon_Ni,left [H_left, rho]

X_Ni,right(rho) =
  gamma_Ni,right D[sigma_+](rho) - i epsilon_Ni,right [H_right, rho]
```

QIT class:

```text
Amplitude damping / T1 relaxation with sheet-Hamiltonian perturbation.
```

Bloch dynamics:

```text
D[sigma_-]:
  dot x = -x/2
  dot y = -y/2
  dot z = -(1 + z)

D[sigma_+]:
  dot x = -x/2
  dot y = -y/2
  dot z = 1 - z
```

This can decrease entropy. It is the canonical correction to any sloppy
"open means entropy increases" statement.

### 14.4 Si: Hill / Citadel

Generator:

```text
X_Si,s(rho) =
  -i[K_s, rho]
  + kappa_s(P_+^s rho P_+^s + P_-^s rho P_-^s - rho)

P_pm^s = 1/2(I +/- m_s . sigma)
[K_s, P_pm^s] = 0
```

QIT class:

```text
projector dephasing along m_s . sigma with commuting Hamiltonian rotation.
```

Bloch dynamics:

```text
dot r = 2 omega (m x r) - kappa (r - (m . r)m)
```

The component along `m` is preserved; transverse components decay.

## 15. Operators Versus Terrains

The four judging operators are maps on density matrices. They are not
topologies.

| Operator | Channel class | Generator | Native frame |
| --- | --- | --- | --- |
| Ti | z-basis dephasing | `(k1/2)(sigma_z rho sigma_z - rho)` | direct: Se, Ne |
| Te | x-basis dephasing | `(k2/2)(sigma_x rho sigma_x - rho)` | conjugated: Ni, Si |
| Fi | x-axis rotation | `-i[(omega3/2)sigma_x, rho]` | direct: Se, Ne |
| Fe | z-axis rotation | `-i[(omega4/2)sigma_z, rho]` | conjugated: Ni, Si |

Layer separation:

```text
terrain math  = generator/vector-field laws
operator math = channel/superoperator laws
token math    = ordered grammar
axis math     = slice/readout over M(C)
engine math   = charted composition of terrain placements and operator tokens
```

Do not collapse these layers.

## 16. Engine Charts

There are two current engine type charts.

### 16.1 Engine Type 1

```text
admission_status = not_admitted_source_aligned_engine_chart_only
Rows below are current chart grammar to be tested. They are not final engine
ontology and not a substitute for per-row QIT channel/path controls.
```

```text
outer loop = deductive order on lifted base
inner loop = inductive order on fiber
```

Rows:

| Topology | Outer | Inner |
| --- | --- | --- |
| Se | TiSe | SeFi |
| Ne | NeTi | FiNe |
| Ni | NiFe | TeNi |
| Si | FeSi | SiTe |

### 16.2 Engine Type 2

```text
admission_status = not_admitted_source_aligned_engine_chart_only
Rows below are current chart grammar to be tested. They are not final engine
ontology and not a substitute for per-row QIT channel/path controls.
```

```text
outer loop = inductive order on fiber
inner loop = deductive order on lifted base
```

Rows:

| Topology | Outer | Inner |
| --- | --- | --- |
| Se | FiSe | SeTi |
| Si | TeSi | SiFe |
| Ni | NiTe | FeNi |
| Ne | NeFi | TiNe |

Triple-swap symmetry:

```text
fiber       <-> lifted base
deductive   <-> inductive
outer role  <-> inner role
```

Engine type is not recoverable from `(A3, A4)` alone. At minimum, a runtime row
needs:

```text
engine_type
chart_loop_role
path_class
loop_order_family
sheet_sign or sheet role
operator_family
token_precedence
action_side
```

Flux may help explain the missing determinant, but flux is not admitted yet.

## 17. Flux Status

Flux is not a root and not currently an admitted axis. It is an open derived
current/binding candidate family.

Candidate families:

```text
J_geom   = geometric transport current
J_chi    = chirality or sheet-separation current
J_Bloch  = differential Bloch current
J_ent    = entropy/information current
J_cut    = cut-state information current
J_axis   = axis-internal readout current
J_cross  = coupled multi-axis observable
```

Possible placements still open:

```text
manifold-level basin binding
engine-level current
path/loop current
cross-axis current
Axis0 companion current
```

Forbidden shortcut:

```text
Flux = Axis3
```

Axis3 is fiber/base path class. Flux may read changes along fiber/base and
engine loops, but it is not the path class itself.

## 18. QIT-FEP And Holodeck Process

Classical FEP tends to import continuous states, probability densities,
Gaussian recognition densities, Markov blankets, and primitive time.

The QIT-aligned replacement is:

```text
finite density states
finite CPTP instruments
finite Kraus histories
finite path sums
quantum relative entropy
finite cut/process states
```

Holodeck engineering translation:

| Holodeck word | QIT/CS object |
| --- | --- |
| world model | finite density/process state |
| cue | finite compressed reference/cut state |
| projection | finite instrument/action family |
| perception/error | finite POVM/effect readout |
| update | posterior channel |
| plan | finite path comparison |
| surprise/free energy | relative-entropy/path-evidence functional |

Current QIT-FEP process target:

```text
engine chart row
  -> terrain generator
  -> operator token
  -> finite Kraus history
  -> rho_AB posterior
  -> Axis0 candidate family
  -> matched controls
  -> stress controls
```

The missing hard object remains:

```text
Xi : geometry/history -> rho_AB
```

Until Xi is closed, every Axis0 readout is a candidate family.

## 19. Allowed Entropies

Allowed when finite, density-native or instrument-derived, gauge-safe, and
capacity-bounded:

```text
S(rho) = -Tr rho log rho
S(rho_A)
S(A|B)
I_c(A -> B)
I(A:B)
I(A:C|B)
D(rho || sigma)
sandwiched Renyi divergences
smooth min/max entropies
log-negativity
concurrence for two-qubit cuts
finite path entropy over p_h
```

Not allowed as primitive:

```text
continuous differential entropy over R^n
classical hidden-state Markov entropy
infinite bath entropy
unbounded path-integral entropy
raw tensor-index entropy
```

Tensor networks are allowed as computational tools:

```text
MPS
MPO
PEPS
process tensors
quantum combs
finite tensor contractions
```

But raw tensor indices are not ontology.

## 20. Enforceability Rules

Every axis, terrain, operator, flux, or Axis0 claim needs:

```text
1. exact object
2. finite fixture
3. positive construction
4. graveyard control
5. matched nuisance control
6. gauge/control-family safety check
7. receipt path
8. claim ceiling
```

Minimal examples:

```text
F01:
  positive = finite H, finite registry, finite path set
  negative = unbounded path family or continuum integral without finite surrogate

N01:
  positive = AB(rho) != BA(rho)
  negative = commuting A,B collapses order gap

A3:
  positive = fiber density stationary, base density traversing
  negative = chart path mislabeled as geometry if density behavior does not match

A5:
  positive = dephasing contracts transverse Bloch components, rotation preserves spectrum
  negative = amplitude damping destroys false "all Lindblad entropy increases" rule

A6:
  positive = left/right action gap agrees with sqrt(2)||a x r||
  negative = commutative or aligned state gives zero gap

Axis0:
  positive = candidate separates intended geometry/history from matched controls
  negative = product, commuting, amplitude-scrambled, spectrum-matched, and gauge controls

Flux:
  positive = current family predicts or separates engine/runtime behavior beyond controls
  negative = same signal appears under phase/amplitude/sheet scrambling
```

## 21. Open Items

1. Xi bridge:

```text
geometry/history -> rho_AB
```

still open.

2. Final Phi_0:

```text
Phi_0(rho_AB)
```

still open.

3. Flux placement:

```text
manifold binding vs engine current vs axis-internal current vs cross-axis current
```

still open.

4. A3/A6 qualifier:

```text
b_6 = -b_0 b_3 uses chart inner/outer A3, not raw fiber/base A3.
```

should be enforced in runtime row schemas.

5. Hopf chart y-sign:

```text
r_y = -sin(2 eta) sin(2 chi)
```

should be treated as the standard Pauli-y correction and reconciled with older
source text.

6. Engine-type determinant:

```text
(A3, A4) underdetermines engine type.
```

The row matrix needs chart role, sheet sign, path class, order family, and
possibly flux bookkeeping.

7. A4 level:

```text
A4 appears likely engine-instance-level rather than per-stage.
```

This needs cross-check against engine charts and runtime sims.

8. Load-bearing formal proof:

```text
The current z3 fence in the math consistency scout is supportive only. It checks
nonpromotion/dependency bookkeeping; it is not a load-bearing theorem that the
axis derivations, Xi boundary, or flux boundary are impossible to violate.
```

A stronger z3/cvc5 proof packet is a separate future gate.

## 22. Next Sim Requirements

The next clean sim pack should include:

```text
axes_qit_engine_math_consistency_probe
  - Axis0 torus entropy fixture
  - Hopf Bloch sign fixture
  - A3 fiber/base fixture
  - A5 channel/generator fixture
  - A6 left/right gap fixture
  - 16-token projection fixture
  - T1/T2 engine chart fixture
  - claim-ceiling/nonpromotion fixture

full_engine_chart_qit_fep_bridge_probe
  - engine row -> terrain -> operator -> Kraus history -> rho_AB posterior
  - Axis0 candidate batch
  - matched/stress controls

flux_current_family_grid_probe
  - J_geom, J_chi, J_Bloch, J_ent, J_cut, J_axis, J_cross
  - multi-seed/multi-topology/multi-carrier controls

cellular_holodeck_qit_fep_probe
  - finite lattice cells carrying density states
  - local CPTP update
  - coarse-grained process cuts
  - finite variance across seed/topology/layer
```

## 23. Bottom Line

The clean current reading is:

```text
F01 + N01
  -> finite distinguishability under noncommuting operations
  -> Hopf/Weyl finite QIT carrier
  -> terrain generator laws
  -> judging operator channels
  -> ordered token grammar
  -> engine charts
  -> QIT-FEP/Holodeck process state
  -> open flux currents
  -> open Xi bridge
  -> open Axis0 kernel
```

The system is strongest when every metaphor is translated into an operator,
channel, entropy, path family, probe family, or finite receipt.
