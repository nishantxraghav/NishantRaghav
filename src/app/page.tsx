import { Nav } from "@/components/layout/nav";
import { About } from "@/components/sections/about";
import { Contact } from "@/components/sections/contact";
import { Hero } from "@/components/sections/hero";
import { Journey } from "@/components/sections/journey";
import { Projects } from "@/components/sections/projects";
import { Stack } from "@/components/sections/stack";
import { RevealObserver } from "@/components/ui/reveal-observer";

export default function Home() {
  return (
    <>
      <RevealObserver />
      <Nav />
      <main id="main" className="relative">
        <span aria-hidden className="margin-rule hidden lg:block" />
        <Hero />
        <About />
        <Projects />
        <Stack />
        <Journey />
      </main>
      <Contact />
    </>
  );
}
