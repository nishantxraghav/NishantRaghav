/**
 * The page's one gesture: a loose ring drawn by hand around something. It starts
 * off-axis and overshoots its own start, the way a pen does. `seed` varies the wobble.
 * `square` below 1 pushes the curve into the corners, so a wide line of text fits inside.
 */
export function ringPath(width: number, height: number, seed = 0, square = 1): string {
  const cx = width / 2;
  const cy = height / 2;
  const rx = width / 2 - 3;
  const ry = height / 2 - 3;
  const steps = 72;
  const start = -2.2 + seed;
  const sweep = Math.PI * 2.14;

  const points: string[] = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const angle = start + sweep * t;
    const wobble = 1 + 0.035 * Math.sin(angle * 3 + seed) + 0.02 * Math.sin(angle * 5 - seed);
    // The radius drifts as it goes, so the two ends of the stroke don't meet.
    const drift = 1 - 0.07 * t;
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    const x = cx + Math.sign(cos) * Math.abs(cos) ** square * rx * wobble * drift;
    const y = cy + Math.sign(sin) * Math.abs(sin) ** square * ry * wobble * drift;
    points.push(`${x.toFixed(1)} ${y.toFixed(1)}`);
  }
  return `M${points.join("L")}`;
}
