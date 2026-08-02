import { Clock, FileText, Route } from "lucide-react"

import { Header } from "@/components/layout/header"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { ROLE_ZONES, type UserRole } from "@/lib/ums-roles"

function titleFromSegment(segment: string) {
  return segment
    .replace(/\[|\]/g, "")
    .replace(/[-_]/g, " ")
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ")
}

function breadcrumbsForUrl(url: string) {
  const parts = url.split("/").filter(Boolean)

  return parts.map((part, index) => ({
    href: `/${parts.slice(0, index + 1).join("/")}`,
    title: titleFromSegment(part),
  }))
}

type PlannedWorkflowPageProps = {
  role: UserRole
  title: string
  description: string
  path: string
  items?: string[]
}

export function PlannedWorkflowPage({
  role,
  title,
  description,
  path,
  items = [
    "Connect role-aware API data.",
    "Replace placeholder cards with workflow tables or forms.",
    "Add status, empty, loading, and error states.",
  ],
}: PlannedWorkflowPageProps) {
  const zone = ROLE_ZONES[role]

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={breadcrumbsForUrl(path)} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-3">
            <span className="inline-flex h-6 w-fit items-center rounded-full border border-border bg-background px-2.5 text-xs font-medium text-muted-foreground">
              {zone.label} Zone
            </span>
            <div className="space-y-2">
              <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                {title}
              </h1>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                {description}
              </p>
            </div>
          </div>
          <div className="rounded-lg border border-border bg-background px-4 py-3 text-sm text-muted-foreground lg:max-w-sm">
            <p className="font-medium text-foreground">Planned Route</p>
            <p className="mt-1 font-mono text-xs">{path}</p>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="flex flex-row items-start gap-3">
              <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                <FileText className="size-5" />
              </span>
              <div className="space-y-1">
                <CardTitle>{title}</CardTitle>
                <CardDescription>{description}</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <p>
                This page is intentionally stubbed from the updated portal plan.
                It reserves the frontend route now, while the real data model,
                permissions, and API workflow can be filled in later.
              </p>
              <div className="grid gap-2 sm:grid-cols-2">
                <div className="rounded-lg border border-border bg-background p-3">
                  <p className="font-medium text-foreground">Required Role</p>
                  <p className="mt-1">{zone.shortLabel}</p>
                </div>
                <div className="rounded-lg border border-border bg-background p-3">
                  <p className="font-medium text-foreground">Status</p>
                  <p className="mt-1">Placeholder route</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">Next Implementation</CardTitle>
              <CardDescription>
                Dummy checklist for the real workflow pass.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {items.map((item) => (
                <div key={item} className="flex gap-2 text-muted-foreground">
                  <Clock className="mt-0.5 size-4 shrink-0 text-amber-600" />
                  <p>{item}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </section>

        <Card className="border-border/70 bg-card/95 shadow-sm">
          <CardHeader className="flex flex-row items-start gap-3">
            <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
              <Route className="size-5" />
            </span>
            <div className="space-y-1">
              <CardTitle className="text-base">Plan Alignment</CardTitle>
              <CardDescription>{zone.scope}</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            This stub exists so routing, navigation, and role boundaries can be
            tested before the backend endpoints are wired.
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
