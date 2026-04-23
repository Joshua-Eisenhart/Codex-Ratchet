**Terrain Packet**

## State Variables

| Label | Math |
|---|---|
| spinor | \(\psi_s(\phi,\chi;\eta)=\begin{pmatrix}e^{i(\phi+\chi)}\cos\eta\\ e^{i(\phi-\chi)}\sin\eta\end{pmatrix},\quad s\in\{L,R\}\) |
| domain | \(\phi,\chi\in[0,2\pi),\quad \eta\in[0,\pi/2]\) |
| carrier | \(S_s^3=\{\psi_s\in\mathbb C^2:\|\psi_s\|=1\}\) |
| density | \(\rho_s=\psi_s\psi_s^\dagger\) |
| density matrix | \(\rho_s(\phi,\chi;\eta)=\begin{pmatrix}\cos^2\eta & e^{2i\chi}\cos\eta\sin\eta\\ e^{-2i\chi}\cos\eta\sin\eta & \sin^2\eta\end{pmatrix}\) |
| Bloch form | \(\rho_s=\frac12(I+r_x\sigma_x+r_y\sigma_y+r_z\sigma_z)\) |
| Bloch vector | \(\vec r_s(\phi,\chi;\eta)=\bigl(\sin 2\eta\cos 2\chi,\ \sin 2\eta\sin 2\chi,\ \cos 2\eta\bigr)\) |

## Fixed Matrices

| Label | Math |
|---|---|
| \(I\) | \(\begin{pmatrix}1&0\\0&1\end{pmatrix}\) |
| \(\sigma_x\) | \(\begin{pmatrix}0&1\\1&0\end{pmatrix}\) |
| \(\sigma_y\) | \(\begin{pmatrix}0&-i\\ i&0\end{pmatrix}\) |
| \(\sigma_z\) | \(\begin{pmatrix}1&0\\0&-1\end{pmatrix}\) |
| \(\sigma_-\) | \(\begin{pmatrix}0&0\\1&0\end{pmatrix}\) |
| \(\sigma_+\) | \(\begin{pmatrix}0&1\\0&0\end{pmatrix}\) |

## Loop Geometry

| Label | Math |
|---|---|
| torus family | \(T_\eta^s=\{\psi_s(\phi,\chi;\eta):\phi,\chi\in[0,2\pi)\}\subset S_s^3\) |
| connection | \(A=-i\,\psi_s^\dagger d\psi_s=d\phi+\cos(2\eta)\,d\chi\) |
| inner loop | \(\gamma_{\mathrm{in}}^s(u)=\psi_s(\phi_0+u,\chi_0;\eta_0)\) |
| outer loop | \(\gamma_{\mathrm{out}}^s(u)=\psi_s(\phi_0-\cos(2\eta_0)u,\chi_0+u;\eta_0)\) |
| horizontal condition | \(A(\dot\gamma_{\mathrm{out}}^s)=0\) |

## Loop Vector Fields

| Label | Math |
|---|---|
| inner field | \(Y_{\mathrm{in}}\psi_s=\partial_\phi\psi_s=i\begin{pmatrix}e^{i(\phi+\chi)}\cos\eta\\ e^{i(\phi-\chi)}\sin\eta\end{pmatrix}\) |
| outer field | \(Y_{\mathrm{out}}\psi_s=\bigl(-\cos(2\eta)\partial_\phi+\partial_\chi\bigr)\psi_s=i\begin{pmatrix}(1-\cos 2\eta)e^{i(\phi+\chi)}\cos\eta\\ -(1+\cos 2\eta)e^{i(\phi-\chi)}\sin\eta\end{pmatrix}\) |

## Density Visibility

| Label | Math |
|---|---|
| inner density path | \(\rho_{\mathrm{in}}^s(u)=\rho_s(\phi_0+u,\chi_0;\eta_0)=\rho_s(\phi_0,\chi_0;\eta_0)\) |
| outer density path | \(\rho_{\mathrm{out}}^s(u)=\rho_s(\phi_0-\cos(2\eta_0)u,\chi_0+u;\eta_0)\) |
| outer density matrix | \(\rho_{\mathrm{out}}^s(u)=\begin{pmatrix}\cos^2\eta_0 & e^{2i(\chi_0+u)}\cos\eta_0\sin\eta_0\\ e^{-2i(\chi_0+u)}\cos\eta_0\sin\eta_0 & \sin^2\eta_0\end{pmatrix}\) |

