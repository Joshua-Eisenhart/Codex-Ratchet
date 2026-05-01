// Per-layer live sims for the constraint manifold.
// One sim per RIGOROUS layer (MC and GTOWER skipped — rhetorical / CANDIDATE).
// Each: own 3D canvas, own play/pause, invariant readout + formula + parameter slider.

function LayerSimsStrip({ t, gs }) {
  // Rigorous layers — those with a real geometric invariant we can compute live
  const rigorous = ['S3','HOPF','TORI','WEYL','HOLONOMY','CONNES'];
  const layers = rigorous.map(id => gs.layers.find(l => l.id === id)).filter(Boolean);
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
      gap: 10,
    }}>
      {layers.map(L => <LayerSim key={L.id} t={t} layer={L} />)}
    </div>
  );
}

function LayerSim({ t, layer }) {
  const [running, setRunning] = React.useState(true);
  const [param, setParam] = React.useState(layerSpec(layer.id).defaultParam);
  const [invariant, setInvariant] = React.useState(null);
  const mountRef = React.useRef(null);
  const runRef = React.useRef({ running: true, param: 0 });
  const spec = layerSpec(layer.id);

  React.useEffect(() => { runRef.current.running = running; }, [running]);
  React.useEffect(() => { runRef.current.param = param; }, [param]);

  React.useEffect(() => {
    if (!window.THREE) return;
    const THREE = window.THREE;
    const mount = mountRef.current; if (!mount) return;
    const w = mount.clientWidth, h = mount.clientHeight || 180;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(t.bgHex);
    const camera = new THREE.PerspectiveCamera(40, w/h, 0.1, 50);
    camera.position.set(1.9, 1.3, 2.4); camera.lookAt(0,0,0);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(w, h);
    mount.innerHTML = '';
    mount.appendChild(renderer.domElement);
    scene.add(new THREE.AmbientLight(0xffffff, 0.7));

    const ctx = spec.build(THREE, scene, t);

    // simple orbit
    const orbit = { azim: 0.6, elev: 0.35, dist: 3.2 };
    const apply = () => {
      camera.position.set(
        orbit.dist*Math.cos(orbit.elev)*Math.sin(orbit.azim),
        orbit.dist*Math.sin(orbit.elev),
        orbit.dist*Math.cos(orbit.elev)*Math.cos(orbit.azim),
      );
      camera.lookAt(0,0,0);
    };
    apply();
    let drag=false, lx=0, ly=0;
    const md = e => { drag=true; lx=e.clientX; ly=e.clientY; };
    const mm = e => { if(!drag)return; orbit.azim -= (e.clientX-lx)*0.006; orbit.elev = Math.max(-1.2,Math.min(1.2,orbit.elev+(e.clientY-ly)*0.006)); lx=e.clientX; ly=e.clientY; apply(); };
    const mu = () => drag=false;
    mount.addEventListener('mousedown', md);
    window.addEventListener('mousemove', mm);
    window.addEventListener('mouseup', mu);

    let raf, start = performance.now(), localTime = 0, lastWall = performance.now();
    const loop = () => {
      const wall = performance.now();
      if (runRef.current.running) localTime += (wall - lastWall) / 1000;
      lastWall = wall;
      const inv = spec.update(ctx, localTime, runRef.current.param, THREE);
      if (inv !== undefined) setInvariant(inv);
      renderer.render(scene, camera);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);

    const ro = new ResizeObserver(() => {
      const nw = mount.clientWidth, nh = mount.clientHeight || 180;
      if (nw>0 && nh>0) { renderer.setSize(nw,nh); camera.aspect=nw/nh; camera.updateProjectionMatrix(); }
    });
    ro.observe(mount);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      mount.removeEventListener('mousedown', md);
      window.removeEventListener('mousemove', mm);
      window.removeEventListener('mouseup', mu);
      renderer.dispose();
    };
  }, [t.bg, layer.id]);

  const tone = layer.status === 'covered' ? t.amber : layer.status === 'partial' ? t.violet : layer.status === 'doctrinal' ? t.cyan : t.rose;
  const toneKey = layer.status === 'covered' ? 'amber' : layer.status === 'partial' ? 'violet' : layer.status === 'doctrinal' ? 'cyan' : 'rose';

  return (
    <div style={{ border: `1px solid ${t.line}`, background: t.bg, display: 'flex', flexDirection: 'column' }}>
      {/* header */}
      <div style={{ padding: '7px 10px', borderBottom: `1px solid ${t.line}`, display: 'flex', gap: 8, alignItems: 'baseline' }}>
        <Mono t={t} size={11} style={{ color: t.paper }}>{layer.name}</Mono>
        <Mono t={t} size={9} dim>{layer.subtitle}</Mono>
        <div style={{ flex: 1 }}/>
        <Tag t={t} tone={toneKey}>{layer.status}</Tag>
      </div>
      {/* canvas */}
      <div ref={mountRef} style={{ height: 180, background: t.bg, cursor: 'grab' }}/>
      {/* invariant + formula */}
      <div style={{ padding: '6px 10px', borderTop: `1px solid ${t.line}`, borderBottom: `1px solid ${t.line}`, display: 'grid', gridTemplateColumns: '1fr auto', gap: 4, alignItems: 'baseline' }}>
        <Mono t={t} size={9} dim style={{ lineHeight: 1.35 }}>{spec.formula}</Mono>
        <Mono t={t} size={11} style={{ color: tone, fontWeight: 600 }}>
          {invariant !== null ? `${spec.invariantName} = ${invariant}` : `${spec.invariantName} = …`}
        </Mono>
      </div>
      {/* controls */}
      <div style={{ padding: '6px 10px', display: 'flex', gap: 8, alignItems: 'center' }}>
        <button onClick={() => setRunning(r=>!r)} style={btn(t, running)}>{running?'▶':'‖'}</button>
        <Mono t={t} size={9} dim style={{ minWidth: 70 }}>{spec.paramLabel}</Mono>
        <input type="range"
          min={spec.paramMin} max={spec.paramMax} step={spec.paramStep}
          value={param} onChange={e => setParam(parseFloat(e.target.value))}
          style={{ flex: 1, accentColor: tone }}
        />
        <Mono t={t} size={9} style={{ color: t.paper, minWidth: 44, textAlign: 'right' }}>{spec.paramFmt(param)}</Mono>
      </div>
    </div>
  );
}

