"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { ArrowRight } from "lucide-react"

import { applicationStatusLabel } from "@/components/apply/application-status-steps"
import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { loadApplyApplications } from "@/lib/apply"

export function ApplyStatus() {
  const [application, setApplication] = useState<
    Awaited<ReturnType<typeof loadApplyApplications>>[number] | null
  >(null)
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let active = true
    const timer = window.setTimeout(() => {
      setIsLoading(true)
      setError("")
      void loadApplyApplications()
        .then((applications) => {
          if (active) setApplication(applications[0] ?? null)
        })
        .catch((caught) => {
          if (active) {
            setError(
              caught instanceof Error
                ? caught.message
                : "Unable to load application status."
            )
          }
        })
        .finally(() => {
          if (active) setIsLoading(false)
        })
    }, 0)
    return () => {
      active = false
      window.clearTimeout(timer)
    }
  }, [])

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/apply", title: "Apply" },
          { href: "/apply/status", title: "Status" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold text-teal-700 dark:text-teal-300">
              Application Status
            </p>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
              Review Timeline
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              Track submission, admission screening, scholarship review, and
              final decisions.
            </p>
          </div>
          <Button variant="outline" render={<Link href="/apply/application" />}>
            Open Form <ArrowRight className="size-4" />
          </Button>
        </section>

        {error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-200">
            {error}
          </div>
        ) : null}

        {!isLoading && !application ? (
          <div className="rounded-lg border border-border bg-background p-5 shadow-sm">
            <p className="text-sm text-muted-foreground">
              No application has been created yet.
            </p>
            <Button
              className="mt-4"
              render={<Link href="/apply/application" />}
            >
              Start Application
            </Button>
          </div>
        ) : null}

        {application ? (
          <section className="grid gap-5 lg:grid-cols-[22rem_minmax(0,1fr)]">
            <div className="rounded-lg border border-border bg-background p-5 shadow-sm">
              <p className="text-sm font-medium text-muted-foreground">
                Current Status
              </p>
              <p className="mt-2 text-2xl font-semibold">
                {applicationStatusLabel(application.status)}
              </p>
              <p className="mt-2 text-sm text-muted-foreground">
                {application.application_number || "Draft application"}
              </p>
              {application.review_notes ? (
                <div className="mt-4 rounded-lg border border-border bg-muted/40 p-3 text-sm">
                  {application.review_notes}
                </div>
              ) : null}
            </div>

            <div className="rounded-lg border border-border bg-background p-5 shadow-sm">
              <h2 className="text-lg font-semibold">Timeline</h2>
              <div className="mt-4 space-y-3">
                {application.status_events.length ? (
                  application.status_events.map((event) => (
                    <div
                      key={event.id}
                      className="rounded-lg border border-border p-3"
                    >
                      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                        <p className="text-sm font-medium">
                          {applicationStatusLabel(event.to_status)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(event.created_at).toLocaleString()}
                        </p>
                      </div>
                      {event.note ? (
                        <p className="mt-2 text-sm leading-6 text-muted-foreground">
                          {event.note}
                        </p>
                      ) : null}
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No status updates yet.
                  </p>
                )}
              </div>
            </div>
          </section>
        ) : null}
      </main>
    </div>
  )
}
