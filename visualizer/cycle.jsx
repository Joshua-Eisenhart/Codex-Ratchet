// Animated controller state-transition cycle.
// Grounded in system_v5/new docs/EXPLICIT_CONTROLLER_MODEL.md — the controller
// is a state-transition manager for bounded research objects, NOT a
// graveyard/recon/mining/compile narrative.
//
// Allowed transitions (§ Allowed State Transitions):
//   A. Source Material        → Normalized Object
//   B. Normalized Object      → Queued Build Target
//   C. Queued Build Target    → Fresh Evidence
//   D. Fresh Evidence         → Registry / Ledger Update
//   E. Local Lego             → Pairwise / Coexistence Successor
//   F. Candidate              → Blocked / Rejected   (side-path)
//
// Operational hierarchy (§ Operational Hierarchy):
//   1. fresh result artifacts & reruns
//   2. validator / audit outputs
//   3. machine ledgers & queue surfaces
//   4. execution docs & controller contracts
//   5. reference prose & theory docs        (lowest authority)

function RatchetCycle({ t }) {
  const W = 1280, H = 720;
  return (
    <Stage width={W} height={H} duration={18} background={t.bg}>
      <BackdropGrid t={t} />
      <StageTitle t={t} />
      <PhaseIndicator t={t} />

      {/* Persistent surfaces */}
      <Sprite start={0} end={18} keepMounted><StateRailSprite t={t} /></Sprite>
      <Sprite start={0} end={18} keepMounted><AuthorityStackSprite t={t} /></Sprite>
      <Sprite start={0} end={18} keepMounted><ObjectBoardSprite t={t} /></Sprite>

      {/* Phase captions */}
      <Sprite start={0.2} end={2.8}>
        <Caption t={t} label="A · SOURCE → NORMALIZED"
          note="bundled prose surfaces an object · isolate it into an explicit lego row + dependency note + suggested probe"
          color={t.paperDim} />
      </Sprite>
      <Sprite start={2.8} end={5.4}>
        <Caption t={t} label="B · NORMALIZED → QUEUED"
          note="prerequisites known · bounded probe nameable · emit queue item with probe path, expected artifact, verify step"
          color={t.cyan} />
      </Sprite>
      <Sprite start={5.4} end={8.6}>
        <Caption t={t} label="C · QUEUED → FRESH EVIDENCE"
          note="run the bounded probe · return path-citable artifact · label under repo truth vocabulary"
          color={t.amber} />
      </Sprite>
      <Sprite start={8.6} end={11.4}>
        <Caption t={t} label="D · EVIDENCE → LEDGER UPDATE"
          note="registry row rewritten · stale prose fenced · backlog & truth-audit reconciled to match evidence"
          color={t.amber} />
      </Sprite>
      <Sprite start={11.4} end={14.4}>
        <Caption t={t} label="E · LEGO → PAIRWISE SUCCESSOR"
          note="only if the lego is real enough · one bounded successor queued · no bridge smuggling"
          color={t.paper} />
      </Sprite>
      <Sprite start={14.4} end={16.6}>
        <Caption t={t} label="F · CANDIDATE → BLOCKED / REJECTED"
          note="dependency failed · local negative case killed it · late-surface classification preserved, not deleted"
          color={t.rose} />
      </Sprite>
      <Sprite start={16.6} end={18}>
        <Caption t={t} label="∎ CYCLE CLOSES"
          note="one honest bounded move · queue or evidence state actually changed · otherwise: documentation motion, not progress"
          color={t.paperDim} />
      </Sprite>

      {/* The bounded object travels through its state transitions */}
      <BoundedObject t={t} />
      {/* Forbidden-move watermark */}
      <ForbiddenWatermark t={t} />
    </Stage>
  );
}

function BackdropGrid({ t }) {
  return (
    <div style={{
      position: 'absolute', inset: 0,
      backgroundImage: `linear-gradient(${t.line}22 1px, transparent 1px), linear-gradient(90deg, ${t.line}22 1px, transparent 1px)`,
      backgroundSize: '40px 40px',
      pointerEvents: 'none',
    }} />
  );
}

