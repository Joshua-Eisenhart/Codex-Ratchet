function IchingYinYang({ t, selected, running, hexagram }) {
  const bits = (hexagram && hexagram.bits_bottom_to_top) || [0, 0, 0, 0, 0, 0];
  const yangCount = bits.reduce((a, b) => a + b, 0);
  const angle = selected * 360 / 64;
  const MiniRotor = ({ x, y, scale, turn, label }) => (
    <g transform={`translate(${x} ${y}) rotate(${turn}) scale(${scale})`} style={{ transition: running ? 'transform 0.45s linear' : 'transform 0.25s ease' }}>
      <circle cx="0" cy="0" r="52" fill={t.bg2Hex} stroke={t.lineHex} strokeWidth="2" />
      <circle cx="0" cy="0" r="42" fill={t.cyanHex} opacity="0.9" />
      <path d="M0,-42 A42,42 0 0 1 0,42 A21,21 0 0 1 0,0 A21,21 0 0 0 0,-42" fill={t.amberHex} opacity="0.9" />
      <circle cx="0" cy="-21" r="5" fill={t.cyanHex} />
      <circle cx="0" cy="21" r="5" fill={t.amberHex} />
      <text x="0" y="74" textAnchor="middle" fill={t.paperDimHex} fontFamily="JetBrains Mono" fontSize="22">{label}</text>
    </g>
  );
  return (
    <svg viewBox="0 0 620 360" style={{ width: '100%', border: `1px solid ${t.line}`, background: t.bg }}>
      <rect x="0" y="0" width="620" height="360" fill={t.bgHex} />
      <g transform={`translate(178 178) rotate(${angle})`} style={{ transition: running ? 'transform 0.45s linear' : 'transform 0.25s ease' }}>
        <circle cx="0" cy="0" r="118" fill={t.cyanHex} opacity="0.92" />
        <path d="M0,-118 A118,118 0 0 1 0,118 A59,59 0 0 1 0,0 A59,59 0 0 0 0,-118" fill={t.amberHex} opacity="0.92" />
        <circle cx="0" cy="-59" r="15" fill={t.cyanHex} />
        <circle cx="0" cy="59" r="15" fill={t.amberHex} />
        <circle cx="0" cy="0" r="118" fill="none" stroke={t.paperDimHex} strokeWidth="1.5" />
      </g>
      <MiniRotor x={80} y={70} scale={0.48} turn={angle * 2} label="lower" />
      <MiniRotor x={154} y={70} scale={0.48} turn={-angle * 1.5} label="upper" />
      <MiniRotor x={228} y={70} scale={0.48} turn={angle * 0.75} label="cycle" />
      <g transform="translate(370 70)">
        {bits.slice().reverse().map((bit, i) => (
          <g key={i} transform={`translate(0 ${i * 34})`}>
            {bit ? (
              <rect x="0" y="0" width="150" height="12" fill={t.amberHex} />
            ) : (
              <g>
                <rect x="0" y="0" width="64" height="12" fill={t.cyanHex} />
                <rect x="86" y="0" width="64" height="12" fill={t.cyanHex} />
              </g>
            )}
            <text x="170" y="11" fill={t.paperDimHex} fontFamily="JetBrains Mono" fontSize="10">line {6 - i}</text>
          </g>
        ))}
      </g>
      <text x="40" y="40" fill={t.paperDimHex} fontFamily="JetBrains Mono" fontSize="11">symbolic 64-state engine</text>
      <text x="40" y="322" fill={t.paperDimHex} fontFamily="JetBrains Mono" fontSize="11">yang lines: {yangCount} / yin lines: {6 - yangCount}</text>
      <text x="370" y="318" fill={t.paperDimHex} fontFamily="JetBrains Mono" fontSize="11">state {hexagram ? hexagram.state : 'not loaded'} · parity {hexagram ? hexagram.parity : 'not loaded'}</text>
    </svg>
  );
}

