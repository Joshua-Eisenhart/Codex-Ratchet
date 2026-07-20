using JSON3
using LinearAlgebra

function spinor(eta, phi, chi)
    ComplexF64[exp(im * phi) * cos(eta), exp(im * chi) * sin(eta)]
end

function loop_holonomy_from_links(eta, phi0, n_loop)
    points = [spinor(eta, phi0, 2 * pi * k / n_loop) for k in 0:(n_loop - 1)]
    sum(angle(dot(points[k], points[k == n_loop ? 1 : k + 1])) for k in 1:n_loop)
end

payload = JSON3.read(read(ARGS[1], String))
protocol = payload["protocol"]
eta1 = Float64(protocol["eta1"])
phi0 = Float64(protocol["phi0"])
n_loop = Int(protocol["n_loop"])
rows = Any[]
for item in payload["ticks"]
    encoded = item["rho_before"]
    rho = Matrix{ComplexF64}(undef, 4, 4)
    for i in 1:4, j in 1:4
        rho[i, j] = ComplexF64(Float64(encoded[i][j][1]), Float64(encoded[i][j][2]))
    end
    # Literal equivalent of v1's reshape(...).diagonal(...).sum(...)[1].
    p1_left = real(sum(rho[2 * a + 2, 2 * c + 2] for a in 0:1, c in 0:1))
    eta2 = 0.3 + 0.4 * clamp(p1_left, 0.0, 1.0)
    h1 = loop_holonomy_from_links(eta1, phi0, n_loop)
    h2 = loop_holonomy_from_links(eta2, phi0, n_loop)
    push!(rows, Dict("tick" => Int(item["tick"]), "eta2" => eta2,
                     "holonomy_eta1" => h1, "holonomy_eta2" => h2,
                     "flux" => h1 - h2))
end
println(JSON3.write(Dict("ticks" => rows)))
