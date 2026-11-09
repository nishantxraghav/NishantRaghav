"use client";

import { Menu, X } from "lucide-react";
import { m } from "motion/react";
import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import { profile } from "@/content/profile";

const SECTIONS = [
  { id: "about", label: "About" },
  { id: "work", label: "Work" },
  { id: "stack", label: "Stack" },
  { id: "journey", label: "Journey" },
  { id: "contact", label: "Contact" },
] as const;

const MARKER_SPRING = { type: "spring", stiffness: 420, damping: 36, mass: 0.6 } as const;
const CLOSE_MS = 220;

export function Nav() {
  const [active, setActive] = useState<string | null>(null);
  const [bar, setBar] = useState({ x: 0, w: 0 });
  const [scrolled, setScrolled] = useState(false);
  const listRef = useRef<HTMLUListElement>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);

  // The section crossing the middle of the viewport is the current one.
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) setActive(entry.target.id);
          else if (entry.target.id === SECTIONS[0].id && entry.boundingClientRect.top > 0) setActive(null);
        }
      },
      { rootMargin: "-50% 0px -50% 0px" },
    );
    for (const { id } of SECTIONS) {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    }
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const measure = useCallback(() => {
    const list = listRef.current;
    const link = active ? list?.querySelector<HTMLElement>(`a[href="#${active}"]`) : null;
    if (!list || !link) {
      setBar((b) => ({ ...b, w: 0 }));
      return;
    }
    const a = link.getBoundingClientRect();
    const b = list.getBoundingClientRect();
    setBar({ x: a.left - b.left, w: a.width });
  }, [active]);

  useEffect(() => {
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, [measure]);

  const openMenu = () => dialogRef.current?.showModal();
  const closeMenu = () => {
    const dialog = dialogRef.current;
    if (!dialog || dialog.dataset.closing !== undefined) return;
    dialog.dataset.closing = "";
    setTimeout(() => {
      dialog.close();
      delete dialog.dataset.closing;
    }, CLOSE_MS);
  };

  return (
    <header
      className={`fixed inset-x-0 top-0 z-40 flex h-[var(--nav-h)] items-center justify-between px-[var(--gutter)] transition-colors duration-200 ${
        scrolled ? "bg-paper shadow-[0_1px_0_var(--color-rule)]" : "bg-transparent"
      }`}
    >
      <a href="#top" className="py-2 font-mono text-[0.8125rem] tracking-tight">
        {profile.name}
      </a>

      <nav aria-label="Sections" className="hidden md:block">
        <ul ref={listRef} className="relative flex items-center gap-7">
          {SECTIONS.map(({ id, label }) => (
            <li key={id}>
              <a
                href={`#${id}`}
                aria-current={active === id ? "true" : undefined}
                className={`inline-block py-2 text-sm transition-colors duration-150 hover:text-pen ${
                  active === id ? "text-pen" : "text-ink"
                }`}
              >
                {label}
              </a>
            </li>
          ))}
          <m.span
            aria-hidden
            className="pointer-events-none absolute bottom-1 left-0 h-0.5 w-px origin-left bg-pen"
            initial={false}
            animate={{ x: bar.x, scaleX: bar.w, opacity: bar.w ? 1 : 0 }}
            transition={MARKER_SPRING}
          />
        </ul>
      </nav>

      <button
        type="button"
        onClick={openMenu}
        aria-haspopup="dialog"
        className="pressable -mr-3 flex size-12 cursor-pointer items-center justify-center md:hidden"
      >
        <Menu aria-hidden size={22} />
        <span className="sr-only">Open menu</span>
      </button>

      <dialog
        ref={dialogRef}
        className="mobile-menu on-pen"
        aria-label="Menu"
        onCancel={(e) => {
          e.preventDefault();
          closeMenu();
        }}
      >
        <div className="flex h-full flex-col px-[var(--gutter)] pb-10">
          <div className="flex h-[var(--nav-h)] items-center justify-between">
            <span className="font-mono text-[0.8125rem]">{profile.name}</span>
            <button
              type="button"
              onClick={closeMenu}
              className="pressable -mr-3 flex size-12 cursor-pointer items-center justify-center"
            >
              <X aria-hidden size={22} />
              <span className="sr-only">Close menu</span>
            </button>
          </div>
          <ul className="mt-auto">
            {SECTIONS.map(({ id, label }, i) => (
              <li key={id} className="menu-item border-t border-paper/25" style={{ "--i": i } as CSSProperties}>
                <a href={`#${id}`} onClick={closeMenu} className="display block py-3 text-[3.25rem]">
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </dialog>
    </header>
  );
}
