import { Reveal } from "@/components/ui/reveal";
import { Section } from "@/components/ui/section";
import { profile } from "@/content/profile";

export function About() {
  return (
    <Section id="about" label="About" title="Same problem, different clothes.">
      <div className="grid gap-10 lg:grid-cols-12 lg:gap-6">
        <div className="space-y-5 lg:col-span-7">
          <Reveal as="p" className="lede">
            I&apos;m a developer in New Delhi, and building things is how I spend my time. I&apos;ve gone
            from Nand2Tetris logic gates to machine learning pipelines to a full-stack platform with
            encrypted data, and I like the distance between those things.
          </Reveal>
          <Reveal as="p" delay={70} className="lede">
            The projects I keep returning to share a shape: a stream of messy signals and one person
            who needs to know what matters. An insider in a log file. Distress in a chat message.
            Bad air over a city. A candidate waiting on a background check.
          </Reveal>
          <Reveal as="p" delay={140} className="lede">
            I keep the logic pure and the interface thin. Lume&apos;s detection runs without a single
            API call. TSSPL_SaaS won&apos;t build its report templates if one value from the sample
            survives. And I leave the misses in: one of my models caught two of three planted insiders, and the chart
            on this page still shows the third.
          </Reveal>
        </div>

        <div className="lg:col-span-4 lg:col-start-9">
          <h3 className="tag text-dim">Exploring right now</h3>
          <Reveal as="ul" kind="list" className="mt-2 border-t border-ink">
            {profile.exploring.map((item, i) => (
              <li key={item} className="border-b border-rule py-2 text-[0.9375rem]" style={{ "--i": i } as React.CSSProperties}>
                {item}
              </li>
            ))}
          </Reveal>
        </div>
      </div>
    </Section>
  );
}
