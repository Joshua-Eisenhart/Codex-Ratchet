/* Engine v6 Lab — dynamics-first visualizer for TrainableEngineV6.
   Data: engine-v6-trajectory-data.js (computed by canonical engine module)
         engine-v6-witness-data.js (mirrored verbatim from canonical results JSON)
   Design contract: visualizer/DESIGN.md. Motion only between exported substage
   samples; no value here implies a proof result or basin promotion. */

const { useState, useEffect, useRef, useMemo } = React;

const C = {
  bg: "#0b0d10", panel: "#11141a", panel2: "#0e1116", border: "#262b33",
  text: "#c7cdd6", dim: "#6b7280", amber: "#f59e0b", cyan: "#22d3ee",
  rose: "#f43f5e", grid: "#1a1f27",
};
const MONO = "'JetBrains Mono', monospace";
const TERRAIN_COLORS = { funnel: "#8a6d1f", vortex: "#1f6d8a", ladder: "#5d5d72", strata: "#6d3a4a" };

const T = window.ENGINE_V6_TRAJECTORY;
const W = window.ENGINE_V6_WITNESS;
const NF = T.engines.L.frames.length; // 32
const NQ = T.meta.n_qubits;

const fmt = (x, d = 3) => (x == null ? "—" : Number(x).toFixed(d));

function Panel({ title, right, children, style }) {
  return (
    <div style={{ background: C.panel, border: `1px solid ${C.border}`, display: "flex", flexDirection: "column", minWidth: 0, ...style }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "5px 8px", borderBottom: `1px solid ${C.border}` }}>
        <span style={{ fontFamily: MONO, fontSize: 10, letterSpacing: "0.08em", color: C.dim }}>{title}</span>
        {right}
      </div>
      <div style={{ flex: 1, minHeight: 0, padding: 8 }}>{children}</div>
    </div>
  );
}

function Chip({ color, children }) {
  return <span style={{ fontFamily: MONO, fontSize: 9, color, border: `1px solid ${color}`, padding: "1px 5px", marginLeft: 6 }}>{children}</span>;
}

/* ---------- transport: 4x8 terrain/substage grid + play controls ---------- */
function Transport({ frame, setFrame, playing, setPlaying, speed, setSpeed }) {
  const frames = T.engines.L.frames;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <button onClick={() => setPlaying(!playing)}
        style={{ fontFamily: MONO, fontSize: 11, background: playing ? C.amber : C.panel2, color: playing ? "#000" : C.text, border: `1px solid ${C.border}`, padding: "4px 12px", cursor: "pointer" }}>
        {playing ? "PAUSE" : "PLAY"}
      </button>
      <select value={speed} onChange={e => setSpeed(+e.target.value)}
        style={{ fontFamily: MONO, fontSize: 10, background: C.panel2, color: C.text, border: `1px solid ${C.border}`, padding: "3px" }}>
        <option value={400}>slow</option><option value={180}>med</option><option value={80}>fast</option>
      </select>
      <div style={{ display: "grid", gridTemplateColumns: `repeat(${NF}, 1fr)`, gap: 2, flex: 1 }}>
        {frames.map((f, i) => (
          <div key={i} onClick={() => { setFrame(i); setPlaying(false); }} title={`substage ${i} · ${f.terrain_name} · ${f.op}${f.op_sign > 0 ? "+" : "−"}`}
            style={{ height: 22, cursor: "pointer", background: TERRAIN_COLORS[f.terrain_name],
              opacity: i === frame ? 1 : 0.38, outline: i === frame ? `1px solid ${C.amber}` : "none" }} />
        ))}
      </div>
      <span style={{ fontFamily: MONO, fontSize: 11, color: C.amber, minWidth: 150 }}>
        s{String(frame).padStart(2, "0")} · {frames[frame].terrain_name} · {frames[frame].op}{frames[frame].op_sign > 0 ? "+" : "−"}
      </span>
    </div>
  );
}

