"use client"

import Link from "next/link"
import type { LucideIcon } from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  CalendarDays,
  CheckCircle2,
  Clock,
  History,
  Loader2,
  RefreshCw,
  Search,
  XCircle,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { apiFetch } from "@/lib/auth"
import { statusClassName } from "@/lib/status-utils"

type RegistrationRecordsView = "requests" | "history"

type SemesterSummary = {
  id: number | string
  name: string
  academic_session?: string
  semester_type?: string
  max_credit_hours?: number
}

type RegistrationRecord = {
  id: number
  offering: number
  status: string
  is_manual?: boolean
  request_note?: string
  decision_note?: string
  created_at: string
  updated_at?: string
  approved_at?: string | null
  offering_detail?: {
    id: number
    section?: string
    course_detail?: {
      code?: string
      title?: string
      credits?: number | string
      has_lab?: boolean
    }
    semester_detail?: SemesterSummary
  }
  tutorial_group_detail?: { id: number; code: string } | null
  lab_group_detail?: { id: number; code: string } | null
}

type RegistrationRecordsResponse = {
  title: string
  section: string
  semester?: SemesterSummary | null
  registrations: RegistrationRecord[]
  summary?: {
    total: number
    pending: number
    approved: number
    rejected: number
    dropped: number
    credit_hours: number
    semesters?: number
  }
}

function endpointForView(view: RegistrationRecordsView) {
  return view === "requests"
    ? "/student/registration/requests"
    : "/student/registration/history"
}

function titleForView(view: RegistrationRecordsView) {
  return view === "requests" ? "My Registrations" : "History"
}

