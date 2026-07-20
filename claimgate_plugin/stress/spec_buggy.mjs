// Function an agent might write: merge a list of {start,end} ranges.
// Planted bugs: crashes on empty list; produces end<start when input has
// a reversed range; drops the mutated-extra-key case into NaN via arithmetic.
function mergeRanges(ranges) {
  const sorted = [...ranges].sort((a, b) => a.start - b.start);
  const out = [sorted[0]];                     // bug: throws pattern on empty
  for (const r of sorted.slice(1)) {
    const last = out[out.length - 1];
    if (r.start <= last.end) last.end = Math.max(last.end, r.end);
    else out.push({ start: r.start, end: r.end });
  }
  return out;
}
export default {
  name: "mergeRanges (buggy)",
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
