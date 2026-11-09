# Motion and UX upgrade: audit and plan

Status: **awaiting approval** (2026-11-09). Nothing below is built yet.

## Baseline (measured 2026-11-09, production build, before any change)

| Lighthouse mobile | Run 1 | Run 2 |
| --- | --- | --- |
| Performance | 83 | 80 |
| Accessibility / Best practices / SEO | 100 / 100 / 100 | 100 / 100 / 100 |
| LCP | 3.55 s | 3.72 s |
| CLS | 0.000 | 0.000 |
| TBT | 267 ms | 318 ms |
| Benchmark index | 2267 | 2113 |

LCP element: the hero lede `<p class="lede">`. TTFB 13%, render delay 87% (3.08 s).
Main-thread work: 2.9 s. Baseline screenshots (375/768/1440/1920, normal and reduced
motion) live in the session scratchpad under `before/`.

## Audit, most severe first

### Critical
1. **Performance is already under the 95 target.** LCP lands at ~3.5 s with nearly all of it
   render delay, and the main thread does 2.9 s of work on load. The likely culprits are the
   hero's own JS (LogField canvas + NoticingWord) competing with the first paint, and a
   font-swap repaint of the lede. This has to be fixed first, because every animation added
   to the hero makes it worse.

### Major
2. **One entrance for everything.** About 30 blocks use the same `Reveal kind="fade"`
   (opacity + 14px rise), and every title uses the same masked rise. That's the "generic
   fade-up on everything" the brief bans. Only Stack (`write`) and Journey (view timeline)
   move in a way that belongs to the pad.
3. **The contact handoff is a hard cut.** The page goes from paper to solid pen blue with no
   transition. It's the biggest colour event on the site and nothing marks it.
4. **Mobile chart labels collide.** At 375px, ThreatWatch's `u20` and `u13` labels run
   together into "2013", which reads as a year, and the cutoff line clips "Flagged" to "Flaggec".
5. **Plate drift crops the screenshots.** `plate-shift` uses `margin-block: -2%` with a
   ±3% drift. At 1920 the AirPulse and TSSPL screenshots lose their top bar, which goes
   against the comment saying it "crops a sliver".
6. **Every project ends off-site.** There is no deep link to one project and no way to share
   one.
7. **Project visuals don't respond to scroll.** The chart and the report flow play once
   and then sit there. Nothing pauses offscreen, and only the chart can be replayed
   (through its radio buttons).

### Minor
8. On mobile, the hero's "out of place" note sits on top of a log line.
9. The nav marker is a plain box underline, and the pen never shows up in it.
10. Buttons only scale on press. The outline button only changes border colour on hover, and
    there is no keyboard-only press state.
11. The 404 and error pages are static apart from the field.
12. Margin labels just appear. On a pad, these are the handwritten part.

Scans: `anti_slop_scan` and `check_component_coherence` are clean. `audit_motion` flags 19,
but nearly all are false positives: it reads `--ease-in-out-soft` as `ease-in`, and
`scaleX(0)`/`scaleY(0)` are stroke draws rather than pops. The real ones are the 720 ms and
1180 ms chart delays, which are earned because they're sequenced storytelling, and the
`dot-mark` `scale(0)`, which I'll change to start at 0.4 with opacity.

## Motion system (built first, in its own commit)

**Durations.** I'll keep the existing scale (`--dur-feedback` 160 · `exit` 220 · `state` 320 ·
`draw` 480 · `reveal` 560 · `wipe` 800 · `--step` 36) and add one token:
`--dur-morph: 420ms` for view-transition morphs.

