import type { CSSProperties } from "react";
import { Reveal } from "@/components/ui/reveal";
import { Section } from "@/components/ui/section";
import { stack } from "@/content/stack";

const order = (i: number) => ({ "--i": i }) as CSSProperties;

/** Ink is in something built. Pencil is still being explored. */
export function Stack() {
  return (
    <Section id="stack" label="Tech stack" title="Written in ink, sketched in pencil.">
      <Reveal>
        <p className="lede max-w-[38rem]">
          <span className="font-medium">Ink</span> means I&apos;ve built with it.{" "}
          <span className="text-dim">Pencil</span> means I&apos;m exploring it, with no project behind it
          yet.
        </p>
      </Reveal>

      <dl className="mt-10 border-t border-ink">
        {stack.map((group) => (
          <Reveal key={group.name} kind="write" className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-12">
            <dt className="tag text-dim lg:col-span-3">{group.name}</dt>
            <dd className="text-[1.0625rem] leading-relaxed lg:col-span-9">
              <span className="sr-only">Built with: </span>
              {group.ink.map((item, i) => (
                <span key={item}>
                  <span className="write-ink" style={order(i)}>
                    {item}
                    {i < group.ink.length - 1 ? "," : ""}
                  </span>{" "}
                </span>
              ))}
              {group.pencil.length ? (
                <>
                  <span className="sr-only">. Exploring: </span>
                  <span aria-hidden className="write-pencil text-dim" style={order(group.ink.length)}>
                    /
                  </span>{" "}
                  {group.pencil.map((item, i) => (
                    <span key={item}>
                      <span className="write-pencil italic text-dim" style={order(group.ink.length + i)}>
                        {item}
                        {i < group.pencil.length - 1 ? "," : ""}
                      </span>{" "}
                    </span>
                  ))}
                </>
              ) : null}
            </dd>
          </Reveal>
        ))}
      </dl>
    </Section>
  );
}
