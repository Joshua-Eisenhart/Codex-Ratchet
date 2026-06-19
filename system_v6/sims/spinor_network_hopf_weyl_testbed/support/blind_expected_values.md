# SN Expected Values

Read-only independent lane. I did not read `system_v6/sims/`.

Notation:

- `psi(phi, chi; eta) = (exp(i(phi+chi)) cos eta, exp(i(phi-chi)) sin eta)`.
- Nodes: `eta_i = pi/8 + i*pi/20`, so `2 eta_i = pi/4 + i*pi/10`, `i=0..5`.
- For a pure spinor return defect I use the Hilbert norm `||psi_final - psi_initial||_2`.

## 1. Fiber Loop

Fiber loop: `gamma_f(u): phi -> phi + u`, `u:0->2pi`.

The component phase arguments change as

- component 1: `(phi+u)+chi - (phi+chi) = u`, so at `u=2pi` the shift is `+2pi`;
- component 2: `(phi+u)-chi - (phi-chi) = u`, so at `u=2pi` the shift is `+2pi`.

Thus

```text
psi_f(2pi) = exp(i 2pi) psi(0) = psi(0)
```

Exact fiber return defect:

```text
||psi_f(2pi) - psi(0)||_2 = 0
```

## 2. Base Loop Return Defect

Base loop: `gamma_b(u): phi -> phi - cos(2 eta) u`, `chi -> chi + u`.

Let `c = cos(2 eta)`. The component phase shifts are

```text
Delta_1 = (-c u) + u = (1-c)u
Delta_2 = (-c u) - u = -(1+c)u
```

At `u=2pi`:

```text
Delta_1 = 2pi(1-c)
Delta_2 = -2pi(1+c)
```

Because `exp(i 2pi(1-c)) = exp(-i 2pi c)` and `exp(-i 2pi(1+c)) = exp(-i 2pi c)`, both components acquire the same final multiplier. Therefore

```text
psi_b(2pi) = exp(-i 2pi cos(2 eta)) psi(0)
```

and

```text
defect_b(eta)
  = |exp(-i 2pi cos(2 eta)) - 1|
  = sqrt(2 - 2 cos(2pi cos(2 eta)))
  = 2 |sin(pi cos(2 eta))|.
```

Node values:

| i | eta_i | cos(2 eta_i) | exact defect | 12-digit numeric |
|---:|---|---|---|---:|
| 0 | `pi/8` | `sqrt(2)/2` | `2 sin(pi sqrt(2)/2)` | `1.591386403135` |
| 1 | `7pi/40` | `cos(7pi/20)` | `2 sin(pi cos(7pi/20))` | `1.979143640047` |
| 2 | `9pi/40` | `cos(9pi/20)` | `2 sin(pi cos(9pi/20))` | `0.943815486749` |
| 3 | `11pi/40` | `cos(11pi/20)` | `2 |sin(pi cos(11pi/20))|` | `0.943815486749` |
| 4 | `13pi/40` | `cos(13pi/20)` | `2 |sin(pi cos(13pi/20))|` | `1.979143640047` |
| 5 | `3pi/8` | `-sqrt(2)/2` | `2 sin(pi sqrt(2)/2)` | `1.591386403135` |

General zero and maximal conditions:

- Exact zero iff `cos(2 eta) in Z`, so within the real range this means `cos(2 eta) in {-1, 0, 1}`.
- Exact maximum `2` iff `cos(2 eta) in Z + 1/2`, so within the real range this means `cos(2 eta) in {-1/2, 1/2}`.
- None of the six listed nodes is exactly zero or exactly maximal.
- The largest node defects are at `i=1` and `i=4`: `1.979143640047`, close to but not equal to the maximum `2`.

Dual composition, base then fiber:

The fiber loop contributes a final multiplier `exp(i 2pi)=1`, so composing base then fiber gives the same final multiplier as the base loop:

```text
psi_(b then f)(final) = exp(-i 2pi cos(2 eta)) psi(0)
defect_(b then f)(eta) = 2 |sin(pi cos(2 eta))|.
```

## 3. Density Invariance And Bloch Path Length

For the fiber loop, both spinor components are multiplied by the same phase `exp(iu)`, so

```text
rho_f(u) = psi_f(u) psi_f(u)^dagger
         = exp(iu) psi(0) psi(0)^dagger exp(-iu)
         = rho(0).
```

Thus density is exactly invariant under the fiber loop.

For the base loop, only `chi` matters for the Bloch azimuth:

```text
r(u) = (sin(2 eta) cos(2 chi(u)),
        sin(2 eta) sin(2 chi(u)),
        cos(2 eta)),
chi(u) = chi_0 + u.
```

