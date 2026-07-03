# julia_engine_3q.py analogue -- 3-qubit engine in Julia (4th route on C^8).
# DEPENDENCY-FREE (stdlib LinearAlgebra + hand-rolled JSON). Reads targets_3q.json
# constants, emits julia_results_3q.json (63-dim Pauli readout). Column-stacking vec
# matches numpy/jax/torch. Run: julia julia_engine_3q.jl   scratch_diagnostic.
using LinearAlgebra
const HERE = @__DIR__

function read_constants(path)
    txt = read(path, String)
    m = match(r"\"model_constants\"\s*:\s*\{([^}]*)\}", txt); body = m.captures[1]
    C = Dict{String,Any}()
    for kv in eachmatch(r"\"(\w+)\"\s*:\s*(\[[^\]]*\]|-?[\d.eE+-]+)", body)
        k=kv.captures[1]; v=kv.captures[2]
        C[k] = startswith(v,"[") ? [parse(Float64,s) for s in split(strip(v,['[',']']),",")] : parse(Float64,v)
    end
    return C
end
jnum(x) = (isinteger(x) && abs(x)<1e15) ? string(Int(round(x))) : string(x)
jarr(v) = "[" * join([jnum(x) for x in v], ",") * "]"
function write_results(path, stages)
    io=IOBuffer(); print(io, "{\"substrate\":\"julia\",\"stages\":[")
    for (i,s) in enumerate(stages)
        print(io,"{\"t\":",s[:t],",\"op\":\"",s[:op],"\",\"pvec_down\":",jarr(s[:pd]),
              ",\"pvec_up\":",jarr(s[:pu]),",\"order_gap\":",s[:og],"}")
        i<length(stages) && print(io,",")
    end
    print(io,"]}"); open(path,"w") do f; write(f,String(take!(io))); end
end

const C = read_constants(joinpath(HERE,"targets_3q.json"))
const G,KAP,Q,TH,T_FLOW,J_COUP = C["G"],C["KAP"],C["Q"],C["TH"],C["T_FLOW"],C["J_COUP"]
const PROBE_B = C["PROBE_B"]
const I2=Matrix{ComplexF64}(I,2,2)
const sx=ComplexF64[0 1;1 0]; const sy=ComplexF64[0 -im;im 0]; const sz=ComplexF64[1 0;0 -1]
const sp=0.5*(sx+im*sy); const sm=0.5*(sx-im*sy)
const PAULI=Dict('I'=>I2,'X'=>sx,'Y'=>sy,'Z'=>sz)
kron3(a,b,c)=kron(kron(a,b),c)
on0(A)=kron3(A,I2,I2)
const I8=Matrix{ComplexF64}(I,8,8)
const ZZ01=kron3(sz,sz,I2); const ZZ12=kron3(I2,sz,sz)
sL(A)=kron(I8,A); sR(A)=kron(transpose(A),I8)
sD(L)=sL(L)*sR(L')-0.5*(sL(L'*L)+sR(L'*L)); sC(H)=-im*(sL(H)-sR(H))
const TERR=Dict(0=>(+1,"damp",+1),1=>(+1,"depol",0),2=>(+1,"damp",-1),3=>(+1,"proj",0),
                4=>(-1,"damp",-1),5=>(-1,"depol",0),6=>(-1,"damp",+1),7=>(-1,"proj",0))
const NATIVE=Dict(0=>("Ti","Fi"),1=>("Ti","Fi"),4=>("Ti","Fi"),5=>("Ti","Fi"),
                  2=>("Te","Fe"),3=>("Te","Fe"),6=>("Te","Fe"),7=>("Te","Fe"))
function gen_super(ti)
    eps,kind,pole=TERR[ti]
    H=on0(eps*(sx+sy+sz)/sqrt(3.0))+J_COUP*(ZZ01+ZZ12)
    Ls=G*sC(H)
    if kind=="damp"; Ls+=KAP*sD(on0(pole>0 ? sp : sm))
    elseif kind=="depol"; Ls+=0.5*KAP*(sD(on0(sx))+sD(on0(sy)))
    else; Ls+=KAP*sD(on0(sz)); end
    return Ls
end
function op_map(name)
    P0=0.5*(I2+sz);P1=0.5*(I2-sz);Qp=0.5*(I2+sx);Qm=0.5*(I2-sx)
    name=="Ti" && return (1-Q)*Matrix{ComplexF64}(I,64,64)+Q*(sL(on0(P0))*sR(on0(P0))+sL(on0(P1))*sR(on0(P1)))
    name=="Te" && return (1-Q)*Matrix{ComplexF64}(I,64,64)+Q*(sL(on0(Qp))*sR(on0(Qp))+sL(on0(Qm))*sR(on0(Qm)))
    U=on0(exp(-im*TH/2*(name=="Fi" ? sx : sz))); return sL(U)*sR(U')
end
vecr(r)=reshape(r,64); unvec(v)=reshape(v,8,8)
const STRINGS=[join(p) for p in Iterators.product("IXYZ","IXYZ","IXYZ") if Set(p)!=Set(['I'])]
# build Pauli readout matrices in the SAME order python uses: product over 3 slots, row-major
function pauli_mats()
    mats=[]; strs=[]
    for a in "IXYZ", b in "IXYZ", c in "IXYZ"
        (a=='I'&&b=='I'&&c=='I') && continue
        push!(mats, kron3(PAULI[a],PAULI[b],PAULI[c])); push!(strs, string(a,b,c))
    end
    return mats,strs
end
const PMATS,PSTR = pauli_mats()
pvec(r)=[real(tr(r*P)) for P in PMATS]
function main()
    rho0=0.5*(I2+PROBE_B[1]*sx+PROBE_B[2]*sy+PROBE_B[3]*sz)
    plus=0.5*(I2+sx); probe=kron3(rho0,plus,plus)
    stages=[]
    for t in 0:7, o in NATIVE[t]
        F=exp(T_FLOW*gen_super(t)); M=op_map(o); pv=vecr(probe)
        down=unvec(M*(F*pv)); up=unvec(F*(M*pv))
        down=0.5*(down+down'); up=0.5*(up+up')
        dv=pvec(down); uv=pvec(up)
        push!(stages, Dict(:t=>t,:op=>o,:pd=>dv,:pu=>uv,:og=>norm(dv-uv)))
    end
    write_results(joinpath(HERE,"julia_results_3q.json"), stages)
    println("julia_results_3q.json written (16 stages, 63-dim Pauli)")
end
main()
