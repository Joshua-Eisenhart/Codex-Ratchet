# Authoritative Julia leg for the cut_dependent_entropy arrow — QuantumOptics.jl.
# Carries the SIGNED-correlation witness: negative conditional entropy S(A|B) is
# born at the tensor cut, and marginalization forgets it. numpy is control.
using QuantumOptics
using JSON

b = SpinBasis(1//2)
up = spinup(b); dn = spindown(b)

# Bell state and the product of its own marginals (identical marginals, different correlation)
bell = normalize(tensor(up, up) + tensor(dn, dn))
rho_bell = dm(bell)
rho_A = ptrace(rho_bell, 2)   # keep A (subsystem 1)
rho_B = ptrace(rho_bell, 1)   # keep B (subsystem 2)
rho_prod = tensor(rho_A, rho_B)   # product of the marginals: same marginals, zero correlation

nats2bits = 1.0 / log(2.0)

S_AB_bell  = real(entropy_vn(rho_bell)) * nats2bits        # 0
S_A        = real(entropy_vn(rho_A))    * nats2bits        # 1 bit
S_B        = real(entropy_vn(rho_B))    * nats2bits        # 1 bit
S_AB_prod  = real(entropy_vn(rho_prod)) * nats2bits        # 2 bits

S_cond_bell = S_AB_bell - S_B      # S(A|B) on Bell = -1 bit  (NEGATIVE -> no classical shadow)
S_cond_prod = S_AB_prod - S_B      # S(A|B) on product = +1 bit
I_bell = S_A + S_B - S_AB_bell     # mutual info Bell = 2 bits
I_prod = S_A + S_B - S_AB_prod     # mutual info product = 0

marg_gap = tracedistance(ptrace(rho_bell,2), ptrace(rho_prod,2)) +
           tracedistance(ptrace(rho_bell,1), ptrace(rho_prod,1))

out = Dict(
    "engine" => "julia:QuantumOptics",
    "s_cond_bell_bits" => S_cond_bell,
    "s_cond_product_bits" => S_cond_prod,
    "mutual_info_bell_bits" => I_bell,
    "mutual_info_product_bits" => I_prod,
    "marginal_gap_bell_vs_product" => marg_gap,
    "s_cond_bell_is_negative" => (S_cond_bell < -1e-9),
    "born_at_cut_witness" => (marg_gap < 1e-9) && (abs(I_bell - I_prod) > 0.5) && (S_cond_bell < -1e-9),
)
println(JSON.json(out))
