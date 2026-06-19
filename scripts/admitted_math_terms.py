#!/usr/bin/env python3
"""Definedness registry for math-surface language gates.

CEILING: this module is a LANGUAGE/definedness registry only. It says whether
a token is admitted standard math/physics vocabulary, schema plumbing, owner
jargon, or undefined. It does NOT judge mathematical correctness,
constraint-admissibility, evidence strength, promotion, or canonical status.
"""

from __future__ import annotations

import argparse
import re


L0_PRIMITIVES: dict[str, str] = {
    "finite": "Standard finiteness condition used throughout finite-dimensional mathematics and physics.",
    "dimensional": "Standard adjective for vector-space and Hilbert-space dimension.",
    "hilbert": "Hilbert spaces are standard state spaces in functional analysis and quantum theory.",
    "space": "Standard mathematical term for a structured set such as a vector, Hilbert, or topological space.",
    "density": "Density matrices are standard quantum states represented by positive trace-one operators.",
    "matrix": "Matrices are standard linear-algebra objects representing linear maps and operators.",
    "operator": "Operators are standard maps on vector or Hilbert spaces.",
    "channel": "Quantum channels are standard completely positive trace-preserving maps.",
    "cptp": "CPTP abbreviates completely positive trace-preserving, standard for quantum channels.",
    "unitary": "Unitary operators are standard norm-preserving Hilbert-space automorphisms.",
    "lindblad": "Lindblad generators are standard generators of Markovian open quantum dynamics.",
    "hamiltonian": "Hamiltonians are standard energy operators and dynamics generators in physics.",
    "commutator": "Commutators are standard algebraic brackets AB-BA.",
    "anticommutator": "Anticommutators are standard algebraic brackets AB+BA.",
    "trace": "Trace is the standard sum of diagonal entries or operator trace.",
    "partial": "Partial operations such as partial trace are standard in tensor-product systems.",
    "tensor": "Tensor products are standard multilinear constructions for composite systems.",
    "superoperator": "Superoperators are standard linear maps acting on operators.",
    "generator": "Generators are standard infinitesimal descriptions of dynamics or transformations.",
}


