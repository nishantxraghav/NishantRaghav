/** Months each project started. Nothing here is inferred employment. */
export type Milestone = { date: string; title: string; note: string; href?: string };

const repo = (name: string) => `https://github.com/nishantxraghav/${name}`;

export const journey: Milestone[] = [
  {
    date: "2025-12",
    title: "Heart Disease Predictor",
    note: "First machine learning project: KNN, decision tree and random forest compared in a notebook.",
    href: repo("Heart-Disease-Predictor"),
  },
  {
    date: "2026-01",
    title: "Insider threat pipeline",
    note: "Simulated logs, engineered features and three anomaly detectors.",
    href: repo("AI-Powered-Insider-Threat-Detection-Defense-System"),
  },
  {
    date: "2026-02",
    title: "Lume begins",
    note: "A mental wellness companion, followed the same month by a run of React and async JavaScript builds.",
    href: repo("Lume"),
  },
  {
    date: "2026-04",
    title: "AirPulse",
    note: "Redux Toolkit, lazy routes and error boundaries around a live air quality API.",
    href: repo("Airpulse"),
  },
  {
    date: "2026-06",
    title: "Arabico",
    note: "TypeScript, Tailwind design tokens and centralised motion on a multi-page cafe site.",
    href: repo("Arabico"),
  },
  {
    date: "2026-08",
    title: "Smart Time Table",
    note: "A live schedule on a pure engine, tested against every minute of the week.",
    href: repo("Smart-Time-Table"),
  },
  {
    date: "2026-10",
    title: "TSSPL_SaaS",
    note: "A full-stack background verification platform for a client: FastAPI, encrypted Aadhaar data and generated Word reports.",
  },
];