function IchingWheel({ t, hexagrams, selected, setSelected }) {
  return (
    <svg viewBox="0 0 420 420" style={{ width: '100%', border: `1px solid ${t.line}`, background: t.bg }}>
      <rect x="0" y="0" width="420" height="420" fill={t.bgHex} />
      {hexagrams.map((h, i) => {
        const a = i / 64 * Math.PI * 2 - Math.PI / 2;
        const r1 = i === selected ? 142 : 154;
        const r2 = i % 8 === 0 ? 194 : 184;
        const x1 = 210 + Math.cos(a) * r1;
        const y1 = 210 + Math.sin(a) * r1;
        const x2 = 210 + Math.cos(a) * r2;
        const y2 = 210 + Math.sin(a) * r2;
        const color = h.loop_family === 'inductive' ? t.amberHex : t.cyanHex;
        return (
          <g key={h.index} onClick={() => setSelected(i)} style={{ cursor: 'pointer' }}>
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={i === selected ? t.paperHex : color} strokeWidth={i === selected ? 4 : i % 8 === 0 ? 2 : 1} opacity={i === selected ? 1 : 0.62} />
            <circle cx={x2} cy={y2} r={i === selected ? 5 : 2.5} fill={i === selected ? t.paperHex : color} />
          </g>
        );
      })}
      <circle cx="210" cy="210" r="132" fill="none" stroke={t.lineHex} />
      <circle cx="210" cy="210" r="198" fill="none" stroke={t.lineHex} />
      <text x="210" y="204" textAnchor="middle" fill={t.paperHex} fontFamily="JetBrains Mono" fontSize="28">64</text>
      <text x="210" y="228" textAnchor="middle" fill={t.paperDimHex} fontFamily="JetBrains Mono" fontSize="10">single-line cycle</text>
    </svg>
  );
}

