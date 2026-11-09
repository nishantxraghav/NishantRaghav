import type { ReactNode } from "react";
import { MaskedTitle } from "@/components/ui/masked-title";

type SectionProps = {
  id: string;
  /** What the margin says about this section. */
  label: string;
  title: string;
  children: ReactNode;
  className?: string;
};

/** A sheet row: label in the margin, heading and content on the page. */
export function Section({ id, label, title, children, className = "" }: SectionProps) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className={`sheet py-20 lg:py-32 ${className}`}>
      <p className="margin-label mb-3 lg:mb-0 lg:pt-3">{label}</p>
      <div className="min-w-0">
        <MaskedTitle id={`${id}-title`} text={title} className="display h-section" />
        <div className="mt-10 lg:mt-14">{children}</div>
      </div>
    </section>
  );
}
