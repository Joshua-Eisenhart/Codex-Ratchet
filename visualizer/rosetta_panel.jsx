function rosettaTone(t, value) {
  if (value === false || value === 'blocked' || value === 'rejected' || value === 'killed') return 'rose';
  if (value === 'open' || value === 'partial') return 'cyan';
  return 'amber';
}

function rosettaText(value) {
  if (value === null || value === undefined) return 'not loaded';
  if (Array.isArray(value)) return value.join(', ');
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function StatusCard({ t, label, value, sub, tone }) {
  return (
    <div style={{ border: `1px solid ${t.line}`, background: t.bg2, padding: 12, minHeight: 96 }}>
      <Mono t={t} size={9} dim style={{ letterSpacing: 1.2 }}>{label}</Mono>
      <div style={{ marginTop: 9 }}>
        <Mono t={t} size={22} style={{ color: tone === 'rose' ? t.roseHex : tone === 'cyan' ? t.cyanHex : t.amberHex }}>
          {rosettaText(value)}
        </Mono>
      </div>
      {sub && <Mono t={t} size={10} dim style={{ display: 'block', marginTop: 8, lineHeight: 1.45 }}>{sub}</Mono>}
    </div>
  );
}

function RosettaRow({ t, title, status, rows }) {
  return (
    <div style={{ border: `1px solid ${t.line}`, background: t.bg, padding: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'baseline' }}>
        <Mono t={t} size={12}>{title}</Mono>
        {status !== undefined && <Tag t={t} tone={rosettaTone(status)}>{rosettaText(status)}</Tag>}
      </div>
      <LedgerRows t={t} rows={rows} />
    </div>
  );
}

function RosettaMiniWheel({ t, data }) {
  const hexagrams = (data && data.hexagrams) || [];
  const activeCount = hexagrams.length || 64;
  const ticks = Array.from({ length: 64 }, (_, i) => {
    const angle = (i / 64) * Math.PI * 2 - Math.PI / 2;
    const inner = 82;
    const outer = i % 8 === 0 ? 110 : 100;
    return {
      i,
      x1: 130 + Math.cos(angle) * inner,
      y1: 130 + Math.sin(angle) * inner,
      x2: 130 + Math.cos(angle) * outer,
      y2: 130 + Math.sin(angle) * outer,
      major: i % 8 === 0,
      loaded: i < activeCount,
    };
  });
  return (
    <div style={{ border: `1px solid ${t.line}`, background: t.bg2, padding: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 10 }}>
        <Mono t={t} size={10} dim style={{ letterSpacing: 1.2 }}>64-STATE SYMBOLIC WHEEL</Mono>
        <Tag t={t} tone={hexagrams.length ? 'amber' : 'cyan'}>{hexagrams.length ? 'source-backed' : 'fallback grid'}</Tag>
      </div>
      <svg viewBox="0 0 260 260" style={{ width: '100%', maxHeight: 300, marginTop: 8 }}>
        <rect x="0" y="0" width="260" height="260" fill={t.bgHex} />
        <circle cx="130" cy="130" r="78" fill="none" stroke={t.lineHex} />
        <circle cx="130" cy="130" r="112" fill="none" stroke={t.lineHex} />
        {ticks.map(tick => (
          <line
            key={tick.i}
            x1={tick.x1}
            y1={tick.y1}
            x2={tick.x2}
            y2={tick.y2}
            stroke={tick.major ? t.amberHex : tick.loaded ? t.cyanHex : t.paperDimHex}
            strokeWidth={tick.major ? 2 : 1}
            opacity={tick.major ? 0.9 : 0.45}
          />
        ))}
        <text x="130" y="124" textAnchor="middle" fill={t.paperHex} fontFamily="JetBrains Mono" fontSize="24">64</text>
        <text x="130" y="145" textAnchor="middle" fill={t.paperDimHex} fontFamily="JetBrains Mono" fontSize="10">one-line schedule</text>
      </svg>
      <LedgerRows t={t} rows={[
        ['source', data && data.summary && data.summary.visual_payload],
        ['states', data && data.summary && data.summary.state_count],
        ['axes', data && data.summary && data.summary.axis_count],
        ['claim boundary', data && data.summary && data.summary.scope_note],
      ]} />
    </div>
  );
}

function CouplingTriangle({ t, coupled }) {
  const edges = (coupled && coupled.coupling_graph && coupled.coupling_graph.weighted_edges) || [];
  const pos = {
    carnot: [126, 54],
    szilard: [56, 218],
    iching_64: [226, 218],
  };
  const labels = {
    carnot: 'Carnot',
    szilard: 'Szilard',
    iching_64: 'Six-bit cycle',
  };
  return (
    <div style={{ border: `1px solid ${t.line}`, background: t.bg2, padding: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 10 }}>
        <Mono t={t} size={10} dim style={{ letterSpacing: 1.2 }}>COUPLING TOPOLOGY</Mono>
        <Tag t={t} tone={edges.length ? 'amber' : 'cyan'}>{edges.length ? `${edges.length} sourced edges` : 'not loaded'}</Tag>
      </div>
      <svg viewBox="0 0 282 270" style={{ width: '100%', maxHeight: 320, marginTop: 8 }}>
        <rect x="0" y="0" width="282" height="270" fill={t.bgHex} />
        {edges.map(edge => {
          const a = pos[edge.left] || [0, 0];
          const b = pos[edge.right] || [0, 0];
          const mx = (a[0] + b[0]) / 2;
          const my = (a[1] + b[1]) / 2;
          const width = Math.max(1.5, Math.min(6, Number(edge.score || 1) * 2));
          return (
            <g key={`${edge.left}-${edge.right}`}>
              <line x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={t.amberHex} strokeWidth={width} opacity="0.75" />
              <rect x={mx - 23} y={my - 11} width="46" height="20" fill={t.bg2Hex} stroke={t.lineHex} />
              <text x={mx} y={my + 4} textAnchor="middle" fill={t.paperHex} fontFamily="JetBrains Mono" fontSize="10">{edge.score}</text>
            </g>
          );
        })}
        {Object.entries(pos).map(([id, xy]) => (
          <g key={id}>
            <circle cx={xy[0]} cy={xy[1]} r="28" fill={t.bg3Hex} stroke={t.cyanHex} strokeWidth="1.5" />
            <text x={xy[0]} y={xy[1] + 4} textAnchor="middle" fill={t.paperHex} fontFamily="JetBrains Mono" fontSize="10">{labels[id]}</text>
          </g>
        ))}
      </svg>
      <LedgerRows t={t} rows={[
        ['nodes', coupled && coupled.coupling_graph && coupled.coupling_graph.nodes],
        ['edges', coupled && coupled.coupling_graph && coupled.coupling_graph.edges],
        ['xgi edges', coupled && coupled.coupling_graph && coupled.coupling_graph.xgi_edges],
        ['QIT promotion', coupled && coupled.summary && coupled.summary.qit_promotion_blocked ? 'blocked' : 'not loaded'],
      ]} />
    </div>
  );
}

function RosettaEntropyStack({ t, entropyTopology }) {
  const rows = (entropyTopology && entropyTopology.entropy_rows) || [];
  const maxEntropy = Math.max(1, ...rows.map(row => Number(row.entropy_family && row.entropy_family.max_entropy) || 0));
  return (
    <div style={{ border: `1px solid ${t.line}`, background: t.bg2, padding: 12 }}>
      <Mono t={t} size={10} dim style={{ letterSpacing: 1.2 }}>ENTROPY FAMILY SWEEP</Mono>
      <div style={{ display: 'grid', gap: 10, marginTop: 12 }}>
        {rows.map(row => {
          const shannon = Number(row.entropy_family && row.entropy_family.shannon) || 0;
          const purity = Number(row.entropy_family && row.entropy_family.purity) || 0;
          return (
            <div key={row.engine} style={{ border: `1px solid ${t.line}`, background: t.bg, padding: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
                <Mono t={t} size={11}>{row.engine}</Mono>
                <Tag t={t} tone={row.family_pass ? 'amber' : 'rose'}>{row.family_pass ? 'pass' : 'blocked'}</Tag>
              </div>
              <div style={{ height: 8, border: `1px solid ${t.line}`, marginTop: 8, background: t.bg2 }}>
                <div style={{ width: `${Math.max(2, Math.min(100, (shannon / maxEntropy) * 100))}%`, height: '100%', background: t.amberHex }} />
              </div>
              <LedgerRows t={t} rows={[
                ['support', row.support_size],
                ['shannon', shannon.toFixed(4)],
                ['purity', purity.toFixed(4)],
                ['trace checks', row.density_entropy_checks && row.density_entropy_checks.pass],
              ]} />
            </div>
          );
        })}
      </div>
    </div>
  );
}

function EngineLabCoveragePanel({ t, openRows, nextWork, successorCoverage, szilardConsolidation }) {
  const coverageRows = (successorCoverage && successorCoverage.rows) || [];
  const queueRows = (nextWork && nextWork.rows) || [];
  const openAuditRows = (openRows && openRows.rows) || [];
  const szilardRows = (szilardConsolidation && szilardConsolidation.rows) || [];
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 0.8fr) minmax(360px, 1.2fr)', gap: 12 }}>
      <div style={{ display: 'grid', gap: 10 }}>
        <div style={{ border: `1px solid ${t.rose}`, background: t.bg2, padding: 12 }}>
          <Mono t={t} size={10} style={{ lineHeight: 1.45 }}>
            Engine Lab contract: successor coverage means every current queue row is covered by a successor, consolidated recheck, or supersession lane. It does not make the source rows scientifically passing, does not admit QIT/GStack/axis claims, and does not promote a runtime engine.
          </Mono>
        </div>
        <StatusCard
          t={t}
          label="successor-layer coverage"
          value={`${(successorCoverage && successorCoverage.summary && successorCoverage.summary.active_uncovered_row_count) ?? 'unknown'} active uncovered`}
          tone={(successorCoverage && successorCoverage.summary && successorCoverage.summary.active_uncovered_row_count) === 0 ? 'amber' : 'rose'}
          sub={`${(successorCoverage && successorCoverage.summary && successorCoverage.summary.queue_row_count) || 0} queue rows; ${(successorCoverage && successorCoverage.summary && successorCoverage.summary.covered_by_successor_count) || 0} successor, ${(successorCoverage && successorCoverage.summary && successorCoverage.summary.covered_by_consolidated_closed_count) || 0} consolidated, ${(successorCoverage && successorCoverage.summary && successorCoverage.summary.covered_by_superseded_count) || 0} superseded`}
        />
        <StatusCard
          t={t}
          label="source layer"
          value={(successorCoverage && successorCoverage.summary && successorCoverage.summary.source_rows_preserved_negative) ? 'preserved negative' : 'check source rows'}
          tone={(successorCoverage && successorCoverage.summary && successorCoverage.summary.source_rows_preserved_negative) ? 'cyan' : 'rose'}
          sub="Original nonpassing rows stay negative; successor receipts do not rewrite them."
        />
        <StatusCard
          t={t}
          label="promotion gate"
          value={(successorCoverage && successorCoverage.summary && successorCoverage.summary.qit_or_axis_promotion_allowed) ? 'open' : 'closed'}
          tone={(successorCoverage && successorCoverage.summary && successorCoverage.summary.qit_or_axis_promotion_allowed) ? 'rose' : 'amber'}
          sub="No QIT, GStack, axis, or runtime-engine admission follows from this coverage panel."
        />
        <RosettaRow t={t} title="receipt freshness" status={(successorCoverage && successorCoverage.summary && successorCoverage.summary.schema_error_count) ? 'blocked' : 'checked'} rows={[
          ['generated at', successorCoverage && successorCoverage.generated_at],
          ['schema errors', successorCoverage && successorCoverage.summary && successorCoverage.summary.schema_error_count],
          ['open-row audit rows', openAuditRows.length],
          ['next-work queue rows', queueRows.length],
          ['Szilard consolidation rows', szilardRows.length],
        ]} />
        {szilardConsolidation && (
          <RosettaRow t={t} title="Szilard four-row consolidation" status={(szilardConsolidation.summary && szilardConsolidation.summary.all_pass) ? 'constraint-covered' : 'blocked'} rows={[
            ['source negatives', szilardConsolidation.summary && szilardConsolidation.summary.source_negative_count],
            ['passing successors', szilardConsolidation.summary && szilardConsolidation.summary.passing_successor_count],
            ['fresh receipts', szilardConsolidation.summary && `${szilardConsolidation.summary.fresh_source_count} source / ${szilardConsolidation.summary.fresh_successor_count} successor`],
            ['accepted constraints', szilardConsolidation.summary && szilardConsolidation.summary.accepted_constraint_count],
            ['blocked promotion edges', szilardConsolidation.summary && (szilardConsolidation.summary.blocked_promotion_edges || []).join(', ')],
          ]} />
        )}
      </div>
      <div style={{ display: 'grid', gap: 10 }}>
        {szilardRows.map(row => (
          <RosettaRow key={`szilard-${row.row_id}`} t={t} title={`Szilard: ${row.row_id}`} status={row.accepted ? 'successor constraint' : 'blocked'} rows={[
            ['survived', row.survived],
            ['failed/killed', row.failed_or_killed],
            ['constraint', row.coupling_constraint],
            ['source preserved negative', row.source_preserved_negative],
            ['receipt fresh', `${row.source_receipt_fresh} source / ${row.successor_receipt_fresh} successor`],
          ]} />
        ))}
        {coverageRows.map(row => (
          <RosettaRow key={row.row_id || row.schema_error} t={t} title={row.row_id || 'schema error'} status={row.covered ? 'successor-layer covered' : 'uncovered'} rows={[
            ['audit class', row.audit_class],
            ['lane', row.recommended_lane],
            ['passing successors', row.passing_successor_count],
            ['consolidated status', row.consolidated_admission_status],
            ['graveyard covered', row.graveyard_covered],
            ['source negative preserved', row.source_negative_preserved],
            ['schema error', row.schema_error],
          ]} />
        ))}
      </div>
    </div>
  );
}

function EngineRosettaWorkbench({ t, data }) {
  const registry = window.ROSETTA_LEGO_REGISTRY_DATA || null;
  const coupled = window.ROSETTA_LEGO_COUPLED_ARRAY_DATA || null;
  const coupledGraveyard = window.ROSETTA_LEGO_COUPLED_ARRAY_GRAVEYARD_DATA || null;
  const primeSidecar = window.PRIME_QIT_SIDECAR_DATA || null;
  const triadModes = window.ROSETTA_TRIAD_MODES_DATA || null;
  const entropyTopology = window.ROSETTA_TRIAD_ENTROPY_TOPOLOGY_DATA || null;
  const orderGraveyard = window.ROSETTA_TRIAD_ORDER_GRAVEYARD_DATA || null;
  const iching = window.SIX_BIT_GRAY_CODE_CYCLE_DATA || null;
  const engineLabOpenRows = window.ENGINE_LAB_OPEN_ROW_AUDIT_DATA || null;
  const engineLabNextWork = window.ENGINE_LAB_NEXT_WORK_QUEUE_DATA || null;
  const engineLabSuccessorCoverage = window.ENGINE_LAB_SUCCESSOR_COVERAGE_DATA || null;
  const szilardConsolidation = window.SZILARD_OPEN_ROW_CONSOLIDATION_DATA || null;
  const [mode, setMode] = React.useState('overview');

  const modes = [
    ['overview', 'Overview'],
    ['triad', 'Triad Modes'],
    ['entropy', 'Entropy'],
    ['topology', 'Topology'],
    ['registry', 'Lego Registry'],
    ['coupled', 'Coupled Graph'],
    ['density', 'Density'],
    ['negative', 'Failed Variants'],
    ['prime', 'Prime Sidecar'],
    ['engine-lab', 'Engine Lab'],
    ['boundaries', 'Boundaries'],
  ];

  const coupledEdges = (coupled && coupled.coupling_graph && coupled.coupling_graph.weighted_edges) || [];
  const registryRows = (registry && registry.registry_rows) || [];
  const negativeRows = [
    ...((coupledGraveyard && coupledGraveyard.variant_rows) || []).map(row => ({ family: 'coupled array', ...row })),
    ...((orderGraveyard && orderGraveyard.variant_rows) || []).map(row => ({ family: 'order gate', ...row })),
    ...((data && data.graveyard_rows) || []).map(row => ({ family: 'engine rosetta', ...row })),
  ];

  const renderOverview = () => (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1fr) minmax(320px, 1fr)', gap: 12 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 10 }}>
        <StatusCard t={t} label="payload" value={data && data.summary && data.summary.all_pass ? 'source-backed' : 'partial'} tone={data && data.summary && data.summary.all_pass ? 'amber' : 'cyan'} sub={data && data.summary && data.summary.visual_payload} />
        <StatusCard t={t} label="registry rows" value={registry && registry.summary && registry.summary.registry_row_count} tone="amber" sub="Carnot, Szilard, and 64-state symbolic rows stay separate." />
        <StatusCard t={t} label="allowed couplings" value={registry && registry.summary && registry.summary.allowed_coupling_count} tone="cyan" sub="Allowed by registry compatibility, not proof promotion." />
        <StatusCard t={t} label="blocked promotion" value={coupled && coupled.summary && coupled.summary.qit_promotion_blocked ? 'yes' : 'not loaded'} tone="rose" sub="QIT promotion remains blocked unless a canonical result admits it." />
        <StatusCard t={t} label="prime sidecar" value={primeSidecar && primeSidecar.summary && primeSidecar.summary.all_pass ? 'bounded' : 'not loaded'} tone="cyan" sub="Finite-N candidate-prior probe; no RH/PNT/QIT admission." />
      </div>
      <CouplingTriangle t={t} coupled={coupled} />
      <RosettaEntropyStack t={t} entropyTopology={entropyTopology} />
      <RosettaMiniWheel t={t} data={iching} />
      <div style={{ gridColumn: '1 / -1', border: `1px solid ${t.rose}`, background: t.bg2, padding: 12 }}>
        <Mono t={t} size={10} style={{ lineHeight: 1.45 }}>
          UI contract: this tab combines sourced mechanics, result metadata, and comparison surfaces. It does not create Carnot/Szilard/QIT proof claims, does not collapse state spaces, and does not promote axis slots.
        </Mono>
      </div>
    </div>
  );

  const renderRows = () => {
    if (mode === 'triad') {
      return ((triadModes && triadModes.mode_matrix) || []).map((row, i) => (
        <RosettaRow key={`${row.engine}-${row.mode}-${i}`} t={t} title={`${row.engine} / ${row.mode}`} status={row.pass} rows={[
          ['claim', row.claim],
          ['geometry', row.geometry],
          ['entropy readout', row.entropy_readout],
          ['states / operators / axes', `${row.state_count} / ${row.operator_count} / ${row.axis_count}`],
          ['boundary', row.boundary],
        ]} />
      ));
    }
    if (mode === 'entropy') {
      return ((entropyTopology && entropyTopology.entropy_rows) || []).map(row => (
        <RosettaRow key={row.engine} t={t} title={row.engine} status={row.family_pass ? 'pass' : 'blocked'} rows={[
          ['support size', row.support_size],
          ['shannon', row.entropy_family && Number(row.entropy_family.shannon).toFixed(6)],
          ['renyi 2', row.entropy_family && Number(row.entropy_family.renyi_2).toFixed(6)],
          ['min entropy', row.entropy_family && Number(row.entropy_family.min_entropy).toFixed(6)],
          ['purity', row.entropy_family && Number(row.entropy_family.purity).toFixed(6)],
          ['density checks', row.density_entropy_checks && row.density_entropy_checks.pass],
        ]} />
      ));
    }
    if (mode === 'topology') {
      return ((entropyTopology && entropyTopology.topology_rows) || []).map(row => (
        <RosettaRow key={row.engine} t={t} title={row.engine} status={row.topology_pass ? 'pass' : 'blocked'} rows={[
          ['nodes / edges', `${row.nodes} / ${row.edges}`],
          ['beta0 / beta1', `${row.beta0_laplacian} / ${row.beta1_cycle_rank}`],
          ['euler characteristic', row.euler_characteristic],
          ['spectral gap', typeof row.laplacian_spectral_gap === 'number' ? row.laplacian_spectral_gap.toFixed(6) : row.laplacian_spectral_gap],
          ['PyG nodes / edges', `${row.pyg_nodes} / ${row.pyg_edges}`],
          ['TopoNetX shape', row.toponetx_shape],
        ]} />
      ));
    }
    if (mode === 'registry') {
      return registryRows.map(row => (
        <RosettaRow key={row.row || row.name} t={t} title={row.row || row.name} status={row.source_all_pass ? 'pass' : 'blocked'} rows={[
          ['source receipt', row.source_receipt],
          ['lego ids', row.lego_ids],
          ['entropy families', row.entropy_families],
          ['topology', row.topology_signature],
          ['operators', row.operators && `${row.operators.count} / ${row.operators.readout}`],
          ['claim ceiling', row.claim_ceiling],
        ]} />
      ));
    }
    if (mode === 'coupled') {
      return coupledEdges.map(row => (
        <RosettaRow key={`${row.left}-${row.right}`} t={t} title={`${row.left} <-> ${row.right}`} status="allowed" rows={[
          ['coupling score', row.score],
          ['graph nodes', coupled && coupled.coupling_graph && coupled.coupling_graph.nodes],
          ['graph edges', coupled && coupled.coupling_graph && coupled.coupling_graph.edges],
          ['xgi hyperedges', coupled && coupled.coupling_graph && coupled.coupling_graph.xgi_edges],
        ]} />
      ));
    }
    if (mode === 'density') {
      const density = coupled && coupled.coupling_density;
      return [(
        <RosettaRow key="density" t={t} title="coupled density witness" status={density ? 'pass' : 'not loaded'} rows={[
          ['probabilities', density && density.probabilities],
          ['shannon entropy', density && density.shannon_entropy],
          ['scipy vn entropy', density && density.scipy_vn_entropy],
          ['qiskit trace', density && density.qiskit_trace],
          ['qutip trace', density && density.qutip_trace],
          ['torch gradient positive', density && density.torch_gradient_positive],
          ['sympy normalization', density && density.sympy_normalization_identity],
        ]} />
      )];
    }
    if (mode === 'negative') {
      return negativeRows.map((row, i) => (
        <RosettaRow key={`${row.family}-${row.variant || row.claim || i}`} t={t} title={`${row.family}: ${row.variant || row.claim || row.mutation || i}`} status={row.status || (row.survives ? 'survives' : 'blocked')} rows={[
          ['engine', row.engine],
          ['mutation', row.mutation],
          ['order', row.order],
          ['reason', row.reason],
          ['evidence', row.evidence],
          ['survives', row.survives_order_gate !== undefined ? row.survives_order_gate : row.survives],
        ]} />
      ));
    }
    if (mode === 'prime') {
      const evalRow = primeSidecar && primeSidecar.sidecar_evaluation;
      const gapStats = primeSidecar && primeSidecar.prime_gap_statistics;
      const baselines = (primeSidecar && primeSidecar.baselines) || {};
      return [
        <RosettaRow key="prime-sidecar" t={t} title="prime/QIT sidecar boundary" status={primeSidecar && primeSidecar.summary && primeSidecar.summary.all_pass ? 'sidecar pass' : 'not loaded'} rows={[
          ['N', primeSidecar && primeSidecar.parameters && primeSidecar.parameters.N],
          ['fixed states match primes', primeSidecar && primeSidecar.summary && primeSidecar.summary.fixed_states_match_primes],
          ['prime / composite count', primeSidecar && primeSidecar.summary && `${primeSidecar.summary.prime_count} / ${primeSidecar.summary.composite_count}`],
          ['baseline exact matches', primeSidecar && primeSidecar.summary && primeSidecar.summary.baseline_exact_match_count],
          ['claim ceiling', primeSidecar && primeSidecar.summary && primeSidecar.summary.claim_ceiling],
        ]} />,
        <RosettaRow key="prime-survivor" t={t} title="survivor/fixed-state measurement" status={evalRow && evalRow.exact_fixed_state_match ? 'pass' : 'blocked'} rows={[
          ['precision / recall', evalRow && `${Number(evalRow.precision).toFixed(3)} / ${Number(evalRow.recall).toFixed(3)}`],
          ['fixed state count', evalRow && evalRow.fixed_state_count],
          ['spectral gap proxy', evalRow && evalRow.spectral && evalRow.spectral.spectral_gap_proxy],
          ['unit eigenvalues', evalRow && evalRow.spectral && evalRow.spectral.unit_eigenvalue_count],
          ['fixed sample', evalRow && evalRow.fixed_state_sample],
        ]} />,
        <RosettaRow key="prime-gaps" t={t} title="gap statistics, not RH evidence" status="sidecar" rows={[
          ['gap count', gapStats && gapStats.count],
          ['mean gap', gapStats && gapStats.mean_gap],
          ['max gap', gapStats && gapStats.max_gap],
          ['spacing ratio', gapStats && gapStats.mean_spacing_ratio],
          ['references', gapStats && `Poisson ${gapStats.poisson_ratio_reference}, GUE ${gapStats.gue_ratio_reference}`],
        ]} />,
        ...Object.entries(baselines).map(([name, row]) => (
          <RosettaRow key={`baseline-${name}`} t={t} title={`baseline: ${name}`} status={row.exact_fixed_state_match ? 'overfit' : 'rejected'} rows={[
            ['fixed state count', row.fixed_state_count],
            ['precision / recall', `${Number(row.precision).toFixed(3)} / ${Number(row.recall).toFixed(3)}`],
            ['exact fixed-state match', row.exact_fixed_state_match],
            ['spectral gap proxy', row.spectral && row.spectral.spectral_gap_proxy],
            ['logm error', row.spectral && row.spectral.logm_error],
          ]} />
        )),
      ];
    }
    if (mode === 'engine-lab') {
      return [
        <EngineLabCoveragePanel
          key="engine-lab-coverage"
          t={t}
          openRows={engineLabOpenRows}
          nextWork={engineLabNextWork}
          successorCoverage={engineLabSuccessorCoverage}
          szilardConsolidation={szilardConsolidation}
        />,
      ];
    }
    return [
      <RosettaRow key="scope" t={t} title="source/fallback boundary" status={data && data.summary && data.summary.all_pass ? 'source-backed' : 'partial'} rows={[
        ['engine rosetta source', data && data.summary && data.summary.visual_payload],
        ['triad modes source', triadModes && triadModes.summary && triadModes.summary.visual_payload],
        ['entropy topology source', entropyTopology && entropyTopology.summary && entropyTopology.summary.visual_payload],
        ['order negative source', orderGraveyard && orderGraveyard.summary && orderGraveyard.summary.visual_payload],
        ['lego registry source', registry && registry.summary && registry.summary.visual_payload],
      ]} />,
      <RosettaRow key="not-claimed" t={t} title="not claimed" status="blocked" rows={((data && data.qit_analogue_map && data.qit_analogue_map.not_yet_claimed) || []).map((item, i) => [`not claimed ${i + 1}`, item])} />,
    ];
  };

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: 16, display: 'grid', gridTemplateColumns: 'minmax(560px, 1fr) 340px', gap: 14 }}>
      <section style={{ border: `1px solid ${t.line}`, background: t.bg }}>
        <div style={{ padding: 14, borderBottom: `1px solid ${t.line}`, display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 280 }}>
            <Mono t={t} size={10} dim style={{ letterSpacing: 1.4 }}>COMBINED ENGINE ROSETTA</Mono>
            <div style={{ marginTop: 5 }}><Mono t={t} size={18}>Carnot / Szilard / 64-state comparison workbench</Mono></div>
          </div>
          {modes.map(([id, label]) => (
            <button key={id} onClick={() => setMode(id)} style={engineButton(t, mode === id)}>{label}</button>
          ))}
        </div>
        <div style={{ padding: 14, display: 'grid', gap: 10 }}>
          {mode === 'overview' ? renderOverview() : renderRows()}
        </div>
      </section>

      <aside style={{ border: `1px solid ${t.line}`, background: t.bg2, padding: 14, display: 'flex', flexDirection: 'column', gap: 14 }}>
        <Tag t={t} tone={data && data.summary && data.summary.all_pass ? 'amber' : 'cyan'}>{data && data.summary && data.summary.all_pass ? 'source-backed' : 'partial'}</Tag>
        <Mono t={t} size={10} dim style={{ lineHeight: 1.45 }}>{data && data.summary && data.summary.visual_payload}</Mono>
        <div style={{ border: `1px solid ${t.rose}`, padding: 10, background: t.bg }}>
          <Mono t={t} size={10} style={{ lineHeight: 1.45 }}>{data && data.summary && data.summary.scope_note}</Mono>
        </div>

        <div>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.4 }}>LOADED SOURCES</Mono>
          <LedgerRows t={t} rows={[
            ['Carnot dual stack', !!window.CARNOT_DUAL_STACK_DATA],
            ['Szilard dual stack', !!window.SZILARD_DUAL_STACK_DATA],
            ['Engine Rosetta', !!window.ENGINE_ROSETTA_DATA],
            ['Six-bit cycle', !!window.SIX_BIT_GRAY_CODE_CYCLE_DATA],
            ['Triad modes', !!window.ROSETTA_TRIAD_MODES_DATA],
            ['Entropy topology', !!window.ROSETTA_TRIAD_ENTROPY_TOPOLOGY_DATA],
            ['Order variants', !!window.ROSETTA_TRIAD_ORDER_GRAVEYARD_DATA],
            ['Prime sidecar', !!window.PRIME_QIT_SIDECAR_DATA],
            ['Engine lab open rows', !!window.ENGINE_LAB_OPEN_ROW_AUDIT_DATA],
            ['Engine lab next work', !!window.ENGINE_LAB_NEXT_WORK_QUEUE_DATA],
            ['Engine lab successor coverage', !!window.ENGINE_LAB_SUCCESSOR_COVERAGE_DATA],
            ['Szilard consolidation', !!window.SZILARD_OPEN_ROW_CONSOLIDATION_DATA],
          ]} />
        </div>

        <div>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.4 }}>LEGO SCALING STATUS</Mono>
          <LedgerRows t={t} rows={[
            ['registry rows', registry && registry.summary && registry.summary.registry_row_count],
            ['allowed couplings', registry && registry.summary && registry.summary.allowed_coupling_count],
            ['coupled pairs', coupled && coupled.summary && coupled.summary.coupled_pair_count],
            ['qit promotion blocked', coupled && coupled.summary && coupled.summary.qit_promotion_blocked],
            ['negative variants killed', coupledGraveyard && coupledGraveyard.summary && coupledGraveyard.summary.killed_or_blocked_count],
            ['prime sidecar fixed match', primeSidecar && primeSidecar.summary && primeSidecar.summary.fixed_states_match_primes],
            ['engine lab active uncovered', engineLabSuccessorCoverage && engineLabSuccessorCoverage.summary && engineLabSuccessorCoverage.summary.active_uncovered_row_count],
            ['engine lab gate closed', engineLabSuccessorCoverage && engineLabSuccessorCoverage.summary ? !engineLabSuccessorCoverage.summary.qit_or_axis_promotion_allowed : null],
          ]} />
        </div>

        <div>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.4 }}>SHARED CANDIDATES</Mono>
          <LedgerRows t={t} rows={Object.entries((data && data.qit_analogue_map && data.qit_analogue_map.shared_candidates) || {})} />
        </div>
      </aside>
    </div>
  );
}

function RosettaPanel({ t }) {
  const engineRosetta = window.ENGINE_ROSETTA_DATA || {
    summary: {
      all_pass: false,
      visual_payload: 'cycle-invariant-correlation-data.js not loaded',
      scope_note: 'No engine Rosetta payload is loaded; this tab stays fail-closed instead of showing unrelated material.',
    },
    tier_correlations: [],
    triadic_qit_rows: [],
    degree_of_freedom_comparison: [],
    graveyard_rows: [],
    qit_analogue_map: { shared_candidates: {}, not_yet_claimed: ['engine Rosetta payload missing'] },
  };
  return <EngineRosettaWorkbench t={t} data={engineRosetta} />;
}

Object.assign(window, { RosettaPanel, EngineRosettaWorkbench });