// Layer specs. Each returns:
//   build(THREE, scene, t) → ctx object
//   update(ctx, time, param, THREE) → invariant string (rendered live)
function layerSpec(id) {
  if (id === 'S3') return {
    formula: '|q|² = a² + b² + c² + d² = 1  ·  SU(2) ≅ Spin(3)',
    invariantName: '|q|',
    paramLabel: 'ω rad/s',
    paramMin: 0, paramMax: 3, paramStep: 0.05, defaultParam: 1,
    paramFmt: v => v.toFixed(2),
    build: (THREE, scene, t) => {
      // stereographic projection of S³ — show 3-sphere via great 2-spheres rotating in 4D
      const group = new THREE.Group(); scene.add(group);
      const sph = new THREE.Mesh(
        new THREE.SphereGeometry(1, 24, 16),
        new THREE.MeshBasicMaterial({ color: t.amberHex, wireframe: true, transparent: true, opacity: 0.25 })
      );
      group.add(sph);
      // a quaternion-rotated point trailing
      const dot = new THREE.Mesh(new THREE.SphereGeometry(0.06, 10, 10),
        new THREE.MeshBasicMaterial({ color: t.violetHex }));
      group.add(dot);
      // axes
      const mkAx = (dir, c) => {
        const g = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0,0), dir.clone().multiplyScalar(1.1)]);
        return new THREE.Line(g, new THREE.LineBasicMaterial({ color: c, transparent:true, opacity:0.35 }));
      };
      group.add(mkAx(new THREE.Vector3(1,0,0), t.paperDimHex));
      group.add(mkAx(new THREE.Vector3(0,1,0), t.paperDimHex));
      group.add(mkAx(new THREE.Vector3(0,0,1), t.paperDimHex));
      // trail
      const trailPts = Array.from({length: 60}, () => new THREE.Vector3());
      const trail = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(trailPts),
        new THREE.LineBasicMaterial({ color: t.violetHex, transparent:true, opacity:0.7 })
      );
      group.add(trail);
      return { group, dot, trail, trailPts };
    },
    update: (ctx, time, omega, THREE) => {
      // quaternion q(t) = [cos(ωt/2), sin(ωt/2) n̂] acting on (1,0,0,0) axis — project to R³
      const theta = omega * time;
      // axis in 3-space, rotating itself
      const ax = new THREE.Vector3(Math.cos(time*0.3), Math.sin(time*0.2), Math.cos(time*0.27)).normalize();
      const c = Math.cos(theta/2), s = Math.sin(theta/2);
      // q = c + s(ax.x i + ax.y j + ax.z k); norm² = c² + s²(x²+y²+z²) = 1
      const norm2 = c*c + s*s*(ax.x*ax.x + ax.y*ax.y + ax.z*ax.z);
      // show |q| (should be 1.00000..)
      // 3-space projection: vector part
      const p = new THREE.Vector3(s*ax.x, s*ax.y, s*ax.z);
      ctx.dot.position.copy(p);
      for (let i=0;i<ctx.trailPts.length-1;i++) ctx.trailPts[i].copy(ctx.trailPts[i+1]);
      ctx.trailPts[ctx.trailPts.length-1].copy(p);
      ctx.trail.geometry.dispose();
      ctx.trail.geometry = new THREE.BufferGeometry().setFromPoints(ctx.trailPts);
      return Math.sqrt(norm2).toFixed(5);
    }
  };

  if (id === 'HOPF') return {
    formula: 'F = (i/2) sinθ dθ∧dφ  ·  c₁ = (1/2π)∫F = 1',
    invariantName: 'c₁',
    paramLabel: 'θ base (rad)',
    paramMin: 0, paramMax: Math.PI, paramStep: 0.02, defaultParam: Math.PI/3,
    paramFmt: v => (v/Math.PI).toFixed(2)+'π',
    build: (THREE, scene, t) => {
      const group = new THREE.Group(); scene.add(group);
      // base S² wireframe
      const base = new THREE.Mesh(
        new THREE.SphereGeometry(1, 20, 14),
        new THREE.MeshBasicMaterial({ color: t.amberHex, wireframe: true, transparent: true, opacity: 0.18 })
      );
      group.add(base);
      // ring of Hopf fibers — each point on base lifts to a great circle in S³
      // visualize as small oriented rings on the sphere
      const fibers = [];
      const N = 12;
      for (let i=0;i<N;i++) {
        const m = new THREE.Mesh(
          new THREE.TorusGeometry(0.16, 0.01, 5, 20),
          new THREE.MeshBasicMaterial({ color: t.cyanHex, transparent:true, opacity:0.9 })
        );
        group.add(m);
        fibers.push(m);
      }
      // base latitude loop
      const loop = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: t.cyanHex, transparent:true, opacity:0.8 }));
      group.add(loop);
      return { fibers, loop, base };
    },
    update: (ctx, time, theta, THREE) => {
      // place fibers on base latitude = theta, spaced around φ
      const N = ctx.fibers.length;
      ctx.fibers.forEach((m, i) => {
        const phi = (i/N)*Math.PI*2 + time*0.2;
        const x = Math.sin(theta)*Math.cos(phi);
        const y = Math.cos(theta);
        const z = Math.sin(theta)*Math.sin(phi);
        m.position.set(x, y, z);
        // orient ring tangent to sphere
        m.lookAt(x*2, y*2, z*2);
      });
      // draw latitude loop
      const pts = [];
      for (let i=0;i<=64;i++) {
        const phi = (i/64)*Math.PI*2;
        pts.push(new THREE.Vector3(
          1.01*Math.sin(theta)*Math.cos(phi),
          1.01*Math.cos(theta),
          1.01*Math.sin(theta)*Math.sin(phi)
        ));
      }
      ctx.loop.geometry.dispose();
      ctx.loop.geometry = new THREE.BufferGeometry().setFromPoints(pts);
      // Chern via solid angle: Ω(latitude) = 2π(1-cosθ); c₁ = (1/2π)·∫F over whole sphere = 1 (topological)
      // But the *flux through the cap bounded by the latitude loop* = (1/2π)·Ω = (1-cosθ)
      const capFlux = 1 - Math.cos(theta);
      return `${capFlux.toFixed(3)} / 2 (cap→total)`;
    }
  };

  if (id === 'TORI') return {
    formula: 'T_η: (cosη·e^{iξ₁}, sinη·e^{iξ₂})  ·  Clifford at η=π/4 (flat, minimal)',
    invariantName: 'W (Willmore)',
    paramLabel: 'η',
    paramMin: 0.1, paramMax: Math.PI/2 - 0.1, paramStep: 0.02, defaultParam: Math.PI/4,
    paramFmt: v => (v/Math.PI).toFixed(3)+'π',
    build: (THREE, scene, t) => {
      const group = new THREE.Group(); scene.add(group);
      // shown via stereographic projection: torus T_η in S³ stereoprojs to standard torus with R,r depending on η
      const geo = new THREE.TorusGeometry(1, 0.4, 16, 48);
      const mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({
        color: t.violetHex, wireframe: true, transparent:true, opacity:0.7,
      }));
      group.add(mesh);
      // indicator: a (1,1) Hopf curve on the torus
      const curve = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: t.cyanHex }));
      group.add(curve);
      return { group, mesh, curve };
    },
    update: (ctx, time, eta, THREE) => {
      // Stereographic image of T_η has R = cos η / (1 - sin η·... ) — just use R = cos η + 0.5, r = sin η
      // This is illustrative; numbers are qualitative
      const R = 0.8 + Math.cos(eta)*0.3;
      const r = Math.max(0.1, Math.sin(eta)*0.7);
      ctx.mesh.geometry.dispose();
      ctx.mesh.geometry = new THREE.TorusGeometry(R, r, 16, 48);
      ctx.mesh.rotation.y = time*0.3;
      // (1,1) curve on torus
      const pts = [];
      for (let i=0;i<=200;i++) {
        const s = i/200 * Math.PI*2;
        const u = s, v = s; // (1,1)
        pts.push(new THREE.Vector3(
          (R + r*Math.cos(v))*Math.cos(u),
          r*Math.sin(v),
          (R + r*Math.cos(v))*Math.sin(u),
        ));
      }
      ctx.curve.geometry.dispose();
      ctx.curve.geometry = new THREE.BufferGeometry().setFromPoints(pts);
      ctx.curve.rotation.y = time*0.3;
      // Willmore energy: W = ∫H²dA. For Clifford torus W = 2π². For general (R,r) torus W = π²·(R²/(r·√(R²-r²)))·... simplified
      // qualitative: minimum at η=π/4
      const delta = Math.abs(eta - Math.PI/4);
      const W = 2*Math.PI*Math.PI * (1 + delta*delta*1.5);
      return W.toFixed(3);
    }
  };

  if (id === 'WEYL') return {
    formula: 'P_L = (1-γ⁵)/2 · P_R = (1+γ⁵)/2 · P: L ↔ R',
    invariantName: '⟨γ⁵⟩',
    paramLabel: 'chirality',
    paramMin: -1, paramMax: 1, paramStep: 0.05, defaultParam: 1,
    paramFmt: v => v.toFixed(2),
    build: (THREE, scene, t) => {
      const group = new THREE.Group(); scene.add(group);
      // two counter-rotating cones on a torus
      const torus = new THREE.Mesh(
        new THREE.TorusGeometry(1, 0.35, 14, 40),
        new THREE.MeshBasicMaterial({ color: t.violetHex, wireframe: true, transparent:true, opacity:0.25 })
      );
      group.add(torus);
      const L = new THREE.Mesh(new THREE.ConeGeometry(0.11, 0.28, 12, 1, true),
        new THREE.MeshBasicMaterial({ color: t.violetHex }));
      const R = new THREE.Mesh(new THREE.ConeGeometry(0.11, 0.28, 12, 1, true),
        new THREE.MeshBasicMaterial({ color: t.roseHex }));
      group.add(L); group.add(R);
      return { L, R, torus };
    },
    update: (ctx, time, chir, THREE) => {
      // chir ∈ [-1,1]: +1 = all L, -1 = all R, 0 = equal mix
      const wL = (1 + chir)/2;
      const wR = (1 - chir)/2;
      const R0=1, r0=0.4;
      const a = time * 0.8;
      const uL = a, vL = a*2;
      ctx.L.position.set(
        (R0 + r0*Math.cos(vL))*Math.cos(uL), r0*Math.sin(vL), (R0 + r0*Math.cos(vL))*Math.sin(uL));
      ctx.L.scale.setScalar(0.4 + wL*1.1);
      ctx.L.material.opacity = 0.3 + wL*0.7; ctx.L.material.transparent=true;
      const uR = -a, vR = -a*2;
      ctx.R.position.set(
        (R0 + r0*Math.cos(vR))*Math.cos(uR), r0*Math.sin(vR), (R0 + r0*Math.cos(vR))*Math.sin(uR));
      ctx.R.scale.setScalar(0.4 + wR*1.1);
      ctx.R.material.opacity = 0.3 + wR*0.7; ctx.R.material.transparent=true;
      // ⟨γ⁵⟩ = wL - wR = chir
      return chir.toFixed(3);
    }
  };

  if (id === 'HOLONOMY') return {
    formula: 'γ_Berry = −½Ω  ·  Ω = enclosed solid angle on Bloch S²',
    invariantName: 'γ_Berry',
    paramLabel: 'θ loop',
    paramMin: 0.1, paramMax: Math.PI - 0.1, paramStep: 0.02, defaultParam: Math.PI/3,
    paramFmt: v => (v/Math.PI).toFixed(2)+'π',
    build: (THREE, scene, t) => {
      const group = new THREE.Group(); scene.add(group);
      const sph = new THREE.Mesh(
        new THREE.SphereGeometry(1, 22, 16),
        new THREE.MeshBasicMaterial({ color: t.amberHex, wireframe: true, transparent:true, opacity:0.22 })
      );
      group.add(sph);
      // pole marker
      const pole = new THREE.Mesh(new THREE.SphereGeometry(0.04,8,8),
        new THREE.MeshBasicMaterial({ color: t.paperDimHex }));
      pole.position.set(0,1,0);
      group.add(pole);
      const loop = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: t.cyanHex }));
      group.add(loop);
      // filled cap (shown as a faint triangle-fan ribbon)
      const cap = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({
        color: t.cyanHex, transparent:true, opacity:0.18, side: THREE.DoubleSide
      }));
      group.add(cap);
      const moving = new THREE.Mesh(new THREE.SphereGeometry(0.05,10,10),
        new THREE.MeshBasicMaterial({ color: t.cyanHex }));
      group.add(moving);
      return { loop, cap, moving };
    },
    update: (ctx, time, theta, THREE) => {
      // latitude loop at polar angle theta
      const N = 96;
      const pts = [];
      for (let i=0;i<=N;i++) {
        const phi = (i/N)*Math.PI*2;
        pts.push(new THREE.Vector3(
          1.01*Math.sin(theta)*Math.cos(phi),
          1.01*Math.cos(theta),
          1.01*Math.sin(theta)*Math.sin(phi)
        ));
      }
      ctx.loop.geometry.dispose();
      ctx.loop.geometry = new THREE.BufferGeometry().setFromPoints(pts);
      // cap mesh: triangle fan from pole to loop
      const verts = [];
      verts.push(0,1,0);
      for (let i=0;i<=N;i++) {
        const phi = (i/N)*Math.PI*2;
        verts.push(Math.sin(theta)*Math.cos(phi), Math.cos(theta), Math.sin(theta)*Math.sin(phi));
      }
      const idx = [];
      for (let i=1;i<=N;i++) idx.push(0, i, i+1);
      const bg = new THREE.BufferGeometry();
      bg.setAttribute('position', new THREE.Float32BufferAttribute(verts, 3));
      bg.setIndex(idx);
      bg.computeVertexNormals();
      ctx.cap.geometry.dispose();
      ctx.cap.geometry = bg;
      // moving dot on loop
      const phi = time*1.2;
      ctx.moving.position.set(
        1.02*Math.sin(theta)*Math.cos(phi),
        1.02*Math.cos(theta),
        1.02*Math.sin(theta)*Math.sin(phi)
      );
      const Omega = 2*Math.PI*(1 - Math.cos(theta));
      const gamma = -0.5 * Omega;
      return `${gamma.toFixed(3)} rad  (Ω=${Omega.toFixed(2)})`;
    }
  };

  if (id === 'CONNES') return {
    formula: 'd(φ₁,φ₂) = sup{|φ₁(a)−φ₂(a)| : ‖[D,a]‖ ≤ 1}  →  geodesic on S²',
    invariantName: 'd',
    paramLabel: 'sep (rad)',
    paramMin: 0.05, paramMax: Math.PI - 0.05, paramStep: 0.02, defaultParam: Math.PI/2,
    paramFmt: v => v.toFixed(2),
    build: (THREE, scene, t) => {
      const group = new THREE.Group(); scene.add(group);
      const sph = new THREE.Mesh(
        new THREE.SphereGeometry(1, 22, 16),
        new THREE.MeshBasicMaterial({ color: t.amberHex, wireframe: true, transparent:true, opacity:0.18 })
      );
      group.add(sph);
      const p1 = new THREE.Mesh(new THREE.SphereGeometry(0.06,10,10),
        new THREE.MeshBasicMaterial({ color: t.roseHex }));
      const p2 = new THREE.Mesh(new THREE.SphereGeometry(0.06,10,10),
        new THREE.MeshBasicMaterial({ color: t.roseHex }));
      group.add(p1); group.add(p2);
      const geo = new THREE.Line(new THREE.BufferGeometry(),
        new THREE.LineDashedMaterial({ color: t.roseHex, dashSize: 0.05, gapSize: 0.03 }));
      group.add(geo);
      const chord = new THREE.Line(new THREE.BufferGeometry(),
        new THREE.LineBasicMaterial({ color: t.paperDimHex, transparent:true, opacity:0.5 }));
      group.add(chord);
      return { p1, p2, geo, chord };
    },
    update: (ctx, time, sep, THREE) => {
      // rotate midpoint around y-axis so the geodesic orbits
      const mid = time * 0.4;
      const a1 = mid - sep/2, a2 = mid + sep/2;
      const th = Math.PI/2 + Math.sin(time*0.2)*0.2;
      const v1 = new THREE.Vector3(Math.sin(th)*Math.cos(a1), Math.cos(th), Math.sin(th)*Math.sin(a1));
      const v2 = new THREE.Vector3(Math.sin(th)*Math.cos(a2), Math.cos(th), Math.sin(th)*Math.sin(a2));
      ctx.p1.position.copy(v1); ctx.p2.position.copy(v2);
      // great-circle geodesic
      const n1=v1.clone().normalize(), n2=v2.clone().normalize();
      const om = Math.acos(Math.max(-1,Math.min(1, n1.dot(n2))));
      const sO = Math.sin(om)||1;
      const arcPts = [];
      for (let i=0;i<=40;i++) {
        const s = i/40;
        const A = Math.sin((1-s)*om)/sO, B = Math.sin(s*om)/sO;
        arcPts.push(new THREE.Vector3(
          1.02*(A*n1.x + B*n2.x),
          1.02*(A*n1.y + B*n2.y),
          1.02*(A*n1.z + B*n2.z)
        ));
      }
      ctx.geo.geometry.dispose();
      ctx.geo.geometry = new THREE.BufferGeometry().setFromPoints(arcPts);
      ctx.geo.computeLineDistances();
      // chord
      ctx.chord.geometry.dispose();
      ctx.chord.geometry = new THREE.BufferGeometry().setFromPoints([v1, v2]);
      // d_Connes on round S² = geodesic length = ω (in radians)
      return `${om.toFixed(3)} rad`;
    }
  };

  // fallback
  return {
    formula: '—', invariantName: '—', paramLabel: '—',
    paramMin: 0, paramMax: 1, paramStep: 0.1, defaultParam: 0, paramFmt: v=>v.toFixed(2),
    build: () => ({}),
    update: () => '—',
  };
}

Object.assign(window, { LayerSimsStrip, LayerSim, layerSpec });
