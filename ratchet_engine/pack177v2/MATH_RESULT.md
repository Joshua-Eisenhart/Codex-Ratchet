# Exact mathematical result

For each anonymous source \(s\), the returned data are finite records

\[
D_s\subseteq\mathbb F_2^3\times\mathbb F_2,
\qquad
(h_0,h_1,p;o).
\]

No rows from different sources are pooled for selection.

## Quotient completion

For every coordinate subset \(J\subseteq\{h_0,h_1,p\}\), project with
\(\pi_J\). The outcome factors through that quotient exactly when

\[
\pi_J(x)=\pi_J(y)\Longrightarrow o(x)=o(y)
\quad\text{for all observed }x,y.
\]

All eight subsets are enumerated. The inclusion-minimal sufficient subsets
form a plural antichain. Every coordinate in every retained minimum has a
concrete deletion witness.

The geometry co-view is the finite quotient incidence partition. The counting
co-view is computed on the same partition boundary:

\[
B_J=\prod_{c\in\pi_J(D_s)}
|\{o:(c,o)\in D_s\}|.
\]

For binary outcomes this is \(2^{n_J}\), where \(n_J\) is the number of
conflicting quotient cells. It counts deterministic sections compatible with
the observed quotient cells. It is not probability or thermodynamic entropy.

## Exact Boolean completion

Every Boolean map on three bits has a unique ANF:

\[
f(x)=\bigoplus_{A\subseteq\{0,1,2\}}c_A\prod_{i\in A}x_i.
\]

There are exactly \(2^8=256\) coefficient vectors. Pack 177 enumerates all of
them and keeps every map matching every record. It reports two explicit MSS
views: monomial-support inclusion and lexicographic `(degree, monomial count)`.

If identical full contexts have both outcomes, no deterministic map over the
returned coordinates can close. The exact observed continuation relation is
then retained; each edge has a deletion witness. This is not called a failed
source. It is a measured residual demanding either relational semantics or a
new, independently measured coordinate.

## Full-data result

| Anonymous source | Rows | Deterministic ANF survivors | Minimal coordinate antichain |
|---|---:|---:|---|
| `src-1858a5f7dbbb248f` | 12 | 8 | `{h0}` |
| `src-5cb0baaed60f7057` | 96 | 0 | relation remains |
| `src-9ec2675726f1c445` | 64 | 0 | relation remains |
| `src-b5d70477f00ce3f6` | 66 | 0 | relation remains |
| `src-bc7ff4b7cc12163d` | 256 | 0 | relation remains |
| `src-bd2e50ac87b07f6c` | 5 | 64 | `{h0}`, `{h1}`, `{p}` |
| `src-d52c7f63b586c435` | 35 | 16 | `{h0,h1}`, `{h0,p}`, `{h1,p}` |
| `src-d96fbba7308dd1d5` | 16,384 | 0 | relation remains |

The contextuality projection has 16 train survivors; held-out return kills 8,
leaving the 8 reported above. Those eight killed candidates are parked and
universally eligible after a material context change.

The 16,384-row source has exactly one source-level frontier, not 16,384 votes.
Uniformly duplicating any source's rows leaves its frontier unchanged.