function descriptionForView(view: RegistrationRecordsView) {
  return view === "requests"
    ? "Review current semester course registrations and their approval status."
    : "Review previous and current course registration records across semesters."
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "Not set"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "Not set"
  return date.toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function formatNumber(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") return "0"
  const parsed = Number(value)
  if (Number.isNaN(parsed)) return String(value)
  return Number.isInteger(parsed) ? String(parsed) : parsed.toFixed(2)
}

function statusLabel(status: string) {
  return status
    .replace(/[-_]/g, " ")
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ")
}

function groupLabel(record: RegistrationRecord) {
  const tutorial = record.tutorial_group_detail?.code
  const lab = record.lab_group_detail?.code
  if (tutorial && lab) return `${tutorial} / ${lab}`
  if (tutorial) return tutorial
  if (lab) return lab
  return "Unassigned"
}

function courseCode(record: RegistrationRecord) {
  return record.offering_detail?.course_detail?.code ?? "Course"
}

function courseTitle(record: RegistrationRecord) {
  return record.offering_detail?.course_detail?.title ?? "Registered course"
}

function semesterName(record: RegistrationRecord) {
  return record.offering_detail?.semester_detail?.name ?? "Unassigned semester"
}

function computeSummary(records: RegistrationRecord[]) {
  return records.reduce(
    (summary, record) => {
      const status = record.status.toLowerCase()
      if (status === "pending") summary.pending += 1
      if (status === "approved") {
        summary.approved += 1
        summary.credit_hours +=
          Number(record.offering_detail?.course_detail?.credits ?? 0) || 0
      }
      if (status === "rejected") summary.rejected += 1
      if (status === "dropped") summary.dropped += 1
      const semesterId = record.offering_detail?.semester_detail?.id
      if (semesterId !== undefined && semesterId !== null)
        summary.semesterIds.add(String(semesterId))
      summary.total += 1
      return summary
    },
    {
      total: 0,
      pending: 0,
      approved: 0,
      rejected: 0,
      dropped: 0,
      credit_hours: 0,
      semesterIds: new Set<string>(),
    }
  )
}

function SummaryTile({
  title,
  value,
  subtitle,
  icon: Icon,
}: {
  title: string
  value: string
  subtitle: string
  icon: LucideIcon
}) {
  return (
    <Card className="border-border/70 shadow-sm">
      <CardContent className="flex items-center justify-between gap-3 p-4">
        <div className="min-w-0">
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="mt-1 truncate text-2xl font-semibold">{value}</p>
          <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>
        </div>
        <Icon className="size-5 shrink-0 text-muted-foreground" />
      </CardContent>
    </Card>
  )
}

function EmptyState({
  title,
  description,
}: {
  title: string
  description: string
}) {
  return (
    <div className="rounded-lg border border-dashed border-border bg-background p-8 text-center">
      <BookOpen className="mx-auto size-8 text-muted-foreground" />
      <p className="mt-3 font-medium">{title}</p>
      <p className="mx-auto mt-1 max-w-md text-sm leading-6 text-muted-foreground">
        {description}
      </p>
    </div>
  )
}

export function StudentRegistrationRecordsPage({
  view,
}: {
  view: RegistrationRecordsView
}) {
  const [data, setData] = useState<RegistrationRecordsResponse | null>(null)
  const [query, setQuery] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")

  const loadData = useCallback(async () => {
    const response = await apiFetch<RegistrationRecordsResponse>(
      endpointForView(view)
    )
    setData(response)
  }, [view])

  useEffect(() => {
    let active = true

    async function hydrate() {
      try {
        await loadData()
      } catch (caught) {
        if (!active) return
        setError(
          caught instanceof Error
            ? caught.message
            : "Unable to load registration records."
        )
      } finally {
        if (active) setIsLoading(false)
      }
    }

    void hydrate()

    return () => {
      active = false
    }
  }, [loadData])

  async function refreshData() {
    setIsLoading(true)
    setError("")
    try {
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to load registration records."
      )
    } finally {
      setIsLoading(false)
    }
  }

  const records = useMemo(
    () => data?.registrations ?? [],
    [data?.registrations]
  )
  const filteredRecords = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    if (!normalized) return records
    return records.filter((record) =>
      [
        courseCode(record),
        courseTitle(record),
        record.offering_detail?.section,
        semesterName(record),
        record.status,
        groupLabel(record),
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalized)
    )
  }, [query, records])

  const computedSummary = useMemo(() => computeSummary(records), [records])
  const summary = data?.summary ?? {
    total: computedSummary.total,
    pending: computedSummary.pending,
    approved: computedSummary.approved,
    rejected: computedSummary.rejected,
    dropped: computedSummary.dropped,
    credit_hours: computedSummary.credit_hours,
    semesters: computedSummary.semesterIds.size,
  }

  const pageTitle = titleForView(view)
  const pageDescription = descriptionForView(view)

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: "/student/registration", title: "Registration" },
          { href: `/student/registration/${view}`, title: pageTitle },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold sm:text-3xl">{pageTitle}</h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              {pageDescription}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => void refreshData()}
              disabled={isLoading}
            >
              <RefreshCw
                className={isLoading ? "size-4 animate-spin" : "size-4"}
              />
              Refresh
            </Button>
            <Button
              render={<Link href="/student/registration/offered-courses" />}
            >
              Offered Courses
              <ArrowRight className="size-4" />
            </Button>
          </div>
        </section>

        {error ? (
          <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <p>{error}</p>
          </div>
        ) : null}

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-6">
            <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <SummaryTile
                title={view === "requests" ? "Semester" : "Semesters"}
                value={
                  view === "requests"
                    ? (data?.semester?.name ?? "No active semester")
                    : String(summary.semesters ?? 0)
                }
                subtitle={
                  view === "requests"
                    ? data?.semester?.academic_session ||
                      "Current registration view"
                    : "Academic terms with records."
                }
                icon={CalendarDays}
              />
              <SummaryTile
                title="Records"
                value={String(summary.total)}
                subtitle="Submitted registration records."
                icon={History}
              />
              <SummaryTile
                title="Approved"
                value={String(summary.approved)}
                subtitle={`${formatNumber(summary.credit_hours)} approved credit hours.`}
                icon={CheckCircle2}
              />
              <SummaryTile
                title={view === "requests" ? "Pending" : "Dropped / Rejected"}
                value={
                  view === "requests"
                    ? String(summary.pending)
                    : `${summary.dropped}/${summary.rejected}`
                }
                subtitle={
                  view === "requests"
                    ? "Awaiting action if approvals are enabled."
                    : "Closed registration records."
                }
                icon={view === "requests" ? Clock : XCircle}
              />
            </section>

            <Card className="border-border/70 shadow-sm">
              <CardHeader>
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div>
                    <CardTitle>
                      {view === "requests"
                        ? "Current Registration Records"
                        : "Registration Records"}
                    </CardTitle>
                    <CardDescription>
                      {view === "requests"
                        ? "Course registrations for the selected semester."
                        : "Registration activity ordered by semester and submission date."}
                    </CardDescription>
                  </div>
                  <div className="relative md:w-72">
                    <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      className="pl-9"
                      placeholder="Search course or status"
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {filteredRecords.map((record) => (
                  <div
                    key={record.id}
                    className="rounded-lg border border-border bg-background p-4"
                  >
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-semibold">{courseCode(record)}</p>
                          <Badge variant="outline">
                            {record.offering_detail?.section || "Main"}
                          </Badge>
                          <Badge variant="secondary">
                            {formatNumber(
                              record.offering_detail?.course_detail?.credits
                            )}{" "}
                            credits
                          </Badge>
                          {record.is_manual ? (
                            <Badge variant="outline">Manual</Badge>
                          ) : null}
                          <span
                            className={`rounded-full border px-2 py-0.5 text-xs font-medium ${statusClassName(record.status)}`}
                          >
                            {statusLabel(record.status)}
                          </span>
                        </div>
                        <p className="mt-2 text-sm font-medium">
                          {courseTitle(record)}
                        </p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {semesterName(record)} / {groupLabel(record)}
                        </p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        render={
                          <Link href={`/student/courses/${record.offering}`} />
                        }
                      >
                        Open
                        <ArrowRight className="size-4" />
                      </Button>
                    </div>

                    <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2 xl:grid-cols-4">
                      <div>
                        <p className="text-muted-foreground">Submitted</p>
                        <p className="mt-1 font-semibold">
                          {formatDateTime(record.created_at)}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Approved</p>
                        <p className="mt-1 font-semibold">
                          {formatDateTime(record.approved_at)}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Request Note</p>
                        <p className="mt-1 line-clamp-2 font-semibold">
                          {record.request_note || "None"}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Decision Note</p>
                        <p className="mt-1 line-clamp-2 font-semibold">
                          {record.decision_note || "None"}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
                {filteredRecords.length === 0 ? (
                  <EmptyState
                    title={
                      records.length === 0
                        ? "No registration records"
                        : "No matching records"
                    }
                    description={
                      records.length === 0
                        ? "Course registration records will appear here after a course is submitted."
                        : "Try a different course code, semester, group, or status."
                    }
                  />
                ) : null}
              </CardContent>
            </Card>
          </div>
        )}
      </main>
    </div>
  )
}
