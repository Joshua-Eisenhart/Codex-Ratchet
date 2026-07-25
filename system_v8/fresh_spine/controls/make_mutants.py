#!/usr/bin/env python3
"""Write C2 KERNEL-MUTATION copies of the three lanes.

The originals are never edited. Each mutation is an exact string replacement on
a copy; if the anchor text is not found the script raises, so a mutation can
never be silently skipped and then reported as applied.

Two mutation families, both named in the control spec:
  c2a  the RANK call          -- the decisive operation behind f0_*_a2
  c2b  the ADJACENCY build    -- the decisive operation behind f2_*
"""

import pathlib
import sys

FS = pathlib.Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v8/fresh_spine")
MUT = FS / "controls" / "mutants"
MUT.mkdir(parents=True, exist_ok=True)

MUTATIONS = [
    # ---- jax -------------------------------------------------------------
    ("jax_lane.py", "c2a_rank_jax_lane.py",
     "@jax.jit\ndef rank_kernel(M):\n    return jnp.linalg.matrix_rank(M)\n",
     "@jax.jit\ndef rank_kernel(M):\n    return jnp.linalg.matrix_rank(M.at[0].set(0))\n",
     "rank kernel now ranks the field with row 0 zeroed"),
    ("jax_lane.py", "c2b_adj_jax_lane.py",
     '        A = jcall("jnp .at[].set (adjacency scatter k->j)", lambda: A.at[ib, ia].set(1))\n',
     "",
     "adjacency scatter k->j deleted; adjacency is no longer symmetric"),
    # ---- pytorch ---------------------------------------------------------
    ("pytorch_lane.py", "c2a_rank_pytorch_lane.py",
     "    A = M.clone()\n    n, m = A.shape\n",
     "    A = M.clone()\n    A[0] = 0\n    n, m = A.shape\n",
     "Bareiss rank now runs on the field with row 0 zeroed"),
    ("pytorch_lane.py", "c2b_adj_pytorch_lane.py",
     "        adj[E[:, 1], E[:, 0]] = 1\n",
     "",
     "adjacency back-scatter deleted; adjacency is no longer symmetric"),
    # ---- julia -----------------------------------------------------------
    ("julia_lane.jl", "c2a_rank_julia_lane.jl",
     "    A = copy(M)\n    nr, nc = size(A)\n",
     "    A = copy(M)\n    A[1, :] .= 0\n    nr, nc = size(A)\n",
     "exact_rank now ranks the matrix with row 1 zeroed"),
    ("julia_lane.jl", "c2b_adj_julia_lane.jl",
     "        Graphs.add_edge!(g, a + 1, b + 1)\n",
     "        Graphs.add_edge!(g, a + 1, mod1(b + 2, 16))\n",
     "adjacency build attaches every edge to the wrong head vertex"),
]


def main():
    for src, dst, anchor, repl, note in MUTATIONS:
        text = (FS / src).read_text()
        if anchor not in text:
            raise SystemExit("ANCHOR NOT FOUND in %s for %s" % (src, dst))
        if text.count(anchor) != 1:
            raise SystemExit("ANCHOR NOT UNIQUE in %s for %s (%d hits)"
                             % (src, dst, text.count(anchor)))
        out = text.replace(anchor, repl)
        if out == text:
            raise SystemExit("MUTATION WAS A NO-OP for %s" % dst)
        (MUT / dst).write_text(out)
        print("wrote %-32s  delta_bytes=%+d  %s" % (dst, len(out) - len(text), note))


if __name__ == "__main__":
    sys.exit(main())