## Sheet Hamiltonians

| Label | Math |
|---|---|
| base Hamiltonian | \(H_0=n_x\sigma_x+n_y\sigma_y+n_z\sigma_z=\begin{pmatrix}n_z&n_x-i n_y\\ n_x+i n_y&-n_z\end{pmatrix}\) |
| Type 1 sheet | \(H_L=+H_0\) |
| Type 2 sheet | \(H_R=-H_0\) |

## Sheet Flows

| Label | Math |
|---|---|
| Type 1 | \(\dot\rho_L=-i[H_L,\rho_L],\qquad \dot{\vec r}_L=2\,\vec n\times \vec r_L\) |
| Type 2 | \(\dot\rho_R=-i[H_R,\rho_R],\qquad \dot{\vec r}_R=-2\,\vec n\times \vec r_R\) |

## Dissipator

| Label | Math |
|---|---|
| dissipator | \(D[L](\rho)=L\rho L^\dagger-\frac12(L^\dagger L\rho+\rho L^\dagger L)\) |

## Eight Terrain Generators

| Label | Math |
|---|---|
| `Se / Funnel` | \(X_{Se,L}(\rho)=\lambda_{Se,L}\sum_{j=x,y,z}D[\sigma_j](\rho)-i\,\varepsilon_{Se,L}[H_L,\rho]\) |
| `Se / Cannon` | \(X_{Se,R}(\rho)=\lambda_{Se,R}\sum_{j=x,y,z}D[\sigma_j](\rho)-i\,\varepsilon_{Se,R}[H_R,\rho]\) |
| `Ne / Vortex` | \(X_{Ne,L}(\rho)=-i[H_L,\rho]\) |
| `Ne / Spiral` | \(X_{Ne,R}(\rho)=-i[H_R,\rho]\) |
| `Ni / Pit` | \(X_{Ni,L}(\rho)=\gamma_{Ni,L}D[\sigma_-](\rho)-i\,\varepsilon_{Ni,L}[H_L,\rho]\) |
| `Ni / Source` | \(X_{Ni,R}(\rho)=\gamma_{Ni,R}D[\sigma_+](\rho)-i\,\varepsilon_{Ni,R}[H_R,\rho]\) |
| `Si / Hill` | \(X_{Si,L}(\rho)=-i[\omega_L\,\hat m_L\!\cdot\!\vec\sigma,\rho]+\kappa_L\bigl(P_+^L\rho P_+^L+P_-^L\rho P_-^L-\rho\bigr)\) |
| `Si / Citadel` | \(X_{Si,R}(\rho)=-i[\omega_R\,\hat m_R\!\cdot\!\vec\sigma,\rho]+\kappa_R\bigl(P_+^R\rho P_+^R+P_-^R\rho P_-^R-\rho\bigr)\) |

## Projectors In The Last Two Rows

| Label | Math |
|---|---|
| left projectors | \(P_\pm^L=\frac12(I\pm \hat m_L\!\cdot\!\vec\sigma)\) |
| right projectors | \(P_\pm^R=\frac12(I\pm \hat m_R\!\cdot\!\vec\sigma)\) |

## Type 1 Engine: 8 Placements

