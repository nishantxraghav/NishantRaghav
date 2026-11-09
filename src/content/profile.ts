/**
 * Contact details and links come from the public GitHub profile and profile README.
 * `linkedin` stays null until there is a real URL: the profile README's LinkedIn
 * badge currently links nowhere. Components hide any link that is null.
 */
export const profile = {
  name: "Nishant Raghav",
  username: "nishantxraghav",
  location: "New Delhi",
  role: "Software developer",
  email: "info@nishantraghav.com",
  siteUrl: process.env.NEXT_PUBLIC_SITE_URL ?? "https://www.nishantraghav.in",
  description:
    "Nishant Raghav is a software developer in New Delhi building software that notices: anomaly detection, a CBT-aware wellness companion, and a background verification platform.",
  links: {
    github: "https://github.com/nishantxraghav",
    linkedin: null as string | null,
    x: "https://x.com/nishantxraghav",
    instagram: "https://instagram.com/_nishantraghav_",
  },
  exploring: ["LLMs", "Embeddings", "Vector databases", "C++"],
  collaboration: "Open to collaborating on open-source GenAI projects.",
} as const;

export type SocialLink = { label: string; href: string };

export const socialLinks: SocialLink[] = [
  { label: "GitHub", href: profile.links.github },
  ...(profile.links.linkedin ? [{ label: "LinkedIn", href: profile.links.linkedin }] : []),
  { label: "X", href: profile.links.x },
  { label: "Instagram", href: profile.links.instagram },
];
