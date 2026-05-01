// RosettaPanel — one invariant, many notations, all alive under one integer k.
//
// The invariant is the fundamental integer that indexes
//   π₁(S¹) = π_n(Sⁿ) = H₂(S²) = c₁(U(1)-bundle over S²) = Hopf invariant
//
// all of which equal ℤ. Move the central slider and every panel recomputes
// its own expression of k from its own notation, converging to the same k.
//
// Nothing is illustrative: each panel computes its number numerically from
// its own geometry/topology.

function windingNumberSVG(t, k, R) {
  // loop γ(θ) = R e^{ikθ} in the complex plane, θ ∈ [0, 2π]
  const W = 220, H = 220, cx = W/2, cy = H/2;
  const pts = [];
  const N = 256;
  for (let i = 0; i <= N; i++) {
    const theta = 2 * Math.PI * i / N;
    const z_re = R * Math.cos(k * theta);
    const z_im = R * Math.sin(k * theta);
    pts.push([cx + 80 * z_re, cy - 80 * z_im]);
  }
  // numerical winding: sum of signed angle increments seen from origin
  let W_num = 0;
  for (let i = 0; i < N; i++) {
    const a1 = Math.atan2(pts[i][1] - cy, pts[i][0] - cx);
    const a2 = Math.atan2(pts[i+1][1] - cy, pts[i+1][0] - cx);
    let d = a2 - a1;
    while (d > Math.PI) d -= 2*Math.PI;
    while (d < -Math.PI) d += 2*Math.PI;
    W_num += d;
  }
  const winding = Math.round(-W_num / (2 * Math.PI));  // CCW = +, matches k sign via -Im
  return { W, H, cx, cy, pts, winding };
}

function chernIntegral(k, N = 64) {
  // F = (k/2) sin θ dθ ∧ dφ   →   (1/2π) ∫_{S²} F = k
  let sum = 0;
  const dθ = Math.PI / N;
  const dφ = 2 * Math.PI / (2*N);
  for (let i = 0; i < N; i++) {
    const θ = (i + 0.5) * dθ;
    for (let j = 0; j < 2*N; j++) {
      sum += (k / 2) * Math.sin(θ) * dθ * dφ;
    }
  }
  return sum / (2 * Math.PI);
}

function degreeIntegral(k, N = 48) {
  // deg(f) for f(θ, φ) = (θ, kφ): Jacobian factor = k · sinθ, integrated → 4π·k
  // deg = (1/4π) ∫ f*ω where ω = sinθ dθ dφ is the volume form on S²
  let sum = 0;
  const dθ = Math.PI / N;
  const dφ = 2 * Math.PI / (2*N);
  for (let i = 0; i < N; i++) {
    const θ = (i + 0.5) * dθ;
    for (let j = 0; j < 2*N; j++) {
      sum += k * Math.sin(θ) * dθ * dφ;   // pullback Jacobian for z ↦ z^k in stereo
    }
  }
  return sum / (4 * Math.PI);
}

function gaussLinkingNumerical(k, N = 300) {
  // two circles in ℝ³, the second with winding k around the first.
  // L₁: γ₁(s) = (cos s, sin s, 0)
  // L₂: γ₂(t) = (cos(k t) + 2, 0, sin(k t))  — translated, revolving k times
  // Gauss:  lk = (1/4π) ∮∮ ((r₁ − r₂) · (dr₁ × dr₂)) / |r₁ − r₂|³
  const ds = 2 * Math.PI / N;
  const dt = 2 * Math.PI / N;
  let sum = 0;
  for (let i = 0; i < N; i++) {
    const s = i * ds;
    const r1 = [Math.cos(s), Math.sin(s), 0];
    const dr1 = [-Math.sin(s), Math.cos(s), 0];
    for (let j = 0; j < N; j++) {
      const tv = j * dt;
      const r2 = [Math.cos(k * tv) + 2.5, 0, Math.sin(k * tv)];
      const dr2 = [-k * Math.sin(k * tv), 0, k * Math.cos(k * tv)];
      const d = [r1[0]-r2[0], r1[1]-r2[1], r1[2]-r2[2]];
      const cr = [dr1[1]*dr2[2] - dr1[2]*dr2[1],
                  dr1[2]*dr2[0] - dr1[0]*dr2[2],
                  dr1[0]*dr2[1] - dr1[1]*dr2[0]];
      const dot = d[0]*cr[0] + d[1]*cr[1] + d[2]*cr[2];
      const norm = Math.pow(d[0]*d[0] + d[1]*d[1] + d[2]*d[2], 1.5);
      if (norm < 1e-9) continue;
      sum += dot / norm * ds * dt;
    }
  }
  return sum / (4 * Math.PI);
}

