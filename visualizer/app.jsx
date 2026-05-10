// Detail panel & app shell

function DetailPanel({ t, data, resolution, cell }) {
  const r = data.resolutions.find(x => x.r === resolution);
  return (
    <div style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div>
        <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>SELECTED · RESOLUTION</Mono>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginTop: 4 }}>
          <Mono t={t} size={24}>R{r.r}</Mono>
          <Mono t={t} size={13}>{r.name}</Mono>
        </div>
        <Mono t={t} size={11} dim style={{ display: 'block', marginTop: 2 }}>{r.what}</Mono>
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <Tag t={t} tone={STATUS_TONE[r.status]} solid>{r.status}</Tag>
        <Tag t={t} tone="paperDim">{r.sims} sims</Tag>
      </div>

      <div style={{ borderLeft: `2px solid ${statusColor(t, r.status)}`, paddingLeft: 10 }}>
        <Mono t={t} size={11} style={{ lineHeight: 1.5, color: t.paperDim }}>{r.note}</Mono>
      </div>

      <div>
        <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>PRIMARY ARTIFACT</Mono>
        <div style={{ marginTop: 4, padding: 8, background: t.bg2, border: `1px solid ${t.line}` }}>
          <Mono t={t} size={10}>{r.artifact}</Mono>
        </div>
      </div>

      <div>
        <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>STATUS VOCABULARY</Mono>
        <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 4 }}>
          {data.meta.vocab.map(v => (
            <div key={v} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <StatusDot status={v} t={t} size={6} />
              <Mono t={t} size={10} dim>{v}</Mono>
            </div>
          ))}
        </div>
        <Mono t={t} size={9} dim style={{ display: 'block', marginTop: 8, lineHeight: 1.4 }}>
          forbidden: {data.meta.forbidden.join(' · ')}
        </Mono>
      </div>

      {cell && (
        <div style={{ borderTop: `1px solid ${t.line}`, paddingTop: 10 }}>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>
            MICROSTEP · #{cell.idx}{cell.slot ? ` · ${cell.slot}★` : ''}
          </Mono>
          <div style={{ display: 'flex', gap: 10, marginTop: 6, alignItems: 'baseline' }}>
            <Mono t={t} size={15}>{cell.label}</Mono>
          </div>
          <Mono t={t} size={10} dim style={{ display: 'block', marginTop: 4 }}>
            {cell.terrain} · {cell.op} · {cell.engine} / {cell.flux}
          </Mono>
          {cell.stage ? (
            <div style={{ marginTop: 6, padding: 8, border: `1px solid ${t.line}`, background: t.bg2 }}>
              <Mono t={t} size={9} dim style={{ letterSpacing: 1 }}>MACRO-STAGE BLOCK · {cell.stage.sign} · {cell.stage.role}</Mono>
              <div style={{ marginTop: 4 }}>
                <Mono t={t} size={10} dim style={{ lineHeight: 1.4 }}>
                  stage <b style={{ color: t.paper }}>{cell.stage.token}</b> spans 4 microsteps ({cell.stage.sign === 'UP' ? 'Ti↑ Te↑ Fi↑ Fe↑' : 'Ti↓ Te↓ Fi↓ Fe↓'}) · this is the <b style={{ color: t.paper }}>{cell.isNamed ? 'Ax6-naming' : `${cell.op}`}</b> microstep
                </Mono>
              </div>
            </div>
          ) : null}
        </div>
      )}

      <div style={{ borderTop: `1px solid ${t.line}`, paddingTop: 10 }}>
        <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>ENFORCEMENT</Mono>
        <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 6 }}>
          {data.enforcement.slice(0, 4).map(e => (
            <div key={e.n} style={{ display: 'grid', gridTemplateColumns: '16px 70px 1fr', gap: 6 }}>
              <Mono t={t} size={10} dim>{e.n}.</Mono>
              <Mono t={t} size={10}>{e.name}</Mono>
              <Mono t={t} size={10} dim style={{ lineHeight: 1.4 }}>{e.rule}</Mono>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const VIEWS = [
  { id: 'carnot-engine', label: 'Carnot', group: 'Engine Lab' },
  { id: 'szilard-engine', label: 'Szilard', group: 'Engine Lab' },
  { id: 'iching-engine', label: 'I Ching 64', group: 'Engine Lab' },
  { id: 'rosetta',     label: 'Rosetta', group: 'Engine Lab' },
  { id: 'sim-receipts', label: 'Sim Receipts', group: 'Engine Lab' },
  { id: 'schedule',    label: '64-Schedule', group: 'QIT System' },
  { id: 'atlas',       label: 'Fiber Atlas', group: 'QIT System' },
  { id: 'gstack-live', label: 'G-Stack Live', group: 'QIT System' },
  { id: 'lie',         label: 'Lie [X,Y]', group: 'Math Surfaces' },
  { id: 'mc',          label: 'M(C)', group: 'Math Surfaces' },
  { id: 'connes',      label: 'Connes', group: 'Math Surfaces' },
  { id: 'cycle',       label: 'Cycle Video', group: 'Legacy' },
  { id: 'gstack',      label: 'G-Stack Static', group: 'Legacy' },
];

function ViewTabs({ t, active, onChange }) {
  const groups = [...new Set(VIEWS.map(v => v.group))];
  return (
    <div style={{ display: 'flex', borderBottom: `1px solid ${t.line}`, overflowX: 'auto', background: t.bg }}>
      {groups.map(group => (
        <div key={group} style={{ display: 'flex', alignItems: 'stretch', borderRight: `1px solid ${t.line}` }}>
          <div style={{ padding: '9px 10px', background: t.bg2, minWidth: 92, borderRight: `1px solid ${t.line}` }}>
            <Mono t={t} size={9} dim style={{ textTransform: 'uppercase' }}>{group}</Mono>
          </div>
          {VIEWS.filter(v => v.group === group).map(v => {
            const isActive = active === v.id;
            return (
              <button key={v.id} onClick={() => onChange(v.id)}
                style={{
                  padding: '9px 12px', cursor: 'pointer',
                  border: 'none',
                  borderRight: `1px solid ${t.line}`,
                  background: isActive ? t.bg3 : 'transparent',
                  borderBottom: isActive ? `2px solid ${t.amber}` : '2px solid transparent',
                  marginBottom: -1,
                  whiteSpace: 'nowrap',
                }}>
                <Mono t={t} size={10} dim={!isActive} style={{ textTransform: 'uppercase' }}>{v.label}</Mono>
              </button>
            );
          })}
        </div>
      ))}
    </div>
  );
}

function TopBar({ t, data, tone, setTone, density, setDensity }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center',
      padding: '10px 18px',
      borderBottom: `1px solid ${t.line}`,
      gap: 14,
    }}>
      {/* diamond brand mark */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 12, height: 12, border: `1.5px solid ${t.amber}`, transform: 'rotate(45deg)' }} />
        <Mono t={t} size={12} style={{ letterSpacing: 2, textTransform: 'uppercase' }}>Codex Ratchet</Mono>
        <Mono t={t} size={10} dim>/ visualizer</Mono>
      </div>

      <div style={{ flex: 1 }} />

      <Mono t={t} size={10} dim>snapshot {data.meta.snapshot}</Mono>
      <Mono t={t} size={10} dim>·</Mono>
      <Mono t={t} size={10} dim>{data.meta.repo} @ {data.meta.commit}</Mono>
    </div>
  );
}

