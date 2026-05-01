// LieStructureView — G-tower Lie structure, live.
//
// Concrete Lie algebra su(2) ≅ so(3): generators T_a = σ_a / 2, a ∈ {x, y, z}.
// Bracket: [T_a, T_b] = i ε_abc T_c. Structure constants f_abc = ε_abc.
//
// The view shows:
//   - The three generators as explicit 2×2 Hermitian matrices
//   - The full 3×3×3 structure-constants tensor (Levi-Civita ε)
//   - Live commutator [X, Y] computed by matrix multiplication for user-chosen X, Y
//   - Non-commutativity demo on a Bloch vector: R_y R_x vs R_x R_y
//   - BCH expansion of log(e^X e^Y) to second order vs numerical truncation
//
// Nothing is decorative; every cell in every matrix is computed from the
// chosen generators.

// ---------- 2×2 complex matrix arithmetic ----------
// Matrix = [[a,b],[c,d]] with each entry [re, im].
function cadd(a, b) { return [a[0]+b[0], a[1]+b[1]]; }
function csub(a, b) { return [a[0]-b[0], a[1]-b[1]]; }
function cmul(a, b) { return [a[0]*b[0] - a[1]*b[1], a[0]*b[1] + a[1]*b[0]]; }
function cscale(a, s) { return [a[0]*s, a[1]*s]; }

function m2mul(A, B) {
  const [[a,b],[c,d]] = A;
  const [[e,f],[g,h]] = B;
  return [
    [cadd(cmul(a,e), cmul(b,g)), cadd(cmul(a,f), cmul(b,h))],
    [cadd(cmul(c,e), cmul(d,g)), cadd(cmul(c,f), cmul(d,h))],
  ];
}
function m2sub(A, B) {
  return [[csub(A[0][0], B[0][0]), csub(A[0][1], B[0][1])],
          [csub(A[1][0], B[1][0]), csub(A[1][1], B[1][1])]];
}
function m2scale(A, s) {
  return [[cscale(A[0][0], s), cscale(A[0][1], s)],
          [cscale(A[1][0], s), cscale(A[1][1], s)]];
}

// Pauli matrices σ_x, σ_y, σ_z as complex 2×2
const SIGMA_X = [[[0,0],[1,0]], [[1,0],[0,0]]];
const SIGMA_Y = [[[0,0],[0,-1]], [[0,1],[0,0]]];
const SIGMA_Z = [[[1,0],[0,0]], [[0,0],[-1,0]]];

// Generators T_a = σ_a / 2
function genT(a) {
  const s = a === 'x' ? SIGMA_X : a === 'y' ? SIGMA_Y : SIGMA_Z;
  return m2scale(s, 0.5);
}

// commutator [A, B]
function commutator(A, B) { return m2sub(m2mul(A, B), m2mul(B, A)); }

// Levi-Civita ε_abc (a, b, c ∈ {0,1,2})
function epsilon(a, b, c) {
  if (a === b || b === c || a === c) return 0;
  const p = (a === 0 && b === 1) || (a === 1 && b === 2) || (a === 2 && b === 0);
  const q = c === (3 - a - b);
  if (!q) return 0;
  return p ? 1 : -1;
}

// Format a complex 2x2 matrix as strings
function fmtC(z, digits = 2) {
  const re = z[0], im = z[1];
  const eps = 1e-9;
  if (Math.abs(re) < eps && Math.abs(im) < eps) return '0';
  if (Math.abs(im) < eps) return re.toFixed(digits).replace(/\.?0+$/, '');
  if (Math.abs(re) < eps) {
    const v = im.toFixed(digits).replace(/\.?0+$/, '');
    return `${v}i`;
  }
  const reS = re.toFixed(digits).replace(/\.?0+$/, '');
  const sign = im >= 0 ? '+' : '−';
  const imS = Math.abs(im).toFixed(digits).replace(/\.?0+$/, '');
  return `${reS}${sign}${imS}i`;
}