function StageTitle({ t }) {
  return (
    <div style={{ position: 'absolute', left: 48, top: 36 }}>
      <Mono t={t} size={11} dim style={{ letterSpacing: 2 }}>§07 · CONTROLLER · ONE HONEST MOVE</Mono>
      <div style={{ marginTop: 6 }}>
        <Mono t={t} size={26} style={{ letterSpacing: 1, textTransform: 'uppercase' }}>
          State-Transition Cycle
        </Mono>
      </div>
      <div style={{ marginTop: 4 }}>
        <Mono t={t} size={10} dim>
          source → normalized → queued → evidence → ledger → successor · with blocked/rejected as side-path
        </Mono>
      </div>
    </div>
  );
}

function PhaseIndicator({ t }) {
  const time = useTime();
  const phases = [
    [0,    2.8,  'A · NORMALIZE'],
    [2.8,  5.4,  'B · QUEUE'],
    [5.4,  8.6,  'C · RUN PROBE'],
    [8.6, 11.4,  'D · LEDGER'],
    [11.4,14.4,  'E · SUCCESSOR'],
    [14.4,16.6,  'F · BLOCK / REJECT'],
    [16.6,18,    '∎ CLOSE'],
  ];
  const cur = phases.find(([s, e]) => time >= s && time < e) || phases[phases.length - 1];
  return (
    <div style={{ position: 'absolute', right: 48, top: 36, textAlign: 'right' }}>
      <Mono t={t} size={11} dim style={{ letterSpacing: 2 }}>CURRENT TRANSITION</Mono>
      <div style={{ marginTop: 6 }}>
        <Mono t={t} size={20} style={{ letterSpacing: 1 }}>{cur[2]}</Mono>
      </div>
      <div style={{ marginTop: 4 }}>
        <Mono t={t} size={10} dim>t = {time.toFixed(2)}s / 18.00s</Mono>
      </div>
    </div>
  );
}

// LEFT: the 6 object states (rail). Current state glows.
function StateRailSprite({ t }) {
  const time = useTime();
  const states = [
    { id: 'source',      label: 'SOURCE MATERIAL',       enter: 0,    exit: 2.8  },
    { id: 'normalized',  label: 'NORMALIZED OBJECT',     enter: 2.0,  exit: 5.4  },
    { id: 'queued',      label: 'QUEUED BUILD TARGET',   enter: 4.6,  exit: 8.6  },
    { id: 'evidence',    label: 'FRESH EVIDENCE',        enter: 7.8,  exit: 11.4 },
    { id: 'ledger',      label: 'REGISTRY / LEDGER',     enter: 10.6, exit: 14.4 },
    { id: 'successor',   label: 'PAIRWISE SUCCESSOR',    enter: 13.6, exit: 18   },
  ];
  return (
    <div style={{ position: 'absolute', left: 48, top: 170, width: 280 }}>
      <Mono t={t} size={10} dim style={{ letterSpacing: 2 }}>OBJECT STATE RAIL</Mono>
      <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
        {states.map((s, i) => {
          const active = time >= s.enter && time < s.exit;
          const passed = time >= s.exit;
          const opacity = active ? 1 : passed ? 0.55 : 0.3;
          const color = active ? t.amber : passed ? t.cyan : t.paperDim;
          return (
            <div key={s.id} style={{ display: 'flex', gap: 10, alignItems: 'center', opacity, transition: 'opacity 200ms' }}>
              <div style={{
                width: 12, height: 12,
                border: `1.5px solid ${color}`,
                background: active ? color : 'transparent',
                transform: 'rotate(45deg)',
                transition: 'all 200ms',
              }} />
              <Mono t={t} size={11} style={{ color }}>{s.label}</Mono>
            </div>
          );
        })}
      </div>
      {/* connectors */}
      <div style={{ marginTop: 12, paddingLeft: 5 }}>
        <Mono t={t} size={9} dim style={{ lineHeight: 1.5, display: 'block' }}>
          ↓ allowed transitions only · no skipping ·<br />
          no prose promotion · no bridge smuggling
        </Mono>
      </div>
    </div>
  );
}

