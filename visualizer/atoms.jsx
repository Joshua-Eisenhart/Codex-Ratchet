// Shared style atoms for Ratchet visualizer
const RATCHET_TOKENS = {
  // Cool near-black, warm paper, oklch accents at same chroma/lightness (~ c 0.13, l 0.72)
  terminal: {
    bg: '#0b0d10',
    bg2: '#13161b',
    bg3: '#1a1e25',
    line: '#262b33',
    paper: '#e8ebee',
    paperDim: '#9aa3af',
    paperFaint: '#5a6270',
    amber: 'oklch(0.74 0.13 70)',    // survived
    rose:  'oklch(0.68 0.13 20)',    // killed / open-blocking
    cyan:  'oklch(0.74 0.10 210)',   // embargoed / doctrinal / recon
    violet:'oklch(0.70 0.11 290)',   // meta / candidate
    // Hex mirrors for Three.js (which can't parse oklch)
    amberHex:  '#df9b44',
    roseHex:   '#dd7577',
    cyanHex:   '#51bcce',
    violetHex: '#9d92de',
    paperHex:     '#e8ebee',
    paperDimHex:  '#9aa3af',
    paperFaintHex:'#5a6270',
    lineHex:      '#262b33',
    bgHex:        '#0b0d10',
    bg2Hex:       '#13161b',
    bg3Hex:       '#1a1e25',
  },
  paper: {
    bg: '#f1eee8',
    bg2: '#e9e5dd',
    bg3: '#ddd8cd',
    line: '#cac3b3',
    paper: '#18150f',
    paperDim: '#4f4a3e',
    paperFaint: '#8a8474',
    amber: 'oklch(0.58 0.13 70)',
    rose:  'oklch(0.52 0.14 20)',
    cyan:  'oklch(0.54 0.10 210)',
    violet:'oklch(0.52 0.11 290)',
    amberHex:  '#aa6a00',
    roseHex:   '#ab4046',
    cyanHex:   '#007e8f',
    violetHex: '#695ca3',
    paperHex:     '#18150f',
    paperDimHex:  '#4f4a3e',
    paperFaintHex:'#8a8474',
    lineHex:      '#cac3b3',
    bgHex:        '#f1eee8',
    bg2Hex:       '#e9e5dd',
    bg3Hex:       '#ddd8cd',
  },
};

const STATUS_TONE = {
  survived: 'amber',
  killed: 'rose',
  open: 'rose',
  split: 'rose',
  embargoed: 'cyan',
  doctrinal: 'cyan',
  not_yet_tested: 'paperFaint',
  derived: 'paperDim',
  active: 'paper',
};

function statusColor(t, status) {
  const key = STATUS_TONE[status] || 'paperDim';
  return t[key];
}

function Tag({ tone, children, t, solid }) {
  const color = tone ? t[tone] : t.paperDim;
  return (
    <span style={{
      fontFamily: 'JetBrains Mono, ui-monospace, monospace',
      fontSize: 10,
      letterSpacing: 0.4,
      textTransform: 'uppercase',
      padding: '2px 6px',
      color: solid ? t.bg : color,
      background: solid ? color : 'transparent',
      border: solid ? 'none' : `1px solid ${color}`,
      borderRadius: 2,
      whiteSpace: 'nowrap',
      display: 'inline-block',
    }}>{children}</span>
  );
}

function StatusDot({ status, t, size = 8 }) {
  const c = statusColor(t, status);
  const hollow = status === 'open' || status === 'split';
  return (
    <span style={{
      display: 'inline-block',
      width: size, height: size, borderRadius: 0,
      background: hollow ? 'transparent' : c,
      border: `1.5px solid ${c}`,
      transform: 'rotate(45deg)',
      flexShrink: 0,
    }} />
  );
}

function Mono({ children, dim, t, size = 11, style }) {
  return (
    <span style={{
      fontFamily: 'JetBrains Mono, ui-monospace, monospace',
      fontSize: size,
      color: dim ? t.paperDim : t.paper,
      ...style,
    }}>{children}</span>
  );
}

function Rule({ t, vertical, style }) {
  return <div style={{
    background: t.line,
    [vertical ? 'width' : 'height']: 1,
    [vertical ? 'height' : 'width']: '100%',
    ...style,
  }} />;
}

function FrameLabel({ t, n, title, right, children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <div style={{
        display: 'flex', alignItems: 'baseline', gap: 12,
        padding: '10px 14px 8px 14px',
        borderBottom: `1px solid ${t.line}`,
      }}>
        <Mono t={t} dim size={10} style={{ letterSpacing: 1.5 }}>§{n}</Mono>
        <Mono t={t} size={11} style={{ letterSpacing: 1.5, textTransform: 'uppercase' }}>{title}</Mono>
        <div style={{ flex: 1 }} />
        {right}
      </div>
      <div style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>{children}</div>
    </div>
  );
}

Object.assign(window, { RATCHET_TOKENS, STATUS_TONE, statusColor, Tag, StatusDot, Mono, Rule, FrameLabel });