Differentiate:

```text
dr/du = (-2 sin(2 eta) sin(2 chi + 2u),
          2 sin(2 eta) cos(2 chi + 2u),
          0)
||dr/du|| = 2 sin(2 eta)
```

for these nodes, where `sin(2 eta)>0`. Therefore the base-loop Bloch path length over `u:0->2pi` is

```text
L_b(eta) = integral_0^(2pi) 2 sin(2 eta) du = 4pi sin(2 eta).
```

Node values:

| i | eta_i | exact length | 12-digit numeric |
|---:|---|---|---:|
| 0 | `pi/8` | `2 sqrt(2) pi` | `8.885765876317` |
| 1 | `7pi/40` | `4 pi sin(7pi/20)` | `11.196718202763` |
| 2 | `9pi/40` | `4 pi sin(9pi/20)` | `12.411657739400` |
| 3 | `11pi/40` | `4 pi sin(11pi/20)` | `12.411657739400` |
| 4 | `13pi/40` | `4 pi sin(13pi/20)` | `11.196718202763` |
| 5 | `3pi/8` | `2 sqrt(2) pi` | `8.885765876317` |

## 4. Chirality Gap

Convention used for this independent lane:

```text
H_L = (sigma_x + sigma_y + sigma_z)/sqrt(3)
H_R = (sigma_x - sigma_y + sigma_z)/sqrt(3)
```

This is the complex-conjugate/right-handed Pauli convention, flipping the `sigma_y` sign.

Pinned state:

```text
psi_0 = psi(0.3, 0.2; pi/8)
t = 0.4
U_L = exp(-i H_L t)
U_R = exp(-i H_R t)
```

Measured quantity:

```text
Delta_z = <sigma_z>_L - <sigma_z>_R
```

12-digit numeric result:

```text
<sigma_z>_L = 0.218352256244
<sigma_z>_R = 0.813511623484
Delta_z    = -0.595159367240
```

If the build uses a different L/R mirror convention, this is the item most likely to differ.

## 5. Order Gap

Definitions used:

```text
H_0 = (sigma_x + sigma_y + sigma_z)/sqrt(3)
Phi_T(rho) = exp(-i H_0 t) rho exp(i H_0 t), t=0.4
Ti(rho) = (1-q) rho + q sigma_z rho sigma_z, q=0.3
rho = |psi(0.3, 0.2; pi/8)><psi(0.3, 0.2; pi/8)|
```

Computed commutator witness:

```text
G = Phi_T(Ti(rho)) - Ti(Phi_T(rho))
```

Trace norm:

```text
||G||_1 = 0.329354806547
```

For the commuting control `Ti` versus a pure `z` rotation `Fe(rho)=exp(-i sigma_z t) rho exp(i sigma_z t)`, dephasing and rotation are both diagonal-axis operations, so

```text
Fe(Ti(rho)) - Ti(Fe(rho)) = 0
||Fe(Ti(rho)) - Ti(Fe(rho))||_1 = 0
```

The floating calculation gives only roundoff residue, about `1e-16`.

## 6. Quaternion And Octonion Witnesses

Quaternion edge noncommutation:

```text
i j = k
j i = -k
i j - j i = 2k
||i j - j i|| = ||2k|| = 2
```

Octonion chord witness, using the standard Cayley-Dickson/Fano orientation where `e1 e2 = e3`, `e3 e4 = e7`, and `e2 e4 = e6`, `e1 e6 = -e7`:

```text
(e1 e2) e4 = e7
e1 (e2 e4) = -e7
[(e1, e2, e4)] = (e1 e2) e4 - e1 (e2 e4) = 2e7
```

Exact associator norm:

```text
||2e7|| = 2
```

## 7. 6-Site Chord Cut

If the build creates a product of node states and no entangling step, then across any chord cut `A|B`:

```text
rho_AB = rho_A tensor rho_B
S(AB) = S(A) + S(B)
I(A:B) = S(A) + S(B) - S(AB) = 0
```

If the implemented quantity is the coherent-information-style chord value

```text
I_c = S(B) - S(AB)
```

then for a pure product across the cut, `S(B)=0` and `S(AB)=0`, so

```text
I_c = 0.
```

More generally, without an entangling/correlating step the chord cut should not show positive correlation:

```text
product / uncorrelated indicator: I(A:B) = 0, and I_c <= 0
correlated indicator: positive mutual information I(A:B) > 0
entanglement-capable indicator: positive coherent information I_c > 0, depending on the exact cut/channel convention
```

So for a pure product build, a positive chord-cut value is a red flag that the build has introduced correlation, changed the quantity, or computed the cut incorrectly.
