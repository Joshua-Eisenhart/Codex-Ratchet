const ENGINE_PANEL = {
  source: 'source',
  mechanics: 'mechanics',
  entropy: 'entropy',
  topology: 'topology',
  axes: 'axes',
  boundaries: 'boundaries',
};

function fmtEngineValue(v) {
  if (typeof v === 'number') return Math.abs(v) < 1e-12 ? '0.000000' : v.toFixed(6);
  if (Array.isArray(v)) return v.join(' -> ');
  if (v && typeof v === 'object') return JSON.stringify(v);
  return String(v);
}

function EngineToolbar({ t, mode, setMode, running, setRunning, selected, count, stepForward, stepBack, speed = 900, setSpeed }) {
  const modes = [
    ['mechanics', 'Mechanics'],
    ['entropy', 'Entropy'],
    ['topology', 'Topology'],
    ['axes', 'Axes'],
    ['boundaries', 'Fences'],
  ];
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
      <button onClick={() => setRunning(!running)} title={running ? 'Pause engine run' : 'Run engine sequence'} style={engineButton(t, running)}>
        {running ? 'Pause' : 'Run'}
      </button>
      <button onClick={stepBack} title="Previous stage" style={engineButton(t, false)}>Prev</button>
      <button onClick={stepForward} title="Next stage" style={engineButton(t, false)}>Next</button>
      <Mono t={t} size={10} dim>{selected + 1}/{count}</Mono>
      {setSpeed && (
        <select value={speed} onChange={e => setSpeed(Number(e.target.value))} style={{
          ...engineButton(t, false),
          padding: '6px 8px',
          color: t.paperDim,
        }}>
          <option value={1400}>slow</option>
          <option value={900}>steady</option>
          <option value={450}>fast</option>
        </select>
      )}
      <div style={{ width: 1, height: 24, background: t.line }} />
      {modes.map(([id, label]) => (
        <button key={id} onClick={() => setMode(id)} style={engineButton(t, mode === id)}>
          {label}
        </button>
      ))}
    </div>
  );
}

function engineButton(t, active) {
  return {
    padding: '7px 10px',
    minHeight: 30,
    cursor: 'pointer',
    border: `1px solid ${active ? t.amber : t.line}`,
    background: active ? t.bg3 : 'transparent',
    color: active ? t.paper : t.paperDim,
    fontFamily: 'JetBrains Mono, monospace',
    fontSize: 10,
    textTransform: 'uppercase',
  };
}

function LedgerRows({ t, rows }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {rows.map(([k, v]) => (
        <div key={k} style={{ display: 'grid', gridTemplateColumns: '142px 1fr', gap: 10, borderTop: `1px solid ${t.line}`, padding: '9px 0' }}>
          <Mono t={t} size={10} dim>{k}</Mono>
          <Mono t={t} size={10} style={{ lineHeight: 1.45 }}>{fmtEngineValue(v)}</Mono>
        </div>
      ))}
    </div>
  );
}

function SourceBoundary({ t, source, sourcePath, warning }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <Tag t={t} tone={source ? 'amber' : 'paperFaint'}>{source ? 'source-backed' : 'fallback'}</Tag>
      <Mono t={t} size={10} dim style={{ lineHeight: 1.45 }}>{sourcePath}</Mono>
      {!source && <Mono t={t} size={10} dim>No canonical sim result loaded; displaying UI skeleton only.</Mono>}
      <div style={{ border: `1px solid ${t.rose}`, padding: 10, background: t.bg }}>
        <Mono t={t} size={10} style={{ lineHeight: 1.45 }}>{warning}</Mono>
      </div>
    </div>
  );
}

function EntropyBars({ t, rows }) {
  const numeric = rows.map(r => Math.abs(typeof r.value === 'number' ? r.value : 0));
  const max = Math.max(0.000001, ...numeric);
  return (
    <div style={{ display: 'grid', gap: 10 }}>
      {rows.map(row => {
        const value = typeof row.value === 'number' ? row.value : 0;
        const w = `${Math.max(4, Math.abs(value) / max * 100)}%`;
        const color = value < 0 ? t.rose : value > 0 ? t.amber : t.paperFaint;
        return (
          <div key={row.label}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
              <Mono t={t} size={10}>{row.label}</Mono>
              <Mono t={t} size={10} dim>{fmtEngineValue(row.value)}</Mono>
            </div>
            <div style={{ height: 10, background: t.bg, border: `1px solid ${t.line}`, marginTop: 5 }}>
              <div style={{ width: w, height: '100%', background: color, opacity: 0.78 }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function AxisGrid({ t, axes }) {
  const entries = Object.entries(axes || {});
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 8 }}>
      {entries.map(([id, axis]) => (
        <div key={id} style={{ border: `1px solid ${t.line}`, background: t.bg, padding: 10 }}>
          <Mono t={t} size={10} dim>{id}</Mono>
          <div style={{ marginTop: 4 }}><Mono t={t} size={12}>{axis.local_name}</Mono></div>
          <Mono t={t} size={10} dim style={{ display: 'block', marginTop: 6, lineHeight: 1.45 }}>{axis.degree_of_freedom || axis.observable}</Mono>
        </div>
      ))}
    </div>
  );
}

function TopologyMap({ t, nodes, edges, activeNode }) {
  const positions = nodes.map((node, i) => {
    const angle = (-Math.PI / 2) + (i / nodes.length) * Math.PI * 2;
    return { node, x: 210 + Math.cos(angle) * 126, y: 132 + Math.sin(angle) * 88 };
  });
  const pos = Object.fromEntries(positions.map(p => [p.node, p]));
  return (
    <svg viewBox="0 0 420 265" style={{ width: '100%', border: `1px solid ${t.line}`, background: t.bg }}>
      {edges.map((edge, i) => {
        const a = pos[edge[0]] || positions[i % positions.length];
        const b = pos[edge[1]] || positions[(i + 1) % positions.length];
        return <line key={`${edge[0]}-${edge[1]}-${i}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={t.lineHex} strokeWidth="2" />;
      })}
      {positions.map(p => (
        <g key={p.node}>
          <rect x={p.x - 48} y={p.y - 16} width="96" height="32" fill={p.node === activeNode ? t.bg3 : t.bg2} stroke={p.node === activeNode ? t.amberHex : t.paperFaintHex} />
          <text x={p.x} y={p.y + 4} textAnchor="middle" fill={p.node === activeNode ? t.paperHex : t.paperDimHex} fontFamily="JetBrains Mono" fontSize="9">{p.node}</text>
        </g>
      ))}
    </svg>
  );
}

function BoundaryList({ t, boundaries }) {
  return (
    <div style={{ display: 'grid', gap: 8 }}>
      {Object.entries(boundaries || {}).map(([id, b]) => (
        <div key={id} style={{ border: `1px solid ${t.line}`, background: t.bg, padding: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
            <Mono t={t} size={10}>{id}</Mono>
            <Tag t={t} tone={b.pass ? 'amber' : 'rose'}>{b.pass ? 'pass' : 'open'}</Tag>
          </div>
          <Mono t={t} size={10} dim style={{ display: 'block', marginTop: 6, lineHeight: 1.45 }}>{b.result || b.scope_note || 'boundary recorded'}</Mono>
        </div>
      ))}
    </div>
  );
}

Object.assign(window, {
  ENGINE_PANEL,
  fmtEngineValue,
  engineButton,
  EngineToolbar,
  LedgerRows,
  SourceBoundary,
  EntropyBars,
  AxisGrid,
  TopologyMap,
  BoundaryList,
});
