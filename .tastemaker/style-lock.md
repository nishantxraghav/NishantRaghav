# Style lock

**Thesis:** I build software that notices. Each project pulls one signal out of noise.

**Material:** an engineer's computation pad. Margin for metadata, page for content.

## Color contract

| Token | Hex | Role |
| --- | --- | --- |
| paper | #E5ECE0 | Ground |
| paper-raised | #EFF4EB | Instruments (demo, chart) |
| rule | #C6D3BF | Hairlines |
| ink | #12211C | Reading text |
| dim | #4A5B51 | Secondary text (5.99:1 on paper) |
| pen | #1C2BBE | Voice of the page (8.14:1 on paper) |
| pencil | #BE2F1C | Reserved for anomalies, warnings and the margin rule (4.82:1 on paper) |

Text-safe: ink, dim, pen and pencil on paper or paper-raised; paper on pen.
Never: pencil text on ink or pen.

## Type

- Display: Big Shoulders (variable, 400 to 840 on the hero word, 800 on headings)
- Text: Geist
- Data and metadata: Geist Mono

## Signature

The word "notices." responds to the pointer. Above it, a log file sits on the ruled lines with one entry out of place, and a red pencil ring finds it. The same ring returns around the email when it is copied. Nothing else on the page competes with these.

## Motion

CSS first, using the `--dur-*` scale and the two `--ease-*` curves. Scroll-linked work runs on CSS view timelines. Motion is loaded async and used only for the magnetic CTA, the nav marker spring and the copy label swap. One shared IntersectionObserver drives every reveal, so reveals add nothing to hydration. Hidden start states sit inside `prefers-reduced-motion: no-preference`, so reduced motion gets the finished design. The word sweep is mouse-only on load; touch starts on touch or scroll.

## Copy

No em dashes. Every claim is checked against repository source.