/* ---------- per-qubit Bloch cell: XY-disk with trail + Z gauge ---------- */
function BlochCell({ q, frame, mode, selQubit, setSelQubit }) {
  const r = 40, cx = 50, cy = 50;
  const sel = selQubit === q;
  const trail = (eng) => T.engines[eng].frames.slice(0, frame + 1)
    .map(f => `${cx + f.bloch[q][0] * r},${cy - f.bloch[q][1] * r}`).join(" ");
  const cur = (eng) => T.engines[eng].frames[frame].bloch[q];
  const show = (eng) => mode === "both" || mode === eng;
  const zBar = (eng, x) => {
    const z = cur(eng)[2];
    const col = eng === "L" ? C.amber : C.cyan;
    return (
      <g key={eng}>
        <rect x={x} y={10} width={6} height={80} fill="none" stroke={C.border} />
        <line x1={x} x2={x + 6} y1={50} y2={50} stroke={C.dim} strokeWidth="0.6" />
        <rect x={x + 1} y={z >= 0 ? 50 - z * 40 : 50} width={4} height={Math.abs(z) * 40} fill={col} opacity="0.9" />
      </g>
    );
  };
  return (
    <svg viewBox="0 0 126 100" onClick={() => setSelQubit(sel ? null : q)}
      style={{ width: "100%", cursor: "pointer", background: sel ? C.panel2 : "transparent", border: `1px solid ${sel ? C.dim : C.border}` }}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={C.border} />
      <line x1={cx - r} x2={cx + r} y1={cy} y2={cy} stroke={C.grid} /><line x1={cx} x2={cx} y1={cy - r} y2={cy + r} stroke={C.grid} />
      {show("R") && <polyline points={trail("R")} fill="none" stroke={C.cyan} strokeWidth="0.8" opacity="0.55" />}
      {show("L") && <polyline points={trail("L")} fill="none" stroke={C.amber} strokeWidth="0.8" opacity="0.7" />}
      {show("R") && <circle cx={cx + cur("R")[0] * r} cy={cy - cur("R")[1] * r} r="2.5" fill={C.cyan} />}
      {show("L") && <circle cx={cx + cur("L")[0] * r} cy={cy - cur("L")[1] * r} r="2.5" fill={C.amber} />}
      {show("L") && zBar("L", 104)}{show("R") && zBar("R", 114)}
      <text x="6" y="14" fill={C.text} fontFamily={MONO} fontSize="9">q{q}</text>
      <text x="6" y="95" fill={C.dim} fontFamily={MONO} fontSize="7">xy-disk · z</text>
    </svg>
  );
}

/* ---------- MI web: qubits on a ring, edge width = pairwise MI ---------- */
function MIWeb({ frame, mode, selQubit }) {
  const R = 56, cx = 80, cy = 78;
  const pos = q => [cx + R * Math.cos((q / NQ) * 2 * Math.PI - Math.PI / 2), cy + R * Math.sin((q / NQ) * 2 * Math.PI - Math.PI / 2)];
  const edges = (eng, col, dash) => T.engines[eng].frames[frame].mi_pairs.map((p, k) => {
    const [x1, y1] = pos(p.i), [x2, y2] = pos(p.j);
    const wgt = Math.max(0, p.mi) / Math.log(4); // normalize by max MI for a qubit pair
    const dim = selQubit != null && p.i !== selQubit && p.j !== selQubit;
    return <line key={eng + k} x1={x1} y1={y1} x2={x2} y2={y2} stroke={col} strokeDasharray={dash}
      strokeWidth={0.5 + wgt * 7} opacity={dim ? 0.12 : 0.4 + wgt * 0.6} />;
  });
  const f = T.engines[mode === "R" ? "R" : "L"].frames[frame];
  return (
    <svg viewBox="0 0 160 160" style={{ width: "100%", height: "100%" }}>
      {(mode === "both" || mode === "R") && edges("R", C.cyan, "3 2")}
      {(mode === "both" || mode === "L") && edges("L", C.amber, null)}
      {Array.from({ length: NQ }, (_, q) => {
        const [x, y] = pos(q);
        return (
          <g key={q}>
            <circle cx={x} cy={y} r="9" fill={C.panel2} stroke={selQubit === q ? C.amber : C.border} />
            <text x={x} y={y + 3} textAnchor="middle" fill={C.text} fontFamily={MONO} fontSize="8">q{q}</text>
          </g>
        );
      })}
      <text x="4" y="155" fill={C.dim} fontFamily={MONO} fontSize="7">edge width = pairwise MI (max ln4) · L solid / R dashed</text>
      <text x="4" y="12" fill={C.dim} fontFamily={MONO} fontSize="8">I(half:half) L={fmt(T.engines.L.frames[frame].mi_halfchain)} R={fmt(T.engines.R.frames[frame].mi_halfchain)}</text>
    </svg>
  );
}

