function SzilardBox({ t, selected, op }) {
  const partitionVisible = selected >= 1 && selected < 4;
  const particleX = selected < 2 ? 168 : selected === 2 ? 126 : 254;
  const memory = selected < 2 ? 'blank' : selected < 4 ? 'record' : 'erased';
  const probeOn = selected === 2;
  const feedbackOn = selected === 3;
  const eraseOn = selected === 4;

  return (
    <svg viewBox="0 0 620 360" style={{ width: '100%', minHeight: 320, border: `1px solid ${t.line}`, background: t.bg }}>
      <rect x="34" y="42" width="552" height="276" fill={t.bg2} stroke={t.lineHex} />
      <rect x="70" y="88" width="330" height="142" fill={t.bg} stroke={t.paperDimHex} strokeWidth="2" />
      {partitionVisible && <line x1="235" y1="88" x2="235" y2="230" stroke={t.cyanHex} strokeWidth="5" />}
      <circle cx={particleX} cy="160" r="13" fill={feedbackOn ? t.amberHex : t.paperHex} />
      <text x="80" y="70" fill={t.paperDimHex} fontFamily="JetBrains Mono" fontSize="11">{op.title}</text>
      <rect x="430" y="86" width="104" height="72" fill={memory === 'record' ? t.bg3 : t.bg} stroke={memory === 'record' ? t.amberHex : t.paperDimHex} />
      <text x="482" y="113" textAnchor="middle" fill={t.paperDimHex} fontFamily="JetBrains Mono" fontSize="10">demon memory</text>
      <text x="482" y="138" textAnchor="middle" fill={memory === 'record' ? t.amberHex : t.paperFaintHex} fontFamily="JetBrains Mono" fontSize="12">{memory}</text>
      {probeOn && <path d="M398 122 C420 112, 430 112, 452 122" fill="none" stroke={t.amberHex} strokeWidth="3" />}
      {feedbackOn && <path d="M430 178 C380 196, 328 206, 268 166" fill="none" stroke={t.amberHex} strokeWidth="4" />}
      {eraseOn && <path d="M482 158 l0 54" stroke={t.roseHex} strokeWidth="4" />}
      <rect x="88" y="260" width="154" height="36" fill={partitionVisible ? t.cyanHex : t.bg3} opacity={partitionVisible ? 0.25 : 1} stroke={partitionVisible ? t.cyanHex : t.lineHex} />
      <text x="165" y="283" textAnchor="middle" fill={partitionVisible ? t.paperHex : t.paperDimHex} fontFamily="JetBrains Mono" fontSize="11">partition state</text>
      <rect x="254" y="260" width="154" height="36" fill={feedbackOn ? t.amberHex : t.bg3} opacity={feedbackOn ? 0.25 : 1} stroke={feedbackOn ? t.amberHex : t.lineHex} />
      <text x="331" y="283" textAnchor="middle" fill={feedbackOn ? t.paperHex : t.paperDimHex} fontFamily="JetBrains Mono" fontSize="11">work extraction</text>
      {[0, 1, 2, 3, 4].map(i => (
        <g key={i}>
          <circle cx={86 + i * 62} cy="246" r="6" fill={i === selected ? t.amberHex : t.bg3Hex} stroke={i === selected ? t.amberHex : t.paperFaintHex} />
          {i < 4 && <line x1={92 + i * 62} y1="246" x2={142 + i * 62} y2="246" stroke={t.lineHex} />}
        </g>
      ))}
      <text x="70" y="330" fill={t.paperFaintHex} fontFamily="JetBrains Mono" fontSize="10">display sequence keeps measurement, feedback, and erase as ordered operations</text>
    </svg>
  );
}

