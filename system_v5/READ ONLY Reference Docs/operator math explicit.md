Right.

The intrinsic operator math is only the **4 base operators**.  
`UP / DOWN` is **not** extra operator math by itself. It only appears **after** a terrain map is chosen.

So here is the operator packet with only the actual operators, fully expanded.

## State Matrix

\[
\mathcal H=\mathbb C^2
\]

\[
\mathcal D(\mathcal H)=\{\rho\in\mathcal B(\mathcal H):\rho\ge 0,\ \operatorname{Tr}\rho=1\}
\]

\[
\rho=
\begin{pmatrix}
a & u-iv\\
u+iv & d
\end{pmatrix}
\]

with

\[
a,d,u,v\in\mathbb R,\qquad a\ge 0,\qquad d\ge 0,\qquad a+d=1,\qquad u^2+v^2\le ad
\]

## Fixed Matrices

\[
I=
\begin{pmatrix}
1&0\\
0&1
\end{pmatrix}
\]

\[
\sigma_x=
\begin{pmatrix}
0&1\\
1&0
\end{pmatrix}
\]

\[
\sigma_y=
\begin{pmatrix}
0&-i\\
i&0
\end{pmatrix}
\]

\[
\sigma_z=
\begin{pmatrix}
1&0\\
0&-1
\end{pmatrix}
\]

## Projectors

\[
P_0=\frac12(I+\sigma_z)=
\begin{pmatrix}
1&0\\
0&0
\end{pmatrix}
\]

\[
P_1=\frac12(I-\sigma_z)=
\begin{pmatrix}
0&0\\
0&1
\end{pmatrix}
\]

\[
Q_+=\frac12(I+\sigma_x)=
\frac12
\begin{pmatrix}
1&1\\
1&1
\end{pmatrix}
\]

\[
Q_-=\frac12(I-\sigma_x)=
\frac12
\begin{pmatrix}
1&-1\\
-1&1
\end{pmatrix}
\]

## First Operator

Side label: `Ti`

### Exact channel
\[
\rho\longmapsto (1-q_1)\rho+q_1(P_0\rho P_0+P_1\rho P_1)
\]

### Full matrix multiplication
\[
P_0\rho P_0=
\begin{pmatrix}
1&0\\
0&0
\end{pmatrix}
\begin{pmatrix}
a&u-iv\\
u+iv&d
\end{pmatrix}
\begin{pmatrix}
1&0\\
0&0
\end{pmatrix}
=
\begin{pmatrix}
a&0\\
0&0
\end{pmatrix}
\]

\[
P_1\rho P_1=
\begin{pmatrix}
0&0\\
0&1
\end{pmatrix}
\begin{pmatrix}
a&u-iv\\
u+iv&d
\end{pmatrix}
\begin{pmatrix}
0&0\\
0&1
\end{pmatrix}
=
\begin{pmatrix}
0&0\\
0&d
\end{pmatrix}
\]

so

\[
P_0\rho P_0+P_1\rho P_1=
\begin{pmatrix}
a&0\\
0&d
\end{pmatrix}
\]

and therefore

\[
(1-q_1)\rho+q_1(P_0\rho P_0+P_1\rho P_1)
=
(1-q_1)
\begin{pmatrix}
a&u-iv\\
u+iv&d
\end{pmatrix}
+
q_1
\begin{pmatrix}
a&0\\
0&d
\end{pmatrix}
\]

\[
=
\begin{pmatrix}
a&(1-q_1)(u-iv)\\
(1-q_1)(u+iv)&d
\end{pmatrix}
\]

### Kraus form
\[
K_0=
\sqrt{1-q_1}
\begin{pmatrix}
1&0\\
0&1
\end{pmatrix},
\qquad
K_1=
\sqrt{q_1}
\begin{pmatrix}
1&0\\
0&0
\end{pmatrix},
\qquad
K_2=
\sqrt{q_1}
\begin{pmatrix}
0&0\\
0&1
\end{pmatrix}
\]

\[
\rho\longmapsto K_0\rho K_0^\dagger+K_1\rho K_1^\dagger+K_2\rho K_2^\dagger
\]

### Trace-preserving check
\[
K_0^\dagger K_0+K_1^\dagger K_1+K_2^\dagger K_2
=
(1-q_1)I+q_1P_0+q_1P_1
=
I
\]

