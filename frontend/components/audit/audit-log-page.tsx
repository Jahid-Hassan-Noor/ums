"use client"

import { FormEvent, useEffect, useState } from "react"
import {
  AlertCircle,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Loader2,
  RotateCcw,
  Search,
  UserRound,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"

type AuditRole = "admin" | "executive"

type AuditActor = {
  profile_id: number | null
  username: string
  email: string
  full_name: string
  role: string
}

type AuditEntry = {
  id: number
  action: string
  object_type: string
  object_id: string
  details: unknown
  created_at: string
  actor: AuditActor
}

type SettingChange = {
  setting: string
  previous_value: unknown
  new_value: unknown
}

type AuditDetails = {
  changed_fields?: string[]
  changes?: SettingChange[]
  high_impact?: boolean
  new_value?: unknown
  previous_value?: unknown
  reason?: string
  setting?: string
}

type Scope = {
  kind: "school" | "center" | null
  id: number | null
  code: string
  name: string
}

type AuditResponse = {
  count: number
  next: string | null
  previous: string | null
  results: AuditEntry[]
  scope?: Scope
}

type Filters = {
  search: string
  action: string
  actor: string
  object_type: string
  category: string
  date_from: string
  date_to: string
}

const emptyFilters: Filters = {
  search: "",
  action: "",
  actor: "",
  object_type: "",
  category: "",
  date_from: "",
  date_to: "",
}

function formatTimestamp(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value))
}

function buildQuery(filters: Filters, page: number) {
  const params = new URLSearchParams({ page: String(page), page_size: "25" })
  Object.entries(filters).forEach(([key, value]) => {
    if (value.trim()) {
      params.set(key, value.trim())
    }
  })
  return params.toString()
}

function asAuditDetails(value: unknown): AuditDetails {
  return value && typeof value === "object" ? (value as AuditDetails) : {}
}

function formatAuditValue(value: unknown) {
  if (value === undefined) return "Not recorded"
  if (typeof value === "string") return value || "Empty"
  return JSON.stringify(value, null, 2) ?? String(value)
}

function settingChanges(details: AuditDetails): SettingChange[] {
  if (Array.isArray(details.changes)) {
    return details.changes.filter(
      (change) => change && typeof change.setting === "string"
    )
  }
  if (details.setting) {
    return [
      {
        setting: details.setting,
        previous_value: details.previous_value,
        new_value: details.new_value,
      },
    ]
  }
  return []
}

