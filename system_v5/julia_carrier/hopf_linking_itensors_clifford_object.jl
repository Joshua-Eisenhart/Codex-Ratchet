# GENUINE NON-NUMPY CARRIER (owner): Hopf linking-number = A-C log-negativity on an ITensors tensor network,
# with the SU(2) gauge built from a CliffordAlgebras rotor. Julia/ITensors (no numpy); CliffordAlgebras spinor.
using ITensors, ITensorMPS, CliffordAlgebras, LinearAlgebra, JSON

const cl = CliffordAlgebra(:Cl3)   # Cl(3,0): even subalgebra ~ SU(2) (the spinor rotors)

"SU(2) spinor matrix of a Cl(3) rotor R=exp(-θ/2 * (e_i e_j)); the Hopf/spinor gauge from geometric algebra."
function clifford_rotor_su2(theta, i, j)
    B = getproperty(cl, Symbol("e$i")) * getproperty(cl, Symbol("e$j"))   # bivector
    R = exp(-0.5*theta*B)
    # spinor rep: rotor acts as cos(θ/2)·I - sin(θ/2)·(unit bivector as Pauli). Extract via scalar+bivector coeffs.
    a = CliffordAlgebras.scalar(R)                 # cos(θ/2)
    # map e1e2->-iσz, e2e3->-iσx, e3e1->-iσy (standard Cl(3)+ ~ su(2))
    c12 = real(R.e1e2); c23 = real(R.e2e3); c31 = real(R.e3e1)
    σx=[0 1;1 0]; σy=[0 -im;im 0]; σz=[1 0;0 -1]
    return real(a)*[1 0;0 1] - im*(c12*σz + c23*σx + c31*σy)
end

function build(s, A, B, C, L, kind; gauge=false)
    psi = MPS(s, "0")
    for i in 1:L
        a=A[i]; c=C[i]; b=B[i]
        psi = apply(op("H", s, a), psi)
        psi = apply(op("CNOT", s, a, kind=="linked" ? c : b), psi; cutoff=1e-14, maxdim=64)
    end
    if gauge
        g = clifford_rotor_su2(0.7, 1, 2)
        for q in vcat(A,C)
            G = ITensor(g, prime(s[q]), s[q])
            psi = apply(G, psi)
        end
    end
    psi
end

function rdm(psi, reg, s)
    T = prod(psi); Tc = dag(T)
    for i in reg; Tc = prime(Tc, s[i]); end
    T*Tc
end

function logneg(psi, A, C, s; dephase=false)
    reg = vcat(A,C); ρ = rdm(psi, reg, s)
    rinds = [prime(s[i]) for i in reg]; cinds = [s[i] for i in reg]
    Cr = combiner(rinds...); Cc = combiner(cinds...)
    M = ITensors.matrix(ρ * Cr * Cc, combinedind(Cr), combinedind(Cc))
    if dephase                                # commuting/classical negative: keep only diagonal
        M = Diagonal(diag(M)) |> Matrix
    end
    # partial transpose on C block: reshape (dA,dC,dA,dC) and swap the C bra/ket
    dA = 2^length(A); dC = 2^length(C)
    R = reshape(M, (dC,dA,dC,dA))             # note combiner index order; build PT by permute
    Rpt = permutedims(R, (3,2,1,4))
    Mpt = reshape(Rpt, (dA*dC, dA*dC))
    ev = real(eigvals(0.5*(Mpt+Mpt')))
    return log2(sum(abs.(ev)))
end

function halfchain_entropy(psi, b)
    orthogonalize!(psi, b)
    U,S,V = svd(psi[b], (linkind(psi,b-1), siteind(psi,b)))
    sv = 0.0
    for n in 1:dim(S,1); p=S[n,n]^2; p>1e-12 && (sv -= p*log2(p)); end
    sv
end

results = Dict()
rows = []
for L in [3,4,5]
    N=3L; s=siteinds("Qubit", N)
    A=collect(1:L); B=collect(L+1:2L); C=collect(2L+1:3L)
    linked=build(s,A,B,C,L,"linked"); unlinked=build(s,A,B,C,L,"unlinked")
    prod_st=MPS(s,"0"); gauged=build(s,A,B,C,L,"linked";gauge=true)
    ln_link=logneg(linked,A,C,s); ln_unlink=logneg(unlinked,A,C,s)
    ln_prod=logneg(prod_st,A,C,s); ln_gauge=logneg(gauged,A,C,s)
    ln_deph=logneg(linked,A,C,s;dephase=true)
    bond=maxlinkdim(linked); hce=halfchain_entropy(linked, N÷2)
    rp = (abs(ln_link-L)<1e-3) && (abs(ln_unlink)<1e-6) && (abs(ln_prod)<1e-6) &&
         (abs(ln_gauge-ln_link)<1e-6) && (abs(ln_deph)<1e-6) && (bond>=8) && (hce>1e-6)
    push!(rows, Dict("linking_number"=>L,"n_sites"=>N,"bond"=>bond,"half_chain_entropy"=>round(hce,digits=4),
        "LN_linked"=>round(ln_link,digits=4),"LN_unlinked"=>round(ln_unlink,digits=6),
        "LN_product"=>round(ln_prod,digits=6),"LN_gauged"=>round(ln_gauge,digits=4),
        "LN_dephased"=>round(ln_deph,digits=6),"pass"=>rp))
    println("L=$L: LN_linked=$(round(ln_link,digits=3))(=$L) unlinked=$(round(ln_unlink,digits=4)) gauged=$(round(ln_gauge,digits=3)) dephased=$(round(ln_deph,digits=4)) bond=$bond pass=$rp")
end
results["carrier"]="ITensors (Julia, non-numpy) + CliffordAlgebras rotor gauge"
results["all_pass"]=all(r["pass"] for r in rows)
results["rows"]=rows
open("hopf_linking_itensors_clifford_result.json","w") do f; JSON.print(f, results, 2); end
println("all_pass=", results["all_pass"], " | carrier=", results["carrier"])