// RIGHT: authority stack — which surface wins when surfaces disagree.
function AuthorityStackSprite({ t }) {
  const time = useTime();
  // During D (ledger update 8.6-11.4) the ledger row visibly rewrites.
  const ledgerRewriting = time >= 8.6 && time < 11.4;
  const layers = [
    { n: 1, label: 'fresh artifacts / reruns', tone: t.amber },
    { n: 2, label: 'validator / audit outputs', tone: t.amber },
    { n: 3, label: 'machine ledgers / queues',  tone: t.cyan },
    { n: 4, label: 'execution docs',            tone: t.paperDim },
    { n: 5, label: 'reference prose / theory',  tone: t.paperFaint },
  ];
  return (
    <div style={{ position: 'absolute', right: 48, top: 170, width: 280 }}>
      <Mono t={t} size={10} dim style={{ letterSpacing: 2 }}>AUTHORITY STACK</Mono>
      <div style={{ marginTop: 4 }}>
        <Mono t={t} size={9} dim>higher explains · lower decides</Mono>
      </div>
      <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 4 }}>
        {layers.map(l => {
          const ledgerRow = l.n === 3;
          return (
            <div key={l.n} style={{
              display: 'grid', gridTemplateColumns: '18px 1fr',
              gap: 6, alignItems: 'center',
              padding: '6px 8px',
              border: `1px solid ${ledgerRow && ledgerRewriting ? t.amber : t.line}`,
              background: ledgerRow && ledgerRewriting ? `${t.amber}14` : 'transparent',
              transition: 'all 200ms',
            }}>
              <Mono t={t} size={10} style={{ color: l.tone }}>{l.n}</Mono>
              <Mono t={t} size={10} style={{ color: l.tone }}>{l.label}</Mono>
            </div>
          );
        })}
      </div>
      {ledgerRewriting && (
        <div style={{ marginTop: 10, padding: 8, border: `1px dashed ${t.amber}`, background: `${t.amber}10` }}>
          <Mono t={t} size={9} style={{ color: t.amber, letterSpacing: 1 }}>● LEDGER ROW REWRITING</Mono>
          <div style={{ marginTop: 4 }}>
            <Mono t={t} size={9} dim style={{ lineHeight: 1.4, display: 'block' }}>
              evidence path cited · stale prose fenced · audit reconciled
            </Mono>
          </div>
        </div>
      )}
    </div>
  );
}

// CENTER: object board — real rows from the 64-schedule atlas + queue.
function ObjectBoardSprite({ t }) {
  const time = useTime();

  // One real object followed through the cycle — a chart-locked macro-stage
  // pulled from the atlas. We follow S10: Ne-in × Ti↓ · NeTi · WIN · T1 outer.
  const obj = {
    slot:    'S10',
    row:     'Ne-in',
    col:     'Ti↓',
    token:   'NeTi',
    role:    'T1 outer',
    outcome: 'WIN',
    probe:   'sim_results/axis0_xi_bakeoff_results.json',
    verify:  'rerun_manifest_verify.py',
    dep:     'Ax4 canonical order · open',
  };

  // Progressive reveal by phase — only what the current transition has earned.
  const hasNormalized = time >= 2.0;
  const hasQueue      = time >= 4.6;
  const hasEvidence   = time >= 7.8;
  const hasLedger     = time >= 10.6;
  const hasSuccessor  = time >= 13.6;

  // During C (run probe, 5.4-8.6) the evidence spinner is active.
  const probing = time >= 5.4 && time < 8.6;

  return (
    <div style={{
      position: 'absolute',
      left: '50%', top: 180,
      transform: 'translateX(-50%)',
      width: 560,
    }}>
      <div style={{ textAlign: 'center', marginBottom: 12 }}>
        <Mono t={t} size={10} dim style={{ letterSpacing: 2 }}>BOUNDED OBJECT · ONE ROW</Mono>
      </div>

      {/* Atlas slot — object identity, always visible */}
      <ObjectCard t={t} tone="paper" title={`${obj.slot}★ · chart-locked macro-stage`}>
        <Row t={t} k="terrain"  v={obj.row} />
        <Row t={t} k="signed op" v={obj.col} />
        <Row t={t} k="token"    v={obj.token} />
        <Row t={t} k="role"     v={obj.role} />
        <Row t={t} k="outcome"  v={obj.outcome} tone="amber" />
      </ObjectCard>

      {/* Normalized → Queued → Evidence → Ledger — stacked cards */}
      <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <Fade show={hasNormalized}>
          <ObjectCard t={t} tone="cyan" title="B · QUEUE ITEM">
            <Row t={t} k="probe"    v={obj.probe} mono />
            <Row t={t} k="verify"   v={obj.verify} mono />
            <Row t={t} k="blocker"  v={obj.dep} tone="paperDim" />
          </ObjectCard>
        </Fade>
        <Fade show={hasEvidence}>
          <ObjectCard t={t} tone="amber" title={probing ? 'C · PROBE RUNNING…' : 'C · FRESH EVIDENCE'}>
            <Row t={t} k="artifact" v="axis0_xi_bakeoff_results.json" mono />
            <Row t={t} k="size"     v="12,489 bytes" mono />
            <Row t={t} k="label"    v={probing ? 'pending' : 'survived · 8/8 VN-positive'} tone={probing ? 'paperDim' : 'amber'} />
          </ObjectCard>
        </Fade>
        <Fade show={hasLedger}>
          <ObjectCard t={t} tone="amber" title="D · LEDGER ROW UPDATED">
            <Row t={t} k="registry" v="17_actual_lego_registry.md" mono />
            <Row t={t} k="row"      v={`${obj.slot} · survived · cites evidence path`} tone="amber" />
            <Row t={t} k="stale"    v="2 prose docs fenced" tone="rose" />
          </ObjectCard>
        </Fade>
        <Fade show={hasSuccessor}>
          <ObjectCard t={t} tone="paper" title="E · PAIRWISE SUCCESSOR QUEUED">
            <Row t={t} k="successor" v="S13 · Ne-in × Fi↑ · FiNe · lose · T1 inner" />
            <Row t={t} k="gated by"  v="S10 real enough · no bridge claim" tone="paperDim" />
          </ObjectCard>
        </Fade>
      </div>
    </div>
  );
}