/* ---------- strip chart over 32 substages with terrain bands ---------- */
function Strip({ frame, setFrame, series, yLabel, h = 90 }) {
  const w = 640, padL = 34, padB = 12, padT = 6;
  const xs = i => padL + (i / (NF - 1)) * (w - padL - 6);
  const all = series.flatMap(s => s.vals);
  const lo = Math.min(...all), hi = Math.max(...all);
  const ys = v => padT + (1 - (v - lo) / (hi - lo || 1)) * (h - padT - padB);
  const frames = T.engines.L.frames;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: "100%", display: "block" }}
      onClick={e => {
        const box = e.currentTarget.getBoundingClientRect();
        const x = ((e.clientX - box.left) / box.width) * w;
        setFrame(Math.max(0, Math.min(NF - 1, Math.round(((x - padL) / (w - padL - 6)) * (NF - 1)))));
      }}>
      {frames.map((f, i) => (
        <rect key={i} x={xs(i) - (w - padL - 6) / (NF - 1) / 2} y={padT} width={(w - padL - 6) / (NF - 1)} height={h - padT - padB}
          fill={TERRAIN_COLORS[f.terrain_name]} opacity="0.13" />
      ))}
      {series.map((s, k) => (
        <polyline key={k} fill="none" stroke={s.color} strokeWidth="1.2" strokeDasharray={s.dash}
          points={s.vals.map((v, i) => `${xs(i)},${ys(v)}`).join(" ")} />
      ))}
      <line x1={xs(frame)} x2={xs(frame)} y1={padT} y2={h - padB} stroke={C.amber} strokeWidth="1" />
      <text x="2" y="12" fill={C.dim} fontFamily={MONO} fontSize="8">{yLabel}</text>
      <text x="2" y={h - 2} fill={C.dim} fontFamily={MONO} fontSize="7">{fmt(lo, 2)}–{fmt(hi, 2)}</text>
    </svg>
  );
}

