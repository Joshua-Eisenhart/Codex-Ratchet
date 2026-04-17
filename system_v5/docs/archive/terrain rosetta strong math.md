## Definitions

### State Space
| Label | Exact math |
|---|---|
| Hilbert space | \(\mathcal H=\mathbb C^2\) |
| density space | \(\mathcal D(\mathcal H)=\{\rho\in\mathcal B(\mathcal H):\rho\ge 0,\ \operatorname{Tr}\rho=1\}\) |
| left spinor | \(\psi_L\in S^3\subset\mathbb C^2\) |
| right spinor | \(\psi_R\in S^3\subset\mathbb C^2\) |
| carrier manifold | \(\displaystyle S^3=\{\psi\in\mathbb C^2:\|\psi\|=1\}\) |

### Hopf Coordinates
| Label | Exact math |
|---|---|
| spinor chart | \(\displaystyle \psi_s(\phi,\chi;\eta)=\begin{pmatrix}e^{i(\phi+\chi)}\cos\eta\\ e^{i(\phi-\chi)}\sin\eta\end{pmatrix},\quad s\in\{L,R\}\) |
| torus family | \(\displaystyle T_\eta=\{\psi_s(\phi,\chi;\eta):\phi,\chi\in[0,2\pi)\}\subset S^3\) |
| Hopf projection | \(\displaystyle \pi(\psi)=\psi^\dagger\vec\sigma\,\psi=(r_x,r_y,r_z)\in S^2\) |
| Bloch coordinates | \(\displaystyle r_x=\sin(2\eta)\cos(2\chi),\quad r_y=\sin(2\eta)\sin(2\chi),\quad r_z=\cos(2\eta)\) |
| density reduction | \(\displaystyle \rho_s(\phi,\chi;\eta)=\psi_s\psi_s^\dagger=\frac12\left(I+\vec r(\chi,\eta)\cdot\vec\sigma\right)\) |
| fiber-blind reduction | \(\displaystyle \rho_s(\phi+\theta,\chi;\eta)=\rho_s(\phi,\chi;\eta)\) |

### Pauli Data
| Label | Exact math |
|---|---|
| Pauli triple | \(\vec\sigma=(\sigma_x,\sigma_y,\sigma_z)\) |
| \(\sigma_x\) | \(\begin{pmatrix}0&1\\1&0\end{pmatrix}\) |
| \(\sigma_y\) | \(\begin{pmatrix}0&-i\\i&0\end{pmatrix}\) |
| \(\sigma_z\) | \(\begin{pmatrix}1&0\\0&-1\end{pmatrix}\) |
| \(\sigma_-\) | \(\begin{pmatrix}0&0\\1&0\end{pmatrix}\) |
| \(\sigma_+\) | \(\begin{pmatrix}0&1\\0&0\end{pmatrix}\) |

### Loop Geometry
| Label | Exact math |
|---|---|
| Hopf connection | \(\displaystyle \mathcal A=-i\,\psi^\dagger d\psi=d\phi+\cos(2\eta)\,d\chi\) |
| left inner loop | \(\displaystyle \gamma_f^L(u)=\psi_L(\phi_0+u,\chi_0;\eta_0)\) |
| left outer loop | \(\displaystyle \gamma_b^L(u)=\psi_L(\phi_0-\cos(2\eta_0)u,\chi_0+u;\eta_0)\) |
| right inner loop | \(\displaystyle \gamma_f^R(u)=\psi_R(\phi_0+u,\chi_0;\eta_0)\) |
| right outer loop | \(\displaystyle \gamma_b^R(u)=\psi_R(\phi_0-\cos(2\eta_0)u,\chi_0+u;\eta_0)\) |
| horizontal condition | \(\displaystyle \mathcal A(\dot\gamma_b^s)=0\) |
| fiber density path | \(\displaystyle \rho_{f}^s(u)=|\gamma_f^s(u)\rangle\langle\gamma_f^s(u)|=\rho_f^s(0)\) |
| base density path | \(\displaystyle \rho_{b}^s(u)=|\gamma_b^s(u)\rangle\langle\gamma_b^s(u)|=\frac12\left(I+\vec r(\chi_0+u,\eta_0)\cdot\vec\sigma\right)\) |

