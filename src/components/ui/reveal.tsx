import type { CSSProperties, ReactNode } from "react";

type RevealProps = {
  children: ReactNode;
  className?: string;
  /** Delay in milliseconds, for a short stagger between neighbours. */
  delay?: number;
  /** Use "p" for text and "li", "ul" or "ol" inside lists, so the markup stays valid. */
  as?: "div" | "p" | "li" | "ul" | "ol";
  /** How it arrives. The styles live in globals.css under [data-reveal]. */
  kind?: "fade" | "write" | "list";
};

/**
 * One-shot scroll reveal. A plain server element: RevealObserver flips [data-shown],
 * so a page full of these adds nothing to hydration. Hidden only when JS is present.
 */
export function Reveal({ children, className, delay = 0, as: Tag = "div", kind = "fade" }: RevealProps) {
  return (
    <Tag data-reveal={kind} className={className} style={delay ? ({ "--d": `${delay}ms` } as CSSProperties) : undefined}>
      {children}
    </Tag>
  );
}
