"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { GraduationCap, LayoutDashboard, LogIn } from "lucide-react"

import { MobileSidebar } from "@/components/public/public-mobile-sidebar"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/ui/theme-toggle"
import { defaultRouteForRole, ensureValidSession } from "@/lib/auth"
import type { AuthSession } from "@/lib/auth"

export function PublicHeaderActions() {
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
    <div className="flex shrink-0 items-center gap-2 sm:gap-3">
      <ThemeToggle />
      {session ? (
        <Button
          className="hidden h-9 rounded-full bg-teal-600 px-4 text-white hover:bg-teal-500 lg:inline-flex"
          render={<Link href={defaultRouteForRole(session.role)} />}
        >
          <LayoutDashboard className="size-4" />
          Dashboard
        </Button>
      ) : (
        <>
          <Button
            variant="outline"
            className="hidden h-9 rounded-full border-slate-200 bg-white px-4 text-slate-700 hover:bg-slate-100 hover:text-slate-950 dark:border-white/12 dark:bg-white/10 dark:text-slate-200 dark:hover:bg-white/16 dark:hover:text-white lg:inline-flex"
            render={<Link href="/apply" />}
          >
            <GraduationCap className="size-4" />
            Apply
          </Button>
          <Button
            className="hidden h-9 rounded-full bg-teal-600 px-4 text-white hover:bg-teal-500 lg:inline-flex"
            render={<Link href="/login" />}
          >
            <LogIn className="size-4" />
            Login
          </Button>
        </>
      )}
      <div className="lg:hidden">
        <MobileSidebar />
      </div>
    </div>
  )
}
