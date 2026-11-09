import { Section } from "@/components/ui/section";
import { journey } from "@/content/journey";
import { formatMonth } from "@/lib/dates";

export function Journey() {
  return (
    <Section id="journey" label="When each one started" title="How the line got here.">
      <div className="relative pl-7">
        {/* The pen line and each milestone's dot run on CSS view timelines, so scrolling drives them. */}
        <span aria-hidden className="absolute inset-y-0 left-1 w-px bg-rule" />
        <span aria-hidden className="journey-line absolute inset-y-0 left-1 w-px origin-top bg-pen" />
        <ol className="border-t border-ink">
          {journey.map((item) => (
            <li key={item.title} className="relative grid gap-x-6 gap-y-0.5 border-b border-rule py-4 md:grid-cols-12">
              <span aria-hidden className="journey-dot absolute -left-[1.625rem] top-[1.45rem] size-[9px] rounded-full border border-dim/40 bg-paper" />
              <time dateTime={item.date} className="tag text-dim md:col-span-2 md:pt-1">
                {formatMonth(item.date)}
              </time>
              <h3 className="text-[1.0625rem] font-medium md:col-span-4">
                {item.href ? (
                  <a href={item.href} target="_blank" rel="noreferrer" className="inline-block py-0.5 transition-colors duration-150 hover:text-pen">
                    {item.title}
                  </a>
                ) : (
                  item.title
                )}
              </h3>
              <p className="text-[0.9375rem] leading-snug text-dim md:col-span-6 md:pt-0.5">{item.note}</p>
            </li>
          ))}
        </ol>
      </div>
    </Section>
  );
}
