include("common.jl")
using ITensors, ITensorMPS
b2run("itensormps", "system_v8/engine_estate/results/jax/receipt.json") do
    sites=siteinds("Qubit",3); A=zeros(2,2,2); A[1,1,1]=1/sqrt(2);A[2,2,2]=1/sqrt(2); ψ=MPS(A,sites;cutoff=1e-14); ψo=orthogonalize(ψ,1); _,S,_=svd(ψo[1],siteind(ψo,1)); p=[S[i,i]^2 for i in 1:dim(S,1)]; ent=-sum(q->q<1e-14 ? 0.0 : q*log(q),p);err=abs(ent-log(2)); (err,Dict("ghz_cut_entropy"=>ent,"pass"=>err<1e-10))
end
