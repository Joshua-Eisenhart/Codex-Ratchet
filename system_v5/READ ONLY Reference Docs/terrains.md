## Definitions

### Carrier
| Label | Exact math |
|---|---|
| left spinor | \(\psi_L \in \mathbb C^2,\ \|\psi_L\|=1\) |
| right spinor | \(\psi_R \in \mathbb C^2,\ \|\psi_R\|=1\) |
| carrier manifold | \(\displaystyle S^3=\{\psi\in\mathbb C^2:\|\psi\|=1\}\) |
| left density | \(\displaystyle \rho_L=\psi_L\psi_L^\dagger=\frac12\left(I+\vec r_L\cdot\vec\sigma\right)\) |
| right density | \(\displaystyle \rho_R=\psi_R\psi_R^\dagger=\frac12\left(I+\vec r_R\cdot\vec\sigma\right)\) |
| Hopf coordinates | \(\displaystyle \psi_s(\phi,\chi;\eta)=\begin{pmatrix}e^{i(\phi+\chi)}\cos\eta\\ e^{i(\phi-\chi)}\sin\eta\end{pmatrix},\quad s\in\{L,R\}\) |
| Hopf projection | \(\displaystyle \pi(\psi)=\psi^\dagger \vec\sigma\,\psi\in S^2\) |

### Pauli Data
| Label | Exact math |
|---|---|
| Pauli triple | \(\vec\sigma=(\sigma_x,\sigma_y,\sigma_z)\) |
| \(\sigma_x\) | \(\begin{pmatrix}0&1\\1&0\end{pmatrix}\) |
| \(\sigma_y\) | \(\begin{pmatrix}0&-i\\ i&0\end{pmatrix}\) |
| \(\sigma_z\) | \(\begin{pmatrix}1&0\\0&-1\end{pmatrix}\) |
| \(\sigma_-\) | \(\begin{pmatrix}0&0\\1&0\end{pmatrix}\) |
| \(\sigma_+\) | \(\begin{pmatrix}0&1\\0&0\end{pmatrix}\) |

### Hamiltonians
| Label | Exact math |
|---|---|
| base Hamiltonian | \(\displaystyle H_0=n_x\sigma_x+n_y\sigma_y+n_z\sigma_z\) |
| left Hamiltonian | \(\displaystyle H_L=+H_0\) |
| right Hamiltonian | \(\displaystyle H_R=-H_0\) |
| left Bloch law | \(\displaystyle \dot{\vec r}_L=2\,\vec n\times \vec r_L\) |
| right Bloch law | \(\displaystyle \dot{\vec r}_R=-2\,\vec n\times \vec r_R\) |

### Dissipative Objects
| Label | Exact math |
|---|---|
| dissipator | \(\displaystyle D[L](\rho)=L\rho L^\dagger-\frac12\left(L^\dagger L\rho+\rho L^\dagger L\right)\) |
| left Se family operators | \(\displaystyle L^{F,L}_k=a^{F,L}_{k0}I+a^{F,L}_{kx}\sigma_x+a^{F,L}_{ky}\sigma_y+a^{F,L}_{kz}\sigma_z\) |
| right Se family operators | \(\displaystyle L^{C,R}_k=a^{C,R}_{k0}I+a^{C,R}_{kx}\sigma_x+a^{C,R}_{ky}\sigma_y+a^{C,R}_{kz}\sigma_z\) |
| left Ne family operators | \(\displaystyle M^{V,L}_k=b^{V,L}_{k0}I+b^{V,L}_{kx}\sigma_x+b^{V,L}_{ky}\sigma_y+b^{V,L}_{kz}\sigma_z\) |
| right Ne family operators | \(\displaystyle M^{S,R}_k=b^{S,R}_{k0}I+b^{S,R}_{kx}\sigma_x+b^{S,R}_{ky}\sigma_y+b^{S,R}_{kz}\sigma_z\) |
| left Si projectors | \(\displaystyle P^{H,L}_j=\frac12\left(I+\hat m^{H,L}_j\cdot\vec\sigma\right),\quad [K_L,P^{H,L}_j]=0\) |
| right Si projectors | \(\displaystyle P^{Ci,R}_j=\frac12\left(I+\hat m^{Ci,R}_j\cdot\vec\sigma\right),\quad [K_R,P^{Ci,R}_j]=0\) |

