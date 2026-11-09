"use client";

import { Check, Copy } from "lucide-react";
import { AnimatePresence, m } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { Magnetic } from "@/components/ui/magnetic";
import { ringPath } from "@/lib/ring";

const SHOWN_MS = 2400;
const SWAP = { duration: 0.16, ease: [0.23, 1, 0.32, 1] } as const;

type Ring = { width: number; height: number; d: string };

/** The address itself, plus a copy button that circles it: the hero's ring, in paper. */
export function CopyEmail({ email }: { email: string }) {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");
  const [ring, setRing] = useState<Ring | null>(null);
  const linkRef = useRef<HTMLAnchorElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => () => clearTimeout(timer.current), []);

  const copy = async () => {
    const box = linkRef.current?.getBoundingClientRect();
    try {
      await navigator.clipboard.writeText(email);
      setState("copied");
      if (box) {
        // Wide on a big screen, and never past the edge of a phone.
        const width = Math.round(box.width + 2 * Math.min(30, box.left - 4));
        const height = Math.round(box.height + 30);
        setRing({ width, height, d: ringPath(width, height, Math.random() * 6, 0.55) });
      }
    } catch {
      // Clipboard refused: select the address, so one more press copies it.
      const link = linkRef.current;
      const selection = window.getSelection();
      if (link && selection) {
        const range = document.createRange();
        range.selectNodeContents(link);
        selection.removeAllRanges();
        selection.addRange(range);
      }
      setState("failed");
    }
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setState("idle"), SHOWN_MS);
  };

  const label = state === "copied" ? "Copied" : state === "failed" ? "Address selected" : "Copy address";

  return (
    <>
      <div className="relative w-fit" data-ring={state === "copied" ? "drawn" : "ready"}>
        <a ref={linkRef} href={`mailto:${email}`} className="contact-email link-pen font-display font-semibold leading-tight">
          {email}
        </a>
        {ring ? (
          <svg
            aria-hidden
            width={ring.width}
            height={ring.height}
            viewBox={`0 0 ${ring.width} ${ring.height}`}
            className="field-ring pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
            fill="none"
          >
            <path key={ring.d} d={ring.d} pathLength={1} className="ring-path" stroke="currentColor" strokeWidth={2.5} />
          </svg>
        ) : null}
      </div>

      <div className="mt-6">
        <Magnetic>
          <button
            type="button"
            onClick={copy}
            className="pressable inline-flex min-h-12 min-w-40 cursor-pointer items-center gap-2 overflow-hidden border border-paper/40 px-5 text-[0.9375rem] hover:border-paper"
          >
            {state === "copied" ? <Check aria-hidden size={16} /> : <Copy aria-hidden size={16} />}
            <span aria-live="polite" className="relative inline-block">
              <AnimatePresence mode="popLayout" initial={false}>
                <m.span
                  key={label}
                  className="inline-block"
                  initial={{ y: 14, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  exit={{ y: -14, opacity: 0 }}
                  transition={SWAP}
                >
                  {label}
                </m.span>
              </AnimatePresence>
            </span>
          </button>
        </Magnetic>
      </div>
    </>
  );
}
