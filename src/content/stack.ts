/**
 * Ink: used in a project I've built (cross-checked against package.json,
 * requirements.txt and notebook imports).
 * Pencil: on the profile or the exploring list, with no project behind it yet.
 */
export type StackGroup = { name: string; ink: string[]; pencil: string[] };

export const stack: StackGroup[] = [
  {
    name: "Languages",
    ink: ["JavaScript", "TypeScript", "Python", "SQL", "HTML", "CSS"],
    pencil: ["C++"],
  },
  {
    name: "Frontend",
    ink: ["React", "Vite", "Tailwind CSS", "Framer Motion", "Redux Toolkit", "React Router", "Recharts", "shadcn/ui"],
    pencil: ["Next.js"],
  },
  {
    name: "Backend",
    ink: ["FastAPI", "Node.js", "Express", "Supabase Auth", "Supabase Realtime", "Streamlit"],
    pencil: ["Flask"],
  },
  {
    name: "Databases",
    ink: ["PostgreSQL", "Row-level security"],
    pencil: ["MongoDB", "FAISS", "ChromaDB"],
  },
  {
    name: "AI and machine learning",
    ink: ["scikit-learn", "pandas", "NumPy", "SHAP", "LIME", "NetworkX", "Groq API", "Prompt design"],
    pencil: ["PyTorch", "TensorFlow", "Hugging Face", "LangChain", "OpenAI API"],
  },
  {
    name: "Developer tools",
    ink: ["Git", "GitHub", "Playwright", "Capacitor", "ESLint", "Postman", "Jupyter"],
    pencil: ["GitHub Actions", "MLflow"],
  },
  {
    name: "Infrastructure",
    ink: ["Vercel", "Docker"],
    pencil: ["Google Cloud"],
  },
];