function SzilardEngineView({ t }) {
  const source = window.SZILARD_DUAL_STACK_DATA || null;
  const rosetta = window.ENGINE_ROSETTA_DATA || null;
  const [loopKey, setLoopKey] = React.useState('inductive_heating_loop');
  const loop = source && source.loops ? source.loops[loopKey] : null;
  const trace = loop && Array.isArray(loop.stage_trace) ? loop.stage_trace : [];
  const fallbackTrace = [
    { kind: 'initialized', before: 'empty', after: 'box_initialized', information_delta: 'not loaded', free_energy_gain: 'not loaded', erasure_cost: 'not loaded' },
    { kind: 'partition', before: 'box_initialized', after: 'partition_inserted', information_delta: 'not loaded', free_energy_gain: 'not loaded', erasure_cost: 'not loaded' },
    { kind: 'measurement', before: 'partition_inserted', after: 'measured_record', information_delta: 'not loaded', free_energy_gain: 'not loaded', erasure_cost: 'not loaded' },
    { kind: 'feedback', before: 'measured_record', after: 'feedback_purified', information_delta: 'not loaded', free_energy_gain: 'not loaded', erasure_cost: 'not loaded' },
    { kind: 'erasure', before: 'feedback_purified', after: 'erased_closed', information_delta: 'not loaded', free_energy_gain: 'not loaded', erasure_cost: 'not loaded' },
  ];
  const sourcedOps = trace.length
    ? (loopKey === 'inductive_heating_loop'
      ? [
        { kind: 'initialized', before: 'blank', after: 'initial_mixed_blank', information_delta: 0, free_energy_gain: 0, erasure_cost: 0 },
        { kind: 'partition', before: 'initial_mixed_blank', after: 'partition_inserted', information_delta: 'not represented in source row', free_energy_gain: 0, erasure_cost: 0 },
        ...trace,
      ]
      : trace)
    : fallbackTrace;
  const forwardTitles = ['Box initialized', 'Partition inserted', 'Measurement/probe', 'Feedback/work extraction', 'Memory erase / Landauer accounting'];
  const reverseTitles = ['Erase reversal bookkeeping', 'Feedback reversal', 'Measurement reversal'];
  const ops = sourcedOps.map((s, i) => ({
    ...s,
    title: (loopKey === 'deductive_cooling_loop' ? reverseTitles : forwardTitles)[i] || s.kind,
  }));
  const states = source && source.states ? source.states : {};
  const [selected, setSelected] = React.useState(0);
  const [running, setRunning] = React.useState(false);
  const [mode, setMode] = React.useState('mechanics');
  const [speed, setSpeed] = React.useState(900);
  const op = ops[selected] || ops[0];

  React.useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setSelected(i => (i + 1) % ops.length), speed);
    return () => clearInterval(id);
  }, [running, ops.length, speed]);

  React.useEffect(() => {
    setSelected(0);
    setRunning(false);
  }, [loopKey]);

  const sourcePath = source ? 'system_v4/probes/a2_state/sim_results/measure_feedback_erasure_recovery_cycle_pair_results.json mirrored by visualizer/szilard-dual-stack-data.js' : 'fallback UI skeleton';
  const topologyNodes = ops.map(o => o.after);
  const topologyEdges = ops.slice(1).map(o => [o.before, o.after]);
  const currentState = states[op.after] || {};
  const entropyRows = [
    { label: 'operation information delta', value: op.information_delta },
    { label: 'operation free energy gain', value: op.free_energy_gain },
    { label: 'operation erasure cost', value: op.erasure_cost },
    { label: 'state joint entropy', value: currentState.joint_entropy },
    { label: 'state memory entropy', value: currentState.memory_entropy },
    { label: 'state mutual information', value: currentState.mutual_information },
  ];
  const rosettaRows = rosetta ? rosetta.tier_correlations || [] : [];

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: 16, display: 'grid', gridTemplateColumns: 'minmax(520px, 1.35fr) minmax(340px, 0.65fr)', gap: 14 }}>
      <section style={{ border: `1px solid ${t.line}`, background: t.bg2, minWidth: 0 }}>
        <div style={{ padding: 14, borderBottom: `1px solid ${t.line}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
          <div>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.4 }}>SZILARD ENGINE · RUNNABLE DISPLAY SURFACE</Mono>
            <div style={{ marginTop: 5 }}><Mono t={t} size={18}>Ordered probe, feedback, work, and erase sequence</Mono></div>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
            {[
              ['inductive_heating_loop', 'measure'],
              ['deductive_cooling_loop', 'recover'],
            ].map(([id, label]) => (
              <button key={id} onClick={() => setLoopKey(id)} style={engineButton(t, loopKey === id)}>{label}</button>
            ))}
            <EngineToolbar t={t} mode={mode} setMode={setMode} running={running} setRunning={setRunning} selected={selected} count={ops.length} stepForward={() => setSelected((selected + 1) % ops.length)} stepBack={() => setSelected((selected + ops.length - 1) % ops.length)} speed={speed} setSpeed={setSpeed} />
          </div>
        </div>

        <div style={{ padding: 14, display: 'grid', gap: 12 }}>
          {mode === 'mechanics' && <SzilardBox t={t} selected={selected} op={op} />}
          {mode === 'entropy' && <div style={{ border: `1px solid ${t.line}`, background: t.bg, padding: 16 }}><EntropyBars t={t} rows={entropyRows} /></div>}
          {mode === 'topology' && <TopologyMap t={t} nodes={topologyNodes.filter(Boolean)} edges={topologyEdges} activeNode={op.after} />}
          {mode === 'axes' && <AxisGrid t={t} axes={source && source.axes_candidate_model && source.axes_candidate_model.axes} />}
          {mode === 'boundaries' && <BoundaryList t={t} boundaries={source && source.boundaries} />}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, minmax(0, 1fr))', gap: 8 }}>
            {ops.map((s, i) => (
              <button key={`${s.title}-${i}`} onClick={() => setSelected(i)} style={{
                minHeight: 86, padding: 10, cursor: 'pointer', textAlign: 'left',
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
        <SourceBoundary t={t} source={source} sourcePath={sourcePath} warning="Measurement/probe display is UI mechanics only unless backed by a cited sim artifact." />
        <div>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.4 }}>SELECTED OPERATION LEDGER</Mono>
          <LedgerRows t={t} rows={[
            ['operation', op.title],
            ['transition', `${op.before} -> ${op.after}`],
            ['information delta', op.information_delta],
            ['work channel', op.free_energy_gain],
            ['erase/Landauer note', op.erasure_cost],
            ['protocol direction', loopKey],
            ['state memory entropy', currentState.memory_entropy],
            ['state mutual information', currentState.mutual_information],
            ['net after erasure', source ? source.summary.net_after_erasure : 'not loaded'],
          ]} />
        </div>
        <div style={{ borderTop: `1px solid ${t.line}`, paddingTop: 12 }}>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.4 }}>QIT / ROSETTA BOUNDARY</Mono>
          <div style={{ marginTop: 8, display: 'grid', gap: 7 }}>
            {rosettaRows.slice(0, 4).map(row => (
              <div key={row.tier} style={{ border: `1px solid ${t.line}`, background: t.bg, padding: 9 }}>
                <Mono t={t} size={10}>{row.name}</Mono>
                <Mono t={t} size={9} dim style={{ display: 'block', marginTop: 5, lineHeight: 1.45 }}>{row.szilard}</Mono>
              </div>
            ))}
          </div>
        </div>
      </aside>
    </div>
  );
}

Object.assign(window, { SzilardEngineView });
