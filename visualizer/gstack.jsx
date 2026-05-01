// G-Stack view — three modes for inspecting the geometry stack.
//
// DISCIPLINE (from user):
//   - M(C) is primary; all geometry shells are illustrative CHARTS on M(C).
//   - G-tower is CANDIDATE math, not canon. It renders dashed/hollow.
//   - A stack is a RATCHET only if A∘B ≠ B∘A. Commuting couplings are decorative.
//   - No "verified/confirmed/PASS" — only survived / killed / open / not_yet_tested.
//   - Legos render at their real status; blocked legos look blocked.

// ============================================================================
// Small shared helpers
// ============================================================================

const GS_MODES = [
  { id: 'isolated',   label: 'Isolated',    hint: 'each shell alone · shell-local sims' },
  { id: 'coupled',    label: 'Coupled',     hint: 'pairwise · non-commutativity = ratchet' },
  { id: 'integrated', label: 'Integrated',  hint: 'all shells on M(C) · legos below' },
];

function roleColor(t, role) {
  return role === 'canon' ? t.amber : role === 'candidate' ? t.violet : t.paperDim;
}

function StatusChip({ t, status, size = 10 }) {
  const map = {
    covered: { tone: 'amber', label: 'covered' },
    doctrinal: { tone: 'cyan', label: 'doctrinal' },
    partial: { tone: 'cyan', label: 'partial' },
    needs_deeper_lego_work: { tone: 'rose', label: 'needs deeper' },
    blocked: { tone: 'rose', label: 'blocked' },
    open: { tone: 'rose', label: 'open' },
    survived: { tone: 'amber', label: 'survived' },
    derived: { tone: 'paperDim', label: 'derived' },
    not_yet_tested: { tone: 'paperFaint', label: 'not tested' },
  };
  const m = map[status] || { tone: 'paperDim', label: status };
  return <Tag t={t} tone={m.tone}>{m.label}</Tag>;
}

// Dashed square for candidates, solid diamond for canon.
function RoleGlyph({ t, role, size = 10 }) {
  const c = roleColor(t, role);
  if (role === 'candidate') {
    return (
      <span style={{
        display: 'inline-block', width: size, height: size,
        border: `1.5px dashed ${c}`,
        transform: 'rotate(45deg)',
        flexShrink: 0,
      }} />
    );
  }
  return (
    <span style={{
      display: 'inline-block', width: size, height: size,
      background: c,
      transform: 'rotate(45deg)',
      flexShrink: 0,
    }} />
  );
}

// ============================================================================
// Mode header (shared)
// ============================================================================

function GStackModeTabs({ t, active, onChange }) {
  return (
    <div style={{
      display: 'flex', gap: 0,
      borderBottom: `1px solid ${t.line}`,
      background: t.bg,
    }}>
      {GS_MODES.map(m => {
        const isActive = m.id === active;
        return (
          <div key={m.id} onClick={() => onChange(m.id)}
            style={{
              padding: '9px 16px', cursor: 'pointer',
              borderRight: `1px solid ${t.line}`,
              background: isActive ? t.bg2 : 'transparent',
              borderBottom: isActive ? `2px solid ${t.amber}` : '2px solid transparent',
              marginBottom: -1,
              display: 'flex', alignItems: 'baseline', gap: 10,
            }}>
            <Mono t={t} size={11} dim={!isActive} style={{ letterSpacing: 1, textTransform: 'uppercase' }}>
              {m.label}
            </Mono>
            <Mono t={t} size={9} dim>{m.hint}</Mono>
          </div>
        );
      })}
      <div style={{ flex: 1, borderBottom: '2px solid transparent', marginBottom: -1 }} />
    </div>
  );
}

// Persistent doctrine watermark — present in every mode.
function DoctrineBar({ t }) {
  return (
    <div style={{
      padding: '7px 16px',
      borderBottom: `1px solid ${t.line}`,
      background: t.bg,
      display: 'flex', gap: 14, alignItems: 'center', flexWrap: 'wrap',
    }}>
      <Mono t={t} size={9} dim style={{ letterSpacing: 1.5 }}>DOCTRINE</Mono>
      <Mono t={t} size={10}>M(C) primary</Mono>
      <Mono t={t} size={9} dim>·</Mono>
      <Mono t={t} size={10}>shells = charts on M(C)</Mono>
      <Mono t={t} size={9} dim>·</Mono>
      <Mono t={t} size={10}>ratchet ⇔ A∘B ≠ B∘A</Mono>
      <Mono t={t} size={9} dim>·</Mono>
      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
        <RoleGlyph t={t} role="canon" />
        <Mono t={t} size={10} dim>canon</Mono>
      </div>
      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
        <RoleGlyph t={t} role="candidate" />
        <Mono t={t} size={10} dim>candidate (not canon)</Mono>
      </div>
    </div>
  );
}

// ============================================================================
// MODE 1 · ISOLATED — each layer as its own card, stacked vertically.
// Emphasis: shell-local sims, "what lives here alone".
// ============================================================================

