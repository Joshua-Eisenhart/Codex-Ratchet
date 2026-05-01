// ConnesSpectralTripleView — (A, H, D) on a finite discrete space of N = 4 points.
//
//   A = diagonal 4×4 real matrices  (functions on {1, 2, 3, 4})
//   H = C^4
//   D = 4×4 Hermitian matrix with zero diagonal (user-controlled off-diagonals)
//
// Commutator [D, a] for diagonal a has entries M_ij = D_ij (a_j − a_i).
// Operator-norm constraint ||[D, a]|| ≤ 1 is stronger than the pointwise
// bound |a_j − a_i| ≤ 1 / |D_ij|. Under the pointwise bound, Connes distance
//     d(i, j) = sup { a_j − a_i : |a_k − a_l| ≤ 1 / |D_kl| ∀ k, l }
// reduces to the shortest-path on the complete graph K_4 with edge weights
// w_kl = 1 / |D_kl|. That's the Connes distance we display — labelled
// "geodesic bound" since it's an upper bound on the operator-norm-exact one.
//
// We also compute the true operator norm ||[D, a]|| for the geodesic-saturating
// a via power iteration on M†M, so the user sees the actual norm sitting
// below 1.

const N_POINTS = 4;
const POINT_POS = [  // 4 points on a unit-ish square/diamond
  [ 1.0,  0.0], [0.0,  1.0],
  [-1.0,  0.0], [0.0, -1.0],
];

// Hermitian matrix = N×N real (we constrain to real symmetric for this view).
// Build from 6 upper-triangular off-diagonals.
function buildD(off) {
  const M = Array.from({length: N_POINTS}, () => new Array(N_POINTS).fill(0));
  let k = 0;
  for (let i = 0; i < N_POINTS; i++) {
    for (let j = i + 1; j < N_POINTS; j++) {
      M[i][j] = off[k]; M[j][i] = off[k]; k++;
    }
  }
  return M;
}

// Dijkstra shortest path on complete graph with weights w_ij = 1 / |D_ij|.
function connesDistMatrix(D) {
  const W = Array.from({length: N_POINTS}, () => new Array(N_POINTS).fill(Infinity));
  for (let i = 0; i < N_POINTS; i++) {
    W[i][i] = 0;
    for (let j = 0; j < N_POINTS; j++) {
      if (i === j) continue;
      W[i][j] = Math.abs(D[i][j]) > 1e-9 ? 1 / Math.abs(D[i][j]) : Infinity;
    }
  }
  // Floyd–Warshall
  const d = W.map(r => r.slice());
  for (let k = 0; k < N_POINTS; k++)
    for (let i = 0; i < N_POINTS; i++)
      for (let j = 0; j < N_POINTS; j++)
        if (d[i][k] + d[k][j] < d[i][j]) d[i][j] = d[i][k] + d[k][j];
  return d;
}

// Predecessor matrix for shortest paths from source s.
function shortestPathFrom(D, s) {
  const W = [];
  for (let i = 0; i < N_POINTS; i++) {
    W.push([]);
    for (let j = 0; j < N_POINTS; j++) {
      W[i].push(i === j ? 0 : (Math.abs(D[i][j]) > 1e-9 ? 1 / Math.abs(D[i][j]) : Infinity));
    }
  }
  const dist = new Array(N_POINTS).fill(Infinity);
  const prev = new Array(N_POINTS).fill(-1);
  const visited = new Array(N_POINTS).fill(false);
  dist[s] = 0;
  for (let step = 0; step < N_POINTS; step++) {
    let u = -1, min = Infinity;
    for (let i = 0; i < N_POINTS; i++) if (!visited[i] && dist[i] < min) { min = dist[i]; u = i; }
    if (u < 0) break;
    visited[u] = true;
    for (let v = 0; v < N_POINTS; v++) {
      if (visited[v]) continue;
      const alt = dist[u] + W[u][v];
      if (alt < dist[v]) { dist[v] = alt; prev[v] = u; }
    }
  }
  return { dist, prev };
}