| Label | Spinor law | Density law |
|---|---|---|
| `Se / Funnel / inner` | \(\dot\psi_L=\Omega_{Se,L,\mathrm{in}}\,Y_{\mathrm{in}}\psi_L\) | \(\dot\rho_L=X_{Se,L}(\rho_L)\) |
| `Se / Funnel / outer` | \(\dot\psi_L=\Omega_{Se,L,\mathrm{out}}\,Y_{\mathrm{out}}\psi_L\) | \(\dot\rho_L=X_{Se,L}(\rho_L)\) |
| `Ne / Vortex / inner` | \(\dot\psi_L=\Omega_{Ne,L,\mathrm{in}}\,Y_{\mathrm{in}}\psi_L\) | \(\dot\rho_L=X_{Ne,L}(\rho_L)\) |
| `Ne / Vortex / outer` | \(\dot\psi_L=\Omega_{Ne,L,\mathrm{out}}\,Y_{\mathrm{out}}\psi_L\) | \(\dot\rho_L=X_{Ne,L}(\rho_L)\) |
| `Ni / Pit / inner` | \(\dot\psi_L=\Omega_{Ni,L,\mathrm{in}}\,Y_{\mathrm{in}}\psi_L\) | \(\dot\rho_L=X_{Ni,L}(\rho_L)\) |
| `Ni / Pit / outer` | \(\dot\psi_L=\Omega_{Ni,L,\mathrm{out}}\,Y_{\mathrm{out}}\psi_L\) | \(\dot\rho_L=X_{Ni,L}(\rho_L)\) |
| `Si / Hill / inner` | \(\dot\psi_L=\Omega_{Si,L,\mathrm{in}}\,Y_{\mathrm{in}}\psi_L\) | \(\dot\rho_L=X_{Si,L}(\rho_L)\) |
| `Si / Hill / outer` | \(\dot\psi_L=\Omega_{Si,L,\mathrm{out}}\,Y_{\mathrm{out}}\psi_L\) | \(\dot\rho_L=X_{Si,L}(\rho_L)\) |

## Type 2 Engine: 8 Placements

| Label | Spinor law | Density law |
|---|---|---|
| `Se / Cannon / inner` | \(\dot\psi_R=\Omega_{Se,R,\mathrm{in}}\,Y_{\mathrm{in}}\psi_R\) | \(\dot\rho_R=X_{Se,R}(\rho_R)\) |
| `Se / Cannon / outer` | \(\dot\psi_R=\Omega_{Se,R,\mathrm{out}}\,Y_{\mathrm{out}}\psi_R\) | \(\dot\rho_R=X_{Se,R}(\rho_R)\) |
| `Ne / Spiral / inner` | \(\dot\psi_R=\Omega_{Ne,R,\mathrm{in}}\,Y_{\mathrm{in}}\psi_R\) | \(\dot\rho_R=X_{Ne,R}(\rho_R)\) |
| `Ne / Spiral / outer` | \(\dot\psi_R=\Omega_{Ne,R,\mathrm{out}}\,Y_{\mathrm{out}}\psi_R\) | \(\dot\rho_R=X_{Ne,R}(\rho_R)\) |
| `Ni / Source / inner` | \(\dot\psi_R=\Omega_{Ni,R,\mathrm{in}}\,Y_{\mathrm{in}}\psi_R\) | \(\dot\rho_R=X_{Ni,R}(\rho_R)\) |
| `Ni / Source / outer` | \(\dot\psi_R=\Omega_{Ni,R,\mathrm{out}}\,Y_{\mathrm{out}}\psi_R\) | \(\dot\rho_R=X_{Ni,R}(\rho_R)\) |
| `Si / Citadel / inner` | \(\dot\psi_R=\Omega_{Si,R,\mathrm{in}}\,Y_{\mathrm{in}}\psi_R\) | \(\dot\rho_R=X_{Si,R}(\rho_R)\) |
| `Si / Citadel / outer` | \(\dot\psi_R=\Omega_{Si,R,\mathrm{out}}\,Y_{\mathrm{out}}\psi_R\) | \(\dot\rho_R=X_{Si,R}(\rho_R)\) |

## Full 16 Placements

