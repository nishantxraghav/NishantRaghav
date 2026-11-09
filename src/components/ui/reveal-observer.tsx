"use client";

import { useEffect } from "react";

/** Words on the same line rise together, wherever the title happened to wrap. */
function assignLines(el: Element) {
  const words = el.querySelectorAll<HTMLElement>(".title-inner");
  let line = -1;
  let top = Number.NEGATIVE_INFINITY;
  words.forEach((word) => {
    const y = (word.parentElement as HTMLElement).offsetTop;
    if (y > top + 4) {
      line += 1;
      top = y;
    }
    word.style.setProperty("--line", String(line));
  });
}

/** The single observer behind every [data-reveal] on the page. */
export function RevealObserver() {
  useEffect(() => {
    const targets = document.querySelectorAll<HTMLElement>("[data-reveal]");
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          const el = entry.target as HTMLElement;
          if (el.dataset.reveal === "title") assignLines(el);
          el.dataset.shown = "";
          observer.unobserve(el);
        }
      },
      { rootMargin: "0px 0px -8% 0px" },
    );
    targets.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return null;
}