function CellFromKey(data, key) {
  if (!key) return null;
  const [ri, ci] = key.split(',').map(Number);
  const op = data.signedOps[ci];
  const terrain = data.terrains[ri];
  // find the macro-stage that contains this microstep
  const stage = data.macroStages.find(s => s.row === ri && s.cols.includes(ci));
  const isNamed = stage && stage.cols[0] === ci;
  const slot = isNamed ? stage.slot : null;
  return {
    idx: ri * 8 + ci + 1,
    slot,
    label: stage ? `${stage.token} · ${stage.outcome}` : `${terrain} × ${op.id}`,
    terrain,
    op: op.id,
    stage,
    isNamed,
    engine: data.terrainEngine[ri],
    flux: data.terrainFlux[ri],
  };
}

function App({ tweaks, setTweaks }) {
  const palette = tweaks.tone === 'paper' ? RATCHET_TOKENS.paper : RATCHET_TOKENS.terminal;
  const t = palette;
  const data = window.RATCHET_DATA;
  const [selectedR, setSelectedR] = React.useState(6);
  const [view, setView] = React.useState(() => {
    try {
      const requested = new URLSearchParams(window.location.search).get('view');
      return VIEWS.some(v => v.id === requested) ? requested : 'sim-receipts';
    } catch (e) {
      return 'sim-receipts';
    }
  });
  const [gridCell, setGridCell] = React.useState(null);
  const [gstackMode, setGstackMode] = React.useState('integrated');
  const [gsLayer, setGsLayer] = React.useState(null);
  const [gsCoupling, setGsCoupling] = React.useState(null);
  const [gsLego, setGsLego] = React.useState(null);

  React.useEffect(() => {
    try {
      const url = new URL(window.location.href);
      url.searchParams.set('view', view);
      window.history.replaceState(null, '', url);
    } catch (e) {}
  }, [view]);

  const cell = CellFromKey(data, gridCell);
  const focusWorkspace = view === 'carnot-engine' || view === 'szilard-engine' || view === 'iching-engine' || view === 'rosetta' || view === 'sim-receipts';

  return (
    <div data-screen-label="01 Console" style={{
      position: 'fixed', inset: 0,
      background: t.bg, color: t.paper,
      fontFamily: 'Inter, system-ui, sans-serif',
      display: 'flex', flexDirection: 'column',
      overflow: 'hidden',
    }}>
      <TopBar t={t} data={data} tone={tweaks.tone} setTone={v => setTweaks({ ...tweaks, tone: v })} />

      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: focusWorkspace ? '1fr' : '280px 1fr 340px', minHeight: 0 }}>
        {/* LEFT RAIL */}
        {!focusWorkspace && <div style={{ borderRight: `1px solid ${t.line}`, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <FrameLabel t={t} n="01" title="Resolution ladder · M(C)">
            <ResolutionLadder t={t} data={data} selected={selectedR} onSelect={setSelectedR} />
          </FrameLabel>
          <div style={{ borderTop: `1px solid ${t.line}` }}>
            <div style={{ padding: '8px 14px', borderBottom: `1px solid ${t.line}` }}>
              <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>§02 · LANES · NEVER MERGE</Mono>
            </div>
            <LanesStrip t={t} data={data} />
          </div>
        </div>}

        {/* CENTER */}
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0, background: t.bg }}>
          <ViewTabs t={t} active={view} onChange={setView} />
          <div style={{ flex: 1, overflow: view === 'cycle' || view === 'gstack-live' || view === 'schedule' || view === 'atlas' || view === 'lie' || view === 'mc' || view === 'connes' || view === 'rosetta' || view === 'sim-receipts' || view === 'iching-engine' || view === 'carnot-engine' || view === 'szilard-engine' ? 'hidden' : 'auto', position: 'relative' }}>
            {view === 'atlas' && <FiberBundleAtlas t={t} />}
            {view === 'lie' && <LieStructureView t={t} />}
            {view === 'mc' && <MCLevelSetView t={t} />}
            {view === 'connes' && <ConnesSpectralTripleView t={t} />}
            {view === 'rosetta' && <RosettaPanel t={t} />}
            {view === 'sim-receipts' && <SimReceiptIndexPanel t={t} />}
            {view === 'carnot-engine' && <CarnotEngineView t={t} />}
            {view === 'szilard-engine' && <SzilardEngineView t={t} />}
            {view === 'iching-engine' && <IchingEngineView t={t} />}
            {view === 'gstack-live' && <GStackLiveView t={t} data={data} />}
            {view === 'schedule' && <Schedule64Sim t={t} data={data} />}
            {view === 'cycle' && <RatchetCycle t={t} />}
            {view === 'gstack' && <GStackView t={t} data={data}
              mode={gstackMode} setMode={setGstackMode}
              selectedLayer={gsLayer} setSelectedLayer={setGsLayer}
              selectedCoupling={gsCoupling} setSelectedCoupling={setGsCoupling}
              selectedLego={gsLego} setSelectedLego={setGsLego} />}
          </div>
        </div>

        {/* RIGHT RAIL */}
        {!focusWorkspace && <div style={{ borderLeft: `1px solid ${t.line}`, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'auto' }}>
          <DetailPanel t={t} data={data} resolution={selectedR} cell={cell} />
        </div>}
      </div>

      {/* footer */}
      <div style={{
        borderTop: `1px solid ${t.line}`,
        padding: '6px 18px',
        display: 'flex', gap: 16, alignItems: 'center',
      }}>
        <Mono t={t} size={9} dim>graveyard-first</Mono>
        <Mono t={t} size={9} dim>·</Mono>
        <Mono t={t} size={9} dim>finitude + noncommutation</Mono>
        <Mono t={t} size={9} dim>·</Mono>
        <Mono t={t} size={9} dim>contamination-isolated boots</Mono>
        <div style={{ flex: 1 }} />
        <Mono t={t} size={9} dim>{data.meta.doctrine}</Mono>
      </div>

      <TweaksPanel t={t} tweaks={tweaks} setTweaks={setTweaks} />
    </div>
  );
}