function IsolatedView({ t, gs, selectedLayer, setSelectedLayer }) {
  return (
    <div style={{ padding: 16, display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 12 }}>
      {gs.layers.map(layer => (
        <IsolatedLayerCard key={layer.id} t={t} layer={layer}
          selected={selectedLayer === layer.id}
          onSelect={() => setSelectedLayer(layer.id)} />
      ))}
    </div>
  );
}

function IsolatedLayerCard({ t, layer, selected, onSelect }) {
  const isCandidate = layer.role === 'candidate';
  const accent = roleColor(t, layer.role);
  return (
    <div onClick={onSelect} style={{
      border: `1px ${isCandidate ? 'dashed' : 'solid'} ${selected ? accent : t.line}`,
      background: t.bg2,
      padding: 14,
      cursor: 'pointer',
      display: 'flex', flexDirection: 'column', gap: 10,
      position: 'relative',
    }}>
      {/* header */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
        <RoleGlyph t={t} role={layer.role} />
        <Mono t={t} size={16}>{layer.name}</Mono>
        <Mono t={t} size={10} dim>{layer.subtitle}</Mono>
        <div style={{ flex: 1 }} />
        <StatusChip t={t} status={layer.status} />
      </div>

      {/* iconographic representation */}
      <LayerIcon t={t} layer={layer} />

      {/* description */}
      <Mono t={t} size={10} dim style={{ lineHeight: 1.5 }}>{layer.description}</Mono>

      {/* witness */}
      <div style={{
        borderLeft: `2px solid ${accent}`, paddingLeft: 8,
        background: t.bg, padding: '6px 10px',
      }}>
        <Mono t={t} size={9} dim style={{ letterSpacing: 1.3 }}>ANCHOR</Mono>
        <Mono t={t} size={10} style={{ display: 'block', marginTop: 3, lineHeight: 1.4 }}>
          {layer.witness}
        </Mono>
      </div>

      {isCandidate && (
        <Mono t={t} size={9} dim style={{
          position: 'absolute', top: 10, right: 10,
          letterSpacing: 1.5, color: t.violet,
        }}>CANDIDATE</Mono>
      )}
    </div>
  );
}

// Mini iconographic renderer for each layer — done in SVG.
function LayerIcon({ t, layer }) {
  const accent = roleColor(t, layer.role);
  const dim = t.paperFaint;
  const line = t.line;
  const W = 300, H = 90;

  switch (layer.kind) {
    case 'surface': // M(C) — a jagged surface
      return (
        <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ background: t.bg, border: `1px solid ${line}` }}>
          <defs>
            <pattern id="mcgrid" width="12" height="12" patternUnits="userSpaceOnUse">
              <path d="M 12 0 L 0 0 0 12" fill="none" stroke={line} strokeWidth="0.5"/>
            </pattern>
          </defs>
          <rect width={W} height={H} fill="url(#mcgrid)"/>
          <path d={`M 0 ${H*0.7} C 40 ${H*0.3} 80 ${H*0.85} 140 ${H*0.5} S 240 ${H*0.25} ${W} ${H*0.6}`}
                fill="none" stroke={accent} strokeWidth="1.5"/>
          <path d={`M 0 ${H*0.7} C 40 ${H*0.3} 80 ${H*0.85} 140 ${H*0.5} S 240 ${H*0.25} ${W} ${H*0.6} L ${W} ${H} L 0 ${H} Z`}
                fill={accent} opacity="0.08"/>
          {[0, 60, 120, 180, 240].map((x, i) => (
            <circle key={i} cx={x + 20} cy={H*0.5 + Math.sin(i*1.3)*15} r="1.5" fill={accent}/>
          ))}
          <text x={W-6} y={H-6} fontSize="9" fill={dim} textAnchor="end" fontFamily="JetBrains Mono">M(C) · admissibility surface</text>
        </svg>
      );

    case 'sphere3': // S³ — a sphere with a great circle
      return (
        <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ background: t.bg, border: `1px solid ${line}` }}>
          <circle cx={W/2} cy={H/2} r={H/2 - 10} fill="none" stroke={accent} strokeWidth="1.2"/>
          <ellipse cx={W/2} cy={H/2} rx={H/2 - 10} ry={10} fill="none" stroke={accent} strokeWidth="0.8" opacity="0.6"/>
          <ellipse cx={W/2} cy={H/2} rx={10} ry={H/2 - 10} fill="none" stroke={accent} strokeWidth="0.8" opacity="0.6"/>
          <text x={W/2 + H/2} y={H/2 - 20} fontSize="9" fill={dim} fontFamily="JetBrains Mono">S³ ≅ SU(2)</text>
          <text x={W/2 + H/2} y={H/2 - 8} fontSize="9" fill={dim} fontFamily="JetBrains Mono">unit quaternions</text>
          <text x={W/2 + H/2} y={H/2 + 4} fontSize="9" fill={dim} fontFamily="JetBrains Mono">Hopf total space</text>
        </svg>
      );

    case 'hopf': // S¹ → S³ → S² — bundle diagram
      return (
        <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ background: t.bg, border: `1px solid ${line}` }}>
          {/* total space S³ */}
          <circle cx={W*0.2} cy={H/2} r={H/2 - 14} fill="none" stroke={accent} strokeWidth="1.2"/>
          <text x={W*0.2} y={H - 4} fontSize="8" fill={dim} fontFamily="JetBrains Mono" textAnchor="middle">S³</text>
          {/* projection arrow */}
          <line x1={W*0.38} y1={H/2} x2={W*0.58} y2={H/2} stroke={accent} strokeWidth="1"/>
          <polygon points={`${W*0.58},${H/2} ${W*0.55},${H/2-3} ${W*0.55},${H/2+3}`} fill={accent}/>
          <text x={W*0.48} y={H/2 - 6} fontSize="9" fill={dim} fontFamily="JetBrains Mono" textAnchor="middle">π</text>
          {/* base S² */}
          <circle cx={W*0.75} cy={H/2} r={H/2 - 14} fill="none" stroke={accent} strokeWidth="1.2"/>
          <ellipse cx={W*0.75} cy={H/2} rx={H/2 - 14} ry={7} fill="none" stroke={accent} strokeWidth="0.8" opacity="0.5"/>
          <text x={W*0.75} y={H - 4} fontSize="8" fill={dim} fontFamily="JetBrains Mono" textAnchor="middle">S² = Bloch</text>
          {/* fiber label */}
          <text x={W*0.2} y={10} fontSize="8" fill={dim} fontFamily="JetBrains Mono" textAnchor="middle">fiber S¹ · c₁=1</text>
        </svg>
      );

    case 'toriFoliation':
      return (
        <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ background: t.bg, border: `1px solid ${line}` }}>
          {[0.15, 0.25, 0.35, 0.45].map((r, i) => (
            <ellipse key={i} cx={W/2} cy={H/2} rx={W*r} ry={H*r*0.5}
              fill="none" stroke={accent} strokeWidth={i === 1 ? 1.5 : 0.7}
              opacity={i === 1 ? 1 : 0.5} />
          ))}
          <text x={W*0.5 + W*0.2} y={H/2 + 4} fontSize="9" fill={accent} fontFamily="JetBrains Mono">η=π/4</text>
          <text x={10} y={12} fontSize="8" fill={dim} fontFamily="JetBrains Mono">Clifford torus foliation · (1,1)-curves</text>
        </svg>
      );

    case 'weyl':
      return (
        <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ background: t.bg, border: `1px solid ${line}` }}>
          {/* left chirality */}
          <circle cx={W*0.25} cy={H/2} r={H/2 - 16} fill="none" stroke={accent} strokeDasharray="3 2" strokeWidth="1.2"/>
          <text x={W*0.25} y={H/2 + 4} fontSize="11" fill={accent} fontFamily="JetBrains Mono" textAnchor="middle">ψ_L</text>
          <text x={W*0.25} y={H - 6} fontSize="8" fill={dim} fontFamily="JetBrains Mono" textAnchor="middle">P_L = (1−γ⁵)/2</text>
          {/* right chirality */}
          <circle cx={W*0.75} cy={H/2} r={H/2 - 16} fill="none" stroke={accent} strokeDasharray="3 2" strokeWidth="1.2"/>
          <text x={W*0.75} y={H/2 + 4} fontSize="11" fill={accent} fontFamily="JetBrains Mono" textAnchor="middle">ψ_R</text>
          <text x={W*0.75} y={H - 6} fontSize="8" fill={dim} fontFamily="JetBrains Mono" textAnchor="middle">P_R = (1+γ⁵)/2</text>
          {/* parity exchange */}
          <path d={`M ${W*0.40} ${H/2 - 6} Q ${W/2} ${H/2 - 22} ${W*0.60} ${H/2 - 6}`} fill="none" stroke={accent} strokeWidth="0.8"/>
          <path d={`M ${W*0.40} ${H/2 + 6} Q ${W/2} ${H/2 + 22} ${W*0.60} ${H/2 + 6}`} fill="none" stroke={accent} strokeWidth="0.8"/>
          <text x={W/2} y={H/2 + 3} fontSize="8" fill={dim} fontFamily="JetBrains Mono" textAnchor="middle">P</text>
        </svg>
      );

    case 'gtower':
      const steps = ['GL', 'O', 'SO', 'U', 'SU', 'Sp'];
      return (
        <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ background: t.bg, border: `1px solid ${line}` }}>
          {steps.map((s, i) => {
            const x = 20 + i * ((W - 40) / (steps.length - 1));
            const y = H/2;
            return (
              <g key={s}>
                <rect x={x - 14} y={y - 10} width={28} height={20}
                  fill="none" stroke={accent} strokeDasharray="3 2" strokeWidth="1.2"/>
                <text x={x} y={y + 4} fontSize="10" fill={accent} fontFamily="JetBrains Mono" textAnchor="middle">{s}</text>
                {i < steps.length - 1 && (
                  <>
                    <line x1={x + 14} y1={y} x2={x + (W - 40) / (steps.length - 1) - 14} y2={y}
                      stroke={accent} strokeWidth="0.8" strokeDasharray="2 2"/>
                    <polygon points={`${x + (W - 40) / (steps.length - 1) - 14},${y} ${x + (W - 40) / (steps.length - 1) - 18},${y - 3} ${x + (W - 40) / (steps.length - 1) - 18},${y + 3}`} fill={accent}/>
                  </>
                )}
              </g>
            );
          })}
          <text x={W/2} y={H - 4} fontSize="8" fill={dim} fontFamily="JetBrains Mono" textAnchor="middle">5/6 reductions rigid · G₂ exceptional open · CANDIDATE</text>
        </svg>
      );

    case 'holonomy':
      return (
        <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ background: t.bg, border: `1px solid ${line}` }}>
          <circle cx={W/2} cy={H/2} r={H/2 - 16} fill="none" stroke={accent} strokeWidth="1.2" strokeDasharray="3 2"/>
          {/* loop with solid angle */}
          <path d={`M ${W/2} ${H/2 - 25} Q ${W/2 + 35} ${H/2 - 15} ${W/2 + 30} ${H/2 + 10} Q ${W/2 - 10} ${H/2 + 25} ${W/2 - 30} ${H/2} Q ${W/2 - 20} ${H/2 - 20} ${W/2} ${H/2 - 25} Z`}
                fill={accent} opacity="0.15" stroke={accent} strokeWidth="1"/>
          <text x={W/2 + H/2} y={H/2} fontSize="9" fill={dim} fontFamily="JetBrains Mono">γ = −Ω/2</text>
          <text x={W/2 + H/2} y={H/2 + 12} fontSize="9" fill={dim} fontFamily="JetBrains Mono">Berry phase</text>
        </svg>
      );

    case 'connes':
      return (
        <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ background: t.bg, border: `1px solid ${line}` }}>
          <circle cx={W*0.3} cy={H/2} r="4" fill={accent}/>
          <text x={W*0.3} y={H/2 - 10} fontSize="9" fill={accent} fontFamily="JetBrains Mono" textAnchor="middle">φ₁</text>
          <circle cx={W*0.7} cy={H/2} r="4" fill={accent}/>
          <text x={W*0.7} y={H/2 - 10} fontSize="9" fill={accent} fontFamily="JetBrains Mono" textAnchor="middle">φ₂</text>
          <path d={`M ${W*0.3} ${H/2} Q ${W/2} ${H/2 + 20} ${W*0.7} ${H/2}`} fill="none" stroke={accent} strokeDasharray="3 2"/>
          <text x={W/2} y={H/2 + 30} fontSize="9" fill={dim} fontFamily="JetBrains Mono" textAnchor="middle">d = sup{"{"}|φ₁(a)−φ₂(a)| : ‖[D,a]‖≤1{"}"}</text>
        </svg>
      );

    default:
      return <div style={{ height: 60, border: `1px dashed ${line}`, background: t.bg }} />;
  }
}