### Continuous-time generator
\[
\mathcal L_1(\rho)=\frac{\kappa_1}{2}(\sigma_z\rho\sigma_z-\rho)
\]

\[
\sigma_z\rho\sigma_z=
\begin{pmatrix}
1&0\\
0&-1
\end{pmatrix}
\begin{pmatrix}
a&u-iv\\
u+iv&d
\end{pmatrix}
\begin{pmatrix}
1&0\\
0&-1
\end{pmatrix}
=
\begin{pmatrix}
a&-(u-iv)\\
-(u+iv)&d
\end{pmatrix}
\]

so

\[
\mathcal L_1(\rho)=
\frac{\kappa_1}{2}
\left(
\begin{pmatrix}
a&-(u-iv)\\
-(u+iv)&d
\end{pmatrix}
-
\begin{pmatrix}
a&u-iv\\
u+iv&d
\end{pmatrix}
\right)
\]

\[
=
\begin{pmatrix}
0&-\kappa_1(u-iv)\\
-\kappa_1(u+iv)&0
\end{pmatrix}
\]

## Second Operator

Side label: `Te`

### Exact channel
\[
\rho\longmapsto (1-q_2)\rho+q_2(Q_+\rho Q_+ + Q_-\rho Q_-)
\]

### Full matrix multiplication
\[
Q_+\rho Q_+
=
\frac14
\begin{pmatrix}
1&1\\
1&1
\end{pmatrix}
\begin{pmatrix}
a&u-iv\\
u+iv&d
\end{pmatrix}
\begin{pmatrix}
1&1\\
1&1
\end{pmatrix}
\]

First multiply on the left:

\[
\begin{pmatrix}
1&1\\
1&1
\end{pmatrix}
\begin{pmatrix}
a&u-iv\\
u+iv&d
\end{pmatrix}
=
\begin{pmatrix}
a+u+iv&u+d-iv\\
a+u+iv&u+d-iv
\end{pmatrix}
\]

Then multiply on the right:

\[
Q_+\rho Q_+
=
\frac14
\begin{pmatrix}
a+d+2u&a+d+2u\\
a+d+2u&a+d+2u
\end{pmatrix}
=
\frac14
\begin{pmatrix}
1+2u&1+2u\\
1+2u&1+2u
\end{pmatrix}
\]

Similarly,

\[
Q_-\rho Q_-
=
\frac14
\begin{pmatrix}
1-2u&-1+2u\\
-1+2u&1-2u
\end{pmatrix}
\]

Add them:

\[
Q_+\rho Q_+ + Q_-\rho Q_-=
\begin{pmatrix}
\frac12&u\\
u&\frac12
\end{pmatrix}
\]

Therefore

\[
(1-q_2)\rho+q_2(Q_+\rho Q_+ + Q_-\rho Q_-)
\]

\[
=
(1-q_2)
\begin{pmatrix}
a&u-iv\\
u+iv&d
\end{pmatrix}
+
q_2
\begin{pmatrix}
\frac12&u\\
u&\frac12
\end{pmatrix}
\]

\[
=
\begin{pmatrix}
(1-q_2)a+\frac{q_2}{2}&u-i(1-q_2)v\\
u+i(1-q_2)v&(1-q_2)d+\frac{q_2}{2}
\end{pmatrix}
\]

### Kraus form
\[
K_0=
\sqrt{1-q_2}
\begin{pmatrix}
1&0\\
0&1
\end{pmatrix}
\]

\[
K_1=
\sqrt{q_2}\,
\frac12
\begin{pmatrix}
1&1\\
1&1
\end{pmatrix}
\]

\[
K_2=
\sqrt{q_2}\,
\frac12
\begin{pmatrix}
1&-1\\
-1&1
\end{pmatrix}
\]

\[
\rho\longmapsto K_0\rho K_0^\dagger+K_1\rho K_1^\dagger+K_2\rho K_2^\dagger
\]

### Trace-preserving check
\[
K_0^\dagger K_0+K_1^\dagger K_1+K_2^\dagger K_2
=
(1-q_2)I+q_2Q_++q_2Q_-=I
\]

### Continuous-time generator
\[
\mathcal L_2(\rho)=\frac{\kappa_2}{2}(\sigma_x\rho\sigma_x-\rho)
\]

