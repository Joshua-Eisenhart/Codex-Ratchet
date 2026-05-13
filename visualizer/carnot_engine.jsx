function CarnotChamber({ t, stage, selected, states }) {
  const widthByStage = [150, 220, 118, 70][selected] || 150;
  const activeCold = /cold/i.test(stage.after || '') || selected === 2;
  const activeHot = /hot/i.test(stage.before || '') || selected === 0 || selected === 3;
  const state = states.find(s => s.label === stage.after) || states.find(s => (stage.after || '').startsWith(s.label)) || states[selected % Math.max(1, states.length)] || {};
  const excitedY = 166 - (Number(state.p_excited || 0) * 80);

  return (
    <svg viewBox="0 0 620 360" style={{ width: '100%', minHeight: 320, border: `1px solid ${t.line}`, background: t.bg }}>
      <rect x="34" y="42" width="552" height="276" fill={t.bg2} stroke={t.lineHex} />
      <rect x="62" y="82" width="330" height="150" fill={t.bg} stroke={t.paperDimHex} strokeWidth="2" />
      <rect x="62" y="82" width={widthByStage} height="150" fill={activeHot ? t.amberHex : activeCold ? t.cyanHex : t.paperFaintHex} opacity="0.18" />
      <line x1={62 + widthByStage} y1="72" x2={62 + widthByStage} y2="242" stroke={t.paperHex} strokeWidth="6" />
      <line x1={62 + widthByStage} y1="157" x2="464" y2="157" stroke={t.paperDimHex} strokeWidth="3" />
      <rect x="464" y="126" width="46" height="62" fill={t.bg3} stroke={t.paperDimHex} />
      <circle cx="154" cy={excitedY} r="10" fill={t.amberHex} />
      <line x1="136" y1="190" x2="172" y2="126" stroke={t.lineHex} strokeWidth="2" />

      <rect x="72" y="258" width="154" height="36" fill={activeHot ? t.amberHex : t.bg3} opacity={activeHot ? 0.28 : 1} stroke={activeHot ? t.amberHex : t.lineHex} />
      <text x="149" y="281" textAnchor="middle" fill={activeHot ? t.paperHex : t.paperDimHex} fontFamily="JetBrains Mono" fontSize="11">hot reservoir</text>
      <rect x="238" y="258" width="154" height="36" fill={activeCold ? t.cyanHex : t.bg3} opacity={activeCold ? 0.28 : 1} stroke={activeCold ? t.cyanHex : t.lineHex} />
      <text x="315" y="281" textAnchor="middle" fill={activeCold ? t.paperHex : t.paperDimHex} fontFamily="JetBrains Mono" fontSize="11">cold reservoir</text>
      <path d="M506 96 C560 108, 560 206, 506 218" fill="none" stroke={Number(stage.work_by_system) >= 0 ? t.amberHex : t.roseHex} strokeWidth="4" />
      <text x="520" y="74" fill={t.paperDimHex} fontFamily="JetBrains Mono" fontSize="11">work channel</text>
      <text x="64" y="60" fill={t.paperDimHex} fontFamily="JetBrains Mono" fontSize="11">{stage.title}</text>
      {[0, 1, 2, 3].map(i => (
        <g key={i}>
          <circle cx={92 + i * 92} cy="304" r="7" fill={i === selected ? t.amberHex : t.bg3Hex} stroke={i === selected ? t.amberHex : t.paperFaintHex} />
          {i < 3 && <line x1={99 + i * 92} y1="304" x2={177 + i * 92} y2="304" stroke={t.lineHex} />}
        </g>
      ))}
      <text x="64" y="330" fill={t.paperFaintHex} fontFamily="JetBrains Mono" fontSize="10">piston width, heat contact, and probability marker are display projections from sourced state/stage fields</text>
    </svg>
  );
}

