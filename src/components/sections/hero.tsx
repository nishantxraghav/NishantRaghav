import { LogField } from "@/components/hero/log-field";
import { NoticingWord } from "@/components/hero/noticing-word";
import { ButtonLink } from "@/components/ui/button";
import { Magnetic } from "@/components/ui/magnetic";
import { profile, socialLinks } from "@/content/profile";

export function Hero() {
  const links = socialLinks.filter((l) => l.label === "GitHub" || l.label === "LinkedIn");

  return (
    <section id="top" className="relative flex min-h-dvh flex-col pt-[var(--nav-h)]">
      <LogField />

      <div className="sheet relative flex flex-1 flex-col justify-end lg:grid lg:grid-rows-[1fr]">
        <div className="margin-label fade-in hidden flex-col justify-end pb-3 lg:flex" style={{ "--d": "520ms" } as React.CSSProperties}>
          <p>{profile.role}</p>
          <p>{profile.location}</p>
        </div>

        <div className="flex min-w-0 flex-col justify-end pt-10 lg:pt-6">
          <h1 className="display">
            <span className="hero-line block font-medium">
              <span data-field-clear className="word-mask">
                <span className="rise">I build software that</span>
              </span>
            </span>
            <span data-field-bottom className="hero-word block text-pen">
              <NoticingWord />
            </span>
          </h1>
        </div>
      </div>

      <div className="sheet relative mt-6 pb-10 [@media(min-height:820px)]:lg:mt-8 lg:pb-14">
        <div aria-hidden />
        <div className="grid min-w-0 gap-8 md:grid-cols-12 md:gap-6">
          {/* Not animated: it's there from the first paint, so it can be read at once. */}
          <p className="lede md:col-span-6">
            <span className="lg:hidden">
              {profile.role} in {profile.location}.{" "}
            </span>
            I&apos;ve taught a model to flag insiders in log files, a chat app to catch distorted
            thinking, and a case system to turn background checks into finished reports.
          </p>
          <div
            className="fade-in flex flex-wrap items-center gap-3 md:col-span-6 md:justify-end"
            style={{ "--d": "420ms" } as React.CSSProperties}
          >
            <Magnetic>
              <ButtonLink href="#work" icon="down">
                See the projects
              </ButtonLink>
            </Magnetic>
            {links.map((link) => (
              <ButtonLink key={link.label} href={link.href} variant="outline">
                {link.label}
              </ButtonLink>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