function Fade({ show, children }) {
  return (
    <div style={{
      opacity: show ? 1 : 0,
      transform: show ? 'translateY(0)' : 'translateY(8px)',
      transition: 'all 300ms',
      pointerEvents: show ? 'auto' : 'none',
    }}>
      {show && children}
    </div>
  );
}

function ObjectCard({ t, tone = 'paper', title, children }) {
  const borderColor = tone === 'amber' ? t.amber :
                      tone === 'cyan'  ? t.cyan :
                      tone === 'rose'  ? t.rose : t.line;
  return (
    <div style={{
      border: `1px solid ${borderColor}`,
      background: t.bg2,
      padding: '10px 12px',
    }}>
      <Mono t={t} size={10} style={{ color: borderColor, letterSpacing: 1.2 }}>{title}</Mono>
      <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 3 }}>
        {children}
      </div>
    </div>
  );
}

function Row({ t, k, v, mono, tone }) {
  const valColor = tone === 'amber' ? t.amber :
                   tone === 'rose'  ? t.rose :
                   tone === 'paperDim' ? t.paperDim :
                   t.paper;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 10 }}>
      <Mono t={t} size={10} dim>{k}</Mono>
      <Mono t={t} size={10} style={{ color: valColor, fontFamily: mono ? 'JetBrains Mono, monospace' : undefined }}>{v}</Mono>
    </div>
  );
}