\[
\sigma_x\rho\sigma_x=
\begin{pmatrix}
0&1\\
1&0
\end{pmatrix}
\begin{pmatrix}
a&u-iv\\
u+iv&d
\end{pmatrix}
\begin{pmatrix}
0&1\\
1&0
\end{pmatrix}
=
\begin{pmatrix}
d&u+iv\\
u-iv&a
\end{pmatrix}
\]

so

\[
\mathcal L_2(\rho)=
\frac{\kappa_2}{2}
\left(
\begin{pmatrix}
d&u+iv\\
u-iv&a
\end{pmatrix}
-
\begin{pmatrix}
a&u-iv\\
u+iv&d
\end{pmatrix}
\right)
\]

\[
=
\frac{\kappa_2}{2}
\begin{pmatrix}
d-a&2iv\\
-2iv&a-d
\end{pmatrix}
\]

## Third Operator

Side label: `Fi`

### Exact channel
\[
\rho\longmapsto U_x(\theta)\rho U_x(\theta)^\dagger
\]

with

\[
U_x(\theta)=
\begin{pmatrix}
\cos\frac{\theta}{2}&-i\sin\frac{\theta}{2}\\
-i\sin\frac{\theta}{2}&\cos\frac{\theta}{2}
\end{pmatrix}
\]

and

\[
U_x(\theta)^\dagger=
\begin{pmatrix}
\cos\frac{\theta}{2}&i\sin\frac{\theta}{2}\\
i\sin\frac{\theta}{2}&\cos\frac{\theta}{2}
\end{pmatrix}
\]

### Full matrix multiplication
\[
U_x(\theta)\rho
=
\begin{pmatrix}
\cos\frac{\theta}{2}&-i\sin\frac{\theta}{2}\\
-i\sin\frac{\theta}{2}&\cos\frac{\theta}{2}
\end{pmatrix}
\begin{pmatrix}
a&u-iv\\
u+iv&d
\end{pmatrix}
\]

\[
=
\begin{pmatrix}
a\cos\frac{\theta}{2}-i(u+iv)\sin\frac{\theta}{2}&(u-iv)\cos\frac{\theta}{2}-id\sin\frac{\theta}{2}\\
-ia\sin\frac{\theta}{2}+(u+iv)\cos\frac{\theta}{2}&-i(u-iv)\sin\frac{\theta}{2}+d\cos\frac{\theta}{2}
\end{pmatrix}
\]

Then

\[
U_x(\theta)\rho U_x(\theta)^\dagger
=
\begin{pmatrix}
a'&u'-iv'\\
u'+iv'&d'
\end{pmatrix}
\]

with

\[
a'=a\cos^2\frac{\theta}{2}+d\sin^2\frac{\theta}{2}+v\sin\theta
\]

\[
d'=a\sin^2\frac{\theta}{2}+d\cos^2\frac{\theta}{2}-v\sin\theta
\]

\[
u'=u
\]

\[
v'=v\cos\theta-\frac{a-d}{2}\sin\theta
\]

So the full output matrix is

\[
U_x(\theta)\rho U_x(\theta)^\dagger
=
\begin{pmatrix}
a\cos^2\frac{\theta}{2}+d\sin^2\frac{\theta}{2}+v\sin\theta
&
u-i\left(v\cos\theta-\frac{a-d}{2}\sin\theta\right)
\\[1ex]
u+i\left(v\cos\theta-\frac{a-d}{2}\sin\theta\right)
&
a\sin^2\frac{\theta}{2}+d\cos^2\frac{\theta}{2}-v\sin\theta
\end{pmatrix}
\]

### Continuous-time generator
\[
\mathcal L_3(\rho)=-i\left[\frac{\omega_3}{2}\sigma_x,\rho\right]
\]

\[
\left[\sigma_x,\rho\right]
=
\begin{pmatrix}
0&1\\
1&0
\end{pmatrix}
\begin{pmatrix}
a&u-iv\\
u+iv&d
\end{pmatrix}
-
\begin{pmatrix}
a&u-iv\\
u+iv&d
\end{pmatrix}
\begin{pmatrix}
0&1\\
1&0
\end{pmatrix}
\]

