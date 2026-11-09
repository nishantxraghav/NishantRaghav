import { ArrowDown, ArrowUpRight } from "lucide-react";
import type { ReactNode } from "react";

type ButtonLinkProps = {
  href: string;
  children: ReactNode;
  variant?: "solid" | "outline";
  icon?: "down" | "external" | "none";
  className?: string;
};

const variants = {
  solid: "bg-pen text-paper hover:bg-pen-deep",
  outline: "border border-ink/30 text-ink hover:border-ink",
} as const;

export function ButtonLink({ href, children, variant = "solid", icon = "external", className = "" }: ButtonLinkProps) {
  const external = /^https?:/.test(href);
  const Icon = icon === "down" ? ArrowDown : icon === "external" ? ArrowUpRight : null;
  return (
    <a
      href={href}
      {...(external ? { target: "_blank", rel: "noreferrer" } : {})}
      className={`pressable inline-flex min-h-12 items-center gap-2 px-5 text-[0.9375rem] font-medium ${variants[variant]} ${className}`}
    >
      {children}
      {Icon ? <Icon aria-hidden size={16} strokeWidth={2} /> : null}
    </a>
  );
}
