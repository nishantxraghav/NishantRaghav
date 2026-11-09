"use client";

import { useEffect, useRef } from "react";

const WORD = "notices.";
/**
 * Advance widths of the word's letters in Big Shoulders at weight 400, in em. Written
 * into the HTML so the letters stay put when the web font swaps in on a slow device.
 */
const WIDTHS = [0.3796, 0.3641, 0.2461, 0.1796, 0.3486, 0.3511, 0.3296, 0.2081];
const REST = 400;
const PEAK = 840;
/** Phones get a lighter lens: the word has less room, and the thumb covers it anyway. */
const PEAK_TOUCH = 680;
/** Reach of the pointer's influence, as a multiple of the word's height. */
const REACH = 0.9;
const EASE = 0.14;
/** Starts as the letters land, so the whole load sequence fits inside two seconds. */
const SWEEP_AT = 700;
const SWEEP_MS = 700;

/**
 * The headline's last word watches you: letters near the pointer or finger gain weight
 * and push their neighbours aside, like a lens. One sweep plays on load with a mouse.
 * On touch nothing runs until you touch: press or drag the word, or scroll, and the
 * lens moves through it.
 *
 * Layout never changes. Each letter's slot has a fixed width, and the push comes from
 * transforms worked out from measured widths, so nothing shifts. With reduced motion
 * the word simply stays still.
 */
export function NoticingWord() {
  const rootRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const canHover = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
    const peak = canHover ? PEAK : PEAK_TOUCH;

    const letters = Array.from(root.querySelectorAll<HTMLElement>("[data-letter]"));
    const slots = letters.map((l) => l.parentElement as HTMLElement);
    const current = letters.map(() => REST);
    let restWidths: number[] = [];
    let peakWidths: number[] = [];
    let centres: number[] = [];
    let top = 0;
    let height = 1;
    let pointer: { x: number; y: number } | null = null;
    let sweepStart = canHover ? Math.max(performance.now(), SWEEP_AT) : Number.POSITIVE_INFINITY;
    let frame = 0;
    let running = false;

    /** Resting positions and both extremes, so moving letters never feed back into the maths. */
    const measure = () => {
      slots.forEach((slot) => {
        slot.style.transform = "";
      });
      letters.forEach((l) => {
        l.style.fontWeight = String(PEAK);
      });
      peakWidths = letters.map((l) => l.getBoundingClientRect().width);
      letters.forEach((l) => {
        l.style.fontWeight = String(REST);
      });
      current.fill(REST);
      const boxes = letters.map((l) => l.getBoundingClientRect());
      restWidths = boxes.map((b) => b.width);
      centres = boxes.map((b) => b.left + b.width / 2 + window.scrollX);
      const rootBox = root.getBoundingClientRect();
      top = rootBox.top + window.scrollY;
      height = rootBox.height;
    };

    const tick = (now: number) => {
      let moving = false;
      const sweepT = (now - sweepStart) / SWEEP_MS;
      const sweeping = sweepT >= 0 && sweepT <= 1;
      const first = centres[0] ?? 0;
      const last = centres[centres.length - 1] ?? 0;
      const sweepX = first - height * 0.4 + (last - first + height * 0.8) * sweepT;
      const reach = height * REACH;
      // On touch, scrolling carries the lens through the word as it leaves.
      const scrolled = canHover ? 0 : window.scrollY / Math.max(1, height * 2.4);
      const scrollX = first + (last - first) * scrolled;

      let shift = 0;
      letters.forEach((letter, i) => {
        const cx = (centres[i] ?? 0) - window.scrollX;
        let strength = 0;
        if (sweeping) {
          strength = Math.max(0, 1 - Math.abs(cx + window.scrollX - sweepX) / (height * 0.5));
        }
        if (scrolled > 0 && scrolled < 1.2) {
          strength = Math.max(strength, Math.max(0, 1 - Math.abs(cx - scrollX) / (height * 0.7)));
        }
        if (pointer) {
          const cy = top - window.scrollY + height / 2;
          const dist = Math.hypot(pointer.x - cx, (pointer.y - cy) * 0.6);
          strength = Math.max(strength, Math.max(0, 1 - dist / reach));
        }
        const target = REST + (peak - REST) * strength * strength * (3 - 2 * strength);
        const value = current[i] ?? REST;
        const next = value + (target - value) * EASE;
        if (Math.abs(next - value) > 0.5 || Math.abs(target - next) > 1) moving = true;
        current[i] = next;
        letter.style.fontWeight = String(Math.round(next));

        const slot = slots[i];
        if (slot) slot.style.transform = shift ? `translateX(${shift.toFixed(2)}px)` : "";
        const rest = restWidths[i] ?? 0;
        shift += ((peakWidths[i] ?? rest) - rest) * ((next - REST) / (PEAK - REST));
      });

      if (moving || sweeping || now < sweepStart) {
        frame = requestAnimationFrame(tick);
      } else {
        running = false;
      }
    };

    const wake = () => {
      if (running) return;
      running = true;
      frame = requestAnimationFrame(tick);
    };

    const onPointer = (e: PointerEvent) => {
      if (e.pointerType !== "mouse") return;
      pointer = { x: e.clientX, y: e.clientY };
      wake();
    };
    const onLeave = () => {
      pointer = null;
      wake();
    };
    const onTouch = (e: PointerEvent) => {
      if (e.pointerType === "mouse") return;
      pointer = { x: e.clientX, y: e.clientY };
      wake();
    };
    const onScroll = () => {
      if (window.scrollY < height * 3.2) wake();
    };
    let lastWidth = window.innerWidth;
    const onResize = () => {
      if (window.innerWidth === lastWidth) return;
      lastWidth = window.innerWidth;
      sweepStart = Number.POSITIVE_INFINITY;
      measure();
    };

    let cancelled = false;
    void document.fonts.ready.then(() => {
      if (cancelled) return;
      measure();
      if (canHover) wake();
    });

    if (canHover) {
      window.addEventListener("pointermove", onPointer, { passive: true });
      document.documentElement.addEventListener("pointerleave", onLeave);
    } else {
      root.addEventListener("pointerdown", onTouch, { passive: true });
      root.addEventListener("pointermove", onTouch, { passive: true });
      root.addEventListener("pointerup", onLeave, { passive: true });
      root.addEventListener("pointercancel", onLeave, { passive: true });
      window.addEventListener("scroll", onScroll, { passive: true });
    }
    window.addEventListener("resize", onResize);

    return () => {
      cancelled = true;
      cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", onPointer);
      document.documentElement.removeEventListener("pointerleave", onLeave);
      root.removeEventListener("pointerdown", onTouch);
      root.removeEventListener("pointermove", onTouch);
      root.removeEventListener("pointerup", onLeave);
      root.removeEventListener("pointercancel", onLeave);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  return (
    <span ref={rootRef} className="flex w-fit touch-pan-y">
      <span className="sr-only">{WORD}</span>
      {Array.from(WORD).map((letter, i) => (
        <span key={i} className="word-mask letter-slot" style={{ width: `${WIDTHS[i]}em` }} aria-hidden>
          <span data-letter className="rise" style={{ "--d": `${80 + i * 34}ms`, fontWeight: REST } as React.CSSProperties}>
            {letter}
          </span>
        </span>
      ))}
    </span>
  );
}