### Hamiltonians And Dissipators
| Label | Exact math |
|---|---|
| base Hamiltonian | \(\displaystyle H_0=n_x\sigma_x+n_y\sigma_y+n_z\sigma_z\) |
| left Hamiltonian | \(\displaystyle H_L=+H_0\) |
| right Hamiltonian | \(\displaystyle H_R=-H_0\) |
| left Bloch law | \(\displaystyle \dot{\vec r}_L=2\,\vec n\times \vec r_L\) |
| right Bloch law | \(\displaystyle \dot{\vec r}_R=-2\,\vec n\times \vec r_R\) |
| dissipator | \(\displaystyle D[L](\rho)=L\rho L^\dagger-\frac12\left(L^\dagger L\rho+\rho L^\dagger L\right)\) |
| left \(Se\) operators | \(\displaystyle L_k^{F,L}=a_{k0}^{F,L}I+a_{kx}^{F,L}\sigma_x+a_{ky}^{F,L}\sigma_y+a_{kz}^{F,L}\sigma_z\) |
| right \(Se\) operators | \(\displaystyle L_k^{C,R}=a_{k0}^{C,R}I+a_{kx}^{C,R}\sigma_x+a_{ky}^{C,R}\sigma_y+a_{kz}^{C,R}\sigma_z\) |
| left \(Ne\) operators | \(\displaystyle M_k^{V,L}=b_{k0}^{V,L}I+b_{kx}^{V,L}\sigma_x+b_{ky}^{V,L}\sigma_y+b_{kz}^{V,L}\sigma_z\) |
| right \(Ne\) operators | \(\displaystyle M_k^{S,R}=b_{k0}^{S,R}I+b_{kx}^{S,R}\sigma_x+b_{ky}^{S,R}\sigma_y+b_{kz}^{S,R}\sigma_z\) |
| left \(Si\) projectors | \(\displaystyle P_j^{H,L}=\frac12\left(I+\hat m_j^{H,L}\cdot\vec\sigma\right),\ P_j^{H,L}P_m^{H,L}=\delta_{jm}P_j^{H,L},\ \sum_jP_j^{H,L}=I,\ [K_L,P_j^{H,L}]=0\) |
| right \(Si\) projectors | \(\displaystyle P_j^{Ci,R}=\frac12\left(I+\hat m_j^{Ci,R}\cdot\vec\sigma\right),\ P_j^{Ci,R}P_m^{Ci,R}=\delta_{jm}P_j^{Ci,R},\ \sum_jP_j^{Ci,R}=I,\ [K_R,P_j^{Ci,R}]=0\) |

### Stage Generators And Channels
| Label | Exact math |
|---|---|
| left \(Se\) generator | \(\displaystyle X_F^L(\rho)=\sum_k D[L_k^{F,L}](\rho)-i\,\varepsilon_{F,L}[H_L,\rho]\) |
| left \(Ne\) generator | \(\displaystyle X_V^L(\rho)=-i[H_L,\rho]+\varepsilon_{V,L}\sum_k D[M_k^{V,L}](\rho)\) |
| left \(Ni\) generator | \(\displaystyle X_P^L(\rho)=\gamma_{P,L}D[\sigma_-](\rho)-i\,\varepsilon_{P,L}[H_L,\rho]\) |
| left \(Si\) generator | \(\displaystyle X_H^L(\rho)=-i[K_L,\rho]+\sum_j\kappa_{H,L,j}\left(P_j^{H,L}\rho P_j^{H,L}-\frac12(P_j^{H,L}\rho+\rho P_j^{H,L})\right)\) |
| right \(Se\) generator | \(\displaystyle X_C^R(\rho)=\sum_k D[L_k^{C,R}](\rho)-i\,\varepsilon_{C,R}[H_R,\rho]\) |
| right \(Ne\) generator | \(\displaystyle X_S^R(\rho)=-i[H_R,\rho]+\varepsilon_{S,R}\sum_k D[M_k^{S,R}](\rho)\) |
| right \(Ni\) generator | \(\displaystyle X_{So}^R(\rho)=\gamma_{So,R}D[\sigma_+](\rho)-i\,\varepsilon_{So,R}[H_R,\rho]\) |
| right \(Si\) generator | \(\displaystyle X_{Ci}^R(\rho)=-i[K_R,\rho]+\sum_j\kappa_{Ci,R,j}\left(P_j^{Ci,R}\rho P_j^{Ci,R}-\frac12(P_j^{Ci,R}\rho+\rho P_j^{Ci,R})\right)\) |
| stage channel | \(\displaystyle \Phi_\tau^s(t)=e^{tX_\tau^s},\qquad t\ge 0\) |
| probe | \(\displaystyle O=O^\dagger,\qquad p_O(\rho)=\operatorname{Tr}(O\rho)\) |
| stage readout | \(\displaystyle p_O^{s,\ell,\tau}(t)=\operatorname{Tr}\!\left(O\,\Phi_\tau^s(t)\big[\rho_\ell^s(0)\big]\right)\) |

### IGT Parse Rule
| Label | Exact rule |
|---|---|
| outer word | uppercase word in the IGT label |
| inner word | lowercase word in the IGT label |
| precedence up | \(\displaystyle \operatorname{UP}_A(\rho)=A\rho\) |
| precedence down | \(\displaystyle \operatorname{DOWN}_A(\rho)=\rho A\) |

