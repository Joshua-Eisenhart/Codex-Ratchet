// Fiber Bundle Atlas — rich math visualization of the Hopf bundle π: S³ → S²
// Structure made explicit: base, fiber, total space, section (obstruction), connection, curvature, holonomy.
// Real geometry: fibers are great circles in S³, stereo-projected to circles in R³; any two fibers are linked with lk=1.
// Rosetta: quaternion q ∈ S³  ↔  complex (z₁,z₂) ∈ C² (|z₁|²+|z₂|²=1)  ↔  spherical (θ,φ,ψ).

// ────────────────────────────────────────────────────────────────────────────
// Core Hopf math
// Standard Hopf map π: S³ ⊂ C² → S² ⊂ R³, π(z₁,z₂) = (2·Re(z₁ z̄₂), 2·Im(z₁ z̄₂), |z₁|² − |z₂|²)
//
// A fiber over (X,Y,Z) ∈ S² is parametrized by ψ ∈ [0,2π).
// One convenient fiber parametrization (over a base point with spherical coords θ_b, φ_b):
//   z₁ = cos(θ_b/2) · e^{i(φ_b+ψ)/2}
//   z₂ = sin(θ_b/2) · e^{i(φ_b-ψ)/2}·e^{-iφ_b}·e^{iφ_b}   — simplified below
// We use: z₁ = cos(θ/2) e^{i(ξ+ψ)},  z₂ = sin(θ/2) e^{iψ}
// so that π gives (sinθ cos ξ, sinθ sin ξ, cosθ) and ψ sweeps the fiber.
// ────────────────────────────────────────────────────────────────────────────

function hopfFiberPoint(thetaB, phiB, psi) {
  // S¹ ↪ S³, sitting over the base (θ, φ) ∈ S². ψ sweeps the fiber.
  const c = Math.cos(thetaB / 2), s = Math.sin(thetaB / 2);
  const a1 = (phiB + psi) / 2, a2 = (phiB - psi) / 2;
  // Write quaternion q = (z₁, z₂) = (a + b i, c + d i) — 4 reals on S³
  return {
    x: c * Math.cos(a1),   // Re(z₁)
    y: c * Math.sin(a1),   // Im(z₁)
    z: s * Math.cos(-a2),  // Re(z₂)  (sign chosen so projection gives (sinθ cosφ, sinθ sinφ, cosθ))
    w: s * Math.sin(-a2),  // Im(z₂)
  };
}

// Stereographic projection S³ \ {N} → R³, N = (0,0,0,1).
// (x,y,z,w) → (x,y,z) / (1 − w). Returns {x,y,z} or null if at pole.
function stereo(p4) {
  const d = 1 - p4.w;
  if (Math.abs(d) < 1e-5) return null;
  return { x: p4.x / d, y: p4.y / d, z: p4.z / d };
}

// Sample a stereographically-projected fiber into R³ as a closed polyline.
// If the fiber passes too near the north pole, we break it (the circle goes to ∞ — draw long arc instead).
function fiberPolyline(thetaB, phiB, samples = 128) {
  const pts = [];
  let maxR = 0;
  for (let k = 0; k <= samples; k++) {
    const psi = (k / samples) * Math.PI * 2;
    const p4 = hopfFiberPoint(thetaB, phiB, psi);
    const p3 = stereo(p4);
    if (!p3) continue;
    const r = Math.sqrt(p3.x * p3.x + p3.y * p3.y + p3.z * p3.z);
    if (r > 50) continue; // truncate — visual cap
    if (r > maxR) maxR = r;
    pts.push([p3.x, p3.y, p3.z]);
  }
  return { pts, maxR };
}

// ────────────────────────────────────────────────────────────────────────────
// FiberBundleAtlas — top-level tab component
// ────────────────────────────────────────────────────────────────────────────