ADMITTED_EXTENSIONS: dict[str, str] = {
    "eigenvalue": "Standard scalar associated with an eigenvector of a linear operator.",
    "eigenvector": "Standard nonzero vector mapped to a scalar multiple by an operator.",
    "spectrum": "Standard set or multiset of operator eigenvalues.",
    "eigendecomposition": "Standard decomposition of an operator into eigen-data.",
    "schmidt": "Schmidt decomposition and Schmidt rank are standard bipartite quantum notions.",
    "rank": "Rank is a standard linear-algebra invariant.",
    "purity": "Purity is a standard trace-based quantum-state quantity.",
    "negativity": "Negativity is a standard entanglement measure.",
    "entropy": "Entropy is a standard information-theoretic and thermodynamic quantity.",
    "vonneumann": "Von Neumann entropy is a standard quantum entropy.",
    "von": "Component of the standard phrase von Neumann entropy.",
    "neumann": "Component of the standard phrase von Neumann entropy.",
    "shannon": "Shannon entropy is a standard classical information entropy.",
    "mutual": "Mutual information is a standard information-theoretic quantity.",
    "information": "Information is standard in information theory.",
    "conditional": "Conditional entropy/information are standard information-theoretic quantities.",
    "coherent": "Coherent information is a standard quantum information quantity.",
    "relative": "Relative entropy is a standard divergence in information theory.",
    "quotient": "Quotients are standard constructions by equivalence relations.",
    "equivalence": "Equivalence relations are standard reflexive-symmetric-transitive relations.",
    "partition": "Partitions are standard decompositions into disjoint blocks.",
    "kernel": "Kernels are standard algebraic or linear-map null structures.",
    "probe": "Probe is standard terminology for a measurement or test object.",
    "family": "Families are standard indexed collections of mathematical objects.",
    "distinguishability": "Distinguishability is standard in statistics and quantum information.",
    "indistinguishability": "Indistinguishability is standard equivalence under a probe family.",
    "marginal": "Marginals are standard reduced distributions or reduced states.",
    "projection": "Projections are standard idempotent linear maps or geometric maps.",
    "map": "Maps are standard mathematical functions between sets or spaces.",
    "maps": "Plural map terminology for computed functions.",
    "bloch": "Bloch vectors/spheres are standard one-qubit state representations.",
    "pauli": "Pauli matrices are standard quantum spin operators.",
    "sigma": "Sigma is standard notation for maps, Pauli matrices, and algebraic symbols.",
    "spinor": "Spinors are standard geometric and quantum objects.",
    "weyl": "Weyl spinors/operators are standard in geometry and quantum theory.",
    "chirality": "Chirality is standard handedness terminology in geometry and physics.",
    "hopf": "Hopf fibration and Hopf-related structures are standard topology.",
    "fibration": "Fibrations are standard topology and geometry structures.",
    "connection": "Connections are standard geometric structures for transport/differentiation.",
    "curvature": "Curvature is a standard geometric invariant of a connection or metric.",
    "holonomy": "Holonomy is standard parallel-transport data around loops.",
    "clifford": "Clifford algebras are standard algebraic structures.",
    "octonion": "Octonions are standard non-associative division algebra objects.",
    "quaternion": "Quaternions are standard noncommutative division algebra objects.",
    "lie": "Lie groups and Lie algebras are standard continuous symmetry structures.",
    "group": "Groups are standard algebraic symmetry structures.",
    "orthogonal": "Orthogonal groups and maps are standard metric-preserving structures.",
    "symplectic": "Symplectic geometry/groups are standard Hamiltonian structures.",
    "su": "SU(n) is standard notation for special unitary groups.",
    "spin": "Spin groups and spinors are standard geometry/physics structures.",
    "pin": "Pin groups are standard Clifford-theoretic symmetry groups.",
    "g2": "G2 is a standard exceptional Lie group.",
    "f4": "F4 is a standard exceptional Lie group.",
    "jordan": "Jordan algebras are standard nonassociative algebraic structures.",
    "endofunction": "Endofunctions are standard functions from a set to itself.",
    "scc": "SCC abbreviates strongly connected component in graph theory.",
    "terminal": "Terminal classes/components are standard graph and Markov-chain terms.",
    "involution": "Involutions are standard self-inverse maps.",
    "radix": "Radix is standard positional-base terminology.",
    "graph": "Graphs are standard combinatorial objects.",
    "cell": "Cell complexes are standard topological/combinatorial structures.",
    "complex": "Complexes are standard algebraic/topological structures.",
    "transition": "Transition maps/tables are standard dynamics and automata terminology.",
    "table": "Tables are standard finite data representations of maps or relations.",
    "tables": "Plural table terminology for finite data representations.",
    "trajectory": "Trajectories are standard paths through a state or phase space.",
    "cycle": "Cycles are standard graph and dynamical-system structures.",
    "absorbing": "Absorbing states/classes are standard Markov-chain terminology.",
    "reachability": "Reachability is standard graph and transition-system terminology.",
    "bipartition": "Bipartitions are standard two-block partitions.",
    "cut": "Cuts are standard graph, partition, and information-splitting objects.",
    "cone": "Cones are standard convex/geometric structures.",
    "simplex": "Simplices/simplexes are standard convex and topological primitives.",
    "gkls": "GKLS generators are standard Gorini-Kossakowski-Lindblad-Sudarshan generators.",
    "kraus": "Kraus operators are standard operator-sum representations of quantum channels.",
    "povm": "POVMs are standard positive operator-valued quantum measurements.",
    "effect": "Effects are standard positive operators in quantum measurement theory.",
    "observable": "Observables are standard measurable/operator quantities.",
    "expectation": "Expectations are standard averages of random variables or observables.",
    "expectations": "Plural expectation terminology for computed observable averages.",
    "lattice": "Lattices are standard ordered, algebraic, and geometric structures.",
    "form": "Forms are standard differential-geometric or multilinear objects.",
    "transpose": "Transpose and partial transpose are standard linear-algebra operations.",
    "state": "States are standard elements of a state space or quantum state objects.",
    "states": "Plural of standard state terminology.",
    "set": "Sets are the standard base objects of mathematics.",
    "size": "Size/cardinality is standard finite-set terminology.",
    "label": "Labels are standard indexing metadata for mathematical objects.",
    "labels": "Plural label terminology for indexed mathematical objects.",
    "class": "Equivalence classes are standard quotient structures.",
    "classes": "Plural class terminology for quotient/equivalence structures.",
    "count": "Counts/cardinalities are standard finite combinatorial quantities.",
    "counts": "Plural count terminology for finite combinatorial quantities.",
    "full": "Standard qualifier for complete/full data rather than a subset.",
    "through": "Standard range connective used in depth labels such as 1q through 4q.",
    "z2": "Z2 is standard notation for the cyclic group of order two.",
    "mod": "Modulo arithmetic is standard number theory.",
    "parity": "Parity is standard mod-two terminology.",
    "orbit": "Orbits are standard equivalence classes under group or map actions.",
    "equivariant": "Equivariant maps are standard maps compatible with an action.",
    "mixed": "Mixed structures such as mixed-radix coordinates are standard qualifiers.",
    "shape": "Shape is standard array/tensor/combinatorial metadata terminology.",
    "coordinate": "Coordinates are standard mathematical labels for positions/components.",
    "formula": "Formula is standard expression metadata.",
    "question": "Question/query metadata key for SMT proof rows.",
    "encoding": "Encoding metadata key for SMT proof rows.",
    "interpretation": "Interpretation metadata key for proof/result rows.",
    "real": "Real numbers and real-valued quantities are standard mathematics.",
    "vs": "Versus/comparison connective in result keys.",
    "structural": "Structural relation metadata key.",
    "axiom": "Axioms are standard mathematical assumptions.",
    "receipt": "Receipt metadata key for executable result evidence.",
    "note": "Note metadata key.",
    "exp": "Expectation/exponential abbreviation used in result keys.",
    "equal": "Equality is standard mathematical relation terminology.",
    "vector": "Vectors are standard linear-algebra objects.",
    "vectors": "Plural vector terminology.",
    "rational": "Rational numbers and rational coordinates are standard mathematics.",
    "rx": "Coordinate label for an x component in Bloch/vector data.",
    "ry": "Coordinate label for a y component in Bloch/vector data.",
    "rz": "Coordinate label for a z component in Bloch/vector data.",
    "x": "Standard coordinate/symbol label.",
    "y": "Standard coordinate/symbol label.",
    "z": "Standard coordinate/symbol label.",
    "rho": "Rho is standard notation for a density matrix or state.",
    "tr": "Tr is standard notation for trace.",
    "p": "Standard symbolic label in formulas and maps.",
    "q": "Standard symbolic label in formulas and maps.",
    "r": "Standard symbolic label in formulas and maps.",
    "l": "Standard left-label shorthand in paired structures.",
    "m": "Standard symbolic label in formulas and maps.",
    "k": "Standard index/symbol label.",
    "c": "Standard symbolic label in formulas and maps.",
    "d": "Standard derivative/symbol label.",
    "iff": "If-and-only-if is standard logical terminology.",
    "qubit": "Qubit is standard quantum-information terminology.",
    "matrices": "Plural matrix terminology.",
    "hermitian": "Hermitian matrices/operators are standard quantum linear algebra.",
    "psd": "PSD abbreviates positive semidefinite, standard matrix terminology.",
    "jacobian": "Jacobians are standard derivative matrices.",
    "autograd": "Autograd is standard automatic-differentiation tooling terminology.",
    "derivative": "Derivatives are standard calculus objects.",
    "delta": "Delta is standard notation for differences or Kronecker/Dirac deltas.",
    "identity": "Identity maps/relations are standard mathematical objects.",
    "selection": "Selection/projection terminology is standard for indexed components.",
    "dimension": "Dimension is a standard vector-space and state-space invariant.",
    "dim": "Common abbreviation for dimension in mathematical result keys.",
    "dimensions": "Plural dimension terminology for declared state or Hilbert dimensions.",
    "depth": "Depth is standard layered/indexed structure terminology for finite systems.",
    "rung": "Rung is plumbing for indexed finite-depth evidence rows.",
    "rungs": "Plural rung plumbing for indexed finite-depth evidence rows.",
    "lineage": "Evidence-lineage plumbing for derived mathematical artifacts.",
    "ancestry": "Evidence-ancestry plumbing for derived mathematical artifacts.",
    "fixed": "Standard qualifier for a fixed finite object or rung.",
    "affirmative": "Evidence-plumbing qualifier for non-denial lineage assertions.",
    "root": "Standard root/base terminology for foundational objects.",
    "surface": "Standard/plumbing term for an exposed result surface.",
    "by": "Standard relation connective in compound evidence keys.",
    "under": "Standard relation connective in compound evidence keys.",
    "of": "Standard relation connective in compound evidence keys.",
    "over": "Standard relation connective in compound evidence keys.",
    "to": "Standard relation connective in compound evidence keys.",
    "at": "Standard relation connective in compound evidence keys.",
    "per": "Standard per-object qualifier in result keys.",
    "non": "Standard negation prefix in result keys.",
    "anti": "Standard negation prefix in result keys.",
    "field": "Fields are standard algebraic structures and physics quantities.",
    "strength": "Field strength is standard gauge/curvature terminology.",
    "loop": "Loops are standard path and topology objects.",
    "integral": "Integrals are standard calculus and geometry quantities.",
    "wilson": "Wilson loops are standard gauge-theory observables.",
    "parallel": "Parallel transport is standard connection geometry terminology.",
    "transport": "Transport is standard geometric/dynamical terminology.",
    "correlation": "Correlation is a standard statistical/quantum information quantity.",
    "geometry": "Geometry is standard mathematical structure.",
    "compatible": "Compatibility is standard consistency terminology in mathematics.",
    "compatibility": "Compatibility is standard consistency terminology in mathematics.",
    "inverse": "Inverse maps/systems are standard mathematical structures.",
    "system": "Systems are standard mathematical/physical collections under study.",
    # --- Standard-math registry widening (over-rejection repair) ---
    # These are unambiguous standard math/physics/quantum-information/graph
    # terms that the corpus uses on its computational KEY surface and that the
    # registry was missing, causing legit sims to be rejected as "undefined".
    # Each is standard vocabulary, never owner jargon.
    "concurrence": "Concurrence is a standard two-qubit entanglement measure.",
    "maxmix": "Maximally-mixed state, standard quantum-information shorthand.",
    "nats": "Nats are the standard natural-log unit of entropy/information.",
    "bits": "Bits are the standard base-two unit of entropy/information.",
    "bit": "Bit is the standard base-two unit of information.",
    "mi": "MI is the standard abbreviation for mutual information.",
    "log": "Logarithm is a standard mathematical function.",
    "log2": "Base-two logarithm is standard in information theory.",
    "ln": "Natural logarithm is a standard mathematical function.",
    "exp": "Exponential is a standard mathematical function (already as abbreviation).",
    "fiber": "Fibers are standard fibration/bundle geometry objects.",
    "fibers": "Plural fiber terminology for fibration/bundle geometry.",
    "fibration": "Fibrations are standard topology and geometry structures.",
    "base": "Base spaces are standard fibration/bundle geometry objects.",
    "section": "Sections are standard bundle/sheaf geometry objects.",
    "bundle": "Bundles are standard geometric fiber structures.",
    "clique": "Cliques are standard complete-subgraph graph-theory objects.",
    "cliques": "Plural clique terminology for complete subgraphs.",
    "node": "Nodes are standard graph-theory vertices.",
    "nodes": "Plural node terminology for graph vertices.",
    "edge": "Edges are standard graph-theory objects.",
    "edges": "Plural edge terminology for graph objects.",
    "vertex": "Vertices are standard graph-theory objects.",
    "vertices": "Plural vertex terminology for graph objects.",
    "adjacency": "Adjacency matrices are standard graph-theory objects.",
    "incidence": "Incidence structures are standard combinatorial geometry objects.",
    "condensation": "Graph condensation is the standard SCC-quotient construction.",
    "reachable": "Reachability is standard graph and transition-system terminology.",
    "connected": "Connectivity is standard graph-theory terminology.",
    "communicating": "Communicating classes are standard Markov-chain terminology.",
    "defect": "Defect is standard terminology for a deviation/obstruction quantity.",
    "deviation": "Deviation is standard statistics/error terminology.",
    "residual": "Residuals are standard fit/error quantities.",
    "gap": "Gaps (spectral/order/energy) are standard quantitative invariants.",
    "bound": "Bounds are standard inequality/limit quantities.",
    "radius": "Radius is a standard geometric metric quantity.",
    "radii": "Plural radius terminology for geometric metrics.",
    "distance": "Distance is a standard metric quantity.",
    "norm": "Norms are standard linear-algebra magnitude functions.",
    "fro": "Frobenius norm abbreviation, standard matrix terminology.",
    "frobenius": "Frobenius norm/inner-product, standard matrix terminology.",
    "mean": "Mean is a standard statistical average.",
    "variance": "Variance is a standard statistical spread quantity.",
    "std": "Standard deviation abbreviation, standard statistics terminology.",
    "min": "Minimum is a standard extremal quantity.",
    "max": "Maximum is a standard extremal quantity (also infra).",
    "sum": "Sum is a standard arithmetic aggregation.",
    "avg": "Average abbreviation, standard statistics terminology.",
    "abs": "Absolute value is a standard mathematical operation.",
    "squared": "Squared/square are standard arithmetic operations.",
    "square": "Square/squared are standard arithmetic operations.",
    "sqrt": "Square root is a standard mathematical function.",
    "nonzero": "Nonzero is a standard qualifier for nonvanishing quantities.",
    "zero": "Zero is the standard additive identity / vanishing value.",
    "volume": "Volume is a standard geometric measure.",
    "area": "Area is a standard geometric measure.",
    "phase": "Phase is a standard complex-amplitude/geometric quantity.",
    "amplitude": "Amplitudes are standard quantum-state coefficients.",
    "coefficient": "Coefficients are standard linear-combination scalars.",
    "coefficients": "Plural coefficient terminology for linear-combination scalars.",
    "order": "Order is standard for group order, ordering relations, and indices.",
    "index": "Indices are standard enumeration/labelling integers.",
    "indices": "Plural index terminology.",
    "position": "Position is standard coordinate/index terminology.",
    "site": "Sites are standard lattice/spin-system positions.",
    "sites": "Plural site terminology for lattice positions.",
    "block": "Blocks are standard matrix/partition substructures.",
    "blocks": "Plural block terminology for matrix/partition substructures.",
    "left": "Left is a standard handedness/chirality position label (L).",
    "right": "Right is a standard handedness/chirality position label (R).",
    "plus": "Plus is a standard sign/orientation label (+).",
    "minus": "Minus is a standard sign/orientation label (-).",
    "sign": "Sign is a standard +/- orientation quantity.",
    "product": "Products are standard multiplicative constructions.",
    "prod": "Product abbreviation, standard arithmetic terminology.",
    "tensorproduct": "Tensor products are standard multilinear constructions.",
    "direct": "Direct sums/products are standard algebraic constructions.",
    "closure": "Closure is standard order/topology/algebra terminology.",
    "boundary": "Boundary is standard topology/chain-complex terminology.",
    "interior": "Interior is standard topology terminology.",
    "support": "Support is standard measure/function terminology.",
    "singleton": "Singletons are standard one-element sets/orbits.",
    "extension": "Extensions are standard algebraic/field constructions.",
    "restriction": "Restrictions are standard map-domain constructions.",
    "signature": "Signature is standard (metric/permutation/form) invariant terminology.",
    "negative": "Negative/positive are standard sign qualifiers.",
    "positive": "Positive is a standard sign/definiteness qualifier.",
    "pure": "Pure states are standard quantum-state terminology.",
    "representative": "Representatives are standard quotient-class terminology.",
    "carrier": "Carrier sets/algebras are standard underlying-structure terminology.",
    "global": "Global is a standard scope qualifier in geometry/topology.",
    "local": "Local is a standard scope qualifier in geometry/topology.",
    "concentric": "Concentric is standard geometric nesting terminology.",
    "nested": "Nesting is standard structural-containment terminology.",
    "nesting": "Nesting is standard structural-containment terminology.",
    "stack": "Stacks are standard layered/fibered structural terminology.",
    "stacked": "Stacked is standard layered structural terminology.",
    "layer": "Layers are standard layered structural terminology.",
    "layered": "Layered is standard structural terminology.",
    "pairing": "Pairings are standard bilinear/duality maps.",
    "dual": "Duals/dual spaces are standard linear-algebra constructions.",
    "commuting": "Commuting is standard operator-algebra terminology.",
    "noncommuting": "Noncommuting is standard operator-algebra terminology.",
    "anticommuting": "Anticommuting is standard operator-algebra terminology.",
    "commute": "Commute is standard operator-algebra terminology.",
    "commutative": "Commutative is standard algebra terminology.",
    "noncommutation": "Noncommutation is standard operator-algebra terminology.",
    "noncommute": "Noncommute is standard operator-algebra terminology.",
    "associative": "Associativity is standard algebra terminology.",
    "nonassociative": "Nonassociativity is standard algebra terminology.",
    "biseparable": "Biseparable is standard multipartite-entanglement terminology.",
    "separable": "Separable states are standard entanglement terminology.",
    "separability": "Separability is standard entanglement terminology.",
    "separation": "Separation is standard probe/distinguishability terminology.",
    "entangled": "Entangled states are standard quantum-information terminology.",
    "entanglement": "Entanglement is standard quantum-information terminology.",
    "tripartite": "Tripartite is standard multipartite terminology.",
    "bipartite": "Bipartite is standard two-party partition terminology.",
    "multipartite": "Multipartite is standard many-party partition terminology.",
    "marginals": "Marginals are standard reduced-state/distribution terminology.",
    "reduced": "Reduced density matrices are standard quantum terminology.",
    "ghz": "GHZ states are standard multiqubit entangled states.",
    "dicke": "Dicke states are standard symmetric multiqubit states.",
    "bell": "Bell states are standard maximally-entangled two-qubit states.",
    "w": "W states are standard multiqubit entangled states.",
    "ckw": "CKW (Coffman-Kundu-Wootters) monogamy is standard entanglement theory.",
    "monogamy": "Monogamy of entanglement is standard quantum-information theory.",
    "concurrences": "Plural concurrence terminology.",
    "syndrome": "Syndromes are standard error-correcting-code measurements.",
    "code": "Codes are standard error-correction/coding-theory objects.",
    "codeword": "Codewords are standard coding-theory objects.",
    "stabilizer": "Stabilizers are standard quantum-error-correction operators.",
    "parity": "Parity is standard mod-two/error-correction terminology.",
    "z4": "Z4 is standard notation for the cyclic group of order four.",
    "zn": "Zn is standard notation for a cyclic group of order n.",
    "so": "SO(n) is standard notation for special orthogonal groups.",
    "so3": "SO(3) is the standard rotation group of three-space.",
    "spinor": "Spinors are standard geometric and quantum objects.",
    "twistor": "Twistors are standard projective-geometry / spinor objects.",
    "chir": "Chir is the standard abbreviation for chirality (handedness).",
    "rotation": "Rotations are standard geometric transformations.",
    "reflection": "Reflections are standard geometric transformations.",
    "translation": "Translations are standard geometric transformations.",
    "theta": "Theta is standard angle notation.",
    "phi": "Phi is standard angle/scalar notation.",
    "eta": "Eta is standard parameter notation.",
    "chi": "Chi is standard parameter/character notation.",
    "psi": "Psi is standard state-vector notation.",
    "alpha": "Alpha is standard scalar/parameter notation.",
    "beta": "Beta is standard scalar/parameter notation.",
    "gamma": "Gamma is standard scalar/parameter and gamma-matrix notation.",
    "lambda": "Lambda is standard eigenvalue/parameter notation.",
    "mu": "Mu is standard index/parameter notation.",
    "nu": "Nu is standard index/parameter notation.",
    "pi": "Pi is the standard circle constant and projection notation.",
    "omega": "Omega is standard frequency/angular notation.",
    "epsilon": "Epsilon is standard small-quantity/Levi-Civita notation.",
    "kron": "Kron(ecker) product is a standard tensor-product matrix operation.",
    "kronecker": "Kronecker products/deltas are standard linear algebra.",
    "matmul": "Matrix multiplication is a standard linear-algebra operation.",
    "eigvals": "Eigenvalues abbreviation, standard linear algebra.",
    "eigvalsh": "Hermitian eigenvalues abbreviation, standard linear algebra.",
    "svd": "Singular value decomposition is standard linear algebra.",
    "svdvals": "Singular values abbreviation, standard linear algebra.",
    "diag": "Diagonal/diagonalization is standard linear algebra.",
    "diagonal": "Diagonal matrices are standard linear algebra.",
    "offdiagonal": "Off-diagonal entries are standard linear algebra.",
    "det": "Determinant abbreviation, standard linear algebra.",
    "determinant": "Determinants are standard linear-algebra invariants.",
    "rank": "Rank is a standard linear-algebra invariant (already present).",
    "nullspace": "Null spaces are standard linear-algebra subspaces.",
    "image": "Images are standard map-range structures.",
    "preimage": "Preimages are standard map-domain structures.",
    "basis": "Bases are standard vector-space spanning sets.",
    "span": "Spans are standard linear-combination subspaces.",
    "orthonormal": "Orthonormal bases are standard inner-product structures.",
    "projector": "Projectors are standard idempotent self-adjoint operators.",
    "idempotent": "Idempotents are standard algebraic self-square elements.",
    "involutive": "Involutive maps are standard self-inverse structures.",
    "equivariance": "Equivariance is standard symmetry-compatibility terminology.",
    "invariant": "Invariants are standard quantities preserved under maps.",
    "invariance": "Invariance is standard symmetry-preservation terminology.",
    "conserved": "Conserved quantities are standard physics invariants.",
    "conservation": "Conservation is standard physics-invariant terminology.",
    "symmetry": "Symmetries are standard transformation-group structures.",
    "asymmetric": "Asymmetric is standard relation/structure terminology.",
    "symmetric": "Symmetric is standard relation/matrix terminology.",
    "reflexive": "Reflexive is standard relation-property terminology.",
    "transitive": "Transitive is standard relation-property terminology.",
    "preorder": "Preorders are standard reflexive-transitive relations.",
    "poset": "Posets are standard partially-ordered sets.",
    "modulus": "Modulus is standard absolute-value/modular terminology.",
    "digit": "Digits are standard positional-numeral components.",
    "carry": "Carry is standard positional-arithmetic terminology.",
    "operation": "Operations are standard algebraic maps.",
    "operations": "Plural operation terminology.",
    "orientation": "Orientation is standard geometric/sign terminology.",
    "membership": "Membership is standard set-theory terminology.",
    "cardinality": "Cardinality is standard set-size terminology.",
    "disjoint": "Disjoint is standard set-theory terminology.",
    "subset": "Subsets are standard set-theory objects.",
    "superset": "Supersets are standard set-theory objects.",
    "tuple": "Tuples are standard finite ordered collections.",
    "tuples": "Plural tuple terminology.",
    "pair": "Pairs are standard two-element ordered collections.",
    "pairs": "Plural pair terminology.",
    "triple": "Triples are standard three-element ordered collections.",
    "constant": "Constants are standard fixed mathematical quantities.",
    "linear": "Linear is standard algebra terminology (also infra).",
    "bilinear": "Bilinear maps are standard multilinear-algebra objects.",
    "multilinear": "Multilinear maps are standard tensor-algebra objects.",
    "convex": "Convex sets/combinations are standard geometry/optimization.",
    "extreme": "Extreme points are standard convex-geometry objects.",
    "ray": "Rays are standard convex-cone/geometry objects.",
    "rays": "Plural ray terminology for convex-cone geometry.",
    "facet": "Facets are standard polytope-geometry objects.",
    "polytope": "Polytopes are standard convex-geometry objects.",
    "additive": "Additivity is standard map-property terminology.",
    "additivity": "Additivity is standard map-property terminology.",
    "multiplicative": "Multiplicativity is standard map-property terminology.",
    "homomorphism": "Homomorphisms are standard structure-preserving maps.",
    "isomorphism": "Isomorphisms are standard structure-preserving bijections.",
    "endomorphism": "Endomorphisms are standard self-maps of a structure.",
    "endomorphisms": "Plural endomorphism terminology.",
    "automorphism": "Automorphisms are standard structure-preserving self-bijections.",
    "morphism": "Morphisms are standard category-theory maps.",
    "functor": "Functors are standard category-theory maps.",
    "category": "Categories are standard abstract-structure collections.",
    "limit": "Limits are standard analysis/category-theory constructions.",
    "colimit": "Colimits are standard category-theory constructions.",
    "tower": "Towers are standard inverse/direct-system constructions.",
    "filtration": "Filtrations are standard nested-subobject sequences.",
    "stratified": "Stratification is standard decomposition terminology.",
    "strata": "Strata are standard stratification components.",
    "alphabet": "Alphabets are standard formal-language/automata symbol sets.",
    "string": "Strings are standard formal-language symbol sequences.",
    "word": "Words are standard formal-language symbol sequences.",
    "letter": "Letters are standard formal-language alphabet symbols.",
    "readout": "Readout is standard measurement-output terminology.",
    "threshold": "Thresholds are standard cutoff quantities.",
    "weight": "Weights are standard scalar coefficients / Hamming weights.",
    "weights": "Plural weight terminology.",
    "uniform": "Uniform distributions/measures are standard.",
    "distribution": "Distributions are standard probability objects.",
    "distributions": "Plural distribution terminology.",
    "probability": "Probability is standard measure-theoretic terminology.",
    "stochastic": "Stochastic maps/matrices are standard probability objects.",
    "markov": "Markov chains/processes are standard stochastic dynamics.",
    "transient": "Transient states are standard Markov-chain terminology.",
    "recurrent": "Recurrent states are standard Markov-chain terminology.",
    "componentwise": "Componentwise operations are standard elementwise maps.",
    "elementwise": "Elementwise operations are standard array maps.",
    "pointwise": "Pointwise operations are standard function-space maps.",
    "ket": "Kets are standard Dirac-notation state vectors.",
    "bra": "Bras are standard Dirac-notation dual vectors.",
    "braket": "Bra-kets are standard Dirac inner products.",
    "overlap": "Overlaps are standard inner-product fidelity quantities.",
    "fidelity": "Fidelity is a standard quantum-state similarity measure.",
    "ix": "Pauli-string label (I/X tensor word), standard quantum notation.",
    "iy": "Pauli-string label, standard quantum notation.",
    "iz": "Pauli-string label, standard quantum notation.",
    "xx": "Pauli-string label, standard quantum notation.",
    "xy": "Pauli-string label, standard quantum notation.",
    "xz": "Pauli-string label, standard quantum notation.",
    "yx": "Pauli-string label, standard quantum notation.",
    "yy": "Pauli-string label, standard quantum notation.",
    "yz": "Pauli-string label, standard quantum notation.",
    "zx": "Pauli-string label, standard quantum notation.",
    "zy": "Pauli-string label, standard quantum notation.",
    "zz": "Pauli-string label, standard quantum notation.",
}


