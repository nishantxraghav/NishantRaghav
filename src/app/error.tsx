"use client";

import { LogField } from "@/components/hero/log-field";

export default function ErrorPage({ retry }: { error: unknown; retry: () => void }) {
  return (
    <main className="relative flex min-h-dvh flex-col justify-end px-[var(--gutter)] pb-12 pt-[var(--nav-h)] lg:pl-[var(--page-left)]">
      <span aria-hidden className="margin-rule hidden lg:block" />
      <LogField variant="broken" />
      <div className="relative">
        <p className="margin-label">Error</p>
        <h1 data-field-bottom className="display mt-2 text-[clamp(3.5rem,12vw,10rem)] text-pencil">
          This page failed to load.
        </h1>
        <p className="lede mt-6 max-w-[34rem]">Reload it to try again.</p>
        <button
          type="button"
          onClick={() => retry()}
          className="pressable mt-6 inline-flex min-h-12 cursor-pointer items-center bg-pen px-5 text-[0.9375rem] font-medium text-paper hover:bg-pen-deep"
        >
          Reload the page
        </button>
      </div>
    </main>
  );
}