### Loop Geometry
| Label | Exact math |
|---|---|
| torus family | \(\displaystyle T_\eta=\{\psi_s(\phi,\chi;\eta):\phi,\chi\in[0,2\pi)\}\subset S^3\) |
| left fiber loop | \(\displaystyle \Gamma_f^L(\eta,\chi_0)=\{\psi_L(\phi,\chi_0;\eta):\phi\in[0,2\pi)\}\) |
| left base-lift loop | \(\displaystyle \Gamma_b^L(\eta,\phi_0)=\{\psi_L(\phi_0-\cos(2\eta)\chi,\chi;\eta):\chi\in[0,2\pi)\}\) |
| right fiber loop | \(\displaystyle \Gamma_f^R(\eta,\chi_0)=\{\psi_R(\phi,\chi_0;\eta):\phi\in[0,2\pi)\}\) |
| right base-lift loop | \(\displaystyle \Gamma_b^R(\eta,\phi_0)=\{\psi_R(\phi_0-\cos(2\eta)\chi,\chi;\eta):\chi\in[0,2\pi)\}\) |

### Probe
| Label | Exact math |
|---|---|
| observable probe | \(\displaystyle O=O^\dagger\) |
| probe readout | \(\displaystyle p_O(\rho)=\operatorname{Tr}(O\rho)\) |

## Eight Terrain Laws

### Left sheet / Type 1 laws
| Label | Exact math |
|---|---|
| `Se / Funnel` | \(\displaystyle X_F^L(\rho_L)=\sum_k D[L^{F,L}_k](\rho_L)-i\,\varepsilon_{F,L}[H_L,\rho_L]\) |
| `Ne / Vortex` | \(\displaystyle X_V^L(\rho_L)=-i[H_L,\rho_L]+\varepsilon_{V,L}\sum_k D[M^{V,L}_k](\rho_L)\) |
| `Ni / Pit` | \(\displaystyle X_P^L(\rho_L)=\gamma_{P,L}D[\sigma_-](\rho_L)-i\,\varepsilon_{P,L}[H_L,\rho_L]\) |
| `Si / Hill` | \(\displaystyle X_H^L(\rho_L)=-i[K_L,\rho_L]+\sum_j \kappa_{H,L,j}\left(P^{H,L}_j\rho_LP^{H,L}_j-\frac12(P^{H,L}_j\rho_L+\rho_LP^{H,L}_j)\right)\) |

### Right sheet / Type 2 laws
| Label | Exact math |
|---|---|
| `Se / Cannon` | \(\displaystyle X_C^R(\rho_R)=\sum_k D[L^{C,R}_k](\rho_R)-i\,\varepsilon_{C,R}[H_R,\rho_R]\) |
| `Ne / Spiral` | \(\displaystyle X_S^R(\rho_R)=-i[H_R,\rho_R]+\varepsilon_{S,R}\sum_k D[M^{S,R}_k](\rho_R)\) |
| `Ni / Source` | \(\displaystyle X_{So}^R(\rho_R)=\gamma_{So,R}D[\sigma_+](\rho_R)-i\,\varepsilon_{So,R}[H_R,\rho_R]\) |
| `Si / Citadel` | \(\displaystyle X_{Ci}^R(\rho_R)=-i[K_R,\rho_R]+\sum_j \kappa_{Ci,R,j}\left(P^{Ci,R}_j\rho_RP^{Ci,R}_j-\frac12(P^{Ci,R}_j\rho_R+\rho_RP^{Ci,R}_j)\right)\) |

## The Four Loops

| Label | Exact math object |
|---|---|
| Type 1 inner loop | \((\rho_L,\Gamma_f^L)\) |
| Type 1 outer loop | \((\rho_L,\Gamma_b^L)\) |
| Type 2 inner loop | \((\rho_R,\Gamma_f^R)\) |
| Type 2 outer loop | \((\rho_R,\Gamma_b^R)\) |

These four are not the same because:
\[
\Gamma_f^L\neq \Gamma_b^L,\qquad
\Gamma_f^R\neq \Gamma_b^R,\qquad
H_L\neq H_R
\]

## Type 1 Inner Loop

| Stage | Label | Carrier constraint | Density law |
|---|---|---|---|
| 1 | `Se / Funnel` | \(\psi_L(t)\in \Gamma_f^L\) | \(\dot\rho_L=X_F^L(\rho_L)\) |
| 2 | `Ne / Vortex` | \(\psi_L(t)\in \Gamma_f^L\) | \(\dot\rho_L=X_V^L(\rho_L)\) |
| 3 | `Ni / Pit` | \(\psi_L(t)\in \Gamma_f^L\) | \(\dot\rho_L=X_P^L(\rho_L)\) |
| 4 | `Si / Hill` | \(\psi_L(t)\in \Gamma_f^L\) | \(\dot\rho_L=X_H^L(\rho_L)\) |

## Type 1 Outer Loop