JARGON_REJECT: dict[str, str] = {
    "terrain": "Owner coinage/project nickname, not an admitted math primitive.",
    "engine_tier": "Project tier claim, not a standard math primitive.",
    "tier": "Project tier/claim word, not admitted math language.",
    "terrain_engine": "Project compound carrying owner jargon.",
    "engine_consensus": "Project claim/tier wording outside the exact envelope key.",
    "axis0": "Project nickname/symbol, not a standard math primitive.",
    "axis": "Project noun usage, not a standard math primitive.",
    "basin": "Project noun usage here, not admitted as a primitive.",
    "ratchet": "Project-as-noun/owner coinage, not admitted math language here.",
    "gcm": "Project acronym, not admitted standard math language.",
    "rpf": "Project acronym, not admitted standard math language.",
    "retrocausal": "Project framing term, not admitted as a math primitive.",
    "possibility_field": "Owner coinage, not standard math language.",
    "holodeck": "Project nickname, not standard math language.",
    "rosetta": "Project nickname, not standard math language.",
    "allostatic": "Project nickname here, not admitted math language.",
    "homeostatic": "Project nickname here, not admitted math language.",
    "overlay": "Project noun usage here, not admitted math language.",
    "wiggle": "Owner nickname, not standard math language.",
    "conflation": "Project diagnostic nickname, not standard math language.",
    "phi0": "Coined symbol in this project surface, not admitted as a primitive.",
    "xi": "Coined symbol in this project surface, not admitted as a primitive.",
    "b6": "Coined symbol in this project surface, not admitted as a primitive.",
    "stage": "Project noun usage, not admitted math language.",
    "shell": "Project noun usage, not admitted math language.",
    "runtime": "Project noun usage, not admitted math language except exact infra keys.",
    "flux": "Runtime/project noun usage, not admitted math language here.",
    "se": "MBTI cognitive-function nickname, not admitted math language.",
    "ne": "MBTI cognitive-function nickname, not admitted math language.",
    "ni": "MBTI cognitive-function nickname, not admitted math language.",
    "si": "MBTI cognitive-function nickname, not admitted math language.",
    "te": "MBTI cognitive-function nickname, not admitted math language.",
    "ti": "MBTI cognitive-function nickname, not admitted math language.",
    "fe": "MBTI cognitive-function nickname, not admitted as a bare token.",
    "fi": "MBTI cognitive-function nickname, not admitted math language.",
}