// TWEAKS
function TweaksPanel({ t, tweaks, setTweaks }) {
  const [visible, setVisible] = React.useState(false);
  React.useEffect(() => {
    const onMsg = (e) => {
      if (!e.data || typeof e.data !== 'object') return;
      if (e.data.type === '__activate_edit_mode') setVisible(true);
      if (e.data.type === '__deactivate_edit_mode') setVisible(false);
    };
    window.addEventListener('message', onMsg);
    window.parent.postMessage({ type: '__edit_mode_available' }, '*');
    return () => window.removeEventListener('message', onMsg);
  }, []);

  const persist = (k, v) => {
    const next = { ...tweaks, [k]: v };
    setTweaks(next);
    window.parent.postMessage({ type: '__edit_mode_set_keys', edits: { [k]: v } }, '*');
  };

  if (!visible) return null;
  return (
    <div style={{
      position: 'fixed', bottom: 20, right: 20, width: 260,
      background: t.bg2, border: `1px solid ${t.line}`,
      padding: 14, zIndex: 100,
      boxShadow: '0 10px 40px rgba(0,0,0,0.4)',
    }}>
      <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>TWEAKS</Mono>
      <div style={{ height: 1, background: t.line, margin: '8px -14px 12px' }} />

      <Mono t={t} size={10} dim>tone</Mono>
      <div style={{ display: 'flex', marginTop: 6, marginBottom: 10 }}>
        {['terminal', 'paper'].map(v => (
          <button key={v} onClick={() => persist('tone', v)}
            style={{
              flex: 1, padding: '6px 8px', cursor: 'pointer',
              background: tweaks.tone === v ? t.paper : 'transparent',
              color: tweaks.tone === v ? t.bg : t.paperDim,
              border: `1px solid ${t.line}`,
              fontFamily: 'JetBrains Mono, monospace', fontSize: 10,
              textTransform: 'uppercase', letterSpacing: 1,
            }}>{v}</button>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { DetailPanel, ViewTabs, TopBar, App, TweaksPanel, VIEWS });