// Construct a that saturates d(s, t) via geodesic: a_k = dist(s, k) if on
// the shortest path tree of s, else 0 — and translate so a_s = 0, a_t = d(s,t).
// (Simplest realization: a_k = -dist(s, k) so a_s = 0, a_t = -d. We flip sign.)
function saturatingA(D, s, t) {
  const { dist } = shortestPathFrom(D, s);
  // choose a = dist (so a_t - a_s = d(s,t) is the geodesic distance)
  const a = dist.slice();
  return a;
}

// [D, a] entries: M_ij = D_ij (a_j − a_i)
function commutator(D, a) {
  const M = Array.from({length: N_POINTS}, () => new Array(N_POINTS).fill(0));
  for (let i = 0; i < N_POINTS; i++)
    for (let j = 0; j < N_POINTS; j++)
      M[i][j] = D[i][j] * (a[j] - a[i]);
  return M;
}

// Operator norm via power iteration on M^T M
function operatorNorm(M, iters = 60) {
  const n = M.length;
  let v = new Array(n).fill(0).map(() => Math.random());
  for (let it = 0; it < iters; it++) {
    // w = M v
    const w = new Array(n).fill(0);
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) w[i] += M[i][j] * v[j];
    // u = M^T w
    const u = new Array(n).fill(0);
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) u[i] += M[j][i] * w[j];
    let nrm = 0; for (let i = 0; i < n; i++) nrm += u[i] * u[i];
    nrm = Math.sqrt(nrm);
    if (nrm < 1e-14) return 0;
    for (let i = 0; i < n; i++) v[i] = u[i] / nrm;
  }
  // Rayleigh: ||M v|| where v is approx top right-singular vec
  const w = new Array(n).fill(0);
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) w[i] += M[i][j] * v[j];
  let nrm = 0; for (let i = 0; i < n; i++) nrm += w[i] * w[i];
  return Math.sqrt(nrm);
}