INFRASTRUCTURE_EXEMPT: dict[str, str] = {
    "engine": "Bare backend leg label.",
    "julia": "Backend/runtime label for the Julia leg.",
    "jax": "Backend/runtime label for the JAX leg.",
    "pytorch": "Backend/runtime label for the PyTorch leg.",
    "engines": "Exact envelope infrastructure key.",
    "engine_values": "Exact envelope infrastructure key.",
    "engine_rows_match": "Exact envelope infrastructure key.",
    "engine_consensus": "Exact envelope infrastructure key when used exactly.",
    "canon_runtime": "Exact envelope infrastructure key.",
    "foreign_runtime": "Exact envelope infrastructure key.",
    "schema": "Schema identifier key.",
    "spec": "Specification identifier/key plumbing.",
    "codex": "Schema namespace component.",
    "ratchet": "Schema namespace component only.",
    "result": "Result schema/file plumbing term.",
    "results": "Result schema/file plumbing term.",
    "sim": "Simulation identifier/key plumbing.",
    "description": "Description metadata key.",
    "id": "Generic identifier plumbing term.",
    "identifier": "Generic identifier plumbing term.",
    "identifiers": "Generic identifier plumbing term.",
    "expected": "Expected-value/schema plumbing term for fixture assertions.",
    "version": "Version metadata key.",
    "classification": "Classification metadata key.",
    "scratch": "Scratch diagnostic classification value.",
    "diagnostic": "Scratch diagnostic classification value.",
    "promotion": "Promotion metadata key.",
    "allowed": "Boolean permission metadata key.",
    "formal": "Formal admission metadata key.",
    "admission": "Admission metadata key.",
    "claim": "Claim metadata key.",
    "ceiling": "Claim-ceiling metadata key.",
    "path": "Path metadata key.",
    "source": "Source metadata key.",
    "sha": "Hash metadata key.",
    "sha256": "Hash metadata key.",
    "json": "JSON serialization metadata key.",
    "date": "Date metadata key.",
    "dates": "Date metadata key.",
    "generated": "Generated-at metadata key.",
    "computation": "Computation metadata key.",
    "style": "Style metadata key.",
    "styles": "Style metadata key.",
    "package": "Package metadata key.",
    "packages": "Package metadata key.",
    "versions": "Package version metadata key.",
    "used": "Tool-use metadata key.",
    "tried": "Tool-use metadata key.",
    "reason": "Tool-manifest reason metadata key.",
    "tool": "Tool metadata key.",
    "tools": "Tool metadata key.",
    "manifest": "Tool manifest metadata key.",
    "integration": "Tool integration metadata key.",
    "depth": "Tool integration depth metadata key.",
    "load": "Load-bearing metadata key.",
    "bearing": "Load-bearing metadata key.",
    "supportive": "Tool integration depth value.",
    "aligned": "Tool alignment metadata key.",
    "reads": "Peer-read metadata key.",
    "peer": "Peer-read metadata key.",
    "all": "Boolean/plumbing qualifier.",
    "three": "Count/plumbing qualifier.",
    "agree": "Agreement metadata key.",
    "agreement": "Agreement metadata key.",
    "failure": "Failure metadata key.",
    "failures": "Failure metadata key.",
    "confirmed": "Confirmation metadata key.",
    "does": "Predicate metadata key.",
    "not": "Predicate metadata key.",
    "self": "Self-reference metadata key.",
    "upgrade": "Upgrade metadata key.",
    "max": "Maximum/error metadata key.",
    "err": "Error metadata key abbreviation.",
    "error": "Error metadata key.",
    "smt": "SMT solver metadata key.",
    "sat": "SMT satisfiable verdict.",
    "unsat": "SMT unsatisfiable verdict.",
    "cvc5": "CVC5 solver label.",
    "cvc": "CVC solver label component.",
    "z3": "Z3 solver label.",
    "torch": "PyTorch package/module label.",
    "numpy": "NumPy package/module label.",
    "networkx": "NetworkX package/module label.",
    "linear": "Linear algebra package/component label.",
    "algebra": "Algebra package/component label.",
    "eigen": "Eigenvalue/eigenvector prefix.",
    "eigenvalues": "Plural eigenvalue terminology.",
    "trace": "Trace metadata token.",
    "traces": "Plural trace metadata token.",
    "floor": "Floor/root-rung metadata token.",
    "foundation": "Foundation/root-rung metadata token.",
    "erased": "Erased-control metadata token.",
    "flip": "Flip/control metadata token.",
    "pair": "Pair metadata token.",
    "v": "Version schema component.",
    "all": "Boolean/plumbing qualifier.",
    "pass": "Boolean/plumbing qualifier.",
    "passes": "Boolean/plumbing qualifier.",
    "ok": "Boolean/plumbing qualifier.",
    "true": "Boolean literal.",
    "false": "Boolean literal.",
    "value": "Generic result value plumbing term.",
    "values": "Generic result value plumbing term.",
    "row": "Generic tabular plumbing term.",
    "rows": "Generic tabular plumbing term.",
    "match": "Generic equality/check plumbing term.",
    "matches": "Generic equality/check plumbing term.",
    "computed": "Generic computed-output qualifier.",
    "compute": "Generic computation qualifier.",
    "output": "Generic output plumbing term.",
    "outputs": "Generic output plumbing term.",
    "input": "Generic input plumbing term.",
    "inputs": "Generic input plumbing term.",
    "definition": "Generic definition/evidence plumbing term.",
    "predicate": "Generic predicate/formula plumbing term.",
    "id": "Generic identifier plumbing term.",
    "is": "Generic predicate/schema connective.",
}

