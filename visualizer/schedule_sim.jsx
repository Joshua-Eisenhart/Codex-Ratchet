// Schedule64Sim — 64-schedule driven by a real Lindblad master equation.
//
// State: single qubit density matrix ρ = (I + r·σ)/2, tracked via Bloch vector r.
// Each microstep applies a (H, L) pair for time dt:
//   dρ/dt = -i[H, ρ] + L ρ L† - ½ {L†L, ρ}
// integrated in closed form per op. Purity p = Tr(ρ²) = (1 + |r|²)/2.
// vN entropy S = -λ₊ log λ₊ - λ₋ log λ₋, λ± = (1 ± |r|)/2.
//
// Op map:
//   Ti: pure dephasing in z  — L = √γ σz, H = (ω/2) σz     (shrinks r_x, r_y)
//   Te: amplitude damping    — L = √γ σ_-, H = 0            (relaxes toward -z)
//   Fi: unitary σx rotation  — L = 0,      H = (ω/2) σx     (rotation around x)
//   Fe: unitary σz rotation  — L = 0,      H = (ω/2) σz     (rotation around z)
// Sign ↑ uses +ω, ↓ uses -ω. Dissipation (γ) is sign-independent — dephasing and
// damping are monotone no matter which way the unitary rotates.

const LINDBLAD_DT     = 0.22;
const LINDBLAD_OMEGA  = 1.1;   // coherent rotation rate
const LINDBLAD_GAMMA  = 0.55;  // dissipation rate

function applyLindblad(r, op, dt = LINDBLAD_DT) {
  const sgn = op.order === 'operator-first' ? +1 : -1;
  const w   = LINDBLAD_OMEGA * sgn;
  const g   = LINDBLAD_GAMMA;
  let { rx, ry, rz } = r;

  switch (op.op) {
    case 'Ti': {
      // unitary σz rotation + pure dephasing
      const c = Math.cos(w * dt), s = Math.sin(w * dt);
      const rx1 = c * rx - s * ry;
      const ry1 = s * rx + c * ry;
      const decay = Math.exp(-2 * g * dt);
      return { rx: rx1 * decay, ry: ry1 * decay, rz };
    }
    case 'Te': {
      // amplitude damping toward -z (ground = |1⟩ at rz = -1)
      const k = Math.exp(-0.5 * g * dt);
      const ez = Math.exp(-g * dt);
      return { rx: rx * k, ry: ry * k, rz: rz * ez - (1 - ez) };
    }
    case 'Fi': {
      // unitary σx rotation (no dissipation)
      const c = Math.cos(w * dt), s = Math.sin(w * dt);
      return { rx, ry: c * ry - s * rz, rz: s * ry + c * rz };
    }
    case 'Fe': {
      // unitary σz rotation (no dissipation)
      const c = Math.cos(w * dt), s = Math.sin(w * dt);
      return { rx: c * rx - s * ry, ry: s * rx + c * ry, rz };
    }
    default:
      return r;
  }
}

function blochMag(r) { return Math.hypot(r.rx, r.ry, r.rz); }
function purity(r)   { return 0.5 * (1 + r.rx*r.rx + r.ry*r.ry + r.rz*r.rz); }
function vnEntropy(r) {
  const m = Math.min(1, blochMag(r));
  const p = 0.5 * (1 + m), q = 0.5 * (1 - m);
  const h = (x) => x <= 0 ? 0 : -x * Math.log(x) / Math.log(2);
  return h(p) + h(q);  // bits
}