export function AuditLogPage({ role }: { role: AuditRole }) {
  const [filters, setFilters] = useState<Filters>(emptyFilters)
  const [appliedFilters, setAppliedFilters] = useState<Filters>(emptyFilters)
  const [data, setData] = useState<AuditResponse | null>(null)
  const [page, setPage] = useState(1)
  const [reloadKey, setReloadKey] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")
  const endpoint = `/${role}/audit-log`
  const isExecutive = role === "executive"
  const title = isExecutive ? "Executive Audit Log" : "Admin Audit Log"

  useEffect(() => {
    let isCurrent = true

    async function loadData() {
      setIsLoading(true)
      setError("")
      try {
        const response = await apiFetch<AuditResponse>(
          `${endpoint}?${buildQuery(appliedFilters, page)}`
        )
        if (isCurrent) {
          setData(response)
        }
      } catch (caught) {
        if (isCurrent) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Unable to load audit activity."
          )
        }
      } finally {
        if (isCurrent) {
          setIsLoading(false)
        }
      }
    }

    loadData()
    return () => {
      isCurrent = false
    }
  }, [appliedFilters, endpoint, page, reloadKey])

  function updateFilter(field: keyof Filters, value: string) {
    setFilters((current) => ({ ...current, [field]: value }))
  }

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setPage(1)
    setAppliedFilters(filters)
  }

  function resetFilters() {
    setFilters(emptyFilters)
    setAppliedFilters(emptyFilters)
    setPage(1)
  }

  function showSettingsChanges() {
    const settingsFilters = { ...emptyFilters, category: "settings" }
    setFilters(settingsFilters)
    setAppliedFilters(settingsFilters)
    setPage(1)
  }

  const totalPages = Math.max(1, Math.ceil((data?.count ?? 0) / 25))

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: `/${role}`, title: isExecutive ? "Executive" : "Admin" },
          { href: `/${role}/audit-log`, title: "Audit Log" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-3 border-b border-border/70 pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              {title}
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              {isExecutive
                ? "Review changes made by executive accounts in your assigned school or centre."
                : "Review privileged changes across admin and executive accounts."}
            </p>
            {data?.scope ? (
              <p className="text-sm font-medium">
                Scope: {data.scope.name}{" "}
                {data.scope.code ? `(${data.scope.code})` : ""}
              </p>
            ) : null}
          </div>
          <Button
            variant="outline"
            onClick={() => setReloadKey((current) => current + 1)}
          >
            <RotateCcw />
            Refresh
          </Button>
        </section>

        <Card className="border-border/70 bg-card/95 shadow-sm">
          <CardHeader>
            <CardTitle>Search and filters</CardTitle>
            <CardDescription>
              Search activity text or narrow results by account, action, object
              type, and date.
            </CardDescription>
            {!isExecutive ? (
              <div className="pt-2">
                <Button
                  type="button"
                  variant={
                    filters.category === "settings" ? "default" : "outline"
                  }
                  onClick={showSettingsChanges}
                >
                  Settings changes
                </Button>
              </div>
            ) : null}
          </CardHeader>
          <CardContent>
            <form className="grid gap-4 lg:grid-cols-3" onSubmit={applyFilters}>
              <div className="space-y-2 lg:col-span-3">
                <Label htmlFor="audit-search">Search</Label>
                <Input
                  id="audit-search"
                  placeholder="Action, setting, reason, object, name, or account"
                  value={filters.search}
                  onChange={(event) =>
                    updateFilter("search", event.target.value)
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="audit-action">Action</Label>
                <Input
                  id="audit-action"
                  placeholder="e.g. Updated"
                  value={filters.action}
                  onChange={(event) =>
                    updateFilter("action", event.target.value)
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="audit-actor">Account</Label>
                <Input
                  id="audit-actor"
                  placeholder="Name, username, or email"
                  value={filters.actor}
                  onChange={(event) =>
                    updateFilter("actor", event.target.value)
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="audit-object-type">Object type</Label>
                <Input
                  id="audit-object-type"
                  placeholder="e.g. Organization"
                  value={filters.object_type}
                  onChange={(event) =>
                    updateFilter("object_type", event.target.value)
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="audit-date-from">From date</Label>
                <Input
                  id="audit-date-from"
                  type="date"
                  value={filters.date_from}
                  onChange={(event) =>
                    updateFilter("date_from", event.target.value)
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="audit-date-to">To date</Label>
                <Input
                  id="audit-date-to"
                  type="date"
                  value={filters.date_to}
                  onChange={(event) =>
                    updateFilter("date_to", event.target.value)
                  }
                />
              </div>
              <div className="flex items-end gap-2">
                <Button type="submit">
                  <Search />
                  Apply filters
                </Button>
                <Button type="button" variant="outline" onClick={resetFilters}>
                  Reset
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {error ? (
          <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <p>{error}</p>
          </div>
        ) : null}

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <section className="space-y-3">
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>{data?.count ?? 0} audit entries</span>
              <span>
                Page {page} of {totalPages}
              </span>
            </div>
            {data?.results.length ? (
              data.results.map((entry) => {
                const details = asAuditDetails(entry.details)
                const changes = settingChanges(details)
                const isSettingsChange =
                  entry.action.toLowerCase().includes("settings") ||
                  entry.object_type.toLowerCase().includes("settings")

                return (
                  <Card
                    key={entry.id}
                    className="border-border/70 bg-card/95 shadow-sm"
                  >
                    <CardHeader>
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div className="space-y-1">
                          <CardTitle>{entry.action}</CardTitle>
                          <CardDescription>
                            {entry.object_type || "Portal action"}
                            {entry.object_id ? ` #${entry.object_id}` : ""}
                          </CardDescription>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <span className="w-fit rounded-full bg-muted px-2.5 py-1 text-xs font-medium capitalize">
                            {entry.actor.role || "unknown role"}
                          </span>
                          {details.high_impact ? (
                            <span className="w-fit rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-800">
                              High-impact change
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid gap-3 text-sm sm:grid-cols-2">
                        <div className="flex gap-2">
                          <UserRound className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                          <div>
                            <p className="font-medium">
                              {entry.actor.full_name}
                            </p>
                            <p className="text-muted-foreground">
                              @{entry.actor.username}
                              {entry.actor.email
                                ? ` · ${entry.actor.email}`
                                : ""}
                            </p>
                          </div>
                        </div>
                        <div className="flex gap-2 sm:justify-end">
                          <CalendarDays className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                          <p>{formatTimestamp(entry.created_at)}</p>
                        </div>
                      </div>
                      {isSettingsChange ? (
                        <div className="space-y-3 rounded-lg border border-border/70 bg-muted/20 p-4">
                          <div>
                            <p className="text-sm font-medium">
                              Settings change
                            </p>
                            <p className="text-xs text-muted-foreground">
                              Older entries may only show the names of changed
                              fields.
                            </p>
                          </div>
                          {changes.length ? (
                            <div className="space-y-3">
                              {changes.map((change) => (
                                <div
                                  key={change.setting}
                                  className="grid gap-3 rounded-md border border-border/60 bg-background p-3 md:grid-cols-2"
                                >
                                  <p className="text-sm font-medium md:col-span-2">
                                    {change.setting}
                                  </p>
                                  <div>
                                    <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                                      Previous value
                                    </p>
                                    <pre className="mt-1 text-sm break-words whitespace-pre-wrap">
                                      {formatAuditValue(change.previous_value)}
                                    </pre>
                                  </div>
                                  <div>
                                    <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                                      New value
                                    </p>
                                    <pre className="mt-1 text-sm break-words whitespace-pre-wrap">
                                      {formatAuditValue(change.new_value)}
                                    </pre>
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : details.changed_fields?.length ? (
                            <p className="text-sm text-muted-foreground">
                              Changed fields:{" "}
                              {details.changed_fields.join(", ")}
                            </p>
                          ) : (
                            <p className="text-sm text-muted-foreground">
                              Detailed values were not recorded for this change.
                            </p>
                          )}
                          <div>
                            <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                              Reason
                            </p>
                            <p className="mt-1 text-sm">
                              {details.reason || "No reason was recorded."}
                            </p>
                          </div>
                        </div>
                      ) : null}
                      <details className="rounded-lg border border-border/70 bg-muted/30 p-3">
                        <summary className="cursor-pointer text-sm font-medium">
                          View action details
                        </summary>
                        <pre className="mt-3 overflow-x-auto text-xs break-words whitespace-pre-wrap text-muted-foreground">
                          {JSON.stringify(entry.details ?? {}, null, 2)}
                        </pre>
                      </details>
                    </CardContent>
                  </Card>
                )
              })
            ) : (
              <Card className="border-border/70 bg-card/95 shadow-sm">
                <CardContent className="py-12 text-center text-muted-foreground">
                  No audit entries match these filters.
                </CardContent>
              </Card>
            )}
            <div className="flex items-center justify-end gap-2 pt-2">
              <Button
                variant="outline"
                disabled={!data?.previous}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
              >
                <ChevronLeft />
                Previous
              </Button>
              <Button
                variant="outline"
                disabled={!data?.next}
                onClick={() => setPage((current) => current + 1)}
              >
                Next
                <ChevronRight />
              </Button>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}