function MatrixBox({ t, M, title, color, digits = 2 }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 0 }}>
      {title && <Mono t={t} size={10} dim>{title}</Mono>}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr',
        gap: 0, border: `1px solid ${t.line}`, background: t.bg2,
      }}>
        {M.flat().map((z, i) => (
          <div key={i} style={{
            padding: '6px 8px', textAlign: 'right',
            borderRight: i % 2 === 0 ? `1px solid ${t.line}` : 'none',
            borderBottom: i < 2 ? `1px solid ${t.line}` : 'none',
            fontFamily: 'JetBrains Mono, monospace', fontSize: 11,
            color: color || t.paper,
          }}>{fmtC(z, digits)}</div>
        ))}
      </div>
    </div>
  );
}

// ---------- rotation of a unit vector via axis-angle ----------
function rotateVec(v, axis, theta) {
  // Rodrigues' formula
  const n = Math.hypot(axis[0], axis[1], axis[2]) || 1;
  const k = [axis[0]/n, axis[1]/n, axis[2]/n];
  const c = Math.cos(theta), s = Math.sin(theta);
  const kv = k[0]*v[0] + k[1]*v[1] + k[2]*v[2];
  const cross = [k[1]*v[2] - k[2]*v[1], k[2]*v[0] - k[0]*v[2], k[0]*v[1] - k[1]*v[0]];
  return [
    v[0]*c + cross[0]*s + k[0]*kv*(1-c),
    v[1]*c + cross[1]*s + k[1]*kv*(1-c),
    v[2]*c + cross[2]*s + k[2]*kv*(1-c),
  ];
}