function FiberBundleAtlas({ t }) {
  const [panel, setPanel] = React.useState('anatomy');  // anatomy | connection | linking
  const [rosetta, setRosetta] = React.useState('spherical'); // spherical | complex | quaternion
  const [basePt, setBasePt] = React.useState({ theta: Math.PI / 3, phi: 0 });
  const [markedFibers, setMarkedFibers] = React.useState([
    { theta: Math.PI / 3, phi: 0.0, color: 'amber' },
    { theta: Math.PI / 3, phi: 2.2, color: 'rose' },
    { theta: 0.9, phi: 4.0, color: 'cyan' },
  ]);

  const panels = [
    { id: 'anatomy',    label: 'Bundle anatomy · π: S³→S²' },
    { id: 'connection', label: 'Connection · curvature · Chern' },
    { id: 'linking',    label: 'Fiber linking · lk(F_p, F_q)' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      {/* header */}
      <div style={{ borderBottom: `1px solid ${t.line}`, padding: '8px 14px', display: 'flex', gap: 10, alignItems: 'center' }}>
        <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>FIBER BUNDLE ATLAS · HOPF · S¹ ↪ S³ →^π S²</Mono>
        <div style={{ flex: 1 }} />
        <RosettaToggle t={t} value={rosetta} onChange={setRosetta} />
      </div>

      {/* sub-tabs */}
      <div style={{ display: 'flex', borderBottom: `1px solid ${t.line}` }}>
        {panels.map(p => {
          const on = panel === p.id;
          return (
            <div key={p.id} onClick={() => setPanel(p.id)}
              style={{
                padding: '7px 14px', cursor: 'pointer',
                borderRight: `1px solid ${t.line}`,
                background: on ? t.bg2 : 'transparent',
                borderBottom: on ? `2px solid ${t.amber}` : '2px solid transparent',
                marginBottom: -1,
              }}>
              <Mono t={t} size={10} dim={!on} style={{ letterSpacing: 0.8, textTransform: 'uppercase' }}>
                {p.label}
              </Mono>
            </div>
          );
        })}
      </div>

      {/* body */}
      <div style={{ flex: 1, minHeight: 0, overflow: 'auto', display: 'flex' }}>
        {panel === 'anatomy' && (
          <BundleAnatomyPanel
            t={t}
            rosetta={rosetta}
            basePt={basePt}
            setBasePt={setBasePt}
            markedFibers={markedFibers}
            setMarkedFibers={setMarkedFibers}
          />
        )}
        {panel === 'connection' && <ConnectionCurvaturePanel t={t} />}
        {panel === 'linking' && <LinkingPanel t={t} />}
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────────────
// Rosetta toggle — quaternion / complex pair / spherical
// ────────────────────────────────────────────────────────────────────────────

function RosettaToggle({ t, value, onChange }) {
  const opts = [
    { id: 'spherical',  label: '(θ,φ,ψ)' },
    { id: 'complex',    label: '(z₁,z₂)∈C²' },
    { id: 'quaternion', label: 'q∈ℍ' },
  ];
  return (
    <div style={{ display: 'flex', gap: 0, border: `1px solid ${t.line}` }}>
      {opts.map(o => {
        const on = value === o.id;
        return (
          <div key={o.id} onClick={() => onChange(o.id)}
            style={{
              padding: '4px 10px', cursor: 'pointer',
              background: on ? t.bg2 : 'transparent',
              borderRight: `1px solid ${t.line}`,
            }}>
            <Mono t={t} size={10} dim={!on}>{o.label}</Mono>
          </div>
        );
      })}
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────────────
// Panel 1 — Bundle anatomy
// Three linked views: base S² (draggable point), total space R³ (stereo-projected fibers), fiber circle (ψ sweep)
// ────────────────────────────────────────────────────────────────────────────

function BundleAnatomyPanel({ t, rosetta, basePt, setBasePt, markedFibers, setMarkedFibers }) {
  return (
    <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1.4fr', minHeight: 0 }}>
      {/* left column: base S² on top, fiber circle below */}
      <div style={{ display: 'flex', flexDirection: 'column', borderRight: `1px solid ${t.line}`, minHeight: 0 }}>
        <div style={{ flex: 1, minHeight: 0, borderBottom: `1px solid ${t.line}`, display: 'flex', flexDirection: 'column' }}>
          <PanelHeader t={t} title="Base · S²" right={<Mono t={t} size={9} dim>drag the point</Mono>} />
          <div style={{ flex: 1, minHeight: 0 }}>
            <BaseSphereCanvas t={t} basePt={basePt} setBasePt={setBasePt} markedFibers={markedFibers} setMarkedFibers={setMarkedFibers} />
          </div>
        </div>
        <div style={{ height: 170 }}>
          <PanelHeader t={t} title="Fiber · S¹" right={<Mono t={t} size={9} dim>ψ ∈ [0, 2π)</Mono>} />
          <FiberReadout t={t} basePt={basePt} rosetta={rosetta} />
        </div>
      </div>

      {/* right: total space */}
      <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <PanelHeader t={t} title="Total space · S³ (stereographic → R³)" right={<Mono t={t} size={9} dim>drag to orbit · scroll to zoom</Mono>} />
        <div style={{ flex: 1, minHeight: 0 }}>
          <TotalSpaceCanvas t={t} basePt={basePt} markedFibers={markedFibers} />
        </div>
        <div style={{ padding: '8px 14px', borderTop: `1px solid ${t.line}`, display: 'flex', gap: 16, alignItems: 'center' }}>
          <Mono t={t} size={9} dim>
            base B = S² · fiber F = S¹ · total E = S³ · group G = U(1) · π₁(E) = 0 · π₂(B) = Z · c₁(E) = 1
          </Mono>
          <div style={{ flex: 1 }} />
          <button onClick={() => setMarkedFibers([...markedFibers, { theta: basePt.theta, phi: basePt.phi, color: pickColor(markedFibers.length) }])} style={btn(t, true)}>
            pin fiber
          </button>
          <button onClick={() => setMarkedFibers([])} style={btn(t, false)}>clear</button>
        </div>
      </div>
    </div>
  );
}

function PanelHeader({ t, title, right }) {
  return (
    <div style={{ borderBottom: `1px solid ${t.line}`, padding: '6px 12px', display: 'flex', alignItems: 'center' }}>
      <Mono t={t} size={10} style={{ letterSpacing: 1.2, textTransform: 'uppercase' }}>{title}</Mono>
      <div style={{ flex: 1 }} />
      {right}
    </div>
  );
}

function pickColor(i) {
  const cs = ['amber', 'rose', 'cyan', 'violet'];
  return cs[i % cs.length];
}

// ────────────────────────────────────────────────────────────────────────────
// Base S² canvas — SVG, drag the base point, highlight pinned fibers as dots
// ────────────────────────────────────────────────────────────────────────────

function BaseSphereCanvas({ t, basePt, setBasePt, markedFibers, setMarkedFibers }) {
  const ref = React.useRef(null);
  const [dims, setDims] = React.useState({ w: 300, h: 260 });
  const [rot, setRot] = React.useState({ yaw: 0.6, pitch: 0.3 });
  const [dragging, setDragging] = React.useState(null); // 'orbit' | 'point' | null

  React.useEffect(() => {
    if (!ref.current) return;
    const ro = new ResizeObserver(() => {
      const r = ref.current.getBoundingClientRect();
      setDims({ w: r.width, h: r.height });
    });
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);

  const R = Math.min(dims.w, dims.h) * 0.38;
  const cx = dims.w / 2, cy = dims.h / 2;

  // Project a point on S² (unit) using current yaw/pitch to 2D
  const proj = (x, y, z) => {
    // yaw around y-axis, pitch around x-axis
    const cosY = Math.cos(rot.yaw), sinY = Math.sin(rot.yaw);
    const x1 = x * cosY + z * sinY;
    const z1 = -x * sinY + z * cosY;
    const cosP = Math.cos(rot.pitch), sinP = Math.sin(rot.pitch);
    const y2 = y * cosP - z1 * sinP;
    const z2 = y * sinP + z1 * cosP;
    return { u: cx + x1 * R, v: cy - y2 * R, depth: z2 };
  };

  const fromBasePt = bp => ({
    x: Math.sin(bp.theta) * Math.cos(bp.phi),
    y: Math.cos(bp.theta),
    z: Math.sin(bp.theta) * Math.sin(bp.phi),
  });

  const onPointerDown = (e) => {
    const rect = ref.current.getBoundingClientRect();
    const px = e.clientX - rect.left, py = e.clientY - rect.top;
    const p = fromBasePt(basePt);
    const pj = proj(p.x, p.y, p.z);
    const dx = px - pj.u, dy = py - pj.v;
    if (Math.hypot(dx, dy) < 12 && pj.depth >= -0.1) setDragging('point');
    else setDragging({ kind: 'orbit', x: e.clientX, y: e.clientY, yaw: rot.yaw, pitch: rot.pitch });
  };
  const onPointerMove = (e) => {
    if (!dragging) return;
    const rect = ref.current.getBoundingClientRect();
    if (dragging === 'point') {
      // Invert projection approximately: find θ,φ such that forward-proj lands on cursor
      const px = e.clientX - rect.left, py = e.clientY - rect.top;
      const u = (px - cx) / R, v = (cy - py) / R;
      const r2 = u * u + v * v;
      if (r2 > 1) return;
      // Un-pitch, un-yaw
      const w = Math.sqrt(Math.max(0, 1 - r2));
      // We assume the nearest hemisphere (w > 0 after inverse rotation)
      const cosP = Math.cos(-rot.pitch), sinP = Math.sin(-rot.pitch);
      const y0 = v;
      const y1 = y0 * cosP - w * sinP;
      const z1 = y0 * sinP + w * cosP;
      const cosY = Math.cos(-rot.yaw), sinY = Math.sin(-rot.yaw);
      const x1 = u * cosY + z1 * sinY;
      const z2 = -u * sinY + z1 * cosY;
      const theta = Math.acos(Math.max(-1, Math.min(1, y1)));
      const phi = Math.atan2(z2, x1);
      setBasePt({ theta, phi });
    } else if (dragging.kind === 'orbit') {
      const dx = e.clientX - dragging.x, dy = e.clientY - dragging.y;
      setRot({ yaw: dragging.yaw + dx * 0.008, pitch: Math.max(-1.3, Math.min(1.3, dragging.pitch + dy * 0.008)) });
    }
  };
  const onPointerUp = () => setDragging(null);

  // latitude + longitude grid
  const gridLines = [];
  for (let i = 1; i < 6; i++) {
    const th = (i / 6) * Math.PI;
    const pts = [];
    for (let j = 0; j <= 48; j++) {
      const ph = (j / 48) * Math.PI * 2;
      const p = proj(Math.sin(th) * Math.cos(ph), Math.cos(th), Math.sin(th) * Math.sin(ph));
      if (p.depth >= -0.05) pts.push([p.u, p.v]);
    }
    gridLines.push(pts);
  }
  for (let i = 0; i < 12; i++) {
    const ph = (i / 12) * Math.PI * 2;
    const pts = [];
    for (let j = 0; j <= 48; j++) {
      const th = (j / 48) * Math.PI;
      const p = proj(Math.sin(th) * Math.cos(ph), Math.cos(th), Math.sin(th) * Math.sin(ph));
      if (p.depth >= -0.05) pts.push([p.u, p.v]);
    }
    gridLines.push(pts);
  }

  const basePos = fromBasePt(basePt);
  const basePrj = proj(basePos.x, basePos.y, basePos.z);

  return (
    <div ref={ref} style={{ width: '100%', height: '100%', cursor: dragging === 'point' ? 'grabbing' : 'grab', userSelect: 'none' }}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerLeave={onPointerUp}>
      <svg width={dims.w} height={dims.h}>
        {/* sphere outline */}
        <circle cx={cx} cy={cy} r={R} stroke={t.line} fill="none" />
        {/* grid */}
        {gridLines.map((pts, i) => (
          <polyline key={i} points={pts.map(p => p.join(',')).join(' ')} stroke={t.line} fill="none" opacity={0.4} />
        ))}
        {/* pinned fibers (base points) */}
        {markedFibers.map((m, i) => {
          const p = { x: Math.sin(m.theta) * Math.cos(m.phi), y: Math.cos(m.theta), z: Math.sin(m.theta) * Math.sin(m.phi) };
          const pj = proj(p.x, p.y, p.z);
          if (pj.depth < -0.1) return null;
          return <g key={i}>
            <circle cx={pj.u} cy={pj.v} r={4} fill={t[m.color + 'Hex']} />
          </g>;
        })}
        {/* current base point */}
        {basePrj.depth >= -0.1 && (
          <g>
            <circle cx={basePrj.u} cy={basePrj.v} r={8} fill="none" stroke={t.paper} strokeWidth={2} />
            <circle cx={basePrj.u} cy={basePrj.v} r={3} fill={t.paper} />
          </g>
        )}
        {/* axis labels */}
        <text x={cx + R + 8} y={cy + 4} fill={t.paperDim} fontSize={9} fontFamily="JetBrains Mono">x</text>
        <text x={cx} y={cy - R - 4} fill={t.paperDim} fontSize={9} fontFamily="JetBrains Mono" textAnchor="middle">y</text>
        {/* readout */}
        <text x={10} y={dims.h - 26} fill={t.paperDim} fontSize={10} fontFamily="JetBrains Mono">θ = {basePt.theta.toFixed(3)} rad  ({(basePt.theta / Math.PI).toFixed(3)}π)</text>
        <text x={10} y={dims.h - 12} fill={t.paperDim} fontSize={10} fontFamily="JetBrains Mono">φ = {basePt.phi.toFixed(3)} rad  ({(basePt.phi / Math.PI).toFixed(3)}π)</text>
      </svg>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────────────
// Fiber readout — shows the current fiber parametrically in the active Rosetta notation
// ────────────────────────────────────────────────────────────────────────────

function FiberReadout({ t, basePt, rosetta }) {
  const [psi, setPsi] = React.useState(0);
  const p4 = hopfFiberPoint(basePt.theta, basePt.phi, psi);
  const norm = Math.sqrt(p4.x * p4.x + p4.y * p4.y + p4.z * p4.z + p4.w * p4.w);

  let body;
  if (rosetta === 'quaternion') {
    body = (
      <div>
        <Mono t={t} size={10} dim>q = a + b𝐢 + c𝐣 + d𝐤  ·  |q|² = 1</Mono>
        <div style={{ marginTop: 4 }}>
          <Mono t={t} size={11} style={{ color: t.paper }}>a = {p4.x.toFixed(4)}  b = {p4.y.toFixed(4)}  c = {p4.z.toFixed(4)}  d = {p4.w.toFixed(4)}</Mono>
        </div>
        <div style={{ marginTop: 2 }}>
          <Mono t={t} size={10} style={{ color: t.amber }}>|q| = {norm.toFixed(6)}</Mono>
        </div>
      </div>
    );
  } else if (rosetta === 'complex') {
    const z1_re = p4.x, z1_im = p4.y;
    const z2_re = p4.z, z2_im = p4.w;
    const m1 = Math.sqrt(z1_re * z1_re + z1_im * z1_im);
    const m2 = Math.sqrt(z2_re * z2_re + z2_im * z2_im);
    body = (
      <div>
        <Mono t={t} size={10} dim>(z₁, z₂) ∈ C²  ·  |z₁|² + |z₂|² = 1</Mono>
        <div style={{ marginTop: 4 }}>
          <Mono t={t} size={11}>z₁ = {fmtComplex(z1_re, z1_im)}  (|z₁| = {m1.toFixed(4)})</Mono><br />
          <Mono t={t} size={11}>z₂ = {fmtComplex(z2_re, z2_im)}  (|z₂| = {m2.toFixed(4)})</Mono>
        </div>
        <div style={{ marginTop: 2 }}>
          <Mono t={t} size={10} style={{ color: t.amber }}>|z₁|² + |z₂|² = {(m1 * m1 + m2 * m2).toFixed(6)}</Mono>
        </div>
      </div>
    );
  } else {
    body = (
      <div>
        <Mono t={t} size={10} dim>base (θ, φ) on S²  ·  fiber coord ψ on S¹</Mono>
        <div style={{ marginTop: 4 }}>
          <Mono t={t} size={11}>θ = {basePt.theta.toFixed(4)}  φ = {basePt.phi.toFixed(4)}  ψ = {psi.toFixed(4)}</Mono>
        </div>
        <div style={{ marginTop: 2 }}>
          <Mono t={t} size={10} style={{ color: t.amber }}>π(q) = (sinθ cosφ, sinθ sinφ, cosθ)</Mono>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '8px 12px' }}>
      {body}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 10 }}>
        <Mono t={t} size={9} dim style={{ minWidth: 30 }}>ψ</Mono>
        <input type="range" min={0} max={Math.PI * 2} step={0.02} value={psi}
          onChange={e => setPsi(parseFloat(e.target.value))}
          style={{ flex: 1, accentColor: t.amber }} />
        <Mono t={t} size={9} style={{ color: t.paper, minWidth: 48, textAlign: 'right' }}>
          {(psi / Math.PI).toFixed(2)}π
        </Mono>
      </div>
    </div>
  );
}

function fmtComplex(re, im) {
  const sign = im >= 0 ? '+' : '−';
  return `${re.toFixed(4)} ${sign} ${Math.abs(im).toFixed(4)}𝑖`;
}

// ────────────────────────────────────────────────────────────────────────────
// Total space canvas — 3D, fibers as closed circles in R³ (stereo-projected)
// ────────────────────────────────────────────────────────────────────────────

function TotalSpaceCanvas({ t, basePt, markedFibers }) {
  const mountRef = React.useRef(null);
  const stateRef = React.useRef({ basePt, markedFibers });
  React.useEffect(() => { stateRef.current = { basePt, markedFibers }; }, [basePt, markedFibers]);

  React.useEffect(() => {
    if (!window.THREE) return;
    const THREE = window.THREE;
    const mount = mountRef.current; if (!mount) return;
    const w = mount.clientWidth || 500, h = mount.clientHeight || 420;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(t.bgHex);
    const camera = new THREE.PerspectiveCamera(50, w / h, 0.05, 100);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(w, h);
    mount.innerHTML = '';
    mount.appendChild(renderer.domElement);
    scene.add(new THREE.AmbientLight(0xffffff, 0.8));

    // axes (R³ frame after stereo projection)
    const axLen = 3;
    const mkAx = (dir, c) => {
      const g = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), dir.clone().multiplyScalar(axLen)]);
      return new THREE.Line(g, new THREE.LineBasicMaterial({ color: c, transparent: true, opacity: 0.35 }));
    };
    scene.add(mkAx(new THREE.Vector3(1, 0, 0), t.paperDimHex));
    scene.add(mkAx(new THREE.Vector3(0, 1, 0), t.paperDimHex));
    scene.add(mkAx(new THREE.Vector3(0, 0, 1), t.paperDimHex));

    // equator of S³ (w=0) stereographically projects to the unit sphere — draw faint
    const unit = new THREE.Mesh(
      new THREE.SphereGeometry(1, 30, 20),
      new THREE.MeshBasicMaterial({ color: t.paperDimHex, wireframe: true, transparent: true, opacity: 0.12 })
    );
    scene.add(unit);

    // Fiber line group — rebuilt each frame from state
    const fiberGroup = new THREE.Group();
    scene.add(fiberGroup);
    const liveGroup = new THREE.Group();
    scene.add(liveGroup);

    // orbit camera
    const orbit = { azim: 0.8, elev: 0.3, dist: 5.5 };
    const apply = () => {
      camera.position.set(
        orbit.dist * Math.cos(orbit.elev) * Math.sin(orbit.azim),
        orbit.dist * Math.sin(orbit.elev),
        orbit.dist * Math.cos(orbit.elev) * Math.cos(orbit.azim),
      );
      camera.lookAt(0, 0, 0);
    };
    apply();
    let drag = false, lx = 0, ly = 0;
    const md = e => { drag = true; lx = e.clientX; ly = e.clientY; };
    const mm = e => {
      if (!drag) return;
      orbit.azim -= (e.clientX - lx) * 0.006;
      orbit.elev = Math.max(-1.3, Math.min(1.3, orbit.elev + (e.clientY - ly) * 0.006));
      lx = e.clientX; ly = e.clientY; apply();
    };
    const mu = () => drag = false;
    const onWheel = e => { e.preventDefault(); orbit.dist = Math.max(1.2, Math.min(30, orbit.dist + e.deltaY * 0.005)); apply(); };
    mount.addEventListener('mousedown', md);
    mount.addEventListener('wheel', onWheel, { passive: false });
    window.addEventListener('mousemove', mm);
    window.addEventListener('mouseup', mu);

    const ro = new ResizeObserver(() => {
      const nw = mount.clientWidth, nh = mount.clientHeight;
      if (nw > 0 && nh > 0) { renderer.setSize(nw, nh); camera.aspect = nw / nh; camera.updateProjectionMatrix(); }
    });
    ro.observe(mount);

    // Build one fiber as a TubeGeometry along the stereographic polyline
    const buildFiber = (theta, phi, colorHex, isLive) => {
      const { pts } = fiberPolyline(theta, phi, 256);
      if (pts.length < 4) return null;
      const v3 = pts.map(p => new THREE.Vector3(p[0], p[1], p[2]));
      // close (if not truncated)
      const d = v3[0].distanceTo(v3[v3.length - 1]);
      if (d < 5) v3.push(v3[0].clone());
      const curve = new THREE.CatmullRomCurve3(v3, false);
      const geo = new THREE.TubeGeometry(curve, Math.min(400, v3.length * 2), isLive ? 0.02 : 0.015, 8, false);
      const mat = new THREE.MeshBasicMaterial({
        color: colorHex,
        transparent: true,
        opacity: isLive ? 0.95 : 0.75,
      });
      return new THREE.Mesh(geo, mat);
    };

    let raf;
    let lastState = null;
    const loop = () => {
      const { basePt, markedFibers } = stateRef.current;
      const sig = `${basePt.theta.toFixed(4)},${basePt.phi.toFixed(4)}|${markedFibers.map(m => `${m.theta.toFixed(4)},${m.phi.toFixed(4)},${m.color}`).join(';')}`;
      if (sig !== lastState) {
        lastState = sig;
        // clear
        [fiberGroup, liveGroup].forEach(g => {
          while (g.children.length) {
            const c = g.children.pop();
            if (c.geometry) c.geometry.dispose();
            if (c.material) c.material.dispose();
          }
        });
        // pinned
        markedFibers.forEach(m => {
          const mesh = buildFiber(m.theta, m.phi, t[m.color + 'Hex'], false);
          if (mesh) fiberGroup.add(mesh);
        });
        // live (current base)
        const live = buildFiber(basePt.theta, basePt.phi, t.paperHex, true);
        if (live) liveGroup.add(live);
      }
      renderer.render(scene, camera);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      mount.removeEventListener('mousedown', md);
      mount.removeEventListener('wheel', onWheel);
      window.removeEventListener('mousemove', mm);
      window.removeEventListener('mouseup', mu);
      [fiberGroup, liveGroup].forEach(g => {
        while (g.children.length) {
          const c = g.children.pop();
          if (c.geometry) c.geometry.dispose();
          if (c.material) c.material.dispose();
        }
      });
      renderer.dispose();
    };
  }, [t.bg]);

  return <div ref={mountRef} style={{ width: '100%', height: '100%', cursor: 'grab' }} />;
}

// ────────────────────────────────────────────────────────────────────────────
// Panel 2 — Connection · curvature · Chern number
// Show the connection 1-form A and curvature 2-form F = dA on S².
// For the Hopf bundle, in spherical coords with gauge fixed on the chart excluding the south pole:
//   A_+ = (1 − cosθ)/2  dφ    (on U_+ = S² \ {S})
// Curvature: F = dA = (sinθ)/2  dθ ∧ dφ
// Chern: c₁ = (1/2π) ∫_{S²} F = 1
// ────────────────────────────────────────────────────────────────────────────

function ConnectionCurvaturePanel({ t }) {
  const [thetaCap, setThetaCap] = React.useState(Math.PI / 2);

  // flux through spherical cap of polar angle θ_cap:
  //   Φ(θ) = ∫₀^{θ} ∫₀^{2π} (sinθ')/2 dφ dθ' = π (1 − cosθ)
  //   normalize by 2π → Chern fraction in cap = (1 − cos θ)/2
  const capFraction = (1 - Math.cos(thetaCap)) / 2;
  const capFlux = 2 * Math.PI * capFraction;
  const totalFlux = 2 * Math.PI;

  return (
    <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: 0 }}>
      <div style={{ borderRight: `1px solid ${t.line}`, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <PanelHeader t={t} title="Connection A+ · U(1) gauge" />
        <div style={{ padding: 16, flex: 1, display: 'flex', flexDirection: 'column', gap: 14, minHeight: 0 }}>
          <Mono t={t} size={11} dim style={{ lineHeight: 1.5 }}>
            The Hopf bundle does not admit a global section. On the chart U_+ = S² \ {S} (excluding the south pole), a natural U(1) connection is
          </Mono>
          <Formula t={t} tex="A_+ = ½ (1 − cos θ) dφ" />
          <Mono t={t} size={11} dim style={{ lineHeight: 1.5 }}>
            On U_− = S² \ {N} the gauge-equivalent form is
          </Mono>
          <Formula t={t} tex="A_− = −½ (1 + cos θ) dφ" />
          <Mono t={t} size={11} dim style={{ lineHeight: 1.5 }}>
            Transition on the overlap U_+ ∩ U_− (equator) is the U(1) gauge change
          </Mono>
          <Formula t={t} tex="g_{+−} = e^{iφ}  ·  winding n = 1 generates π₁(U(1)) = Z" />
          <div style={{ flex: 1 }} />
          <Mono t={t} size={10} dim style={{ lineHeight: 1.5 }}>
            Obstruction to a global section ⇔ nontrivial transition winding ⇔ c₁ ≠ 0. The Hopf bundle is the unique (up to iso) principal U(1)-bundle over S² with c₁ = 1.
          </Mono>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <PanelHeader t={t} title="Curvature F = dA · Chern integration" />
        <div style={{ padding: 16, flex: 1, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Formula t={t} tex="F = dA_+ = ½ sin θ dθ ∧ dφ" />
          <Formula t={t} tex="c₁ = (1/2π) ∫_{S²} F = (1/2π) · 2π · ∫₀^π ½ sin θ dθ = 1" />

          <div style={{ marginTop: 6 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
              <Mono t={t} size={10} dim>cap extent θ_c</Mono>
              <Mono t={t} size={10} style={{ color: t.paper }}>{(thetaCap / Math.PI).toFixed(2)}π</Mono>
            </div>
            <input type="range" min={0.01} max={Math.PI - 0.01} step={0.02}
              value={thetaCap} onChange={e => setThetaCap(parseFloat(e.target.value))}
              style={{ width: '100%', marginTop: 6, accentColor: t.amber }} />
          </div>

          <div style={{ marginTop: 4, display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '6px 14px', alignItems: 'baseline' }}>
            <Mono t={t} size={10} dim>Φ(θ_c)</Mono>
            <Mono t={t} size={11} style={{ color: t.amber }}>{capFlux.toFixed(4)} rad</Mono>
            <Mono t={t} size={10} dim>Φ(θ_c)/2π</Mono>
            <Mono t={t} size={11} style={{ color: t.amber }}>{capFraction.toFixed(4)}</Mono>
            <Mono t={t} size={10} dim>full S²</Mono>
            <Mono t={t} size={11} style={{ color: t.paper }}>{totalFlux.toFixed(4)} rad  →  c₁ = 1</Mono>
          </div>

          <CapFluxBar t={t} cap={capFraction} />
          <Mono t={t} size={10} dim style={{ lineHeight: 1.5 }}>
            As θ_c sweeps 0 → π, the cap flux sweeps 0 → 2π. The integer quantization of ∫F/2π is what the *topology* forces — any smooth connection on this bundle gives the same integer.
          </Mono>
        </div>
      </div>
    </div>
  );
}

function Formula({ t, tex }) {
  return (
    <div style={{ padding: '10px 14px', background: t.bg2, border: `1px solid ${t.line}` }}>
      <Mono t={t} size={12} style={{ color: t.paper, letterSpacing: 0.5 }}>{tex}</Mono>
    </div>
  );
}

function CapFluxBar({ t, cap }) {
  return (
    <div style={{ display: 'flex', height: 14, border: `1px solid ${t.line}` }}>
      <div style={{ width: `${cap * 100}%`, background: t.amber, transition: 'width 60ms' }} />
      <div style={{ flex: 1 }} />
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────────────
// Panel 3 — Linking number between two fibers
// Any two distinct Hopf fibers in S³ are linked with linking number = 1.
// We project both to R³ and compute lk via signed crossings on a chosen projection plane.
// ────────────────────────────────────────────────────────────────────────────

function LinkingPanel({ t }) {
  const [p, setP] = React.useState({ theta: Math.PI / 3, phi: 0.2 });
  const [q, setQ] = React.useState({ theta: Math.PI / 3, phi: 2.5 });

  // Compute linking number by signed crossings on the xz-plane projection
  const lk = computeLinkingNumber(p, q);

  return (
    <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: 0 }}>
      <div style={{ borderRight: `1px solid ${t.line}`, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <PanelHeader t={t} title="Two fibers in R³ (stereo-projected)" />
        <div style={{ flex: 1, minHeight: 0 }}>
          <TwoFiberCanvas t={t} p={p} q={q} />
        </div>
      </div>
      <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 14, overflow: 'auto' }}>
        <Mono t={t} size={11} dim style={{ lineHeight: 1.5 }}>
          Two distinct fibers F_p, F_q of the Hopf map are disjoint great circles in S³. Stereographically projected to R³, they form <b style={{ color: t.paper }}>linked circles</b>.
        </Mono>
        <Formula t={t} tex="lk(F_p, F_q) = c₁(E) = 1  for all p ≠ q" />

        <Mono t={t} size={10} dim style={{ letterSpacing: 1.5, marginTop: 6 }}>BASE POINT P</Mono>
        <FiberSlider t={t} label="θ_p" value={p.theta} min={0.05} max={Math.PI - 0.05} onChange={v => setP({ ...p, theta: v })} />
        <FiberSlider t={t} label="φ_p" value={p.phi} min={0} max={Math.PI * 2} onChange={v => setP({ ...p, phi: v })} />

        <Mono t={t} size={10} dim style={{ letterSpacing: 1.5, marginTop: 6 }}>BASE POINT Q</Mono>
        <FiberSlider t={t} label="θ_q" value={q.theta} min={0.05} max={Math.PI - 0.05} onChange={v => setQ({ ...q, theta: v })} />
        <FiberSlider t={t} label="φ_q" value={q.phi} min={0} max={Math.PI * 2} onChange={v => setQ({ ...q, phi: v })} />

        <div style={{ padding: 14, background: t.bg2, border: `1px solid ${t.line}` }}>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>COMPUTED LINKING NUMBER</Mono>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginTop: 6 }}>
            <Mono t={t} size={28} style={{ color: lk === 1 ? t.amber : (lk === 0 ? t.paperDim : t.rose) }}>{lk}</Mono>
            <Mono t={t} size={10} dim>via signed crossings · xz-plane projection</Mono>
          </div>
          <Mono t={t} size={10} dim style={{ display: 'block', marginTop: 6, lineHeight: 1.4 }}>
            Expected: lk = 1 for distinct p, q (topological invariant of the Hopf fibration). If you hit the same base point (p = q) the two fibers coincide and crossings degenerate.
          </Mono>
        </div>
      </div>
    </div>
  );
}

function FiberSlider({ t, label, value, min, max, onChange }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <Mono t={t} size={10} dim style={{ minWidth: 36 }}>{label}</Mono>
      <input type="range" min={min} max={max} step={0.02} value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        style={{ flex: 1, accentColor: t.amber }} />
      <Mono t={t} size={10} style={{ color: t.paper, minWidth: 52, textAlign: 'right' }}>
        {(value / Math.PI).toFixed(2)}π
      </Mono>
    </div>
  );
}

// Signed-crossings linking number.
// Project both closed curves to xz-plane. At each crossing, use y as height to assign sign.
function computeLinkingNumber(p, q) {
  const { pts: A } = fiberPolyline(p.theta, p.phi, 256);
  const { pts: B } = fiberPolyline(q.theta, q.phi, 256);
  if (A.length < 4 || B.length < 4) return 0;
  const lines2D = (pts) => {
    const L = [];
    for (let i = 0; i < pts.length - 1; i++) L.push([pts[i], pts[i + 1]]);
    L.push([pts[pts.length - 1], pts[0]]);
    return L;
  };
  const La = lines2D(A), Lb = lines2D(B);
  let crossings = 0;
  for (const a of La) {
    const [a0, a1] = a;
    for (const b of Lb) {
      const [b0, b1] = b;
      // 2D intersection test on xz plane (indices 0 and 2)
      const r = segSeg(a0[0], a0[2], a1[0], a1[2], b0[0], b0[2], b1[0], b1[2]);
      if (!r) continue;
      // y-height of A at crossing vs B at crossing
      const ya = a0[1] + r.ta * (a1[1] - a0[1]);
      const yb = b0[1] + r.tb * (b1[1] - b0[1]);
      // tangent directions projected to xz
      const ax = a1[0] - a0[0], az = a1[2] - a0[2];
      const bx = b1[0] - b0[0], bz = b1[2] - b0[2];
      const cross = ax * bz - az * bx; // z-component of 2D cross
      const sign = (ya > yb ? 1 : -1) * (cross >= 0 ? 1 : -1);
      crossings += sign;
    }
  }
  // Gauss formula: lk = (1/2) Σ signed crossings
  return Math.round(crossings / 2);
}

function segSeg(x1, y1, x2, y2, x3, y3, x4, y4) {
  const d = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3);
  if (Math.abs(d) < 1e-12) return null;
  const ta = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / d;
  const tb = ((x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)) / d;
  if (ta < 0 || ta > 1 || tb < 0 || tb > 1) return null;
  return { ta, tb };
}

function TwoFiberCanvas({ t, p, q }) {
  const mountRef = React.useRef(null);
  const stateRef = React.useRef({ p, q });
  React.useEffect(() => { stateRef.current = { p, q }; }, [p, q]);

  React.useEffect(() => {
    if (!window.THREE) return;
    const THREE = window.THREE;
    const mount = mountRef.current; if (!mount) return;
    const w = mount.clientWidth || 500, h = mount.clientHeight || 420;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(t.bgHex);
    const camera = new THREE.PerspectiveCamera(50, w / h, 0.05, 100);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(w, h);
    mount.innerHTML = '';
    mount.appendChild(renderer.domElement);
    scene.add(new THREE.AmbientLight(0xffffff, 0.8));

    // unit ref sphere
    scene.add(new THREE.Mesh(
      new THREE.SphereGeometry(1, 28, 18),
      new THREE.MeshBasicMaterial({ color: t.paperDimHex, wireframe: true, transparent: true, opacity: 0.1 })
    ));

    // axes
    const axLen = 2.5;
    const mkAx = (dir, c) => {
      const g = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), dir.clone().multiplyScalar(axLen)]);
      return new THREE.Line(g, new THREE.LineBasicMaterial({ color: c, transparent: true, opacity: 0.35 }));
    };
    scene.add(mkAx(new THREE.Vector3(1, 0, 0), t.paperDimHex));
    scene.add(mkAx(new THREE.Vector3(0, 1, 0), t.paperDimHex));
    scene.add(mkAx(new THREE.Vector3(0, 0, 1), t.paperDimHex));

    const group = new THREE.Group();
    scene.add(group);

    const orbit = { azim: 0.8, elev: 0.3, dist: 4.5 };
    const apply = () => {
      camera.position.set(
        orbit.dist * Math.cos(orbit.elev) * Math.sin(orbit.azim),
        orbit.dist * Math.sin(orbit.elev),
        orbit.dist * Math.cos(orbit.elev) * Math.cos(orbit.azim),
      );
      camera.lookAt(0, 0, 0);
    };
    apply();
    let drag = false, lx = 0, ly = 0;
    const md = e => { drag = true; lx = e.clientX; ly = e.clientY; };
    const mm = e => {
      if (!drag) return;
      orbit.azim -= (e.clientX - lx) * 0.006;
      orbit.elev = Math.max(-1.3, Math.min(1.3, orbit.elev + (e.clientY - ly) * 0.006));
      lx = e.clientX; ly = e.clientY; apply();
    };
    const mu = () => drag = false;
    const onWheel = e => { e.preventDefault(); orbit.dist = Math.max(1.2, Math.min(25, orbit.dist + e.deltaY * 0.005)); apply(); };
    mount.addEventListener('mousedown', md);
    mount.addEventListener('wheel', onWheel, { passive: false });
    window.addEventListener('mousemove', mm);
    window.addEventListener('mouseup', mu);

    const ro = new ResizeObserver(() => {
      const nw = mount.clientWidth, nh = mount.clientHeight;
      if (nw > 0 && nh > 0) { renderer.setSize(nw, nh); camera.aspect = nw / nh; camera.updateProjectionMatrix(); }
    });
    ro.observe(mount);

    const buildFiber = (theta, phi, colorHex) => {
      const { pts } = fiberPolyline(theta, phi, 256);
      if (pts.length < 4) return null;
      const v3 = pts.map(p => new THREE.Vector3(p[0], p[1], p[2]));
      const d = v3[0].distanceTo(v3[v3.length - 1]);
      if (d < 5) v3.push(v3[0].clone());
      const curve = new THREE.CatmullRomCurve3(v3, false);
      const geo = new THREE.TubeGeometry(curve, Math.min(400, v3.length * 2), 0.025, 8, false);
      return new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: colorHex, transparent: true, opacity: 0.9 }));
    };

    let raf;
    let lastSig = null;
    const loop = () => {
      const { p, q } = stateRef.current;
      const sig = `${p.theta.toFixed(4)},${p.phi.toFixed(4)}|${q.theta.toFixed(4)},${q.phi.toFixed(4)}`;
      if (sig !== lastSig) {
        lastSig = sig;
        while (group.children.length) {
          const c = group.children.pop();
          if (c.geometry) c.geometry.dispose();
          if (c.material) c.material.dispose();
        }
        const a = buildFiber(p.theta, p.phi, t.amberHex);
        const b = buildFiber(q.theta, q.phi, t.cyanHex);
        if (a) group.add(a);
        if (b) group.add(b);
      }
      renderer.render(scene, camera);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      mount.removeEventListener('mousedown', md);
      mount.removeEventListener('wheel', onWheel);
      window.removeEventListener('mousemove', mm);
      window.removeEventListener('mouseup', mu);
      while (group.children.length) {
        const c = group.children.pop();
        if (c.geometry) c.geometry.dispose();
        if (c.material) c.material.dispose();
      }
      renderer.dispose();
    };
  }, [t.bg]);

  return <div ref={mountRef} style={{ width: '100%', height: '100%', cursor: 'grab' }} />;
}

Object.assign(window, { FiberBundleAtlas });