function CarnotEngineView({ t }) {
  const source = window.CARNOT_DUAL_STACK_DATA || null;
  const rosetta = window.ENGINE_ROSETTA_DATA || null;
  const [loopKey, setLoopKey] = React.useState('inductive_heating_loop');
  const loop = source && source.loops ? source.loops[loopKey] : null;
  const trace = loop && Array.isArray(loop.stage_trace) ? loop.stage_trace : [];
  const fallbackTrace = [
    { kind: 'isothermal', before: 'A', after: 'B', heat_into_system: 'not loaded', work_by_system: 'not loaded', delta_entropy: 'not loaded' },
    { kind: 'adiabatic', before: 'B', after: 'C', heat_into_system: 'not loaded', work_by_system: 'not loaded', delta_entropy: 'not loaded' },
    { kind: 'isothermal', before: 'C', after: 'D', heat_into_system: 'not loaded', work_by_system: 'not loaded', delta_entropy: 'not loaded' },
    { kind: 'adiabatic', before: 'D', after: 'A', heat_into_system: 'not loaded', work_by_system: 'not loaded', delta_entropy: 'not loaded' },
  ];
  const forwardTitles = ['Isothermal expansion', 'Adiabatic expansion', 'Isothermal compression', 'Adiabatic compression'];
  const reverseTitles = ['Adiabatic reverse return', 'Cold isothermal intake', 'Adiabatic reverse lift', 'Hot isothermal rejection'];
  const stages = (trace.length ? trace : fallbackTrace).map((s, i) => ({
    ...s,
    title: (loopKey === 'deductive_cooling_loop' ? reverseTitles : forwardTitles)[i] || s.kind,
  }));
  const states = source && Array.isArray(source.states) ? source.states : [];
  const [selected, setSelected] = React.useState(0);
  const [running, setRunning] = React.useState(false);
  const [mode, setMode] = React.useState('mechanics');
  const [speed, setSpeed] = React.useState(900);
  const stage = stages[selected] || stages[0];

  React.useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setSelected(i => (i + 1) % stages.length), speed);
    return () => clearInterval(id);
  }, [running, stages.length, speed]);

  React.useEffect(() => {
    setSelected(0);
    setRunning(false);
  }, [loopKey]);

  const sourcePath = source ? 'system_v4/probes/a2_state/sim_results/two_bath_heat_work_reversible_cycle_pair_results.json mirrored by visualizer/carnot-dual-stack-data.js' : 'fallback UI skeleton';
  const topologyNodes = states.map(s => s.label);
  const topologyEdges = stages.map(s => [s.before, String(s.after || '').replace('_return', '')]);
  const rosettaRows = rosetta ? rosetta.tier_correlations || [] : [];
  const entropyRows = [
    { label: 'stage heat into system', value: stage.heat_into_system },
    { label: 'stage work by system', value: stage.work_by_system },
    { label: 'stage entropy delta', value: stage.delta_entropy },
    { label: 'loop hot reservoir delta', value: loop && loop.hot_reservoir_entropy_delta },
    { label: 'loop cold reservoir delta', value: loop && loop.cold_reservoir_entropy_delta },
    { label: 'loop total reservoir delta', value: loop && loop.total_reservoir_entropy_delta },
  ];

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: 16, display: 'grid', gridTemplateColumns: 'minmax(520px, 1.35fr) minmax(340px, 0.65fr)', gap: 14 }}>
      <section style={{ border: `1px solid ${t.line}`, background: t.bg2, minWidth: 0 }}>
        <div style={{ padding: 14, borderBottom: `1px solid ${t.line}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
          <div>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.4 }}>CARNOT ENGINE · RUNNABLE DISPLAY SURFACE</Mono>
            <div style={{ marginTop: 5 }}><Mono t={t} size={18}>Four-leg heat/work cycle with sourced ledgers</Mono></div>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
            {[
              ['inductive_heating_loop', 'engine'],
              ['deductive_cooling_loop', 'refrigerator'],
            ].map(([id, label]) => (
              <button key={id} onClick={() => setLoopKey(id)} style={engineButton(t, loopKey === id)}>{label}</button>
            ))}
            <EngineToolbar t={t} mode={mode} setMode={setMode} running={running} setRunning={setRunning} selected={selected} count={stages.length} stepForward={() => setSelected((selected + 1) % stages.length)} stepBack={() => setSelected((selected + stages.length - 1) % stages.length)} speed={speed} setSpeed={setSpeed} />
          </div>
        </div>

        <div style={{ padding: 14, display: 'grid', gap: 12 }}>
          {mode === 'mechanics' && <CarnotChamber t={t} stage={stage} selected={selected} states={states} />}
          {mode === 'entropy' && <div style={{ border: `1px solid ${t.line}`, background: t.bg, padding: 16 }}><EntropyBars t={t} rows={entropyRows} /></div>}
          {mode === 'topology' && <TopologyMap t={t} nodes={topologyNodes.length ? topologyNodes : ['A', 'B', 'C', 'D']} edges={topologyEdges} activeNode={String(stage.after || '').replace('_return', '')} />}
          {mode === 'axes' && <AxisGrid t={t} axes={source && source.axes_candidate_model && source.axes_candidate_model.axes} />}
          {mode === 'boundaries' && <BoundaryList t={t} boundaries={source && source.boundaries} />}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 8 }}>
            {stages.map((s, i) => (
              <button key={s.title} onClick={() => setSelected(i)} style={{
                minHeight: 82, padding: 10, cursor: 'pointer', textAlign: 'left',
                background: selected === i ? t.bg3 : t.bg,
                color: t.paper, border: `1px solid ${selected === i ? t.amber : t.line}`,
                fontFamily: 'JetBrains Mono, monospace',
              }}>
                <Mono t={t} size={10} dim>{String(i + 1).padStart(2, '0')} · {s.kind}</Mono>
                <div style={{ marginTop: 6 }}><Mono t={t} size={11}>{s.title}</Mono></div>
                <Mono t={t} size={9} dim style={{ display: 'block', marginTop: 5 }}>{s.before} -> {s.after}</Mono>
              </button>
            ))}
          </div>
        </div>
      </section>

      <aside style={{ border: `1px solid ${t.line}`, background: t.bg2, padding: 14, display: 'flex', flexDirection: 'column', gap: 14 }}>
        <SourceBoundary t={t} source={source} sourcePath={sourcePath} warning="UI displays declared/sourced mechanics only; it does not create proof claims." />
        <div>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.4 }}>SELECTED LEG LEDGER</Mono>
          <LedgerRows t={t} rows={[
            ['current stage', stage.title],
            ['transition', `${stage.before} -> ${stage.after}`],
            ['heat transfer', stage.heat_into_system],
            ['work channel', stage.work_by_system],
            ['entropy note', stage.delta_entropy],
            ['loop role', loop && loop.role],
            ['cycle direction', loopKey],
            ['reported efficiency', source ? source.summary.forward_efficiency : 'not loaded'],
          ]} />
        </div>
        <div style={{ borderTop: `1px solid ${t.line}`, paddingTop: 12 }}>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.4 }}>QIT / ROSETTA BOUNDARY</Mono>
          <div style={{ marginTop: 8, display: 'grid', gap: 7 }}>
            {rosettaRows.slice(0, 4).map(row => (
              <div key={row.tier} style={{ border: `1px solid ${t.line}`, background: t.bg, padding: 9 }}>
                <Mono t={t} size={10}>{row.name}</Mono>
                <Mono t={t} size={9} dim style={{ display: 'block', marginTop: 5, lineHeight: 1.45 }}>{row.carnot}</Mono>
              </div>
            ))}
          </div>
        </div>
      </aside>
    </div>
  );
}

Object.assign(window, { CarnotEngineView });