EXACT_INFRA_KEYS = frozenset(
    {
        "engines",
        "engine_values",
        "engine_rows_match",
        "engine_consensus",
        "canon_runtime",
        "foreign_runtime",
        "schema",
    }
)

_NUMBER_RE = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?", re.IGNORECASE)
_CAMEL_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def admitted_terms() -> frozenset[str]:
    return frozenset(L0_PRIMITIVES) | frozenset(ADMITTED_EXTENSIONS)


def _is_number(tok: str) -> bool:
    return bool(_NUMBER_RE.fullmatch(tok.strip()))


def split_identifier(identifier: str) -> list[str]:
    spaced = _CAMEL_RE.sub("_", identifier)
    raw = [t for t in re.split(r"[^A-Za-z0-9]+", spaced.lower()) if t]
    pieces: list[str] = []
    for t in raw:
        pieces.append(t)
        if re.fullmatch(r"[a-z]\d+", t) or re.fullmatch(r"[fn]\d+", t):
            continue
        stripped = t.rstrip("0123456789")
        if stripped and stripped != t:
            pieces.append(stripped)
    return pieces


def _jargon_bases(tok: str) -> list[str]:
    low = tok.strip().lower()
    bases = [low]
    stripped = low.rstrip("0123456789")
    if stripped and stripped != low:
        bases.append(stripped)
    return bases


