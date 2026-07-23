# Authoritative Julia leg for the extension_fibre_capacity arrow — QuantumOptics.jl.
# Independent recompute, no echo: rebuilds the 8-member joint candidate family,
# recomputes every B-marginal via QuantumOptics' own ptrace, re-enumerates the
# extension fibres, and recomputes the Hartley/Renyi-0 capacities kappa = log|fibre|.
using QuantumOptics
using JSON

b = SpinBasis(1//2)
k0 = spinup(b); k1 = spindown(b)

# entangled(t) = cos(t)|01> + sin(t)|10> (A first, B second), as a density operator.
joint_pure(t) = dm(cos(t) * tensor(k0, k1) + sin(t) * tensor(k1, k0))

eye_half = dense(identityoperator(b)) / 2
bell = joint_pure(pi / 4)
product_maxmixed = tensor(eye_half, eye_half)
ccorr = 0.5 * joint_pure(0.0) + 0.5 * joint_pure(pi / 2)
werner_half = 0.5 * bell + 0.5 * product_maxmixed

# Same 8-member family, same order, as build_candidate_family() in the main sim.
family = [
    bell,                    # bell
    product_maxmixed,        # product_maxmixed
    ccorr,                   # ccorr
    werner_half,             # werner_half
    joint_pure(pi / 6),      # entangled_pi6
    joint_pure(pi / 3),      # entangled_pi3
    joint_pure(0.0),         # prod_pure_01
    joint_pure(pi / 2),      # prod_pure_10
]

# B-marginal via the restriction map: ptrace(rho, 1) traces out A, keeps B.
marginals = [ptrace(rho, 1) for rho in family]

maxmixed_target = eye_half
product_01_target = marginals[7]   # B-marginal of the |0>_A (x) |1>_B endpoint
product_10_target = marginals[8]   # B-marginal of the |1>_A (x) |0>_B endpoint

TOL = 1.0e-9
matches(m, target) = maximum(abs.(m.data - target.data)) < TOL
fibre_count(target) = count(m -> matches(m, target), marginals)

n_maxmixed = fibre_count(maxmixed_target)
n_product_01 = fibre_count(product_01_target)
n_product_10 = fibre_count(product_10_target)

out = Dict(
    "engine" => "julia:QuantumOptics",
    "kappa_maxmixed_nats" => log(n_maxmixed),
    "kappa_product_01_nats" => log(n_product_01),
    "kappa_product_10_nats" => log(n_product_10),
    "fibre_maxmixed_cardinality" => n_maxmixed,
    "fibre_product_01_cardinality" => n_product_01,
    "fibre_product_10_cardinality" => n_product_10,
)
println(JSON.json(out))
