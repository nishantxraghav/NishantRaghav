import { ArrowUpRight } from "lucide-react";
import { AnomalyChart } from "@/components/projects/anomaly-chart";
import { DistortionDemo } from "@/components/projects/distortion-demo";
import { ProjectPlate } from "@/components/projects/project-plate";
import { ReportFlow } from "@/components/projects/report-flow";
import { MaskedTitle } from "@/components/ui/masked-title";
import { Reveal } from "@/components/ui/reveal";
import type { Project } from "@/content/projects";

function ProjectLinks({ project }: { project: Project }) {
  if (!project.live && !project.repo) return null;
  return (
    <p className="flex flex-wrap gap-x-5 gap-y-1">
      {project.live ? (
        <a href={project.live} target="_blank" rel="noreferrer" className="link-pen inline-flex items-center gap-1 text-pen">
          Open the live site <ArrowUpRight aria-hidden size={15} />
        </a>
      ) : null}
      {project.repo ? (
        <a href={project.repo} target="_blank" rel="noreferrer" className="link-pen inline-flex items-center gap-1 text-pen">
          Read the code <ArrowUpRight aria-hidden size={15} />
        </a>
      ) : null}
    </p>
  );
}

function Visual({ project }: { project: Project }) {
  const { visual } = project;
  if (visual.kind === "demo") return <DistortionDemo />;
  if (visual.kind === "chart") return <AnomalyChart />;
  return (
    <ProjectPlate
      src={visual.src}
      alt={visual.alt}
      width={visual.width}
      height={visual.height}
      href={project.live}
      label={`Open ${project.name}`}
      sizes="(min-width: 1024px) 60vw, 100vw"
    />
  );
}

function Detail({ project }: { project: Project }) {
  return (
    <>
      <div>
        <h4 className="tag text-dim">The problem</h4>
        <p className="body-copy mt-1">{project.problem}</p>
      </div>
      <div>
        <h4 className="tag text-dim">How it&apos;s built</h4>
        <p className="body-copy mt-1">{project.implementation}</p>
        {project.credit ? <p className="body-copy mt-2 text-dim">{project.credit}</p> : null}
      </div>
    </>
  );
}

/**
 * Two layouts, alternated so the list never settles into a card rhythm:
 * interactive pieces sit beside their text, screenshots run wide above it.
 */
export function ProjectEntry({ project }: { project: Project }) {
  const interactive = project.visual.kind !== "image";

  return (
    <article id={project.slug} className="scroll-mt-24 border-t border-ink pt-6">
      <div className="lg:relative">
        {/* Facts for the margin. On narrow screens they sit inline above the name. */}
        <dl className="tag mb-4 flex flex-wrap gap-x-5 text-dim lg:absolute lg:right-full lg:top-0 lg:mb-0 lg:mr-[calc(var(--gutter)*2)] lg:block lg:w-[calc(var(--margin)-var(--gutter))]">
          <div className="flex gap-1.5 lg:block">
            <dt className="sr-only">Started</dt>
            <dd>{project.started}</dd>
          </div>
          <div className="flex gap-1.5 lg:block">
            <dt className="sr-only">Status</dt>
            <dd>{project.status ?? (project.live ? (project.notice ? "Deployed, feed down" : "Live") : "Source only")}</dd>
          </div>
          <div className="hidden lg:mt-5 lg:block">
            <dt className="sr-only">Stack</dt>
            {project.stack.map((tech) => (
              <dd key={tech}>{tech}</dd>
            ))}
          </div>
        </dl>

        <MaskedTitle as="h3" text={project.name} className="display h-project" />
        <Reveal delay={120}>
          <p className="lede mt-3 max-w-[38rem]">{project.tagline}</p>
        </Reveal>
      </div>

      {interactive ? (
        <div className="mt-10 grid gap-10 lg:grid-cols-12 lg:gap-6">
          <Reveal className={project.visual.kind === "chart" ? "lg:col-span-12" : "lg:col-span-7 lg:order-2"}>
            <Visual project={project} />
          </Reveal>
          <Reveal
            className={
              project.visual.kind === "chart"
                ? "grid gap-8 lg:col-span-12 lg:grid-cols-3 lg:gap-6"
                : "space-y-7 lg:col-span-5 lg:pr-8"
            }
          >
            <Detail project={project} />
            <div>
              <h4 className="tag text-dim">What it does</h4>
              <ul className="mt-1 space-y-1.5">
                {project.features.map((f) => (
                  <li key={f} className="body-copy">
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
        </div>
      ) : (
        <div className="mt-10 grid gap-8 lg:grid-cols-12 lg:gap-x-6">
          <div className="lg:col-span-9">
            <Visual project={project} />
          </div>
          <Reveal delay={100} className="lg:col-span-3">
            <h4 className="tag text-dim">What it does</h4>
            <ul className="mt-1 space-y-2.5">
              {project.features.map((f) => (
                <li key={f} className="text-[0.9375rem] leading-snug">
                  {f}
                </li>
              ))}
            </ul>
          </Reveal>
          {project.flow ? (
            <div className="lg:col-span-9">
              <ReportFlow />
            </div>
          ) : null}
          <Reveal className="grid gap-8 md:grid-cols-2 md:gap-6 lg:col-span-9">
            <Detail project={project} />
          </Reveal>
        </div>
      )}

      <Reveal className="mt-8 space-y-2">
        {project.notice ? (
          <p className="body-copy text-pencil">{project.notice}</p>
        ) : null}
        <ProjectLinks project={project} />
        <p className="tag text-dim lg:hidden">{project.stack.join(", ")}</p>
      </Reveal>
    </article>
  );
}