// ============================================================================
// MODE 2 · COUPLED — pairwise non-commutativity matrix.
// X axis: layer A; Y axis: layer B; cell: coupling(A,B) type + status.
// A RATCHET is visualized as a solid-filled cell; decorative = hollow; open = dashed.
// ============================================================================

function CoupledView({ t, gs, selectedCoupling, setSelectedCoupling }) {
  // only show non-M(C) layers in the matrix — M(C) admissibility is its own row below.
  const layers = gs.layers.filter(l => l.id !== 'MC');

  // map from `${a}|${b}` → coupling (symmetric; also store reverse)
  const byPair = {};
  gs.couplings.forEach(c => {
    if (c.a === 'MC' || c.b === '*') return; // admissibility row handled separately
    byPair[`${c.a}|${c.b}`] = c;
    byPair[`${c.b}|${c.a}`] = c;
  });

  const mcCoupling = gs.couplings.find(c => c.id === 'MC_ALL');

  return (
    <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 14, minHeight: 0 }}>
      {/* legend */}
      <div style={{
        display: 'flex', gap: 18, flexWrap: 'wrap',
        padding: 10, border: `1px solid ${t.line}`, background: t.bg2,
      }}>
        <CoupleLegend t={t} type="noncomm" status="survived" label="non-comm · survived (ratchet)" />
        <CoupleLegend t={t} type="noncomm" status="open" label="non-comm · open (missing sim)" />
        <CoupleLegend t={t} type="derived" status="survived" label="derived · by construction" />
        <CoupleLegend t={t} type="rosetta" status="open" label="Rosetta · predicted agreement" />
        <CoupleLegend t={t} type="commuting" status="survived" label="commuting (decorative)" />
      </div>

      {/* the matrix */}
      <div style={{ overflow: 'auto', border: `1px solid ${t.line}`, background: t.bg2 }}>
        <table style={{ borderCollapse: 'collapse', width: '100%', tableLayout: 'fixed' }}>
          <thead>
            <tr>
              <th style={{ padding: 8, borderRight: `1px solid ${t.line}`, borderBottom: `1px solid ${t.line}`, background: t.bg, width: 90 }}>
                <Mono t={t} size={9} dim>B ↓ / A →</Mono>
              </th>
              {layers.map(a => (
                <th key={a.id} style={{
                  padding: 8, borderLeft: `1px solid ${t.line}`, borderBottom: `1px solid ${t.line}`,
                  background: t.bg,
                  textAlign: 'center',
                }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                    <RoleGlyph t={t} role={a.role} />
                    <Mono t={t} size={10}>{a.name}</Mono>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {layers.map(b => (
              <tr key={b.id}>
                <td style={{
                  padding: 8, borderRight: `1px solid ${t.line}`, borderTop: `1px solid ${t.line}`,
                  background: t.bg,
                }}>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    <RoleGlyph t={t} role={b.role} />
                    <Mono t={t} size={10}>{b.name}</Mono>
                  </div>
                </td>
                {layers.map(a => {
                  if (a.id === b.id) {
                    return (
                      <td key={a.id} style={{
                        borderLeft: `1px solid ${t.line}`, borderTop: `1px solid ${t.line}`,
                        background: t.bg3, padding: 0, height: 64,
                      }}>
                        <div style={{ width: '100%', height: '100%',
                          background: `repeating-linear-gradient(45deg, transparent 0 4px, ${t.line} 4px 5px)`,
                        }} />
                      </td>
                    );
                  }
                  const c = byPair[`${a.id}|${b.id}`];
                  return (
                    <CoupleCell key={a.id} t={t} coupling={c} selected={c && selectedCoupling === c.id}
                      onSelect={() => c && setSelectedCoupling(c.id)} />
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* M(C) admissibility row — every layer must chart points ON M(C) */}
      <div style={{ border: `1px solid ${t.line}`, background: t.bg2 }}>
        <div style={{
          padding: '8px 12px', borderBottom: `1px solid ${t.line}`,
          display: 'flex', alignItems: 'baseline', gap: 10,
        }}>
          <RoleGlyph t={t} role="canon" />
          <Mono t={t} size={12}>M(C) ⊗ every layer</Mono>
          <Mono t={t} size={10} dim>admissibility · fail-closed</Mono>
          <div style={{ flex: 1 }} />
          <StatusChip t={t} status={mcCoupling.status} />
        </div>
        <div style={{ padding: 10 }}>
          <Mono t={t} size={10} dim style={{ lineHeight: 1.5 }}>{mcCoupling.claim}</Mono>
          <Mono t={t} size={9} dim style={{ display: 'block', marginTop: 6 }}>
            evidence: {mcCoupling.evidence}
          </Mono>
        </div>
      </div>

      {/* selected coupling detail */}
      {selectedCoupling && (() => {
        const c = gs.couplings.find(x => x.id === selectedCoupling);
        if (!c) return null;
        const a = gs.layers.find(l => l.id === c.a);
        const b = gs.layers.find(l => l.id === c.b);
        return (
          <div style={{ border: `1px solid ${t[couplingTone(c.type, c.status)]}`, background: t.bg2, padding: 14 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 8 }}>
              <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>COUPLING</Mono>
              <Mono t={t} size={14}>{a.name} ∘ {b.name}</Mono>
              <Tag t={t} tone={couplingTone(c.type, c.status)}>{c.type}</Tag>
              <StatusChip t={t} status={c.status} />
            </div>
            <Mono t={t} size={11} dim style={{ lineHeight: 1.5 }}>{c.claim}</Mono>
            <div style={{ marginTop: 10, padding: 8, background: t.bg, border: `1px solid ${t.line}` }}>
              <Mono t={t} size={9} dim style={{ letterSpacing: 1.3 }}>EVIDENCE</Mono>
              <Mono t={t} size={10} style={{ display: 'block', marginTop: 3 }}>{c.evidence}</Mono>
            </div>
          </div>
        );
      })()}
    </div>
  );
}

function couplingTone(type, status) {
  if (status === 'open') return 'rose';
  if (type === 'noncomm') return 'amber';  // the ratchet
  if (type === 'rosetta') return 'violet';
  if (type === 'admissibility') return 'cyan';
  if (type === 'derived') return 'paperDim';
  return 'paperDim';
}

function CoupleLegend({ t, type, status, label }) {
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      <CoupleMark t={t} type={type} status={status} size={18} />
      <Mono t={t} size={10} dim>{label}</Mono>
    </div>
  );
}

function CoupleMark({ t, type, status, size = 18 }) {
  const tone = couplingTone(type, status);
  const c = t[tone];
  if (status === 'open') {
    return <div style={{ width: size, height: size, border: `1.5px dashed ${c}` }}/>;
  }
  if (type === 'noncomm') {
    return <div style={{ width: size, height: size, background: c }}/>;
  }
  if (type === 'rosetta') {
    return <div style={{ width: size, height: size, border: `1.5px solid ${c}`,
      background: `repeating-linear-gradient(45deg, ${c} 0 2px, transparent 2px 5px)` }}/>;
  }
  if (type === 'derived') {
    return <div style={{ width: size, height: size, border: `1px solid ${c}` }}/>;
  }
  if (type === 'commuting') {
    return <div style={{ width: size, height: size, border: `1px dotted ${c}` }}/>;
  }
  return <div style={{ width: size, height: size, background: c, opacity: 0.6 }}/>;
}

function CoupleCell({ t, coupling, selected, onSelect }) {
  if (!coupling) {
    return (
      <td style={{
        borderLeft: `1px solid ${t.line}`, borderTop: `1px solid ${t.line}`,
        background: t.bg, padding: 0, height: 64,
        verticalAlign: 'middle', textAlign: 'center',
      }}>
        <Mono t={t} size={9} dim>—</Mono>
      </td>
    );
  }
  const tone = couplingTone(coupling.type, coupling.status);
  const bg = coupling.status === 'open'
    ? 'transparent'
    : (coupling.type === 'noncomm' ? t[tone] : 'transparent');
  const border = coupling.status === 'open' ? `1.5px dashed ${t[tone]}` : `1.5px solid ${t[tone]}`;
  return (
    <td onClick={onSelect} style={{
      borderLeft: `1px solid ${t.line}`, borderTop: `1px solid ${t.line}`,
      background: selected ? t.bg3 : t.bg,
      padding: 6, height: 64,
      cursor: 'pointer',
      verticalAlign: 'middle',
    }}>
      <div style={{
        width: '100%', height: '100%', minHeight: 50,
        border,
        background: bg,
        opacity: coupling.type === 'noncomm' && coupling.status !== 'open' ? 0.75 : 1,
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
      }}>
        <Mono t={t} size={9} style={{
          color: coupling.type === 'noncomm' && coupling.status !== 'open' ? t.bg : t[tone],
          letterSpacing: 0.5,
        }}>
          {coupling.type === 'noncomm' ? 'A∘B≠B∘A' :
           coupling.type === 'rosetta' ? 'ROSETTA' :
           coupling.type === 'derived' ? 'derived' : coupling.type}
        </Mono>
        <Mono t={t} size={8} style={{
          color: coupling.type === 'noncomm' && coupling.status !== 'open' ? t.bg : t[tone],
          opacity: 0.85,
        }}>
          {coupling.status}
        </Mono>
      </div>
    </td>
  );
}

// ============================================================================
// MODE 3 · INTEGRATED — all shells on M(C), legos below as foundation row.
// ============================================================================

function IntegratedView({ t, gs, selectedLayer, setSelectedLayer, selectedLego, setSelectedLego }) {
  return (
    <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 14 }}>
      {/* nested shells diagram */}
      <IntegratedShells t={t} gs={gs} selectedLayer={selectedLayer} setSelectedLayer={setSelectedLayer} />

      {/* legos row */}
      <div style={{ border: `1px solid ${t.line}`, background: t.bg2 }}>
        <div style={{
          padding: '8px 12px', borderBottom: `1px solid ${t.line}`,
          display: 'flex', alignItems: 'baseline', gap: 10,
        }}>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>§ LEGOS</Mono>
          <Mono t={t} size={11}>Local math objects · must exist before pairwise couplings</Mono>
          <div style={{ flex: 1 }} />
          <Mono t={t} size={9} dim>{gs.legos.filter(l => l.status === 'covered').length}/{gs.legos.length} covered</Mono>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 1, background: t.line }}>
          {gs.legos.map(lego => (
            <LegoCard key={lego.id} t={t} lego={lego}
              selected={selectedLego === lego.id}
              onSelect={() => setSelectedLego(lego.id === selectedLego ? null : lego.id)} />
          ))}
        </div>
      </div>

      {/* Rosetta predictions strip */}
      <div style={{ border: `1px solid ${t.line}`, background: t.bg2 }}>
        <div style={{
          padding: '8px 12px', borderBottom: `1px solid ${t.line}`,
          display: 'flex', alignItems: 'baseline', gap: 10,
        }}>
          <Mono t={t} size={10} dim style={{ letterSpacing: 1.5 }}>§ ROSETTAS · predicted agreements (NOT confirmed)</Mono>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 1, background: t.line }}>
          {gs.rosettas.map(r => (
            <div key={r.id} style={{ background: t.bg2, padding: 12 }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'baseline', marginBottom: 6 }}>
                <Mono t={t} size={13}>{r.id}</Mono>
                <Mono t={t} size={10} dim>{r.name}</Mono>
                <div style={{ flex: 1 }}/>
                <StatusChip t={t} status={r.status} />
              </div>
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 6 }}>
                {r.tools.map(tl => <Tag key={tl} t={t} tone="violet">{tl}</Tag>)}
              </div>
              <Mono t={t} size={10} dim style={{ lineHeight: 1.4 }}>{r.claim}</Mono>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function IntegratedShells({ t, gs, selectedLayer, setSelectedLayer }) {
  // Render nested shells as concentric boxes.
  // M(C) is the backdrop (watermark). Inside are S³, then Hopf, then tori.
  // Alongside (to the right) sits the candidate G-tower + Weyl/holonomy/Connes stack.
  const canonLayers = gs.layers.filter(l => l.role === 'canon' && l.id !== 'MC');
  const candidates = gs.layers.filter(l => l.role === 'candidate');

  return (
    <div style={{
      border: `1px solid ${t.line}`, background: t.bg2,
      display: 'grid', gridTemplateColumns: '1.4fr 1fr',
      minHeight: 420,
    }}>
      {/* LEFT · M(C) watermark + canon nested shells */}
      <div style={{
        position: 'relative', padding: 24,
        borderRight: `1px solid ${t.line}`,
        overflow: 'hidden',
      }}>
        {/* M(C) watermark */}
        <MCWatermark t={t} />

        <div style={{ position: 'relative', zIndex: 2, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
            <RoleGlyph t={t} role="canon" />
            <Mono t={t} size={14}>M(C)</Mono>
            <Mono t={t} size={10} dim>— primary. Everything below is a chart on this surface.</Mono>
          </div>
          {/* nested shells as visually-stacked boxes */}
          <div style={{ position: 'relative', marginTop: 8 }}>
            {canonLayers.map((l, i) => {
              const inset = i * 18;
              return (
                <div key={l.id}
                  onClick={() => setSelectedLayer(l.id === selectedLayer ? null : l.id)}
                  style={{
                    marginLeft: inset, marginRight: inset,
                    marginBottom: 6, padding: '10px 14px',
                    background: t.bg,
                    border: `1px solid ${selectedLayer === l.id ? t.amber : t.line}`,
                    cursor: 'pointer',
                    display: 'flex', alignItems: 'baseline', gap: 10,
                  }}>
                  <RoleGlyph t={t} role={l.role} />
                  <Mono t={t} size={12}>{l.name}</Mono>
                  <Mono t={t} size={9} dim>{l.subtitle}</Mono>
                  <div style={{ flex: 1 }}/>
                  <StatusChip t={t} status={l.status} />
                </div>
              );
            })}
          </div>
          <Mono t={t} size={9} dim style={{ marginTop: 6, lineHeight: 1.4 }}>
            These nest as math structures: S³ is where qubits live; U(1)⊂SU(2) carves the Hopf fibration;
            tori T_η foliate S³ and their fibers are (1,1)-curves. The nesting is geometric, not a process order.
          </Mono>
        </div>
      </div>

      {/* RIGHT · candidate G-tower + Weyl/holonomy/Connes */}
      <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 10, position: 'relative' }}>
        <div style={{
          position: 'absolute', top: 8, right: 14,
          fontSize: 9, color: t.violet, letterSpacing: 2, fontFamily: 'JetBrains Mono',
        }}>CANDIDATE · NOT CANON</div>

        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
          <RoleGlyph t={t} role="candidate" />
          <Mono t={t} size={13}>Candidate overlays</Mono>
        </div>
        <Mono t={t} size={9} dim style={{ lineHeight: 1.4 }}>
          Math that might carve ratchet structure on M(C). Dashed = not promoted; probes are shell-local only.
        </Mono>

        {/* G-tower as dashed ladder */}
        <div style={{ marginTop: 6 }}>
          <GTowerLadder t={t} gs={gs} selectedLayer={selectedLayer} setSelectedLayer={setSelectedLayer} />
        </div>

        {/* other candidates */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 6 }}>
          {candidates.filter(l => l.id !== 'GTOWER').map(l => (
            <div key={l.id}
              onClick={() => setSelectedLayer(l.id === selectedLayer ? null : l.id)}
              style={{
                padding: '8px 12px',
                background: t.bg,
                border: `1px dashed ${selectedLayer === l.id ? t.violet : t.line}`,
                cursor: 'pointer',
                display: 'flex', alignItems: 'baseline', gap: 10,
              }}>
              <RoleGlyph t={t} role="candidate" />
              <Mono t={t} size={11}>{l.name}</Mono>
              <Mono t={t} size={9} dim>{l.subtitle}</Mono>
              <div style={{ flex: 1 }}/>
              <StatusChip t={t} status={l.status} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function MCWatermark({ t }) {
  const c = t.amber;
  return (
    <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', zIndex: 1 }}
         preserveAspectRatio="none" viewBox="0 0 400 400">
      <defs>
        <pattern id="wm-grid" width="24" height="24" patternUnits="userSpaceOnUse">
          <path d="M 24 0 L 0 0 0 24" fill="none" stroke={t.line} strokeWidth="0.5"/>
        </pattern>
      </defs>
      <rect width="400" height="400" fill="url(#wm-grid)"/>
      <text x="200" y="370" fontSize="56" fill={c} opacity="0.06"
        textAnchor="middle" fontFamily="JetBrains Mono" fontWeight="600" letterSpacing="8">M(C)</text>
    </svg>
  );
}

function GTowerLadder({ t, gs, selectedLayer, setSelectedLayer }) {
  const gtower = gs.layers.find(l => l.id === 'GTOWER');
  const steps = ['GL', 'O', 'SO', 'U', 'SU', 'Sp'];
  return (
    <div onClick={() => setSelectedLayer(gtower.id === selectedLayer ? null : gtower.id)}
      style={{
        border: `1px dashed ${selectedLayer === gtower.id ? t.violet : t.line}`,
        padding: 12, cursor: 'pointer', background: t.bg,
      }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 8 }}>
        <RoleGlyph t={t} role="candidate" />
        <Mono t={t} size={12}>G-structure tower</Mono>
        <Mono t={t} size={9} dim>{gtower.subtitle}</Mono>
        <div style={{ flex: 1 }}/>
        <StatusChip t={t} status={gtower.status} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 6 }}>
        {steps.map((s, i) => (
          <React.Fragment key={s}>
            <div style={{
              padding: '4px 8px',
              border: `1px dashed ${t.violet}`,
              background: t.bg2,
            }}>
              <Mono t={t} size={11} style={{ color: t.violet }}>{s}</Mono>
            </div>
            {i < steps.length - 1 && (
              <Mono t={t} size={12} dim>↓</Mono>
            )}
          </React.Fragment>
        ))}
      </div>
      <Mono t={t} size={9} dim style={{ marginTop: 8, display: 'block', lineHeight: 1.4 }}>
        5/6 adjacent reductions rigid · G₂ exceptional open · z3 UNSAT on reversed chains = ratchet signature · full-chain pairwise coupling sim NOT YET RUN
      </Mono>
    </div>
  );
}

function LegoCard({ t, lego, selected, onSelect }) {
  const blocked = lego.queue === 'blocked_on_lego' || lego.queue === 'blocked_from_assembly';
  const accent = lego.status === 'covered' ? t.amber
               : lego.status === 'partial' ? t.cyan
               : lego.status === 'needs_deeper_lego_work' ? t.rose
               : t.paperDim;
  return (
    <div onClick={onSelect} style={{
      background: t.bg2,
      padding: 10,
      cursor: 'pointer',
      opacity: blocked ? 0.55 : 1,
      borderLeft: `3px solid ${accent}`,
      outline: selected ? `1px solid ${accent}` : 'none',
      outlineOffset: -1,
      display: 'flex', flexDirection: 'column', gap: 6,
      position: 'relative',
      minHeight: 120,
    }}>
      <div style={{ display: 'flex', gap: 6, alignItems: 'baseline', flexWrap: 'wrap' }}>
        <Mono t={t} size={10}>{lego.name}</Mono>
      </div>
      <StatusChip t={t} status={lego.status} />
      <Mono t={t} size={8} dim style={{ lineHeight: 1.4 }}>
        queue: {lego.queue}
      </Mono>
      <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        {lego.tools.slice(0, 4).map(tool => (
          <span key={tool} style={{
            fontSize: 8, padding: '1px 4px',
            border: `1px solid ${t.line}`,
            color: t.paperFaint,
            fontFamily: 'JetBrains Mono',
          }}>{tool}</span>
        ))}
      </div>
      {blocked && (
        <Mono t={t} size={8} dim style={{ color: t.rose, letterSpacing: 1 }}>BLOCKED</Mono>
      )}
    </div>
  );
}

// ============================================================================
// TOP-LEVEL G-STACK VIEW
// ============================================================================

function GStackView({ t, data, mode, setMode, selectedLayer, setSelectedLayer, selectedCoupling, setSelectedCoupling, selectedLego, setSelectedLego }) {
  const gs = data.gStack;
  if (!gs) {
    return <div style={{ padding: 20 }}>
      <Mono t={t} size={12} dim>No g-stack data loaded.</Mono>
    </div>;
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0, height: '100%' }}>
      <GStackModeTabs t={t} active={mode} onChange={setMode} />
      <DoctrineBar t={t} />
      <div style={{ flex: 1, overflow: 'auto' }}>
        {mode === 'isolated' && <IsolatedView t={t} gs={gs} selectedLayer={selectedLayer} setSelectedLayer={setSelectedLayer} />}
        {mode === 'coupled' && <CoupledView t={t} gs={gs} selectedCoupling={selectedCoupling} setSelectedCoupling={setSelectedCoupling} />}
        {mode === 'integrated' && <IntegratedView t={t} gs={gs}
          selectedLayer={selectedLayer} setSelectedLayer={setSelectedLayer}
          selectedLego={selectedLego} setSelectedLego={setSelectedLego} />}
      </div>
    </div>
  );
}

Object.assign(window, {
  GStackView, IsolatedView, CoupledView, IntegratedView,
  GStackModeTabs, DoctrineBar,
});
