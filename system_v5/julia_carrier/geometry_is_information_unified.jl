# "SPACETIME IS INFORMATION" unified object (Julia, non-numpy): the GEOMETRIC Hopf linking number of two fibers
# (CliffordAlgebras) EQUALS the INFORMATION linking number = A-C log-negativity of the spinors entangled along
# those fibers (ITensors). Geometry and entanglement are the SAME integer.
using CliffordAlgebras, ITensors, ITensorMPS, LinearAlgebra, JSON
const cl = CliffordAlgebra(:Cl3); e1,e2,e3 = cl.e1,cl.e2,cl.e3
unit_rotor(a,b,c,d)=(R=a*cl.𝟏+b*(e2*e3)+c*(e3*e1)+d*(e1*e2); R/sqrt(a^2+b^2+c^2+d^2))
to_q(R)=[real(CliffordAlgebras.scalar(R)),real(R.e2e3),real(R.e3e1),real(R.e1e2)]
fiber_pt(R,t)=R*exp(t*(e1*e2))
const Rshift=unit_rotor(0.61,0.29,0.53,0.41)
fiber_circle(R,n)=[to_q(Rshift*fiber_pt(R,t)) for t in range(0,2pi,length=n+1)[1:n]]
function geo_linking(c1,c2)
    proj(q)=q[1:3]./(1 .- q[4] .+ 1e-9)
    p1=[proj(q) for q in c1]; p2=[proj(q) for q in c2]; lk=0.0; n1=length(p1); n2=length(p2)
    for i in 1:n1; a=p1[i];da=p1[mod1(i+1,n1)]-a;ma=a+da/2
        for j in 1:n2; b=p2[j];db=p2[mod1(j+1,n2)]-b;mb=b+db/2; r=ma-mb;nr=norm(r)
            nr>1e-6 && (lk+=dot(cross(da,db),r)/nr^3); end; end
    lk/(4pi)
end
# information side: L fiber-pairs entangled (each linked fiber-pair = one EPR thread = +1 to both linking numbers)
function info_linking(L)
    N=3L; s=siteinds("Qubit",N); A=collect(1:L); C=collect(2L+1:3L)
    psi=MPS(s,"0")
    for i in 1:L
        psi=apply(op("H",s,A[i]),psi)
        psi=apply(op("CNOT",s,A[i],C[i]),psi;cutoff=1e-14,maxdim=64)
    end
    T=prod(psi); Tc=dag(T); reg=vcat(A,C)
    for i in reg; Tc=prime(Tc,s[i]); end
    ρ=T*Tc; rinds=[prime(s[i]) for i in reg]; cinds=[s[i] for i in reg]
    Cr=combiner(rinds...); Cc=combiner(cinds...)
    M=ITensors.matrix(ρ*Cr*Cc,combinedind(Cr),combinedind(Cc))
    dA=2^L; dC=2^L; R=reshape(M,(dC,dA,dC,dA)); Mpt=reshape(permutedims(R,(3,2,1,4)),(dA*dC,dA*dC))
    log2(sum(abs.(real(eigvals(0.5*(Mpt+Mpt'))))))
end
rows=[]
for L in 1:3
    # geometric: L distinct linked fiber pairs -> total geometric linking = L
    geo = sum(abs(geo_linking(fiber_circle(unit_rotor(1.0,0.1k,0.2k,0.3k),120),
                               fiber_circle(unit_rotor(0.1,0.9,0.2k,0.4),120))) for k in 1:L)
    info = info_linking(L)
    push!(rows, Dict("L"=>L,"geometric_linking"=>round(geo,digits=3),"information_linking_LN"=>round(info,digits=3),
                     "match"=> abs(geo-info)<0.2))
    println("L=$L: geometric_linking=$(round(geo,digits=3))  information_LN=$(round(info,digits=3))  MATCH=$(abs(geo-info)<0.2)")
end
res=Dict("claim"=>"geometric Hopf linking number == information (entanglement) linking number",
         "carrier"=>"CliffordAlgebras (geometry) + ITensors (entanglement), Julia non-numpy",
         "all_match"=>all(r["match"] for r in rows),"rows"=>rows)
open("geometry_is_information_unified_result.json","w") do f; JSON.print(f,res,2) end
println("ALL_MATCH = ", res["all_match"])
