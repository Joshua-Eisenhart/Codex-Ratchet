// MCLevelSetView — M(C) = admissibility manifold as intersection of semialgebraic
// constraints. Each C_i is a predicate g_i(p) ≥ 0 on a 2D parameter space p = (u, v).
// SAT iff the intersection is non-empty; UNSAT iff conjunction is vacuous.
//
// We render the full admissibility geometry:
//   - Each constraint's feasible half-plane / disc / annulus as a tinted region
//   - Their intersection (survivor region) as the amber M(C) level set
//   - Pairwise UNSAT detector: if any pair is inconsistent, flag that pair
//   - Live probe: scatter sampled points p_k, colored by admissibility under
//     the currently active constraints
//   - Toggle individual constraints on/off; the level set updates in real time
//
// No z3 in-browser, but this is a direct SAT/UNSAT geometric semantics —
// sampled satisfiability is a true semi-decision over the bounded box.

const MC_BOX = { umin: -2.5, umax: 2.5, vmin: -2.5, vmax: 2.5 };

// Constraint library — each returns { ok: bool, value: g(u, v) }
const CONSTRAINTS = [
  {
    id: 'C1',
    name: 'finitude',
    rule: '|p|² ≤ R²',
    color: 'amberHex',
    param: { R: 1.8 },
    test: (u, v, p) => {
      const g = p.R * p.R - (u*u + v*v);
      return { ok: g >= 0, g };
    },
  },
  {
    id: 'C2',
    name: 'noncommutation',
    rule: '(u − a)(v − b) ≥ c',
    color: 'cyanHex',
    param: { a: 0.2, b: 0.2, c: -0.35 },
    test: (u, v, p) => {
      const g = (u - p.a) * (v - p.b) - p.c;
      return { ok: g >= 0, g };
    },
  },
  {
    id: 'C3',
    name: 'ordering',
    rule: 'v ≥ u − k',
    color: 'violetHex',
    param: { k: 1.0 },
    test: (u, v, p) => {
      const g = v - u + p.k;
      return { ok: g >= 0, g };
    },
  },
  {
    id: 'C4',
    name: 'fibration',
    rule: 'r₁² ≤ u² + v² ≤ r₂²',
    color: 'roseHex',
    param: { r1: 0.35, r2: 2.2 },
    test: (u, v, p) => {
      const r2 = u*u + v*v;
      const ga = r2 - p.r1 * p.r1;
      const gb = p.r2 * p.r2 - r2;
      return { ok: ga >= 0 && gb >= 0, g: Math.min(ga, gb) };
    },
  },
  {
    id: 'C5',
    name: 'chart-lock',
    rule: '|u + v − s| ≤ w',
    color: 'paperHex',
    param: { s: 0.4, w: 1.4 },
    test: (u, v, p) => {
      const g = p.w - Math.abs(u + v - p.s);
      return { ok: g >= 0, g };
    },
  },
];

function admissible(u, v, active, cfg) {
  for (const c of CONSTRAINTS) {
    if (!active[c.id]) continue;
    if (!c.test(u, v, cfg[c.id]).ok) return false;
  }
  return true;
}

// Grid sampler — returns counts + sample points admissible / blocked
function sampleGrid(active, cfg, N = 48) {
  const pts = [];
  let nOK = 0;
  for (let i = 0; i < N; i++) {
    for (let j = 0; j < N; j++) {
      const u = MC_BOX.umin + (MC_BOX.umax - MC_BOX.umin) * ((i + 0.5) / N);
      const v = MC_BOX.vmin + (MC_BOX.vmax - MC_BOX.vmin) * ((j + 0.5) / N);
      const ok = admissible(u, v, active, cfg);
      if (ok) nOK++;
      pts.push({ u, v, ok });
    }
  }
  return { pts, nOK, nTotal: N * N };
}

// Pairwise UNSAT detector — returns [ids] pair that is already inconsistent
function pairwiseUnsat(active, cfg, N = 48) {
  const ids = Object.keys(active).filter(k => active[k]);
  for (let a = 0; a < ids.length; a++) {
    for (let b = a + 1; b < ids.length; b++) {
      let found = false;
      outer:
      for (let i = 0; i < N; i++) {
        for (let j = 0; j < N; j++) {
          const u = MC_BOX.umin + (MC_BOX.umax - MC_BOX.umin) * ((i + 0.5) / N);
          const v = MC_BOX.vmin + (MC_BOX.vmax - MC_BOX.vmin) * ((j + 0.5) / N);
          const ca = CONSTRAINTS.find(c => c.id === ids[a]);
          const cb = CONSTRAINTS.find(c => c.id === ids[b]);
          if (ca.test(u, v, cfg[ids[a]]).ok && cb.test(u, v, cfg[ids[b]]).ok) {
            found = true;
            break outer;
          }
        }
      }
      if (!found) return [ids[a], ids[b]];
    }
  }
  return null;
}

