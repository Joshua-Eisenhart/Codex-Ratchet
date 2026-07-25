#!/usr/bin/env python3
"""Place lane copies into each control-fixture directory.

Two classes of edit, kept strictly separate and both declared:

  HARNESS edits   change only where a lane looks for its fixture, or the frozen
                  hash it compares against. They do not touch any computation.
  CARRIER edits   relax the n == 4 assertions and the hardcoded 16s in the julia
                  lane so a 3-cube can reach the arithmetic at all. Used only to
                  answer "do the numbers move", never to claim the unmodified
                  lane accepted a 3-cube.

Every replacement is anchored and asserted unique, so a skipped edit raises.
"""

import hashlib
import json
import pathlib
import shutil

FS = pathlib.Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v8/fresh_spine")
C = FS / "controls"

JAX_PATH_ANCHOR = (
    'FIXTURE_PATH = Path(\n'
    '    "/Users/joshuaeisenhart/Codex-Ratchet/system_v8/fresh_spine/fixture_v0.json"\n'
    ')\n'
)
JAX_PATH_REPL = 'FIXTURE_PATH = Path(__file__).resolve().parent / "fixture_v0.json"\n'

TORCH_SHA_ANCHOR = 'EXPECTED_FIXTURE_SHA256 = "1ce948f00d82729d2cd0056477ff55942a25efa394f6da11144253e8e60ff9da"\n'

# julia CARRIER relaxations, 4-cube -> 3-cube
JULIA_N3 = [
    ("@assert n == 4\n", "@assert n == 3\n"),
    ("@assert length(J) == 16\n", "@assert length(J) == 8\n"),
    ("@assert J == collect(0:15)\n", "@assert J == collect(0:7)\n"),
    ("F_diag = Matrix{Rational{BigInt}}(undef, 16, 16)\n",
     "F_diag = Matrix{Rational{BigInt}}(undef, 8, 8)\n"),
    ("F_coh  = Matrix{Rational{BigInt}}(undef, 16, 16)\n",
     "F_coh  = Matrix{Rational{BigInt}}(undef, 8, 8)\n"),
    ("nz_diag_unordered = count(!iszero, [F_diag[i, k] for i in 1:16 for k in i:16])\n",
     "nz_diag_unordered = count(!iszero, [F_diag[i, k] for i in 1:8 for k in i:8])\n"),
    ("nz_coh_unordered  = count(!iszero, [F_coh[i, k]  for i in 1:16 for k in i:16])\n",
     "nz_coh_unordered  = count(!iszero, [F_coh[i, k]  for i in 1:8 for k in i:8])\n"),
    ("    g = Graphs.SimpleGraph(16)\n", "    g = Graphs.SimpleGraph(8)\n"),
    ("ring_derived = sort([(min(gray_order[i], gray_order[mod1(i + 1, 16)]),\n"
     "                      max(gray_order[i], gray_order[mod1(i + 1, 16)])) for i in 1:16])\n",
     "ring_derived = sort([(min(gray_order[i], gray_order[mod1(i + 1, 8)]),\n"
     "                      max(gray_order[i], gray_order[mod1(i + 1, 8)])) for i in 1:8])\n"),
    ("sigma_is_bijection = sort(sigma_tab) == collect(0:15)\n",
     "sigma_is_bijection = sort(sigma_tab) == collect(0:7)\n"),
    ("sigma_matches_formula = all(sigma_tab[v+1] == mod(3v + 7, 16) for v in 0:15)\n",
     "sigma_matches_formula = all(sigma_tab[v+1] == mod(3v + 7, 8) for v in 0:7)\n"),
]


def edit(text, pairs, tag):
    for anchor, repl in pairs:
        if text.count(anchor) != 1:
            raise SystemExit("ANCHOR count %d (want 1) in %s for:\n%r"
                             % (text.count(anchor), tag, anchor[:80]))
        text = text.replace(anchor, repl)
    return text


def sha_of(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def place(subdir, carrier_relax=False):
    d = C / subdir
    fx_sha = sha_of(d / "fixture_v0.json")

    # jax : HARNESS edit only (its fixture path is an absolute literal)
    jx = edit((FS / "jax_lane.py").read_text(),
              [(JAX_PATH_ANCHOR, JAX_PATH_REPL)], subdir + "/jax")
    (d / "jax_lane.py").write_text(jx)

    # pytorch : verbatim copy first -- its sha gate is a real enforcement point
    shutil.copy2(FS / "pytorch_lane.py", d / "pytorch_lane.py")
    # and a second copy whose frozen sha is re-pointed at this fixture
    tx = edit((FS / "pytorch_lane.py").read_text(),
              [(TORCH_SHA_ANCHOR,
                'EXPECTED_FIXTURE_SHA256 = "%s"\n' % fx_sha)], subdir + "/torch")
    (d / "pytorch_lane_shaok.py").write_text(tx)

    # julia : verbatim copy first -- its n == 4 assertions are a real gate
    shutil.copy2(FS / "julia_lane.jl", d / "julia_lane.jl")
    if carrier_relax:
        jl = edit((FS / "julia_lane.jl").read_text(), JULIA_N3, subdir + "/julia")
        (d / "julia_lane_n3.jl").write_text(jl)

    print("%-20s fixture_sha=%s  files=%s"
          % (subdir, fx_sha[:16], sorted(p.name for p in d.iterdir())))


place("c3_n3", carrier_relax=True)
place("c4a_inconsistent")
place("c4b_consistent")
