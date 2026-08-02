import { Activity, Clock3, ServerCog, ShieldCheck, Wrench } from "lucide-react"

import { ThemeToggle } from "@/components/ui/theme-toggle"

const statusItems = [
  {
    title: "Services updating",
    description: "Core systems are being refreshed behind the scenes.",
    icon: ServerCog,
  },
  {
    title: "Admin access active",
    description: "Administrators can still monitor and complete the work.",
    icon: ShieldCheck,
  },
  {
    title: "Back shortly",
    description: "Public access will reopen when the window is complete.",
    icon: Clock3,
  },
]

export default function MaintenancePage() {
  return (
    <main className="bg-campus relative min-h-svh overflow-hidden px-4 py-10 text-slate-950 sm:px-6 dark:text-white">
      <div className="bg-grid pointer-events-none absolute inset-0 opacity-60 dark:opacity-30" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-teal-400 via-amber-300 to-sky-400" />
      <div className="absolute top-4 right-4 z-20 sm:top-6 sm:right-6">
        <ThemeToggle className="size-11 rounded-full border-white/70 bg-white/80 shadow-lg backdrop-blur hover:bg-white dark:border-white/15 dark:bg-white/10 dark:hover:bg-white/20" />
      </div>

      <section className="relative z-10 mx-auto grid min-h-[calc(100svh-5rem)] w-full max-w-6xl items-center gap-10 py-8 lg:grid-cols-[minmax(0,1fr)_26rem]">
        <div className="animate-fade-up">
          <div className="inline-flex items-center gap-2 rounded-full border border-amber-300/60 bg-white/75 px-3 py-1.5 text-sm font-medium text-amber-900 shadow-sm backdrop-blur dark:border-amber-300/30 dark:bg-amber-300/10 dark:text-amber-100">
            <span className="relative flex size-2.5">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-amber-400 opacity-75 motion-reduce:animate-none" />
              <span className="relative inline-flex size-2.5 rounded-full bg-amber-500" />
            </span>
            Maintenance in progress
          </div>

          <h1 className="mt-6 max-w-3xl text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl lg:text-6xl dark:text-white">
            Website is under maintenance
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600 sm:text-lg dark:text-slate-300">
            Scheduled server updates are in progress. We are keeping the portal
            protected while the maintenance window completes.
          </p>

          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            {statusItems.map(({ title, description, icon: Icon }) => (
              <div
                key={title}
                className="rounded-lg border border-white/70 bg-white/70 p-4 shadow-sm backdrop-blur dark:border-white/10 dark:bg-white/5"
              >
                <Icon
                  className="size-5 text-teal-600 dark:text-teal-300"
                  aria-hidden="true"
                />
                <p className="mt-3 text-sm font-semibold text-slate-950 dark:text-white">
                  {title}
                </p>
                <p className="mt-1 text-xs leading-5 text-slate-600 dark:text-slate-300">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="animate-fade-up relative mx-auto flex min-h-[26rem] w-full max-w-md items-center justify-center [animation-delay:120ms] motion-reduce:animate-none">
          <div className="absolute inset-0 rounded-lg border border-white/70 bg-white/60 shadow-2xl backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/70" />
          <div className="absolute inset-6 rounded-lg border border-dashed border-slate-300/80 dark:border-slate-700/80" />
          <div className="relative flex size-72 items-center justify-center">
            <div className="absolute inset-0 animate-[spin_18s_linear_infinite] rounded-full border border-amber-300/50 motion-reduce:animate-none" />
            <div className="absolute inset-8 animate-[spin_12s_linear_infinite] rounded-full border border-sky-300/50 [animation-direction:reverse] motion-reduce:animate-none" />
            <div className="relative w-56 rounded-lg border border-slate-200 bg-white p-5 shadow-xl dark:border-white/10 dark:bg-slate-900">
              <div className="animate-float-slow mx-auto flex size-16 items-center justify-center rounded-lg bg-amber-100 text-amber-700 shadow-lg motion-reduce:animate-none dark:bg-amber-300 dark:text-slate-950">
                <Wrench className="size-8" aria-hidden="true" />
              </div>
              <div className="mt-5 text-center">
                <p className="text-sm font-semibold text-slate-950 dark:text-white">
                  Update window active
                </p>
                <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-300">
                  Services are being checked and restarted in sequence.
                </p>
              </div>

              <div className="mt-5 space-y-3">
                <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-white/10">
                  <div className="h-full w-2/3 animate-pulse rounded-full bg-gradient-to-r from-teal-400 via-amber-300 to-sky-400 motion-reduce:animate-none" />
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <span className="h-1.5 animate-pulse rounded-full bg-teal-400 motion-reduce:animate-none" />
                  <span className="h-1.5 animate-pulse rounded-full bg-amber-300 [animation-delay:160ms] motion-reduce:animate-none" />
                  <span className="h-1.5 animate-pulse rounded-full bg-sky-400 [animation-delay:320ms] motion-reduce:animate-none" />
                </div>
              </div>

              <div className="mt-5 flex items-center justify-center gap-2 text-xs font-medium text-slate-500 dark:text-slate-300">
                <Activity className="size-4 animate-pulse text-teal-500 motion-reduce:animate-none" />
                Monitoring portal health
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}
