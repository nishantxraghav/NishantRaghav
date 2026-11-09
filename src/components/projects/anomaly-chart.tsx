"use client";

import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { DETECTORS, SCORES, type Detector } from "@/content/anomaly-scores";

const TOP = 3;

function rank(detector: Detector) {
  const values = SCORES.map((s) => s[detector]);
  const min = Math.min(...values);
  const max = Math.max(...values);
  // Rank-based height for the SVM, whose scores bunch tightly around zero.
  const ordered = [...SCORES].sort((a, b) => b[detector] - a[detector]);
  const position = new Map(ordered.map((s, i) => [s.user, i]));
  const height = (value: number, place: number) =>
    detector === "oneClassSvm" ? 1 - place / SCORES.length : (value - min) / (max - min);
  return { ordered, position, height };
}

/** The pipeline's real scores. Switching detector re-ranks the same twenty users. */
export function AnomalyChart() {
  const [detector, setDetector] = useState<Detector>("isolationForest");
  const { ordered, position, height } = useMemo(() => rank(detector), [detector]);
  const rootRef = useRef<HTMLElement>(null);
  const [stage, setStage] = useState<"waiting" | "playing" | "settled">("waiting");

  // Bars grow in rank order, the cut-off draws, then the planted users show up in red.
  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting) return;
        observer.disconnect();
        setStage("playing");
        timer = setTimeout(() => setStage("settled"), 1700);
      },
      { threshold: 0.35 },
    );
    observer.observe(root);
    return () => {
      observer.disconnect();
      clearTimeout(timer);
    };
  }, []);

  const planted = ordered.filter((s) => s.planted);
  const caught = planted.filter((s) => (position.get(s.user) ?? 99) < TOP).length;
  const lowest = planted[planted.length - 1];
  const lowestRank = lowest ? (position.get(lowest.user) ?? 0) + 1 : 0;
  const label = DETECTORS.find((d) => d.id === detector)?.label ?? "";

  return (
    <figure ref={rootRef} data-stage={stage} className="chart border border-ink bg-paper-raised">
      <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 border-b border-ink px-4 py-2">
        <p className="tag">anomaly_scores.csv, twenty simulated users</p>
        <fieldset className="flex flex-wrap gap-x-4">
          <legend className="sr-only">Detector</legend>
          {DETECTORS.map((d) => (
            <label key={d.id} className="tag flex min-h-6 cursor-pointer items-center gap-1.5">
              <input
                type="radio"
                name="detector"
                value={d.id}
                checked={detector === d.id}
                onChange={() => setDetector(d.id)}
                className="size-3 cursor-pointer accent-pen"
              />
              {d.label}
            </label>
          ))}
        </fieldset>
      </div>

      <div className="px-4 pb-2 pt-8 sm:px-5">
        <div className="relative h-52 sm:h-64" aria-hidden>
          {/* The analyst's cut-off: only the first three get looked at. */}
          <div
            className="chart-cutoff absolute inset-y-0 left-0 border-r border-dashed border-ink"
            style={{ width: `${(TOP / SCORES.length) * 100}%` }}
          >
            <span className="chart-red tag absolute -top-6 left-0 whitespace-nowrap text-dim">Flagged</span>
          </div>

          {SCORES.map((s) => {
            const place = position.get(s.user) ?? 0;
            const h = Math.max(0.04, height(s[detector], place));
            return (
              <div
                key={s.user}
                className="rank-bar absolute inset-y-0 left-0 flex items-end"
                style={{
                  width: `${100 / SCORES.length}%`,
                  transform: `translateX(${place * 100}%)`,
                }}
              >
                <span
                  className="bar-fill relative mx-auto block h-full w-[46%] origin-bottom bg-pen"
                  style={{ "--h": h, "--place": place } as CSSProperties}
                >
                  {s.planted ? <span className="chart-red absolute inset-0 bg-pencil" /> : null}
                </span>
                {s.planted ? (
                  <span className="chart-red tag absolute left-1/2 top-full -translate-x-1/2 text-pencil max-sm:text-[0.625rem]">
                    <span className="max-sm:hidden">u</span>
                    {s.user.replace("user", "")}
                  </span>
                ) : null}
              </div>
            );
          })}
        </div>
        <div className="h-7 border-t border-ink" />
      </div>

      <figcaption className="body-copy border-t border-rule px-4 py-3 sm:px-5">
        <span key={detector} className="swap-in font-medium">
          {label}: {caught} of {planted.length} planted insiders flagged.
        </span>{" "}
        <span className="text-dim">
          Red bars are the planted users, and the lowest ranks {lowestRank} of {SCORES.length}.
          Bar height is relative to each detector&apos;s own scale.
        </span>
        <span className="sr-only">
          Ranking: {ordered.map((s, i) => `${i + 1}. ${s.user}${s.planted ? " (planted)" : ""}`).join(", ")}.
        </span>
      </figcaption>
    </figure>
  );
}
