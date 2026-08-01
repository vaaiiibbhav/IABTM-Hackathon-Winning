"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const ROUTES = [
  { href: "/today", label: "Today" },
  { href: "/twin", label: "Self Twin" },
  { href: "/why", label: "Why" },
] as const;

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/90 backdrop-blur-sm">
      <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-3">
        <Link
          href="/today"
          className="score-mono text-xs font-semibold tracking-[0.22em] text-foreground uppercase"
        >
          Praxis
        </Link>
        <nav className="flex items-center gap-1">
          {ROUTES.map((route) => {
            const active = pathname?.startsWith(route.href);
            return (
              <Link
                key={route.href}
                href={route.href}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm transition-colors",
                  active
                    ? "bg-secondary text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {route.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
