"use client";

import { Check, RotateCcw } from "lucide-react";
import { useEffect, useRef, useState, type CSSProperties } from "react";
import { ringPath } from "@/lib/ring";

/** Made-up case. Real TSSPL data never reaches this site. */
const FIELDS = [
  { label: "Candidate", value: "Demo Candidate" },
  { label: "Client", value: "Example Corp" },
  { label: "Aadhaar", value: "XXXX XXXX 0000" },
  { label: "Reference", value: "0001-DEMO-01.11.2026" },
];

const CHECKS = [
  { name: "Identity", status: "Positive-Green" },
  { name: "Address", status: "Positive-Green" },
  { name: "Education", status: "Positive-Green" },
  { name: "Employment", status: "Discrepancy-Red", odd: true },
  { name: "Court", status: "Positive-Green" },
];

const LINES = [100, 84, 92, 60];

const RING = { width: 136, height: 36 };

const at = (ms: number) => ({ "--t": `${ms}ms` }) as CSSProperties;

/** The product in one pass: a case goes in, each check gets a status, the report comes out. */
export function ReportFlow() {
  const rootRef = useRef<HTMLElement>(null);
  const [played, setPlayed] = useState(false);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting) return;
        setPlayed(true);
        observer.disconnect();
      },
      { threshold: 0.4 },
    );
    observer.observe(root);
    return () => observer.disconnect();
  }, []);

  const replay = () => {
    setPlayed(false);
    requestAnimationFrame(() => requestAnimationFrame(() => setPlayed(true)));
  };

  return (
    <figure ref={rootRef} data-played={played} className="flow border border-ink bg-paper-raised">
      <div className="flex items-center justify-between gap-4 border-b border-ink px-4 py-1.5">
        <p className="tag">case_to_report, made-up data</p>
        <button type="button" onClick={replay} className="tag pressable -mr-2 inline-flex min-h-8 cursor-pointer items-center gap-1.5 px-2 text-pen">
          <RotateCcw aria-hidden size={13} />
          Run again
        </button>
      </div>

      <div className="grid md:grid-cols-[1fr_1.15fr_1fr]">
        <div className="p-4 sm:p-5">
          <h4 className="tag text-dim">1. Case form</h4>
          <dl className="mt-3 space-y-2.5">
            {FIELDS.map((field, i) => (
              <div key={field.label}>
                <dt className="tag leading-4 text-dim">{field.label}</dt>
                <dd className="flow-wipe text-[0.9375rem] font-medium" style={at(120 + i * 170)}>
                  {field.value}
                </dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="border-t border-rule p-4 sm:p-5 md:border-l md:border-t-0">
          <h4 className="tag text-dim">2. Checks</h4>
          <ul className="mt-3 space-y-1">
            {CHECKS.map((check, i) => (
              <li key={check.name} className="flex min-h-8 items-center justify-between gap-3 text-[0.9375rem]">
                <span className="flex items-center gap-2">
                  <span className="flow-fade text-pen" style={at(840 + i * 150)}>
                    <Check aria-hidden size={14} strokeWidth={2.5} className={check.odd ? "text-pencil" : undefined} />
                  </span>
                  {check.name}
                </span>
                <span className={`flow-fade tag relative whitespace-nowrap ${check.odd ? "text-pencil" : "text-dim"}`} style={at(900 + i * 150)}>
                  {check.status}
                  {check.odd ? (
                    <svg
                      aria-hidden
                      width={RING.width}
                      height={RING.height}
                      viewBox={`0 0 ${RING.width} ${RING.height}`}
                      className="absolute right-[-14px] top-1/2 -translate-y-1/2"
                      fill="none"
                    >
                      <path
                        d={ringPath(RING.width, RING.height, 1.2)}
                        pathLength={1}
                        className="flow-ring"
                        stroke="currentColor"
                        strokeWidth={1.25}
                        style={at(1720)}
                      />
                    </svg>
                  ) : null}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="border-t border-rule p-4 sm:p-5 md:border-l md:border-t-0">
          <h4 className="tag text-dim">3. Report</h4>
          <div className="flow-page mt-3 border border-ink bg-paper p-3.5" style={at(2120)}>
            <p className="text-[0.875rem] font-medium leading-snug">Background verification report</p>
            <div aria-hidden className="mt-2.5 space-y-1.5">
              {LINES.map((w, i) => (
                <span key={i} className="flow-line block h-0.5 bg-dim/50" style={{ width: `${w}%`, ...at(2300 + i * 70) }} />
              ))}
            </div>
            <p className="flow-fade tag mt-2.5 text-pencil" style={at(2620)}>
              Colour: Red
            </p>
          </div>
          <p className="tag mt-2 text-dim">Word file, ready to send</p>
        </div>
      </div>
      <figcaption className="sr-only">
        A made-up case is entered, five checks are run and one comes back Discrepancy-Red, so the finished Word report is marked Red.
      </figcaption>
    </figure>
  );
}
