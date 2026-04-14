"""Common carrier/admissibility encodings for pairwise coupling sims.

Each framework is projected onto a small integer carrier {0..4} with a
shell-local admissibility predicate drawn from its atom_7 claim:

  holodeck  : admissible iff state is "coherent" -> x in {0,1,2}
              (2-qubit sector; 3..4 are out-of-shell).
  igt       : yin/yang parity survivors -> x in {0,2,4} (even = WIN).
  leviathan : hierarchy order preserved  -> x in {1,2,3} (monopoly
              forbidden at extremes 0,4).
  sci_method: falsifiable window         -> x in {0,1,2,3} (x<4: probe
              reachable).
  fep       : Markov-blanket-stable      -> x in {1,2,3,4} (internal
              state bounded away from 0).

These sets were chosen to give nontrivial intersection structure so
that coupling predicates can discriminate interacting vs additive
pairs under z3 joint admissibility.
"""

FRAMEWORKS = {
    "holodeck":   lambda x: 0 <= x <= 2,
    "igt":        lambda x: x % 2 == 0 and 0 <= x <= 4,
    "leviathan":  lambda x: 1 <= x <= 3,
    "sci_method": lambda x: 0 <= x <= 3,
    "fep":        lambda x: 1 <= x <= 4,
}

DOMAIN = list(range(5))

# Coupling predicates: how the two frameworks interact when paired.
# Keyed by unordered pair (sorted tuple).  If the predicate is strictly
# less permissive than True, the pair is "genuinely interacting".
COUPLINGS = {
    # holodeck carrier must remain a coherent subsystem of the joint ->
    # no-cloning-style: x != y required when both nonzero.
    ("holodeck","igt"):        lambda x,y: not (x == y and x != 0),
    ("fep","holodeck"):        lambda x,y: x + y <= 4,           # blanket budget
    ("holodeck","leviathan"):  lambda x,y: x <= y,               # holodeck nested in hierarchy
    ("holodeck","sci_method"): lambda x,y: True,                  # additive (no interaction)
    ("igt","leviathan"):       lambda x,y: x + y != 4,           # anti-monopoly
    ("fep","igt"):             lambda x,y: (x + y) % 2 == 0,     # parity sync
    ("igt","sci_method"):      lambda x,y: True,                  # additive
    ("leviathan","sci_method"):lambda x,y: y <= x,               # probe below rank
    ("fep","leviathan"):       lambda x,y: x >= y,               # blanket absorbs hierarchy
    ("fep","sci_method"):      lambda x,y: x - y <= 2,           # bounded surprise
}

def pair_key(a, b):
    return tuple(sorted((a, b)))
