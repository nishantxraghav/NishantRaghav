"use client";

import { m, useMotionValue, useSpring } from "motion/react";
import type { PointerEvent, ReactNode } from "react";

const PULL = 0.18;
const SPRING = { stiffness: 260, damping: 22, mass: 0.4 };

/** Leans a few pixels toward the pointer. Mouse only: a finger has no hover. */
export function Magnetic({ children }: { children: ReactNode }) {
  const rawX = useMotionValue(0);
  const rawY = useMotionValue(0);
  const x = useSpring(rawX, SPRING);
  const y = useSpring(rawY, SPRING);

  const onMove = (e: PointerEvent<HTMLDivElement>) => {
    if (e.pointerType !== "mouse") return;
    const box = e.currentTarget.getBoundingClientRect();
    rawX.set((e.clientX - box.left - box.width / 2) * PULL);
    rawY.set((e.clientY - box.top - box.height / 2) * PULL);
  };

  const onLeave = () => {
    rawX.set(0);
    rawY.set(0);
  };

  return (
    <m.div className="inline-block" style={{ x, y }} onPointerMove={onMove} onPointerLeave={onLeave}>
      {children}
    </m.div>
  );
}