/* ---------- witness panel: L0 metric trajectories vs random controls ---------- */
function Witness({ frame, setFrame, method, setMethod }) {
  const m = W.methods[method];
  const w = 640, h = 150, padL = 40, padB = 14, padT = 8;
  const runs1 = m.type1_runs.filter(r => r.l0_metrics), runs2 = m.type2_runs.filter(r => r.l0_metrics);
  const ctrls = W.controls.filter(r => r.l0_metrics);
  const all = [...runs1, ...runs2, ...ctrls].flatMap(r => r.l0_metrics);
  const lo = Math.min(...all), hi = Math.max(...all);
  const xs = i => padL + (i / (NF - 1)) * (w - padL - 6);
  const ys = v => padT + (1 - (v - lo) / (hi - lo || 1)) * (h - padT - padB);
  const band = Array.from({ length: NF }, (_, i) => {
    const vals = ctrls.map(r => r.l0_metrics[i]);
    return [Math.min(...vals), Math.max(...vals)];
  });
  const bandPath = "M" + band.map(([mn], i) => `${xs(i)},${ys(mn)}`).join(" L") +
    " L" + band.map(([, mx], i) => `${xs(i)},${ys(mx)}`).reverse().join(" L") + " Z";
  return (
    <div>
      <div style={{ display: "flex", gap: 6, marginBottom: 6 }}>
        {Object.keys(W.methods).map(k => (
          <button key={k} onClick={() => setMethod(k)}
            style={{ fontFamily: MONO, fontSize: 9, padding: "3px 8px", cursor: "pointer", background: k === method ? C.amber : C.panel2, color: k === method ? "#000" : C.dim, border: `1px solid ${C.border}` }}>
            {k}
          </button>
        ))}
        <span style={{ fontFamily: MONO, fontSize: 9, color: C.dim, marginLeft: "auto" }}>
          grey band = random-purified controls (min–max) · amber = type-1 · cyan = type-2
        </span>
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} style={{ width: "100%", display: "block" }}
        onClick={e => {
          const box = e.currentTarget.getBoundingClientRect();
          const x = ((e.clientX - box.left) / box.width) * w;
          setFrame(Math.max(0, Math.min(NF - 1, Math.round(((x - padL) / (w - padL - 6)) * (NF - 1)))));
        }}>
        <path d={bandPath} fill={C.dim} opacity="0.18" />
        {runs1.map((r, k) => <polyline key={"a" + k} fill="none" stroke={C.amber} strokeWidth="1" opacity="0.85"
          points={r.l0_metrics.map((v, i) => `${xs(i)},${ys(v)}`).join(" ")} />)}
        {runs2.map((r, k) => <polyline key={"b" + k} fill="none" stroke={C.cyan} strokeWidth="1" opacity="0.85"
          points={r.l0_metrics.map((v, i) => `${xs(i)},${ys(v)}`).join(" ")} />)}
        <line x1={xs(frame)} x2={xs(frame)} y1={padT} y2={h - padB} stroke={C.amber} strokeWidth="1" />
        <text x="2" y="12" fill={C.dim} fontFamily={MONO} fontSize="8">L0 finite_regularization_diff</text>
        <text x="2" y={h - 2} fill={C.dim} fontFamily={MONO} fontSize="7">{lo.toExponential(2)}–{hi.toExponential(2)}</text>
      </svg>
      <div style={{ fontFamily: MONO, fontSize: 9, color: C.dim, marginTop: 6, lineHeight: 1.7 }}>
        {Object.entries(W.checks.positive).map(([k, v]) => v.pass !== undefined && (
          <div key={k}>
            <span style={{ color: v.pass ? C.amber : C.rose }}>{v.pass ? "✓" : "✗"}</span> {k}
            {v.value !== undefined && <span> = {String(v.value).slice(0, 60)}</span>}
          </div>
        ))}
        <div style={{ color: C.rose, marginTop: 4 }}>promotion_allowed: {String(W.meta.promotion_allowed)} · classification: {W.meta.classification}</div>
        <div style={{ color: C.dim, marginTop: 2 }}>claim_ceiling: {W.meta.claim_ceiling}</div>
      </div>
    </div>
  );
}