**Easing.** I'll keep `--ease-out-soft` and `--ease-in-out-soft` and add `--ease-pen:
cubic-bezier(0.55, 0, 0.25, 1)`, used only for drawn strokes. A pen accelerates off the
start and decelerates into the end, more than a UI ease does.

**Springs** (`src/lib/motion.ts`):
- `marker`: the existing values, 420/36/0.6.
- `press`: 700/32/0.5, for keys.
- `lift`: 260/26/0.8, for plate tilt and shadow.
- `snap`: 520/30/0.6, for the palette and the shortcut sheet.

**Stagger rule.** Each item waits `--step` × index, and the index is capped at 8. A group never
takes longer than 288 ms to start its last item. Longer lists reveal by row group.

**Primitives:**
- `<PenMark kind="underline | ring | tick | arrow | strike">`. These are seeded, slightly
  wobbly SVG paths built from the existing `lib/ring.ts`, drawn with `pathLength=1` and
  dashoffset. Triggers: `data-reveal="mark"` (the shared observer), a hover/focus parent, or
  an imperative `data-ring`. Under reduced motion they render fully drawn. Every annotation
  on the site uses this one component.
- `data-reveal` gains `title-scroll`, `label-write` and `mark`. `fade` stays only where nothing
  better fits, and I'll aim for under 8 uses.
- `useInView(ref, {pauseOffscreen})`, shared by the canvases and the project visuals. It also
  pauses when `document.hidden`.

**Guardrails.**
- Only transform, opacity, clip-path, filter and stroke-dashoffset get animated.
- Hover motion sits behind `(hover: hover) and (pointer: fine)`.
- Every hidden start state stays inside `prefers-reduced-motion: no-preference`, which
  is the current pattern.
- Motion stays lazy. No new runtime dependencies: view transitions come from React's built-in
  `<ViewTransition>`, and the palette and shortcut sheet use native `<dialog>`.

## Per-section spec

| # | Section | What moves | Trigger | Tokens | Reduced motion | Concept |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Load | The grid opacity settles from 0.4 to 1. The margin rule draws (already there). The headline rises (already there). The lens wakes on "notices." The ring circles the odd entry. Total ≤ 1.2 s. The lede and CTA are painted at first paint and never animated. | load | reveal, draw, pen | All of it is static on arrival | The pad gets its first mark |
| 2 | Hero | Idle breathing in LogField: a ±0.06 alpha drift on 2–3 lines, at most once every 4 s. The ring redraws when the page finds a new anomaly (a retrace of the old ring, then a fresh one). Click-to-fix ripples stay. Pointer parallax: grid 2px, field 4px, headline 6px, only with a fine pointer. The canvas pauses offscreen and in hidden tabs. | pointer, rAF while active | draw, pen | No breathing, no parallax, the ring already drawn | Noticing |
| 3 | Section titles | Masked word rise on a `view()` timeline over a short range (entry 10% to 45%), so a title has finished before it reaches reading position. The IO one-shot stays as the fallback. The margin label writes in letter by letter with a clip from left to right. | scroll | wipe range, step | Static | Written in the margin |
| 4 | About | Ballpoint underlines draw under "a stream of messy signals", "one person who needs to know what matters" and "keep the logic pure". The pencil ring circles "the chart on this page still shows the third". "Exploring right now" items get a pen tick drawn in, one after another. | mark observer | draw, step | Marks already drawn | Annotating |
| 5 | Projects | A hand-numbered index (01 to 05) sits in the margin as a drawn numeral above the date, and its stroke draws on entry. Plates tilt with the pointer (≤3°, `lift` spring) with a paper shadow that deepens as they lift. The chart, demo and report flow play in view, pause offscreen, and get a "Replay" control. The plate crop gets fixed. "Also on GitHub" rows slide in a pen-drawn arrow on hover and focus. | mark observer, pointer, IO | draw, lift | No tilt, visuals already finished, Replay still works | A pinned sheet, numbered |
| 5b | Case studies | `/work/[slug]` routes, one per project. Home → detail morphs the plate (or chart/demo frame) and title through `<ViewTransition name>`. Back reverses it. Esc and the Back link both work. Focus goes to the `<h1>` on arrival and back to the link that opened it. | navigation | morph, exit | Instant swap | Turning to that page |
| 6 | Stack | Ink items: the existing clip write gets a 1px pen stroke that leads the reveal like a nib. Pencil items: a dashed sketch underline that redraws slightly differently on hover (a seeded wobble, ~2px). | mark, hover | state, pen | Static underline | Ink vs pencil |
| 7 | Journey | A nib dot (pen-coloured, 7px) rides the existing scroll line on the same view timeline. Milestone dots stay hollow until the nib passes, then press in (scale 0.4 → 1.15 → 1, plus a small paper dent shadow). | scroll | linear on scroll | Line and dots shown complete | The line being drawn |
| 8 | Contact | Ink flood: a scroll-driven `clip-path` on the footer, from a blot at the margin rule to full bleed, over the last ~60vh before Contact. When copied, a red-pencil "copied" stamp draws at a −4° rotation next to the address, and the ring around the address stays. | scroll, click | flood on scroll, draw | Solid footer, the stamp just appears | Ink soaking the page |
| 9 | Nav | The marker becomes a pen stroke (an SVG path with a slight wobble) on the existing spring. Mobile menu: a page flip over the top binding (rotateX from −100° to 0, origin at the top, perspective 1200px), the way a pad turns. ⌘K / Ctrl+K / "/" opens a palette (jump to a section or project, copy the email, open GitHub/X/Instagram). "?" opens the shortcut sheet. | key, click | snap, exit | Opens instantly | The pad's binding |
| 10 | Micro-interactions | Buttons: a key press (translateY 2px + shadow collapse on the `press` spring), with matching `:active` and keyboard (Space/Enter down) states. Links: a drawn underline grows from the cursor side. Every control gets defined hover, focus-visible (on paper and on pen), pressed and disabled states. | pointer, key | feedback | Colour change only | Tactile |
| 11 | 404 / error | 404: the field is empty, the ring searches 2–3 positions, finds nothing, and writes "nothing here". Error: one log line breaks, a pencil strike goes through it, and the Retry button shows a redraw. | load | draw | Final frame shown | Noticing absence and failure |

## Cuts and swaps (proposed)

- **Preview card on "Also on GitHub" hover: cut.** The three minor projects have no
  screenshots, and making them up would break the honesty rule. A card holding only the note
  would repeat the row it sits on. The drawn arrow stays.
- **Page-flip menu: kept, but as a top-bound pad flip** (rotateX) instead of a book flip
  (rotateY), because a computation pad turns over its top binding.

## Order of work (one commit each, with typecheck, lint, build, and a browser check at four widths with reduced motion on)

0. Fix performance (LCP/main thread) and bugs 4, 5 and 8, then build the motion system and the primitives.
1. Load sequence and hero
2. Section titles and margin labels
3. About
4. Projects (index, tilt, in-view visuals, GitHub rows)
5. Case-study routes and view transitions
6. Stack
7. Journey
8. Contact flood and copied stamp
9. Nav: pen marker, pad-flip menu, palette, shortcut sheet
10. Micro-interaction sweep
11. 404 and error
12. Final: Lighthouse before/after at a similar benchmark index and under CPU load, a scroll recording, and the cuts list
