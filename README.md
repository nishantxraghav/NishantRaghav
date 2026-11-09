# Nishant Raghav: portfolio

Personal site built with Next.js 16, TypeScript (strict), Tailwind CSS 4 and Motion. The concept is an engineer's computation pad: *I build software that notices*.

## Run it

```bash
npm install
npm run dev         # http://localhost:3000
npm run build && npm start
npm run typecheck && npm run lint
```

Copy `.env.example` to `.env.local` to set the site URL.

## Where things live

| Path | What it holds |
| --- | --- |
| `src/content/` | All copy and data: profile, projects, stack, journey. Edit these, not the components. |
| `src/components/sections/` | One file per page section |
| `src/components/hero/` | The reactive headline word |
| `src/components/projects/` | Case-study layouts, the Lume demo and the anomaly chart |
| `src/app/globals.css` | Design tokens and shared CSS |

## Adding your LinkedIn

Set `links.linkedin` in `src/content/profile.ts`. It appears in the hero, the contact section and the structured data automatically.

## Regenerating project images

Screenshots in `public/projects/` were captured from the live deployments, except `tsspl-saas.png`. That app is private and handles personal data, so its screenshot is the real frontend running locally against a stub API with made-up cases. Never replace it with a capture of the production system. Replace a file to update it, and keep `width` and `height` in `src/content/projects.ts` in step.
