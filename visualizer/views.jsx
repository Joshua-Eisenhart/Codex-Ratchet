// Main visualizer views

function ResolutionLadder({ t, data, selected, onSelect }) {
  return (
    <div style={{ padding: '4px 0' }}>
      {data.resolutions.map((r) => {
        const active = selected === r.r;
        return (
          <div key={r.r}
            onClick={() => onSelect(r.r)}
            style={{
              display: 'grid',
              gridTemplateColumns: '28px 16px 1fr auto',
              alignItems: 'center',
              gap: 8,
              padding: '8px 14px',
              cursor: 'pointer',
              background: active ? t.bg3 : 'transparent',
              borderLeft: `2px solid ${active ? statusColor(t, r.status) : 'transparent'}`,
            }}>
            <Mono t={t} size={11} dim>R{r.r}</Mono>
            <StatusDot status={r.status} t={t} />
            <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
              <Mono t={t} size={12} style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.name}</Mono>
              <Mono t={t} size={10} dim style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.what}</Mono>
            </div>
            <Mono t={t} size={10} dim>{r.sims || '·'}</Mono>
          </div>
        );
      })}
    </div>
  );
}

function LanesStrip({ t, data }) {
  return (
    <div style={{ display: 'flex', borderTop: `1px solid ${t.line}` }}>
      {data.lanes.map((l, i) => (
        <div key={l.id} style={{
          flex: 1,
          padding: '10px 12px',
          borderRight: i < data.lanes.length - 1 ? `1px solid ${t.line}` : 'none',
          display: 'flex', flexDirection: 'column', gap: 4,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <StatusDot status={l.status} t={t} />
            <Mono t={t} size={11} style={{ textTransform: 'uppercase', letterSpacing: 1 }}>{l.name}</Mono>
          </div>
          <Mono t={t} size={10} dim>{l.subtitle}</Mono>
          <Mono t={t} size={10} style={{ color: t.paperDim, lineHeight: 1.4 }}>{l.note}</Mono>
          <Mono t={t} size={9} dim style={{ marginTop: 4 }}>{l.artifact}</Mono>
        </div>
      ))}
    </div>
  );
}

function ScheduleGrid64({ t, data, selected, setSelected }) {
  const rows = data.terrains;
  const cols = data.signedOps;
  const cell = 62;

  // Build {row,col} -> macro-stage lookup. Every cell is in exactly one stage
  // (32 microsteps per engine × 2 engines = 64 total; no empty cells).
  const stageByKey = React.useMemo(() => {
    const m = {};
    data.macroStages.forEach(s => {
      s.cols.forEach((c, i) => {
        m[`${s.row},${c}`] = { stage: s, isNamed: i === 0 };
      });
    });
    return m;
  }, [data]);

  // S-slot lookup (only starred naming-cells have atlas S-numbers).
  const slotByKey = React.useMemo(() => {
    const m = {};
    data.scheduleAtlas.forEach(a => { m[`${a.row},${a.col}`] = a.slot; });
    return m;
  }, [data]);

  return (
    <div style={{ padding: 20, display: 'inline-block' }}>
      <div style={{ paddingBottom: 10 }}>
        <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>§03 · ENGINE_64_SCHEDULE_ATLAS · 64 MICROSTEPS = 2 ENGINES × 8 MACRO-STAGES × 4 OPERATOR SLOTS</Mono>
        <div style={{ marginTop: 4, maxWidth: 820 }}>
          <Mono t={t} size={10} dim>
            each terrain row holds two macro-stages: one ↑-signed, one ↓-signed · each stage occupies 4 microsteps (its sign class) · ★ = Ax6-naming operator within the block
          </Mono>
        </div>
      </div>

      {/* column header */}
      <div style={{ display: 'grid', gridTemplateColumns: `76px repeat(${cols.length}, ${cell}px)` }}>
        <div />
        {cols.map(c => {
          const isUp = c.order === 'operator-first';
          return (
            <div key={c.id} style={{
              height: 46, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end',
              paddingBottom: 6, borderBottom: `1px solid ${t.line}`,
              background: isUp ? `${t.amber}08` : `${t.rose}08`,
            }}>
              <Mono t={t} size={11} style={{ letterSpacing: 0.6 }}>{c.id}</Mono>
              <Mono t={t} size={8} dim style={{ letterSpacing: 0.4 }}>{isUp ? 'UP' : 'DOWN'}</Mono>
            </div>
          );
        })}
      </div>

      {rows.map((r, ri) => {
        const engine = data.terrainEngine[ri];
        const flux = data.terrainFlux[ri];
        return (
          <div key={r} style={{ display: 'grid', gridTemplateColumns: `76px repeat(${cols.length}, ${cell}px)` }}>
            <div style={{
              height: cell, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', justifyContent: 'center',
              paddingRight: 8, borderRight: `1px solid ${t.line}`,
            }}>
              <Mono t={t} size={11}>{r}</Mono>
              <Mono t={t} size={8} dim style={{ letterSpacing: 0.4 }}>{engine} · {flux}</Mono>
            </div>

            {cols.map((c, ci) => {
              const key = `${ri},${ci}`;
              const entry = stageByKey[key];
              if (!entry) return <div key={ci} />;
              const { stage, isNamed } = entry;
              const slot = slotByKey[key]; // only defined on named cell
              const isSel = selected === key;

              const winning = stage.outcome === 'WIN' || stage.outcome === 'win';
              const majorCase = stage.outcome === 'WIN' || stage.outcome === 'LOSE';
              const stageColor = winning ? t.amber : t.rose;

              // Stage-wide background tint + a darker strip on the named cell.
              const bg = isSel ? t.bg3 : `${stageColor}${isNamed ? '28' : '12'}`;

              // Block boundary: thick border when the neighbor cell belongs to
              // a different macro-stage. Simpler heuristic: UP-block cells are
              // {0,2,4,6} and DOWN-block cells are {1,3,5,7}, so the boundary
              // is between ODD and EVEN columns' stages — which differ.
              const leftNeighbor = ci > 0 ? stageByKey[`${ri},${ci - 1}`] : null;
              const diffStageLeft = !leftNeighbor || leftNeighbor.stage !== stage;
              const rightNeighbor = ci < 7 ? stageByKey[`${ri},${ci + 1}`] : null;
              const diffStageRight = !rightNeighbor || rightNeighbor.stage !== stage;

              return (
                <div key={ci}
                  onClick={() => setSelected(isSel ? null : key)}
                  style={{
                    height: cell,
                    borderTop: `1px solid ${t.line}`,
                    borderBottom: `1px solid ${t.line}`,
                    borderLeft: `${diffStageLeft ? 2 : 1}px solid ${diffStageLeft ? stageColor : `${t.line}55`}`,
                    borderRight: `${diffStageRight ? 2 : 1}px solid ${diffStageRight ? stageColor : `${t.line}55`}`,
                    background: bg,
                    position: 'relative', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    outline: isSel ? `1px solid ${t.paper}` : 'none',
                  }}>
                  {/* S-slot number (top-left) — only on the naming cell */}
                  {slot && (
                    <div style={{
                      position: 'absolute', top: 3, left: 4,
                      fontFamily: 'JetBrains Mono, monospace', fontSize: 8,
                      color: t.paperDim, letterSpacing: 0.3,
                    }}>{slot}★</div>
                  )}

                  {/* Micro-step index (bottom-right) — every cell */}
                  <div style={{
                    position: 'absolute', bottom: 3, right: 5,
                    fontFamily: 'JetBrains Mono, monospace', fontSize: 8, color: t.paperFaint,
                  }}>{ri * 8 + ci + 1}</div>

                  {/* Named cell shows full token + outcome. Non-named cells
                      show a small marker + the operator id — they're the
                      OTHER 3 microsteps of the same macro-stage. */}
                  {isNamed ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                      <Mono t={t} size={11} style={{ color: stageColor, letterSpacing: 0.3, fontWeight: majorCase ? 600 : 400 }}>
                        {stage.token}
                      </Mono>
                      <Mono t={t} size={8} style={{
                        color: stageColor, letterSpacing: 0.5,
                        textTransform: majorCase ? 'uppercase' : 'lowercase',
                        fontWeight: majorCase ? 600 : 400,
                      }}>
                        {stage.outcome}
                      </Mono>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1, opacity: 0.55 }}>
                      <div style={{
                        width: 4, height: 4,
                        background: stageColor,
                        borderRadius: '50%',
                      }} />
                      <Mono t={t} size={8} style={{ color: stageColor, letterSpacing: 0.4 }}>
                        {c.id}
                      </Mono>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        );
      })}

      <div style={{ paddingTop: 16, display: 'flex', gap: 24, flexWrap: 'wrap', maxWidth: 860, lineHeight: 1.6 }}>
        <Legend t={t} status="survived" label="WIN · win (major · minor)" />
        <Legend t={t} status="killed" label="LOSE · lose (major · minor)" />
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{
            width: 10, height: 10, border: `2px solid ${t.paperDim}`,
            display: 'inline-block',
          }} />
          <Mono t={t} size={10} dim>thick edge = macro-stage boundary (4 microsteps inside)</Mono>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Mono t={t} size={10} dim>★ = Ax6-naming operator (16 of 64) · other 48 are the same stage's 3 remaining operator microsteps</Mono>
        </div>
      </div>
    </div>
  );
}

function Legend({ t, status, label }) {
  const color = statusColor(t, status);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{
        width: 10, height: 10,
        border: `1.5px solid ${color}`,
        background: status === 'survived' || status === 'killed' ? color : 'transparent',
        opacity: status === 'killed' ? 0.5 : 1,
        transform: 'rotate(45deg)',
      }} />
      <Mono t={t} size={10} dim>{label}</Mono>
    </div>
  );
}

function AxesSurface({ t, data }) {
  return (
    <div style={{ padding: 20 }}>
      <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>ACTIVE AXES · 0–6</Mono>
      <div style={{
        marginTop: 10,
        display: 'grid', gridTemplateColumns: 'auto auto 1fr auto auto',
        columnGap: 16, rowGap: 6,
        fontFamily: 'JetBrains Mono, monospace', fontSize: 11,
      }}>
        <Mono t={t} size={10} dim>ax</Mono>
        <Mono t={t} size={10} dim>status</Mono>
        <Mono t={t} size={10} dim>role · math</Mono>
        <Mono t={t} size={10} dim>grounding</Mono>
        <Mono t={t} size={10} dim />
        {data.axes.map(a => (
          <React.Fragment key={a.n}>
            <Mono t={t} size={12}>Ax{a.n}</Mono>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <StatusDot status={a.status} t={t} size={7} />
              <Mono t={t} size={10} dim>{a.status}</Mono>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <Mono t={t} size={11}>{a.role}</Mono>
              <Mono t={t} size={10} dim>{a.math}</Mono>
            </div>
            <Mono t={t} size={10} dim style={{ maxWidth: 280 }}>{a.grounding}</Mono>
            <div />
          </React.Fragment>
        ))}
      </div>

      <div style={{ height: 1, background: t.line, margin: '20px 0' }} />

      <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>CANDIDATE AXES · 7–12 · NOT ESTABLISHED</Mono>
      <div style={{
        marginTop: 10,
        display: 'grid', gridTemplateColumns: '1fr 1fr 2fr',
        columnGap: 16, rowGap: 6,
      }}>
        {data.candidateAxes.map(a => (
          <React.Fragment key={a.n}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 8, height: 8, border: `1.5px dashed ${t.cyan}`, transform: 'rotate(45deg)' }} />
              <Mono t={t} size={12}>Ax{a.n}</Mono>
            </div>
            <Mono t={t} size={11} dim>{a.domain}</Mono>
            <Mono t={t} size={10} dim>{a.basis}</Mono>
          </React.Fragment>
        ))}
      </div>

      <div style={{ height: 1, background: t.line, margin: '20px 0' }} />

      <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>4 INTRINSIC OPERATORS</Mono>
      <div style={{ marginTop: 10, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
        {data.operators.map(o => (
          <div key={o.id} style={{ border: `1px solid ${t.line}`, padding: 12 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <Mono t={t} size={18}>{o.id}</Mono>
              <Tag t={t} tone={o.kind === 'unitary' ? 'amber' : 'cyan'}>{o.kind}</Tag>
            </div>
            <Mono t={t} size={10} dim style={{ display: 'block', marginTop: 6 }}>{o.gen}</Mono>
            <Mono t={t} size={10} dim style={{ display: 'block' }}>family: {o.family}</Mono>
            <Mono t={t} size={10} style={{ color: t.paperDim, display: 'block', marginTop: 8, lineHeight: 1.4 }}>{o.effect}</Mono>
          </div>
        ))}
      </div>
    </div>
  );
}

function Graveyard({ t, data }) {
  const g = data.graveyard;
  const total = g.survived + g.killed + g.open;
  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: 'flex', gap: 40, alignItems: 'baseline', marginBottom: 20 }}>
        <div>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>SEEDED</Mono>
          <div><Mono t={t} size={28}>{g.seeded}</Mono></div>
        </div>
        <div>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>SURVIVED</Mono>
          <div><Mono t={t} size={28} style={{ color: t.amber }}>{g.survived}</Mono></div>
        </div>
        <div>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>KILLED</Mono>
          <div><Mono t={t} size={28} style={{ color: t.rose }}>{g.killed}</Mono></div>
        </div>
        <div>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>OPEN</Mono>
          <div><Mono t={t} size={28} style={{ color: t.cyan }}>{g.open}</Mono></div>
        </div>
      </div>

      {/* stacked bar */}
      <div style={{ height: 8, display: 'flex', border: `1px solid ${t.line}`, marginBottom: 6 }}>
        <div style={{ flex: g.survived, background: t.amber }} />
        <div style={{ flex: g.killed, background: t.rose, opacity: 0.6 }} />
        <div style={{ flex: g.open, background: t.cyan }} />
      </div>
      <Mono t={t} size={10} dim>ratio survived : {(g.survived / total * 100).toFixed(0)}%  ·  graveyard-first policy</Mono>

      <div style={{ height: 1, background: t.line, margin: '20px 0' }} />

      <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>SAMPLE · 12 OF {g.seeded}</Mono>
      <div style={{ marginTop: 10 }}>
        {g.sample.map((s, i) => (
          <div key={i} style={{
            display: 'grid', gridTemplateColumns: '14px 180px 60px 1fr',
            gap: 12, padding: '6px 0',
            borderBottom: i < g.sample.length - 1 ? `1px solid ${t.line}` : 'none',
            alignItems: 'center',
          }}>
            <StatusDot status={s.outcome} t={t} />
            <Mono t={t} size={11}>{s.id}</Mono>
            <Mono t={t} size={10} dim>{s.at}</Mono>
            <Mono t={t} size={10} dim style={{ lineHeight: 1.3 }}>{s.reason}</Mono>
          </div>
        ))}
      </div>
    </div>
  );
}

function EventSpine({ t, data, onPick }) {
  return (
    <div style={{ padding: '8px 20px 20px' }}>
      <div style={{
        display: 'grid', gridTemplateColumns: '120px 50px 38px 14px 1fr auto',
        gap: 10, padding: '8px 0',
        borderBottom: `1px solid ${t.line}`,
      }}>
        <Mono t={t} size={10} dim>timestamp</Mono>
        <Mono t={t} size={10} dim>lane</Mono>
        <Mono t={t} size={10} dim>boot</Mono>
        <div />
        <Mono t={t} size={10} dim>event</Mono>
        <Mono t={t} size={10} dim>artifact</Mono>
      </div>
      {data.events.map((e, i) => (
        <div key={i}
          onClick={() => onPick && onPick(e)}
          style={{
            display: 'grid', gridTemplateColumns: '120px 50px 38px 14px 1fr auto',
            gap: 10, padding: '6px 0',
            borderBottom: `1px solid ${t.line}`,
            alignItems: 'center', cursor: 'pointer',
          }}>
          <Mono t={t} size={10} dim>{e.t}</Mono>
          <Mono t={t} size={10}>{e.lane}</Mono>
          <Tag t={t} tone={e.boot === 'B' ? 'rose' : e.boot === 'A1' ? 'cyan' : e.boot === 'A2' ? 'amber' : 'paperDim'}>{e.boot}</Tag>
          <StatusDot status={e.status} t={t} />
          <Mono t={t} size={11} style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{e.label}</Mono>
          <Mono t={t} size={9} dim style={{ whiteSpace: 'nowrap' }}>{e.path}</Mono>
        </div>
      ))}
    </div>
  );
}

function BootsPanel({ t, data }) {
  return (
    <div style={{ padding: 20 }}>
      <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>BOOT TERMINALS · CONTAMINATION-ISOLATED</Mono>
      <div style={{ marginTop: 14, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        {data.boots.map(b => (
          <div key={b.id} style={{ border: `1px solid ${t.line}`, padding: 12 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
              <Mono t={t} size={20}>{b.id}</Mono>
              <Mono t={t} size={11} dim>{b.name}</Mono>
              <div style={{ flex: 1 }} />
              <Tag t={t} tone={b.color === 'rose' ? 'rose' : b.color === 'amber' ? 'amber' : 'cyan'}>{b.runner}</Tag>
            </div>
            <Mono t={t} size={11} style={{ display: 'block', marginTop: 10, lineHeight: 1.4, color: t.paperDim }}>{b.role}</Mono>
            <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 3 }}>
              <div style={{ display: 'flex', gap: 8 }}>
                <Mono t={t} size={10} style={{ color: t.amber }}>+</Mono>
                <Mono t={t} size={10} dim>{b.canWrite}</Mono>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <Mono t={t} size={10} style={{ color: t.rose }}>−</Mono>
                <Mono t={t} size={10} dim>{b.canNotWrite}</Mono>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ height: 1, background: t.line, margin: '20px 0' }} />

      <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>ENTROPY TIERS · FUEL CLASSIFICATION</Mono>
      <div style={{ marginTop: 10 }}>
        {data.entropyTiers.map(e => (
          <div key={e.e} style={{
            display: 'grid', gridTemplateColumns: '40px 60px 1fr 1fr',
            gap: 12, padding: '6px 0',
            borderBottom: `1px solid ${t.line}`, alignItems: 'center',
          }}>
            <Mono t={t} size={13}>E{e.e}</Mono>
            <Mono t={t} size={10} dim>{e.label}</Mono>
            <Mono t={t} size={11}>{e.src}</Mono>
            <Mono t={t} size={10} dim>{e.owner}</Mono>
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, {
  ResolutionLadder, LanesStrip, ScheduleGrid64, AxesSurface,
  Graveyard, EventSpine, BootsPanel,
});