/* ---------- app ---------- */
function App() {
  const [frame, setFrame] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(180);
  const [mode, setMode] = useState("both");
  const [method, setMethod] = useState("eigh_argmax");
  const [selQubit, setSelQubit] = useState(null);

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => setFrame(f => (f + 1) % NF), speed);
    return () => clearInterval(id);
  }, [playing, speed]);

  useEffect(() => {
    const onKey = e => {
      if (e.key === " ") { e.preventDefault(); setPlaying(p => !p); }
      if (e.key === "ArrowRight") setFrame(f => Math.min(NF - 1, f + 1));
      if (e.key === "ArrowLeft") setFrame(f => Math.max(0, f - 1));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const fL = T.engines.L.frames[frame], fR = T.engines.R.frames[frame];
  const ent = eng => T.engines[eng].frames.map(f => f.entropy);
  const pur = eng => T.engines[eng].frames.map(f => f.purity);
  const mih = eng => T.engines[eng].frames.map(f => f.mi_halfchain);

  return (
    <div style={{ fontFamily: "Inter, sans-serif", color: C.text, padding: 10, display: "flex", flexDirection: "column", gap: 8, maxWidth: 1500, margin: "0 auto" }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
        <span style={{ fontFamily: MONO, fontSize: 14, color: C.text }}>ENGINE V6 LAB</span>
        <span style={{ fontFamily: MONO, fontSize: 9, color: C.dim }}>TrainableEngineV6 · {NQ} qubits · 32 substages · seed {T.meta.seed}</span>
        <Chip color={C.amber}>source-backed</Chip>
        <Chip color={C.rose}>untrained reference · display-only</Chip>
        <div style={{ marginLeft: "auto", display: "flex", gap: 4 }}>
          {["L", "R", "both"].map(k => (
            <button key={k} onClick={() => setMode(k)}
              style={{ fontFamily: MONO, fontSize: 9, padding: "3px 10px", cursor: "pointer", background: mode === k ? C.amber : C.panel2, color: mode === k ? "#000" : C.dim, border: `1px solid ${C.border}` }}>
              {k === "L" ? "L (type-1)" : k === "R" ? "R (type-2)" : "L + R"}
            </button>
          ))}
        </div>
      </div>

      <Panel title="TRANSPORT — 8 stages × 4 substage kicks (terrain-colored) · space=play · ←/→=step">
        <Transport frame={frame} setFrame={setFrame} playing={playing} setPlaying={setPlaying} speed={speed} setSpeed={setSpeed} />
      </Panel>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr 1.3fr", gap: 8 }}>
        {Array.from({ length: NQ }, (_, q) => (
          <Panel key={q} title={`Q${q} BLOCH · S=${fmt(fL.qubit_entropy[q])}${mode !== "L" ? ` / ${fmt(fR.qubit_entropy[q])}` : ""}`}>
            <BlochCell q={q} frame={frame} mode={mode} selQubit={selQubit} setSelQubit={setSelQubit} />
          </Panel>
        ))}
        <Panel title="MI WEB — pairwise mutual information">
          <MIWeb frame={frame} mode={mode} selQubit={selQubit} />
        </Panel>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        <Panel title="FULL-STATE ENTROPY (solid) + PURITY (dashed) — L amber / R cyan" right={
          <span style={{ fontFamily: MONO, fontSize: 9, color: C.dim }}>S={fmt(fL.entropy)} / {fmt(fR.entropy)} · P={fmt(fL.purity)} / {fmt(fR.purity)}</span>}>
          <Strip frame={frame} setFrame={setFrame} yLabel="S, purity"
            series={[
              ...(mode !== "R" ? [{ vals: ent("L"), color: C.amber }, { vals: pur("L"), color: C.amber, dash: "3 2" }] : []),
              ...(mode !== "L" ? [{ vals: ent("R"), color: C.cyan }, { vals: pur("R"), color: C.cyan, dash: "3 2" }] : []),
            ]} />
        </Panel>
        <Panel title="HALF-CHAIN MUTUAL INFORMATION I(01:23)">
          <Strip frame={frame} setFrame={setFrame} yLabel="I(L:R) nats"
            series={[
              ...(mode !== "R" ? [{ vals: mih("L"), color: C.amber }] : []),
              ...(mode !== "L" ? [{ vals: mih("R"), color: C.cyan }] : []),
            ]} />
        </Panel>
      </div>

      <Panel title={`L0 PURIFICATION-BRIDGE WITNESS — canonical probe results (${W.meta.timestamp_utc})`}>
        <Witness frame={frame} setFrame={setFrame} method={method} setMethod={setMethod} />
      </Panel>

      <div style={{ fontFamily: MONO, fontSize: 8, color: C.dim, lineHeight: 1.6, padding: "2px 2px 10px" }}>
        trajectory: computed by {T.meta.source_module} via {T.meta.exporter} · exported {T.meta.exported_utc} · {T.meta.engine_params}<br />
        witness: mirrored verbatim from {W.meta.canonical_path} · {T.meta.claim_note}
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