// A single traveling glyph threading through the state rail on the left.
function BoundedObject({ t }) {
  const time = useTime();
  // Rail y-positions (left column) — match StateRailSprite order.
  // Each transition shifts the glyph to the next state. During F (14.4-16.6)
  // a side-path fork shows a *different* candidate being rejected.
  const kfs = [
    { t: 0.2, x: 72,  y: 208, c: t.paperDim, label: 'source'     },
    { t: 2.3, x: 72,  y: 238, c: t.cyan,     label: 'normalized' },
    { t: 4.9, x: 72,  y: 268, c: t.cyan,     label: 'queued'     },
    { t: 7.6, x: 72,  y: 298, c: t.amber,    label: 'evidence'   },
    { t: 10.8,x: 72,  y: 328, c: t.amber,    label: 'ledger'     },
    { t: 14.0,x: 72,  y: 358, c: t.paper,    label: 'successor'  },
    { t: 17.5,x: 72,  y: 358, c: t.paper,    label: 'successor'  },
  ];
  let p1 = kfs[0], p2 = kfs[kfs.length - 1];
  for (let i = 0; i < kfs.length - 1; i++) {
    if (time >= kfs[i].t && time <= kfs[i + 1].t) { p1 = kfs[i]; p2 = kfs[i + 1]; break; }
  }
  const span = p2.t - p1.t;
  const local = span > 0 ? Math.min(1, Math.max(0, (time - p1.t) / span)) : 0;
  const ease = Easing.easeInOutCubic(local);
  const x = p1.x + (p2.x - p1.x) * ease;
  const y = p1.y + (p2.y - p1.y) * ease;
  const c = local < 0.5 ? p1.c : p2.c;
  const pulse = 1 + 0.12 * Math.sin(time * 5);

  // Side-path glyph — appears during F, travels right→down off-rail into a REJECTED box.
  const sidePathVisible = time >= 14.4 && time < 16.6;
  const sidePathP = sidePathVisible ? (time - 14.4) / 2.2 : 0;
  const sx = 72 + sidePathP * 520;
  const sy = 358 + sidePathP * 180;

  return (
    <>
      <div style={{
        position: 'absolute',
        left: x, top: y,
        transform: `translate(-50%, -50%) scale(${pulse})`,
        pointerEvents: 'none',
      }}>
        <div style={{
          width: 16, height: 16,
          transform: 'rotate(45deg)',
          background: c,
          boxShadow: `0 0 18px ${c}`,
        }} />
      </div>

      {sidePathVisible && (
        <>
          <div style={{
            position: 'absolute',
            left: sx, top: sy,
            transform: 'translate(-50%, -50%) rotate(45deg)',
            width: 14, height: 14,
            background: 'transparent',
            border: `2px solid ${t.rose}`,
            opacity: 1 - sidePathP * 0.3,
            pointerEvents: 'none',
          }} />
          {sidePathP > 0.8 && (
            <div style={{
              position: 'absolute', left: sx + 20, top: sy - 10,
              padding: '4px 8px', border: `1px solid ${t.rose}`,
              background: `${t.rose}15`,
            }}>
              <Mono t={t} size={9} style={{ color: t.rose, letterSpacing: 1 }}>
                BLOCKED · dep failed · preserved
              </Mono>
            </div>
          )}
        </>
      )}
    </>
  );
}

function ForbiddenWatermark({ t }) {
  return (
    <div style={{
      position: 'absolute', left: 48, bottom: 36,
      display: 'flex', flexDirection: 'column', gap: 2,
    }}>
      <Mono t={t} size={9} dim style={{ letterSpacing: 1.5 }}>FORBIDDEN</Mono>
      <Mono t={t} size={9} style={{ color: t.rose, opacity: 0.7, lineHeight: 1.5 }}>
        prose promotion without evidence · treating "exists" as "runs" ·<br />
        merging lanes across unrelated programs · skipping local → bridge
      </Mono>
    </div>
  );
}

function Caption({ t, label, note, color }) {
  const { progress } = useSprite();
  const fadeIn = Math.min(1, progress / 0.15);
  const fadeOut = progress > 0.8 ? 1 - (progress - 0.8) / 0.2 : 1;
  const o = Math.min(fadeIn, fadeOut);
  const slide = (1 - fadeIn) * 10;

  return (
    <div style={{
      position: 'absolute',
      left: '50%', bottom: 64,
      transform: `translateX(-50%) translateY(${slide}px)`,
      opacity: o,
      maxWidth: 760, textAlign: 'center',
    }}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'baseline', justifyContent: 'center' }}>
        <div style={{
          width: 12, height: 12, transform: 'rotate(45deg)',
          background: color,
        }} />
        <Mono t={t} size={16} style={{ letterSpacing: 1.4, color }}>{label}</Mono>
      </div>
      <div style={{ marginTop: 6 }}>
        <Mono t={t} size={11} dim style={{ lineHeight: 1.55 }}>{note}</Mono>
      </div>
    </div>
  );
}

Object.assign(window, { RatchetCycle });