def is_jargon_token(tok: str) -> bool:
    return any(base in JARGON_REJECT for base in _jargon_bases(tok))


def is_admitted_token(tok: str) -> bool:
    low = tok.strip().lower()
    if is_jargon_token(low) and low not in EXACT_INFRA_KEYS:
        return False
    if re.fullmatch(r"\d+q", low):
        return True
    if re.fullmatch(r"[a-z]\d+", low):
        return True
    if re.fullmatch(r"[fn]\d+", low):
        return True
    return low in admitted_terms() or low in INFRASTRUCTURE_EXEMPT or _is_number(low)


def classify_token(tok: str) -> str:
    if is_admitted_token(tok):
        return "admitted"
    if is_jargon_token(tok):
        return "jargon"
    return "undefined"


# Tokens that are admitted as a BARE leg/infra label but must NOT silently
# admit a multi-token COMPOUND. `engine` is the project "engine-tier" jargon
# object: bare `engine` (value jax/julia/pytorch), `engine_leg*`, and the exact
# envelope infra keys are exempted by the callers' `_engine_token_exempt` /
# EXACT_INFRA_KEYS check BEFORE `is_admitted_compound` is consulted, so any
# `engine_*` compound reaching here (engine_stack, engine_comparison,
# engine_tier, terrain_engine, ...) must fall through to the per-token jargon
# walk rather than be wholesale-admitted. This preserves the caught-hack fix
# while the registry widening admits genuine standard-math compound tokens.
COMPOUND_NONADMITTING_PIECES = frozenset({"engine"})


