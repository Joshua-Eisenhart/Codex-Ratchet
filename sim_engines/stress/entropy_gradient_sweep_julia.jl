# Julia cross-check leg for the unofficial entropy-gradient stress probe.
# Computes S(A|B) in bits for |psi(theta)> = cos(theta)|00> + sin(theta)|11>
# at the thetas given as ARGS, via QuantumOptics (separate process from JAX).
using QuantumOptics
using JSON

b = SpinBasis(1//2)
up = spinup(b); dn = spindown(b)
nats2bits = 1.0 / log(2.0)

thetas = [parse(Float64, a) for a in ARGS]
vals = Float64[]
for th in thetas
    psi = normalize(cos(th) * tensor(up, up) + sin(th) * tensor(dn, dn))
    rho = dm(psi)
    s_ab = real(entropy_vn(rho)) * nats2bits
    s_b = real(entropy_vn(ptrace(rho, 1))) * nats2bits
    push!(vals, s_ab - s_b)
end
println(JSON.json(Dict("engine" => "julia:QuantumOptics", "theta" => thetas, "s_cond_bits" => vals)))
