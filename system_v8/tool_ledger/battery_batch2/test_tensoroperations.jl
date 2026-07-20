include("common.jl")
using TensorOperations, LinearAlgebra
b2run("tensoroperations", "system_v8/engine_estate/results/jax/receipt.json") do
    ψ=zeros(ComplexF64,2,2,2); ψ[1,1,1]=1/sqrt(2); ψ[2,2,2]=1/sqrt(2); ρ=zeros(ComplexF64,2,2)
    @tensor ρ[a,b] := ψ[a,c,d] * conj(ψ[b,c,d])
    p=real.(eigvals(Hermitian(ρ))); S=-sum(q->q<1e-14 ? 0.0 : q*log(q),p); err=abs(S-log(2))
    (err, Dict("ghz_cut_entropy"=>S,"quimb_reference"=>log(2),"pass"=>err<1e-10))
end