def is_admitted_compound(identifier: str, *, split_fn=None) -> bool:
    ident = identifier.strip().lower()
    if not ident:
        return False
    if ident in EXACT_INFRA_KEYS:
        return True
    pieces = list((split_fn or split_identifier)(identifier))
    if not pieces:
        return False
    # A multi-piece compound carrying `engine` is never wholesale-admitted: the
    # bare/leg/infra exemptions are handled upstream, so anything reaching here
    # with an `engine` component is the compound jargon object and must be
    # token-walked (where it is flagged).
    distinct = {p for p in pieces if p}
    if len(distinct) > 1 and distinct & COMPOUND_NONADMITTING_PIECES:
        return False
    idx = 0
    consumed = False
    while idx < len(pieces):
        piece = pieces[idx]
        if not piece:
            idx += 1
            continue
        if piece == "fe" and idx + 1 < len(pieces) and pieces[idx + 1] == "lattice":
            idx += 2
            consumed = True
            continue
        if not is_admitted_token(piece):
            return False
        consumed = True
        idx += 1
    return consumed


def _selftest() -> int:
    failures: list[str] = []

    for tok in L0_PRIMITIVES:
        if classify_token(tok) != "admitted":
            failures.append(f"L0 not admitted: {tok}")
    for tok in ADMITTED_EXTENSIONS:
        if classify_token(tok) != "admitted":
            failures.append(f"extension not admitted: {tok}")
    for tok in JARGON_REJECT:
        if tok == "engine_consensus":
            continue
        if classify_token(tok) != "jargon":
            failures.append(f"jargon not rejected: {tok} -> {classify_token(tok)}")
    if classify_token("florble") != "undefined":
        failures.append("dummy coinage florble should be undefined")
    for num in ("0", "1", "1.5", ".25", "3e-4"):
        if not is_admitted_token(num):
            failures.append(f"number not admitted: {num}")
    for ident in (
        "von_neumann_entropy",
        "partial_transpose",
        "mutual_information",
        "connection_1_form",
        "schmidt_rank",
        "fe_lattice",
        "fe-lattice",
    ):
        if not is_admitted_compound(ident):
            failures.append(f"compound should be admitted: {ident}")
    for ident in ("terrain_engine", "axis0_predicate", "basin_id", "engine_leg_tier"):
        if is_admitted_compound(ident):
            failures.append(f"compound should NOT be admitted: {ident}")
    for ident in (
        "engine",
        "engines",
        "engine_values",
        "engine_rows_match",
        "engine_consensus",
        "canon_runtime",
        "foreign_runtime",
    ):
        if not is_admitted_compound(ident):
            failures.append(f"infra key should be exempt: {ident}")
    if classify_token("fe") != "jargon":
        failures.append("bare fe should remain MBTI jargon")

    if failures:
        print("SELFTEST FAILED")
        for failure in failures:
            print("  -", failure)
        return 1
    print("SELFTEST PASSED")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Admitted math term registry.")
    parser.add_argument("--selftest", action="store_true", help="run built-in self-test and exit")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
