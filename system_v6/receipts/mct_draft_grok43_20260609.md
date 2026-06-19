**M(C,t) Definition**

Let \(C\) be a finite set of predicates on a finite universe \(U\). At step \(n\), let \(S_n\subseteq U\) be finite, \(P_n\) a finite set of maps \(S_n\to V_p\) (\(V_p\) finite), \(E_n\subseteq S_n\times S_n\) a binary relation, and \(\mathrm{Adm}_n=\{s\in S_n\mid\forall c\in C,\,c(s)\}\).

Equivalence: \(s\sim_n s'\) iff \(\forall p\in P_n,\,p(s)=p(s')\). Classes: \([S_n]_\sim=\{[s]\mid s\in S_n\}\).

**Primitives (choice point: order of application within one \(U_n\))**

- **COMPRESSION** (\(P_n\mapsto P_n'\subset P_n\)): new \(\sim'\) coarser. Map \(\pi:S_n\to S_{n+1}=S_n/\sim'\) the quotient projection. \(E_{n+1}=\{(\pi(s),\pi(s'))\mid(s,s')\in E_n\}\). \(\mathrm{Adm}_{n+1}=\pi(\mathrm{Adm}_n)\).

- **EXPANSION** (\(P_n\mapsto P_n\cup\{p_\mathrm{new}\}\)): new \(\sim'\) finer. \(S_{n+1}=S_n\), \(E_{n+1}=E_n\), \(\mathrm{Adm}_{n+1}=\mathrm{Adm}_n\).

- **WARPING**: replace \(E_n\) by arbitrary \(E_{n+1}\subseteq S_n\times S_n\). All else fixed.

- **FOLDING**: partial surjection \(\phi:S_n\rightharpoonup S_{n+1}\) with \(\mathrm{dom}(\phi)\supseteq\mathrm{Adm}_n\), \(\phi(s)=\phi(s')\) allowed for \(s\not\sim_n s'\). Push \(E_{n+1}=\{(\phi(s),\phi(s'))\mid(s,s')\in E_n,\,s,s'\in\mathrm{dom}(\phi)\}\). \(\mathrm{Adm}_{n+1}=\phi(\mathrm{Adm}_n)\). Probes transported by post-composition where defined.

- **REINDEXING**: bijection \(\rho:S_n\to S_{n+1}\). All structure transported by \(\rho\); \(P_{n+1}=\{p\circ\rho^{-1}\}\), etc.

\(U_n\) is any finite composition of the five.

**Invariants / Monotones (falsifiable claims)**

- COMPRESSION: \(|[S_{n+1}]|\le|[S_n]|\) (strict if any class merged). Entropy \(H(\{|c|\})\) of class-size multiset non-decreasing.
- EXPANSION: \(|[S_{n+1}]|\ge|[S_n]|\) (strict if split occurs). \(H\) non-increasing.
- WARPING: \(|S|\), \(|P|\), class sizes invariant. Number of strongly connected components of \(E\) may change arbitrarily.
- FOLDING: \(|S_{n+1}|\le|S_n|\). \(|\mathrm{Adm}_{n+1}|\le|\mathrm{Adm}_n|\). If \(\phi\) identifies distinct \(\sim\)-classes then \(|[S_{n+1}]|<|[S_n]|\).
- REINDEXING: all numeric invariants (\(|S|\), class sizes, \(|E|\), \(H\)) preserved.

**Ratchet condition**

A sequence \(U^{(1)},U^{(2)}\) is order-sensitive when \(U^{(2)}\circ U^{(1)}\ne U^{(1)}\circ U^{(2)}\) on the triple \((S,P,E)\). Finite witness: two concrete primitives (one COMPRESSION, one EXPANSION) whose successive application on a 4-element set with two probes yields distinct final class counts depending on order.

**Minimal fixture** (\(|S_0|=4\))

\(S_0=\{a,b,c,d\}\), \(P_0=\{p_1,p_2\}\) with \(p_1(a)=p_1(b)=0\), \(p_1(c)=p_1(d)=1\); \(p_2(a)=p_2(c)=0\), \(p_2(b)=p_2(d)=1\). Classes: four singletons. \(\mathrm{Adm}_0=S_0\). \(E_0=\emptyset\).

Step 1 COMPRESSION (drop \(p_2\)): two classes \(\{a,b\},\{c,d\}\).

Step 2 EXPANSION (add \(p_3\) splitting \(\{a,b\}\)): three classes.

Step 3 FOLDING (\(\phi(a)=\phi(c)=x\), \(\phi(b)=y\), \(\phi(d)=z\)): two classes, \(|\mathrm{Adm}|=2\).

Kill-controls:
- Compression fake: run Step 1, assert class count = 2; fails if count remains 4.
- Expansion fake: run Step 2, assert class count = 3; fails if count stays 2.
- Ratchet: apply COMPRESSION then EXPANSION vs. reverse; final class counts differ (2 vs. 3).

All quantities finite; every operation expressible by quantifier-free arithmetic on finite tables.