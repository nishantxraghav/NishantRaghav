import { CopyEmail } from "@/components/sections/copy-email";
import { MaskedTitle } from "@/components/ui/masked-title";
import { Reveal } from "@/components/ui/reveal";
import { profile, socialLinks } from "@/content/profile";

export function Contact() {
  const year = new Date().getFullYear();

  return (
    <footer id="contact" className="on-pen flex min-h-[calc(100dvh-var(--nav-h))] scroll-mt-[-24px] flex-col bg-pen text-paper">
      <div className="flex flex-1 flex-col px-[var(--gutter)] pb-6 pt-14 lg:pb-8 lg:pl-[var(--page-left)] lg:pt-16">
        <MaskedTitle text="Got a noisy problem?" className="contact-title display" />

        <div className="mt-auto pt-10">
          <Reveal className="max-w-[36rem]">
            <p className="lede">
              Recruiters, collaborators, or anyone with data that won&apos;t talk: write to me. {profile.collaboration}
            </p>
          </Reveal>

          <Reveal delay={80} className="mt-6">
            <CopyEmail email={profile.email} />
          </Reveal>
        </div>

        <div className="mt-10 flex flex-wrap items-end justify-between gap-x-10 gap-y-4 border-t border-paper/30 pt-3">
          <ul className="flex flex-wrap gap-x-6 gap-y-1">
            {socialLinks.map((link) => (
              <li key={link.label}>
                <a href={link.href} target="_blank" rel="noreferrer" className="link-pen inline-block py-1">
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
          <p className="tag">
            {profile.name}, {profile.location}, {year}
          </p>
        </div>
      </div>
    </footer>
  );
}