| # | Label | Math |
|---|---|---|
| 1 | `Se / Funnel / inner` | \((\dot\psi_L,\dot\rho_L)=\bigl(\Omega_{Se,L,\mathrm{in}}Y_{\mathrm{in}}\psi_L,\ X_{Se,L}(\rho_L)\bigr)\) |
| 2 | `Se / Funnel / outer` | \((\dot\psi_L,\dot\rho_L)=\bigl(\Omega_{Se,L,\mathrm{out}}Y_{\mathrm{out}}\psi_L,\ X_{Se,L}(\rho_L)\bigr)\) |
| 3 | `Ne / Vortex / inner` | \((\dot\psi_L,\dot\rho_L)=\bigl(\Omega_{Ne,L,\mathrm{in}}Y_{\mathrm{in}}\psi_L,\ X_{Ne,L}(\rho_L)\bigr)\) |
| 4 | `Ne / Vortex / outer` | \((\dot\psi_L,\dot\rho_L)=\bigl(\Omega_{Ne,L,\mathrm{out}}Y_{\mathrm{out}}\psi_L,\ X_{Ne,L}(\rho_L)\bigr)\) |
| 5 | `Ni / Pit / inner` | \((\dot\psi_L,\dot\rho_L)=\bigl(\Omega_{Ni,L,\mathrm{in}}Y_{\mathrm{in}}\psi_L,\ X_{Ni,L}(\rho_L)\bigr)\) |
| 6 | `Ni / Pit / outer` | \((\dot\psi_L,\dot\rho_L)=\bigl(\Omega_{Ni,L,\mathrm{out}}Y_{\mathrm{out}}\psi_L,\ X_{Ni,L}(\rho_L)\bigr)\) |
| 7 | `Si / Hill / inner` | \((\dot\psi_L,\dot\rho_L)=\bigl(\Omega_{Si,L,\mathrm{in}}Y_{\mathrm{in}}\psi_L,\ X_{Si,L}(\rho_L)\bigr)\) |
| 8 | `Si / Hill / outer` | \((\dot\psi_L,\dot\rho_L)=\bigl(\Omega_{Si,L,\mathrm{out}}Y_{\mathrm{out}}\psi_L,\ X_{Si,L}(\rho_L)\bigr)\) |
| 9 | `Se / Cannon / inner` | \((\dot\psi_R,\dot\rho_R)=\bigl(\Omega_{Se,R,\mathrm{in}}Y_{\mathrm{in}}\psi_R,\ X_{Se,R}(\rho_R)\bigr)\) |
| 10 | `Se / Cannon / outer` | \((\dot\psi_R,\dot\rho_R)=\bigl(\Omega_{Se,R,\mathrm{out}}Y_{\mathrm{out}}\psi_R,\ X_{Se,R}(\rho_R)\bigr)\) |
| 11 | `Ne / Spiral / inner` | \((\dot\psi_R,\dot\rho_R)=\bigl(\Omega_{Ne,R,\mathrm{in}}Y_{\mathrm{in}}\psi_R,\ X_{Ne,R}(\rho_R)\bigr)\) |
| 12 | `Ne / Spiral / outer` | \((\dot\psi_R,\dot\rho_R)=\bigl(\Omega_{Ne,R,\mathrm{out}}Y_{\mathrm{out}}\psi_R,\ X_{Ne,R}(\rho_R)\bigr)\) |
| 13 | `Ni / Source / inner` | \((\dot\psi_R,\dot\rho_R)=\bigl(\Omega_{Ni,R,\mathrm{in}}Y_{\mathrm{in}}\psi_R,\ X_{Ni,R}(\rho_R)\bigr)\) |
| 14 | `Ni / Source / outer` | \((\dot\psi_R,\dot\rho_R)=\bigl(\Omega_{Ni,R,\mathrm{out}}Y_{\mathrm{out}}\psi_R,\ X_{Ni,R}(\rho_R)\bigr)\) |
| 15 | `Si / Citadel / inner` | \((\dot\psi_R,\dot\rho_R)=\bigl(\Omega_{Si,R,\mathrm{in}}Y_{\mathrm{in}}\psi_R,\ X_{Si,R}(\rho_R)\bigr)\) |
| 16 | `Si / Citadel / outer` | \((\dot\psi_R,\dot\rho_R)=\bigl(\Omega_{Si,R,\mathrm{out}}Y_{\mathrm{out}}\psi_R,\ X_{Si,R}(\rho_R)\bigr)\) |

## Exact Separation

| Layer | Count | Math |
|---|---:|---|
| terrain families | 4 | \(\{Se,Ne,Ni,Si\}\) |
| terrains | 8 | \(\{(Se,L),(Se,R),(Ne,L),(Ne,R),(Ni,L),(Ni,R),(Si,L),(Si,R)\}\) |
| loop placements | 16 | \(\{(\tau,s,\ell):\tau\in\{Se,Ne,Ni,Si\},\ s\in\{L,R\},\ \ell\in\{\mathrm{in},\mathrm{out}\}\}\) |

This is the explicit terrain chart:
- the terrain is the generator \(X_{\tau,s}\)
- the loop is the spinor path field \(Y_{\mathrm{in}}\) or \(Y_{\mathrm{out}}\)
- a placement is the pair \((X_{\tau,s},Y_\ell)\)

That is the structure.