"use client"

import Link from "next/link"
import {
  ChevronRight,
  GraduationCap,
  LayoutDashboard,
  LogIn,
  Menu,
} from "lucide-react"
import { useEffect, useState } from "react"

import { PublicBrand } from "@/components/public/public-brand"
import { Button } from "@/components/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { cn } from "@/lib/utils"
import { defaultRouteForRole, ensureValidSession } from "@/lib/auth"
import type { AuthSession } from "@/lib/auth"
import type { PublicNavGroup } from "@/lib/public-api"

export function MobileSidebar({
  navGroups,
  tone = "default",
}: {
  navGroups: PublicNavGroup[]
  tone?: "default" | "inverse"
}) {
  const [open, setOpen] = useState(false)
  const [session, setSession] = useState<AuthSession | null>(null)

  useEffect(() => {
    let isMounted = true
    ensureValidSession().then((nextSession) => {
      if (isMounted) setSession(nextSession)
    })
    return () => {
      isMounted = false
    }
  }, [])

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        render={
          <Button
            variant="outline"
            size="icon-md"
            aria-label="Open mobile menu"
            className={cn(
              "shrink-0 rounded-xl",
              tone === "inverse"
                ? "border-white/20 bg-white/10 text-white hover:bg-white/16"
                : "border-slate-200 bg-white text-slate-950 shadow-sm hover:bg-slate-100 dark:border-white/12 dark:bg-white/10 dark:text-white dark:hover:bg-white/16"
            )}
          />
        }
      >
        <Menu className="size-5" />
        <span className="sr-only">Toggle menu</span>
      </SheetTrigger>
      <SheetContent
        side="left"
        className="w-[min(88vw,22rem)] max-w-[calc(100vw-1.5rem)] gap-0 border-r border-slate-200/70 bg-white/95 p-0 backdrop-blur dark:border-white/10 dark:bg-slate-950/95"
      >
        <SheetHeader className="border-b border-slate-200/70 p-5 pr-12 text-left dark:border-white/10">
          <SheetTitle className="sr-only">Public navigation</SheetTitle>
          <PublicBrand size="md" className="max-w-full gap-3" />
        </SheetHeader>
        <div className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto p-5">
          {navGroups.map((group, index) => {
            const hasChildren = Boolean(group.children?.length)
            if (hasChildren) {
              return (
                <Collapsible key={`${group.label}-${index}`} className="w-full">
                  <CollapsibleTrigger
                    render={
                      <button className="group flex w-full items-center justify-between rounded-xl px-3 py-3 text-left text-sm font-semibold text-slate-700 transition hover:bg-slate-100 hover:text-slate-950 dark:text-slate-200 dark:hover:bg-slate-800 dark:hover:text-white" />
                    }
                  >
                    <span>{group.label}</span>
                    <ChevronRight className="size-4 text-slate-400 transition-colors group-hover:text-teal-700 dark:group-hover:text-teal-300" />
                  </CollapsibleTrigger>
                  <CollapsibleContent className="mt-1 space-y-1 border-l border-slate-200/70 pl-4 dark:border-white/10">
                    {group.children?.map((child) => (
                      <Link
                        key={child.href}
                        href={child.href}
                        onClick={() => setOpen(false)}
                        className="block rounded-lg px-3 py-2 text-sm font-medium text-slate-500 transition hover:bg-teal-50 hover:text-teal-700 dark:text-slate-400 dark:hover:bg-teal-300/10 dark:hover:text-teal-200"
                      >
                        {child.label}
                      </Link>
                    ))}
                  </CollapsibleContent>
                </Collapsible>
              )
            }

            return (
              <Link
                key={`${group.label}-${index}`}
                href={group.href}
                onClick={() => setOpen(false)}
                className="block rounded-xl px-3 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 hover:text-slate-950 dark:text-slate-200 dark:hover:bg-slate-800 dark:hover:text-white"
              >
                {group.label}
              </Link>
            )
          })}

          {navGroups.length === 0 ? (
            <p className="rounded-xl border border-dashed border-slate-200 px-3 py-4 text-sm text-slate-500 dark:border-white/10 dark:text-slate-400">
              No public navigation links are published.
            </p>
          ) : null}

          <div className="mt-auto grid gap-2 border-t border-slate-200/70 pt-5 dark:border-white/10">
            {session ? (
              <Button
                className="h-11 rounded-xl bg-teal-600 text-white hover:bg-teal-500"
                render={
                  <Link
                    href={defaultRouteForRole(session.role)}
                    onClick={() => setOpen(false)}
                  />
                }
              >
                <LayoutDashboard className="size-4" />
                Dashboard
              </Button>
            ) : (
              <>
                <Button
                  className="h-11 rounded-xl bg-teal-600 text-white hover:bg-teal-500"
                  render={<Link href="/apply" onClick={() => setOpen(false)} />}
                >
                  <GraduationCap className="size-4" />
                  Apply Now
                </Button>
                <Button
                  className="h-11 rounded-xl bg-slate-950 text-white hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
                  render={<Link href="/login" onClick={() => setOpen(false)} />}
                >
                  <LogIn className="size-4" />
                  <span>Login</span>
                </Button>
              </>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