function Schedule64Sim({ t, data }) {
  const [running, setRunning] = React.useState(true);
  const [speed, setSpeed] = React.useState(1.5);
  const [idx, setIdx] = React.useState(0);
  const [trail, setTrail] = React.useState([]);
  const [bloch, setBloch] = React.useState({ rx: 0.9, ry: 0.05, rz: 0.1 });
  const [history, setHistory] = React.useState([]);  // [{m, p, S}]
  const mountRef = React.useRef(null);
  const stateRef = React.useRef(null);

  // advance
  React.useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setIdx(i => (i + 1) % 64), Math.max(80, 800 / speed));
    return () => clearInterval(id);
  }, [running, speed]);

  // apply Lindblad per cell
  React.useEffect(() => {
    const row = Math.floor(idx / 8);
    const col = idx % 8;
    const op = data.signedOps[col];
    setBloch(r => {
      const r2 = applyLindblad(r, op);
      setHistory(h => [...h, { m: blochMag(r2), p: purity(r2), S: vnEntropy(r2) }].slice(-64));
      return r2;
    });
    const locked = data.lockedCells.has(`${row},${col}`);
    if (locked) {
      const stage = data.macroStages.find(s => s.row === row && s.cols[0] === col);
      if (stage) {
        setTrail(tr => [{ slot: stage.slot, token: stage.token, outcome: stage.outcome, role: stage.role, i: idx }, ...tr].slice(0, 8));
      }
    }
  }, [idx]);

  // 3D Bloch ball + surface
  React.useEffect(() => {
    if (!window.THREE) return;
    const THREE = window.THREE;
    const mount = mountRef.current;
    if (!mount) return;
    const w = mount.clientWidth, h = mount.clientHeight;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(t.bgHex);
    const camera = new THREE.PerspectiveCamera(42, w/h, 0.1, 100);
    camera.position.set(2.2, 1.4, 2.6);
    camera.lookAt(0, 0, 0);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(w, h);
    mount.innerHTML = '';
    mount.appendChild(renderer.domElement);
    scene.add(new THREE.AmbientLight(0xffffff, 0.7));

    // Bloch sphere (pure-state boundary)
    const sphere = new THREE.Mesh(
      new THREE.SphereGeometry(1, 28, 20),
      new THREE.MeshBasicMaterial({ color: t.amberHex, wireframe: true, transparent: true, opacity: 0.18 })
    );
    scene.add(sphere);

    // axes
    const axMat = new THREE.LineBasicMaterial({ color: t.paperDimHex });
    [[1.3,0,0],[0,1.3,0],[0,0,1.3],[-1.3,0,0],[0,-1.3,0],[0,0,-1.3]].forEach(e => {
      const g = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0,0), new THREE.Vector3(...e)]);
      scene.add(new THREE.Line(g, axMat));
    });

    // state vector (arrow head)
    const head = new THREE.Mesh(
      new THREE.SphereGeometry(0.07, 14, 14),
      new THREE.MeshBasicMaterial({ color: t.roseHex })
    );
    scene.add(head);
    // shaft
    const shaftGeo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]);
    const shaft = new THREE.Line(shaftGeo, new THREE.LineBasicMaterial({ color: t.roseHex }));
    scene.add(shaft);

    // trail
    const trailPts = Array.from({length: 48}, () => new THREE.Vector3());
    const trailGeo = new THREE.BufferGeometry().setFromPoints(trailPts);
    const trailLine = new THREE.Line(trailGeo, new THREE.LineBasicMaterial({ color: t.cyanHex, transparent: true, opacity: 0.55 }));
    scene.add(trailLine);

    stateRef.current = { scene, camera, renderer, head, shaft, trailPts, trailLine, THREE };

    const ro = new ResizeObserver(() => {
      const nw = mount.clientWidth, nh = mount.clientHeight;
      if (nw > 0 && nh > 0) {
        renderer.setSize(nw, nh);
        camera.aspect = nw / nh;
        camera.updateProjectionMatrix();
        renderer.render(scene, camera);
      }
    });
    ro.observe(mount);

    return () => { ro.disconnect(); renderer.dispose(); };
  }, [t.bg]);

  React.useEffect(() => {
    const s = stateRef.current;
    if (!s) return;
    const { rx, ry, rz } = bloch;
    s.head.position.set(rx, ry, rz);
    s.shaft.geometry.dispose();
    s.shaft.geometry = new s.THREE.BufferGeometry().setFromPoints([new s.THREE.Vector3(0,0,0), new s.THREE.Vector3(rx, ry, rz)]);
    for (let i = 0; i < s.trailPts.length - 1; i++) s.trailPts[i].copy(s.trailPts[i+1]);
    s.trailPts[s.trailPts.length - 1].set(rx, ry, rz);
    s.trailLine.geometry.dispose();
    s.trailLine.geometry = new s.THREE.BufferGeometry().setFromPoints(s.trailPts);
    s.renderer.render(s.scene, s.camera);
  }, [bloch]);

  const row = Math.floor(idx / 8);
  const col = idx % 8;
  const m = blochMag(bloch);
  const p = purity(bloch);
  const S = vnEntropy(bloch);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      {/* controls */}
      <div style={{ padding: '8px 16px', borderBottom: `1px solid ${t.line}`, display: 'flex', gap: 14, alignItems: 'center' }}>
        <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>64-SCHEDULE · LINDBLAD SIM</Mono>
        <div style={{ flex: 1 }}/>
        <Mono t={t} size={10} dim>microstep {idx+1}/64</Mono>
        <Mono t={t} size={10} dim>·</Mono>
        <Mono t={t} size={10}>{data.terrains[row]} × {data.signedOps[col].id}</Mono>
        <div style={{ flex: 1 }}/>
        <button onClick={() => { setBloch({ rx: 0.9, ry: 0.05, rz: 0.1 }); setHistory([]); setTrail([]); setIdx(0); }} style={btn(t, false)}>reset</button>
        <button onClick={() => setRunning(r => !r)} style={btn(t, running)}>{running?'running':'paused'}</button>
        <button onClick={() => setSpeed(s => s === 3 ? 0.5 : s + 0.5)} style={btn(t, false)}>{speed}×</button>
      </div>

      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 380px', minHeight: 0 }}>
        {/* LEFT: master equation + grid + history */}
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10, minHeight: 0, overflow: 'auto' }}>
          <div style={{ border: `1px solid ${t.line}`, background: t.bg2, padding: 10 }}>
            <Mono t={t} size={9} dim style={{ letterSpacing: 1.5 }}>LINDBLAD MASTER EQUATION · per microstep (dt = {LINDBLAD_DT})</Mono>
            <div style={{ marginTop: 6, fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: t.paper, lineHeight: 1.6 }}>
              dρ/dt = −i[H, ρ] + L ρ L<sup>†</sup> − ½&#123;L<sup>†</sup>L, ρ&#125;
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '60px 1fr 1fr', gap: 6, marginTop: 8 }}>
              <Mono t={t} size={9} dim>op</Mono><Mono t={t} size={9} dim>H</Mono><Mono t={t} size={9} dim>L</Mono>
              <Mono t={t} size={10}>Ti</Mono><Mono t={t} size={10} dim>(ω/2) σz · sgn</Mono><Mono t={t} size={10} dim>√γ σz</Mono>
              <Mono t={t} size={10}>Te</Mono><Mono t={t} size={10} dim>0</Mono><Mono t={t} size={10} dim>√γ σ−</Mono>
              <Mono t={t} size={10}>Fi</Mono><Mono t={t} size={10} dim>(ω/2) σx · sgn</Mono><Mono t={t} size={10} dim>0</Mono>
              <Mono t={t} size={10}>Fe</Mono><Mono t={t} size={10} dim>(ω/2) σz · sgn</Mono><Mono t={t} size={10} dim>0</Mono>
            </div>
            <Mono t={t} size={9} dim style={{ display: 'block', marginTop: 6 }}>
              ω = {LINDBLAD_OMEGA} · γ = {LINDBLAD_GAMMA} · sgn(↑)=+1, sgn(↓)=−1
            </Mono>
          </div>

          <Mono t={t} size={10} dim>terrain (row) × signed operator (col)</Mono>
          <div style={{
            display: 'grid',
            gridTemplateColumns: `90px repeat(8, 1fr)`,
            gap: 2, background: t.line, border: `1px solid ${t.line}`,
          }}>
            <div style={{ background: t.bg, padding: 6 }}/>
            {data.signedOps.map((op, c) => (
              <div key={c} style={{ background: t.bg, padding: 6, textAlign: 'center' }}>
                <Mono t={t} size={9}>{op.id}</Mono>
              </div>
            ))}
            {data.terrains.map((terr, r) => (
              <React.Fragment key={r}>
                <div style={{ background: t.bg, padding: 6 }}>
                  <Mono t={t} size={9}>{terr}</Mono>
                  <Mono t={t} size={8} dim style={{display:'block'}}>{data.terrainEngine[r]}/{data.terrainFlux[r]}</Mono>
                </div>
                {data.signedOps.map((op, c) => {
                  const isCurrent = r === row && c === col;
                  const locked = data.lockedCells.has(`${r},${c}`);
                  const stage = locked && data.macroStages.find(s => s.row === r && s.cols[0] === c);
                  const outcomeColor = stage && (
                    stage.outcome === 'WIN' ? t.amber :
                    stage.outcome === 'LOSE' ? t.rose :
                    stage.outcome === 'win' ? t.cyan : t.paperFaint
                  );
                  return (
                    <div key={c} style={{
                      background: isCurrent ? t.paper : locked ? t.bg2 : t.bg,
                      padding: 6,
                      border: isCurrent ? `1px solid ${t.rose}` : 'none',
                      position: 'relative',
                      minHeight: 44,
                      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                    }}>
                      {stage ? (
                        <>
                          <Mono t={t} size={9} style={{ color: isCurrent ? t.bg : outcomeColor }}>{stage.token}</Mono>
                          <Mono t={t} size={8} style={{ color: isCurrent ? t.bg : outcomeColor }}>{stage.outcome}</Mono>
                        </>
                      ) : (
                        <div style={{ width: 4, height: 4, background: isCurrent ? t.bg : t.paperFaint, borderRadius: '50%', opacity: 0.4 }}/>
                      )}
                    </div>
                  );
                })}
              </React.Fragment>
            ))}
          </div>

          {/* purity / entropy time series */}
          <div style={{ border: `1px solid ${t.line}`, background: t.bg2, padding: 10 }}>
            <Mono t={t} size={9} dim style={{ letterSpacing: 1.5 }}>TIME SERIES · last 64 microsteps</Mono>
            <TimeSeries t={t} history={history} />
          </div>

          {/* fired outcomes */}
          <div style={{ border: `1px solid ${t.line}`, background: t.bg2, padding: 10 }}>
            <Mono t={t} size={9} dim style={{ letterSpacing: 1.5 }}>FIRED OUTCOMES · most recent first</Mono>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
              {trail.length === 0 && <Mono t={t} size={10} dim>waiting for first chart-lock…</Mono>}
              {trail.map((f, i) => (
                <div key={i} style={{
                  padding: '3px 8px', border: `1px solid ${f.outcome==='WIN'||f.outcome==='win'?t.amber:t.rose}`,
                  opacity: 1 - i * 0.1,
                }}>
                  <Mono t={t} size={9}>{f.slot} · {f.token} · {f.outcome}</Mono>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT: Bloch ball + readouts */}
        <div style={{ borderLeft: `1px solid ${t.line}`, display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '8px 12px', borderBottom: `1px solid ${t.line}` }}>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>BLOCH BALL · ρ = (I + r·σ) / 2</Mono>
          </div>
          <div ref={mountRef} style={{ flex: 1, minHeight: 280, background: t.bg }}/>
          <div style={{ padding: 12, borderTop: `1px solid ${t.line}`, display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '60px 1fr', rowGap: 4, columnGap: 8 }}>
              <Mono t={t} size={10} dim>op</Mono>
              <Mono t={t} size={10}><b style={{color:t.paperHex}}>{data.signedOps[col].id}</b> · sgn = {data.signedOps[col].order === 'operator-first' ? '+1' : '−1'}</Mono>
              <Mono t={t} size={10} dim>r</Mono>
              <Mono t={t} size={10}>({bloch.rx.toFixed(3)}, {bloch.ry.toFixed(3)}, {bloch.rz.toFixed(3)})</Mono>
              <Mono t={t} size={10} dim>|r|</Mono>
              <Mono t={t} size={10} style={{color:t.amberHex}}>{m.toFixed(4)}</Mono>
              <Mono t={t} size={10} dim>purity</Mono>
              <Mono t={t} size={10} style={{color:t.cyanHex}}>{p.toFixed(4)}</Mono>
              <Mono t={t} size={10} dim>S (bits)</Mono>
              <Mono t={t} size={10} style={{color:t.violetHex}}>{S.toFixed(4)}</Mono>
            </div>
            <div style={{ height: 1, background: t.line, margin: '4px 0' }}/>
            <Mono t={t} size={9} dim style={{ lineHeight: 1.5 }}>
              pure-state boundary: |r| = 1, S = 0, p = 1 · maximally mixed: |r| = 0, S = 1 bit, p = 0.5 · Ti-dominated runs drive r into xy-plane toward 0 · Te drags rz → −1 · Fi/Fe are unitary (|r| conserved).
            </Mono>
          </div>
        </div>
      </div>
    </div>
  );
}

