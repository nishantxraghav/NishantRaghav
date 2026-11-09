"use client";

import { useEffect, useRef } from "react";
import { ringPath } from "@/lib/ring";

type Variant = "hero" | "empty" | "broken";

type Word = { x: number; y: number; len: number; row: number; s: number; hidden?: boolean };
type Odd = { word: Word; amount: number; target: number };

const UNIT = 24;
const BASE_WIDTH = 2;
const LENS_WIDTH = 5;
const REST_ALPHA = 0.42;
const EASE = 0.16;
const ODD_EASE = 0.2;
const REVEAL_MS = 420;
const RIPPLE_MS = 760;
/** How far the pointer's influence reaches. The lens on "notices." behaves the same way. */
const REACH = 96;

const NOTES: Record<Variant, string> = {
  hero: "out of place",
  empty: "nothing here",
  broken: "",
};

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

/**
 * A log file seen from far away, written on the pad's ruled lines. One entry doesn't
 * belong, and a red pencil ring finds it. Lines near the pointer gain weight the same
 * way the headline does; click or tap the odd entry and it snaps back, and the page
 * finds another. Decorative, so it's hidden from assistive tech, and the canvas only
 * draws while something is moving.
 *
 * The parent must be positioned and hold a [data-field-bottom] element. Anything marked
 * [data-field-clear] keeps its space free of marks.
 */