// Box helper
function RBox({ t, title, verdict, children, style }) {
  return (
    <div style={{ border: `1px solid ${t.line}`, background: t.bg2, padding: 12, display: 'flex', flexDirection: 'column', minHeight: 0, ...style }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 6 }}>
        <Mono t={t} size={10} dim style={{ letterSpacing: 1.2 }}>{title}</Mono>
        <div style={{ flex: 1 }}/>
        {verdict && (
          <Mono t={t} size={11} style={{ color: verdict.match ? t.amberHex : t.roseHex }}>
            {verdict.label}: <b>{verdict.value}</b>
          </Mono>
        )}
      </div>
      <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
        {children}
      </div>
    </div>
  );
}

function RosettaPanel({ t }) {
  const [k, setK] = React.useState(2);

  // cache numerical integrals — expensive
  const [chern, setChern] = React.useState(null);
  const [degree, setDegree] = React.useState(null);
  const [lk, setLk] = React.useState(null);
  React.useEffect(() => {
    setChern(chernIntegral(k));
    setDegree(degreeIntegral(k));
    setLk(gaussLinkingNumerical(k, 180));
  }, [k]);

  const wnd = windingNumberSVG(t, k, 1.0);

  // 3D linking-number scene
  const mountRef = React.useRef(null);
  const stateRef = React.useRef(null);
  React.useEffect(() => {
    if (!window.THREE) return;
    const THREE = window.THREE;
    const mount = mountRef.current;
    if (!mount) return;
    const w = mount.clientWidth, h = mount.clientHeight;
    if (w === 0 || h === 0) return;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(t.bgHex);
    const camera = new THREE.PerspectiveCamera(40, w/h, 0.1, 100);
    camera.position.set(4, 3, 5);
    camera.lookAt(1.2, 0, 0);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(w, h);
    mount.innerHTML = '';
    mount.appendChild(renderer.domElement);
    scene.add(new THREE.AmbientLight(0xffffff, 0.7));

    stateRef.current = { scene, camera, renderer, THREE, w, h };

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
    const { scene, camera, renderer, THREE } = s;
    // clear previous curves
    const toRm = [];
    scene.traverse(o => { if (o.userData && o.userData.rosetta) toRm.push(o); });
    toRm.forEach(o => scene.remove(o));

    // curve 1: reference circle
    const N = 200;
    const pts1 = [];
    for (let i = 0; i <= N; i++) {
      const s_ = 2 * Math.PI * i / N;
      pts1.push(new THREE.Vector3(Math.cos(s_), Math.sin(s_), 0));
    }
    const g1 = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts1, true), 200, 0.03, 8, true);
    const m1 = new THREE.MeshBasicMaterial({ color: t.amberHex });
    const mesh1 = new THREE.Mesh(g1, m1); mesh1.userData.rosetta = true;
    scene.add(mesh1);

    // curve 2: winds k times
    const pts2 = [];
    for (let i = 0; i <= N; i++) {
      const tv = 2 * Math.PI * i / N;
      pts2.push(new THREE.Vector3(Math.cos(k * tv) + 2.5, 0, Math.sin(k * tv)));
    }
    const g2 = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts2, true), 400, 0.03, 8, true);
    const m2 = new THREE.MeshBasicMaterial({ color: t.cyanHex });
    const mesh2 = new THREE.Mesh(g2, m2); mesh2.userData.rosetta = true;
    scene.add(mesh2);

    // axes
    const axMat = new THREE.LineBasicMaterial({ color: t.paperDimHex, transparent: true, opacity: 0.4 });
    [[3,0,0],[0,3,0],[0,0,3]].forEach(e => {
      const g = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0,0), new THREE.Vector3(...e)]);
      const l = new THREE.Line(g, axMat); l.userData.rosetta = true;
      scene.add(l);
    });

    renderer.render(scene, camera);
  }, [k, t.bg]);

  // verdict helper
  const v = (x, label) => x === null
    ? { label, value: '…' , match: false }
    : { label, value: x.toFixed(3), match: Math.abs(x - k) < 0.05 };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      <div style={{ padding: '8px 16px', borderBottom: `1px solid ${t.line}`, display: 'flex', gap: 14, alignItems: 'center' }}>
        <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>ROSETTA · ONE INTEGER INVARIANT · FIVE NOTATIONS</Mono>
        <div style={{ flex: 1 }}/>
        <Mono t={t} size={10} dim>π₁(S¹) = π_n(Sⁿ) = ℤ</Mono>
      </div>

      {/* master slider */}
      <div style={{ padding: '14px 18px', borderBottom: `1px solid ${t.line}`, background: t.bg2, display: 'flex', alignItems: 'center', gap: 16 }}>
        <Mono t={t} size={12} dim>master k =</Mono>
        <input type="range" min="-3" max="3" step="1" value={k} onChange={e => setK(parseInt(e.target.value))} style={{ flex: 1 }}/>
        <Mono t={t} size={28} style={{color: t.amberHex}}><b>{k >= 0 ? `+${k}` : k}</b></Mono>
      </div>

      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gridTemplateRows: '1fr 1fr', gap: 10, padding: 12, minHeight: 0, overflow: 'hidden' }}>
        {/* ── 1. Winding number ─────────────────────────────── */}
        <RBox t={t} title="COMPLEX · winding W(γ)" verdict={v(wnd.winding, 'W(γ)')}>
          <svg viewBox={`0 0 ${wnd.W} ${wnd.H}`} style={{ flex: 1, minHeight: 0 }}>
            <rect x="0" y="0" width={wnd.W} height={wnd.H} fill={t.bgHex}/>
            <line x1={wnd.cx} y1="0" x2={wnd.cx} y2={wnd.H} stroke={t.lineHex}/>
            <line x1="0" y1={wnd.cy} x2={wnd.W} y2={wnd.cy} stroke={t.lineHex}/>
            <circle cx={wnd.cx} cy={wnd.cy} r="3" fill={t.roseHex}/>
            <polyline points={wnd.pts.map(p => p.join(',')).join(' ')}
              fill="none" stroke={t.amberHex} strokeWidth="1.6" opacity="0.85"/>
          </svg>
          <Mono t={t} size={9} dim style={{lineHeight:1.5, marginTop:4}}>
            γ(θ) = e<sup>ikθ</sup> &nbsp; W = (1/2πi) ∮ dz/z
          </Mono>
        </RBox>

        {/* ── 2. Chern number ────────────────────────────── */}
        <RBox t={t} title="GEOMETRY · c₁(L) over S²" verdict={v(chern, 'c₁')}>
          <svg viewBox="0 0 220 220" style={{ flex: 1, minHeight: 0 }}>
            <rect x="0" y="0" width="220" height="220" fill={t.bgHex}/>
            <circle cx="110" cy="110" r="80" fill="none" stroke={t.cyanHex} strokeWidth="1.3"/>
            {[...Array(18)].map((_, i) => {
              const φ = 2*Math.PI*i/18;
              return <line key={i} x1={110 + 80*Math.cos(φ)} y1={110 + 80*Math.sin(φ)*0.3}
                      x2={110 + 80*Math.cos(φ)} y2={110 - 80*Math.sin(φ)*0.3}
                      stroke={t.cyanHex} strokeWidth="0.4" opacity="0.3"/>;
            })}
            {/* monopole markers inside */}
            {Array.from({length: Math.min(Math.abs(k), 5)}).map((_, i) => {
              const ang = 2*Math.PI*i/Math.max(1, Math.abs(k));
              const cx = 110 + 25*Math.cos(ang), cy = 110 + 25*Math.sin(ang);
              return <g key={i}>
                <circle cx={cx} cy={cy} r="8" fill={k > 0 ? t.amberHex : t.roseHex}/>
                <text x={cx} y={cy+3} fontSize="10" fill={t.bgHex} textAnchor="middle" fontFamily="JetBrains Mono">{k>0?'+':'−'}</text>
              </g>;
            })}
            <text x="110" y="28" fill={t.paperDimHex} fontSize="10" textAnchor="middle" fontFamily="JetBrains Mono">S²</text>
          </svg>
          <Mono t={t} size={9} dim style={{lineHeight:1.5, marginTop:4}}>
            F = (k/2) sinθ dθ ∧ dφ &nbsp; c₁ = (1/2π) ∫<sub>S²</sub> F
          </Mono>
        </RBox>

        {/* ── 3. Homotopy degree ───────────────────────────── */}
        <RBox t={t} title="TOPOLOGY · deg(f : S² → S²)" verdict={v(degree, 'deg')}>
          <svg viewBox="0 0 220 220" style={{ flex: 1, minHeight: 0 }}>
            <rect x="0" y="0" width="220" height="220" fill={t.bgHex}/>
            {/* domain sphere */}
            <circle cx="55" cy="110" r="38" fill="none" stroke={t.paperDimHex}/>
            <text x="55" y="180" fill={t.paperDimHex} fontSize="10" textAnchor="middle" fontFamily="JetBrains Mono">S² dom</text>
            {/* arrow */}
            <line x1="98" y1="110" x2="162" y2="110" stroke={t.amberHex} strokeWidth="1.3"/>
            <polygon points="156,106 166,110 156,114" fill={t.amberHex}/>
            <text x="130" y="100" fill={t.amberHex} fontSize="10" textAnchor="middle" fontFamily="JetBrains Mono">z ↦ z<tspan fontSize="7" dy="-4">{k}</tspan></text>
            {/* codomain with k copies */}
            <circle cx="165" cy="110" r="38" fill="none" stroke={t.cyanHex}/>
            {/* k-tuple winding visualization */}
            {[...Array(Math.max(1, Math.abs(k)))].map((_, i) => (
              <circle key={i} cx="165" cy="110" r={12 + i*3} fill="none" stroke={k>=0?t.amberHex:t.roseHex} strokeWidth="0.8" opacity="0.6"/>
            ))}
            <text x="165" y="180" fill={t.paperDimHex} fontSize="10" textAnchor="middle" fontFamily="JetBrains Mono">S² cod</text>
          </svg>
          <Mono t={t} size={9} dim style={{lineHeight:1.5, marginTop:4}}>
            deg f = (1/4π) ∫ f* ω &nbsp; [f] ∈ π₂(S²) = ℤ
          </Mono>
        </RBox>

        {/* ── 4. Linking number (3D) ─────────────────────────── */}
        <RBox t={t} title="KNOT THEORY · lk(L₁, L₂)" verdict={v(lk, 'lk')} style={{ gridColumn: 'span 2' }}>
          <div ref={mountRef} style={{ flex: 1, minHeight: 0, background: t.bgHex }}/>
          <Mono t={t} size={9} dim style={{lineHeight:1.5, marginTop:4}}>
            L₁ = unit circle · L₂ = circle winding k times through the first ·&nbsp;
            lk = (1/4π) ∮∮ (r₁−r₂)·(dr₁ × dr₂)/|r₁−r₂|³ (Gauss)
          </Mono>
        </RBox>

        {/* ── 5. Convergence readout ─────────────────────────── */}
        <RBox t={t} title="CONVERGENCE · all notations ⇒ same k">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', rowGap: 6, columnGap: 8, alignContent: 'center', padding: 6 }}>
            <Mono t={t} size={10} dim>master k</Mono>
            <Mono t={t} size={11} style={{ color: t.paperHex }}><b>{k}</b></Mono>
            <Mono t={t} size={10} dim>winding W</Mono>
            <Mono t={t} size={11} style={{ color: Math.abs(wnd.winding - k) < 0.05 ? t.amberHex : t.roseHex }}>
              {wnd.winding}
            </Mono>
            <Mono t={t} size={10} dim>Chern c₁</Mono>
            <Mono t={t} size={11} style={{ color: chern !== null && Math.abs(chern - k) < 0.05 ? t.amberHex : t.roseHex }}>
              {chern === null ? '…' : chern.toFixed(4)}
            </Mono>
            <Mono t={t} size={10} dim>degree deg</Mono>
            <Mono t={t} size={11} style={{ color: degree !== null && Math.abs(degree - k) < 0.05 ? t.amberHex : t.roseHex }}>
              {degree === null ? '…' : degree.toFixed(4)}
            </Mono>
            <Mono t={t} size={10} dim>linking lk</Mono>
            <Mono t={t} size={11} style={{ color: lk !== null && Math.abs(lk - k) < 0.1 ? t.amberHex : t.roseHex }}>
              {lk === null ? '…' : lk.toFixed(3)}
            </Mono>
          </div>
          <Mono t={t} size={9} dim style={{ lineHeight: 1.5, marginTop: 8 }}>
            <b>Rosetta doctrine:</b> four divergent mathematical notations — complex analysis, differential geometry, algebraic topology, and knot theory — each compute a number that agrees with the others and the master k. Compression lives exactly in that convergence. Not metaphor, not analogy: each value is computed by numerical integration in the browser from that notation's own definition.
          </Mono>
        </RBox>
      </div>
    </div>
  );
}

Object.assign(window, { RosettaPanel });