## Type 1 Token Table

| IGT label | Outer word | Outer pair | Inner word | Inner pair |
|---|---|---|---|---|
| `WINlose` | `WIN` | `NeTi` | `lose` | `FiNe` |
| `winWIN` | `WIN` | `FeSi` | `win` | `SiTe` |
| `LOSEwin` | `LOSE` | `TiSe` | `win` | `SeFi` |
| `loseLOSE` | `LOSE` | `NiFe` | `lose` | `TeNi` |

## Type 2 Token Table

| IGT label | Outer word | Outer pair | Inner word | Inner pair |
|---|---|---|---|---|
| `winLOSE` | `LOSE` | `NeFi` | `win` | `TiNe` |
| `WINwin` | `WIN` | `TeSi` | `win` | `SiFe` |
| `loseWIN` | `WIN` | `FiSe` | `lose` | `SeTi` |
| `LOSElose` | `LOSE` | `NiTe` | `lose` | `FeNi` |

## Type 1 Inner Loop
\[
\mathcal L_{L,f}=\{(\gamma_f^L,X_F^L),(\gamma_f^L,X_V^L),(\gamma_f^L,X_P^L),(\gamma_f^L,X_H^L)\}
\]

| Stage | Terrain label | Generator | Channel | Carrier curve | IGT label | Realized word | Jungian pair | Precedence |
|---|---|---|---|---|---|---|---|---|
| 1 | `Se / Funnel` | \(X_F^L\) | \(\Phi_F^L(t)\) | \(\gamma_f^L\) | `LOSEwin` | `win` | `SeFi` | `DOWN / Fi` |
| 2 | `Ne / Vortex` | \(X_V^L\) | \(\Phi_V^L(t)\) | \(\gamma_f^L\) | `WINlose` | `lose` | `FiNe` | `UP / Fi` |
| 3 | `Ni / Pit` | \(X_P^L\) | \(\Phi_P^L(t)\) | \(\gamma_f^L\) | `loseLOSE` | `lose` | `TeNi` | `UP / Te` |
| 4 | `Si / Hill` | \(X_H^L\) | \(\Phi_H^L(t)\) | \(\gamma_f^L\) | `winWIN` | `win` | `SiTe` | `DOWN / Te` |

## Type 1 Outer Loop
\[
\mathcal L_{L,b}=\{(\gamma_b^L,X_F^L),(\gamma_b^L,X_V^L),(\gamma_b^L,X_P^L),(\gamma_b^L,X_H^L)\}
\]

| Stage | Terrain label | Generator | Channel | Carrier curve | IGT label | Realized word | Jungian pair | Precedence |
|---|---|---|---|---|---|---|---|---|
| 1 | `Se / Funnel` | \(X_F^L\) | \(\Phi_F^L(t)\) | \(\gamma_b^L\) | `LOSEwin` | `LOSE` | `TiSe` | `UP / Ti` |
| 2 | `Ne / Vortex` | \(X_V^L\) | \(\Phi_V^L(t)\) | \(\gamma_b^L\) | `WINlose` | `WIN` | `NeTi` | `DOWN / Ti` |
| 3 | `Ni / Pit` | \(X_P^L\) | \(\Phi_P^L(t)\) | \(\gamma_b^L\) | `loseLOSE` | `LOSE` | `NiFe` | `DOWN / Fe` |
| 4 | `Si / Hill` | \(X_H^L\) | \(\Phi_H^L(t)\) | \(\gamma_b^L\) | `winWIN` | `WIN` | `FeSi` | `UP / Fe` |

## Type 2 Inner Loop
\[
\mathcal L_{R,f}=\{(\gamma_f^R,X_C^R),(\gamma_f^R,X_S^R),(\gamma_f^R,X_{So}^R),(\gamma_f^R,X_{Ci}^R)\}
\]

| Stage | Terrain label | Generator | Channel | Carrier curve | IGT label | Realized word | Jungian pair | Precedence |
|---|---|---|---|---|---|---|---|---|
| 1 | `Se / Cannon` | \(X_C^R\) | \(\Phi_C^R(t)\) | \(\gamma_f^R\) | `loseWIN` | `lose` | `SeTi` | `DOWN / Ti` |
| 2 | `Ne / Spiral` | \(X_S^R\) | \(\Phi_S^R(t)\) | \(\gamma_f^R\) | `winLOSE` | `win` | `TiNe` | `UP / Ti` |
| 3 | `Ni / Source` | \(X_{So}^R\) | \(\Phi_{So}^R(t)\) | \(\gamma_f^R\) | `LOSElose` | `lose` | `FeNi` | `UP / Fe` |
| 4 | `Si / Citadel` | \(X_{Ci}^R\) | \(\Phi_{Ci}^R(t)\) | \(\gamma_f^R\) | `WINwin` | `win` | `SiFe` | `DOWN / Fe` |

