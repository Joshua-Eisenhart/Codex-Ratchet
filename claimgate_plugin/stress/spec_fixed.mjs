// The repaired version an agent would write after seeing the counterexamples.
function mergeRanges(ranges) {
  if (!Array.isArray(ranges)) return [];
  const valid = ranges.filter((r) => r && typeof r === "object"
    && typeof r.start === "number" && typeof r.end === "number"
    && !Number.isNaN(r.start) && !Number.isNaN(r.end)
    && Number.isFinite(r.start) && Number.isFinite(r.end));
  const norm = valid.map((r) => ({ start: Math.min(r.start, r.end), end: Math.max(r.start, r.end) }));
  norm.sort((a, b) => a.start - b.start);
  const out = [];
  for (const r of norm) {
    const last = out[out.length - 1];
    if (last && r.start <= last.end) last.end = Math.max(last.end, r.end);
    else out.push({ start: r.start, end: r.end });
  }
  return out;
}
export default {
  name: "mergeRanges (fixed)",
  fn: mergeRanges,
  seeds: [
    [{ start: 0, end: 5 }, { start: 3, end: 9 }],
    [{ start: 1, end: 2 }, { start: 10, end: 12 }],
  ],
  invariants: [
    { id: "no-throw", check: (inp, out, err) => err === undefined },
    { id: "ordered-pairs", check: (inp, out, err) => err !== undefined || out.every((r) => typeof r.start === "number" && typeof r.end === "number" && r.start <= r.end && !Number.isNaN(r.start) && !Number.isNaN(r.end)) },
    { id: "no-overlap", check: (inp, out, err) => err !== undefined || out.every((r, i) => i === 0 || out[i - 1].end < r.start) },
  ],
};