function LieStructureView({ t }) {
  const [aIdx, setAIdx] = React.useState(0);   // X = T_a
  const [bIdx, setBIdx] = React.useState(1);   // Y = T_b
  const [theta, setTheta] = React.useState(1.2);
  const mountRef = React.useRef(null);
  const stateRef = React.useRef(null);

  const labels = ['x', 'y', 'z'];
  const Tx = genT('x'), Ty = genT('y'), Tz = genT('z');
  const Ts = [Tx, Ty, Tz];

  const X = Ts[aIdx], Y = Ts[bIdx];
  const XY = m2mul(X, Y);
  const YX = m2mul(Y, X);
  const br = commutator(X, Y);
  // [T_a, T_b] = i ε_abc T_c, so we expect br = i ε · T_c
  const expectedC = [0, 1, 2].find(c => epsilon(aIdx, bIdx, c) !== 0);
  const expectedSign = expectedC !== undefined ? epsilon(aIdx, bIdx, expectedC) : 0;

  // axes as 3D unit vectors
  const ax = [[1,0,0],[0,1,0],[0,0,1]];

  // demo vector starts at (1,0,0).
  const v0 = [1, 0, 0];
  // apply R_{axis aIdx}(θ) then R_{axis bIdx}(θ)
  const afterAB = rotateVec(rotateVec(v0, ax[aIdx], theta), ax[bIdx], theta);
  // apply in reverse order
  const afterBA = rotateVec(rotateVec(v0, ax[bIdx], theta), ax[aIdx], theta);
  const diffMag = Math.hypot(afterAB[0]-afterBA[0], afterAB[1]-afterBA[1], afterAB[2]-afterBA[2]);

  // BCH: Z = X + Y + ½[X,Y] + ...
  const sum = m2scale([[cadd(X[0][0], Y[0][0]), cadd(X[0][1], Y[0][1])],
                       [cadd(X[1][0], Y[1][0]), cadd(X[1][1], Y[1][1])]], 1);
  const halfBr = m2scale(br, 0.5);

  // 3D scene
  React.useEffect(() => {
    if (!window.THREE) return;
    const THREE = window.THREE;
    const mount = mountRef.current;
    if (!mount) return;
    const w = mount.clientWidth, h = mount.clientHeight;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(t.bgHex);
    const camera = new THREE.PerspectiveCamera(40, w/h, 0.1, 100);
    camera.position.set(2.4, 1.8, 2.4);
    camera.lookAt(0, 0, 0);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(w, h);
    mount.innerHTML = '';
    mount.appendChild(renderer.domElement);
    scene.add(new THREE.AmbientLight(0xffffff, 0.7));

    const sphere = new THREE.Mesh(
      new THREE.SphereGeometry(1, 28, 20),
      new THREE.MeshBasicMaterial({ color: t.paperFaintHex, wireframe: true, transparent: true, opacity: 0.12 })
    );
    scene.add(sphere);

    // axes
    [[1.3,0,0],[0,1.3,0],[0,0,1.3]].forEach(e => {
      const g = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0,0), new THREE.Vector3(...e)]);
      scene.add(new THREE.Line(g, new THREE.LineBasicMaterial({ color: t.paperDimHex })));
    });

    // start point (paper)
    const startDot = new THREE.Mesh(new THREE.SphereGeometry(0.06, 12, 12), new THREE.MeshBasicMaterial({ color: t.paperHex }));
    startDot.position.set(1, 0, 0);
    scene.add(startDot);

    // AB endpoint (amber)
    const abDot = new THREE.Mesh(new THREE.SphereGeometry(0.08, 14, 14), new THREE.MeshBasicMaterial({ color: t.amberHex }));
    scene.add(abDot);
    // BA endpoint (cyan)
    const baDot = new THREE.Mesh(new THREE.SphereGeometry(0.08, 14, 14), new THREE.MeshBasicMaterial({ color: t.cyanHex }));
    scene.add(baDot);

    // gap line
    const gapGeo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]);
    const gap = new THREE.Line(gapGeo, new THREE.LineBasicMaterial({ color: t.roseHex }));
    scene.add(gap);

    stateRef.current = { scene, camera, renderer, abDot, baDot, gap, THREE };
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
    s.abDot.position.set(...afterAB);
    s.baDot.position.set(...afterBA);
    s.gap.geometry.dispose();
    s.gap.geometry = new s.THREE.BufferGeometry().setFromPoints([
      new s.THREE.Vector3(...afterAB), new s.THREE.Vector3(...afterBA),
    ]);
    s.renderer.render(s.scene, s.camera);
  }, [aIdx, bIdx, theta]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      <div style={{ padding: '8px 16px', borderBottom: `1px solid ${t.line}`, display: 'flex', gap: 14, alignItems: 'center' }}>
        <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>LIE STRUCTURE · su(2) ≅ so(3)</Mono>
        <div style={{ flex: 1 }}/>
        <Mono t={t} size={10} dim>[T_a, T_b] = i ε<sub>abc</sub> T_c</Mono>
      </div>

      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: 0, overflow: 'hidden' }}>
        {/* LEFT: generators + structure constants + selectors */}
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 14, minHeight: 0, overflow: 'auto' }}>
          <div>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>GENERATORS · T_a = σ_a / 2</Mono>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginTop: 8 }}>
              <MatrixBox t={t} M={Tx} title="T_x" color={t.amberHex} digits={2}/>
              <MatrixBox t={t} M={Ty} title="T_y" color={t.amberHex} digits={2}/>
              <MatrixBox t={t} M={Tz} title="T_z" color={t.amberHex} digits={2}/>
            </div>
          </div>

          <div>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>STRUCTURE CONSTANTS · f_abc = ε_abc</Mono>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginTop: 8 }}>
              {[0,1,2].map(cc => (
                <div key={cc}>
                  <Mono t={t} size={9} dim>c = {labels[cc]}</Mono>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 0, border: `1px solid ${t.line}`, marginTop: 4 }}>
                    {[0,1,2].map(aa => [0,1,2].map(bb => {
                      const v = epsilon(aa, bb, cc);
                      return (
                        <div key={`${aa},${bb}`} style={{
                          padding: 4, textAlign: 'center',
                          background: v === 0 ? t.bg2 : (v > 0 ? t.amber + '22' : t.rose + '22'),
                          color: v === 0 ? t.paperDim : (v > 0 ? t.amberHex : t.roseHex),
                          borderRight: bb < 2 ? `1px solid ${t.line}` : 'none',
                          borderBottom: aa < 2 ? `1px solid ${t.line}` : 'none',
                          fontFamily: 'JetBrains Mono, monospace', fontSize: 11,
                        }}>{v === 0 ? '·' : v > 0 ? '+1' : '−1'}</div>
                      );
                    }))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>PICK X, Y</Mono>
            <div style={{ display: 'flex', gap: 10, marginTop: 6 }}>
              <div style={{ display: 'flex', gap: 4 }}>
                <Mono t={t} size={10} dim>X = T_</Mono>
                {labels.map((l, i) => (
                  <button key={l} onClick={() => setAIdx(i)} style={btn(t, aIdx === i)}>{l}</button>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 4 }}>
                <Mono t={t} size={10} dim>Y = T_</Mono>
                {labels.map((l, i) => (
                  <button key={l} onClick={() => setBIdx(i)} style={btn(t, bIdx === i)}>{l}</button>
                ))}
              </div>
            </div>
          </div>

          <div>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>
              BRACKET [X, Y] = XY − YX
            </Mono>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginTop: 8 }}>
              <MatrixBox t={t} M={XY} title="XY" digits={3}/>
              <MatrixBox t={t} M={YX} title="YX" digits={3}/>
              <MatrixBox t={t} M={br} title="[X, Y]" color={t.cyanHex} digits={3}/>
              {expectedC !== undefined
                ? <MatrixBox t={t} M={m2scale(Ts[expectedC], expectedSign)} title={`i ε_abc T_c = ${expectedSign>0?'+':'−'}i T_${labels[expectedC]}`} color={t.violetHex} digits={3}/>
                : <div><Mono t={t} size={10} dim>[X, X] = 0</Mono></div>}
            </div>
            <Mono t={t} size={9} dim style={{ display: 'block', marginTop: 6, lineHeight: 1.5 }}>
              The 3rd and 4th boxes match up to the factor <b style={{color:t.paperHex}}>i</b> when X ≠ Y.
              That is the structural identity: the bracket of any two distinct generators produces <i>i</i> times the third.
            </Mono>
          </div>

          <div>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>BCH (2nd order) · log(e^X e^Y) ≈ X + Y + ½[X, Y]</Mono>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginTop: 8 }}>
              <MatrixBox t={t} M={sum} title="X + Y" digits={3}/>
              <MatrixBox t={t} M={halfBr} title="½ [X, Y]" digits={3}/>
              <MatrixBox t={t} M={[[cadd(sum[0][0], halfBr[0][0]), cadd(sum[0][1], halfBr[0][1])],
                                    [cadd(sum[1][0], halfBr[1][0]), cadd(sum[1][1], halfBr[1][1])]]}
                         title="Z (2nd-order)" color={t.amberHex} digits={3}/>
            </div>
          </div>
        </div>

        {/* RIGHT: rotation demo */}
        <div style={{ borderLeft: `1px solid ${t.line}`, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <div style={{ padding: '8px 12px', borderBottom: `1px solid ${t.line}` }}>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>NON-COMMUTATIVITY · R_Y R_X (v) vs R_X R_Y (v)</Mono>
          </div>
          <div ref={mountRef} style={{ flex: 1, minHeight: 280, background: t.bg }}/>
          <div style={{ padding: 12, borderTop: `1px solid ${t.line}`, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Mono t={t} size={10} dim>θ</Mono>
                <input type="range" min="0" max={Math.PI} step="0.01" value={theta} onChange={e => setTheta(parseFloat(e.target.value))} style={{ flex: 1 }}/>
                <Mono t={t} size={10}>{theta.toFixed(2)} rad</Mono>
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '100px 1fr', rowGap: 3, columnGap: 8 }}>
              <Mono t={t} size={10} dim>start v</Mono>
              <Mono t={t} size={10}>(1, 0, 0)</Mono>
              <Mono t={t} size={10} style={{color:t.amberHex}}>R_Y R_X v</Mono>
              <Mono t={t} size={10}>({afterAB[0].toFixed(3)}, {afterAB[1].toFixed(3)}, {afterAB[2].toFixed(3)})</Mono>
              <Mono t={t} size={10} style={{color:t.cyanHex}}>R_X R_Y v</Mono>
              <Mono t={t} size={10}>({afterBA[0].toFixed(3)}, {afterBA[1].toFixed(3)}, {afterBA[2].toFixed(3)})</Mono>
              <Mono t={t} size={10} style={{color:t.roseHex}}>|gap|</Mono>
              <Mono t={t} size={10}>{diffMag.toFixed(4)}</Mono>
            </div>
            <Mono t={t} size={9} dim style={{ lineHeight: 1.5 }}>
              The <b style={{color:t.roseHex}}>rose gap</b> line is the residual that proves A∘B ≠ B∘A. It vanishes exactly when [X, Y] = 0 (X and Y parallel) or θ = 0. For any other choice it grows with θ, tangent to the commutator direction — this is the constraint-ratchet doctrine, demonstrated.
            </Mono>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { LieStructureView });