function TimeSeries({ t, history }) {
  const W = 340, H = 110, pad = 4;
  if (!history.length) {
    return <Mono t={t} size={10} dim style={{ display:'block', marginTop: 6 }}>step the sim to populate…</Mono>;
  }
  const line = (vals, color, yMin, yMax) => {
    const pts = vals.map((v, i) => {
      const x = pad + (W - 2*pad) * (i / Math.max(1, history.length - 1));
      const y = H - pad - (H - 2*pad) * ((v - yMin) / (yMax - yMin));
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');
    return <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5"/>;
  };
  return (
    <div style={{ marginTop: 6 }}>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: H, display: 'block' }}>
        <rect x="0" y="0" width={W} height={H} fill={t.bgHex} />
        {/* guide lines at y = 0.5, 1.0 */}
        <line x1={pad} x2={W-pad} y1={H - pad - (H-2*pad)*0.5} y2={H - pad - (H-2*pad)*0.5} stroke={t.lineHex} strokeDasharray="2 3"/>
        <line x1={pad} x2={W-pad} y1={pad} y2={pad} stroke={t.lineHex} strokeDasharray="2 3"/>
        {line(history.map(h => h.m), t.amberHex, 0, 1)}
        {line(history.map(h => h.p), t.cyanHex, 0.5, 1)}
        {line(history.map(h => h.S), t.violetHex, 0, 1)}
      </svg>
      <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
        <LegendSwatch t={t} color={t.amberHex} label="|r|" />
        <LegendSwatch t={t} color={t.cyanHex} label="purity" />
        <LegendSwatch t={t} color={t.violetHex} label="S (bits)" />
      </div>
    </div>
  );
}

function LegendSwatch({ t, color, label }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
      <div style={{ width: 10, height: 2, background: color }}/>
      <Mono t={t} size={9} dim>{label}</Mono>
    </div>
  );
}

function btn(t, on) {
  return {
    padding: '4px 10px', cursor: 'pointer',
    background: on ? t.amber : 'transparent',
    color: on ? t.bg : t.paper,
    border: `1px solid ${on ? t.amber : t.line}`,
    fontFamily: 'JetBrains Mono, monospace', fontSize: 10,
    textTransform: 'uppercase', letterSpacing: 1,
  };
}

Object.assign(window, { Schedule64Sim, applyLindblad, blochMag, purity, vnEntropy });