export function LogField({ variant = "hero" }: { variant?: Variant }) {
  const hostRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const ringRef = useRef<SVGSVGElement>(null);
  const pathRef = useRef<SVGPathElement>(null);
  const noteRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const host = hostRef.current;
    const canvas = canvasRef.current;
    const ring = ringRef.current;
    const path = pathRef.current;
    const note = noteRef.current;
    const section = host?.parentElement;
    const ctx = canvas?.getContext("2d");
    if (!host || !canvas || !ring || !path || !note || !section || !ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const styles = getComputedStyle(document.documentElement);
    const colour = (name: string, fallback: string) => styles.getPropertyValue(name).trim() || fallback;
    const dim = colour("--color-dim", "#4a5b51");
    const pen = colour("--color-pen", "#1c2bbe");
    const pencil = colour("--color-pencil", "#be2f1c");

    let words: Word[] = [];
    let odds: Odd[] = [];
    let width = 0;
    let height = 0;
    let left = 0;
    let right = 0;
    let revealStart = 0;
    let revealed = reduced ? 1 : 0;
    let pointer: { x: number; y: number } | null = null;
    let ripple: { x: number; y: number; start: number } | null = null;
    let raf = 0;
    let visible = true;
    let seed = Math.random() * 6;
    const timers: ReturnType<typeof setTimeout>[] = [];

    const placeRing = (word: Word) => {
      const w = Math.max(84, word.len + 58);
      const h = 58;
      const cx = word.x + word.len / 2;
      const cy = word.y - 8;
      ring.setAttribute("viewBox", `0 0 ${w} ${h}`);
      ring.setAttribute("width", String(w));
      ring.setAttribute("height", String(h));
      ring.style.transform = `translate(${cx - w / 2}px, ${cy - h / 2}px)`;
      path.setAttribute("d", ringPath(w, h, seed));
      seed += 1.7;

      const noteWidth = note.offsetWidth;
      const fitsRight = cx + w / 2 + 10 + noteWidth < right;
      const x = fitsRight ? cx + w / 2 + 10 : cx - w / 2 - 10 - noteWidth;
      const y = cy - 12;
      note.style.transform = `translate(${x}px, ${y}px)`;
      // The note sits on clear paper, so it never reads through a line.
      for (const w of words) {
        const beside = w.x + w.len > x - 8 && w.x < x + noteWidth + 8;
        w.hidden = noteWidth > 0 && beside && w.y > y - 4 && w.y < y + 28;
      }
    };

    const showRing = (state: "drawn" | "gone" | "ready") => {
      host.dataset.ring = state;
    };

    const pickOdd = (avoid?: Word): Word | undefined => {
      const span = right - left;
      const navH = parseFloat(styles.getPropertyValue("--nav-h")) || 56;
      const wide = words.filter((w) => w.len >= 20 && w.len <= 76 && w !== avoid);
      const roomy = wide.filter(
        (w) => w.x > left + span * 0.34 && w.x + w.len < right - 56 && w.y > navH + 48 && w.y < height - 34,
      );
      const pool = roomy.length ? roomy : wide;
      return pool[Math.floor(Math.random() * pool.length)];
    };

    const build = () => {
      const box = section.getBoundingClientRect();
      const bottomEl = section.querySelector("[data-field-bottom]");
      if (!bottomEl) return;
      const bottomBox = bottomEl.getBoundingClientRect();
      const gutter = parseFloat(styles.getPropertyValue("--gutter")) || 16;
      const navH = parseFloat(styles.getPropertyValue("--nav-h")) || 56;

      width = box.width;
      left = bottomBox.left - box.left;
      right = width - gutter;
      height = Math.max(0, bottomBox.top - box.top);

      const clear = Array.from(section.querySelectorAll("[data-field-clear]")).map((el) => {
        const r = el.getBoundingClientRect();
        return {
          left: r.left - box.left - UNIT,
          right: r.right - box.left + UNIT,
          top: r.top - box.top - UNIT / 2,
          bottom: r.bottom - box.top + UNIT / 2,
        };
      });

      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      words = [];
      let indent = 0;
      let row = 0;
      for (let y = Math.ceil((navH + UNIT) / UNIT) * UNIT; y < height - UNIT * 0.6; y += UNIT, row++) {
        if (Math.random() < 0.1) continue;
        if (Math.random() < 0.36) indent = clamp(indent + (Math.random() < 0.5 ? -1 : 1), 0, 5);
        let x = left + indent * UNIT;
        let end = left + (right - left) * (0.34 + 0.66 * Math.random());
        while (x < end) {
          const len = Math.min(10 + Math.random() ** 2 * 62, right - x);
          if (len < 6) break;
          const hit = clear.find((c) => y > c.top && y < c.bottom && x + len > c.left && x < c.right);
          if (hit) {
            x = hit.right;
            // A scrap of a line beside the headline reads as a mistake, not a log.
            if (right - x < 140) break;
            end = Math.max(end, Math.min(right, x + 260));
            continue;
          }
          words.push({ x, y: y - 4, len, row, s: 0 });
          x += len + 7;
        }
      }

      odds = [];
      if (variant === "hero") {
        const word = pickOdd();
        if (word) {
          odds = [{ word, amount: 1, target: 1 }];
          placeRing(word);
        }
      } else if (variant === "empty") {
        const word = pickOdd();
        if (word) {
          placeRing(word);
          words = words.filter((w) => w !== word);
        }
      } else {
        const count = Math.min(7, Math.floor(words.length / 24));
        const shuffled = [...words].sort(() => Math.random() - 0.5).slice(0, count);
        odds = shuffled.map((word) => ({ word, amount: 1, target: 1 }));
      }
    };

    const draw = () => {
      ctx.clearRect(0, 0, width, height);
      const span = right - left;
      const rows = Math.max(1, words[words.length - 1]?.row ?? 1);
      const isOdd = new Set(odds.map((o) => o.word));

      const reach = (w: Word) => {
        const line = left + span * (revealed * 1.5 - (w.row / rows) * 0.5);
        return Math.min(w.x + w.len, line);
      };

      ctx.lineCap = "butt";
      ctx.lineWidth = BASE_WIDTH;
      ctx.strokeStyle = dim;
      ctx.globalAlpha = REST_ALPHA;
      ctx.beginPath();
      for (const w of words) {
        if (w.hidden || w.s > 0.01 || isOdd.has(w)) continue;
        const end = reach(w);
        if (end <= w.x) continue;
        ctx.moveTo(w.x, w.y);
        ctx.lineTo(end, w.y);
      }
      ctx.stroke();

      ctx.strokeStyle = pen;
      for (const w of words) {
        if (w.hidden || w.s <= 0.01 || isOdd.has(w)) continue;
        ctx.globalAlpha = REST_ALPHA + (1 - REST_ALPHA) * w.s;
        ctx.lineWidth = BASE_WIDTH + LENS_WIDTH * w.s;
        ctx.beginPath();
        ctx.moveTo(w.x, w.y);
        ctx.lineTo(reach(w), w.y);
        ctx.stroke();
      }

      for (const odd of odds) {
        const { word, amount } = odd;
        if (reach(word) <= word.x) continue;
        ctx.save();
        ctx.translate(word.x + word.len / 2, word.y - 8 * amount);
        ctx.rotate(-0.24 * amount);
        ctx.globalAlpha = REST_ALPHA + (1 - REST_ALPHA) * amount;
        ctx.strokeStyle = amount > 0.4 ? pencil : dim;
        ctx.lineWidth = BASE_WIDTH + 1.5 * amount;
        ctx.beginPath();
        ctx.moveTo(-word.len / 2, 0);
        ctx.lineTo(word.len / 2, 0);
        ctx.stroke();
        ctx.restore();
      }
      ctx.globalAlpha = 1;
    };

    const frame = (now: number) => {
      raf = 0;
      let busy = false;

      if (revealStart && revealed < 1) {
        revealed = clamp((now - revealStart) / REVEAL_MS, 0, 1);
        busy = true;
      }

      let rippleAt = -1;
      if (ripple) {
        const age = now - ripple.start;
        if (age > RIPPLE_MS) ripple = null;
        else {
          rippleAt = age * 0.62;
          busy = true;
        }
      }

      for (const w of words) {
        let target = 0;
        if (pointer) {
          const dx = pointer.x - clamp(pointer.x, w.x, w.x + w.len);
          target = Math.max(0, 1 - Math.hypot(dx, pointer.y - w.y) / REACH);
        }
        if (ripple && rippleAt >= 0) {
          const dx = ripple.x - clamp(ripple.x, w.x, w.x + w.len);
          const ring = Math.abs(Math.hypot(dx, ripple.y - w.y) - rippleAt);
          target = Math.max(target, Math.max(0, 1 - ring / 44));
        }
        const next = w.s + (target - w.s) * EASE;
        w.s = Math.abs(next - target) < 0.004 ? target : next;
        if (w.s !== target) busy = true;
      }

      for (const odd of odds) {
        const next = odd.amount + (odd.target - odd.amount) * ODD_EASE;
        odd.amount = Math.abs(next - odd.target) < 0.004 ? odd.target : next;
        if (odd.amount !== odd.target) busy = true;
      }

      draw();
      if (busy) wake();
    };

    function wake() {
      if (!raf && visible && !reduced) raf = requestAnimationFrame(frame);
    }

    const local = (e: PointerEvent) => {
      const box = section.getBoundingClientRect();
      return { x: e.clientX - box.left, y: e.clientY - box.top };
    };

    /** The odd entry snaps into line, and the page goes looking for the next one. */
    const fix = (odd: Odd) => {
      odd.target = 0;
      showRing("gone");
      wake();
      timers.push(
        setTimeout(() => {
          const next = pickOdd(odd.word);
          if (!next) return;
          odds = [{ word: next, amount: 0, target: 1 }];
          placeRing(next);
          showRing("ready");
          wake();
          timers.push(setTimeout(() => showRing("drawn"), 240));
        }, 420),
      );
    };

    const onMove = (e: PointerEvent) => {
      if (e.pointerType !== "mouse") return;
      pointer = local(e);
      wake();
    };
    const onLeave = () => {
      pointer = null;
      wake();
    };
    const onDown = (e: PointerEvent) => {
      const at = local(e);
      if (at.y > height) return;
      const odd = variant === "hero" ? odds[0] : undefined;
      if (odd && odd.target === 1) {
        const cx = odd.word.x + odd.word.len / 2;
        if (Math.hypot(at.x - cx, at.y - (odd.word.y - 8)) < 48) {
          fix(odd);
          return;
        }
      }
      if (e.pointerType !== "mouse") {
        ripple = { ...at, start: performance.now() };
        wake();
      }
    };

    let lastWidth = 0;
    const onResize = () => {
      if (window.innerWidth === lastWidth) return;
      lastWidth = window.innerWidth;
      showRing("ready");
      build();
      revealed = 1;
      draw();
      if (variant !== "broken") showRing("drawn");
    };

    const visibility = new IntersectionObserver(([entry]) => {
      visible = entry?.isIntersecting ?? true;
      if (visible) wake();
    });

    const start = () => {
      lastWidth = window.innerWidth;
      build();
      if (reduced) {
        draw();
        if (variant !== "broken") showRing("drawn");
        return;
      }
      // Timed from navigation, so a slow start skips the wait instead of adding to it.
      const revealAt = variant === "hero" ? 900 : 240;
      const wait = Math.max(0, revealAt - performance.now());
      timers.push(
        setTimeout(() => {
          revealStart = performance.now();
          wake();
          if (variant !== "broken") {
            timers.push(setTimeout(() => showRing("drawn"), REVEAL_MS + 60));
          }
        }, wait),
      );
      window.addEventListener("pointermove", onMove, { passive: true });
      document.documentElement.addEventListener("pointerleave", onLeave);
      section.addEventListener("pointerdown", onDown, { passive: true });
      window.addEventListener("resize", onResize);
      visibility.observe(host);
    };

    let cancelled = false;
    void document.fonts.ready.then(() => {
      if (!cancelled) start();
    });

    return () => {
      cancelled = true;
      cancelAnimationFrame(raf);
      timers.forEach(clearTimeout);
      visibility.disconnect();
      window.removeEventListener("pointermove", onMove);
      document.documentElement.removeEventListener("pointerleave", onLeave);
      section.removeEventListener("pointerdown", onDown);
      window.removeEventListener("resize", onResize);
    };
  }, [variant]);

  return (
    <div ref={hostRef} data-ring="ready" aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      <canvas ref={canvasRef} className="absolute left-0 top-0" />
      <svg ref={ringRef} className="field-ring absolute left-0 top-0" fill="none">
        <path ref={pathRef} pathLength={1} className="ring-path text-pencil" stroke="currentColor" strokeWidth={1.75} />
      </svg>
      {NOTES[variant] ? (
        <span ref={noteRef} className="field-note tag absolute left-0 top-0 whitespace-nowrap text-pencil">
          {NOTES[variant]}
        </span>
      ) : (
        <span ref={noteRef} className="hidden" />
      )}
    </div>
  );
}
