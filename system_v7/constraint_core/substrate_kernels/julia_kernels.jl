# Load-bearing QIT kernels -- Julia (LinearAlgebra stdlib only, dependency-free arbiter).
using LinearAlgebra, Printf
const sx=ComplexF64[0 1;1 0]; const sy=ComplexF64[0 -1im;1im 0]; const sz=ComplexF64[1 0;0 -1]; const I2=Matrix{ComplexF64}(I,2,2)
const sp=0.5*(sx+1im*sy); const sm=0.5*(sx-1im*sy); const G=0.35; const KAP=1.0
const TERR=Dict(0=>(1,"damp",1),1=>(1,"depol",0),2=>(1,"damp",-1),3=>(1,"proj",0),4=>(-1,"damp",-1),5=>(-1,"depol",0),6=>(-1,"damp",1),7=>(-1,"proj",0))
Dop(L,r)=L*r*L'-0.5*(L'*L*r+r*L'*L)
function terrain_step(ti,r,dt)
    eps,kind,pole=TERR[ti]; H=eps*(sx+sy+sz)/sqrt(3)
    out=-1im*G*(H*r-r*H)
    if kind=="damp"; out+=KAP*Dop(pole>0 ? sp : sm,r)
    elseif kind=="depol"; out+=0.5*KAP*(Dop(sx,r)+Dop(sy,r))
    else; out+=KAP*Dop(sz,r); end
    return r+dt*out
end
function flow(ti,r,t,steps); dt=t/steps; for _ in 1:steps; r=terrain_step(ti,r,dt); end; return r; end
function vn_entropy(r); w=real(eigvals(Hermitian(r))); w=w[w.>1e-12]; return -sum(w.*log.(w)); end
function liouville_spectrum(ti)
    B=[I2/sqrt(2),sx/sqrt(2),sy/sqrt(2),sz/sqrt(2)]; M=zeros(ComplexF64,4,4)
    eps,kind,pole=TERR[ti]; H=eps*(sx+sy+sz)/sqrt(3)
    for j in 1:4
        img=-1im*G*(H*B[j]-B[j]*H)
        if kind=="damp"; img+=KAP*Dop(pole>0 ? sp : sm,B[j])
        elseif kind=="depol"; img+=0.5*KAP*(Dop(sx,B[j])+Dop(sy,B[j]))
        else; img+=KAP*Dop(sz,B[j]); end
        for i in 1:4; M[i,j]=tr(B[i]'*img); end
    end
    return sort(abs.(eigvals(M)),rev=true)
end
println("JULIA_KERNELS_BEGIN")
for ti in 0:7
    fp=flow(ti,0.5*I2,12.0,3600)
    bl=[real(tr(fp*s)) for s in (sx,sy,sz)]
    ls=liouville_spectrum(ti)
    @printf("t%d bloch %.10f %.10f %.10f vn %.10f liou %.10f %.10f %.10f %.10f\n", ti, bl[1],bl[2],bl[3], vn_entropy(fp), ls[1],ls[2],ls[3],ls[4])
end
println("JULIA_KERNELS_END")
