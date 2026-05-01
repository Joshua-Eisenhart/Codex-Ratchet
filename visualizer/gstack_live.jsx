// G-Stack Live (nested) — ONE shared three.js scene where shells carry shells.
// M(C) watermark grid, then S³ as the stage, Hopf fibers on it, tori foliating
// S³, Weyl spinors on a torus, a G-tower ladder to the side, holonomy loop
// on the Bloch base, Connes geodesics between states.
//
// Couplings rendered as live A∘B vs B∘A mini-panels below, on one clock.

function GStackLiveView({ t, data }) {
  const gs = data.gStack;
  const mountRef = React.useRef(null);
  const stateRef = React.useRef(null);
  const [running, setRunning] = React.useState(true);
  const [highlight, setHighlight] = React.useState(null); // layer id
  const [submode, setSubmode] = React.useState('nested'); // 'nested' | 'layers' | 'couplings'

  // main nested scene
  React.useEffect(() => {
    if (!window.THREE) return;
    const THREE = window.THREE;
    const mount = mountRef.current;
    if (!mount) return;
    const w = mount.clientWidth, h = mount.clientHeight;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(t.bgHex);
    const camera = new THREE.PerspectiveCamera(38, w/h, 0.1, 200);
    camera.position.set(4.5, 3.2, 6);
    camera.lookAt(0,0,0);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(w, h);
    mount.innerHTML = '';
    mount.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffffff, 0.55));
    const d = new THREE.DirectionalLight(0xffffff, 0.6); d.position.set(4,6,4); scene.add(d);

    // --- M(C) watermark grid (large, faint, behind everything) ---
    const mcGrid = new THREE.Mesh(
      new THREE.PlaneGeometry(12, 12, 24, 24),
      new THREE.MeshBasicMaterial({ color: t.amberHex, wireframe: true, transparent: true, opacity: 0.06 })
    );
    mcGrid.rotation.x = -Math.PI/2;
    mcGrid.position.y = -2;
    scene.add(mcGrid);
    const mcLabel = mkTextSprite(THREE, 'M(C)', t.amberHex, 0.06);
    mcLabel.position.set(-5, -1.9, -5);
    scene.add(mcLabel);

    // --- S³ hosting shell (wireframe sphere) ---
    const s3 = new THREE.Group();
    scene.add(s3);
    const s3Mesh = new THREE.Mesh(
      new THREE.SphereGeometry(1.8, 32, 24),
      new THREE.MeshBasicMaterial({ color: t.amberHex, wireframe: true, transparent: true, opacity: 0.22 })
    );
    s3.add(s3Mesh);

    // --- Hopf fibers ON S³ (living inside it) ---
    const hopfFibers = new THREE.Group();
    s3.add(hopfFibers);
    const N_FIB = 10;
    const fibers = [];
    for (let i = 0; i < N_FIB; i++) {
      const phi = (i/N_FIB) * Math.PI * 2;
      const theta = Math.PI/3 + (i%3) * 0.22;
      const cx = Math.sin(theta) * Math.cos(phi) * 1.3;
      const cy = Math.cos(theta) * 1.3;
      const cz = Math.sin(theta) * Math.sin(phi) * 1.3;
      const geo = new THREE.TorusGeometry(0.38, 0.018, 6, 40);
      const mat = new THREE.MeshBasicMaterial({ color: t.cyanHex, transparent: true, opacity: 0.75 });
      const m = new THREE.Mesh(geo, mat);
      m.position.set(cx, cy, cz);
      m.rotation.x = theta;
      m.rotation.y = phi;
      hopfFibers.add(m);
      fibers.push({ mesh: m, phase: i * 0.5 });
    }

    // --- Tori foliating S³ (nested inside, with one Clifford highlighted) ---
    const toriGroup = new THREE.Group();
    s3.add(toriGroup);
    const etas = [0.2, 0.35, 0.5, 0.65, 0.8];
    const tori = [];
    etas.forEach((eta, i) => {
      const R = 1.0, tr = 0.35 + 0.1 * Math.sin(eta * Math.PI);
      const geo = new THREE.TorusGeometry(R, tr * 0.4, 10, 56);
      const clifford = Math.abs(eta - 0.5) < 0.05;
      const mat = new THREE.MeshBasicMaterial({
        color: clifford ? t.violetHex : t.amberHex,
        wireframe: true,
        transparent: true, opacity: clifford ? 0.9 : 0.25,
      });
      const m = new THREE.Mesh(geo, mat);
      m.rotation.x = Math.PI/2;
      toriGroup.add(m);
      tori.push({ mesh: m, clifford });
    });

    // --- Weyl spinors ON the Clifford torus (two counter-rotating cones) ---
    const weylGroup = new THREE.Group();
    s3.add(weylGroup);
    const wL = new THREE.Mesh(
      new THREE.ConeGeometry(0.12, 0.26, 12, 1, true),
      new THREE.MeshBasicMaterial({ color: t.violetHex, wireframe: true })
    );
    const wR = new THREE.Mesh(
      new THREE.ConeGeometry(0.12, 0.26, 12, 1, true),
      new THREE.MeshBasicMaterial({ color: t.roseHex, wireframe: true })
    );
    weylGroup.add(wL); weylGroup.add(wR);

    // --- Holonomy loop on the base S² (below S³, a small sphere) ---
    const baseGroup = new THREE.Group();
    baseGroup.position.set(2.8, -0.5, 0);
    scene.add(baseGroup);
    const baseSph = new THREE.Mesh(
      new THREE.SphereGeometry(0.7, 20, 14),
      new THREE.MeshBasicMaterial({ color: t.amberHex, wireframe: true, transparent: true, opacity: 0.3 })
    );
    baseGroup.add(baseSph);
    // loop
    const loopN = 60;
    const loopPts = [];
    for (let i = 0; i <= loopN; i++) {
      const ph = (i/loopN) * Math.PI * 2;
      const th = Math.PI/3;
      loopPts.push(new THREE.Vector3(
        0.71 * Math.sin(th) * Math.cos(ph),
        0.71 * Math.cos(th),
        0.71 * Math.sin(th) * Math.sin(ph)
      ));
    }
    const loop = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(loopPts),
      new THREE.LineBasicMaterial({ color: t.cyanHex })
    );
    baseGroup.add(loop);
    const berryDot = new THREE.Mesh(
      new THREE.SphereGeometry(0.04, 8, 8),
      new THREE.MeshBasicMaterial({ color: t.cyanHex })
    );
    baseGroup.add(berryDot);
    const baseLabel = mkTextSprite(THREE, 'S² base · Berry loop', t.paperDimHex, 0.04);
    baseLabel.position.set(0, -1.0, 0);
    baseGroup.add(baseLabel);

    // --- G-tower ladder (to the side) ---
    const gtGroup = new THREE.Group();
    gtGroup.position.set(-3.2, 0, 0);
    scene.add(gtGroup);
    const steps = ['GL','O','SO','U','SU','Sp'];
    const gBoxes = [];
    steps.forEach((s, i) => {
      const sz = 0.7 - i * 0.08;
      const geo = new THREE.BoxGeometry(sz, 0.15, sz);
      const edges = new THREE.EdgesGeometry(geo);
      const m = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: t.violetHex, transparent: true, opacity: 0.7 }));
      m.position.y = -1.3 + i * 0.42;
      gtGroup.add(m);
      gBoxes.push(m);
      // label
      const lbl = mkTextSprite(THREE, s, t.violetHex, 0.05);
      lbl.position.set(0.55, m.position.y, 0);
      gtGroup.add(lbl);
    });
    const gtLabel = mkTextSprite(THREE, 'G-tower · CANDIDATE', t.violetHex, 0.05);
    gtLabel.position.set(0, 1.5, 0);
    gtGroup.add(gtLabel);

    // --- Connes geodesic pair on the base ---
    const connesGroup = new THREE.Group();
    connesGroup.position.set(2.8, -0.5, 0);
    scene.add(connesGroup);
    const cp1 = new THREE.Mesh(new THREE.SphereGeometry(0.05, 10, 10), new THREE.MeshBasicMaterial({ color: t.roseHex }));
    const cp2 = new THREE.Mesh(new THREE.SphereGeometry(0.05, 10, 10), new THREE.MeshBasicMaterial({ color: t.roseHex }));
    connesGroup.add(cp1); connesGroup.add(cp2);
    const arc = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineDashedMaterial({ color: t.roseHex, dashSize: 0.05, gapSize: 0.03 }));
    connesGroup.add(arc);

    // --- layer labels ---
    const s3Label = mkTextSprite(THREE, 'S³ · host', t.amberHex, 0.055);
    s3Label.position.set(0, 2.0, 0); s3.add(s3Label);

    // --- hand-rolled orbit controls ---
    const controls = { azim: 0.5, elev: 0.35, dist: 8, target: new THREE.Vector3(0,0,0) };
    const applyCam = () => {
      const { azim, elev, dist, target } = controls;
      camera.position.set(
        target.x + dist * Math.cos(elev) * Math.sin(azim),
        target.y + dist * Math.sin(elev),
        target.z + dist * Math.cos(elev) * Math.cos(azim)
      );
      camera.lookAt(target);
    };
    applyCam();
    let dragging = false, lastX=0, lastY=0;
    const onDown = e => { dragging=true; lastX=e.clientX; lastY=e.clientY; mount.style.cursor='grabbing'; };
    const onMove = e => {
      if (!dragging) return;
      controls.azim -= (e.clientX - lastX) * 0.005;
      controls.elev = Math.max(-1.2, Math.min(1.2, controls.elev + (e.clientY - lastY) * 0.005));
      lastX = e.clientX; lastY = e.clientY;
      applyCam();
    };
    const onUp = () => { dragging=false; mount.style.cursor='grab'; };
    const onWheel = e => { e.preventDefault(); controls.dist = Math.max(3, Math.min(20, controls.dist + e.deltaY * 0.01)); applyCam(); };
    mount.addEventListener('mousedown', onDown);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    mount.addEventListener('wheel', onWheel, { passive: false });
    mount.style.cursor = 'grab';

    // --- resize observer (flex layout may settle after mount) ---
    const ro = new ResizeObserver(() => {
      const nw = mount.clientWidth, nh = mount.clientHeight;
      if (nw > 0 && nh > 0) {
        renderer.setSize(nw, nh);
        camera.aspect = nw / nh;
        camera.updateProjectionMatrix();
      }
    });
    ro.observe(mount);

    // --- animation loop ---
    let raf;
    const start = performance.now();
    const animate = () => {
      const time = (performance.now() - start) / 1000;
      if (stateRef.current.running) {
        // S³ slow rotation
        s3.rotation.y = time * 0.2;
        // fibers spin on their own axes (bundle flow)
        fibers.forEach((f, i) => { f.mesh.rotation.z = time * 0.9 + f.phase; });
        // tori — Clifford pulses
        tori.forEach((to, i) => {
          if (to.clifford) to.mesh.material.opacity = 0.55 + 0.35 * Math.sin(time * 1.2);
        });
        // Weyl — on Clifford torus, opposite rotations
        const ang = time * 0.8;
        const R = 1.0, r = 0.4;
        const u = ang, v = ang * 2;
        wL.position.set((R + r*Math.cos(v))*Math.cos(u), r*Math.sin(v), (R + r*Math.cos(v))*Math.sin(u));
        wL.rotation.y = time * 1.2;
        const u2 = -ang, v2 = -ang * 2;
        wR.position.set((R + r*Math.cos(v2))*Math.cos(u2), r*Math.sin(v2), (R + r*Math.cos(v2))*Math.sin(u2));
        wR.rotation.y = -time * 1.2;
        // G-tower pulse sweep
        const ph = (time * 0.5) % steps.length;
        gBoxes.forEach((b, i) => {
          const d = Math.min(Math.abs(i - ph), steps.length - Math.abs(i - ph));
          b.material.opacity = 0.3 + 0.6 * Math.max(0, 1 - d);
        });
        // Berry dot on loop
        const bp = time * 1.3;
        const bth = Math.PI/3;
        berryDot.position.set(
          0.72 * Math.sin(bth) * Math.cos(bp),
          0.72 * Math.cos(bth),
          0.72 * Math.sin(bth) * Math.sin(bp)
        );
        // Connes pair + geodesic
        const a1 = time * 0.5, a2 = time * 0.5 + Math.PI * 0.8;
        const cth = Math.PI/2 + Math.sin(time*0.3)*0.25;
        const c1v = new THREE.Vector3(0.72 * Math.sin(cth)*Math.cos(a1), 0.72*Math.cos(cth), 0.72*Math.sin(cth)*Math.sin(a1));
        const c2v = new THREE.Vector3(0.72 * Math.sin(cth)*Math.cos(a2), 0.72*Math.cos(cth), 0.72*Math.sin(cth)*Math.sin(a2));
        cp1.position.copy(c1v); cp2.position.copy(c2v);
        // great-circle arc
        const v1n = c1v.clone().normalize(), v2n = c2v.clone().normalize();
        const om = Math.acos(Math.max(-1, Math.min(1, v1n.dot(v2n))));
        const sO = Math.sin(om) || 1;
        const arcPts = [];
        for (let i = 0; i <= 30; i++) {
          const s = i/30;
          const a = Math.sin((1-s)*om)/sO, b = Math.sin(s*om)/sO;
          arcPts.push(new THREE.Vector3(
            0.73 * (a*v1n.x + b*v2n.x),
            0.73 * (a*v1n.y + b*v2n.y),
            0.73 * (a*v1n.z + b*v2n.z)
          ));
        }
        arc.geometry.dispose();
        arc.geometry = new THREE.BufferGeometry().setFromPoints(arcPts);
        arc.computeLineDistances();
      }
      renderer.render(scene, camera);
      raf = requestAnimationFrame(animate);
    };
    stateRef.current = { running: true };
    raf = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      mount.removeEventListener('mousedown', onDown);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      mount.removeEventListener('wheel', onWheel);
      renderer.dispose();
    };
  }, [t.bg, submode]);

  React.useEffect(() => {
    if (stateRef.current) stateRef.current.running = running;
  }, [running]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, overflow: 'hidden' }}>
      {/* submode tabs */}
      <div style={{ display: 'flex', borderBottom: `1px solid ${t.line}`, background: t.bg2 }}>
        {[
          ['nested', 'Nested · geometry on geometry'],
          ['layers', 'Per-layer sims · live invariants'],
          ['couplings', 'Pairwise couplings · A∘B vs B∘A'],
        ].map(([k, label]) => (
          <button key={k} onClick={() => setSubmode(k)} style={{
            padding: '8px 14px', background: submode===k ? t.bg : 'transparent',
            border: 'none', borderRight: `1px solid ${t.line}`,
            borderBottom: submode===k ? `2px solid ${t.amber}` : '2px solid transparent',
            color: submode===k ? t.paper : t.paperDim,
            fontFamily: 'JetBrains Mono, ui-monospace, monospace',
            fontSize: 10, letterSpacing: 1.3, textTransform: 'uppercase',
            cursor: 'pointer',
          }}>{label}</button>
        ))}
        <div style={{ flex: 1 }}/>
      </div>

      {submode === 'nested' && (
        <>
          <div style={{ padding: '8px 16px', borderBottom: `1px solid ${t.line}`, display: 'flex', gap: 14, alignItems: 'center' }}>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>G-STACK · LIVE · GEOMETRY ON GEOMETRY</Mono>
            <div style={{ flex: 1 }}/>
            <Mono t={t} size={9} dim>drag to orbit · scroll to zoom</Mono>
            <button onClick={() => setRunning(r => !r)} style={btn(t, running)}>{running?'running':'paused'}</button>
          </div>

          <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 300px', minHeight: 420 }}>
            <div ref={mountRef} style={{ background: t.bg, minHeight: 420 }}/>
            <div style={{ borderLeft: `1px solid ${t.line}`, overflow: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
              <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>WHAT'S IN THE SCENE</Mono>
              <LegendRow t={t} color={t.amber} shape="square" label="M(C) watermark · primary surface" />
              <LegendRow t={t} color={t.amber} shape="circle" label="S³ host shell (unit quaternions)" />
              <LegendRow t={t} color={t.cyan} shape="ring" label="Hopf fibers · on S³" />
              <LegendRow t={t} color={t.violet} shape="ring" label="Tori foliation · Clifford at η=π/4" />
              <LegendRow t={t} color={t.violet} shape="cone" label="Weyl ψ_L / ψ_R · on Clifford torus" />
              <LegendRow t={t} color={t.violet} shape="ladder" label="G-tower ladder · CANDIDATE, shell-local only" />
              <LegendRow t={t} color={t.cyan} shape="loop" label="Berry holonomy · loop on S² base" />
              <LegendRow t={t} color={t.rose} shape="arc" label="Connes geodesic · spectral-triple distance" />
              <div style={{ height: 1, background: t.line, margin: '6px 0' }}/>
              <Mono t={t} size={9} dim style={{ lineHeight: 1.5 }}>
                Nesting is geometric: S³ hosts Hopf fibers and tori; Weyl spinors live on a torus; base S² is S³/U(1);
                Berry loop lives on the base. G-tower sits beside as candidate reduction chain.
              </Mono>
            </div>
          </div>
        </>
      )}

      {submode === 'layers' && (
        <div style={{ flex: 1, overflow: 'auto', padding: 12, background: t.bg2 }}>
          <div style={{ display: 'flex', gap: 14, alignItems: 'baseline', marginBottom: 10 }}>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>PER-LAYER LIVE SIMS · EACH LAYER'S CHARACTERISTIC INVARIANT</Mono>
            <div style={{ flex: 1 }}/>
            <Mono t={t} size={9} dim>independent clocks · drag canvas to orbit</Mono>
          </div>
          <LayerSimsStrip t={t} gs={gs} />
          <div style={{ marginTop: 10, padding: 10, border: `1px dashed ${t.line}`, display: 'flex', gap: 10, alignItems: 'baseline' }}>
            <Tag t={t} tone="paperFaint">skipped</Tag>
            <Mono t={t} size={10} dim>
              M(C) is rhetorical (no chartable manifold); G-tower is marked CANDIDATE per user doctrine — shell-local only, no full-chain sim exists.
            </Mono>
          </div>
        </div>
      )}

      {submode === 'couplings' && (
        <div style={{ flex: 1, overflow: 'auto', padding: 12, background: t.bg2 }}>
          <div style={{ display: 'flex', gap: 14, alignItems: 'baseline', marginBottom: 10 }}>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>PAIRWISE COUPLINGS · A∘B vs B∘A · non-comm = ratchet</Mono>
            <div style={{ flex: 1 }}/>
            <button onClick={() => setRunning(r => !r)} style={btn(t, running)}>{running?'running':'paused'}</button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 10 }}>
            {gs.couplings.filter(c => c.a !== 'MC' && c.b !== '*').map((c, i) => (
              <CouplingMiniSim key={c.id} t={t} coupling={c} gs={gs} seed={i * 1.7} running={running} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function LegendRow({ t, color, shape, label }) {
  const sw = 16, sh = 12;
  let glyph;
  if (shape === 'square') glyph = <div style={{ width: sw, height: sh, background: color, opacity: 0.35 }}/>;
  else if (shape === 'circle') glyph = <div style={{ width: sw, height: sh, border: `1px solid ${color}`, borderRadius: '50%' }}/>;
  else if (shape === 'ring') glyph = <div style={{ width: sw, height: sh/2, border: `1px solid ${color}`, borderRadius: sw }}/>;
  else if (shape === 'cone') glyph = <div style={{ width: 0, height: 0, borderLeft: `${sw/2}px solid transparent`, borderRight: `${sw/2}px solid transparent`, borderBottom: `${sh}px solid ${color}` }}/>;
  else if (shape === 'ladder') glyph = <div style={{ width: sw, height: sh, borderTop: `1px dashed ${color}`, borderBottom: `1px dashed ${color}`}}/>;
  else if (shape === 'loop') glyph = <div style={{ width: sw, height: sh, border: `1px solid ${color}`, borderRadius: '50%', borderStyle: 'dashed' }}/>;
  else glyph = <div style={{ width: sw, height: sh, background: color }}/>;
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      <div style={{ width: 18, display: 'flex', justifyContent: 'center' }}>{glyph}</div>
      <Mono t={t} size={10} dim style={{ lineHeight: 1.35 }}>{label}</Mono>
    </div>
  );
}

// Tiny A∘B vs B∘A sim in a single canvas per coupling.
function CouplingMiniSim({ t, coupling, gs, seed, running }) {
  const a = gs.layers.find(l => l.id === coupling.a);
  const b = gs.layers.find(l => l.id === coupling.b);
  if (!a || !b) return null;
  const isOpen = coupling.status === 'open';
  const tone = isOpen ? t.rose : (coupling.type === 'noncomm' ? t.amber : coupling.type === 'rosetta' ? t.violet : t.paperDim);
  const mountRef = React.useRef(null);
  const refState = React.useRef({ time: 0, running: true });
  const [drift, setDrift] = React.useState(0);

  React.useEffect(() => {
    if (!window.THREE || isOpen) return;
    const THREE = window.THREE;
    const mount = mountRef.current;
    if (!mount) return;
    const w = mount.clientWidth, h = mount.clientHeight;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(t.bgHex);
    const camera = new THREE.PerspectiveCamera(40, w/h, 0.1, 50);
    camera.position.set(1.6, 1.0, 2.3); camera.lookAt(0,0,0);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(w, h);
    mount.innerHTML = '';
    mount.appendChild(renderer.domElement);
    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const sph = new THREE.Mesh(
      new THREE.SphereGeometry(1, 18, 12),
      new THREE.MeshBasicMaterial({ color: t.lineHex, wireframe: true, transparent: true, opacity: 0.2 })
    );
    scene.add(sph);
    const c1 = new THREE.Color(t.amberHex);
    const c2 = new THREE.Color(t.roseHex);
    const h1 = new THREE.Mesh(new THREE.SphereGeometry(0.07, 10, 10), new THREE.MeshBasicMaterial({ color: c1 }));
    const h2 = new THREE.Mesh(new THREE.SphereGeometry(0.07, 10, 10), new THREE.MeshBasicMaterial({ color: c2 }));
    scene.add(h1); scene.add(h2);
    const T = 50;
    const tp1 = Array.from({length:T}, () => new THREE.Vector3());
    const tp2 = Array.from({length:T}, () => new THREE.Vector3());
    const tl1 = new THREE.Line(new THREE.BufferGeometry().setFromPoints(tp1), new THREE.LineBasicMaterial({ color: c1, transparent: true, opacity: 0.8 }));
    const tl2 = new THREE.Line(new THREE.BufferGeometry().setFromPoints(tp2), new THREE.LineBasicMaterial({ color: c2, transparent: true, opacity: 0.8 }));
    scene.add(tl1); scene.add(tl2);
    let raf;
    const start = performance.now();
    const loop = () => {
      if (refState.current.running) {
        const time = (performance.now() - start) / 1000 + seed;
        refState.current.time = time;
        const rotX = new THREE.Matrix4().makeRotationX(Math.sin(time * 0.7) * 0.9);
        const rotZ = new THREE.Matrix4().makeRotationZ(Math.cos(time * 0.5) * 0.9);
        const p1 = new THREE.Vector3(1,0,0).applyMatrix4(rotZ).applyMatrix4(rotX);
        const p2 = new THREE.Vector3(1,0,0).applyMatrix4(rotX).applyMatrix4(rotZ);
        h1.position.copy(p1); h2.position.copy(p2);
        for (let i = 0; i < tp1.length-1; i++) { tp1[i].copy(tp1[i+1]); tp2[i].copy(tp2[i+1]); }
        tp1[tp1.length-1].copy(p1); tp2[tp2.length-1].copy(p2);
        tl1.geometry.dispose(); tl1.geometry = new THREE.BufferGeometry().setFromPoints(tp1);
        tl2.geometry.dispose(); tl2.geometry = new THREE.BufferGeometry().setFromPoints(tp2);
        const d = p1.distanceTo(p2);
        setDrift(d);
      }
      renderer.render(scene, camera);
      raf = requestAnimationFrame(loop);
    };
    refState.current.running = running;
    raf = requestAnimationFrame(loop);
    const ro = new ResizeObserver(() => {
      const nw = mount.clientWidth, nh = mount.clientHeight;
      if (nw > 0 && nh > 0) {
        renderer.setSize(nw, nh);
        camera.aspect = nw / nh;
        camera.updateProjectionMatrix();
      }
    });
    ro.observe(mount);
    return () => { cancelAnimationFrame(raf); ro.disconnect(); renderer.dispose(); };
  }, [t.bg, isOpen]);

  React.useEffect(() => { refState.current.running = running; }, [running]);

  return (
    <div style={{ border: `1px ${isOpen?'dashed':'solid'} ${tone}`, background: t.bg, display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '6px 10px', borderBottom: `1px solid ${t.line}`, display: 'flex', gap: 6, alignItems: 'baseline' }}>
        <Mono t={t} size={11}>{a.name} ∘ {b.name}</Mono>
        <div style={{ flex: 1 }}/>
        <Tag t={t} tone={isOpen?'rose':(coupling.type==='noncomm'?'amber':coupling.type==='rosetta'?'violet':'paperDim')}>{coupling.type}</Tag>
      </div>
      {isOpen ? (
        <div style={{ height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: `repeating-linear-gradient(45deg, transparent 0 6px, ${t.line} 6px 7px)` }}>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>SIM MISSING</Mono>
        </div>
      ) : (
        <div ref={mountRef} style={{ height: 120, background: t.bg }}/>
      )}
      <div style={{ padding: '5px 10px', borderTop: `1px solid ${t.line}`, display: 'flex', gap: 8, alignItems: 'center' }}>
        <Mono t={t} size={9} dim>‖Δ‖</Mono>
        <div style={{ flex: 1, height: 3, background: t.bg2, border: `1px solid ${t.line}` }}>
          <div style={{ height: '100%', width: `${Math.min(100, drift * 50)}%`, background: tone }}/>
        </div>
        <Mono t={t} size={9} style={{ color: tone }}>{isOpen ? '—' : drift.toFixed(2)}</Mono>
      </div>
      <div style={{ padding: '5px 10px' }}>
        <Mono t={t} size={9} dim style={{ lineHeight: 1.35 }}>{coupling.claim}</Mono>
      </div>
    </div>
  );
}

// Tiny text sprite helper
function mkTextSprite(THREE, text, color, scale) {
  const canvas = document.createElement('canvas');
  canvas.width = 256; canvas.height = 64;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = color;
  ctx.font = 'bold 36px "JetBrains Mono", monospace';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 128, 32);
  const tx = new THREE.CanvasTexture(canvas);
  const m = new THREE.SpriteMaterial({ map: tx, transparent: true });
  const s = new THREE.Sprite(m);
  s.scale.set(scale * 16, scale * 4, 1);
  return s;
}

Object.assign(window, { GStackLiveView });