| Stage | Label | Carrier constraint | Density law |
|---|---|---|---|
| 1 | `Se / Funnel` | \(\psi_L(t)\in \Gamma_b^L\) | \(\dot\rho_L=X_F^L(\rho_L)\) |
| 2 | `Ne / Vortex` | \(\psi_L(t)\in \Gamma_b^L\) | \(\dot\rho_L=X_V^L(\rho_L)\) |
| 3 | `Ni / Pit` | \(\psi_L(t)\in \Gamma_b^L\) | \(\dot\rho_L=X_P^L(\rho_L)\) |
| 4 | `Si / Hill` | \(\psi_L(t)\in \Gamma_b^L\) | \(\dot\rho_L=X_H^L(\rho_L)\) |

## Type 2 Inner Loop

| Stage | Label | Carrier constraint | Density law |
|---|---|---|---|
| 1 | `Se / Cannon` | \(\psi_R(t)\in \Gamma_f^R\) | \(\dot\rho_R=X_C^R(\rho_R)\) |
| 2 | `Ne / Spiral` | \(\psi_R(t)\in \Gamma_f^R\) | \(\dot\rho_R=X_S^R(\rho_R)\) |
| 3 | `Ni / Source` | \(\psi_R(t)\in \Gamma_f^R\) | \(\dot\rho_R=X_{So}^R(\rho_R)\) |
| 4 | `Si / Citadel` | \(\psi_R(t)\in \Gamma_f^R\) | \(\dot\rho_R=X_{Ci}^R(\rho_R)\) |

## Type 2 Outer Loop

| Stage | Label | Carrier constraint | Density law |
|---|---|---|---|
| 1 | `Se / Cannon` | \(\psi_R(t)\in \Gamma_b^R\) | \(\dot\rho_R=X_C^R(\rho_R)\) |
| 2 | `Ne / Spiral` | \(\psi_R(t)\in \Gamma_b^R\) | \(\dot\rho_R=X_S^R(\rho_R)\) |
| 3 | `Ni / Source` | \(\psi_R(t)\in \Gamma_b^R\) | \(\dot\rho_R=X_{So}^R(\rho_R)\) |
| 4 | `Si / Citadel` | \(\psi_R(t)\in \Gamma_b^R\) | \(\dot\rho_R=X_{Ci}^R(\rho_R)\) |

## Full 16 Placements

| # | Label | Exact placement |
|---|---|---|
| 1 | `Se / Funnel on Type 1 inner` | \((X_F^L,\Gamma_f^L)\) |
| 2 | `Ne / Vortex on Type 1 inner` | \((X_V^L,\Gamma_f^L)\) |
| 3 | `Ni / Pit on Type 1 inner` | \((X_P^L,\Gamma_f^L)\) |
| 4 | `Si / Hill on Type 1 inner` | \((X_H^L,\Gamma_f^L)\) |
| 5 | `Se / Funnel on Type 1 outer` | \((X_F^L,\Gamma_b^L)\) |
| 6 | `Ne / Vortex on Type 1 outer` | \((X_V^L,\Gamma_b^L)\) |
| 7 | `Ni / Pit on Type 1 outer` | \((X_P^L,\Gamma_b^L)\) |
| 8 | `Si / Hill on Type 1 outer` | \((X_H^L,\Gamma_b^L)\) |
| 9 | `Se / Cannon on Type 2 inner` | \((X_C^R,\Gamma_f^R)\) |
| 10 | `Ne / Spiral on Type 2 inner` | \((X_S^R,\Gamma_f^R)\) |
| 11 | `Ni / Source on Type 2 inner` | \((X_{So}^R,\Gamma_f^R)\) |
| 12 | `Si / Citadel on Type 2 inner` | \((X_{Ci}^R,\Gamma_f^R)\) |
| 13 | `Se / Cannon on Type 2 outer` | \((X_C^R,\Gamma_b^R)\) |
| 14 | `Ne / Spiral on Type 2 outer` | \((X_S^R,\Gamma_b^R)\) |
| 15 | `Ni / Source on Type 2 outer` | \((X_{So}^R,\Gamma_b^R)\) |
| 16 | `Si / Citadel on Type 2 outer` | \((X_{Ci}^R,\Gamma_b^R)\) |

## Count

| Label | Count |
|---|---:|
| loops | 4 |
| stages per loop | 4 |
| placements | 16 |

This is the clean structure:

\[
\text{4 loops}=
\{(\rho_L,\Gamma_f^L),(\rho_L,\Gamma_b^L),(\rho_R,\Gamma_f^R),(\rho_R,\Gamma_b^R)\}
\]

\[
\text{16 terrain placements}=
\{\text{4 terrain laws on each of the 4 loops}\}
\]

If you want, I can do the next pass as an even stricter packet with only these five tables:
- carrier
- 8 terrain laws
- 4 loops
- 4 stage tables
- 16 placements