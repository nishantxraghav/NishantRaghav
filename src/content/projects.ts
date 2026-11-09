/**
 * Case studies. Every claim was checked against the repository source, not just
 * its README. Where the two disagree the code wins: Lume's README says Gemini,
 * but the code calls Llama on Groq. ThreatWatch's dashboard shows accuracy figures
 * that are UI constants, so they are not quoted anywhere on this site.
 */
export type ProjectVisual =
  | { kind: "demo" }
  | { kind: "chart" }
  | { kind: "image"; src: string; alt: string; width: number; height: number };

export type Project = {
  slug: string;
  name: string;
  /** Month it started. */
  started: string;
  tagline: string;
  problem: string;
  features: string[];
  implementation: string;
  stack: string[];
  /** Left out for private work, so visitors never land on a 404. */
  repo?: string;
  live?: string;
  /** Overrides the status worked out from `live`. */
  status?: string;
  /** Shows the animated case-to-report explainer under the screenshot. */
  flow?: boolean;
  /** A plain statement about current state, shown beside the links. */
  notice?: string;
  credit?: string;
  visual: ProjectVisual;
};

const repo = (name: string) => `https://github.com/nishantxraghav/${name}`;

export const projects: Project[] = [
  {
    slug: "lume",
    name: "Lume",
    started: "Feb 2026",
    tagline: "A wellness companion that reads between the lines.",
    problem:
      "A chatbot answers the words you typed, and it answers them seconds later. Someone in distress often means more than they wrote and needs a response right away.",
    features: [
      "Support appears instantly when distress patterns show up, before the model replies",
      "Ten CBT distortions detected, each with a reframing question",
      "Emotional memory that recalls what helped last time",
      "Three personalities: Calm Therapist, Strict Coach, Logical Analyst",
      "Mood logs, insights, breathing exercises and crisis helplines",
      "Android build through Capacitor",
    ],
    implementation:
      "Each message runs through local middleware first. sentimentGuard grades severity, distortionDetector scores patterns by weight, and the results shape the system prompt for Llama 3.3 on Groq. About 1,800 lines across six hand-written modules, with Supabase row-level security around mood logs and chat history.",
    stack: ["React", "Vite", "Supabase", "Groq", "ElevenLabs", "Capacitor"],
    repo: repo("Lume"),
    visual: { kind: "demo" },
  },
  {
    slug: "threatwatch",
    name: "ThreatWatch",
    started: "Jan 2026",
    tagline: "Finding the insider in a week of ordinary logs.",
    problem:
      "An insider has valid credentials, so nothing they do trips a firewall. The only trace is behaviour that drifts from normal: a few more files, a USB stick, a login after midnight.",
    features: [
      "Simulated login, file, USB and email logs with planted red-team users",
      "Features from behaviour, email NLP and graph centrality",
      "Isolation forest, one-class SVM and an autoencoder scored side by side",
      "SHAP and LIME explanations for why a user was flagged",
      "Streamlit dashboard with an interactive at-risk graph",
      "Later React dashboard with Supabase Realtime alerts and CERT scenarios",
    ],
    implementation:
      "A Python pipeline: simulate logs, engineer features, merge, train, explain. scikit-learn does the scoring, NetworkX builds the user and device graph, and SHAP opens up the isolation forest. The chart here is the pipeline's own output on twenty simulated users, misses included.",
    stack: ["Python", "scikit-learn", "SHAP", "NetworkX", "Streamlit", "React", "Supabase"],
    repo: repo("AI-Powered-Insider-Threat-Detection-Defense-System"),
    credit: "The React and Supabase dashboard was added by Saksham.",
    visual: { kind: "chart" },
  },
  {
    slug: "tsspl-saas",
    name: "TSSPL_SaaS",
    started: "Oct 2026",
    status: "Live, login required",
    flow: true,
    live: "https://tssplchecks.vercel.app",
    tagline: "From a case form to a finished background check report, in the firm's own format.",
    problem:
      "A background verification firm delivers one long Word report per candidate, in a strict house format, built from whichever checks apply. Doing that by hand is slow and easy to get wrong, and the inputs include Aadhaar numbers that need real protection.",
    features: [
      "Case entry with autosave, Save & add next and Aadhaar duplicate detection",
      "Word reports generated per candidate, with per-site report formats",
      "Bulk ZIPs with live progress, plus Excel exports in the team's tracker layout",
      "Admin, operator and viewer roles, with an audit log of every change",
    ],
    implementation:
      "FastAPI holds all the business logic, and table access is revoked for the browser's Supabase key, so every read goes through the API. Aadhaar numbers are encrypted with AES-256-GCM and matched through an HMAC. Reports are composed from Word block templates generated from a real sample, the template build fails if any of that sample's candidate data survives, and fidelity tests compare the output with the sample page by page.",
    stack: ["FastAPI", "Python", "React", "TypeScript", "Supabase", "PostgreSQL", "Playwright", "Vercel"],
    credit:
      "This is a private client system, so the live site stops at its login page and the source isn't public. The screenshot is the real interface running on made-up data.",
    visual: {
      kind: "image",
      src: "/projects/tsspl-saas.png",
      alt: "TSSPL_SaaS cases page with summary tiles for drafts, ready and red cases, above a table of demo candidates with colour and status badges.",
      width: 2160,
      height: 1350,
    },
  },
  {
    slug: "arabico",
    name: "Arabico",
    started: "Jun 2026",
    tagline: "A cafe in Janakpuri, from the first scroll to the last sip.",
    problem:
      "A cafe sells a feeling, and a listing page can't carry one. The site had to feel warm and unhurried, and still get someone to the menu and the map quickly.",
    features: [
      "Six pages: home, about, menu, gallery, reviews and contact",
      "Menu with category filters and live search across 22 items",
      "Masonry gallery with a keyboard-navigable lightbox",
      "Full-screen mobile menu and animated route changes",
    ],
    implementation:
      "Design tokens live in one place through Tailwind's @theme, and motion variants in one module, so every animation shares a curve and a rhythm. Reduced motion is handled in CSS from the start.",
    stack: ["React 19", "TypeScript", "Tailwind CSS", "Framer Motion", "Lenis"],
    repo: repo("Arabico"),
    live: "https://arabico-sable.vercel.app",
    visual: {
      kind: "image",
      src: "/projects/arabico.jpg",
      alt: "Arabico home page: the headline over a full-bleed photograph of roasted coffee beans.",
      width: 2160,
      height: 1350,
    },
  },
  {
    slug: "airpulse",
    name: "AirPulse",
    started: "Apr 2026",
    tagline: "What the air is doing, and what that means for you today.",
    problem:
      "Air quality numbers are easy to find and hard to act on, especially in a city like Delhi. A raw index tells you very little about whether to go for a run.",
    features: [
      "Debounced city search across the OpenWeatherMap geocoder",
      "Animated SVG gauge, pollutant cards and health guidance",
      "Trend charts, saved cities and a configurable auto-refresh",
      "Sidebar that becomes icons, then a bottom nav, as the screen narrows",
    ],
    implementation:
      "Redux Toolkit slices and async thunks hold state, Axios interceptors handle auth and errors, and routes load lazily. Every section sits behind its own error boundary, with loading, empty and error states designed in.",
    stack: ["React", "Redux Toolkit", "Recharts", "OpenWeatherMap API"],
    repo: repo("Airpulse"),
    live: "https://airpulse-omega.vercel.app",
    notice: "City readings are down until the deployed API key is replaced.",
    visual: {
      kind: "image",
      src: "/projects/airpulse.png",
      alt: "AirPulse home page with a city search field and cards for New Delhi, Beijing, London and New York.",
      width: 2160,
      height: 1350,
    },
  },
];

export type MinorProject = { name: string; note: string; href: string; tech: string };

export const minorProjects: MinorProject[] = [
  {
    name: "NeuroMap AI",
    note: "Turns a public GitHub profile into skill and team analytics.",
    href: repo("Interactive-3D-Knowledge-Graph-Builder"),
    tech: "JavaScript, Chart.js, GitHub API",
  },
  {
    name: "Heart Disease Predictor",
    note: "KNN, decision tree and random forest compared on patient data.",
    href: repo("Heart-Disease-Predictor"),
    tech: "Python, scikit-learn",
  },
  {
    name: "Smart Time Table",
    note: "A live schedule view on a pure engine tested against every minute of the week.",
    href: repo("Smart-Time-Table"),
    tech: "React 19, Vite, Tailwind CSS",
  },
];
