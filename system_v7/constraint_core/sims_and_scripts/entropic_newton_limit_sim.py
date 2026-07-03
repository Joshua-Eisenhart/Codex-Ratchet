"""
entropic_newton_limit_sim.py -- PURE MATH, no jargon. 2026-07-02, Layer 0.4.

"My engines account for how spacetime/gravity work -- not literally GR, but new foundations that lead
to the SAME observations and explain what the empirical universe shows that GR+visible-matter can't."
This sim REPRODUCES the Newtonian limit (falls out exactly given the Verlinde premises), and FENCES the
explanation half (flat rotation curves without particulate dark matter) as phenomenological-not-derived.

Substrate: the model's "gravity = entropy gradient" (Layer 0.2) + signed -S(A|B) kernel (Layer 0.3),
in the holographic/entropic-force form (Verlinde 2011): a holographic screen carries N bits ∝ its
AREA; equipartition E=Mc^2=1/2 N kT fixes the screen temperature; the Unruh relation kT=hbar a/(2pi c)
turns temperature into acceleration.

RESULTS (deterministic):
 (1) EXACT NEWTONIAN LIMIT: a = 2pi c kT/hbar with N=A c^3/(G hbar), kT=2Mc^2/N reproduces
     a = G M / r^2 to ratio 1.000000 across Earth/Sun/galaxy masses and r from 6.4e6 to 3e20 m
     (Earth surface gravity 9.7275 m/s^2 falls out). The inverse-square law is NOT assumed -- it is a
     consequence of AREA bit-scaling.
 (2) STRUCTURAL: bit-count N ∝ r^p gives a ∝ r^(p-3). Holographic AREA p=2 -> slope -2 (Newton);
     extensive VOLUME p=3 -> slope -3 (inverse-cube, WRONG). The holographic (area) law is what forces
     inverse-square; the extensive control fails. This is the load-bearing structural fact.
 (3) DARK-SECTOR (FENCED, phenomenological): a point-mass baryonic disk gives Keplerian v=sqrt(GM/r)
     (falls 48% over the outer disk). Adding an entropy-gradient term a ∝ 1/r (a logarithmic
     entanglement-entropy potential, the kind Layer 0.3's signed I_c source would produce for an
     isothermal profile) flattens v(r) to ~5% variation -- reproducing observed flat rotation curves
     WITHOUT particulate dark matter. FENCE: the 1/r term's strength a0 is PHENOMENOLOGICAL, NOT
     derived from RC-1+RC-2. This is the "explains what GR+visible-matter can't" claim in its honest,
     under-test form -- a target for the ratchet, not an earned result.

HONEST SCOPE: (1)+(2) reproduce established entropic-gravity results (Verlinde) on the model's
substrate -- a genuine reproduction, not novel physics. (3) is owner doctrine under test (sec-7 fence).
The model does NOT here derive G, the area law, or a0 from the two root constraints; it shows the
foundation is CONSISTENT with -- and gives the same observations as -- Newtonian gravity, and names the
dark-sector explanation as the open target. No claim to replace GR/SM.
scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
except ImportError as e:
    print(f"SKIP_OPTIONAL entropic_newton_limit_sim: missing tool ({e.name})"); sys.exit(0)

G=6.674e-11; c=2.998e8; hbar=1.055e-34
def a_entropic(M,r):
    A=4*np.pi*r**2; N=A*c**3/(G*hbar); kT=2*M*c**2/N; return 2*np.pi*c*kT/hbar
def a_newton(M,r): return G*M/r**2
def a_scaling(M,r,p):  # N ∝ r^p, normalized to area case
    N=(r**p)*(c**3/(G*hbar))*(4*np.pi if p==2 else (4/3)*np.pi)
    return 2*np.pi*c*(2*M*c**2/N)/hbar

Ms=[5.97e24,1.99e30,1.99e42]; rs=[6.4e6,1.5e11,3e20]
ratios=[a_entropic(M,r)/a_newton(M,r) for M in Ms for r in rs]
g_earth=a_entropic(5.97e24,6.4e6)
print(f"(1) exact Newtonian limit: ratio a_entropic/a_newton in [{min(ratios):.6f},{max(ratios):.6f}]; Earth surface g={g_earth:.4f} m/s^2")

r=np.logspace(6,20,40); M=1.99e30
s2=np.polyfit(np.log(r),np.log([a_scaling(M,ri,2) for ri in r]),1)[0]
s3=np.polyfit(np.log(r),np.log([a_scaling(M,ri,3) for ri in r]),1)[0]
print(f"(2) bit-scaling N∝r^p: area p=2 slope={s2:.3f} (Newton -2), volume p=3 slope={s3:.3f} (inverse-cube WRONG)")

rr=np.linspace(0.5,30,80); Mb=1.0; a0=0.20
v_kep=np.sqrt(Mb/rr); v_ent=np.sqrt(rr*(Mb/rr**2+a0/rr))
kep_fall=(1-v_kep[-1]/v_kep[20])*100; ent_var=v_ent[20:].std()/v_ent[20:].mean()*100
print(f"(3) FENCED dark-sector: Keplerian falls {kep_fall:.0f}% over outer disk; entropy-gradient flat ({ent_var:.1f}% var) -- a0 phenomenological, NOT derived")

assert max(ratios)-1<1e-5 and 1-min(ratios)<1e-5, "entropic force reproduces Newton a=GM/r^2 exactly (area-scaling)"
assert abs(g_earth-9.7275)<1e-3, "Earth surface gravity 9.7275 m/s^2 falls out"
assert abs(s2+2)<1e-3 and abs(s3+3)<1e-3, "area-scaling forces inverse-square; volume control gives inverse-cube"
assert kep_fall>40 and ent_var<10, "entropy-gradient 1/r term flattens rotation curve where Keplerian falls (fenced)"
print("\nPASS entropic_newton_limit_sim")