function SimReceiptIndexPanel({ t }) {
  const receipts = [
    { name: 'Carnot dual stack', family: 'Carnot', cls: 'canonical loaded', path: 'system_v4/probes/a2_state/sim_results/two_bath_heat_work_reversible_cycle_pair_results.json', pass: window.CARNOT_DUAL_STACK_DATA && window.CARNOT_DUAL_STACK_DATA.summary && window.CARNOT_DUAL_STACK_DATA.summary.all_pass, visual: 'loaded into Carnot tab' },
    { name: 'Carnot entropy family array', family: 'Carnot', cls: 'canonical indexed', path: 'system_v4/probes/a2_state/sim_results/carnot_entropy_family_array_results.json', pass: null, visual: 'indexed path; browser payload not generated yet' },
    { name: 'Carnot tool coupling matrix', family: 'Carnot', cls: 'canonical indexed', path: 'system_v4/probes/a2_state/sim_results/carnot_tool_coupling_matrix_results.json', pass: null, visual: 'indexed path; browser payload not generated yet' },
    { name: 'Szilard dual stack', family: 'Szilard', cls: 'canonical loaded', path: 'system_v4/probes/a2_state/sim_results/measure_feedback_erasure_recovery_cycle_pair_results.json', pass: window.SZILARD_DUAL_STACK_DATA && window.SZILARD_DUAL_STACK_DATA.summary && window.SZILARD_DUAL_STACK_DATA.summary.all_pass, visual: 'loaded into Szilard tab' },
    { name: 'Szilard topology entropy array', family: 'Szilard', cls: 'canonical indexed', path: 'system_v4/probes/a2_state/sim_results/szilard_topology_entropy_array_results.json', pass: null, visual: 'indexed path; browser payload not generated yet' },
    { name: 'Szilard measurement feedback substeps', family: 'Szilard', cls: 'canonical indexed', path: 'system_v4/probes/a2_state/sim_results/szilard_measurement_feedback_substeps_results.json', pass: null, visual: 'indexed path; browser payload not generated yet' },
    { name: 'QIT Szilard Landauer cycle', family: 'QIT/Szilard', cls: 'canonical indexed', path: 'system_v4/probes/a2_state/sim_results/qit_szilard_landauer_cycle_results.json', pass: null, visual: 'indexed path; browser payload not generated yet' },
    { name: 'I Ching 64 Rosetta', family: 'I Ching', cls: 'canonical loaded', path: 'system_v4/probes/a2_state/sim_results/six_bit_gray_code_single_flip_cycle_invariant_results.json', pass: window.SIX_BIT_GRAY_CODE_CYCLE_DATA && window.SIX_BIT_GRAY_CODE_CYCLE_DATA.summary && window.SIX_BIT_GRAY_CODE_CYCLE_DATA.summary.all_pass, visual: 'loaded into I Ching 64 tab' },
    { name: 'Triad modes', family: 'Rosetta', cls: 'canonical loaded', path: 'system_v4/probes/a2_state/sim_results/rosetta_triad_modes_results.json', pass: window.ROSETTA_TRIAD_MODES_DATA && window.ROSETTA_TRIAD_MODES_DATA.summary && window.ROSETTA_TRIAD_MODES_DATA.summary.all_pass, visual: 'loaded into Rosetta tab' },
    { name: 'Triad entropy/topology', family: 'Rosetta', cls: 'canonical loaded', path: 'system_v4/probes/a2_state/sim_results/rosetta_triad_entropy_topology_sweep_results.json', pass: window.ROSETTA_TRIAD_ENTROPY_TOPOLOGY_DATA && window.ROSETTA_TRIAD_ENTROPY_TOPOLOGY_DATA.summary && window.ROSETTA_TRIAD_ENTROPY_TOPOLOGY_DATA.summary.all_pass, visual: 'loaded into Rosetta tab' },
    { name: 'Triad order negatives', family: 'Rosetta', cls: 'canonical loaded', path: 'system_v4/probes/a2_state/sim_results/rosetta_triad_order_graveyard_results.json', pass: window.ROSETTA_TRIAD_ORDER_GRAVEYARD_DATA && window.ROSETTA_TRIAD_ORDER_GRAVEYARD_DATA.summary && window.ROSETTA_TRIAD_ORDER_GRAVEYARD_DATA.summary.all_pass, visual: 'loaded into Rosetta tab' },
    { name: 'Lego registry', family: 'Rosetta lego', cls: 'canonical loaded', path: 'system_v4/probes/a2_state/sim_results/rosetta_lego_registry_results.json', pass: window.ROSETTA_LEGO_REGISTRY_DATA && window.ROSETTA_LEGO_REGISTRY_DATA.summary && window.ROSETTA_LEGO_REGISTRY_DATA.summary.all_pass, visual: 'loaded into Rosetta tab' },
    { name: 'Coupled array', family: 'Rosetta lego', cls: 'canonical loaded', path: 'system_v4/probes/a2_state/sim_results/rosetta_lego_coupled_array_results.json', pass: window.ROSETTA_LEGO_COUPLED_ARRAY_DATA && window.ROSETTA_LEGO_COUPLED_ARRAY_DATA.summary && window.ROSETTA_LEGO_COUPLED_ARRAY_DATA.summary.all_pass, visual: 'loaded into Rosetta tab' },
    { name: 'Coupled negatives', family: 'Rosetta lego', cls: 'canonical loaded', path: 'system_v4/probes/a2_state/sim_results/rosetta_lego_coupled_array_graveyard_results.json', pass: window.ROSETTA_LEGO_COUPLED_ARRAY_GRAVEYARD_DATA && window.ROSETTA_LEGO_COUPLED_ARRAY_GRAVEYARD_DATA.summary && window.ROSETTA_LEGO_COUPLED_ARRAY_GRAVEYARD_DATA.summary.all_pass, visual: 'loaded into Rosetta tab' },
    { name: 'Prime QIT sidecar', family: 'Sidecar', cls: 'sidecar loaded', path: 'system_v4/probes/a2_state/sim_results/prime_qit_sidecar_probe_results.json', pass: window.PRIME_QIT_SIDECAR_DATA && window.PRIME_QIT_SIDECAR_DATA.summary && window.PRIME_QIT_SIDECAR_DATA.summary.all_pass, statusLabel: 'sidecar only', visual: 'loaded into Rosetta Prime Sidecar mode; no RH/PNT/QIT admission' },
    { name: 'Engine lab open-row audit', family: 'Engine lab', cls: 'controller index loaded', path: 'system_v4/probes/a2_state/sim_results/engine_lab_open_row_audit_results.json', pass: window.ENGINE_LAB_OPEN_ROW_AUDIT_DATA && window.ENGINE_LAB_OPEN_ROW_AUDIT_DATA.summary && window.ENGINE_LAB_OPEN_ROW_AUDIT_DATA.summary.audit_complete, statusLabel: 'audit loaded', visual: 'loaded into Rosetta Engine Lab mode' },
    { name: 'Engine lab next-work queue', family: 'Engine lab', cls: 'controller index loaded', path: 'system_v4/probes/a2_state/sim_results/engine_lab_next_work_queue_results.json', pass: window.ENGINE_LAB_NEXT_WORK_QUEUE_DATA && window.ENGINE_LAB_NEXT_WORK_QUEUE_DATA.summary && window.ENGINE_LAB_NEXT_WORK_QUEUE_DATA.summary.queue_complete, statusLabel: 'queue loaded', visual: 'loaded into Rosetta Engine Lab mode' },
    { name: 'Engine lab successor coverage', family: 'Engine lab', cls: 'controller index loaded', path: 'system_v4/probes/a2_state/sim_results/engine_lab_successor_coverage_audit_results.json', pass: window.ENGINE_LAB_SUCCESSOR_COVERAGE_DATA && window.ENGINE_LAB_SUCCESSOR_COVERAGE_DATA.summary && window.ENGINE_LAB_SUCCESSOR_COVERAGE_DATA.summary.all_pass, statusLabel: 'successor-covered', visual: 'successor-layer coverage only; source rows remain preserved-negative' },
    { name: 'Szilard open-row consolidation', family: 'Engine lab / Szilard', cls: 'controller index loaded', path: 'system_v4/probes/a2_state/sim_results/szilard_open_row_consolidation_results.json', pass: window.SZILARD_OPEN_ROW_CONSOLIDATION_DATA && window.SZILARD_OPEN_ROW_CONSOLIDATION_DATA.summary && window.SZILARD_OPEN_ROW_CONSOLIDATION_DATA.summary.all_pass, statusLabel: 'constraint-covered', visual: 'four Szilard open rows preserved negative with successor constraints only' },
  ];
  const loadedCount = receipts.filter(r => r.pass === true).length;
  const indexedCount = receipts.length - loadedCount;
  return (
    <div style={{ height: '100%', overflow: 'auto', padding: 16, display: 'grid', gap: 10 }}>
      <div style={{ border: `1px solid ${t.line}`, background: t.bg2, padding: 14 }}>
        <Mono t={t} size={10} dim style={{ letterSpacing: 1.4 }}>SIM RECEIPT INDEX</Mono>
        <div style={{ marginTop: 5 }}><Mono t={t} size={18}>What the visualizer is allowed to show</Mono></div>
        <div style={{ marginTop: 10, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Tag t={t} tone="amber">{loadedCount} loaded receipts</Tag>
          <Tag t={t} tone="cyan">{indexedCount} indexed paths</Tag>
          <Tag t={t} tone="paperDim">fallback claims disabled</Tag>
        </div>
      </div>
      {receipts.map(row => (
        <div key={row.name} style={{ border: `1px solid ${t.line}`, background: t.bg2, padding: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
            <Mono t={t} size={12}>{row.name}</Mono>
            <Tag t={t} tone={row.pass === true ? 'amber' : row.pass === null ? 'cyan' : 'rose'}>
              {row.statusLabel || (row.pass === true ? 'loaded/pass' : row.pass === null ? 'indexed only' : 'not loaded')}
            </Tag>
          </div>
          <LedgerRows t={t} rows={[
            ['family', row.family],
            ['classification', row.cls],
            ['result path', row.path],
            ['visual source', row.visual],
          ]} />
        </div>
      ))}
    </div>
  );
}

function IchingEngineView({ t }) {
  const source = window.SIX_BIT_GRAY_CODE_CYCLE_DATA || null;
  const hexagrams = (source && source.hexagrams) || [];
  const [selected, setSelected] = React.useState(0);
  const [running, setRunning] = React.useState(false);
  const [speed, setSpeed] = React.useState(700);
  const [mode, setMode] = React.useState('mechanics');
  const active = hexagrams[selected] || null;

  React.useEffect(() => {
    if (!running || !hexagrams.length) return;
    const id = setInterval(() => setSelected(i => (i + 1) % hexagrams.length), speed);
    return () => clearInterval(id);
  }, [running, speed, hexagrams.length]);

  const stepForward = () => setSelected(i => hexagrams.length ? (i + 1) % hexagrams.length : 0);
  const stepBack = () => setSelected(i => hexagrams.length ? (i - 1 + hexagrams.length) % hexagrams.length : 0);
  const axisRows = Object.entries((source && source.axes_candidate_model && source.axes_candidate_model.axes) || {});
  const currentRows = [
    ['current index', active && active.index],
    ['state', active && active.state],
    ['bits bottom->top', active && active.bits_bottom_to_top],
    ['lower trigram', active && active.lower_trigram],
    ['upper trigram', active && active.upper_trigram],
    ['polarity', active && active.polarity],
    ['loop family', active && active.loop_family],
    ['changed line', active && active.changed_line_from_previous],
  ];

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: 16, display: 'grid', gridTemplateColumns: 'minmax(560px, 1fr) 350px', gap: 14 }}>
      <section style={{ border: `1px solid ${t.line}`, background: t.bg }}>
        <div style={{ padding: 14, borderBottom: `1px solid ${t.line}`, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 260 }}>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.4 }}>I CHING 64 SYMBOLIC ENGINE</Mono>
            <div style={{ marginTop: 5 }}><Mono t={t} size={18}>Single-line transition schedule from canonical sim result</Mono></div>
          </div>
          <EngineToolbar t={t} mode={mode} setMode={setMode} running={running} setRunning={setRunning} selected={selected} count={hexagrams.length || 64} stepForward={stepForward} stepBack={stepBack} speed={speed} setSpeed={setSpeed} />
        </div>
        <div style={{ padding: 14, display: 'grid', gap: 12 }}>
          {mode === 'mechanics' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(360px, 1fr) 360px', gap: 12 }}>
              <IchingYinYang t={t} selected={selected} running={running} hexagram={active} />
              <IchingWheel t={t} hexagrams={hexagrams} selected={selected} setSelected={setSelected} />
            </div>
          )}
          {mode === 'entropy' && <EntropyBars t={t} rows={[
            { label: 'parity / loop family', value: active ? active.parity : 0 },
            { label: 'yang line count', value: active ? active.bits_bottom_to_top.reduce((a, b) => a + b, 0) : 0 },
            { label: 'state index / 64', value: active ? active.index / 64 : 0 },
          ]} />}
          {mode === 'topology' && <TopologyMap t={t} nodes={hexagrams.slice(0, 16).map(h => `h${h.index}`)} edges={hexagrams.slice(0, 15).map((h, i) => [`h${i}`, `h${i + 1}`])} activeNode={`h${selected < 16 ? selected : 0}`} />}
          {mode === 'axes' && <AxisGrid t={t} axes={source && source.axes_candidate_model && source.axes_candidate_model.axes} />}
          {mode === 'boundaries' && <BoundaryList t={t} boundaries={{
            symbolic_only: { pass: true, scope_note: source && source.summary && source.summary.scope_note },
            not_qit_engine: { pass: true, scope_note: 'No QIT engine or GStack promotion is claimed by this view.' },
            axis_candidate_only: { pass: true, scope_note: source && source.axes_candidate_model && source.axes_candidate_model.boundary },
          }} />}
        </div>
      </section>
      <aside style={{ border: `1px solid ${t.line}`, background: t.bg2, padding: 14, display: 'flex', flexDirection: 'column', gap: 14 }}>
        <SourceBoundary t={t} source={source} sourcePath="system_v4/probes/a2_state/sim_results/six_bit_gray_code_single_flip_cycle_invariant_results.json -> visualizer/six-bit-gray-code-cycle-data.js" warning="This view displays the symbolic 64-state sim receipt. It is not an I Ching proof, not QIT admission, and not an axis promotion." />
        <div>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.4 }}>CURRENT STATE</Mono>
          <LedgerRows t={t} rows={currentRows} />
        </div>
        <div>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.4 }}>AX0-AX6 CURRENT OBSERVABLES</Mono>
          <LedgerRows t={t} rows={axisRows.map(([id, axis]) => [id, `${axis.local_name}: ${axis.observable}`])} />
        </div>
      </aside>
    </div>
  );
}

Object.assign(window, { IchingEngineView, SimReceiptIndexPanel });