## Type 2 Outer Loop
\[
\mathcal L_{R,b}=\{(\gamma_b^R,X_C^R),(\gamma_b^R,X_S^R),(\gamma_b^R,X_{So}^R),(\gamma_b^R,X_{Ci}^R)\}
\]

| Stage | Terrain label | Generator | Channel | Carrier curve | IGT label | Realized word | Jungian pair | Precedence |
|---|---|---|---|---|---|---|---|---|
| 1 | `Se / Cannon` | \(X_C^R\) | \(\Phi_C^R(t)\) | \(\gamma_b^R\) | `loseWIN` | `WIN` | `FiSe` | `UP / Fi` |
| 2 | `Ne / Spiral` | \(X_S^R\) | \(\Phi_S^R(t)\) | \(\gamma_b^R\) | `winLOSE` | `LOSE` | `NeFi` | `DOWN / Fi` |
| 3 | `Ni / Source` | \(X_{So}^R\) | \(\Phi_{So}^R(t)\) | \(\gamma_b^R\) | `LOSElose` | `LOSE` | `NiTe` | `DOWN / Te` |
| 4 | `Si / Citadel` | \(X_{Ci}^R\) | \(\Phi_{Ci}^R(t)\) | \(\gamma_b^R\) | `WINwin` | `WIN` | `TeSi` | `UP / Te` |

## Full 16 Placements
\[
\mathcal P_{s,\ell,\tau}=(\gamma_\ell^s,X_\tau^s,\Phi_\tau^s)
\]

| # | Label | Exact placement |
|---|---|---|
| 1 | `Se / Funnel on Type 1 inner` | \((\gamma_f^L,X_F^L,\Phi_F^L)\) |
| 2 | `Ne / Vortex on Type 1 inner` | \((\gamma_f^L,X_V^L,\Phi_V^L)\) |
| 3 | `Ni / Pit on Type 1 inner` | \((\gamma_f^L,X_P^L,\Phi_P^L)\) |
| 4 | `Si / Hill on Type 1 inner` | \((\gamma_f^L,X_H^L,\Phi_H^L)\) |
| 5 | `Se / Funnel on Type 1 outer` | \((\gamma_b^L,X_F^L,\Phi_F^L)\) |
| 6 | `Ne / Vortex on Type 1 outer` | \((\gamma_b^L,X_V^L,\Phi_V^L)\) |
| 7 | `Ni / Pit on Type 1 outer` | \((\gamma_b^L,X_P^L,\Phi_P^L)\) |
| 8 | `Si / Hill on Type 1 outer` | \((\gamma_b^L,X_H^L,\Phi_H^L)\) |
| 9 | `Se / Cannon on Type 2 inner` | \((\gamma_f^R,X_C^R,\Phi_C^R)\) |
| 10 | `Ne / Spiral on Type 2 inner` | \((\gamma_f^R,X_S^R,\Phi_S^R)\) |
| 11 | `Ni / Source on Type 2 inner` | \((\gamma_f^R,X_{So}^R,\Phi_{So}^R)\) |
| 12 | `Si / Citadel on Type 2 inner` | \((\gamma_f^R,X_{Ci}^R,\Phi_{Ci}^R)\) |
| 13 | `Se / Cannon on Type 2 outer` | \((\gamma_b^R,X_C^R,\Phi_C^R)\) |
| 14 | `Ne / Spiral on Type 2 outer` | \((\gamma_b^R,X_S^R,\Phi_S^R)\) |
| 15 | `Ni / Source on Type 2 outer` | \((\gamma_b^R,X_{So}^R,\Phi_{So}^R)\) |
| 16 | `Si / Citadel on Type 2 outer` | \((\gamma_b^R,X_{Ci}^R,\Phi_{Ci}^R)\) |

## Structural Lock
\[
\{\text{4 loops}\}=\{\gamma_f^L,\gamma_b^L,\gamma_f^R,\gamma_b^R\}
\]

\[
\{\text{8 terrain laws}\}=\{X_F^L,X_V^L,X_P^L,X_H^L,X_C^R,X_S^R,X_{So}^R,X_{Ci}^R\}
\]

\[
\{\text{16 placements}\}=\{\mathcal P_{s,\ell,\tau}:s\in\{L,R\},\ \ell\in\{f,b\},\ \tau\in\{Se,Ne,Ni,Si\}\}
\]

This is the upgraded packet.

Next clean pass would be the same format again, but with `Axis 0–7` added as explicit columns on each of the 16 rows.