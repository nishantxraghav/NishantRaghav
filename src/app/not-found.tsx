import Link from "next/link";
import { LogField } from "@/components/hero/log-field";

export default function NotFound() {
  return (
    <main className="relative flex min-h-dvh flex-col justify-end px-[var(--gutter)] pb-12 pt-[var(--nav-h)] lg:pl-[var(--page-left)]">
      <span aria-hidden className="margin-rule hidden lg:block" />
      <LogField variant="empty" />
      <div className="relative">
        <p className="margin-label">404</p>
        <h1 data-field-bottom className="display mt-2 text-[clamp(4rem,14vw,12rem)] text-pen">
          Nothing noticed here.
        </h1>
        <p className="lede mt-6 max-w-[34rem]">This page doesn&apos;t exist. The ring above found the gap where it should be.</p>
        <Link href="/" className="pressable mt-6 inline-flex min-h-12 items-center bg-pen px-5 text-[0.9375rem] font-medium text-paper hover:bg-pen-deep">
          Go to the home page
        </Link>
      </div>
    </main>
  );
}