\[
=
\begin{pmatrix}
u+iv&d\\
a&u-iv
\end{pmatrix}
-
\begin{pmatrix}
u-iv&a\\
d&u+iv
\end{pmatrix}
=
\begin{pmatrix}
2iv&d-a\\
a-d&-2iv
\end{pmatrix}
\]

Therefore

\[
\mathcal L_3(\rho)
=
-i\frac{\omega_3}{2}
\begin{pmatrix}
2iv&d-a\\
a-d&-2iv
\end{pmatrix}
=
\begin{pmatrix}
\omega_3 v&-\frac{i\omega_3}{2}(d-a)\\
\frac{i\omega_3}{2}(d-a)&-\omega_3 v
\end{pmatrix}
\]

## Fourth Operator

Side label: `Fe`

### Exact channel
\[
\rho\longmapsto U_z(\phi)\rho U_z(\phi)^\dagger
\]

with

\[
U_z(\phi)=
\begin{pmatrix}
e^{-i\phi/2}&0\\
0&e^{i\phi/2}
\end{pmatrix}
\]

and

\[
U_z(\phi)^\dagger=
\begin{pmatrix}
e^{i\phi/2}&0\\
0&e^{-i\phi/2}
\end{pmatrix}
\]

### Full matrix multiplication
\[
U_z(\phi)\rho U_z(\phi)^\dagger
=
\begin{pmatrix}
e^{-i\phi/2}&0\\
0&e^{i\phi/2}
\end{pmatrix}
\begin{pmatrix}
a&u-iv\\
u+iv&d
\end{pmatrix}
\begin{pmatrix}
e^{i\phi/2}&0\\
0&e^{-i\phi/2}
\end{pmatrix}
\]

\[
=
\begin{pmatrix}
a&e^{-i\phi}(u-iv)\\
e^{i\phi}(u+iv)&d
\end{pmatrix}
\]

Now expand the off-diagonal terms:

\[
e^{-i\phi}(u-iv)
=
(\cos\phi-i\sin\phi)(u-iv)
=
(u\cos\phi-v\sin\phi)-i(u\sin\phi+v\cos\phi)
\]

\[
e^{i\phi}(u+iv)
=
(u\cos\phi-v\sin\phi)+i(u\sin\phi+v\cos\phi)
\]

So the full output matrix is

\[
U_z(\phi)\rho U_z(\phi)^\dagger
=
\begin{pmatrix}
a&
(u\cos\phi-v\sin\phi)-i(u\sin\phi+v\cos\phi)
\\[1ex]
(u\cos\phi-v\sin\phi)+i(u\sin\phi+v\cos\phi)
&
d
\end{pmatrix}
\]

### Continuous-time generator
\[
\mathcal L_4(\rho)=-i\left[\frac{\omega_4}{2}\sigma_z,\rho\right]
\]

\[
[\sigma_z,\rho]
=
\begin{pmatrix}
1&0\\
0&-1
\end{pmatrix}
\begin{pmatrix}
a&u-iv\\
u+iv&d
\end{pmatrix}
-
\begin{pmatrix}
a&u-iv\\
u+iv&d
\end{pmatrix}
\begin{pmatrix}
1&0\\
0&-1
\end{pmatrix}
\]

\[
=
\begin{pmatrix}
a&u-iv\\
-(u+iv)&-d
\end{pmatrix}
-
\begin{pmatrix}
a&-(u-iv)\\
u+iv&-d
\end{pmatrix}
=
\begin{pmatrix}
0&2(u-iv)\\
-2(u+iv)&0
\end{pmatrix}
\]

Therefore

\[
\mathcal L_4(\rho)
=
-i\frac{\omega_4}{2}
\begin{pmatrix}
0&2(u-iv)\\
-2(u+iv)&0
\end{pmatrix}
=
\begin{pmatrix}
0&-i\omega_4(u-iv)\\
i\omega_4(u+iv)&0
\end{pmatrix}
\]

## Exact Lock

These are the only intrinsic operator families in this packet:

\[
\mathcal O_1,\ \mathcal O_2,\ \mathcal O_3,\ \mathcal O_4
\]

with side labels

- `Ti`
- `Te`
- `Fi`
- `Fe`

`UP` and `DOWN` are **not** additional operator formulas.  
They are only composition order once a terrain map is supplied.

If you want, next I will do the same thing for the terrains:
- full explicit matrix math
- every term expanded
- no shorthand.