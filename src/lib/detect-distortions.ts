import { DISTORTIONS } from "@/content/distortions";

export type Span = { start: number; end: number };

export type DetectedDistortion = {
  id: string;
  name: string;
  reframe: string;
  weight: number;
  spans: Span[];
};

/** Mirrors Lume's norm(): lowercase, straight apostrophes, collapsed whitespace. */
export function normalise(text: string): string {
  return text.toLowerCase().replace(/[‘’]/g, "'").replace(/\s+/g, " ").trim();
}

/** The sentence as typed, with the same length and offsets as normalise(). */
export function tidy(text: string): string {
  return text.replace(/\s+/g, " ").trim();
}

/** The same scoring as Lume: sum trigger weights, keep the top two. */
export function detectDistortions(text: string): DetectedDistortion[] {
  const input = normalise(text);
  if (!input) return [];

  const found: DetectedDistortion[] = [];
  for (const d of DISTORTIONS) {
    let weight = 0;
    const spans: Span[] = [];
    for (const { pattern, weight: w } of d.triggers) {
      const match = pattern.exec(input);
      if (match) {
        weight += w;
        spans.push({ start: match.index, end: match.index + match[0].length });
      }
    }
    if (weight > 0) found.push({ id: d.id, name: d.name, reframe: d.reframe, weight, spans });
  }
  return found.sort((a, b) => b.weight - a.weight).slice(0, 2);
}

/** Splits text into plain and flagged runs, merging overlaps. */
export function markRuns(input: string, spans: Span[]) {
  const sorted = [...spans].sort((a, b) => a.start - b.start);
  const merged: Span[] = [];
  for (const s of sorted) {
    const last = merged[merged.length - 1];
    if (last && s.start <= last.end) last.end = Math.max(last.end, s.end);
    else merged.push({ ...s });
  }

  const runs: { text: string; flagged: boolean }[] = [];
  let cursor = 0;
  for (const s of merged) {
    if (s.start > cursor) runs.push({ text: input.slice(cursor, s.start), flagged: false });
    runs.push({ text: input.slice(s.start, s.end), flagged: true });
    cursor = s.end;
  }
  if (cursor < input.length) runs.push({ text: input.slice(cursor), flagged: false });
  return runs;
}