function ConnesSpectralTripleView({ t }) {
  const [off, setOff] = React.useState([1.2, 0.9, 0.6, 1.0, 0.7, 1.1]);  // 6 off-diagonals
  const [src, setSrc] = React.useState(0);
  const [dst, setDst] = React.useState(2);

  const D = React.useMemo(() => buildD(off), [off]);
  const distMat = React.useMemo(() => connesDistMatrix(D), [D]);
  const { prev } = React.useMemo(() => shortestPathFrom(D, src), [D, src]);
  const a = React.useMemo(() => saturatingA(D, src, dst), [D, src, dst]);
  const aNorm = React.useMemo(() => {
    // rescale so ||[D, a]|| = 1 exactly
    const rawM = commutator(D, a);
    const n = operatorNorm(rawM);
    if (n < 1e-12) return a;
    return a.map(x => x / n);
  }, [D, a]);
  const Mcomm = React.useMemo(() => commutator(D, aNorm), [D, aNorm]);
  const opNorm = React.useMemo(() => operatorNorm(Mcomm), [Mcomm]);

  const connesD_st = distMat[src][dst];
  // realized distance = |a_t - a_s| after rescale
  const realized = Math.abs(aNorm[dst] - aNorm[src]);

  // reconstruct path src → dst
  const path = [];
  { let x = dst;
    while (x !== -1) { path.unshift(x); if (x === src) break; x = prev[x]; }
  }

  // SVG canvas for graph
  const W = 420, H = 340, pad = 40;
  const xScale = (x) => W/2 + x * (W/2 - pad);
  const yScale = (y) => H/2 - y * (H/2 - pad);

  const labels = ['①', '②', '③', '④'];
  const idxLabel = ['(1,2)','(1,3)','(1,4)','(2,3)','(2,4)','(3,4)'];
  const idxPair  = [[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]];

  const onPointClick = (i) => {
    if (i === src) return;
    if (i === dst) setDst(src);
    setSrc(i);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      <div style={{ padding: '8px 16px', borderBottom: `1px solid ${t.line}`, display: 'flex', gap: 14, alignItems: 'center' }}>
        <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>SPECTRAL TRIPLE · (A, H, D) · FINITE DISCRETE N = 4</Mono>
        <div style={{ flex: 1 }}/>
        <Mono t={t} size={10} dim>d(φ, ψ) = sup&#123; |φ(a) − ψ(a)| : ||[D, a]|| ≤ 1 &#125;</Mono>
      </div>

      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 420px', minHeight: 0, overflow: 'hidden' }}>
        {/* LEFT: triple definition + graph + distance matrix */}
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 14, minHeight: 0, overflow: 'auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
            <div style={{ border: `1px solid ${t.line}`, background: t.bg2, padding: 10 }}>
              <Mono t={t} size={10} dim>A · algebra</Mono>
              <Mono t={t} size={12} style={{ display: 'block', marginTop: 4, color: t.amberHex }}>C(X) ≅ ℝ⁴</Mono>
              <Mono t={t} size={9} dim style={{ display:'block', marginTop: 4, lineHeight: 1.5 }}>
                diagonal 4×4 real matrices; a = diag(a₁, a₂, a₃, a₄). Dense in continuous functions on the 4-point space.
              </Mono>
            </div>
            <div style={{ border: `1px solid ${t.line}`, background: t.bg2, padding: 10 }}>
              <Mono t={t} size={10} dim>H · Hilbert space</Mono>
              <Mono t={t} size={12} style={{ display: 'block', marginTop: 4, color: t.cyanHex }}>ℂ⁴</Mono>
              <Mono t={t} size={9} dim style={{ display:'block', marginTop: 4, lineHeight: 1.5 }}>
                the L² space of X. A acts on H by pointwise multiplication: (a·ψ)_i = a_i ψ_i.
              </Mono>
            </div>
            <div style={{ border: `1px solid ${t.line}`, background: t.bg2, padding: 10 }}>
              <Mono t={t} size={10} dim>D · Dirac operator</Mono>
              <Mono t={t} size={12} style={{ display: 'block', marginTop: 4, color: t.violetHex }}>4×4 Hermitian, zero diagonal</Mono>
              <Mono t={t} size={9} dim style={{ display:'block', marginTop: 4, lineHeight: 1.5 }}>
                self-adjoint; [D, a] bounded ⟹ axiom of spectral triple satisfied (finite dim, automatic).
              </Mono>
            </div>
          </div>

          {/* D matrix + sliders */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <div>
              <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>D · OFF-DIAGONALS</Mono>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 0, border: `1px solid ${t.line}`, marginTop: 6 }}>
                {D.map((row, i) => row.map((val, j) => (
                  <div key={`${i}-${j}`} style={{
                    padding: '5px 6px', textAlign: 'right',
                    borderRight: j < 3 ? `1px solid ${t.line}` : 'none',
                    borderBottom: i < 3 ? `1px solid ${t.line}` : 'none',
                    background: i === j ? t.bg : (Math.abs(val) > 0.001 ? t.bg2 : t.bg),
                    fontFamily: 'JetBrains Mono, monospace', fontSize: 10,
                    color: i === j ? t.paperFaintHex : (Math.abs(val) > 0.001 ? t.paper : t.paperFaintHex),
                  }}>
                    {val.toFixed(2)}
                  </div>
                )))}
              </div>
            </div>
            <div>
              <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>EDIT · |D_ij|</Mono>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 6 }}>
                {idxLabel.map((lbl, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Mono t={t} size={9} dim style={{ width: 40 }}>{lbl}</Mono>
                    <input type="range" min="0" max="2.5" step="0.01" value={off[i]}
                      onChange={e => setOff(o => { const n = o.slice(); n[i] = parseFloat(e.target.value); return n; })}
                      style={{ flex: 1 }}/>
                    <Mono t={t} size={10}>{off[i].toFixed(2)}</Mono>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Graph + geodesic */}
          <div>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>
              DISCRETE SPACE X · EDGES WEIGHTED BY 1/|D_ij| · SHORTEST PATH = CONNES DISTANCE
            </Mono>
            <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', maxWidth: 560, display: 'block', background: t.bgHex, border: `1px solid ${t.line}`, marginTop: 6 }}>
              {/* edges — thickness ∝ |D_ij| */}
              {idxPair.map((pair, k) => {
                const [i, j] = pair;
                const mag = Math.abs(off[k]);
                const [x1, y1] = POINT_POS[i]; const [x2, y2] = POINT_POS[j];
                const onPath = path.some((n, idx) => idx < path.length - 1 && ((path[idx] === i && path[idx+1] === j) || (path[idx] === j && path[idx+1] === i)));
                return (
                  <g key={k}>
                    <line x1={xScale(x1)} y1={yScale(y1)} x2={xScale(x2)} y2={yScale(y2)}
                      stroke={onPath ? t.amberHex : t.lineHex}
                      strokeWidth={onPath ? 3 : Math.max(0.5, mag * 1.2)}
                      opacity={onPath ? 1 : 0.6}/>
                    <text x={(xScale(x1) + xScale(x2))/2 + 4} y={(yScale(y1) + yScale(y2))/2 - 4}
                      fill={onPath ? t.amberHex : t.paperDimHex}
                      fontFamily="JetBrains Mono" fontSize="9">
                      {mag > 0.01 ? (1/mag).toFixed(2) : '∞'}
                    </text>
                  </g>
                );
              })}
              {/* nodes */}
              {POINT_POS.map((p, i) => {
                const isSrc = i === src, isDst = i === dst;
                return (
                  <g key={i} onClick={() => onPointClick(i)} style={{ cursor: 'pointer' }}>
                    <circle cx={xScale(p[0])} cy={yScale(p[1])} r="14"
                      fill={isSrc ? t.cyanHex : isDst ? t.violetHex : t.bg2}
                      stroke={isSrc || isDst ? t.paperHex : t.paperDimHex} strokeWidth="1.5"/>
                    <text x={xScale(p[0])} y={yScale(p[1]) + 5}
                      fill={isSrc || isDst ? t.bgHex : t.paperHex}
                      textAnchor="middle" fontFamily="JetBrains Mono" fontSize="14">
                      {labels[i]}
                    </text>
                  </g>
                );
              })}
              <text x={W - 10} y={16} fill={t.cyanHex} textAnchor="end" fontFamily="JetBrains Mono" fontSize="10">source (click another)</text>
              <text x={W - 10} y={30} fill={t.violetHex} textAnchor="end" fontFamily="JetBrains Mono" fontSize="10">sink</text>
            </svg>
            <div style={{ display: 'flex', gap: 8, marginTop: 8, alignItems: 'center' }}>
              <Mono t={t} size={10} dim>sink =</Mono>
              {labels.map((l, i) => (
                <button key={i} onClick={() => setDst(i)} style={btn(t, dst === i)}>{l}</button>
              ))}
              <div style={{ flex: 1 }}/>
              <Mono t={t} size={10} dim>d({labels[src]}, {labels[dst]}) =</Mono>
              <Mono t={t} size={14} style={{ color: t.amberHex }}><b>{connesD_st.toFixed(3)}</b></Mono>
            </div>
          </div>

          {/* distance matrix */}
          <div>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>CONNES DISTANCE MATRIX · d(i, j)</Mono>
            <div style={{ display: 'grid', gridTemplateColumns: '28px repeat(4, 1fr)', gap: 0, border: `1px solid ${t.line}`, marginTop: 6 }}>
              <div style={{ background: t.bg2 }}/>
              {labels.map((l, j) => (
                <div key={j} style={{ background: t.bg2, padding: 6, textAlign: 'center', borderLeft: `1px solid ${t.line}` }}>
                  <Mono t={t} size={10} dim>{l}</Mono>
                </div>
              ))}
              {labels.map((li, i) => (
                <React.Fragment key={i}>
                  <div style={{ background: t.bg2, padding: 6, textAlign: 'center', borderTop: `1px solid ${t.line}` }}>
                    <Mono t={t} size={10} dim>{li}</Mono>
                  </div>
                  {labels.map((lj, j) => {
                    const isSel = (i === src && j === dst) || (i === dst && j === src);
                    return (
                      <div key={j} style={{
                        padding: 6, textAlign: 'center',
                        borderTop: `1px solid ${t.line}`,
                        borderLeft: `1px solid ${t.line}`,
                        background: i === j ? t.bg : isSel ? t.amber + '33' : t.bg,
                        color: i === j ? t.paperFaintHex : isSel ? t.amberHex : t.paper,
                        fontFamily: 'JetBrains Mono, monospace', fontSize: 10,
                      }}>
                        {distMat[i][j] === Infinity ? '∞' : distMat[i][j].toFixed(3)}
                      </div>
                    );
                  })}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT: saturating a, [D,a], operator norm */}
        <div style={{ borderLeft: `1px solid ${t.line}`, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'auto' }}>
          <div style={{ padding: '8px 12px', borderBottom: `1px solid ${t.line}` }}>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>
              SATURATING a · [D, a] · ||[D, a]||_op
            </Mono>
          </div>
          <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <Mono t={t} size={10} dim>a = diag(a₁, a₂, a₃, a₄)</Mono>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 4, marginTop: 6 }}>
                {aNorm.map((v, i) => (
                  <div key={i} style={{ padding: 6, textAlign: 'center', border: `1px solid ${t.line}`, background: i === src ? t.cyan + '22' : i === dst ? t.violet + '22' : t.bg2 }}>
                    <Mono t={t} size={9} dim>a{['₁','₂','₃','₄'][i]}</Mono>
                    <div style={{ height: 4 }}/>
                    <Mono t={t} size={11}>{v.toFixed(3)}</Mono>
                  </div>
                ))}
              </div>
              <Mono t={t} size={9} dim style={{ display: 'block', marginTop: 6, lineHeight: 1.5 }}>
                built from geodesic: a_k = dist(src, k), then rescaled so ||[D, a]||_op = 1 exactly.
                φ_i(a) = a_i, so the measured distance is |a_{dst} − a_{src}|.
              </Mono>
            </div>

            <div>
              <Mono t={t} size={10} dim>[D, a] · 4×4 matrix</Mono>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 0, border: `1px solid ${t.line}`, marginTop: 6 }}>
                {Mcomm.map((row, i) => row.map((val, j) => (
                  <div key={`${i}-${j}`} style={{
                    padding: '5px 6px', textAlign: 'right',
                    borderRight: j < 3 ? `1px solid ${t.line}` : 'none',
                    borderBottom: i < 3 ? `1px solid ${t.line}` : 'none',
                    background: Math.abs(val) > 0.001 ? t.bg2 : t.bg,
                    fontFamily: 'JetBrains Mono, monospace', fontSize: 9,
                    color: Math.abs(val) > 0.001 ? t.paper : t.paperFaintHex,
                  }}>
                    {val.toFixed(2)}
                  </div>
                )))}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', rowGap: 4, columnGap: 8 }}>
              <Mono t={t} size={10} dim>||[D, a]||_op</Mono>
              <Mono t={t} size={10} style={{color: t.amberHex}}><b>{opNorm.toFixed(4)}</b></Mono>
              <Mono t={t} size={10} dim>realized |a_t − a_s|</Mono>
              <Mono t={t} size={10} style={{color: t.amberHex}}>{realized.toFixed(4)}</Mono>
              <Mono t={t} size={10} dim>geodesic bound</Mono>
              <Mono t={t} size={10}>{connesD_st.toFixed(4)}</Mono>
              <Mono t={t} size={10} dim>match</Mono>
              <Mono t={t} size={10} style={{color: Math.abs(realized - connesD_st) < 1e-2 ? t.amberHex : t.roseHex}}>
                {Math.abs(realized - connesD_st) < 1e-2 ? 'tight ✓' : `gap = ${(connesD_st - realized).toFixed(3)}`}
              </Mono>
            </div>

            <div style={{ borderTop: `1px solid ${t.line}`, paddingTop: 10 }}>
              <Mono t={t} size={9} dim style={{ lineHeight: 1.5 }}>
                <b>What's happening:</b> for diagonal A, [D, a]_ij = D_ij (a_j − a_i). The operator-norm constraint is stronger than the pointwise bound |a_j − a_i| ≤ 1/|D_ij|, so the shortest-path construction is an upper bound on Connes distance. When D is far from rank-1, the geodesic a saturates the op-norm unit ball up to a small factor, so realized ≈ geodesic bound.
                <br/><br/>
                <b>Doctrine hook:</b> this is one of the axes where the nominalist system <i>earns</i> its metric — not from coordinates, but from a Dirac operator that encodes distinguishability constraints on H. The graph is not a picture; it is literally what (A, H, D) says about X.
              </Mono>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { ConnesSpectralTripleView });
