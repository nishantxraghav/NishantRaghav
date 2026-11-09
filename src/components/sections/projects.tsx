import { ArrowUpRight } from "lucide-react";
import { ProjectEntry } from "@/components/projects/project-entry";
import { Reveal } from "@/components/ui/reveal";
import { Section } from "@/components/ui/section";
import { minorProjects, projects } from "@/content/projects";

export function Projects() {
  return (
    <Section id="work" label="Selected work" title="Five things that notice.">
      <div className="space-y-24 lg:space-y-36">
        {projects.map((project) => (
          <ProjectEntry key={project.slug} project={project} />
        ))}

        <Reveal>
          <h3 className="tag border-b border-ink pb-1 text-dim">Also on GitHub</h3>
          <ul>
            {minorProjects.map((p) => (
              <li key={p.name} className="border-b border-rule">
                <a
                  href={p.href}
                  target="_blank"
                  rel="noreferrer"
                  className="group grid gap-x-6 gap-y-0.5 py-3 transition-colors duration-150 hover:text-pen md:grid-cols-12"
                >
                  <span className="flex items-center gap-1 font-medium md:col-span-4">
                    {p.name}
                    <ArrowUpRight aria-hidden size={15} className="opacity-0 transition-opacity duration-150 group-hover:opacity-100 group-focus-visible:opacity-100" />
                  </span>
                  <span className="text-[0.9375rem] md:col-span-5">{p.note}</span>
                  <span className="tag text-dim md:col-span-3 md:text-right">{p.tech}</span>
                </a>
              </li>
            ))}
          </ul>
        </Reveal>
      </div>
    </Section>
  );
}
