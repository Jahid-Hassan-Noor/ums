"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { ArrowRight, FileCheck2, GraduationCap, Upload } from "lucide-react"

import {
  ApplicationStatusSteps,
  applicationStatusLabel,
} from "@/components/apply/application-status-steps"
import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { loadApplyApplications, loadApplyOptions, type ApplyOptions } from "@/lib/apply"

export function ApplyDashboard() {
  const [applications, setApplications] = useState<
    Awaited<ReturnType<typeof loadApplyApplications>>
  >([])
  const [options, setOptions] = useState<ApplyOptions | null>(null)
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let active = true
    const timer = window.setTimeout(() => {
      setIsLoading(true)
      setError("")
      void Promise.all([loadApplyApplications(), loadApplyOptions()])
        .then(([data, nextOptions]) => {
          if (!active) return
          setApplications(data)
          setOptions(nextOptions)
        })
        .catch((caught) => {
          if (active) {
            setError(
              caught instanceof Error
                ? caught.message
                : "Unable to load applications."
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

  const latestApplication = applications[0]
  const documentCount = latestApplication?.documents?.length ?? 0
  const nextAction =
    latestApplication?.status === "submitted"
      ? "/apply/status"
      : "/apply/application"

  const metrics = useMemo(
    () => [
      {
        title: "Application Status",
        value: applicationStatusLabel(latestApplication?.status, options?.status_options),
        detail:
          latestApplication?.application_number || "Create a draft to begin.",
        icon: FileCheck2,
      },
      {
        title: "Programme Preferences",
        value: String(
          latestApplication?.programme_preferences?.filter(Boolean).length ?? 0
        ),
        detail: "Four preferences are required before submission.",
        icon: GraduationCap,
      },
      {
        title: "Documents",
        value: String(documentCount),
        detail: "Upload identity, academic, and scholarship files.",
        icon: Upload,
      },
    ],
    [documentCount, latestApplication, options]
  )

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/apply", title: "Apply" },
          { href: "/apply/dashboard", title: "Dashboard" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold text-teal-700 dark:text-teal-300">
              University Apply
            </p>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
              Application Dashboard
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              Continue your admission application, scholarship request, and
              document submission.
            </p>
          </div>
          <Button render={<Link href={nextAction} />}>
            {latestApplication?.status === "submitted"
              ? "View Status"
              : "Continue Form"}
            <ArrowRight className="size-4" />
          </Button>
        </section>

        {error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-200">
            {error}
          </div>
        ) : null}

        <section className="grid gap-4 md:grid-cols-3">
          {metrics.map((metric) => {
            const Icon = metric.icon
            return (
              <div
                key={metric.title}
                className="rounded-lg border border-border bg-background p-5 shadow-sm"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">
                      {metric.title}
                    </p>
                    <p className="mt-2 text-2xl font-semibold">
                      {isLoading ? "..." : metric.value}
                    </p>
                  </div>
                  <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                    <Icon className="size-5" />
                  </span>
                </div>
                <p className="mt-3 text-xs leading-5 text-muted-foreground">
                  {metric.detail}
                </p>
              </div>
            )
          })}
        </section>

        <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
          <div className="rounded-lg border border-border bg-background p-5 shadow-sm">
            <h2 className="text-base font-semibold">Application Flow</h2>
            <div className="mt-4">
              <ApplicationStatusSteps steps={options?.steps.map((step) => step.label)} />
            </div>
          </div>

          <div className="rounded-lg border border-border bg-background p-5 shadow-sm">
            <h2 className="text-base font-semibold">Quick Links</h2>
            <div className="mt-4 grid gap-2">
              {[
                { label: "Application Form", href: "/apply/application" },
                { label: "Upload Documents", href: "/apply/documents" },
                { label: "Application Status", href: "/apply/status" },
              ].map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded-lg border border-border px-3 py-2 text-sm font-medium transition hover:bg-muted"
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