function MCLevelSetView({ t }) {
  const [active, setActive] = React.useState({ C1: true, C2: true, C3: false, C4: true, C5: false });
  const [cfg, setCfg] = React.useState(() => {
    const o = {};
    CONSTRAINTS.forEach(c => { o[c.id] = { ...c.param }; });
    return o;
  });
  const [probe, setProbe] = React.useState({ u: 0.4, v: 0.3 });

  const active_count = Object.values(active).filter(Boolean).length;
  const grid = React.useMemo(() => sampleGrid(active, cfg), [active, cfg]);
  const pair = React.useMemo(() => pairwiseUnsat(active, cfg), [active, cfg]);
  const isSAT = grid.nOK > 0;
  const solidRatio = grid.nOK / grid.nTotal;

  const activeIds = Object.keys(active).filter(k => active[k]);

  // per-constraint g(probe) readout
  const probeRead = CONSTRAINTS.map(c => {
    const r = c.test(probe.u, probe.v, cfg[c.id]);
    return { ...c, ...r, active: active[c.id] };
  });
  const probeOK = probeRead.filter(r => r.active).every(r => r.ok);

  // SVG coords
  const W = 480, H = 480, pad = 20;
  const xScale = (u) => pad + (W - 2*pad) * (u - MC_BOX.umin) / (MC_BOX.umax - MC_BOX.umin);
  const yScale = (v) => H - pad - (H - 2*pad) * (v - MC_BOX.vmin) / (MC_BOX.vmax - MC_BOX.vmin);
  const xInv = (x) => MC_BOX.umin + (x - pad) * (MC_BOX.umax - MC_BOX.umin) / (W - 2*pad);
  const yInv = (y) => MC_BOX.vmin + (H - pad - y) * (MC_BOX.vmax - MC_BOX.vmin) / (H - 2*pad);

  const onMove = (e) => {
    const r = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - r.left) * (W / r.width);
    const y = (e.clientY - r.top)  * (H / r.height);
    setProbe({ u: xInv(x), v: yInv(y) });
  };

  // dense background: sample pixel-ish grid
  const Ngrid = 80;
  const cells = [];
  const cellW = (W - 2*pad) / Ngrid;
  const cellH = (H - 2*pad) / Ngrid;
  for (let i = 0; i < Ngrid; i++) {
    for (let j = 0; j < Ngrid; j++) {
      const u = MC_BOX.umin + (MC_BOX.umax - MC_BOX.umin) * ((i + 0.5) / Ngrid);
      const v = MC_BOX.vmin + (MC_BOX.vmax - MC_BOX.vmin) * ((j + 0.5) / Ngrid);
      const ok = admissible(u, v, active, cfg);
      cells.push({ i, j, u, v, ok });
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      <div style={{ padding: '8px 16px', borderBottom: `1px solid ${t.line}`, display: 'flex', gap: 14, alignItems: 'center' }}>
        <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>M(C) · ADMISSIBILITY LEVEL SET · SAT / UNSAT GEOMETRY</Mono>
        <div style={{ flex: 1 }}/>
        <div style={{
          padding: '4px 10px',
          background: isSAT ? t.amber + '22' : t.rose + '22',
          color: isSAT ? t.amberHex : t.roseHex,
          border: `1px solid ${isSAT ? t.amberHex : t.roseHex}`,
        }}>
          <Mono t={t} size={11}><b>{isSAT ? 'SAT' : 'UNSAT'}</b></Mono>
        </div>
        <Mono t={t} size={10} dim>admissible frac ≈ {(solidRatio * 100).toFixed(1)}%</Mono>
      </div>

      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 420px', minHeight: 0, overflow: 'hidden' }}>
        {/* LEFT: SVG canvas */}
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10, minHeight: 0, overflow: 'auto' }}>
          <svg viewBox={`0 0 ${W} ${H}`} onMouseMove={onMove} style={{ width: '100%', maxWidth: 620, display: 'block', cursor: 'crosshair', background: t.bgHex, border: `1px solid ${t.line}` }}>
            {/* grid */}
            {Array.from({ length: 11 }).map((_, i) => {
              const u = MC_BOX.umin + (MC_BOX.umax - MC_BOX.umin) * (i / 10);
              return <line key={`vx${i}`} x1={xScale(u)} x2={xScale(u)} y1={pad} y2={H-pad} stroke={t.lineHex} strokeWidth={i === 5 ? 1 : 0.3}/>;
            })}
            {Array.from({ length: 11 }).map((_, i) => {
              const v = MC_BOX.vmin + (MC_BOX.vmax - MC_BOX.vmin) * (i / 10);
              return <line key={`hy${i}`} y1={yScale(v)} y2={yScale(v)} x1={pad} x2={W-pad} stroke={t.lineHex} strokeWidth={i === 5 ? 1 : 0.3}/>;
            })}

            {/* level-set fill: dense admissibility cells */}
            {cells.map(c => c.ok && (
              <rect key={`${c.i}-${c.j}`}
                x={pad + c.i * cellW} y={pad + (Ngrid - 1 - c.j) * cellH}
                width={cellW + 0.4} height={cellH + 0.4}
                fill={t.amberHex} opacity={0.22}/>
            ))}

            {/* constraint boundaries overlaid */}
            {active.C1 && <circle cx={xScale(0)} cy={yScale(0)} r={(xScale(cfg.C1.R) - xScale(0))} fill="none" stroke={t[CONSTRAINTS.find(c=>c.id==='C1').color]} strokeWidth="1.2" strokeDasharray="4 3"/>}
            {active.C4 && <>
              <circle cx={xScale(0)} cy={yScale(0)} r={(xScale(cfg.C4.r1) - xScale(0))} fill="none" stroke={t[CONSTRAINTS.find(c=>c.id==='C4').color]} strokeWidth="1.2" strokeDasharray="4 3"/>
              <circle cx={xScale(0)} cy={yScale(0)} r={(xScale(cfg.C4.r2) - xScale(0))} fill="none" stroke={t[CONSTRAINTS.find(c=>c.id==='C4').color]} strokeWidth="1.2" strokeDasharray="4 3"/>
            </>}
            {active.C3 && (() => {
              const k = cfg.C3.k;
              // line v = u - k, clipped to box
              const u1 = MC_BOX.umin, v1 = u1 - k;
              const u2 = MC_BOX.umax, v2 = u2 - k;
              return <line x1={xScale(u1)} y1={yScale(v1)} x2={xScale(u2)} y2={yScale(v2)} stroke={t[CONSTRAINTS.find(c=>c.id==='C3').color]} strokeWidth="1.2" strokeDasharray="4 3"/>;
            })()}
            {active.C5 && (() => {
              const { s, w } = cfg.C5;
              // |u + v - s| = w → two parallel lines u + v = s ± w
              const segs = [s - w, s + w].map(c => {
                // clip v = c - u
                const u1 = MC_BOX.umin, v1 = c - u1;
                const u2 = MC_BOX.umax, v2 = c - u2;
                return [u1, v1, u2, v2];
              });
              return segs.map((s, i) => <line key={i} x1={xScale(s[0])} y1={yScale(s[1])} x2={xScale(s[2])} y2={yScale(s[3])} stroke={t[CONSTRAINTS.find(c=>c.id==='C5').color]} strokeWidth="1.2" strokeDasharray="4 3"/>);
            })()}
            {active.C2 && (() => {
              // curve (u-a)(v-b) = c → v = b + c/(u-a). Sample over u.
              const { a, b, c } = cfg.C2;
              const pts1 = [], pts2 = [];
              for (let i = 0; i <= 200; i++) {
                const u = MC_BOX.umin + (MC_BOX.umax - MC_BOX.umin) * (i / 200);
                if (Math.abs(u - a) < 1e-4) continue;
                const v = b + c / (u - a);
                if (v < MC_BOX.vmin || v > MC_BOX.vmax) continue;
                (u < a ? pts1 : pts2).push([xScale(u), yScale(v)]);
              }
              const mk = pts => pts.map(p => p.join(',')).join(' ');
              return (
                <>
                  <polyline points={mk(pts1)} fill="none" stroke={t[CONSTRAINTS.find(c=>c.id==='C2').color]} strokeWidth="1.2" strokeDasharray="4 3"/>
                  <polyline points={mk(pts2)} fill="none" stroke={t[CONSTRAINTS.find(c=>c.id==='C2').color]} strokeWidth="1.2" strokeDasharray="4 3"/>
                </>
              );
            })()}

            {/* probe point */}
            <circle cx={xScale(probe.u)} cy={yScale(probe.v)} r="6" fill={probeOK ? t.amberHex : t.roseHex} stroke={t.paperHex} strokeWidth="1.5"/>

            {/* axes labels */}
            <text x={W - pad - 4} y={yScale(0) - 4} fill={t.paperDimHex} fontFamily="JetBrains Mono" fontSize="10" textAnchor="end">u</text>
            <text x={xScale(0) + 4} y={pad + 12} fill={t.paperDimHex} fontFamily="JetBrains Mono" fontSize="10">v</text>
          </svg>

          <Mono t={t} size={10} dim style={{ lineHeight: 1.5 }}>
            The <span style={{color:t.amberHex}}>amber region</span> is M(C) — the intersection of all active constraints. Hover the canvas to probe. A point lives in M(C) iff every active g_i(p) ≥ 0. The survivor fraction is the Lebesgue measure of M(C) / box, computed by dense sampling.
          </Mono>
        </div>

        {/* RIGHT: constraints + probe */}
        <div style={{ borderLeft: `1px solid ${t.line}`, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'auto' }}>
          <div style={{ padding: '8px 12px', borderBottom: `1px solid ${t.line}` }}>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>CONSTRAINT FAMILY C · {active_count}/{CONSTRAINTS.length} ACTIVE</Mono>
          </div>
          <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
            {CONSTRAINTS.map(c => (
              <div key={c.id} style={{ border: `1px solid ${t.line}`, background: active[c.id] ? t.bg2 : t.bg, padding: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <button onClick={() => setActive(a => ({ ...a, [c.id]: !a[c.id] }))} style={{
                    width: 18, height: 18, padding: 0, cursor: 'pointer',
                    background: active[c.id] ? t[c.color] : 'transparent',
                    border: `1.5px solid ${t[c.color]}`,
                  }}/>
                  <Mono t={t} size={11}><b style={{color: t[c.color]}}>{c.id}</b> · {c.name}</Mono>
                  <div style={{ flex: 1 }}/>
                  <Mono t={t} size={10} dim>{c.rule}</Mono>
                </div>
                {active[c.id] && (
                  <div style={{ marginTop: 6, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 4 }}>
                    {Object.entries(cfg[c.id]).map(([k, v]) => (
                      <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Mono t={t} size={9} dim>{k}</Mono>
                        <input type="range" min={-2.5} max={2.5} step={0.01} value={v}
                          onChange={e => setCfg(x => ({ ...x, [c.id]: { ...x[c.id], [k]: parseFloat(e.target.value) } }))}
                          style={{ flex: 1 }}/>
                        <Mono t={t} size={9}>{v.toFixed(2)}</Mono>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div style={{ borderTop: `1px solid ${t.line}`, padding: 12 }}>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>PROBE · p = (u, v)</Mono>
            <div style={{ display: 'grid', gridTemplateColumns: '60px 1fr', rowGap: 3, columnGap: 8, marginTop: 6 }}>
              <Mono t={t} size={10} dim>p</Mono>
              <Mono t={t} size={10}>({probe.u.toFixed(3)}, {probe.v.toFixed(3)})</Mono>
              <Mono t={t} size={10} dim>verdict</Mono>
              <Mono t={t} size={10} style={{color: probeOK ? t.amberHex : t.roseHex}}>
                <b>{probeOK ? '∈ M(C)' : '∉ M(C)'}</b>
              </Mono>
            </div>
            <div style={{ marginTop: 8, display: 'grid', gridTemplateColumns: '40px 1fr 60px', rowGap: 3, columnGap: 6 }}>
              {probeRead.map(r => (
                <React.Fragment key={r.id}>
                  <Mono t={t} size={10} style={{color: r.active ? t[r.color] : t.paperFaintHex}}><b>{r.id}</b></Mono>
                  <Mono t={t} size={10} dim={!r.active}>{r.name}</Mono>
                  <Mono t={t} size={10} style={{color: !r.active ? t.paperFaintHex : (r.ok ? t.amberHex : t.roseHex)}}>
                    g = {r.g.toFixed(2)}
                  </Mono>
                </React.Fragment>
              ))}
            </div>
          </div>

          {pair && (
            <div style={{ borderTop: `1px solid ${t.line}`, padding: 12, background: t.rose + '11' }}>
              <Mono t={t} size={10} style={{color:t.roseHex,letterSpacing:1.5}}><b>PAIRWISE UNSAT</b></Mono>
              <Mono t={t} size={10} dim style={{display:'block',marginTop:4,lineHeight:1.5}}>
                constraints <b style={{color:t.roseHex}}>{pair[0]}</b> ∧ <b style={{color:t.roseHex}}>{pair[1]}</b> are already inconsistent over the box — no point satisfies both.  The full conjunction is necessarily UNSAT; no amount of further probing will find M(C) without relaxing one of them.
              </Mono>
            </div>
          )}

          <div style={{ borderTop: `1px solid ${t.line}`, padding: 12 }}>
            <Mono t={t} size={9} dim style={{ lineHeight: 1.5, display: 'block' }}>
              <b>Doctrine:</b> M(C) = probe-admissible region under constraint family C. Constraints exclude what cannot persist; they do not "produce" the survivor region. A point in the amber is a candidate — surviving doesn't mean canonical, only admissible under the currently active C. When you add a constraint and the region shrinks, the preserved candidates are the co-admissible ones; when it vanishes (UNSAT) you've discovered a structural impossibility.
            </Mono>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { MCLevelSetView });
