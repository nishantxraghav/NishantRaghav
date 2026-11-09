"use client";

import { useCallback, useDeferredValue, useEffect, useId, useMemo, useRef, useState } from "react";
import { detectDistortions, markRuns, tidy } from "@/lib/detect-distortions";

const SAMPLES = [
  "I always ruin everything and everyone knows it.",
  "They must think I'm an idiot. I know they hate me.",
  "I should be further along by now. I'll never catch up.",
];

const FIRST = SAMPLES[0] ?? "";
const TYPE_MS = 30;

/** Lume's real detector, running in the browser. Nothing leaves the page. */
export function DistortionDemo() {
  const [text, setText] = useState(FIRST);
  const [playing, setPlaying] = useState(false);
  const deferred = useDeferredValue(text);
  const inputId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const touched = useRef(false);

  /** Any touch ends the demo at once, with the full example in place. */
  const stop = useCallback(() => {
    if (touched.current) return;
    touched.current = true;
    clearTimeout(timer.current);
    if (resultsRef.current) resultsRef.current.style.minHeight = "";
    setPlaying((was) => {
      if (was) setText(FIRST);
      return false;
    });
  }, []);

  useEffect(() => {
    const root = rootRef.current;
    if (!root || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const type = (length: number) => {
      setText(FIRST.slice(0, length));
      if (length < FIRST.length) {
        timer.current = setTimeout(() => type(length + 1), TYPE_MS);
        return;
      }
      setPlaying(false);
      if (resultsRef.current) resultsRef.current.style.minHeight = "";
    };

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting) return;
        observer.disconnect();
        if (touched.current) return;
        // Hold the finished height, so the page below doesn't move while it plays.
        const results = resultsRef.current;
        if (results) results.style.minHeight = `${results.offsetHeight}px`;
        setPlaying(true);
        type(1);
      },
      { threshold: 0.55 },
    );
    observer.observe(root);
    return () => {
      observer.disconnect();
      clearTimeout(timer.current);
    };
  }, []);

  const input = useMemo(() => tidy(deferred), [deferred]);
  const results = useMemo(() => detectDistortions(deferred), [deferred]);
  const runs = useMemo(() => markRuns(input, results.flatMap((r) => r.spans)), [input, results]);

  return (
    <div
      ref={rootRef}
      onPointerDownCapture={stop}
      onFocusCapture={stop}
      onKeyDownCapture={stop}
      className="border border-ink bg-paper-raised"
    >
      <div className="flex items-baseline justify-between gap-4 border-b border-ink px-4 py-2">
        <p className="tag">distortionDetector.js</p>
        <p className="tag text-dim">{playing ? "Playing example 1" : "Runs in your browser"}</p>
      </div>

      <div className="p-4 sm:p-5">
        <label htmlFor={inputId} className="body-copy block font-medium">
          Type a sentence the way you&apos;d say it to yourself
        </label>
        <textarea
          id={inputId}
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={2}
          maxLength={240}
          className="body-copy mt-2 w-full resize-none border border-rule bg-paper-raised p-3 outline-offset-0 focus:border-pen"
        />
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
          {SAMPLES.map((sample, i) => (
            <button
              key={sample}
              type="button"
              onClick={() => setText(sample)}
              className="tag link-pen min-h-6 cursor-pointer text-pen"
              aria-label={`Use example ${i + 1}: ${sample}`}
            >
              Example {i + 1}
            </button>
          ))}
        </div>

        <div ref={resultsRef} aria-live={playing ? "off" : "polite"} className="mt-5 min-h-[11.5rem]">
          {!input ? (
            <p className="body-copy text-dim">Waiting for a sentence.</p>
          ) : (
            <>
              <p className="body-copy">
                {runs.map((run, i) =>
                  run.flagged ? (
                    <mark key={i} className="bg-transparent text-pencil underline decoration-pencil decoration-[1.5px] underline-offset-4">
                      {run.text}
                    </mark>
                  ) : (
                    <span key={i}>{run.text}</span>
                  ),
                )}
              </p>

              {results.length === 0 ? (
                <p className="body-copy mt-4 text-dim">
                  No pattern matched. That can mean a clear thought, or a phrasing the 67 rules
                  don&apos;t know.
                </p>
              ) : (
                <ul className="mt-4 space-y-3">
                  {results.map((r) => (
                    <li key={r.id} className="result-in border-t border-rule pt-3">
                      <p className="flex items-baseline justify-between gap-3 text-[0.9375rem] font-medium">
                        {r.name}
                        <span className="tag shrink-0 font-normal text-dim">weight {r.weight}</span>
                      </p>
                      <p className="body-copy mt-1 text-dim">{r.reframe}</p>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </div>
      </div>

      <p className="tag border-t border-rule px-4 py-2 text-dim sm:px-5">
        A pattern matcher, not support. In India, iCall counsellors are on{" "}
        <a href="tel:+919152987821" className="link-pen text-ink">
          9152987821
        </a>
        .
      </p>
    </div>
  );
}
